# Changelog

All notable changes to The Eighth Day.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.3] — 2026-09-02

All six workstations modelled. Export-ready.

### Added
- **Machine shop, drafting table, reagent bench and synthesis lab models**, completing the
  set. Each pair that previously shared a vanilla mesh now has a deliberately opposed
  silhouette: heavy flat steel bench with a lathe and drill column vs a tilted drawing board
  on a trestle; open wooden lab bench with a retort stand and glassware vs an enclosed steel
  fume cabinet with a dark window, exhaust duct and gas bottles. Same pipeline, same 9k
  budget, same 1 m footprint, icons rendered from the models.

### Changed
- `blocks.xml`: all six blocks drop `CustomIcon` for their atlas icons and carry a
  commented `Meshfile` line awaiting the bundle.
- Lab glass is modelled as opaque grimy glass. Transmission does not survive a diffuse bake
  — it comes out near-black — and a year into the apocalypse that is what glass looks like
  anyway.

## [0.3.2] — 2026-09-02

First custom 3D assets.

### Added
- **Bloomery and blast furnace models** — real geometry built in Blender, procedurally
  textured, baked to BaseColor / Normal / Roughness / Metallic at 1024², exported as FBX at
  a 9k-triangle budget with a 1 m footprint and base-centre pivot. Their item icons are
  rendered from the same models, so hand and world match. These two were first because they
  both extended `forge` and were indistinguishable in-world and in inventory.
- `tools/gen_models.py` — the asset pipeline. Build → normalise → preview → icon → join →
  decimate → unwrap → bake → FBX, per asset, in one command.
- `tools/unity/EighthDayBundleBuilder.cs` — the desktop half. Two menu items in Unity turn
  the FBX and maps into `eighthday.unity3d`, handling colour spaces, metallic-smoothness
  packing, materials and colliders.
- Verification item 18 for the bundle and atlas pickup.

### Changed
- `blocks.xml`: the two blocks drop `CustomIcon` in favour of their atlas icons, and carry
  their `Meshfile` line commented out until the bundle exists. Nothing depends on the Unity
  step having happened.

## [0.3.1] — 2026-09-02

### Fixed
- **Enemy archetypes were visually unreadable.** All seven reused vanilla meshes with no
  visual difference from their base, which broke the mod's own difficulty principle: an
  8000 HP Grinder looked exactly like an ordinary fat cop, and a Rotweaver with 65% bullet
  resistance looked like an ordinary soldier zombie — so it read as *my gun stopped working*
  rather than *wrong tool for this one*.

  Every archetype now carries a tell built from vocabulary players already read: `SizeScale`
  for silhouette, feral glow for "faster and tougher", radiated glow for "this one is a
  problem". The Grinder is nearly twice normal size and radiated; the Hollow is deliberately
  unmarked because its tell is silence, which needs no art at all.

  Still vanilla meshes — this is readability, not custom models. Each class carries its
  fallback base in a comment, and verification item 17 covers the property and variant names.

## [0.3.0] — 2026-09-02

Callings are now earned. The last "this is a placeholder" is gone from the design.

### Added
- **Six Proving quest chains** (`quests.xml`), three stages each. Completing a chain rewards
  that Calling's Writ, which grants the Mark. **Writs are no longer sold** — a Proving is
  now the only route into a Calling, because a Calling you can buy is a purchase rather than
  a discipline.
- **The Grinder** — Cycle 7+ Titan-class. 8000 HP and structural damage on a scale that
  makes static fortification a losing strategy, which is the point: past Cycle 7 the mod
  stops rewarding the best box and starts rewarding knowing when to leave. Rare, slow, loud
  and visible a long way out — never a surprise.
- `tools/check-refs.py` — resolves every cross-reference in the modlet: recipe ingredients,
  craft areas, `Extends` bases, buffs applied, entities spawned, loot groups, quest reward
  chains and every localisation key. All of these load silently when broken, which without
  a game install means they never surface at all. Now runs in CI.
- `docs/VANILLA-DEPENDENCIES.md` — auto-generated manifest of every vanilla identifier the
  mod depends on and where it is used, so verification against a real install is a
  mechanical pass rather than a hunt.

### Changed
- Localisation is now properly quoted CSV, and the validator parses it as CSV rather than
  counting commas. Prose no longer has to avoid commas to survive the check.
- `docs/CALLINGS.md` reconciled with what the quest objectives can actually express. Three
  Provings had design intent — bow-only, cure-an-infection, hold-a-position — that objective
  types do not support; those are now marked as flavour rather than mechanics instead of
  quietly reading as implemented.
- New verification item 16 covering quest structure and, critically, how a trader offers
  these at all. Until that is confirmed, Callings could be unreachable — the mitigation is
  documented in `traders.xml`.

## [0.2.0] — 2026-09-02

Backfills the Calling trees. In 0.1 two thirds of the perk unlocks pointed at recipes that
did not exist; they all point at real content now.

### Added
- **Weapons** — Support MG (belt-fed, brutal to feed), Marksman Rifle (armour-piercing,
  the Rotweaver answer at range), Marshal's Carbine (capstone), Carbide Maul.
- **Tools** — Carbide Pickaxe and Axe (Ironmonger capstone), Salvage Rig (Scavenger
  capstone).
- **Armour** — composite helmet, vest and leg armour.
- **Fortification** — rebar and high-density concrete, iron spikes, barricades, composite
  bulwark, heavy dart and powered blade emplacements.
- **Trapper kit** — snares, deadfalls, bodkin and toxin arrows, cured meat, pemmican.
- **Apothecary kit** — synthesis lab, combat stimulant and steady hand (both with a real
  comedown), gas grenades, toxin coating.
- **Scavenger kit** — salvaged circuit boards, sensor modules, vehicle parts kits, sealed
  fuel cells.
- Research loop completed: all six Field Note disciplines now reconstruct into something,
  so no note type is dead weight.
- Cross-Calling recipes — toxin arrows need the Trapper's arrow and the Apothecary's
  coating, and neither can make them alone.
- [`docs/ART.md`](docs/ART.md) and the `UIAtlases/ItemIconAtlas/` folder: the icon and
  model pipelines documented and scaffolded so art drops in without restructuring.

### Fixed
Four systems were defined but never actually driven — each looked complete in its own file
and did nothing in play. Found by auditing every identifier for an inbound reference.

- **Infection could never start.** All four stages existed with no entry point. Vanilla's
  own infection buff now hands off into stage 1 and clears itself, so every existing
  infection source in the game feeds the chain and there is only one system in play.
- **No medicine cured the staged infection.** The three cures extended a vanilla item that
  clears vanilla's buff, not this mod's. Each now removes the stages it should, guarded by
  a new `edInfCured` CVar so that curing a stage cannot trip its own advance-on-finish
  effect and immediately apply the next one.
- **Archetype loot tables were orphaned.** Five loot groups were defined and referenced by
  nothing; the enemies dropped vanilla loot. Now wired via `LootListOnDeath`.
- **The cycle tracker was never applied to anyone.** Now attached to players on first spawn
  and respawn, which is a prerequisite for the Turning announcement layer.
- Three new verification items (13, 14, 15) covering the vanilla names these fixes depend on.

### Changed
- Marshal's "Emplaced Guns" is built on fixed trap emplacements rather than robotic
  turrets, because V3.2 removed the vanilla auto-turret. Better fit for the Calling anyway.
- Enemy archetypes apply infection on hit at their own rates — the Hollow at 30%, the Husk
  at 5% — so which enemy hurt you now decides how much it costs later.
- Icons: the 2D generation pipeline was tried and removed. See `docs/ART.md`; the 3D render
  route is scaffolded in `tools/gen_icons_blender.py` and items keep vanilla icons for now.
- Two new verification items (11, 12) covering the vanilla weapon, armour and block bases
  the new gear extends.

### Known issues
- Still no custom art — see `docs/ART.md` for exactly what it would take.
- Still never loaded by the game. The new gear roughly doubles the surface area of
  unverified vanilla identifiers.

## [0.1.0] — 2026-09-02

Initial skeleton and first vertical slice. **Pre-alpha. Never loaded by the game — see
[`docs/VERIFICATION.md`](docs/VERIFICATION.md) before installing.**

### Added
- **The Turning** — cycle escalation system driven by gamestage bands (`gamestages.xml`),
  with Cycles 0–3 populated and the dawn-announcement layer scaffolded.
- **Callings** — all six perk branches (`progression.xml`), CVar-gated behind their Marks.
- **The Long Craft** — tier-1/2 production chain: bloomery, blast furnace, machine shop,
  reagent bench and drafting table workstations, with crude iron, flux, precision parts,
  polymer and hardened steel intermediates.
- **Enemy archetypes** — Husk, Bloater, Carrion Hound, Rotweaver, The Hollow and Choir as
  stat/buff variants of vanilla entities.
- **Attrition** — four-stage infection rework with tiered cures.
- Stretched XP curve and raised level cap.
- Field Notes research items and drafting-table recipe reconstruction.
- Full English localisation for all added content.
- Packaging (`tools/build.sh`, `tools/build.ps1`) and XML validation (`tools/validate.sh`)
  scripts, plus CI well-formedness checks.

### Known issues
- No item or enemy art — new items borrow vanilla icons, new enemies reuse vanilla meshes.
- Turning dawn announcement is inert pending verification item 1.
- Proving quest chains are stubbed; Calling Marks are currently granted by trader purchase
  as a placeholder until the quest chains land in 0.2.
- All balance values are first estimates with no play-test data behind them.
