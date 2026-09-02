#!/usr/bin/env python3
"""
Check the CVars this mod runs on.

CVars are the mod's only persistent per-player state. Calling Marks, the infection
cure guard, the Turning's cycle read and its once-ever announcement flags are all
CVars, and every one of them is a gate: something writes it, something else reads it
and refuses to fire until it says the right thing.

Nothing validates that pairing. An unset CVar reads as zero, so a gate whose CVar is
never written is not an error - it is a door that quietly never opens. The perk tree
would look complete, load clean, resolve every reference, and grant nothing.

Three checks:

  1. UNWRITTEN   a CVar is read by a requirement and written by nothing. That gate can
                 never open. This is the expensive one - it is how a whole Calling
                 branch becomes unreachable without a single error message.
  2. UNREAD      a CVar is written and never read. Dead bookkeeping, or the read was
                 meant to exist and does not.
  3. VOCABULARY  the modlet writes CVars with more than one spelling of the same
                 operation. Exactly one of them is the engine's, and the other fails
                 silently - so this is not a style question, it is a live bug in
                 whichever half is wrong.

Usage:  ./tools/check-cvars.py [modlet ...]     (default: every modlet in the repo)
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GREEN, RED, YELLOW, DIM, NC = (
    "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[2m", "\033[0m")

# A CVar written by a triggered effect: action="ModifyCVar" ... cvar="x" operation="y"
WRITE_RE = re.compile(
    r'action="ModifyCVar"[^>]*?cvar="([^"]+)"[^>]*?operation="([^"]+)"', re.S)
# ... and the same attributes in the other order, which is legal XML.
WRITE_ALT_RE = re.compile(
    r'action="ModifyCVar"[^>]*?operation="([^"]+)"[^>]*?cvar="([^"]+)"', re.S)
# A CVar read by a gate.
READ_RE = re.compile(r'name="CVarCompare"[^>]*?cvar="([^"]+)"', re.S)

# Spellings of "assign this value" that cannot all be right at once.
ASSIGN_SYNONYMS = {"set", "setvalue", "setValue", "assign", "="}


def scan(modlet: Path):
    writes: dict[str, set[str]] = defaultdict(set)   # cvar -> files
    reads: dict[str, set[str]] = defaultdict(set)
    ops: dict[str, set[str]] = defaultdict(set)      # operation -> files

    cfg = modlet / "Config"
    if not cfg.is_dir():
        return writes, reads, ops

    for path in sorted(cfg.glob("*.xml")):
        text = path.read_text(encoding="utf-8")
        # Comments describe what the code should do; they are not the code.
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        for cvar, op in WRITE_RE.findall(text):
            writes[cvar].add(path.name)
            ops[op].add(path.name)
        for op, cvar in WRITE_ALT_RE.findall(text):
            writes[cvar].add(path.name)
            ops[op].add(path.name)
        for cvar in READ_RE.findall(text):
            reads[cvar].add(path.name)
    return writes, reads, ops


def check(modlet: Path) -> int:
    writes, reads, ops = scan(modlet)
    if not writes and not reads:
        print(f"{YELLOW}skip{NC}  {modlet.name} (no CVars)")
        return 0

    problems = []

    for cvar in sorted(set(reads) - set(writes)):
        where = ", ".join(sorted(reads[cvar]))
        problems.append(
            f"{RED}UNWRITTEN{NC}  {cvar} gates something in {where} and nothing ever "
            f"writes it - an unset CVar reads as zero, so that gate never opens")

    for cvar in sorted(set(writes) - set(reads)):
        where = ", ".join(sorted(writes[cvar]))
        problems.append(
            f"{RED}UNREAD{NC}     {cvar} is written in {where} and read by nothing")

    assign_used = {op for op in ops if op.lower() in {s.lower() for s in ASSIGN_SYNONYMS}}
    if len(assign_used) > 1:
        detail = "; ".join(
            f'"{op}" in {", ".join(sorted(ops[op]))}' for op in sorted(assign_used))
        problems.append(
            f"{RED}VOCABULARY{NC} ModifyCVar assigns with {len(assign_used)} different "
            f"operation names - {detail}. Only one is the engine's; the other fails "
            f"silently wherever it is used")

    for p in problems:
        print(p)

    if not problems:
        vocab = ", ".join(sorted(ops))
        print(f"{DIM}cvars: {len(writes)} written, {len(reads)} read; "
              f"operations used: {vocab}{NC}")
        print(f"{GREEN}ok{NC}    {modlet.name}: every CVar gate has a writer and every "
              f"written CVar has a reader")
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
