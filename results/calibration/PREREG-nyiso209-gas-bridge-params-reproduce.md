# PRE-REGISTRATION — nyiso-209: do the NYISO gas-commitment-bridge parameters reproduce from the shipped derive script at HEAD?

**Session:** nyiso-209, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-6l12xd`, off `main` `992760ec`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — will not change.

**Committed and pushed BEFORE any number is read.** Nothing below was written after seeing a
measurement. §0 discloses exactly what was read first.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3 / v3.6) and is **NOT an objective** of this session. No metrics
file, price series, volume residual or scored criterion will be opened at any point. Rule 1
`[R-STRUCT]` forbids selecting a mechanism because a residual moved, and no mechanism is being
selected here at all. Six consecutive sessions (203–208) returned clean negatives or measurements;
a seventh is a full result.

**Owner ruling (v) — the nyiso-208 card's precedent question on READING out-of-training CAMPD
extracts — has NOT been ruled** (no ruling exists in `docs/`, `results/calibration/`,
`docs/governance/rule-history.md` or `docs/calibration-log/nyiso.md` at this HEAD). The pre-2023
span test is therefore **not taken**, and `NY_2019/2020/2021/2022/2026` will not be read. Rulings
(i)–(iv) are likewise untouched.

---

## 0. Disclosure — what was read before this document was written

Read (definition of the object and its producer): `data/raw/_processed-legacy/`
`campd_gas_commitment_params_NYISO.csv` (the 2-row class summary — the frozen values and their
`source` prose), the committed per-unit detail `campd_gas_commitment_params_NYISO_units.csv`
(78 rows; the header and first four rows only), the CT sibling
`campd_ct_commitment_params_NYISO.csv` (1 row), the full source of
`scripts/data/derive_campd_gas_commitment_params.py`, the `ScenarioConfig` field block
`nyiso_gas_bridge_*` in `config/scenarios.py`, `data/campd.py::ISO_STATES` / `_ONLINE_MW`, the
keeper's `run_config.json` (which fields are armed — NOT `metrics.json`), the keeper's
`calibration_attestation.json` `free_parameters` names, `docs/FINDING-nyiso87` §"Measured
identification" (the derivation record), and the GitHub commit history of the artifact and of
the `NY_2024` / `NY_2025` CAMPD extracts.

Environment checks done and disclosed: the six CAMPD extracts the script reads
(`NY_2023/24/25`, `NJ_2023/24/25`) are on disk **byte-identical to the git index blobs**
(`git hash-object` = `git ls-files -s`), so the source is the committed source.

**Not read, and not run:** the derive script's output at HEAD, any CAMPD grossLoad series, any
per-unit statistic beyond the four header rows above, the HEAD fleet roster the script would
build (`class_plant_codes`), any prior session's re-derivation (none exists — §2).

## 1. The object

**`campd_gas_commitment_params_NYISO.csv`** — produced ONCE by
`derive_campd_gas_commitment_params.py --iso NYISO --detail` on **2026-07-27** (session nyiso-87,
commit `153001ce`) and **never re-derived since**. It carries **four values that are LIVE in the
keeper** (`run_config.json`: `nyiso_gas_commitment_bridge: true`, `nyiso_gas_bridge_min_run: true`):

| keeper field | value | artifact column | class |
|---|---:|---|---|
| `nyiso_gas_bridge_cc_min_load_frac` | **0.523** | `min_load_frac` (= 0.5231…) | CC_REGULAR |
| `nyiso_gas_bridge_st_min_load_frac` | **0.239** | `min_load_frac` (= 0.2394…) | ST_GAS |
| `nyiso_gas_bridge_cc_min_run_hours` | **21.0** | `run_hours_p50_capwtd` | CC_REGULAR |
| `nyiso_gas_bridge_st_min_run_hours` | **13.0** | `run_hours_p50_capwtd` | ST_GAS |

Every one is the identification source of a floor the keeper's headline mechanism (the
startup-aware gas commitment bridge) applies. The CT sibling artifact
(`campd_ct_commitment_params_NYISO.csv`: 0.238 / p25 2 h) feeds `nyiso_gas_bridge_ct_min_load_frac`
and `_ct_min_run_hours`, which are **NOT live** (`nyiso_gas_bridge_ct: false`); it is used here only
as an instrument control (§4 M4).

### 1.1 What the script depends on — and which inputs have moved since 2026-07-27

The construction (docstring, verbatim in the artifact's `source` column): per CAMPD unit,
`HSL = p99.5` of pooled grossLoad, `online = load ≥ max(1.0 MW, 0.05×HSL)`, `LSL = p5` of
online-hour load, `lsl_frac = LSL/HSL`; class value = HSL-weighted p50 across units; run lengths
= maximal online blocks within a year, class p50 HSL-weighted. Its inputs are exactly three:

1. **The CAMPD state-year extracts** `NY_{2023,2024,2025}` + `NJ_{2023,2024,2025}` — **unchanged**
   since 2026-06-18 (commit `95a34668`), i.e. identical to what nyiso-87 read.
2. **The script's constants** `_HSL_PCTILE 99.5`, `_ONLINE_FRAC 0.05`, `_LSL_PCTILE 5.0`,
   `_CLASS_PCTILE 50.0`, `_ONLINE_MW 1.0` — all **match** the artifact's own `source` prose at HEAD.
3. **The model fleet roster** via `load_fleet_from_csv("NYISO")` → `class_plant_codes`: the set of
   plant codes whose fleet rows are CC_REGULAR or ST_GAS, with any plant spanning both classes
   dropped as ambiguous. **This is the input that HAS moved.** Since 2026-07-27 the NYISO fleet
   went through the Astoria split-facility routing (nyiso-187), `cc_capacity_reconcile`
   (nyiso-188), the steam-collapse heat-rate identity (nyiso-189), the merit-order panel
   (nyiso-192) and the Cricket Valley id repair (nyiso-196), among others. Whether any of those
   changed a plant's **class membership** — the only thing this script takes from the fleet — is
   unknown before measuring, and is the natural drift channel.

**Arithmetic on the live seam:** `ScenarioConfig` carries the two fractions rounded to 3 dp and
the two run hours as integers, so the *live* reproduction criterion is
`round(min_load_frac, 3) ∈ {0.523, 0.239}` and `run_hours_p50_capwtd ∈ {21.0, 13.0}` — the
committed CSV carries full float precision, which gives a second, stricter byte-level criterion.

## 2. Why this is new work and not a DO-NOT-REDO violation

nyiso-207/208 established that the NYISO **reliability-floor** derive scripts reproduce nine of
ten live coefficients at HEAD. **No session has ever re-run `derive_campd_gas_commitment_params.py`
against its committed artifact** — the artifact has one commit. This is the same
reproduce-from-source test, on a **different mechanism's** artifact (`gas_commitment_bridge`, a
`K` cell), and it re-opens none of the five closed reliability-floor columns (membership, fill
order, fill level, coefficient basis, coefficient identification). No cell marked `R`/`I`/`G` in
`docs/codebase-site/data/mechanism-matrix/NYISO.js` is re-tested. It is not a tuning lever: no
value can be chosen here.

## 3. Instrument

**The shipped script itself**, run with its own defaults —
`--iso NYISO --years 2023 2024 2025 --detail --out <scratchpad path>` — so the committed artifact
is **never overwritten**. The probe `scripts/probes/_nyiso209_gas_bridge_params_reproduce.py`
runs it, diffs the class summary and the per-unit table against the committed files, and calls
the shipped `class_plant_codes` by import for M3. **Zero LP.** Rule 29 `[R-SCREEN]` step 0 gates
the solve to zero: the only outcomes on the table are a measurement and possibly a card,
**neither of which is an arm**, so no screen year is pre-registered because there is nothing for
a screen to gate.

## 4. Measurements

- **M1 — the four live values.** HEAD `min_load_frac` and `run_hours_p50_capwtd` for CC_REGULAR
  and ST_GAS vs the committed row, at (a) full float precision (`|Δ| ≤ 1e-9`) and (b) the live
  3-dp / integer seam (§1.1).
- **M2 — every other column of the class summary** (`n_units`, `n_plants`, `capacity_mw`,
  `min_load_frac_p25/p75`, `online_frac`, `n_runs`, all ten run-hour percentiles), reported as
  a per-column equal/unequal table. Context for M1, never a verdict on its own.
- **M3 — the roster.** The HEAD `class_plant_codes("NYISO")` mapping and its ambiguous list vs
  the plant set implied by the committed `_units.csv` (29 plants: 19 CC_REGULAR + 10 ST_GAS,
  78 units). Report added / removed / re-classed plants by code and name, and which class each
  touches.
- **M4 — the per-unit table.** HEAD `_units.csv` vs committed: the set of `(plant_code, unit_id)`
  keys (78 committed), and for every common key `hsl_mw`, `lsl_mw`, `lsl_frac`, `online_hours`,
  `n_runs`, `median_run_hours` at `|Δ| ≤ 1e-9`.
- **M5 — CT control.** `--ct --out <scratchpad>`: `min_load_frac`, `run_hours_p25_capwtd`,
  `n_units`, `n_runs` vs the committed CT artifact (0.238 / 2 / 80 / 34,024).
- **O1 — a read, not a measurement, reported in every branch:** the keeper's
  `calibration_attestation.json` `free_parameters` (13 entries) carries **no entry** naming this
  artifact or the four fields it identifies, while the analogous
  `campd_ct_run_lengths_NYISO.csv` **is** ledgered as `measured-physical`. Whether a measured
  identification source must appear in the rule-21 `[R-DOF]` ledger is an attestation-content
  question this lane reports and does not decide.

## 5. Predictions — signs, magnitudes, and their mutual consistency

The measurements partition cleanly on two binary facts: **is the unit set identical (M4 keys)?**
and **do the four live values reproduce at the live seam (M1b)?**

**P1 — FULL REPRODUCTION.** *(This session's preferred answer.)* M4 key set identical (78 = 78),
every common-key statistic equal to 1e-9, M1a all four `|Δ| ≤ 1e-9`. Mechanism: the CAMPD input
is byte-identical and the script constants match, so the only way to miss is the roster.

**P2 — THE PREDICTION THAT CUTS AGAINST P1: ROSTER DRIFT ON THE CC SIDE.** Every NYISO fleet
repair since 2026-07-27 named in §1.1(3) touched a **combined-cycle** plant (Astoria I/II, Cricket
Valley, the CC capacity reconcile, the CC steam-collapse identity). P2 predicts: M3 shows the
CC_REGULAR plant set changed by **1–3 plants** (added, removed, or newly ambiguous), the
**ST_GAS plant set is unchanged**, and M4's key set differs on the CC side only. **Magnitude
prediction that can hurt P2 itself:** a weighted p50 over 35 CC units is a robust order
statistic, so under P2 the CC `min_load_frac` moves by **|Δ| < 0.02** and — because the live seam
is 3 dp — **may or may not** still round to 0.523; CC `run_hours_p50_capwtd` moves by **≤ 4 h**.
ST_GAS values are predicted **byte-identical** under P2. *If the ST_GAS set changes, P2's
mechanism story is wrong and will be reported as wrong.*

*P1 and P2 are mutually exclusive* (P1 requires an identical key set; P2 requires it to differ)
and leave a declared third outcome: an **identical unit set with moved values** — which, given
identical inputs and constants, can only be the script or its numeric dependencies changing
behaviour, i.e. an instrument problem.

**P3 — THE CT CONTROL REPRODUCES.** M5: `|min_load_frac − 0.2381| ≤ 1e-6`, `run_hours_p25_capwtd
= 2.0`, `n_units = 80`, `n_runs = 34,024`. The CT roster is a different class set
(`CT_PEAKER`, restricted to CAMPD `unitType == "Combustion turbine"`), and no CT-class plant
repair is named in §1.1(3). **Cuts against the session:** if P3 fails while the CC/ST roster is
unchanged, the instrument itself has drifted and nothing about M1 can be attributed to the
roster. *Consistency with P2:* P2-true and P3-true are consistent (P2 is a CC-side roster claim;
the CT path never touches CC plants).

## 6. Pre-registered verdicts and the decision rule

| verdict | condition | consequence |
|---|---|---|
| **R — REPRODUCES** | P1 ∧ P3 | All four live gas-bridge parameters regenerate byte-exactly from committed source at HEAD. **Clean negative — a full result.** No card. O1 reported. |
| **D — ROSTER DRIFT, LIVE VALUES INTACT** | ¬P1 ∧ M4 keys differ ∧ M1b all four hold ∧ P3 | The artifact's provenance columns (`n_units`, `capacity_mw`, …) no longer describe the roster the script would use, but every live value survives at the seam it is consumed at. **No card, no edit**: reported as a stale-provenance note with the changed plants named; whether a roster change is a rule-23 `[R-FROZEN-DERIVE]` source-data trigger is stated as an open question, not decided. |
| **U — UNIDENTIFIED** | M4 keys differ ∧ any of the four fails M1b ∧ P3 | A live keeper coefficient on a CALIBRATED ISO no longer reproduces from its own stated construction at HEAD. **Owner card. No coefficient is edited, no replacement value is proposed** — the HEAD value is reported as *a measurement of the gap*. |
| **X — INSTRUMENT** | (M4 keys identical ∧ any M1a fails) ∨ ¬P3 | The script does not regenerate its own artifact from identical inputs. **Owner card**; nothing is concluded about the roster. |

O1 is reported in every branch. Any check not listed in §4 that is run after a number is read
goes in an addendum labelled **POST-HOC**, committed before it is executed, with its
multiple-comparison caveat and reporting rule fixed in advance.

## 7. What this session will NOT do — declared in advance so a clean result cannot become a licence

- **No coefficient is edited and no replacement value is proposed**, in any branch. The committed
  CSVs, `ScenarioConfig` defaults and the keeper's `run_config.json` are read-only to this
  session. A HEAD value that differs is reported as a *measurement of the gap*, never as a
  candidate. Rule 23 `[R-FROZEN-DERIVE]` governs re-derivation and that is an owner call.
- **No derive script, `ScenarioConfig` field, CSV row, `src/market_sim/` file or scorer file is
  changed.** Zero DOF, zero registered fields, zero re-derivations into any tracked artifact
  (the script is run with `--out` into the scratchpad; the untracked `NYISO_fleet_binned.parquet`
  side-output is not a tracked file).
- **No other ISO is measured** (rule 25 `[R-ISO-SCOPE]`). The script has per-ISO siblings
  (`CAISO` artifacts are committed); their exposure stays unmeasured here.
- **No `offer_curve_by_group` band multiplier is touched** — owner court under carve-out
  condition (c).
- **No out-of-training year is solved, scored, registered — or read** (rule 22; ruling (v)
  pending). 2023–2025 extracts only.
- **No marker is touched.** `complete` (WITHDRAWN, Q5) and `frontier` re-entry are owner acts;
  C-19 / Q51 stays PARKED. No keeper promotion, no re-stamp, no registration.
- **The five pending owner rulings are not taken**: nyiso-206 (i), nyiso-207 (ii), nyiso-203 §6
  (iii), `DECISION-CARD-nyiso193` §5/§5.1 (iv), nyiso-208 (v).
- **Rule 20 `[R-FORCED-BUDGET]` leg (a) stays open**; the unit-grain C8 exposure is untouched.
- **The reliability-floor mechanism is not re-opened** on any of its five closed columns.

## 8. Governance

| item | state |
|---|---|
| **LP** | **zero.** Rule 29 step 0 gates it; no arm is on the table, so no screen year is pre-registered |
| **Rule 29(b) G-DRIFT** | being re-validated **EMPIRICALLY** at this HEAD in parallel with this PREREG: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` after the targeted `curate_capacity_deliverability` + `curate_nyiso_interface_flows` rebuild; `git status --porcelain -uno` must be EMPTY. Result recorded in the finding. G-CTRL form 4 valid; no control solve owed or spent (nothing is differenced against a solve). *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate, an `R` cell, part of the committed record and **not** a drift signal.)* |
| **Rule 26 `[R-MECH-MATRIX]`** | NYISO shard `gas_commitment_bridge` cell updated in **this** session whatever the verdict, with the key set diffed against `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing to register — no run, no bundle. Git history + the finding are the record |
| **Rule 29(c)** | no screen or control bundle will exist, so there is nothing to delete before merge |
| **Rule 27 `[R-PUSH]`** | any push touching a file ≥ 300 lines gets a blob verification before the next commit |
| **Deliverable** | a measured finding on a named object, plus an owner card **only** under verdicts U or X. **A clean negative (R, or D) is a full result.** |

---

*(nyiso-209 pre-registration. Zero LP. Predictions declared with their signs, their magnitudes,
the one that cuts against the session's preferred answer, and their mutual consistency checked.)*
