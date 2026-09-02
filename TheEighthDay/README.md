# The Eighth Day

> *You survived seven days. The eighth is when it starts.*

An overhaul for **7 Days to Die V3.2 (Henpocalypse)**, built around one idea:
**the world escalates faster than you do.**

> ⚠️ **v0.1.0 is pre-alpha and has never been loaded by the game.** Read
> [`docs/VERIFICATION.md`](docs/VERIFICATION.md) before installing anywhere you care about.

---

## Why

Vanilla has an inverted difficulty curve. Days 1–7 are genuinely tense. Then it turns over,
and by day 40 the horde night is a chore you AFK through. Every overhaul in this genre fixes
that by making the early game longer — which moves the ceiling but never removes it.

The Eighth Day removes it. The world levels up alongside you and never levels back down.
There is no build in which you have finished. There is only how long you lasted.

---

## The four pillars

### The Turning
The game's blood moon lands on day 7. **Day 8 is ours.** Every horde night you survive, the
world Turns at dawn — permanently, one-way. A new enemy archetype enters the spawn pool and
never leaves. Wandering hordes grow. Biome hostility spreads outward. By Cycle 5 night stops
being an option, and no amount of gear changes that.

→ [`docs/CYCLES.md`](docs/CYCLES.md)

### Callings
Six specialist paths — Ironmonger, Trapper, Apothecary, Sapper, Marshal, Scavenger — each
**earned** through a trader-issued Proving that makes you do the discipline's actual work
before it opens up. No Calling is self-sufficient. A Marshal without an Ironmonger runs out
of ammunition; a Marshal without a Sapper fights in the open.

→ [`docs/CALLINGS.md`](docs/CALLINGS.md)

### The Long Craft
Industry you build rather than unlock. Bloomery → forge → blast furnace → machine shop, with
flux, precision parts and polymer as deliberate bottlenecks. High-tier recipes are not in the
perk tree and not in schematic loot — they are reconstructed at a **Drafting Table** from
Field Notes you have to go and find.

### Attrition
Four-stage infection with tiered cures, where stage 4 needs an Apothecary and nothing else
will do. Repairs that give back less each time. A stretched XP curve with no "done" state.

---

## Difficulty philosophy

Hard in ways you can **see coming.** Every escalation is announced, telegraphed and
consistent. No ambush difficulty, no invisible stat inflation, no enemy that counters your
build with no tell.

If you die, you should be able to name the decision that killed you. Every balance change
gets tested against that line.

---

## Install

Copy the `TheEighthDay` folder into your game's `Mods` folder, disable EAC, start a new save.
Full instructions — including dedicated server setup and the version-matching rules that
will bite you if you skip them — are in [`docs/INSTALL.md`](docs/INSTALL.md).

Running it on a server: [`docs/SERVER.md`](docs/SERVER.md).

---

## Status

**v0.3.1 — pre-alpha.** Callings are now earned. What exists:

- ✅ Cycle system (gamestage-driven), Cycles 0–6 populated
- ✅ All six Calling perk branches, Mark-gated, **every unlock backed by real content**
- ✅ Tier-1/2 production chain and six workstations
- ✅ Weapons, tools, armour, fortification, traps, stimulants and salvage gear
- ✅ Seven enemy archetypes, including the Cycle 7+ Grinder
- ✅ Four-stage infection
- ✅ Research loop complete — all six Field Note disciplines reconstruct into something
- ✅ Six Proving quest chains — Callings are earned, and Writs are no longer sold
- ⚠️ Turning dawn announcement scaffolded but inert (verification item 1)
- ⚠️ No custom art — items borrow vanilla icons, weapons and enemies reuse vanilla
  meshes. Enemies now carry size and glow tells so they are at least readable.
  The pipeline is scaffolded and specified in [`docs/ART.md`](docs/ART.md); it needs an
  artist, not a programmer
- ❌ No play-test data behind any balance value

Roadmap in [`docs/DESIGN.md`](DESIGN.md#5-roadmap), release history in
[`CHANGELOG.md`](CHANGELOG.md).

---

## Originality

Written from scratch. No XML, assets, code, config or text from any other mod. Overhauls as
a genre share design pillars — class systems, extended tech trees, escalating threat — and
those are not ownable. The specific expression here is: names, numbers, mechanics, structure,
items, enemies and every word of text.

## Licence

**Proprietary — all rights reserved.** See [LICENSE](../LICENSE). You may play it and run it
on your own server; you may not reupload, repackage, fork, bundle or reuse it without written
permission.
