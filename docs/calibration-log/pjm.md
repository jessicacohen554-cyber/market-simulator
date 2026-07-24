# Calibration Log — PJM

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for PJM calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — PJM DAM outage/availability data intake (no solve)

Owner-authorized data-intake session (branch `claude/pjm-dam-data-intake-19dqnf`):
fetched PJM Data Miner 2 `gen_outages_by_type` ("Generation Outage for Seven
Days by Type"), 2018-01-01 → 2026-07-19 (65,511 rows), the PJM analogue of
ERCOT's 60-Day DAM disclosure thermal availability and the aggregate-coverage
replacement for the CAMPD unit-outage fallback. Processed by the derive step to
per-year CSVs `data/raw/pjm-outages/by-year/gen_outages_by_type_<YEAR>.csv` + an
efficient `data/raw/pjm-dam-availability.parquet`. **Neither data file is
committed** — the API-only push path can't carry the binary parquet or the
~4.3 MB of CSV rows, and `git push` is disallowed; both regenerate from the
committed fetch+derive scripts in one command, and the loader degrades to the
statistical fallback until they exist. Schema `pjm-outages`. Committed the loader
`market_sim.data.pjm_outages.pjm_dam_availability_series` (a **default-off,
backcast-only** seam); the `ScenarioConfig.pjm_dam_availability` flag + the
`data.fleet` water-fill application (shared with the ERCOT overlay) are the
ready-to-apply patch in `docs/handoffs/pjm-dam-availability-wiring-2026-07.md`,
deferred because they touch two 8k–10k-line core files the API-only push path
can't re-emit safely (rule 27). PJM publishes no per-fuel-class outage split, so
the transform is a fleet-wide uniform derate (forced + maintenance) against the
model's PJM fossil-thermal nameplate; sub-regional totals retained for a future
zone/class refinement. **No LP solved/scored, no keeper, no marker** (the
2018–2022 + H1-2026 out-of-training years enter as data only; validation is no-LP
loader-resolvability / row-count / invariant checks per rule 22).

Committed this session: the raw fetch + derive scripts, the loader module
`data/pjm_outages.py`, the `pjm-outages` schema, the tests, and the wiring
handoff (the data files themselves are the pending item above). Two small
text-only follow-ups were deferred because the API-only push path can't safely
re-emit the 600–1,600-line files they touch: (a) mirror this entry into the
canonical intake ledger `docs/out-of-sample-results-2026-07.md` §1 (as §1.5);
(b) register `pjm-outages` in `scripts/render_data_dictionary.py`'s
`DATATYPE_ORDER` + `NARRATIVE` and re-render `data-dictionary.md` (the schema
currently sits unregistered alongside the pre-existing `dam-public-bids` /
`lmp-components`, which are in the same state). Flagged for the PJM calibration
owner: applying the wiring
(`docs/handoffs/pjm-dam-availability-wiring-2026-07.md`), turning the overlay on,
and choosing its final allocation/denominator is a keeper session subject to the
holdout tiers.

## 2026-07-24 — pjm-117: gas-offer net-revenue-margin A/B — PROMOTED as offer-curve STRUCTURE (owner decision; NOT-YET, level-retune to follow)

Charter rollout of the `gas_offer_net_revenue_margin` mechanism (NEISO keeper
`neiso-61`) to PJM. **Identification pre-landed** (branch
`claude/gas-offer-net-revenue-isos-1px5vg`, merged): PJM `phys_*` keys on the
identifiable gas classes + anchor **3.3483 $/MMBtu**
(`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, mean of the keeper delivered-gas overlay
2023-2025 = 2.54/2.19/3.52 → the training-window p50 basis). Default-OFF and
byte-inert flag-off (986 gas tranches marked up flag-on, heat rates identical /
markups zero flag-off; median fixed margin 9.51 $/MWh, max 255.97 peaker).

A/B: same-HEAD `replay_keeper` of the `pjm_gasshape_interpfix_main` (pjm-115)
recipe — BASE arm (flag off) vs MARGIN arm (single delta `gas_offer_margin=true`),
full 2023–2025, RT-scored. **Solved via the rule-12 per-year chain** (`--years`
+ `--reuse-solved`, one fresh year per process) because a single 3-year process
OOMs the 15 GB box at year 2 (~16 GB peak). Bundles `pjm_netrev_base`
(pjm-116) / `pjm_netrev_margin` (pjm-117). PJM DA-virtuals (`pjm_da_virtual_bids`,
in the keeper recipe) were re-fetched from DataMiner2 (gitignored raw) to replay.

**Structural result (verified in code + live solve):** at `fuel==anchor` the
offer reduces EXACTLY to the registered multiplier surface; the markup becomes a
fixed `markup_hr × anchor` $/MWh margin, gas-invariant (elasticity 1→0). Zero
fitted scalars (rule 24/25): the markup LEVELS are the registered surface, the
anchor is a measured delivered-gas p50.

| year | gas vs anchor 3.3483 | C3a base→margin | C3b dur-NRMSE base→margin |
|---|---|---|---|
| 2023 | 2.54 (< → firm up) | +4.6 → +5.5 % | 0.414 → **0.427** (worse) |
| 2024 | 2.19 (< → firm up) | −4.6 → −3.1 % | 0.414 → **0.435** (worse) |
| 2025 | 3.52 (> → compress) | −9.4 → **−10.6 %** (FAIL) | 0.761 → **0.772** (worse) |

Full determination scoring (not just the A/B shape probe): BASE (flag off)
**reproduces the pjm-115 keeper CALIBRATED-grade** — C1/C2/C3a/C3b/C4/C5a/C7/C8
all PASS (only C3c tail FAILs, and it fails in BOTH arms — a pre-existing
scorer/commit drift from the keeper's `688e168`, supporting tier, not the flag).
**MARGIN scores NOT-YET**: the fixed margin firms CC offers ~$1/MWh too high at
below-anchor gas and prices combined-cycle gas out of merit → **C1 fuel-mix
CC_REGULAR 2023 320.3→316.8 TWh vs 325.7 (−8.9 TWh, out of band, PASS→FAIL)**;
**C3a mean LMP 2025 −9.4→−10.6 % (PASS→FAIL)**; C3b degrades all three years
(within tolerance, PASS).

**Verdict: this is the pre-registered REFUTATION signature** (C3b degrades every
year + now two load-bearing FAILs; the same direction that rejected the CAISO
twin, caiso-112). **Owner decision 2026-07-24 (made with full sight of the
above): the net-revenue-margin form is the CORRECT offer-curve STRUCTURE and is
PROMOTED as the PJM keeper (pjm-117), per rule 1 "right market structure first,
offer-curve tuning second."** The structure is adopted despite the current fit
degradation; the C1/C3a misses are **open MODEL MISSES** (not accepted
limitations, so NOT logged as attestation exceptions — determination stays
NOT-YET) to be closed by **re-tuning the offer-curve multiplier LEVELS around the
fixed-margin structure** — the `offer_curve_by_group` DOF surface, the
rule-1-sanctioned tuning lever. Level retune is the active next phase; no lever
was tuned to any residual in THIS promotion (rules 1/11/13 — the anchor is a
measured p50, the repricing is structural). 2022 holdout NOT touched (PJM has no
calibration-complete marker). Both arms registered on the dashboard.

Next number: pjm-118.
