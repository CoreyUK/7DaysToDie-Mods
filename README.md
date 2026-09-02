# 7 Days to Die Mods

Source collection for my 7 Days to Die mods, built and maintained for **CUKServers**.

Everything here targets the current stable game build. Each mod lives in its own top-level
folder and ships as a self-contained modlet — drop the folder into `Mods/`, done.

| Mod | Type | Game build | Status |
|---|---|---|---|
| [The Eighth Day](TheEighthDay/) | Overhaul | V3.2 (Henpocalypse) | Pre-alpha (v0.5.0) |

---

## The Eighth Day

> *You survived seven days. The eighth is when it starts.*

A full overhaul built around one idea: **the world escalates faster than you do.**

Vanilla's power curve peaks and then flattens — by day 50 you are farming the apocalypse.
The Eighth Day removes that ceiling. Every horde night you survive, the world *Turns*:
new enemy archetypes enter the spawn pool permanently, loot shifts, and biomes you had
written off as safe stop being safe. You never finish the game. You only last longer.

Core pillars:

- **Callings** — six specialist paths earned through trader proving-work, not bought.
- **The Long Craft** — a deep, tiered production chain with real intermediate industry.
- **The Turning** — permanent, one-way world escalation tied to horde nights.
- **Attrition** — staged infection, harsher durability, meaningful medicine.

Full design docs: [`TheEighthDay/docs/DESIGN.md`](TheEighthDay/docs/DESIGN.md)

### This is original work

The Eighth Day is not a fork, reskin or derivative of any existing overhaul. No third-party
XML, assets, code or config are used. Design pillars common to the genre (class systems,
extended tech trees, escalating threat) are implemented from scratch with their own naming,
balance and mechanics.

---

## Repo layout

```
7DaysToDie-Mods/
├── TheEighthDay/          # the overhaul modlet — this is what you copy into Mods/
│   ├── ModInfo.xml
│   ├── Config/            # all XPath patches, mirrors the game's Data/Config
│   └── docs/              # design, install, server and verification docs
├── tools/                 # packaging + local validation scripts
└── .github/workflows/     # XML well-formedness CI
```

## Building a release

```bash
./tools/build.sh TheEighthDay          # -> dist/TheEighthDay-0.1.0.zip
./tools/validate.sh                    # XML well-formedness across every modlet
```

Windows equivalent: `tools\build.ps1`.

## Licence

**Proprietary — all rights reserved.** See [LICENSE](LICENSE).

Short version:

- ✅ **You may** download it, play it, and run it on your own server — including a public or
  donation-supported one.
- ✅ **You may** modify your own copy for your own server.
- ❌ **You may not** reupload, mirror, repackage, bundle into a modpack, publish a fork or
  derivative, sell it, or reuse its XML, values or text in another project.

Any of the above needs written permission first — ask in
[Discord](https://discord.cukservers.net) and the answer is usually yes.

> **Note on GitHub forks:** GitHub's Terms of Service let any user fork a public repo through
> GitHub's interface, and that operates independently of this licence. A fork made that way
> does not grant permission to redistribute or publish derivative work — see section 4 of the
> licence. Making the repo private is the only way to remove that platform permission.

## Links

- Website: [cukservers.net](https://cukservers.net)
- Discord: [discord.cukservers.net](https://discord.cukservers.net)
