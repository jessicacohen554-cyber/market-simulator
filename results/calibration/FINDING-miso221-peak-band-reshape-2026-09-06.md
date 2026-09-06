# FINDING miso-221 — THE PEAK-BAND RESHAPE IS **ARITHMETICALLY UNREACHABLE** ON THE AUTHORIZED CHANNEL. The arm dies at phase 0, **no LP spent**, and the reason is not the reshape's size but the composition of the block that pins the price: at the model's own maximum-price hour of 2025, **only 10.2 % of the supply above the clearing price carries an `offer_curve_by_group` entry at all.** Keeper unchanged (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the
single ledgered caveat. **No solve was run in this session, no bundle was produced, and
nothing is registered on the dashboard** — rule 15 `[R-DASHBOARD]` registers completed
runs, and there is none. Rule 22: the probe reads 2023–2025 only. Rule 29 `[R-SCREEN]`
step 0 killed the arm before step 1; **no screen year was ever named and no screen
solve was launched.**

Instrument: `scripts/probes/_miso221_peak_shape_phase0.py` → `_miso221_peak_shape.json`
(zero-solve; rebuilds the keeper's own fleet and offer basis through
`_miso134_ct_night_order_screen.build_year` and re-prices the object's hours against
candidate tables at the model's own dispatched quantity).

---

## 0. Verdict in one paragraph

The charter's diagnosis was right and its lever was wrong. `CT_PEAKER` **is** the class
at the margin, and `CT_PEAKER|econ` **is** the dominant block sitting above the clearing
price in the object's hours (49.9 / 46.6 / 27.6 % of it) — so the authorized channel
does reach the right capacity. It still cannot move C3c, for two measured reasons that
compose. **(1) Shape alone is inert.** A `peak` lift of 4.5× moves the object hours'
mean price by **−$0.04 / −$0.03 / +$3.04**, and a mean-preserving econ spread — which is
the only reshape that protects the `CT_PEAKER`-2023 cell — moves it by **−$0.62 / +$0.53
/ +$2.78**, *downward in 2023*, because the marginal tranche sits in the lower half of
the block it re-slices. **(2) Level has reach but no room.** The smallest level lift
tested, ×1.5, removes **7.74 TWh** of `CT_PEAKER`-2023 energy against **0.015 TWh** of
C1 headroom — **516× over** — and still puts **0 of 15** object hours above $200, with a
maximum object-hour price of **$52.50** against actuals of $122–$355. Pushing to ×5.0
does not fix 2023 either: still 0 of 15, still a $56.47 ceiling. **2023 is unreachable
at every admissible value**, and rule 1 condition (b) requires one config across all
three years, so 2023 governs. The structural reason is the last measurement: at 2025
07-28 HE19 — the model's own annual maximum, $187.04 against an actual $683.21 — the
capacity above the clearing price is **2,849 MW, of which 2,557 MW (89.8 %) is the
non-tranche block** (wind, nuclear, solar, imports, hydro, biomass, oil) that carries no
`offer_curve_by_group` entry. **The offer-curve channel controls 10.2 % of the supply
that would have to be re-priced, at the single hour where it controls the most.**

## 1. A GOVERNANCE CORRECTION THE CHARTER NEEDS, stated first because it scoped the work

The charter names the shape knob as "**`peak` and `pct_peaking`**". **`pct_peaking` is
not on the authorized channel.** Rule 1 `[R-STRUCT]`'s 2026-09-05 carve-out, condition
(a), admits *"the `offer_curve_by_group` band multipliers ONLY (`committed` / `econ_low`
/ `econ_high` / `peak`) — never `phys_*` (measured physics), **never the structural
shares (`econ_low_share`, `pct_peaking`)**"*. Moving capacity between tranches is
exactly the structural-share move the condition excludes, so the "move capacity out of
the flat econ block into a steeper peak tranche" formulation is **not available** under
the ruling as written. Every candidate in this probe therefore moves band multipliers
only, and the module asserts it (`_assert_scope`, which fails the run if any `phys_*`,
`econ_low_share` or `pct_peaking` value differs from the keeper's).

This is not a technicality that changed the answer — the level family below tests the
strongest form the channel permits and it fails on its own terms. But it does mean the
charter's stated mechanism was never admissible, and a future session that wants the
capacity-reshape form must take it to the owner as an amendment, not run it as a lever.

## 2. THE OBJECT, re-measured against the CURRENT keeper

The charter carried numbers built on the **miso-217** keeper. Rebuilt on **miso-220**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model hours RT > $200 | 3 | 7 | **0** |
| actual hours RT > $200 | 30 | 37 | **88** |
| **model annual max $/MWh** | 238.87 | 500.00 | **187.04** |

2025 is the sharp case and it is sharper than the charter states: the model's **entire
2025 price distribution tops out at $187.04**, so its C3c count is 0, not "see below".

`CT_PEAKER|peak` is **no longer entirely out of merit** — under miso-220's `peak` = 4.4
it holds the margin in **2 of 2025's 15 object hours** (06-23 HE19, 07-28 HE18). That
correction is what made the `peak` limb worth testing rather than dismissing.

## 3. A-1 / A-3 — WHAT SITS ABOVE THE PRICE, and how much of it this channel owns

Mean capacity above the committed clearing price across each year's 15 object hours:

| class \| band | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `CT_PEAKER\|econ` | **12,282 MW (49.9 %)** | **8,828 MW (46.6 %)** | 2,239 MW (27.6 %) |
| **`\|?` (no offer entry)** | 3,188 MW (12.9 %) | 3,155 MW (16.6 %) | **2,894 MW (35.7 %)** |
| `COAL\|econ` | 2,275 MW (9.2 %) | 1,308 MW (6.9 %) | 175 MW (2.2 %) |
| `CC_REGULAR\|peak` | 1,764 MW (7.2 %) | 1,153 MW (6.1 %) | 845 MW (10.4 %) |
| `CT_PEAKER\|committed` | 1,566 MW (6.4 %) | 1,098 MW (5.8 %) | 339 MW (4.2 %) |
| `CT_PEAKER\|peak` | 1,132 MW (4.6 %) | 1,130 MW (6.0 %) | 1,019 MW (12.6 %) |
| `ST_GAS\|econ` | 719 MW (2.9 %) | 1,060 MW (5.6 %) | 178 MW (2.2 %) |
| **TOTAL above price** | **24,624 MW** | **18,964 MW** | **8,104 MW** |

The `|?` block is the fleet's non-tranche rows — wind, nuclear, solar, imports, hydro,
`OTHER`, biomass, oil — none of which carries an `offer_curve_by_group` entry. miso-220
declared `oil` (3,278.8 MW), `biomass` (1,865.7 MW) and `ST_CHP` (698.3 MW) unreachable;
**this measurement widens that declaration to hydro and imports and makes it the
binding constraint in 2025**, where the unreachable block is the LARGEST single
component above the price.

**At the model's own 2025 annual maximum (07-28 HE19, $187.04 vs actual $683.21):**

| class \| band | cap MW | cap-w $ | above price MW |
|---|---:|---:|---:|
| `\|?` | 15,885 | 48.39 | **2,557** |
| `CT_PEAKER\|peak` | 1,125 | 168.21 | 271 |
| `CT_PEAKER\|committed` | 2,493 | 51.54 | 21 |
| | | **total** | **2,849** |

**292 MW of 2,849 MW — 10.2 % — is on the authorized channel.** This is the finding.

## 4. THE CENSUS — every candidate, its reach and its cost

All candidates move band multipliers only; `phys_*`, `econ_low_share` and `pct_peaking`
are byte-identical to the keeper in every one. Re-priced at the model's own dispatched
quantity; the construction reproduces the keeper's committed dual with a maximum
residual of **$0.14 / $0.17 / $1.35**, so the reconstruction is not the story.

### 4a. Shape family (`CT_PEAKER` only; keeper `econ_low` = `econ_high` = 1.10, `peak` = 4.40)

| candidate | | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| `peak20` (4.5×) | obj hrs > $200 | 0/15 | 0/15 | **1**/15 |
| | mean Δ price | **−$0.04** | **−$0.03** | +$3.04 |
| | max obj price | $46.32 | $54.72 | $212.54 |
| | `CT_PEAKER` energy removed | 0.0019 TWh | 0.0051 TWh | 0.0008 TWh |
| `spread0.44` (0.66 / 1.54) | obj hrs > $200 | 0/15 | 0/15 | 0/15 |
| | mean Δ price | **−$0.62** | +$0.53 | +$2.78 |
| `spread0.88` (0.22 / 1.98) | obj hrs > $200 | 0/15 | 0/15 | 0/15 |
| | mean Δ price | **−$1.27** | +$1.56 | +$4.08 |
| | max obj price | $46.29 | $66.71 | $194.26 |
| `spread0.44 + peak12` | obj hrs > $200 | 0/15 | 0/15 | 1/15 |

**The `peak` limb is nearly free and nearly inert.** Its `CT_PEAKER` energy cost is
0.0008–0.0051 TWh — three orders of magnitude *inside* the 0.015 TWh headroom, because
the keeper's `CT_PEAKER|peak` band produces essentially nothing (**0.0007 / 0.0019 /
0.0001 TWh** of committed annual energy). So F-2 is not what stops it. What stops it is
that the band is 4.6–12.6 % of the capacity above the price: lift it and the clearing
point simply settles on the next tranche.

**The mean-preserving spread is the only reshape that protects the C1 cell, and it moves
2023 the wrong way.** Setting `econ_low` = 1.10 − δ and `econ_high` = 1.10 + δ arms the
already-configured `offer_curve_smoothing_n` = 6 ramp (the keeper's equal multipliers
fail the builder's `pk_m > lo_m` test, so `CT_PEAKER` — alone among MISO's spread-carrying
fossil classes — has a *flat* econ block by construction) and is exactly mean-preserving,
because the ramp's six equal slices have midpoints averaging 0.5. It still fails: even at
δ = 0.88, an `econ_low` of 0.22 that is far outside anything defensible, the maximum
object-hour price is **$194.26** and no hour crosses $200. And because it makes the
bottom half cheaper, it admits **+4.8 to +14.2 TWh** more `CT_PEAKER` capacity below the
price — a swing that would demolish C1 across the rest of the fleet even where it moves
`CT_PEAKER`'s own cell the safe way.

### 4b. Level family — THE TRADE-OFF FRONTIER, and the kill

The only form with first-order reach is a pure level lift on the block that is actually
above the price. All four authorized bands × L:

| year | arm | obj hrs > $200 | mean Δ price | max obj price | **`CT_PEAKER` energy removed** |
|---|---|---:|---:|---:|---:|
| **2023** | ×1.5 | **0/15** | +$2.51 | **$52.50** | **7.736 TWh** |
| | ×2.5 | **0/15** | +$2.84 | **$56.47** | **7.900 TWh** |
| | ×5.0 | **0/15** | +$2.84 | **$56.47** | **7.922 TWh** |
| 2024 | ×1.5 | 0/15 | +$6.67 | $70.89 | 9.501 TWh |
| | ×2.5 | 0/15 | +$19.79 | $113.01 | 9.755 TWh |
| | ×5.0 | 3/15 | +$51.67 | $212.43 | 9.760 TWh |
| 2025 | ×1.5 | 1/15 | +$15.22 | $212.54 | 9.914 TWh |
| | ×2.5 | 1/15 | +$45.68 | $212.54 | 10.648 TWh |
| | ×5.0 | 10/15 | +$124.39 | $264.99 | 10.701 TWh |

**Against `CT_PEAKER`-2023: model 9.053 TWh, actual 17.038, error −7.985 against ±8.00 —
0.015 TWh of headroom.** The smallest lift tested removes **7.736 TWh**, i.e. **516× the
headroom**, taking the cell to roughly −15.7 TWh, about **twice the band**.

**Reported against interest, with the correction applied in the arm's favour.** The
first-order estimate holds the price at the keeper's own dual and ignores the
`reliability_floor × CT_PEAKER` mechanism, which forces **2.2619 TWh** of the class in
2023 (D-2, window h14-21, the object's own hours). Floored energy cannot be priced out,
so the true displacement is bounded by ≈ 9.053 − 2.26 = **6.8 TWh**, not 7.74. **That
bound is still 450× the headroom and still ~2× outside the band.** The kill does not
depend on the estimate being tight.

**And 2023 never reaches the tail at any value.** Its ceiling is $56.47 at ×5.0 — because
once `CT_PEAKER` is priced out, `COAL|econ`, `CC_REGULAR|peak` and the unreachable `|?`
block take the margin at ~$56. Lifting *those* too is a whole-fleet level move, which is
miso-218 again with worse C1 consequences. Rule 1 condition (b) requires one config
across every scored year, so **2023 governs and 2023 has no path.**

## 5. THE DECISION RULE, applied

The charter's rule: charter an A/B only if phase 0 shows (a) the reshape puts material MW
in the price range the tail needs, (b) `CT_PEAKER`-2023's exposure is tolerable against
0.015 TWh, and (c) it rides the authorized channel under all five conditions.

* **(a) FAILS.** No admissible candidate puts material MW in the $200–$1,800 range at the
  2023 or 2024 object hours; 2025 reaches only under a level lift that (b) forbids.
* **(b) FAILS for every candidate with reach.** 7.7–10.7 TWh against 0.015 TWh.
* **(c) holds for the candidates tested** (band multipliers only) but is what excludes the
  charter's own `pct_peaking` formulation entirely (§1).

**Verdict: write the finding, mint nothing, stop.** miso-219 is the precedent that this
is a full session's work rather than a failure; this session adds that it cost **zero LP
minutes** rather than miso-219's diagnostic solves.

## 6. G-DRIFT (rule 29(b) form 4) — recorded even though no arm was solved

Run because it is cheap and it tells the next session whether the keeper's committed
bundle is still a valid control. `git diff 4545300d..b2bd9fdb` over
`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` = **43 files, +2,136 / −553.**

**The single strongest fact: `scripts/run_calibration.py` — the backcast orchestrator
itself — is UNCHANGED**, absent from the diff entirely.

| hunk group | Δ | class | reason |
|---|---:|---|---|
| `model/lp/rows.py`, `model/lp/model.py`, `lp/__init__.py`, `policy/{clean_tiers,federal_ces,cap_and_trade,constraints}.py`, `runner.py` | +643/−111 | **INERT** | the clean-tier / RPS / federal-CES row family and the partial-footprint carbon column. Keeper config: `rps_enabled` **false**, `miso_clean_tier_rows` **false**, `carbon_price` **0.0**, new `federal_ces_target_by_year` default **None**. `carbon_mc_column` returns the scalar **as the same object** at `carbon_price == 0`; `append_federal_ces_region` returns `state_arrays` **unchanged** with no target row. `runner.py` is the FORECAST orchestrator |
| `data/outages.py`, `data/fleet/arrays.py` | +148/−33 | **INERT** | gated on the new `unit_outage_extract_basis_share`, default **False**, absent from the keeper's config; plus a dead-code deletion (`read_clean_outages`) |
| `data/cod_ramp.py`, `run_calibration_full.py` (`_band_categorical`), `pipeline/solve.py` (`malloc_trim`), `utils/heap.py` | +305/−76 | **INERT** | wall-clock only, each documented byte-identical by construction and unit-test-gated |
| `config/constants.py` (`DATACENTER_ZONE_SHARE` MISO rows), `capacity_evolution/{ccs,evolve}.py`, `config/capacity_market.py`, `matrix.py` | +250/−49 | **INERT** | forecast-only: capacity evolution, the scenario matrix and datacenter siting. A `mode="backcast"` run never enters them |
| `model/interchange/spec.py` | +46/−6 | **INERT** | gated on the CAISO corridor inventory; `caiso_corridor_flow_limit` **false**, MISO has no corridors (rule 25) |
| `data/{som_conduct,reserve_requirements,floor_mechanisms,eia923,benchmark_corridor}.py`, `fleet/eia860.py`, `results/metrics.py`, `pipeline/{result,__init__}.py`, `config/{paths,plant_taxonomy}.py` | +7/−257 | **INERT** | the 2026-09-05 delete-not-archive cleanup (`677b605a`) plus the Y-10 formatting pass (`2cc74f8c`) — dead code and reflow |
| `results/{emissions,export,outputs}.py`, `scripts/lib/*` | +358/−15 | **INERT for determination** | reporting only: adds `import_co2_mt_reported`. C5a `co2` is a REPORTED-ONLY stream (demoted at rubric v2.9), contributing no status, caveat or reason line |
| `data/raw/_validation-source/actual_lmp.json` | +64/−2 | **INERT** | adds PJM `rt_lw`/`da_lw` rows. **No MISO row changed** |
| `config/scenarios.py` | +311/−0 | **INERT** | purely additive: **three** new fields, all default-off — `federal_ces_acp_usd_per_mwh` (None), `federal_ces_target_by_year` (None), `unit_outage_extract_basis_share` (False). A replay takes a new field at its current default, so all three land off. No existing default changed |
| `data/offer_curves.py`, `data/miso_outages.py`, `pipeline/reference.py` | +4/−4 | **INERT** | black reflow; one unused constant removed |

**ALL HUNKS INERT ⇒ form 4 is valid and `miso220_nonsteamlift_B` remains the control at
HEAD. No control solve is owed.** Corroborating (not proof): this session rebuilt the
keeper's fleet and offer basis at HEAD and reproduced its committed P1 duals to within
**$0.14 / $0.17 / $1.35** through an independent merit reconstruction — a fleet-path
change would not leave that residual intact.

## 7. WHAT THIS CLOSES, AND WHAT IT HANDS ON

**Matrix bookkeeping (rule 28b), stated because the absence of a verdict flip is
deliberate.** No cell verdict moved. The matrix carries no peak-band-reshape row — the
mechanism is `offer_curve_by_group`, MISO's own **`K`**, and nothing here refutes it;
what is refuted is three *parameterisations* of it. The cell keeps `K` with this
session's evidence appended, the same "evidence about the container, no verdict" form
miso-215 used. No `ScenarioConfig` field was added, so no base row was minted and no
other ISO's shard was touched (rule 28c not engaged, rule 25 `[R-ISO-SCOPE]` intact).

**CLOSED BY MEASUREMENT (do not re-run):** the `CT_PEAKER` peak-band reshape in every
form the authorized channel permits — `peak` level, mean-preserving `econ` spread, and
pure `CT_PEAKER` level lift — as a route to C3c. The `peak` limb is inert (4.6–12.6 % of
the above-price block); the spread cannot reach ($194.26 ceiling at an indefensible
δ = 0.88) and moves 2023 backwards; the level limb has reach only in 2025 and costs
450–516× the `CT_PEAKER`-2023 headroom, with 2023 capped at $56.47 regardless.

**The generalisation, and it is the one that matters.** C3c is not an offer-curve
problem in MISO. In the object's hours the model carries **8.1–24.6 GW above its own
clearing price**, of which **12.9 / 16.6 / 35.7 %** — and **89.8 % at the single tightest
hour** — is fleet the `offer_curve_by_group` channel cannot address at all. Combined with
miso-219's arithmetic closure of the reserve/scarcity family (zero shortfall in all
26,280 hours) and F-7's finding that `maxgen_emergency_tier_pricing` contributes exactly
$0 because load slack is 0.000 MWh, **the remaining C3c levers must either remove
capacity from the stack in those hours or re-price the non-tranche fleet.** The
owner-court **ELMP / emergency-supply mapping** filed by miso-219 §5/§9 — re-basing the
emergency tier from load slack onto an emergency-range MW cohort — is exactly a
capacity-removal mechanism and is the single most promising remaining lever. This
session's measurement strengthens the case for taking it to the owner: it is now the
only named candidate that acts on the right object.

**Standing result this session did not touch and does not undo:** miso-214 measured that
62–70 % of the CT energy the model misses was produced by the real market *below* the
plant's own delivered cost. No offer or price mechanism reaches it, and nothing here is
presented as closing the `CT_PEAKER` class gap.

**Standing risk, unchanged:** every 2025 C1 cell is `SKIPPED` on a preliminary EIA-923
vintage (71/96 prior plants missing, 26 % reporting). When it completes, 2025 fuelmix
becomes gated against a configuration that has never been scored there.

## 8. Reproduction

```
python3 scripts/probes/_miso221_peak_shape_phase0.py            # shape family, 3 years
MISO221_FAMILY=level python3 scripts/probes/_miso221_peak_shape_phase0.py
```
Each is ~50 min sequential; this session ran six single-year processes in parallel
(`MISO221_YEARS=<y> MISO221_FAMILY=<f>`, ~12 min wall) and assembled the record with
`_miso221_peak_shape_phase0.merge`. Zero LP minutes either way.
