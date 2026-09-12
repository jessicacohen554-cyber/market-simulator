# FINDING — spp-30: SPP out-of-training LMP intake (2019–2022), and a CLAUDE.md-vs-code gate discrepancy that resolves the opposite way from the lane charter

**Lane:** SPP-30 (SPP held-out-year DATA INTAKE). **Date:** 2026-09-12.
**Base:** `9e499b0e8d6f851a4e726bbd42b207ca5368654c` (`origin/main` at session start;
main advanced to `4607258a` during the session — no solve-path file in this lane's
scope changed).
**LP spent: ZERO.** No year was solved, scored or registered. No keeper file, no
`calibration-complete.json`, no `frontend/data/backcast/keepers/*` was written.
**DATA PROFILE:** spp.

---

## 0. Headline

SPP was the only ISO in the program with no out-of-training price actuals
(`actual_lmp_hourly_SPP.parquet` carried 2023–2025 and nothing else). **That gap is
now closed for 2019–2022** from SPP's own portal, validated without a dispatch solve.

**And the charter's central premise is wrong, in the direction that helps.** The lane
prompt states that the `[R-HOLDOUT]` gates are LIVE at HEAD and that SPP therefore
cannot emit 2020–2022 rows without a `complete` marker. **Every one of those gates was
already removed** (commit `b0a807a8`, "Remove [R-HOLDOUT]: the holdout year machinery
and all four spend gates"). CLAUDE.md rule 22's coda is accurate; the lane prompt is
not. The measured consequence is the opposite of the one predicted: the derive scripts
**do** emit the new years, so **C3c becomes scorable on 2019–2022 with no marker and no
authorization**. §4 puts the residue to the owner.

---

## 1. Coverage — BEFORE and AFTER

`BEFORE` is read from the committed tree at `9e499b0e`, not from the working copy.

### 1.1 The load-bearing product — `_validation-source` price actuals

| File | BEFORE | AFTER | Rows before → after |
|---|---|---|---|
| `actual_lmp_hourly_SPP.parquet` | 2023–2025 | **2019–2025** | 26,280 → 61,320 |
| `actual_lmp_hourly_zonal_SPP.parquet` | 2023–2025 | **2019–2025** | 52,560 → 122,640 |
| `actual_lmp_hourly_area_SPP.parquet` | 2023–2025 | 2023–2025 (**deliberately unextended**, §1.4) | 26,280 → 26,280 |

Cross-ISO position after this lane (`year` values present per sidecar):

| ISO | Coverage |
|---|---|
| NEISO / NYISO / ERCOT | 2018–2026 |
| PJM | 2018–2025 |
| **SPP** | **2019–2025** ← was 2023–2025 |
| MISO / CAISO | 2022–2026 |

SPP is no longer the outlier. It remains the only ISO with no 2018 and no 2026.

### 1.2 Supporting products landed

| Product | BEFORE | AFTER | Notes |
|---|---|---|---|
| `spp-genmix/GenMix_<y>.csv` | 2023, 2024, 2025 | **2019–2025** | 4 files, 61.1 MB; byte counts equal the portal's served sizes exactly |
| `spp-hourly-load/hourly-load-<y>.zip` | 2023, 2024 | **2019–2024** | 4 zips, 5.18 MB; **2019 dailies are partial at source** (§1.3) |
| `spp-wind-shape/spp_<y>_wind_zone_shape.parquet` | 2023–2025 | **2019–2025** | rebuilt by the committed builder, NASA POWER + EIA-860 |

### 1.3 Honest gaps in what landed

Measured from the landed payloads, not assumed:

* **`hourly-load-2019.zip` is partial at source.** 117 CSV members against 377 for every
  other year: **all 12 monthly files are present**, but dailies begin only
  **2019-09-18** (105 of 365). SPP's archive does not carry Jan–mid-Sep 2019 dailies.
  The monthly series — the one the load products actually read — is complete.
* **`hourly-load-2020.zip` is missing exactly one day, 2020-01-30** (365 of 366 dailies).
  **Feb 29 2020 is present**; this is an ordinary archive gap, not a leap-year artifact.
* `GenMix_2021.csv` is 12.19 MB against ~16 MB for its neighbours. **Not a truncation**:
  105,122 lines and 22 columns, the same shape as every other year (8,760 × 12 five-minute
  intervals + header; 105,409 for leap-year 2020). The publisher's own file is narrower.

### 1.4 What was deliberately NOT fetched, and why

Two charter items were checked and declined on evidence. Both would have been wasted egress.

* **`actual_lmp_hourly_area_SPP.parquet` — not extended.** The repo's own
  `data/raw/_validation-source/README.md:13` states it is **"NOT a model-zone benchmark
  and NOT read by any scorer"** — it is the third point of the three-point spread lane
  SPP-57 identified the OK↔S link TTC on, kept so that identification is reproducible
  "without the ~900 MB pull". Extending it buys no scorable year at a ~900 MB cost. Its
  builder is `docs/handoffs/spp57/build_area_price.py`, not a `scripts/` instrument.
* **`lmp-data/DAMLZHBSPP_<year>.zip` — NOT AN SPP PRODUCT.** The charter lists it as SPP
  intake. It is **ERCOT** data: `DAMLZHBSPP` = *DAM Load Zone and Hub Settlement Point
  Prices*, where the trailing "SPP" is *Settlement Point Prices*, not Southwest Power
  Pool. Verified two ways — the zip member is
  `rpt.00013060.0000000000000000.DAMLZHBSPP_2023.xlsx` (an ERCOT MIS report id), and
  `scripts/hydrate_data.py:186–191` warns in as many words that a bare `spp` token
  "would also claim ERCOT's settlement-point zips `DAMLZHBSPP_<year>.zip`" and that
  "`DAMLZHBSPP_2023.zip` is not equal to `SPP`". ERCOT already holds 2018–2026.
* **Not re-fetched (already present, per charter):** `zone-specific-demand/SPP`
  (2019–2022 ✓), EIA-930 `SWPP_{region,fueltype}.parquet` (2015-07→2026-05 ✓),
  `campd-unit-level` (2019+ ✓).

---

## 2. The route — already proven, re-verified, not re-swept

Lane SPP-14's row-4 route was used unmodified; its third-party sweep is a DO-NOT-REDO and
was not repeated. The route is `portal.spp.org/file-browser-api`, anonymous plain HTTPS,
no token and no cookie, `Range` honoured.

**Phase 0, zero bulk download.** The committed builder's own
`_remote_size` / `_central_directory` were driven against the archived year zips and all
12 `MONTHLY-SL` members were found in **every** year, for **both** products — i.e.
`scripts/data/build_spp_lmp_reference.py` runs against 2019–2022 with **no code change**:

| Product | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| `DA-LMP` zip bytes | 228,667,478 | 232,711,485 | 261,793,877 | 280,525,231 | 286,071,592 |
| `DA-LMP` MONTHLY-SL months | 1–12 | 1–12 | 1–12 | 1–12 | 1–12 |
| `RTBM-LMP` zip bytes | 4,027,796,207 | 4,167,267,200 | 4,616,074,817 | 5,024,338,629 | 4,986,546,038 |
| `RTBM-LMP` MONTHLY-SL months | 1–12 | 1–12 | 1–12 | 1–12 | 1–12 |

Every probe returned `206` (Range honoured). The RTBM archives are 4–5 GB each; only the
12 monthly members are range-fetched out of them — **578.1 MB compressed for 2019–2022**
(DA 64.6 / 65.5 / 74.3 / 82.5 MB; RTBM 65.1 / 66.2 / 75.8 / 84.1 MB), never the 18 GB of
whole zips. Zenodo record 17676746 was **not** used: the publisher's own series was
reachable throughout, which is the rule 13 `[R-MEASURED]` preference.

---

## 3. The calendar convention — stated, because getting it wrong shifts every number

From `scripts/data/build_spp_lmp_reference.py` (lines 165–166, 172–177, 341–342, 419–448),
and confirmed by measurement against the committed years:

* **Fixed non-leap 8,760-hour local calendar. Feb 29 is DROPPED** in a leap year, so 2020
  and 2024 land on 8,760 rows exactly like every other year (rule 8 `[R-8760]`).
* **Hour-beginning.** SPP's `HE-nn` → model hour `nn-1`.
* **Fixed CST (`Etc/GMT+6`), no DST term**: `model[t] = gmt[t+6]`, every hour of every
  year. This is `derive_actual_lmp._STD_TZ`'s clock, the same fixed offset
  `eia_loader._eia_hourly_frame` produces.
* The **last 6 model hours** of a year fall in the next year's GMT file and are filled
  from that year's head when it is in the same batch — which is why this lane built
  **2019–2025 in ONE invocation**. The DST spring-forward hour is absent at source and
  stays `NaN`; the scorer skips non-finite hours as it always has.

Every ISO sidecar in the repo carries exactly 8,760 rows per year on this same clock
(measured: ERCOT and NEISO 2018–2026 all 8,760, hour 0..8759), so SPP's new years are
schema- and calendar-identical to every other ISO's.

---

## 4. THE DISCREPANCY — and it resolves the OPPOSITE way from the lane charter

The charter instructed me to state a CLAUDE.md-vs-code discrepancy in which **CLAUDE.md
claims the `[R-HOLDOUT]` gates are removed while the code still enforces them**, and not
to resolve it. I did not resolve it. **But the evidence runs the other way: the code has
no such gates. CLAUDE.md is correct and the charter's reading of HEAD is not.**

### 4.1 Every gate the charter names as LIVE does not exist

Measured at `9e499b0e`:

| Charter claim | Measured at HEAD | Evidence |
|---|---|---|
| "`run_calibration_full.enforce_holdout_year_gate` exists and is CALLED at two entry points (lines ~8889 and ~13049)" | **No such function anywhere in the repo.** `grep -rn "def enforce_holdout_year_gate"` → no match. Line 8889 is inside a docstring about `ercot_reserve_supply_cap_from_year`; line 13049 is the `--nyiso-gas-bridge-startup` argparse block. Neither is a gate call. | `scripts/run_calibration_full.py:8885–8893`, `:13045–13053` |
| "`--holdout-authorized` is still a registered CLI flag in BOTH `run_calibration_full.py` and `run_calibration.py`" | **Not a registered flag in either, or anywhere.** The only `add_argument` matching `holdout` in the repo is `--holdout-year` in `stamp_touchpoint_holdout.py:141`, an unrelated stamping tool. | `grep -rn 'add_argument.*holdout'` → 1 hit, not this flag |
| "`dashboard_add_run.py` still reads the marker file" | **`enforce_registration_marker_gate` does not exist.** `dashboard_add_run.py:31` and `:151–155` are stale *prose* naming it; `_load_json_doc` is a generic JSON reader with no holdout caller. | `scripts/dashboard_add_run.py:31,148–160` |
| "`frontend/data/backcast/holdout-freeze.json` is `active: true` scoped `{isos: ALL, tiers: [locked_test]}`" | **The file does not exist.** Deleted in `b0a807a8`. The only match in the tree is an unapplied patch, `docs/handoffs/patches/holdout-freeze-gate.patch`. | `find . -name 'holdout-freeze*'` |
| "`derive_actual_tail.py` + `derive_actual_amplitude.py` still carry a per-tier marker gate that SILENTLY SKIPS an unauthorized ISO-year" | **Both `_year_emittable` seams are `return True`** with the docstring "Always True — every year is emittable." | `scripts/data/derive_actual_tail.py:103–111`, `scripts/data/derive_actual_amplitude.py:74–82` |
| "even with the data landed, SPP holds no `complete` marker, so `derive_actual_tail.py` will emit NO 2020-2022 rows for SPP and C3c would score SKIPPED there" | **False.** Both derives iterate every year present in the parquet with an always-true gate; `TAIL_THRESHOLD["SPP"] = 200.0` is registered. §5 gate 2 shows the new years emitted. | `derive_actual_tail.py:57–65, 118–125` |

`holdout_policy` itself exports neither `authorized` nor `frozen_tiers` (public names are
`CALIBRATION_YEARS`, `HINDCAST_*`, `LOCKED_TEST_YEARS`, `TIER_*`, `VALIDATION_YEARS`,
`hindcast_solve_year_violations`, `tier_for_year`), even though
`dashboard_add_run.py:152–155` still describes both.

**A third, independent corroboration** — the data file itself. `calibration-complete.json`'s
own `note` opens: *"AUTHORIZES NOTHING. [R-HOLDOUT] — the three-tier holdout regime and
every gate that enforced it — was REMOVED 2026-09-09 by owner instruction … Any year may
now be solved, scored and registered freely, with no marker and no one-shot."* And the SPP
keeper's note records *"SPP has NO `complete` entry and this promotion deliberately does
NOT create one"* alongside *"[R-HOLDOUT] was removed 2026-09-09, so no year is protected
from having been iterated against."*

### 4.2 What the residue actually is — stale prose, two dead constants, one vacuous test

The gates are gone; what survives is documentation that still describes them, which is
what a reader (and the charter) can mistake for live enforcement.

1. **Stale docstrings/comments in 8 live modules**: `run_calibration_full.py:8684,8695`,
   `run_calibration.py:15–16,6947`, `dashboard_add_run.py:29–31,151–155`,
   `derive_actual_tail.py:26–28,67–100,154–155`, `derive_actual_amplitude.py:39–41`,
   `knob_jacobian.py:10,230`, `invariant_ledger.py:19–20`,
   `fetch_campd_unit_level.py:71`, `register_forecast_run.py:1218`.
   `derive_actual_tail.py`'s stale text is the most consequential: it is copied into the
   **emitted `actual_tail.json`'s own `note` field** (lines 154–155), so the published
   artifact tells its reader it is marker-gated when it is not.
2. **Two dead constants** — `HOLDOUT_CALIBRATION_YEARS = frozenset({2023,2024,2025})` and
   `HOLDOUT_MARKER_FILE` at `run_calibration_full.py:8690–8691`: **defined, never read**
   (grep finds only the definition lines). Also
   `derive_actual_tail.py:80`'s `ALLOWED_YEARS` — assigned, never used. Under rule 26
   `[R-DELETE]` ("a deprecated parameter that still parses is a re-armable answer key")
   these are exactly the shape the rule forbids.
3. **One vacuous regression test.**
   `tests/regression/test_recipe_replay_gates.py:79` asserts
   `"enforce_holdout_year_gate" in inspect.getsource(kj.solve_year)`. It **passes on
   docstring prose**: `solve_year` spans lines 206–269, its docstring spans 216–250, and
   the token's only occurrence in the function is **line 230 — inside the docstring**.
   Zero occurrences in code. The test therefore asserts a gate exists while the gate does
   not, and it would keep passing if the function were deleted from the repo (it has been).

### 4.3 THE OPEN QUESTION FOR THE OWNER

I did not touch any of it — not CLAUDE.md, not a gate, not a marker, not a test. Which way
this resolves changes what the whole program is permitted to spend, so it is the owner's
call. **Two readings are consistent with the tree, and they differ materially:**

* **(A) The removal is complete and only the documentation lags.** Then the residue is a
  docs-and-cleanup task: strip the stale prose, delete the two dead constants and
  `ALLOWED_YEARS` under rule 26 `[R-DELETE]`, and either delete the vacuous assertion or
  re-point it at a gate that exists. Any year is spendable today, which is what the code
  does.
* **(B) The removal was broader than intended** — in particular, `derive_actual_tail.py`'s
  emitted `note` still promises marker-gating to every consumer of `actual_tail.json`, and
  a `locked_test` classification still exists in `tier_for_year` with nothing enforcing it.
  Then something needs re-arming, and this lane's 2019 intake (tier `locked_test`) is the
  first thing affected.

**Questions I am not answering myself:**

1. Is reading (A) correct — is every year genuinely spendable at HEAD, with the residue
   being documentation only?
2. If yes, should a follow-up lane do the rule-26 cleanup (stale prose, the two dead
   constants, `ALLOWED_YEARS`, the vacuous test)? It is not in this lane's scope.
3. **2019 is landed as pure data and I am NOT presenting it as a ladder rung.**
   `tier_for_year(2019)` = `locked_test`, and `tier_for_year(2026)` = `locked_test` too.
   With no freeze file and no gate, nothing mechanically stops a 2019 solve. Is 2019
   intended to be spendable, or should it stay unspent by convention?

---

## 5. The validation gates — no-LP only, every number re-derived here

Four gates, all run without a dispatch solve. Gate bars were fixed before the build.

### Gate 1 — OVERLAP IDENTITY: **PASS, bit-exact**

*Bar (pre-registered): `corr ≥ 0.999999` and `|Δannual-mean| ≤ 0.01 %` on every overlap year.*

The build span was **2019–2025 in one invocation**, so 2023/2024/2025 were re-fetched by
the new code path and differenced against the committed sidecars. Result is stronger than
the bar and stronger than SPP-14's 0.0000 % gate — it is **exact equality at float32
storage precision on every mutually-finite hour**:

| File | Years | Series | `corr` | `Δmean` | `Δmean %` | `max|Δ|` | exact-equal hours |
|---|---|---|---|---|---|---|---|
| `actual_lmp_hourly_SPP` | 2023/24/25 | rt, da | **1.000000** | 0.000000 | 0.0000 | 0.00000 | 8,754/8,754 (2024 rt 8,748/8,748) |
| `actual_lmp_hourly_zonal_SPP` | 2023/24/25 × 2 hubs | rt, da | **1.000000** | 0.000000 | 0.0000 | 0.00000 | same |

18 series in total (year × hub × {rt,da}). Annual means reproduced to the cent:
2023 rt 23.4732 / da 25.6029, 2024 rt 23.3135 / da 25.9239, 2025 rt 27.1112 / da 28.7151.

**The merge was nonetheless conservative.** Even with bit-exact reproduction in hand, the
committed 2023–2025 rows were **preserved byte-for-byte** and only 2019–2022 added — the
keeper's scored inputs are not this lane's to rewrite. Machine-checked before writing
(`committed rows preserved EXACTLY in result: True`), with dtypes and column order
asserted identical.

### Gate 2 — LOADER RESOLVABILITY: **PASS, functionally**

Proven by *running* the production chain rather than by inspection. Each step resolves
through `config/paths.py` (`CALIBRATION_DIR`); **no `Path(__file__).parents[...]`, no new
`if iso ==` ladder, no new code**:

| Step | Command | Result |
|---|---|---|
| C3a/C3b bands | `derive_actual_lmp.py --isos SPP --years 2019..2022` | `actual_lmp.json` 48 → **52 iso-years**; SPP 3 → 7 |
| C3c tail | `derive_actual_tail.py` | SPP `2019: RT 47h, 2020: 23h, 2021: 140h, 2022: 99h` |
| D-A amplitude | `derive_actual_amplitude.py` | SPP `2019: $19.03, 2020: $18.43, 2021: $51.35, 2022: $57.65` |

Verified per-ISO against `HEAD`: in `actual_lmp.json` **only SPP moved** (3→7 years) and
**no existing year's record changed** in any ISO, SPP's own 2023–2025 included.

### Gate 3 — CROSS-SOURCE COHERENCE / CLOCK ALIGNMENT: **PASS, with 2021 resolved by measurement**

Alignment was **measured per year**, not inherited from another lane's constant. It is
reported as a **relative** gate against controls, and here is why that matters:

> **The instrument the charter specified is weak, and the controls prove it.** A
> level-on-level correlation of *price* against load is dominated by fuel cost, scarcity
> spikes and negative-price wind hours. Running the sweep on the three
> **already-committed, keeper-scored** years yields `best_shift = −2` for demand in **all
> three** (r 0.047 / 0.377 / 0.225). The −2 is a property of the instrument, not of any
> year's data — so a new year is judged against how the known-good years behave, never
> against an absolute 0.

**Instrument A — diurnal price profile (decisive).** `best_shift` vs the committed-year
reference shape is the binding test; a clock error shifts it, and it is robust to level
drift. Controls: peak hour 16–17, `best_shift = 0`.

| Year | peak h | `r` vs ref | `best_shift` | mean $ | verdict |
|---|---|---|---|---|---|
| 2019 | 14 | 0.944 | **0** | 20.846 | PASS (see below) |
| 2020 | 17 | 0.968 | **0** | 16.515 | PASS |
| 2021 | 18 | 0.776 | +1 | 37.362 | flagged → resolved |
| 2022 | 17 | 0.989 | **0** | 44.092 | PASS |
| *2023/24/25 (control)* | 17/16/17 | 0.987/0.984/0.976 | 0/0/0 | 23.47/23.31/27.11 | — |

**2021 is Winter Storm Uri, and that is measured, not asserted.** A clock error is present
in all 8,760 hours and cannot be removed by deleting 288 of them; a February storm can.
Excising **2021-02-09 … 02-20** (288 h, 3.29 % of the year) and applying the *identical*
excision to every year:

| Year | peak h full → −Uri | `r` full → −Uri | shift full → −Uri | mean $ | max $ | h > $200 |
|---|---|---|---|---|---|---|
| **2021** | 18 → **17** | 0.776 → **0.964** | +1 → **0** | 37.36 → 24.65 | **4,028.99** | 140 → 49 |
| 2019 | 14 → 14 | 0.944 → 0.945 | 0 → 0 | 20.85 | 1,170.65 | 47 |
| 2020 | 17 → 17 | 0.968 → 0.969 | 0 → 0 | 16.52 | 525.25 | 23 |
| 2022 | 17 → 17 | 0.989 → 0.988 | 0 → 0 | 44.09 | 1,259.25 | 99 |
| 2023/24/25 | unchanged | Δ ≤ 0.004 | 0 → 0 | — | 856–1,093 | 42–68 |

2021 snaps onto the controls' own peak hour and shift; **every other year moves by
≤ 0.004**. Two independent corroborations: 2021's max is **$4,028.99** against $525–1,421
elsewhere, and `derive_actual_tail.py` independently counts **140 RT hours > $200** in
2021 — the exact figure this diagnostic measured.

**2019's h14 argmax is a flat-profile artifact, not phase error.** Its profile is the
**flattest of the seven years** (peak-to-mean **1.379** against 1.490–2.132), the
afternoon is a plateau (h12–h19 all $26.4–28.7), and h14 beats h17 by **$0.875 = 3.04 %
of peak**. The keeper-scored control **2024 shows the same ±1 wander** (peak h16, $0.888
above h17). The binding test — `best_shift = 0` — passes.

**Instrument B — price vs EIA-930 SWPP, reported with its controls.** Demand
`best_shift = −2` in **all seven** years, new and committed alike — perfect consistency
with the controls. Wind wanders: −1 or 0 in the controls, −2 in 2019 and 2021, −1 in 2020
and 2022. That ±1 wander on the weak instrument is **reported, not explained away**, and
it is not evidence of a clock error given that instrument A is unambiguous and demand is
consistent across all seven years. (The EIA-930 side is complete for every target year:
8,760 rows — 8,784 in leap 2020 — zero nulls, for both demand and wind.)

### Gate 4 — DST AND LEAP-YEAR ACCOUNTING: **PASS**

| Year | leap | rows | hour range | rt NaN | da NaN | rt coverage | non-tail NaN hours |
|---|---|---|---|---|---|---|---|
| 2019 | | 8,760 | 0–8759 | 6 | 6 | 0.9993 | — |
| **2020** | **yes** | **8,760** | 0–8759 | 6 | 6 | 0.9993 | — |
| 2021 | | 8,760 | 0–8759 | 6 | 6 | 0.9993 | — |
| 2022 | | 8,760 | 0–8759 | 6 | 6 | 0.9993 | — |
| 2023 | | 8,760 | 0–8759 | 6 | 6 | 0.9993 | — |
| **2024** | **yes** | **8,760** | 0–8759 | 12 | 6 | 0.9986 | 738–743 |
| 2025 | | 8,760 | 0–8759 | 6 | 6 | 0.9993 | — |

Identical for the zonal file, per hub. **How 8,760 is produced in a leap year: Feb 29 is
dropped.** 2020 and 2024 therefore land on 8,760 exactly like every other year — the
model's fixed non-leap clock, rule 8 `[R-8760]`.

The **6-hour NaN tail is in every year, including the committed ones**, and is not a
batching artifact: its filler is the next year's first 6 GMT hours, and those hours belong
to the previous *local* December 31, which SPP's monthly files do not carry — exactly as
`build_spp_lmp_reference`'s docstring states. Coverage is therefore **0.9993 in every new
year, identical to the committed years** — no regression. 2024's extra 6 (hours 738–743,
Jan 31 18:00–23:00) is a real RTBM source gap, present in the committed file too.

### Gate 5 — REGRESSION: **PASS, zero failures introduced**

`1,511 passed, 12 skipped, 146 subtests passed`. **16 failures are PRE-EXISTING at HEAD**
and none is mine — established by reverting the five artifacts to `HEAD`, re-running the
same selection, and diffing the failure sets: **identical before and after** (zero
introduced, zero fixed). They sit in `test_ff_readiness_battery`,
`test_golden_manifest_provenance`, `test_gate_a_provenance`, `test_replay_keeper_strict`,
`test_audit_keepers_lineage`, `test_backcast_artifacts` — forecast-marker, golden-manifest
and keeper-replay concerns untouched by a price-actual intake.

**Pushed-blob verification (rule 27 `[R-PUSH]`).** No existing ≥300-line source file was
rewritten, and every pushed artifact was fetched back and compared: all nine checked
blobs match local on both sha256 and line count, the two parquets included.

### Scope note — one unavoidable cross-ISO side-effect, flagged not buried

`derive_actual_amplitude.py` has **no `--isos` or `--years` flag**, so re-running it also
refreshed **six other ISOs** (ERCOT/NEISO/NYISO **+2018/2019/2026**, PJM **+2018/2019**,
MISO **+2022/2026**, CAISO **+2026**). **This is not caused by this lane's data.** The
committed file was **stale against HEAD**: it was generated while the now-removed
`[R-HOLDOUT]` marker gate still suppressed out-of-training years, and the always-true
seam (§4.1) now emits them. Blast radius is display-only — `diurnal_amplitude` is in
`REPORTED_ONLY`, absent from `CRITERIA`, and `calibration_verdict.py:486` says it "never
gates and never budgets a caveat". Committed as the unmodified script's output and flagged
here, because hand-editing a generated artifact is worse than refreshing it. **It is a
second, independent symptom of the §4 discrepancy** and belongs with that question.

---

## 6. What is now scorable — and what still is not

### 6.1 Scorable

The price-actual chain has four artifacts, and all four are reachable for the new years
through existing instruments with **no new code and no `if iso ==` ladder**:

| Artifact | Consumer | Reached by |
|---|---|---|
| `actual_lmp_hourly_{,zonal_}SPP.parquet` | everything below | `build_spp_lmp_reference.py --years …` (this lane) |
| `actual_lmp.json` SPP block | **C3a, C3b** price bands | `derive_actual_lmp.py --isos SPP --years …` |
| `tail/actual_tail.json` | **C3c** price tail / scarcity | `derive_actual_tail.py` |
| `amplitude/actual_amplitude.json` | D-A diurnal amplitude (reported-only) | `derive_actual_amplitude.py` |

`derive_actual_lmp.py`'s SPP branch (`_spp`, line 1163) **reads** the committed hourly
parquets and returns `None` for the hourly frame, so running it refreshes the JSON and
**cannot rewrite the parquet**; the JSON write is an explicit merge ("Merge into the
committed reference rather than overwriting", line 1484). Other ISOs' entries are
untouched by `--isos SPP`.

**C3a, C3b, C3c and D-A can now be scored for SPP 2019–2022** where before they had no
actuals to score against. That is the whole deliverable, and it is what makes the
validation ladder 2020/2021/2022 reachable for SPP at all.

### 6.2 NOT scorable / NOT delivered — stated plainly

* **No year was solved.** This lane spent zero LP and produced no run, so there is
  **nothing to register** on the dashboard (rule 15 `[R-DASHBOARD]` is satisfied by there
  being no run, not by an omission) and **no mechanism-matrix cell to update** (rule 31
  `[R-MECH-MATRIX]` — no mechanism was tested). A model score for 2019–2022 requires a
  separate solve lane.
* **2018 and 2026 are absent and were not attempted.** SPP's portal serves 2013→current,
  so 2018 is *reachable*; it was left alone because the program's working span is
  2019–2025 (`holdout_policy` comments: 2018 was dropped 2026-08-06 by owner decision) and
  landing it would invite a rung nobody asked for.
* **2019 is landed as data, NOT offered as a ladder rung.** `tier_for_year(2019)` =
  `locked_test`. See §4.3 question 3.
* **`actual_lmp_hourly_area_SPP.parquet` stays 2023–2025** (§1.4) — not read by any scorer.
* **`hourly-load-2019` dailies and `2020-01-30` are missing at source** (§1.3). Not
  recoverable from this route; not interpolated, not filled.
* **No `intake_log` entry was written.** The charter permits one only on explicit in-session
  owner authorization, which was not given. **It is owed.**

### 6.3 A caveat that outranks all of the above

`[R-HOLDOUT]` was removed on 2026-09-09, so **no year in this program is protected from
being iterated against** — 2019–2022 included, from the moment this data lands. A score on
any of these years is model-**selection** evidence, not a certified out-of-sample skill
number, and should never be quoted as one. CLAUDE.md rule 22's coda says this in as many
words, and the SPP keeper's own note repeats it. Landing the data does not create
out-of-sample evidence; it creates *more years to be careful about*.

---

## 7. Rules discharged

* **Zero LP** — no `run_calibration_full.py` / `run_calibration.py` / `replay_keeper.py`
  invocation, no `--holdout-authorized` (which does not exist), nothing solved or scored.
  Rule 32 `[R-SHARD]`(a) is satisfied trivially and no shard was needed: intake and its
  no-LP validation are parent work by that rule's own carve-out.
* **Rule 31 `[R-RETAIN]`** — nothing deleted. The scratch build outputs live under the
  session scratchpad, outside the repo.
* **Keeper untouched** — `frontend/data/backcast/keepers/SPP.json`,
  `calibration-complete.json` and `results/calibration/spp27_span` were read and **not
  written**. SPP's determination (`2026-09-10-spp-27-commitment-grain`, CALIBRATED, 7/8,
  0 fails, 1 ledgered C3c) is unmoved, and no intake could move it.
* **No new GitHub Actions workflow** — every fetch ran in-session.
* **Rule 26 `[R-DELETE]`** — I found three violations of it (§4.2 item 2) and **left them
  in place**, because removing them is resolving the discrepancy, which is the owner's call.
* **No `if iso ==` ladder, no `Path(__file__).parents[...]`** added anywhere; every path
  resolves through `config/paths.py` (`CALIBRATION_DIR`).
* **Rule 27 `[R-PUSH]`** — no existing source file was rewritten from regenerated content;
  doc edits were made locally with targeted edits and the pushed blobs verified (§5 gate 5).
