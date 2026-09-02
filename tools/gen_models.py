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


def rod_between(p0, p1, r, mat, verts=12):
    """A cylinder whose ends sit exactly at p0 and p1. Anything articulated -
    lamp arms, pipe runs, struts - is built from its joints outward with this,
    because hand-placing angled segments by eye is how the first drafting-table
    lamp ended up in three floating pieces."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = G.cylinder(r, d.length, loc=tuple((p0 + p1) / 2), verts=verts)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return G.assign(o, mat)


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


# --------------------------------------------------------------------------
# shared material palette for the four bench-type workstations
# --------------------------------------------------------------------------

def bench_palette():
    """Materials the benches share. Built per scene because Blender materials
    belong to a file, and every asset starts from an empty one.

    GLASS is opaque on purpose. Transmission does not survive a diffuse bake -
    it comes out near-black - so lab glass is grimy, tinted and solid, which is
    also simply what glass looks like a year into the apocalypse."""
    return dict(
        steel=weathered("edm_steel", G.hexc("#4a4d52"), G.hexc("#2b2d31"), 0.5, 7,
                        bump=0.6, bump_scale=16, metallic=0.9),
        iron=weathered("edm_castiron", G.hexc("#2f2f31"), G.hexc("#1c1c1e"), 0.72, 5,
                       bump=0.9, bump_scale=12, metallic=0.8),
        rust=weathered("edm_rust", G.hexc("#6b3f22"), G.hexc("#3a2414"), 0.9, 5,
                       bump=1.2, bump_scale=12, metallic=0.4),
        wood=weathered("edm_wood", G.hexc("#6a4a2e"), G.hexc("#3f2b19"), 0.75, 2.2,
                       bump=1.0, bump_scale=9),
        oiledwood=weathered("edm_oiledwood", G.hexc("#3a2818"), G.hexc("#1f150c"), 0.55, 3,
                            bump=0.8, bump_scale=10),
        paper=weathered("edm_paper", G.hexc("#d8cfb4"), G.hexc("#b9ae90"), 0.85, 6,
                        bump=0.25, bump_scale=30),
        brass=weathered("edm_brass", G.hexc("#9c7a3a"), G.hexc("#6a4f22"), 0.4, 6,
                        bump=0.4, bump_scale=14, metallic=0.95),
        enamel=weathered("edm_enamel", G.hexc("#6f7f6a"), G.hexc("#48543f"), 0.45, 4,
                         bump=0.5, bump_scale=11),
        rubber=weathered("edm_rubber", G.hexc("#1e1e1f"), G.hexc("#101011"), 0.95, 5,
                         bump=0.4, bump_scale=20),
        glass=weathered("edm_glass", G.hexc("#9fb1ac"), G.hexc("#6f8580"), 0.22, 5,
                        bump=0.25, bump_scale=18),
        darkglass=weathered("edm_darkglass", G.hexc("#2c3a3a"), G.hexc("#1a2424"), 0.18, 5,
                            bump=0.15, bump_scale=18),
        green=weathered("edm_liq_green", (0.10, 0.55, 0.20, 1), (0.05, 0.35, 0.12, 1), 0.3,
                        emission=((0.2, 0.9, 0.3, 1), 0.12)),
        amber=weathered("edm_liq_amber", (0.75, 0.45, 0.08, 1), (0.5, 0.28, 0.04, 1), 0.3,
                        emission=((1.0, 0.6, 0.1, 1), 0.12)),
        violet=weathered("edm_liq_violet", (0.45, 0.15, 0.6, 1), (0.3, 0.08, 0.4, 1), 0.3,
                         emission=((0.7, 0.3, 1.0, 1), 0.12)),
        flame=weathered("edm_flame", (1, 0.5, 0.1, 1), (1, 0.3, 0.05, 1), 0.5,
                        emission=((1.0, 0.45, 0.08, 1), 14.0)),
        bulb=weathered("edm_bulb", (1, 0.9, 0.7, 1), (1, 0.85, 0.6, 1), 0.3,
                       emission=((1.0, 0.85, 0.55, 1), 10.0)),
    )


def bench_frame(parts, m, w, d, h, top_t=0.08, leg=0.08, top_mat=None, leg_mat=None):
    """Four box-section legs and a slab top. Returns the top-surface z."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            l = G.cube(1.0, loc=(sx * (w / 2 - leg / 2), sy * (d / 2 - leg / 2), (h - top_t) / 2),
                       scale=(leg, leg, h - top_t))
            G.bevel(l, 0.008, 2)
            parts.append(G.assign(l, leg_mat or m["steel"]))
    # stretchers
    for sy in (-1, 1):
        s = G.cube(1.0, loc=(0, sy * (d / 2 - leg / 2), 0.16), scale=(w - leg * 2, leg * 0.7, leg * 0.7))
        parts.append(G.assign(s, leg_mat or m["steel"]))
    top = G.cube(1.0, loc=(0, 0, h - top_t / 2), scale=(w, d, top_t))
    G.bevel(top, 0.012, 3)
    parts.append(G.assign(top, top_mat or m["oiledwood"]))
    return h


def build_machine_shop():
    """Heavy steel bench with a lathe along the back and a drill column.

    Silhouette rule: long horizontal mass low, one tall vertical at the back
    corner. Nothing else in the set has that profile."""
    m = bench_palette()
    parts = []
    W, D = 1.30, 0.78
    top_z = bench_frame(parts, m, W, D, 0.88, top_mat=m["oiledwood"])

    # drawer unit under the left side
    unit = G.cube(1.0, loc=(-0.33, 0.0, 0.40), scale=(0.52, 0.62, 0.60))
    G.bevel(unit, 0.01, 2)
    parts.append(G.assign(unit, m["steel"]))
    for i, z in enumerate((0.24, 0.42, 0.60)):
        front = G.cube(1.0, loc=(-0.33, -0.318, z), scale=(0.46, 0.02, 0.14))
        parts.append(G.assign(front, m["enamel"] if i != 1 else m["rust"]))
        handle = G.cylinder(0.012, 0.16, loc=(-0.33, -0.34, z), rot=(0, R(90), 0), verts=12)
        parts.append(G.assign(handle, m["brass"]))

    # lathe bed along the back
    bed = G.cube(1.0, loc=(0.05, 0.20, top_z + 0.06), scale=(1.0, 0.20, 0.12))
    G.bevel(bed, 0.012, 2)
    parts.append(G.assign(bed, m["iron"]))
    # ways - two bright rails
    for y in (0.13, 0.27):
        rail = G.cube(1.0, loc=(0.05, y, top_z + 0.13), scale=(0.96, 0.03, 0.02))
        parts.append(G.assign(rail, m["steel"]))
    # headstock, chuck, workpiece
    head = G.cube(1.0, loc=(-0.32, 0.20, top_z + 0.27), scale=(0.24, 0.26, 0.30))
    G.bevel(head, 0.015, 3)
    parts.append(G.assign(head, m["iron"]))
    chuck = G.cylinder(0.09, 0.07, loc=(-0.165, 0.20, top_z + 0.30), rot=(0, R(90), 0), verts=32)
    G.bevel(chuck, 0.008, 2)
    parts.append(G.assign(chuck, m["steel"]))
    for k in range(3):
        a = k * math.tau / 3
        jaw = G.cube(1.0, loc=(-0.12, 0.20 + math.cos(a) * 0.055, top_z + 0.30 + math.sin(a) * 0.055),
                     scale=(0.04, 0.03, 0.03), rot=(a, 0, 0))
        parts.append(G.assign(jaw, m["iron"]))
    work = G.cylinder(0.028, 0.46, loc=(0.10, 0.20, top_z + 0.30), rot=(0, R(90), 0), verts=20)
    parts.append(G.assign(work, m["steel"]))
    # handwheel on the headstock
    wheel = G.torus(0.075, 0.012, loc=(-0.46, 0.20, top_z + 0.30), rot=(0, R(90), 0))
    parts.append(G.assign(wheel, m["brass"]))
    # tailstock and carriage
    tail = G.cube(1.0, loc=(0.44, 0.20, top_z + 0.22), scale=(0.16, 0.20, 0.20))
    G.bevel(tail, 0.012, 2)
    parts.append(G.assign(tail, m["iron"]))
    carriage = G.cube(1.0, loc=(0.16, 0.20, top_z + 0.17), scale=(0.18, 0.30, 0.10))
    parts.append(G.assign(carriage, m["iron"]))
    cwheel = G.torus(0.045, 0.01, loc=(0.16, 0.04, top_z + 0.17), rot=(R(90), 0, 0))
    parts.append(G.assign(cwheel, m["brass"]))

    # drill column at the back-right - the tall vertical
    col = G.cylinder(0.045, 0.78, loc=(0.52, 0.22, top_z + 0.39), verts=24)
    parts.append(G.assign(col, m["iron"]))
    colbase = G.cube(1.0, loc=(0.52, 0.22, top_z + 0.02), scale=(0.20, 0.20, 0.04))
    parts.append(G.assign(colbase, m["iron"]))
    dhead = G.cube(1.0, loc=(0.46, 0.06, top_z + 0.72), scale=(0.28, 0.40, 0.16))
    G.bevel(dhead, 0.02, 3)
    parts.append(G.assign(dhead, m["enamel"]))
    spindle = G.cylinder(0.02, 0.20, loc=(0.46, -0.10, top_z + 0.55), verts=16)
    parts.append(G.assign(spindle, m["steel"]))
    dtable = G.cube(1.0, loc=(0.46, -0.08, top_z + 0.36), scale=(0.22, 0.22, 0.03))
    parts.append(G.assign(dtable, m["iron"]))
    dwheel = G.torus(0.06, 0.01, loc=(0.61, 0.06, top_z + 0.72), rot=(0, R(90), 0))
    parts.append(G.assign(dwheel, m["brass"]))

    # bench vise at the front-right corner
    vbase = G.cube(1.0, loc=(0.40, -0.30, top_z + 0.05), scale=(0.18, 0.12, 0.10))
    parts.append(G.assign(vbase, m["iron"]))
    for x in (0.34, 0.47):
        jaw = G.cube(1.0, loc=(x, -0.30, top_z + 0.15), scale=(0.05, 0.14, 0.10))
        parts.append(G.assign(jaw, m["iron"]))
    screw = G.cylinder(0.014, 0.30, loc=(0.52, -0.30, top_z + 0.12), rot=(0, R(90), 0), verts=12)
    parts.append(G.assign(screw, m["steel"]))
    # scattered swarf / a wrench on the top
    wrench = G.cube(1.0, loc=(-0.05, -0.26, top_z + 0.012), scale=(0.28, 0.035, 0.012), rot=(0, 0, R(18)))
    parts.append(G.assign(wrench, m["steel"]))
    return parts


def build_drafting_table():
    """Tilted drawing board on a trestle, lamp, rolled plans.

    Silhouette rule: one big tilted plane. Every other bench is flat."""
    m = bench_palette()
    parts = []
    tilt = R(24)      # positive: surface faces the front (-y), top edge at the back
    bx, by, bz = 1.22, 0.86, 0.96

    # trestle: two A-frames of leaning timbers joined by a crossbar
    for sx in (-1, 1):
        for lean in (-1, 1):
            leg = G.cube(1.0, loc=(sx * 0.50, lean * 0.20, 0.44),
                         scale=(0.07, 0.07, 0.90), rot=(R(-13 * lean), 0, 0))
            parts.append(G.assign(leg, m["wood"]))
        cross = G.cube(1.0, loc=(sx * 0.50, 0.0, 0.36), scale=(0.06, 0.36, 0.05))
        parts.append(G.assign(cross, m["wood"]))
    bar = G.cube(1.0, loc=(0, 0, 0.36), scale=(1.04, 0.06, 0.06))
    parts.append(G.assign(bar, m["wood"]))
    # rolled plans resting on the bar
    for i, (x, r) in enumerate(((-0.25, 0.035), (0.0, 0.03), (0.22, 0.04))):
        roll = G.cylinder(r, 0.62, loc=(x, 0.02, 0.36 + 0.03 + r), rot=(R(90), 0, R(-6 + i * 5)), verts=16)
        parts.append(G.assign(roll, m["paper"]))

    # the board and its frame
    board = G.cube(1.0, loc=(0, 0.02, bz), scale=(bx, by, 0.045), rot=(tilt, 0, 0))
    G.bevel(board, 0.01, 2)
    parts.append(G.assign(board, m["wood"]))
    # normal of the tilted board (rotation about x)
    nx, ny, nz = 0.0, -math.sin(tilt), math.cos(tilt)
    def on_board(u, v, lift):
        # u along x, v along the board's up direction
        vy, vz = math.cos(tilt), math.sin(tilt)
        return (u, 0.02 + v * vy + ny * lift, bz + v * vz + nz * lift)
    # drawing surface
    sheet = G.plane(1.0, loc=on_board(0, 0, 0.026), rot=(tilt, 0, 0), scale=(bx - 0.10, by - 0.10, 1))
    parts.append(G.assign(sheet, m["paper"]))
    # pinned sheets, slightly askew
    for u, v, rz, sw, sh in ((-0.30, 0.10, 4, 0.36, 0.26), (0.22, -0.12, -7, 0.42, 0.30), (0.05, 0.22, 2, 0.30, 0.20)):
        p = G.plane(1.0, loc=on_board(u, v, 0.032), rot=(tilt, 0, R(rz)), scale=(sw, sh, 1))
        parts.append(G.assign(p, m["paper"]))
        for du, dv in ((-sw / 2 + 0.02, sh / 2 - 0.02), (sw / 2 - 0.02, sh / 2 - 0.02)):
            pin = G.sphere(0.012, loc=on_board(u + du, v + dv, 0.04), segs=10, rings=5)
            parts.append(G.assign(pin, m["brass"]))
    # T-square hooked over the top edge
    tsq = G.cube(1.0, loc=on_board(-0.10, by / 2 - 0.02, 0.05), rot=(tilt, 0, 0), scale=(0.80, 0.05, 0.015))
    parts.append(G.assign(tsq, m["oiledwood"]))
    tblade = G.cube(1.0, loc=on_board(-0.10, by / 2 - 0.32, 0.05), rot=(tilt, 0, 0), scale=(0.05, 0.62, 0.012))
    parts.append(G.assign(tblade, m["oiledwood"]))
    # pencil tray along the bottom edge
    tray = G.cube(1.0, loc=on_board(0, -by / 2 - 0.02, 0.03), rot=(tilt, 0, 0), scale=(bx, 0.07, 0.04))
    parts.append(G.assign(tray, m["wood"]))
    for i in range(4):
        pen = G.cylinder(0.006, 0.18, loc=on_board(-0.4 + i * 0.12, -by / 2 - 0.02, 0.055),
                         rot=(tilt, 0, R(90 + i * 6)), verts=8)
        parts.append(G.assign(pen, m["brass"] if i % 2 else m["rubber"]))

    # lamp: clamp at the top-right corner, then joint -> arm -> elbow -> arm ->
    # shade, every segment spanning two known points so nothing can float
    clamp_at = Vector(on_board(0.56, by / 2 - 0.05, 0.03))
    clamp = G.cube(1.0, loc=tuple(clamp_at), rot=(tilt, 0, 0), scale=(0.08, 0.10, 0.10))
    parts.append(G.assign(clamp, m["iron"]))
    j0 = clamp_at + Vector((0, 0, 0.06))
    j1 = Vector((0.40, 0.16, 1.66))          # elbow: up and back
    j2 = Vector((0.02, -0.06, 1.46))         # over the middle of the board
    parts.append(rod_between(j0, j1, 0.014, m["enamel"]))
    parts.append(G.assign(G.sphere(0.03, loc=tuple(j1), segs=12, rings=6), m["iron"]))
    parts.append(rod_between(j1, j2, 0.014, m["enamel"]))
    parts.append(G.assign(G.sphere(0.024, loc=tuple(j2), segs=12, rings=6), m["iron"]))
    shade = G.cone(r1=0.16, r2=0.04, depth=0.15, loc=(j2.x, j2.y, j2.z - 0.09), verts=32)
    parts.append(G.assign(shade, m["enamel"]))
    bulb = G.sphere(0.04, loc=(j2.x, j2.y, j2.z - 0.15), segs=14, rings=7)
    parts.append(G.assign(bulb, m["bulb"]))
    ld = bpy.data.lights.new("lamp", "POINT")
    ld.energy = 25
    ld.color = (1.0, 0.85, 0.6)
    lo = bpy.data.objects.new("ember_lamp", ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (j2.x, j2.y, j2.z - 0.18)
    return parts


def build_reagent_bench():
    """Open wooden lab bench: retort stand, burner, glassware, a shelf of bottles.

    Silhouette rule: flat bench with a forest of small verticals on top and a
    low backboard. The synthesis lab is the opposite - one big closed box."""
    m = bench_palette()
    parts = []
    W, D = 1.24, 0.72
    top_z = bench_frame(parts, m, W, D, 0.90, top_t=0.07, leg=0.07,
                        top_mat=m["rubber"], leg_mat=m["wood"])
    # wooden apron under the top so the rubber reads as a sheet on timber
    apron = G.cube(1.0, loc=(0, 0, top_z - 0.105), scale=(W - 0.02, D - 0.02, 0.07))
    parts.append(G.assign(apron, m["wood"]))

    # backboard and shelf with bottles
    back = G.cube(1.0, loc=(0, D / 2 - 0.02, top_z + 0.26), scale=(W, 0.03, 0.52))
    parts.append(G.assign(back, m["wood"]))
    shelf = G.cube(1.0, loc=(0, D / 2 - 0.10, top_z + 0.34), scale=(W - 0.06, 0.16, 0.025))
    parts.append(G.assign(shelf, m["wood"]))
    bottles = ((-0.48, 0.035, 0.16, "amber"), (-0.36, 0.03, 0.12, "green"), (-0.22, 0.04, 0.20, "violet"),
               (-0.06, 0.028, 0.11, "glass"), (0.10, 0.035, 0.15, "amber"), (0.26, 0.03, 0.18, "green"),
               (0.42, 0.04, 0.13, "glass"))
    for x, r, h, mat in bottles:
        b = G.cylinder(r, h, loc=(x, D / 2 - 0.10, top_z + 0.352 + h / 2), verts=16)
        G.bevel(b, 0.008, 2)
        parts.append(G.assign(b, m[mat]))
        neck = G.cylinder(r * 0.45, 0.04, loc=(x, D / 2 - 0.10, top_z + 0.352 + h + 0.02), verts=12)
        parts.append(G.assign(neck, m["glass"]))
        cork = G.cylinder(r * 0.4, 0.025, loc=(x, D / 2 - 0.10, top_z + 0.352 + h + 0.05), verts=12)
        parts.append(G.assign(cork, m["wood"]))

    # retort stand with a round-bottom flask over a burner
    sx, sy = -0.30, -0.02
    base = G.cube(1.0, loc=(sx, sy, top_z + 0.012), scale=(0.20, 0.14, 0.025))
    parts.append(G.assign(base, m["iron"]))
    rod = G.cylinder(0.012, 0.62, loc=(sx - 0.08, sy + 0.05, top_z + 0.33), verts=12)
    parts.append(G.assign(rod, m["steel"]))
    arm = G.cylinder(0.008, 0.16, loc=(sx, sy + 0.05, top_z + 0.42), rot=(0, R(90), 0), verts=10)
    parts.append(G.assign(arm, m["steel"]))
    ring = G.torus(0.075, 0.008, loc=(sx + 0.02, sy, top_z + 0.42))
    parts.append(G.assign(ring, m["steel"]))
    flask = G.spin_profile([(0, 0), (0.06, 0.005), (0.10, 0.06), (0.09, 0.13), (0.03, 0.17),
                            (0.03, 0.26), (0.036, 0.27), (0, 0.27)], segments=28,
                           loc=(sx + 0.02, sy, top_z + 0.345))
    parts.append(G.assign(flask, m["glass"]))
    liquid = G.sphere(0.078, loc=(sx + 0.02, sy, top_z + 0.42), segs=20, rings=10)
    parts.append(G.assign(liquid, m["green"]))
    burner = G.cylinder(0.025, 0.14, loc=(sx + 0.02, sy, top_z + 0.09), verts=16)
    parts.append(G.assign(burner, m["brass"]))
    bfoot = G.cylinder(0.06, 0.015, loc=(sx + 0.02, sy, top_z + 0.03), verts=20)
    parts.append(G.assign(bfoot, m["iron"]))
    flame = G.cone(r1=0.02, r2=0.0, depth=0.11, loc=(sx + 0.02, sy, top_z + 0.22), verts=12)
    parts.append(G.assign(flame, m["flame"]))
    ember_light((sx + 0.02, sy, top_z + 0.24), 18)

    # conical flask, beaker, mortar and pestle
    con = G.spin_profile([(0, 0), (0.09, 0), (0.035, 0.15), (0.035, 0.20), (0.042, 0.21), (0, 0.21)],
                         segments=28, loc=(0.06, -0.14, top_z))
    parts.append(G.assign(con, m["glass"]))
    cliq = G.cone(r1=0.085, r2=0.05, depth=0.09, loc=(0.06, -0.14, top_z + 0.048), verts=24)
    parts.append(G.assign(cliq, m["amber"]))
    beaker = G.spin_profile([(0, 0), (0.06, 0), (0.06, 0.15), (0.066, 0.155), (0, 0.155)],
                            segments=24, loc=(0.24, -0.10, top_z))
    parts.append(G.assign(beaker, m["glass"]))
    bliq = G.cylinder(0.055, 0.07, loc=(0.24, -0.10, top_z + 0.04), verts=24)
    parts.append(G.assign(bliq, m["violet"]))
    mortar = G.spin_profile([(0, 0), (0.07, 0), (0.09, 0.05), (0.085, 0.08), (0.06, 0.03), (0, 0.03)],
                            segments=24, loc=(0.44, -0.12, top_z))
    parts.append(G.assign(mortar, m["enamel"]))
    pestle = G.cylinder(0.014, 0.16, loc=(0.47, -0.10, top_z + 0.10), rot=(R(20), R(30), 0), verts=10)
    parts.append(G.assign(pestle, m["enamel"]))
    # a notebook and a rag
    book = G.cube(1.0, loc=(0.42, 0.10, top_z + 0.012), scale=(0.20, 0.26, 0.025), rot=(0, 0, R(-8)))
    parts.append(G.assign(book, m["paper"]))
    return parts


def build_synthesis_lab():
    """Enclosed steel fume cabinet: dark window, exhaust duct, gas bottles, gauges.

    Silhouette rule: one tall closed box with hard industrial attachments. It is
    the Apothecary's second tier and should look like it costs what it costs."""
    m = bench_palette()
    parts = []
    W, D, H = 1.10, 0.70, 1.55

    # plinth and cabinet body
    plinth = G.cube(1.0, loc=(0, 0, 0.06), scale=(W + 0.04, D + 0.04, 0.12))
    parts.append(G.assign(plinth, m["iron"]))
    body = G.cube(1.0, loc=(0, 0.04, 0.12 + (H - 0.12) / 2), scale=(W, D - 0.08, H - 0.12))
    G.bevel(body, 0.015, 3)
    parts.append(G.assign(body, m["enamel"]))
    # lower service doors
    for sx in (-1, 1):
        door = G.cube(1.0, loc=(sx * 0.27, -D / 2 + 0.045, 0.42), scale=(0.48, 0.02, 0.50))
        parts.append(G.assign(door, m["enamel"]))
        hd = G.cylinder(0.01, 0.12, loc=(sx * 0.06, -D / 2 + 0.03, 0.42), verts=10)
        parts.append(G.assign(hd, m["steel"]))
    # the window: dark glass set into a steel sash, upper front
    sash = G.cube(1.0, loc=(0, -D / 2 + 0.05, 1.08), scale=(0.94, 0.03, 0.66))
    parts.append(G.assign(sash, m["steel"]))
    win = G.cube(1.0, loc=(0, -D / 2 + 0.035, 1.08), scale=(0.84, 0.01, 0.56))
    parts.append(G.assign(win, m["darkglass"]))
    # faint interior glow so the window reads as lit from inside
    glow = G.plane(1.0, loc=(0, -D / 2 + 0.028, 0.90), rot=(R(90), 0, 0), scale=(0.34, 0.04, 1))
    parts.append(G.assign(glow, weathered("edm_glow", (0.3, 0.9, 0.5, 1), (0.2, 0.7, 0.4, 1), 0.5,
                                          emission=((0.35, 1.0, 0.55, 1), 0.7))))
    # sash handle
    sh = G.cylinder(0.012, 0.30, loc=(0, -D / 2 + 0.02, 0.76), rot=(0, R(90), 0), verts=12)
    parts.append(G.assign(sh, m["steel"]))

    # control panel below the window
    panel = G.cube(1.0, loc=(0, -D / 2 + 0.05, 0.70), scale=(0.94, 0.03, 0.10))
    parts.append(G.assign(panel, m["iron"]))
    for i, x in enumerate((-0.32, -0.16, 0.0)):
        gauge = G.cylinder(0.035, 0.02, loc=(x, -D / 2 + 0.03, 0.70), rot=(R(90), 0, 0), verts=20)
        parts.append(G.assign(gauge, m["brass"]))
        face = G.cylinder(0.026, 0.006, loc=(x, -D / 2 + 0.018, 0.70), rot=(R(90), 0, 0), verts=16)
        parts.append(G.assign(face, m["paper"]))
    for x in (0.18, 0.34):
        valve = G.torus(0.035, 0.008, loc=(x, -D / 2 + 0.02, 0.70), rot=(R(90), 0, 0))
        parts.append(G.assign(valve, m["rust"]))
        stem = G.cylinder(0.008, 0.05, loc=(x, -D / 2 + 0.035, 0.70), rot=(R(90), 0, 0), verts=8)
        parts.append(G.assign(stem, m["steel"]))

    # exhaust duct off the top with an elbow
    duct = G.cylinder(0.12, 0.34, loc=(0.22, 0.10, H + 0.17), verts=28)
    parts.append(G.assign(duct, m["steel"]))
    elbow = G.sphere(0.12, loc=(0.22, 0.10, H + 0.34), segs=20, rings=10)
    parts.append(G.assign(elbow, m["steel"]))
    duct2 = G.cylinder(0.12, 0.40, loc=(0.22, 0.32, H + 0.34), rot=(R(90), 0, 0), verts=28)
    parts.append(G.assign(duct2, m["rust"]))
    band = G.torus(0.125, 0.012, loc=(0.22, 0.10, H + 0.06))
    parts.append(G.assign(band, m["rust"]))

    # gas bottles strapped to the left side
    for y, mat in ((-0.12, "enamel"), (0.14, "rust")):
        cyl = G.cylinder(0.11, 0.86, loc=(-W / 2 - 0.12, y, 0.12 + 0.43), verts=24)
        parts.append(G.assign(cyl, m[mat]))
        dome = G.sphere(0.11, loc=(-W / 2 - 0.12, y, 0.98), segs=20, rings=10)
        parts.append(G.assign(dome, m[mat]))
        vlv = G.cylinder(0.03, 0.10, loc=(-W / 2 - 0.12, y, 1.13), verts=12)
        parts.append(G.assign(vlv, m["brass"]))
        pipe = G.cylinder(0.012, 0.16, loc=(-W / 2 - 0.04, y, 1.15), rot=(0, R(90), 0), verts=8)
        parts.append(G.assign(pipe, m["steel"]))
    strap = G.cube(1.0, loc=(-W / 2 - 0.12, 0.01, 0.75), scale=(0.26, 0.50, 0.04))
    parts.append(G.assign(strap, m["steel"]))

    # reaction vessel on a bracket, right side, piped into the cabinet
    bracket = G.cube(1.0, loc=(W / 2 + 0.10, 0.02, 0.62), scale=(0.22, 0.30, 0.04))
    parts.append(G.assign(bracket, m["iron"]))
    vessel = G.cylinder(0.14, 0.50, loc=(W / 2 + 0.16, 0.02, 0.62 + 0.27), verts=28)
    parts.append(G.assign(vessel, m["steel"]))
    vdome = G.sphere(0.14, loc=(W / 2 + 0.16, 0.02, 1.14), segs=20, rings=10)
    parts.append(G.assign(vdome, m["steel"]))
    for z in (0.75, 1.02):
        r = G.torus(0.145, 0.012, loc=(W / 2 + 0.16, 0.02, z))
        parts.append(G.assign(r, m["rust"]))
    sight = G.cube(1.0, loc=(W / 2 + 0.30, 0.02, 0.86), scale=(0.02, 0.06, 0.28))
    parts.append(G.assign(sight, m["violet"]))
    for z in (0.70, 1.20):
        p = G.cylinder(0.02, 0.18, loc=(W / 2 + 0.04, 0.02, z), rot=(0, R(90), 0), verts=10)
        parts.append(G.assign(p, m["steel"]))
    return parts


ASSETS = {
    "edBlockBloomery": build_bloomery,
    "edBlockBlastFurnace": build_blast_furnace,
    "edBlockMachineShop": build_machine_shop,
    "edBlockDraftingTable": build_drafting_table,
    "edBlockReagentBench": build_reagent_bench,
    "edBlockSynthesisLab": build_synthesis_lab,
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
