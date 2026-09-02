# Verification Checklist

**Read this before running the mod on anything you care about.**

v0.1.0 was authored without access to a 7 Days to Die V3.2 installation. Every file here is
well-formed XML and follows documented modding conventions, but **none of it has been loaded
by the game**. The items below are the places where a vanilla identifier, attribute name or
trigger name must be confirmed against the real `Data/Config/` before this can be called
tested.

Work through this list with the game's own config files open. Each item names the file to
check against and what "correct" looks like.

---

## Priority 1 — will stop the mod loading if wrong

### 1. The Turning announcement
**Check:** `Data/Config/buffs.xml`
*No longer a Priority 1 blocker. It keeps this number so the `VERIFY-1` tags in the config
files stay stable.*

This item used to read "find the requirement name for dawn after a blood moon". That approach
was **abandoned rather than deferred** — the reasoning is in `Config/buffs.xml` section 3. The
short version: it needed a requirement name nobody could confirm, and it counted horde nights
while the spawn table counted gamestage, so the two could disagree and the message could name
the wrong archetype.

The announcement now fires on first contact with each archetype, which cannot disagree with
what spawned. What remains to confirm is ordinary and low-risk, because every mechanism it
uses is already load-bearing elsewhere in this mod:

- `CVarCompare` with `operation="LT"` — the mod already relies on `Equals` / `NotEquals`
  (perk gates, `edInfCured`). Confirm `LT` is valid; if it is not, the one-way cycle read can
  be rebuilt from `NotEquals` guards on the per-cycle `edSeenCycleN` CVars, which are already
  written.
- `ModifyCVar` with `operation="setvalue"` — already used by the infection chain.
- `AddBuff` with `target="other"` and with `target="selfAOE" range="..."` — both already used
  by the infect-on-hit groups and by the Bloater rupture.
- `display_value` on an effect group — cosmetic; a wrong name means the cycle number does not
  render, nothing more.

**Worth checking while you are in there:** whether an AOE target filter restricted to players
exists. The death half of the trigger also lands on nearby zombies, where it is inert — they
run the CVar bookkeeping against their own CVars and have no UI to show it in — but a filter
would be tidier.

**If any of it is wrong:** you lose the journal entries. The escalation itself lives in
`gamestages.xml` and depends on none of this.

### 2. `entitygroups.xml` element form
**Check:** `Data/Config/entitygroups.xml`
V3.0 converted entity groups back to standard XML elements, and V3.2 edited the file again.
Confirm the current child element and attribute names (`<entity name= prob=>` vs something
else) and that the vanilla group names this mod appends to still exist.

### 3. Vanilla entity names used as `Extends` bases
**Check:** `Data/Config/entityclasses.xml`
Every new archetype extends a vanilla zombie. Confirm each base name still exists in V3.2 —
zombie class names have changed across versions, and V3.2 removed the auto-turret, so assume
other removals are possible.

### 4. Workstation window names
**Check:** `Data/Config/blocks.xml` and `Config/XUi_InGame/windows.xml`
New workstations reuse vanilla crafting windows rather than shipping custom UI. Confirm the
window names referenced still exist — V3.0 split XUi into `XUi_Common` / `XUi_InGame` /
`XUi_Menu` and renamed `controls.xml` to `templates.xml`, so anything UI-adjacent is
higher-risk than usual.

---

### 11. Vanilla weapon, tool, armour and explosive `Extends` bases
**Check:** `Data/Config/items.xml`
The gear section of `Config/items.xml` extends vanilla weapons (`gunMGT3M60`,
`gunRifleT3SniperRifle`, `gunMGT2TacticalAR`), tools (`meleeToolPickT3SteelPickaxe`,
`meleeToolAxeT3SteelAxe`, `meleeWpnSledgeT3SteelSledgehammer`, `meleeToolRatchet`), armour
(`armorMilitaryHelmet`, `armorMilitaryVest`, `armorMilitaryLegArmor`), explosives
(`explosiveTimedCharge`, `grenadeContact`), ammo (`ammoArrowSteel`), food
(`foodCharredMeat`) and drugs (`drugSteroids`).
Weapon and armour names change between versions more often than resource names, and V2.0
reworked armour into sets — treat the three armour bases as the highest risk in this list.

### 12. Vanilla block `Extends` bases
**Check:** `Data/Config/blocks.xml`
The fortification section of `Config/blocks.xml` extends `concreteBlock`, `steelBlock`,
`spikesWoodBlock`, `dartTrap`, `bladeTrap` and `chemistryStation`. Block naming shifted
when shape variants landed, so confirm each.
**Already handled:** V3.2 removed the vanilla auto-turret, so the Marshal's "Emplaced Guns"
unlock is built on fixed trap emplacements rather than robotic turrets. Do not reintroduce
a turret base.

### 13. Vanilla infection buff name
**Check:** `Data/Config/buffs.xml`
`Config/buffs.xml` patches `buffInfection` to hand off into this mod's four-stage chain.
That patch is the **only entry point for the entire Attrition pillar** — if the vanilla buff
was renamed in V3.2, infection silently never starts and nothing else reports an error.
Confirm the name, and confirm `RemoveBuff` inside a buff's own effect group is legal.

### 14. Player entity class names and spawn triggers
**Check:** `Data/Config/entityclasses.xml`
`Config/entityclasses.xml` attaches the cycle tracker to `playerMale` and `playerFemale`
via `onSelfFirstSpawn` / `onSelfRespawn`. Confirm both class names still exist and both
triggers fire for players. Without this, `edCycle` is never readable — harmless today
because the announcement layer is inert, but it is a prerequisite for item 1.

### 15. `RandomRoll` requirement
**Check:** `Data/Config/buffs.xml` or `entityclasses.xml`
The archetype infection chances use a `RandomRoll` requirement. Confirm the element name
and its `min`/`max`/`value` attribute shape. If it does not exist under that name, the
effect groups either never fire or always fire — check both.

### 16. Quest structure, and how a trader offers a Proving
**Check:** `Data/Config/quests.xml`
`Config/quests.xml` is the least verifiable file in this mod. Confirm:
- objective type names — `Craft`, `FetchKeep`, `AnimalKill`, `ZombieKill`
- reward type names — `Exp`, `Quest`, `Item`
- the property names carrying strings (`name_key`, `subtitle_key`, `description_key`,
  `offer_key`, `statement_key`)
- **most importantly, how a quest reaches a trader's offer list.** Quest offering has
  changed across versions and these may need a quest tier or group entry, or a hook in
  `traders.xml`, before they appear at all.

Until 16 is resolved the Provings may be uncompletable, and because Writs are no longer
sold, **Callings would then be unreachable**. If you need to unblock a test server before
verifying, temporarily restore the `edWrits` trader group (see the comment in
`traders.xml`) rather than editing the quests.

### 17. `SizeScale`, and the Feral / FeralRadiated variant names
**Check:** `Data/Config/entityclasses.xml`
Every archetype now carries a visual tell built from `SizeScale` plus, in four cases, a
feral or radiated vanilla base. Confirm:
- `SizeScale` exists as an entity-class property and takes a plain multiplier
- the variant names — `zombieArleneFeral`, `zombieSoldierFeral`, `zombieNurseFeral`,
  `zombieFatCopFeralRadiated`. Each class carries its fallback base in a comment, so a
  wrong name is a one-word revert rather than a redesign.
- **the Grinder's inherited death explosion.** `zombieFatCop` explodes on death; on a Titan
  that reads well, but confirm it does not destroy the loot it just dropped.

V2.0 added Charged and Infernal traits. If those have entity variants, they are stronger
tells than feral and worth switching to.

**If SizeScale does not exist**, the archetypes still work — they just lose their
silhouette tell, and the Grinder in particular goes back to being unreadable. Treat that as
blocking for the Grinder specifically.

### 18. Custom mesh bundle and icon atlas pickup
**Check:** in-game, after the Unity step in `docs/ART.md`
- All six workstation icons ship in `UIAtlases/ItemIconAtlas/`, with those blocks'
  `CustomIcon` removed. Confirm the game picks them up from a modlet atlas folder in V3.2 —
  if not, restore `CustomIcon` on each (`forge`, `workbench` or `chemistryStation` to match
  its `Extends`).
- Once `eighthday.unity3d` is built, uncomment the `Meshfile` lines in `blocks.xml` and
  confirm: the bundle was built on the **exact** Unity version the game runs (a mismatch
  fails silently), the prefab names inside match the `?name` suffix, the block sits on the
  ground at the right scale (1 m footprint, pivot at base centre), and the mesh collider
  blocks movement.

### 19. Biome names and spawn attributes
**Check:** `Data/Config/spawning.xml`
`Config/spawning.xml` now touches four biomes: `wasteland`, `burnt_forest`, `desert` and
`snow`. Confirm all four names and the `<spawn maxcount= respawndelay= time= entitygroup=>`
attribute set, including that `time="Day"` is spelled that way.

This matters more than it did when this item only covered The Hollow. Biome hostility is now
the whole of the mod's ambient presence — a wrong biome name means that biome is silently
vanilla, and the archetype it was meant to teach is not met until a horde night brings it.
The mod still loads either way.

Also confirm the starter biome names while you are there (`pine_forest`, `plains`), not
because anything patches them, but because the design depends on knowing which they are.

### 20. Assumed vanilla item values
**Check:** `Data/Config/items.xml`
`tools/check-economy.py` derives every item's price from its recipe, and the leaves of that
tree are vanilla materials whose `EconomicValue` this mod has **guessed** (`VANILLA_COST` in
that file). Correct the table against the real values and re-run with `--fix`; every price in
`items.xml` re-derives from one edit. Wrong assumptions here give prices that are internally
consistent but collectively off — a far better failure than 49 unrelated guesses.

### 21. Crop bases, seed template, and inherited harvest drops
**Check:** `Data/Config/blocks.xml` and `items.xml`
The highest-risk patch in the farm. `Config/blocks.xml` builds each crop's three growth
stages by extending a vanilla crop (`plantedHops`, `plantedCorn`, `plantedGoldenrod`,
`plantedChrysanthemum`), and seeds extend `masterSeed`. Confirm:
- all four vanilla crop names and their `1`/`2`/`3` stage suffixes
- `masterSeed` exists and `Create_item` is how a seed names the block it plants
- **whether a redefined `<drop event="Harvest">` REPLACES the inherited one or stacks.**
  If it stacks, flax plants will drop hops as well as flax. The fix is to extend
  `cropsGrowingMaster` / `cropsGrownMaster` and set `Model` explicitly — which needs the
  vanilla model paths, and is why it was not done that way first.

A wrong crop base is a crop that will not plant. This is the one farming failure that is
loud rather than silent.

### 22. Container sizes, and the deferred backpack
**Check:** `Data/Config/blocks.xml`, and `Config/XUi_*/` for the backpack
- Confirm `cntStorageChest` exists and that `LootSize` takes `cols,rows` in that order.
  A wrong order gives a container the right capacity in the wrong shape — cosmetic, not fatal.
- **The bigger backpack is deliberately not implemented.** It is the most-felt QoL change in
  the genre and it lives in XUi, which V3.0 restructured with a new binding model rather
  than a rename. Every other patch in this mod either loads or silently no-ops; a malformed
  XUi window can leave the game unusable, so this one waits for the real files.

  When you have them, the work is: find the backpack window's grid definition, widen rows
  and columns, and check the container-scaling behaviour at several resolutions. Ship it as
  a **separate optional modlet** rather than folding it into the overhaul, so a server can
  drop it without touching anything else.

### 23. Trader stocking and tier gating
**Check:** `Data/Config/traders.xml`
`Config/traders.xml` appends three stock groups to `/traders/trader_info/items`. Confirm:
- that path reaches every trader, and `<item_group name= count= tier=>` is the right shape
- **how vanilla tiers its own stock.** The `tier` attribute is the intended gate for making
  stock follow the Turning. If V3.2 gates differently, all three tiers are simply available
  from the start — more stock than intended, which is a balance problem, not a break.

Note the previous failure this replaced: the groups existed and nothing stocked them, so
every one was unbuyable. `check-refs.py` now treats an unstocked trader group as an orphan.

### 24. The `ModifyCVar` operation name — check this one first
**Check:** `Data/Config/buffs.xml`, any `action="ModifyCVar"` triggered effect

Every CVar this mod writes uses `operation="set"`. **If the engine spells that differently,
the Calling system does not work at all** — a Writ would set no Mark, every perk branch would
stay shut, and nothing would report an error, because an unset CVar reads as zero and a
CVar gate that never opens is indistinguishable from a gate you have not earned yet.

This is the cheapest item on the list to check and the most expensive to get wrong, so do it
before anything else. Look at any vanilla buff that writes a CVar and copy its spelling.

The fix, if it is wrong, is one `sed` across `Config/`: the mod deliberately uses a single
spelling everywhere, and `check-cvars.py` fails the build if a second one appears. It had
two — `set` and `setvalue` — until that check was written.

Vanilla's other operations (`add`, `subtract`, `multiply`, `divide`) are worth noting while
you are there; nothing here uses them yet.

## Priority 2 — will load but behave wrong

### 5. `CustomIcon` names
**Check:** the game's icon atlas
Every new item borrows a vanilla icon by name. A wrong name shows a missing-icon square —
cosmetic, not fatal, but check them.

### 6. Perk requirement CVars
**Check:** `Data/Config/progression.xml`
The Calling gate uses a CVar requirement on each perk. Confirm the requirement element name
and that perks accept it in V3.2's schema.

### 7. Localization.csv header
**Check:** `Data/Config/Localization.csv`
This mod ships the minimal header (`Key,File,Type,UsedInMainMenu,NoTranslate,english`).
Confirm V3.2 still accepts a partial header; if not, match the vanilla column set exactly.

### 8. Buff stat and effect names
**Check:** `Data/Config/buffs.xml`
The staged infection system references stat names for stamina, health regen and speed
modifiers. Confirm each `CVarName` / `passive_effect` name.

---

## Priority 3 — balance, not correctness

### 9. Gamestage band boundaries
Play-test the Cycle pacing. The bands in `gamestages.xml` are a first estimate of "roughly
every eighth day at typical pace" and will need real data. Log gamestage against day number
on CUKServers for a week and retune.

### 10. Loot probability weights
The Field Note drop rates are guesses. Too low and the research loop stalls; too high and it
trivialises the tech tree.

---

## How to test a load

**Do step 0 first. It answers most of this checklist in about a second, before the game is
even launched.**

```bash
./tools/check-vanilla.py "/path/to/7 Days To Die/Data/Config"
```

That resolves every one of this mod's ~70 XPath patch targets and ~90 referenced vanilla
identifiers against the real files, and prints the ones that are gone. Almost every item on
this list is that question wearing a different hat — *is the vanilla thing we patch still
called that* — and a patch whose target no longer exists is not an error: the game applies
zero edits, logs nothing, and the feature is silently absent.

Work the output top-down, then:

1. Copy `TheEighthDay/` into `Mods/` on a **throwaway** install.
2. Launch and watch the console for red XML errors — they name the file and line.
3. `getgamestage` and `spawnentity` in the console let you jump cycles without playing 48 days.
4. Grep the log for `EIGHTHDAY` — every non-obvious patch is tagged with a comment.

Then work the items `check-vanilla.py` cannot see, because they are about *behaviour* rather
than *existence*: item 24 (the `ModifyCVar` operation spelling — check this before anything
else, it gates the entire Calling system), item 1 (the announcement's requirement and target
names), item 17 (`SizeScale` and the feral variants), item 21 (whether a redefined harvest
drop replaces the inherited one or stacks with it), and every icon name, which lives in a
texture atlas rather than in `Data/Config`.

Fix in priority order. Items 1–4 are the difference between "loads" and "doesn't"; items
11–12 decide whether the Calling payloads exist at all; item 24 decides whether the Callings
can be earned at all.
