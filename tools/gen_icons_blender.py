#!/usr/bin/env python3
"""
Photoreal item-icon renderer for The Eighth Day.

*** WORK IN PROGRESS - FOUNDATION ONLY, NOT WIRED INTO THE BUILD. ***

What exists here: the render pipeline. Scene setup, Cycles configuration,
orthographic three-quarter camera, three-point studio lighting, a Principled
material factory with procedural roughness break-up and bump, and geometry
helpers (bevel, subsurf, displace, lathe, polygon extrude, boolean).

What does NOT exist yet: the per-item geometry builders and a main(). Nothing
calls this module, and no icons ship from it. It is parked deliberately - see
TheEighthDay/docs/ART.md for the decision.

WHY THIS APPROACH
-----------------
7 Days to Die's icons are renders of the game's own 3D assets. A first attempt
generated icons in 2D - silhouettes lit by a distance-field normal solver with
procedural surface grain. It produced clean, consistent, readable icons, and it
still sat visibly outside the game's visual language, because a shaded drawing
is not a photograph of an object. That approach was abandoned rather than
refined; the ceiling was the method, not the tuning.

Building real geometry and path-tracing it is the same process that produced
the vanilla icons, so it is the only route that lands in the same place.

REQUIREMENTS
------------
    pip install bpy            # ~370 MB wheel, needs CPython 3.11

Verified working in this environment: Blender 5.0.1 as a module, Cycles on CPU,
~1.3 s for a 160px render at 48 samples with denoising. Rendering at 480 and
downsampling to 160 keeps edges clean at a sane sample count.

SCOPE WHEN FINISHED: only items whose vanilla borrowed icon is ambiguous -
resources, notes, chemicals, medicines, electronics, food, explosives, ammo and
writs. Weapons, tools, armour and blocks keep vanilla art, which is rendered
from the real game assets and is better than anything generated here.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS = REPO_ROOT / "TheEighthDay" / "UIAtlases" / "ItemIconAtlas"
TEXCACHE = Path("/tmp/ed_icon_tex")

OUT_SIZE = 160
RENDER_SIZE = 480
SAMPLES = 128

TAU = math.tau
R = math.radians


# ==========================================================================
# scene plumbing
# ==========================================================================

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.caustics_refractive = True
    sc.render.resolution_x = RENDER_SIZE
    sc.render.resolution_y = RENDER_SIZE
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filter_size = 1.4
    # Filmic/AgX crush the mid-tones on a transparent-background product shot.
    try:
        sc.view_settings.view_transform = "Standard"
    except Exception:
        pass
    sc.view_settings.look = "None"


def setup_world(strength=0.35):
    """Dim neutral ambient so shadow sides never go pure black."""
    world = bpy.data.worlds.new("w")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.58, 0.62, 1.0)
    bg.inputs["Strength"].default_value = strength


def add_camera(ortho_scale=2.5):
    """Orthographic three-quarter view - the product-shot convention vanilla uses."""
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (2.6, -4.2, 3.0)
    track_to(cam, (0, 0, 0))
    return cam


def track_to(obj, target_loc):
    tgt = bpy.data.objects.new("tgt", None)
    bpy.context.scene.collection.objects.link(tgt)
    tgt.location = target_loc
    c = obj.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


def add_lights():
    """Key upper-left, cool fill lower-right, rim from behind. Large sources so
    highlights are broad, which is what makes a render read as photographed
    rather than CG."""
    specs = [
        ("key", (-4.5, -3.2, 5.2), 1400, 7.0, (1.0, 0.97, 0.92)),
        ("fill", (4.6, -2.6, 0.9), 300, 8.0, (0.80, 0.87, 1.0)),
        ("rim", (1.2, 4.6, 3.4), 420, 6.0, (1.0, 0.98, 0.95)),
        ("top", (0.0, -0.6, 6.5), 260, 9.0, (1.0, 1.0, 1.0)),
    ]
    for name, loc, energy, size, colour in specs:
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.size = size
        ld.color = colour
        lo = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = loc
        track_to(lo, (0, 0, 0))


# ==========================================================================
# materials
# ==========================================================================

def _set(bsdf, name, value):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = value


def material(name, base, metallic=0.0, roughness=0.5, *,
             rough_var=0.0, rough_scale=8.0,
             bump=0.0, bump_scale=14.0, bump_detail=2.0,
             transmission=0.0, ior=1.45, alpha=1.0, coat=0.0,
             subsurface=0.0, texture_image=None):
    """A Principled material with optional procedural roughness break-up and
    bump. Uniform roughness is the single biggest CG tell, so almost everything
    here gets some rough_var."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    if len(base) == 3:
        base = (*base, 1.0)
    _set(bsdf, "Base Color", base)
    _set(bsdf, "Metallic", metallic)
    _set(bsdf, "Roughness", roughness)
    _set(bsdf, "IOR", ior)
    _set(bsdf, "Alpha", alpha)
    _set(bsdf, "Transmission Weight", transmission)
    _set(bsdf, "Coat Weight", coat)
    _set(bsdf, "Subsurface Weight", subsurface)

    if texture_image is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = texture_image
        tex.interpolation = "Cubic"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if rough_var > 0:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = rough_scale
        noise.inputs["Detail"].default_value = 6.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.68
        lo = max(0.02, roughness - rough_var)
        hi = min(1.0, roughness + rough_var)
        ramp.color_ramp.elements[0].color = (lo, lo, lo, 1)
        ramp.color_ramp.elements[1].color = (hi, hi, hi, 1)
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

    if bump > 0:
        bnoise = nt.nodes.new("ShaderNodeTexNoise")
        bnoise.inputs["Scale"].default_value = bump_scale
        bnoise.inputs["Detail"].default_value = bump_detail
        bump_node = nt.nodes.new("ShaderNodeBump")
        bump_node.inputs["Strength"].default_value = bump
        nt.links.new(bnoise.outputs["Fac"], bump_node.inputs["Height"])
        nt.links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def hexc(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    # sRGB -> linear, otherwise every colour renders washed out
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)


# ==========================================================================
# geometry helpers
# ==========================================================================

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def bevel(obj, width=0.02, segments=3, angle=50):
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = R(angle)
    m.harden_normals = False
    return obj


def smooth(obj, angle=40):
    for p in obj.data.polygons:
        p.use_smooth = True
    if hasattr(obj.data, "use_auto_smooth"):
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = R(angle)
    else:
        m = obj.modifiers.new("smoothbyangle", "SMOOTH_BY_ANGLE")
        if hasattr(m, "angle"):
            m.angle = R(angle)
    return obj


def subsurf(obj, levels=2):
    m = obj.modifiers.new("subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return obj


def displace(obj, strength=0.05, scale=1.2, noise_type="VORONOI"):
    tex = bpy.data.textures.new("disp", type="VORONOI" if noise_type == "VORONOI"
                                else "CLOUDS")
    if noise_type != "VORONOI":
        tex.noise_scale = scale
    else:
        tex.noise_scale = scale
    m = obj.modifiers.new("disp", "DISPLACE")
    m.texture = tex
    m.strength = strength
    m.mid_level = 0.5
    return obj


def cube(size=1.0, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return o


def cylinder(r=0.5, depth=1.0, loc=(0, 0, 0), rot=(0, 0, 0), verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    return bpy.context.object


def cone(r1=0.5, r2=0.0, depth=1.0, loc=(0, 0, 0), rot=(0, 0, 0), verts=64):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot, vertices=verts)
    return bpy.context.object


def sphere(r=0.5, loc=(0, 0, 0), segs=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=segs,
                                         ring_count=rings)
    o = bpy.context.object
    smooth(o)
    return o


def torus(major=0.5, minor=0.08, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot,
                                     major_segments=64, minor_segments=16)
    o = bpy.context.object
    smooth(o)
    return o


def plane(size=1.0, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return o


def extrude_polygon(pts2d, depth, loc=(0, 0, 0)):
    """Build a prism from a 2D outline - used for the gear."""
    me = bpy.data.meshes.new("poly")
    ob = bpy.data.objects.new("poly", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, 0.0)) for x, y in pts2d]
    bm.faces.new(verts)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=depth)
    bm.to_mesh(me)
    bm.free()
    ob.location = loc
    return ob


def boolean_diff(obj, cutter):
    m = obj.modifiers.new("bool", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = "EXACT"
    cutter.hide_render = True
    return obj


def spin_profile(profile, segments=64, loc=(0, 0, 0)):
    """Lathe a 2D profile [(r, z), ...] around Z. Used for glassware."""
    me = bpy.data.meshes.new("spin")
    ob = bpy.data.objects.new("spin", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, axis=(0, 0, 1), cent=(0, 0, 0),
                   dvec=(0, 0, 0), angle=TAU, steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    ob.location = loc
    smooth(ob, 50)
    return ob
