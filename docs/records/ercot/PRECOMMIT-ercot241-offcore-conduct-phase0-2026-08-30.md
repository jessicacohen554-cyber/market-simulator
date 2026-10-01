# PRECOMMIT — ercot-241 (2026-08-30): Phase-0 MEASURED CONDUCT-PARAMETERIZATION screen on the off-core missed-event object (11-hour conduct core + h2058) — ZERO-SOLVE, measurement only; Phase-1 (one 2023 probe solve on the k33 carve-out) opens ONLY on the declared gate below

**Session ercot-241, branch `claude/ercot-241-conduct-param-adpfmm`.** Executes
FINDING-ercot239-missedevents-phase0-2026-08-30.md §6 **OBJECT 1** (the
off-core conduct object), per the dispatch charter: measure whether ERCOT's
60-Day SCED energy-offer curves shift with reserve-room / net-load tightness
at the object hours vs matched controls, and whether that dependence
identifies a **zero-fitted-scalar** parameterization. This precommit is pushed
and blob-verified BEFORE any measurement runs. All measurements are zero-solve
reads of committed artifacts and the tracked raw SCED corpus. The two-config
keeper (forward `2026-08-25-234-eastex-identity`, 2023 carve-out
`2026-08-25-236-swcap-clip-k33`) is untouched by Phase-0.

**Corpus note resolving the dispatch's warning:** the object hours are all
delivery-2023, which is covered by the TRACKED all-resource corpus
`data/raw/ercot/SCED/` (ERCOT-157 owner re-upload, publications
2023-03..2024-03, 323 shards at tip, all 365 delivery days; BLOAT-B-1 slim
kept the 108-column consumer union INCLUDING `SCED2 Curve-MW/Price1..35`,
TPO, HSL/HASL/LSL/Base Point and statuses — `scripts/data/
slim_ercot_dam_disclosure.py` KEEP registry). The gitignored re-fetch-only
`SCED-CT/` corpus (delivery 2024-01-24+, CT-only) is NOT needed and is not
fetched: no out-of-2023 measurement is chartered. SCED1 curves were dropped
by the slim and are unrecoverable for these publications; **SCED2 (the
as-dispatched curve, the armed RT wall's own basis) is the measured object
throughout** — declared, not a limitation worked around.

## 0. Standing closures this round sits under (cited, not re-tested)

* **ercot-217 (2026-08-17):** the 2023 scarcity-episode price level is the
  adjudicated conduct/model-class object; no admissible regime lever. This
  round tests the ONE direction ercot-239 §6.1 names admissible: a measured
  conduct parameterization from the 60-Day SCED corpus.
* **Door A (ercot-210/211) + `ercot_storage_rt_offer_surface` = R:** storage
  RT conduct is measured NOT-TRANSFERABLE, model-free non-identifiable, and
  its verbatim surface is rule-13-refused. **No storage-scoped
  parameterization can come out of this round whatever the census shows.**
* **ercot-161 (2026-08-04):** on the top-100 gap hours the armed RT wall was
  EXONERATED within net-load bin 6 (gap-hour gas spare ladder ≡ bin-6-rest,
  CC p90 197 vs 194, un-separable by PRC within bin 6); the real marginal
  segments were PWRSTR (0.91 of 1.10 GW offered ≥$500; merchant-gas
  dispatched p99 $81 (CC), gas ≥$500 offered ~0.06–0.08 GW); storage's
  hockey-stick is standing in ALL SEVEN net-load bins. **This round's
  population is different** — the k33 family's 12 off-core hours sit in
  net-load bins 2–6 (pct 66.3–98.1) at measured-room p0.1–17.1 — and its
  question is different: room-conditioned separation at MATCHED net load
  across bins, which ercot-161 measured only inside bin 6 on its own hours.
  Where results coincide, they confirm ercot-161; nothing here re-opens its
  bin-geometry or ceiling/rung adjudications.
* **ercot-178 `ercot_offer_surface_continuous` = R; ercot-180
  `top_scoped` = R:** no continuous or top-scoped NET-LOAD grain is
  re-proposed. The candidate axis here is measured reserve ROOM — a
  different driver, absent from every adjudicated cell.
* **V0 (ercot-195) / ercot-201:** the ANNUAL rent-vs-tightness identification
  for the retirement screen is non-identifiable and stays closed. This
  round's object is hourly ex-ante posted offer curves within 2023 —
  measured-vs-measured at hour grain — not the annual rent function; the
  V0 closure is cited to mark the boundary, not crossed.
* **Item 8 (CT band, CLOSED on daily-gas data; ercot-224 CME screen
  negative):** no daily Texas-hub basis exists on disk, so conduct-vs-basis
  CAUSE attribution at day grain is not attempted. The candidate mechanism
  inherits the armed wall's own convention (HR-multiple over HH-daily +
  fixed ERCOT basis, `derive_ercot_dam_cleared_share._gas_day_series`) —
  identical admissibility basis to the standing K cell; no Henry-Hub
  substitution for a local-basis claim is made anywhere.
* **DO-NOT-REDO surfaces:** `ercot_offer_surface_lowcurve*`, negative-offer
  variants, the ercot-212 net-credits leg (G-SPUR R), any ORDC steepening
  (the real curve is equally flat at these room levels, ercot-239 §5).
* **Object 2 (event-hour demand gap): CLOSED** by
  FINDING-ercot240-eventhour-demandgap-2026-08-30.md — the gap is the DC-tie
  import identity; no demand-side measurement here beyond quoting. **Object
  3 (wind pair h6399/h7145): queued, not chartered** — excluded from the
  object set and not measured. **The August steepness object (ercot-237 §7
  item 2, legs U2/U3): out of scope** — every object hour here has model
  < $200, disjoint from U2/U3 by construction.

## 1. Population and the V-0 identity gate (hard assert, run first)

Recompute the 2023 model/actual series byte-identically to
`scripts/probes/ercot239_missedevents_phase0.py::_series` (k33 carve-out
sidecar `results/calibration/ercot236_k33_clip/hourly/system_2023.parquet`
P1 load-weighted price, NaN→0; committed actuals RT). The recomputed
population {h : model < $200 ∧ actual ≥ $500} must equal the committed
14-hour family {2058, 2971, 4578, 4623, 4626, 5369, 5484, 5777, 5943, 5945,
6399, 7001, 7145, 7480} or the probe hard-stops with nothing written.

**The OBJECT SET is the 12-hour subset** = family minus the wind pair
{6399, 7145} (ercot-239 §4 sub-populations 1+3: the 11-hour conduct core +
h2058). Committed event-side facts quoted as inputs (ercot-239 JSON):
model $35–175, actual $537–2,014, measured RTOLCAP percentile 0.1–17.1,
actual net-load percentile 66.3–98.1 → armed-wall net-load bins
(edges 0.25/0.50/0.70/0.80/0.90/0.97): h2058→2, h2971→3, h7480→3, h7001→4,
h4623/h4626/h5777/h5943→5, h4578/h5369/h5484/h5945→6.

## 2. Declared constructions (fixed before measurement)

Sources: tracked SCED corpus via
`derive_ercot_sced_offer_wall.{_sced_source_files,_delivery_year_rows,
_coerce_sced_numeric,_READ_COLS,_SCED2_MW,_SCED2_PR}` (+`LSL`,`HSL`,`QSE`
never read here beyond the KEEP set); CPT→CST hoy conversion exactly as
`ercot161_price_setter_census.py`; measured room = `rtolcap` from
`data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet` (hourly; intervals
inherit their hour; percentile = year fraction ≤, NaN-dropped); net-load
percentile = `derive_ercot_dam_cleared_share._netload_pct(2023)` (EIA-930,
the armed wall's own conditioning variable); λ = `system_lambda` same
parquet. Status filter: `Telemetered Resource Status` startswith("ON") AND
≠ "ONTEST" (the ERCOT-154 discipline). Price forms: absolute $ (clipped to
HCAP $5,000) and HR-multiple (÷ delivered-gas day, the wall convention).
Segment walks: **census** = above-LSL slices (dispatched to min(q,BP),
offered to min(q,HASL)) per `ercot161_price_setter_census`; **spare** =
Base-Point→HASL slices per `derive_ercot_sced_offer_wall._spare_segments`.

**Declared room-percentile grid (fixed convention, never adjusted):** bin
edges (0.02, 0.05, 0.10, 0.175, 0.30, 0.50, 0.70) on the rtolcap year
percentile → 8 bins. "Tight" ≔ ≤ 0.10 pooled; "loose/control" ≔ ≥ 0.30.

**Matched controls per object hour e:** all 2023 hours c with month(c) =
month(e), |hod(c) − hod(e)| ≤ 1, |nl_pct(c) − nl_pct(e)| ≤ 0.075, and
room_pct(c) ≥ 0.30. Controls are DRIVER-DEFINED ONLY — never selected on
any price outcome. Fallback (declared): if < 6 control hours, widen to
month ± 1; if still < 6, that hour's paired panel is reported UNMATCHED and
excluded from paired aggregates (never silently padded).

The measurements:

* **M-1 (WHO — per-object-hour all-type census):** at each of the 12 hours,
  per Resource Type: dispatched MW in the λ-band [0.7, 1.3]×λ(h); dispatched
  and offered MW ≥ $500 and ≥ $1,000; offered MW in the **gap band**
  [max(200, model(h)), λ(h)] — the mass the model would have to price
  through. Interval-mean MW per hour. Wall-scope share ≔
  (CCGT90+CCLE90+SCGT90+SCLE90) / all-types, per bucket.
* **M-2 (event-vs-control spare ladders):** per class CC/CT (ST_GAS and the
  two coal types REPORT-ONLY — their pricing is owned by the drag/steam and
  per-plant coal structures, rule 19): capacity-weighted LADDER_QUANTILES
  (p10..p90) of spare-segment prices, event hours pooled vs each hour's
  controls pooled, in $ and HR-mult.
* **M-3 (within-resource paired repricing, position-fixed):** for each
  object hour e and resource r (CC/CT classes; report-only classes too) ON
  at e and ON in ≥ 3 of e's controls: position prices P_r at 0.5×HSL and
  0.9×HSL on the SCED2 step curve (per-hour value = median across the
  hour's intervals; NaN if the curve does not reach the position);
  Δ_r(e) = P_r(e) − median_c P_r(c). Class aggregate: HSL-weighted median
  and (p25, p75) of Δ across resources, per hour and pooled, in $ and
  HR-mult. This is the composition-free and position-free conduct-shift
  measure (the spare window moves with Base Point; M-3 does not).
* **M-4 (the candidate surface itself, pooled full-year):** per (class ∈
  {CC, CT} × armed net-load bin × declared room bin): capacity-weighted
  quantiles (p10..p90) of spare-segment prices in HR-mult and $, plus
  occupancy (segment count, resource-interval count, distinct delivery
  days). Computed via fixed log-spaced price histograms (declared: 480 bins
  over $[0.5, 5000] and HR-mult [0.05, 2000], underflow bucket below) —
  deterministic, memory-bounded, ≤2 % grid error, far inside every
  threshold margin below. This table IS the shape of the candidate
  zero-fitted-scalar artifact: values measured, both bin grids fixed ex
  ante (net-load edges = the armed wall's; room edges = §2 grid).
* **M-5 (model-side reconciliation, rule 19 — committed values only):** per
  object hour, what already prices it in the k33 config: model price, ORDC
  total dual, family duals/shortfall, rtordpa_overlay (all re-quoted from
  the ercot-239 JSON), plus the armed offer-path flags from the k33
  `run_config.json` (`ercot_offer_surface_cleared_share_rt` mode=replace on
  net-load edges [0.8, 0.9, 0.97]-pcts, `position_tail`, `swcap_clip` +
  k=33 peak bands, faststart pool). No solve, no replay: the enumeration
  grounds the reconciliation statement (a room axis would EXTEND the same
  wall mechanism — one mechanism, finer conditioning — never a stacked
  adder/floor).

## 3. Declared priors (graded in the FINDING; never selection criteria)

* **P1 (composition):** wall-scope (CC/CT) share of the λ-band dispatched
  mass < 1/3 in ≥ 8 of 12 hours; PWRSTR the largest single type in ≥ 8.
  (Basis: ercot-161's census — storage hockey-stick standing in all seven
  net-load bins; gas dispatched p99 $81.)
* **P2 (gas high-price mass):** CC+CT offered-≥$500 interval-mean ≤ 0.15 GW
  at ≥ 10 of 12 hours (ercot-161 base rates 0.06 GW CC + 0.082 GW SCLE90).
* **P3 (room shift small):** paired M-3 pooled median Δ at 0.9×HSL
  < +$25/MWh, AND tight(≤0.10)/loose(0.30–0.70) p90 spare ratio < 1.25 at
  every net-load bin 2–6 (the ercot-161 within-bin-6 ≡ result, extended
  off-core).
* **P4 (h2058 differs):** March outage-season composition — coal+ST_GAS
  λ-band share at h2058 ≥ 2× the other hours' median share.
* **P5 (occupancy adequate):** the pooled tight (≤0.10) × bins 2–6 cells
  hold ≥ 100 CC resource-intervals and ≥ 10 distinct days each (the room
  axis is derivable if wanted); sparse cells named if not.

## 4. Discriminators, kills, and the Phase-1 gate (direction-blind, fixed)

* **K-1 (scope kill):** if the wall-scope share of λ-band dispatched mass
  is < 1/3 in ≥ 8 of 12 hours → the family's clearing level is carried by
  resource populations whose conduct parameterization is CLOSED (Door
  A/PWRSTR) or owned elsewhere (coal per-plant, ST_GAS drag) → **no
  admissible mechanism from this charter; Phase-0 records the kill.**
* **K-2 (no-dependence kill):** if BOTH (a) M-3 pooled paired median Δ at
  0.9×HSL < +$10/MWh AND (b) M-4 tight/loose p90 ratio < 1.15 in every
  net-load bin 2–6 for both CC and CT → no measured room dependence exists
  to parameterize → kill.
* **K-3 (identifiability kill):** if the pooled tight (≤0.10) × bins 2–6
  occupancy is < 100 resource-intervals or < 10 distinct delivery days for
  BOTH classes → a year-scoped room-conditioned surface is not derivable
  under rule 23 discipline → kill.
* **PHASE-1 GATE (all four required):** (i) K-1, K-2, K-3 all clear;
  (ii) the measured tight-room surface REACHES the object: in ≥ 6 of 12
  hours, the (class, hour's net-load bin, room ≤ 0.10) M-4 cell prices
  p90 ≥ $500 (the family's own actual band floor) for CC or CT;
  (iii) the room axis adds content beyond the armed conditioning: the
  tight/loose contrast at matched net-load bin exceeds 1.25× at p90 in ≥ 3
  of bins 2–6; (iv) occupancy per P5 in every cell the mechanism would
  arm. Only then does Phase-1 (separate pushed precommit; ONE 2023 probe
  solve on the k33 carve-out config; full gates; rule-15 registration as
  probe/candidate; verdict unrewritten; keeper consequence ESCALATED to the
  owner, never self-adopted) open. **A gate miss is recorded at full
  magnitude as the round's verdict — not reframed, not re-thresholded.**

## 5. What this round may and may not do

Zero solves in Phase-0; no year scored or registered; no `ScenarioConfig`
field, no constant, no derive re-run, no data intake (the corpus is on
disk and tracked); no matrix cell or row edit unless Phase-1 actually tests
a mechanism (rule 28(b)/(c) — the ercot-239 "nothing tested ⇒ no stamp"
precedent governs a Phase-0 kill); rule 22: 2023 only, no marker, freeze
respected; rule 25: ERCOT surfaces and data only. Deliverables pushed as
produced: this precommit, the probe
(`scripts/probes/ercot241_offcore_conduct_phase0.py`), its JSON
(`results/calibration/ercot241_offcore_conduct_phase0.json`), the FINDING,
the calibration-log entry (shorthand ercot-241). Push transport: `git push`
on a freshly-fetched base; HTTP/1.1 fallback on 408/500 with backoff;
blob-verify every pushed file ≥ 300 lines. capx-* files off-limits.

## 6. Amendment protocol

Any construction found broken (a column absent, a source misread, a control
set empty) is recorded as a numbered Amendment in this file — what changed
and why, BEFORE the measurement it covers is used — and pushed. Thresholds
in §3–§4 are never amended after first measurement; a threshold discovered
to be wrongly SPECIFIED (not wrongly valued) stops the round instead.
