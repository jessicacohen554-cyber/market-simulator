# PRECOMMIT — R-ERCOT: re-solve ERCOT 2019–2025 on corrected backcast inputs

**Session:** R-ERCOT (parent/orchestrator; never solves — rule 32(a)), 2026-09-24.
**Charter:** `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.2, executed in full.
**Precondition:** F1 (#6572) and F2 (#6569) merged; branch cut from `9210075392a128d14a5efb168ab1f9955a9b6946`.
**Incumbent:** `2026-09-19-ercot266-mer-five-year`, bundle `results/calibration/ercot_mer20260919_five_year`, registered **{2021, 2022, 2023, 2024, 2025}**.
**Owner instruction (2026-09-24):** every backcast year 2019–2025 on the year-correct EIA-860 vintage, plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

This is an **input correction, not a tuning exercise**. Offer-curve multipliers are UNCHANGED from the incumbent, leg for leg (rule 1(c)). Nothing here is selected on a residual.

---

## 1. Year set (rules 34(c) / 35(b))

The registered ERCOT year union over every ERCOT sidecar is **{2021, 2022, 2023, 2024, 2025}**. There is one registered run, the keeper, and nothing is folded to it. This lane solves **2019–2025**: the five incumbent years plus 2019 and 2020, which are new.

Benchmarks exist for all seven years. `actual_lmp_hourly_ERCOT` and `actual_lmp_zonal_ERCOT` cover 2018–2026, EIA-930 BALANCE covers 2019+, and TX CAMPD covers 2019–2026. The zero-LP fleet build ran clean for 2019 and 2020 (§4).

## 2. Recipe groups — which partition 2019/2020 take, and why

The incumbent is the owner's two-config keeper (ruling 2026-08-26), which has three recipe groups:

| group | years | overlay over the forward recipe |
|---|---|---|
| carve-out A | 2021, 2022, **and now 2019, 2020** | `ercot_offer_swcap_clip=true` + the ×33 `offer_curve_by_group` (`CC_REGULAR.peak 151.008`, `CT_PEAKER.peak 433.95`) |
| carve-out B | 2023 | the same, plus `ercot_zonal_spread_ep_referenced=false` |
| forward | 2024, 2025 | none (`swcap_clip=false`, `CC_REGULAR.peak 4.576`, `CT_PEAKER.peak 13.15`) |

**2019 and 2020 take carve-out A.** The reason is structural, not the residual:
- The forward config is designated for the forward market: the regime the model uses going forward, from 2024 on.
- ERCOT's pre-2023 years (2021, 2022) already run on carve-out A.
- 2019 and 2020 share that pre-ECRS market design: ECRS went live June 2023, and they predate the post-Uri ORDC and market reforms.
- The SWCAP clip is an offer-domain invariant, "no thermal offer above the cap", which holds by market design in every year.

No 2019 or 2020 number was looked at to make this choice; neither year has ever been solved. The carve-out-A offer curve is committed verbatim, copied from the keeper's own 2021 overlay, at `docs/handoffs/r-ercot/carveout_a_offer_curve_by_group.json`. The 2021 and 2022 overlays are byte-equal.

## 3. The arm — what changes over the incumbent, in every year

The following flags are set explicitly on every leg with `--set`. None of them is new. Six of them are F1's backcast defaults, which the keeper's `meta.json` records as null.

| flag | value | what it does for ERCOT |
|---|---|---|
| `eia860_vintage_tracks_solve_year` | true | Each year reads `vintage_<Y>` (2019–2024; 2025 reads canonical) for the non-bin EIA-860 units, the COD map and the retiree channel. On the bin path it also arms the **year-matched eGRID** step below. |
| `measured_{ct,coal,st,cc,chp}_heat_rates` | true | These are F1's per-year CAMPD artifacts. They were **inert on ERCOT's bin path until this lane** (see §3a). |
| `unit_outage_short_windows` + `unit_outage_short_windows_gas` | true | The < 5-day CAMPD windows, from F2's ERCOT `campd-unit-outages-short.csv` and `-shortgas.csv`. The gas scope can only be read through the coal flag, which is why both are set. |

Everything else is carried over unchanged: the std extract, `ercot_partial_outage_shaped_derate`, `ercot_noncampd_plant_availability`, the DAM availability stack and every offer-curve band.

### 3a. The code change: ERCOT's curated bins get year-matched plant heat rates

**Provenance of the sheet's `Plant_Avg_HR_MMBtu_MWh` (deliverable (a), measured this session).** The sheet has 304 rows, all a single snapshot:
- **200 of 283 non-null rows (71 %) are eGRID 2023 `PLHTRT`, exact to 2 dp.** The match rate against every other vintage is below 10 %.
- The remainder is mostly `CC_REGULAR` (38 of 41 rows), `COAL` (9 of 10) and a few CT/CHP rows. These track a **CAMPD gross-basis annual rate (heat input ÷ gross load) over 2023–2024**, with a median ratio of 1.003, but are not exactly reproducible. They look like hand curation, with the curation years undocumented. Because they are on a gross basis, coal runs about 9 % below its net rate: Martin Lake is 10.28 on the sheet against 11.79 in eGRID 2023.
- `docs/binning-methodology.md` says the bins were "derived from EPA CAMPD gross generation for 2023-2024". That describes the bin split, not the heat rate.

So every ERCOT solve year dispatched on 2023-era rates.

**Change (deliverable (b)).** `campd_bins.resolve_bin_heat_rates` plus new keyword arguments on `load_campd_bins`. `run_calibration.run_year` passes them **only when `mode == "backcast"`**. Each sheet row is re-resolved for the solve year through the F1 hierarchy every other ISO already uses:

1. the class's measured CAMPD artifact: the solve year's own `ok` row, else the pooled 2019–2025 `ok` row. Class routing is COAL→coal, ST_GAS→ST, CC_REGULAR→CC, CT_PEAKER→CT, and CC/CT/ST_CHP→CHP power-only, keyed on (plant, class);
2. else eGRID `PLHTRT` at the solve year's vintage, with the nearest-vintage fallback;
3. else the sheet value;
4. else `BIN_GROUP_HR_DEFAULT`.

**Zero new `ScenarioConfig` fields and zero free parameters.** The gates are the six existing F1 flags, all coerced off outside backcast, so every forecast and hindcast bin frame is byte-identical. A unit test pins this. The cache ledger carries a same-key entry because the flags were already key-moving, but the ERCOT path ignored them.

**Deliverable (c).** The vintage flag resolves per year. On the non-bin `(none)` class, fleet MW moves from 5,656 to 5,043 / 5,065 / 5,201 / 5,598 MW in 2019–2022, as vintage_<Y> rows replace the snapshot. In 2025 it is identical, because there is no `vintage_2025`. F1's census already verified the ERCOT retiree channel: class-table MW went 1,670 → 354 (2019) and 840 → 0 (2020–2023).

### 3b. Kiamichi (F2's routed item): NOT added — rule 19

F2 routed Tenaska Kiamichi (55501, 1,370 MW, CEMS filed under OK) here. **It is already measured by a better ERCOT-native source.** `ercot_noncampd_plant_availability` (armed on the keeper) applies the 60-Day DAM per-plant live HSL / Resource Status for Kiamichi, which measures its *switchable ERCOT share*. OK CEMS windows would measure the whole plant, including hours it serves SPP. Adding them would stack a second outage mechanism on the same plant, which rule 19 `[R-ONE-MECH]` forbids. Its heat rate is covered: CAMPD CC `ok` row / eGRID.

### 3c. Short-gas "merit guard clears" — measured

F2 derived the ERCOT short-gas extract with `merit_order_guard=true`. The guard booked **262 / 238 / 140 / 218 / 204 / 245 / 302** windows (2019–2025) as economic layup, against **506 / 460 / 461 / 452 / 382 / 397 / 428** kept as in-merit forced stops. That means 23–41 % was separated out, compared with 5–11 % on PJM. The guard is live and doing work on ERCOT's own fleet, so this arms it as the charter directs.

**The standing ERCOT objection (matrix cell `U`) is answered by measurement, not inherited from PJM.** Where the 60-Day DAM availability overlay covers an hour, it **rescales the class-hour (and pins crosswalked plants) to the measured DAM level after every other layer**. On covered hours, short-gas windows therefore only redistribute within the class. They bind at the level only on DAM-uncovered hours.

## 4. Phase-0 census (zero LP): `docs/handoffs/r-ercot/census_r_ercot.json`

The census comes from `scripts/probes/_r_ercot_census.py`, which rebuilds each year's LP fleet with `run_year(fleet_only=True)` twice: once with the incumbent recipe at HEAD (all eight §3 flags pinned False), and once with the arm.

**(b) Bin heat-rate sources, every year:**

| source | MW |
|---|---|
| measured CAMPD | 70,097–70,290 |
| year-matched eGRID | 8,368–8,561 |
| sheet | 1,917 |
| class default | **1,129.9** |

The sheet rows are W A Parish [ST] 34702 and Barney M Davis [ST] 49392: synthetic codes with no CAMPD or eGRID match. The class-default rows are the plants **absent from every source under the sheet's plant code**:
- Hidalgo Energy Center 55545 (551.3 MW),
- Arthur Von Rosenberg 7512 (575.0 MW),
- WAL1801 / WAL5479 / WAL537 (1.2 MW each).

**Found and routed, not fixed:** Hidalgo *is* in eGRID, as ORISPL **7762** "Calpine Hidalgo Energy Center", 551.3 MW. It has no `PLHTRT`, but `PLHTIAN / PLNGENAN` gives 6.96–7.18 across 2019–2024. The sheet's 55545 does not match. Repairing that needs a curated code crosswalk (a reference-data change with downstream derive consequences), which is outside an input-correction solve. The three WAL units carry zero heat input in eGRID.

**Cap-weighted base heat rate, sheet → arm (MMBtu/MWh), and cap-weighted median `mc_base` ($/MWh), incumbent → arm:**

| class | HR 2019 | HR 2023 | HR 2025 | median mc 2019 | 2021 | 2023 | 2025 |
|---|---|---|---|---|---|---|---|
| CC_CHP | 7.88 → 8.91 | 7.88 → 9.12 | 7.88 → 9.08 | 22.6 → 31.7 | 45.5 → 70.7 | 23.2 → 33.7 | 24.8 → 36.6 |
| CC_REGULAR | 7.82 → 7.90 | 7.82 → 7.69 | 7.82 → 7.70 | 17.6 → 17.9 | 51.8 → 52.7 | 18.9 → 19.1 | 23.8 → 23.9 |
| COAL | 10.34 → 10.91 | 10.34 → 11.20 | 10.34 → 11.16 | 18.5 → 18.5 | 18.5 → 18.5 | 20.8 → 20.8 | 18.5 → 18.5 |
| CT_CHP | 9.51 → 8.82 | 9.51 → 7.39 | 9.51 → 7.11 | 39.5 → 23.9 | 99.4 → 48.8 | 40.8 → 20.7 | 42.9 → 20.7 |
| CT_PEAKER | 10.92 → 11.66 | 10.92 → 11.59 | 10.92 → 11.53 | 40.5 → 43.6 | 82.9 → 86.2 | 42.1 → 45.0 | 45.8 → 48.4 |
| ST_GAS | 11.18 → 11.46 | 11.18 → 11.35 | 11.18 → 11.35 | 31.4 → 32.4 | 87.2 → 89.2 | 33.2 → 34.0 | 42.7 → 44.1 |

**Read-outs, stated before any solve:**
- **The largest mover is CC_CHP (+13–17 % base HR, +40–55 % median offer).** This is F1's power-only CHP rate (eGRID heat with the CHP useful-thermal allocation added back) replacing the steam-credited rate.
- **CT_CHP moves the other way (−7 to −25 % HR).**
- **Coal's base HR rises 6–8 %, but its median offer does not move.** ERCOT-144's per-plant SCED TPO offer levels reprice every coal committed/econ tranche, so coal HR reaches only must-run / peak tranches and emissions.

**(c) Outage availability (mean available MW), incumbent → arm:**

| year | CC_REGULAR | ST_GAS | COAL | CC_CHP |
|---|---|---|---|---|
| 2019 | −588 | −263 | −128 | +6 |
| 2020 | −503 | −148 | −88 | +7 |
| 2021 | −347 | −84 | −59 | +30 |
| 2022 | −198 | −109 | −95 | −2 |
| 2023 | −349 | −35 | −65 | −46 |
| 2024 | −216 | −61 | −99 | −48 |
| 2025 | −287 | −35 | −142 | −73 |

**Nameplate is identical in every thermal class.** ERCOT's dispatch fleet is the curated sheet.

## 5. G-DRIFT (rule 29(b)) — LIVE, so a control is solved

`git diff 5926ca52 9210075 --` over the backcast path touches **55 files, +11,607 / −340**. The following are **LIVE by design**:
- F1: `data/egrid.py`, `data/fleet/eia860.py`, `data/fleet/campd_bins.py`, `scripts/lib/heat_rate_years.py`, and the six `scenarios.py` default flips;
- F2: `data/campd.py` merit-panel pin (deriver-only) and the re-derived extracts;
- this lane's own `campd_bins.py` / `run_calibration.py` change.

The rest (ten days of engine commits, including `model/lp/*`, `pipeline/solve.py`, `data/outages.py`, `fleet/arrays.py`) is **not hunk-classified**. At this size an honest classification is a lane of its own. **So rather than asserting form 4, a CONTROL is solved:** the incumbent recipe at HEAD for 2021–2025, with all eight §3 flags pinned False. Arm − control isolates the input correction. Control − keeper measures engine drift since `5926ca52`. Control bundles are pushed (rule 34(a)) and kept out of `main` (rule 29(c)).

## 6. Shards (rule 36: one year per shard, own container)

All shards are pinned to the SHA of the commit carrying this PRECOMMIT. There are twelve:
- **ARM** 2019, 2020, 2021, 2022, 2023, 2024, 2025: out-dir `results/calibration/r_ercot_arm_<Y>/`, branch `claude/r-ercot-arm-<Y>`;
- **CTL** 2021, 2022, 2023, 2024, 2025: out-dir `results/calibration/r_ercot_ctl_<Y>/`, branch `claude/r-ercot-ctl-<Y>`.

Every leg is `scripts/replay_keeper.py results/calibration/ercot_mer20260919_five_year --years <Y> --out-dir … --set …`. The keeper's own `config_partition_overrides` supplies each incumbent year's overlay. **2019 and 2020 additionally take `--set ercot_offer_swcap_clip=true` and `--set offer_curve_by_group=<carveout_a file>`**, which uses the same two-channel routing the overlay uses.

**Per-leg config signature, a hard stop:**

| leg | `swcap_clip` | `zonal_spread_ep_referenced` | `CC_REGULAR.peak` | `CT_PEAKER.peak` |
|---|---|---|---|---|
| 2019–2022 | true | true | 151.008 | 433.95 |
| 2023 | true | false | 151.008 | 433.95 |
| 2024 / 2025 | false | true | 4.576 | 13.15 |

In addition, the eight §3 flags must read true on arms and false on controls.

**Input sha256 (hard stop):**

| file | sha256 |
|---|---|
| `campd-unit-outages.csv` | `b569de2a…` |
| `-short.csv` | `d0d03bf0…` |
| `-shortgas.csv` | `2ac566ac…` |
| `custom-bin-assignments.csv` | `19d726cd…` |
| `campd_cc_heat_rates_ERCOT.csv` | `3ebfd9b5…` |
| `chp_power_only_heat_rates_ERCOT.csv` | `2f1dfd18…` |

**Budget:** ~15–20 min per year (974 s / 12.6 GiB measured on ERCOT with MER). The twelve legs run in parallel in twelve containers.

## 7. Sealed predictions (scored in the RESULT)

- **P1:** CC_CHP energy falls against the control in every year, and CT_CHP energy rises. Both are the direct sign of the HR moves.
- **P2:** coal energy moves less than 2 % against the control in every year, because its offer levels are SCED-anchored.
- **P3:** every arm year dispatches zero MW of the eGRID-less / CAMPD-less residual at a class-table HR outside the 1,129.9 MW listed in §4.
- **P4:** if a C-criterion regresses against the control, it is reported at full magnitude and root-caused (rule 14). No multiplier is re-tuned.
- **P5:** the ISO determination for the promotion question is scored on the arm's own composite. Its train-tier years are 2023–2025 (rule 30(c)). 2019–2022 are reported per year.

## 8. Retention

- Every leg pushes its full bundle, including `dispatch/<Y>_P1.parquet`, via a `.gitignore` negation and a plain `git add` (rule 34(a)).
- The parent requires `git ls-tree` to show more than 0 files, then fetches, verifies and composes before archiving (rules 33/34(d)).
- What must survive lands on `main` in the composed bundle (rule 33(f)).
- Nothing is deleted (rule 31). The promotion question goes to the owner, and **this session does not promote**.
