# LMP component decomposition (`lmp-components`) — raw holding

Per-node hourly LMP with published congestion (MCC) and loss (MLC)
components. First ISO: MISO. Curated by
`scripts/data/curate_lmp_components.py` onto
`data/dictionary/schema/lmp-components.schema.yaml`; consumed by
`scripts/data/derive_miso_loss_surface.py` (the miso-76 marginal
delivery-factor surface — charter
`docs/handoffs/miso-nc-price-separation-design-2026-07.md` §4) and by
congestion-vs-loss decomposition validation.

## MISO source

Public daily all-node market reports, no auth (verified live 2026-07-19):

    https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv
    https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv

Each file carries every node's `LMP` / `MCC` / `MLC` row x hour-ending
1-24, **Eastern Standard Time year-round** (no DST — each file's header
states it). `docs.misoenergy.org` retains only a rolling ~3.5-year window
of these dailies; the MISO Data Exchange Pricing API is the fallback for
aged-off dates (see `scripts/data/fetch_miso_hub_lmp.py`).

## Why this directory carries no bulk files (shared staging)

The verbatim MISO raw holding for this datatype **already exists in the
repo**: `data/raw/lmp-data/MISO/miso_hub_lmp_<year>_<da|rt>.csv.gz`
(2023-2025; 2022+ as `_p<NN>.csv` chunks), staged by
`scripts/data/fetch_miso_hub_lmp.py` under scope decision D6. That staging
filters each daily report to the eight named trading hubs but keeps **all
three Value rows (LMP, MCC, MLC) verbatim** — exactly the component record
this datatype needs (verified 2026-07-19: 8760/8784 rows per (year,
market) = days x 8 hubs x 3 components, no gaps, 2023-2025 both markets).

Duplicating ~5 MB of committed verbatim rows into this directory would
violate the single-source-of-truth principle for no gain, so the MISO
`lmp_components` spec reads the shared staging directly
(`scripts/lib/lmp_components/miso.py`, `raw_subdir="lmp-data/MISO"`,
RAW_DIR-relative). Re-fetching or extending coverage (more hubs, more
node classes, new years) goes through `fetch_miso_hub_lmp.py`, never by
hand-editing the staging.

Hubs held (scope D6): ARKANSAS.HUB, ILLINOIS.HUB, INDIANA.HUB,
LOUISIANA.HUB, MICHIGAN.HUB, MINN.HUB, MS.HUB, TEXAS.HUB.
Hub -> model-zone crosswalk: `scripts/data/derive_miso_hub_lmp.py`
`HUB_TO_ZONE` (MISO-Plains has no hub; consumers use the documented
MINN+ILLINOIS bracketing proxy).

## Quarantine (CLAUDE.md rule 22)

Default curation covers market-date years 2023-2025 (the train window)
ONLY. The staged 2022 chunks belong to the authorized validation-holdout
intake and are NOT curated by default; `--allow-out-of-train` (plus
session-logged owner authorization) is required to curate them, and no
clean partition for an out-of-train year may feed a solve before the
MISO calibration-complete marker exists.

## Integrity property (checked at curation)

Within one (market, interval), `LMP - MCC - MLC` is the system marginal
energy component (MEC), identical across all nodes up to the report's
2-decimal rounding. `curate_lmp_components.py` recomputes the cross-node
MEC spread per interval and warns loudly if it exceeds the rounding
tolerance — a drifting MEC identity means a corrupted staging row, not a
market feature.

DATA NEEDED: nothing for the current MISO window (2023-2025 committed).
Other ISOs publish components inside their existing `lmp-data` holdings
(CAISO MCC/MCL columns, NYISO LBMP components); an ISO lands here by
registering its own `scripts/lib/lmp_components/<iso>.py` module — never
by branching shared code on the ISO name.
