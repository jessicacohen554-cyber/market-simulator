# RESULT — the 2025 SCREEN CLEARS EVERY GATE, and the mechanism's sign REVERSES between the screen year and 2021, which is the point (ercot-255)

> Scored against `docs/PRECOMMIT-ercot255-zonal-spread-ep-reference-2026-09-07.md`
> and its `docs/ADDENDUM-ercot255-g1c-correction-2026-09-07.md`, both pushed
> before any LP ran. All bundles are **deleted before merge** (rule 29
> `[R-SCREEN]` clause c); every number this session cites is in these three
> documents, and git history is the record for the bytes.
> **Rule 30(c): ERCOT's determination is the train-tier verdict and is
> untouched — CALIBRATED on `2026-09-05-ercot248-two-config-keeper`.**

*(Sections 3-5 — the training window, the 2021 re-test against the eight
pre-registered predictions, and the disposition — are appended when those solves
land. Nothing below is provisional.)*

## 1. Phase 0 (zero LP) — the object, and why it is not the object the charter named

The charter pointed at the 2021 per-zone rows' February contamination. They are
contaminated, but **that is not what breaks the merit order**: within the three
EIA-923-measured zones the 2021 raw spread is **1.94 $/MMBtu** against 1.10 in
2023 — barely wider. The headline 6.45 $/MMBtu range comes from somewhere else.

`data/raw/ercot_zonal_gas_hub.csv` **mixes two provenance classes in one
column**, and they are not commensurable:

| group | zones | what the number is |
|---|---|---|
| **F923** | North, Northeast, South_Central, South | EIA-923 Sch5 qty-weighted **delivered** price − HH = statewide **LEVEL + differential** |
| **convention** | Houston, West, Panhandle | cited hub-vs-hub constants = **differential only** |

`apply_ercot_zonal_gas_basis` recentres the combined vector on its
gas-capacity-weighted mean, and its own docstring calls that dropping *"the
EIA-923 regulated-utility level bias … only its relative shape is kept."* **It
cannot.** One mean over a mixed vector removes a *blend*, so the F923 group's
level survives into the SPREAD with weight `1 − w923 = 0.33484`, where
`w923 = 39,835.785 / 59,889.530 = 0.66516` is the F923 zones' share of ERCOT gas
capacity (measured on the committed bundles' own fleets; the gas pmax vector is
identical in 2021 and 2023–2025).

The surviving term is **`ep_basis` itself — the same statewide quantity
`level_corr` already carries in full.** One phenomenon, two mechanisms (rule 19
`[R-ONE-MECH]`). It is ~nil in the training years and **+5.2779 $/MMBtu in
2021**, so Winter Storm Uri enters the merit order as false **locational**
dispersion.

**Phase-0 fidelity.** The reconstruction is the applier's own arithmetic and it
lands on the committed solve logs to the cent — 2021 `−4.04..2.41` reproduces as
−4.042..+2.408, 2023 `−0.92..1.03` as −0.922..+1.028, 2022 `−1.47..0.96` as
−1.469..+0.961. The F923 receipt sample reproduces exactly from the committed
`eia923_monthly_fuel_costs.parquet` under the derive script's own plant→zone map
(2023 North **5 plants / 60,440,096**, South_Central **12 / 172,081,116**,
South **3 / 9,024,099**). **Houston has 124 fleet gas plants and ZERO F923 cost
reporters**; West has 22 and zero — the conventions are a real data gap, not a
derivation failure.

## 2. The 2025 screen — EVERY GATE PASSES

Screen year named ex ante on the mechanism's own footprint (0.1919 $/MMBtu, 96×
2023's and 5× 2024's), never on a residual.

### 2a. Pre-solve, zero LP

| gate | 2023 | **2025 (screen)** | 2021 | bar | verdict |
|---|---|---|---|---|---|
| **G-1a** per-zone Δ is ONE exact constant | 0.00e+00 | **≤ 8.88e-16** | ≤ 1.78e-15 | > 1e-9 | **PASS** |
| — F923 zones | −0.001502 | **+0.155170** | −1.767281 | — | reproduces the registered prediction to 6 dp |
| — convention zones | +0.002984 | **−0.308237** | +3.510617 | — | same |
| **G-2** non-gas confinement | 0.000e+00 | **0.000e+00** | 0.000e+00 | any nonzero | **PASS** |
| **G-3** LEVEL NEUTRALITY at the mechanism's seam | −5.5e-17 | **−1.9e-17** | −4.9e-16 | > 1e-9 | **PASS (machine zero)** |
| **G-3b** residual after the keeper's West step | −5.5e-17 | +1.448e-02 | −4.3e-16 | reported | attributed in full |
| **G-4** forward inertness | — | — | — | any delta | **PASS** (unit test) |

**G-3 is the load-bearing structural gate and it passes exactly.** The arm is a
pure redistribution: the capacity-weighted mean delivered gas price does not
move, in any year, to machine precision. G-3b's 2025 residual is West's absorbed
share to five decimals — West is 2,813.03/59,889.53 = 4.697 % of gas capacity and
its intended Δ was −0.308237, and 0.308237 × 0.04697 = **+0.01448** — absorbed by
`ercot_west_netload_gas_shape`'s own delivered floor, which binds in BOTH arms.
Nothing is unexplained.

### 2b. Post-solve, arm vs a same-HEAD control ONE FLAG APART (G-CTRL form 2)

| gate | measured | STOP bar | verdict |
|---|---|---|---|
| **G-5** magnitude, Δ system LW LMP | **−0.0477 $/MWh** (33.4425 → 33.3948) | > $5.00 | **PASS** |
| **G-6** non-target load-bearing (C2, C3a, C3b) | **zero status flips** | any PASS→FAIL | **PASS** |
| **G-7** protective (C6, C8) | C6 UNATTESTED in both, C8 SKIPPED in both | any flip | **PASS** (by identity — a replay bundle writes no attestation) |
| **G-8** shed | slack **0.0000** and dump **0.0000** in both | > 1.0 MWh | **PASS** |
| **G-9** direction | **CT_PEAKER +0.8555 TWh — RISES** | falls | **PASS** |

**Every scored criterion is status-identical between arm and control** — 18
records across `fuelmix`, `sysvol`, `price_mean`, `price_shape`, `price_tail`,
`dispatch_corr`, `forced_share`, `governance`. C3a −7.8 % → −8.0 %, C3b 0.101 →
0.101, both PASS.

### 2c. S-1 was CORRECT ON ALL FIVE CLASSES

Registered pre-solve from each class's convention-zone capacity share:

| class | conv share | predicted Δmc 2025 | **measured Δ energy** | registered as | verdict |
|---|---|---|---|---|---|
| CT_PEAKER | 0.651 | −2.52 $/MWh | **+0.8555 TWh** | RISES | **correct** |
| CC_CHP | 0.845 | −2.16 | **+0.4888** | RISES | **correct** |
| CT_CHP | 0.873 | −2.38 | **+0.0820** | RISES | **correct** |
| CC_REGULAR | 0.193 | +0.48 | **−1.7576** | falls | **correct** |
| ST_GAS | 0.246 | +0.49 | **−0.0173** | falls | **correct** |

**And COAL_PRB moves only +0.2965 TWh** — the in-sample analogue of prediction
P5. Unlike ercot-254's level arm, this one changes no fleet-aggregate gas price
(G-3), so there is no coal-displacement channel. That is the specific blind spot
`RESULT-ercot254` §3a diagnosed in its own arithmetic, and it is closed here by
construction rather than by hope.

### 2d. The sign REVERSES between the screen year and 2021 — the strongest evidence it is not a 2021 fix

`ep_basis` is **negative** in every training year and strongly positive in 2021,
so the mechanism pushes the two groups in **opposite directions** in the two
regimes:

| | 2025 (screen) | 2021 |
|---|---|---|
| F923 zones | **+0.155** | **−1.767** |
| Houston / West | **−0.308** | **+3.511** |
| CT_PEAKER | **energy RISES** | energy predicted to FALL |
| spread range | 2.970 → **3.433 (WIDENS)** | 6.450 → **1.940 (collapses)** |

A construction tuned to shrink 2021's dispersion would not widen 2025's. Rule 1
`[R-STRUCT]` is satisfied on the mechanism's own behaviour, not on assertion.

## 2e. G-CTRL — one control solve, and it licenses form 4 for the rest

The 2025 control measures HEAD drift against the committed keeper at
**+0.0293 $/MWh** on the system load-weighted LMP (keeper 33.4132 → control
33.4425; slack, dump and the >$200 hour count identical). That is **the same
value to four decimals that `RESULT-ercot254` §1 measured at a different HEAD**,
a day of merges to `main` earlier — so the drift is not merely small, it is
*stable*. It is 0.6× the arm's own −0.0477 and three orders below the $5.00 bar.
Form 4 (the committed bundles as control) is therefore licensed **empirically at
this HEAD** for the full span and the 2021 re-test, and exactly one control solve
is spent instead of four.

## 3. Governance

Pre-registered before the solve; the screen gate is STOP-only and **C1, the
target criterion, is not a gate in either direction**. No parameter was
identified on, fitted to, or selected against any out-of-training year. Nothing
is registered, no dashboard entry moves, and no keeper changes.

**One correction the gates themselves caught, before any LP ran.** PRECOMMIT §4's
G-1c asserted West would be exactly inert, transcribed from `RESULT-ercot254`
§1's G-1″. That is **ercot-254's** arm's property, not this one's:
`apply_ercot_west_netload_gas_shape` is annual-**mean**-preserving, so their
within-year relocation left `p_mean` untouched while this arm moves it by
construction. Corrected in a pushed addendum before the screen solved, with G-3
split into the mechanism's own seam (gated, machine zero) and the post-step
residual (reported, fully attributed).
