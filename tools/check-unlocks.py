#!/usr/bin/env python3
"""
Cross-check perk RecipeUnlock tags against the recipes that are meant to satisfy them.

A perk that unlocks nothing is a perk nobody spends a point on, and it is completely
invisible to XML well-formedness checking - the mod loads fine and the tree is just
hollow. v0.1 shipped with two thirds of its unlocks unbacked, which is why this exists.

Also enforces the trader rule: THE TRADER SELLS INPUTS, NEVER A CALLING'S
OUTPUT. A Calling whose product sits on a shelf is a Calling nobody needs, and
that pillar is too easy to erode one convenient stock entry at a time.

Reports three failure modes:
  * UNBACKED - a perk promises a recipe tag that no recipe carries
  * ORPHAN   - a recipe is tagged for a perk unlock that no perk references
  * FOR SALE - a perk-gated item appears in trader stock

Usage:  ./tools/check-unlocks.py [modlet ...]     (default: every modlet in the repo)
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UNLOCK_RE = re.compile(r'tags="(edRecipe[A-Za-z0-9_]+)"')
TAGS_RE = re.compile(r'tags="([^"]+)"')

GREEN, RED, YELLOW, NC = "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[0m"


def gated_items(recipes_text: str) -> set[str]:
    """Items whose only route is a Calling perk: tagged edRecipe* AND flagged
    unlocked_by_recipe="false" so they cannot be learned any other way."""
    out = set()
    for m in re.finditer(r'<recipe\s+([^>]*?)/?>', recipes_text):
        a = m.group(1)
        if "edRecipe" in a and 'unlocked_by_recipe="false"' in a:
            n = re.search(r'name="([^"]+)"', a)
            if n:
                out.add(n.group(1))
    return out


def trader_stock(modlet: Path) -> set[str]:
    traders = modlet / "Config" / "traders.xml"
    if not traders.exists():
        return set()
    return set(re.findall(r'<item name="([^"]+)"\s+count=', traders.read_text()))


def check(modlet: Path) -> int:
    progression = modlet / "Config" / "progression.xml"
    recipes = modlet / "Config" / "recipes.xml"

    if not progression.exists() or not recipes.exists():
        print(f"{YELLOW}skip{NC}  {modlet.name} (no progression.xml/recipes.xml)")
        return 0

    promised = set(UNLOCK_RE.findall(progression.read_text()))

    delivered: set[str] = set()
    for group in TAGS_RE.findall(recipes.read_text()):
        delivered.update(t.strip() for t in group.split(","))

    unbacked = sorted(promised - delivered)
    orphaned = sorted({t for t in delivered if t.startswith("edRecipe")} - promised)

    for tag in unbacked:
        print(f"{RED}UNBACKED{NC}  {tag} - a perk unlocks it, no recipe provides it")
    for tag in orphaned:
        print(f"{RED}ORPHAN{NC}    {tag} - a recipe is tagged for it, no perk unlocks it")

    # the trader rule
    gated = gated_items(recipes.read_text())
    for_sale = sorted(gated & trader_stock(modlet))
    for name in for_sale:
        print(f"{RED}FOR SALE{NC}  {name} is perk-gated but appears in trader stock - "
              f"a Calling whose product can be bought is a Calling nobody needs")

    if not unbacked and not orphaned and not for_sale:
        print(f"{GREEN}ok{NC}    {modlet.name}: {len(promised)} unlock tag(s) all backed; "
              f"{len(gated)} perk-gated item(s), none purchasable")

    return len(unbacked) + len(orphaned) + len(for_sale)


def main() -> int:
    if len(sys.argv) > 1:
        modlets = [REPO_ROOT / name for name in sys.argv[1:]]
    else:
        modlets = [d for d in REPO_ROOT.iterdir()
                   if d.is_dir() and (d / "ModInfo.xml").exists()]

    if not modlets:
        print("No modlets found.")
        return 1

    return 1 if sum(check(m) for m in modlets) else 0


if __name__ == "__main__":
    sys.exit(main())
