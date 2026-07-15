# DIAGNOSIS — PJM-2025 phase drift de-confounded + the real coal/zonal structure (2026-07-15)

**Charter:** the post-clock-fix PJM Fable design session
(`docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md` Part B, amended by the
2026-07-15 ALL-ISO scoring-clock-fix log entry): de-confound the PJM-2025
uniform +1 h phase drift FIRST (lane c — "smells like a 2025-vintage EIA-930
extract phase issue"), then re-measure the July-2025 coal over-run and the CC
zonal misallocation on the corrected clock, build the D-1p per-plant cycling
instrument, and identify mechanisms + pre-committed gates (rule 1). **No
solve, no config flip — every number below is measured from committed
artifacts and raw source data (no-LP probes), 2023–2025 only.**

**Verdict in one line:** the "2025-vintage extract phase issue" hypothesis is
*backwards* — the 2025 inputs are the CLEANEST of the three years; what the
clock fix exposed is (a) a **2023 wide-extract indexing defect** (all columns
1 h LATE) and a **2022–2024 source-side fueltype-family clock defect** (all
`NG:` columns 1 h EARLY, fixed upstream ~Feb-2025) whose accidental
cancellations made 2023 *look* aligned, plus (b) a **year-invariant ~1 h-early
model-side lead in dispatch and price** — the LP's perfect-foresight overnight
cycling, i.e. the same LP-vs-MIP posture boundary C3c already discloses —
that the 2023 input error was masking; and (c) the surviving 2025 volume
residuals are real and converge on ONE structural gap: **the model has no
Dominion congestion separation** (real Dominion−AEP premium +2.8→+7.0 $/MWh
2023→2025, congestion-dominant, carried below the published-interface level),
which simultaneously explains the coal geography, the CC belt under-run, and
the 2025 coal-for-gas substitution. A fourth finding: **the 2025 EIA-930 PJM
vintage carries a May-onward Total-Interchange collapse that PJM's own tie
record contradicts by 15 TWh** — a new owner-level benchmark-basis item.

Probes (committed, no-LP): `scripts/probes/_pjm2025_phase_drift.py`,
`_pjm2025_payload_lag.py`, `_pjm2025_event_phase.py`,
`_pjm2025_exact_input_phase.py`, `_pjm2025_plateau_check.py`,
`_pjm2025_balance_xcheck.py`, `_pjm2025_dispatch_phase.py`,
`_pjm2025_final_localization.py`, `_pjm2025_wind_anchor.py`,
`_pjm_d1p_diurnal_cycling.py` (the D-1p instrument). Model side decoded from
the committed pjm-110 payload (per-plant hourly dispatch + `lmpDeltaHr`
reconstruction `model = actual_new + delta_new`, exact to int16 rounding).

---

## 1. Lead 0 — the phase-drift decomposition (input catalog + model-side lead)

### 1a. Reference set (all independent, all UTC- or sun-anchored)

* **PJM `hrl_load_metered`** (`datetime_beginning_utc`) — settlement-grade
  system load, the demand truth.
* **PJM Generation-by-Fuel feed** (`data/raw/ISO-specific-gen-data/
  PJM_{year}_gen_by_fuel.csv`, `datetime_beginning_utc`) — wind/solar/gas
  truth; its July solar centroid is 11.93/11.99/12.02 across 2023/24/25 —
  astronomically consistent (expected ≈ 11.7–12.0 for the fleet's 77–83° W
  span on hour-beginning EST positions).
* **EIA-930 BALANCE archive** (explicit `UTC Time at End of Hour`) — the
  independent absolute-clock copy of the same EIA series.
* **The sun** — solar-noon centroids cannot move year-over-year.
* **CAMPD CEMS** (local standard time) and the corrected
  `actual_lmp_hourly_PJM.parquet` (UTC-derived) for the output side.

### 1b. The input-clock catalog (verified multi-way)

| year | demand / region family | wind/solar/gas `NG:` fueltype family |
|---|---|---|
| 2023 | **1 h LATE** (930 peak lands +1 vs meter on 96 % of days; wide = BALANCE shifted −1, exact match 1.000) | **ALIGNED — by double error**: source 1 h early (BALANCE-2023 solar centroid 10.9) + extract 1 h-late shift = 0 (PJM-feed diff-lag best 0; centroid 11.9 ✓) |
| 2024 | aligned (97 % of days at 0) | **1 h EARLY at the source** (centroid 10.9; wind AND gas diff-lag +1 vs PJM feed) |
| 2025 | aligned (97 %) | aligned from ~Feb (centroid 11.9; W/S/G diff-lag 0 vs PJM feed; Jan-2025 straddles the source's convention switch — BALANCE Jan centroid 11.15) |

Mechanically: the wide `PJM hourly.parquet` 2023 vintage is value-identical
to the BALANCE archive with **every column placed one position late** (an
hour-beginning/hour-ending label mix-up in that vintage's construction);
2024/2025 rows sit on the BALANCE clock. Independently, **EIA's own PJM
fueltype series ran 1 h early through 2024 and was fixed upstream around
Feb-2025** (the demand family was always correct). The label columns
(`Local time` − `UTC time`) are internally consistent in every year — the
defects are in content placement, invisible without external anchors.

Also confirmed prevailing-clock loaders (DST months 1 h late, all years):
`pjm_net_interchange` / `pjm_zonal_interchange` (tie CSV read via
`datetime_beginning_ept`, `eia_loader.py:2572/2648`) and `parse_pjm_shares`
(`curate_zonal_shares.py:100`) — all three files carry a
`datetime_beginning_utc` column the loader ignores.

### 1c. The model-side lead (the actual carrier of the 2025 “+1”)

With the 2025 inputs verified clean, the keeper's 2025 output is still ~1 h
early — in **both** price and dispatch, against two independent references:

* Price: reconstructed model system price vs corrected actual RT — best lag
  +1 in all four 2025 seasons (diff-series estimator; the estimator control
  dDA~dRT scores 0 sharply every year). Daily-peak events: model peak −1 vs
  actual (2025 median).
* Dispatch: class-aggregate model gas dispatch vs CAMPD (and vs PJM's own
  feed): diff-lag **+1 in 2024 and 2025** (r 0.81 at +1 vs 0.71–0.75 at 0),
  **0 in 2023**.
* Against its own exact input net-load the model price leads +1 in every year
  and season — and the lead **concentrates overnight** (h0–6: +1 decisive;
  midday: 0; evening: noisy).

Interpretation (mechanism, not indexing): the write path is straight
`arange(T)` everywhere (`dispatch.py:3974`, `_system_frame`, renderer), an LP
cannot shift duals against its own RHS, and the lead is hour-of-day
structured — this is the **perfect-foresight cycling posture**: the LP sheds
and restarts capacity at the exact economic crossing overnight while reality
carries commitment inertia (min-run, startup lead), so the model's overnight
down-ramps and price decay run ~1 h ahead of the real ones. In 2023 the 1 h-
late demand input cancelled it (aligned-looking outputs, the pre-fix state);
in 2024 the early fueltype family compounded it; in 2025 (clean inputs) it
stands exposed. It is the phase-domain face of the same LP-vs-MIP online-
posture boundary C3c discloses, and of the D-1p flat-overnight residual (§4).

### 1d. How much of the PJM-2025 residual is phase?

* **Scored metrics: none.** All scored criteria are shift-invariant (verified
  in the 2026-07-15 entry); C3c stays FAIL on its own content (system model
  tail 7 h vs actual 59 h >$200 on the corrected pairing).
* **Hourly-paired diagnostics:** re-pairing the model +1 h moves total hourly
  MAE by only −0.4 % (2025) but cuts the **evening-window (h17–22) MAE 16 %**
  (18.69→15.69 $/MWh; 2024: −19 %) — the evening band of the `lmpDeltaHr`
  heatmap is substantially phase artifact; the overnight band is real
  conduct.
* **Volume/monthly quantities (Leads 1–2): clock-invariant, all survive.**

## 2. Lead 1 — July-2025 coal, re-measured (it is conduct-by-congestion, not price vintage, not floors)

Re-confirmed on the 923 basis: July-2025 coal **+1.90 TWh** (COAL_BIT +1.64;
West_APS +0.85, AEP_Ohio +0.66, SWMAAC +0.36, Dominion −0.24); annual 2025
coal **+7.77** / gas **−6.91** — i.e. net fossil ≈ +0.9: a **within-fleet
coal-for-gas substitution**, not an over-supply wedge (§3 kills the export-
wedge reading). Structure:

* **Not a price-vintage artifact.** The F923 2025 delivered-coal series is
  complete (128–142 plant-rows every month, 12/12 months for the reporters)
  and 2025 delivered prices genuinely FELL (Mountaineer 3.06→2.69 $/MMBtu,
  Amos 3.50→3.20, Mitchell 3.43→3.10) while gas rose 2.19→3.52 — the
  coal-favorable spread move is real, and reality also ran more coal; the
  model just runs *more still*, in the *wrong places*. (Several top
  over-runners — Brandon Shores, Conemaugh, Harrison, Gavin, Clover — are
  F923 non-reporters priced by the state fallback; a second-order item worth
  a look in the solve session, not the driver.)
* **Not sub-floor forcing (issue #1302 cleared for this residual).** The July
  over-run rides at economic-dispatch CF, not floor CF: model July CF 0.83–
  0.94 vs CAMPD 0.47–0.73 at the top over-runners (Mountaineer 0.94/0.71,
  Brandon Shores 0.83/0.47, Harrison 0.89/0.73, Conemaugh 0.79/0.58), with
  p5(hourly CF) = 0 at nearly all of them — they two-shift to zero, so no
  committed-multiplier floor is holding them up.
* **The geography mirrors the CC belt exactly** and flips sign at Dominion:
  over-runners are the WV/OH/W-PA bituminous fleet plus Brandon Shores
  (SWMAAC RMR), under-runners are Mt Storm (July −222 GWh), Clover (−172),
  Rockport (−114) — Dominion-zone units the model starves while importing.
* **The 2025 onset is April–October** (AEP_Ohio m−a: −0.61 in March → +0.27
  /+0.81/+0.76/+0.66… from April), tracking exactly the widening real
  Dominion congestion premium (§3) and the gas-price regime, i.e. the months
  where a flat congestion surface lets the LP wheel cheap western coal east.

## 3. Lead 2 — re-measured on the corrected clock: the congestion surface is the binding constraint

* **The model has no west→Dominion price separation.** Model 2025 annual
  zonal duals: Dominion 41.2 ≡ AEP_Ohio 41.2 (July 43.0 ≡ 43.0). Reality
  (PJM hub file, hourly, UTC-stamped): **Dominion−AEP-Dayton annual RT
  +2.79 (2023) → +3.07 (2024) → +7.02 $/MWh (2025)**, and the premium is
  **congestion-dominant** (2025: +5.81 congestion + 1.21 loss) — so a
  lossless LP *can* represent it; the model's Dominion import links
  (4,069 + 3,000 + 3,500 MW) simply never separate.
* **The published transfer-limit interfaces cannot carry it**: in PJM's own
  2025 transfer-limits feed, AP-South/AEP-DOM/Bedington-BlackOak flows sit at
  45–75 % of their limits and bind (≥98 %) in ≈ 0.0 % of hours. The keeper
  already runs `pjm_measured_interface_limits=True` — faithfully — and it is
  structurally insufficient: the real 2025 Dominion premium forms **below**
  the RTO transfer-interface aggregation (locally binding facilities around
  the NoVA load pocket). No tuning of the existing links is admissible or
  useful; the missing structure is sub-interface.
* **The interchange r = −0.164 is mostly a benchmark artifact, and the
  benchmark itself broke in 2025.** The fuelRow compares the model's priced
  seam against EIA-930 TI. But 930 TI diverges from PJM's own tie-line record
  starting **May-2025** (May–Sep: tie 2.88/3.59/4.09/5.08/3.42 TWh vs 930
  1.54/0.80/0.86/1.10/0.82; annual 32.93 vs 17.97 — the two agreed within
  0.3 TWh in 2023 and 2024). On PJM's own record the model **under-exports
  every year** (−11.1 / −10.5 / −8.0 TWh), continuing the known seam-depth
  boundary — there is no 2025 export-wedge over-supply. The r series
  (0.57 → 0.42 → −0.16) collapses exactly when its reference series does;
  re-scoring r against the tie record needs the origin bundle's hourly seam
  flows (solve-session item), but the level story is settled here.

## 4. D-1p — the per-plant diurnal cycling instrument (built, committed)

`scripts/probes/_pjm_d1p_diurnal_cycling.py` scores every ≥500 MW CC_REGULAR
plant from committed artifacts only (payload hourly CF vs bench CAMPD hourly;
CEMS is standard-time stamped, so the metric never depended on the LMP clock
fix): overnight CF (h0–6) model vs CEMS, overnight-turndown depth
(1 − night/evening CF), night share of |m−c|, and a per-plant phase lag.
Headlines from pjm-110: the known over-runners are flat overnight where
reality two-shifts (2025: Newark turndown 0.28 vs 0.51, York 0.04 vs 0.12,
South Field 0.01 vs 0.09, Hanging Rock 0.01 vs 0.06; 30–42 % of each plant's
total |error| accrues in h0–6), and the flat-offender count is 3/5/1 plants
(15+ pt turndown gap) in 2023/24/25 with a long tail of 5–10 pt gaps.
**Clock caveat encoded in the script:** the phase column is only clean for
2025 (2023 demand-late / 2024 renewables-early inputs contaminate the model's
overnight timing); the CF/turndown columns are phase-robust in all years.

## 5. Owner boundary notes (deferred decisions, NOT chartered work)

1. **C1 930-vs-923 anchoring (from the July diagnosis §7.4, now with the 2025
   numbers).** The two federal series invert the sign of the 2025 mix error:
   coal +7.7 OVER (923) vs −1.6 UNDER (930); gas −6.9 UNDER (923) vs +13.4
   OVER (930). volErr and every class gate already score on 923; C1's
   gas/coal rows remain 930-anchored. Decision requested: move C1's fuel rows
   to the 923 basis (or dual-report). Until then, no volume charter should be
   seeded from a model-vs-930 delta without a 923 cross-check.
2. **The 2025 interchange actual (NEW).** EIA-930 TI and PJM's tie-line
   record disagree by 15 TWh from May-2025 (§3). Every phase/level check this
   session says PJM's own settlement-grade record is the trustworthy side —
   and the same 2025 vintage independently changed its fueltype clock
   (Feb-2025) and diverges from 923. Decision requested: score the seam
   against the tie record (and flag `e930.interchange` 2025 as
   corrupt-vintage, the `EIA930_NG_CELL_CORRUPT` pattern).
3. **EIA-930 fueltype-family clock (cross-ISO).** The PJM fueltype family was
   1 h early at the source through 2024 (§1b). CAISO-2025 (−1/−2) and
   MISO-2025 (−2) drifts from the clock-fix table are the same follow-up
   family — the per-family audit built here (meter/astro/ISO-feed anchors)
   generalizes; those ISOs' audits are their own lanes (log entry lanes b–d),
   not chartered by this doc.

## 6. Mechanisms identified + pre-committed gates (rule 1: structure first, never the residual)

**M-1 — PJM input-clock repair (Opus, no-LP derive + one re-solve/re-gate).**
Rebuild the wide `PJM hourly.parquet` 2023–2025 rows from the BALANCE archive
with per-family clock conventions, and switch the three EPT-indexed loaders
(`pjm_net_interchange`, `pjm_zonal_interchange`, `parse_pjm_shares`) to the
files' `datetime_beginning_utc` columns. Rule-14 admissible (measured data,
placement fix); rule-23 (source-data action, cites this audit). Because 2023
demand moves by 1 h, the keeper recipe re-solves all three years, one bundle
(rule 16). **Pre-committed gates (all source-anchored, residual-blind):**
  * demand: daily-peak offset vs `hrl_load_metered` mode-0 on ≥95 % of days,
    each year (2023 currently 96 % at **+1**);
  * solar: July generation-weighted centroid ∈ [11.5, 12.3] each year
    (PJM-feed reference 11.93–12.02);
  * wind & gas benchmark: diff-series best-lag 0 vs the PJM UTC-stamped
    gen-by-fuel feed, each year;
  * interchange/shares: re-derived series byte-equal outside DST windows and
    exactly −1 h inside them;
  * scored-metric expectation is *within-noise* (phase cancels in monthly and
    duration metrics) — any C-criterion flip is investigated as a bug, not
    banked as a win. Expected visible effect: the 2023 evening heatmap band
    tightens the way §1d predicts; D-1p phase column becomes clean for 2023/24.
  * Model-side expectation stated in advance (falsifiable): after M-1 the
    output phase lead becomes **uniformly ≈ +1 in all three years** (the
    2023 cancellation disappears). If 2023 stays at 0, the model-lead
    diagnosis of §1c is wrong and must be revisited.

**M-2 — Dominion congestion separation (Opus/owner, new charter — the ONLY
lever that addresses the surviving volume residual).** The measured facts
(§2–§3): congestion-dominant premium, sub-interface formation, coal+CC
geography flipping sign at the Dominion boundary. The admissible structure is
a **measured intake of PJM's binding-constraint record** (DataMiner
transmission-constraints feed: constraint name, binding hours, shadow price)
crosswalked to a Dominion-import interface (or a NoVA zone refinement —
owner's topology call, the NYISO-pocket precedent). Driver: published
constraint data + data-center load growth in the Dominion zone (forward
story: constraint set regenerates from PJM planning postings; responds to
load growth and upgrades). **Pre-committed gate:** with the mechanism on and
zero fitted scalars, the model's Dominion−AEP annual RT spread reproduces the
*sign and growth* of the measured premium (2023 < 2024 < 2025, each within
±40 % of actual) and the D-1/volErr Dominion cells (CC belt + Mt Storm/
Clover) move toward CEMS **as a consequence** — the gate is the spread
structure, never the coal MAE. If the intake shows the 2025 premium is not
representable at the 8-zone grain, the honest outcome is a documented
boundary (as with C3c), not a fitted adder (rules 1/11/13/26).

**M-3 — overnight commitment inertia (deferred; the ERCOT gas-commitment-
bridge pattern).** The model-side 1 h-early lead (§1c) and the D-1p
flat-overnight residual (§4) are one phenomenon: P1 has no overnight
commitment posture. The eventual lever is the ISO-neutral P0-pattern bridge
(ERCOT-63 construction: physics-gated per rule 18, measured LSL fractions,
D-2 id, D-4 window = overnight bridge hours) **only if** the PJM offer-floor
corpus (`data/raw/pjm-energy-offers`) supports the committed-state evidence —
that corpus intake is its own charter. Until then this stays a disclosed
boundary alongside C3c; per the session charter, no adder, no haircut, no
reserve-supply re-open.

**Sequencing:** M-1 first (it moves the 2023 solve and cleans every phase
diagnostic), then M-2 (the volume/structure lever), M-3 last. C3c itself is
expected to remain FAIL-as-disclosed-boundary after M-1 (its tails are
shift-invariant); if M-2's real congestion prices the 2025 summer tail hours
into the Dominion/EMAAC zones, C3c may move — measured, not targeted.

## 7. Guardrail review (rules 1/11/13/14/22/26)

* **No solve, no config flip, no new tunables** — probes only; every claim
  traces to a measured source (meter, sun, BALANCE, PJM feeds, CEMS, hub
  LMPs) or a committed artifact.
* **Rule 13/14:** every proposed fix is a measured-input placement/intake
  repair with a forward story; no measured *outcome* is fed back in; gates in
  §6 are source-anchored, none scores a residual.
* **Rule 22:** 2023–2025 only. (2022/2026 rows appear solely as extract-
  vintage metadata — no out-of-training content was scored or solved.)
* **Rule 26 check:** M-1 removes the accidental error-cancellation the 2023
  backcast currently *benefits* from; the expected honest cost (the exposed
  uniform model lead in 2023) is stated in §6 in advance.
* The interchange r and the coal headline were both sitting on a broken 2025
  benchmark cell — reinforcing the July-diagnosis case study: **no volume
  charter from a single-basis delta.**

## Pointers

* Keeper: `2026-07-14-pjm-110-bench-hygiene` (unchanged; keepers.json
  untouched — owner-only).
* Grounding: `docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md` §4/§7;
  `docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md` Part B; calibration-log
  2026-07-15 (ALL-ISO scoring-clock fix);
  `docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md`.
* CAISO precedent for a measured input-clock correction:
  `caiso_demand_clock_realign` (caiso-75).
