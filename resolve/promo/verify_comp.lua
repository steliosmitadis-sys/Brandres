-- verify_comp.lua <file.comp>
-- A Fusion .comp IS a Lua expression. This evaluates it with stub constructors
-- (exactly how Fusion's own parser consumes it) and then walks the node graph
-- for dangling links, orphans and malformed splines.

local path = assert((...), "usage: lua verify_comp.lua <file.comp>")
local fh = assert(io.open(path, "r"))
local src = fh:read("a"); fh:close()

-- any unknown global is treated as a tool/value constructor: Name { ... }
local env = { ordered = function() return function(t) return t end end }
setmetatable(env, { __index = function(t, k)
  local fn = function(tbl) tbl = tbl or {}; tbl.__ctor = k; return tbl end
  rawset(t, k, fn); return fn
end })

local chunk, err = load("return " .. src, "comp", "t", env)
if not chunk then print("PARSE FAIL: " .. tostring(err)); os.exit(1) end
local ok, comp = pcall(chunk)
if not ok then print("EVAL FAIL: " .. tostring(comp)); os.exit(1) end

local tools = comp.Tools
if type(tools) ~= "table" then print("FAIL: no Tools table"); os.exit(1) end

local MODIFIER = { BezierSpline = true, XYPath = true, Path = true }
local problems, kinds, n = {}, {}, 0
local edges = {}

for name, t in pairs(tools) do
  n = n + 1
  local kind = t.__ctor or "?"
  kinds[kind] = (kinds[kind] or 0) + 1
  edges[name] = {}

  -- every SourceOp must resolve to a real tool
  for inp, v in pairs(t.Inputs or {}) do
    if type(v) == "table" and v.SourceOp then
      if not tools[v.SourceOp] then
        problems[#problems + 1] = ("%s.%s -> unknown SourceOp %q")
          :format(name, tostring(inp), tostring(v.SourceOp))
      else
        table.insert(edges[name], v.SourceOp)
      end
    end
  end

  -- non-modifier tools need a graph position or they stack at the origin
  if not MODIFIER[kind] and not t.ViewInfo then
    problems[#problems + 1] = name .. " (" .. kind .. ") has no ViewInfo"
  end

  -- spline sanity: >=2 keys, finite handles
  if kind == "BezierSpline" then
    local frames = {}
    for f, kf in pairs(t.KeyFrames or {}) do
      frames[#frames + 1] = f
      if type(kf[1]) ~= "number" then
        problems[#problems + 1] = name .. " key " .. tostring(f) .. " has non-numeric value"
      end
      for _, hnd in ipairs({ "LH", "RH" }) do
        local hv = kf[hnd]
        if hv and (type(hv[1]) ~= "number" or type(hv[2]) ~= "number"
                   or hv[1] ~= hv[1] or hv[2] ~= hv[2]) then
          problems[#problems + 1] = name .. " key " .. tostring(f) .. " has bad " .. hnd
        end
      end
    end
    if #frames < 2 then
      problems[#problems + 1] = name .. " has only " .. #frames .. " keyframe(s)"
    end
  end
end

-- reachability from ActiveTool: catches a scene that never got merged in
local root = comp.ActiveTool
local seen, stack = {}, { root }
if root and tools[root] then
  seen[root] = true
  while #stack > 0 do
    local cur = table.remove(stack)
    for _, dep in ipairs(edges[cur] or {}) do
      if not seen[dep] then seen[dep] = true; stack[#stack + 1] = dep end
    end
  end
  local orphans = {}
  for name in pairs(tools) do
    if not seen[name] then orphans[#orphans + 1] = name end
  end
  table.sort(orphans)
  if #orphans > 0 then
    problems[#problems + 1] = ("%d tool(s) unreachable from ActiveTool %q: %s")
      :format(#orphans, root, table.concat(orphans, ", ", 1, math.min(#orphans, 12))
              .. (#orphans > 12 and " ..." or ""))
  end
else
  problems[#problems + 1] = "ActiveTool missing or not a real tool: " .. tostring(root)
end

-- report
print(("PARSED OK  %s"):format(path))
print(("  tools: %d   ActiveTool: %s"):format(n, tostring(root)))
local ks = {}
for k in pairs(kinds) do ks[#ks + 1] = k end
table.sort(ks)
local line = "  kinds:"
for _, k in ipairs(ks) do line = line .. (" %s=%d"):format(k, kinds[k]) end
print(line)

for _, want in ipairs({ "WORK_01", "WORK_02", "WORK_03", "WORK_04", "WORK_05", "FINAL_OUT" }) do
  print(("  %-10s %s"):format(want, tools[want] and "present" or "*** MISSING ***"))
end

if #problems == 0 then
  print("  problems: none")
else
  print(("  problems: %d"):format(#problems))
  for _, p in ipairs(problems) do print("    - " .. p) end
  os.exit(1)
end
