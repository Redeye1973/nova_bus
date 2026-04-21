import bpy, sys
# factory-reset scene
bpy.ops.wm.read_factory_settings(use_empty=False)
bpy.context.scene.render.resolution_x = 160
bpy.context.scene.render.resolution_y = 120
bpy.context.scene.render.resolution_percentage = 50
bpy.context.scene.render.image_settings.file_format = "PNG"
out = sys.argv[-1]
bpy.ops.wm.save_as_mainfile(filepath=out)
print(f"saved: {out}")
