# RESULT — SPP-27 SCREEN, 2023. **SIX OF SIX STOP GATES PASS. The span is authorized.**

**Lane** SPP-27 · **Charter** `docs/handoffs/PRECOMMIT-spp-27-commitment-grain-2026-09-10.md` (pushed
at `32dfd75e`, **before** any LP) · **Addendum**
`docs/handoffs/ADDENDUM-spp-27-registration-seam-2026-09-10.md` · **Screen shard** pinned
`1d175c88b6f99738c4e32a96c3b6438d742335cb`, raw report
`docs/SHARDREPORT-spp27-screen-2023.md` · **Control** `2026-09-10-spp-64-stgas-selfcommit` /
`results/calibration/spp64_span`, **differenced, never re-solved** (rule 29(b) form 4; §7 of the
charter found ZERO solve-path drift).

Solve: `replay_keeper.py … --years 2023 --set mustrun_window_commitment_grain=true`, exit 0,
**311 s**. Rule 32 `[R-SHARD]`: the parent ran **no LP**.

---

## The gate table — every gate at full magnitude

| gate | bar (pre-registered) | measured | |
|---|---|---|---|
| **G-1** config identity | one live field; `st_gas_mustrun_p25_level` / `mustrun_online_frac_per_year` / `mustrun_layup_window_mask` / `mustrun_plant_exclusions` / `cc_mustrun_per_plant` all false; `offer_curve_by_group` byte-identical | **exactly ONE differing `scenario_config` key across the whole config — `mustrun_window_commitment_grain`** (control `None`, the declared default materializing; arm `True`). All five companions false. `offer_curve_by_group` byte-identical **True**. | **PASS** |
| **G-2** the window's own SHAPE | mechanism-16 floored-MWh-weighted diurnal peak-to-mean = 1.000 ± 0.005 | **1.2349 → 1.0000** | **PASS** |
| **G-3** the PHYSICS it implies (rule 18) | implied starts ≤ **647** (the fleet's measured 2023 runs) | **2,843 → 288** (0.45× the meter, from 4.39×) | **PASS** |
| **G-4** SIZE preservation — the "not a shrinkage repair" gate | floored energy (all-on) inside **[3.95, 4.20] TWh** | **3.870051 → 4.070490 TWh** (+5.18 %). Solved corroboration: D-2 realized forced energy **2.3238 → 2.555 TWh**, +9.9 % | **PASS** |
| **G-5** reach | dump = 0; no class other than ST_GAS acquires `min_gen`; slack ≤ 370.102 MWh | dump **0.0000** both; slack **0.0000** both; D-2 mechanism set unchanged (`nuclear_mustrun`, `chp_steam`, `st_gas_mustrun_per_plant`) with CC_REGULAR / COAL / CT_PEAKER / hydro all **0.0 %** forced; parent rebuild: mech 1 and 2 byte-identical and `max |Δ min_gen| = 0.000000` over every cell neither run tags ST_GAS-mustrun | **PASS** |
| **G-6** no non-target load-bearing regression | C3a within ±10 %, C3b ≤ 0.20, C2 in band, **C1 not PASS → FAIL** | C3a **+1.0 % → +0.9 %** (PASS→PASS); C3b **0.173 → 0.173** (PASS→PASS); every C1 class stays in band by a wide margin (below) | **PASS** |

**Where each number was measured, stated so the substitution is visible.** G-1, G-5's dump/slack,
G-6 and the D-diagnostics are from the **shard's solved bundle**. G-2, G-3, G-4 and G-5's `min_gen`
leg are properties of the **fleet arrays**, which the config alone determines; the parent measured
them at **zero LP** by rebuilding the control's recipe with the one override
(`run_year(fleet_only=True)` via `scripts/lib/bundle_fleet.py`), which is the same configuration
G-1 then proved the shard solved. The charter said the parent would rebuild the *shard's own returned
bundle*; the shard commits no bundle (it is gitignored, rule 29(c)), so the parent rebuilt the
control-plus-override instead. G-1's exactly-one-differing-key result is what makes the two the same
object. **The SPAN shard commits its bundle's slim files, so the span gets the chartered form.**

## C1 — every class, and nothing leaves the band (gross P1 TWh)

| class | control | ARM | Δ |
|---|---|---|---|
| **ST_GAS** | 9.4181 | **9.6983** | **+0.2801** |
| COAL_PRB | 65.8052 | 65.6343 | −0.1709 |
| CC_REGULAR | 41.9243 | 41.8267 | −0.0976 |
| CT_PEAKER | 15.7407 | 15.7601 | +0.0195 |
| COAL_LIGNITE | 7.1926 | 7.1781 | −0.0145 |
| **wind** | 113.7422 | 113.7294 | **−0.0128** |
| CC_CHP / CT_CHP / ST_CHP | 1.8477 / 1.2034 / 0.2926 | 1.8472 / 1.2030 / 0.2922 | −0.0005 / −0.0004 / −0.0004 |
| nuclear / hydro / biomass / solar / OTHER / oil | — | — | **0.0000** each |
| **TOTAL** | 284.6338 | 284.6364 | **+0.0026** |

The increment is paid by coal and CC_REGULAR and **not** by curtailing wind (−0.011 %). Against the
keeper's own scored 2023 row (ST_GAS grid-delivered 8.986 against 15.020 actual, Δ **−6.034** TWh,
band ±8.00), a +0.28 TWh gross increment moves the row **toward** the actual and no class comes near
the band edge. **C1 cannot flip PASS → FAIL on this year**, which is what G-6's one-sided leg asked.
It is reported, and it is **not** evidence for the mechanism: no gate reads it and rule 1
`[R-STRUCT]` forbids treating a residual move as a warrant.

## The TARGET — D-4, reported in full, read by NO gate

`D4.passed = False` on both the arm and the keeper. The 2023 conduct-FAIL set is **identical**:
plants **1230, 1235, 1271, 3008** — four rows on both runs.

| plant | keeper `measured_zero_share` | **ARM** | |
|---|---|---|---|
| 1230 Cimarron River | 0.7018 | **0.6096** | improves 0.092 |
| 1235 Great Bend | 0.6230 | **0.5606** | improves 0.062 |
| 1271 Coffeyville | 0.6976 | **0.5875** | improves 0.110 |
| **3008 Mooreland** | 0.5357 | **0.6002** | **worsens 0.065** |

**This is exactly what the charter predicted before the solve, in both directions.** The three
flat-profile plants move materially toward the 0.50 bar without crossing it; **Mooreland — the one
plant in the fleet whose measured online hour-of-day profile is genuinely two-shifted (peak-to-mean
1.609 against 1.007–1.146 for the other 21)** — moves away from it, because a uniform whole-day
window is the wrong grain for a daily cycler. It is **not** special-cased: a per-plant grain
predicate needs a threshold, which is a free parameter (rule 21 `[R-DOF]`), and choosing it against
this statistic is the fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids.

**So the arm does not close card R-be on 2023, and this lane says so rather than reframing it.**
What it does close is the structural half: the floor's diurnal shape (G-2) and the starts it asserts
(G-3).

## The other diagnostics, reported

- **C8 / rule 20 `[R-FORCED-BUDGET]`:** ST_GAS forced share **0.1962 → 0.2112** against
  `d2_merchant_max_share` 0.30. Still under, so the rule's conditional-pass limb is again not
  reached. Every other class stays **0.0 %** forced — rule 19 `[R-ONE-MECH]` holds on the solved
  artifact, not just the pre-solve census.
- **D-1:** `D1.passed = True`. ST_GAS `profile_r` **0.997 → 0.987** (bar 0.80) and `cv_ratio`
  **2.117 → 1.672** (bar 0.50, one-sided) — the ratio moves further **toward** 1.0, i.e. the model's
  off-peak ST_GAS variability moves toward the measured. The `profile_r` slip is real and is reported;
  it is nowhere near its bar.
- **C3c is mechanically frozen:** the system price max is **59.3126 in both runs**, so not one tail
  hour could have moved. C3c is untouched by this arm and remains card R-bd.

## Two notes carried forward

1. **A container-environment finding, not a repo change.** The shard's container had no Python
   dependencies installed (`ModuleNotFoundError: numpy`); it ran `uv sync` and solved with
   `.venv/bin/python`. Nothing under `src/` or `scripts/` was touched. The SPAN shard is told to do
   this first.
2. **A duplicate screen shard exists.** The parent misread the wall clock, judged the first screen
   shard stalled and launched a second, leaner one; the second is the one reported here. The first
   was **not** interrupted or deleted (rule 31 `[R-RETAIN]`). Cost: one duplicated ~5-minute LP,
   recorded rather than tidied away.

**RULE 29 `[R-SCREEN]`: the screen may kill an arm and may never promote one. It did not kill it, so
the full span is authorized — and nothing in this document is a promotion argument.**
