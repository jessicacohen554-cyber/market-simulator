# Calibration-log entry — fold into `docs/calibration-log.md` under "## Runs" (top), dated 2026-07-15

(Standalone entry file, the `_pjm_phase_drift_log_entry.md` pattern: the full
calibration-log is too large for the API-only push path from this sandbox. Fold
this verbatim as the newest entry — ABOVE the `_pjm_phase_drift_log_entry.md`
Fable diagnostic entry — and delete both stubs.)

---

### 2026-07-15 — PJM — pjm-112 (input-clock repair, M-1): the two PJM EIA-930 per-family clock defects fixed at the source — **2023 region family −1 h** (extract hour-beginning/hour-ending mix-up) and **2024 fueltype family +1 h** (EIA-930 source ran 1 h early through 2024), value-preserving; the three PJM DataMiner loaders switched `datetime_beginning_ept` → `datetime_beginning_utc`; pjm-110 recipe re-solved all three years at corrected inputs. **Every scored criterion IDENTICAL to pjm-110 (NOT-YET on C3c), zero flips — within-noise as predicted.** Falsifiable model-lead prediction **REFUTED for 2023**: the lead is +1 in 2024/2025 but 2023 stays 0, so §1c's uniform-lead claim does not hold. Keeper CANDIDATE, keepers.json unchanged (owner promotes)

**Charter:** `docs/DIAGNOSIS-pjm-2025-phase-drift-and-zonal-structure-2026-07.md`
§6 M-1 (the Opus solve execution of the 2026-07-15 Fable diagnosis, the entry
directly below). Rule-14 admissible (measured data, placement fix); rule-23
(source-data action citing the audit, never a residual). 2023–2025 training
only (rule 22); zero fitted values; DOF ledger byte-identical to pjm-110; no
ScenarioConfig change.

**The two source defects, corrected by a value-preserving UTC-time re-placement**
(`scripts/data/extend_eia930_hourly_from_balance.py --rebuild-pjm-input-clock`; each
cell keeps its measured value and only moves to the UTC hour it belongs to — no
re-pull, no interpolation): (a) the **2023 region family**
(`Demand`/`Demand forecast`/`Net generation`/`Total interchange`) was built one
position LATE (verified value-identical to the EIA-930 BALANCE archive placed
hour-ending but +1 slot) → **−1 h**; (b) the **fueltype family** (`NG:` columns)
ran one hour EARLY at the EIA-930 source through 2024 (fixed upstream ~Feb-2025;
July solar centroid ~10.9 vs the astronomically-fixed ~11.9) → **2024 +1 h**.
2023's fueltype was already aligned (the two errors offset) and is KEPT; 2024's
region was already correct and is KEPT; 2025 untouched (Jan-2025 straddles the
upstream switch, centroid 11.15 — left as measured, no fabricated sub-month
shift). Every cell outside the two shifted (family, year) blocks is
byte-identical to the pre-fix file. The three DataMiner loaders that indexed the
prevailing `datetime_beginning_ept` stamp (`pjm_net_interchange`,
`pjm_zonal_interchange` in `eia_loader.py`; `parse_pjm_shares` in
`scripts/data/curate_zonal_shares.py`) now index `datetime_beginning_utc` on the
model's fixed-EST clock — byte-identical outside DST, exactly one hour earlier
inside. Per-family convention documented in `data/raw/eia-930-hourly/README.md`.

**Pre-committed gates (source-anchored, residual-blind — diagnosis §6; all PASS):**
demand daily-peak mode-0 vs `hrl_load_metered` — 2023 **96.4 %** / 2024 96.7 % /
2025 97.0 % (2023 was best-lag −1, now 0); July solar generation-weighted centroid
∈ [11.5, 12.3] — 2023 11.90 / 2024 **11.93** (was 10.94) / 2025 12.03; wind & gas
diff-series best-lag 0 vs the PJM UTC-stamped gen-by-fuel feed each year;
interchange/shares byte-equal outside DST windows, exactly −1 h inside (one Nov
fall-back transition hour per year, the boundary itself).

**Scored verdict (vs pjm-110):** IDENTICAL on every criterion — C1 16/16 (free
12/12), C2, C3a, C3b, C4, C5a, C6, C7, C8 PASS; **C3c FAIL** (the LP-vs-MIP
scarcity-representation boundary; its tails are shift-invariant, so the phase fix
cannot move it — confirmed). Determination **NOT-YET on C3c**, same as pjm-110.
No C-criterion flipped — the input-clock phase correction is within-noise on every
monthly/duration metric, exactly as predicted (phase cancels in shift-invariant
scores). (C8 2024 CT_PEAKER is a grounded-above-budget clean PASS: 15.2 % forced,
all binding mechanisms clear D-4, profile r 0.966 / CV ratio 0.916 — rubric v2.2.)

**Falsifiable model-lead prediction — REFUTED for 2023 (reported honestly per
diagnosis §6).** Prediction: after M-1 the model output phase lead becomes
uniformly ≈ +1 h in all three years (the 2023 input-error cancellation
disappears). Measured on the pjm-112 payload — model price vs its own corrected
input net-load, diff-series best-lag: **2023 = 0**, 2024 = +1, 2025 = +1; and the
D-1p per-plant dispatch phase (CEMS-anchored, phase-robust) is mostly 0 in 2023,
mixed 0/+1 in 2024/2025. **2023 stays at 0**, so by the diagnosis's own stated
criterion the §1c hypothesis — a year-invariant ~1 h-early model cycling lead that
the 2023 input error was merely masking — **does not hold**. The corrected reading:
the model's overnight perfect-foresight lead is real in 2024/2025 but genuinely
absent in 2023; 2023's pre-M-1 +1-vs-input was the input defect itself (the model
faithfully followed its 1 h-late input), not a masked model lead. The lead is
year-dependent, not a masked constant — §1c to be revised. (C3c remains
FAIL-as-disclosed-boundary as expected; M-1 was never predicted to move it.)

**Bundle / environment note.** Bundle `results/calibration/pjm112_input_clock`,
dashboard id `2026-07-15-pjm-112-input-clock`, label `pjm 112 input-clock`. This
15 GB box OOMs on a single-process 3-year PJM co-opt solve (accumulated prior-year
state peaks ~16 GB); the bundle was produced by solving **one fresh year per
process** and chaining the identical pjm-110 recipe via `--reuse-solved` (a new
forward in `run_replay_bundle`; `plan_reuse_solved` enforces recipe/config
identity + clean-tree, so each reused year's dispatch is byte-identical to a fresh
solve — a resume, not a methodology change). Years solved sequentially throughout
(rule 12); the DataMiner `hrl_da_incs_decs` 2023–2025 corpus was re-fetched
(gitignored, DataMiner2 restriction) for the `pjm_da_virtual_bids` leg. M-2
(Dominion congestion) and M-3 (overnight commitment) not started — owner scope /
corpus charter pending (diagnosis §6).
