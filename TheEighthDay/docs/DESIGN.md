# The Eighth Day — Design Document

> *You survived seven days. The eighth is when it starts.*

**Target build:** 7 Days to Die V3.2 "Henpocalypse"
**Type:** Full overhaul, pure XML (no compiled assembly)
**Status:** v0.11.1 pre-alpha

---

## 1. The problem this mod is solving

Vanilla 7 Days to Die has an inverted difficulty curve. The first seven days are genuinely
tense — you are underfed, under-armed and one broken leg from restarting. Then the curve
turns over. By day 40 you have a steel base, an auto-turret corridor and a motorbike, and
the horde night is a chore you AFK through. The game stops being survival and becomes
maintenance.

Every overhaul in this genre attacks that problem the same way: make the early game longer.
That works, but it only moves the ceiling — it doesn't remove it. Eventually you out-scale
the world again, just later.

**The Eighth Day removes the ceiling instead.** The world levels up alongside you, and it
never levels back down. There is no build in which you have finished. There is only how
long you lasted.

---

## 2. The four pillars

### Pillar 1 — The Turning (the mod's identity)

The game's blood moon lands on day 7. **Day 8 is ours.**

As you climb, the world *Turns*. A Turning is permanent and one-way. It is announced, it is
visible, and it makes the map worse forever:

- A new enemy archetype enters the horde and wandering pools and never leaves.
- Wandering horde size and frequency step up — and a wandering horde goes anywhere,
  including the biome you settled in because it was quiet.
- Trader stock rotates toward things you now need instead of things you wanted.

**Ambient biome population is deliberately not part of that.** Ambient spawning has no
gamestage gate — that lives only in `gamestages.xml` — so rather than claim an escalation
the engine cannot express, hostility outside the hordes is gated by **geography**: each
harsh biome permanently carries one archetype, and the starter biomes carry none. The
difficulty selector is the map. You can go and find Cycle 4 on day four, and the biome told
you before you went. Reasoning in full in `Config/entitygroups.xml`.

Cycle 0 is days 1–7: recognisably vanilla, deliberately. Cycle 1 begins on **day 8**.
By Cycle 6 the surface at night is not survivable in a way that any amount of gear fixes —
it is survivable by planning, positioning and knowing when not to be outside.

The player-facing framing matters as much as the numbers. Each Turning leaves a journal
entry written in-world, fired the first time that Cycle's archetype reaches you — so the
escalation reads as *the world doing something to you*, not as a difficulty slider moving,
and it cannot name a thing you have not met.

See [`CYCLES.md`](CYCLES.md) for the full cycle table and the implementation mechanism.

### Pillar 2 — Callings

Six specialist paths. You will realistically master two in a long playthrough, and a
four-player server that co-ordinates its Callings meaningfully outperforms one that doesn't.

Callings are **earned, not bought.** Each is unlocked by a trader-issued *Proving* — a short
quest chain that makes you actually do the work of that discipline before it opens up. The
Ironmonger's Proving has you smelt and forge before it opens up; the Trapper's has you take
game and bring the meat back. Objective types cannot express every intent in the original
design — [`CALLINGS.md`](CALLINGS.md) marks which parts are mechanics and which are flavour.

| Calling | Owns | Fantasy |
|---|---|---|
| **Ironmonger** | Smelting, alloys, forges, tools, ammo casings | The one who makes the things that make things |
| **Trapper** | Hunting, animals, traps, stealth, bows, preserved food | Feeds the group, works alone, hates noise |
| **Apothecary** | Chemistry, medicine, infection, gas, stimulants | The reason anyone survives an infection |
| **Sapper** | Explosives, fortification, excavation, concrete | Shapes the ground the fight happens on |
| **Marshal** | Firearms, armour, turrets, squad logistics | Wins the fight the Sapper set up |
| **Scavenger** | Salvage, vehicles, electronics, loot yield | Turns other people's ruins into your industry |

Full trees, perks and Proving chains: [`CALLINGS.md`](CALLINGS.md).

### Pillar 3 — The Long Craft

Vanilla's production chain is two steps deep: ore goes in the forge, the item comes out of
the workbench. The Eighth Day makes industry a thing you *build*, with real intermediates
that have their own supply problems.

```
    ore ──► Bloomery ──► crude iron ──┐
                                      ├──► Forge ──► iron / brass / lead stock
    scrap ─────────────────────────────┘                       │
                                                               ▼
    coal + flux ──► Blast Furnace ──► steel ──► hardened steel ──► carbide
                                                               │
    Machine Shop ◄── precision parts ◄─────────────────────────┘
         │
         ▼
    Drafting Table ──► reads Field Notes ──► unlocks recipes the perk tree cannot
```

Two mechanics carry this pillar:

**Research over lootboxes.** High-tier recipes are not in the perk tree and are not in
schematic loot. They come from **Field Notes** — partial, damaged documents you find in
themed locations, which the **Drafting Table** consumes several at a time to reconstruct a
recipe. You cannot buy your way past this and you cannot perk your way past it. You have to
go to the places the notes are.

**Intermediates that bottleneck.** Flux, precision parts and polymer are the choke points.
Each is cheap to make and annoying to source, which keeps mid-game players going outside
rather than sitting in a base perking up.

**The farm is a second supply line, not a food minigame.** Four crops, and every one of them
feeds a chain that already existed: flax and rapeseed press to oil that feeds polymer, rye
mashes to alcohol that feeds reagent base, comfrey is the medicinal input. A player who farms
is supplying the workshop, not opting out of it — and the numbers bear it out, because the
scavenged route is still *cheaper*. Farming buys you renewability and independence from
looting, not a discount. Any future crop has to pass that test: if it only makes food, it
does not belong.

### Pillar 4 — Attrition

Damage should have a memory.

- **Staged infection.** Four stages, each with its own symptom set and its own cure tier.
  Stage 1 is a cough and a stamina tax; stage 4 is not curable with honey and a nap. Only an
  Apothecary-tier antibiotic reverses stage 3+, which makes one player's Calling the group's
  actual lifeline.
- **Durability that bites.** Every repair returns meaningfully less than vanilla, so gear
  drifts toward replacement rather than living forever on one repair kit. That keeps the
  production chain relevant at Cycle 6 instead of being something you finished at Cycle 2.

  *This was originally specified as repairs restoring less **each time** — diminishing
  returns per repair on a given item. That needs per-item state, which XML has nowhere to
  keep, so it is a C# module or nothing. A flat penalty ships instead: the same pressure,
  one dimension simpler, and honest about which one it is.*
- **Stretched progression.** Raised level cap, flatter XP curve, scarcer skill points. You
  are never "done" perking, so you are always choosing.

---

## 3. What this mod deliberately does *not* do

- **No lasers, no sci-fi tier.** The top of the tech tree is industrial and military —
  carbide, composites, belt-fed weapons. The fantasy stays grounded, because a grounded
  fantasy makes the horror land.
- **No compiled assembly.** Pure XML survives game patches. A DLL breaks on every point
  release and turns the mod into a maintenance treadmill. Where a system genuinely cannot be
  done in XML it is named as such and left out rather than faked — see the durability note
  in Pillar 4.
- **Art only where it earns its place.** All six workstations have their own models and
  icons. Items still reuse vanilla icons via `CustomIcon`/`CustomIconTint`, and enemies reuse
  vanilla meshes differentiated by size and glow. Content and balance first; art after the
  design has proven itself.
- **No third-party content.** No XML, assets, code or config from any other mod. See §6.

---

## 4. Difficulty philosophy

The mod should be hard in ways the player can *see coming*.

- **Fair:** every escalation is announced, telegraphed and consistent. A Turning happens at
  dawn, with a message, on a schedule you can count.
- **Not fair:** ambush difficulty, invisible stat inflation, enemies that counter a build
  with no tell.

If a player dies, they should be able to name the decision that killed them. That is the
line every balance change gets tested against.

---

## 5. Roadmap

| Version | Content |
|---|---|
| **0.1** | Skeleton + first vertical slice: Cycles 0–3, all six Callings' perk trees, tier-1/2 production chain, six enemy archetypes, staged infection |
| 0.2 | Proving quest chains, Drafting Table research loop, Field Note locations, trader rework |
| 0.3 | Cycles 4–6, late production tier (carbide/composite), Titan-class enemy, biome hostility (shipped as geography, not as a clock — see §2) |
| 0.4 | Balance pass from CUKServers live data, localisation beyond English |
| 1.0 | Custom icons and enemy variants, optional C# module for the systems XML genuinely can't reach |

---

## 6. Originality statement

The Eighth Day is written from scratch. It contains no XML, assets, code, configuration or
text copied or adapted from any other mod, including any existing overhaul.

Overhauls as a genre share design pillars — class systems, extended tech trees, escalating
threat, harsher survival. Those pillars are not ownable and are common to the category. What
is ownable is the specific expression of them: names, numbers, mechanics, structure, item
lists, enemy design and text. All of that here is original.

Where this mod's mechanics resemble another mod's, it is because both are solving the same
well-known problem with the same well-known genre tools, and the implementation was written
independently. Nothing was referenced line-by-line, and no file originates anywhere else.
