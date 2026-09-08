# FINDING — capx D88: fleet `unit_id` uniqueness (guard + vintage-stamped re-mint)

**Lane:** capx D88 · **Branch:** `claude/capx-d88-fleet-id-uniqueness-x31hi6` · **Date:** 2026-09-08
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso` + `code`
**Authority:** OWNER RULING **Q62** (capx ledger §0bf.3(a)) — *"Fix first, flag the verdict now."*
**Scope source:** `DESIGN-capx-d87-d88-s19-read-2026-09-08.md` §2.6 · **Gates pre-registered:**
`PRECOMMIT-capx-d88-2026-09-08.md` (committed `cfdddb04`, **before** any arm was solved)

---

## 0. HEADLINE

**PHASE 0 — THE GUARD IS SILENT ON EVERY BACKCAST KEEPER.** An on-recipe
`run_year(fleet_only=True)` rebuild of all seven ISOs' designated keepers, across **every** solved
year — **23 keeper-years** — fires the new `ValueError` **zero** times. No keeper can be touched by
this lane. Nothing fired anywhere unpredicted, so there is **no second population** and the lane's
shape is unchanged.

| ISO | keeper bundle | years | n_gen | guard |
|---|---|---|---|---|
| CAISO | `caiso260_demand_vintage` | 2023–2025 | 1846 / 1840 / 1845 | **SILENT** |
| ERCOT | `ercot256_five_year_keeper` | 2021–2025 | 2323 / 2321 / 2320 / 2318 / 2307 | **SILENT** |
| MISO | `miso243_sppair_K` | 2023–2025 | 3162 / 3150 / 3130 | **SILENT** |
| NEISO | `neiso106_offerlevel` | 2023–2025 | 816 / 806 / 806 | **SILENT** |
| NYISO | `nyiso213_summer_seam` | 2023–2025 | 812 / 809 / 809 | **SILENT** |
| PJM | `pjm_debugb_inputclock_A` | 2023–2025 | 3407 / 3413 / 3416 | **SILENT** |
| SPP | `spp43_screened_B` | 2023–2025 | 1151 / 1148 / 1148 | **SILENT** |

**THE SCREEN PASSES G1–G5 AND FAILS G6 ONLY AS LITERALLY WRITTEN, in one year, at a level that is
not a decision.** The arm does not die. And the delta the charter recorded as **UNMEASURED** is now
measured: **the collision delayed an exit decision by two years.**

---

## 1. STOP TABLE (pre-registered `PRECOMMIT` §4; STOP-only — it may kill, never promote)

Graded against the **in-container pre-D88 control** (§3 explains why that, and not the committed
bundle, is the control the gates are graded on):

| gate | verdict | evidence |
|---|---|---|
| **G1** guard silent every year | **PASS** | 0 raises across 2026–2040 |
| **G2** 2026–2030 byte-identical | **PASS** | all five ledgers byte-identical |
| **G3** 2031 rename-only, no decision delta | **PASS** | the **sole** difference in the entire ledger is the additive `to_unit_id = gas_cc_ccs_h_class_Central_r2031`; every event list and every scalar identical |
| **G4** 2032–2036 no decision delta | **PASS** | all five ledgers byte-identical |
| **G5** no duplicate id from 2037; `to_unit_id`s distinct | **PASS** | no duplicate in any year |
| **G6** no non-gas row moves in any year | **FAIL as written, 2040 only** | see below |

**G6, stated precisely rather than explained away.** 2026–2039 carry **no** non-gas movement at all
(2038 and 2039 contain **zero** non-gas `pipeline_events` rows in either arm). In **2040** both arms
carry **the same four oil units**, both with the **same `entry_capped` outcome** — i.e. **no non-gas
decision changes**. What moves is their valuation: `capacity_revenue_usd` 0.0 → 14.2–18.6 M and
`depth_usd_per_kw_yr` 25.0 → 14.47, which is the four oil candidates being re-priced off the changed
reserve margin that the **in-scope gas correction** produced. The gate as written tests ledger rows;
its purpose was scope. **At decision level G6 holds in every year**; at byte level it fails in one,
downstream of a change the gate itself expects. Reported as a FAIL, not converted into a PASS.

---

## 2. THE DECISION DELTA — previously UNMEASURED, now measured

**It is a TIMING shift, not a level shift.** The control retires four `gas_cc_ccs` units totalling
**955.076 MW** in **2040**; the arm retires the **identical four units at the identical MW** in
**2038** — two years earlier — and then retires a *further* **1,115.861 MW** (a different four) in
2040.

| year | retirements ctl → arm | retired MW ctl → arm | `gas_cc_ccs` after | reserve margin |
|---|---|---|---|---|
| 2036 | 2 → 2 | 4.371 → 4.371 | 7707.864 → 7707.864 | 0.036696 → 0.036696 |
| 2037 | 0 → 0 | 0.000 → 0.000 | 7707.864 → 7707.864 | 0.088540 → 0.088540 |
| **2038** | **0 → 4** | **0.000 → 955.076** | 7707.864 → 6752.788 | 0.081741 → 0.047660 |
| 2039 | 2 → 2 | 3.255 → 3.255 | 7707.864 → 6752.788 | 0.131172 → 0.097538 |
| **2040** | 4 → 4 | **955.076 → 1115.861** | 6752.788 → 5636.926 | 0.090426 → 0.051645 |

Cumulative retirements through 2040: **962.7 MW (control) → 2,078.6 MW (arm)**.

**The mechanism is the one the read predicted.** `retirements.py:3423`'s `idx_of` is last-write-wins
and `loss_years` is one shared counter, so while the duplicate existed the converted representative
and its unabated twin were addressed as one unit: the exit clock ran on the wrong dispatch and the
955.076 MW cohort's exit was deferred. With the ids distinct, that cohort exits on its own economics
in 2038 and the fleet's accredited `gas_cc_ccs` and reserve margin follow.

**DIRECTION IS REPORTED, NOT SCORED.** The screen is STOP-only. That the repaired trajectory retires
more and earlier is a *measurement*; this lane does not claim it is more accurate beyond the
structural argument that duplicate-free identity is correct. **Scoring the corrected NEISO T3 run is
NOT this lane's** — it routes to the **D63/D65-B batch** on repaired code.

---

## 3. G-DRIFT: form 4 PASSED ON ITS OWN BASIS AND WAS THEN FALSIFIED EMPIRICALLY

This is the methodological finding of the lane and it generalises beyond D88.

**The audit passed, on the strongest available basis.** Per the charter, G-DRIFT's basis is the
bundle's **recorded cache key**, not `git diff <git_sha> HEAD` (dead after the 2026-08-16 rewrite):

```
control bundle                 results/ff-t3-neiso-golden/bau-d65br/NEISO/0fc42cb56c24d544
recorded key (dir name)                                               0fc42cb56c24d544
recomputed at HEAD + D88 from its own committed run_config.json        0fc42cb56c24d544
unknown config keys dropped in the reconstruction                     0
```

Corroborated from the code: `SURFACE_MODULES` excludes `data/fleet` and `model/capacity_evolution`,
and ids are not hashed — so the three edited files cannot move a key by either route.

**And the committed bundle still was not a valid byte-level control.** Grading the arm against it
showed a 2027 delta — a year in which **D88 is provably inert** (`apply_ccs_retrofit` returns below
`ccs_retrofit_available_year` = 2028, and the guard did not fire). An in-container **pre-D88** solve
settles it:

| 2027 comparison | result |
|---|---|
| committed control == D88 arm | **False** |
| **in-container pre-D88 control == D88 arm** | **True** ← attribution |
| in-container pre-D88 control == committed control | **False** |

**The 2027 delta is 100 % this container's derived-input tree and 0 % D88.** `data/clean` is
gitignored, derived and disposable; this container had to rebuild it from `data/raw` (which is
byte-identical to HEAD), and the rebuild moved a `pipeline_events` ordering — the same unit set, one
plant shifted position. A full 2026–2040 pre-D88 control was then solved and every gate re-graded
against it, which is the table in §1.

**The lesson for the program: G-DRIFT form 4 audits CODE drift and cannot see DERIVED-INPUT drift.**
A committed bundle is a valid byte-level control only if the session's `data/clean` reproduces it —
which a fresh container's does not, by construction. Where a form-4 comparison shows a delta in a
year the code says is inert, the cheap resolution is a short same-container control solve, and that
is what earned the one here (rule 29 (b): a LIVE finding earns a control solve, and only for the
years the screen needs).

---

## 4. THE ZERO-LP CENSUS (independent re-derivation of the read's §2.2)

Over **all 72 committed evolution bundles**, keyed on legacy-form `gas_cc_<bin>_<zone>` retrofit rows:

| class | rows | where |
|---|---|---|
| **A. COLLIDING** | 12 | **all nine NEISO T3 golden variants** — `bau` (2032), `bau-d46` + its four `fc6` arms, `bau-d60`, `bau-d65br` (2031, colliding **2037+**), `bau-prera` (**2031, 2040, 2042, 2044** — four generators named `gas_cc_h_class_Central` by 2045) — plus **ERCOT `ff-t1f-d65br`** 2030 (terminal year, no screen reads it) |
| **B. RENAME-ONLY** | 14 | NYISO `d45r`/`d60`/`d65br`, CAISO `d46`/`d60`/`d65br`, MISO `s123/verify`, PJM `s6-pjm/ledger`, ERCOT `d65br` 2029, two later NEISO T3 conversions |
| **C. untouched** | — | **54 of 72** bundles carry no legacy-form retrofit at all |

**In all 26 rows the renamed id appears in NO other decision row in any year** — no retirement, no
floor retention, no thermal addition. That is the byte-identity evidence the charter asked for on one
bundle, obtained on every one.

**Two `unit_id` EXACT-TIE tiebreaks were enumerated in the PRECOMMIT before the solve**, because a
rename can move a unit across a bit-identical tie: `retirements.py:2864` (`(-depth, unit_id)`) and
`adequacy.py:726` (the D57 clearing stack, `(offer, unit_id)`, PJM-armed only). Neither bit in this
screen. `interchange/miso.py:846` filters on `_ref{imp,exp}_` before its `int(uid.rsplit("#"))`
parse, which a renamed id never matches — safe by construction; `legacy_bins.py:599/679` are
coal-only; `eia860.py:2925` runs before any conversion exists.

---

## 5. WHAT LANDED

* **`data/fleet/arrays.py`** — the guard, at the top of `generators_to_fleet_arrays` (same detected
  set as the read's `unit_ids=` line; failing before ~400 lines of array work). Names each duplicated
  id with its multiplicity, ISO and year.
* **`model/capacity_evolution/ccs.py`** — the re-mint, gated on `not is_campd_bin` **and** an exact
  match on `f"gas_cc_{efficiency_bin}_{zone}"`, producing
  `f"gas_cc_ccs_{efficiency_bin}_{zone}_r{year}"` plus the additive `to_unit_id` on the log row.
* **`model/capacity_evolution/evolve.py`** — `exit_exempt_unit_ids` takes the **NEW** id (it is
  matched against the current fleet's `g.unit_id`); `loss_tracker` is popped on the **OLD** id (that
  is the key its loss years accumulated under). **These are different keys and addressing both with
  one silently mis-targets one of them.** The `ccs_retrofits` ledger writer resolves its post-side
  lookup through the rename map — without that hop `uid in _post_ccs` is `False` for every re-minted
  unit and the row is **silently dropped**, which would break the I4 capacity-accounting invariant.
* **`results/cache.py`** — the cache-epoch entry (a true same-key invalidation) naming the nine NEISO
  T3 variants with their keys and ERCOT `d65br`, and what is **not** invalidated.
* **`tests/unit/model/test_ccs_retrofit.py`** — 8 new cases (re-mint; group-key release; two
  conversions in one zone; CAMPD passthrough; non-legacy id untouched; guard silent/raises/names).
  **65 pass** in the file; `tests/unit/model` + `tests/unit/data` = **3,405 passed**.
* **`docs/codebase-site/data/mechanism-matrix/NEISO.js`** — the `ccs_retrofit_screen` cell (rule 28
  duty b). Verdict letter **unchanged at `K`**: a defect repair, nothing armed or disarmed.
* **`frontend/data/forecast/ff-verdicts.json`** — the Q62 flag (§6).

**Zero `ScenarioConfig` fields, zero constants** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`), so rule 28
duty (c) is not engaged. **Zero keys move.** Nothing transferred between ISOs (rule 25).

**Boundaries held:** `ccs.py:475-476` and `evolve.py:664` (D87 lane) and the evolution-ledger
adequacy-block writer (D83 lane) are untouched. **No overlap reached.**

---

## 6. THE FLAG (Q62 second half) — ADDITIVE, AND VERIFIED TO SURVIVE `--reindex`

One field, `provenance.known_defect`, on the `neiso-t3` record. Verified, not asserted:

* **It is the only change to the file.** Re-parsed and compared: with the key removed the document
  is `==` the pre-edit document. `determination` stays `HOLD`.
* **It survives `--reindex`** and reaches the generated namespace.
* **It changes no generated verdict.** Reindexing the whole namespace with and without the flag and
  diffing all **180** generated sidecars: **4 differ, each by exactly `/provenance/known_defect` and
  nothing else** — no verdict letter, no score, no leg status, no other byte.
* **All four flagged runs carry `cache_epoch = f04fd06348e1623d`** (the `bau-d60` bundle), which
  collides **from 2032** — so the flag's wording is exact for every run it reaches.

**Noted, not forced:** `neiso-2026-2050-t3-golden3-d65br` (`cache_epoch = 0fc42cb56c24d544`) is also
in the colliding set but carries **no stamped verdict** (`run_id: None`, an UNSCORED stamp), so there
is no verdict record to flag. Reported here rather than manufactured.

**The re-score is NOT this lane's** — routed to the **D63/D65-B batch** on repaired code.

---

## 7. EIGHTEEN PRE-EXISTING FAILURES ON `main`, NONE OF THEM THIS LANE'S

**Measured both ways after rebasing onto `origin/main` `5e3b6c6a`:**

| tree | result |
|---|---|
| clean `origin/main` (`src` + `tests` checked out from it, D88 absent) | **18 failed, 3,381 passed** |
| this branch (D88 + 8 new D88 cases) | **18 failed, 3,389 passed** |

**The failing set is identical and the +8 is exactly this lane's new tests.** This branch adds eight
passing tests and **zero** failures.

**Sixteen of the eighteen are cache-key pin tests** — `test_default_cache_key_is_unmoved`,
`…_is_byte_stable`, `…_unmoved_and_armed_distinct` and kin across `test_capacity.py`,
`test_scarcity.py`, `test_storage_entry_gates.py`, `test_smr_available_year.py`,
`test_entry_vre_zone_selection.py`, `test_vre_procurement_ffr5e.py`,
`test_capacity_screen_scarcity_restoration.py`, `test_storage_whole_class_accreditation.py`,
`test_ercot219_option_b.py`, `test_caiso_nqc_class_factors.py`,
`test_cc_committed_offer_margin.py`, `test_miso_intermediate_gas_offer_margin.py`,
`test_ramp_envelope_basis.py`, and **two inside `test_ccs_retrofit.py` itself**
(`TestCapexCo2Scaling` / `TestFixedCostCo2Scaling::test_off_is_byte_identical_and_cache_neutral`) —
the latter two verified failing on clean `origin/main` with this lane's edits checked out, precisely
because they sit in the file this lane touched. The signature says something landed on `main` that
**moved the default cache key without re-pinning** it. That is a live registration/pin problem on
`main` and it is **not repaired here** (out of scope, and it is not this lane's key: D88 moves none).

The remaining two are the ones this lane saw before the rebase and are unrelated to keys:
`test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none`, and
`test_caiso_st_gas_peak_measured.py::…::test_registry_value_matches_the_committed_artifact`
(asserts `1.154 != 1.166`; it reads the **committed**
`data/raw/_validation-source/caiso_offer_curve_measured.json`, byte-identical to HEAD here, so it is
not container state either).

**Surfaced for the owning lanes.** Worth treating as stop-the-line for whoever owns the pin: a moved
`PINNED_DEFAULT_CACHE_KEY` with no epoch/pin entry is the exact class the cache-epoch ledger exists
to make visible.

## 8. ROUTED ONWARD

1. **The `neiso-t3` re-score** on repaired code → **D63/D65-B batch**. The nine T3 variants and ERCOT
   `d65br` are named in the cache-epoch entry.
2. **The I5 forecast invariant's own keying** (`check_forecast_invariants.py:482-492`) → the forecast
   desk, **with this guard as the fix**: a re-minted twin following a retired twin is the exact
   false-positive shape of "retire-and-re-enter".
3. **G-DRIFT form 4's derived-input blind spot** (§3) → the audit board, as a method note.
4. **capx D87** may now land: its NYISO screen runs with the guard armed, as the read's §3 sequencing
   requires.
