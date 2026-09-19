# FINDING — SOCO-53e (2026-09-19): a per-unit meter separates two boilers that share a prime mover, and the lever is a fifth the size it was routed at

**Lane** SOCO-53e · **Model** Opus 5 · **Date** 2026-09-19 ·
**Branch** `claude/soco-st-gas-heat-rates-wfiz0w` · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53e-2026-09-19.md` (pushed at
`cc1bcb24e11a719c4d02ac3ea75834d988f0ceab`, before the solve) ·
**Control** `2026-09-19-soco53d-campaign-commitment`, bundle
`results/calibration/soco53d_campaign`, basis `0b3f2fdc` ·
**Run** `2026-09-19-soco53e-measured-st-gas`, bundle `results/calibration/soco53e_st_hr`,
recoverable in full at `884dca3132e8d1d1e1f18fbb789c356506a4e343`.

---

## 1. HEADLINE

A southeastern steam station is routinely **a coal boiler and a gas boiler behind one ORIS code**,
and because both machines are prime mover `ST`, the eGRID **plant** rate blends them *and so does
the prime-mover-**family** rate this lane's own predecessor armed*. Only a per-unit meter can
separate two boilers inside one family. `ScenarioConfig.measured_st_heat_rates` does that, and at
E C Gaston it moves 1,020 MW of gas steam from a coal-blended **11.5505** to its own metered
**11.0744** — which independently reproduces the **10.887** eGRID gas-steam *sub*-family rate
SOCO-53c routed as a separate lever, so this mechanism **subsumes** it.

**The lane's first act was to correct the number that commissioned it, before spending an LP.**
`FINDING-soco-53d` §8.1 routed *"+0.539 MMBtu/MWh, +5.2 %, too dear on 3,131 MW … worth
$1.5–3.3/MWh."* That figure converted SOCO's **boilers** at the `CT_PEAKER` parasitic factor
**0.99**; the `ST_GAS` class factor is **0.95**. On the right basis the capacity-weighted level
moves **10.9613 → 10.8522, −1.0 %**, and the delivered displacement is **an order of magnitude
below the routing**. The lever is real; it is a fifth the size it was sold at.

**The gates do not move, and every scored row improves.** Determination **`NOT-YET`** (rubric v3.8,
PRICE UNSCORED) on both sides, C1 all **13/14** · free **9/10** on both sides, C2/C4/C6/C8 PASS,
0 ledgered and 0 protective caveats, **zero free parameters added** (DOF 3 entries / 1 residual,
unchanged). 2023 `CT_PEAKER` stays the single failure at **+9.82 TWh**, so **SOCO's headline defect
is not fixed** — which the PRECOMMIT said first, with the number.

**The owner ruled `Promote` and it is executed** (§10): SOCO's keeper is now
`2026-09-19-soco53e-measured-st-gas`, the outgoing keeper's three stores are pruned, and
`audit_keepers --check --iso SOCO` returns **0 failures**. The promotion also surfaced a defect
that is this lane's own — the solve shard ran on **unpinned** dependencies, including HiGHS 1.15.1
against the control's pinned 1.14.0 — which is reported at full magnitude in §10.2 with the
evidence that bounds it — and which is **not** closed, because the pin-confirm re-solve was
abandoned unfinished (§10.3).

---

## 2. THE MEASUREMENT, AND THE BASIS ERROR IT CORRECTS

### 2.1 The parasitic class, settled by measurement rather than convention

`hr_net = hr_gross / factor`, so the class of the factor is the whole of the level. Phase 0
re-derived from scratch rather than inheriting, and **reproduced SOCO-53d's table to ±0.03 at
0.99** — so 53d's arithmetic was right and its *class* was wrong. The basis is then settled on
SOCO's own meter: EIA-923 `ST`/`NG` net generation over CAMPD gas-boiler gross, per plant-year.

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| 10 Greene County | 0.9400 | 0.9390 | 0.9345 |
| 2049 Jack Watson | 0.9431 | 0.9413 | 0.9393 |
| 728 Yates | 0.9402 | 0.9431 | *(no 923 row)* |
| 26 E C Gaston | 0.9821 | 0.9403 | **1.2454** ✗ |
| 3 Barry | 0.9445 | **1.0344** ✗ | **1.1634** ✗ |

The eight unambiguous plant-years cluster at **0.938–0.943**. (A factor above 1.0 is impossible, so
the three rejected cells are EIA-923 attribution defects; Barry's `ST`/`NG` rows also cover unit 4,
which is out of this population.) **The committed `ST_GAS` class default 0.95 reproduces that to
1.2 %; the `CT_PEAKER` default 0.99 misses it by 5.5 %.** The committed chain is used — per-plant
map first, class default otherwise — exactly as the coal sibling uses its own, so the derived rate
and the generation it is scored against share one convention and no new number is introduced.

### 2.2 The corrected artifact

`campd_st_heat_rates_SOCO.csv`, sha256[:16] **`3755b4becfd9f460`**, **5 of 5 plants / 3,131.1 of
3,131.1 MW = 100 % of `ST_GAS` capacity**, 160,139 in-band steady boiler hours at 12 units,
AL/GA/MS 2023–2025:

| plant | ST_GAS MW | units | steady h | gross | **net (applied)** | model | Δ | flag |
|---|---|---|---|---|---|---|---|---|
| 26 E C Gaston | 1,020.0 | 4 | 45,317 | 10.5207 | **11.0744** | 11.5505 | **−0.4761** | `ok` |
| 2049 Jack Watson | 721.0 | 2 | 42,287 | 9.8416 | **10.3596** | 10.4128 | −0.0532 | `ok` |
| 728 Yates | 714.0 | 2 | 36,397 | 10.2568 | **10.7966** | 10.8138 | −0.0172 | `ok` |
| 10 Greene County | 516.1 | 2 | 33,617 | 9.6969 | **10.2073** | 10.2562 | −0.0489 | `ok` |
| 3 Barry | 160.0 | 2 | 2,521 | 13.2853 | **13.9845** | 12.6100 | **+1.3745** | `ok` |

**Capacity-weighted 10.9613 → 10.8522 (−1.0 %)**, generation-weighted 10.7229 → 10.6004 (−1.1 %).
The level barely moves; the per-plant structure moves a great deal, and that is the finding.

**Barry moves the other way and is applied at full magnitude.** Two 1954-vintage 80 MW boilers,
metered at 13.98 over 2,521 steady hours with **98 % of their operating hours inside the physical
band** — a genuinely poor machine run 1.6 % of the time, not a meter artifact. Rule 14's
misalignment exception does **not** apply: unlike SOCO-53c's cogens, this rate is on the *same*
boundary as the rate it replaces. It independently corroborates SOCO-53d's campaign-duty gate
refusing Barry at a 6.3 % synchronized share — two instruments, one conclusion: Barry's small
boilers are standby iron.

### 2.3 Membership, and why the coal sibling's fuel tag cannot be used

CAMPD files **Barry unit 4 — a 330 MW boiler — as *Pipeline Natural Gas***, while the model carries
it as a **362 MW `COAL` row**. A `primaryFuelInfo` selection would therefore price the model's two
80 MW `ST_GAS` rows off a boiler the model dispatches as coal; `unitType` cannot separate them
either, since both are boilers. **The model's own class assignment governs, because the rate is
applied to model rows.** Each plant's CAMPD boiler units are paired to that plant's own model
boiler rows (`COAL` ∪ `ST_GAS`) by descending capacity — SOCO-53d's device — and only the `ST_GAS`
partners are kept. All 15 pairs fall in a capacity ratio of **[0.750, 1.059]**, and every
membership decision is separated by a factor of ≥ 2.8.

**The pairing cannot change an applied number, and that is checked rather than asserted.** The
artifact is at plant grain, so a within-plant permutation is inert; `--check-pairing` re-runs
membership under an exact generator-id-first rule (which pairs Gaston differently *inside* the
plant) and reports **`applied plant rows identical: True`**.

---

## 3. RULE 19 `[R-ONE-MECH]`, ESTABLISHED MECHANICALLY AT TWO GRAINS

**Built fleet** (393 rows, keeper recipe ± the field): row set, `pmax`, `pmin`,
`emission_rate_co2`, `vom`, `plant_group`, `fuel_type`, `zone` all identical; `heat_rate` moves on
**exactly 12 rows**, all `ST_GAS`; every other class at max |Δ| **0.000000000000** — COAL (16),
CT_PEAKER (100), CC_REGULAR (90), CC_CHP (14), CT_CHP (14), ST_CHP (13).

**LP rows** (`mc_base`, 327 rows): **20 of 327 move, all `ST_GAS` tranche rows**; COAL (28),
CT_PEAKER (89), CC_REGULAR (67), CC_CHP (14), CT_CHP (14), ST_CHP (11) and hydro (42) at max |Δmc|
**0.0000000000**.

The three measured-rate mechanisms are disjoint by construction — `measured_ct_heat_rates` gates on
`group == "CT_PEAKER"`, `measured_coal_heat_rates` on `== "COAL"`, `measured_st_heat_rates` on
`== "ST_GAS"`, and a row resolves to one group. The frame-level `egrid_family_heat_rates` runs
earlier, so this field **replaces** the family rate on the rows it covers rather than stacking.
**No row is priced twice.**

---

## 4. WHAT THE RUN DELIVERED

### 4.1 Class volumes, arm − control (TWh)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`ST_GAS`** | **+0.0897** | **+0.1878** | **+0.0846** |
| **`CT_PEAKER`** | **−0.0761** | **−0.1769** | **−0.0789** |
| `COAL_PRB` | −0.0170 | −0.0022 | −0.0033 |
| `CC_REGULAR` | −0.0012 | −0.0085 | −0.0070 |
| `COAL_BIT` | +0.0000 | −0.0003 | +0.0037 |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | +0.0000 / −0.0000 / +0.0000 | +0.0000 / −0.0000 / +0.0000 | +0.0000 / −0.0001 / +0.0000 |
| nuclear, hydro, wind, solar, biomass, oil | **0.0000** | **0.0000** | **0.0000** |

`ST_GAS` by plant (ctl → arm): **2023** p3 0.0038→0.0010, p10 0.5722→0.5742, **p26 0.4598→0.5622**,
p728 0.1111→0.1120, p2049 2.3644→2.3516 · **2024** p3 0.0096→0.0007, **p10 0.4249→0.5490**,
p26 0.2136→0.2456, p728 0.9465→0.9555, p2049 1.8858→1.9174 · **2025** p3 0.0671→0.0376,
p10 0.5919→0.6019, **p26 0.2068→0.2822**, p728 0.9484→0.9570, p2049 1.9175→1.9377.

### 4.2 The scored C1 rows — every one improves

| year | class | control model / actual / Δ | arm model / actual / Δ | ctl | arm |
|---|---|---|---|---|---|
| 2023 | `CT_PEAKER` | 14.432 / 4.534 / **+9.90** (+4.12pp) | 14.356 / 4.534 / **+9.82** (+4.09pp) | **FAIL** | **FAIL** |
| 2023 | `ST_GAS` | 3.511 / 10.483 / −6.97 (−2.91pp) | 3.601 / 10.483 / −6.88 (**−2.88pp**) | PASS | PASS |
| 2024 | `CT_PEAKER` | 11.338 / 4.785 / +6.55 (+2.62pp) | 11.161 / 4.785 / +6.38 (+2.54pp) | PASS | PASS |
| 2024 | `ST_GAS` | 3.480 / 8.879 / −5.40 (−2.17pp) | 3.668 / 8.879 / −5.21 (−2.10pp) | PASS | PASS |

**The row at risk got safer, not riskier.** The handoff flagged the 2023 `ST_GAS` row as passing by
only 0.09pp of share margin and able to cross back out. Against its ±3.00pp band the margin
**widens to 0.12pp**, and the volume margin from 0.22 to 0.31 TWh. The 2025 `CT_PEAKER` and
`ST_GAS` rows are SKIPPED by the scorer on the preliminary EIA-923 vintage (17 of 23 and 1 of 7
plants unfiled), so 2025 is **reported but not gated** — and those are the two rows this lane moves
most.

### 4.3 Gates

| | control | arm |
|---|---|---|
| determination | `NOT-YET` (PRICE UNSCORED) | `NOT-YET` (PRICE UNSCORED) |
| C1 | FAIL, 1 row (2023 `CT_PEAKER`) | FAIL, 1 row (2023 `CT_PEAKER`) |
| C1 all · free | **13/14 · 9/10** | **13/14 · 9/10** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C3a / C3b / C3c | UNSCORABLE | UNSCORABLE |
| `grade_summary` | scored 5, target 4, fails 1 | scored 5, target 4, fails 1 |
| caveats | 0 ledgered, 0 protective | 0 ledgered, 0 protective |
| DOF | 3 entries / 1 residual | **unchanged** |

C2's ungated 2025 coal row moves +12.1 % → +12.2 %; 2025 gas +1.6 %, unchanged. C5a (reported-only,
not gating) is −6.0 % / −10.0 % / +3.9 %, unchanged from the control.

### 4.4 The owed rule-17 re-measurement — performed, and it holds

SOCO-53d §8.1 recorded that its rule 17 `[R-FLOOR-WINDOW]` evidence was measured on a P0 pattern
priced with the wrong `ST_GAS` heat rate, and owed a re-measurement once this arm landed. **This is
a genuine test**: the campaign floor reads a P0 pattern this arm perturbs, and a cheaper Gaston
runs more in P0. Measured on this bundle's own `floors/<year>_P1.npz` (the tool first validated by
reproducing the control's §4.5 table exactly):

| plant | 2023 bind / meas | 2024 | 2025 | median floored block (h) |
|---|---|---|---|---|
| 2049 Jack Watson | 0.808 / 0.920 | 0.652 / 0.920 | 0.762 / 0.920 | 194 / 161 / 172 |
| 728 Yates | 0.134 / 0.843 | 0.536 / 0.843 | 0.749 / 0.843 | 459 / 216 / 341 |
| 10 Greene County | 0.312 / 0.752 | 0.300 / 0.752 | 0.506 / 0.752 | 202 / 388 / 321 |
| 26 E C Gaston | 0.203 / 0.639 | 0.106 / 0.639 | 0.184 / 0.639 | 112 / 138 / 87 |
| **3 Barry** | **0.000** / 0.063 | **0.000** / 0.063 | **0.000** / 0.063 | — |

**Zero exceedances in all twelve plant-years.** Barry still carries zero floored unit-hours, the
floored blocks keep a median of **87–459 h** (campaigns, not gap fills), the mechanism still touches
`ST_GAS` and nothing else, and D-4's off-window share is **exactly 0.0** in all three years.
`ST_GAS` forced share **0.0917 / 0.0999 / 0.1157** against the 30 % merchant cap, so C8 passes on
the budget.

### 4.5 D-1 is MIXED, and this lane claims no shape win

| year | `cv_ratio` ctl → arm | model off-peak CV ctl → arm | actual | `profile_r` |
|---|---|---|---|---|
| 2023 | 1.942 → **2.026** (worse) | 0.545 → 0.569 | 0.281 | 0.984 |
| 2024 | 2.499 → **2.413** (better) | 0.658 → 0.635 | 0.263 | 0.992 |
| 2025 | 2.166 → **2.091** (better) | 0.448 → 0.432 | 0.207 | 0.981 |

Two years improve, one degrades; all six clear the ≥ 0.5 gate and `profile_r` stays far above its
0.8 floor, so D-1 passes on both sides. Unlike SOCO-53d — whose *object* was the conduct — this
lane's object is the cost of a machine, and shape is a second-order consequence. It is reported as
mixed rather than framed as a win.

### 4.6 Marginal emission rate

Every `hourly/system_<year>.parquet` carries `marginal_emission_rate`. P1 load-weighted mean
**0.6263 / 0.6090 / 0.6369** tCO2/MWh on the arm against **0.6240 / 0.6092 / 0.6363** on the
control; p10 / median / p90 **0.4187 / 0.5905 / 0.8194** (2023), **0.3833 / 0.5818 / 0.8717**
(2024), **0.3833 / 0.5848 / 1.0896** (2025); zero-share **0.00 / 0.00 / 0.15 %**, unchanged. The
mean moves by at most 0.0023 and every percentile is unchanged or within 0.003 — the expected
signature of swapping one thermal machine's cost for another at a near-identical emission rate.

---

## 5. THIS LANE'S OWN PREDICTIONS, SCORED HONESTLY

| # | prediction | outcome |
|---|---|---|
| P1 | `ST_GAS` rises +0.02 to +0.35 TWh every year | **CONFIRMED**: +0.0897 / +0.1878 / +0.0846. Delivered slightly ABOVE §4.2's economic upper bound in all three years, which is the floor amplification the band was widened for. |
| P2 | `CT_PEAKER` falls 0.01–0.30 TWh; the 2023 row stays FAILED above +9.5 TWh | **CONFIRMED**: −0.0761 / −0.1769 / −0.0789; 2023 stays FAILED at +9.82. |
| P3 | `CC_REGULAR` moves < 0.10 TWh, no status change | **CONFIRMED**: −0.0012 / −0.0085 / −0.0070. |
| P4 | C1's failing-row SET unchanged; C1 all 13/14, free 9/10 both sides; NOT-YET both sides | **CONFIRMED exactly.** The named live risk — the 2023 `ST_GAS` row crossing back out on its 0.09pp margin — did not fire; the margin widened to 0.12pp. |
| P5 | Barry's energy falls every year, below 0.01 TWh in 2023 and 2024 | **CONFIRMED exactly**: 0.0038→0.0010, 0.0096→0.0007, 0.0671→0.0376. |
| P6 | Rule 17 holds in all twelve plant-years; Barry keeps zero floored hours | **CONFIRMED exactly** (§4.4). |
| P7 | C8 passes with `ST_GAS` forced share in 0.08–0.16 | **CONFIRMED**: 0.0917 / 0.0999 / 0.1157. |
| P8 | CHP / non-thermals < 0.001 TWh; COAL < 0.20 TWh | **CONFIRMED**: max \|Δ\| on any CHP class 0.0001; nuclear / hydro / wind / solar / biomass / oil exactly 0.0000; COAL max 0.0170. |
| P9 | 2023 marginal p90 rises or unchanged; lw-mean moves < 0.01 | **CONFIRMED**: p90 unchanged at 0.8194; lw-mean moves +0.0023 / −0.0002 / +0.0006. |

**Nine of nine hold.** That is a better record than either predecessor's, and it is worth saying
why rather than claiming credit: this lane's object is a *cost input whose effect is computable
without an LP*, so the offer-array delta and the headroom-capped hourly displacement bound could be
measured before the solve. The arm's delivered per-plant `mc` reproduced the zero-LP prediction to
four decimals (Gaston 41.4971 against 41.497; Barry 50.5564 against 50.556). SOCO-53d's object was
a commitment floor, whose effect runs through a P0 pattern no offline estimator reproduces — which
is exactly why its P5 missed by a factor of two. **The lesson is about what is predictable, not
about care.**

---

## 6. A/B INTEGRITY, AND THE BENCH POSTURE

**G-DRIFT (rule 29(b) form 4).** `git diff 0b3f2fdc HEAD` over the solve path returns 720
insertions across 10 files, decomposing **exactly** into three upstream commits, every one
classified INERT with its reason in PRECOMMIT §3: caiso-287's `--persist-p0-dispatch` (CLI opt-in,
write-only, `if "p0_dispatch_mw" not in p2_state: return []`), spp-48's `mid_vintage_exit_carry`
(default off, absent from the recipe, every consumer short-circuits), and nwpp-42's
`measured_coal_heat_rates` (default off, absent from the recipe, **and** a strict no-op here since
`campd_coal_heat_rates_SOCO.csv` does not exist). **No control solve was spent.** Both inherited
precedents were re-verified rather than assumed: SOCO is absent from
`eia930/frames.py::_POOL_HOURLY_MEMBERS`, and the keeper's `run_config.json` records
`measured_coal_heat_rates: None`.

**Cache-key inertness, measured.** Over all **21** committed `run_config.json` on disk, **zero keys
move** at the new field's declared default and **all 21** key distinctly when armed.
`check_cache_key_registration.py` passes (856 fields, 311 registered, all declared defaults match
HEAD).

**SOCO's bench parts were deliberately NOT rebuilt.** `dashboard_add_run.py` auto-rebuilds the parts
for a run's years as a side effect of registering; those rebuilds were **reverted** and
`metrics.json` re-written on the committed bench, exactly as SOCO-53c and SOCO-53d did.
`check_bench_freshness` is red repo-wide from `ed96378e` (caiso-284) editing
`render_calibration_html.py`, a `PAYLOAD_SOURCE`; this lane touched no fingerprint source, and
rebuilding SOCO's alone would have scored the arm against a different benchmark from its control
and destroyed the form-4 comparison. **Recorded for the owner: on the rebuilt bench the arm reads
the same determination, the same single 2023 `CT_PEAKER` failure (+9.83 TWh / +4.1pp) and the same
C1 all 13/14 · free 9/10.**

---

## 7. ROUTED

1. **`measured_coal_heat_rates` for SOCO — and this arm CREATES the reason.** Gaston's blended ST
   family rate 11.5505 is carried by its `COAL` row (26_5, 832 MW) as well as by its four gas
   boilers. Repricing only the gas side leaves the coal boiler on a rate the same arithmetic says
   is roughly 0.5 MMBtu/MWh too **cheap** for a coal machine. The mechanism already exists at HEAD
   (nwpp-42) and needs only a SOCO artifact — `scripts/data/derive_campd_coal_heat_rates.py --iso
   SOCO`. Stacking it here would be the rule 19 violation §3 spent its evidence disproving. **This
   is the obvious next SOCO lever and it is cheap.**
2. **`parasitic_load_factors.parquet` has no SOCO plants.** `derive_parasitic_load.py` covers 544
   plants across other ISOs and has never been run for SOCO, so every SOCO plant falls back to a
   class default. This lane measured 0.938–0.943 against the 0.95 default for gas steam — close,
   but a per-plant measured factor is strictly the better rule-14 input. It is a **cross-ISO data
   intake** (the artifact re-keys seven ISOs), not a lane's call.
3. **Barry unit 4** — 362 MW the model prices as coal and CAMPD files as gas. Unchanged from
   SOCO-53d, and this lane *depends* on the current assignment rather than changing it (§2.3).
4. **E C Gaston's fuel-subfamily lever is SUBSUMED, not open.** Two independent sources now agree
   its gas boilers sit near 11.0 (CAMPD 11.0744; the eGRID gas-steam sub-family 10.887), and a
   per-unit meter does at unit grain what a sub-family construction was proposed to approximate.
   The routing is closed.
5. **SOCO-53b — the 2025 EIA-923 hydro input hole**, unchanged; hydro is byte-identical here.
6. **NWPP-41's ERCOT-pooled PRB proxy reaches SOCO** (6002 Miller, 6073 Daniel, 6257 Scherer);
   `coal_prb_proxy_own_iso` is a cheap rule-14/25 data lever.
7. **`test_soco_token_collides_with_no_other_raw_name` gains one more offender and was NOT
   patched.** RED at HEAD; this lane's artifact follows the established convention
   (`campd_st_heat_rates_SOCO.csv`). Verified: it fails identically with and without this lane's
   file. The fix is a naming-convention decision across every SOCO artifact and belongs to the SOCO
   desk.
8. **`soco15_spp_arm`** — a dead but COMMITTED bundle in the SOCO namespace holding
   `check_registry_payload_parity` RED in CI. **Not deleted** (rule 31 — the owner has not ruled).
   **This is a question for the owner**, put in §10.

---

## 8. GATES

| gate | state |
|---|---|
| `check_cache_key_registration` | **PASS** — 856 fields, 311 registered, all declared defaults match HEAD |
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, anchors (0 unresolvable), keeper stamps, §5.x prose headers, all three ratchets, **"1 new field(s) all registered"** |
| `tests/unit/data/test_measured_st_heat_rates.py` | **PASS** (18) |
| `tests/unit/model` + `tests/unit/pipeline` | **PASS** (1,774 passed, 0 failed) |
| `tests/unit/data` | 2,300 passed, **25 pre-existing failures** — the identical 25 fail with this lane's `src/` and `scripts/` replaced by `origin/main`'s, so **none is this lane's**; they are CAISO firm-import, NEISO fleet, gas-offer-anchor and the SOCO token test, all absent-data or pre-existing |
| `tests/unit/config` | 4 pre-existing failures, verified identical at HEAD |
| `ruff check` / `ruff format` | clean on every file this lane touched; the **2** repo errors in `scripts/gen_nyiso229_attestation.py` are pre-existing and verified identical at HEAD |
| `check_registry_payload_parity` | **RED on the two pre-existing dirs only** — `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`. Named; **neither deleted** (rule 31) |
| `check_bench_freshness` | RED repo-wide from `ed96378e`; not this lane's (§6) |
| `check_gate_a_provenance` | SOCO's only line is the expected NOTE; **no gate-(a) stamp created**, no `calibration-complete.json` entry |
| `audit_keepers --check --iso SOCO` | E11 warning (expected, documented); **E13 fires** — see §8.1 |

### 8.1 E13 fires again, for the third time, and for the same structural reason

`2026-09-19-soco53e-measured-st-gas` is registered for SOCO but is neither the keeper nor stamped to
one. **It is not a superseded run left behind a promotion**; it is a newly registered candidate
whose promotion the owner has not ruled on, and E13 has no state for that. The red is the
unavoidable consequence of obeying three rules at once — rule 15 `[R-DASHBOARD]` (register the
moment it finishes), rule 31 `[R-RETAIN]` (never delete before the owner rules) and rule 35(f) /
E13 (every registered run is the keeper or stamped to it). Each way to turn it green breaks one of
them: pruning deletes a result before the ruling; stamping `holdout.keeper` would be **factually
false** (rule 30 `[R-TOUCHPOINT-FOLD]` (a) is for the keeper's own recipe on a *held-out year*, and
this is a *different config on the same years*); promoting pre-empts the owner. **Either ruling
clears it immediately.** This is the identical analysis `FINDING-soco-53` §9.1 and
`FINDING-soco-53d` §9.1 recorded, and it recurs because the gap in E13 was never closed — the
routed fix is a `candidate: true` sidecar field, or an E13 exemption for a run registered after the
current keeper's date with no promotion recorded. **Three lanes have now hit it; it is worth
fixing.**

**E11** ("lineage recipe diff not computable") is the documented post-prune degradation concerning
the *former* keeper `2026-09-17-soco53-measured-ct-hr`, whose bundle rule 35(a) pruned. Unchanged
from the baseline measured before this lane registered anything. **If the owner promotes, E11
becomes computable for this promotion**, because the outgoing keeper's bundle
(`results/calibration/soco53d_campaign`) is committed.

---

## 9. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** The parent ran no LP of any length (rule 32(a)). Every number in §2,
  §3, §5's predictions and §7's routing is zero-LP — the CAMPD record read directly, the fleet
  loaders called directly, EIA-923 monthly generation, and two `fleet_only` rebuilds off the
  keeper's own committed bundle.
- **One shard, one `--year 2023 2024 2025` invocation**, pinned to `cc1bcb24`.
- **The arm's bundle is RETRIEVABLE IN FULL and a promotion costs ZERO re-solves** (rule 34(e)):
  the slim + `hourly/` set is committed on this branch, and the complete 34-file bundle — including
  `dispatch/{2023,2024,2025}_P1.parquet`, `floors/` and the per-plant `unit_hourly` — is recoverable
  with
  `git checkout 884dca3132e8d1d1e1f18fbb789c356506a4e343 -- results/calibration/soco53e_st_hr`.
  Verified by `git ls-tree`: **34 files, non-zero.**
- **The control is recoverable at `730ae912e0e608695e3425e00daa00ad18138706`** (with
  `results/calibration/_shared/SOCO` on the same SHA).
- **The shard container is ARCHIVED** (rule 33(a): fetched, checked out, config-signature and
  artifact-sha verified first — and the flag confirmed to have BITTEN, by the arm's per-plant `mc`
  reproducing the zero-LP prediction to four decimals). **Its branch `claude/soco-53e-span` is
  DELIBERATELY KEPT, and stays kept even now that the owner has ruled** (rule 33(f) step 3). The
  ruling was PROMOTE, so this branch carries the **current keeper's** full per-plant layer, not a
  declined candidate's: `main` holds 17 of the bundle's files and this branch holds all 34, so
  `dispatch/*_P1.parquet`, `floors/`, `unit_hourly`, `system.parquet` and the rest exist NOWHERE
  else. Deleting it would strand the layer a re-registration or any unit-level diagnostic needs and
  would kill the recovery command cited in this doc, in `keepers/SOCO.json` and in the matrix
  stamp — which rule 33(f) step 4 forbids leaving dead. It is not a stale result. (A deletion was
  attempted during the owner's shard sweep and refused with **HTTP 403**, which rule 33(f)(5)
  documents as this environment's behaviour: the session credential can create and update refs but
  not delete them. No harm done, but the attempt was the wrong call and is recorded rather than
  quietly dropped.)
- **Nothing was deleted.** The two parity-red bundle dirs are named, not removed.

---

## 10. THE OWNER RULED **PROMOTE** — AND ONE DEFECT THE PROMOTION SURFACED

**Owner ruling, 2026-09-19: "Promote".** Executed in this session under rule 35 `[R-PROMOTE]`.
SOCO's keeper is now **`2026-09-19-soco53e-measured-st-gas`**.

### 10.1 What the promotion did, in rule-35 order

| step | rule | result |
|---|---|---|
| Enumerate the year union **before** deleting | 35(b) | **{2023, 2024, 2025}** over both registered runs; no folded touchpoints, no dangling `holdout.keeper` |
| Capture the lineage diff while **both** bundles were on disk | 35(b) | over all **856** `scenario_config` fields the recipes differ in **three**, and only **one** is solve-affecting — `measured_st_heat_rates` absent → true. `measured_coal_heat_rates` and `mid_vintage_exit_carry` did not exist at the outgoing keeper's basis `0b3f2fdc` and sit at their inert defaults `false`, exactly as §6's G-DRIFT classified them |
| Incoming keeper covers the union | 35(c) | yes — all three years in one `--year` invocation, so the promotion **shrinks nothing** |
| Write the keeper shard | 35(a) | `frontend/data/backcast/keepers/SOCO.json` → the new id, with `superseded` and `promotion_note_soco53e` |
| `calibration-complete.json` | 35(d) | **no change, deliberately** — SOCO has never had an entry (it is `NOT-YET`, not "complete"), so there is nothing to re-key |
| **Verify before deleting** | 35(e) | `audit_keepers --check --iso SOCO` run **between** promotion and prune: the incoming three stores resolve |
| Rebuild the status part | 30(b) | `build_status.py --iso SOCO` → `run_id` `2026-09-19-soco53e-measured-st-gas`, `NOT-YET` |
| Re-stamp the matrix shard + §5.8 prose | 28 | shard `keeper`/`gates` re-stamped, cell **`O` → `K`**, §5.8 header rewritten; `check_mechanism_matrix` green on all of it |
| **Then** prune | 35(a)/(d) | `prune_iso_runs.py --iso SOCO --force-uncite` removed the outgoing keeper's **three stores together** — `registry/<id>.json`, `runs/<id>.js` and `results/calibration/soco53d_campaign`. `--force-uncite` is the **intended** route here (35(d)): the only citation was this lane's own `superseded` history block, which rule 35(d) says stays as the audit trail |
| Invariant | 35(f) | **`audit_keepers --check --iso SOCO` → 0 failures.** E13 cleared |

The outgoing keeper's bundle is recoverable in full at
`730ae912e0e608695e3425e00daa00ad18138706` (with `results/calibration/_shared/SOCO` on the same
SHA); git history is the record, exactly as rule 15 says.

### 10.2 A DEFECT THE PROMOTION SURFACED, AND IT IS THIS LANE'S

`audit_keepers` **E14** fires four times on the new keeper:

| package | this keeper solved on | `requirements.txt` pins | the control solved on |
|---|---|---|---|
| **`highspy`** | **1.15.1** | **1.14.0** | **1.14.0** |
| `pandas` | 3.0.6 | 3.0.3 | 3.0.3 |
| `pyarrow` | 25.0.1 | 24.0.0 | 24.0.0 |
| `pydantic` | 2.13.5 | 2.13.4 | 2.13.4 |

**The cause is a defect in this lane's own shard prompt**, not in the mechanism: it said
`pip install numpy pandas pyarrow pydantic scipy highspy` where it should have said
`pip install -r requirements.txt`. This container image ships **without** those packages, so the
shard installed the latest of each. The control had been solved a day earlier in a container that
already carried the pins. **So the A/B differs in the LP solver version as well as in the
mechanism, and that is stated rather than buried.**

**What bounds it.** Differencing the arm against the control over all 45 class-years, **28 are
EXACTLY 0.0 MWh** — bit-identical — across **ten** classes: nuclear, hydro, wind, solar, biomass,
oil, `ST_CHP`, `CC_CHP`, `OTHER` and `COAL_BIT` (2023). A solver-version change that was
re-selecting among degenerate optima would not leave ten classes bit-identical in three separate
years. The classes that *do* move are precisely the ones the mechanism prices, in the predicted
direction and magnitude, and the arm's per-plant marginal costs reproduced the zero-LP offer-array
prediction to four decimals.

**That is strong evidence, not proof, so a pin-confirm re-solve was launched** — the identical
config on `pip install -r requirements.txt`, into `results/calibration/soco53e_pinned`, with a
hard stop if any version differs from the pins. Its result is recorded in §10.3.

**Two things follow beyond this lane.** (a) Every shard prompt in this repo should say
`pip install -r requirements.txt`; mine is the template others copy, and it was wrong. (b) The
container image no longer ships the pinned scientific stack, so **any** lane that installs
ad hoc will silently solve off-pin — an environment finding for the desk, not for SOCO.

### 10.3 THE PIN-CONFIRM RE-SOLVE WAS **ABANDONED**, AND THE E14 QUESTION STAYS OPEN

**It did not complete, and no pinned bundle exists.** The shard was launched
(`results/calibration/soco53e_pinned`, same config, `pip install -r requirements.txt` with a hard
stop on any off-pin version), reported *"solve running (PID 722); fleet build underway"*, and then
**ended its turn instead of blocking on the process** — the same shard-lifecycle defect that
wastes a container. It could not be woken: `SendMessage` reports the session unreachable, because
peer messaging only reaches sessions on this machine and a cloud shard is not one. The owner then
directed a shard sweep, and it was **archived unfinished**. Branch `claude/soco-53e-pinned` was
never pushed and does not exist.

**So the E14 dependency drift on this keeper is NOT closed — it is BOUNDED, and the two are
different claims.** What stands is §10.2's evidence: 28 of 45 class-years difference to **exactly
0.0 MWh** across ten classes, the moved classes are exactly the ones the mechanism prices, and the
per-plant marginal costs reproduce the zero-LP prediction to four decimals. That is strong
circumstantial evidence that HiGHS 1.15.1 returned the same solution 1.14.0 would have, and it is
**not** the direct confirmation a pinned re-solve would give.

**Consequence for the keeper, stated plainly:** `2026-09-19-soco53e-measured-st-gas` remains SOCO's
keeper and its determination, gates and per-plant results are unaffected by this — but its
`environment.packages` record an off-pin solve, `audit_keepers` will keep emitting four E14
warnings against it, and **no run in this repo has yet demonstrated that SOCO's LP is invariant to
that HiGHS minor version.** A future lane that needs a clean controlled A/B against this keeper
should re-run the pin-confirm first; the recipe is in this section and costs ~10 minutes of one
shard. `FINDING-soco-53f`'s handoff carries it as its first task.

**The re-usable lesson, which is bigger than this lane:** a shard prompt must tell the shard to
**block on its solve** (`wait`, or an `until` loop on the PID) rather than end a turn while a
background process runs, because a parent cannot read a shard's disk and an idle cloud shard
cannot be poked back awake.

---

## 11. THE ORIGINAL PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — ANSWERED

### 11.1 The case as it was put to the owner

**The promotion is open and it is the owner's.** SOCO's keeper is unchanged at
`2026-09-19-soco53d-campaign-commitment`; nothing has been pruned.

The case **for** promoting: it is a pure rule 14 `[R-ACCURATE]` measured-data repair with **zero
free parameters**, it removes a real structural misattribution that no eGRID construction can reach
(a coal boiler blended into four gas boilers' offer), it **subsumes** a separately-routed lever on
two independently agreeing sources, every scored C1 row **improves**, the at-risk row's margin
**widens**, and the owed rule-17 re-measurement **holds in all twelve plant-years**.

The case **against**: the determination does not move (`NOT-YET` both sides), the headline defect is
untouched, D-1's shape evidence is **mixed**, and the lever is a fifth the size it was routed at.

**If the owner promotes**, rule 35 `[R-PROMOTE]` binds and the year union is already enumerated:
SOCO's registered years are exactly **{2023, 2024, 2025}** (one registered run before this one, the
keeper, no folded touchpoints), and this run covers all three, so the promotion shrinks nothing.
The order is: write the id into `frontend/data/backcast/keepers/SOCO.json`, re-key
`calibration-complete.json`, run `audit_keepers --check --iso SOCO` (E1 + E11 green), rebuild
`build_status.py --iso SOCO`, re-stamp the SOCO matrix shard and the §5.8 prose header, and **only
then** `scripts/prune_iso_runs.py --iso SOCO --force-uncite`.

**Two questions beyond the promotion:**

1. **`soco15_spp_arm`** is a dead, committed bundle in the SOCO namespace holding
   `check_registry_payload_parity` RED in CI. Rule 31 forbids this lane from deleting it. **May it
   be pruned?**
2. **E13 has now fired on three consecutive SOCO candidates** for the same structural reason (§8.1).
   **Is a `candidate: true` sidecar field worth adding**, so "registered, promotion pending" stops
   reading as "superseded run left behind a promotion"?

---

## Log entry

## soco-53e — 2026-09-19 — a per-unit meter separates two boilers that share a prime mover, and the lever is a fifth the size it was routed at

A southeastern steam station is routinely a coal boiler and a gas boiler behind one ORIS code, and because both machines are prime mover ST, the eGRID plant rate blends them and so does the prime-mover-family rate this lane's own predecessor armed. Only a per-unit meter can separate two boilers inside one family, and that is what `ScenarioConfig.measured_st_heat_rates` does: the gas-steam sibling of `measured_ct_heat_rates` and `measured_coal_heat_rates`, on the identical seam, the identical identification and the identical artifact schema, default off and byte-identical off. At E C Gaston it moves 1,020 MW of gas steam from a coal-blended 11.5505 to its own metered 11.0744, which independently reproduces the 10.887 eGRID gas-steam sub-family rate SOCO-53c routed as a separate lever — two sources agreeing, so this mechanism subsumes that routing rather than competing with it.

The lane's first act was to correct the number that commissioned it, before spending an LP. SOCO-53d §8.1 routed "+0.539 MMBtu/MWh, +5.2 %, too dear on 3,131 MW, worth $1.5–3.3/MWh", and that figure converted SOCO's boilers at the CT_PEAKER parasitic factor 0.99 where the ST_GAS class factor is 0.95. Phase 0 re-derived from scratch rather than inheriting, reproduced 53d's table to ±0.03 at 0.99 — so the arithmetic was right and the class was wrong — and then settled the basis by measurement rather than convention: SOCO's gas-steam fleet's own metered net/gross over its eight unambiguous plant-years is 0.938 to 0.943, which the committed 0.95 default reproduces to 1.2 % and 0.99 misses by 5.5 %. On the right basis the capacity-weighted level moves 10.9613 to 10.8522, minus one percent, not minus five. The lever is real and it is a fifth the size it was sold at, and that was in the PRECOMMIT before the solve rather than in the write-up after it.

What survives, and is the actual case, is the per-plant structure: Gaston −0.476 on 1,020 MW, Greene County −0.049, Jack Watson −0.053, Yates −0.017, and Barry +1.374 the other way. Barry is applied at full magnitude — two 1954-vintage 80 MW boilers metered at 13.98 over 2,521 steady hours with 98 % of them inside the physical band, a genuinely poor machine run 1.6 % of the time. Rule 14's misalignment exception does not apply because the rate sits on the same boundary as the one it replaces, and the result independently corroborates SOCO-53d's campaign-duty gate refusing Barry at a 6.3 % synchronized share. Membership is a capacity-rank pairing to each plant's own model boiler rows rather than the coal sibling's fuel tag, because CAMPD files Barry unit 4 — a 330 MW boiler — as Pipeline Natural Gas while the model carries it as a 362 MW coal row, so a fuel-tag selection would have priced two 80 MW ST_GAS rows off a boiler the model dispatches as coal. The pairing cannot change an applied number and that is checked rather than asserted: the artifact is at plant grain, and `--check-pairing` re-runs membership under an exact generator-id rule and reports the applied rows identical.

Zero free parameters were added and the DOF ledger is unchanged at three entries and one residual. The physical band is measurably inert — every plausible band moves the capacity-weighted result by less than 0.03 MMBtu/MWh — and the gross-to-net factor is the committed class default, not a value this lane chose. Rule 19 is established mechanically at two grains: twelve of 393 built-fleet rows and twenty of 327 LP rows move, all ST_GAS, with COAL, CT_PEAKER, CC_REGULAR, all three CHP classes and hydro byte-identical at max delta exactly zero. It is a new default-off field rather than a widened `measured_ct_heat_rates`, because widening would arm five other ISOs' keepers on a measurement their lanes never made.

The gates do not move and every scored row improves. Determination NOT-YET both sides, C1 all 13/14 and free 9/10 both sides, C2/C4/C6/C8 passing, zero ledgered and zero protective caveats. 2023 CT_PEAKER stays the single failure at +9.90 to +9.82 TWh, so SOCO's headline defect is not fixed and the PRECOMMIT said so first with the number — a headroom-capped hourly displacement upper bound of +0.066, +0.154 and +0.053 TWh against delivered ST_GAS of +0.090, +0.188 and +0.085. The row the handoff flagged as at risk got safer rather than riskier: the 2023 ST_GAS share margin widens from 0.09pp to 0.12pp against its ±3.00pp band. Nine of nine ex-ante predictions hold, and the reason is worth stating rather than claiming credit for — this lane's object is a cost input whose effect is computable without an LP, so the arm's delivered per-plant marginal costs reproduced the zero-LP offer-array prediction to four decimals, where a commitment floor runs through a P0 pattern no offline estimator reproduces.

Two things are reported against the lane. D-1's shape evidence is mixed — the ST_GAS cv_ratio improves in 2024 and 2025 and degrades in 2023, all six values passing — so this lane claims no shape win where its predecessor could. And the arm creates an asymmetry it does not close: Gaston's coal row still carries the blended rate, now roughly 0.5 MMBtu/MWh too cheap for a coal machine, which `measured_coal_heat_rates` would close with only a SOCO artifact and which is routed rather than absorbed. The rule-17 re-measurement SOCO-53d owed was performed on this bundle's own floors and holds in all twelve plant-years, with Barry still carrying zero floored hours and floored blocks keeping a median of 87 to 459 hours. One further finding for the SOCO desk: `parasitic_load_factors.parquet` has never been derived for SOCO, so every SOCO plant falls back to a class default. The promotion is open and is the owner's; the keeper is unchanged, nothing was pruned, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. Record: `docs/handoffs/FINDING-soco-53e-2026-09-19.md`.
