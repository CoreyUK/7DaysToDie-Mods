# The Turning — Cycle System

The mod's namesake mechanic. Day 7 is the game's blood moon; **day 8 is ours.**

Every horde night you survive, the world Turns at dawn. Turnings are permanent and one-way.

---

## 1. The cycle table

| Cycle | Begins | Enters the world | Feel |
|---|---|---|---|
| **0** | Day 1 | — | Vanilla-adjacent, deliberately. You are learning the map. |
| **1** | **Day 8** | **Husks** — desiccated, fast, fragile, arrive in numbers | The first "oh". Speed you weren't planning for. |
| **2** | Day 16 | **Bloaters** — swollen, slow, rupture into a lingering toxic cloud | Melee stops being free. Corridors become traps. |
| **3** | Day 24 | **Carrion Hounds** — pack animals, flank, run down stragglers | Open ground stops being safe. Travel gets expensive. |
| **4** | Day 32 | **Rotwardens** — armoured heavies, resist small-arms fire | Your ammo economy breaks. Time to industrialise. |
| **5** | Day 40 | **The Hollow** — silent, night-only stalkers, no audio tell | Night ends as an option. Not a difficulty spike — a curfew. |
| **6** | Day 48 | **Choirs** — buff nearby zombies, never attack directly | Hordes gain a shape. You have to prioritise targets. |
| **7+** | Day 56+ | **Grinders** — Titan-class; the base-ender | Fortification becomes a losing game. Mobility wins. |

Cycles do not stop at 7. Cycle 8+ continues scaling density, health and wandering-horde
frequency indefinitely, with no new archetypes. The mod has no win state.

---

## 2. Implementation

This is the part that matters technically, so it is documented honestly.

### The reliable driver: gamestage bands

The mechanical escalation is driven by **gamestage bands**, because gamestage is vanilla
plumbing that is guaranteed to work, is already multiplayer-aware, and already accounts for
days survived, player level and deaths.

`entitygroups.xml` defines one spawn group per cycle. `gamestages.xml` maps gamestage bands
onto those groups. A player crosses a band roughly every eighth day at typical play pace, so
the cycle table above is the *expected* schedule rather than a hard calendar guarantee — a
player who levels aggressively meets Husks early, and a player who turtles meets them late.

That is a feature, not a compromise: the world escalates in response to *you*, so the
schedule is honest for a solo player and for an eight-player server both.

```
Cycle 0  gamestage   0– 22
Cycle 1  gamestage  23– 52
Cycle 2  gamestage  53– 90
Cycle 3  gamestage  91–135
Cycle 4  gamestage 136–190
Cycle 5  gamestage 191–255
Cycle 6  gamestage 256–340
Cycle 7+ gamestage 341+
```

Bands are defined once in `Config/gamestages.xml` and referenced everywhere else, so
retuning the pace is a single-file change.

### The narrative layer: the dawn announcement

The *felt* moment — "the world just Turned" — is a buff-driven announcement that fires at
dawn following a horde night, reading the player's current cycle from the `edCycle` CVar and
showing the matching journal entry.

**Verification required.** The exact trigger and requirement names for "dawn after a blood
moon night" must be confirmed against V3.2's `Data/Config/buffs.xml` before this layer can be
called done — see [`VERIFICATION.md`](VERIFICATION.md), item 1. Until it is confirmed, the
announcement layer is scaffolded but inert, and **the gamestage driver carries the mechanic
on its own.** The mod is fully playable with the announcement layer switched off; you just
lose the drama, not the escalation.

This split is deliberate. The part that must not break is on vanilla rails. The part that is
cosmetic is where the risk lives.

---

## 3. Enemy archetypes

All six v0.1 archetypes reuse vanilla meshes with original stats, buffs, loot and behaviour.
Custom models are a v1.0 concern; the design has to prove itself first.

### Husk — Cycle 1
Starved-fast, low health, arrives in threes and fours. Teaches the player that Cycle 0
positioning habits are already obsolete. Low XP, low loot — a tax, not a payday.

### Bloater — Cycle 2
Slow, high health, ruptures on death into a toxic cloud that lingers ~20s and applies
stacking poison. Punishes melee-in-a-corridor, which is the vanilla player's default answer
to everything. Rewards ranged, spacing and *not* fighting in your own base hallway.

### Carrion Hound — Cycle 3
Pack of 3–6, fast, flanks, targets the isolated player. The anti-travel enemy. Makes
vehicles a survival tool rather than a convenience.

### Rotweaver — Cycle 4
*(working name: Rotwarden)* Armoured. Heavy small-arms damage resistance, weak to explosives
and armour-piercing. The enemy that forces the ammo economy to industrialise — a Cycle 4
player still on scrap 9mm is a dead player.

### The Hollow — Cycle 5
Night only. No idle audio, no footsteps, no scream. Slow, extremely high damage, low health.
Turns night from "harder" into "don't". The only enemy in the mod designed around denial
rather than combat.

### Choir — Cycle 6
Never attacks. Applies an aura buff to nearby zombies (damage, speed, health regeneration).
Fragile. Introduces target prioritisation to horde nights, which vanilla never asks for.

### Grinder — Cycle 7+
Titan-class. Structural damage on a scale that makes static fortification a losing strategy.
Rare, slow, unstoppable, telegraphed a long way out. The intended answer is to leave.

---

## 4. Tuning

Everything above is exposed at the top of each config file as a clearly-marked block. Server
operators can retune cycle pacing without touching mechanics:

- `Config/gamestages.xml` — band boundaries (cycle pace)
- `Config/entitygroups.xml` — which archetypes enter at which cycle
- `Config/entityclasses.xml` — per-archetype stats

A "slow burn" preset (bands ×1.5) and a "gauntlet" preset (bands ×0.6) ship as commented
alternates in `gamestages.xml`.
