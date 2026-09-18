--[[
  fusion_api_probe.lua — enumerate what Resolve's Lua sandbox actually exposes.

  Resolve 21.x Free removes `io` and `os.execute` from the Fusion/Resolve Lua
  environment. This probe answers, empirically and on YOUR machine, exactly
  which primitives survive — so the bridge can be built on facts, not guesses.

  RUN -- the Fusion console evaluates LUA, not shell commands or bare paths.
  Typing `probe/fusion_api_probe.lua` gives "'=' expected near '/'". Use dofile:

  RUN (either works):
    Workspace > Console  -> switch to Lua -> dofile("C:/brandres-resolve/resolve/probe/fusion_api_probe.lua")
    Workspace > Scripts  -> (after copying this file into the Scripts/Utility folder)

  It prints a report to the Console AND tries to write it to disk. If the disk
  write succeeds, the path is printed -- that alone proves a usable write path.
]]

local report = {}
local function say(s) print(s); report[#report+1] = s end
local function has(v) return v ~= nil end
local function tick(b) return b and "YES" or "no " end

say("=============================================================")
say(" FUSION / RESOLVE LUA API PROBE")
say("=============================================================")

---------------------------------------------------------------- globals
local G = _G
say("")
say("-- core globals ---------------------------------------------")
for _, n in ipairs({ "bmd", "fusion", "fu", "app", "resolve", "comp", "composition",
                     "io", "os", "package", "require", "dofile", "loadfile",
                     "load", "loadstring", "collectgarbage" }) do
  local v = rawget(G, n)
  say(string.format("  %-14s %s  (%s)", n, tick(has(v)), type(v)))
end

---------------------------------------------------------------- os
say("")
say("-- os.* members --------------------------------------------")
if os then
  for _, n in ipairs({ "execute", "getenv", "remove", "rename", "time", "clock",
                       "date", "tmpname", "exit", "difftime" }) do
    say(string.format("  os.%-10s %s", n, tick(has(os[n]))))
  end
else
  say("  os is NIL -- no os.* available at all")
end

---------------------------------------------------------------- io
say("")
say("-- io.* members --------------------------------------------")
if io then
  for _, n in ipairs({ "open", "lines", "read", "write", "close", "popen", "output", "input" }) do
    say(string.format("  io.%-10s %s", n, tick(has(io[n]))))
  end
else
  say("  io is NIL -- classic Lua file I/O unavailable (expected on Resolve Free)")
end

---------------------------------------------------------------- bmd
say("")
say("-- bmd.* members (the important one) ------------------------")
if bmd then
  for _, n in ipairs({ "readfile", "writefile", "readstring", "writestring",
                       "createdir", "direxists", "fileexists", "getfiles",
                       "wait", "scriptapp", "setacp", "openfileDialog",
                       "savefileDialog", "UIDispatcher", "getcurrentdir",
                       "gettime", "getappfilename", "openurl", "parseFilename" }) do
    say(string.format("  bmd.%-16s %s", n, tick(has(bmd[n]))))
  end
  say("")
  say("  full bmd key dump:")
  local keys = {}
  for k in pairs(bmd) do keys[#keys+1] = tostring(k) end
  table.sort(keys)
  local line = "   "
  for _, k in ipairs(keys) do
    if #line + #k + 2 > 76 then say(line); line = "   " end
    line = line .. " " .. k
  end
  if #line > 3 then say(line) end
else
  say("  bmd is NIL -- this is fatal for every file-based bridge design")
end

---------------------------------------------------------------- app / fusion
say("")
say("-- app / fusion methods ------------------------------------")
for name, obj in pairs({ app = rawget(G, "app"), fusion = rawget(G, "fusion"), fu = rawget(G, "fu") }) do
  if obj then
    for _, m in ipairs({ "MapPath", "GetResolve", "GetCurrentComp", "SetPrefs",
                         "GetPrefs", "SavePrefs", "SetData", "GetData", "Print" }) do
      local ok, v = pcall(function() return obj[m] end)
      say(string.format("  %s:%-16s %s", name, m, tick(ok and has(v))))
    end
  end
end

---------------------------------------------------------------- MapPath
say("")
say("-- writable path resolution --------------------------------")
local mapper = (fusion and fusion.MapPath and fusion) or (app and app.MapPath and app) or (fu and fu.MapPath and fu)
local tempdir
if mapper then
  for _, p in ipairs({ "Temp:/", "UserPaths:/", "UserData:/", "Comps:/" }) do
    local ok, r = pcall(function() return mapper:MapPath(p) end)
    say(string.format("  MapPath(%-12s) -> %s", p, (ok and tostring(r)) or "FAILED"))
    if p == "Temp:/" and ok and r then tempdir = r end
  end
else
  say("  no MapPath available on app/fusion/fu")
end

---------------------------------------------------------------- sockets
say("")
say("-- socket / network ----------------------------------------")
for _, m in ipairs({ "socket", "socket.core", "luasocket", "ljsocket", "http", "ssl" }) do
  local ok, mod = pcall(require, m)
  say(string.format("  require(%-12s) %s", m, ok and ("YES -> " .. type(mod)) or "no"))
end
say(string.format("  package.path present: %s", tick(package and has(package.path))))
if package and package.cpath then say("  package.cpath = " .. tostring(package.cpath):sub(1, 200)) end

---------------------------------------------------------------- UIManager
say("")
say("-- UIManager / timers --------------------------------------")
local uim = (fu and fu.UIManager) or (fusion and fusion.UIManager) or (app and app.UIManager)
say(string.format("  UIManager           %s", tick(has(uim))))
say(string.format("  bmd.UIDispatcher    %s", tick(bmd and has(bmd.UIDispatcher))))
if uim and bmd and bmd.UIDispatcher then
  local ok = pcall(function()
    local d = bmd.UIDispatcher(uim)
    local w = d:AddWindow({ ID = "ProbeWin", WindowTitle = "probe", Hidden = true },
                          { uim:VGroup{ uim:Timer{ ID = "ProbeTimer", Interval = 1000 } } })
    return w ~= nil
  end)
  say(string.format("  ui:Timer construct  %s", tick(ok)))
end

---------------------------------------------------------------- comp
say("")
say("-- composition access --------------------------------------")
local C = rawget(G, "comp") or rawget(G, "composition")
if not C and fusion and fusion.GetCurrentComp then local ok, r = pcall(function() return fusion:GetCurrentComp() end); if ok then C = r end end
say(string.format("  comp object         %s", tick(has(C))))
if C then
  for _, m in ipairs({ "Paste", "Lock", "Unlock", "StartUndo", "EndUndo",
                       "AddTool", "GetToolList", "SetData", "GetData",
                       "MapPath", "Save", "GetAttrs" }) do
    local ok, v = pcall(function() return C[m] end)
    say(string.format("  comp:%-16s %s", m, tick(ok and has(v))))
  end
  local ok, attrs = pcall(function() return C:GetAttrs() end)
  if ok and attrs then
    say("  COMPN_FileName = " .. tostring(attrs.COMPS_FileName))
    say("  frame range    = " .. tostring(attrs.COMPN_RenderStart) .. " .. " .. tostring(attrs.COMPN_RenderEnd))
  end
end

---------------------------------------------------------------- resolve
say("")
say("-- resolve object ------------------------------------------")
local R = rawget(G, "resolve")
if not R and bmd and bmd.scriptapp then local ok, r = pcall(bmd.scriptapp, "Resolve"); if ok then R = r end end
if not R and fusion and fusion.GetResolve then local ok, r = pcall(function() return fusion:GetResolve() end); if ok then R = r end end
say(string.format("  resolve object      %s", tick(has(R))))
if R then
  local ok, pn = pcall(function() return R:GetProductName() end)
  local ok2, vs = pcall(function() return R:GetVersionString() end)
  say("  product = " .. (ok and tostring(pn) or "?") .. "  version = " .. (ok2 and tostring(vs) or "?"))
  local okp, pm = pcall(function() return R:GetProjectManager() end)
  if okp and pm then
    local okc, pr = pcall(function() return pm:GetCurrentProject() end)
    if okc and pr then say("  current project = " .. tostring(pr:GetName())) end
  end
end

---------------------------------------------------------------- WRITE TEST
say("")
say("=============================================================")
say(" WRITE-PATH TEST  (this decides whether the bridge can work)")
say("=============================================================")
local dir = (tempdir or "C:/Users/Public/") .. "resolve-mcp-probe/"
local wrote_to = nil

if bmd and bmd.createdir then
  local ok, err = pcall(bmd.createdir, dir)
  say(string.format("  bmd.createdir(%s) -> %s", dir, ok and "OK" or ("FAILED: " .. tostring(err))))
end

-- candidate 1: bmd.writefile (the preferred transport)
if bmd and bmd.writefile then
  local p = dir .. "probe_writefile.txt"
  local ok, err = pcall(bmd.writefile, p, { probe = "hello", n = 42, nested = { a = 1, b = "two" } })
  say(string.format("  bmd.writefile       -> %s", ok and ("OK  " .. p) or ("FAILED: " .. tostring(err))))
  if ok then
    wrote_to = wrote_to or p
    if bmd.readfile then
      local ok2, back = pcall(bmd.readfile, p)
      say(string.format("  bmd.readfile back   -> %s", (ok2 and type(back) == "table")
          and ("OK  probe=" .. tostring(back.probe) .. " n=" .. tostring(back.n))
          or ("FAILED: " .. tostring(back))))
    end
  end
end

-- candidate 2: classic io (expected to fail on Free)
if io and io.open then
  local p = dir .. "probe_io.txt"
  local ok, err = pcall(function()
    local f = io.open(p, "w"); f:write("hello"); f:close(); return true
  end)
  say(string.format("  io.open write       -> %s", ok and ("OK  " .. p) or ("FAILED: " .. tostring(err))))
  if ok then wrote_to = wrote_to or p end
else
  say("  io.open write       -> UNAVAILABLE (io is nil)")
end

-- candidate 3: dofile read-back (proves the inbound direction)
if dofile and wrote_to and bmd and bmd.writefile then
  local p = dir .. "probe_dofile.lua"
  local ok = pcall(bmd.writefile, p, { marker = "dofile-target" })
  if ok then
    local ok2, res = pcall(dofile, p)
    say(string.format("  dofile read-back    -> %s", ok2 and ("OK (returned " .. type(res) .. ")")
        or ("expected-fail: " .. tostring(res))))
  end
end

---------------------------------------------------------------- verdict
say("")
say("-- VERDICT --------------------------------------------------")
local can_read  = has(dofile) or (bmd and has(bmd.readfile)) or (io and has(io.open))
local can_write = (bmd and has(bmd.writefile)) or (io and has(io.open))
say("  inbound  (host -> Resolve): " .. (can_read  and "POSSIBLE" or "BLOCKED"))
say("  outbound (Resolve -> host): " .. (can_write and "POSSIBLE" or "BLOCKED"))
if can_read and can_write then
  say("  => file-RPC bridge is viable. Run bridge/resolve_bridge_free.lua")
else
  say("  => report this output; the bridge needs a different transport")
end

-- persist the report next to the probe files
if bmd and bmd.writefile then
  local p = dir .. "probe_report.txt"
  pcall(bmd.writefile, p, { lines = report })
  print("")
  print("[probe] report written to: " .. p)
  print("[probe] paste that file (or this console output) back to Claude.")
end
