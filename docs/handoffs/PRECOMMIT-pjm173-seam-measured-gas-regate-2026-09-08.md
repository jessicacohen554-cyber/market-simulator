# PRECOMMIT — pjm-173: re-gate and screen the seam-local measured backcast gas repair (F-A)

**Session** pjm-173 · **ISO** PJM · **Date** 2026-09-08
**Status: WRITTEN BEFORE ANY SOLVE** (rule 29 `[R-SCREEN]`). No LP has been spent by this session.
**Predecessor card** `docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md`
**Predecessor result** `results/calibration/FINDING-pjm172-seam-measured-gas-2026-09-07.md`
**Route** FINDING §6 option **(a)** — *"a successor PRECOMMIT restates S1 and S3 with the
gas-elasticity in them, then screens as this card intended."*
**Keeper** `2026-08-15-pjm-162-inputclock` — unchanged by this card in every training year.
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).

---

## 1. WHY THIS CARD EXISTS

pjm-172 built the F-A repair, proved it inert in every scored year, and then **killed it at its own
pre-solve gates S1 and S3** — correctly, because the card's kill rule said so. The FINDING then
established that **the gates, not the mechanism, were mis-specified**: S1 required
`neighbor_heat_rate` to be *unchanged*, which **no** change to PJM's pre-2023 seam gas level can
satisfy, because three of PJM's five seams price their implied heat rate as a declared function of
that very gas level.

This card restates those two gates so they measure what the mechanism actually does, and then runs
the measurement pjm-172 could not: **S4 footprint, S5 net-export direction and S6 collateral**, none
of which has ever been observed.

**No code changes in this card.** The F-A implementation and its 40 tests are already merged on this
branch and are not touched. The only new thing here is the gate specification and the solve.

---

## 2. THE ARM — unchanged from pjm-172 §2

In `market_sim/data/neighbor_price.py::neighbor_gas_price`, when the requested year falls **before
the trajectory's first knot**, the Henry Hub level resolves from the **measured** annual series
(`data/raw/gas-prices/henry_hub_monthly.csv`, annual mean of monthly EIA spot) instead of holding
the 2023 knot flat. `gas_basis` is applied unchanged. A `hindcast_asknown_*` look-ahead refusal
guards the capacity-hindcast path.

**Zero free parameters, zero new `ScenarioConfig` fields** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`):
2019 **2.565** · 2020 **2.034** · 2021 **3.910** · 2022 **6.419**, all measured, none selectable by
a result.

**Still NOT bundled** (rule 19 `[R-ONE-MECH]`): card F-B (the missing 2021/2022 `hr_by_year`
entries), any edit to `HENRY_HUB_TRAJECTORIES` (owner ruled the shape seam-local, 2026-09-07), the
parent finding's trough object, and the EMAAC availability census.

---

## 3. THE RESTATED GATES

### 3.1 An integrity disclosure that binds this card

**S1′ and S3′ are REPRODUCTION gates, not prediction gates, and this card says so before using
them.** pjm-172 already measured these quantities at zero LP; their values are known. Restating S3′
at 61.1448 therefore asserts only that *this HEAD reproduces the predecessor's measurement*. It
carries **no** predictive credit and is not evidence for the mechanism. The gates that retain
predictive force — fixed here before any number exists — are **S4, S5 and S6**, which have never
been observed in any run.

### 3.2 The gate table

| # | gate | pass condition |
|---|---|---|
| **S1′** | resolution | Only the seam **gas level** is set directly. `neighbor_gas_price` moves to the §4 arm values (≤1e-9). `neighbor_heat_rate` moves **only through the declared elastic law** `hr = hr_phys + hr_adder/gas` = `5.6 + 14.2/gas`, and **only** on the three seams carrying `hr_by_year = None` (Carolinas, TVA, LGEE). MISO (12.9) and NYISO (10.4) carry per-year heat rates and must be **unchanged**. Any HR move that the elastic law does not predict to ≤1e-9 fails. |
| **S2** | identity | For every year ≥ 2023 and every forecast year, `neighbor_gas_price` is **bit-identical** to control across all 5 neighbours and all of `low`/`mid`/`high`. **Already PASSES by test** (pjm-172); re-asserted, not re-litigated. |
| **S3′** | magnitude | 2022 seam baseload mean = **61.1448 $/MWh**, per-neighbour **MISO 82.8059 · NYISO 72.4782 · Carolinas/TVA/LGEE 50.1467**; 2021 mean **41.0197**. \|err\| ≤ 1e-4. |
| **S4** | footprint | The only `mc` rows that move are the **80** reference-price seam rows (5 neighbours × 8 tranches × 2 directions). Zero non-seam rows move; zero seam rows fail to move. **NEVER OBSERVED.** |
| **S5** | direction | 2022 model **net export RISES** from the control's 21.65 TWh (measured actual 31.64). A fall, or a rise overshooting 31.64 by more than 25 %, fails. **NEVER OBSERVED.** |
| **S6** | collateral | No criterion that **PASSES on the control's 2022 column** may FAIL on the arm, other than C3a. On the control those are **C2** (load-bearing), **C4** (supporting), **C8** and **C6** (protective). C1 `fuelmix` and C3b `price_shape` already FAIL on the control, so they cannot flip; their movement is **reported at full magnitude and gates nothing**. **NEVER OBSERVED.** |

**Kill rule.** S1′, S3′ or S4 failing kills the arm outright. S5 failing kills it as a
direction miss. S6 failing kills it as a collateral miss. A kill is the session's result.

**C3a is deliberately absent from every gate**, in both years. Gating on it would be exactly the
fitted-mechanism selection rules 1 `[R-STRUCT]` and 29 forbid. Its movement is reported.

### 3.3 Why S1′ is not a weakening of S1

S1 asked for an *unchanged* heat rate. That was **unsatisfiable by construction**, not a high bar —
`_HR_GAS_ELASTIC` makes `hr` a declared function of `gas` on the three SERC seams, so the original
S1 would fail for *any* correct implementation and *any* incorrect one alike. A gate that cannot
discriminate is not a gate. S1′ restores discrimination by pinning the **law** rather than the
value: the HR must move by exactly what `5.6 + 14.2/gas` predicts, on exactly the three seams that
take that branch, and not at all on the two that do not. That is a **stricter** test of the
implementation than "unchanged" ever was, because it can catch a wrong-magnitude or wrong-seam move
that "unchanged" would have failed indistinguishably.

---

## 4. THE MEASURED PRE-SOLVE FOOTPRINT (predecessor's, restated as this card's basis)

Per-seam control → arm, 2022 (the screen year):

| neighbour | gas ctl | gas arm | HR ctl | HR arm | baseload ctl | baseload arm |
|---|---|---|---|---|---|---|
| MISO | 2.5400 | 6.4191 | 12.9000 | 12.9000 | 32.7660 | **82.8059** |
| NYISO | 3.0900 | 6.9691 | 10.4000 | 10.4000 | 32.1360 | **72.4782** |
| Carolinas | 2.5400 | 6.4191 | 11.1906 | **7.8122** | 28.4240 | **50.1467** |
| TVA | 2.5400 | 6.4191 | 11.1906 | **7.8122** | 28.4240 | **50.1467** |
| LGEE | 2.5400 | 6.4191 | 11.1906 | **7.8122** | 28.4240 | **50.1467** |
| **MEAN** | | | | | **30.0348** | **61.1448** |

2021 mean: **30.0348 → 41.0197**.

**Screen-year choice, uncontaminated.** Corrected footprint **+31.110 $/MWh** (2022) vs **+10.985**
(2021) — ratio **2.832**, reproducing the predecessor card's stated 2.83×. 2022 remains the year the
mechanism is largest, so the choice was made on footprint and not on a residual.

**Both years are solved in one invocation**, matching the committed control's own span, with years
**sequential** within the run (rule 12 `[R-PARALLEL]`).

---

## 5. G-CTRL / G-DRIFT — re-audited at THIS HEAD, before the solve

pjm-172's Appendix A audited `f36cee6e → 172af213`. That revision **no longer exists** (the branch
was merged and `main` has advanced), so the audit is re-run here at its rule-29(b) form,
`f36cee6e → HEAD 22eda76a`, and the delta against the predecessor's finding is stated.

**Scope diff:** 73 files (was 69), +16,173 / −82.

**A. Instrument checks.**

1. **PJM solve-surface projection (capx D79).** At HEAD: **212 rows**, and
   **`moved_rows("PJM") == {}` — EMPTY**. Against the control's recorded 211 rows, the difference is
   **exactly one ADDED row and zero MOVED rows**. The added name is
   **`THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`** (capx D84), verified absent from all seven
   `SURFACE_MODULES` at `f36cee6e` and present at HEAD. It is read only by
   `thermal_accreditation_vintage_armed`, whose gate `pjm_thermal_accreditation_vintage` has
   dataclass default **False** and is **coerced back to that default under `if self.mode ==
   "backcast"`** — and a backcast runs no capacity evolution at all, so the table has no seam to
   reach. **INERT.**
2. **PJM scoring reference — checked because a moved reference would stale the control's committed
   scores.** Every PJM-keyed subtree of `data/raw/_validation-source/actual_lmp.json` and
   `calibration_reference.json` was extracted at both revisions and hashed:
   `b4edaf49c24e619c → b4edaf49c24e619c` and `763eea657b57941a → 763eea657b57941a` —
   **byte-identical**. The 637-line `actual_lmp.json` insertion is a **CAISO 2022** block; the
   417-line `calibration_reference.json` insertion is an **SPP** block. The control's committed
   2022/2021 scores are therefore still current and are a valid comparison column.

**B. New-since-predecessor hunks, classified.**

| file(s) | verdict | reason |
|---|---|---|
| `model/capacity_evolution/retirements.py`, `__init__.py` | INERT | capx D84 thermal ELCC vintage. New gate default-OFF and backcast-coerced (A.1); forecast-lane capacity evolution, which a `mode="backcast"` run never enters. |
| `model/reserves/__init__.py` | INERT | re-exports only — `spp_contingency_reserve_demand_steps`, `_spp_design`. No PJM symbol added or changed. |
| `scripts/lib/wind_shape.py` | INERT | **new file, imported nowhere** on the solve path — no reference from `src/market_sim`, `run_calibration*.py` or `scripts/lib` (verified by grep). A builder library for `scripts/data/build_*_wind_shape.py`. |
| `data/raw/_validation-source/*` | INERT for PJM | SPP capacity/LMP artifacts + a CAISO 2022 LMP block; PJM subtrees hash-identical (A.2). |

**C. Carried forward.** Every other file in the 73 is one pjm-172 already classified INERT in its
Appendix A, on reasoning this session re-read and did not disturb.

**VERDICT: ZERO LIVE hunks at HEAD `22eda76a`. G-CTRL form 4 is VALID — the committed
`pjm169_tp2022_2021_f2arm` columns are the control, and NO control LP is spent** (rule 29(b)).

---

## 6. EXPECTED RESIDUAL MOVEMENT — recorded again so it cannot be written to fit

Unchanged from the predecessor card §7, and **none of it is a gate**:

- **2022 C3a improves.** Control −9.9 %; dearer imports ⇒ less import ⇒ PJM climbs its own stack.
- **2021 C3a WORSENS.** Already +10.8 %; this pushes it further outside the band. Under rule 14
  `[R-ACCURATE]` a worse fit on an accurate input is a **discovered bug elsewhere** — the parent
  finding's trough object — and **never** a reason to revert the measured input.
- **C1 `CC_REGULAR` direction genuinely uncertain.** No prediction is claimed.

---

## 7. GOVERNANCE

- **Rule 22 `[R-HOLDOUT]`** — 2021 and 2022 are **validation tier**. PJM holds the `complete`
  marker; the holdout freeze scopes the locked test alone. `--holdout-authorized` is required and
  the marker is re-checked at registration. Both years are **iterable selection evidence** and
  **neither may ever be quoted as an out-of-sample skill number**; no parameter is identified
  against either.
- **Rule 29 `[R-SCREEN]`** — the bundle is a **throwaway diagnostic probe**: never registered,
  never a keeper, never quoted as a keeper number. This document carries every number the session
  will cite.
- **Rule 31 `[R-RETAIN]`** — the arm bundle is **gitignored, never deleted**. It stays on local disk
  until the owner rules on promotion, and the session surfaces the promotion question before it ends.
- **Rule 30(c)** — a held-out year never downgrades the ISO. PJM stays **CALIBRATED** whatever the
  arm reads.
- **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — no gate is re-read, re-weighted or re-written once a
  number exists. The F-A input is a measured physical fuel price with a forward analogue, not an
  outcome pinned to an actual.
- **The recipe is frozen.** `replay_keeper.py` replays the committed touchpoint's own kwargs, so the
  arm is *the control's recipe plus the F-A delta and nothing else*. `pjm_da_virtual_bids`, the
  per-gen reserve co-opt and the zonal loss surface are **never** disabled to fit memory — a cheaper
  solve would measure a different model and void the A/B.

---

## 8. DELIVERABLES

The A/B measurement graded against §3.2; a FINDING carrying the full gate table; the PJM matrix
shard cell; a calibration-log entry; and the owner-facing rule-14 merge question left explicitly
open. **No registration, no promotion.**
