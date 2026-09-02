# Item Icon Atlas

Drop custom item icons here as PNGs named **exactly** after the item or block `name`
attribute in `Config/items.xml` / `Config/blocks.xml` — e.g. `edResourceCarbide.png`.

- PNG, 32-bit with alpha
- 160 x 160 px
- Transparent background, ~8 px padding
- Case-sensitive filename match

The game builds the atlas at load; no code or SDK required. When you add an icon here,
delete that item's `CustomIcon` and `CustomIconTint` properties so the atlas takes over.

Full specification and style guide: [`../../docs/ART.md`](../../docs/ART.md)
