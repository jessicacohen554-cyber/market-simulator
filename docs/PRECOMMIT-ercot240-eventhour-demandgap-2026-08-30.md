# PRECOMMIT — ercot-240 (2026-08-30): event-hour demand-gap ZERO-SOLVE characterization — root-cause adjudication of the +0.7–0.9 GW EIA-930-vs-model demand gap in the 14 missed-event hours, NO input change, NO lever, NO gate change

**Session ercot-240, designated branch `claude/ercot-240-demand-gap-xbdwn5`.**
Charter: the owner's 2026-08-30 PM charter of
`FINDING-ercot239-missedevents-phase0-2026-08-30.md` §6 **OBJECT 2 ONLY**
(objects 1 and 3 not chartered): the event-hour demand gap — EIA-930 actual
`Demand` minus model demand = **+651…+873 MW in 12 of the 14 missed-event
hours** against a **+98 MW** 2023 year mean (finding §0.5/§4; per-hour rows
in the committed `results/calibration/ercot239_missedevents_phase0.json`).
This is a CHARACTERIZATION round: enumerate candidate root causes BEFORE any
input change — (a) 4CP / load-resource response in the demand source,
(b) the EIA-930-vs-MIS settlement boundary, (c) weather-hour alignment —
and adjudicate WHICH root cause carries the gap, with measurement. Any input
change is a SEPARATE owner-visible round. This precommit is pushed and
blob-verified BEFORE any gap measurement is computed (ercot-239 precedent:
priors declared ex ante, then graded as declared).

Keeper structure resolved fresh at dispatch (unchanged): FORWARD KEEPER
`2026-08-25-234-eastex-identity` (2024–2025) + 2023 CARVE-OUT
`2026-08-25-236-swcap-clip-k33` (bundle `results/calibration/ercot236_k33_clip`).
NEITHER config is touched. ZERO SOLVES, hard. Reads ⊂ {2023} (train span;
the event year and the carve-out config's year). ERCOT surfaces only
(rule 25 `[R-ISO-SCOPE]`). Every comparison is diagnostic; no measured
outcome feeds anything (rule 13 `[R-MEASURED]`); no derive script re-runs
(rule 23 `[R-FROZEN-DERIVE]`).

## 0. Pre-registered structural observation (declared BEFORE measurement; from design reading only)

Two facts were established during pre-measurement design reading — of the
demand-loader source and of the ALREADY-COMMITTED ercot-239 record the
charter directs this session to read — and are declared here so the round's
priors are honest about what was known ex ante:

1. **The model's ERCOT demand construction is `Demand + Total interchange`,
   both read from the same EIA-930 `ERCO hourly` frame**
   (`src/market_sim/data/eia930/demand.py::_load_ercot_hourly` +
   `load_demand`: "a net import lowers what the internal fleet must serve, a
   net export raises it"). The keeper runs `td_loss_factor = 0.0`,
   `priced_interchange = False` (so interchange IS folded in) and
   `ercot_tie_zonal_interchange = True` (zonal PLACEMENT of the same netted
   total — column sums conserved by construction). By the EIA-930 identity
   (Demand = Net generation − Total interchange, interchange
   export-positive), the model's served demand is the measured **net
   generation** boundary, i.e. what ERCOT's internal fleet actually
   produced — which is the correct energy-balance target for an
   internal-fleet dispatch model.
2. **In the committed ercot-239 JSON, `gap_components_mw.demand` +
   `actual_side.interchange` = 0 (to the JSON's 1-MW rounding) in ALL 14
   rows.** The finding's own P3 grading ("ERCOT was net-IMPORTING 111–873 MW
   in every event hour") and its §0.5 gap statement ("+651…+873 MW in 12 of
   14") are numerically the same series with the sign flipped.

Consequently this round declares a **fourth candidate, (d) — the
comparison-frame identity**: the measured gap is the netted DC-tie import
itself, i.e. an artifact of comparing the model's served-demand boundary
(≈ net generation) against the EIA-930 total-demand boundary — not a defect
in the demand source. The chartered candidates (a)/(b)/(c) are then graded
on the question that remains after the identity is measured: **does the
demand source itself (EIA-930 `Demand`) misstate the settlement-boundary
load in these hours?** — measured against the independent ERCOT MIS
native-load record. Declaring (d) ex ante inverts nothing about the
method: every candidate below still gets its discriminating measurement and
its refutation criterion, and an identity that FAILS to close the gap
re-opens (a)/(b)/(c) at headline magnitude.

## 1. Population and identity gates (hard asserts, run first)

* **V-0 (population identity):** model/actual price series byte-identical to
  the ercot-239/237 constructions (keeper sidecar
  `hourly/system_2023.parquet` P1 demand-weighted zonal price;
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet` `rt`).
  The recomputed population {h : model < $200 ∧ actual ≥ $500} must equal
  the committed 14-hour list {2058, 2971, 4578, 4623, 4626, 5369, 5484,
  5777, 5943, 5945, 6399, 7001, 7145, 7480}. Mismatch STOPS the probe
  (no result written) and is an Amendment, never worked around.
* **V-1 (loader identity):** `load_demand("ERCOT", 2023,
  td_loss_factor=0.0, include_interchange=True,
  ercot_tie_zonal_interchange=True)` summed over zones must match the
  keeper sidecar's per-hour system demand (Σ zones, P1) with
  max |Δ| ≤ 0.5 MW over all 8760 hours — proving the decomposition below
  is a decomposition OF THE KEEPER'S OWN INPUT, not of a reconstruction.
  Failure → Amendment; the decomposition then re-bases onto the sidecar
  series and says so.

## 2. Measurements (all zero-solve; committed artifacts + raw measured inputs only)

Probe `scripts/probes/ercot240_eventhour_demandgap.py` →
`results/calibration/ercot240_eventhour_demandgap.json`. Sources (all
already on disk; no fetch): the keeper sidecar system_2023.parquet; the
EIA-930 wide extract `data/raw/eia-930-hourly/ERCO hourly.parquet`
(columns `Demand`, `Net generation`, `Total interchange`, `CEN`/`CFE`/
`SWPP`, `Subregion COAS…WEST`, hour-ending `UTC time`/`Local time`);
the ERCOT MIS native-load record
`data/raw/zone-specific-demand/ERCOT_Native_Load_2023.xlsx` (NP3-565-CD,
hour-ending labels `MM/DD/YYYY HH:00` 01–24, spring-forward HE 03:00 row
absent, fall-back duplicate marked `02:00 DST`, 8 weather zones + `ERCOT`
total); the committed ercot-239 JSON (event rows); the actuals parquet
(RT price, for conditioning only).

**Join convention (declared, not fitted):** native rows are joined to the
930 frame by TIMEZONE-AWARE UTC hour-ending stamps — parse the label,
tz-localize America/Chicago with the fall-back ambiguity resolved by the
file's own `DST` marker (plain `02:00` = first/CDT pass, `02:00 DST` =
second/CST pass), convert to UTC, match the extract's `UTC time`. The
constructed native UTC axis must be strictly monotone at +1 h steps and
land exactly 8760 matches; anything else is an Amendment. Wall-clock
formula indices (the shares parser's convention) are NOT used for level
joins — the CDT-span offset between the wall-clock grid and the positional
clock is itself measured under M-3(iii).

* **M-1 — the identity decomposition (candidate d).** With `D930(t)` = the
  raw extract `Demand`, `TI(t)` = raw `Total interchange`, `Dmodel(t)` =
  the V-1 loader/sidecar series: gap(t) = D930 − Dmodel; residual
  r(t) = gap(t) + TI(t), all 8760 hours. Report: r's p50/p95/p99/max |r|,
  count of |r| > 1 MW and > 25 MW and their hour locations (expected only
  at extract-repair/interp hours); the 14-hour table gap vs −TI vs r; the
  full-year regression-free identity share = 1 − Σ|r(h)|/Σ|gap(h)| over
  the 14 hours.
* **M-2 — the settlement-boundary wedge (candidate b).** w(t) =
  D930(t) − native_ERCOT_total(t) on the tz-joined clock. Report: year
  distribution (p5/p50/p95, mean), by month, by native-load decile; the 14
  event-hour values; event excess vs a DECLARED matched-control set
  (same month, hod within ±2, native load within ±3 %, actual RT < $100,
  event hours excluded; per event hour the control median w and the
  excess). Plus the 1:1 boundary panel: 930 `Subregion` columns vs native
  weather-zone columns (per-zone median/max |Δ|) and Σ subregions vs
  `Demand`.
* **M-3 — weather-hour alignment (candidate c).**
  * (i) Dmodel vs D930 lag scan (lags −3…+3), full year and split by DST
    regime (CST-early / CDT / CST-late) — the solve-input alignment.
  * (ii) native vs D930 lag scan under the tz-aware join, same splits;
    plus per-event-hour local best lag (±3 h window, levels).
  * (iii) The shares parser's wall-clock-hoy vs positional-clock offset
    during CDT (`scripts/data/curate_zonal_shares.py::parse_ercot_shares`
    month/day/hour formula vs frame position): measured and REPORTED as a
    zonal-weights observation — system-total-neutral by construction
    (share columns sum to 1), so it cannot carry the system gap; it is
    recorded for the owner queue, not adjudicated here.
  * (iv) gap-vs-ramp: if a ±1 h alignment error carried the gap, gap(h) ≈
    local D930 ramp × 1 h at the event hours; report the per-hour ratio.
* **M-4 — 4CP / load-resource response (candidate a).**
  * (i) 4CP-candidate windows W = {Jun–Sep 2023, top-8 native-load days
    per month, HE 16–18}: wedge w(t) in W vs same-month/same-hod non-W.
  * (ii) Event-hour dip test: for native and for D930 separately,
    x(t) − ½(x(t−1) + x(t+3)/0 — REPLACED, see below — the declared form
    is x(t) − ½(x(t−1)+x(t+1)), the symmetric 1-h neighborhood dip; a dip
    appearing in BOTH series is real load response correctly present in
    the source; only a DIFFERENTIAL dip (one boundary, not the other)
    can carry a wedge.
  * (iii) Price-conditioned wedge: w(t) binned by actual RT price
    (< $50, 50–100, 100–500, ≥ $500).
* **M-5 — context panel (report-only; grades nothing).** The 930 identity
  residual (Net generation − TI − Demand) year distribution and at the 14
  hours; event-hour import levels vs the tie counterparties (CEN/CFE/SWPP)
  and the import PERCENTILE at the M-2 matched controls (are near-max
  imports event-specific — context for the owner's conduct object, no
  adjudication here).

(The stray fragment in M-4(ii) above is a typo caught at write time; the
declared dip statistic is the symmetric form x(t) − ½(x(t−1)+x(t+1)). No
measurement had run when this was fixed.)

## 3. Adjudication rules and declared priors (graded in the FINDING; never selection criteria)

Materiality line for "carries gap mass": **300 MW** at event hours —
comfortably below the +651 MW floor of the 12-hour family (so nothing
material can hide under it) and above metering/rounding noise. Identity
tolerance: **25 MW** per event hour; identity REFUTED at any event hour
with |r| > 100 MW.

* **A-d:** candidate (d) carries the gap iff |r(h)| ≤ 25 MW in ≥ 12 of 14
  event hours AND the identity share (M-1) ≥ 0.95. Refuted iff any event
  hour has |r| > 100 MW (that mass re-opens (a)/(b)/(c) at headline level).
* **A-b:** candidate (b) carries gap mass iff |median event-hour w| ≥ 300 MW
  AND the median event excess over matched controls ≥ 300 MW. Refuted iff
  median event-hour |w| < 100 MW, or the wedge shows no event excess
  (≤ 100 MW) — then whatever wedge exists is a level property of the
  boundary, not this gap's carrier.
* **A-c:** candidate (c) carries gap mass iff a best lag ≠ 0 appears in any
  DST regime for a series that feeds the solve (M-3 i), or per-event-hour
  local best lag ≠ 0 in ≥ 7 of 14 with implied MW ≥ 300 (M-3 iv ratio in
  [0.5, 2] against the actual gap). Refuted iff lag 0 wins in every regime
  on both level joins.
* **A-a:** candidate (a) carries gap mass iff the price-conditioned wedge
  (M-4 iii) or the 4CP-window wedge (M-4 i) shows ≥ 300 MW event/window
  excess — i.e. the two boundaries treat curtailment DIFFERENTLY. A dip in
  both series (M-4 ii) refutes (a) as a gap carrier: response that is real
  and present in the source is correct representation, not a root cause of
  understatement.

Declared priors:

* **P1:** (d) passes A-d — the identity carries ≥ 95 % of the 14-hour gap.
  (Basis: §0's two pre-registered facts.)
* **P2:** (b) refuted as a gap carrier: median event-hour |w| < 150 MW and
  no ≥ 300 MW event excess. (Basis: ERCOT reports its 930 demand from the
  same settlement metering that produces the native-load record; the
  extract even carries the weather zones as its `Subregion` columns.)
* **P3:** (c) refuted: lag 0 in every regime on both level joins (basis:
  the ercot-239 lag-0 verification, 0.9997 vs 0.986 at ±1 h, and the
  frames-module hour-ending conventions), with the M-3(iii) shares-parser
  CDT offset PRESENT as predicted by code reading but system-neutral.
* **P4:** (a) refuted as a gap carrier: no ≥ 300 MW price- or
  window-conditioned wedge excess; where event-hour load response is
  visible it dips BOTH series.
* **P5 (disposition prior):** no input change is warranted; the phase-0
  "event-hour demand understatement" framing is re-adjudicated as the
  DC-tie import identity — the model's energy balance already serves the
  correct internal-fleet boundary, and reality met these hours with the
  ties importing near capability, a scarcity-consistent measured input the
  loader already nets. Any owner-queue item emerging is about
  scarcity-coupled import behavior in FORECAST mode (the priced-node
  lane), not about the backcast demand source.

## 4. What this round may and may not do

* MAY: read committed sidecars, the committed ercot-239/237 records, and
  raw measured inputs; compute the measurements above; write the probe +
  JSON + FINDING + calibration-log entry; grade the priors as declared;
  name owner-queue items.
* MAY NOT: solve anything ([R-HOLDOUT] untouched by construction); change
  any input, gate, config, offer curve, overlay, or mechanism; re-run any
  derive script; stamp any matrix cell (nothing is tested); arm or test
  any lever ([R-MECH-MATRIX] duties do not fire). **K-1:** V-0/V-1 failure
  → Amendment + stop until re-based. **K-2:** residual gap mass no
  candidate carries is reported OPEN, never force-fitted. **K-3:** any
  repair or mechanism that emerges is NAMED FOR THE OWNER QUEUE — a
  separate owner-visible round arms it, never this one.
* Years touched ⊂ {2023}; no `--holdout-authorized`; no marker; ERCOT
  surfaces only. No dashboard registration (no run is produced; rule 15
  does not trigger — ercot-237/239 zero-solve precedent).

## 5. Amendment protocol

Any deviation from §1–§2's constructions discovered mid-round (a gate
failure, a source column absent, a join that cannot be made 8760-complete)
is recorded as an Amendment to this precommit BEFORE any further
measurement, pushed, and the FINDING cites it — never silently absorbed.
