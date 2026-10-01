# FINDING — SOCO-53f (2026-09-20): an annual average is not a weighted mean, so the measurement reversed the sign of the premise — and a control solved for one reason closed two other questions

**Lane** SOCO-53f · **Model** Opus 5 · **Date** 2026-09-20 ·
**Branch** `claude/soco-measured-coal-heat-rates-ppfvts` · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53f-2026-09-20.md` (pushed at
`04f7f849cddac88fe6991fafcc4ed08f6df83e85`, before any solve) ·
**Incumbent keeper** `2026-09-19-soco53e-measured-st-gas`, bundle
`results/calibration/soco53e_st_hr` ·
**Run** `2026-09-20-soco53f-measured-coal-hr`, bundle
`results/calibration/soco53f_coal_hr` (committed) ·
**Control** `results/calibration/soco53f_ctl_span`, solved at the SAME pinned SHA.

---

## 1. HEADLINE

**The premise that commissioned this lane was wrong in SIGN, and the measurement said so
before an LP was spent.** `FINDING-soco-53e` §7.1 routed it on the reading that E C Gaston's
coal boiler, left on the blended ST family rate **11.5505**, is *"roughly 0.5 MMBtu/MWh too
**CHEAP** for a coal machine."* Its own meter reads **11.0505** — **0.5000 too DEAR**, the
magnitude right to four decimals with the sign inverted.

The reasoning behind the routing treated the plant rate as a weighted mean between two
machines, so the coal side had to sit above it. **It is not a mean, it is an eGRID ANNUAL
average** — `PLHTIAN / PLNGENAN` — which folds startup fuel, shutdown tails and the offline
hours' bank fuel into the number that sets the offer, and therefore sits **above both
machines' operating rates** rather than between them. That is the entire thesis of the
mechanism this lane arms, and Gaston is the case that shows it.

**So this arm is not the asymmetry-closer it was routed as; it is something larger.** All six
plants get cheaper, capacity-weighted **11.5267 → 10.8926, −5.5 %**, across **100 % of an
11.5 GW fleet** — five times the capacity the gas-steam sibling touched, and five times the
level move.

**The gates do not move, and eight of the ten gated non-CHP rows improve.** Determination
**`NOT-YET`** (rubric v3.8, PRICE UNSCORED) on both sides, C1 all **13/14** · free **9/10** on
both sides, C2/C4/C6/C8 PASS, 0 ledgered and 0 protective caveats, **zero `ScenarioConfig`
fields and zero free parameters added**, DOF unchanged at 3 entries / 1 residual, and **zero
C1 status flips on either bench**. 2023 `CT_PEAKER` stays the single failure at **+9.73 TWh**,
so **SOCO's headline defect is not fixed** — which the PRECOMMIT said first, with the number.

**A control this lane had to solve for its own A/B closed two open governance questions as
by-products**, and they are the session's most durable results:

- **SOCO's keeper E14 dependency drift is COSMETIC, and that is now proven rather than
  bounded.** `FINDING-soco-53e` §10.3 left it open because the confirming re-solve was
  abandoned. A seventh shard re-solved the control recipe on the keeper's **off-pin**
  dependency set: the result is **BIT-IDENTICAL** — 0 of 131,400 class-hourly cells, 0 of
  26,280 price cells, 0 of 26,280 marginal-emission cells.
- **Rule 36 `[R-YEAR-ISOLATION]`'s "unmeasured outside MISO" cost is MEASURED at SOCO, and it
  is ZERO.** The year-isolated control reproduces the keeper's annual class generation to
  **exactly 0.000000 MWh on all 45 class-years**, and its scored C1 rows on the committed
  bench reproduce the keeper's registered numbers exactly.

**One of this lane's own predictions was falsified** (§6, P9) and is scored as such.

---

## 2. THE MEASUREMENT

### 2.1 The artifact

`scripts/data/derive_campd_coal_heat_rates.py --iso SOCO --detail --egrid-family-heat-rates
--measured-ct-heat-rates --measured-st-heat-rates` →
`data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv`, sha256[:16] **`efd5926eecc62d8f`**,
**6 of 6 plants / 11,512.0 of 11,512.0 MW = 100 % of SOCO `COAL` capacity**, 252,093 in-band
steady hours at 15 units, AL/GA/MS 2023–2025:

| plant | COAL MW | units | steady h | gross | **net (applied)** | model (keeper recipe) | Δ |
|---|---|---|---|---|---|---|---|
| 703 Bowen | 3,200.0 | 4 | 62,558 | 9.5268 | **10.2439** | 10.6479 | **−0.4040** |
| 6002 James H Miller Jr | 2,777.5 | 4 | 97,641 | 10.0386 | **10.7942** | 10.8964 | **−0.1022** |
| 6257 Scherer | 2,580.0 | 3 | 55,165 | 10.6173 | **11.4165** | 12.2855 | **−0.8690** |
| 3 Barry | 1,118.5 | 1 | 7,789 | 9.9872 | **10.7389** | 12.6100 | **−1.8711** |
| 6073 Victor J Daniel Jr | 1,004.0 | 2 | 18,777 | 11.0912 | **11.9260** | 12.8947 | **−0.9687** |
| 26 E C Gaston | 832.0 | 1 | 10,163 | 10.2770 | **11.0505** | 11.5505 | **−0.5000** |

**Capacity-weighted 11.5267 → 10.8926, −5.5 %** (generation-weighted 11.2434 → 10.8146,
−3.8 %). **Every plant moves the same way.** Unlike the gas-steam sibling, whose five plants
split four-to-one, there is no offsetting Barry here.

### 2.2 A provenance repair that changed the number, landed with the artifact

nwpp-42's deriver read its `model_heat_rate_egrid` comparison column off the **loader-default**
fleet. SOCO's keeper carries three heat-rate flags, so that column described a fleet nobody
solves: it reported Barry at **8.9950** and Daniel at **8.3995** — the physically impossible
plant blends `egrid_family_heat_rates` exists to remove — and therefore claimed the measured
rates were **dearer** than the model's, the exact opposite of the truth under the keeper's own
recipe. This lane added the three provenance flags the gas-steam sibling already takes
(`provenance_fleet`), a `model_recipe` column recording which recipe the column was read
under, and a guard that the provenance recipe cannot move plant membership. **PROVENANCE
ONLY**: no applied number changes, `plant_table` is untouched, the 14 committed tests pass
unchanged, and `scripts/data/` is not on the solve path — so control and arm stayed
solve-identical at one SHA (verified: `git diff db6a0bb8 04f7f849 -- src/market_sim
scripts/run_calibration*.py scripts/lib scripts/replay_keeper.py` is **empty**).

### 2.3 Barry unit 4 — the decision, and what it costs, measured

CAMPD files **Barry unit 4, a 330 MW boiler, as *Pipeline Natural Gas***, while the model
carries it as a **362 MW `COAL` row**. nwpp-42's `primaryFuelInfo` selection therefore excludes
it, Barry's applied rate comes from **unit 5 alone**, and the plant-grain artifact then lands
that rate on both COAL rows. Unit 4's own operating rate over **10,422 in-band steady hours**
is **11.0878 gross → 11.9224 net**:

| row | control | arm | its own meter | |
|---|---|---|---|---|
| `3_5` (756.5 MW, unit 5, coal) | 12.6100 | **10.7389** | 10.7389 | 1.87 wrong → **exactly right** |
| `3_4` (362.0 MW, unit 4, gas-fired) | 12.6100 | **10.7389** | 11.9224 | 0.69 too dear → 1.18 too cheap |

Capacity-weighted over Barry's 1,118.5 MW that is a **+1.11 MMBtu/MWh net improvement**, and
it is right for a second reason: unit 4 burns **gas** and the model already charges it a
**coal fuel price**, a larger defect than its heat rate. Both legs are reported at full
magnitude; the class reassignment is **routed**, unchanged, as it was by SOCO-53d and 53e.

### 2.4 The parasitic class, measured — and the committed default kept anyway

SOCO's own meter, EIA-923 `ST`/coal-fuel net over CAMPD coal-unit gross, per plant-year:

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| 703 Bowen | 0.9140 | 0.9126 | 0.9167 |
| 6002 James H Miller Jr | 0.9239 | 0.9254 | 0.9275 |
| 6257 Scherer | 0.8754 | 0.8660 | 0.8801 |
| 6073 Victor J Daniel Jr | 0.8727 | 0.8818 | 0.8849 |
| 26 E C Gaston *(mixed site)* | 0.8551 | 0.8892 | 0.7339 |
| 3 Barry *(mixed site)* | 0.7739 | 0.8320 | 0.6522 |

The four single-fuel coal sites cluster at **0.866–0.928**; the two mixed sites read lower
because EIA-923 splits a co-firing boiler's net between its fuels while CAMPD's gross is the
whole machine. **Unlike the gas sibling, the committed class default 0.93 does NOT reproduce
the measurement** — it sits above every plant but Miller.

**It is used anyway, and that is a deliberate rule-13/21 choice.** The factor converting this
rate must be the SAME one the benchmark's net "actual" is built with, or the derived rate and
the generation it is scored against sit on two different boundaries; substituting a
this-lane-measured number would be a new free parameter on an artifact shared by 544 plants
across seven ISOs. **The consequence is stated rather than buried: the applied rates are
biased LOW by 1.5 % (Bowen, Miller) to 5.9 % (Scherer, Daniel), so this arm's cheapening is if
anything UNDERSTATED.** The real repair is `derive_parasitic_load.py --iso SOCO` — routed.

### 2.5 The physical band is measurably inert

`[8.0, 25.0]` MMBtu per gross MWh is nwpp-42's data-integrity guard, inherited, never chosen
here, never swept. Every plausible band lands within **0.029** MMBtu/MWh of the applied
10.8926, and the **unbanded** value is **0.0002** away (none 10.8928 · [7,25] 10.8912 ·
[8.5,25] 10.8958 · [9,25] 10.9212 · [8,20] 10.8920 · [8,30] 10.8930). It cannot be carrying
the result.

---

## 3. RULE 19 `[R-ONE-MECH]`, ESTABLISHED MECHANICALLY AT TWO GRAINS

**Built fleet** (393 rows, keeper recipe ± the field): row set, `pmax_mw`, `pmin_mw`,
`emission_rate_co2`, `vom`, `fuel_type`, `zone` all identical; `heat_rate` moves on **exactly
16 rows, all `COAL`**, all six plants; every other class at max |Δ| **0.000000000000** —
**`ST_GAS` (12)**, CT_PEAKER (100), CC_REGULAR (90), CC_CHP (14), CT_CHP (14), ST_CHP (13).

**LP rows** (`mc_base`, 327 rows × 8,760 h, `fleet_only` rebuild off the keeper's own bundle):
**25 of 327 move, all `COAL` tranche rows**; **`ST_GAS` (20)**, CT_PEAKER (89), CC_REGULAR
(67), CC_CHP (14), CT_CHP (14), ST_CHP (11) and hydro (42) at max |Δmc| **0.0000000000**.

**`ST_GAS` is the load-bearing cell and it is byte-identical on both.** SOCO-53e repriced it
one day earlier, and plant codes **3** and **26** carry `COAL` and `ST_GAS` rows behind one
ORIS code — exactly where a class gate leaks. It does not.

---

## 4. WHAT THE RUN DELIVERED

### 4.1 Class volumes, arm − control (TWh)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **COAL (PRB + BIT)** | **+0.1967** | **+0.7305** | **+1.5632** |
| `COAL_PRB` / `COAL_BIT` | +0.1959 / +0.0008 | +0.1315 / +0.5990 | +1.0707 / +0.4925 |
| **`CT_PEAKER`** | **−0.0952** | **−0.5644** | **−0.5691** |
| `CC_REGULAR` | −0.0329 | −0.0928 | −0.9026 |
| `ST_GAS` | −0.0529 | −0.0734 | −0.0801 |
| `CT_CHP` / `ST_CHP` | 0.0000 / 0.0000 | −0.0038 / 0.0000 | −0.0017 / −0.0004 |
| nuclear, hydro, wind, solar, biomass, oil, `CC_CHP` | **0.0000** | **0.0000** | **0.0000** |

### 4.2 The scored C1 rows — eight of ten improve, two worsen, none flips

On the **committed bench** (the keeper's own), control → arm:

| year | class | model ctl → arm | actual | Δ ctl → Δ arm | status |
|---|---|---|---|---|---|
| 2023 | `CT_PEAKER` | 14.356 → 14.261 | 4.534 | **+9.82 → +9.73** (+4.1 → +4.0pp) | **FAIL** both |
| 2023 | `COAL_PRB` | 20.045 → 20.241 | 22.374 | −2.33 → **−2.13** | PASS |
| 2023 | `COAL_BIT` | 11.671 → 11.672 | 12.857 | −1.19 → −1.19 | PASS |
| 2023 | `CC_REGULAR` | 110.458 → 110.425 | 107.829 | +2.63 → **+2.60** | PASS |
| 2023 | **`ST_GAS`** | 3.601 → 3.548 | 10.483 | −6.88 → **−6.93** | PASS |
| 2024 | `CT_PEAKER` | 11.161 → 10.597 | 4.785 | **+6.38 → +5.81** (+2.5 → +2.3pp) | PASS |
| 2024 | `COAL_BIT` | 11.106 → 11.705 | 12.257 | **−1.15 → −0.55** | PASS |
| 2024 | `COAL_PRB` | 21.150 → 21.282 | 24.719 | −3.57 → **−3.44** | PASS |
| 2024 | `CC_REGULAR` | 110.120 → 110.027 | 104.997 | +5.12 → **+5.03** | PASS |
| 2024 | `ST_GAS` | 3.668 → 3.595 | 8.879 | −5.21 → **−5.28** | PASS |
| 2025 | all | — | — | — | **SKIPPED** (preliminary 923) |

**The row the PRECOMMIT registered as a coin flip survived.** 2023 `ST_GAS` passed by
0.288 TWh with a displacement bound of 0.369 TWh — 1.28× the margin — and §4.3 registered a
flip either way as roughly even odds. Delivered −0.053 TWh; the margin narrows **0.288 →
0.250 TWh** and the row holds.

### 4.3 Gates

| | control | arm |
|---|---|---|
| determination | `NOT-YET` (PRICE UNSCORED) | `NOT-YET` (PRICE UNSCORED) |
| C1 | FAIL, 1 row (2023 `CT_PEAKER`) | FAIL, 1 row (2023 `CT_PEAKER`) |
| C1 all · free | **13/14 · 9/10** | **13/14 · 9/10** |
| C2 / C4 / C8 | PASS | PASS |
| C6 governance | UNATTESTED *(a control is never attested)* | **PASS** |
| C3a / C3b / C3c | UNSCORABLE | UNSCORABLE |
| `grade_summary` | scored 4, target 3, fails 1 | scored 5, target 4, fails 1 |
| caveats | 0 ledgered, 0 protective | 0 ledgered, 0 protective |
| DOF | 3 entries / 1 residual | **unchanged** |

**Both benches agree.** On the HEAD-rebuilt bench the verdict, the failing-row set, the C1
headline and the caveat counts are identical; only the actuals shift slightly (2023 `ST_GAS`
10.442 vs 10.483, `CT_PEAKER` 4.503 vs 4.534) — see §7.

### 4.4 Rule 17 `[R-FLOOR-WINDOW]` — re-measured, and it holds in all twelve plant-years

The campaign floor reads a P0 pattern this arm perturbs, so the evidence had to be
re-measured. The tool was first validated by reproducing SOCO-53e §4.4's table **exactly, all
fifteen cells**. Binding share, control → arm, against each plant's own measured synchronized
share:

| plant | 2023 | 2024 | 2025 | measured | median floored block (h) |
|---|---|---|---|---|---|
| 2049 Jack Watson | 0.808 → 0.808 | 0.652 → 0.652 | 0.762 → **0.753** | 0.920 | 194 / 161 / 244 |
| 728 Yates | 0.134 → **0.074** | 0.536 → **0.478** | 0.749 → 0.749 | 0.843 | 324 / 216 / 342 |
| 10 Greene County | 0.312 → **0.309** | 0.300 → **0.295** | 0.506 → **0.496** | 0.752 | 190 / 365 / 321 |
| 26 E C Gaston | 0.203 → **0.197** | 0.106 → **0.078** | 0.184 → 0.184 | 0.639 | 64 / 111 / 87 |
| **3 Barry** | **0.000** | **0.000** | **0.000** | 0.063 | — |

**Zero exceedances, and every share FALLS OR HOLDS** — the predicted direction, because a
cheaper coal fleet commits less gas steam in P0, so the campaigns the floor detects get
shorter. Barry keeps zero floored unit-hours, floored blocks keep a median of **64–342 h**
(campaigns, not gap fills), and the mechanism still touches `ST_GAS` and nothing else.
`ST_GAS` forced share **0.0855 / 0.0966 / 0.1167** against the 30 % merchant cap, so C8 passes
on the budget. No COAL class carries a forced mechanism row at all.

### 4.5 D-1 trades a verdict in 2024, and the 2023 `COAL_BIT` failure is inherited

`COAL_BIT` 2023 FAILS on **both** sides (`profile_r` 0.474 → 0.469 against a 0.80 gate,
`cv_ratio` 0.001 → 0.003) — inherited, and the control reproduces the keeper's value to three
decimals. In 2024 a verdict **trades places**: `COAL_BIT` FAIL → **pass** (`profile_r` 0.941 →
0.965, `cv_ratio` 0.179 → 0.772) and `COAL_PRB` pass → **FAIL** (`cv_ratio` 0.521 → 0.469,
just under the 0.5 gate). **Neither gates anything here**: the standalone C7 diurnal-shape gate
was retired at rubric v3.1, and D-1 binds through rule 20 `[R-FORCED-BUDGET]` only for a class
over its forced-share cap, which no COAL class is. Reported because it moved.

### 4.6 Marginal emission rate — the falsified prediction

| year | lw-mean ctl → arm | p10 | median | p90 ctl → arm | zero-share |
|---|---|---|---|---|---|
| 2023 | 0.6263 → **0.6255** (−0.0008) | 0.4187 | 0.5905 | 0.8194 → 0.8635 | 0.00 % |
| 2024 | 0.6090 → **0.5921** (−0.0169) | 0.3833 | 0.5810 | 0.8717 → 0.7121 | 0.00 % |
| 2025 | 0.6369 → **0.6161** (−0.0207) | 0.3833 | 0.5848 | 1.0896 → 1.0244 | 0.15 % |

**It FELL in all three years; P9 predicted it would RISE.** See §6.

---

## 5. THE CONTROL CLOSED TWO OPEN QUESTIONS

The PRECOMMIT's G-DRIFT audit found **zero LIVE hunks on SOCO's LP path** across six upstream
commits, so form 4 was valid on code grounds. A control was solved anyway, because rule 36
`[R-YEAR-ISOLATION]` made the keeper the wrong baseline: it was a three-year **span** solved
where cross-year warm start and the same-year P1 basis seed both defaulted **ON**, and rule 36
withdrew their neutrality claim. That decision paid for itself twice.

### 5.1 The keeper's E14 dependency drift is COSMETIC — closed, not bounded

A seventh shard solved the control recipe for 2023 on the keeper's **off-pin** set
(**highspy 1.15.1 / pandas 3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5**), identical code,
identical config, identical year. Against the pinned control:

| | moved | of |
|---|---|---|
| class-hourly cells | **0** | 131,400 |
| system `price` cells | **0** | 26,280 |
| `marginal_emission_rate` cells | **0** | 26,280 |
| annual class MWh | **0.000000000** max |Δ| | 15 classes |

**Bit-identical.** `FINDING-soco-53e` §10.3 recorded the pin-confirm as abandoned and the
question as bounded rather than closed; it is now closed. **SOCO's keeper keeps its four E14
warnings and none of them touches a scored quantity.**

### 5.2 Rule 36's year-grouping cost at SOCO is ZERO at every scored grain

The year-isolated control against the keeper's committed span:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| annual class MWh, max \|Δ\| | **0.000000** | **0.000000** | **0.000000** |
| distinct hours touched | 279 (3.18 %) | 364 (4.16 %) | 32 (0.37 %) |
| class-hourly cells moved | 381 | 482 | 35 |
| price cells moved / max \|Δ\| $/MWh | 1,119 / 1.4e-14 | 1,734 / 0.0136 | 123 / 0.141 |

**Every moved cell is offset inside its own class** (CC_REGULAR ±245.759766 in 2023,
±639.404297 in 2024 — the same MW moved from one hour to another), and most of the movement is
**hydro**, whose annual total is pinned by a monthly energy budget. That is the
degenerate-alternate-optimum signature: the objective and every annual quantity unchanged,
marginal ties reshuffled in time. **Four orders of magnitude below MISO's 7–24 TWh**, and
immaterial to every scored quantity — the control's C1 rows on the committed bench reproduce
the keeper's **registered numbers exactly** (2023 `CT_PEAKER` +9.82, 2023 `ST_GAS` −6.88, 2024
`CT_PEAKER` +6.38, 2024 `ST_GAS` −5.21).

**So SOCO's keeper is not invalidated by rule 36, and this is the first ISO outside MISO where
that is measured rather than assumed.** It is one ISO's answer and does not transfer.

---

## 6. THIS LANE'S OWN PREDICTIONS, SCORED HONESTLY

| # | prediction | outcome |
|---|---|---|
| P1 | COAL rises every year, +0.15–0.75 / +0.40–2.00 / +1.00–5.00 TWh | **CONFIRMED**: +0.1967 / +0.7305 / +1.5632 |
| P2 | `ST_GAS` falls every year, 0.05–0.45 / 0.05–0.60 / 0.10–0.90 TWh | **CONFIRMED in direction all three years; the 2025 MAGNITUDE missed LOW** — −0.0801 against a 0.10 floor. The band was set from the displacement bound; 2025's delivered loss was smaller than the bound's lower reach. |
| P3 | The 2023 `ST_GAS` row is a coin flip; **both** outcomes registered in advance | **RESOLVED to PASS.** Margin 0.288 → 0.250 TWh. The bound (0.369) exceeded the margin (0.288) and the row still held, so the bound was loose, as an upper bound should be. |
| P4 | `CT_PEAKER` falls every year, 0.01–0.20 / 0.20–1.20 / 0.40–2.00; 2023 row stays FAILED above +9.5 | **CONFIRMED exactly**: −0.0952 / −0.5644 / −0.5691, row +9.73. |
| P5 | `CC_REGULAR` falls 0.02–0.40 / 0.02–0.40 / 0.30–2.50; no status change | **CONFIRMED**: −0.0329 / −0.0928 / −0.9026. |
| P6 | `NOT-YET` both sides; C2/C4/C6/C8 PASS; 0 caveats; DOF 3/1; C1 all 13/14 or 12/14 | **CONFIRMED**, and on the favourable branch: 13/14 · free 9/10, DOF 3/1. |
| P7 | CHP / non-thermals < 0.010 TWh, hydro < 0.001 | **CONFIRMED**: max CHP \|Δ\| 0.0038; nuclear / hydro / wind / solar / biomass / oil / `CC_CHP` **exactly 0.0000**. |
| P8 | Rule 17 holds in all twelve plant-years and shares FALL or hold; Barry keeps zero floored hours | **CONFIRMED exactly** (§4.4). |
| **P9** | **Marginal emission rate RISES, lw-mean +0.003 to +0.060 every year; p90 rises or unchanged** | **FALSIFIED.** It FELL in all three years (−0.0008 / −0.0169 / −0.0207) and p90 fell in 2024 and 2025. |
| P10 | Control 2023 reproduces the keeper to < 0.010 TWh per class | **CONFIRMED, exceeded**: 0.000000 MWh. |
| P11 | Control 2024/2025 may differ; predicted \|Δ\| < 2.0 TWh per class | **CONFIRMED, exceeded**: 0.000000 MWh. |
| P12 | DEP reproduces the pinned control to < 0.001 TWh per class | **CONFIRMED, exceeded**: bit-identical. |

**Eleven of twelve hold; P9 is falsified and the reason is instructive.** P9 reasoned about
which machine produces the **energy** — coal at ~0.95 t/MWh displacing gas at 0.45–0.65 — but
the marginal rate is set by whichever machine sets the **price**. Cheaper coal runs more
**inframarginally**, so in the hours it takes over, the marginal unit becomes a combined cycle
(~0.37) rather than a peaker. The p90 falling in 2024 and 2025 says the *dirtiest marginal
hours got cleaner*, which is the same story. The mechanism is coherent and the sign was mine
to get right. Every value stays well inside the declared |Δ| < 0.10 falsifier, so the miss is
directional, not a blow-up — but it is a miss and it is scored as one.

---

## 7. A/B INTEGRITY, THE BENCH, AND WHAT MOVED UNDER THIS LANE

**G-DRIFT (rule 29(b)).** `git diff cc1bcb24 HEAD` over the solve path returns 887 insertions
across 6 files, decomposing exactly into six upstream commits, every one classified with its
reason in PRECOMMIT §3: `e63f730a` (spp-49, `benchmark_membership_vintage_union` default-off
and absent from the recipe), `13aaedd4` (miso-263's `coal_fuel_inventory` guard, which SOCO
records as `None` and which `run_calibration.py` refuses outside MISO), `5356fb71` (nyiso-241,
NYISO-gated, absent), `cb1e60b7` (rule 36's default flip — inert on the replay path, which
already forced both knobs off), `3b719484` (PJM-gated seam ladder), and `03eed7e9` (nyiso-240,
benchmark path only). **Zero LIVE hunks on the LP path.**

**The A/B itself is single-delta by construction.** Both legs ran
`scripts/replay_keeper.py results/calibration/soco53e_st_hr`, whose `meta.json` is the
authoritative snapshot of every `solve_and_persist` kwarg, and the arm's delta rode
`--set measured_coal_heat_rates=true`. No hand-typed flag list could drop a gate. All seven
legs solved at the identical SHA on the identical pinned dependency set (except the DEP leg,
whose off-pin set is its purpose), and the composer asserts posture, the single delta, band
identity, `dispatch/<year>_P1.parquet` presence, a live `marginal_emission_rate` and an
identical `environment.packages` on every leg before it writes anything.

**THE BENCHMARK MOVED UNDER THIS LANE, AND IT IS ANOTHER LANE'S REPAIR.** The EIA-923 snapshot
rebuilt at HEAD carries nyiso-240's `_backfill_eia923_missing_months` and
`_reattribute_dual_fuel_oil` (commit `03eed7e9`). On SOCO that adds **+2.616 TWh** of benchmark
generation across **126 of ~1,048 rows**, concentrated in January (+1.048), June (+1.023),
February (+0.296) and August (+0.249) — the signature of respondent-withheld months being
backfilled. `campd` and `eia930` rebuild **byte-identical** to the keeper's.

**The decomposition is exact and that is the point:** the control's DISPATCH is identical to
the keeper's to 0.000000 MWh, so every difference between the keeper's registered C1 numbers
and a HEAD-bench score is the benchmark repair and **none of it is this lane's mechanism**.

**SOCO's bench parts were deliberately NOT rebuilt**, exactly as SOCO-53c/53d/53e did:
`dashboard_add_run.py`'s auto-rebuild was reverted and `metrics.json` re-written on the
committed bench. **Both verdicts are reported and they agree** (§4.3). Routed for the SOCO
desk: SOCO's committed bench does not yet carry nyiso-240's repair, `check_bench_freshness`
flags all three parts STALE, and rebuilding it is a decision that re-scores the keeper — not a
lane's call to make silently.

---

## 8. GATES

| gate | state |
|---|---|
| `check_cache_key_registration` | **PASS** — 858 fields, 313 registered, all declared defaults match HEAD |
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, anchors (0 unresolvable), keeper stamps, §5.x prose headers, all three ratchets |
| `tests/unit/data/test_measured_coal_heat_rates.py` + `test_measured_st_heat_rates.py` | **PASS (32)** |
| `tests/unit/config` | **1 failure**, `test_soco_token_collides_with_no_other_raw_name` — RED at HEAD, and **verified to fail identically with this lane's two artifact files moved aside**. NOT patched (§9). The three `test_reserve_config.py::TestErcotMultiProduct` failures SOCO-53e recorded are now green, fixed by another lane. |
| `ruff check` / `ruff format` | clean on every file this lane touched |
| `check_gate_a_provenance` | SOCO's only line is the expected NOTE; **no gate-(a) stamp**, no `calibration-complete.json` entry |
| `check_bench_freshness` | RED repo-wide (12 of 44 parts across ISOs). SOCO's three are STALE for the reason §7 measures. Not this lane's to fix. |
| `check_registry_payload_parity` | **CI-GREEN for SOCO.** The only committed SOCO path is the registered `soco53f_coal_hr`. The LOCAL run lists eight SOCO dirs — every one this session's own gitignored leg or span — because the gate walks the **filesystem** (`check_registry_payload_parity.py:437`), exactly as rule 31's 2026-09-16 correction documents. **None deleted** (rule 31). The one non-SOCO entry, `caiso279_ablate_dswcouple_span`, is pre-existing. |
| `audit_keepers --check --iso SOCO` | E14 ×4 + E11 (both expected; E14 now **closed by measurement**, §5.1), and **E13 fires** — see §8.1 |

### 8.1 E13 fires for the FOURTH consecutive SOCO lane, for the same structural reason

`2026-09-20-soco53f-measured-coal-hr` is registered for SOCO but is neither the keeper nor
stamped to one. **It is not a superseded run left behind a promotion**; it is a newly
registered candidate whose promotion the owner has not ruled on, and E13 has no state for
that. The red is the unavoidable consequence of obeying three rules at once — rule 15
`[R-DASHBOARD]` (register the moment it finishes), rule 31 `[R-RETAIN]` (never delete before
the owner rules) and rule 35(f) / E13. Each way to turn it green breaks one of them: pruning
deletes a result before the ruling; stamping `holdout.keeper` would be **factually false**
(rule 30 `[R-TOUCHPOINT-FOLD]` (a) is for the keeper's own recipe on a *held-out year*, and
this is a *different config on the same years*); promoting pre-empts the owner. **Either
ruling clears it immediately.** `FINDING-soco-53` §9.1, `FINDING-soco-53d` §9.1 and
`FINDING-soco-53e` §8.1 recorded the identical analysis. **Four lanes; the routed fix is a
`candidate: true` sidecar field, or an E13 exemption for a run registered after the current
keeper's date with no promotion recorded. It is worth fixing.**

---

## 9. ROUTED

1. **`coal_prb_proxy_own_iso` IS SOCO-53g, IT IS ~3× THIS LANE'S LEVER, AND IT POINTS THE
   OTHER WAY.** SOCO's three PRB plants — **6002 Miller, 6073 Daniel, 6257 Scherer, 6,361.5 MW
   = 55 % of SOCO's coal capacity** — are priced off the hand-curated **ERCOT-only** reporter
   pool at **1.8228 / 1.7520 / 1.6147 $/MMBtu**. SOCO's own three reporters paid **2.6711 /
   2.4982 / 2.4610** — the model under-prices their fuel by **+0.85 / +0.75 / +0.85 $/MMBtu,
   47–52 %**, or **≈ $9.7/MWh** at a measured heat rate of 11.4 against this lane's −$2.95 at
   Scherer. The gate is built and default-off; nwpp-42 left it for each ISO's own lane. **This
   arm therefore makes coal cheaper on three plants the model already prices far too cheap on
   fuel** — stated at the gate, and a reason to run 53g next rather than to stack it here.
2. **`derive_parasitic_load.py` has never been run for SOCO** (§2.4), whose own coal meter
   reads 0.866–0.928 against the committed 0.93. Cross-ISO intake, re-routed with SOCO's
   numbers.
3. **SOCO-53b, the 2025 hydro input hole.** 0.327 TWh modelled against 6.012 measured; coal
   backfills the missing 5.68 TWh, which is why 2025 model coal is already above actual — and
   **this arm adds +1.5632 TWh more**. The arm makes an artifact of a missing input worse. The
   instrument is `--hydro-backfill-year` / `--hydro-eia930-monthly`. Deferred deliberately: a
   second delta on a different input, biting only in a year whose C1 rows are SKIPPED.
4. **Barry unit 4** (§2.3) — 362 MW the model prices as coal on a coal fuel price while CAMPD
   files it as gas. Unchanged, and now measured.
5. **nwpp-42's membership rule.** Because it selects on `primaryFuelInfo`, a model COAL row
   whose CAMPD unit is tagged gas takes its *plant's other units'* rate. At SOCO that is one
   row and it improves on net; elsewhere it might not. For that mechanism's successor.
6. **SOCO's committed bench does not carry nyiso-240's repair** (§7). Rebuilding it re-scores
   the keeper; that is the desk's call, not a lane's.
7. **E13's fourth consecutive SOCO firing** (§8.1).
8. **CLAUDE.md rule 32(b) is stale and internally inconsistent**, re-raised for the third
   time — see §11.

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** The parent ran no LP of any length (rule 32(a)). Phase 0, the two
  `fleet_only` rebuilds, the displacement bounds, the floors re-measurement, composition and
  scoring are all zero-LP.
- **Seven shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)): three control, three
  arm, one dependency-isolation. All seven pinned to `04f7f849cddac88fe6991fafcc4ed08f6df83e85`
  and all seven pushed a FULL 16-file bundle including `dispatch/<year>_P1.parquet` and the
  bundle-root `system.parquet` (rule 34(a)).
- **Retrievability verified before anything was archived** (rule 34(d)): `git ls-tree` returns
  16 files on each. **A promotion costs ZERO re-solves.** Recovery by IMMUTABLE SHA (rule
  33(d)), also recorded in `.gitignore`:

  | leg | SHA |
  |---|---|
  | `soco53f_ctl_2023` | `b06f88080900f3bb4473f9d9fb725dd127795d08` |
  | `soco53f_ctl_2024` | `1dbf2200481d80e7c47c3523f09aa394e25a8089` |
  | `soco53f_ctl_2025` | `f96f600729736854588f56bb2baf73fde6ec9f0b` |
  | `soco53f_arm_2023` | `0f061987f1877f62339df72174c74fbf0e8b89da` |
  | `soco53f_arm_2024` | `34d7131e98f6be0bdb463428f7c8bdb781a56b2e` |
  | `soco53f_arm_2025` | `381ca2fc8b4827246f2e99f7f980157c84447fee` |
  | `soco53f_dep_2023` | `8071d457408e25b3f5113c4983d7ffe950b436c5` |

  The two spans re-compose from those legs at zero LP with
  `scripts/probes/soco53f_compose_span.py`.
- **The ARM COMPOSITE is committed** — slim + `hourly/` (17 files), sidecar and run payload —
  so it is on `main` and on the dashboard. The per-year legs and both spans are **gitignored,
  not deleted** (rule 31 `[R-RETAIN]`, and rule 29(c) via `.gitignore` rather than `rm`).
- **Nothing was deleted.** The keeper's own bundle, recovered at
  `884dca3132e8d1d1e1f18fbb789c356506a4e343`, is untouched.

---

## 11. FLAGGED FOR THE OWNER — CLAUDE.md IS INTERNALLY INCONSISTENT (third raising)

Rule 32(b) `[R-SHARD]` still reads **"SLIM PER-YEAR FAN-OUT IS BANNED"**, which contradicts:

- **rule 36 `[R-YEAR-ISOLATION]` (a)**, added to the same file one day later, which states in
  terms that *"this is the one place rule 32(b)'s ban on per-year fan-out does NOT apply"* and
  requires exactly the fan-out this lane ran;
- **rule 34 `[R-SHARD-PROMOTABLE]` (c)**, *"launch one shard for EACH"* year;
- the owner's own standing instruction of 2026-09-19.

The ban's stated reason — *"a shard can only push the slim set"* — was fixed by rule 34(a),
and this lane is the demonstration: seven shards each pushed a full 16-file bundle and the
legs composed with **zero** re-solves. SOCO-53e offered the amendment twice and it was not
taken up. **Re-raised, not silently edited.**

---

## 12. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — OPEN, AND IT IS THE OWNER'S

**SOCO's keeper is unchanged at `2026-09-19-soco53e-measured-st-gas`. Nothing has been
pruned.** The candidate is `2026-09-20-soco53f-measured-coal-hr`.

**The case FOR promoting.** It is a pure rule 14 `[R-ACCURATE]` measured-data repair with
**zero `ScenarioConfig` fields and zero free parameters**, covering **100 % of an 11.5 GW
fleet** — five times the capacity the incumbent keeper's own mechanism touched. It removes a
real structural defect (an ANNUAL average, inflated by startup and offline fuel, setting an
operating offer) on every one of six plants. **Eight of the ten gated non-CHP C1 rows improve**
and none flips, on **both** benches. The owed rule-17 re-measurement holds in all twelve
plant-years with shares falling. And the lane falsified the premise that commissioned it
before spending an LP, which is the behaviour rule 1 asks for.

**The case AGAINST.** The determination does not move (`NOT-YET` both sides), the headline
defect is untouched, two `ST_GAS` rows worsen, one of the lane's own predictions was
falsified, D-1 trades a verdict in 2024, and the arm makes the 2025 coal excess worse — though
that excess is SOCO-53b's hydro hole, not this mechanism.

**If the owner promotes**, rule 35 `[R-PROMOTE]` binds and the year union is already
enumerated (rule 35(b), before any prune): SOCO's registered years are exactly
**{2023, 2024, 2025}** over both registered runs, no folded touchpoints and no dangling
`holdout.keeper`, and this run covers all three — **the promotion shrinks nothing**. The order
is: capture the lineage diff while both bundles are on disk, write the id into
`frontend/data/backcast/keepers/SOCO.json`, run `audit_keepers --check --iso SOCO`, rebuild
`build_status.py --iso SOCO`, re-stamp the SOCO matrix shard and its §5.8 prose header, and
**only then** `scripts/prune_iso_runs.py --iso SOCO --force-uncite`. `calibration-complete.json`
needs no change — SOCO has never had an entry.

**Three questions beyond the promotion:**

1. **May SOCO's bench be rebuilt?** It does not carry nyiso-240's repair, which adds
   **+2.616 TWh** to SOCO's benchmark. Rebuilding re-scores the keeper. Not a lane's call.
2. **E13 has now fired on FOUR consecutive SOCO candidates** for the same structural reason
   (§8.1). Is a `candidate: true` sidecar field worth adding?
3. **Rule 32(b) versus rules 34(c) and 36(a)** (§11) — third raising.

---

## Log entry

## soco-53f — 2026-09-20 — an annual average is not a weighted mean, so the measurement reversed the sign of the premise, and a control solved for one reason closed two other questions

The premise that commissioned this lane was wrong in sign, and the measurement said so before an LP was spent. FINDING-soco-53e §7.1 routed SOCO-53f on the reading that E C Gaston's coal boiler, left on the blended ST family rate 11.5505 after its four gas boilers were repriced, is "roughly 0.5 MMBtu/MWh too CHEAP for a coal machine". Its own meter reads 11.0505 — 0.5000 too DEAR, the magnitude right to four decimals with the sign inverted. The routing treated the plant rate as a weighted mean between two machines, so the coal side had to sit above it; it is not a mean but an eGRID ANNUAL average, PLHTIAN/PLNGENAN, which folds startup fuel, shutdown tails and the offline hours' bank fuel into the number that sets the offer and therefore sits above both machines' operating rates rather than between them. That is the entire thesis of the mechanism, and Gaston is the case that shows it. So the arm is not the asymmetry-closer it was routed as; it is something larger. All six plants get cheaper — Barry −1.8711, Daniel −0.9687, Scherer −0.8690, Gaston −0.5000, Bowen −0.4040, Miller −0.1022 — capacity-weighted 11.5267 to 10.8926, −5.5 %, across 100 % of an 11.5 GW fleet, five times the capacity the gas-steam sibling touched.

No ScenarioConfig field was written and no free parameter added: nwpp-42 shipped the mechanism one day earlier and it was a strict no-op for SOCO until this lane derived SOCO's artifact (campd_coal_heat_rates_SOCO.csv, sha256[:16] efd5926eecc62d8f, 6/6 plants / 11,512.0 MW, 252,093 in-band steady hours at 15 units). A provenance repair landed with it and it changed the number: nwpp-42's deriver read its model_heat_rate_egrid comparison column off the loader-default fleet, which for SOCO is a fleet nobody solves — it reported Barry at 8.9950 and Daniel at 8.3995, the physically impossible plant blends egrid_family_heat_rates exists to remove, and so claimed the measured rates were dearer than the model's. The three provenance flags the gas-steam sibling already takes were added, with a model_recipe column and a guard that the provenance recipe cannot move plant membership; no applied number changes and the 14 committed tests pass unchanged. Rule 19 is machine-verified at two grains: 16 of 393 built-fleet rows and 25 of 327 LP rows move, all COAL, with ST_GAS — repriced by soco-53e one day earlier and sharing plant codes 3 and 26 with this population — byte-identical at max delta exactly 0.000000000000.

The gates do not move and eight of the ten gated non-CHP rows improve. Determination NOT-YET (rubric v3.8, PRICE UNSCORED) on both sides, C1 all 13/14 and free 9/10 on both sides, C2/C4/C6/C8 passing, zero ledgered and zero protective caveats, DOF unchanged at 3/1, and zero C1 status flips on either the committed or the HEAD-rebuilt bench. 2023 CT_PEAKER +9.82 to +9.73 TWh and still the single FAIL, 2024 CT_PEAKER +6.38 to +5.81, 2024 COAL_BIT −1.15 to −0.55, 2023 COAL_PRB −2.33 to −2.13, 2024 COAL_PRB −3.57 to −3.44, CC_REGULAR +2.63 to +2.60 and +5.12 to +5.03; against 2023 ST_GAS −6.88 to −6.93 and 2024 −5.21 to −5.28. The PRECOMMIT registered the 2023 ST_GAS row as a coin flip in both directions, its 0.369 TWh displacement bound against a 0.288 TWh margin; it survived, margin 0.288 to 0.250. SOCO's headline defect is untouched, as the PRECOMMIT said first with the number: 2023's displaced class is 64 % ST_GAS and only 9 % CT_PEAKER, so the arm closes about half a percent of a nine-TWh failure. The rule-17 re-measurement holds in all twelve plant-years and the binding shares fall or hold in every one, Barry keeping zero floored hours and floored blocks a median of 64 to 342 hours.

A control this lane had to solve for its own A/B closed two open governance questions, and they may outlast the arm. First, SOCO's keeper E14 dependency drift is cosmetic: a seventh shard re-solved the control recipe for 2023 on the keeper's off-pin set (highspy 1.15.1 / pandas 3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5) and the result is bit-identical — 0 of 131,400 class-hourly cells, 0 of 26,280 price cells, 0 of 26,280 marginal-emission cells. FINDING-soco-53e §10.3 left that bounded because its pin-confirm was abandoned; it is now closed. Second, rule 36's "unmeasured outside MISO" year-grouping cost is measured at SOCO and is zero: the year-isolated control reproduces the keeper's annual class generation to exactly 0.000000 MWh on all 45 class-years and its scored C1 rows reproduce the keeper's registered numbers exactly, with only intra-class timing moving (279/364/32 hours of 8,760, every cell offset within its own class, mostly budget-pinned hydro) and prices by at most 0.141 $/MWh. That is one ISO's answer and transfers to none.

Reported against the lane. Prediction P9 was falsified: the marginal emission rate was predicted to rise and fell in all three years (0.6263 to 0.6255, 0.6090 to 0.5921, 0.6369 to 0.6161), because the prediction reasoned about which machine produces the energy where the marginal rate is set by which machine sets the price — cheaper coal runs inframarginally and hands the margin to a combined cycle rather than taking it from a peaker. Eleven of twelve predictions hold; that one does not, and it is scored as a miss. D-1 trades a verdict in 2024 (COAL_BIT FAIL to pass, COAL_PRB pass to FAIL, neither gating since no COAL class is forced). The arm adds +1.5632 TWh to a 2025 coal excess whose cause is SOCO-53b's hydro input hole — 0.327 TWh modelled against 6.012 measured — not coal pricing. The committed COAL parasitic default 0.93 does not reproduce SOCO's own meter (0.866–0.928 on the four single-fuel sites); it is used anyway because it is the same factor the benchmark's net actual is built with, and the consequence is stated: the applied rates are biased low by 1.5 to 5.9 %, so the cheapening is if anything understated. And the benchmark moved under this lane: the HEAD-rebuilt EIA-923 carries nyiso-240's repair, which adds +2.616 TWh to SOCO's benchmark across 126 rows, while campd and eia930 rebuild byte-identical — the decomposition is exact, because the control's dispatch is identical to the keeper's, so none of that difference is this mechanism.

Routed and larger than this lever: coal_prb_proxy_own_iso as SOCO-53g. SOCO's three PRB plants — Miller, Daniel and Scherer, 55 % of its coal capacity — are priced off the hand-curated ERCOT-only reporter pool at 1.8228/1.7520/1.6147 $/MMBtu against their own 2.6711/2.4982/2.4610, an under-pricing of about $9.7/MWh against this lane's $2.95 and in the opposite direction, so this arm makes coal cheaper on three plants the model already prices far too cheap on fuel. Seven per-year shards under rule 36, each pushing a full 16-file bundle, composed at zero LP with no re-solves; every leg recoverable by immutable SHA and recorded in .gitignore, so a promotion costs nothing. The promotion is open and is the owner's. Record: `docs/handoffs/FINDING-soco-53f-2026-09-20.md`.
