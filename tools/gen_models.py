#!/usr/bin/env python3
"""
3D asset generator for The Eighth Day's custom blocks.

Builds each workstation as real geometry in Blender, bakes its procedural
materials to image textures, exports an FBX for Unity, and renders the item
icon from the same model - so the thing in your hand matches the thing on the
ground.

    python3 tools/gen_models.py                    # every asset
    python3 tools/gen_models.py --only edBlockBloomery
    python3 tools/gen_models.py --no-bake          # previews and icons only, fast

Outputs per asset:
    TheEighthDay/Resources/src/<name>/<name>.fbx          model, Y-up, metres
    TheEighthDay/Resources/src/<name>/<name>_BaseColor.png
    TheEighthDay/Resources/src/<name>/<name>_Normal.png    tangent space, OpenGL
    TheEighthDay/Resources/src/<name>/<name>_Roughness.png invert for Unity smoothness
    TheEighthDay/Resources/src/<name>/<name>_Metallic.png
    TheEighthDay/UIAtlases/ItemIconAtlas/<name>.png        160px icon
    dist/previews/<name>.png                               480px review render

The FBX + textures go through Unity on your desktop to become an AssetBundle -
see tools/unity/ and docs/ART.md. Nothing in the mod depends on that step
having happened: blocks keep their vanilla mesh until a Meshfile is wired.

SCALE: 7 Days to Die blocks are 1 m cubes. Every asset is normalised so its
footprint fits inside 1 m and its origin is at the base centre, which is where
the game expects a block's pivot.

Requires:  pip install bpy   (Blender 5.x as a Python module, CPython 3.11)
"""

from __future__ import annotations

import argparse
import math
import random
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_icons_blender as G  # noqa: E402  scene, camera, lights, primitives

REPO_ROOT = Path(__file__).resolve().parent.parent
MOD = REPO_ROOT / "TheEighthDay"
SRC_OUT = MOD / "Resources" / "src"
ICON_OUT = MOD / "UIAtlases" / "ItemIconAtlas"
PREVIEW_OUT = REPO_ROOT / "dist" / "previews"

ICON_SIZE = 160
BAKE_SIZE = 1024
TARGET_TRIS = 9000        # vanilla workstations are a few thousand; this is generous
R = math.radians


# ==========================================================================
# materials - weathered, two-tone, optional soot gradient
# ==========================================================================

def _link(nt, a, b):
    nt.links.new(a, b)


def weathered(name, col_a, col_b, roughness=0.9, mottle_scale=3.0,
              soot_from=None, soot_to=None, bump=1.2, bump_scale=8.0,
              metallic=0.0, emission=None):
    """Two-tone noise mottle, roughness break-up, fine bump, optional
    height-driven soot. Uniform colour and uniform roughness are the two
    biggest CG tells, and this kills both."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    mat["ed_metallic"] = metallic          # remembered for the metallic bake

    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = mottle_scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.65
    _link(nt, coord.outputs["Object"], noise.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[0].color = col_a
    ramp.color_ramp.elements[1].color = col_b
    _link(nt, noise.outputs["Fac"], ramp.inputs["Fac"])
    colour_out = ramp.outputs["Color"]

    if soot_from is not None:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        _link(nt, coord.outputs["Object"], sep.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = soot_from
        mr.inputs["From Max"].default_value = soot_to
        _link(nt, sep.outputs["Z"], mr.inputs["Value"])
        n2 = nt.nodes.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = 6.0
        _link(nt, coord.outputs["Object"], n2.inputs["Vector"])
        madd = nt.nodes.new("ShaderNodeMath")
        madd.operation = "MULTIPLY_ADD"
        _link(nt, n2.outputs["Fac"], madd.inputs[0])
        madd.inputs[1].default_value = 0.8
        madd.inputs[2].default_value = 0.3
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        _link(nt, mr.outputs["Result"], mul.inputs[0])
        _link(nt, madd.outputs["Value"], mul.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        _link(nt, mul.outputs["Value"], mix.inputs["Factor"])
        _link(nt, colour_out, mix.inputs[6])
        mix.inputs[7].default_value = (0.015, 0.013, 0.012, 1)
        colour_out = mix.outputs[2]

    _link(nt, colour_out, bsdf.inputs["Base Color"])

    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = max(0.25, roughness - 0.25)
    rr.inputs["To Max"].default_value = min(1.0, roughness + 0.08)
    _link(nt, noise.outputs["Fac"], rr.inputs["Value"])
    _link(nt, rr.outputs["Result"], bsdf.inputs["Roughness"])

    bn = nt.nodes.new("ShaderNodeTexNoise")
    bn.inputs["Scale"].default_value = bump_scale
    bn.inputs["Detail"].default_value = 10.0
    _link(nt, coord.outputs["Object"], bn.inputs["Vector"])
    bump_node = nt.nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = bump
    bump_node.inputs["Distance"].default_value = 0.04
    _link(nt, bn.outputs["Fac"], bump_node.inputs["Height"])
    _link(nt, bump_node.outputs["Normal"], bsdf.inputs["Normal"])

    if emission:
        bsdf.inputs["Emission Color"].default_value = emission[0]
        bsdf.inputs["Emission Strength"].default_value = emission[1]
    return mat


def ember_light(loc, energy=60):
    ld = bpy.data.lights.new("ember", "POINT")
    ld.energy = energy
    ld.color = (1.0, 0.45, 0.12)
    ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("ember", ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    return lo


# ==========================================================================
# asset builders - each returns a list of mesh objects, built in metres-ish
# and normalised afterwards
# ==========================================================================

def build_bloomery():
    """Clay shaft furnace on a fieldstone skirt.

    The body runs to the ground and the stones lean against it - v1 floated
    because the body started at z=0.25 inside a ring of 0.28 m stones."""
    rng = random.Random(8)
    parts = []

    clay = weathered("edm_clay", G.hexc("#9a7654"), G.hexc("#6e5138"), 0.93,
                     mottle_scale=2.4, soot_from=1.5, soot_to=2.5, bump=1.4, bump_scale=7)
    stones = [weathered(f"edm_stone{i}", G.hexc(a), G.hexc(b), 0.96, 5, bump=1.8, bump_scale=10)
              for i, (a, b) in enumerate((("#7a746b", "#55504a"), ("#6d665c", "#4a453f"),
                                          ("#837c72", "#5e5850")))]
    soot = weathered("edm_soot", (0.02, 0.018, 0.016, 1), (0.05, 0.045, 0.04, 1), 0.98,
                     bump=0.8, bump_scale=14)
    iron = weathered("edm_iron", G.hexc("#4c4845"), G.hexc("#2e2b29"), 0.62, 8,
                     bump=0.6, bump_scale=18, metallic=0.85)
    ember = weathered("edm_ember", (1, 0.35, 0.05, 1), (1, 0.2, 0.02, 1), 0.6,
                      emission=((1.0, 0.30, 0.03, 1), 9.0))

    # body to the ground
    body = G.spin_profile([
        (0.00, 0.00), (0.84, 0.00), (0.90, 0.30), (0.89, 0.85),
        (0.82, 1.30), (0.68, 1.80), (0.54, 2.20), (0.47, 2.45), (0.00, 2.45),
    ], segments=64)
    G.subsurf(body, 2)
    G.displace(body, strength=0.09, scale=0.55, noise_type="CLOUDS")
    parts.append(G.assign(body, clay))

    # fieldstone skirt, pressed against the body
    for i in range(15):
        a = i / 15 * math.tau + rng.uniform(-0.05, 0.05)
        w, d, h = rng.uniform(0.32, 0.44), rng.uniform(0.28, 0.38), rng.uniform(0.24, 0.34)
        rad = 0.84 + d * 0.42
        s = G.cube(1.0, loc=(math.cos(a) * rad, math.sin(a) * rad, h / 2 - 0.01),
                   scale=(w, d, h), rot=(rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), a))
        G.subsurf(s, 2)
        G.displace(s, strength=0.16, scale=0.35, noise_type="CLOUDS")
        parts.append(G.assign(s, rng.choice(stones)))

    throat = G.spin_profile([(0.0, 2.44), (0.31, 2.44), (0.31, 1.9), (0.22, 1.2), (0.0, 1.2)],
                            segments=32)
    parts.append(G.assign(throat, soot))
    rim = G.torus(0.40, 0.10, loc=(0, 0, 2.43))
    G.displace(rim, strength=0.05, scale=0.3, noise_type="CLOUDS")
    parts.append(G.assign(rim, soot))

    arch = G.cube(1.0, loc=(0, -0.86, 0.40), scale=(0.36, 0.22, 0.40))
    G.bevel(arch, 0.06, 4)
    parts.append(G.assign(arch, soot))
    parts.append(G.assign(G.sphere(0.16, loc=(0, -0.80, 0.40)), ember))
    ember_light((0, -0.98, 0.42))

    pipe = G.cylinder(0.075, 0.95, loc=(0.97, -0.36, 0.74), rot=(0, R(90), R(-22)))
    parts.append(G.assign(pipe, iron))
    flange = G.cylinder(0.135, 0.06, loc=(0.79, -0.43, 0.74), rot=(0, R(90), R(-22)))
    G.bevel(flange, 0.01, 2)
    parts.append(G.assign(flange, iron))
    for z, r in ((0.98, 0.875), (1.68, 0.71)):
        parts.append(G.assign(G.torus(r, 0.03, loc=(0, 0, z)), iron))
    return parts


def build_blast_furnace():
    """Square refractory-brick stack in a riveted steel frame.

    Deliberately nothing like the bloomery: square not round, brick not clay,
    steel-framed, with a charging hood. The two currently share a mesh in-game
    and are indistinguishable; the silhouette has to carry the difference."""
    parts = []

    brick = weathered("edm_brick", G.hexc("#6b3a2e"), G.hexc("#3f241d"), 0.95,
                      mottle_scale=6, soot_from=1.1, soot_to=1.9, bump=1.6, bump_scale=14)
    steel = weathered("edm_steel", G.hexc("#4a4d52"), G.hexc("#2b2d31"), 0.55, 7,
                      bump=0.7, bump_scale=16, metallic=0.9)
    rust = weathered("edm_rust", G.hexc("#6b3f22"), G.hexc("#3a2414"), 0.9, 5,
                     bump=1.2, bump_scale=12, metallic=0.4)
    concrete = weathered("edm_concrete", G.hexc("#7c7871"), G.hexc("#5a5650"), 0.97, 4,
                         bump=1.5, bump_scale=9)
    ember = weathered("edm_ember2", (1, 0.35, 0.05, 1), (1, 0.2, 0.02, 1), 0.6,
                      emission=((1.0, 0.30, 0.03, 1), 9.0))

    # plinth
    plinth = G.cube(1.0, loc=(0, 0, 0.09), scale=(1.06, 1.06, 0.18))
    G.bevel(plinth, 0.02, 2)
    parts.append(G.assign(plinth, concrete))

    # brick stack: square frustum. SIMPLE subdivision adds the geometry the
    # displace needs WITHOUT rounding the corners - Catmull-Clark on a 4-sided
    # cone turns it into an egg, which is exactly what v1 shipped. Sized so the
    # corner posts bite into it rather than standing clear of it.
    stack = G.cone(r1=0.68, r2=0.52, depth=1.55, loc=(0, 0, 0.18 + 1.55 / 2),
                   rot=(0, 0, R(45)), verts=4)
    G.bevel(stack, 0.025, 2)
    sub = stack.modifiers.new("subsurf", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 3
    G.displace(stack, strength=0.025, scale=0.22, noise_type="CLOUDS")
    parts.append(G.assign(stack, brick))

    # steel corner posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            post = G.cube(1.0, loc=(sx * 0.46, sy * 0.46, 0.18 + 0.80), scale=(0.07, 0.07, 1.60))
            G.bevel(post, 0.012, 2)
            parts.append(G.assign(post, steel))

    # steel bands (four flat bars each)
    for z, half in ((0.45, 0.455), (0.95, 0.42), (1.45, 0.375)):
        for i in range(4):
            a = i * math.pi / 2
            b = G.cube(1.0, loc=(math.cos(a) * half, math.sin(a) * half, z),
                       scale=(0.05, half * 2 + 0.05, 0.10), rot=(0, 0, a))
            G.bevel(b, 0.008, 2)
            parts.append(G.assign(b, rust if z < 1.0 else steel))
            # rivets - low-poly; 48 of them at default sphere resolution was
            # most of the 107k-triangle bill
            for t in (-0.6, -0.2, 0.2, 0.6):
                rv = G.sphere(0.022, loc=(math.cos(a) * (half + 0.03) - math.sin(a) * t * half,
                                         math.sin(a) * (half + 0.03) + math.cos(a) * t * half, z),
                              segs=10, rings=5)
                parts.append(G.assign(rv, steel))

    # charging hood and chute
    hood = G.cylinder(0.30, 0.22, loc=(0, 0, 1.73 + 0.11), verts=32)
    G.bevel(hood, 0.02, 3)
    parts.append(G.assign(hood, steel))
    chimney = G.cylinder(0.11, 0.55, loc=(0.16, 0.12, 1.95 + 0.27), verts=24)
    parts.append(G.assign(chimney, rust))
    # charging chute, leaning into the hood rather than floating beside it
    chute = G.cube(1.0, loc=(-0.30, -0.20, 1.86), scale=(0.22, 0.18, 0.62),
                   rot=(R(24), 0, R(-38)))
    G.bevel(chute, 0.015, 2)
    parts.append(G.assign(chute, steel))

    # tuyeres, both sides low on the stack
    for sx in (-1, 1):
        pipe = G.cylinder(0.055, 0.55, loc=(sx * 0.72, 0.10, 0.62), rot=(0, R(90), 0))
        parts.append(G.assign(pipe, rust))
        fl = G.cylinder(0.10, 0.05, loc=(sx * 0.62, 0.10, 0.62), rot=(0, R(90), 0))
        parts.append(G.assign(fl, steel))

    # tap hole with glow
    tap = G.cube(1.0, loc=(0, -0.60, 0.42), scale=(0.28, 0.16, 0.26))
    G.bevel(tap, 0.03, 3)
    parts.append(G.assign(tap, steel))
    parts.append(G.assign(G.sphere(0.10, loc=(0, -0.60, 0.42)), ember))
    ember_light((0, -0.72, 0.44), 45)
    return parts


ASSETS = {
    "edBlockBloomery": build_bloomery,
    "edBlockBlastFurnace": build_blast_furnace,
}


# ==========================================================================
# normalise, bake, export
# ==========================================================================

def bounds(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        ev = o.evaluated_get(dg)
        for v in ev.bound_box:
            w = ev.matrix_world @ Vector(v)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def normalise(objs, footprint=0.98):
    """Uniformly scale so the XY footprint fits in `footprint` metres and the
    base sits at z=0 centred on the origin - a 7DTD block pivot."""
    lo, hi = bounds(objs)
    size = hi - lo
    s = footprint / max(size.x, size.y)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in objs:
        o.location = (o.location - centre) * s
        o.scale = o.scale * s
    for l in [o for o in bpy.context.scene.objects if o.type == "LIGHT" and o.name.startswith("ember")]:
        l.location = (Vector(l.location) - centre) * s
    return s


def tri_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimate_to(obj, target: int) -> int:
    """Collapse-decimate down to roughly `target` triangles.

    Subdivision and displacement make good renders and terrible game meshes.
    Vanilla workstations are a few thousand tris; the first blast furnace came
    out at 107k. Runs BEFORE UV projection so the UVs fit the final mesh."""
    before = tri_count(obj)
    if before <= target:
        return before
    m = obj.modifiers.new("decimate", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = target / before
    m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    return tri_count(obj)


def join_for_export(objs, target_tris: int):
    """Apply modifiers, join into one mesh, decimate to budget, unwrap."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target="MESH")          # applies modifiers
    bpy.ops.object.join()
    joined = bpy.context.object

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")

    before = tri_count(joined)
    after = decimate_to(joined, target_tris)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=R(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"  mesh: {before} -> {after} tris")
    return joined


def bake_maps(obj, name, out_dir: Path, size=BAKE_SIZE):
    """Bake BaseColor, Roughness, Normal and Metallic to PNGs.

    Every material on the object gets an image node pointing at the same
    target image, set active, so a single bake covers the whole mesh."""
    sc = bpy.context.scene
    sc.cycles.samples = 24
    sc.render.bake.margin = 8
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    mats = [s.material for s in obj.material_slots if s.material]
    nodes_added = []

    def target(img):
        for m in mats:
            nt = m.node_tree
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            nt.nodes.active = tex
            nodes_added.append((nt, tex))

    def cleanup():
        while nodes_added:
            nt, tex = nodes_added.pop()
            nt.nodes.remove(tex)

    def save(img, suffix):
        # GOTCHA: do NOT touch img.colorspace_settings after baking. On a
        # generated image that regenerates the buffer and silently discards
        # the bake - every map comes out solid black with no error. Colour
        # space is decided at creation via is_data instead.
        img.filepath_raw = str(out_dir / f"{name}_{suffix}.png")
        img.file_format = "PNG"
        img.save()

    # BaseColor
    img = bpy.data.images.new("bake_color", size, size)
    target(img)
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True
    bpy.ops.object.bake(type="DIFFUSE")
    save(img, "BaseColor")
    cleanup()

    # Roughness
    img = bpy.data.images.new("bake_rough", size, size, is_data=True)
    target(img)
    bpy.ops.object.bake(type="ROUGHNESS")
    save(img, "Roughness")
    cleanup()

    # Normal (tangent, OpenGL convention - Unity imports this directly)
    img = bpy.data.images.new("bake_normal", size, size, is_data=True)
    target(img)
    sc.render.bake.normal_space = "TANGENT"
    bpy.ops.object.bake(type="NORMAL")
    save(img, "Normal")
    cleanup()

    # Metallic - not a bake type, so route each material's constant through
    # emission and bake EMIT.
    saved = []
    for m in mats:
        b = m.node_tree.nodes["Principled BSDF"]
        saved.append((b, b.inputs["Emission Color"].default_value[:],
                      b.inputs["Emission Strength"].default_value))
        mv = float(m.get("ed_metallic", 0.0))
        # disconnect anything driving emission colour
        for l in list(m.node_tree.links):
            if l.to_socket == b.inputs["Emission Color"]:
                m.node_tree.links.remove(l)
        b.inputs["Emission Color"].default_value = (mv, mv, mv, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    img = bpy.data.images.new("bake_metal", size, size, is_data=True)
    target(img)
    bpy.ops.object.bake(type="EMIT")
    save(img, "Metallic")
    cleanup()
    for b, col, strength in saved:
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = strength


def export_fbx(obj, path: Path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
        mesh_smooth_type="FACE", use_mesh_modifiers=True, path_mode="STRIP",
        embed_textures=False, add_leaf_bones=False, bake_anim=False,
    )


def render_to(path: Path, size: int, ortho: float, cam_loc, samples=128):
    sc = bpy.context.scene
    cam = sc.camera
    cam.data.ortho_scale = ortho
    cam.location = cam_loc
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.cycles.samples = samples
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def downsample(src: Path, dst: Path, size: int):
    from PIL import Image
    Image.open(src).resize((size, size), Image.LANCZOS).save(dst)


# ==========================================================================
# main
# ==========================================================================

def produce(name: str, do_bake: bool):
    t0 = time.time()
    G.reset()
    G.setup_render()
    G.setup_world(0.5)
    G.add_camera(ortho_scale=1.6)
    G.add_lights()

    parts = ASSETS[name]()
    scale = normalise(parts)
    lo, hi = bounds(parts)
    height = hi.z - lo.z
    centre_z = height / 2

    # aim camera and lights at the object's centre rather than the origin
    for o in bpy.context.scene.objects:
        for c in o.constraints:
            if c.type == "TRACK_TO" and c.target:
                c.target.location = (0, 0, centre_z)

    ground = G.plane(30, loc=(0, 0, -0.001))
    ground.is_shadow_catcher = True

    PREVIEW_OUT.mkdir(parents=True, exist_ok=True)
    ICON_OUT.mkdir(parents=True, exist_ok=True)
    out_dir = SRC_OUT / name
    out_dir.mkdir(parents=True, exist_ok=True)

    ortho = max(1.0, height) * 1.35
    render_to(PREVIEW_OUT / f"{name}.png", 480, ortho, (1.9, -3.0, 1.2 + centre_z), 160)

    # icon: no ground, tight frame, transparent
    ground.hide_render = True
    tmp = PREVIEW_OUT / f"{name}_icon480.png"
    render_to(tmp, 480, max(1.0, height) * 1.18, (1.9, -3.0, 1.1 + centre_z), 128)
    downsample(tmp, ICON_OUT / f"{name}.png", ICON_SIZE)
    tmp.unlink()

    if do_bake:
        joined = join_for_export(parts, TARGET_TRIS)
        joined.name = name
        bake_maps(joined, name, out_dir)
        export_fbx(joined, out_dir / f"{name}.fbx")
        print(f"  {name}: {tri_count(joined)} tris, scale x{scale:.3f}, {height:.2f} m tall")

    print(f"  {name} done in {time.time() - t0:.0f}s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--no-bake", action="store_true",
                    help="skip UV/bake/FBX; previews and icons only")
    args = ap.parse_args()
    names = args.only or list(ASSETS)
    for n in names:
        if n not in ASSETS:
            print(f"unknown asset {n}; known: {', '.join(ASSETS)}")
            return 1
        produce(n, not args.no_bake)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
