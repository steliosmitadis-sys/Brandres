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

local n, last = 0, 0
for _, tool in pairs(tbl.Tools or {}) do
  n = n + 1
  -- every generator carries GlobalOut, so the highest one is the last frame
  local go = type(tool) == "table" and tool.Inputs and tool.Inputs.GlobalOut
  local v = type(go) == "table" and go.Value or (type(go) == "number" and go)
  if type(v) == "number" and v > last then last = v end
end
log("loaded " .. n .. " tools from " .. COMP_FILE)

c:Lock()
c:StartUndo("Paste promo")
local pasted = c:Paste(tbl)
c:EndUndo(true)
c:Unlock()

if pasted == false then
  log("comp:Paste returned false -- nothing was added.")
  log("Use the clipboard route instead (see the header of this script).")
  return
end
log("pasted the graph.")

-- Wire FINAL_OUT into the comp's MediaOut. Without this the viewer just says
-- "No frame available for MediaOut1", which looks like the paste failed.
local function find_mediaout()
  for _, t in pairs(c:GetToolList(false) or {}) do
    local a = t:GetAttrs()
    if a and a.TOOLS_RegID == "MediaOut" then return t end
  end
  return c:FindTool("MediaOut1")
end

local fin, out = c:FindTool("FINAL_OUT"), find_mediaout()
if fin and out then
  c:Lock(); c:StartUndo("Connect promo")
  local ok = pcall(function() out.Input = fin.Output end)
  c:EndUndo(true); c:Unlock()
  log(ok and "connected FINAL_OUT -> " .. tostring(out:GetAttrs().TOOLS_Name)
         or "could not connect automatically -- drag FINAL_OUT into MediaOut1")
else
  log("could not find " .. (fin and "a MediaOut node" or "FINAL_OUT")
      .. " -- connect them by hand")
end

-- Match the comp range to the graph so the whole piece plays.
if last > 0 then
  local ok = pcall(function()
    c:SetAttrs({ COMPN_GlobalStart = 0, COMPN_GlobalEnd = last,
                 COMPN_RenderStart = 0, COMPN_RenderEnd = last })
  end)
  log(ok and ("range set to 0-" .. last)
         or ("set the comp range to 0-" .. last .. " by hand"))
end

log("DONE. Now replace the WORK_01..WORK_05 images with your screenshots.")
