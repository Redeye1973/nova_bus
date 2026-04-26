-- Smoke test: schrijf minimale sprite naar NOVA Aseprite-outputmap.
-- Run (batch): Aseprite.exe -b --script "L:\!Nova V2\scripts\aseprite_output_sink_probe.lua"
local W, H = 64, 64
local outDir = "L:/! 2 Nova v2 OUTPUT !/! Aseprite"
local outPng = outDir .. "/nova_aseprite_sink.png"
local outAse = outDir .. "/nova_aseprite_sink.aseprite"

local sprite = Sprite(W, H, ColorMode.RGB)
local layer = sprite.layers[1]
layer.name = "sink_probe"
local cel = layer:cel(1)
if cel == nil then
  cel = sprite:newCel(layer, 1)
end
local cx = math.floor(W / 2)
local cy = math.floor(H / 2)
cel.image:drawPixel(cx, cy, Color { r = 255, g = 140, b = 32, a = 255 })
app.activeSprite = sprite
sprite:saveCopyAs(outPng)
sprite:saveAs(outAse)
sprite:close()
print("[aseprite_output_sink_probe] OK " .. outPng)
print("[aseprite_output_sink_probe] OK " .. outAse)
