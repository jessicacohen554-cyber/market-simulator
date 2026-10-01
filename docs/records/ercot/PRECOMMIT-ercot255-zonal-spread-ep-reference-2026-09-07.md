# PRE-COMMIT — ercot-255: the ERCOT zonal gas SPREAD is referenced to Henry Hub while the LEVEL it competes against is the EP series, so a statewide fuel event enters the merit order as false LOCATIONAL dispersion

> **Pushed BEFORE any solve** (rule 29 `[R-SCREEN]`). Every gate, the screen year,
> the control form and the 2021 predictions below are registered here so none of
> them can be written to fit a result. Phase 0 was **zero LP**: read-only
> reconstructions of the committed `ercot248_two_config_keeper` /
> `ercot253_2021_touchpoint` fleets plus direct reads of the committed input
> files. **ERCOT's determination is the train-tier verdict and is untouched** —
> `2026-09-05-ercot248-two-config-keeper`, CALIBRATED (rule 30(c)).

## 0. Which lever, and why this one

The charter offered two. **Lever B is taken.** The reasons are recorded before
the work, not after:

1. **C1 is what the 2021 rung actually fails on the load-bearing tier**, together
   with C3a and C3b (`frontend/data/backcast/registry/2026-09-07-ercot253-2021-rung.json`).
   Lever A's target, C3c, **already PASSES on that rung**, and under rubric v3.6
   a C3c miss on an out-of-training year is an auto-ledgered CAVEAT whatever else
   that year does (rule 30) — so Lever A cannot move a 2021 determination even if
   it works perfectly.
2. **`RESULT-ercot254` §4 named the zonal spread as the likelier C1 driver** after
   the monthly-EP level repair moved CC_REGULAR by +0.87 TWh of a 16 TWh miss and
   pushed CT_PEAKER and ST_GAS the wrong way.
3. **Lever A's data does not exist in a free, reproducible form.** Phase 0 swept
   the disk: `data/raw/gas-prices/` carries daily Henry Hub, Algonquin citygate,
   CAISO citygate, MISO citygate and Transco Z6 — and **no daily Waha, Houston
   Ship Channel or Katy series for ERCOT**. EIA publishes exactly one daily gas
   spot series (Henry Hub); its TX hub prints are monthly (`N3045TX3`,
   `N3050TX3`) or weekly narrative. `scripts/data/derive_ercot_zonal_gas_hub.py`
   states the same thing independently for the annual case: *"the Waha average is
   NOT derivable from an in-repo/API source."*
4. **Daily Henry Hub cannot substitute, and the matrix says so twice.** ERCOT
   already runs `gas_daily_shape` **as a keeper mechanism** (cell `K`,
   `docs/PRECOMMIT-ercot145-gas-daily-shape-2026-07-31.md`) — a mean-preserving
   daily HH staircase on the commodity. It cannot carry Uri because the February
   2021 basis is **additive and flat at +$54.4/MMBtu** while HH's own daily
   staircase peaks at ~4.5x a $5.35 month mean. And the two adjacent cells are
   already adjudicated `G` for ERCOT — `gas_monthly_actuals` rejected at Run-77
   (the ~20 %-coverage F923 reporter sample runs ~+$1/MMBtu above the merchant
   hub) and `gas_plant_monthly_fuel_pricing` off by measured design (~12 % of CC
   MW). Re-entering that family without new evidence is the DO-NOT-REDO the
   matrix protocol forbids (rule 28 `[R-MECH-MATRIX]` duty (a)).

Lever A therefore stands as a **data-intake question**, named in §7 and not
solved here. Lever B is solvable today from files already on disk.

## 1. The object — a REFERENCE mismatch, provable from the code and the inputs alone

`apply_ercot_zonal_gas_basis` composes a gas unit's delivered price from two
measured pieces:

```
delivered = HH_month + GAS_BASIS_DIFFERENTIAL(-0.50) + level_corr + zone_spread[z]
            level_corr = ep_basis - (-0.50)          # ep_basis = EP/1.036 - HH, ANNUAL
            zone_spread = raw[z] - capacity_weighted_mean(raw)
```

and the function's own docstring states the intent of that recentring: *"each
zone's EIA-923 basis minus its gas-capacity-weighted mean, so the spread moves
only the cross-zonal split and **the EIA-923 regulated-utility level bias is
dropped** — only its relative shape is kept."*

**That intent is not achieved, and cannot be, because only half the vector is on
the EIA-923 level.** `data/raw/ercot_zonal_gas_hub.csv` mixes two provenance
classes in one column:

| zone | 2021 row | what the number IS | group |
|---|---|---|---|
| North / Northeast | +6.12 | F923 Sch5 qty-weighted **delivered** price − HH | **F923** |
| South_Central | +6.30 | F923 Sch5 qty-weighted **delivered** price − HH | **F923** |
| South | +4.36 | F923 Sch5 qty-weighted **delivered** price − HH | **F923** |
| Houston | −0.15 | a cited **hub-vs-hub** constant (HSC ≈ HH − 0.15), never re-measured | CONV |
| West / Panhandle | *absent* | Waha annual − HH (no 2021 row) | CONV |

A F923 row carries **level + differential**. A convention row carries
**differential only**. Subtracting one capacity-weighted mean from that mixed
vector removes a *blend*, so the F923 group's level survives into the spread with
weight `1 − w923`, where `w923` is the F923 zones' share of ERCOT gas capacity.

**Measured, from the committed bundles' own fleets** (gas pmax is identical in
2021 and 2023–2025): `w923 = 39,835.785 / 59,889.530 = 0.66516`
(North 20,418.654 + Northeast 1,653.000 + South_Central 11,923.286 + South
5,840.845 MW; Houston 17,240.715, West 2,813.030, Panhandle 0).

The surviving level is `ep_basis`, and that is the whole story:

| year | `ep_basis` $/MMBtu | leak into the spread |
|---|---|---|
| 2021 | **+5.2779** | **the Uri statewide event, in full** |
| 2022 | −0.3010 | small |
| 2023 | +0.0045 | ~nil |
| 2024 | −0.0858 | small |
| 2025 | −0.4634 | small |

**The 2021 "cross-zonal dispersion" is therefore ~70 % common mode.** Within the
three measured zones the 2021 spread of the raw rows is 6.30 − 4.36 = **1.94**
$/MMBtu against 1.10 in 2023 — barely wider. The headline 6.45 $/MMBtu range
(`FINDING-ercot254` §1a) is produced almost entirely by three zones carrying a
statewide event that the other three, being conventions, do not.

**Rule 19 `[R-ONE-MECH]` is the charge:** the statewide delivered level is
carried TWICE — once, correctly, by `level_corr`, and again, differentially and
by accident, by the F923 rows.

### 1a. Phase-0 fidelity — the arithmetic reproduces the solves exactly

The reconstruction is not a model of the applier, it *is* the applier's
arithmetic, and it lands on the committed solve logs to the cent:

| year | log line | reconstructed |
|---|---|---|
| 2021 | `zonal spread -4.04..2.41` | −4.042 .. +2.408 |
| 2023 | `zonal spread -0.92..1.03` | −0.922 .. +1.028 |
| 2022 | `zonal spread -1.47..0.96` | −1.469 .. +0.961 |

The F923 receipt sample itself also reproduces exactly from the committed
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` under the derive
script's own plant→zone map: 2023 North **5 plants / 60,440,096**,
South_Central **12 / 172,081,116**, South **3 / 9,024,099**, against the
committed `source` strings' "5 plants 60M MMBtu", "12 plants 172M", "3 plants
9M". **Houston has 124 fleet gas plants and ZERO F923 cost-reporting plants**;
West has 22 and zero. The conventions are a real data gap, not a derivation
failure.

## 2. The repair — `ercot_zonal_spread_ep_referenced`, zero new data, zero free parameters

**Reference the F923 rows to the same series that carries the level.**

```
raw'[z] = raw[z] - ep_basis      for z in the F923 group
raw'[z] = raw[z]                 for z in the convention group
```

then everything downstream — haircut, delivered floor, the capacity-weighted
mean-zero recentring, the level term — is **untouched**. One seam, one line of
arithmetic, and it is the docstring's own stated intent actually executed.

Why this and not a weighted sample mean: because it needs **no weighting choice
at all**, and therefore carries **no free parameter** (rules 21 `[R-DOF]` / 24
`[R-REGISTRY]`). `ep_basis` is already loaded by this very function. And the
construction is an **identity**: for a F923 zone,

```
delivered = HH + ep_basis + (raw[z] - ep_basis) = HH + raw[z] = delivered_923[z]
```

up to the fleet-level recentring constant — a North CC ends up paying its own
measured North delivered price. That is a testable pre-solve gate (G-1), not a
claim.

**Group membership is read from the data's own provenance**, not hardcoded: a row
is F923 iff its `source` contains `EIA-923 Sch5`, or `proxy->North` (Northeast
inherits North's F923 row). Houston (`HSC ~ Henry Hub`), West (`Waha annual
avg`) and Panhandle (`proxy->Waha`) are conventions. Absent the `source` column
the mechanism fails closed to a no-op.

**Forward behaviour, rule 13 `[R-MEASURED]`:** a forecast year has no EP rows, so
`ercot_electric_power_gas_basis` returns `None`, the level term is already 0
there, and the arm is a **no-op by construction** — every forecast and every
non-ERCOT ISO is byte-identical. Default **off**, ERCOT-only.

**Rule 19 — the slot.** Nothing else in the ERCOT gas path re-references the
zonal rows. `ercot_ep_gas_basis_monthly` (ercot-254, built, default-off) acts on
the LEVEL's resolution and this acts on the SPREAD's reference; they are
independent and this arm is tested **alone**. `ercot_west_netload_gas_shape`
(keeper-armed) owns the West rows' level outright, which is why West is expected
exactly inert (G-1c below).

**Rule 23 `[R-FROZEN-DERIVE]` is not engaged:** no derive script runs, no
measured parameter is re-derived, and `data/raw/ercot_zonal_gas_hub.csv` is not
edited. This is a consumption-side construction fix.

## 3. Footprint, and the screen year named ON IT

Capacity-weighted mean |Δ zonal spread|, computed pre-solve from the committed
table and the committed fleets:

| year | `ep_basis` | **footprint $/MMBtu** | = $/MWh at CC hr 7.29 | spread range ctl → arm |
|---|---|---|---|---|
| 2023 | +0.0045 | **0.0020** | 0.015 | 1.950 → 1.946 |
| 2024 | −0.0858 | **0.0382** | 0.279 | 2.820 → 2.906 |
| **2025** | **−0.4634** | **0.2064** | **1.505** | 2.970 → **3.433** |
| *(2021)* | *+5.2779* | *2.3510* | *17.139* | *6.450 → **1.940*** |

**THE SCREEN YEAR IS 2025** — the training year in which this mechanism's own
measured footprint is largest (103× 2023, 5.4× 2024). It is named here, ex ante,
on the mechanism's footprint and **never on a residual** (rule 29). 2023 is
predicted near-inert and that is a *prediction*, not a convenience.

**The mechanism is not a 2021 fix and the table proves it.** `ep_basis` is
*negative* in every training year, so in-sample the arm **widens** the spread
range (2.970 → 3.433 in 2025) and it *narrows* it only in 2021. A construction
tuned to shrink 2021's dispersion would not widen 2025's. Per-zone Δ:

| zone | Δ 2025 | Δ 2021 |
|---|---|---|
| North / Northeast / South_Central / South | **+0.155** | **−1.767** |
| Houston | **−0.308** | **+3.511** |
| West / Panhandle | −0.308 (expected absorbed by the net-load step) | +3.511 (same) |

## 4. The screen gates — STRUCTURAL, STOP-only, and never read against C1

C1 is the target criterion. **It is not a gate in either direction** — reading it
as one is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids. The screen
may kill this arm; it may never promote it.

**Pre-solve, zero LP, on the reconstructed 2025 fleet:**

| gate | question | STOP bar |
|---|---|---|
| **G-1a** identity | every non-West gas row's Δ delivered fuel equals its zone's predicted constant (F923 +0.15517, Houston −0.30826) | any row off by > 1e-9 |
| **G-1b** F923 identity | a F923-zone unit's arm delivered price = `HH + raw[z]` + the recentring constant | > 1e-9 |
| **G-1c** West inertness | all West/Panhandle gas rows exactly 0.0 (owned by `ercot_west_netload_gas_shape`) | any nonzero |
| **G-2** confinement | non-gas rows Δ exactly 0 | any nonzero |
| **G-3** LEVEL NEUTRALITY | capacity-weighted mean delivered gas price is unchanged — the defining property of a pure redistribution | > 1e-6 $/MMBtu |
| **G-4** forward inertness | with the EP series absent the arm is a no-op | any delta |

**G-3 is the load-bearing structural gate.** If the fleet-aggregate gas level
moves at all, this is not the mechanism claimed and the arm dies there.

**Post-solve, 2025 arm vs a 2025 control ONE FLAG APART at the same HEAD
(G-CTRL form 2):**

| gate | STOP bar |
|---|---|
| **G-5** magnitude — Δ system load-weighted LMP | > $5.00/MWh |
| **G-6** non-target load-bearing — C2, C3a, C3b | any PASS → FAIL |
| **G-7** protective — C6, C8 | any flip |
| **G-8** shed — slack, dump | > 1.0 MWh in the arm |
| **G-9** direction | CT_PEAKER 2025 energy must **RISE** (its cap-weighted mc falls −2.52 $/MWh; §5) — a mechanism-behaviour check on the arm's own arithmetic, **not** a residual read | falls |

**G-CTRL.** A 2025 control is solved at this HEAD rather than differenced against
the committed keeper, because the keeper bundle's `git_sha` is `0207d69d` and
`RESULT-ercot254` §1 records that a hunk-by-hunk INERT classification of the
intervening diff (172 files, 153,004 insertions) **could not honestly be made**.
The control also re-measures HEAD drift at *this* HEAD — ercot-254 measured
+0.0293 $/MWh at theirs — and that measurement is what licenses **form 4 (the
committed bundles as control) for the full span and the 2021 re-test**, so
exactly one control solve is spent, not four.

## 5. Predictions, registered BEFORE any solve

Capacity-weighted per-class Δ delivered fuel and Δ marginal cost, from the 2021
fleet's class × zone gas capacity (F923 conv-share in brackets) — the class MW
table is `CC_REGULAR 33,120.0 / ST_GAS 12,596.9 / CT_PEAKER 7,485.2 /
CC_CHP 5,713.5 / CT_CHP 965.2 / ST_CHP 8.7`:

| class | conv share | Δ fuel 2025 | Δ mc 2025 | Δ fuel 2021 | Δ mc 2021 |
|---|---|---|---|---|---|
| CC_REGULAR | 0.193 | +0.066 | **+0.48** | −0.746 | **−5.44** |
| ST_GAS | 0.246 | +0.041 | **+0.49** | −0.470 | **−5.56** |
| CT_PEAKER | 0.651 | −0.146 | **−2.52** | +1.668 | **+28.68** |
| CC_CHP | 0.845 | −0.236 | **−2.16** | +2.695 | **+24.65** |
| CT_CHP | 0.873 | −0.245 | **−2.38** | +2.840 | **+27.63** |

**S-1 (screen, 2025).** CT_PEAKER and CC_CHP energy **RISE**; CC_REGULAR and
ST_GAS **fall slightly**; |Δ system LW LMP| < $2.00/MWh; no criterion flips.

**S-2 (2023).** Near-inert — |Δ system LW LMP| < $0.10/MWh, no criterion flips.

**The 2021 re-test** (touchpoint-loop step 4; run only if the screen clears and
only after the full span). Against `2026-09-07-ercot253-2021-rung`
(model vs `classFull` actual, TWh):

| # | prediction | run253 | actual |
|---|---|---|---|
| **P1** | **CT_PEAKER FALLS**, miss +5.996 shrinks (mc +28.68) | 10.6412 | 4.6456 |
| **P2** | **CC_REGULAR RISES**, miss −16.019 shrinks (mc −5.44) | 97.2256 | 113.2445 |
| **P3** | **CC_CHP FALLS**, miss +2.896 shrinks (mc +24.65) | 30.0272 | 27.1317 |
| **P4** | **ST_GAS RISES — ADVERSE.** It is already over-running and this makes it cheaper; its miss +4.761 **GROWS** | 17.1051 | 12.3438 |
| **P5** | **COAL is near-inert**, \|Δ COAL_PRB\| < 1.0 TWh — unlike ercot-254's level arm, this moves no fleet-aggregate gas level, so there is no coal-displacement channel | 58.9562 | 58.0638 |
| **P6** | **C3a barely moves**, \|Δ\| < 5 % of the +28.2 % bias — the arm is level-neutral by construction (G-3) | +28.2 % | — |
| **P7** | **C3c does not blow out** (the ercot-254 failure mode is a LEVEL effect; this arm has none) | 234 h, PASS | 258 h |
| **P8** | **The CT−CC mc spread widens $4.78 → ~$38.9**, i.e. close to 2023's $23.12 scaled by the fuel ratio 3.72/2.54 = **$33.9**, and NOT to 2023's raw value | $4.78 | — |

**P4 is registered as an expected adverse outcome**, and P1/P2/P3 are registered
as directional, not magnitude, claims. `RESULT-ercot254` §3a scored two of three
class predictions **wrong in sign** because its arithmetic ignored the coal
margin; P5 is this session's explicit answer to that lesson, and if P5 fails the
same blind spot is back.

**2021 cannot be fixed by this arm alone and that is stated up front.** The rung
fails C1, C3a and C3b. This arm is level-neutral, so C3a is not its object — the
C3a lever is ercot-254's `ercot_ep_gas_basis_monthly`, which stays default-off
and is **not** stacked here (rule 29: one mechanism per screen).

## 6. Governance

- **Rule 22 `[R-HOLDOUT]`.** Every parameter, the group partition, the screen
  year and the gates are identified on **2023–2025 and the input files only**.
  2021 is touched exactly once, as a **step-4 re-test** of an in-sample-identified
  repair, under ERCOT's `complete` marker (validation tier, outside the holdout
  freeze). Nothing is tuned to it. Predictions are committed above, upstream of
  the solve.
- **Rule 16 `[R-ALLYEARS]`.** The screen bundle is a throwaway diagnostic probe,
  never registered; the full span is one `--year 2023 2024 2025` invocation.
- **Rule 29(c).** The screen and control bundles are **deleted before merge**;
  this document and its RESULT carry every number the session will ever cite.
- **Rule 28 `[R-MECH-MATRIX]`.** A new row `ercot_zonal_spread_ep_referenced` is
  added to `docs/codebase-site/data/mechanism-matrix.js` with a cell line in
  every ISO shard, in the same PR (duty (c)).
- **Rule 27 `[R-PUSH]`.** Scope touches `src/market_sim/`; this session is Opus.
- **Rule 30(c).** A held-out year never downgrades the ISO. ERCOT stays
  CALIBRATED on the train tier whatever 2021 does.

## 7. Named and NOT taken here

* **Lever A (daily delivered basis)** — a genuine data-intake question (§0.3):
  daily Waha / HSC / Katy settlements are not on disk and not free from EIA.
  The honest next step is an intake charter, not a solve.
* **A measured Houston row.** The −0.15 constant is the arm's residual
  imprecision: it is a hub-vs-hub statement being read as a level-relative
  differential. In every training year |`ep_basis`| ≤ 0.46 so the two readings
  agree within $0.46; in 2021 they do not, and the arm's reading is the
  defensible one. A measured Houston basis would close it.
* **The absent 2021 West `neg_day_freq`** (falls back to a 2024 default of 0.42
  and inverts the regimes: deep $7.45 above firm $3.41).
* **The two provenance defects** of `FINDING-ercot254` §5, plus the merged
  two-config `meta.json` that cannot reproduce the 2023 carve-out.
