# Callings

Six specialist paths. Each is **earned** through a trader-issued *Proving* — a short chain
that makes you do the discipline's actual work before it opens up. You cannot buy a Calling,
and you cannot stumble into one from loot.

A realistic long playthrough masters two. A co-ordinated server covers all six and
outperforms one that doesn't — that's the point.

---

## How they work

1. **Discovery.** Any trader offers the *Proving* for any Calling you haven't taken, from
   day 1. There is no gate on which you can attempt.
   *(How a quest reaches a trader's offer list is verification item 16 — unconfirmed.)*
2. **The Proving.** A 3-stage quest chain that requires doing the work, not paying for it.
3. **The Mark.** Completing the final stage rewards that Calling's **Writ**. Consuming it
   sets the Mark — a permanent status that unlocks the Calling's perk branch.

   Writs are **not sold, not looted and not craftable.** Finishing a Proving is the only
   way to get one. A Calling you can buy is a purchase, not a discipline.
4. **Multiple Callings.** You can hold as many as you earn. Nothing charges you extra for the
   second or the fifth, and nothing needs to — the cost of dabbling is **opportunity cost**,
   and it is real.

   Every branch is four cheap perks and one capstone at five points, against a deliberately
   stretched XP curve. Points are the binding constraint for the whole of the early and mid
   game, so spreading them across three Callings means reaching no capstone in any of them
   while the world Turns on its own schedule. Specialising early is stronger because the
   capstone is where each Calling's identity actually lives.

   Very late, a survivor with enough levels can hold everything. That is fine, and it is the
   mod working: there is no win state, so "you eventually mastered all six" is not a finish —
   the world is at Cycle 7+ by then and does not care.

   *This used to say each subsequent Proving cost progressively more in time, materials and
   skill points. Nothing implemented it — quest objectives are fixed per chain, perk costs are
   uniform, and no Mark is referenced anywhere in `quests.xml` — so the claim is gone rather
   than left reading as a mechanic.*

Mechanically, a Mark is a CVar (`edMarkIronmonger` etc.). Every perk in that branch carries
a requirement on its Mark, so the branch is visible but unspendable until you've earned it.
That keeps the whole system inside vanilla progression plumbing — no custom UI needed.

**The rule the Provings must never break:** no objective may require anything gated behind
a Calling. The Proving is how you earn the Calling, so requiring its own output is a
deadlock the player cannot see coming and cannot escape. That is why the Trapper's chain
asks for raw meat rather than cured, and the Sapper's for plain cement rather than the
reinforced concrete they will later own — the good material is on the far side of the door
being opened. Re-check this every time `quests.xml` is touched.

---

## The six

### Ironmonger
*The one who makes the things that make things.*

Owns the metal chain end to end: bloomery, forge, blast furnace, alloys, tool heads, ammo
casings. Nobody else can produce hardened steel or carbide, which makes the Ironmonger the
bottleneck on every other Calling's late-game gear.

**Proving:** smelt 20 crude iron → prepare 12 flux → deliver 25 crude iron.
Tests that you've built the early chain rather than looted it.

| Perk | Levels | Effect |
|---|---|---|
| Bloom & Billet | 5 | Smelting speed and ore yield |
| Alloying | 5 | Unlocks steel → hardened steel → carbide tiers |
| Tempering | 4 | Tools and weapons you craft start at higher quality |
| Casings | 4 | Ammo crafting yield |
| Master of the Forge | 1 | Capstone: blast furnace efficiency, exclusive carbide recipes |

---

### Trapper
*Feeds the group, works alone, hates noise.*

Hunting, animal handling, traps, bows, and food that survives being carried. The Trapper is
the reason the group isn't eating rotten meat on day 30, and the only Calling that makes the
wilderness a resource rather than a commute.

**Proving:** take 6 animals → bring back 40 raw meat → take 12 more animals.
*Design intent was bow-only, which quest objectives cannot express — the objective types
have no weapon filter. The flavour text carries the intent; the mechanics do not enforce it.*

| Perk | Levels | Effect |
|---|---|---|
| Quiet Foot | 5 | Noise and light footprint |
| Field Dressing | 5 | Meat and hide yield, unlocks preservation recipes |
| Snares & Deadfalls | 4 | Unlocks trap blocks; your own damage to structures |
| Bowyer | 4 | Bow damage, unlocks advanced arrow tiers |
| Ghost | 1 | Capstone: near-total noise suppression |

---

### Apothecary
*The reason anyone survives an infection.*

Chemistry, medicine, infection treatment, gas and stimulants. In a mod where infection has
four stages and stage 3+ needs real antibiotics, this Calling is not optional on a server —
it is the group's lifeline.

**Proving:** prepare 8 reagent base → crack 6 polymer → deliver 12 reagent base.
*Design intent was "cure an infection", which needs an objective type that fires on curing
another player. Not available, so the chain tests the chemistry chain instead.*

| Perk | Levels | Effect |
|---|---|---|
| Reagents | 5 | Chemistry yield, unlocks reagent bench tiers |
| Antisepsis | 5 | Unlocks tiered infection cures |
| Field Medic | 4 | Healing item potency and application speed |
| Compounds | 4 | Unlocks stimulants, gas grenades, toxin coatings |
| Physician | 1 | Capstone: the serum, and nothing else cures stage 4 |

---

### Sapper
*Shapes the ground the fight happens on.*

Explosives, fortification, excavation, concrete. The Sapper decides where the horde goes and
what it walks into. Owns the entire structural tier of the build tree.

**Proving:** produce 100 cement → produce 150 more → deliver 120.
Slow, heavy and deliberately boring, which is exactly what the Calling feels like to play.

| Perk | Levels | Effect |
|---|---|---|
| Earthworks | 5 | Dig speed, and digging costs less stamina |
| Formwork | 5 | Unlocks reinforced concrete tiers, build speed |
| Demolitions | 4 | Explosive damage, unlocks shaped charges and mining explosives |
| Emplacements | 4 | Unlocks spike, barricade and killbox blocks with real HP |
| Siege Engineer | 1 | Capstone: structural repairs mid-combat, exclusive fortification tier |

---

### Marshal
*Wins the fight the Sapper set up.*

Firearms, armour, emplacements, squad logistics. The most direct Calling, and deliberately the one
that is weakest alone — a Marshal without an Ironmonger runs out of ammunition, and a Marshal
without a Sapper fights in the open.

**Proving:** kill 60 → kill 120 more → deliver 150 gunpowder.
*Design intent was "hold a marked position", which needs a defend-location objective. The
final stage carries the real lesson instead: every Marshal who died out there died with an
empty gun.*

| Perk | Levels | Effect |
|---|---|---|
| Marksmanship | 5 | Firearm damage, reload speed |
| Plate & Weave | 5 | Unlocks composite armour tiers, armour effectiveness |
| Ordnance | 4 | Unlocks heavy weapon tiers and belt-fed conversions |
| Emplaced Guns | 4 | Unlocks emplacement tiers, emplacement damage |
| Marshal's Command | 1 | Capstone: exclusive weapon tier |

**The Command aura is not implemented, and this table used to say it was.** The design is a
group-wide combat buff — everyone fighting near the Marshal fights better — and delivering it
needs a player-side area buff that can tell allies from zombies. The Choir already showed why
that is not a detail: an unfiltered `selfAOE` aura lands on *everything* in range, so the same
mechanism that would buff your squad would buff the horde standing in it (verification item
28). Until that targeting question is answered against the real game, a Marshal capstone that
strengthens whatever is nearest is worse than one that does not exist.

It is the weakest of the six capstones as a result, and that is recorded here rather than
papered over.

---

### Scavenger
*Turns other people's ruins into your industry.*

Salvage, vehicles, electronics, loot yield. Doesn't produce anything new — makes everything
already out there worth more. The Calling that keeps a server's economy moving, and the one
that finds the Field Notes everyone else's recipes depend on.

**Proving:** recover 40 mechanical parts → 30 electrical parts → 60 paper.
*Design intent was location-typed recovery. Objectives cannot require that an item came from
a particular POI type, so the quantities do the work instead.*

| Perk | Levels | Effect |
|---|---|---|
| Wrecker | 5 | Salvage speed and yield from vehicles and machinery |
| Sorting | 5 | Loot quality and quantity, better container outcomes |
| Circuits | 4 | Unlocks electronics tiers, powered equipment recipes |
| Motor Pool | 4 | Vehicle crafting, fuel efficiency, unlocks vehicle tiers |
| Rag & Bone | 1 | Capstone: loot stage bonus, exclusive salvage-only recipes |

**Motor Pool, specifically.** The Scavenger's vehicle identity is *manufacturing* one, not
owning a special one — minibike, motorcycle, 4x4 and gyrocopter assembled at the Machine Shop
from a parts kit you built, instead of hoping a garage coughs up a chassis. Vanilla assembly
still works; this is the shortcut, not the gate.

The 4x4 is the one that matters, because the deposits made it necessary: the good materials
are a long way from the base now and scheelite is in the wasteland. The gyrocopter is
deliberately last, deliberately expensive, and deliberately needs the Ironmonger's carbide —
the build that skips the map is the one no single Calling can make alone.

---

## Balance intent

- **No Calling is self-sufficient.** Each has a hard dependency on at least one other, by
  design. Solo players will take two and trade for the rest; the trader economy is tuned
  around that assumption.
- **Capstones are group-facing.** Every capstone benefits people other than the holder,
  which makes the sixth skill point in a branch a social decision rather than a stat bump.
- **Perk points stay scarce.** With the stretched XP curve, filling two branches is a
  full playthrough's worth of points. Filling all six is not intended to be reachable.
