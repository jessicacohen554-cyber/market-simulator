# PRECOMMIT — SPP-63: arm `spp_curtailment_ceiling` on keeper 7

**Lane** SPP-63 · **Base** `24737d3c1a3824b92e3d91fde1990bd6bf13ff77` ·
**Control** keeper 7 `2026-09-10-spp-62-vintage-census`, bundle `results/calibration/spp62_span`
(committed WITH its `hourly/` sidecars) · **Written and pushed BEFORE ANY SOLVE.**

**DECIDED BY** owner instruction, 2026-09-10, verbatim: *"No spp 58 was killed just proceed with
your solve"* — issued in response to this lane's recommendation to defer to lane SPP-58. SPP-58 is
dead, so `spp_curtailment_ceiling` is unowned and this lane takes it.

**PRIOR IN THIS LANE:** `docs/handoffs/FINDING-spp-63-2026-09-10.md` (pushed at `ec0f1df2`) refuted
the chartered object **R-az** (the ST_GAS offer / commitment defect) at phase 0 on measured
arithmetic, zero LP. This PRECOMMIT does not re-open it.

---

## 1. THE OBJECT, AND THE ONE SEAM

**`ScenarioConfig.spp_curtailment_ceiling`** (bool, dataclass default `False`), with
**`spp_curtail_depth_wind`** (float, dataclass default **`0.288137`**) **LEFT AT ITS DECLARED
DEFAULT AND NEVER SWEPT.** SPP-only, already BUILT (SPP-58) and default-off.

**The seam is the wind CF upper bound**, one multiplier per (zone, hour):

```
ceiling_frac(t) = 1 − depth_wind × congestion_share(t)
```

`congestion_share` is read off SPP's own derived binding-incidence table
(`data/raw/reference/spp_curtailment_share.csv`, 867 rows) on the **model's own** net-load decile ×
hour-of-day × season axis, so it regenerates for a forward year and responds to changed conditions —
rule 13 `[R-MEASURED]`'s forward test. **Shape** from SPP's published RTBM binding-constraint archive
(binding *incidence* only — never a volume, never a price, never a residual). **Level** from SPP's
published measured curtailment MW (SPP MMU ASOM,
`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`): the single energy-weighted value that centres
all three years at once (per-year 0.2565 / 0.3139 / 0.2917, **pooled 0.288137**). **Solar takes no
ceiling** — SPP's solar bound is delivered-pinned and carries no gross-up headroom.

## 2. WHY — rule 14 `[R-ACCURATE]`, not the residual

Re-derived in this lane from the keeper's committed sidecars and the committed EIA-930 benchmark
(`FINDING-spp-63` §3): model wind exceeds actual by **+10.708 / +11.407 / +11.586 TWh** while the LP
takes only **2.71 / 2.30 / 1.80 %** of the **11.01 / 11.68 / 11.80 TWh** of curtailment the measured
record implies. The wind **potential** is right (114.0552 / 120.9925 / 122.2552 TWh); the
**curtailment** is missing. The accurate input is SPP's published curtailment; the model is running
without it.

## 3. RULE 19 `[R-ONE-MECH]` — REPLACEMENT, ENFORCED IN CODE

Three mechanisms answer "where does SPP's measured curtailment land":

| mechanism | status in keeper 7 | under the arm |
|---|---|---|
| flat gross-up (`_forecast_uncurtailed_cf`) | fallback basis | **basis reverts to it** |
| `vre_curtailment_oversupply_allocation` | **ARMED** (cell `K`, SPP-51c) | **SUPERSEDED — disarmed in code** |
| `spp_curtailment_ceiling` | off | **ARMED — sole owner** |

`data/renewables.py` skips the oversupply allocation whenever the ceiling is armed
(`and not _spp_ceiling`), so **the two can never both be live in one solve, whatever a recipe asks
for.** No stacking. Nothing else floors, ceilings or prices SPP wind: SPP carries no wind must-take,
no PTC offer vintage (`wind_ptc_vintage_offers` = `I`), and `negative_renewable_offers` = `I`.

## 4. SCREEN YEAR — **2025**, named by MEASURED FOOTPRINT, before any solve

Rule 29 `[R-SCREEN]` (1): the screen year is the year the mechanism's **own measured footprint is
largest**, never the residual year. Computed **zero-LP** in the parent by applying
`spp_curtail_multipliers` at the declared depth to each year's reconstructed wind bound, using the
identical net-load construction the solve uses (`demand.sum(0) − wind_pot.sum(0) − solar_pot.sum(0)`):

| year | bound (potential) | ceilinged bound | **REMOVED** | implied real curtailment | ceiling/real |
|---|---|---|---|---|---|
| 2023 | 114.0552 | 102.8111 | **11.2442** | 11.0062 | 1.022 |
| 2024 | 120.9925 | 108.8994 | **12.0931** | 11.6755 | 1.036 |
| **2025** | **122.2552** | **109.8996** | **12.3556** | **11.7982** | **1.047** |

**2025 is the largest footprint and is deliberately NOT a failing-residual year** — the failing C1
rows are 2023 and 2024, and 2025's ST_GAS row is unscorable (preliminary EIA-923). The screen
therefore cannot be read as chasing the target residual even by accident.

*Stated as an estimate, not a prediction to the decimal:* SPP-58's solved 2024 arm measured the bound
falling 11.766 TWh where this construction gives 12.093 (2.7 % apart). The difference is the
within-year net-load decile ranking over near-ties plus the solve's own post-COD-mask bound. G-2's
band is set wide enough that this cannot decide it.

## 5. THE STOP GATES — STRUCTURAL, STOP-ONLY, AND NONE READS C1

Rule 29: these may **kill** the arm; they may **never promote** it, and none is gated on the target
residual. **C1 and the ST_GAS rows are read NOWHERE below.**

| gate | asks | PASS requires |
|---|---|---|
| **G-1** config identity & liveness | the arm is the arm | `run_config` shows `spp_curtailment_ceiling: true`, `spp_curtail_depth_wind: 0.288137`; ten fossil classes at 0.93 × 4 bands; `wc -l coal_supply_SPP.csv` = 32; `grep -c "^6193,prb,"` = 1; **the log does NOT contain `oversupply curtailment allocation`** (the rule-3 supersession is the empirical proof the flag reached the solve — SPP-58's own liveness test, and the defect that wasted its first shard) and **does NOT contain `ceiling skipped`** |
| **G-2** reach | the dispatch response has the direction and order of magnitude the pre-solve delta implies | 2025 wind **dispatch** falls by **9.0–15.0 TWh** vs the control's **122.0430** |
| **G-3** the identity it asserts | the ceiling binds where its own driver says, not uniformly | lowest-net-load decile carries **> 1.15 ×** the share of the removal a flat cut implies |
| **G-4** no new forcing | the arm does not buy its answer with unserved energy | `dump` **= 0.000 MWh** AND `slack` **≤ 100.0 MWh** (control 2025 slack = **0.0000**) |
| **G-5** no load-bearing regression | nothing non-target breaks | no non-target load-bearing (**C2, C3a, C3b, C4**) or protective (**C6, C8**) criterion flips PASS → FAIL in 2025 |

**Control values for 2025, from the keeper's committed sidecars** (re-derived this session): wind
dispatch **122.0430** TWh, slack **0.0000** MWh, dump **0.0000** MWh, load-weighted price
**$29.2249**, negative-price hours **167**. C3a **+2.2 %** (band ±10 %), C3b NRMSE **0.167** (band
≤0.20), C4 gas **r 0.949 / NRMSE 0.253**, coal **r 0.912 / NRMSE 0.177** (bands r ≥ 0.70,
NRMSE ≤ 0.30).

**G-5 is the gate with real bite, and it is declared as such now.** Removing ~12 TWh of zero-cost
wind raises prices and removes the negative-price regime (SPP-58's 2024 arm: negative-price hours
**214 → 0**). C3b's headroom is **0.033** and C4-2025 gas NRMSE's is **0.047**. If G-5 fails,
**the span is not spent** and the regression is reported as this lane's result.

**What a G-5 failure does NOT mean, pre-registered so it cannot be re-read afterwards.** Under rule 1
`[R-STRUCT]` a structurally-correct mechanism is never rejected because the fit moved. A G-5 stop is
a **spend decision** — it says the root cause behind the regression must be found before three years
of LP are committed — and it is **not** a verdict of `R` on the mechanism. The matrix cell would go
to `O`, not `R`.

## 6. G-DRIFT — rule 29(b) form 4 is VALID; NO CONTROL SOLVE IS SPENT

`git diff 67feede7…24737d3c` over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` is
**8 files, +1,235 / −2**. Every hunk classified **INERT for the control**:

| file | Δ | classification |
|---|---|---|
| `data/raw/reference/spp_curtailment_share.csv` | +867 | **INERT off** — new table, read only under the armed flag |
| `scripts/run_calibration_full.py` | +62 | **INERT off** — CLI flags, `None`-gated |
| `scripts/run_calibration.py` | +65 | **INERT off** — backcast leg guarded `if config.spp_curtailment_ceiling and iso == "SPP"` |
| `src/market_sim/config/scenarios.py` | +62 | **INERT off** — two new fields, both declared in the frozen cache-key drop dict at their defaults (`"False"` / `"0.288137"`), so an unarmed run's key is unchanged |
| `src/market_sim/data/curtailment_share.py` | +113 | **INERT off** — new SPP functions, called only under the flag |
| `src/market_sim/data/renewables.py` | +19/−2 | **INERT off** — adds `and not _spp_ceiling`; with the flag off the predicate is identical |
| `src/market_sim/model/interchange/spec.py` | +20/−2 | **INERT absolutely** — **comment-only** (miso-252), zero executable change |
| `src/market_sim/runner.py` | +29 | **INERT twice over** — forecast leg (`run_scenario_iso`), which a `mode="backcast"` run never enters, AND behind `iso == "SPP" and flag` |

**Corroborations** (§7 of the shard protocol): keeper 7's `basis_sha`
`67feede7403240374091cc73a536d836ba6d08c4` **resolves**; the capx-D79 **SPP solve-surface fingerprint
`moved_rows("SPP")` is `{}`** — zero rows moved at HEAD. `tests/unit/data/test_spp_curtailment_ceiling.py`
**6 passed**, including SPP-58's two-sided CLI-delivery guard.

## 7. DOF EFFECT — rule 21 `[R-DOF]`

The ledger goes **3 entries / 2 residual → 4 entries / 2 residual**. `spp_curtail_depth_wind`
= 0.288137 enters as a **ledgered free parameter whose identification source is MEASURED, not the
residual**: SPP's published curtailment MW (SPP MMU ASOM,
`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`), pooled energy-weighted across 2023–2025 —
**ONE config across every scored year, set ex ante here, and never swept against any gate above.**
`n_residual` does **not** rise: this is not the authorized offer-curve channel and it is not tuned on
price or volume. `spp_curtailment_ceiling` itself is a boolean gate, not a parameter.

## 8. THE SOLVES — rule 32 `[R-SHARD]`

The parent runs **NO LP**. SPP solves ~150 s/year and ~440 s for the span, so each shard is far
inside the 20-minute budget.

```
SCREEN  claude/spp63-screen-2025   results/calibration/spp63_screen_2025   ~150 s
  python3 scripts/replay_keeper.py results/calibration/spp62_span \
    --years 2025 --out-dir results/calibration/spp63_screen_2025 \
    --set spp_curtailment_ceiling=true

SPAN    claude/spp63-span          results/calibration/spp63_span          ~440 s
  python3 scripts/replay_keeper.py results/calibration/spp62_span \
    --years 2023 2024 2025 --out-dir results/calibration/spp63_span \
    --set spp_curtailment_ceiling=true
```

**The SPAN is the only registerable bundle** (protocol §3: per-year bundles carry different
year-scoped input snapshots and cannot be composed). The screen is a **throwaway probe** — never
registered, never a keeper, never quoted as a keeper number — and its year is re-solved inside the
span. Both families are **gitignored** (`results/calibration/spp63_*/`), which is what discharges
rule 29(c); **rule 31 `[R-RETAIN]` forbids `rm`**, and nothing will be deleted before the owner rules.

**KNOWN TRAP, pre-declared:** `replay_keeper.py --out-dir` does **not** propagate
`calibration_attestation.json`, so the bundle scores **C6 UNATTESTED** unless the parent authors it.
`scripts/gen_spp63_attestation.py` will inherit keeper 7's ledger, add the entry in §7, and re-point
`attested_by` at this lane.

## 9. WHAT THIS LANE PRE-COMMITS TO REPORTING, WHATEVER THE RESULT

- **The ceiling alone is not expected to close the ST_GAS rows.** SPP-58's 2024 arm moved ST_GAS only
  **+0.801** of 11.5 TWh, most of it going to CC_REGULAR and COAL_PRB. On keeper 7's **harder** basis
  (the vintage repair took ST_GAS 11.970 → 10.386) the arithmetic projection is ≈ **−8.9 TWh**,
  **still outside the ±8.00 band**. If C1 still fails, that is the expected outcome and **not** a
  reason to re-cut the depth — re-cutting it against a gate is exactly the fitted-mechanism selection
  rule 1 `[R-STRUCT]` condition (c) forbids, and this lane will not do it.
- Whether the negative-price regime survives, and what C3a / C3b / C4 do, **at full magnitude**.
- Registration under rule 15 `[R-DASHBOARD]` **whatever the span says** — keeper or rejection.
- The **promotion question** put explicitly in-session (rule 31), with the bundles on local disk and
  the statement that they do not survive this container.
- **CALIBRATED is the scorer's to produce.** The `complete` marker and any `frontier` declaration are
  OWNER acts and are neither added, requested nor implied. `[R-HOLDOUT]` was removed 2026-09-09, so
  no year is protected from being iterated against and every number here is model-**SELECTION**
  evidence.
