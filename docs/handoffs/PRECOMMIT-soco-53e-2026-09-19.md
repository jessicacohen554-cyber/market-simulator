# PRECOMMIT — SOCO-53e: `measured_st_heat_rates`, the per-unit meter that separates two boilers inside one prime-mover family

**Lane** SOCO-53e · **Model** Opus 5 · **Date** 2026-09-19 ·
**Branch** `claude/soco-st-gas-heat-rates-wfiz0w` · **Data profile** `soco` ·
**Incumbent keeper (the control of record)** `2026-09-19-soco53d-campaign-commitment`,
bundle `results/calibration/soco53d_campaign`, basis
`0b3f2fdcd0ebc41bdf96cd90406b40dc979596b5`.
**Predecessors** `FINDING-soco-53d-2026-09-19.md` (§8.1 routes this lane; §2 the pairing device;
§6 the estimator post-mortem this lane's estimator is built to avoid),
`PRECOMMIT-soco-53d-2026-09-19.md` (§5 the ex-ante-prediction pattern),
`docs/calibration-log/soco.md`.
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 19 `[R-ONE-MECH]`, 21 `[R-DOF]`, 23 `[R-FROZEN-DERIVE]`,
24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`, 29 `[R-SCREEN]`,
31 `[R-RETAIN]`, 32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`,
35 `[R-PROMOTE]`.

**Pushed before anything is solved.** Every number below is ZERO-LP: the committed CAMPD
unit-level record read directly, the fleet loaders called directly, EIA-923 monthly generation,
and the keeper's own committed `mc_base` arrays and `hourly/unit_hourly_<year>.parquet` replayed
through a `fleet_only` rebuild. **The parent ran no LP of any length** (rule 32(a)). Nothing below
is revised after the solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json` carries **no
SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent`. C3a / C3b / C3c are **UNSCORABLE, not failed**. The
ceiling is rubric v3.8 `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can **never** read
`CALIBRATED`. Scored on **C1 / C2 / C4 / C6 / C8 only**. Gate **G17** absolute: no neighbouring
hub, no proxy, no cost-stack price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0.** With no price benchmark there is
no price residual, so the rule-1 authorized channel is unreachable here, not merely unused. This
lane touches no band, share, floor level, threshold or offer. **The attestation's governance block
will carry NO `authorized_price_tuning` KEY at all** — `calibration_verdict.py:3299` validates any
present value as a structured rule-1 declaration and a prose string there FAILS C6. The
declared-NONE statement goes in `attested_by` prose.

This matters more than usual for *this* mechanism. A measured heat rate is the one input that
could look like price tuning, and here it cannot be: there is no price to tune to.

---

## 1. PHASE 0 — THE LANE FALSIFIES ITS OWN HANDOFF PREMISE BEFORE IT SPENDS AN LP

### 1.1 The routed number was measured on the wrong parasitic class

`FINDING-soco-53d` §8.1 routed this lane with: *"the model is +0.539 MMBtu/MWh, +5.2 %, too dear
on 3,131 MW … at $3.2-3.6/MMBtu that is $1.5-3.3/MWh."* **That figure converted SOCO's BOILERS to a
net basis at 0.99 — the `CT_PEAKER` parasitic factor.** The class factor for a steam boiler is
`1 - DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]` = **0.95**, which is what
`derive_campd_coal_heat_rates.py` uses for its own class and what this deriver uses for its own.
`hr_net = hr_gross / factor`, so 0.99 understates every rate by **4.2 %**.

Re-derived by this lane from scratch (not scaled from 53d's table), the reproduction is exact: at
0.99 this lane measures a capacity-weighted 10.4110 against 53d's 10.4223, and the per-plant rows
match to ±0.03. **So the number is right and the basis is wrong.**

**The basis question is settled by measurement, not by convention.** SOCO's gas-steam fleet's own
metered net/gross — EIA-923 `ST`/`NG` net generation over CAMPD gas-boiler gross, per plant-year:

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| 10 Greene County | 0.9400 | 0.9390 | 0.9345 |
| 2049 Jack Watson | 0.9431 | 0.9413 | 0.9393 |
| 728 Yates | 0.9402 | 0.9431 | *(no 923 row)* |
| 26 E C Gaston | 0.9821 | 0.9403 | **1.2454** ✗ |
| 3 Barry | 0.9445 | **1.0344** ✗ | **1.1634** ✗ |

The eight unambiguous plant-years cluster at **0.938–0.943**. (The three rejected cells are EIA-923
attribution defects, not physics: a factor above 1.0 is impossible, and Barry's `ST`/`NG` rows also
cover unit 4, which is out of this population.) **0.95 reproduces the measurement to 1.2 %; 0.99
misses it by 5.5 % and is the wrong class.** The committed class default is therefore used, exactly
as the coal sibling uses its own — zero new numbers, one convention shared with the benchmark.

### 1.2 The corrected measurement: the LEVEL barely moves, the STRUCTURE moves a great deal

`scripts/data/derive_campd_gas_st_heat_rates.py --iso SOCO --detail --check-pairing
--egrid-family-heat-rates --measured-ct-heat-rates` →
`data/raw/_processed-legacy/campd_st_heat_rates_SOCO.csv`, **5 of 5 plants / 3,131 of 3,131 MW =
100 % of SOCO `ST_GAS` capacity**, 160,139 in-band steady hours across 12 units, AL/GA/MS
2023–2025:

| plant | ST_GAS MW | units | steady h | `heat_rate_gross` | **`heat_rate` (net)** | model (keeper recipe) | Δ | flag |
|---|---|---|---|---|---|---|---|---|
| 26 E C Gaston | 1,020.0 | 4 | 45,317 | 10.5207 | **11.0744** | 11.5505 | **−0.4761** | `ok` |
| 2049 Jack Watson | 721.0 | 2 | 42,287 | 9.8416 | **10.3596** | 10.4128 | −0.0532 | `ok` |
| 728 Yates | 714.0 | 2 | 36,397 | 10.2568 | **10.7966** | 10.8138 | −0.0172 | `ok` |
| 10 Greene County | 516.1 | 2 | 33,617 | 9.6969 | **10.2073** | 10.2562 | −0.0489 | `ok` |
| 3 Barry | 160.0 | 2 | 2,521 | 13.2853 | **13.9845** | 12.6100 | **+1.3745** | `ok` |

**Capacity-weighted 10.9613 → 10.8522, −1.0 %** (generation-weighted 10.7229 → 10.6004, −1.1 %).
Not −5.2 %.

**So the handoff's headline is withdrawn and replaced, before the solve.** What survives, and is
the actual case for the mechanism, is the per-plant structure:

- **E C Gaston is the finding.** Its ST prime-mover-family rate 11.5505 blends **one 832 MW coal
  boiler with four ~255 MW gas boilers**, and no eGRID construction can separate them because both
  machines are prime mover `ST`. The gas boilers' own metered rate is **11.0744** — which
  independently corroborates the **10.887** eGRID gas-steam SUB-family rate `FINDING-soco-53c`
  routed as a separate lever. **This mechanism therefore SUBSUMES routed item 3** (the Gaston
  fuel-subfamily lever): a per-unit meter does at unit grain what a sub-family construction was
  proposed to approximate, and it does it with the same answer from an independent source.
- **Barry moves the other way and is applied at full magnitude.** Its two 1954-vintage 80 MW
  boilers meter at 13.98 over 2,521 steady hours, **98 % of their operating hours inside the
  physical band** — a genuinely poor machine run 1.6 % of the time, not a meter artifact. **Rule
  14's misalignment exception does NOT apply**: unlike SOCO-53c's cogens, this rate is on the same
  boundary (net MWh, same parasitic convention) as the rate it replaces. It is simply a bad
  machine, and it independently corroborates SOCO-53d's campaign-duty gate refusing Barry at a
  6.3 % synchronized share. Two measurements, two instruments, one conclusion: Barry's small
  boilers are standby iron.

### 1.3 The membership rule, and why the coal sibling's fuel tag cannot be used

The coal deriver separates a mixed site by CAMPD `primaryFuelInfo`. **That tag would put an applied
number on the wrong rows here.** CAMPD files **Barry unit 4 — a 330 MW tangentially-fired boiler —
as *Pipeline Natural Gas***, while the model carries it as a **362 MW `COAL` row**; a fuel-tag
selection would price the model's two 80 MW `ST_GAS` rows off a boiler the model dispatches as
coal. `unitType` alone cannot do it either, since a coal boiler and a gas boiler carry the same
boiler tags.

**The model's own class assignment governs, because the rate is applied to model rows** (rule 19:
the `COAL` rows are the coal sibling's population, not this one's). So each plant's CAMPD boiler
units are paired to that plant's own model **boiler** rows (`COAL` ∪ `ST_GAS`) by descending
capacity — SOCO-53d's device — and only the `ST_GAS` partners are kept. All 15 pairs:

| plant | CAMPD unit | CAMPD fuel | p95 op MW | model row | model class | model MW | ratio |
|---|---|---|---|---|---|---|---|
| 3 Barry | 5 | Coal | 699.0 | `3_5` | COAL | 756.5 | 0.924 |
| 3 Barry | **4** | **Pipeline Natural Gas** | 330.0 | `3_4` | **COAL** | 362.0 | 0.912 |
| 3 Barry | 2 | Pipeline Natural Gas | 60.0 | `3_2` | ST_GAS | 80.0 | 0.750 |
| 3 Barry | 1 | Pipeline Natural Gas | 60.0 | `3_1` | ST_GAS | 80.0 | 0.750 |
| 10 Greene | 1 / 2 | Pipeline Natural Gas | 271.0 / 270.0 | `10_2` / `10_1` | ST_GAS | 258.3 / 257.8 | 1.049 / 1.047 |
| 26 Gaston | 5 | Coal | 816.0 | `26_5` | COAL | 832.0 | 0.981 |
| 26 Gaston | 3 / 4 / 1 / 2 | Pipeline Natural Gas | 257 / 250 / 246 / 230 | `26_ST4` / `26_2` / `26_1` / `26_3` | ST_GAS | 256 / 256 / 254 / 254 | 1.004 / 0.977 / 0.969 / 0.906 |
| 728 Yates | Y6BR / Y7BR | Pipeline Natural Gas | 363.0 / 360.0 | `728_7` / `728_6` | ST_GAS | 358.5 / 355.5 | 1.013 / 1.013 |
| 2049 Watson | 5 / 4 | Pipeline Natural Gas | 500.0 / 250.0 | `2049_5` / `2049_4` | ST_GAS | 485.0 / 236.0 | 1.031 / 1.059 |

**The pairing cannot change an applied number, and that is CHECKED rather than asserted.** The
artifact is at PLANT grain, so a permutation *within* one plant's `ST_GAS` rows leaves the
generation-weighted plant value identical; the only thing the pairing decides is plant MEMBERSHIP,
and at SOCO every such decision is separated by a factor of ≥ 2.8 in capacity. `--check-pairing`
re-runs membership under an exact generator-id-first rule (which pairs Gaston differently *within*
the plant) and reports **`applied plant rows identical: True`**.

### 1.4 Rule 19 `[R-ONE-MECH]`, established MECHANICALLY at two grains

**Built-fleet grain** (`load_fleet_from_csv`, keeper recipe ± the new field), 393 rows:

- row set, `pmax`, `pmin`, `emission_rate_co2`, `vom`, `plant_group`, `fuel_type`, `zone`: **all
  identical**;
- `heat_rate` moved on **exactly 12 rows**, all `ST_GAS`, all five plants;
- every other class max |Δhr| = **0.000000000000** — COAL (16 rows), CT_PEAKER (100), CC_REGULAR
  (90), CC_CHP (14), CT_CHP (14), ST_CHP (13), and the 134 unclassed rows.

**LP-row grain** (`mc_base`, 2023 `fleet_only` rebuild off the keeper's own bundle), 327 rows:
**20 of 327 move, all of them `ST_GAS` tranche rows**; COAL (28), CT_PEAKER (89), CC_REGULAR (67),
CC_CHP (14), CT_CHP (14), ST_CHP (11) and hydro (42) all at max |Δmc| = **0.0000000000**.

The precedence chain is therefore established as claimed: `measured_ct_heat_rates` applies in the
row loop gated on `group == "CT_PEAKER"`, `measured_coal_heat_rates` on `== "COAL"`,
`measured_st_heat_rates` on `== "ST_GAS"` — three disjoint branches, because a row resolves to one
group. The frame-level `egrid_family_heat_rates` is applied earlier, so this field **replaces** the
family rate on the rows it covers rather than stacking on it. **No row is priced twice.**

---

## 2. THE MECHANISM, AND WHAT IT DELIBERATELY DOES NOT DO

`ScenarioConfig.measured_st_heat_rates` (default **off**, byte-identical off, registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at its frozen default `"False"`).

**A NEW FIELD, not a widened `measured_ct_heat_rates` — and the handoff's question answered
explicitly.** Widening the CT field's scope to `ST_GAS` would arm the change in **five other ISOs
whose keepers already carry `measured_ct_heat_rates=True`** (CAISO, MISO, NEISO, NYISO, PJM) on a
measurement none of their lanes made. That is precisely the cross-ISO transfer rule 25
`[R-ISO-SCOPE]` forbids and rule 28(d) restates, and it is **refused**. A new default-off field with
a per-ISO artifact is the same shape nwpp-42 chose for the coal sibling one day earlier, and it
leaves every other ISO's cell at `U`.

**Zero free parameters** (rule 21). Every applied number is `sum(heatInput)/sum(grossLoad)` over
the plant's own steady hours. The four constants in the deriver are data-integrity guards fixed on
physics before any solve, not knobs — and the band is measurably inert:

| gross band | steady hours excluded | cap-weighted measured | Δ vs model |
|---|---|---|---|
| none | 0.00 % | 10.8645 | −0.0969 |
| [6.0, 25.0] | 0.63 % | 10.8494 | −0.1119 |
| **[7.0, 25.0] (applied)** | **0.71 %** | **10.8522** | **−0.1088** |
| [7.5, 20.0] | 0.98 % | 10.8576 | −0.1038 |
| [8.0, 25.0] | 1.22 % | 10.8777 | −0.0836 |
| [6.0, 30.0] | 0.59 % | 10.8510 | −0.1104 |

Every plausible band lands within 0.03 MMBtu/MWh, and the unbanded value is inside that spread, so
the band does no work. `[7.0, 25.0]` is fixed on the physical argument — below 7.0 implies > 48 %
HHV efficiency, which no Rankine steam cycle reaches (the floor sits below the coal sibling's 8.0
because a gas boiler is the more efficient machine); above 25.0 the heat-input or gross-load
channel is broken. It is **never swept against a gate**, and there is no price gate here to sweep
against.

**Refused ex ante, each with its reason:**

- **A `COAL` leg.** Gaston's coal boiler shares the blended 11.5505 too, and by the same arithmetic
  is now ~0.5 MMBtu/MWh too CHEAP. That is `measured_coal_heat_rates` — a mechanism that already
  exists at HEAD and needs a SOCO artifact — and stacking it here is exactly the rule 19 violation
  this lane spent §1.4 disproving. **Routed, and named at the gate as an asymmetry this run
  creates**: arming ST alone makes Gaston's gas cheaper while leaving its coal too cheap.
- **Any re-derivation of `parasitic_load_factors.parquet` for SOCO.** SOCO's plants are absent from
  it, and deriving them would be a strictly better rule-14 input — but that artifact is shared by
  544 plants across seven ISOs and re-keys them. **Routed as a cross-ISO data intake**, not taken
  here.
- **Barry unit 4's fuel class.** 362 MW the model prices as coal and CAMPD files as gas. This lane
  *depends* on the current assignment (it is what the pairing reads) and does not change it.
  Routed, unchanged, from SOCO-53d §8.2.

---

## 3. G-DRIFT (rule 29(b)) — THREE COMMITS, ALL INERT, NO CONTROL SOLVE SPENT

`git diff 0b3f2fdcd0ebc41bdf96cd90406b40dc979596b5 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` returns
720 insertions over 10 files. The keeper's basis is the SOCO-53d branch tip, which `main` merged as
`1b289fcf` with identical content, so that lane's own hunks cancel and the diff decomposes
**exactly** into three upstream commits:

| commit | lane | object | classification |
|---|---|---|---|
| `eec172c0` (merged `ae0ad5cf`) | caiso-287 | `--persist-p0-dispatch`, a P0 dispatch/dual sidecar in `run_calibration*.py` only | **INERT** — CLI opt-in, default off; the writer's first line is `if "p0_dispatch_mw" not in p2_state: return []`, and the key is only populated under the flag. Write-only and solve-invariant; absent from SOCO's recipe. |
| `72373757` | spp-48 | `mid_vintage_exit_carry` (`scenarios.py`, `fleet/__init__.py`, `arrays.py`, `campd_bins.py`, `eia860.py`, `outages.py`, `runner.py`) | **INERT** — `bool = False`, registered at declared default `"False"`, absent from SOCO's recipe. Every consumer short-circuits: `outages.py`'s four touched helpers each open with `if not mid_vintage_exit_carry: return <the pre-existing call>`, and `runner.py` only widens the year-threading predicate when it is on. |
| `9961a6a5` | nwpp-42 | `measured_coal_heat_rates` (`scenarios.py`, `fleet/__init__.py`, `assembly.py`, `campd_bins.py`, `eia860.py`, `run_calibration*.py`) | **INERT, doubly** — `bool = False`, absent from SOCO's recipe; and even if armed it is a strict no-op here, because `data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv` does not exist, so the loader returns `{}`. |

Two precedents re-verified rather than assumed: **SOCO is not in
`eia930/frames.py::_POOL_HOURLY_MEMBERS`** (only NWPP is), so the pool path is inert for SOCO; and
the keeper's `run_config.json` records `measured_coal_heat_rates: None` and no
`mid_vintage_exit_carry`.

**All hunks INERT ⇒ G-CTRL form 4 is valid and the keeper's committed bundle IS the control. No
control solve is spent.**

**Cache-key inertness, measured rather than assumed.** Over all **21** committed `run_config.json`
on disk, **zero keys move** at the new field's declared default and **all 21** key distinctly when
armed. `check_cache_key_registration.py` passes (856 fields, 311 registered, all declared defaults
match HEAD).

---

## 4. THE CONSEQUENCE, MEASURED BEFORE THE SOLVE

From the keeper's own committed `mc_base` arrays and `hourly/unit_hourly_<year>.parquet`.

### 4.1 Merit order (2023, mean over hours)

| plant | mc control | mc arm | Δ | CT MW priced below it, control → arm |
|---|---|---|---|---|
| 26 Gaston | 43.109 | 41.497 | **−1.612** | 8,787.6 → **7,987.8** (overtakes **799.8 MW** of CT) |
| 3 Barry | 45.981 | 50.556 | **+4.576** | 8,792.2 → **9,632.2** (falls behind all but 2 MW of the 9,634 MW CT fleet) |
| 10 Greene | 40.405 | 40.232 | −0.174 | 7,987.8 → 7,987.8 (no change) |
| 728 Yates | 44.651 | 44.586 | −0.065 | 8,792.2 → 8,792.2 (no change) |
| 2049 Watson | 32.910 | 32.762 | −0.148 | 1,056.2 → 1,056.2 (no change) |

For scale, the 2023 `CT_PEAKER` mc distribution is min 27.15 / p25 33.62 / p50 36.21 / p90 43.40 /
max 50.15, and `CC_REGULAR` maxes at 31.49 — so no CC row is ever in a crossed band.

### 4.2 Displacement UPPER BOUND, hour by hour, capped by the keeper's own headroom

For each hour: the non-`ST_GAS` energy the keeper dispatched whose own hourly mc lies strictly
between the plant's armed and control mc, capped by that plant's own available headroom in that
hour. **This is an upper bound and is labelled one** — it is deliberately NOT the construction that
over-called SOCO-53d's P5 by a factor of two, which summed a floor array instead of reproducing the
consumer's own accounting.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| 26 Gaston | +0.0680 | +0.0108 | +0.0437 |
| 10 Greene | 0.0000 | +0.1164 | +0.0058 |
| 728 Yates | 0.0000 | +0.0077 | +0.0110 |
| 2049 Watson | 0.0000 | +0.0287 | +0.0182 |
| 3 Barry (LOSS) | −0.0019 | −0.0095 | −0.0262 |
| **net `ST_GAS`** | **≤ +0.066** | **≤ +0.154** | **≤ +0.053** |

**The displaced class is `CT_PEAKER`, 99 %+ in every year** (the remainder is ≤ 0.0015 TWh of COAL
and ≤ 0.0003 TWh of CT_CHP). That is a better-directed lever than SOCO-53d's floor, whose marginal
class was mostly `CC_REGULAR` — and it is an order of magnitude smaller.

### 4.3 STATED AT THE GATE, BEFORE THE SOLVE

**This arm does not fix SOCO's headline defect, and its first-order economic term is roughly a
tenth of the campaign floor's.** The single remaining C1 failure is 2023 `CT_PEAKER` at **+9.898
TWh / +4.12pp**; a bound of 0.066 TWh closes at most **0.7 %** of it. The honest description of
this mechanism is: a **rule 14 `[R-ACCURATE]` correctness repair with zero free parameters that
also removes a real structural misattribution** (a coal boiler blended into four gas boilers'
offer), not a lever on the residual. It is armed for that reason and for no other, and whatever the
gates read afterwards is reported at full magnitude and nothing is reverted.

**The 2023 `ST_GAS` row is a row at risk, in both directions.** It passes today by **0.09pp of share
margin and 0.22 TWh of volume margin** (model 3.511 / actual 10.483, Δ −6.972 TWh / −2.91pp against
bands of ±7.19 TWh / ±3.00pp). A first-order gain of ≤ +0.066 TWh moves the share by ≈ +0.03pp, to
about −2.88pp — *further inside*. But the floor interaction (§5, P6) can move it either way by more
than that, and **a flip out of band is a live possibility that is registered here rather than
explained afterwards.**

---

## 5. EX-ANTE PREDICTION, registered BEFORE the solve, with falsifiers that name the object

| # | prediction | falsifier |
|---|---|---|
| **P1** | `ST_GAS` **RISES in every year**, by **+0.02 to +0.35 TWh**. The band is wider than §4.2's first-order bound on the upside only, because a cheaper Gaston runs more in P0, which lengthens the campaign floor's detected runs — an amplification the economic bound cannot see. | `ST_GAS` falls in any year, or rises by more than 0.6 TWh in any year. |
| **P2** | `CT_PEAKER` **FALLS in every year**, by **0.01 to 0.30 TWh**, and **the 2023 `CT_PEAKER` row STAYS FAILED above +9.5 TWh**. | `CT_PEAKER` rises in any year, or the 2023 row changes status. |
| **P3** | `CC_REGULAR` moves by **less than 0.10 TWh** in every year, and no `CC_REGULAR` C1 row changes status. Basis: `CC_REGULAR`'s mc maxes at 31.49 against a cheapest moved `ST_GAS` row at 32.76, so no CC row is ever in a crossed band — any CC movement is a second-order re-commitment, not a direct swap. | `CC_REGULAR` moves by more than 0.30 TWh in any year. |
| **P4** | **C1's failing-row SET is unchanged**: 2023 `CT_PEAKER` remains the single failure, C1 all **13/14** and free **9/10** on both sides, determination **`NOT-YET`** (PRICE UNSCORED) on both sides. | Any C1 row changes status in either direction — **including the 2023 `ST_GAS` row crossing back OUT on its 0.09pp margin**, which §4.3 registers as a live possibility. |
| **P5** | **Barry's energy FALLS** in every year (control 0.0038 / 0.0096 / 0.0671 TWh) and is **below 0.01 TWh in 2023 and 2024**. Its mc rises +4.58 / +3.85 / +5.58 and it lands behind essentially the entire CT fleet. | Barry's energy rises in any year. |
| **P6** | **The campaign floor's rule-17 evidence survives**: every one of the twelve plant-years' binding share stays **at or below that plant's own measured synchronized share** (10 → 0.752, 26 → 0.639, 728 → 0.843, 2049 → 0.920), and **Barry keeps ZERO floored unit-hours** in all three years. This is the re-measurement SOCO-53d §8.1 says is owed, and it is a genuine test: the floor reads a P0 pattern this arm perturbs. | Any plant-year's binding share exceeds its own measured synchronized share, or Barry carries any floored hour. A miss here is a **rule 17 `[R-FLOOR-WINDOW]` finding and it OUTRANKS this arm's gate result.** |
| **P7** | **C8 passes on the budget**, with `ST_GAS` forced share in **0.08–0.16** (control 0.0944 / 0.1001 / 0.1160) — moving little, because the floor's MW level is unchanged and only the P0 pattern it reads can shift. | Forced share above 0.30 (→ the rule-20 escalation) or a C8 status change. |
| **P8** | **`CC_CHP` / `CT_CHP` / `ST_CHP`, nuclear, hydro, wind and solar move by less than 0.001 TWh**, and COAL by less than 0.20 TWh in each year. The falsifier names the OBJECT: the CHP classes are priced by `measured_chp_heat_rates` and floored by `chp_steam`, neither of which this field can reach — §1.4 shows their mc rows at max |Δ| exactly 0.0000000000 — so any movement there is a seam defect, not a re-dispatch. | Any `*_CHP` or non-thermal class moves by more than 0.001 TWh, or any COAL class by more than 0.5 TWh. |
| **P9** | **The 2023 marginal emission rate's p90 RISES or is unchanged** from the control's 0.8194 tCO2/MWh, and the load-weighted mean moves by less than 0.01 from 0.6240 / 0.6092 / 0.6363. Direction: the arm puts gas steam (heat rate ~11) on the margin in hours a gas turbine (~11.3–12.8) would otherwise have set it, so the marginal rate should if anything soften, not spike. | The load-weighted mean moves by more than 0.02 in any year. |

**The determination is predicted UNCHANGED at `NOT-YET`** (rubric v3.8, PRICE UNSCORED), with
C2 / C4 / C6 / C8 passing and C3a/b/c unscorable. **It is armed anyway**, and that is rules 1
`[R-STRUCT]` and 14 `[R-ACCURATE]` operating as written: a measured physical input replaces an
estimate that is demonstrably a blend of two different machines, at zero free parameters, on an ISO
where no residual exists that it could have been fitted to.

---

## 6. WHAT THE SHARD SOLVES, AND HOW IT IS VERIFIED

**ONE shard, ONE `--year 2023 2024 2025` invocation, ONE bundle** (rules 16 / 32(b) / 34(c)).
SOCO's registered year union, read from `frontend/data/backcast/registry/*.json` **before** any
prune (rule 35(b)), is exactly **{2023, 2024, 2025}** — one registered run, the keeper, no folded
touchpoints — so the span covers it in full and no year is left out.

The recipe is the keeper's, plus one flag:

```
--iso SOCO --year 2023 2024 2025 \
  --measured-ct-heat-rates --egrid-family-heat-rates --soco-gas-st-campaign-commitment \
  --measured-st-heat-rates
```

**Config signature the shard must see, or STOP and not push:** `measured_st_heat_rates: true`,
`measured_ct_heat_rates: true`, `egrid_family_heat_rates: true`,
`soco_gas_st_campaign_commitment: true`, `measured_coal_heat_rates` absent/false,
`mid_vintage_exit_carry` absent/false, every `offer_curve_by_group` band exactly 1.0, and
`campd_st_heat_rates_SOCO.csv` sha256[:16] **`3755b4becfd9f460`** (recorded in §7).

**The bundle is PUSHED** (rule 34(a)), including `dispatch/<year>_P1.parquet`, plus
`results/calibration/_shared/SOCO/`.

---

## 7. ARTIFACT IDENTITY (rule 23 `[R-FROZEN-DERIVE]`)

| file | rows | sha256[:16] |
|---|---|---|
| `data/raw/_processed-legacy/campd_st_heat_rates_SOCO.csv` | 5 plants | **`3755b4becfd9f460`** |
| `data/raw/_processed-legacy/campd_st_heat_rates_SOCO_units.csv` | 12 units | **`905cbcd0b03341be`** |

Re-derives ONLY when CAMPD publishes new or revised vintages, never because a residual moved; the
re-derivation commit must cite the data change. The eight applied values are pinned by
`tests/unit/data/test_measured_st_heat_rates.py::TestArtifactLoader::test_committed_soco_values`.

---

## 8. DOF LEDGER (rule 21 `[R-DOF]`)

**This lane adds ZERO free parameters.** The keeper's ledger is unchanged at `n_entries` 3 /
`n_residual` 1. Every applied number in the new artifact is a measured ratio over the plant's own
metered hours; the deriver's four constants are data-integrity guards fixed on physics ex ante and
shown inert in §2; the gross-to-net factor is the committed class default, validated against the
plants' own metered net/gross in §1.1. `authorized_price_tuning`: **NONE, and unreachable** — SOCO
has no price benchmark, so there is no price residual to tune against. **No
`authorized_price_tuning` key is written into the attestation's governance block**; the
declared-NONE statement goes in `attested_by` prose.

---

## 9. GATES AT PRECOMMIT

| gate | state |
|---|---|
| `check_cache_key_registration` | **PASS** — 856 fields, 311 registered, all declared defaults match HEAD |
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, anchors (0 unresolvable), keeper stamps, §5.x prose headers, all three ratchets |
| `tests/unit/data/test_measured_st_heat_rates.py` | **PASS** (18) |
| `ruff check` / `ruff format` | clean on every file this lane touched; the **2** repo errors in `scripts/gen_nyiso229_attestation.py` are pre-existing and verified identical at HEAD |
| `tests/unit/config` | 4 pre-existing failures, **verified identical at HEAD with this lane's changes stashed**: `test_soco_token_collides_with_no_other_raw_name` (routed to the SOCO desk; this lane's artifact follows the established `_SOCO.csv` convention and the test fails identically with and without it) and three `test_reserve_config.py::TestErcotMultiProduct` cases (another lane's) |
| `check_bench_freshness` | RED repo-wide from `ed96378e`; not this lane's. SOCO's bench parts are **NOT rebuilt** — see below |
| `check_registry_payload_parity` | RED on the two pre-existing dirs `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`, plus this session's own gitignored working-tree bundle. **Named; NONE deleted** (rule 31) |
| `check_gate_a_provenance` | SOCO's only line is the expected NOTE; **no gate-(a) stamp created**, no `calibration-complete.json` entry |
| `audit_keepers --check --iso SOCO` | E11 warning expected (post-prune lineage); E13 will fire on registration — the documented "registered candidate, promotion pending" state |

**SOCO's bench parts are deliberately NOT rebuilt**, exactly as SOCO-53c and SOCO-53d did: the
auto-rebuild `dashboard_add_run.py` performs is reverted and `metrics.json` re-written on the
committed bench, because rebuilding SOCO's alone would score the arm against a different benchmark
from its control and destroy the form-4 comparison. The verdict is reported on **both** benches,
labelled.

---

## 10. RETRIEVABILITY AND THE PROMOTION QUESTION (rules 31 / 34(e))

The shard pushes its full bundle to its own branch, so a promotion costs **zero re-solves**. The
keeper's own full 33-file bundle is recovered in this session at
`730ae912e0e608695e3425e00daa00ad18138706` and is gitignored, so it reaches neither `main` nor CI.
**Nothing is deleted.** The promotion question goes to the owner in the RESULT, with the bundle's
full SHA named.
