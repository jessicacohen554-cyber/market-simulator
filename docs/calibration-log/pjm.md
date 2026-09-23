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
(`PJM152_COLLAPSE_DMW`) that **exists nowhere in the repository**. Filed as an
open verification debt — and then **DISCHARGED mid-session**: main advanced from
`a96f9743` to `6fbd3f28` while this session worked, the arm landed, and **E1
PASSES absolutely** (`max_abs_class_hour_dMW = 0.0`, `n_nonzero = 0` across all
166,440 class-hours in each of 2023/2024/2025, zero breaches;
`_pjm152_collapse_gates.json`; bundle registered as
`2026-08-04-pjm-152-collapse`). K2's `FAIL` is environment drift only. **Nothing
is owed.** The row's original claim was true, merely un-evidenced at the commit
this session measured; its citation is now the real gate record. Recorded rather
than quietly dropped — a claim with no committed artifact is *unverified*, not
false.

The keeper-note duplicate ordinal **(15)** is disambiguated to **(15a)/(15b)**
without renumbering either, so existing references to "item 15" still resolve.

`results/calibration/FINDING-pjm153-queue-clear-2026-08-04.md`;
`results/calibration/MEMO-pjm153-g20b-within-window-tight-hour-2026-08-04.md`;
`results/calibration/_pjm153_item15_attribution.json`,
`_pjm153_supply_cap_reachability.json`, `_pjm153_queue_screens.json`;
`scripts/probes/pjm153_item15_ladder_attribution.py`,
`scripts/probes/pjm153_reserve_supply_cap_reachability.py`,
`scripts/probes/pjm153_queue_screens.py`.

### pjm-153 addendum — KEEPER PROMOTED to `2026-08-04-pjm-152-collapse`

**KEEPER → `2026-08-04-pjm-152-collapse`** (was `2026-08-03-pjm-151-seam-envelope`).
A **rule 26 `[R-DELETE]` debt discharge, not a mechanism and not a lever** — and the
only kind of promotion that carries zero model risk.

**Why the keeper moves.** The superseded bundle's recorded recipe names
`pjm_seam_envelope_by_neighbor`, a `ScenarioConfig` field HEAD no longer has, so it
is **not replayable as recorded**. The collapse arm's recipe is. Structural
integrity improves and **nothing regresses**.

**Measured, not asserted.** Recipe: **zero value diffs** on every shared field; the
only deltas are the deleted flag and four fields `ScenarioConfig` gained after the
incumbent solved, each at a falsy default and PJM-unreachable. Dispatch: E1
**`max |dMW| = 0.0`, 0 nonzero class-hours across all 166,440 class-hours in each of
2023/2024/2025**, zero breaches (`_pjm152_collapse_gates.json`). K5 passes, no
holdout year touched. K2's `FAIL` is **environment drift only** (platform string +
basis SHA from re-solving at a moved HEAD — the pjm-147 template artifact).

**Determination: CALIBRATED, 9/9, C1 all 16/16 · free 12/12, zero fails, zero
caveats** — identical criterion-for-criterion to the superseded keeper, as
bit-identical dispatch requires. DOF ledger carried **verbatim** (n_entries 19,
n_residual 6), asserted rather than claimed.

**The gap pjm-153 closed.** pjm-152 shipped the bundle and the gate record but
**never wrote the governance attestation**, so C6 scored UNATTESTED and held the run
short of a determination while all eight model-determined criteria passed
identically. `scripts/gen_pjm153_collapse_attestation.py` generates it with every
premise **computed** from the committed bundles and gate record — recipe identity,
E1 byte identity, and the DOF ledger — aborting without writing if any assertion
fails. That is what made the promotion scoreable.

**Rule 22 D-5(b) discharged**: `calibration-complete.json`'s PJM `complete` entry
re-keyed to the new run with a determination **re-verification** (not a
re-assertion); the re-verified determination is **not worse** — it is identical.
`scripts/audit_keepers.py --iso PJM` passes (check M1), matrix keeper stamp and
§5.3 prose header re-stamped.

Next shorthand: pjm-154. *(**SUPERSEDED** — the `pjm-154` label was spent by the
merged `claude/pjm-154-cross-iso-queue-5e2frp` dispatch, which logged as
`miso-127`. The live next shorthand is at the foot of pjm-155 below.)*

## pjm-155 — the lane is PARKED PENDING OWNER (no LP, no solve, no cell moved)

**SHORTHAND.** Numbered **pjm-155**; the `pjm-154` line above is **stale**. That
label was consumed by the merged `claude/pjm-154-cross-iso-queue-5e2frp` dispatch
(PRs #3516/#3520), which hit this same missing-owner-answer condition, routed its
Lane B to MISO and logged there as **miso-127** — so nothing was written back
here. Same spent-label pattern pjm-153 handled; nyiso-121 precedent.

**Keeper UNCHANGED** at `2026-08-04-pjm-152-collapse` (**CALIBRATED**). **No LP
built, no solve launched, no bundle created, no run registered, no mechanism
armed, no cell verdict moved, no year touched outside 2023–2025.** Ran as **Lane
B** of the `pjm-155-owner-decision` dispatch: Lane A1 (`state_carbon_pricing`) and
Lane A2 (G-20b memo sign-off) are both owner-gated and **the dispatch carried no
owner answer**, so no lever was picked up and none was invented.

**Re-verified from committed artifacts alone** (no solve): `calibration_verdict.py
--run-id` returns **CALIBRATED, 9/9, zero FAILs, zero CAVEATs**, C1 `all 16/16 ·
free 12/12`. The four C8 grounded-above-budget rows (`CT_PEAKER` 16.2/16.4/16.7 %,
`ST_GAS` 2025 39.9 %) are **clean PASSes** under rule 21's grounded-pass clause —
D-4 clear, profile r 0.927/0.962/0.974/0.896 — not caveats.
`scripts/audit_keepers.py --iso PJM` **PASSes 0 failures / 0 warnings** (keeper,
holdout, marker and status shards all clean; M1 re-key check clean). Lever queue
confirmed **EMPTY**; frontier **DECLARED 2026-07-31**, unchanged.

**Holdout.** `final` contains only `_note` — **EMPTY for every ISO** — and the
spend freeze is **ACTIVE** (declared 2026-07-25, HELD 2026-07-26), verified
enforced at `run_calibration_full.py:7578-7587` where it is read **BEFORE** the
marker and **fails closed**. So 2022, 2019 and H1-2026 are ALL closed to PJM and
the `complete` marker grants nothing spendable today. Nothing was spent.

**Decision 1 — `state_carbon_pricing`, cell `O`, PENDING OWNER, unchanged.**
Verified at head: PJM's cell is `O` in `cells: ".KOUKK"`, and
`pjm_rggi_allowance_pricing: bool = False` at `scenarios.py:1207`. Built, solved,
registered A/B; **zero fitted parameters**; all five pre-registered gates PASS;
DOF 18→19 with `n_residual` unchanged at 6; D-2 clears **all three** `CT_PEAKER`
forced-share FAILs. Blocked solely by the **UNLICENSED** C1 `CC_REGULAR`
**−16.06/−13.84 TWh** — right in kind, too elastic in magnitude. Arming costs PJM
its zero-caveat CALIBRATED status; leaving it off means no carbon price at all in
the four PJM states that had one (a disclosed accuracy gap, not a gate failure).
Named successor if the magnitude is to be fixed first: the **CC→coal substitution
elasticity** under its **own** charter, identified from PJM's own record (rule 25)
— **never** a haircut, offset or scalar tuned onto the adder (rules 13/21/24).

**Decision 2 — G-20b within-window tight-hour memo (item 5).** Needs a **yes/no on
chartering a charter**, not a fix. Guard constants verified **unmoved** (rule 23):
`MERIT_RCC_PCTL = 0.90`, `MERIT_OOM_FRAC = 0.90` at `outage_detect.py:450,452`.
**YES** is bound by memo §5 and only §5 — an hour-grain **REPLACEMENT** of the
window-grain veto (rule 19, never a stack), zero fitted parameters, both guard
constants FROZEN, scored on **tightest-decile AMPLITUDE** never the annual mean
(PJM's level passes by cancellation), mandatory C3c report (model tail 3/10/32 h),
LOYO within 2023–2025, kills K1–K4. **NO** closes item 5 and root cause (6b)'s
remnant as **owner-refused** — a complete and final answer.

**Known-open, NOT landed here:** the cross-ISO thermal-tranche artifact staleness
(PJM `ST_GAS` `online_frac` 0/10, CAISO 0/70; regenerating rewrites columns ARMED
keeper floors read — needs a cross-ISO charter with a CONTROL ARM, and must not be
landed as a side effect of another lane, miso-127 §7 being the same family); and
`pjm_reserve_supply_cap`, filed at pjm-153 as a rule 19 enforcement gap whose
closing guard would make the current keeper's own recorded config raise — an owner
call.

**Rule duties.** Rule 15 — no run produced, nothing to register, dashboard
untouched and correct. Rule 16 — no solve, duty does not fire. Rule 22 — no
out-of-training year solved, scored, read or registered; no promotion, so no
D-5(b) re-key owed. Rule 23 — nothing re-derived. Rule 25 — no verdict imported
into PJM, no other ISO's cell written. Rule 27 — no source file ≥300 lines
touched; documentation only. Rule 28(b) — **no mechanism tested, so no cell
verdict moves**; the §5.3 parked block is stamped in this same session.

**Evidence:** `results/calibration/FINDING-pjm155-lane-parked-2026-08-04.md`.

Next shorthand: pjm-156.

## pjm-156 — the 2022 VALIDATION TOUCHPOINT is SPENT: price level and tail HOLD, `CC_REGULAR` volume and price shape DEGRADE (2026-08-05)

**What was run.** PJM's designated keeper recipe
(`2026-08-04-pjm-152-collapse`, CALIBRATED on 2023–2025, zero caveats), frozen
and replayed on the held-out year 2022 via
`replay_keeper.py --years 2022 --holdout-authorized`. **Zero recipe deltas**, so
the rule 20 `[R-DOF]` ledger carries onto the touchpoint attestation
byte-identical (19 entries, 6 residual-identified). **No parameter was
identified, re-identified or re-fitted on 2022.** Registered
`2026-08-05-pjm-2022-touchpoint`.

**Authorization.** Spent under a **narrow owner lift** of the 2026-07-25 holdout
spend freeze (owner, 2026-08-05: "lift, spend, re-arm"), scoped to the PJM and
NEISO 2022 touchpoints alone; the freeze is **RE-ARMED in the same session**.
PJM's locked tier is **NOT authorized** — `final` is empty and 2019 / H1-2026
were not touched.

**Result, as scored — NOT-YET on 2022 against CALIBRATED in-sample.**

| | criterion | in-sample | 2022 |
|---|---|---|---|
| **DEGRADED** | C1 fuel-mix | PASS | **FAIL — `CC_REGULAR` +18.28 TWh, share +1.6 pp** |
| **DEGRADED** | C3b price duration/shape | PASS | **FAIL — NRMSE 0.206** |
| HELD | C3a mean LMP | PASS | **PASS** |
| HELD | C3c price tail (RT) | PASS | **PASS** |
| HELD | C2 system volume | PASS | PASS |
| HELD | C4 dispatch correlation | PASS | PASS |
| HELD | C6 governance | PASS | PASS |
| HELD | C7 diurnal shape | PASS | PASS |
| HELD | C8 forced-energy share | PASS | PASS |

**PJM and NEISO fail in OPPOSITE directions, and that contrast is the session's
most useful output.** NEISO (neiso-84, same day) held its whole quantity side
and lost price level (+14.7 %) and shape; PJM **held price level and the
scarcity tail** — the two things NEISO lost — and lost **volume**: the model
puts +18.28 TWh too much through `CC_REGULAR`, a +1.6 pp share error, in a year
of extreme gas. A single shared cause (e.g. "2022 gas is mis-passed-through")
does not explain both, so the two lanes need separate root-cause work rather
than one cross-ISO fix. D-10 records C1 7/8 all-class, 5/6 free-class.

**C8 note, not a caveat.** `CT_PEAKER` 2022 is forced 31.1 % (4.93 of 15.84 TWh),
above the 15 % peaker cap but a **grounded PASS** under rule 21: every binding
mechanism clears D-4 off-window binding, profile r 0.927, off-peak CV ratio
1.004. Reported as a clean pass, per rule 21's grounded-pass clause.

**What this is NOT.** Validation tier is **ITERABLE model-SELECTION evidence** —
not a certified out-of-sample skill number, never quotable as one.

**AVAILABILITY-ENVELOPE PARITY IS VERIFIED — corrected 2026-08-05.** An earlier
draft of this entry said the `CC_REGULAR` miss "must be re-measured after the
envelope fix before it is attributed to the offer stack", on the reasoning that
an over-counted outage envelope and a CC over-dispatch could be confounded. That
framing is **withdrawn as too broad**: it would be right only if 2022's envelope
were worse than the tuned years', and it is not. 2022 comes from the SAME
uniform 2018–2026 detector regeneration, carries the SAME merit-order guard
(layup windows disjoint from the standard extract — 0 of 10,670 PJM windows
overlap), was solved against the **byte-identical** layup artifact the keeper
used (`unit_outages_layup-b8ac78eb969e`), and is in family on volume
(11.78 M MW-days vs a 2023–2025 range of 10.53–12.97 M; median window 12 d).
The confound would have to explain why the SAME defect produces a passing C1 on
the tuned years and an +18.28 TWh `CC_REGULAR` miss on 2022 — so it is not a
sufficient explanation, and the miss stands as a real out-of-sample signal
pointing at the CC offer stack / gas passthrough under extreme 2022 gas. The
envelope defect still discounts the **absolute level** of both sides; it does
not discount the **delta**.

**No re-tune was performed.** Rule 22 sends a validation miss back to 2023–2025;
this session measured and reported only.

**Governance.** No mechanism tested → no matrix cell moves (rule 28b), no new
`ScenarioConfig` field (rule 28c). Keeper UNCHANGED, no marker re-keyed — a
touchpoint is not a promotion. Rule 16 `[R-ALLYEARS]` is not engaged (it governs
keepers; this is a single held-out year, the shape the `complete` marker
authorizes). Run explorer pruned 15 → 4, keeping the keeper, the touchpoint and
every run cited by `calibration-complete.json` or `keepers/PJM.json`.

**Environment note for whoever re-runs this.** PJM 2022 needs **~16 GB RSS** at
LP build/solve and OOM-killed twice on a 15 GB box; it completed only after
10 GB of swap was added. Solve it alone — do not run a second ISO or a
`regenerate_clean` pass concurrently.

Next shorthand: **pjm-157.**

---

## pjm-157 — the CC gas-elasticity object **DOES NOT SURVIVE Phase 0**; the lane re-points (no LP, no solve, no cell moved) (2026-08-05)

**What was run.** Nothing. **Zero LP solves, zero scoring, zero registration.**
Every number is read from committed artifacts: the `pjm2022_touchpoint` and
`pjm152_collapse_A` P1 hourly sidecars, the two dashboard run payloads, the
per-year `bench/PJM/*.json.gz`, `data/raw/eia-930/`, and the EIA-923 monthly
delivered-cost parquet. Full write-up:
`results/calibration/FINDING-pjm157-cc-object-does-not-survive-phase0-2026-08-05.md`.
Probes: `_pjm157_energy_balance.py`, `_pjm157_virtual_channel.py`,
`_pjm157_switching_elasticity.py`, `_pjm157_fuel_and_vintage.py`.

**The pjm-156 hand-back's decisive claim is refuted on the model's own in-sample
data.** The chartered object was "the model's CC fleet is gas-price-INELASTIC".
It is not. Regressing the coal share of (coal + `CC_REGULAR`) on
`ln(delivered gas / delivered coal)` over **36 in-sample months** spanning ratios
**1.00–2.51**: model slope **0.0781** vs actual **0.0814** — **ratio 0.959**. On
2022 the model is *over*-elastic (**1.414**). Annual coal-share error is
**−0.04 / +0.13 / −0.42 / +0.41 pp** (2022 is the *smallest*). And from 2023 to
2022 the model moved **+33.03 TWh** into `COAL_BIT` against a measured **+33.08**
— a **0.15 % error on a 33 TWh fuel-switching swing**.

**This entry supersedes pjm-156's closing framing.** That entry ended by pointing
the miss "at the CC offer stack / gas passthrough under extreme 2022 gas". The
switching measurement above says the passthrough is right; the offer-stack
reading is withdrawn. (pjm-156's *envelope-parity* correction is untouched and
was not re-litigated.)

**What the +25.40 TWh `CC_REGULAR` error actually is.** Decomposed into the
*level* of total (coal + CC) thermal energy and the coal↔CC *switching share*:

| yr | ΔT | Δ share pp | **CC err** | **from LEVEL** | **from SHARE** | level % |
|---|---:|---:|---:|---:|---:|---:|
| **2022** | +30.64 | −1.09 | **+25.40** | **+20.31** | +5.09 | **80 %** |
| 2023 | +2.45 | −0.34 | +3.28 | +1.81 | +1.47 | 55 % |
| 2024 | +5.11 | −0.56 | +6.32 | +3.78 | +2.54 | 60 % |
| 2025 | **+18.67** | +0.51 | +10.73 | **+13.18** | −2.45 | 123 % |

**80 % is thermal LEVEL, and the same level defect is already present IN-SAMPLE
in 2025 at 65 % of 2022's magnitude, in a year that PASSED C1.** The elasticity
object survives only at **5.09 of 25.40 TWh (20 %)**, and as a level-of-share
offset, not a slope deficiency.

**Phase 0.1 — which term absorbs it.** On a self-closing EIA-930 basis the
model's *total* 2022 generation error is **+3.9 TWh (+0.5 %)**, not +30. Demand
**CLEARS** (model rises +25.37 TWh from 2023 vs a measured +25.10 — a 0.27 TWh
delta error); nonfossil **CLEARS** (nuclear −0.1 %, wind/solar 0.0 %; hydro is on
the pjm-143-corrected 923 `HY` basis — do **not** read the bench's PS-contaminated
`classFull.hydro` 16.0 as a model shortfall); BTM **CLEARS**. Two terms do not:

* **the DA virtual layer**, whose net cleared volume swings **+18.57 TWh** from
  2023 to 2022 (+7.45 → −11.12) into phantom demand;
* **net interchange**, where the model under-exports by **18.25 TWh** vs
  12.36 / 12.16 / 9.75 in-sample — the *already-chartered* pjm-135 M4 defect
  ("nothing in the model constrains it"), widened ~6 TWh. Note its **sign**: it
  *reduces* the model's generation requirement, so it offsets the CC surplus.

**`pjm_da_virtual_bids` breaks its own admissibility invariant IN-SAMPLE.** The
mechanism's rule-13 case (module docstring, citing pjm-105) is that the annual
net cleared at *actual* DA prices is ≈0 — measured **−0.68 / −0.95 / +1.32 TWh**.
The keeper clears it to **+7.45 / +6.55 / −0.91**, i.e. **+8.13 / +7.50 / −2.23
TWh away from that anchor in the tuned years**, on flat gross turnover
(30–36 TWh) — so the clearing *point* moved, not the curve mass. Cause is a
transmission channel: hours where the model's dual sits below actual clear net
virtual DEMAND and hours above clear net SUPPLY, in all four years
(corr +0.12/+0.30/+0.30/+0.21). **The layer converts a C3b price-shape error into
a C1 quantity error, with a gain that scales with the price level** — invisible
in-sample at a $29–44 level with C3b passing, dominant at 2022's $67 level with
C3b failing (hourly price MAE $20.61 vs an in-sample 9.20/10.50).

**Phase 0.3 — the fuel input is clean.** PJM-footprint EIA-923 delivered gas
**$7.14/MMBtu** (2022) vs $3.81/$3.37/$4.37, Dec **$9.76**, Aug **$8.97**;
gas/coal ratio **1.35 → 2.80**; 972 plant-month reporters vs 977/959/941. No
pooled or stale vintage fallback. A fuel-input bug is excluded.

**Phase 0.4 — the pooled-vintage bound is small and adverse.**
`measured_ct_heat_rates` is pooled 2023-25 (71/71 PJM plants `ok`, median
`model_over_measured` 0.991) and prices only `CT_PEAKER`, whose error is
**−3.20** (2022) vs −0.49/−0.75/+2.98 in-sample. So it could own **≲3 TWh** — but
the model runs `CT_PEAKER` too **low**, so correcting it displaces `CC_REGULAR`
*downward*. **Wrong sign for the CC object.** (`measured_ramp_capability`'s clean
partition is gitignored/absent and is bounded the same empirical way.)

**One prerequisite before anyone reads the 2022 C1/C2 coal rows.** On an
**identical 42-plant / 38,003 MW census** in 2022 and 2023, EIA-930 `COL` minus
the bench's CAMPD grid-delivered coal is **+19.49 TWh** (11.7 %) in 2022 against
+7.26 / +7.05 / +11.02 (5.8–7.6 %) in-sample — **~7–9 TWh wider than the
in-sample relationship predicts, on the same plants**. This is why the two bases
disagree on the **sign** of the model's 2022 coal error (**+5.1** against the
bench's own 42 plants; **−14.2** against 930 `COL`). It is a bench/coverage
question, not a dispatch one, and could not be closed here — the 2022 CAMPD
facility extract is absent from the container (2023–2025 only).

**Also logged, unopened:** ~7 TWh/yr of double-counted pumped-storage pumping
load (model demand is 930 `D`, which already contains PS pumping, *and* the model
charges its own PS) — constant in every year including in-sample, so it explains
none of the holdout regression; and `ST_GAS` **+4.38** in 2022 vs
+1.47/−2.82/+0.64. Separately, **2025's 930 `TI` cell is unusable**
(`NG − TI − D = +14.68` vs ≤0.04 elsewhere) and the bench's `interchange` row
carries it.

**No mechanism armed — a documented refusal with cause (rule 1 / 13 / 26).** The
chartered object dissolved; Object B is already chartered at pjm-135; Object A's
*root* is the C3b price shape and PJM's price-formation frontier is
**owner-declared at pjm-142** (diurnal-amplitude family CLOSED, overnight gas
commitment bridge `R`), so opening it here would re-enter a closed lane without
authorization; and completing Object A's diagnosis needs the 2022
`hrl_da_incs_decs` corpus, which is gitignored, absent, and whose re-fetch is
out-of-training data intake requiring explicit owner authorization (rule 22
channel 1). The **in-sample half is already established and needs no new data.**

**Recommended next charter.** Object A, **in-sample only**: a pre-registered,
leave-one-year-out 2023–2025 A/B on whether the keeper is better described with
the DA virtual layer **disarmed** than with a layer whose net clearing runs ±8 TWh
from its own admissibility anchor. That is a rule-1 structural question, needs no
new data, and never touches 2022. Question C should be settled first or in
parallel. **Note what the fix is NOT:** pinning the layer's cleared volume to a
measured outcome would violate rule 13 and recreate the condemned pjm-102 clamp.

**Governance.** Rule 22: the freeze is **intact** — 2022 was not solved, scored,
re-registered or worked around, and nothing was tuned on or against the 2022
residual; every identification is in-sample. Rule 25: no NEISO parameter or
verdict transplanted (the shared December miss is noted, not used as evidence).
Rule 21: the C8 `CT_PEAKER` 31.1 % grounded pass was **not** treated as a defect.
Rule 28: **OFF-QUEUE BY NECESSITY** — a new object opened by holdout evidence, not
a re-test of a closed cell; no closed cell re-opened. **No mechanism was tested,
so no status letter moves** — `da_virtual_bids` PJM stays **`K`** — but the
pjm-157 evidence and the open question are appended to that cell's note and
`ev.P` so the ledger does not read as settled (duty b, citation half). No new
`ScenarioConfig` field (duty c). Rule 15: no run produced, nothing to register;
the pjm-156 touchpoint stands as-is. Keeper **UNCHANGED**, no marker re-keyed.
Availability parity not re-litigated, as instructed.

---

## pjm-158 — the DA virtual layer's admissibility invariant is defined at a price this LP does not produce; the rung compression is **exact**; question C is **CLOSED** (2026-08-06)

**Pre-registration:** `results/calibration/PREREG-pjm158-da-virtual-clearing-2026-08-05.md`,
committed and pushed at `6a3dab7a` **before either arm solved** (the pjm-143
precedent). Full write-up:
`results/calibration/FINDING-pjm158-da-virtual-clearing-2026-08-06.md`.
Probes: `_pjm158_coal_basis.py`, `_pjm158_virtual_gain.py`,
`_pjm158_virtual_basis.py`, `_pjm158_virtual_shape.py`.
**Holdout freeze (rule 22): intact.** 2022 was not solved, scored or registered;
every identification is in-sample on 2023-2025. The measured corpus was fetched
with `scripts/data/fetch_pjm_da_virtuals.py`, whose default span **is** 2023-2025
— in-sample, unrestricted, not data intake.

**Question C is CLOSED, and the 2022 coal rows were readable all along.** The
bench carries THREE coal measures and pjm-157 differenced against the two the
scorer does **not** use. 2022 is absent from `completeness.js`, so
`family_is_complete(PJM, "coal", 2022)` is `True` and C1/C2 score coal against
EIA-923 `classFull` — where the model's 2022 coal is **-0.012 TWh (-0.008 %)**,
the *smallest* error of the four years, and the committed touchpoint metrics
already record **C2 = PASS**. Of the three candidate causes: **(a) net/gross is
excluded** by scaling (the in-sample gap-vs-output fit predicts 13.7 TWh for
2022 against 19.9 observed) *and* by sign (2022's census ran at CF 0.443 vs
0.341/0.347/0.405, so the parasitic fraction should be *smaller*); **(c) a CAMPD
extract defect is excluded** because the widening also appears between EIA-930
and EIA-923 (+14.66 TWh in 2022 vs +8.49/+7.16/+9.02), two full-footprint
sources that never touch CAMPD; **(b) out-of-census coal is the residual** —
EIA-860 records 4,431.9 MW retiring during 2022 and 4,014.1 MW during 2023
against a census frozen at the same 42 plants for both years.

**A CROSS-ISO bench defect found on the way (hourly only).** Plants whose
nameplate lookup fails default to `npl = 1 MW`, which destroys their per-plant
hourly `campd` blob (`uint8 % of nameplate`) while leaving `c_ann` and every
annual gate correct. PJM 2022: **4 plants / 9.87 TWh** stranded (W H Sammis,
Homer City, AES Warrior Run, Joliet 29); PJM 2023 4/3.26; also MISO
(2.77/1.79/1.60), NEISO (1.66/1.34/1.27) and CAISO (0.29). Same cause
everywhere: a plant retiring inside the backcast window drops out of the
operable vintage. **Any probe reconstructing hourly/monthly actuals from those
blobs is affected** — including pjm-157 §2's monthly coal panel, whose fidelity
check was run on `CC_REGULAR` (exact) rather than coal. Reported, not fixed; no
verdict crosses an ISO boundary (rule 25 — a shared data-builder defect is not a
mechanism verdict).

**Phase 0.3 — the `N_RUNGS` compression is EXACT, so the representation fix the
lane hoped for does not exist.** A five-step attribution chain (anchor -> price
level -> zonal dispersion -> ladder -> the LP) reproduces the LP's own cleared
volume to **<= 0.09 TWh** against a 30-36 TWh gross turnover:

| step (TWh, + = net virtual DEMAND) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| anchor @ actual DA price | -0.755 | -1.620 | +0.204 |
| + model price level | -7.408 | -6.649 | +0.852 |
| + zonal dual dispersion | -7.395 | -6.577 | +0.925 |
| + `N_RUNGS` ladder compression | -7.462 | -6.585 | +0.815 |
| OBSERVED (the LP) | -7.451 | -6.552 | +0.905 |

Compression contributes **-0.068/-0.008/-0.110 TWh**, lambda-0 displacement is
**-0.19/-0.23/-0.48 $/MWh**, and 8->64 rungs moves the cleared volume by
**<= 0.13 TWh**. `virtual_bids.N_RUNGS`'s "resolution only, never tunable
values" is **verified, not merely asserted**. 97-99 % of the deviation is the
price the curve is cleared at.

**Phase 0.2 — the gain.** `dNet/dlambda` = **-440 / -463 / -340 MW per $/MWh**
(stable across +-$1/$5/$10), steepest overnight (h00-h09, -450 to -540) and
flattest at the afternoon peak; **3.0-4.1 TWh/yr** per uniform $1/MWh. The
layer's time-of-day *reshaping* survives in the LP (hour-of-day corr
**+0.755/+0.661/+0.651** against the reference position) but runs **1.3-1.4x too
large**, concentrated in h00-h05.

**THE FINDING — the invariant is defined at a price this LP does not produce.**
The rule-13 anchor **reproduces** at actual DA prices (-0.755/-1.620/+0.204 TWh;
pjm-105's -0.68/-0.95/+1.32 to within rung discretization, on the same committed
series `_pjm105_symmetric_equilibrium.py` used). But the model's dual is gated as
**real-time** by the scorer's own definition — `calibration_verdict
.score_price_mean`: *"vs actual RT (fallback DA) ... perfect-foresight dispatch
LP prices RT physics, not day-ahead risk"*, with DA a **non-gated diagnostic** —
and PJM's bench carries `rt_lw` in all three years, so the RT branch is taken.
Clearing the **same measured curve** at actual RT:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| anchor @ actual **DA** (the rule-13 reference) | -0.755 | -1.620 | +0.204 |
| anchor @ actual **RT** (what the model is gated on) | **+5.082** | **+3.001** | **+6.781** |
| **DA-RT basis term** | **+5.836** | **+4.621** | **+6.577** |
| — LEVEL leg | +2.991 | +0.973 | +2.432 |
| — SHAPE / dispersion leg | +2.845 | +3.648 | +4.145 |

**A model whose dual reproduced actual RT exactly — a perfect model by the
project's own load-bearing price gate — would clear this layer at +5.08/+3.00/
+6.78 TWh of phantom DEMAND, not ~0.** So the deviation pjm-157 opened is **not**
a C3b symptom a better price would cure; it is a market-basis mismatch, and
neither leg is closable alone (the level leg reproduces `-mean(DA-RT) x gain` to
~1 %, validating the split). Two consequences: the keeper's near-cancellation is
a **coincidence of two large opposing errors** (basis +5.8/+4.6/+6.6 against
model price error -12.5/-9.6/-5.9), so improving PJM's price shape moves the
layer **toward** phantom demand; and the adopted symmetric form clears at up to
**7.45 TWh of phantom SUPPLY** — the mirror image of the pjm-102 clamp condemned
for +10.3/+14.8/+17.2 TWh of phantom demand — with pjm-105's own table recording
that it moved 2024 `CC_REGULAR` **+9.07 -> -1.78 TWh**.

**Caveat, stated plainly.** The anchor is reference-price sensitive: across PJM's
published hubs the same curve's annual net spans **12.7-24.4 TWh**. The canonical
committed system series is the right reference and it does give ~0, so the
admissibility argument stands *as written* — but "~0" is a property of the curve
**evaluated at one particular price**, not of the curve.

**Rule 28.** The `da_virtual_bids` PJM cell's note and `ev.P` carry the Phase-0
evidence; the **status move is conditioned on the A/B**, per the
pre-registration's own decision rule, not on Phase 0. Session is **OFF-QUEUE BY
NECESSITY** (PJM's queue cleared at pjm-153, frontier owner-declared at
pjm-142); the diurnal-amplitude family and the overnight gas commitment bridge
were **not** re-opened, net interchange (pjm-135) was **not** opened, and the CC
gas-elasticity object was **not** re-tested.

**PHASE 1 — the pre-registered A/B is SOLVED, both arms REGISTERED (rule 15).**
`2026-08-06-pjm-158-control-virtual` (`pjm158_ctl_A`, armed) vs
`2026-08-06-pjm-158-novirtual-disarmed` (`pjm158_novirt_B`, single delta
`pjm_da_virtual_bids=false`); 2023 2024 2025 each in one invocation, years
sequential (rules 12/16). **The CONTROL reproduces the pjm-152 keeper
BYTE-IDENTICALLY — max |Δ| 0.00000 TWh over every class and year** — so HEAD IS
solve-identical for PJM's backcast path (the 37-file / 6,414-insertion diff
since `bc9e6dbf` is all forecast-lane code) and the delta is clean. Verified by
solving, as the handoff required, not by inspection.

**All three pre-registered predictions CONFIRMED.**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **P1** NG-equivalent error, control → treatment | −9.94 → **−3.99** | −9.25 → **−4.07** | +1.72 → **−0.29** |
| **P2** Δ `CC_REGULAR` (bar was \|Δ\| ≥ 2 TWh) | **+5.220** | **+6.848** | **+2.689** |
| **P3** hourly price MAE ($/MWh) | 9.20 → **9.94** | 10.50 → **11.82** | 13.97 → **15.24** |

P1's point predictions are missed because the **unconstrained star node
(pjm-135 M4) absorbed +1.00/+0.67/+0.37 TWh** — the caveat pre-registered with
them. **Rubric: control passes EVERY criterion; treatment FAILS C3c-2025**
(model 22 h > $200 vs RT actual 59 h, 0.37×) — exactly the criterion pjm-105's
adoption note credited the layer with fixing.

**Reported against my own prediction.** P2's fit-DIRECTION sub-claim (that
`CC_REGULAR` would move away from zero) holds in 2024/2025 but fails in 2023,
because I anchored it on pjm-157's CEMS-basis errors while **C1 scores EIA-923
`classFull`**. The two bases differ by a stable **+6–7 TWh** for `CC_REGULAR`
in every year, so **the 2022 `CC_REGULAR` error is +18.28 TWh on the gate's own
basis, not +25.40** — the same three-bases trap Question C resolves for coal.
The CC object itself was **not** re-tested.

**VERDICT — cell stays `K`, DEPARTING from the pre-registration's own `K` → `R`
recommendation, with cause (finding §5.5).** That rule assumed disarming would
*improve* the fit, which is what would have made `R` the rule-1-clean call. The
measured outcome is the opposite on **every** load-bearing and supporting gate,
and rejecting real market structure violates rule 1 as firmly as keeping a
fitted one. The defect is **rule 14 `[R-ACCURATE]`-shaped — a real measured
input misaligned to our representation** — so it is documented, not buried:
the layer's cleared volume **must not be read as a measured cleared volume**,
and the root cause (the LP carries ONE price series, gated as RT, while the
curve needs a DA price) is an **architecture question inside PJM's
owner-declared-closed price-formation frontier (pjm-142)** and is **escalated
to the owner**, not pulled as a lever here.

**Standing warning for the PJM price lane.** The DA−RT basis (+5.8/+4.6/+6.6)
and the model's own price error (−12.5/−9.6/−5.9) currently oppose each other
by coincidence. **Improving C3b toward RT GROWS this layer's phantom energy
toward +5 to +7 TWh of phantom DEMAND** — toward the condemned pjm-102 clamp,
not away from it. Expect this mechanism's C1 contribution to move against any
future PJM price-shape work.

**Keeper UNCHANGED** at `2026-08-04-pjm-152-collapse`; no marker re-keyed, no
promotion, no `ScenarioConfig` field added.

**Environment note for the next session.** This container had **15 GB RAM, 0
swap** and an **empty `data/clean`** (gitignored, so a fresh clone has none).
Both had to be solved before any solve: 8 GB of swap was added, and the clean
tree rebuilt from raw. Two time savers worth recording: `data/clean/emissions`
is **not on the solve path** (`campd.load_campd_hourly` reads the RAW extracts
unless `MARKET_SIM_USE_CLEAN` is set, and it is unset), and most curate scripts
accept `--years`, so only 2023-2025 need building.

Next shorthand: **pjm-159.**

---

## pjm-159 — FINAL-declaration assessment: **HOLD**. Two new blockers found; the locked tier is not spendable, and would not run the keeper's model if it were (2026-08-06)

**Full assessment:** `results/calibration/ASSESSMENT-pjm159-final-declaration-2026-08-06.md`.
**No LP.** No solve, no score of any out-of-training year, no registration, no
mechanism tested, no keeper touched, no marker edited, no freeze touched. Every
number is a read of a committed artifact, a re-run of the committed-artifacts-only
scorer on the **in-sample** years, or a read of source at HEAD.

**RECOMMENDATION: HOLD — do not declare PJM `final`.** Four blockers, each
sufficient alone; two are new this session.

**What is in good order, stated first.** The keeper `2026-08-04-pjm-152-collapse`
re-verifies **CALIBRATED, 9/9, C1 all 16/16 free 12/12, ZERO fails and ZERO
caveats** (four C8 grounded-above-budget report notes, clean PASSes under rule
21). `audit_keepers.py --iso PJM` → **0 failures, 0 warnings** across keeper,
holdout, marker and status shards. Lever queue still clear (pjm-153), frontier
still owner-declared (pjm-142). The objection is not that PJM's calibration is
unfinished.

**B1 — neither locked-test year is solvable today (verified on disk).** PJM 2019
has no demand driver (`eia_demand_profiles.parquet` starts at 2021 for EVERY ISO
— the cross-ISO F3 gap, hand-uploaded artifact with no in-repo builder), no
`calibration_reference.json` `isos.PJM.2019` block (on-disk coverage is
2021-2025) and no `PJM_2019_renewable_capacity.csv` (same span). H1-2026 is
blocked by construction: the full-8760 demand contract is unbuildable from a
partial year, `pjm_2026_as_up_mw.parquet` is absent because the builder refuses a
partial year, the LMP parquet block is deliberately not built, CAMPD Q2-2026 is
unposted and EIA delivered gas stops before May-2026. **A `final` grant issued
today would be unspendable** — permanent authorization, touch-once years, and no
way to exercise it.

**B2 — NEW: the frozen keeper recipe does not reproduce on 2019.**
`pjm_seam_measured_ladder` is armed, but `PJM_SEAM_LADDER_BY_YEAR`
(`model/interchange/spec.py:1251`) carries **{2023, 2024, 2025} only** — and
`import_nodes.py:971-981` shows that outside those years the ladder silently
no-ops **AND `inject_reference_price_firm_export` fires in its place** — the firm
scheduled-export floor the ladder DISPLACES under rule 19. A 2019 run of "the
frozen keeper config" would run the keeper's rule-19 *alternative*, chosen by a
year key, in the exact channel (the seam) that carries PJM's largest one-signed
volume error. Two further armed overlays are pooled on the training window by
construction: `measured_ramp_capability` (`POOLED_VINTAGES = (2023, 2024, 2025)`,
an explicit rule-22 quarantine constant) and `measured_ct_heat_rates`
(`years == "2023-2024-2025"`, plant-keyed, already graded DEGRADED-accepted).
And the `pjm_da_virtual_bids` corpus is gitignored/absent with a loader that
**raises** rather than degrading, so 2019 needs its own channel-1 intake
authorization (retention is indefinite; a step, not a wall). The code is correct
as written — the defect is that "spend the frozen keeper config on 2019" is not a
well-defined operation while a load-bearing armed mechanism is year-keyed to the
training window.

**B3 — NEW: the locked-test C3a would use a different statistic than every
in-sample number.** The rubric-v2.4 basis ladder is `rt_lw > da_lw > rt > da`
(`calibration_verdict.py:1250-1257`); PJM's bench parts carry `rt_lw`/`da_lw` for
**2023-2025 ONLY** (checked all four committed parts — 2022 has `da`/`rt` alone).
Load-weighting raises PJM's RT actual by **+1.11/+1.78/+2.91 $/MWh =
+3.9/+6.0/+6.8 %**, against a C3a band of ±10 %. Restating the keeper's own gated
C3a on the legacy basis it would be forced onto: **2023 +6.4 % PASS -> +10.5 %
FAIL**, 2024 -0.4 % -> +5.6 %, 2025 -7.5 % -> -1.3 %. A basis change alone moves
the keeper across the gate boundary. **And it cannot be fixed for 2019
independently of B1:** `lw_retrofit` (`derive_actual_lmp.py:963`) calls
`load_demand`, the same F3-blocked artifact — B1 and B3 close together or not at
all. *Recorded retrospectively:* the spent 2022 touchpoint's C3a is on the legacy
basis while every in-sample number is load-weighted; its caveat establishes
availability-envelope parity (correctly) but this price-statistic non-parity was
never recorded. 2022 is iterable, so it is a note to carry, not a defect to
repair.

**B4 — the pjm-158 DA/RT basis defect IS disqualifying for the touch-once tier**
(not for the keeper — pjm-158's rule-14 disposition stands and the cell stays
`K` — and not for the iterable validation tier). The reason is sharper than "an
open defect": the layer's C1 contribution is `-(DA-RT) x gain`, and **PJM's DA-RT
spread flips sign outside the training window.** Read off the committed bench
(measured data only, no model output, no scoring — the pjm-157/pjm-158 §1 class
of read): **2023/24/25 = +0.89/+0.25/+0.82** but **2019 = +0.10** (an order of
magnitude smaller) and 2018/2020/2021/2022 = **-0.03/-0.25/-0.27/-1.49**. So the
in-sample near-cancellation is regime-specific in BOTH terms, not just in the
model's price error: on a year where DA-RT ~ 0 the basis term largely vanishes
and the price error stands uncancelled. A 2019 miss could not be attributed, and
a 2019 pass could not be trusted — the exact condition the freeze exists to
prevent, applied to a second independent input defect. The pjm-158 standing
warning is re-stated: improving C3b toward RT GROWS the layer's phantom demand
toward the condemned pjm-102 clamp, so the certified number's known trajectory is
to break.

**pjm-135 M4 — open, uncharted, and asymmetric in the direction the error runs.**
NOT independently disqualifying (fails no gate, fully disclosed, root cause is a
declared representation boundary), but it compounds B2/B4. The model
under-exports **one-signed at -9.57/-9.17/-5.40 TWh** on the keeper's own
attested net position, while the only mechanism bounding the net position
(`build_pjm_external_net_position_cut_groups`, `interchange/pjm.py:293`) is
**`bidirectional=False` by design** — it caps net IMPORT and "never bounds net
export". pjm-158's A/B proved it absorbs perturbations (**+1.00/+0.67/+0.37 TWh**
into the star node, which is why P1's point predictions missed). pjm-153 collapsed
item 15b into the frontier, so chartering it "would re-open the frontier under a
new name" — it stays uncharted deliberately.

**The freeze's `lifts_when`: the owner RE-ADJUDICATED it on 2026-08-06 and chose
to HOLD.** State at this session's HEAD (`305688a4`, rebased mid-session):
`holdout-freeze.json` reads `active: false`, but that is a **transient
NEISO-2022-only lift** (session neiso-86, re-solving NEISO 2022 on a corrected
gas-basis input) whose own `lift_scope` says *"NOT 2019 or H1-2026 … and NOT any
other ISO"* and which is re-armed in the same session by design — **PJM is
authorized nothing by it.** And the same owner entry disposes of what an earlier
draft flagged as a stale contradiction: *"charter section 9 records the
investigation CLOSED ON EVIDENCE across four lanes … with a recommendation to
close with cause and lift FULLY — **but the owner deliberately did NOT take that
broader step here**."* So the freeze's basis is a **live owner decision made the
same day as this assessment**, which STRENGTHENS the HOLD. The charter's evidence,
for completeness (`campd-economic-layup-fix-charter-2026-07.md` §9, residual
investigation **CLOSED on evidence**, all steps done, no LP): step 1 PASSED
(residual tracks ISO-NE's published `uncommitted_available_gen_nonfast_mw` at
+0.70..+0.85, anti-correlated with published outages -0.85/-0.86), step 2
NEGATIVE (AUC 0.47-0.57), LANE B negative (82/180 cells, median gain -0.0003),
LP-side closure negative (neiso-68) — the over-count is a **definitional seam**
(published *unavailability* vs CEMS *non-operation*), "explained, quantified,
bounded and shown not to be closable by a detector change. That is a cause, not a
stall". **Lifting the freeze would not make PJM ready in any case:** B1-B4 are all
independent of it, and B1/B3 are data-availability facts no governance act can
change.

**The precedent that should settle it.** NEISO's locked test was spent 2026-07-07
on `2026-07-07-neiso53-winter-fuelsec-coldsnap`; the keeper moved to `neiso-54`
the NEXT DAY and stands at `2026-08-05-neiso-83-ca1-reclass` — **thirty keeper
generations later.** Its honest out-of-sample number describes a model that no
longer exists and is never re-grantable. PJM is in a better position than NEISO
was, but it also carries three defects NEISO's declaration did not know about,
**two of them found in the last 48 hours** (pjm-157 2026-08-05, pjm-158
2026-08-06) and two more found today. A lane still producing material findings at
that rate is not a lane at rest — that is the strongest single argument for HOLD,
and it is about rate of discovery, not any one defect's severity.

**Path to ready (assessment §9, ordered):** (1) close the F3 demand gap for 2019
— fixes B1 and, via `lw_retrofit`, B3 in one no-LP step; (2) build PJM 2019
`rt_lw`/`da_lw`; (3) owner decision on the year-keyed recipe (derive
`PJM_SEAM_LADDER_BY_YEAR[2019]` on the frozen formula from the already-landed 2019
tie file — rule 23's "source data extends" case — or declare explicitly that the
locked test runs the rule-19 alternative; same for the pooled vintages) — silence
is the one unacceptable option; (4) authorize the 2019 `pjm-da-virtuals` intake;
(5) dispose of B4 (charter the architecture question, or record the regime
dependence as a stated limitation of the certified number); (6) owner lifts the
freeze; (7) then declare and spend once. **Note `final` as written grants BOTH
locked years at once** — the owner may prefer to grant 2019 alone rather than
issue a two-year grant of which one year is structurally unspendable.

**Recorded in passing, nothing re-opened.** (a) **pjm-158 §5.3's C3a row is not on
the C3a gate's basis.** Re-running the committed scorer on both registered arms
gives, on the gated `rt_lw` basis: control **+6.4/-0.4/-7.5 %**, treatment
**+6.5/+0.5/-9.7 %** (control identical to the keeper, as byte-identical dispatch
requires) — not the +8.8->+9.7 / +2.1->+3.5 / -5.0->-6.3 the finding tabulates.
**The A/B's conclusion is unaffected and STRENGTHENED:** C3a degrades in all three
years and the treatment's 2025 error is **-9.7 %, 0.3 pp inside the ±10 % band**,
i.e. it very nearly fails C3a as well as C3c. Both arms score NOT-YET on
C6-unattested alone, exactly as pjm-158 §5.4 reported. (b) C3c on the gate basis:
control 3/10/32 h vs RT actual 6/18/59 h, all PASS; treatment 2/24/22 h with
**2025 FAIL at 0.37x** — confirms §5.4 and watch-item W2 exactly. (c) **The
three-bases trap generalizes past coal and CC_REGULAR to PRICES**: check which of
the four price bases (`rt_lw`/`da_lw`/`rt`/`da`) an inherited PJM number is on
before sizing against it; only 2023-2025 have all four. (d) The cross-ISO bench
`npl = 1 MW` defect (task C) is confirmed **still open at HEAD and unfixed**;
pjm-158's inventory stands. It remains the cheapest cross-ISO win and is
unaffected by the freeze.

**Governance.** Rule 22: freeze respected absolutely, no out-of-training year
solved/scored/registered (branch rebased onto `origin/main` 305688a4 mid-session
and the freeze re-verified at that HEAD — see above); the 2019 and 2018-2022 figures are reads of measured
committed bench artifacts with **no model output on either side**, present
precisely to size a governance risk WITHOUT spending the year. Rules 16/12: no
bundle, no solve. Rule 28: matrix and PJM lever queue checked; no mechanism
proposed or tested, so no cell moves. Rule 15: no run produced, nothing owed to
either dashboard. Rule 27: Opus. Keeper **UNCHANGED**; no marker re-keyed; `final`
stays **EMPTY** — the declaration is the owner's.

---

### pjm-159 task B — the DA/RT architecture question: **NO admissible architecture exists; the mismatch is a MEASURED, CLOSED representation boundary.** And PJM is **NOT** a lambda0 attractor (2026-08-06)

**Owner-authorized** 2026-08-06 ("Do task B and c") -- the explicit authorization
the pjm-158 escalation required. The pjm-142 frontier was opened for **this
question only** and **closes again** with the finding.
**PREREG:** `results/calibration/PREREG-pjm159-da-rt-architecture-2026-08-06.md`,
committed at `d4310783` **before any probe ran**. **FINDING:**
`FINDING-pjm159-da-rt-architecture-closed-2026-08-06.md`. Probes
`_pjm159_dart_predictability.py`, `_pjm159_lambda0_attractor.py`; committed JSON
`_pjm159_{dart_predictability,lambda0_attractor}.json`. **Zero LP solves. No
ScenarioConfig field added. Keeper UNCHANGED.**

**All four candidate architectures are dead.**

**(1) TWO-PRICE LP -- dead on measurement AND on mandate.** A second LP pass can
differ from the first only through state it can SEE, so the DA-RT spread it would
reproduce must be a function of model-visible state. It is not: adjusted R2
**0.038 / 0.047 / 0.054** against the pre-registered **0.25** bar, on a
deliberately generous seven-block ladder (calendar -> weekend -> net-load
percentile -> load level & VRE share -> net-load ramp -> tightness proxy -> a
264-column hod x month interaction). The interaction block LOWERS adjusted R2 in
2023/2024 (0.0381->0.0299, 0.0471->0.0374) -- the penalty correctly refusing to
pay for 264 columns. Nothing measured is on the RHS: no LMP, no cleared price, no
DA quantity, because a regressor the model cannot produce forward is not an
admissible driver and including one would manufacture a pass. K-A2 kills it again
independently: the repo is no-MIP and P2 is archived, so a DA pass without
commitment is a second copy of the same LP with the same dual, and pjm-138 already
put the reserve-opportunity-cost half of PJM's price gap outside a no-MIP LP.

**(2) MEASURED RECONCILIATION WEDGE -- dead on the same regression, as rule 13's
forward test.** A state-conditional wedge reaches **0.108 / 0.172 / 0.224 TWh** of
pjm-158's **2.845 / 3.648 / 4.145 TWh** SHAPE leg = **4-5 %** of the leg it exists
to close. (The LEVEL leg is closed by any intercept *definitionally*, which says
nothing about identifiability, and a constant tuned to a measured mean has no
forward analogue.) What the spread actually is: mean **+0.89/+0.26/+0.83** against
sd **14.5/16.5/35.1** and mean|.| **6.65/7.97/11.70** $/MWh -- a forecast-error and
risk-premium process, exactly what a perfect-foresight LP cannot generate and must
not be made to imitate. Independent hazard even had it passed: the spread FLIPS
SIGN outside the training window (assessment section 5), so an in-sample wedge
would carry the wrong sign in four of five other committed years.

**(3) RE-ANCHOR TO THE MODEL'S OWN DUAL -- dead on rule 13's face, NOT on its kill
test.** Re-deriving the measured book so it nets ~0 at the model's price is
rescaling a measured input so the model's output lands somewhere -- the forbidden
move -- and it destroys the identification, since the book's net-zero property at
the actual DA price is a measured fact about what participants submitted. PREREG
section 4 anticipated this ("killed by K-B1 **or by rule 13 on its face**"), so it
is not a deviation.

**(4) RE-GATE THE SCORER TO DA -- REFUSED EX ANTE**, no measurement: the model IS
an RT analogue and bending a load-bearing rubric criterion to accommodate one
mechanism is worse than fitting a parameter. Any future attempt needs its own
owner decision as a rubric amendment.

**=> PREREG section 4 branch 2. The DA/RT clearing-basis mismatch is a MEASURED,
CLOSED representation boundary**, with a falsification bar (finding section 4) any
future proposal must clear. Phase 1 was correctly never entered -- no candidate
survived Phase 0, so no mechanism was built and no A/B was solved.

**THE CELL'S PRE-IDENTIFIED OPEN ITEM IS NOW RUN, AND PJM PASSES IT: PJM IS NOT A
lambda0 ATTRACTOR.** The matrix cell had carried "the lambda0-attractor question
... was never asked in PJM ... it needs PJM's own lambda0-gap and N/(S+N)
measurement." Run on PJM's own corpus, on miso-105's bars:

| K-B1 | 2023 | 2024 | 2025 | bar | MISO, for contrast |
|---|---:|---:|---:|---|---|
| (i) median \|lambda0 - actual DA\| | $3.90 | $3.78 | $5.33 | <= $2 | $0.09 / $1.80 / $0.17 |
| hours within $2 | 27.4 % | 28.5 % | 19.2 % | — | — |
| (ii) displacement share N/(S+N) | 11.9 % | 11.6 % | 11.5 % | >= 30 % | 31-34 % |

**NEITHER bar fires.** PJM's book does not pin the price it cleared at, and PJM's
stack is far more elastic (pjm-142's measured **2.88/3.37/2.57 GW per $1**), so the
same-sized book supplies about a third as much price displacement. **Rule 25
vindicated by MEASUREMENT rather than assertion:** the family is `G` in MISO
*because* MISO is an attractor, and PJM measurably is not.

**So `da_virtual_bids` PJM stays `K` on an evidential basis pjm-158 LACKED.** Two
additions: the misalignment is **irreparable rather than merely unrepaired**, so
rule 14's "keep the accurate input and document the misalignment" is the TERMINAL
disposition, not a deferral; and the mechanism is measurably **not corrupting the
model's price**, so the rule-1 worry that killed MISO's version does not apply here.

**STATED AGAINST INTEREST -- this session CORRECTED its own pre-registered
estimator.** The PREREG said bar (ii) would be judged on a net-load-CONDITIONAL
stack slope, reasoning it was the conservative choice. That was wrong:
conditioning on net load removes the movement ALONG the stack together with the
demand shift (within a decile, dispatchable quantity is nearly pinned by load), so
`dQ/dlambda` is driven toward zero mechanically -- it lands at **0.085/0.496/0.424
GW/$**, 6-30x below pjm-142's independent measurement of the same quantity. **On
that broken slope bar (ii) WOULD have fired at 82/47/44 %, and I would have
reported an attractor finding that is an artifact.** Bar (ii) is therefore judged
on pjm-142's directly measured slope, cross-checked by this probe's revealed slope
(1.54/1.94/1.26 GW/$, giving 18.6-21.0 % -- also below the bar). The correction
moves the result TOWARD the incumbent, so it gets the most scrutiny, not the least:
all three estimates are in the committed JSON, both readings of the kill rule are
recorded (the PREREG's "either bar" vs miso-105's conjunction -- moot here, since
neither fires), and the falsification route is explicit -- **a stack-derived S
below ~0.9 GW/$ would cross 30 % and re-open the attractor question.**

**STANDING WARNING UNCHANGED, now with a reason.** The DA-RT basis
(+5.84/+4.62/+6.58) and the model's own price error (-12.53/-9.55/-5.88) still
oppose each other by coincidence, so improving C3b toward RT still **GROWS** this
layer's phantom demand toward +5 to +7 TWh -- toward the condemned pjm-102 clamp.
Task B's contribution is the reason it cannot be fixed in passing: the basis is not
a calibration residual with a driver, so there is nothing to co-calibrate, and
**section 1 is the standing record that no admissible wedge exists to offset it --
do not reach for one.**

**Governance.** Frontier opened by owner authorization for this question only and
CLOSED again by the finding; no successor lane opened or implied. Rule 28 duty (b)
discharged -- the `da_virtual_bids` PJM cell is updated in this session with the
lambda0 result and the closed-boundary verdict (`scripts/check_mechanism_matrix.py`
integrity OK); duty (c) does not arise, no new mechanism. Rules 12/16: no bundle,
no solve. Rule 15: no run, nothing owed to either dashboard. Rule 22: freeze
respected, no out-of-training year solved/scored/registered; the 2018-2022 and 2019
spreads are reads of measured committed artifacts with no model output on either
side. Corpus: 36 `hrl_da_incs_decs` files fetched, default span 2023-2025 --
in-sample, unrestricted, NOT rule-22 intake (the pjm-158 precedent).

---

### pjm-159 task C — the cross-ISO bench `npl = 1 MW` defect is FIXED (2026-08-06)

`scripts/render_calibration_html.py::_eia860_plant_info` now unions
`eia860_generator_retired_within_window.parquet` -- the SAME artifact the model
side already consumes via `fleet.load_retired_within_window` for exactly this gap,
whose docstring names **Mystic (plant 1588)** as its motivating example. The bench
side never got the same treatment, and NEISO 1588 is in the stranded population.
Retiree pass read FIRST so the operable pass wins on conflict: purely additive,
every already-correct entry byte-identical, no parameter introduced.

**Severity sharpened.** pjm-158 said the hourly blob was "destroyed"; measured, it
is more specific. `_b64` clips at 250, so with `npl = 1` every generation hour
above 2.5 MW saturates and the blob collapses to 2-6 distinct byte values (13-87 %
at the clip). Consequence: **energy is EXACT** (consumers rescale by the committed
`c_ann`, which is why no annual gate ever caught it), the **commitment pattern
survives**, and the **loading profile inside committed hours is LOST**.

**Population and recovery: 18 stranded plant-years / 24.17 TWh -> 0.00 TWh, all
four ISOs.** PJM 13.45 (2022 9.87 / 2023 3.26 / 2024 0.32), MISO 6.16, NEISO 4.27,
CAISO 0.29. Names repaired too -- the bench carried bare plant codes and now reads
W H Sammis (1,706.5 MW), Homer City (2,012.0), AES Warrior Run (229.0), Joliet 29
(1,320.0), Mystic (1,744.4), Rush Island (1,242.0), Edwardsport (812.7), CAISO 356
(821.4). The residual `or 1.0` guard now REPORTS on stderr instead of failing
silently.

**NO GATED NUMBER MOVES IN THIS COMMIT** -- committed bench parts are unchanged, so
every keeper scores exactly as before. The bench payload is rebuilt on every run
registration (`dashboard_add_run.py`), so the correction **propagates to each ISO
the next time it registers a run**, at which point D-1/D-2 for a class holding one
of these plants may move. That is the point of the fix and must be reported by
whichever session next registers in PJM / MISO / NEISO / CAISO (rule 14: keep the
accurate input, find the root cause, do not bury it). Rule 25: a shared
data-builder defect is not a mechanism verdict -- no verdict transfers.

Tests: `tests/scoring/test_bench_nameplate_retiree_vintage.py`, 4 hermetic tests
(both vintages read; operable wins on conflict; a retiree-only plant resolves to
its real MW; the `_b64` 250-clip that made the defect silent is pinned). Probe
`_pjm159_bench_nameplate_fix.py` + committed `_pjm159_bench_nameplate_fix.json`.

**Pre-existing and NOT fixed here:** 7 failures in `tests/scoring/`
`test_ff_readiness_battery.py` + `test_forecast_parity.py` reproduce identically on
`origin/main` with this session's changes stashed (ERCOT `ercot_storage_as_soc_reserve`
and NYISO `nyiso_seam_deliverability_envelope` armed with no forecast-parity
registry declaration). Another lane's debt, reported not adopted.

Next shorthand: **pjm-160.**

---

### pjm-160 task 1 — the bench-regen blast radius: **3 of 26 D-1 rows move, all improving, NO gate flips** (2026-08-06)

`results/calibration/FINDING-pjm160-bench-nameplate-blast-radius-2026-08-06.md`.
No LP solve; committed artifacts in, committed artifacts out. Keeper **UNCHANGED**
at `2026-08-04-pjm-152-collapse`, which **re-verifies CALIBRATED, zero fails, zero
caveats**.

pjm-159 task C fixed the `npl = 1 MW` nameplate fall-through but left the
**committed** bench parts pre-fix (they rebuild only on a run registration, and
no PJM run has registered since). `scripts/regen_bench_nameplate.py` applies it
to the committed parts directly — a full re-render needs `system.parquet` +
`dispatch/*_P1.parquet` + the `_shared/` store, all gitignored and absent outside
a solve.

| | before | after |
|---|---:|---:|
| 2023 COAL_BIT `profile_r` / `cv_ratio` | 0.888 / 0.890 | **0.892 / 0.876** |
| 2023 ST_GAS `profile_r` / `cv_ratio` | 0.970 / 1.830 | **0.973 / 1.583** |
| 2024 COAL_BIT `profile_r` / `cv_ratio` | 0.869 / 1.137 | **0.870 / 1.136** |

Every other row byte-identical; the pre-existing `2025 COAL_WC profile r 0.749`
D-1 failure unchanged at the same value (non-gating — C7 is retired and COAL_WC
is not over its C8 budget).

**The parity guard is what makes a targeted patch admissible.** The CAMPD frame
is rebuilt from `data/raw` with the **solver's own** `_campd_hourly_frame`, then
every unaffected single-class plant is re-encoded at its committed nameplate and
must return byte-identical: **194 / 197 / 197 / 196** per year, and the only
plants that ever differ are exactly the `npl == 1` population. (Trap worth
recording: `npl` is `round(cap)` but the blob is encoded at the **unrounded**
`cap` — re-encoding at the rounded value mismatches 113 of 206 plants and looks
like a basis failure.)

**Repaired:** 21 plant-years / 13.54 TWh across 2022-2024 (2025 had none). Per-plant
hourly L1 movement is **10-67 % of the plant's own energy** — the defect really did
destroy the loading profile — but the plants are 0.3-7.6 % of their class, which
is why D-1 moves ≤ 0.004. Every class that moved holds a repaired plant, every
class holding one at ≥ 0.3 % moved, nothing else moved: fully attributed by the
`--exclusion-diagnostic` pass.

**THE DEFECT IS TWO-SIDED and pjm-159 did not state it.** `runs/<id>.js`
`plants[*].m` is encoded through the same `cap` and is equally saturated (2
distinct byte values for 2866 / 3122 / 10678). Repairing it needs a re-solve. The
naive expectation — that fixing only the actual side breaks a spuriously high
correlation and *lowers* `profile_r` — is contradicted in all three cells, which
bounds the residual model-side defect at a few thousandths. It closes for free on
PJM's next registration; **no re-solve is justified for this defect alone.**

**C7 was retired the same day** (rubric v3.1 owner amendment): `score_shape` and
`C7_GATED_CLASSES` are deleted, so D-1 now binds only through rule 21's
grounded-above-budget escalation for C8. None of the four grounded C8 notes
(CT_PEAKER 2023/24/25, ST_GAS 2025) holds a repaired plant in its year — all four
stay clean grounded PASSes.

**D-2 moves too, and the mechanism is worth recording** — a first reading (that
`npl` cannot reach D-2, since `_decode_cf_bytes` ignores it whenever `c_ann` /
`m_ann` is present) is **wrong**. `at_floor_mask` widens its tolerance as
`atol += 0.01 × npl`, so a plant at `npl = 1` was given a ~0.01 MW tolerance
against a series quantized at ~17 MW and its at-floor hours were **under**-counted.
Measured like-for-like (identical bundle, floors, container; only the bench parts
swapped): **3 of 35 D-2 rows move, all in 2023** — COAL `coal_mustrun`
5.0838 → **5.4141** TWh (4.48 % → 4.77 % of class), ST_GAS `st_netload_drag`
4.8171 → **4.8378** (50.89 % → 51.11 %), CT_PEAKER `ct_netload_drag` +0.0006 —
and **D-2's gate failures are byte-identical** (the same three CT_PEAKER budget
breaches at 16.4 / 16.7 / 16.8 %), **D-4 PASSES on both sides**. The accurate
input therefore moves a *protective* metric **against** the model (+0.33 TWh of
measured forced coal) and is kept anyway — rule 14 as written — landing at 4.77 %
against a 30 % budget. C8 **as gated today** cannot have moved at all: the scorer
reads the bundle's committed `legitimacy_diagnostics.json`, which was
deliberately **not** overwritten.

**PJM 2022 is repaired but NOT re-scored** (freeze ACTIVE; a measured input is
applied consistently across all years, but its committed diagnostics stay on the
pre-repair basis). **Cross-ISO:** MISO 6.16 / NEISO 4.27 / CAISO 0.29 TWh still
carry the defect; `--iso` is required so one lane cannot move another's gates
(rule 25) and only PJM was run.

### pjm-160 task 2 — the F3 gap was **`load_demand_META`, not `load_demand`**: B1 and B3 CLOSED for PJM 2019 (2026-08-06)

`results/calibration/FINDING-pjm160-f3-demand-profile-closure-2026-08-06.md`.
Channel-1 data intake, zero LP solves, freeze ACTIVE and untouched, `final` still
EMPTY.

**The blocker was recorded one layer away from where it lived, and that is why
four ISOs routed around it.** The register and the pjm-159 assessment both had it
as the demand driver (*"`load_demand('PJM', 2019)` raises"*). Measured at HEAD:

```
load_demand(iso, 2019) and (iso, 2020)      : OK for ALL SIX ISOs
load_demand_meta(iso, 2019) and (iso, 2020) : RAISES for all six
```

`load_demand` has resolved through the per-BA `DEMAND_LOADERS` adapters since
every ISO gained one (`PJM hourly.parquet` covers **2018-2026**); the
demand-profiles parquet is only the fallback. The gap was one function wide —
`load_demand_meta` falls through to `eia_demand_meta.parquet`, which starts at
2021 like the profiles file it summarizes. That single `ValueError` blocked
`build_calibration_reference._demand_totals` and with it the whole `isos.PJM.2019`
block.

**Fixed at the curation seam** (`data/raw` is immutable; nothing appended, no new
raw artifact): `curate_demand_profile` gains `PRE_WINDOW_YEARS = (2019, 2020)` and
`curate_pre_window()`, sourcing each series from **the ISO's own `DEMAND_LOADERS`
adapter** — the exact series `load_demand` serves — so the pre-window meta is by
construction the summary of the demand the LP would dispatch against. 12 partitions,
6 ISOs × 2 years, 0 impossible hours. 2021-2025 untouched.

| blocker | status |
|---|---|
| **B1** 2019 unsolvable | **CLOSED** — `isos.PJM` = [2019, 2021…2025]; `PJM_2019_renewable_capacity.csv` built; readiness probe reports **`2019: SOLVABLE`** |
| **B3** locked-test C3a on a different statistic | **CLOSED at the source** — `actual_lmp.json` PJM 2019 carries `rt_lw 26.54 / da_lw 26.56` |
| **B2** year-keyed recipe | **STANDS** — owner decision, untouched |
| **B4** DA-RT regime flip | **STANDS, SHARPENED** — on the gate's own load-weighted basis 2019 is **+0.02** vs +0.96/+0.29/+0.78 in training |

**The readiness probe now tests instead of quoting.** `check_solvability` carried a
hardcoded `demand_years = [2021…2025]` *"taken from the register's measured
statement rather than re-read here"*; it now calls `load_demand` /
`load_demand_meta`. The assumption is what produced the wrong answer.

**Two defects found, reported, not buried (rule 14).**

1. **PJM 2020 `peak_mw` is wrong by ~47 GW** — top hours 192,229 / 176,085 against
   a 145,428 third-highest; `max/median` **2.26** where every other PJM year is
   1.66-1.75 and this module's own docstring derives a ≤ 2.1 envelope. They survive
   because the loader spike screen fires at 2.5× median and the curator's bounds
   screen at 5×. **Not fixed here** — the root cause is a threshold in a shared,
   solve-affecting loader screen that every training year runs through (its own
   cross-ISO sweep + keeper re-verification), a second pre-window-only screen would
   stack two mechanisms on one phenomenon (rule 19), and inventing a threshold is
   rule 5. **Consequence: PJM 2020 is deliberately NOT added** to
   `CALIBRATION_YEARS_BY_ISO` — a reference block is where a wrong `peak_mw` would
   hide. **This is the open item for whoever wants the 2020 ladder rung.**
2. **The committed 2023-2025 `rt_lw` rows do NOT re-derive** (assessment §9 item 2
   asked for this check): PJM gives **29.58 / 31.36 / 45.89** at HEAD against the
   committed **29.55 / 31.31 / 45.80**, because PJM's load weights moved when
   `load_demand` switched to the per-BA extract and gained the dropout/spike
   screens. **Restored, not landed** — `rt_lw` IS a gate input (the scorer reads it
   off the bench part, which re-renders from this file on the next registration),
   so refreshing it would silently move C3a for six ISOs. Cross-ISO and
   owner-visible, not a side effect of a PJM data task.

**`calibration_reference.json`** moves 152 numeric fields across existing blocks —
inspected, not waved through. It is the `curate_demand_profile` repair finally
reaching the reference: PJM 2021 `peak_mw` **2,147,480,000 → 149,590** and
`total_twh` **4,902.59 → 796.52**; MISO 2021/22/24 `min_mw` **0.0 → ~52 GW**. Both
sentinels are named in that script's own docstring as the defects it exists to
repair. **Verified not a gate input before landing:** `calibration_verdict`,
`legitimacy_diagnostics` and `audit_keepers` never read the file; the solve reads
only the top-level `henry_hub_actual` table (unchanged); the one solve-side use of
`isos.*` is a printed report.

**Cross-ISO:** the 12 partitions let CAISO / NYISO / NEISO / MISO add their own
pre-2021 reference blocks whenever their lanes want them — the *"extending it is
not a <ISO> task"* comments in `build_calibration_reference.py` no longer describe
a real obstacle. **This session adds no other ISO's years.**

### pjm-160 addendum — owner decisions, a B2 correction, and the new sequencing (2026-08-06)

`results/calibration/ASSESSMENT-pjm160-final-declaration-2026-08-06.md` §10.

**The four answers.** B2 → **derive the ladder** (as recommended). B4 → **wait for the price
lane** (against recommendation, recorded as decided). B5 → **refresh `rt_lw` cross-ISO
first** (as recommended). Freeze → **HOLD** (against recommendation). **Net: `final` stays
undeclared, the freeze stays ACTIVE on its 2026-07-25 basis, no year is spent.**
`holdout-freeze.json` is untouched — "hold" is the status quo, so there is nothing to write.

**CORRECTION — B2 is worse than pjm-159 §3.1 stated, and pjm-160 propagated the error.**
The claim was that outside the ladder years the ladder no-ops *and the rule-19 firm
scheduled-export floor fires in its place*. **It does not.**
`inject_reference_price_firm_export` applies a floor only for a neighbour carrying a
`firm_export_floor_by_year` entry for the year and returns `False` otherwise; both PJM
neighbour specs carry `{2023, 2024, 2025}` and nothing else. The gate site's own comment says
it: *"no ladder entry AND no floor entry, so both paths no-op identically."* **So outside
2023–2025 the keeper's seam runs with NEITHER mechanism**, leaving only the bare economic
tranches — a stronger form of B2, not a weaker one. The error survived because
`_pjm159_final_readiness.py` reports `rule-19 floor fires: True` from a **source-text check
that the branch exists** (`"if not _pjm_ladder_active and inject_reference_price_firm_export"
in nodes`), which was read as a year-aware test. The probe line should be re-worded or made
year-aware by whoever next touches it.

**The correction reaches BACKWARD.** `results/calibration/pjm2022_touchpoint/run_config.json`
carries `pjm_seam_measured_ladder: true` with `2022 ∉ PJM_SEAM_LADDER_BY_YEAR`, so
**`2026-08-05-pjm-2022-touchpoint` was solved with PJM's measured seam pricing entirely
absent** — in the channel carrying the keeper's largest single-signed volume error (net export
−9.57/−9.17/−5.40 TWh, one-signed under-export in all three in-sample years). Its NOT-YET is
on exactly two criteria: **C1** (`CC_REGULAR` +18.28 TWh) and **C3b** — and net-export error
lands in `CC_REGULAR` volume. **Hypothesis, not finding**: nothing here re-scores 2022; every
number is a committed-artifact read with no model output produced. But it is testable, and
deriving the 2022 ladder is the direct test. **Scope the authorized B2 derive to 2019, 2021
AND 2022**, not 2019 alone.

**Sequencing (owner directive).** *"After 2022 passes we will run a 2022-2035 forecast test on
the keeper formula before testing any further holdout years and then 2021 will be the next
touchpoint testing year."* → step 0 prep (ladder derive + `rt_lw` refresh, **ungated**) →
step 1 **2022 passes** → step 2 **2022–2035 forecast test** (running it is unrestricted;
registers on the **separate** forecast dashboard via `register_forecast_run.py`, never the
backcast registry; scoring its 2022 leg against measured actuals remains gated) → step 3
**2021 touchpoint** → step 4 **2019**, the one-touch year. Coherent with B4 = wait (the locked
year moves further out); **raises B5's priority** (2022 and 2021 are scored on `rt_lw` too, so
the vintage should be settled before either is re-run).

**One scheduling conflict, recorded not resolved:** step 1 cannot start under the held freeze
— `frozen_operations` are exactly solve/score/registration for every out-of-training year,
validation tier included. The established remedy is a narrow 2022-only lift with a
same-session re-arm (used 2026-08-05 PJM+NEISO and 2026-08-06 NEISO), which leaves 2021, 2020,
2019 and H1-2026 protected. **Not requested and not taken here** — the HOLD stands.

**B4's exit condition is still unnamed.** Candidates: the no-MIP mandate changes; a proposal
clears the 0.25 falsification bar (FINDING-pjm159 §4); or the step-2 forecast test supplies the
evidence — the third would fold B4 into the sequence instead of leaving it open-ended.

Next shorthand: **pjm-161.**

## 2026-08-06 — RECORD CORRECTION (owner decision D-23, cross-ISO): the "precedent that should settle it" rested on a FALSE premise — NEISO's locked test was never spent

**GOVERNANCE lane, committed artifacts only. No solve, no scoring, no year touched,
no PJM lane state changed, no PJM marker granted or withdrawn. Correct-by-addendum —
the pjm-159 entry this corrects is left intact, as is the pjm-160 addendum that
follows it (checked this session: pjm-160 does **not** repeat the claim).**

**THIS ONE IS LOAD-BEARING FOR AN OPEN PJM DECISION, which is why it gets its own
entry rather than a footnote.** The pjm-159 `final`-declaration argument in this log
(§ *"The precedent that should settle it"*) reads:

> "NEISO's locked test was spent 2026-07-07 on
> `2026-07-07-neiso53-winter-fuelsec-coldsnap`; the keeper moved to `neiso-54` the NEXT
> DAY and stands at `2026-08-05-neiso-83-ca1-reclass` — **thirty keeper generations
> later.** Its honest out-of-sample number describes a model that no longer exists and
> is never re-grantable."

**The premise is false and the cited precedent does not exist.** NEISO's locked test
was **never granted and never spent**: no NEISO 2019 or H1-2026 year has ever been
solved, scored or registered (every NEISO registry sidecar ever committed declares
years drawn only from {2022, 2023, 2024, 2025}; `bench/NEISO/` holds 2022–2025;
`actual_tail.json` has no 2019 row; the memo cited as the authorization never mentions
2019, and the one-shot it *did* authorize was on **2022** and was held the same day).
The id named as the "frozen config" is a **TRAIN-tier 2023–2025 run**. There is no
"honest out-of-sample number" describing a superseded NEISO model, because there is no
out-of-sample number.

**What this does to the pjm-159 argument.** The *conclusion* — HOLD, do not declare PJM
`final` — is **untouched and not revisited here**; this correction neither grants nor
withdraws anything for PJM, and the B1–B4 blockers stand on their own evidence. What
is withdrawn is one *supporting analogy*. Note the direction of the error: the analogy
was deployed as a **caution** ("look how fast a spent one-shot goes stale"), and the
true state of the record — *nobody has ever spent one* — is if anything a **stronger**
caution, because the program has no worked example of a locked-test spend at all. A
future PJM session must not cite NEISO as precedent for either half of the question:
NEISO is not an example of a spent one-shot, and it is not an example of a foreclosed
one. Its own `final` answer is **NOT YET** on independent merits (2019 unsolvable at
HEAD; C3c non-discriminating in 2019).

Citation chain: `results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
`docs/third-party-peer-review-2026-07.md` §6.3 item 1 → **owner decision D-23, SIGNED
at the 2026-08-06 sitting Addendum X.6**. Full record:
`docs/handoffs/neiso-record-correction-2026-08-06.md`. *(The same false premise appears
in `results/calibration/ASSESSMENT-pjm159-final-declaration-2026-08-06.md` §8 and its
§1 summary. That file is an immutable per-run session record and was deliberately NOT
rewritten; this entry is the live correction for the PJM lane.)*

### pjm-160 (cont.) — B5 refresh landed; is the seam ladder forecastable? **No, by design** (2026-08-06)

**B5 EXECUTED (owner-authorized).** `rt_lw`/`da_lw` refreshed across all six ISOs for
2023–2025, propagated into all 17 committed bench parts, every keeper re-scored, status
shards rebuilt. **17 of 18 ISO-years move (−0.08 to +0.31 $/MWh); NO determination flips and
NO C3a criterion flips in any lane**, largest shift 0.8 pp (ERCOT 2024 +3.3 % → +2.5 %).
`audit_keepers.py` 0/0. Done as ONE pass because `rt_lw` is a gate input the scorer reads
off the bench part — refreshing the reference alone would have moved C3a for six ISOs
silently at whatever moment each next registered. **Attribution checked, not assumed:** an
early baseline showed NYISO flipping NOT-YET → CALIBRATED-WITH-CAVEATS, but scoring NYISO at
`origin/main` with the tree stashed already returns CALIBRATED-WITH-CAVEATS — that flip is
caiso-179/neiso-88/nyiso's, not this change's.

**OWNER QUESTION: is seam pricing a forecastable mechanism? Answer: the measured ladder is
NOT, and the repo already knows it.** `inject_pjm_seam_ladder_prices`'s own docstring:
*"forecast years fall through to the gas-elastic reference-price formula, the `hr_by_year`
two-track design."* So PJM's seam has **two tracks**, selected by year:

| track | years | prices the bands by | rule-13 forecastable? |
|---|---|---|---|
| measured ladder | **2023–2025 only** | Q-Q duration coupling of settlement tie flows × measured DA LMP | **NO** — needs that year's realized flows and prices |
| gas-elastic reference price | every other year, backcast **and** forecast | hurdle-gated gas × heat-rate × load-shape | **YES** |

**CORRECTION to the §10.2 addendum above** (`ASSESSMENT-pjm160` §11.2): "outside 2023–2025 the
seam runs with NEITHER mechanism / bare economic tranches" was **too strong**. The bands are
still priced — by the gas-elastic formula; `_inject_seam_ladder` returning `False` leaves the
reference-price values in place rather than zeroing them. Accurate statement: **outside
2023–2025 PJM's seam runs the FORECAST track.** §10.2's substance survives (a touchpoint or
locked year does not run the keeper's own seam representation); its severity was overstated,
and §10.3's 2022 hypothesis should read *"ran the forecast-track seam"*, not *"ran with no
seam pricing"*. The §3 probe line is annotated with a forward pointer so this does not
propagate a fourth time.

**B4 DECIDED (owner): the 2022–2035 forecast test is its exit condition.** Note the test will
run on the **gas-elastic track** by construction, so it characterises the seam the *forecast*
uses and **cannot validate the measured ladder** — worth stating in that test's charter.

**The larger point, and the strongest argument for the owner's sequencing:** the keeper is
calibrated *with* the measured ladder and the forecast runs *without* it — a real
backcast→forecast representation gap sitting in PJM's largest single-signed volume channel,
which is exactly what rule 22's crossover window exists to measure.

**OPEN, not adjudicated — the 2022 question now has two defensible answers.** *"Does the
keeper reproduce 2022?"* → derive the 2022 ladder first. *"Does the thing we will actually
forecast with reproduce 2022?"* → leave 2022 on the forecast track and read its C1/C3b miss
as information about the **forecast** seam, which makes the already-spent result more
valuable than §10.3 implied. Owner choice; this session ends on it.

Next shorthand: **pjm-161.**

### pjm-160 (cont.) — B2 EXECUTED: seam ladders derived for 2019, 2021, 2022 (2026-08-07)

Owner decision on the reframed 2022 question: ***"Does the KEEPER reproduce 2022?" — derive
the ladder first.*** Done. `PJM_SEAM_LADDER_BY_YEAR` now carries **2019, 2021, 2022, 2023,
2024, 2025**; the 2023–2025 entries are **byte-identical** (verified against the prior file).

**Rule 23 basis: the SOURCE DATA EXTENDS, not a residual.** `derive_pjm_seam_ladders.py` ran
the **frozen** formula — no script edit — over inputs that already covered these years:
`PJM_<year>_import_export_act_sch_interchange.csv` (2018–2025 on disk) and
`actual_lmp_hourly_PJM.parquet` `da` (2018–2025). **No parameter is introduced.**

**Reproduction quality of the added years matches 2023–2025** (offline P9, per seam):

| year | DA anchor | MISO | NYISO | Carolinas | TVA | LGEE |
|---|---:|---|---|---|---|---|
| 2019 | $25.54 | −30.81 vs −30.79 | −11.92 vs −11.92 | +2.37 vs +2.37 | +5.68 vs +5.69 | +3.07 vs +3.08 |
| 2021 | $36.87 | −32.09 vs −32.09 | −13.44 vs −13.45 | +1.33 vs +1.32 | +4.93 vs +4.93 | +1.46 vs +1.47 |
| 2022 | $67.30 | −28.40 vs −28.46 | −14.11 vs −14.12 | +2.15 vs +2.14 | +6.05 vs +6.07 | +2.59 vs +2.59 |

TWh, model vs actual; duration RMSE 40–280 MW; import-hour shares within a few points; the
direction-structural signature the ladder exists to reproduce holds in every year (MISO/NYISO
0–1 % import hours, Carolinas/TVA/LGEE 52–92 %).

**What this changes.** A 2022 re-run will now run **the keeper's own seam mechanism** instead
of the forecast track, so its C1 (`CC_REGULAR` +18.28 TWh) / C3b miss becomes a test of the
keeper rather than an artifact of year-keying. **It does NOT make the ladder forecastable** —
it still needs that year's realized flows and prices, forecast years still fall through to the
gas-elastic formula, and the two-track design is unchanged.

**Nothing is spent.** This is ungated prep: no year solved, scored or registered; the freeze
is ACTIVE and untouched; `final` is EMPTY. The 2022 re-run itself still requires a narrow
owner lift. Verification: 285 seam/interchange/ladder tests pass, mechanism-matrix guard
clean, keeper re-verifies **CALIBRATED** and `audit_keepers --iso PJM` 0/0 (the keeper's own
2023–2025 solve is untouched by construction).

Next shorthand: **pjm-161.**

### pjm-161 — the 2022 touchpoint fails for TWO separable reasons; the outage envelope INVERTS in scarcity; the event-cap lever is REFUTED as built (2026-08-14)

**Nothing was spent.** The holdout freeze is ACTIVE and untouched, `final` is EMPTY, and
**no out-of-training year was solved, scored or registered.** Both arms are
`--year 2023 2024 2025`, one invocation, years sequential. Every 2022 number below is a READ
of the already-committed `2026-08-05-pjm-2022-touchpoint` bundle or of raw measured inputs.

**Phase 0 split the object in two, and neither half is a tuning residual.**

* **C1 `CC_REGULAR` +18.28 TWh — the DA-virtual layer, and the in-sample reading was
  incomplete.** The layer clears **+11.12 TWh of net virtual DEMAND** in 2022, and that is
  **not a phantom**: the raw measured curve's own rule-13 anchor at actual 2022 DA prices is
  **+12.25 TWh**, so the LP sits **1.13 TWh** from its admissibility reference — the
  **smallest deviation of any year** (in-sample −6.70 / −4.93 / +0.70). PJM's real 2022 DA
  market genuinely held ~12 TWh of net virtual demand; the model reproduces it faithfully and
  then, carrying ONE price and ONE energy balance, **serves a financial position as physical
  energy**. pjm-158's "the anchor is ≈ 0" is a property of the 2023–2025 window, not of the
  curve. At pjm-158 §5.2's measured 80 % channel that is **≈ +8.9 TWh of the miss (49 %)**,
  from a mechanism whose in-sample contribution to the same class has the OPPOSITE SIGN.
  **Escalated, not levered** — this is the architecture question pjm-158 raised, now with the
  out-of-sample measurement that makes it concrete. Nothing disarmed.
* **C3b 0.206 — Winter Storm Elliott, 96 hours.** 74.9 % of the squared error is **December
  alone** (drop it: 0.196 → 0.110, better than any in-sample year), and inside December the
  **23–26 Dec window carries 115 %** of the monthly gap from 13 % of its hours — the other 648
  hours are *over*-priced by +$7.78. The model prices the event **$100.58 vs $494.58**, runs
  **+11.5 GW more gas than actual** (+16.8 GW at peak), takes **zero** unserved energy and
  produces **zero** hours > $200 against an actual RT 34. Load in the window is EXACT.

**THE FINDING — the CAMPD outage envelope is ANTI-CORRELATED WITH SCARCITY, in every year.**
corr(derated MW, net load) = **−0.701 / −0.680 / −0.714 / −0.772** (2022–2025) and the
top-1 % net-load hours carry only **0.376 / 0.306 / 0.216 / 0.245×** the annual-mean derate.
During Elliott the envelope asserts **15,555 MW out — its lowest level of the year** —
against PJM's own published **31.1 / 35.8 / 27.1 GW forced** (40.7 GW total on 25 Dec). Cause
is the detector's construction: it infers unavailability from **zero generation**, so it
cannot see an outage at a unit that would not have run anyway, and a unit in economic layup
**runs** when prices spike. This is the **SHAPE** consequence of the neiso-63 layup finding
the holdout freeze rests on, which had only ever been stated as a LEVEL defect — annual means
in fact agree within ~7 %. It also **falsifies, for PJM, the documented ground on which
`correlated_forced_outage` is coerced off in backcast mode** ("a backcast's measured CAMPD
overlays carry the real cold events"). Measured for PJM only; no verdict transfers (rule 25),
and the other five ISOs are worth a census.

**The lever, pre-registered before either arm solved and REFUTED by its own predictions.**
`pjm_measured_outage_event_cap` (new, default off, PJM+backcast gated) — a REMOVE-ONLY,
TOTAL-outage-basis cap on the ERCOT-148/149 shape, taking pjm-145's own named re-open route
(3), zero fitted parameters. **The ex-ante probe rejected my first design before any solve**
(class grain degenerated into "every class ceilinged at the fleet mean": 282–305 of 364
binding days for 4.8–6.3 GW); the implemented form is fleet grain, 99/61/110 binding days.
Arms `2026-08-14-pjm-161-control` and `2026-08-14-pjm-161-event-cap`. **The control
reproduces the pjm-152 keeper BYTE-IDENTICALLY (max |Δ| 0.000000 TWh)**, so the field is
provably inert at default and the A/B is valid. Scorecard: **P1 PASS**, **P2 PASS exactly**
(max(avail_arm − avail_ctl) = 0.000000000000 — the pjm-145 resurrection branch is unreachable
by construction), **P5 PASS** (ΔCC_REGULAR −0.508 / −0.283 / −0.688), **P3 PARTIAL** (mean
dual up in all three, +0.19/+0.08/+0.34, but hourly MAE worse in all three), **P4 FAILED
OUTRIGHT** (C3c hours > $200 3→3, 10→10, 32→32; max price identical), **P6 passes on the
letter and fails on the substance** (corr narrows in all three but the top-1 %-net-load
unavailable MW is UNCHANGED: 23,160→23,160 / 25,403→25,403 / 24,222→24,249).

**Why: the cap adds ~zero outage in the hours it was built for.** PJM's published TOTAL is
dominated by **planned** outages, scheduled AWAY from peaks — 12.2 / 14.0 / 18.0 GW on the
top-20 peak-net-load days against annual means 33.3 / 33.0 / 35.9 — so it does not bind there;
and the **forced** component, which IS correctly signed (event/annual 1.30–2.84 every year),
is trivially inert against a 41.6 / 43.2 / 41.2 GW model envelope that carries planned
outages too. A remove-only rule cannot RESHAPE an envelope, only deepen it.

**NOT PROMOTED, and the favourable residuals are the reason for care.** No gate regresses —
both arms C1 16/16 · free 12/12, C2/C3a/C3b/C3c/C4/C8 PASS, NOT-YET only on C6 UNATTESTED
(the ordinary replay state, as at pjm-158) — and class errors move mostly favourably (2025
COAL_BIT +5.357→+3.477, 2024 CC_REGULAR +0.322→+0.039, 2025 CC_REGULAR +3.957→+3.268, against
2023 CC_REGULAR −3.451→−3.959 and 2025 CT_PEAKER +3.555→+4.821). But the mechanism **failed
its own targeting test**, and adopting it on a mixed sub-TWh residual gain after that failure
is the trade rule 1 forbids. **Keeper UNCHANGED at `2026-08-04-pjm-152-collapse`.** LOYO:
zero free parameters, so nothing is identified against any year; per-year consistency holds
(P5 negative ×3, P6 narrowing ×3, P4 null ×3).

**A third term, already repaired, that a 2022 re-spend would carry.** The registered
touchpoint reads `pjm_seam_measured_ladder = True`, but on 2026-08-05 `PJM_SEAM_LADDER_BY_YEAR`
carried only 2023–2025, so the gate `year in PJM_SEAM_LADDER_BY_YEAR` was False and the run
fell through to `inject_reference_price_firm_export` — a DIFFERENT seam mechanism from the
keeper's own years. pjm-160 landed the 2022 ladder **two days later**. So the −18.22 TWh
export shortfall is partly a year-keying artifact HEAD has already fixed — **and repairing it
makes C1 WORSE**, because exports are a sink and PJM's 2022 marginal class is `CC_REGULAR`
(+5 to +7 TWh onto a class already +18.28 over). **There is no combination of the identified
objects that makes 2022 pass, and a re-spend should not be requested as a route to one.**

**Named successors, selected by measurement.** (1) pjm-145 route (1) — the restore ceiling
composed with the structural-derate registry (port the ercot137 fix): the envelope's defect is
SHAPE not level, fixing a shape needs a mechanism that moves capacity in BOTH directions, and
route (1) is what makes restoring safe. (2) The model's envelope carries **no planned/forced
split**, which is why neither basis works; splitting the CAMPD-detected windows into
maintenance-season planned vs event-driven forced is the input a reshaping mechanism needs.
(3) The DA-virtual architecture question, owner-level, unchanged from pjm-158 and now
evidenced out of sample. Neither (1) nor (2) is opened here.

`state_carbon_pricing` was adjudicated as the prompt required and left PENDING OWNER: it is
sign-matched to 2022 and correctly year-varying (pjm-146's K3 audit already reproduces
Virginia's 2024 RGGI exit exactly), but pjm-146 measured CC_REGULAR −16.06 / −13.84 TWh
in-sample against keeper errors of −3.45 / +0.32, so arming it takes 2023 to roughly −19.5 TWh
— four times outside the band. That is the textbook fixes-2022-breaks-training signature, and
pjm-146 already named the real defect (the CC→coal substitution elasticity) as the successor.

Evidence: `PREREG-pjm161-measured-outage-event-cap-2026-08-14.md`,
`FINDING-pjm161-outage-inversion-and-da-virtual-energy-2026-08-14.md`, probes
`_pjm161_{energy_balance,virtual_2022,c3b_months,december,outage_inversion,removeonly_exante,ab}.py`
and their committed `_pjm161_*.json` records.

Next shorthand: **pjm-162.**

### pjm-162 — route (1) is ANTI-TARGETED; the availability family closes on a CAPACITY-BASE mismatch; `final` readiness assessed NOT-YET (2026-08-15)

**Nothing was spent.** The freeze is ACTIVE and untouched, `final` is EMPTY, and **no
out-of-training year was solved, scored or registered.** **No LP was solved at all** — this is
the pjm-145 / ERCOT-145-146-147 no-solve-closure pattern, so there is no pre-registration
(there is no arm to pre-register) and no dashboard registration (no run exists).

**TASK A — the named successor, refused on its own prerequisite check.** pjm-161 §7.4 selected
pjm-145 **route (1)** — "restore ceiling composed with the structural-derate registry (port the
ercot137 fix)" — and the session prompt required Phase 0 to decide first whether it needs a
planned/forced split of the model's envelope. Phase 0 answers a harder question than the one
asked, and the answer kills the route.

**THE DIRECTION TEST.** A bidirectional water-fill repairs a SHAPE defect only if it moves the
envelope the right way in the hours the shape is wrong; pjm-161 measured the envelope as too
SHALLOW in scarcity, so route (1) must REMOVE on high-net-load days. Measured net signed MW
(`_pjm162_route1_phase0.json`; **+ = RESTORE**), over the covered fossil-thermal classes:

| year | basis | all | top-10 % NL | **top-1 % NL** | **winter event** |
|---|---|---:|---:|---:|---:|
| 2023 | total / unplanned | +8,048 / +25,720 | +12,237 / +12,237 | **+10,367 / +10,367** | **+7,614 / +11,227** |
| 2024 | total / unplanned | +9,882 / +27,671 | +11,411 / +11,412 | **+12,354 / +12,359** | **+9,241 / +11,493** |
| 2025 | total / unplanned | +4,984 / +22,877 | +6,521 / +6,919 | **+6,961 / +7,024** | **+2,166 / +3,109** |

**Twenty-four of twenty-four cells RESTORE.** Route (1) would hand capacity BACK exactly where
the defect is that it is too shallow. A restore CEILING bounds how much is restored; it cannot
change the SIGN. **Refused ex ante, no solve.**

**WHY — and it is NOT the outage-type split the prompt asked about.** The cause is a
**CAPACITY-BASE mismatch** neither pjm-145 nor pjm-161 named. **19.2 / 20.4 / 19.2 % of the
model's fossil nameplate sits at HARD ZERO every day** (layup, retiree CEMS caps, COD masks,
full windows) — capacity PJM's `gen_outages_by_type` does not carry as "outage" at all, being an
operational report over units in commercial operation. So the model asserts **30.3 / 31.4 /
29.9 %** of fossil nameplate unavailable against PJM's published **24.2 / 24.0 / 26.0 %** on the
same denominator, and **on top-1 % net-load days 21.3 / 25.5 / 23.8 GW against a published TOTAL
of 10.8 / 13.0 / 16.7 GW — roughly TWICE the operator's whole-system figure.** Every comparison
against that aggregate reads "the model is more derated than PJM says", on every day, whatever
the outage-type basis. The gap is about **twice** the type-composition gap a split would repair.

**THE CEILING, measured, works as advertised and is not enough.** Structural-zero resurrection
is **58.8 / 60.8 / 60.6 %** of the restore-day lift (reproducing pjm-145 §5's 66–68 % on this
envelope) — and **5.4–6.9 GW/day of living-unit restore survives it**, still pointed the wrong
way in scarcity.

**THE SPLIT IS DERIVABLE — a real result, just not the blocker.** Stratifying the CAMPD windows
by duration against PJM's published typed series separates cleanly in all four years: short
windows track published **FORCED** (r +0.09..+0.44) and **RISE** in every named winter event
(**4.35 / 9.17 / 9.88 / 6.05×**, against the published forced series' own 1.30–2.84×); long
windows track **PLANNED+MAINTENANCE** (r +0.73..+0.93) and fall (0.19–0.74×). **The kill test
passes** — forced-outage information IS present in CAMPD, in the short-duration family. It also
quantifies a genuine composition defect: the model's window envelope is **~94 % planned-like /
~6 % forced-like (≈2.1 GW)** against PJM's real **~73 % / ~27 % (forced 7.7–10.5 GW)**. The
boundary is **not sharply picked by the data** (corr positive across 2–10 d, no optimum), so any
cut is a free parameter needing a DOF entry — recorded as a derived, validated, currently-unused
input, not armed.

**IT EXPLAINS pjm-161's NULL RESULT.** The event cap added ~zero outage in the top-1 % hours
(P4/P6) because **there was no room**: the model was already ~2× more derated than the published
total there. A cap that can only deepen cannot bind against a target it is already below.
**Correction stated against interest:** pjm-161's inversion measurement (corr −0.68..−0.77 on the
window family) STANDS, but the conclusion drawn from it — "the envelope is too shallow in
scarcity" — does not survive comparing the WHOLE envelope against the operator's record. Both are
true of different objects; the prescription that followed from the shorter one is not supported.

**CLOSED (DO-NOT-REDO).** The whole "compare the model's availability envelope against PJM's
published aggregate" family: route (3) `R` (pjm-161), route (1) refused here, and the refusal
GENERALISES because the capacity-base gap is a property of the comparison, not of any transform
over it. Only pjm-145 route (2) survives — a class/unit-resolved PJM source — which is
**data-blocked** (PJM publishes no GADS-style unit detail). **Redirection, the session's most
consequential output:** PJM's scarcity defect is **not** an availability defect; three sessions
have now spent their lever on that hypothesis. The next PJM scarcity lever should come from price
formation, imports or the demand side.

**TASK B — `final` readiness: NOT YET**, on the merits, four independent grounds, any one
sufficient (`ASSESSMENT-pjm162-final-readiness-2026-08-15.md`). Grants nothing; `final` untouched.

* **(a) The keeper re-verifies CALIBRATED at HEAD rubric, every criterion PASS, zero caveats, governance
  attested** (`calibration_verdict.py --run-id 2026-08-04-pjm-152-collapse`, no solve; C1 16/16
  free 12/12). `audit_keepers.py --iso PJM` **0 failures / 0 warnings**. Ground (a) is satisfied
  and is NOT what blocks. (The bundle's own `metrics.json` still reads NOT-YET — the frozen
  pre-attestation record pjm-153 later fixed; the marker already documents this.)
* **(b) The DA-virtual escalation IS a blocker, and it is now MEASURED for 2019** rather than
  assumed (`_pjm162_virtual_2019.json`, no LP — PJM's own submitted DA curves at PJM's own
  published 2019 DA prices, pjm-158's helper chain unchanged). **2019 net DA virtual position =
  +7.08 TWh**, against **−0.82 / −2.11 / −0.84** in 2023-2025 on the same RTO hub-mean basis:
  **3.4× the largest training-year magnitude, the opposite sign to two of three, and 60 % of
  2022's** (+11.71 on the same basis — which also validates the basis, matching pjm-161's +12.25
  canon). 2019 is a **2022-like year for this layer**, not a training-like one. At pjm-158 §5.2's measured ~80 %
  channel that is **≈ +5.7 TWh of phantom physical energy on `CC_REGULAR`** — larger than the
  keeper's entire in-sample CC_REGULAR error range (−3.45 / +0.32 / +3.96). *Basis note:*
  pjm-161's headline used the canonical committed system DA series; 2019 has no bundle and hence
  no canon series, so every cell above is on the hub-mean basis and is internally like-for-like.
  *And the uncertainty runs the wrong way:* ±$5 around actual DA moves the anchor +25.3 → −10.0
  TWh, and the model's own 2019 price error is unmeasurable without spending the year — so the
  result would be **uninterpretable**, which is exactly what a touch-once tier must not be spent
  on.
* **(c) The 2022 arithmetic confirms no passing combination** (−8.9 TWh virtual-phantom removal
  vs +5 to +7 TWh seam repair, against a +18.28 TWh miss). It bears on `final` because declaring
  it would spend the touch-once tier while the ITERABLE tier below it is unresolved — and, per
  (b), spend it on the year where the same unresolved cause is largest.
* **(d) The freeze is ACTIVE and its lift condition is unmet — and this session quantified PJM's
  share of the residual the freeze names rather than closing it** (§4 above; the 2026-07-26 `held`
  entry's "a residual over-count survives the guard", now located and measured for PJM).

**What would change the answer:** (1) the owner lifts the freeze or closes the merit-order-guard
charter with cause; (2) the DA-virtual architecture question is DECIDED — a ruling that the layer
stays as-is with the artifact disclosed also unblocks, provided the +7.08 TWh is on the record in
advance, which is why it is measured now rather than after the fact; (3) an explicit owner
disposition of 2022.

**Matrix (rule 28b):** `dam_availability_rebasis` stays **`G`** with its re-open condition (1)
recorded CLOSED ex ante; `pjm_measured_outage_event_cap` **`R`** — pjm-161's stranded verdict,
landed this session (its own git write path returned 403 throughout). No cell is armed. **Keeper
UNCHANGED at `2026-08-04-pjm-152-collapse`.**

Evidence: `FINDING-pjm162-outage-envelope-basis-closure-2026-08-15.md`,
`ASSESSMENT-pjm162-final-readiness-2026-08-15.md`, probes
`_pjm162_{route1_phase0,split_derivability,split_threshold,virtual_2019}.py` and their committed
`_pjm162_*.json` records.

Next shorthand: **pjm-163.**


---

## pjm-163 — 2026-08-16 — KEEPER PROMOTED: `2026-08-15-pjm-162-inputclock` (DEBUG-B corrected-input replay); O2 resolved; ≤2022 clock-extension chartered

**Session:** DEBUG-manager reissue (`claude/fable-debug-manager-reissue-t8dg4w`, off main
`8a118e7`), serving the plan §8 director dispatch. **No solve** — promotion mechanics only
(the candidate bundle was held from the BLOAT-B-3 prune precisely so promotion needs no
re-solve). *(Shorthand note: the dashboard run id `2026-08-15-pjm-162-inputclock` was minted
by the DEBUG-B lane and collides numerically with this log's pjm-162 outage-envelope session
— unrelated work. This sitting takes pjm-163 per the previous entry's "next shorthand"; the
run keeps its registered id.)*

**O2 resolved first** (audit gap register row; one-paragraph note in
`docs/handoffs/debug-sweep-2026-08.md` Addendum §A.1): the DEBUG-B finding table's "incumbent
C6 UNATTESTED / NOT-YET" was the **registration-time rubric-2.9 snapshot** (pjm-152 shipped
without an attestation; pjm-153 retro-generated it with computed premises), not scorer drift.
Definitive `calibration_verdict.py --run-id` re-score at `8a118e7`: **pjm-152 = CALIBRATED /
C6 PASS; pjm-162 = NOT-YET solely on the missing promotion-time attestation** — so the
promotion bar applied was the full not-worse-than-CALIBRATED bar, not a NOT-YET-vs-NOT-YET
tie-break.

**Owner card (in-session, BLOAT-B-5 sitting pattern): PROMOTE signed.** Second card: **≤2022
+1 h fueltype extension CHARTERED** (executed as a separate data-repair commit this session —
no ≤2022 year solved/scored/registered; freeze untouched).

**Promotion mechanics executed (order matters, D-5(b)):**

1. **Attestation** written into `results/calibration/pjm_debugb_inputclock_A/` by
   `scripts/gen_pjm163_inputclock_attestation.py` — every premise **computed, none typed**
   (the pjm-153/gen_* precedent): recipe identity vs incumbent (0 shared-value diffs;
   keeper_only = 6 `coal_tranche_*` schema deletions at HEAD; 45 arm_only drift fields all at
   HEAD defaults, non-falsy ones individually PJM-unreachable — rule-25 prefixes,
   `storage_measured_base_fleet` scoped to `STORAGE_MEASURED_BASE_FLEET_ISOS={CAISO}`,
   statutory `ira_ptc_credit_window_years=10` consumed only by the forecast new-entry screen;
   2 since-deleted fields recorded falsy); July `NG: SUN` centroids recomputed from the
   committed parquet **11.90 / 11.93 / 12.03** (gate [11.5, 12.3]); verdict parity (incumbent
   CALIBRATED; arm's sole pre-attestation blocker C6); **DOF ledger carried VERBATIM 19/6**
   (a blind `build_dof_ledger.py` rebuild measurably drops curated entries — `--check` reads
   STALE on the incumbent's own committed ledger, the nyiso-8x failure mode).
2. **Re-verify before landing:** `calibration_verdict.py --run-id 2026-08-15-pjm-162-inputclock`
   → **CALIBRATED**, every criterion PASS, C1 16/16 free 12/12, zero caveats/fails; C8
   grounded notes carry over (CT_PEAKER 16.2/16.4/16.7 %, ST_GAS 2025 39.9 %). **NOT WORSE —
   identical criterion-for-criterion.**
3. `keepers/PJM.json` re-pointed (promotion note carries the O2 correction);
   `build_status.py --iso PJM` → `status/PJM.js` [PJM:CALIBRATED].
4. `calibration-complete.json` PJM entry **re-keyed** (keeper + determination re-verification
   text; `keeper_at_declaration` untouched). One `audit_keepers` lesson worth recording:
   M1b's token extractor reads the FIRST bare determination token in the prose, so the
   marker's touchpoint aside must not name the touchpoint's verdict token — reworded.
5. `audit_keepers.py --iso PJM --check` → **PASS 0/0** (M1a/M1b, holdout, status).
6. **Rule-28 re-stamps** (the duty finding §4 deferred to promotion):
   `mechanism-matrix/PJM.js` `updated`/`keeper`/`gates` stamps + `diurnal_price_amplitude`
   and `seam_flow_envelopes` evidence annotated **pre-repair-basis, verdicts NOT
   re-adjudicated** (G and K stand); §5.3 prose header re-stamped.
   `check_mechanism_matrix.py` green, zero warnings.

**Blast radius (measured at registration, re-cited here):** bench/PJM `2023.json.gz` +
`2024.json.gz` recomputed; `2025.json.gz` byte-identical. Rule 14 never invoked — nothing
worsened at the corrected inputs.

**Superseded keeper `2026-08-04-pjm-152-collapse`:** stays on the dashboard under the
2026-08-09 site-retention directive (remediation record of the 2022 touchpoint); its
pjm-153 promotion note is preserved in this log (2026-08-04 entry) and in its bundle
attestation. The 2022 touchpoint record stands as scored — measured on the pre-repair clock;
any future 2022 iteration (owner freeze-lift required) measures against the corrected
instrument.

Next shorthand: **pjm-164.**

## pjm-164 — 2026-09-01 — C3c program Q1: the reserve-dual channel is REAL, not the ercot-214 phantom (zero solve; keeper untouched)

**Charter:** `docs/CHARTER-c3c-scarcity-program-2026-08-31.md` Q1 — audit whether the PJM
keeper's C3c PASS (the program's only existence proof that this LP class can form a scarcity
tail) rides an ercot-214-shaped phantom channel. **Zero solve — committed artifacts + in-repo
published data only.** State re-verified first: `2026-08-15-pjm-162-inputclock` CALIBRATED,
every criterion PASS, `audit_keepers --iso PJM` clean.

**Verdict: REAL — charter Q2 proceeds.** Full record:
`docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`; per-year counts/shares/hour lists:
`results/calibration/_pjm164_c3c_overlap.json`.

- **Construction** (caiso-144 §D overlap, replicated to the gated basis): the PJM payload has
  no `overlay` key, so C3c scores the energy-only fallback — hours where the max-across-zones
  P1 energy dual > $200. Replication matched the payload exactly (4/10/32 vs actual 6/18/59).
- **T1 overlap** (model tail ∩ actual RT >$200): **0/4, 1/10, 14/32** (share of actual tail
  0.00/0.06/**0.24**). 2025 is NYISO-shaped (right hours — the June 23–25/July 28–29 heat
  events; dual sum $258 in the hour reality printed $1,722); 2023–24 have near-zero overlap
  but also near-zero reserve involvement (channel fires **0 h in 2023**, 2 h in 2024).
- **T2 (data in-repo:** `data/raw/PJM-AS/reserve_market_results_<year>.parquet`**):** PJM
  reality priced hourly-mean reserve MCP >$25 in 92/235/391 h; in the model's 29 binding
  hours of 2025 the published MCP p50 was **$88** (max $1,614, same days) — versus
  ercot-214's RTORPA p50 $14.2 in its contaminated hours. The mechanism is the market's own;
  reality's >$200 tail hours are themselves reserve-priced (2025: 46/59).
- **T3 load-bearing check:** without the channel the 2025 tail brackets to 5–30 h vs band
  [29.5, 118] — strict removal FAILs, dual-subtracted passes by one hour. The channel **is**
  load-bearing for the 2025 PASS; legitimate, since it is real.
- **Caveats recorded unrewritten** (none determination-level): the 2023 PASS is small-count
  guard + a mis-timed 4-hour July congestion episode (0 reserve hours — cite **2025**, not
  2023, as the existence proof); the channel under-fires reality's reserve pricing ~10× and
  misses the winter-morning face entirely; 2024's tail is congestion-formed and mostly
  mis-timed. These belong to the program synthesis, not this lane.

No keeper/shard/marker/determination change; no fix; no matrix cell moved (nothing tested —
`energy_reserve_coopt` PJM stays K, `ordc_scarcity_overlay` PJM stays G). Cross-ISO
governance log deliberately untouched (nyiso-164 possibly parallel).

Next shorthand: **pjm-165.**

## pjm-165 — 2026-08-31 — C3c program Q1 INDEPENDENTLY REPLICATED: REAL, by a different construction (zero solve; keeper untouched)

**Charter:** `docs/CHARTER-c3c-scarcity-program-2026-08-31.md` Q1, under owner ruling R-E
(which chartered Q1+Q2 in one grant). **Zero solve — committed artifacts + in-repo published
data only.** Keeper re-verified at open and close: `2026-08-15-pjm-162-inputclock`,
CALIBRATED. Record: `docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md`; probe
`scripts/probes/c3c_q1_pjm_phantom_audit.py` → `results/calibration/_c3c_q1_pjm_phantom_audit.json`.

**PRIOR ART — this is a REPLICATION, not a first execution.** Q1 was already executed by
**pjm-164** (`docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`), which returned REAL.
This lane ran in parallel and did not see that record until after its own measurement. **The
verdict is pjm-164's first.** This entry records an independent construction reaching the same
answer, plus four legs their record does not carry.

**Verdict: REAL — agreeing with pjm-164.** Different construction: pjm-164 overlapped the
model's C3c *tail hours* against the actual RT LMP tail; this overlaps the model's
*positive-reserve-dual hours* against PJM's *published reserve-market record*
(`data/raw/PJM-AS/reserve_market_results_<y>.parquet`, service PR, locales PJM_RTO + MAD).

- **Provenance is an EXACT IDENTITY** (new): model `requirement_mw` == published `as_req_mw`
  + the published 190 MW ORDC outer breakpoint in **8,735/8,735/8,759 covered hours per
  family — 26,229 family-hours, zero exceptions**, lag scan r = 1.00000 at 0.
- **Channel census** (new): ORDC shortfall identically **0 in all 52,560 family-hours**; the
  dual is opportunity cost, bounded by LP construction below the **cheapest published penalty
  step ($300)** and observed at most **$187.90** (63 % of it). PJM's own curve says that MW is
  worth $300 to PJM — the model never pays above what the published curve would.
- **Overlap with published severity tiers** (new, with significance): 2025 `pjm_primary`
  **18/20** reserve-priced (lift 3.66×, p 1.1e-9), **6/20** on a published ORDC penalty step
  (lift **75.08×**, p 9.7e-11), **6/20** in hours PJM was actually short (lift **90.61×**,
  p 2.8e-11). MAD: 22/29, 7/29, 2/29. 2024 is n=2 and **non-discriminating (p 0.379)**;
  2023 the family never binds at all.
- **Direction** (new): the model prices **2.7–7× LESS** than PJM posted in the same hours
  (2025 RTO mean $72.96 vs published $194.50; MAD $31.95 vs $225.23; ceiling $187.90 vs a
  realized 5-min max of $1,700/$2,550). A phantom over-prices. Consistent with pjm-164's
  "under-fires ~10×".
- **Premise correction, same as pjm-164's:** C3c scores the **energy-only** dual (no overlay
  in any year; `scarcity_price_overlay`/`scarcity_pricing_enabled` both False), and the
  channel is load-bearing in **2025 only** — 2023: 0 of 4 tail hours have a positive dual;
  2024: 2 of 10 (max $8.49); 2025: 27 of 32. Cite 2025 as the existence proof.
- **NEW CAVEAT neither lane carried — an alignment exposure.** PJM's `_dt_ept` is
  **prevailing** (measured: UTC−`_dt_ept` = 4 h in 409,464 rows, 5 h in 219,528) while the
  model's PJM clock is `Etc/GMT+5`. The §2 identity proves the model's reserve *requirement*
  rides the prevailing positional index, so the dual-vs-price comparison is self-consistent —
  but an offset scan shows the model running **ahead**: energy dual vs actual RT LMP peaks at
  **lag −1** in 2023 (0.4096 vs 0.3997) and 2025 (0.6529 vs 0.5906), 2024 a tie; and mean
  published reserve MCP in the model's positive-dual hours by lag is −2 $368 / −1 $303 /
  0 $175 / +1 $62. **All overlaps are reported at lag 0, which the scan shows is the WEAKEST
  alignment — the counts are a lower bound and the verdict is robust.** Whether this is a
  requirement-placement issue against the EST energy clock (the `pjm-162` "inputclock" family)
  or genuine lead is **NOT diagnosed here** — flagged for a future PJM lane, and the 1–3 h
  "lead" in the hour table must not be read as established model behaviour.

No keeper/shard/marker/determination change; nothing armed; no `ScenarioConfig` field.
**No matrix cell moves and no shard edited** — duty (b) not triggered (nothing tested or
adjudicated; `energy_reserve_coopt` PJM stays **K**), duty (c) not triggered. Rule 25: this
PJM finding enters no other ISO's shard.

## pjm-166 — 2026-09-06 — the held-out C1 object is NOT a merit-order-position object (phase 0 refutation + the same-HEAD control)

**Dispatch:** take PJM's gas-over / coal-under C1 signature on the 2021/2022 touchpoints back
to 2023-2025 as an object (rule 22 step 3), starting zero-LP (rule 29 `[R-SCREEN]` clause 0),
and close the open HEAD-drift limit the touchpoint assessment named
(`ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05` §4 i / §5 item 2).
**Keeper UNCHANGED** at `2026-08-15-pjm-162-inputclock`; no mechanism armed, swept or tuned;
no `ScenarioConfig` field touched; no cell verdict moved; no held-out year solved, scored or
registered. Record: `results/calibration/FINDING-pjm166-c1-object-phase0-2026-09-06.md` +
`PRECOMMIT-pjm166-c1-object-2026-09-06.md`.
*(Session renumbered off the SPENT `pjm-164` and `pjm-165` labels — both consumed by the
C3c-program Q1 sessions of 2026-08-31/09-01; the log's own "Next shorthand" was already
**pjm-166**. nyiso-121 precedent.)*

**THE DISPATCH HYPOTHESIS DOES NOT SURVIVE PHASE 0, and its premise is factually inverted.**
On measured EIA-923 delivered receipts, 2021 and 2022 are the two **DEAREST-gas** and two
**CHEAPEST-coal** years of 2021-2025 — gas $4.12/$7.12 (ranks 4 and 5), coal $2.07/$2.62
(ranks 1 and 2), against gas $3.26/$2.85 (ranks 2 and 1) in 2023/2024 — not "the cheapest
delivered-gas year in the span". Three independent kills, all zero-LP on committed artifacts:
**(1) the sign test fails** — `CC_REGULAR` over-runs **+28.7 / +22.3 TWh in the two
dearest-gas years** and only **−3.4 / +0.5 TWh in the two cheapest**, the opposite of what a
too-cheap gas offer would produce; **(2) the in-sample elasticity is already right** — coal
share of (coal + `CC_REGULAR`) on `ln(delivered gas/coal)` over 36 in-sample months gives
actual `0.2637 + 0.0772·x` vs model `0.2631 + 0.0686·x`, **slope ratio 0.888, intercept gap
−0.0007**, worth 0.7 pp extrapolated against a 3.6 pp gap; **(3) coal is not saturated** —
model coal runs **0.25-0.68 of its own annual peak** in 2021's high-`ln(g/c)` months on a
*larger* 2021 fleet (36.9 vs 31.3 GW), so `COAL_BIT` −9.45 TWh is no capacity ceiling.

**IT IS NOT A REORDERING AT ALL — it is an additive fossil surplus.** Total fossil is
**+19.6 / +26.7 TWh** over measured in the held-out years against **−3.7 / −7.9** in
2023/2024, while model demand matches EIA-930 **within ±2.2 TWh in every year**. **Correction
to the standing narrative:** coal-under is **2021 only** — 2022 coal is **+2.0 TWh, slightly
over**. The touchpoint assessment's own criterion table says this; its §3.1/§5 prose
generalised past it. The hydro (−6 to −7 TWh) and oil (−1 to −2 TWh) deficits are real but
**tier-neutral** — present in every year, in-sample included — so they cannot explain a
boundary they do not cross.

**EXACTLY ONE MODEL QUANTITY CROSSES THE TIER BOUNDARY: the DA-virtual layer's net cleared
position** — `VIRTUAL_INC + VIRTUAL_DEC` = **+7.40 / +6.48 / −0.89 TWh in-sample vs −6.14 /
−9.91 held-out**, i.e. 6 to 10 TWh of net phantom **DEMAND** that physical gas must serve,
against the mechanism's own rule-13 anchor of ≈0 at actual DA prices. **This is pjm-158's own
STANDING WARNING realized out of sample** ("improving C3b toward RT GROWS this layer's phantom
energy … toward the condemned pjm-102 clamp"): pjm-158 measured 2023-2025 only, and the
held-out rungs put the layer on the **other side of its crossing price**, ~2× larger, on
exactly the two years C1 fails. Sign agreement is **5 of 5 years**. **RE-MEASURED, NOT
RE-OPENED** — cell `da_virtual_bids` **stays `K`**, and its root cause (the LP carries one
price series gated as RT while the curve needs a DA price) remains the architecture question
**escalated to the owner** inside PJM's owner-declared-closed price-formation frontier
(pjm-142). At pjm-158's **own measured channel gain** the held-out positions bound
**~21 % of 2021's and ~44 % of 2022's** `CC_REGULAR` miss; **55-79 % stays unexplained and
this session does not claim otherwise.**

**Two candidates tested and NOT confirmed** (recorded so they are not re-tried): (a) `ST_GAS`
— the second-largest 2021 C1 failure (+8.07 TWh) — is **not floor-forced**: 76 % of its 2021
energy is `econlo`/`econhi` economic and `mustrun` is **0.00**, so rule 17
`[R-FLOOR-WINDOW]` does not fire; (b) the `ST_GAS`↔`CT_PEAKER` substitution hypothesis
**FAILS its own test** — monthly delta correlation **+0.077 / −0.165 / +0.497 / +0.178 /
+0.076**, positive in four of five years, so the annual near-offset is coincidence. **Filed,
not pursued:** the model's `ST_GAS` holds a near-constant CF of its own peak
(0.156/0.184/0.157/0.156/0.242) while the measured class swings 3.8 → 14.8 TWh — an
**in-sample** question for 2023-2025, since chasing it from a held-out year is the fitting
rule 22 step 3 forbids.

**G-DRIFT IS STRUCTURALLY UNDISCHARGEABLE FOR THIS KEEPER, which is what earned the control.**
`pjm_debugb_inputclock_A/meta.json` records `git_sha` **`457ae04`** (2026-08-15); it **does
not exist at HEAD** and is **not** in `docs/governance/citation-commit-map.txt` — it predates
the **2026-08-16 history rewrite** by one day, and the clone was deepened to **11,640 commits**
without resolving it. There is **no diff to classify**, which is stronger than NEISO's "too
large to classify" (assessment §4 i); an unclassifiable diff is treated as LIVE, and a LIVE
hunk is the one thing that earns a control solve under rule 29 (b). NEISO's INERT verdict does
**not** transfer (rule 25 `[R-ISO-SCOPE]`). So `pjm_headctrl_k162` was solved — the keeper
recipe replayed on **2023-2025 only**, one invocation, **no `--holdout-authorized`** — against
thresholds fixed in the PRECOMMIT **before** it ran.

**THE CONTROL CAME BACK BIT-IDENTICAL.** Every pre-registered threshold held at **exactly
zero**: system mean zonal price +0.0000 % (30.7538 / 29.8080 / 40.3556 unchanged to 4 dp),
demand / slack / dump **bit-identical**, reserve_price +0.0000 %, total generation +0.0000 %
(787.9243 / 816.7908 / 847.9144 TWh, Δ = +0.00000), worst per-class annual energy
**0.0000 %**. At hourly grain, `max|Δ| = 0` on every numeric column of `class_hourly`
(166,440 rows/yr), `reserve_family` (dual, requirement, held MW, shortfall) and `storage`
(charge, discharge), in all three years — 499,320 class-hours, not one megawatt-hour moved.
**HEAD drift is INERT for PJM's backcast path**, and *stronger* than NEISO's, which carried a
−0.008 % price residual from degenerate-LP tie-breaking; PJM has no residual at all. This
CLOSES the §4(i) open limit the touchpoint assessment carried for PJM: the in-sample and
held-out columns are like-for-like, so the DA-virtual sign flip above is a property of the
years, not of the code. Stated against interest: the audit could not be performed and the
thing it was meant to establish held anyway — which is exactly why rule 29 (b) treats an
unclassifiable diff as LIVE rather than presuming inertness; bit-identity was the hypothesis,
not the prior. **Filed for the audit desk, not acted on here:** an unresolvable `git_sha` is a
GENERAL hazard for every artifact whose sha predates 2026-08-16 and is absent from the commit
map — G-CTRL form 4's code-audit route is unavailable for all of them until their bundles are
re-stamped.

**Governance.** PJM holds `complete`; the holdout freeze is scoped to `locked_test` alone.
**No held-out year was solved this session** (the control is training-tier), so no marker is
spent and the rule-22 registration gate is not engaged; `final` is not granted and 2019 /
H1-2026 are untouched. Rule 28: duty (b) not triggered (nothing tested or adjudicated —
`da_virtual_bids` stays `K` with an **evidence append only**), duty (c) not triggered. Rule
25: this finding enters no other ISO's shard. The control bundle is **deleted before merge**
per rule 29 (c), following the `neiso_headctrl_k99` precedent (that bundle is likewise absent
from `results/calibration/` and from the registry, and
`check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES` has been **empty** since the
2026-09-05 keeper-only prune); every number cited from it lives in the FINDING.

**Dispatch item corrected, against interest:** the "ALSO OPEN, unrelated but red" claim —
`tests/scoring/test_ff_readiness_battery.py` (4) and `test_gate_a_provenance.py` (1) failing
on main over a superseded MISO keeper — **does not reproduce and is a false alarm on both
halves.** The 4 failures are an **environment artifact**: `data/clean` is gitignored and
starts empty, and the `confirmed-retirements` partition was missing
(`InputResolution(iso='ERCOT', name='confirmed_retirements', status='MISSING', detail='clean
partition …')`). After `python scripts/regenerate_clean.py confirmed-retirements`, **37/37
pass**, `test_gate_a_provenance.py` included (it had **zero** failures either way). And the
forecast board was **already re-keyed** on 2026-09-05 (r#42):
`frontend/data/forecast/program-status.json` cites `2026-09-05-miso-220-nonsteam-lift`,
matching `keepers/MISO.json`. **No board edit was made** — there was nothing to fix, and a
cross-lane MISO edit from a PJM session would be unjustified.


---

## pjm-167 — 2026-09-06 — the chartered 2022 touchpoint re-run was ALREADY SPENT (zero LP); the stale keeper-shard `holdout_touchpoint` REPAIRED; PJM's G-DRIFT baseline is UNRECOVERABLE

**Branch:** `claude/pjm-2022-touchpoint-rerun-0j2ng2` · **Base:** `origin/main` @ `dbf8796b`
**Finding:** `docs/FINDING-pjm167-touchpoint-rerun-already-spent-2026-09-06.md`
**Keeper UNCHANGED** (`2026-08-15-pjm-162-inputclock`) · **no solve, no score, no registration,
no marker change, no matrix verdict moved** · **ZERO LP minutes.**

**The chartered task was already done.** The session opened to re-measure PJM's 2022 validation
touchpoint against the corrected input clock, on the premise that the registered rung was the
2026-08-05 pre-repair one. Phase 0 found it executed on **2026-09-05** and registered:
`2026-09-05-pjm-2022-2021-touchpoints` (bundle `pjm_tp2022_2021_k162`, solved at `46e08e5b`, well
after the 2026-08-16 ≤2022 clock extension) — **and it walked 2021 as well**. Preconditions were
checked in the chartered order first and all passed (PJM holds `complete`; `frozen_tiers` =
`{locked_test}` only; `tier_for_year(2022)` = `validation`; `final` empty), so the lane was
legitimately open and is closed on **evidence**, not on a gate.

**The answer, reported at full magnitude: the input-clock repair does NOT close 2022 — it moves
the rung backwards.** C1 `CC_REGULAR` **+18.28 → +22.26 TWh**; C3b NRMSE **0.206 → 0.250**. pjm-162
*is* the stale rung's named repair and the rung fails the same two criteria, ~4 TWh larger. 2021 is
NOT-YET on three (C1 `CC_REGULAR` +28.72 / `ST_GAS` +8.07 / `COAL_BIT` −9.45 TWh; C3a +25.7 %;
C3b 0.355), C3c ledgered under rubric v3.6. Re-solving would have spent ~40–70 min of LP to
reproduce a committed number, so it was not spent.

**What was actually outstanding was a records defect, and it is repaired.**
`keepers/PJM.json` carried a hand-authored `holdout_touchpoint` block naming
`2026-08-05-pjm-2022-touchpoint` — **pruned** under the 2026-09-05 keeper-only retention directive.
`build_status.py:574` copies that block through **without validating it against the registry** and
`calibration-status.js:406` renders it, so the live PJM status card showed **two different 2022
numbers stacked**: a `HOLDOUT 2022` panel reading +18.28 TWh / 0.206 with a **dead link** to the
pruned run, directly above the derived ladder reading +22.26 TWh / 0.250. The block is **removed**
(not re-authored) and the status part rebuilt — rule 30 `[R-TOUCHPOINT-FOLD]` (b) names a
hand-authored holdout block as the wrong shape, the derived ladder strictly dominates it (per-year,
auto-derived), and **ERCOT is the precedent**: it has spent 2022 touchpoints and carries a ladder
with no such block. Four of six ISOs already had none. Gates after: `audit_keepers --iso PJM
--check` **PASS 0/0**; parity **OK** (14 runs, 47 bundle dirs); matrix guard **exit 0** (its 244
anchor warnings measured identical on a clean stash of main — pre-existing).

**NEISO carries the identical defect — ROUTED, not fixed** (`2026-08-06-neiso-2022-corrected-basis`,
also pruned). Already routed once at capx r#41 and still open; left untouched on lane discipline
(rule 25 `[R-ISO-SCOPE]`, `keepers/README.md`). **A guard is warranted and deliberately NOT landed
here**: no `audit_keepers` check asserts that shard-referenced run ids exist in the registry, but
CI runs `audit_keepers --check` across every ISO, so the guard would red `main` on NEISO's still-open
block. Correct order is NEISO's repair first, guard second, in that lane's PR.

**PJM's G-DRIFT baseline is UNRECOVERABLE — the one open limit is harder than the assessment
assumed.** The 2026-09-05 assessment left PJM's HEAD-drift limit open and recommended a same-HEAD
control solve; rule 29 `[R-SCREEN]` (b) directs the zero-LP G-DRIFT audit first. It is **not
dischargeable as recorded**: the keeper's `git_sha` `457ae04` is a 7-char **pre-rewrite** prefix
(not a valid object; CLAUDE.md warns such prefixes may now resolve WRONG), its full
`basis_sha c447199c…35454` does not resolve and a targeted `git fetch` of it did not return in
~3 min, and **neither is in `citation-commit-map.txt`**. The keeper solved 2026-08-15, one day
before the 2026-08-16 history rewrite. *Stated against interest:* this does not prove the object is
gone from the remote — only that it is unobtainable by the two routes available here; a
`--unshallow` (5.46 GiB) was judged out of proportion. **Consequence:** under rule 29(b) an
unclassifiable drift audit is treated as **LIVE**, so PJM's control solve *is* authorized — the
same place NEISO landed by a different route. It is an owner call, not a session's to spend: its
only product is closing a stated limit on a number rule 22 forbids quoting as skill and rule 30(c)
forbids from downgrading the ISO.

**Successor, unchanged and now doubly supported (rule 22 step 3):** PJM's **gas-over / coal-under
C1 signature**, running the same direction on *both* held-out rungs against a tuned window where C1
passes clean. It goes to **2023–2025**, never to the touchpoint year. Prep items, unrestricted and
marker-free: PJM 2020 is not data-ready on three measured blockers (inflated zonal demand feed,
missing `calibration_reference` block, missing renewable-capacity file), and the PJM 2021 int32
sentinel (2,147,480,064 MW, three hours) is located but unfixed — fixing it re-renders PJM's
committed benchmark and needs its own decision.

**Re-scored from committed artifacts (no solve), and one new observation.**
`calibration_verdict.py --run-id 2026-09-05-pjm-2022-2021-touchpoints` at HEAD reproduces every
figure above exactly and confirms the basis as **three** failing criteria, not four —
`fuelmix, price_mean, price_shape` — with C3c reading **CAVEAT / ACCEPTED MODEL-CLASS LIMITATION**
under the rubric v3.6 holdout clause. Benign vintage note: the bundle's committed `metrics.json`
still carries the solve-time stamp (rubric 3.5, fails 4, C3c counted); the sidecar, the derived
ladder and the re-score all carry v3.6, and the sidecar is the scored surface. **NEW, for the
successor:** the scorer's band-free REPORTED-ONLY `D-A` row shows the two rungs diverging sharply
on diurnal amplitude — 2021 **112.7 %** of measured ($28.65 vs $25.42), 2022 **60.7 %** ($28.18 vs
$46.40). The model's own hod range is flat across the two years while the market's nearly doubles,
so amplitude is not tracking the C1 miss. That is the **flat-offer-stack signature** of the
keeper's own note item (15a), now visible out-of-sample and the natural companion to 2022's C3b
0.250. Recorded as evidence only — item (15a)'s lever queue is empty with no open successor, D-A
is band-free and never a tuning target, and rule 22 step 3 sends any work to 2023-2025.

**RENUMBERED, and TWO OF THIS ENTRY'S CLAIMS ARE SUPERSEDED BY pjm-166 (the entry directly
above), which landed on `main` while this session was open.** This session began as pjm-166 and is
renumbered pjm-167. (a) **The successor named below is REFUTED — do not take the C1 signature to
2023-2025 as a merit-order-position object.** pjm-166 did exactly that, zero-LP, and killed it on
three independent tests; and the clause "on the year with the cheapest delivered gas in the span",
inherited from the registered sidecar's note rather than measured here, is **inverted** — 2021 and
2022 are the two DEAREST-gas and CHEAPEST-coal years of 2021-2025. Coal-under is **2021 only**
(2022 coal is +2.0 TWh, over). The defect is an **additive fossil surplus**, not a reordering, and
the live object is the **DA-virtual layer's net cleared position** (the only quantity crossing the
tier boundary; `da_virtual_bids` stays `K`, root cause escalated to the owner). (b) **The G-DRIFT
finding below is INDEPENDENTLY REPLICATED and its owner-court item is DISCHARGED**: pjm-166 reached
the same conclusion by a stronger route (deepened to 11,640 commits without resolving `457ae04`, so
there is *no diff to classify*) and spent the control (`pjm_headctrl_k162`, training-tier only,
deleted before merge per rule 29 c). Do not re-raise or re-spend it. Everything else here stands.


**Log-gap note:** the 2026-09-05 touchpoint session registered its run and wrote
`results/calibration/ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md`, but left **no
entry in this log**. This entry records its result so the log is not silent on it; the assessment
remains that session's own record.

Next shorthand: **pjm-168.**


## pjm-171 — 2026-09-07 — 2021's C3a is the flat-offer-stack defect WITHOUT its offset; no admissible lever closes it (zero LP; keeper untouched)

**Charter:** continue PJM backcast calibration toward bringing 2021 inside the ±10 % C3a band.
**Answer: it cannot be done by any admissible change, and the reason is structural rather than
a shortfall of effort.** Keeper UNCHANGED `2026-08-15-pjm-162-inputclock`; nothing promoted,
nothing registered; PJM headline UNCHANGED **CALIBRATED** (rule 30(c)). **ZERO LP SOLVED** —
rule 29 `[R-SCREEN]` phase 0 killed the candidate before a screen. Full record:
`results/calibration/FINDING-pjm171-2021-c3a-is-the-flat-stack-without-its-offset-2026-09-07.md`.

**The decomposition.** Splitting each year's C3a gap ($/MWh) into a TROUGH leg (load deciles
1–8) and a PEAK leg (d9–10), with the counterfactual C3a if either leg alone were closed:

| year | C3a | trough | peak | if trough fixed | if peak fixed |
|---|---|---|---|---|---|
| 2021 (holdout) | **+10.7 %** | +3.56 | +0.57 | **+1.5 %** | +9.2 % |
| 2022 (holdout) | −10.3 % | +4.24 | −11.87 | **−16.0 %** | +5.7 % |
| 2023 (train) | +5.7 % | +3.42 | −1.72 | −5.8 % | **+11.5 %** |
| 2024 (train) | −1.4 % | +2.28 | −2.73 | −8.6 % | +7.2 % |
| 2025 (train) | −8.1 % | +0.82 | −4.54 | −9.8 % | +1.8 % |

**The trough leg is positive in ALL FIVE YEARS, the three tuned ones included.** The peak leg
is the year-varying term and it sets C3a's sign. 2021 is the only year whose peak leg is ≈ 0 —
its decile-10 actual is $56.55/MWh against $172.00 (2022), $48.28 (2023), $62.10 (2024),
$92.67 (2025) — so nothing offsets the trough surplus and the defect reads at full magnitude.
**2021 is therefore the cleanest measurement the lane has of a defect it already knows**, not a
new object.

**The decision-grade result: no single-ended repair survives.** Closing the trough alone sends
2022 to −16.0 %; closing the peak alone sends **training year 2023 to +11.5 %**. Both are
outside the ±10 % commercial band, and both hold at split deciles 7/8/9. So the cancellation
pjm-141 named (*"the annual level being right is a cancellation, not a correct level"*) is
**load-bearing in the TUNED window too**, which pjm-141 asserted on 2023–2025 and this session
now measures across the full 2021–2025 span. Any admissible repair must move both ends.

**Year-invariant structural signature (§3).** Bottom-decile implied market heat rate, price ÷
the model's OWN `_gas_series`: model **8.46 / 7.92 / 8.71 / 9.28 / 9.17** (2021–2025) against
actual **6.55 / 5.87 / 6.02 / 6.35 / 7.01**. The model's overnight margin is a gas CC at about
its rated heat rate in every year; PJM's own overnight clears *below any CC's full-load heat
rate*. This reproduces pjm-141's T6 (within-day offer σ = $0.000000) on the load axis.

**A separate new DOF observation (§4), recorded not levered.** Realized annual-mean bituminous
passthrough on the keeper's own parameters: **2024 0.81 · 2023 0.92 · 2025 1.06 · 2021 1.12 ·
2022 1.32** (saturated at the ceiling in 12/12 months). **The training window exercises only the
sigmoid's lower limb** — the `ceil` and `gas_mid` that set the held-out years' coal offers are
effectively unidentified by the years they were tuned against (rule 21 `[R-DOF]`). It is not a
lever here: pjm-170 measured the full 32 % markup removal as worth only **−$0.17/MWh** on the
annual mean, and the `ceil`-alone cell is **R** (DO-NOT-REDO).

**Nothing re-adjudicated, nothing re-tested.** `diurnal_price_amplitude` **G** (owner-closed,
no admissible in-model route), `measured_offer_surface` **R**, `ordc_scarcity_overlay` **G**,
`coal_passthrough_sigmoids` `ceil`-alone **R** — this session's evidence corroborates all four.
The PJM matrix shard's `diurnal_price_amplitude` evidence is extended with the five-year
decomposition; the **G** verdict is untouched.

**Rule 22 discipline.** Nothing was tuned, fitted or selected against 2021. Every measurement is
on the object (offer level, implied heat rate, realized passthrough), never on the residual;
the touchpoint loop sends any repair to 2023–2025, where §2 shows the same trough defect lives.

**Successor: do NOT open a card to close 2021.** The live card is unchanged — pjm-170 §7 item 2,
now restated with both faces: PJM's price distribution is compressed at both ends, the ends
cancel, and the cancellation holds the tuned years inside the band. Re-opening either end is an
owner decision on rule 1 `[R-STRUCT]` structural grounds, never on the fit.

Next shorthand: **pjm-172.**


## pjm-171 ADDENDUM — 2026-09-07 — the priced-interchange seam is FROZEN AT 2023 CONDITIONS in every pre-2023 year (zero LP; keeper untouched)

**Owner question:** *"Are imports being repriced each year? If not they should be."*
**Answer: not before 2023 — and it binds on both the keeper and the registered touchpoint.**
Record: `results/calibration/ADDENDUM-pjm171-seam-fuel-basis-freeze-2026-09-07.md`.

**Two stacking freezes.** (F-A) `constants.HENRY_HUB_TRAJECTORIES` (`low`/`mid`/`high`) has its
**first knot at 2023**, so `_hold_flat_extrapolate` hands the seam the 2023 knot ($2.54) for every
earlier year. (F-B) `NeighborInterface.hr_by_year` covers **{2023, 2024, 2025} only**, so 2021/2022
fall through to the **gas-elastic forward formula** and resolve identically to each other
(MISO 12.90/12.90, NYISO 10.40/10.40, DUK/TVA/LGEE 11.19/11.19) across a $3.91-vs-$6.42 Henry Hub gap.

**The contract that fails.** `neighbor_gas_price`'s own docstring promises *"a neighbor and its
bordering ISO see the same Henry Hub level"*. Measured: error 0 % in 2023/2024/2025, **−32 % in
2021** (own 3.72 vs seam 2.54) and **−61 % in 2022** (6.45 vs 2.54). 2019/2020 are affected too.

**It binds:** `reference_price_interface = True` and `priced_interchange = True` in BOTH
`pjm_debugb_inputclock_A` and `pjm169_tp2022_2021_f2arm`.

**Measured consequence** — model net export vs EIA-930 (sentinels masked, `> 1e6 MW`):
2021 **23.43 vs 37.94 (−14.51 TWh)** · 2022 21.65 vs 31.64 (−9.99) · 2023 27.47 vs 39.87 (−12.40) ·
2024 20.45 vs 32.56 (−12.12) · 2025 23.23 vs 17.97 (+5.26). Too **import-ward** in 2021–2024 —
the exact mechanism `derive_neighbor_hr_by_year.py`'s docstring names as *"the root of the PJM 2025
over-export / 2024 under-export"*, never applied to the two dearest-gas years it flags as worst.

**Demand is ruled out.** Model LP demand vs EIA-930: +0.0 / +0.3 / +0.2 / −0.1 / −0.0 % for
2021–2025. This is NOT the 2020-style inflated-zonal-demand blocker.

**Rules 22 + 14.** The measured anchor exists, is derived by a committed script, and is applied to
the three TRAINING years only — an input-parity break, with the data on disk
(`henry_hub_monthly.csv` 1997–2025; `hindcast_realized` already carries a 2021 knot).

**The repair is inert in the training window by construction** (the extrapolator returns the exact
knot when present; new `hr_by_year` keys cannot change 2023–2025 lookups), so it moves only
pre-2023 backcast years: keeper untouched, no training re-solve, nothing promoted. Input coverage
checked — NYISO realized LMP 2018–2026 (2021 ✓ 2022 ✓); MISO 2022–2026, so 2021 has no MISO anchor
and falls back to the structural `marginal_heat_rate`, that script's own designed behaviour.

**Stated against interest:** correcting it is expected to move 2021's C3a **further from the band**
(dearer imports ⇒ less import, more export ⇒ PJM climbs its own stack ⇒ the trough leg, already
+$3.56/MWh high, rises). A prediction needing a screen — and under rule 14 never a reason to keep
the estimate.

**Owner-facing fork, nothing built:** `HENRY_HUB_TRAJECTORIES` is shared by every ISO, so the
repair is either (1) pre-2023 knots on the shared table, or (2) a seam-local measured-backcast gas
resolution mirroring the ISO's own `gas_price_override` path. **Cross-ISO (rule 25):** any ISO
arming `reference_price_interface` on a pre-2023 year hits the same freeze — every lane must verify
its own exposure before spending a pre-2023 touchpoint; no verdict transfers.

**Plant-level corroboration.** PJM 2021 model − EIA-923 by zone (TWh): **EMAAC +12.98** (vs CEMS
**+21.7**), SWMAAC +4.96, ATSI +0.35, Central PA +0.20, West APS −0.68, **AEP Ohio −1.66**,
ComEd −1.70, Dominion −1.75. By class: **CC_REGULAR +26.77**, COAL_BIT −6.84, CT_PEAKER −11.40.
**Bergen (2398, EMAAC, CC_REGULAR, 1401 MW): model 5.586 vs CEMS 1.104 vs EIA-923 1.740 — 3.21× the
923, `nodata` = False.** CEMS does under-report Bergen (1.104 < 1.740) but the model is above BOTH,
so no CEMS-coverage argument reaches a 3.2× over-run. Also Linden +2.64, Red Oak +2.64, Wildcat
Point +2.04, Hay Road +1.68, Chalk Point ST_GAS +1.54 (15.3×). Correction to the standing read:
**AEP Ohio nets −1.66 TWh** (it contains over-runs — Rockport +1.60, Hanging Rock +1.10 — but is
net under). The EMAAC concentration in CC plants with low measured utilisation is consistent with
the open availability-envelope over-count, **as a hypothesis, not a measurement** — the next probe
is named in the addendum §8.

**Also corrected:** `ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §3.4 says all three
corrupt PJM 2021 hours carry 2,147,480,064 MW; only one does (the others carry 1.528e9 and 4.31e8).
Its conclusion is unaffected, but a guard written to the literal sentinel catches one of three —
use a `> 1e6 MW` bound.

Next shorthand: **pjm-172.**


## pjm-171 ADDENDUM 2 — 2026-09-07 — the EMAAC CC over-run: CEMS coverage is ruled out; the defect is outage APPLICATION, not detection (zero LP)

**Owner observation:** *"too much available capacity for cc regular … Bergen is +4 twh … they
indicate CEMS is missing data but there's no reason our model should be 2x the 923 data."*
**Confirmed, and the CEMS objection is answered.** Record:
`results/calibration/ADDENDUM-pjm171-emaac-availability-census-2026-09-07.md`.

**26.85 TWh** of PJM 2021 gas-fleet model energy is produced in hours the plant's own CEMS record
reads zero; **9.79 TWh in EMAAC** (Central PA 4.69, SWMAAC 3.87, Dominion 3.25, AEP Ohio 1.63,
ComEd 1.38, West APS 1.13, ATSI 1.11).

**The discriminating statistic is the longest continuous off-run.** Bergen: CEMS zero for **838
consecutive hours (35 days)**, model longest off **24 h**. Red Oak **800 h vs 7 h**. Hopewell
**1,155 h vs 0 h** — never stopped. Against a clean control set where the machinery works to a few
percent: Wildcat Point 460/489, Tenaska Virginia 1,589/1,608, Fremont 463/480, Woodbridge 315/336,
St Joseph 299/312. **The mechanism works; it does not reach the rows above.**

**CEMS coverage is ruled out.** Every named plant is present in raw CAMPD with a full per-unit
8,760-h record (Bergen 52,560 rows / 6 units; `nodata` = False). CEMS *does* under-report Bergen
(1.104 vs EIA-923's 1.740 TWh) but **the model sits above both at 5.586 TWh = 3.21× the 923**.

**Detection is mostly not the problem either — APPLICATION is.** `unit-outage-events/PJM` carries
1,379 PJM 2021 rows including a **282-day** Chalk Point event and a **132-day** Montour event, yet
the model's longest off-run at Chalk Point is **68 h**. The event table is per-UNIT with
`unit_pct_of_plant` while the LP row is a per-PLANT CAMPD bin, so a plant whose units are out at
different times carries a derate without ever going offline. Two genuine detection gaps survive:
**Hunterstown 55976** (0 events vs 37 measured days off) and **Eddystone 3161** (1 event of 11.7 d
vs 187 days).

**Honest split, and it matters.** A CEMS zero is not proof of unavailability. Availability is the
live hypothesis for the modern CCs — Bergen (45.6 % model CF vs 9.0 % measured), Red Oak (70.2 vs
21.9), Hay Road, Woodbridge, West Deptford. **Merit order** is the likelier owner for Eddystone (a
1960s steam plant, 187 days off) and the Chalk Point ST_GAS bin — those belong with the parent
finding's offer-stack object. Phantom energy is an **upper bound**, never "the availability error".

**Phase B is blocked at HEAD and the block is named:** the fleet rebuild needs
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_2021_*`, a converted corpus whose payload is gitignored
(recovery = re-fetch). Successor card, zero LP once unblocked: take `pmax × availability` per plant
and test Chalk Point's detected 282-day event against it — the event never reaches the fleet, or it
reaches it as a partial derate, or the binning re-spreads it. Three different repairs.

**Not a route to the band either.** Cutting phantom CC energy reduces CC volume (toward C1's
+26.77 TWh) but removes mid-merit supply, raising price — the same direction as the seam repair and
away from 2021's +10.8 %. Rule 30(c): PJM stays **CALIBRATED**.

**In-session correction:** an earlier pass used plant codes recalled from memory and reported
"Eddystone not in CAMPD" and "Hunterstown zero events in all years". Both were wrong-identifier
artifacts (Eddystone is 3161 not 3169; Hunterstown 55976 not 55196). Every code in the addendum is
now read from the committed payloads.

## pjm-172 PRECOMMIT — 2026-09-07 — seam-local measured backcast gas (F-A), written before any build

`docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md`. Owner decision 2026-09-07: the
repair shape is **seam-local**, not an edit to the shared `HENRY_HUB_TRAJECTORIES`. ONE declared
delta (the gas level); **F-B (the missing 2021/2022 `hr_by_year` entries) is explicitly NOT
bundled** (rule 19). Zero free parameters — measured EIA HH annual means already on disk (2021
3.910, 2022 6.419). **Look-ahead guard is load-bearing and fixed ex ante:** the measured path is
refused for every `hindcast_asknown_*` scenario key, so the as-known hindcast lane cannot be
contaminated. **Screen year 2022, chosen on FOOTPRINT before any solve** — seam baseload delta
+44.122 $/MWh (2022) vs +15.579 (2021), a 2.83× ratio. Disclosed against interest: 2022 is also
where the repair is expected to help the residual, which is a coincidence of the footprint rule and
**C3a is deliberately not a pass condition**. Six pre-registered STOP gates (S1 resolution, S2
bit-identity for every year ≥2023 and every forecast year, S3 magnitude against the tabled
prediction, S4 footprint = the 80 seam rows only, S5 net export rises, S6 collateral). G-CTRL form 4
against the committed touchpoint with a G-DRIFT audit owed before the arm solves. Expected residual
movement recorded ex ante: **2022 improves, 2021 worsens** — rule 14, never a reason to keep the
estimate.

Next shorthand: **pjm-172.**

## 2026-09-07 — pjm-172: F-A (seam-local MEASURED backcast gas) BUILT and KILLED at its own pre-solve gates S1/S3 — ZERO LP, nothing promoted

**Card** `docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md` (binding, not rewritten).
**Result** `results/calibration/FINDING-pjm172-seam-measured-gas-2026-09-07.md`.
**Keeper** `2026-08-15-pjm-162-inputclock` — unchanged. **PJM headline: CALIBRATED** (rule 30(c)).
**LP spent: none.** No screen bundle exists; PJM's `complete` marker is unspent and
`--holdout-authorized` was never passed.

**G-DRIFT first (rule 29(b)), zero LP.** `git diff f36cee6e HEAD` over the solve path = 69 files,
+15,065/−76, and **every hunk classifies INERT for the PJM backcast path** — appended as Appendix A
to the PRECOMMIT *before* the arm was built. Two instrument checks: the PJM solve-surface
fingerprint is `0f749d17202c32d9` / 211 rows / `moved {}` at **both** revisions, matching the value
the control bundle recorded; and the control's config rebuilt at HEAD resolves every recorded field
unchanged, with the five new default-off fields **and** the `capacity_screen_peak_measured_hindcast`
default flip all dropping out of `cache_key()`. Two hunks were adjudicated on measurement rather
than category: PJM's new `retirement_sector_gate` ISOConfig override (coerced to `False` in
backcast — verified by running it) and the new **ungated** EIA-930 fuel-spike screen (**0 hours
flagged for PJM in every year 2021–2025**, raw and filled frames alike). ⇒ **G-CTRL form 4 valid,
no control LP.**

**The arm was implemented exactly as §2 declares and it works.** Below the trajectory's first knot
`neighbor_gas_price` now resolves Henry Hub from the measured annual series — 2022 **$2.54 →
$6.419058**/MMBtu, 2021 → **$3.909683** — with `gas_basis` unchanged, **zero free parameters, zero
new `ScenarioConfig` fields**, plus the load-bearing `hindcast_asknown_*` look-ahead refusal (with a
reachability assertion so the guard cannot go vacuous). **Gate S2 PASSES**: 2023/2024/2025 and every
forecast year are **bit-identical** across all five seams and all of `low`/`mid`/`high`, for every
registered ISO — asserted by test, so no keeper can move.

**S1 and S3 FAIL, both from one structural fact the card did not anticipate.** Carolinas / TVA /
LGEE carry `hr_by_year = None` in **every** year — SERC publishes no nodal LMP to anchor one to —
so they always take `neighbor_heat_rate`'s gas-elastic branch `hr = 5.6 + 14.2/gas`. Their implied
heat rate is a *function of the very gas level this card moves*, and falls as gas rises —
deliberately, so the coal/nuclear Southeast does not ride Henry Hub up in a dear-gas year.

- **S1 FAIL** — it requires `neighbor_heat_rate` **unchanged**; it moves on 3 of 5 seams
  (11.1906 → 9.2320 in 2021; 11.1906 → **7.8122** in 2022).
- **S3 FAIL** — measured 2022 seam baseload mean **61.1448 $/MWh** vs §4's predicted **74.156**
  (tolerance 1e-6). MISO **82.806** and NYISO **72.478** reproduce §4 exactly; Carolinas/TVA/LGEE
  land **50.147** against a predicted 71.833 (−21.686 each).
- **S4 / S5 / S6 NOT REACHED** — they need the solve, and the kill lands before it.

**Root cause is the card's arithmetic, not the implementation.** §4's arm column carried the
*control's* heat rate (`71.833 = 6.419058 × 11.1906`, the $2.54 heat rate). The apparatus is
vindicated by the control column, which reproduces §4 on **all five** seams (32.766 / 32.136 /
28.424 ×3, mean 30.0348 vs 30.035). **S1 is structurally unsatisfiable for any change to PJM's
pre-2023 seam gas level, and card F-B cannot rescue it** — the Southeast trio's elastic branch is
not a 2021/2022 gap but their permanent price-formation anchor. This refines pjm-171's F-B reading:
the 11.19/11.19 two-year identity holds on the *frozen* path precisely because the gas is the same
held knot in both years; repair the gas and the years separate.

**Corrected footprint:** the mechanism moves the seam baseload **+31.110 $/MWh** in 2022 and
**+10.985** in 2021 — ~70 % of the predicted size — but the ratio is **2.832**, i.e. §4's stated
**2.83×**, so the screen-year choice was uncontaminated.

**NOT measured, not quotable:** the 2022 net-export direction, the `mc` footprint, any collateral
criterion, and **any C3a movement in either year**. The card's ex-ante predictions (2022 improves,
2021 worsens) remain predictions.

**Open and owner-facing.** The pre-2023 input defect is **real and unrepaired**, and rule 14
`[R-ACCURATE]` argues for landing the corrected input regardless of the gate outcome. The code and
its 40 tests are on the branch, **unarmed and unpromoted**, and inert in every scored year. Routes:
(a) a successor card restating S1/S3 with the gas-elasticity in them (S3 = 61.145) then screening
2022 — **recommended**; (b) land it as an input correction on rule-14 grounds without a screen;
(c) drop it. Cross-ISO unchanged (rule 25): no verdict transfers, and MISO's own pre-2023 exposure
is still its lane's to verify.

Matrix: `reference_price_interface` STAYS **K**, cell annotated in the PJM shard (rule 32 duty b).

### pjm-172 addendum (same day) — the 2021/2022 measurement is BLOCKED ON CONTAINER RAM, not on the mechanism

Owner directed the lane to finish the repair rather than stop at the gate grading. Done as far as
the environment allows. The G-CTRL form-4 A/B was set up per PRECOMMIT §6 (`replay_keeper` on the
committed touchpoint at this HEAD, so the only delta is F-A), and two container-state gaps were
closed first: `data/clean/` was entirely unbuilt (curated 15 datatypes from `data/raw`; `lmp` fails
on a pre-existing **CAISO** column defect, `KeyError: 'MGHG'`, unrelated to PJM), and
`data/raw/pjm-da-virtuals/` was empty — **all 24 monthly `hrl_da_incs_decs_{2021,2022}` files
re-fetched**, which also unblocks the EMAAC availability card's Phase B.

The solve then reached LP construction on 2022 — past every data gate, seam repricing and per-gen
reserve co-opt both logged — and was **OOM-killed (exit 137) twice**: once with the clean build
competing, and once **alone on the box with 14 GB free at launch**, memory falling 14 → 6 → 3 → 2 →
0 GB. This container has 15 GB and one PJM plant-level 8760 LP on the keeper recipe exceeds it
(rule 12 `[R-PARALLEL]` caps *concurrent* per-plant runs at ~2; here even one does not fit).
Nothing was disabled to make it fit — dropping the virtuals, the per-gen co-opt or the loss surface
would change the recipe and the A/B's validity rests on the arm being the touchpoint recipe plus
F-A and nothing else.

**Unchanged: S4 / S5 / S6 and any C3a movement in either year remain UNMEASURED and unquotable.**
Both partial bundle dirs hold no solved output, so rule 31 `[R-RETAIN]` has no artifact at risk.
**Not a keeper candidate in either direction** — the repair is byte-identical in 2023–2025, so it
cannot move the keeper's scored years or its determination; it is an input correction to the
held-out pre-2023 seam. Successor needs a larger-RAM runner and nothing else.

## pjm-173 — 2026-09-08

**THE F-A SEAM GAS REPAIR IS STRUCTURALLY INERT ON THE PJM KEEPER — the measured seam ladder
already owns the seam price.** Keeper `2026-08-15-pjm-162-inputclock` unchanged; PJM stays
**CALIBRATED** (rule 30(c)); nothing registered, nothing promoted. LP spent: **2022 only** (~13 min).

The successor card pjm-172 recommended was written and **committed before any solve** (`b8112519`),
then graded. **S1′ and S3′ PASS exactly**: S1′ pins the seam heat rate to the *declared* elastic law
`5.6 + 14.2/gas` rather than demanding it be unchanged (the original S1 was unsatisfiable for any
pre-2023 gas change on PJM, so it could not discriminate) — measured `|hr − law| = 0.0`, on precisely
the three `hr_by_year = None` SERC seams, MISO 12.9 / NYISO 10.4 unmoved; S3′ reproduces the
corrected 2022 seam baseload mean **61.1448** to 4.8e-05.

**Then the 2022 screen ran, and the arm is BYTE-IDENTICAL to the committed control on every scored
quantity** — gas 357.63, coal 155.21, nuclear 272.19, interchange 21.65 TWh, every per-fuel `r`, and
load-weighted mean LMP 66.73 $/MWh, **all +0.00** — against a **+31.110 $/MWh** seam baseload
repricing. **S4 FAILS** (zero of the 80 seam `mc` rows move), **S5 FAILS** (net export 21.65 → 21.65,
no movement; actual 31.69), **S6 PASSES** (`screen_collateral_gate`: 0 flips).

**Cause, proven not inferred:** `pjm_seam_measured_ladder = True` on the keeper recipe, and
`import_nodes.py:1051` reprices the seam bands from **measured per-seam Q-Q ladders**, displacing the
reference price and the firm export floor — rule 19 `[R-ONE-MECH]`, stated in the code's own comment
(*"alternatives, never stacked"*). `PJM_SEAM_LADDER_BY_YEAR` covers **{2019, 2021, 2022, 2023, 2024,
2025}** — every year PJM solves. So `neighbor_gas_price` is computed and then **overwritten**: the
pjm-171 input-parity defect is **real but unreachable** here. Per the card's kill rule **2021 was not
spent**, and it is inert by the same construction.

**No C3a movement was tested in either year.** The card's ex-ante prediction (2022 improves, 2021
worsens) is **neither confirmed nor refuted** and must not be cited.

**NOT a keeper candidate**, and not on a gate ground: byte-identical in 2023–2025 *and* now measured
byte-identical in 2022, so it cannot move any scored year in either direction — there is nothing to
promote. The live question is merge/keep; the owner ruled **KEEP** (2026-09-08) and the measurement
**strengthens** that — a strictly more accurate input (the seam was wrong by −60.6 % / −31.7 % against
the ISO's own burned gas) with provably zero behavioural risk on every PJM year now solved. It stays
live for PJM 2020 and for any ISO without a measured ladder; rule 25 `[R-ISO-SCOPE]`, MISO's exposure
is its own lane's.

**REDIRECTION — where the C1/C3b work goes.** PJM's three failing criteria are one defect (too much
gas, too little coal, too little export; 2022 +27.35 / −12.17 / −10.04 TWh, 2021 +37.67 / −30.83 /
−14.51). Its largest and worst-correlated term is **interchange** (r 0.498/0.546 vs 0.92+ for gas and
coal; nrmse 0.58/0.55 vs 0.14–0.21). This session proves that row is set by the **measured ladder**,
not the gas level — so the next lever is the **ladder construction**, not `neighbor_gas_price`.
Rule 28: `diurnal_price_amplitude` and `ordc_scarcity_overlay` are **G** for PJM,
`measured_offer_surface` and `temp_dependent_derate` are **R**; the ladder is the open route.

**RUNNER — the charter's "REQUIRES ≥32 GB RAM" is WRONG and the LP did not grow.** Three attempts
OOM-killed at **13.95 GiB** against the `claude-code-bash` cgroup's **13.34 GiB**
`memory.limit_in_bytes` (`CONSTRAINT_MEMCG`, on a 16.4 GB box with ~15 GB free). pjm-169 §3.1a had
already measured the same peak (13,755,496 kB, ~420 MiB over) **and published the fix**: a swapfile,
which clears the cap because `memory.memsw.limit_in_bytes` is unlimited. The solve succeeded on the
first attempt with swap armed (338–347 MB spilled). pjm-169 also documented why it looks intermittent
— the swapfile is **silently deactivated** mid-session — which this session reproduced and initially
misattributed to mount namespaces. Three lanes (167, 172, 173) re-derived this ceiling from scratch;
the recipe belongs somewhere a lane reads *before* launching a PJM solve.

Artifacts: `results/calibration/FINDING-pjm173-seam-measured-gas-regate-2026-09-08.md`,
`docs/handoffs/PRECOMMIT-pjm173-seam-measured-gas-regate-2026-09-08.md`. Arm bundle
`pjm173_fa_arm_2022` is gitignored (`2482cc81`, rule 31 `[R-RETAIN]`) and **retained on local disk**,
not deleted.

---

## pjm-d4-1 — 2026-09-09 — the ST_GAS card resolves to ONE channel; the allocation family is FALSIFIED and the one arm that works must be REFUSED (ZERO LP, keeper untouched)

**Branch** `claude/pjm-d4-1-qa8gwk` · **Keeper UNCHANGED** `2026-09-09-pjm-fuelvintage-ep-level`.
**No LP solved, nothing promoted, nothing registered, no holdout year touched.** Every number is a
committed artifact or an on-recipe `run_year(..., fleet_only=True)` build through
`replay_keeper.run_year_kwargs` (3,789 rows, the keeper's own fleet), armed through the same
`prb_overrides` bag `replay_keeper --set` uses. Control: G-CTRL form 4 **IMPAIRED** (G-DRIFT still
not runnable for PJM), bands ±0.25 % / ±2.4 % CT_PEAKER — pre-registered, and it never bound, because
every arm/control pair was built in one process at one HEAD.

**THE MERIT ORDER IS NOT INVERTED — the card's own premise fails.** Capacity-weighted `mc_base` puts
ST_GAS **above** CT_PEAKER by **+1.276** (2024) and **+1.835** (2025) $/MWh and within **0.426** of it
in 2023 (below in 49.6 % of hours, a coin flip); ST_GAS is above CC_REGULAR by **+19.7 / +20.4 /
+25.5** with **0 %** of hours below. The CT_PEAKER displacement needs only **adjacency**, not
inversion — so there is **ONE channel (the floor), not two**, and the handoff's step-4 discriminator
resolves negative.

**C8 IS PURELY PROVENANCE AND GATES IN EXACTLY ONE YEAR.** ST_GAS is materiality-SKIPPED in five of
six years (1.5–1.8 % of ISO load) and material only in **2025** (2.2 %), whose failure text names
**only** the D-4 per-unit conduct leg (plants 3131/3138/3148/3775/593). **The 30 % cap is not what
fails PJM** — the grounded-above-budget escalation is available — so the mandate's **LEVEL need not
move and its MEMBERSHIP must.**

**RULE 19 DISCHARGED FROM THE ARTIFACT**: `st_netload_drag` is the sole mechanism forcing PJM ST_GAS
in D-2 in all six years and the sole ST_GAS floor in D-4. **RULE 17 CONVICTION**: 41 of 58 metered
floored plant-years carry a measured median of **0.000 MW over the floor's own binding hours** —
73.8 % of the rider-covered forced energy — with a **bimodal, no-overlap** split (FAIL zero-share
0.532–0.986 vs pass 0.000–0.457), against a declared **h0-23** window whose stated justification is
ERCOT's *"there is no hour the class's own driver evidence says it is offline"*. Handoff option (c)
is **closed**: for an all-hours window the D-4 `window` check is vacuous by construction, so the old
12-row form measured nothing here.

**NEW NUMBER — the mandate against the METER, not the model.** Forced ÷ measured class energy =
**83.1 / 173.7 / 104.1 / 53.6 / 33.8 / 48.4 %** for 2020-2025: in 2021 the floor alone mandates 74 %
more energy than PJM's entire gas-steam fleet metered that year. And **2024 is the clean rule-1 case**
— ST_GAS is dead on actual (m/a **1.00**) with **36.6 %** of it forced.

**THE ALLOCATION FAMILY IS FALSIFIED PRE-SOLVE** (rule 29 `[R-SCREEN]` clause (0)). Conduct failures
on the `{min_gen>0}` basis — a **superset** of `at_floor_mask`, i.e. the more forgiving one:

| year | C | M `merit_allocation` | P `min_run_persistence` | MP both | L `layup_window_mask` |
|---|---|---|---|---|---|
| 2023 | 4 | **4** | **4** | **5** | **1** |
| 2024 | 2 | **2** | **2** | **2** | — |
| 2025 | 2 | **2** | **2** | **3** | **0** |
| mandate TWh 2025 | 11.5063 | 11.5063 | 11.5332 | 11.5332 | **7.5974** |

**Not one plant flips FAIL → pass under M, P or MP in any year**, and the composition pjm-177 §5
item 3 explicitly named as the fix is **strictly worse**, adding the same conviction (plant 3148) in
both scored years. M's own contract is honoured exactly — aggregate preserved 8.8093 → 8.8093 TWh,
max hourly |Δ| **0.000000 MW**, 42 of 3,789 rows move all ST_GAS, `mc_base` max |Δ|
**0.0000000000** — so this falsifies the **object**, not the implementation. **Why it cannot work:**
the fleet-total mandate hours are supportable by the meter (mandate h ÷ 2 × meter-nonzero h =
**0.91 / 0.70 / 0.76**) but the **distribution** is wrong — plant 3775 is floored **87 % of the year
on a unit whose meter reads non-zero in 8 % of it** — and `merit_allocation`'s signal is bid heat
rate, which is not duty (its own docstring: Spearman vs online fraction only −0.286, p = 0.49, 2025).

**THE LAY-UP MASK CLEARS THE GATE AND IS REFUSED.** `netload_drag_layup_window_mask` (ercot-256)
takes convictions to **0 (2025) / 1 (2023)** — but by cutting the mandate **~34 % in both years**
(a LEVEL change, not an allocation one), and it is registered in `_BACKCAST_ONLY_OVERLAY_FIELDS`,
so under rule 13 `[R-MEASURED]` it has no forward analogue and cannot satisfy rule 17 clause (c).
**Reported as a diagnostic, refused as a fix — that it is the one arm that works is a reason for
suspicion, not adoption.** It does quantify the object: **~34 % of PJM's ST_GAS drag mandate sits
inside measured economic lay-up.** Its own residual failure (plant **3149**, 14.3 % duty in 2023,
never classified by the lay-up derive) argues for membership over lay-up **independently of rule 13**.

**THE ROOT CAUSE AND THE SUCCESSOR, NOT ARMED HERE.** `data.outages.ST_GAS_PEAKER_PLANTS` already
exists to keep *"peaker-class ST_GAS plants: patchy/spiky run rate (run only when called)"* out of the
reliability min-gen floor — its CAISO members admitted on *"online only 0.4–2.5 % of hours"*. **It
names 6 ERCOT plants, 3 CAISO plants and NO PJM PLANT**, while PJM's plant **3161 runs 2.3 / 4.3 /
3.0 % of the year on 862 MW and is floored 7,666–7,885 h**. Every PJM ST_GAS plant below ~25 % meter
duty is convicted in every year it is floored, with **zero passes** (3775 15.4 % duty 6F/0p, 384
16.4 % 4F/0p, 593 23.6 % 6F/0p). **Stated honestly:** the split is imperfect above that (3138 at
58.4 % and 3131 at 60.1 % are also convicted), so membership is the **largest** part of the defect,
not provably all of it.

**CARD 2 RE-MEASURED (committed artifacts).** The fossil surplus is **2–90× larger in the holdout
years than the training years** (+35.10 / +26.87 / +34.46 for 2020-22 against +7.90 / +0.36 / +19.24
for 2023-25) and its **composition is not stable** — 2020 is carried by COAL (+21.25), 2021/2022 by
CC_REGULAR (+27.59 / +24.84) — so one mechanism is unlikely to own both. The DA-virtual phantom-demand
position is negative in **exactly** the three touchpoint years (−2.62 / −11.16 / −14.03) and ≈0 in the
training years. ST_GAS is 14–33 % of it, so card 1 could not close it even if fully repaired.
**Routed to PJM's price-formation frontier (pjm-142), not armed.** Rule 30(c): **none of this
downgrades PJM.**

**GATES** (baselined on this tree; it changes **no source code** — the diff is two docs, a
`.gitignore` block and PJM's matrix shard): `check_mechanism_matrix --base origin/main` **integrity
OK / keeper stamps match / §5.x prose headers match**; `audit_keepers --iso PJM` **PASS 0/0**;
`build_status --check --iso PJM` **in sync**; `check_cache_key_registration --base origin/main`
**green** (the `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` RED the handoff expected is no longer present on
`main`); `check_registry_payload_parity` fails on the **five pre-existing `ercot262_arm_*`** bundles
only (ERCOT's, committed on `main` — rule 25, left alone), this tree adds none;
`pytest tests/scoring` **15 failed / 1,533 passed** — all in `test_golden_manifest_provenance.py` and
`test_registration_marker_gate.py`, files this diff cannot reach (the handoff's expected baseline was
16, i.e. `main` moved by one, and this session adds none); the three matrix-shard unit tests **33
passed**.

**Rule 28 duty discharged**: PJM's shard alone re-stamped, `netload_drag_floors` cell **stays K** with
both sub-gates now adjudicated **R for PJM**.

Artifacts: `docs/RESULT-pjm-d4-1-stgas-merit-order-2026-09-09.md`,
`docs/PRECOMMIT-pjm-d4-1-stgas-merit-order-2026-09-09.md`. **No bundle was written** — no LP ran — so
rule 31 `[R-RETAIN]` has nothing on disk to preserve; the open promotion question is instead whether
pjm-177's `netload_drag_min_run_persistence` should now be answered **NO** on this evidence.

## pjm-d4-2 — 2026-09-10

**PJM's training span reads CALIBRATED.** C8 forced-energy share — the single criterion PJM was
NOT-YET on — moves **FAIL → PASS**, every other scored criterion is unchanged at PASS, and the run
carries **zero caveats** (0 ledgered, 0 protective; determination basis empty).

**The object was MEMBERSHIP**, not the drag's hours or its merit order. pjm-d4-1 falsified the
allocation family at zero LP and located the seam: `data.outages.ST_GAS_PEAKER_PLANTS` existed to
keep run-when-called steamers out of the reliability min-gen floor and named 6 ERCOT plants, 3 CAISO
plants and **no PJM plant**. Eleven PJM plants are now admitted — **zero new `ScenarioConfig` fields,
zero free parameters** (rules 19 `[R-ONE-MECH]` / 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

**The criterion was declared ex ante and cannot have been fitted.** Admission is CAMPD meter-online
share of the plant's ST_GAS slice, pooled over every bench year passing the benchmark's own
`e_ann/c_ann ≤ 1.1` trust test, below **35 %**. The threshold is read off the registry's OWN revealed
membership in ERCOT and CAISO with PJM never consulted (ERCOT admits to 34.7 %, excludes from 36.9 %;
CAISO admits to 31.0 %, excludes from 45.1 % — both gaps empty). It carries **no leverage**: PJM's own
duty distribution has an empty interval 30.8–48.6 % that strictly contains the precedent-admissible
window, so the admitted set is identical across 17.8 points. The competing most-recent-two-years
window — the evidence the registry's own CAISO comment cites — was **tested and falsified** (it makes
ERCOT's admitted set overlap its excluded set).

**Measured, six years, one LP per rule-32 `[R-SHARD]` container pinned to `5f133fd5`:** ST_GAS forced
share 54.3/64.0/46.5/39.1/36.6/41.3 % → **16.1/25.6/15.7/8.2/7.4/7.7 %**; D-4 per-unit conduct
convictions 10/8/8/6/4/5 → **3/2/2/1/2/2**, the survivors in every year *exactly* the non-admitted
plants. Rule 17 leave-one-year-out: the arm reads CALIBRATED in all three 2023–2025 pairs where the
incumbent reads NOT-YET in both pairs containing 2025.

**Costs, reported and not netted out.** 2024 ST_GAS moves off an exact 1.00 to 0.90 (pjm-d4-1 §4's
point landing: 2024 reached the right total by mandating a third of it); 2025 CT_PEAKER moves
1.19 → 1.23, further over actual, exactly as the PRECOMMIT pre-committed to accepting; part of the
released energy relocates onto CC_REGULAR and COAL_BIT, which were already high. Total fossil surplus
improves in all six years. **Plants 3138 (48.6 % duty) and 3131 (51.0 %) still fail D-4 in nearly
every year — an open root cause, routed not closed; they do not decide C8 only because the forced
share now clears the 30 % budget outright.**

**The holdout span is UNCHANGED — zero criterion flips** (NOT-YET both sides; C1 fuel-mix, C3a mean
LMP and C3b price shape fail in both). This card does not resolve the holdout-year rubric failures
and does not claim to; the ST_GAS collapse there is real but ungated (C8 skips ST_GAS as immaterial
at 0.8–1.1 % of load). Rule 30(c): a held-out year never downgrades PJM.

**Runs** `2026-09-10-pjm-d4-2-stgas` (2023–2025, CALIBRATED) + `2026-09-10-pjm-d4-2-touchpoint`
(2020–2022, folded under rule 30(a)). **Keeper promotion is the OWNER's call (rule 31 `[R-RETAIN]`)
and is put explicitly** in `docs/RESULT-pjm-d4-2-stgas-membership-2026-09-10.md` §9. Nothing was
deleted; the six shard bundles are gitignored on local disk.

**Routed follow-up:** `ST_GAS_PEAKER_PLANTS` is solve-affecting but invisible to `cache_key()` (not
in `solve_surface.SURFACE_MODULES`, and `SOLVE_EPOCHS` is empty). This predates the card but the card
makes it materially larger for PJM; `data/outages.py` imports numpy/pandas so it cannot join the
stdlib-only surface, leaving a `SolveEpoch` as the route.

## pjm-d4-3 — 2026-09-10

**The holdout-year card: object measured, arm already adjudicated, keeper UNCHANGED.** Nothing was
promoted, nothing registered, no matrix verdict moved. PJM's training span re-scores **CALIBRATED**,
0 caveats, determination basis *"all criteria pass, governance attested"* (rule 30(c) confirmed).
Full record: `docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md`; PRECOMMIT
`docs/PRECOMMIT-pjm-d4-3-da-virtual-net-2026-09-10.md`, pushed at `6eb223b5` before any solve.

**Phase 0 (zero LP) answered both handoff questions.** The CC_REGULAR holdout surplus decomposes
(model-vs-CAMPD per plant-hour, identity closing to ≤4.5 GWh/yr) into a **chronic online-hours leg**
(`a−c` = +16.4/+18.5/+14.4 TWh 2020–22 but also +8.8/+8.3/+6.4 in the CALIBRATED training years) and
a **holdout-distinctive loading leg** (`b+−b−` = +18.2/+19.5 in 2021/2022 against +1.7–5.2 in
training, and only +1.5 in 2020) — **two objects, not one**. It is **not forced**: D-2
`cc_mustrun_per_plant` forces 9.444/6.409/9.429 TWh in 2020–22 against 23.758/13.338/10.523 in
2023–25, i.e. least where the surplus is largest.

**The new measurement.** `virtual_bids.py` states its rule-13 admissibility as *"the annual net of
the whole curve cleared at actual DA prices is ≈ 0"*, measured on 2023–2025 only (pjm-105).
Recomputed from the module's own loader for all six years: **+16.537 / +16.812 / +12.248 TWh in
2020/2021/2022** against −0.755/−1.620/+0.204 in 2023/24/25 (reproducing pjm-105 in sign and order;
the 0.72/1.10 TWh 2024/2025 differences are unreconciled and reported). **In the holdout years there
is no price at which this curve nets to ~0** — the ≈0 anchor is a property of 2023–2025, which
corrects the pjm-158 DA−RT framing without changing its disposition.

**The 2022 screen: all four pre-registered gates PASS, and G3's composition refutes my own
attribution.** Removing 13.0134 TWh of net virtual demand returns **−13.0382 TWh** of physical
supply (the identity to 0.19 %) — but **CC_REGULAR absorbs only 1.876 TWh (14.2 %), i.e. 7.0 % of
its own +26.817 TWh C1 miss**, not the 41.5 % the arithmetic suggested. **CT_PEAKER (−5.395) and
COAL_BIT (−3.643) carry it.** pjm-158's in-sample gain of ~0.7–1.0 TWh CC per TWh net virtual, which
pjm-166 transported to bound 2022 at ~44 % of the CC_REGULAR miss, **measures 0.14 here — ~5×
smaller.** Cost of the arm, reported never gated: mean price −1.72 $/MWh on a control already −11.9 %
on C3a, hour-of-day price range −28.7 %, CT_PEAKER's miss more than doubling, storage throughput
−41 %.

**DO-NOT-REDO failure, mine.** The arm (`pjm_da_virtual_bids=false`) was solved as a full 2023–2025
A/B by **pjm-158** with both arms registered, and the architecture closed by **pjm-159** inside the
owner's price-formation frontier; **pjm-166** had already routed it *"NOT A LEVER"*. I launched the
shard before finishing the rule 28(a) matrix read. The cell **stays `K`** and is re-stamped with the
2020–2022 anchor measurement and the corrected gain. The same read also retired a second lead before
it cost an LP (the flat-backcast-coal / gas-coal merit-order framing — pjm-166 already ruled it out
on a sign test my own gas measurement, 4.115/7.116 $/MMBtu, reproduces exactly).

**Retracted so no successor chases them:** the flat diurnal price amplitude is **not** a holdout
signature (D-A 39.3/34.4 % of measured in 2021/2022 but 30.6/29.0/32.3 % in the CALIBRATED
2023/24/25); and demand/exports move the surplus the **wrong** way (model demand within
+1.11/+2.15/+1.84/−0.46/−0.00 TWh of EIA-930; model net exports BELOW actual by 13.59/8.65/8.65/10.07
TWh in 2021–2024).

**G-DRIFT is RUNNABLE for PJM again** — the keeper's `git_sha` `5f133fd5` is post-rewrite and alive,
and all 13 changed solve-path files since it classify INERT, so **G-CTRL form 4 holds and no control
solve was spent**. Three prior sessions' "NOT RUNNABLE" is stale and should not be inherited.

**Escalated, not absorbed:** (1) the shard edited `scripts/replay_keeper.py` against its own prompt
and auto-merged as `ae3d9982` — reviewed on merits and **left standing**, because it reveals that
**every composed multi-year keeper bundle on `main` was unreplayable**, `pjm_d4_2_TP`/`pjm_d4_2_A`
included; (2) the shard's screen bundle auto-merged as `db564ec5` and is **untracked here**
(`git rm -r --cached`, never `rm` — rules 29(c)/31); (3) the PJM hydro deficit (m/a ≈ 0.56) may be
partly a **pumped-storage accounting seam** — bench `hydro` is EIA-930 `NG: WAT`, which includes PS
gross generation, while the model carries PS in its storage class (discharge 5.09–5.79 TWh/yr); not
resolved here, routed to the hydro lane. Inherited open items are untouched: plants 3138/3131 D-4,
and `ST_GAS_PEAKER_PLANTS`'s `cache_key()` invisibility.

## 2026-09-10 — pjm-d4-4: the forced-outage composition gap — kill gate PASSED, mechanism built, one screen gate retired on arithmetic

Session `pjm-d4-4`, branch `claude/pjm-forced-outage-gap-o0kzlz`. **Keeper UNCHANGED** at
`2026-09-10-pjm-d4-2-stgas` (+ `-touchpoint`, folded); rule 30(c) untouched, `audit_keepers --iso
PJM` and `build_status --check --iso PJM` both pass. **Nothing promoted, nothing armed by default,
nothing registered on the dashboard.** Full record:
`docs/RESULT-pjm-d4-4-forced-outage-composition-2026-09-10.md`; pre-registration
`docs/PRECOMMIT-pjm-d4-4-forced-outage-composition-2026-09-10.md` (the kill bar, committed BEFORE
the measurement) and `docs/PRECOMMIT-pjm-d4-4-screen-addendum-2026-09-10.md` (the screen gates,
committed BEFORE the shard).

**THE DEFECT.** `outages.UNIT_OUTAGE_MIN_DAYS = 5` discards every shorter outage window, and the
sub-floor companion that recovers them (`unit_outage_short_windows`, ARMED in the keeper)
re-filters to `plant_group == "COAL"` — so the 0–5 d family is captured for coal and **thrown away**
for CC_REGULAR / CC_CHP / ST_GAS / ST_CHP. Verified on disk: the ≥5-day extract's min duration is
exactly 5.0 d, and `campd-unit-outages-short-PJM.csv` is 934 rows, **100 % COAL**. (CT_PEAKER is not
reachable by this family at all — outside `QUALIFYING_PLANT_GROUPS`, CT_CHP dropped at routing — so
the handoff's naming of it does not survive contact with the machinery.)

**THE KILL GATE, registered first and then measured.** Both bars in `a231d912`, before any gas
window was detected; neither reads a price residual. G-KILL-1 (mean removed-availability MW over
2022's 92 actual RT>$200 hours, bar = ¼ of the +9.7 GW model-minus-meter over-dispatch in exactly
those hours): **4,570 vs 2,425 → PASS 1.88×**. G-KILL-2 (annual mean, bar = 10 % of the +6,999 MW
forced gap): **1,185 vs 700 → PASS 1.69×**. That is ~**5×** the handoff's own naive scaling
prediction of 200–380 MW, because window *count* was the wrong scaling variable.

**IDENTIFICATION — tested, not assumed.** ERCOT's lane had struck a near-neighbour arm on the ground
that a cycling unit's brief stop can be economic dispatch (rule 28(d): that verdict is ERCOT's and
stands there). The gas scope answers with a different instrument: `SHORT_BASELOAD_CF` is a BASELOAD
guard a cycling CC cannot pass, so the gas leg carries the **merit-order guard** instead — SRMC
against revealed clearing cost — and the derive CLI *refuses* to emit it without one. Measured:
the guard removes **10.8 %** of the annual mean and **5.1 %** of the tail (93 of 494 windows), and
the committed artifact carries the **smaller, guarded** family — a choice against interest, since
both clear both bars. Corroboration is a **natural experiment**: over Elliott (Dec 24–27 2022) PJM
published FORCED 31,078 / 35,844 / 27,058 / 24,052 MW against a recovered family of
10,998 / 13,611 / 13,297 / 10,158 MW, rising from a 3.0–4.5 GW pre-event baseline — in hours whose
RT averaged **$844**, where nothing idles economically.

**REPORTED AGAINST INTEREST, not netted out.** corr vs published FORCED is **+0.395** (2022) and
**+0.314** (2021) but **+0.106 / +0.047 / +0.003 / −0.015** in 2024 / 2023 / 2025 / 2020; **2025 has
the LARGEST published forced outage (10,531 MW) and the SMALLEST recovered family (587 MW)**; the
family *falls* through the 2025 named event (0.33× annual) where it rises **8.6×** through Elliott;
and even in 2022 it is Elliott-weighted (9,639 MW over the 35 December tail hours against 1,854 MW
over the other 57). It closes **19 %** of the composition gap (6,999 → 5,814 MW; forced-like share
6.8 % → 10.5 % against a published 26.6 %), not the gap. **The honest reading: this family
reproduces correlated event-driven gas forced outage — which is what 2022's missing tail is made of
— and does NOT reproduce PJM's 7.7–10.5 GW baseline forced outage.**

**THE HANDOFF'S OWN FIRST SCREEN GATE IS RETIRED ON ARITHMETIC, BEFORE THE LP.** It asked for "the
reserve dual becoming non-zero in the target hours". Tail-hour headroom ≈ **19 GW** (ADDENDUM §3)
minus the arm's 4,570 MW leaves ≈ **14.4 GW**, against a `pjm_primary` requirement whose **maximum**
is 4,224 MW — 3.4× over. The dual cannot move, and spending a PJM year to rediscover a subtraction
is what rule 29 clause 0 forbids. **The cost is stated, not absorbed: this mechanism cannot alone
restore PJM's scarcity price formation**, and the co-opt's inertness is now a *sized* open root
cause — any mechanism that wants `pjm_primary` to bind in 2022 must find **~15 GW**, not 4.6.

**BUILT (default off, nothing armed).** `ScenarioConfig.unit_outage_short_windows_gas` +
`outages.unit_outage_short_gas_csv_for_iso` / `_SHORT_GAS_GROUPS`; derive
`--short-window-groups {coal,gas}` writing a SEPARATE companion so the coal extract is never
rewritten; `data/raw/campd-unit-outages-shortgas-PJM.csv` (1,859 windows, 2020–2025) + its layup
companion (439 reclassified); matrix row + a cell in all seven shards (PJM `O`, every other `U`,
ERCOT's recording that its own objection stands); cache-key registration in the same commit; four
tests. **Off-path byte-inertness PROVED** over 7 ISOs × 4 years × `extract_basis_share` {False,
True}, digests identical to `origin/main`; the derive's coal default path `diff`-identical.
Zero free parameters — the boundary is the categorical 7-day sign flip (8 positive cells, 12
negative, zero exceptions across 2022–2025) and it was **not re-swept**; rule 23 is satisfied
because the **scope** was wrong, a construction repair.

**G-DRIFT passes EXACTLY and no control solve was spent** — a stronger form than the file-by-file
audit the prior entry used: the keeper's own 833-field `cache_key()` is the identical
`725009b54d387c32` at `git_sha` `5f133fd5` and at HEAD, and since capx D79 that key carries the
solve-surface fingerprint, so an unmoved key certifies no registry table, no solve-surface row and
no config default the keeper touches has moved. **The committed keeper bundle IS the control.**

**Escalated, not absorbed.** (1) The co-opt's inert dual, now sized at ~15 GW — `ordc_scarcity_overlay`
is `G` on the premise that "the in-LP co-opt already owns the phenomenon", which is measurably false
in 2021–2023; still **not** a licence to arm the adder. (2) The cross-year weakness above is
unexplained. (3) A 2.5 % boundary-day double count (47 of 1,851 unit-days) — pre-existing, the
`unit_outage_per_unit_clip` `U` cell's object, unrepaired here. (4) Inherited and untouched: the
hydro pumped-storage accounting seam, `ST_GAS_PEAKER_PLANTS`'s `cache_key()` invisibility, plants
3138/3131 D-4, and the `da_virtual_bids` anchor not reproducing in 2020–2022.

**The rule-31 `[R-RETAIN]` promotion question is asked explicitly** in RESULT §10: should the full
six-year span (2020–2025, six shards, one bundle) be spent? Session recommendation, stated so it can
be overruled: **spend it** — rule 14 `[R-ACCURATE]` says an accurate input that worsens the fit is a
discovered bug, and this is a **discard**, not an estimate. Nothing is deleted while the decision is
open; `.gitignore` line 1757 already keeps the bundle family out of `main`.

### pjm-d4-4 SCREEN RESULT (same session, appended after the shard returned)

**S-1, S-2 and S-4 PASS; S-3 FAILS by 3.4×. The arm is NOT carried to the full span on this card's
rationale, and its tail-repair claim is REFUTED.** One shard, 2022, pinned to `57c3557e`; 24 min 13 s,
peak RSS 13.94 GB — **4 minutes over the rule-32(b) budget**, worth knowing before six of them are
launched. Every number: `docs/SHARD-REPORT-pjm-d4-4-screen-2022.md`.

| gate | measured | bar | verdict |
|---|---|---|---|
| **S-1** envelope depth, annual / tail-hour | **+1,049.8** / **+4,323.6** MW | +1,185 ±15 % / +4,570 ±20 % | **PASS**, inside both |
| **S-2** confinement | CC_REGULAR +984.0, CC_CHP +44.1, ST_GAS +19.9, ST_CHP +1.8 MW; **CT_PEAKER and every coal group 0.0** | gas groups only | **PASS**, exact at the input layer |
| **S-3** model−meter thermal gap over the 92 RT>$200 h | **0.592 GW** fall (89.930 → 89.339 vs a meter of 80.100) | ≥ 2.0 GW | **FAIL** |
| **S-4** non-target load-bearing flip | none, either direction | none | **PASS** |

**THE ROOT CAUSE IS NAMED, NOT LEFT AS A NULL: the LP BACKFILLS 87 % of the withdrawn gas, mostly
with coal** (CC_REGULAR −4.2555 TWh, CT_PEAKER +1.6850, COAL_BIT +0.9200, ST_GAS +0.4350). **PJM's
2022 tail defect is therefore not gated by gas availability at all** — it is gated by what stands
behind the marginal gas unit in the merit order. The arm adds **zero** model hours above $200 on
every system price basis (3 on the max-zonal basis, unchanged, an oil unit's own $247.50 offer) and
C3c is untouched at 3 h vs 92 h.

**REPORTED, GATED IN NEITHER DIRECTION, AND NOT USED TO RESCUE THE ARM (rule 1 `[R-STRUCT]`):** C3a
−11.9 % → −10.7 %, C3b 0.262 → 0.246, C1 CC_REGULAR +26.82 → +22.56 TWh — all improve, all still
FAIL. C8: every non-exempt forced share falls. C6 **UNSCOREABLE** on the arm (a `replay_keeper` probe
writes no attestation). **REGRESSIONS AT FULL MAGNITUDE:** COAL_BIT +6.60 → +7.52 TWh, COAL_PRB
+0.42 → +0.57, ST_GAS +2.46 → +2.89, **C2 coal 159.63 → 160.74 against 152.72 actual** — all still
PASS, all the wrong way.

**A PREDICTION OF THIS SESSION'S WAS FALSIFIED, AND IT IS THE MOST CONSEQUENTIAL OUTPUT.** The entry
above retired the handoff's reserve-dual gate before the solve, on the arithmetic that ~19 GW of
tail-hour headroom minus 4.57 GW cannot reach a requirement whose **maximum** is 4,224 MW.
**`pjm_primary_mad` BOUND in 2 of 8,760 hours at $11.42 and $12.26/MW, and BOTH hours are inside the
92 target hours** (actual RT $369.54 / $410.24), at a requirement of **~2,722 MW**. The control
baseline is CONFIRMED (0 non-zero-dual hours in 2022, both families), so the ADDENDUM §2 reading
stands; what was wrong is that **a system-wide headroom number cannot decide whether a LOCATIONAL
family binds**. Retiring the gate before the solve was procedurally right and substantively wrong,
and both statements are left standing in place rather than edited away. **Escalated:** the PJM
co-optimisation is closer to binding than the committed record implies, and the binding object is
locational — which no measurement in this lane had reached. `ordc_scarcity_overlay` stays `G`; a
stack on a mechanism that *does* bind is worse, not better.

**Also corrected:** the **+9.7 GW** control tail gap quoted above and in the PRECOMMIT is an
arithmetic slip inherited from `docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md` §3, whose own
operands (89.9 and 80.1) differ by **9.83**. G-KILL-1's bar moves 2,425 → 2,458 MW and the measured
4,570 clears both, so **no verdict changes**.

**Matrix cell `unit_outage_short_windows_gas` stays `O`, deliberately not `R`.** What the screen
refuted is one CLAIM (the tail repair — **do not re-test it**), not the mechanism: it replaces a
**discard**, not an estimate, with measured merit-guarded windows, and rules 14 `[R-ACCURATE]` / 1
`[R-STRUCT]` both say such an input is not judged by the residual. Whether to land it as an input
correction is an open owner decision.

**THE SESSION'S RECOMMENDATION CHANGED AFTER THE SCREEN and is recorded as changed: do NOT spend the
six-year span now.** Before the screen it recommended spending it. Rule 29 clause 0 exists so the
remaining five years are not spent confirming a mechanism cannot do the job it was built for. The
successors the screen points at, in the order the evidence now supports: **(a) the merit order** —
what sits behind the marginal gas unit; **(b) the locational reserve family** just measured binding;
**(c) partial derates** (`ercot_partial_outage_shaped_derate`, `·`, unbuilt). (a) and (b) both
outrank (c), reversing the ordering this lane inherited. **Rule 31:** the 196 MB screen bundle lived
on the shard's ephemeral disk, gitignored, never committed, never `rm`'d, and does not survive that
session; every number it produced is committed in the shard report.

## 2026-09-11 — pjm-d4-4 PROMOTED: `2026-09-11-pjm-d4-4-gasoutage` is PJM's keeper

**KEEPER CHANGED** from `2026-09-10-pjm-d4-2-stgas` to **`2026-09-11-pjm-d4-4-gasoutage`**
(2023-2025), with **`2026-09-11-pjm-holdout-gasoutage-touchpoint`** (2020-2022) registered and
FOLDED to it under rule 30(a). Owner ruling in force: *"If structural integrity improves but gates
regress that may still be a keeper"* — though **the arm did not need that latitude**: no training
gate regresses out of band.

**DETERMINATION `CALIBRATED` · 8/8 target grade · 0 caveats · 0 fails · EVERY criterion PASS.**
Verified by re-running `scripts/calibration_verdict.py` against the registered run in the parent
session, **not** accepted from the solving shard's report. Basis, verbatim: *"all criteria pass,
governance attested."*

| criterion | verdict |
|---|---|
| C1 fuel-mix (grid-delivered) | PASS — 16/16 all, 12/12 free |
| C2 system volume · C3a mean LMP · C3b shape · C3c tail | PASS |
| **C4** dispatch correlation | **PASS** — gas r 0.945/0.942/0.945, coal r 0.920/0.935/0.943 |
| **C6** governance | **PASS**, attested |
| **C8** forced share (D-2) | **PASS**, inside every cap |

**C4, C6 and C8 were measured on this arm for the FIRST time at registration.** Every earlier
number in this lane came from a substitution method that could only reach `gmModel` and `lmp`; that
gap is now closed and all three pass.

**THE DELTA IS ONE GATED FIELD**, `unit_outage_short_windows_gas` (default off), with **zero free
parameters and zero fitted scalars**; the DOF ledger is unchanged at 19 entries / 6 residual. It
widens a **DISCARD** — `UNIT_OUTAGE_MIN_DAYS = 5` threw away every shorter window and the sub-floor
companion re-filtered to COAL — replacing it with measured, merit-guarded CAMPD windows for
CC_REGULAR / CC_CHP / ST_GAS / ST_CHP. Rules 14 `[R-ACCURATE]` and 1 `[R-STRUCT]`, not the residual,
are the basis.

**GAINS:** C3a improves in all three training years (−1.3/−5.2/−8.3 % → −0.5/−4.2/−7.8 %); C1's
worst cell CC_REGULAR improves **6.04 → 2.86 TWh** (2023) and **4.08 → 0.67 TWh** (2024); on the
holdout, 2020 C1 CC_REGULAR flips **FAIL +10.28 → PASS +7.56 TWh**.

**REGRESSIONS AT FULL MAGNITUDE, none leaving a PASS band:** COAL_BIT 2023 +1.33 → +2.10 TWh,
CT_PEAKER 2024 +0.54 → +1.82, ST_GAS 2023 +2.04 → +2.44, C3b 2023 0.111 → 0.112, C2 coal 2025
+9.3 → +9.6 %. **On the holdout**, 2020 degrades on C3a (+21.4 → +22.3 %), C3b (0.234 → 0.242) and
COAL_BIT (+21.97 → +22.83) — all already FAIL, and **PREDICTED**: 2020 is the OPPOSITE defect
(model over-prices), so a deeper outage envelope must worsen it. Rule 30(c) applies.

**WHAT THIS PROMOTION IS NOT, and it must not be misread.** It is an **input correction**. The
stage-2 screen's S-3 **FAILED by 3.4×** — 0.592 GW of a 9.830 GW tail gap closed against a 2.0 GW
bar — because **the LP backfills 87 % of the withdrawn gas, mostly with coal**. The arm adds **zero**
model hours above $200 on any system price basis and leaves C3c's tail count unmoved. **PJM's 2022
tail defect is not gated by gas availability at all** — it is gated by what stands behind the
marginal gas unit in the merit order. **The tail-repair claim stays REFUTED; do not re-test it.**

**THE PRODUCTION PATH REPRODUCED THE PROBE PATH EXACTLY** — 2022 solved through
`run_calibration_full --replay-bundle` lands on every cell the `replay_keeper --set` screen
predicted (CC_REGULAR +22.56 TWh, COAL_BIT +7.52, CT_PEAKER −1.45, ST_GAS +2.89, C3a −10.7 %,
C3b 0.246).

**Rule 32(b) exception, stated on the run rather than papered over:** the six years were solved
**sequentially in ONE invocation in ONE container** (~60 min), because the payload builder reads
heavy per-year parquets that cannot be assembled across containers. Six per-year shards had already
solved the arm; their slim pushes could not be registered, which was a shard-prompt design error.

**Escalated, not absorbed:** `pjm_primary_mad` **BOUND in 2 of 8,760 hours** at $11.42 / $12.26 per
MW, **both inside the 92 target hours**, at a requirement of ~2,722 MW — the first non-zero PJM
reserve dual measured in this lane, and it **falsified this session's own pre-solve prediction**
that a ~19 GW system-wide headroom made binding impossible. The binding object is **locational**,
which a system-wide number cannot decide. `ordc_scarcity_overlay` stays `G`.

**Known warning, deliberately not silenced:** `audit_keepers --iso PJM` reports E3 — the A bundle's
`meta.json` years [2023,2024,2025] differ from `calibration_flags` years [2020…2025], because one
six-year invocation was split into A and TP. The scorer uses `meta.json`. **Rewriting provenance
metadata to quiet an auditor would be the wrong trade**, so it stands as a documented warning.

**Successors, in the order the evidence now supports:** (a) the **merit order** behind the marginal
gas unit; (b) the **locational reserve family** just measured binding; (c) partial derates
(`ercot_partial_outage_shaped_derate`, `·`, unbuilt).

## 2026-09-12 — pjm-h1: the hydro miss is **100 %** an accounting seam, and CC_REGULAR is the only PJM class whose CF does not track reality

**KEEPER UNCHANGED** at `2026-09-11-pjm-d4-4-gasoutage` (2023-2025), re-scored in-session:
**CALIBRATED, 8/8, 0 caveats, 0 fails**, basis verbatim *"all criteria pass, governance
attested."* Holdout `2026-09-11-pjm-holdout-gasoutage-touchpoint` unchanged at NOT-YET.
**ZERO LP. Nothing solved, nothing registered, nothing armed, no cell verdict moved, and no
shared code changed.** Records: `docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md`,
`docs/FINDING-pjm-h1-cc-cf-does-not-track-2026-09-12.md`.

**(1) THE HYDRO CARD'S PREMISE IS REFUTED AND THE SEAM IS BIGGER.** The commissioning card said
`classify_plant`'s `fuel == "WAT"` short-circuit puts ~5-6 TWh/yr of PS *gross* generation into
the EIA-923 `classFull.hydro` actual. Two measurements kill that: **EIA-923 reports PS as NET
generation, which is NEGATIVE** (PJM −1.78 to −2.67 TWh/yr), and **the 923 bucket is not the C1
actual for PJM anyway** (6.19-8.44 TWh vs a bench `classFull.hydro` of 15.47-16.64). The real
mechanism is `run_calibration_full._backfill_renewables_eia930`, which lists `hydro` in
`_EIA930_RENEWABLE_CLASSES` and **replaces the class with EIA-930 `NG: WAT`** when the 923 total
is below 0.90× it — for PJM the ratio is 0.39-0.55, so it fires every year — and
`constants.EIA930_PS_FOLDED_INTO_WAT` already declares `{MISO, PJM}`: PJM files no `NG: PS`, so
its `NG: WAT` folds PS **gross discharge**, 5.96-7.11 TWh/yr at an implied round-trip efficiency
of **0.72-0.77** (the physical cross-check). **Like-for-like the model's conventional hydro is
within ±0.9 % in every complete-vintage year** — stated as *plumbing, not skill*, since
`hydro_level_923_hy` pins that level and hydro is a declared D-10 free class (L6).
**The asymmetry is self-inflicted:** pjm-143 fixed this contamination on the MODEL side
(`hydro_level_923_hy` `U` → `K`) and its §7 open list names three items, none of them the
benchmark.

**THE CARD IS CORRECTED ON THE STAKE, AND IT IS SMALLER THAN IT SAID:** **`hydro` is not a C1 row**
(`score_fuelmix` iterates gas+coal only; `class_is_gated` is the 923 *vintage-completeness*
predicate). The repair moves the C1 volume band by **0.000 TWh** in all six years (the 8 TWh cap
binds either way) and flips **zero** C1 cells. Gate-neutral — which is why it cannot be a
residual fit. Blast radius measured: **PJM all six years (5.96-7.11), MISO 2020+2022-2025
(0.39-1.70), NEISO 2020-2022+2024 (0.42-0.68)**; ERCOT/CAISO/NYISO/SPP clean. `classify_plant`
IS defective (it contradicts its own comment, and makes
`run_calibration_full._pumped_storage_plant_ids()` a dead no-op) but only by −0.05 to −0.72
TWh/yr, in the opposite direction, where the 930 swap does not fire. **ESCALATED, NOT EXECUTED
— shared ISO-agnostic code, rule 25.**

**(2) A NEW HOLDOUT OBJECT, AND THREE DEAD CANDIDATES.** Matched-fleet annual CF, model vs CAMPD,
2020-2025: **CC_REGULAR is the ONLY PJM class that does not track reality** — cross-year
**r = −0.183**, model CF range 0.015 against the meter's 0.058 — while COAL_BIT **+0.912**,
CT_PEAKER **+0.896**, ST_GAS **+0.968** and CC_CHP **+0.775** all do. The model runs the 54-62 GW
merchant CC fleet at 0.606-0.621 every year; the meter moves 0.550 (2021) / 0.563 (2022) /
0.586-0.609 (2020, 2023-25). **The two flattest years are exactly the two C1 failures.**
**FALSIFIED at zero LP, so no successor spends an LP on them:** partial derates / capability
(meter revealed capability p99.5/npl is FLAT at 0.894-0.912, 2022 the *highest* of six; and
`campd-partial-outages-shaped.csv` carries **zero PJM rows**); a `measured_cc_heat_rates`
candidate (CAMPD `heatInput/grossLoad` over 4,756,608 unit-hours on all 70 plants: model
**7.1954** vs measured-net **7.2974** capacity-weighted, i.e. **1.4 % cheap**, median per-plant
delta **+0.008**, and **39 of 69 plants DEARER in the model** — reported against this session's
own hypothesis); and any pjm-d4-2-shaped membership repair (the over-run is fleet-wide, 46-47 of
68-70 plants). **The survivor is price-distribution compression** (D-A amplitude 29.9-32.9 % of
measured in every year) pinning a large mid-merit class online 78-83 % of hours at 72-76 %
loading — inside PJM's owner-declared-closed price-formation frontier (pjm-142). **ROUTED to the
standing pjm-159 escalation, not pulled as a lever**, now carrying a refutable prediction it did
not have: an amplitude repair that leaves CC_REGULAR's cross-year CF correlation at ≈ 0 has not
addressed it.

**(3) A PRE-EXISTING PJM PARITY RED DISCHARGED, AND A RULE-TEXT DISCREPANCY FOUND.**
`results/calibration/pjm_d4_4_y2025` — a leftover per-year shard dir whose 2025 sidecars are all
duplicated in the registered composite `pjm_d4_4_A/hourly/` — is untracked and gitignored, **never
`rm`'d** (rule 31, the ercot-255 incident; bytes stay on local disk, history keeps the blobs).
Reported: rule 31 asserts the parity gate *"only ever sees committed dirs"*, but
`check_registry_payload_parity.py:437` sweeps `calib_root.iterdir()` — the **working tree**. The
conclusion holds in CI (fresh checkout, dir absent, gate passes) and fails locally, which is the
exact state rule 31 tells a lane to leave bundles in. Not fixed here — shared infrastructure and
a governance choice. `results/calibration/nyiso227_rebasis_span` is the **other** pre-existing
red and is **NYISO's lane, untouched**.

**GATES:** `audit_keepers --iso PJM` PASS (0 failures, the known-and-deliberate E3 warning
stands); `build_status --check --iso PJM` in sync; `check_mechanism_matrix --base origin/main`
integrity OK; `check_cache_key_registration` OK (no new fields); `check_gate_a_provenance` fails
on **CAISO's** row only (pre-existing, another lane's); `pytest tests/scoring` **16 failed** —
all 16 reproduce on an unmodified `origin/main` tree, **none new** (the handoff's baseline of 15
is stale by one).

## 2026-09-12 — pjm-h2: phase 0 kills the holdout arm; the real basis defect has not landed yet

**ZERO LP.** Parent never solved, no shard launched (rule 32 `[R-SHARD]` (a)). Nothing armed,
nothing registered, no shared code changed, no `ScenarioConfig` field added, **no matrix cell
verdict moved** (no mechanism tested). **Keeper `2026-09-11-pjm-d4-4-gasoutage` UNCHANGED and
re-scored before AND after: CALIBRATED, 8/8, zero caveats, zero fails.** Touchpoint
`2026-09-11-pjm-holdout-gasoutage-touchpoint` NOT-YET, 4/8, before and after.
Record: `docs/FINDING-pjm-h2-holdout-basis-2026-09-12.md`.

**Step 1 — the basis split, quantified.** `FINDING-pjm-holdout-phase0` §4's "live lead" is
**REFUTED on arithmetic**: `reconcile_vintage_classes` fires in **no** PJM year 2020-2025. §4
tested against the **undeflated** EIA-930 gas+coal cell; the code deflates it by
`gas_foldin_deflation` first, and with the deflation the ratios read **0.9713 / 0.9721** — inside
the 0.97 deadband. All six committed years are on ONE construction. Basis share of the all-fossil
C1 residual: **2020 4 %, 2021 55 %, 2022 43 %**; per class **COAL_BIT 2020 1.6 %**, **CC_REGULAR
2021 31 % / 2022 38 %**. **No C1 cell flips** on the correction (+22.47 / +18.06 / +14.04 TWh
against an 8 TWh band), so what survives is real model error.

**The defect that has not landed.** `gov-hydro-seam-1`'s PS→`OTHER` half (`26f8508b`, merged)
drops PJM's `OTHER` by 1.78-2.67 TWh/yr → shrinks the fold-in → raises the reconcile target →
pushes **PJM 2021 and 2022 out of the deadband** (margins were 0.64 / 1.06 TWh). At the next
registration the reconcile **fires** (×1.03343 / ×1.03281): C1 CC_REGULAR **+26.31 → +16.98** and
**+22.56 → +12.81 TWh**, COAL_BIT 2021 **+1.33 → −3.71** (sign flip), 2022 +7.52 → +3.05; **2020
unmoved at +22.83 FAIL**. Swept over all 42 committed parts in all seven ISOs: **exactly two
ISO-years, both PJM**. All 8 registered PJM runs re-scored on HEAD-basis parts: **zero
determination flips, zero status flips**. So `gov-hydro-seam-1`'s gate-neutrality headline
survives, but its magnitudes claim does not — it substituted only the repaired `hydro`, and the
reconcile's *trigger* reads `OTHER`. **ESCALATED, not executed** (rule 25 `[R-ISO-SCOPE]`, pjm-h1
precedent): whether PS-net-inclusive `OTHER` is the right operand for `gas_foldin_deflation` is a
shared ISO-agnostic construction question — EIA-930's "Other Fuel Sources" carries no pumped
storage. Owner's call; worth 9.3-9.8 TWh of held-out C1 and **zero determinations**.

**Step 2 — no admissible arm.** (a) The merit-split cell is `R` (pjm-166) on a statistic — coal
share of coal+CC — that is **exactly scale-invariant** under a uniform reconcile, so the basis
finding is provably **no** evidence about the split; rule 28(a) holds. (b) Restoring **2020**, the
year pjm-166 omitted, gives a **non-monotone** coal-share error in the gas level (+2.88 / −0.39 /
+0.00 / −2.14 / +1.18 / −0.49 pp at $1.94 → $6.47) — not a merit-position signature, and picking
2020 because its Δ is largest would be picking on the residual. (c) On the EIA-930 basis only
**2020** is anomalous: held-out fossil surplus **+29.6 / +8.6 / +16.3** TWh against an in-sample
**+3.6 / +7.6 / +21.1** — 2021 and 2022 sit *inside* the in-sample range. **Successor unchanged
and not this lane's to open:** the DA-virtual net cleared position (cell `K`, owner-escalated
inside the closed price-formation frontier), which swings ~12-14 TWh across the tier boundary;
plus, 2020 only, a **+8.44 TWh (+1.11 %)** demand over-statement and a −2.85 TWh export shortfall,
which together close 2020's +10.84 TWh generation excess.

**Corrupt EIA-930 PJM 2021 `net_gen` — verified, not assumed.** The scorer **never reads it**
(`net_gen` appears zero times in `calibration_verdict.py`; `_gen_totals` sums `classFull`/`gmModel`)
— **C2 is cleared**. The benchmark builder **does**: `_vintage_completeness(2021, PJM)` reads
**0.1654** against a true ~0.98, so both consumers enter their `<0.90` branch — and both are
blocked by the `est > annual` guard (`est` 0.977 / 1.257 TWh vs `annual` 5.957 / 7.543).
**Inert in effect, latent trap in kind**: the guard holds only because the corruption is ~6×.
Escalated for repair of the committed extract.

**Gates:** `check_mechanism_matrix --base origin/main` exit 0 · `audit_keepers --iso PJM` PASS 0/1
· `build_status --iso PJM --check` in sync · `check_gate_a_provenance` OK · `check_cache_key_
registration` ok · `pytest tests/scoring` **15 failed / 1474 passed — exactly the stated baseline,
zero new** · `check_registry_payload_parity` **5 pre-existing REDs, all committed on `origin/main`,
none this lane's**: `nyiso227_rebasis_span`, `caiso275_B_gascoupling_{2023,2024,2025}` and a NEW
one since this card was written, **`spp36_2025`** (SPP's lane). Not touched — rule 31 `[R-RETAIN]`
forbids reaching for `rm` on another lane's solved bundles.

## 2026-09-12 — pjm-h2 part 2: it is NOT the coal sigmoid and NOT the CC bands; seven candidates killed at zero LP

**ZERO LP.** Parent never solved, no shard launched. Nothing armed, nothing registered, no
verdict moved. **Keeper `2026-09-11-pjm-d4-4-gasoutage` UNCHANGED, CALIBRATED 8/8, re-scored after
the matrix edit.** Record: `docs/FINDING-pjm-h2b-coal-cc-object-2026-09-12.md`.

**Coal sigmoid — NO, measured three ways.** PJM BIT passthrough by year on the keeper's own gas
series: **0.674 / 1.011 / 1.315 / 0.757 / 0.753 / 0.965** (2020-2025). (a) **2022 sits at maximum
suppression — ×1.315, 74.8 % of hours pinned on the ceiling asymptote — and coal is still +8.0 TWh
over on the 923 basis**, so lowering the ceiling makes it worse (reproducing pjm-170). (b) **2020
sits on the same limb as the two passing years (0.674 vs 0.753/0.757) and is +23.1 TWh over** —
same curve position, twelve times the error. (c) **2021's 1.011 is the most cost-faithful value the
curve takes and 2021's coal is the best-matched year (−0.5 TWh)**; its C1 failure is CC_REGULAR
alone. The **full re-derivation is also killed**: the committed provenance row
(`coal_sigmoid_params.csv`, delivered 2026-07, never transcribed) `{0.50, 1.00, 7.08, 1.0}` gives
0.649/0.725/0.951/0.665/0.663/0.738 — **cheaper coal in every year**, so it moves 2020 the wrong
way and risks the keeper's 2023/2024.

**CC bands — NO.** The object is **on-hours, not price position**: model CC online **+7.7/+8.8/+5.8
pp** in 2020-2022 vs +4.6/+4.8/+3.7 in 2023-2025, CF flat at 0.606-0.621 in all six years against a
meter moving 5.8 points (pjm-h1, corroborated here). A band multiplier moves price position; it
does not make a flat fleet responsive.

**Market dynamics — YES, a fleet-size × price-variance product.** PJM 2020-2022 carried **5-9 GW
more coal** (model coal peak 37.3/40.6/36.7 vs 31.3/32.8/31.4 GW) and those years had a far wider
realised price distribution. The model's **D-A amplitude is 29.9-32.9 % of measured in EVERY year**;
flat dispatch against a big coal fleet is a large volume error and against a small one is not.

**Killed at zero LP, recorded so no successor spends a solve:** coal-sigmoid ceiling; coal-sigmoid
re-derivation; `gas_offer_margin_anchor_vintage` (already `R`, pjm-169); `retiree_vintage_status_
scope` (**7.5 MW** of PJM coal in every year); **partial derates / capability for COAL** (per-plant
CEMS p99.5 flat across all six years — pjm-h1's CC verdict extended to coal); forcing (D-2 coal
forced share **0.6-1.4 %** in the bad years vs **4.0-4.1 %** in the good ones); outage coverage
(20.4/18.4/18.5 GW-equiv 2020-22 vs 20.9/16.8/15.5 2023-25 — the bad years carry *more*).

**THE ONE SURVIVING ARM — a measured asymmetry in PJM's own offer registry.** PJM's registered
gas `phys_*` keys reproduce `data/raw/reference/pjm_campd_marginal_hr_summary.csv` **byte for byte**
(CC_REGULAR 1.015 / 0.87 / 1.052), while **COAL_BIT carries no `phys_*` key at all** — so PJM coal
keeps the fully fuel-scaled multiplicative markup that `gas_offer_net_revenue_margin` (cell `K`,
armed in the keeper) exists to retire, and because coal's offer is gas-keyed through the sigmoid its
above-physical markup swings ×0.674 → ×1.315 across 2020-2022. The artifact's COAL row is committed
and unused (0.916 / 0.803 / 0.809). **It is a BUILD, not an arm** — `coal_offer_net_revenue_margin`
as implemented is `_mustrun`-scoped and needs the ERCOT SCED TPO instrument, so pjm-146's block
stands and the cell stays `U`. **It does not reach a solve until the pre-solve offer-array delta is
computed and fixed in a PRECOMMIT** (rule 29 clause 0); screen year would be named on footprint.

**ROUTED, NOT OPENED:** the surviving explanation is price-distribution compression inside the
owner-declared-closed pjm-142 frontier. Re-opening it is an owner act.

## pjm-h3 — 2026-09-13 — the SYNCHRONIZED reserve sub-product split is REFUTED at the liveness gate

**Arm** `pjm_reserve_pergen_sync` (Manual 11 §4.2/§4.3.3), armed on the owner-RE-OPENED pjm-142
price-formation frontier (`docs/calibration-log/governance.md`, "2026-09-13 — OWNER RULING").
Pre-registration `docs/PRECOMMIT-pjm-h3-reserve-sync-2026-09-13.md`, pushed at
`ed6bb099…` **before any solve**; gates fixed there and not re-read.
Result: `docs/RESULT-pjm-h3-reserve-sync-screen-2026-09-13.md`.
**Keeper `2026-09-11-pjm-d4-4-gasoutage` re-scored BEFORE and AFTER: CALIBRATED, 8/8, zero
caveats — UNCHANGED. Nothing armed; the field stays default-off.**

**KILLED AT S2.** SYNC dual non-zero in **107 of 8,760 hours = 1.22 %** against a **≥20 %** bar and
against PJM's published **61.3 %** in 2022. The 2020/2021 years were never spent (rule 29 clause 2).

**STRUCTURALLY CORRECT, QUANTITATIVELY INERT — both halves measured.** S3 shape **PASSES**
($0.1333 at h16-18 vs **exactly $0.0000** at h01-04); S4 confinement **PASSES** (r = **+0.738**;
off-hour movement **0.17 %** of on-hour); S5 protected set **PASSES**. It books the rent to the
right product — the control priced 2 h in `pjm_primary_mad` (a *synchronized* requirement met by
*offline* capacity, the pjm-87 misrepresentation), the arm prices **0** there and **107** in
`pjm_sync_mad` (mean $6.23, max $65.27, **zero** shortfall hours). **But it moves nothing:**
CC_REGULAR **−0.0100 TWh** on 319.69; C1 +22.56 → +22.55; C3a −10.7 % → −10.7 %; C3b 0.246 →
0.246; C3c 3 h → 3 h; annual price 64.074 → 64.092 $/MWh.

**CAUSE — the supply margin, not the product definition.** Zero-LP census: PJM fleet 10-min ramp
**38.24 GW** availability-weighted (the solve independently logs 38.2 GW) against a measured SYNC
requirement of **1.71 GW** — **22.3×**, *wider* than the ~19× `FINDING-pjm-eas-screen-2026-09-07`
measured on the Primary requirement. Online-only scoping moves CT_PEAKER's 14.75 GW (mostly
offline) to NON-SYNC but leaves CC_REGULAR's 15.76 GW as the SYNC source, still ~9×.

**DO-NOT-REDO:** do not propose a further reserve-PRODUCT refinement for PJM price formation. The
tightest defensible definition the design space offers — online-only, 10-min deliverable ramp,
sharing the pool joint P+R headroom row — still cannot make reserve scarcity bind at this fleet
size. This **extends** pjm-eas's retirement of the reserve-scarcity lever family from the forecast
lane to the **backcast** lane.

**OPERATIONAL, reported because it is real:** the arm doubles the R-column count and OOM-killed P0
on **three** successive standard containers (anon-RSS 13.28 GiB vs a 13.34 GiB cgroup ceiling;
`memsw.max_usage` 17.33 GiB = ceiling + 4 GiB swap **exactly**). It completed only after
`hydrate_data.py --profile pjm --force` freed 4.1 GiB so the preflight could reach ~23 GiB. The
binding constraint on a PJM per-plant solve here is **free disk**, because the swapfile is sized
`int(min(deficit, free − 2 GiB))`.

**Screen bundle retrievable with ZERO re-solves** (17 files incl. `dispatch/2022_P1.parquet`):
`git checkout 786affd47cf95334aa1fc7579135c230492f1296 -- results/calibration/pjmh3_syncarm_2022`.
Promotion recommendation: **do not promote** — inert, and it costs memory on every future PJM
solve. The question is put explicitly to the owner in RESULT §11.5.

## pjm-h3b — 2026-09-13 — the PJM 2022 miss is the Elliott scarcity tail, not a stack defect

**ZERO LP.** Finding: `docs/FINDING-pjm-h3b-2022-miss-is-the-elliott-tail-2026-09-13.md`.
Keeper `2026-09-11-pjm-d4-4-gasoutage` UNCHANGED (CALIBRATED, 8/8, zero caveats).

**C3a-2022, C3b-2022 and the ledgered C3c-2022 caveat are ONE defect.** Of the $4.717/MWh annual
price gap (model 64.074 vs actual RT 68.792), **18 hours of 8,760 carry 84 %** (actual mean
**$2,071**, model **$144**) and **15 of those 18 are Winter Storm Elliott, 23–24 Dec 2022** (the
other 3 are 13 Jun 2022). The 92 hours above $200 contribute **120 %** of the gap; **the remaining
8,668 hours are OVER-priced at +1.5 %**, contributing **−20 %**. C3b is the same object: dropping
the top 18 actual hours cuts the price-duration error **73 %**, the top 92 cuts it **85 %**.

**DO-NOT-REDO — no 2022 PRICE lever.** (a) The adder route (`ordc_scarcity_overlay`) is `G` and the
2026-09-13 owner re-opening explicitly does not license it. (b) The reserve-scarcity route was
refuted by this lane's own screen the same day (pjm-h3, S2 1.22 % vs a 22.3× supply margin).
(c) Every body-directed lever is **counter-indicated**: the body is already +1.5 % over, so lifting
ordinary hours to chase the annual mean worsens 8,668 hours to chase 18 — and the authorized band
multiplier is year-invariant, so the same move pushes 2023–2025 (−3.6 / −5.1 / −9.3 %) further out
in the same direction.

**THE LIVE PJM OBJECT IS C1 VOLUME, NOT PRICE.** CC_REGULAR-2022 **+22.56 TWh** is a real separate
miss, and it is already scheduled to move to **+12.81 TWh** at the next registration when the merged
`gov-hydro-seam-1` PS→`OTHER` repair makes `reconcile_vintage_classes` fire in PJM 2021/2022
(pjm-h2 §3; zero determination flips). Re-measure the residual **after** that lands before
proposing anything.

## pjm-h10 — 2026-09-19 — the ENERGY IDENTITY reconciles; the 923↔930 "gap" does not exist; the live defect is the SEAM, and PJM's 2020 runs no measured seam at all

**Branch:** `claude/pjm-energy-identity-s4l8ow` · **Base:** `origin/main` @ `4583e70b`
**Finding:** `docs/FINDING-pjm-h10-the-energy-identity-2026-09-19.md`
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-pjm-h10-2026-09-19.md`
**Keeper UNCHANGED** (`2026-09-11-pjm-d4-4-gasoutage`) · **no run registered, no mechanism armed,
no matrix cell moved, no determination changed** · **ZERO LP minutes in this session** (rule 32
`[R-SHARD]` (a); two control replays were sharded).

**THE PREMISE IS REFUTED. There is no 60–75 TWh EIA-923↔EIA-930 gap for PJM.** The bridge closes to
**−6.43 … +9.29 TWh (−0.76 % … +1.10 %)** in every complete year. The quoted **739 TWh reproduces at
738.42** as EIA-923's PJM footprint **minus CHP minus wind+solar** — 66.93 TWh in 2020, 87.10 in
2024, which *is* the apparent gap. The premise's sign was also inverted (PJM exports, so the identity
is generation − net export ≈ demand). The three plant sets are near-identical: `ba_code == 'PJM'` vs
the model's 8 zones differ by 10.05 TWh in 2020 (retirees the current eGRID/860 vintage cannot place,
led by W H Zimmer 5.57; plus OVEC 9.03 the other way — its own BA inside PJM's footprint) and by
**exactly 0.00 in 2023**.

**THE LIVE DEFECT IS THE SEAM, AND IT IS NOT A CAP AND NOT THE NEIGHBOUR PRICE.** PJM's settlement
tie-line file and EIA-930 `Total interchange` agree to **≤0.19 TWh in 2020–2024**; the model is handed
that number and delivers **2.816 / 13.541 / 9.108 / 9.104 / 10.548 / 8.546 TWh less** (2020–2025).
The measured export envelope is **never binding — 0 hours at ≥95 % of the system cap in any year**,
median export 22–36 % of cap; and the whole hourly distribution is shifted down (2023 p50 4,477 →
3,393 MW, p95 8,542 → 6,489), which is a price signature, not a limit. The ladder-at-model-price vs
ladder-at-measured-DA gap is **2.583–7.841 TWh** — real, consistent with pjm-h3b's +1.5 % over-priced
body, but not the 9–13.5 to be explained. The defect splits into **TWO legs of comparable size**, and their
balance shifts across the span: taking `min(per-seam p90 cap, ladder @ model price)` as admissible
gross export against PJM's measured gross, the **gross-export shortfall** is 9.458/6.278/4.706/4.434/
3.888 TWh (2021-2025) and the **implied import-side excess** is 4.083/2.830/4.398/6.114/4.658 —
export-dominated in 2021/2022, **import**-dominated by 2024. The import leg is `spec.py`'s own named
failure mode ("phantom imports that displace CC_REGULAR"). **The import column is an INFERENCE, not a
measurement** (a residual of two quantities measured on different objects); the measured split needs
`hourly/network_<year>.parquet`, which the keeper bundle does not commit — one parquet, no re-solve
beyond the replays. A lever here must pick the leg, and the leg depends on the year.

**NEW: PJM's keeper 2020 runs NEITHER measured seam mechanism.** `PJM_SEAM_LADDER_BY_YEAR` covers
2019, 2021, 2022, 2023, 2024, 2025 — **2020 is absent** — and `firm_export_floor_by_year` covers only
2023–2025 (and is *displaced* by the ladder wherever it has data, so it is **inert in every keeper
year**). So 2020 falls through to the **forecast gas-elastic track**, which is the exact defect
pjm-160 fixed for 2022 and left behind when it extended to 2019/2021/2022. **This is a STALE INVARIANT, not a second oversight**: pjm-173 recorded that the ladder
"covers {2019, 2021, 2022, 2023, 2024, 2025} = EVERY year PJM solves", and that was TRUE when written
— the then-keeper `pjm_debugb_inputclock_A` (pjm-162) solved 2023–2025. **2020 entered PJM's solved
span with the `pjm_d4_4_TP` touchpoint and nothing re-checked the claim**, which is why a rule-19
inertness argument has to be re-verified whenever an ISO's year set grows. **Both 2020 source inputs
are on disk** (`PJM_2020_import_export_act_sch_interchange.csv`; the DA LMP parquet covers 2018–2025),
so filling it is a rule-23 `[R-FROZEN-DERIVE]` re-derivation with zero new parameters. **Stated
against interest (rule 1 `[R-STRUCT]`): it will probably make 2020 WORSE** — 2020 currently has the
*smallest* export shortfall precisely because the unmechanised track exports more. The case is
representation consistency, never the residual.

**EIA-930's OWN IDENTITY DOES NOT CLOSE FOR PJM in 2019/2020/2025.** `D + TI − NG` = **+9.85 / +8.56 /
−14.76 TWh** against ≤0.19 in 2021–2024. Consequences: **~9 of 2020's apparent +12.66 TWh "generation
overshoot" is EIA-930's, not the model's**; **EIA-930's 2025 `Total interchange` is the defective
series**, and against PJM's tie file 2025 *under*-exports by 8.55 TWh like every other year — the
charter's "+6.41 over-export" was an artifact of the wrong benchmark.

**Q5: the 2021 repair is SOUND, the 2020 repair is NOT.** Raw 2021 sums to 4,902.23 TWh with a worst
hour of 2,147,480,064 MW (int32 overflow); the screen flags 3 hours → **796.17 TWh**, peak 149,590 MW.
But **two 2020 hours survive** the 2.5×-median bar: 2020-07-28 **H13 at 192,229 MW** (2.26× median,
**20–30 % above every clean year's maximum in the very file the model reads** — the extract's clean
years top out at 147,605–160,560 MW; at 1 p.m. on a day whose own H17 reads lower; and failing the
extract's own identity by −56,665 MW) and 2020-07-29 H17 at 176,085 MW. The model serves both.

**Q4 per-class, on the EIA-923 basis** (EIA-930's `NG: SUN` is 0.2–1.0 TWh against 6–21 measured —
**unusable for PJM**, and the apparent "solar overshoot" reverses sign on the correct benchmark).
CC_REGULAR **+26.2 (2021) / +22.5 (2022)** but **+2.9 / +0.7 in 2023/2024 — a PRE-2023 phenomenon
only**; the registered C1 payload reads **+21.1** for 2022, and the predicted move to +12.81 from the
PS→`OTHER` repair **has not happened yet** (it is a LIVE hunk, so the shard replays are its test).
What is systematically UNDER every year, answering "something else must be under": **CT_CHP −2.2…−2.9
and ST_CHP −2.1…−2.4 (together −4.4…−5.0/yr)**, **`oil` = 0.000 TWh in every year** against 0.6–2.0
measured, **solar −2.9…−5.3**, and **COAL_PRB −2.7…−6.1 while COAL_BIT is over in 4 of 5** — a
within-coal merit-order misallocation invisible to C2, which scores the family.

**Q3 WAS ALREADY ADJUDICATED — by pjm-d4-3, not here** (`docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md`
§4, carried on the matrix cell `da_virtual_bids`; rule 28(a) DO-NOT-REDO). It measured `net @ actual DA`
on all six years — **+16.537 / +16.812 / +12.248 TWh** of net virtual demand in 2020–22 against
−0.755 / −1.620 / +0.204 in 2023–25 — and established that the layer's ≈0 admissibility anchor is a
property of **2023–2025, not of the construction**: in the holdout years there is no price at which
the curve nets to ~0. Cause is PJM's own book (gross INC 51.4 → 103.5 TWh 2021→2025, DEC/INC ratio
1.69 → 1.28, the off-peak *supply* side thinner pre-2023), and the disposition is the standing
pjm-159 architecture escalation. **This session adds only corroboration on the CURRENT keeper**, which
pjm-d4-3 could not use: net phantom demand +1.883 / +9.971 / +12.138 / −1.987 / −2.416 / +2.415 TWh
against its +2.414 / +10.525 / +13.013 / −1.338 / −1.713 / +2.870 — same sign in all six years, within
0.5–0.9 TWh, so **the d4-4 promotion did not move this object.** The only new content is the
cross-reference: the years of largest net phantom demand (2021, 2022) are exactly the years CC_REGULAR
is most over and the under-export is worst; pjm-d4-3's own channel gain already bounds that at
~7–12 TWh of the pre-2023 CC over-run, and no new attribution is asserted.

**TWO CORRECTIONS to the state handed in.** (a) The model's internal sink is **NOT** storage
round-trip loss: storage is **28–41 %** of it and **not monotone** (1.374/1.267/1.284/1.307/1.455/
1.427); the majority is the measured `pjm_zonal_loss_surface` (+2.037…+3.692). (b) The touchpoint's
**C2 is a PASS**, not a FAIL — the failures are C1/C3a/C3b with C3c ledgered.

**The model's energy identity closes EXACTLY**: `physical gen = demand + net export + storage loss +
zonal tx loss − virtual net − slack + dump`, residual **0.000000 TWh** in all six years. So total
generation is not free and cannot "overshoot"; only the terms can be wrong, and the wrong ones are
**net export** and **virtual net**.

**G-DRIFT (rule 29 `[R-SCREEN]` (b)): form 4 is FALSIFIED for PJM at this HEAD.** Unlike pjm-162's,
this keeper's `git_sha f09eddbe` **does resolve** (pjm-167's "unrecoverable" was the *previous*
keeper), so the audit is dischargeable. 81 files / 9,125 insertions / 264 deletions over 8 days; 56
files pure-add. **Four LIVE hunks**: the **rebuilt `pjm_offer_midcurve_condbinned.json`** (the
keeper's own live offer input — 3 → 6 delivery years, and quantified per rung: 2025 **0/48 rungs
move**, 2023 ≤0.05 on 10/48, 2024 ≤0.15 on 27/48 for the keeper's named LONG_RUN+CC_LIKE, while the
*pooled* table the pre-2023 years used to fall back to moves up to 4.35 $/MWh); the **SOCO-15 card-S12
COD-grain** change (`cod_ramp_enabled=True` + plant-level CAMPD bins → fractional online mask);
**`plant_taxonomy` PS→`OTHER`**; and the **MER dual** itself. Everything else classified INERT with
its gate checked against the keeper's recipe (`eia860_vintage_tracks_solve_year=False` kills SPP-38's
cache re-key; `campd_per_unit_attribution=False` kills `hour_grain`; PJM absent from every changed
ISO gate set; `ba_codes('PJM')==('PJM',)`; NWPP/SOCO registration; and NWPP-37's own census proves
**PJM carries no flagged `NG:` hour in any year**). `calibration_reference.json`: **319 PJM leaf keys,
0 changed.**

**Q6 GOVERNANCE, PROPOSED ONLY — nothing adopted, nothing re-scored.** A **total-energy** criterion
would be **vacuous** (the identity above closes to zero, so it cannot fail independently) — recommend
refusing it. An **interchange-volume** criterion has content, but **five of nine ISOs have no `import`
class** (ERCOT/NEISO/SPP/SOCO/NWPP apply interchange as an exogenous demand adder, so they
**auto-PASS**), so it could only ever fail the four carrying a *priced* seam — a rule-1 inversion that
penalises the more structural representation. Retroactive, scored zero-LP from committed sidecars:
worst-year |error| as % of served load is **CAISO 4.83 %** (−10.02 TWh, 2023), MISO 1.55 %, PJM
1.28 %, NYISO 0.33 %; at a 2 % threshold **exactly one determination flips (CAISO CALIBRATED →
NOT-YET)**, at 1 % two (CAISO and PJM). **Recommendation: reported-only now, alongside `co2` and
`diurnal_amplitude`; do not gate until every ISO's seam is priced and each ISO's interchange boundary
is named in the data contract.**

**Shards.** Two control replays of the committed bundles at the pinned SHA, for the marginal-emission
rate PJM owes the marginal-abatement page and as the empirical check on the G-DRIFT verdict. The
first pair (`session_01GVm2g4rPYhEHZT6kRmiB3S`, `session_01WiG8kSC7zZRG9R6xb85HJp`) **stalled — each
ended its turn before its solve completed**, and there is **no cross-session messaging route from a
CCR parent to a CCR shard** (`SendMessage` returns "no agent reachable"; the MCP surface exposes
`create_session` but no `send_message`), so they could not be nudged. **Operational lesson for rule 32
`[R-SHARD]` (c): a shard prompt cannot be steered after launch and must therefore state explicitly
that the turn may not end while the solve is running — a background job plus an in-turn poll loop.**
Relaunched as `session_01FKXs8PaaohGkVSsYJTp6gK` (branch `claude/pjm-h10-mer-a2`, 2023–2025) and
`session_01HSskC9q1YEKBMcv9RydYHr` (branch `claude/pjm-h10-mer-tp2`, 2020–2022) with that instruction
added. **A metrics difference in these replays is EXPECTED, not a regression** (the four LIVE hunks),
and neither may re-register or overwrite the keeper.

### pjm-h10 CODA — 2026-09-19 — the shard outcome: NO MER BUNDLE, an OOM finding, and a setup-chain defect

**Six shards across three generations produced no MER bundle.** All are archived (rule 33
`[R-SHARD-ARCHIVE]` (e)); none was left alive. Record:
`docs/ADDENDUM-pjm-h10-the-shard-setup-chain-2026-09-19.md` and the shard's own
`docs/FINDING-pjm-h10-shard-mer-tp-oom-2026-09-19.md` (rescued onto the lane branch from the
**immutable SHA `0bcb1a3c6265cdb253e5447b08288e4aa030bdf7`**, rule 33(d)).

**Generation 2's TP shard was a SUCCESS by the rule's own definition** — it cleared every setup
blocker itself, was **OOM-killed in the 2020 P0→P1 seam**, and pushed a finding instead of a bundle.
Its numbers: `oom-kill constraint=CONSTRAINT_MEMCG`, **anon-rss 13,949,260 kB = 13.30 GiB against a
13.36 GiB ceiling** — the identical figure rule 32(c)(8) records for miso-252/253 — after 2020 P0 had
completed (`Solve 574.607 s`, 382,243 simplex iterations). **THE RUNNER'S SWAP MITIGATION WAS INERT**:
a 5.0 GiB swapfile was active with `/proc/swaps` **Used = 0** at the kill, and preflight had already
printed *"ceiling+swap 18.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be
OOM-killed here"* — then ran anyway. Rule 32(c)(8) rests on the premise that provisioning a swapfile
is what makes a per-plant PJM/MISO year fit; **on this container it was not**, and the addendum puts
to the owner that preflight should REFUSE rather than warn. Ceilings also **vary between containers**
(13.36 GiB here, 24 GiB on another shard), so the value must be read, never assumed.

**THE MER ATTRIBUTION IS CONFOUNDED AND STAYS OPEN — do not cite this as evidence against the
emissions dual.** The dual cannot be toggled at this HEAD without a code edit the shard was forbidden
to make, and the container was flagged under-provisioned before the dual was reached. The OOM is
equally consistent with PJM per-plant simply not fitting a 13.36 GiB cgroup with or without it.

**A SETUP-CHAIN DEFECT, and part of it was this session's own prompt.** Rule 32 `[R-SHARD]` (c)(2)
documents ONE setup step (the `DATA PROFILE`). A PJM per-plant replay needs **six**: hydrate; install
deps (`uv sync --no-dev` is better than pip — `uv.lock`'s pins match the source bundle's recorded
environment exactly); the `transfer-interface-limits` clean partition (`pjm_measured_interface_limits`);
the `ramp-capability` clean partition (`measured_ramp_capability`); the `data/clean` tree generally;
and a re-fetch of the **licensing-gitignored** `pjm-da-virtuals` corpus that `pjm_da_virtual_bids=True`
reads and that is in no clone, ever. **Generation 2's prompt FORBADE `regenerate_clean.py`**, which
turned a setup step into two dead containers — my error, recorded as such. Measured here: the full
`regenerate_clean.py` is **~42 min / 1.6 GB / 57 of 58 datatypes**, so the TP shard's pattern is
better — let the runner hard-raise, read the datatype it names, curate that one.

**ANSWERED, and it closes an open question the addendum raised: DataMiner2 DOES still serve
`hrl_da_incs_decs` for 2020–2022** (36 files, 15 MB, 577 s with `--years 2020 2021 2022`). The PJM
holdout touchpoint's inputs ARE re-obtainable from a cold container. Also: `build_pjm_da_virtual_units`
has **no fallback and no year gate**, so the committed touchpoint's own container demonstrably held
those parquets.

**ONE prediction from the PRECOMMIT was CONFIRMED before the kill**: the 2020 build logged
`year table 2020`, i.e. 2020 now draws its **own** PJM midcurve offer table instead of the pooled
2023–2025 fallback — exactly the LIVE hunk the zero-LP G-DRIFT audit named. No scored number survived
to quantify it, so **G-DRIFT form 4 remains FALSIFIED-but-unquantified** and the control replay is
still owed.

**STILL OWED:** the marginal-emission-rate series for PJM, and the empirical check on the G-DRIFT
verdict. Cost to reproduce: one shard per span on a container whose **binding cgroup** exceeds
~13.36 GiB (or with usable swap charged to that cgroup), plus ~10 min of curate + fetch before any LP.

## pjm-h11 — 2026-09-19 — C-1 ARMED (2020 joins the seam ladder), G-DRIFT QUANTIFIED, and the offer-table rebuild is shown to push 2020/2021 the WRONG way

**Orchestrator session. ZERO LP MINUTES** (rule 32 `[R-SHARD]` (a)). Every number below is a
zero-LP phase 0: a frozen-formula re-derivation, an offer-array delta, a committed-sidecar
reconstruction and a code-level drift audit. Keeper UNCHANGED at write time
(`2026-09-11-pjm-d4-4-gasoutage`). **PRECOMMIT:** `docs/handoffs/PRECOMMIT-pjm-h11-2026-09-19.md`.

**C-1 ARMED: 2020 added to `PJM_SEAM_LADDER_BY_YEAR`** (`spec.py`, commit `3b719484`). Closes the
stale invariant pjm-h10 found — the table covered {2019, 2021–2025} and `firm_export_floor_by_year`
covers only 2023–2025 and is displaced where the ladder has data, so PJM's keeper year **2020 ran
NEITHER measured seam mechanism** and fell through to the forecast gas-elastic track. Rule 23
`[R-FROZEN-DERIVE]` re-derivation over sources that already cover 2020; **zero new parameters, zero
`ScenarioConfig` fields** (rules 21/24).

**Gates, declared ex ante.** G2 (monotonicity), G3 (no new field/scalar) and G4 — **added by this
session**, pjm-160's own published acceptance bar — all PASS: offline P9 volume error ≤ **0.04 TWh**,
duration RMSE **40–276 MW**, import-hour shares within 2–11 points.

**G1 as literally written FAILS, and the failure is PRE-EXISTING. It is reported, not rewritten.**
477 of 480 rungs reproduce exactly; three do not — 2023 Carolinas.import b2 (24.10 → 24.11), 2024
Carolinas.export b2 (13.75 → 13.76), 2025 LGEE.import b3 (40.64 → 40.65). The unrounded values sit
**0.07–0.28 cents from any rounding boundary**, so this is not a tie, not banker's rounding and not a
ULP; the script's own `round(p, 2)` gives `.11/.76/.65` and the registry holds the **truncations**.
Three hand-transcription truncations, made when the rows were written. **Decisive:** re-running with
the original `--years 2023 2024 2025` set — no 2020 anywhere in the frame — moves **the same three
cents**, and comparing the with-2020 against the without-2020 derivation rung-for-rung gives
**240 rungs compared, 0 moved**. So **G1's INTENT passes** and the arm adds the 2020 key only. The
three rungs are deliberately left untouched (fixing them would move three rungs inside the
CALIBRATED training keeper's own scored years with no data change to cite, rule 23) and go to the
owner as PRECOMMIT **Q1**.

**EX-ANTE PREDICTION, declared before any solve: C-1 makes 2020's export residual WORSE.** Measured
from the committed `pjm_d4_4_TP` sidecar by FINDING pjm-h10 §2.4's construction (method validated —
its `@measured DA` column reproduces **exactly** in all five years): the 2020 ladder's **gross**
export ceiling at the model's own price is **37.340 TWh**, **below** the **38.810 TWh net** the
forecast track delivers today, against **41.626** measured. Net ≤ gross, so 2020's shortfall widens
from −2.816 toward ~−4 TWh. Armed on rules 14 `[R-ACCURATE]` / 23 — a keeper year must run the
keeper's own mechanism, and 2020's small residual is the compensating estimate rule 14 describes —
and **never on the residual**; rule 1 `[R-STRUCT]` keeps it in if a gate moves the wrong way. The
root cause it points at: 2020's model-price→measured-DA gap is **13.441 TWh, the largest of any
year** (next 2021 at 7.82), the same defect as its CC_REGULAR **+7.5** / COAL_BIT **+16.9 TWh**
over-run. The ladder converts a hidden price error into a visible volume error.

**G-DRIFT (rule 29 `[R-SCREEN]` (b)) re-audited `f09eddbe → 995f7b7e` and QUANTIFIED** — the number
pjm-h10 owed. `git fetch origin f09eddbe…` resolves. **The increment since pjm-h10's audit base adds
NO new LIVE hunk**: `measured_coal_heat_rates` (NWPP-42) and `mid_vintage_exit_carry` (SPP-48) are
both default-off and **absent from both PJM keeper recipes**, with clean early-return gating; the new
`interchange/spec.py` registries are NWPP/SOCO and its two new `"PJM": {` blocks sit inside
**`MISO_SEAM_LADDER_BY_YEAR`** — another ISO's branch; `eia930/envelopes.py` is additive with no PJM
function body moved.

**The offer-midcurve rebuild is the big LIVE hunk, and scoping it changes the story.** The keeper
runs `pjm_offer_midcurve_segments = ['LONG_RUN', 'CC_LIKE']`, so **CT_FAST is out of scope** and its
−50 % move is inert — quoting it would have been wrong. Scoped to what the keeper actually reads:

* **Training keeper `pjm_d4_4_A` (2023–2025): essentially untouched** — mean drift ≤ +0.2 % on a
  multiplier of 7–12, **2025 byte-identical**. Its CALIBRATED 8/8 is not in question from this hunk.
* **Touchpoint `pjm_d4_4_TP` (2020–2022): materially changed**, every rung of 2021 included —
  LONG_RUN **−3.2 / −23.9 / −2.6 %** and CC_LIKE **−11.0 / −7.6 / +11.9 %** for 2020/2021/2022
  against the pooled fallback it actually used. **The direction is against this lane's target**: the
  2020/2021 multipliers move DOWN, making those units cheaper, so they dispatch MORE — in exactly
  the years C1 already fails with CC_REGULAR **+7.5 / +26.2 TWh OVER**. HEAD's rebuild is expected
  to push C1-2020/2021 **further over**.

So **form 4 stays FALSIFIED and a control at HEAD is EARNED — now with a number**, and an arm result
cannot be attributed without it.

**NEW, and it is a structural obstacle rather than a hunk: the MER dual is UNGATED.**
`model/lp/model.py::_marginal_emission_rate` is new at HEAD, has **no `ScenarioConfig` field
anywhere**, and `solve()` calls it on **every pass of every solve of every ISO**, running a second
HiGHS `run()` in the post-solve window — **the exact window the pjm-h10 PJM shard was OOM-killed
in**. The attribution stays genuinely confounded and **this is not evidence the dual caused that
kill**. What is now fact rather than inference: **no shard can avoid it without the code edit its
prompt forbids.** PRECOMMIT **Q3** puts the gating question to the owner.

**Also established:** `pjm_d4_4_A` and `pjm_d4_4_TP` carry **byte-identical `scenario_config` across
all 841 fields** — the PJM keeper is ONE config solved into two bundles, not a partitioned keeper, so
a single six-year replay reproduces the whole of it.

**C-2 (the gross/net seam split) cannot be closed in the parent**: `hourly/network_<year>.parquet`
is verified **absent** from both committed bundles' sidecar sets. It rides the shards.

**SHARDS:** two, each one `--years 2020 2021 2022 2023 2024 2025` invocation into one bundle
(rules 16 / 32(b) / 34(c); per-year fan-out banned) — CONTROL at `0fae26c3` (no 2020 key) and ARM at
`3b719484` (2020 key present). Differencing two immutable SHAs is what makes the arm a single delta
**without a new `ScenarioConfig` field**. Both prompts carry the memory gate first (STOP below
16 GiB, binding cgroup only), the full six-step setup with **nothing on a forbidden list**, the
in-turn poll loop, and the rule-34(a) `.gitignore`-negation + plain-`git add` bundle push.

## pjm-h11 (promotion) — 2026-09-20

**KEEPER PROMOTED: `2026-09-11-pjm-d4-4-gasoutage` → `2026-09-19-pjm-h11-c1seam-span`**
(+ folded touchpoint `2026-09-19-pjm-h11-c1seam-touchpoint`, 2020–2022, rule 30 `[R-TOUCHPOINT-FOLD]`
(a)). Owner ruling 2026-09-20, verbatim: *"Promote anyway"* — given after this lane declined to
self-promote and put the three-way "is it an improvement" table to the owner.

**Delta:** card **C-1** — the 2020 key added to
`src/market_sim/model/interchange/spec.py::PJM_SEAM_LADDER_BY_YEAR`. A rule 23 `[R-FROZEN-DERIVE]`
re-derivation of the already-armed measured seam ladder on one more year: **zero `ScenarioConfig`
fields, zero scalars, zero free parameters**, DOF ledger carried verbatim at 19 entries / 6 residual.
Until this run PJM's 2020 had no ladder row and fell through to the **forecast gas-elastic** seam
track while 2021–2025 ran the measured one — the stale-invariant defect pjm-h10 §2.6 recorded, now
closed. Basis is rule 14 `[R-ACCURATE]`, never the residual.

**Method — the first PJM keeper solved under rule 36 `[R-YEAR-ISOLATION]`.** Twelve solves (six ARM
years, six same-HEAD CONTROL years), **one year per shard container**, both cross-year warm-start
knobs off, **zero LP minutes in the parent** (rule 32(a)); composed at zero LP by
`scripts/probes/pjm_h11_compose_span.py`, which asserts the PJM keeper posture on every leg. All
twelve legs carry solve-surface fingerprint `905116f13849914f` at HEAD `3b719484`.

**Scored:** training half **CALIBRATED**, empty determination basis, zero caveats, all eight criteria
PASS (C1 18/18 all · 14/14 free). Touchpoint **NOT-YET**, exactly as the incumbent's touchpoint read;
rule 30(c) — a held-out year never downgrades the ISO.

**Scope proven through the solver:** arm-vs-control 2021–2025 `max |Δ class TWh| = 0.000000`, zero
classes moved. C-1 touches 2020 alone.

**Reported at full magnitude.** CC_REGULAR **+7.50 → +0.35 TWh**, total class |error| **48.2 → 47.05**.
COAL_BIT **+16.90 → +22.27 TWh — WORSE**, and **the cause is not C-1**: a CONTROL at the same HEAD
with no C-1 reads **+25.16**, so the rebuilt committed input
`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json` carries **+8.26 TWh** on its own and
C-1 recovers 2.89. That drift lands on PJM whenever it next re-solves, armed or not — **it is the
next lane's target**. C-1's own 2020 effect is likewise adverse and was **predicted in the PRECOMMIT
before the solve**: net export 40.391 → 28.344 TWh against 41.626 measured, fossil −10.574 TWh.

**C-2 measured, and it refutes a prior finding:** PJM's seam shortfall is **~100 % export-side**
(model gross import 0.000–0.048 TWh vs measured 0.000–0.603 across six years). pjm-h10 §2.5's
inferred import-side excess does not exist; the "phantom imports displace CC_REGULAR" suspect is
retired at the system boundary.

**Open, disclosed, untouched — owner question Q1:** 3 of 480 existing ladder rungs (2023
Carolinas.import b2, 2024 Carolinas.export b2, 2025 LGEE.import b3) sit one cent below the frozen
formula's output. Pre-existing hand-transcription truncations: they reproduce with no 2020 in the
frame, and the unrounded values sit 0.07–0.28 cents from any rounding boundary. **None of the 240
rungs shared with the scored years moves** when 2020 is added. Repairing them would be a
solve-affecting change with no data change to cite (rule 23), so they are left alone.

**Promotion hygiene (rule 35 `[R-PROMOTE]`).** Year union enumerated BEFORE the delete (35(b)): PJM
is {2020, 2021, 2022, 2023, 2024, 2025}; the incoming pair covers it exactly (35(c)). Order was
promote → `audit_keepers.py` (E1/M1 clean) → prune (35(e)). `prune_iso_runs.py --iso PJM
--force-uncite` removed the outgoing keeper's three stores and its touchpoint's —
`2026-09-11-pjm-d4-4-gasoutage` (`pjm_d4_4_A`) and `2026-09-11-pjm-holdout-gasoutage-touchpoint`
(`pjm_d4_4_TP`) — PJM only. `audit_keepers --iso PJM` finishes **0 failures / 0 warnings**.
Mechanism-matrix PJM shard re-stamped and the `reference_price_interface` cell updated (rule 28(b));
the cell **stays K** — what moved is its coverage, not its verdict.

**Pre-existing RED not this lane's and not touched:**
`check_registry_payload_parity.py` flags `results/calibration/caiso279_ablate_dswcouple_span` as a
tracked, unmapped bundle on `origin/main` — a CAISO-lane item; rule 35(a) scopes pruning per-ISO.
The twelve `pjm_h11_{arm,ctl}_<year>` legs also flag **locally only**: they are gitignored, so CI
(which checks out only what is committed) stays green — the rule 31 `[R-RETAIN]` clause corrected by
pjm-h8 on 2026-09-16.

**Docs:** `docs/RESULT-pjm-h11-c1-seam-ladder-2026-09-20.md`,
`docs/ADDENDUM-pjm-h11-the-2020-readout-2026-09-19.md`,
`docs/handoffs/PRECOMMIT-pjm-h11-2026-09-19.md`,
`docs/FINDING-pjm-h11-the-pjm-oom-is-a-disk-ordering-bug-2026-09-19.md`.

## pjm-h12 — 2026-09-20

**ZERO LP, ZERO SHARDS.** Card D-1 (root-cause the offer-midcurve rebuild) is answered entirely from
git and the keeper's committed sidecars — which is the outcome the charter predicted for the branch
it landed on. Keeper `2026-09-19-pjm-h11-c1seam-span` untouched; nothing registered, nothing pruned.
**Doc:** `docs/FINDING-pjm-h12-the-midcurve-rebuild-is-a-clean-rederivation-2026-09-20.md`.

**D-1a → branch (i): the rebuild is a LEGITIMATE, cited rule 23 `[R-FROZEN-DERIVE]` re-derivation,
and the table STAYS.** Verified three ways rather than taken from the commit message: (V1) the
artifact's own `_provenance` corroborates the corpus claim — `n_month_files_parsed` 36 → 72, 12-of-12
month coverage in each added year; (V2) **the derive script is blob-identical** at the old table's
commit, the rebuild commit and HEAD (`1e7ba58ab4bd1145d62c9041bec4fb8e280f11ea`), so *"the derive ran
unmodified"* is verified, not asserted; (V3) zero new `ScenarioConfig` fields, zero scalars. Rule 14
`[R-ACCURATE]` independently required it — the old table priced 2020/2021/2022 from `pooled`, a
capacity-weighted blend **of 2023–2025**, i.e. years that had not happened yet.

**So COAL_BIT's +8.26 TWh is a genuine response to a better input, and its mechanism is measured:**
the rebuild made PJM coal cheaper in exactly the three years that moved. LONG_RUN mean implied-HR
multiplier, own-year minus the `pooled` it replaces: **−0.298 / −1.993 / −0.164** (2020/2021/2022)
against **+0.000 / +0.002 / +0.000** (2023/2024/2025). 2021 is the event — the committed rung
s = 0.45 falls 8.025/7.725/7.825/7.775 → 6.125/5.425/5.325/5.525, ~30 % cheaper, ~$10/MWh at 2021
delivered gas. **2022 is not monotone with the others** (cheaper at the bottom of the curve, dearer
at the top); a successor modelling this as a uniform coal discount will mis-predict it.

**Training-year restatement: 129 of 432 cells, but 73 of them are `CT_FAST`, which the solve never
reads** (`pjm_offer_midcurve_segments = ['LONG_RUN','CC_LIKE']`). In the armed segments the largest
training-year move is 0.10 (LONG_RUN) / 0.15 (CC_LIKE), and LONG_RUN's means are ~0 — consistent with
the keeper passing C1 18/18 on the training years.

**Two h9c assertions that do not survive checking** (neither damages the keeper; both live for the
next lane). (a) *"a 2020-2022 mask never contributes to a 2023-2025 unit's median physics"* is FALSE
as written — `_unit_physics` medians over **every** parsed file, so segment membership is pooled
across years and the added years can re-segment a surviving key. The falsifier is **2025 = exactly 0
cells moved in all three segments** while 2023/2024 move; a disjoint-key story predicts zero
everywhere. (b) **The OLD table was stale against its own landed derive script** — it lacks
`conditioning`/`season_of_month`, which blob `1e7ba58a` emits unconditionally, and both landed in the
same commit. h9c was the first run of the landed script, so part of the 2023/2024 restatement is that
staleness being cured; the 129 cells are an **upper bound** on the data-addition effect, not a
measurement of it.

**D-1b → there is nothing to un-stack (rule 19 `[R-ONE-MECH]`).** From the keeper's committed
`legitimacy_diagnostics.json`, no re-solve: every mechanism forcing COAL, summed
(`coal_mustrun` + `reliability_floor` + `chp_steam`), is **4.538 / 4.679 / 1.440 TWh** =
**4.00 % / 4.14 % / 0.99 %** of class energy against a 30 % budget. D-4 does read `passed: false`,
but its failures are `st_netload_drag` (plant 3138) and `cc_mustrun_per_plant` × CC_REGULAR (2393,
7153) — **no coal mechanism appears in any D-4 failure row.** **PJM coal over-generates
economically, not by forcing**: removing every coal floor could not close a +16.90-to-+25.16 TWh
six-year C1 error. The target is the coal **offer level** / merit position against gas, and a new
floor here would be a mechanism aimed at a residual forcing does not produce — refused under rule 1
`[R-STRUCT]`.

**Latent reproducibility trap, found in passing and NOT fixed.** The committed surface depends on six
years of corpus, but `fetch_pjm_energy_offers.py` and `derive_pjm_offer_midcurve.py` **both** still
default to `--years 2023 2024 2025`. A bare run of the documented pipeline regenerates the old
three-year table and silently reverts the rule-14 repair, with no error and no script diff; the
corpus payload is gitignored (DataMiner2 redistribution restriction), so the defaults *are* the
contract. Left for the owner (Q4): the derive script is rule-23 frozen and the pair must move
together — fixing only the fetch default gives the worse state of a six-year corpus read three years
deep. The corpus README is corrected (documentation only, plus two stale `scripts/` → `scripts/data/`
paths).

**Card D-2 (export seam) not advanced.** `seam_neighbour_hourly_ladder` stays `O`; the charter bars
re-running that arm as-is and a successor must demonstrate the hourly claim the last one failed.
pjm-174 already holds the design: the defect is Q-Q **anchoring**, and quantile-mapping the model
price onto the measured DA marginal with hourly ranking untouched returns the measured volume exactly
(31.732 / 37.805 TWh) through the **unchanged** ladder. That is a PRECOMMIT-and-six-shards task, not
started here.

**Carried open, not silently resolved:** Q1 (three truncated ladder rungs), Q3 (the MER dual is
ungated), the proposed rule 32(c)(8) addendum. **Pre-existing RED not this lane's:**
`results/calibration/caiso279_ablate_dswcouple_span`.

### pjm-h12 card D-2 — the export seam gap is ONE defect, and the chartered successor is dead at zero LP

**Doc:** `docs/ADDENDUM-pjm-h12-the-seam-is-a-variance-compression-2026-09-20.md` · **Probe:**
`scripts/probes/pjm_h12_seam_qq_phase0.py`. Still ZERO LP, ZERO shards — every number is from the
keeper pair's committed `hourly/system_<year>.parquet` sidecars plus
`_validation-source/actual_lmp_hourly_PJM.parquet` and `eia-930-interchange/`.

**Both limbs of C-2 have ONE cause: the model's price distribution is VARIANCE-COMPRESSED against
measured DA.** Model ÷ measured at matched quantiles runs ~1.5 at p1 down to ~0.7 at p99, crossing
1.0 near the median, monotone in all six years — too high in the low tail (p10 ratio 1.18–1.40), too
low in the high tail (p99 0.63–0.89), median right (p50 0.998–1.187, which is why C3a passes). The
ladder's rungs ARE quantiles of measured DA, so clearing them against a compressed distribution
under-clears both ends at once. **That derives the sign of the export shortfall from first
principles** (PJM exports when cheap; the model's cheap hours aren't cheap enough), with no fitting.

**The import limb is UNREACHABLE, not under-modelled.** `qq_import` = `quantile(da, 1-exceed)`, so a
never-exceeded depth prices at the year's measured MAXIMUM. The model's hourly price reaches that
ceiling in **7 hours of 52,560 (0.013 %)** and in **2022/2023/2024/2025 never once**. That
mechanically explains pjm-h11's C-2 reading (model gross import 0.000–0.048 TWh vs measured
0.000–0.603).

**The re-anchoring repair is real and large on VOLUME.** Driving the derivation's own `offline_score`
law with three price series: span volume error **P9 +0.100 / ASIS +37.368 / ARM +0.060 TWh**,
duration RMSE **121.1 / 358.1 / 118.6**. Reproduces pjm-174's 2021/2022 numbers to the milli-TWh and
extends them to six years. *Scope limit stated: this is the derivation's offline law — the live LP
also applies per-border envelopes and its own price feedback, so +37.368 is direction and scale, not
the LP's seam error (pjm-h11 measured 9.0–12.3 TWh/yr live).*

**AND THE CHARTERED SUCCESSOR IS DEAD, killed at zero LP.** The charter required a successor to
"demonstrate the hourly claim". It cannot: **fed the exact price it was derived from, the ladder's
own hourly r is 0.052** — the ceiling is already zero. The ARM improves hourly r in 4 of 5 seams and
its mean (0.0547) even exceeds P9's (0.0522), but at an absolute 0.05 that is noise and is not
quoted as a win. Structural, not a tuning shortfall: `qq_*` match exceedance FREQUENCIES, so a step
ladder calibrated on duration statistics pins the flow DISTRIBUTION by construction and says nothing
about which hour gets which block. **This retrospectively explains why
`seam_neighbour_hourly_ladder`'s hourly claim was contradicted by its solve — it was never
achievable.**

**The signal is not in the input.** Measured hourly seam flow vs measured hourly PJM DA price: |r|
0.00–0.33 with **signs that flip between years and seams** (NYISO −0.3663 in 2020 → +0.2213 in 2022;
Carolinas +0.0324 in 2021 → −0.3321 in 2022). PJM's hourly interchange is not in reality a function
of PJM's own hourly price — it is the neighbour's price, bilateral schedules and transmission
outages. MISO is the one partial exception (0.15–0.31, sign-stable). **No re-anchoring, hourly ladder
or quantile map can recover a signal the input does not carry.**

**Cell `seam_neighbour_hourly_ladder` stays `O` and was NOT re-tested; no matrix cell edited** (rule
28(b) triggers on testing a mechanism — this is a diagnostic on committed artifacts, nothing wired
into a solve). No successor built, no shards launched: phase 0 killed an arm before an LP was spent,
which is what rule 29 `[R-SCREEN]` clause (0) survives as practice to do.

**New owner questions.** **Q5 — withdraw the hourly bar from this mechanism family?** It tests a
duration-curve device for hourly skill its input cannot carry, so keeping it guarantees every future
seam successor fails for a reason unrelated to its merit; the proposal is to judge seam anchoring on
volume + duration RMSE and route hourly interchange to a different input (neighbour price /
scheduled bilaterals) as its own card. **Q6 — build a quantile-indexed ladder?** The ARM series is a
DIAGNOSTIC and is **not** admissible as a mechanism (mapping onto the measured DA marginal at runtime
has no forward analogue → fails rule 13 `[R-MEASURED]`). The admissible form stores each rung's
QUANTILE and evaluates it against the model's own within-year distribution — no measured price level,
regenerates forward, removes the censoring automatically. That is a new `ScenarioConfig` field (rule
28(c): matrix row in the same PR) and a PRECOMMIT-plus-six-shards task, not started here because Q5
decides what it would be gated on.

### pjm-h12 card D-3 — the commitment-feasibility clip is REJECTED for PJM (cell U -> R)

**Doc:** `docs/RESULT-pjm-h12-d3-the-clip-is-not-the-rule17-repair-2026-09-20.md`. 12 solves across
6 shards (one year each, rule 36 `[R-YEAR-ISOLATION]`, ARM+CONTROL at pinned SHA `65ab6205`);
**ZERO LP in the parent** (rule 32(a)). **NOT PROMOTED** — keeper
`2026-09-19-pjm-h11-c1seam-span` untouched, nothing registered, nothing pruned.

**The arm fires and is not inert:** 65–66 of 69 floored plant-groups infeasible, 106.7k–114.3k
infeasible plant-hours, ~7–8.5 TWh of commitment floor released per year. **G1 PASS** every year,
**G2 PASS** (the 2025 leg reproduced its own offline census to **0.02 %**).

**It is refused because G6 — the gate written to test its own justification — FAILS (2024: 8 → 9).**
The charter called it "promotable on rule 17 `[R-FLOOR-WINDOW]` alone" because PJM's keeper D-4 fails
on `cc_mustrun_per_plant`. **The populations are DISJOINT.** In 2023 the D-4 `cc_mustrun_per_plant`
failure set is **byte-identical across legs** — 2393, 7153, 10308, 10751, 59220 — so the arm repairs
**none** of them, and fires instead on already-passing plants (3797, 56807). The clip tests
**feasibility** (available capacity < asserted commitment, an outage-derate question); D-4 tests
**conduct** (floored while the meter reads zero). Different plants. **That conflation was this
lane's own error in the PRECOMMIT**, and nothing measurable before the solve would have exposed it —
the census counted plant-hours, never *which* plants.

**The causal chain is refuted 0/6.** G4 (decile-1 price falls) fails in **every** year, same sign
(+0.0032 to +0.0416 $/MWh); G5 (net export rises) likewise. **G3 PASSES 6/6** (CC_REGULAR falls
0.1612–0.7731 TWh) but that is only **2–11 % of the released floor** — the LP re-dispatches the freed
capacity economically and COAL_BIT / CT_PEAKER / COAL_PRB absorb it (2024: +0.0744 / +0.0817 /
+0.0053 against CC −0.2868), so the trough gets **dearer**, not cheaper. G7 PASS in 2024 (all
mechanisms < 0.5 %); 2021 flagged `reliability_floor` +27.44 %, year-specific.

**Reported, not buried:** 2022 is a genuine counter-example — D-4 `cc_mustrun_per_plant` **6 → 4**.
The arm helps in one year of six; the bar is no increase in any year.

**By-product — the G-DRIFT LIVE hunk is ~nil.** `data/fuel/hubs.py::_basis_bridge_blackouts` was
classified LIVE in the PRECOMMIT (ungated, moves delivered citygate gas, the denominator of PJM's
offer surface), and that is what earned twelve control solves. Measured: the 2022 control reproduces
the committed keeper with **0 of 78,840 price cells moved**. The conservative call cost six extra
solves and bought certainty — stated plainly, **form 4 would have been valid**. A successor may treat
that hunk as INERT for PJM on this evidence.

**The underlying rule-17 defect is REAL and UNREPAIRED.** Plants 2393, 7153, 10308, 10751, 59220
still fail D-4 on `cc_mustrun_per_plant` in both legs in every year. The successor is a
**conduct**-based membership correction (`mustrun_plant_exclusions`, cell `U`), which first needs a
PJM lay-up census — `data/raw/_processed-legacy/campd_bridge_layup_exclusions_PJM.csv` does not
exist (only MISO and NYISO are built), so that is a data-intake step.

**Retention (rules 31/33/34):** all 12 bundles pushed to their shard branches with
`dispatch/<year>_P1.parquet`; every shard fetched, checked out and verified before archiving; all six
sessions archived; **branches left in place** (rule 33(f)(3) — a branch carrying a bundle a promotion
would register stays until the owner rules). `.gitignore` keeps them out of `main` and carries the
full-SHA recovery lines. **Nothing was `rm`'d.** Cell `mustrun_commitment_feasibility_clip` **U → R**
in PJM's matrix shard (rule 28(b)); rules 25/28(d) — PJM's cell only, SPP-42's identification
untouched.

## pjm-h13 — 2026-09-20 — the ST_GAS net-load drag is an ALLOCATION defect; the merit swap takes D-4 drag failures 12 → 5 and the determination holds at CALIBRATED

**Record:** `docs/RESULT-pjm-h13-the-drag-is-an-allocation-defect-2026-09-20.md`.
**Charter:** `docs/handoffs/PRECOMMIT-pjm-h13-2026-09-20.md` + `ADDENDUM-pjm-h13-presolve` +
`ADDENDUM2-pjm-h13-g2-disambiguation`, all pushed **before any arm result existed**.
**Method:** six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]`), ARM-ONLY at pinned SHA
`ed3f5efd`, **zero LP in the parent** (rule 32(a)); composed at zero LP by
`pjm_h11_compose_span.py` with `legitimacy_diagnostics.json` **regenerated over each composite**.

**NO CONTROL SOLVES — six solves, not twelve.** G-DRIFT over `65ab6205..HEAD` classified every hunk
INERT for PJM (`constants.py` NWPP rows only; `scenarios.py` **zero executable lines**; `hubs.py`
one hunk inside the `caiso_citygate_blackout_bridge` branch, flag absent on both PJM bundles), so
form 4 held. **pjm-h12's correction #1 was right** and it halved this lane's LP.

**The queued lever was adjudicated at ZERO LP and NOT taken.** The missing PJM lay-up census was
built from the **frozen** nyiso-140 criterion (separation textbook: 10 plants at 18/18 zero cells,
nearest non-qualifier at 14/18) and is committed. It selects 2393 Gilbert and 10751 Camden from the
keeper's D-4 failures and **independently declines** 7153, 10308 and 59220 (cyclers and a workhorse,
P(on) 0.39–0.59). But its footprint is **0.027 TWh over six years** — 24 % of the D-4 failure ROWS,
**0.6 % of the failing ENERGY**. Correct and sub-marginal; cell stays `U`, re-stamped with the
measurement, arming it later is a one-flag change. Measuring it is what localised the real mass.

**Delta:** `netload_drag_merit_allocation` (ercot-259) **False → True** on the keeper's own recipe
via `replay_keeper.py --set` — **zero code change, zero scalars, zero free parameters** (frozen
tranche capacities, the fleet's own bid heat rates), DOF ledger carried verbatim, rule 19 clean,
**forward-native**.

**The defect, from the incumbent keeper's own committed diagnostics, never a residual:** the
pro-rata drag floors **exactly four plants** of an 8.95 GW ST_GAS fleet; **3131 Shawville** and
**3138 New Castle** read a measured median of **exactly 0.000 MW** over their own binding hours,
while **3148 Martins Creek (1700 MW)** and **3149 Montour (1504 MW)** — the two largest, in no D-4
skip list — carry **no floor at all**. 0.92 GW floored dark, 3.2 GW unfloored: the error runs both
ways. This is the defect **pjm-177 recorded and did not take**.

**Measured, six years, composed vs composed.** D-4 `st_netload_drag` FAIL **12 → 5** with **no
increase in any year** (3→1, 2→2, 2→1, 1→0, 2→0, 2→1); `cc_mustrun_per_plant` **unchanged in all six
years** (33→33), so nothing is traded away. **In 24 of 24 per-plant-year rows the share of floored
hours whose meter reads zero FALLS**, and the median over those hours **rises in 19, never falls**.
Pre-solve mandate identical to **0.0000 TWh** every year, verified before the solve.

**Scored:** span 2023–2025 **CALIBRATED**, all eight criteria PASS, zero caveats, basis *"all
criteria pass, governance attested"*. Touchpoint 2020–2022 **NOT-YET**, criterion-for-criterion
identical to the incumbent's touchpoint. Max |Δ class TWh| 0.69–0.96/yr.

**Reported at full magnitude.** (a) **G5 FAILED AS WRITTEN** — `ct_netload_drag`'s D-2 share moves
+0.031…+0.082 against a 0.005 bar, because **one flag governs both limbs** (`floors.py:570` /
`:646`) and the gate scoped "other mechanism" by D-2 id rather than by FAMILY. A charter-scoping
error by this lane, **disclosed and deliberately NOT amended** after the numbers landed; outside the
drag family the largest move is **0.0007**. (b) T1 tripped — delivered forced energy rises (st
+12.0…+111.5 %, ct +21.9…+44.3 %); the mandate is unchanged, and **14 of 17 gaining plant-years PASS
D-4**. (c) **3138 New Castle is the named residual defect** — still FAILS 2020–2022 and gains floor,
the registered heat-rate-proxy weakness. (d) 3131 still fails 2021/2025; Martins Creek and Montour
stay unfloored. (e) The defect is **invisible to every gate** (ST_GAS immaterial, C8 skips it even
where the drag forces 30.8 % of the class), so the card is judgeable only on rules 17/1.
(f) **This lane's own ex-ante prediction about 3138 was WRONG**, in the mechanism's favour.

**METHOD NOTE a successor must not rediscover: per-year leg diagnostics are NOT comparable to a
composed span.** D-4's `ct_only` vintage guard borrows flags across **sibling years in the bundle**
— the control span's 2021 extended to 11 plants, a single-year leg to 8 — so 2393 and 7153 read as
phantom new `cc_mustrun` failures on the legs and vanish on the composite. Always compose and
regenerate the diagnostics over the composite before scoring anything.

**PROMOTION IS OPEN (rule 31 `[R-RETAIN]`).** Both composites are registered
(`2026-09-20-pjm-h13-meritalloc-span` / `-touchpoint`) and committed. This lane **recommends
promotion on the structural merits** with G5's failure disclosed; the keeper
`2026-09-19-pjm-h11-c1seam-span` **stands untouched** until the owner rules. PJM's year union
{2020…2025} is covered exactly by the incoming pair (rule 35(b)/(c)). Six shards archived after
fetch + checkout + verify (rule 33(a)); shard branches are transport and are cut when this PR
merges, so any leg not on `main` costs a re-solve, not a checkout.

## pjm-h18 — 2026-09-23 — Lever B LOCALISED at zero LP: two events on one compression, no level knob

**Zero LP, zero shards.** Keeper `2026-09-22-pjm-hydro2-ror-span` (the handoff's h16 keeper was
superseded by hydro-2 the same day). Record: `docs/FINDING-pjm-h18-price-object-localised-2026-09-23.md`.

- **Every year** runs too high in the bottom half of hours (+$2.6–4.8/MWh) and too low in the top
  5 %; 2023–2025 pass C3a by **cancellation**. The sign flip lives in the **CT/ST-marginal hours**
  (+0.27 in 2020 → −10.86 in 2022). CC-marginal hours are +16–20 % high in every year.
- **2022 = Winter Storm Elliott.** Dec 23–26 carries −5.6 of −8.0 $/MWh; without it 2022 reads C3a
  −3.5 %, C3b 0.114 (both PASS).
- **2020 carries an input glitch.** Two EIA-930 demand hours (192 GW, 176 GW) shed 28 / 13 GW at
  VOLL: +4.4 of the 18.6 C3a points and the **whole** C3b failure (0.208 → 0.152). A 2024
  dropout hour (56 GW) sits in the training span. `_screen_demand_spikes` (2.5× median) misses all.
- **Cards (owner picks, none launched):** A — demand-spike repair, zero DOF, rule 14 (expected: 2020
  C3b FAIL→PASS, C3a still FAIL); B — accept Elliott as a one-event miss (recommended); C — Lever C
  as the CC + CT **pair**, never one half alone.

## pjm-h16 — 2026-09-22

**PROMOTED.** `2026-09-20-pjm-h15-coalwindow-span` → **`2026-09-22-pjm-h16-coalgrain-span`**
on the owner's standing ruling (*"If structural integrity improves but gates regress that may still
be a keeper"*). The superseded pair was pruned in this session per rule 35 `[R-PROMOTE]` (a) —
`--keep` on the incoming touchpoint (pjm-h14 correction #1: the script does not honour a
`holdout.keeper` stamp), `--force-uncite` for the `keeper_history` citation — and
`audit_keepers --iso PJM` reads **0 failures, 0 warnings** after. Registered:
`2026-09-22-pjm-h16-coalgrain-span` (2023–2025, **CALIBRATED, 8/8 PASS, zero caveats, empty basis**)
+ `2026-09-22-pjm-h16-coalgrain-touchpoint` (2020–2022, NOT-YET), stamped to the span under rule
30(a). Sole config delta **`coal_sync_window_commitment_grain` False → True**, **zero free
parameters**, DOF ledger carried verbatim. **ZERO criterion flips in either span** — the touchpoint
carries the identical `fuelmix` / `price_mean` / `price_shape` FAILs and the identical ledgered
`price_tail` CAVEAT.

**The defect (rule 17 `[R-FLOOR-WINDOW]` + rule 18 `[R-PHYSICS]`, measured at zero LP on PJM's own
CAMPD record, never off a residual).** pjm-h15 repaired the window's VINTAGE and named PLACEMENT as
the half it could not reach. `arrays.py::_compose_min_gen_floors` places the coal synchronization
floor in `load_rank[:k]` — the top *k* **individual hours** by the window series — so the floor
carries the diurnal shape of LOAD, while a coal plant's synchronization is a whole-operating-day
decision. Over 29 covered plants × 6 years (173 plant-years, **152 reachable**): the plant's own
ONLINE hour-of-day peak-to-mean is **1.0001–1.3097** (median **1.0091**, ≤ 1.10 on 143 of 152) and
its overnight/afternoon on-share ratio **0.788–1.027** (median **0.9968**, inside [0.9, 1.1] on 145
of 152) — **when a PJM coal unit is synchronized it runs through the overnight trough** — against an
incumbent window whose own peak-to-mean is **1.0132–4.8608** (median 1.3011) and which is **MORE
PEAKED THAN THE PLANT ON 152 OF 152**. Rule 18: that window implies **3,963 / 4,354 / 4,689 / 5,517
/ 4,992 / 4,356 starts a year against the fleet's metered 238 / 290 / 303 / 302 / 302 / 334** —
13.0×–18.3×, with **253 implied starts on 1,299 MW plant 6264 in 2024 against 4 measured**. The
sharp test, actuals only: in the hours the incumbent HOLDS and a day window RELEASES the real plants
average 267.9 MW and are online 52.17 %, against **297.2 MW and 67.13 %** in the reverse set —
+29.4 MW and +15.0 points, in all six years.

**Gates: G1, G2, G5 PASS — G3 and G4 FAIL, and both are this lane's own bars, disclosed and NOT
amended.** G2 is exact and is the strongest statement: on a zero-LP `fleet_only` build in all six
years `pmax_mw` and `coal_sync_pmin_mw` move by **0.000e+00** and the ONLY mechanism id whose floor
array moves is `MECH_COAL_MUSTRUN`. G1 fires in all six years (+0.290 / +0.032 / +0.050 / +0.424 /
+0.337 / +0.130 TWh) but **monotone positive**, a weaker not-a-level-channel statement than
pjm-h15's both-directions result — that claim rests here on the HOURS evidence (asserted coal
floor-hours move 0.000 / +0.018 / +0.033 / −0.025 / −0.046 / +0.019 %, rounding UP in 70 and DOWN in
73 of 152 plant-years), not on the solver. **G3 fails on 2020 alone at 2.05× against a 2.0× bar**
(2021–2025 read 1.68 / 1.74 / 1.66 / 1.69 / 1.54× against a control of 16.87 / 14.88 / 14.28 / 16.47
/ 14.99 / 12.48×). **G4 fails on both limbs**: the chartered reachable set {1384/2023, 7213/2023}
moves 0.3154 → 0.3105 TWh (**−1.6 %**, not the halving the bar demanded) and neither clears — 1384
improved its zero-share 0.5507 → 0.5006 without crossing 0.5 — and six-year conduct-FAIL energy goes
0.3165 → 0.3192. **The card does not close the rule-17 defect it was aimed at.**

**THE HEAD-DRIFT MEASUREMENT — six control years came back EXACTLY ZERO, and that is a deliverable.**
The charter spent six same-HEAD CONTROL years although G-DRIFT classified every hunk INERT, because
the byte evidence behind the two PERF-C hunks is **cross-ISO** (a byte gate on the NEISO keeper, not
PJM) and because pjm-h15's G2 failed on a dispatch-less control regeneration. Measured at the cell
level over `6de36475 → c25d7e50`: **max |ΔMW| = 0.000000e+00, 0 of 166,440 class-hour cells moved,
in all five years solved on both sides.** G-DRIFT form 4 now rests on a PJM measurement rather than a
NEISO inference, and the dispatch-backed control **retires pjm-h15's G2 failure as the instrument
defect that lane disclosed it to be** (arm and control agree to four decimals on every non-coal
mechanism in 2020–2022 too: `chp_steam` 0.0166 / 0.0349 / 0.0360 both sides).

**Reported at full magnitude, declared reported-only ex ante:** C1 COAL_BIT rises **+0.019 to
+0.036 TWh** and CC_REGULAR falls **−0.015 to −0.042 TWh** in every year — the direction the charter
PREDICTED BEFORE THE SOLVE, at **~10× smaller magnitude than it predicted**, and three orders of
magnitude inside the standing +25.7 (2020) / +19.6 (2021) TWh error, so no criterion band can move.
The dispatch response is **~20× smaller than the asserted-floor footprint** (+1.04 to +2.82 %) —
the arm moves a FLOOR, not a cheap BAND. **Against it:** plant **7213/2022**'s floored exposure grows
**10×** (0.0008 → 0.0082 TWh, 30 → 184 binding hours) while its zero-share improves 0.900 → 0.663.

**Rule 19 `[R-ONE-MECH]`:** its OWN gate, not a widening of `mustrun_window_commitment_grain` —
widening the shared field would have moved SPP's designated keeper, which arms it and has coal, with
no SPP lane measuring anything. SPP-71's `coal_sync_ensemble_level`, a THIRD placement rule for the
same floor merged after this charter was pushed, is mutually exclusive by construction and absent
from the pinned SHA.

**Traps recorded:** all three pjm-h15 composition corrections reproduced (`--rebuild-benchmark` is
what materialises `results/calibration/_shared/PJM/`; a composed bundle inherits no attestation; a
shard bundle is not self-contained). **New:** two concurrent `legitimacy_diagnostics.py` runs on one
bundle will race on `--json-out`; and a `fleet_only` A/B probe running beside two diagnostics jobs
will OOM this container (cgroup ceiling **14.35 GB** — read the nested cgroup, never `free`).

Record: `docs/RESULT-pjm-h16-2026-09-22.md`, charter
`docs/handoffs/PRECOMMIT-pjm-h16-2026-09-22.md`.

## pjm-h15 — 2026-09-21

**PROMOTED.** `2026-09-20-pjm-h14-coalmustrun-span` → **`2026-09-20-pjm-h15-coalwindow-span`**
on the owner's ruling 2026-09-21 (*"If structural integrity improves but gates regress that may
still be a keeper"*). The superseded pair was pruned in this session per rule 35 `[R-PROMOTE]`
(a) — `--keep` on the incoming touchpoint, `--force-uncite` for the `keeper_history` citation —
and `audit_keepers --iso PJM` reads **0 failures, 0 warnings** after. Registered:
`2026-09-20-pjm-h15-coalwindow-span` (2023–2025, **CALIBRATED, 8/8 PASS, zero caveats**) +
`2026-09-20-pjm-h15-coalwindow-touchpoint` (2020–2022, NOT-YET), stamped to the span under rule 30(a).
Sole config delta **`coal_sync_online_frac_per_year` False → True**, **zero free parameters**, DOF
ledger carried verbatim at 19/6. **ZERO criterion flips in either span** — the same four C1 rows, the
same two C3a years, the same two C3b years, the same ledgered C3c.

**The defect (rule 17 `[R-FLOOR-WINDOW]` + rule 14 `[R-ACCURATE]`, measured at zero LP, never off a
residual).** pjm-h14 repaired the UNCOVERED coal cohort; the COVERED 29 plants still carried ONE
pooled `online_frac` — derived on **2023–2025**, re-established by re-running that window through the
FROZEN deriver and reproducing the committed column on **168 of 168 rows, 0 mismatched** — applied as
EVERY solve year's commitment window. Plant **50888 is floored across 68.4 % of 2020 by a fraction
measured three years later, in a year whose own meter says it synchronized in 1.3 % of the hours**;
3118 reads pooled 0.520 vs own-year 0.951 (2020), 3136 0.413 vs 0.944 (2021), 7213 Clover 0.314 vs
0.102 (2023). Rule 23 is NOT engaged: `thermal_tranches_PJM.csv` is not regenerated and xiso-5's
refusal stands.

**Gates: G1, G3, G5 PASS — G2 and G4 FAIL, and both failures are this lane's, disclosed and NOT
amended.** G5 is exact and is the strongest statement here: on a zero-LP `fleet_only` build in all six
years, `pmax_mw` and `coal_sync_pmin_mw` move by **0.000e+00** and the ONLY mechanism id whose floor
array moves is `MECH_COAL_MUSTRUN`. G3 cuts the one reachable conduct failure (7213/2023) **0.3656 →
0.1123 TWh (−69 %)** and total conduct-FAIL energy **0.5574 → 0.3165**. G2's breaches are all in
2020–2022 and none in 2023–2025 (where arm and control agree to four decimals); the 2020–2022 control
is this lane's own regeneration over a bundle with **no `dispatch/`**, reading `chp_steam × CT_CHP` at
0.0145–0.0290 against a committed family of 0.19–0.38 — **the control is the broken side**. G4 adds one
row, 7213/2022, 0.0008 TWh over 30 binding hours, on which the arm actually CUT floored energy 80 %.

**THE GENERALIZABLE LESSON, extending pjm-h14 correction #6:** a bar on another mechanism's D-2 forced
energy is a **displacement** test, not a **stacking** test — in absolute TWh just as much as in share.
Only the floor-ARRAY comparison separates them. A successor should gate scope on the array.

**Reported at full magnitude, declared reported-only ex ante:** C1 COAL_BIT worsens in five of six
years (2020 +25.422 → +25.704, 2021 +19.486 → +19.615) and **improves in 2023** (+0.650 → +0.527),
while CC_REGULAR improves in five of six. The adverse direction in 2020–2022 was **predicted in the
charter before the solve** and is rule 14's own diagnosis — the pooled window was silently
compensating. The dispatch response is **~20× smaller** than the asserted-floor footprint: the arm
moves a FLOOR, not a cheap BAND.

**Traps recorded:** a composed bundle inherits its FIRST LEG's single-year `shared_inputs`
(registration dies in `build_payload`) — `--rebuild-benchmark` after composition is mandatory; a
composed bundle does not inherit `calibration_attestation.json` either, so C6 reads UNATTESTED; a
shard bundle is not self-contained (`_shared/<ISO>/` is untracked for PJM); and **19 `cache_key` pin
tests already fail at `origin/main`**, failure set byte-identical with and without this change.

Record: `docs/RESULT-pjm-h15-2026-09-21.md`, charter
`docs/handoffs/PRECOMMIT-pjm-h15-2026-09-20.md`.

## pjm-h14 — 2026-09-20

**PROMOTED.** `2026-09-20-pjm-h13-meritalloc-span` → **`2026-09-20-pjm-h14-coalmustrun-span`**
(2023–2025, CALIBRATED, 8/8 PASS, zero caveats) + folded touchpoint
`2026-09-20-pjm-h14-coalmustrun-touchpoint` (2020–2022, NOT-YET). Owner's standing rule: *"If
structural integrity improves but gates regress that may still be a keeper."*

Sole config delta **`coal_mustrun_requires_measured_row` False → True**, **zero free parameters** —
the arm *withdraws* an assertion with no measurement behind it rather than asserting a level.
**Zero criterion flips** in either span, re-scored at HEAD. `audit_keepers --iso PJM` 0/0.

**The defect (rule 17 + rule 14, measured at zero LP, never off a residual).** A coal plant absent
from the CAMPD thermal-tranche artifact falls through **two unmeasured defaults that compound**: a
45 %-of-nameplate must-run tranche from a constant whose own comment calls its population
*"rarely-online units with no reliable observed floor"*, and a **force-all (1.0)** synchronization
window because the online%-scaled rule-17 window also defaults to 1.0 with no measured share. The
plants with the least evidence carried the strongest and widest floor. PJM 2020: **36 uncovered coal
plants / 15,774.7 MW asserting 58.04 TWh of must-run against 22.97 TWh of TOTAL metered output**;
Bruce Mansfield 2,490 MW asserting **9.82 TWh against 0.00 metered**. Not closeable by re-deriving —
the artifact's window is 2023–2025 (byte-equal key set on a frozen re-run) over a **year-blind**
EIA-860 fleet, so six per-year re-derives gained **zero rows**.

**Second deliverable, diagnostic-only:** `(MECH_COAL_MUSTRUN, None): (0, 24)` in `D4_WINDOWS` — the
coal synchronization floor carried **no D-4 entry in any ISO** and was the one commitment floor the
rule-17 diagnostic could not see. It exposed 5 genuine conduct failures on **covered** plants
(1040, 7213 ×3, 1384) that were invisible before.

**Gates:** G1/G2/G4 PASS — G2 **exactly** (zero uncovered plants floored on the arm, all six years).
**G3 and G5 FAIL, and both are this lane's scoping errors, disclosed and NOT amended**: G3's five
residual failures are all on covered plants the arm does not touch; G5's 2020 breach (0.0092 vs
0.005) is ~70 % a denominator move.

**Reported at full magnitude, declared reported-only ex ante:** C1 COAL_BIT improves every year
(2020 +28.128 → +25.422, 2023 +2.090 → +0.650) and **CC_REGULAR gets worse every year**
(2020 +0.265 → +2.634). The pre-solve footprint over-predicted the dispatch response **~10×** — the
arm removes a floor, not a cheap band.

**Traps recorded:** `prune_iso_runs.py` does **not** honor a `holdout.keeper` stamp (pass `--keep`,
or a promotion deletes its own touchpoint); `_slug` caps run ids at 4 words, so two labels sharing a
prefix silently overwrite each other.

Record: `docs/RESULT-pjm-h14-2026-09-20.md`, charter
`docs/handoffs/PRECOMMIT-pjm-h14-2026-09-20.md`.

## hydro-2 — 2026-09-22/23 — `hydro_ror_split` PROMOTED

Keeper `2026-09-22-pjm-h16-coalgrain-span` → **`2026-09-22-pjm-hydro2-ror-span`** (+ touchpoint
`2026-09-22-pjm-hydro2-ror-touchpoint`, 2020–2022). Sole delta `hydro_ror_split=true`: PJM's 57
run-of-river-class hydro plants run flat at their EIA-923 monthly budget. Hours at 0 MW hydro
1,010–1,965 → 0 in all six years; annual hydro energy unchanged to four decimals; zero criterion
status changes in either span (span CALIBRATED 8/8, touchpoint NOT-YET on the pre-existing C1/C3a/C3b
FAILs). G1 MW limb fails on a nameplate-sized bar (disclosed, not amended). Six per-year shards at
`152c546a`; 2023's former blocker (gitignored `pjm-da-virtuals` corpus) closed by per-shard re-fetch
with `pjm_da_virtual_bids` left true. Owner ruling 2026-09-23: "Promote it". Record:
`docs/RESULT-hydro-2-pjm-2026-09-22.md`.
