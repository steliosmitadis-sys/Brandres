# DaVinci Resolve 21.1 Free — Fusion bridge + generated motion-design promo

Two deliverables:

1. **`promo/`** — a generated 1080×1920 / 30 fps / 24 s Fusion node graph with five
   replaceable screenshot placeholders. Needs **no bridge, no MCP, no Python inside
   Resolve**. This is the path to the finished video.
2. **`bridge/`** — the upstream file-RPC bridge rewritten so it runs under Resolve
   21.1 Free's Lua sandbox (no `io`, no `os.execute`, no `os.remove`). For live
   iteration once the video exists.

---

## 1. The blocker, precisely

Resolve 21.1 Free's Lua sandbox removes `io` and most of `os`. Upstream's
`bridge/resolve_bridge.lua` touches those in exactly **seven** places — that is the
whole problem, and every one has a native replacement:

| Upstream | Replacement in `resolve_bridge_free.lua` |
|---|---|
| `os.getenv("HOME")` | `fusion:MapPath("Temp:/")` |
| `os.execute('mkdir -p')` ×2 | `bmd.createdir()` |
| `io.open(p,"r")` | **`dofile(p)`** — requests *are* Lua chunks |
| `io.open(p,"w")` | `bmd.writefile()`, with an `io` fallback |
| `os.time()` | monotonic tick counter |
| `os.remove()` ×2 | **removed** — a rising `seq` field supersedes deletion |

The `dofile` move is the key one: `dofile` is provably present, because it is how you
loaded the bridge in the first place. So the inbound direction was never actually
blocked — only the transport *assumed* `io`.

**Sockets are not needed and were not used.** `require("socket")` may well be absent;
`probe/fusion_api_probe.lua` reports the answer for your build either way. A file
channel through `Temp:/` is simpler, has no port/firewall surface, and survives a
Resolve restart.

## 2. Fastest route to the video (recommended — zero API risk)

```cmd
cd resolve\promo
python make_placeholders.py
python build_promo.py --assets "C:/promo/assets"
copy out\assets\*.png C:\promo\assets\
type out\stelios_promo.comp | clip
```

Then in Resolve: open the **Fusion page** on a clip → click in the node editor →
**Ctrl+V**. Fusion's own parser reads the clipboard; nothing in the sandbox is involved.

Then:
- connect **`FINAL_OUT`** → **`MediaOut1`**
- set the comp render range to **0–719**
- set the timeline to **1080×1920 @ 30 fps**

To swap in real work, either overwrite `C:/promo/assets/WORK_01.png` … `WORK_05.png`,
or select the `WORK_01`…`WORK_05` Loader nodes and point them at any file.

`promo/Paste_Promo.lua` does the same thing from **Workspace ▸ Scripts** if you prefer
a button; it falls back to telling you to use the clipboard if `bmd.readfile` is
missing on your build.

**Paste `out/smoke_test.comp` first** (17 nodes, ~10 seconds). It contains one of every
construct the big graph uses — Text+, Transform, XYPath, BezierSpline, RectangleMask,
Loader, animated Merge. If it renders, the 354-node graph will too.

## 3. The design

Frames are 30 fps, 0–719.

| Frames | Time | Content |
|---|---|---|
| 0–90 | 0–3 s | Hook — "BRANDS / BUILT TO / BE SEEN" |
| 90–540 | 3–18 s | `WORK_01`…`WORK_05`, 90 frames each |
| 540–630 | 18–21 s | Value proposition — 01 / 02 / 03 numbered grid |
| 630–720 | 21–24 s | End card — STELIOS MITADIS / GRAPHIC DESIGNER / LET'S BUILD YOUR BRAND |

Black `#0B0B0C`, white `#F2F2F4`, one electric-blue accent `#1240FF`. Helvetica Neue
Bold, left-aligned to a single margin at 8.3 % (≈90 px). Motion is crop-reveals,
position, scale and layout — no particles, no glow, no dissolves. Scene changes are a
hard-edged blue block wipe, alternating direction, horizontal for the final cut.

**Every motion channel is eased** (expo/quint/quart/back). The only non-eased splines
are the 8 scene-visibility `Blend` channels, which are intentional hard cuts hidden
under the wipe. `sim_check.py` enforces this.

### Tuning

Constants live at the top of `build_promo.py`:

- `H_LEFT = 0` — **the one value most likely to need changing.** Text+'s
  `HorizontalJustificationNew` enum is not documented; if your text lands centred
  instead of left-aligned, set `H_LEFT = 1` and regenerate.
- `MEGA / H1 / H2 / BODY / LABEL` — type scale
- `BLUE` — the accent
- `--font "Helvetica Neue" --style Bold` — Helvetica Neue often isn't installed on
  Windows; `--font Inter` or `--font "Arial"` are decent substitutes.

Copy lives in `WORKS` and the `scene_*` functions.

## 4. The bridge (optional, for live iteration)

```cmd
python probe\fusion_api_probe.lua   :: actually: run this INSIDE Resolve
```

In Resolve, **Workspace ▸ Console ▸ Lua**:

```lua
dofile("C:/davinci-resolve-mcp/probe/fusion_api_probe.lua")   -- what your build exposes
dofile("C:/davinci-resolve-mcp/bridge/resolve_bridge_free.lua")
```

The bridge prints its `dir =` line. Then on the host:

```cmd
python bridge\selftest.py --dir "<that dir>"
```

which runs your ladder in order and stops at the first failure:

```
PASS  1. ping / pong           2. sandbox report      3. Resolve project name
PASS  4. Fusion composition    5. create Text+ 'TEST'  6. animate a parameter
```

`--paste C:/promo/stelios_promo.comp` adds rung 7.

## 5. What is verified, and what is not

I could not reach your Windows machine from this session, so the split matters.

**Verified here, mechanically:**
- `out/stelios_promo.comp` parses through a real **Lua 5.4** interpreter with
  Fusion-style stub constructors — the same way Fusion consumes it. 354 tools, every
  `SourceOp` resolves, all reachable from `FINAL_OUT`, no orphans (`verify_comp.lua`).
- All 85 splines simulated across all 720 frames: keyframes strictly ascending, no
  duplicates, no un-eased motion, **exactly one scene visible on every frame**, blue
  wipe fully hidden outside its windows and at full coverage at all 7 boundaries
  (`sim_check.py`).
- The bridge runs the **full 7-rung ladder** inside `mock_resolve_free.lua`, which
  loads the real bridge into a sandbox with `io=nil, os.execute=nil, os.remove=nil,
  os.getenv=nil` — i.e. the transport is proven not to need them.

**Not verifiable without your machine:**
- Whether `bmd.writefile` / `bmd.createdir` / `fusion:MapPath` exist on Resolve 21.1
  Free. `probe/fusion_api_probe.lua` answers this; the bridge falls back to `io` and
  reports `writer = NONE` with a clear error rather than failing silently.
- Whether `bmd.readfile` parses a `.comp`. If not, use the clipboard route — it
  bypasses that call entirely.
- Text+'s justification enum (`H_LEFT`) and exact Text+ `Size` scaling.
- Whether `ui:Timer` works, which decides non-blocking vs blocking polling. Both are
  implemented; the bridge picks automatically and says which.

## 6. Files

```
probe/fusion_api_probe.lua     what your Lua sandbox actually exposes
bridge/resolve_bridge_free.lua the io/os-free bridge
bridge/bridge_client_free.py   host client + Lua-literal parser (self-testing)
bridge/selftest.py             the 7-rung ladder
bridge/mock_resolve_free.lua   Resolve-Free sandbox simulator for regression tests
promo/build_promo.py           the node-graph generator
promo/make_placeholders.py     the five placeholder stills (stdlib only)
promo/verify_comp.lua          structural validation via real Lua
promo/sim_check.py             frame-by-frame spline simulation
promo/Paste_Promo.lua          one-click paste from Workspace > Scripts
promo/out/stelios_promo.comp   the deliverable (354 nodes)
promo/out/smoke_test.comp      paste this first
```

Regression-test everything without Resolve:

```bash
cd promo && python3 build_promo.py && lua5.4 verify_comp.lua out/stelios_promo.comp && python3 sim_check.py
cd ../bridge && python3 bridge_client_free.py
```
