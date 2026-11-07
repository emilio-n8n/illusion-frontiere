#!/usr/bin/env python3
"""Procedural neural-network scene — L'Illusion de la frontière (shot B01-S03).

Everything is built here: no .blend file, deterministic output (seeded).
Author locally, render on GitHub Actions (see .github/workflows/blender.yml).

Local smoke test (ONE cheap frame, weak machines welcome):
    blender -b --python blender/neural_net.py -- --frames 1 --res 25 --samples 16 --out /tmp/opencode/nn-smoke

Full render (Actions does this):
    blender -b --python blender/neural_net.py -- --frames 144 --res 100 --samples 64 --out out/blender/B01-S03
"""

import argparse
import math
import random
import sys

import bpy
from mathutils import Vector


# ---------------------------------------------------------------- args
def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=144)
    ap.add_argument("--frame-start", type=int, default=None, help="render from this frame")
    ap.add_argument("--frame-end", type=int, default=None, help="render up to this frame")
    ap.add_argument("--res", type=int, default=100, help="resolution percentage")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--engine", default="eevee", choices=["eevee", "cycles"])
    ap.add_argument("--device", default="CPU", choices=["CPU", "CUDA", "OPTIX"],
                    help="cycles compute device (Colab T4: OPTIX)")
    ap.add_argument("--seed", type=int, default=7001)
    ap.add_argument("--out", default="/tmp/blender-out/B01-S03")
    return ap.parse_args(argv)


ARGS = parse_args()
rng = random.Random(ARGS.seed)


def safe_set(obj, attr, value):
    """Set a render property if it exists in this Blender version, else skip."""
    try:
        setattr(obj, attr, value)
        return True
    except (AttributeError, TypeError):
        print(f"  [warn] {type(obj).__name__}.{attr} not available, skipped")
        return False


# ---------------------------------------------------------------- scene setup
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights):
        for x in list(coll):
            coll.remove(x)


def emission_mat(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    emi = nodes.new("ShaderNodeEmission")
    emi.location = (0, 0)
    emi.inputs["Color"].default_value = (*color, 1.0)
    emi.inputs["Strength"].default_value = strength
    links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return mat


def principled_mat(name, base_color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


# ---------------------------------------------------------------- build
clear_scene()
scene = bpy.context.scene
scene.frame_start = ARGS.frame_start if ARGS.frame_start is not None else 1
scene.frame_end = ARGS.frame_end if ARGS.frame_end is not None else max(1, ARGS.frames)

BLUE = (0.20, 0.45, 0.55)
BLUE_DIM = (0.10, 0.22, 0.28)
BURGUNDY = (0.45, 0.06, 0.07)
PULSE = (0.75, 0.92, 0.95)

mat_blue = emission_mat("NodeBlue", BLUE, 3.0)
mat_blue_dim = emission_mat("NodeBlueDim", BLUE_DIM, 0.9)
mat_red = emission_mat("NodeRed", BURGUNDY, 4.0)
mat_edge = emission_mat("Edge", (0.16, 0.30, 0.36), 0.5)
mat_pulse = emission_mat("Pulse", PULSE, 9.0)
mat_floor = principled_mat("Floor", (0.012, 0.018, 0.024), metallic=0.55, roughness=0.42)

# world: near-black blue
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.020, 0.028, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world

# floor
bpy.ops.mesh.primitive_plane_add(size=70, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(mat_floor)

# --- node layers (x = depth, camera dollies along +X) ---
LAYERS = [6, 5, 4]
XS = [-3.0, 0.5, 4.0]
nodes = []  # (Vector, object)
for li, (count, x) in enumerate(zip(LAYERS, XS)):
    for i in range(count):
        y = (i - (count - 1) / 2) * 0.95 + rng.uniform(-0.08, 0.08)
        z = 1.15 + rng.uniform(-0.25, 0.25) + (0.12 if i % 2 else 0.0)
        pos = Vector((x, y, z))
        hero_red = (li == 0 and i == 2) or (li == 1 and i == 1)
        hero_blue = (li == 2 and i == 1)
        mat = mat_red if hero_red else (mat_blue if (hero_blue or (li == 1)) else mat_blue_dim)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.22, location=pos)
        ob = bpy.context.active_object
        ob.name = f"Node-L{li}-{i}"
        ob.data.materials.append(mat)
        # gentle breathing (scale keys)
        mid = max(2, ARGS.frames // 2)
        s_mid = 1.10 if (i + li) % 2 == 0 else 0.94
        for f, s in ((1, 1.0), (mid, s_mid), (ARGS.frames, 1.0)):
            ob.scale = (s, s, s)
            ob.keyframe_insert("scale", frame=f)
        nodes.append((pos, ob))

# --- edges: thin emissive cylinders between consecutive layers ---
def cylinder_between(a, b, radius, mat, name):
    d = b - a
    length = d.length
    mid = (a + b) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=1, location=mid)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.scale = (1, 1, length)
    ob.data.materials.append(mat)
    return ob


layer_nodes = []
k = 0
for count in LAYERS:
    layer_nodes.append(nodes[k:k + count])
    k += count

edges = []
for l in range(len(layer_nodes) - 1):
    for a_pos, _ in layer_nodes[l]:
        for b_pos, _ in layer_nodes[l + 1]:
            edges.append((a_pos, b_pos))
            cylinder_between(a_pos, b_pos, 0.02, mat_edge, f"Edge-{l}-{len(edges)}")

# --- signal pulses travelling along random edges ---
PULSES = 12
TRAVEL = 44  # frames per crossing
chosen = rng.sample(edges, min(PULSES, len(edges)))
for p, (a, b) in enumerate(chosen):
    offset = p * 4
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.07, location=a)
    ob = bpy.context.active_object
    ob.name = f"Pulse-{p}"
    ob.data.materials.append(mat_pulse)
    f = 1
    while f <= ARGS.frames:
        t = ((f + offset) % TRAVEL) / TRAVEL
        ob.location = a.lerp(b, t)
        ob.keyframe_insert("location", frame=f)
        f += 6

# --- hero node glow pulse (emission strength keys) ---
for node_name, base in (("Node-L0-2", 4.0), ("Node-L1-1", 4.0)):
    ob = bpy.data.objects.get(node_name)
    if ob is None:
        continue
    emi = ob.data.materials[0].node_tree.nodes.get("Emission")
    if emi is None:
        continue
    # NOTE: shared material would pulse every user; heroes share mat_red,
    # so copy it to keep the pulse local.
    hero_mat = ob.data.materials[0].copy()
    hero_mat.name += "-hero"
    ob.data.materials.clear()
    ob.data.materials.append(hero_mat)
    emi = hero_mat.node_tree.nodes.get("Emission")
    for f, v in ((1, base), (max(2, ARGS.frames // 3), base * 1.7),
                 (max(3, 2 * ARGS.frames // 3), base * 0.8), (ARGS.frames, base)):
        emi.inputs["Strength"].default_value = v
        emi.inputs["Strength"].keyframe_insert("default_value", frame=f)

# --- lights: dim blue area + burgundy accent ---
bpy.ops.object.light_add(type="AREA", location=(-6, -5, 6))
key = bpy.context.active_object
key.name = "KeyBlue"
key.data.energy = 900
key.data.color = (0.45, 0.65, 0.80)
key.data.size = 6.0

bpy.ops.object.light_add(type="POINT", location=(5.5, 3.0, 2.5))
acc = bpy.context.active_object
acc.name = "AccentRed"
acc.data.energy = 350
acc.data.color = (0.60, 0.08, 0.08)
safe_set(acc.data, "shadow_soft_size", 0.6)

# --- camera: slow dolly + sway, tracked on the mid layer ---
bpy.ops.object.camera_add(location=(-11, 0, 1.3))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 55
safe_set(cam.data, "clip_start", 0.1)
scene.camera = cam

bpy.ops.object.empty_add(location=(1.5, 0, 1.1))
focus = bpy.context.active_object
focus.name = "Focus"
track = cam.constraints.new("TRACK_TO")
track.target = focus
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"

mid = max(2, ARGS.frames // 2)
for f, loc in ((1, (-12.5, 0, 1.60)), (mid, (-10.0, 0.35, 1.70)), (ARGS.frames, (-7.5, 0, 1.60))):
    cam.location = loc
    cam.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- render settings
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
    cycles = scene.cycles
    cycles.samples = ARGS.samples
    if ARGS.device == "CPU":
        cycles.device = "CPU"
    else:
        # headless GPU (Colab T4): enable the compute device in prefs first.
        # Blender 5.x: prefs choose OPTIX/CUDA, the scene selector is just GPU.
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = ARGS.device  # OPTIX or CUDA
            prefs.get_devices()
            for d in prefs.devices:
                d.use = (d.type != "CPU")
            cycles.device = "GPU"
        except Exception as exc:
            print(f"  [warn] gpu setup ({exc}), falling back to CPU")
            cycles.device = "CPU"
    safe_set(cycles, "use_denoising", True)
    # cheap scene: emissive materials barely need indirect bounces
    safe_set(cycles, "diffuse_bounces", 2)
    safe_set(cycles, "glossy_bounces", 2)
    safe_set(cycles, "transmission_bounces", 0)
else:
    try:
        render.engine = "BLENDER_EEVEE"
    except TypeError:
        render.engine = "BLENDER_EEVEE_NEXT"
    ee = scene.eevee
    safe_set(ee, "taa_render_samples", ARGS.samples)
    safe_set(ee, "taa_samples", max(1, ARGS.samples // 4))
    # NOTE (Blender 5.x): EEVEE has no bloom setting. The glow and the film
    # grade are applied later in ffmpeg (see .github/workflows/blender.yml), so
    # every shot — Blender or not — shares the same look.
    safe_set(ee, "use_shadows", True)

# --- view transform / grade (raw render; glow is post-processed) ---
vs = scene.view_settings
try:
    vs.view_transform = "AgX"
except TypeError:
    vs.view_transform = "Filmic"
safe_set(vs, "exposure", -0.4)

print(f"[scene] {len(nodes)} nodes, {len(edges)} edges, {PULSES} pulses, "
      f"frames 1-{ARGS.frames}, res {ARGS.res}%, {ARGS.engine}, out {ARGS.out}", flush=True)

bpy.ops.render.render(animation=True)
print("[scene] render complete", flush=True)
