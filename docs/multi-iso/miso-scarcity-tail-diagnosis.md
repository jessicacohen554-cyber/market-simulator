# MISO scarcity tail (>$200) — root cause, event anatomy, and the deliverability mechanism

**Date:** 2026-07-02. **Session:** `claude/miso-scarcity-tail-8q5k84`.
**Starting point:** keeper `2026-07-02-miso-38-zonal-reserves`, gate 4 PARTIAL —
the MISO-South zonal ORDC family fires (dual nonzero 266/287/875 h) but only at
re-dispatch opportunity cost ($8–21/MWh); the >$200 tail stays 0 h vs actual
30/37/88 (2023/24/25). This doc records the design-first evaluation the scope
doc's gate-4 note called for: WHAT the actual tail hours are, WHY a
perfect-foresight LP misses them, WHICH real mechanism closes the reachable
part, and what remains out of representation. Zero parameters fitted to the
residual (CLAUDE.md #1/#10).

## 1. Anatomy of the actual tail (the 30/37/88)

Source: `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
(D6 hub actuals). The benchmark tail counts are **Indiana Hub RT** hours >$200.
Decomposition:

| year | RT h >$200 | consecutive-run lengths | DA >$200 in those RT hours | DA median in those hours | DA tail total (h >$200) |
|---|---|---|---|---|---|
| 2023 | 30 | 30×1h (all isolated) | 0 | $40 | **1** |
| 2024 | 37 | 35×1h, 1×2h | 1 | $49 | **24** |
| 2025 | 88 | 52×1h + runs up to 10h | 19 | $100 | **38** |

- **2023's entire tail is single-hour RT transients** at morning/evening ramp
  hours (hod 6–9 / 16–21), scattered over 26 days across all seasons. In the
  same hours the day-ahead market — which has unit commitment, ramp modeling
  and a full network — priced a median of $40 and never crossed $200. These
  are 5-minute-market events (ramp scarcity inside the hour, net-load forecast
  misses, RT re-dispatch) averaged up to an hour.
- **2024's DA tail (24 h) is Winter Storm Heather, Jan 14–17** — a Midwest
  cold event — and is almost disjoint from its RT tail (1 shared hour): DA
  committed conservatively and RT rarely re-spiked.
- **2025 is the first year with genuine multi-hour scarcity blocks** visible
  in both markets: Jan 20–22 (winter storm), Feb 20–21, Jun 23–24 and
  Jul 24/28–29 (heat waves), where DA reached $203–433 and RT $200–1,783.

**Representation bound (deterministic perfect-foresight hourly LP ≈ DA):** the
reachable structural target is the DA-visible scarcity — order 1/24/38 h —
plus the fraction of RT-only hours whose *physical* tightness an hourly model
can see. Reproducing all 30/37/88 would require modeling forecast error and
sub-hourly re-dispatch, which is outside this model's representation; a
mechanism tuned to hit those counts would fail the rule-#10 admissibility test.

## 2. Why the miso-38 LP never prices the curve (quantified)

Bind-gate probe (`scripts/probes/_miso_scarcity_bindgate.py`, no LP re-solve):
reconstructs the keeper fleet (CAMPD outage overlay, summer derates) against
the keeper-repro dispatch (`results/calibration/MISO/_diag_miso38_base`,
faithful to the registered keeper to $0.01), and measures reserve supply three
ways against the LP's own requirements (market-wide RBDC 4,353 MW; South zonal
3,953 MW):

| family / measure (MW) | 2023 min / h<req | 2024 min / h<req | 2025 min / h<req |
|---|---|---|---|
| market-wide: aggregate headroom | 17,313 / 0 | 11,390 / 0 | 12,435 / 0 |
| market-wide: ramp-deliverable (re-dispatch max) | 17,313 / 0 | 11,390 / 0 | 12,435 / 0 |
| South: aggregate headroom | 3,953 / 0 | 3,953 / 0 | 3,953 / 0 |
| South: ramp-deliverable, as-dispatched | 3,487 / **59** | 3,210 / **63** | 3,257 / **207** |
| South: ramp-deliverable, re-dispatch max | 3,953 / **38** | 3,953 / **41** | 3,953 / **124** |

- **Market-wide RBDC can never carry the tail**: deliverable reserve stays
  ≥11 GW against a 4.4 GW requirement in every hour of every year, including
  every actual event hour. (Same conclusion as PJM's pjm-62 empirical re-gate:
  a system-wide requirement on a perfect-foresight fleet is structurally
  slack.)
- **The South aggregate headroom pins EXACTLY at the requirement** (min =
  3,953.0 in all years) — the LP holds the zonal balance at equality and
  prices the opportunity cost; it can always re-dispatch/import its way back
  to the requirement, so the shortfall steps never engage. That is the
  perfect-foresight-headroom diagnosis of miso-38, now measured.
- **10-minute deliverability is what breaks the equality.** Capping each
  (zone, fuel-class) pool's reserve at its availability-scaled 10-minute ramp
  (`Σ ramp10 × avail`; NREL/TP-5500-55588 class ramp rates: coal 0.15,
  CC 0.40, CT/oil 1.00, gas-ST 0.20 of capacity) puts South deliverable
  reserve BELOW the zonal requirement in 38–207 h/yr — and those hours
  coincide with the actual events: in 2025, 27/88 of the actual RT-tail hours
  and **28/38 of the actual DA-tail hours** fall in the as-dispatched
  deliverable-short set. Shortfall depths (up to ~700 MW vs the 791 MW first
  step) price at the published $200 step, occasionally deeper.

### Timing coincidence, checked per candidate (the design-first questions)

1. **Ramp/response-time limits on reserve delivery — CONFIRMED as the binding
   mechanism** for the South leg (table above). Class-level pooling
   (columns = zones × fuel-classes ≈ 30/hour) is memory-feasible; per-plant
   pooling at MISO scale is not (miso-reserve-coopt.md memory note).
2. **Outage/derate coincidence — carried, and load-bearing.** The deliverable
   measure is availability-scaled: the CAMPD outage overlay plus the summer CC
   derate is what thins the South pools in exactly the event windows (the
   deliverable-short set concentrates in Jun 23–24 / Jul 28–29 / Jan 21–22
   2025). Thin-but-sufficient in the aggregate view; thin-and-SHORT once
   10-min deliverability is enforced.
3. **P2 commitment screen interaction — not applicable.** The MISO keeper
   lineage runs `commitment_enabled=False`; no P2 pass exists to re-admit
   decommitted capacity. The perfect-commitment posture is itself part of the
   residual (every slow unit's headroom is synchronized-by-assumption), which
   is why market-wide deliverable stays ≥11 GW; that is the PJM "Phase 1
   commitment posture" analogue and stays out of scope here.

## 3. The mechanism (implemented, gated default off)

`ScenarioConfig.miso_reserve_pergen` / CLI `--miso-reserve-pergen`
(`reserve_config._miso_design` pergen branch → the existing
`dispatch._build_reserve_rows_pergen` machinery, the PJM Phase-2 build):

- One reserve column per **(zone, fuel-class) pool** of reserve-eligible
  units with nonzero 10-min ramp (nuclear drops out); ~30 columns/hour at 7
  zones — columns scale with classes × zones, not generators.
- **Joint headroom** per pool-hour: `Σ P + R ≤ Σ pmax·availability` — a MW
  held as reserve cannot clear as energy, so reserve competes with energy at
  the pool margin (the opportunity-cost band the aggregate build already
  priced).
- **Deliverability bound**: `R[pool,t] ≤ Σ ramp10 × availability[g,t]` —
  hourly, so on-outage/derated units contribute no 10-minute ramp
  (`dispatch.build_variable_bounds` now accepts `(n_r, T)` pergen caps).
- Families unchanged: market-wide RBDC + the MISO-South zonal family at the
  published BPM-002 §5.2.1.2 curve. No breakpoint, penalty, or requirement was
  touched.

**Admissibility (rule #10):** ramp10 = published class ramp rates × capacity
(regenerates for any forecast fleet and responds to fleet mix); availability =
the outage overlay (backcast) / forecast availability; requirements =
fleet-derived MSSC quantities. MISO's market design requires contingency
reserve to convert to energy within 10 minutes (BPM-002; Spin + Supplemental,
quick-start counting for Supplemental — the CT/oil 1.00 fraction), so the
bound is the market rule, not a fit. Trivial-case tests first
(`tests/test_reserve_coopt.py::TestMisoPergenReserveLP`): headroom-covered but
ramp-short fleet prices the curve step while the aggregate build clears $0; no
phantom scarcity when ramp is ample; opportunity-cost competition on the
marginal pool.

## 4. What the mechanism does NOT reach (recorded before the solve)

- **2023's tail (all-RT single-hour transients):** essentially none of it is
  DA-visible scarcity; expected model tail contribution O(0–5 h). Matching 30 h
  would be reproducing forecast error the model doesn't represent.
- **2024's Midwest winter-storm DA tail (Jan 14–17, 24 h):** the market-wide
  family stays ≥11 GW deliverable (perfect commitment posture + no Midwest
  locational family). Reaching it needs either the commitment-posture work or
  a Midwest reserve zone with a defensible published requirement — both
  separate workstreams.
- **RT max prices ($585–1,783):** the model's top step is $3,300 (zonal) but
  the depth of actual RT spikes reflects 5-minute dynamics; only the $200–1,100
  band is structurally reachable at hourly resolution.

## 5. Result — miso-39 (`--miso-reserve-pergen` probe)

*(filled after the 3-year solve; bundle
`results/calibration/MISO/miso_39_reserve_pergen`, registered on the dashboard
either way per rules #14/#15.)*
