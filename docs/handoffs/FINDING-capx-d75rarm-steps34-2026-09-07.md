# FINDING — capx D75-R-ARM steps 3–4: the bare `pjm-t1h` re-solved at the DECLARED key and registered; realized == declared, 14/14 invariants PASS, and the row is a JOINT Q55+Q56 posture

**Lane:** capx D75-R-ARM **steps 3–4**, released by the r#54 charter re-emission. **Branch:**
`claude/capx-d75r-arm-steps34-mc5342`. **Solve HEAD:** `10cda1fa` (guard held). **Model:** Opus.
**DATA PROFILE:** `pjm`. **Binding:** `PRECOMMIT-capx-d75r-arm-2026-09-06.md` +
its `ADDENDUM-B-steps34` (every number below was declared there **before** the LP ran) +
`FINDING-capx-d75r-2026-09-06.md` + the D67-ARM precedent.

---

## 0. THE ANSWER

**The key question the charter made load-bearing: the bare `pjm-t1h` recipe carries
`fb16fda2ddb0a94a` at this head — NOT the `b518f5fe7d02f961` the charter's body names.** D78-ARM
merged (`24311a95` + the `fd2a0d18` salvage, PR #5373) before this lane was dispatched, so the
charter's branch B applies. Declared in ADDENDUM B and pushed before any LP; **the solve realized
exactly that key**.

| | |
|---|---|
| declared key (pushed pre-solve) | `fb16fda2ddb0a94a` |
| **realized key** (`meta.json`) | **`fb16fda2ddb0a94a`** |
| verdict | **realized == declared** — the arm reproduces the recipe the Q55/Q56 A/Bs were measured on; neither basis needs re-reading |
| HEAD guard | `10cda1fa`, **held** (no commit made while the LP ran) |
| invariants | **14 PASS, 0 FAIL, 0 WARN** |

---

## 1. STEP 3 — the solve

One invocation, PJM solo, 2021–2025 **sequential** (rule 12 `[R-PARALLEL]`), through
`docs/handoffs/d75rarm/run_steps34.sh`, which carries both guards fail-closed (HEAD → `exit 90`,
key mismatch → `exit 91`). The governance banner records the tier discipline in the run's own words:

> this window **SOLVES [2021, 2023, 2024, 2025]** and **BRIDGES [2022]** (evolved across, LP never
> solved, measured data never read — rule 22)

`leakage_violations: []`. No out-of-training year solved, scored or registered; **no marker spent**.

**The bundle:** `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm`, retention class
D67-ARM's — the 13 slim ledgers committed (`evolution_*.json`, `score.json`, `solve_surface.json`,
`year_*_floor_retentions.json`, `meta.json`, `run_config.*`), the heavy `year_*.parquet` /
`config.yaml` / `*.npz` gitignored. This is a **registered** bundle, not a screen, so rule 29(c)'s
delete-before-merge does not apply to it.

---

## 2. STEP 4 — the registration, and what it touched

Registered through the **SINGLE** `scripts/register_forecast_run.py` path (rule 15). The
`VERDICT_MAP` re-key lands **in the same commit as the registration** — correct at registration and
wrong before it, which is why the D78-ARM salvage held its own version of that hunk:

| bundle | verdict id | |
|---|---|---|
| `pjm-2021-2025-realized-t1h-d67arm` | `pjm-t1h-pre-d75rarm` | preserved verbatim, its own verdict standing, **nothing re-scored** |
| `pjm-2021-2025-realized-t1h-d75rarm` | **`pjm-t1h`** | the shipped PJM T1-H posture from here on |

**Which artifact the registration touches — resolved from the code path, as the charter's closing
NOTE asks, and confirmed by the run.** `register_forecast_run.py` declares
`frontend/data/hindcast` *"the CANONICAL per-run record"* and writes
`frontend/data/hindcast/pjm-2021-2025-realized-t1h-d75rarm.json`. `ff-verdicts.json` is a
**committed input, READ and never written** by that script (`_load_verdicts`; the module docstring
names it *"the source, NOT output"*), so it **moves only when a verdict moves** — and this
registration did not touch it. The generated namespace (`registry/`, `runs/`, `manifest.js`,
`program-status.js`) is gitignored; the Pages deploy is its single writer. Corroborated by the
committed record: the live `ff-verdicts.json` `pjm-t1h` entry still names
`pjm-2021-2025-realized-t1h-d57-clearing` at `f0e050e820c1159a` — **D67-ARM's own registration did
not move it either**, for exactly the same reason.

### 2.1 The preserved name is `-pre-d75rarm` ON THE MERITS, not merely by charter

The charter names `pjm-t1h-pre-d75rarm`; the D78-ARM salvage's held hunk names the same bundle
`pjm-t1h-pre-d78arm`. **They are not interchangeable and the charter's is correct:** the bundle is
`a9c66d8ea25acb9d`, the posture immediately **before D75-R-ARM**. The posture immediately before
D78-ARM is `b518f5fe7d02f961`, and **no bundle at that key exists to preserve** — D76-P3B solved it
as its own control and deleted it before merge under rule 29(c). `-pre-d78arm` would label an
`a9c66d8ea25acb9d` bundle with a `b518f5fe7d02f961` posture's name.

---

## 3. THE ROW IS A JOINT Q55+Q56 POSTURE — the load-bearing consequence

At this head there is **exactly ONE bare `pjm-t1h` recipe and it carries both ruled arms**. Two
things follow, both declared in ADDENDUM B §2 before the solve:

1. **No number in §4 may be attributed to Q55 alone.** The isolated attribution already exists and
   is untouched: `FINDING-capx-d75r-2026-09-06.md`'s A/B, control `a9c66d8ea25acb9d` → arm
   `b518f5fe7d02f961`, on one base. This registration does not re-open, re-measure or supersede it.
2. **This solve IS the solve D78-ARM still owed** — `docs/handoffs/d78arm/run_arm.sh` is the same
   invocation at the same key against the same control (`FINDING-pr5319-d78arm-salvage-2026-09-07.md`
   §4 item 1). Registering it once **discharges both lanes**; D78-ARM COMPLETION must rebase and
   re-declare rather than solve or register a second `pjm-t1h`. Rule 19 `[R-ONE-MECH]` in its
   registration form: one recipe, one row, one bundle.

**This lane touched no `retirement_sector_gate` code, config, test, help string or matrix cell** —
the charter's DO-NOT honoured to the letter. What it could not do is un-arm the field: Q56 is in
`_pjm_config` at HEAD, so it is in the recipe. Carrying an armed field another lane owns is not
touching it.

---

## 4. FC-3 — differenced against the COMMITTED control, reported at full magnitude

Rule 29(b) **form 4**: the control is the committed `pjm-t1h` bundle, differenced, never re-solved.
**Every direction below was declared in ADDENDUM B §4 D-4 before the LP ran**, and every one held.

| row | control (`a9c66d8ea25acb9d`) | **arm (`fb16fda2ddb0a94a`)** | band | declared ex ante |
|---|---:|---:|---|---|
| `retire.total_gw.model` (actual **15.062**) | 18.058 | **15.292** | **FAIL → PASS** | "falls; may cross FAIL→PASS" ✔ |
| `retire.total_gw.err_frac` | 0.199 | **0.015** | — | ✔ |
| `false_retire.false_gw` | 8.065 | **6.825** | FAIL → FAIL | "falls, stays FAIL" ✔ |
| `false_retire.frac_of_model` | 0.447 | 0.446 | FAIL → FAIL | ✔ |
| `unit_recall_gt300.recall` | 0.650 | **0.550** | FAIL → FAIL | "**FALLS**" ✔ |
| `plant_release_precision.window.all` | 0.421 | **0.495** | reported-only | "rises" ✔ |
| additions shares (wind/solar/gas_cc/gas_ct/storage) | — | **byte-identical** | unchanged | ✔ |

**Flip-gate extras** (scorer-side, no re-solve): T-R10a **PASS** / T-R10b **PASS** (first mover
`gas_st`); LOYO **holds 2/3** — `tr10a` and `tr10b` PASS in all three folds, `recall` FAIL in all
three (`-2023` 6/12, `-2024` 11/19, `-2025` 11/19); BLK-10 fired **0.0 GW**.

### 4.1 Two bands stay FAIL and recall FALLS — stated as neither defect nor success

Both were written down before the LP ran, so neither can be reframed afterwards. A supply-side
accreditation repair plus a sector partition **remove FALSE exits without finding missing TRUE
ones**, and a partition that removes matched sector-1 exits **must** cost recall. Nothing was
re-tuned in response (rule 1 `[R-STRUCT]`).

**The named successor is visible in this solve's own screen output**, which is the useful part: the
CT / ST / oil zero-E&AS operand (D57 §4). In the 2022 screen `gas_st` reads **net_rev 0.0 $/kW-yr**
against a **35.0 $/kW-yr** going-forward bar, and the pipeline executes **all 103 `gas_st` exits,
8,693 MW** — after which `gas_st` disappears from the 2023-2025 screen stacks entirely. That is the
mechanism behind the residual `false_retire`, measured rather than inferred, and it is **routed, not
absorbed**.

**Also routed, not closed:** D66 card B's remaining half — the 2024/25 and 2025/26 census below the
published cleared position. Clearing prices on the row: 2022 **90.41**, 2023 **86.52**, 2024
**165.97**, 2025 **213.06** $/MW-day; positions 1.0426 / 1.0445 / 1.0276 / 1.0119, the 2025 leg
clearing all offers (`all_offers_clear_curve_sets_price`).

---

## 5. G-DRIFT and the four control legs

**G-DRIFT** was re-run for this lane's own window — the control bundle's `scored_at_sha`
**`9911ff21f42e` → `f37121bd`**, then extended over the 45 further commits to **`abdd30c9`**
(ADDENDUM B §3 / §7). **The only LIVE drift is the two ruled arms**; every other hunk is classified
INERT with its reason (capx D76's `runner.py` guard inspected line by line, pjm-169 F2's "ARM"
shown to be `backcast_config`-only, the five SPP commits shown to touch PJM in comments alone).
Form 4 is valid and **no control solve was spent**.

**The four D57/D67 control legs move**, pre-declared in the PRECOMMIT §2.1 and again in ADDENDUM B
§1.2 rather than discovered afterwards — the exact miss `FINDING-capx-d67arm` §2.1 recorded against
itself. Cause is structural and unchanged: both armed fields are `_CACHE_KEY_OPTIONAL_FIELDS`
members registered at `False`, dropped from the hash while unarmed and entering it once armed, on
every PJM forecast leg whatever the other flags say. **Not a defect — the arm is fully invertible**,
and the two-flag leg reaches `a9c66d8ea25acb9d` exactly, so every pre-arm recipe stays reachable and
identified.

**One correction carried at full magnitude** (ADDENDUM B §7): ERCOT's bare key moved
`46d013cbf1f35d27` → `f18431f2447bad01` between the two measurements, from ercot-253's own
`09c812aa`. §1.1 had declared all five non-PJM bare keys unmoved; that is true of MISO, NYISO,
NEISO and CAISO and **false of ERCOT**. Another ISO's measured-input act, not this lane's — and the
property actually being asserted (that the Q55 arm moves no non-PJM key) is untouched.

**A probe defect worth recording**, because it produces a plausible wrong answer: setting the
override attributes on an already-built `ScenarioConfig` and applying the ISO defaults afterwards
silently re-arms every field, collapsing all twelve PJM legs onto the bare key — a table that looks
like a finding ("the flags are inert!") and is an artifact. Overrides must go **through
`build_config`**, as explicit CLI-caller arguments. Caught and corrected before any leg was reported.

---

## 6. Environment notes (not findings, but they cost the lane time)

* `data/clean` was empty and was rebuilt: **54/56 datatypes OK**. Two failures, **neither on the PJM
  T1-H solve path**, both belonging to other lanes:
  1. `emissions-unit-annual` — **OOM (exit -9)** after writing 2019 only. Read solely by
     `scripts/loyo_co2_rates.py` and `scripts/data/derive_plant_emissions_v2.py`; **no reader in
     `src/market_sim/`**, so no solve consumes it.
  2. `load-forecast` — **exit 1** on `basis(es) not in vocab: ['coincident']`. **PJM's parquet was
     written successfully first** (1,533 rows, 2026–2046, 2026 LTLF); the failure is on **SPP**, the
     seventh ISO registered days earlier. A real defect in the new SPP intake, reported here for its
     owner.
* The container advances only while the session holds execution, so a multi-hour LP needs a
  persistent monitor rather than polling.

## 7. What this lane does NOT claim

It arms nothing. It moves no `ScenarioConfig` default, no registry value, no marker, no freeze file,
no calibration determination, no other ISO's shard or cell (rule 25 — PJM only). It writes no board
file. It re-opens no adjudicated cell and no A/B. It is **not a keeper and cannot be one**: keepers
are a backcast concept (rule 15) and this is a forecast-family T1-H row.

It does not claim either arm closes what its own finding says it does not: the model's
`false_retire` still FAILs, `unit_recall_gt300` **falls** to 0.550, and D66 card B's remaining half
stands.
