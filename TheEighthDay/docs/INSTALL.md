# Installation

**Game build:** 7 Days to Die **V3.2** (Henpocalypse). Other versions are not supported.

> ⚠️ **v0.1.0 is pre-alpha and has never been loaded by the game.** Install it on a throwaway
> copy first and work through [`VERIFICATION.md`](VERIFICATION.md). Do not put this on a live
> server yet.

---

## Client (single player)

1. Find your game folder — in Steam: **right-click 7 Days to Die → Manage → Browse local files**.
2. Create a `Mods` folder there if one doesn't exist.
3. Copy the whole **`TheEighthDay`** folder into it.

You should end up with:

```
7 Days to Die/
└── Mods/
    └── TheEighthDay/
        ├── ModInfo.xml
        └── Config/
```

If you see `Mods/TheEighthDay/TheEighthDay/ModInfo.xml`, you've nested it one level too deep.

4. **Start a brand new save.** This is an overhaul — existing saves will break.
5. **EAC must be off.** Launch through the launcher and untick Easy Anti-Cheat, or use the
   `-noeac` launch option. The game will refuse to load modded XML with EAC on.

---

## Dedicated server

1. Copy `TheEighthDay` into the server's `Mods` folder, same structure as above.
2. Copy the **identical** folder to every client that will connect.
3. Wipe the world and player data — `Saves/` and the region files for the world you're using.
4. Restart the server and watch the console output on first boot.

### Version matching is not optional

7 Days to Die does **not** push config XML to clients. Every player must have the exact same
version of the mod as the server. A client on 0.1.0 connecting to a server on 0.1.1 will get
unknown-block and unknown-item errors, or will be kicked outright.

Pin a version, tell your players which one, and don't hot-update the server mid-wipe.

---

## Verifying it loaded

On startup the console prints the loaded mod list. Look for:

```
Loaded Mod: CUK_TheEighthDay (0.1.0)
```

Then in game, `F1` console:

- `getgamestage` — shows your current gamestage, which determines your Cycle
  (band table is in [`CYCLES.md`](CYCLES.md))
- `giveself edResourceCrudeIron 10` — if this resolves, `items.xml` patched correctly

Red XML errors in the console name the file and the line. Cross-reference against
[`VERIFICATION.md`](VERIFICATION.md) before reporting a bug.

---

## Uninstalling

Delete the `TheEighthDay` folder from `Mods/` and start a new save. You cannot cleanly revert
an existing world — every block and item this mod added will be missing, and the save will be
full of holes.

---

## Compatibility

**Assume nothing else is compatible.** This mod rewrites progression, items, blocks, recipes,
loot and spawning. Anything else touching those files will conflict, and last-loaded wins.

- Server-side-only utilities (chat bots, admin tools, log parsers) — generally fine
- Cosmetic and QoL modlets that don't touch config XML — usually fine
- Anything touching `progression.xml`, `items.xml`, `blocks.xml`, `recipes.xml`,
  `entitygroups.xml` or `loot.xml` — will conflict

Load order is alphabetical by folder name. If you must run a conflicting modlet, rename its
folder so it loads after `TheEighthDay` and accept that its changes win.
