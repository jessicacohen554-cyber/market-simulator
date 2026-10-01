# RESULT — the 2025 SCREEN CLEARS EVERY GATE, and the mechanism's sign REVERSES between the screen year and 2021, which is the point (ercot-255)

> Scored against `docs/PRECOMMIT-ercot255-zonal-spread-ep-reference-2026-09-07.md`
> and its `docs/ADDENDUM-ercot255-g1c-correction-2026-09-07.md`, both pushed
> before any LP ran. All bundles are **deleted before merge** (rule 29
> `[R-SCREEN]` clause c); every number this session cites is in these three
> documents, and git history is the record for the bytes.
> **Rule 30(c): ERCOT's determination is the train-tier verdict and is UNCHANGED at
> CALIBRATED. The designated keeper is now `2026-09-07-ercot255-five-year-keeper`
> (owner instruction 2026-09-07; §5) — re-verified CALIBRATED on the train tier and
> on every designated span, identical to the ercot-248 incumbent it replaces.**

## 0. Bottom line

| | |
|---|---|
| **The defect** | **CONFIRMED, and it is a REFERENCE mismatch, not the February contamination the charter named.** §1 |
| **The 2025 screen** | **CLEARS EVERY GATE**, zero criterion flips, level-neutral to machine zero. §2 |
| **The training window** | **NEAR-INERT in 2024 and 2025** — every criterion PASS→PASS at the same values. §3 |
| **2021 C1 (the target)** | **FAIL → PASS.** CC_REGULAR's 16.02 TWh miss falls to **3.95**; all four gas classes improve 43–75 %. §4 |
| **2021 C3a / C3b** | both improve (+28.2 % → **+26.2 %**; 0.361 → **0.333**), both still FAIL. §4 |
| **2021 C3c** | **holds PASS** (234 → 230 h vs actual 258) — no blow-out. §4 |
| **The cost, reported at full magnitude** | **C8 ST_GAS 20.8 % → 37.6 % forced, PASS → FAIL.** §4c — and the arithmetic says the arm *revealed* this rather than caused it. |
| **Predictions** | 6 of 8 fully correct, 1 outside its registered band in the right direction, **1 WRONG IN SIGN**. §4b |
| **Keeper candidate?** | **PROMOTED** by owner ruling as ONE five-year run; train tier re-verifies CALIBRATED, identical to the incumbent. §5 |

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
| **G-7** protective (C6, C8) | **C8 PASS in both** (ST_GAS 20.2 % → 20.1 %, CC_REGULAR 1.4 % → 1.7 %, COAL 3.3 % → 3.2 %); C6 UNATTESTED in both | any flip | **PASS** — C8 on the merits, C6 by identity (a replay bundle writes no attestation) |
| **G-8** shed | slack **0.0000** and dump **0.0000** in both | > 1.0 MWh | **PASS** |
| **G-9** direction | **CT_PEAKER +0.8555 TWh — RISES** | falls | **PASS** |

**Every scored criterion is status-identical between arm and control** — 21
records across `fuelmix`, `sysvol`, `price_mean`, `price_shape`, `price_tail`,
`dispatch_corr`, `forced_share`, `governance`. C3a −7.8 % → −8.0 %, C3b 0.101 →
0.101, both PASS; C8 forced-share PASS on every scored class in both.

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

## 3. The training window — near-inert where it should be, and 2023 is CONFOUNDED exactly as ercot-254 recorded

Full span 2023–2025 in one bundle (rule 16), differenced against the committed
keeper (G-CTRL form 4, licensed by §2e):

| year | criterion | keeper | arm | reading |
|---|---|---|---|---|
| 2024 | C3a | PASS −0.2 % | PASS **−0.0 %** | inert |
| 2024 | C3b | PASS 0.131 | PASS **0.132** | inert |
| 2024 | C3c | 22 h | **22 h** | identical |
| 2024 | C1 (7 classes) | all PASS | all PASS | max class move 0.36 TWh |
| 2024 | C8 ST_GAS | PASS 15.2 % | PASS **15.3 %** | inert |
| 2025 | C3a | PASS −7.9 % | PASS **−8.0 %** | inert |
| 2025 | C3b | PASS 0.101 | PASS **0.101** | identical |
| 2025 | C3c | 1 h | **1 h** | identical |
| 2025 | C8 ST_GAS | PASS 20.2 % | PASS **20.1 %** | inert |

**Prediction S-2 (2023 near-inert) is confirmed at the level it can be**: the
mechanism's 2023 footprint is 0.0020 $/MMBtu because `ep_basis(2023) = +0.0045`,
and that value is a property of the measured input, **not of the config** — so
2023 inertness holds whichever config is applied.

**2023 is NOT otherwise interpretable, and the reason is a known provenance
defect, not this mechanism.** `replay_keeper` on the merged
`ercot248_two_config_keeper` applies the **FORWARD** config to every year (the
merged `meta.json` carries neither `ercot_offer_swcap_clip` nor the carve-out
CC `peak` band 151.008), so the arm's 2023 reads C3a **−39.7 %** and C3b
**0.730** — which are, to the decimal, the **ercot-234 forward-config-on-2023**
numbers the keeper's own matrix stamp records and that `RESULT-ercot254` §2
documented. A mechanism whose 2023 footprint is 0.0020 $/MMBtu cannot move C3a
by 32 points; the flip is the config, not the arm.

Two further keeper-vs-arm "flips" are **replay artifacts, not effects**:
`governance` PASS → UNATTESTED (a replay bundle writes no attestation), and
C3c 2024/2025 CAVEAT → FAIL at *identical magnitudes* (22 h and 1 h) because the
C3c standing rule requires governance to PASS — guard (b) working exactly as
rule 22 specifies.

## 4. The 2021 re-test — C1 flips FAIL → PASS

Touchpoint-loop **step 4**: a re-test of a repair identified entirely in-sample
and on the input files, against predictions committed upstream of the solve.
Differenced against the committed `2026-09-07-ercot253-2021-rung`.

### 4a. C1 — the load-bearing criterion this lever targeted

| class | actual | run253 | **re-test** | miss run253 | **miss re-test** | |
|---|---|---|---|---|---|---|
| **CC_REGULAR** | 113.2445 | 97.2256 | **109.2940** | **−16.0189** | **−3.9505** | **−75 %** |
| **CT_PEAKER** | 4.6456 | 10.6412 | **6.0428** | **+5.9956** | **+1.3972** | **−77 %** |
| **ST_GAS** | 12.3438 | 17.1051 | **11.1773** | **+4.7613** | **−1.1665** | **−75 %** |
| **CC_CHP** | 27.1317 | 30.0272 | **28.7864** | **+2.8955** | **+1.6547** | **−43 %** |
| COAL_PRB | 58.0638 | 58.9562 | 58.7024 | +0.8924 | +0.6386 | −28 % |
| COAL_LIGNITE | 16.4463 | 17.4486 | 17.4660 | +1.0023 | +1.0197 | flat |
| CT_CHP | 6.1294 | 5.3243 | 5.0447 | −0.8051 | −1.0847 | worse |

**C1 `fuelmix` flips FAIL → PASS** (run253 failed on CC_REGULAR at −16.02 TWh /
−4.0 pp; the arm reads −3.95 TWh / −0.9 pp, in band). **C2 `sysvol` gas** goes
from "PASS, C1 flags: CC_REGULAR" to "PASS all classes in band".

Prices, all on ONE basis — the hourly system load-weighted LMP recomputed from
each bundle's own `hourly/system_2021.parquet`, demand-weighted within month.
**This reproduces `RESULT-ercot254` §3's run253 column exactly** (Feb −4.1 %,
ex-Feb +160.8 %, annual +28.2 %), so the two sessions are comparable:

| | actual | run253 | **re-test** | err run253 | **err re-test** |
|---|---|---|---|---|---|
| **ex-Feb** | 34.15 | 89.05 | **85.04** | +160.8 % | **+149.0 %** |
| Feb (Uri) | 1521.84 | 1459.52 | 1470.80 | −4.1 % | **−3.4 %** |
| **annual (C3a)** | 148.19 | 189.97 | **187.09** | **+28.2 %** | **+26.2 %** |
| C3b NRMSE | — | 0.361 | **0.333** | — | improved |
| **C3c** h>$200 | 258 | 234 (**PASS**) | **230 (PASS)** | — | **holds** |

**Every one of the twelve months improves**, C3a and C3b both improve, and C3c
does **not** blow out — the contrast with ercot-254's 234 → 688 h is the whole
point: that was a LEVEL effect, and this arm has none (G-3).

### 4b. Prediction scorecard — reported at full magnitude, hits and misses alike

| # | registered prediction | measured | verdict |
|---|---|---|---|
| **P1** | CT_PEAKER FALLS, miss +5.996 shrinks | 10.641 → **6.043**, miss **+1.397** | **CORRECT** |
| **P2** | CC_REGULAR RISES, miss −16.019 shrinks | 97.226 → **109.294**, miss **−3.951** | **CORRECT** |
| **P3** | CC_CHP FALLS, miss +2.896 shrinks | 30.027 → **28.786**, miss **+1.655** | **CORRECT** |
| **P4** | **ST_GAS RISES — registered as ADVERSE** | 17.105 → **11.177 — it FELL** | **WRONG IN SIGN** |
| **P5** | COAL near-inert, \|Δ COAL_PRB\| < 1.0 TWh | **−0.2537 TWh** | **CORRECT** |
| **P6** | C3a barely moves, \|Δ\| < 5 % of the +28.2 % bias | **2.0 pts = 7.1 %** | direction right, **magnitude outside the registered band** |
| **P7** | C3c does not blow out | **234 → 230 h, PASS held** | **CORRECT** |
| **P8** | CT−CC mc spread → ~$33.9 (2023's scaled by the fuel ratio) | **16.73 → 33.19 $/MWh** | **CORRECT, within $0.71** |

**P4 was wrong, and it was wrong in my favour, which is the kind that needs
saying loudest.** I registered ST_GAS as an expected *adverse* outcome: its
convention-zone share is 0.246, so the arm makes it $5.56/MWh cheaper and I
reasoned it would run more. It ran **5.93 TWh less**. The error is the mirror of
the one `RESULT-ercot254` §3a diagnosed in itself: I reasoned about each class's
own marginal cost in isolation and ignored the **competition for the freed
energy**. CC_REGULAR and ST_GAS got near-identical relief ($5.44 vs $5.56/MWh),
but CT_PEAKER's +28.68 displacement freed ~4.6 TWh into a 33 GW CC fleet with
16 TWh of headroom — so CC absorbed the freed energy *and* took ST_GAS's marginal
hours as well. The lesson generalises: a class's response is set by its position
relative to the units that can absorb the same MWh, not by its own Δmc.

**P8's basis, stated so it is not overread.** `FINDING-ercot254` §3 quotes the
2021 CT−CC spread as $4.78 on a *delivered-fuel × class heat-rate* construction;
the $16.73 → $33.19 above is the capacity-weighted p50 of each bundle's own
`mc_base` array — a different statistic of the same object. The registered target
(~$33.9) was hit on the basis it was measured on.

### 4c. THE COST — C8 forced-share flips PASS → FAIL on ST_GAS, and the arithmetic says the arm REVEALED it

| | forced TWh | model TWh | **forced share** | forced ÷ **ACTUAL** (12.3438) |
|---|---|---|---|---|
| run253 | 3.5618 | 17.1051 | **20.8 % PASS** | 28.9 % |
| **re-test** | **4.2050** | **11.1773** | **37.6 % FAIL** | **34.1 %** |

This is a **protective** criterion and it is reported without softening. But the
decomposition is the finding, not an excuse:

* The ST_GAS net-load drag floor is `clip(0.00906·netGW − 0.1376, 0, 0.34)`
  × capacity — **a function of net load alone**, so the floor's MW are *identical*
  in both arms. Forced volume rose only **+0.6432 TWh** while class energy fell
  **−5.9278 TWh**; the share moved because the **denominator collapsed**.
* **At the measured 2021 ST_GAS volume the floor is over budget either way**:
  4.2050 ÷ 12.3438 actual = **34.1 %**, above the 30 % cap. run253 sat at 28.9 %
  of actual only because its ST_GAS was over-running by **+38.6 %**.
* So the honest reading is that **run253 passed C8 on ST_GAS because the class
  was inflated**, and repairing the merit order removed the inflation that was
  hiding an over-budget floor. That is precisely the signal rule 16
  `[R-FORCED-BUDGET]` exists to raise — "floors are commitment scaffolding, not
  the dispatch model."
* It does **not** clear itself: ST_GAS is material (12.34 TWh ≈ 3.2 % of ERCOT
  load), so rule 16's escalation to a conditional pass on **provenance + shape**
  applies and would need a cited `D4_WINDOWS` entry for the drag floor plus a
  passing D-1 profile. Neither exists today. **It is an open item, named in §6.**

Also reported: 2021 slack rises **1,113.99 → 1,763.96 MWh** (dump 0.0000 in
both) — +650 MWh on a ~380 TWh year, in the one year ERCOT genuinely shed load.

## 5. Disposition — **PROMOTED** by owner ruling, as ONE five-year run

> **SUPERSEDED 2026-09-07 by owner instruction**, verbatim: *"Leave the 2023 results
> be as they are under a different config. Promote the combined result of
> 2021-22-24-25 along with the 23 config as a single run on the dashboards. 23 was
> an outlier year with weird market design."* This section's original recommendation
> — NOT promoted — is preserved below as §5a because the reasoning that produced it
> is part of the record, and because **its stated blocker was answered rather than
> waived**: the merged `meta.json` could not reproduce the 2023 carve-out, so the
> promotion does not ask it to. 2023 is copied byte-for-byte from the committed
> ercot-248 composite, exactly as ercot-248 itself composed its two configs.

**The designated ERCOT keeper is now `2026-09-07-ercot255-five-year-keeper`**, one
run spanning 2021–2025:

| span | config | determination |
|---|---|---|
| 2024, 2025 | forward + EP reference | **CALIBRATED** |
| 2023 | carve-out, **UNCHANGED**, byte-for-byte from ercot-248 | **CALIBRATED** |
| **train {2023, 2024, 2025}** | — | **CALIBRATED** |
| 2022 | carve-out recipe + EP reference (**validation**) | CALIBRATED-WITH-CAVEATS |
| 2021 | carve-out recipe + EP reference (**validation**) | NOT-YET |

**Rule 22 D-5(b) re-verification PASSES.** Recomputed from committed artifacts with
no solve, the new keeper reads **CALIBRATED** on the train tier and on each
designated span — **identical to the ercot-248 incumbent on all three**. A promotion
whose re-verified determination were *worse* would have stopped here; it is not.

**Rule 30(c) governs the two held-out rungs**: they are REPORTED at full magnitude
on the keeper's panel and the status page's per-year ladder, and they move the ISO
headline in neither direction. ERCOT stays **CALIBRATED** on the train-tier verdict.

**Two scorer-path repairs this promotion required**, both narrow and both rule-30(c)
citations rather than judgement calls — a `config_partition` may now designate a
HELD-OUT span, which neither surface anticipated:

* `scripts/build_status.py` — the "worst config determination over the designated
  spans" fold now runs over **train-tier configs only**; held-out configs are still
  scored and rendered, but cannot decertify the ISO.
* `scripts/audit_keepers.py` — the same filter in M1b's partition rollup, fail-closed
  (a partition with no train-tier config falls back to the plain single-run compare).

A config without a `tier` field defaults to `train`, so **every other ISO's rollup and
status part is byte-identical** — verified by rebuilding all six and finding only
timestamp deltas, which were reverted.

### 5a. The original recommendation, preserved



**The merits are strong**, and stronger than ercot-254's:

1. **A code-level construction defect, provable without any solve** — the
   applier's own documented intent is unachievable while half the vector sits on
   a different reference. Zero new data, zero free parameters, zero weighting
   choice, and level-neutral to machine zero.
2. **In-sample it costs nothing** — 2024 and 2025 are inert on every criterion.
3. **On the validation rung it fixes a load-bearing criterion**, C1 FAIL → PASS,
   with C3a, C3b and C3c all moving the right way or holding.
4. **Its sign reverses between the screen year and 2021** (§2d), so it cannot be
   a 2021 fit.

**What blocks a promotion is a provenance defect, not a result.** The merged
two-config `meta.json` cannot reproduce the 2023 carve-out (§3), so **rule 16
`[R-ALLYEARS]` cannot be satisfied from that bundle** — promoting this arm would
silently drop the keeper's 2023 carve-out config. That is the identical blocker
`RESULT-ercot254` §5 hit, it is now blocking a second consecutive mechanism, and
**it should be fixed before any further ERCOT promotion is attempted.**

Two further reasons a promotion would be wrong *today*, independent of that:

* **Rule 22 forbids banking the 2021 gain.** A validation rung is iterable
  model-SELECTION evidence and can neither certify nor decertify (rule 30(c));
  the in-sample window shows no gain to bank because the mechanism is inert
  there.
* **The C8 ST_GAS breach is unadjudicated** (§4c). It needs the D-4 window
  evidence rule 16 requires, and that is a separate piece of work.

**Recommendation (SUPERSEDED — the owner ruled promote; see §5): keep
`ercot_zonal_spread_ep_referenced` BUILT and default-OFF** … *It is one CLI switch
from a promotion A/B.* — which is exactly what the owner then called for. The
mechanism is now **armed on the designated keeper** in 2021/2022/2024/2025, and the
matrix cell reads **`K`**.

## 6. Named, and NOT taken here

* **The two-config `meta.json` provenance defect is ANSWERED FOR THIS PROMOTION,
  not fixed.** The five-year keeper composes 2023 byte-for-byte from the committed
  ercot-248 bundle rather than asking `replay_keeper` to reproduce it, so rule 16 is
  satisfied by composition. `replay_keeper` on the merged bundle still applies the
  forward config to 2023, so the defect is live for anything that replays it: It has blocked ercot-254 and ercot-255 in succession. The
  merged bundle records neither `ercot_offer_swcap_clip` nor the carve-out
  CC_REGULAR `peak` band 151.008, so `replay_keeper` applies the forward config to
  2023 and rule 16 is unsatisfiable from it. **Fix this before the next ERCOT
  keeper attempt.**
* **The ST_GAS net-load drag floor is over budget at the correct 2021 dispatch
  volume** (§4c) — 34.1 % of the measured class energy, above the 30 % cap,
  independent of this arm. Needs a cited `D4_WINDOWS` entry and a D-1 shape check.
* **A measured Houston row.** The −0.15 constant is this arm's residual
  imprecision — a hub-vs-hub statement read as a level-relative differential. In
  every training year |`ep_basis`| ≤ 0.46 so the readings agree within $0.46; in
  2021 they do not, and the arm's is the defensible one.
* **The arm removes the statewide LEVEL, not the EIA-923 sample bias.** What
  remains in a F923 row after referencing is (923 regulated-utility bias +
  locational), and the existing recentring handles that blend exactly as well —
  or badly — as it always did. Stated so the claim is not overread.
* **Lever A, a daily delivered-gas basis** — a genuine data-intake charter (§0.3
  of the PRECOMMIT): daily Waha / HSC / Katy settlements are not on disk and not
  free from EIA, and the adjacent cells are already adjudicated `G` for ERCOT.
* **The absent 2021 West `neg_day_freq`** (2024 default 0.42, inverted regimes:
  deep $7.45 above firm $3.41), and the `prb_overrides` provenance defect of
  `FINDING-ercot254` §5.
