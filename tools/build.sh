#!/usr/bin/env bash
#
# Package a modlet for release.
#
#   ./tools/build.sh TheEighthDay     ->  dist/TheEighthDay-0.1.0.zip
#   ./tools/build.sh                  ->  builds every modlet
#
# The zip contains the modlet folder at its root, so players can extract straight
# into their Mods/ directory and get Mods/TheEighthDay/ModInfo.xml. Getting this
# nesting wrong is the single most common install failure, so it is asserted below.
#
# Docs and repo furniture are excluded from the shipped zip - they belong on GitHub,
# not in every player's game folder.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; NC=$'\033[0m'

command -v zip >/dev/null 2>&1 || { echo "${RED}zip not found.${NC}"; exit 2; }

if [ $# -gt 0 ]; then
    modlets=("$@")
else
    modlets=()
    for d in */; do
        [ -f "${d}ModInfo.xml" ] && modlets+=("${d%/}")
    done
fi

# Validate before packaging. Never ship a modlet that fails well-formedness.
echo "Validating before build..."
"$REPO_ROOT/tools/validate.sh" "${modlets[@]}" >/dev/null || {
    echo "${RED}Validation failed. Run ./tools/validate.sh for detail.${NC}"
    exit 1
}
echo "${GREEN}Validation passed.${NC}"

mkdir -p dist

for modlet in "${modlets[@]}"; do
    modinfo="$modlet/ModInfo.xml"
    [ -f "$modinfo" ] || { echo "${RED}$modlet has no ModInfo.xml${NC}"; exit 1; }

    version=$(sed -n 's/.*<Version value="\([^"]*\)".*/\1/p' "$modinfo" | head -1)
    [ -n "$version" ] || { echo "${RED}Could not read <Version> from $modinfo${NC}"; exit 1; }

    out="dist/${modlet}-${version}.zip"
    rm -f "$out"

    zip -r -q "$out" "$modlet" \
        -x "$modlet/docs/*" \
        -x "$modlet/CHANGELOG.md" \
        -x "*/.DS_Store"

    # Assert the nesting is right before anyone downloads it.
    if ! unzip -l "$out" | grep -q "$modlet/ModInfo.xml"; then
        echo "${RED}$out has the wrong structure - ModInfo.xml is not at $modlet/ModInfo.xml${NC}"
        exit 1
    fi

    size=$(du -h "$out" | cut -f1)
    echo "${GREEN}built${NC} $out ($size)"
done
