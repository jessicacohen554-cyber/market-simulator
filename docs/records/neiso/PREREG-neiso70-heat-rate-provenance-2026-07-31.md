# PRE-REGISTRATION — neiso-70 heat-rate provenance: two measured-input arms off one shared control

**Written and pushed BEFORE either arm solves** (caiso-146 precedent: prereg
committed at `abaa952` before any solve). Everything below — gates, thresholds,
predictions, kill conditions — is fixed in advance. Nothing here is revised
after a number is seen.

| | |
|---|---|
| **Session** | neiso-70 |
| **Branch** | `claude/neiso-70-heat-rate-provenance-xg9qge` |
| **Keeper (unchanged unless an arm is promoted)** | `2026-07-23-neiso-61-netrev-margin`, bundle `results/calibration/neiso61_netrev_margin` |
| **Keeper determination** | CALIBRATED-WITH-CAVEATS, rubric 2.9, 0 FAILs, 1 ledgered caveat (C3c price tail), C1 all 12/12 · free 8/8 |
| **Frozen session HEAD** | `65455a3dae628f67bcf0b42bf9ec372b9dd0afe8` — all three bundles solve at this one sha |
| **Lane** | rule 14 `[R-ACCURATE]` input-accuracy. **NOT** C3c scarcity work. |
| **Years** | 2023, 2024, 2025 — exactly, in one invocation per bundle (rule 16 `[R-ALLYEARS]`) |

**Scope discipline.** Lever 1 is §5.6 item 3 of the NEISO lever queue
(audit-grade, no charter needed). Lever 2 is an unqueued transfer candidate:
caiso-128 §3 measured CHP heat rates understated 12–62 % across five ISOs on a
consistent net basis, so NEISO is a standing candidate — entered as `U` under
rule 25 `[R-ISO-SCOPE]`, deriving NEISO's **own** artifact, importing no verdict
and no parameter from CAISO or MISO. §5.6 items 1, 2 (charter required), 4
(NG:PS time split) and 5 (owner decision pending) are **not opened here**, and
C3c is not touched.

---

## §1 — the delta, exactly

Three bundles, one shared control, all at the frozen HEAD:

| bundle | delta vs control |
|---|---|
| `neiso70_control_A` | none — zero-delta replay of the keeper at HEAD |
| `neiso70_ctheatrate_B` | `measured_ct_heat_rates=true` **only** |
| `neiso70_chpheatrate_B` | `measured_chp_heat_rates=true` **only** |

**Why the control is mandatory and non-negotiable.** The keeper's `meta.json`
records `git_sha` `eede1c4`, and **that commit is not in the repo** — it was
squash-merged away, so the code that produced the keeper cannot be checked out.
Any keeper-relative delta therefore charges unattributable code drift to the
mechanism. neiso-69 caught exactly this: its true 2024/2025 mechanism delta was
**exactly 0.0 for every class**, while the same comparison against the committed
keeper showed CT_PEAKER −189.7 GWh and CC_REGULAR +145.8 GWh in 2025 — **100 %
drift**. CAISO carries the same standing instruction
(`docs/calibration-log/caiso.md:1165`). Every scored number in this session is
**arm − control**, never arm − committed keeper.

---

## §2 — construction gates (fixed in advance; all four must hold)

### G-1 Flag fidelity — **DISCHARGED PRE-SOLVE, both arms LIVE**

The ERCOT-146 hazard, checked before any solve was spent. There,
`measured_ct_heat_rates`'s consumer is `eia860._rows_to_generators`, but under
`use_campd_bins` ERCOT's thermal fleet comes from the curated `load_campd_bins`
sheet, which never receives the kwarg — the flag was **inert by wiring**, an A/B
would have been bit-identical, and the cell was stamped `I` with **no solve
spent**. The NEISO keeper runs the same `use_campd_bins=True` /
`plant_level_fleet=True` configuration, so the question had to be asked here.

**NEISO takes the other branch.** In
`market_sim.data.fleet.assembly.load_or_synthesize_bins`, only `iso == "ERCOT"`
reads the curated sheet; every other ISO **synthesizes** its bins from
`load_fleet_from_csv(..., measured_ct_heat_rates=…, measured_chp_heat_rates=…)`,
and `build_base_fleet` passes both flags again on the non-thermal leg. Verified
empirically rather than by reading, at the keeper's own ScenarioConfig
(`scripts/probes/_neiso70_flag_fidelity.py`, no LP):

| arm | generators moved | MW moved | class cap-wt HR at the LP seam |
|---|---|---|---|
| `measured_ct_heat_rates` | 31 / 1,166 | 910.4 | CT_PEAKER 13.7959 → 13.2196 (**−4.18 %**) |
| `measured_chp_heat_rates` | 20 / 1,166 | 271.0 | CC_CHP 8.1437 → 10.4210 (**+27.96 %**), CT_CHP 6.2962 → 6.7784 (**+7.66 %**) |

Both arms are **live at the fleet seam**. NEISO is not ERCOT-146; both solves
are justified.

### G-2 Control integrity

The control must be a genuine zero-delta replay: its `run_config.scenario_config`
must equal the keeper's on every field except recorded provenance, and both
flags must read `False`. If the control's own criteria do not reproduce the
keeper's determination **structure** (0 FAILs, C3c the sole ledgered caveat),
the drift is large enough that the session reports the drift as its finding and
does **not** claim a mechanism verdict.

### G-3 Mechanism liveness — **`I`, not `R`, on failure**

An arm is **live** iff `max |Δ class MW|` (arm − control, over all class-hours of
the arm's target classes) **> 50 MW in at least one year**. An arm that fails
this is **inert**: its matrix cell is stamped **`I`**, never `R` — nothing was
refuted on the merits when there was no effect to refuse. Verified **first**,
before any scorecard is read (the nyiso-89 §4a / caiso-147 §6.4 check).

### G-4 Single-delta proof

Read from the arms' own committed `run_config.json`, not asserted: each arm's
`scenario_config` must differ from the control's in **exactly one** field, and
that field must be the arm's flag. Any second difference invalidates the arm.

### G-5 Year span

Each bundle's `meta.years` must be exactly `[2023, 2024, 2025]` (rule 16). The
holdout spend freeze (`frontend/data/backcast/holdout-freeze.json`) is **ACTIVE**
and outranks every marker; NEISO's locked test is already **SPENT** (2026-07-07)
and never re-grantable. No year outside 2023–2025 is solved, scored or touched
(rule 22 `[R-HOLDOUT]`).

---

## §3 — the artifacts, as derived (STEP 1 result, pre-solve)

Both derived at the frozen HEAD, `--iso NEISO`, zero fitted parameters.

### Lever 1 — `campd_ct_heat_rates_NEISO.csv` (CT_PEAKER)

* **8 plant rows, 8 applied (`flag == "ok"`), ZERO excluded by the physical
  band** [6.0, 25.0]; 17 per-unit detail rows.
* **Coverage: 910 / 1,204 MW = 75.6 %** of class capacity, but **100.0 % of the
  class's own metered CAMPD CT energy** (1.458 / 1.458 TWh) — the energy basis
  is the one that matters for an offer swap.
* **Exclusions, all with zero metered CT energy:** 28 plants / 115.2 MW (9.6 %
  of class MW) have no CAMPD account at all (the Part-75 boundary — mostly fuel
  cells, median 2.5 MW); 1 plant / 178.0 MW (14.8 %) — Bucksport Generation —
  has a CAMPD account but no `unitType == 'Combustion turbine'` unit.
* **Adverse selection: PRESENT and stated, not waved away.** Covered cap-wt
  incumbent HR **10.208** vs uncovered **11.830** (+1.621 MMBtu/MWh): the
  uncovered set is dearer on paper, driven by Bucksport (178 MW at 13.24) and by
  fuel-cell rows carrying the 9.000 default. This **differs from CAISO**
  (10.819 vs 11.004, effectively neutral). It is mitigated but not erased by the
  energy basis: every uncovered plant meters **zero** CT energy, so there is
  nothing to swap in for them. Recorded as a limitation of reach, not as a claim
  of neutrality.
* **Direction — NEISO's own, TWO-SIDED with a net-cheaper tilt.** 6 plants /
  817 MW cheaper, **2 plants / 94 MW dearer**; cap-weighted **−0.579
  MMBtu/MWh (−5.7 %)**, generation-weighted **−0.889**; ratio model/measured min
  0.826 / median 1.038 / max 1.170; 6 plants move > 0.5, 4 move > 1.0.
  NEISO is **not** any precedent: two-directional like NYISO/PJM, net-cheaper
  like CAISO but roughly **half** CAISO's size (−5.7 % vs −10.7 %), and unlike
  PJM's net **+**0.229.
* **Thin rows flagged in advance:** A L Pierce has only **154** loaded hours and
  is one of the two dearer rows (+1.203); MMWEC has **51**, right at the ≥ 50
  floor (−0.179). Neither is excluded — the screen is the committed one and is
  not re-tuned here (rule 23 `[R-FROZEN-DERIVE]`) — but both are reported.

### Lever 2 — `chp_power_only_heat_rates_NEISO.csv` (CC_CHP / CT_CHP)

* **40 (plant, class) rows, 12 applied**, 28 excluded: `not_unfired_topping` 22,
  `no_egrid_row` 5, `basis_mismatch` 1.
* **CC_CHP: 3/7 rows, 378 / 494 MW (76.6 %), and 99.5 % of the class's own
  metered CAMPD energy** (6.965 / 7.001 TWh) — strong reach.
* **CT_CHP: 9/33 rows, 52 / 267 MW (19.3 %), and 0.0 % of metered CAMPD
  energy** (0.000 / 0.328 TWh). Every covered CT_CHP plant sits **below the
  Part-75 boundary**, so none of them meters. This is **thin AND has zero
  metered reach** — stated as a limitation, **never claimed as identification**
  (the caiso-147 CT_CHP caveat, worse here). CT_CHP is not a scored C1 row.
* **CEMS validation: 4/4 covered plants within 1 %, median ratio 1.00000.**
* **Selection: the EPA-envelope gate working as designed, and it IS selection.**
  CC_CHP covered credited 6.964 (thermal_share 0.266) vs excluded 2.632 (0.527);
  CT_CHP covered 8.699 (0.227) vs excluded 5.338 (0.629). The applied population
  is systematically the **low-thermal-share tail**; the 22 `not_unfired_topping`
  rows (247 MW, thermal_share min 0.511 / median 0.633 / max 0.793 against the
  0.50 EPA ceiling) would otherwise have taken a median 14.56 / max 23.6
  MMBtu/MWh rate. Correctly excluded.
* **Direction — NEISO's own, ONE-SIDED DEARER in BOTH classes.** CC_CHP cap-wt
  **6.964 → 9.521 (+36.7 %)**, 3 dearer / **0 cheaper**; CT_CHP **8.701 → 11.515
  (+32.3 %)**, 9 dearer / **0 cheaper**. This is the MISO "uniformly under"
  picture, and it is **the opposite of CAISO**, whose two classes moved in
  opposite directions (CC dearer, CT cheaper). Stated per rule 25: derived on
  NEISO's data, nothing transferred.

---

## §4 — the NAMED RISK for lever 2, decided BEFORE solving

**The concern.** NEISO's C1 scorecard lists `CC_CHP`/`CT_CHP`/`ST_CHP` in
`pinned_classes` and `CC_CHP`/`ST_CHP` in `excluded_from_free`. If those classes
were **pinned in the LP**, re-pricing them would move nothing: a variable held
exactly at a floor is a constant in the objective, and — the ERCOT-64 result —
**a pinned variable cannot price**. The arm would then be live at the fleet seam
but inert in dispatch, and could only act indirectly through the merit order on
free classes.

**Resolved measurably, from the keeper's own committed diagnostics, before any
solve.** "Pinned" here is the **scorer-side D-10 label**, not an LP pin:
`free_class_score` excludes classes whose dispatch is pinned to a measured
realization *so that a C1 pass there is not counted as skill*. The LP reality,
from the keeper's `legitimacy_diagnostics.json` D-2 rows:

| class | D-2 forced mechanism | forced share of class energy, 2023 / 2024 / 2025 |
|---|---|---|
| **CC_CHP** | **none — no D-2 row in any year** | **0 % / 0 % / 0 %** |
| CT_CHP | `chp_steam` | 2.84 % / 5.24 % / 5.55 % |

**CC_CHP is 100 % free in the LP in all three years**, and CT_CHP is 94–97 %
free. So the re-price acts **directly on dispatch** for both classes; it does not
depend on an indirect merit-order argument. NEISO differs sharply from CAISO
here, where CC_CHP's `chp_steam` forced share was 0.435–0.470.

**What the pin label DOES cost, pre-registered.** The risk is on the **scoring**
side, and it is real: because `CC_CHP` is `excluded_from_free`, any C1
improvement on CC_CHP itself is **invisible in the `free 8/8` headline** and
shows only in `all 12/12`; and `CT_CHP` is **not a scored C1 row at all**. So
lever 2 **cannot** improve the free-class score by construction. Its C1 evidence
is the all-class row plus the D-1 shape diagnostics, and it will be reported
that way — not dressed up as a free-class gain.

**Decision rule fixed in advance for lever 2:**
* **`I`** if G-3 fails — max |Δ CC_CHP/CT_CHP class MW| ≤ 50 in every year. Given
  CC_CHP's 0 % forced share and a +27.96 % cap-wt seam move, this would itself be
  a finding worth reporting (it would mean the class is bound by something other
  than its offer).
* **`K` candidate** if the arm is live, every construction gate holds, no
  criterion verdict regresses against the control, and no protective gate breaks.
* **Live-but-not-promoted** stays a reported result with the cell stamped on its
  merits — an accurate input is not reverted because its scored benefit is
  invisible (rules 1, 14).

---

## §5 — predictions (pre-registered, directional and refutable)

Baseline from the keeper's own scorecard, C1 grid-delivered TWh (model vs
actual). **2025's C1 rows are `SKIPPED`** — preliminary EIA-923 vintage,
incomplete plant data (57 % reporting; 2.382 TWh vintage gap on CC_REGULAR
alone) — so C1 is scored on **2023 + 2024 only** (12 rows = 6 classes × 2 years).

| class | 2023 | 2024 | 2025 *(unscored)* |
|---|---|---|---|
| CT_PEAKER | 0.234 / 0.466 = **0.50×** | 0.453 / 0.655 = **0.69×** | 1.289 / 0.619 = 2.08× |
| CC_CHP | 1.219 / 1.072 = **1.14×** | 1.178 / 1.124 = **1.05×** | 1.166 / 1.194 = 0.98× |

**P1 (lever 1).** Measured CT rates are net cheaper (−4.18 % at the seam), so
**CT_PEAKER generates MORE**. In the two scored years the class is *under*
actual (0.50× / 0.69×), so the move is **toward** actual. Stated against
interest: in **2025** the class is already 2.08× over, so the same move pushes
it **further over** — against an incomplete actual, and in a year C1 does not
score. That is disclosed here in advance, not discovered later.

**P2 (lever 2).** Measured CHP rates are uniformly dearer (+27.96 % CC_CHP at
the seam), so **CC_CHP generates LESS**, with the displaced energy landing
mainly on **CC_REGULAR**. In both scored years CC_CHP is *over* actual (1.14× /
1.05×), so the move is **toward** actual.

**P3.** Total generation moves ~0 in both arms (an offer swap reallocates; it
does not create energy).

**These are predictions, not requirements.** The pjm-137 prereg predicted the
opposite direction and was recorded as **refuted** — the mechanism was
per-plant, not zonal-average. A refuted prediction is reported as refuted and
does not by itself reject an accurate input.

---

## §6 — REPORTED vs what can KILL

Judged against the **same-HEAD control**, never against committed keeper bytes.

### KILL (rejects promotion)

1. **Any load-bearing criterion verdict regresses** (PASS → CAVEAT/FAIL) in any
   year where the control passed.
2. **A protective gate breaks** on a *gated* class: C7 `profile_r` < 0.80 or
   `cv_ratio` < 0.50, or C8 forced share above its cap (30 % merchant / 15 %
   peakers), where the control passed. **Framing correction carried from
   caiso-147 and binding here:** `CC_CHP`/`CT_CHP` are exempt from **both** C7
   and C8 by explicit class list (host-steam-pinned duty), **not** by the 2 %
   materiality floor — so their D-1/D-2 numbers are **diagnostics, never a
   passed gate**, and must not be reported as one in either direction.
3. **The protective caveat budget is spent** — NEISO is at protective 0/1;
   arming must not open a protective caveat.
4. **Determination degrades** from CALIBRATED-WITH-CAVEATS via a new FAIL.
5. **A construction gate fails** — G-2 (control integrity), G-4 (single delta) or
   G-5 (year span). G-3 is not a kill: it yields `I`.

### REPORTED, never a kill

* **A worse backcast on C1 / C3a / any fit metric.** Rule 1 `[R-STRUCT]` and
  rule 14 `[R-ACCURATE]`: a measured input that degrades the fit is a
  **discovered bug to root-cause**, not a kill condition, and reverting to the
  eGRID estimate because it fits better is **forbidden**. A degraded fit is
  reported in full and blocks *promotion*, not the *input*.
* The control-vs-committed-keeper **drift**, reported separately as its own
  finding — it is evidence about the repo, not a failed gate. That comparison is
  what produced the neiso-69 catch.
* Both arms' full criterion tables, the adverse-selection and coverage
  limitations of §3, and any refuted prediction from §5.

### C3c materiality trigger

C3c is NEISO's single ledgered caveat and the frontier is declared. This session
does not target it. **Pre-registered trigger: if C3c's tail-hour count moves at
all in either arm, it is reported and never tuned toward**, and a favourable move
is **not** cited as justification for promotion. If C3a moves ≥ **1.0 pp** in any
year (the caiso-146/147 threshold), the mechanism is scored **leave-one-year-out
within 2023–2025** before any promotion is proposed.

---

## §7 — DOF ledger (rule 21 `[R-DOF]`)

**Zero free parameters in both arms.** Both artifacts are measured swaps of a
published estimate for a measured value on the same basis:

* Lever 1 — CAMPD unit-level hourly `grossLoad`/`heatInput` over the loaded
  window, converted to a NET basis by the **committed** parasitic factor map
  (the same one the benchmark's net actual uses), so derived rate and scored
  actual share one gross-to-net convention. Screen constants (0.8 × p95, ≥ 50
  loaded hours, band [6.0, 25.0]) are the committed shipped values, unchanged.
* Lever 2 — eGRID's own published `(PLHTIAN + CHPCHTI) / PLNGENAN` on the same
  net denominator, so no gross-to-net factor is involved; thermal-share ceiling
  0.50 is the EPA CHP Partnership unfired gas-turbine envelope.

Neither is swept against a residual. Per rule 23 `[R-FROZEN-DERIVE]` both
re-derive **only** when their source data updates (a new CAMPD vintage / a new
eGRID vintage), and any such commit must cite the data change. **If either arm
needs a tuned value to help, that is an open root-cause issue and is filed as
one — never a new parameter** (rule 24 `[R-REGISTRY]`).

---

## §8 — mechanics

All three bundles at the frozen HEAD `65455a3`, years **2023 2024 2025 in one
invocation each** (rule 16), years **sequential within** each invocation and at
most **2 invocations concurrent** (rule 12 `[R-PARALLEL]`). No solve is offloaded
to GitHub Actions — this is a private, billed repo.

```
scripts/replay_keeper.py results/calibration/neiso61_netrev_margin \
    --out-dir results/calibration/neiso70_control_A   --note "…"
scripts/replay_keeper.py results/calibration/neiso61_netrev_margin \
    --out-dir results/calibration/neiso70_ctheatrate_B \
    --set measured_ct_heat_rates=true  --note "…"
scripts/replay_keeper.py results/calibration/neiso61_netrev_margin \
    --out-dir results/calibration/neiso70_chpheatrate_B \
    --set measured_chp_heat_rates=true --note "…"
```

A zero-delta replay restores the source keeper's date into `meta.json`; the
control's timestamp is corrected to the session date **before**
`dashboard_add_run`, so it does not mint a stale run id.

**Scoring.** An A/B scorer under `scripts/probes/`, modelled on
`scripts/probes/_caiso146_ctheatrate_ab.py`, scoring **only** the gates
pre-registered above.

**Deliverables regardless of outcome:** all three bundles registered on the
backcast dashboard (rule 15 `[R-DASHBOARD]`) — keeper, rejected and inert arms
alike; **both** matrix cells (`measured_ct_heat_rates` and
`measured_chp_heat_rates`, NEISO index 5) updated with evidence citations in
**this** session including on `R`/`I` (rule 28b), plus the NEISO header
re-stamp; `docs/mechanism-testing-matrix.md` §5.6 updated (strike item 3, add
lever 2's outcome, file the nuclear crosswalk as the neiso-71 follow-on); and a
`docs/calibration-log/neiso.md` entry ending with the next shorthand. No rule-22
marker is written for NEISO.
