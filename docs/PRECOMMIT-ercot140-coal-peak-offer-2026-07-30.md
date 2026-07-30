# PRE-COMMIT — ERCOT-140: the coal offer-curve UPPER TAIL on its MEASURED gas-anchored level

**Date** 2026-07-30 · **ISO** ERCOT · **Lane** ercot140-coal-p90-curve ·
**Phase** 2 (mechanism + full-span arm) ·
**Keeper under test** `2026-07-30-ercot139-cc-committed-offer`
(bundle `results/calibration/ercot139_cc_committed_arm`) ·
**Chartered by** `docs/DIAGNOSIS-ercot138-coal-gas-ranking-2026-07-29.md` §5.6
(the p90 finding) routed through the ERCOT-123 §7.2 successor charter
(the coal offer-curve UPPER TAIL), owner-issued as the ERCOT-140 lane ·
**Derive** `scripts/data/derive_coal_peak_offer_margin.py` ·
**Precommit pushed BEFORE any solve** (rule 15/26b discipline).

This document is fixed before the LP runs. Its predictions and decision rule
are the falsifier; the run is scored against what is written here.

---

## 0. The mechanism question — DECIDED, with evidence

The lane charter poses three candidate owners for the p90 deficit (model COAL
curve **−10.21 / −9.60 / −11.59 / −15.49 $/MWh UNDER** measured at p90 in all
four SCED subsets — it tops out too low):

**(i) a coal offer-CEILING object** (the top of the coal curve),
**(ii) a SCARCITY/reserve price-formation object** (ORDC/co-opt adder),
**(iii) a commitment-STATE object** (too much cheap online headroom).

**This lane chooses (i).** The evidence, each item checkable before the solve:

1. **(i) is measured directly, on two independent instruments that agree.**
   The deficit is in the coal fleet's own *submitted* RT offers, not in price
   formation: (a) ERCOT-138 §E (`E_bid_detail`, COAL p90): measured
   34.82/34.82/43.00/48.01 vs model 24.61/25.22/31.41/32.52 — every subset,
   denominator-free; (b) ERCOT-123 §5 (the ~99 %-coverage SCED supply grid):
   measured RT coal supply is 0.908–0.920 of HASL at ≤$25 — where the model
   already matches — but needs **$500** to reach 1.00 while the model's stack
   is fully offered by **$32–34** (over-offered 5–7 pp of HASL in the $32–100
   band, ~4 pp above $100). A quantity measured in the offer conduct itself
   cannot be a price-formation artifact.
2. **(ii) is a CLOSED family, and the object is out of its reach.**
   ERCOT-107/108 refuted the reserve-side family on the completed 2×2 (the
   envelope is bistable, the span is not the confound); ERCOT-101/102
   attributed the >$200 tail as a measured-input bound. The p90 object lives
   at **$35–48/MWh** — two orders below the scarcity wall; no ORDC/reserve
   mechanism reprices a submitted $27 coal offer to its measured $35–48.
   Conversely this arm **composes with** the attributed depth diagnosis
   (ERCOT-107/108: "~1.5 GW too much cheap supply at the spike hours"): it
   removes up to ~0.7 GW of mispriced sub-$35 supply from the spike-hour
   stack for measured reasons, without touching ORDC, reserves, or any gas
   curve.
3. **(iii) cannot produce the measurement, and its live successor is a
   different object.** A commitment state moves `min_gen` and run patterns,
   never a submitted TPO price; the measured statistic here IS the submitted
   price. The live state lane (precommit ercot139 §4.1, the CC committed
   block's floor coverage) is gas-side and is the OTHER chartered successor —
   this lane does not touch it (rule 19).
4. **The signal-vs-gate routing reconciles.** ERCOT-138 §5.6 attributes the
   p90 *signal* to coal but routes the *gate* to the near-tail/C3c lane
   adjudicated by ERCOT-99/101/107/108/119. Reconciliation: those
   adjudications closed the **gas-offer-wall reach** (99), the **reserve-side
   family** (107/108), and the **gas econ rebasis** (118/119) as C3c fixes,
   and attributed the residual >$200 tail to *depth*. None of them measured or
   adjudicated the **coal top band** — ERCOT-122 measured the coal DAM top
   (and refuted a level *rebasis*, which moves coal DOWN), ERCOT-123 then
   found the RT upper tail and chartered it as its §7.2 successor, never
   built. This arm is that successor: it does not claim the C3c gate (the
   >$200 tail stays attributed), it repairs the measured $32–100-band offer
   deficit that the same adjudication left open.

### 0.1 The FORM question — gas-anchored margin, not a multiplier, not coal-fuel

The measured coal top moves **$34.82 → $45.43** (res-hours-pooled p90,
2024 → 2025) while:

* **delivered coal FELL** ($1.748 → $1.630/MMBtu, ERCOT-138 §J `fuel_capwtd`
  COAL) — a coal-fuel-scaled form requires an implied slope of
  **−89.9 MMBtu/MWh**: wrong sign, physically absurd. The existing
  composition (peak HR-multiplier × delivered coal × gas-keyed sigmoid ≤ 1.0)
  is that form, and it is what leaves the top $7–14 short.
* **delivered gas ROSE** ($2.213 → $3.232, same artifact, CC rows) — the
  gas-referenced implied slope is **10.4100 MMBtu/MWh**, within 4.5 % of the
  coal fleet's own measured cap-weighted offer heat rate (**10.905**,
  ERCOT-138 §J `offer_hr_capwtd` COAL). The real fleet prices its top
  increment at ~its own heat rate × the **gas** price plus a fixed margin —
  gas-parity opportunity pricing, the structurally sensible conduct for the
  marginal coal MW that runs only when it beats the gas competition
  (rule 1: the mechanism mirrors real conduct; the model already carries the
  same concept in the gas-keyed sigmoid passthroughs).

So the form is the validated ERCOT-137/139 margin template with the slope on
**gas**:

```
mc[g, t] = GAS_HR × (gas_cc(t) − gas_anchor) + LEVEL   [+ emis(t)]
```

at the SHARED gas anchor 2.2494 (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT']`,
reused, never a second anchor — rule 19 bookkeeping). `gas_cc(t)` is the
model's own cap-weighted CC_REGULAR delivered-gas series at the LP seam — the
same basis the identification's `fuel_capwtd` was measured on.

---

## 1. The arm — ONE change, one bundle, one mechanism

`coal_peak_offer_margin` (new `ScenarioConfig` gate, default off,
ERCOT-scoped by its level registry): the CAMPD coal **`_peak` tranche** (10
plants, 5.0 % of the 13,964 MW fleet ≈ 698 MW, 6.9 % of above-mustrun
capability) is repriced from its band-multiplier composition to the measured
gas-anchored margin form, implemented on the assembled base cost as

```
mc[g, :] += LEVEL + GAS_HR × (gas_cc(t) − anchor) − heat_rate[g] × coal_fuel[g, t] − vom[g]
```

so the assembled coal-fuel and VOM terms are folded into the measured all-in
level (the measured conduct says the top does NOT track coal fuel — §0.1) and
the emissions adders (zero in the ERCOT backcast) remain. Applied to the
**BASE** cost, so P0 run discovery and the P1 bid see the same curve — like
the three margin forms it mirrors.

### 1.1 Rule 19 `[R-ONE-MECH]` — this REPLACES, it does not stack

What prices the CAMPD coal `_peak` row in the ercot139 keeper, enumerated
from its `run_config.json` before the solve:

| mechanism | armed | touches coal `_peak`? |
|---|---|---|
| `offer_curve_by_group[COAL_*]` band multipliers (`peak` 1.55/1.562 × base HR) | yes | **YES — sets `hr_peak`. Replaced (the repriced rows ignore it).** |
| supply-chain gas-keyed sigmoid passthrough (PRB floor 0.76 / lignite floor 0.675 ceil 1.0) | yes | **YES — discounts the peak row's fuel term (≤1.0). Replaced: the margin branch exits before the fuel-frac discount.** |
| `coal_offer_net_revenue_margin` (level 15.8807 / anchor 1.7387) | yes | **No — `_mustrun` rows only, provably (suffix-gated).** |
| `coal_econ_marginal_hr_bound` | yes | **No — econ bands only; its own docstring puts "the peak scarcity wall" out of scope.** |
| `ercot_offer_surface_cleared_share` / `_conditional` | yes | **No — gas classes only (`econ*` CC/CT; conditional peak rungs are `CONDITIONAL_SURFACE_GROUPS`, gas).** |
| `ercot_gas_commitment_bridge` | yes | **A gas-CC `min_gen` floor; never coal, never `mc`.** |
| measured availability envelope (`ercot_thermal_dam_availability_coal`) | yes | **Quantity, not price. UNTOUCHED (rule 14).** |

**Exactly two composed mechanisms price this row, and this arm replaces the
composition.** The `_mustrun` / `_committed` / `_econ*` rows of every coal
plant, every other class, and every gas curve are **untouched**.
`coal_tranche_pct` shares stay the measured CAMPD thermal-tranche artifact —
the arm reprices the existing tranche, it does not resize it.

---

## 2. The identification — MEASURED, zero fitted parameters

`scripts/data/derive_coal_peak_offer_margin.py` (rule-23 frozen; reads only
COMMITTED artifacts, re-runs nothing):

* **ANCHOR = 2.2494 $/MMBtu** — NOT newly derived; the shared
  `GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT']` (rule 19).
* **GAS_HR = 10.4100 MMBtu/MWh** — the corpus's own measured gas response:
  `(45.4278 − 34.8200) / (3.232 − 2.213)` where the p90s are res-hours-pooled
  per year (`ercot138_coal_gas_ranking.json` `E_bid_detail` COAL p90 rows,
  weights `B_measured` COAL `res_hours` 23021/20807/19265/18113). Its
  falsifier: physical plausibility — it lands within 4.5 % of the fleet's own
  measured offer heat rate 10.905 (§J), which a non-fuel-responsive top would
  not do.
* **LEVEL = 35.1989 $/MWh** — the four subset p90s expressed at the anchor:
  `level_i = p90_i − GAS_HR × (gas_i − anchor)`, res-hours-pooled:

| subset | res-hours | p90 | gas | anchored level |
|---|---|---|---|---|
| 2024 tail | 23,021 | 34.82 | 2.213 | **35.1989** |
| 2024 control | 20,807 | 34.82 | 2.213 | **35.1989** |
| 2025 control | 19,265 | 43.00 | 3.232 | **32.7711** |
| 2025 tail | 18,113 | 48.01 | 3.232 | **37.7811** |
| **pooled** | 81,206 | | | **35.1989** |

**Identification-quality statistic:** cross-subset dispersion falls
**±18.74 % raw → ±7.12 % anchored** — the anchoring removes 62 % of the
dispersion it claims to explain (ercot139's construction removed 85 %;
ercot137's coal bottom was ±[comparable]). The coal-fuel alternative is
REFUTED (implied slope −89.9, §0.1), so the gas-anchored form is not merely
better, it is the only measured form with the right sign.

### 2.1 What the level targets, honestly stated

The measured p90 is the **top-10 %-of-above-LSL boundary price**; the model's
`_peak` tranche is the **top 6.9 % of above-mustrun capability**. The level
therefore prices the tranche at the measured *entry* to the top decile — if
anything an UNDERSTATEMENT of the tranche's mid-mass measured price
(direction-safe: the defect is under-pricing). The arm covers ~⅔ of the
measured >$35 mass; the remaining ~3 pp sits atop the econ ramp, whose
pricing is owned by closed lanes (`coal_econ_marginal_hr_bound`, the
sigmoids — rule 19: not stacked on here). The direct target is the measured
**mass and level above $35**, not the exact p90 order statistic.

### 2.2 The identification RISK — the §H same-plants 2025 flip, stated ex ante

ERCOT-138 §H (crosswalk-restricted, coal = 4 plants / 49–54 % of measured
HSL, declared "noisy at the top decile") has coal p90 measured
**31.14/31.14** in 2024 (same sign as §E) but **24.30/24.71** in 2025 —
the same-plants 2025 top did NOT rise with gas; the fleet-wide 2025 rise
($43–48) is carried by the non-crosswalked half of the fleet. The primary
instrument stays §E (full CLLIG fleet at ~100 % curve coverage — the
population the model's 10-plant fleet represents; §H is a 50 %-coverage sign
check). But the risk is real: **if the 2025 fleet-wide gas-tracking is
compositional rather than fuel-responsive, the repriced 2025 top ($45.4) is
too dear on roughly half the fleet**, and the arm will show it as a 2025-
specific degradation (coal give-back too deep / C3a 2025 over-lift /
spurious 2025 tail hours). The per-year gates in §4 are this risk's
falsifier; if they fire in 2025 the successor is a **per-plant top-step
identification (data intake)**, never a re-tuned level (rule 13).

---

## 3. Predictions — fixed before the solve

### 3.1 The offer surface (the direct target, measurable without gates)

The repriced `_peak` bid at the corpus's matched-hours gas: 2024
`35.1989 + 10.41 × (2.213 − 2.2494)` = **$34.82** vs measured 34.82 (keeper:
27.40/27.95); 2025 = **$45.43** vs measured 43.00/48.01 pooled 45.43 (keeper:
31.41/31.73). 2023 is the declared extrapolation (no SCED disclosure
exists): at the year's EP delivered-gas annual mean 2.5402 the bid runs
**≈$38.2** annual-mean, daily-varying with gas.

### 3.2 The gates

* **C1 coal — predicted to IMPROVE (the structural target), all three
  years.** The keeper's residual over-run is +2.4/+5.3/+5.6 TWh; the
  repriced 698 MW gives back on the order of **0.3–1.6 TWh/yr** (ERCOT-123's
  hand sizing of the tail, bounded by the tranche's utilization). Displaced
  energy lands in gas (the ercot139 pattern).
* **C3a mean LMP — predicted to IMPROVE, modestly** (order +$0.2–1.5/MWh on
  the mean): hours clearing $27–45 where the coal peak was marginal reprice
  upward toward actual, and hours where it exits merit clear on dearer gas.
  Both directions run toward actual (C3a is −36.8/−16.7/−14.6 %). It must
  NOT overshoot: a year's C3a crossing above **0 %** is a guard breach (§4.1).
* **C3c scarcity tail — predicted ≈unchanged to slightly RECOVERED** (keeper
  47/6/0 vs RT actual 181/53/31). The repriced bid tops at ~$45–48 — deep
  inframarginal at the scarcity wall — so it cannot form a tail hour by
  itself; any recovered hour comes from removing mispriced sub-$35 depth at
  real scarcity hours (the ERCOT-107/108 attributed diagnosis). Recovery is
  legitimate ONLY at hours whose RT actual is >$200; anything else is
  spurious (§4.1).
* **C3b / C4 / C7 / C8** — C3b expected to improve slightly (duration-curve
  mid-top); C4 2024 coal r (0.854 FAIL) direction unknown, reported as it
  falls; C7 2023 COAL_LIGNITE (FAIL) plausibly helped (less ceiling-riding —
  ERCOT-123 §7.2's expectation) but **gated, not assumed**; C8 expected PASS
  held (coal forcing 0.0–0.4 %).

---

## 4. PRE-REGISTERED FAILURE MODES (mandatory, per the lane charter)

### 4.1 ERCOT-89/91's zero-spurious + C3a level guard — ORDINARY REJECTION

Both prior top-of-curve arms (`ercot_shoulder_online_span`, ercot89; the
band-hour steam wall, ercot91) died here: they lifted ~230 same-cell
sub-$150 hours by $10–20 and manufactured tail hours outside the measured
scarcity hours (spurious Δ +2/+5 tripped the gate). Declared now, before the
solve:

* **Zero-spurious:** the count of hours where the model settles **>$200
  while the RT actual is ≤$200** must not increase over the keeper's own
  count in ANY year. Any increase is an ordinary rejection — whatever it
  does to C1 or the offer-surface target.
* **C3a level guard:** no year's C3a may cross above 0 % (over-fire), and no
  year's C3a may DEGRADE (move away from actual) — a degradation in any year
  is a rejection (this doubles as the §2.2 risk falsifier for 2025 and the
  extrapolation gate for 2023 — the ERCOT-123 §7.2 "LOYO per-year, 2-of-3 is
  FAIL" requirement: 3/3 or reject).

### 4.2 The crossing band is MEASURED-CORRECT and must not regress

ERCOT-139's coal give-back (−3.81/−3.49/−3.00 TWh) and CC_REGULAR gain
(+5.22/+5.07/+4.49) are the keeper's structural gain, resting on measured
levels (rule 14). Declared now: this arm touches **no gas curve and no coal
row below the `_peak` tranche** — the mechanism log must show exactly the
coal `_peak` rows repriced and nothing else, and C1 coal must not INCREASE
vs the keeper in any year. An arm that buys its result by re-inflating the
CC committed level, the coal committed/econ bands, or any measured input is
reversing a measured quantity — refused ex ante, not run.

### 4.3 Rule 26(a) clearance — why this is not a closed-lane re-run

| closed lane | what it closed | why this arm is outside it |
|---|---|---|
| coal offer LEVEL rebasis (ercot122 §5.2 / ercot132 leg B) | re-basing the whole coal curve DOWN to the flat $21 DAM level; pooled `econ_high` 2.856 refuted as fleet-representative | this arm moves the top **UP** to a measured RT level; touches only the `_peak` tranche |
| coal offer REACH (ercot123 §7.1) | "the error is how much coal is offered" — refuted; model ~100 % reach is CORRECT | this arm changes no reach/quantity — it prices the already-offered top; it IS §7.2's chartered successor |
| coal min-load PRICE (ercot136/137) | `_mustrun` level, measured, keeper | different row, different end of the curve |
| coal-side of the crossing band (ercot138) | coal committed/econ bands exonerated in the crossing band | untouched — the p90 finding is §5.6's separate, opposite-sign object |
| EP rebasis / bands (ercot118/119) | gas econ/peak multiplier rebasis; C3c drain owned by gas econ legs | no gas band touched; coal top gets DEARER, the drain channel (cheaper CC) is structurally absent |
| `ercot_offer_surface_lowcurve` / `_floorscoped` | gas committed/econ DAM ladders | gas-side, different instrument, different rows |

---

## 5. The decision rule — fixed now

1. **Any §4.1 breach (spurious increase in any year, C3a overshoot past 0,
   or C3a degradation in any year) ⇒ ORDINARY REJECTION.** Registered as a
   rejected probe with its matrix cell; not promoted. A 2025-only breach
   additionally confirms the §2.2 compositional risk and routes the
   successor to per-plant top-step identification (data intake).
2. **Guards intact + C1 coal improves in all three years ⇒ KEEPER
   CANDIDATE**, surfaced to the owner on the ERCOT-137/139 structural
   standard. Promotion is the owner's call, not this session's.
3. **Guards intact + C1 coal does NOT improve 3/3 ⇒ REJECTED PROBE**; the
   finding is that the measured top repricing does not carry the residual
   coal over-run, which hands the over-run back to the D-2/G1 enumeration
   with the tail hypothesis retired.
4. A result outside all three is reported as it falls; nothing is re-tuned
   to land inside one. **No parameter in this arm is swept.** The level,
   slope and anchor are measured; if they are wrong the derive's source
   artifacts are wrong (rule 23).

---

## 6. Open owner rulings surfaced (NOT decided here)

1. **Carried from ERCOT-137 §7 / ERCOT-138 §7.1 / ERCOT-139 §6, still
   open:** delete outright vs leave inert the retired
   `coal_tranche_1_fuel_passthrough` pricing path and the legacy non-CAMPD
   `split_coal_tranches` `_t1/_t2/_t3` path (rule 26 `[R-DELETE]`).
2. **Carried from ERCOT-138 §7.2 / ERCOT-139 §6, still open:**
   `ercot_offer_hrmult_ep_rebasis` / `_bands` are solve-affecting
   `ScenarioConfig` fields with no mechanism-matrix row — a rule-26(c) gap
   predating three lanes (the CI guard only checks fields NEW vs base).
   Recorded, not fixed here.
3. **The OTHER live successor** (precommit ercot139 §4.1: the CC committed
   block's commitment-STATE floor coverage) remains chartered and untouched
   by this lane; which lane runs next after ERCOT-140 stays the owner's
   sequencing call.

---

## 7. Honest limits, stated before it runs

1. **The measured corpus is probe days, not a span** — 79 delivery days,
   2024–2025 only, hours 11–22 for three of four subsets. **No 2023 SCED
   exists**, so the 2023 application is a declared extrapolation, gated
   per-year in §4.1.
2. **The p90-vs-tranche-mid-mass basis note** (§2.1): the level is the
   measured top-decile boundary applied to a tranche spanning the top 6.9 %
   — an understatement of the tranche's measured mid-mass price, declared,
   not corrected (correcting it would need an uncommitted statistic).
3. **The §H same-plants 2025 flip** (§2.2) is this identification's largest
   stated risk; its falsifier is pre-registered (§4.1 per-year gates).
4. **A uniform fleet slope:** GAS_HR is one measured fleet slope applied at
   every plant (no per-plant top data is committed). At the identification
   points the fleet cap-weighted bid is exact by construction; per-plant
   dispersion around it is unmodeled and declared.
5. **Coal-fuel tracking is REMOVED on the repriced rows** — that is the
   measured finding (§0.1, slope −89.9 on coal fuel), not an omission. The
   emissions adders (zero in the ERCOT backcast, non-zero in
   carbon-priced forecasts) remain on top of the margin form.
6. **The P1 startup amortization is absent from the §E capture** but COAL
   shows `model_p1 == model_all` at every quantile — no amortization lands
   on the coal rows today, so the capture is the scored curve.

---

## 8. Scope

Full span **`--year 2023 2024 2025` in ONE bundle** (rule 16). Holdout years
(2022 / 2019 / ≤2021 / H1-2026) untouched (rule 22). ERCOT-scoped only
(rule 25 — the level/slope enter `COAL_PEAK_OFFER_LEVEL_BY_ISO` /
`COAL_PEAK_OFFER_GAS_HR_BY_ISO` for ERCOT alone; other ISOs hard-fail rather
than inherit). No residual-tuned adder (rule 13). Availability stays
MEASURED (rule 14). One mechanism per phenomenon (rule 19, §1.1). The new
`ScenarioConfig` fields carry their mechanism-matrix row in the same push
(rule 26c). No new GitHub Actions workflow. Registration keeper-or-rejected
with the matrix cell stamped in this same session (rules 15/26b).

Every CLOSED lane honoured: the CC committed offer LEVEL (ercot139 —
measured, keeper; never re-derived or re-tuned), the COAL side of the
crossing band (ercot138), `gas_offer_net_revenue_margin` on the CC band
(ercot138 §J — inert), `ercot_offer_hrmult_ep_rebasis` / `_bands`
(ercot118/119), `ercot_offer_surface_lowcurve` / `_floorscoped`,
`ercot_shoulder_online_span` (ercot89), the band-hour steam wall (ercot91),
`measured_ct_heat_rates` on the CC defect, coal min-load PRICE (ercot137),
coal offer REACH (ercot123 §7.1), coal offer LEVEL rebasis (ercot132 leg B),
pooled `econ_high` 2.856 (ercot122 §5.2), F923 delivered-coal price as a
price question (ercot135 §3), coal ramp trajectory (ercot127/132),
availability ENVELOPE layer (ercot126), min-config upper bound (ercot130),
plant-grain fractional min-load floor (ercot127 §3), unit-grain commitment
STATE (ercot128), age/temp derates (ercot121 §1a), EP-rebasis C3c
(ercot119), `ercot_zonal_gas_basis`, West/Panhandle topology split. P2 is
ARCHIVED — not a calibration option.
