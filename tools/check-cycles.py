#!/usr/bin/env python3
"""
Check that the Turning agrees with itself.

The Turning is described in four places that have no way of noticing each other:

    entitygroups.xml   which archetype each Cycle pool actually introduces
    gamestages.xml     which pool each gamestage band actually spawns
    entityclasses.xml  which Cycle each archetype announces on first contact
    Localization.csv   what the announcement says entered the world
    docs/CYCLES.md     the table players and the designer both read

Nothing in the game or in the other checkers relates those to each other. Retune the
bands, reorder a pool, or rename an archetype and every one of them still loads, still
resolves, still prices - and the dawn message calmly names the wrong monster.

That is not a cosmetic failure in this mod. The stated difficulty principle is "hard in
ways you can see coming", and an announcement that lies is worse than no announcement:
it teaches the player to prepare for the wrong thing. So the agreement is checked.

Six invariants:

  1. CUMULATIVE POOLS   pool N contains everything in pool N-1. A Turning is permanent
                        and one-way; an archetype that can leave the world breaks the
                        entire mechanic, not just the schedule.
  2. ONE ARRIVAL        pool N introduces exactly one archetype. Two at once means one
                        of them has no Cycle of its own and can never be announced.
  3. BANDS ASCEND       gamestage bands rise, and map to the Cycle pools in order.
  4. HOOKED             the archetype introduced at Cycle N is the one that announces
                        Cycle N, and nothing announces a Cycle it does not introduce.
  5. TEXT AGREES        the announcement text for Cycle N names that archetype.
  6. DOCS AGREE         the CYCLES.md table names it too.

Usage:  ./tools/check-cycles.py [modlet ...]     (default: every modlet in the repo)
"""

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

POOL_RE = re.compile(r'<entitygroup\s+name="edCycle(\d+)Pool"\s*>(.*?)</entitygroup>', re.S)
ENTITY_RE = re.compile(r'<entity\s+name="([^"]+)"')
BAND_RE = re.compile(r'<gamestage\s+stage="(\d+)"\s*>(.*?)</gamestage>', re.S)
SPAWN_RE = re.compile(r'<spawn\s+group="(edCycle(\d+)Pool)"')
CLASS_RE = re.compile(r'<entity_class\s+name="(ed[A-Za-z0-9_]+)"(.*?)</entity_class>', re.S)
TURNBUFF_RE = re.compile(r'buff="edBuffTurning(\d+)"')
BUFFDEF_RE = re.compile(r'<buff\s+name="edBuffTurning(\d+)"([^>]*)>')


def pools(text: str) -> dict[int, list[str]]:
    out = {}
    for cycle, body in POOL_RE.findall(text):
        out[int(cycle)] = ENTITY_RE.findall(body)
    return out


def bands(text: str) -> list[tuple[int, int]]:
    """(stage, cycle) for the blood moon spawner, in file order."""
    m = re.search(r'<append\s+xpath="[^"]*BloodMoonHordes[^"]*"\s*>(.*?)</append>',
                  text, re.S)
    if not m:
        return []
    body = m.group(1)
    out = []
    for stage, inner in BAND_RE.findall(body):
        for _, cycle in SPAWN_RE.findall(inner):
            out.append((int(stage), int(cycle)))
    return out


def announcements(text: str) -> dict[str, set[int]]:
    """archetype -> the Cycles it announces."""
    out = {}
    for name, body in CLASS_RE.findall(text):
        found = {int(n) for n in TURNBUFF_RE.findall(body)}
        if found:
            out[name] = found
    return out


def display_names(csv_path: Path) -> dict[str, str]:
    if not csv_path.exists():
        return {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {r[0]: r[5] for r in csv.reader(fh) if len(r) > 5}


def doc_table(md_path: Path) -> dict[int, str]:
    """Cycle -> the 'Enters the world' cell of the CYCLES.md table."""
    if not md_path.exists():
        return {}
    out = {}
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*\*\*(\d+)\+?\*\*\s*\|[^|]*\|([^|]*)\|", line)
        if m:
            out[int(m.group(1))] = m.group(2).strip()
    return out


def check(modlet: Path) -> int:
    cfg = modlet / "Config"
    needed = ["entitygroups.xml", "gamestages.xml", "entityclasses.xml", "buffs.xml"]
    if not all((cfg / f).exists() for f in needed):
        print(f"{YELLOW}skip{NC}  {modlet.name} (no cycle system)")
        return 0

    pool = pools((cfg / "entitygroups.xml").read_text())
    if not pool:
        print(f"{YELLOW}skip{NC}  {modlet.name} (no edCycleNPool groups)")
        return 0

    band = bands((cfg / "gamestages.xml").read_text())
    hooks = announcements((cfg / "entityclasses.xml").read_text())
    buffs_text = (cfg / "buffs.xml").read_text()
    defined_buffs = {int(n) for n, _ in BUFFDEF_RE.findall(buffs_text)}
    names = display_names(cfg / "Localization.csv")
    docs = doc_table(modlet / "docs" / "CYCLES.md")

    problems: list[str] = []
    cycles = sorted(pool)

    # --- 1 & 2: cumulative pools, one arrival each -------------------------
    intro: dict[int, str] = {}
    previous: list[str] = []
    for c in cycles:
        current = pool[c]
        lost = [e for e in previous if e not in current]
        if lost:
            problems.append(
                f"{RED}LEAVES{NC}    Cycle {c} pool has dropped {', '.join(lost)} - "
                f"a Turning is permanent and one-way")
        new = [e for e in current if e not in previous]
        if len(new) == 1:
            intro[c] = new[0]
        elif len(new) == 0:
            # Legitimate for a repeated top band; only flag inside the ramp.
            if c != max(cycles):
                problems.append(
                    f"{RED}NO ARRIVAL{NC} Cycle {c} introduces nothing new, so it has "
                    f"nothing to announce")
        else:
            problems.append(
                f"{RED}TWO AT ONCE{NC} Cycle {c} introduces {len(new)} archetypes "
                f"({', '.join(new)}) - only one can own the Cycle")
        previous = current

    # --- 3: bands ascend and map to pools in order -------------------------
    last_stage, last_cycle = -1, 0
    for stage, cycle in band:
        if stage <= last_stage:
            problems.append(
                f"{RED}BAND ORDER{NC} gamestage {stage} does not follow {last_stage}")
        if cycle < last_cycle:
            problems.append(
                f"{RED}BAND ORDER{NC} gamestage {stage} spawns Cycle {cycle} after "
                f"Cycle {last_cycle} - the world would walk backwards")
        last_stage, last_cycle = stage, cycle
    unbanded = [c for c in intro if c not in {cy for _, cy in band}]
    if unbanded:
        problems.append(
            f"{RED}NEVER SPAWNS{NC} Cycle pool(s) {', '.join(map(str, unbanded))} are "
            f"defined but no gamestage band spawns them")

    # --- 4: the right archetype announces the right Cycle ------------------
    for cycle, arch in sorted(intro.items()):
        claimed = hooks.get(arch, set())
        if not claimed:
            problems.append(
                f"{RED}SILENT{NC}    {arch} arrives at Cycle {cycle} and announces "
                f"nothing - the player is never told the world Turned")
        elif cycle not in claimed:
            problems.append(
                f"{RED}MISMATCH{NC}  {arch} arrives at Cycle {cycle} but announces "
                f"Cycle {sorted(claimed)[0]}")
    owner = {c: a for c, a in intro.items()}
    for arch, claimed in sorted(hooks.items()):
        for c in sorted(claimed):
            if owner.get(c) != arch:
                problems.append(
                    f"{RED}IMPOSTOR{NC}  {arch} announces Cycle {c}, which belongs to "
                    f"{owner.get(c, 'nothing')}")
            if c not in defined_buffs:
                problems.append(
                    f"{RED}NO BUFF{NC}   {arch} adds edBuffTurning{c}, which is not defined")

    # --- 5 & 6: the words agree with the mechanism -------------------------
    for cycle, arch in sorted(intro.items()):
        shown = names.get(arch)
        if not shown:
            problems.append(f"{RED}NO NAME{NC}   {arch} has no localised display name")
            continue
        desc = names.get(f"edBuffTurning{cycle}Desc")
        if desc is None:
            if cycle in defined_buffs:
                problems.append(
                    f"{RED}NO TEXT{NC}   edBuffTurning{cycle}Desc is missing, so the "
                    f"Cycle {cycle} announcement says nothing")
        elif shown.lower() not in desc.lower():
            problems.append(
                f"{RED}LIES{NC}      the Cycle {cycle} announcement never names "
                f"{shown!r} - it reads: {desc[:60]}...")
        cell = docs.get(cycle)
        if cell and shown.lower() not in cell.lower():
            problems.append(
                f"{RED}DOC DRIFT{NC} CYCLES.md says Cycle {cycle} brings {cell!r}, "
                f"the pools bring {shown!r}")

    for p in problems:
        print(p)

    if not problems:
        order = " -> ".join(f"{c}:{names.get(a, a)}" for c, a in sorted(intro.items()))
        print(f"{DIM}cycles: {order}{NC}")
        print(f"{GREEN}ok{NC}    {modlet.name}: {len(intro)} Cycle(s) - pools, bands, "
              f"announcements, text and docs all agree")
    return len(problems)


def main() -> int:
    if len(sys.argv) > 1:
        modlets = [REPO_ROOT / name for name in sys.argv[1:]]
    else:
        modlets = [d for d in REPO_ROOT.iterdir()
                   if d.is_dir() and (d / "ModInfo.xml").exists()]
    if not modlets:
        print("No modlets found.")
        return 1
    print()
    return 1 if sum(check(m) for m in modlets) else 0


if __name__ == "__main__":
    sys.exit(main())
