#!/usr/bin/env python3
"""
Cold-start reachability analysis for The Eighth Day.

Every other check in this repo asks "is this reference valid". This one asks the
question that actually matters to a player: **starting with nothing, can you get
there at all?**

That is a different failure and a much nastier one. Every identifier can resolve,
every price can be consistent, and the mod can still contain a deadlock - a thing
whose only recipe needs its own output, or a Calling whose Proving demands
something only that Calling can make. Nothing reports it. The player simply
cannot progress, and finds out forty hours in.

This repo has already shipped one: seeds were craftable only from crops, crops
grew only from seeds, and the one thing breaking the circle - trader stock - was
defined but wired to nothing. The farm could not be started. It was found by
accident. This is so the next one is not.

HOW IT WORKS
    Fixpoint closure over everything a player can obtain.

    Seeds of the closure (obtainable with no prerequisites):
        - every vanilla item          (assumed present in the world)
        - anything in a loot table
        - anything in trader stock
        - NOT crop harvests. Harvesting is downstream of planting, which is
          downstream of the seed. Treating a harvest as free was the first
          version's bug: it made the checker blind to the exact circular
          dependency it exists to find.

    Then repeat until nothing new is reachable:
        - a RECIPE fires if its craft_area is reachable, every ingredient is
          reachable, and its perk gate (if any) is satisfied
        - a BLOCK provides its craft_area once the block itself is reachable
        - a SEED plants a crop block; a reachable crop block makes its harvest
          drops reachable. That is what closes the seed/crop loop honestly
        - a MARK is reachable once its Writ is
        - a WRIT is reachable once its Proving chain is completable END TO END.
          Stages are linked by their "next quest" reward, and a stage is only
          completable if its predecessor is. Checking stages in isolation was
          the second version's bug: the Writ hangs off the LAST stage, so an
          impossible stage 1 went unnoticed while stage 3 looked fine.

    Anything still unreachable at the end cannot be obtained by any route.

    ./tools/check-progression.py            # report
    ./tools/check-progression.py --trace X  # explain how X is reached, or why not
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFIX = "ed"

GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

VANILLA_CRAFT_AREAS = {
    "workbench", "campfire", "forge", "chemistryStation", "cementMixer",
    "beaker", "advancedForge", "player", "",
}


class World:
    def __init__(self, modlet: Path):
        self.cfg = modlet / "Config"
        self.name = modlet.name

        self.defined_items: set[str] = set()
        self.defined_blocks: set[str] = set()
        self.recipes: list[dict] = []
        self.area_of_block: dict[str, list[str]] = {}
        self.from_loot: set[str] = set()
        self.from_trader: set[str] = set()
        self.plants_from_seed: dict[str, str] = {}      # seed item -> stage-1 block
        self.next_stage: dict[str, str] = {}            # stage block -> next stage
        self.harvest_of: dict[str, list[str]] = {}      # stage block -> drops
        self.gate_of_tag: dict[str, str] = {}      # edRecipeX -> edMarkY
        self.writ_of_mark: dict[str, str] = {}     # edMarkY -> edWritY
        self.quest_chain: dict[str, list[dict]] = defaultdict(list)  # writ -> quests
        self.why: dict[str, str] = {}

    # ---------------------------------------------------------------- load
    def load(self):
        def root(f):
            p = self.cfg / f
            return ET.parse(p).getroot() if p.exists() else None

        # items and where they come from for free
        r = root("items.xml")
        if r is not None:
            for it in r.iter("item"):
                n = it.get("name")
                if n and not it.get("count"):
                    self.defined_items.add(n)
                    # a Writ grants a Mark when consumed
                    for te in it.iter("triggered_effect"):
                        if te.get("action") == "ModifyCVar" and te.get("cvar", "").startswith("edMark"):
                            self.writ_of_mark[te.get("cvar")] = n
                    # a seed plants a block
                    for pr in it.iter("property"):
                        if pr.get("name") == "Create_item" and pr.get("value"):
                            self.plants_from_seed[n] = pr.get("value")

        r = root("blocks.xml")
        if r is not None:
            for b in r.iter("block"):
                n = b.get("name")
                if not n:
                    continue
                self.defined_blocks.add(n)
                for p in b.iter("property"):
                    if p.get("name") == "CraftingAreaRecipes" and p.get("value"):
                        self.area_of_block[n] = [a.strip() for a in p.get("value").split(",")]
                # growth chain and harvest yield, kept per-block so they stay
                # gated behind actually having planted the thing
                for p in b.iter("property"):
                    if p.get("name") == "PlantGrowing.Next" and p.get("value"):
                        self.next_stage[n] = p.get("value")
                drops = [d.get("name") for d in b.iter("drop")
                         if d.get("event") == "Harvest" and d.get("name")]
                if drops:
                    self.harvest_of[n] = drops

        r = root("recipes.xml")
        if r is not None:
            for rc in r.iter("recipe"):
                n = rc.get("name")
                if not n:
                    continue
                ings = [i.get("name") for i in rc.iter("ingredient") if i.get("name")]
                self.recipes.append(dict(
                    out=n, area=rc.get("craft_area", ""), ings=ings,
                    tags=set((rc.get("tags") or "").split(",")),
                    gated=rc.get("unlocked_by_recipe") == "false"))

        for f, bucket in (("loot.xml", self.from_loot), ("traders.xml", self.from_trader)):
            r = root(f)
            if r is None:
                continue
            for it in r.iter("item"):
                if it.get("name") and it.get("count"):
                    bucket.add(it.get("name"))

        # which Mark unlocks which recipe tag
        r = root("progression.xml")
        if r is not None:
            for perk in r.iter("perk"):
                mark = None
                for req in perk.iter("requirement"):
                    if req.get("name") == "CVarCompare" and req.get("cvar", "").startswith("edMark"):
                        mark = req.get("cvar")
                if not mark:
                    continue
                for pe in perk.iter("passive_effect"):
                    if pe.get("name") == "RecipeUnlock" and pe.get("tags"):
                        self.gate_of_tag[pe.get("tags")] = mark

        # Proving chains: which quests reward which Writ, and what they demand
        r = root("quests.xml")
        if r is not None:
            for q in r.iter("quest"):
                qid = q.get("id")
                objs = [o.get("id") for o in q.iter("objective") if o.get("id")]
                writ = None
                nxt = None
                for rw in q.iter("reward"):
                    if rw.get("type") == "Item":
                        writ = rw.get("id")
                    elif rw.get("type") == "Quest":
                        nxt = rw.get("id")
                self.quest_chain[qid] = dict(objs=objs, writ=writ, next=nxt)

    def _predecessors(self):
        """stage -> the stage that unlocks it, from the next-quest rewards."""
        if not hasattr(self, "_pred"):
            self._pred = {}
            for qid, q in self.quest_chain.items():
                if q.get("next"):
                    self._pred[q["next"]] = qid
        return self._pred

    def _chain_blocker(self, qid, reach):
        """Walk back to the head of the chain. Returns the first stage that
        cannot be completed, or None if the whole chain is clear."""
        pred = self._predecessors()
        seen, cur = set(), qid
        while cur and cur not in seen:
            seen.add(cur)
            q = self.quest_chain.get(cur)
            if not q:
                return cur
            for o in q["objs"]:
                if o not in reach:
                    return cur
            cur = pred.get(cur)
        return None

    # ------------------------------------------------------------- closure
    def solve(self):
        reach: set[str] = set()

        def add(name, why):
            if name and name not in reach:
                reach.add(name)
                self.why[name] = why

        # seeds of the closure
        for n in self.from_loot:
            add(n, "found in loot")
        for n in self.from_trader:
            add(n, "bought from a trader")
        # every vanilla identifier referenced anywhere is assumed obtainable
        for rc in self.recipes:
            for i in rc["ings"]:
                if not i.startswith(PREFIX):
                    add(i, "vanilla")
        for q in self.quest_chain.values():
            for o in q["objs"]:
                if not o.startswith(PREFIX):
                    add(o, "vanilla")

        marks: set[str] = set()

        changed = True
        while changed:
            changed = False

            # planting a reachable seed makes its crop - and then everything
            # that crop drops - reachable
            for seed, plant in self.plants_from_seed.items():
                if seed in reach and plant not in reach:
                    add(plant, f"planted from {seed}")
                    changed = True
            for stage, nxt in self.next_stage.items():
                if stage in reach and nxt not in reach:
                    add(nxt, f"grows from {stage}")
                    changed = True
            for stage, drops in self.harvest_of.items():
                if stage in reach:
                    for d in drops:
                        if d not in reach:
                            add(d, f"harvested from {stage}")
                            changed = True

            # a Proving chain grants its Writ only if EVERY stage is completable
            for qid, q in self.quest_chain.items():
                if q["writ"] and q["writ"] not in reach:
                    blocked = self._chain_blocker(qid, reach)
                    if blocked is None:
                        add(q["writ"], f"reward for completing {qid}")
                        changed = True

            # consuming a Writ grants its Mark
            for mark, writ in self.writ_of_mark.items():
                if mark not in marks and writ in reach:
                    marks.add(mark)
                    changed = True

            # craft areas provided by reachable blocks
            areas = set(VANILLA_CRAFT_AREAS)
            for blk, provided in self.area_of_block.items():
                if blk in reach:
                    areas.update(provided)

            for rc in self.recipes:
                if rc["out"] in reach:
                    continue
                if rc["area"] not in areas:
                    continue
                if not all(i in reach for i in rc["ings"]):
                    continue
                gate = None
                for tag in rc["tags"]:
                    if tag in self.gate_of_tag:
                        gate = self.gate_of_tag[tag]
                if gate and gate not in marks:
                    continue
                add(rc["out"], f"crafted at {rc['area'] or 'hand'}"
                               + (f" once {gate} is earned" if gate else ""))
                changed = True

        self.reach = reach
        self.marks = marks
        return reach, marks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modlets", nargs="*")
    ap.add_argument("--trace", help="explain how one item is reached")
    args = ap.parse_args()

    roots = ([REPO_ROOT / n for n in args.modlets] or
             [d for d in sorted(REPO_ROOT.iterdir())
              if d.is_dir() and (d / "ModInfo.xml").exists()])

    failures = 0
    for root in roots:
        w = World(root)
        w.load()
        reach, marks = w.solve()

        ours = {n for n in w.defined_items | w.defined_blocks if n.startswith(PREFIX)}
        # growth-stage crop blocks are placed by a seed, not crafted or looted
        ours = {n for n in ours if not re.match(r"^edPlant\w+[123]$", n)}
        unreachable = sorted(ours - reach)

        print(f"\n=== {root.name} ===")
        print(f"{DIM}obtainable: {len(ours & reach)}/{len(ours)} of this mod's items and "
              f"blocks   Callings earnable: {len(marks)}/6{NC}")

        if args.trace:
            n = args.trace
            print(f"\n{n}: {w.why.get(n, RED + 'UNREACHABLE by any route' + NC)}")

        for n in unreachable:
            print(f"{RED}UNREACHABLE{NC}  {n} - no recipe, loot, trader or quest route")
        missing_marks = {m for m in w.writ_of_mark} - marks
        for m in sorted(missing_marks):
            writ = w.writ_of_mark[m]
            stage = next((q for q, d in w.quest_chain.items() if d.get("writ") == writ), None)
            blocker = w._chain_blocker(stage, reach) if stage else None
            detail = f" - stage {blocker} demands something unobtainable" if blocker else ""
            print(f"{RED}UNEARNABLE{NC}   {m}: its Proving cannot be completed{detail}")

        if not unreachable and not missing_marks:
            print(f"{GREEN}ok{NC}    every item is obtainable from a cold start, "
                  f"and all six Callings can be earned")
        failures += len(unreachable) + len(missing_marks)

    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
