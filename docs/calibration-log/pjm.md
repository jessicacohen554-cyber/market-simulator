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
