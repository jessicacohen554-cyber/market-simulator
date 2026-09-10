# PRECOMMIT — pjm-d4-3: the DA-virtual layer's own admissibility premise, and the ONE screen it earns

**Session** `pjm-d4-3` · **ISO** PJM · **Date** 2026-09-10 · **Branch** `claude/pjm-d4-3-1o5yev`
**Incumbent keeper** `2026-09-10-pjm-d4-2-stgas` (2023-2025, **CALIBRATED**, 0 caveats) +
`2026-09-10-pjm-d4-2-touchpoint` (2020-2022, NOT-YET), folded under rule 30(a). **UNCHANGED by
this session unless the owner rules otherwise.**

**Committed and pushed BEFORE the screen shard is launched.** Every gate bar, the screen year, the
control posture and the rule-1 non-gates below are fixed here and are quoted unchanged in the
RESULT.

---

## 1. WHAT PHASE 0 FOUND (zero LP, committed artifacts + the gitignored raw PJM corpus)

### 1a. The CC_REGULAR surplus decomposes into TWO legs, and only ONE is holdout-distinctive

Per plant-hour, model `m` vs CAMPD meter `c`, `on` = > 1 % nameplate + 1 MW, decoded exactly as
`legitimacy_diagnostics` decodes the payload and the bench (`a` = model on / meter off, `b+` =
both on and model above, `b-` = both on and model below, `c` = meter on / model off; identity
`a + b+ - b- - c == model - meter` holds to ≤ 4.5 GWh in every year):

| year | net | **hours leg** `a - c` | **loading leg** `b+ - b-` |
|---|---|---|---|
| 2020 | +17.887 | **+16.407** | +1.482 |
| 2021 | +36.661 | **+18.450** | **+18.215** |
| 2022 | +33.913 | **+14.385** | **+19.531** |
| 2023 | +12.764 | +8.816 | +3.950 |
| 2024 | +10.079 | +8.347 | +1.736 |
| 2025 | +11.601 | +6.428 | +5.177 |

The **hours** leg is chronic — elevated in every year, ~2× in the holdout span. The **loading**
leg is 3.5-11× larger in 2021/2022 than in any training year and is essentially absent in 2020.
**2020 is a different animal from 2021/2022**, as pjm-d4-1 §10 predicted from the composition.

### 1b. CC_REGULAR is NOT forced — the holdout surplus is ECONOMIC

D-2 rows, `class == CC_REGULAR`, all six years, from the committed
`legitimacy_diagnostics.json` of both bundles. `cc_mustrun_per_plant` forces
**9.444 / 6.409 / 9.429** TWh in 2020/21/22 against **23.758 / 13.338 / 10.523** in 2023/24/25;
`reliability_floor` is ≤ 0.058 TWh in every year. **Forcing is LOWER exactly where the surplus is
LARGER.** This card is therefore not a rule-17 `[R-FLOOR-WINDOW]` object and not a rule-19
`[R-ONE-MECH]` object; it is an offer / demand / merit-order object.

### 1c. THE FINDING — the DA-virtual layer's stated admissibility premise is FALSE in 2020-2022

`src/market_sim/data/virtual_bids.py`'s module docstring states the symmetric-net form's
admissibility, verbatim:

> "the annual net of the whole curve cleared at actual DA prices is ≈ 0 (**−0.6/−0.9/+1.3 TWh
> 2023/24/25**, vs the one-sided clamp's **+10.3/+14.8/+17.2 TWh of phantom demand**)"

That number was measured on 2023-2025 and generalised. Recomputed for all six years from the
module's **own** loader (`_load_bids_frame` — no curve is reimplemented), with
`net(λ) = Σ_{DEC ≥ λ} MW − Σ_{INC ≤ λ} MW`:

| year | **net @ ACTUAL DA price** | net @ model price | **realized in the LP** | gross DEC / INC (TWh) |
|---|---|---|---|---|
| 2020 | **+16.537** | +2.366 | **+2.414** | 78.0 / 58.7 |
| 2021 | **+16.812** | +10.527 | **+10.525** | 87.1 / 51.4 |
| 2022 | **+12.248** | +12.989 | **+13.013** | 105.7 / 70.4 |
| 2023 | −0.755 | −1.324 | −1.338 | 91.1 / 80.7 |
| 2024 | −1.620 | −1.711 | −1.713 | 114.2 / 97.8 |
| 2025 | +0.204 | +2.838 | +2.870 | 132.8 / 103.5 |

**Method validation, stated before it is used:** the `net @ actual DA` column reproduces the
docstring's own 2023/24/25 numbers in sign and order — measured **−0.755 / −1.620 / +0.204**
against the docstring's **−0.6 / −0.9 / +1.3**. The 2024 and 2025 differences (0.72 and 1.10 TWh)
are **not** reconciled here and are reported as a method caveat, not hidden: the docstring's
figures predate the model-clock and vintage this measurement uses. They do not affect the
conclusion, whose magnitudes are 12-17 TWh.

**Three things follow, and the third is the one that decides the card.**

1. **It is NOT a model-price artifact.** At the *actual* DA price the measured curve itself holds
   **+16.5 / +16.8 / +12.2 TWh** of net virtual DEMAND in 2020/2021/2022. The model's realized
   position is if anything *smaller* (2020: +2.4 against +16.5). So the phantom demand is the
   content of the measured input, not a feedback loop from the model's own dual.
2. **PJM's virtual market changed shape.** Gross INC nearly doubles from 51.4 TWh (2021) to
   103.5 TWh (2025) while gross DEC grows 1.5×; the DEC/INC ratio falls 1.69 → 1.28. The
   ≈ 0 annual net of 2023-2025 is a property of those years, not of the construction.
3. **In a SINGLE-SETTLEMENT LP scored against PHYSICAL generation, a non-zero net virtual
   position is served by physical units.** The layer injects **+13.013 TWh** of phantom physical
   demand into 2022 and **+10.525** into 2021 — **41.5 % and 41.6 %** of those years' fossil
   surplus (+31.38 / +25.31 TWh against `classFull`). Every one of those TWh is generated by a
   real unit in the model and scored against a benchmark that never contained it.

### 1d. What the layer does at the PEAKS — measured, because it decides the risk

Net virtual demand averaged over the model's own top-100 load hours: **+5.25 / +5.73 / +8.72 GW**
(2020-22) and **+9.44 / +9.18 / +8.81 GW** (2023-25) — i.e. the layer delivers the "~7-11 GW at
the top summer-load hours" its docstring designs for in **every** year, holdout included. The
years differ in the *off-peak* offset: the mean net position over the 2,000 lowest-load hours is
**−0.98 / −0.39 / −1.38 GW** (2020-22) against **−2.43 / −2.55 / −1.94 GW** (2023-25). **The
annual net fails to cancel in the holdout years because the off-peak supply side is thinner
there, not because the peak side behaves differently.**

### 1e. Two hypotheses this session tested and RETRACTS, so they are not carried forward

* **The flat diurnal price amplitude is NOT a holdout signature.** D-A reads 39.3 % / 34.4 % of
  measured in 2021/2022 — but **30.6 % / 29.0 % / 32.3 % in 2023/2024/2025**, the years PJM reads
  CALIBRATED. It is a chronic all-year model property. (2020, at 94.4 %, is the outlier the other
  way.) Any story keyed to it is refuted.
* **Demand and exports do not carry the surplus.** Model annual demand tracks EIA-930 to
  **+1.11 / +2.15 / +1.84 / −0.46 / −0.00 TWh** (2020, 2022-2025; the 930 2021 row is corrupt —
  4,902 TWh — and is not used). Model net exports are **BELOW** actual in 2021-2024
  (−13.59 / −8.65 / −8.65 / −10.07 TWh), which moves the surplus the *wrong* way and makes it
  larger, not smaller. Neither is the object.

---

## 2. THE CONTROL POSTURE — G-DRIFT IS RUNNABLE AGAIN, AND IT PASSES

pjm-177, `PRECOMMIT-pjm-fuelvintage-solve-2026-09-09.md` and pjm-d4-1 §2 all declared **G-DRIFT
NOT RUNNABLE for PJM** because the then-keeper's `git_sha` was dead after the 2026-08-16 history
rewrite. **That is no longer true.** `pjm_d4_2_TP.meta.git_sha` is
`5f133fd595aeb8d6c88058b566fce4b4e8b56e19` (2026-09-10, post-rewrite) and `git cat-file -t`
resolves it. G-DRIFT is run here for the first time in this lane, per rule 29 `[R-SCREEN]` (b):

`git diff 5f133fd5..HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib scripts/replay_keeper.py data/raw/_validation-source data/raw/reference`
= **13 files, 2,108 insertions, 22 deletions.** Every hunk classified:

| changed path | classification | reason |
|---|---|---|
| `src/market_sim/config/scenarios.py` | **INERT** | adds `spp_curtailment_ceiling=False`, `spp_curtail_depth_wind` (read only under that gate), `nyiso_hub_gap_month_level=False`, `caiso_dsw_lateevening_clean=False` — all default-off AND absent from PJM's recipe |
| `src/market_sim/data/curtailment_share.py` | **INERT** | new SPP-only module |
| `src/market_sim/data/renewables.py` | **INERT** | guarded `iso == "SPP" and spp_curtailment_ceiling` |
| `src/market_sim/runner.py` | **INERT** | same SPP guard (forecast leg) |
| `src/market_sim/data/fuel/hubs.py` | **INERT** | `nyiso_hub_gap_month_level`, default off, not in PJM's recipe |
| `src/market_sim/model/interchange/{__init__,caiso,spec}.py` | **INERT** | CAISO DSW late-evening injector — another ISO's branch |
| `scripts/run_calibration{,_full}.py` | **INERT** | SPP flag wiring + the `--replay-bundle` path/`--help` repair + removal of the `holdout_authorized` parameter (rule 22 coda) — no PJM solve-path behaviour |
| `data/raw/_validation-source/calibration_reference.json` | **INERT** | structural diff is exactly `ADDED /isos/MISO/2020` + the `generated` stamp; **zero PJM keys move** |
| `data/raw/_validation-source/MISO_2020_renewable_capacity.csv` | **INERT** | another ISO's per-ISO artifact |
| `data/raw/reference/spp_curtailment_share.csv` | **INERT** | SPP artifact |

**ALL HUNKS INERT ⇒ G-CTRL form 4 is VALID and the committed `pjm_d4_2_TP` bundle IS the
control. NO CONTROL SOLVE IS SPENT** (rule 29(b)). `data/outages.py` — which pjm-d4-2 edited — is
**not** in the diff, so the arm's fleet carries the identical `ST_GAS_PEAKER_PLANTS` membership as
the control.

---

## 3. THE ARM — a boolean flip of an existing registered field to its own dataclass default

    ScenarioConfig.pjm_da_virtual_bids : True (keeper) -> False (arm)

* **Zero new fields, zero free parameters, nothing to sweep** (rules 21 `[R-DOF]`, 24
  `[R-REGISTRY]`). There is no number in this arm. It adds **zero** DOF-ledger entries.
* **Rule 25 `[R-ISO-SCOPE]`:** PJM-gated field, PJM evidence, no other ISO touched.
* **Rule 19 `[R-ONE-MECH]`:** a removal cannot stack.
* **One config across every scored year** (rule 1 `[R-STRUCT]` (b)). A per-year gate — arming the
  layer in 2023-2025 and not in 2020-2022 — **is refused here, before any result is known**: that
  is per-year fitting, and the fact that it would obviously score better is the reason it is
  refused, not a reason to do it.

### 3a. The rule-13 `[R-MEASURED]` forward argument, stated BEFORE the arm is proposed

`virtual_bids.py`'s own docstring: *"The forecast-path wiring is not built yet — this flag lives
in the backcast calibration path only, like the other measured overlays."* **PJM's forecast
already runs with the layer OFF.** So the arm makes the dispatch being *validated* the dispatch
being *forecast* — which is rule 13's own test, met in the strongest available form. Nothing has
to regenerate forward, because the forward path is the arm.

This is the mirror image of `netload_drag_layup_window_mask`, which pjm-d4-1 §9a **refused even
though it cleared every gate** because it was backcast-only. Consistency requires that the same
standard be applied to a mechanism that is *already armed*, not only to a candidate.

### 3b. WHAT THIS ARM IS NOT, DECLARED NOW

**It is NOT proposed for promotion, and this is fixed before the solve so no result can move it.**
The pre-solve arithmetic says it cannot close the card:

* 2021 C1 CC_REGULAR is **+29.16 TWh (+10.4 % of class)**; removing 10.53 TWh of phantom demand
  leaves ~+19 TWh — still far outside any band that fails 2020 at +10.28 TWh (+3.6 %).
* 2022 C1 CC_REGULAR is **+26.82**; removing 13.01 leaves ~+14.
* 2020's COAL_BIT **+21.97 TWh** leg is untouched (the layer's 2020 realized net is only +2.41).
* It strips **8.7-9.4 GW** of top-100-hour DA procurement depth from the *training* years too
  (§1d), where the layer's annual net is already ≈ 0 — i.e. all of the price effect, none of the
  volume benefit. Rule 30(c) makes that a live threat to PJM's CALIBRATED headline.

**The screen is therefore a MEASUREMENT of attribution with a falsification test attached, not a
promotion path.** It exists to answer one question the committed artifacts cannot: *which classes
absorb the phantom demand when it is removed* — and to give my own +41.5 % attribution a chance to
be wrong.

---

## 4. THE SCREEN (rule 29 `[R-SCREEN]`) — ONE YEAR, NAMED HERE

**SCREEN YEAR = 2022.** Chosen as the year the mechanism's **own measured footprint is largest**
on the quantity this card is about — the **annual net virtual position**: 13.013 (2022) > 10.525
(2021) > 2.870 (2025) > 2.414 (2020) > 1.713 (2024) > 1.338 (2023) TWh. **It is NOT chosen for its
residual**, and the competing footprint measure (peak-hour depth) is explicitly named and rejected
as the wrong one for this card: by peak depth the largest year would be 2023 (9.44 GW), but this
card's object is the annual net, so the annual net selects the year. **Only 2022 is solved.
2021 is NOT spent**, and neither is any training year.

**Control:** the committed `results/calibration/pjm_d4_2_TP` bundle, year 2022 (§2). No control
solve.

### 4a. THE GATES — structural, STOP-only, declared here, never swept

Control values, from the committed bundle, P1, 2022 (TWh):
`CC_REGULAR 323.9474 · COAL_BIT 142.7099 · CT_PEAKER 15.3324 · ST_GAS 8.2465 · CC_CHP 7.4854 ·
COAL_PRB 10.3463 · COAL_WC 6.5766 · CT_CHP 1.3519 · ST_CHP 1.0979 · oil 0.0180 · hydro 8.9685 ·
nuclear 272.1869 · import −22.9888 · VIRTUAL_DEC −21.7187 · VIRTUAL_INC +8.7052 · demand 810.1881
· storage charge 6.3577 / discharge 5.0904` — gas family **357.4614**, coal family **159.6327**,
**net virtual demand +13.0134**.

| id | gate | bar |
|---|---|---|
| **G1** | **IDENTITY** — the override applied | the arm bundle's `class_hourly_2022.parquet` contains **no** `VIRTUAL_DEC` and **no** `VIRTUAL_INC` rows, and its `run_config.json` records `pjm_da_virtual_bids: false` |
| **G2** | **VOLUME RESPONSE** — direction + order of magnitude | Σ(fossil + hydro + net storage + import) falls by the removed net demand, **13.0134 TWh ± 15 % ⇒ [11.06, 14.96]**. The ±15 % is a tolerance on an *energy-balance identity* (exports and storage are LP-endogenous and may absorb part of it), fixed here, and is not a criterion |
| **G3** | **CONFINEMENT** | **≥ 60 %** of the fall lands on the gas family (`CC_*`, `CT_*`, `ST_GAS`, `ST_CHP`) — the marginal family in 2022 on the committed stack. Below 60 % **refutes** this card's CC_REGULAR attribution |
| **G4** | **NO NON-TARGET LOAD-BEARING FLIP** | on 2022, **C2** and **C4** must not go PASS → FAIL |

**A gate may KILL the arm. No gate can promote it** — §3b already fixed the disposition.

### 4b. EXPLICITLY NOT GATES (rule 1 `[R-STRUCT]`)

Whether **C1 CC_REGULAR** improves; whether **C3a mean LMP** or **C3b price shape** improves;
the size of any residual; the fossil surplus. All four are **REPORTED at full magnitude in the
RESULT, in both directions, and none of them can pass or fail this arm.** C1/C3a/C3b already FAIL
on 2022 in the control, so they cannot flip PASS → FAIL and are deliberately outside G4.

### 4c. What I expect to be WRONG about, said now

If G3 comes back below 60 %, the honest reading is that the phantom demand was being served by
**coal and imports** rather than by CC_REGULAR, and §1c's "41.5 % of the CC_REGULAR surplus"
becomes "41.5 % of the *fossil* surplus, allocated elsewhere". I will report that as a refutation
of my own attribution, not re-cut the gate.

---

## 5. RULE 32 `[R-SHARD]` — THE PARENT SOLVES NOTHING

One shard, one year, one commit, ≤ 20 min. Pinned to the **full 40-character SHA** of the commit
carrying this PRECOMMIT. The shard runs:

    uv run python scripts/replay_keeper.py results/calibration/pjm_d4_2_TP \
      --years 2022 --set pjm_da_virtual_bids=false \
      --out-dir results/calibration/pjm_d4_3_screen_2022 \
      --note "pjm-d4-3 SCREEN: DA-virtual layer OFF, 2022 — throwaway probe, never registered"

The parent does phase 0, this PRECOMMIT, the launch, and then the scoring and the write-up. It
calls no LP.

## 6. RULES 29(c) / 31 `[R-RETAIN]`

The screen bundle is a throwaway probe: **never registered, never a keeper, never quoted as a
keeper number** (rule 29 clause 2), and it is kept OUT OF `main` by **`.gitignore`, not by `rm`**
(rule 31, the ercot-255 incident). Every number this session will ever cite from it is in this
document and in the RESULT. **Nothing is deleted before the owner rules on promotion**, and the
promotion question is put explicitly in the RESULT, together with the statement that this
container is ephemeral.

## 7. RULE 30(c)

PJM's determination is the **train-tier (2023-2025) verdict** and nothing else. Nothing in this
session touches it: no keeper moves, no training year is solved, no status part is rewritten.
A number from any year here is model-**SELECTION** evidence — `[R-HOLDOUT]` was removed
2026-09-09, so no year in this program is protected from being iterated against and **none of
these is a skill claim.**
