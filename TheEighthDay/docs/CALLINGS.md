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
2. **The Proving.** A 3-stage quest chain that requires doing the work, not paying for it.
3. **The Mark.** Completing it grants the Calling's Mark — a permanent, non-transferable
   status that unlocks that Calling's perk branch for spending skill points in.
4. **Multiple Callings.** You can hold more than one, but each subsequent Proving costs
   progressively more (time, materials and skill points), so specialising early is
   genuinely stronger than dabbling.

Mechanically, a Mark is a CVar (`edMarkIronmonger` etc.) set on quest completion. Every
perk in that branch carries a requirement on its Mark, so the branch is visible but
unspendable until you've earned it. That keeps the whole system inside vanilla progression
plumbing — no custom UI needed.

---

## The six

### Ironmonger
*The one who makes the things that make things.*

Owns the metal chain end to end: bloomery, forge, blast furnace, alloys, tool heads, ammo
casings. Nobody else can produce hardened steel or carbide, which makes the Ironmonger the
bottleneck on every other Calling's late-game gear.

**Proving:** smelt crude iron from raw ore, forge a set of tool heads to spec, deliver to
the trader inside a deadline. Tests that you've built the early chain, not looted it.

| Perk | Levels | Effect |
|---|---|---|
| Bloom & Billet | 5 | Smelting speed and ore yield |
| Alloying | 5 | Unlocks steel → hardened steel → carbide tiers |
| Tempering | 4 | Tools and weapons you craft start at higher quality |
| Casings | 4 | Ammo crafting yield and unlocks bulk casing recipes |
| Master of the Forge | 1 | Capstone: blast furnace efficiency, exclusive carbide recipes |

---

### Trapper
*Feeds the group, works alone, hates noise.*

Hunting, animal handling, traps, bows, and food that survives being carried. The Trapper is
the reason the group isn't eating rotten meat on day 30, and the only Calling that makes the
wilderness a resource rather than a commute.

**Proving:** take large game with a bow only — no firearms, no explosives — and return the
meat unspoiled. Tests patience and stealth, which is the whole fantasy.

| Perk | Levels | Effect |
|---|---|---|
| Quiet Foot | 5 | Stealth, noise reduction, animal detection range |
| Field Dressing | 5 | Meat and hide yield, unlocks preservation recipes |
| Snares & Deadfalls | 4 | Unlocks trap blocks, trap damage and reset speed |
| Bowyer | 4 | Bow damage, draw speed, unlocks advanced arrow tiers |
| Ghost | 1 | Capstone: near-total noise suppression while crouched |

---

### Apothecary
*The reason anyone survives an infection.*

Chemistry, medicine, infection treatment, gas and stimulants. In a mod where infection has
four stages and stage 3+ needs real antibiotics, this Calling is not optional on a server —
it is the group's lifeline.

**Proving:** brew a course of antibiotics from base reagents and cure an infection —
yours or someone else's. Tests that you've built the chemistry chain.

| Perk | Levels | Effect |
|---|---|---|
| Reagents | 5 | Chemistry yield, unlocks reagent bench tiers |
| Antisepsis | 5 | Unlocks tiered infection cures, treatment potency |
| Field Medic | 4 | Healing item potency and application speed, revive speed |
| Compounds | 4 | Unlocks stimulants, gas grenades, toxin coatings |
| Physician | 1 | Capstone: cure stage 4 infection, craft the group-wide prophylactic |

---

### Sapper
*Shapes the ground the fight happens on.*

Explosives, fortification, excavation, concrete. The Sapper decides where the horde goes and
what it walks into. Owns the entire structural tier of the build tree.

**Proving:** excavate to bedrock depth and pour a reinforced structure to spec. Slow,
material-hungry, and exactly what the Calling feels like to play.

| Perk | Levels | Effect |
|---|---|---|
| Earthworks | 5 | Dig speed, unlocks powered excavation tools |
| Formwork | 5 | Unlocks reinforced concrete tiers, build speed and cost |
| Demolitions | 4 | Explosive damage, unlocks shaped charges and mining explosives |
| Emplacements | 4 | Unlocks spike, barricade and killbox blocks with real HP |
| Siege Engineer | 1 | Capstone: structural repairs mid-combat, exclusive fortification tier |

---

### Marshal
*Wins the fight the Sapper set up.*

Firearms, armour, turrets, squad logistics. The most direct Calling, and deliberately the one
that is weakest alone — a Marshal without an Ironmonger runs out of ammunition, and a Marshal
without a Sapper fights in the open.

**Proving:** hold a marked position against a wave with a trader-supplied loadout. No base,
no prep. Tests the fantasy directly.

| Perk | Levels | Effect |
|---|---|---|
| Marksmanship | 5 | Firearm handling, reload speed, recoil |
| Plate & Weave | 5 | Unlocks composite armour tiers, armour effectiveness |
| Ordnance | 4 | Unlocks heavy weapon tiers and belt-fed conversions |
| Emplaced Guns | 4 | Turret damage, targeting, unlocks turret tiers |
| Marshal's Command | 1 | Capstone: group-wide combat aura, exclusive weapon tier |

---

### Scavenger
*Turns other people's ruins into your industry.*

Salvage, vehicles, electronics, loot yield. Doesn't produce anything new — makes everything
already out there worth more. The Calling that keeps a server's economy moving, and the one
that finds the Field Notes everyone else's recipes depend on.

**Proving:** recover a specific set of salvaged components from named location types and
deliver them intact. Tests that you've actually gone out and looked.

| Perk | Levels | Effect |
|---|---|---|
| Wrecker | 5 | Salvage speed and yield from vehicles and machinery |
| Sorting | 5 | Loot quality and quantity, better container outcomes |
| Circuits | 4 | Unlocks electronics tiers, powered equipment recipes |
| Motor Pool | 4 | Vehicle crafting, fuel efficiency, unlocks vehicle tiers |
| Rag & Bone | 1 | Capstone: Field Note find rate, exclusive salvage-only recipes |

---

## Balance intent

- **No Calling is self-sufficient.** Each has a hard dependency on at least one other, by
  design. Solo players will take two and trade for the rest; the trader economy is tuned
  around that assumption.
- **Capstones are group-facing.** Every capstone benefits people other than the holder,
  which makes the sixth skill point in a branch a social decision rather than a stat bump.
- **Perk points stay scarce.** With the stretched XP curve, filling two branches is a
  full playthrough's worth of points. Filling all six is not intended to be reachable.
