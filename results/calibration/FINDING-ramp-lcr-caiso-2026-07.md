# FINDING — ramp-envelope + LCR structure does not lift CAISO evening CT through merit (2026-07)

**Thread:** phase-1 implementation of the ramp-rate + locational design
(`docs/ramp-locational-design-2026-07.md`), targeting the evening-CT-merit gap
established in `FINDING-caiso-evening-merit-2026-07-04.md`.

**Verdict:** the two mechanisms are implemented, gated, forecast-parity, tested
and cheap — but on the CAISO fleet they **do not lift evening CT dispatch
through merit**. The ramp constraint is near-inert (binds ~1.6 % of CC
transitions; +2 MW evening CT) because the CC fleet has enough *aggregate* ramp
to follow the evening net-load ramp; the LCR gives a small legitimate lift
(+39 MW) but its pockets are mostly served by in-area CC. Evening CT lands at
243 MW (drag-off merit + LCR) vs the drag's 627 and actual ~770.

**The load-bearing result is the D-2 legitimacy contrast:** the drag reaches
its CT level by **forcing 65-76 % of CT energy at the floor (D-2 FAIL,
rule #19)**, while ramp+LCR force 0.5-1.5 % (D-2 PASS). The drag's level is not
merit — so the task's "CT through merit" goal is unreachable by ramp/LCR *or*
by the drag. Registered as a **rejected probe**
(`2026-07-04-caiso-ramplcr-probe-rejected`); `ct_netload_drag` is **not**
retired (nothing legitimately replaces its level) but is flagged as a
rule-19-strained scaffold. Mechanisms stay gated default-off — ramp
deprioritized (inert), LCR kept as the promising locational home once CC is
repriced.

## What was built (phase 1)

- `_build_ramp_rows` (`model/dispatch.py`): two-sided plant-group hourly ramp
  rows, `|ΣP[g,t] − ΣP[g,t−1]| ≤ RU/RD_eff`, availability-edge widening;
  `ScenarioConfig.ramp_limits`. Envelopes = CAMPD max observed 1-h plant
  gross-load delta (`scripts/derive_campd_ramp_envelopes.py`; 30 well-observed
  CAISO CC plants, CC up-envelope median 0.49× pmax).
- `_build_local_capacity_rows`: per published-LCR-area `ΣP_area ≥ share·zone_load
  − import_cap` (uplift-not-price dual; thermal-only feasibility cap);
  `ScenarioConfig.local_capacity_constraints`. Inputs = CAISO LCT-report
  `peak_load`/`requirement` + NQC-list membership.
- Both in the shared builder (forecast parity), gated default-off, 17 tests,
  flag-off byte-identity. Solve cost: **P0 cold 103 s / P1 warm 27 s** (vs
  ~120-160 s / 15-30 s baseline) — no runtime penalty (design 3× abort not
  approached).

## Why it doesn't lift CT (the diagnostic)

**Ramp is inert.** On CAISO 2024 (arm Y), the CC plant-hour dispatch hits its
measured envelope in only **1.6 %** of transitions (2.2 % within 80 %). The CC
fleet backs down to 5.4 GW midday and ramps to 9.5 GW in the evening on its own
— the ~4 GW evening ramp spread across ~20 CC plants is ~200 MW/h each, far
under their ~250-550 MW/h envelopes. CC *can* chase the ramp, stays cheapest,
so CT does not clear.

CC_REGULAR diurnal (arm Y, 2024, mean MW/h): midday 11-14 = 5,416 CC / 54 CT;
evening 18-20 = 9,536 CC / 205 CT; overnight 1-4 = 8,833 CC / 18 CT.

**LCR binds but is mostly CC-served.** LA Basin LCR binds 54 h/yr in 2024 (428
h in 2023, requirement 7,529 MW), San Diego-IV ~5,000-8,700 h/yr (2 GW import
cap) — but both pockets carry large in-area CC (Alamitos/Huntington/El Segundo),
so most forced local generation clears as CC, not CT.

## 3-year A/B (P1 evening h15-21 CT_PEAKER, mean MW)

Arms on the caiso-51 + Lever-A/B recipe, `--year 2023 2024 2025`:

| arm | evening CT | vs scrub S | per-year 2023 / 2024 / 2025 |
|---|---|---|---|
| **W** drag ON (status quo) | **627** | — | 857 / 599 / 425 |
| **S** scrub, drag OFF, no mechanism | 202 | (baseline) | 394 / 147 / 67 |
| **X** ramp only, drag OFF | 204 | **+2** | 396 / 147 / 67 |
| **Y** ramp+LCR, drag OFF | 243 | **+41** | 476 / 162 / 92 |

Reference (CAMPD 2024 CT_PEAKER subset, prior FINDING): evening ~770 MW.
X isolates ramp (**+2**), so LCR-only ≈ Y − X = **+39** (a dedicated arm Z
reproduces this; it OOM-killed under concurrency and is re-solved for the
dashboard bundle). CC_REGULAR evening is ~8,200 MW in **every** drag-off arm —
the mechanisms do not displace CC; CC ~66-67 TWh/yr and imports ~31 TWh/yr are
flat across arms.

**Attribution.** Ramp = +2 MW (inert, confirms the 1.6 %-binding diagnostic;
the FINDING's "slow CC can't chase the ramp" premise is *not supported* at
fleet-aggregate resolution). LCR = +39 MW (small but real, concentrated in the
high-requirement 2023, +77 MW). Combined = 243, still 384 short of the drag and
527 short of actual.

## The legitimacy contrast (D-2 forced-energy) — the real headline

`legitimacy_diagnostics --only D2` on the two ends:

| arm | CT_PEAKER forced share (2023/24/25) | D-2 |
|---|---|---|
| **W** drag ON | **65 % / 76 % / 75 %** (`ct_netload_drag` floor) | **FAIL** (≫ 10 % peaker budget) |
| **Y** ramp+LCR, drag OFF | 0.5 % / 1.5 % / 0.02 % | **PASS** |

The drag reaches the right CT *level* (627, near actual 770) **illegitimately**
— it forces **65-76 % of CT energy at the floor** (rule #19: "floors are
commitment scaffolding, not the dispatch model"; "a keeper fails if a peaker
class dispatches > 10 % of its energy at binding floors"). The floor *is* the
CT dispatch. Ramp+LCR are the legitimate opposite (0.5-1.5 % forced, pure merit
plus a published-LCR lift) but that legitimacy supports only 243 MW, because
the merit order (too-cheap CC, cheap Lever-B imports) cannot carry more CT.
**The task's goal — CT toward actual *through merit* — is not reachable by
ramp/LCR; the level the drag reaches is not itself merit.**

## Decision (design §5)

§5 criterion (i) — CT rises toward actual through merit — **fails** (Y 243 ≪
drag 627 ≪ actual 770). Criterion (iii) — D-2 forced share below the drag arm —
**passes decisively** (0.5-1.5 % vs 65-76 %). So:

- **`ct_netload_drag` is NOT retired** — nothing legitimately replaces its CT
  *level*. But the drag's level is 65-76 % floor-forced; it stays a **known
  rule-19-strained scaffold**, not a solved mechanism.
- **Ramp: gated default-off, deprioritized** — inert for CAISO (+2 MW / 1.6 %
  binding); structurally correct (rule #1), may bind for other ISOs (PJM
  winter, ERCOT) or steeper future years. Do **not** tighten the envelope to
  force binding — that would forbid observed moves (rule #13).
- **LCR: gated default-off, the more promising** — a small *real, legitimate*
  locational lift (+39 MW, up to +77 in the high-requirement 2023), grounded in
  published CAISO LCR studies. It is the correct home for the locational
  commitment the drag currently fakes, and should grow more useful once CC is
  repriced (a short pocket forced to run local capacity clears CT once CC is no
  longer the universal cheapest option).

**Open root cause (sharpened):** the CT-merit deficit is **not** aggregate-ramp
driven. It is (a) CC over-supply — CC too cheap, so it covers the evening ramp
and the LCR pockets alike (Lever A raised the committed band but CC stays
cheapest; Lever B added cheap imports that push CT down further), and (b)
genuine **sub-plant** locational/commitment granularity below the LCR-area
resolution. Closing it through merit needs CC repricing + a finer locational cut
(LA-basin zone split or bus-level LCR) or relaxed-commitment P1 — the phase-3
build, not a floor (rule #1).

## Files
- `results/calibration/caiso_rampLCR_probe/` — registered probe bundle (slim);
  dashboard id `2026-07-04-caiso-ramplcr-probe-rejected` (payload generated
  locally; not pushed due to the git-relay size limit).
- `scripts/derive_campd_ramp_envelopes.py`, `scripts/derive_lcr_membership.py`,
  `src/market_sim/data/local_capacity.py`, `model/dispatch._build_ramp_rows` /
  `_build_local_capacity_rows`, `data/fleet.build_ramp_groups`.

## Handoff note (branch push state)

The git relay 413s on every push (even empty commits); `mcp__github__push_files`
is the only working path. This branch carries the finding, `local_capacity.py`
and `derive_campd_ramp_envelopes.py`. The remaining phase-1 code (the LP rows in
`dispatch.py`, `fleet.build_ramp_groups`, the two `ScenarioConfig` flags, the
runner/run_calibration/run_calibration_full wiring, the `--ct-netload-drag`
toggle, and the two test files) is fully specified by the design doc
(`docs/ramp-locational-design-2026-07.md`, in main) plus this finding and
`local_capacity.py`; a follow-on session re-applies them via `push_files`.
