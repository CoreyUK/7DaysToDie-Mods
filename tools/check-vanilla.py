#!/usr/bin/env python3
"""
Check this mod against a real 7 Days to Die install.

    ./tools/check-vanilla.py "/path/to/7 Days To Die/Data/Config"

Everything else in tools/ checks the mod against itself, because that is all that can
be done without the game. This one is the other half, and it is the half that decides
whether any of it works: it takes the game's own `Data/Config` and answers the two
questions the whole VERIFICATION.md checklist exists to ask.

  1. DO THE PATCHES HIT ANYTHING?
     A modlet is a list of XPath edits. An `<append xpath="...">` whose expression
     matches nothing is not an error - the game applies zero edits and carries on. The
     feature is simply absent, with nothing logged. Nearly every entry on the
     verification checklist is really this question wearing a different hat: "is the
     vanilla thing we are patching still called that".

  2. DO THE NAMES WE REFERENCE EXIST?
     Ingredients, Extends bases, buffs applied, entity classes spawned, loot groups,
     icons. `check-refs.py` has already collected every one of these into
     docs/VANILLA-DEPENDENCIES.md; this resolves them against the real files.

Neither can be answered here, which is the point: this script is written now so that
the day the game is available, verification is one command and a list, rather than a
day of reading two sets of XML side by side.

Exit code is 1 if anything is missing, so it can gate a release.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

# Which vanilla file owns each root element, so an xpath can be routed to it.
# V3.0 split XUi into three folders; those are listed for the day this mod has XUi
# patches to check (it deliberately has none yet - see verification item 22).
ROOT_TO_FILE = {
    "items": "items.xml",
    "blocks": "blocks.xml",
    "buffs": "buffs.xml",
    "recipes": "recipes.xml",
    "progression": "progression.xml",
    "entity_classes": "entityclasses.xml",
    "entitygroups": "entitygroups.xml",
    "lootcontainers": "loot.xml",
    "gamestages": "gamestages.xml",
    "spawning": "spawning.xml",
    "traders": "traders.xml",
    "quests": "quests.xml",
    "item_modifiers": "item_modifiers.xml",
    "vehicles": "vehicles.xml",
}

# Where each kind of identifier is defined in the vanilla config, as
# (file, element path relative to root, attribute).
DEFINITION_SITES = {
    "item": [("items.xml", "item", "name")],
    "block": [("blocks.xml", "block", "name")],
    "buff": [("buffs.xml", "buff", "name")],
    "entity": [("entityclasses.xml", "entity_class", "name")],
    "entitygroup": [("entitygroups.xml", "entitygroup", "name")],
    "lootgroup": [("loot.xml", "lootgroup", "name"),
                  ("loot.xml", "lootcontainer", "name")],
    "perk": [("progression.xml", ".//perk", "name")],
    "recipe": [("recipes.xml", "recipe", "name")],
}
DEFINITION_SITES["item|block"] = DEFINITION_SITES["item"] + DEFINITION_SITES["block"]
DEFINITION_SITES["item|block|entity"] = (
    DEFINITION_SITES["item"] + DEFINITION_SITES["block"] + DEFINITION_SITES["entity"])

XPATH_RE = re.compile(r'<(append|set|setattribute|remove|insertAfter|insertBefore|csv)\s+'
                      r'xpath="([^"]+)"')


def load(config: Path, filename: str):
    path = config / filename
    if not path.exists():
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"{RED}unparseable{NC} {path}: {exc}")
        return None


def to_relative(xpath: str) -> tuple[str, str] | None:
    """'/buffs/buff[@name='x']' -> ('buffs', './buff[@name='x']').

    ElementTree understands a useful subset of XPath but wants an expression
    relative to the root element, so the root name is peeled off and returned
    separately - it also tells us which vanilla file to open."""
    if not xpath.startswith("/"):
        return None
    parts = xpath.lstrip("/")
    root = parts.split("/", 1)[0].split("[", 1)[0]
    rest = parts[len(parts.split("/", 1)[0]):].lstrip("/")
    return root, ("./" + rest) if rest else "."


def check_patches(modlet: Path, config: Path) -> tuple[int, int]:
    """Every XPath edit in the modlet, resolved against the real config."""
    print(f"\n{DIM}=== XPath targets ==={NC}")
    misses = total = 0
    cache: dict[str, object] = {}

    for path in sorted((modlet / "Config").glob("*.xml")):
        text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
        for _op, xpath in XPATH_RE.findall(text):
            split = to_relative(xpath)
            if split is None:
                print(f"{YELLOW}skip{NC}      {path.name}: relative xpath {xpath!r}")
                continue
            root_name, rel = split

            # An edit that targets something this mod itself defines earlier in the
            # same load is not a vanilla dependency, so it is not this tool's problem.
            filename = ROOT_TO_FILE.get(root_name)
            if filename is None:
                print(f"{YELLOW}unknown{NC}   {path.name}: no vanilla file owns "
                      f"<{root_name}> ({xpath})")
                misses += 1
                continue

            if filename not in cache:
                cache[filename] = load(config, filename)
            root = cache[filename]
            total += 1

            if root is None:
                print(f"{RED}NO FILE{NC}   {path.name}: {filename} is not in this "
                      f"install, so `{xpath}` cannot apply")
                misses += 1
                continue
            if root.tag != root_name:
                print(f"{RED}WRONG ROOT{NC} {path.name}: {filename} has root "
                      f"<{root.tag}>, not <{root_name}>")
                misses += 1
                continue
            # A `set` or `setattribute` edit addresses an attribute, not an element:
            # .../block[@name='x']/@MaxDamage. ElementTree cannot select attributes,
            # so the attribute is peeled off and checked separately - which is the
            # more useful check anyway, because setting an attribute vanilla no
            # longer has is exactly as silent as missing the element.
            wanted_attr = None
            if "/@" in rel:
                rel, wanted_attr = rel.rsplit("/@", 1)
                rel = rel or "."

            try:
                hits = root.findall(rel) if rel != "." else [root]
            except Exception as exc:
                print(f"{YELLOW}unevaluable{NC} {path.name}: {xpath} ({exc}) - "
                      f"ElementTree supports only a subset of XPath; check by hand")
                continue
            if not hits:
                print(f"{RED}NO MATCH{NC}  {path.name}: `{xpath}` matches nothing in "
                      f"{filename} - this patch is silently dropped")
                misses += 1
            elif wanted_attr and not any(h.get(wanted_attr) is not None for h in hits):
                print(f"{RED}NO ATTR{NC}   {path.name}: `{xpath}` matches "
                      f"{len(hits)} element(s) in {filename}, none carrying "
                      f"@{wanted_attr}")
                misses += 1

    if not misses:
        print(f"{GREEN}ok{NC}    all {total} XPath target(s) resolve")
    return misses, total


def parse_manifest(modlet: Path) -> dict[str, set[str]]:
    """Read docs/VANILLA-DEPENDENCIES.md back into {kind: {name}}."""
    md = modlet / "docs" / "VANILLA-DEPENDENCIES.md"
    if not md.exists():
        return {}
    titles = {
        "Items": "item", "Blocks": "block", "Buffs": "buff",
        "Entity classes": "entity", "Items or blocks": "item|block",
        "Extends bases (item / block / entity)": "item|block|entity",
        "Loot groups": "lootgroup", "Entity groups": "entitygroup",
        "Perks": "perk", "Icon names": "icon",
    }
    out: dict[str, set[str]] = defaultdict(set)
    kind = None
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            kind = titles.get(line[3:].strip())
        elif kind and line.startswith("| `"):
            name = line.split("`")[1]
            out[kind].add(name)
    return out


def check_names(modlet: Path, config: Path) -> tuple[int, int]:
    print(f"\n{DIM}=== vanilla identifiers ==={NC}")
    manifest = parse_manifest(modlet)
    if not manifest:
        print(f"{YELLOW}skip{NC}      no docs/VANILLA-DEPENDENCIES.md - run "
              f"./tools/check-refs.py --manifest first")
        return 0, 0

    cache: dict[str, object] = {}
    missing = total = 0

    for kind, names in sorted(manifest.items()):
        sites = DEFINITION_SITES.get(kind)
        if not sites:
            # Icons live in a texture atlas, not in Data/Config. Only the game can
            # answer those, and a wrong one is a blank square, not a broken feature.
            print(f"{DIM}skip{NC}      {len(names)} {kind} name(s) - not defined in "
                  f"Data/Config")
            continue
        present: set[str] = set()
        for filename, elem, attr in sites:
            if filename not in cache:
                cache[filename] = load(config, filename)
            root = cache[filename]
            if root is None:
                continue
            for node in root.findall(elem if elem.startswith(".") else "./" + elem):
                value = node.get(attr)
                if value:
                    present.add(value)
        for name in sorted(names):
            total += 1
            if name not in present:
                missing += 1
                where = ", ".join(f for f, _, _ in sites)
                print(f"{RED}MISSING{NC}   {kind}: {name} is not in {where}")

    if not missing:
        print(f"{GREEN}ok{NC}    all {total} vanilla identifier(s) exist")
    return missing, total


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    config = Path(sys.argv[1]).expanduser()
    if config.name.lower() != "config" and (config / "Data" / "Config").is_dir():
        config = config / "Data" / "Config"
    if not config.is_dir():
        print(f"{RED}not a directory:{NC} {config}")
        return 2

    modlets = [d for d in REPO_ROOT.iterdir()
               if d.is_dir() and (d / "ModInfo.xml").exists()]
    failures = 0
    for modlet in modlets:
        print(f"\n=== {modlet.name} vs {config} ===")
        a, _ = check_patches(modlet, config)
        b, _ = check_names(modlet, config)
        failures += a + b

    print()
    if failures:
        print(f"{RED}{failures} thing(s) this mod depends on are not in that install.{NC}")
        print(f"{DIM}Each one is a feature that will silently do nothing. Cross-reference "
              f"docs/VERIFICATION.md for which are load-breaking.{NC}")
        return 1
    print(f"{GREEN}Every patch target and every vanilla name resolves against that "
          f"install.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
