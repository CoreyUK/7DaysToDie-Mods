#!/usr/bin/env python3
"""
Reference-integrity checker for The Eighth Day.

XML well-formedness proves a file parses. It says nothing about whether a recipe
consumes an item that exists, whether a buff being applied was ever defined, or
whether an entity that is spawned has a class. Those bugs load silently and only
show up in play - which, without a game install, means they do not show up at all.

So this walks every cross-reference in the modlet and resolves it:

    recipe ingredients        -> items
    recipe outputs            -> items or blocks
    craft_area                -> a block that provides it
    Extends                   -> item / block / entity base
    AddBuff / RemoveBuff      -> buffs
    entitygroup members       -> entity classes
    spawn groups              -> entitygroups
    LootListOnDeath           -> loot groups
    loot / trader stock       -> items
    ProgressionLevel          -> perks
    every localisation key    -> Localization.csv

References to this mod's own identifiers (the "ed" prefix) MUST resolve - an
unresolved one is a hard error. References to vanilla identifiers cannot be
checked without the game, so they are collected instead and written to a
dependency manifest, turning eventual verification into a mechanical pass.

    ./tools/check-refs.py                    # check every modlet
    ./tools/check-refs.py --manifest         # also write the vanilla manifest
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFIX = "ed"

GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

# Craft areas the base game provides. Anything else must be supplied by a block
# in this modlet via CraftingAreaRecipes.
VANILLA_CRAFT_AREAS = {
    "workbench", "campfire", "forge", "chemistryStation", "cementMixer",
    "beaker", "advancedForge", "player", "",
}


class Modlet:
    def __init__(self, root: Path):
        self.root = root
        self.name = root.name
        self.config = root / "Config"

        self.defined: dict[str, set[str]] = defaultdict(set)
        self.refs: list[tuple[str, str, str, str]] = []   # kind, name, where, why
        self.craft_areas_provided: set[str] = set()
        self.loc_keys: set[str] = set()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    # -- collection -------------------------------------------------------

    def load(self):
        if not self.config.is_dir():
            return
        for path in sorted(self.config.glob("*.xml")):
            try:
                tree = ET.parse(path)
            except ET.ParseError as e:
                self.errors.append(f"{path.name}: unparseable ({e})")
                continue
            self._scan(tree.getroot(), path.name)

        loc = self.config / "Localization.csv"
        if loc.is_file():
            with loc.open(newline="", encoding="utf-8") as fh:
                for i, row in enumerate(csv.reader(fh)):
                    if i == 0 or not row:
                        continue
                    if row[0].strip():
                        self.loc_keys.add(row[0].strip())

    def _scan(self, node, where: str):
        tag = node.tag
        attr = node.attrib

        # ---- definitions ----
        define_tags = {
            "item": "item", "block": "block", "buff": "buff",
            "entity_class": "entity", "entitygroup": "entitygroup",
            "lootgroup": "lootgroup", "perk": "perk",
            "trader_item_group": "tradergroup",
        }
        if tag in define_tags and "name" in attr:
            self.defined[define_tags[tag]].add(attr["name"])

        # Quests are keyed by id rather than name, unlike everything else.
        if tag == "quest" and "id" in attr:
            self.defined["quest"].add(attr["id"])

        # ---- references ----
        if tag == "ingredient" and "name" in attr:
            self.refs.append(("item", attr["name"], where, "recipe ingredient"))

        if tag == "recipe":
            if "name" in attr:
                self.refs.append(("item|block", attr["name"], where, "recipe output"))
            if "craft_area" in attr:
                self.refs.append(("craft_area", attr["craft_area"], where, "craft_area"))

        if tag == "property":
            pname, pval = attr.get("name"), attr.get("value")
            if pname == "Extends" and pval:
                self.refs.append(("item|block|entity", pval, where, "Extends"))
            elif pname == "LootListOnDeath" and pval:
                self.refs.append(("lootgroup", pval, where, "LootListOnDeath"))
            elif pname == "CustomIcon" and pval:
                self.refs.append(("icon", pval, where, "CustomIcon"))
            elif pname == "CraftingAreaRecipes" and pval:
                for area in pval.split(","):
                    self.craft_areas_provided.add(area.strip())
            elif pname == "DescriptionKey" and pval:
                self.refs.append(("loc", pval, where, "DescriptionKey"))
            elif pname and pname.endswith("_key") and pval:
                # quests carry their strings as properties rather than attributes
                if pname not in ("category_key",):
                    self.refs.append(("loc", pval, where, pname))

        if tag == "triggered_effect" and attr.get("buff"):
            self.refs.append(("buff", attr["buff"], where,
                              attr.get("action", "triggered_effect")))

        if tag == "entity" and "name" in attr:
            self.refs.append(("entity", attr["name"], where, "entitygroup member"))

        if tag == "spawn" and "group" in attr:
            self.refs.append(("entitygroup", attr["group"], where, "gamestage spawn"))

        if tag == "item" and "name" in attr and "count" in attr:
            # an <item> carrying a count is loot/trader stock, not a definition
            self.refs.append(("item", attr["name"], where, "loot/trader stock"))

        if tag == "item_group" and "name" in attr:
            self.refs.append(("tradergroup", attr["name"], where, "trader stock list"))

        if tag == "reward" and attr.get("id"):
            rtype = attr.get("type", "")
            if rtype == "Quest":
                self.refs.append(("quest", attr["id"], where, "quest reward chain"))
            elif rtype in ("Item", "LootItem"):
                self.refs.append(("item", attr["id"], where, f"{rtype} reward"))

        if tag == "objective" and attr.get("id"):
            self.refs.append(("item|block", attr["id"], where,
                              f"{attr.get('type', 'objective')} objective"))

        if tag == "requirement" and attr.get("progression_name"):
            self.refs.append(("perk", attr["progression_name"], where,
                              "ProgressionLevel"))

        # localisation keys carried as attributes
        for key_attr in ("name_key", "description_key", "desc_key"):
            if attr.get(key_attr):
                self.refs.append(("loc", attr[key_attr], where, key_attr))

        # a defined item/block/buff/entity also needs a display-name string
        if tag in ("item", "block", "entity_class") and "name" in attr \
                and "count" not in attr:
            self.refs.append(("loc?", attr["name"], where, "display name"))

        for child in node:
            self._scan(child, where)

    # -- checking ---------------------------------------------------------

    def _pool(self, kind: str) -> set[str]:
        pool: set[str] = set()
        for k in kind.split("|"):
            pool |= self.defined.get(k, set())
        return pool

    def check(self):
        vanilla: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for kind, name, where, why in self.refs:
            if not name:
                continue

            if kind == "craft_area":
                if name in VANILLA_CRAFT_AREAS:
                    continue
                if name in self.craft_areas_provided:
                    continue
                self.errors.append(
                    f"{where}: craft_area '{name}' is provided by no block "
                    f"(no CraftingAreaRecipes supplies it)")
                continue

            if kind in ("loc", "loc?"):
                if name in self.loc_keys:
                    continue
                if kind == "loc":
                    self.errors.append(
                        f"{where}: localisation key '{name}' ({why}) missing "
                        f"from Localization.csv")
                else:
                    self.warnings.append(
                        f"{where}: '{name}' has no display-name string in "
                        f"Localization.csv")
                continue

            if kind == "icon":
                vanilla["icon"].append((name, where))
                continue

            if name.startswith(PREFIX):
                if name not in self._pool(kind):
                    self.errors.append(
                        f"{where}: {why} references '{name}' which this modlet "
                        f"never defines as {kind.replace('|', ' or ')}")
            else:
                vanilla[kind].append((name, where))

        # Definitions nothing points at. The mirror image of an unresolved
        # reference and just as silent: an entity group with no spawner, a buff
        # nothing applies, a loot group no entity drops. The mod loads and the
        # feature simply is not in the game.
        referenced_names = {n for _, n, _, _ in self.refs}
        # things that are legitimately entry points rather than referenced
        ENTRY_POINTS = {
            "item": "craftable/lootable by the player",
            "block": "placeable by the player",
            "perk": "spendable in the skill tree",
            "quest": "offered by a trader",
        }
        for kind, names in sorted(self.defined.items()):
            if kind in ENTRY_POINTS:
                continue
            for name in sorted(names):
                if name not in referenced_names:
                    self.warnings.append(
                        f"orphan: {kind} '{name}' is defined but nothing references it")

        # orphaned localisation strings
        referenced_loc = {n for k, n, _, _ in self.refs if k in ("loc", "loc?")}
        for key in sorted(self.loc_keys):
            if key in referenced_loc:
                continue
            if key.endswith("Desc") and key[:-4] in referenced_loc:
                continue
            base = re.sub(r"(Name|Desc)$", "", key)
            if base in referenced_loc or base in self.loc_keys:
                continue
            self.warnings.append(
                f"Localization.csv: '{key}' is defined but nothing references it")

        return vanilla


def report(m: Modlet, vanilla, show_warnings=True) -> int:
    print(f"\n=== {m.name} ===")
    counts = ", ".join(f"{len(v)} {k}" for k, v in sorted(m.defined.items()) if v)
    print(f"{DIM}defines: {counts}{NC}")
    print(f"{DIM}internal references checked: "
          f"{sum(1 for k, n, _, _ in m.refs if n.startswith(PREFIX))}{NC}")

    for w in m.warnings if show_warnings else []:
        print(f"{YELLOW}warn{NC}  {w}")
    for e in m.errors:
        print(f"{RED}FAIL{NC}  {e}")

    if not m.errors:
        print(f"{GREEN}ok{NC}    every internal reference resolves")

    total = sum(len(v) for v in vanilla.values())
    print(f"{DIM}vanilla identifiers depended on: {total} "
          f"({len(set(n for v in vanilla.values() for n, _ in v))} unique){NC}")
    return len(m.errors)


def write_manifest(m: Modlet, vanilla):
    out = m.root / "docs" / "VANILLA-DEPENDENCIES.md"
    kinds = {
        "item": "Items", "block": "Blocks", "buff": "Buffs",
        "entity": "Entity classes", "item|block": "Items or blocks",
        "item|block|entity": "Extends bases (item / block / entity)",
        "lootgroup": "Loot groups", "entitygroup": "Entity groups",
        "perk": "Perks", "icon": "Icon names",
    }

    lines = [
        "# Vanilla Dependencies",
        "",
        "**Generated by `tools/check-refs.py --manifest`. Do not edit by hand.**",
        "",
        "Every vanilla identifier this mod depends on, and where it is used. These",
        "cannot be verified without a game install, which is exactly why they are",
        "listed: with `Data/Config/` open, confirming them is a mechanical pass",
        "rather than a hunt through the modlet.",
        "",
        "A name that no longer exists in the target build fails **silently** - the",
        "mod loads and the feature simply does nothing. See `VERIFICATION.md` for",
        "which of these are load-breaking and which merely misbehave.",
        "",
    ]
    grand = 0
    for kind, title in kinds.items():
        entries = vanilla.get(kind)
        if not entries:
            continue
        byname: dict[str, set[str]] = defaultdict(set)
        for name, where in entries:
            byname[name].add(where)
        grand += len(byname)
        lines += [f"## {title}", "", "| Identifier | Referenced from |", "|---|---|"]
        for name in sorted(byname):
            lines.append(f"| `{name}` | {', '.join(sorted(byname[name]))} |")
        lines.append("")

    lines += [f"---", "", f"**{grand} unique vanilla identifiers.**", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{DIM}manifest: {out.relative_to(REPO_ROOT)}{NC}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modlets", nargs="*")
    ap.add_argument("--manifest", action="store_true",
                    help="write docs/VANILLA-DEPENDENCIES.md")
    ap.add_argument("--quiet", action="store_true", help="errors only")
    args = ap.parse_args()

    if args.modlets:
        roots = [REPO_ROOT / n for n in args.modlets]
    else:
        roots = [d for d in sorted(REPO_ROOT.iterdir())
                 if d.is_dir() and (d / "ModInfo.xml").exists()]

    if not roots:
        print("No modlets found.")
        return 1

    failures = 0
    for root in roots:
        m = Modlet(root)
        m.load()
        vanilla = m.check()
        failures += report(m, vanilla, show_warnings=not args.quiet)
        if args.manifest:
            write_manifest(m, vanilla)

    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
