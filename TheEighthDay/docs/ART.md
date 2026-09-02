# Art Pipeline — Icons and Models

What it takes to give this mod its own visual identity, and why v0.2 doesn't have one yet.

---

## Current state

Every item and block added by The Eighth Day currently borrows a vanilla icon via
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

## Custom icons — achievable, needs an artist

Icons are the cheap win. A modlet can ship its own atlas folder and the game builds it at
load; there is no code, no assembly and no SDK involved.

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

## Custom models — achievable, needs Unity and a 3D artist

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
