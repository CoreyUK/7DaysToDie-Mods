#!/usr/bin/env bash
#
# Validate every modlet in this repo.
#
#   ./tools/validate.sh              # all modlets
#   ./tools/validate.sh TheEighthDay # one modlet
#
# Checks performed:
#   1. XML well-formedness on every .xml file
#   2. ModInfo.xml exists and carries the required v2 fields
#   3. Every Config/*.xml uses <configs> as its root (modlets are XPath patches)
#   4. Localization.csv has a consistent column count on every row
#   5. Perk unlocks are backed by real recipes, and no gated item is for sale
#   6. Every internal cross-reference resolves
#   7. Everything is obtainable from a cold start
#   8. The Turning's pools, bands, announcements, text and docs all agree
#   9. Nothing is priced below its own input cost
#
# This does NOT check that vanilla identifiers exist - only the game can do that.
# See TheEighthDay/docs/VERIFICATION.md.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; NC=$'\033[0m'
errors=0
checked=0

fail() { echo "${RED}FAIL${NC}  $*"; errors=$((errors + 1)); }
warn() { echo "${YELLOW}WARN${NC}  $*"; }
pass() { echo "${GREEN}ok${NC}    $*"; }

if ! command -v xmllint >/dev/null 2>&1; then
    echo "${RED}xmllint not found.${NC} Install libxml2-utils (Debian/Ubuntu) or libxml2 (macOS)."
    exit 2
fi

# Which modlets? A modlet is any top-level dir containing a ModInfo.xml.
if [ $# -gt 0 ]; then
    modlets=("$@")
else
    modlets=()
    for d in */; do
        [ -f "${d}ModInfo.xml" ] && modlets+=("${d%/}")
    done
fi

if [ ${#modlets[@]} -eq 0 ]; then
    echo "No modlets found (looking for top-level dirs containing ModInfo.xml)."
    exit 1
fi

for modlet in "${modlets[@]}"; do
    echo
    echo "=== $modlet ==="

    # --- 2. ModInfo.xml -----------------------------------------------------
    modinfo="$modlet/ModInfo.xml"
    if [ ! -f "$modinfo" ]; then
        fail "$modlet has no ModInfo.xml"
        continue
    fi
    for field in Name DisplayName Version Description Author; do
        if ! grep -q "<$field value=" "$modinfo"; then
            fail "$modinfo is missing required field <$field value=... />"
        fi
    done

    # --- 1. XML well-formedness --------------------------------------------
    while IFS= read -r -d '' xml; do
        checked=$((checked + 1))
        if out=$(xmllint --noout "$xml" 2>&1); then
            pass "$xml"
        else
            fail "$xml"
            echo "$out" | sed 's/^/        /'
        fi

        # --- 3. Config files must be XPath patch documents ------------------
        case "$xml" in
            "$modlet"/Config/*)
                root=$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null)
                if [ "$root" != "configs" ]; then
                    fail "$xml root element is <$root>, expected <configs>"
                fi
                ;;
        esac
    done < <(find "$modlet" -name '*.xml' -type f -print0)

    # --- 4. Localization.csv column consistency -----------------------------
    csv="$modlet/Config/Localization.csv"
    if [ -f "$csv" ]; then
        checked=$((checked + 1))
        # Parsed as real CSV, not by counting commas: localisation prose contains
        # commas and is legitimately quoted, which a naive count mis-reports.
        if command -v python3 >/dev/null 2>&1; then
            if out=$(python3 - "$csv" <<'PY'
import csv, sys
path = sys.argv[1]
with open(path, newline="", encoding="utf-8") as fh:
    rows = [r for r in csv.reader(fh) if r]
want = len(rows[0])
bad = [(i + 1, len(r)) for i, r in enumerate(rows) if len(r) != want]
if bad:
    print(f"expected {want} columns; offending rows: "
          + ", ".join(f"line {n} has {c}" for n, c in bad[:10]))
    sys.exit(1)
print(f"{len(rows) - 1} entries, {want} columns")
PY
            ); then
                pass "$csv ($out)"
            else
                fail "$csv: $out"
            fi
        else
            warn "python3 not found - skipping $csv structure check"
        fi
    fi
done

# --- 5. Perk unlocks must be backed by real recipes -------------------------
# Invisible to XML checking: the mod loads fine with a hollow perk tree.
if command -v python3 >/dev/null 2>&1; then
    echo
    echo "=== perk unlock coverage ==="
    if ! python3 "$REPO_ROOT/tools/check-unlocks.py" "${modlets[@]}"; then
        errors=$((errors + 1))
    fi

    # --- 6. Every internal cross-reference must resolve ---------------------
    # Recipes consuming items that do not exist, buffs applied but never
    # defined, entities spawned with no class. All load silently.
    echo
    if ! python3 "$REPO_ROOT/tools/check-refs.py" "${modlets[@]}" --quiet; then
        errors=$((errors + 1))
    fi

    # --- 7. Everything must be obtainable from a cold start -----------------
    # A deadlock resolves, prices, and validates perfectly. The player just
    # cannot get there, and finds out forty hours in.
    echo
    if ! python3 "$REPO_ROOT/tools/check-progression.py" "${modlets[@]}"; then
        fail "unreachable content - run ./tools/check-progression.py"
    fi

    # --- 8. The Turning must agree with itself ------------------------------
    # Pools, gamestage bands, announcements, journal text and the docs table are
    # five descriptions of one mechanic with no way to notice each other.
    echo
    if ! python3 "$REPO_ROOT/tools/check-cycles.py" "${modlets[@]}"; then
        fail "the Turning contradicts itself - run ./tools/check-cycles.py"
    fi

    # --- 9. No item may be priced below its own input cost ------------------
    # That is a trader exploit: buy the inputs, craft, sell the output, repeat.
    echo
    if ! python3 "$REPO_ROOT/tools/check-economy.py" >/dev/null; then
        fail "items priced below their input cost - run ./tools/check-economy.py"
    fi
else
    warn "python3 not found - skipping perk unlock and reference checks"
fi

echo
if [ "$errors" -eq 0 ]; then
    echo "${GREEN}All $checked file(s) passed.${NC}"
    exit 0
else
    echo "${RED}$errors error(s) across $checked file(s).${NC}"
    exit 1
fi
