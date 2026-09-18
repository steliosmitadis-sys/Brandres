# Fusion Motion Graphics MCP — DaVinci Resolve (incl. **Free**)

Design motion graphics in DaVinci Resolve by asking Claude. Works on Resolve
21.1 **Free**, which blocks external scripting.

```
claude> make me a 24 second vertical portfolio promo and put it on my clipboard
```

Claude generates a real Fusion node graph — text, shapes, masks, keyframes,
easing, transitions, replaceable image slots — validates it, and puts it on your
clipboard. You press **Ctrl+V** in the Fusion node editor.

---

## Setup

```cmd
cd C:\
git clone -b claude/keen-fermi-mhx6jp https://github.com/steliosmitadis-sys/Brandres.git brandres-resolve
pip install fastmcp
python C:\brandres-resolve\resolve\install.py
```

The installer creates `C:\promo`, generates placeholder images and a first
promo, copies the helper scripts into Resolve's Scripts folder, retires the old
broken `MCP_Bridge.lua`, and prints the last command — a `claude mcp add …` line
with your paths already filled in. Paste that, restart Claude Code, done.

**Then in Resolve:** Fusion page → click the node editor → **Ctrl+V** →
connect `FINAL_OUT` to `MediaOut1` → set the render range to `0-719`.

To use your own work, drop five screenshots over
`C:\promo\assets\WORK_01.png` … `WORK_05.png`. Nothing else to change.

## What you can ask for

| Ask | Tool |
|---|---|
| "portfolio promo, accent colour orange, 4 seconds per slide" | `make_portfolio_promo` |
| "a title card that says LESS / BUT / BETTER" | `make_title_card` |
| "a 1080×1350 square-ish piece with two scenes…" | `make_composition` |
| "put that on my clipboard" | `send_to_clipboard` |
| "make placeholder images" | `make_placeholders` |
| "is the graph valid?" | `validate_composition` |
| "what's my Resolve project?" | `resolve_info` *(needs bridge)* |
| "paste it into Resolve for me" | `push_to_resolve` *(needs bridge)* |

Everything above the divider works with **no bridge and no Resolve scripting**.

## Why it works on Resolve Free

Resolve Free blocks external scripting, and its Lua sandbox removes `io` and
`os.execute`, which is what broke the usual MCP bridges.

This project routes around that. A Fusion composition is plain text in Lua
syntax, and Fusion's node editor accepts it from the clipboard. So the graph is
built entirely on the host in Python and delivered by paste — no sandboxed API
is involved at any point.

The live bridge is a **bonus**, not a dependency. If it runs you also get
`resolve_info`, `fusion_comp_info` and `push_to_resolve`. If it doesn't,
everything else is unaffected.

### The bridge, if you want it

Upstream's bridge touches `io`/`os` in exactly seven places. Each is replaced:

| Upstream | Here |
|---|---|
| `os.getenv("HOME")` | `fusion:MapPath("Temp:/")` |
| `os.execute('mkdir -p')` ×2 | `bmd.createdir()` |
| `io.open(p,"r")` | **`dofile(p)`** — requests *are* Lua chunks |
| `io.open(p,"w")` | `bmd.writefile()`, falling back to `io` |
| `os.time()` | monotonic tick counter |
| `os.remove()` ×2 | **dropped** — a rising `seq` replaces deletion |

`dofile` was never blocked — it is how you load a script in the first place. So
the inbound direction always worked; only the transport assumed `io`. No sockets
are needed.

Start it in Resolve — **Workspace ▸ Console**, set to **Lua**:

```lua
dofile("C:/brandres-resolve/resolve/bridge/resolve_bridge_free.lua")
```

The console evaluates Lua, so a bare path gives `'=' expected near '/'`. It must
be wrapped in `dofile("...")` with forward slashes.

## The design it generates

1080×1920, 30 fps, 720 frames. Black `#0B0B0C`, white `#F2F2F4`, one electric
blue `#124DFF`. Helvetica Neue Bold, left-aligned to a single 8.3 % margin.

| Frames | Content |
|---|---|
| 0–90 | Hook |
| 90–540 | `WORK_01`…`WORK_05`, 90 frames each |
| 540–630 | Value proposition, numbered grid |
| 630–720 | End card |

Motion is crop-reveals, position, scale and layout — no particles, no glow, no
dissolves. Cuts are a hard-edged blue block wipe, alternating direction. **Every
motion channel is eased**; the only hard cuts are scene visibility switches
hidden under the wipe.

If Helvetica Neue isn't installed, pass another font — `Inter` is a good stand-in.

**If text comes out centred when it should be left-aligned**, set `H_LEFT = 1`
in `fusion_mcp/compbuilder.py` and regenerate. Text+'s justification enum is the
one value I could not verify without your machine.

## Verification

Run without Resolve:

```bash
cd resolve/promo
python3 build_promo.py && python3 sim_check.py
lua5.4 verify_comp.lua out/stelios_promo.comp     # if you have lua
cd ../bridge && python3 bridge_client_free.py
```

Checked mechanically here:

- the graph parses through a real **Lua 5.4** interpreter with Fusion-style stub
  constructors; 354 tools, every link resolves, all reachable from `FINAL_OUT`
- all 85 splines solved across all 720 frames: keys ascending, no duplicates, no
  un-eased motion, **exactly one scene visible per frame**, transition block
  hidden outside its windows and fully covering at every cut
- the validator is checked against four deliberately corrupted graphs and
  catches all four
- the MCP server answers a real MCP client: 13 tools, valid output, and clean
  rejection of malformed specs
- the bridge passes a 7-rung ladder inside a sandbox with `io`, `os.execute`,
  `os.remove` and `os.getenv` all nil

Not verifiable without your machine: whether `bmd.writefile`/`createdir`/
`MapPath` exist on your build (the probe reports it, and the clipboard route
does not care), the Text+ justification enum, and exact Text+ size scaling.

## Files

```
install.py                     one-command setup
fusion_mcp/server.py           the MCP server (13 tools)
fusion_mcp/compbuilder.py      spec -> Fusion node graph
fusion_mcp/templates.py        portfolio_promo, title_card
fusion_mcp/validate.py         structural + frame-by-frame checks
bridge/resolve_bridge_free.lua the io/os-free bridge
bridge/bridge_client_free.py   host client + Lua parser
bridge/selftest.py             the 7-rung ladder
bridge/mock_resolve_free.lua   sandbox simulator for tests
probe/fusion_api_probe.lua     what your Lua sandbox exposes
promo/build_promo.py           CLI equivalent of the MCP generate tools
promo/verify_comp.lua          validation via real Lua
promo/sim_check.py             spline simulation
```
