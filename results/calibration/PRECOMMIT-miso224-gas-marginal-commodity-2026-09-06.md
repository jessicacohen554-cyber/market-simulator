# PRECOMMIT miso-224 — THE BODY IS A FUEL-CONVENTION OBJECT: the model prices gas at the EIA-923 *average* delivered cost where the market prices it at *marginal* commodity. Screen arm = `miso_gas_marginal_commodity_pricing` on 2023

**Written and committed BEFORE the screen solve.** Rule 29 `[R-SCREEN]`: phase 0 is complete
(four zero-LP instruments, §1–§4), the screen year is named from the mechanism's own footprint
(§4), the gates are structural and STOP-only (§5), the scorer is committed blind alongside this
document, and the G-DRIFT audit that makes the committed keeper the control is in §7.

Keeper at entry: **`2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), CALIBRATED, C3c the single ledgered caveat.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only.

Successor to miso-223 (`FINDING-miso223-committed-band-debody-2026-09-06.md`), which killed the
`committed`-band arm on G-1 and named two successor objects: (A) dead endogenous wind
curtailment, (B) the body aimed at the bands above `committed`, with marginal frequency as the
mandatory footprint. **Both were measured; (A) is refused on the bound and (B) is not a
multiplier object — it is the gas fuel-cost convention.** §1–§3 are the measurements.

Instruments (all committed, all zero-LP, all reproducible from committed artifacts):
`scripts/probes/_miso224_floor_anatomy_phase0.py` → `_miso224_floor_anatomy.json`;
`_miso224_marginal_frequency_phase0.py` → `_miso224_marginal_frequency.json`;
`_miso224_offer_decomposition_phase0.py` → `_miso224_offer_decomposition.json`;
`_miso224_static_remerit_phase0.py` → `_miso224_static_remerit.json`;
`_miso224_liveness_prebuild.json` (the arm's fuel array rebuilt on the keeper recipe, §5 S-2).

---

## 1. WHERE THE BODY ERROR LIVES — a gradient over the whole body, not a floor spike

Zone-matched, hour-matched: model P1 price at MISO-Indiana vs INDIANA.HUB RT (the C3a
comparator), banded by the decile of the ACTUAL price. Mean error ($/MWh) per decile:

| decile of actual | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | +11.7 | +9.8 | +9.2 | +8.7 | +8.1 | +6.9 | +5.9 | +4.3 | +0.6 | −36.7 |
| 2024 | +10.3 | +8.8 | +8.2 | +7.6 | +7.5 | +6.7 | +5.5 | +3.4 | −2.3 | −41.8 |
| 2025 | +12.5 | +10.9 | +9.9 | +8.6 | +7.4 | +5.7 | +3.9 | +0.2 | −6.5 | −74.0 |

**Against the system energy price (MEC = LMP − MCC − MLC, congestion stripped) the body is
worse, not better**: annual model − MEC = **+5.31 / +3.69 / +0.29** against model − hub
+2.85 / +1.37 / −2.16, because the hubs carry ~$2.4 of negative congestion. Hub − MEC is
within ±2.5 in every decile d1–d9 and lives in d10 (+31 to +37, the scarcity-hour congestion
miso-204 characterised). **The body object is an ENERGY-PRICE object.**

## 2. OBJECT (A) IS REFUSED ON THE BOUND

The negative-price mechanism (wind's −$26 PTC offer reaching the price) is a system-level
event in **1 / 7 / 0** hours a year (MEC < $0) and MEC < $10 in **53 / 157 / 34** hours. Even
closing every sub-$10 hour to the MEC moves the annual body mean by ≤ **$0.27** (157 h × ~$15 /
8,760) against a body error of +$6–13 in the cheap deciles. The real MISO cleared **$10–20**
(not negative) in 1,765 / 2,959 / 681 hours — below every thermal SRMC the model carries — and
that is the object. The gross-up's separate defect (miso-206: +5.1 TWh/yr of phantom wind
displacing thermal in every hour) pushes prices DOWN, the wrong sign for the body. **No lever
on (A); the `vre_reference_rate_curtailment_grossup` cell keeps `K`.**

## 3. OBJECT (B), AIMED BY MARGINAL FREQUENCY — and it is not the multipliers

**3.1 Who holds the margin** (the miso-223 lesson applied: marginal frequency, not energy).
MISO-Indiana, keeper P1, reconstruction residual (price − marginal `mc_base`) p50 **$0.01**,
p90 **$0.07** — the price IS the marginal tranche's base offer in every body hour:

| share of BODY hours at the margin | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `econ` bands (econlo/econhi/econc00–05) | **0.749** | **0.776** | **0.754** |
| `committed` | 0.119 | 0.137 | 0.133 |
| `peak` | 0.091 | 0.047 | 0.053 |
| `mustrun` | 0.000 | 0.000 | 0.000 |
| COAL\|econ / CC_REGULAR\|econ / CT_PEAKER\|econ / ST_GAS\|econ | .26/.22/.12/.09 | .24/.23/.17/.09 | .21/.19/.22/.08 |
| in the real sub-$20 hours: CC_REGULAR\|econ / COAL\|econ | .43/.33 | .41/.21 | .31/.20 |

`committed` holds the margin 12–14 % of body hours while carrying 47 % of energy — miso-223's
G-1 result explained. `mustrun` never sets price.

**3.2 What the marginal offer is made of.** Per hour, `model − MEC = (price − mc_base) +
(mc_base − SRMC) + (SRMC_delivered − SRMC_spot) + (SRMC_spot − MEC)`: the P1 startup adder,
the MARKUP layer (band multipliers, coal ladder, gas net-revenue margin), the FUEL-CONVENTION
layer (EIA-923 average delivered print vs the traded Chicago Citygate hub, gas rows only) and
the residual. MISO-Indiana, body hours:

| body | gap | startup | **markup** | **fuel convention** | residual |
|---|---:|---:|---:|---:|---:|
| 2023 | +6.16 | 0.02 | 0.11 | **+4.68** | +1.35 |
| 2024 | +4.66 | 0.02 | 1.07 | **+3.44** | +0.13 |
| 2025 | +3.22 | 0.02 | −0.67 | **+3.25** | +0.61 |

The band-multiplier layer — the authorized tuning channel and the object the charter named —
is **$0.1–1.1** of a $3–6 body wedge. The fuel convention is **74 / 74 / 101 %** of it. In the
CC-marginal hours the wedge is entirely the fuel layer (2024: gap 7.58 = markup 0.27 +
fuel 7.92 + residual −0.63; marginal CC print $2.88 vs Chicago $1.92 at HR 8.6). In the
COAL-marginal hours the residual (+4.7 / +7.1 / +5.0) is the model running coal at the margin
where a spot-priced CC would have been marginal instead — the same cause, second order.

**3.3 The convention, stated.** A dispatch offer is a MARGINAL cost: hub commodity plus
variable transport. The EIA-923 print is the plant's AVERAGE delivered cost — commodity plus
demand charges and contracted transport amortized over the month's takes — and it exceeds the
Chicago hub by **+$0.5–1.3/MMBtu in most months, +$2.6 in Feb-2024** (CC fleet, cap-weighted;
the print lags the collapse of the commodity). miso-212 sized this ISO-wide and left it in owner
court as a cross-ISO convention; miso-156 refused `gas_hub_basis_overlay` on the valid rule-14
ground that a flat ISO series replaces per-plant dispersion — **and on a comparator that was
the EIA Illinois utility-citygate SURVEY, which sits $1–2/MMBtu above the traded hub because
it carries LDC transport** (`gas_basis_by_iso_month.csv` "N3050IL3 − HH"; 2024 basis +0.5 to
+2.1 against a traded Chicago basis of −0.6 to +0.5). Against the traded index the model's
delivered gas is not "$0.09 above spot" in 2024; the marginal CC's print is $0.96 above it.

**3.4 The structural claim (rule 1, first half).** The forecast path already prices gas at
hub + basis (`resolve_annual_gas_price`) — marginal commodity. Only the backcast overlays the
average print. The arm makes the backcast use the forecast's convention: a rule-13 input with
an exact forward analogue, and a closure of a backcast→forecast input gap (rule 22's crossover
object), not the opening of one. Rule 14's misalignment clause: both are measured; the print is
measured on the wrong basis for a dispatch offer; prefer the reconciled measured input.

## 4. THE ARM, and the screen year from the footprint

`miso_gas_marginal_commodity_pricing = True` (new `ScenarioConfig` field, default off,
byte-identical off — `tests/unit/data/test_fuel.py`; matrix row
`gas_marginal_commodity_pricing` minted with the field, rule 28c). Every MISO gas row's fuel
= the measured daily hub spot for its zone from the published `miso_zonal_gas_hub.csv`
selector: Chicago Citygate daily (flow-date staircase) for the Chicago-hub AND MidCon zones,
Henry Hub daily (trade-date staircase) for MISO-South. Zero fitted scalars. Supersedes, never
stacks (rule 19): the winter Chicago SHAPE overlay and the mean-zero zonal increment are
skipped on the repriced rows. MISO-scoped, hard error elsewhere (rule 25). Applied via
`replay_keeper --set miso_gas_marginal_commodity_pricing=true` (the generic override channel).

**Screen year = 2023**, from the mechanism's own footprint — the fuel-convention layer at the
MARGINAL tranche in body hours (§3.2): **$4.68 (2023) > $3.44 (2024) > $3.25 (2025)**.
Disclosed: 2023 also carries the largest body residual (+8.71 vs the hubs); the choice is by
the footprint column and would be 2023 on the CC-fleet print-minus-hub and on the static
prediction (§5 G-1) too. It is not 2025, the largest-|C3a| and largest-tail year.

## 5. SCREEN GATES — structural, STOP-only, never gated on the target residual

Scorer: `scripts/probes/_miso224_screen_gates.py`, committed in the same push as this
document, run once when the solve exits, never edited after.

- **S-1 single delta.** The arm's `run_config.scenario_config` differs from the keeper's ONLY
  in `miso_gas_marginal_commodity_pricing`, over the NON-year-scoped fields (`weather_year`,
  `gas_price_override`, `start_year`/`end_year`/`year(s)` excluded ex ante — the miso-223 §2
  artifact) and with fields absent from the keeper's older config listed, not counted. Else STOP.
- **S-2 liveness.** Rebuilding the fuel array from the ARM's recorded config, every MISO gas
  row equals its zone's daily hub staircase exactly (Midwest = Chicago, South = Henry Hub;
  dual-fuel parity can only lower it). Pre-solve on the keeper recipe:
  `_miso224_liveness_prebuild.json` — 1,448 gas rows, share exactly at hub **1.000**. Else STOP.
- **G-1 direction & magnitude.** MISO-Indiana mean price over the keeper's OWN 2023 body hours
  (bottom 90 % of its price) falls by **$3.36–$10.08** — 0.5×–1.5× the static re-merit
  prediction of **−$6.72** (instrument self-error −$1.17 on the keeper basis; p10/p50/p90
  −10.3/−6.4/−3.6). Outside the band ⇒ the mechanism does not do what its arithmetic says ⇒ STOP.
- **G-3 dispatch response.** In the 1,230 hours where INDIANA.HUB cleared below $20 in 2023 —
  where the keeper runs coal **+3.2 GW** over and gas **−3.0 GW** under EIA-930 — the arm moves
  coal DOWN and gas UP against the keeper by at least **0.3×** the static prediction
  (coal −2,919 MW, gas +2,990 MW): coal Δ ≤ −876 MW and gas Δ ≥ +897 MW. Wrong direction or
  below the fraction ⇒ the footprint is not where the mechanism claims ⇒ STOP.
- **G-4 no non-target load-bearing flip (rule 29's own clause).** No 2023 C1 class flips
  PASS → FAIL. Scored from the sidecars by DELTA TRANSFER (a single-year replay writes no
  `metrics.json`): `arm_gm = keeper_gm + (arm class_hourly − keeper class_hourly)`, against
  the committed `classFull` actuals and the verdict's own band (min(max(2 % load, 3 % gen),
  8 TWh) = **8.0 TWh**, share ±3 pp). The transfer is exact per plant and approximate per
  class (the payload re-maps a few plants across 923 classes: keeper ST_GAS 20.10 TWh in the
  sidecar vs 14.48 in `gmModel`), so a miss within **±1.5 TWh** of the band edge is reported
  INCONCLUSIVE, not a kill. **C2 is UNSCORED ex ante.** C3a/C3b/C3c are the target family
  and are reported, never gated.

**NAMED EX ANTE AS THE LIKELIEST KILL — G-4 on the COAL classes.** The static re-merit says
spot-priced gas displaces **−3.3 GW** of coal on the 2023 annual mean (≈ −29 TWh across
COAL_PRB 120 / COAL_BIT 54 TWh; keeper cells −1.56 / −2.92 against ±8.0) and adds +3.4 GW of
gas (CC_REGULAR keeper −4.17; ST_GAS +0.54; CT_PEAKER **−7.985, 0.015 TWh of headroom** — the
arm makes CTs cheaper, so this one moves AWAY from the edge). The static stack has no
commitment floors, so it is an upper bound on displacement, and **the LP answers exactly the
question it cannot: does the keeper's coal self-commitment structure hold coal at ~19 GW when
gas is priced where the market priced it?** Two readings, fixed now:

1. **Coal holds (no G-4 flip):** the commitment structure is adequate; the arm survives the
   screen and goes to the owner's cross-ISO ruling (§6) before any full span.
2. **Coal collapses (G-4 flips on a coal class):** the arm is KILLED on the screen per rule
   29's letter — and the finding is rule 14's: the average-cost gas print was **silently
   compensating** for missing coal self-commitment, holding coal in merit by PRICE where the
   real market holds it by COMMITMENT. The accurate input stays right; the root cause (a coal
   self-commitment floor with a window, a driver and a forward story, rule 17) becomes the
   successor object. This reading is a structural result, not a residual verdict.

Second exposure: **CC_REGULAR-2023** (−4.17 + up to +30 TWh of gas gain): a flip here reads the
same way as coal (gas takes energy the market gave to coal) and is reported as such.

## 6. REPORTED AGAINST THE ARM, BEFORE IT RUNS — and what this screen cannot license

- **C3a will get worse in 2023 and every year, and that is not a reason to reject it** (rule 1).
  Static: annual LW −$7.4 / −$7.2 / −$6.5 → C3a-2023 from +7.15 % to about **−14 %**; the
  cancellation that makes C3a pass today (+$6–9 body vs −$16–44 tail) is removed and the tail
  deficit — the reserve/ORDC/emergency family miso-219/221/222 measured 3–12× short — is exposed
  at full magnitude. The tail is predicted to move **−$14 to −$21** too (the gas stack shifts
  in every hour). A run that reads NOT-YET on C3a with a correct body and an honest tail is the
  true state of the lane; the owner ruled 2026-09-06 that structural integrity with regressed
  gates may still be a keeper. **This document does not propose the arm as a keeper.**
- **Full span is gated on the OWNER, not on the screen.** miso-212 §8 put the
  average-vs-marginal convention in owner court as cross-ISO methodology. A cleared screen is
  the evidence for that ruling; it is not a licence to spend 2024/2025 or to promote. Rule 29(2)
  is therefore narrowed here ex ante: screen → owner ruling → full span, never screen → full span.
- The screen bundle `results/calibration/miso224_spotgas_S` is never registered and is
  **deleted before the PR merges** (rule 29(c), owner ruling R-AV); every number cited lives in
  the FINDING.

## 7. G-DRIFT — the audit that makes form 4 valid (rule 29(b)); NO CONTROL SOLVE

miso-223 Addendum D audited `4545300d..b3fb0edc` (its own tip): ALL INERT. Extended here from
`b3fb0edc` to HEAD `cd2f1ed8` over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
— six files, **448 insertions, 0 deletions**:

| changed file(s) | classification | reason |
|---|---|---|
| `config/scenarios.py` (+66), `pipeline/backcast_config.py` (+51), `scripts/run_calibration_full.py` (+31), `scripts/run_calibration.py` (+31) | **INERT** | The nyiso-199 `nyiso_ct_peaker_bands_measured` field, default `False`, absent from the keeper's recipe, and a HARD ERROR if armed on a non-NYISO ISO — it cannot fire on a MISO run. |
| `config/constants.py` (+1) | **INERT** | One added import (`resolve_capacity_adequacy_requirement_published`, capacity-market, forecast-only). |
| `scripts/lib/invariant_ledger.py` (+268, new) | **INERT** | Session tooling; not on the solve path. |
| **this session's own diff** (`data/fuel/basis/miso.py`, `data/fuel/resolve.py`, facade exports, `scenarios.py` field) | **INERT for the control** | Default-off; the off path calls the winter overlay and the zonal applier exactly as before (`spot_cells is None`), verified by `test_miso_gas_marginal_commodity_off_is_byte_identical` and the untouched MISO fuel suite (14 passed). |

**VERDICT: no LIVE hunk. The committed keeper is the control; no control solve is spent.**
Residual caveat carried from miso-223 Addendum D: the keeper was solved with cross-year
warm-start ON, `replay_keeper` pins it OFF; prices are bit-identical under that switch and
marginal-tie dispatch reshuffles ~0.003 %, which is inside G-4's ±1.5 TWh inconclusive width.

## 8. Governance

Rule 1 `[R-STRUCT]`: structure first — no multiplier is touched, the DOF ledger is unchanged
at 41/2, and no number is chosen (zero fitted scalars). Rule 13: a hub spot is a reproducible
market input with a forward analogue. Rule 14: the misalignment clause, documented in the
field and the applier docstrings. Rule 19: supersede, never stack (winter shape, zonal
increment). Rule 25: MISO-scoped, hard error elsewhere; the cross-ISO question stays in owner
court. Rule 28: base row + six cell lines with the field; MISO cell `U` until the screen is
scored, then stamped in this session. Rule 29: one year, footprint-named, structural STOP-only
gates, scorer blind, keeper as control, bundle deleted before merge. Rule 22: 2023 only.
Memory: `FINDING-miso169` §3 recipe — 8 GB swapfile (live), `MARKET_SIM_HIGHS_THREADS=4`,
pandas 3.0.3 / pyarrow 24.0.0 / highspy 1.14.0, openpyxl.
