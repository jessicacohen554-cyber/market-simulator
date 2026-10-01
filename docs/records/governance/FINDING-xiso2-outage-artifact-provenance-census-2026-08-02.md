# xiso-2 — post-guard provenance census of the outage-derived artifacts, all six ISOs

**Session:** xiso-2 (cross-ISO calibration, Arm A). **Date:** 2026-08-02.
**LP spent: ZERO.** No solve, no scoring, no registration, no bundle.
**Probe:** `scripts/probes/_xiso2_outage_artifact_provenance_census.py`
**Transcript:** `results/calibration/PROBE-xiso2-outage-artifact-provenance-census-2026-08-02.txt`

This closes §5.7's **oldest open cross-cutting audit**, flagged in
`docs/calibration-log/governance.md` on 2026-07-26 and still unaudited after xiso-1
cleared the row above it.

---

## 0. Headline

**The corpus is in far better shape than the flag implied, and the two real defects
are both outside the calibration lane.**

* **5 of the 6 committed guard-on standard extracts re-derive BYTE-IDENTICALLY at
  HEAD** (ERCOT, CAISO, NEISO, NYISO, PJM — md5 match on the whole 2018–2026 file).
* **MISO is the sole mismatch**, and it is a clean, fully-attributed one: the
  re-derivation is a strict **superset** (+17 windows, **0 lost**), **all 17 are
  2022 COAL**, its layup companion is byte-identical, and **the 2023–2025 training
  window is identical row-for-row**. Root cause is a **source-data change** —
  commit `5cd937407` (2026-07-31) filled the MISO EIA-930 2022 hourly hole,
  7 rows → 8,760. **No MISO keeper reads a stale byte.**
* **Two artifacts are genuinely PRE-GUARD/stale**, and **neither is consumed by any
  backcast keeper**: `MAINTENANCE_MONTHLY_SHAPE` (forecast-mode only) and
  `caiso-dam-resource-crosswalk.csv` (zero code consumers at all).
* **One live code defect found and FIXED this session**: `derive_maintenance_shape.py`
  pooled `campd-unit-outages*.csv`, a glob that since the guard landed also matched
  the guard's **own vetoed-window companions**. It drew **24 files / 58,744 rows**
  where **6 / 39,755** were intended (**+47.8 %** row inflation).

**No keeper is invalidated by this audit. No re-derive-and-commit sweep was
performed** (per the arm's scope) — the deliverable is this census plus the
per-artifact rule-23 admissibility verdict.

---

## 1. Admissibility, stated up front

This is an **audit, not a mechanism**. It reads committed bytes and re-runs frozen
derive scripts. It arms nothing, changes no `ScenarioConfig` field, and produces no
run. Rule 1 `[R-STRUCT]` is not engaged: there is no fit to move.

**Holdout (rule 20 `[R-HOLDOUT]`).** The extracts span 2018–2026, but only their
**bytes** were compared. Rule 20 explicitly permits "byte-identity /
loader-resolvability checks" on out-of-training data, and forbids solve/scoring/
registration — none occurred. The holdout **spend freeze remains ACTIVE and
untouched**; nothing was solved, scored or registered in any year.

**Rule 23 `[R-FROZEN-DERIVE]` is the governing constraint on any follow-up.** A
re-derivation is admissible only on a **source-data change**, never on a residual.
The audit therefore reports, per artifact, *whether such a change exists* — it does
not perform the re-derivation.

**Reported against interest** throughout: a byte-identical result is a full
deliverable and is stated as prominently as a miss. Where a corrective measurement
did **not** help, that is said plainly (§4).

---

## 2. The guard timeline

The neiso-64 merit-order guard was adopted 2026-07-26 (charter
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §8; governance.md
2026-07-26 "ADOPTED-AS-IMPROVEMENT; holdout freeze HELD"). Every ISO's committed
`campd-unit-outages[-<ISO>].csv` was re-derived guard-on in:

> **`6a8f285c5` — 2026-07-26 00:36:26 +0000 — "neiso-65: adopt guard-corrected CAMPD
> extracts, all six ISOs + layup companions"**

with the vetoed economic-layup windows moved to `campd-unit-outages-layup-<ISO>.csv`
companions that no loader reads by default. That commit is the **post-guard
boundary** used throughout; membership is tested with
`git merge-base --is-ancestor`, not by date string, so same-day ordering is resolved
correctly (this matters — see NYISO in §3).

Note there were **two** extract-content changes in that week: the 2026-07-24
backfill `59f8bc30d` (2018–2026 + EIA-923 fallback) and the guard itself. An
artifact predating **either** is stale with respect to today's extracts; caiso-123
already recorded that the 07-24 change is a separate confound from the guard.

---

## 3. The dependency census

Producers were separated into **real readers** (an actual file read) and
**docstring mentions**, because the naive grep over `campd-unit-outages` returns 60
files, most of which never open one. Only real readers appear below; the excluded
set is enumerated in §3.2 so the exclusion is checkable rather than silent.

### 3.1 Artifacts downstream of a guard-affected extract

| # | Committed artifact | Producer | Last derived | vs guard | Consumer |
|---|---|---|---|---|---|
| 1 | `config/fuel_trajectories.py::MAINTENANCE_MONTHLY_SHAPE` | `derive_maintenance_shape.py` | **2026-06-25** (`1fd092221`) | **PRE-GUARD — STALE** | `data/fleet/arrays.py`, **FORECAST mode only** (`maintenance_monthly_shape`, default **True**) |
| 2 | `data/raw/reference/caiso-dam-resource-crosswalk.csv` | `derive_caiso_dam_resource_crosswalk.py` | **2026-07-19** (`3bdd8df68`) | **PRE-GUARD — STALE** | **NONE** — no code path reads it (docs/findings only) |
| 3 | `reliability_floor_coeffs_NYISO.csv` (NYC/LI/Capital `ST_GAS` limbs) | `derive_nyiso_st_reliability_floor.py` (prints; CSV hand-transcribed) | 2026-07-26 **18:56Z** (`261d7472b`, nyiso-81) | **POST-GUARD** ✓ | `RELIABILITY_FLOOR_REGISTRY` → **NYISO keeper** |
| 4 | `campd-unit-outages-maxgen-MISO.csv` | `derive_campd_maxgen_outages.py` | 2026-07-26 (`6b0d55aab`, miso-94) | **POST-GUARD** ✓ | `unit_outage_maxgen_derate_factors` (gated, default off) |
| 5 | `campd-unit-outages-short-<ISO>.csv` ×5 | `derive_campd_unit_outages.py --short-windows` | 07-28 (CAISO/NEISO/NYISO), 07-31 (MISO/PJM) | **POST-GUARD** ✓ | `unit_outage_short_derate_factors` |
| 6 | `data/clean/**` curated Parquet | `curate_outages.py`, `curate_unit_outage_events.py` | — | **n/a** | gitignored derived tree — regenerated on demand, **no staleness surface by construction** |

**Row 3 is the one that would have mattered and it is clean.** NYISO's ST_GAS
reliability-floor limbs are the only keeper-consumed artifact in the census, and
nyiso-81 re-derived them **18 hours after** the guard landed the same day. Dating by
calendar day would have mis-scored this as ambiguous; the ancestry test resolves it.

### 3.2 Excluded by inspection — mention an extract, never read one

`build_calibration_reference.py` (comment), `build_neiso_operable_capacity.py`
(docstring; reads `morning_report_*.csv`), `derive_ct_deployment.py` (docstring),
`derive_ercot_commitment_loading_state.py` (comment), `derive_partial_outages.py`
(comment; reads CAMPD unit-level directly), `derive_nyiso_ct_reliability_floor.py`
(reads `bin_assignments` + the weather archive), `derive_reliability_coeffs.py` and
the whole `*_drag` derive family (no outage read at all — the reliability-coeff CSVs
for ERCOT/CAISO/MISO/NEISO/PJM are **not** downstream of the outage extracts, which
is why their 06-30…07-08 dates are **not** a staleness finding).

---

## 4. Byte-reproduction of the six standard extracts at HEAD

Each ISO re-derived at HEAD with the recipe the committed files were built from
(`--years 2018 … 2026 --merit-order-guard`), then md5-compared:

| ISO | verdict |
|---|---|
| ERCOT | **BYTE-IDENTICAL** |
| CAISO | **BYTE-IDENTICAL** |
| NEISO | **BYTE-IDENTICAL** |
| NYISO | **BYTE-IDENTICAL** |
| PJM | **BYTE-IDENTICAL** |
| MISO | *** MISMATCH *** |

**5/6 reproduce exactly.** That is a strong positive control on the whole family:
the detector is deterministic, the committed extracts are authentic, and the guard's
classification is reproducible.

### 4.1 MISO — the one mismatch, fully attributed

* Re-derivation is a **strict superset**: **+17 windows, 0 lost** (10,462 vs 10,445
  data rows).
* **All 17 are 2022 `COAL`** windows (durations 5.6–38.6 d; `capacity_source`
  12 `eia_exact` / 3 `observed_peak` / 2 `eia_digits`).
* The **layup companion is byte-identical** (2,424 rows, md5 match) — so the
  merit-order guard's own classification reproduces exactly. The 17 are in
  **neither** the committed kept file **nor** the committed layup file: they were
  never *detected* before, rather than detected-and-vetoed.
* **Not detector drift.** No commit has touched
  `scripts/data/derive_campd_unit_outages.py` or `scripts/lib/outage_detect.py`
  since the guard, and no file under `data/raw/campd-unit-level/` has changed.
* **Root cause — a source-data change.** Commit **`5cd937407` (2026-07-31),
  "eia-930: fill the CISO/MISO 2022 wide-hourly hole (audit §5.1)"** rewrote
  `data/raw/eia-930-hourly/MISO hourly.parquet`. Measured directly:

  | MISO EIA-930 hourly | rows | 2022 rows | 2022 non-null `Demand` |
  |---|---|---|---|
  | before `5cd937407` | 65,712 | **7** | **7** |
  | at HEAD | 74,471 | **8,760** | **8,757** |

  The detector's revealed-availability / high-load filter needs system load. With
  2022 essentially absent it could not retain those windows; with 2022 filled it
  does. The 2022-only, coal-only signature is exactly what that predicts.

* **The 2023–2025 training window is IDENTICAL row-for-row** (3,659 rows each side,
  `DataFrame.equals` → `True`). **The entire divergence sits inside the 2022
  VALIDATION holdout.** No MISO keeper — none of which may solve 2022 — reads a
  stale byte.

* **Honest asymmetry, reported against interest:** the same commit filled the
  **CISO** 2022 hole too, yet **CAISO's extract still reproduces byte-identically**.
  So the 930 fill is not a universal invalidator; MISO's coal fleet is what makes it
  bite. Do not generalise the MISO result to other ISOs — this audit already tested
  all six directly, and only MISO moved.

**Verdict (rule 23):** re-deriving MISO's standard extract is **ADMISSIBLE** — it
rests on a cited source-data change, not a residual. It is also **not urgent**
(training window unaffected) and **must not be done as a side effect of a
calibration session**: rule 23 requires the re-derivation commit to cite the data
change, and rule 20 blocks any 2022 *use* regardless while the freeze is active.

---

## 5. `MAINTENANCE_MONTHLY_SHAPE` — stale, and its refresh path was broken

### 5.1 The glob defect (found and FIXED this session)

`derive_maintenance_shape.py` pooled `glob('data/raw/campd-unit-outages*.csv')`. Its
own docstring states the intended source: the per-ISO extracts written by
`derive_campd_unit_outages.py`, "which have already passed the revealed-availability
filter (economic idling dropped)". At HEAD that glob matched **24 files**:

| bucket | n | why it does not belong |
|---|---|---|
| **STANDARD (intended)** | 6 | — |
| `-layup-` | **6** | the economic-idling windows the guard **exists to veto** — pooling them **partially inverts the guard** (rule 19 `[R-ONE-MECH]`) |
| `-e923-` | 6 | EIA-923 non-CAMPD fallback — a **different source**, double-counting units |
| `-short-` | 5 | sub-5-day companions, a different duration regime |
| `-maxgen-` | 1 | partial **derates**, not full-stop outages |

**24 files / 58,744 rows drawn where 6 / 39,755 were intended — +47.8 % row
inflation.** The glob was harmless when the constant was baked (2026-06-25: no
companion files existed) and became live as companions accumulated —
maxgen 07-16, e923 07-24, **layup 07-26**, short 07-28+. So **the committed constant
is not contaminated; its refresh path was.**

**Fixed:** `load_unit_outages()` now enumerates
`derive_maintenance_shape._STANDARD_EXTRACTS` (the six standard extracts) and raises
on a missing one, instead of globbing. Cited to this finding in the source.

### 5.2 The constant does not reproduce — under either selector

Re-derived at HEAD three ways and compared to the committed constant
(max |Δ| over the 12 monthly weights, per plant group):

| group | max │Δ│ PRE-FIX glob | max │Δ│ standard-6 |
|---|---|---|
| COAL | 0.245 | 0.210 |
| CC_REGULAR | 0.495 | 0.421 |
| CC_CHP | 0.311 | 0.282 |
| CT_PEAKER | 0.375 | 0.239 |
| CT_CHP | 0.595 | **0.710** |
| ST_GAS | 0.350 | **0.417** |
| ST_CHP | 0.362 | **0.428** |
| _POOLED | 0.375 | 0.239 |

**Against interest, and this is the load-bearing caveat: the corrected selector is
NOT uniformly closer to the committed value** — for CT_CHP, ST_GAS and ST_CHP it is
*further*. **Fixing the glob does not restore the committed constant.** The artifact
is genuinely stale with respect to the 2026-07-24 backfill *and* the 2026-07-26
guard, both of which are source-data changes.

**Verdict (rule 23):** re-derivation is **ADMISSIBLE** (two cited source-data
changes) and should now be done on the **fixed** selector, or the contamination
would be baked in. **It was deliberately NOT done here** — the arm's scope is a
census, not a re-derive-and-commit sweep, and this constant is a **forecast-lane**
input whose refresh belongs to a forecast session that can gate it.

### 5.3 Exposure

`maintenance_monthly_shape: bool = True` (`scenarios.py:5189`) and the apply site is
gated `_mode == "forecast"`. So:

* **No backcast keeper consumes it** — every calibration run takes the legacy flat
  shoulder block. This audit invalidates **no** keeper.
* **Every forecast run does**, by default. The stale weights are the live
  forecast-mode planned-maintenance seasonality for all six ISOs.

Because `w` is normalised to a month-length-weighted mean of 1, the **annual POF
budget is conserved exactly** whatever the weights are — the staleness moves
maintenance *between months*, never its total. That bounds the defect but does not
excuse it.

### 5.4 Registry-hygiene note (rule 24 `[R-REGISTRY]`, rule 28 `[R-MECH-MATRIX]` duty c)

`maintenance_monthly_shape` is a solve-affecting `ScenarioConfig` field that is
**absent from the cross-ISO mechanism matrix**. CI does not catch it because
`check_mechanism_matrix.py` diffs new fields against the PR base, so a
pre-existing field is grandfathered — the checker is clean at HEAD. **Filed, not
silently fixed:** the field's per-ISO forecast-lane verdicts have never been tested,
so this session will not invent them; it is recorded on the audit row instead.

---

## 6. `caiso-dam-resource-crosswalk.csv` — stale and inert

Derived 2026-07-19 (caiso-105), **pre-guard**, from `campd-unit-outages-CAISO.csv`.
A repo-wide search finds **no code path that reads it** — the only references are
its own derive script and three prose documents (caiso-105/caiso-106 findings, the
caiso-105 handoff, `docs/calibration-log/caiso.md`).

**Verdict:** stale but **provably inert** — it cannot affect any solve. Re-derivation
is rule-23 admissible (the CAISO extract changed twice) but has **zero** model
consequence; it is a documentation artifact. Flagged as a **registry-hygiene** item,
not a calibration one.

---

## 7. Per-ISO verdicts (rule 25 `[R-ISO-SCOPE]` — reported per ISO, never transferred)

| ISO | extract reproduces? | keeper-consumed artifact stale? | verdict |
|---|---|---|---|
| **ERCOT** | **byte-identical** | no | **CLEAN** |
| **CAISO** | **byte-identical** | no (its one pre-guard artifact is the inert crosswalk) | **CLEAN**, one inert hygiene item |
| **PJM** | **byte-identical** | no | **CLEAN** |
| **MISO** | mismatch, **2022 only** | no — 2023–2025 identical | **CLEAN in the training window**; admissible 2022 re-derivation pending |
| **NYISO** | **byte-identical** | no — ST_GAS floor limbs re-derived post-guard (nyiso-81) | **CLEAN** |
| **NEISO** | **byte-identical** | no | **CLEAN** |

**No ISO's keeper consumes a stale outage-derived artifact.** The 2026-07-26 flag is
answered: the corpus was, with one 2022-scoped exception, already re-derived.

---

## 8. What this licenses, and what it does not

* **Licenses:** a rule-23-admissible re-derivation of `MAINTENANCE_MONTHLY_SHAPE`
  (on the fixed selector, in a forecast session that can gate it) and of MISO's
  2022 extract window (citing `5cd937407`). Both are **optional and non-urgent**.
* **Does not license:** any keeper change, any re-solve, any registration. **No LP
  was spent and none is warranted by this audit** — no keeper input moved.
* **Opens no adjudicated cell** and **transfers no verdict** (rule 25). The MISO
  finding is MISO's; the CAISO null on the same 930 commit is CAISO's.
* **DO-NOT-REDO:** do not re-run this census by hand. Re-run the probe — it
  regenerates the census and the glob measurement in ~1 minute, and takes
  `--verify-extracts DIR` for the byte half.

---

## 9. Changes made this session

1. `scripts/data/derive_maintenance_shape.py` — glob → explicit
   `_STANDARD_EXTRACTS` enumeration (§5.1). Behaviour change to a **derive script's
   input selector**, not to a parameter: no value was tuned, and the committed
   constant was deliberately **left un-re-derived**.
2. `scripts/probes/_xiso2_outage_artifact_provenance_census.py` — new, the
   reproducible record.
3. Docs: §5.7 audit row, mechanism-matrix audit row `outage_artifact_provenance`,
   `docs/calibration-log/governance.md`.

**No `ScenarioConfig` field added or changed. No keeper touched. No bundle
registered** (rule 15 — an arm that spends no LP registers nothing; the
neiso-71/73/74 + xiso-1 disposition).
