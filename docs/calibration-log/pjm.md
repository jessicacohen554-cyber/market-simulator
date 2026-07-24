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

## 2026-07-24 — pjm-118: offer-level retune around the net-revenue-margin structure — C1 CLOSED, C3a 2025 found STRUCTURAL (NOT-YET)

Level-tuning phase promised by the pjm-117 keeper note ("open model misses to
close by re-tuning the offer-curve multiplier LEVELS around the fixed-margin
structure — the active next phase"). Continues session
`claude/pjm-gas-offer-netrev-ab-i9k1cz`. Structure decision UNCHANGED (owner,
rule 1): `gas_offer_net_revenue_margin=True`, anchor 3.3483 $/MMBtu, NOT reverted.

**What moved (rule 24, on-registry `offer_curve_by_group`; zero NEW free params).**
Three band LEVELS re-tuned around the fixed-margin structure:
- `CC_REGULAR` econ_low **1.0 → 0.96** — the fixed margin firmed CC's efficient
  low-load offer ~$1/MWh too high at below-anchor gas, pricing CC out of merit.
- `CT_PEAKER` econ_low **1.05 → 1.25**, econ_high **1.27 → 1.65** — firms the CT
  part-load offer to curb the high-gas 2025 CT over-run.

No price adder, no pinning, no off-registry channel; the anchor is the unchanged
measured delivered-gas p50.

**Result — C1 fuel-mix CLOSED, honestly scored (rebuilt `system.parquet` so C3a
scores all years):**

| year | CC_REGULAR (was) | CT_PEAKER (was) | C3a mean LMP |
|---|---|---|---|
| 2023 | 319.1 PASS (316.8 **FAIL**) | 22.9 PASS | +5.0% PASS |
| 2024 | 333.3 PASS | 23.2 PASS | −3.3% PASS |
| 2025 | 333.3 PASS | 30.6 PASS (32.0 **FAIL**) | **−10.5% FAIL** |

C1 8/8 PASS (both the CC-2023 and the CT-2025 over-run closed); C2/C3b/C4/C5a/C7/C8
PASS. **Determination NOT-YET** — load-bearing C3a 2025 (−10.5%) and supporting
C3c scarcity-tail (2024/2025) remain.

**KEY FINDING — the 2025 price miss is STRUCTURAL, not offer-level (rule 1).**
A four-run offer-level sweep (baseline + candidates A/B/C/D) proves the offer
surface cannot close C3a 2025:
- The undershoot is entirely SUMMER scarcity — monthly model-vs-actual LMP: Jan
  −1.0 / Feb −2.1 (fine) but **Jun −19.9 / Jul −9.8 / Sep −8.1 / Oct −6.5 $/MWh**.
- The model's 2025 price tail caps at **$324 (48 h > $100)** vs real summer
  scarcity (**59 h > $200**).
- Levers tested: raising CC `econ_high` lifts 2025 price but BREAKS C1 CC-2023
  (firms CC in low-gas hours, −7.5 TWh); lowering CC `econ_low` fixes C1 but
  FLOODS 2025 CC and lowers price (−11.0%); raising CC-`peak` + CT offers is
  **INERT** on 2025 (+0.02 $/MWh; tail p99 82.6→84.6 unchanged) because the
  marginal unit in the undershooting hours is not a peaker.
- Root cause: too much cheap supply (margin-compressed high-gas gas offers +
  imports, 34% import-hours vs 1.7% actual) meets summer peaks, so scarcity never
  forms → a **structural supply-adequacy / scarcity-formation** issue. Found, not
  faked with an adder.

**Consequence.** Offer-level tuning for PJM is AT FRONTIER: C1 is closeable, C3a
2025 is not. Finishing PJM to CALIBRATED needs a **structural** session on the
summer-scarcity / import-seam supply-adequacy lane (why cheap supply clears the
June/July 2025 peaks instead of forming scarcity), NOT more offer tuning. Opened
as the standing PJM open root cause.

Promoted as the PJM keeper (supersedes pjm-117): same structure + closed C1,
strictly more dispatch-faithful; C3a 2025 / C3c reclassified from "close by level
tuning" to "structural, needs a structural session." 2022 holdout NOT touched
(PJM has no calibration-complete marker). Both control (pjm-118 replaces the
inherited pjm-115 levels; the margin baseline reproduced pjm-117 exactly:
CC_REGULAR 2023 316.8, C3a 2025 −10.6%).

Next number: pjm-119.
