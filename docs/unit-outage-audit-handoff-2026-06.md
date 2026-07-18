# Handoff — comprehensive unit-outage audit (CC steam-turbine coupling)

**Date opened:** 2026-06-19. **Trigger:** a spot-check of Wolf Hollow II's 2025
outage surfaced a systemic under-derate in the CAMPD-derived unit-outage overlay:
**combined-cycle steam turbines are never derated when their combustion turbines
go down.** This is the audit the finding warrants.

## The finding (concrete, measured)

Plant **59812 (Wolf Hollow II)**, a 2-CT + 1-ST combined cycle. EIA-860
generators (`data/raw/eia-860/eia860_generators.parquet`):

| generator | nameplate MW | prime_mover | meaning |
|---|---|---|---|
| CGT4 | 360.0 | CT | combustion turbine |
| CGT5 | 360.0 | CT | combustion turbine |
| **STG6** | **511.2** | **CA** | **combined-cycle steam turbine** |

Sum = 1231.2 MW = the model bin `(59812, CC_REGULAR)` capacity exactly.

CAMPD (`data/raw/campd-unit-level/TX_2025.parquet`) confirms **CGT5 was genuinely
idle 2025-10-03 → 12-31 (90 days)** — and that outage *is* correctly present in
`data/raw/campd-unit-outages.csv` (`2025-10-02 → 12-31`). So no outage is
"missing." The bug is the **derate magnitude**:

- `unit_outage_derate_factors` (`src/market_sim/data/outages.py`) derates the
  plant bin by `unit_capacity_mw / bin_capacity`. For CGT5 that is
  **360 / 1231.2 = 29%**.
- Physically, CGT5 is a 360 MW CT **plus its share of the 511 MW steam turbine**
  (the HRSG steam from CGT5's exhaust). Losing one of two CTs kills ~half the
  steam (~256 MW), so the real loss ≈ **360 + 256 ≈ 616 MW ≈ 50%** of the block.
- The model keeps the plant **~71% available** for 90 days when reality is **~50%**
  — an under-derate of ~256 MW × 90 days. Confirmed dispatch-side: during the
  CGT5 outage the model runs WHII up to **~59% of total capacity**, while the
  actual plant maxes at **~40%** in that period — the model has phantom steam
  capacity online that physically went down with the CT.

### Root cause — basis mismatch the derivation can't see

`scripts/data/derive_campd_unit_outages.py::unit_capacity_mw` **prefers the EIA-860
generator nameplate** (`eia_exact`) for the numerator, "so the derate denominator
is on the same nameplate basis as the model bin." But:

1. The **steam turbine (prime_mover `CA`) burns no fuel**, so it has no CAMPD CEMS
   series and can **never** be detected as an outage on its own. It only goes
   down (partially) *because* a feeding CT went down — the coupling the detector
   has no signal for.
2. The numerator (CT nameplate, 360, steam-excluded) and the denominator (bin
   capacity, 1231, steam-**included**) are therefore **not on the same basis**.
   The CT's true share of the bin is `CT + allocated steam`, not the CT nameplate
   alone. CAMPD even reports each CC unit at ~588 MW peak (CT + folded steam),
   already above the 360 MW EIA-860 CT nameplate — a tell that the steam belongs
   with the CT.

The same applies wherever a CC block's steam turbine is a distinct EIA-860 `CA`
generator and the CTs are detected independently.

## Scale (why it's worth an audit, not a one-off patch)

Across the **46 CC plants** in `campd-unit-outages.csv`, **43 carry an EIA-860
steam-turbine (`CA`) generator** that is currently underatable — **12,743 MW** of
CC steam capacity orphaned from every outage derate. Any detected CT outage at
these plants under-derates by the orphaned steam share (42% of the block at Wolf
Hollow II). Quick reproduction:

```
uv run python - <<'PY'
import pandas as pd, sys; sys.path.insert(0,'src')
g=pd.read_parquet("data/raw/eia-860/eia860_generators.parquet")
o=pd.read_csv("data/raw/campd-unit-outages.csv")
cc=o[o['plant_group'].isin(['CC_REGULAR','CC_CHP'])]['facility_id'].unique()
gT=g[g['plant_id'].isin(cc)]
steam=gT[gT['prime_mover']=='CA'].groupby('plant_id')['nameplate_capacity_mw'].sum()
print(f"CC plants {len(cc)}, with CA steam {steam.gt(0).sum()}, orphaned steam {steam.sum():,.0f} MW")
PY
```

## The task

**Fix the CC steam-turbine outage coupling across ALL ISOs and regenerate the
outage data / derates.** A genuine driver, not a fit to actuals (repo rule). The
principle (stated by the requester): **when a CC combustion turbine goes down it
also cuts the plant's steam turbine by that CT's share of steam capacity** — the
downed CT's steam must be derated, not left online. So the derate for a CC CT
outage must include the CT's allocated steam.

Candidate fix (A/B it): in `derive_campd_unit_outages.py`, for CC units make
`unit_capacity_mw` the unit's **full block share**, e.g.
`CT_nameplate + (CT_nameplate / Σ CT_nameplate at plant) × Σ CA_nameplate at
plant`, so the summed CT shares reconstitute the bin capacity and one CT out
derates its CT + its steam fraction. Equivalently, allocate each `CA` generator
across the block's CTs. Then **regenerate** `campd-unit-outages.csv` (don't
hand-edit — it is a derived artifact) and re-run the calibration.

### Checks the audit must cover

1. **Every CC plant**, all ISOs (`campd-unit-outages.csv` and the
   `campd-unit-outages-<ISO>.csv` siblings). Confirm the numerator/denominator
   basis is consistent at each.
2. **Single-shaft CC** (`prime_mover = CS`): CT and steam share one shaft/
   generator id — no orphaned steam, must NOT be double-counted. Distinguish
   `CS` from `CT + CA`.
3. **Split / mixed facilities** already special-cased in
   `outages.py::_unit_outage_target` — W A Parish (3470, coal vs ST_GAS 34702)
   and Barney M Davis (4939, ST_GAS 49392 vs CC). Verify the steam allocation
   doesn't cross these splits.
4. **CT_PEAKER and `ST_GAS_PEAKER_PLANTS`** are intentionally excluded (economic
   dispatch) — keep them excluded; the steam fix is for sustained-run CC/ST only.
5. **The informational `plant_capacity_mw` column** in the CSV (720 for 59812) is
   the CT-only sum and disagrees with the model bin (1231) — the derate uses the
   bin, so 720 is cosmetic, but fix it for consistency or document it.
6. **Concurrent-CT clipping:** `unit_outage_derate_factors` sums concurrent unit
   derates and clips at full (1.0). With steam-inclusive shares, two CTs out must
   sum to ~100%, not overshoot — verify the clip still behaves.

## Key files

- `scripts/data/derive_campd_unit_outages.py` — the derivation (`unit_capacity_mw`,
  `build_capacity_index`, the per-unit detector). **Regenerate the CSV here.**
- `src/market_sim/data/outages.py` — `unit_outage_derate_factors` (applies the
  derate), `_unit_outage_target` / `_generic_unit_outage_target` (routing),
  `ST_GAS_PEAKER_PLANTS`, the GROUPS filter.
- `data/raw/campd-unit-outages.csv` (+ `-<ISO>.csv` siblings) — the derived output.
- `data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` — CAMPD source (per-unit).
- `data/raw/eia-860/eia860_generators.parquet` — nameplate + `prime_mover`
  (CT/CA/CS) — the steam-vs-CT signal.

## Gate (this is a GATED change — it alters derate → dispatch → volumes)

Re-run the ERCOT 3-year co-opt keeper recipe (see
`docs/ercot-run131-lmp-decomposition-2026-06.md` for the command) and hold the
standing gates: monthly LMP MAE/avg per year (2023 ~10.5/46.7, 2024 ~10.5/29.0,
2025 ~2.7/33.9), the >$200/>$500 tails (181/104, 53/16, 31/3), and per-class TWh
(≥12/18). A deeper CC derate should, if anything, *help* the tight-day tails
(less phantom CC availability on outage windows) — confirm it doesn't crater
ST_GAS/CC volumes. Register the run on the dashboard (`/calibration-report`).
Other ISOs (PJM/NYISO/NEISO/CAISO/MISO) have their own outage CSVs and keepers —
re-gate each ISO whose CC plants the fix touches.

## What is NOT broken (don't chase these)

- The Wolf Hollow II CGT5 90-day outage is present and correct — the issue is
  only its magnitude (the orphaned steam), not a missing window.
- The CT-only `eia_exact` matching itself is fine for pure CT/coal/ST units; it's
  specifically the CC CT→steam coupling that needs the allocation.

## Resolution (2026-06-19)

Implemented the candidate fix in `build_capacity_index` /
`unit_capacity_mw`: a combined-cycle CT's `unit_capacity_mw` is now its full
block share `CT_nameplate × (1 + Σ CA / Σ CT)` over the plant's `CT`/`CA` prime
movers, so the CT shares reconstitute the bin and one CT out derates its
turbine + its steam fraction. A `(detect_mw, derate_mw, cc_augmented)` capacity
entry keeps the *detector's* CF denominator on the CT's own nameplate, so the
steam allocation changes derate magnitude only — **detection is unchanged**
(verified window-neutral: 0 windows lost across all six ISOs; the only added
windows are `observed_peak` rows from newly-landed CAMPD extracts, independent
of this fix). Wolf Hollow II's CTs go 360 → 615.6 MW (sum 1231.2 = the bin); the
CGT5 90-day outage now derates 50%, and the cosmetic `plant_capacity_mw` column
equals the bin. CS single-shaft blocks, the W A Parish / Barney M Davis splits,
the peaker exclusions, and the concurrent-CT clip all behave (see CHANGELOG
2026-06-19). All six unit-outage CSVs regenerated; ERCOT 3-yr keeper re-gated.
