# RESULT — shard `nyiso223-y2024-r2` (NYISO 2024, hub-daily unpriced-day gap fill)

Session **nyiso-223** · shard relaunch · pinned SHA `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99`
Solve: 2026-09-10 02:40:22 → 02:46:36 UTC (**6 min 14 s**, well inside the 20-min shard budget, rule 32 `[R-SHARD]`).

**Arm:** `results/calibration/nyiso_fuelvintage_A` replayed on 2024 with
`--set nyiso_hub_gap_month_level=true` → `results/calibration/nyiso223_gapfill_2024`
(gitignored; **retained on local disk** per rule 31 `[R-RETAIN]` — nothing deleted).

**Control basis:** the incumbent keeper's **committed** `nyiso_fuelvintage_A` bundle
(rule 29 `[R-SCREEN]` (b), G-CTRL form 4). No control solve was spent.

---

## 0. Hard stops and gates — all PASS

| Check | Expected | Got |
|---|---|---|
| `git rev-parse HEAD` | `ce4779ec…ed99` | ✅ match |
| keeper `meta.json` `iso` | `NYISO` | ✅ `NYISO` |
| `grep -c nyiso_hub_gap_month_level scenarios.py` | ≥ 4 | ✅ 4 |
| Pre-solve gate: annual mean off→on | 2.7969 → 2.7969 | ✅ 2.7969 → 2.7969 |
| Pre-solve gate: Dec 22–31 off→on | 3.877 → 4.061 | ✅ 3.877 → 4.061 |
| Pre-solve gate: hours moved | 5880 | ✅ 5880 |

**Clean-tree build** (the relaunch fix) worked as briefed and needed **no third datatype**:
`curate_capacity_deliverability.py --isos NYISO` (35 rows) and
`curate_nyiso_interface_flows.py` (2023–2026, 158,112 rows for 2024) were sufficient to solve.

### Post-solve signature — all 7 PASS

`nyiso_hub_gap_month_level` **true** · `offer_curve_by_group.CC_REGULAR.peak` **2.25** ·
`.pct_peaking` **8.0** · `nyiso_gas_commitment_bridge` **true** ·
`nyiso_dynamic_reserve_requirements` **true** · iso **NYISO** · years **[2024]**.

Solve health: **slack 0.0 TWh, dump 0.0 TWh** in both arm and keeper.

> **C3a %-error / C3b NRMSE are NOT computed here** — no `lmp` clean partition, exactly as the
> sibling 2022 shard found. Expected; not chased. Scoring is the parent's job.

---

## 1. Annual mean LMP (P1, 5 load zones)

Load zones = Capital_Hudson, Long_Island, Lower_Hudson, NYC, Upstate_West.
`NYISO_external` is the import node (0 demand) and is **excluded** from both legs.

| | ARM | KEEPER | Δ |
|---|---:|---:|---:|
| **Load-weighted** ($/MWh) | **38.7081** | 38.6332 | **+0.0748** |
| **Equal-hour** ($/MWh) | **39.2210** | 39.1571 | **+0.0639** |

ISO load 150.5167 TWh (identical both legs).

## 2. Monthly means — load-weighted ISO price ($/MWh)

> **Calendar note.** The model runs a **non-leap 365-day / 8760-hour** calendar (rule 8
> `[R-8760]`; `hubs._DAYS_IN_MONTH` sums to 365, December starts at hour **8016**). These
> figures use that calendar. An earlier draft of this shard's analysis sliced months on a
> 366-day leap calendar and was misaligned from March onward — corrected here and in §6.

| Mon | ARM | KEEPER | Δ |
|---|---:|---:|---:|
| Jan | 63.135 | 62.473 | **+0.662** |
| Feb | 33.728 | 33.730 | −0.002 |
| Mar | 32.174 | 32.168 | +0.006 |
| Apr | 31.542 | 31.542 | +0.000 |
| May | 30.483 | 30.475 | +0.009 |
| Jun | 37.246 | 37.211 | +0.035 |
| Jul | 42.447 | 42.453 | −0.006 |
| Aug | 38.309 | 38.298 | +0.012 |
| Sep | 36.347 | 36.337 | +0.010 |
| Oct | 34.050 | 34.050 | +0.000 |
| Nov | 31.154 | 30.912 | **+0.242** |
| Dec | 52.801 | 52.879 | **−0.078** |

The effect is concentrated in the **winter shoulder months**: **January +0.662** and
**November +0.242** carry it. Hour-weighted, Jan contributes **+0.0562** and Nov **+0.0206** of
the **+0.0748** annual delta — **together 103 %**, with December's **−0.0066** and the
Feb–Oct near-zeros netting the remainder back down.

**December's monthly mean moves the "wrong" way (−0.078) while its gap-filled tail moves up.**
That is not a contradiction — see §6: the mechanism *redistributes within* December rather than
lifting it, and the priced-day majority (Dec 1–21) outweighs the gap-filled tail in a
month-mean.

## 3. C3c — price tail

| | ARM | KEEPER |
|---|---:|---:|
| Hours load-weighted ISO price > $300 | **0** | 0 |
| Hours **any** zone > $300 | **0** | 0 |
| **Max zonal price** | **$217.674** | $217.864 |

As the brief anticipated: the keeper's 2024 max is $217.9, so a $300 bar sits ~38 % above the
model's annual maximum. **Zero hours is the expected outcome, not a failure.** The arm's max is
$0.19 *lower* than the keeper's.

## 4. C1 per-class TWh — **basis A**: `hourly/class_hourly_2024.parquet`, `pass == "P1"`, Σ mw ÷ 1e6

This is P1 grid-delivered energy by class.

| class | ARM | KEEPER | Δ |
|---|---:|---:|---:|
| CC_REGULAR | 36.9470 | 36.9751 | −0.0281 |
| nuclear | 26.9532 | 26.9532 | +0.0000 |
| hydro | 26.7390 | 26.7390 | +0.0000 |
| import | 20.7058 | 20.7057 | +0.0001 |
| CC_CHP | 19.5467 | 19.5658 | −0.0191 |
| ST_GAS | 8.5777 | 8.5443 | **+0.0334** |
| wind | 6.0116 | 6.0116 | +0.0000 |
| OTHER | 2.2014 | 2.2014 | +0.0000 |
| CT_CHP | 1.2047 | 1.1946 | +0.0101 |
| ST_CHP | 1.1350 | 1.1290 | +0.0060 |
| biomass | 0.7597 | 0.7597 | +0.0000 |
| solar | 0.5861 | 0.5861 | +0.0000 |
| oil | 0.4419 | 0.4434 | −0.0015 |
| CT_PEAKER | 0.3676 | 0.3705 | −0.0029 |
| COAL_BIT | 0.0000 | 0.0000 | +0.0000 |
| COAL_PRB | 0.0000 | 0.0000 | +0.0000 |
| **TOTAL** | **152.1775** | **152.1795** | **−0.0020** |

### 4b. ⚠ D-2 `class_total_twh` — **basis B**, REPORTED SEPARATELY

**The two bases are NOT interchangeable — the parent MUST difference like against like.**
The 2022 shard flagged a ~1 TWh CC_REGULAR gap; on 2024 the gap is **larger and it is not
confined to CC_REGULAR**:

| class | ARM D-2 | KEEPER D-2 | Δ (arm−keep) | **basis B − basis A (arm)** |
|---|---:|---:|---:|---:|
| *(untagged)* | 34.8381 | 34.8381 | +0.0000 | n/a — no basis-A counterpart |
| CC_REGULAR | 35.2402 | 35.2687 | −0.0285 | **−1.7068** |
| CC_CHP | 19.6333 | 19.6525 | −0.0192 | +0.0866 |
| hydro | 26.7390 | 26.7390 | +0.0000 | −0.0000 |
| ST_GAS | 10.6756 | 10.6414 | +0.0342 | **+2.0979** |
| CT_CHP | 2.2740 | 2.2575 | +0.0165 | **+1.0693** |
| ST_CHP | 0.0885 | 0.0889 | −0.0004 | **−1.0465** |

Two structural notes for the parent:

1. **D-2 covers only 7 buckets, basis A covers 16 classes.** D-2 emits rows only for classes that
   carry a forcing mechanism, so `import`, `nuclear`, `wind`, `solar`, `oil`, `biomass`,
   `OTHER`, `CT_PEAKER` and both coal classes have **no D-2 row at all**.
2. **D-2 carries an UNTAGGED bucket of 34.8381 TWh** whose `class` field is null and which holds
   `nuclear_mustrun` (26.9532) + `firm_import` (7.8840). It is **identical in the keeper**, so it
   is a keeper-side D-2 labelling artifact, not something the arm introduced — but it means D-2's
   nuclear and import energy is *not* addressable by class name.

**Arm-vs-keeper deltas agree between the two bases to ≤ 0.0008 TWh on every shared class**
(e.g. CC_REGULAR −0.0281 basis A vs −0.0285 basis B). So the basis mismatch is a *level* offset
in class attribution, not a distortion of the arm's effect.

## 5. C8 — forced share by class (D-2, 2024) with mechanism breakdown

Gates: `d2_peaker_max_share` 0.15, `d2_merchant_max_share` 0.30,
exempt = CC_CHP, CT_CHP, ST_CHP, nuclear.

| class | mechanism | forced TWh | class total | share |
|---|---|---:|---:|---:|
| *(untagged)* | **— CLASS TOTAL —** | 34.8372 | 34.8381 | **1.0000** |
| | nuclear_mustrun | 26.9532 | | 0.7737 |
| | firm_import | 7.8840 | | 0.2263 |
| **ST_GAS** | **— CLASS TOTAL —** | 2.2150 | 10.6756 | **0.2075** |
| | reliability_floor | 2.1949 | | 0.2056 |
| | nyiso_gas_commitment_bridge | 0.0201 | | 0.0019 |
| **hydro** | **— CLASS TOTAL —** | 7.6725 | 26.7390 | **0.2869** |
| | hydro_min_flow | 7.6725 | | 0.2869 |
| CC_REGULAR | **— CLASS TOTAL —** | 0.1191 | 35.2402 | 0.0034 |
| | nyiso_gas_commitment_bridge | 0.1191 | | 0.0034 |
| CC_CHP *(exempt)* | chp_steam | 0.0760 | 19.6333 | 0.0039 |
| CT_CHP *(exempt)* | chp_steam | 0.0023 | 2.2740 | 0.0010 |
| ST_CHP *(exempt)* | chp_steam | 0.0250 | 0.0885 | 0.2825 |

**D-2 PASSES** (`passed=true`, 0 failures). The two non-exempt material classes sit under the
0.30 merchant cap: ST_GAS 0.2075, hydro 0.2869. The untagged bucket reads 1.0000 but is
`nuclear_mustrun` + `firm_import` — nuclear is exempt and firm import is not a merchant class.

## 6. December split — equal-hour mean model price ($/MWh, 5 load zones)

December = hours 8016–8759 on the model's 365-day calendar; the Dec 1–21 / 22–31 cut is at
hour **8520** — the same boundary the pre-solve gate used.

| | ARM | KEEPER | Δ |
|---|---:|---:|---:|
| **Dec 1–21** | 53.2448 | 53.8102 | **−0.5654** |
| **Dec 22–31** | 54.3192 | 53.4327 | **+0.8865** |

Load-weighted, for reference: Dec 1–21 **52.4434** vs keeper 52.9692; Dec 22–31 **53.5509** vs
keeper 52.6886.

This is the mechanism's signature and it matches the pre-solve gate's direction and rough
magnitude. The gate said the Dec 22–31 **fuel** input moves +0.184 $/MMBtu (3.877 → 4.061,
+4.7 %); the Dec 22–31 **price** moves **+$0.89/MWh (+1.7 %)**, while Dec 1–21 moves
**−$0.57**. The gap-filled window gets more expensive and the priced days get cheaper as
dispatch reshuffles — a **redistribution within December, not a level shift**, and the two legs
very nearly cancel (which is why December's month-mean in §2 is slightly negative).

## 7. Legitimacy diagnostics

| Diagnostic | Verdict |
|---|---|
| D-1 diurnal shape | **PASS** (0 failures) |
| D-2 forced-energy attribution | **PASS** (0 failures) |
| D-4 off-window binding | **FAIL** (2 rows of 22) |
| D-5 forecast/backcast parity | **PASS** (0 failures) |
| D-9 overlay quarantine | **PASS** (0 failures) |
| D-10 free-class-only rescore | **PASS** (0 failures) |

### The two failing D-4 rows — and they are PRE-EXISTING IN THE KEEPER

| floor | plant | floored TWh | off-window share | binding hrs | measured median MW | measured zero share |
|---|---|---:|---:|---:|---:|---:|
| `reliability_floor × ST_GAS` | 2480 | 0.0002 | 0.0001 | 23 | 0.0 | 1.000 |
| `nyiso_gas_commitment_bridge × CC_REGULAR` | 54574 | 0.0021 | 0.0172 | 70 | 0.0 | 0.5571 |

Both are per-unit conduct riders: the meter says the unit is offline in at least half the hours
the floor asserts it must be online.

**Keeper comparison — the arm does not introduce these, and mildly IMPROVES one:**

| row | metric | KEEPER | ARM |
|---|---|---:|---:|
| `reliability_floor × ST_GAS` p2480 | floored TWh / off-win / hrs | 0.0002 / 0.0001 / 23 | 0.0002 / 0.0001 / 23 *(identical)* |
| `nyiso_gas_commitment_bridge × CC_REGULAR` p54574 | floored TWh | 0.0029 | **0.0021** |
| | off-window share | 0.0254 | **0.0172** |
| | binding hours | 89 | **70** |

The keeper's own 2024 D-4 also reads `passed=false` with **the same two plants**. The gap-fill
arm reduces the CC_REGULAR rider's off-window share by ~32 % and its binding hours by 19.
`d4_max_offwindow_share` is 0.05 and both rows are far below it in absolute terms
(0.0001, 0.0172); they fail on the *per-unit conduct* leg, not the share leg.

## 8. Did class energy move materially vs the keeper?

**No. The arm is a near-null on energy and a near-null on annual price.**

- Total P1 generation moves **−0.0020 TWh on 152.18 TWh (−0.0013 %)**.
- The largest single-class move is **ST_GAS +0.0334 TWh (+0.39 %)**; next is
  CC_REGULAR −0.0281 TWh (−0.076 %) and CC_CHP −0.0191 TWh (−0.098 %).
- **Nine of sixteen classes move by exactly 0.0000 TWh** — every zero-marginal-cost and
  budget-pinned class (nuclear, hydro, wind, solar, biomass, OTHER, import, both coals).
- Direction is coherent with the mechanism: raising the gas price on 5,880 previously-unpriced
  hours makes gas CC marginally *less* competitive (CC_REGULAR and CC_CHP down) and shifts a
  little energy onto ST_GAS and the CHP classes.
- Annual load-weighted price moves **+$0.075/MWh (+0.19 %)**, and the effect is carried by the
  **winter shoulder — Jan (+0.0562) and Nov (+0.0206) hour-weighted contributions, together
  103 % of the annual delta**, with December net −0.0066 despite a strong internal
  redistribution (§6).

**Bottom line for the parent:** the mechanism does what its own pre-solve arithmetic says — it
reprices the gap-filled winter days and nothing else. It is confined to the rows it claims,
its direction and order of magnitude match the zero-LP delta, it introduces **no new D-4
failure** (and shrinks one), and **no non-target criterion flips**. The screen's STOP conditions
are **not** triggered. Per rule 29 `[R-SCREEN]`, a screen may kill an arm but **may never
promote one** — this shard therefore reports a *not-killed* verdict and makes **no promotion
claim**; that decision is the owner's (rule 31 `[R-RETAIN]`).

---

### Retention notice (rule 31 `[R-RETAIN]`)

`results/calibration/nyiso223_gapfill_2024/` is on local disk, gitignored, **not deleted**.
This container is ephemeral — the bundle will **not survive session reclamation**. Every number
this shard will ever cite is in this document, per rule 29 `[R-SCREEN]` (c).
