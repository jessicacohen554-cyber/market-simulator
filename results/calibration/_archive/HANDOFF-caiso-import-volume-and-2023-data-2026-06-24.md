# HANDOFF — CAISO import volume (Fix B) + 2023 intertie-LMP data gap (2026-06-24)

Branch: `claude/caiso-load-demand-issue-ujznb8`. Picks up from the "CAISO load/
demand off?" investigation. **The load numbers are fine and geothermal is not
missing** — see "What this was NOT" below. This handoff covers the two open
items: (B) the real over-import / gas-underburn, and (C) the missing 2023
intertie-LMP data + an approximation plan.

## What was already done this session (shipped)

- **Fix A — `[1]` fuel-mix report apples-to-oranges (commit `0e37964`, pushed).**
  The generic calibration report (`_report_generic` / `_canon_fuel` in
  `scripts/run_calibration_full.py`) printed a TOTAL that didn't equal the sum of
  its rows: the must-run `OTHER` class (geothermal ~8 TWh) was upper-cased and so
  skipped by the print loop while still counted in TOTAL. Fixed `_canon_fuel` to
  lower-case non-gas labels (`OTHER`→`other`) so it prints, and added a note that
  EIA-930 "gas" folds in geothermal+biomass (compare model gas to EIA-923, not
  EIA-930). No dispatch change.

## What this was NOT (do not re-chase)

- **Not the load/demand input.** 2023 total in-region generation 181.6 vs
  EIA-930 184.3 TWh (−2.7). Demand from EIA-930 CISO is correct.
- **Not missing geothermal.** Geothermal IS modeled — injected via the `OTHER`
  must-run class (`_INJECTED_MUSTRUN_CLASSES = ("biomass", "OTHER")`,
  `_must_run_profiles`), netted from demand and re-added as pseudo-units,
  reproducing 8.05/7.81/7.83 TWh (2023/24/25) from EIA-923. **Do NOT model
  geothermal as LP fleet units** (`_map_fuel_type` returning `None` for `GEO` is
  intentional) — that double-counts it and breaks the interchange match. (An
  early attempt to do exactly this was made and reverted; today's
  `AUDIT-caiso-cod-ramp-all-classes-2026-06-24.md` is misleading on this point —
  it describes the fleet-LP path only and misses the `OTHER` injection.)

## The real issue (Fix B): over-import / gas under-burn

The "~11 TWh short / big system-volume error even though imports look right" is
an **import-vs-gas substitution**, not a volume hole. 2023 keeper-config
(static/pooled import node):

| 2023 | model | actual / EIA-923 |
|---|---|---|
| net imports | 38.3 TWh | 28.9 |
| import hours | 97.6% | 85.9% |
| gas burn | 68.2 TWh | 76.0 (EIA-923) |

Cheap priced-node imports undercut in-state gas and steal ~8–10 TWh of its share.
When imports are held to actual, that surfaces as the in-region shortfall.

### Quantified lever test (2024, where measured data exists)

Adding the two grounded levers `--caiso-per-hub-intertie` + `--interchange-shaping`
(measured EIA-930 availability envelope) to the keeper config:

| metric (2024) | static/pooled | per-hub + shaping | actual |
|---|---|---|---|
| net imports (TWh) | ~36 (over) | **24.7 (under)** | 32.4 |
| import hours | 97.6% | **90.9%** | 89.0% |
| diurnal corr | −0.35 | **+0.30** | (positive) |
| gas vs EIA-923 | under | **+11.8 over** | — |

**Conclusion:** the grounded levers fix the *hours* and *diurnal shape* (the
user's real symptom) but **over-correct the volume** — it flips from over-import
to under-import, and gas over-burns. The truth sits between the two regimes.

### Recommended Fix B (next session)

Implement the **per-hub-signed-legs** topology described in
`DIAGNOSIS-caiso-perhub-overimport-diurnal-2026-06-23.md`: split the pooled
`WECC_import` bubble into the two real corridors (`WECC_import→NP15` = COI/Path-66
~Malin; `WECC_import→SP15` = Path-46/WOR ~Palo Verde), each a SINGLE signed flow
so import/export net per corridor instead of running as independent legs on one
bubble. The topology already separates the links (`config/iso_configs.py` CAISO);
the keeper just pools them. This is the designed fix that gets netting right
without the volume over/under-shoot. **Validate across 2024 + 2025** (2023 is
data-blocked — see below), then register a proper 3-year keeper. Do NOT curve-fit
a config to land the volume on actual (rule #10).

A **diagnostic-only** 3-year bundle of the per-hub + shaping config is on the
dashboard (`caiso_perhub_shaping_diag_3yr`), labelled a probe — it under-imports
and is NOT a keeper (kept only so the regime is viewable per request).

## The 2023 intertie-LMP data gap (Fix C)

**Confirmed still missing, and it is an OASIS-retention problem, not a fetch gap**
(your hypothesis was right — retried yesterday, did not land). Do NOT clear the
"2023 falls back to the static ladder" note.

Precise state of `data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet`:

| year | MALIN | PALOVRDE |
|---|---|---|
| 2023 | **7056/8760** hrs | **7056/8760** hrs |
| 2024 | 8759/8760 | 8759/8760 |
| 2025 | 8759/8760 | 8759/8760 |

So 2023 is **80.5% present** — only ~1704 hours (Jan–early-Mar) aged out of OASIS
retention. The loader (`measured_import_hub_prices`, `eia_loader.py:675`) rejects
the *whole* year because of its all-finite check
(`not np.all(np.isfinite(price[:hours]))`), so 2023 silently falls back to the
static ladder. **The real task is a ~1704-hour gap-fill, not a whole-year
synthesis.**

### Building blocks already in repo (all cover 2023)

- `wecc_intertie_lmp_hourly_CAISO.parquet` — 7056 measured 2023 hours (MALIN,
  PALOVRDE delivered nodal LMP), full 2024/2025.
- `data/raw/eia-930-interchange/CISO interchange hourly.parquet` — full 2023+
  BA-to-BA net interchange, DIBAs: BPAT/PACW (→ Malin/PNW corridor),
  AZPS/SRP/WALC/NEVP/IID (→ Palo Verde/desert-SW corridor), LDWP/BANC/TIDC/CEN.
  Already consumed by `measured_corridor_flow_envelope` via
  `CAISO_CORRIDOR_DIBA` (`constants.py:2730`).
- F923 / hub gas prices, CAISO load shape — all present for 2023.

---

## PROMPT FOR NEXT SESSION (copy-paste)

```
CAISO 2023 intertie-LMP gap-fill + Fix B (per-hub signed legs). Branch off latest
origin/main.

CONTEXT
- The CAISO backcast lacks measured WECC intertie hub LMPs for ~1704 hours of
  early-2023 (Jan–early-Mar), aged out of CAISO OASIS retention (NOT a fetch bug;
  retried, won't land). The file
  data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet has 7056/8760
  hours for 2023 (MALIN + PALOVRDE), full 2024/2025. measured_import_hub_prices()
  (src/market_sim/data/eia_loader.py:675) drops the whole year on its all-finite
  check, so 2023 falls back to the static import ladder and over-imports.
- Do NOT re-investigate load/demand or geothermal: load is correct; geothermal is
  already injected via the OTHER must-run class (do not add it as LP fleet units).

TASK 1 — try to recover the real 2023 data first (web crawl).
Search for an alternative host of CAISO 2023 Jan–Feb intertie/scheduling-point
hourly LMP at MALIN (COI/Path-66) and PALOVRDE (Path-46): CAISO OASIS archives /
mirrors, gridstatus.io, GridStatus/EIA, Yes Energy/ABB/Velocity samples, ENTSO-
equivalents, academic WECC datasets (e.g. Breakthrough Energy / GridEmissions),
FERC EQR, S&P Global, university Dataverse mirrors. Acceptance: hourly $/MWh nodal
LMP (energy+congestion+loss) at those two scheduling points (or close proxies:
Mid-C/Malin and Palo Verde hubs) for 2023-01-01..2023-03-15. If found, ingest into
the existing parquet schema (year, hour [0-based, fixed non-leap calendar], hub,
price) and DONE — the loader picks it up automatically.

TASK 2 — if no real data, derive a grounded approximation for the missing hours.
This is admissible only as a reproducible physical/statistical reconstruction
(methodology rule #10), labelled as such — NOT a fit to the price/volume residual.
Method:
  a) On the COVERED 2023 hours + all of 2024, fit per-hub (MALIN, PALOVRDE) a
     model of delivered hub LMP from regressors that DO exist for the missing
     2023 hours:
       - EIA-930 corridor net interchange (CISO interchange hourly.parquet,
         summed per corridor via CAISO_CORRIDOR_DIBA: PNW=BPAT+PACW,
         DSW=AZPS+SRP+WALC+NEVP+IID),
       - CAISO load (zone-specific demand), month, hour-of-day, weekday/weekend,
       - monthly gas hub price (iso_hub_monthly_gas_prices) — gas sets the
         Palo Verde marginal level,
       - (optional) CAISO solar/wind potential for the desert-SW midday crash.
     A monotone/g-additive or gradient-boosted regression is fine; report
     cross-validated error on held-out 2024 hours and on the covered 2023 hours.
  b) Predict the ~1704 missing 2023 hours from their own 2023 regressors and
     splice into the parquet (mark provenance: add a `source` column =
     'measured' | 'reconstructed_2023janfeb').
  c) Relax measured_import_hub_prices() to accept a year that is >= ~95% finite
     after the splice (or keep the all-finite check now that the gap is filled).
  d) Sanity gates: reconstructed Apr/May not needed (covered); check the
     reconstructed Jan–Feb level is plausible vs 2024 Jan–Feb and vs the EIA-930
     net-import sign that month (CAISO deep-imports in winter overnight).

TASK 3 — Fix B (per-hub signed legs), independent of TASK 1/2.
Implement the per-hub-signed-legs topology from
results/calibration/DIAGNOSIS-caiso-perhub-overimport-diurnal-2026-06-23.md:
split the pooled WECC_import node into the two corridors as SINGLE signed flows so
each nets import/export per corridor. Validate on 2024 + 2025 (data present);
2023 only after TASK 1/2 lands its data. Target: import hours/diurnal stay matched
(already ~90%/+0.30 with per-hub+shaping) AND net-import volume returns to ~32 TWh
(2024) without over-burning gas. Then register a proper 3-year keeper bundle on
the dashboard (calibration-report skill; all years per rules #14/#15), pruning the
caiso_perhub_shaping_diag_3yr probe.

VALIDATION/KEEPER RULES: solve all available years in one bundle; register via the
calibration-report skill; push bundle files via mcp__github__push_files (avoid the
413 git push loop, see CLAUDE.md). No curve-fitting to residuals.
```

## Files touched this session
- `scripts/run_calibration_full.py` — `_canon_fuel` lower-case fix + `[1]`
  gas-bundling note (Fix A, committed `0e37964`, pushed).
- (revert) An exploratory geothermal-as-LP-units change to
  `config/constants.py` + `data/fleet.py` was made and fully reverted — see
  "What this was NOT".
