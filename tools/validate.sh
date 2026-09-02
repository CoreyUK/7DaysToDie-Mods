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
        expected=$(head -1 "$csv" | awk -F',' '{print NF}')
        # NB: "exp" is a reserved function name in awk - do not use it as a variable.
        bad=$(awk -F',' -v want="$expected" 'NR>1 && NF>0 && NF!=want {print NR": "NF" cols"}' "$csv")
        if [ -n "$bad" ]; then
            # A quoted field containing a comma is legal and will trip the naive count,
            # so this is a warning rather than a hard failure.
            warn "$csv rows whose column count differs from the header ($expected):"
            echo "$bad" | sed 's/^/        /'
        else
            pass "$csv ($expected columns)"
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
else
    warn "python3 not found - skipping perk unlock coverage check"
fi

echo
if [ "$errors" -eq 0 ]; then
    echo "${GREEN}All $checked file(s) passed.${NC}"
    exit 0
else
    echo "${RED}$errors error(s) across $checked file(s).${NC}"
    exit 1
fi
