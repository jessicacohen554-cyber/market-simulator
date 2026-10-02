# PRECOMMIT — PJM close-out: Winter Storm Elliott modeled structurally (cold-correlated forced outage, backcast residual form)

Lane `closeout-PJM` (branch `claude/closeout-pjm-wave1`), 2026-10-02. **Owner ruling (relayed by the close-out desk, verbatim): "It counts but we should be able to simulate it?"** — no one-event caveat; 2022 scores in full. Plan §3.6 step 4 is re-chartered from "L3 event overlay or caveat" to a structural mechanism. **No solve is authorised by this document**: solves HOLD until the post-W0 PJM keeper lands on main (desk). Nothing here is built yet.

## 1. What census 0b established (FINDING-pjm-closeout-wave1-censuses-2026-10-02.md §3)

- No **level** gap: the keeper already carries more unavailable thermal MW (26–35 GW, 20–28 Dec) than PJM's published forced outage (10–36 GW).
- A missing **event rise**: published forced rises ~20–25 GW over its 20–22 Dec baseline on 24–25 Dec (+15.5 / +20.8 GW more than the model's own rise); the model's thermal unavailability rises only 4–7 GW. Reserve duals, shortfall and slack are 0 in every window hour; max zonal price ≤ $136 vs an actual top-18-hour mean of $2,071.
- Zero-LP headroom read (keeper `unit_marginal_2022`, Σ`cap_mw` − Σ`mw`, imports and offline CTs included): minimum 23.3 GW on 24 Dec, 22.6 GW on 23 Dec, against a `pjm_primary` requirement of 2.9 GW. Removing the missing 15–21 GW leaves ≈ 2–8 GW of headroom — the regime where the per-generator reserve families can go short and the ORDC ($850 / $1,700 steps) sets price. So the structure can plausibly reach the tail; it is not guaranteed (import caps during Elliott were themselves stressed).

**Why the measured overlay misses it.** The CAMPD outage overlays (rule 13 backcast inputs) detect sustained low-output spans (≥ 5-day windows plus the short-gas family); Elliott's outages were 1–3 days, cold-driven equipment failures and gas-supply curtailment (PJM: ~70 % of December forced outages were gas units). The backcast guard in `data/outages.py::apply_correlated_outage_derate` (`mode != "forecast"` ⇒ no-op, charter D.5) assumes "the measured CAMPD outage overlays already carry the actual events". **For short cold events in PJM that premise is measured false** (0b) — the same class of defect `neiso_coldsnap_derate_dualfuel_unswitched` corrected for NEISO ("that premise is a condition, not a fact").

## 2. Mechanism (rule 19: one cold-event mechanism, both modes)

Use the existing `correlated_forced_outage` mechanism (`ScenarioConfig.correlated_forced_outage`, default ON in forecast, ERCOT curve only; PJM cell `.` / fc `I`) as PJM's single cold-event mechanism, in two pieces:

1. **A PJM curve** in `constants.CORRELATED_OUTAGE_CURVE["PJM"]`, derived by `scripts/data/derive_correlated_outage_curve.py --iso PJM` (rule 23 frozen derive) with the method already written for ERCOT: per class, `excess(T) = clip(slope·(t0 − TMIN_sys), 0, cap)`; TMIN_sys = the PJM load-weighted zone daily minimum (`data/raw/pjm-weather/pjm_zone_temp_daily*.csv`); instrument = the class's best-mustered CAMPD hour on certified cold days; t0 = −7 °C (the shared NERC anchor, unchanged). **Sample: every certified PJM cold window 2018–2025** (Jan 2018, Jan 2019, Dec 2022, Jan 2024, Jan 2025 — whichever pass the in-merit certificate), never Elliott alone. Class split from the CAMPD instrument; the published RTO `gen_outages_by_type` forced series is the external cross-check (as FERC/NERC Feb-2021 is for ERCOT), not a fit target.
2. **A backcast residual form** — new field `correlated_outage_backcast_residual: bool = False` (PJM-scoped). When armed in backcast, the derate applied is per class-day `max(0, excess_curve(T) − excess_overlay)`, where `excess_overlay` is the cold-window availability reduction the CAMPD overlays already apply to that class over its own pre-window baseline. The overlay keeps every event it caught; the curve adds only what it missed. This is a reconcile, not a stack (rule 19); the D.5 double-count guard is kept by construction.

Rule 13: TMIN-driven, regenerates for any forward year (the forecast arm already runs the same curve); responds to conditions (colder ⇒ deeper; winterization era via `correlated_outage_winterized_year`). Rule 17: window = days with TMIN_sys ≤ t0; driver = measured temperature; forward story = the forecast mechanism. Rule 21: the curve's slope/cap per class are measured identifications (ledgered with the derive as source), zero tuned values. **Gas-supply curtailment** enters as the gas classes' excess in the same curve (the CAMPD instrument measures it as lost muster); a separate gas-curtailment field would be a second mechanism on the same phenomenon and is out of scope.

New field ⇒ a matrix row and a cell in every shard in the building PR (rule 28; CI `check_mechanism_matrix.py`).

## 3. Zero-LP phase 0 (before any solve; each reported with its reading)

| # | step | pre-fixed reading |
|---|---|---|
| E0a | derive the PJM curve; list certified windows and per-class slope/cap | ≥ 2 certified windows other than Elliott, else STOP (the curve would be Elliott-identified; report and return to the owner) |
| E0b | leave-one-out: re-derive without Dec 2022 | the 24–25 Dec predicted residual moves ≤ 30 %, else report as Elliott-dependent |
| E0c | footprint: every 2019–2025 day with a nonzero residual derate, MW by class | list reported; any day outside Dec–Feb is a construction defect |
| E0d | Elliott increment: model thermal unavailable rise 24–25 Dec over 20–22 Dec with the residual applied (rebuilt availability, no LP) | within [0.7, 1.3] × the published increment (+15.5 / +20.8 GW) |
| E0e | headroom: keeper Σ`cap_mw` − Σ`mw` minus the residual, hourly 23–26 Dec | count of hours below the `pjm_primary` requirement reported (no threshold — the solve decides) |

## 4. Solve gates (fixed now)

Control = the post-W0 PJM keeper span (rule 29b; G-DRIFT zero-LP audit). Full span, one shard per year (the residual can touch any certified cold day).

STOP: S1 identity — applied derate equals E0's residual table to 1e-6 per class-day; S2 footprint — availability byte-identical to the control on every day with TMIN_sys > t0; S3 no non-target flip — C2, C4, C8 do not go PASS → FAIL in any year, and no C1 class goes PASS → FAIL.
Pre-fixed outcome reading (plan §3.6 step 4; reported, promotion on structure is the owner's call): **model mean price 23–24 Dec 2022 ≥ $800; C3b 2022 ≤ 0.20**; C3a 2022 and C3c 2022 reported. Every other year's C3c is reported (a cold-day tail elsewhere is a side effect to read, not to tune).

## 5. Out of scope / rejected routes

`pjm_measured_outage_event_cap` (R, remove-only), `ordc_scarcity_overlay` (G), any price adder (rule 1), `winter_citygate_daily` (R, data-blocked), pinning published outage MW as the backcast input (fails the rule-13 forward test as a direct pin; it is the cross-check instead).
