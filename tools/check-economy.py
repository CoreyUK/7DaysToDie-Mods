#!/usr/bin/env python3
"""
Economy consistency checker for The Eighth Day.

Every item carries an EconomicValue that sets its trader price. Written by hand,
those are 49 unrelated guesses - and a guess that lands below an item's own input
cost is not just untidy, it is a trader exploit: buy the inputs, craft, sell the
output, repeat.

This derives each craftable item's cost from its recipe, recursively, and checks
the declared value against it.

    ./tools/check-economy.py            # report
    ./tools/check-economy.py --fix      # rewrite EconomicValue in items.xml

THE RULE
    EconomicValue should sit at CRAFT_MARGIN x derived input cost. Crafting adds
    value because your labour and your workstation are worth something, but not
    so much that the trader becomes a mint.

    Below 1.0x  -> exploitable, and the chain loses money to build. Always wrong.
    Far above   -> the item is a money printer via bought inputs.

VANILLA COSTS ARE ASSUMPTIONS. The table below is this mod's single source of
truth for what vanilla materials are worth. It is guesses - but it is guesses in
ONE place that can be corrected in one edit, rather than smeared across 49 items.
Confirm against Data/Config/items.xml when you have the game (VERIFY-20).
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "TheEighthDay" / "Config"

CRAFT_MARGIN = 1.25          # value added by crafting
TOLERANCE = 0.35             # how far from target before it is worth reporting
UTILITY_CAP = 2.5            # see below

# Some things are genuinely worth more than the sum of their materials. A gas
# grenade is not "some powder and a tin", it is area denial at the moment you
# need it, and a serum is the only thing standing between somebody and a
# terminal infection. Those get a premium.
#
# The cap exists because the premium is also the exploit: at some multiple of
# input cost, buying inputs from a trader and selling the crafted output becomes
# a mint. UTILITY_CAP is where that line sits. Nothing may exceed it, however
# useful it is.
#
# Anything absent from this table is priced at plain CRAFT_MARGIN - materials
# and intermediates should never carry a premium, because they ARE the cost
# everything else is measured against.
UTILITY = {
    # medicine - the Apothecary's whole reason to exist
    "edMedSerum": 2.5, "edMedAntibiotic": 2.0, "edMedTincture": 1.8,
    # ordnance - worth more than its powder at the moment it matters
    "edExpGasGrenade": 2.5, "edExpShapedCharge": 2.0, "edExpMiningCharge": 1.8,
    "edToxinCoating": 1.8,
    # stimulants - two minutes of being better, at a price
    "edDrugCombatStim": 2.2, "edDrugSteadyHand": 2.2,
    # preserved food - the point is that it survives being carried
    "edFoodPemmican": 2.0, "edFoodCuredMeat": 1.8,
    # ammunition - specialist rounds beat their metal
    "edAmmoToxinArrow": 1.8, "edAmmoBodkinArrow": 1.5,
    # finished weapons, armour and tools - end products, not stock
    "edWeaponMarshalCarbine": 1.6, "edWeaponSupportMG": 1.5,
    "edWeaponMarksmanRifle": 1.5, "edMeleeCarbideMaul": 1.4,
    "edToolCarbidePickaxe": 1.35, "edToolCarbideAxe": 1.35, "edToolSalvageRig": 1.4,
    "edArmorCompositeVest": 1.4, "edArmorCompositeLegs": 1.4,
    "edArmorCompositeHelmet": 1.4,
    # efficiency item - goes further than what you poured in
    "edVehicleFuelCell": 2.0,
}

GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

# Cost basis for everything that is NOT crafted: vanilla materials, and this
# mod's crops. A crop has no recipe - it comes out of the ground - so like ore
# it is a leaf of the cost tree, priced for the plot, seed and days it took
# rather than for materials consumed.
VANILLA_COST = {
    # farm primary production
    "edCropFlax": 10, "edCropRye": 10, "edCropComfrey": 14, "edCropRapeseed": 12,
    "resourceIronFragment": 1, "resourceCoal": 2, "resourceCrushedSand": 1,
    "resourceBone": 2, "resourceForgedIron": 12, "resourceForgedSteel": 40,
    "resourceMechanicalParts": 60, "resourceElectricParts": 60,
    "resourceOil": 10, "resourceAcid": 90, "resourceNitratePowder": 3,
    "resourceWaterBottle": 8, "resourcePaper": 2, "resourceCement": 6,
    "resourceClayLump": 1, "resourceStone": 1, "resourceWood": 1,
    "resourceCloth": 3, "resourceGlue": 8, "resourceGunPowder": 6,
    "resourceHerbalAntibiotics": 150, "drugAntibiotics": 250,
    "resourceFeather": 2, "foodRawMeat": 12, "foodAnimalFat": 10,
    "foodCharredMeat": 20, "resourceGasCan": 6, "ammoArrowSteel": 20,
    "resourceRottingFlesh": 1,
}


def parse():
    items, recipes = {}, {}

    root = ET.parse(CONFIG / "items.xml").getroot()
    for it in root.iter("item"):
        name = it.get("name")
        if not name or it.get("count"):
            continue
        for p in it.iter("property"):
            if p.get("name") == "EconomicValue":
                items[name] = int(float(p.get("value")))

    for f in ("recipes.xml",):
        root = ET.parse(CONFIG / f).getroot()
        for rc in root.iter("recipe"):
            name = rc.get("name")
            if not name:
                continue
            out = int(rc.get("count", 1))
            ings = [(i.get("name"), int(i.get("count", 1))) for i in rc.iter("ingredient")]
            if not ings:
                continue
            # research recipes reconstruct from notes and are not a production
            # route - costing an item by them makes nonsense of the ladder
            if "edResearch" in (rc.get("tags") or ""):
                continue
            # Keep EVERY route. Picking one up front by a proxy like "fewest
            # ingredients" is how the farm broke this: the alternative polymer
            # recipe went through a crop that had no cost basis, so polymer -
            # and composite plate, and every medicine downstream of it - all
            # silently became uncostable. Cost them all, take the cheapest that
            # actually prices, because that is the one a player will exploit.
            recipes.setdefault(name, []).append((out, ings))
    return items, recipes


def cost_of(name, items, recipes, memo, stack=()):
    if name in memo:
        return memo[name]
    if name in VANILLA_COST:
        memo[name] = float(VANILLA_COST[name])
        return memo[name]
    if name in stack:                      # recipe cycle - break it
        return None
    routes = recipes.get(name)
    if not routes:
        memo[name] = None
        return None
    best = None
    for out, ings in routes:
        total = 0.0
        ok = True
        for ing, cnt in ings:
            c = cost_of(ing, items, recipes, memo, stack + (name,))
            if c is None:
                ok = False
                break
            total += c * cnt
        if ok:
            unit = total / max(out, 1)
            best = unit if best is None else min(best, unit)
    memo[name] = best
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                    help="rewrite EconomicValue in items.xml to the derived target")
    args = ap.parse_args()

    items, recipes = parse()
    memo: dict[str, float | None] = {}

    rows, unpriced, fixes = [], [], {}
    for name in sorted(items):
        c = cost_of(name, items, recipes, memo)
        if c is None:
            unpriced.append(name)
            continue
        mult = min(UTILITY.get(name, CRAFT_MARGIN), UTILITY_CAP)
        target = round(c * mult)
        declared = items[name]
        ratio = declared / c if c else 0
        rows.append((name, c, declared, target, ratio))
        # Below input cost is the exploit condition, not a matter of taste, so
        # it is always a fix regardless of how close to target it happens to
        # land. TOLERANCE only governs cosmetic drift above 1.0x.
        if ratio < 1.0 or abs(declared - target) / max(target, 1) > TOLERANCE:
            fixes[name] = target

    print(f"\n{DIM}craftable items priced from their recipes: {len(rows)}"
          f"   uncosted (no recipe / vanilla-only inputs unknown): {len(unpriced)}{NC}")
    print(f"{DIM}target = input cost x {CRAFT_MARGIN}, or the item's UTILITY "
          f"premium (capped at {UTILITY_CAP}x){NC}\n")
    print(f"{'item':34} {'inputs':>9} {'declared':>9} {'target':>8} {'ratio':>7}")
    print("-" * 72)
    exploit = 0
    for name, c, declared, target, ratio in sorted(rows, key=lambda r: -r[1]):
        flag = ""
        if ratio < 1.0:
            flag, exploit = f" {RED}<- below input cost{NC}", exploit + 1
        elif name in fixes:
            flag = f" {YELLOW}<- off target{NC}"
        print(f"{name:34} {c:9.1f} {declared:9d} {target:8d} {ratio:6.2f}x{flag}")

    if unpriced:
        print(f"\n{DIM}uncosted: {', '.join(unpriced)}{NC}")

    print()
    if exploit:
        print(f"{RED}{exploit} item(s) priced below their own input cost - "
              f"buy inputs, craft, sell, repeat.{NC}")
    if fixes:
        print(f"{YELLOW}{len(fixes)} item(s) more than "
              f"{int(TOLERANCE * 100)}% off target.{NC}")
    if not fixes and not exploit:
        print(f"{GREEN}every priced item sits within tolerance of its input cost.{NC}")

    if args.fix and fixes:
        path = CONFIG / "items.xml"
        text = path.read_text()
        for name, target in fixes.items():
            pat = re.compile(
                r'(<item name="' + re.escape(name) + r'">.*?'
                r'<property name="EconomicValue" value=")\d+(" />)', re.S)
            text, n = pat.subn(lambda m: m.group(1) + str(target) + m.group(2), text, count=1)
            if not n:
                print(f"{RED}could not rewrite {name}{NC}")
        path.write_text(text)
        print(f"{GREEN}rewrote {len(fixes)} EconomicValue(s) in items.xml{NC}")

    return 1 if exploit else 0


if __name__ == "__main__":
    sys.exit(main())
