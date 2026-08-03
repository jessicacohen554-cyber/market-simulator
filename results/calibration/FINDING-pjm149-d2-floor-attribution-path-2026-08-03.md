# FINDING — pjm-149: the D-2/D-4 dispatch-path attribution drop is REAL, is FIXED, moves NO determination at any ISO — and the pjm-148 side finding mis-identified its own example

**Verdict: FIXED and shipped. Zero LP. No keeper touched, no artifact regenerated,
no determination moved at any of the six ISOs.**

Pre-registration:
`results/calibration/PREREG-pjm149-d2-floor-attribution-path-2026-08-03.md`,
committed **and pushed** at `76d0fcf` before any measurement that decides the
contract. Census probe `scripts/probes/_pjm149_d2_path_census.py`; machine
record `results/calibration/_pjm149_census.json`.

Keepers at entry, all **UNTOUCHED**: ERCOT `2026-08-02-ercot150b-zonal-anchor`,
PJM `2026-08-03-pjm-147b-chp-heat`, CAISO `2026-08-03-caiso156-meter-screen-b`,
NYISO `2026-08-02-nyiso-113-li-locational`, NEISO
`2026-08-03-neiso-caiso156-meter-screen`, MISO `2026-08-03-miso-117b-ct-heat`.

---

## §0 — verdict table

| pre-registered question | result |
|---|---|
| **C1** is the defect real at current keepers? | **YES, at all six.** 2–130 floored plants per ISO-year carry no dispatch series and lose every D-2/D-4 row: **23–272 TWh/yr** |
| **C3b** does it move the C8 **numerator** anywhere? | **NO. EMPTY at every ISO-year.** Every dropped plant's mechanism is `nuclear_mustrun` / `hydro_min_flow` — all D-2-exempt |
| **C3a** does it move a gated class's **denominator**? | **YES, at CAISO and NYISO** (`hydro`, 7.4–18.7 TWh/yr). Share stays 0.0 ⇒ pass either way |
| **C6** is the committed corpus path-consistent? | **NO — it is SPLIT.** CAISO/MISO/NEISO/NYISO artifacts are parquet-born; ERCOT/PJM are payload-born |
| **A3** does any determination or criterion move? | **NO. Zero changes at all six ISOs**, through the production `calibration_verdict` rubric |
| **pjm-148 §4's claim** that PJM's 14 CC_CHP codes are payload-absent | **REFUTED — all 14 are PRESENT** in the payloads of pjm-144, pjm-146 and pjm-147 alike |

## §1 — the defect, and what it cost

`scripts/legitimacy_diagnostics.py` built the D-2/D-4 row set as a comprehension
over the **dispatch map**:

```python
all_pids = [p for p in model_plants_plant if p in klass_by_pid or p in pid_strs]
```

so a plant that was **floored** but absent from that map was dropped silently —
no row, no failure, no note. The map is the solve's own
`dispatch/<year>_<pass>.parquet` (every model plant, gitignored ⇒ absent from
every committed bundle) or, failing that, the CAMPD-bench-keyed dashboard run
payload, which carries only metered plants. caiso-155's `pseudo_pids` re-admitted
**only** the `plant_code <= 0` (`u:`) interchange family; real plants stayed
dropped. The membership filter predates caiso-155 (`git log -S`), so this is not
a caiso-155 regression — not re-litigated, per the charter.

Census at the six current keepers (payload path + G-06 floors rebuild, no LP):

| ISO | fleet | dispatch map | floored | **C1 dropped** | **C1 TWh/yr (2023/24/25)** | classes dropped |
|---|---|---|---|---|---|---|
| CAISO | 446–457 | 193 | 179–185 | **125–130** | 28.76 / 27.59 / 24.93 | `''` nuclear, `hydro` |
| NYISO | 297–305 | 100 | 131–141 | **120–127** | 46.08 / 45.70 / 43.26 | `''` nuclear, `hydro` |
| PJM | 605–606 | 311 | 264–276 | **17** | 272.02 / 270.59 / 269.33 | `''` nuclear |
| MISO | 770–775 | 383–384 | 131–142 | **10** | 87.15 / 90.20 / 90.59 | `''` nuclear |
| NEISO | 360–364 | 100–101 | 42–43 | **2** | 23.16 / 26.48 / 27.61 | `''` nuclear |
| ERCOT | 180–193 | 173 | 65–83 | **2** | 40.39 / 38.29 / 41.30 | `''` nuclear |

C5 (the control) — 5 to 381 plants per ISO-year are absent from the map **and
unfloored**; they stay excluded, as pre-registered.

## §2 — the committed corpus is SPLIT across both paths, which is the part nobody could see

`legitimacy_diagnostics.json` is written **during the producing run**, while
`dispatch/` still exists — i.e. on the parquet path — but is re-scored later from
the committed slim file set, i.e. the payload path. Which path a given keeper's
artifact was born on is recorded nowhere. Fingerprinting on the `''` bucket (a
row the payload path could not produce):

* **parquet-born:** CAISO, MISO, NEISO, NYISO — their committed artifacts carry
  the `''` nuclear rows and are *complete*.
* **payload-born:** ERCOT, PJM — their committed artifacts are missing them.

So two keepers' artifacts and four keepers' artifacts were never comparable
documents, and rule 18 `[R-FORCED-BUDGET]` is scored **entirely** from this file.

## §3 — the contract, and why the floor-energy convention is the right one

Shipped as pre-registered (§3.1/§3.2), ISO-generic, in the new pure function
`build_plant_matrices`:

1. **Row set is path-independent.** Every floored plant enters the matrices on
   every path. A floor is a fact about the fleet build; which dispatch artifact
   happens to exist cannot decide whether it is reported.
2. **A floored plant the map does not cover enters with `disp := its own floor`**
   — caiso-155's convention generalized from pseudo-units to real plants, and
   **subsuming** it (one mechanism, not two — rule 19 `[R-ONE-MECH]`).

The charter asked this be justified or rejected, not inherited. It is justified
by a **one-sided bound**, which caiso-155 never needed to state:

* forced energy sums dispatch over **at-floor** hours only, and at-floor means
  `dispatch ≈ min_gen` ⇒ true forced energy ≤ floor energy: **upper bound on the
  numerator**;
* LP feasibility gives `P ≥ min_gen` ⇒ true dispatch ≥ floor energy:
  **understates the denominator**.

⇒ the reported `forced_share` is an **UPPER BOUND**. Rule 18 fails HIGH, so the
bound is **sound on a pass** and **indeterminate on a fail** — never a valid FAIL
by itself. The flag travels with the number: `upper_bound: true` on every
affected D-2 summary row, a note naming every substituted plant and the source it
was missing from, and an annotation in `calibration_verdict.score_forced_share`.
**A breach is deliberately NOT suppressed** — silently weakening rule 18 would be
worse than an over-strict flag — it is marked indeterminate and escalates.

**Rejected, as pre-registered:** `disp := 0` (the row still vanishes — `run_d2`
skips zero-MWh rows — and it asserts a dispatch the LP forbids);
exclude-but-disclose (leaves the row set path-dependent and leaves rule 18's own
artifact without the attribution); `disp := floor` on the parquet path too
(discards measured dispatch, rule 14 `[R-ACCURATE]`); widening the payload to
carry every model plant (**the true long-run fix** — it removes the information
loss instead of bounding it — but it changes the payload format and needs every
registered run re-emitted; named successor, §6.2).

## §4 — the external anchor: the convention reproduces the parquet truth EXACTLY for nuclear

`pjm144_control_A` is **parquet-born**, so its committed artifact is ground truth
for a bundle whose payload also exists — the one place the convention can be
checked against the number it approximates. Payload-path recompute **with the
fix** vs that committed truth:

| row | truth (parquet) | fix (payload) | delta |
|---|---|---|---|
| 2023 `''` nuclear_mustrun | 272.0222 | **272.0222** | **+0.0000** |
| 2024 `''` nuclear_mustrun | 270.5943 | **270.5943** | **+0.0000** |
| 2025 `''` nuclear_mustrun | 269.3312 | **269.3312** | **+0.0000** |

Exact to 4 dp in all three years, because nuclear must-run sits *on* its floor —
which is precisely the regime the bound is tight in. Every other pre-existing row
reproduces within ±0.24 TWh (worst: `COAL coal_mustrun` +0.2358 on a 4.79 TWh
row, 4.9 %), inside the documented G-06 reconstruction tolerance.

## §5 — pjm-148 §4 mis-identified its own example, and the real cause is a SECOND defect

The charter required the exemption claim be confirmed per ISO rather than
assumed. Confirming it refuted the example instead.

**pjm-148 §4 states: "Not one of PJM's 14 CC_CHP plant codes appears in the
payload (… all absent)". This is wrong.** Measured directly, **14/14 are present**
in the payload of `pjm144_control_A`, `pjm146_rggi_B` and `pjm147_chp_B` alike
(311 plants each). PJM's C1 population is **17 plants, every one nuclear**. So
PJM's missing CC_CHP row was never a plant-set drop, and **this fix does not
restore it** — correctly, because nothing was dropped.

The real cause is a **distinct, second path defect on plants that ARE covered**:
the payload-decoded dispatch series and the parquet series disagree about whether
a plant is *at* its floor. On the current keeper, 6–7 CC_CHP plants carry a
`chp_steam` floor of 3.82 / 4.00 / 3.67 TWh, and on the payload series **zero of
8,760 hours** are at-floor — every plant clears its floor by 8.9 to 239 MW, far
outside the ±(1 MW + 1 % nameplate) tolerance, so this is not byte quantization.
Same-bundle at `pjm144_control_A`, seven rows exist on the parquet path and not on
the payload path even with the fix: `CC_CHP chp_steam` (0.9938/0.6918/0.8147),
`CC_CHP reliability_floor`, `ST_CHP chp_steam` and a 2025 `COAL chp_steam`.

**Settling that needs the parquet series, which no committed bundle carries — so
it needs a solve, and this charter is zero-LP.** Filed as the named successor
(§6.1), not chased. It does not change this session's contract: the row-set fix
is necessary either way, and it is what makes the nuclear block visible.

**A third path asymmetry surfaced incidentally** and is also not mine: the
materiality guard needs `total_load_mwh`, which is read from the run payload's
`fuelRows` **via the sidecar**, so an in-run parquet-path generation has
`load_share = None` and gates *every* class. At `pjm144_control_A` this alone
flips ST_GAS 2023/24/25 from FAIL (parquet, guard off) to pass-immaterial
(payload, `load_share` 0.012–0.017 < 0.02) — while the *shares themselves* agree
to ~1 pp. That bundle is not a keeper, and the flip pre-dates this session's
change entirely (it is parquet-vs-payload, not pre-vs-post).

## §6 — what this leaves open

1. **The dispatch-VALUE path divergence on covered plants (§5)** — its own
   charter, and it needs one solve to hold both series for the same bundle. It is
   the live reason PJM's CHP attribution differs between artifacts.
2. **Widening the run payload to every model plant** — removes the loss instead
   of bounding it; blocked on payload format + re-emission of registered runs.
3. **The materiality-guard path asymmetry (§5, third)** — `total_load_mwh` should
   resolve on the parquet path too, or the guard's absence should be recorded in
   the artifact. Cheap; not in this charter's scope.
4. **DO-NOT-REDO.** Do not re-derive the row-set rule from the dispatch map (a
   regression test now pins the defect). Do not re-open pjm-148's CC_CHP
   payload-absence claim — it is measured and refuted here. Do not regenerate the
   four parquet-born keeper artifacts on the payload path (§7).

## §7 — per-ISO keeper impact (charter scope item 3), stated BEFORE anything was touched

**No committed keeper artifact was regenerated, at any ISO.** The reason is
measured, not cautious: four of the six committed artifacts are **parquet-born**
(§2), so regenerating them on the only path now available would *replace measured
dispatch with a bound* — a downgrade, and exactly what rule 14 `[R-ACCURATE]`
forbids. The fix improves every artifact written from here on, on whichever path
it is born.

Had they been regenerated, the delta would have been (pre-fix vs post-fix regen,
same session, same environment — gate A2):

| ISO | D-2 rows | D-2 summary | D-4 rows | verdict flips |
|---|---|---|---|---|
| CAISO | +6 (`''` nuclear ×3, `hydro` ×3); 3 `firm_import` rows re-based | +3 (`hydro`, share 0.0, pass, `upper_bound`) | +3 (`hydro_min_flow`, 0 % off-window, pass) | **NONE** |
| NYISO | +6 (same shape) | +3 (same) | +3 (same) | **NONE** |
| PJM / MISO / NEISO / ERCOT | +3 each (`''` nuclear) | **+0** | **+0** | **NONE** |

Nothing was removed anywhere; **D-1 is byte-identical at all six**. The three
re-based `firm_import` rows are a *correction*: they live in the `''` bucket,
whose denominator previously held only the firm-import floor, so
`share_of_class` read a spurious 1.0 and now reads the true 0.22–0.56. `''`
never enters the gated summary, so there is no C8 effect.

## §8 — gates

* **A1 reproduction baseline** — pre-fix regen taken in-session at HEAD for all
  six keepers; every post-fix diff is against that, never against committed bytes.
* **A2 confined delta** — PASS. Table in §7: additions only, plus the `''`-bucket
  denominator correction. No pre-existing row removed or altered outside the
  affected classes.
* **A3 determination invariance** — **PASS at all six ISOs**, through the
  production `scripts/calibration_verdict.py`: determination unchanged
  (CAISO/NYISO/NEISO CALIBRATED-WITH-CAVEATS, PJM CALIBRATED, ERCOT/MISO NOT-YET),
  **zero criterion-record status differences**, identical `grade_summary`.
* **A4 parquet-path no-op** — tested, not asserted
  (`test_no_op_when_the_dispatch_source_covers_the_floored_fleet`). The claim is
  bounded honestly: the fix is a no-op **wherever the dispatch source covers the
  floored fleet**, which is the parquet path's normal state. Two structural
  exceptions are recorded rather than assumed away — CAISO's endogenous-WECC
  external-zone exclusion drops those zones from `_dispf`, and a rebuild/solve
  fleet mismatch could too; in both cases the fix reports a bounded row where the
  old code reported nothing.
* **A5 new-test coverage** — 8 tests, including
  `test_prefix_comprehension_is_the_defect_regression_guard`, which reproduces the
  **old** comprehension inline and asserts it loses the plant while the shipped
  builder keeps it.
* **A6 suite health** — `tests/scoring/` **900 passed**, 4 failed. All four are
  in `test_ff_readiness_battery.py` and are **PRE-EXISTING**: verified by
  re-running with this session's changes stashed, identical failure set.
  `ruff format --check` and `ruff check` clean; `check_mechanism_matrix.py` green.

## §9 — stop rules

* **S1 (determination flip)** — not triggered; A3 clean at six ISOs.
* **S2 (C3 non-empty)** — **C3b EMPTY everywhere**, so no C8 numerator moves and
  the §3.4 rubric question stays closed. C3a is non-empty at CAISO/NYISO
  (`hydro`) but is denominator-only on a class whose gated share is 0.0.
* **S3 (blocked rebuild)** — hit at PJM (`pjm_da_virtual_bids` needs the
  gitignored `data/raw/pjm-da-virtuals/`); resolved by fetching the 2023–2025
  `hrl_da_incs_decs` feed in-session rather than marking PJM BLOCKED. NYISO
  needed the `capacity-deliverability` clean partition regenerated.
* **S4 (empty defect)** — not triggered; C1 non-empty at all six.
* **S5 (concurrent-lane collision)** — honoured by regenerating **nothing**; the
  per-ISO impact is stated in §7 instead.

## §10 — rule compliance

* **Rule 12 `[R-PARALLEL]`** — zero LP; census/regens run as concurrent
  per-ISO invocations.
* **Rule 15 `[R-DASHBOARD]`** — no solve ⇒ no bundle, no registration (the
  caiso-155 / pjm-131 / neiso-71 no-LP precedent).
* **Rule 16 `[R-ALLYEARS]`** — every measurement spans 2023/2024/2025.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; `holdout-freeze.json` untouched.
  The PJM virtuals fetch was restricted to 2023–2025.
* **Rules 1 / 19 / 20 / 21 / 23 / 24 / 25** — nothing tuned; no mechanism armed,
  no `ScenarioConfig` field added, no parameter derived, no per-ISO branch in
  shared scorer structure. caiso-155's pseudo-unit path is **subsumed** by the
  general rule rather than stacked beside it (rule 19).
* **Rule 27 `[R-PUSH]`** — `legitimacy_diagnostics.py` (2,528 lines) and
  `calibration_verdict.py` were edited **locally with `Edit`**; no regenerated
  full-file content was pushed; blob verification run immediately after the push.
* **Rule 28 `[R-MECH-MATRIX]`** — no mechanism cell's verdict or evidence
  changes: this is scorer visibility, not a lever. The existing cross-cutting
  audit row `diagnostics_plant_set_census` is the vehicle if one is ever needed.
* **Keepers untouched** ⇒ no shard edit, no `calibration-complete.json` re-key
  (rule 22 D-5(b) triggers on promotion), no `calibration-keeper-auditor` run
  (no keeper's committed diagnostics were regenerated).

## §11 — reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/regenerate_clean.py \
    transfer-interface-limits ramp-capability lmp capacity-deliverability
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_da_virtuals.py \
    --feeds hrl_da_incs_decs --years 2023 2024 2025      # PJM floors rebuild only
PYTHONPATH=. .venv/bin/python scripts/probes/_pjm149_d2_path_census.py \
    --json-out results/calibration/_pjm149_census.json
# the §4 anchor — payload-path recompute vs the parquet-born committed artifact:
PYTHONPATH=. .venv/bin/python scripts/legitimacy_diagnostics.py \
    --bundle results/calibration/pjm144_control_A --iso PJM --years 2023 2024 2025 \
    --only D1 D2 D4 --json-out /tmp/pjm149_anchor.json
.venv/bin/python -m pytest tests/scoring/test_legitimacy_diagnostics.py -q
```
