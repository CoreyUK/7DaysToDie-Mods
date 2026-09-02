# Server Operator Guide

Written for people running this on real hardware with real players — i.e. for CUKServers, and
for anyone else who asks permission first (see [LICENSE](../../LICENSE)).

---

## V3.0+ changed how server config works

If you last ran a 7DTD server on V2.x, the biggest change is **SandboxCode**. More than two
dozen `serverconfig.xml` properties (`GameDifficulty`, `XPMultiplier`, `BloodMoonFrequency`
and friends) were removed in V3.0 in favour of a single `SandboxCode` value.

The workflow now:

1. Start a local single-player game and set the sandbox options you want in the UI.
2. Copy the generated sandbox code.
3. Paste it as the single `SandboxCode` value in `serverconfig.xml`.

Don't try to hand-edit the removed properties — they're ignored.

---

## Sandbox settings this mod is tuned around

The Eighth Day assumes roughly default sandbox values. It provides its own difficulty; adding
more on top compounds badly.

| Setting | Recommended | Why |
|---|---|---|
| Blood moon frequency | **7 days** | Cycles are named and paced off a 7-day horde. Change this and "the Eighth Day" stops meaning anything. |
| Blood moon count | Default or lower | The mod raises horde quality, not quantity. Stacking both is unplayable by Cycle 4. |
| XP multiplier | **100%** | The stretched progression curve is tuned at 1×. Raising it fast-forwards you into cycles you aren't equipped for. |
| Loot abundance | 100% | Loot is already retuned. |
| Day length | 60 min | Cycle pacing estimates assume this. |
| Difficulty | Warrior or below to start | Mod difficulty is on top of this, not instead of it. |

The mod's own tuning knobs live in `Config/gamestages.xml` (cycle pace) — prefer changing
those over sandbox settings, because they're what the balance is actually built on.

---

## Wipe policy

Cycles are permanent and one-way, and gamestage only goes up. A long-running server drifts
into Cycle 7+ where the intended experience is attrition, not progress.

Recommended: **wipe every 8–10 weeks.** Long enough for a group to reach the late production
tier, short enough that the server isn't permanently in Grinder territory.

Announce wipes well ahead. This mod asks for a lot of player investment, and people take it
badly if it vanishes without warning.

---

## Performance notes

- New enemy archetypes are stat and buff variants of vanilla entities — no new meshes, so no
  additional memory or draw-call cost over vanilla equivalents.
- Cycle 5+ raises concurrent entity counts. If you're already near your entity cap on
  vanilla, expect to lower `MaxSpawnedZombies` before Cycle 5, not after.
- The staged infection system adds per-player buff ticks. Negligible for under 20 players;
  worth watching above that.

---

## Updating a live server

1. **Never** hot-swap the mod folder on a running server.
2. Announce, stop the server, back up `Saves/`.
3. Replace the mod folder on the server **and** publish the same version to players.
4. Restart and check the console for XML errors before letting anyone in.

Point releases (0.1.0 → 0.1.1) that only change balance values are usually save-safe. Anything
that adds or renames blocks or items is **not** save-safe and needs a wipe. The changelog says
which is which for every release.

---

## Reporting problems

Console log first, always. Red XML errors name the file and line. Grep for `EIGHTHDAY` — every
non-obvious patch carries a tagged comment so you can find what changed a value.

Known-unverified areas are listed in [`VERIFICATION.md`](VERIFICATION.md); check there before
raising anything.
