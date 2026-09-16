# RESULT — miso-259: the coal fuel-inventory screen CLEARED every stop gate

```
SESSION : miso-259        ISO: MISO        KEEPER: 2026-09-12-miso-255-sil-measured
MECHANISM: coal_fuel_inventory — NEW ScenarioConfig field, default OFF, MISO-gated,
           backcast-only. The missing CEILING on coal.
SCREEN  : 2022, ARM vs same-HEAD CONTROL, single delta. Both solved by shards;
          the parent ran ZERO LP (rule 32 [R-SHARD] (a)).
VERDICT : ALL FIVE pre-registered STOP GATES PASS. A screen may KILL an arm and
          never promote one — the promotion decision is the OWNER'S (rule 31).
```

This document carries **every number this session cites** from either screen
bundle, so the record is the doc and not the parquet (rule 29 `[R-SCREEN]` (c)).

---

## 1. RESULT

> The armed 2022 solve cuts MISO coal from **265.72 to 231.04 TWh** against an
> actual of **223.05** — closing **81.3 %** of the control's error without
> overshooting below it — and the released 34.68 TWh lands on gas and imports
> with **slack and dump both exactly 0.0000 TWh**. The sum of absolute class
> energy error **halves, 102.47 → 50.04 TWh**, and all three classes that were
> failing C1's 8 TWh band in 2022 come inside it.

| | control | **ARM** | actual | control err | **arm err** |
|---|---:|---:|---:|---:|---:|
| coal (all classes) | 265.72 | **231.04** | 223.05 | +42.67 | **+7.98** |
| COAL_PRB | 181.76 | **157.58** | 149.69 | +32.08 | **+7.90** |
| COAL_BIT | 77.33 | **67.46** | 66.91 | +10.42 | **+0.55** |
| COAL_LIGNITE | 6.27 | 5.69 | 6.46 | −0.19 | −0.76 |
| CC_REGULAR | 99.07 | **118.15** | 125.57 | −26.50 | **−7.41** |
| CC_CHP | 13.73 | 15.95 | 18.95 | −5.22 | −3.00 |
| CT_PEAKER | 12.88 | 17.03 | 14.12 | −1.24 | +2.91 |
| ST_GAS | 14.05 | 15.44 | 12.11 | +1.94 | +3.33 |
| ST_CHP | 2.55 | 2.97 | 4.99 | −2.44 | −2.02 |
| CT_CHP | 5.27 | 5.55 | 7.51 | −2.25 | −1.96 |
| import | 13.92 | 20.84 | — | — | — |
| **Σ \|class error\|** | **102.47** | **50.04** | | | **−52.43** |

Unmoved by construction (the mechanism touches only coal): nuclear −4.75, wind
+5.14, solar, hydro, biomass, OTHER all identical to the control.
`OTHER_FOSSIL` stays at −8.98 — a **pre-existing, separate** miss the arm
neither helps nor harms.

Load-weighted LMP **52.73 → 57.47 $/MWh** against an actual RT of 69.87.
**REPORTED ONLY.** C3a is not a screen gate and was never scored as one; a
screen gated on the target residual is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, done one year at a time.

## 2. THE FIVE PRE-REGISTERED STOP GATES, AS SCORED

| gate | verdict | measured |
|---|---|---|
| **G-FOOTPRINT** binds 2022, inert 2023/24/25 | **PASS** | On the LP's own 85-plant coal footprint: 2022 **−4.7 TWh BINDS**; 2020 +142.7, 2021 +65.6, 2023 +91.2, 2024 +115.7, 2025 +50.6 — all inert |
| **G-DIRECTION** falls toward actual, no overshoot | **PASS** | 265.72 → 231.04 against 223.05; lands **+7.98 TWh ABOVE** actual, so it does not overshoot |
| **G-DISPLACE** released MWh land on gas/imports, not slack/dump | **PASS** | +34.04 of 34.68 TWh absorbed by CC_REGULAR / import / CT_PEAKER / CC_CHP / ST_GAS / ST_CHP / CT_CHP. slack 0.0000 → **0.0000**; dump 0.0000 → **0.0000** |
| **G-NOFLIP** no non-target load-bearing criterion PASS → FAIL | **PASS** | No class crosses the 8 TWh C1 band in either direction. The three regressions are small and stay well inside it: CT_PEAKER −1.24 → +2.91, ST_GAS +1.94 → +3.33, COAL_LIGNITE −0.19 → −0.76. C1 2023–25 cannot move — this is a 2022-only screen |
| **G-PIN** budget reconstructible from (opening stock, delivery rate) alone | **PASS** | Enforced in code and covered by a unit test (`test_solved_year_stock_and_receipts_are_never_read`). The builder reads December of *Y−1* and receipts over *Y−2*, *Y−1*; the reader module exposes **no** function returning the target year's own receipts |

Single-delta confirmed from the committed bundles: `coal_fuel_inventory` **True**
vs **False**, both `mode: backcast`, both on solve-surface fingerprint
**`9f0845000dc8af6e`** — the same surface the keeper records.

## 3. TWO THINGS THIS SESSION GOT WRONG — stated, not buried

### 3.1 The PRECOMMIT's footprint was a PROXY, and the shard caught it

The arm shard stopped on HARD STOP 2 and reported an **86-vs-67 plant
divergence**. It was right. The PRECOMMIT's phase-0 table was built from the
committed **bench part's** coal plant set, and the bench part is a **SCORING
artifact, not a fleet census**: 256 thermal plant-keys for MISO 2022, with no
hydro, nuclear or VRE rows at all. The LP's own 2022 coal fleet is **85 plants**
(measured from `dispatch/2022_P1.parquet`; the shard's 86 counted one key twice).

Re-scored on the LP's own footprint — which is the set the LP row actually
constrains, and therefore the only correct one — **the gate verdict is
unchanged**:

| yr | open Mt | rate Mt | avail TWh | MODEL | slack | verdict |
|---|---:|---:|---:|---:|---:|---|
| 2020 | 35.71 | 165.69 | 342.0 | 199.3 | +142.7 | inert |
| 2021 | 41.94 | 141.02 | 311.4 | 245.8 | +65.6 | inert |
| **2022** | **25.05** | **128.42** | **261.0** | **265.7** | **−4.7** | **BINDS** |
| 2023 | 26.76 | 132.61 | 271.8 | 180.6 | +91.2 | inert |
| 2024 | 37.13 | 128.76 | 283.1 | 167.5 | +115.7 | inert |
| 2025 | 34.73 | 114.08 | 252.4 | 201.8 | +50.6 | inert |

`scripts/probes/_miso259_coal_budget_phase0.py --plant-ids-json` now takes the
LP's own codes, and its shared-storage fold applies the **same membership test**
as `coal_fuel_inventory.coal_footprint_plant_ids` against the **same committed
crosswalk** — so the probe and the LP can no longer disagree about what the
footprint is.

### 3.2 The pre-solve yardstick was the wrong one — the ANNUAL form, for a MONTHLY mechanism

The PRECOMMIT predicted the arm would remove ~5 TWh (LP footprint, annual form).
The solve removed **34.68**. That is **not** the mechanism misbehaving, and the
decomposition is exact rather than hand-waved:

| prediction basis | predicted cut |
|---|---:|
| annual budget, HR 10.661 | 4.72 TWh |
| **monthly** budget (the mechanism's actual grain), HR 10.661 | 26.74 TWh |
| monthly budget at the fleet's **true dispatch-weighted HR** | **≈34.7 TWh** |
| **OBSERVED** | **34.68 TWh** |

Two structural corrections, neither a fit:

* **The grain.** The budget is twelve monthly rows, not one annual row. MISO's
  coal is not spread evenly across the year, so months 1, 2, 6, 7, 8, 9 and 12
  exceed a flat 1/12 cap even in a year whose annual total nearly fits. This is
  the stated no-carry limitation doing the work, and it is reported as such
  rather than presented as extra accuracy.
* **The heat rate.** The cap is in **MMBtu**, so converting it to TWh needs the
  fleet's dispatch-weighted heat rate. Recovered from the solve itself, the
  implied HR on the seven binding months is **11.320 MMBtu/MWh (11.056–11.621)**
  — a tight, coherent fleet number across seven independent months, which is
  itself the evidence that each row binds exactly at its cap. The `base_hr`
  **10.661** used in the pre-solve table is the CAMPD *marginal* summary's base,
  a different statistic, **6.2 % lower**.

Per-month, so the claim is checkable (TWh):

| mo | control | ARM | cut | implied HR |
|---|---:|---:|---:|---:|
| 1 | 24.54 | 20.42 | 4.12 | 11.357 |
| 2 | 21.06 | 19.95 | 1.11 | 11.621 |
| 3 | 18.47 | 18.47 | 0.00 | — |
| 4 | 15.65 | 15.65 | 0.00 | — |
| 5 | 18.80 | 18.80 | 0.00 | — |
| 6 | 26.13 | 20.48 | 5.65 | 11.320 |
| 7 | 30.90 | 20.97 | 9.93 | 11.056 |
| 8 | 29.88 | 20.90 | 8.98 | 11.092 |
| 9 | 24.03 | 20.53 | 3.50 | 11.292 |
| 10 | 17.45 | 17.45 | 0.00 | — |
| 11 | 17.24 | 17.24 | 0.00 | — |
| 12 | 21.56 | 20.15 | 1.40 | 11.505 |

Five months are untouched to the milli-TWh — the row is genuinely slack there,
not quietly re-shaping the year.

**The correction that follows for the FULL SPAN**: the annual-form slack in
§3.1 is the wrong statistic for predicting bite in *any* year. A year with large
annual slack can still bind in a peak month. The span's per-year result must be
read on the monthly grain, and the G-FOOTPRINT claim that 2020/21/23/24/25 are
"inert" is an **annual** statement that the span will test directly.

## 4. G-DRIFT — reported INCOMPLETE, and one control spent because of it

Rule 29 `[R-SCREEN]` (b) makes the keeper's committed bundle the control
(**form 4**) only when a code-level drift audit finds every changed hunk INERT.
It could not be completed:

1. **The keeper's recorded `git_sha` `d0fec486` is UNREACHABLE** — `git cat-file`
   returns *"Not a valid object name"*. It was a shard-branch commit and the
   branch has been deleted, which is precisely the failure rule 33
   `[R-SHARD-ARCHIVE]` (d) exists to prevent. The literal audit cannot run.
2. Against `3cd1021b` (the commit that landed the keeper bundle on `main`) the
   solve path has moved **51 files / 5,280 insertions** — not a volume this
   session will certify hunk-by-hunk.

Established mechanically instead, and worth keeping:

* **MISO's solve-surface fingerprint is byte-identical at HEAD**:
  `9f0845000dc8af6e`, **210 rows, `moved: {}`** — the value the keeper's own
  `run_config` records, and the value **both screen bundles carry**.
* Every MISO mention in the changed backcast-path files is set-membership
  expansion adding **NWPP/SOCO**; MISO's own membership is untouched.
* Default `cache_key` unchanged.

Form 4 was therefore **not claimed**, the LIVE-hunk branch applied, and one
control was spent for the screen year. That is also strictly better evidence: a
same-HEAD A/B cannot be contaminated by drift at all.

## 5. KNOWN LIMITS — carried forward

* **Monthly rows do NOT carry stock across months.** §3.2 shows this is doing
  most of the work, so it is the first thing a successor should challenge. A
  true SOC-style carry is a new LP row family and was deliberately not this arm.
* **Minimum operating stock is ZERO**, so the budget is *looser* than physics. A
  floor may be added later only from a **cited days-of-burn source**, never from
  the gap.
* **One number carries the falsification**: at a coal fleet heat rate of exactly
  10.0 MMBtu/MWh the annual budget is non-binding. It is measured at 10.661
  (CAMPD summary) and the fleet's dispatch-weighted value is 11.32.
* **The footprint is conservatively tight by an unquantified amount**: terminals
  in the EIA record (`CCT Terminal` IL, `Four Rivers` KY, `Keystone`/`Conemaugh`
  PA) cannot be tied to a served plant from the data alone and are omitted
  rather than guessed. Only `DTE-BRSC` (8841) is crosswalked, and including it
  **loosens** the budget.
* **2025 plant-level stocks are not published.** 2025's opening stock is
  December 2024 and its rate is 2023+2024 — both curated. Verified, not assumed:
  the 2025 row above is computed.

## 6. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

Both screen bundles are on local disk **and** on their shard branches, so a
promotion costs **zero re-solves**. They are `.gitignore`d, not deleted — rule 31
`[R-RETAIN]`, and the `.gitignore` entry itself carries the recovery lines.
Recovery is pinned by **full SHA**, never branch name (rule 33 (d)):

```
git checkout 71ad0a1a5a476ec767776b5675654463df09c79a -- results/calibration/miso259_screen_arm
git checkout 70ef3071eed52d694254592258f8e3beec00d3b4 -- results/calibration/miso259_screen_control
```

| shard | id | outcome | archived |
|---|---|---|---|
| screen ARM 2022 | `session_01BGzerCZNzqG7QLHheUgyBg` | solved 12m13s, pushed `71ad0a1a…` | **yes**, after fetch + checkout + verify |
| screen CONTROL 2022 | `session_015CAYrZRWrXYKXsvd8RPqFA` | solved, pushed `70ef3071…` | **yes**, same order |
| full span 2020–2025 | `session_01CvgiaL1tMHNupUWJCCVuxe` | in flight, ~90 min budget stated in its prompt | no — still solving |

## 7. GATES AT HEAD

| check | result |
|---|---|
| `check_cache_key_registration` | **ok** — 302 registered, all resolve, all declared defaults match |
| `check_mechanism_matrix --base origin/main` | **exit 0** (anchor-drift warnings are pre-existing and not this lane's rows) |
| `build_status --iso MISO --check` | **in sync** |
| `audit_keepers --iso MISO` | **0 failures**, 1 warning (the pre-existing E3 `meta.json`-vs-`calibration_flags` years) |
| `check_bench_freshness --iso MISO` | 6 parts, **0 STALE**, all reproduce at HEAD |
| `check_registry_payload_parity` | 2 REDs, both **pre-existing and not MISO's** (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) — neither touched |
| `check_gate_a_provenance` | fails on **NYISO** and **SPP** only; MISO's row clean. Escalated, not fixed |
| `pytest tests/scoring` | **18 failed at HEAD, 18 on `origin/main`, identical sets — ZERO new** |
| `node --check` on all 10 matrix files | pass |
| default `cache_key` | **`9ca2c6052b4850ea`** on both `origin/main` and HEAD; armed `51e13b62907f1911` |

## 8. RULES

Rule 1 `[R-STRUCT]` (the screen is structural and was never scored on the price
residual) · rule 13 `[R-MEASURED]` (G-PIN, enforced in code and tested) · rule 14
`[R-ACCURATE]` (the shared-storage reconciliation, taken in the direction that
weakens the mechanism) · rule 19 `[R-ONE-MECH]` (a missing limb; its own kwarg
family) · rule 21 `[R-DOF]` (one ledger entry, identified by the owner's ex-ante
ruling) · rule 24 `[R-REGISTRY]` · rule 25 `[R-ISO-SCOPE]` (MISO-gated by a
raise) · rule 28 `[R-MECH-MATRIX]` (base row + a cell in all nine shards) · rule
29 `[R-SCREEN]` (phase 0 first; one-year screen; G-DRIFT reported incomplete and
the control spent; bundles kept out of `main`) · rule 31 `[R-RETAIN]` (nothing
deleted; the promotion question is the owner's) · rule 32 `[R-SHARD]` (the parent
ran no LP) · rule 33 `[R-SHARD-ARCHIVE]` (archived after fetch + checkout +
verify; recovery by full SHA) · rule 34 `[R-SHARD-PROMOTABLE]` (every shard
pushed its bundle).
