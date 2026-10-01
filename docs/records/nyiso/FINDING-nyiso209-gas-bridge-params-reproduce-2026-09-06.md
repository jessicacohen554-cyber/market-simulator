# FINDING — nyiso-209: the shipped `derive_campd_gas_commitment_params.py` regenerates the NYISO gas-commitment-bridge artifact **byte-identically** at HEAD. All four keeper-live parameters reproduce to 1e-9; the session's own roster-drift counter-prediction is **refuted**. Clean negative.

**Session:** nyiso-209, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-6l12xd`, off `main` `992760ec`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — **UNCHANGED**.
Nothing promoted, nothing registered, no `ScenarioConfig` field, no coefficient edit, no CSV edit,
no derive-script edit, no `src/market_sim/` change, no scorer change, no marker touched.

**ZERO LP WAS SPENT.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero, as the PREREG said it
would: the only outcomes on the table were a measurement and possibly a card, **neither is an
arm**, so no screen year was pre-registered because there was nothing for a screen to gate.

**PREREG:** `results/calibration/PREREG-nyiso209-gas-bridge-params-reproduce.md` — committed and
pushed **before any number was read** (`b9ad2ec5`). No POST-HOC addendum was needed: every check
reported here is one the PREREG declared.
**Instrument:** the **shipped** `scripts/data/derive_campd_gas_commitment_params.py`, run as a
subprocess with its own defaults and `--out` into the scratchpad;
`scripts/probes/_nyiso209_gas_bridge_params_reproduce.py` →
`results/calibration/_nyiso209_gas_bridge_params_reproduce.json`.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3 / v3.6) and was **not an objective**. **No metrics file, price
series, volume residual or scored criterion was opened at any point in this session.**

**Owner ruling (v) — the nyiso-208 precedent question — has NOT been ruled.** No ruling exists
anywhere in the repo at this HEAD, so the pre-2023 span test was **not taken** and
`NY_2019/2020/2021/2022/2026` were **not read**. Rulings (i)–(iv) are untouched.

---

## 0. Verdict in one paragraph

nyiso-207 and nyiso-208 established that the NYISO reliability-floor derive scripts are faithful
(nine of ten live coefficients regenerate exactly). **The equivalent had never been established for
any other NYISO derived input.** This session ran the same reproduce-from-source test on the
artifact that identifies the keeper's headline mechanism — the startup-aware gas commitment
bridge's four live parameters, `campd_gas_commitment_params_NYISO.csv`, derived once on
2026-07-27 (nyiso-87) and never re-derived. **Result: the shipped script regenerates the class
summary, the 78-row per-unit table AND the CT sibling artifact byte-for-byte at HEAD** (`cmp`
identical, all three files). The four keeper-live values — CC `min_load_frac` 0.5231, ST_GAS 0.2394,
CC min-run 21 h, ST_GAS min-run 13 h — reproduce to 1e-9, every other summary column is equal,
and the unit population is identical (78 = 78 keys, zero per-unit statistic differences). The
pre-registered verdict is **R — REPRODUCES**. The session's own counter-prediction — CC-side roster
drift from the five fleet repairs landed since 2026-07-27 — is **refuted**: the HEAD roster differs
from the 07-27 unit population only by three CC plant codes that have **no CEMS hours under their
own id** and so contributed nothing on either date. **Clean negative; a full result. Nothing is
proposed.**

**Not a keeper candidate. There is nothing to promote.**

---

## 1. The object

`data/raw/_processed-legacy/campd_gas_commitment_params_NYISO.csv`, produced by
`derive_campd_gas_commitment_params.py --iso NYISO --detail` in commit `153001ce` (2026-07-27,
nyiso-87) and untouched since. Four of its values are **live in the keeper**
(`run_config.json`: `nyiso_gas_commitment_bridge: true`, `nyiso_gas_bridge_min_run: true`):

| keeper field | live value | artifact column | class |
|---|---:|---|---|
| `nyiso_gas_bridge_cc_min_load_frac` | 0.523 | `min_load_frac` = 0.5231316… | CC_REGULAR |
| `nyiso_gas_bridge_st_min_load_frac` | 0.239 | `min_load_frac` = 0.2393617… | ST_GAS |
| `nyiso_gas_bridge_cc_min_run_hours` | 21.0 | `run_hours_p50_capwtd` | CC_REGULAR |
| `nyiso_gas_bridge_st_min_run_hours` | 13.0 | `run_hours_p50_capwtd` | ST_GAS |

The construction is stated verbatim in the artifact's own `source` column: per CAMPD unit,
`HSL = p99.5` of pooled grossLoad, online = `load ≥ max(1.0 MW, 0.05 × HSL)`, `LSL = p5` of
online-hour load, `lsl_frac = LSL / HSL`; class value = HSL-weighted p50 across units; run lengths
= maximal online blocks within each year, class p50 HSL-weighted.

### 1.1 The three inputs, and which one could have moved

| input | state at HEAD vs 2026-07-27 |
|---|---|
| CAMPD extracts `NY_{2023,24,25}`, `NJ_{2023,24,25}` | **unchanged** since 2026-06-18 (`95a34668`); on disk byte-identical to the git index blobs |
| script constants (`_HSL_PCTILE` 99.5, `_ONLINE_FRAC` 0.05, `_LSL_PCTILE` 5.0, `_CLASS_PCTILE` 50, `_ONLINE_MW` 1.0) | **match** the artifact's `source` prose |
| the model fleet roster → `class_plant_codes("NYISO")` | **has moved**: Astoria split-facility routing (nyiso-187), `cc_capacity_reconcile` (188), steam-collapse HR identity (189), merit-order panel (192), Cricket Valley id repair (196) |

So the only live drift channel was the roster, and the PREREG's counter-prediction P2 was built on
it (§3).

## 2. The result — byte-identical, on every leg

**The shipped script's three outputs, `cmp`'d against the committed files:**

| file | rows | result |
|---|---:|---|
| `campd_gas_commitment_params_NYISO.csv` | 2 | **BYTE-IDENTICAL** |
| `campd_gas_commitment_params_NYISO_units.csv` | 78 | **BYTE-IDENTICAL** |
| `campd_ct_commitment_params_NYISO.csv` (control, `--ct`) | 1 | **BYTE-IDENTICAL** |

**M1 — the four live values** (PREREG §4):

| value | committed | HEAD | Δ | at the live seam |
|---|---:|---:|---:|---|
| CC `min_load_frac` | 0.5231316725978647 | 0.5231316725978647 | 0 | rounds to **0.523** ✓ |
| ST_GAS `min_load_frac` | 0.2393617021276596 | 0.2393617021276596 | 0 | rounds to **0.239** ✓ |
| CC `run_hours_p50_capwtd` | 21.0 | 21.0 | 0 | **21** ✓ |
| ST_GAS `run_hours_p50_capwtd` | 13.0 | 13.0 | 0 | **13** ✓ |

**M2** — all 34 other numeric summary cells (`n_units` 35 / 43, `n_plants` 19 / 10, `capacity_mw`
7,162.5 / 7,605.4, p25 / p75 fractions, `online_frac`, `n_runs` 4,808 / 10,976, all ten run-hour
percentiles): **0 unequal**; both `source` prose strings identical.

**M4 — per-unit table:** 78 committed keys, 78 HEAD keys, **key set identical**; over all 78 common
keys and six statistics (`hsl_mw`, `lsl_mw`, `lsl_frac`, `online_hours`, `n_runs`,
`median_run_hours`): **0 differences at 1e-9**.

**M5 — CT control** (not live: `nyiso_gas_bridge_ct: false`): `min_load_frac` 0.238095…,
`run_hours_p25_capwtd` 2.0, `n_units` 80, `n_runs` 34,024 — **all exact**, 0 columns unequal.
**P3 CONFIRMED**, so the instrument is validated on an independent class roster and code path.

## 3. The counter-prediction, refuted — and why the roster moved without the population moving

PREREG §5 declared two mutually exclusive outcomes and a third:

| prediction | condition | measured | verdict |
|---|---|---|:---:|
| **P1** — full reproduction | key set identical ∧ all four exact | 78 = 78, Δ = 0 | **TRUE** |
| **P2** — CC-side roster drift (*the one that cut against P1*) | key set differs on the CC side | key set identical | **FALSE** |
| — | identical keys, moved values (instrument) | — | not reached |

**M3 explains why P2 failed without the roster being static.** `class_plant_codes("NYISO")` at HEAD
returns **32 target plants (22 CC_REGULAR + 10 ST_GAS)** against the **29 (19 + 10)** that carry
committed unit rows, and drops **one** code as mixed-class:

| HEAD roster fact | plant | why it changes nothing |
|---|---|---|
| CC code with no committed units | 7784 Allegany Cogen (Upstate_West) | no CEMS hours under its own id in the six extracts → contributes no unit on either date |
| CC code with no committed units | 54808 New York University Central Plant (NYC) | same |
| CC code with no committed units | 57664 Astoria Energy II (NYC) | CAMPD files its CT3/CT4 under **55375** (the nyiso-187 routing object); 55375 is itself CC_REGULAR in the roster, so those units were and are counted under 55375, **same class** |
| dropped as mixed-class | 2500 Ravenswood (NYC: ST_GAS + CC_REGULAR) | absent from the committed `_units.csv` too, so it was dropped identically on 2026-07-27 (the script prints the same `(dropping 1 mixed-class plant code(s) … [2500])` note) |

Whether 7784 / 54808 / 57664 were also in the 07-27 roster cannot be read from the artifact (a
plant with no CEMS hours leaves no trace), and it does not matter: the unit population the
statistics are taken over is **identical**, which is the fact P2 turned on. **Every fleet repair
since 07-27 touched a CC plant's capacity, heat rate, outage attribution or CAMPD-unit routing —
none touched a plant's class membership**, which is the only thing this script takes from the fleet.

## 4. Two observations — reported, not acted on

**O1 (pre-registered read).** The keeper's `calibration_attestation.json` `free_parameters` ledger
(13 entries) carries **no entry** naming this artifact or the four fields it identifies, while the
analogous `campd_ct_run_lengths_NYISO.csv` **is** ledgered as `measured-physical`. Under rule 21
`[R-DOF]` the ledger lists "each free parameter with its identification source"; whether a
measured-physical identification source that is *not* a free parameter belongs in it is an
attestation-content question. Reported for the owner; this lane does not edit the attestation.

**O2 (an observation on the construction, from the script's own stdout — labelled so because it is
not one of the PREREG's measurements).** The facility-level ambiguity drop excludes **Ravenswood
2500** — 1,724.8 MW of ST_GAS, the class's largest plant (per the matrix
`thermal_tranche_artifact_coverage` cell's own census) — from the ST_GAS `min_load_frac` and
min-run statistics, by the script's declared construction ("a plant whose model fleet rows span
more than one target class … is dropped with a printed note"). The 0.239 the keeper applies to
Ravenswood's steam tranches is therefore measured on the **other** nine ST_GAS plants. This is not
drift and not an error in the script; it is a scope property of the coefficient's identification
basis, and it bears on pending owner rulings **(i)** (nyiso-206: aggregate share vs per-unit rule)
and **(ii)** (nyiso-207: must identification basis match application basis). **It is not ruled
here and no change is proposed.** The `--ct` path already solves the same problem for CTs via
CAMPD `unitType`; whether an analogous `unitType`-scoped attribution is admissible for steam is an
owner question, not a lane fix.

## 5. What is deliberately NOT taken — named so silence is not read as absence

- **No coefficient is edited and no replacement value is proposed** — there is none to propose;
  every value reproduces.
- **No derive script, `ScenarioConfig` field, CSV row, `src/market_sim/` file, scorer or
  attestation is changed.** The script was run with `--out` into the scratchpad; the committed
  artifacts were never written.
- **No other ISO is measured** (rule 25 `[R-ISO-SCOPE]`). The CAISO siblings of this artifact are
  equally untested and were not tested here.
- **No out-of-training extract was read** (rule 22; ruling (v) pending).
- **The `offer_curve_by_group` channel was not touched** — owner court under carve-out
  condition (c).
- **The five pending owner rulings are untouched** — nyiso-206 (i), nyiso-207 (ii), nyiso-203 §6
  (iii), `DECISION-CARD-nyiso193` §5/§5.1 (iv), nyiso-208 (v). §4 O2 notes that Ravenswood bears
  on (i)/(ii); it does not rule them.
- **The reliability-floor mechanism is not re-opened** on any of its five closed columns.
- **Rule 20 `[R-FORCED-BUDGET]` leg (a) stays open**; the unit-grain C8 exposure (ST_GAS
  0.351 / 0.343 / 0.268 vs the 0.30 cap) is unchanged.
- **No marker is touched.** `complete` (WITHDRAWN, Q5) and `frontier` re-entry are owner acts;
  C-19 / Q51 stays **PARKED**.

## 6. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 step 0 gated it; no arm was on the table, so no screen year was pre-registered |
| **Rule 29(b) G-DRIFT** | **re-validated EMPIRICALLY at this HEAD, not by reading hunks:** after the targeted `curate_capacity_deliverability` + `curate_nyiso_interface_flows` rebuild, `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git status --porcelain -uno` **EMPTY** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically. G-CTRL form 4 valid; **no control solve spent**, none owed. *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate, an `R` cell; part of the committed record, **not** a drift signal.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **UNCHANGED**. Not a keeper candidate; no promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual; none selected at all |
| **Rule 21 / 23** | zero fields, zero DOF entries, **zero re-derivations into any tracked artifact** |
| **Rule 22 `[R-HOLDOUT]`** | 2023–2025 extracts only; nothing out-of-training solved, scored, registered or read |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only |
| **Rule 26 / 28 `[R-MECH-MATRIX]`** | NYISO shard `gas_commitment_bridge` cell updated **in this session** (cell unchanged at `K`, evidence appended); key set verified identical to `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing registered — no run finished, so there is no run. Git history + this finding are the record |
| **Rule 29(c)** | no screen bundle and no control bundle exist, so there is nothing to delete before merge |
| **Rule 27 `[R-PUSH]`** | the shard (930 lines) is blob-verified after push before any further commit |
| **Files added** | 1 probe, 1 JSON record, 1 PREREG, this finding; 1 shard cell edited. **No `src/market_sim/` change, no CSV edit, no derive-script edit, no scorer edit** |

### 6.1 Reported, not fixed — other lanes' pre-existing failures at HEAD

**Re-measured** at this session's HEAD over the charter's six named files (this session's tracked
changes are additive only): **36 failed / 69 passed** — **one fewer failure than nyiso-206/207/208's
37 / 68.** `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` now
**PASSES** on `main` (fixed by another lane between nyiso-208's HEAD `a6e4b6db` and `992760ec`).
The other five files are unchanged, failure for failure:

| file | failures | owner |
|---|---:|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 15 | capx |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | 12 | capx |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF-readiness |
| `tests/scoring/test_collate_scenario_campaign_common_set.py` | 4 | SCN-WS5A-LOAD |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | CAISO |

**Not fixed from this lane** (rule 25): none is NYISO's file or NYISO's number.

## 7. What this closes, what stays open

**Closed — DO-NOT-REDO.** The gas-commitment-bridge parameter artifact and its CT sibling are
**reproducible byte-for-byte** from committed source at HEAD; every keeper-live value it identifies
(0.523 / 0.239 / 21 h / 13 h) and the non-live CT pair (0.238 / 2 h) regenerate exactly. With
nyiso-207/208, that is now **two of the keeper's measured-input families** (reliability-floor
coefficients; gas-bridge parameters) whose derive pipelines are shown not to be drifting. Do not
re-run this test on this artifact without a source-data change.

**Established (positive).** The roster the script reads **has** moved since 2026-07-27 (32 vs 29
target plants) without moving the unit population — the five fleet repairs since then changed
capacities, heat rates, outage attribution and CAMPD routing, never class membership.

**Open, for the owner (no card — nothing is broken).** O1: whether a measured-physical
identification source belongs in the rule-21 ledger when it is not a free parameter. O2: the
ST_GAS statistic is identified on a roster that excludes Ravenswood by the script's declared
ambiguity rule — a basis-scope fact bearing on rulings (i)/(ii). The remaining untested NYISO
derived inputs — `campd_ramp_envelopes_NYISO.csv`, the eGRID family / identity / steam-collapse
heat-rate artifacts — are the natural next objects for the same zero-LP test.
`DECISION-CARD-nyiso193`, `-nyiso206`, `-nyiso207` and `-nyiso208` all remain **UNRULED**.

---

*(nyiso-209, 2026-09-06. Zero LP. Three files regenerated byte-identically from committed source,
four live coefficients reproduced to 1e-9, an instrument control passed on an independent code
path, and this session's own counter-prediction refuted. A clean negative, reported as one.)*
