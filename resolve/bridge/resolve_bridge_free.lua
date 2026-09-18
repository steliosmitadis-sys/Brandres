--[[
  resolve_bridge_free.lua -- file-RPC bridge for DaVinci Resolve 21.1 FREE.

  WHAT CHANGED vs the upstream bridge, and why
  --------------------------------------------------------------------------
  Resolve 21.1 Free's Lua sandbox has `io == nil` and `os.execute == nil`, so
  upstream's transport (io.open + os.execute + os.remove) cannot run at all.
  Every one of those seven call sites is replaced:

    os.getenv("HOME")      ->  fusion:MapPath("Temp:/")   (path-map, no env)
    os.execute("mkdir -p") ->  bmd.createdir()
    io.open(p, "r")        ->  dofile(p)        <- requests ARE Lua chunks
    io.open(p, "w")        ->  bmd.writefile()  <- with io fallback
    os.time()              ->  a monotonic counter
    os.remove(REQ)         ->  removed entirely: a monotonically increasing
    os.remove(STOP)            `seq` field supersedes deletion, so the bridge
                               never needs to mutate the filesystem to
                               acknowledge a request.

  The `dofile` route is the key move: the host writes a request as a Lua chunk
  (`return { seq = 7, op = "ping" }`) and the bridge simply executes it. dofile
  is confirmed present -- it is how this file itself gets loaded.

  RUN
    Workspace > Console -> Lua ->
      dofile("C:/brandres-resolve/resolve/bridge/resolve_bridge_free.lua")
    or copy into the Scripts folder and use Workspace > Scripts.

  STOP
    Click Stop in the little window, or send op="stop".
]]

local PROTO = "v3free"
local POLL_MS = 60
local MAX_SECONDS = 12 * 3600

----------------------------------------------------------------------
-- 0. locate hosts
----------------------------------------------------------------------
local G = _G
local FU = rawget(G, "fusion") or rawget(G, "fu") or rawget(G, "app")
local RESOLVE = rawget(G, "resolve")
if not RESOLVE and bmd and bmd.scriptapp then
  local ok, r = pcall(bmd.scriptapp, "Resolve"); if ok then RESOLVE = r end
end
if not RESOLVE and FU and FU.GetResolve then
  local ok, r = pcall(function() return FU:GetResolve() end); if ok then RESOLVE = r end
end

local function getcomp()
  local c = rawget(G, "comp") or rawget(G, "composition")
  if c then return c end
  if FU and FU.GetCurrentComp then
    local ok, r = pcall(function() return FU:GetCurrentComp() end)
    if ok then return r end
  end
  return nil
end

----------------------------------------------------------------------
-- 1. writable directory, without os.getenv
----------------------------------------------------------------------
local DIR
if FU and FU.MapPath then
  local ok, r = pcall(function() return FU:MapPath("Temp:/") end)
  if ok and r and r ~= "" then DIR = tostring(r) end
end
DIR = (DIR or "C:/Users/Public/") .. "resolve-mcp-" .. PROTO .. "/"
DIR = DIR:gsub("\\", "/"):gsub("//+", "/")

if bmd and bmd.createdir then pcall(bmd.createdir, DIR) end

local REQ = DIR .. "req.lua"
local RES = DIR .. "res.lua"
local HELLO = DIR .. "hello.lua"

----------------------------------------------------------------------
-- 2. transport: pick a write backend at runtime and say which one
----------------------------------------------------------------------
local function sanitize(v, depth)
  depth = depth or 0
  local t = type(v)
  if t == "number" or t == "boolean" or t == "string" then return v end
  if t == "nil" then return nil end
  if t == "table" and depth < 8 then
    local out = {}
    for k, val in pairs(v) do
      local kt = type(k)
      if kt == "string" or kt == "number" then
        local s = sanitize(val, depth + 1)
        if s ~= nil then out[k] = s end
      end
    end
    return out
  end
  return tostring(v)
end

local WRITER_NAME, write_table
if bmd and bmd.writefile then
  WRITER_NAME = "bmd.writefile"
  write_table = function(path, tbl)
    -- pcall's own flag only says the call did not raise; writefile signals a
    -- failed write (bad path, no permission) by RETURNING false. Both matter.
    local ok, r = pcall(bmd.writefile, path, sanitize(tbl))
    if not ok then return false, tostring(r) end
    if r == false then return false, "writefile returned false (bad path or permissions)" end
    return true
  end
elseif io and io.open then
  WRITER_NAME = "io.open"
  write_table = function(path, tbl)
    local function ser(v, ind)
      local t = type(v)
      if t == "string" then return string.format("%q", v) end
      if t == "number" or t == "boolean" then return tostring(v) end
      if t ~= "table" then return string.format("%q", tostring(v)) end
      local parts = { "{" }
      for k, val in pairs(v) do
        local key = type(k) == "string" and (k .. " = ") or ""
        parts[#parts + 1] = ind .. "\t" .. key .. ser(val, ind .. "\t") .. ","
      end
      parts[#parts + 1] = ind .. "}"
      return table.concat(parts, "\n")
    end
    local ok, r = pcall(function()
      local f = io.open(path, "w")
      if not f then return false end
      f:write(ser(sanitize(tbl), "")); f:close(); return true
    end)
    if not ok then return false, tostring(r) end
    if r == false then return false, "io.open failed for " .. tostring(path) end
    return true
  end
else
  WRITER_NAME = "NONE"
  write_table = function() return false, "no write backend available" end
end

-- requests are Lua chunks; dofile IS the reader
local function read_request()
  if not dofile then return nil end
  local ok, res = pcall(dofile, REQ)
  if ok and type(res) == "table" then return res end
  return nil
end

----------------------------------------------------------------------
-- 3. ops
----------------------------------------------------------------------
local ops = {}
local TICK = 0

function ops.ping(a)
  return { pong = true, echo = a and a.echo or nil, tick = TICK,
           writer = WRITER_NAME, dir = DIR }
end

function ops.env()
  local c = getcomp()
  return {
    has_io          = io ~= nil,
    has_os_execute  = (os ~= nil and os.execute ~= nil) or false,
    has_bmd         = bmd ~= nil,
    has_writefile   = (bmd and bmd.writefile ~= nil) or false,
    has_dofile      = dofile ~= nil,
    writer          = WRITER_NAME,
    dir             = DIR,
    has_resolve     = RESOLVE ~= nil,
    has_comp        = c ~= nil,
  }
end

function ops.project_info()
  assert(RESOLVE, "no resolve object in this context")
  local pm = RESOLVE:GetProjectManager()
  local pr = pm and pm:GetCurrentProject()
  assert(pr, "no project open")
  local tl = pr:GetCurrentTimeline()
  return {
    product   = RESOLVE:GetProductName(),
    version   = RESOLVE:GetVersionString(),
    project   = pr:GetName(),
    timelines = pr:GetTimelineCount(),
    timeline  = tl and tl:GetName() or nil,
    fps       = pr:GetSetting("timelineFrameRate"),
    width     = pr:GetSetting("timelineResolutionWidth"),
    height    = pr:GetSetting("timelineResolutionHeight"),
  }
end

function ops.comp_info()
  local c = getcomp()
  assert(c, "no current composition -- open the Fusion page on a clip first")
  local attrs = c:GetAttrs() or {}
  local names, count = {}, 0
  for _, tool in pairs(c:GetToolList(false) or {}) do
    count = count + 1
    if count <= 200 then
      local ta = tool:GetAttrs() or {}
      names[#names + 1] = tostring(ta.TOOLS_Name) .. " (" .. tostring(ta.TOOLS_RegID) .. ")"
    end
  end
  return {
    filename    = attrs.COMPS_FileName,
    tool_count  = count,
    tools       = names,
    render_start= attrs.COMPN_RenderStart,
    render_end  = attrs.COMPN_RenderEnd,
    current_time= c.CurrentTime,
  }
end

function ops.add_text(a)
  local c = getcomp(); assert(c, "no current composition")
  c:Lock(); c:StartUndo("MCP add text")
  local t = c:AddTool("TextPlus", a.x or -32768, a.y or -32768)
  assert(t, "AddTool(TextPlus) returned nil")
  t.StyledText[c.CurrentTime] = a.text or "TEST"
  if a.size  then t.Size[c.CurrentTime]  = a.size end
  if a.font  then t.Font[c.CurrentTime]  = a.font end
  if a.style then t.Style[c.CurrentTime] = a.style end
  if a.name  then t:SetAttrs({ TOOLS_Name = a.name }) end
  c:EndUndo(true); c:Unlock()
  return { name = t:GetAttrs().TOOLS_Name, regid = t:GetAttrs().TOOLS_RegID }
end

function ops.animate(a)
  -- a = { tool="Text1", input="Size", keys={ {frame=0,value=0.05}, ... } }
  local c = getcomp(); assert(c, "no current composition")
  local t = c:FindTool(a.tool); assert(t, "tool not found: " .. tostring(a.tool))
  local inp = t[a.input]; assert(inp, "input not found: " .. tostring(a.input))
  c:Lock(); c:StartUndo("MCP animate")
  for _, k in ipairs(a.keys or {}) do inp[k.frame] = k.value end
  c:EndUndo(true); c:Unlock()
  return { tool = a.tool, input = a.input, keys = #(a.keys or {}) }
end

function ops.paste_comp(a)
  -- a = { path = "C:/.../stelios_promo.comp" }  -- the generated node graph
  local c = getcomp(); assert(c, "no current composition")
  assert(a and a.path, "paste_comp needs a path")
  local tbl
  if bmd and bmd.readfile then
    local ok, r = pcall(bmd.readfile, a.path)
    if ok and type(r) == "table" then tbl = r end
  end
  if not tbl and dofile then
    local ok, r = pcall(dofile, a.path)          -- .comp is a bare table -> needs `return`
    if ok and type(r) == "table" then tbl = r end
  end
  assert(tbl, "could not load comp file: " .. tostring(a.path))

  local cleared = 0
  if a.clear ~= false then
    local doomed = {}
    for _, t in pairs(c:GetToolList(false) or {}) do
      local at = t:GetAttrs()
      local id = at and at.TOOLS_RegID
      if id ~= "MediaOut" and id ~= "MediaIn" then doomed[#doomed + 1] = t end
    end
    if #doomed > 0 then
      c:Lock(); c:StartUndo("MCP clear")
      for _, t in ipairs(doomed) do pcall(function() t:Delete() end) end
      c:EndUndo(true); c:Unlock()
      cleared = #doomed
    end
  end

  c:Lock(); c:StartUndo("MCP paste")
  local ok = c:Paste(tbl)
  c:EndUndo(true); c:Unlock()

  -- connect FINAL_OUT to the MediaOut, or the viewer shows nothing
  local connected = false
  local fin = c:FindTool("FINAL_OUT")
  local out
  for _, t in pairs(c:GetToolList(false) or {}) do
    local at = t:GetAttrs()
    if at and at.TOOLS_RegID == "MediaOut" then out = t; break end
  end
  out = out or c:FindTool("MediaOut1")
  if fin and out then
    c:Lock(); c:StartUndo("MCP connect")
    connected = pcall(function() out.Input = fin.Output end)
    c:EndUndo(true); c:Unlock()
  end

  local last = 0
  for _, tool in pairs(tbl.Tools or {}) do
    local go = type(tool) == "table" and tool.Inputs and tool.Inputs.GlobalOut
    local v = type(go) == "table" and go.Value or (type(go) == "number" and go)
    if type(v) == "number" and v > last then last = v end
  end
  if last > 0 then
    pcall(function()
      c:SetAttrs({ COMPN_GlobalStart = 0, COMPN_GlobalEnd = last,
                   COMPN_RenderStart = 0, COMPN_RenderEnd = last })
    end)
  end
  return { pasted = ok and true or false, connected = connected,
           cleared = cleared, last_frame = last, path = a.path }
end

function ops.eval(a)
  local loader = load or loadstring
  local fn, err = loader(a.code); assert(fn, "compile: " .. tostring(err))
  return fn()
end

function ops.stop() return { stopping = true } end

----------------------------------------------------------------------
-- 4. poll loop -- seq numbers instead of file deletion
----------------------------------------------------------------------
local last_seq, handled, stopping = -1, 0, false

local function poll()
  TICK = TICK + 1
  local req = read_request()
  if not req or type(req.seq) ~= "number" or req.seq <= last_seq then return end
  last_seq = req.seq

  local resp
  local h = ops[req.op]
  if not h then
    resp = { seq = req.seq, id = req.id, ok = false, error = "unknown op: " .. tostring(req.op) }
  else
    local ok, result = pcall(h, req.args or {})
    resp = ok and { seq = req.seq, id = req.id, ok = true, result = result }
              or { seq = req.seq, id = req.id, ok = false, error = tostring(result) }
    if ok and req.op == "stop" then stopping = true end
  end
  local wok, werr = write_table(RES, resp)
  handled = handled + 1
  print(("[bridge] #%d seq=%d op=%s ok=%s%s")
        :format(handled, req.seq, tostring(req.op), tostring(resp.ok),
                wok and "" or ("  WRITE FAILED: " .. tostring(werr))))
end

print("=============================================================")
print("[bridge] UP   proto=" .. PROTO)
print("[bridge] dir    = " .. DIR)
print("[bridge] writer = " .. WRITER_NAME)
print("[bridge] reader = " .. (dofile and "dofile" or "NONE"))
print("[bridge] resolve=" .. tostring(RESOLVE ~= nil) .. "  comp=" .. tostring(getcomp() ~= nil))
if WRITER_NAME == "NONE" then
  print("[bridge] FATAL: no write backend. Run probe/fusion_api_probe.lua and send the output.")
  return
end
local hok, herr = write_table(HELLO, { up = true, proto = PROTO, writer = WRITER_NAME, dir = DIR })
if hok and bmd and bmd.fileexists then
  local ok, exists = pcall(bmd.fileexists, HELLO)
  if ok and exists == false then
    hok, herr = false, "write reported success but the file is not on disk"
  end
end
print("[bridge] handshake file: " .. (hok and "OK" or ("FAILED -- " .. tostring(herr))))
print("[bridge]   -> " .. HELLO)
if not hok then
  print("[bridge] FATAL: cannot write to " .. DIR)
  print("[bridge] Create that folder by hand, or edit DIR at the top of this file.")
  return
end
print("[bridge] waiting for requests at " .. REQ)
print("=============================================================")

-- preferred: UIManager timer, which does not block Resolve's UI
local ui = (rawget(G, "fu") and fu.UIManager) or (FU and FU.UIManager)
local ran_ui = false
if ui and bmd and bmd.UIDispatcher then
  ran_ui = pcall(function()
    local disp = bmd.UIDispatcher(ui)
    local win = disp:AddWindow(
      { ID = "MCPBridge", WindowTitle = "MCP Bridge (" .. PROTO .. ")",
        Geometry = { 200, 200, 460, 150 } },
      ui:VGroup{
        ui:Label{ ID = "L1", Text = "Bridge running. Writer: " .. WRITER_NAME },
        ui:Label{ ID = "L2", Text = DIR },
        ui:Button{ ID = "StopBtn", Text = "Stop bridge" },
        ui:Timer{ ID = "Poll", Interval = POLL_MS },
      })
    win.On.Poll.Timeout = function()
      poll()
      if stopping then disp:ExitLoop() end
    end
    win.On.StopBtn.Clicked = function() disp:ExitLoop() end
    win.On.MCPBridge.Close = function() disp:ExitLoop() end
    win:Show(); disp:RunLoop(); win:Hide()
    return true
  end)
end

-- fallback: blocking loop (works from the Console)
if not ran_ui then
  print("[bridge] UIManager unavailable -- falling back to a blocking poll loop.")
  local step = POLL_MS / 1000
  for _ = 1, math.floor(MAX_SECONDS / step) do
    poll()
    if stopping then break end
    if bmd and bmd.wait then bmd.wait(step) else break end
  end
end
print("[bridge] DOWN. handled=" .. handled)
