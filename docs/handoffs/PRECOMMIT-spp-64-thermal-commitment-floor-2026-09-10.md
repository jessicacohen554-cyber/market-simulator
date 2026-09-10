# PRECOMMIT — SPP-64: SPP has NO commitment floor, and that is what R-bb is

**Lane** SPP-64 · **Base / pin** `2a267cc44f01fad85cc1be8fca329ea34d78bb53` ·
**Control** keeper 7 `2026-09-10-spp-62-vintage-census`, bundle `results/calibration/spp62_span`
(committed WITH `hourly/` sidecars — differenced against, NEVER re-solved) ·
**Written and pushed BEFORE ANY SOLVE.**

**CHARTER** `RESULT-spp-63-screen-2026-09-10.md` §5 card **R-bb** — "SPP price formation without the
phantom wind". Root-caused below at **zero LP**.

---

## 0. TWO CORRECTIONS TO THE SPP-63 RECORD, BOTH MEASURED, BOTH AGAINST THIS LANE'S CONVENIENCE

A **three-year** ceiling arm now exists (`results/calibration/spp63_span`, gitignored, 2023+2024+2025,
ceiling live in all three at mean 0.9170 / 0.9146 / 0.9141, oversupply allocation superseded in all
three). It was launched in the SPP-63 shard container under the owner's in-session promotion
instruction, after the RESULT doc was written; that doc's "the span was NOT spent" and "no span bundle
exists" are **superseded as of this lane**. It cost this lane no LP and it changes two of SPP-63's
findings.

**(1) G-4's failure DOES NOT REPRODUCE. It was an artifact of the single-year bundle.**

| 2025 slack | MWh |
|---|---|
| keeper 7 | 0.000 |
| ceiling arm — **screen** bundle (SPP-63's G-4 input) | **211.208** |
| ceiling arm — **span** bundle, same config | **0.000** |

The screen and span disagree on 2025 because per-year bundles carry different year-scoped input
snapshots — `PRECOMMIT-spp-63` §8's own documented property, here biting the gate rather than the
composition. Worse for SPP-63's framing: **keeper 7 is not slack-free either.** It carries
**370.102 MWh in 2024** (SPP-South h7071 128.9 + h7072 241.2); the arm carries **364.929 MWh in the
same two zone-hours**. Span totals: keeper **370.102**, arm **364.929**, dump **0.000** both.
**On the span the arm's unserved energy is BELOW the control's, so G-4 as written PASSES.**

**(2) G-5's failure reproduces and is BROADER than the screen showed.** Scored with
`scripts/lib/spp63_g5.py`, first re-validated against `calibration_verdict.py` on keeper 7
(2023/2024/2025 C3a 25.65 / 25.79 / 29.23, C3b 0.172 / 0.172 / 0.167 — exact):

| year | C3a keeper | C3a arm | C3b keeper | C3b arm (band ≤0.20) |
|---|---|---|---|---|
| 2023 | +2.1 % | +9.3 % | 0.172 | **0.241 FAIL** |
| 2024 | +1.3 % | +7.4 % | 0.172 | **0.240 FAIL** |
| 2025 | +2.2 % | +8.5 % | 0.167 | **0.243 FAIL** |

C3a passes in all three (all near the ±10 % edge). **C3b fails in all three, not one.** Note the
registerable 2025 C3b is **0.243** (span), not the 0.253 the RESULT doc headlines from the screen.

## 1. THE ROOT CAUSE — SPP IS THE ONLY ISO IN THE MODEL WITH NO COMMITMENT FLOOR

`iso_configs.RELIABILITY_FLOOR_REGISTRY`, read at HEAD:

| ISO | ERCOT | MISO | PJM | NYISO | NEISO | CAISO | **SPP** |
|---|---|---|---|---|---|---|---|
| limbs | 48 | 78 | 61 | 46 | 34 | 19 | **0** |

The LP therefore has a free choice in every low-net-load hour between spilling wind and decommitting
thermal, and it decommits thermal — **below anything SPP's own meter has ever shown.** Measured
EIA-930 `SWPP_fueltype.parquet` against keeper 7's committed sidecars:

| 2025 | measured min | measured p1 | keeper model min |
|---|---|---|---|
| coal | **2,128 MW** | 3,180 | **0.0** |
| gas | **2,236 MW** | 2,955 | 103.9 |

**Hours the keeper runs a fuel below its own measured annual minimum**, and the energy it books there:

| year | coal hours | gas hours | coal TWh | gas TWh |
|---|---|---|---|---|
| 2023 | 470 (5.37 %) | 1,120 (12.79 %) | 0.4622 | 0.9980 |
| 2024 | 873 (9.97 %) | 1,256 (14.34 %) | 0.9622 | 1.7172 |
| 2025 | 490 (5.59 %) | 1,748 (19.95 %) | 0.6371 | 2.3296 |

In the **200 cheapest** load-weighted hours of 2025 the keeper's whole ~40 GW thermal fleet averages
**1,120.7 MW** (min **157.4**; coal reaches **0.0**). No commitment state produces that.

## 2. THAT ONE DEFECT EXPLAINS BOTH HALVES OF R-bb

**(a) The keeper's negative-price regime is MANUFACTURED by the decommitment.** Negative prices are
almost entirely **exactly −$26.000/MWh** — wind's own §45 PTC offer, i.e. **wind is the marginal
unit** — in **291 of 318** negative zone-hours (2025; 423/423 in 2023, 370/370 in 2024). But wind
only reaches the margin *after* thermal has been driven to ~1.1 GW. The shape is right for a reason
the market does not use.

**(b) The ceiling cannot be marginal, so removing the phantom wind removes the whole regime.** The
ceiling lowers wind's CF **upper bound**, so wind sits AT that bound and can never set price. Measured
zonal price floor, 2025:

| | keeper | ceiling arm |
|---|---|---|
| min zonal price | **−26.000** | **+18.318** |
| zone-hours at exactly −26.000 | 291 | **0** |
| negative zone-hours | 318 | **0** |

Real curtailment is the LP's **endogenous response** to a negative offer; the ceiling implements it as
an **exogenous bound**. Same energy, wrong instrument — and the instrument is what price formation runs on.

**(c) The corroboration that settles which mechanism is at fault.** The ceiling, incidentally and with
no gate looking, **repairs the decommitment it is being blamed for**:

| hours below measured minimum | keeper → ceiling arm |
|---|---|
| coal 2023 / 2024 / 2025 | 470 → **0** · 873 → **46** · 490 → **0** |
| gas 2023 / 2024 / 2025 | 1,120 → **109** · 1,256 → **170** · 1,748 → **438** |
| coal energy below min, 2025 | 0.6371 → **0.0000 TWh** |

And its wind lands almost exactly on measured in all three years: **+0.098 / −0.085 / −0.232 TWh**
against EIA-930, from **+10.708 / +11.407 / +11.586**. **The ceiling is not the defect. The absent
floor is.**

**(d) The 211 MWh of slack was a REAL locational signal, not a numerical artifact** — worth recording
even though §0 shows it does not survive into the span. In screen h8507/h8508 the N→S link is pinned
at **3,400 MW** with dual **−1,979.765** (= VOLL 2000 − SPP-North's **20.235**): cheap energy stranded
behind a full pipe while SPP-South sheds load. **h8508 is the same hour SPP-57b independently flagged**
(`unserved 89 → 444 MWh, new hour h8508`). Three lanes, one pressure point → routed to the SPP
topology desk as **R-bc**, not absorbed here.

## 3. THE OBJECT, AND THE ONE SEAM

**`coal_mustrun_per_plant`** (bool, dataclass default `False`, matrix cell **`U`** for SPP) armed for
SPP, with **SPP's coal plants given rows in `fleet.COAL_MUSTRUN_BY_PLANT`** derived from **each
plant's own CAMPD unit-level meter** (`data/raw/campd-unit-level/<STATE>_<year>.parquet`), by the
construction already in `data/raw/_processed-legacy/coal_mustrun_floors.csv`
(`minload_pct_of_max`, `online_share`, `cf_p5`). One seam: the per-plant must-run percentage the
tranche builder reads. **Zero new `ScenarioConfig` fields, zero new tunables** (rules 21 / 24).

**Rule 25 `[R-ISO-SCOPE]` is satisfied by construction, not by assertion:** the table is keyed by
`plant_code` and every value is that plant's own measured floor. The CSV's 10 incumbent rows are
ERCOT plants and **not one of their numbers is read by an SPP plant**; SPP plants absent from the
table today fall back to the uniform CSV/override path, which is exactly the current keeper behaviour.

**THE DERIVATION RECIPE IS FIXED HERE, EX ANTE, AND IS NEVER SWEPT.** Floor per plant =
`minload_pct_of_max` computed as that plant's **p5 of hourly gross load / max observed gross load**
over 2023–2025 CAMPD hours in which the plant is online (gross load > 0) — the identical statistic
and percentile the incumbent rows carry. **One value per plant, one config across every scored year.**
No level is selected against any gate; a gate-selected floor is the fitted-mechanism selection rule 1
`[R-STRUCT]` condition (c) forbids and this lane will not do it.

## 4. RULE 19 `[R-ONE-MECH]` — WHAT ELSE FLOORS SPP COAL TODAY: NOTHING

| mechanism | SPP status at HEAD | under the arm |
|---|---|---|
| `reliability_floor` | registry has **0 SPP limbs** — inert whatever the flag | untouched, still inert |
| `coal_mustrun_per_plant` | off; **no SPP rows in the table** | **ARMED — sole owner** |
| `coal_lignite_mustrun_override` / `coal_prb_mustrun_override` | `None` in keeper 7's recipe | untouched (`None`) |
| `ercot_coal_min_config_floor` | ERCOT-scoped (rule 25) | `·` n/a |
| `spp_gas_commitment_bridge` | **`R`**, SPP-44 | **NOT re-armed** — see below |
| `spp_curtailment_ceiling` | `O`, off in keeper 7 | **NOT armed in this screen** — see §5 |

**Rule 28(a) DO-NOT-REDO, stated explicitly.** `spp_gas_commitment_bridge` is `R` and is not
re-tested. This object is distinguishable on all three axes SPP-44's own kill turned on: it is
**coal**, not gas (coal is the class measured at 0.0 MW); it is a **measured commitment-state floor**,
not a **P0-pattern bridge** — SPP-44's stated re-test condition is verbatim *"a MEASURED
commitment-state membership … never this leg re-armed on the P0 pattern"*; and its target is **price
formation**, not the ST_GAS volume. SPP-44's structural reading ("a bridge can only refuse to STOP a
unit the model started") is precisely why a *floor* and not a *bridge* is the instrument.

## 5. SCREEN YEAR — **2025**, NAMED BY MEASURED FOOTPRINT, BEFORE ANY SOLVE

Rule 29 `[R-SCREEN]` (1). Footprint = energy a measured thermal floor would ADD on keeper 7's own
committed dispatch, computed zero-LP at four candidate measured levels:

| level | 2023 | 2024 | **2025** |
|---|---|---|---|
| measured min | 1.4602 | 2.6795 | **2.9667** |
| measured p1 | 3.1419 | 4.6461 | **5.0014** |
| measured p5 | 6.0201 | 7.1807 | **7.6962** |
| measured p25 | 14.7851 | 16.1110 | **17.1807** |

**2025 is the largest at every level** — a rank robust to the level choice. It is **deliberately not a
failing-residual year**: the failing C1 `ST_GAS` rows are **2023 and 2024**, so the screen cannot be
read as chasing the target residual even by accident.

**The ceiling is NOT armed in this screen** (rule 19: one mechanism at a time, and the floor must be
measurable alone before any reconciliation). The floor-plus-ceiling reconciliation is this lane's
successor question, not its screen.

## 6. THE STOP GATES — STRUCTURAL, STOP-ONLY, AND **NONE READS C3b OR C1**

C3b is this lane's **target** residual, so no gate below reads it; nor does any read C1. These may
**kill** the arm and may **never promote** it.

| gate | asks | PASS requires |
|---|---|---|
| **G-1** identity & liveness | the arm is the arm | `run_config` shows `coal_mustrun_per_plant: true`; the SPP coal plants carry table rows; ten fossil classes at 0.93 × 4 bands; `coal_supply_SPP.csv` 32 lines / `^6193,prb,` = 1 |
| **G-2** reach | the floor does what its own arithmetic says | coal hours below the measured annual minimum fall from **490** to **≤ 100** in 2025 |
| **G-3** the identity it asserts | the floor makes wind spill **endogenously**, which is the whole point | interior-wind hours (wind strictly inside its bound) **rise above 3**, and the zonal price in those hours is **exactly −26.000** |
| **G-4** no new forcing | the floor does not buy its answer with unserved energy | `dump` = 0.000 MWh AND 2025 `slack` ≤ 100.0 MWh (keeper 2025 = 0.000) |
| **G-5** no non-target load-bearing regression | nothing non-target breaks | no non-target load-bearing (**C2, C3a, C4**) or protective (**C6, C8**) criterion flips PASS → FAIL in 2025. **C3b and C1 are excluded as targets and are REPORTED at full magnitude, never gated.** |

**Declared now so it cannot be re-read later:** G-3 is the gate with real bite. If the floor raises
thermal without making wind marginal, the mechanism has not reached its object and the arm dies there
whatever C3b does. And a floor at the measured **min** closes only **25.6 %** of 2025's wind gap
(p5: 66.4 %) — **this lane does not expect the floor alone to close the wind row**, and will not
re-cut the percentile to make it.

## 7. G-DRIFT — RULE 29(b) FORM 4 IS VALID; NO CONTROL SOLVE IS SPENT

`git diff 67feede7…2a267cc4` over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` =
**13 files, +1,747 / −10**. Every hunk **INERT for an SPP backcast**:

| file | Δ | classification |
|---|---|---|
| `pipeline/ttc.py` | +33/−? | **INERT absolutely** — the changed block's first statement is `if iso != "NYISO": return ttc` |
| `config/constants.py` | +171 | **INERT absolutely** — the sole added symbol is `NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH` |
| `config/solve_surface_declared.py` | +4 | **INERT** — one declared drop value for that NYISO table |
| `config/scenarios.py` | +113 | **INERT off** — three new fields, all default-off/absent from keeper 7's recipe (`spp_curtailment_ceiling` False, `spp_curtail_depth_wind`, `nyiso_total_east_cutset_ttc` False) |
| `data/curtailment_share.py`, `data/raw/reference/spp_curtailment_share.csv` | +113 / +867 | **INERT off** — reached only under the ceiling flag, which this screen does not arm |
| `data/renewables.py` | +19/−2 | **INERT off** — adds `and not _spp_ceiling`; identical with the flag off |
| `runner.py` | +29 | **INERT twice** — forecast leg, and behind `iso == "SPP" and flag` |
| `scripts/run_calibration{,_full}.py` | +69 / +62 | **INERT off** — `None`-gated CLI flags |
| `model/interchange/spec.py` | +63/−2 | **INERT** — comment-only (miso-252) |
| `scripts/lib/spp63_g5.py`, `forecast_parity_registry.py` | +144 / +70 | **INERT** — scoring/forecast instruments, not on the solve path |

**Empirical corroboration, stronger than the audit:** the capx-D79 SPP solve-surface fingerprint
`moved_rows("SPP")` is **`{}` — zero rows moved at HEAD**. Keeper 7's `basis_sha` `67feede7` resolves.

## 8. DOF EFFECT — RULE 21 `[R-DOF]`

Ledger **3 entries / 2 residual → 3 entries / 2 residual: UNCHANGED.** The arm sets **no value**. The
per-plant floors are not free parameters: each is one plant's own measured `minload_pct_of_max` from
its own CAMPD meter, on a recipe fixed in §3 before any solve, re-derivable only when the CAMPD source
updates (rule 23 `[R-FROZEN-DERIVE]`). `coal_mustrun_per_plant` is a boolean gate, not a parameter.
Keeper 7's `authorized_price_tuning` block (uniform 0.93, ten fossil classes) is **replayed verbatim,
not re-cut, and not swept** — SPP-52a already measured it a pure LEVEL lever (flat to 0.12 pp across
three years), so it cannot repair a SHAPE criterion and this lane does not touch it.

## 9. WHAT THIS LANE PRE-COMMITS TO REPORTING, WHATEVER THE RESULT

- **C3b and C1 at full magnitude**, as reported-not-gated targets, in the screen year.
- That the floor is expected to close only **~26–66 %** of the wind gap depending on percentile, and
  that a shortfall is **not** grounds to re-cut the percentile.
- Registration under rule 15 `[R-DASHBOARD]` if and only if a span is spent; a screen is never registered.
- **The promotion question put explicitly in-session** (rule 31 `[R-RETAIN]`), naming that
  `spp63_span`, `spp63_screen_2025` and this lane's bundles are gitignored, sit on local disk, and
  **do not survive this container**.
- `CALIBRATED` is the scorer's to produce. No `complete` marker and no `frontier` declaration is
  added, requested or implied. `[R-HOLDOUT]` was removed 2026-09-09, so **no year here is
  out-of-sample** and every number is model-SELECTION evidence.
