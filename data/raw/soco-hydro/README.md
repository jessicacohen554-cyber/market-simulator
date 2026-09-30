# SOCO hydro — derived per-plant forebay storage

`soco_hydro_pondage.csv`: one row per SOCO conventional-hydro plant with identified storage (41 plants,
3,311 MW). It is written by `scripts/data/build_hydro_pondage.py --iso SOCO`: USACE NID `Max Storage` ×
NID head (hydraulic height, else the labelled NID-height proxy), turbine efficiency 1.0. The plant→dam link is
ORNL HILARRI v4. There are zero fitted constants (rule 21 `[R-FROZEN-DERIVE]`), and the file is re-derived only
when NID, HILARRI or EHA publish a new vintage, never because a residual moved. Every dam is SOCO's own
(rule 25 `[R-ISO-SCOPE]`).

**Source subset:** `data/raw/nid/nid_soco_hydro_dams.csv` (vintage 2026-9-23). The subset rebuilds this file
**byte-identical** to a build from the full national export. The sha256 is in `SHA256SUMS.txt`.

**Upper bound, stated.** `Max Storage` is a reservoir volume, not the licensed operating band, and η = 1.0.
Both over-state what a plant can hold, so the bound this file feeds can only be too loose, never too tight.

**Consumer:** `data/hydro.py::load_hydro_pondage`, only when `ScenarioConfig.hydro_pondage_bound` is armed
(not armed in any committed SOCO run). Phase-0 record: `docs/handoffs/r-soco/FINDING-soco-93-pondage-phase0-2026-09-30.md`.

Regenerate:

```
curl -sSL "https://nid.sec.usace.army.mil/api/nation/csv" -o nid_nation.csv
uv run python scripts/data/build_hydro_pondage.py --iso SOCO --nid-csv nid_nation.csv
```
