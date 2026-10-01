# PRECOMMIT — caiso-205: Phase-1 A/B of the adaptive-expectation storage offer (CAISO leg), pre-registered before either arm is solved

**Owner order (caiso-205 charter, branch 1, 2026-08-19):** Phase-1 entry over
the caiso-204 recorded Phase-0 FAIL (G-BOOT sole structural fail) — the
ercot-188/213/215/221 pattern: A/B at full magnitude, direction-blind kill
table, both runs registered whatever the verdict. This file is committed and
pushed BEFORE either solve is launched; nothing below moves after a result is
read.

## §1 — The mechanism as built (single delta)

`caiso_storage_adaptive_expectation` (ScenarioConfig, default off,
CAISO-gated — the ERCOT field is NOT widened, rule 25). Two-pass P1 through
the existing `pipeline/solve.py p1_storage_discharge_cost` seam
(`scripts/run_calibration.py::run_year`), one adaptation pass:

- **Event basis (pass 1):** the model's OWN daily max CA demand-weighted P1
  energy dual — pure lambda, which IS CAISO's scored backcast price
  (caiso-137b: the calibration lane's price writer carries no CAISO overlay
  term). Zero measured content in the armed path (rule 13). WECC_import has
  load_share 0.0, so the all-zone demand weighting equals the caiso-204
  G-BOOT instrument's CA-zone weighting exactly.
- **Constants, FROZEN at the caiso-204 identification**
  (`caiso204_adaptive_phase0.json`; charter guardrail):
  event threshold **$200** (`CAISO_ADAPTIVE_EVENT_USD`), window **h18–21 PT**
  (`CAISO_ADAPTIVE_WINDOW_HOURS`, model fixed clock), park cap **$1,000**
  (`CAISO_ADAPTIVE_PARK_CAP_USD`), trail 120 d (shared
  `ERCOT_ADAPTIVE_TRAIL_DAYS`), half-life **30 d**
  (`caiso_adaptive_half_life_days`), beta **0.5945** (`caiso_adaptive_beta`),
  per-solve-year reset (shared `ercot_adaptive_expectation_daily` helper).
- **Floor (pass 2, THE scored pass):** battery discharge offer
  `max(vom, P_hat × $1,000)` in window hours only; **battery rows only** —
  pumped storage keeps its own calibrated adder (the caiso-204 S4 classifier
  excluded PS from the conduct population). Off-window hours carry the
  incumbent vom exactly.
- Audit sidecar `hourly/adaptive_<year>.parquet` (s_model_day / p_hat_day /
  floor_usd), the same columns as the ERCOT leg.

## §2 — The A/B

- **Control A** (`results/calibration/caiso205_control_A`):
  `replay_keeper.py results/calibration/caiso200_h1_memberpanel` — zero-delta
  replay of the keeper, full span 2023 2024 2025 (years sequential within the
  invocation, rule 12).
- **Arm B** (`results/calibration/caiso205_adaptive_B`): identical replay +
  the single delta `--set caiso_storage_adaptive_expectation=true`.
- Both bundles registered on the backcast dashboard (rule 15/16) whatever the
  gates say, as `2026-08-19-caiso205-ctl-headbase` /
  `2026-08-19-caiso205-arm-adaptive`.

## §3 — Ex-ante expectation, recorded before solving (caiso-204 §C, charter)

From the caiso-204 G-BOOT measurement of the keeper's own committed path
(model event days 0 / 1 / 0 at $200):

- **2023 and 2025: byte-identical A/B by construction** (S_m ≡ 0 → P_hat ≡ 0
  → floor ≡ 0 → the pass-2 cost array equals the incumbent vom everywhere).
- **2024: near-inert** — one event day, max floor ≈ $14.5 on the ~30-day
  decay window's evening hours, below the $53.2 quiet-day standing ask and
  far below window-hour clearing prices: predicted zero dispatch effect.
- **The A/B buys the honest stamp, not a gate move.** If the arm nonetheless
  moves anything, the gates below adjudicate it direction-blind.

## §4 — Direction-blind kill table (all bars fixed now; a kill is a kill
whatever direction the residual moved)

| gate | bar | kill condition |
|---|---|---|
| G-REPRO | control A reproduces the keeper: every committed `hourly/` sidecar sha256-identical to `caiso200_h1_memberpanel` (12 files: class_hourly/system/reserve_family × 3 years — reserve_family absent on both sides counts as identical) | control fails to reproduce → the A/B basis is the CONTROL, and the non-reproduction is reported as its own finding; arm-vs-keeper comparisons are then inadmissible |
| G-CAP | no hour in ANY zone of the armed run prices above CAISO's $2,000 hard cap (Tariff §39.6.1) where the control does not | any arm-introduced above-cap hour → REJECTED-AS-ARMED |
| G-SHED | the armed run introduces NO new load-shed hour: per year, the set of hours with any zonal `slack > 0` is a subset of the control's | any new shed hour → REJECTED-AS-ARMED (the ercot-221 G-SHED bar verbatim) |
| G-BAT | per-year total battery discharge energy, arm / control ∈ [0.80, 1.25] (a byte-identical year reads 1.000 trivially) | outside band → REJECTED-AS-ARMED (floor collapsed or gamed storage dispatch) |
| G-D2 | armed bundle's `legitimacy_diagnostics.json` carries the `caiso_storage_adaptive_expectation` D-5 attribution row; D-4 rows otherwise identical to control | missing attribution or a new off-window D-4 binding → REJECTED-AS-ARMED |
| G-DOF | armed DOF ledger = control ledger + EXACTLY one entry (`caiso_adaptive_half_life_days / caiso_adaptive_beta`, measured-physical, n_scalars 2); control ledger unchanged vs keeper (charter: 10/7 may only hold) | any other delta → REJECTED-AS-ARMED |
| MUST-NOT-REGRESS (charter) | on the arm: C3b per-year ≤ 0.20 (control 0.097 / 0.174 / 0.181), C8 PASS, C6 attested | any regression past a bar → REJECTED-AS-ARMED |
| G-ADA | REPORTED, never a gate: per-year pass-1 model spike days, P_hat max, count of window hours with floor > battery vom, max floor | — |

**Verdict rule (fixed now):** all gates pass AND the arm is byte-identical /
dispatch-inert in every year → matrix cell stays **I** (armed-and-inert on
this keeper, Phase-1 confirmed — the recorded wall measured at full
magnitude); all gates pass AND the arm does real work → promotion question
goes to the owner with the direction-blind numbers (never auto-promoted);
any kill → **R**. The C3a residual's direction is INADMISSIBLE as acceptance
evidence in either direction (caiso-203 owner ruling; charter guardrail) —
it is reported as a side-effect line only.

## §5 — DO-NOT-REDO carried forward

The caiso-204 §F list is binding here: no measured event series in any armed
path; no model-side threshold below $200; no quoting beta = 0.5945 as skill.
The caiso-204 Phase-0 identification is NOT re-run (its JSON is the record).

Next number after this session: caiso-206.
