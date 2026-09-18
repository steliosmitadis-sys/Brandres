--[[
  Paste_Promo.lua -- drop the generated promo graph into the open Fusion comp.

  This is the LOW-RISK path: it needs no MCP server, no bridge, no sockets,
  no Python inside Resolve, and no `io`/`os.execute`. It uses only
  bmd.readfile + comp:Paste, both of which are native Fusion Lua.

  INSTALL
    Copy this file to:
      %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Comp\
    (Comp, not Edit -- it needs a composition to paste into.)

  USE
    Open the Fusion page on a clip, then: Workspace > Scripts > Paste_Promo

  If bmd.readfile turns out to be unavailable on your build, fall back to the
  clipboard route, which always works:
      PowerShell:  Get-Content -Raw C:\promo\promo.comp | Set-Clipboard
      cmd:         type C:\promo\promo.comp | clip
      then click in the Fusion node editor and press Ctrl+V.
]]

-- EDIT THIS to wherever you put the generated file -------------------------
local COMP_FILE = "C:/promo/stelios_promo.comp"
----------------------------------------------------------------------------

local function log(s) print("[promo] " .. tostring(s)) end

local c = comp
if not c then
  local FU = fusion or fu or app
  if FU and FU.GetCurrentComp then
    local ok, r = pcall(function() return FU:GetCurrentComp() end)
    if ok then c = r end
  end
end

if not c then
  log("FAILED: no current composition.")
  log("Open the Fusion page on a clip first, and run this from Scripts > Comp.")
  return
end

if not bmd or not bmd.readfile then
  log("FAILED: bmd.readfile is not available on this build.")
  log("Use the clipboard route instead:")
  log('  type "' .. COMP_FILE .. '" | clip     then Ctrl+V in the node editor')
  return
end

if bmd.fileexists then
  local ok, exists = pcall(bmd.fileexists, COMP_FILE)
  if ok and exists == false then
    log("FAILED: file not found -> " .. COMP_FILE)
    log("Edit COMP_FILE at the top of this script.")
    return
  end
end

local ok, tbl = pcall(bmd.readfile, COMP_FILE)
if not ok or type(tbl) ~= "table" then
  log("FAILED: bmd.readfile could not parse " .. COMP_FILE)
  log("  reason: " .. tostring(tbl))
  log("Use the clipboard route instead (see the header of this script).")
  return
end

local n = 0
for _ in pairs(tbl.Tools or {}) do n = n + 1 end
log("loaded " .. n .. " tools from " .. COMP_FILE)

c:Lock()
c:StartUndo("Paste promo")
local pasted = c:Paste(tbl)
c:EndUndo(true)
c:Unlock()

if pasted == false then
  log("comp:Paste returned false -- nothing was added.")
  log("Use the clipboard route instead (see the header of this script).")
else
  log("DONE. Pasted the graph.")
  log("Next: connect FINAL_OUT to MediaOut1, and set the comp range to 0-719.")
  log("Then point WORK_01..WORK_05 at your screenshots.")
end
