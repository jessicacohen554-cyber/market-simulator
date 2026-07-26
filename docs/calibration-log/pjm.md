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

## 2026-07-25 — pjm-120: C3a-2025 diagnosed as a monotone price-DISPERSION compression; the anchor lead REFUTED and reserve-product coverage MEASURED INERT (no keeper change)

**Task.** Close PJM's last open gate — C3a mean LMP 2025, −10.7% against a ±10%
band, the single NOT-YET criterion on keeper `2026-07-24-pjm-119-overlay-restore`
(9/10 scored PASS). **Outcome: diagnosis + two refutations, no lever promoted,
keeper unchanged.** Full write-up:
`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md`.

**1. The handoff's leading lead is REFUTED on sign.** It proposed that 2025 fails
because gas ($3.52 HH) exceeds the `gas_offer_margin_anchor` ($3.3483), so
`gas_offer_net_revenue_margin` compresses offers in the failing year. The sign of
`mc += markup_hr × (anchor − fuel)` is set by the DELIVERED series, not the annual
HH scalar. PJM 2025 delivered $/MMBtu: Jan 6.79, Feb 4.99, Mar 4.07, Apr 4.03,
May 3.41, **Jun 2.99, Jul 3.26, Aug 2.89, Sep 2.66, Oct 3.12**, Nov 3.94, Dec 5.09.
Every failing month is BELOW the anchor, so the mechanism RAISES those offers; it
compresses only in Jan/Feb/Dec, the best-scoring months. Lowering the anchor (e.g.
to the pooled p50, 2.9449) would make 2025 worse. Independent of the owner's
2026-07-24 decision to keep the mechanism — it simply is not the C3a driver.
(Incidental: the pjm-117/pjm-118 entries above describe the anchor as "a measured
p50"; it is the MEAN of annual delivered means — 3.3483 = mean(3.2551, 2.8556,
3.9341), pooled p50 is 2.9449. Code is self-consistent; only the prose is wrong.
Flagged for `/sync-docs`, not edited — rule 23.)

**2. The residual is a dispersion compression, not a level miss or a tail
truncation.** 2025-only byte-faithful replay of the keeper (`replay_keeper`, east
cut confirmed live at `2 link(s) … mean 8149 MW`; probe
`results/probes/pjm120_c3a_2025`, rule-16 diagnostic, never registerable). Model
$41.19 vs actual $46.07 load-weighted, gap −$4.89. By ACTUAL-price stratum
(contribution to gap): 0-25 **+1.965**, 25-50 **+2.045**, 50-100 −3.736, 100-200
−2.499, 200-376 −1.127, >376 −1.534. Per-hour error: **+10.4 / +3.7 / −17.5 /
−64.8 / −166.5 / −634.5**. The model is too EXPENSIVE when slack and too CHEAP
when tight, monotonically. **This corrected an earlier draft of the same finding**
(pushed as `6b3dc33`) which had argued the gate was lost in ~14 extreme hours; the
>$376 stratum is only 31% of the negative side, less than the 50-100 band. The
refutation is recorded in the doc rather than silently rewritten.
**Guard: no level knob can fix this** — the cheap 77% of hours are already
$4-10/MWh too high, and 2023 already runs +4.7%.

**3. Reserve-product coverage cannot be the lever — measured, not inferred.** The
keeper prices 1 of PJM's 3 nested reserve products (`pjm_primary` + `pjm_primary_mad`;
`pjm_reserve_pergen_sync` off, Secondary/30-Min not in the LP at all), while PJM at
2025-06-24 18:50 was short on ALL THREE with every ORDC curve at its $850 Step-1
penalty (SR $2,550 = 3×850, PR $1,700, 30MIN $850) — that cascade set the $1,722
LMP. But the model's balance never binds: `hourly/system_2025.parquet::reserve_price`
is nonzero in **22 of 8,759 hours**, reaches **$300 in ZERO hours** and $850 in zero,
max **$210.99**, mean $0.151. At the worst hour (h4193, actual $1,722) the dual is
$210.99. Cause: **38.1 GW of deliverable 10-min ramp against a ~3.7 GW requirement**
(~10× slack) vs PJM's actual 1.6 GW cleared against 2.5 GW. A second demand curve
over that slack clears in the same sub-shortage regime.
The A/B arm (`--set pjm_reserve_pergen_sync=true`) built correctly (78 R columns /
4 balance families vs 39/2) and cleared P0 in 561 s but was **OOM-killed in the P1
warm-start** (exit 137) — the documented failure mode for PJM's finer reserve tiers
(`model/reserves/spec.py`), so it returned no C3a number; the reserve dual settles
the question directly and more strongly. This **reproduces the pjm-87 result
("never crosses $300") on the current east-cut-restored model**, so the owner's
2026-07-11 G-20b hold was not an artifact of the degraded-overlay era — it is
re-derived here from a different criterion (C3a, not C3c) and stands strengthened.

**Forward.** The live lane is reserve/LP tightness (G-20b / ERCOT-G-22 class): the
perfect-foresight all-online dispatch carries an order of magnitude more deliverable
ramp than PJM holds, so no demand curve can price scarcity and the upper strata stay
compressed. Caution for scoping: closing only the >$376 stratum would pass C3a-2025
(≈ −7.3%) while leaving −$7.4 of compression and the over-priced cheap hours intact —
per rule 1 that is a partial repair, not a closure.

**Reproducibility note.** `regenerate_clean.py transfer-interface-limits
ramp-capability` suffices (seconds; the full 46-datatype sweep is not needed), and
`fetch_pjm_da_virtuals.py --years 2025` is REQUIRED — the keeper's
`pjm_da_virtual_bids` hard-fails on a fresh container without the gitignored raw feed.

Next number: pjm-121.

## 2026-07-25 — pjm-121: the measured CC_LIKE mid-curve belt closes C3a — first all-pass PJM determination (CALIBRATED, 10/10); level-form arm REFUTED without a solve; dispersion lane unchanged

**Task.** Close C3a-2025 (−10.7%, the sole open gate on keeper
`2026-07-24-pjm-119-overlay-restore`). **Outcome: candidate keeper
`2026-07-25-pjm-121-cc-belt` (bundle `results/calibration/pjm121_ccbelt`) scores
CALIBRATED, 10/10 criteria PASS** — PJM's first all-pass determination.
`keepers.json` is owner-only and untouched; the promotion is flagged, not made.
Full write-up: `docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md`.

**1. The lever — one rule-19 scope flag, zero new free parameters.**
`pjm_offer_midcurve_segments: ("LONG_RUN",) → ("LONG_RUN", "CC_LIKE")`, handing
the CC_REGULAR econ tranches to the already-frozen measured mid-curve surface
(`pjm_offer_midcurve_condbinned.json`) at the same P1-only `mc_bid_adjust` seam,
same floor-only semantics, same VOLL cap as the LONG_RUN scope live since
pjm-104 (264 → 461 priced rows). This is the pjm-108 lever, rejected then on C1
(8.52 TWh CC displacement) — re-tested because the base changed: the pjm-105
symmetric-net virtuals removed the one-sided phantom demand, pjm-119 restored
the east cut/measured limits, pjm-118 added the net-revenue margin. On the
current base C1 is clean: 16/16 gated rows, free 12/12. C3a: 2023 +5.6 / 2024
−2.5 / **2025 −9.3** (model $41.53 vs actual $45.80 rt_lw). All three mid-merit
segments are now measured-owned (CT_FAST pjm-103, LONG_RUN pjm-104, CC_LIKE
here); CC peak rungs stay fitted-owned (rule 19 by replacement).

**2. HONEST SCOPE — a level effect, not the dispersion repair.** Stratified on
the pjm-120 bins, +$0.254 of the +$0.35 2025 gain (73%) comes from the two
CHEAP strata the model already over-priced (0-25 +1.965→+2.015, 25-50
+2.045→+2.249); the four tight strata contribute +$0.087 combined. The pjm-120
dispersion compression is intact. The gate closed on a legitimate measured
mechanism — not a fitted adder — but it must never be reported as the
dispersion fix (rule 1).

**3. Level-form arm REFUTED without spending a solve.** The measured-ladder
LEVEL form (bid SET to the measured level, signed markup — the
`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §A.1 step-3 construction) is
implemented default-off behind `ScenarioConfig.pjm_offer_midcurve_level_segments`
(six regression tests, `tests/test_pjm_offer_midcurve_level_form.py`).
`scripts/probes/pjm121_level_form_precheck.py` ran the real builder on the real
fleet/offer arrays with a pre-registered kill criterion: level CC_LIKE LOWERS
the CC econ bids −$8.76/MWh MW-weighted (87.5% of row-hours cheaper) and
NARROWS the offer spread in every net-load bin (p90−p10: 23.21→19.65,
33.70→24.27, 33.45→24.57, 20.84→18.23), where the floor form widens all four.
A level-lowering lever cannot close a dispersion gap — killed pre-LP. Cause:
the model's CC econ rows sit at within-plant shares where the measured ladder
is flat/cheap; the measured steep belt (s0.95–0.99) lands on the CC PEAK rows
the mechanism excludes by design. Kept in the codebase default-off as the
correct construction for a fleet whose fitted bands sit BELOW measured.

**4. New probe — who sets the price.** `scripts/probes/pjm121_marginal_decomp.py`:
on the 2025 keeper baseline **COAL sets 38–80% of the price in EVERY actual-price
stratum** (the measured LONG_RUN corpus caps coal at ~8.6× gas ≈ $36, yet coal is
marginal in strata clearing $66–252) and **CC_REGULAR is essentially never
marginal (0–1%)** despite 33–50 GW dispatched. In the 50-100 stratum the model
carries 15.6 GW idle CT_PEAKER with only 1.8 GW within $10 of the dual. The open
root cause stays where pjm-120 put it: reserve/LP supply-side tightness (G-20b /
ERCOT-G-22), 38.1 GW deliverable 10-min ramp vs a ~3.7 GW requirement.

**Not re-opened** (closed by measurement): the level-form CC ladder (§3), a
CT_FAST HR-multiplier reprice (pjm-101/102 over-expression; CT_FAST is rule-19
owned by the pjm-103 start-cost amortization and a `mc_base`-anchored floor
would STACK with the startup markup), `gas_offer_margin_anchor` (pjm-120 §1),
reserve-product coverage (pjm-120 §3 — the dual never reaches $300).

**Provenance note.** The pjm-121 container was archived before its artifacts
landed; the scored verdict evidence (metrics.json + registry sidecar + the
pre-check probe) merged as PR #2897, and the remaining artifacts — the
level-form mechanism + tests, this entry, and the byte-faithful bundle re-solve
per the FINDING doc's recipe — were recreated and landed by pjm-122.

Next number: pjm-122.
