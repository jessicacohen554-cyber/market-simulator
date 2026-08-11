# CAISO-VINTAGE-INTAKE — the as-of-2021 CAISO demand-growth cell

**Session:** CAISO-VINTAGE-INTAKE, 2026-08-11. Branch
`claude/caiso-vintage-2021-intake-hdbyvi`, cut from `origin/main` @ `e346cfb`.
**Scope:** DATA + CITATION + TEST ONLY. **No LP solved, no default changed, no run
registered, no keeper touched, no mechanism added.** The holdout freeze is untouched.

**Headline:** `DEMAND_GROWTH_RATES_VINTAGES[2021]["CAISO"]` is landed from the **CEC
"California Energy Demand Forecast Update, 2020–2030" (CEDU 2020)** — the last CEC demand
forecast adopted at or before the 2021 base year. The table is now **12/12** (ISO, vintage)
cells: both vintages cover all six registered ISOs. FH-5's CAISO Arm K is unblocked on this
axis; **it is not run here** — that is FH-5's arm.

```python
"CAISO": {
    "low":  {"near": 0.0009, "long": 0.0009},
    "mid":  {"near": 0.0091, "long": 0.0091},
    "high": {"near": 0.0158, "long": 0.0158},
},
```

---

## 1. The source document

| | |
|---|---|
| Edition | **California Energy Demand Forecast Update, 2020–2030, Baseline Forecast** ("CEDU 2020" / "Demand Forecast 2020") |
| Proceeding | 2020 IEPR Update, CEC docket **20-IEPR-03** |
| Adopted | **2021-01-26**, CEC **Resolution No. 21-0125-2** (TN 236455); Notice of Availability TN 236333 (2021-01-14) |
| Forms used | **STATE Planning Area**, **Form 1.2 — Total Energy to Serve Load (GWh)**, column `Total_Energy_For_Load` |
| Filings | Low **TN 236984** · Mid **TN 236983** · High **TN 236985**, all the "Corrected – February 2021" workbooks (docketed 2021-03-04) |
| Retrieval | `https://efiling.energy.ca.gov/GetDocument.aspx?tn=236983` (swap the `tn`); docket index `https://efiling.energy.ca.gov/Lists/DocketLog.aspx?docketnumber=20-IEPR-03` |

Per-case arithmetic, straight off Form 1.2:

| case | 2021 GWh | 2030 GWh | CAGR | stored (4 dp) |
|---|---:|---:|---:|---:|
| low | 256,568.979 | 258,557.502 | +0.0858 %/yr | 0.0009 |
| **mid** | **262,562.244** | **284,825.953** | **+0.9084 %/yr** | **0.0091** |
| high | 268,824.268 | 309,599.149 | +1.5815 %/yr | 0.0158 |

The edition's horizon **ends at 2030** — zero post-2030 forecast years — so `long` is
**edge-held** to `near`, the same treatment ERCOT and NEISO carry in this vintage. Phase B
solves 2021–2025, so `long` never binds there anyway.

### 1.1 Why THIS edition, and not the two obvious neighbours

* **CED 2021** ("Demand Forecast Update, 2021–2035", Resolution 22-0126-02, TN 241296) was
  **adopted 2022-01-26** — after the base year. Using it would be the post-base-year leak
  FH-3 refused when it declined to seed this cell from CEDU 2022.
* **CEDU 2022** is the 2023 cell's source and is three vintages forward of 2021.

CEDU 2020 is therefore the *latest* edition an analyst standing in 2021 actually had. Its
January adoption makes it **earlier in the base year** than MISO's November-2021 edition,
which FH-3 §3.4 already flags as the table's latest-published driver — so this cell tightens
rather than loosens the as-of discipline.

### 1.2 The corrected-vs-original filing

The March-2021 correction is documented as fixing "peak and sector energy totals". Diffed
against the original STATE Mid filing (TN 236317), Form 1.2 moves by **< 0.1 GWh** on
~262,562 (2021: 262,562.207 → 262,562.244; 2030: 284,825.878 → 284,825.953) and the CAGR is
**identical to 6 dp**. The cell does not depend on the choice; the corrected form is cited per
rule 14 `[R-ACCURATE]`.

### 1.3 Why all three cases, when the 2023 CAISO cell carries `mid` alone

The construction rule is per-edition: *"CASES = only what the edition PUBLISHES as a full
low/base/high series."*

* **CEDU 2020 publishes three separate STATE workbooks** (Low / Mid / High Demand Case).
* **CEDU 2022 publishes one** — docket 22-IEPR-03 carries exactly one STATE filing, TN 248375
  "CEDU 2022 Baseline Forecast - STATE", titled *"California Energy Demand Forecast, 2022 -
  2035 Baseline Forecast"* with no case suffix.

So the asymmetry between the two CAISO cells is an **edition difference, not a construction
difference** — and it already has precedent in the table: MISO is `mid`-only at 2021 and a
full band at 2023, for exactly the same reason (its 2021 SUFG edition published High/Low
CAGRs but no series).

The CEC band is admissible as a band: **Form 2.2 varies personal income, commercial
employment, commercial floorspace and households** across the three cases — an
economic/demographic band, the same kind of object as NYISO's Gold Book Low/Baseline/High,
and **not** the 90/10 *weather* spread FH-3 §4 M3 ruled inadmissible for ERCOT and PJM.

---

## 2. Construction match against the other five 2021 rows

The five landed 2021 rows agree with each other; there is **no disagreement to report**. Every
one reproduces from its own cited source values under one rule — CAGR from the base year to
2030, and 2031 → last forecast year for `long`, edge-held when fewer than 3 post-2030 years
exist — and all round to 4 dp:

| ISO | source span | recomputed near | stored | ✓ |
|---|---|---:|---:|:-:|
| ERCOT | 405,842 → 485,143 (2021→2030) | 2.0027 % | 0.0200 | ✓ |
| PJM | 780,068 → 804,517 | 0.3435 % | 0.0034 | ✓ |
| NYISO (mid) | 150,980 → 145,960 | −0.3750 % | −0.0038 | ✓ |
| NEISO | 121,692 → 133,960 | 1.0729 % | 0.0107 | ✓ |
| MISO | 643,003 → 714,142 | 1.1727 % | 0.0117 | ✓ |
| **CAISO (new)** | **262,562.244 → 284,825.953** | **0.9084 %** | **0.0091** | ✓ |

**One documented-rule imprecision found and corrected in the header comment** (docs-follow-code,
not a value change). The rule as written said *near = CAGR from **the edition's first forecast
year*** to 2030. In 11 of 12 cells the base year and the edition's first forecast year are the
same, so nothing distinguished the two readings. CEDU 2020 opens at **2020** while its vintage
key is **2021**, which forces the question — and the table's own CAISO 2023 cell already
answers it: that cell anchors at **2023** inside a **2022**–2035 edition. Recomputing it from
the source workbook confirms the base-year reading is what is stored:

```
CEDU 2022 STATE Form 1.2 (TN 248375):
  269,058.088 (2023) -> 294,481.804 (2030)  => 0.012982  -> stored 0.0130  ✓
  298,860.411 (2031) -> 314,981.502 (2035)  => 0.013221  -> stored 0.0132  ✓
```

The base-year anchor is also the only one consistent with the consumer: `runner._scale_demand`
starts compounding at the base year. The header comment now says base year, and names the one
cell where the two readings differ.

---

## 3. The purely-additive proof (brief step 3)

**Nothing that solves today reads this key**, and nothing moved.

Cache keys, measured before and after the edit on the same head:

| config | pre-edit | post-edit |
|---|---|---|
| `ScenarioConfig()` (pinned default) | `603c2498bf71d21d` | **`603c2498bf71d21d`** |
| `ScenarioConfig(mode="backcast")` | `35b6dc12f97968f1` | **`35b6dc12f97968f1`** |
| ERCOT backcast 2023 | `df386bca96a1d288` | **unchanged** |
| CAISO backcast 2023 | `a9afddae291525c1` | **unchanged** |
| PJM / MISO / NYISO / NEISO backcast 2023 | `9834b2018b598423` / `2a1252c3acae89e9` / `fd15030b3ee60f11` / `5b1633171fead559` | **unchanged** |

Both pins are the literals `tests/regression/test_persisted_identity.py` asserts, and that
suite passes. Three independent reasons the key cannot move:

1. `DEMAND_GROWTH_RATES_VINTAGES` is a module constant; it is not in `cache_key`'s payload at
   any value. Only `ScenarioConfig.demand_growth_vintage` is hashed, and it is registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` (dropped at its `None` default).
2. Adding a key to a dict cannot change an existing lookup. Every FH-3 cell resolves to its own
   value, pinned by a new test.
3. **No run on disk addresses (2021, CAISO)** — that is precisely the refusal FH-5 hit.
   The vintaged bundles under `results/hindcast/` are `*-t1ff-armk-fh5` at 2021 for ERCOT /
   MISO / NYISO / PJM / NEISO, and `*-t1ff-armk-fh4` at 2023 for all six. CAISO 2021 is the one
   combination absent — so there is no cached run whose key this could orphan.

`scripts/check_cache_key_registration.py` → ok (718 fields, 165 registered, all resolve).

---

## 4. Tests (brief step 4)

`tests/unit/config/test_fh2_as_of_channels.py`, four added to
`TestDemandGrowthVintageMechanism` (32 → 36 in the file; whole file passes):

| test | asserts |
|---|---|
| `test_every_landed_vintage_covers_every_registered_iso` | both vintages resolve for **every** ISO in `MARKET_DESIGN` — the six-ISO completeness gate, and it fails if a seventh ISO is registered without its vintage rows |
| `test_caiso_2021_is_the_cedu_2020_edition` | the three values pinned; `long == near` (edge-held); `low < mid < high`; and the whole band sits under the live 2.8 %/yr CAISO rate, i.e. it is genuinely as-of |
| `test_fh3_cells_are_undisturbed_by_the_caiso_intake` | each of the five FH-3 2021 cells still resolves to its own edition's rate (neighbouring-row slip guard) |
| `test_a_vintage_with_no_row_still_fails_closed_for_every_iso` | 2020 and 2022 — genuinely unregistered vintages — still raise at config build **for every ISO including CAISO**, naming the registry |

**The fail-closed behaviour is not weakened anywhere.** The vintage-level, ISO-level and
case-level refusals are untouched; the existing tests covering all three still pass unchanged,
including `test_vintage_missing_the_iso_raises`, which exercises the missing-ISO refusal
against an injected synthetic table and so is unaffected by the real CAISO row landing.

Gates run inline: `pytest tests/unit/config/ tests/regression/test_persisted_identity.py`
(511 passed — the 3 initial `test_reserve_config.py` failures were a missing `tzdata` package in
this container, green once installed, unrelated to this change) · `ruff check` + `ruff format
--check` clean · `scripts/check_cache_key_registration.py` ok ·
`scripts/check_mechanism_matrix.py` integrity OK · `scripts/audit_keepers.py --check` PASS
(0 failures) · `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` D-6 quarantine
PASS.

---

## 5. Remaining gaps (brief step 5)

**At cell level: none. The table is complete.**

| vintage | CAISO | ERCOT | MISO | NEISO | NYISO | PJM |
|---|---|---|---|---|---|---|
| 2021 | low, mid, high | mid | mid | mid | low, mid, high | mid |
| 2023 | mid | mid | low, mid, high | mid | low, mid, high | mid |

12/12 cells present, and {2021, 2023} is the complete set of vintages the program needs —
hindcast-forward plan §3.1 defines exactly two T1-FF bases (Phase A 2023, Phase B 2021), and
`run_capacity_hindcast.py` sets `demand_growth_vintage = start_year` for `--arm asknown`. A new
base year would need a new vintage; none is planned.

**What is still open is at CASE level, and each is a settled negative rather than a to-do:**

| cells | `mid`-only because | status |
|---|---|---|
| CAISO 2023 | CEDU 2022 publishes a single Baseline STATE workbook (verified in docket 22-IEPR-03) | **CLOSED** — nothing to fetch |
| ERCOT 2021/2023, PJM 2021/2023, NEISO 2021/2023 | their published spreads are **weather** 90/10, not an economic band (FH-3 §4 M3) | open-but-judged; a genuine economic band would have to come from supplementary materials |
| MISO 2021 | the Nov-2021 SUFG edition publishes High/Low **CAGRs** but no High/Low **series** | edition limitation |

A `low`/`high` request on any of those raises rather than inventing a band — unchanged, and
correct. FH-3 §4 M1 (this cell) is now closed; **M2 remains open and untouched**: pulling the
Nov-2020 / Nov-2022 SUFG editions would remove MISO's inside-the-base-year publication date.
It is an optional tightening, not a blocker.

---

## 6. Governance

* **Rule 13 `[R-MEASURED]`** — a published *forward-looking* forecast as of a vintage date, the
  admissible kind. Nothing is back-solved from any outcome, no residual was consulted, and no
  measured actual enters. The number would regenerate for a forward base year from the CEC
  edition current at that date.
* **Rule 5 `[R-NO-MAGIC]`** — every value carries document, form, column, TN and arithmetic.
* **Rule 22 `[R-HOLDOUT]`** — no year solved, scored or registered. Data prep is unrestricted by
  the 2026-08-06 clarification; the freeze and both markers are untouched.
* **Rule 27 `[R-PUSH]`** — `constants.py` (4,172 → 4,218 lines) edited on disk with `Edit`, never
  regenerated; blob-verified after push.
* **Rule 28 `[R-MECH-MATRIX]`** — no mechanism added or tested; the `demand_growth_vintage` row
  already exists. No matrix edit due. `check_mechanism_matrix.py` clean.
* **Rules 12 / 15 / 16** — n/a, no solve and no dashboard-eligible run.
* **Out of scope, deliberately untouched:** FH-5's CAISO Arm K solve, `holdout_policy.py`, every
  keeper, every other ISO's rows, and the resolver's refusal behaviour.

## 7. For the next lane

CAISO Arm K at base 2021 now **builds** — verified by constructing the config
`run_capacity_hindcast.py --arm asknown` would build for CAISO Phase B and resolving the rate
for 2021–2025 (0.91 %/yr each year, +3.69 % compounded 2021→2025). The fuel axis was already
landed by FH-3 (`hindcast_asknown_aeo2021`). Nothing further is prepared here; the arm should
be run by a Phase-B continuation against the pinned `src/` (`3ae7465`) its sibling arms used,
per the FH-5 findings doc §3.
