# Art Pipeline — Icons and Models

How this mod gets its own visual identity: what is built, what is pipeline, what still needs an artist.

---

## Current state

**All six workstations have their own 3D models, baked textures and icons** — see the
models section below. Everything else — items, weapons, enemies — borrows a vanilla icon via
`CustomIcon` and separates itself with `CustomIconTint`:

```xml
<property name="CustomIcon" value="resourceForgedSteel" />
<property name="CustomIconTint" value="4c5a66" />
```

This produces **genuinely working icons** — they render correctly, they're readable, and
they're real game art rather than placeholders. Carbide is a cold blue-grey steel ingot,
crude iron is a muddy brown one, polymer is a white oil canister. You can tell the tiers
apart at a glance in a full inventory, which is the actual job an icon has to do.

The same applies to weapons: every weapon in the mod is a mechanically new item that reuses
a vanilla mesh and animation set. The Support MG behaves nothing like an M60 — different
damage, magazine, reload, recipe and gating — but it looks like one.

**This is a resourcing constraint, not a design position.** Both ceilings below are lifted
without writing a single line of C#.

---

## Decision record — how custom icons get made

**Status: solved for blocks (rendered from their models). Parked for the ~60 items, which
keep vanilla tinted icons until their geometry exists.**

Two approaches were evaluated.

### Rejected — 2D generation

A generator was built that produced icons procedurally in 2D: silhouette masks lit by a
distance-field normal solver, with Lambert and specular response, procedural surface grain,
per-material roughness, contact occlusion and no outlines.

It produced 37 clean, consistent, readable icons. It was still **rejected**, because 7 Days
to Die's icons are photographs of objects in all but name, and a shaded drawing does not
read as one no matter how carefully it is shaded. The ceiling was the method, not the
tuning, so the code was removed rather than kept around to tempt anyone.

### Chosen — 3D render, same as vanilla

Build real geometry, give it physically based materials, light it, and path-trace it. This
is how the vanilla icons were made, so it is the only route that lands in the same visual
language.

Feasibility is **confirmed in this repo's toolchain**, not assumed:

- `pip install bpy` gives Blender 5.0.1 as a Python module (~370 MB, CPython 3.11)
- Cycles renders a 160px icon in ~1.3 s on CPU at 48 samples with denoising
- 37 icons at 480px and 128 samples is a few minutes, once per change

`tools/gen_icons_blender.py` holds the finished half: scene setup, camera, three-point
studio lighting, the material factory (procedural roughness break-up, bump, transmission)
and geometry helpers including lathe, polygon extrude and boolean. What remains is the
per-item geometry and a `main()`.

**Nothing in the mod depends on this.** Items keep their `CustomIcon` and tint until real
icons land, so the mod is complete and consistent without it.

---

## How custom icons plug in

A modlet can ship its own atlas folder and the game builds it at load; there is no code,
no assembly and no SDK involved.

### How

1. Create `TheEighthDay/UIAtlases/ItemIconAtlas/`.
2. Drop in one PNG per item, **named exactly as the item name** in `items.xml`:
   `edResourceCarbide.png`, `edWeaponSupportMG.png`, and so on.
3. Delete that item's `CustomIcon` and `CustomIconTint` properties — the atlas takes over.

### Specification

| | |
|---|---|
| Format | PNG, 32-bit with alpha |
| Size | 160 × 160 px |
| Background | Fully transparent |
| Margin | ~8 px of padding so icons don't touch in the atlas |
| Naming | Exactly the item/block `name` attribute, case-sensitive |

### Style guide for this mod

The visual language should follow the fiction: **industrial, salvaged, grounded.** Nothing
in The Eighth Day is futuristic, and nothing glows.

- Three-quarter view, single light source from upper left, matching vanilla's convention
- Muted palette — the tint colours already in `items.xml` are the intended hues and are a
  usable starting reference for each tier
- Wear and use on everything. Nothing in this world is new
- Tier should read from silhouette and material, not from an added effect

### Where this stands

The folder is created and documented, and the naming convention is fixed, so dropping real
art in is a file copy plus deleting two properties per item. What's missing is somebody to
draw roughly 60 icons. That is the entire blocker.

---

## Custom models — the pipeline is live

**Status: all six workstations built and export-ready. Unity bundle step pending (needs a desktop).**

`tools/gen_models.py` builds each workstation as real geometry in Blender, bakes its
procedural materials to textures, exports an FBX, and renders the item icon from the same
model — so the thing in your hand matches the thing on the ground.

```
python3 tools/gen_models.py                    # every asset, ~3 min each
python3 tools/gen_models.py --only edBlockBloomery
python3 tools/gen_models.py --no-bake          # previews + icons only, fast
```

Per asset it writes:

| Output | Where |
|---|---|
| `<name>.fbx` — Y-up, metres, single mesh, ≤9k tris | `Resources/src/<name>/` |
| `_BaseColor` `_Normal` `_Roughness` `_Metallic` — 1024² | `Resources/src/<name>/` |
| 160px icon | `UIAtlases/ItemIconAtlas/` |
| 480px review render | `dist/previews/` (not committed) |

Every asset is normalised to a 1 m footprint with its origin at the base centre, which is
where the game expects a block pivot.

### Built — all six workstations

| Asset | Tris | Height | Silhouette rule |
|---|---|---|---|
| `edBlockBloomery` | 9,000 | 0.97 m | Round tapered clay on a fieldstone skirt |
| `edBlockBlastFurnace` | 8,999 | 1.23 m | Square brick stack in a riveted steel frame |
| `edBlockMachineShop` | 8,452 | 1.25 m | Long low steel bench, one tall drill column at the back |
| `edBlockDraftingTable` | 1,640 | 1.36 m | One big tilted plane — the only non-flat top in the set |
| `edBlockReagentBench` | 6,398 | 1.22 m | Open bench, a forest of small verticals, low backboard |
| `edBlockSynthesisLab` | 9,000 | 1.18 m | One tall closed cabinet with hard industrial attachments |

Each pair that previously shared a vanilla mesh — bloomery/blast furnace on `forge`,
machine shop/drafting table on `workbench`, reagent bench/synthesis lab on
`chemistryStation` — now has deliberately opposed silhouettes, so they read apart at a
glance in the dark. All six are export-ready: FBX plus four baked maps each, waiting only on
the Unity bundle step below.

Every asset was reviewed as a render before it was committed. That caught a floating
bloomery, an egg-shaped furnace, a lamp in three disconnected pieces and a window glow that
rendered white-hot — none of which a triangle count or a validator would ever surface.

### The desktop step

Blender can't build a Unity AssetBundle; only Unity can, on the game's exact Unity version.
`tools/unity/EighthDayBundleBuilder.cs` makes that two menu clicks:

1. Find the game's Unity version — `Player.log` prints `Initialize engine version: …` at the
   top. Install exactly that via Unity Hub. **Any other version silently fails to load.**
2. New 3D project. Copy the `.cs` to `Assets/Editor/`. Copy `Resources/src/*` to
   `Assets/EighthDay/Models/`.
3. **Eighth Day → 1. Create Prefabs From Models** — imports textures with the right colour
   spaces, packs roughness into Unity's metallic-smoothness alpha, builds materials, adds
   mesh colliders, tags the bundle.
4. **Eighth Day → 2. Build AssetBundle** → `Bundles/eighthday.unity3d`.
5. Copy that into `TheEighthDay/Resources/` and uncomment each block's `Meshfile` line in
   `blocks.xml`. That's verification item 18.

Until step 5, blocks keep their vanilla mesh and nothing is broken — the icons already ship.

### Two gotchas the pipeline learned the hard way

- **Never touch `colorspace_settings` on a generated image after baking.** It regenerates
  the buffer and every map saves as solid black with no error. Decide colour space at
  creation via `is_data`.
- **Catmull-Clark subdivision on a 4-sided cone makes an egg.** Use `SIMPLE` subdivision
  when you want displacement detail on something that must stay square.

---

## Custom models — what still needs an artist

Bespoke weapon and block models are how the larger overhauls get their own identity. It is
more involved than icons but still requires **no C# and no Harmony patching** — it is an
asset pipeline, not a code one.

### How

1. Model and texture in Blender (or equivalent).
2. Import into Unity, on the **same Unity version the current game build ships with** —
   this must match or the bundle won't load.
3. Set the prefab up with the collider and attachment points the game expects.
4. Export as an AssetBundle.
5. Ship it in `TheEighthDay/Resources/` and reference it from XML:

```xml
<property name="Meshfile" value="#@modfolder:Resources/eighthday.unity3d?edWeaponSupportMG" />
```

### What it costs

- Unity, matching the game's version
- The 7 Days to Die modding SDK for reference rigs and shaders
- An actual 3D artist — for weapons, also animation work, since a new mesh that doesn't fit
  the existing rig needs its own reload and fire animations

### Why it isn't done

None of that exists in this repo's toolchain, and a badly-modelled gun is worse than a
well-chosen vanilla one. The XML is written so that adding a `Meshfile` property later
changes nothing else — no restructuring, no renaming, no migration.

---

## Priority

If art effort becomes available, spend it in this order:

1. **Icons for the production intermediates** — eight items that all currently look like
   tinted vanilla resources, and they're the ones players interact with most often.
2. **Icons for the Field Notes** — six items that are all tinted paper right now, and
   telling them apart matters for the research loop.
3. **Icons for weapons and tools** — higher effort, lower confusion cost, since these are
   already distinguishable by name and slot.
4. **Models** — last, and only for the capstone items where a distinct silhouette actually
   earns something: the Carbide Maul, the Marshal's Carbine, the Salvage Rig.

Everything above 4 is achievable by one artist with no programming involvement at all.
