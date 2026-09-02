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
| **4** | Day 32 | **Rotweavers** — armoured heavies, resist small-arms fire | Your ammo economy breaks. Time to industrialise. |
| **5** | Day 40 | **The Hollow** — silent, night-only stalkers, no audio tell | Night ends as an option. Not a difficulty spike — a curfew. |
| **6** | Day 48 | **Choirs** — buff nearby zombies, never attack directly | Hordes gain a shape. You have to prioritise targets. |
| **7+** | Day 56+ | **Grinders** — Titan-class; the base-ender | Fortification becomes a losing game. Mobility wins. |

Cycles do not stop at 7. Past it there are no new archetypes, only more of everything: nine
further blood-moon bands run out to gamestage 3000, and the wandering hordes climb with them.
The mod has no win state.

That tail is not decoration. The table used to stop at gamestage 600, which quietly put back
the exact ceiling this mod exists to remove — a player at 900 got the same horde as one at
600, forever, and *"you never finish, you only last longer"* stopped being true precisely
where it was meant to start mattering.

`num` keeps climbing across those bands; `maxAlive` climbs far more slowly and stops at 45,
because `maxAlive` is concurrent entities and therefore the number that decides whether a
dedicated server survives the night. **Operators trimming for performance should trim
`maxAlive` and leave `num` alone** — fewer at once for longer is the same fight at a fraction
of the cost.

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

### The narrative layer: the announcement

The *felt* moment — "the world just Turned" — is a journal entry that fires **the first time
a Cycle's archetype touches you or dies beside you.** One per Cycle, once ever.

It reads as a page torn out of somebody's notebook, not a stat readout, and never the words
"Cycle 3 unlocked". The Rotweaver entry is someone realising most of a magazine did nothing.
The Hollow entry is someone realising nothing woke them.

#### Why first contact and not dawn

This originally fired at dawn after a horde night, off a counter incremented once per
Turning. It was rewritten, for one practical reason and one that would have shipped a lie.

The practical reason: *"it is dawn and last night was a blood moon"* needs a requirement name
that cannot be confirmed without the game's own config, so the whole pillar sat commented out
waiting on a fact nobody had.

The reason that matters: **the counter and the spawn table were two independent clocks.**
Spawns are chosen by gamestage. A horde-night count is chosen by the calendar. Those agree
only for a player at average pace — someone who levels hard is fighting Cycle 3 pools on day
12 while a dawn counter still reads Cycle 1, and the announcement would have confidently
named the wrong monster.

In a mod whose stated principle is *hard in ways you can see coming*, an announcement that
lies is worse than none: it teaches you to prepare for the wrong thing.

So the trigger is the archetype itself. The thing announcing its arrival **is** the arrival,
so the message cannot disagree with the spawn table — not because the two are carefully kept
in step, but because there is only one event.

One consequence worth stating: Cycles can arrive out of order. A wandering horde can hand you
a Bloater before you ever meet a Husk, and you get the Bloater entry. That is correct — each
entry announces what you just met — and the cycle read only ever climbs, so meeting a Husk
afterwards does not walk the world back to Cycle 1.

`tools/check-cycles.py` enforces the agreement between the pools, the bands, the
announcements, the text and the table above, on every push.

---

## 3. Enemy archetypes

All archetypes reuse vanilla meshes with original stats, buffs, loot and behaviour. Custom
models are a v1.0 concern; the design has to prove itself first.

**But every one carries a visual tell**, built from vocabulary the player already reads:
size, feral glow, radiated glow. An archetype you cannot pick out of a horde is not "hard
but fair", it is unexplained — and this mod's whole difficulty philosophy is that you should
be able to name the decision that killed you.

### Husk — Cycle 1
Starved-fast, low health, arrives in threes and fours. Teaches the player that Cycle 0
positioning habits are already obsolete. Low XP, low loot — a tax, not a payday.

**Recognise it by:** feral glow, slightly smaller frame. Glowing eyes already mean *faster than you expect*.

### Bloater — Cycle 2
Slow, high health, ruptures on death into a toxic cloud that lingers ~20s and applies
stacking poison. Punishes melee-in-a-corridor, which is the vanilla player's default answer
to everything. Rewards ranged, spacing and *not* fighting in your own base hallway.

**Recognise it by:** 20% larger than the fat zombie beside it. Swollen is the concept and size is the cue that survives a dark room.

### Carrion Hound — Cycle 3
Pack of 3–6, fast, flanks, targets the isolated player. The anti-travel enemy. Makes
vehicles a survival tool rather than a convenience.

**Recognise it by:** noticeably bigger than a normal dog, and never alone.

### Rotweaver — Cycle 4
Armoured. Heavy small-arms damage resistance, weak to explosives
and armour-piercing. The enemy that forces the ammo economy to industrialise — a Cycle 4
player still on scrap 9mm is a dead player.

**Recognise it by:** feral glow on an armoured body. This tell matters most — without it, 65% bullet resistance reads as *my gun broke* rather than *wrong tool*.

### The Hollow — Cycle 5
Night only. No idle audio, no footsteps, no scream. Slow, extremely high damage, low health.
Turns night from "harder" into "don't". The only enemy in the mod designed around denial
rather than combat.

**Recognise it by:** nothing. That is the tell — no idle audio, no footsteps, no scream. You notice the absence, and it needs no art at all.

### Choir — Cycle 6
Never attacks. Applies an aura buff to nearby zombies (damage, speed, health regeneration).
Fragile. Introduces target prioritisation to horde nights, which vanilla never asks for.

**Recognise it by:** feral glow, small, hanging back from the fight. The horde has to be readable enough to prioritise or the mechanic is invisible.

### Grinder — Cycle 7+
Titan-class. Structural damage on a scale that makes static fortification a losing strategy.
Rare, slow, unstoppable, telegraphed a long way out. The intended answer is to leave.

**Recognise it by:** nearly twice the size of anything else, and radiated. It is meant to be visible a long way out — a Grinder that surprises you is a design failure.

---

## 4. Tuning

Everything above is exposed at the top of each config file as a clearly-marked block. Server
operators can retune cycle pacing without touching mechanics:

- `Config/gamestages.xml` — band boundaries (cycle pace)
- `Config/entitygroups.xml` — which archetypes enter at which cycle
- `Config/entityclasses.xml` — per-archetype stats

A "slow burn" preset (bands ×1.5) and a "gauntlet" preset (bands ×0.6) ship as commented
alternates in `gamestages.xml`.
