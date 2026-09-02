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

### 1. Blood-moon / dawn detection for the Turning announcement
**Check:** `Data/Config/buffs.xml`
The announcement layer in `Config/buffs.xml` needs a requirement that reads "it is dawn and
last night was a horde night". Confirm the exact requirement name the game exposes (candidates
to look for: an `IsBloodMoon`-style requirement, a `TimeOfDay` requirement, or a readable
world-time CVar).
**Until confirmed:** the announcement effect group is commented out and marked
`EIGHTHDAY-VERIFY-1`. The gamestage driver in `gamestages.xml` carries the mechanic without
it, so the mod is fully playable — you just don't get the dawn message.

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

1. Copy `TheEighthDay/` into `Mods/` on a **throwaway** install.
2. Launch and watch the console for red XML errors — they name the file and line.
3. `getgamestage` and `spawnentity` in the console let you jump cycles without playing 48 days.
4. Grep the log for `EIGHTHDAY` — every non-obvious patch is tagged with a comment.

Fix in priority order. Items 1–4 are the difference between "loads" and "doesn't"; items
11–12 decide whether the Calling payloads exist at all.
