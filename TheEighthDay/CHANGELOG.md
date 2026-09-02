# Changelog

All notable changes to The Eighth Day.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
