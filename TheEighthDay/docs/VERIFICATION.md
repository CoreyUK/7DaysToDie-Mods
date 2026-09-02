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
