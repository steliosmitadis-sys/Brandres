--[[
  mock_resolve_free.lua -- reproduce Resolve 21.1 Free's Lua sandbox.

  Loads the real resolve_bridge_free.lua into an environment where
  io == nil, os.execute == nil, os.remove == nil and os.getenv == nil,
  exactly as reported on Resolve 21.1 Free / Windows 11, with bmd.* and a
  fake resolve/comp supplied. This lets the transport be regression-tested
  with no Resolve install.

  usage: lua5.4 mock_resolve_free.lua <bridge.lua> <tempdir>
]]

io.stdout:setvbuf("line")
local bridge_path = assert((...), "need bridge path")
local tempdir = assert(select(2, ...), "need tempdir")

-- capture the real primitives BEFORE sandboxing; the sandbox never sees them
local real_io, real_clock, real_time = io, os.clock, os.time

local function raw_write(path, s)
  local f = real_io.open(path, "w"); if not f then return false end
  f:write(s); f:close(); return true
end

-- serializer standing in for Fusion's bmd.writefile
local function ser(v, ind)
  local t = type(v)
  if t == "string" then return string.format("%q", v) end
  if t == "number" or t == "boolean" then return tostring(v) end
  if t ~= "table" then return string.format("%q", tostring(v)) end
  local parts, keys = { "{" }, {}
  for k in pairs(v) do keys[#keys + 1] = k end
  table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
  for _, k in ipairs(keys) do
    local key = type(k) == "string" and (k .. " = ") or ""
    parts[#parts + 1] = ind .. "\t" .. key .. ser(v[k], ind .. "\t") .. ","
  end
  parts[#parts + 1] = ind .. "}"
  return table.concat(parts, "\n")
end

local bmd = {
  writefile = function(path, tbl) return raw_write(path, ser(tbl, "")) end,
  -- Fusion's bmd.readfile understands the ASCII format's constructors
  -- (Input{}, FuID{}, Clip{}, ordered(), tool names). An empty environment
  -- would reject every real .comp, so synthesize them the way Fusion does.
  readfile  = function(path)
    local f = real_io.open(path, "r"); if not f then return nil end
    local s = f:read("a"); f:close()
    local env = { ordered = function() return function(t) return t end end }
    setmetatable(env, { __index = function(t, k)
      local ctor = function(tbl) tbl = tbl or {}; tbl.__ctor = k; return tbl end
      rawset(t, k, ctor); return ctor
    end })
    local fn = load("return " .. s, "rf", "t", env)
    if not fn then return nil end
    local ok, r = pcall(fn); return ok and r or nil
  end,
  createdir = function(p) return os.execute('mkdir -p "' .. p .. '"') and true or false end,
  fileexists = function(p)
    local f = real_io.open(p, "r"); if f then f:close(); return true end; return false
  end,
  wait = function(sec)
    local t0 = real_clock()
    while real_clock() - t0 < sec do end
  end,
}

-- fake tool: any input name auto-creates a keyframe table.
-- Renaming via SetAttrs{TOOLS_Name=...} must also re-key the comp's tool table,
-- because that is what Fusion does -- comp:FindTool() looks up the CURRENT name.
local tools = {}
local function faketool(name, regid)
  local attrs = { TOOLS_Name = name, TOOLS_RegID = regid }
  local self
  self = setmetatable({
    GetAttrs = function() return attrs end,
    Delete = function() tools[attrs.TOOLS_Name] = nil; return true end,
    SetAttrs = function(_, t)
      for k, v in pairs(t) do
        if k == "TOOLS_Name" and v ~= attrs.TOOLS_Name then
          tools[attrs.TOOLS_Name] = nil
          tools[v] = self
        end
        attrs[k] = v
      end
      return true
    end,
  }, { __index = function(t, k) local v = {}; rawset(t, k, v); return v end })
  return self
end

tools.Background1 = faketool("Background1", "Background")
tools.MediaOut1 = faketool("MediaOut1", "MediaOut")
local ntools = 2

local comp = {
  CurrentTime = 0,
  Lock = function() end, Unlock = function() end,
  StartUndo = function() end, EndUndo = function() end,
  GetAttrs = function() return { COMPS_FileName = "mock.comp",
                                 COMPN_RenderStart = 0, COMPN_RenderEnd = 719 } end,
  GetToolList = function() return tools end,
  FindTool = function(_, n) return tools[n] end,
  AddTool = function(_, regid)
    ntools = ntools + 1
    local n = regid .. tostring(ntools)
    tools[n] = faketool(n, regid); return tools[n]
  end,
  -- Fusion's Paste really does add the tools, so FindTool() must see them
  -- afterwards; a stub that just returns true would leave the caller's
  -- connect-up step silently untested.
  Paste = function(_, t)
    if type(t) ~= "table" then return false end
    for name, tool in pairs(t.Tools or {}) do
      local regid = (type(tool) == "table" and tool.__ctor) or "Unknown"
      tools[name] = faketool(name, regid)
      ntools = ntools + 1
    end
    return true
  end,
}

local project = {
  GetName = function() return "MOCK_PROJECT" end,
  GetTimelineCount = function() return 1 end,
  GetCurrentTimeline = function() return { GetName = function() return "Timeline 1" end } end,
  GetSetting = function(_, k)
    return ({ timelineFrameRate = "30", timelineResolutionWidth = "1080",
              timelineResolutionHeight = "1920" })[k]
  end,
}
local resolve = {
  GetProductName = function() return "DaVinci Resolve" end,
  GetVersionString = function() return "21.1.0 (mock)" end,
  GetProjectManager = function()
    return { GetCurrentProject = function() return project end }
  end,
}
local fusion = {
  MapPath = function(_, p) return p == "Temp:/" and tempdir or p end,
  GetCurrentComp = function() return comp end,
  GetResolve = function() return resolve end,
}

-- the sandbox: a trimmed os, NO io, NO os.execute/remove/getenv
local sandbox_os = { clock = nil, date = os.date, difftime = os.difftime }
local S = {
  bmd = bmd, fusion = fusion, fu = fusion, app = fusion,
  resolve = resolve, comp = comp,
  os = sandbox_os, io = nil,
  print = print, pairs = pairs, ipairs = ipairs, type = type, tostring = tostring,
  tonumber = tonumber, string = string, table = table, math = math,
  pcall = pcall, select = select, error = error, assert = assert,
  rawget = rawget, rawset = rawset, setmetatable = setmetatable,
  load = load, dofile = dofile, require = require, unpack = table.unpack,
}
S._G = S

print("[mock] sandbox: io=" .. tostring(S.io)
      .. "  os.execute=" .. tostring(S.os.execute)
      .. "  os.remove=" .. tostring(S.os.remove)
      .. "  os.getenv=" .. tostring(S.os.getenv))

local f = assert(real_io.open(bridge_path, "r"))
local src = f:read("a"); f:close()
local chunk = assert(load(src, "@" .. bridge_path, "t", S))
chunk()
print("[mock] bridge returned")
