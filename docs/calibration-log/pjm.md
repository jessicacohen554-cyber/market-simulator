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

## 2026-07-26 — pjm-122: pjm-121 artifacts landed (bundle re-solved to the cent); dispersion lane reframed as measured marginal-ownership misallocation

**Task 1 — landing (PR #2900).** The pjm-121 verdict evidence had merged as PR
#2897; everything else was recreated: the level-form mechanism
(`pjm_offer_midcurve_level_segments` default-off + the `offer_surfaces.py`
level branch, registered in `_CACHE_KEY_OPTIONAL_FIELDS` so the pinned default
cache key is unchanged), its six regression tests, the pjm-121 log entry, and
the full bundle re-solve per the FINDING recipe (rule-12 chain, ~15 min/yr,
peak 14.8 GB; mechanism engagement 410/444/461 rows — the FINDING's "264→461"
is the 2025 pair). **Fidelity: the 2025 stratum readout reproduces the scored
run to the cent** (model_lw 41.53 / actual 46.07 / gap −4.54, all six stratum
contributions identical) and `calibration_verdict.py` re-scores CALIBRATED
10/10 with metrics.json byte-equal to the committed copy. Registered
(`dashboard_add_run`, id preserved as `2026-07-25-pjm-121-cc-belt` via the
meta-timestamp pin; pjm-107 pruned per top-15 retention). Slim bundle JSONs +
log pushed via API and fetch-verified byte-identical; the payload / bench gz /
hourly parquets / `scenarios.py` + tests sit in a ready local commit **awaiting
an owner-authorized `git push`** (~7.6 MB; the API content path cannot carry
them — no append, binary, and rule-27 emission limits). Transport note for
future sessions: the current `push_files` is **byte-literal** (verified by
experiment — literal UTF-8 and real newlines land exactly; no JSON-decode of
content), so text files of any composition push safely with fetch-back
verification.

**Task 2 — the lane.** Full write-up:
`docs/FINDING-pjm122-marginal-ownership-2026-07.md`. The decomp reproduces on
the CALIBRATED bundle (COAL sets 79/76/55/49/44% of the price by stratum;
CC_REGULAR 0–1%). NEW measurement: in the four tight strata the model dual
exceeds the **measured coal ceiling** (LONG_RUN ladder top 8.62× that hour's
delivered gas) in **93–100% of hours while coal is the price setter in 44–55%
of them** — the price-setting rungs are fitted `econ_high`/sigmoid tops the
36-month offer corpus says coal does not submit, and the raise-only floor can
never touch them. The corpus assigns $40–150 to the CC top belt (s0.95–0.99 =
11.1–18.8× gas ≈ $49–83 — exactly the model's CC econ→peak hole, 9.6×→31.9×)
and CT_FAST (33–40× ≈ $96–174 vs the model's $47–80 idle shelf). Candidate for
pjm-123 (NOT armed): the three-leg measured re-ownership — coal econ LEVEL
form, CC PEAK rows measured belt, CT_FAST max()-seam reprice — with
pre-registered no-LP kill criteria (cheap bins must fall AND bin3 must rise;
CC spread must not narrow; CT leg must be max(), never a sum). Scope split:
offers can plausibly reach the 50-100/100-200 strata (−$3.66/−$2.49 of the
−$4.54 gap); the >$200 scarcity tail stays with G-20b reserve/LP tightness.

## 2026-07-26 — pjm-123: the dispersion composite is REFUTED at the no-LP pre-check, and the reason retires the measured offer surface as a dispersion lever

**No solve was spent. The CALIBRATED keeper `2026-07-25-pjm-121-cc-belt` is
untouched** — no config change, no re-solve, no dashboard change (nothing to
register: rule 14 covers completed solves, and none was run). Full write-up:
`docs/FINDING-pjm123-composite-precheck-2026-07.md`.

**The pre-check.** `scripts/probes/pjm123_composite_precheck.py` builds all
three pjm-122 §4 legs on the real fleet and offer arrays (fleet reconstruction
only, ~4 min/yr) and diffs each arm against the keeper, with the kill criteria
written into its docstring before the first run. Leg 1 needed no code; legs 2
and 3 are new default-off mechanisms:
`ScenarioConfig.pjm_offer_midcurve_peak_segments` (measured top belt on the
`peak*` rungs, LEVEL form, rejected at config construction alongside the
top-of-curve surface — rule 19) and `pjm_ct_measured_max_reprice` + the new
`p1_bid_max_target` seam / `pipeline.solve.apply_bid_max_target`. Ten
regression tests; zero free parameters; surface JSON untouched; 2023–2025 only.

**Verdict — refuted in all three years at both endpoints of the startup-markup
bracket.** The decisive statistic is the K1 **gradient** (composite bid delta
in the tightest bin minus the slackest — weighting-robust, unlike the two sign
tests): **2023 −1.32/−0.89 · 2024 −1.79/−1.52 · 2025 −4.79/−4.63** (lo/hi),
where it must be positive. The composite raises SLACK-hour bids more than
TIGHT-hour bids everywhere. Legs 1 and 2 are near-flat level reductions
(coal/ST_GAS/CC-peak down $4–85 with almost no bin gradient); leg 3 dominates
and carries the wrong shape (+$23 in bin2, only +$12 in bin3).

**Root cause, and why it generalizes.** Reading the frozen surface directly:
in the TIGHTEST net-load bin the corpus prices **CT_FAST** at 22.5–25.2 × gas
against 32.7–34.5 × in bin2, **CC_LIKE** at 4.83–4.92 against 5.17–5.53, and
**LONG_RUN**'s top at 8.07–8.47 against bin0's 8.57–8.97. Every segment is
cheapest (or near-cheapest) in bin3 — and it is not a gas artifact, since
bin3's delivered gas is itself the lowest of the four. **Any mechanism that
hands a class its measured conditional level inherits that inversion and
compresses top-end dispersion rather than widening it.** That closes legs 1/2/3
and any recombination — the surface is retired as the dispersion lever, not
just this composite. The live question it leaves is a DERIVE question under
rule 20 (is the inversion real, or an artifact of within-year net-load
conditioning that mixes winter/summer tight hours and samples already-committed
fast-start units?), owner-gated, never a residual-driven re-derive.

**K3 passed on its merits and is the reusable result.** The measured CT level
enters as `max(bid, target)` against the FULL P1 bid — after the startup
amortization and every additive adjustment — with **zero additive row-hours in
all three years**. That is the rule-19 reconciliation pjm-101/102 lacked when
the same level was floored against `mc_base` alone and stacked with the pjm-103
start-cost pricing (CT −12 TWh). The seam is now a tested primitive.

**Defect found (FINDING §6).** `derive_pjm_ordc_overlay._run_year_kwargs` — the
helper every PJM no-LP probe rebuilds a bundle's fleet with — drops **38
non-default `run_year` flags** the pjm-121 keeper records, including all three
`tranche_startup_*` gates (the CT stack's own pricing), `ct_netload_drag` /
`gas_st_netload_drag` and their overrides, and the `pjm_offer_midcurve_conditional`
master gate. The first pass of this pre-check measured leg 3 against a CT stack
with no start-cost markup at all; the symptom was the startup bracket
collapsing to `lo == hi`, now a hard error. The probe uses a widened
`full_run_year_kwargs` plus fidelity guards. Consequence: pjm-121 §5's
level-form magnitudes were measured on the partial reconstruction — its
conclusion is unaffected and is independently reconfirmed here, but those
specific numbers should not be quoted as the keeper fleet's.

**Verification.** The refactor letting the mid-curve builder and the CT target
share one surface/share context is **bit-identical** on the real 2025 keeper
fleet — the keeper-scope markup array (3,325 × 8,760) is byte-equal before and
after, 431 priced rows both ways.

Next number: pjm-124.
Next number: pjm-123.
## 2026-07-26 — PJM keeper re-audit on the guard-corrected CAMPD envelope (neiso-65 charter, attempted) — BLOCKED on container RAM after year 2023; superseded target: replay pjm-121

Charter execution (campd-economic-layup-fix-charter §8). Attempted on the
then-keeper pjm-119-overlay-restore recipe (per-gen reserve co-opt, 2,403
members): completed 2023 running alone, then OOM-killed at 15.9 GB during
2024's build in this session's 15 GB container. The 2023 partial bundle was
NOT registered (rule 16 — no partial-year bundles), no numbers from it are
quoted, and it was deleted before session end (regenerable whole by the
future replay). Replay
needs a ≥24 GB environment; clean partition prerequisites
(`transfer-interface-limits`, `ramp-capability`, gitignored
`pjm-da-virtuals` re-fetch) in
`results/calibration/RESULTS-neiso65-crossiso-reaudit-2026-07.md` §2/§3e.
Mid-session the parallel lane promoted `2026-07-25-pjm-121-cc-belt` (keeper)
and pruned the pjm-116…119 lineage incl. the attempted bundle, so the future
re-audit replays `results/calibration/pjm121_ccbelt` instead — solved
2026-07-25 on the pre-adoption envelope, so it carries the A0 semantics this
method requires; same RAM class (the delta is an offer surface, not LP size).
(This entry deliberately claims no lane number: pjm-122 was concurrently
taken by the artifacts-landing session above.)

## 2026-07-26 — pjm-124: `ramp10` deliverability scoping (frontier Lane 1, framing 2) — REFUTED on a no-LP pre-check, NO SOLVE SPENT

Full adjudication: `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`.
Probe: `scripts/probes/pjm124_ramp10_scope_precheck.py`, kill criteria K1/K2/K3
committed to git (`84288c3`) **before** the probe was run; per-year JSON in
`results/calibration/pjm124_precheck_{2023,2024,2025}.json`.

**The mechanism cannot remove the capacity that creates the slack.** The
keeper's balance families are **Primary** Reserve, and Primary = Synchronized +
**Non-Synchronized** (Manual 11 §4.2) — Non-Sync reserve *is* offline
10-min-startable iron. So a commitment-state scoping may drop offline
non-fast-start capacity (a cold CC/ST backs nothing) but may **not** drop
offline fast-start capacity, which counts either way. Measured on the
reconstructed keeper fleet: **1,411 fast-start members, 30.6 GW nameplate,
F = 17.6 GW mean — 45 % of the 38.9 GW deliverable-ramp cap, and 5.2× the
3.35 GW requirement by itself.**

Adding the two other dispatch-free online terms (`MG`, min-gen-floored units
online by construction; `DISP`, the greedy online capacity implied by the
keeper's own committed P1 class-hourly dispatch) gives a **rigorous lower
bound** on the scoped supply — the most generous case for the mechanism:

| GW mean | 2023 | 2024 | 2025 |
|---|---|---|---|
| requirement R | 3.09 | 3.42 | 3.35 |
| keeper cap | 38.74 | 38.67 | 38.95 |
| **S_lower** | **32.56 (10.5×R)** | **33.17 (9.7×R)** | **33.64 (10.0×R)** |
| reduction | 15.9 % | 14.2 % | 13.6 % |
| tight-bin hours ≤ 2×R | 0/2,191 | 0/2,190 | 0/2,190 |

**K1 KILLs unanimously in all three years**, by ~3× the PASS band, and does not
reach even the PARTIAL band (which needed a ≥50 % reduction). K2 is reported as
split and marginal (10.8 / 10.6 / 9.8 pp against a 10 pp threshold) and is moot;
what matters in that row is the **sign** — the scoping shaves 18–21 % in the
slackest net-load quartile but only 8–10 % in the tightest, i.e. least where the
residual lives. K3 passes: the scoping is fleet-physics + own-dispatch derivable,
no measured outcome enters. Framing 2 was never inadmissible — it is **inert**.

**The strict online-only variant is closed too**, on two independent grounds:
deleting non-synchronized supply from a *Primary* balance prices Synchronized
while calling it Primary (a product mismatch — rule 1's "never reach the right
number through a mechanism that isn't real"), and its own lower bound is still
**4.9× / 4.6× / 4.8× the requirement**. The whole framing-2 family is closed in
its admissible and inadmissible forms.

**Ledger consequence — this qualifies pjm-82's LP-vs-MIP attribution.** Even
with commitment state read exactly, and counting only iron the tariff permits,
the balance stays ~10× slack: **a MIP would not close this gate either.** The
slack is the size of PJM's reserve-eligible fast-ramping fleet against a ~3.4 GW
requirement — a real fleet property, not a representation artifact. Strong prior
that framing 1 (pjm-125) lands the same way; still worth running for the record.

**Free corroboration, no re-solve** — the keeper's persisted reserve dual
extended from pjm-120's 2025-only reading to all three years:
**0 hours ≥ $300 in 26,280**; 2023 and 2024 are *identically zero all year*;
2025's 22 nonzero hours (max $210.99, mean $0.151) are the tightest of the
three, not representative.

**Housekeeping done (frontier handoff §5).** `scripts/lib/bundle_fleet.py` now
owns the widened bundle-fleet reconstruction (`full_run_year_kwargs`,
`reconstruct_bundle_fleet`, year-chain gas-price fallback, generalized fidelity
guard over the offer-path *and* reserve gates);
`pjm123_composite_precheck.full_run_year_kwargs` delegates to it.

**Keeper unchanged** — `2026-07-25-pjm-121-cc-belt` stands, with its honest-scope
caveat intact (73 % of the 2025 C3a gain is a level lift; the dispersion
compression is untouched, and pjm-123 closed the offer-surface route to it).
Fidelity of this session's reconstruction confirmed against the committed keeper
hourlies: `pjm120_c3a_stratum_readout` reads model_lw 41.53 / actual 46.07 /
gap −4.54. No dashboard registration: no solve was run, so there is no bundle to
register (the pjm-123 precedent). **Frontier readiness flagged, never declared.**
## 2026-07-26 — the neiso-65 keeper re-audit is RE-ATTEMPTED on `pjm121_ccbelt` and RE-BLOCKED at the same point; the block is the container, not the recipe

Replayed `--replay-bundle results/calibration/pjm121_ccbelt --year 2023 2024
2025` in a fresh 15 GB / 4-core container, with every clean partition the recipe
needs regenerated first (`transfer-interface-limits`, `ramp-capability`,
`capacity-deliverability`, plus the gitignored PJM DA-virtual raw). pjm-121 does
require all three measured overlays (`pjm_measured_interface_limits`,
`measured_ramp_capability`, `pjm_da_virtual_bids`), so the §2 checklist applies
to it in full.

**Checklist addition (cost: one silent no-op each).** Two curate scripts abort
with `ModuleNotFoundError: No module named 'scripts'` when invoked plainly —
`curate_ramp_capability.py` and `curate_capacity_deliverability.py` must be run
as `PYTHONPATH=. uv run python scripts/data/curate_<...>.py`. In a `set -x`
prereq block the tracebacks scroll past and the solve then runs degraded; the
`data/clean/` listing is the check that catches it.

**Result: OOM again, same place.** The solve log carries no missing-input
warning (only the known eGRID/pmax reconciliations), so the replay was faithful.
Year 2023 completed; the process was SIGKILLed (`RC=137`) building 2024 — the
identical failure point the neiso-65 attempt hit on `pjm119_overlay_restore`.
Sampled peak RSS 13.8 GB at 20 s granularity, so the killing spike is not in the
trace. Since the recipe changed (pjm-119 → pjm-121) and the prereqs are now
present, the remaining variable is the container: the replay needs ≥24 GB, as
§3e said.

**Lead for that run.** 2023 fits alone and 2024 does not, on both attempts. That
is consistent with the year loop retaining the prior year's arrays rather than
with any single year being too large — worth measuring before assuming the LP
itself is the ceiling.

The partial bundle was deleted, not registered (rule 16 — no single-year
keepers, and no partial-year bundle on the dashboard). No numbers from the
completed 2023 are quoted anywhere.

(This entry deliberately claims no lane number, following the neiso-65
precedent: this is charter/cross-ISO work, not a PJM calibration lane, and
`pjm-124` was concurrently taken by the ramp10-deliverability pre-check session
above. The PJM lane's own numbering is untouched.)

Next number: pjm-125.

## 2026-07-26 — pjm-125: constrained commitment (frontier Lane 1, framing 1) — PARTIAL on a no-LP pre-check, NO SOLVE SPENT; **Lane 1 is now COMPLETE**

Full adjudication: `docs/FINDING-pjm125-commitment-constraint-precheck-2026-07.md`.
Probe: `scripts/probes/pjm125_commitment_constraint_precheck.py`, criteria
committed (`4860cf7`) **before** the run; JSON in
`results/calibration/pjm125_precheck_{2023,2024,2025}.json`. Run in the same
session as pjm-124 at the owner's explicit direction, after 124 closed.

**Framing 1 is NOT inert — and still cannot make the balance bind.** Where
framing 2 (pjm-124) attacked the per-pool ramp bound, framing 1 attacks the
other constraint family: the joint `Σ P + R ≤ Σ cap` row, which counts every
member's capacity committed or not. It works: a maximal commitment constraint
cuts the effective reserve supply bound by **51–53 %**, and — unlike framing 2 —
bites **hardest in the tightest net-load quartile** (40–43 pp, vs framing 2's
8–10 pp). K2 passes decisively.

| GW mean | 2023 | 2024 | 2025 |
|---|---|---|---|
| requirement R | 3.09 | 3.42 | 3.35 |
| keeper effective bound = min(ramp, joint headroom) | 37.12 (12.0×R) | 35.78 (10.5×R) | 34.80 (10.4×R) |
| hours where the RAMP family binds | 81 % | 70 % | 60 % |
| **S_floor** (commitment-invariant) | **17.34 (5.6×R)** | **17.18 (5.0×R)** | **16.99 (5.1×R)** |
| reduction vs keeper effective | 53.3 % | 52.0 % | 51.2 % |
| tight-quartile hours ≤ 2×R | 5/2,191 | 52/2,190 | 69/2,190 |

**K1 lands PARTIAL in all three years** (≥50 % narrowing, but the floor stays
5.0–5.6×R and the annual mean never reaches the ≤3×R PASS band). Verdict NO
SOLVE — which is what PARTIAL prescribes.

**Why the floor cannot go lower — and why this ends Lane 1.** Offline fast-start
capacity is **Non-Synchronized Primary reserve** (Manual 11 §4.2), so no
commitment mechanism may remove it: 17.5 GW, 45 % of the deliverable ramp. That
floor alone is 5.0–5.6× the requirement. Both framings pjm-120 §7 named are now
on record — 2 inert, 1 effective-but-insufficient — and they bound the entire
reserve **supply** side between them.

**This sharpens and partly qualifies pjm-82's LP-vs-MIP attribution.** pjm-82 is
right that commitment is where the surplus comes from (framing 1's 51–53 % bite
confirms it), but **a MIP would not close this gate either**: the 5×R floor
survives any commitment representation. The binding fact is that PJM's ~3.4 GW
requirement is small relative to the fast-ramping fleet serving it (30.6 GW
nameplate / 17.5 GW of 10-min deliverable ramp) — a real system property.
**Consequence: the remaining >$200 residual is not on the reserve supply side.**

**New ledger measurement (§2).** On the keeper today the **ramp** family binds
81 % / 70 % / 60 % of hours across 2023/2024/2025 — the joint capacity row is
progressively becoming the binding family, so framing 1 was aimed at a live
constraint, not a slack one. Separately: on the quantity that actually bounds
the co-opt, the surplus is 10.4–12.0×R (10.5–12.4× the measured SR+REG target),
*larger* than the 2.7–3.1× premise figure — **not the same quantity** pjm-82
measured (unloaded headroom on committed units under a posture-constrained arm),
so no claim is made about pjm-82's number; it only means framing 1's task was
harder, not easier.

**Disclosure (rule-1 honesty).** The pre-registered PARTIAL and KILL bands as
worded overlap. The first implementation checked only the "above 3×R" clause and
printed KILL; the measured 51–53 % reduction means the PARTIAL band applies. The
**code was corrected to match the pre-registered prose, not the reverse**, with
PARTIAL taking precedence as the more specific band; the NO-SOLVE decision is
identical either way. pjm-124 carries the same overlap but its reduction
(13.6–15.9 %) is far below the 50 % threshold, so **its reported KILL stands
unchanged** and was not revisited.

**Keeper unchanged** — `2026-07-25-pjm-121-cc-belt`, honest-scope caveat intact
(73 % of the 2025 C3a gain is a level lift; the dispersion compression is
untouched and pjm-123 closed the offer-surface route to it). No dashboard
registration: no solve was run. **Lane 1 complete; Lane 2 (pjm-126, the
owner-gated pjm-123 derive-conditioning review) is the only open lane.
Frontier readiness flagged, never declared.**

Next number: pjm-126.

## 2026-07-26 — pjm-126: the mid-curve surface's tightest-bin inversion is a CONDITIONING ARTIFACT (frontier Lane 2) — Lane 2 STAYS OPEN, frontier NOT ready

Full adjudication: `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md`.
Probe: `scripts/probes/pjm126_midcurve_conditioning_precheck.py`, criteria
committed (`9409f7f`) **before** the run; JSON in
`results/calibration/pjm126_conditioning_precheck_2025.json`. No LP, no surface
written, no derive re-run.

**The inversion does not survive re-conditioning.** Inversion gap =
median(bin2) − median(bin3); positive = tightest bin cheaper:

| segment | A_frozen (within-year) | B_season (within-season) | flag |
|---|---|---|---|
| CT_FAST | **+10.000** | **−0.850** | **FLIP** |
| CC_LIKE | **+0.350** | **−0.200** | **FLIP** |
| LONG_RUN | +0.100 | +0.250 | HOLDS (1 % of base) |

2 of 3 segments flip → **ARTIFACT** on the pre-registered criteria. **Fidelity
guard passed at full strength**: arm A reproduces the committed
`pjm_offer_midcurve_condbinned.json` 2025 ladders to **8.5e-13** (tol 0.05).

**Mechanism named — and it is the OPPOSITE of the handoff's hypothesis.** Not
co-mingling: **segregation**. PJM is summer-peaking, so winter's own tight hours
never reach the annual top-3 % of net load. Bin3 is **87 % summer (229 of 263 h,
only 34 winter)**; bins 1–2 are winter-enriched (477 / 249 winter hours). Winter
is when CT offers are most expensive (oil parity, gas basis, cold snaps), so the
middle bins are inflated and the tightest bin is a summer-only sample. Under
within-season ranking each bin is balanced (88/88/88) and the inversion vanishes.
The lower bin3 gas ($4.03 vs $4.53) is a *symptom* of the same segregation, not
an independent check — which is why the earlier gas test did not catch it.

**Limitation, stated plainly.** Arm C (fixed population) is **VACUOUS** — 711 of
711 units offer in all four bins, because PJM units submit offers regardless of
commitment — so its HOLDS flags are not evidence and the **commitment-status**
half of the hypothesis is **NOT tested**. That needs the DA *awards* side, which
the offer corpus does not carry. The verdict rests entirely on arm B, which is
decisive on its own for the two segments carrying the effect.

**Consequences.** pjm-123 §3 narrows to "the surface **as conditioned in the
2026-07 vintage**" — its legs 1/2/3 A/B results stand; the generalization to the
whole measured-offer-surface family does not. The measured surface is a **live
candidate dispersion lever again**, aimed at exactly the residual pjm-125 left
standing (pjm-121's caveat: the dispersion compression is untouched). **PJM has a
named admissible mechanism NOT tried — which is what the frontier bar excludes.
Frontier is NOT ready.**

**Not authority to re-derive.** Rule 20: a season-conditioned surface IS a
definitional change and admissible on that basis, but adopting it is a separate
**owner-authorized** step with its own admissibility memo — and the edges are
**shared with the frozen pjm-99 top-of-curve surface**, so the memo must settle
scope for both. Never because a residual moved.

**Conflict of interest, disclosed.** This probe was run by a session with an
interest in the REAL outcome (it would have closed Lane 2 and completed the
ledger). Criteria were made symmetric and quantitative and committed before any
arm was computed, with the ARTIFACT branch spelled out as specifically as the
REAL branch. The result went against that interest and is reported as measured.

**Scope: 2025 only** (fidelity-exact). 2023/2024 corpus fetching for
confirmation — the CT_FAST flip is far too large to be plausibly reversed, but
the multi-year check is owed (pjm-127). Keeper unchanged; no dashboard
registration (no solve).

Next number: pjm-127.

## 2026-07-26 — pjm-127: the conditioning artifact CONFIRMS in all three years (no-LP); the re-derive decision memo goes to the owner

**Task.** Frontier Lane 2 follow-through: (a) the multi-year confirmation
pjm-126 §5 owed, (b) the owner admissibility memo for the season-conditioned
re-derive. Both no-LP; **no solve spent, keeper unchanged, no dashboard
registration (no bundle exists).** Full write-up:
`docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`; the decision memo:
`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`.

**1. pjm-127a — ARTIFACT in every year, and pooled.** The identical pjm-126
probe (one NA-safety fix for the 2023 fall-back day's NaT row — mechanical,
committed before the 2023 run) on the freshly fetched 36-month corpus:
**2023 ARTIFACT 3/3 segments FLIP** (CT_FAST +3.00→−3.00, CC_LIKE
+0.20→−0.30, LONG_RUN +0.25→−0.30), **2024 ARTIFACT 2/3** (CC_LIKE FLIP
+0.40→−0.30; CT_FAST NARROW 77%, +5.10→+1.15), **2025 reproduced
identically** from pjm-126 on the re-fetched corpus, and the **pooled
three-year hard-guard run: ARTIFACT 3/3 FLIP** (CT_FAST +5.85→−0.60,
CC_LIKE +0.20→−0.30, LONG_RUN +0.25→−0.05; worst fidelity deviation
9.2e-13, `--skip-fidelity` never used). Mechanism evidence is starker in
the confirmation years: the annual top-3% net-load bin holds **3 winter
hours in 2023 and 1 in 2024** (34 in 2025) — winter scarcity is
unrepresentable under within-year ranking by construction. Arm C stays
vacuous every year (≥99.2% of units offer in all four bins), so the
commitment-status half is still untested (pjm-128, DA awards side).

**2. pjm-127b — the owner memo, pre-registered before the numbers.** The
memo's definitional case (within-season rank as the better tightness-state
definition, argued from PJM's seasonal market structure only — no residual),
its scope decision (BOTH surfaces re-condition as one definitional vintage —
the mid-curve and the frozen pjm-99 top-of-curve share one tightness
definition by design — plus coherent solve-time seam change and a vintage
guard), the pjm-126 season boundaries kept verbatim, a staged pre-registered
A/B (no-LP K1-gradient pre-check before any solve; tight-strata-gradient
PASS vs level-shift REFUTATION signatures), and the forward-regeneration
consequences (rule 13 passes identically; forecast winters see the measured
tight state for the first time) were **committed while the probes were still
running** (`cee35d5`) and only the status banner changed after. Rule 20 is
satisfied on its face: the re-derive, if authorized, cites a
conditioning-definition change, never a residual.

**Lane state.** Lane 2 remains open pending the owner's call on the memo.
If authorized: staged re-derive per memo §4 (pre-check first, then the A/B
chain, rules 12/14/16). If declined: the lever is formally blocked on an
owner decision — a legitimate ledger entry, not a frontier completion.
Frontier stays NOT ready either way until the lever is tried or formally
blocked.

Next number: pjm-128.
## 2026-07-26 — CAMPD charter LANE B (cross-ISO, **no PJM lane number claimed**): the day-grain `R < 0` cut does not replace the guard's window-grain cut

Charter/cross-ISO session — measurement only: no guard change, no extract
re-derive, no LP solve, **no PJM keeper touched**, no dashboard registration.
Full record: `results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md`;
cross-ISO entry in `docs/calibration-log/governance.md`.

PJM's cell of the 180-cell sweep (`--rcc-pctl {0.50, 0.75, 0.90, 0.99}` × `--horizon {24, 48, 72}` ×
2023–2025), scored against **PJM Data Miner 2 `gen_outages_by_type`, region `PJM RTO`, `lead_days = 0`**:

* **KEPT-extract monthly `r` at the default p90 / h24**, window-grain → day-grain:
  2023 **+0.90 → +0.90** (Δ +0.001), 2024 **+0.91 → +0.90** (Δ −0.006), 2025
  **+0.95 → +0.95** (Δ +0.002). Over PJM's 36 cells the day cut is better in
  **19/36**, median Δ **+0.000**; both cuts clear the placebo in the same 21/36
  cells.
* **The two cuts pick the same windows**: Jaccard 0.88 / 0.88 / 0.92. PJM carries
  the sweep's largest day-only veto counts (29 / 26 / 22) and they buy nothing —
  out of ~1,600 windows a year they move the kept-`r` by ≤ 0.006.
* **Control passed**: the re-implemented incumbent reproduces PJM's committed
  kept/layup split on 1,676/1,684, 1,624/1,635, 1,583/1,591 windows.

**Nothing in PJM changes.** The merit-order guard stands as the charter §8
verdict adopted it, PJM's committed extract and layup companion are
untouched, and no rule-22 obligation arises because no mechanism change is
proposed. The PJM keeper re-audit still blocks on a ≥ 24 GB environment (OOM at 15.9 GB);
Lane B needed no solve and is unaffected by it. Next number unchanged: **pjm-128**.

## 2026-07-26 — pjm-128: the commitment-status half of Lane 2 is BLOCKED ON NON-PUBLIC DATA — no public unit-level DA award feed exists

Full write-up: `docs/FINDING-pjm128-da-award-feed-scope-2026-07.md`. Census:
`scripts/probes/pjm128_da_award_feed_scope.py` (admissibility test committed
`d52740b` **before** the census ran); result JSON
`results/calibration/pjm128_da_award_feed_scope.json`. **No LP, no solve, no
surface written, no derive re-run, keeper unchanged, no dashboard registration
(no bundle exists).** No bulk intake — every request is a sample.

**0. The owner memo is still undecided, so nothing was re-derived.** The
session checked for a decision on
`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md` first, found none,
and fell through to pjm-128 per the charter — no nudge, no re-derive. Rule 20
leaves the season-conditioned surface inadmissible until the owner decides.

**1. Verdict: NO_PUBLIC_FEED.** pjm-126 arm C was vacuous in all three years
(≥99.2 % of units offer in all four bins), so the commitment-status half of the
conditioning hypothesis — the tight-bin offer population being disproportionately
*already committed* — was never tested. It needs the DA **awards** side. The
admissibility test committed before the census: a feed qualifies only if it
resolves **an individual unit (A1)** × **an hourly-or-finer time key (A2)** ×
**a cleared/awarded/committed quantity (A3)**. PJM's public DataMiner2 catalog
was enumerated from the API itself — **119 feeds**, 26 tripping a
commitment/award keyword net — and every plausible candidate sampled live so the
verdict rests on measured schemas, not catalog prose. **None satisfies A1+A2+A3.**
The only unit-resolved hourly feed is the offer corpus we already hold
(`energy_market_offers`, 90.6 M rows) and it fails A3: offers, never awards.
The near misses fail on grain — `ops_init_commit` is **zone**-level (20 zones,
out-of-market commitments only), `rt_and_self_ecomax` and `day_gen_capacity`
are **system** totals, `gen_specific_uplift_credit` is per-generator but
**monthly dollars**. PJM's own posting page states it: no cleared/awarded MW, no
day-ahead schedule or commitment status, no unit online/offline status.

**2. PJM withholds the committed quantity by rule — measured, not inferred.**
`rt_and_self_ecomax` is the closest published committed-capacity series and is a
**system hourly total**; even there the RT-committed column is redacted under
PJM's own `"Confidentiality Rules Prohibit Display"` flag in **35.9 %** of hours
(Jul 2025) and **49.7 %** (Jan 2023). A quantity redacted at *system* level is
not one published per unit — that is the mechanism behind the absence.

**3. A second, independent blocker: the offer corpus cannot be joined to
anything.** The question is the committed share *of the offer population*, so any
external award source would have to join to the offers. Measured on one mid-July
day per year: **1,219 distinct `unit_code` in 2023, 1,252 in 2024, and 0 codes in
common — Jaccard 0.0000.** PJM re-draws the masked codes annually and publishes
no crosswalk, so the two code spaces are completely disjoint. Even a perfect
external unit-hour award series could not be attached. **Route refused, not
untried:** fingerprinting masked units against EIA-860/CAMPD by their
ecomax/ecomin/start-cost signature would de-anonymise data PJM masks under its
confidentiality rules; recorded as refused so no later session treats it as
unexplored.

**4. No aggregate proxy, deliberately.** `ops_init_commit` (zone) and
`day_gen_capacity` (system `total_committed`) could each be regressed against the
tightness bins to manufacture a committed-share number. The charter forbids it and
rule 1 forbids it independently. The half stays **untested, not refuted**.

**Ledger.** Lane 2's commitment-status half is **CLOSED, terminal — blocked on
data that does not exist publicly**, which is the frontier bar's own second
clause (the state NYISO's remaining lever occupies). The season half is
unaffected: pjm-126/127's ARTIFACT verdict never rested on arm C. **Frontier
remains NOT ready, and now for exactly one reason** — the owner decision on the
re-conditioning memo is the last named admissible mechanism that is neither tried
nor formally blocked. Authorize-and-run or decline-and-record; the ledger is
whole either way.

Next number: pjm-129.

## 2026-07-26 — pjm-129: the keeper does NOT hold on the guard-corrected CAMPD envelope — RE-TUNE REQUIRED (3 gates), and the "needs ≥24 GB" block was never real

**Lane:** the last PJM cell of
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §5/§8. Charter,
pre-registered and committed **before any result was read**:
`docs/handoffs/pjm-129-keeper-reaudit-charter-2026-07.md`. Full evidence:
`results/calibration/FINDING-pjm129-keeper-reaudit-meritguard-2026-07.md`.
(Opened as pjm-128; renumbered when the concurrent DA-award-feed census, PR
#2965, took that number mid-session.)

**Registered arm:** `2026-07-26-pjm-129-meritguard-a1` (PJM 2023/2024/2025, one
bundle, rule 16; rule 15 — registered whatever the verdict).

### Verdict

**DETERMINATION `CALIBRATED` (10/10, PJM's first all-pass) → `NOT-YET` (7/10).
RE-TUNE REQUIRED**, three newly-failing gates:

| gate | keeper | A1 | band |
|---|---|---|---|
| C3a mean LMP **2025** | −9.3 % ($41.53 / actual $45.80) | **−10.6 %** ($40.93) | ±10 % |
| C3c tail **2024** | 9 h vs 18 h, 0.50× | **7 h, 0.39×** | ≥0.5× |
| C3c tail **2025** | 39 h vs 59 h, 0.66× | **28 h, 0.47×** | ≥0.5× |
| C1 **2023** CC_REGULAR | −7.87 TWh, −0.4 pp | **−8.10 TWh**, −0.5 pp | 8 TWh **and** 3 pp |

C2 / C3a-2023,24 / C3b / C4 / C5a / C6 / C7 / C8 all still PASS; free-class C1
16/16 → 15/16 (free 12/12 → 11/12). **C3a-2023 (+5.6 → +4.0 %), C3b-2023 (0.157 →
0.152) and C5a-2023/24 improve.** Nothing was tuned and nothing is licensed to be.
**Keeper designation UNCHANGED** — promoting/demoting on a NOT-YET arm is an owner
call (miso-88 precedent).

### The isolation — the code is provably PJM-inert, the extract is the whole story

The charter flagged that `0069f8e..HEAD` is 28 files / +2,235 lines under `src/`,
including `offer_surfaces.py` +391 — the module owning the keeper's own
`pjm_offer_midcurve_segments` `CC_LIKE` scope. One single-year throwaway probe
closed it: 2025 solved at HEAD with `campd-unit-outages-PJM.csv` reverted to the
keeper's blob `5283f5c6`.

| arm | 2025 sidecar LW $/MWh | C3a |
|---|---|---|
| KEEPER (`0069f8e`, pre-guard extract) | 40.070 | −9.3 % |
| A0′ (HEAD, pre-guard extract) | **40.070** | −9.3 % |
| A1 (HEAD, guard-corrected extract) | 39.552 | **−10.6 %** |

**Code drift with the extract held fixed: $+0.000.** A0′'s `system_2025` and
`class_hourly_2025` are `max|diff| = 0` against the keeper's committed sidecars on
**every** column (price/slack/dump/demand/reserve_price/per-class mw). Corroborated
in-log: A0′ reports deliverable ramp mean **38.1 GW**, the exact figure in the
keeper's own designation note, vs A1's 38.9 GW. The guard/extract owns **100 %** of
the −$0.518 (−1.3 pp) move. PJM does **not** carry the caiso-123 confounded-A0
defect (the extract blob changes exactly once after the keeper's sha, at `6a8f285`,
and the on-disk file hashes to HEAD's blob). Keeper re-scored on the same bench
**after** registration: still CALIBRATED 10/10.

### Why prices fall (measured from the two blobs, no solve)

Guard removes **903 windows / 4,624 GW-days** over 2023–25 and adds zero — 15.3 /
9.7 / 14.3 % of each year's envelope (11.7 % pooled, close to MISO's 12.8 %), of
which **ST_GAS is 2,528 GW-days (54.7 %)**, COAL 984, CC_REGULAR 841. Class volumes
move accordingly (2023 TWh): ST_GAS 8.09 → 10.60, COAL_BIT +0.92, **CT_PEAKER 23.20
→ 21.78**. Rule 11 discovered bug — the keeper's offer curves were compensating for
an inflated envelope (NEISO / ERCOT-79 / nyiso-63 / miso-93 condition; −1.3 pp here
vs MISO's −1.4 pp). **2025 fails because it started 0.7 pp from the veto, not
because its move was largest.** C3c is the consequence the charter *missed*: adding
supply removes scarcity hours (5→2 / 9→7 / 39→28 against unchanged 6/18/59) — it
deepens the already-open G-20b/G-22 reserve-tightness root cause rather than
creating a new one.

### The RAM block is closed, and it was never a bigger box

Two prior attempts (neiso-65 on `pjm119_overlay_restore`, then its re-attempt on
`pjm121_ccbelt`) were SIGKILLed at 15.9 GB building **2024** and both concluded
"needs ≥24 GB". Measured here from the release-block telemetry, one fresh process
per solve-year:

| year | `resident` after release | `peak` | accumulators |
|---|---|---|---|
| 2023 | 1.06 GB | 14.87 GB | 0.07 GB |
| 2024 | 1.19 GB | 14.94 GB | 0.13 GB |
| 2025 | 1.26 GB | 15.06 GB | 0.19 GB |

**The year loop is not leaking** — it releases to a fully-attributed ~1.1 GB floor
(miso-92's attribution, 35 % of it already removed). What kills a single-process
run is `peak(N+1) + floor(N)` = **15.93 GB at year 2**, reproducing the reported
15.9 GB kill at the year both attempts reported it, to 0.03 GB. **The single-year
LP peak is the ceiling.** The staged one-year-per-process `--reuse-solved` chain
fits every PJM year in this 15.7 GB box with 0.6–0.8 GB spare — and
`pjm121_ccbelt`'s own attestation already recorded it was solved that way at
"peak ~14.8 GB". No CI job was spun up; no bigger box is needed. The suggested
1-zone/24-hour toy was deliberately **not** run: at ~0.01 GB it cannot
discriminate a 15 GB peak from a 1.1 GB floor.

### Ops

* Four solve-years (2023, 2024, 2025 + one 2025 isolation probe). The probe bundle
  and both staged intermediates were **deleted**; no partial-year bundle exists
  (rule 16). `class_hourly_2023/2024` lifted from the staged bundles and verified
  `max|diff| = 0` against the final bundle's own `system_<year>` slices.
* Prereqs regenerated before solving (`transfer-interface-limits`,
  `ramp-capability`, `capacity-deliverability`, all 36 months of
  `pjm-da-virtuals/hrl_da_incs_decs`); every solve log audited — overlays confirmed
  live (6 measured interfaces + EAST cut, 128 DA virtual pseudo-units, deliverable
  ramp 38.7–38.9 GW).
* **Reported, not introduced:** registration moved four CHP cells in
  `bench/PJM/2025.json.gz` (`classFull` CT_CHP 0.5456 → **−0.3726**). That is the
  documented run-own-`btm.parquet` subtraction — the stored CHP split belongs to
  whichever run registered last; symmetric, so no C1 row is biased, and the keeper
  re-scores 10/10 on it. Flagged for the PJM lane.
* Rule 22: 2023–2025 only; **freeze untouched and NOT lifted** (owner only).
* Rule 12: years strictly sequential, one process each. No concurrent invocation —
  a single PJM year needs 14.9–15.1 GB of a 15.7 GB box.

### Notes for the next session

* **PJM needs a re-tune charter** scoped to three gates under a ~1.3 pp structural
  price reduction, and it must close **by structure** — the corrected extract stays
  in (rule 1). Cheapest first: **C1-2023 CC_REGULAR is 0.10 TWh past an 8 TWh
  band** (1.2 % of band) on a class the guard barely moved (−0.23 TWh). **C3a-2025**
  is the pjm-120/122/123 dispersion/level stratum, with pjm-122's measured-ownership
  route the standing candidate. **C3c** is downstream of G-20b/G-22 and both
  scoping framings are already closed (pjm-124/125), so it needs the root cause.
* Code churn `0069f8e..HEAD` is measured **PJM-inert**; don't re-establish it.
* Next number: **pjm-130.**

---

## pjm-130 — the re-tune opens: gate 1 is displacement with a real lever, gates 2/3 blocked, and a negative metered volume fixed (2026-07-27)

**No LP solved.** Charter: `docs/handoffs/pjm-130-retune-charter-2026-07.md`.
Finding: `results/calibration/FINDING-pjm130-gate1-and-bench-symmetry-2026-07.md`.
Both probes were committed before they were run (`0aa1b88`, `b93c305`).

**Gate 1 (C1-2023 CC_REGULAR, −8.10 TWh vs 8.00 band) — DIAGNOSED, not closed.**
Pre-registered displacement rule met unambiguously in the failing year: **99.6 %**
of CC_REGULAR's gross hourly loss falls in hours the guard-returned supply rose,
r = **−0.369** (2025 also confirms, −0.433; 2024 reported AMBIGUOUS on its own
rule rather than rounded in). The pre-registered kill criterion — a lever exists
only if a returned class overshoots its *metered* actual — is **met**: 2023
CC_CHP **+2.54 TWh (+41 % over meter)** and ST_GAS **+1.72 TWh (+19 %)** against
CC_REGULAR's −8.10. CT_PEAKER *improves* to +0.12 (was +1.54). So the guard
displaced peaking correctly but routed the freed energy to classes the meter says
did not serve it — the same merit-ownership question pjm-122 named for gate 2.
**Gates 1 and 2 are one stratum.**

**Gate 2 (C3a-2025) — BLOCKED, owner decision.** Its only level-bearing
admissible route needs the re-conditioning memo, verified **still undecided**
(last commit `f1070d4`). Not nudged, not re-derived, no proxy taken (rule 23).

**Gate 3 (C3c 2024/2025) — LEDGERED, root cause out of reach.** Both scoping
framings closed (pjm-124/125); the shared floor is 5.0–5.6× the requirement and
17.5 GW of it is tariff-protected Non-Sync Primary reserve, so a MIP would not
close it either. No mechanism invented (rules 1 / 19).

**Shipped — the gate-1 prerequisite.** pjm-129 §6's negative committed metered
volume (`bench/PJM/2025.json.gz`, `classFull.CT_CHP = −0.3726 TWh`) is
reproduced, localized and **fixed** (`03e105f`). `--btm-backfill-year` repaired
the *subtrahend only*: the benchmark's own CAMPD repair fires on **non-CHP**
plants by construction, so a backfilled CHP plant's host share was subtracted
from a class total that never received its energy. Arming
`--btm-backfill-year 2024` recovers the committed `btmClass` cells
**4.4251 / 2.0959 / 0.6801 to 4 dp** and breaks the invariant at exactly CT_CHP.
`_backfill_chp_eia923_from_donor` mirrors the repair onto the benchmark (same
donor, same `campd_active` gate, same per-(plant, class) key), so
`btm[k] ≤ e923_bench[k]` holds by construction. **2023/2024 are byte no-ops**;
2025 CT_CHP `classFull` −0.2798 → **+1.4653**. No C1 row changes verdict. The
corrected bench lands on the next PJM registration. Pinned by
`tests/regression/test_btm_benchmark_symmetry.py` (6 tests).

Because 2023 is a complete vintage the fix is a no-op there, so gate 1's
+2.54 TWh CC_CHP overshoot is real and unaffected.

**Reported, not introduced:**
`test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
fails on a clean checkout of `origin/main` in this container (expected
`edbc1b103207170a`, got `30065460cdc3042c`) — verified pre-existing by stashing.
Flagged, not touched; the test warns against updating the literal to silence it.

**Rules:** 22 — 2023–2025 only, freeze untouched and NOT lifted. 15 — no solve
completed, so no bundle to register; nothing solved and dropped. 20/23/24 —
nothing tuned. 27 — `run_calibration_full.py` (10,422 lines) edited in place and
blob-verified byte-identical after push. Keeper `2026-07-25-pjm-121-cc-belt`
untouched.

Fidelity anchor re-verified this session (no solve): `pjm120_c3a_stratum_readout.py
results/calibration/pjm121_ccbelt --year 2025` → model_lw **41.53** / actual
**46.07** / gap **−4.54**.

---

## pjm-131 (2026-07-27) — gate 1 has no admissible arm: its CC_CHP half is an economic merit miss, its ST_GAS half is grounded, and the measured host-share artifact is globally degenerate

**No LP solved.** Charter: `docs/handoffs/pjm-131-gate1-arm-charter-2026-07.md`
(committed as `e454b87` **before** the probe ran). Finding:
`results/calibration/FINDING-pjm131-gate1-no-admissible-arm-2026-07.md`.

**Priority 1 — the re-conditioning memo is STILL UNDECIDED.** Verified: last
commit `f1070d4`, live banner "awaits the owner's decision", no authorization
anywhere in the tree. Not nudged, not re-derived, no proxy taken (rule 23).
Gate 2 stays blocked, so the session proceeded to gate 1.

**Gate 1, CC_CHP half — REFUTED as an arm, and re-classified.** The only
structural lever pointing at CC_CHP is the behind-the-meter host share, which
for the gas CHP classes is a **grid-capacity pull-out** (`grid_cap = nameplate ×
(1 − pct_mr/100)`, `mustrun_cap = 0`) and is simultaneously the bench
subtrahend. On the `pjm129_meritguard_a1` fleet reconstructed with **no LP**
(`scripts/lib/bundle_fleet.py`), **κ = 0.0226** of CC_CHP's 2023 energy is
produced at ≥99 % of its hour-varying available grid capacity, at **72.7 % mean
utilization**. The pre-registered Q3 rule (`κ ≤ 0.20` ⇒ economic ⇒ refuted)
fires with room to spare: the class **clears on price, it is not
capacity-constrained**, so a capacity cut is absorbed while the bench actual
falls in full and the overshoot *enlarges*. The probe reproduces pjm-130 §2
exactly — model **8.653** / actual **6.1148** / overshoot **+2.538 TWh**.

This **upgrades pjm-130's "gates 1 and 2 are one stratum" from an analogy to a
measured dependency**: the +2.54 TWh is a merit-ownership miss, so it closes
only via the re-ownership of the $40–150 region (pjm-122) — gate 2's
owner-blocked route. Gate 1 is **not independently armable**; no separate CC_CHP
lane should be opened.

**Gate 1, ST_GAS half — GROUNDED, ledgered.** From the A1 bundle's committed
`legitimacy_diagnostics.json` (no solve): `st_netload_drag` forces **54.6 %** of
ST_GAS in 2023 (5.05 of 9.25 TWh), over the 30 % cap — but it carries a **cited
`D4_WINDOWS` declaration** (all-24h, on measured CAMPD overnight-CF evidence)
and scores **D-4 pass, 0.000 off-window** in all three years, with D-1 shape
passing (`profile_r` 0.97 / 0.92 / 0.90). That is rule 18's over-budget
escalation path satisfied — a clean pass, reported as a note. Per the
pre-registered Q5 rule: **not a floor-window artifact ⇒ ledgered, not
mechanised** (rules 1 / 19). Recorded but not acted on: ST_GAS `cv_ratio`
1.9 / 2.8 / 2.2 — the model's off-peak ST_GAS is *more* variable than the
measured fleet.

**New defect — `chp-btm-share` is globally degenerate.** `btm_share ≡ 1.0` on
**62 of 62 rows across 5 ISOs** (CAISO curates none). Root-caused upstream in
`plant_emission_rates_v2`: the curation's cogen signature is
`steam_load_klbh_sum > 0` and it sums `net_mwh` over exactly those rows, but at
CEMS the steam load and the electrical output are reported on **different
units** — **2,914 of 2,915** steam-reporting unit-years carry
`gross_mwh = net_mwh = 0`, so the CAMPD term is zero by construction. A
plant-level repair recovers only **24 of 134** cogen plants (a CEMS-visibility
-biased sample), so **no repair was shipped**: this is rule 14's own
"misaligned to our representation" exception and the sector-keyed estimate
correctly stands, now documented. **Latent forecast exposure flagged:**
`runner.py` resolves this artifact for forecast years, so any ISO with a curated
partition would pull every covered CHP plant 100 % behind the meter.

**Corrections disclosed (finding §4):** the charter's Q4 propagation had a sign
slip (`1 − κ·delta_cap` should be `1 + κ·delta_cap`, `delta_cap` being the
signed capacity change) and one verdict key was mis-named. Both corrected at the
site with the correction commented; neither changes a verdict.

**pjm-130 §6's test failure is NOT reproducible.**
`test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
**passes** at `origin/main` = `8e5053e`: `ScenarioConfig().cache_key()` returns
the pinned **`edbc1b103207170a`**, the pin literal is unedited, it is not
data-dependent (re-run with `data/clean/` moved aside), and `scenarios.py` has no
live env-var knobs (all five hits are historical comments — rule 24 clean).
Recorded as unreproduced, not silenced. **`--reuse-solved` is unaffected.**

**Rules:** 22 — 2023–2025 only, freeze untouched and NOT lifted. 15 — no solve
completed, so no bundle to register; nothing solved and dropped
(pjm-124/125/126/127/128/130 precedent). 16 — no bundle produced. 1/19/20/23/24/26
— nothing tuned, no mechanism invented for either half. 27 — no existing file
≥300 lines modified; the only new code is two probes. Keeper
`2026-07-25-pjm-121-cc-belt` untouched.

**Still pending:** pjm-130's bench fix has **not** landed on the dashboard — the
renderer writes `bench/` at registration and this session registered nothing, so
`bench/PJM/2025.json.gz` `classFull.CT_CHP ≈ +1.4653` awaits the next PJM
registration.

Fidelity anchor re-verified this session (no solve): `pjm120_c3a_stratum_readout.py
results/calibration/pjm121_ccbelt --year 2025` → model_lw **41.53** / actual
**46.07** / gap **−4.54**.

**Next number: pjm-132.**

---

## pjm-132 (2026-07-27) — the authorized within-season re-conditioning is REFUTED; Lane 2 ends; PJM is NOT frontier, and the blocker is the keeper

**Two solves registered** (rule 15, win or lose): `2026-07-27-pjm-132-control`
and `2026-07-27-pjm-132-withinseason`, both 2023+2024+2025 in one bundle
(rule 16), both **rejected probes**. `keepers.json` untouched.
Charter: `docs/handoffs/pjm-132-midcurve-reconditioning-charter-2026-07.md`.
Finding: `results/calibration/FINDING-pjm132-withinseason-refuted-2026-07.md`.

**The memo was AUTHORIZED** (owner, 2026-07-27) with a *"keep the current config
as default unless seasonal is new keeper"* amendment, which superseded memo §2's
file-swap clause only: the within-year surfaces keep their filenames and stay
live, the within-season vintage is a separate artifact, and one default-OFF
`ScenarioConfig` gate switches the JSON vintage and the seasonal binning
together behind a vintage guard.

**Stage 1 PASSED, Stage 2 REFUTED.** K1 gradient 3/3 positive on bids (+0.997 /
+0.437 / +0.125) but the pre-registered honesty bound fired in every year,
worst in the only failing year (2025 tight-bin rise **$0.152/MWh** vs a ~$1
floor) — reported to the owner *before* the chain was spent. The A/B then
measured the predicted nothing: C3a-2025 **−0.011 $/MWh** against a −4.54 gap,
dispersion NARROWS in 2023 (−0.045) and 2024 (−0.144). The PASS signature
required the 2025 gain carried by the tight strata AND dispersion widening
toward actual; neither holds. **Lane 2 ends** — the measured-offer-surface
family has now been tried as a dispersion lever under BOTH conditioning
definitions.

**The control validated itself:** 2025 at **40.932**, reproducing pjm-129's
guard-corrected A1 (40.93), not the keeper's pre-guard 41.53.

**The artifact is real and ISO-wide** (EIA-930 only, no LP): MISO and NYISO
carry **zero winter hours** in their annual top-3% bin all three years; PJM is
mid-pack at 95.2% summer. So the definitional case is not PJM-specific, but
acting on it elsewhere needs each ISO's own memo (rules 23/25). The gate stays
**default-off** — the owner's "default if it helps the forecast" condition is
**unverified** (forecast skill is a different program) so it did not fire.
Runtime cost measured: **2.85 ms/solve-year**, 0.0003% of a solve.

**Shipped — pjm-130's bench fix was INERT and now actually lands.** The mirror
`_backfill_chp_eia923_from_donor` recovered `btm_backfill_year` from
`run_config.json`, but **no bundle records it there** — it lives in
`meta.json`, which is where the BTM side reads it. So the one-sided repair
persisted and PJM 2025 `classFull.CT_CHP` stayed at a **negative metered
volume**. `rebuild_benchmark` now checks `meta.json` first: **−0.3726 →
+1.3724** (CC_CHP 6.2811 → 6.4446); 2023/2024 byte no-ops; invariant restored;
6/6 symmetry tests pass. pjm-130 predicted +1.4653 — the live path gives
+1.3724 and the ~0.09 offset is left open, not quoted away. Found because the
owner questioned why CHP BTM would not simply be measured from the backcast
year's own EIA-923 (it is — the backfill only repairs plants missing entirely
from the thin 2025 vintage).

**FRONTIER: recommend NOT declaring.** The **mechanism-ledger half is complete**
— no named admissible mechanism remains untried. But the **calibration half is
not met**, and the frontier handoff's claim that "PJM clears the first half
already (10/10)" is no longer true on corrected data: the keeper is CALIBRATED
only on the pre-guard inflated outage envelope, while the same recipe on the
corrected envelope is **NOT-YET (C1 FAIL 15/16, C3a FAIL, C3c FAIL)**. Frontier
requires every hard **and volume** criterion in band with the residual confined
to the C3c tail; PJM fails a volume criterion *and* a price-level one. The real
open item is upstream and **owner-only** (miso-88 precedent): the keeper
designation on the corrected envelope. Three routes in the finding §5.

**Rules:** 22 — 2023–2025 only. 15/16 — both arms registered, one bundle each,
parity clean, `audit_keepers.py --iso PJM` PASS. 25 — PJM only. 1/20/23/24/26 —
ranking scope changed and nothing else; gate registered in
`_CACHE_KEY_OPTIONAL_FIELDS` so the pinned default cache key stays
`edbc1b103207170a`. 27 — every ≥300-line file edited in place and blob-verified.


## 2026-07-27 (pjm-133) — KEEPER RE-DESIGNATED onto the corrected envelope: `2026-07-26-pjm-129-meritguard-a1`, NOT-YET 7/10 (owner instruction; FINDING-pjm132 §5 route 2)

No solve. The owner took the keeper-designation call pjm-129 flagged and
pjm-132 §5 reserved: PJM's keeper is now the run reproducible on TODAY'S
code — `2026-07-26-pjm-129-meritguard-a1`, the pjm-121 recipe (zero config
delta) replayed at HEAD on the guard-corrected outage envelope, 2023+2024+2025
one bundle (rule 16). Determination **NOT-YET, 7/10**: C3a-2025 −10.6 %
(±10 band), C3c-2024 0.39× / C3c-2025 0.47× (≥0.5× band), C1-2023 CC_REGULAR
−8.10 TWh (8.00 band, 0.10 over). C2/C3a-2023,24/C3b/C4/C5a/C6/C7/C8 hold;
C3a-2023, C3b-2023, C5a-2023/24 improve vs pjm-121.

**Why:** `2026-07-25-pjm-121-cc-belt` scores CALIBRATED 10/10 only on the
pre-guard inflated envelope — data the project corrected and kept — and does
not reproduce at HEAD (pjm-129 isolation: post-keeper code drift $0.000, the
extract owns 100 % of the −$0.518 move; pjm-132 control independently
reproduces the corrected 2025 baseline, 40.932 ≈ 40.93). Keeper = most
structurally faithful on current data (rules 1/13/14), not the best score on
superseded data. pjm-121 stays registered as the historical all-pass; its
sidecar is untouched. (Dashboard-confusion note, for the record: the "122"
in pjm-121's notes is the pjm-122 *session* that byte-faithfully re-solved
the bundle after the original container was archived — there is no pjm-122
run id.)

**Frontier state is unchanged by the swap and remains NOT frontier** — the
mechanism ledger is complete (pjm-124…132) but a volume criterion is out of
band and the residual is not confined to the C3c tail (pjm-132 §5). The
three failing gates have no named admissible mechanism left; what remains is
new structure on the G-20b/G-22 reserve-tightness class (now carrying the
guard-falseneg-audit SUSPECT-grade lead: ~2.8–5.0 GW avg returned capacity
per tight net-load hour, `FINDING-guard-falseneg-audit-2026-07-27.md` §6) or
a governance attestation of the misses as measured-input limitations
(pjm-132 §5 route 3 — C1-2023 at 1.2 % over band is arguably one, C3a-2025
at −10.6 % is a harder case; owner call, not taken here).

Rules: 15 — no solve, nothing new registered; keeper swap + status rebuild
only. 22 — no year touched. 27 — `audit_keepers.py --iso PJM` PASS 0
failures after `build_status.py --iso PJM`; sidecar definition refreshed to
describe the run as keeper (calibration-keeper-auditor pass). Files:
`keepers/PJM.json`, `registry/2026-07-26-pjm-129-meritguard-a1.json`,
`status/PJM.js`.

**Next number: pjm-134.**

---

## pjm-133 — `hydro_budget_nameplate_aware`: every gate passes, no kill fires

**Executes the caiso-130 cross-ISO hand-off** (FINDING-caiso130 §5 item 4) as its
own single-delta A/B. Registered: `2026-07-27-pjm-133-nameplate` (arm B) and
`2026-07-27-pjm-133-control` (arm A), both 2023+2024+2025, one bundle each
(rules 15/16). Prereg `PREREG-pjm133-...-2026-07-27.md` committed at `e1bb3d1`
and merged to main **before either arm solved**. Full write-up:
`results/calibration/FINDING-pjm133-hydro-budget-nameplate-aware-2026-07-27.md`.

**The pre-solve prediction was exact.** The prereg stated the nameplate clip
explains **98.0 / 94.0 / 99.9 %** of PJM's entire hydro volume deficit and
predicted post-delta gaps of −0.017 / −0.037 / −0.001 TWh. The solve returned
**−0.017 / −0.037 / −0.001**. Delivery is **100.0 %** of the re-allocated energy
in all three years — the keeper was already at its deliverable ceiling and the
only thing withholding the energy was a budget the LP's own `pmax` bound
silently clipped.

**Scorecard — no pre-registered kill fired.** P1 PASS 3/3; P2/K5 PASS (0 MWh over
bound, month totals to 1.4e-9, plant count unchanged); P3 PASS (worst D-2 move
0.33 pp of a 2 pp bound, hydro forced share stays 0.0 %, D-4 unchanged); K1 C3a
−0.10/+0.10/+0.09 pp of a 0.75 pp bound; **K2 volume collateral IMPROVES every
year, −0.534/−0.145/−1.120 TWh**; K3 CO2 +0.14/+0.10/−0.16 pp; K4 rubric
identical in both arms. Zero DOF — the bound is EIA-860 nameplate × the calendar.

**Basis: clean once attributed.** Arm A does not reproduce the committed keeper
bundle (max |Δ| 2453/3459/3330 MW) but IS **byte-identical (0.000000 MW, every
class, every hour, all three years) to `pjm132_control_A`** — the previous
session's post-guard control. The difference is entirely the documented
pre-guard → corrected-outage-envelope change, predates this session, and is
carried identically by both arms. Independent confirmation: arm A's 2025 λ is
**40.93**, the guard-corrected A1 exactly.

**Two honest notes.** (i) The prereg predicted K2 "≈ neutral in 2023/2024"; the
measured result improved in all three years — the prediction was too pessimistic
and is recorded as such. (ii) The freed water spreads almost exactly flat
(window shares within ~5 pp of hours-shares, mild overnight tilt) — the same
signature caiso-130 measured, reproduced on a keeper with none of CAISO's
evening-λ pin. Not gated here, by pre-registration: PJM files no `NG: PS`, so
its `NG: WAT` comparator is pumped-storage-contaminated.

**Disclosed, not fixed, not bundled:** PJM's pinned hydro level is the
PS-inclusive `NG: WAT`, **+6.5 to +7.0 TWh/yr above** the EIA-923 prime-mover-`HY`
budget, asking a 3.3 GW fleet for energy the model's separate 5.0 GW PS fleet
already generates. Rule 14 reading: the clip was deleting that phantom energy
before the LP saw it; removing it EXPOSES the pin rather than causing it. Affects
every hydro ISO whose BA omits `NG: PS` (PJM/CAISO/NYISO/MISO; ISNE has it).
Filed as an ask.

**Disposition — NOT promoted, promotion not requested.** Arm B strictly dominates
arm A: identical recipe plus one flag, no criterion regresses, volume error
improves in all three years. What blocks a clean promotion is upstream: both arms
score NOT-YET on the corrected envelope while the designated keeper is registered
CALIBRATED on the pre-guard envelope, so arm B is comparable only to the
same-recipe control. That envelope/keeper-designation decision is **owner-only**
and was already open before this session (miso-88 precedent, FINDING-pjm132 §5).
Promoting arm B effectively decides it — which is why this session does not
self-promote.

**Cross-ISO reading:** caiso-130 armed this flag on the ISO with the *smallest*
exposure (0.12–1.50 %) and was killed by an overnight gate driven by CAISO's own
storage-arbitrage λ pin. PJM carries 3.6–6.7 % and passes everything. The
mechanism is sound; the caiso-130 kill was a property of CAISO's evening λ
surface, not of the nameplate bound. MISO (0.87–2.12 %) and NEISO (0.28–0.91 %)
remain untested, each its own A/B and its own owner act.

**Also filed this session:** `ASK-pjm134-dominion-zonal-inversion-2026-07-27.md`
— the owner-raised Dominion CC_REGULAR / CT_PEAKER underrun, measured from
committed payloads only. It is an **allocation inversion**, not a level error
(Dominion CT runs 5.3 % model CF vs 19.5 % actual while AEP_Ohio runs 19.5 % vs
10.1 %, on capacity that is present and correctly zoned), and the pjm-132
within-season delta moves Dominion by **0.00 TWh** — the offer-surface family
re-conditions price ISO-wide and cannot reach which zone clears.

**Environment (provisioning, not methodology).** A PJM per-plant year-solve peaks
at **14.80/15.21/15.21 GB** on a 15 GB box; an attempt was OOM-killed in 2024 at
that peak. Resident-after-release is flat at ~1.0 GB, so there is **no leak** —
and splitting years into separate invocations does **not** help, because the peak
is intra-year (rule 16 is not in tension with the memory limit). Resolved with
swap. The container also shipped an empty `data/clean` tree (48 datatypes
regenerated) and an empty `data/raw/pjm-da-virtuals` (36 months fetched).

**Next number: pjm-134.**

**PROMOTED 2026-07-27 (owner, in-session).** PJM keeper is now
`2026-07-27-pjm-133-nameplate`, superseding `2026-07-26-pjm-129-meritguard-a1`.
The owner's criterion — *"if structural integrity improves but gates regress
that may still be a keeper"* — is met a fortiori: **nothing regresses at all**.

**The blocker recorded above was resolved by main, not by this session.** While
these arms solved, main designated `pjm-129-meritguard-a1` — the pjm-121 recipe
replayed VERBATIM on the guard-corrected envelope, NOT-YET 7/10 — as the PJM
keeper, deciding the corrected-envelope question. So the A/B is like-for-like
against the designated keeper after all, and **arm A reproduces
`pjm129_meritguard_a1` byte-identically: 0.000000 MW, all 19 classes, every
hour, all three years.** The determination is unchanged (NOT-YET, C1/C3a/C3c
FAIL, exactly as pjm-129 reads on the same envelope); what changes is that a
real physical defect closes with zero DOF and total class-volume error improves
in all three years.

`calibration_attestation.json` written for arm B with a 14-entry DOF ledger
(rule 23); the new entry is measured-external with ZERO solves added to the
tuning lineage. C6 governance PASSES. `audit_keepers.py --iso PJM` PASS,
0 failures / 0 warnings.

---

## pjm-134 — the Dominion CT/CC zonal inversion: C1 refuted, C2 fires, and the AP-South joint cut is INERT

**Runs:** `2026-07-28-pjm-134-control` (arm A) / `2026-07-28-pjm-134-apsouth`
(arm B), 2023+2024+2025 each in one invocation (rule 16). Gates:
`PREREG-pjm134-apsouth-joint-cut-2026-07-27.md`, committed at `b9d2b4d` and
merged to main **before either arm solved**. Write-up:
`FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md`. Probes:
`_pjm134_c1_zonal_gas_basis.py`, `_pjm134_c2_dominion_interface.py`,
`_pjm134_apsouth_ab.py`.

**The measurement (no LP).** ASK-pjm134 §4's two candidates were separated:

- **C1 zonal gas basis — REFUTED.** Against EIA-923 Sch.2 plant receipts
  volume-weighted over the plants `build_zone_lookup("PJM")` itself places in
  each zone, the model's Dominion−AEP_Ohio spread (+1.007/+0.578/+0.694 $/MMBtu)
  is *smaller* than measured (+1.231/+0.649/+0.643) in 2023/24 and within $0.05
  in 2025. No sign inversion in any year. The basis is measured-faithful.
- **C2 transfer capability — FIRES.** The keeper's PJM is a copper-plate:
  Dominion clears at the identical dual to all three neighbours in **100.0 % of
  26,280 hours**; all eight zones plus the import node share one price in
  95.5/97.3/96.2 % of hours; EMAAC (`pjm_east_interface_cut`) is the only
  internal cut that ever binds. PJM's own DA congestion separates DOM from
  AEP-DAYTON by >$1 in 59.2/49.5/62.7 % of hours (DOM dearer in 55.9/42.8/49.9 %,
  mean +$2.17/+$2.53/+$4.41). Misallocated energy: Dominion fossil
  −20.0/−19.8/−12.1 TWh while 2025's ISO-wide fossil balance is **+0.2 TWh** —
  right fuel, wrong states.

**Together these are one result.** The gas basis is *correct*, and Dominion
really does pay $0.6–1.2/MMBtu more ($6–13/MWh on a peaker). Reality runs its
CTs at 19.5 % CF anyway because the network decides. With no congestion at all,
the correct basis alone decides the allocation.

**The delta and its verdict.** `pjm_apsouth_interface_cut` (new, default off,
zero DOF): one one-sided aggregate group capping
Flow(West_APS→SWMAAC)+Flow(West_APS→Dominion) at the measured AP-South hourly
limit — the joint-cut twin of the EAST cut, replacing (rule 19) the misalignment
`PJM_INTERFACE_LINK_MAP` already flags in its own note.

**Every pre-registered gate PASSES** — P1 engagement (0.03/0.09/0.62 % of hours
vs arm A's 0.00 %), P2 direction (Dominion the dearer side in **100.0 %** of
separated hours, floor 2/3), P3, K1 (rubric criteria byte-identical), K2
(slack/dump 0/0), K4 (determination identical NOT-YET), K5 (**arm A reproduces
`pjm132_control_A` byte-identically, 0.000000000 MW, all 19 classes, every hour,
all three years**).

**And the correction is real:** arm A's joint AP-South flow **violates PJM's
published cap in 11.6/11.7/20.4 % of hours by up to 3,000 MW**; arm B enforces it
to 0.00 %.

**Determination: INERT on the defect** (the PREREG §4 pre-registered outcome).
Dominion CT_PEAKER 0.68→0.68 / 1.25→1.25 / 2.46→2.47 TWh against gaps of
−6.7/−7.4/−7.2; largest zonal move anywhere **0.01 TWh**. Per §4's no-feedback
ceiling **no scale factor was applied to the published series, and none may be.**

**WHY — the finding that matters.** The mesh re-routes. Dominion's supply
decomposition (arm A 2025, from `flows.parquet`): **AEP_Ohio +34.0 TWh/yr,
EXTERNAL star node +19.9, West_APS +9.5, export to SWMAAC −28.7, net +34.6.**
AP-South carries the *smallest* inbound path. And the network is degenerate —
SWMAAC↔Dominion sits at its 3,500 MW bound in 80.1 % of hours with a price
difference of exactly 0.0000 — so tightening any one internal path is re-routed
at zero cost.

**Next charter (filed, NOT built):** the **external star-node import into
Dominion**, +19.9 TWh/yr — larger than the zone's entire 12.1 TWh fossil deficit,
and governed by the seam/import-envelope family
(`pjm_seam_flow_limit`, `priced_interchange`, `PJM_EXTERNAL_FLOW_PERCENTILE`),
NOT by `PJM_INTERFACE_LINK_MAP`. No internal interface cut can touch it.

**Solve cost (recorded for whoever carries this):** arm B ran **~2.5× slower**
than arm A (2023 P0 1,902 s vs 765 s; whole arm 2 h 07 vs 59 m) — the added 8,760
interface rows cut across the degenerate face. That cost recurs on every PJM
solve and is the main argument against carrying a flag that moves 0.01 TWh.

**Keeper: NOT recommended, and not self-promoted** (owner-only act). Matrix cell
`pjm_apsouth_cut` = **I** (inert), flag stays default-off.

**Next number: pjm-135.**

---

## pjm-135 — the external star node: the border decomposition is degenerate, the NET POSITION is the defect, and the joint cut flips C1+C3a

**Runs:** `2026-07-28-pjm-135-control` (arm A) / `2026-07-28-pjm-135-netpos`
(arm B) on the pjm-121 recipe, plus `pjm135_netpos_keeper_C` re-based onto the
pjm-133 keeper recipe. All 2023+2024+2025 in one invocation (rule 16). Gates:
`PREREG-pjm135-star-node-net-position-cut-2026-07-28.md`, committed and pushed
**before any arm solved**. Write-up:
`FINDING-pjm135-star-node-import-2026-07-28.md`. Probes:
`_pjm135_star_node_import.py`, `_pjm135_star_node_net_position.py`,
`_pjm135_star_flow_utilisation.py`, `_pjm135_netpos_ab.py`.

**The measurement (no LP).** FINDING-pjm134 §7 handed this session the
`PJM_external → PJM_Dominion` star link (+2,266 MW / +19.9 TWh/yr). Four
measurements, all on committed data:

- **M1 border attribution — the map is SOUND, the band is not.** All 22 ties in
  the file match `_PJM_TIE_ZONE` (the default never fires) and Dominion's four
  are genuinely Carolinas/TVA-facing. Dominion measurably net-imports
  **11.6/12.2/11.3 TWh**, in 86–93 % of hours. The band it is handed is
  **1.71/1.78/1.92×** that.
- **M2 shape — a capability envelope used as an energy schedule.** The band is a
  281–286-value (month × hod) p95 climatology; its R² against the measured
  hourly import is **negative every year**. From arm A's flows: the link sits
  **AT** the band in **92.6/93.3/76.5 %** of hours, and the export side rides
  its bands too (ComEd at its export band in 98.3–98.8 %).
- **M3 degeneracy — the charter's own number is a vertex artifact.**
  `PJM_external` clears at the **identical dual to every PJM zone in 100.00 % of
  hours**, max |Δ| = **0.0000 $/MWh**. The border decomposition is not a physical
  statement, so per-border re-attribution is provably re-routable. **That lever
  is dead on arrival and was not pursued.**
- **M4 net position — the real, non-degenerate defect.** `PJM_external` carries
  zero demand, so the `import` class **is** `Σ_z Flow(ext→z)` (verified against
  flows to **0.0005 MW**). It reads **−28.89/−21.86/−25.80 TWh** against a
  measured **−39.98/−32.83/−32.93** — the star node supplies PJM with
  **7.1–11.1 TWh/yr the real seam did not** — with a **negative** hourly R² and
  ~10 % of hours more import-heavy than PJM has *ever* been in that bucket.
  Three star-node mechanisms exist and **every one is marginal**; nothing
  constrains the total.

**The delta.** `pjm_external_net_position_cut` (new, default off, **zero DOF**):
one one-sided aggregate row per hour caps `Σ_z Flow(PJM_external → z)` at the
measured (month × hod) p95 net-position envelope — the same tie-line file, the
same `PJM_EXTERNAL_FLOW_PERCENTILE`, the same bucketing, via the same
`_build_joint_interface_cut` core as the EAST and AP-South cuts. Rule 19: it
REPLACES the sum-of-marginals ceiling on the aggregate question (five marginal
p95s summed as though joint — 4,235/5,140/5,358 MW against a joint p95 of
3,309/3,855/3,996; the per-neighbor bands compound it by double-counting
Dominion and triple-counting AEP_Ohio).

**Every pre-registered gate PASSES.** P1 enforcement 23.48/21.22/18.56 % of
hours above the envelope → **0.00 %** (max excess on the constrained flows
**0.000000 MW**); P2 direction toward measured, never past it; **K2 zero slack
and zero dump in BOTH arms, ALL years** — the pre-registered principal risk,
since the cap binds in **93.2/92.1/96.6 %** of top-1 % load hours; K5 arm A
reproduces `pjm134_control_A` **byte-identically** (0.000000000 MW). Realised
net move −1.52/−1.80/−1.73 TWh against −1.54/−1.80/−1.73 **pre-computed before
the solve**. **Solve cost: none** — arm B ran **33.6 min vs arm A's 40**.

**And the rubric improves, which the gate table could not anticipate:** C1
**FAIL → PASS** (all 16/16, free 12/12) and C3a **FAIL → PASS**, with C3c
**byte-identical** — target grade 5 → 7, fails 3 → 1.

**INERT on the chartered defect, as PREREG §4 pre-registered.** Dominion
CT_PEAKER +0.024/+0.038/+0.063 TWh against gaps of −6.7/−7.4/−7.2; only ~15 % of
the ISO-wide CC gain lands in Dominion, the rest going west exactly as M3's
zero-dual copper-plate predicts. **The zonal inversion stays OPEN.**

**PROMOTED 2026-07-28 (owner, in-session).** PJM keeper is now
`2026-07-28-pjm-135-netpos-keeper` (`pjm135_netpos_keeper_C` — the pjm-133
recipe carried VERBATIM plus the single flag; hydro budget preserved to the GWh
at 15.451/15.819/15.506 TWh), superseding `2026-07-27-pjm-133-nameplate`. The
owner's criterion — *"if structural integrity improves but gates regress that
may still be a keeper"* — is met a fortiori: **nothing regresses and two
load-bearing criteria improve.** C1 **FAIL → PASS** (2023 CC_REGULAR
−8.45 → **−7.89** TWh against ±8.00; all 16/16, free 12/12), C3a **FAIL → PASS**,
C3c **byte-identical**; fails **3 → 1**, with the C3c scarcity tail now the
**sole** failing criterion. C6 governance PASSES on a 15-entry DOF ledger
(n_residual unchanged at 6). `audit_keepers.py --iso PJM`: **PASS, 0 failures,
0 warnings.** Matrix cell `pjm_external_net_position_cut` = **K**.

**Two caveats carried, not buried.** (a) C1's flip is **thin** — −7.89 inside a
±8.00 band, 1.4 % of margin — and a future delta could flip it back. (b) The
delta is **INERT on the Dominion inversion it was chartered against**; the
C1/C3a gain is an ISO-wide level effect, not a zonal-allocation fix.

**Next number: pjm-136.** The Dominion zonal inversion remains the open defect,
but the per-border lever is now **CLOSED by measurement** (§7 DO-NOT-REDO): the
star node is price-tied to every PJM zone in 100.00 % of hours at max |Δ| =
0.0000 $/MWh, so no re-attribution can bind. A successor needs a mechanism that
changes the *dual structure* — real internal congestion — not another flow cap.

---

## pjm-136 — the copper-plate was the defect: PJM's internal network is LOSSLESS, the Dominion links are bound-but-priceless, and the measured loss surface breaks the single dual, moves the zonal allocation for the first time, and flips C3c

**Runs:** `2026-07-28-pjm-136-control` (arm A) / `2026-07-28-pjm-136-lossurf`
(arm B), both on the `2026-07-28-pjm-135-netpos-keeper` recipe, all three years
in one invocation (rule 16), arms sequential (rule 12). Gates:
`PREREG-pjm136-zonal-loss-surface-2026-07-28.md`, committed and pushed **before
either arm solved**. Write-up:
`FINDING-pjm136-zonal-dual-structure-2026-07-28.md`. Probes:
`_pjm136_zonal_dual_structure.py`, `_pjm136_model_vs_measured_zonal.py`,
`_pjm136_lossurf_ab.py`.

**The measurement (no LP).** pjm-135 §7 handed this session a closed per-border
lever and the instruction to find a mechanism that changes the *dual structure*.

- **M1a/M1b — the model has NO dual structure on any Dominion boundary.** The
  keeper separates on `AEP_Ohio→Dominion`, `West_APS→Dominion` and
  `SWMAAC→Dominion` in **0.0 % of all 26,280 hours**; all eight zones sit at ONE
  dual in **96.4/97.6/97.0 %**. PJM's own DA prices separate on every one of
  those links in **100.0 %** (mean max zonal spread $16.83/$18.06/$29.64 vs the
  model's $0.29/$0.63/$0.97).
- **M1a flow space — bound-but-priceless, NOT slack.** `AEP_Ohio→Dominion` is
  **pinned at its bound in 84.4/90.7 %** of hours at a shadow price of **exactly
  0.000**; `SWMAAC→Dominion` 68.5/80.5 %, same. Exactly one internal link ever
  prices (`ComEd→AEP_Ohio`, 0.35 % of 2025). Tightening a limit that is already
  ridden and still prices at zero only moves the simplex to another vertex on
  the same zero-cost face — which is precisely the re-routing pjm-134 observed
  and pjm-135 measured. **The degeneracy IS the disease.**
- **M2 — losses separate duals with nothing binding.** The loss component
  carries **20/24/23 %** of the measured DOM-vs-AEP gap and exceeds $1 on its
  own in **24/33/54 %** of hours, on a **sign-stable** gradient (Dominion
  positive 12/12 months, SWMAAC 12/12, ComEd negative 12/12) — the contrast with
  the cancelling MISO pair-year that tripped miso-76's R2.
- **M3 — the 8-zone reduction can carry it.** Intra-zone hub spread inside
  ComEd/AEP_Ohio is $0.25–$1.70 against an inter-zone DOM-vs-AEP $3.02/$3.88/
  $6.57. (EMAAC hides $4.3–$5.0 internally — disclosed, separate, not this
  defect.)

**Intake + derive (rule 14 / rule 23).** PJM's `type = ZONE` LMP components for
all 21 transmission zones, 2023-2025 (bulk gitignored under the DataMiner2
non-member restriction with a committed sha256 manifest; only the dimensionless
surface is committed). `dev_z,m = Σ MLC_z / Σ MEC`, DA basis, load-weighted onto
the eight model zones through the canonical `_PJM_LOAD_ZONE_GROUPS` crosswalk —
**every model zone real, NONE interpolated**. Keyed on the UTC interval, not the
EPT stamp: the DST fall-back hour shares one EPT label and keying on it merges
two market intervals (it surfaces as a $3.84/MWh break in the MEC identity,
which is how it was found; on UTC the identity holds at exactly 0.000000).
Offline acceptance **12/12 pair-years in [0.5×, 1.5×]** (0.95–1.07) before any
solve.

**The delta.** `pjm_zonal_loss_surface` (new, default off, **zero DOF** —
`n_residual` unchanged at 6). Each internal PJM link splits into a one-way pair
whose receiving-end energy-balance coefficient is `1 − eps(month)`,
`eps_(x→y),m = max(0, (dev_y−dev_x)/(1+dev_y))`. Losses consume MWh; prices stay
LP duals (rule 4). Rule 19: the **loss** component only — congestion stays with
the measured interface limits and the joint EAST/AP-South/net-position cuts, and
the external star node is deliberately **not** lossy (a fictitious pricing node
has no published deviation; inventing one would be a fitted scalar).

**RESULT.**

- **P2 — the copper-plate does not shrink, it DISAPPEARS**: all-8-zones-at-one-
  dual **96.4/97.6/97.0 % → 0.00 %** in every year, against PJM's measured 0.0 %.
- **P1** reproduces the measured loss component in band on **31/33** link-years
  and on **all nine** Dominion-facing ones.
- **K2** zero slack, zero dump, both arms, all years — losses consume
  **1.52/1.72/2.26 TWh/yr** and the fleet covered every megawatt.
- **K5** arm A byte-identical to the committed keeper (**0.000000000 MW** over
  166,440 class-hours per year). **K6** solve cost **+1.8 %** overall (2025 was
  *faster* with the mechanism on).
- **C3c FAIL → PASS** — the sole blocker since pjm-133: 2024 **7 h → 10 h** vs
  RT 18 h (0.39× → 0.56×), 2025 **28 h → 32 h** vs RT 59 h (0.47× → 0.54×).
  Arm B's determination is **CALIBRATED**; arm A's is NOT-YET.
- **THE ZONAL RESULT — the first lever in the lineage to move it.** Dominion
  CC_REGULAR **+0.537/+1.410/+1.764 TWh**, which is **115/82/78 %** of the
  ISO-wide CC_REGULAR move (pjm-135 landed ~15 % in Dominion), with **ComEd —
  the measured upstream generation pocket — giving up −0.978/−1.521/−1.512**.
  Dominion CT_PEAKER **+0.015/+0.096/+0.411** while the ISO-wide CT total
  *falls* in 2024-25: pure reallocation toward the deficit zone.

**CARRIED CAVEATS, none buried.** (a) **C3c's flip is THIN** — the floor is 0.5×,
so 2024 clears by **1 hour** and 2025 by **2.5 hours**. (b) **P1 as written is an
all-33 gate and misses 2** (`AEP_Ohio↔ATSI` 2023, ratio −0.22 on tiny
quantities; `West_APS→Central_PA` 2025 at 0.50×, the band edge). (c) **K1's sign
clause fails 1 of 9 Dominion link-years** — `SWMAAC→Dominion` 2025, the exact
case PREREG §3 pre-declared *with its numbers* because congestion offsets loss
there, but the sign clause did not carve it out; recorded as a fail of the
clause as written. (d) **Dominion CC_REGULAR 2025 overshoots**: −0.907 → +0.857
vs actual — |error| improves by a hair but the sign flips. (e) **The CT_PEAKER
leg is still ~94 % open**, exactly as PREREG §4 pre-registered
INERT-on-the-CT-leg.

**Rule-22 leave-one-year-out clean:** same-signed in every year independently
(copper-plate breaks in all three; Dominion CC_REGULAR and CT_PEAKER rise in all
three), and the C3c flip is carried by **two different years** (2024 and 2025
each flip on their own), so it rests on neither alone.

**PROMOTED 2026-07-28 (owner, in-session).** PJM keeper is now
`2026-07-28-pjm-136-lossurf` (bundle `pjm136_lossurf_B` — the pjm-135 recipe
carried VERBATIM plus the single flag, with pjm-135's own net-position cut and
pjm-133's hydro budget preserved beneath it), superseding
`2026-07-28-pjm-135-netpos-keeper`. **This is the first PJM keeper to carry a
`CALIBRATED` determination — no failing criterion remains.** `build_status.py
--iso PJM` rebuilt `status/PJM.js` (PJM:CALIBRATED); `audit_keepers.py --iso
PJM`: **PASS, 0 failures, 0 warnings**. Matrix cell `zonal_loss_surface` PJM =
**K** and the matrix header re-stamped (MISO stays **R** — rule 25, no verdict
crosses the boundary in either direction). PREREG §4's no-feedback ceiling was
honoured: no multiplier, percentile, haircut, blend, scale, floor, cap or
scarcity exemption was applied to the surface, and none may be.

**The five caveats above travel WITH the promotion**, into the keeper shard's
`promotion_note` and `note` rather than being dropped at the moment of
acceptance — in particular that C3c now passes by **1 hour** (2024) and **2.5
hours** (2025) against a 0.5× floor, that Dominion CC_REGULAR 2025 now
*overshoots* where every prior keeper undershot, and that the CT_PEAKER leg is
~94 % open.

**Next number: pjm-137.** The Dominion CT_PEAKER leg is the open defect; the
network now has a real dual structure to work against, and the remaining
76–80 % of the measured DOM-vs-AEP separation is **congestion**, which no
mechanism in the model currently produces on that boundary.

## pjm-137 — the Dominion congestion is SUB-ZONAL: PJM's own binding-constraint record puts 3–6 % of its DA congestion rent on zonal-scale interfaces and 0.04–0.24 % on AEP-DOM, the DOM-separation hours are driven by Loudoun facilities with BOTH ends inside `PJM_Dominion`, and there is more price separation INSIDE the Dominion zone than across the DOM–AEP boundary. The chartered defect was also mis-sized ~1.9×. `measured_ct_heat_rates` promoted.

**Runs:** `2026-07-29-pjm-137-control` (arm A) / `2026-07-29-pjm-137-ctheatrate`
(arm B), both on the `2026-07-28-pjm-136-lossurf` recipe, all three years in one
invocation (rule 16), arms sequential (rule 12). Gates:
`PREREG-pjm137-measured-ct-heat-rates-2026-07-29.md`, committed and pushed
**before either arm solved** (including its own §2a correction). Write-up:
`FINDING-pjm137-dominion-congestion-is-subzonal-2026-07-29.md`. Probes:
`_pjm137_dominion_ct_congestion.py`, `_pjm137_intrazonal_ehv_spread.py`,
`_pjm137_ctheatrate_ab.py`.

**Two new public intakes** (gitignored bulk, committed README + sha256 manifest):
`data/raw/pjm-binding-constraints/` (DataMiner2 `da_marginal_value` — PJM's OWN
binding day-ahead constraints with monitored facility, contingency and **shadow
price**, the MISO `bc_HIST` analogue and directly comparable to the model's own
transmission duals; 228,795 constraint-hours) and `data/raw/pjm-ehv-lmp/`
(DataMiner2 `da_hrl_lmps` `type = EHV` — 500 kV aggregate-node LMPs, ~135 nodes,
**38 inside DOM alone**; the server-side `zone` filter 400s on archived rows so
the fetcher pulls every zone and filters locally, which is why the measurement
covers all eight model zones).

**THE MEASUREMENT (no LP).** pjm-136 §5 asked a successor to *"make an internal
PJM constraint actually price, or prove it can't."* **It can't.**

- **M1 — the loss surface did exactly what it claimed; the residual is
  congestion.** On the NEW keeper the model separates on `AEP_Ohio→Dominion` in
  **96.1/98.9/96.9 %** of hours (was 0.0 %), reproducing the measured LOSS
  component (−0.54/−1.06/−1.90) and **none** of the measured congestion
  (−3.65/−4.42/**−12.44**).
- **M2 — PJM's congestion is not on the boundaries a zonal model has.** Only
  **6.34/3.06/6.19 %** of the shadow-price record sits on a named zonal-scale
  interface; **80.0–87.8 %** sits on facilities rated **≤ 230 kV** (pooled:
  115–138 kV 54.9 %, 230 kV 23.0 %, 500 kV 4.0 %). **`AEP-DOM` carries
  0.041/0.071/0.236 %.** In the top-decile DOM-separation hours the largest rent
  *lift* is **PLEASNTV TX3 500 kV (+4.98 pp)**, then GOOSECRE TX1 500 kV,
  PLEASNTV-ASHBURN 230 kV, ASHBURN-GOOSECRE 230 kV, BRAMBLET-EVRGREEN — and PJM's
  `/api/v1/pnode` registry returns **`zone = DOM`** for every one, so **both ends
  are inside `PJM_Dominion`**.
- **M3 — the CT leg is a price-formation defect.** The nine-plant / **40-turbine**
  roster (`unitType == 'Combustion turbine'`) runs **68.3/54.4/62.4 %** of hours;
  CT-energy-weighted measured DOM LMP **$50.78/$62.04/$103.41** against the
  model's **$33.06/$35.35/$48.80** — a deficit of **$17.72/$26.69/$54.61**, of
  which measured congestion is **51/46/51 %**. **80 % of 2025's real CT energy is
  produced in hours PJM prices Dominion congestion above $5.**
- **M4 — there is MORE separation inside Dominion than across its boundary.**
  Intra-`PJM_Dominion` EHV dispersion **$6.18/$8.68/$16.78** vs the inter-zonal
  DOM-vs-AEP spread **$4.76/$6.13/$14.42** — ratio **1.30/1.42/1.16×**. Six of
  seven measurable zones are at or above their inter-zonal spread; ComEd
  ($0.65–$1.93) is the exception, which is why pjm-136 §3's hub-based test read
  clean — PJM publishes multiple hubs only inside its two most uniform zones.

**VERDICT: the zonal-congestion route is CLOSED BY MEASUREMENT** — the
ERCOT/MISO `internal_congestion_split` refusal class, established for PJM on
PJM's own published numbers.

**THE DEFECT WAS MIS-SIZED ~1.9×.** Every prior handoff and the keeper note
state the Dominion `CT_PEAKER` actual as 7.38/8.68/9.64 TWh. On the join the
dashboard itself renders, the benchmark says **3.066/4.048/5.218 TWh** — its
Doswell record carries `split: "unit_hourly"` and puts that site's CT share at
1.079 TWh against 4.454 TWh of CC. The quoted figure reproduces exactly as
*whole-plant* net (7.320/8.635/9.632). **The benchmark and dashboard have always
been right; the prose number was computed on the wrong basis** — the same
mixed-facility trap that corrupted this session's own first pre-computation.

**The delta.** `measured_ct_heat_rates` (existing field, first PJM artifact from
the existing frozen derive, **zero DOF**, `n_residual` unchanged at 6). Chartered
under rule 14 `[R-ACCURATE]`, not as a fix for the residual: eGRID publishes ONE
plant-average rate, so Doswell's three peaking turbines carried the **9.027**
average of a site that is six CC blocks, against a **measured 11.350**. 71
plants, **zero excluded** by the physical band, 29 moved > 0.5 MMBtu/MWh, **35
cheaper / 36 dearer** — a measurement, not a multiplier.

**RESULT.**

- **K5** arm A byte-identical to the committed keeper (**0.000000000 MW** over
  166,440 class-hours, each year). **K4** zero slack, zero dump, both arms.
  **K3** zero band exclusions.
- **K1, the C3c standing kill: PASS and UNCHANGED** — model tail-hour counts
  identical at 3/10/32 h. The keeper's thinnest margin was not touched.
- **Both arms CALIBRATED with every criterion passing**; C1 **16/16, free 12/12**
  in both.
- **THE ZONAL RESULT.** Dominion `CT_PEAKER` **0.724→0.721 / 1.380→1.448 /
  2.923→3.162 TWh** while the **ISO-wide class FALLS 2.857/2.635/2.794** — pure
  reallocation toward the deficit zone. Against the benchmark's actual the gap
  goes −2.342→−2.345 / −2.668→−2.600 / −2.295→**−2.056**, closing **10.4 %** of
  the 2025 gap.
- **THE PRE-REGISTRATION WAS REFUTED ON ITS OWN EXPECTED DIRECTION** and is
  recorded as such rather than re-written. PREREG §4 predicted the delta would
  push Dominion the *wrong* way because its zone-average rate rises most
  (+0.634 MMBtu/MWh). It did rise, and Dominion still gained — the mechanism is
  **per plant**: Doswell (+2.324) and Gravel Neck (+3.204) are correctly made
  dearer while Remington (−0.329) and Ladysmith (−0.001) are not.

**CARRIED CAVEATS, none buried.** (a) ISO-wide `CT_PEAKER` volume moves *further*
from its EIA-923 class total in two of three years (|err| 0.75→2.11 in 2023,
0.94→3.57 in 2024) while 2025 improves markedly (6.11→3.32); C1 holds 16/16 so no
band breaks, but the trade is real — `CC_REGULAR` (7.42→6.07, 3.03→1.84) and
`COAL_BIT` (0.87→0.29, 2.15→1.62) both improve as CT energy moves into them.
(b) C8 `CT_PEAKER` forced share rises to **16.3/16.9/17.1 %** (2023 newly above
the 15 % peaker cap), all **GROUNDED** — D-4 clear, profile r 0.923–0.973, CV
ratio 0.703–1.083 — so a clean pass under rule 20, but a shrinking class carrying
a larger forced fraction. (c) The delta does not touch the congestion half of the
price deficit. (d) C3c still passes by ~1 h / ~2.5 h, inherited unchanged.
(e) Dominion `CC_REGULAR` 2025 still overshoots, inherited from pjm-136.

**PROMOTED 2026-07-29 (owner, in-session).** PJM keeper is now
`2026-07-29-pjm-137-ctheatrate` (bundle `pjm137_ctheatrate_B` — the pjm-136
recipe carried VERBATIM plus the single flag), superseding
`2026-07-28-pjm-136-lossurf`. `build_status.py --iso PJM` rebuilt `status/PJM.js`
(PJM:CALIBRATED); `audit_keepers.py --iso PJM`: **PASS, 0 failures, 0 warnings**.
Matrix cell `measured_ct_heat_rates` PJM **U → K** with the header re-stamped and
§5.3 rewritten (NYISO stays K on its own evidence — rule 25, no verdict crosses
the boundary).

**Next number: pjm-138.** The successor's target is the **system-energy-price**
half of the CT-hour deficit — **$8.63/$14.37/$26.88 /MWh** after netting out
measured congestion, with measured DOM MEC at a p50 of $35.94/$41.35/$58.86 in CT
hours against the model's whole Dominion dual at $32.07/$32.28/$42.72. A
`PJM_Dominion` NoVA/Loudoun split is the structurally correct fix for the
congestion half and is **refused until a measured sub-zonal load basis exists**
(PJM's metered-load feed stops at the transmission zone; a sub-zonal share would
be a fitted scalar).

## pjm-138 — the SYSTEM-ENERGY half is mostly the reserve opportunity cost the no-MIP LP cannot price: PJM prices synchronized reserve above zero in 84/97/48 % of ALL hours and the model prices it in 0/2/28 of 8,760, with the requirement, the published two-step ORDC curve and the in-LP co-optimization all already correct and armed. Of the CT-hour deficit, 8/23/22 % is reachable. NO delta chartered, no LP solved, no run registered.

**Runs:** none. This is a measurement session; nothing was solved, nothing was
registered, and the keeper is unchanged at `2026-07-29-pjm-137-ctheatrate`.
Write-up: `FINDING-pjm138-system-energy-is-reserve-opportunity-cost-2026-07-29.md`.
Probes: `_pjm138_mec_gap_shape.py` (M2/D1–D5), `_pjm138_marginal_ownership.py`
(M1 + the G-20b price sizing). Committed inputs only, plus the pjm-136 zonal
LMP-component intake re-fetched by its own committed fetcher.

**THE CHARTER.** pjm-137 closed the CONGESTION half of the Dominion CT-hour
price deficit by measurement and handed the successor the other half: the
system-energy component, which a zonal model *could* in principle produce. The
charter's own discriminator was diffuse (offer-stack level) vs concentrated
(scarcity/reserve).

- **D1 — the split is an exact identity, and both halves are now sized.**
  `measured_DOM_LMP − model_DOM_dual = (measured_MEC − model_load_weighted_dual)
  + (measured_DOM_basis − model_DOM_basis)`, identity residual **0.000000000**
  in every hour of every year. CT-energy-weighted the total deficit is
  **$17.97 / $26.44 / $54.06**, splitting **$8.15 / $12.74 / $24.78** system
  energy and **$9.82 / $13.70 / $29.28** basis. **PJM's `system_energy_price_da`
  is RTO-UNIFORM** (zero spread across all 23 zonal pnodes, every hour), so the
  system-energy half is not a Dominion quantity at all.
- **D2 — it is a DISPERSION defect, not a level one.** Annual load-weighted the
  model reproduces PJM's own MEC to **+$0.47 / +$2.62 / +$8.48**, while running
  **−$4.86…−$5.78 too DEAR** in the slackest net-load decile and
  **+$14.32 / +$21.59 / +$39.92 too CHEAP** in the tightest. Overnight (h01–h04)
  it is $1.6–7.3 too dear; the gap peaks at the morning ramp (h06–h07) and the
  evening peak (h16–h19). CT-weighted, **DJF 2025 is +$46.05** — the winter
  morning ramp is the worst cell in the measurement.
- **D4 — the tail is 3–6× too thin inside PJM's own energy component.** Measured
  MEC exceeds $100 in **29 / 128 / 392** hours; the model's load-weighted system
  price in **3 / 72 / 65**. Above $150: **14 / 26 / 146** vs **0 / 1 / 24**.
- **D5 — and the missing price is the reserve opportunity cost, which PJM
  publishes.** From `data/raw/PJM-AS/da_reserve_market_results_*` (committed):
  synchronized-reserve MCP is above zero in **84.2 / 96.7 / 47.6 %** of hours
  (Primary 45.1 / 64.0 / 30.8 %) at a cover ratio of **1.00–1.11**, while the
  **model's reserve dual is above zero in 0 / 2 / 28 hours of 8,760**. It
  correlates with the model's system-energy gap at **r = +0.788 / +0.604 /
  +0.657**, the top net-load decile carries **26.2 / 26.5 / 35.9 %** of the
  year's reserve price, and in the Dominion CT hours it is
  **$6.71 / $6.65 / $14.18** against a system-energy gap of
  **$8.17 / $12.74 / $24.78** — **82 / 52 / 57 %** of it. The co-optimized LP's
  own optimality conditions make this additive, not analogical: a unit interior
  in both products satisfies `λ = mc + μ`.

- **M1 — and keeper root cause (6) is CLOSED by measurement.** On the current
  keeper's own fleet (rebuilt no-LP through `replay_keeper.build_kwargs` →
  `solve_and_persist` with `run_year` forced to `fleet_only=True`), `COAL` is
  **18.2 / 16.7 / 12.7 %** of the marginal set across all hours and
  **17.6 / 14.4 / 11.1 %** in the $40–150 band — against pjm-122's
  **44–79 %** on the `pjm-121` bundle. `CC_REGULAR` + `CT_PEAKER`, the classes
  the measured DataMiner2 corpus assigns that region, hold
  **68.4 / 72.6 / 75.5 %** of it, and `CT_PEAKER` alone is
  **60.7 / 65.9 / 67.1 %** of the tightest net-load decile. The intervening
  keeper line (the CC mid-curve belt, the net-position cut, the loss surface,
  the measured CT heat rates) is the plausible cause. **Root cause (6) should be
  retired from `keepers/PJM.json`** — a promotion-lane edit this session reports
  rather than performs.
- **M3 — the G-20b guard lead now has a PRICE, which is what its own audit said
  was missing.** Removing capacity from the tightest decile's own offer stack
  (`mc(Q+Δ) − mc(Q)`, no solve) moves the clearing price **+$3.97 / +$8.02 /
  +$14.95** at 3 GW and **+$7.45 / +$12.46 / +$23.36** at 5 GW on the mean —
  **28–59 %** of that decile's system-energy gap, and a LOWER bound (P0
  base-cost stack, no startup markup). Strongly right-skewed (3 GW p50 only
  $1.41 / $2.32 / $3.59). The shelf within $1 of the dual thins
  **2.10 → 1.54 → 1.01 GW**. This raises the lane's **stakes**, not its
  **verdict**: `FINDING-guard-falseneg-audit-2026-07-27`'s D2 population test is
  clean 3/3 for PJM and its D3 exceedance is mostly a window-LENGTH effect, so
  its §7.2 route (a within-window tight-hour treatment memo, owner sign-off, its
  own charter, LOYO within 2023–2025) remains the correct next step and is not
  taken here.

**VERDICT: NOT A MISSING MECHANISM.** The requirement is PJM's own measured
Primary series (`load_pjm_measured_reserve_requirement`, RTO + the nested
Mid-Atlantic/Dominion subzone), validated here against PJM's published
day-ahead requirement to **2–4 %**; the demand curve is PJM's published two-step
ORDC (`pjm_ordc_curve.csv`, m11 §4.3.3, $850/$300, in force since the 2022-10-01
Reserve Price Formation reform); and the in-LP per-generator joint-headroom
co-optimization — whose dual *is* the forgone energy margin by construction — is
armed and is the sole reserve-price owner under rule 19. It clears at $0 anyway
because the model's reserve **supply** is 5–10× the requirement, which pjm-82
already attributed to the **LP-vs-MIP boundary**: with a continuous commitment
variable, fractional online capacity is free, so every idle unit's headroom is
synchronized-reserve-eligible. PJM's market cannot do that, which is exactly why
its cover ratio is 1.0–1.1 and its price is positive in half to almost all
hours. **Under the no-MIP mandate this is a DISCLOSURE, not a defect** — and the
lane was owner-closed 2026-07-11 ("do not re-open reserve-supply probes for PJM
C3c"). Requirement-side dynamic reserves (lever-queue item 9) is adjudicated
**INERT by measurement**; matrix cell `.` → **K**.

**WHAT IS LEFT.** Of the CT-hour deficit, pjm-137 closed **54.6 / 51.8 / 54.2 %**
(intra-zonal congestion) and pjm-138 attributes **37.3 / 25.2 / 26.2 %** to the
reserve opportunity cost. **Only 8.1 / 23.1 / 22.1 % is reachable by any
energy-stack mechanism** — $1.46 / $6.12 / $11.97 /MWh. Crediting the whole
measured reserve price takes the annual load-weighted gap to
**−$2.36 / −$0.08 / +$2.76**, i.e. the energy stack's LEVEL is right and the
residual is shape-only.

**AN HOUR-KEY CORRECTION TO pjm-137, and its size.** That session's measured-side
loader indexes hour-of-year on `datetime_beginning_ept` — Eastern PREVAILING
time — while the model's 8760 index and the CAMPD record are both Eastern
STANDARD, so from March to November the measured series sat one hour ahead of
both. Re-keyed on `datetime_beginning_utc` at UTC−5 the correlation improves
0.704 → **0.745**, 0.732 → **0.764**, 0.772 → **0.823**, and the DST/standard
split is the signature (2025 Apr–Oct 0.7964 → **0.8731**; Jan/Feb/Dec 0.7807 →
0.7867, i.e. unchanged). **pjm-137's headline stands** — its M3 levels move
$0.12–0.38/MWh (total CT-hour deficit 17.586 → 17.968, 26.559 → 26.439,
54.389 → 54.059) and M1/M2/M4 are unaffected — but **no diurnal statistic may be
quoted from `_pjm137_dominion_ct_congestion.py`**.

**NO DELTA CHARTERED, and why.** The charter is explicit that a mechanism is
proposed only after a measurement fires one. The measurement fired at the
reserve lane, and that lane is closed four ways — measured requirement,
published curve, live co-optimization, owner closure — with its residual named
as the no-MIP boundary. Every other lane the shape points at is already
adjudicated: zonal congestion `R` (pjm-137), the measured offer surface as a
dispersion lever `R` (pjm-123/126/127/132), the post-solve ORDC adder `G`,
reserve deliverability scoping `I`. Under rule 1 `[R-STRUCT]` the keeper is
CALIBRATED with every criterion passing and there is no gate to chase; under
rule 28 the adjudicated cells are not re-tested without new evidence, and the
new evidence **confirms** them.

**STANDING KILLS, unchanged because nothing was solved.** C3c still passes by
~1 h (2024: 10 h vs 18 h RT, 0.56×) and ~2.5 h (2025: 32 h vs 59 h, 0.54×)
against a 0.5× floor — still the thinnest margin in the keeper. C8 `CT_PEAKER`
forced share stays 16.3 / 16.9 / 17.1 %, all GROUNDED (D-4 clear, profile
r 0.923–0.973, off-peak CV ratio 0.703–1.083). C1 stays 16/16 free 12/12; ISO
`CT_PEAKER` |err| stays 2.11 / 3.57 / 3.32 TWh.

**Next number: pjm-139.** The named lever is **`gas_daily_shape`** (**U**,
measured, mean-preserving, zero new DOF, never probed on PJM): the largest
single cell in this measurement is the winter morning ramp, and
`DIAGNOSIS-pjm-dof-scarcity-tail` §B.4.1 named that mechanism for exactly that
phenomenon — a January merit order priced on a flat monthly gas level cannot
express the measured intra-month cold-snap spike. Second: the **overnight
over-pricing** (h01–h04, $1.6–7.3/MWh too dear, worst in 2023) is the one part
of the dispersion defect the reserve credit does not touch, and nothing in this
lineage has measured what sets the model's overnight price against what set
PJM's.

## pjm-139 — the chartered lever was ALREADY ARMED, and the winter morning ramp is a RAMP-RATE deficit, not a fuel-price one: `gas_daily_shape` is `K` on PJM (live since pjm-107, `run_config.json::scenario_config.gas_daily_shape = True`) and has ZERO intra-day resolution by construction, while the model reproduces only 26/21/18 % of PJM's own DJF morning price ramp because it meets it with cheap STEAM it cannot physically move that fast. `ramp_envelopes` chartered and pre-checked. NO delta armed, no LP solved, no run registered.

**Runs:** none. Measurement session; nothing solved, nothing registered, keeper
unchanged at `2026-07-29-pjm-137-ctheatrate`. Write-up:
`FINDING-pjm139-winter-morning-ramp-is-a-ramp-rate-deficit-2026-07-30.md`.
Pre-registration for the successor, committed before any arm solves:
`PREREG-pjm140-ramp-envelopes-2026-07-30.md`. Probe:
`_pjm139_winter_ramp.py` (W1–W7). Committed inputs only, plus the pjm-136 zonal
LMP-component intake re-fetched by its own committed fetcher.

**THE CHARTER WAS VOID BEFORE IT WAS WRITTEN.** The session was chartered to test
`gas_daily_shape` — described by the handoff, by `DIAGNOSIS-pjm-dof-scarcity-tail`
§B.3/§B.4 and by `mechanism-testing-matrix` §5.3 item 9 as matrix `U`, never
probed on PJM, keeper `False`. All three are false. `pjm137_ctheatrate_B`'s
`run_config.json` records `scenario_config.gas_daily_shape = True` (carried on the
`prb_overrides` channel as `coal_prb_sigmoid_overrides.gas_daily_shape`); the
matrix cell string is `"UKKKKK"` against `isos: ["ERCOT","CAISO","PJM","MISO",
"NYISO","NEISO"]`, so **PJM = `K`** and only ERCOT is `U`; and the mechanism was
probed at **pjm-107** (2026-07-14, leg A of the pjm-107/108/109 measured-tail
cycle), passed every gate, and became the `2026-07-14-pjm-107-gas-daily` keeper.
pjm-107 had also already **inverted** the §B.4 hypothesis the charter rests on —
on the mean-preserving builder, daily gas *removed* spurious winter tail hours
(2025 model tail 17 h → 6 h) because the flat-monthly baseline had been
over-pricing every January day at the elevated monthly mean. The `DIAGNOSIS` text
was never updated and is what the handoff read. Under rule 28 a `K` cell is not
re-tested as untested, and there is no A/B: arm B would be the keeper.

**AND THE MECHANISM COULD NOT HAVE REACHED THIS DEFECT ANYWAY — an all-ISO scope
bound.** `gas_daily_shape_factors` builds one factor per CALENDAR DAY and repeats
it across 24 hours (`hubs.py`, `np.repeat(day_factor, 24)`): max within-day σ
**1.11e-16 / 4.44e-16 / 2.22e-16**, hour-of-day mean profile range **0.000000**,
corr with hour-of-day ~1e-18. It is not inert — the January peak calendar-day
factor is **1.151 / 3.287 / 2.143** with 0/4/4 DJF days above 2× — it simply has
no intra-day resolution. The defect is an intra-day differential: DJF
load-weighted the system-energy gap runs **−7.71 / −2.63 / +3.18** overnight,
**+2.25 / +11.96 / +26.94** at the h06–h07 ramp and **−5.55 / −2.66 / +1.69**
midday, an intra-day swing of **$9.96 / $14.62 / $25.25**. A day-scale lever
cannot move it, and its sign is wrong on the overnight half. The handoff's own M1
confirms it independently: corr(day gas factor, system-energy gap) =
**−0.039 / −0.249 / +0.050** all hours and **−0.030 / −0.359 / +0.078** in DJF —
2024 materially *negative* — and the mean gas factor is **1.000 in every DJF
hour-of-day window**. Recorded on the matrix row as a bound on `gas_daily_shape`
**and** on the still-`U` PJM `winter_citygate_daily`: a daily gas series is
chartered against a winter *level* or a *day*-scale tail, never a diurnal defect,
in any ISO.

**WHAT THE DEFECT IS.** The model's winter price profile is **too flat — trough
too dear, peak too cheap**. PJM's own DJF system energy price rises
**+$15.28 / +$21.63 / +$35.45** from h04 to h07; the model's rises
**+$3.93 / +$4.55 / +$6.51**, i.e. **26 / 21 / 18 %** of it. Whole-day DJF
trough-to-peak: measured **$16.56 / $23.24 / $40.33** against the model's
**$5.23 / $6.22 / $8.34** (**32 / 27 / 21 %**). In 2025 PJM climbs from $48.87 at
h04 to **$84.32** at h07 and back to $54.12 by h09; the model goes $46.68 →
$53.19 and does not even peak at h07. That is why the annual load-weighted level
looks right (+$0.47/+$2.62/+$8.48, pjm-138) while the shape does not. Decomposed
on pjm-138's identity, DJF h06–h07 CT-weighted the deficit is
**$23.99 / $85.33 / $114.43** — basis **$13.86 / $37.55 / $43.84** (pjm-137
closed), measured Sync MCP **$6.19 / $17.30 / $30.48** (pjm-138 closed), leaving
a reachable residual of **$3.93 / $30.48 / $40.11** (load-weighted after the
reserve credit: **−$0.37 / +$5.55 / +$13.44**, so 2023 is fully explained and
2024–25 are not).

**THE ROOT CAUSE, MEASURED.** The keeper runs **`ramp_limits = False`** — the LP
carries no intertemporal coupling on the thermal fleet at all, so every hour is an
independent economic dispatch and the morning ramp is a free slide up the merit
order. DJF h01–h04 → h06–h07 mean rise, model against the benchmark's own
per-plant CAMPD record: **ST +2.42/+2.73/+2.57 GW against actual
+1.33/+1.13/+0.97** (the model ramps steam **1.8× / 2.4× / 2.6×** harder than the
real fleet) while **CT +0.66/+1.36/+2.08 against actual +1.14/+1.79/+2.50** (only
**58 / 76 / 83 %** as hard). The model meets the winter morning ramp with the
cheapest thing on the stack — coal and steam it cannot physically move that fast —
instead of the dearest thing PJM actually starts. A cheap marginal unit prints a
flat price. It also predicts the keeper's standing C1 note, where ISO-wide
`CT_PEAKER` runs 2.11/3.57/3.32 TWh short while `COAL_BIT`/`CC_REGULAR` improve.

**THE SUCCESSOR IS CHARTERED AND PRE-CHECKED (no LP).** `ramp_envelopes`
(`ScenarioConfig.ramp_limits` + the frozen `derive_campd_ramp_envelopes.py`,
CAMPD-measured max observed 1-h move per plant-family, **zero fitted DOF**, matrix
PJM `U`, armed in no keeper in any ISO). Pre-check: at the p99 1-h up-move as a
fraction of each side's own fleet peak, model ÷ actual = **CC 1.42/1.72/1.53,
CT 1.38/1.70/1.52, ST 1.61/1.62/1.50** — the model out-ramps the real fleet in
every family and every year, and because the aggregate is the sum of the parts,
aggregate excess **proves** per-plant rows would bind. The test is one-sided and
is reported as such: it can prove the mechanism FIRES, never that it is inert.
ERCOT's `R` and CAISO's `I` were reached on different defects and do not transfer
(rule 25). Not armed here: the PJM artifact has never been derived, and the LP
memory cost of the extra rows is unquantified on a 15 GB box — PREREG §7 requires
a one-year solve to measure the peak before a three-year arm.

**pjm-138's queue item 8 is WITHDRAWN on a size measurement.**
`st_gas_mustrun_p25_level` was promoted by pjm-138 as the overnight-over-pricing
lever. `ST_GAS` carries **0.9 / — / 1.9 %** of the keeper's overnight (h01–h04)
thermal energy (0.44 / 1.04 GW) at a night/peak ratio of **0.22 / 0.35** and cv
**1.18 / 1.00** — a small peak-following class, not an overnight-floored one —
against `CC_REGULAR` **68.9 / — / 65.7 %** and `COAL_BIT` **22.5 / — / 25.6 %**.
Its keeper forcing mechanism is also `st_netload_drag` (D-2: 54.7/51.3/42.5 % of
class), not the "six overnight floor limbs" the item describes (the MISO form).
The overnight defect itself is measured and re-characterised: **not** a
floor-pinning artifact (the model prints 872/825/951 distinct overnight price
levels at a 0.7–0.9 % modal share) but a **bottom-of-distribution level miss** —
model p05 **$21.22 / $20.15 / $26.35** against PJM's **$13.32 / $11.44 / $17.02**,
with PJM's MEC below the model's in **97.6 / 93.9 / 84.3 %** of overnight hours.
Which *tranche* of CC/COAL sets it is still unmeasured; the probe carries the
census as `--with-fleet` (W6), unrun because the container's `data/clean/`
regeneration had not completed.

**Record corrections (prose only, no solve affected).**
`DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3 rows for `gas_daily_shape` and
the `CC_LIKE` leg restated from "proposed" to LIVE with the keeper's own
`run_config` values cited (`pjm_offer_midcurve_segments = ["LONG_RUN","CC_LIKE"]`);
§B.4 item 1 struck and replaced with the three-way closure; §B.4's closing
paragraph stamped with the pjm-107/108 OUTCOME. `mechanism-testing-matrix.md`
§5.3: item 9 struck with the reason recorded rather than deleted, item 10 given
the same resolution bound, item 8's overnight motivation withdrawn.
`mechanism-matrix.js` header re-stamped; `gas_daily_shape`,
`winter_citygate_daily` and `ramp_envelopes` notes updated (the last gaining a `P`
evidence key). **No cell verdict moves** — nothing was armed and nothing solved.
`check_mechanism_matrix.py` PASS.

**Holdouts / governance.** No LP solved, so no `--year` was passed at all; no
out-of-training year touched (rule 22). No offer curve, sigmoid, floor, derive
value or ORDC parameter changed (rules 13/21/23/26). No dashboard change — no run
was produced (rule 15 is satisfied vacuously, the pjm-138 precedent). Keeper
pointer untouched; `keepers/PJM.json` NOT edited, so pjm-138's two owner-lane
items are still pending and pjm-139 adds a third: root cause (3)'s reachable share
is **concentrated in the winter morning ramp**, not spread across CT hours.

---

## 2026-07-30 — pjm-140: `ramp_envelopes` ARMED, A/B'd and PROMOTED. The measured envelope removes **85–91 % of the keeper's physically infeasible hourly ramping** (~0.5 TWh/yr) and moves the chartered winter-morning price by **+$0.03–0.07/MWh**. Keeper `2026-07-29-pjm-137-ctheatrate` → **`2026-07-30-pjm-140-rampenv`**.

**Two arms, all three years each, arms sequential (rule 12), years sequential
within each (rule 16).** `2026-07-30-pjm-140-control` (arm A, no delta) and
`2026-07-30-pjm-140-rampenv` (arm B, `ramp_limits` False → True). Both
**CALIBRATED**, every criterion PASS. Arm A reproduces the superseded keeper
**BYTE-IDENTICALLY** — `0.000000000` MW over **166,440** class-hours in each of
2023/2024/2025 — so the single delta is provably isolated (PREREG K5).

**The artifact.** `derive_campd_ramp_envelopes.py --iso PJM --years 2023 2024 2025`
run for PJM for the **first time** — the existing frozen derive for a new ISO, the
pjm-137 pattern, **not** a re-derivation against a residual (rule 23). 209 rows,
145 well-observed plant-family groups, 61 sparse rows the loader never reads, 3
`class_fraction` rows (CC 0.4435/0.5801, CT 0.7606/0.7535, ST 0.3152/0.4365; the
loader applies CC/ST only — CT gets no class fallback).

**Coverage (K7 PASS).** The loader puts a **live envelope on 194 of 323**
(plant, family) groups = **124.1 GW = 90.1 %** of ramp-eligible thermal capacity
(56.7 % of all capacity). Only **6 groups / 664 MW** prune as non-binding (2 CC,
4 CT); **123 CT groups / 12.9 GW** get no row at all — bang-bang is the measured
norm, and there is no class-name gate anywhere (rule 18). Live up-envelope median
**0.40** of group pmax (p25 0.32 / p75 0.53), down median 0.53. Gross→net rebasis
on **142 measured per-plant** EIA-923-net/CAMPD-gross factors (min 0.8252, median
0.9700, max 0.9968) + **2** cited class defaults (0.9750).

**Memory, measured before the three-year arm (PREREG §7.1).** One-year throwaway
probe peaked **15.32 GB** RSS (~3.1 GB swap) and was deleted un-registered (rule
16 forbids a single-year bundle). Arm A peaked **15.18 GB**, arm B **15.55 GB**.
The rows add **1,699,246** LP rows (each two-sided) and **~23.3 M** nonzeros, so
**swap is now a requirement, not a cushion**, for a PJM per-plant solve on a
15 GB box.

**THE STRUCTURAL RESULT, and it is why this was promoted (D-ENV, new).** With the
flag off the LP asserts every thermal plant can move from any output to any other
in one hour — and the model *acts* on it. Measured on the superseded keeper's own
per-unit dispatch, it crosses the measured envelope in **0.393 / 0.463 / 0.319 %**
of 1,699,246 group-transitions (**149 / 167 / 147** of 194 groups ever cross),
carrying **555,882 / 587,079 / 536,940 MWh a year** of hourly ramping the real PJM
fleet's own measured maxima say those machines could not deliver that fast.
Arming the envelope cuts that to **51,161 / 64,048 / 82,425 MWh** — a
**90.8 / 89.1 / 84.6 %** reduction. Arm B's residual is **by design**: the
availability-edge widening (`RU_eff = RU + max(0, cap[t] − cap[t−1])`) is the
row's only slack, so every remaining crossing sits at a capacity discontinuity.

**THE PRE-REGISTRATION WAS REFUTED ON MAGNITUDE** and is recorded as such rather
than re-written (the pjm-137 precedent). K6, the primary — the DJF h04→h07 model
system-price rise — moves **UP** in all three years, so K6 passes its literal
test: **+3.933→+4.004**, **+4.554→+4.600**, **+6.512→+6.546**. But that is
**+$0.07 / +$0.05 / +$0.03** against PJM's own measured **+$15.28 / +$21.63 /
+$35.45**, i.e. **0.6 / 0.2 / 0.1 %** of the remaining gap, against a
pre-registered claimable ceiling of **+$5.55 / +$13.44** load-weighted for
2024–25. PREREG §4 secondary 1 is **also** refuted: `CC_REGULAR` moves **up** and
`CT_PEAKER` **down** — the opposite of the predicted direction. Arm A reproduces
`FINDING-pjm139`'s published model column **exactly** (+3.93/+4.55/+6.51), so the
control is validated against the statistic itself.

**WHY the pre-check misfired — an all-ISO scope bound.** pjm-139 W7 compared the
model's **p99** 1-h up-move to the real fleet's **p99** (CC 1.42/1.72/1.53, CT
1.38/1.70/1.52, ST 1.61/1.62/1.50) and concluded aggregate excess "PROVES
per-plant rows would bind." The measurement is sound; the inference does not
follow, because **the envelope is not the fleet's p99 — it is each plant's MAX**,
pooled over 26,280 hours. On arm A's own dispatch the model's p99 sits at
**0.281 / 0.293 / 0.289** of that max (its own max at 1.415/1.478/1.361, p90
2.533/2.825/2.548). **A MAX-based envelope cannot be pre-checked with a p99-based
excess statistic** — pre-check a bound against the bound. This is the ERCOT-127
property ("the real fleet violates the envelope 0–10 times a year") now measured
on PJM's own fleet.

**Gates.** Determination **CALIBRATED** in both arms; C1 · C2 · C3a · C3b · C3c ·
C4 · C6 · C7 · C8 all **PASS**; C1 **16/16 with free 12/12** (pinned `CC_CHP` /
`ST_CHP` excluded as always). **K3, the standing kill: C3c is IDENTICAL** — model
tail-hour counts **3 / 10 / 32 h in BOTH arms** — so the keeper's thinnest margin
(~1 h in 2024, ~2.5 h in 2025 against a 0.5× floor) was untouched in either
direction. **K4: ZERO slack and ZERO dump**, both arms, all years, so the envelope
is not infeasibly tight. C8 `CT_PEAKER` forced share **unchanged at 16.3 / 16.9 /
17.1 %**, all GROUNDED (D-4 clear, profile r 0.923–0.973, off-peak CV ratio
0.705–1.084) — as pre-registered, a ramp row is not a min-gen floor and adds no
D-2 mechanism id. D-1/D-2 read FAIL in both arms **and in the superseded keeper's
own committed `legitimacy_report.md`**: pre-existing states that the rule-20
materiality filter and C7/C8 grounding resolve to PASS, unchanged by the delta.
**K1 does not fire**: the literal test (every class < 0.1 %) is not met — worst
class **+0.262 / −0.184 / −0.219 %** (`COAL_PRB` / `VIRTUAL_INC` / `ST_GAS`) —
but every **material** class moves under 0.06 % and the ISO total moves 2–5 GWh
of ~820 TWh, so **near-inert** is the honest description.

**DOF.** Ledger **17 → 18 entries with `n_residual` UNCHANGED at 6**. Every number
in the artifact is a measured maximum from the CEMS trace; PREREG §5's no-feedback
ceiling was honoured absolutely — no multiplier, scale, haircut, blend, floor,
cap, widening, tightening, per-plant override or quantile swap, and the only knob
touched was the flag's on/off state. Rule 19: no other keeper mechanism owns
intertemporal thermal coupling. Rule 25: PJM's artifact from PJM's own plants;
ERCOT's `R` and CAISO's `I` do not transfer and were not touched.

**Promotion rationale (rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`).** Promoted
because the measured envelope is more accurate than the implicit infinite-ramp
estimate it replaces — demonstrably so, at ~0.5 TWh/yr of infeasible dispatch —
and **not** because it improved the fit, which it essentially did not. A real
physical constraint stays in even when the residual does not move. **Honest scope,
leading rather than trailing: the winter morning ramp is NOT closed and its root
cause is still unidentified.**

**Probe defect found and fixed in-session, disclosed because it changed a reported
number.** The first D-ENV pass mapped the dispatch parquet's `klass` through
`_RAMP_BUCKET_BY_GROUP` directly, silently dropping **every coal group** — the
fleet's `plant_group` is the single `COAL` while `klass` splits into
`COAL_BIT`/`COAL_PRB`/`COAL_WC` — losing 42 of 194 live groups and **38.6 GW
(31 %)** of live capacity, i.e. exactly the class the defect implicates. Fixed by
collapsing the coal variants before mapping; the probe now reports its own match
rate (**194/194**, full 124.1 GW) so the denominator can never be silent again.
All D-ENV figures above are post-fix.

**Matrix (rule 28 duty b).** `ramp_envelopes` PJM **`U` → `K`** — the first keeper
in **any** ISO to carry `ramp_limits=True`. Header re-stamped, keeper pointer
updated, note extended with the coverage, the A/B result, the D-ENV measurement
and the p99-vs-max scope bound; the `P` evidence key **extended, not replaced**.
ERCOT `R` / CAISO `I` untouched (rule 25). `check_mechanism_matrix.py` PASS.
`mechanism-testing-matrix.md` §5.3: item 11 **closed with the result and the
inference error recorded** rather than deleted, and a new item 12 names the
successor instrument.

**Holdouts / governance.** `--years 2023 2024 2025` only; no out-of-training year
touched (rule 22), no `--holdout-authorized` passed. No offer curve, sigmoid,
floor, derive value or ORDC parameter changed (rules 13/21/23/26); the derive was
**run**, not modified. Both arms registered on the dashboard (rule 15), pruning
`2026-07-25-pjm-121-cc-belt` and `2026-07-26-pjm-129-meritguard-a1` under the
top-15 PJM retention. `audit_keepers.py --check` passes PJM's own row; its single
failure is the **pre-existing** stale `status/NEISO.js` on main, which belongs to
NEISO's lane and was deliberately not touched.

## 2026-07-31 — pjm-143: the PS-fold hydro LEVEL closed — `hydro_level_923_hy` ARMED at PJM, A/B'd and PROMOTED. Keeper `2026-07-30-pjm-140-rampenv` → **`2026-07-31-pjm-143b-hy-level`**.

The miso-109 cross-ISO screen measured PJM as the largest pumped-storage fold
of the six ISOs and left it for this lane (rule 25). Re-derived from source
in-session: PJM files no `NG: PS` column, its `NG: WAT` peaks 6,633/6,383 MW
against a 3,334.2 MW conventional nameplate (1,437/1,572 h/yr above it, beside
a 5,046.1 MW PS fleet — Bath County 2,862), zero negative hours, EIA-923 PS
netgen NEGATIVE every year; coverage-gated level gap **+6.475 TWh (+72.1 %)
2023, +6.957 TWh (+78.5 %) 2024** (2025 never differenced — early release,
13 of a modal 77 plants). The keeper pinned the LP's EIA-923 `HY` units to that
PS-inclusive series, so ~70–80 % of PJM's real hydro budget was phantom
zero-marginal-cost energy — on a keeper the board called CALIBRATED.

**The fix is one line** — `"PJM"` into `constants.EIA930_PS_FOLDED_INTO_WAT`
(commit `7bfaa73`) — arming both prebuilt lanes at once: the miso-109 backcast
pin refusal and the miso-110 forecast 923-climatology (forward level
15.875 → 9.254 TWh). Zero new parameters; DOF ledger unchanged (18/6). No
reconciliation factor — none identifiable, and **the MISO sign-change premise
does NOT transfer** (PJM's monthly gap never changes sign; the refusal rests on
the 0.654→0.556 share drift + the 3–6× seasonal range + rule 13).

**Pre-registered A/B** (`PREREG-pjm143-hydro-level-923hy-2026-07-31.md`
committed before either arm solved; sign, magnitude band, kill/keep).
Control `2026-07-31-pjm-143a-control-930pin` reproduces the outgoing keeper's
load-weighted prices to the third decimal. Candidate
`2026-07-31-pjm-143b-hy-level`: hydro −6.548/−6.958/−7.042 TWh → fossil
+5.19/+5.64/+5.65 TWh (CT_PEAKER +0.99/+1.24/+1.51, narrowing its C1 deficit
note) + imports; LMP **+0.287/+0.293/+0.383 $/MWh** (~+0.9 %), summer-peaked
on the fold's own Jul/Aug signature; C3a 2024/25 toward actual, 2023 away
(+2.05→+2.99 %) exactly as pre-declared. **CALIBRATED 9/9 in BOTH arms — no
gate flipped**; C3c tail counts byte-identical (3/10/32 vs 6/18/59); C8
CT_PEAKER grounded share improves to 15.2/15.4/15.8 %. Magnitude band refuted
by $0.013/$0.007 in 2023/24 (holds 2025) — recorded, not re-written.
`hydro_budget_nameplate_aware` PJM **K → I** (inert on the corrected level,
L1 = 0.000 GWh exactly; under the pin it shuffled 1,703/1,147/2,085 GWh — its
entire apparent signal was the defect). Keeper note 11 CLOSED. Rule 22: only
2023–2025 touched; 2022 deliberately not spent. Full write-up:
`results/calibration/FINDING-pjm143-hydro-level-923hy-2026-07-31.md`.

## 2026-08-02 — cross-ISO audit touching PJM (caiso-154): the caiso-153 OLS-attenuation defect is NOT LIVE in PJM; the ARMED midcurve artifact re-derives BYTE-IDENTICALLY

No-LP input-standing audit, logged in full in `docs/calibration-log/caiso.md`
(caiso-154) and `results/calibration/FINDING-caiso154-xiso-ols-attenuation-not-live-2026-08-02.md`.
PJM outcomes: (1) neither PJM offer-surface derive contains a regression
estimator — the caiso-153 family is structurally absent, and
`pjm_offer_surface_conditional` is off in the keeper anyway; (2) the ARMED
`pjm_offer_midcurve_condbinned.json` reproduces BYTE-IDENTICALLY from its own
script + a fully refetched 36/36-month corpus (1,152/1,152 leaves), and the
top surface to 0.016 % — the caiso-152 unreproducibility class is CLEAR in
PJM; (3) the counterfactual transplant of the CAISO slope classifier is
REFUTED on PJM's own corpus: admissible OLS everywhere, no slope collapse,
and the hr-cut split misbuckets 6–11 GW of physics-CC_LIKE under EVERY
estimator — the physics segmentation is load-bearing, so any future
slope-based PJM identification owes its own charter against that measured
warning; (4) shipped-estimator tail sensitivity ≤4.8 % vs the 10 % bar
(11 Jan-2024/-25 HH+basis tail days carry 53 % of the fuel regressor's
variance — a precision, not a level, exposure). `measured_offer_surface` PJM
stays `R`; keeper `2026-07-31-pjm-143b-hy-level` untouched; nothing
registered. Do not re-test without new evidence (rule 28a).

## 2026-08-02 — pjm-144: `gas_offer_margin_zonal_anchor` transferred to PJM, A/B'd and adjudicated **`I` — dispatch-live, price-inert**. Keeper **unchanged** (`2026-07-31-pjm-143b-hy-level`).

The nyiso-109 cross-ISO charter (its §7: the gas-offer margin anchor is
ISO-level while the solve prices per-zone fuel; PJM arms
`pjm_zonal_gas_basis=true` with the second-largest measured spread,
1.483 $/MMBtu). **The admissibility check reshaped the experiment before any
solve**: PJM's applier is the capacity-weighted MEAN-ZERO core (not NYISO's
reference-zone-down convention), so the ISO anchor 3.3483 is the fleet
centroid, the defect is TWO-SIDED (east premium under-marked / west discount
over-marked), nyiso-109's one-sided K6 direction gate was **dropped ex
ante**, K3 liveness was priced on the ZONAL grain, and — because the applier
weights by per-zone gas capacity — the derive gained `--weights-bundle`: the
keeper's own per-year fleet rebuilt no-LP supplies the weights (removed means
−0.105/+0.169/+0.239 $/MMBtu; an unweighted synthetic fleet would be off by
up to 0.106, larger than the 0.1 inertness bar). Anchor table registered in
`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]` (SWMAAC 4.4328 /
Dominion 3.8798 / EMAAC 3.4898 / ComEd 3.2575 / AEP_Ohio+ATSI 3.1201 /
Central_PA 2.9708 / West_APS 2.9495; capw invariant EXACT at 3.3483
Δ+0.0000; zero fitted parameters; +1 derived DOF entry 18→19, n_residual
6 unchanged; 13/13 mechanism tests; default cache_key byte-identical to
main at 0e9fce2fb55b889f).

**Pre-registered** (PREREG-pjm144-zonal-margin-anchor-2026-08-02.md, pushed
before either arm solved). Two solves, three years each, sequential (recipe
peaks ~15.5 GB; swap re-asserted per keeper note 14; 34–35 min/arm).
Control `2026-07-31-pjm-144a-control-zerodelta` reproduces the committed
keeper **byte-for-byte** (0.0 MW max class-hour delta, all three years;
legitimacy diagnostics content-identical) despite 27 src files landing on
main since the keeper's HEAD — the prereg's PJM-inertness expectation held.
Arm `2026-08-02-pjm-144b-zonal-anchor`: K1/K2/K4/K5 PASS, **no kill fires**
— both arms CALIBRATED 9/9, C1 16/16 free 12/12, zero FAILs, C3c statuses
and tail counts identical, slack/dump 0.0 — but **K3 FAILS its zonal-price
leg**: max zonal |Δλ| 0.034/0.032/0.026 $/MWh vs the 0.10 gate (system
+0.030/+0.027/+0.021), while dispatch moves 1317/1288/1537 MW at the max
class-hour (CC_REGULAR −0.40/−0.70/−0.97 TWh → ST_GAS +0.40/+0.51/+0.91,
CT_PEAKER +0.12/+0.22/+0.12 — both standing class-accuracy notes nudged
toward actual; REPORTED, never banked). PJM's price-coupled zones absorb the
mean-zero redistribution: same mechanism as NYISO, opposite convention,
opposite verdict — the rule-25 case study in miniature.

**Disposition is the prereg's own K3 rule: verdict `I`, keeper unchanged,
NOT a promotion** — the owner's standing promote-if-recommended instruction
was answered NO on that rule (no gate regressed; there is nothing a
promotion would change that any gate can see, and the escalation branch was
pre-committed for P-kills only). The structural correction is preserved, not
lost: table registered, derive standing, flag one CLI switch away; re-open
conditions named in the finding (zone-decoupling mechanism / zone-grain
criterion / owner override). Matrix cell PJM `U→I` with both A/B ids and
artifacts cited; §5.3 adjudication added; ERCOT/MISO stay `U` (ERCOT's West
decouples under GTCs — measure, don't assume PJM's inertness transfers).

**Registered per rule 15**: both bundles on the dashboard (labels
"pjm 144a control zerodelta" / "pjm 144b zonal anchor"); top-15 retention
pruned `2026-07-27-pjm-133-control` and `2026-07-27-pjm-133-nameplate`.
Artifacts: `_pjm144_zonal_anchor_ab.json` (scorer, criteria straight from
calibration_verdict metrics — the nyiso-108 scorer-bug class avoided),
`_pjm144_zonal_anchor_derivation.json` (weights + invariant + marked-up
census 986/994/993, 0 band-scoped), attestations generated from the
committed A/B JSON (gen_pjm144_attestation.py — nothing hand-transcribed;
arm 19 entries / 6 residual). Holdout: 2023–2025 only, freeze ACTIVE, 2022
not spent.

**Test baseline at this HEAD** (tests/{curation,scoring,unit} after a full
`regenerate_clean`): **13 failed / 4550 passed / 14 skipped / 1 xfailed /
254 subtests passed** in 11m50s. All 13 are the standing known-red set
(`test_measured_chp_heat_rates` 7, the three stale-pinned cache-key
byte-stability tests — the default `ScenarioConfig().cache_key()` is
byte-identical to origin/main at `0e9fce2fb55b889f`, re-verified after this
session's constants addition — `test_consume_lmp` 1,
`test_ff_readiness_battery` 1, `test_outages` 1). Zero attributable to
pjm-144; the nyiso-109 baseline's 14th
(`test_clean_io::test_datatype_list_matches_schemas`) is fixed on main.

Next shorthand: pjm-145.

## 2026-08-02 — pjm-145: `pjm_dam_availability` (queue §5.3 item 7) **REFUSED EX ANTE — no solve spent**, matrix `dam_availability_rebasis` PJM `U → G`. Keeper **unchanged** (`2026-07-31-pjm-143b-hy-level`).

The intaken-but-untested DAM-availability lever, taken as the live head of the
cross-ISO queue (MISO: no live lever after miso-111/112/113; ERCOT items 7–8
data-intake-first; NEISO charter-first; CAISO's live items are a charter and a
derive re-identification). Full protocol: PREREG committed before any
measurement (`PREREG-pjm145-dam-availability-2026-08-02.md` — kill rules,
gates K1–K4/P1–P5, direction prediction), then the no-LP ex-ante instrument
(`_pjm145_damavail_exante.py`, the real `generators_to_fleet_arrays` path via
`run_year(fleet_only=True)` with the keeper's own meta kwargs), then the
decomposition addendum (`_pjm145_damavail_decompose.py`).

**Measured, and decisive without an LP:** the armed overlay is a
**+24.0/+23.7/+18.8 GW mean-availability net RESTORE** (2023/2024/2025;
restore on 364/364/360 covered days, remove on 0/0/5 — the mechanism as built
is ~entirely its restore leg), against model covered-class availabilities of
0.44–0.83 vs the uniform fleet-mean target 0.867–0.887. The addendum
decomposes the restore-day lift: **66.0/66.6/68.4 % is structural-zero
resurrection** (17.7/19.2/18.5 GW mean) — units the model's finer measured
record holds at zero (CAMPD unit/short/partial outage windows, layup, retiree
CEMS caps, mid-year COD masking, and `cc_outage_derate_from_top`'s
top-of-stack tranche zeros) revived to λ by the water-fill's `_flat` branch.
That is the ERCOT-135 §7.2 "destroyed unit resurrected" defect; the ercot137
pmax-ceiling fix was applied to the ERCOT path only, and the PJM class-grain
block carries no ceiling.

**Refusal grounds** (rule 1: dominant effect is physically-false capacity
injection — an A/B would adjudicate the transform's artifact, not the data;
rule 14 misalignment clause: one RTO-wide whole-fleet unplanned aggregate,
non-fossil forced MW included, is a wrong-boundary datum for a per-class
application and overwrites finer measured inputs already armed; rule 19: the
unit-grain CAMPD stack is the incumbent availability owner — this stacks a
coarser second owner that mostly UNDOES it). The ERCOT contrast is the grain:
its 60-Day disclosure is per-class/plant and ceiling-composed, hence
adoptable; PJM's public aggregate is not. **Honesty record:** none of the
three pre-registered kill-rule LETTERS fired (the degeneracy mode was
resurrection-at-λ, not the operationalized cap-saturation/target≤0), and the
direction prediction (net REMOVE, prices up) was **WRONG** — both scored as
written in the FINDING. The refusal follows the ERCOT-145/caiso-149
refused-ex-ante pattern: no arm, no bundle, no dashboard registration; C3c's
1 h / 2.5 h margins untouched.

**Session preamble outcomes** (the handoff's two standing fixes): (a) the
drifted default cache key was ALREADY REPAIRED upstream at f58339b (FFR-W1X
Wave-1 close registered `coal_prb_committed_dispatchable`/`_split`); verified
`ScenarioConfig().cache_key() == 603c2498bf71d21d` and all three pinned tests
green, plus an AST field-diff vs the pin commit (all 10 post-pin fields
registered). (b) Full-suite baseline on origin/main f58339b recorded BEFORE
any edit: **11 failed / 5869 passed** — the known set
(`test_measured_chp_heat_rates` ×7, `test_outages` ×1,
`test_ff_readiness_battery` ×1) plus two additional pre-existing
(`test_consume_phase3d` zone parity, `test_fleet_arrays_golden` ERCOT
golden). **Keeper-replay reproducibility on a fresh clone** (recorded for the
next PJM session): the pjm-143b recipe needs two gitignored inputs
regenerated first — `data/raw/pjm-da-virtuals/hrl_da_incs_decs_*.parquet`
(36 monthly files, `scripts/data/fetch_pjm_da_virtuals.py --feeds
hrl_da_incs_decs`; the keeper arms `pjm_da_virtual_bids`, whose loader
hard-fails without them) and `data/raw/PJM-AS/pjm_{2023..2025}_as_up_mw.parquet`
(`scripts/data/build_pjm_as_withholding.py`; the deriver also rewrites the
committed ≤2022 parquets with byte-churned metadata — `git checkout` them,
rule 23). The unused A/B chain script (`_pjm145_chain.sh`) stays committed
for any post-re-open session.

**Re-open conditions** (own charter, PJM-derived parameters, rule 25): (1)
restore ceiling composed with the structural-derate registry (port the
ercot137 fix — note the remaining content is then ~9 GW/day of living lift
toward a still-contaminated fleet-mean target, so (2) or (3) is likely also
needed); (2) a class-/unit-resolved or fuel-split outage numerator; (3) the
event-window-cap form (ERCOT-148/149 shape) identified from PJM's own record.

Next shorthand: pjm-146.

## (stub) caiso-155 — 2026-08-02 — PJM: plant-set census S3-blocked on pjm-da-virtuals; static census clean; two clean partitions regenerated

Cross-ISO scorer audit (main entry: `docs/calibration-log/caiso.md`
caiso-155). The empirical floors census for `2026-07-31-pjm-143b-hy-level`
is blocked on the documented uncommitted raw (`data/raw/pjm-da-virtuals/` —
fetchable via `scripts/data/fetch_pjm_da_virtuals.py` in a PJM-lane
session); the G-06 CI recompute shares the blind spot (notes-and-skips).
Static census: no firm-floor config exists on any PJM neighbor and no
firm-import flag in the keeper meta — no exposure expected. En route this
session regenerated two derived `data/clean` partitions the rebuild needed
(`transfer-interface-limits`, `ramp-capability`). Matrix cell `P = O` on the
`diagnostics_plant_set` audit row until the empirical half runs.

## pjm-146 — 2026-08-02 — RGGI allowance cost: mechanism LIVE and gates pass, but the model's leakage response is too elastic (`U → O`, keeper unchanged)

**Phase 1 (no LP): the matrix-column triage.** All 21 open PJM cells classified —
4 live candidates, 9 data-/instrument-blocked, 7 forecast-lane, 1
precedence-superseded (`docs/handoffs/pjm-matrix-column-triage-2026-08.md`).
`state_carbon_pricing` confirmed rank 1; `measured_chp_heat_rates` rank 2 and the
named successor for the next PJM session.

**Phase 2: the pre-registered single-delta A/B.** Arms
`2026-08-02-pjm-146a-control-zerodelta` (`pjm146_control_A`) and
`2026-08-02-pjm-146b-rggi-allowance` (`pjm146_rggi_B`), both registered.
One delta: `pjm_rggi_allowance_pricing=true`. Zero fitted parameters — published
RGGI auction clearing means metric-converted (14.87/22.83/24.35 $/t), exact
EIA-860 state membership, fleet's own emission rates. DOF ledger 18 → 19 entries,
**n_residual UNCHANGED at 6**.

**ALL FIVE PRE-REGISTERED GATES PASS.** K1 mc identity exact to 3.7e-13 (tol
1e-9); K2 control reproduces the keeper to **0.0 MW** on every class-hour, all
three years; K3 membership audit clean (VA charged in 2023, zero in 2024/25
across 719 units); K4 sign; K5 liveness. Load-weighted LMP
**+1.4226/+1.4278/+1.2595 $/MWh** (+4.53/+4.58/+2.97 %), inside the ex-ante E1b
band. **Not the pjm-144 outcome** — PJM's price coupling TRANSMITS a one-signed
level shift where it CANCELLED a mean-zero spread, so coupling is not a general
bar on PJM zonal-cost levers.

**Structure improves:** D-2 clears all three CT_PEAKER forced-share FAILs
(0.1541/0.1579/0.1591 → 0.1328/0.1203/0.1298); C3a-2025 improves (−9.0 → −6.3 %);
C3c bit-identical; C3b/C4/C6/C7/C8 PASS. RGGI **leakage is reproduced
endogenously** — CC_REGULAR −12.80/−14.78/−10.00 TWh to CT_PEAKER, coal, ST_GAS
and net imports, nuclear/wind/solar/hydro bit-unchanged.

**Gates regress, and the keeper is NOT changed:** determination CALIBRATED →
NOT-YET. C3a 2023 FAILS at +11.1 % (from +2.99 %) — E1d **pre-declared and
licensed** this. C1 FAILS on CC_REGULAR **volume** (−16.06 TWh 2023, −13.84 TWh
2024; C1 16/16 free 12/12 → 14/16 free 10/12) — E1d did **not** license this; no
C1 magnitude gate was pre-registered, so it is an unpredicted regression on a
load-bearing criterion in the class carrying ~40 % of ISO load.

**Reading: right in KIND, too elastic in MAGNITUDE.** Real PJM CC units did not
shed 16 TWh to non-member coal and the measured fuel mix says so. Per rule 14
the accurate input stays available (default-OFF) and the elasticity becomes the
root-cause lane, rather than being deleted or armed on the level story alone.
**Unscored, flagged:** system CO2 likely RISES (~+1.3 Mt/yr 2023, estimate — PJM
scores no CO2 criterion) and imports rise, moving emissions off-footprint.

**Successor:** the CC→coal substitution elasticity under a partial-footprint
carbon price, its own charter, identified from PJM's own record — never a haircut
tuned onto the adder (rule 13, and it would destroy the zero-DOF property).

**Incidental defect carried forward:** D-2's failure list depends on
uncommitted artifacts — an unregistered run has `load_share: null` (materiality
untestable) and a full bundle resolves mechanisms the gitignored-slim committed
tree cannot. Score **both** arms on the committed file set; same class as the
caiso-155 `diagnostics_plant_set` charter.

`results/calibration/FINDING-pjm146-rggi-allowance-2026-08-02.md`;
`PREREG-pjm146-rggi-allowance-2026-08-02.md`;
`results/calibration/_pjm146_rggi_ab.json`.

---

## pjm-147 (2026-08-03) — measured power-only CHP heat rates: `U → K`, **PROMOTED**

**New keeper `2026-08-03-pjm-147b-chp-heat`** (owner instruction in-session).
Arms `2026-08-03-pjm-147a-control-zerodelta` / `-147b-chp-heat`; single delta
`measured_chp_heat_rates=true`; years 2023/2024/2025 in one bundle per arm.
Charter: matrix-triage §2.2 (rank 2). Rule 25 — PJM entered as `U` and was
judged on PJM's own artifact; MISO/CAISO/NYISO `K` and NEISO `O` transferred
nothing.

**Two prerequisites, both real.** The 7 `TestDerive` failures were ONE stale
harness signature (`plant_table()` grew `basis_hr` in the caiso-147 seam fix,
call site never updated) — repaired, plus the missing case that a hand-factored
shipped rate whose *seam* rate matches eGRID's credited rate must flag `ok`; 15
passed. And PJM's artifact had never been derived: 65 (plant,class) rows, 21
applied, CC_CHP 5/14 plants = 74.0 % of class capacity but **82.5 % of the
class's own metered CAMPD energy**; CEMS 11/12 within 1 %, median 1.00000.

**Keeper note 13 CLOSED** ("PJM CC_CHP runs +42 %", carried from pjm-135):

| year | CC_CHP model → | actual | \|C1 error\| control → arm |
|---|---|---|---|
| 2023 | 9.062 → 8.606 | 6.115 | 2.947 → **2.491** |
| 2024 | 8.710 → 8.071 | 7.283 | 1.427 → **0.788** |
| 2025 | 7.806 → 6.835 | 6.445 | 1.361 → **0.390** |

Improving every year, **never crossing under** — the pre-registered neiso-70
overshoot kill (K5) does not fire. CALIBRATED 9/9, C1 all 16/16 · free 12/12,
zero fails, zero caveats. **Zero fitted parameters**; DOF 18 → 19 with
`n_residual` UNCHANGED at 6; the off-registry ×1.8 / ×1.15 hand factor RETIRED
on covered plants (rules 21/24).

**The pre-registration closed pjm-146's own named gap.** E1d declared ex ante
that no C1-gated class may move > 1.5 TWh; largest non-CC_CHP move was
CC_REGULAR **+0.366** TWh. pjm-146 licensed a C3a move but registered no C1
magnitude gate, which is exactly why its CC_REGULAR regression could not be
adjudicated on its prereg alone.

**K2 FAILED, and this promotion is what fixes it.** The control does not
reproduce the outgoing keeper (943/1031/1245 MW; +$0.057/+$0.044/+$0.077).
Cause: caiso-158's CT hour-grain meter screen moved PJM's
`campd_ct_heat_rates` artifact on 63 of 71 applied plants / 19,887 MW
(11.4749 → 11.5556, +0.70 %), and PJM arms `measured_ct_heat_rates`.
**A framing this session got wrong and withdrew:** an earlier commit called it
an unchartered CAISO-lane change violating the matrix's "own charter" warning —
false. caiso-158 executed `PREREG-caiso156`, pre-registered PJM's own +0.0693
delta (reproduced here to 4 dp independently), and **declared the PJM scope cut
on the record** (its §5: PJM not launched for want of swap on a 15 GB box).
**So the control arm IS caiso-158's follow-up item 2**, now discharged with
12 GB of swap and the `--years`/`--reuse-solved` chain: CT_PEAKER
−0.924/−0.657/−0.899 TWh, dispatch-live and **score-neutral** (control
CALIBRATED 9/9, scorecard identical to the outgoing keeper) — the same shape
caiso-158 measured in CAISO/NEISO/NYISO. One adverse diagnostic row, stated:
D-2 CT_PEAKER **rises** 15.2/15.4/15.8 % → 16.3/16.4/16.5 %, GROUNDED ABOVE
BUDGET PASS throughout.

**Binding on successors.** (1) The caiso-147 seam defect is **measured SMALL**
in PJM — 4 applied rows / 182.2 MW vs CAISO's 59 / 3,089 MW. (2) **CC_CHP is a
PINNED class** (audit L4) excluded from the free-class score, so the lever
cannot move PJM's headline and equally cannot be gate-chasing — rule-1
`[R-STRUCT]` work only. (3) The **CT_CHP half is NOT identified** (32.6 %
capacity / 25.1 % of its own metered energy), NOT scored (`FUELMIX_EXCLUDED`)
and nearly INERT at the seam (+0.36 %) — not citable in either direction.

**Not fully closed, and the successor is named.** 2023 still runs +2.49 TWh
over; the offer is now measured, so the residual is a **quantity** question —
the host-steam holdout (`chp_btm_pct` / `chp_grid_pmin_mw`) and the `chp_steam`
floor level, nyiso-105's named lane. **DO NOT re-derive the heat rate against
that residual** (rule 23 `[R-FROZEN-DERIVE]`). Separately chartered, not done
here: the caiso-147 sub-6.0-MMBtu/MWh **meter-hour** screen on the shared CHP
derive (PJM 1.55 % of loaded hours, +0.081 energy-weighted) — the CHP analogue
of the CT screen caiso-158 shipped, cross-ISO, not a PJM session.

**Process note.** Arm B's link 3 refused `--reuse-solved` and re-solved all
three years because this session committed probe files under `scripts/` while
the chain ran (the gate checks `src/`, `scripts/`, `data/`). Conservative
failure — cost was time, not correctness; both arms record `git.dirty=false`
with zero `src/`/`data/raw/` commits between them. **Do not commit to
`scripts/` mid-chain.**

`results/calibration/FINDING-pjm147-measured-chp-heat-rates-2026-08-03.md`;
`PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md`;
`results/calibration/_pjm147_chp_ab.json`, `_pjm147_k2_drift.json`,
`_pjm147_flag_fidelity.json`.

Next shorthand: pjm-148.

## 2026-08-03 — pjm-148: the CHP host-steam holdout lane REFUSED (no LP spent); D-2 floor attribution found path-dependent

**Verdict: REFUSE.** No solve, no bundle, no registration; keeper
`2026-08-03-pjm-147b-chp-heat` untouched. Pre-registration
`results/calibration/PREREG-pjm148-chp-host-steam-holdout-2026-08-03.md`
committed at `6f14dbc` **before any measurement that decides a verdict** (its
push failed transiently and landed later in-session; the content was never
edited after). Rule 25 `[R-ISO-SCOPE]`: reached independently of nyiso-105, on
PJM's own data.

The lane pjm-147 §8 named — move `chp_btm_pct` / `chp_grid_pmin_mw` / the
`chp_steam` floor **level** to close CC_CHP +2.491/+0.788/+0.390 TWh — has **no
admissible arm**, on four pre-registered questions:

* **Q2 (κ) REFUTED, harder than at pjm-131.** κ = **0.0101 / 0.0404 / 0.0236**
  on the *current* keeper against the inherited ≤ 0.20 rule. 2023 more than
  **halved** from pjm-131's 0.0226 — pjm-147's +7 % dearer offer moved CC_CHP
  further from its ceiling. A capacity pull-out is absorbed while the bench
  actual (identical share) falls in full ⇒ the overshoot would **worsen**.
* **Q3 DEAD on both limbs, and the repair is bigger than pjm-131 scoped.**
  `chp-btm-share` re-curates to 35 rows, **35 degenerate** (`btm_share == 1.0`,
  `campd_net_mwh == 0`) **and zero CC_CHP rows** — every one `ST_CHP`, because
  the steam-reporting CEMS unit is a **boiler** (1,754 of 1,755 PJM
  steam-reporting unit-years carry `gross_mwh = net_mwh = 0`; census 655
  dry-bottom wall-fired / 490 other boiler / 254 CFB / 217 stoker / 102
  tangential vs 8 CTs). Fixing the electrical-channel limb pjm-131 named would
  **still** leave CC_CHP at 0 % coverage. `CHP_BTM_PCT_BY_SECTOR['merchant'] =
  35.0` correctly stands as PJM's only available input.
* **Q1 SURVIVES — the floor binds, and the handoff's figure was right while the
  keeper's own artifact is wrong.** PJM CC_CHP `chp_steam` forces **0.994 /
  0.692 / 0.815 TWh = 11.0 / 7.9 / 10.4 %** (superseded keeper
  `pjm143_hy_level_B`), on a floor **verified unchanged** into the current
  keeper (436.4 MW mean / 485.3 MW max, 2023, identical to 1 dp) — yet
  `pjm147_chp_B` carries **no CC_CHP `chp_steam` row at all**. Both of Q1's
  pre-registered limbs proved to be invalid instruments and are reported as
  such: limb (b) is insensitive (0/8,760 hours on the superseded keeper too,
  because it compares class-aggregate dispatch to the summed floor), and limb
  (a) reads an artifact produced by the lossy path below.
* **Q4 — no identification.** Only a floor *reduction* helps (CC_CHP is over in
  all three years, so raising it — including deriving the WP-3 `steam_level_cf`
  PJM's pre-WP-3 artifact lacks, a `max(level, p2)` swap — is wrong-signed by
  construction, declared in the prereg before anything was measured). Both
  channels are closed: `chp_pmin_cf` by rule 23 `[R-FROZEN-DERIVE]`,
  `btm_share` by Q3. Anything else is a level sized by the 2.49 TWh gap — the
  neiso-71 kill, rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`. The magnitude does not
  reach anyway: deleting the floor *entirely* releases ~0.99 of 2.49 TWh, and
  deleting a measured rule-13 input to improve a fit is barred by rules 1/14.

**Structural reading.** κ ≈ 0.01 plus an ~11 % floor together say ~**89 % of PJM
CC_CHP is voluntary economic clearing** between cap and floor — a merit-order
residual, not a quantity one. That is where pjm-131 landed and what pjm-147
tightened by measuring the offer.

**SIDE FINDING — D-2 floor attribution is PATH-DEPENDENT (own cross-ISO charter
needed; deliberately not fixed here).** The dispatch join at
`scripts/legitimacy_diagnostics.py:2325-2327` — the equivalent filter **predates
caiso-155**, so this is not a regression from it — resolves per-plant dispatch
from `dispatch/<year>_<pass>.parquet` when present, else from the dashboard
**run payload**, which is CAMPD-bench-keyed: **311 plants** for PJM 2023,
containing **none** of PJM's 14 CC_CHP plant codes. The calibration protocol
*mandates* scoring on the committed slim file set — the payload path — so
CC_CHP / ST_CHP / nuclear silently lose all D-2/D-4 attribution with no failure
raised. pjm-146 onward dropped **10 rows** vs pjm-144, including a **272 TWh
`nuclear_mustrun`** row every year. Proven by running **current** code over
`pjm144_control_A`, whose own committed file records `CC_CHP chp_steam
0.9938 TWh`, and getting **zero** CC_CHP rows (log: `model dispatch from run
payload … (311 plants)`). **No verdict moves and no keeper is invalidated** —
all three classes are C8-exempt — but rule 18 `[R-FORCED-BUDGET]` is scored
*entirely* from this file, so it is an invisible attribution channel expected to
affect **every ISO's slim-scored keeper**.

**DO-NOT-REDO.** Do not re-derive a PJM CC_CHP host-steam floor or BTM share
against this residual; do not arm `chp_steam_floor_p25` for PJM (pre-WP-3
artifact ⇒ inert, the NEISO position, and wrong-signed regardless).

Rule 15 `[R-DASHBOARD]`: no solve completed ⇒ nothing to register (pjm-131 /
neiso-71 precedent). Rule 22 `[R-HOLDOUT]`: 2023–2025 only, `holdout-freeze.json`
untouched. Matrix: `chp_steam_following` PJM stays `K`, cell re-stamped with the
refusal + DO-NOT-REDO + the path-dependence (rule 28b).

`results/calibration/FINDING-pjm148-chp-host-steam-refused-2026-08-03.md`;
`PREREG-pjm148-chp-host-steam-holdout-2026-08-03.md`;
`results/calibration/_pjm148_screen.json`, `_pjm148_floor_binding.json`;
`scripts/probes/_pjm148_floor_binding.py`.

## 2026-08-03 — pjm-150: the CT meter screen was ALREADY promoted; the re-gate proves the keeper still reproduces BIT-IDENTICALLY

**No promotion, none needed. Keeper unchanged at `2026-08-03-pjm-147b-chp-heat`.**
Registered `2026-08-03-pjm-150-ct-regate` (bundle `pjm150_ctmeter_regate_A`).

**The chartered task was moot before the session opened.** The handoff (carried
from `FINDING-caiso160` §7 item 1) said PJM was the last artifact-consuming ISO
not re-based onto the caiso-156 CT heat-rate meter screen. It was already false:
`pjm-147` ran PJM's leg the same day. Verified from the repo's own bytes — the
artifact has exactly **two** commits on any ref (`c9a370d`, then the fix
`f6238a5` at 00:05:32); the keeper's `basis_sha` `217e5b1` (01:57:04) is a
**descendant** of the fix; and `git show 217e5b1:…campd_ct_heat_rates_PJM.csv`
is md5 `32c26167…`, the POST-FIX blob. `_pjm147_k2_drift.json` and
`mechanism-testing-matrix.md` §5.3 both already say so ("now discharged").

Artifact delta re-measured rather than trusted: applied cap-weighted
**11.5817 → 11.6511 (+0.0694)**, 71/71 applied both sides, 63 changed
(58 dearer / 5 cheaper), **zero flag changes**. Over the 63 changed rows alone it
is **11.4749 → 11.5556**, which reproduces pjm-147's note exactly — the two
figure-pairs in circulation are ONE measurement over TWO populations, never a
discrepancy.

**So the compute went to the gate pjm-147 could not run.** Its own K2 strict-byte
gate FAILED by construction (its comparison spanned two HEADs), and **11
`src/market_sim` commits** landed after the keeper solved, leaving PJM the one
consumer ISO with no bit-identity evidence and the caiso-146 HEAD-drift item
untested. One arm: the keeper recipe replayed COLD at HEAD against the SAME
artifact, no `--set`.

**K2 PASSES — max |ΔMW| = 0.000000 in 2023, 2024 and 2025**, across 499,320 P1
class-hours (787.9277 / 816.8304 / 847.9046 TWh, equal to the last digit).
**THE caiso-146 HEAD-DRIFT ITEM IS ANSWERED IN THE NEGATIVE FOR PJM.** It is now
closed for NYISO (caiso-160) and PJM, and **stays open for CAISO** — the only ISO
where a keeper's sidecars have actually been seen to diverge (up to 3.2 GW).

K1 PASSES with five value diffs, every one an enumerated moved default, derived
for PJM and not inherited: `retirement_rule` (`24b1602`), `entry_rate_limits` +
`entry_commissioning_lag` (`3e33f15`), `net_cone_forward_escalation` (`e6f0cdb`),
`caiso_ra_min_load_frac` (`a0fc302` 3b). **The shared justification is firmer
than caiso-160's**: NOT "forecast-mode only" — `evolve_fleet` has no mode branch
and `runner.py` enters it every year after the first — but that **the calibration
harness never calls it**, because `solve_and_persist` loops years through
`run_calibration.run_year`, a standalone per-year backcast solve. Schema drift
only elsewhere: 3 arm-only fields added since, and the `ct_*_hr_override` triple
`a0fc302` deleted (checked against PJM's own recipe — its readers sat in the
`else` of `if offer is not None` and PJM carries a truthy
`offer_curve_by_group["CT_CHP"]`). **Every entry is a hypothesis; K2 is the
evidence.**

K4: **all EIGHT model-determined criteria identical** to the keeper, C1 headline
`all 16/16 · free 12/12` identical. C6 flips `PASS → UNATTESTED` because a probe
carries no rule-21 attestation (caiso-159 §3) — reported, not absorbed, and no
attestation was authored since nothing is promoted.

**SECOND RESULT, free and zero-confound: the pjm-149 D-2 attribution fix measured
exactly.** Because the dispatch is bit-identical, every difference between the
keeper's committed `legitimacy_diagnostics.json` and the arm's is
*definitionally* not a solve difference. D-1/D-4/D-5/D-9/D-10 are row-for-row
unchanged; **D-2 goes 32 → 42 rows** (nuclear_mustrun ×3 at 272.02/270.59/269.33
TWh exactly as pjm-149 predicted, plus CC_CHP/ST_CHP/COAL `chp_steam` and
`reliability_floor` rows), and **32 shared rows change value** —
`CT_CHP:chp_steam` share **0.0024 → 0.2399 / 0.0013 → 0.1804 / 0.0153 → 0.2780**
on a `class_total_twh` re-basis 4.558 → 1.5256. **This exceeds pjm-149 §7's
projection for PJM** (`+3 / +0 / +0`, gate A2 "additions only"). Stated carefully:
that session's baseline was a pre-fix regen at ITS HEAD, mine is committed-vs-now,
so my delta spans the whole diagnostics-code distance and `f46bdfd` is the leading
but not provably sole contributor. **No gate moves** — C8's own class barely
shifts (`CT_PEAKER:ct_netload_drag` 0.1072→0.1058 / 0.1221→0.1194 /
0.1097→0.1088) and the big movers are CT_CHP/ST_CHP/CC_CHP, all C7- and
C8-exempt. Confirming the attribution is the pjm-149 lane's, not PJM's.

**Environment findings that cost real time.** (1) The handoff's rule-12 chain
`--out-dir X --reuse-solved X` raises `shutil.SameFileError` at
`_copy_reused_year:2978`; pjm-147 avoided it only by chaining through a separate
dir. (2) `--reuse-solved` refuses on THREE independent cleanliness conditions —
dirty tree, prior bundle solved dirty, and **any `src`/`scripts`/`data` commit
between the prior bundle and HEAD**, including the session's own — and the first
only surfaces as a WARNING that silently re-solves every year. (3)
`pjm_da_virtual_bids` needs `data/raw/pjm-da-virtuals/`, which is gitignored and
was EMPTY; `virtual_bids.py` correctly hard-fails rather than no-opping, so **any
PJM session on a fresh container must re-fetch it first**
(`scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds
hrl_da_incs_decs`). (4) `regenerate_clean` ran **50/50 with zero failures** — the
documented `ancillary-services exit -6` teardown false alarm did not fire, so it
is not deterministic.

**DO-NOT-REDO.** Do not run the PJM CT meter-screen A/B — it is done and in the
keeper. Do not re-test `measured_ct_heat_rates` as a mechanism (input correction,
no `ScenarioConfig` surface; PJM cell stays `K`). Do not read K2 = 0 as "the
screen does nothing" — that is a statement about the keeper reproducing, and
pjm-147 measured the artifact as dispatch-live and score-neutral. Do not justify
a `DEFAULT_MOVES` entry with "forecast-mode only."

Rule 15 `[R-DASHBOARD]`: registered, and the top-15 PJM retention re-applied
(pruned `2026-07-28-pjm-135-netpos-keeper`). Rule 16: 2023-2025 in ONE bundle.
Rule 22 `[R-HOLDOUT]`: 2023-2025 only; PJM's `complete` marker unspent, `final`
absent, `holdout-freeze.json` untouched; no keeper change, so no M1 re-key.
Matrix: `measured_ct_heat_rates` PJM stays `K`, note/evidence extended (rule 28b).

**Session ordinal note:** the handoff issued this session as *pjm-149*, but
`d338ba6` had already spent that ordinal on the D-2 floor-attribution session
(filed in `governance.md`, which is why this log's counter never advanced).

`results/calibration/FINDING-pjm150-ct-heat-rate-regate-2026-08-03.md`;
`PREREG-pjm150-ct-heat-rate-regate-2026-08-03.md`;
`results/calibration/_pjm150_regate_gates.json`;
`scripts/probes/pjm150_ct_regate_arm.py`, `scripts/probes/pjm150_regate_gates.py`.

## pjm-151 — the seam envelopes were built on the wrong grain (KEEPER)

**KEEPER → `2026-08-03-pjm-151-seam-envelope`** (was `2026-08-03-pjm-147b-chp-heat`).
CALIBRATED, 9/9, C1 `all 16/16 · free 12/12`, zero caveats. ONE config delta,
`pjm_seam_envelope_by_neighbor`; **ZERO free parameters** and the DOF ledger carried
VERBATIM (19 entries / 6 residual, asserted by `scripts/gen_pjm151_attestation.py`).

**Three phases, two of them spending no LP at all.**

**Phase 0 — PJM's rule-28(c) matrix column is CLOSED.** 15 absent + 1 prose-only +
5 armed-with-no-cell → 0/0/0; ratchet PJM 15 → 0. All 16 closed as literal
sub-scalar registrations on 6 existing rows: zero new rows, zero mechanism verdicts,
one audit-status mint. Mechanical cause is the caiso-161 §2 defect again — the seam
family hid behind the glob `pjm_seam_* :7371+`, whose anchor was itself stale
(`:9019+`), and two of those fields shape the published keeper. Census findings:
`pjm_reserve_online_rho` is recorded in every PJM `run_config.json` and is
unobservable on the keeper (sole read gated on `pjm_reserve_online_gated`, which is
False) — **not** a rule-26 candidate, so nothing filed; and, filed as an observation
only (rule 28(d)), the keeper arms `pjm_reserve_supply_cap=True` alongside
`pjm_reserve_pergen=True` with **both** read paths gated off by pergen. MISO's
ratchet moved 11 → 8 in the same commit and is **not** a MISO census: the PJM seam
literals would have substring-shadowed three `miso_seam_*` fields into "covered", so
those three are written out as real literals rather than dropped by an artifact.

**Phase 2 — the lever, and the chartered question was the wrong one.** Keeper-note
item 12 (carried since pjm-135) charged an inconsistency: `_PJM_TIE_ZONE` puts the
whole TVA tie on `PJM_Dominion` while `INTERFACE_NEIGHBORS` splits it across two
zones. **Two corrections to the charter's premises.** (a) **LGEE is inconsistent
identically** — it is not the self-consistent contrast case. (b) **The two-zone
share never needed deriving.** The two structures are not independent:
`inject_pjm_seam_flow_limit` builds a per-ZONE p90 envelope and SUMS it over each
neighbour's `border_zones`, and a zone bucket holds every tie that lands in it, so
each seam's cap absorbs other seams' ties. The object needed is per-NEIGHBOUR;
building it from the seam's own ties needs only an **identity** read off PJM's own
tie labels. Zero parameters, same file, same shipped p90 (rules 5/13).
`_PJM_TIE_ZONE` is unchanged and stays correct for the per-zone objects.

**Measured ex ante, no LP.** Legacy ÷ direct cap: TVA export **124×/53×/40×**, LGEE
export **33×/42×/26×**, neither binding in any 2023-24 (month × hod) cell — so
`pjm_seam_export_limit`, armed precisely to fix the structural over-export, was
effectively **INERT on two of the five seams**. It **loosens as well as tightens**
(legacy LGEE import cap **0 MW** vs a measured 518/539/549 MW; legacy Carolinas
export 0.67/0.97/0.81× measured), which a residual-fitted change would not. NYISO
reproduces at **1.00× exactly** — the control. A first version of the probe clipped
per-tie before summing (MISO import 2,225 MW vs a netted 0.1 MW) and is recorded as
wrong in its own docstring, with a regression test pinning the netting order.

**Gates.** K1 PASS (one delta; the rest enumerated schema drift / known default
moves — the delta arrives as `arm_only` because the keeper predates the field, and
the first gate-scorer version mis-FAILed on exactly that). K2 discharged **without a
solve** (pjm-150's bit-identity plus six provably PJM-inert `src` commits), so arm A
is the committed keeper. K3 LIVE (max |ΔMW| 1481/1699/1648). K4 **no criterion
regresses**. E1 PASS with zero breaches, largest class move 1.24 TWh vs a declared
3.0 TWh cap.

**THE TRADE, pre-registered before the arm solved and disclosed not absorbed.** Net
export falls in all three years, so interchange family error goes
−10.82/−9.86/**+8.20** → −12.48/−12.22/**+5.21** TWh: better 2025, worse 2023-24.
Gas improves in all three (+4.98/+10.92/+23.05 → +3.91/+9.34/+21.02); coal degrades
slightly. Promoted on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`, with the 2023-24
under-export filed as **new open root cause item 15** — not a seam-deliverability
defect (the repair moved all three years the same way), so it must not be chased by
loosening caps or tuning the tie map. **Rule 26 follow-up OWED:** collapse the gate
flag and delete the zone-summed path.

**Phase 1 — NOT COMPLETED, stated rather than dropped.** The pjm-149 D-2 projection
check needs the diagnostics artifact regenerated from one bundle at two commits, and
each regeneration rebuilds per-plant floors via `run_year` — memory-comparable to the
LP on a 15 GB box, so it could not run alongside the arm chain without risking an OOM
of the deliverable. The pre-fix code view is materialised and the harness is ready; no
claim is offered either way. No verdict depends on it, but rule 18 is scored entirely
from that file at every ISO, so the record correction is **carried forward as an open
item**.

Rule 15: registered, top-15 retention re-applied (pruned `2026-07-28-pjm-136-control`).
Rule 22: 2023-2025 only; `complete` re-keyed **with** a determination re-verification
(D-5(b)) that is not worse; `final` absent; freeze untouched;
`audit_keepers.py --iso PJM --check` PASSES. Rule 28: matrix row added in the same PR,
cell verdict + evidence updated, keeper stamp and PJM gates re-stamped; off-queue entry
declared explicitly under 28(a) as a NEW measured identification.

`results/calibration/FINDING-pjm151-seam-envelope-attribution-2026-08-03.md`;
`PREREG-pjm151-seam-envelope-attribution-2026-08-03.md`;
`results/calibration/_pjm151_seam_gates.json`;
`results/calibration/_pjm151_seam_envelope_attribution.json`;
`scripts/probes/pjm151_seam_arm.py`, `scripts/probes/pjm151_seam_envelope_attribution.py`,
`scripts/probes/pjm151_seam_gates.py`, `scripts/gen_pjm151_attestation.py`.

## pjm-153 — the lever queue is CLEARED (no LP, no bundle, keeper unchanged)

**SHORTHAND RENUMBERED.** This session was dispatched as `pjm-152`; that label is
**SPENT**. A separate merged session (`claude/pjm-152-backcast-calibration-gaq8jv`)
already consumed it for the rule-26 `pjm_seam_envelope_by_neighbor` collapse and a
Task-C item-15 scoping probe, but logged nothing here — which is why the line above
still read "Next shorthand: pjm-152". Renumbered off the spent label per the
nyiso-121 precedent.

**Keeper UNCHANGED at `2026-08-03-pjm-151-seam-envelope`**, re-verified at head
from committed artifacts alone (`scripts/calibration_verdict.py --run-id`, no
solve): **CALIBRATED, 9/9, zero FAILs, zero CAVEATs**, C1 `all 16/16 · free
12/12`. No promotion, so no rule-22 D-5(b) re-key is owed —
`calibration-complete.json`'s PJM `complete` entry already keys this run.

**Zero LP solved. Zero bundles produced. No year touched outside 2023–2025 in any
mode** (PJM holds `complete`, is absent from `final`, and the holdout spend freeze
is ACTIVE and outranks both). Rule 15 has no run to register.

Every remaining PJM lever-queue item reaches a terminal state:

* **Root cause (15-new) → CLOSED by measured refutation, no charter.** It is not an
  independent defect but the flat-stack amplitude defect measured on the seam. The
  2025 "runs long" clause is a **benchmark artifact** (EIA-930 `Total interchange`
  fails its own Net-gen − Demand identity by 14.762 TWh in 2025, hourly r 0.373);
  on PJM's own settlement record the model **under-exports in all three years**
  (−9.57/−9.17/−5.40 TWh). The envelope ceiling has **34–36 TWh of headroom** so it
  cannot bind; the binding side is the model's own price duration curve, which
  explains **86.6/65.3/76.9 %** of the shortfall because the model is too dear at
  the bottom (p5 +$7.32/+$7.57/+$7.36).
* **Item 5 / root cause (6b) remnant → ROUTED.** The §7.2 within-window tight-hour
  memo is **written** (`MEMO-pjm153-g20b-within-window-tight-hour-2026-08-04.md`),
  with the evidence stated both ways and kills K1–K4 pre-registered. Owner sign-off
  pending; nothing armed, no guard parameter moved.
* **`state_carbon_pricing` → UNCHANGED at `O`, PENDING OWNER**; restated for
  decision, not armed, cell not flipped.
* **Item 8 `st_gas_mustrun_p25_level` → CLOSED, cell `U` → `I`** (provably inert:
  ST_GAS `online_frac` 0/10 on PJM's committed artifact).
* **Item 10 `winter_citygate_daily` → CLOSED, cell `U` → `R`**, premise refuted at
  Phase 0 with no intake required — the keeper prices PJM gas off **measured
  EIA-923 delivered receipts**, not Henry Hub.
* **Item 3 (Dominion split) → BLOCKED, re-confirmed and narrowed** — `DOM` is one
  `load_area`, but six other zones do subdivide, so the old "the feed stops at the
  transmission zone" framing is corrected.
* **Items 4 and 6 → RECLASSIFIED as watch items** in `keepers/PJM.json`; C8
  CT_PEAKER re-measured at **16.2/16.4/16.7 %** (grounded pass), C3c **3/10/32 h**,
  and a **newly surfaced** C8 2025 ST_GAS 39.9 % added to the watch list.
* **`pjm_reserve_supply_cap` → ADJUDICATED** as a rule 19 `[R-ONE-MECH]`
  **enforcement gap** (not cosmetic, not a rule 26 delete candidate). Proved with
  `ast`; all 15 committed PJM bundles are armed-and-unobservable. **Filed for the
  owner, not deleted** — the closing guard would make the keeper's own recorded
  config raise.

**Two corrections made against the record rather than inherited.** (1) The D-2
attribution defect pjm-148 routed as needing a cross-ISO charter **does not
reproduce** — it was fixed at pjm-149, which also refuted pjm-148's own CC_CHP
example; the routing paragraph is struck. (2) The `seam_flow_envelopes` matrix row
asserted the pjm-152 collapse's E1 gate had been scored, citing a token
(`PJM152_COLLAPSE_DMW`) that **exists nowhere in the repository**; the gate was
never scored and is filed as an open verification debt needing a solve.

The keeper-note duplicate ordinal **(15)** is disambiguated to **(15a)/(15b)**
without renumbering either, so existing references to "item 15" still resolve.

`results/calibration/FINDING-pjm153-queue-clear-2026-08-04.md`;
`results/calibration/MEMO-pjm153-g20b-within-window-tight-hour-2026-08-04.md`;
`results/calibration/_pjm153_item15_attribution.json`,
`_pjm153_supply_cap_reachability.json`, `_pjm153_queue_screens.json`;
`scripts/probes/pjm153_item15_ladder_attribution.py`,
`scripts/probes/pjm153_reserve_supply_cap_reachability.py`,
`scripts/probes/pjm153_queue_screens.py`.

Next shorthand: pjm-154.
