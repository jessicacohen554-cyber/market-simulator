# FINDING miso-248 — **MISO's SPP seam was pricing a repaired-clock anchor against pre-repair-clock offsets, in 8,758 of 8,760 hours a year.** The ladder is re-derived under rule 23 on the cited commit, **all four screen gates PASS**, and the failing pin closes with `atol=0.005` untouched. **My own `G-2` failed first and is published first**

**KEEPER → `2026-09-09-miso-248-spp-ladder`** (bundle `results/calibration/miso248_fullspan_K`),
full span **2023–2025 in ONE invocation and ONE bundle** (rule 16 `[R-ALLYEARS]`).
**DETERMINATION CALIBRATED**, C3c the single ledgered non-downgrading caveat, grade summary
**scored 8 / target 7 / ledgered 1 / fails 0**, **DOF 41/2** — every one **identical** to the
`2026-09-09-miso-247-p19-posture` predecessor, **C3c's hour counts included** (model 3/7/11 h > \$200
against a measured 30/37/88).

**Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY.** MISO holds no `complete` marker; **none was sought,
inferred or granted**, and no out-of-training year was solved, scored or registered. **C3c was a
target in neither direction.**

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item 1.** Records, each pushed **before**
the numbers it governs: `PREREG-miso248-the-spp-hourly-ladder-rederive-on-the-repaired-clock-2026-09-09.md`
and three ADDENDA (phase 0 + `G-DRIFT`; the `G-2` failure; the four gates). Machine records
`_miso248_spp_rederive_phase0.json`, `_miso248_screen_gates.json`, `_miso248_g4_collateral.json`,
`_miso248_fullspan_bands_vs_keeper.json` and the preserved first-run failure
`_miso248_g2_first_run_UNSATISFIABLE.json`.

---

## 0. STATED FIRST, AGAINST INTEREST

### 0a. **MY OWN GATE `G-2` FAILED ON ITS FIRST RUN**

Published in full in ADDENDUM 2, **before** any repair, with the first-run record preserved verbatim.
It returned `PASS: false`. **Unlike miso-247's `G-1`, it was NOT satisfiable**: it demanded
`float(d.std()) == 0.0` **exactly** on `d(t) = (hub(t)+δ_new) − (hub(t)+δ_old)` in float64, whose
per-hour rounding varies with `hub(t)` — a ~1e-14 spread no correct implementation can avoid. That
makes it a **broken gate, not a result**, which is the one case this lane's own discipline licenses
repairing. The repair and its decision rule were **pushed before the repaired number was computed**,
the unsatisfiable literal was **DELETED** rather than widened (rule 26 `[R-DELETE]`), and the
substantive clauses — exactly 16 rows, zero non-SPP — were never relaxed.

**What held on the first run, reported before the repair:** 16 of 48 rows moved, all SPP, **zero**
non-SPP, every delta within **8e-15**. The label `n_non_spp_rows_moved: 5` was my code's own
mislabelling; all five listed rows are SPP rows.

### 0b. **THE HANDOFF NAMED A TABLE THAT IS NOT THE OBJECT — measured, not asserted**

The handoff's item 1 says *"re-derive `MISO_SEAM_LADDER_BY_YEAR`'s SPP entries"*. `P-1` tested that
before anything else: **that table reproduces its derivation at 192/192 entries, max abs
0.000000**, and is untouched here. `derive()` couples the EIA-930 seam-flow duration curve to the
**MISO** hub DA and never reads an SPP price, so `86e45462` cannot reach it. The object is
`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` — **48/48 mismatched**, max abs 114.18 — which is
what the failing pin actually tests. **This costs the session nothing and is reported because it is
true.**

### 0c. **THE SCREEN YEAR IS THE ONLY YEAR WHOSE PREDICTED DIRECTION IS POSITIVE**

`ΔE_pred` is **+0.2085 TWh in 2023** against **−0.2090 / −0.2820** in 2024 / 2025. The year was
chosen by `argmax F` under a rule fixed in the PREREG before `ΔE_pred` existed — but a reader is
entitled to know the screen's **direction does not generalise**, and the other direction is measured
only in the full span. This is a limit on the screen's power and it is why the screen is STOP-only.

### 0d. **`G-1`'s 1.21× IS REPORTED, NOT CLAIMED AS SKILL**

The prediction is a **first-order** calculation on the keeper's *frozen* internal price, declared as
such in advance. A factor-of-three band is all `G-1` was ever asked to detect, and a single seam's
16 rows is a far simpler object than miso-247's fleet-wide fuel repair (whose in-scope classes ran
0.52–3.28×). **Agreement this close is as much luck as design.**

## 1. THE OBJECT, AND WHY IT IS NOT AN ORDINARY LEVER

The **single delta** against the predecessor is **not a `ScenarioConfig` field**. No field was
created, changed or flipped; no gate, no flag. The bundle's own `run_config.json` records it:
`git.dirty = true`, `changed_files = ["src/market_sim/model/interchange/spec.py"]`, one file, 69
insertions. The delta is the committed registry table
`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` (48 offsets), re-derived by the **byte-identical
frozen estimator**, plus its **consumer-free** rule-13 forward-story twin `..._SPP_POOLED` (no
consumer anywhere in `src/`, so it reaches no solve; re-derived so the forward story and the backcast
table stand on one clock).

**THE TRIGGER IS A CITED SOURCE-DATA CHANGE AND NEVER A RESIDUAL** (rule 23 `[R-FROZEN-DERIVE]`,
rule 1 `[R-STRUCT]`):

> `86e45462` (2026-09-09) — *"Repair the SPP actual-LMP clock: the sidecar was on SPP's GMT market
> interval, the model is on fixed CST"*

rewrote `data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet`, which is **both** the
series `derive_spp_neighbour_hourly` Q-Q couples against **and** the series
`eia_loader.measured_miso_spp_hub_prices` applies at solve time.

> **IT COULD NOT BE DECLINED.** That anchor is **UNGATED DATA** — no `ScenarioConfig` field, no
> cache-key entry — so **every** MISO solve after the repair carries it whether or not it carries
> repaired offsets. Between the repair and this re-derive the applied offer `π_k(t) = hub(t) + δ_k`
> was a **MIXTURE**: repaired-clock anchor, pre-repair-clock offsets. `P-2` measured the anchor
> moving in **8,758 / 8,757 / 8,758 of 8,760** hours in 2023 / 2024 / 2025 (max |Δ| 203.94 / 410.55 /
> 277.69 \$/MWh). This is the same structural shape that made miso-247's `_apply_simple_cycle_hr_floor`
> non-declinable, and it is why the promotion is not a lever choice.

**Rule 21 `[R-DOF]`: ZERO free parameters created; DOF 41/2 unchanged.** `K` stays at
`SEAM_FLOW_TRANCHES`; the midpoint-depth grid, the measured EIA-930 flow series, the `SPPNORTH_HUB`
anchor (named on **topology** at miso-233, never on which hub scores better) and the no-wash
reconciliation are byte-for-byte the incumbent ones. The no-wash clamp raised **no note**.

## 2. THE RE-DERIVE, AND ITS THREE STOP CONDITIONS

| year | import offsets | export offsets |
|---|---|---|
| 2023 | 10.62 · 25.73 · 43.07 · 62.47 · 83.98 · 90.56 · 90.56 · 90.56 | 0.24 · −10.16 · −25.87 · −56.57 · −153.04 · −166.65 · −166.65 · −166.65 |
| 2024 | 14.40 · 33.33 · 56.44 · 109.27 · 203.29 · 203.29 · 203.29 · 203.29 | 2.84 · −6.48 · −14.46 · −20.33 · −27.41 · −32.26 · −36.24 · −47.02 |
| 2025 | 16.86 · 37.50 · 67.75 · 140.17 · 182.10 · 232.18 · 252.79 · 290.12 | 0.34 · −10.42 · −18.49 · −28.01 · −45.96 · −69.66 · −140.45 · −140.45 |

**All three STOP conditions hold**: the miso-243 row-count pin (8,760 → 8,760 in every year, so this
is a source change and **not** a recurrence of the cross-year join defect); import rising / export
falling; `max(export) < min(import)`.

**The structural character of the move: the repaired clock makes the seam MORE active in BOTH
directions** — every import offset falls, every export offset rises. Nothing about that was chosen.

## 3. `G-DRIFT` — one LIVE hunk, and it is this session's own object

From the predecessor's own `git.basis_sha` `f29b7ab0` to HEAD, 8 files over 5 commits, every hunk
classified (ADDENDUM 1 §5): **`86e45462`'s zonal SPP parquet is LIVE**; `actual_lmp.json` moved for
**SPP alone** (MISO's block and the other five byte-identical, measured); pjm-177's
`netload_drag_min_run_persistence` is INERT **doubly** (default off, absent from the recipe, and MISO
runs `gas_st_netload_drag = False`, the limb it touches); capx D91's registration is cache-key
accounting. **Rule 29(b) form 4 FALSIFIED, a control solve EARNED** and spent on the screen year
alone — exactly as the PREREG fixed in advance.

## 4. THE FOUR SCREEN GATES — **ALL PASS**

Screen year **2023**, `argmax F` where `F` = band-hour clearing-status flips × band capacity, on the
keeper's **own committed** `MISO_external` P1 price: **1.1835 / 1.1580 / 0.8820 TWh**, a 2.15 % margin
so no tiebreak fires. **The statistic and the selection rule were declared before either was
computed, and the residual was never consulted.**

| gate | bar | measured | |
|---|---|---|---|
| `G-1` | same sign as `ΔE_pred = +0.2085` TWh, ratio ∈ `[1/3, 3]` | **+0.252459 TWh · 1.2108 ·** same sign | **PASS** |
| `G-2` | only SPP rows move, by exactly `δ_new − δ_old`, hour-constant | **16/48 moved, all SPP, 0 non-SPP, ≤ 1e-9** | **PASS** |
| `G-3` | `mc = hub(t) + δ_k` at `atol 0.01`, **both** bundles | arm 16 rows / **0** violating hours / 1.4e-05; control 16 / **0** / 1.3e-05 | **PASS** |
| `G-4` | zero load-bearing PASS → FAIL flips | **0 flips** | **PASS** |

The SPP seam's own energy in the screen year (from each bundle's own `unit_hourly`, so the pooled
fallback never fired): control import 1.8907 / export −0.7134 / **net 1.1773** TWh; arm 2.4330 /
−1.0032 / **net 1.4297**. **Both directions grew**, as §2's offset structure implies.

## 5. THE FULL SPAN — bands both ways, **zero flips, 12 toward, 11 away**

Scored by the same in-memory scorer against the keeper's committed artifacts, bench held fixed.

**TOWARD (12).** 2023: `CT_PEAKER` −0.687 → **−0.563**, `COAL_PRB` −2.619 → −2.594, `COAL_BIT`
−3.356 → −3.305, system **coal** −6.54 → −6.46. 2024: `CC_REGULAR` 3.149 → 2.983, `CT_PEAKER`
−0.482 → **−0.355**, `ST_GAS` −3.167 → −3.133, `COAL_PRB` −4.59 → −4.524, `COAL_BIT` −3.988 →
−3.924, `COAL_LIGNITE` −0.805 → −0.804, system **coal** −9.27 → −9.14. 2025: **mean price −2.86 →
−2.82**.

**AWAY (11).** 2023: `CC_REGULAR` −6.306 → **−6.562**, `CC_CHP` −1.986 → −2.026, `ST_GAS` +0.171 →
+0.208, `ST_CHP` −2.741 → −2.745, `COAL_LIGNITE` −0.714 → −0.715, system **gas** −11.55 → −11.69,
**mean price 1.69 → 1.71**. 2024: `CC_CHP` −0.347 → −0.36, `ST_CHP` −2.677 → −2.679, system **gas**
−3.52 → −3.54, **mean price 0.54 → 0.59**.

> **MEAN PRICE MOVES AWAY IN TWO OF THREE YEARS.** Named here rather than left in the machine
> record. Rule 1 `[R-STRUCT]`: it is not a bar in either direction and no bar was set on it.

> **SIX OF THE SEVEN SCORED COAL ROWS MOVE TOWARD — and this closes nothing.** MISO's coal deficit
> is miso-247's handed-forward object. It was **not targeted**; the moves are 0.001–0.13 of a band on
> deficits of 2.6–9.1; and a seam repair is not an attribution of the coal shortfall. **It is a
> by-product, and it is not a reason for anything.** The coal deficit remains the lane's open
> object.

**Diagnostics (D-1 / D-2 / D-4), reported, all three `passed: False` on BOTH sides so no state
changes:** `D-2`'s `CT_PEAKER` `ct_netload_drag` forced share falls 0.3050 → 0.2985 (2023) and
0.1988 → 0.1953 (2024), and `D-4`'s off-window share falls in all three years (0.0211 → 0.0207,
0.0200 → 0.0195, 0.0296 → 0.0292). **C8 still reads PASS via the rule-20 grounded-above-budget
route in all three years, exactly as on the predecessor.**

## 6. THE FAILING PIN IS CLOSED THE ONLY LICENSED WAY

`tests/iso/miso/test_miso_seam_ladder.py` — **29 passed**, including
`TestHourlySppOverlay::test_registry_reproduces_the_frozen_derivation`, which failed at 8/8 elements
and max abs 62.38 at the predecessor's tip.

* **`atol=0.005` NOT widened.**
* **`_MISO244_KNOWN_LADDER_DIVERGENCES` NOT re-added** — deleted stays deleted (rule 26).
* **No test skipped, `xfail`ed or silenced.**
* **All 192 incumbent entries and all 48 overlay entries carried, with NO exceptions.**

## 7. WHY THIS IS A KEEPER — the authority named, and it is **NOT** the screen's

Rule 29's screen is **STOP-only**: passing authorises nothing.

1. **Rule 23 `[R-FROZEN-DERIVE]`** — the licence, with the source-data change cited and the residual
   never consulted. Zero free parameters.
2. **Rule 14 `[R-ACCURATE]` + the ungated anchor** (§1) — the pre-repair posture was **not available
   to keep**, and leaving MISO's designated keeper on it leaves it unreproducible at HEAD **and**
   leaves a failing test on `main`.
3. **Rule 16 `[R-ALLYEARS]`** — a determination cannot come from a one-year screen.
4. **The lane's promotion rule (miso-227): promote on CALIBRATED / CALIBRATED-WITH-CAVEATS**, under
   the owner's standing posture quoted across this lane's shard (*"If structural integrity improves
   but gates regress that may still be a keeper"*). Determination CALIBRATED, zero flips, grade
   summary and DOF identical.

## 8. WHAT IS HANDED FORWARD

1. **MISO's COAL DEFICIT is still the named successor object.** It moved slightly toward here as an
   untargeted by-product and is **not** closed. It remains an **attribution** question first — fuel
   cost, commitment, or must-run — and the adjudicated coal offer cells (`R`/`I`/`S`) stay closed.
2. **`_apply_simple_cycle_hr_floor` remains an unregistered solve-affecting change in spirit**
   (rules 24 / 28(c)) — no field, no key, no `SOLVE_EPOCHS` entry, no matrix row, absent from
   `SURFACE_MODULES`. **This is a cross-ISO governance item and not MISO's to close** (rule 25).
   **`86e45462`'s repaired anchor is a SECOND instance of the same shape**: a solve-affecting data
   change with no gate and no key. Five other lanes carry the same exposure on the first; every lane
   with an SPP-anchored object carries it on the second.
3. **SPP's gate-(a) row still cites a superseded keeper**, so `test_gate_a_provenance.py::test_live_board_passes`
   still fails on `main`. **MISO's row passes** (re-keyed here, same session as the promotion, so no
   promoter miss is created). Re-keying SPP's row is SPP's lane's R-T duty and rule 25 forbids this
   lane touching it.
4. **MISO's 2022 `complete` marker remains the owner's open decision.** Nothing here grants, infers
   or recommends it.

## 9. Governance

**Rule 1** `[R-STRUCT]`: no criterion, band or residual appears in any bar; the case rests on
construction. **Rule 12** `[R-PARALLEL]`: years sequential within every invocation. **Rule 13**
`[R-MEASURED]`: the ladder regenerates for a forward year from the same published series, and the
pooled forward twin was re-derived on the same clock. **Rule 14** `[R-ACCURATE]`: the basis, applied
against two mean-price bands that moved away rather than around them. **Rule 15** `[R-DASHBOARD]`:
registered; miso-247 pruned (`--force-uncite`); MISO carries exactly one run. **Rule 16**
`[R-ALLYEARS]`: 2023 2024 2025, one invocation, one bundle. **Rule 19** `[R-ONE-MECH]`: no floor or
bridge added; the offsets **replace** the incumbent SPP rows and never stack. **Rule 21** `[R-DOF]`:
**41/2 unchanged, zero parameters created.** **Rule 22** `[R-HOLDOUT]`: training tier only; no marker
sought. **Rule 23** `[R-FROZEN-DERIVE]`: the re-derive cites the data change and never a residual.
**Rule 24** `[R-REGISTRY]`: no env knob, no hardcoded dict; the anchor's registry gap is escalated in
§8.2, not exploited. **Rule 25** `[R-ISO-SCOPE]`: MISO's shard, section and lane only; SPP's row left
alone. **Rule 26** `[R-DELETE]`: the unsatisfiable `G-2` literal deleted, not widened; no exception
list re-added. **Rule 27** `[R-PUSH]`: on-disk edits only, blobs verified after push. **Rule 28**: the
handoff's recommended item taken; the tested cell re-stamped in MISO's shard in-session; the R-T duty
discharged. **Rule 29** `[R-SCREEN]`: zero-LP phase 0 first, one screen year on the mechanism's own
footprint, **all four gates PASS**, and the full span's authority named rather than borrowed.
**Rule 31** `[R-RETAIN]`: **nothing was deleted** — the screen arm and its earned control are retained
in the session scratchpad; **see §10.**

## 10. **RULE 31 `[R-RETAIN]` — THE PROMOTION QUESTION, SURFACED EXPLICITLY**

The keeper bundle `results/calibration/miso248_fullspan_K` is **committed** (slim set) and survives.
**Two solved bundles do NOT**: the 2023 screen **arm** and its **earned control**, retained on local
disk in the session scratchpad and gitignored, never deleted. **This container is ephemeral, so they
will not survive the session.** Every number this session will ever cite from them is in this
document and in the committed machine records, so nothing is lost that is quoted anywhere — but if
the owner wants either bundle for a further attribution, it must be said before the session ends;
reproducing them costs **~9 minutes of LP each**.

## 11. NON-CLAIMS

1. **`G-2`'s first-run failure is not withdrawn or hidden**; its record is preserved verbatim and the
   repair was declared before the repaired number.
2. **This promotion is not claimed as a scoring improvement.** Determination, grade summary, caveat
   and DOF are identical; mean price moves away in two of three years.
3. **The coal movement is a by-product and closes nothing.**
4. **`G-1`'s 1.21× is not a skill claim** (§0d).
5. **`86e45462`'s own re-index identity is neither verified nor asserted here** — my `P-2` compares
   full 8,760-hour arrays whose ends necessarily differ from a six-hour re-index, and that is named
   rather than presented as a defect.
6. **Zero free parameters**; no `ScenarioConfig` field created or changed.
7. **No marker sought or implied**; **C3c untouched** and still the designated frontier.
8. **2025 C1/C2 are SKIPPED** on the preliminary EIA-923 vintage; no 2025 C1 pass is read as
   evidence, and 2025's only scored band — mean price — is the one that moved **toward**.
