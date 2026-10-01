# PRECOMMIT — SOCO-53g: `coal_prb_proxy_own_iso` for SOCO, and the $9.7/MWh defect that never reaches the LP

**Lane** SOCO-53g · **Model** Opus 5 · **Date** 2026-09-20 ·
**Branch** `claude/soco-coal-prb-proxy-own-iso-4qln9o` · **Data profile** `soco` ·
**Incumbent keeper** `2026-09-20-soco53f-measured-coal-hr`, bundle
`results/calibration/soco53f_coal_hr`, basis `04f7f849`; the full 16-file per-year
layer recovered in this session (§8). **Parent HEAD** `a57b26146354bedc74308ec347f2505adb1d0b08`.
**Predecessors** `FINDING-soco-53f-2026-09-20.md` (§9 item 1 commissions this lane,
§2.4 the parasitic finding, §5 two closed governance questions, §6 P9,
§7 the bench), `PRECOMMIT-soco-53f-2026-09-20.md`, `docs/calibration-log/soco.md`.
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`,
14 `[R-ACCURATE]`, 15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 17 `[R-FLOOR-WINDOW]`,
19 `[R-ONE-MECH]`, 21 `[R-DOF]`, 23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`,
25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`, 29 `[R-SCREEN]`, 31 `[R-RETAIN]`,
32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`,
**36 `[R-YEAR-ISOLATION]`**.

**Pushed before anything is solved.** Every number below is ZERO-LP: the committed
EIA-923 receipts cache read directly, the fleet loaders called directly, and the
keeper's own recomposed bundle replayed through `run_year(..., fleet_only=True)`
rebuilds. **The parent ran no LP of any length** (rule 32(a)). Nothing below is
revised after a solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json`
carries **no SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent`. C3a / C3b / C3c are **UNSCORABLE, not
failed**. The ceiling is rubric v3.8 `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can
**never** read `CALIBRATED`. Scored on **C1 / C2 / C4 / C6 / C8 only**. Gate **G17**
absolute: no neighbouring hub, no proxy, no cost-stack price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0.** With no price benchmark
there is no price residual, so the rule-1 authorized channel is unreachable here, not
merely unused. This lane touches no band, share, floor level, threshold or offer. **The
attestation's governance block will carry NO `authorized_price_tuning` KEY at all** —
`calibration_verdict.py` validates any present value as a structured rule-1 declaration
and a prose string there FAILS C6. The declared-NONE statement goes in `attested_by`
prose. `scripts/gen_soco53f_attestation.py` is the copy source; it machine-verifies this.

---

## 1. HEADLINE — THE COMMISSIONING PREMISE IS FALSE, AND PHASE 0 SAYS SO WITHOUT AN LP

`FINDING-soco-53f` §9 item 1 routed this lane on a measured claim:

> SOCO's three PRB plants *"are priced off the hand-curated ERCOT-only reporter pool at
> 1.8228 / 1.7520 / 1.6147 $/MMBtu. SOCO's own three reporters paid 2.6711 / 2.4982 /
> 2.4610 — the model under-prices their fuel by +0.85 / +0.75 / +0.85 $/MMBtu, 47–52 %,
> or ≈ $9.7/MWh."*

**Both pooled numbers are correct and I reproduce them exactly (§2). The inference from
them is wrong, and it is wrong for a structural reason: NEITHER POOL EVER REACHES THE
LP.** The pool proxy is written onto SOCO's PRB rows and then **completely overwritten**,
three lines later in the same function, by each plant's OWN filed EIA-923 monthly
delivered cost. The model does not price Miller at 1.8228. It prices Miller at **2.1886**,
Daniel at **3.8505** and Scherer at **3.3945** (2023) — each plant's own receipts.

**Measured consequence, at full float precision, on the keeper's own rebuilt LP inputs
(§3): `coal_prb_proxy_own_iso` moves NOTHING in 2023, NOTHING in 2024, and in 2025 it
moves four tranche rows of ONE plant for 744 hours.** That is its entire live footprint
at SOCO.

**This lane is therefore run as a rule-14 `[R-ACCURATE]` POSTURE repair of a genuinely
small object, declared as such before the solve, not as the 3× lever it was routed as.**
§6 registers the near-certain predictions that follow, including a **bit-identity**
prediction for 2023 and 2024 that is the strongest falsifier this lane can offer.

---

## 2. PHASE 0 STEP 1 — BOTH SERIES RE-DERIVED FROM SCRATCH, MONTHLY

`fc._prb_monthly_actuals(None)` vs `fc._prb_monthly_actuals("SOCO")`, re-derived in this
session rather than inherited. **The annual means reproduce 53f's to four decimals.**

| year | series | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **mean** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | default (ERCOT) | 1.8989 | 1.8481 | 1.8632 | 1.8396 | 1.8194 | 1.8008 | 1.7853 | 1.7626 | 1.7794 | 1.7911 | 1.8383 | 1.8466 | **1.8228** |
| 2023 | SOCO own | 2.8571 | 2.8007 | 2.7497 | 2.5742 | 2.6294 | 2.6174 | 2.5720 | 2.5862 | 2.5699 | 2.6781 | 2.7267 | 2.6923 | **2.6711** |
| 2024 | default (ERCOT) | 1.8183 | 1.7938 | 1.7699 | 1.7922 | 1.7718 | 1.7638 | 1.7468 | 1.7274 | 1.7401 | 1.7052 | 1.6883 | 1.7060 | **1.7520** |
| 2024 | SOCO own | 2.6146 | 2.4996 | 2.5603 | 2.6238 | 2.5399 | 2.5780 | 2.4628 | 2.4628 | 2.4555 | 2.3826 | 2.3872 | 2.4117 | **2.4982** |
| 2025 | default (ERCOT) | 1.7441 | 1.7308 | 1.7182 | 1.6448 | 1.5984 | 1.5642 | 1.5471 | 1.5534 | 1.5811 | 1.5728 | 1.5708 | 1.5503 | **1.6147** |
| 2025 | SOCO own | 2.3941 | 2.3890 | 2.4460 | 2.5301 | 2.5348 | 2.5412 | 2.5303 | 2.5245 | 2.3909 | 2.2722 | 2.3746 | 2.6039 | **2.4610** |

**LEVEL OR SHAPE? It is overwhelmingly LEVEL, with a real shape limb in 2025 only.** The
monthly ratio SOCO/ERCOT stays inside **1.373–1.680** across all 36 months — a roughly
uniform +40–60 % lift. Month-to-month correlation is **+0.82 (2023)** and **+0.90
(2024)** — the two series move together — but **−0.32 in 2025**, where the ERCOT series
falls through the year (1.744 → 1.550) while SOCO's rises mid-year (2.394 → 2.541 → 2.272
→ 2.604). Both series are low-variance (cv 0.021–0.045). **So: a level mechanism in 2023
and 2024, and a level-plus-shape mechanism in 2025.** The write-up says which, as owed.

---

## 3. PHASE 0 STEP 2 — THE POOL IS DEEPER THAN THE DEFAULT IT REPLACES, AND NOTHING IS FILLED

The step-2 question was whether `_prb_monthly_actuals` is papering over gaps with its
`monthly[np.isnan(monthly)] = np.nanmean(monthly)` annual-mean fill, in which case rule
14's misalignment exception might apply. **It is not, in either pool:**

| pool | plants in the population | months reported | **NaN-FILLED months** | reporters/month |
|---|---|---|---|---|
| default (`COAL_PLANT_SUPPLY` prb) | 7 listed — **only 2 file anything**: 6179, 7097 (both TX) | 12/12 in all three years | **0 / 0 / 0** | 2 / 1.92 / 2 |
| SOCO own (`coal_supply_by_iso`) | 3 — 6002 Miller, 6073 Daniel, 6257 Scherer | 12/12 in all three years | **0 / 0 / 0** | 3 / 3 / 2.83 |

**Zero filled months on either side, so the fill path is never exercised and rule 14's
misalignment exception does not apply.** And the finding runs the other way from the
concern: **SOCO's pool is backed by THREE reporters where the ERCOT default is backed by
TWO.** Five of the seven hand-curated `COAL_PLANT_SUPPLY` PRB plants file no coal receipt
at all in 2023–2025, so "the ERCOT pool" is in fact a two-plant Texas pool. On pool depth
the arm is the stronger input, not the weaker one.

Quantity weights inside the SOCO pool (2023): Miller **0.6252**, Scherer **0.3072**,
Daniel **0.0676**.

## 3.1 PHASE 0 STEP 3 — NO CIRCULARITY, AND RULE 13'S FORWARD TEST IS MET EXPLICITLY

The step-3 risk was real and named: SOCO's pool **is** the three plants being repriced.
Three things dispose of it, and the third is measured rather than argued.

1. **Source.** EIA-923 Schedule 2 **fuel receipts and costs** — the delivered price and
   quantity of coal a plant *purchased*, quantity-weighted. It is an input measurement of
   a procurement transaction. **The model's dispatch, generation and prices do not enter
   it at any point**, so it cannot be an outcome fed back (rule 13's forbidden case).
2. **Forward test — "could this same quantity be produced for a forward year from forward
   drivers, and would it respond to changed conditions?" YES, and the code already does
   it.** `_build_coal_price_trajectories` extends PRB past 2025 from forward drivers
   (`PRB_COMMODITY_SHARE` / `PRB_COMMODITY_DECLINE` / `PRB_RAIL_DIESEL_SHARE` /
   `PRB_RAIL_NONDIESEL_SHARE` + `INFLATION_RATE`), and `_prb_monthly_actuals` returns
   `{}` for a forward year so the trajectory takes over. The *construction* — quantity-
   weighted delivered cost over this market's own filed receipts — is the identical
   construction ERCOT already uses, regenerates for any year with receipts, and moves
   with a coal or rail-diesel shock. **Zero free parameters** (rule 21).
3. **THE SELF-REFERENCE IS MEASURED AND IT IS EXACTLY ZERO.** The arm's only live
   consumer is Daniel (6073) in **January 2025** (§4). **Daniel files NOTHING in January
   2025** — its 2025 reported months are 2–12. So the January pool value is built from
   Miller and Scherer alone, and the **leave-one-out** value excluding Daniel is
   **2.3941 against the pooled 2.3941 — identical, because Daniel contributes no rows to
   that month by construction.** The plant being priced contributes nothing to the number
   that prices it.

**And the arm moves toward truth without reaching it, which is the right direction for an
input repair.** Daniel's own nearest filed month is **February 2025 at 3.4190 $/MMBtu**.
The control charges Daniel **1.7441** in January; the arm charges **2.3941**. The arm
closes roughly **39 %** of the gap to Daniel's own adjacent month and stays well below it,
so the residual is **understated, never overstated**.

---

## 4. PHASE 0 STEP 4 — RULE 19 `[R-ONE-MECH]`, MECHANICALLY, AT TWO GRAINS

This mechanism moves **FUEL PRICE**, not heat rate, so the fleet-build grain shows
nothing by construction. The proof is on `fuel_prices` and on `mc_base`, from
`run_year(..., fleet_only=True)` rebuilds off the keeper's own recomposed bundle, control
vs `prb_overrides={"coal_prb_proxy_own_iso": True}`. **Resolved config verified on every
leg: `ctl=False`, `arm=True`** — so a null result is the mechanism, not the plumbing.

### 4.1 The whole-LP answer

| year | LP rows | `fuel_prices` rows moved | `mc_base` rows moved | max \|Δ mc_base\| $/MWh |
|---|---|---|---|---|
| 2023 | 327 | **0** | **0** | **0.000000000000** |
| 2024 | ~327 | **0** | **0** | **0.000000000000** |
| 2025 | 290 | **5** | **4** | **7.7512** (744 h only) |

**Every non-COAL class is at max \|Δ\| exactly 0.000000000000 in all three years**, which
is not a gate that had to hold but an identity: `apply_coal_supply_pricing` writes only
rows carrying `coal_supply ∈ {lignite, prb}`, and nothing else in the function touches
`fuel_prices`. `ST_GAS`, `CT_PEAKER`, `CC_REGULAR`, `CC_CHP`, `CT_CHP`, `ST_CHP` and
hydro are untouched. Plant codes **3** and **26** carry `COAL` and `ST_GAS` rows behind
one ORIS code, and plant **6073** carries a 1,132 MW gas `CC_REGULAR` beside its coal
rows — **the CC rows do not move**, so the class gate does not leak.

### 4.2 The mutation-sequence decomposition — WHY it is zero

Replaying `run_calibration.py:4484-4495`'s exact sequence by hand, with the proxy OFF and
ON, snapshotting after each step:

| step | 2023 max\|OFF−ON\| | 2024 | 2025 |
|---|---|---|---|
| 1. `resolve_fuel_prices(apply_monthly=False)` | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| 2. after `apply_coal_supply_pricing` | **0.958175366013** | **0.831525117241** | **1.053587942453** |
| 3. after `apply_plant_monthly_fuel_prices` | **0.000000000000** | **0.000000000000** | **0.649940697470** |

**The mechanism fires — 15 rows move at step 2, exactly the three PRB plants' five
tranches each, 1.8227 → 2.6706 $/MMBtu in 2023 — and is then erased.** The plant-monthly
overlay writes **8,760 of 8,760 cells** on every one of those 15 rows in 2023 and 2024.
What survives to the LP is each plant's own filed receipts:

| plant | model's delivered coal price, 2023 / 2024 / 2025 ($/MMBtu, annual mean) |
|---|---|
| 6002 James H Miller Jr | 2.1886 / 2.0999 / 2.1638 |
| 6073 Victor J Daniel Jr | 3.8505 / 3.6943 / 2.9328 (ctl) → **2.9880 (arm)** |
| 6257 Scherer | 3.3945 / 3.1173 / 3.0816 |

**So the "47–52 % too cheap" reading compared two pool proxies to each other. The LP sees
neither.** Rule 14 `[R-ACCURATE]` was already being honoured at SOCO, one layer further
down, by `coal_plant_monthly_pricing` — which `backcast_config` sets True for every ISO.

### 4.3 The 2025 residual, pinned exactly

**One plant, one month, 744 contiguous hours.**

- Rows: `Victor J Daniel Jr` **committed / econlo / econhi / peak** (`mustrun` moves on
  `fuel_prices` but not on `mc_base`; reported and re-checked post-solve).
- Hours: **0–743**, contiguous, = **2025-01-01 00:00 .. 2025-01-31 23:00**. Zero hours in
  any other month.
- Cause: the plant-monthly overlay wrote **8,016 of 8,760** cells on Daniel's rows —
  744 short, exactly January — because **Daniel filed no January-2025 receipt** and the
  `nearby_fuel_price_fallback` did not reach it. Scherer also missed one reporting month
  in 2025 and the fallback DID cover it (8,760/8,760), so this is a per-plant gap, not a
  systematic one.
- Size: fuel **+0.6500 $/MMBtu** (1.7441 → 2.3941), offer **+7.7512 $/MWh** on all four
  rows, flat across the 744 hours.
- Exposure: Daniel's COAL tranches generated **0.2811 TWh** in those 744 hours under the
  keeper (`mustrun` 0.1265 floored + `committed` 0.0141 + `econlo` 0.0750 + `econhi`
  0.0599 + `peak` 0.0056), of which the **at-risk econ/peak energy is 0.1405 TWh**.
- **DISPLACEMENT BOUND: 0.4108 TWh** — all four moved tranches at `pmax` for every one of
  the 744 hours. An absolute ceiling, not a prediction.

**2025's C1 rows are SKIPPED (preliminary EIA-923), so this arm cannot move a single
scored C1 row in any year.** That is stated here, before the solve, and it is the whole
gate story.

### 4.4 BARRY UNIT 4 IS PROVABLY OUTSIDE THE BLAST RADIUS

The handoff flagged Barry unit 4 — a 362 MW `COAL` model row that CAMPD files as Pipeline
Natural Gas and the model charges a coal fuel price — as "squarely in your blast radius
even though Barry is bituminous, not PRB". **It is not, and the reason is structural
rather than incidental.** `apply_coal_supply_pricing` builds `price_by_supply` with
exactly two keys, `"lignite"` and `"prb"`, and does `price_by_supply.get(gen.coal_supply)`
— a `"bituminous"` row returns `None` and is skipped entirely. `coal_supply_by_iso("SOCO")`
tags **3 Barry, 26 Gaston and 703 Bowen `bituminous`**; only 6002 / 6073 / 6257 are `prb`.
Measured: Barry's rows are **not among the 15** that move at step 2 in any year, at max
\|Δ\| exactly 0.000000000000. **Barry unit 4's real defect — a gas-fired boiler paying a
coal fuel price — is untouched by this lane and stays routed**, exactly as 53f §9 item 4
left it. This lever is not its instrument.

---

## 5. G-DRIFT (rule 29(b)) — ZERO LIVE HUNKS, SO FORM 4 IS VALID AND NO CONTROL IS SOLVED

`git diff 04f7f849 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib scripts/replay_keeper.py
data/raw/_validation-source data/raw/reference` → **309 insertions over 5 files**,
decomposing into two upstream commits:

| commit | lane | object | classification |
|---|---|---|---|
| `aa4bb5b5` | caiso-288 | `caiso_citygate_blackout_bridge` + `data/fuel/hubs.py` bridge | **INERT** — new `bool = False`, ABSENT from the keeper's recipe, and its only consumer is the CAISO citygate daily path, which a SOCO run never enters |
| `3fc20b97` | MAC sidecar | `constants.REGIONAL_RENEWABLE_CF` + `PPA_COST_RECOVERY_YR`; `new_entry.py` `cf_override`/`life_override` | **INERT** twice over — both constants are consumed ONLY by `scripts/build_mac_sidecar.py` and `scripts/data/derive_regional_renewable_cf.py` (verified by grep over `src/` and `scripts/`), neither on the solve path; and `new_entry.py` is capacity evolution, which a `mode="backcast"` run never enters. Both new params default `None` and are byte-identical there |

**Zero LIVE hunks on SOCO's LP path.** The incumbent keeper was itself solved on the
**pinned** dependency set and **year-isolated** under rule 36, so it is a clean form-4
control and no control solve is spent. The three shards go to the ARM only.

**Cache-key inertness.** This lane adds no `ScenarioConfig` field — `coal_prb_proxy_own_iso`
has existed since nwpp-41 at `bool = False` with its frozen declared default `"False"` —
so no key moves at any default. `check_cache_key_registration` state is recorded in §9.

---

## 6. EX-ANTE PREDICTION, registered BEFORE the solve, with falsifiers that name the object

The A/B is **arm − KEEPER** (form 4; both per-year, both year-isolated, both on pinned
deps). Predictions P1 and P2 are unusually strong because §4 computed them rather than
estimated them — **that is the point**: a zero-LP method that can predict bit-identity is
worth more than one that predicts a band, and it is falsifiable in one comparison.

| # | prediction | falsifier |
|---|---|---|
| **P1** | **2023 IS BIT-IDENTICAL TO THE KEEPER'S 2023.** Every class-hourly cell, every price cell, every `marginal_emission_rate` cell, every annual class MWh: **max \|Δ\| exactly 0.000000**. Basis: `mc_base` is identical at full float precision over 327 × 8,760 cells, and for a SOCO backcast `fuel_prices` reaches the LP **only** through `mc_base` (its last functional use is `run_calibration.py:4990`, both `build_*_offer_surface_conditional_markup` calls, and both are PJM/CAISO-gated and off here). | **ANY** moved cell in 2023. That would mean either a solve-path channel for `fuel_prices` I have not found, or a G-DRIFT hunk I misclassified — and either stops this lane and goes to the owner. |
| **P2** | **2024 IS BIT-IDENTICAL TO THE KEEPER'S 2024**, on the same basis and the same falsifier. | As P1. |
| **P3** | **2025 MOVES, and only through Daniel's four moved tranche rows in hours 0–743.** `COAL_PRB` FALLS by **0.000–0.141 TWh** (the at-risk econ/peak energy in those hours; the `mustrun` 0.1265 TWh is floored and cannot move) and the displaced energy is picked up by **`CC_REGULAR` and/or `CT_PEAKER`**, which are what sits above a $33/MWh coal offer in a SOCO January. | `COAL_PRB` RISES in 2025, or falls by more than the **0.4108 TWh** displacement bound, or any class moves in a month other than January. |
| **P4** | **NO SCORED C1 ROW CHANGES VALUE IN ANY YEAR.** 2023 and 2024 are bit-identical (P1/P2) and 2025's C1 rows are SKIPPED for preliminary EIA-923. So: 2023 `CT_PEAKER` stays the single FAIL at **+9.73 TWh**, 2023 `ST_GAS` stays at **−6.93**, 2024 `CT_PEAKER` at **+5.81**, 2023/2024 `COAL_PRB` at **−2.13 / −3.44**. **THIS ARM DOES NOT FIX SOCO'S HEADLINE DEFECT AND DOES NOT WORSEN IT.** | Any C1 row changes value. |
| **P5** | **Determination `NOT-YET` (PRICE UNSCORED), identical to the keeper.** C2 / C4 / C6 / C8 PASS; C3a/b/c UNSCORABLE; **0 ledgered and 0 protective** caveats; C1 all **13/14**, free **9/10**; **DOF unchanged at 3 entries / 1 residual**; **zero `ScenarioConfig` fields and zero free parameters added**. | Any criterion changes status, any caveat appears, or the DOF ledger moves. |
| **P6** | **Rule 17 `[R-FLOOR-WINDOW]` HOLDS in all twelve `ST_GAS` plant-years**, every binding share at or below that plant's own measured synchronized share (3 → 0.063, 10 → 0.752, 26 → 0.639, 728 → 0.843, 2049 → 0.920), and **Barry keeps ZERO floored hours**. 2023 and 2024 reproduce the keeper's shares **exactly** (0.000/0.309/0.197/0.074/0.808 and 0.000/0.295/0.078/0.478/0.652) by P1/P2; only 2025 can move, and it **RISES or holds** — a dearer Daniel commits marginally more gas steam in P0 — bounded above by **+0.05** on any plant-year. | Any plant-year's share exceeds its own measured share, or Barry carries any floored hour, or any 2023/2024 share differs from the keeper's at all. **A miss here is a rule 17 finding and OUTRANKS this arm's gate result.** |
| **P7** | **The marginal emission rate is UNCHANGED in 2023 and 2024** (0.6255 / 0.5921 lw-mean, bit-identical by P1/P2) and **RISES in 2025** from 0.6161 by **0.0000 to +0.0050** lw-mean. Direction, and I am reasoning about **which machine sets the PRICE**, not which makes the energy — the mistake 53f's P9 made: a dearer Daniel is *withdrawn* from the margin in some of 744 hours and a gas CC (~0.37) or a peaker (~0.55–0.65) sets price instead. **Both signs are live**: coal→CC pushes the rate DOWN, coal→peaker pushes it UP, and 744 hours of one 552 MW plant cannot move an 8,760-hour load-weighted mean far either way. **I therefore predict the MAGNITUDE confidently and the SIGN weakly, and say so before the solve rather than after.** | 2023 or 2024 moves at all; or 2025's lw-mean moves by more than **0.010** in either direction. |
| **P8** | **`check_registry_payload_parity` is CI-GREEN for SOCO** and the local run lists only this session's own gitignored dirs. `audit_keepers --check --iso SOCO` fires **E13** on registration (fifth consecutive SOCO lane, §9) and E11 lineage; nothing else new. | A new gate class fires. |

**The determination is predicted UNCHANGED, and every scored number is predicted
UNCHANGED.** The arm is taken anyway, and that is rule 14 `[R-ACCURATE]` operating as
written: for **744 hours where SOCO has no measured price of its own**, the model
currently charges **Texas rail economics**, and SOCO's own market's filed receipts are
the accurate input. Rule 14's misalignment exception cannot apply — the pool is deeper
than the default it replaces (§3), nothing is gap-filled, and the plant being priced
contributes nothing to the number pricing it (§3.1). Rule 1 `[R-STRUCT]` is the other
half: this is a structural correctness repair whose bite happens to be small, and
**"it barely moves anything" is not a reason to arm it and not a reason to refuse it** —
the reason is that the input is right.

**STATED AT THE GATE, so it cannot be discovered later.** As a *posture* the arm's value
is forward-looking and larger than its 2025 bite: it makes SOCO's PRB fallback SOCO's own
in every future gap-month and in any year whose receipts are thinner. Its value **today**
is 744 hours of one plant in an unscored year. Both halves are the honest account.

---

## 7. WHAT THE SHARDS SOLVE, AND HOW EACH IS VERIFIED

**Rule 36 `[R-YEAR-ISOLATION]` (a) is the solve shape: ONE SHARD PER YEAR**, composed in
the parent at zero LP. This is the one place rule 32(b)'s fan-out ban does not apply, and
rule 34 `[R-SHARD-PROMOTABLE]` (a) makes it work — every shard pushes its FULL bundle
including `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet`.

**SOCO's registered year union is exactly {2023, 2024, 2025}** — enumerated from
`frontend/data/backcast/registry/*.json` **before** anything is pruned (rule 35(b)):
SOCO carries **ONE** registered run, `2026-09-20-soco53f-measured-coal-hr`, years
`[2023, 2024, 2025]`, `holdout: None`. No folded touchpoints, no dangling
`holdout.keeper`. Three shards cover the union in full (rule 34(c)); none is omitted.

| shard | year | out-dir | branch |
|---|---|---|---|
| A | 2023 | `results/calibration/soco53g_arm_2023` | `claude/soco53g-arm-2023` |
| B | 2024 | `results/calibration/soco53g_arm_2024` | `claude/soco53g-arm-2024` |
| C | 2025 | `results/calibration/soco53g_arm_2025` | `claude/soco53g-arm-2025` |

Each runs the keeper's own `meta.json` through `replay_keeper.py`, so the A/B is
**single-delta by construction** and no hand-typed flag list can drop a gate:

```
python3 scripts/replay_keeper.py results/calibration/soco53f_coal_hr \
  --years <Y> --out-dir results/calibration/soco53g_arm_<Y> \
  --set coal_prb_proxy_own_iso=true --note "soco-53g arm: coal_prb_proxy_own_iso"
```

**`--set` routing, declared before the solve.** `coal_prb_proxy_own_iso` is a
`ScenarioConfig` field but **NOT** a `solve_and_persist` kwarg (verified this session), so
`--set` routes it through the generic `prb_overrides` channel ONLY. The bundle's
`meta.json` will therefore record `coal_prb_sigmoid_overrides {} -> {"coal_prb_proxy_own_iso": true}`.
**That trips `audit_keepers` E11 at promotion. It is BENIGN** — the RESOLVED
`scenario_config.coal_prb_sigmoid_overrides` stays `null` and
`scenario_config.coal_prb_proxy_own_iso` reads `true` — and it is declared here, before
the solve, and will be declared again in the keeper shard's promotion prose, copying
SOCO-53f's wording.

**Hard stops in every shard prompt** (rule 32(c)(4)), each self-checkable:

1. `git rev-parse HEAD` == this PRECOMMIT's pinned **40-character** SHA. Never rebase,
   never `git pull`, never "sync".
2. `pip install -r requirements.txt --ignore-installed PyYAML`, then assert **highspy
   1.14.0 / numpy 2.4.6 / scipy 1.17.1 / pandas 3.0.3 / pyarrow 24.0.0 / pydantic
   2.13.4**. The `--ignore-installed PyYAML` is REQUIRED — Debian's PyYAML 6.0.1 has no
   RECORD file and aborts the whole install. This image ships without the scientific stack.
3. Config signature read back from `run_config.json` AFTER the solve:
   `coal_prb_proxy_own_iso: true`, and the keeper posture intact —
   `measured_coal_heat_rates: true`, `measured_ct_heat_rates: true`,
   `egrid_family_heat_rates: true`, `measured_st_heat_rates: true`,
   `soco_gas_st_campaign_commitment: true`, and **every `offer_curve_by_group` band
   exactly 1.0**. Anything else ⇒ **STOP, do not push.**
4. **BLOCK ON THE SOLVE** — foreground, no `nohup`, never end a turn with a solve running.

**Forbidden by name in every prompt** (rule 32(c)(6)): `git add -A`, `git add .`,
`git add -f`, `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
`prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under `src/`,
`scripts/` or `requirements.txt`, opening a PR, deleting any result (rule 31). And:
*"A shard that stops with a clear report is a SUCCESS; a shard that repairs
infrastructure is a FAILURE."*

Composition is the parent's, at zero LP (rule 32(d)), with
`scripts/probes/soco53f_compose_span.py --expect-coal true` extended by a
`measured_coal_heat_rates: True` `KEEPER_POSTURE` entry and a parameterised single delta.

---

## 8. WHERE THE KEEPER'S BYTES ARE — THE SHAs RESOLVE, WITH ONE CORRECTION

The handoff's recovery SHAs were to be verified before being relied on. **All three
resolve, but NOT from a default clone's refs** — `git cat-file -t` fails until each is
fetched explicitly, because the shard branches were auto-deleted:

```
git fetch origin <sha>        # required first; then
git checkout <sha> -- results/calibration/soco53f_arm_<year>
```

| leg | SHA | files | state |
|---|---|---|---|
| `soco53f_arm_2023` | `0f061987f1877f62339df72174c74fbf0e8b89da` | 16 | **RESOLVES** after explicit fetch |
| `soco53f_arm_2024` | `34d7131e98f6be0bdb463428f7c8bdb781a56b2e` | 16 | **RESOLVES** after explicit fetch |
| `soco53f_arm_2025` | `381ca2fc8b4827246f2e99f7f980157c84447fee` | 16 | **RESOLVES** after explicit fetch |

All three recovered in this session and re-composed at zero LP with
`soco53f_compose_span.py --expect-coal true`: posture OK on every leg, `coal=True`, bands
1.0, `dispatch/<y>_P1.parquet` present, `marginal_emission_rate` live
(26,280 / 26,280 / 26,241 nonzero), `solve_surface` fingerprint **`f4d250dfebdf2c96`**
identical across legs, `environment.packages` identical. **The keeper's full per-plant
layer is on this session's disk and a promotion costs ZERO re-solves.** Independently
confirmed against the committed slim bundle: `marginal_emission_rate` lw-mean
**0.6255 / 0.5921 / 0.6161**, reproducing `FINDING-soco-53f` §4.6 exactly.

---

## 9. GATES AND EXPECTED NOISE, recorded before the solve

| gate | expected state | why |
|---|---|---|
| `check_cache_key_registration` | **PASS** | no field added; `coal_prb_proxy_own_iso` already registered with frozen default `"False"` |
| `check_mechanism_matrix --base origin/main` | **PASS** | no new `ScenarioConfig` field; this lane stamps SOCO's own shard cell + §5.8 prose header |
| `audit_keepers --check --iso SOCO` | **E13 fires** on registration — **FIFTH** consecutive SOCO lane | a newly registered candidate is neither the keeper nor stamped to one, and E13 has no state for that. Clearing it would break rule 15, 31 or 30. **Re-raised, not worked around.** |
| `audit_keepers` E11 | fires (lineage + the `prb_overrides` recipe diff of §7) | expected and declared |
| `check_bench_freshness` | **RED repo-wide**, SOCO's three parts STALE | nyiso-240's EIA-923 repair; `FINDING-soco-53f` §7. Not this lane's. **SOCO's bench is NOT rebuilt**; `dashboard_add_run.py`'s auto-rebuild is reverted and `metrics.json` re-written on the committed bench, with **both** verdicts reported and labelled |
| `check_registry_payload_parity` | **CI-GREEN**; local RED listing only this session's own gitignored dirs | the gate walks the filesystem (`:437`) — rule 31's 2026-09-16 correction. **Nothing deleted** |
| `tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name` | **RED at HEAD** | verified independently of this lane's files; a naming-convention decision for the SOCO desk. NOT patched |
| `tests/unit/data` under profile `soco` | ~25 ABSENT-DATA failures | CAISO firm-import / NEISO fleet; A/B'd against `origin/main` before any is believed to be this lane's |

## 9.1 ALSO OWED BY THIS LANE, AND NOT DEFERRED

- **Rule 17 floors re-measurement** on this lane's own `floors/<year>_P1.npz`, the tool
  first validated by reproducing the keeper's 2023 row **0.000 / 0.309 / 0.197 / 0.074 /
  0.808** exactly (§6 P6).
- **`marginal_emission_rate`** confirmed live on every `hourly/system_<year>.parquet`,
  with per-year lw-mean, p10/median/p90 and zero-share against the keeper's baseline (§8).
- **Both benches reported, labelled** — committed and HEAD-rebuilt (§9).
- **The 858-field `scenario_config` lineage diff captured while both bundles are on disk,
  BEFORE any prune** (rule 35(b), §9).
- **Re-routed, not taken:** SOCO's never-derived `parasitic_load_factors`
  (`FINDING-soco-53f` §2.4 — coal meter 0.866–0.928 against the committed 0.93, so every
  SOCO coal heat rate is biased LOW by 1.5–5.9 %); SOCO-53b's 2025 hydro input hole
  (0.327 TWh modelled against 6.012 measured); Barry unit 4 (§4.4); and — **new from this
  lane** — the cross-ISO census below.
- **NEW AND ROUTED: `_prb_monthly_actuals`'s own docstring overstates its live
  footprint.** It records the ERCOT series as sticking to non-reporting PRB plants in
  "MISO (12 plants), PJM (2) and SPP (3–5) as well as NWPP (5)". At SOCO that census
  would have counted **3 plants** where the true live footprint is **one plant for one
  month**, because `coal_plant_monthly_pricing` + `nearby_fuel_price_fallback` overwrite
  the proxy wherever a receipt or a neighbour exists. **The census counts PRB plants; it
  does not count plant-months the overlay fails to reach, which is the quantity that
  matters.** Each of those ISOs' lanes should re-measure its own footprint the way §4.2
  does here before spending a solve — and nwpp-41's own NWPP arm deserves the same
  re-measurement. This is a method correction, not a verdict on any other ISO.
