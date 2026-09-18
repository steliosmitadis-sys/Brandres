#!/usr/bin/env python3
"""
bridge_client_free.py -- host side of the Resolve 21.1 Free file-RPC bridge.

The Lua side cannot emit JSON (no `io` to write arbitrary text), so it writes
Lua table literals via bmd.writefile. This module contains a small parser for
that format plus the request/response loop.

Protocol (no file deletion anywhere -- Resolve Free cannot os.remove):
  host -> req.lua   `return { seq = N, id = "...", op = "...", args = {...} }`
  Resolve dofile()s it, ignores any seq it has already served
  Resolve -> res.lua  `{ seq = N, ok = true, result = {...} }`
  host polls res.lua until the seq matches
"""
import os, time, uuid

PROTO = "v3free"


# ------------------------------------------------------------------ parser
class LuaSyntaxError(ValueError):
    pass


def _tokenize(s):
    i, n, out = 0, len(s), []
    while i < n:
        ch = s[i]
        if ch in " \t\r\n,;":
            i += 1
        elif s.startswith("--[[", i):
            j = s.find("]]", i)
            i = n if j < 0 else j + 2
        elif s.startswith("--", i):
            j = s.find("\n", i)
            i = n if j < 0 else j + 1
        elif ch in "{}[]=":
            out.append((ch, ch)); i += 1
        elif ch in "\"'":
            q, j, buf = ch, i + 1, []
            while j < n and s[j] != q:
                if s[j] == "\\":
                    nxt = s[j + 1] if j + 1 < n else ""
                    buf.append({"n": "\n", "t": "\t", "r": "\r",
                                "\\": "\\", '"': '"', "'": "'"}.get(nxt, nxt))
                    j += 2
                else:
                    buf.append(s[j]); j += 1
            if j >= n:
                raise LuaSyntaxError("unterminated string at %d" % i)
            out.append(("str", "".join(buf))); i = j + 1
        else:
            j = i
            while j < n and (s[j].isalnum() or s[j] in "._-+"):
                j += 1
            if j == i:
                raise LuaSyntaxError("unexpected %r at %d" % (ch, i))
            word = s[i:j]
            try:
                out.append(("num", int(word)))
            except ValueError:
                try:
                    out.append(("num", float(word)))
                except ValueError:
                    out.append(("name", word))
            i = j
    return out


def lua_loads(text):
    """Parse a Lua table literal (Fusion's bmd.writefile output) into Python."""
    toks = _tokenize(text.strip())
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else (None, None)

    def eat(kind=None):
        if pos[0] >= len(toks):
            raise LuaSyntaxError("unexpected end of input")
        t = toks[pos[0]]; pos[0] += 1
        if kind and t[0] != kind:
            raise LuaSyntaxError("expected %s, got %r" % (kind, t))
        return t

    def value():
        k, v = peek()
        if k == "{":
            return table()
        if k in ("str", "num"):
            eat(); return v
        if k == "name":
            eat()
            if v == "true":  return True
            if v == "false": return False
            if v == "nil":   return None
            # a constructor such as FuID { "x" } or Clip { ... }
            if peek()[0] == "{":
                inner = table()
                return {"__ctor": v, **(inner if isinstance(inner, dict) else {"items": inner})}
            return v
        raise LuaSyntaxError("bad value %r" % (peek(),))

    def table():
        eat("{")
        d, arr = {}, []
        while True:
            k, _ = peek()
            if k is None:
                raise LuaSyntaxError("unterminated table")
            if k == "}":
                eat(); break
            if k == "[":                              # [key] = value
                eat("["); key = value(); eat("]"); eat("=")
                d[key] = value()
            elif k == "name" and pos[0] + 1 < len(toks) and toks[pos[0] + 1][0] == "=":
                key = eat("name")[1]; eat("=")
                d[key] = value()
            else:
                arr.append(value())
        if d and arr:
            for n, item in enumerate(arr, 1):
                d[n] = item
            return d
        return d if d or not arr else arr

    return value()


# ------------------------------------------------------------------ client
class BridgeError(RuntimeError):
    pass


class Bridge:
    def __init__(self, directory=None, timeout=15.0):
        self.dir = directory or self.default_dir()
        self.req = os.path.join(self.dir, "req.lua")
        self.res = os.path.join(self.dir, "res.lua")
        self.hello = os.path.join(self.dir, "hello.lua")
        self.timeout = timeout
        self.seq = int(time.time()) % 1000000       # survives host restarts

    @staticmethod
    def default_dir():
        """Mirror fusion:MapPath('Temp:/') as closely as we can from outside."""
        env = os.environ
        for base in (env.get("TEMP"), env.get("TMP"),
                     os.path.join(env.get("USERPROFILE", ""), "AppData", "Local", "Temp"),
                     "/tmp"):
            if base and os.path.isdir(base):
                return os.path.join(base, "resolve-mcp-" + PROTO)
        return os.path.join(os.path.expanduser("~"), "resolve-mcp-" + PROTO)

    def handshake(self):
        if not os.path.exists(self.hello):
            raise BridgeError(
                "No handshake file at %s\n"
                "The bridge is not running, or it resolved a different temp dir.\n"
                "Start it in Resolve (Workspace > Console > Lua):\n"
                '  dofile("C:/davinci-resolve-mcp/bridge/resolve_bridge_free.lua")\n'
                "then read the `dir =` line it prints and pass it as --dir." % self.hello)
        return lua_loads(open(self.hello, encoding="utf-8", errors="replace").read())

    def call(self, op, **args):
        self.seq += 1
        seq = self.seq
        body = "return { seq = %d, id = %s, op = %s, args = %s }" % (
            seq, _to_lua(uuid.uuid4().hex[:8]), _to_lua(op), _to_lua(args))
        os.makedirs(self.dir, exist_ok=True)
        tmp = self.req + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, self.req)                    # atomic: never a half-read chunk

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                if os.path.exists(self.res):
                    data = lua_loads(open(self.res, encoding="utf-8", errors="replace").read())
                    if isinstance(data, dict) and data.get("seq") == seq:
                        if data.get("ok"):
                            return data.get("result")
                        raise BridgeError("%s: %s" % (op, data.get("error")))
            except LuaSyntaxError:
                pass                                 # mid-write; try again
            time.sleep(0.03)
        raise BridgeError(
            "timeout after %.0fs waiting for op %r.\n"
            "Is the bridge window still open in Resolve? Check its console output."
            % (self.timeout, op))


def _to_lua(v):
    if isinstance(v, dict):
        return "{ " + ", ".join("%s = %s" % (k, _to_lua(x)) for k, x in v.items()) + " }"
    if isinstance(v, (list, tuple)):
        return "{ " + ", ".join(_to_lua(x) for x in v) + " }"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if v is None:
        return "nil"
    return '"%s"' % str(v).replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    # self-test of the parser against realistic bmd.writefile output
    sample = '''{
	ok = true,
	seq = 12,
	result = {
		pong = true,
		tick = 42,
		writer = "bmd.writefile",
		dir = "C:\\\\Users\\\\steli\\\\AppData\\\\Local\\\\Temp\\\\resolve-mcp-v3free/",
		tools = { "Text1", "Merge1" },
		nested = { a = 1.5, b = false, c = nil },
		mode = FuID { "None" }
	}
}'''
    got = lua_loads(sample)
    assert got["ok"] is True, got
    assert got["seq"] == 12
    r = got["result"]
    assert r["pong"] is True and r["tick"] == 42
    assert r["writer"] == "bmd.writefile"
    assert "Temp" in r["dir"] and "\\\\" not in r["dir"]
    # pure-array Lua tables come back as 0-indexed Python lists, not 1-indexed dicts
    assert r["tools"] == ["Text1", "Merge1"], r["tools"]
    assert r["nested"]["a"] == 1.5 and r["nested"]["b"] is False
    assert r["mode"]["__ctor"] == "FuID"
    assert _to_lua({"a": 1, "b": "x", "c": [1, 2]}) == '{ a = 1, b = "x", c = { 1, 2 } }'
    # the request body must be valid Lua, not Python %-formatting
    _b = "return { seq = %d, id = %s, op = %s, args = %s }" % (
        7, _to_lua("abc123"), _to_lua("ping"), _to_lua({"echo": "hi", "n": 2}))
    assert _b == 'return { seq = 7, id = "abc123", op = "ping", args = { echo = "hi", n = 2 } }', _b
    _needle = "%" + "q"   # built at runtime so this guard never matches itself
    _self = open(__file__, encoding="utf-8").read()
    assert _needle not in _self.replace('"%" + "q"', ""), "Lua format specifier leaked into Python"
    print("lua_loads + _to_lua self-test PASSED")
    print("default bridge dir ->", Bridge.default_dir())
