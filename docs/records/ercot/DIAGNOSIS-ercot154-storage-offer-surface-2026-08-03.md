# ERCOT-154 — the measured ESR evening discharge-offer surface IS identified, and the arm is REFUSED anyway: the model's evening supply curve is flat, so re-pricing storage buys $1.38–$3.05/MWh while withholding ~90 % of a fleet that is already 17.7 % short of its measured volume. The ERCOT-153 evening-ramp premium is a DISPATCHABLE-STACK dispersion object, not a storage-offer object.

**Session 2026-08-03. Keeper: `2026-08-02-ercot150b-zonal-anchor` (NOT-YET; open
gates C3a 2023-only −32.6 %, C3b 2023-only 0.616, C3c, C7 2023-lignite cv-leg).
Phase 1 only — NO LP built, NO year solved, NO mechanism armed, NO flag added,
keeper UNCHANGED.** Probes
`scripts/probes/ercot154_storage_offer_surface.py` (the measurement) and
`ercot154_storage_binding_check.py` (the keeper confrontation); committed
records `results/calibration/ercot154_storage_offer_surface.json` and
`ercot154_storage_binding_check.json`. Every input is already committed: the
four 60-Day SCED sample-day parquets, the ercot150b keeper hourly sidecars,
`data/raw/eia-930-hourly/ERCO hourly.parquet`.

## 0. Verdict

**The chartered arm is REFUSED, and the refusal is NOT an identification
failure.** The measured object exists, is well covered and clears the
year-pair test at one rung. It is refused on three *other* measured grounds,
each independently sufficient, and the third re-points the lane.

1. **IDENTIFIED — the surface is real.** The bottom of the ERCOT ESR fleet's
   discharge ladder is stable across the year pair in ABSOLUTE $/MWh: the p30
   rung's 2025/2024 ratio has median **0.969**, rel IQR **0.143**, range
   0.74–1.33 over the 14 cells both years populate at ≥40 SCED intervals. The
   evening block is the best-covered region of the corpus (104–244 intervals,
   10–23 days, 144–232 distinct resources per cell). **The wall's gas-multiple
   basis is REFUTED** at every rung (median ratios 0.31–0.62 while delivered
   gas went ×2.17, $1.52 → $3.30/MMBtu) — a battery has no heat rate, and the
   measurement says so rather than the argument.
2. **REFUSED (a) — REPRESENTATION.** The measured object is a *rising ladder*
   (evening p10 ≈ \$21–45, p30 ≈ \$52–100, p50 ≈ \$75–199, p90 pinned at the
   \$5,000 HCAP). The LP layout carries **one** discharge column per storage
   unit (`P | W | S | Chg | Dis | SOC | Flow | Slack | Dump`), so any arm
   collapses that ladder to a single price. The rungs a multi-tranche form
   would need are **not identified**: p70's cross-year ratio is **0.111**
   (rel IQR 1.07) and p90 is degenerate — both years pin at HCAP, so its
   ratio of exactly 1.000 is an artifact, not agreement.
3. **REFUSED (b) — THE LEVER CANNOT PRODUCE THE PHENOMENON.** On the keeper's
   own committed hourlies, the matched (month × hour-of-day) evening
   supply-curve slope is **1.56 / 1.62 \$/MWh per GW** (2024/2025; p90 cell
   7.42 / 2.49). Withholding the model's **entire** evening storage discharge
   buys **\$1.38 / \$3.05** at the median cell (\$6.58 / \$4.71 at the p90
   cell). The ERCOT-153 object is a **\$20–66/MWh** everyday evening-ramp
   premium. The lever reaches at most 5–15 % of it, and only if the withheld
   energy never returns.
4. **REFUSED (c) — IT BREAKS A MEASURED QUANTITY THAT IS ALREADY SHORT.**
   **88.3 % / 93.8 %** of the keeper's storage discharge sits at a model price
   below the measured p30 level for its own cell, and only **5.3–5.6 %** of
   evening hours clear above \$66 — so the arm withholds ~90 % of the fleet.
   Against EIA-930 `NG: BAT` the model is **already 17.7 % short** in 2025
   (model 4,483.3 GWh vs measured 5,444.8 GWh, 100 % series coverage). There
   is no volume headroom to spend, and rule 14 `[R-ACCURATE]` runs the other
   way: this trade makes an accurate measured quantity dramatically worse to
   buy \$1–3/MWh.
5. **THE FINDING, and the re-pointed object.** The ERCOT-153 evening-ramp
   premium has no former in the model **because the model's mid-merit evening
   supply curve is flat** — 1.6 \$/MWh per GW across ~25 GW of thermal
   headroom above its own mean evening dispatch (evening thermal ~35.3–35.7 GW
   against a 60.4–61.1 GW annual maximum). Nothing on the storage side can
   create an amplitude the dispatchable stack does not have. This is the same
   **under-dispersion / near-tail-frequency signature** ERCOT-145 §5 named in
   the attributed scarcity-formation family, now measured on a second,
   independent instrument.

## 1. Why this is a rule-1 refusal and not a rule-1 violation

Rule 1 `[R-STRUCT]` forbids rejecting a structurally-correct mechanism because
the residual did not move. That protection is not engaged here, and the
distinction matters enough to state precisely.

*"Real ERCOT batteries offer discharge at opportunity cost, not at \$10"* is a
real market behaviour. **The arm does not install it.** The real behaviour is a
curve that rises from ~\$21 to the \$5,000 cap and delivers 5,445 GWh/yr; the
model can carry exactly one point of that curve on one aggregated unit per
zone. Arming the identified point makes the model's battery a \$66
all-or-nothing block that runs in 5 % of evening hours — a caricature that is
wrong in a **measurable** direction (−95 % against a measured actual), not a
faithful installation of the measured conduct.

That is precisely the exception rule 14 `[R-ACCURATE]` carves out: an accurate
input may be held back when it is *"genuinely misaligned to our representation
so that using it literally would make overall results less reflective of
reality … a different time/area aggregation"*. The misalignment here is grain:
the measurement lives on a per-resource 35-step curve; the representation is
one aggregated unit per zone with one price. Rule 14's instruction in that case
is to **document the misalignment and open the root-cause investigation** —
which is §4 below.

The selection of the rung is also worth recording, because the tempting move is
the illegitimate one. The *non-circular* selection rule — take the rung the
cross-year stability test identifies, a criterion computed entirely from the
SCED corpus and blind to any model residual — picks **p30**, and p30 is what
grounds (b) and (c) refuse. The rung that the model could actually absorb is
around p10, and choosing it *because* the model can absorb it would be a value
selected on the model's own output: a fitted parameter wearing a measurement's
clothes, barred by rules 20 `[R-DOF]` and 13 `[R-MEASURED]`. **No successor
should arm p10 on that reasoning.**

## 2. What was measured (construction and coverage)

Population: `Resource Type == PWRSTR` rows telemetered **ON / ONREG /
ONFFRRRS / FRRSUP**. `ONTEST` is excluded (49,865 rows 2024 / 42,916 rows 2025
— units under commissioning test are not offering commercially) and disclosed;
`OUT`/`OFF`/`NA`/`ONHOLD` never enter.

Increment: per interval-resource, the SCED2 (as-dispatched) curve segmented
between `max(LSL, 0)` and `min(step MW, HASL)` — the ERCOT-86/87/88 family
construction, imported rather than re-implemented so edges, quantiles and the
CPT → fixed-CST clock cannot drift.

**The HASL cap is what makes this rule-19 `[R-ONE-MECH]` clean against the
measured AS stack.** HASL is HSL net of the resource's AS responsibility, so
the ladder prices only the energy headroom
`ercot_storage_as_reserve` / `_product_credit` / `_deployment` leave to energy.
That reservation is large and worth recording on its own: the AS stack holds
back **49.6 %** of online battery HSL in 2024 and **30.9 %** in 2025 (mean
online HSL 5,270 → HASL 2,657 MW; 9,346 → 6,457 MW).

| year | days | resources (online) | hours present (CST) |
|---|---|---|---|
| 2024 | 47 | 173 | **h10–h22 only** |
| 2025 | 38 | 240 | h0–h23 |

**A hard corpus limit, disclosed:** three of the four committed extracts are
hour-truncated to ~h10–h22 CST; only the 2025 `ercot86_tail_days` file (16
days) carries full 24-hour days. 2024 therefore has **zero** overnight (h0–5)
coverage and thin morning cells. The chartered object (h16–21) is inside the
window in both years, so this did not block the measurement — but it would
have bounded any arm, and it is the same blind spot ERCOT-143 hit.

### 2.1 The defect, in the ERCOT-138 §2.3 construction

The share of the fleet's above-LSL, AS-net evening MW offered at or below a
price — robust to the HCAP saturation that ruins the upper quantiles:

| ≤ | \$20 | \$30 | \$50 | \$75 | \$100 |
|---|---|---|---|---|---|
| 2024 evening (7 bins) | 0.064–0.094 | 0.106–0.175 | 0.217–0.294 | 0.321–0.402 | 0.415–0.521 |
| 2025 evening (7 bins) | 0.035–0.081 | 0.060–0.131 | 0.123–0.287 | 0.208–0.456 | 0.322–0.621 |
| **model** | **1.000** | 1.000 | 1.000 | 1.000 | 1.000 |

The real fleet offers **6–9 %** of its evening energy headroom at ≤\$20 and
**22–29 %** at ≤\$50. The model offers **100 %** of it at \$10
(`battery_dispatch_adder`, DOF-ledger `identification: residual`). The defect
is real and correctly diagnosed by the ercot-153 charter. It is the *fix* that
does not survive contact with the model's own supply curve.

## 3. The confrontation numbers (committed record)

`results/calibration/ercot154_storage_binding_check.json`, all on the ercot150b
keeper's committed sidecars:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| keeper storage discharge (GWh) | 833.5 | 2,150.2 | 4,483.3 |
| cell coverage of hours | 0 % (no 2023 corpus) | 74.0 % | 98.0 % |
| discharge below the measured level | 0 % | **88.3 %** | **93.8 %** |
| evening share of that withheld MWh | — | 90.7 % | 92.3 % |
| matched evening slope (\$/MWh per GW) | 1.383 | **1.557** | **1.616** |
| price gain if ALL evening storage withheld | \$0.37 | **\$1.38** | **\$3.05** |
| evening hours above \$66 | — | 5.6 % | 5.3 % |
| EIA-930 measured discharge (GWh) | n/a | 722.4 (19 % coverage) | **5,444.8 (100 %)** |
| model vs measured | — | guard unusable | **−17.7 %** |

Two entries deserve emphasis. **The withholding share is a partial-equilibrium
upper bound**, computed at the keeper's frozen prices; a real solve re-prices
and some energy returns. That is exactly why ground (b) is the decisive one and
not ground (c): the slope measurement bounds *how much* can return, and at
1.6 \$/MWh per GW the answer is "almost none of it, at almost no price gain".
And **storage is essentially never the model's marginal unit today** — the
model price sits within \$1 of the \$10 offer in **12 hours (2024) and 7 hours
(2025)** of the year — so the arm's price channel was always displacement, not
storage setting the dual.

The 2024 EIA-930 guard is **unusable**: the ERCOT `NG: BAT` series begins
2024-10-23 (1,680 of 8,784 hours). 2025 is the only enforceable volume year.

## 4. Successors (what this hands the lane)

**Named object: the dispatchable stack's price dispersion in the mid-merit
evening region.** 25 GW of thermal headroom priced within ~1.6 \$/MWh per GW
is the reason the evening premium has no former. This is the ERCOT-145 §5
under-dispersion signature on a second instrument, and it is *not* an offer
LEVEL object — the whole SCED-TPO level program (ERCOT-99/100/118/119/136–140/
144/150) is adjudicated closed. It is a **slope/dispersion** object.

**Do NOT re-open, from this session's evidence:**
- The storage discharge-offer surface as a single-price arm — refused here on
  (a)/(b)/(c). New evidence would have to be a *layout* change (multi-tranche
  storage discharge columns), and even then ground (b) caps its reach at
  \$1–3/MWh.
- The gas-multiple basis for any storage offer — refuted by measurement
  (ratios 0.31–0.62 across a ×2.17 gas move).
- Arming the p10 rung "because the model can absorb it" — a fitted value
  (§1).

**The charter's fallback was run and it is REFUSED TOO — inert by wiring.**
See §5.

## 5. Fallback Phase 0 — `measured_ramp_capability` is INERT BY WIRING at ERCOT

The charter names `measured_ramp_capability` (ERCOT `U`, `K` at PJM;
`scenarios.py:5072`) as the fallback, *distinct* from the REFUTED
`ramp_envelopes` cell (ERCOT `R`, ERCOT-127 §1 — not re-tested here). The
pjm-140 / nyiso-111 discipline says derive ERCOT's own artifact and measure the
keeper crossing-rate before arming. **One step comes before both, and it
settles the cell:** this flag changes exactly one array — `FleetArrays.ramp10`
(`data/fleet/withholding.py::_ramp10_capability`, reconciled per plant by
`data/ramp_capability.py::measured_ramp10_frac`) — so it can only matter if
some ERCOT-reachable path *reads* `ramp10`.

An AST census of `src/market_sim` (probe
`scripts/probes/ercot154_ramp_capability_census.py` → committed record
`results/calibration/ercot154_ramp_capability_census.json`; parsed, so
docstrings and comments cannot inflate the count) finds **5 functional read
sites, all of them behind a non-ERCOT gate**:

| read site | function | gate | ERCOT keeper |
|---|---|---|---|
| `model/reserves/spec.py:1860` | `pjm_pergen_structure` | `pjm_reserve_pergen` | **False** |
| `model/reserves/spec.py:1937` | `pjm_pergen_pool_ramp10` | `pjm_reserve_pergen` | **False** |
| `model/reserves/spec.py:2528` | `_miso_design` | `miso_reserve_pergen` | **False** |
| `model/reserves/spec.py:3105` | `caiso_pergen_structure` | `caiso_reserve_coopt` | **False** |
| `results/scarcity.py:1686` | `pjm_reserve_deliverable_supply_cap_mw` | `pjm_reserve_supply_cap` | **False** |

And ERCOT's own reserve builders never mention it: `_ercot_design` and
`_ercot_multiproduct_design` contain **0** occurrences of `ramp10` in their
bodies. The LP-side consumer (`model/lp/bounds.py`) only ever sees
`reserve_pergen_ramp10`, which is populated exclusively by those three pergen
designs. So arming `measured_ramp_capability` on the ERCOT keeper
(`ercot_multiproduct_as_coopt=True`, `energy_reserve_coopt=True`) produces a
**bit-identical bundle** — the ERCOT-146 `measured_ct_heat_rates` outcome,
reached before a solve was spent rather than after. **ERCOT cell → `I`. Do not
test the flag; do not build the artifact for this purpose.**

The physical row it would have occupied is already held by a *better* measured
input, which is why this is a clean `I` and not a gap: ERCOT's deliverable
reserve-supply cap is `ercot_rtolcap_supply_cap_mw` on the **measured ERCOT
RTOLCAP online-capability series** (`ercot_reserve_supply_cap=True` in the
keeper). PJM uses a ramp-derived proxy precisely *because* it has no such
published series. Substituting a ramp proxy for a measured series would invert
rule 14 `[R-ACCURATE]`, and stacking one alongside it would breach rule 19
`[R-ONE-MECH]`.

**The symptom the lane was aimed at is confirmed and now quantified** (same
probe, keeper's committed `system_<year>.parquet`). Of 1,825 evening h17–21
hours per year the reserve co-opt prices reserve above \$1 in **34 (2023) / 13
(2024) / 0 (2025)** hours, and in 2025 the co-opt is silent *all year* — 0
hours above \$1, annual mean reserve price \$0.00. ERCOT-153's "reserve price
≈ \$0 at h17–21" is exact. But this session's §0.5 finding says the successor
is not on the reserve-supply side either: with 25 GW of thermal headroom priced
within 1.6 \$/MWh per GW, neither a reserve requirement nor a deliverability
cap can manufacture an evening premium the energy stack's own dispersion does
not contain.

## 6. Governance

No mechanism tested in the LP sense, no flag added, no `ScenarioConfig` field
added, no solve, no registration (the ERCOT-142/143/145/147/152 no-LP pattern).
Matrix rule-28(b) duty discharged on `battery_dispatch_adder` (ERCOT cell note
— the cell stays `K`, since the incumbent is unchanged and this session
adjudicated its *replacement*, not the incumbent). Holdouts untouched:
2023–2025 only, and 2023 carries no measured surface by construction.
ERCOT-scoped (rule 25) — no other ISO's cell is touched, and the CAISO/NEISO
storage verdicts were neither imported nor exported.
