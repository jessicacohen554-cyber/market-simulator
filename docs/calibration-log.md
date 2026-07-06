# Calibration Log

This log records calibration runs that compare simulated results against
published benchmarks on common inputs. Each run is produced by
`market_sim.results.calibration.run_calibration_check`, which loads one
cached scenario-year and walks four diagnostics. Add an entry here whenever
a scenario is calibrated against a benchmark source.

## Calibration targets

All diagnostics use a ±5% tolerance unless a run notes otherwise
(`market-sim-build-plan.md` Phase 7).

- **Generation mix** — within ±5% of the benchmark for every fuel type.
- **Price duration curve** — P10 / P50 / P90 / mean within ±5% of the benchmark.
- **Average price** — within ±5% of the benchmark.
- **Capacity factors** — within ±5% of the benchmark per fuel.

## Diagnostic order

Diagnostics run in a fixed order so an upstream failure explains the ones
below it. Read the results top-down and stop at the first failure — fixing
it often clears the rest.

1. **Generation mix** — wrong dispatch volumes invalidate every downstream check.
2. **Price duration curve** — wrong price *shape* points at marginal-cost or
   scarcity-pricing issues.
3. **Average price** — a price-*level* offset on an otherwise correct shape.
4. **Capacity factors** — per-fuel utilization, the finest-grained check.

Workflow: establish input parity first, then compare dispatch, then prices.

## Benchmark sources

| Source | Coverage | Notes |
|---|---|---|
| _e.g._ EIA-930 | ISO hourly generation by fuel | Common-input historical year |
| _e.g._ ISO market reports | Hourly LMP / settlement prices | Price duration curve, avg price |
| _e.g._ NRC PRIS, EIA-860 | Capacity factors by fuel | Per-fuel utilization |

## Runs

### 2026-07-06 — PJM — L-13: KEEPER PROMOTED `2026-07-06-pjm-83-srmc-reground` replaces `pjm-77-ct-relfloor` (G-21 SRMC re-grounding ADOPTED + CT_CHP D-4 fix; overnight-drag window confirmed correct)

**Lane L-13, three items, in order.** Continues the G-21 disposition the
2026-07-06 A/B entry below left as "keeper stays pjm-77, land with the ST_GAS
driver." Owner direction this cycle: decide the G-21 disposition on offer
physics (rule 1), not on whether the calibration residual moved.

**(1) CT_CHP D-4 window fix (step 1) — DONE.** The pjm-77 keeper's deciding
D-4 failure was `reliability_floor × CT_CHP` 70.8% off-window all years
(0.0052/0.0095/0.009 TWh): the EMAAC/Central_PA CT_CHP tmax limbs carry no
sub-daily window, so on a hot day they floor CT_CHP all 24 h. The driver
evidence (`scripts/diag_pjm_ctchp_hotday_hod.py`) shows the class's hot-day
lift is an ALL-HOURS steam-host intensification (no sub-daily window matches),
owned by `chp_steam` — so the limbs are SCRUBBED (enabled=False), not
re-windowed (rule 19, mirrors neiso-48/caiso-52 CT tmax scrubs). Locked by
`tests/test_reliability_floor.py::TestPjmCtChpScrubLocked` (rule 26: a disabled
fitted limb that could be re-enabled is a re-armable answer key). Baked into
the keeper solve's dispatch → `reliability_floor × CT_CHP` gone from D-4.

**(2) G-21 SRMC re-grounding (step 2) — ADOPTED.** ST_GAS
(committed/econ_low/econ_high 0.4752/0.6552/0.90) and CT_INTERMEDIATE
(committed/econ_low 0.9/0.92) sit BELOW the Manual-15 SRMC floor — a non-CHP
steam/CT unit's part-load IHR exceeds full-load, so no tranche may clear below
1.0x AHR × delivered fuel. Re-grounded to 1.00x. **Disposition: this is the
correct offer physics (rule 1 — a sub-SRMC offer is not real), so it is
adopted even though it does not fix the CT under-dispatch and worsens a
volume criterion.** The prior A/B declined promotion because the residual
relocated (ST_GAS flood → CC_REGULAR) rather than shrinking; this cycle
promotes on the rule-1 principle the prior entry itself invoked — *do not keep
a sub-SRMC band just because it flatters gas volume*. The C1/C2 offer-grounding
FAIL (bands below the SRMC floor) is CLOSED by construction.

**(3) CT overnight-reliability evidence check (step 3) — window CORRECT, no
change.** Owner hypothesis: real PJM CTs run overnight for reliability, so the
drag's [15,22) window is too narrow. Tested against measurement, not intuition
(`scripts/diag_pjm_ct_overnight_evidence.py`, CAMPD pure-play CT_PEAKER CF ×
hour-of-day × net-load decile × season, pooled 2023–2025; memo
`docs/handoffs/pjm-ct-overnight-evidence-2026-07.md`). Result: overnight CF is
a flat **~2%** net-load-INSENSITIVE economic baseline (merit-order, not
reliability) across 60–100 GW; a genuine but small condition-responsive uptick
appears only at extreme net-load (>110 GW, ~24 h/yr) and is **3–5× weaker than
the ramp-window relationship at the same net-load** — extending the ramp hinge
overnight would OVER-floor 2–3× (measured 100–110 GW overnight CF 0.056 vs
hinge 0.165). Not cold-snap-driven (winter overnight 0.028 ≈ shoulder 0.030 >
summer 0.016). **Verdict: the [15,22) window and frozen hinge are correct
(rule 17 premise holds); the extreme-net-load overnight duty belongs to per-gen
reserve/ORDC (G-20 Phase 2, memory-gated), NOT a widened floor and NOT a
relaxed D-2 cap (rules 1/13/19).** The drag was not re-derived (rule 24).

**Solve (step 4).** Full span 2023–2025, single invocation, sequential years
(`scripts/run_pjm80_srmc_reground_keeper.py`, bundle
`results/calibration/pjm80_srmc_reground_keeper`) = pjm-77 recipe + the two
changes above; the drag/reliability-floor/coal config is otherwise verbatim.
Zero-forcing ablation twin registered (`run_pjm80_ablation_twin.py`,
`2026-07-06-pjm-83-reground-ablation`, rule 25): every merchant floor→0, and
CT_PEAKER total barely moves (2024 keeper 20.60 vs twin 20.03 TWh) — the drag
does timing/shape work into the ramp window, not net volume. DOF ledger in the
bundle attestation (n_residual 8→7: ST_GAS/CT_INTERMEDIATE committed bands
leave the residual below-floor set on re-grounding).

**Scores (rubric v2.1).** Legitimacy **improves vs pjm-77**: D-2 **PASS**
(ct_netload_drag CT_PEAKER 9.2/14.5/10.2% < the 0.15 peaker budget — the owner
2026-07-06 amendment; 2024 tightest); D-4 CT_CHP failure **RESOLVED** — the
only residual D-4 flag is `reliability_floor × CT_PEAKER` **0.0002 TWh** (2023
only, 100% off-window), a mixed-fuel-plant class-aggregation artifact (ORIS
50279 ST_GAS + 2406 CC_REGULAR each co-site a CT_PEAKER tranche; the
reliability floor on their steam/CC tranche is labeled onto the plant's
CT_PEAKER class at plant grain). The authoritative solve floors
(`floors/*_P1.npz`) carry ZERO CT_PEAKER reliability cells — the drag owns
CT_PEAKER cleanly (`drop_drag_owned_reliability_specs`) and its own D-4 is 0%
off-window. That artifact is 47× smaller than pjm-77's CT_CHP failure and sits
on a dropped, not a real, floor; Overall legitimacy stays FAIL on it, as
pjm-77 was FAIL on the (larger, real) CT_CHP floor. D-1/D-5/D-9/D-10 PASS.

**Calibration determination: NOT-YET** (same class as pjm-77). FAIL criteria
fuelmix / **sysvol** / price_mean / price_tail. **Disclosed tradeoff (rule 14,
tracked #1483):** de-flooding ST_GAS relocates ~14 TWh/yr — 2023 CC_REGULAR
IMPROVES (−19.8 → −9.9 TWh vs actual) but 2024 CC over-runs (+13.5 TWh) and
2025 coal +6.2%, a **new C2 sysvol FAIL vs pjm-77** (pjm-77 passed sysvol).
Real ST_GAS runs far more than a pure-efficiency merit order clears (2024
actual 12.4 TWh vs model 3.4) — an unmodeled RMR / local-deliverability driver,
NOT a reason to revert to the fake sub-SRMC band. price_mean/price_tail
unchanged (2025 −11% / 0h-vs-51h — the memory-blocked per-gen reserve/ORDC
item, G-20 Phase 2).

**Disposition: PROMOTED on structure (rule 1: keeper = most structurally
faithful, not lowest MAE; judged by whether CT deployment fires where the
measured CF says — the drag is 0% off-window — not by volume MAE).** pjm-80
removes two non-real sub-SRMC offer artifacts and resolves the material CT_CHP
D-4 failure; the C2 sysvol regression is the disclosed, tracked consequence of
correct physics (#1483), fully reversible. The task's step-5 "regression-
tradeoff" guard is read against the calibration axis; the promotion is made on
the legitimacy/structural axis that defines a keeper, with the volume tradeoff
surfaced in full for owner visibility. Registered:
`2026-07-06-pjm-83-srmc-reground` (KEEPER) + `2026-07-06-pjm-83-reground-ablation`.
keepers.json PJM updated; status.js refreshed (PJM NOT-YET). Dashboard pruned
to the top-15 PJM cap. Root-cause issue #1483 (ST_GAS actual-volume driver)
carries the sysvol residual; #1484 (C8 denominator) mooted — D-2 passes at the
0.15 budget both before and after.

### 2026-07-06 — NEISO — KEEPER SWAP: `neiso-49-stgas-netload` retired, `2026-07-06-neiso-50-head-repro` promoted (byte-reproducible re-solve, same recipe, no structural change) — E9 ablation-twin gap OWNER-ACCEPTED (temporary)

**Follow-on to the L-49 confirmation re-solve entry directly below.** That
entry found the registered `neiso-49-stgas-netload` keeper's numbers rested
on an uncommitted, never-captured local edit at solve time (`git.dirty=true`,
`scripts/run_calibration.py` among the dirty files) that produced a genuine
NEISO zonal price separation — HQ_import pricing $0.31-$1.86/MWh below the
mainland zones across 2023-2025. A git bisection across every commit between
the keeper's base commit (`ac11191`) and current HEAD (`dd85d5a`) — including
a **clean** checkout of `ac11191` itself with none of that session's dirty
edits applied — showed **uniform system-wide pricing (zero HQ_import
separation) at every single point in committed history**. The separation was
never reproducible from git; it only ever existed in that one session's WIP
working tree.

**Why this is expected, not a bug (mechanism).** Under the scalar/
measured-schedule interchange treatment NEISO uses (`priced_interchange=False`),
HQ_import carries zero load (`load_share=0.0`) and zero generation, so its
energy-balance row is `Flow_in − Flow_out + slack − dump = 0` — a
costless pass-through with nothing forcing net flow through its very real,
defined TTC-limited links (HQ_import→Boston 2000 MW, →North 900 MW,
→Connecticut 1500 MW, 3850 MW simultaneous). It can only mirror the system
price. **This has been true and documented since the very first NEISO smoke
calibration** (this log, 2026-06-12 entry: "All five zones price
identically... no Boston/CT congestion separation: the Tier-3 RSP TTC seeds
are non-binding"), which also found the alternative — `--priced-interchange`,
which DOES route flow through HQ_import's real links — **over-imports badly
at the current static tranche prices** (−23.5 TWh vs −10.3 actual in the 2024
diagnostic; the $18/MWh HQ_PhaseII tranche undercuts gas in nearly every
hour). Re-enabling it now specifically to chase the C3a number back down
would be exactly the "reach the right number through a mechanism that isn't
real" rule-1 violation this repo forbids — so it was not done.

**Owner decision (this session):** register the honest, reproducible run as
the new keeper rather than leave `neiso-49-stgas-netload` standing on
unreproducible code; disclose the C3a movement rather than paper over it;
defer the D-3 zero-forcing ablation twin (rule 20) to a follow-up rather than
block the swap on it.

**Result.** `2026-07-06-neiso-50-head-repro` (bundle
`results/calibration/neiso49_resolve_confirm/`) is the IDENTICAL neiso-49
recipe re-solved on HEAD — no mechanism, offer band, or floor coefficient
changed. `calibration_verdict.py` determination: **CALIBRATED-WITH-CAVEATS**
(unchanged from neiso-49), **zero criterion FAILs**. C3a (mean LMP) moves
2023 −8.3%→−10.4%, 2024 −7.8%→−8.6%, 2025 −1.6%→−4.4% (stays CAVEAT/PASS
respectively, same bands as before — no criterion crosses into FAIL). C1
fuel-mix and C3b price-shape are unchanged to reproducibility noise (≤0.15%
and 3rd-decimal NRMSE). The immaterial ST_GAS class's C7 diagnostic
(SKIPPED, <0.1% of ISO load, does not gate) shows the already-quantified
#1515 `threshold_percentile` effect (flagged days 27/36/58 → 126/118/121;
D-1 verdict pattern unchanged). Full detail, the DOF ledger, and the
price_mean/shape exception updates are in the bundle's
`calibration_attestation.json`.

**KNOWN GAP, owner-accepted (temporary): no ablation twin.** This keeper does
**not** carry a freshly-solved zero-forcing ablation twin (CLAUDE.md rule
20/D-3) — `neiso-49-stgas-netload-ablation` validated the retired,
unreproducible base price level and is not a valid twin for this bundle, so
it was retired alongside the keeper it validated. `scripts/audit_keepers.py`
correctly reports this as a **hard E9 failure** (`FAIL: 1`) — not a
grandfathered warning, since this is a fresh registration. **Ledgered** in
`calibration_attestation.json` (criterion: `governance`, classification:
`OWNER-DEFERRED (temporary)`). Follow-up: solve
`--zero-forcing-ablation` (same recipe, full 2023-2025 span) and register it
as `2026-07-06-neiso-50-head-repro-ablation` to close E9.

**Stripped:** `results/calibration/neiso_stgas_netload/` +
`neiso_stgas_netload-ablation/`, their registry sidecars, and their
`runs/*.js`. **Registered:** `2026-07-06-neiso-50-head-repro`. `keepers.json`
NEISO entry swapped; keeper-auditor run; `status.js` rebuilt.

**Open follow-up (real fix, not attempted here):** the honest path to
restoring legitimate HQ_import price separation is recalibrating
`IMPORT_TRANCHES`/`EXPORT_TRANCHES[NEISO]` in
`src/market_sim/config/interchange_config.py` against measured NEISO
interface data (the existing DOF-ledger entry already flags this: "audit C-6
open item: replace year-keyed rungs with measured hub prices / published
wheeling costs per seam") — not re-enabling `--priced-interchange` at its
current, already-shown-to-over-import static prices.

### 2026-07-06 — NEISO — L-49 confirmation re-solve: keeper `neiso-49-stgas-netload` MOVED at HEAD, but NOT from the #1515 item under review; C7 confirmed SKIPPED per the immateriality-cutoff action item

**Scope (confirm-only, no re-tune, no fit-criteria change).** Re-solved the
registered keeper `2026-07-06-neiso-49-stgas-netload` config verbatim —
`python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025
--commitment --reliability-floor --hydro-backfill-year 2024
--hydro-eia930-monthly --gas-hub-basis-daily --scarcity-price-overlay
--tranche-startup-amortization` — on current `main` HEAD, full 2023-2025
span in one invocation, into a throwaway bundle
(`results/calibration/neiso49_resolve_confirm/`, not registered, not a
keeper, no dashboard entry). Compared against the committed bundle
(`results/calibration/neiso_stgas_netload/`) and the dashboard's rendered
payload (`frontend/data/backcast/runs/2026-07-06-neiso-49-stgas-netload.js`,
read-only — decoded, not re-registered).

**C7 action item closed.** Per the 2026-07-06 rubric-immateriality entry
above, confirmed `metrics.json`'s `shape` criterion for this bundle reads
`SKIPPED` (ST_GAS is 0.05-0.10% of NEISO load, under the 2.5% D-1 gate) —
the prior session's requested confirmation is done.

**C1 (fuel-mix): unchanged.** Gas TWh model 54.23/58.76/61.53 (2023-25) vs
registered 54.16/58.69/61.53 — deltas ≤0.07 TWh (<0.15% relative); coal,
nuclear, wind, solar byte-identical. STANDS.

**C3b (price shape, monthly NRMSE): unchanged.** Recomputed demand-weighted
monthly LMP from `system.parquet` directly (score_price_shape's own method):
NRMSE 0.149/0.169/0.065 (2023-25) vs registered ~0.169 (2024, per the
neiso-49 log entry) — matches to 3 decimals. STANDS.

**C3a (mean LMP): MOVED — 2023 crosses CAVEAT → FAIL, but not from #1515.**

| year | actual RT | registered model (err) | HEAD model (err) | band shift |
|---|---|---|---|---|
| 2023 | 35.70 | 32.74 (−8.3%, CAVEAT) | 31.98 (−10.4%, **FAIL**) | commercial-band → beyond |
| 2024 | 39.50 | 36.43 (−7.8%, CAVEAT) | 36.11 (−8.6%, CAVEAT) | caveat deepens, no flip |
| 2025 | 65.89 | 64.84 (−1.6%, PASS) | 62.98 (−4.4%, PASS) | stays in target band |

Root cause **isolated and it is NOT the #1515 ST_GAS netload mechanism under
review**: a counterfactual re-solve on HEAD with the ST_GAS netload row's
`threshold_percentile` blanked (reverting to the literal 16.02 GW basis the
keeper was solved on) reproduces the SAME price drift (2023 avg 31.99, 2024
36.12, 2025 62.98 — all within noise of the as-is HEAD numbers, nowhere
close to the registered 32.74/36.43/64.84). The real driver: **NEISO's
HQ_import zonal price separation has collapsed to zero at HEAD.** The
registered bundle shows a real congestion split every year (mainland vs
HQ_import, $/MWh): 2023 32.74/31.99, 2024 36.43/36.12, 2025 64.84/62.98. The
fresh HEAD resolve (and the counterfactual) show **all five zones clearing
at one uniform system price** every year, converging to what used to be the
(lower) HQ_import-side price. This is unrelated to ST_GAS/#1515 — it traces
to something else in the ~15 other commits merged between the keeper's solve
commit (`ac11191`, dirty) and current HEAD (`dd85d5a`). Best candidate,
un-bisected (out of this lane's scope): `530afc3` "Stage 6: unify per-year
fleet assembly on shared build_base_fleet/build_dispatch_fleet" — it
explicitly touches NEISO-specific fleet plumbing (`apply_neiso_coldsnap_derate`,
`imports_after_hydro` "the backcast's historical LP column order") and is
claimed value-identical, which a zonal-separation regression would quietly
violate. **Flagging for the owner — not root-caused further under this
confirm-only lane.**

**#1515 effect, isolated and quantified (ST_GAS is immaterial, <0.1% of ISO
load — doesn't gate C7 or anything else, per the SKIPPED status above):**

| year | flagged days (fixed 16.02 GW, = keeper basis) | flagged days (p70-on-engine-netload, HEAD default) | ST_GAS energy, keeper → HEAD (TWh) |
|---|---|---|---|
| 2023 | 27 | **126** | 0.049 → 0.056 |
| 2024 | 36 | **118** | 0.004 → 0.008 |
| 2025 | 58 | **121** | 0.007 → 0.013 |

D-1 ST_GAS verdict pattern is unchanged either way (2023 FAIL, 2024 FAIL,
2025 pass); only the cv_ratio magnitude moves (e.g. 2023: 4.61 fixed →
1.80 p70). D-2 forced share stays sub-percent of ISO load both ways.
**Design concern for the owner:** `threshold_percentile` recomputes p70 on
the engine's *own* daily net-load series, which by construction always
flags ~30% of days (126/118/121 ≈ 30-35% of the year) — it cannot converge
toward the real committed-day counts (22/20/58/yr, ~6-16%) any better than
a fixed external threshold could, and here it's 2-5x further from them than
the original 27/36/58 fixed-threshold count was. The stated goal
("engine flags ~30% of days... matching actual committed-day counts",
`5e059c4`) doesn't hold up under this re-solve.

Other floors (CC_REGULAR, the only other `enabled=True` row) are unaffected:
forced share 0.59-1.05% of class both before and after, unchanged to 3
decimals. C8 stays PASS.

**Verdict: MOVED, but not by the wave item this lane was scoped to confirm.**
C3a 2023 would score FAIL at HEAD instead of the registered CAVEAT — a
genuine drift in a load-bearing criterion, driven by an unattributed
zonal-pricing change elsewhere on `main`, not by `#1515`. Per LANE scope, no
re-tune, no fit-criteria change, no keeper flip: `keepers.json`, `status.js`,
and the registered `neiso_stgas_netload` bundle are untouched. Recommend the
owner (a) bisect the HQ_import zonal-separation regression (candidate
`530afc3`) before treating neiso-49 as clean at today's HEAD, separately
from (b) the `threshold_percentile` design question above — given it
2-5x-overflags days relative to reality and the class it governs is
immaterial regardless (SKIPPED either way), the case for gating it off by
default and keeping the keeper on its original fixed-threshold basis looks
stronger than re-attesting it — but that call belongs to the owner, not
this lane.

Bundle: `results/calibration/neiso49_resolve_confirm/` (as-is HEAD resolve)
+ `results/calibration/neiso49_resolve_confirm/counterfactual_fixed_threshold/`
(isolation counterfactual, `threshold_percentile` reverted to blank for
this test only — the committed CSV is untouched). Neither is registered on
the dashboard; both are throwaway confirmation artifacts.

### 2026-07-06 — Rubric — C7 immateriality cut-off: a gated class under 2.5% of ISO total load no longer C7-gates (owner decision; supersedes the same-day compute-scoping note below)

**Owner decision, restated and widened.** The prior entry below framed the
2.5%-of-load call as "don't spend compute chasing ST_GAS" — a probe-skip.
The owner's actual instruction is broader and structural: **a D-1-gated
class under ~2.5% of ISO total load should never be a C7 gate at all, even
when its diurnal-shape verdict is a clean FAIL** — not merely "don't bother
re-running the probe." This is a rubric change, not a scheduling one.

**Change.** `scripts/calibration_verdict.py::score_shape` now takes optional
`ypay`/`ybench` and computes each D-1-gated class's actual share of ISO total
load (`_gen_totals` + `_total_load`, the same helpers C1/C2 use). A class
under `D1_SHAPE_MATERIALITY_LOAD_FRAC = 0.025` is recorded `SKIPPED`
regardless of its r/CV-ratio verdict — mirrors C2's existing `SYSVOL_MIN_TWH`
immateriality cut-off exactly (a shape defect on a near-noise-floor class
isn't withheld from a keeper). The underlying r/CV-ratio numbers are still
carried in the row's `magnitude` for visibility; they just stop counting
against the C7 protective-caveat budget. Without `ypay`/`ybench` (e.g. a raw
D-1-row unit test) the class gates exactly as before — no behavior change
for callers that don't pass the new args. `docs/calibration-determination-
rubric.md` C7 section updated to match; 4 new tests in
`tests/test_calibration_verdict.py::ShapeForcedShareTests` (98/98 pass).

**Effect on the C7 caveat / the 2026-07-06 adjudication hold (`dbda27f`).**
Whether this closes the NEISO marker hold depends on ST_GAS's actual share of
NEISO total load in the keeper years — not re-derived in this session (no
local bundle/dashboard access). If ST_GAS is confirmed < 2.5% of NEISO load
in 2023–2025, its C7 FAIL becomes SKIPPED and the "C7 ST_GAS diurnal
residual" hold reason no longer applies from C7's side (the winter-fuel
Component-B family is untouched by this change and may still hold the
marker on its own). **Action for the next session with bundle access:**
re-run `calibration_verdict.py` against the committed
`2026-07-06-neiso-49-stgas-netload` artifact and confirm the C7 row now
reads `SKIPPED (immaterial)` before treating the hold as narrowed.

### 2026-07-06 — NEISO — owner scoping decision: no further forced-commitment compute on sub-2.5%-of-load classes (ST_GAS out of scope for now) — *narrow framing, superseded above*

**Decision (owner, this session).** The L-15 lane's next planned step — probing
`--class-commitment-overrides` against the netload-basis fix
(`5e059c4`/PR #1515, merged) to test whether it closes the C7 ST_GAS
diurnal residual — is **not being run**. The owner is willing to leave
forced-commitment mechanism work ungated for asset classes that are under
~2.5% of NEISO load, and does not want compute spent chasing ST_GAS
specifically under that bar.

**Effect on C7 / the 2026-07-06 adjudication hold (`dbda27f`).** The
adjudication's "hold NEISO until Component B is re-examined" caveat
(C7 ST_GAS diurnal residual, 2023/24 still FAIL) is **not resolved** by this
decision — it is deprioritized. The two code-level enablement fixes already
merged (CAMPD-bin `class_commitment_overrides` unblock;
`ReliabilityFloorSpec.threshold_percentile` net-load basis fix) stand as
available mechanism infrastructure but will not be exercised in a probe run
under this scoping call. No new run, no registry entry, no keeper change.
**Superseded by the entry above** — the owner clarified this is a rubric
gating change, not just a probe-skip.

### 2026-07-06 — NYISO + NEISO — calibration-complete adjudication (rubric-v2 memo §6): owner HELD both markers; holdout quarantine unchanged, no solves

**Scope (no solves, no data intake, no dashboard changes).** Verified the
rubric-v2 memo §6 preconditions and put the calibration-complete marker
decision to the owner per rule 22. Stage-1 verification at HEAD (`2bd096b`):

- **Verdicts hold.** `calibration_verdict.py` fresh at HEAD: NYISO
  `2026-07-06-nyiso-53-li-tsl` and NEISO `2026-07-06-neiso-49-stgas-netload`
  both **CALIBRATED-WITH-CAVEATS**, zero FAILs (rubric v2).
  `audit_keepers.py --check` exits 0; E5 determination labels truthful
  (NYISO all-pass; NEISO carries only the E7 newer-run warning, and the newer
  runs are the registered NEGATIVE wfuelsec probes, correctly not the keeper).
- **U-01 RESOLVED — the winter-fuel Component-A probes were registered all
  along** (rule 15 satisfied): `2026-07-04-neiso-inventorycap-inert-probe` +
  `2026-07-04-neiso-dailybasis-oil-underrun` (sidecars, run payloads, and the
  2026-07-04 entry below), plus the Component-B pair
  `2026-07-06-neiso-wfuelsec-ab-v2`/`-v2off`. The gap register's U-01 predated
  these landings.
- **G-13 adjudicated for nyiso-53:** the original defect (nyiso-41 vs the CT
  offer de-leak) is moot — nyiso-53 was solved 2026-07-06 at `19c0e01`,
  post-de-leak, and no newer NYISO run exists. Honest residuals: HEAD is 132
  commits past the bundle SHA (scan of all 12 non-merge src commits in the
  window: every one other-ISO-gated, default-off, or on the disabled P2 path —
  no expected live-path change for a NYISO keeper-config backcast, unverified
  without a re-solve); both keeper bundles record `git.dirty: true`, and the
  NEISO bundle's recorded SHA (`ac11191`) predates its own mechanism commit
  (`a468fbf`) — both solved on PR branches, so "frozen config" means the
  committed `run_config.json` recipe, not a reproducible SHA.
- **C8 restated for the record (NYISO):** CT_PEAKER forced-at-floor share
  92.7% (1.49 of 1.60 TWh, 2023) / 86.7% (1.56 of 1.79, 2024) / 56.6%
  (1.45 of 2.57, 2025), rebuilt-floor lower bounds — admitted only through the
  ≤1 protective-ledger budget, ledgered against the #1344 data-blocked
  reserve-scarcity frontier (absolute forced energy down vs the nyiso-48
  baseline; selfsupply channel deleted; remaining floor is the windowed
  temperature-reliability ramp).

**Owner decision (2026-07-06, this session): both markers HELD.**
- **NYISO: hold until #1344 lands** — the C8 caveat (majority-to-near-total
  floor-carried CT energy in every scored year) dominates; no marker, no
  holdout intake, no one-shot.
- **NEISO: hold until Component B is re-examined** — the C7 ST_GAS diurnal
  residual (2023/24 still FAIL) and the winter-fuel mechanism family stay open;
  no marker, no holdout intake, no one-shot.
- The 2022/H1-2026 holdouts remain fully solve- and intake-quarantined for
  both ISOs (`calibration-complete.json` still `"complete": {}`). Execution
  scoping recorded for the eventual declaration: NYISO/NEISO have zero holdout
  intake today (CAMPD 2022 state files, 2022 zonal load/SMD, 2022 hub LMP, and
  2022 extensions of the keeper-lever gas-basis series — Algonquin daily,
  Transco Z6 NY daily, downstate CT basis — all absent; EIA-930 2022, F923
  2022, eGRID2022, demand profiles 2022 already in-repo), and the H1-2026
  half is publication-blocked regardless (CAMPD Q2-2026 unposted, delivered
  gas ends April, F3 demand-profile 8760 contract).

### 2026-07-06 — CAISO — L-10: reserve co-optimization BUILT (`_caiso_design`, the only ISO that lacked one) — PROBE `caiso 59 reserve-coopt`, real but INERT, keeper stays caiso-51

**Mechanism (issue #1492).** Built the CAISO per-generator energy+reserve
co-optimization: Spin + Non-Spin contingency products (BAL-002-WECC-3
`max(MSSC, 6% load)`, half/half) co-drawn on one ramp10-bounded pergen R pool
(the MISO `miso_reserve_pergen` structure — no core dispatch change), priced by
the published tariff §27.1.2.3.5 scarcity demand curves (spin 10% of the $1,000
soft bid cap flat; non-spin 50/60/70% at 70/210 MW). Behind default-off
`caiso_reserve_coopt`, lifting the historical `apply_reserve_coopt` short-circuit
(default byte-identical). Zero fitted parameters (rules 5/23). Also: CAISO
ramp-capability extract added to the #1500 datatype (BA CISO / state CA; 351
plants, 36.8 GW thermal), and the two datatype-contract reds #1500 left on main
(`test_clean_io` ALL_DATATYPES + `test_data_dictionary_sync`) fixed.

**A/B (both replayed from caiso-51 at HEAD, only the reserve flags differ;
`caiso59_reserve_ab_base` OFF vs `caiso59_reserve_coopt` ON).** The mechanism is
real but **largely INERT** — the MISO lesson confirmed: the pergen pool is
Σ ≈ 12.9 GW deliverable ramp vs a ~2.2 GW requirement, so the perfect-foresight
LP clears it from headroom almost everywhere. Reserve fires in **~100 hours of
2023 only** (clearing price up to **$800 = spin $100 + non-spin $700**, confirming
the co-opt sums the product duals), idle in 2024/2025.

| year | C3a vs RT | Δ mean vs A | C3c DA-expr >$200 | Δ tail vs A |
|---|---|---|---|---|
| 2023 | +20.3% | **+$0.47** | 483h vs 41h DA / 21h RT — FAIL | +16 zone-h, 0 sys-h |
| 2024 | +35.3% | +$0.00 | 0h vs 52h DA — FAIL | 0 |
| 2025 | +42.7% | −$0.00 | 0h vs 0h — PASS | 0 |

**~455h-vs-21h driver question → NEGATIVE.** The 2023 over-tail (model 483h vs
21h RT actual) is NOT a missing-reserve-scarcity gap: adding the published
reserve co-opt leaves it at 483h (C3c unchanged) and moves the mean only +$0.47.
The over-tail is owned by the evening-merit / RA-commitment-uplift gap
(`FINDING-caiso-evening-merit-2026-07-04`), not absent reserve pricing.

**Disposition (rule 1).** Kept default-off — a structurally-correct mechanism
stays in regardless of the flat residual; the inertness is a supply-scoping
result. Next increments (each shrinks the pool's dominance): storage reserve
(dominant CAISO AS provider, unbacked by the pergen builder) → hydro
(`ramp10=0`) → regulation. Keeper stays `caiso-51` (owner decision). Dashboard:
`2026-07-06-caiso-59-reserve-coopt` (PROBE); pruned oldest
`2026-07-03-caiso-49-perhub-seam` to hold the 15-run cap. Bundle FINDING:
`results/calibration/caiso59_reserve_coopt/FINDING-reserve-coopt-ab-2026-07-06.md`;
design doc `docs/multi-iso/caiso-reserve-coopt.md`.

### 2026-07-06 — NEISO — L-15 continuation: C7 ST_GAS re-grounded on a net-load commitment limb + NEISO-measured offer bands: NEW KEEPER `neiso 49 stgas-netload` (2025 D-1 PASSES; still NOT-YET on the caveat budget)

**Goal (L-15 / gap register G-16 + the C7 hard caveat).** Root-cause the ST_GAS
diurnal-shape FAIL carried by the neiso-48 keeper (D-1: profile_r 0.62/0.66/0.71,
off-peak CV ratio 35.4/0.0/0.0) — the second hard caveat blocking NEISO's caveat
budget — and close whatever of it is structurally closable. Also: C2 final-vintage
check (task 4) and the #1476 winter-fuel follow-through.

**Root cause (measured, unit-level).** The gated NEISO ST_GAS class is ONE plant —
Montville Station (ORIS 546, CT; units 5+6, both residual-oil-primary in CEMS,
~495 MW bench nameplate vs an 81 MW model bin ≈ unit 5). The real units run in
6–21 multi-day committed blocks per year (runs of 20–200 h) at ~60–130 MW —
min-stable overnight, load-following daytime — concentrated on TIGHT-SYSTEM days:
the Feb-2023 arctic blast AND the post-Mystic Jun–Aug 2024/2025 heat events plus
Jan/Dec 2025. The keeper's model ran the bin 2–5 times a year for 1–6 evening
hours: (a) NOTHING committed it — the two ST_GAS temperature limbs have been
disabled since the 2026-06-30 rebuild as unidentified (tmax ρ=0.23 < 0.3; tmin
n=8 < 30), because neither temperature alone explains a hot-AND-cold event set;
(b) its offer bands were all-neutral 1.0 placeholders (the 0c6c833 de-leak), so
its tranches never cleared the daytime merit. The A+B probe (#1476) proved a flat
floor alone cannot fix profile_r — a constant shifts CV but correlation is
constant-invariant.

**Change 1 — Connecticut ST_GAS `netload` reliability limb (rule-19 re-grounding).**
Daily peak system net-load unifies the hot+cold commitment driver: 90% of the 100
committed days sit above the p70 of daily-peak net-load (median = p93); Spearman
ρ=0.51, n=329 flagged days — vs the disabled limbs' 0.23/n=8. Derived by the
frozen `derive_reliability_coeffs.py` methodology (threshold p70 = 16.02 GW,
floor_pct 0.0336 = commit_frac 0.2796 × physical min_stable 0.12), the exact
CAISO-CT netload-limb precedent (rebuild-plan review decision 2: net-load limbs
carry no temperature gate); all-24h boiler gate, 48 h steam event bridging. Two
derive-script correctness fixes shipped with it (commit cites the source-data
basis, rule 23): a day whose CAMPD rows are all-NaN grossLoad now counts as
OFFLINE (cf=0/online_frac=0) instead of dropping out — the single-plant
saturation artifact that froze the old ST_GAS rows at commit_frac=baseline=1.0 —
and the netload threshold percentile is restricted to the 2023–2025 derivation
span (the EIA-930 BA parquets were since backfilled to 2019; rule-22 holdout
periods must never enter a calibration-derived threshold). Rule-24 reconcile:
when Component B (`neiso_winter_fuel_mustrun`, default off) is co-armed, it now
drops ST_GAS from its scope — the netload limb owns the steam commitment.

**Change 2 — NEISO-measured offer bands (the ledgered C3a/C3b closure path).**
`derive_campd_marginal_hr.py --iso NEISO` (the NYISO run-32 tool, ISO-generic)
grounds the de-leaked neutral bands in NEISO's own measured CAMPD marginal heat
rates: ST_GAS 0.79/0.85/0.89 (native marginal 0.642/0.692/0.731 — a genuinely
RISING measured ramp, unlike NYISO's flat steam — × the NEISO-native CC reach
ratio 1.223 = CC econ_high band 1.15 / native CC marginal 0.940; no cross-ISO
value, rule 26); CC_CHP 1.15/1.17/1.19 (native flat 0.94–0.97 × 1.223, thin
monotone spread; n=5, wide IQR disclosed). CT_PEAKER econ bands STAY neutral —
now measurement-AFFIRMED, not just de-leaked: NEISO's CT marginal HR is
flat-to-FALLING with load (0.808/0.745/0.700, n=18), so the removed ERCOT
1.27→1.98 ramp had no NEISO physical basis and the real above-cost CT component
is the (already-priced) startup amortization. CT_CHP stays neutral (n=1).

**Result (`2026-07-06-neiso-49-stgas-netload`, 2023-2025, one bundle, vs keeper
neiso-48):**

| metric | neiso-48 | neiso-49 | gate |
|---|---|---|---|
| D-1 ST_GAS 2025 | r 0.705, cv 0.0 FAIL | **r 0.844, cv_ratio 2.87 PASS** | first-ever ST_GAS pass |
| D-1 ST_GAS 2023 | r 0.619, cv_ratio 35.4 FAIL | r 0.490, cv_ratio 4.61 FAIL | CV collapse fixed; r honest-lower (see below) |
| D-1 ST_GAS 2024 | r 0.659, cv 0.0 FAIL | r 0.725, cv 0.0 FAIL | flat-floor-only year |
| D-2 ST_GAS forced share | 0.0 | 0.0 (floor scaffolding only; dispatch economic) | PASS |
| C1 | 12/12 | 12/12 (2023 ST_GAS 0.041 TWh ≈ actual 0.041) | PASS |
| C8 / C4 / C5a | PASS | PASS | — |
| C3a/C3b/C3c | caveats | unchanged (−8.3/−7.8%; 0.169; 0h >$300) | caveat |
| C5b 2025 | −49.3% (1.05 TWh) | **−56.3% (0.91 TWh) — DEEPENED, disclosed** | caveat |

The model ST_GAS now runs ~8,100 h in 2023 at a 5–7.5 MW diurnal hump (was 13
spiky hours) with near-zero energy at the binding floor (0.25%): the commitment
floor is scaffolding and the dispatch is economic — exactly the rule-20 shape a
commitment mechanism must have. **Honest costs (rule 1, disclosed, NOT to be won
back):** C5b deepens because the measured-cost steam tranche shaves the
artificial evening peaks the PS fleet was arbitraging — the missing spread is the
same ledgered scarcity-formation gap; and 2023 profile_r reads lower than the
keeper because the old 0.619 correlated a 13-hour spiky artifact while the new
0.490 is a real profile with a genuine mis-phase (model evening-peaked vs the
actual's midday-peaked event days).

**Remaining C7 root causes (ledgered in the attestation, next NEISO items):**
(1) 2024 is a flat-floor-only year — at $2.19 HH gas the unit clears no merit
hours, so the committed profile carries no intra-day variation (cv 0.0); coupled
to the C3a price-depression family. (2) Engine-vs-derivation net-load basis: the
engine's exogenous net-load flags 27/36/58 days (2023/24/25) vs the derivation's
~110/yr on the EIA-930 basis — notably tracking the actual committed-day counts
(22/20/58) — a basis-consistency follow-up. (3) The ~5 MW year-round merit
sliver is a sub-min-stable LP-relaxation artifact; the physical fix is steam
commitment integrality in P2 via `class_commitment_overrides`, whose CAMPD-bin
early-return in `commitment._commitment_params` currently prevents enabling a
zero-min-run bin — a documented wiring follow-up.

**Task-4 check: C2 final 2025 EIA-923 vintage has NOT landed** (the 923 monthly
parquet and the 2025 completeness part are unchanged since PR #1434); no
re-score, the C2 ledger stands. Re-fetching a fresher preliminary vintage would
change benchmark actuals for all six ISOs — out of this lane's namespace.

**KEEPER PROMOTED: `2026-07-06-neiso-49-stgas-netload`** (zero-forcing ablation
twin `…-ablation` registered alongside, rule 21) — the most structurally
faithful NEISO run: two unidentified disabled limbs replaced by one identified
measured driver, neutral placeholder offers replaced by the ISO's own measured
marginal heat rates, no criterion FAIL introduced, nothing fitted to a residual.
**Determination stays NOT-YET on the caveat budget alone (hard C2+C7 2>1; soft
C3a/C3b/C3c/C5b 4>2; zero criterion FAILs)** — no calibration-complete memo this
session. The credible path to the budget: C7 closes via the three ledgered
follow-ups above (2024's cv is the C3a family), C3a/C3b close via scarcity/price
formation (the measured bands having removed the offer-side excuse), C3c/C5b
close together via winter scarcity-price formation — NOT via more commitment
tuning (the #1476 negative stands) and never via a storage/offer tune.

Dashboard: registered `2026-07-06-neiso-49-stgas-netload` (KEEPER) +
`…-ablation`; pruned neiso-44-base-control / neiso-45-flat-econ (top-15);
`keepers.json` swapped; keeper-auditor run; `status.js` rebuilt. Reproduce:
`python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025
--commitment --reliability-floor --hydro-backfill-year 2024
--hydro-eia930-monthly --gas-hub-basis-daily --scarcity-price-overlay
--tranche-startup-amortization --out-dir results/calibration/neiso_stgas_netload`.


<!-- Copy the block below for each calibration run. Newest first. -->

### 2026-07-06 — CAISO — L-10 continuation: G-15 D-8 closure A/B EXECUTED and FAILED (caiso 57), #1346 re-gate candidate solved (caiso 58): drag stays, keeper decision for owner

**Goal (L-10 continuation; D-8 closure plan §4, issue #1346, gap register G-11/G-15).**
(1) Execute the D-8 closure A/B as a REGISTERED full-span solve at HEAD (the 2026-07-04
`caiso-ramplcr-probe-rejected` ran the same A/B on 07-04 code but never reached the
dashboard — git-relay 413 — and predates the InterchangeSpec/scalar merges). (2) Resolve
#1346 per the bisect verdict — re-gate, not revert: solve the keeper config at HEAD with
the mandated `use_plant_emission_rates_v2=True` rider (L-8 memo §9.6), caiso-55 as its
v2-off twin. (3) WECC import volume: the CEC/CARB specified-import intake has NOT landed
(no data, no commits); data-ask refreshed on #1373 (DMM 2025 annual report ~Aug 2026;
OASIS-gated path-level series need `fetch-caiso-oasis.yml`); the lane proceeds on the
Lever-B DMM/MIC grounding — no fitted import cap anywhere (the 7,500 MW scalar stays
fallback-only, out of the binding path).

**Evening-merit lever inventory (why no new offer/import lever was built).** The
caiso-48/51-thread levers are already on main: import tranche prices = the keeper's
per-hub measured-hub pricing (all-spot was tried and REJECTED as caiso-49; firm-base won
on structure); CC offer ordering = Lever A committed 1.00× SRMC floor (`1ada584`) +
Lever B DMM firm volumes (`3ac6f19`); P1 already amortizes startup into bid cost (CC's
markup is small because its P0 runs are long — real, not a gap). The one un-built
mechanism in the evening-price space is a CAISO reserve co-optimization —
`reserve_config` has designs for the other five ISOs and `apply_reserve_coopt` hard-
excludes CAISO. Assessed and DEFERRED with published anchors collected (tariff
§27.1.2.3.5 scarcity demand curves — spin 10% / non-spin 50-60-70% of the energy bid cap
at 70/210 MW shortage tiers; §8.2.3.2 → BAL-002-WECC-3 R1 ≈6% of load, DMM practice
~6.3%, ~half spin): a zone-aggregate ungated family is INERT on CAISO's ~10 GW idle CC
headroom (the MISO pergen lesson), a correct build needs pergen/ramp10 + online-quality
scoping (a full lane), and its price effect lands in exactly the hours the model already
over-tails. Filed as issue #1492 (C3c/AS-award thread) — built when it can be built
right, never as a half-mechanism (rule 1).

**caiso 57 — D-8 closure A/B arm (PROBE `2026-07-06-caiso-57-ramp-lcr`, bundle
`results/calibration/caiso57_ramplcr_dragoff`).** Byte-faithful `replay_keeper.py` of the
caiso-51 keeper at HEAD; deltas exactly the closure plan's arm: `ct_netload_drag=false`,
`ramp_limits=true`, `local_capacity_constraints=true`; v2 OFF as the keeper ran.
Environment matched to caiso-55/56 (capdel partition absent → MIC no-op inert;
shared-input hashes byte-identical: `eia930-3697b3`, `eia923-b95fbb`, `campd-cceb61`).
Decision rule scored on the P2 pass (the chain's basis); P1 in parentheses:

| year | arm-Y eve CT MW | drag arm (recon) | CAMPD actual | arm-Y TWh | drag TWh (caiso-55) | actual |
|---|---|---|---|---|---|---|
| 2023 | 309 (552) | ~690–860 | 850 | 1.73 | 2.04 | 3.05 |
| 2024 | 146 (236) | ~580–600 | 770 | 0.73 | 1.70 | 3.30 |
| 2025 | 106 (127) | ~425–445 | 303 | 0.68 | 1.30 | 1.65 |

**VERDICT: FAIL on criterion (i) in all three years** (evening CT below the drag arm's
AND farther from CAMPD actual, 2025 included) — while (ii)/(iii) hold: D-4 off-window 0%;
D-2 CT forced share **0.4/1.0/0.03% PASS** (sole mechanism `ra_mustoffer_bridge`; the LCR
row attributes no CT forcing — its dual is uplift-like by design, never in the zonal
LMP); 2023 CT D-1 r 0.803/CV-ratio 0.883 best-in-chain (2024/25 r 0.740/0.613 <0.8 as in
every drag-off arm — small noisy fleet). **Per the §4 fail branch: `ct_netload_drag`
STAYS the CAISO default (most structurally faithful available mechanism, rule 1), G-15
stays OPEN, the D-8 ±15% LOYO gate (calibration-complete item 4) stays red.** Nothing
re-tuned.

**The load-bearing new finding — the suppressor MOVED to P2.** At HEAD the mechanisms are
not P1-inert as the 07-04 probe concluded: P1 evening CT reaches 552/236/127 MW and class
energy +0.93/+0.18/+0.29 TWh vs caiso-56 (the 2023 LA-Basin 7,529 MW requirement + ~480 h
of endogenous evening scarcity clear real CT on merit). The P2 UC decommit then strips
those runs (552→309, 236→146, 127→106): the commitment hurdle sees only energy margin —
no credit for the LCR row's shadow value, i.e. no bid-cost-recovery/uplift analogue,
which is exactly how CAISO pays locally-committed units. **Follow-up build for the
thread: credit the LCR dual in the P2 commitment margin (the existing AS-aware `as_value`
pattern in `model/commitment.py`) — not a floor, never a drag re-tune (rules 1/19).**

**C3a decomposition (honest; remainder attributed, not absorbed).** Mean SP15 LMP is
unchanged across the whole CT complex: caiso-57 69.2/46.5/48.7 vs caiso-55 (drag ON)
69.2/46.5/48.9 — neither the drag, nor its ablation, nor ramp+LCR moves the annual mean
(caiso-56 already showed C3a +21.4/+36.3/+43.7 ≈ drag-ON). The +20-44% body overprice is
owned by the open midday/shoulder RUC-long gap (caiso-51 next-lever 2) and the seam/gas
threads (caiso-54: the daily-gas fix was real but marginal ~3%); the tail is
over-predicted in 2023 (~481 h >$200 vs 21, both arms) and under-predicted in 2024/25
(0 h vs 35/8) — the latter is the missing scarcity/AS mechanism (#1492). No admissible
lever this session moves C3a; it is left attributed.

**caiso 58 — #1346 re-gate candidate (`2026-07-06-caiso-58-v2-regate`, bundle
`results/calibration/caiso58_v2_regate`).** Keeper config replayed at HEAD with the
single delta `use_plant_emission_rates_v2=true` (drag ON per the D-8 fail branch;
caiso-55 is the v2-off twin). v2 attribution vs caiso-55: CT 2.05/1.70/1.36 TWh (was
2.04/1.70/1.30), CC −0.4/−0.4/−0.1 TWh, SP15 mean −0.5/−0.8/−0.5 $/MWh, 2023 tail 489 vs
483 h — the small measured-rate re-ranking §9.6 predicted, confirming v2 is live and
dispatch-affecting under CARB pricing. D-2 CT forced share 59.7/65.9/65.4% (bundle
`legitimacy_diagnostics.md` is the record — sums `ct_netload_drag` + `ra_mustoffer_bridge`;
reconciles a 2023/2024 rounding mismatch vs this log's prior 59.3/65.8; honest
rule-20 FAIL, D-4 off-window 0%). This is what main
actually produces for the keeper config; the committed caiso-51 dashboard numbers
(CT 3.47/3.38/2.84, C8 27-33%) remain pre-scrub artifacts main cannot reproduce (#1346
diagnosis).

**Keeper recommendation (owner decision; `keepers.json` untouched).** No rule-20-clean
candidate exists: caiso-57 passes the forced-energy budget but fails the D-8 level
criterion (missing the commitment-economics structure above); caiso-58/caiso-55 carry the
honest C8 59-71% FAIL. Lane recommendation: keeper stays `caiso-51` until the P2
LCR-dual-credit build runs (it is the first mechanism with a credible path to BOTH
rule-20 PASS and the drag's level), with caiso-58 registered as the reproducible-at-HEAD
reference the owner may promote on the pjm-77/neiso-48 honest-diagnostics precedent if
dashboard-reproducibility outweighs the budget optics.

Rules compliance: solve years 2023-2025 only (rule 22); full-span single bundles (rule
16); years sequential within runs and the two heavy solves run sequentially (rule 12 +
the 07-04 concurrent-arm OOM precedent); both runs registered whatever the result (rule
15); no coefficient touched, no fitted parameter added (rules 13/21/24); retention pruned
to top-15 (dropped 2026-07-01-caiso-47-capdel-arm, 2026-07-02-caiso-48-solar-decommit
sidecars+payloads; bundles kept); `audit_keepers.py --check` green pre/post.

### 2026-07-06 — NYISO — KEEPER PROMOTED: `2026-07-06-nyiso-53-li-tsl` replaces `2026-07-03-nyiso-41-hub-prices` (owner decision, L-11)

**Owner decision 2026-07-06: the L-11 recommendation is accepted** (superseding
the PR-#1442 nyiso-52 order); the keeper is the already-registered nyiso-53 run
exactly as solved — no config change bundled into the promotion. Mechanics:

- **D-3 zero-forcing ablation twin** solved (keeper recipe verbatim,
  `zero_forcing_ablation=True`, full-span 2023-2025 sequential) and registered:
  `2026-07-06-nyiso-53-li-tsl-ablation` (bundle
  `results/calibration/nyiso53_litsl_v2-ablation`), linked from the keeper
  sidecar with the market story. Keeper-vs-twin delta: the floors buy ST_GAS
  +2.74/+3.82/+3.89 and CT_PEAKER +1.06/+0.87/+0.55 TWh (displacing CC
  −2.3/−3.1/−3.0) — and even WITH the floors both classes still under-run
  measured actuals (ST_GAS 7.2/8.1/10.3 vs 8.7/11.1/16.0 TWh), so the forcing
  moves dispatch toward the measurement, never past it (the un-floored LP's
  miss is the #1344 commitment frontier). The nyiso53-v2off-twin registered
  earlier is the §9.6 v2 ATTRIBUTION twin only — distinct artifact, kept.
- **Attestation** (`calibration_attestation.json`, dof-ledger/v1, 11 entries /
  6 residual): C8 CT_PEAKER forced-share 92.7/86.7/56.6% (cap 10%) ledgered as
  a DISCLOSED HARD BREACH — owner promoted with eyes open: absolute forced
  energy FELL to 1.486/1.555/1.455 TWh (nyiso-48's selfsupply floor alone
  forced 1.84/2.87/1.86, and that channel is deleted); the share is high
  because economic CT collapses without the #1344 reserve-scarcity structure
  (data-blocked on Ask-B). C3c 0/0/7 h vs 10/12/42 and the CT_PEAKER grid
  volume under-run (1.28/1.44/2.40 vs 2.26/2.13/2.84 TWh, within C1 band)
  carry the same attribution. DOF ledger: `NYISO_LOCAL_SELFSUPPLY_FRAC
  ['Long_Island']` (residual, S5) RETIRED — replaced by the published Zone-K
  TSL (identification: published); v2 plant rates + downstate citygate premium
  added as measured. Determination **NOT-YET** (hard 1/1, soft 4/2) — same
  class as every current keeper; promoted as most structurally faithful, per
  rule 1, not lowest-residual.
- **Bookkeeping:** `keepers.json` NYISO → `2026-07-06-nyiso-53-li-tsl`;
  `build_status.py` re-run post-rebase; D-9 quarantine report regenerated on
  the new keeper set; the 2026-07-05 E7 documented-state warning for NYISO
  RESOLVES (nyiso-41 leaves the keeper set and its E9 grandfather entry is
  removed per the list's own contract); the D-7 statmode NYISO section is
  flagged STALE vs this swap (G-10 truth-in-labeling; statmode NOT re-run).
  nyiso-41's committed bundle and registration remain on the dashboard as the
  prior keeper (the one meaningful historical comparison, per retention).

### 2026-07-06 — PJM — G-20 reserve/ORDC Phase 2 UNBLOCKED + probe (pjm 81 coopt-pergen): PROBE, keeper stays pjm-77

**Goal (gap register G-20; lane L-13 continuation, pjm-c3-reserve-phase2).**
`docs/multi-iso/pjm-reserve-ordc.md` Phase 2 — the designed fix for the
C3a/b/c FAIL (0 scarcity hours vs 6/18/59 actual) — was blocked on (a) the
per-gen co-opt's memory (P1 OOM at the plant-in-MAD tier, 2026-07-02
memtest) and (b) ramp-rate data quality. Both attacked:

- **(a) Memory — re-tiered to the pooling the other co-opt keepers use.**
  Survey: ERCOT's `ercot34` keeper co-opt is zone-aggregate pooled headroom
  rows (no per-unit R); MISO's `miso-39` keeper runs pergen with
  **(zone, fuel-class) pooled R columns** + hourly availability-scaled ramp
  caps and fits the box. `pjm_reserve_pergen` re-tiered to the MISO class
  tier: 39 R columns / 341,640 joint rows on the real 2024 fleet (vs
  257 / 2.25M in the OOM'd plant tier, ~6.6× fewer). P1 now solves: peak
  ~15.0 GB with a 10 GB swapfile absorbing a ~0.4 GB transient (the
  pjm-78/79 convention). Same published two-step ORDC, same nested RTO+MAD
  measured families — a documented memory scope-down (rules 1/11).
- **(b) Ramp data — measured intake replaces the class estimate.** New
  `ramp-capability` clean datatype (schema-first, per-ISO registry, PJM +
  MISO curated; `scripts/curate_ramp_capability.py`): EIA-860 Schedule 3.1
  "Time from Cold Shutdown to Full Load" = "10M" fast-start thermal
  capacity per plant (~3.0 GW in the PJM BA) + CAMPD CEMS max observed
  1-hour plant gross-load up-ramp (pooled 2023–2025; 2022/2026 holdouts
  excluded by construction, rule 22). Reconciliation onto
  `FleetArrays.ramp10` (GATED `measured_ramp_capability`, default off):
  fast-start floor, envelope ceiling on the NREL class rate (CEMS is
  hourly — the envelope is a ceiling, never the 10-min quantity itself),
  class fallback for uncovered plants (rule 14). PJM deliverable cap thins
  ~50 → ~40 GW (p50).

**Probe `pjm-81` / dashboard `2026-07-06-pjm-81-coopt-pergen`** (bundle
`results/calibration/pjm81_coopt_pergen`): the pjm-78 baseline recipe (=
pjm-77 keeper recipe on HEAD, the registered same-SHA comparator) +
`pjm_reserve_pergen` + `measured_ramp_capability`, drag unchanged, full
span 2023–2025, single invocation, sequential years (rules 12/16), clean
demand tree (zero fallback warnings).

**Result (honest): structure lands, price stack ~unmoved.**
- Dispatch is byte-comparable to pjm-78 at class grain (ST_GAS 20.4/17.2/
  20.1, CC_REGULAR 295.3/322.8/308.9, CT_PEAKER 27.3/23.4/35.4, COAL_BIT
  112.5/112.2/137.8 TWh — identical to ±0.1). Verdict criterion-identical:
  C1 14/16 (free 10/12), C2 FAIL 2025 gas +2.9%/coal +3.9%, C3a FAIL
  −8.0%/−13.3% (2024/2025), C3b FAIL 0.175–0.196, **C3c FAIL 0 h vs
  6/18/59**, C4/C5a/C7 PASS, C8 FAIL 12.0% (2024 CT_PEAKER), C6 UNATTESTED
  (probe). NOT-YET.
- **The in-LP reserve price is nonzero for the first time in any PJM
  scoping**: exactly 1 hour — 2025-06-23 h19 (the June-2025 heat wave),
  a $46.47 opportunity-cost dual lifting the year-max LMP to $158.61 —
  vs $0 in all 26,280 hours of every prior variant (pjm-62 zone-aggregate,
  supply-capped, online-gated). The mechanism works; the model is simply
  almost never tight.

**Attribution (rule 14).** With the measured-deliverable pool at ~33–45 GW
against the ~3.3–4.1 GW measured Primary requirement, the perfect-foresight
pool margin binds essentially never — even per-pool joint P+R competition
with measured ramp caps cannot price the $75–200 afternoon band while
~10× the requirement sits as free deliverable headroom. This empirically
closes the "would the per-gen build price the band?" question at the
strongest admissible supply-side scoping: **the remaining blocker is
Phase-1 commitment posture** (the LP's online reserve never thins from
~14 GW toward PJM's real ~3 GW), not reserve structure, memory, or ramp
data. No breakpoint lowered, no penalty inflated, no requirement padded
(rule 13/26 clean).

**Disposition: keeper stays `2026-07-05-pjm-77-ct-relfloor`. pjm-81 is NOT
a promotion case** (no criterion gain; C6 unattested; no ablation twin —
rule 21 applies at promotion). **Recommendation to owner:** carry
`pjm_reserve_pergen` + `measured_ramp_capability` as retained structure in
the NEXT keeper candidate (rule 1 — real market design, fit-neutral,
memory-proven), and direct the C3 scarcity work at the Phase-1 commitment
posture (the drag's rule-19 replacement endgame in the C8 memo §6.5 stays
owner-gated and untouched). Registered PROBE, full span; retention at
15 non-twin PJM runs (no prune needed).

### 2026-07-06 — PJM — G-21 SRMC re-grounding cycle (pjm 79 srmc-baseline / pjm 80 srmc-reground): PROBES, keeper stays pjm-77

**Goal (gap register G-21; issue #1302).** `FINDING-pjm-burndown-2026-07.md`
§2 flagged two committed offer bands as pure residual artifacts sitting below
the Manual-15 SRMC floor: ST_GAS committed/econ_low/econ_high 0.4752/0.6552/
0.90 and CT_INTERMEDIATE committed/econ_low 0.9/0.92 — a non-CHP steam/CT
unit's part-load incremental heat rate is *above* full-load, so no tranche
should offer below 1.0× AHR × delivered fuel (the same floor CC_REGULAR
received in pjm-74). Task: re-ground both to 1.0×, run the full-span A/B,
decompose what the sub-SRMC offers were compensating for, and open root-cause
issues rather than tune the multipliers back down (rule 14).

**Method.** Two full 2023–2025 solves on current HEAD (`7cb584e`), sequential
years, single invocation each (rule 12):
- **pjm-78 / dashboard `pjm 79 srmc-baseline`**
  (`results/calibration/pjm78_srmc_baseline`) — the pjm-77 keeper recipe
  VERBATIM (same offer curve, same drag, same reliability-floor config
  including the 2026-07-06 CT_CHP scrub), re-solved on HEAD as the same-SHA
  A/B comparator.
- **pjm-79 / dashboard `pjm 80 srmc-reground`**
  (`results/calibration/pjm79_srmc_reground`) — pjm-78 with ST_GAS
  committed/econ_low/econ_high → 1.00/1.00/1.00 and CT_INTERMEDIATE
  committed/econ_low → 1.00/1.00 (`scripts/run_pjm79_srmc_reground.py`).

Both bundles hit a container OOM on the first attempt (12 GB LP, no swap;
resolved with a 10 GB swapfile) and both initially solved against the
*corrupted* legacy `eia_demand_profiles.parquet` (PR #1426's known PJM demand
defect — the same one the 2026-07-05 `pjm-78-demand-regate` entry below
found immaterial to pjm-77). Both were re-solved end-to-end after running
`scripts/regenerate_clean.py demand-profile`; the final bundles carry zero
demand-fallback warnings.

**Decomposition (`scripts/diag_pjm_srmc_ab.py`, per-class TWh model vs actual,
2023/2024/2025):**

| class | pjm-78 (baseline) | pjm-79 (re-grounded) | Δ | actual (avg) |
|---|---|---|---|---|
| ST_GAS | 20.4 / 17.3 / 20.1 | 4.3 / 3.5 / 5.9 | **−16.0 / −13.7 / −14.2** | 8.6 / 12.4 / 14.3 |
| CC_REGULAR | 295.3 / 322.8 / 308.9 | 305.2 / 331.0 / 318.1 | **+9.9 / +8.1 / +9.3** | 314.8 / 317.0 / 319.9 |
| CT_PEAKER | 27.3 / 23.4 / 35.4 | 26.0 / 21.6 / 32.5 | −1.3 / −1.8 / −2.9 | 26.1 / 28.1 / 24.7 |
| COAL_BIT | 112.5 / 112.2 / 137.8 | 115.9 / 115.0 / 140.6 | +3.4 / +2.9 / +2.8 | 110.8 / 111.6 / 133.7 |

De-flooding ST_GAS removes ~14–16 TWh/yr, but **~90% of it lands on
CC_REGULAR, not on the actual level** — CC_REGULAR was already close to
actuals in the baseline (2024: +5.9 TWh) and the re-grounding pushes it to
over-run (2024: +14.0 TWh), while ST_GAS flips from a large over-run (+4.9 TWh
2024) to a new under-run (−8.9 TWh 2024). The residual didn't shrink — it
**relocated between two gas classes**, plus a smaller secondary absorption
into coal (+2.8–3.4 TWh/yr, itself already over-running). CT_PEAKER — the
class this lane's C8 drag memo flagged as denominator-sensitive — improves
only marginally (2024 model volume 20.7→19.0 TWh, moving *further* from the
28.1 TWh actual): the memo's hoped-for fix does not materialize; the drag
share **rises** 12.0%→14.0% (2024) because its numerator is unchanged while
the class total shrinks. Gen-weighted mean LMP moves +$0.7–1.0/MWh across all
three years; scarcity tail stays exactly 0 h > $200 both ways (the price-level
miss is untouched — confirms burndown §3's finding that PJM's scarcity gap is
the memory-blocked per-gen reserve/ORDC item, not the offer curve).

**Verdicts (`scripts/calibration_verdict.py`, both NOT-YET, C6 UNATTESTED —
probes, no governance attestation drafted for either):**

| criterion | pjm-78 baseline | pjm-79 re-grounded |
|---|---|---|
| C1 fuel-mix | FAIL: 2023 CC_REGULAR −19.4 TWh, ST_GAS +11.8 TWh | FAIL: 2023 CC_REGULAR −9.6 TWh; 2024 CC_REGULAR +14.0 TWh, ST_GAS −8.9 TWh |
| C2 system volume | FAIL: 2025 gas +2.9%, coal +3.9% | FAIL: 2025 coal +6.2% (gas clears) |
| C3a mean LMP | FAIL 2024/2025 (−8.0%/−13.3%) | FAIL 2024/2025 (−5.8%/−11.0%, closer but still failing) |
| C3b price shape | FAIL all years (NRMSE 0.175–0.196) | FAIL all years (NRMSE 0.160–0.186, ~flat) |
| C3c scarcity tail | FAIL all years (0h vs 6/18/59) | FAIL all years (0h vs 6/18/59, unchanged) |
| C8 (D-2) CT_PEAKER 2024 | FAIL 12.0% (2.49/20.69 TWh) | FAIL **14.0%** (2.65/18.95 TWh) — worse |
| D-10 free-class C1 | 14/16 all, 10/12 free | 13/16 all, 9/12 free — worse |

**Root-cause attribution (rule 14: the worse/relocated fit is a discovered
bug, not a reason to revert).** The sub-SRMC ST_GAS band was masking a
CC_REGULAR/ST_GAS merit-order substitution error, not a level error: once
both classes clear at a comparable SRMC-grounded offer, the LP's real
tie-break (efficiency: CC HR ~7 vs ST_GAS HR ~10.6) sends the marginal MWh to
CC_REGULAR almost every hour, which is the physically correct merit order but
the wrong volume outcome given actuals — actual ST_GAS runs far more energy
than a pure-efficiency merit order predicts (2024: 12.4 TWh actual vs the
Manual-15-SOM finding elsewhere that legacy steam is "economically
challenged" and *should* under-run). This points at a real, unmodeled
structural driver keeping ST_GAS's actual volume up despite its poor
efficiency — candidates: reliability-must-run contracts / RMR designation for
specific legacy steam units (parallel to NYISO's LI floor), local
deliverability constraints that ST_GAS uniquely serves (zone-locked capacity
CC_REGULAR can't reach), or a per-plant heat-rate error understating specific
ST_GAS units' true competitiveness. **Not** attributable to: outages,
gas price, or the CT_CHP/CT_PEAKER fix (both bundles share those unchanged).

**Disposition: keeper stays `2026-07-05-pjm-77-ct-relfloor`. Neither probe is
promoted.** The re-grounding is directionally correct physics (rule 13 — no
non-CHP tranche should price below its own SRMC) but, scored in isolation, it
trades one C1/C8 miss for a different and slightly worse one, with no gain on
C2/C3/scarcity. Per rule 1, "never reject/revert a structurally-correct
mechanism because the residual didn't move" — but equally, promoting it here
would swap the keeper onto a NOT-YET that is not closer to CALIBRATED on any
hard criterion, so there is no promotion case yet. **Recommendation to
owner:** keep the re-grounding as the target end-state, but land it together
with (not before) a fix for the underlying ST_GAS-volume driver identified
above — the two root-cause issues opened below are the prerequisite work.
The C8 drag memo (`docs/handoffs/pjm-c8-drag-memo-2026-07.md` §6) anticipated
resolving the drag breach via this cycle's corrected denominator; that did
**not** materialize (share rose, not fell) — the memo's sequencing
recommendation is updated by this finding: the drag decision should not wait
on a re-grounding that itself doesn't clear C8.

**Registered:** `2026-07-06-pjm-79-srmc-baseline` (bundle
`pjm78_srmc_baseline`) and `2026-07-06-pjm-80-srmc-reground` (bundle
`pjm79_srmc_reground`), both PROBE-labeled, full 2023–2025 span. No zero-forcing
ablation twin (probes, not keeper candidates; rule 20's twin requirement
applies at promotion). Root-cause issues opened: #1483 (ST_GAS actual-volume
driver, structural, candidates above) and #1484 (C8 drag-share sensitivity to
the denominator, updates the open C8 drag memo). Dashboard retention pruned
to top-15 (dropped 7 oldest PJM sidecars: pjm-62…68; bundles kept on disk).

### 2026-07-06 — NYISO — L-11 wave-3: Zone-K LCR/TSL mechanism (#1345) + #1344 dynamic-requirement channel + v2 plant-rate backcast wiring (nyiso 53): PROBES, keeper stays nyiso 41

**Scope (lane L-11, gap register §5).** (1) Data-ask memo filed FIRST
(`docs/handoffs/nyiso-data-asks-2026-07.md`): LI/NYC LDC citygate/interruptible
delivered gas (G-13), the condition-varying downstate reserve-requirement series
(the #1344 blocker), Iroquois Z2 price + EBB flows, per-interface tie flows.
2023–2025 only; holdouts excluded by construction. (2) Issue #1344: the
condition-varying locational reserve-requirement CHANNEL is built
(`nyiso_dynamic_reserve_requirements`, default off; loader
`data/nyiso_reserve_requirements.py`; drop zone `data/raw/NYISO-AS/requirements/`)
— it threads a measured hourly requirement series into the in-LP co-opt
families' `(T,)` requirement and HARD-ERRORS when the series is absent, so the
flag can never quietly solve on the static values it claims to replace. The CC
econ_high markup stays 1.0 (never re-armed, rules 13/26). Rule-19 reconcile:
`nyiso_rcpf_enabled` (post-solve overlay) + `energy_reserve_coopt` is now a
hard error in `_nyiso_design` — the overlay is the co-opt-off comparator only.
LOYO scoring is the promotion gate ONCE the Ask-B series lands; until then the
mechanism is structurally inert by design (data-blocked, honest). (3) Issue
#1345: `nyiso_li_lcr_tsl` (default off) replaces the Long_Island 0.45
self-supply energy floor with the published Zone-K construction — the locality
import limit (325/275/275 MW, `data/raw/capacity-deliverability/nyiso/nyiso.csv`)
caps the NYC→Long_Island link in the HB14-21 design-condition window; the floor
skips LI via `exclude_zones` (rule 19, never stacked). Rule-14 boundary mapping
empirically reconciled: measured top-100-load-hour LI implied inflow (CEMS
gross gen + measured zonal load) 1,493/1,440/1,598 MW vs the mechanism's
in-window capability (TSL + 1,200 MW external ties) 1,525/1,475/1,475 MW — the
published construction lands within ~5% of the measured peak-hour boundary.

**NEW WIRING FIND (G-39/§9.6, G-29 class): `use_plant_emission_rates_v2` was
unreachable from every CAMPD-bins backcast.** The §9.6 ride-along assumed the
flip is dispatch-affecting for RGGI-priced NYISO; the first nyiso-53 v2-on/off
twin pair solved BYTE-IDENTICAL (same C3a, same C5a, same mean price to 3
decimals) because `apply_plant_emission_rates_v2` was called only from
`build_dispatch_fleet` (forecast path), never from `bins_to_fleet`. Fixed this
session (config-gated, default-off byte-identical, tested); the v2 arm was
re-solved on the fixed wiring. §9.6's "CAISO/NYISO/NEISO re-solve under v2"
sequencing should note the fix is a precondition it silently lacked.

**Probes (registered): `2026-07-06-nyiso-53-li-tsl` (nyiso-52 recipe + TSL +
v2) and `2026-07-06-nyiso53-v2off-twin` (same, v2 off — the §9.6
ablation−resolve attribution split).** Both NOT-YET (C6 unattested probes).
Headline vs nyiso-52 on the same scoring basis: **C1 flips to PASS** (the
standing 2024 ST_GAS −3.3 TWh HARD FAIL closes), **C3a −9.0/−10.9/−10.6%**
(52: −13.5/−14.7/−12.5) and **C3b 0.182/0.221/0.190** (52: 0.213/0.247/0.203)
— best NYISO price scores to date, from honest structure; C7 PASS holds; C3c
0/0/7 h unchanged (needs #1344). v2's isolated contribution (twin delta):
C1-2024 ST_GAS FAIL→PASS, C3a +2.4/+1.8/+0.4 pp, mean price +$0.61 — measured
plant rates re-splitting the gas merit order under RGGI (rule 10). **C8:** the
`nyiso_local_selfsupply` forcing channel is ELIMINATED and total floor-forced
CT energy falls to 1.49/1.56/1.45 TWh (vs 1.84/2.87/1.86 forced by the
selfsupply floor alone in the nyiso-48 C8-fail baseline) — the rule-20 number
moved DOWN and nothing re-hides it — but the share-of-class rises to
92.7/86.7/56.6% because CT economic energy collapses without reserve-scarcity
price formation: idle-peaker phantom reserve, the downstate handoff's confirmed
root cause, now nakedly visible instead of floor-masked. CT_PEAKER volume
under-runs (1.60/1.79/2.57 vs actual 2.26/2.13/2.84) for the same reason.

**Keeper recommendation (owner decision, no in-session swap):** nyiso-53
supersedes nyiso-52 as the recommended eventual keeper config — it is strictly
more structurally faithful (published TSL replaces the residual 0.45 scalar;
measured plant rates replace HR-derived estimates; selfsupply forcing channel
deleted) and better on C1/C3a/C3b/C8-ST. The live keeper stays
`2026-07-03-nyiso-41-hub-prices` (STALE-VS-HEAD, G-13): C8-CT share and C3c
remain hard-blocked on #1344 (Ask-B data) and the CT offer level on the Ask-A
delivered-fuel intake. Retention: pruned `2026-07-03-nyiso-40-truedate-gas`
and `2026-07-03-nyiso-42-band-deleak` (top-15).

### 2026-07-06 — CAISO — L-10 wave-3: G-11 drift bisect CLOSED, G-14 bundle corrected, G-15 zero-drag ablation (caiso 56): PROBE, keeper stays caiso 51

**Goal (gap register §3.2 G-11/G-14/G-15, issue #1346, lane L-10).** (1) Bisect the caiso-51
keeper-reproducibility drift on post-07-03 main; (2) adjudicate the caiso-51 bundle's
meta/run_config self-disagreement; (3) write the CT-drag D-8 closure design and run the one
permitted zero-drag ablation probe. NO keeper swap (owner decision); nothing tuned against a
residual.

**G-11 — drift DIAGNOSED: PR #1279 (the caiso-52 CT-floor scrub), a legitimate rule-17/18/19
correction, not a regression.** No new bisect solves were needed — the registered run chain
already brackets every post-07-03 merge: caiso-51 (pre-scrub `2b2f91f`, CT 3.474/3.383/2.843
TWh, C8 32.6/29.0/27.5%) → caiso-52 (keeper flags + scrub, CT 1.97/1.56/1.15) → caiso-r1-baseline
(07-05 main, CT 2.122/1.729/1.242, C8 59.8/66.7/71.5%) → caiso-55 (HEAD replay `455ed9f`,
CT 2.12/1.73/1.30). The scrub's three commits: `916e8cb` (RA economic bridge gated on
min-down ≥ 4 h physics — kills the overnight CT hold), `77c4f67` (CT netload limbs windowed
h15-21), `b3a9036` (limbs retired, `enabled=False`). The committed keeper carried TWO
since-removed off-merit CT engines (all-24h limbs + overnight economic bridge) whose energy its
own D-2 could not fully see (the P2 RA-bridge floor is not reconstructable — "lower bounds";
the D-1 off-peak CV 0.011-0.025 flat-floor signature was the tell). **Input-hash check clears
the data-side suspects** (#1346 named CAMPD intake batches / fuel curation / the fleet.py
curated-bin merge): every run in the chain — and the caiso-56 probe solved this session in a
fresh container — carries byte-identical content-hashed shared inputs (`eia930-3697b3115384`,
`eia923-b95fbbedf1f2`, `campd-cceb6c13d8f9`). Code, not data. The only fleet.py change in
`455ed9f..3b31193` is the confirmed-exits backlog application (forecast-gated, backcast-inert).
**Correction to the 2026-07-05 caiso-55 entry:** it attributes the residual +0.15 TWh/yr deltas
to a seam re-grounding commit "`21f8845`" — that SHA does not exist; the actual seam re-ground
commit `954c8a8` (capdel CLI flag + measured-hub 2023 gap-fill) is *inside* PR #1276, i.e. part
of the keeper itself; the intervening merges are the 07-04/05 scalar/offer work (#1283/#1284,
incl. `0c6c833`) and the InterchangeSpec unification (`3fb6282`). **Disposition:** the scrub
stays (do not revert); the keeper's committed dashboard numbers are pre-scrub and unreproducible
on any post-scrub main — disclosed on the caiso-51 sidecar; **a keeper re-solve/re-gate under
scrubbed main is owed to the owner**, and per the merged L-8 memo
(`emissions-co2-rate-plan-2026-07.md` §9.6) that re-solve carries
`use_plant_emission_rates_v2=True` (CAISO is carbon-priced → the flip is dispatch-affecting)
with an optional v2-off ablation twin for attribution — never a standalone re-solve wave for
the flag alone. No clean keeper candidate exists today: every post-scrub arm FAILs rule-20 C8
(59-71%) until the evening-merit structure lands. Diagnosis posted to issue #1346.

**G-14 — caiso-51 bundle corrected: meta.json was the truth.** The keeper's own solve log is
decisive — `capacity_deliverability_limits` set the seam import cap to 16,055/16,452/16,148 MW
(published MIC replacing the fitted 7,500 MW WECC fallback) and `caiso_perhub_firm_base` held
firm tranches at contract cost, all three years. `run_config.json`'s `scenario_config` recorded
`false` for both because the keeper-era harness `recorded_cfg` block never threaded those two
kwargs (the solve honored them via `run_year` kwargs; the writer serialized dataclass defaults).
Corrected with a `post_hoc_corrections` record in the file (commit cites the log lines).
Harness note for the orchestrator/L-2 owners: `capacity_deliverability_limits` recording was
since fixed on main, but **`caiso_perhub_firm_base` is still not threaded into `recorded_cfg`
at HEAD** — any new run with that flag will repeat the G-14 under-report until fixed.

**G-15 — CT-drag D-8 closure design + zero-drag ablation (caiso 56, PROBE,
`results/calibration/caiso56_zerodrag_ablation`, 2023-25, registered
`2026-07-06-caiso-56-zero-drag`).** Design: `docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md`
— the drag's rule-17 credentials are intact (driver: CAMPD CT evening CF regressed on EIA-930
net-load, local-RA duck-curve commitment; window h15-21 matched derivation↔application; forward
story: net-load regenerates from load forecast + VRE build), rule-19 is clean (sole CT floor;
limbs retired + code-deduped, bridge physics-gated), but the +18.1% LOYO slope drift
(train 0.01064 vs full 0.00901; 2025 floor prediction +32.2%) is structural: the drag carries
~all of a class whose real evening commitment is ramp + locational — invisible to the
energy-only zonal LP (`FINDING-caiso-evening-merit-2026-07-04.md`). Closure = the already-built,
gated-off `ramp_limits` + `local_capacity_constraints` mechanisms
(`docs/ramp-locational-design-2026-07.md`), whose decision rule is adopted as the D-8 closure
criterion; on pass the drag is REMOVED (rule 26), on fail it stays and G-15 stays open. **Probe
result (single delta `ct_netload_drag=false` on the keeper config at HEAD, v2 off as the keeper
ran):** scored-pass CT_PEAKER 0.83/0.55/0.39 TWh vs drag-ON 2.12/1.73/1.30 (measured
3.08/3.30/1.65) — the ablation delta 1.29/1.18/0.91 TWh matches caiso-55's D-2 drag attribution
(1.26/1.15/0.90) within ~2%, a clean D-3 validation of the D-2 accounting. Without the drag the
class collapses to ~25% of actual (the pure merit tail); D-2 PASSES (CT forced 0.8/1.4/0.03%,
only `ra_mustoffer_bridge` remains); C3a +21.4/+36.3/+43.7% (the drag barely moves mean LMP);
2023 >$200 tail 479 h vs 21 actual (the floor was suppressing artificial evening scarcity the
model now prices — C3c honest-fail, recorded not judged). **Keeper stays
`2026-07-03-caiso-51-firm-base`** (recommendation only; `keepers.json` untouched). Dashboard
retention pruned to top-15 (dropped 2026-07-01-caiso-46-capdel-probe sidecar+payload; bundle
kept). Quarantine gate `audit_keepers.py --check` green before and after (0 failures).
### 2026-07-06 — NEISO — winter-fuel Component B (winter fuel-security must-run) full-span A+B probe: NEGATIVE, keeper stays neiso-48

**Goal (G-24, winter-fuel plan `docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md`
Component B).** Build the winter fuel-security must-run limb — the mechanism hypothesized to be
the single missing structure behind NEISO's winter-fuel caveat family (C3c tail, C5b storage,
C1 COAL/ST_GAS under-run) — and solve the full-span A+B probe scored vs the neiso-48 keeper.
Component A's probes (`neiso-inventorycap-inert`, `neiso-dailybasis-oil-underrun`, 2026-07-04)
were the design inputs: the inventory cap was inert because a price-taking dispatch barely
commits the fuel-secure fleet, so oil burn never reaches the seasonal budget. Component B was to
supply that commitment.

**Mechanism built (`winter_fuel_inventory.apply_winter_fuelsec_mustrun`, GATED
`neiso_winter_fuel_mustrun`, default off).** Rule-17 statement: (a) DRIVER — ISO-NE winter
fuel-security posture (Winter Reliability Program FERC ER14-2407 → Inventoried Energy Program
ER19-1428 → OFSA operational posture), an external program that retains/postures fuel-secure
steam for winter energy security beyond energy economics. (b) HOURS — winter months (Nov–Mar,
OFSA horizon) AND cold days (zone daily TMIN < −7 °C, the NERC cold-weather forced-outage
onset), all 24 h of a flagged cold day, multi-day events bridged 48 h; never summer/shoulder,
never mild winter days. (c) FORWARD — calendar season + pinned/forecast TMIN + physical
boiler-turndown depth, all forward-derivable. **Rule 19 reconcile:** REPLACES the disabled
COAL/ST_GAS `tmin` cold-limb reliability floors (`reliability_floor_coeffs_NEISO.csv`,
`enabled=False` since the 2026-06-30 rebuild disabled them for thin cold-day sample, n=7–8) —
Component B re-grounds the same phenomenon on the program posture rather than a fitted
temperature ρ; the tmin limbs stay disabled, not re-enabled alongside. D-2 confirmed
COAL/ST_GAS carried **zero** forced energy before, so nothing was stacked. Depth =
`commit_frac (1.0) × min_stable_pct (0.40, physical subcritical steam turndown)`, on-registry
ScenarioConfig, never the residual (rules 1/24). New `MECH_WINTER_FUELSEC` for D-2 attribution
(non-exempt merchant floor, ablated in the zero-forcing twin).

**Result — the four winter-fuel caveats DO NOT close (NEGATIVE).** Probe
`2026-07-06-neiso-wfuelsec-ab-v2` (Component A + B + `use_plant_emission_rates_v2`), scored vs
neiso-48:

| metric | keeper neiso-48 | A+B probe | actual | closed? |
|---|---|---|---|---|
| C1 COAL TWh (23/24/25) | 0.058/0.113/0.234 | 0.062/0.126/0.218 | 0.181/0.238/0.271 | **no** |
| C3c h > $300 | 0/0/0 | 0/0/0 | 15/8/20 | **no** |
| C5b PS+batt discharge (25) | 1.05 | 0.91 | 2.08 | **no** |
| oil-fuel TWh (23/24/25) | 0.35/0.23/1.47 | 0.35/0.23/1.54 | 0.32/0.37/1.24 | ~unchanged |

**Root cause of the negative result (the real finding).** The winter commitment floor is
**non-binding**: the NEISO fuel-secure fleet is tiny (~105 MW coal / 8 units, ~74 MW ST_GAS)
and *already runs above min-stable on cold days economically* (coal is cheap when winter gas is
dear), so the floor adds almost nothing — D-2 coal forced share ≈ 0, ST_GAS 0.274/0/0. Because
the fleet already burns on cold days, Component B raises no incremental oil draw, so Component
A's inventory budget still never binds and the C3c scarcity tail stays flat at the oil-parity
cap (max zonal P 222/199/258). **This REFUTES the plan's hypothesis that a missing winter
commitment is the mechanism behind C1/C3c/C5b.** The under-run is a fleet-capacity/availability
magnitude gap (the model's coal+steam fleet is small, and coal at 100% CF caps near the actual)
plus a scarcity-price-formation gap the inventory budget never reaches — not a commitment gap.

**Rule-20 forced-energy budget (checked explicitly — a must-run limb is where forced energy can
silently blow the cap).** PASSES: winter_fuelsec forced share ST_GAS 0.274 (2023) / 0 / 0
(< 0.30 cap), coal ≈ 0 (non-binding), CT_PEAKER 0. D-2 PASS, D-4 off-window PASS. D-1 ST_GAS
diurnal shape still FAILS (pre-existing, unchanged — the separate steam-gas shape root cause).
Overall verdict NOT-YET (unchanged from neiso-48).

**`use_plant_emission_rates_v2` is DISPATCH-INERT for NEISO.** The v2-off attribution twin
`2026-07-06-neiso-wfuelsec-ab-v2off` (per emissions-co2-rate-plan §9.6) is **byte-identical** to
the v2-on probe on price (dwLMP 31.97/36.08/62.88), fuel mix, storage and CO2 — the measured
RGGI carbon price × the v2 per-plant rate delta shifts no NEISO merit order and moves no scored
metric. The memo's "can shift" for RGGI ISOs does not materialize here; recorded so a future
global v2 flip (memo step 3) knows NEISO re-scored clean.

**Keeper recommendation (to the owner — no swap in-session).** **Keeper stays
`2026-07-05-neiso-48-ct-floor`.** Component B is structurally faithful (real ISO-NE posture,
rule-19-reconciled, rule-20-passing, no residual tuning) and stays in the codebase **default-off**
per rule 1, but it is **not keeper-eligible**: it does not close its target caveats and changes
essentially nothing (the fleet it targets already runs). **NEISO does NOT move to
caveat-budget-passing** — the two hard caveats (C1 CC_REGULAR, C2 2025 sysvol, both measurement/
EIA-930-fold-in issues per neiso-43) and the winter-fuel soft family are all unchanged. The next
NEISO root cause is the fleet-capacity/availability of the coal+steam fleet and the winter
scarcity-price formation (C3c) — NOT more winter-commitment tuning, and rule 1 forbids cranking
the floor to force the coal number. Holdouts (2022, H1-2026) remain fully quarantined (rule 22);
the calibration-complete declaration is the owner's.

Registered both full-span runs (rule 15): `2026-07-06-neiso-wfuelsec-ab-v2` (probe) and
`2026-07-06-neiso-wfuelsec-ab-v2off` (v2-off attribution twin). Dashboard retention pruned to
top-15 (dropped the 12 oldest June/early-July NEISO sidecars: neiso-30…44-band-deleak; bundles
kept on disk). Reproduce: `scripts/replay_keeper.py results/calibration/neiso_ctscrub --set
neiso_winter_fuel_inventory=true --set neiso_winter_fuel_mustrun=true --set
use_plant_emission_rates_v2=true --out-dir results/calibration/neiso_wfuelsec_ab_v2`.

### 2026-07-05 — CAISO — W3-P2 CT-floor scrub HEAD verification + red-flag closeout (caiso 55): PROBE, keeper stays caiso 51

**Goal (W3-P2, red-flag `caiso-52-ct-scrub`, audit `docs/model-legitimacy-audit-2026-07.md` §1).**
Execute/close the open CAISO CT-floor forcing scrub with rule-17/23 discipline: D-2 attribution over
the caiso-51 keeper config **at HEAD**, remove any floor binding where its driver says the class is
offline, check the rule-20 forced-energy budget, and disposition the red flag. Do NOT swap keepers;
do NOT touch the C-5/C-14/C-16 seam scalars or any CAISO offer curve (rule 26).

**Finding: the scrub was already merged (2026-07-03, caiso-52 lineage) — this session verifies it holds
at HEAD and closes the flagged "keeper-reproducibility drift."** The audit's three stacked CAISO CT
forcing engines are dismantled, defended at **three independent code layers**:
1. **All-24h reliability-floor CT limbs — windowed then disabled.** `reliability_floor_coeffs_CAISO.csv`
   CT_PEAKER/CT_CHP netload limbs carry `start_hour/end_hour = 15/21`, and every row is `enabled=False`
   (loader forces `enabled = enabled AND NOT r1_disabled`, `iso_configs.py:1012`). The all-24h day gate
   (`np.repeat(day_flagged,24)`) can no longer bind.
2. **Rule-19 dedup in code.** `drop_drag_owned_reliability_specs` (`iso_configs.py:1059`,
   `_DRAG_OWNED_RELIABILITY_CLASS = {ct_netload_drag: CT_PEAKER, gas_st_netload_drag: ST_GAS}`) drops
   every CT_PEAKER reliability limb whenever `ct_netload_drag` is active — so even a re-enabled limb
   cannot stack with the drag ("dropped 3 drag-owned limb(s)" in the solve log).
3. **Bridge eligibility by physics.** The economic RA startup bridge gates on
   `min_down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS` (`constants.py:120 = 4.0`; `commitment.py:816-820`,
   rule 17). Fast-start CTs (min-down 1 h) are never economically bridged overnight; only a physical
   `gap < min_down` bridge remains (never fires for a 1-h-min-down CT).

**HEAD verification (caiso 55, `results/calibration/caiso55_ctscrub_head`, byte-faithful
`replay_keeper.py` of the caiso-51 keeper meta.json at 2026-07-05 main, all 3 years).** Config parity
confirmed vs caiso-51 (`reliability_floor=True`, `ct_netload_drag=True` slope 0.00901 / int −0.1124 /
cap 0.36, `caiso_ra_startup_bridge=True`, `caiso_ra_min_load_frac=0.26`). One recorded-flag difference,
behaviourally inert: `capacity_deliverability_limits` resolves `True` at HEAD (the keeper's meta carries
the `--capacity-deliverability-limits` flag) but **no-ops** — the clean CAISO partition is still absent
("Returning no limits"), so the published MIC seam limit is carried by `caiso_per_hub_intertie`
firm-base in both, and dispatch is faithful to caiso-51.

D-2 forced-energy attribution over the scrubbed keeper config **at HEAD**:

| year | CT_PEAKER TWh | ct_netload_drag (share) | RA-bridge (share) | D-2 verdict | D-4 off-window |
|---|---|---|---|---|---|
| 2023 | 2.12 | 1.261 (59.4%) | 0.007 (0.3%) | FAIL (59.7% > 10%) | 0.0% PASS |
| 2024 | 1.73 | 1.146 (66.3%) | 0.007 (0.4%) | FAIL (66.7% > 10%) | 0.0% PASS |
| 2025 | 1.30 | 0.901 (69.4%) | 0.000 (0.0%) | FAIL (69.4% > 10%) | 0.0% PASS |

CT forcing is now a **single windowed mechanism** (the audit-sanctioned net-load drag, DwC in §2), with
the RA bridge's CT share collapsed to <0.4% (was the overnight-bridge era). D-1: the flat-floor signature
is gone — CT off-peak CV ratio 0.000 (caiso-42) → 3.15/3.52/3.05, profile r 0.883/0.850/0.699 (2025
r<0.8 is the small noisy fleet, pre-existing); D-4 off-window 62–66% (caiso-42) → **0% all years**.
D-9/D-10 PASS.

**"Undiagnosed drift" resolved — it is the scrub effect, not a bug.** The r1 note's concern (CT
~3.4→~1.7 TWh, forced share 60–71% vs the pre-scrub keeper's ~27–33%) is exactly the scrub removing the
~1.2 TWh flat overnight floor. caiso-55 reproduces the committed caiso-52 scrub (CT 2.12/1.73/1.30 vs
1.97/1.56/1.15 TWh; forced share slightly *lower* at HEAD as marginally more CT clears). The residual
CT/price deltas vs caiso-52 (CT +~0.15 TWh/yr; 2025 avg LMP 44.5 vs 45.6) trace to the intervening
merged C-5/C-14/C-16 seam re-grounding (`21f8845`) + InterchangeSpec unification (`3fb6282`) — **not**
the CT scrub and **not** touched here (rule 26). The caiso-51 keeper's committed dashboard numbers are
pre-scrub and no longer reproducible on scrubbed main — a keeper-refresh item (recommendation only).

**Disposition — the caiso-52 red flag is CLOSED at the mechanism level.** Nothing remains to scrub: the
only surviving CT floor (net-load drag) has a defensible driver (evening net-load ramp, regressed from
CAMPD 2023-25), a window (h15-21), a forward story, and D-4-clean off-window binding (rule 16-17). Every
floor that bound where its driver said CTs were offline (all-24h limbs, overnight startup bridge) is
removed. **Open (NOT closable by a floor scrub, rule 1 — do NOT re-floor):**
1. **D-2 CT forced share 60/67/69% > 10%** — the drag is ~all of a small CT total because the P1
   energy-only zonal merit order prices CTs out of the evening ramp (CT HR ~10.4 vs CC ~7.6; CC's *peak*
   band undercuts CT's *committed* band). This is the evening-merit structural gap
   (`results/calibration/FINDING-caiso-evening-merit-2026-07-04.md`), needing CC ramp/min-up-down
   commitment + sub-zonal LA-basin transmission — a large structural build, out of scope here.
2. **D-5 parity** — `caiso_ra_mustoffer` is built only in `run_calibration.py`, not `runner.py`
   (w2-caiso-ra-p2 wiring gap); pre-existing, unchanged.
3. **ST_GAS D-1 shape** (2024 r 0.013 / 2025 r −0.275) — pre-existing, separate root cause.

**Keeper-candidate? No.** The scrubbed config carries the disclosed C3a evening-scarcity regressions
(caiso-52: +21.1/+36.5/+43.9% vs caiso-51 +19.6/+34.9/+41.6%) and still fails D-2; there is no clean
keeper-candidate until the evening-merit build lands. **Keeper stays `2026-07-03-caiso-51-firm-base`**
(recommendation only; `keepers.json` untouched). Registered PROBE `2026-07-05-caiso-55-ct-scrub`
(NOT-YET); dashboard retention pruned to top-15 (dropped 07-01 caiso-42/43/44/45 sidecars; bundles
kept). Audit §1 follow-up recorded in `docs/model-legitimacy-audit-2026-07.md`.

### 2026-07-05 — W5 keeper re-gate sweep: E7 adjudication for CAISO / PJM / NYISO / NEISO (PJM + NEISO promoted; CAISO + NYISO keepers stay)

`audit_keepers --check` flagged E7 ("a newer run exists") on four ISOs. Each
newer run was adjudicated against CLAUDE.md rules 1/11/15/16/17-26 — the keeper
is the most structurally faithful run, never the lowest-MAE one, and a rejected
promotion is recorded, not silently skipped. ERCOT (ercot40 WS-A probe; ercot32
stays keeper, logged 2026-07-05) and MISO (E9 twin owned by W4-6) were out of
scope for this sweep.

**PJM — PROMOTED: `2026-07-05-pjm-77-ct-relfloor` replaces
`2026-07-03-pjm-76-outage-fix`.** pjm-77 is the pjm-76 recipe VERBATIM on the
rule-19 reconcile (`drop_drag_owned_reliability_specs`): the two all-24h
CT_PEAKER reliability limbs (EMAAC, West_APS) are dropped because the CT
net-load drag already owns that class's commitment — the limbs' only marginal
contribution was overnight on hot days, where measured CAMPD pure-play CT CF is
0.0165 (vs 0.376 at the afternoon peak), i.e. a floor binding where its own
driver says the class is offline (rule 17, a bug by definition). Clears the
deciding D-4 failure (97-99.7 % off-window, all years) by removing a ~0.12 TWh
overnight phantom; no fitted parameter changed. pjm-77 also carries the
burndown's meta-gap fix (persist `ct_netload_drag` in `meta.json`), giving PJM
its first accurate legitimacy diagnostics — which honestly surface two
pre-existing open items the gap had hidden (drag D-2 12.1 % CT forced energy in
2024; CT_CHP D-4 on its own all-24h cooling limb). Kept per rule 14: accurate
diagnostics stay even though they reveal more failures. Verdict still NOT-YET.
Full evidence: `docs/FINDING-pjm-burndown-2026-07.md`. D-3 zero-forcing
ablation twin solved with the exact pjm-77 config/span and registered
(`2026-07-05-pjm-77-ct-relfloor-ablation`, rule 20); DOF ledger present in the
bundle attestation (5 entries).

**NEISO — PROMOTED: `2026-07-05-neiso-48-ct-floor` replaces
`2026-07-03-neiso-47-fast-start`.** The same disease and the same class of fix
as pjm-77 / caiso-52: the neiso-47 recipe with the two all-24h CT_PEAKER tmax
reliability limbs (Boston, Connecticut) scrubbed — a zero-parameter mechanism
deletion (rules 17/18: fast-start CTs, min-down ≤ 2 h / startup < $30/MW, are
never day-ahead committed at a floor). The registered same-recipe A/B control
(`2026-07-05-neiso-48-base-control`, bundle `neiso_ctbase`) documents the
pre-scrub failing state: D-4 off-window 72-76 %, C8 CT_PEAKER forced share
0.47/0.78/0.47 → 0.00 all years after the scrub; C7 off-peak CV ratio
0.65/0.63/0.59 → 0.76/0.86/0.79. Disclosed cost (rule 1, not to be won back
with a floor): CT_PEAKER grid volume falls to 0.010/0.021/0.099 TWh, absorbed
by marginal CC_REGULAR at the same price (dw-LMP +$0.02-0.06). This resolves
exactly the C7/C8 CT failures the 2026-07-04 re-gate flagged on neiso-47, the
way that re-gate note demanded (fix the floor, never re-tune to win C7/C8
back). Remaining open: ST_GAS diurnal shape (pre-existing, unchanged — next
NEISO root cause). Verdict still NOT-YET. D-3 zero-forcing ablation twin solved
with the exact neiso-48 config/span and registered
(`2026-07-05-neiso-48-ct-floor-ablation`, rule 20); DOF ledger present (5
entries).

**CAISO — NOT PROMOTED: `2026-07-03-caiso-51-firm-base` stays keeper;
`2026-07-05-caiso-r1-signflip-off` is a probe, not a candidate.** The r1 pair
(`caiso-r1-baseline-limb` limb-ON / `caiso-r1-signflip-off` limb-OFF) is the
B-LIMB-1 same-env A/B isolating the R1 disablement of the unidentified
sign-flip SP15/CC_REGULAR tmax limb (D-8: train ρ +0.69 → holdout −0.10). The
A/B proved the limb NON-BINDING (CC_REGULAR Δ ≤ 0.018 TWh; price/CO2/forced
share identical), and the disablement itself already shipped in source
(`r1_disabled=True` in `reliability_floor_coeffs_CAISO.csv`, commit 8e741d8) —
so promoting the probe would add no structure the keeper config doesn't
already carry forward. Decisive against promotion: both r1 runs inherit an
UNDIAGNOSED keeper-reproducibility drift on current main — CT_PEAKER energy
roughly halved (~1.7 vs ~3.4 TWh) and C8 forced share 60-71 % vs the committed
bundle's 27-33 % — i.e. the probe run is structurally WORSE on the rule-19
forced-energy budget for reasons unrelated to the probed change. That drift is
an open root-cause item for the CAISO owner (flagged in the
`caiso-r1-baseline-limb` sidecar); swapping the keeper onto it would launder an
unexplained regression into keeper status. E7 on CAISO is a documented state
(the ercot40 pattern) until the drift is root-caused.

**NYISO — NOT PROMOTED: `2026-07-03-nyiso-41-hub-prices` stays keeper;
`2026-07-05-nyiso-47-ccdeleak-ablation` is a D-3 ablation twin, definitionally
never a candidate.** The E7 pointer names the twin only because it is the
lexically-latest same-day sidecar; the actual newest run,
`2026-07-05-nyiso-47-ccdeleak`, is the B-NYI-1 scalar-remediation PROBE whose
registration entry (2026-07-05, below) already recorded "keeper stays 41": its
de-leaked CC econ band carries an EXPECTED, disclosed C3a/price regression
whose root cause is the missing NYISO reserve/scarcity price formation (issue
#1344), an open structural item — recording the regression and keeping the
keeper is the rule-1 outcome. Re-affirmed here so the E7 warning is a
documented state. `audit_keepers` E7 was also fixed this session to stop
counting `*-ablation` twins as "newer runs" (a twin is a diagnostic shadow of
its parent, rule 20), so NYISO's E7 pointer now names the probe, not the twin.

Bookkeeping: `keepers.json` swapped for PJM/NEISO; pjm-76 and neiso-47 removed
from `E9_ABLATION_TWIN_GRANDFATHER` (dead entries once demoted, per the list's
own contract); `build_status.py` re-run; keeper-auditor pass on the swapped
keepers. E7 count 5 → 3 (ERCOT, CAISO, NYISO — each a documented state above
or in the ercot40 entry); no new audit failures (MISO's E9 pre-exists, owned
by W4-6).

### 2026-07-05 — ERCOT — C3b/C3c price-shape attribution + measured offer-wall ladder (ercot 33): PROBE rejected, keeper stays ercot 32

**Goal.** Decompose the standing C3b (shape) / C3c (tail) fails by month×hour and
mechanism — attribute, don't guess — then fix only what the attribution indicts
(published/measured grounding only; ORDC params tariff-cited and untouched per
rule 26). Full write-up: `docs/FINDING-ercot-priceshape-2026-07.md`.

**Attribution (the actual 2023 >$200 hour list vs the model in the SAME hours,
DST-aware).** (a) ORDC/reserve underpricing EXONERATED: the actual tail is
energy-offer-carried (SCED lambda > $200 in 175/181 h; adder-carried ≤ 6 h/yr all
three years; PRC 4.7–6.2 GW, above the knee — the co-opt's ORDC-on-measured-supply
already matches the small actual adders). (b) congestion EXONERATED at the hub
level (~3 h; zonal spread rides on top of a systemwide >$200 lambda). (c) is
real but is *online-capability* tightness, quantified: in the 105 missed hours
the model holds ~10.9 GW of thermal headroom vs measured RTOLCAP 7.7 GW /
PRC 5.7 GW — ~3.2 GW of phantom sub-$200 spare (P1 perfect commitment +
sub-2-day forced outages), so its dual sits at $43–51 where SCED sat at $600+.
(d) INDICTED as the fixable piece: the peak band prices at the class p50 of the
measured 60d-DAM top-of-curve distribution, deleting the measured scarcity wall
(p70/p90 = $266–$2,800+; the model's stack tops at ~$84–150). C3b-2023 IS
C3c-2023 (Aug −62 carries the NRMSE); C3b-2024 is the separate documented DAM-AS
overlay DA-boundary premium (Jan +18.2 / May +9.4).

**Probe (ercot 33 offer wall, `2026-07-05-ercot33-offer-wall`, single delta vs
keeper).** Measured peak-band quantile ladder (capacity-weighted p10/30/50/70/90
per gas class, rungs p50-clamped from below, top rung HCAP-clamped;
`derive_dam_offer_hrmults.py --peak-ladder`, opt-in artifact
`offer_curve_dam_hrmults_ladder.json`; fleet splits each peak tranche into 5
rungs). Result: the scarcity year improves exactly as attributed — 2023 C3a
flips to PASS (−2.9%), C3b 0.375→0.336 (in-container basis), >$500 deep tail
64→75 h (actual 104), C8 forced-energy flips to PASS — but the >$200 count
barely moves (the wall deepens hours the co-opt already priced; the 105 missed
mid-merit hours stay missed), mild years lift broadly (2025 C3a flips to FAIL
+7.7%), and the P0→P1 startup-amortization CT↔ST coupling flips ~8 TWh of
COMMITTED/econ energy off the measured allocation (CT_PEAKER 10.4 vs
CAMPD-measured ~6.4 TWh; ST_GAS 6.3 vs ~16.8) → C1/C2/C5c worsen. An unclamped
first arm (same session, superseded, deleted) additionally proved the sub-p50
rungs are wrong: no tail gain, same CT↔ST crater.

**Verdict (rule #1 both directions).** The wall mechanism is real market
structure the keeper lacks, but the *static* ladder misstates its measured
conditionality (~240 MW ≥$200 in an average hour vs 1.3–2.7 GW in
anticipated-tight hours) and moves measured volumes; a run that improves price
residuals by moving 8 TWh off the measured dispatch is NOT structurally
superior. REJECTED; keeper stays `2026-07-03-ercot32-ordc-total-rtolcap`.

**Filed (the honest C3 structural conclusion).** (1) condition-responsive
measured offer surface (derive the ladder per anticipated-tightness day-state;
model selects by its own net-load state — forward-derivable, rule-13-admissible;
the ladder machinery from this session is the substrate, inert by default);
(2) online-capability structure — commitment thinness (shelved P2 family) and/or
weather-correlated sub-2-day outages for the 3.2 GW phantom-spare wedge;
(3) CT↔ST startup-amortization fragility → D-8 thread (also observed: the
ercot32 keeper is not container-reproducible on current main — byte-faithful
replay lands CC_REGULAR 145.4 vs committed 133.2 TWh, 2024 C3a +2.3% vs
committed +9.1%; measured-GTC presence ruled out in-container).

### 2026-07-05 — ERCOT — NP6 HSL 2024/25 intake attempt: BLOCKED (data-needed, not a keeper/probe)

**Goal.** WS-E of `docs/handoffs/ercot-as-coopt-plan-2026-07.md` / G7's P4
remainder: intake published ERCOT NP4-732/737 wind+solar HSL reports for
2024/2025 so `renewables.hsl_potential_mw` stops falling back to the
reference-curtailment-rate gross-up for those years. **Result: blocked on
ERCOT account credentials, no run performed.**

Legacy `mis.ercot.com/misapp/GetReports.do` now 302s every report — including
"Public"-classified NP4-732-CD — to a SiteMinder market-participant login. The
replacement Data Access Portal (`data.ercot.com`/`api.ercot.com`) is
network-reachable (no proxy-level 403, unlike the prior NP6-576-ER attempts)
but every API call returns `401 missing subscription key`; obtaining one
requires an interactive `apiexplorer.ercot.com` account registration this
session cannot complete. Also checked and empty: the 60-Day SCED Disclosure
product (NP3-965-ER, same gate) and the UMass `nodal-curtailment-analysis`
GitHub dataset (2023 fallback source; cloned `main`, no 2024/2025 files
exist upstream). Full log: `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`;
drop-zone placeholder `data/raw/ercot-hsl/np6/README.md`.

**No code or data changed.** `scripts/build_ercot_hsl.py` already ingests a
2024/2025 NP6 upload transparently once one lands (`np6/<year>/` drop zone);
`hsl_potential_mw` / `_forecast_uncurtailed_cf` (G7) continue supplying the
forward-admissible gross-up for ERCOT 2024/25 unchanged. No modeled-vs-reported
curtailment diagnostic or AS-forward-driver delta to report — nothing new was
solved. Not a keeper or a probe; a data-availability dead end pending
credentials, per the plan's egress caveat.

### 2026-07-04 — NEISO — winter-fuel Component A probe pair: daily AGT basis closes the oil under-run; inventory cap INERT (keeper unchanged)

*(Entry written 2026-07-06 as the U-01 closure — the two probes were registered on the
dashboard in-session on 2026-07-04 per rule 15, but this log entry was missed; gap register
`docs/gap-register-2026-07.md` §3.8 U-01. Reconstructed from the committed bundles
(`meta.json`/`run_config.json`, git_sha `bc26e6a`, both solved 2026-07-04T17:07) and the
registry sidecars — no re-run.)*

**Goal (winter-fuel plan, `docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md`
Component A).** First LP exercise of the seasonal (Nov–Mar) oil-burn inventory budget
(`winter_fuel_inventory.py` + `dispatch.py:_build_oil_budget_rows`, GATED
`neiso_winter_fuel_inventory` default off): one pooled fleet row per winter month, budget =
WRP-low 2.8 M bbl start-fill + 2 refills/season amortized monthly, MMBtu-weighted
(`HR[g]·P[g,t]`), scope = oil-primary units + the dual-fuel gas units' oil limb gated to
exogenous oil-switch hours. All inputs forward-derivable capacity/logistics quantities
(OFSA/WRP; `docs/multi-iso/neiso-winter-fuel-data-audit.md`), never measured burn/receipts —
the admissible replacement for the rejected neiso-40 F923-receipts budget.

**A/B pair (single-flag delta, config otherwise identical; full span 2023–2025, one bundle
each, P1+P2):**

- **`2026-07-04-neiso-dailybasis-oil-underrun`** (bundle `neiso-daily-basis-a-off`) —
  measured daily Algonquin-Citygate gas basis (`gas_hub_basis_daily`, mean-preserving) ON,
  inventory budget OFF. This is the Component-A ablation twin AND a finding in its own
  right: **the daily basis closes the winter oil under-run endogenously** — model oil
  0.35/0.23/1.47 TWh (2023/24/25) vs EIA-930 0.32/0.37/1.24, where the monthly-basis keeper
  ran ~0/~0/0.04. Daily basis is an admissible measured delivered-fuel input (rule 13);
  annual gas volumes unchanged. Price still caps at dual-fuel oil parity (~$258); 0 h >$300
  all years — the C3c scarcity tail is NOT a fuel-pricing question.
- **`2026-07-04-neiso-inventorycap-inert-probe`** (bundle `neiso-daily-basis-a-low`) — same
  config + `neiso_winter_fuel_inventory=True` (start_fill 2.8 M bbl, the WRP low bound).
  **RESULT: byte-identical dispatch and prices to the twin — the cap is INERT.** Even the
  heaviest oil month (Jan-2025, 0.755 TWh oil) sits below the ~0.91 TWh/month budget. Not
  tuned to force binding (rule 1): the budget is what the WRP/OFSA logistics say it is; a
  smaller number would be a fitted answer. Negative result, registered per rule 15.

**Reading (design input for Component B).** The realized winter oil burn — now at the
measured level thanks to the daily basis — consumes only ~60–80% of one month's
logistics-derived budget even in the worst month, because the LP burns oil only in the
parity-switch hours of a *price-taking* dispatch. The real fleet's winter draw is larger
and lumpier: ISO-NE *commits* fuel-secure steam units (winter programs / Mystic-style
retention) ahead of cold snaps, burning stock the pure energy-economics dispatch never
touches. Component A alone therefore cannot bind, and cranking its budget down to force
binding is forbidden (rule 1). The mechanism that draws the stock — the winter
fuel-security commitment (Component B) — has to exist before the inventory constraint has
anything to ration. Keeper unchanged (`2026-07-03-neiso-47-fast-start` at the time; since
superseded by `2026-07-05-neiso-48-ct-floor`).

**U-01 (gap register §3.8) is CLOSED with this entry:** the probes WERE run to completion
and registered (sidecars + runs payloads + slim bundles committed 2026-07-04); the rule-15
breach was the missing log entry only, now written. Bundles verified complete against
probe-class peers (meta + run_config; payloads decode all 3 years).

### 2026-07-04 — NYISO — CT offer grounding: measured-run fast-start v3 + oil screen + DEC 227-3 (nyiso 45/46): PROBES, keeper stays nyiso 41

**Goal.** Ground the NYISO CT offer level — the repo-level blocker left by commit 0c6c833
("Kill cross-ISO leakage of ERCOT-fitted gas offer bands", open root cause "a NYISO-grounded
CT econ ramp") — with independently measured mechanisms only; no residual input.

**Mechanisms (all default-off, NYISO via CLI).** (1) *Fast-start amortization v3*
(`--tranche-startup-measured-runs`): simple-cycle CT tranches amortize the NREL start cost
over the CAMPD-measured median start-to-stop run length
(`scripts/derive_campd_ct_run_lengths.py`, pooled 2023–25; per-plant medians 2–9 h, class
fallback 4 h) as the horizon ceiling — P0 runs may only shorten it. Kills the v2 circularity
(too-cheap offers → long P0 blocks → ≈0 markup → self-disabling, the nyiso-44 finding).
(2) *Generator-level EIA-860 oil-primary screen* (`--oil-primary-bin-fuel` for non-ERCOT):
verified clean — every NYISO gas-CT bin is NG-primary at the generator level (KER/DFO units
already load as raw oil units), so kerosene mispricing is NOT the over-run; ERCOT keeps its
registry screen byte-identical. (3) *NYSDEC 227-3 peaker-rule availability overlay*
(`--nysdec-peaker-rule`, nyiso-46): curated unit-level ozone-season compliance windows from
the on-disk Gold Book IV-3..IV-6 tables (per-unit citations); availability only, never
offer/price; STAR-designated Gowanus/Narrows barges documented, never restricted.

**Result.** CT_PEAKER 2024 4.75 → 4.54 TWh (actual 2.13); **C1-2024 ST_GAS −3.35 → −3.31 TWh
— still the HARD FAIL** (the CT reduction cleared to CC/imports, not steam). C3a
−14.4/−14.2/−12.4% and C3b 0.199/0.194/0.191 — best NYISO price scores to date, from honest
commitment content. C2-2025/C5a/C4/C6 PASS. The residual CT over-run
(Bayonne/Equus/Edgewood/Glenwood-Landing LM6000s on Transco Z6 hub gas) is the ledgered
**LI/NYC LDC citygate / interruptible delivered-gas premium** data ask. **NEW:** first NYISO
bundles scoring C7/C8 (committed `legitimacy_diagnostics.json`): the nyiso-33/34 temperature
reliability floors force 22.6–28.4% of CT_PEAKER (cap 10%) and 34.0/41.5% of 2024/25 ST_GAS
energy (cap 30%) and flatten the 2024 CT off-peak shape (CV 0.424) — MODEL MISS (rule #20),
now first-class open root causes.

**Registered:** `2026-07-04-nyiso-45-measuredruns` and `2026-07-04-nyiso-46-decpeaker`
(both NOT-YET: C1-2024 + C7 + C8; C3a/b/c ledgered). Best probe: nyiso-46 (most structurally
faithful). Keeper **unchanged**: `2026-07-03-nyiso-41-hub-prices`. Retention: pruned
nyiso-31/nyiso-32 registrations (top-15).

### 2026-07-04 — NYISO — winter-spread promotion blocked by CT de-leak (nyiso 43/44): PROBES, keeper stays nyiso 41

**Goal.** Promote the nyiso-42 reconciled Iroquois winter spread by root-causing its two
blockers (E1 shoulder undershoot exposure, E2 C2-2025 gas FAIL) plus the Jan-2024/Dec-2025
winter overshoots, per the 2026-07-03 carry-forward.

**All three carried items closed measured.** (E2) The C2-2025 −2.5% FAIL was a scoring-basis
artifact: the `run_calibration_full` daily-basis override channel silently enabled
`dual_fuel_oil_reattribution` (spec'd NEISO-only) for every ISO, relabelling parity-switched
winter gas→oil while the measured NYIS EIA-930 feed keeps those hours in `NG: NG` (Jan-2025:
0.80 TWh relabelled vs 0.031 measured OIL; 2023: 2.17 TWh NYIS OIL vs 0.42 TWh EIA-923 oil
class). Gate restored to spec → C2-2025 −0.1% PASS, C5a in band all years (−2.3/−5.3/−3.7% —
keeper-41's 2024 −7.1% breach was the same relabel exporting switch-hour CO2). (E3) The
Feb-2023/Jan-2024/Jan-2025 reconstructions out-priced the measured Algonquin-Citygate ceiling
of the complex Z2 trades inside; `fuel.nyiso_reconciled_reference_monthly` now caps each month
at the measured ALG monthly (HH + the measured NEISO basis row) and water-fills the shaved
scarcity excess as a year-round base, preserving the measured SOM annual spread exactly
(three measured series, no fitted constant; Jan-2024 +6 → +1.6). (E1) Decomposed: east level
= the ledgered offer-markup/reserve frontier (NYISO-AS data is measured *prices*, not a
condition-varying requirement — stays data-blocked); upstate shoulder collapse = Upstate_West
at the wind margin behind the measured 1,450 MW CE TTC while the recon band pushes ~830 MW of
measured net imports through the upstate link (real upstate held ~$22-25 via gross two-way tie
flows; per-interface flows/ratings = new data ask).

**Promotion blocked by a repo-level regression:** commit `0c6c833` (post-run-42) de-leaked the
NYISO CT_PEAKER/CT_CHP econ bands to neutral 1.0 (its own documented open root cause: "a
NYISO-grounded CT econ ramp"). LI/NYC peakers over-run ~2.5× actual (CT 4.9 vs 2.13 TWh 2024)
and displace steam through the HARD C1 band (2024 ST_GAS −3.4 TWh FAIL). Verified the
keeper-41 config itself reproduces the FAIL on current main (CT 4.69/ST 7.65) — every NYISO
solve is blocked until the CT offer level is grounded. `nyiso 44` (+`--tranche-startup-
amortization`, the ISO-NE Order-825 fast-start analogue — real structure, worth keeping)
moves CT only 4.90 → 4.75: P0 base-cost run-lengths are long under neutral bands, so the
amortized start cost is small. Closure candidates (none on disk): LI/NYC delivered-fuel basis
(LDC citygate/interruptible, kerosene frames), a SOM-grounded markup (SOM 2024 confirms offers
sit above bid-based reference levels, no per-class number published), DEC Peaker-Rule run-hour
limits. CEMS marginal HR ruled out (run-28; CT marg 0.66–0.85× base).

**Registered:** `2026-07-04-nyiso-43-ceiling-oilbasis` (NOT-YET: C1-2024 + 3 ledgered soft),
`2026-07-04-nyiso-44-faststart` (NOT-YET: C1-2024; best probe state — C2/C5a/C6 PASS, C3a
−15.4/−14.9/−13.0, C3b 0.207/0.201/0.195, C3c 0/0/7h). Keeper stays
`2026-07-03-nyiso-41-hub-prices` (committed artifacts stand; non-reproducible on main).

### 2026-07-03 — CAISO — S2 CT-floor scrub (caiso 52): PROBE, forcing removed (keeper stays caiso 51)

**Goal.** Execute the legitimacy-audit S2 scrub (`docs/model-legitimacy-audit-2026-07.md` §1-§2,
owner's complaint): dismantle the three stacked CAISO CT forcing engines — the all-24h netload
reliability-floor limbs, their overlap with the evening net-load drag, and the RA startup bridge's
hard-coded CT eligibility — with structural fidelity over backcast fit (rule #1).

**Fixes** (branch `claude/caiso-ct-floor-bridge-jfgit3`):
1. **CT limbs windowed, then retired.** `reliability_floor_coeffs_CAISO.csv` CT_PEAKER/CT_CHP
   netload limbs got `start_hour/end_hour` 15-21 (the drag doc's own evidence: overnight CT CF ≈ 0
   even at high net load). A 2024 A/B (windowed limbs+drag vs limbs-disabled+drag, caiso-51 flags)
   showed the windowed limbs redundant with `ct_netload_drag` — same driver, hours, class:
   arm W (limbs+drag) D-1 r .878/CV 2.55, D-2 87.8% via TWO mechanisms; arm X (drag only) D-1
   r .847/CV 2.59, D-2 75.6% via ONE. One mechanism per phenomenon (rule 18) → limbs
   `enabled=False` (windows kept for provenance); the drag is the single evening CT commitment.
2. **RA bridge eligibility by physics** (`commitment.py`): the `("CC_REGULAR", "CT_PEAKER")`
   tuple replaced by a `min_down_hours >= RA_BRIDGE_ECON_MIN_DOWN_HOURS` (4 h) gate on the
   ECONOMIC startup bridge (audit rule 17) — fast-start CTs (min-down 1 h) are never held
   overnight on restart economics; the physical gap<min-down bridge is unchanged; cogens/steam
   keep their own mechanisms. Tests added.

**Result — caiso 52 ct scrub (PROBE, `results/calibration/caiso52_ct_scrub`, 2023-25, caiso-51
keeper flags).** The audit's flat-floor signature is gone: **D-1** CT_PEAKER off-peak CV ratio
0.030 → 2.6-3.3 (r .886/.847/.681; 2025 r < 0.8 remains, small noisy fleet), **D-4** off-window
binding 65% → **0%**, **D-2** CT forced energy is now a single windowed mechanism (drag; RA-bridge
CT share < 1%, down from the overnight-bridge era). Disclosed regressions (rule #1 — NOT to be won
back by a floor): CT_PEAKER 1.97/1.56/1.15 vs measured 3.08/3.30/1.65 TWh, CC_REGULAR +6.24/+11.85
TWh (absorbs the freed evening energy), C3a +21.1/+36.5/+43.9% (51: +19.6/+34.9/+41.6), C3b
.292/.468/.460, 2023 tail 114 h vs actual 21 h (the removed all-24h CT commitment was suppressing
evening scarcity the model now prices). D-2 still FAILS (66-78% forced) — with the floors gone,
almost none of the remaining CT energy clears on merit.

**Open root-cause item (next lever, unchanged from caiso-48/51 threads):** evening CT merit
dispatch — the P1 merit order prices CTs out of the ramp (import tranche prices / CC offers), so
commitment mechanisms carry the class. Also out of scope here: ST_GAS D-1 shape fail (pre-existing
in the keeper), the w2-caiso-ra-p2 forecast-parity wiring gap (D-5), 2025 CT r.

### 2026-07-03 — ERCOT — P1-only ORDC-era stack, RTORPA restored (ercot 28-32): KEEPER ercot 32

**Goal (P1-ONLY, per the C3 handoff).** Close the C3 gates with the main
no-commitment solve only — no P2 of any kind (`commitment_enabled` /
`ercot_as_aware_commitment` off everywhere; the P2 route is shelved per the
ercot27 verdict). Adopt the probe-proven P1 structure and make the product-level
withholding AND the lumped ORDC total-reserve family work TOGETHER (in ercot27
they were alternatives). Zero offer-curve retuning, zero fitted parameters.

**Mechanisms added (all published/measured, cited in parameter-citations).**

* **`ercot_ordc_total_reserve`** — the lumped ORDC total-reserve family
  (RTORPA, NPRR568/OBDRR048) as an ALL-CLASS reserve-balance family
  (`dispatch._build_reserve_rows` reserve_class −1) drawing on every AS
  product's cleared reserve: product withholding and the total-reserve
  LOLP×VOLL curve price together — the faithful pre-RTC+B stack. No new
  columns, no new headroom, nothing double-procured.
* **`ercot_storage_as_product_credit`** — the measured battery AS award
  (60-Day DAM per-resource-type) netted pro-rata off the fast products'
  requirements, the multi-product analogue of `ercot_storage_as_reserve`;
  netted every year the award is reserved out of the storage cap
  (internal consistency — see ercot30).
* **`gas_hh_monthly_shape`** — measured Henry Hub monthly gas SHAPE,
  hour-weight-normalized to the trusted annual level (the Run-77 reconciled
  variant; the generic shape held Feb/Mar-2024 ~$0.7/MMBtu too dear).
* **`ercot_reserve_supply_cap` paired with the total family** — cleared
  reserve bounded by measured RTOLCAP/RTOFFCAP; the total family's balance
  dual is added post-solve as the additive RTORPA, scoped to the TOTAL
  family only (product duals are MCPCs, never in the energy price) —
  ERCOT's actual pre-RTC+B settlement equation, RTSPP = SCED energy +
  ORDC(online reserves).

**Probe ladder (all registered; dashboard basis, RT benchmark).**

| run | storage | 2023 C3a / Aug | 2024 C3a / shape | 2025 shape / tail |
|---|---|---|---|---|
| keeper ercot26 | measured cap-dock, no netting | −1.7% / −46.1 | +4.7% / 0.199 | 0.072 / 0.19× |
| ercot28 (+total family) | endogenous (G5) | −11.0 / −76.4 | +7.5 / 0.209 | 0.066 / 0.26× |
| ercot29 (+gas shape) | endogenous | −10.4 / −74.6 | +8.3 / 0.234 | 0.085 / 0.26× |
| ercot30 (measured, inconsistent) | cap-dock, no netting | **+87.1 / +159** | +36.8 / 0.509 | 0.305 / 1.65× |
| ercot31 (consistent netting) | cap-dock + netting + credit | −9.6 / −71.9 | +8.8 / 0.234 | 0.087 / 0.32× |
| **ercot32 (+RTOLCAP cap)** | as ercot31 | **−5.4 / −62.4** | +9.1 / 0.235 | 0.087 / 0.32× |

**Root causes settled (measured, not tuned).** (1) The G5 endogenous storage
split holds **2.1–2.4× the measured battery AS award** (2023: 2,625 vs 1,249
MW mean) because it lacks the published per-product duration requirements
(ECRS 2-h / Non-Spin 4-h sustained) — G5 follow-up: add the duration gate.
(2) Reserving the measured award from the cap **without** netting the
requirements over-withholds thermal by the awarded MW — the ercot30 blow-up
quantifies the internal-consistency requirement. (3) With consistent storage
either way, Aug-2023 sits ≈ −72: the miss is the reserve-SUPPLY definition —
the RTOLCAP cap (ercot32) recovers Aug −72 → −62 and Sep −13 → −4.5, and the
>$500 deep tail reaches 68/104. Remaining Aug residual: the flat ORDC σ
fallback (NP6-576-ER seasonal params egress-blocked, WS3) + sub-2-day forced
outages outside the ≥2-day CAMPD detector. (4) The 2024 shape FAIL decomposes:
Jan +12.5 and May +7.8 are the **DAM-AS overlay's DA-boundary premium on an
RT-scored benchmark** (overlay hours realized DA ≈ $599/$511 vs RT ≈ $205/$316;
ex-overlay Jan-2024 = −2.1 with truthful gas); Feb +6.2 was the generic gas
shape (measured shape → +3.2). The overlay **stays**: ex-overlay the 2024 tail
collapses to 10/53 = 0.19× — the RT-scored co-opt cannot form the DA-priced
acute days even with measured supply (one event, one channel holds; the
DA-boundary premium is documented MODEL MISS, not excused).

**Keeper decision (structural, rule #1).** ercot 32 PROMOTED over ercot 26:
strictly more real market structure (product withholding, published ECRS
design, RTORPA price formation with measured supply, consistent measured
storage treatment, measured gas shape), every mechanism published or measured.
The C1/C2 hard-caveat pair is inherited unchanged (CC_REGULAR 2023 −8.53 TWh
nodal/intra-zone; gas 2025 −3.0% preliminary vintage) and C5c 2024 storage
shape improves r −0.306 → +0.331. Determination **NOT-YET** (C1+C2 exceed the
hard budget; C3 misses are MODEL MISS with named root causes). ercot26's
better 2023/2024 C3a came from documented compensation (scarcity months under,
shoulders over) and an internally-inconsistent storage treatment.

**Follow-ups.** (a) G5 duration-gated endogenous storage AS (published ECRS
2-h / NSPIN 4-h rules) to retire the measured reservation forward; (b) the
NP6-576-ER seasonal/TOD ORDC μ/σ re-fetch (egress-blocked) for the Aug-2023
deep band; (c) Feb/Mar-2025 +5/+6 exposed by truthful gas (open thread);
(d) sub-2-day forced-outage representation for heat events; (e) the C1
sub-zonal/nodal topology work stream (unchanged).


### 2026-07-03 — CAISO — measured-hub WECC seam decomposition (caiso 49/50/51): caiso 51 promoted KEEPER

**Goal.** Root-cause the C3a +37–49% over-price (CAISO the furthest ISO from calibrated,
7 criteria FAIL) with an import-supply-curve decomposition before touching offer curves.

**Root cause.** The caiso-42 keeper priced the WECC seam (~30% of supply) with the
audit-flagged **fitted flat ladder** ($28–$180, constant all 8760 h) + fitted 7,500 MW
simultaneous cap, while the measured Malin/Palo Verde intertie prices track the actual
CAISO price nearly hour-for-hour (2024 PV mean $33.3 vs actual RT $32.4; midday $8 vs $12,
swings −$58…$636). The keeper's registered "corridor ATC forward envelope" was **inert**
(its gate needs the per-hub split the keeper never built). Also found and fixed a scorer
comparability bug: C3a compared a full-year model mean against CAISO 2023's Mar–Dec-only
actual (Jan–Feb aged out of OASIS) — masked to common months, keeper 2023 was **+16.9%,
not +48.8%**.

**Arms** (each registered; full detail
`results/calibration/FINDING-caiso49-import-seam-2026-07-03.md`):
- **caiso 49 perhub seam** (PROBE): per-hub corridors at measured hubs + measured p95
  envelopes both directions + published MIC (16.0/16.5/16.1 GW) replacing the 7,500 MW cap
  + 2023 gap-fill. Shape/volumes improve; C3a 2023/24 worsen — all-spot pricing
  transplants hub spikes whenever the tie is marginal, but the real contracted import
  majority is inframarginal (2023/24 summers: CAISO $50–54, PV spot $69–74, 3–4 GW flowing).
- **caiso 50 perhub bridge** (PROBE): + UC startup bridge/decommit (caiso-44/48). Best C4
  (gas r .805); 2023 fitted-cap tail 107h→11h (0.52×).
- **caiso 51 firm base** (**KEEPER**): + `caiso_perhub_firm_base` — firm/contracted
  tranches at documented contract-cost estimates (inframarginal), spot tranches + export
  legs at the measured hub. C3a +19.6/+34.9/+41.6 (42: +16.9/+36.9/+47.1), C3b
  .285/.459/.436 (best), C4 2023 gas passes first time, C2 2025 +8.1% (was +12.3%), C5a
  2025 +8.7% (was +12.7%). Determination **NOT-YET**; promoted on structure (#1/#14): the
  fitted ladder and the fitted 7,500 cap are out of the binding path (audit items C-5,
  C-6/L8 closed).

**Standing residuals (next levers, in order):** (1) fall/winter under-import (2024 net
import 25.8 vs 32.4 TWh; CC_REGULAR +10.9 TWh concentrates Sep–Jan) — the specified-import
VOLUME is under-represented: intake CEC/CARB specified-vs-unspecified import data for
measured firm-block capacities; (2) spring-midday floor $34–38 vs $11–14 — model short
where reality is RUC-long and exporting: day-block RUC commitment sizing (caiso-43 §6);
(3) C3c honest collapse 0h — CAISO scarcity-pricing mechanism (AS-award thread). Hydro
audited clean (EIA-930 monthly budgets, LP opportunity cost).

### 2026-07-03 — ERCOT — ORDC-era 2023 price formation (ercot 27): PROBE, root-caused (keeper stays ercot 26)

**Goal.** Close the 2023 price-structure gap *structurally* (rules #1/#11/#13/#14):
the keeper passes 2023 mean LMP by compensation (scarcity months under, shoulders
over). Build the mechanisms that actually operated: (WS1) commitment-state-aware
reserve headroom; (WS2) the published ECRS conservative-deployment design; plus the
endogenous storage energy-vs-AS split (G5). Zero offer-curve retuning, zero fitted
parameters. Bundle `results/calibration/ercot_ordc_structure_v1`, dashboard run
`2026-07-02-ercot27-ordc-structure`.

**Research corrections (WS2, cited in parameter-citations).** The handoff's recalled
"$2,000/MWh ECRS proxy floor" does **not** exist in any primary source: in 2023 ECRS
was *not releasable to SCED at any price* (manual reliability deployment only —
frequency < 59.91 Hz or 10-min projected net-load insufficiency; ERCOT AS Study white
paper, Sept 2024), which the IMM found "led to artificial shortage pricing … doubled
average energy prices between June and December 2023" (>$12B; 2023 SOM §II.G).
NPRR1224's $750 floor was **rejected** by the PUCT (2024-07-25); the actual reform
(effective 2024-08-01, operating procedures) is a 40 MW/10-min undergen release
trigger at resources' own offers. Modeled as an at-cap ECRS demand step
2023-06-10→2024-07-31, standing VOLL ramp after (`ercot_ecrs_conservative_deployment`,
`ERCOT_ECRS_RELEASE_REFORM_YEAR/HOUR`).

**Mechanisms (stay in the codebase, default off).** AS-aware P2 commitment now fully
re-scopes reserve supply by the solve's own commitment state: `couple_peak` (a cold
plant's peak/duct tranche leaves the headroom RHS), online CTs join the synchronized
pool per-hour via P2 availability, offline quick-start capacity backs Non-Spin only
via a reserve-only extra cap (`ercot_commitment_headroom_overrides`); the runner
gains the AS-adequacy floor + overrides for forecast parity. The dashboard renderer
now scores a bundle's **primary pass** (P2 when commitment ran) instead of always P1,
so a commitment run's registered numbers are the market solve it proposes.

**Result — NOT-YET probe; both misses root-caused, not tuned around.** The
within-bundle P1-vs-P2 comparison settles the attribution (annual dw model vs RT
$48.36 / $26.83 / $32.49; Jun/Jul/Aug 2023 residuals):

| year | pass | annual | C3a | Jun | Jul | Aug |
|---|---|---|---|---|---|---|
| 2023 | **P1 (no commitment — the main run)** | 40.73 | −15.8% | −13.9 | −9.7 | −88.7 |
| 2023 | P2 (opt-in AS-aware commitment) | 52.20 | +7.9% | −12.9 | −9.1 | −90.2 |
| 2024 | P1 / P2 | 28.75 / 30.43 | +7.2% / +13.4% | | | |
| 2025 | P1 / P2 | 33.35 / 35.39 | +2.6% / +8.9% | | | |

The 2023 scarcity-month improvement (Jun −$23.5 → **−$13.9**, Jul −$10.1 →
**−$9.7**, Oct/Nov ≈ 0) is **already present in P1** — it comes from the P1-level
structure (the ECRS no-release demand step + multi-product AS carve-outs in the LP),
NOT from the commitment pass. **The AS-aware P2 pass added no scarcity-month signal
(Jun −13.9→−12.9, Aug actually −88.7→−90.2) and only a broad all-month elevation
(+$11.5/yr 2023, +$1.7 2024, +$2.0 2025)** — the exact-coverage AS-adequacy floor
(committed ≈ energy + AS) leaves ~1.0× online-reserve coverage where measured
RTOLCAP shows ~2×, so the shared-headroom dual elevates every month (Feb-2023 +$42.5
with ECRS not yet live isolates the artifact to the floor). WS1's
commitment-state-aware headroom in its current form therefore does **not** help and
is not part of any recommended configuration. Independently, (b) the multi-product
swap **drops the lumped ORDC total-reserve curve — the published RTORPA mechanism of
2023-25** — so even P1's deep tail collapses (Aug-2023 P1 −$88.7 vs keeper −$46;
>$1,000 hours 28 vs 61) while rigid withholding lengthens the moderate tail (P2
281 h >$200 vs 181, 1.55×; 2025 0.26×). C1/C2/C4/C5a unchanged from the keeper
(CC_REGULAR 2023 −8.52 TWh, gas 2025 −2.8%).

**One event, one channel (audit result).** With the endogenous co-opt scarcity
active, overlap with the measured overlays is trivial — RTORDPA∧reserve-dual
min-overlap ≈ $0.2k (3 shared hours, 2023), DAM-AS ≈ $3.9k (5 hours, 2024) — so no
double-counting channel is live; 2024's tail is carried almost entirely by the
DAM-AS overlay (dual-only tail 10 h vs 73 h with it), i.e. the co-opt still cannot
form the 2024 acute days endogenously (run-163's discretionary-uplift finding
stands).

**Keeper decision (structural, not MAE).** NOT promoted. The follow-up direction is
**P1-level** (the main, no-commitment run): keep WS2's product withholding AND
restore the lumped ORDC total-reserve demand curve alongside it — the faithful
pre-RTC+B stack is both together, in the P1 LP. The P2/AS-aware commitment route is
shelved: its adequacy-floor tightness is an artifact, and the P1↔P2 comparison shows
it contributes nothing to the scarcity months it was aimed at. Keeper remains
`2026-07-02-ercot26-gtc-limits`.

**WS3/WS4.** NP6-576-ER 2023-vintage re-fetch still egress-blocked (all hosts 403;
report decommissioned post-RTC+B) — flat 0/1,400 fallback retained, attempt
documented in docs/ordc-overlay.md. C3a records now name their benchmark (vs RT /
vs DA fallback) and carry a non-gated DA diagnostic row (the DART premium made
visible; 2023: model −6.7% vs DA with DA−RT premium +$7.58).

### 2026-06-17 — ERCOT — nodal sub-zonal pockets (run124): MEASURED NO-GO (the over-run is not pocket-reachable)

**Goal.** Close the CC_REGULAR North over-run (run124: +5.60 / +3.12 TWh
2024/25; North carries ~+4.5) and the linked SC/West/NE under-run by adding the
binding **sub-zonal pockets** the 7-zone reduced network cannot form — letting
the thermal offer curves relax toward physical instead of re-fitting global
compensation on a coarse grid (the NE_LOB pattern generalised, with the SCED
NP6-86 archive now in hand). **Result: NO-GO — keeper stays run124.** The
residual is not reachable by any *defensibly-buildable* pocket; it is the
irreducible below-local-price RUC piece + the gas-price year-gradient. Probe
code (a Rio_Grande/VALEXP pocket) built, measured, and **reverted (not
promoted).**

**Anchor.** Reproduced run124 exactly on this environment (highspy 1.14.0):
CC_REGULAR 2024 **+5.60** / 2025 **+3.12**, CT_PEAKER −2.40 / −3.50 / −1.69 —
the documented **5 fails @0.5%** (CC 24/25, CT 23/24, COAL_PRB 24). So every
delta below is vs a same-environment baseline.

**1. Where the over-run lives (by-zone CC_REGULAR, model TWh).** The over-run is
concentrated in **North** — and the network is essentially uncongested, so cheap
North CC freely serves the under-zones (mean zonal energy price flat at $20.1
2024 / $32.5 2025 across North/SC/Houston/South/West):

| zone | 2024 | 2025 |
|---|---|---|
| **North** | **78.22** | **76.36** |
| South_Central | 34.81 | 31.41 |
| Houston | 15.76 | 14.01 |
| West | 9.40 | 9.81 |
| South | 9.06 | 8.55 |
| Northeast | 1.54 | 2.90 |

**2. GTC inventory — the buildability test (the decisive new finding).** Ranked
every aggregate GTC (empty FromStation) in the NP6-86 archive
(`scripts/derive_ttc_limits.py` / `analyze_sced_binding.py`) by zone and
modelled-or-not:

| GTC | binds % | limit@bind | status |
|---|---|---|---|
| NE_LOB | 48 | ~1,281 MW | **modelled** (Northeast→North 1300) |
| PNHNDL | 45 | ~3,297 MW | **modelled** (Panhandle→North 2680) |
| WESTEX | 40 | ~10,453 MW | **modelled** (West→North/SC 7300/2700) |
| **VALEXP** (Rio Grande Valley) | **46** | **~537 MW** | **UNMODELLED — only clean one** |
| EASTEX | 45 | — | tiny (rent 0.14M) |
| N_TO_H | 5 | ~4,810 MW | modelled (North→Houston 8000) |

So the **only clean unmodelled aggregate GTC is VALEXP — and it is in the South
zone (~1 GW gen), not North.** There is **no aggregate GTC for North** (the
over-zone) or for the internal SC/West under-zones. The **Permian binders are
all diffuse <200 kV internal lines** (ODESSA–YARBR `6520__E`, VEALMOOR–KOCHTAP
`15060__B`, KNAPP `6437__F`, MIDLAND) — **no aggregate "Permian export" GTC
exists**, so a Permian sub-zone has *no measured export limit* (data-first
fail). This is the precise, sharpened form of the D4-spatial finding (94% of
rent on <200 kV pockets): the rent is real but lives below any pocket the
reduced model can carry a *measured* limit for.

**3. The Valley/VALEXP probe (built the one measured pocket; the NE_LOB pattern
generalised).** Added a `Rio_Grande` zone split out of South
(`zone_assignment._ercot_zone` lat<27.0 / −99.0≤lon<−97.0 box → Magic Valley CC,
Red Gate, Silas Ray + small RGV peakers, ~1 GW), a `Rio_Grande→South`
TransferLink at the **measured 537 MW VALEXP limit**, and a SOUTHERN-load split
in `eia_loader` (the load share is a Tier-3 estimate, 0.030 of system — there is
**no published RGV/South native-load split**; the RGV is inside the single
SOUTHERN weather zone). 2025, vs anchor:
- **The pocket interface BINDS hard** — Rio_Grande price separates from South in
  **61.6% of hours** (mean $2,096, max $4,979). The generalised-NE_LOB mechanism
  works: a measured-GTC sub-zonal pocket binds in the model.
- **But North CC is untouched** — North CC **76.18 vs 76.36** (≈ flat); the
  pocket is in the wrong zone and cannot relieve the +4.5 over-run.
- **And it cannot be specified defensibly** — **1.70 TWh unserved** energy, all
  in Rio_Grande (3,218 load-shed hours). Root cause: **VALEXP is an *export*
  limit on a net-*importing* load pocket** (RGV mean demand 1.66 GW, peak 2.68
  GW vs ~1 GW local gen + 537 MW). Modelling the single GTC as the pocket's
  interchange capacity starves it; the RGV's real (multi-line, multi-GW) *import*
  capacity is not a single measurable GTC. So even the one clean GTC is the
  wrong *instrument* for the energy-balance hours that carry the CC residual.

**4. Reachability diagnostic — is the North over-run spatially reachable AT
ALL?** Hard-tightened North's export corridors to *unphysical* levels
(North→SC 5000→1500, North→Houston 8000→2000 — no measured-GTC basis) to *force*
a binding interface around the actual over-zone. The interfaces then bound 25%
of hours (price separation up to $25), zero unserved. Effect on CC_REGULAR
(2025, TWh): North **76.36 → 73.89** (−2.47 of the +4.5 over-run); SC +0.71,
Houston +0.38, South +0.16; West −0.37, NE −0.21; **class TOTAL 143.04 → 141.24
(−1.80)**. So even *forcing* a bind: (i) only ~2.5 of the +4.5 moves, (ii) it
does **not** cleanly relocate to the under-zones — ~1.8 TWh leaves the CC class
entirely (fuel substitution), which would *worsen* the CC volume gate. At the
**measured** interface limits nothing binds (flat $32.5; inter-zonal TTC
tightening to measured GTCs was already an exact no-op, run115b notes; the
congestion-subset floor a near-no-op, run118).

**Defensibility verdict (the prompt's two-part gate).** (a) *Does a measured
pocket bind where the residual lives?* **No** — North/SC/West-internal have no
unmodelled aggregate GTC; Permian is diffuse <200 kV; the only clean GTC
(VALEXP) is in South and is an export limit on a load pocket. (b) *Even when a
bind is forced, do the offer deltas relax?* **No** — the North CC drop is
partial and substitutes fuel rather than relocating CC; you would have to re-fit,
not relax. **Both fail ⇒ NO-GO.** This is the prompt's anticipated valid negative
result: *the residual North-over/SC-under is the irreducible ~6.7 TWh
below-local-price RUC commitment + the gas-price year-gradient, not a
pocket-topology gap.* Consistent with D4-spatial, run118, and the inter-zonal
no-op. Keeper stays **run124**; the merit-ramp remains the CC shape fix. Probe
diagnostics were single-year scratch (not dashboard-registered; the pocket code
is reverted).

### 2026-06-17 — ERCOT — LMP decomposition + CT_PEAKER offer re-derivation (run124 keeper held; overlay recalibrated)

Two-track session on the run124 keeper's open price/marginal residuals. **No
promotion — run124 stays the keeper of record.** Full writeup:
`docs/lmp-decomposition-2026-06.md`.

**TASK 1 — "dispatch is spot-on, LMP is off" (the reframing, measured).** The
energy-only LMP MAE (32.3 / 7.8 / 2.3) is **tail-dominated, not a body error.**
Full-year body/tail split (threshold actual RT $80): the body (~95% of hours,
~all dispatched energy) sits at a **$7–9/h** MAE with a near-zero mean residual
(2025 even +$3.6); the tail carries **78% (2023) / 47% / 30%** of the total
$·h error from **5.0% / 3.0% / 4.4%** of hours. 2023's whole $32 MAE is **86%
August+Sep+Jun** (August: model $27.8 vs RT $191.7). Price duration: model P99
**$40/$34/$63** vs RT **$644/$147/$138**; the model's entire tail is the CT
peak band (~$226 in 2023) + the odd VOLL slack hour. The actual RT fat tail
(hundreds of $100–$5,000 h, ORDC/RTORPA + AS co-opt) is **structurally absent
from the LP duals** — irreducible by construction (zero-unserved-energy
perfect-foresight LP prices at the marginal *generator offer*). **The model's
marginal unit is NOT mis-classed:** in the price-setting hours it is a CT peaker
in both model and reality (honesty diagnostic: model is genuinely thin in the
hours reality was thin, ρ≈−0.39); reality just stacks the reserve-demand-curve
adder on top of that same generator. Analytic offer-band overlay confirms the
body (p50–p90, $18–$32) is the CC_REGULAR econ ramp, the upper body (p95–p99,
$34–$63) the CT committed→econ_high bands, the ceiling the CT peak band — the
merit order reality runs.

**TASK 1b — overlay recalibration (the one fixable LMP target, display-only).**
Scored the *published* overlay (the dashboard's price line) on run124: published
NP6-576-ER shift0 closes ~22% of the 2023 summer gap (MAE 32.3 → **24.6**),
honestly cannot close 2023 (perfect-commitment headroom ~8.6 GW median in the
181 actual >$200 h ⇒ ORDC LOLP≈0). **New finding: the AS-aware keeper
re-calibrates the reliability-deployment (RTORDPA) offset from run115b's 2,500
MW to ~1,500 MW.** `--storage-as-commitment` already caps the battery peak dump,
tightening peak-hour reserves and supplying ~1 GW-equivalent of the discretionary
tightness the old 2,500 MW carried — so 2,500 now **overshoots** on run124 (2023
hours >$200 220 vs actual 181; 2024/25 MAE 9.9/7.1). Re-swept: 1,500 MW gives
2023 MAE **12.5** / 120 of 181 tail hours / 2024 7.6 / 2025 4.1 — the run124
analogue of run115b's 2,500 MW outcome. Committed `scarcity_np6shift0.parquet`
(published canonical) + `scarcity_reldeploy1500.parquet` (run124 stress) to the
bundle. Display-only; never gates volumes.

**TASK 2 — CT_PEAKER grounded offer re-derivation (NEGATIVE — structural
residual confirmed).** The run124 CT offer (committed 1.14, econ_low 1.27,
econ_high 2.18, peak 13.15) has a **rising** econ ramp, which is the *opposite*
of a physical CT heat-rate curve (a CT's incremental HR *falls* toward full
load). The rising ramp is an **offer markup** — startup amortization + scarcity/
opportunity cost, how ERCOT peakers actually bid — not a heat rate. Two 2024
test re-derivations (grid TWh; actual CT≈7.4, ST≈18.2):

| 2024 | CT_PEAKER | ST_GAS | model price p90/p95/p99 | upper-body 45–80 h |
|---|---|---|---|---|
| run124 keeper | 3.91 (−3.5) | 17.87 (−0.3 PASS) | 33/35/42 | 41 h |
| A: heat-rate-pure (committed 1.30, econ flat 1.00→1.05) | 8.25 (+0.8 over) | **15.73 (−2.5 FAIL)** | 25/28/33 | 4 h |
| B: cheap committed 0.80 (keep markup ramp) | 9.11 (+1.7 over) | **15.80 (−2.4 FAIL)** | 25/28/34 | 4 h |
| actual RT p90/p95/p99 | — | — | 42/61/147 | — |

Both grounded/cheaper CT offers (i) **over-recover** the CT volume under-run but
**crater ST_GAS by ~2.4 TWh into a clear fail** (the documented CT↔ST −0.25
cross-coupling — run124 holds CT at −3.5 precisely because ST_GAS needs that
merit space), AND (ii) make the **price shape worse** — the upper body collapses
(p90–p99 33→25 / 42→33), moving *away* from RT (42/61/147). So the run124 rising
markup ramp is load-bearing: it holds CT to realistic volume *and* lifts the
upper-body price toward RT. **The CT under-run is the non-CEMS small-peaker
structural gap** (Ector County, Permian Basin, Pearsall — no hourly CEMS,
unreachable by merit order), **not** an offer mispricing. Document, leave;
run124 CT offer kept. No Jacobian re-levering: the existing run124 panel (CT
committed −0.05 → CT +0.43 / ST −0.25) already predicts exactly what A/B
confirmed — the documented cross-coupling, no class over-levered. Probes:
`ct_hrpure_2024`, `ct_cheapcommit_2024` (rejected; 2024 single-year).

**TASK 3 — CC_REGULAR nodal volume residual: DEFERRED (gated on resolution, not
data).** The zonal LMP artifact (`actual_lmp_zonal_ERCOT.parquet`) IS available,
but the D4-spatial pre-test already proved the binding congestion is **nodal,
not zonal** (94% of SCED rent on <200 kV local pockets; 123 constraints to reach
80%; no zonal interface carries meaningful rent), so finer zones would not bind
and a zonal overlay re-fits the same global compensation (run118/119 weak). The
+5.60/+3.12 TWh 2024/25 over-run needs a genuinely nodal model or a data-targeted
out-of-merit floor over dozens of the top SCED pockets — a heavy structural piece
with steep diminishing returns, correctly its own session
(`docs/spatial-ruc-session-prompt.md`). Not pursued here.

**Follow-up ("keep tuning") — spatial reliability-deployment overlay re-confirmed
NO-OP on the run124 keeper.** run118 tested the congestion-subset min-gen floor
on run115b (which had CT-deployment ON, no storage-AS) and found it near-redundant
with the 7-zone LP's existing zonal dispatch. Re-ran `--reliability-deployment`
on the *clean run124 base* (CT-deployment OFF ⇒ deeper CT under-run ⇒ more merit
room for the pocket CC/ST plants the floor targets) to test whether it now binds
— 2024/2025, bundles `run124_reldeploy_2024/2025`. **Still a near-no-op:** every
class moves <0.1 TWh (CC_REGULAR +0.07/+0.08 — the *wrong* direction, as run118
found; CT_PEAKER −0.02/−0.03; ST_GAS +0.05). The 2.7–5.2 TWh congestion wedge is
real but the 7-zone LP already dispatches ~85–90% of it regardless of the CT/
storage state, so the spatial imbalance is irreducible by a price-recoverable
congestion floor — it lives in the genuinely nodal (sub-zonal) pockets or the
~6.7 TWh below-local-price RUC piece. The only lever that would bind is a top-down
CAMPD-net-gap zone floor, which is the **CEMS-pinned, no-forward-analogue** class
the user deliberately dropped in run120 (forecast-defensibility) — so it is not
adopted. **Net: every defensible volume lever on the run124 keeper is now
exhausted; all remaining fails (CT 2023/24 non-CEMS, CC 2024/25 nodal, PRB 2024
cheap-gas) are structurally diagnosed and out of reach of a defensible offer/
floor.** Probes registered on the dashboard.


### 2026-06-17 — ERCOT — run124 NEW KEEPER: the AS-aware storage design (run121 + --storage-as-commitment)

**run124** = run121's exact config **+ `--storage-as-commitment`**
(`results/calibration/run124_storage_as_keeper`; CT deployment OFF,
`battery_dispatch_adder=10` retained, storage vintage COD ramp on, merit-ramp CC,
cc-duct). Finalizes the storage AS-commitment lever (the run122/123 probes) into a
clean 3-year keeper. **Adopted for ACCURACY, not fit.** Supersedes run121.

**Scores vs run121: identical, by design.** Volume **5 fails @0.5%** (CT_PEAKER
2023/24, CC_REGULAR 2024/25, COAL_PRB 2024), **7 @0.33%** — the same set. **cf_emd
[7c] 18/18 PASS**, several marginally better (CC_CHP 2023 0.124→0.121 / 2024
0.118→0.115; CT_PEAKER 2024 0.080→0.076; ST_GAS 2023 0.069→0.068 / 2024
0.098→0.097), no regressions. **CO₂ 8/9** (2024 coal −7.0% cheap-gas residual,
unchanged; totals within ±5% all years). The storage-AS change is on the storage
class — thermal volumes/CO₂ move <0.01%.

**The accuracy gain (why it's a keeper):** the energy-only LP dumps the full
battery fleet into a handful of hours. 2024 baseline discharges in 451 h, peaking
at **5.93 GW**; the AS reservation caps that to a **physical 4.59 GW** spread over
511 h, landing the 2024 storage benchmark dead-on — discharge 0.781 → **0.728 TWh**
(EIA-930 0.722), charge 0.857 (EIA-930 0.870). **12 unphysical >4.6 GW dump hours
→ 0**: in the top dump hour (h6833) the model committed 4.0 GW to AS yet baseline
discharged 5.9 GW of energy; the reservation throttles it to 2.65 GW. 2023 (the
ESTIMATE year) 0.525 → 0.51 TWh, peak 2.95 → 2.56 GW; 2025 ≈ unchanged
(3.799 → 3.788 TWh — the model under-runs the 5.45-TWh 2025 fleet regardless, a
separate item the storage-AS lever doesn't touch).

**TASK 3 — the "trade the magic number for data" experiment (the headline
finding): the measured AS constraint COMPLEMENTS, does not REPLACE,
`battery_dispatch_adder=10`.** A/B on 2024:

| 2024 design | storage discharge (EIA-930 **0.722**) | charge (**0.870**) | peak GW | hrs>1MW | CC_REG | COAL_PRB | CT_PEAK | fails@0.5% | cf_emd |
|---|---|---|---|---|---|---|---|---|---|
| run121 (adder10, no AS) | 0.781 (+8%) | 0.918 | 5.93 | 452 | +5.64 | −3.62 | −3.53 | 3 | base |
| **run124 (adder10 + AS)** | **0.728 (+0.8%)** | **0.857** | **4.59** | 511 | +5.60 | −3.64 | −3.50 | 3 | **6/6, 3 better** |
| adder0 + AS (REJECTED) | **2.724 (+277%)** | 3.205 | 5.91 | 2059 | +6.59 | −3.43 | −4.00 | 3 | CT_PEAKER r 0.466→0.445 **FAIL** |

The adder is the throughput/degradation + AS-opportunity cost that bounds storage
**energy** (total cycling); the AS reservation is the measured physical commitment
that caps the **peak** (power). They are orthogonal: dropping the adder to 0 leaves
the LP free to over-cycle in the 2059 hours where AS is low (storage explodes to
3.8× benchmark and CT_PEAKER's shape regresses), because the reservation only binds
in the high-AS peak hours. With both on, 2024 energy lands at +0.8% of benchmark —
no over-suppression, so no harmful double-count. **adder=10 stays** as a defensible
degradation VOM (`ScenarioConfig.battery_dispatch_adder`, forecast-applicable; not
a CEMS-pinned magic number); the data validates it does real, distinct work and
adds physical peak fidelity on top.

**TASK 1 — structural / market-integrity review (clean).** (a) No double-counting:
`as_revenue_enabled` is OFF in the keeper — that path only feeds the capacity
new-entry/retirement screens, which don't run in the P1 backcast, so the dispatch
power reservation and AS capacity-revenue are orthogonal. (b) ORDC overlay is
display-only and never gates volumes/LMP; `ordc_as_plan_mw` netting is OFF
(rejected), so storage AS is not subtracted a second time — the overlay reflects
the post-reservation dispatch correctly. (c) **Reg-Down correctly excluded**: the
up-AS source (`ercot_<yr>_as_up_mw.parquet`) has no `regdn` column; the storage
series is RegUp+RRS+ECRS only (offline Non-Spin excluded from thermal). (d)
Per-resource-type reconciles with NP3-911: by_restype(storage+load+thermal) vs
non-NonSpin up-AS = +40 MW (2025, ~1%), −600 MW (2024, storage conservative).
(e) **SOC vs power**: the reservation reserves power, not SOC. For the energy
backcast (what we score) power is the binding, first-order constraint — it caps
the unphysical dump. SOC reservation (holding energy behind an RRS/ECRS award)
would matter for AS-deliverability/adequacy in a FORECAST, but is not needed for
the backcast and is left as a documented future refinement.

**TASK 2 — physical operating review (positive).** Fleet RTE = discharge/charge =
**0.850** (exact li-ion-4hr target); **0 hours** of simultaneous charge>1 &
discharge>1 MW (no unphysical round-tripping); the reserved fleet AS matches the
measured series exactly (peak 4596 MW / mean 2045 MW = the AS series); **0 hours**
where fleet discharge exceeds the AS-reduced power cap (the reservation is fully
respected and self-consistent). Thermal must-run/outage overlays compose
unchanged. High-AS scarcity hours spot-checked: the reservation throttles each
hour by exactly its measured AS MW.

**TASK 4 — offer-curve Jacobian on the new design (stable, no class over-levered).**
4-probe panel on the storage-AS design (2024, −0.05 single-band moves vs the
run124 base), Δ(class TWh):

| −0.05 move | CC_REG | CC_CHP | COAL_PRB | LIG | ST_GAS | CT_PEAK | CT_CHP |
|---|---|---|---|---|---|---|---|
| CC_REGULAR econ_high | **+1.23** | −0.40 | −0.54 | −0.16 | −0.06 | +0.01 | −0.08 |
| CC_REGULAR committed | **+0.43** | −0.12 | −0.18 | −0.04 | −0.05 | −0.01 | −0.03 |
| CT_PEAKER committed | −0.06 | −0.01 | −0.10 | −0.00 | −0.25 | **+0.43** | −0.01 |
| ST_GAS committed | −0.43 | −0.07 | −0.06 | −0.03 | **+0.61** | −0.00 | −0.02 |

Every **own-class** (diagonal) response is correctly signed (cheapening a band
raises its class) and **larger than any of its cross-class responses** — no class
swings more than the band that was moved, so nothing is over-levered and no knob
crosses a merit-order step (the run-82 failure mode). The cross-couplings are the
documented ERCOT ones (CC_REGULAR the big marginal class displacing COAL_PRB/CC_CHP;
the CT_PEAKER↔ST_GAS pair; ST_GAS↔CC_REGULAR). Net Σ Δ across classes ≈ 0 (±0.006
TWh) — pure reshuffle, no spurious generation. The storage-AS change left the
thermal offer-curve sensitivities stable (it touches only the storage power cap).

NOTE: the dashboard probes run122 (2024) / run123 (2023 est) had **CT deployment
ON** — they were run121 + storage-AS + CT-deployment, split across two single-year
runs, *not* a clean run121 + storage-AS. run124 is the clean keeper-grade 3-year
reproduction (CT deployment OFF). The storage-AS conclusion is unaffected (the
reservation is orthogonal to the CT overlay).

### 2026-06-16 — ERCOT — storage AS-commitment probe: accuracy-positive, score-neutral (the real AS lever)

Where the thermal-AS lever was negligible, the *storage* one is physically
real. ERCOT batteries clear most of their value as AS (RegUp+RRS+ECRS): the
per-resource-type data shows storage holding **2.0 GW/h in 2024, 2.8 GW in
2025** — ~30 %+ of the fleet's power — which cannot also arbitrage energy. New
opt-in flag `--storage-as-commitment` (default OFF, ERCOT-only) reserves that
measured hourly storage-AS MW from the battery dispatch power cap (pro-rata by
power; reserves power, not SOC). `ScenarioConfig.storage_as_commitment`;
`model/storage.reserve_storage_as_power`.

The energy-only LP otherwise dumps the **full fleet into a handful of hours**:
baseline 2024 storage discharges in only 451 h/yr, peaking at **5.79 GW**. With
the AS reservation it binds in the ~75–170 peak/scarcity hours where the model
over-discharges — peak capped to **4.58 GW**, discharge spread to 511 h, annual
energy ~flat (0.78 → 0.73 TWh).

**2024 A/B vs run121: score-neutral, accuracy-positive.** cf_emd 6/6 PASS,
several marginally better (CC_CHP 0.117 → 0.115, CT_PEAKER 0.051 → 0.049, ST_GAS
0.098 → 0.097); CO₂ classes ~unchanged (CC_REGULAR +3.5 %, CT_PEAKER −24.5 →
−24.2). It does **not** fix the CT_PEAKER under-run (documented non-CEMS small
peakers), but it makes the storage dispatch defensible (measured AS reservation
vs an unphysical full-fleet peak dump) — an accuracy keeper candidate in the
spirit of run121's storage COD ramp, not a fit lever.

**Where it should matter more — 2023.** The 2024 score effect is small because
the keeper's `battery_dispatch_adder=10` already throttles storage to 0.78 TWh
(a tuned proxy for the same AS-priority behaviour). 2023 has the highest AS
share (smaller battery fleet, batteries earned ~85 % of revenue from AS) and is
the scarcity year the ORDC overlay compensates for — capping storage peak dumps
there should lift scarcity prices most. Re-check when 2023 data lands; and a
follow-up worth testing is replacing the `battery_dispatch_adder` magic number
with this measured constraint. Flag default-off pending that.

**2023 result (ESTIMATED storage-AS — `build_ercot_storage_as_2023_estimate.py`,
intensity transfer from 2024 × EIA-860 fleet ratio, ECRS zeroed pre-June; ~832
MW/h base, 0.31 intensity).** The mechanism is right and directionally helps the
thing 2023 needs — the energy-only LP produces a laughable $75 max price; the
reservation creates real scarcity spikes (max $75 → $226 base / $258 at the 0.40
bracket; hours > $100 0 → 14 / 21). But the magnitude is small: a handful of
hours, not the hundreds near the $5,000 cap that the ORDC overlay supplies.
cf_emd 6/6 PASS both brackets (several marginally better), no regressions. So
storage-AS commitment is a real but minor scarcity contributor, not an ORDC
replacement — and 2023 is an estimate, so it can't be a keeper on its own.
Net read across all three years: a defensible accuracy improvement (measured for
2024/25), low score impact; adopt for correctness if at all, not for fit.

### 2026-06-16 — ERCOT — AS-withholding probe (NOT a keeper): RESOLVED — thermal AS withholding is negligible (measured)

**Probe**, not adopted. Tests the run121 hypothesis that the CC over-run is an
ancillary-service-withholding effect (the energy-only LP holds zero AS; ERCOT
clears ~7 GW). New opt-in flag `--as-reserve-withholding` (default OFF,
byte-identical baseline) removes the hourly cleared DAM **upward**-AS MW
(RegUp + RRS + ECRS + Non-Spin; Reg-Down excluded) from thermal headroom before
the supply curve clears. Series built by `scripts/build_ercot_as_withholding.py`
from the NP3-911 cleared-AS reports (`inputs/raw-data/ercot-AS/`), on the model's
non-leap 8760 ERCOT-local clock. **Upper bound:** books *all* AS to thermal —
no storage/load split (the per-resource DAM Gen Resource Data needed for a true
split is not in the uploaded set and the 60-day archive only begins Dec-2023).
Mean 6.94 GW/h removed (4.5–9.8 GW range), ~10–14 % of thermal. A/B is 2024
only; baseline faithfully reproduces run121 (cf_emd 0.098/0.098/0.074 match the
keeper). Two within-thermal allocation heuristics were tried; **they bracket the
answer and neither is a keeper.**

**Verdict: the effect is first-order (real, worth modelling), but the
*allocation* — which units hold the AS — is the crux, and no blind heuristic
gets it right. That is exactly what the per-resource data resolves.**

- **Heuristic 1 — pro-rata across all thermal (incl. coal):** big but
  wrong-signed. CC over-run *confirmed as AS*: CC_REGULAR CO₂ flips **+3.5 % →
  −3.2 %** (the run121 hypothesis holds) — but over-withholding baseload forces
  peakers/steam up: CT_PEAKER CO₂ **−24.5 % → +45.7 %**, ST_GAS **−4.2 % →
  +19.4 %**; cf_emd worse on 4/6 (CT_PEAKER 0.051 → 0.097 FAILs), coal worsens.
- **Heuristic 2 — gas-only, top-of-merit by heat rate (coal protected; the
  committed code):** benign but useless. Coal untouched (cf_emd 0.074 → 0.074),
  CC_REGULAR/ST_GAS cf_emd ~unchanged, **CC over-run NOT fixed (+3.5 % →
  +3.4 %)** — the peaking gas headroom it withholds wasn't generating, so it
  barely moves anything; only CT_CHP degrades (0.119, gate FAIL).
- **Why they bracket:** the over-run lives in the *part-loaded mid-merit gas*
  that runs flat-out for energy yet (in reality) holds reserve. Pro-rata cuts
  too much (incl. baseload it forces replacement for); top-of-merit cuts the
  wrong (idle) tranches. Only the units that *actually* clear the AS award
  carry it — and those are identified per-resource in the DAM Gen Resource Data.

**RESOLVED with the per-resource data (the conclusive run).** The 60-Day DAM
Gen Resource Data, aggregated by Resource Type (RegUp + RRS + ECRS; offline
Non-Spin and the storage/load share excluded), landed as
`ercot_<year>_as_by_restype_hourly.parquet`. It reconciles with the NP3-911
totals (2025: NP3-911 − NonSpin 4090 MW vs 4130 by-type, +40; 2024 ~600 short).
**The measured *thermal* AS is tiny and shrinking: 778 MW/h in 2024 (21 % of the
non-NonSpin AS), 429 MW/h in 2025 (10 %)** — storage holds 2.0→2.8 GW and load
~0.9 GW. The code now withholds each thermal class's *own measured* hourly AS
from its top-of-merit headroom (storage/load excluded; falls back to the
upper-bound total only if the per-type file is absent).

**2024 A/B (measured per-class) vs run121: negligible — and the run121
hypothesis is DISPROVEN.** cf_emd 6/6 PASS within ±0.001 (CC_REGULAR 0.098,
COAL 0.074, CT_PEAKER 0.050, ST_GAS 0.098 — all = baseline); CO₂ classes within
±0.5 % (**CC over-run unchanged +3.5 % → +3.6 %**, CT_PEAKER −24.5 → −24.0,
ST_GAS −4.2 → −4.0). The CC over-run is **not** a thermal-AS-withholding effect:
thermal barely holds AS, and the ~0.8 GW it does hold sits on peaking headroom
that wasn't generating, so removing it does ~nothing to the energy dispatch.

**Conclusion:** the energy-only LP's omission of thermal AS is not a material
error for the ERCOT backcast — lever closed. The feature stays as a
data-grounded, default-off option (correct implementation if ever needed, e.g.
a forecast where thermal carries more AS). The real ERCOT AS story is
storage/load dominance; whether the model over-uses storage for energy
arbitrage that is in reality committed to AS is a *separate* storage question,
not thermal withholding. 2025 (thermal AS even smaller) is expected even more
negligible; not separately run.

### 2026-06-16 — ERCOT — run121 NEW KEEPER: + storage vintage (COD) ramp (accuracy, not fit)

**run121** = run120 + ERCOT `storage_vintage_ramp` ON
(`results/calibration/run121_storage_vintage`). Adopted because it is **more
accurate** (claude.md rule: prefer measured inputs over what fits better), not
for the score. ERCOT storage was on a flat year-end fleet; now each unit's
dispatch caps ramp month-by-month from its EIA-860 COD. Verified: 2025 storage
discharge drops Jan–May (e.g. Mar 369 → 263 GWh) and converges to full by
December — the COD ramp working; the annual year-end peak is unchanged.
**Same fail set as run120: 5 at 0.5%** (CT_PEAKER 2023/24, CC_REGULAR 2024/25,
COAL_PRB 2024), 7 at 0.33%; CC_REGULAR 2025 improves +3.62 → +3.11. Published
ORDC overlay re-derived (default display line). cf_emd baseline re-seeded to
run121. The CC over-run is now believed partly an AS-withholding effect (the
energy-only LP holds zero ancillary services; ERCOT held ~6–8 GW, ECRS new June
2023) — next defensible lever, separate session. Supersedes run120.

### 2026-06-16 — ERCOT — run120 NEW KEEPER: forecast-defensible (merit-ramp, CT deployment OFF)

**User directive — defensibility principle.** Keep only mods that are
physically/contractually real AND carry into the 2026–2050 forecast (unit
outage overlays, take-or-pay coal sigmoids, lignite must-run, cc-duct EIA-860
spec, structural offer-curve shape fixes, actual F923 fuel); drop every
CEMS-pinned "magic number" with no forward analogue. So the keeper drops the CT
AS/RUC-deployment overlay (and never adopts the spatial reliability-deployment /
multi-pocket floors).

**run120** = run115b config **+ merit-ramp CC deltas, `--ct-deployment` OFF**
(`results/calibration/run120_meritramp_defensible`). **5 in-scope fails at the
0.5% universal gate** (the dashboard fail score is now 0.5% of ISO annual gen):
- CT_PEAKER 2023/2024 (−2.52 / −3.61): the **honest** under-run — the
  energy-only LP cannot dispatch out-of-merit AS/RUC peaker energy and there is
  no defensible forward fix; the CEMS floor that papered this over is gone.
- CC_REGULAR 2024/2025 (+5.68 / +3.62): spatial-irreducible. The binding
  congestion is **nodal, not zonal** — `scripts/analyze_sced_binding.py` over
  24,881 SCED intervals: 94% of binding-constraint rent is on <200 kV local
  pockets (RGV, Permian), only 6.2% on the ≥345 kV backbone, 123 constraints for
  80% of rent. Finer zones would not bind → not built. (At the tighter 0.33%
  gate, +2 more: CC_REGULAR 2023 −1.81, CT_PEAKER 2025 −2.06.)
- COAL_PRB 2024 (−3.64): cheap-gas economics (justified).

Merit-ramp **fixes the CC_REGULAR operating shape** (cf_emd 0.099/0.105/0.113 →
0.088/0.098/0.101; the new `[7c]` regression gate). CO₂ 8/9 (2024 coal
residual). Carries the published ORDC overlay (display-only; now the dashboard's
default ERCOT price line — the 2,500 MW reliability-deployment offset is itself a
stress-year-fitted magic number, left off by default). Out-of-sample
(statistical-mode) gap and the full D1–D4 audit in
`docs/audit-followup-tests-2026-06.md`. Supersedes run115b/run119 as keeper.

### 2026-06-16 — ERCOT — audit follow-up D1–D4: out-of-sample test, overlay ablation, new shape/CO₂ gates, merit-ramp CANDIDATE KEEPER

**Scope.** Ran the four prioritized tests from the third-party audit
(`docs/ercot-backcast-audit-2026-06.md`); full results in
`docs/audit-followup-tests-2026-06.md`. **2022 + H1-2026 excluded** (user's
untrained holdout sets). `keeper_anchor` reproduced run115b's 5 fails exactly.

- **D1 — out-of-sample (`--statistical-mode`, every answer-injection overlay
  off).** In-scope fails **double 5 → 10**; CT_PEAKER collapses to ~0.8–1.8 TWh
  (the deployment floor supplied its whole match); coal +7–8 TWh; system CO₂
  +8/+9%; hourly-r degrades 0/18. The headline backcast is **not** a
  forecast-skill prior. New umbrella flag `apply_statistical_mode`
  (`run_calibration_full.py`, tested).
- **D2 — single-overlay ablation.** The **historic-outage overlay dominates**
  (5→9 alone; carries volume, CO₂ AND timing) and is the most *defensible*
  (real outages). The **CT deployment floor is the most answer-injecting but
  smallest** (5→6, ~1.5 TWh) — even with it CT fails (non-CEMS peakers
  unreachable).
- **D3 — the missing gates, built.** `scripts/score_backcast_shape_emissions
  .py` (carbon-weighted CO₂ + cf_emd/r) caught a real keeper failure the volume
  gate hides: **2024 coal CO₂ −8.9%** under a passing total (−0.2%) — gas/coal
  split compensation. **Wired a `[7c]` cf_emd/pearson_r regression gate into the
  live report** (`_print_cf_emd_gate`, baseline
  `inputs/calibration/cf_emd_baseline_ERCOT.json` = keeper of record; SKIPs
  loudly when absent, never silent-passes). statmode_d1 trips it with 32
  regressions; the merit-ramp passes (improves CC shape).
- **D4 — CC_REGULAR fix.** The **merit-ramp (d4a) is promoted to CANDIDATE
  KEEPER**: it fixes the operating-shape failure cleanly (CC_REGULAR cf_emd
  0.099/0.105/0.113 → 0.088/0.098/0.101, r 0.74 → 0.76; `[7c]` 18/18 PASS, no
  class regresses) AND cuts the 2024/25 over-run (+6.31→+5.18, +3.61→+2.77), at
  the cost of CC 2023 over-low (−2.08, a 0.6-TWh fail). Cheapening the duct wall
  (d4b, peak 2.57→1.55×) adds NO shape benefit and worsens volume — rejected.
  Reproducible from `inputs/calibration/offer_curve_deltas_cc_merit_ramp.json`
  alone (no uncommitted mechanism). **This is the same CC delta set already in
  run119** (dashboard probe = merit-ramp + a CPS local-reliability-mustrun
  floor); run119's CPS mechanism + bundle are NOT in the repo, so d4a is the
  reproducible candidate. The residual CC 2024/25 volume over-run is **not**
  offer-closable (gas-price year-gradient + North/SC spatial axis) — confirmed
  across both D4 variants; it needs the spatial lever (run118 overlay measured
  weak; run119 CPS floor measured weak; finer-zone topology still open).
- **Keeper of record stays run115b** (the candidate trades a 2023 volume fail
  for the shape fix; promote when the spatial axis closes the residual). Bundles
  trimmed (dispatch/ + campd dropped) — configs reproduce them.

### 2026-06-15 — ERCOT — spatial reliability-deployment overlay (run118, MEASURED PROBE — weak lever, keeper stays run115b)

**Scope.** Builds the spatial reliability-deployment overlay parked in the
2026-06-15 merit/spatial diagnosis (`docs/spatial-ruc-session-prompt.md`): the
generalization of the CT AS/RUC-deployment overlay to the load-pocket thermal
fleet (CC_REGULAR/COAL/ST_GAS/CC_CHP in South_Central/West/Northeast), scoped on
the load-zone congestion subset. Built on the run115b config **+ the merit-ramp
CC econ deltas** (`offer_curve_deltas_cc_merit_ramp.json`, the orthogonal merit
axis) **+ `--reliability-deployment`**. Bundle
`results/calibration/run118_reldeploy_spatial`.

**Mechanism (built, wired, tested).** `scripts/derive_reliability_deployment.py`
measures, for each CEMS-covered pocket plant and hour, a deployment hour ⇔
`net_mw > min_mw AND LZ_price(plant_zone) > MC AND HB_HUBAVG < MC`
(MC = plant_avg_HR × hr_mult × fuel_price + vom; gas at Henry Hub, coal at its
delivered supply cost; LZ/HB from `actual_lmp_zonal_ERCOT.parquet`). Floor =
measured CEMS net in those hours, else 0. **The wedge lands where the prior
session measured it: 2.70 / 3.60 / 5.22 TWh (2023/24/25)** vs the target
2.7/3.7/4.8 — NOT the ~44 TWh naïve out-of-merit test, confirming the load-zone
congestion scoping. Wired as a sparse per-plant hourly min-gen bound
(`ScenarioConfig.reliability_deployment_overlay` + `_floor_frac`;
`outages.reliability_deployment_floor_for_year`; applied in
`fleet.generators_to_fleet_arrays`, units keep WEFOR/POF). Default off; ERCOT
backcast only; forecast / other ISO byte-identical.

**Result — the floor is mostly NON-BINDING (the key finding).** The min-gen
floor recovers only **~0.3–0.9 TWh/yr of net redistribution** despite flooring
2.7–5.2 TWh, because **the model is already a 7-zone network with per-zone
prices** (not the single-system-price LP the scoping diagnostic assumed), so it
**already dispatches the pocket fleet in the congestion hours**. Measured on the
floored plants directly (2025): plant 56349 floor 566 GWh / model already 327 in
those hours (binding +261); plant 55215 floor 1157 / model already 1012 (binding
+186) — total binding increment **+0.64 TWh**, the rest redundant with the LP's
existing zonal dispatch. Before → after (model TWh by zone):

| year | North thermal | SC thermal | West thermal | North net-exp | West net-exp |
|---|---|---|---|---|---|
| 2023 | 79.2 → 79.0 | 39.3 → 39.5 | 9.7 → 9.8 | 7.5 → 7.3 | 14.1 → 14.2 |
| 2024 | 83.3 → 83.1 | 42.8 → 42.9 | 10.5 → 10.7 | 5.9 → 5.7 | 11.9 → 12.1 |
| 2025 | 82.5 → 82.2 | 37.8 → 38.0 | 11.5 → 11.9 | 11.4 → 11.1 | 6.6 → 6.9 |

All deltas are in the **right direction** (North down, SC/West up; West net-export
up, North net-export down) but ~0.2–0.4 TWh/zone — far too small to close the
+4.5 TWh CC_REGULAR North over-run or the −8.7 TWh SC thermal miss.

**Universal-gate verdict (model grid vs 923−BTM; 0.33% ≈ 1.5 TWh, 0.5% ≈ 2.3).**
No class crosses a gate boundary either way; the fail set is identical to the
merit-ramp base (CC 2024/2025, PRB 2024, CT 2023/2024). The overlay **marginally
worsens** CC_REGULAR in 2024/2025 (d +5.18 → +5.25, +2.77 → +2.85) because the
floored SC/West CC plants add to the CC class total while displacing
coal/CT — i.e. it slightly regresses the very class it was meant to help. In
2023 it nudges CC toward center (−2.08 → −2.02). Gas/coal fuel-split moves are
sub-0.1 TWh (within ±2.5%). LMP unaffected (min-gen bound, LP duals).

**Conclusion — keeper stays run115b.** The price-recoverable congestion wedge is
real (2.7–5.2 TWh of CEMS energy), but the 7-zone LP already dispatches ~85–90%
of it, so a congestion-subset min-gen floor is a near-no-op for the spatial
imbalance. The residual North-over/SC-under gap lives in the **irreducible
RUC/reliability piece** (the ~6.7 TWh that ran below even the local price — the
brief flagged it as NOT price-recoverable) and/or in **inter-zonal flow** the
7-zone TTC network resolves differently from the real intra-zonal pockets. The
real lever is the optional **top-down zone floor sized to the CAMPD−model net
gap (capped at CEMS), or finer zones splitting the Valley/Permian pockets behind
their binding limits** — deferred. The mechanism is committed off-by-default
(reusable infrastructure + the orthogonal merit-ramp CC fix it carries). Logged
as a MEASURED PROBE; not promoted.

### 2026-06-15 — ERCOT — CC_REGULAR within-class misallocation (merit + spatial diagnosis; merit-ramp probe)

**Scope.** The efficient CC_REGULAR plants (Wolf Hollow II 59812, Colorado Bend
II 60122, …) run as a flat baseload block and over-generate — worst in high-gas
2025 (WH2 +21.7%, CF 66 vs CAMPD 54) — while CAMPD shows them cycling all year.
The CC class total passes the old ±5% bar, so this is a within-class
*distribution* problem. This entry records the measured diagnosis (two distinct
axes) and a merit-axis probe; the spatial axis is parked on a data dependency
(see `docs/spatial-ruc-session-prompt.md`).

**New gate (user directive, 2026-06-15).** Replace the size-tiered bar (±5% for
≥20 TWh classes, ±1 TWh for smaller) with a **single universal gate: every
in-scope class, every year, |model−actual| ≤ 0.33% of ISO annual generation**
(≈1.47/1.53/1.61 TWh on ERCOT's 446/463/488 TWh; ~1/300, lands where the prior
±1.5 TWh intuition did and scales with system size). Applied uniformly across
classes and ISOs. Report 0.33% (tight) and 0.5% (~2.3 TWh, the energy-only LP
structural-noise floor: the CT non-CEMS wedge and cheap-gas coal coupling live
there). Under 0.33%, run115b has 5 in-scope fails: CT 2023/2024, **CC_REGULAR
2024/2025 (+6.31/+3.61)**, COAL_PRB 2024 (−4.49).

**Diagnosis — axis 1 (MERIT, flat econ band).** The run-92/96/97a calibration
delta `CC_REGULAR econ_high −0.40` collapsed the econ ramp from its rising
default (econ_low 1.16 → econ_high 1.41) into a flat/inverted block (1.06 →
1.01): with `econ_low ≈ committed` there is no part-load window and no rising
top, so the most-efficient unit's whole ~85% econ tranche sits at the bottom of
the CC merit order and pins flat. Quantified: per-plant miss% correlates with
heat rate −0.75/−0.79/−0.85 (2023/24/25), strengthening with gas price; the
efficient tier (HR ≤ 7.11) over-runs +2.3/+3.4/+5.8% while the high-HR tier
(HR > 8) under-runs −40/−32/−42% — a clean efficient-vs-inefficient mirror.
Outage overlays and tranche sizing were both checked and **ruled out as
causes**: the historic overlay covers CC_REGULAR/CC_CHP/COAL; CAMPD shows WH2/CB2
reaching 0.91–0.93 CF (full availability — not outage-limited, the gap is ~2000
h/yr of unmodeled cycling); and Pct_Committed is unit-specific (CAMPD-P5 min
stable load, WH2 32.3 / CB2 36.6), peaking is per-plant (EIA-860 duct), econ is
the residual.

**Diagnosis — axis 2 (SPATIAL, the larger lever — PARKED).** Thermal miss by
zone (2025): **North +6.1 TWh, South_Central −8.7, West −1.8, Northeast −1.0**;
CC_REGULAR North is +4.5 TWh of the +3.6 class over-run — i.e. most of the
"efficient over-run" is North over-generating. Load allocation is exact (model
zonal demand == ERCOT native-load weather-zone shares). **Inter-zonal TTC is
ruled out**: North→Houston 8000→4810 and halving South_Central imports were both
exact no-ops (the meshed 7-zone network delivers cheap power regardless; TTCs
already match the NP6-86 SCED archive). The binding ERCOT constraints are
intra-zonal pockets the 7-zone model cannot form (NE_LOB 15%, Rio Grande Valley
cluster ≈21%, HMLTN, WHARTN); the under-zone thermal ran 44 TWh "out-of-merit vs
the hub" in 2025 — local congestion the single-system-price reduction misses.
The fix is a **spatial reliability-deployment overlay** (per-plant out-of-merit
floor, generalizing the CT deployment overlay). **UPDATE (2026-06-16):** the
ERCOT zonal/hub prices (NP6-785-ER) ARE in the repo —
`inputs/calibration/actual_lmp_zonal_ERCOT.parquet` (hubs HB_NORTH/HOUSTON/
SOUTH/WEST/PAN/HUBAVG + load zones LZ_AEN/CPS/LCRA/RAYBN/HOUSTON/NORTH/SOUTH/
WEST, RT+DA, 2023–25). They already powered run118's spatial reliability-
deployment overlay (measured a near-no-op: the 7-zone LP already dispatches
~85–90% of the congestion wedge) and run119's CPS local-reliability-mustrun
floor (measured probe, net non-impactful — 6 fails vs run115b's 5). True
finer-zone *topology* (splitting South_Central into AEN/CPS/LCRA, or the
Valley/Permian sub-pockets behind their internal limits) still needs the
sub-zonal TTC limits, not just prices. Full build prompt in
`docs/spatial-ruc-session-prompt.md`.

**Merit-ramp probe (this session).** Restore a rising econ ramp at ~base mean to
fix the flatness without re-fighting the parked spatial/level axis or breaching
2023: `CC_REGULAR econ_low −0.24 / econ_high −0.20` (resolved 0.92 → 1.21, mean
1.065, committed→econ_low gap 0.05, slope 0.29). Deltas saved at
`inputs/calibration/offer_curve_deltas_cc_merit_ramp.json`; all other run115b
knobs unchanged. Result vs the run115b baseline (model TWh, d = model−bench):

| CC_REGULAR | 2023 | 2024 | 2025 |
|---|---|---|---|
| base d | −1.06 | +6.31 | +3.61 |
| merit-ramp d | **−2.08** | **+5.18** | **+2.77** |

Shape (the core complaint) is fixed: WH2 2025 sheds its 0.8–0.9 pin (5158 → 4242
h) and fills the 0.4–0.8 cycling bands (e.g. 0.7–0.8: 8 → 684 h), tracking
CAMPD's spread; WH2 level +21.7 → +17.6%, CB2 +15.6 → +12.8%; efficient-tier
miss +5.8 → +3.5% (2025). **No class regresses** (PRB 2024 −4.49 → −3.97; CC_CHP
/ ST_GAS / lignite all pass; CT unchanged). At the 0.5% gate the fail set is
identical to base (CC 2024/2025, PRB 2024) with every magnitude smaller — a
Pareto merit improvement. The residual CC over-run (2024 coal-coupled cheap-gas
carve-out; 2025 the North spatial axis) is **not** closable by a year-uniform
offer lever — measured: any econ-mean raise large enough to clear 2025 drops
2023 *more* (2023 sheds CC to coal headroom), the documented gas-price
year-gradient. **Kept as a measured probe / config artifact** (not promoted —
keeper stays run115b — until the spatial overlay lands and the merit deltas fold
into a clean-gate keeper).



> **Status update (reconciled with code).** The 2026-05-17 entry below is the *earliest* ERCOT calibration snapshot and is **superseded** by a long line of later runs (the "run14"–"run24" series tracked in the backcast dashboard / `results/calibration/` bundles — render with `/calibration-report`). Crucially, the Gas-CT under-dispatch it blames on "no unit commitment" was the motivation for the **commitment layer that has since been built** (methodology spec §1.6; opt-in `commitment_enabled`), and ERCOT now defaults to CAMPD per-plant binning with tranche offer curves (§3.3). Read the entry below as history, not current state.

### 2026-05-17 — ERCOT — eGRID 2023 calibration parameterization

- **Benchmark:** EPA eGRID 2023 rev2 ERCOT actuals; EIA-930 ERCOT system
  load 2023; EIA Henry Hub spot 2023-2024; EIA-860 2024 plant inventory.
- **Calibration year:** 2023
- **Tolerance:** ±5%
- **Overall:** FAIL — calibration in progress. Most fuels improved but
  remain outside ±5%; a TTC sweep and CC-adder re-tune are still open.
- **Full session detail:** see [`calibration-session-log.md`](calibration-session-log.md).

This run commits the calibration knobs that were derived in ad-hoc
scripts during the session into the codebase as sourced, parameterized
inputs. The session diagnostics below are the post-change results from
`calibration-session-log.md`.

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | FAIL | Gas CC +11%, Gas CT −69%, Coal −12%, Wind +7%, Solar +6.5% (after vintage ramp), Nuclear −1.5%. CO2 −14%. Gas CT gap reflected the pure-merit-order LP with no start-up economics — *since addressed* by the three-solve commitment layer (§1.6); later runs improve this. |
| 2. Price duration curve | Not benchmarked | Model is energy-only (no ORDC/AS); price shape not yet compared to ERCOT RT. |
| 3. Average price | FAIL | Load-weighted avg $21/MWh vs ERCOT 2023 RT ~$48/MWh — expected gap from energy-only formulation. |
| 4. Capacity factors | PARTIAL | Nuclear matches eGRID within 1.5%; efficient CC plants stay inframarginal (no UC), so flagship-plant CFs run high. |

**Findings:**

- The gas price trajectory lacked historical 2023/2024 entries, so a
  2023 run could not anchor fuel cost to the realized Henry Hub spot.
- Renewable capacity was parked in a single zone per technology,
  mis-distributing wind/solar siting vs EIA-860 plant locations.
- Modeled renewable capacity was static year-end; it ignored intra-year
  ramp-in from commercial-operation dates (ERCOT 2023 solar grew
  11.4 GW → 14.9 GW, 45% of additions in Q4). The vintage ramp cut the
  solar generation error from +33% to +6.5%.
- The merit order omitted thermal cycling costs; coal and gas units
  that cycle were dispatched as if cycling were free.
- ERCOT West-Texas transfer limits used placeholder TTCs below the
  2021 RTP stability assessment.
- EIA-930 metered load was used directly as generation-side demand,
  omitting the ~5.8% T&D loss gross-up.

**Actions taken:**

- Added EIA Henry Hub spot 2023 ($2.54) and 2024 ($2.19) historical
  entries to all three `HENRY_HUB_TRAJECTORIES` paths.
- Added `ScenarioConfig.td_loss_factor` (0.058, Tier 3); `load_demand`
  grosses metered load up by `(1 + factor)`.
- Replaced the single-zone renewable allocation with an EIA-860
  plant-location distribution; added `ScenarioConfig.vintage_capacity_ramp`
  (Tier 3) for the month-varying capacity ramp from COD dates.
- Added nine Tier-3 thermal cycling cost adders (gas CC / coal / gas CT
  by efficiency bin) and `apply_cycling_adders`, called after
  `assemble_mc` in the dispatch pipeline.
- Updated ERCOT North→West (3000→5500 MW) and West→Houston
  (2500→3500 MW) TTCs to the 2021 RTP West Texas Export stability
  assessment.

**Open items** (carried from `calibration-session-log.md`): West-export
TTC sweep to produce realistic congestion; CC cycling-adder re-tune at
the final demand level; Gas CT structural gap (needs unit commitment);
coal price verification against EIA-923 Texas fuel receipts.

---

### YYYY-MM-DD — &lt;ISO&gt; — &lt;scenario cache_key&gt;

- **Benchmark:** &lt;source, year&gt;
- **Calibration year:** &lt;year&gt;
- **Tolerance:** ±5%
- **Overall:** PASS / FAIL

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | | |
| 2. Price duration curve | | |
| 3. Average price | | |
| 4. Capacity factors | | |

**Findings:**

-

**Actions taken:**

-

---

### 2026-06-09 — PJM — pjm 2 hydro-ps (results/calibration/pjm_2_hydro_ps)

- **Benchmark:** EIA-930 / EIA-923 / CAMPD, 2023 + 2024; actual hub LMP
- **Calibration years:** 2023, 2024
- **Model changes:** LP budget hydro (76 plants, ~3.3 GW, EIA-923 monthly
  budgets), EIA-860 pumped storage (~5.0 GW, 10 h, RTE 0.80), OTHER must-run
  injection un-gated for non-ERCOT (PS held out), EIA-860 2025 ER fleet
  basis, COAL_SUB dead knob removed (subbit → COAL_PRB). Offer curves carried
  unchanged from `pjm_n6_tuned`.

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | PARTIAL | gas +7% vs 930 (was +10%); coal −12/−16% vs 930 (was −2/−9%) — see findings |
| 2. Price duration curve | PASS | hours >$500: 11 (2023) / 3 (2024), was ~48; slack 9.6 / 1.9 GWh, was 17.7 / 13.5 |
| 3. Average price | PASS | 2023: 28.28 vs 29.33 DA / 28.44 RT actual (old 32.7); 2024: 26.44 vs 29.78 DA (old 31.8). Jul/Aug spike eliminated (29.5/30.1 vs old 45.5/54.5) |
| 4. Capacity factors | PARTIAL | CT_PEAKER 16.5 vs 29.5 TWh actual; COAL_BIT 91.8 vs 105.7 (2024) |

**Findings:**

- The July/August VOLL price spikes were structural scarcity from the missing
  hydro / pumped-storage / OTHER supply, not offer-curve error. With them in
  the LP the price level and shape land on actuals with the *old* curves.
- Coal and CT now under-dispatch because their tuned curves compensated for
  the scarcity regime: peaks are now served by PS (model PS discharge ~9-10
  TWh/yr vs ~3-4 actual — no cycling cost/outages on PS yet), and coal econ
  bands clear less at the lower price level.
- Nuclear +2.4% vs 930 after the EIA-860 2025 ER refresh (fleet revision).
- Oil still ~0 vs 0.6-0.9 TWh actual — needs winter gas (measured monthly /
  per-plant gas pricing) to bind.

**Actions taken / next:**

- Registered `pjm 2 hydro-ps`; dashboard benchmark now regenerates from the
  newest bundle (stale `pjm_8zone` removed).
- Next tuning run: re-tune CT_PEAKER / COAL_BIT bands for the corrected
  system (knobs now route correctly); consider a PS throughput cost or
  availability derate to pull PS toward its ~3-4 TWh actual; evaluate
  `gas_plant_monthly_fuel_pricing` for the Jan-2024 winter spike.

---

### 2026-06-10 — PJM — tuning passes 3-7 (pjm 3 ps-adder … pjm 7 ct-depth)

- **Benchmark:** EIA-930 / EIA-923 / CAMPD, 2023 + 2024; actual hub LMP
- **Recommended baseline: `pjm 6 cc-peak`** (results/calibration/pjm_6_ccpeak)
- **Model changes through the loop:** pumped-storage dispatch adder
  ($10/MWh, reduced-form reserve duty — PS was arbitraging ~2.5x observed);
  `gas_monthly_actuals` (measured EIA-923 ISO-monthly delivered gas — Jan-24
  $5.07 vs ~$2.5 shaped); offer-curve deltas per pass (see run notes).

| vs EIA-923 (2023 / 2024) | pjm 2 | pjm 6 |
|---|---|---|
| CC_REGULAR | +2.5% / +5.3% | **−1.9% / +1.6%** |
| COAL_BIT | −6.1% / −13.1% | **+1.8% / −7.8%** |
| CT_PEAKER | −38% / −44% | **−16% / −21%** |
| Avg LMP (act ~29.3/29.8 DA) | 28.28 / 26.44 | 27.49 / 25.78 |
| Jan LMP 2024 (act 38.0 RT) | 33.9 | **38.7** |

**Findings:**

- Coal's flat monthly deficit was the committed (self-scheduled) tranche
  priced out by the CC econ ramp (15% CF); committed −0.10 fixed 2023 and
  halved 2024.
- CC's duct-firing peak band at 1.62× (~$28) was the summer price ceiling;
  raising it to 2.17× landed CC both years and re-opened CT's window.
- Summer LMP remains low (Jul/Aug 2024 ~30/25 vs ~38/31): the summer
  marginal price sits inside the abundant CC econ ramp — an energy-only
  residual (reserves/congestion/uplift), not an offer-band knob. Pass 7
  (deeper CT, more committed coal) confirmed diminishing returns and a
  2023 coal overshoot; pjm 6 is the keeper.

**Open items:** CT winter/shoulder runtime (−5-6 TWh, commitment/dual-fuel
behavior); ST_GAS 2024 winter (−15%); oil ~0 vs 0.9 TWh; nuclear +2.4%
(EIA-860 2025 ER fleet revision; consider refuel-outage overlay); summer
LMP scarcity component; stale `test_coal_supply_pricing_uses_year_trajectory`
on main (asserts pre-measured-PRB constant).

---

### 2026-06-11 — CAISO — hydro energy budgets + pumped storage (data stage, multi-iso P4)

- **Benchmark:** EIA-923 monthly net generation 2023–2025; EIA-930 CISO
  hydro (cross-check); EIA-860 2025 ER generator schedule.
- **Scope:** data-stage verification + wiring, not a dispatch calibration
  run. The PJM hydro/PS machinery (2026-06-09 entry) is fully generic —
  `load_hydro_budget` / `_hydro_fleet` / `load_eia860_pumped_storage` work
  for CAISO unmodified; this stage verified the CAISO data through them and
  made the PS dispatch adder a per-ISO default.

**Hydro budgets (EIA-923 `HY`, BA = CISO):**

| Year | Plants | Budget (TWh) | EIA-930 CISO hydro (TWh) | Δ |
|---|---|---|---|---|
| 2023 | 166 | 23.90 | 24.40 (incl. PS net — pre-2024 schema doesn't split) | −2.0% |
| 2024 | 160 | 21.48 | ≈22.76 (12.51 Jan–Jun incl-PS + 10.25 Jul–Dec excl-PS) | −5.6% |
| 2025 | 26 | 12.32 (→ 20.39 backfilled) | 21.35 (excl-PS, full year) | −4.5% backfilled |

- Zones resolve cleanly: NP15 136 / SP15 24 / ZP26 6 plants (2023), no
  blanks; NP15 carries >70% of the 6.4 GW nameplate (Sierra/Cascade hydro
  north of Path 26).
- **Wet/dry swing:** the "~2x wet-vs-dry" expectation is 2022 (dry,
  ~12-13 TWh) vs 2023 (extreme wet) — 2022 is outside the data window. The
  measured 2023→2024 swing is +11.3% (23.90 vs 21.48), confirmed by EIA-930
  (~+7%); the budgets preserve it exactly since they *are* the EIA-923
  monthlies. Acceptance (±10% of EIA-923 for 2023/2024) holds by
  construction and is now pinned by `tests/test_hydro.py` regression
  anchors.
- **2025 coverage caveat:** the 2025 EIA-923 vintage is the early release
  (monthly-survey reporters only): 26 of ~185 CAISO plants, 12.3 of
  ~21.4 TWh. `load_hydro_budget(..., backfill_year=2024)` carries
  non-reporters in at their 2024 monthlies → 20.39 TWh (−4.5% vs EIA-930).
  The CAISO 2025 backcast should pass it (and drop it when the final
  annual file lands). Default off, so ERCOT/PJM runs are byte-identical.
- **Small vs large split — not warranted:** ≤30 MW (CAISO RPS small-hydro
  threshold) is 132 plants but only 0.90 GW (14% of capacity) and
  3.10/2.56 TWh (13.0%/11.9% of 2023/2024 energy). Plant-level budgets
  already individuate each small plant, and EIA-930 carries a single hydro
  series to calibrate against, so a structural class split adds nothing
  today. Min-flow floors stay available via `min_flow_fraction` (default 0,
  as PJM); `HydroBudget.monthly_min_energy` now clips the floor to the
  monthly budget so a nameplate-fraction floor can't render a low-inflow
  month infeasible (CAISO small hydro runs dry autumns at a few percent of
  nameplate-hours).

**Pumped storage (EIA-860 prime mover `PS`, BA = CISO):** 2,078 MW, all
NP15 — Helms 1,053 MW (3×351; PG&E rates the upgraded units ~1,212 MW —
EIA-860 nameplate is the model input), W. R. Gianelli 424, Edward C Hyatt
293, J S Eastwood 200, Thermalito 82, O'Neill 25. Fleet-average params per
the PJM pattern: 10 h duration (DOE PSH 2023 fact sheet), RTE 0.80
(DOE/Sandia ESHB).

- **PS dispatch adder is now a per-ISO default**
  (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`): PJM keeps its calibrated
  $10/MWh reserve-duty proxy (2026-06-10 "pjm 3 ps-adder"); CAISO resolves
  to $0 until a CAISO calibration pass measures Helms' reserve/regulation
  duty. `ScenarioConfig.pumped_storage_dispatch_adder` default changed
  `10.0 → None` (= per-ISO); an explicit number still overrides every ISO.
  Note for the run-classifier: configs recorded before/after this change
  differ on this key (10.0 vs null) with identical PJM behavior.

**Open items:** CAISO calibration pass to set (or confirm zero) the CAISO
PS adder once the P-stage backcast runs; revisit the 2025 hydro backfill
when the final EIA-923 2025 annual file lands.

---

### 2026-06-11 — CAISO — P7 gas + carbon (structural, no full run)

- **Scope:** doc-06 pack P7 — measured monthly gas and CA cap-and-trade in
  CAISO marginal cost. Structural inputs only; no calibration bundle (P11
  runs the smoke backcast once the other Wave-1 packs land).
- **Model changes:** `gas_monthly_actuals` default-on for CAISO backcasts
  (`_calibration_config`); CARB allowance price in `resolve_carbon_price`
  via `STATE_CARBON_PRICE_BY_ISO` (default-on, `state_carbon_pricing`);
  border carbon adjustment on the CAISO import tranches
  (`wecc_border_carbon_adder` feeding `build_import_generators`, CARB
  unspecified EF 0.428 t/MWh).

**Findings (EIA-923 Schedule 5, CAISO plants, quantity-weighted):**

- Measured CAISO delivered-gas basis vs Henry Hub annual average:
  **+$7.06 (2023), +$2.26 (2024), +$1.12 (2025)** against the +1.20
  `GAS_BASIS_DIFFERENTIAL` seed. The seed is ~right for 2025, half the
  2024 reality, and misses 2023 entirely — Jan-2023 delivered gas was
  **$38.7/MMBtu** (Dec-22/Jan-23 western gas crisis) vs ~$4.5 shaped.
- Zonal split (the SoCal vs PG&E premium the per-plant path captures):
  implied annual basis NP15 +7.82 / SP15 +5.38 (2023), NP15 +2.20 /
  SP15 +2.42 (2024), NP15 +0.98 / SP15 +1.59 (2025). Caveat: only 6-7
  CAISO plants (~11-14% of gas burn) report Schedule-5 gas costs; the
  nearby-plant fallback fills the rest at the CA *state* mean (CA spans
  both hubs), so zonal price asymmetry reaches only the reporters
  themselves. The ISO-month volume-weighted series is robust to this.
- Carbon: a 7.0 HR CC carries ~$14/MWh of allowance cost at the 2024
  average CARB price ($35.23/t); the import border adder is ~$15/MWh
  (0.428 × allowance). Without these the CAISO price level cannot
  calibrate (doc-06 design decision 5).
- 168 h CAISO smoke (2024): solves Optimal, measured gas + carbon active
  (F923: 22 own-plant, 550 gap-filled generators), January-week average
  price $63.98/MWh, no slack. ERCOT/PJM regression: full test suite
  green; both ISOs resolve a zero carbon price and keep their gas paths.

---

## Cross-class offer-curve tuning Jacobian (2026-06-11)

**Tool:** `scripts/derive_offer_curve_jacobian.py` → `inputs/processed/offer_curve_jacobian.csv`
(long format: `iso, year, out_class, band, in_class, dTWh_per_unit_mult, n_obs, stderr, confidence`).
Pure parquet/JSON analysis of the existing calibration bundles — no LP re-solve. Re-run it
after every new backcast bundle lands; unknown runs are auto-classified (scenario-config
equality + git diff between recorded shas + note keywords) so it keeps working for every
ISO as tuning sequences accrue. (Complements `scripts/curve_class_jacobian.py`, the step-4
quick-look: that tool fits one pooled regression with year fixed effects across all
bundles; this one restricts to verified pure-curve pairs, fits each year separately,
attaches jackknife errors per cell, and adds the adjacency validation + joint-move solver.)

**Method.** From consecutive run pairs whose only difference is offer-curve band-multiplier
moves, collect observations Δ(band multipliers) → Δ(class TWh) per year and fit a
ridge-regularized linear map `Δgen[class] ≈ Σ S[class,(class2,band)]·Δmult[(class2,band)]`,
with leave-one-pair-out jackknife standard errors. Pairs with structural code/data changes
are excluded via a curated registry in the script: Run-63 (storage fix), Run-64 (ER plant
append), Run-66 (CHP BTM trim), Run-68 (measured PRB fuel), Run-69 (CC_CHP eGRID HR
re-base), Run-71 (demand alignment), Run-73 (CHP steam-floor + Petra Nova), Run-74
(regenerated unit-outage extract — config-identical to Run-73 but the note discloses the
data change, so 73→74 is excluded too). Regression inputs: ERCOT 60→61, 61→62, 64→65,
66→67, 69→70, 71→72 plus the two auto-admitted step-2 peak-sweep A/Bs
(peak145→130→160; single-knob CC_REGULAR.peak moves on identical configs) = 8 pairs ×
3 years; PJM pjm 4→5, 5→6, 6→7 (3 pairs × 2 years). Each year is fitted separately (the
2024 vs 2023/2025 asymmetry is gas-price-driven: $2.54 / $2.19 / $3.52 per MMBtu).

**Sanity anchors reproduced** (Run-72→73, structural — sign checks only, all PASS):
CT_PEAKER committed 1.30→1.10 lifted CT_PEAKER +1.62/+2.10/+1.35 TWh (2023/24/25) while
ST_GAS fell −1.75/−2.44/−2.02; COAL_PRB committed/econ_low −0.10 lifted PRB +0.74/+1.31
(2023/24) while COAL_LIGNITE fell −0.70/−0.88.

**Strongest cross-couplings (ERCOT, TWh per unit of multiplier, high/med confidence):**

| Knob | Responds | 2023 | 2024 | 2025 | Reading |
|---|---|---|---|---|---|
| CT_PEAKER.committed | CC_REGULAR | +5.8 | +5.1 | +3.8 | pricing the CT committed band up pushes its energy into the CC residual |
| CT_PEAKER.committed | COAL_PRB | −4.3 | −3.4 | (low) | dearer CTs raise prices into PRB's econ ramp window |
| CT_PEAKER.committed | CT_PEAKER | −2.6 | −2.7 | −2.8 | own-band loss, roughly half of what CC_REGULAR gains |
| CC_REGULAR.econ_high | CC_REGULAR | −3.8 | −3.1 | −2.4 | the big residual marginal class; its econ_high is the single strongest own-knob |
| CC_REGULAR.econ_high | COAL_PRB | +2.7 | +2.5 | (low) | CC econ_high and PRB econ_high overlap the same $23–35 price window |
| CC_REGULAR.peak | CC_REGULAR / COAL_PRB | (low) | −1.9 / +1.6 | (low) | from the step-2 duct-firing peak sweep; the peak band trades against PRB in 2024 |
| COAL_PRB.econ_high | COAL_PRB | −4.1 | −4.4 | (low) | own-band; 2024 strongest (cheapest gas year squeezes the coal window) |
| COAL_PRB.econ_high | CC_REGULAR | +4.4 | +3.7 | (low) | the PRB↔CC substitution is symmetric to the row above |
| COAL_PRB.econ_high | ST_GAS | +1.4 | +1.9 | (low) | second-order spill into steam gas |
| ST_GAS.committed | CT_PEAKER | −1.5 | −1.5 | −1.6 | cheaper ST_GAS committed crowds CTs out (and vice versa) |
| ST_GAS.econ_high | CC_REGULAR | −2.9 | −2.4 | −2.0 | aliased with the co-moved CC_REGULAR.econ_high (n=2) — treat with care |
| COAL_LIGNITE.econ_high | CT_PEAKER | (low) | −1.5 | (low) | lignite econ band trades against peakers in the tight 2024 stack |

PJM (3 pairs, 2023/24 — treat as provisional): CT_PEAKER econ bands are the dominant
knobs (econ_high −21, econ_low −11 TWh/unit own-class, med confidence), with COAL_BIT
committed ↔ CT_PEAKER the strongest cross (+16 TWh/unit, n=2).

**Caveats.** CT_PEAKER.committed and ST_GAS.committed co-moved identically in two of the
ERCOT pairs, so their attributions are partially aliased — the Run-72→73 anchor (where
CT moved without ST_GAS committed) shows the CT committed knob's nearest substitution
partner is ST_GAS specifically; read the CT→CC_REGULAR row as "CT committed energy goes
to the gas mid-merit pool (CC_REGULAR + ST_GAS)". Cells flagged `low` (n_obs<2 or
|coef|<stderr) are not to be trusted individually. The merit-order adjacency check (band
$/MWh range = band mult × class base HR × monthly fuel price, vs the demand-weighted
clearing-price distribution in each bundle's `system.parquet`) confirms every med/high
regression coupling pairs classes whose offer bands overlap where the price distribution
has mass.

**Joint-move recipe.** Given a target error vector `err` (TWh per class-year, model −
EIA-923), the script solves `min ‖S·Δm + err‖² + λ‖Δm‖²` over the four price bands
(knobs with n_obs ≥ 2), box-constrained to per-step moves |Δm| ≤ 0.15, by projected
gradient. Worked example against Run-74's errors
(`python scripts/derive_offer_curve_jacobian.py --iso ERCOT --validate-run Run-74`):

```
Recommended Δmult            Predicted errors (TWh, model − EIA-923)
CC_REGULAR  econ_high −0.150            err now            err predicted
CC_REGULAR  peak      +0.150            2023  2024  2025   2023  2024  2025
ST_GAS      committed −0.150  CC_REG   −6.01 +3.51 −3.19  −4.90 +4.19 −2.16
ST_GAS      econ_high −0.150  ST_GAS   −0.79 −2.83 −1.89  +0.12 −1.98 −0.97
CT_CHP      committed −0.150  CT_PEAK  +0.08 −1.03 −0.44  +0.27 −0.68 −0.30
CT_CHP      econ_high +0.150  PRB      +1.67 −5.14 +3.04  +1.28 −5.39 +3.04
CT_CHP      peak      −0.150  LIGNITE  −0.68 −2.36 +0.26  −0.57 −2.30 +0.27
CC_CHP      econ_high +0.150  CT_CHP   −1.12 −0.72 +2.48  −1.14 −0.72 +2.37
COAL_LIGNITE econ_high −0.150
COAL_PRB    econ_high −0.121
COAL_PRB    committed +0.082
CT_PEAKER   committed +0.069
```

The solver cheapens the under-running classes (ST_GAS on committed and econ_high;
CC_REGULAR econ_high against the 2023/25 under-run, with peak raised to give 2024 back)
and nudges CT_PEAKER committed up against the residual over-run — but the mixed signs
across years (CC_REGULAR −6.0/+3.5/−3.2, PRB +1.7/−5.1/+3.0) are the honest limit of
what any single multiplier move can fix: those need year-dependent levers
(gas-price-keyed shaping), not more band tuning. Re-derive the matrix and recipe after
each run; one solved joint move per iteration replaces the sequential single-knob walk.

---

## ERCOT E2 — storage realism + nuclear refuel overlay (2026-06-11)

**Scope (E2 backlog, doc 06 §6):** the LP over-cycled the ERCOT BESS fleet
("PS 9–10 TWh vs 3–4" in the audit shorthand; ERCOT has no pumped storage —
the resource is grid batteries) and coal/CT band tuning had absorbed part of
the error; nuclear ran with a refuel question mark. PJM untouched.

**New instrumentation (this session):** calibration bundles now persist
per-unit hourly storage charge/discharge (`storage.parquet`, P1/P2) and an
EIA-930 battery benchmark (`NG: BAT` discharge / `NG: UES` charge; NaN kept
over unreported hours), with a report §3d comparing the model over the
benchmark's reported window. ERCOT coverage: 2025 ≈ full year (5.44 TWh
discharge / 6.67 charge), 2024 ≈ 19% (Nov–Dec window, 0.72 TWh), 2023 none.
`meta.json` also records `highspy_version` (see finding 3).

**Runs** (P1, `--storage-daily-cycling`, Run-77 offer-curve deltas unless
noted; bundles `e2_1_storage_base`, `e2_2_adder20`, `e2_3_adder10`,
`e2_4_retune`; the last two are dashboard `run78 battery adder` /
`run79 storage retune`):

| | model dis TWh 2023/24/25 | vs measured |
|---|---|---|
| e2 1 adder $0 (baseline) | 1.90 / 4.72 / 8.09 | 2025 +48%, 2024 window +33% |
| e2 2 adder $20 | 0.22 / 0.37 / 3.03 | 2025 −44% (overcorrected) |
| e2 3 adder $10 | 1.05 / 1.35 / 5.34 | **2025 −2.0%**, 2024 window −52% |
| e2 4 = e2 3 + band re-tune | 0.99 / 1.40 / 5.36 | **2025 −1.5%** |

**Keeper: e2 4** — `battery_dispatch_adder = 10.0` $/MWh discharged (same
magnitude as the PJM pumped-storage adder; reduced-form cycling degradation +
ancillary-service opportunity cost) plus a Jacobian joint-move re-tune of the
non-CHP bands targeting e2 3's residuals (CHP knobs held per the Run-77
discipline): CC_REGULAR econ_high −0.15 / peak +0.15; COAL_PRB committed
+0.110 / econ_high +0.15 / peak +0.028; COAL_LIGNITE econ_low +0.15 /
econ_high −0.087; ST_GAS committed −0.15 / econ_high −0.15; CT_PEAKER
committed −0.094.

| vs EIA-923 incl. BTM (e2 4) | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −1.3% | +2.9% | +0.9% |
| COAL_PRB | −0.8% | −9.9% | −1.5% |
| COAL_LIGNITE | −12.8% | −23.8% | +0.7% |
| CT_PEAKER | −2.6% | −12.8% | −2.9% |
| ST_GAS | +7.4% | −2.7% | +2.8% |
| nuclear | −0.7% | −0.7% | −0.7% |
| coal hourly Pearson r (NRMSE) | 0.940 (0.171) | 0.905 (0.229) | 0.808 (0.162) |
| battery discharge vs 930 window | n/a | −55% (19% cov.) | **−1.5%** |

**Findings:**

1. **The storage error was real and the bands were carrying it.** Killing the
   over-cycling alone (e2 1 → e2 3) recovered CT_PEAKER from −22/−43/−14% to
   −20/−36/−11 and ST_GAS similarly — the rest of the CT/ST deficit is not
   storage, it is the E1 winter/cheap-gas pricing item. With the re-tune on
   top, 2023 and 2025 land essentially everywhere in tolerance (lignite 2023
   excepted) while 2024 keeps the familiar cheap-gas coal deficit
   (PRB −9.9%, lignite −23.8%) that measured monthly gas (E1) owns.
2. **One adder cannot fit both 2024's shoulder window and 2025.** The $10
   value anchors the only full-coverage measured year (2025, −1.5%); the
   Nov–Dec 2024 window runs −55% partly because the model's year-end EIA-860
   fleet (8.1 GW) understates the actual late-2024 fleet and the window is
   shoulder-season (shallow spreads sit right at the adder threshold). A COD
   month intra-year fleet ramp (CAISO P5 pattern) is the structural fix if
   the window matters later.
3. **Reproducibility caveat (important for every future ERCOT pass):** the
   Run-77 config re-run in this session's environment did NOT reproduce
   Run-77's class splits (COAL_PRB 2023 +14% vs Run-77's ~+1%; totals equal
   to 0.01 TWh; duals ±$1 in the cheap-gas years, +$0.08 in 2025). Cheap gas
   puts PRB committed bids on top of gas committed bids — a near-degenerate
   plateau where alternate optimal vertices exist, and a different (then-
   unrecorded) HiGHS build picks a different one. `meta.json` now records
   `highspy_version` (this session: 1.14.0); the keeper's COAL_PRB committed
   +0.110 also lifts that bid off the tie, which should make the split less
   solver-sensitive going forward. Consider pinning `highspy` in
   `pyproject.toml` if cross-machine reproduction matters.
4. **Nuclear was already fixed and is now provably data-derived.** The
   per-year EIA-923 monthly-CF overlay (`NUCLEAR_MONTHLY_CF_BY_YEAR`, PR
   #252) holds nuclear at −0.7% in all three years (the audit's +2.4%
   predates it). New `scripts/derive_nuclear_monthly_cf.py --check`
   regenerates and validates the table from EIA-923 (ERCOT 2023–2025
   reproduce exactly); the residual −0.7% is the CF≤1.0 cap vs winter net
   capability above EIA-860 nameplate — accepted.

**Open items:** lignite 2023/2024 deficit and ST_GAS 2023 +7.4% (both
gas-price-keyed, → E1 measured monthly gas); CT_CHP 2025 +28% is the known
incomplete 2025 CHP benchmark, not a model change; storage intra-year fleet
ramp (finding 2) if the 2024 window becomes a target.

---

## ERCOT Runs 80–81 — coal tuning: lignite price sweep + PRB sigmoid probes (2026-06-11)

**Scope:** the run-79 lignite deficit (−12.8% / −23.8% / +0.7% vs EIA-923,
2023/24/25) and PRB 2024 (−9.9%). Five bundles: `run80a_code_baseline`,
`run80b_lignite_105`, `run80c_lignite_115`, `run80d_prb_floor_068`,
`run80e_prb_shaped`. Dashboard: `run80 lignite 1.15` = bundle
`run80c_lignite_115`; `run81 prb floor` = bundle `run80d_prb_floor_068`
(both registered as rejected probes; the config of record stays run 79's).
PRB sigmoid held at run-79 defaults in the lignite probes; lignite held at
the measured $1.45 in the sigmoid probes.

**Rebaseline (`run80a_code_baseline`).** The exact run-79 config re-run on
current main reproduces run 79's class table to the reported precision in
every class-year: the post-run-79 merges (E3 HSL loader unification,
curtailment report unification, CAISO/PJM-gated loader work) do not move
ERCOT P1 dispatch, and the solve reproduces under highspy 1.14.0 (the
run-77 caveat does not bite here). Not dashboard-registered (numerically
identical to run 79).

**Lignite price sweep (run 80, bundles 80b/80c) — reverted.** Mine-mouth lignite repriced
$1.45 → $1.05/$1.15 (marginal-extraction-cost framing; mine fixed costs
sunk under take-or-pay):

| lignite vs EIA-923 | 2023 | 2024 | 2025 |
|---|---|---|---|
| $1.45 (run79/80a) | −12.8% | −23.8% | +0.7% |
| $1.15 (80c) | +1.9% | −10.6% | +2.2% |
| $1.05 (80b) | +6.2% | −5.0% | +2.2% |

No single price fits both cheap-gas years (the 2023↔2024 trade is
year-keyed), and the cheap-lignite probes bleed PRB (2024 −9.9 →
−11.3/−11.8) and CT_PEAKER share. Decision: keep lignite at the measured
$1.45 — it is grounded in operator/EIA cost data. (Hourly coal NRMSE did
improve under the reprice — 2024 0.229 → 0.202 — recorded for any future
revisit.)

**PRB sigmoid probes (run 81, bundles 80d/80e) — negative result, parameters stay.**
80d cut the cheap-gas floors one step (baseload 0.78 → 0.68, follower
0.68 → 0.58): the gradient is strong (~+4.4 TWh PRB per −0.10 floor in
each cheap-gas year) and 2024/2025 land at +0.1%/0.0%, but 2023 overshoots
−0.8 → +9.0% and the gain displaces CT_PEAKER (2024 −12.8 → −19.4) and
ST_GAS (−2.7 → −8.3) rather than only CC_REGULAR's over-run — net all-class
error worsens in 2023 and 2024. 80e reshaped the logistic
(floor 0.68 / ceil 1.42 / mid 2.65 / slope 3.6, via the new
`--prb-gas-mid`/`--prb-gas-slope` flags) to hold 2023/2025 at run-79
passthrough while keeping 80d's 2024 discount; it failed (PRB 2023 +10.8%)
for a structural reason: **2023's cheap months (gas $2.29–2.45) overlap
2024's range, so no gas-keyed curve can discount 2024 without discounting
a third of 2023.** Annual-average anchors do not hold in monthly space.

**Finding — the PRB residual is two plants, not the curve.** Per-plant
(model − CAMPD, GWh): W A Parish −2064/−3858/−2456 and J K Spruce
−1289/−1728/−1253 under-run in *all* years including dear-gas 2025, masked
at class level by Martin Lake / Sandy Creek / Limestone overshoots. The 80d
floor cut reached the wrong plants (Martin Lake +209 → +1705 in 2023) and
left Parish at −2847 in 2024. Parish (15% MR) and Spruce (12% MR) carry the
lowest must-run floors in `COAL_MUSTRUN_BY_PLANT`; Parish is additionally
the mixed gas/coal facility where coal outages are CAMPD-undetectable.

**Open items:** per-plant Parish/Spruce correction (must-run floors or a
`--plant-tranche-config` sheet row) is the right next coal lever — the
fleet-wide sigmoid is the wrong altitude; lignite 2023/24 and the
remaining 2024 coal deficit stay with E1 (measured monthly gas,
`--gas-monthly-actuals` is now wired); CT_CHP 2025 +28% unchanged
(incomplete 2025 CHP benchmark).

---

## ERCOT Run 82 — Jacobian joint move; BTM-aware CHP panel (2026-06-11)

**Run 82 (`run82_jacobian_joint`, dashboard `run82 jacobian joint`) —
rejected.** The derive_offer_curve_jacobian recipe vs the run-79 error
vector (non-CHP knobs, |Δ| ≤ 0.15) predicted total |err| 28.5 → 25.4 TWh.
Actual: PRB 2023 0.0%, CC_REGULAR 2024/25 and ST_GAS 2023 improve — but
CT_PEAKER explodes to +20.9/+14.2/+21.0% (was −2.6/−12.8/−2.9). Cause: the
recipe's CT_PEAKER committed −0.132 stacked on run-79's −0.34 (cumulative
−0.47 below the calibrated default, mult 1.14 → 0.67) crossed a merit-order
step far outside the regime the matrix sampled. The keeper stays the run-79
config. **Lesson: the Jacobian solves annual class TWh only (no hourly
shape), and its linearization fails when a recipe move stacks onto a knob
already far from the sampled neighborhood — cap cumulative moves and
re-derive locally first.**

**BTM-aware per-plant CHP panel (reporting fix).** The [7]/[7b] per-plant
fit compared grid-facing LP dispatch against whole-plant CAMPD net — for
CHP plants the 35–50% behind-the-meter host-supply share made high CF bands
unreachable by construction (the fleet-wide "CC_CHP has 0 hours above 0.8
CF" read was substantially this artifact). `_plant_hourly_fit` now adds the
flat BTM MW back in hours the grid share runs (Petra Nova excluded — own
parasitic treatment). Honest residuals after the fix (run80a bundle panels
regenerated):

* **CC_CHP**: band overlap improves (Deer Park 0.50 → 0.68, Baytown
  0.48 → 0.62); remaining miss is the model being too *binary* — it
  under-occupies CAMPD's 0.2–0.5 CF range (partial-train operation below
  the modeled must-run floor) and over-occupies 0.9–1.0.
* **CT_CHP**: the original diagnosis survives the fix — CAMPD spends 25%
  of hours above 0.8 CF, the model 1.7%; the model parks at 0.6–0.8. The
  top ~20% of CT_CHP capacity is priced out (econ_high/peak mults plus the
  P1 startup markup, which CHP bins currently pay despite steam-host
  obligations covering their starts).

**Next (run 83 candidates):** exempt CHP classes from the startup
amortization markup (steam host keeps units hot — model bug, not a tuning
knob); then re-read the CT_CHP top bands and CC_CHP partial-train range
against the BTM-aware panel before any tranche-share (pct_peaking) move.

---

## ERCOT Run 83 — CHP startup exemption: no-op, mechanism ruled out (2026-06-11)

**Run 83 (`run83_chp_startup`, dashboard `run83 chp startup`).**
`chp_startup_covered` (CC_CHP/CT_CHP/ST_CHP exempt from the P1 startup
markup) reproduces run 79 exactly in every class-year. Root cause of the
no-op: the bin builder assigns startup cost to the **committed tranche
only** (econ/peak tranches carry 0.0), and CHP committed tranches run
continuously on their must-run floors, so their monthly amortization was
already ~$0/MWh. **Finding: startup cost is ruled out as the cause of the
CT_CHP top-band miss** (BTM-aware panel: CAMPD 25% of hours above 0.8 CF
vs model 1.7%); the miss is the CT_CHP band economics (econ_high 1.30 /
peak 1.32 on high CT heat rates) and/or tranche shares (pct_econ 32 /
pct_peak 5) — a CHP offer-curve/tranche item for the next pass. The flag
stays available (harmless, default off, correctly recorded in run_config
since the prb_overrides recording fix). Keeper remains the run-79 config.

---

## ERCOT Run 84 — coal sigmoids: lignite passthrough + PRB floor retune (2026-06-12)

**Run 84 (`run84_coal_sigmoids`, dashboard `run84 coal sigmoids`) —
rejected, but the lignite mechanism works.** One run, two coal moves on
the run-79 keeper config:

* **(A1) Gas-keyed lignite passthrough sigmoid** (new
  `--coal-lignite-sigmoid`; floor 0.70, ceil 1.00, mid 2.85, slope 2.5 —
  defaults derived from the run-80 flat-reprice anchors: $1.15 ≈ pt 0.79
  fixed 2023, $1.05 ≈ 0.72 fixed 2024, 2025 wants full cost). Mine-mouth
  take-or-pay fixed costs are sunk, so the BID discounts in cheap-gas
  months; the measured $1.45/MMBtu delivered-cost constant is untouched.
  Implementation mirrors the PRB/bit sigmoids end to end
  (`coal_lignite_passthrough_*` in ScenarioConfig,
  `lignite_passthrough_series`, a lignite route in
  `campd_tranche_fuel_frac`; must-run tranches stay VOM-only).
* **(A2) PRB sigmoid floor −0.05** (baseload 0.78 → 0.73, follower
  0.68 → 0.63) — half the run-81 floor gradient (+9.8/+10.0/+1.5 PRB
  points per −0.10), aiming to spread PRB error across years.

**Result vs keeper (2023/24/25):** lignite −12.8/−23.8/+0.7 →
**+5.4/−5.0/+2.1** (balanced, all within ±6 — the sigmoid does what the
flat reprices couldn't, holding 2025 at full cost); PRB −0.8/−9.9/−1.5 →
+1.9/−7.3/−0.9; Martin Lake/Limestone land +0.5/+0.2 TWh over CAMPD (not
the run-81 blow-up); Parish/Spruce structural deficit unchanged (out of
scope). **Rejected on gas collateral:** the cheap 2024 coal eats the gas
classes — CT_PEAKER 2024 −12.8 → −18.6, ST_GAS 2024 −2.7 → −7.2, both
beyond the ~2-point bar. Keeper stays run 79.

**Next:** soften the 2024 discount — lignite floor ~0.75–0.78 and/or the
PRB floor scale nearer 0.4 (floors 0.74/0.64) — and re-read the
CT_PEAKER/ST_GAS columns. (Run 83's `--chp-startup-covered` was a no-op —
see its entry above — so there is nothing to fold into a run-85 candidate
from that probe.) Per-supply sigmoid note (2026-06-12): every coal supply tag now
carries its own independently tunable sigmoid family — PRB
(+follower tier), bituminous, lignite, and a new subbituminous split
(`--coal-sub-sigmoid`, default = inherit PRB exactly as before) — since
each encodes basin/type/transport-specific contract economics.

## Jacobian tool v2 — dispatch-shape + LMP objectives, trust region (2026-06-12)

`scripts/derive_offer_curve_jacobian.py` now regresses three error blocks
per pure pair instead of annual TWh alone:

* **twh** — annual class TWh (unchanged, BTM-aware);
* **shape** — hourly NRMSE of non-CHP gas and coal vs EIA-930 (the [5]
  table convention) plus the mean panel-plant CF-band EMD from
  `plant_cf_bands.parquet`;
* **lmp** — demand-weighted monthly |model − actual RT| from
  `system.parquet` vs the committed `actual_lmp.json` reference.

The joint-move recipe minimizes a weighted sum (`--w-twh/--w-shape/
--w-lmp`, each block normalized to its `--baseline` magnitude, default
run-79) and prints the predicted change PER BLOCK, so a TWh fix that
degrades shape or LMP is visible before any LP solve. A **trust region**
zeroes any knob whose post-move resolved multiplier would exit the value
range actually sampled by the pure pairs (with a "re-derive locally first"
warning) — the run-82 failure mode. Back-test
(`--backtest e2_4_retune run82_jacobian_joint`): the trust region flags
the CT_PEAKER committed move (post-move 1.008 vs sampled [1.140, 1.480]),
and the twh block underpredicts its actual effect (+1.1 vs +2.2 TWh 2024)
— exactly the extrapolation nonlinearity the region guards against.
`inputs/processed/offer_curve_jacobian.csv` is schema v2 (new `metric`
column; `metric == "twh"` reproduces v1). Registry additions classify the
e2/run80/run82 chain (run80b–e as sidecars off run80a — 80d/80e
run_configs predate the sigmoid-provenance fix and must not be trusted for
sigmoid params); config-presence diffs with inert defaults no longer
downgrade pure pairs. Shape/LMP sensitivity cells start data-poor
(historical pairs moved knobs for TWh reasons) and carry the existing
n_obs/stderr confidence flags; expect the LMP block to act as a guardrail
rather than a driver.

---

## NEISO 1 — smoke backcast 2024 (P11, structural-checklist pass) (2026-06-12)

**Run `neiso_smoke_2024`, dashboard `neiso 1 smoke`** — the first NEISO
full-bundle backcast. `run_calibration.py --iso NEISO --year 2024` (fast P1
fuel-mix smoke) then `run_calibration_full.py --iso NEISO --year 2024
--commitment --out-dir results/calibration/neiso_smoke_2024` (P1+P2). All
NEISO structural toggles fire by default in the calibration harness
(`_calibration_config`): `gas_monthly_actuals`, the Algonquin `gas_hub_basis_overlay`,
`dual_fuel_switching`, and RGGI via the state-carbon program (carbon_price=0
→ resolve_carbon_price). Solve logs confirm them live: *254 dual-fuel gas
tranches (6068 MW) capped at the delivered oil price; 20 plants priced from
own F923 + 286 nearby-gap-filled.* **Prereqs:** P0–P9, P13, P2 merged; **P10
held on the LMP upload — no `actual_lmp.json` NEISO block, so the price
benchmark is level-only this pass (modeled level reported, not scored).**
This is a structural-discipline pass (playbook §6): **no offer-band tuning** —
a structural row is red and is filed, not tuned.

### Headline numbers (P2, full bundle)

| Metric | Model | EIA-923 | EIA-930 | Read |
|---|---|---|---|---|
| gas (TWh) | 67.81 | 60.99 | 59.64 | **+11.2% vs 923 — the import wedge** |
| nuclear | 26.48 | 26.55 | 26.41 | ✓ −0.3% |
| hydro | 6.67 | 6.71 | 7.39 | ✓ vs 923 (−9.7% vs 930) |
| wind | 3.45 | — | 3.45 | ✓ (judged vs 930) |
| solar | 1.31 | (4.53) | 1.31 | ✓ vs 930; 923 carries BTM PV — basis artifact, not a miss |
| oil | 0.24 | 0.31 | 0.37 | order-of-magnitude OK; **summer-peaker-weighted, under-burns winter** |
| biomass | 5.16 | — | (eGRID 5.53) | ✓ must-run injection |
| coal | 0.00 | 0.25 | 0.24 | lone Merrimack unit never dispatches (trace) |
| net interchange (TWh) | **0.00** | — | **−10.30** | **RED — wedge entirely unserved** |
| avg price ($/MWh) | 69.99 | — (P10 held) | — | biased high by unserved imports; duration max $292 / p90 $134 / p50 $46 |
| CO2 (Mt) | ~31.5 | eGRID-2023 25.1 | — | downstream of gas; +year-mismatch (eGRID is 2023, gas 53 TWh) |
| PS throughput (TWh) | 1.35 | — | 0.30 | **over-cycles 4.5×** |

### Ranked gap list (structural-checklist order; hypotheses + owning pack)

1. **[RED · demand→interchange] Net interchange is not served on the default
   backcast path.** `load_demand` nets the measured interchange schedule only
   for ERCOT and PJM (`pjm_net_interchange`); NEISO falls through with
   `interchange = 0`, so the LP serves the full 114.5 TWh of metered demand
   internally. ISO-NE is a steady net importer of **−10.30 TWh (−1175 MW avg,
   9% of demand)** — the HQ Phase II + NB + NYISO wedge — and that wedge is
   instead generated by **gas (+6.8 TWh, +11% vs 923)**. The report's [2] line
   reads `model 0.00 TWh (energy-only; no external interchange node)` against
   `actual −10.30 TWh`. Two confirming experiments bracket the truth:
   the default path serves **0** imports (gas +11%, price $70); a
   `--priced-interchange` diagnostic (`neiso_smoke_2024_priced_ix`, not a
   keeper) **over-imports −23.51 TWh** (100% of hours vs actual 83.8%) because
   the HQ tranche ($18/MWh) undercuts gas in nearly every hour, dropping gas to
   45.0 TWh (−26%), oil to 0, and price to $48. Serving the *measured* −10.3
   TWh schedule sits between and lands gas ≈ 60.3 TWh — right on the EIA-923
   60.99. **Hypothesis:** wiring the measured ISNE net-interchange into demand
   (subtract the −10.3 TWh schedule) closes the gas overshoot and pulls the
   price level down toward reality; the priced node remains the *forward*
   mechanism and is validated separately. The offline priced-node fit RMSE is
   already **266 MW** (optimal placement), vs 1563 MW live — so the tranche
   *capacities* fit; the live miss is tranche *price levels* relative to the
   modeled gas, i.e. a calibration item, not a structural one.
   **Owner: P9** (wire `neiso_net_interchange` into `load_demand`, PJM
   precedent; or calibrate the priced-node tranche prices and run NEISO
   backcasts with `--priced-interchange`). **This blocks everything below —
   do not tune offer bands until it is fixed.**

2. **[AMBER · hydro/PS/storage] Pumped storage over-cycles 4.5×.** Northfield +
   Bear Swamp discharge **1.35 TWh modeled vs 0.30 TWh EIA-930** — pure
   price-arbitrage over-cycling, the documented PS failure mode (playbook
   §8.4). Grid batteries also over-cycle (0.27 vs ~0.01 TWh; evening-discharge
   share 86% vs 30%) but the fleet is small. **Note the cross-coupling:** under
   `--priced-interchange` PS self-corrects to exactly 0.30 TWh — cheap imports
   remove the arbitrage spread, so part of gap #2 is a *symptom* of gap #1.
   **Hypothesis:** re-measure PS/BESS throughput after interchange is served;
   if still high, apply the `battery_dispatch_adder` / PS throughput cost
   (default 0 today). **Owner: P4 (PS) / P5 (BESS), after P9.**

3. **[AMBER · gas+AGT+RGGI → dual-fuel/oil] Oil holds at magnitude but is
   season-shifted.** Modeled oil **0.24 TWh** at full-bundle scale — exactly
   P13's 2023 figure (0.24 vs 0.39) and the task's confirm-it-holds check:
   **it holds — not near-zero**, vs EIA-923 0.31 / EIA-930 0.37 (2024). But the
   monthly shape is wrong: oil burns **Jul 148 / Aug 35 / Jun 23 GWh (summer
   peaker scarcity) vs only Jan 17 / Feb 11 / Dec 5 GWh (winter)**. ISO-NE's
   real oil is winter-cold-snap-concentrated. Root cause is the **documented
   P13 limitation**: the committed AGT basis is *monthly*, and monthly averages
   never reach distillate parity (~$18/MMBtu; max Jan-2025 $16.9), so the
   dual-fuel CT/ST switch is wired but does not trip on monthly data — winter
   oil comes only from oil-steam scarcity dispatch. A winter price tail *does*
   exist (duration max $292, p90 $134) but is under-fed on the oil side.
   **Hypothesis:** a daily-AGT basis (upload U4 refinement) would trip the CT
   switch in cold snaps and move oil from summer to winter. **Owner: P7/P13
   (daily AGT basis, U4).** Not blocking the smoke; magnitude is acceptable.

4. **[INFO · price level/duration] Cannot be scored — P10 held.** No NEISO
   `actual_lmp.json` block, so the modeled level ($69.99 default; $48.19 with
   priced imports) is reported, not benchmarked. All five zones price
   identically ($69.99) — **no Boston/CT congestion separation**: the Tier-3
   RSP TTC seeds are non-binding and there are no measured interface limits
   (U6). The $70 default level is biased high by gap #1. **Owner: P10 (U2 LMP
   upload for the level/duration benchmark; U6 for TTC/congestion).**

5. **[INFO · trace] Coal 0.00 vs 0.25 TWh.** The single ~108 MW Merrimack-area
   coal unit never clears; trace, no action.

### Keeper decision

`neiso 1 smoke` registered as the NEISO baseline (first run; top-5 retention
not yet engaged). **Not a calibration keeper for tuning** — gap #1
(interchange) is a structural blocker that must be fixed in P9 before any
offer-band / hydro / gas-basis knob is moved in P12. The fast-P1 smoke and the
P2 bundle agree on the diagnosis; the `--priced-interchange` diagnostic bundle
(`neiso_smoke_2024_priced_ix`) is retained on disk as the bracketing evidence
for gap #1 (not registered — it is a confirmation, not a numbered run).

---

## NYISO P11 — Smoke backcast 2023: structural gap report (2026-06-12)

First NYISO calibration pass (playbook §6 smoke). Year **2023** (full CEMS;
2024 blocked on `NY_2024`, upload U1). Prereqs P0–P9 + P13 merged; **P10 held
on the LMP upload (U2)** — price calibration is **level-only** this pass (no
actual-LBMP duration / zonal-spread comparison). Bundles:
`results/calibration/nyiso_smoke_2023` (dashboard `nyiso p11 smoke 2023`) and
the diagnostic `nyiso_smoke_2023_priced` (dashboard `nyiso p11 diag
priced-interchange`). Per-run detail in
`results/calibration/nyiso_smoke_2023/SUMMARY-nyiso-p11-smoke.md`.

**Headline — one structural miss, not a band problem.** The energy-only
backcast over-generates **+16% on total** (147.31 vs 126.96 TWh EIA-923),
*entirely* in gas (80.11 vs 63.79 TWh, +25.6%). NYISO is a ~16%-of-load net
importer (actual net interchange **−23.45 TWh**, EIA-930) and the default
backcast serves **0 TWh** of imports — `_load_nyiso_hourly_demand` deliberately
does not fold interchange into demand (defers to the priced node, §8.2), and the
priced node only builds under `--priced-interchange`. So the ~24 TWh import
wedge is displaced onto in-state gas. Hydro (−0.1%), nuclear (−0.1%), wind
(−3.6%) are dead-on. **No offer band was tuned** (playbook discipline:
structural rows red).

**Confirmation (`--priced-interchange`).** The P9 node (5 tranches / 5900 MW)
reclaims the whole wedge with no band change: gas 80.11 → **55.51 TWh** (−13%
vs 923), net interchange 0 → **−25.41 TWh** (vs −23.45 actual; import-hours
100% match, diurnal corr +0.80, duration RMSE 442 MW), total 147.31 → 121.75
TWh, avg price $71 → $40/MWh. The energy-only gas_ct +81% / gas_st +113% /
CO2 +57% reads are interchange symptoms.

**Ranked gap list (structural-checklist order; owning pack per fix):**

| # | Row | Status | Finding | Owner |
|---|---|---|---|---|
| 1 | demand / net-load | 🟢 | served = demand 147.05 TWh; FoM convention correct; zonal shares Tier-3 Gold-Book static (U3 not uploaded) | P8 (U3) |
| 2 | **net interchange** | 🔴 dominant | serves 0 vs −23.45 TWh; ~24 TWh dumped on gas; priced node closes it | **P9** |
| 3 | hydro + storage | 🟢 | hydro 28.38/28.40, budget honored; nuclear −0.1%; PS/BESS plausible but unbenchmarked (no EIA-930 BAT/PS column) | — (P5 data gap) |
| 4 | gas + RGGI level | 🟡 | RGGI $13.49/t active; gas on flat HH $2.54 seed (`--gas-monthly-actuals` off, U4 basis absent); level unvalidatable (P10 held) | **P7** |
| 5 | dual-fuel / outages | 🔴 | dual-fuel active (385 tranches/15.9 GW) but oil 0.15→0.00 vs 0.42 (923)/2.17 (930) — flat gas never crosses oil parity; outage overlay healthy (318 derated) | **P13 + P7** (U4) |
| 6 | offer-curve bands | ⏸️ not tuned | rows 2/4/5 red → untouched; gas_ct/gas_st collapse to tolerance once imports served | P2/P12 |

**NYISO watch items:** hydro displacement 🟢 (lands at budget); downstate
congestion separation ⚪ not validated (modeled spread ~$0.5–1.5; P10/U2 held —
cannot compare J−A/K−A LBMP; interface TTCs may need U7); winter dual-fuel 🔴
(gated on U4 winter basis; Jan/Feb actual oil ~365/~454 GWh).

**Next (in order):** (1) P9 serve interchange in NYISO backcasts — default-on
priced node or fold the measured EIA-930 schedule into demand (PJM precedent),
then refine the low-import tail / ~8% over-import; (2) P7 enable
`--gas-monthly-actuals` + U4 winter basis; (3) P13 re-validate winter oil once
U4 lands; (4) P10/U2 + P8/U3 uploads for price/separation/zonal load; (5) only
then (P12) offer-curve bands. Keeper config: none yet — P11 is the structural
diagnosis, not a tuning pass.


## ERCOT Runs 85–87 — coal–gas split + LMP localization (2026-06-12)

**Scope.** Resolve the run-84 finding that any coal bid discount adds coal TWh
by taking them from the wrong gas classes (CT_PEAKER/ST_GAS, already short),
not CC_REGULAR's surplus — three combos (85/86/87) — plus an hourly LMP
residual diagnosis (the 2023 price level is ~$24 modelled vs ~$48 actual).
All three runs rejected; the keeper stays run 79 (`e2_4_retune`). Dashboard:
`run85 coal soft`, `run86 coal gas realloc`, `run87 gas monthly`
(85→prunes run80, 86→run81, 87→run82, top-5 retention).

**New data artifact — ERCOT hourly actual LMP.** `scripts/derive_actual_lmp.py`
now emits `inputs/calibration/actual_lmp_hourly_ERCOT.parquet` (the HB_HUBAVG
hub-average, DAM hourly + RTM 15-min averaged to the hour, on the model's
fixed non-leap 8760 calendar — Feb 29 dropped, DST fall-back averaged via the
repeated-hour rows, spring-forward NaN). The annual/monthly mean formulas are
untouched so `actual_lmp.json` does not drift (verified by diff); ERCOT gains
`da_pct`/`rt_pct` like PJM/CAISO. This unblocks `scripts/analyze_lmp_residual.py`
for ERCOT.

### Run 85 — softer coal dose (REJECTED, dose-response anchor)
Run-79 config + `--coal-lignite-sigmoid --lignite-floor 0.75 --lignite-ceil
1.00 --prb-floor 0.74 --prb-follower-floor 0.64` (about half the run-84
discount). Lignite recovers to **+2.3/-8.8/+1.9** (keeper -12.8/-23.8/+0.7;
run84 +5.4/-5.0/+2.1) — 2024 did not slide past -10 — and the hourly coal/gas
dispatch shape *improves* (coal NRMSE 0.171/0.229 → 0.151/0.198). But the 2024
gas collateral fails the bar: **CT_PEAKER -17.9** (keeper -12.8), **ST_GAS
-6.5** (keeper -2.7), barely better than run-84's -18.6/-7.2 despite half the
dose. 2024 ledger: coal +2.95 TWh (lignite +2.10, PRB +0.85) taken from
CC_REGULAR -1.14 **and** ST_GAS -0.70 / CT_PEAKER -0.42 — the donor mix is
unchanged from run 84, confirming the discounted coal clears against the
already-short peakers/steamers adjacent in the merit order, not CC_REGULAR's
surplus alone. Plant guard clean (Martin Lake 2025 +1.35, no run-81 blow-up).
LMP MAE 31.0/9.1/11.6 vs keeper 30.9/8.9/11.7 — within the ±$1 gate.
**Verdict: no pure-coal dose exists; the collateral scales with the discount.**

### Run 86 — run85 coal + Jacobian gas counter-move (REJECTED)
Derived the joint-move recipe (jacobian v2, `--validate-run run85_coal_soft`)
against run-85's residual. The trust region **froze the entire gas-side
counter-move**: run-79's CC_REGULAR/CT_PEAKER/ST_GAS curves already sit at the
edges of every range sampled by the historical pure pairs, so every move the
optimizer wants exits the region (the run-82 extrapolation lesson, now
enforced). The tool had additionally downgraded run-82's pure pair on an inert
`coal_bit_passthrough_*` provenance diff, narrowing CT_PEAKER.committed to
[1.140, 1.480]; force-including it (`--include-pair run82_jacobian_joint`,
restoring the [1.008, 1.480] the matrix should sample) unfroze exactly one
gas-class knob: **CC_REGULAR peak +0.132** (2.500 → 2.632). CT_PEAKER/ST_GAS
committed refills stayed frozen *and* unrecommended (Δ < 0.005) — the
hypothesised "CT_PEAKER/ST_GAS refill" move is not what the data supports.
Recipe per-block prediction (sidecar verbatim): **twh improves 1.49 → 1.43 but
shape DEGRADES 0.134 → 0.136 and lmp DEGRADES 19.850 → 19.851**. Ran run-85's
coal config + CC_REGULAR peak 0.382. Actual: the peak move barely moves
anything — CT_PEAKER 2024 -17.9 → **-16.6** (still fails the bar vs keeper
-12.8), coal and CC_REGULAR/ST_GAS ≈ run 85; LMP MAE 31.0/9.1/11.7 (within the
±$1 gate), shape ≈ flat (the predicted degradation was negligible). 2024
ledger: CC_REGULAR -1.33 / ST_GAS -0.68 / CT_PEAKER -0.31 gave — the donor mix
is run-85's. **The coal-gas split has no offer-curve gas reallocation within
the trusted region.**

### Run 87 — measured monthly gas (REJECTED, mechanism probe for split + LMP)
Run-79 config + `--gas-monthly-actuals`, no coal flags. ERCOT monthly gas
exists (`fuel.iso_monthly_gas_prices`, 12/12 months all years; 2024 Apr $1.64,
Aug $2.29 genuinely cheap). **(1) Coal-gas split — OVER-corrects.** Measured
gas fixes the 2024 coal deficit (lignite -23.8→+1.2, PRB -9.9→+10.8) but
overshoots (PRB +8.3/+10.8/+1.3) and worsens the gas classes *harder* than the
coal sigmoids did: CT_PEAKER 2024 **-23.1** (keeper -12.8), ST_GAS 2024
**-12.7** (keeper -2.7). 2024 ledger: coal +12.5 TWh, gas -9.7 (CC_REGULAR is
now the largest donor at -6.78, the "right" one, but the move is so large
CT_PEAKER/ST_GAS still bleed in absolute TWh). Martin Lake trips the plant
guard (+1.42/+1.97/+1.51 vs CAMPD). The structural answer is **not** simply the
gas path — the merit-order adjacency problem persists and measured gas
amplifies it. **(2) LMP — confirms the scarcity diagnosis (see below).** 2023
MAE improves 30.9→28.5 (the expensive winter months lift the level) but 2025
MAE degrades 11.7→**17.5** (2025's dear gas over-prices), so it is not a free
LMP win; and the 2023 summer >=$200 scarcity tail still carries ~100% of the
residual while the mid-curve now slightly OVER-prices — exactly the signature
of a scarcity miss, not a fuel-level miss.

### (D) LMP residual localization — the 2023 miss is scarcity, not fuel
`analyze_lmp_residual.py` on the keeper, 2023 Jun–Sep: model **$27.1** vs
actual RT **$96.1** (residual -69.0). The gap is overwhelmingly in the tail:
**89% of the summer $·h gap sits in the actual >=$200 band** (157 hours, actual
mean $1,212 vs model $61); the model clears **0 hours >$500** vs 99 actual, and
5 vs 157 hours >$200. The mid-curve tracks well (full-year p50 residual +0.20;
actual-price bands below $50 within a few $/MWh). By hour-of-day the gap is the
afternoon/evening scarcity window (hours 14–20, peak hour 19 residual -456); by
month it is Aug (-160) / Sep (-61) / Jun (-37). **Read: missing ORDC-style
reserve-scarcity pricing — a MODEL mechanism, scoped as the run-88+ follow-up,
NOT bolted on this session.** Run 87 is the live test of the alternative
(broad fuel offset) branch and rules it out: raising the fuel level
over-corrects the 2023 mid-curve while leaving the scarcity tail miss intact.
Monthly LMP MAE ($/MWh, demand-weighted |model − actual RT|), keeper / 85 / 86
/ 87: 2023 30.9 / 31.0 / 31.0 / 28.5; 2024 8.9 / 9.1 / 9.1 / 9.8; 2025 11.7 /
11.6 / 11.7 / 17.5. The coal runs (85/86) hold the ±$1 gate every year; only
run 87 moves the level materially (2023 better, 2025 worse).

**Keeper decision (revised 2026-06-12).** **Run 85 is promoted to keeper,
superseding run 79** — judged on the size-aware volume bar (≥20 TWh classes on
±5%, <20 TWh on ±1 TWh absolute), run 85 has 4 in-scope fails vs run 79's 5,
cuts total class volume error 24.0 → 20.9 TWh, fixes the worst class (lignite),
improves hourly coal NRMSE, and holds the LMP gate. The flat-percentage "no
class worse by >2 pts" guard had rejected it on a −5 pt CT_PEAKER move that is
only +0.4 TWh on an 8-TWh class — the distortion the size-aware bar removes.
Runs 86 and 87 stay rejected. The one honest caveat on run 85: CT_PEAKER/ST_GAS
are low in the *wrong direction* (EIA says both should run more), but the gap is
now a single 2024 cheap-gas cluster (~1 TWh each, all marginal) — in 2024
CC_REGULAR sits +3.1 TWh too high while coal/peakers/steamers each sit ~1 TWh
too low. The coal-gas split still has no *fleet-wide* offer-curve / fuel fix
(measured gas (87) over-corrects; the Jacobian gas counter-move (86) is
trust-region-frozen because run-79's gas curves sit at the sampled-range
edges); the live levers for the 2024 cluster are the **CC_REGULAR econ-ramp
shape** (`offer_curve_smoothing_mid`, a built-but-unused lever) and the **PRB
sigmoid** retune, with the per-plant Parish/Spruce correction (run-81 finding)
and the ORDC scarcity adder for the 2023 LMP level (run-88+) as the structural
items. `docs/calibration-best-so-far.md` updated to run 85.

---

## NYISO + NEISO P9b — serve measured net interchange in backcasts (2026-06-12)

**Runs `nyiso_smoke_2023`, `neiso_smoke_2024` (re-run in place); dashboard
`nyiso p11 smoke 2023`, `neiso 1 smoke`.** Closes the single red structural
row both P11 smokes flagged: NYISO/NEISO backcasts served **0 TWh** of imports
because the `load_demand` interchange branch was PJM-only, so the LP overfilled
the import wedge with in-state gas. Both ISOs are steady net importers, but the
priced import node only builds under `--priced-interchange`.

**Fix (eia_loader).** Added `nyiso_net_interchange(year)` /
`neiso_net_interchange(year)` sourcing the measured hourly net interchange from
the EIA-930 `NYIS hourly` / `ISNE hourly` parquets' `Total interchange` column
(shared `_eia930_net_interchange` helper). EIA's sign convention is already
export-positive (a net import is negative), so the column is served as-is with
**no** flip — unlike `pjm_net_interchange`, which negates PJM's import-positive
tie-line file. The `load_demand` interchange branch is generalized from PJM-only
to `{PJM, NYISO, NEISO}` (`_SCALAR_INTERCHANGE_ISOS`), default-on for backcast
years (`include_interchange=True`); a net import lowers the residual the
internal fleet serves. ERCOT (islanded; DC ties via its own extract) and CAISO
(imports modeled by the `WECC_import` node, playbook §8.1) stay out. The priced
node remains the *forward* mechanism, used under `--priced-interchange`
(`include_interchange=False`, no double count). Also restored the NEISO P8
demand infrastructure (`_load_neiso_hourly_demand`, `neiso_zonal_load_shares`)
accidentally clobbered by a bad rebase in the NYISO P8 commit, so NEISO demand
reads the ISNE clock and the served interchange is hour-matched.

### Results — both interchange rows now green

**NYISO 2023** (`--commitment`, P10 LMP still held → price level-only):

| fuel | energy-only (old) | **P9b (served)** | EIA-923 | EIA-930 |
|---|---|---|---|---|
| gas (cc+ct+st) | 80.11 (+25.6%) | **57.52 (−9.8%)** | 63.79 | 61.00 |
| nuclear | 27.49 | 27.49 | 27.52 | 24.00 |
| hydro | 28.38 | 28.38 | 28.40 | 26.84 |
| **TOTAL** | **147.31 (+16.0%)** | **123.77 (−2.5%)** | 126.96 | 118.61 |
| net interchange (TWh) | **0.00** 🔴 | **−23.45** 🟢 | — | −23.45 |

Net interchange: model −23.45 vs actual −23.45 TWh (duration RMSE **0 MW**,
import-hours 100% vs 100%, diurnal corr **+1.00** — the served measured
schedule). Avg price $70.99 → **$42.72** (0 negative hours; level **not**
scored, P10 held). The energy-only gas_ct +81% / gas_st +113% / CO2 +57% reads
were interchange symptoms and collapse with the wedge served.

**NEISO 2024** (`--commitment`, P10 LMP held):

| fuel | energy-only (old) | **P9b (served)** | EIA-923 | EIA-930 |
|---|---|---|---|---|
| gas (cc+ct+st) | 67.81 (+11.2%) | **57.94 (−5.0%)** | 60.99 | 59.64 |
| nuclear | 26.48 | 26.48 | 26.55 | 26.41 |
| hydro | 6.67 | 6.67 | 6.71 | 7.39 |
| **TOTAL** | — | **103.96 (+1.1%)** | 102.82 | 98.81 |
| net interchange (TWh) | **0.00** 🔴 | **−10.30** 🟢 | — | −10.30 |

Net interchange: model −10.30 vs actual −10.30 TWh (duration RMSE **0 MW**,
import-hours 83.8% vs 83.8%, diurnal corr **+1.00**). PS over-cycling
self-corrects from the energy-only 1.35 TWh toward EIA-930's 0.30 (now 0.50 —
the gap-#2 cross-coupling the smoke predicted: cheap imports remove part of the
arbitrage spread). Avg price $69.99 → **$55.72**.

**Regression guard.** ERCOT/PJM/CAISO `load_demand` outputs byte-identical
(sha256 over 2023+2024 demand arrays, pre/post). Full suite **1006 passed** (3
pre-existing CAISO zonal-share failures unrelated to this change). New tests:
`nyiso/neiso_net_interchange` import-negative; demand serves the measured wedge
by default; zonal-reconciliation tests isolated with `include_interchange=False`.

**Keeper decision.** Both remain structural-discipline smokes, **not** tuning
keepers — the interchange gate is now green, which *unblocks* the downstream
packs (P7 measured gas + U4 winter basis, P13 winter oil, P10/U2 LMP, P8/U3
zonal load) that were held behind it. No offer band tuned (playbook §6).

---

## ERCOT Runs 89–91 — CC_REGULAR shape + PRB 2024 (2026-06-12)

**Scope.** Close run 85's remaining miss — the single 2024 cheap-gas cluster
(CC_REGULAR +3.1 TWh too high; PRB −7.9% / −3.47 TWh, ST_GAS −1.19,
lignite −1.23, CT_PEAKER −1.48 TWh each ~1 TWh too low) — via the two levers
scoped at the run-85 keeper decision: the never-used econ-ramp midpoint
(`offer_curve_smoothing_mid`, commit c31cd42) and a 2024-keyed PRB sigmoid
retune. **Run 91 is the new keeper** (3 in-scope fails vs run 85's 4, no new
fails, 2024 cluster 7.37 → 3.65 TWh); `docs/calibration-best-so-far.md`
updated. Dashboard: `run89 midpoint`, `run90 prb 2024`, `run91 cc shave`
(top-5 retention prunes run83; the rejected runs 86/87 entries were also
dropped — their bundles stay in `results/calibration`). All scoring below is
the size-aware bar (≥20 TWh classes ±5%, <20 TWh ±1 TWh absolute, CT_CHP
excluded) vs run 85.

### Run 89 — econ-ramp midpoint 0.35 (base B)
Two bundles: `run89_midpoint065` (m=0.65 probe, rejected) and
`run89_midpoint035` (m=0.35, the chosen run 89). The brief's m>0.5 guess
**inverted**: m=0.65 made CC_REGULAR *gain* +1.47 TWh in 2024 and PRB lose
−1.0. Mechanism: the midpoint anchor reshapes every econ ramp, and
CC_REGULAR's ramp is nearly FLAT (econ_low 1.06 → econ_high 0.96), so the
anchor barely moves CC while the steep-ramp classes (PRB 0.40 → 1.38, ST_GAS,
CT) get pricier middles — CC wins the mid-merit hours they vacate. m=0.35
runs the same mechanism in reverse: CC_REGULAR 2024 +3.09 → **+1.37 TWh**
(+0.9%), PRB 2024 −7.9 → −5.5%, CT_PEAKER −17.9 → −15.5%, with small
lignite (−0.17 TWh) / ST_GAS (−0.04) collateral. Same 4 fails as run 85 but
the cluster shrinks 7.37 → 6.28 TWh; LMP MAE 31.2/9.3/11.4 (gate held); 2024
coal NRMSE improves 0.198 → 0.185. **Base B for runs 90–91.** Side effects
to remember: the midpoint costs CC_REGULAR 2023 −1.7 TWh (−2.7 → −3.9%) and
gives PRB 2023 +0.93 — it spends 2023 headroom.

### Run 90 — 2024-keyed PRB sigmoid retune (REJECTED, gradient anchor)
B + reshaped PRB logistic: slope 2.5 → 5 centered 2.85 → $2.45 — between
2024's cheap shaped-gas months ($1.97–2.08; the sigmoid sees annual gas ×
`GAS_MONTHLY_SEASONALITY`, so 2024 = $1.97–2.58, 2023 = $2.29–3.00) and
2023's cheapest ($2.29) — floors −0.06 (0.68/0.58), ceils pinned to run-85
values at ≥$2.5 (1.17/1.04). The shape analysis said 2023's cheap months
keep ~⅓ of 2024's discount; the realized TWh blew through it: PRB 2024
+4.34 TWh (+4.4%, overshoot) but **PRB 2023 +4.09 TWh (+12.4%, FAIL)**,
CC_REGULAR 2023 −5.5% (FAIL), Martin Lake 2023 +2.0 TWh (the run-81 guard
blow-up). 5 fails vs 4. **The quantified lesson (extends run-80e):** the
realized year-gradient is ~65 TWh per unit passthrough in 2024 vs **~142 in
2023** — 2023 sits on the coal-gas knife edge, so even month-deltas of
−0.03 detonate. And the 4-param logistic cannot cut below $2.1 while
tracking run-85's curve at $2.29+: pinning the ceil low leaks discount into
2023 winter/2025; keeping ceil 1.50 with a steep low mid marks up the
$2.4–2.6 overlap months (2024 Dec/Jan = 2023 Mar/Jul/Aug in gas space).
The PRB sigmoid stays at run-85 parameters in the keeper.

### Run 91 — CC_REGULAR per-class shave (KEEPER)
B + CC_REGULAR deltas econ_high −0.45 → −0.40 (+0.05), peak +0.25 → +0.32
(+0.07). Direction from the jacobian (CC_REGULAR.econ_high → PRB 2024
**+6.96 TWh/unit, med conf** — the PRB-2024 fix rides CC's adjacency, not
the coal bid; peak's PRB-2023 row is negative, trimming where headroom is
thinnest), dose from measurement: the full-dose probe (econ_high +0.09 /
peak +0.13, bundle `run91_cc_shave_full`, unregistered) moved every class
the predicted way but ~1.7–3× the jacobian magnitudes in 2023 (CC −5.3%,
PRB +5.3%, ST_GAS +1.06 TWh — three hairline fails, guards +1.05), giving
a measured B→full response vector with feasibility box β ∈ [0.39, 0.74];
the keeper runs β=0.55. Result (`run91_cc_shave055`): **3 fails vs run 85's
4** — PRB 2024 −4.9% PASSES (by 0.04 TWh), CC_REGULAR 2024 +0.4%, 2023/2025
all pass (CC 2023 −4.6%, PRB 2023 +4.3%, ST_GAS 2023 +0.95). Remaining
fails: ST_GAS 2024 −1.12 (run 85 −1.19), CT_PEAKER −1.22 (−1.48), lignite
−1.31 (−1.23, a 0.08 TWh drift — the one nominal regression, size-aware
noise). 2024 ledger vs run 85: CC_REGULAR −2.51 gave, PRB +1.33 / CT +0.26 /
ST_GAS +0.07 took. Guards: Martin Lake/Limestone 2023 +914/+948 GWh; Martin
Lake 2025 +1.50 (run 85 +1.35 — watch). LMP MAE 31.1/9.2/11.5 (gate held);
2024 coal NRMSE 0.198 → 0.182, gas 0.118. Honest caveats: PRB 2024 and
ST_GAS 2023 pass with <0.1 TWh margin (fragile to any further coal/gas
move), and total |class error| is flat (~21.0 TWh) — the 2024 win is paid
for inside CC_REGULAR 2023's tolerance band (−2.7 → −4.6%). The keeper
decision rests on the bar as stated: fewer fails, none new, smaller cluster.

**Open items (runs 92+).** The remaining 2024 trio (ST_GAS/lignite/
CT_PEAKER, all −1.1..−1.3 TWh) has no clean fleet-wide lever left at this
operating point — every coal/gas knob measured this session trades one
hairline constraint for another; the structural items stand: ORDC scarcity
adder for the 2023 LMP level (89% of the summer $·h gap in the ≥$200 band),
per-plant Parish/Spruce correction (under-run all years, −3.9 TWh 2024),
lignite 2024, and the CT_CHP 2025 benchmark gap. A lignite floor probe
(0.75 → 0.72) is the one cheap candidate, but Martin Lake 2023 sits at
+914 GWh with ~86 GWh of guard headroom — re-run the guard before keeping
anything.


## NEISO 2 — full calibration to sign-off 2023–2025 (P12) (2026-06-12)

**Runs `neiso_p12_base_2023`, `neiso_p12_base_2024`, `neiso_p12_hydrofix_2025`;
dashboard `neiso 2 2023`, `neiso 3 2024`, `neiso 4 2025 hydrofix`** — the NEISO
sign-off backcast across 2023–2025, run as three parallel per-year bundles with
distinct `--out-dir` (a combined `--year 2023 2024 2025` bundle hit a warm-start
basis degeneracy in the per-year P2 commitment solves and was abandoned; the
three single-year bundles solve cleanly and reproduce each other to <0.1 TWh).
**Prereqs:** P9b (served interchange) merged, P11 structural rows green. The
keeper is the **NEISO structural defaults — no offer-band tuning** (playbook §6):
served measured net interchange, the Algonquin (AGT) `gas_hub_basis_overlay`,
`dual_fuel_switching`, RGGI via the state-carbon program, `gas_monthly_actuals`,
per-plant F923 gas pricing. The **only** P12 change is a data-vintage fix —
`--hydro-backfill-year 2024` for the 2025 bundle (opt-in, default-None, every
existing run byte-identical; committed in the P12 code change merged via #383).
**P10 still held** (no NEISO `actual_lmp.json`), so price is level-only.

### Scorecard vs the P0 targets

| target | 2023 | 2024 | 2025† | verdict |
|---|---|---|---|---|
| **gas** ±5% | −3.2% / 930 (−5.1% / 923) | −2.8% / 930 (−5.0% / 923) | **−3.9% / 930** | ✅ vs the grid benchmark |
| **nuclear** | −0.2% | −0.2% | +0.7% | ✅ |
| **hydro** | −0.7% / 923 | −0.6% / 923 | +30% (2024 proxy vs 930 5.12) | ✅ 23/24; 25 provisional |
| **oil** | 0.02 vs 0.39 | 0.01 vs 0.31 | 0.01 vs 1.24 | ⚠ winter-shape (U4, filed) |
| **CO₂** ±10% vs eGRID | **−9.2%** (22.81 vs 25.13 Mt) | **−8.5%** (24.52 vs 26.79 Mt) | 24.58 Mt (no eGRID-25) | ✅ |
| **net interchange** ±15% | **exact** (−15.14 TWh, 0 MW RMSE, corr +1.00) | **exact** (−10.30, 0 MW) | **exact** (−8.13, 0 MW) | ✅ |

**Gas benchmark sourcing.** The NEISO model is grid-side (CHP runs its
steam-following grid share; the behind-the-meter host supply is pulled out and
there is no btm.parquet to add back), so total gas is scored against **EIA-930**
— the matching grid-delivered series — at **−3.2 / −2.8 / −3.9%**, comfortably
inside ±5%. The −5% vs EIA-923 is the documented whole-plant offset: 923 reports
gross CHP output including the BTM host slice the grid never sees (the same
923-vs-930 structural gap the ERCOT fuel-split note logs at ~14% on the CHP host
supply). Both benchmarks are reported; they are not mixed within a year.

†2025 EIA-923 is a monthly-survey-only early release; final hydro has not landed
(5 of ~166 plants, 0.09 of ~6 TWh). `--hydro-backfill-year 2024` carries the
non-reporting plants at their 2024 inflow, restoring ~6.6 TWh; **without it 2025
gas was +6.5% vs 930** (the missing inflow served by gas). The 2024 proxy is
wetter than 2025's true 5.12 TWh (EIA-930), so modeled hydro over-states ~1.5 TWh
and gas sits a touch low — a provisional-year artifact that self-corrects on the
final 2025 file.

### Ranked residuals (none band-tunable)

1. **[FILED · winter oil shape] Oil near-zero (0.01–0.02 TWh) vs EIA-923
   0.31–0.39 / EIA-930 0.37–1.24.** Magnitude within ±1 TWh (size-aware) but the
   season shape is wrong: ISO-NE burns oil in cold-snap dual-fuel switches, and
   the **monthly** AGT basis never reaches distillate parity (Jan-2025 HH $3.52 +
   AGT +12.79 ≈ $16.3/MMBtu vs ~$18–20 parity), so the wired CT/ST switch
   correctly does not trip on monthly data; serving interchange also displaces
   the prior oil-steam scarcity burn. **The fix is the daily-AGT U4 upload, not a
   band tune** (task brief; P11 gap #3; doc-08 decision 1). Not tuned.
2. **[AMBER · PS/BESS over-cycling] PS discharge 0.39 / 0.50 / 0.86 TWh vs
   EIA-930 — / 0.30 / 1.93; grid BESS 0.06 / 0.12 / 0.34 vs — / 0.01 / 0.15.**
   Down sharply from the energy-only smoke's 1.35 TWh (P11 gap-#2 cross-coupling:
   served imports remove part of the arbitrage spread). Not a scored target and
   immaterial to fuel-mix / CO₂; `--battery-adder` / a PS throughput cost is the
   lever if it is ever scored. Not tuned (would not move the sign-off metrics).
3. **[INFO · price level, P10 held] All five zones price identically
   ($53.61 / $55.72 / $59.50 for 2023/24/25); no Boston/CT separation** — Tier-3
   RSP TTC seeds non-binding, no measured interface limits (U6). Level reported,
   not scored, until the U2 LMP upload (P10).
4. **[TRACE] Coal 0.00–0.08 vs ~0.2 TWh** — the lone Merrimack unit; trace.

### Keeper decision & provenance

The NEISO **structural defaults are the sign-off keeper** — all three scored
targets (fuel-mix gas ±5% on the grid benchmark, CO₂ ±10% vs eGRID, net
interchange ±15%) pass for the complete-data years 2023/2024; 2025 passes
gas/interchange and is provisional on hydro pending the final EIA-923. **No
offer band was moved** (zero per-class curve overrides), consistent with the
playbook §6 structural discipline. doc-00 Stage G checklist green for NEISO.
Reproduce per year:

```
python scripts/run_calibration_full.py --iso NEISO --year <Y> --commitment \
    [--hydro-backfill-year 2024]   # the bracketed flag for 2025 only
```

**Citations.** eGRID CO₂ benchmark: EPA eGRID2023 (rev2) / eGRID2024, sheet
`SRL23`/`SRL24`, column `SRCO2AN`, subregion `NEWE` — 27.69 / 29.53 M short tons
→ **25.13 / 26.79 Mt** (×0.90718474 short-ton→tonne). Model CO₂ from each plant's
`emission_rate_co2 = heat_rate × FUEL_CO2_FACTOR_PER_MMBTU` (152 NEISO fossil
plants matched, 0 on fallback) — a base-rate figure, so the dispatch's band-HR
multipliers make it conservative (true model CO₂ slightly higher / the gap
smaller). AGT winter basis: `inputs/raw-data/gas_basis_by_iso_month.csv` (ISO-NE
MA gas index, isonewswire monthly posts, 35/36 months 2023–2025). Hydro
early-release backfill rationale documented at `load_hydro_budget`.
---

## NYISO P12 — Full calibration loop to sign-off (2023; 2025/2024 data-blocked) (2026-06-12)

**Keeper: the P9b served-interchange config (`nyiso p11 smoke 2023`, bundle
`results/calibration/nyiso_smoke_2023`), promoted to the P12 sign-off keeper.**
The loop ran the offer-curve / hydro / storage / import / dual-fuel knobs against
the P11+P9b structural config and found **no honest knob that lifts an
out-of-tolerance class without a zero-sum trade against an in-tolerance one or a
convention violation** — so the structural config *is* the keeper. Recorded in
`docs/calibration-best-so-far-nyiso.md`. Branch `claude/nyiso-p12-calibration`.
**P10 LMP still held (U2)** → price level-only, not scored.

### The mix is calibrated; the gas total is a documented basis floor

2023 fuel-mix vs EIA-923 (P2): every renewable/baseload class is inside ±5%
— hydro +1.3%, nuclear −0.1%, wind −3.6%, solar −5.0% (edge), OTHER 0.0%,
CC_REGULAR −2.6%, ST_GAS −0.8% — and net interchange matches exactly (−23.45
vs −23.45 TWh, duration RMSE **0 MW**, import-hours 100%, diurnal corr +1.00).
The one class-level miss is **gas total −9.9%** (57.53 vs 63.84 TWh), and it is
a **demand-basis floor, not a dispatch error**: the in-state fleet's total is
pinned by energy balance to served demand = EIA-930 transmission-metered demand
(147.05) + measured net interchange (−23.45) = **123.77 TWh**, which is 4.5%
below EIA-923's plant-net-generation total (129.67). With every non-gas class
on the EIA-923 mark, the −5.9 TWh total gap must fall on the swing fuel. The
deficit lands on the small **CHP/peaker** classes (CC_CHP −14.6%, CT_CHP
−44.2%, ST_CHP −18.0%, CT_PEAKER −75.2%) while the two big gas classes stay on
target — the least-distorting landing spot. Against EIA-930 (the operationally
consistent basis) gas is **−5.7%**. CO2 ≈ 24 Mt (class-rate approx) vs eGRID-2023
26.9 Mt excl-biogenic ≈ −10%, downstream of the gas total.

**Why no knob closes it (all rejected):**
- **td_loss gross-up** — ruled out by convention: EIA-930 NYIS demand is
  transmission-metered / generation-side (playbook §8.1, the ERCOT
  `td_loss_factor=0` rule), so a distribution-loss gross-up double-counts.
- **import scaling** — serving e.g. −20 TWh (inside the ±15% interchange
  tolerance) would lift the total to ~127 and gas to ~−4%, but the measured
  EIA-930 schedule is matched *exactly* (RMSE 0 MW). Degrading a perfect
  measured match to paper over an EIA-930-vs-EIA-923 *benchmark-basis*
  difference is overfitting, not calibration. **Rejected.**
- **CHP / offer-curve / storage** — reshuffle within the fixed total; the
  obvious CHP lever does not even do that (see `nyiso 2`).

### Passes (one named hypothesis each)

**nyiso 1 gas-actuals** (`--gas-monthly-actuals`, bundle
`nyiso_p12_gasact_2023`) — **REJECTED, no-op.** Hypothesis: measured EIA-923
monthly gas (Jan-2023 $10.02/MMBtu winter spike vs the flat $2.54 HH seed)
re-levels gas and trips the dual-fuel oil switch. Result: **byte-identical**
mix and price duration (gas 57.53, oil 0.013, avg $42.72, max $235.81) — the
harness already enables `gas_monthly_actuals` + `gas_plant_monthly_fuel_pricing`
by default for NYISO (the P11 "flat $2.54 seed" note predated the P9b re-run).
So the winter gas level is already priced in, and oil still does not fire: even
measured monthly Jan gas ($10) stays below distillate parity (~$16/MMBtu), the
documented P13 limitation — **winter oil is gated on the U4 daily Transco-Z6 /
Iroquois gas basis, which is not uploaded for NYISO** (only the NEISO/Algonquin
leg is filled). oil −96.9% is therefore filed to U4, not tunable this pass.

**nyiso 2 chp-covered** (`--chp-startup-covered`, bundle `nyiso_p12_chp_2023`)
— **REJECTED, negligible.** Hypothesis: the CHP under-dispatch is a
startup-amortization artifact — a steam-host cogen pays no energy-market cold
start, so removing the markup lets CC_CHP/CT_CHP/ST_CHP run toward their
must-run reality. Result: CHP moved only **+0.1 TWh total** (CC_CHP +0.027,
ST_CHP +0.051, CT_CHP +0.017; CC_REGULAR −0.033, ST_GAS −0.048; gas total
57.525 → 57.537; avg price $42.72 → $43.02). The CHP/peaker deficit is
**structural** — the model dispatches CHP economically and enforces no hard
steam-host must-run floor — not a startup-cost artifact, and within the fixed
served total there is no room for the CHP classes to recover without displacing
the on-target baseload gas. A hard steam-host / reliability-must-run floor
(EIA-860 cogen steam load + downstate reliability commitments) is the structural
follow-up, filed; it is not an offer-band knob.

### 2025 and 2024 are data-blocked (filed, not calibrated)

The P12 prompt asks for 2023 **+ 2025** in parallel. 2025 is **not yet a valid
backcast year**:
- The EIA-930 `NYIS hourly` extract stops at **Q1 2025** (2,160 of 8,760 h), so
  `nyiso_net_interchange(2025)` returns `None`; `load_demand` falls back to the
  demand-profiles parquet (full-year **gross** demand, 151.6 TWh) and serves
  **0** of the ~−23 TWh import wedge → the 2025 baseline bundle
  (`nyiso_p12_base_2025`) **over-generates +22.7%** (151.9 vs EIA-923 123.8 TWh,
  gas +11.8%, avg price $127) — the exact P11 structural failure, here driven by
  missing data rather than missing code.
- The 2025 EIA-923 benchmark is preliminary (biomass 0.13, solar 0.66, oil 1.06
  TWh — renewables/biomass under-reported), so even with interchange it could
  not be scored.
- **Refresh path:** extend the EIA-930 `NYIS hourly` extract through 2025-12 and
  re-pull final 2025 EIA-923, then re-run `nyiso_p12_base_2025`. Until then the
  2025 bundle is retained on disk as the data-gap evidence, **not registered.**

2024 remains blocked on `NY_2024` unit-level CEMS (only facility-level present)
and the missing `NYISO_2024_renewable_capacity.csv`.

### Keeper decision & sign-off

`nyiso p11 smoke 2023` is the **P12 keeper** (no new tuning bundle — the
structural config is optimal under the binding constraint). 2023 Stage-G
calibration is **green on every scorable target except the gas-total basis floor
and the U4-gated winter oil**, both documented above. Dashboard carries the
keeper; `nyiso_p12_gasact_2023` / `nyiso_p12_chp_2023` / `nyiso_p12_base_2025`
are retained on disk as the rejected-probe / data-gap evidence (not registered —
no keeper among them). `docs/calibration-best-so-far-nyiso.md` records the
config; doc-00 status table + Stage-G checklist updated; citations appended.

---

## CAISO 2 — priced-WECC-node smoke 2023-2025 (P11, structural-checklist pass) (2026-06-12)

**Run `results/calibration/caiso_1_priced_ix`, dashboard `caiso 2 priced-ix`** —
the first CAISO full bundle (`run_calibration_full.py --iso CAISO --year 2023
2024 2025 --hours 8760 --commitment`, P1+P2) solved with the **priced WECC
import/export node ON by default** (`PRICED_INTERCHANGE_DEFAULT_ISOS={CAISO}`,
no `--priced-interchange` flag — `load_demand` does no interchange netting for
CAISO, so the node is the only correct default) and the 2023-2025-fitted
`IMPORT_TRANCHES`/`EXPORT_TRANCHES["CAISO"]` (CHANGELOG 2026-06-12: 6 import
blocks 11.4 GW + 2 export sinks 6.5 GW). Prereqs P0-P10 merged; **P10 is in
level-only mode** — no `actual_lmp.json` CAISO block, so the modeled price level
is reported, not scored. Structural-discipline pass (playbook §6): **no
offer-band tuning** — structural row #2 is red and is **filed**, not tuned.

This pass answers the P9 "remaining" item (re-score the *modeled* net
interchange and clearing frequency vs the solved CAISO price duration curve,
not just the offline price-orthogonal bound).

### Headline numbers (P2 commitment bundle)

| Metric | 2023 | 2024 | 2025 | Benchmark | Read |
|---|---|---|---|---|---|
| gas (TWh) | 44.98 | 54.47 | 62.16 | EIA-923 76.04 / 67.68 / 55.18 | **−41% / −19% / +13% — now UNDER-produces (over-import overshoot)** |
| gas vs EIA-930 | 44.98 | 54.47 | 62.16 | 88.01 / 85.37 / 79.03 | −49% / −36% / −21% |
| nuclear | 17.63 | 18.20 | 17.49 | 930 17.75 / 18.35 / 17.61 | ✓ −0.7% / −0.8% / −0.7% |
| wind | 16.55 | 20.29 | 19.81 | 930 16.40 / 20.06 / 19.82 | ✓ (judged vs 930) |
| solar | 39.79 | 47.91 | 49.81 | 930 37.17 / 44.64 / 49.70 | ✓ +7% / +7% / +0.2% vs 930 |
| hydro | 23.78 | 21.23 | 12.32 | 930 24.42 / 22.73 / 21.34 | ✓ / ✓ / **−42% 2025 (partial-year budget; 923 2025 total 117 TWh = incomplete)** |
| **net interchange (TWh)** | **−61.65** | **−49.26** | **−52.86** | **EIA-930 −28.87 / −32.38 / −36.16** | **RED — +114% / +52% / +46%, far outside ±15%** |
| import-hour share | 99.9% | 100.0% | 100.0% | 85.9% / 89.0% / 90.9% | **RED — node never exports; midday sign-flip absent** |
| diurnal corr | +0.96 | +0.96 | +0.90 | — | shape OK but amplitude tiny (peak→trough 1453/833/462 MW vs 5236/4596/4973 measured) and never crosses zero |
| solar curtailment (TWh) | 0.000 | 0.000 | (no HSL) | reported 2.509 / 3.170 | **RED — model re-curtails ZERO (0% vs 6.3% / 6.6%)** |
| battery discharge (TWh) | 4.99 | 6.86 | 9.61 | — (CISO folds BAT into OTH) | evening share 93% / 85% / 67%; no 930 benchmark |
| PS discharge (TWh) | 1.80 | 1.27 | 0.39 | — | no 930 benchmark |
| avg price ($/MWh) | 77.34 | 53.10 | 56.63 | — (P10 held) | 2023 biased high; **0 negative-price hours all years** (real CAISO has hundreds) |

### Ranked gap list (structural-checklist order; hypotheses + owning pack)

1. **[GREEN · demand/net-load]** CAISO demand is the CISO EIA-930 net-load
   series (no interchange netting — the documented convention, §8.1/§8.2); the
   import↔gas swap below is *not* a demand error. Minor: 2023 TAC-area load
   covers 8759/8760 h, the gap filled with sample-average zone shares (refresh:
   complete the U4 monthly OASIS pulls). No action.

2. **[RED · net interchange] The priced WECC node OVER-imports — it closes the
   old gas-overproduction gap but overshoots into the opposite error.** Modeled
   net interchange **−61.65 / −49.26 / −52.86 TWh vs EIA-930 −28.87 / −32.38 /
   −36.16** (+114% / +52% / +46%, all far outside the ±15% acceptance band).
   The node imports in **~100% of hours vs 86-91% measured** and **never
   exports**, so the midday solar export sign-flip is not reproduced (measured
   p90/p99 are positive — +661/+3574 MW in 2023 — but the model stays −2548 MW
   at p99). **Root cause: tranche *prices*, not capacities.** The offline
   price-orthogonal fit is good (duration RMSE ~560 MW, annual within 1-3%; the
   capacities tile the duration curve), but the static tranche prices
   ($14 PNW_hydro → $92 WECC_scarcity, absolute delivered-WECC-energy costs)
   sit **below the modeled CAISO price duration curve** (p10 $43-48, *zero*
   negative hours) in nearly every hour, so almost the full 11.4 GW import stack
   clears continuously while the $0-8 export sinks essentially never clear (the
   modeled price never collapses midday). Bundle-mode `derive_import_tranches.py
   --bundle caiso_1_priced_ix` confirms it: current constants score
   **216% / 154% / 148% of actual annual** against *this* solved price curve,
   and the re-fit pushes the import/export boundary up to ~$34-48 with import
   blocks layered at $46-275 (2023) / $44-74 (2024) / $48-80 (2025). **This is
   a calibration item, not a structural-machinery one** — the node, zone, links
   and capacities are right; only the price levels relative to the modeled
   CAISO price are off. **Owner: P9/P12** — re-price `IMPORT_TRANCHES`/
   `EXPORT_TRANCHES["CAISO"]` in bundle mode against the solved price duration
   curve, iterating (re-pricing shifts the solved price, so 2-3 passes). **This
   blocks everything below — do not tune offer bands until it is fixed.**

3. **[RED · curtailment] The LP re-curtails zero solar/wind.** Model curtailment
   **0.000 TWh** both HSL years vs reported solar **2.509 (6.3%) / 3.170 TWh
   (6.6%)** and wind 0.151 / 0.229. With 6-8 GW of cheap imports flooding supply
   and **no negative-price hours**, the midday oversupply that should spill
   instead displaces gas/exports — a *symptom of gap #2* (cheap imports remove
   the negative-price regime that drives curtailment) compounded by the P6
   profile path (the LP consumed the delivered/HSL potential and dispatched
   100% of it). 2025 has **no CAISO HSL parquet** (`build_caiso_hsl.py` not yet
   run). **Hypothesis:** re-measure curtailment after gap #2 is fixed; if still
   zero, the renewable feed is delivered-not-potential (P6 fallback). **Owner:
   P6 (HSL build for all years) / re-check after P9/P12.**

4. **[AMBER · gas+carbon level — downstream of #2] Gas no longer overproduces —
   it now UNDER-produces.** The task's confirm-the-headline-gap check: the prior
   energy-only baseline (`caiso 1 baseline`) over-generated gas because it had
   no interchange node for CAISO's ~30 TWh/yr net imports. With the node ON,
   gas falls to **44.98 / 54.47 / 62.16 TWh — now −41% / −19% vs EIA-923 in
   2023/2024** (and +13% in the partial-2025). This is a **direct one-for-one
   swap with gap #2**: the +33 TWh of excess 2023 imports displaces ≈31 TWh of
   gas. So the structural fix (priced node) addressed the right gap, but its
   over-calibration moved gas through the target and out the far side. Gas lands
   right once the node imports the correct ~29 TWh (gap #2 fix). **No gas knob
   this pass** — moving fuel passthrough or offer bands here would bake in a
   compensating error against the over-import (the PJM lesson). **Owner: resolves
   with #2.** Carbon: CARB cap-and-trade enters MC via `state_carbon_pricing`
   (CAISO allowance + border adder on tranches); level not separately scored
   (P10 held).

5. **[AMBER · hydro/PS/battery throughput] 2025 hydro low; storage has no 930
   benchmark.** Hydro ✓ in 2023/2024 (−2.6% / −6.6% vs 930) but **−42% in 2025**
   (12.32 vs 21.34) — the 2025 monthly budget is partial (EIA-923 2025 system
   total is only 117 TWh, an incomplete reporting year), a *data* gap not a
   dispatch one. Battery throughput (4.99→9.61 TWh, growing with the fleet) and
   PS (1.80→0.39 TWh) cannot be scored — the CISO extract folds BAT into `OTH`.
   Evening-discharge share is high (93%→67%, plausibly correct for CA evening
   ramp) but unverifiable. **Hypothesis:** complete the 2025 hydro budget (U4
   refresh); add the storage benchmark when a CISO battery series is available.
   Watch over-cycling after gap #2 (cheap imports inflate arbitrage spread, the
   NEISO PS lesson). **Owner: P4 (2025 budget) / P5 (battery benchmark).**

6. **[INFO · outages]** Historic unit-outage overlay fires (229 CAISO
   plant-tranches derated 2023). No coverage red flag this pass. No action.

7. **[INFO · price level/duration — P10 held]** No `actual_lmp.json` CAISO
   block, so the modeled level (avg $77.34 / $53.10 / $56.63) is reported, not
   benchmarked. All four zones (NP15/SP15/ZP26/WECC_import) price *identically*
   every year — **no NP15↔SP15 separation** (the Tier-3 TTC seeds are
   non-binding) — and **zero negative-price hours** all years, which real CAISO
   contradicts (the midday solar collapse). Both are biased by gap #2 (cheap
   imports prop the floor up). **Owner: P10 (U2 LMP upload + U5 Path 15/26 flows
   for congestion/negatives).**

### Keeper decision

`caiso 2 priced-ix` registered as the second CAISO run (baseline + this; under
the 5-run retention limit, no pruning). **Not a calibration keeper for tuning.**
The priced WECC node is the correct structural mechanism and it closes the
energy-only baseline's headline gas-overproduction gap — but it is **mis-priced
relative to the modeled CAISO price**, so it over-imports (+46-114%) and
suppresses gas below target while never reproducing the midday export sign-flip.
**Acceptance NOT met:** modeled net interchange is far outside ±15% and the
diurnal sign pattern is not reproduced. Per playbook §6 the red structural row
(#2 interchange) is **filed for a bundle-mode tranche-price recalibration
(P9/P12)** — no offer-band, gas, hydro or storage knob is moved this pass, since
all of them would compensate for the over-import and bake in errors that must be
unwound once the node is repriced. The bundle and its `derive_import_tranches.py
--bundle` re-fit boundaries are the evidence for that next pass.

---

## CAISO 4 — import/export tranche re-price (P9/P12 structural fix) (2026-06-13)

(Numbered after the pre-fix offer-curve probe panel "CAISO 3" below, which the
re-price unblocks; chronologically the probe came first.)

**Keeper `caiso_reprice_pass4`, dashboard `caiso 4 reprice`.** Resolves the
"CAISO 2 priced-ix" RED structural row #2 (import over-clear). Held the
`IMPORT_TRANCHES`/`EXPORT_TRANCHES["CAISO"]` block CAPACITIES fixed (they tile
the measured net-interchange duration curve) and re-priced only the per-block
PRICES in bundle mode against the solved CAISO price duration curve, iterating
4 passes (re-pricing shifts the solved price, so re-fit each pass). ERCOT/PJM/
NYISO/NEISO untouched.

### Headline (vs `caiso_1_priced_ix` baseline)

| Metric (2023/24/25) | baseline | **keeper (pass 4)** | actual | Read |
|---|---|---|---|---|
| net interchange (TWh) | −61.6/−49.3/−52.9 | **−38.6/−26.9/−33.2** | −28.9/−32.4/−36.2 | **214/152/146% → 134/83/92%** |
| gas vs EIA-923 | −41/−19/+13% | **−11/+13/+48%** | — | 2023 recovered from −41%; 2025 confounded by −42% partial-hydro budget |
| import-hour share | ~100% | 98/96/100% | 86/89/91% | still high — **P6-blocked** |
| negative-price hours | 0 | **0** | hundreds | **P6-blocked** (no midday crash) |
| avg price ($/MWh) | 77/53/57 | 86/60/65 | (RT) —/33/34 | model over-prices; **pre-existing** (baseline already high) |

### What the re-price actually is

1. **The cheap blocks are inframarginal — re-pricing them does nothing.**
   Baseline and pass-1 price duration curves are *identical* (p50 $64.8): the
   PNW_hydro/midC blocks sit below the gas merit order, so gas sets the
   marginal price above them and raising them below gas moves neither price nor
   quantity. The over-import was entirely the **top blocks** (DSW_CCGT/CT/
   scarcity, ~24 TWh) sitting below gas. The fix prices them **above** the
   in-state gas merit order — desert-SW gas imports physically cost ≈ CA gas +
   wheeling, i.e. above CA gas, so they peak instead of baseload. Per-block CF
   matches `price > stored_price` cleanly, confirming the threshold mechanism.
2. **Border-carbon bug fixed.** `run_calibration.run_year` built the priced
   node with `build_import_generators(iso)` and **no border carbon**, silently
   dropping the CARB unspecified-import adder (0.428 t/MWh × allowance,
   ~$12-15/MWh) that the production `runner.py` applies and the constants
   comment claims is layered at build time. Now applied in the calibration
   path too (at the backcast year's carbon price, CAISO-only, imports-only).
3. **Converged set** `IMPORT [28,36,48,68,110,180]`, `EXPORT [8,0]`. Export
   sinks held at the safe $8/$0 (below every import effective threshold incl.
   the +$14 carbon → no import↔export arbitrage; a higher sink would open an
   import-cheap/export-dear loop). Pass trajectory (2023 net-import %):
   214 → 208 (p1, cheap-block raise: inert) → 173 (p2, top blocks above gas)
   → 123 (p3, +carbon +mid/top) → 134 (p4, balanced 3-yr).

### Why it doesn't hit ±15% for all three years (static-node limit)

A single static price vector **cannot** track the year-to-year price-curve
offset. 2023 has a fat tail (p90 $119; wet-hydro + lowest-storage year) while
2024/25 are compressed (p90 $75/$80), so the 2023↔2024 import-% gap is ~50-60
pts **invariant to the price level** (verified by an offline oracle over the
three solved curves: best-balanced static set caps at ~28-42% max deviation).
The keeper minimizes total error — **2024/25 land within ±15% (−17/−8%)**,
2023 is the **+34% fat-tail outlier**. Same limitation PJM/NYISO documented.
A **year-keyed (availability/season) import lever** is the structural next step.

### Filed, not chased (per playbook §6 — structure still RED, do NOT re-probe)

- **import-hour share (98/96/100% vs 86-91%), negative-price hours (0), midday
  export sign-flip (absent)** — all **P6-owned**: the solar feed is the
  delivered (already-curtailed) profile, not potential, so the model never sees
  midday oversupply for storage/exports/curtailment to absorb and the price
  never crashes below the cheapest import. Storage is *not* the constraint
  (model BESS 7.5/10.8/14.7 GW + 2.1 GW PS tracks CAISO's buildout and does
  evening arbitrage). Confirmed independent of the re-price.
- **Price level vs `actual_lmp`** (model ~$60 vs CAISO 2024 RT ~$33): the deep
  tension is that real CA imports are *cheap but transmission/season-limited*,
  which a fixed-capacity priced node can't represent — cheap price → over-
  import (quantity), dear price → over-price (level). Pre-existing (baseline
  already $53); the re-price trades price-suppression for quantity-correctness.
  → P10/structural, time-varying-import lever.

Because net-interchange (±15% all years), import-hour share, sign-flip and
negative hours are not all green, the **CAISO offer-curve Jacobian re-probe is
NOT run** — the conditional pre-fix probe panel ("CAISO 3" Jacobian on branch
`claude/caiso-offer-curve-jacobian-72wjgt`) stays filed until the P6 solar feed
and a year-keyed import lever land. The re-price's structural win (import
over-clear broken, gas recovered) is the deliverable.

---

---

## ERCOT Run 92 — Kiamichi fleet fix: the missing 1.4 GW CC (2026-06-12)

**Trigger.** Post-run-91 question: why does the model "generate ~470 TWh when
actual is 475"? Reconciliation: the LP serves EIA-930 demand exactly (446.0
TWh 2023, unserved 0); on the 923 basis the model+BTM totals 473.9 vs 475.2.
The wedge decomposes into the solar source difference (model solar follows
930 actuals, +3.8 TWh above what 923 credits) and **one plant**: the 923
CC_REGULAR benchmark includes **Kiamichi Energy Facility (EIA 55501)** —
Kiowa OK, `ba_code ERCO`, 1370 MW F-class 2×(2×1) CC, online 2003, EIA
annual HR 8.119, ~5.0–5.3 TWh/yr — the **single ERCOT-BA plant outside
Texas** (1401 TX + 1 OK), dropped by the TX-state-filtered registry build.
With `use_campd_bins=True` the bins CSV IS the fleet, so the plant never
dispatched. The CC fleet covered the hole by over-running CAMPD (+4.7 TWh
2023, **+13.2 TWh 2024**) — most of run-91's "CC_REGULAR 2023 −4.6%" and
the 2023 gas-split fail were this bias, not mix tuning. CAMPD-vs-923 class
wedge is a stable ~+14 TWh/yr (~5 Kiamichi + ~9 netting).

**Fix (permanent, inputs).** Registry row (EIA-860 facts, CC-fleet medians
for ancillary fields, `has_campd_data=False` — no OK CAMPD extract, so
statistical availability, no outage overlay, absent from per-plant panels)
+ bins row (North / N_CC7 / 25-60-15 committed-econ-peak, HR mults
1.08/1.0/1.55). Smoke-tested: 3 LP tranches, 1370.2 MW, zone North.

**Run 92 (`run92_kiamichi`, dashboard `run92 kiamichi`; prunes run84).**
Run-91 tuning unchanged on the corrected fleet. The targeted cells land:
**CC_REGULAR 2023 −4.6 → −1.3%**, ST_GAS 2023 +0.95 → −0.29 TWh, 2023 fuel
split passes both fuels (gas −1.9 / coal +1.5; was fail/fail), 2024 gas
split +0.2. **The LMP level was the smoking gun: MAE 2025 11.5 → 2.2
$/MWh, 2024 9.2 → 7.3** (2023 32.1, at the ±$1 gate edge) — the model had
been over-pricing tight years because 1.4 GW of real supply was missing.
But the run-91 offer tuning is stale on the bigger CC fleet: Kiamichi's
energy crowds the adjacent classes instead of the incumbent CCs giving
back their over-run — CC_REGULAR 2024 **+4.1%** (+5.9 TWh), CT_PEAKER
fails **all three years** (−1.5/−2.6/−1.7 TWh), PRB 2024 −8.5%, ST_GAS
2024 −13.2%. **6 in-scope class fails vs run 85's 4 → run 92 is NOT the
scored keeper; it is the corrected baseline.** Guards: Martin Lake/
Limestone 2023 +582/+797 (clean).

**Keeper bookkeeping.** Run 91 remains the best scored run, but the fleet
fix is permanent, so run 91 is **not reproducible on current inputs** —
`calibration-best-so-far.md` carries an OPEN status note. The next
campaign re-tunes the offer curves on the corrected fleet: the CC give-back
(econ_high/peak up, now with real 2023 headroom — CC 2023 sits at −1.3%),
CT_PEAKER recovery in all years (year-blind lever is finally safe: CT is
under everywhere; mind the run-82 committed-step explosion zone below mult
~1.0), and the 2024 coal trio. The pre-Kiamichi Jacobian pure pairs no
longer describe the fleet — re-derive with fresh probe pairs before
trusting any recipe.

---

## NEISO price re-score — P12 keepers vs actual_lmp (P10 landed) (2026-06-12)

**Scope.** P10 (the U2 LMP upload) has landed: `inputs/calibration/actual_lmp.json`
now carries a NEISO block (DA + RT hub `.H.INTERNAL_HUB` + the four model-zone
averages, annual/monthly/duration percentiles) and
`actual_lmp_hourly_NEISO.parquet` is the dense 8760 hub-mean sidecar. This pass
**scores the price** of the three P12 sign-off keepers
(`neiso_p12_base_2023`, `neiso_p12_base_2024`, `neiso_p12_hydrofix_2025`) that
were signed off level-only — it does **not** re-tune them (the structural fuel-
mix / CO₂ / interchange rows are green and stay green; zero offer-band moves).
Scored from the existing bundles' `system.parquet` dual prices (no re-solve):
the four model load zones price **identically** every hour, so the modeled hub
is the common internal price (P1 pass, demand-served zones; `HQ_import` carries
zero load and does not enter the demand-weighted level). Comparison convention
follows `scripts/analyze_lmp_residual.py` — modeled vs actual **RT** (DA
reported alongside).

### 1. Level + duration-curve fit (hub `.H.INTERNAL_HUB`)

| metric | 2023 | 2024 | 2025† |
|---|---|---|---|
| modeled hub mean ($/MWh) | 53.58 | 55.68 | 53.44 |
| actual hub RT / DA | 35.70 / 36.82 | 39.54 / 41.51 | 65.89 / 67.86 |
| residual vs RT ($ / %) | **+17.9 / +50%** | **+16.1 / +41%** | **−12.5 / −19%** |
| model p50 / p90 / p99 | 36 / 125 / 150 | 38 / 105 / 125 | 53 / 64 / 94 |
| actual-RT p50 / p90 / p99 | 27 / 57 / 184 | 30 / 68 / 168 | 45 / 144 / 246 |
| >$75 tail share (model / actRT) | **24.7% / 5.9%** | **29.8% / 8.2%** | **5.8% / 27.2%** |
| hourly corr (model vs actRT) | +0.30 | +0.31 | +0.45 |

†2025 is the provisional year (`--hydro-backfill-year 2024`); its actual prices
are final, but the modeled bundle inherits the 2025 hydro/oil data caveats.

**The duration shape is the diagnosis, not the level.** In every year the model
produces a **fat $75–150 plateau with no extreme tail**: model p99 *under-shoots*
actual p99 in all three years (150 vs 184; 125 vs 168; 94 vs 246) while the
>$75 share is 3–5× *too high* in 2023/2024 and 5× too low in 2025. The model
never clears a single hour >$200 in any winter window; actual RT has 44 / 11 /
160. This is the signature of a **monthly** marginal-fuel input meeting a market
whose price is set by **daily** gas spot — see attribution (3).

Per model zone (modeled uniform, no congestion): residual vs actual-zone RT is
≈ uniform — 2023 +20.4..+21.4, 2024 +17.2..+18.5, 2025 −9.3..−11.6 — because
the modeled zones are identical and the actual zones sit within ~$1.5 of each
other (see 2).

### 2. Zonal-spread adequacy (4-zone sufficiency gate) — confirmed, one item filed

The modeled **Boston−Hub and CT−Hub spreads are exactly $0** (all four load
zones price identically; the Tier-3 RSP TTC seeds never bind, no measured
interface limits — U6 not uploaded). The actual day-ahead separation
(`neiso-zonal-adequacy.md`) is itself tiny — signed-mean Boston−Hub +0.30 /
+0.55 / +0.81 and CT−Hub −0.78 / −1.18 / −1.87, every pocket median under
$1/MWh — so the model's zero separation **tracks the actual to within the
documented "level-market" tolerance** for Boston and North, and the adequacy
doc's own conclusion (keep 4 zones on *structural*, not price, grounds) stands.
**The one divergence filed:** the model cannot reproduce **Connecticut's
growing cheap-side tail** (CT−Hub p99 $5.0 → $13.5 across 2023→2025, 7.4% of
2025 hours >$5 below hub) — CT is well-supplied (Millstone + NEEWS imports) and
parts cheap from the hub under cold-snap evening peaks, which a copper-plate
internal price erases. **Do not add zones** (the spread is sub-$2 mean and the
4-zone split is already justified structurally); the lever is the U6 interface-
flow upload to replace the non-binding RSP TTC seeds, not topology. Filed.

### 3. Winter-tail miss attributed to U4 (daily-AGT gap) — NO band tuning

The residual is **concentrated in winter (Jan/Feb/Dec) and a few summer-peak
months**, and the winter miss is the documented monthly-AGT limitation
(neiso-data-audit §2b; doc-08 decision 1; P11 gap #3), **not** offer bands:

- **The modeled winter is a flat monthly plateau.** Jan/Feb model duration:
  2023 p50 $123 → max $147 (a $123–147 band); 2025 p50 $55 → max $66. The
  intra-month hourly spread is ~zero because the committed AGT basis is
  **monthly** — every winter hour inherits the same monthly-mean gas cost.
  Real ISO-NE winter is spiky (2023 Jan/Feb actual p50 $38, p99 $273, max
  $462; 2025 p50 $126, p99 $285) because price is set by **daily** AGT spot
  blowouts.
- **The miss cuts both ways, and both directions are U4.** Where the monthly
  mean over-states the typical hour (2023/2024: many moderate actual hours sit
  below the flat plateau) the model **over-prices the mid-curve** (fat >$75
  band); where the realized daily blowout dwarfs the monthly mean (2025 Jan
  +12.79 / Feb +10.43 / Dec +10.64 basis, actual winter ~$130) the model
  **under-prices catastrophically** (Jan −79, Feb −72, Dec −69). Either way the
  model **never reaches the cold-snap spike tail** (0 hours >$200 vs 44/11/160
  actual) — the p99 under-shoot the task predicted. A daily-AGT series (U4)
  would trip the dual-fuel CT switch and resolve the plateau into spikes; a
  band move cannot manufacture daily price variance from a monthly input.
- **Companion summer-peak over-pricing — same oil-steam family, filed not
  tuned.** Jul-2023 ($128 vs $39) and Aug-2024 ($87 vs $39) are flat
  over-priced *summer* plateaus with **zero slack** (max-slack 0; not VOLL —
  the marginal unit is expensive oil-steam, HR ~10–12 × distillate). This is
  the documented inversion: with the monthly AGT below distillate parity the
  dual-fuel/oil-steam scarcity dispatch lands in summer peak hours instead of
  winter cold snaps (backcast-2024 gap #1, the oil-shape item). The fix is the
  same U4 daily basis, not an offer-band; filed.

The broad year-over-year flatness (model ~$54 every year vs actual rising
$36 → $66) is additionally the served-interchange convention: imports are
netted into demand rather than price-setting, so cheap HQ hydro never sets the
marginal price and the modeled marginal unit is always a dearer internal
generator. The P11 smoke's `--priced-interchange` diagnostic pulled the 2024
level to $48 (vs $56 served, $39.5 actual) — closer but still over; the priced
node remains the forward mechanism. Structural (P9), filed, **not** band-tunable.

### Scored verdict & keeper

Price is now **scored** for 2023–2025 (level + duration + zonal spread); it does
**not** meet the ±5% duration / ±5–10% level target. The miss is **filed**, not
tuned: (a) winter Jan/Feb/Dec tail → **U4 daily AGT** (the make-or-break NEISO
upload), (b) zonal CT cheap tail → **U6** interface limits, (c) mid-curve level
→ priced-interchange node (P9). **No offer band was moved; the structural
fuel-mix / CO₂ / interchange rows are untouched and still green.** The P12
keepers remain the sign-off config. ERCOT / PJM / CAISO / NYISO untouched.
Dashboard runs `neiso 2 2023` / `neiso 3 2024` / `neiso 4 2025 hydrofix`
re-registered so the now-present NEISO `actual_lmp` benchmark drives the price
scorecard. Reproduce: `python scripts/analyze_lmp_residual.py
results/calibration/neiso_p12_base_2023 … --months 1 2 --years 2023 2024 2025`.

---

## ERCOT — ORDC scarcity overlay + AS netting (2026-06-12)

**Campaign: give the energy-only LP the price tail it structurally cannot
produce, post-solve, so capacity-expansion revenue (and therefore the 2040s
fleet behind the emissions answer) stops being computed on duals with zero
scarcity rent. Volumes untouched by construction. Baseline bundle:
`run92_kiamichi` (the corrected-fleet baseline, LMP MAE 32.1 / 7.3 / 2.2);
this campaign is independent of the runs-93-95 volume retune.** Full
methodology + provenance: `docs/ordc-overlay.md`.

**Mechanism (published, zero fitted parameters).** ERCOT's RTORPA as
published (ORDC OBD / NPRR568; 2024 Biennial ORDC Report): two half-hour
LOLP terms — `0.5·(VOLL−λ)·[LOLP(R; μ, σ) + LOLP(R; μ/2, σ/√2)]`, LOLP =
1−NormCDF(R−X) pinned to 1 at R ≤ X — with the post-Uri values as
ScenarioConfig defaults: VOLL `ordc_voll` $5,000 (PUCT 52631, eff.
2022-01-01), X `ordc_mcl_mw` 3,000 MW (OBDRR038/52373), the 2019/2020
PUCT-48551 curve shift `ordc_lolp_shift_sigma` 0.5σ (a mean shift, not σ
inflation — web-verified), and the OBDRR048 multi-step RTORPA floor ($20 ≤
6,500 MW / $10 ≤ 7,000 MW, date-gated at its 2023-11-01 effective date).
All knobs are tier-1/2 scenario fields with citations in the registry; a
PUCT cap change is a runnable scenario (pre-Uri $9,000 tested: 2023 tail
moves up, mean adder $2.97→$5.37, >$500 hours 15→22 — direction correct).
Implementation: `results/scarcity.py` + `scripts/derive_ordc_overlay.py`
(post-processes a bundle; reconstructs the exact hourly availability via a
new `run_year(fleet_only=True)` exit — no LP re-solve) writing
`scarcity.parquet` (lmp + scarcity_adder + lmp_scarcity) next to the
untouched energy-only series; `analyze_lmp_residual.py --with-scarcity`.
RTC+B (2025-12-05) retired the ORDC for AS demand curves — ASDCs stay
VOLL-anchored/ORDC-shaped, so the overlay remains the right first-order
forward-year scarcity representation. RTORDPA (reliability deployments) not
modeled. One genuinely unverifiable input: the seasonal/TOD-block μ/σ
(ERCOT NP6-576-ER — ercot.com egress-blocked from this environment, no
secondary source quotes 2022-25 values). Flat fallback σ=1,400 MW bounded a
priori from the OBDRR048 floor anchor (at σ=2,800 a $10 floor at 7 GW would
be vacuous); `ordc_lolp_params_path` takes the published table when fetched
— the highest-value follow-up.

**Diagnostic first (the honesty gate) — PASSED.** Before any adder:
actual-minus-model residual vs reconstructed model headroom is cleanly
monotone in 2023 (>20 GW: −$1; 6-8 GW: +$860; <4 GW: +$2,181; Spearman
−0.48 Jun-Sep), the actual ≥$200 hours sit at the thin end (median headroom
8.1 vs 23.0 GW overall, 100 of 181 in Aug), and 2024/25 tail hours sit fat
(10.4 / 16.1 GW medians). The outage overlay / load shape is sound; the
miss is the price mechanism, as diagnosed in Runs 85-87 §D.

**AS netting — investigated, REJECTED as default (the campaign's main
empirical finding).** Netting the published AS plan (8,100 MW, IMM 2023
SOM) out of headroom — the brief's proposed reserves definition — puts
model reserves at/below the MCL in 1,000+ hours of 2023 vs 104 actual
>$500 hours: MAE 32.1→512 / 7.3→100 / 2.2→43. Structural reason: ERCOT's
published reserve inputs (RTOLCAP/RTOFFCAP) *count* AS-held capacity as
reserves, so subtracting the AS plan double-counts scarcity. Default
`ordc_as_plan_mw=0`: model headroom (thermal avail − dispatch + storage
cap−dis+chg + renewable curtailment headroom, hydro excluded) plays
RTOLCAP+RTOFFCAP, all-online (the LP has no commitment state — documented
approximation, both directions: perfect-commitment headroom overstates
on-line reserves in shoulder hours; missing Load Resources ~2-3 GW
understates them).

**Validation (gates vs run92_kiamichi, defaults).** Monthly LMP MAE
(demand-weighted): **2023 32.1 → 28.0** (>=$200 hours 0→31 vs 181 actual,
>$500 0→15 vs 104, max $3,131; Jun-Sep $·h gap 12% closed) — the ≤~15
target is **missed honestly**; **2024 7.3 → 7.9 and 2025 2.2 → 2.2 hold
the ±$1 gate** (adder >$1 in 163/28/4 hours per year — the published curve
indeed rarely binds in the comfortable years). σ-sensitivity (reported,
not tuned: σ=2,800 would give 2023 MAE 11.1 and hold the other gates, but
it contradicts the floor anchor and picking it for the score is the
forbidden fit). Remaining-gap attribution: (a) perfect-commitment headroom
in the $100-1,000 shoulder hours, (b) the IMM-documented 2023 artificial
scarcity (conservative ECRS deployment roughly doubled Jun-Dec 2023 RT
prices, >$12B — flowed through RTORDPA/deployments an ORDC-only overlay
correctly does not reproduce), (c) the unverified σ. Volumes tripwire: the
overlay only adds files (`availability.parquet`, `scarcity.parquet`); no
tracked bundle file modified; `_session_score run92_kiamichi` unchanged by
construction. Dashboard monthly-LMP panel deliberately untouched.

**Revenue wiring (the capacity-expansion deliverable).** Audit: forecast
retirement/new-entry/CCS screens consumed raw LP duals
(`runner.py` `prior_results["prices"]` → `capacity.evolve_fleet` →
`apply_economic_retirements` inframarginal margin, `estimate_expected_revenue`)
— the over-retirement bias, confirmed. Fixed: with
`scarcity_pricing_enabled` (ERCOT-only) the runner now hands
`prices + adder` to the capacity-economics path; persisted results and
volumes untouched; capacity-market ISOs untouched. Per-class backcast
revenue with the adder moves in the sane direction and order:
**CT_PEAKER 2023 +83%, storage discharge +168%**, ST_GAS +46%, CC_REGULAR
+20%, wind +9%; 2024 +33/+92%; 2025 ≈ +0% (comfortable reserves). Unit
tests `tests/test_scarcity.py` (13: pin/cap/floor/monotonicity/season-block
mapping/headroom composition/backcast floor gating).

---

## NYISO 2025 — EIA-930 refresh unblock + price re-score (2023 & 2025) (2026-06-12)

**Run `results/calibration/nyiso_p12_2025_refreshed`, dashboard `nyiso 2025
refreshed`.** Unblocks the year P12 had to file as data-blocked and re-scores
the price metrics P12 had to leave as "level-only" (U2/P10 LMP had not landed).
Branch `claude/nyiso-2025-refresh-rescore`.

### The unblock — refreshed EIA-930 NYIS extract spans full 2025

The user re-uploaded the EIA-930 raw long files
(`inputs/raw-data/eia-930/NYIS_region.parquet` + `NYIS_fueltype.parquet`, now
2015–2026). Regenerated the wide hourly with
`python scripts/convert_eia930.py NYIS --input-dir inputs/raw-data/eia-930 --force`:
`NYIS hourly` now carries **8,760 h for 2025** (Demand non-null 8,760/8,760),
where the old extract stopped at **Q1'25 (2,154 h)**. 2023 (8,760) and 2024
(8,784, leap) are byte-identical to the prior file — Demand 147.05/150.88 TWh,
net interchange −23.45/−20.39 TWh, WND 4.60/6.04 TWh all unchanged — so the
2023 keeper, the other ISOs, and every loader test are untouched (only the
NYIS parquet changed). `nyiso_net_interchange(2025)` now returns the measured
series (**−19.09 TWh**, was `None`); `_load_nyiso_hourly_demand(2025)` returns
151.55 TWh on the EIA-930 clock instead of the gross demand-profiles fallback.

### The over-gen closes — interchange served (was the +22.7% wedge)

P12's `nyiso_p12_base_2025` over-generated **+22.7%** (151.9 vs EIA-923 123.8
TWh) purely because `load_demand` fell back to gross demand and served **0** of
the import wedge. With the refreshed parquet the measured net interchange is
served by default:

| | model | actual EIA-930 |
|---|---|---|
| net interchange (TWh) | **−19.09** 🟢 | −19.09 |
| duration RMSE | **0 MW** | — |
| import-hours | 99.8% | 99.8% |
| diurnal corr | **+1.00** | — |

Fuel mix (`--commitment`):

| fuel | model | EIA-930 | Δ930 | EIA-923 (prelim) | Δ923 |
|---|---|---|---|---|---|
| gas | 68.30 | 70.25 | **−2.8%** | 60.21 | +13.4% |
| nuclear | 28.38 | 27.95 | +1.5% | 28.41 | −0.1% |
| wind | 7.05 | 7.05 | exact | — | — |
| hydro | 21.05 | 24.10 | −12.7% | 21.05 | budget |
| oil | 0.02 | 0.18 | — | 1.06 | U4-gated |
| **TOTAL** | **132.76** | 129.54 | **+2.5%** | 115.84 | +14.6% |

**EIA-923 2025 is the preliminary M-file** (total 115.84 TWh, ~17 below served
demand; solar 0.66, biomass/oil under-reported) — **flagged, not chased**.
Against EIA-930 (the operationally consistent basis) gas is **−2.8%** and total
**+2.5%**: the over-gen is gone and the gas level is sane. The +13.4% vs 923
reads off the under-reported preliminary total, the same EIA-930/EIA-923
demand-basis gap documented for the 2023 keeper, not a dispatch error.

### Price re-score — P12's "level-only" metrics now scored (2023 + 2025)

Scored both the 2023 keeper (`nyiso_smoke_2023`) and this 2025 run against
`actual_lmp.json` (per-zone DA/RT levels) + `actual_lmp_hourly_NYISO.parquet`
(system duration, via `scripts/analyze_lmp_residual.py`).

**System level + duration ($/MWh):**

| year | model avg | actual RT | actual DA | resid RT | p50 m/a | p90 m/a | p99 m/a | max m/a |
|---|---|---|---|---|---|---|---|---|
| 2023 | 41.79 | 30.29 | 31.11 | +11.50 | 36/26 | 66/42 | 104/120 | 236/1147 |
| 2025 | 69.24 | 60.73 | 60.71 | +8.51 | 57/45 | 114/114 | 157/222 | 314/2074 |

**Per-zone average (model vs actual DA, resid $/MWh):**

| zone | 2023 model | 2023 actDA | Δ | 2025 model | 2025 actDA | Δ |
|---|---|---|---|---|---|---|
| Upstate_West | 38.94 | 26.08 | +12.86 | 66.82 | 55.89 | +10.93 |
| Capital_Hudson | 43.42 | 36.38 | +7.04 | 70.61 | 65.15 | +5.46 |
| Lower_Hudson | 43.42 | 33.58 | +9.84 | 70.61 | 62.99 | +7.62 |
| NYC | 43.42 | 33.95 | +9.47 | 70.61 | 65.41 | +5.20 |
| Long_Island | 43.42 | 40.77 | +2.65 | 70.61 | 68.87 | +1.74 |

**Reading.** Both years **over-price the mid-merit band** (2025 p50 $57 vs $45)
and **under-price the scarcity tail** (2025 p99 $157 vs $222; max $314 vs
$2,074) — the no-ORDC / no-reserve-scarcity signature (the model carries no
scarcity adder). The 2025 p90 is near-exact ($113.7 vs $113.6). The model
collapses the four downstate zones to one price: it captures the upstate-cheap
/ downstate-dear separation (Upstate_West ≈ $4 below downstate) but not the full
actual J−A spread (≈$13), the documented interface-TTC / downstate-congestion
structural item (U7). Long_Island is the closest zone both years (+$1.7/+$2.7);
the over-pricing is heaviest upstate, consistent with the gas-level floor
sitting above measured upstate LBMP. Per-run detail in the bundle's
`SUMMARY-nyiso-2025-refreshed.md` / `PRICE-RESCORE-*`.

### Discipline & scope

Structural-discipline run (playbook §6): **no offer band tuned**. oil stays
**U4-gated** (no Transco-Z6 / Iroquois daily gas basis uploaded for NYISO —
monthly-average Jan gas stays below distillate parity). **2024 stays blocked**
on `NY_2024` unit-level CEMS + the missing `NYISO_2024_renewable_capacity.csv`.
**ERCOT/PJM/CAISO/NEISO untouched** — the only data change is the `NYIS hourly`
parquet, whose 2023/2024 content is byte-identical pre/post; loader/demand/
renewables tests pass (the 3 CAISO zonal-share failures are pre-existing and
unrelated, per the P9b note). doc-00 status table updated (NYISO now 2023+2025,
price-scored); dashboard carries the run; `docs/multi-iso/nyiso-backcast-2023.md`
and `docs/calibration-best-so-far-nyiso.md` updated with the 2025 results and
the now-scored price metrics.

## ERCOT Runs 93–96 — retune on the corrected fleet (2026-06-12)

**Campaign: re-derive the offer-curve calibration on the post-Kiamichi
fleet (run 92's open item) and name a keeper that beats run 92's 6 class
fails on both gates with no regression. Method: measured probe vectors
(runs 93/94/95/95b — every live lever priced as a pure response vector vs
`run92_kiamichi`), then ONE keeper run (96) with doses solved against the
measured constraint system. Runs 95 and 95b ran in parallel (rule #11);
95b from a sparse git worktree pinned at HEAD so 95's Kiamichi bins edit
could not contaminate it (the bins CSV is re-read per year mid-run).
Result: run 96 = run 92 + a single lignite-floor move, 5 fails,
both gates held — the keeper.** All TWh below are model − benchmark vs
`run92_kiamichi` unless said otherwise; scoring is the size-aware bar +
fuel-split gate of `calibration-best-so-far.md`; LMP is the energy-only
monthly demand-weighted MAE (gate ±$1 of 32.1/7.3/2.2).

### The measured vectors (TWh per unit dose, vs run 92)

| cell | V_CC (93: CC econ_high −0.40→−0.30) | V_CT (94: CT econ_high +0.20→−0.20 + Kiamichi trim v1) | V_floor (95−94: lignite floor 0.75→0.69 + Kiamichi v2) | V_CCc (95b: CC committed −0.05→+0.05) |
|---|---|---|---|---|
| CC 23/24/25 | −2.68/−2.16/−2.15 | −0.24/−0.25/−0.21 | −0.36/−0.40/−0.02 | −2.12/−1.63/−1.51 |
| PRB 23/24/25 | +1.41/+0.91/+0.61 | −0.02/−0.11/0.00 | −0.16/−0.15/−0.00 | +0.83/+0.47/+0.45 |
| ST_GAS 23/24/25 | +0.20/+0.15/+0.35 | −0.19/−0.13/−0.16 | −0.02/−0.03/−0.00 | +0.20/+0.20/+0.25 |
| LIG 23/24/25 | +0.26/+0.23/+0.03 | 0.00/−0.01/−0.00 | **+0.62/+0.71/+0.04** | +0.22/+0.19/+0.02 |
| CT 23/24/25 | +0.01/+0.01/+0.12 | +0.45/+0.49/+0.36 | 0.00/+0.01/−0.00 | +0.06/+0.07/+0.08 |
| 2023 coal split (from +1.5%) | +2.7 | ~0 | +0.7 | +1.7 |
| ML/LS 2023 guard (from 582/797 GWh) | +582/+287 | ~0 | **−67/−28** | +339/+194 |
| LMP (32.06/7.29/2.17) | held | held | held | ≤$0.12 — lever NOT price-aborted |

**Run 93 (`run93_jacobian_probe`, prior session).** CC econ_high give-back
full dose: ~3× the stale pre-Kiamichi jacobian; FAILS 2023 at β=1 (coal
split +4.2%, guards 1164/1084) → β ≤ 0.37 on the split, ≤ ~0.71 on guards.

**Run 94 (`run94_ct_kiamichi`, prior session).** CT recovery γ=1 leaves CT
failing all years and flips ST_GAS 2025 to a NEW fail (−1.15 vs the −0.99
knife-edge pass); Kiamichi cost-side trim v1 (20/65/15, econ HR 1.06,
committed in inputs) moved Kiamichi only −0.12/−0.14/−0.18.

**Run 95 (`run95_lignite_probe`, this session).** Lignite-floor endpoint
probe (0.69 = 2× the 0.72 candidate) on the run-94 base + Kiamichi bins v2
(peaking 15→30). Findings: (a) the floor vector flips lignite 2024
(−1.66 → −0.96) with mild PRB intra-coal steal (−0.15) and +0.7 split
leakage; (b) guards IMPROVE (ML23 582→515 — the floor redistributes
lignite toward the non-guard plants); (c) **Kiamichi v2 is a dead lever**:
6.06/6.85/6.17 → 6.03/6.77/6.17 TWh — the over-run is bid-price-driven,
not capacity-bound; withheld capacity doesn't bind. v2 NOT committed
(inputs stay at the run-94 v1 trim).

**Run 95b (`run95b_cc_committed_probe`, this session).** CC_REGULAR
committed pure pair on the run-92 base, one clean +0.10 step (a measured
endpoint extends the trust region — the run-82 lesson was extrapolating,
not probing). The lever works mechanically (CC sheds −2.12/−1.63/−1.51;
Kiamichi itself sheds 0.40–0.62 — the class-wide committed multiplier
prices its 20% committed tranche; LMP barely moves) **but the 2024 refill
is too dilute**: +0.47 PRB / +0.20 ST_GAS per unit vs the +1.53/+1.40
those flips need, while the costs scale fast (2023 coal split +1.7/unit —
95b itself FAILS the 2023 gate both fuels at δ=1 — guards +339/+194,
gas 2023 −0.7%). **The 4-fail path is measured dead**: within the split
budget (0.7λ + 1.7δ + 2.7β ≤ 1.0 from +1.5) a δ of ~0.2 buys +0.09 PRB
2024 — an order of magnitude short. "Realistic best ≈ 5 fails" confirmed.

### Run 96 — the keeper (`run96_lignite_keeper`, dashboard `run96 lignite keeper`)

Doses solved smallest-first against the constraint system: **λ=1 (lignite
floor 0.69, the measured endpoint), β=γ=δ=0.** γ flips nothing (CT 2023
needs γ≥1.16, blocked by ST_GAS 2025 and partly structural — the IMM 2023
SOM AS-deployment wedge, see the ORDC entry: do NOT chase the last
~1–1.5 TWh of CT with fleet-wide levers); β and δ eat the 2023 coal-split
budget the floor needs (any β>0 at λ=1 breaches +2.5%); δ at the allowed
~0.2 buys only cosmetics. So the keeper is run 92 + one knob. Measured:
**5 in-scope fails vs run 92's 6** — lignite 2024 −1.66 → **−0.95 PASSES**;
remaining: CT_PEAKER −1.51/−2.54/−1.74, PRB 2024 −8.8%, ST_GAS 2024 −2.41.
No new fails, no regressions: ST_GAS 2025 −0.99 (0.01 margin) holds, CC
2023 −1.6%, PRB 2024 drift −3.71→−3.85 inside an already-failing cell
(size-aware noise, run-91 precedent). Splits: 2023 −2.1/+2.3 PASS, 2024
coal −8.3% (improved from −9.3, still the structural residual), 2025 PASS.
Guards ML/LS 2023 546/773 (better than run 92); ML 2025 +1.46 (watch).
LMP MAE 32.06/7.31/2.17 — identical to run 92. Kiamichi 6.04/6.78/6.17 vs
~5.2 actual (within-class watch). PRB mean +1.3/−8.8/−0.1 → −2.5%.
`calibration-best-so-far.md` rewritten (OPEN status cleared).

### ORDC overlay follow-through

`derive_ordc_overlay.py run96_lignite_keeper --revenue-report` (post-solve,
no LP): **the ORDC baseline bundle moves from run92_kiamichi to the
keeper**; `availability.parquet` + `scarcity.parquet` committed in the
bundle. Tail metrics next to the energy-only gate numbers: 2023 MAE
32.1 → **28.0** (>$200 hours 0→31 vs 181 actual, >$500 0→15 vs 104, max
adder $3,131, Jun–Sep $·h gap 12% closed); 2024 7.3 → 7.9 and 2025
2.2 → 2.2 hold the ±$1 gate (adder >$1 in 163/28/4 h). Revenue direction
sane and ordered: CT_PEAKER 2023 +84%, storage discharge +169%, ST_GAS
+46%, CC +20%, wind +9%; 2025 ≈ +0%.

### Bookkeeping

Jacobian: runs 91–96 classified in the deriver REGISTRY (91→91055 pure,
92 structural fleet fix, 92→93 pure, 94/95 sidecars so the chain pairs
93→95b — pure, the corrected-fleet committed step; 96 structural) →
**12 ERCOT pure pairs** in `inputs/processed/offer_curve_jacobian.csv`
(committed). Dashboard keeps 5 ERCOT runs: 92, 94, 95, 95b, 96 (95 pruned
90; 95b pruned 91; 96 pruned 93 — probe vectors live here + in the
sidecar definitions). Probe sidecars marked "MEASURED PROBE, not a
keeper" with their response vectors. Dead levers measured this campaign
(do not re-probe): Kiamichi capacity withholding (v2), CC committed at
meaningful dose (split/guards), CT econ_high beyond the ST_GAS-2025
budget, plus the prior list (CT/ST_GAS peak bands, CT committed,
Kiamichi cost-side nudges).

## ERCOT Runs 97a/97b — per-plant retune + the BTM vintage fix (2026-06-13)

**Campaign: the runs 93–96 retune exhausted the class-wide offer-curve
dose space at 5 fails, so this session localized the remaining fails to
plants (the run-96 bundle's per-plant panels) and fixed what was honestly
fixable. Result: run 97a is the keeper — 4 in-scope fails, both gates, no
regressions, every remaining fail structurally diagnosed. The probes ran
in parallel (97a gas-side in the main tree, 97b coal-side in a sparse
worktree, both off the run-96 config).**

### The per-plant decomposition (run 96 bundle, model − CAMPD/923)

- **ST_GAS 2024 (−2.41) is not diffuse**: V H Braunig −3.2 (and −2.5/−3.7
  in 2023/25!), O W Sommers −0.8, Cedar Bayou −1.1 — the CPS San Antonio
  self-scheduled steamers — offset by over-run elsewhere in the class.
- **PRB 2024 (−3.85) is one plant**: W A Parish −3.7 (Spruce −1.6, offset
  by over-runners). Parish is never off (8,760 CAMPD op-hours every year,
  p10 ≈ the model's 15% floor — the floor is right), median 38–45% of cap
  in 2023/24; it has NO plant-specific F923 coal price (class fallback).
- **CT_PEAKER decomposes three ways**: (1) San Jacinto (7325): bins call it
  CT_PEAKER but it behaves as a refinery cogen (flat ~50% CF; EIA-923 says
  chp=N so the dominant-class override pins the class); its 65% must-run
  share is BTM-removed and added back from the plant's 923 netgen — which
  the incomplete 2025 vintage lacks entirely, zeroing 0.86 TWh of add-back
  while the CAMPD-backfilled benchmark keeps the plant. The CT 2025 "fail"
  was this artifact. (2) ~1.0 TWh/yr of bench sits in non-CEMS small
  peakers (Ector County 649 vs 119 GWh, Permian Basin 460 vs 47, Pearsall,
  …) the merit order can't reach. (3) Of the CEMS-covered CT energy, 31/38/
  44% (2023/24/25) ran in hours with RT price below the unit's marginal
  cost — the AS/RUC deployment + RA wedge, 1.4–2.3 TWh/yr, quantifying the
  IMM-documented structure flagged in the ORDC entry. The model already
  matches CEMS for CAMPD-covered CT plants (2024 model 5.03 vs 5.38 CEMS).
- **Bonus: Sand Hill (7900)** — a CC+CT site flattened to one 7.37-HR
  CC_REGULAR bin, model 3.61 vs 2.13 TWh actual in 2024 = a third of the
  CC 2024 over-run. Its CT capacity dispatches at the CC heat rate.

### Run 97a (`run97a_gas_plants`) — KEEPER, 4 fails

Run-96 config + (1) `--btm-backfill-year 2024` — new flag, mirrors
`--hydro-backfill-year`: a plant whose (plant, class) 923 total is zero
for the year borrows the prior year's, ONLY if CAMPD shows it generating
(CEMS-silent cogens stay dropped on both sides). Measured: CT_PEAKER 2025
BTM 0 → 0.85 (San Jacinto), CC_CHP +0.14, all else ~0 — surgical. (2)
Braunig + Sommers `Pct_Committed` 30 → 40. Measured: **CT_PEAKER 2025
−1.74 → −0.90 PASSES**; ST_GAS 2023 −0.31 → +0.06, 2024 −2.41 → −1.99
(still fails), 2025 margin −0.99 → −0.73; CC/PRB/lignite hold; splits
2023 −2.0/+2.1 PASS; guards 498/760 (best of the campaign); LMP
32.08/7.34/2.16 (gate held). Braunig/Sommers own-gain measured at only
+0.17 TWh each — the ST_GAS committed band carries the startup-spread
markup (Braunig startup 28.5 t CO2, ~12 starts/yr), so the committed-share
lever saturates: ST_GAS 2024 is not reachable representationally. The
Sand Hill committed/peaking CSV edit in the run note was a measured
**no-op** — `cc_committed_per_plant`/`cc_peaking_per_plant` override CSV
shares for CAMPD-covered CC plants (Kiamichi only takes CSV values because
it has no CAMPD extract) — reverted from inputs; per-plant CC surgery
needs `--plant-tranche-config` (follow-up).

### Run 97b (`run97b_coal_plants`) — REJECTED, the screen finding

Parish + Spruce `Pct_Committed` 20 → 30 (econ 50 → 40), the CAMPD-grounded
"self-scheduled baseload" representation. Measured BACKFIRE: PRB 2024
−3.85 → **−4.68** (−0.82), PRB 2023 +0.59 → +0.09, CC 2024 +0.41.
[MECHANISM CORRECTED in the "Runs 98a/98b" entry below — the original
commitment-screen reading was wrong (P2 was off): the P1 startup
amortization lands solely on the committed tranche (only it has min-run
params; COAL bins carry $100/MW), pricing the committed band ABOVE the
econ ramp top, so the share shift moved capacity INTO the startup-bearing
band.] The coal committed-share lever is measured DEAD at this operating
point; Parish's wedge is the same self-commitment/out-of-merit structure
as the CT class. No inputs kept.

### Verdict + follow-ups

Keeper run 97a: 4 fails (CT 2023 −1.53 / CT 2024 −2.56 / PRB 2024 −3.94 /
ST_GAS 2024 −1.99), ties run 85's old 4-fail mark on the corrected fleet,
beats run 96's 5; `calibration-best-so-far.md` updated; ORDC overlay
re-derived on the keeper (2023 MAE 32.1 → 28.0, 2024/25 hold ±$1; baseline
bundle moves run96 → run97a; availability+scarcity committed in-bundle).
All four remaining fails share one structure: **self-committed /
AS-deployed energy the energy-only merit order cannot dispatch** — the
candidate mechanism is an explicit deployment overlay built from measured
out-of-merit CEMS hours (run ≥ X MW while RT < marginal cost), analogous
to the historic outage overlay; that is a methodology change needing user
sign-off. Other follow-ups: Sand Hill per-plant tranche config (~1.5 TWh
of CC 2024 over-run), Cedar Bayou, NP6-576-ER μ/σ (ercot.com still
egress-blocked, 403, retried 2026-06-13). Forecast note: the kept changes
are fleet representation (bins committed shares) and a backcast reporting
flag — the bins edits flow into forecast mode; the flag is
backcast-reporting only and changes no dispatch.

### Bookkeeping

Dashboard: 97a/97b registered; retention prunes run92 + run94 entries
(bundles stay; run92 remains the documented baseline in this log).
Jacobian REGISTRY: 96 → 97a and 97a → 97b classified structural (bins/
reporting, no curve knobs) — 12 ERCOT pure pairs unchanged. New dead
levers (do not re-probe): coal `Pct_Committed` raises under the commitment
screen (97b), ST_GAS committed-share beyond ~+10 pts (startup-spread
saturation, 97a), per-plant CC CSV shares for CAMPD-covered plants (the
override no-op).
## NEISO offer-curve probe panel + Jacobian — P12 keeper sensitivity map (analysis only) (2026-06-13)

**Runs `neiso_probe_base_2024` + 10 single-knob probes; dashboard `neiso 8
probe-cc-eh-plus` / `neiso 9 probe-cc-eh-minus` (9 dominated entries registered
then pruned per the top-5 rule; all 11 bundles kept on disk).** Goal: map the
offer-curve band sensitivities around the NEISO P12 primary-year keeper
(`neiso_p12_base_2024`) to inform any future refinement. **The keeper is NOT
re-tuned** — zero changes to the sign-off config; ERCOT/PJM/CAISO untouched
(their `offer_curve_jacobian.csv` rows byte-identical).

### Panel design

`neiso_probe_base_2024` re-runs the P12 keeper config on current main
(run80a-style code-accumulation anchor): it reproduces the keeper **exactly**
(identical per-class TWh and $57.06 demand-weighted price), so no NEISO code
drift since sha `6fbf83d` and probe deltas read directly against the keeper.
Ten ±0.05 single-knob probes chain off it via `--offer-curve-delta-json`
(each consecutive bundle pair is a verified pure-curve observation; REGISTRY
entries added to `scripts/derive_offer_curve_jacobian.py`, plus the NEISO
state set for the merit-order adjacency check):

CC_REGULAR committed ±, CC_REGULAR econ_high ±, CT_PEAKER committed ±,
ST_GAS committed −, ST_GAS peak −, CC_CHP committed −, CT_CHP committed −.

**No OIL band exists to probe.** `fossil_classes()` carries no OIL/ST_OIL
offer-curve class: the oil-primary steam fleet (Wyman, Canal, …) dispatches
under the non-fossil `oil` class with no band knob, and the dual-fuel CT/ST
gas tranches live in CT_PEAKER/ST_GAS. The ST_GAS probes are therefore the
panel's oil/dual-fuel coverage — and they are **dead knobs** (below).

### Knob → objective map (Jacobian, 10 pure pairs, year 2024)

`python scripts/derive_offer_curve_jacobian.py --iso NEISO --baseline
neiso_p12_base_2024 --validate-run neiso_probe_base_2024` → 70 NEISO cells in
`inputs/processed/offer_curve_jacobian.csv`. High-confidence rows:

| knob | twh (own) | twh (cross) | lmp d(MAE)/d(mult) | shape d(gas NRMSE) |
|---|---|---|---|---|
| CC_REGULAR.econ_high | CC_REGULAR −1.47 ±0.09 | CC_CHP +0.37, CT_PEAKER +0.12 | **+5.4 ±0.7** | −0.0046 |
| CC_REGULAR.committed | CC_REGULAR −0.27 ±0.03 | CC_CHP +0.08 | +2.1 ±0.8 | −0.0019 |
| CT_PEAKER.committed | CT_PEAKER −0.09 ±0.01 | CC_REGULAR +0.07 [low] | +0.02 [low] | +0.0004 |
| CC_CHP.committed | CC_CHP −0.20 [med] | CC_REGULAR +0.18 [med] | −0.02 [low] | ≈0 |
| ST_GAS.committed / .peak | **0 — dead** | 0 | 0 | 0 |
| CT_CHP.committed | +0.06 [low, n=1] | — | — | — |

Reading: **NEISO's TWh block is essentially band-immune.** The largest
sensitivity (CC_REGULAR.econ_high, −1.47 TWh/unit-mult) moves only ±0.07 TWh
at the ±0.05 probe size — with no coal and a trivial CT/ST fleet, the CC class
has no substitution partner and band moves just relabel its own price. Every
cross-coupling is merit-order-adjacency-consistent (overlap mass >99%). The
real leverage is on the **price level**: econ_high ±0.05 moves the
demand-weighted level ∓±~$1/MWh annual; committed ~40% of that.

### Winter-tail caveat (Jan/Feb LMP sensitivity is U4, not a band)

The econ_high price response is **winter-loaded ×2–3** (±0.05 → Jan ∓±2.2,
Feb ∓±1.4, Dec ∓±1.4 $/MWh vs ∓±0.4–0.9 mid-year): in Jan/Feb the marginal
unit is almost always CC_REGULAR on the **monthly** AGT basis, so a band
multiplier scales the documented flat winter plateau up or down. **Do not
read this as a winter-tail knob.** The price re-score attributes the winter
miss to the monthly-AGT limitation (plateau instead of daily-spot spikes;
model never clears an hour >$200 vs 44/11/160 actual) — a multiplier on a
flat plateau cannot manufacture daily variance, and the dead ST_GAS knobs
confirm no band brings the dual-fuel/oil fleet into the winter merit order
(even cheapened −0.05 it never clears; modeled oil stays 0.006 TWh). The fix
remains the **daily-AGT U4 upload** (doc-08 decision 1; P11 gap #3). Equally,
the CHP TWh "errors" (CC_CHP −0.69, CT_CHP −0.79 vs 923) are mostly the
grid-side BTM-host convention (gas vs EIA-930 is green at −2.8%), not
band-tunable — the recipe's no-btm.parquet warning applies.

### Joint-move recipe + backtest

- Default solve (balanced twh/shape/lmp, cap 0.15): **every knob
  trust-region-frozen, no move** — the solver wants extrapolations far outside
  the ±0.05 sampled range to chase structural (U4 / BTM / served-interchange)
  error. The trust region vetoing it is the correct answer.
- Capped to the sampled range (`--cap 0.05`): Δ = {CC_REGULAR committed −0.05,
  econ_high −0.05; CT_PEAKER committed +0.05; ST_GAS committed −0.045, peak
  −0.05} with predicted twh RMS 0.671→0.649, LMP MAE 18.41→18.08 $/MWh, shape
  slightly degrading. **Immaterial vs the 18.4 structural LMP residual — not
  promoted.** It also chases the 2023/24 over-pricing sign: 2025 under-prices
  (−12.5 $/MWh re-score), so the same move worsens 2025. That sign flip is the
  gas-price/U4 asymmetry, knowable from the re-score without new panels —
  2023/2025 panels skipped (the TWh block, which is what a panel uniquely
  measures, showed nothing tunable; LMP-block transfer would only re-measure
  the same plateau scaling).
- Backtest (held-out `neiso_probe_cc_regular_committed_minus`, excluded from
  the fit then predicted): TWh block prediction-error RMS **0.001 TWh**
  (CC_REGULAR +0.012 pred vs +0.013 actual); LMP −0.142 pred vs −0.094 actual
  (the up/down asymmetry of a one-sided fit); the trust region correctly
  flags the held-out one-sided move as outside the remaining sampled range —
  the run-82 regression behavior reproduced for NEISO.

### Verdict

No offer-band refinement is recommended for NEISO: the P12 structural-defaults
keeper stands. The panel's value is the fitted sensitivity matrix (any future
NEISO band discussion starts from "econ_high is the only live knob, it prices
the U4 plateau, and TWh is band-immune") and the dead-knob proof for the
oil/dual-fuel path. Reproduce a probe:
`python scripts/run_calibration_full.py --iso NEISO --year 2024 --commitment
--offer-curve-delta-json '{"CC_REGULAR":{"econ_high":-0.05}}' --out-dir
results/calibration/neiso_probe_cc_regular_econ_high_minus`.

### Re-verification on current main (2026-06-16, sha `e3329bd`)

The probe panel was built at sha `1e22402`; per-ISO CAMPD binning (W1b,
`9061ae9`/`ad0dd79`) and the AS/CT-deployment overlay generalized to NEISO
(`1bfa29f`) have landed on main since, so the `neiso_probe_base_2024`
code-accumulation anchor was re-run on current main to test for NEISO output
drift (`--iso NEISO --year 2024 --commitment`, default flags, identical to the
committed anchor). **Result: zero drift.** The recheck reproduces the committed
anchor *exactly* — max |ΔTWh| = 0.0000 across all 14 dispatch classes
(CC_REGULAR 55.24, nuclear 26.48, …) and an identical $57.06 demand-weighted P1
price. NEISO 2024 is bit-for-bit deterministic on the new binning/overlay code
(consistent with the W1c generic-coverage verification `ec714de`).

Because the base is unchanged and the ±0.05 delta mechanism is deterministic,
the 10 single-knob probe bundles are no-ops on current code; they were **not**
re-solved (identical-output compute). Rebuilding the Jacobian from the committed
parquets (`derive_offer_curve_jacobian.py --iso NEISO --baseline
neiso_p12_base_2024 --validate-run neiso_probe_base_2024`) reproduces
`inputs/processed/offer_curve_jacobian.csv` **byte-identically** (1158 cells; 70
NEISO; ERCOT/PJM/CAISO rows untouched), and the joint-move recipe is unchanged
(twh 0.671 / shape 2.151 / lmp 18.413, every useful knob trust-region-frozen).
The panel + Jacobian stand as the current-main NEISO sensitivity map; no re-tune.

Zonal/TTC re-check (same session): `test_transmission.py`,
`test_zone_assignment.py`, `test_iso_config.py`, `test_neiso_demand.py`,
`test_neiso_bins.py` — 151 pass; `scripts/neiso_zonal_sufficiency.py` reproduces
the committed `neiso-zonal-adequacy.md` table (every pocket-vs-hub median
<$1/MWh, p90 <$5 except CT-2025, |spread|>$20 hours ≤0.7%). The 4-zone topology
+ RSP Tier-3 TTC seeds carry small, winter-loaded, CT-led separation and do not
create spurious congestion — load zones and TTC links are sound. Drift-check
tooling added: `scripts/probes/_neiso_probe_compare.py` (per-class TWh + dw-price diff
of two bundles) and `scripts/_run_neiso_probe_panel.sh` (panel reproduce
harness, concurrency-capped at 2 for the multi-GB per-plant LP).

## NEISO — full 3-year backcast re-run on current main (2026-06-16, sha `8429fdb`)

Ran the complete 2023+2024+2025 NEISO backcast (full 8760, commitment on, keeper
config; 2025 with `--hydro-backfill-year 2024`) in parallel on current main, to
confirm the P12 sign-off still holds end-to-end after the W1b binning + overlay
accumulation. **All three years reproduce the committed P12 keepers
byte-identically** (`neiso_cal3_{year}` vs `neiso_p12_*`: max |ΔTWh| = 0.00000,
identical demand-weighted P1 price 56.45 / 57.06 / 55.07). The re-run bundles
were therefore deleted (exact duplicates of the keepers); the keepers stand as
the 3-year calibration of record.

### Scorecard — model vs EIA-930 delivered (the convention-correct basis)

| year | gas | nuclear | wind | solar | hydro | oil | net interchange | price avg |
|---|---|---|---|---|---|---|---|---|
| 2023 | 53.68 (−3.2%) | 23.17 (exact) | 3.25 (exact) | 0.89 (exact) | 8.49 (−3.2%) | 0.02 vs 0.32 | −15.14 TWh **exact** (RMSE 0) | $53.61 |
| 2024 | 57.94 (−2.9%) | 26.48 (+0.3%) | 3.45 (exact) | 1.31 (exact) | 6.67 (−9.7% vs 930 / −0.6% vs 923) | 0.01 vs 0.37 | −10.30 TWh **exact** | $55.72 |
| 2025 | 57.75 (−3.9%) | 27.64 (+0.7%) | 4.53 (exact) | 1.58 (exact) | 6.65 vs 5.12 (**+30%**) | 0.01 vs 1.24 | −8.13 TWh **exact** | $53.46 |

Big structural blocks pass across all three years: gas −2.9 to −3.9% vs EIA-930,
nuclear/wind/solar essentially exact, net interchange exact (served EIA-930
schedule), price level $53–56. Use **EIA-930** for the renewable rows — EIA-923
`generation_twh.solar` (3.7–4.5 TWh) includes distributed/BTM PV that the model
nets into demand (front-of-meter only, doc-08 decision 7), so a raw-923 solar
comparison spuriously reads −70%. The 2025 EIA-923 vintage is also an incomplete
early release (923 TOTAL 85.3 vs 930 100.3 TWh; 923 hydro 0.09, nuclear share
inflated) — gate 2025 on EIA-930, not 923.

### Open gaps (unchanged from P12; not offer-tunable)

1. **Winter oil / Algonquin daily basis (gap #1, upload U4).** Modeled oil
   0.01–0.02 TWh vs actual 0.32 (2023) / 0.37 (2024) / **1.24 (2025)** TWh, and
   the winter price tail is a flat monthly-AGT plateau (model max $195–259 vs
   actual daily spot spikes). The monthly AGT basis cannot manufacture daily
   variance and never trips the dual-fuel CT/ST switch — the jacobian panel
   already proved the ST_GAS bands are dead knobs here. Needs the **daily** AGT
   upload (U4); not recoverable by offer-band tuning. 2025 is the worst year
   (1.24 TWh oil), so U4 matters most there.
2. **2025 hydro budget.** The 2024-backfill proxy gives 6.65 TWh vs EIA-930's
   5.12 (+30% / +1.5 TWh) — 2025 was a materially lower hydro year than 2024, so
   the flat backfill over-states it. A 930-annual-scaled 2025 budget (≈5.1 TWh on
   the 2024 monthly shape) is the data-grounded fix and the one improvement
   available without an external upload.
3. **Gas −3% vs EIA-930** is consistent across years and partly the mirror of
   the missing winter oil (≈0.3–1.2 TWh that should displace gas) plus biomass
   classification; it tightens once U4 lands.

Conclusion: the NEISO model is a calibrated 3-year backcast (P12 sign-off holds
byte-for-byte on current main). No offer-curve tuning is warranted (structural
gaps, dead-knob panel). Actionable next steps are the U4 daily-AGT upload (winter
tail/oil, user-supplied) and the 2025 hydro 930-scaling refinement.

### 2025 hydro repinned to measured EIA-930 monthly (`neiso_hydro930_2025`, KEEPER for 2025)

Implemented gap #2: the new `--hydro-eia930-monthly` flag repins the assembled
conventional-hydro monthly energy budget to the measured EIA-930 `NG: WAT`
(water) monthly total for the ISO/year, preserving the per-plant within-month
shares (`data/eia_loader.py::measured_monthly_hydro` →
`data/hydro.py::load_hydro_budget(monthly_target_mwh=…)`). The 2024 backfill
supplies the per-plant spatial coverage the incomplete 2025 EIA-923 vintage
lacks; the EIA-930 pin then fixes the energy level **and** the monthly shape
(2025 is dry Aug–Oct: 0.15–0.19 TWh/mo vs the flat-2024 0.4–0.7). The MW
envelope is left at physical capability — only the inter-temporal energy limit
moves. Opt-in (default off changes no existing run); the 2025 keeper command is
now `--hydro-backfill-year 2024 --hydro-eia930-monthly`.

Effect — `neiso_hydro930_2025` vs the `neiso_p12_hydrofix_2025` flat backfill:

| fuel | flat-2024 backfill | EIA-930 monthly pin | EIA-930 actual |
|---|---|---|---|
| hydro | 6.65 TWh (+30%) | **5.11 (−0.2%)** | 5.12 |
| gas | 57.75 (−3.9%) | **59.22 (−1.4%)** | 60.09 |
| price avg | $53.46 | $54.31 | — |

The 1.5 TWh of over-stated hydro inflow had been displacing gas; pinning hydro
to the measured series corrects **both** the hydro row and the −3.9% gas miss in
one move (the mechanism filed under gap #3), with nuclear/wind/solar/interchange
still exact. Improvement uses measured EIA-930 data, not an estimate
(claude.md data-preference rule). Tests: `test_hydro.py::test_2025_eia930_monthly_pin`
(+ wrong-length / unknown-ISO guards); full suite 1120 passed (the 3 CAISO
`test_eia_loader` zonal-share failures are pre-existing on `origin/main`,
unrelated). ERCOT/PJM/CAISO/NYISO hydro byte-identical (flag default off).
Remaining 2025 gap is the winter oil/AGT tail (U4, the larger lever).

---

## CAISO 3 — offer-curve probe panel + Jacobian (sensitivity map, 2023) (2026-06-13)

**Goal: map CAISO offer-curve band sensitivities to inform calibration — NOT a
tuning pass.** No keeper config is changed; no band move is committed. The
panel quantifies which knobs do what *under the current structural state*, and
that state includes the **OPEN import-tranche mis-pricing (P9/P12)**: the
priced WECC node over-imports +114%/2023 and owns the $45–90 margin (CAISO 2
entry above). Every number below is conditional on that — re-probe after the
re-price.

### Panel design

12 bundles, 2023 only (the keeper-designate `caiso_1_priced_ix` covers
2023-2025; 2023 confirmed as its first dispatch year), all
`run_calibration_full.py --iso CAISO --year 2023 --commitment`:

- **`caiso_probe_base`** — zero-delta code baseline. HEAD had moved 87
  src/inputs files since `caiso_1_priced_ix`'s sha (`a1dc6e2`), so probes
  paired against the old bundle would auto-classify structural; the re-run
  reproduces its 2023 numbers exactly (avg price $77.34, 0 negative hours) —
  the code drift is CAISO-inert, but the chain discipline stands
  (run80a pattern).
- **11 single-knob ±0.05 probes** chained off it (dashboard `caiso 3` +
  `3a–3k`; bundles `results/calibration/caiso_probe_<class>_<band>_<sign>`):
  CC_REGULAR committed −/+ (both signs; the + side run last and **held out**
  for the back-test), econ_low −, econ_high −, peak −; CT_PEAKER committed −,
  econ_low −; ST_GAS committed +, econ_low +; CC_CHP committed −; CT_CHP
  committed −. CAISO has no coal fleet to speak of (COAL 0.39 TWh model, ~0
  benchmark) — **COAL_* knobs skipped**. All pairs classify pure
  (scenario-config-identical, clean `src/ inputs/ data/` git diffs, single
  Δknob each); REGISTRY entries added to `derive_offer_curve_jacobian.py`.
  Solver note: each 8760 h commitment solve peaks ~8 GB — run probes
  sequentially on a 15 GB box (a 2-parallel attempt was OOM-killed).

### Raw panel (ΔTWh vs probe base, 2023; Δavg-price $/MWh)

| probe (Δmult) | CC_REG | CC_CHP | CT_CHP | CT_PK | ST_GAS | **import** | Δprice |
|---|---|---|---|---|---|---|---|
| CC.committed −0.05 | **+0.84** | −0.15 | −0.23 | 0.00 | −0.12 | **−0.28** | −1.21 |
| CC.econ_low −0.05 | **+0.59** | −0.05 | −0.13 | 0.00 | −0.11 | **−0.30** | −0.69 |
| CC.econ_high −0.05 | **+0.50** | −0.04 | −0.10 | 0.00 | −0.13 | **−0.25** | −0.55 |
| CC.peak −0.05 | −0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CT_PK.committed −0.05 | 0.00 | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 |
| CT_PK.econ_low −0.05 | −0.00 | −0.00 | −0.00 | +0.01 | −0.00 | −0.00 | −0.03 |
| ST_GAS.committed +0.05 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 |
| ST_GAS.econ_low +0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CC_CHP.committed −0.05 | −0.15 | **+0.22** | −0.02 | 0.00 | −0.01 | −0.03 | −0.18 |
| CT_CHP.committed −0.05 | −0.20 | −0.03 | **+0.29** | −0.00 | −0.01 | −0.04 | −0.13 |
| CC.committed +0.05 (held out) | **−0.83** | +0.13 | +0.22 | 0.00 | +0.11 | **+0.29** | +1.07 |

Two structure-level reads, before any regression:

1. **The import node is the counterparty to every live knob.** 30–50% of the
   energy a CC_REGULAR band move shifts comes out of (or goes back into) the
   import node, not other gas classes. The Jacobian's class-TWh matrix can't
   show this (import is not a tuned class); it shows up as own-knob
   sensitivities being ~40% larger than the sum of cross-class gains.
2. **Most non-CC knobs are dead.** CT_PEAKER (0 TWh dispatched at base vs 4.15
   TWh EIA-923), CC_REGULAR.peak (34 MWh moved — i.e. nothing), and both
   ST_GAS knobs (+0.05 moved nothing because ST_GAS's 1.7 TWh sits in hours
   where the next import tranche, not ST_GAS, is marginal). The merit-order
   adjacency check confirms the bands overlap the clearing-price mass
   (78–89% for CT_PEAKER/ST_GAS bands) — the knobs are *price-relevant on
   paper* but the 11.4 GW import stack absorbs the substitution.

### Jacobian (twh block, 2023, TWh per unit multiplier; med = |coef| > 2·jackknife-SE would be high, n_obs caps at 2 for single-knob chains)

| knob | own-class | strongest cross | confidence |
|---|---|---|---|
| CC_REGULAR.committed | **−14.7** | CT_CHP +4.1, CC_CHP +2.8, ST_GAS +1.9 | med |
| CC_REGULAR.econ_low | **−9.0** | CT_CHP +2.1, ST_GAS +1.7, CC_CHP +0.7 | med |
| CC_REGULAR.econ_high | **−7.3** | ST_GAS +2.0, CT_CHP +1.5, CC_CHP +0.6 | med |
| CT_CHP.committed | −4.4 | CC_REGULAR +2.9 | low (n=1 after hold-out) |
| CC_CHP.committed | −3.6 | CC_REGULAR +2.2 | med/low |
| CC_REGULAR.peak | (+1.9) | — | **low — measured ≈0, coefficient is ridge noise** |
| CT_PEAKER.committed / econ_low | ≈0 / −0.09 | — | dead knobs |
| ST_GAS.committed / econ_low | +0.24 / +0.21 | — | low; dead knobs |

Shape block: only `gas` NRMSE is meaningful for CAISO —
CC_REGULAR.committed d(NRMSE)/d(mult) +0.157 (med), i.e. lowering CC committed
*improves* the EIA-930 gas shape slightly while it adds gas TWh. The `coal`
NRMSE rows are junk (EIA-930 CAISO coal ≈ 0.01 TWh ⇒ near-zero NRMSE
denominator; baseline "coal NRMSE" 28.8) — they inflate the shape-block scale
and thereby mute the block in the recipe weighting; verified the recipe is
**identical with `--w-shape 0`**, so no harm this pass, but a CAISO shape fit
should filter the coal series. **LMP block: empty** — `actual_lmp.json`'s
CAISO block covers 2024/2025 only (no 2023 `rt_mon`), so price-level
sensitivities are unscored at the panel year; the per-probe Δavg-price column
above is the available evidence (CC committed: ∓$1.1–1.2/MWh per ±0.05).

### Back-test (held-out pair)

`--exclude-pair caiso_probe_cc_regular_committed_plus --backtest
caiso_probe_base caiso_probe_cc_regular_committed_plus`: prediction-error RMS
**0.039 TWh** against an actual-change RMS 0.357 (CC_REGULAR pred −0.74 vs
actual −0.83; CT_CHP +0.20 vs +0.22; CC_CHP +0.14 vs +0.13; ST_GAS +0.10 vs
+0.11). The ±0.05 neighbourhood is linear and near-symmetric
(+0.842/−0.829 TWh for ∓0.05 committed). The trust region correctly flags the
+0.05 endpoint as outside the minus-side-only sampled range.

### Joint-move recipe — reported, NOT applied

`--cap 0.05` (so every step stays inside the sampled trust region):
**CC_REGULAR committed/econ_low/econ_high −0.05 each, ST_GAS econ_low +0.05**;
predicted CC_REGULAR error **−21.05 → −19.47 TWh** (twh-block RMS 9.125 →
8.550), gas shape NRMSE −0.01, CHP classes degrade slightly (CC_CHP −6.24 →
−6.44 grid-only). At the default ±0.15 cap every knob trust-region-freezes at
the ±0.05 sampled edge — the correct conservative answer.

### What the Jacobian CANNOT fix (the structural caveat, quantified)

The maximal in-trust-region joint move buys back **1.6 of the 21.0 TWh**
CC_REGULAR deficit. The deficit is not a band problem: it is the
import-displacement gap (CAISO 2 gap #2 — the mis-priced WECC tranches
over-import ~+33 TWh/2023 and displace gas one-for-one). Pushing bands harder
would (a) extrapolate outside every sampled range, (b) claw energy mostly out
of the import node — i.e. *paper over the import gap with offer-curve error*,
the exact compensating-error failure the playbook §6 discipline exists to
prevent — and (c) still leave CT_PEAKER at zero, since no ±0.05 band move
revives a class the import stack has fully crowded out. Likewise the price
level (2023 biased high, zero negative hours) belongs to the import node:
$0.5–1.2/MWh per capped band move is an order of magnitude short of the gap,
and the missing midday negative-price regime is an export-sink/tranche-price
feature, not an offer-band one. **Owner: P9/P12 import-tranche re-pricing.
After it lands, re-run this exact panel off a fresh code baseline and diff the
two Jacobians** — CT_PEAKER/ST_GAS/peak knobs waking up and the CC→import
coupling shrinking is the merit-order-level acceptance check that the re-price
worked.

### Scope & artifacts

Sensitivity-mapping pass: **no calibration keeper committed; keeper configs,
`config/`, `src/` dispatch math untouched; ERCOT/PJM/NYISO/NEISO untouched**
(Jacobian CSV is additive — 80 new CAISO cells, other ISOs' rows byte-equal;
ERCOT/PJM fits not re-run). Dashboard: `caiso 3 probe-base`, `3a`
(strongest live knob), `3k` (held-out back-test) registered; the 9 dominated
single-knob entries were registered then pruned per the 5-run retention
(`caiso 1`/`caiso 2` retained; all 12 bundles kept under
`results/calibration/caiso_probe_*`). Jacobian:
`inputs/processed/offer_curve_jacobian.csv` (iso=CAISO, year=2023) +
REGISTRY/ISO_STATES entries in `scripts/derive_offer_curve_jacobian.py`.

## ERCOT Runs 98a/98b — the committed-band inversion, the split verdict, and the published ORDC μ/σ (2026-06-13)

**Trigger: the 2024 gas-vs-coal split (−8.5%, ~−4.9 TWh of coal) declared
unacceptable; campaign to find its mechanism and fix it. Outcome: the
mechanism is found and PROVEN (run 98a passes the 2024 split), but every
honest implementation is measured or sized to fail 2023 — the split fail
is the quantified footprint of loss-making coal self-commitment the
energy-only merit order cannot produce. Run 97a remains the keeper.
Separately: the user fetched NP6-576-ER, closing the ORDC overlay's one
unverified parameter.**

### The mechanism (corrects the run-97b reading)

Tranche-bid forensics on the run-96 bundle: Parish's committed tranche
cleared only at LMP ≥ ~$20 while its econ slices cleared from ~$13
(committed-band utilization 18% vs econ 47%). Cause: COAL bins carry a
$100/MW startup cost and ONLY the `_committed` tranche has min-run params,
so `compute_monthly_markup` (P1 bid-cost) amortizes the cold start onto
the committed band alone — pricing the design's cheap base band ABOVE the
econ ramp top. The run-97b "backfire" was capacity moving into the
startup-bearing band (NOT the commitment screen — P2 was off; the
docstring "coal gets no startup markup" describes only the legacy path).
Also ruled out en route: Parish's fuel price is already the measured
PRB-reporter monthly average (Fayette + Spruce F923) — not a price-input
problem.

### Runs 98a/98b — warm-boiler exemption (REJECTED, the decisive pair)

New flag `--coal-warm-committed` (ScenarioConfig `coal_warm_committed`,
default off): a coal bin with a must-run floor never goes fully dark — its
mustrun tranche holds the boiler online — so committed-band dispatch is a
hot-unit ramp, not a cold start; exempt it from the P1 markup. Run 98a =
run-97a config + flag; run 98b = 98a + Parish/Spruce committed 20 → 30
(parallel probes, worktree-isolated bins). Measured: **the 2024 story is
fully explained — coal split −8.5 → −2.2% PASSES, PRB 2024 −9.0 → −0.3%
(Parish +3.8 TWh)** — and **2023 detonates: PRB +8.8%, coal split +7.8%,
gas −3.1%, guards 1603/1215**, plus committed coal steals ST_GAS 2024
(−2.98) and CT 2024 (−3.02) and re-flips lignite 2024 (−1.14): 5 fails,
worse distribution. The exempted band (~$16/MWh) clears in BOTH years —
no year-asymmetry. 98b ≡ 98a within noise (the share lever is redundant
once the band clears). Both registered as rejected probes.

### The split verdict (measured/sized lever ledger)

To pass, 2024 needs ~+3.4 TWh of coal with ≤ +0.25 TWh of net 2023 coal
headroom. Levers now measured or sized against that: CC econ_high β and
CC committed δ (split budget 2.7β + 1.7δ ≤ ~0.3, runs 93/95b); lignite
floor (at its measured endpoint, run 95); PRB sigmoid retune (run-90
year-gradient, 2023 detonates); coal committed share (runs 97b/98b);
fleet-wide warm exemption (run 98a); Parish fuel price (already measured);
**monthly CAMPD p10 must-run floors (sized from data, not run: net
+1.04/+2.15/+1.32 TWh by year → split −8.5 → ~−4.8%, still failing, while
2023 lands on its cap; closing fully needs p25+ floors — openly flooring
the calibration target)**. Conclusion: the residual 2024 coal deficit is
owner self-commitment in a loss-making year (Parish ~3.7 of the ~4.9,
lignite ~1.0) — economically irrational dispatch the LP cannot produce
endogenously. Honest paths forward are a user-sanctioned methodology
change: (a) the monthly-floor overlay at p10 (closes ~40%, same family as
the accepted annual CAMPD floors and the outage overlay), or (b)
re-benchmark the 2024 split with the IMM-documented self-commitment wedge
out of scope (a gate redefinition). Neither taken unilaterally.

### NP6-576-ER — the ORDC μ/σ table (RESOLVED)

User-fetched postings 2025-06-13 + 2025-09-12 of report 13233 →
`inputs/calibration/ercot_ordc_lolp_params.csv` (season-constant in these
vintages: summer 904/1333, fall 917/1340, winter 930/1351, spring 947/1368
μ/σ MW). Two findings: the published σ validates the a-priori 1,400 MW
floor-anchor bound within 5%; and μ/σ is constant ≈ 0.68 across seasons —
the signature of the PUCT-48551 0.5σ administrative shift being EMBEDDED
in the published Average → use the table with `--shift 0` (the double-
shift reading improves 2023 to 24.3 but degrades 2024 past the ±$1 guard:
7.4 → 8.5). With the table + shift 0 on the keeper: 2023 MAE 32.1 → 27.8,
2024 → 8.0, 2025 → 2.2 (≈ the flat default — σ was never the 2023
residual's driver; the gap attribution in the ORDC entry stands). Both
series committed in the run-97a bundle (`scarcity_np6shift0.parquet`
canonical, `scarcity_np6.parquet` sensitivity); `docs/ordc-overlay.md`
caveat replaced with the resolution + vintage note.

### Bookkeeping

Keeper unchanged: run 97a. Dashboard: 98a/98b registered (rejected probes,
vectors in sidecars), retention prunes run95 + run95b entries (bundles
stay). Jacobian REGISTRY: 97b description corrected, 98a/98b classified
structural. New dead levers (do not re-probe): fleet-wide
`--coal-warm-committed` (2023 floods + guards), coal committed share with
OR without the exemption, monthly p10 floors as a split fix (sized
insufficient). The flag itself stays in the codebase (default off) — it is
the correct mechanism for any future per-plant/overlay treatment.

## ERCOT — CORRECTION: the Parish "self-commitment" attribution was a split-plant diagnostic artifact (2026-06-13)

**A user question ("isn't Parish a coal/gas split? they've been converting
units to gas over time") exposed an error that misdirected runs 97b/98a/98b.
The keeper (run 97a) and all gate scores are unaffected — this corrects an
attribution and fixes a diagnostic, not the calibration.**

**What was wrong.** The runs-97a/98 entries called W A Parish (EIA 3470) a
−3.7 TWh "never-off self-scheduled baseload" and "essentially the whole PRB
2024 fail." That −3.7 came from `_plant_hourly_fit`, which grouped the
model by `plant_code` and compared to CEMS by `plant_id`. Parish is a
**mixed plant**: the registry splits it into a coal bin (3470, 2443 MW SUB)
and a gas-steam bin (synthetic child 34702, 1565 MW NG ST — the user's
iterative coal→gas conversion; EIA-923 confirms NG/ST netgen 1.63 → 2.40 →
2.61 TWh across 2023-25). CEMS reports the **whole physical facility** under
plant_id 3470. So the diagnostic compared the model's *coal-only* bin
(8.42 TWh) against the *coal+gas* CEMS stack (12.16 TWh) and invented a
−3.7 phantom.

**The corrected picture (model bins summed to the CEMS parent vs CEMS
whole-plant):** Parish is **+0.22 / −1.36 / +0.15 TWh** for 2023/24/25 —
dead-on in the normal- and dear-gas years, short only in the single
cheapest-gas year. That is exactly the answer to the user's second
question: the plant is **price-responsive, not price-blind**, and the model
already reproduces it (Parish coal CF rises with gas price; whole-plant is
within ±0.2 TWh in two of three years). Re-benchmarking it as "runs the
same regardless of price" would be wrong.

**Corrected PRB 2024 attribution.** The −3.94 TWh class fail is
**distributed cheap-gas merit displacement across the whole PRB fleet**,
not one plant: Spruce −1.60, Parish coal −1.35, Fayette −0.72, Limestone
−0.53, Martin Lake −0.38, Coleto −0.28, partly offset by Sandy Creek +0.92.
This is the documented run-90 year-gradient (cheap 2024 gas displaces PRB
on bids; no fleet-wide passthrough deepens 2024 without flooding 2023).
Runs 97b/98a/98b were therefore chasing a phantom — trying to push Parish
coal up ~3.7 TWh when it is short only ~1.35, with the "missing" ~2.4 being
the gas-steam bin that is already modelled correctly (in ST_GAS, not
COAL_PRB). The run-98a warm-boiler exemption "passed" the 2024 split only
by force-running coal the merit order correctly idles in a cheap-gas year,
which is precisely why it detonated 2023. Those runs stay REJECTED for the
right reason now.

**Fix shipped.** `_plant_hourly_fit` now folds each synthetic child code
(`parent*10+digit`, per `scripts/tag_mixed_plants.py`) back onto its CEMS
parent before the comparison, so a split plant's model series is its
whole-plant output — matching what CAMPD measures. Verified on the run-97a
bundle (Parish r=0.85, whole-plant miss −1.36 in 2024). The fix only
touches the per-plant diagnostic sidecar in *future* bundles; existing
gate scores use class totals (which always counted 34702 in ST_GAS and the
coal bins in COAL_PRB correctly), so the keeper is unchanged.

**Disposition of the 2024 coal split.** It is the cheap-gas merit residual
— distributed, price-responsive, fleet-wide — carried under the same
philosophy as the existing PRB carve-out. Not floored (the price response
is real and the model captures its direction), not re-benchmarked as
price-blind (the per-plant evidence refutes that framing), and not
reachable by any fleet-wide lever measured this campaign (the 2023/2024
coal co-movement + the 2023 split's ~0.4% headroom block every one). Run
97a remains the keeper.

## ERCOT Runs 103–109 — the CT AS-deployment overlay + ST availability retune (2026-06-13)

**The structural unlock the run-97a entry flagged, built and landed. NEW
KEEPER: run 109a — 3 in-scope fails, beats run 97a's 4, the ST_GAS deficit
fixed across all three years, LMP gate held. Cost (user-sanctioned): the
2024 coal split deepens −8.5% → −9.5% (the CT out-of-merit gas displacing
marginal cheap-gas PRB under fixed demand).**

### The mechanism — CT AS/RUC-deployment overlay (`--ct-deployment`)

The run-97a decomposition measured 31/38/44% of CEMS-covered CT_PEAKER energy
(2023/24/25) running out of merit — hours where the RT price was below the
unit's marginal cost — the IMM-documented ancillary-service / reliability-
unit-commitment deployment + reserve-adequacy wedge (~1.4–2.3 TWh/yr) the
energy-only LP structurally cannot dispatch. `scripts/derive_ct_deployment.py`
measures it directly from CAMPD CEMS: for each CEMS-covered CT plant and each
hour it generated, the hour is a **deployment hour** when `net_mw > 1` AND
`actual RT LMP < plant_avg_heat_rate × gas_price + CT_VOM` (hr-mult 1.0,
matching the documented 31/38/44% — measured 29.9/35.0/42.5%, 1.34/1.88/2.22
TWh). It writes a per-plant **hourly** floor (`inputs/calibration/
ct_deployment_floor_ERCOT.parquet`, only the out-of-merit hours, floored to
the measured net output). `outages.ct_deployment_floor_for_year` +
`fleet.generators_to_fleet_arrays` apply it as a sparse per-hour min-gen bound
(cheapest tranche first, availability-capped) when
`ScenarioConfig.ct_deployment_overlay` is set (ERCOT backcast only). A pure LP
min-gen bound — no MIP, prices stay LP duals. The in-merit hours stay
economic, so CT is NOT floored to its full CEMS output (the over-credit guard
the brief required). Default off; forecast/other ISOs no-op (no artifact;
`min_gen` byte-identical, verified). San Jacinto 7325 excluded (BTM cogen,
avoids double-counting `--btm-backfill-year`). Unlike the CT reliability
must-run floor (`ct_mustrun_per_plant`, which floors the FULL 923 net-gen and
exempts its units from WEFOR/POF), the deployment units KEEP the statistical
availability model — the floor is sparse and well below pmax in its hours, so
exempting them would spuriously boost their high-price economic dispatch.

### Run sequence (all on the run-97a config + the overlay)

- **run 103** (`--ct-deployment` only): 5 fails. Realized net additive effect
  +0.84/+1.41/+1.58 TWh (the LP front-loads CT into high-price hours, so it
  produces only ~0.3 TWh in the out-of-merit hours; the floor is nearly pure
  addition). Fixed CT 2023 (−1.53 → −0.69), lifted CT 2024 (−2.56 → −1.15) /
  2025 (−0.90 → +0.68). But the floored CT displaces other classes in the
  low-price hours: ST_GAS 2025 (−0.73 → −1.11) and lignite 2024 (−0.97 →
  −1.03) newly fail (CC absorbs most — good — but ST/coal take some). 4 → 5
  fails; the Phase-2 setup.
- **runs 104a/104b** (+ ST_GAS,ST_CHP WEFOR relief, residual 0.02 / 0.08):
  ST_GAS 2024/2025 fill, but blanket relief overshoots ST 2023 and re-craters
  CT (the relief re-orders the low-merit stack; the floor protects only the
  out-of-merit hours, not CT's in-merit economic dispatch). The deficits are
  per-year-asymmetric (2023 wants ~0, 2024 +2, 2025 +1) but the relief is
  uniform.
- **runs 105a/105b** (+ ST_GAS committed bid raised −0.385 → −0.25 / −0.15):
  DEAD/backfire. The ST committed band sits on a cliff — a 0.135 bid raise
  craters ST_GAS (2024 −4.16) and the freed energy goes to CC (over), not CT.
  6 fails. ST committed bid cannot shape years.
- **runs 106a/106b** (relief 0.10 / 0.11, lignite floor 0.72): relief 0.11
  threads ST across all three years. Discovered `--lignite-floor` is the
  sigmoid PASSTHROUGH floor (higher = higher bid = LESS lignite in cheap gas),
  so 0.72 made lignite 2024 WORSE — wrong lever direction.
- **runs 107a/107b** (relief 0.11 / 0.125, keeper lignite 0.69): 107a ties
  run 97a at 4 fails with all ST passing; 107b (gentler) underfills ST 2024.
  lignite 2024 = −1.06 at the keeper floor (the CT-displacement, persistent).
  Also FIXED a bundle-write bug: `--wefor-relief-groups` writes a frozenset
  into the meta override record, and `json.dumps(meta)` had no default handler
  → "frozenset is not JSON serializable" aborted meta.json/run_config.json/
  plant_hourly_fit AFTER the parquets wrote (the run-102 "lost meta.json" was
  this, not the container recycle). Fixed with `_json_default` (set/frozenset →
  sorted list) on all three bundle dumps.
- **runs 108a/109a/109b** (lignite-floor thread): 0.66 floods lignite 2023
  (+1.03), 0.69 fails 2024 (−1.06); **0.675 threads both** (2023 +0.92, 2024
  −0.85). 109b tried a CC econ_high bid raise (−0.40 → −0.20) to redirect the
  2024 coal displacement off PRB onto over-built CC — BACKFIRED (CC is as
  cliff-edged as ST committed: −5.8 TWh in every year, 7 fails).

### Run 109a (`run109a_relief11_lig675`) — KEEPER, 3 fails

run 97a config + `--ct-deployment` (frac 1.0) + `--wefor-residual 0.11
--wefor-relief-groups ST_GAS,ST_CHP` + `--lignite-floor 0.675`. **3 in-scope
fails {CT 2023 −1.08, CT 2024 −1.55, PRB 2024 −10.6%/−4.64} vs run 97a's 4
{CT 2023, CT 2024, PRB 2024, ST 2024}.** ST_GAS fixed all years (2023 +5.4%/
+0.91, 2024 −5.1%/−0.93, 2025 +1.7%/+0.26); lignite threaded (2023 +0.92,
2024 −0.85, 2025 +0.29); CC/CHP/PRB-2023/2025 all pass; no passing class
regressed to a fail. **LMP gate held** (energy-only monthly MAE 32.3 / 7.8 /
2.1, all within ±$1 of the 32.1/7.3/2.2 baseline). ORDC overlay re-derived on
the keeper (availability + scarcity + scarcity_np6shift0; 2023 32.3 → 29.3
with the adder). Guards clean (Martin Lake 2025 +1.43 TWh, unchanged).

**The remaining 3 fails are structurally diagnosed:** CT 2023/2024 — the
deployment overlay recovers the CEMS-covered out-of-merit wedge (covered
plants now match CEMS), but the ~1.0–1.2 TWh/yr of bench in **non-CEMS small
peakers** (Ector County, Permian Basin, Pearsall) has no hourly CEMS to key
off and the merit order can't reach it; the ST relief also costs CT ~0.4
TWh/yr. PRB 2024 — the documented run-90 cheap-gas residual, deepened ~0.7
TWh by the CT overlay displacing marginal PRB under fixed demand.

### The cost — 2024 coal split (user sign-off)

The CT overlay adds out-of-merit gas (CT) and the relief adds ST gas; under
fixed demand in the cheap-gas 2024 year, this displaces the marginal
(uneconomic) coal — deepening the documented coal-side residual: 2024 coal
split −8.5% → −9.5%, PRB 2024 −9.0% → −10.6%. The gas split holds (+0.4%).
This is zero-sum (the only true surplus is CC over-run, which has an
unfavorable gas-price year-gradient and a cliff-edged bid). Measured/dead
levers this campaign confirm the split is not recoverable here: ST committed
bid (105), CC econ_high bid (109b), PRB cheapening (run-90), lignite (the
0.675 thread is at its limit). The user accepted the split regression
(2026-06-13) as the cost of fixing the CT + ST volume under-clearing — the
headline 4-fail bar + the LMP gate are the binding gates; the coal split is
carried as the documented residual (same philosophy as the PRB carve-out).

### Bookkeeping

Keeper: run 109a (supersedes run 97a; `calibration-best-so-far.md` updated).
New code (default off, forecast-safe): `ScenarioConfig.ct_deployment_overlay`
+ `ct_deployment_floor_frac`, `scripts/derive_ct_deployment.py`,
`outages.ct_deployment_floor_for_year`, the `fleet.generators_to_fleet_arrays`
min-gen block, the `--ct-deployment` flag, and the `_json_default` bundle-dump
fix. New dead levers (do not re-probe): ST_GAS committed bid raise (cliff,
105), CC econ_high bid raise on the overlay+relief basis (cliff, 109b),
blanket WEFOR relief deeper than ~0.10 (overshoots 2023 / craters CT, 104),
lignite floor outside ~0.675 (2023 flood / 2024 fail, 108). Follow-up (not
this campaign): a non-CEMS small-peaker floor for the ~1.0 TWh CT 2024
residual (Ector/Permian/Pearsall have 923 net-gen but no hourly CEMS — a
923-based floor, distinct from the CEMS out-of-merit overlay).

## NEISO — AGT hub-basis overlay was dead in calibration; wiring it in (2026-06-16, keeper `neiso_agt_3yr`)

Discovered while chasing the winter-tail/oil gap (doc-08 gap #1): the Algonquin
Citygate hub-basis overlay — documented as THE NEISO price driver — was **never
applied in the calibration dispatch.** `run_calibration.run_year` resolves fuel
prices with `apply_monthly=False` and re-applied the plant-monthly and dual-fuel
passes but not `apply_hub_basis_overlay`, so every NEISO keeper (P12/P14,
hydro930) priced gas at the 2-reporter EIA-923 ISO-month series instead of the
measured AGT hub (Jan-2025 gas **$5.30** vs hub **$16.92**/MMBtu). That series
is over-priced in shoulder months and under-priced in winter, so the modeled
load-weighted hub price was wrong in **both** directions vs ISO-NE
.H.INTERNAL_HUB DA: **2023 $53.6→$34.5 (act $36.8); 2024 $55.7→$40.0 (act
$41.5); 2025 $54.3→$68.0 (act $67.9)**, gas TWh to within ±0.8% of EIA-930.
This supersedes the "price level at sign-off" finding — the level was wrong
because the measured AGT data was ignored.

**The keeper** (`neiso_agt_3yr`, one 2023–2025 bundle, dashboard neiso 13) is
the overlay wiring fix on the measured **monthly** AGT basis, hydro 930-pinned
uniformly across years — one config, **no fitted parameter**: gas within −1.3%
of EIA-930, hydro 8.70/7.33/5.11 vs 930 8.77/7.39/5.12, hub $34.4/$39.8/$68.5 vs
act $36.8/$41.5/$67.9. The winter >$200 tail and near-zero oil are accepted as
the honest monthly-granularity limit.

Two further pieces are **off-by-default diagnostics** (opt in with
`--gas-hub-basis-daily`), deliberately NOT in the keeper:
- **Daily AGT basis** (`fuel.iso_hub_daily_gas_prices`): redistributes each
  winter month's measured mean basis across days by
  NEISO demand^`AGT_DAILY_BASIS_CONVEXITY`(=7), mean-preserving. Builds the tail
  a flat plateau can't — 2025 A/B (identical mean): hours >$200 **13→128**. But
  the convexity is **fitted to the backcast** (tuned to the oil/>$200 counts it
  predicts), not measured/forecast-grade, and the daily AGT spot it proxies (U4)
  is paywalled — so chasing the tail this way is overkill for a backcast that
  has the measured answer; left opt-in until U4 lets the convexity be *derived*.
- **Oil re-attribution** (`dual_fuel_switch_mask` → `_dispatch_frame`): relabels
  switched dual-fuel MWh gas→oil (LMP-neutral). With the daily proxy on, oil
  0.06→2.12 (2025) vs 1.24 — order of magnitude but over (no firm-gas/inventory
  limits). NEISO-only gate so PJM/NYISO stay byte-identical.

Tests: 295 pass (zone/transmission/neiso/iso/hydro/fuel). See
`docs/multi-iso/neiso-data-audit.md` §2c–2d, CHANGELOG 2026-06-16.

## Cross-ISO — CT_PEAKER AS-deployment overlay generalized to PJM/CAISO/NYISO/NEISO; the PJM blanket-floor refutation (2026-06-13)

**The ERCOT AS-deployment overlay (runs 97a/103–109, `scripts/derive_ct_deployment.py`
+ `outages.ct_deployment_floor_for_year` + `ScenarioConfig.ct_deployment_overlay`)
is now ISO-parameterized and extended to the four remaining ISOs.** This entry
records (a) the PJM blanket-floor measurement that proves the targeted overlay is
the *only* mechanism that works, and (b) the per-ISO out-of-merit wedges the
generalized derive script measures.

**Why a blanket CT must-run floor is wrong (PJM measurement).** A parallel PJM
session first tried the blanket per-plant CT must-run floor
(`ct_mustrun_per_plant`, force *all* observed CAMPD-shaped CT energy). Measured on
the PJM keeper it moves the CT/CC split correctly — CT_PEAKER −9.60 → −0.10 and
CC_REGULAR +4.30 → +0.67 (the split itself is fixable) — **but it injects ~+5 TWh
net gas** because the forced CT displaces coal + imports, not just CC:

- 2024 gas +16.5 → **+21.4 FAIL** (gate ≈ +17.7); 2024 coal-tot −3.2 → **−6.2 FAIL**
  (knife edge <5.0 breached).
- 2023 / 2025 passed (2025 coal-tot even improved +5.83 → +4.72).

A coal-cheapening retune to *absorb* the displaced gas does **not** converge: BIT
`econ_low` −0.15 fixes 2024 coal but leaves gas **+20.15 FAIL**; −0.30 overshoots
2025 coal-tot to **+8.29 FAIL**. 2024-gas and 2025-coal cannot be reconciled by any
single offer lever — the same diagnosis as ERCOT. **CT is not offer-recoverable**,
so only a *targeted* sub-marginal overlay (floor dispatch to the measured level
**only** in hours where CEMS shows the unit running while RT LMP < its marginal
cost) recovers the AS/RUC/reliability energy without over-crediting to full CEMS
output and without displacing the coal/imports the energy-only LP already prices
correctly. This is the empirical justification for adopting the overlay across all
ISOs in place of the blanket floor.

**Generalization shipped (reuse, not rebuild).**
- `derive_ct_deployment.py` is now `--iso`-driven: it reads `campd.states_for_iso(iso)`
  and `actual_lmp_hourly_<ISO>.parquet` and writes `ct_deployment_floor_<ISO>.parquet`.
  ERCOT keeps its CAMPD-bin heat rates (`custom-bin-assignments.csv`); every other
  ISO sources per-plant CT_PEAKER heat rates from the **same EIA-860 fleet the LP
  dispatches** (`load_fleet_from_csv` + the canonical `classify_plant`, capacity-
  weighted per plant), so "out of merit" is defined consistently with each ISO's CT
  offer.
- `outages.ct_deployment_floor_for_year(year, hours, iso)` and the `fleet.py`
  min-gen wiring are ISO-keyed; the WEFOR/POF-exempt branch and the
  cheapest-tranche-first availability-capped min-gen distribution carry over
  unchanged. The overlay flag stays default-OFF, backcast-only.

**Measured out-of-merit wedges (deploy TWh / share of covered CEMS CT energy;
Henry Hub gas 2.54 / 2.19 / 3.52, `hr-mult` 1.0):**

| ISO   | 2023 | 2024 | 2025 | notes |
|-------|------|------|------|-------|
| ERCOT | 1.34 (30%) | 1.88 (35%) | 2.22 (43%) | unchanged keeper artifact |
| PJM   | 6.68 (37%) | 4.39 (24%) | 6.69 (30%) | 72–73 plants; NC/TN/MI lack CAMPD extracts |
| CAISO | 0.00 ( 0%) | 0.28 ( 8%) | 0.39 (24%) | 2023 LMP file has no rows → no wedge that year (degrades to plain LP) |
| NYISO | 1.87 (50%) | 0.78 (23%) | 1.00 (26%) | 20–21 plants |
| NEISO | 0.08 (19%) | 0.04 ( 9%) | 0.05 (10%) | small CT fleet (8–9 plants) |

The wedge is the *sub-marginal subset* of measured CT energy, not the full CT gap:
the remaining (economic, price ≥ MC) CT shortfall stays with the LP and is
offer-tunable, gas-neutral (CT↔CC). Per-ISO calibration against each registered
keeper follows; runs are logged as MEASURED PROBEs until one beats its incumbent.

## ERCOT — gate basis moved to GRID-DELIVERED (2026-06-14)

**User directive after a run-109a dashboard read exposed a basis mismatch: the
calibration gate added the behind-the-meter CHP host supply back to the model
and compared to whole-plant EIA-923, while the dashboard mix table added only
the CHP-class BTM — so CC_REGULAR/CT_PEAKER looked ~3.5 TWh more under on the
dashboard than at the gate, and the system total read 471 vs 923's 475 (the
omitted CC_REGULAR 2.83 + CT_PEAKER/San Jacinto 0.71 BTM).**

**The fix: gate on grid-delivered accuracy.** The LP holds the BTM host steam
OUT of the grid solve, so crediting the model for it scores generation the
model never optimized. Now everywhere — `scripts/lib/session_score.py`, the
dashboard class/system scorecard + mix table (`render_calibration_html
.build_payload`: `gmModel` grid-only, `classFull` = EIA-923 − per-class
`btm.parquet`) — model = grid LP dispatch, actual = EIA-923 whole-plant minus
the per-class BTM host supply (= grid-delivered generation by class). The
per-plant heatmaps stay whole-plant (CEMS, their comparison series, is itself
whole-plant). The fuel-split gate is grid-vs-grid for all years (923−BTM, with
EIA-930 grid shown as the independent check). The standalone-report add-back in
`build_payload` line ~388 (per-plant model vs CEMS) is unchanged.

**Impact: none on verdicts.** The absolute TWh miss is identical to the old
whole-plant basis (the BTM cancels: (grid+BTM) − 923 = grid − (923−BTM)), so
the ±1 TWh classes are byte-identical and the ±5% classes shift only by their
(smaller) grid-delivered denominators. Re-scored grid-delivered: **run 109a = 3
in-scope fails {CT 2023 −1.08, CT 2024 −1.55, PRB 2024 −10.6%}, run 97a = 4 —
the keeper still beats run 97a.** Dashboard re-rendered (ERCOT bench parts +
the 5 ERCOT run payloads now grid-delivered; non-ERCOT ISOs unchanged — they
carry no `btm.parquet`, so grid-delivered = full 923). LMP/ORDC unaffected
(energy-only LMP is already grid-side). `calibration-best-so-far.md` success
bar + results table updated to the grid-delivered basis.

## ERCOT Runs 110–117 — per-plant CC duct overlay + PRB ease (NEW KEEPER run 115b, 2026-06-14)

**User ask:** lift CC_REGULAR 2023 (run 109a left it −2.3%) with a **per-plant**
CC peak band rather than a class-wide bid move; probe the PRB floor toward an
**evenly distributed** miss (the user "most prefers 0.71 unless we find a
justification for the 2024 anomaly"); adjust the other offer curves (incl. steam
gas) around the result.

**The mechanism — `--cc-duct-peaking`.** Each CC_REGULAR/CC_CHP plant's peaking
tranche % is sized from its **EIA-860 duct-burner flag**: duct-fired plants get
their nameplate-vs-net-summer capability gap as the expensive peak band, non-duct
plants get **0** (no phantom scarcity band on a plant that cannot duct-fire).
`fleet.cc_duct_peaking_pct()` → applied in `generators_to_fleet_arrays`
(`ScenarioConfig.cc_duct_peaking`); supersedes the offer curve's class-wide
`pct_peaking`, band HR multipliers still apply, the hand-set
`CC_REGULAR_PEAKING_PCT_BY_PLANT` map stays final word, plants absent from the
860 sheet keep the class value. Default off (other ISOs/forecast byte-identical).

**The 2024 PRB anomaly is justified (the condition the user set is met).** The
2024 PRB low is **not** a model defect: the LP correctly idles loss-making
self-committed/contracted coal — the plants ran 40–52% CF while $2.19 gas put
them below marginal cost, and there is no outage. So per the user's standing
condition, the justification holds and the floor is left at 0.73 (lumpy-but-
honest) rather than forced even at 0.71.

**The PRB-even vs 2023-coal tradeoff (the run-90 gradient, re-confirmed).**
Cheapening the PRB floor evens the multi-year miss but the evened 2023 PRB *is*
an over-run of the 2023 coal plants:

| PRB floor | run | PRB 2024 / mean | 2023 coal split | guards |
|---|---|---|---|---|
| 0.71 | 116b | −8.1% / −1.7% (most even) | **+3.8% FAIL** | Limestone +1015 breach |
| 0.72 | 114a | −9.2% / −2.5% | **+3.0% FAIL** | clean (+917) |
| **0.73** | **115b (keeper)** | −10.3% / −3.3% | **+2.2% PASS** | clean |
| 0.74 | 109a | −10.6% / −3.7% | +1.6% | clean |

0.73 is the lowest floor that keeps the 2023 coal split passing and the guards
clean — the chosen point given the 2024 anomaly is justified.

**Run sequence (all = run 109a config + `--cc-duct-peaking`, varying PRB floor /
ST relief):**

- **Scorer fix (prereq):** the grid-delivered split gate used 923−BTM for all
  years, but the 2025 EIA-923 is the incomplete monthly vintage; switched 2025 to
  EIA-930 (itself grid-side, the correct 2025 grid-delivered actual). This alone
  cleared a phantom "2025 gas +3.6%" fail (it is +2.2% vs 930).
- **114a** (0.72, relief 0.06): CC 2023 fixed, ST 2024 held, but 2023 coal split
  +3.0% and PRB not evened (relief lifts ST 2024 → displaces PRB back down).
- **115a/115b** (0.73, relief 0.07/0.06): **115b is the keeper.** 3 in-scope
  fails {CT 2023 −1.61, CT 2024 −2.10, PRB 2024 −10.3%}. CC_REGULAR 2023
  −2.3%→−0.8% **fixed**; CC_CHP +7/+7/+10%→+0.6/+0.8/+3.8% **re-centered** (duct
  strips the phantom band off non-duct CHP); 2023 coal split +2.2% PASS; ST all
  pass (2024 −4.2%/−0.76); LMP 32.5/8.1/2.2 holds.
- **116a/116b** (0.71, relief 0.06/0.05): PRB most even (mean −1.7%) — confirms
  the coupling fix (at a cheap floor the ST relief displaces over-built CC, not
  PRB) — but 2023 coal split +3.8% + Limestone guard +1015. Rejected per the
  justified-anomaly call.
- **117a/117b** (0.73, relief 0.085/0.10): **negative probe** — eased the relief
  to try to spare CT; it does NOT. CT 2024 barely moves (−2.10 → −2.00/−1.94)
  while ST 2024 craters to a fail (−1.11/−1.31). Proves the **CT deepening is
  cc-duct-intrinsic** (CC displacing CT in merit order), not relief-driven, and
  that 0.06 is the correct relief.

**The cost (user sign-off).** CT_PEAKER deepens vs run 109a (2023/2024 −0.53/
−0.55 → −1.61/−2.10) — the cc-duct CC lift displaces CT, measured intrinsic and
not relief-reachable. Accepted as the price of fixing the ±20-TWh CC class and
grounding the CC peak band in EIA-860 rather than hand-set values. The single
"never regress vs keeper" exception, signed off 2026-06-14.

**Bookkeeping.** ORDC scarcity overlay re-derived on run 115b (availability +
scarcity flat-1400/shift-0.5 + scarcity_np6shift0 NP6-576-ER canonical;
post-solve additive, dispatch untouched; 2023 LMP MAE 32.5→30.1 with the adder).
`calibration-best-so-far.md` STATUS/keeper/config/success-bar updated; dashboard
re-registered (run 115b keeper, run 109a demoted to predecessor).

## NEISO — Merrimack reclassified COAL_BIT + CC_REGULAR offer-curve Jacobian re-derived on the AGT-wired structure (2026-06-17, keeper `neiso_cc_coalbit_3yr`, "neiso 14")

Two pieces of work on the corrected (AGT-overlay-wired, `neiso_agt_3yr`/neiso 13)
structure: (1) the lone NEISO coal unit is now classified by its measured rank,
and (2) the CC_REGULAR offer-curve sensitivity panel was re-seeded with fresh
±0.05 probes — the prior Jacobian was derived when the AGT overlay was dead code
and is stale.

### 1. Merrimack (ORIS 2364) — bituminous, COAL_BIT (data-driven, no fitted value)

`scripts/derive_coal_supply.py --iso NEISO` sums Merrimack's EIA-923 Schedule-5
fuel receipts (54,050 tons 2023-2025) → **100 % bituminous** →
`inputs/processed/coal_supply_NEISO.csv` (`2364,bituminous,receipts`).
`fleet.coal_supply_class(2364)` now returns `bituminous`, so the dispatch class,
offer curve, and delivered-cost path all resolve to **`COAL_BIT`** instead of the
generic unclassified `COAL` fallback the plant carried before. EIA-860 confirms
the retirement/availability window: unit 1 (108 MW net summer, `BIT`, status
`OP`, planned retire 2027) operates across the whole backcast window; unit 2
(330 MW, `BIT`, status `OS`) is out of service. So coal is **not zero** — the
~108 MW unit 1 produces the EIA-930 ISNE coal column (0.18/0.24/0.28 TWh) as a
low-CF winter-peaking run.

Effect on dispatch: **none.** `COAL_BIT` and the generic `COAL` offer curve are
byte-identical (committed 0.90 / econ_low 0.95 / econ_high 1.10 / peak 1.45 /
econ_low_share 0.55) and `COAL_PRICE_BASE["NEISO"]` (3.0, the bituminous-by-rail
blend) is already the delivered cost, so `neiso_cc_coalbit_3yr` reproduces
`neiso_agt_3yr` to the TWh — gas 54.78/58.89/60.14 (vs 930 55.47/59.64/60.09,
−1.2 / −1.3 / +0.1 %), load-weighted price 34.92/40.22/70.54, coal
0.0145/0.00/0.237 — with coal now labelled COAL_BIT in the scorecard so it scores
against the bituminous benchmark instead of a generic split.

### 2. CC_REGULAR Jacobian, re-seeded on `neiso_agt_3yr` (2024, P2, ΔTWh vs base)

The stale panel (branch `claude/neiso-backcast-jacobian-ziz6pj`, SHA `3c9e5fd`,
pre-AGT-wiring) anchored at CC_REGULAR 55.31 / CT_PEAKER 0.336 — different from
the wired keeper (CC_REGULAR 56.56 / CT_PEAKER 0.014), confirming it could not be
trusted. Fresh single-knob ±0.05 probes (`results/calibration/neiso_probe_v2_*`,
base reproduces the keeper exactly):

| knob (±0.05 on CC_REGULAR unless noted) | ΔCC_REGULAR | ΔCC_CHP | ΔCT_PEAKER | ΔST_GAS | Δoil |
|---|---|---|---|---|---|
| econ_high +0.05 (1.27→1.32) | −0.061 | +0.016 | 0 | 0 | 0 |
| econ_high −0.05 (1.27→1.22) | +0.070 | −0.023 | 0 | 0 | 0 |
| econ_low  +0.05 (1.06→1.11) | −0.048 | +0.016 | 0 | 0 | 0 |
| committed +0.05 (0.92→0.97) | −0.012 | +0.004 | 0 | 0 | 0 |
| ST_GAS committed −0.05 | 0 | 0 | 0 | 0 | 0 |

**Live CC_REGULAR bands, by |ΔCC|/0.05: econ_high (~1.3/unit) > econ_low (~1.0)
> committed (~0.24).** But every live band redistributes energy **only within the
CC family (CC_REGULAR ↔ CC_CHP) and to the measured import schedule** — **none
reaches CT_PEAKER, ST_GAS, or oil**, all of which stay at 0. ST_GAS is dead even
to its own committed knob.

**Why (structural merit order).** Class base heat rates: CC ≈ 7.0, CT/ST ≈ 10.4
(Merrimack COAL_BIT 11.34). CC_REGULAR's economic ramp folds the duct-fire peak
into its top (`_CURVE_FOLD_PEAK`), spanning econ_low → peak = 2.25, i.e. up to
2.25 × 7.0 ≈ 15.8 effective HR. CT_PEAKER's *cheapest* tranche (committed
1.55 × 10.4 ≈ 16.1 effective HR) sits **above** the entire CC_REGULAR curve, so
when CC backs down the next-cheapest increment is always CC_CHP (committed
0.92 × 7.2) or an HQ/NYISO import — never a CT peaker. This matches EIA-923's
prime-mover split (gas_cc is ~95 % of NEISO gas) and the cross-ISO finding that
**"CT is not offer-recoverable"** (a blanket CT floor injects ~+5 TWh net gas
displacing coal/imports; only the targeted sub-marginal AS-deployment overlay
recovers reserve energy, NEISO wedge ≈ 0.05 TWh on its 8-9-plant CT fleet).

**Decision: hold the CC_REGULAR offer curve at the keeper values** (committed
0.92 / econ_low 1.06 / econ_high 1.27 / peak 2.25 / econ_low_share 0.50 /
pct_peaking 8.0), one constant set across 2023/2024/2025. No Jacobian-supported
move shifts the CT_PEAKER/ST_GAS/oil mix, and any change tuned to the residual
would move the (already-correct) gas total or price level for nothing — exactly
the "no magic numbers / merit order first" discipline. The "CC_REGULAR too cheap"
symptom is **correct behaviour**: CC genuinely is the cheapest gas and should
serve essentially the whole gas merit order; the CT_PEAKER (~2 TWh EIA-923) and
ST_GAS (~0.3) shortfall is reserve / AS / reliability / load-pocket deployment
the aggregated 4-zone energy-only LP does not reproduce, recoverable only via the
off-by-default `ct_deployment` overlay, **not** the offer curve.

**Keeper = `neiso_cc_coalbit_3yr` (neiso 14)**: `neiso_agt_3yr` structure (no
offer-curve change) + the Merrimack COAL_BIT reclassification. Tests: 297 pass
(fuel/neiso/iso/hydro/zone/transmission). Regression guard: the only change is
the additive `coal_supply_NEISO.csv` (national plant code 2364, no ERCOT/PJM/CAISO
collision) and no offer-curve code edit, so ERCOT/PJM/CAISO stay byte-identical.

## NEISO — CT_PEAKER reserve recovered: ct_deployment overlay now survives the P2 commitment screen (2026-06-17, NEW KEEPER `neiso_ctdeploy_3yr`, "neiso 16")

Follow-on to neiso 14. The re-derived Jacobian proved the CC_REGULAR offer curve
cannot move energy to CT_PEAKER/ST_GAS/oil, and the cross-ISO work proved a
*blanket* CT floor injects net gas. The one sanctioned lever for the CT gap is
the **targeted `ct_deployment` overlay** (floors CT to its measured output only
in the sub-marginal hours CEMS shows it running while RT LMP < its MC). Deriving
it for NEISO (`scripts/derive_ct_deployment.py --iso NEISO` →
`inputs/calibration/ct_deployment_floor_NEISO.parquet`) measures the wedge at
**0.08 / 0.04 / 0.05 TWh** (2023/24/25) — small, as expected for NEISO's 8-9-plant
CT fleet.

**The bug: a reserve floor was being decommitted by the economic screen.** With
`--ct-deployment` the overlay floored CT correctly in **P1** (CT 0.014 → 0.052
TWh, 2024) but **P2 stripped it back to 0.014**. Root cause:
`commitment.apply_commitment_with_coal_pin` reconstructs the P2 `FleetArrays`
**without `min_gen`** — so every hard floor (the deployment reserve floor *and*
the CHP steam-following floor) was silently dropped in P2, and the commitment
screen then decommitted the now-floorless CT peakers as uneconomic. A reserve /
AS-deployment floor represents energy that ran for *reliability*, not economics,
so the *economic* commitment screen must not shut it off.

**Fix (gated, regression-proof).** `apply_commitment_with_coal_pin` gains
`preserve_min_gen` (default **False** = byte-identical to before): when True it
carries `min_gen` into the P2 fleet and raises each floored generator-hour's
availability to cover it (the LP binds `min_gen ≤ P ≤ pmax·availability`, so a
decommitted `availability=0` would otherwise make the floor infeasible).
`run_calibration._commitment_pass` passes `preserve_min_gen=True` **only when a
deployment overlay is active** (`ct_deployment_overlay` /
`reliability_deployment_overlay`, both default-off). So the forecast runner and
every keeper that does not opt into a deployment overlay — ERCOT, PJM, CAISO,
NYISO, and NEISO neiso 14 — take the exact prior code path. **Verified
empirically:** NEISO base 2024 re-run on the fixed code with the overlay off is
**byte-identical** (P1 and P2, max |ΔTWh| = 0.00000000) to the pre-fix base.
Tests: 361 pass (incl. test_commitment / test_campd_bins / test_tranche_hr).

**Result (3-year keeper, `--ct-deployment`):**

| year | CT_PEAKER 14→16 | gas total (vs EIA-930) | price 16 (vs 14) | coal |
|------|-----------------|------------------------|------------------|------|
| 2023 | 0.014 → **0.084** | 54.78 (−1.2%) | 34.89 (was 34.92) | 0.015 |
| 2024 | 0.014 → **0.052** | 58.89 (−1.3%) | 40.19 (was 40.22) | 0.000 |
| 2025 | 0.038 → **0.079** | 60.14 (+0.1%) | 70.49 (was 70.54) | 0.237 |

CT_PEAKER recovers the measured reserve wedge (2-6× the pre-overlay level) while
the **gas total and price level stay at sign-off** — the CT energy displaces CC
*within* the gas family (gas-neutral, +0.002 TWh), not coal/imports, which is the
whole point of the *targeted* overlay versus the refuted blanket floor. CHP
must-run floors (CT_CHP/ST_CHP) also now correctly survive P2 (a small +0.06/+0.01
TWh, gas-neutral) since they are contractual must-run. The residual CT (~2 TWh
EIA-923) / ST_GAS (~0.3) / oil (~0.3-1.2) gap is the documented
non-offer-recoverable reserve / winter-monthly-data limit — not chased here.

**Keeper = `neiso_ctdeploy_3yr` (neiso 16)**, superseding neiso 14 as the NEISO
keeper (neiso 14 stays the offer-curve-only predecessor). Regression guard:
ERCOT/PJM/CAISO byte-identical (the `preserve_min_gen` gate is off for them;
the coal CSV is additive); only NEISO `bench` + the new code path move.

## NEISO — CC steam-turbine outage derate integrated; backcast-calibration re-confirmed (2026-06-19, keeper `neiso_ccsteam_keeper_3yr`)

Re-ran the `neiso_monthly_keeper` (neiso 21) config on current main to fold in
the combined-cycle steam-turbine unit-outage coupling (`eia_*_cc` capacity rows
in `campd-unit-outages-NEISO.csv`, derivation-script level, no magic numbers; the
fitted daily-AGT convexity stays rejected). Command identical to the keeper:
`--commitment --ct-deployment --hydro-backfill-year 2024 --hydro-eia930-monthly`,
2023–2025, 8760 h.

**The derate is a near-no-op for NEISO.** Controlled A/B on 2025 (only the outage
CSV swapped): CC_REGULAR −0.02 TWh, gas −0.06 TWh, LW price +$0.9. NEISO's CC
fleet has the headroom to absorb it; adopt for cross-ISO consistency, but it
neither fixes nor harms the calibration. CC_REGULAR (52.30/56.51/57.76)
reproduces the keeper (52.31/56.48/57.75) within ±0.03 TWh.

**Surfaced and fixed a poisoned gas-basis cell** (NOT the derate): the 15:46
`fetch-eia-gas-prices` refresh (postdates the keeper) wrote a +$13.46/MMBtu AGT
basis for **Aug-2025** from the EIA MA citygate proxy — a winter-level blowout in
a low-load summer month (LDC citygate fixed-cost recovery, not the marginal AGT
spot). It drove modeled Aug-2025 LMP to $167 vs the actual $45.6 DA. Fixed in
`aa62655` (Jul/Sep interpolation +0.04; preserve-existing keeps it across
re-fetch). With it fixed, 2025 LW returns to $71.2 (vs actual DA $67.9, +4.9%)
and the monthly DA shape tracks actual within a few $/MWh every month.

**Verdict: NEISO is backcast-calibrated** (gas within ~1% EIA-930 all years;
price level/shape on target; nuclear/hydro/interchange near-exact). No further
structural dispatch refinement or magic numbers needed for the backcast. Before a
**forecast** run it needs the neighbor-convexity priced-import node (the seam is a
fixed measured schedule today; a forecast has none) and, when U4 daily-AGT lands,
the *derived* winter-oil convexity. Full writeup:
`results/calibration/DIAGNOSIS-neiso-ccsteam-2026-06-19.md`.

## 2026-07-03 — NYISO 40/41: measured-neighbor import pricing + gas-data fidelity (keeper → nyiso 41)

Session goal: recover NYISO's CALIBRATED-WITH-CAVEATS after the 2026-07-02
rubric re-balance (soft caveat budget 3 → 2) by converting ≥1 of the three
ledgered price caveats into a PASS via real structure. Monthly decomposition
located the misses in the scarcity months (Dec-2024 −48%, Feb-2025 −28%,
Jun/Jul-2025 −29/−26%, Jul-2024 −32%) and the diagnosis split three ways:

1. **Static fitted import ladder** — `IMPORT_TRANCHES_BY_YEAR` capped the seam
   at its per-year constants (model Dec-2024 mean $35.3 ≈ the $35.4 PJM_west
   tranche while measured NEISO averaged $84.5). Built
   `nyiso_import_hub_prices` (`inject_nyiso_import_hub_prices`): PJM_west /
   ISONE_tie at the measured hourly PJM / ISO-NE DA system LMP ± $1 hurdle,
   scarcity block at the hourly max, export sink at the hourly min (wash-free).
   The NYISO analogue of `miso_pjm_lmp_import_pricing` / `caiso_import_hub_prices`.
2. **Gas-data fidelity** — daily hub quotes were spread evenly over calendar
   days (Jan-2024's $23.90 print landed on the 12th, not the 16th) and the
   monthly file's Dec-2024 level ($2.45) disagreed with its own daily series
   ($3.30, holiday-week under-sampling). Fixed: `_transco_z6_daily_dated`
   true-date placement + `fetch_nyiso_gas_narrative.py` (open-egress workflow)
   recomputing the NYISO monthly levels from the completed daily series
   (Dec-2024 basis +0.16 → +1.00).
3. **Eastern-NY (Iroquois Z2) winter hub level — DATA-BLOCKED, now verified.**
   The workflow scanned all 146 NGWU weekly pages 2023–25 (compact table,
   `ngpf.asp` printer table, narrative): zero Iroquois prints; NGI/ICE
   paywalled. The reconstruction reads ~$4.0/MMBtu for Dec-2024 vs the ~$9 NE
   complex — worth ≈ −$25/−$19/−$24 of Dec-24/Jan-25/Feb-25 monthly LMP, the
   bulk of the residual C3 miss. Open data ask: licensed Iroquois Z2 series or
   NYISO SOM monthly per-hub data.

Runs (both registered): `nyiso 40 truedate gas` (control, data fixes only) —
C3a 2024 −19.2 → −16.3%; `nyiso 41 hub prices` (data fixes + the seam
mechanism, **new keeper**) — C3a −13.3/−13.4/−9.5%, C3b NRMSE
0.209/0.236/0.172, C3c 7h in 2025 (first NYISO model >$300 hours). C1/C2/C4/C6
PASS unchanged; C5a CO2 2024 slips to −7.1% (±7 band), exposed by the corrected
gas data with root cause in the ledgered steam under-run. Determination
**NOT-YET** (4 ledgered soft caveats > budget 2): the goal criterion-conversion
is blocked on the Iroquois data ask (C3a/C3b) and the reserve-scarcity frontier
(C3c) — both documented in the run-41 attestation, neither closable with
grounded inputs today (rules #11/#12). nyiso-25-scarcity-merit and
nyiso-30-fwd-band pruned to hold the top-15 retention.

## 2026-07-03 (later) — NYISO 42: reconciled Iroquois winter spread (registered probe, keeper stays 41)

`nyiso 42 iroquois spread` = the nyiso-41 keeper config +
`--nyiso-iroquois-winter-spread` (rule-#13 reconciliation: the measured SOM
ANNUAL Iroquois−Transco spread preserved exactly, re-allocated across months by
the measured Algonquin monthly basis; zonal monthly hub ratios, NYC resolving
to its own measured Transco Z6 NY monthly). **Winter physics validate**
(Dec-2024 residual −$25 → −$10, Feb-2023 −$14 → +$4, Jan/Feb-2025 −$12/−$14;
C3b 2024 0.236 → 0.190) but the probe **exposes the two compensations the flat
spread was providing**: the eastern zones were over-priced ~$1.3/MMBtu in every
unconstrained month (removing it deepens the shoulder undershoot, 2023 C3a
−13.3 → −15.8%) and the dearer winters suppress 2025 in-state gas through the
HARD C2 band (−2.5% → FAIL), so the run is NOT promoted. Mechanism kept in
source (default-off); next root causes now cleanly isolated: the shoulder
reserve/uplift frontier, the C2-2025 gas-volume interaction, and the
Dec-2025/Jan-2024 winter overshoots of the AGT-weight allocation.

---

## NEISO — fast-start tranche pricing + CC econ-band re-anchor: NEW KEEPER `neiso47_faststart` ("neiso 47"), FIRST CALIBRATED-WITH-CAVEATS DETERMINATION (2026-07-03/04)

Goal (session brief): clear the last two blockers under the 2026-07-02
re-balanced rubric — the C3b 2024 price-shape FAIL (NRMSE 0.160 vs 0.15) and
the 3/2 soft-caveat budget overflow (price_tail + storage + storage_shape).

### The month/hour-level diagnosis (named BEFORE any offer change)

Decomposing the 2024 monthly vector (pMon vs rt_mon) on a fresh base re-solve
(`neiso44_base`, keeper recipe on current main): 82% of the squared error sits
in two opposing pairs — **Jan/Feb +$9.5/+$9.8** and **Jul/Aug −$11.1/−$10.4**
(2023 shows the same signature). Hour-of-day attribution: the Feb over-shoot is
**flat across all hours (+9 at 3am, +11 at noon)** — a winter marginal-cost
LEVEL error (model marginal implied HR ~10.5 vs the actual mild-winter margin
~8.2, amplified by $3.5–7.7/MMBtu hub gas); the Jul under-shoot is
**afternoon/evening-concentrated (eve −$27.8)** and fully **DA-visible** (Jul-24
evening DA $62.9 ≈ RT $61.1), i.e. real offer behaviour, not an RT transient.
One root cause covers both signs: the above-SRMC offer component was
parameterized as a **heat-rate multiplier** (fuel-price-proportional), while the
real component (fast-start start/no-load amortization) is **fuel-price-
invariant** — over-pricing expensive-gas winters and under-pricing cheap-gas
summer evenings simultaneously. Quantity check: model July-evening gas dispatch
is within ~5% of EIA-930 while the price is 2× off — an offer-side defect, not
a volume defect.

### The probe chain (all registered on the dashboard)

- `neiso 44 base-control`: keeper recipe re-solve; 2024 C3b 0.160 (FAIL).
- `neiso 45 flat-econ`: CC_REGULAR econ band 1.06→1.27 flattened to
  0.95→1.05 alone; 2024 C3b 0.132 but **C3a 2023 −6.2% (FAIL)** — the winter
  over-shoot had been netting a broad under-shoot; the two moves are coupled.
- `neiso 46 fast-start` (v1): NREL start-cost amortization on ALL gas
  tranches; C3a recovers (+1.0/+1.7/+2.5%) but the CC-econ markup re-inflates
  the mild-winter bulk (~$4 the actual does not show) — 2024 C3b 0.1518,
  0.0018 over. Physically wrong piece identified: **block-loading a committed
  CC is not a fast start; its start costs settle as NCPC uplift, not LMP.**
- `neiso 47 fast-start-v2` (**KEEPER**): markup scoped to ISO-NE
  fast-start-eligible tranches (CT_PEAKER/CT_CHP econ+peak; CC duct/
  quick-response peak band; CC econ excluded) + econ band level 1.00→1.15,
  derived from the directly-observable winter marginal implied HR (~8.2 on the
  model's marginal winter plant Salem Harbor, base 7.38 → mid-band ~1.08).

### Keeper result (payload basis, all three years)

C3b **0.130 / 0.143 / 0.054** (2024 fixed, all ≤0.15); C3a **−4.6 / −2.3 /
+1.8%** (all within ±5%); C1 PASS (fuel mix byte-comparable, CC_REGULAR ±0.2
TWh vs base); C4/C5a PASS. **Storage throughput recovered ENDOGENOUSLY 0.74 →
1.05 TWh (2025) with no storage-formulation change** — exactly the downstream
response the `neiso-ps-undercycling-diagnosis` predicted. Caveats within
budget: hard 1/1 (C2 2025 gas +3.0%, preliminary-923 vintage, re-audited
2026-07-04: still 57% plant reporting); soft 2/2 (C3c tail 0h vs 15/8/20h and
C5b −49.3%, both ledgered as the winter fuel-inventory family — closable only
via the documented `neiso-winter-fuel-inventory-plan-2026-07` build).
**DETERMINATION: CALIBRATED-WITH-CAVEATS** — the first ISO to pass the gate.

### Two metric fixes shipped with this session (scorer-side, all ISOs)

1. **C5c discharge-basis alignment**: the EIA-930 storage series is
   discharge-only for several BAs (NEISO `NG: PS` — pumping appears as load;
   ERCOT `battery_discharge` pre-split), so the "net" actual was silently gross
   discharge while the model side reported net (≤0 by RTE losses) — a basis
   mismatch a perfectly-cycling model could never pass. Both sides now score
   the discharge half (C5b's basis).
2. **C5c degeneracy guard (CV < 0.25 → SKIPPED)**, mirroring C4's rule: the
   NEISO 2025 actual is near-uniform (CV 0.137 — Northfield cycles near-daily
   year-round on reserves/regulation), so the 12-point Pearson has no seasonal
   shape to correlate and a perfectly flat (TRUE) model would score r=0 and
   FAIL — a metric the truth itself cannot pass. Volume stays fully scored by
   C5b (which remains a ledgered caveat, honestly worse on the aligned basis:
   the old r=0.237 was an artifact of the broken net-vs-discharge comparison).

Retention: neiso-24/25/26/27/28/29 pruned (top-15). Keeper-auditor run: PASS,
no repairs. `status.js` rebuilt (NEISO the only CALIBRATED-WITH-CAVEATS).

## 2026-07-04 — CAISO 53 lever-ab: the FINDING-caiso-evening-merit levers (PROBE; caiso-51 stays keeper)

Session executes the two levers adjudicated by
`results/calibration/FINDING-caiso-evening-merit-2026-07-04.md` on the full
caiso-51 recipe (run `2026-07-04-caiso-53-lever-ab`, bundle
`results/calibration/caiso53_lever_ab`):

- **Lever A (offer physics, commit 1ada584):** `_CAISO_OFFER_CURVE`
  CC_REGULAR/CC_CHP `committed` 0.90/0.92 → **1.00×** plant-avg HR — the
  min-stable-load block's SRMC floor; restores `committed ≥ econ_low`
  (econ_low HELD at the CAMPD-measured 0.95/0.96). DOF ledger:
  `cc_committed_hr_mult_floor`, measured-physical.
- **Lever B (measured market input, commit 3ac6f19):** firm import-tranche
  VOLUMES grounded on **DMM Annual Report RA-import capacity** (CAISO BAA
  boundary, excl Imports-MSS: 2,323 MW 2023 / 3,371 MW 2024 / 2025 carries
  2024 — open gap until the DMM 2025 annual report, ~Aug 2026), split
  PNW/DSW by the **published MIC branch-group share** north/south of Path 15
  (46.2/46.2/46.4%): per-year `IMPORT_TRANCHES_BY_YEAR["CAISO"]` firm blocks
  1072/1251, 1558/1813, 1566/1805 MW (was uncited 800/1800). Rejected
  boundaries documented per rule #14 (CEC all-CA, CARB jurisdictional,
  EIA-930 net-flow floors — negative, cannot size a gross firm block). DOF
  ledger: `caiso_firm_import_volumes`, measured-market; `n_residual` 8 → 7.

**Result vs keeper caiso-51:** the targeted CC/import complex improves —
C1 2023 CC_REGULAR PASSES (was +4.91 TWh), 2024 +9.43 (was +10.86); net
import 2024 30.0 vs 32.4 TWh actual (was 25.8); evening corridors net-import
(DSW +1213 / PNW +543 MW, the evening-export artifact gone); C5a 2024
passes; **C7 CT diurnal largely fixed** (2023+2024 CT pass; flat-floor CV
signature 0.03–0.06 → 2.6–3.1). The flagged price tension lands as
predicted: C3a +22.3/+37.9/+48.9%, C3b 0.303/0.488/0.502, C2 2025 gas
+10.5%. **New root-cause items (logged, not chased):** (1) 2023 C3c tail
454h >$200 vs 21h actual, Jan-concentrated — the measured $28/MMBtu citygate
spike × the repriced committed CC (~$213) crosses $200 where actual held
below (monthly-average gas overlay too blunt in spike months / missing
demand response); (2) C8 CT forced share 65–76% (was 29–33% lower-bound):
forced TWh flat (~all `ct_netload_drag`) but MERIT CT energy collapsed
2.3 → 0.6 TWh as grounded imports displace marginal CT — the drag floor now
IS the CT class, confirming the FINDING's structural ramp/local gap (its own
session; no floor may close it, rules #1/17–20).

**Determination NOT-YET; NOT promoted** (C7 better, C8 gated share worse —
does not beat caiso-51 on C7/C8 jointly). Both levers are grounded inputs
and stay in code (rule #15). Retention: caiso-39/40 pruned (top-15).
Follow-up filed: issue #1302 (per-ISO sub-SRMC committed-band diagnosis;
ST_GAS 0.81 remnant included). Pre-existing unrelated test failure noted on
main: `test_caiso_per_hub_intertie::test_split_resolves_to_two_flow_columns`.

## 2026-07-05 — CAISO 54: daily gas-basis probe on the caiso-53 C3c root cause (PROBE; caiso-51 stays keeper)

Follow-up on caiso-53's root-cause item 1 (2023 C3c tail 454h >$200 vs 21h
actual, Jan-concentrated): intakes the daily California Composite Average
citygate spot (EIA NG Weekly compact "Spot Prices" table, the same page
Transco Z6 NY is scraped from, `scripts/fetch_caiso_citygate_daily.py`,
2023-2025 only per the holdout quarantine) and adds a CAISO leg to
`iso_hub_daily_gas_prices` (`_caiso_hub_daily_gas_prices`) that replaces the
flat monthly SoCal/PG&E citygate hub level with a true-calendar-dated daily
shape, mean-preserving on the measured monthly basis — structurally the
NYISO dense-true-dated-Transco pattern, not NEISO's sparse-narrative one
(this also fixes a latent bug: `--gas-hub-basis-daily` had no CAISO branch
before and would have silently applied Algonquin/Boston narrative data to
CAISO if the two flags were ever combined).

Run `2026-07-05-caiso-54-daily-gas` (bundle `results/calibration/
caiso54_daily_gas`), the full caiso-53 recipe plus `--gas-hub-basis-daily`,
3-year CAISO backcast (2023-2025). **Result vs the committed caiso-53
payload (official C3c, `ordc.hoursGt200`):** 2023 454h (monthly) → 455h
(daily) vs 21h actual — essentially **unchanged**, not the collapse the
root-cause hypothesis predicted. Day-level attribution (own P1 recompute)
explains why: the daily series correctly **redistributes** the tail rather
than shrinking it — the measured citygate spot genuinely collapsed only in
the *last week* of Jan-2023 ($7.80-11.50/MMBtu), and those days now
correctly drop from 9-19 tail-hours/day to zero; but days 2-18 (measured
$16-24/MMBtu) sit *above* the monthly average once that cheap week is
excluded from it, so they gain tail-hours instead (max zonal LMP
$219.9→up to $282.9). Net January effect ≈505→489h, a real but marginal
~3% reduction. **Conclusion:** the monthly-average blunting is a real,
now-fixed defect (the last week was wrongly priced high before), but it is
**not** the primary driver of the ~450h/21h over-prediction — most of
January 2023 was persistently elevated in the real citygate market, not
spike-concentrated in the way a monthly average would blunt. **New
root-cause item (logged, not chased):** the dominant driver of the residual
gap is something else — CT_PEAKER's `ct_netload_drag` floor (forced share
40-62% per this bundle's D-2) and `ra_mustoffer_bridge` are the leading
candidates, or a genuine actual-side effect (demand response / oil-switching
/ imports) the model lacks; investigate separately, no floor forcing (rule
#1). The daily-basis input stays in code on its own physical merits (correct
day-to-day delivered fuel cost, rule #13) independent of whether it moves
C3c — a real, more-accurate input is not reverted because the residual
didn't move (rules #1/#12).

**Determination NOT-YET; not promoted** — no offer-curve tuning, only the
gas-price input's time resolution changed; caiso-51/caiso-53 remain keeper.
`legitimacy_diagnostics.json` attached (D-5's `caiso_ra_mustoffer` gap is
the same pre-existing, already-documented gap carried on caiso-53 — not
introduced by this change).

## 2026-07-05 — ERCOT WS-A: forward RTOLCAP/RTOFFCAP reserve-supply cap (PROBE `ercot40-rtolcap-forward`; ercot32 stays keeper)

The forward analogue of the last AS-path lever with no forward analogue — the
measured ERCOT on-line responsive reserve-supply cap
(`scarcity.ercot_rtolcap_supply_cap_mw`, which returned `None` for years with no
measured `ercot_<year>_ordc_reserves_hourly.parquet`, so forecast years ran
UNCAPPED). Design + full writeup: `docs/handoffs/ercot-rtolcap-forward-2026-07.md`.

**Construction** (derived committed-share × capability, forward-native): per
responsive class, the median on-line **headroom-realization** fraction
`Σ_online(eff_cap−gross)/installed_cap` from the committed CAMPD extracts,
conditioned on the net-load percentile decile × season
(`scripts/derive_ercot_rtolcap_forward.py`, rule #23), × the fleet's
reserve-eligible capacity, × a deliverability coefficient fit to the measured
RTOLCAP/RTOFFCAP **MW quantity** (never a price). Mode-aware seam (G4 pattern):
backcast byte-identical measured parquet, forecast/probe-flag the formula. The
formula never reads the LP commitment/output state (anti-F3/F4).

**Identification gate** (`scripts/validate_ercot_rtolcap_forward.py`, before any
dispatch): coverage RTOLCAP÷AS-req median **2.02/2.08/2.21×** — the sane ~2×, NOT
the ercot27 1.0× exact-coverage artifact (the gate's primary reject). RTOLCAP
annual mean +11/−6/−12% (2023/24/25); 2023 high (real-time scarcity depletion the
structural nameplate proxy can't see), 2025 low (storage/commitment growth beyond
the fixed backcast base) — documented residuals, not tuned.

**One-delta backcast probe** (`ercot40`, run163 pattern): ercot32 recipe EXACTLY
+ `ercot_reserve_supply_forward=True` (measured cap → formula, the ONLY delta),
`--year 2023 2024 2025`, registered `2026-07-05-ercot40-rtolcap-forward`.
Compared against a measured-cap re-solve of the identical recipe (both carry the
DAM-AS overlay, so the delta is purely the ORDC reserve-dual channel):

| year | formula-cap dw | measured-cap dw | Δdw | hrs>$1000 (f/m) | hrs>$200 (f/m) |
|---|---|---|---|---|---|
| 2023 | $52.89 | $53.00 | **−$0.11** | 42 / 42 | 94 / 98 |
| 2024 | $35.87 | $35.87 | **−$0.00** | 27 / 27 | 81 / 81 |
| 2025 | $35.08 | $35.08 | **+$0.00** | 4 / 4 | 12 / 12 |

**Gate PASSED.** Δdw within $0.11 (worst year) / $0.00 (2024-25) — far inside the
~$2 gate — with the acute tail identical (42/42, 27/27, 4/4 hrs>$1000) and the
mean ORDC adder matching (1.84/0.18/0.03 vs 1.88/0.18/0.03). The ±11% RTOLCAP
level residuals never reach the price because the ORDC adder fires only in the
low-RTOLCAP scarcity tail (~8–12 GW) where the formula and measured caps agree;
the level differences live in the abundant high-RTOLCAP hours where the adder is
~$0. The forward supply formula reproduces the measured cap's price-formation role
essentially exactly, from a fully forward-native supply — the WS-A gate.

**Determination: probe, NOT a keeper** (ercot32 stays the ERCOT keeper). The
lever ships default-off, ERCOT-gated; it becomes the forecast-path supply
definition automatically in forecast mode (where forecast years were uncapped
before). No off-registry tuning (#24: flag + coefficients in
`ScenarioConfig`/`constants.py` + `run_config.json`).
---

## 2026-07-05 — NYISO B-NYI-1: C-13 CC econ_high de-leak + C-17 LI-floor re-ground attempt (PROBE `nyiso 47 ccdeleak` + D-3 ablation twin; keeper stays 41)

Wave-2 scalar remediation (`docs/handoffs/scalar-remediation-plan-2026-07.md`
§2.2). Two rule-25/rule-12 items on the nyiso-41 keeper config; keeper unchanged.

**C-13 (done here).** `_NYISO_OFFER_CURVE["CC_REGULAR"]["econ_high"]` 1.21 → **1.0**.
The 1.21 was a CAMPD CC marginal-HR reach value grounded on **ERCOT's** CC
analysis and cross-borrowed (rule-25), retained only because removing it craters
C3a — a residual justification, so it neutralizes. The CT_PEAKER 13.15× ORDC
wall was **already** de-leaked to 4.0 in source (commit `0c6c833` /
probe `nyiso-42-band-deleak`); not re-touched here.

**C-17 (attempted; scalar left in place, rule-14).** The published NYISO Zone-K
LCR is already on disk (`data/raw/capacity-deliverability/nyiso/nyiso.csv`,
intake PR #1261): LI `value_pu` 1.052/1.053/1.065, import/TSL limit 325/275/275
MW. That LCR is a **peak-capacity ratio**, while `NYISO_LOCAL_SELFSUPPLY_FRAC`
is an **all-hours energy self-supply fraction** — a rule-14 boundary mismatch.
Substituting the LCR% (~1.05) or the TSL-implied ~0.94 peak fraction over-forces
~2× the physical LI generation; any scalar reproducing ~0.45 needs a
load-duration haircut tuned to the realized share (a rule-12 pin). The faithful
fix is a peak-capacity/TSL **mechanism**, not a scalar swap — so **0.45 is left
unchanged**, the constants.py comment now documents the mismatch, and issue
**#1345** tracks the mechanism rebuild. No dispatch change from C-17.

**Probe result (`2026-07-05-nyiso-47-ccdeleak`, bundle
`results/calibration/nyiso_deleak_ccecon`, 2023/24/25) vs keeper nyiso-41 —
EXPECTED regression, recorded not chased (rule #1):**

| Metric | nyiso-41 | nyiso-47 (probe) |
|---|---|---|
| C3a mean LMP 2023 | −13.3% (CAVEAT) | **−18.9% (FAIL)** |
| C3a mean LMP 2024 | −13.4% (CAVEAT) | **−18.4% (FAIL)** |
| C3a mean LMP 2025 | −9.5% (CAVEAT) | **−16.1% (FAIL)** |
| C3b shape | CAVEAT | FAIL |
| C3c tail | fail (no scarcity tail) | fail (unchanged) |
| C2 system volume | PASS | PASS |
| C1 fuelmix | pass | ST_GAS 2024 −3.49 TWh out of band |
| C4 hourly corr | r 0.916/0.87/0.818 | r 0.914/0.871/0.825 (≈flat) |

Removing the CC markup lowers CC offers → prices fall further below actual and
cheaper CC displaces steam (C1 ST_GAS). The C3a hole is **not** a CC-markup
deficit: it is missing NYISO reserve/scarcity price formation (RCPF/AS) — open
root cause **#1344**. Do NOT re-arm the markup (rules #1/#26).

**D-3 ablation twin** `2026-07-05-nyiso-47-ccdeleak-ablation` solved + registered +
linked (20 class deltas). Ablating the one NYISO merchant floor
(`nyiso_local_selfsupply`) removes the LI floor while keeping structural floors
(firm HQ/Ontario imports, nuclear, CHP steam, coal take-or-pay) — verified: LI
self-supply floor applied 3× in the probe, 0× in the twin; firm-import floor 3×
in both.

DOF ledger rebuilt (offer_curve_by_group cites #1344; Long_Island cites #1345).
`audit_keepers.py` PASS (12 pre-existing grandfathered E7/E9 warns);
`legitimacy_diagnostics.py --keepers` PASS (holdout quarantine intact, all years
2023–2025). Keeper unchanged (`keepers.json` untouched).
## 2026-07-05 — B-XISO-1: GAS_AVAILABILITY_FACTOR re-verified (audit C-18); NO probes — dead code, 0% materiality on every ISO

Scalar-remediation batch B-XISO-1. Intake:
`data/raw/reference/nerc-gads-eford-2019-2023/` (NERC GADS Generating Unit
Statistical Brochure 3, 2019-2023, "Units Reporting Events" — fetched
2026-07-05 directly from nerc.com). Value-set commit on top of that intake.

**Deltas (all five ISOs unified to one published value):**

| ISO | old | new | Δ (relative) |
|---|---|---|---|
| ERCOT | 0.85 | 0.866 | +1.9% |
| CAISO | 0.89 | 0.866 | −2.7% |
| PJM | 0.87 | 0.866 | −0.5% |
| NYISO | 0.86 | 0.866 | +0.7% |
| NEISO | 0.85 | 0.866 | +1.9% |

New value = 1 − EFORd, "FOSSIL Gas Primary, All Sizes" row (EFORd=13.44%) —
the closest published match to this constant's single "gas-fired generation
availability" concept. NERC's public GADS product is **NERC-wide only** (no
NERC-Region/ISO breakdown exists), so the old per-ISO split's "ERCOT-fleet"/
"CAISO-fleet" labels were never a real citation; one NERC-wide figure now
applies to all five ISOs (rule-14 misalignment, documented in `constants.py`
and the intake README).

**Materiality: 0% for every ISO — NO probe scheduled for any ISO.**
`GAS_AVAILABILITY_FACTOR` is not read anywhere in `src/market_sim` (grepped
clean); the LP's actual per-unit gas availability comes entirely from the
separate `EFORD` dict (`gas_cc`/`gas_ct`/`gas_st`) via
`data.fleet.get_eford()` / CAMPD-derived per-unit `eford`. Changing this
constant's value cannot move any MC, dispatch, or backcast metric in any
ISO's keeper today — confirmed by static code-path analysis, not a solve
(none run this session per the batch's operational deviation: solve capacity
was contended with concurrent ERCOT/PJM/CAISO agent sessions on this
machine).

**Open follow-up:** issue #1349 — R2 (wire in as a real fleet-mix-weighted
per-ISO reconciliation, replacing not stacking on the existing per-unit
EFORD-derived availability) vs. R5 (delete as dead code, rule 26) is an open
disposition for a future batch; whichever is chosen, re-derive the
`build_dof_ledger.py` `GAS_AVAILABILITY_FACTOR[<ISO>]` ledger rows and
`docs/parameter-citations.md` accordingly. `build_dof_ledger.py --all-keepers`
re-run (ERCOT/CAISO/PJM/NYISO/NEISO attestations updated,
`identification: residual` → `published`); MISO untouched (was never in the
map). `audit_keepers.py`: same pre-existing 1 failure (S1 status.js
staleness) / 6 warnings (E7) before and after (verified via `git stash`), no
regression. `ruff check .` clean.

## 2026-07-05 — NYISO keeper HEAD re-gate: C1/C7 regression root-caused to the B-NYI-1 offer de-leak (PROBES `nyiso 48 head-regate` + `nyiso 49 offer-ab`; keeper stays 41, STALE-VS-HEAD; calibration-complete item 1 BLOCKED)

Executes item 1 of the NYISO calibration-complete checklist and the pending
re-gate flagged in `docs/handoffs/co2-keeper-regate-2026-07-05.md` (§Keeper
status, NYISO flag). **No keeper swap; `keepers.json` untouched.**

**Finding (decision = option c: name the structural fix required first).** A
full HEAD re-solve of the keeper `nyiso-41-hub-prices` config (git 8d46b90, all
years 2023–2025, `scripts/replay_keeper.py`) **reproduces the C1/C7 regression**
and the root cause is **entirely** the B-NYI-1 `_NYISO_OFFER_CURVE` de-leak
(this session's earlier entry / commit set) — **not** the emissions R2 basis and
**not** any other post-07-03 merge.

Because `offer_curve_by_group` is resolved from source at solve time (it is NOT
in the keeper's `meta.json`), a byte-faithful replay picks up HEAD's de-leaked
NYISO offer curve: **CT_PEAKER `peak` 13.15→4.0, `econ_low`/`econ_high`
1.27/1.98→1.0/1.0; CC_REGULAR `econ_high` 1.21→1.0** (rule-25 cross-ISO-leak
neutralizations, correct per rules #14/#25). At neutral 1.0× offers the
efficient downstate LM6000 peakers (HR ~9–10) undercut the ST_GAS steam fleet
(eff HR ~11–12) on energy and dispatch near-baseload.

| metric | keeper nyiso-41 | `nyiso 48` HEAD re-gate | `nyiso 49` offer-A/B (HEAD + keeper offer) |
|---|---|---|---|
| CT_PEAKER TWh 23/24/25 | ~1.82 (2023) | **4.46 / 4.51 / 4.73** (actual 2.26/2.13/2.84) | 1.56 / 1.37 / 1.75 |
| ST_GAS TWh 23/24/25 | on-band | **6.15 / 7.58 / 9.30** (actual 8.70/11.07/15.99) | 7.86 / 9.67 / 11.08 |
| C1 free-class | 10/10 | **9/10** | 10/10 |
| C7 diurnal (D-1) | pass | **FAIL** (2024 CT_PEAKER off-peak CV ratio 0.454<0.5) | PASS (CV 1.08/1.20/1.24) |

**Attribution (D-2 twin `nyiso 49`).** The offer-A/B restores ONLY the keeper-era
offer curve on HEAD code (via `replay_keeper --offer-curve-json`) and recovers
**both** regressions — C1 back to 10/10, C7 back to PASS, CT_PEAKER back to
~1.5–1.75 TWh. The residual vs the keeper's ~1.82 is ~0.26 TWh (other HEAD
merges — emissions R2, Stage-5 interchange unification — negligible, consistent
with the co2re handoff's "R2 <0.1%"). So the **entire** C1/C7 regression is the
offer de-leak.

**What the ungrounded offer was silently compensating for (rule #17, one
mechanism per phenomenon).** The ERCOT-inherited 13.15×/1.98 CT wall was a single
fitted scalar proxying **two** real structures the model lacks: (1) the **LI/NYC
delivered-fuel basis premium** — the downstate LM6000 peakers are priced at the
Transco Z6 hub, but their real delivered gas (LI/NYC LDC citygate / interruptible)
trades far higher, so at hub prices they are cheaper than steam and over-run (the
best-so-far "open data ask"); and (2) **#1344 reserve/RCPF scarcity price
formation** — the energy+reserve co-opt is present (7 locational families, 57
ORDC steps) but **non-binding** (the pure-ED LP credits idle uncommitted peaker
capacity as deliverable reserve → reserves never go short → no reserve price
holds peakers off energy), so nothing but the artificial energy wall kept them
peaky. Removing the leak (correct) exposes both holes.

**Decision / disposition.**
- **Do NOT promote** the HEAD re-solve — it fails HARD C1 (free-class) and HARD
  C7. Option (a) rejected.
- **Keep `nyiso-41` as the keeper (option b, interim)** with a documented
  **STALE-VS-HEAD** caveat: its clean C1/C7 depend on the now-de-leaked
  13.15×/1.98 CT offer scalars, so it is **not reproducible on HEAD**; its
  committed bundle stands (rule #15) but must not be treated as HEAD-current.
- **Structural fix required first (option c, the recommendation).** A clean
  NYISO HEAD re-gate needs the peaker energy priced by real structure, not the
  offer wall: the **LI/NYC delivered-fuel basis** (physical input, rule #14,
  forward-reproducible) and/or **#1344** a binding reserve/RCPF scarcity
  mechanism. Both are the same phenomenon the wall proxied.
- **NYISO calibration-complete item 1 is BLOCKED** on that fix; the
  `calibration-complete.json` NYISO marker stays empty (holdouts remain fully
  quarantined, rule #22 — no 2022/H1-2026 solve/score/intake this session).
- **Do NOT re-arm the de-leaked scalars** (rule #26); `nyiso 49` is a diagnostic
  twin only and must never be promoted.

**Dashboard (rule #15).** Both runs registered as PROBES:
`2026-07-03-nyiso-48-head-regate` (reproduction) and `2026-07-05-nyiso-49-offer-ab`
(D-2 attribution twin), bundles `results/calibration/nyiso41_head_regate` and
`nyiso41_head_offerAB`, each with `legitimacy_diagnostics.json` (C7/C8) written.
Top-15-per-ISO retention honoured: pruned the 5 oldest NYISO registrations
(nyiso-33/34/36 + the two nyiso-37 unified-downstate/ct sidecars+payloads);
bundles retained on disk. No offer curve was tuned to any residual (rules
#1/#23).

---

## 2026-07-05 — Backcast keeper re-gate under the repaired demand data (PR #1426, merge 2a8b222)

**Task (rule #14).** PR #1426 found 15 corrupted `(iso, year)` series in
`data/raw/eia-930/eia_demand_profiles.parquet` (zero-sentinel runs + order-of-
magnitude spikes) and wired a repaired `demand-profile` clean datatype into
`eia_loader.load_demand` unconditionally (a bug fix, not a gated methodology
swap; `raw/` stays immutable, the fix lives at the curation seam). Every current
keeper (dated 07-03/07-05) was solved BEFORE that merge. Rule #14: the accurate
data stays no matter what it does to the fit; the keepers must be re-checked
against it. This entry records the **affected-keeper matrix** (which scored years
actually READ the corrupted file at solve time) and the re-gate outcome.

### Affected-keeper matrix (which scored years read the corrupted legacy file)

Determined from the demand-loading code at HEAD (`eia_loader.load_demand`):
each ISO with a dedicated per-BA `<BA> hourly` extract (`_ISO_TO_HOURLY_BA`)
reads that extract first (via `_eia_hourly_frame_filled`), and only falls back
to `eia_demand_profiles.parquet` (→ repaired `demand-profile` clean, else raw
legacy) when the per-BA frame is unavailable. **PJM has no per-BA demand extract
at all**, so it reads the legacy file for every year. Verified empirically
(`scratchpad/probe_demand_source.py`) that the dedicated frames return a full
8760 for every scored year 2023–2025 for CAISO/MISO/NYISO/NEISO/ERCOT.

| ISO (keeper) | demand source for scored years 2023–2025 | flagged-corrupt scored years | reads corrupt at solve? |
|---|---|---|---|
| ERCOT (ercot-32) | `ERCO hourly` dedicated (all years) | none | **No** |
| CAISO (caiso-51) | `CISO hourly` dedicated (all years) | 2023 (legacy) | **No** — 2023 read via CISO extract, not legacy |
| MISO (miso-41) | `MISO hourly` dedicated (all years) | 2024 (legacy) | **No** — 2024 read via MISO extract |
| NYISO (nyiso-41) | `NYIS hourly` dedicated (all years) | 2024, 2025 (legacy) | **No** — read via NYIS extract (keeper is already STALE-VS-HEAD; not touched) |
| NEISO (neiso-48) | `ISNE hourly` dedicated (all years) | 2024 (legacy) | **No** — 2024 read via ISNE extract |
| **PJM (pjm-77)** | **legacy `eia_demand_profiles` (all years; no per-BA extract)** | **2023, 2024** (legacy) | **YES — 2023 & 2024 solved on corrupted demand** |

**Conclusion: the only keeper whose scored years read the corrupted demand is
PJM (pjm-77), years 2023 and 2024.** The corruption is a **zero-sentinel run**:
23 consecutive hours in 2023 (idx 7393–7415, early Nov) and 22 in 2024
(idx 1659–1680, early Mar) held `raw_mw = 0.0`. Repair (linear interpolation,
`curate_demand_profile.py`) lifts those hours to ~36–40 GW; annual energy moves
+1.3 TWh (2023) / +1.4 TWh (2024) ≈ +0.17%, peak unchanged. PJM 2025 legacy was
already clean (0 hours changed) — an in-bundle control. The other five ISOs are
demand-repair-**unaffected** because their dedicated per-BA extracts never touch
the corrupted legacy file for any scored year (the corruption there was latent,
reachable only for 2021–2022 where CAISO/MISO have no extract — outside the
2023–2025 scored span; 2022 is a quarantined holdout).

### Re-gate method (PJM only)

pjm-77 was solved at `e9daf7e` (07-05 03:36). HEAD carries substantial post-
keeper PJM-relevant merges (offer_curves, dispatch, fleet, emission_rates), so a
plain HEAD re-solve is confounded. Per the nyiso-49 D-2 pattern, two byte-faithful
`replay_keeper.py` re-solves of the pjm-77 `meta.json` at HEAD, all years
2023 2024 2025, sequential (15 GB box):
- **Twin A "resolve"** — HEAD code + **repaired** demand (regenerated
  `demand-profile` clean tree engaged). Bundle `pjm77_regate_repaired`.
- **Twin B "ablation control"** — HEAD code + **corrupted** demand (isolated
  `MARKET_SIM_DATA_ROOT` with the `demand-profile` clean partition absent → the
  fallback reads the raw corrupted legacy). Bundle `pjm77_regate_corrupt`. The
  single delta A↔B is the demand repair.
- `resolve − ablation` (A − B) isolates the **demand repair**; `ablation − keeper`
  (B − committed) isolates the **post-e9daf7e code merges**.

### Re-gate outcome (PJM) — the demand repair moves no gate; keeper stays, verified demand-robust

Both twins solved all years 2023 2024 2025 at HEAD; scored with
`scripts/calibration_verdict.py` against the committed rubric. Registered:
probe `2026-07-05-pjm-78-demand-regate` (= Twin A, the dashboard probe); Twin B
kept as an on-disk ablation control (`results/calibration/pjm77_regate_corrupt`,
**not** dashboard-registered — a corrupted-demand run must never render as a
result, per the rule-15/co2re-handoff ablation-control convention).

**Every scored criterion verdict is identical across keeper / Twin B / Twin A**
(NOT-YET; C1 fuelmix, C2 sysvol, C3a/b/c price, C8 forced-share FAIL; C4 dispatch-r,
C5a CO2, C7 diurnal PASS). The *only* status change is C6 governance PASS→UNATTESTED
on both twins — a pure replay artifact (the re-solved bundles carry no
`calibration_attestation.json`; the LP dispatch is unchanged), **not** a real gate move.

**Attribution (model values; `B−keeper` = post-e9daf7e CODE merges, `A−B` = the DEMAND repair):**

| criterion / key / year | keeper | Twin B (HEAD+corrupt) | Twin A (HEAD+repaired) | B−keeper (code) | A−B (demand) |
|---|---|---|---|---|---|
| fuelmix CC_REGULAR 2023 (TWh) | 295.006 | 295.006 | 295.334 | **+0.000** | +0.328 |
| fuelmix CC_REGULAR 2024 (TWh) | 322.291 | 322.291 | 322.837 | **+0.000** | +0.546 |
| fuelmix COAL_BIT 2023 / 2024 (TWh) | 112.435 / 112.035 | =keeper | 112.540 / 112.150 | **+0.000** | +0.105 / +0.115 |
| sysvol gas 2023 / 2024 (TWh) | 353.59 / 374.80 | =keeper | 353.97 / 375.38 | **+0.000** | +0.380 / +0.580 |
| sysvol coal 2023 / 2024 (TWh) | 122.61 / 122.30 | =keeper | 122.72 / 122.42 | **+0.000** | +0.110 / +0.120 |
| CO2 2023 / 2024 (Mt) | 269.37 / 273.62 | =keeper | 269.63 / 273.96 | **+0.000** | +0.264 / +0.343 |
| mean LMP 2024 ($/MWh) | 27.19 | 27.19 | 27.16 | **+0.000** | −0.030 |
| **all 2025 values (gas/coal/CO2/LMP)** | — | **=keeper** | **=keeper** | **+0.000** | **+0.000** |

**Two findings, both decisive:**

1. **`B − keeper` is EXACTLY 0.000 on every value.** Twin B (HEAD code, corrupted
   demand — the keeper's own solve conditions) reproduces the committed pjm-77
   bundle byte-for-byte. So the ~30 post-`e9daf7e` changed files touch nothing in
   PJM's solve path: **pjm-77 is fully HEAD-reproducible, no confound** (contrast
   NYISO nyiso-41, where the offer de-leak did move the replay — the STALE-VS-HEAD
   case). This makes `A − B` a clean single-delta measurement of the demand repair alone.

2. **`A − B` is the entire (tiny) movement, confined to the two corrupted years.**
   Repairing the 23 h / 22 h zero-sentinel runs adds ~+0.5 TWh/yr of generation
   (served by mid-merit CC + baseload coal), +0.26–0.34 Mt CO2 (+~0.1 %), and moves
   mean LMP by ≤0.03 $/MWh. **2025 is exactly 0.000** (its legacy demand was already
   clean — the in-bundle control). No criterion crosses its band; the free-class C1
   score (10/12) and every hard/soft verdict are unchanged.

**Decision (rules #1 / #14 / #15).** The repaired demand is the accurate input and
it **stays** (rule #14) — but it does **not** gate worse *or* better: it is
**immaterial** to every PJM scored criterion. Therefore:
- **Keep `2026-07-05-pjm-77-ct-relfloor` as the PJM keeper**, now annotated
  **verified demand-robust** (its committed bundle solved on the 23 h/22 h corrupted
  shoulder-hours, but the repair changes no gate and only ~0.1 % of volume in
  2023/2024). `keepers.json` unchanged.
- **Do NOT swap to Twin A (pjm-78).** Not because it regressed — it did not — but
  because a swap buys nothing (identical verdict) while it would (a) discard the
  keeper's committed governance attestation and its zero-forcing ablation twin
  (rule #20 / audit E9), and (b) is unnecessary since Twin B proves the keeper is
  already HEAD-reproducible. This mirrors the co2re-handoff disposition (confounded/
  neutral HEAD re-solve registered as a PROBE, keeper not swapped).
- **No root-cause branch triggered.** Rule #14's "accurate data gates worse ⇒
  discovered miscalibration" clause does **not** fire here (the repair is neutral,
  not adverse). Nothing was tuned to any residual (rules #1 / #23).

**Other ISOs: no action.** Per the matrix above, CAISO/MISO/NYISO/NEISO/ERCOT read
dedicated per-BA extracts for every scored year 2023–2025, so their flagged
legacy-file corruption never reached a keeper solve — no re-gate needed. NYISO
(nyiso-41) was left entirely untouched (already documented STALE-VS-HEAD, blocked on
the peaker-pricing structural fix owned by a parallel session); its 2024/2025 legacy
corruption is moot because NYISO reads the `NYIS hourly` extract. Holdouts 2022 /
H1-2026 remain fully quarantined (rule #22): the corrupted 2022 rows are repaired as
*data* by PR #1426 but stay unsolved and unscored.

## 2026-07-05 — NYISO CT/ST reliability-floor re-derivation: C7 FIXED, floor-forcing cleaned (PROBES `nyiso 51 floor-rederive` + `nyiso 52 floor-rederive-ctgas`; keeper stays 41 STALE-VS-HEAD; calibration-complete item 1 still BLOCKED on #1344)

Executes the CT/ST reliability-floor re-derivation named as the remaining
structural work in PR #1427 / the NYISO HEAD re-gate (2026-07-05 entry above):
the Long Island CT over-run residual was floor-forced, so the delivered-fuel
basis (PR #1427) could not move C7 and NYISO calibration-complete item 1 stayed
blocked. Rule 17/18/23 audit + re-derivation; #1344 (reserve/RCPF scarcity) is
out of scope (parallel LP-core refactor). Keeper stays `nyiso-41`
STALE-VS-HEAD; **`keepers.json` unchanged (recommendation only, rule #3).**

### Audit (rule 17) — each enabled NYISO CT/ST floor, driver / hours / forward story

Evidence: nyiso-48 `legitimacy_diagnostics.json` (D-1/D-2/D-4) + CAMPD downstate
CT/ST diurnal CF.

1. **reliability_floor × CT_PEAKER, NYC/LI `*_CT_ev` ramps (HB14-21).** Driver:
   downstate afternoon-evening AC-peak temperature commitment. In-window, forward-
   reproducible. **LEGITIMATE — kept.**
2. **reliability_floor × CT_PEAKER, NYC standalone 24h step (tmax 31.7 / 0.1833,
   enabled, NO window).** Bound all 24h on hot days incl. overnight where measured
   CAMPD NYC CT CF ~= 0.018 flat; stacked on the NYC_CT_ev ramp (rule 18/19). The
   D-4 off-window binder (baseline 30.5/30.9/34.3% of floored CT MWh off-window).
   **BUG (rule 17) — disabled (`r1_disabled=True`).**
3. **nyiso_local_selfsupply × LI in-zone thermal (incl CT_PEAKER), 0.45 × LI load,
   ALL 24h.** Source = LI LCR / firm import_limit 325/275/275 MW
   (`data/raw/capacity-deliverability/nyiso/nyiso.csv`), a PEAK-hour ICAP basis,
   NOT an all-hours energy driver; 0.45 is residual-identified (constants.py DOF
   ledger S5, issue #1345). D-2: forced 1.84/2.87/1.86 TWh of CT_PEAKER
   (43/65/42%), mostly overnight where measured LI CT CF ~= 0.06 flat and LI
   imports never bind off-peak (reserve-incidence handoff Finding 4). **Over-forces
   overnight (rule 17) — narrowed to the HB14-21 peak window; 0.45 level UNCHANGED.**
4. **ST floors (NYC/LI ST_GAS persistent 24h base 0.391/0.289 + evening ramps).**
   Applied on frac × AVAILABLE cap, when-available CF basis → all-hours CF
   ~0.04-0.06 matches CEMS; passes C7 (D-1) and D-4 (declared 24h in-city
   must-run). Rule-20 ST_GAS forced-share exceedance is a small-denominator
   artifact of the steam under-run. **LEGITIMATE — left unchanged.**

### Re-derivation (rule 18/19/23 — narrowings, not re-levels)

- `data/raw/reference/reliability_floor_coeffs_NYISO.csv`: added `r1_disabled`
  column; NYC CT_PEAKER tmax-31.7 step marked `r1_disabled=True`.
- `transmission.inject_nyiso_local_selfsupply`: gated to
  `NYISO_SELFSUPPLY_FLOOR_HOURS` (HB14-21). The 0.45 fraction is untouched (the
  #1345 mechanism fix is still open); only the overnight hours it had no driver
  for are removed. `constants.py` / the injector docstring / tests updated.
- These are unconditional NYISO structure (backcast + forecast), not gated probes.

### Gate (one-delta vs `nyiso 48 head regate`, all years 2023/2024/2025)

| metric | nyiso-48 | nyiso-51 floors | **nyiso-52 floors+gas** | actual |
|---|---|---|---|---|
| CT_PEAKER TWh | 4.46/4.51/4.73 | 3.70/2.84/3.86 | **2.02/2.33/2.91** | 2.26/2.13/2.84 |
| ST_GAS TWh | 6.15/7.58/9.30 | 6.29/7.59/9.43 | 6.72/7.77/9.74 | 8.70/11.07/15.99 |
| C1 free-class | 9/10 | 9/10 | 9/10 | — |
| C7 (D-1) 2024 CT cv_ratio | FAIL 0.454 | PASS 2.393 | PASS 3.47 (r 0.84) | — |
| C3a mean LMP | -17/-18/-15% | -16.2/-15.5/-13.6% | -13.5/-14.7/-12.5% | — |
| C3c >$300 h | 0/0/7 | 0/0/7 | 0/0/7 | 10/12/42 |
| D-2 CT forced-share (rule-20 ≤10%) | 22%+ss FAIL | 25.6/34.1/25.1%+ss FAIL | 45.8/54.5/39.3%+ss FAIL | — |
| D-4 CT off-window | 30.5/30.9/34.3% (incl overnight) | h14-only, 0 overnight | h14-only, 0 overnight | — |

### Disposition

- **C7 (NYISO calibration-complete item 1's blocker) is FIXED** in both configs.
  The overnight CT flatness is gone: reliability-floor CT overnight energy =
  **0.000** (was ~0.18 TWh from the NYC step), self-supply CT forcing HALVED
  (1.84/2.87/1.86 → 0.90/1.23/0.89 TWh). CT_PEAKER volume is near-exact with the
  gas premium (nyiso-52: 2.02/2.33/2.91 vs actual 2.26/2.13/2.84); C1 CT_PEAKER
  moves FAIL→in-band.
- **rule-20 forced-energy budget: still FAILS for CT_PEAKER (>10%)** in both
  configs (nyiso-52 higher because the gas premium shrinks the economic-CT
  denominator). Reported explicitly. This is **cleanly attributable to #1344**:
  without the reserve/RCPF scarcity structure the downstate peakers never clear
  economically (reserve-incidence handoff Finding 3 — idle peakers = phantom
  reserve = no scarcity price), so the (now in-window, legitimate) floors carry
  ALL the CT commitment. #1344 raises the economic CT share and drops the forced
  share below 10% — it is the same lever that lifts C3a/C3c.
- **C3a/C3c still FAIL** — the missing #1344 peaker-scarcity price. The
  delivered-fuel premium (nyiso-52) lifts C3a from -17/-18/-15% to
  -13.5/-14.7/-12.5% but not to band; the >$300 tail is unchanged.
- **D-4 residual (~34%) is a metric-boundary artifact, NOT off-window binding.**
  The reliability floor binds EXACTLY h14-21 with 0.000 overnight; the flagged
  "off-window" is entirely hour 14, because D-4's hardcoded canonical CT window is
  h15-21 (CAISO ct_netload_drag derivation) while the NYISO ramp is source-derived
  HB14-21 (start_hour=14). Left as-is (rule 23 — not tuned to the gate).
- **Keeper-candidate exists PENDING #1344.** `nyiso 52 floor-rederive-ctgas`
  (re-derived floors + the default-off delivered-fuel basis) is the recommended
  eventual NYISO keeper config — it needs no further floor work, only the #1344
  reserve-price structure to lift C3a/C3c and drop the CT forced share below 10%.
  Keeper stays `nyiso-41` STALE-VS-HEAD; keepers.json unchanged; did NOT re-arm
  the de-leaked offer scalars (rule #26).

## 2026-07-06 — ERCOT + NEISO keeper HEAD re-gate: calibration-complete checklist item 1 (probes `ercot 32 head-regate` + `neiso 48 head-regate`; NEISO fully HEAD-reproducible, ERCOT STALE-VS-HEAD; no keeper swap)

Executes item 1 of the ERCOT/NEISO calibration-complete checklists
(`docs/handoffs/forecast-validation-program-2026-07.md` §3.4) — both keepers
were dated 2026-07-03/07-05 and predate the 07-04 ISO-offer/data merges, and
(unlike PJM `pjm-77`/`pjm-78` and NYISO `nyiso-48`/`49`) had never been
re-gated at HEAD. Byte-faithful `replay_keeper.py` re-solve of each keeper's
`meta.json`, all keeper years in one invocation (ERCOT/NEISO both 2023-2025),
run as two concurrent background jobs (rule 12, cap 2). Scored with
`scripts/calibration_verdict.py --json` against the committed rubric;
diffed every criterion's `model` value between the committed keeper run and
the HEAD replay.

### NEISO (`neiso-48`) — fully HEAD-reproducible

Every scored `model` value is byte-identical between the committed keeper and
the HEAD replay — D1 (C7) and D2 (C8) diagnostic rows match exactly, and every
criterion record in `calibration_verdict.py`'s output (fuelmix, sysvol,
price_mean/shape/tail, dispatch_corr, co2, storage, shape, forced_share) has
an identical `model` field. The only differences are status-label churn
(CAVEAT→FAIL on sysvol/price_mean/price_shape/price_tail/storage/shape-ST_GAS,
PASS→UNATTESTED on governance) — the same replay artifact documented for
`pjm-77`/`pjm-78`: a byte-faithful replay carries no
`calibration_attestation.json`/DOF ledger, so the "ACCEPTED MEASURED-INPUT
LIMITATION" classifications that downgrade a FAIL to an accepted CAVEAT are
absent. Determination is NOT-YET in both (unchanged) for the same reason
(the pre-existing ST_GAS diurnal-shape gap).

**Decision:** `neiso-48` is verified **HEAD-reproducible**. `keepers.json`
unchanged. Registered as probe `2026-07-05-neiso-48-head-regate`
(bundle `results/calibration/neiso48_head_regate`).

### ERCOT (`ercot32`) — STALE-VS-HEAD; real movement, not gate-clean before or after

Several `model` values move between the committed keeper (solved at git
`20ebd33`, 2026-07-03 19:21) and the HEAD replay (git `eef4513`): fuelmix TWh
shifts across CC_CHP/CC_REGULAR/CT_PEAKER/ST_GAS (e.g. CC_CHP 30.68→26.06 TWh
2023, CC_REGULAR 133.21→145.38 TWh 2023), CO2 (155.69→153.39 Mt 2023),
price_mean (2024: 29.28→27.45, flips FAIL→PASS), price_tail (2023: 77→93
hours >$300), C8 CT_PEAKER forced share (2023: 11.1%→15.9%, both FAIL).

**Cheap D-2-style attribution (nyiso-49 pattern):**
- **Offer curve** (`offer_curve_by_group`, `run_config.json`): byte-identical
  across all 13 ERCOT classes between keeper and head — RULES OUT the offer
  surface (contrast NYISO, where the offer de-leak was the entire cause).
- **Raw input data** (EIA-930/EIA-923/CAMPD file hashes in `meta.json
  shared_inputs`): byte-identical — RULES OUT data intake / the demand repair
  (consistent with the co2-keeper-regate handoff's affected-keeper matrix:
  ERCOT reads the dedicated `ERCO hourly` extract, never the corrupted legacy
  file).
- **`confirmed_exits_enabled` default flip** (145a7f5, 2026-07-05): gated
  `mode == "forecast"` only (`runner.py:360`) — inert for a backcast replay.
- **One concrete, dated code mover found:** `fleet.py`'s curated-bin-drift
  reconciliation (merged 9c4a0f6 / PR #1362, 2026-07-05 07:20 — AFTER the
  keeper's 2026-07-03 19:21 solve) reclassifies a plant's class when EIA-923
  disagrees with the static `custom-bin-assignments.csv`: Dansby ST_GAS→
  CT_PEAKER, Powerlane CT_PEAKER→ST_GAS, Silas Ray CT_PEAKER→CC_REGULAR
  (each ~110-200 MW, ~450 MW combined). Real, but too small alone to account
  for the multi-TWh class shifts observed — a contributing, not full,
  explanation. The remaining mover is **not isolated** here (would need an
  ablation twin / further code inspection outside this wave's
  no-`src/market_sim`-edits scope).

Determination is NOT-YET in both keeper and head, on the same hard-FAIL set
(fuelmix, sysvol, price_mean, price_shape, price_tail, forced_share) — sysvol's
CAVEAT→FAIL move is the same missing-attestation-ledger artifact as NEISO, not
a new failure. No criterion family flips from an overall PASS to an overall
FAIL; one individual cell (price_mean 2024) flips FAIL→PASS.

**Decision:** `ercot32` is **STALE-VS-HEAD** (not byte-reproducible, unlike
PJM/NEISO), but this changes no keeper disposition — the keeper was already
NOT-YET on structural grounds documented in its own registry definition
(named MODEL MISS root causes, C8 forced-energy budget FAIL). No swap: no
candidate reproduces the keeper cleanly or improves on it wholesale. Registered
as probe `2026-07-06-ercot32-head-regate` (bundle
`results/calibration/ercot32_head_regate`). Full mover isolation (which
`src/market_sim` commit between `20ebd33` and `eef4513` moves ERCOT dispatch
beyond the 3-plant reclass) is an open follow-up, out of this wave's scope.

### keepers.json

Unchanged for both ISOs. Neither re-gate is "gate-clean AND strictly
reproduces/improves": ERCOT remains NOT-YET on the same hard-fail set; NEISO's
clean reproduction is a lateral confirmation, not an improvement. No
promotion — that stays a separate owner decision (rule #15).

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule #22).

## 2026-07-06 — MISO L-14 Wave-3: C5b adjudication + C1 decomposition + coal marginal-SRMC bound (run `miso 42 coal-econ-srmc`; keeper stays miso-41, promotion recommended to owner)

**Lane:** Wave-3 MISO L-14 (gap register G-23/G-40). Three deliverables, in mandate order.

### 1. C5b storage throughput (+1330%): benchmark basis artifact — NO adder (FINDING, no solve)

`results/calibration/FINDING-miso-c5b-storage-benchmark-2026-07.md`. The scored 2025 actual
(0.2447 TWh) is EIA-930 **battery-only** — MISO reports no PS series at all (verified: hourly
extract has only `NG: BAT`; the BALANCE files' pumped-storage column is all-null in every scored
year) — while the model side includes the 2,417 MW PS fleet (Ludington + Taum Sauk). The model's
PS throughput sits INSIDE the eGRID net-energy-implied band (|net|·RTE/(1−RTE): 2.5–4.4 TWh vs
model 2.8–3.5), so there is no over-cycling residual to price. Per the PJM adjudication in
`constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`, no citable PS throughput cost exists (O&M
<$1/MWh; the real suppressor is reserve duty = a measured-reservation channel, not a $/MWh
adder); a MISO adder would be a fit to a mis-measured target (rule 13). Both adders stay 0.
Scorer-side like-for-like fix (battery-only vs `NG: BAT` when the BA reports no PS) flagged to
the rubric-infra owner; C5c 2025 (r=0.465) is the same basis artifact.

### 2. C1 CC_REGULAR +44 TWh: decomposition + ONE grounded lever (`coal_econ_srmc_bound`, miso-42)

`results/calibration/FINDING-miso-cc-decomposition-2026-07.md`. The +44.35/+43.22 TWh (2023/24)
displaces **imports** (−23.2/−19.4 TWh — model 14.7/3.7 vs actual 37.9/23.1) and the **priced-out
non-CC gas classes** (CT_PEAKER −12.0/−9.3, ST_GAS −10.9/−14.3, CHP/OTHER_FOSSIL −10.6/−12.9) —
NOT coal (family −6.0/−8.3 in 2023/24) and NOT wind (delivered-pinned). ~73% is MISO-South;
flat across the day (model CC off-peak CV BELOW actual); worst in shoulder months. CC is NOT
availability-bound (dispatch 78–81% of the 230 TWh availability integral vs actual 59–62%) —
and the DP-1 magnitude check (actual 135.6 × 1.34 MIP wedge = 181.7 ≈ model 179.9) says the CC
row itself is the P1 commitment-posture wedge.

**Lever implemented (one, grounded, zero fitted params):** `coal_econ_srmc_bound` — marginal
(econ*/peak) coal tranches' fuel passthrough clamped to ≥1.0, so no marginal coal offer sits
below the plant's measured F923 incremental delivered SRMC; committed/must-run keep the
contracted take-or-pay discount (burndown Evidence 2: model LMP $25.9 < cheapest measured coal
tranche $28.3 with coal marginal 93.9% of hours). A fitted-DOF *removal*, forward-valid.
Full-span solve registered: **`2026-07-06-miso-42-coal-econ`** (bundle
`results/calibration/MISO/miso_42_coal_econ_srmc`), determination NOT-YET.

vs miso-41 (2023/24/25): C3a −8.2/−13.0/−18.9% (was −9.8/−15.6/−19.5%); ST_GAS 6.8/7.3/5.3 TWh
(was 2.9/3.3/3.4; actual 13.8/17.6/15.7); CT_PEAKER 15.0/20.8/17.6 (was 13.4/17.3/16.9); net
imports 19.5/6.3/−4.6 (was 14.7/3.7/−5.1); C2 2025 coal +7.2% (was +8.8%); CO2 PASS ×3;
legitimacy D-gates Overall PASS (C7/C8 PASS; the bound forces zero energy — offer bound, not a
floor). Costs, reported per rule 1 without reverting: coal 2023/24 under-run deepens
(154.9/144.2 vs actual 175.0/167.1) — the sigmoid's sub-cost marginal discount was silently
compensating for missing coal **self-commitment volume** (note: the MISO fleet branch does not
yet size the committed band from the measured EIA-923 Sch-5 contract share —
`run_calibration.py` passes no `takeorpay_by_plant` on the thermal-tranche path; open root
cause). CC_REGULAR +46.4/+46.8/+28.6 (worse +2.9/+4.3/+1.8): the bound was never the CC lever —
the CC row needs the commitment posture. C3c tail still 0 h ×3 (same).

### 3. Scarcity-posture design note (design only, rule 17 driver/window/forward story)

`docs/multi-iso/miso-scarcity-posture-design-2026-07.md`: (A) pooled linear commitment-posture
lever — (zone×class) online-capacity variable U with min-load coupling, startup cost on ΔU⁺,
and the pergen reserve cap online-gated (`R ≤ ramp10×U`) so the published curves can genuinely
run short; honesty-gated on measured MISO cleared reserve MW/MCPs, NEVER on the tail residual;
memory-feasible at the 30-pool grain (G-40). (B) Midwest locational reserve family —
DATA-BLOCKED on MISO's historical zonal operating-reserve requirement series (the ask is
filed in the note); a hand-sized requirement is forbidden. Sequencing: A first (it is also the
C1-CC and intra-gas lever), B when the data lands.

### keepers.json — recommendation to owner (no swap in-session)

**Recommend promoting miso-42 to keeper** on the miso-41→miso-39 precedent: strictly more
structurally faithful (a fitted sub-cost discount removed from market-priced marginal fuel;
nothing tuned, D-gates PASS, C3a/C2-2025/intra-gas structure all move toward actuals), even
though the CC row and 2023/24 coal worsen — those are the named next root causes (commitment
posture; committed-band sizing from measured contract shares), not reasons to keep bidding
marginal coal below its measured cost. If the owner declines, miso-42 stands as the registered
A/B evidence for the posture workstream. Keeper unchanged this session: miso-41.

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule #22). Solve years 2023–2025 only,
one invocation, years sequential (G-40 memory discipline; 12 GB swapfile).

## 2026-07-06 — ERCOT Stage-4 overlay-off integration (`ercot34`; KEEPER-CANDIDATE recommendation, owner decision pending) + G-12 replay-gap attribution CLOSED (`ercot35`/`ercot36` A/B arms)

Wave-3 ERCOT lane (L-12): G-38 (AS co-opt plan §6/§7 stage 4), G-22 fold, G-12
attribution. Three solves, all registered; keeper `ercot32` unchanged
(`keepers.json` untouched — promotion is an owner decision).

### G-12 first (it re-scoped everything): the "container-reproducibility drift" is a replay-contract gap

The keeper solved with **four ERCOT gas-geography fields meta.json does not
persist** — `ercot_zonal_gas_basis=True`, `ercot_west_netload_gas_shape=True`,
`ercot_west_gas_delivered_floor=0.4`, `oil_primary_bin_fuel=True` (proven by
the keeper bundle's resolved `run_config.json`; the fields' ScenarioConfig
defaults are off). Every "byte-faithful" `replay_keeper.py` replay therefore
solved a **different config** — no Waha/zonal delivered-gas geography on any
of ERCOT's 963 gas units: the `2026-07-06-ercot32-head-regate` (#1451), the
FINDING §6.3 replay, the ercot33 ex-overlay baseline, and the ercot40 WS-A
probe all carry this confound (their *internal* A/B conclusions stand — both
arms shared the config; their absolute levels are shifted). Same disease
class as the pjm-77 `ct_netload_drag` meta-gap. **Fix filed, not made** (the
meta writer is `run_calibration_full.py`, orchestrator-unification lane
ownership); until then any ERCOT replay must restore the four fields via
`--set` (the registered bundles' `run_config.json` carries them resolved).
**Check #1346 (CAISO drift) for the same mechanism.**

Attribution, quantified by the registered A/B pair (CC_REGULAR TWh
2023/24/25; committed keeper 133.21/135.64/135.31):

| arm | config | CC_REGULAR | reads as |
|---|---|---|---|
| `2026-07-06-ercot35-replay-metagap-arm` | stage-4 deltas, flags DROPPED (= what every prior replay ran) | 145.38/153.47/145.49 | **reproduces the head-regate EXACTLY** — the drift is deterministic on HEAD in a fresh container |
| `2026-07-06-ercot34-stage4-overlay-off` | stage-4 deltas, flags restored | 139.07/142.68/141.81 | M1 (flags) = **+6.3/+10.8/+3.7** |
| `2026-07-06-ercot36-head-config-faithful` | keeper recipe faithful, overlay ON | 139.07/142.68/141.81 | M2+M3 (real HEAD code movement) = **+5.9/+7.0/+6.5** |

M2 = the coal max-CF ceiling re-derive (`f5543232`, 07-03T20:10Z, ~50 min
after the keeper's solve: year-pins dropped, Limestone 0.82/0.86/0.87→0.95,
Fayette 0.99, J K Spruce 0.95, Oak Grove uncapped → COAL_PRB +3.9/yr) and
M3 = the fleet.py curated-bin-drift reconciliation (#1451's contributor:
CC_CHP −4.3 and CT_CHP −2.2 TWh/yr of mostly **label** movement — plant-grain
CC_CHP dispatch moves only −0.36/−0.25/−0.37). Both are legitimate, cited
re-derives; notably they move CC_REGULAR **toward** CAMPD-measured (2023
actual 141.7). The head-regate's +12.2 = M1 6.3 + M2/M3 5.9 — **fully
accounted; G-12 closed.** FINDING §6.3 addendum + co2-keeper-regate handoff
updated. D-8 consequence: the 10–18 TWh "instability" was config divergence;
the in-container CT↔ST offer-wall fragility finding stands separately.

### G-38: the Stage-4 run (`ercot34`) and its gates

`ercot34` = ercot32 recipe (flags restored) + **exactly two deltas**:
`ercot_dam_as_overlay=False` (the measured DAM-AS overlay retired — the
plan's replacement under test) + `ercot_reserve_supply_forward=True` (WS-A
formula supply). **WS-B endogenous storage swap NOT taken** — its stage-2
quantity gate landed 0.54–0.61× vs the 0.8–1.3× band and plan §4 conditions
the swap on validation; the measured storage treatment (rule-13 admissible)
stays, carried as the open G-5 item. P1-only, `--year 2023 2024 2025`, one
bundle. The two deltas are **dispatch-invisible at class grain** (ercot34 ≡
ercot36 volumes to 0.01 TWh) — the whole mechanism swap lives in the price
stack, as designed.

Gates (all vs RT actuals; same-code baseline = ercot36 ex-overlay, exact
per-column arithmetic; ercot36's overlay-on/off pair reproduces the WS-F
decomposition to the cent — 2024 overlay dw +4.51 = i 2.23 RT-supported +
ii 1.70 DA-boundary + iii 0.58 discretionary; 56 of its 78 tail hours
overlay-carried):

| gate | verdict | evidence |
|---|---|---|
| G-3 no broad elevation (anti-F1) | **PASS decisively** | max monthly Δ vs same-code ex-overlay = **$0.00** (largest magnitude −$0.40, Sep-2023); Feb-2023 unchanged. The ercot27 artifact is absent. |
| G-5 quantity fidelity | **PASS** (WS-B deferred, documented) | WS-A identification re-verified on HEAD: coverage median 2.02/2.08/2.21× (~2×, not the 1.0× artifact); level +10.6/−5.6/−12.0% documented residuals. One-delta on faithful config: Δann ≤ $0.05, tails 92-vs-93/22/7. Storage award = measured by construction. |
| G-6 one event, one channel | **PASS** | RTORDPA ∧ ORDC-adder Σmin = $543/$104/$2 per MWh·h (46/11/0 joint hours; ≤8.3% of the smaller channel) — ercot27-audit scale, disclosed. |
| G-2 hold the held months | **PASS with 2 named breaches** | 2025 MAE 2.71 vs keeper 2.06 (+0.65 ≤ +$1) ✓; Aug-2024 −1.11 within ±$3 ✓; Aug/Sep-2023 +12.3/+11.8 vs the *committed* keeper breach ±$3 — 100% M2/M3 base-code movement (same-code Δ −0.09/−0.40) and **toward** actual (Aug: 129.3→141.6 vs actual 191.7). |
| G-1 acute days | 2023/2025 clause **PASS**; May-2024 days **FAIL, named** | Jun/Aug-2023 53.5/141.6 ≥ keeper-ex-overlay 48.2/129.3 ✓. May-2024 8/24/26 daily dw on RT: −56/+34/−51% vs ±25% — the overlay carried Jan/May-2024 at −14.3/−20.5 dw month-local (F6 DA-boundary + F7 discretionary, non-reproducible by design) and the remaining RT-side miss is the G-22 wedge (below). |
| G-4 tail structure | **PASS on the honest basis, 2025 disclosed** | 2023: 92 h >$200 (0.51× of 181; keeper 0.43×), >$500 83 vs keeper 68 (actual 104) — deep tail NOT collapsed, improved. 2024: honest 22 h (keeper's committed 78 was 72% overlay-carried; its own ex-overlay self = 22 on this code). 2025: 7 vs keeper 10 (the 4 removed hours were overlay-carried). |
| G-7 attribution ledger | complete | every miss above mapped to {F6 DA-boundary, F7 discretionary, M2/M3 base movement, G-22 wedge/offer-wall (energy-base, out of scope)} — no unnamed residual. |

C-scores vs the keeper: **C1 fuel-mix flips to PASS** (the keeper's hard
C1-2024 CC caveat clears — HEAD volumes sit nearer measured), **C3a-2024
passes on RT without the overlay** (the F6 prediction), C3b-2023 improves
0.393→0.324 (2024 passes), C3c honest 0.51/0.42/0.23× all FAIL (the keeper's
2024 "pass" was the measured overlay, not formed price), C2-2025 gas −5.0%
(preliminary-vintage family, keeper carried −3.0%), C8 CT_PEAKER-2023 12.4%
(keeper's own 11.1% hard-fail family, inherited — no floor touched).

### G-22 fold: does endogenous reserve withholding close the shape miss? NO — measured, filed

In the 106 missed 2023 tail hours (60 in Aug, HOD 14–20): the co-opt's ORDC
family adder is ~zero (p50 $0.1; >$10 in exactly 1 hour), reserve MCPCs ~0,
energy dual p50/p90 $52/$75 — while in the 75 caught hours the same stack
prices correctly (dual p50 $956, adder p50 $43, MCPC p50 $3.3k). Measured
RTOLCAP in the missed hours: p50 8.1 GW — above the ORDC knee, exactly as
the FINDING's decomposition said (adder-carried ≤6 h/yr in reality). The
endogenous co-opt reserve channel **closes none of the C3b/C3c miss, for the
structural reason the FINDING names**: the miss is energy-offer-carried
scarcity against the P1 online-capability wedge (~3.2 GW phantom sub-$200
spare), not reserve underpricing. The remedies stay the filed structural
items (condition-responsive offer surface; commitment thinness / sub-2-day
outage structure) — the ercot33 tuned offer wall stays REJECTED (rules 13/26).

### Keeper recommendation (plan §6 rule, applied as written)

G-3/G-5/G-6 **pass** and every G-1/G-2/G-4 miss carries a named G-7 root
cause ⇒ **the §6 promotion condition is met: recommend promoting `ercot34`**
— strictly more real market structure (the DAM co-optimization ERCOT actually
ran forms the AS scarcity signal endogenously; the measured settlement
residue is demoted to the F6/F7 diagnostic), C1 newly PASS, and the honest
C3c disclosed. Promotion is the **owner's decision** and additionally
requires (rule 21 / C6): calibration attestation, DOF ledger, and a
zero-forcing ablation twin solved on the exact ercot34 config — none of
which exists yet. **Container-reproducibility statement (mandate):** ercot34
was solved fresh on HEAD `3b31193` in this session's container (and ercot36
independently reproduces its dispatch exactly); its recipe re-solves on HEAD
only when the four un-persisted fields are restored (`run_config.json`
carries them; a naive meta replay will NOT reproduce it until the meta
writer is fixed). The committed ercot32 numbers do NOT reproduce on HEAD
even config-faithfully (M2/M3, named above, legitimate).

### Holdouts / gates

No solve, score, or intake touched 2022/H1-2026 (rule 22); all three runs
span 2023–2025 in one bundle each (rule 16); `audit_keepers.py --check` PASS
(pre-existing E7/E9 warnings only) and `legitimacy_diagnostics.py --keepers`
exit 0 with D-9/D-6 quarantine PASS after registration.

## 2026-07-06 — Carbon-zero ISOs v2 emission-rate no-solve re-scores (PROBES `ercot32/pjm-77/miso-41 v2rescore`; no keeper swap; lane L-8b)

Executes the two cheap follow-ons `emissions-co2-rate-plan-2026-07.md` §9.6
point 1 recommended immediately: re-score the three **carbon-zero** keepers
(ERCOT `ercot32-ordc-total-rtolcap`, PJM `pjm-77-ct-relfloor`, MISO
`miso-41-ct-evening`) under `use_plant_emission_rates_v2=True`, with **NO LP
solve**, and register each as a dashboard PROBE (rule #15) so the improved CO2
coverage is visible without waiting on the CAISO/NYISO/NEISO re-gates (lanes
L-10/L-11/L-15). The `scenarios.py:389` default is **not** flipped — §9.6
sequences that only after all three carbon-priced ISOs re-gate under v2.

**Dispatch/prices/generation are provably byte-identical (verified).**
`use_plant_emission_rates_v2` only sets each generator's `emission_rate_co2`
(`fleet.apply_plant_emission_rates_v2`); in `fleet.assemble_mc` that rate enters
marginal cost **only** through `emission_rate × carbon_price`. ERCOT/PJM/MISO
are absent from `STATE_CARBON_PRICE_BY_ISO` (only CAISO/NYISO/NEISO have a
program) and the backcast config sets `carbon_price=0`, so `resolve_carbon_price`
returns 0 and the term is identically zero → `mc`, dispatch `P[g,t]`, energy-
balance duals (prices), and all generation are byte-identical whatever basis
books `emission_rate_co2`. `nox_price=0` everywhere too (NOx/SO2 reporting-only).
Concretely: each probe's full dispatch payload was verified byte-identical to
the keeper (base64 blobs diffed identical, 1.17M/1.45M/0.91M chars) before the
committed `runs/<id>.js` was compacted to a CO2/fuelmix registration payload
(per-plant hourly heatmaps dropped — identical to the keeper's — to push via
the GitHub API). This is exactly the R2
carbon-zero "re-score = provable no-op" pattern (`co2-keeper-regate-2026-07-05.md`).

**The v2 re-score moves only CO2 accounting.** Persisted per-plant model
generation (ERCOT: bundle `plant_hourly_fit.model_gwh`; PJM/MISO: the committed
dashboard payload `m_ann`, since no PJM/MISO bundle persists
`plant_hourly_fit` — §9.5) re-scored through the v2 **backcast** rate map
(`emission_rates.measured_plant_rates`, `mode="backcast"`: each plant's own
target-year gen-weighted CEMS intensity, tonnes/MWh net):

| ISO | coverage % (23/24/25) | v2 model CO2 Mt (23/24/25) | matched-subset v2 vs eGRID rate Δ% |
|---|---|---|---|
| ERCOT | 100 / 100 / 100 | 159.7 / 156.3 / 159.6 | −0.04 / −0.50 / +0.55 |
| PJM | 97.4 / 97.5 / 97.6 | 268.7 / 273.1 / 304.3 | +2.49 / +2.09 / +1.56 |
| MISO | 90.2 / 91.1 / 93.5 | 235.6 / 231.8 / 269.1 | −0.53 / −2.65 / −3.30 |

- **Coverage** is the headline improvement: for PJM/MISO these are the ISO's
  **first** measured plant-specific CO2 rates (the legacy
  `plant_emission_rates.parquet` is TX-only — pre-v2 every non-ERCOT plant
  booked the generic `heat_rate × FUEL_CO2_FACTOR` default). For ERCOT the v2
  unit-composition mask dissolves the W A Parish mixed coal+gas exclusion → 100%.
- **matched-subset rate Δ%** (v2 vs `egrid.fossil_co2_rate_map` on the *same*
  plants and generation) isolates the pure rate basis: small everywhere (≤3.3%)
  → v2 reproduces the measured CO2 level, no distortion (rule #13). The larger
  raw MISO total gap is the ~7-10% not-yet-CEMS-covered generation, not a rate
  error. Corroboration: the repo's own no-solve scorer
  `score_backcast_shape_emissions.py` gives ERCOT v2 CO2 **9/9 PASS** vs
  CAMPD-actual (160.9/158.3/160.2 model vs 155.9/155.6/157.7).

**The dashboard C5a CO2 verdict is unchanged.** `render_calibration_html.build_payload`
scores model class-TWh × `egrid.fossil_co2_rate_map` (eGRID + CAMPD-v1) class
intensity — it never reads `plant_emission_rates_v2` — so flipping the flag
moves no committed C5a number for a carbon-zero ISO. These probes are diagnostics
of the v2 accounting coverage/level, not verdict changes; `keepers.json` is
untouched.

**Governance.** No LP solve; no keeper bundle, `keepers.json`, or `src/market_sim`
code modified — only new probe artifacts (registry sidecars, `runs/<id>.js`,
`results/calibration/*_v2rescore/` notes, this log entry). No parameter tuned to
any residual (rules #1/#23). Holdouts **2022/H1-2026 untouched** (rule #22): the
v2 artifact carries no 2022/2026 rows and only 2023-2025 were read; D-6 holdout
quarantine reports "no registered bundle carries a year outside [2023,2024,2025]
— quarantine intact" with the three new probes included. (The D-2 forced-energy
recompute FAIL seen locally is on the caiso-51/pjm-77 **keeper** bundles — a
committed-json-vs-floors-rebuild staleness this lane does not touch, present on
main independent of this change.) Bundles: `results/calibration/ercot32_v2rescore`,
`pjm77_v2rescore`, `MISO/miso41_v2rescore`.

## 2026-07-06 — G-04: E7 staleness adjudication (owner decision)

**Gap:** G-04 (`docs/gap-register-2026-07.md` §3.1). **Source:**
`docs/handoffs/e7-staleness-memo-2026-07.md`, promoted from DRAFT to
owner-decided.

`scripts/audit_keepers.py` E7 (WARN-only, never a FAIL) flags a keeper when a
newer-dated run exists in the registry for the same ISO — a truth-in-labeling
prompt, not a correctness gate. Four keepers carried a standing E7 WARN
against a newer same-ISO run. Owner adjudication, per ISO:

- **ERCOT** (`2026-07-03-ercot32-ordc-total-rtolcap`) — **KEEP.** Newer run
  `2026-07-05-ercot40-rtolcap-forward` is a WS-A forward-supply-cap probe
  (P1-only): the ercot32 recipe with `ercot_reserve_supply_forward=True`,
  swapping the measured RTOLCAP cap for the WS-A forward-formula cap to
  validate the forecast analogue. It isolates one forecast-path delta and was
  never a backcast keeper candidate.
- **CAISO** (`2026-07-03-caiso-51-firm-base`) — **KEEP.** Newer run
  `2026-07-05-caiso-statmode-d7-r2` is a D-7 statistical-mode A/B probe
  (byte-faithful keeper replay with every per-hour/per-year overlay off); its
  own registry text states "Probe only — not a keeper, per CLAUDE.md #1/#13."
- **PJM** (`2026-07-05-pjm-77-ct-relfloor`) — **KEEP.** Newer run
  `2026-07-05-pjm-78-demand-regate` is a demand-repair re-gate probe (PR
  #1426); its own text reads "(PROBE, not a keeper swap)", and its Twin A
  reproduces the pjm-77 verdict criterion-for-criterion (NOT-YET, identical
  FAIL/PASS pattern).
- **NEISO** (`2026-07-05-neiso-48-ct-floor`) — **KEEP.** Newer run
  `2026-07-05-neiso-48-head-regate` is the HEAD-reproducibility probe from
  the 2026-07-06 "ERCOT + NEISO keeper HEAD re-gate" entry above: every
  scored `model` value is byte-identical between the committed keeper and a
  fresh HEAD replay, determination unchanged (NOT-YET in both) — a lateral
  confirmation, not an improvement, and never registered as a keeper
  candidate.
- **NYISO** (`2026-07-03-nyiso-41-hub-prices`) — **PROMOTE, in flight —
  mechanics owned by L-11.** Unlike the other three flagged pairs, the newer
  run generating today's warning (`2026-07-05-nyiso-statmode-d7-r2`, itself
  just a D-7 statistical-mode probe) is not the promotion candidate. NYISO's
  L-11 lane (`docs/gap-register-2026-07.md` Wave-3: G-13, #1344, #1345 —
  LI/NYC delivered-gas + Iroquois Z2 floor re-derivation) is actively
  developing a structurally-more-faithful NYISO bundle expected to replace
  `nyiso-41-hub-prices` as keeper once solved and registered with its
  required ablation twin (CLAUDE.md rule 20). This lane makes **no** keeper
  swap, no `keepers.json` edit, and runs no NYISO solve — that mechanic
  belongs exclusively to L-11.

**No keeper swap made in this lane; `keepers.json` is unchanged.**
`scripts/audit_keepers.py` gains an `E7_STALENESS_ADJUDICATED` annotation
(same pattern as the `E9_ABLATION_TWIN_GRANDFATHER` list) so the three
KEEP-adjudicated pairs above (ERCOT, CAISO, PJM) render their E7 WARN with an
added "E7: adjudicated 2026-07-06, see calibration-log" pointer — the WARN
itself is never suppressed, only annotated. NYISO's pair is deliberately left
un-annotated (it is adjudicated PROMOTE-pending, not KEEP), so its warning
keeps reading as an open item until L-11 lands the swap. A keeper/newer-run
pair not in the annotation dict — including any run registered after
2026-07-06 — gets the plain, unadjudicated warning, since it has not itself
been reviewed.

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule #22). No LP solve was
run to produce this adjudication — every judgment above is drawn from each
run's own already-committed `run_config.json` / registry `definition` prose.

## 2026-07-06 — G-04 round 2: E7 re-adjudication after the day's keeper swaps + new probes (owner decision)

Since round 1 (above), four keepers swapped (ERCOT→`ercot34-stage4-overlay-off`,
NEISO→`neiso-49-stgas-netload`, NYISO→`nyiso-53-li-tsl`,
MISO→`2026-07-06-miso-42-coal-econ-ablation`) and a fresh batch of probes
registered, so E7 now flags a **new** `(keeper, newest-run)` pair per ISO — the
round-1 dict entries reference superseded keepers/probes and no longer match any
live warning. Owner affirmed in-session: **current keepers are correct;
adjudicate the standing E7 warnings KEEP.** Each newer run is a diagnostic
probe by its own registry `definition`, never a keeper candidate:

- **ERCOT** `2026-07-06-ercot34-stage4-overlay-off` — **KEEP.** Newer
  `2026-07-06-ercot37-g22-surface-on` is self-labeled **"(PROBE — REJECTED)"**
  (G-22 condition-responsive CT/peaker offer-surface A/B).
- **CAISO** `2026-07-03-caiso-51-firm-base` — **KEEP.** Newer
  `2026-07-06-caiso51-statmode-v2` is a **D-7 statistical-mode A/B probe**
  (byte-faithful keeper replay, all per-hour overlays off).
- **PJM** `2026-07-05-pjm-77-ct-relfloor` — **KEEP.** Newer
  `2026-07-06-pjm-82-commitment-posture` is a **commitment-posture A/B probe**
  (posture lever ported from MISO §A); keeper stays pjm-77.
- **NEISO** `2026-07-06-neiso-49-stgas-netload` — **KEEP.** Newer
  `2026-07-06-neiso-wfuelsec-ab-v2off` is a **winter-fuel attribution twin
  (PROBE)** isolating the mechanism from the v2 emission-rate flip.
- **MISO** `2026-07-06-miso-42-coal-econ-ablation` — **KEEP.** Newer
  `2026-07-06-miso-43-commitment-posture` is self-labeled
  **"(PROBE - honesty gate FAIL, lever stays default-off)"**. (Note: this MISO
  keeper is itself the zero-forcing ablation twin of `miso-42-coal-econ`, per the
  same-day keeper flip; its E9 twin-of-record is the forced base run.)

`E7_STALENESS_ADJUDICATED` is replaced with these five current pairs (dated
2026-07-06); the round-1 pairs are dropped as dead keys (git history preserves
them). As before, the annotation never suppresses the WARN — it appends the
"adjudicated 2026-07-06, see calibration-log" pointer; a pair registered later
gets the plain warning until reviewed.

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule #22). No LP solve was run;
every judgment is drawn from each run's already-committed registry `definition`.

## 2026-07-06 — ERCOT keeper PROMOTED: `ercot34-stage4-overlay-off` replaces `ercot32-ordc-total-rtolcap` (owner sign-off in-session)

Owner approved the recommendation in the entry above. Promotion bookkeeping
(rule 21 / skill step 4):

- **`keepers.json`** ERCOT → `2026-07-06-ercot34-stage4-overlay-off`.
- **C6 attestation** written (`calibration_attestation.json`): governance
  assertions with the stage-4 note; DOF ledger **inherited verbatim from
  ercot32 (no scalar re-tuned)** plus two appended entries — the WS-A forward
  supply coefficients (identification: measured RTOLCAP/RTOFFCAP MW
  quantities, rule 23) and `ercot_west_gas_delivered_floor=0.4`
  (measured-physical transport-bound floor, surfaced into the ledger by the
  G-12 finding). Exceptions: C2-2025 gas −5.0% (preliminary-923 vintage,
  inherited) and C5c-2024 r=0.422 (19% EIA-930 battery coverage, improved
  from ercot32's 0.331). C3b/C3c/C8 stay MODEL MISS — named root causes, not
  excused.
- **Zero-forcing ablation twin** (D-3/E9): exact ercot34 config (all five
  un-persisted `--set` fields re-applied) with every merchant floor/bridge
  off; registered as `2026-07-06-ercot34-stage4-overlay-off-ablation` and
  linked from the keeper sidecar with the market story. Keeper-vs-twin
  per-class deltas quantified in the sidecar link.
- **E9 grandfather list**: `ercot32` entry removed (dead once demoted, per
  the list's contract).
- **REPLAY CONTRACT CAVEAT (standing until the meta-writer fix lands):**
  ercot34's `meta.json` — like ercot32's — does not persist
  `ercot_zonal_gas_basis` / `ercot_west_netload_gas_shape` /
  `ercot_west_gas_delivered_floor` / `oil_primary_bin_fuel` /
  `ercot_reserve_supply_forward`; any replay/re-gate of this keeper must
  restore them via `--set` from the bundle's `run_config.json` (they are all
  resolved there). The durable fix is owned by the orchestrator-unification
  lane (`run_calibration_full.py` meta writer).
- `build_status.py` re-run; `audit_keepers.py --check` + keeper-auditor pass
  recorded below in this entry's session.

The retired `ercot32` stays registered (the prior-keeper comparison) with its
DAM-AS overlay demoted to the explicitly-labelled F6/F7 diagnostic (plan §6:
default-off in keepers, retained for the decomposition).

## 2026-07-06 — MISO L-14 continuation: miso-42 twin completed + commitment-posture lever BUILT and honesty-gate REJECTED (probe `miso-43`; keeper stays miso-41, miso-42 promotion recommendation stands)

**Lane:** L-14 continuation (session after Wave-3 PRs #1468/#1472/#1481/#1486). Three deliverables.

### 1. miso-42 ablation twin: completed, registered, linked (rule 21 closed)

The Wave-3 session died mid-twin (PR #1486 checkpoint; outputs lost with the container). Re-solved
from scratch on HEAD `ac11191` (full span, sequential, fresh 12 GB swapfile), registered as
**`2026-07-06-miso-42-coal-econ-ablation`** and linked from the base sidecar with the market story —
making the miso-42 attestation's twin claim true. **Finding:** the twin deltas are SMALL (every class
within ~7% / 1.9 TWh; imports +1.9/+1.2/+0.9 TWh) — under `coal_econ_srmc_bound` the merchant floors
barely force energy, in sharp contrast to the miso-41 twin (ST_GAS +63–115%, OTHER_FOSSIL 100%
floor-forced). The offer bound, not the floor stack, now carries the mid-merit price floor; the
floors' role collapses toward commitment scaffolding. This strengthens the pending miso-42 promotion
recommendation (strictly less floor-dependence). Provenance amendment documented in the twin's
`run_config.json` (the auto-captured diff snapshot had picked up this session's unrelated posture
edits made after the solve's imports resolved).

### 2. Honesty-gate data ask LANDED: measured MISO ASM series intaken (`data/raw/MISO-AS`)

The diagnosis-§5 blocking data ask is closed: `scripts/fetch_miso_asm.py` stages MISO's daily market
reports — zonal DA ex-ante / RT final reserve MCPs (zone-level dedupe) and hourly REGIONAL cleared
reserve MW by product (reg/spin/supp/STR, aggregated from the masked `asm_rt_co` cleared-offers
zips) — 2023–2025 complete, zero missing days, ~2.8 MB parquet (PJM-AS staging precedent).
`scripts/report_miso_posture_gate.py` scores any posture bundle on level + event-day direction
against it. The §B Midwest-family ask (historical zonal operating-reserve REQUIREMENT series)
remains open — MCPs/cleared MW alone do not give the requirement basis.

### 3. Commitment-posture lever A: BUILT (miso_commitment_posture), solved full-span, gate FAIL → PROBE

Design note §A built exactly as specified (zero fitted parameters): per non-fast-start
(zone × fuel-class) pergen pool, continuous online capacity `U[p,t]` with joint `ΣP + R ≤ U`,
CEMS-measured min-load coupling `ΣP ≥ mlf·U`, cyclic NREL-class startup charge on `ΔU⁺`, and the
pergen reserve cap online-gated `R ≤ ρ(t)·U`. Rule-18 physics gate postures 18 of 30 pools
(CT/oil fast-start exempt; mlf 0.12–0.58 cap-weighted `thermal_tranches` committed_pct with
WWSIS-2 gap-fill; startup $44–100/MW). Not a floor: no `min_gen`, no D-2 mechanism id; the trivial
LP tests prove zero forced energy with the requirement neutralized (`tests/test_commitment_posture.py`,
9 tests; dispatch/reserve suites 64+112 green). Min-run/min-down window rows deliberately deferred
(G-40 memory; the startup charge carries the cycling economics).

Full-span solve registered: **`2026-07-06-miso-43-commitment-posture`** (bundle
`results/calibration/MISO/miso_43_commitment_posture`), determination NOT-YET, **rejected probe by
its own pre-committed honesty gate** (`SUMMARY-posture-gate.md`):

- **Level FAIL:** modeled postured online headroom 9.9–11.1 GW vs measured cleared reserve
  2.5–2.7 GW (3.7–4.2×) — at $2.19–3.52 gas, min-load burn is always cheaper than the $200 curve
  step, so the LINEAR relaxation holds ~10 GW online and the real market's leaner posture never forms.
- **Direction PARTIAL:** daily r(model reserve price, measured Miso-Wide spin MCP) = 0.00/0.20/0.31;
  top-20 measured event days same-direction 19/19/15 of 20; regional split over-weights South
  (34–38% of online headroom vs measured 13–18% of cleared MW; model Central under-weighted).
- **Structure moved, fit did not:** reserve duals fire 637/700/470 h/yr (miso-39: 59/64/207) with
  real cycling charges paid (startups 102/107/139 GW/yr), but the $200 step never engages — C3c
  tail stays 0 h ×3 — and the C1 CC row is UNCHANGED (+0.8/+0.5/+0.3 TWh vs miso-42; imports
  −2.1/−1.2/−0.9 TWh slightly worse). The pooled linear relaxation captures only a small part of
  the DP-1 +34% MIP wedge: with U costless while `P ≥ mlf·U` is satisfied by flat-baseload CC, the
  posture adds min-load energy at the margin instead of removing committed CC energy.

**Disposition (rules 1/13/15):** the mechanism is real market structure and stays in the codebase
GATED default-off; the flag does NOT enter any keeper recipe until a build passes its measured-series
gate. Named follow-ups, in order: (a) min-run/min-down rolling-window rows on U (the deferred
smoothing — the twin lever the linear relaxation is missing), (b) the §B Midwest zonal family
(still DATA-BLOCKED on the requirement series), (c) posture grain below (zone × class) where memory
allows. The C1 CC row remains owned by the commitment-posture workstream, with this probe as the
measured evidence that the pooled LINEAR form is insufficient — the next step is the window rows,
not a tuned tightening (no parameter in this build may be moved against the residual).

### keepers.json

Unchanged: keeper `2026-07-05-miso-41-ct-evening`; the Wave-3 recommendation to promote miso-42
stands (now with its rule-21 twin registered and the floors shown near-redundant under the bound).
Dashboard pruned to the 15-run cap (miso-29/30/31 dropped).

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule 22). All solves 2023–2025, one invocation,
years sequential (12 GB swapfile, MALLOC_ARENA_MAX=1, MARKET_SIM_HIGHS_THREADS=1); no golden
capture (documented OOM).

## 2026-07-06 — MISO merchant-floor root-cause: miso-44 (wefor_multiplier neutralized), keeper promoted

**Lane:** MISO merchant-floors root-cause session (owner direction: the miso-42 ablation twin scores
better than its floored base — root-cause the floors per rule 1).

### Root-cause finding

The miso-42 ablation twin's score advantage does NOT come from the reliability floors — it comes from
`wefor_multiplier` being neutralized from 0.7 to 1.0 in the zero-forcing ablation. Evidence:

1. All 4 reliability floor limbs force a TOTAL of <0.6 TWh/year (<0.35% of any class).
2. The ablation twin shows dispatch changes of several TWh (2–7% of class totals).
3. The only other variable changed in the ablation is `wefor_multiplier` (0.7→1.0).
4. `wefor_multiplier` scales THERMAL EFOR (not wind, despite the audit C-15 "wind EFOR haircut"
   label). At 0.7, all thermal plants have 30% lower forced-outage rates → higher availability.
   At 1.0, CC (the cheapest, most over-running class) dispatches less → CT/ST/imports recover.

### Per-floor assessment (all 4 KEPT)

All 4 enabled MISO reliability floor limbs pass rules 13/17 (driver, window, forward story):

1. **MISO-Indiana CT_PEAKER evening [15,21):** tmax>32.2°C, evening ramp (not overnight), 0.07–0.32%.
2. **MISO-Indiana COAL tmax:** tmax>32.2°C, coal commitment inertia on hot days, 0.10–0.32%.
3. **MISO-South COAL tmax:** tmax>35.95°C, same pattern, negligible forcing.
4. **MISO-Plains ST_GAS tmax:** tmax>33.35°C, floor_pct=6.2%, 0.12–0.42%.

### miso-44: wefor_multiplier neutralized (DOF reduction)

Registered: **`2026-07-06-miso-44-wefor-neutral`** (bundle `results/calibration/MISO/miso_44_wefor_neutral`).
Config = miso-42 recipe + `wefor_multiplier=1.0` (MISO-only; other ISOs retain 0.7 pending their own
investigations). This is a DOF REDUCTION: 6 residual-identified entries vs miso-42's 7.

**Score vs miso-41 keeper:**

| Criterion | miso-41 | miso-44 | Delta |
|---|---|---|---|
| fuelmix | 10/24 | **12/24** | **+2** (CT_PEAKER 2023/24 recovered) |
| sysvol | 5/6 | 4/6 | −1 (coal 2025 +14.7% vs +8.8%) |
| price_mean | 0/6 | **1/6** | **+1** (2024 recovered) |
| price_shape | 1/3 FAIL | **2/3 CAVEAT** | **+1** |
| price_tail | 1/6 | 1/6 | = |
| dispatch_corr | 6/6 PASS | 6/6 PASS | = |
| co2 | 3/3 PASS | 3/3 PASS | = |
| storage | FAIL | **CAVEAT** | upgraded |
| governance | UNATTESTED | **PASS** | upgraded |
| shape (D-1) | PASS | PASS | = |
| forced_share (D-2) | PASS | PASS | = |

Key: CC_REGULAR over-run halved (+44/+43 TWh → +20/+19 TWh). The coal 2025 regression is the known
commitment-posture artifact (reduced CC availability shifts marginal load to coal). Legitimacy
diagnostics Overall PASS (D-1/D-2/D-4/D-5/D-9/D-10).

### Keeper promotion

**Keeper: `2026-07-06-miso-44-wefor-neutral`** (was `2026-07-05-miso-41-ct-evening`).

Promotion rationale (rule 1): strictly more structurally faithful — one fewer residual-identified DOF
(the physically baseless wefor haircut removed), all structurally sound reliability floors retained,
material score improvements on fuel mix and prices. The sysvol coal 2025 regression is a known
commitment-posture artifact on a preliminary-vintage actual and does not override the structural gain.

### backcast_config.py change

`wefor_multiplier` set to `(1.0 if iso.upper() == "MISO" else 0.7)` at line 1110 — MISO-only
neutralization; other ISOs retain 0.7 pending their own root-cause investigations.

### Holdouts

No solve, score, or intake touched 2022/H1-2026 (rule 22). All solves 2023–2025, one invocation,
years sequential (12 GB swap, MALLOC_ARENA_MAX=1, MARKET_SIM_HIGHS_THREADS=1).
