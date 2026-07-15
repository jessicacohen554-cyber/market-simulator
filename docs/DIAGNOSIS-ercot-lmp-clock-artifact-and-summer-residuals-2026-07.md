# DIAGNOSIS — ERCOT LMP delta heatmap: the scoring-clock artifact + the real summer residuals (2026-07-14)

**Task (owner ask, this session).** Explain, against the keeper
`2026-07-12-ercot63-gas-bridge`: (1) the 2024 August model LMP spikes and the
May-2024 undershoot; (2) the 2025 July/August model overruns; (3) the 2024–2025
heatmap banding — model "way under" at evening peaks, over everywhere else —
suspected to be storage-growth related. Drill to causal roots (capacity
availability or otherwise) before the model is used to forecast.

**Answer in one line: the evening-blue/daytime-orange banding is mostly NOT a
model defect — it is a +1-hour scoring-reference clock mismatch (the model's
8760 calendar is chronological/fixed-CST; `derive_actual_lmp.py` builds the
actual on the DST *prevailing* clock, so every hour mid-Mar→early-Nov is paired
one hour off; re-pairing lifts JJA-2024 hourly correlation 0.55 → 0.94); after
alignment the real, forecast-relevant residuals are (a) tight-week evening
scarcity OVER-amplitude that grows 2024 → 2025 with the real fleet's
flexibility (VOLL saturation + one-day spillover Aug 18–20 2024; phantom
$250–375 evening plateaus Jul 30–31 and Aug 18–25 2025 against a spike-free
actual — the C5c/G-37 storage-under-discharge lane plus absent peak demand
response), and (b) the already-filed G-22 DA-tail/offer-formation lanes
(May-2024 event breadth — outage inputs previously verified faithful — and the
winter-morning tail the model never forms).**

Analysis artifacts: keeper payload `lmpDeltaHr` (energy-only load-weighted
duals minus actual RT, 1 $/MWh int16) decoded for 2023–2025; all pivots/lag
tests reproducible from `frontend/data/backcast/runs/2026-07-12-ercot63-gas-bridge.js`
+ `actual_lmp_hourly_ERCOT.parquet`. No solve was run (scorer-side diagnosis).

## 1. The scoring-clock artifact (FIXED 2026-07-15 — see status note at end of section)

**Mechanism.** The model's year is built by `eia_loader._eia_hourly_frame`:
rows sorted by UTC, position k = k-th chronological hour from local midnight
Jan 1 — a fixed-offset (CST) clock with no DST discontinuities. Demand,
interchange, and the NP6 HSL wind/solar parquet all share this clock (verified
empirically: July-2024 demand diurnal peaks at h15–16 = 16:00–18:00 CDT ✓; HSL
July solar dies at h19 = CST sunset 19:45 ✓; January edges exact ✓). The model
is **internally consistent**. But `scripts/derive_actual_lmp.py` indexes the
ERCOT report's *prevailing-clock* date+hour straight into the 8760 calendar
(`hoy = month_start + (d−1)·24 + (HE−1)`, fall-back averaged, spring-forward
NaN). Result: for the ~5,600 DST hours/year, `lmpDeltaHr[k]` compares the
model's CST hour k against the actual's CDT hour k — one real hour apart.

**Evidence (lag cross-correlation, model vs actual, keeper series).** Best lag
is +1 h in *every* DST-heavy season and 0 h in *every* winter:

| season | 2023 r@0 → r@+1 | 2024 r@0 → r@+1 | 2025 r@0 → r@+1 |
|---|---|---|---|
| DJF | **0.13 @0** | **0.50 @0** | **0.65 @0** |
| JJA | 0.72 → **0.80** | 0.55 → **0.94** | 0.41 → **0.44** |
| MAM / SON | +1 wins both | +1 wins both | ~tied |

Re-pairing (model shifted +1 h inside the DST window only) cuts hourly-paired
MAE 2023 −13 %, 2024 −5 %, 2025 ±0, and collapses the signature dipoles the
heatmap shows (Aug-2024 h18 +254 / h20 −82 → a single aligned overrun at the
event hours; the 2023 Aug/Sep ±$300–500 h17-18/h19-20 pairs likewise). The
persistent "evening blue band" in 2024–2025 is this artifact: the actual's
evening peak lands one slot later than the model's identically-timed peak.

**What is and is not contaminated.** Shift-invariant metrics are fine: C3a
means, C3b duration curves, C3c tail *counts*, monthly means (`pMon`). D-1/C4
class-dispatch diagnostics compare against CAMPD CEMS, which reports in local
**standard** time — the model's own clock — so they are aligned (this is why
profile_r ≈ 0.98 coexists with a "broken" price heatmap). Contaminated:
`lmpDeltaHr` (the Report-tab heatmap), the scarcity-overlay demand-weighted
monthly MAE vs `_actual_rt_padded`, and any hour-of-day analysis built on the
paired series. **Scope is all six ISOs** — every `_eia_hourly_frame`-fed model
shares the chronological clock and every `derive_actual_lmp.py` reader builds
prevailing-clock actuals (the May-2024 forensics doc already noted the "DST
labeling convention" for demand vs NP6-346, but the published scoring reference
was never converted).

**Fix (scorer-only, no re-solve):** rebuild `actual_lmp_hourly_<ISO>.parquet`
on the chronological clock (localize the report's prevailing timestamps to the
ISO tz, convert to UTC, index chronologically from local-midnight Jan 1 — the
DST-duplicated hour then occupies its own real slot instead of being averaged,
and no hour is NaN'd), then re-render registered runs so `lmpDeltaHr`/overlay
MAE re-pair. Alternative (cheaper, uglier): convert at the comparison sites.
Either way the fix changes published per-run heatmaps/MAE for every ISO, so it
should land as its own owned change with before/after screenshots, not ride
along in a calibration PR.

**STATUS — FIXED at the source, 2026-07-15 (owner-authorized all-ISO
re-render; calibration-log entry of the same date has the full before/after
lag tables and verification).** `derive_actual_lmp.py`,
`derive_miso_hub_lmp.py` and `fetch_neighbor_lmp._densify_central` now index
chronologically (fixed standard-time zone per ISO); all six system parquets
rebuilt for 2023–2025 (out-of-training rows preserved byte-frozen on the old
clock pending authorized re-derivation); all 33 registered payloads re-paired
in place (`new_delta = old_delta + actual_old − actual_new`, exact to the
render's int16 rounding). ERCOT verifies exactly as predicted (2024 JJA r@0
0.55 → 0.94, best lag 0 in every DST season). The re-pairing EXPOSED
model-side phase defects previously masked by the artifact — NYISO (and
weakly CAISO-2024): DST-seasons-only −1 with DJF at 0, the signature of a
prevailing-phased model INPUT; PJM-2025 (+1), CAISO-2025 (−1/−2), MISO-2025
(−2): uniform all-season year-specific drifts — filed as follow-up
input-clock lanes in the log entry, NOT chased here (rule 14: the reference
stays on the verified true chronology). §2's aligned-residual analysis is
unaffected (it was computed re-paired).

## 2. What remains after alignment — the real residuals

Aligned month×hour pivots (DST months, model re-paired) leave three distinct
structures. Bucket means, Apr–Oct, ex-top-5 event days:

| year | h00–16 | h17–21 |
|---|---|---|
| 2023 | −3.5 | +17.4 |
| 2024 | +1.9 | −10.4 |
| 2025 | +2.7 | −10.9 |

### 2a. Tight-week evening OVER-amplitude, growing 2024 → 2025 (NEW as a filed lane)

> **Status 2026-07-14 (same day, follow-on audit executed):** the causal
> checks below were run —
> `docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md`. Outcome: the
> storage power/energy ENVELOPE is feasible and the outage overlay is
> ground-truth FAITHFUL (disclosure-verified; model thermal is ~+2 GW rich vs
> telemetry) — the defect is the **storage capability basis** (EIA-860 fleet
> power ~2 GW below ERCOT's registered PWRSTR capability in both summers, plus
> the AS-award subtraction at the scarcity margin). The audit doc's §2
> dispositions supersede this section's candidate ranking; the DR charter is
> `docs/handoffs/ercot-demand-response-charter-2026-07.md`.

Hour-level, aligned (model = energy-only dual; VOLL = $5,000):

- **Aug 19 2024 (real event):** actual h19/h20 = $3,060/$1,674; model
  **$5,000/$4,105** — saturates at VOLL where the real market topped out ~$3k.
  **Aug 20 2024:** actual peaked $172; model $1,304/$641 — the model extends
  the event a day reality dodged. (Aug 18 similar, +$50 daily mean.)
- **Jul 30–31 2025 (phantom):** actual evening max $243/$103; model
  **$1,944/$1,407** at h20 with ~$250 plateaus h19–22.
- **Aug 18–25 2025 (phantom):** eight consecutive over days; worst Aug 20 —
  actual ≤$175 all evening, model $300–900 across h18–22. Actual August 2025
  had **zero** hours >$200; the model has **14**.
- 2025 tail composition mismatch the aggregate count hides: model's 25 h >$200
  sit entirely in Jul/Aug evenings; the actual's 31 h sit in winter/shoulder
  mornings (Jan 15, Feb 20, Apr 7, Dec 15 — model forms none) plus scattered
  evenings.

**Causal reading.** The model runs out of evening flexibility exactly in the
year's hottest weeks, while the real 2024–2025 market grew the two cushions the
model under-carries:

1. **Storage energy through the evening ramp** (the already-filed C5c/G-37
   under-discharge lane, quantified here for 2025): backcast fleet is measured
   EIA-860 (Aug-2025 10.8 GW / year-end 13.7 GW — fleet *power* tracks
   reality), but fleet-average duration is only **1.42–1.55 h** and model 2025
   throughput is **4.11 TWh vs 5.46 TWh actual EIA-930 discharge (0.75×)**,
   with measured AS awards withholding a further **3.5 GW mean / 6.2 GW max**
   of evening power (`reserve_storage_as_power`; the measured AS→energy
   draw-down release exists but stops at the daily net-load peak hour — the
   model's $250 plateaus at h21–22 outlive the release window). The h20
   spike-then-plateau shape is the classic SOC-exhaustion signature. Checks:
   (i) audit EIA-860 energy-capacity (MWh) coverage for ERCOT batteries against
   ERCOT CDR/EIA-860M — blank rows default to 2.0 h but under-filled energy
   fields would shrink the fleet's GWh (rule 14: prefer the measured number,
   then root-cause); (ii) re-examine the post-peak boundary of
   `ercot_storage_as_deployment_mw` against the 2025 measured battery series —
   2025 actuals keep discharging past the net-load peak hour.
2. **Peak demand response is absent**: 4CP transmission-charge avoidance, ERS,
   and conservation appeals shed ~2–4 GW at exactly these hours in reality;
   the model's fixed demand must clear the last MW at VOLL. This is real
   market structure with a clean forward story (4CP is tariff mechanics; ERS
   is a procured product) — a legitimate structural mechanism, NOT a fitted
   haircut, but it needs its own charter and a measured identification
   (ERCOT 4CP response is directly observable in the load data around
   coincident-peak intervals).

Forecast relevance is first-order: forward years look like 2025+, and the
current keeper *manufactures* scarcity rent in exactly those years — it would
overstate forecast summer prices, scarcity revenues, and battery/peaker entry
signals.

### 2b. May-2024 (and Apr-2024) — CONFIRMED as the existing G-22 lane, not re-opened

The aligned pivot still shows May 2024 broadly under (monthly −$9.9; May 7
worst: model flat $41–47 through h15–18 while the actual built $257–997 into
the event, then model $1,371/$1,908 vs $2,451/$3,049 at the peak). This is the
already-forensically-closed thread
(`docs/DIAGNOSIS-ercot-may2024-outage-forensics-2026-07.md`): outage inputs
verified faithful to ±0.3 GW at the event hours, May-8 depth improved by the
nuclear-window fix (ercot56), and the remaining depth/breadth (plus the
late-May DA-shoulder days: May 12/20/26/28/29 aligned daily means −$15…−27) is
the filed G-22 DA-expressible offer-formation residual, ledgered as the
keeper's C3c caveat. Nothing new found; do not stack a second mechanism on it
(rule 19).

### 2c. Ordinary-day evening −$10 and the morning-ramp miss (structural, ties to G-22)

Ex-event, DST months, evenings run ~−$10 vs days +$2–3 (table above; winter
mornings h6–7 are −$3…−45 in most months, and every actual winter-morning tail
event — Jan 15-16/22 2024, Jan 15 / Feb 20 / Dec 15 2025 — is missed while the
model forms almost none). A perfect-foresight single-settlement LP cannot carry
the DA/RT ramp-uncertainty premium that the real RT market prices into every
ordinary sunrise/sunset ramp; this is the same family as the ledgered C3c
undershoot ("the model dual under-shoots scarcity by construction"). Any fix
must be a measured, forward-valid mechanism (e.g. ERCOT's actual ancillary
demand curves / uncertainty products), not an evening adder — the NYISO
frontier note (no published formula → rule-26 refusal) is the precedent for
where this line sits.

## 3. Recommended sequence

1. **Scoring-clock fix** (§1) — scorer-only, unblocks honest hourly
   diagnostics everywhere; all-ISO re-render with owner sign-off.
2. **Storage-energy audit** (§2a-1) — data check (EIA-860 MWh field vs
   CDR/860M) + the AS-release post-peak boundary vs 2025 measured discharge;
   both are measured-input corrections under rules 14/15, no new knobs.
3. **Peak demand-response charter** (§2a-2) — structural mechanism with
   measured identification; adjudicate on the Aug-2024/Jul-Aug-2025 windows
   leave-one-year-out per rule 22.
4. Leave May-2024/G-22 and the ramp-premium lane (§2b/§2c) where they are
   filed; re-score them only after (1)–(3) move the summer windows.

The trough/spread (negative-price epoch) frontier declared 2026-07-14 is
untouched by all of this — these are the scarcity-side and scoring-side lanes.
