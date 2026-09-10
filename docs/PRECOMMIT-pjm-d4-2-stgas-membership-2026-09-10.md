# PRECOMMIT / PHASE 0 — PJM membership in `data.outages.ST_GAS_PEAKER_PLANTS`

**Session** `pjm-d4-2` · **ISO** PJM · **Date** 2026-09-10 · **Branch** `claude/pjm-d4-2-1xm7l3`
**Keeper (and G-CTRL form 4 control)** `2026-09-09-pjm-fuelvintage-ep-level`
= `results/calibration/pjm_fuelvintage_A` (2023-25) + `results/calibration/pjm_fuelvintage_TP`
(2020-22, folded). **Scope: PJM ONLY.**
**Predecessor** `docs/RESULT-pjm-d4-1-stgas-merit-order-2026-09-09.md` §12 specifies this card.

> Every number below is **ZERO LP** — a committed artifact, or an on-recipe
> `run_year(..., fleet_only=True)` rebuild through `replay_keeper.run_year_kwargs`, the only
> sanctioned reconstruction. **This document is committed BEFORE any solve is launched.**

---

## 0. THE OBJECT, AND THE ONE THING THAT COULD GO WRONG

The object is **membership in an existing registry**, not a new mechanism (rule 19 `[R-ONE-MECH]`),
on-registry (rule 24 `[R-REGISTRY]`), with **zero new `ScenarioConfig` fields**.

`data.outages.ST_GAS_PEAKER_PLANTS` exists to keep *"peaker-class ST_GAS plants: patchy / spiky run
rate (run only when called)"* out of the reliability min-gen floor. It names 6 ERCOT and 3 CAISO
plants and **no PJM plant**, while PJM's plant 3161 runs 1.8 % of hours and is floored ~7,885 h/yr.

**The whole governance risk is the qualifying threshold**, because a threshold chosen to make C8 pass
is the fitted-mechanism selection rules 1 `[R-STRUCT]` and 29(c) `[R-SCREEN]` exist to forbid. §2
fixes it from evidence in which PJM does not appear, and §2c shows it carries **no leverage at all**.

---

## 1. THE CENSUS — measured, six years, at the right granularity

Meter-online share (CAMPD > 1 % of nameplate) of the plant's **ST_GAS slice**, per bench year.
`x` = the slice fails the benchmark's own trust test (`e_ann / c_ann > 1.1`) and is dropped.

| plant | MW | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | **POOLED** |
|---|---|---|---|---|---|---|---|---|
| 50279 Archbald | 23 | 0.0 | 2.1x | 17.0x | 6.2x | 3.1x | — | **0.0** |
| 874 Joliet 9 | 360 | 1.4 | 0.3 | 0.5 | — | — | — | **0.7** |
| 3809 Yorktown | 628 | 2.1 | 1.7 | 1.1 | — | — | — | **1.6** |
| 599 McKee Run | 114 | 1.6 | — | — | — | — | — | **1.6** |
| 3161 Eddystone | 862 | 0.8 | 1.3 | 1.6 | 2.3 | 4.3x | 3.0 | **1.8** |
| 3775 Clinch River | 475 | 16.9 | 10.3 | 6.3 | 8.1 | 15.2 | 22.4 | **13.2** |
| 1571 Chalk Point | 1318 | 13.7 | 3.6x | 7.1 | 13.2 | 17.7 | 33.8 | **17.1** |
| 384 Joliet 29 | 1320 | 23.4 | 18.5 | 15.4 | 16.4 | — | — | **18.4** |
| 593 Edge Moor | 710 | 11.4 | 18.9 | 22.1 | 16.0 | 21.9 | 32.4 | **20.5** |
| 3148 Martins Creek | 1701 | 7.7 | 8.2 | 5.7 | 15.9 | 48.6 | 50.7 | **22.8** |
| 3149 Montour | 1758 | 4.7 | 20.9 | 21.9 | 14.2 | 49.3 | 73.8 | **30.8** |
| — *empty interval* — | | | | | | | | **30.8 → 48.6** |
| 3138 Brunner Island | 354 | 38.6 | 33.7 | 44.0 | 65.4 | 56.6 | 53.1 | **48.6** |
| 3131 New Castle | 632 | 47.0 | 33.9 | 44.9 | 65.5 | 59.2 | 55.6 | **51.0** |
| 1353 Shawville | 280 | 50.7 | 40.4 | 36.8 | 74.4 | 73.9 | 82.7 | **59.8** |
| 3140 Hatfields Ferry | 1616 | 41.9 | 62.7 | 74.2 | 74.4 | 76.3 | 76.4 | **67.6** |

Reproduces pjm-d4-1 §9 for 2023-25 and extends it to 2020-22. **Slice granularity is load-bearing**:
1571's `ct_only` flag attaches to its **CT_PEAKER** slice (`e/c` 1.648), not to its boilers
(`e/c` 0.98–1.04). At plant granularity the flag would have suppressed a trustworthy boiler meter.

---

## 2. THE QUALIFYING CRITERION — DECLARED HERE, NEVER SWEPT

> **A PJM plant is admitted iff the meter-online share of its ST_GAS slice, pooled over EVERY bench
> year whose own `e_ann / c_ann ≤ 1.1`, is BELOW 35 %. A plant with no trusted bench year is NOT
> admitted (fail-closed).**

### 2a. The threshold is read off the registry's OWN membership, in the ISOs that authored it

PJM was **not consulted** to set it. Same measurement, same code path, applied to ERCOT and CAISO:

| ISO | admitted (members), pooled duty % | excluded, pooled duty % | **revealed gap** |
|---|---|---|---|
| **ERCOT** | 4266 10.3 · 3576 13.3 · 3507 23.1 · 3490 32.2 · 3504 34.1 · **3453 34.7** | **3452 36.9** · 3491 39.4 · 3601 49.9 · 3628 54.1 · 3460 56.0 · 3611 66.8 · 6243 88.9 · 3612 94.5 | **(34.7, 36.9]** |
| **CAISO** | 350 6.6 · 335 11.3 · **315 31.0** | **356 45.1** | **(31.0, 45.1]** |

Both gaps are **empty**: the registry's existing membership is exactly threshold-separable on this
statistic, in both authoring ISOs, and every `T ∈ (34.7, 36.9]` reproduces it. **T = 35 %.**

### 2b. The competing window was TESTED and is FALSIFIED — the test could have gone the other way

The docstring's CAISO comment cites *"CAMPD 2024-25"*, i.e. a most-recent-two-years window. Run
against the same criterion, that window makes ERCOT's admitted set **OVERLAP** its excluded set —
3504 admitted at 46.3 % against 3491 excluded at 31.2 % — so **no threshold on it reproduces the
registry at all**. The all-trusted-years pooling is the only one of the two candidates that is
separable, and it is separable in both ISOs. The window is therefore fixed by a test it could have
failed, not by the set it produces in PJM. *(It matters: the two windows disagree about plant 3149,
which carries 1.585 TWh of the 2025 mandate.)*

### 2c. THE THRESHOLD CARRIES NO LEVERAGE — there is nothing here to sweep

PJM's own duty distribution has an **empty interval from 30.8 % to 48.6 %**, which strictly contains
the precedent-admissible window (34.7, 36.9]. **The admitted set is IDENTICAL for every threshold in
(30.8, 48.6]** — a 17.8-point interval. Under rule 21 `[R-DOF]` this is not a free parameter: its
value cannot be moved to change any outcome. Identification source: **the registry's own revealed
membership in ERCOT and CAISO**, not any PJM residual.

### 2d. Rule 13 `[R-MEASURED]` — the forward argument, stated rather than assumed

The admissibility test is *"could this quantity be produced for a forward year from forward drivers,
and would it respond to changed conditions?"* Peaker-vs-baseload character is a **standing attribute
of a steam plant** — duty follows from its heat rate and age against the fleet it bids into — so the
identical census regenerates from any year's CAMPD vintage and **re-classifies a plant whose
economics change**. It is an input to the commitment/offer treatment, never an outcome the dispatch
is pinned to. The precedent exists (the registry's other 9 members were admitted on measured duty)
but is not automatic, and this is the argument, not the precedent.

**What this is NOT**: it is not the `netload_drag_layup_window_mask` route. That one is registered
`_BACKCAST_ONLY_OVERLAY_FIELDS`, has no forward analogue, and pjm-d4-1 §9a refused it under rule
17(c) **even though it cleared the gate**. This criterion is forward-native by construction.

---

## 3. ALL FOUR CONSUMERS, MEASURED PRE-SOLVE — the blast radius is larger than the card assumed

Arm and control built **in ONE process at ONE HEAD from ONE recipe** (2025, `pjm_fuelvintage_A`), so
HEAD drift cancels identically. Control ST_GAS floor **11.5063 TWh reproduces pjm-d4-1's control to
four decimals** — the reconstruction is the keeper's, not a lookalike.

| leg | consumer | measured effect (2025) |
|---|---|---|
| **1 — floor** | `fleet/floors.py` `exclude_plant_codes` | **whole-fleet mandate −7.9793 TWh**; ST_GAS floor **11.104 → 3.125 TWh (−69.3 %)** |
| **2 — outage overlay** | `derive_campd_unit_outages.py` | **Δ = 0.000000** — *inert, and see below* |
| **3 — offer curve** | `_offer_curve_for_group` → `None` | admitted plants lose the ST_GAS bands (1.0/1.0/1.0/**3.024**) and offer flat CSV heat rate: cap-wtd HR **17.10 → 13.53** (3148), **17.50 → 13.83** (593) |
| **4 — econ split** | `_econ_split_for_group` → `None` | 4 tranches → 3 on each admitted plant (2998 → 2987 fleet rows) |
| **confinement** | — | **only the 11 admitted plants move.** Every non-admitted plant is byte-identical on floor, availability, pmax, heat rate and row count. |

**Leg 2 is inert because the exclusion lives in the DERIVE, not in the solve.** A run reads the
committed CAMPD outage artifact, and this card does not re-derive it: rule 23 `[R-FROZEN-DERIVE]`
says a derive re-runs when its **source data** updates, and the source data has not. So the tested
object is legs 1 + 3 + 4, and the admitted plants **keep** their existing outage derates (593 stays
at 0.357 mean availability). That is the conservative direction and it is declared, not discovered.

**Leg 3 cuts AGAINST the card and is reported at full magnitude.** Removing the 3.024× peak band
re-prices roughly the top 13 % of each admitted plant's capacity from ~$144 to ~$48/MWh at 2025 gas —
about 1.25 GW that moves from scarcity-priced to mid-merit. Floor removal pushes ST_GAS **down**;
this pushes it **up**. **Their net is an LP question and is not pre-judged here.** The seam is tested
**whole**, exactly as ERCOT and CAISO carry it: splitting it to keep only the leg that helps would be
a new PJM-only mechanism and is precisely the selection rule 1 forbids.

---

## 4. THE PRE-SOLVE CONDUCT RIDER — the arm clears every conviction

Scored on `{min_gen > 0}`, a **superset** of the solve's `at_floor_mask` and therefore the **more
forgiving** basis (pjm-d4-1's proxy gap: 2 here vs 5 on the committed artifact in 2025).

| 2025 | control | arm |
|---|---|---|
| ST_GAS plants carrying a floor | 13 | **6** |
| **D-4 conduct convictions** | **2** (593 median 0.00 / zero-share 0.648; 3775 median 0.00 / 0.753) | **0** |

Every surviving floored plant passes: 1353 (median 173.9), 3131 (101.2), 3138 (56.7), 3140 (485.0).
For contrast, pjm-d4-1 measured **zero** flips under `netload_drag_merit_allocation`,
`netload_drag_min_run_persistence` and their composition — the composition was strictly worse.

---

## 5. PRE-REGISTERED EXPECTATIONS — **NONE of these is a gate** (rule 1 `[R-STRUCT]`)

1. **C8 2025 passes on the BUDGET, not on the escalation.** The mandate falls 69 %, so forced share
   should land far below the 30 % cap (control 41.3 %) and the D-4 leg is never reached.
2. **THE HONEST RISK, STATED FIRST.** If forced share stays **above** 30 %, C8 escalates — and
   **3131 and 3138 remain floored and remain convicted on the committed `at_floor` basis**, so
   **C8 would still FAIL.** Membership is the largest part of this defect and provably not all of it.
   Duty alone does not explain a conviction at ~50 %, and no threshold in the precedent-admissible
   window reaches those two.
3. ST_GAS class energy falls (m/a 1.29 in 2025, 1.52 in 2023) — but leg 3 works the other way and
   the net is not pre-judged.
4. CT_PEAKER should **rise** toward actual in 2021/2022/2023 (Δ −32.2 / −24.9 / −10.6 %) as the
   displacement releases.
5. **C1 / C3a / C3b / C4: whatever they do is accepted and reported at full magnitude.** A fix that
   makes ST_GAS right by making CT_PEAKER worse has **moved** the error, not removed it, and will be
   reported as such. 2025 CT_PEAKER is already **+19.2 %** over actual, so leg 3 plausibly makes it
   worse there; that is a cost, not a reason to re-scope the mechanism.
6. Any mechanism-change-driven verdict flip is scored **leave-one-year-out** within 2023-2025 before
   promotion (rule 17).

---

## 6. CONTROL, SCREEN AND SHARDING POSTURE

- **G-DRIFT is NOT RUNNABLE for PJM** — established independently by pjm-177 §4,
  `PRECOMMIT-pjm-fuelvintage-solve` §(a) and pjm-d4-1 §2 (the keeper's `git_sha` predates the
  2026-08-16 history rewrite). **G-CTRL form 4 declared IMPAIRED**, bands **±0.25 %** (**±2.4 %**
  CT_PEAKER), fixed here, before any solve. **No control solve is spent** (rule 29(b)): the
  committed keeper bundles are the control.
- **Rule 29 `[R-SCREEN]` clause (0) was run in full and the arm passed it** — §§1-4 are the zero-LP
  phase 0, and they killed nothing.
- **Clause (1)'s one-year screen is NOT spent, by owner instruction.** The owner directed this
  session to solve **all** years toward a keeper. Clause (1) exists to avoid spending a full span on
  an arm that a single year would have killed; when the owner has directed the full span, the
  screen's economy no longer applies. The year whose footprint was measured is **2025** (7.9793 TWh
  of mandate removed — the largest, following the mandate ordering 2023 8.809 < 2025 11.506, an
  ordering independent of any residual). **Naming it is not gating on it.**
- **Rule 32 `[R-SHARD]`: this parent never runs an LP.** Six shards, one year each, own container,
  own `--out-dir`, own branch, pinned to this commit's 40-char SHA. The parent composes ONE bundle
  covering **2020-2025** and registers it **once** (rule 16 `[R-ALLYEARS]`).
- **Rule 22 coda**: `[R-HOLDOUT]` is REMOVED, so 2020-2022 need no authorization, marker or flag.
  Rule 30(c) still binds: **a held-out year never downgrades PJM.** 2019 and H1-2026 are neither
  attempted nor designed around.
- **Rule 31 `[R-RETAIN]`: nothing is deleted.** The shard bundles are `.gitignore`d — which is what
  discharges rule 29(c) in full — and the promotion question goes to the owner explicitly.

---

## 7. WHAT IS NOT CLAIMED

- No LP has been solved at the time of writing. Nothing here is evidence of forecast skill.
- **The conduct rider is a proxy.** Its basis is more forgiving than the solve's `at_floor_mask`
  (2 convictions vs the committed 5 in 2025); a solved arm can differ.
- **Membership is not proven sufficient** — §5 item 2 is the stated failure mode, not a footnote.
- **Nothing was transferred from ERCOT's or CAISO's verdict** (rule 25 `[R-ISO-SCOPE]`). What was
  taken from them is a **criterion read off their membership**, and every parameter of PJM's arm is
  derived from PJM's own meter. No ERCOT or CAISO plant code is touched; ORIS codes are unique, so
  no other ISO's fleet can move.
- The **offer-band asymmetry** (CT_PEAKER 1.05/1.25/1.65 vs ST_GAS 1.000) is inherited and not
  adjudicated here.
