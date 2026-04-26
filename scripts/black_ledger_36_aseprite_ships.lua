-- 36 intact + 36 damaged top-down **128×128** PNG's naar NOVA Aseprite-outputmap.
-- Run: Aseprite.exe -b --script "L:\!Nova V2\scripts\black_ledger_36_aseprite_ships.lua"

local W, H = 128, 128
local outDir = "L:/! 2 Nova v2 OUTPUT !/! Aseprite"
local latest = outDir .. "/black_ledger_36_latest.txt"

local function C(r, g, b, a)
  return Color { r = r, g = g, b = b, a = a or 255 }
end

local function clearTransparent(img)
  local t = C(0, 0, 0, 0)
  for y = 0, img.height - 1 do
    for x = 0, img.width - 1 do
      img:drawPixel(x, y, t)
    end
  end
end

local function rnd(n, salt)
  local x = math.sin(n * 12.9898 + salt * 78.233) * 43758.5453
  return x - math.floor(x)
end

local function fillRect(img, x0, y0, x1, y1, col)
  for y = y0, y1 do
    for x = x0, x1 do
      if x >= 0 and x < W and y >= 0 and y < H then
        img:drawPixel(x, y, col)
      end
    end
  end
end

local function drawShip(img, n, damaged)
  local cx = math.floor(W / 2)
  local cy = math.floor(H / 2) + 4
  local rh = rnd(n, 1)
  local gh = rnd(n, 2)
  local bh = rnd(n, 3)
  if damaged then
    rh, gh, bh = rh * 0.45, gh * 0.45, bh * 0.45
  end
  local hull = C(math.floor(40 + rh * 80), math.floor(40 + gh * 80), math.floor(50 + bh * 70), 255)
  local wing = C(math.floor(30 + rh * 60), math.floor(60 + gh * 60), math.floor(80 + bh * 60), 255)
  local cock = C(120, 180, 255, damaged and 200 or 255)
  local eng = C(255, 120 + (n % 20), 40, damaged and 140 or 255)
  local scorch = C(25, 12, 8, damaged and 220 or 0)

  -- Hull (diamond / arrow, 2× schaal t.o.v. 64px-versie)
  for dy = -16, 20 do
    local half = math.max(2, 8 + math.floor((20 - math.abs(dy)) * 0.55))
    for dx = -half, half do
      img:drawPixel(cx + dx, cy + dy, hull)
    end
  end
  -- Wings
  local span = damaged and 20 or 28
  for s = -1, 1, 2 do
    for wx = 0, span do
      for wy = -4, 4 do
        img:drawPixel(cx + s * (16 + wx), cy + 4 + wy, wing)
      end
    end
  end
  if damaged then
    for wx = 24, 36 do
      for wy = -2, 2 do
        img:drawPixel(cx + wx, cy + 4 + wy, C(0, 0, 0, 0))
      end
    end
    for dx = -6, 8 do
      for dy = -8, 4 do
        if rnd(n + dx + dy * 7, 9) > 0.35 then
          img:drawPixel(cx + dx + 6, cy + dy - 4, scorch)
        end
      end
    end
  end
  -- Cockpit (breder blok)
  fillRect(img, cx - 2, cy - 6, cx + 2, cy - 3, cock)
  -- Engines 2×2
  fillRect(img, cx - 8, cy + 16, cx - 5, cy + 19, eng)
  fillRect(img, cx + 5, cy + 16, cx + 8, cy + 19, eng)
  if not damaged then
    fillRect(img, cx - 8, cy + 20, cx - 5, cy + 23, C(255, 200, 80, 180))
    fillRect(img, cx + 5, cy + 20, cx + 8, cy + 23, C(255, 200, 80, 180))
  end
  -- Hardpoints (kleine 2px dikke streepjes)
  local hp = 2 + (n % 3)
  for k = 0, hp - 1 do
    if not (damaged and k >= hp - 1) then
      local px = cx + 12 + k * 6
      local py = cy + 10 + k * 2
      local m = C(180, 180, 190, 255)
      fillRect(img, px, py, px + 1, py + 3, m)
      fillRect(img, -px + 2 * cx - 1, py, -px + 2 * cx, py + 3, m)
    end
  end
end

local function saveOne(path, n, damaged)
  local sprite = Sprite(W, H, ColorMode.RGB)
  local layer = sprite.layers[1]
  layer.name = damaged and ("dmg_" .. n) or ("ok_" .. n)
  local cel = sprite:newCel(layer, 1)
  clearTransparent(cel.image)
  drawShip(cel.image, n, damaged)
  app.activeSprite = sprite
  sprite:saveCopyAs(path)
  sprite:close()
end

local lines = {}
for n = 0, 35 do
  local id = string.format("%02d", n + 1)
  local pi = outDir .. "/bl_ship_" .. id .. "_intact.png"
  local pd = outDir .. "/bl_ship_" .. id .. "_damaged.png"
  saveOne(pi, n, false)
  saveOne(pd, n, true)
  table.insert(lines, pi)
  table.insert(lines, pd)
end

local f = io.open(latest, "w")
if f then
  f:write("# black_ledger 36+36 png @128x128\n")
  for _, p in ipairs(lines) do
    f:write(p .. "\n")
  end
  f:close()
end

print("[black_ledger_36_aseprite_ships] wrote 72 PNG 128x128 + " .. latest)
