--[[
  Fix_Output.lua -- diagnose and repair a comp that shows no preview.

  Run from Workspace > Scripts > Fix_Output. It reports what it finds, then
  fixes what it can:
    - counts the tools actually in the comp
    - locates FINAL_OUT and the MediaOut node
    - connects them
    - sets the comp range to match the graph
    - loads the output into viewer 2 so something is actually displayed

  Nothing here is destructive. Safe to run repeatedly.
]]

local function log(s) print("[fix] " .. tostring(s)) end

local c = comp
if not c then
  local FU = fusion or fu or app
  if FU and FU.GetCurrentComp then
    local ok, r = pcall(function() return FU:GetCurrentComp() end)
    if ok then c = r end
  end
end
if not c then
  log("FAILED: no composition. Open the Fusion page on a clip and retry.")
  return
end

log("=====================================================")

-- what is actually in here?
local tools, n = c:GetToolList(false) or {}, 0
local kinds = {}
for _, t in pairs(tools) do
  n = n + 1
  local a = t:GetAttrs()
  local id = a and a.TOOLS_RegID or "?"
  kinds[id] = (kinds[id] or 0) + 1
end
log("tools in comp: " .. n)
if n <= 2 then
  log("The graph is NOT here -- the paste did not land.")
  log("Run Workspace > Scripts > Paste_Promo, then run this again.")
  return
end

-- find the two ends
local fin = c:FindTool("FINAL_OUT")
local out
for _, t in pairs(tools) do
  local a = t:GetAttrs()
  if a and a.TOOLS_RegID == "MediaOut" then out = t; break end
end
out = out or c:FindTool("MediaOut1")

log("FINAL_OUT found: " .. tostring(fin ~= nil))
log("MediaOut found : " .. tostring(out ~= nil)
    .. (out and (" (" .. tostring(out:GetAttrs().TOOLS_Name) .. ")") or ""))

if not fin then
  log("FAILED: no FINAL_OUT. The pasted graph is incomplete -- re-run Paste_Promo.")
  return
end
if not out then
  log("FAILED: no MediaOut node. Add one: right-click > Add Tool > I/O > MediaOut.")
  return
end

-- connect
local ok = pcall(function() out.Input = fin.Output end)
log(ok and "connected FINAL_OUT -> " .. tostring(out:GetAttrs().TOOLS_Name)
       or "could not connect -- drag FINAL_OUT into the MediaOut by hand")

-- range, taken from the graph itself
local last = 0
for _, t in pairs(tools) do
  local okg, v = pcall(function() return t.GlobalOut[c.CurrentTime] end)
  if okg and type(v) == "number" and v > last then last = v end
end
if last > 0 then
  pcall(function()
    c:SetAttrs({ COMPN_GlobalStart = 0, COMPN_GlobalEnd = last,
                 COMPN_RenderStart = 0, COMPN_RenderEnd = last })
  end)
  log("comp range set to 0-" .. last)
end

-- Actually display it. A connected comp still shows nothing until a node is
-- loaded into a viewer, which is the step that most often looks like "broken".
-- The API for this differs between builds, so try the known forms in order.
local shown = false
for _, attempt in ipairs({
  function() c:GetPreviewList().Right:ViewOn(out) end,
  function() c:GetPreviewList().Left:ViewOn(out) end,
  function() out:SetAttrs({ TOOLB_Visible = true }) end,
}) do
  if pcall(attempt) then shown = true; break end
end
log(shown and "loaded the output into a viewer"
        or "could not set the viewer from a script -- click the MediaOut "
           .. "node once and press 2")

log("-----------------------------------------------------")
log("If the Fusion viewer is still blank, click the MediaOut")
log("node once and press 2. The Edit page preview should also")
log("show it now.")
log("=====================================================")
