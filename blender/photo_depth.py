#!/usr/bin/env python3
"""2.5D photo animation: image + depth map -> displaced plane + camera move.

Pipeline: Depth-Anything-V2 (Colab T4, Apache-2.0) writes assets/depth/<id>.png,
this script turns each (photo, depth) pair into a real travelling shot.
No video model, fully deterministic, same grade as the rest of the film.

Usage:
    blender -b --python blender/photo_depth.py -- \\
        --image assets/generated/B00-S01.png --depth assets/depth/B00-S01.png \\
        --move push-in --frames 144 --res 100 --samples 32 \\
        --out out/depth/B00-S01

Moves: push-in | push-out | pan-left | pan-right | drift
"""

import argparse
import sys

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--depth", required=True)
    ap.add_argument("--move", default="push-in",
                    choices=["push-in", "push-out", "pan-left", "pan-right", "drift"])
    ap.add_argument("--frames", type=int, default=144)
    ap.add_argument("--res", type=int, default=100)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--engine", default="eevee", choices=["eevee", "cycles"])
    ap.add_argument("--strength", type=float, default=0.9,
                    help="displacement depth in scene units")
    ap.add_argument("--invert", action="store_true",
                    help="depth map is far=white instead of near=white")
    ap.add_argument("--seed", type=int, default=7001)
    ap.add_argument("--out", default="/tmp/depth-out/shot")
    return ap.parse_args(argv)


ARGS = parse_args()


def safe_set(obj, attr, value):
    try:
        setattr(obj, attr, value)
        return True
    except (AttributeError, TypeError):
        print(f"  [warn] {type(obj).__name__}.{attr} not available, skipped")
        return False


# ---------------------------------------------------------------- build
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
             bpy.data.textures, bpy.data.lights, bpy.data.worlds):
    for x in list(coll):
        coll.remove(x)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = max(1, ARGS.frames)

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
scene.world = world

# photo plane, slightly oversized so camera moves never reveal edges
PW, PH = 7.4, 4.2
bpy.ops.mesh.primitive_grid_add(x_subdivisions=320, y_subdivisions=180,
                                size=1, location=(0, 0, 0))
plane = bpy.context.active_object
plane.name = "Photo"
# NOTE: grid size=1 spans 1x1 units in Blender 5.x (was 2x2 before 4.x?)
plane.scale = (PW, PH, 1)
bpy.ops.object.transform_apply(scale=True)

img = bpy.data.images.load(ARGS.image)
img.colorspace_settings.name = "sRGB"
depth_img = bpy.data.images.load(ARGS.depth)
depth_img.colorspace_settings.name = "Non-Color"

mat = bpy.data.materials.new("PhotoMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()
tex = nodes.new("ShaderNodeTexImage")
tex.image = img
tex.location = (-400, 0)
emi = nodes.new("ShaderNodeEmission")
emi.inputs["Strength"].default_value = 1.0
emi.location = (-100, 0)
out = nodes.new("ShaderNodeOutputMaterial")
out.location = (200, 0)
links.new(tex.outputs["Color"], emi.inputs["Color"])
links.new(emi.outputs["Emission"], out.inputs["Surface"])
plane.data.materials.append(mat)

# depth -> displacement along the camera axis
depth_tex = bpy.data.textures.new("DepthTex", type="IMAGE")
depth_tex.image = depth_img
disp = plane.modifiers.new("Depth", "DISPLACE")
disp.texture = depth_tex
disp.texture_coords = "UV"
disp.direction = "NORMAL"
disp.strength = ARGS.strength
disp.mid_level = 0.0 if not ARGS.invert else 1.0
if ARGS.invert:
    disp.strength = -ARGS.strength

# camera (looks down -Z; plane normal +Z faces it)
bpy.ops.object.camera_add(location=(0, 0, 10))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 55
scene.camera = cam

end = ARGS.frames
MOVES = {
    "push-in": [(1, (0, 0, 10.0)), (end, (0, 0, 8.4))],
    "push-out": [(1, (0, 0, 8.4)), (end, (0, 0, 10.0))],
    "pan-left": [(1, (0.55, 0, 9.4)), (end, (-0.55, 0, 9.4))],
    "pan-right": [(1, (-0.55, 0, 9.4)), (end, (0.55, 0, 9.4))],
    "drift": [(1, (0.3, 0.1, 9.6)), (end // 2, (-0.3, -0.1, 9.2)), (end, (0.15, 0.05, 8.8))],
}
for f, loc in MOVES[ARGS.move]:
    cam.location = loc
    cam.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- render
render = scene.render
render.resolution_x = 1920
render.resolution_y = 1080
render.resolution_percentage = ARGS.res
render.film_transparent = False
render.image_settings.file_format = "PNG"
render.image_settings.color_mode = "RGB"

import os
os.makedirs(ARGS.out, exist_ok=True)
render.filepath = os.path.join(ARGS.out, "frame-####.png")

if ARGS.engine == "cycles":
    render.engine = "CYCLES"
    scene.cycles.samples = ARGS.samples
    scene.cycles.device = "CPU"
    safe_set(scene.cycles, "use_denoising", True)
else:
    try:
        render.engine = "BLENDER_EEVEE"
    except TypeError:
        render.engine = "BLENDER_EEVEE_NEXT"
    safe_set(scene.eevee, "taa_render_samples", ARGS.samples)

# exact photo colors: no filmic curve (the ffmpeg grade owns the look)
try:
    scene.view_settings.view_transform = "Standard"
except TypeError:
    pass

print(f"[depth] {ARGS.image} + {ARGS.depth} | {ARGS.move} | "
      f"frames 1-{ARGS.frames} | {ARGS.engine} | {ARGS.out}", flush=True)
bpy.ops.render.render(animation=True)
print("[depth] render complete", flush=True)
