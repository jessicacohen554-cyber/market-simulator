# PRECOMMIT — SOCO-53c: `egrid_family_heat_rates`, the completing plant-blend repair

**Lane** SOCO-53c · **Model** Opus 5 · **Date** 2026-09-19 ·
**Branch** `claude/soco-egrid-family-heat-rates-xvcows` · **Data profile** `soco` ·
**Incumbent keeper (the control of record)** `2026-09-17-soco53-measured-ct-hr`,
bundle `results/calibration/soco53_measured_ct_hr`, basis
`0f6bd1215b13dcc5a0fc4be5b5ab17dcb74330b1`.
**Predecessors** `FINDING-soco-53-2026-09-17.md` (§2 the inherited diagnosis, §6 this lane's
object, §7 the promotion record), `PRECOMMIT-soco-53-2026-09-17.md` (§2.2 the prediction pattern).
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 19 `[R-ONE-MECH]`, 20 `[R-FORCED-BUDGET]`, 21 `[R-DOF]`,
23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`,
29 `[R-SCREEN]`, 31 `[R-RETAIN]`, 32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`,
35 `[R-PROMOTE]`.

**Pushed before anything is solved.** Every number below is ZERO-LP: the keeper's committed
`hourly/` sidecars, `scripts/calibration_verdict.py` re-run on the committed bundle, the fleet
loaders called directly, the eGRID `PLNT23`/`UNT23`/`GEN23` sheets read directly, and the derive
script. **The parent ran no LP of any length** (rule 32(a)). The phase-0 findings, the construction
repair, the G-DRIFT audit, the arm and the ex-ante prediction are fixed here; nothing below is
revised after the solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json` carries **no
SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent` and silently moves SOCO onto the ordinary
determination path. C3a / C3b / C3c are **UNSCORABLE, not failed**. The ceiling is rubric v3.8
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can **never** read `CALIBRATED`. Scored on
**C1 / C2 / C4 / C6 / C8 only**. Gate **G17** absolute: no neighbouring hub, no proxy, no cost-stack
price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0 and `authorized_price_tuning` stays
declared NONE.** With no price benchmark there is no price residual, so the rule-1 authorized
channel is **unreachable here, not merely unused**. This lane touches no band, share, floor or
threshold.

---

## 1. PHASE 0 — THE MECHANISM IS RIGHT, AND ITS ARTIFACT WAS WRONG AT FIVE OF NINE PLANTS

### 1.1 The derive reproduces SOCO-53's evidence exactly

`scripts/data/derive_egrid_family_heat_rates.py --iso SOCO`, re-run against this lane's own
vintage, returns **18 (plant, family) rows over 9 covered plants, 12 applied** — the same 18 rows,
the same 12, and the same values FINDING-soco-53 §6 recorded (Barry ST 8.995 → 12.610 / CC →
7.821; Daniel ST → 12.895 / CC → 7.553; Greene GT → 14.105; Watson GT → 21.925). The inherited
evidence is confirmed rather than assumed.

### 1.2 Rule 19 `[R-ONE-MECH]` — the two heat-rate mechanisms are CLEANLY COMPLEMENTARY, with a mechanical precedence

The handoff asks whether `egrid_family_heat_rates` double-prices the CT rows
`measured_ct_heat_rates` already owns. **It does not, and the precedence is structural rather than
declared.** `_apply_egrid_family_heat_rates` runs at FRAME level in `_rows_to_generators`
(`eia860.py:1215`), immediately after the boundary repair and the simple-cycle floor;
`measured_ct_heat_rates` is resolved once and applied INSIDE the row loop (`eia860.py:1394`), gated
on `group == "CT_PEAKER"`. The row loop runs last, so **the measured CAMPD loaded rate overwrites
the family rate on every CT_PEAKER row and never the reverse**. The ordering is deliberate and
documented at the seam ("every class-specific measured mechanism downstream … keeps exactly the
precedence it has today").

**The precedence rule, stated once:** measured CAMPD loaded rate ▸ eGRID prime-mover-family rate ▸
eGRID plant blend. One row, one final rate, never a sum.

Machine-verified on the built fleet (393 generators, `measured_ct_heat_rates=True` on both sides):

| class | MW | control HR | arm HR | Δ |
|---|---|---|---|---|
| `CT_PEAKER` | 9,634.2 | 11.2666 | 11.2666 | **+0.0000** |
| `CC_REGULAR` | 18,652.9 | 7.4109 | 7.2449 | −0.1660 |
| `COAL` | 11,512.0 | 10.7834 | 11.5267 | +0.7433 |
| `ST_GAS` | 3,131.1 | 10.8151 | 10.9613 | +0.1462 |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | 746.6 / 336.4 / 197.1 | — | — | **+0.0000** |

`CT_PEAKER` is **byte-identical**, which is the mechanical proof: Greene County's GT family rate
(14.105) and Watson's (21.925) are both computed, both written, and both entirely overwritten by
the measured 12.849 / 14.266. Nothing is priced twice. The CHP classes read +0.0000 for the
separate reason in §1.3.

The stacking also has committed precedent — CAISO's and NYISO's keepers each carry
`measured_ct_heat_rates=True` **and** `egrid_family_heat_rates=True` today.

### 1.3 THE CONSTRUCTION REPAIR — the artifact's own central claim is TESTABLE, and it failed at five of the nine plants

The derive's docstring says the family rate "replaces the blend **on the identical net-annual
boundary**". That is not a description, it is an **identity**: `PLHTRT` is the same ratio over the
union of the families, so a decomposition on that boundary must recompose to it —

```
Σ_families HTIAN ÷ Σ_families GENNTAN  ==  PLHTRT
```

Run over SOCO's nine covered plants, the test partitions them **perfectly, with three orders of
magnitude to spare**:

| plant | Σ HTIAN ÷ Σ GENNTAN | published `PLHTRT` | ratio | |
|---|---|---|---|---|
| 3 Barry | 8.9950 | 8.9950 | **1.000** | same boundary |
| 10 Greene County | 10.4827 | 10.4827 | **1.000** | same boundary |
| 2049 Jack Watson | 10.4180 | 10.4180 | **1.000** | same boundary |
| 6073 Victor J Daniel Jr | 8.3995 | 8.3995 | **1.000** | same boundary |
| 10416 Pensacola Florida Plant | 22.5366 | 5.5680 | **4.048** | *** DIFFERENT *** |
| 54004 WestRock Southeast | 30.4697 | 5.5634 | **5.477** | *** DIFFERENT *** |
| 54802 Mead Coated Board | 31.6880 | 5.5119 | **5.749** | *** DIFFERENT *** |
| 54096 International Paper Riverdale Mill | 41.3008 | 5.5147 | **7.489** | *** DIFFERENT *** |
| 10361 Savannah River Mill | 50.5987 | 6.0210 | **8.404** | *** DIFFERENT *** |

**The five failures are cogeneration paper mills, and the cause is eGRID's own published
convention**: `PLHTRT`'s numerator is STEAM-CREDITED at a CHP plant (the useful thermal output's
heat input is netted out of `PLHTIAN`), while the unit sheet's `HTIAN` is raw fuel. So the family
rate there charges the host's process steam to the electric output. It is not a finer read of the
same number; it is a different number.

**The pre-existing `out_of_window` guard was NOT sufficient, and that is why this matters.** It is
a per-FAMILY plausibility test (3,000–30,000 Btu/kWh) and it caught only the steam halves
(35.3–134.1). The **turbine halves landed INSIDE the window and were applied**: Pensacola GT
11.655, WestRock GT 13.643, Mead GT 15.906, Riverdale CC 16.348 — **four rows, 160.0 MW, repriced
2–3× off a boundary that is provably 4–8× wrong**, onto `CT_CHP` (143.0 MW) and `CC_CHP` (17.0 MW).
`CC_CHP` is a scored C1 row (2023 PASS, +0.52 TWh).

This is **rule 14 `[R-ACCURATE]`'s misalignment exception, verbatim**: accurate data defined on a
different boundary than our representation, which used literally would make results *less*
reflective of reality. It is therefore refused rather than applied — and the model already owns the
CHP boundary through its own chain (`_correct_chp_steam_credit_hr`, `measured_chp_heat_rates`),
with `_apply_simple_cycle_hr_floor` carving CHP out on the identical ground in the same file.

**THE REPAIR, and where it deliberately is NOT.** A `boundary_mismatch` flag in the DERIVE
(`scripts/data/derive_egrid_family_heat_rates.py`), per PLANT — if the decomposition does not
recompose, no family of it is on the plant rate's boundary. **No `src/market_sim` file is touched
and no solve-path file moves**: the artifact schema is unchanged and
`eia860.egrid_family_heat_rates_for` already reads only `flag == "ok"`. A consumer-side guard was
considered and **REFUSED under rule 25 `[R-ISO-SCOPE]`** — it is default-on, so it would have moved
CAISO's keeper fleet from this lane (§1.5).

SOCO's re-derived artifact: **18 rows, 9 plants, 12 applied → 8 applied**, and the 8 are exactly
the four plants that recompose. `CC_CHP` / `CT_CHP` / `ST_CHP` are byte-identical in the arm as a
result (§1.2).

Zero free parameters. `BOUNDARY_IDENTITY_TOL = 0.005` is a rounding allowance for a published
figure, **not a tuned threshold and incapable of being one**: over all 26 covered plants in the
three ISOs that carry an artifact, the passing side sits at ratio 1.0000 (max deviation 5e-6, Jack
Watson) and the failing side starts at 2.800, so **every value in (0.001, 1.8) yields the identical
partition**. It is declared here, ex ante, and never swept. Guarded by two new tests in
`tests/unit/data/test_egrid_family_heat_rates.py`.

### 1.4 The Barry ST question the handoff raises — ANSWERED, and the answer is ACCEPTABLE

The handoff asks whether Barry's eGRID "ST" family blending its COAL unit with its gas boilers is
acceptable or a rule-14 misalignment. **It is acceptable, and the reason is measured rather than
argued.** The family key is prime mover, so Barry's ST family is a further FUEL blend — measured at
unit grain from `UNT23`/`GEN23`:

| Barry (3) ST family | own rate | share of the family |
|---|---|---|
| coal (units 4, 5 — BIT) | **11.699** | 79.6 % (1,692,397 MWh) |
| gas steam (units 1, 2 — NG) | **16.159** | 20.4 % (434,559 MWh) |
| **blended family rate applied** | **12.610** | |

So the applied rate is not either half's own. **The decisive test is whether it moves BOTH halves
toward their own truth, and it does — monotonically, with no trade:**

| Barry row | true | control (plant blend 8.995) | arm (family 12.610) | |
|---|---|---|---|---|
| coal, 1,118.5 MW | 11.699 | error **−2.704** | error **+0.911** | **3.0× closer** |
| gas steam, 160.0 MW | 16.159 | error **−7.164** | error **−3.549** | **2.0× closer** |

Rule 14's exception applies only where using the accurate data literally would make results *less*
reflective of reality. Here it makes both halves **more** so, so the exception does not apply and
the data is kept. Daniel (6073) has no such question at all — its ST family is its two SUB coal
units alone, so 12.895 is a pure coal rate.

**Named and NOT half-repaired (rule 19):** a FUEL-subfamily rate would be a *different* mechanism
with a new `ScenarioConfig` field and a new matrix row, and stacking it on this one in the same run
is exactly what rule 19 forbids. It is **routed**, with its numbers already measured above.

### 1.5 WHAT THIS MECHANISM DOES NOT REACH — stated at the gate, not discovered later

FINDING-soco-53 §6 names nine multi-technology plants. **The mechanism reaches four of them**, and
the other five are not oversights:

- **Gaston (26) — NOT COVERED, and NOT FIXABLE BY THIS CONSTRUCTION.** Its only family with both
  `HTIAN > 0` and `GENNTAN > 0` is `ST` (its single `GT4` row files 108 MWh of generation and no
  heat input), so it has one live family and its plant rate 11.551 **already is** its ST family
  rate. But Gaston's ST family is itself a fuel blend — **coal 12.111 (54.2 %) against gas steam
  10.887 (45.8 %)** — and a PRIME-MOVER family construction cannot separate two boilers. Gaston is
  the fuel-subfamily lever's object, not this one's.
- **McDonough (710) — NOT COVERED, correctly.** Its `GT` generators file **−52.0 MWh** each (net
  station service), so the family is not live; its plant rate 6.724 is already essentially its CC
  rate.
- **The five cogens** — covered, and now refused on the boundary identity (§1.3).

So the "26.0 % of thermal capacity" this lane inherited as its object is **repaired over 6,473.2 MW
(24 rows)**, not over all 11,777 MW. The remainder is named and routed.

---

## 2. THE ARM

```
uv run python scripts/run_calibration_full.py --iso SOCO --year 2023 2024 2025 \
    --measured-ct-heat-rates --egrid-family-heat-rates \
    --out-dir results/calibration/soco53c_family \
    --note "soco-53c: eGRID prime-mover-family heat rates at SOCO's four genuinely multi-technology plants, on this lane's own re-derive with the boundary-identity guard (rule 14 [R-ACCURATE]); measured_ct_heat_rates retained from the keeper; every offer band 1.0, authorized_price_tuning NONE"
```

No other flag. Years sequential inside one invocation (rule 12), one bundle (rules 16 / 32(b) /
34(c)). SOCO's registered year union, enumerated from `frontend/data/backcast/registry/*.json`
**before anything is pruned** (rule 35(b)): **{2023, 2024, 2025}** — one registered run, the keeper,
and the arm covers the same three years in its own bundle, so no `holdout.keeper` stamp is owed.

**Config signature the shard must see, as its hard stop:** `measured_ct_heat_rates: true`,
`egrid_family_heat_rates: true`, every `offer_curve_by_group` band exactly `1.0`,
`authorized_price_tuning` absent.

**What moves: 24 rows / 6,473.2 MW at four plants.**

| plant | class | fuel | MW | control | arm | Δ |
|---|---|---|---|---|---|---|
| 3 Barry | `CC_REGULAR` | gas_cc | 1,821.2 | 8.995 | **7.821** | −1.174 |
| 6073 Daniel | `CC_REGULAR` | gas_cc | 1,132.4 | 8.399 | **7.553** | −0.846 |
| 3 Barry | `COAL` (BIT) | coal | 1,118.5 | 8.995 | **12.610** | **+3.615** |
| 6073 Daniel | `COAL` (PRB) | coal | 1,004.0 | 8.399 | **12.895** | **+4.495** |
| 2049 Jack Watson | `ST_GAS` | gas_st | 721.0 | 10.418 | 10.413 | −0.005 |
| 10 Greene County | `ST_GAS` | gas_st | 516.1 | 10.483 | 10.256 | −0.226 |
| 3 Barry | `ST_GAS` | gas_st | 160.0 | 8.995 | **12.610** | **+3.615** |

**A coal unit at 8.399 MMBtu/MWh is not physically attainable** — Daniel's 1970s subcritical PRB
boilers measure 12.895 on their own meter. That, and not the residual, is why this arms.

Rule 13 `[R-MEASURED]`: a family's own annual heat input over its own net generation is a physical
characteristic that regenerates for a forward year from whichever eGRID vintage the join reads and
responds to changed conditions — an INPUT, never an outcome fed back. Rule 25 `[R-ISO-SCOPE]`:
SOCO's own artifact, derived from SOCO's own plants; no other ISO's number enters. Rule 21
`[R-DOF]`: **zero free parameters added** (§5).

---

## 2.2 EX-ANTE PREDICTION — registered BEFORE the solve, with falsifiers

Unlike SOCO-53, whose prediction was cleanly adverse on its target row, this arm's prediction is
**adverse-to-neutral on the gates and does NOT fix SOCO's headline defect.** That is registered
here rather than discovered afterwards.

**Cost basis.** SOCO coal: bituminous `COAL_PRICE_BASE["SOCO"]` $3.20/MMBtu escalated at 1 %/yr;
PRB `COAL_PRICE_PRB_BY_YEAR` $2.15 (2023) / $2.00 (2024–25). Gas $2.54 / $2.19 / $3.52 (the
PRECOMMIT-soco-53 §2.2 series). *Caveat carried, not hidden:* Daniel's PRB delivered price itself
rides the ERCOT-pooled proxy (§3, routed item), so the $/MWh magnitudes below carry that basis; the
heat-rate deltas above do not and are exact.

| 2023, fuel-only $/MWh | control | arm | Δ |
|---|---|---|---|
| Barry coal (BIT) | 28.78 | **40.35** | **+11.57** |
| Daniel coal (PRB) | 18.06 | **27.72** | **+9.67** |
| Barry CC | 22.85 | 19.87 | −2.98 |
| Daniel CC | 21.33 | 19.18 | −2.15 |
| Barry gas steam | 22.85 | **32.03** | **+9.18** |
| `CC_REGULAR` fleet mean (reference) | 18.82 | 18.40 | — |

**The crossings.** In 2023 **Daniel's 1,004 MW of PRB coal moves from BELOW the whole CC fleet
($18.06 vs $18.82) to clearly above it ($27.72)** — a hard crossing. **Barry's 1,118.5 MW of
bituminous coal moves from between CC and CT to above CT** (CT_PEAKER fuel-only $28.62). So
**2,122.5 MW of coal — 18.4 % of the 11,512 MW coal fleet — is repriced out of its current merit
position**, and **2,953.6 MW of CC is repriced down**.

**Where the displaced coal goes, measured from the keeper's own hourlies.** Against `CC_REGULAR`'s
own observed capability (its year maximum, not nameplate), headroom of ≥ 2,122.5 MW exists in
**5,535 / 8,067 / 7,828 hours (63.2 % / 92.1 % / 89.4 %)** of 2023 / 2024 / 2025. So the CC fleet
absorbs most of it.

**Therefore, per class:**

1. **`COAL` FALLS in all three years.** Bounded below by the coal `pmin = 0.4 × pmax` floor in
   committed hours. Predicted **−1 to −3 TWh each on `COAL_BIT` and `COAL_PRB`**, total coal
   **−2 to −5 TWh**. Both rows are currently UNDER (2023 −1.19 / −1.58 TWh; 2024 −0.02 / −2.79)
   against a ±7.19 / ±7.47 TWh band, so they move **toward the edge and away from the actuals** but
   should stay in band.
2. **`CC_REGULAR` RISES by approximately the coal decrease. THIS IS THE ROW AT RISK.** It is
   already **+2.28 TWh (2023) / +3.37 (2024)**; +2 to +5 TWh puts 2023 at +4.3…+7.3 and **2024 at
   +5.4…+8.4 against a ±7.47 TWh band**. **2024 `CC_REGULAR` is the most likely NEW C1 failure.**
3. **`CT_PEAKER` roughly UNCHANGED — this arm does NOT fix SOCO's gating defect.** Its own heat
   rate is byte-identical (§1.2), and it is not running because the CC fleet is exhausted:
   **`CC_REGULAR` sits at ≥ 99 % of its own annual maximum in only 44 of the 7,305 hours
   `CT_PEAKER` runs in 2023** (3 of 6,447 in 2024; 15 of 7,343 in 2025). CT's over-run is
   structural, exactly as SOCO-53 concluded, and a cost change at four other plants cannot reach
   it. Predicted **|Δ| < 1.0 TWh**; the 2023 `CT_PEAKER` row **stays FAILED**.
4. **`ST_GAS` roughly UNCHANGED**, the three moves near-cancelling (Barry's 160 MW dearer, Greene's
   516 MW slightly cheaper, Watson's 721 MW flat). Predicted **|Δ| < 0.5 TWh**; the 2023 `ST_GAS`
   row **stays FAILED**.
5. **`CC_CHP` / `CT_CHP` / `ST_CHP` BYTE-IDENTICAL**, by the §1.3 guard.

**So the registered expectation is: the two failing C1 rows do not improve, and C1 may acquire a
third failure on 2024 `CC_REGULAR`.** It is armed anyway, and that is not defiance of the brief —
it is rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]` operating as written, on a defect that prices
2,122.5 MW of coal at a heat rate no coal boiler can physically attain. Whatever the gates read
afterwards is reported at full magnitude and nothing is reverted.

**FALSIFIERS.**
- **F1.** If `COAL` does not fall in any year, the §2.2 cost construction is wrong and the FINDING
  says so rather than claiming a success.
- **F2.** If `CT_PEAKER` moves by more than **1.0 TWh** in either direction, the "CT is structural,
  not marginal" reading — inherited from SOCO-53 and re-measured here at 44 / 7,305 hours — is
  wrong, and that is the finding, not a bonus.
- **F3.** If any CHP class moves at all, the §1.3 guard did not hold and the artifact is wrong.

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — recorded BEFORE the solve, and it finds a LIVE hunk

`git diff 0f6bd1215b13dcc5a0fc4be5b5ab17dcb74330b1 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ **14 files, +3,162 / −812.**

| file | verdict | reason |
|---|---|---|
| `config/scenarios.py` | **INERT** | New `coal_prb_proxy_own_iso`, declared default `False`, registered on `_CACHE_KEY_OPTIONAL_FIELDS` **with its frozen drop value in the same commit**, so no existing config re-keys. |
| `pipeline/backcast_config.py` | **INERT** | `coal_prb_proxy_own_iso=(iso.upper() == "NWPP")`. **Verified mechanically**: `backcast_config(year=2023, iso="SOCO", …).coal_prb_proxy_own_iso` is `False`. |
| `data/coal.py`, `data/fuel/coal.py` | **INERT** | The ISO-scoped PRB pooling, reached only when that flag is True; at `False` `proxy_iso` is `None` and `_prb_monthly_actuals()` pools exactly the population it always did. |
| `scripts/lib/benchmark_semantics.py` | **INERT for this A/B** | `OIL_GROUPS` joins the 923/930 reconcile family (nyiso-239). It is a BENCHMARK-BUILDER change, and this lane deliberately does **not** rebuild SOCO's bench parts (§4), so the committed actuals both runs are scored against are byte-identical. **Routed**, not absorbed: whenever SOCO's bench is next rebuilt, its actuals may move. |
| `scripts/lib/bundle_fleet.py` | **INERT** | The `replay_keeper` fleet-only rebuild path; `run_calibration_full.py`'s solve path does not reach it. |
| `results/outputs.py`, `results/export.py`, `results/emissions.py`, `scripts/run_calibration_full.py` | **INERT for numbers, SCHEMA-CHANGING for sidecars** | Write-only: `hourly/system_<year>.parquet` gains `marginal_emission_rate`, `hourly/storage_<year>.parquet` gains `soc_mwh` / `energy_cap_mwh`. Presence-checked on read. The keeper's committed sidecars lack these columns, so differencing is done on the columns both carry. |
| `data/raw/reference/pjm_offer_midcurve_*` | **INERT** | A PJM offer artifact; SOCO reads no PJM file. |
| **`model/lp/model.py`, `model/lp/__init__.py`** | **🔴 LIVE — unresolvable by reading** | See below. |

### 3.1 The LIVE hunk, and why it earns a control solve

Commit `fba0ecd7` ("Emit the marginal emission rate from every solve") adds
`DispatchModel._marginal_emission_rate`, called **unconditionally** at the end of `solve()` for
every ISO, SOCO included. It freezes the cost-optimal basis, **swaps the objective to the CO2 rate
vector via `changeColsCost`**, sets `simplex_iteration_limit = 0`, and calls `h.run()` again to
read `r_B' B^-1` in row order; the basis and the iteration-limit option are restored in a `finally`,
and `objective_value` / `status` are now read *before* it.

It is carefully reasoned and is **designed** to be a no-op — zero iterations means no pivot, and
the next pass reinstalls the cost vector through `changeColsCost`. Its commit message states
"every keeper re-scores byte-identically", **but that is a SCORER claim over committed artifacts,
not a re-solve**: no ISO was re-solved to test it, and this lane is the first solve on any ISO past
that commit that would notice. The residual risks are real ones — HiGHS internal state after a
zero-iteration run under a swapped objective, the P0→P1 warm start, and `export_cross_year_basis`.

**Rule 29(b) is explicit: "A LIVE hunk is the only thing that earns a control solve."** This lane
therefore **spends one**, and pairs it:

- **CONTROL** — `results/calibration/soco53c_control`, the incumbent keeper's recipe **exactly**
  (`--measured-ct-heat-rates` and nothing else), at this lane's pinned SHA.
- **ARM** — `results/calibration/soco53c_family`, the same plus `--egrid-family-heat-rates`, at the
  same SHA.

Both are `--year 2023 2024 2025`, one invocation, one bundle each, and both PUSH their bundles
(rule 34(a)). They are **independent invocations with their own `--out-dir`s and are launched
CONCURRENTLY** (rule 12 `[R-PARALLEL]`; SOCO's measured span is ~11 min wall at 2.65 GiB cgroup
peak, so two fit comfortably). The derive change is inert for the control by construction — with
`egrid_family_heat_rates` off the artifact is never read — so the pair is a clean single-variable
A/B **at HEAD**, immune to any hunk above that this audit has misclassified.

**This buys a second thing the lane reports either way:** differencing the control against the
keeper's committed bundle is the first direct test of `fba0ecd7`'s byte-identity claim on a real
ISO. That result is a cross-ISO finding whichever way it lands.

SOCO-53's own inherited G-DRIFT precedents are re-verified and still hold: `_is_pool_region("SOCO")`
is `False` and `_POOL_HOURLY_MEMBERS` has the single key `NWPP`, so the eia930 pool path is always
inert for SOCO; and SOCO solves 2023–2025 on served measured EIA-930 interchange with no priced
`NeighborInterface`.

---

## 4. WHAT THIS LANE DELIBERATELY DOES NOT DO

- **SOCO's bench parts are NOT rebuilt.** `check_bench_freshness` is RED on **44 of 44 parts across
  every ISO**, pre-existing and another lane's (commit `ed96378e`, caiso-284, editing
  `scripts/render_calibration_html.py`, a `PAYLOAD_SOURCE`). Rebuilding SOCO's would score the arm
  against a different benchmark from its control. **Named; left.**
- **No other ISO's artifact is re-derived.** CAISO's committed
  `egrid_family_heat_rates_CAISO.csv` carries **Torrance Refining (50624)** at ratio 2.800 with
  **two applied rows** (ST 3.412 / GT 16.201), inside the CAISO keeper
  `2026-09-12-caiso-275-gascoupling`. **Routed to the CAISO desk, not touched** (rule 25). NYISO's
  artifact `--check`s **MATCH** — all seven of its covered plants recompose at 1.000, so the guard
  is a strict no-op there, machine-verified. The exposure is pinned by an intentionally TIGHT
  assertion in `tests/unit/data/test_egrid_family_heat_rates.py`, so it cannot rot into a permanent
  carve-out: re-deriving CAISO fails the test until the entry is deleted.
- **No `actual_lmp.json` block, no proxy, no cost-stack price** (gate G17).
- **No band, share, floor or threshold is touched.** No fuel-subfamily mechanism (§1.4, rule 19).
  No commitment mechanism — SOCO-53d remains open and is not this lane's.
- **No result and no shard branch is deleted** (rules 31 / 33(f)).
- **`soco15_spp_arm`** — a dead committed bundle in the SOCO namespace holding
  `check_registry_payload_parity` RED. **Named; NOT deleted**; the owner has not ruled (rule 31).

---

## 5. DOF ledger (rule 21 `[R-DOF]`) — unchanged at n_entries 3 / n_residual 1

This lane adds **no free parameter**. `offer_curve_by_group` stays at the identity on all 13
groups; `offer_curve_smoothing` stays unset; the single inherited residual entry
(`wefor_multiplier` = 0.7, audit C-15) is untouched. `egrid_family_heat_rates` is a
**measured-physical** input — each family's own Σ`HTIAN` ÷ Σ`GENNTAN` from the same eGRID vintage
the plant-grain join already reads, with zero degrees of freedom. `BOUNDARY_IDENTITY_TOL` is a
declared rounding allowance with a measured three-order-of-magnitude margin and **no value in that
range changes any outcome** (§1.3); it is a derive-script construction constant, not a solve
parameter, and it is never swept. `authorized_price_tuning` is declared **NONE** and is unreachable
in principle here.

## 6. ROUTED FROM PHASE 0 (carried into the FINDING)

| item | to |
|---|---|
| **CAISO 50624 Torrance Refining** — 2 applied rows on a 2.800 boundary mismatch, inside the live CAISO keeper | CAISO desk |
| **NWPP-41's ERCOT-pooled PRB proxy reaches SOCO too** — SOCO has three PRB plants (6002 Miller, **6073 Daniel**, 6257 Scherer) and the default pool is seven **Texas** plants. NWPP-41's own census named MISO (12), PJM (2) and SPP (3–5) and **missed SOCO** | SOCO desk |
| **Gaston (26)'s coal/gas-steam ST blend** (12.111 vs 10.887) — unreachable by a prime-mover-family construction; the fuel-subfamily lever's object | SOCO desk |
| **`benchmark_semantics.OIL_GROUPS`** — SOCO's actuals may move whenever its bench is next rebuilt | SOCO desk |
| `fba0ecd7`'s byte-identity claim, tested for the first time by this lane's control | cross-ISO / governance |
