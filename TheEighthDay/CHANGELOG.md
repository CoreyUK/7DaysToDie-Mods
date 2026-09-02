# Changelog

All notable changes to The Eighth Day.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.11.0] — 2026-09-02

### Added
- **`tools/check-vanilla.py` — the other half of the verification pass.** Everything else in
  `tools/` checks the mod against itself, because that is all that can be done without the
  game. This takes the game's own `Data/Config` and answers the two questions the whole of
  `VERIFICATION.md` exists to ask:

  **Do the patches hit anything?** A modlet is a list of XPath edits, and an
  `<append xpath="...">` that matches nothing is not an error — the game applies zero edits,
  logs nothing, and the feature is simply absent. All ~70 targets are now resolved against
  the real files, including `set`/`setattribute` edits that address an *attribute* vanilla
  may no longer have.

  **Do the names exist?** All ~90 vanilla identifiers already collected into
  `VANILLA-DEPENDENCIES.md` — ingredients, `Extends` bases, buffs, entity classes, loot
  groups, perks — resolved against `items.xml`, `blocks.xml` and the rest.

  Written now precisely because the game is not available: the point is that the day it is,
  verification is one command and a list rather than a day spent reading two sets of XML
  side by side. Exit code 1 if anything is missing, so it can gate a release.

  Proven against a synthetic `Data/Config` built to satisfy the mod exactly — clean pass at
  73 targets and 89 identifiers — then by recreating three of the failures this checklist
  actually fears: vanilla renaming `buffInfection` (verification item 13; caught twice, as a
  dropped patch *and* a missing identifier), an armour base removed by an armour rework
  (item 11), and the blood moon spawner renamed (item 2). All three reported by name and
  exit 1.

- `VERIFICATION.md` now opens its test procedure with that command as step 0, and lists
  explicitly what it *cannot* see — the behavioural items: the `ModifyCVar` spelling, the
  announcement's requirement names, `SizeScale`, whether a redefined harvest drop replaces
  or stacks, and icon names, which live in a texture atlas rather than in `Data/Config`.

## [0.10.0] — 2026-09-02

### Fixed
- **The mod wrote CVars two different ways, and at most one of them works.** `operation="set"`
  in `items.xml` (all six Calling Marks) and in the infection cure guard; `operation="setvalue"`
  in the Turning code added two releases ago. Only one of those is the engine's spelling, and
  the other does nothing — silently, because an unset CVar reads as zero.

  If `set` is the wrong one, **no Writ ever grants its Mark and every Calling branch stays
  shut for the whole game**, with no error printed anywhere. That is the single most expensive
  failure still latent in this mod, and it was sitting in plain sight in two files. Everything
  now uses `set`, so there is one thing to confirm and one thing to change — new verification
  item 24, flagged to be checked before anything else on the list.

- **Stage 4 infection could be waited out.** The terminal stage ran for twenty minutes and
  then simply ended. Bandage through it, eat, sit down, and you were cured for free — so the
  stage that exists to make the Apothecary the group's lifeline was, in practice, a timer.
  It now re-applies itself while the cure guard is clear: the serum or dying, nothing else.

### Added
- **`tools/check-cvars.py`.** CVars are this mod's only persistent per-player state, and every
  one of them is a gate. Nothing validated the pairing between the thing that writes a CVar
  and the thing that reads it, and an unset CVar reads as zero — so a gate nobody writes is
  not an error, it is a door that never opens.

  Three checks: a CVar read by a gate and written by nothing (`UNWRITTEN`), a CVar written and
  read by nothing (`UNREAD`), and more than one spelling of the assignment operation
  (`VOCABULARY`). Proven by renaming the Ironmonger's Mark at its write site: it reports the
  gate in `progression.xml` that can now never open *and* the orphaned write, and exits 1.

## [0.9.0] — 2026-09-02

Three bugs in the escalation itself, all found by extending `check-cycles.py` rather than by
reading the file again.

### Fixed
- **Escalation stopped dead at gamestage 600.** The blood moon table's last band was 600, so
  a player at gamestage 900 got exactly the same horde as one at 600 — and one at 2000 did
  too, forever. That is the ceiling this mod exists to remove, reinstated higher up, and it
  landed precisely where *"you never finish the game, you only last longer"* was supposed to
  start mattering.

  Nine further bands now run out to gamestage 3000. `num` climbs throughout; `maxAlive` climbs
  much more slowly and stops at 45, because `maxAlive` is concurrent entities and therefore
  the number that decides whether a dedicated server survives the night. Operators trimming
  for performance should trim `maxAlive` and leave `num` alone.

- **The Choir existed only on horde nights.** The wandering horde table jumped from Cycle 5
  straight to Cycle 7, so Cycle 6's archetype never appeared in it.

- **The Grinder arrived in wandering hordes a band early.** The wandering table handed out
  Cycle 7 at gamestage 341 — the same band the blood moon introduces it — breaking the rule
  written in the comment directly above that table: *a wandering horde picks up a Cycle pool
  one band later, so the first time you meet a new archetype it is on your terms, at night,
  behind a wall.* Instead the Titan met you in the open on the same day it met you behind
  your wall.

### Added
- **Invariant 4 in `check-cycles.py`: wandering follows, never leads.** A wandering horde must
  pick up each Cycle pool strictly later than the blood moon does, and no Cycle may be missing
  from the wandering table. Both of the bugs above were found by writing the check and running
  it against the shipped file, which is the point of writing it.

## [0.8.0] — 2026-09-02

Biome hostility. The map becomes the difficulty selector.

### Fixed
- **Three archetypes were in every biome from the first minute of a new save.** The ambient
  bleed-through appended Husks, Bloaters and Carrion Hounds straight into vanilla's
  `ZombiesAll`, with no gate of any kind on it.

  That contradicted Cycle 0 — described in the design as *"vanilla-adjacent, deliberately;
  you are learning the map"* — and it hollowed out the mod's own name. "Day 8 is ours" stops
  meaning much when the eighth day brings something you have been killing all week.

  It also broke the announcement layer the moment that layer became real, one release ago: a
  blanket ambient pool hands the player the Cycle 1, 2 and 3 journal entries before day two.
  Three one-way, once-ever moments, spent on nothing.

### Added
- **Four biome pools, gated by geography.** Ambient spawning has no gamestage gate — that
  lives only in `gamestages.xml` — so the ambient world cannot escalate on a clock. Rather
  than pretend otherwise, hostility outside the hordes is now a property of *place*, and each
  harsh biome teaches exactly one archetype before the horde ever does:

  | biome | teaches | why there |
  |---|---|---|
  | burnt forest | Bloaters | things that rupture, where it burned |
  | desert | Carrion Hounds | open ground is where you get run down |
  | snow | Rotweavers | armoured, slow, patient |
  | wasteland | most of them, plus a rare Choir | it is the wasteland |

  The starter biomes carry nothing, and that is the design rather than an omission: the safe
  biome stays safe, and what escalates there is what **walks through** it — wandering hordes
  are gamestage-gated and go anywhere. Dread that arrives and then leaves is a better
  mechanic than a forest that quietly gets worse.

  So you can go and find Cycle 4 on day four, and the biome told you before you went. The
  Grinder appears in none of them: it is an event, not a population.

### Changed
- **Three documents were promising an escalation the engine cannot express.** DESIGN.md said
  "biome hostility spreads outward — the forest stops being the safe biome", the root README
  said "biomes you had written off as safe stop being safe", and the roadmap listed biome
  hostility as unshipped. Ambient spawning has never had a gamestage gate, so the first two
  were unimplementable as written rather than merely unimplemented. All three now say what
  actually ships and why.
- DESIGN.md's status line had been stale at v0.4.0 for four releases, and it still described
  the Turning as firing "a screen message" at each horde night.

## [0.7.0] — 2026-09-02

The mod's namesake finally does something the player can see.

### Added
- **The Turning announces itself.** Seven journal entries, one per Cycle, fired the first
  time that Cycle's archetype touches you or dies beside you. Once ever, permanent, written
  as a page out of somebody's notebook rather than a stat readout — the Rotweaver entry is
  someone realising most of a magazine did nothing; the Hollow entry is someone realising
  nothing woke them.

  This was the last core pillar that was scaffolded and inert. It has been the `⚠️` line in
  the README since v0.1.

- **`tools/check-cycles.py`.** The Turning is described in five places that have no way of
  noticing each other: the pools in `entitygroups.xml`, the bands in `gamestages.xml`, the
  announcement hooks in `entityclasses.xml`, the text in `Localization.csv`, and the table in
  `docs/CYCLES.md`. Retune the bands or reorder a pool and every one of them still loads,
  still resolves, still prices — and the message calmly names the wrong monster.

  Six invariants now hold on every push: pools stay cumulative (a Turning is one-way, so an
  archetype that can *leave* the world breaks the mechanic outright), each Cycle introduces
  exactly one archetype, bands ascend and map to pools in order, the archetype that arrives
  at Cycle N is the one that announces Cycle N, the text for Cycle N names it, and the docs
  table agrees.

### Changed
- **The announcement fires on first contact, not at dawn.** The old design was abandoned
  rather than deferred, for one practical reason and one that would have shipped a lie.

  Practically, *"it is dawn and last night was a blood moon"* needs a requirement name that
  cannot be confirmed without the game's own config, which is why the pillar sat commented
  out for six releases waiting on a fact nobody had.

  The reason that matters: the dawn counter and the spawn table were **two independent
  clocks.** Spawns are chosen by gamestage; a horde-night count is chosen by the calendar.
  Those agree only for a player at average pace — someone who levels hard is fighting Cycle 3
  pools on day 12 while the counter still reads Cycle 1. The announcement would have
  confidently named the wrong archetype, and in a mod whose stated principle is *hard in ways
  you can see coming*, an announcement that lies is worse than none: it teaches you to
  prepare for the wrong thing.

  Triggering off the archetype removes the disagreement rather than managing it. The thing
  announcing its arrival **is** the arrival — there is only one event, so there is nothing to
  keep in step. It also means Cycles can arrive out of order, which is correct: a wandering
  horde can hand you a Bloater before you ever meet a Husk, and you get the Bloater entry.
  The cycle read only ever climbs.

  Nothing new is guessed at. Every mechanism used — `CVarCompare` gates, `ModifyCVar`,
  `AddBuff` with `target="other"` and with `target="selfAOE"` — is already load-bearing
  elsewhere in this mod. Verification item 1 shrank from "design and author this layer" to
  four ordinary name confirmations, and if any of them is wrong you lose journal entries,
  not escalation.

- **Cycle tracker initialisation is now guarded.** It reset `edCycle` to zero unconditionally
  on buff start, and the tracker is re-applied on every respawn — so a player's Turning
  history would have been wiped every time they died.

### Fixed
- Verified the new checker by breaking things on purpose rather than trusting it: swapping
  two Cycles' journal text (`LIES`, both cycles named), dropping the Husk out of the Cycle 3
  pool (`LEAVES`, plus the cascade into Cycle 4 owning two arrivals), pointing the Bloater's
  hook at the Carrion Hound's Cycle (`MISMATCH` and `IMPOSTOR`), and retuning a band below
  its predecessor (`BAND ORDER`). All four exit 1.

## [0.6.1] — 2026-09-02

### Added
- **`tools/check-progression.py` — cold-start reachability analysis.** Every other check
  asks "is this reference valid". This one asks the question that matters to a player:
  *starting with nothing, can you get there at all?*

  A deadlock resolves cleanly, prices consistently and validates perfectly. Nothing reports
  it; the player simply cannot progress. This repo already shipped one — seeds came only
  from crops, crops only from seeds, and the trader stock that broke the circle was wired to
  nothing. It was found by accident. This is so the next one is not.

  It computes a fixpoint closure over loot, trader stock, recipes, craft areas, planting and
  harvest, perk gates, Marks and the full Proving chains. Currently: **82/82 items obtainable,
  6/6 Callings earnable.** Runs in CI.

### Fixed
- **Two modelling bugs in that checker, both found by testing it rather than trusting it.**
  First, it treated crop harvests as a free source — which made it blind to the exact
  circular dependency it exists to find. Harvesting is downstream of planting, which is
  downstream of the seed. Second, it checked quest stages in isolation; because the Writ
  hangs off the last stage, an impossible stage 1 went unnoticed while stage 3 looked fine.
  Chains are now walked end to end and the report names the blocking stage.

## [0.6.0] — 2026-09-02

Trader overhaul.

### Fixed
- **Nothing the mod added was ever purchasable.** Both trader groups were defined and
  referenced by nothing — defining a `trader_item_group` does not put it on a shelf,
  something has to stock it. Flux, reagent base, precision parts, compost and all four seeds
  were unbuyable, which also meant **the farm could not be bootstrapped**: a seed recipe
  needs a crop and a crop needs a seed, and the trader was the only thing breaking that
  circle. `check-refs.py` had been treating trader groups as entry points; it now requires
  a trader to stock them, so this cannot recur.

### Added
- **Stock follows the Turning**, delivering a `DESIGN.md` promise that was never
  implemented. Three tiers, and the shift is the point: *Foundation* (seeds, compost, first
  metal — you are building), *Industry* (parts, polymer, reagents, oil — you are scaling),
  *Attrition* (medical stock, alcohol, powder, rations — you are not building any more, you
  are staying alive). By Cycle 5 the shelf should stop offering you a workshop.
- **The trader rule, enforced by the build.** The trader sells inputs and never a Calling's
  output — a Calling whose product sits on a shelf is a Calling nobody needs.
  `check-unlocks.py` now fails if any perk-gated item appears in trader stock. Verified by
  deliberately injecting carbide into stock and confirming the build fails, then reverting.
  41 perk-gated items, none purchasable. Field Notes are excluded on the same principle:
  the research loop's premise is that you cannot buy past it.
- Verification item 23 for the stocking path and tier gating.

## [0.5.1] — 2026-09-02

### Added
- **Two storage tiers.** Footlocker (early, 9x5) and Supply Locker (late, 12x8, built at the
  machine shop from steel, precision parts and polymer) — so the warehouse is something the
  Long Craft pays for rather than free shelving.

### Not added, on purpose
- **A bigger player backpack.** It is the most-felt QoL change in this genre and it is being
  deferred rather than guessed at. Backpack size lives in XUi, and V3.0 changed the binding
  model rather than just renaming files, so a UI mod is a porting job against a structure
  that cannot be inspected from here. Every other patch in this mod either loads or silently
  no-ops; a malformed XUi window can leave the game unusable. That is a different class of
  risk and it is not worth taking blind. Container capacity, which delivers much of the same
  relief, is plain block config and carries none of it. See verification item 22.

## [0.5.0] — 2026-09-02

Farming and cooking. The largest content addition since the Callings.

### Added
- **Four crops**, each feeding a chain that already existed rather than starting a new one:
  flax (fibre + oil), rye (flour + mash), comfrey (medicinal), rapeseed (pressed oil).
  Twelve growth-stage blocks, four seeds, harvest drops with seed return.
- **The farm route into industry.** Pressed oil gives polymer a second recipe; crude alcohol
  gives reagent base one. A Scavenger can grow their way to plastics and an Apothecary is no
  longer hostage to looted acid. Crucially the scavenged route is still cheaper — farming
  buys renewability and independence, not a discount.
- **Compost Bin** — rotting flesh finally does something. Rot plus plant matter becomes the
  compost that seeds cost, so the Husk stops being purely a tax.
- **Drying Rack** — the Trapper's preservation station. Cured meat and pemmican move here
  off the campfire, so preserving is a thing you *built* rather than a recipe you know.
- **Cooking**: hardtack, bone broth, ration pack, and herbal broth — which takes the edge off
  an infection without curing it, deliberately, because curing is the Apothecary's pillar and
  a pot of soup must not undercut it.
- Two food buffs, seeds in trader stock and loot, 56 localisation strings.

### Fixed
- **`check-economy.py` had a latent bug the farm exposed.** Crops have no recipe — they come
  out of the ground — so they had no cost basis, and the route-selection heuristic ("fewest
  ingredients") then picked routes *through* them. Polymer, composite plate and every
  medicine downstream silently became uncostable: the uncosted list jumped from 7 to 41.
  Crops are now priced as primary production like ore, and the checker costs **every** route
  and takes the cheapest that actually prices, rather than guessing one up front.

### Changed
- Verification item 21 covers the crop bases and, specifically, whether a redefined harvest
  drop replaces the inherited one or stacks with it — the one farming failure that would be
  loud rather than silent.

## [0.4.0] — 2026-09-02

An audit pass. Found three things the mod claimed to do and did not.

### Fixed
- **The Hollow's night-only identity did not exist.** `edNightPool` was defined and nothing
  spawned it, so Cycle 5's curfew was a doc promise. Ambient spawning has no gamestage gate —
  that lives only in `gamestages.xml` — so "only at night" and "enters at Cycle 5" cannot
  both come from it. The gate is now **geography**: The Hollow haunts the wasteland and burnt
  forest after dark from day one, and joins the horde pools at Cycle 5. A day-3 player who
  walks into the wasteland at night meets something silent, which is what the wasteland is
  for. Deliberately absent from the starter biomes — that would be a rug-pull, not a curfew.
- **12 items were priced below their own input cost**, including every tier material:
  carbide at 0.30x, composite plate 0.27x, hardened steel 0.39x, precision parts 0.48x.
  Precision parts sat in trader stock at 120 while costing 250 to craft, so a player could
  buy them cheaper than the machine shop could make them — quietly gutting the Long Craft.
  All 26 prices are now derived from their recipes.
- **`--fix` declined to fix the worst cases.** A tolerance gate meant to catch cosmetic drift
  was also suppressing below-input-cost items, which are the actual exploit. Below cost is
  now always corrected regardless of how close to target it happens to land.

### Added
- `tools/check-economy.py` — derives every craftable item's cost from its recipe recursively
  and checks the declared price against it. Items whose play value exceeds their materials
  (medicine, ordnance, stimulants) carry a documented `UTILITY` premium, hard-capped at 2.5x,
  because past that buying inputs to sell output becomes a mint. Runs in CI.
- Orphan detection in `check-refs.py` — definitions nothing references. The mirror image of
  an unresolved reference and just as silent; it is what caught `edNightPool`.
- Attrition durability: every repair returns 35% less, so gear drifts toward replacement.
- Verification items 19 (biome names) and 20 (the assumed vanilla price table).

### Changed
- `DESIGN.md` reconciled with what ships. The Attrition pillar claimed repairs restore less
  *each time* — per-item diminishing returns, which needs per-item state XML cannot keep.
  A flat penalty ships instead, and the doc now says so rather than leaving it aspirational.

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
