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
