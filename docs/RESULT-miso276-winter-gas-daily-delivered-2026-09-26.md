# RESULT — miso-276: winter-month daily delivered gas (owner ruling D1). The ruled construction works as built, but C3b 2021 gets worse (0.290 → 0.416). No criterion flips. Promotion is the owner's call.

```
LANE     : miso-276 (D1, owner rulings 2026-09-26 "Daily delivered price" + "Chicago proxy")
PREREG   : docs/PRECOMMIT-miso276-winter-gas-daily-delivered-2026-09-26.md (pin 2837e3c9)
KEEPER   : 2026-09-26-miso-275-cc-exempt (miso275_span) — unchanged
RUN      : 2026-09-26-miso-276-winter-daily (results/calibration/miso276_span, 2019-2025), registered
DELTA    : miso_winter_gas_daily_delivered = true (new field, default off). DOF +0
CONTROL  : keeper bundle (G-DRIFT e5acf0fe..2837e3c9 all INERT; rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape — the same three criteria as the keeper)
           train 2023-2025 CALIBRATED (unchanged); zero criterion-year status flips
```

## 1. Legs

Seven single-year shards were pinned to `2837e3c9`. 2020 and 2023 were relaunched after 55 min stuck in PENDING
(no container). Each leg was fetched by the parent and passed the recipe, vintage, inputs and classifier checks
there. Each leg's shard reported its log check.

Every bundle has 17 files including `dispatch/<Y>_P1.parquet`. All 9 shard sessions are archived.

| year | leg commit (provenance) | LW internal price keeper → arm $/MWh | slack MWh keeper → arm |
|---|---|---|---|
| 2019 | `e9289f3e` | 27.796 → 27.974 | 0 → 0 |
| 2020 | `90f99410` | 24.377 → 24.494 | 0 → 0 |
| 2021 | `2ba90191` | 38.677 → 40.688 | **0 → 2,021.3 (4 h)** |
| 2022 | `b2d3ebab` | 58.582 → 58.399 | 0 → 0 |
| 2023 | `6cc66eb6` | 33.256 → 32.675 | 0 → 0 |
| 2024 | `26f4347c` | 30.498 → 30.730 | 18,531.5 → 18,531.5 (identical) |
| 2025 | `a640ebca` | 41.792 → 41.670 | 0 → 0 |

The 2021 slack is 4 hours in MISO-South on Feb 15, during Uri, cleared at the $1,000 cap. With South gas on Henry
Hub and the Chicago print in the North, the South can no longer import enough in those hours.

**S-3 is reported, not a stop.** The gate says an arm year with more slack is reported with its hours. MISO did
direct load shed in MISO-South during Uri; that is noted as context only, and the hours are not claimed to match.

## 2. Gates (live scorer, same bench parts for both runs)

| criterion-year | keeper miso-275 | miso-276 |
|---|---|---|
| **C3b 2021** | NRMSE 0.290 FAIL | **0.416 FAIL** (worse) |
| C3b 2019 / 2020 / 2022 / 2023 / 2024 / 2025 | 0.086 / 0.100 / 0.192 / 0.069 / 0.108 / 0.122 | 0.087 / 0.106 / 0.192 / **0.059** / 0.107 / 0.124 |
| C3a 2021 | −4.8 % | **+0.1 %** |
| C3a 2022 | −15.4 % FAIL | −15.8 % FAIL |
| C3a 2019 / 2020 / 2023 / 2024 / 2025 | +5.2 / +6.0 / +1.2 / −5.6 / −8.1 % | +5.9 / +6.5 / −0.5 / −4.9 / −8.3 % |
| C1 ST_GAS 2019 | −8.46 FAIL | −8.60 FAIL |
| C1 CC_REGULAR 2023 | −3.47 | **+0.61** |
| C1 CT_PEAKER 2024 | −2.52 | −4.21 (PASS) |
| C3c 2022–2025 | CAVEAT, identical | CAVEAT, identical |
| C2, C4, C6, C8 | PASS | PASS |
| train tier 2023–2025 | CALIBRATED | CALIBRATED |
| full span | NOT-YET (same three criteria) | NOT-YET (same three criteria) |

**Winter months, load-weighted price $/MWh (keeper → arm, actual):**

| month | keeper → arm | actual |
|---|---|---|
| Feb-2021 | 65.8 → **91.8** | 45.4 |
| Feb 13–16 storm week | 123.6 → **334.8** | ~141 |
| Jan-2024 (Heather) | 39.4 → 44.5 | 42.2 |
| Dec-2021 | 37.6 → 35.4 | 42.5 |

## 3. Reading

**What the arm fixes (the structural half).**
- It removes the construction defect FINDING-miso269 §1 found: Chicago-zone gas priced below the traded commodity
  on calm storm-month days, and the storm cost smeared over every day in the other zones.
- Calm Feb-2021 gas now sits at hub plus transport in every zone: West 13.7 → 5.5, South 20.8 → 5.1, Chicago zones
  1.2–2.0 → 5.3–8.3.
- Jan-2024 moves toward actual, and C3b 2023 improves (0.069 → 0.059).

**What it costs (the declared hazard, realised).**
- The ruled construction passes the $129.52 Chicago Uri weekend print through. Under the owner's proxy ruling it now
  reaches West and Plains as well.
- Storm-week price lands at 334.8 against ~141 actual. That is the 158 → 317 miso-269 measured statically, and a
  little worse.
- February 2021 moves from 20 above actual to 46 above. That alone takes C3b 2021 from 0.290 to 0.416.
- The only zero-DOF alternative would be a threshold on which prints to pass through, which is a fitted selection.
  The owner ruled the spike days in, so the arm does not trim them.

**Net.** No criterion changes status in any year. This is a structural repair of a measured-input construction
(rule 14) that makes one failing object worse. Under rule 1 the worse C3b does not retract it and does not validate
it.

## 4. Where the bytes are

The composite `miso276_span` lands on `main` with this lane's PR. It holds:
- the slim bundle (47 files, 17.6 MB, the keeper's shape);
- the `hourly/` sidecars;
- the attestation (keeper's plus a `miso276` block, DOF +0);
- the regenerated diagnostics;
- the stamped partition, byte-identical to the keeper's and passing `--check`;
- the registry sidecar and the payload.

Promotion from there costs **zero re-solves**.

The per-year leg dirs are on this session's disk only, gitignored. The SHAs above are provenance (rule 33(d)).

## 5. Promotion

**Not recommended on calibration grounds.** C3b 2021 gets materially worse and nothing flips to PASS.

**Arguable on structural grounds.** The owner's standard is *"If it's an improvement structural or calibration then
promote yes."* The arm replaces a construction that priced gas below its own commodity. It is also the owner's own
D1 ruling, built as ruled.

- **If promoted:** the C3b 2021 regression and the 4 h of South slack go on the keeper's record at full magnitude.
- **If declined:** the field stays default-off, and the matrix cell `winter_gas_daily_delivered` goes to `R`, with
  the storm-print pass-through named as the reason.

Year set (rule 35(b)): outgoing {2019–2025}, incoming {2019–2025}, so it is covered.
