# FINDING — caiso-119 BASIS ADJUDICATION: the caiso-118/118b headline is REFUTED on the bytes. "Reality runs 2–3.6× more belly gas than the model" came from EIA-930 CISO `NG: NG` — the same raw 930 gas cell caiso-109 had already condemned as corrupted — and it fails all three independent tests (level, diurnal shape, energy balance). On the honest CEMS basis the model's ANNUAL gas is within 1–3 % of actual and its belly gas is ~1.2–1.5× low, not 2–3.6×. The commitment-paradigm DIRECTION survives; the MAGNITUDE was ~5× overstated, so the chartered caiso-119 build ("floor the belly toward ~8–10 GW") would have over-forced by ~5–6 GW. Re-scoped to the one measured parameter that is genuinely wrong: `caiso_ra_min_load_frac` = 0.26 vs a MEASURED physical 0.570. Also names a new, previously-unreported defect: CT_PEAKER runs at ~8 % of actual, hidden by C1's absolute volume band (2026-07-24)

**Derive-first, measurement-only for this document; the re-scoped single-delta
A/B is reported separately.** Keeper `2026-07-23-caiso-netrev-margin-keeper`
UNCHANGED at the time of writing. Reproduction (no LP):

- `scripts/probes/_caiso119_committed_minload_derive.py` — measured min-load + belly commitment
- `scripts/probes/_caiso119_belly_gas_recheck.py` — model vs both candidate actuals
- `scripts/probes/_caiso119_gas_basis_adjudication.py` — T1/T2/T3 + the true gap

---

## 1. What was claimed, and what it rests on

`FINDING-caiso118-belly-price-undercommit-2026-07-24.md` (Headline / INV5) and
the `FINDING-caiso118b-ra-commitment-paradigm-2026-07-24.md` redirect that
follows from it rest on a single comparison:

| year | model belly gas | claimed ACTUAL belly gas | claimed ratio |
|---|---|---|---|
| 2023 | 4,260 MW | 8,461 MW | 2.0× |
| 2024 | 3,721 MW | 9,633 MW | 2.6× |
| 2025 | 2,947 MW | 10,537 MW | 3.6× |

From that ratio caiso-118b concluded the model commits ~1/3 of the gas reality
commits, and chartered caiso-119 to "floor the belly-committed fleet toward
reality's ~8–10 GW".

**The MODEL side reproduces** (this session's keeper sidecar gives 4,147 / 3,635
/ 2,959 MW all-gas — within 2–3 % of the quoted numbers, different bundle).
**The ACTUAL side does not.** It is EIA-930 CISO `NG: NG` averaged over local
hours 10–15, reproduced to the digit:

```
2023 belly(local hod) = 8,461    2024 = 9,633    2025 = 10,537
```

That is the same raw 930 gas cell caiso-109 explicitly condemned — *"the
caiso-108 −13.66 was the corrupted 930 NG cell"* — and replaced with the CEMS
basis (`gas_cems_grid + gas_cogen_grid`). caiso-118 went back to it.

## 2. Three independent tests — the 930 `NG: NG` series is not CAISO gas generation

### T1 — LEVEL: it exceeds metered gas, and the excess grows every year

| year | 930 `NG: NG` TWh | bench CEMS-basis grid gas TWh | 930 / CEMS |
|---|---|---|---|
| 2023 | 88.0 | 68.7 | **1.28** |
| 2024 | 85.6 | 61.0 | **1.40** |
| 2025 | 79.0 | 51.6 | **1.53** |

CEMS covers essentially the whole CAISO gas fleet (only 2 of 82–84 bench
facilities are absent from the CA unit-level file). A series running 28→53 %
above metered gas — with a monotone drift — is carrying something other than
gas generation. It is a BA-level residual/plug category, not a fuel meter.

### T2 — DIURNAL SHAPE: the decisive test

CAISO is a solar-belly ISO; gas must trough midday and peak on the evening ramp.

| year | series | belly (10–15) | evening (17–21) | belly/evening | duck? |
|---|---|---|---|---|---|
| 2023 | EIA-930 `NG: NG` | 8,461 | 11,898 | 0.71 | yes |
| | CEMS gas (gross) | 5,087 | 9,749 | **0.52** | yes |
| | MODEL keeper | 4,147 | 10,344 | 0.40 | yes |
| 2024 | EIA-930 `NG: NG` | 9,633 | 10,349 | 0.93 | marginal |
| | CEMS gas (gross) | 4,435 | 8,444 | **0.53** | yes |
| | MODEL keeper | 3,635 | 9,049 | 0.40 | yes |
| 2025 | EIA-930 `NG: NG` | 10,537 | 8,754 | **1.20** | **INVERTED** |
| | CEMS gas (gross) | 3,535 | 6,627 | **0.53** | yes |
| | MODEL keeper | 2,959 | 7,384 | 0.40 | yes |

The 930 series' belly/evening ratio drifts 0.71 → 0.93 → **1.20**: by 2025 it
claims CAISO burns MORE gas in the solar belly than on the evening ramp. That is
not a physical dispatch shape. CEMS is a rock-stable 0.52/0.53/0.53 across all
three years — the real duck.

### T3 — ENERGY BALANCE: it does not fit inside the belly

2025 belly (EIA-930 CISO, MW): demand 26,536 − solar 13,852 − wind 1,699 −
nuclear 2,011 − hydro 1,311 − geo 729 − other (−4,671) − net import 1,766
→ **residual available for gas + storage charge + export = 9,838 MW**.

The 930 `NG: NG` claim of **10,537 MW overfills that residual by ~700 MW** —
before a single MW of the several GW of CAISO belly battery charging. CEMS
(3,535 MW) fits with room to spare.

**Verdict: EIA-930 CISO `NG: NG` is refuted as a CAISO gas-generation actual on
level, shape, and balance. The caiso-118/118b magnitude is void.**

## 3. The model's TRUE gas gap on the surviving (CEMS) basis

### Annual — the model's total gas is essentially right

| year | model all-gas MW | CEMS all-gas MW (gross) | ratio |
|---|---|---|---|
| 2023 | 6,949 | 7,176 | **1.03** |
| 2024 | 6,141 | 6,324 | **1.03** |
| 2025 | 5,297 | 5,262 | **0.99** |

CEMS `grossLoad` includes parasitic/steam-host load that never reaches the grid,
so the true grid-delivered ratio is *closer to 1.00 still* — the model is not
gas-short in volume. This also removes the premise of the caiso-109 "closing the
~8 TWh over-import recovers the gas" arithmetic, which was computed on the same
condemned cell.

### Diurnal — the defect is a ~1 GW REDISTRIBUTION, not a 5–6 GW shortfall

Gap (CEMS gross − model, all gas classes, MW):

| hod | 2023 | 2024 | 2025 |
|---|---|---|---|
| 08–09 | +1,081 / +1,022 | +620 / +759 | +749 / +669 |
| 10–15 (belly) | +756 … +1,263 | +564 … +1,256 | +445 … +872 |
| 16–17 | +686 / +278 | +724 / +102 | +735 / +23 |
| 18–21 | −535 … −1,034 | −456 … −979 | −883 … −1,009 |
| 22–23 | −1,099 / −973 | −1,183 / −1,165 | −1,191 / −1,136 |

The model runs ~0.5–1.3 GW **too little** gas across hours 8–17 and ~0.5–1.2 GW
**too much** across hours 18–23, netting to ~0 annually. Its duck is too DEEP
(belly/evening 0.40 vs the measured 0.53) — it over-cycles gas off midday and
over-runs it at night.

**So caiso-118b's DIRECTION is right and its MECHANISM story is plausible — the
model under-commits belly gas and substitutes imports — but the size of the hole
is ~1 GW, not ~6 GW.** A floor built to reach 8–10 GW of belly gas would have
forced ~5–6 GW of phantom generation, blown the C8 forced-energy budget on a
fabricated target, and violated rule 1 outright. This is exactly the failure
mode rule 13 exists to prevent: the "measured" target was not measured.

## 4. What IS measurably wrong — `caiso_ra_min_load_frac` = 0.26

The keeper carries `caiso_ra_min_load_frac = 0.26`: the min-stable-load fraction
at which the RA must-offer bridge holds a committed gas unit. The code default is
0.40 (NREL cycling-cost / CAISO Master File PMin/PMax), and 0.26 is below any
physical CC turn-down — a fit-to-shrink-forced-energy value, rule 11-adjacent.

Measured from CEMS (`_caiso119_committed_minload_derive.py`): among hours a unit
is FULLY online (`opTime == 1.0`), the per-unit 5th-percentile of
`grossLoad / pmax`, capacity-weighted p50 across units with ≥500 operating hours:

| year | CC_REGULAR p05 | CC_REGULAR p10 | all-gas p05 |
|---|---|---|---|
| 2023 | **0.570** | 0.615 | 0.497 |
| 2024 | **0.570** | 0.615 | 0.551 |
| 2025 | **0.570** | 0.626 | 0.560 |

**0.570 in every one of the three years** — and ERCOT's independently-derived
analogue (60-Day DAM disclosure committed LSL/HSL cap-weighted p50,
`ercot_gas_bridge_min_load_frac`) is **0.574**. Two ISOs, two unrelated data
sources, the same number: this is the physical CC turn-down, not a fit.

This is the honest, rule-13/18 single delta the lane actually supports — and its
expected magnitude (roughly doubling the bridge's belly floor from ~1.5 GW) is
the right size for a ~0.8–1.2 GW belly hole. Solved as caiso-119 A/B
(`caiso119_base_A` vs `caiso119_minload_B`, single delta 0.26 → 0.570, three
years one bundle).

## 5. NEW defect (previously unreported) — CT_PEAKER runs at ~8 % of actual

Class comparison, model annual TWh vs the bench `classFull` actual:

| class | 2024 model | 2024 actual | ratio |
|---|---|---|---|
| CC_REGULAR | 43.3 | 45.99 | 0.94 |
| CC_CHP | 8.15 | 6.78 | 1.20 |
| **CT_PEAKER** | **0.34** | **4.33** | **0.08** |
| CT_CHP | 1.55 | 2.01 | 0.77 |
| ST_GAS | 0.63 | 0.12 | 5.2 |

The model burns **8 % of actual CT_PEAKER energy** (0.34 vs 4.33 TWh; 2023 and
2025 are the same story). It is invisible to C1 because that gate's volume band
is `min(2 % of annual generation, 8 TWh)` = ~5 TWh for CAISO — a −4 TWh miss on
a 4.3 TWh class passes on an absolute band while being a 12.7× relative error.
Real CAISO peaker fleet: Panoche 1.42 TWh, Sentinel 0.48, Walnut Creek 0.32 (2024).

This matters beyond C1: peakers are the units that set the evening/scarcity
margin, and **C3c (price tail / scarcity) is one of the keeper's standing
FAILs.** A model that never starts its peakers cannot form a peaker-set tail.
Filed as the next named lane, not touched this session (one delta at a time).

*Caveat on the bench class labels:* `bench.plants[].group` labels the repowered
AES Alamitos (315) and AES Huntington Beach (335) as `ST_GAS`, but their CEMS
units are the post-2020 CCGT repowers and the scored `classFull`/`co2.byClass`
actuals put them in CC_REGULAR (`ST_GAS` actual is only 0.12 TWh in 2024). The
class table above uses `classFull` — the scored basis — not the display label.
Any per-class CEMS work must use `classFull`, or it will invent a phantom
5 TWh `ST_GAS` shortfall.

## 6. Carry-forward

**DO-NOT-REDO (new, this session):**
- **EIA-930 CISO `NG: NG` as a CAISO gas actual, in any window** — refuted on
  level (1.28–1.53× metered), shape (inverts by 2025), and energy balance
  (overfills the 2025 belly). caiso-109 condemned it; caiso-118 re-used it. The
  CAISO gas actual is the CEMS basis (`gas_cems_grid + gas_cogen_grid` /
  unit-level CEMS), full stop.
- **Any belly-gas commitment floor sized to 8–10 GW** — the target is fabricated.
  The measured belly hole is ~0.5–1.3 GW.
- **Per-class CAISO work keyed on `bench.plants[].group`** — stale for repowered
  units (Alamitos/Huntington Beach); use `classFull`.

**Still live / re-scoped:**
- The commitment-STATE direction (caiso-118b) survives, at ~1 GW. The measured
  min-load correction (§4) is its rule-13-clean first delta.
- The RA-obligation *quantity* gate stays a measured no-op (the bridged CC fleet
  is 13.7–13.8 GW pmax, inside the published 15.6–19.1 GW) — nothing to wire.
- **NEW:** CT_PEAKER 12.7× under-run (§5), plausibly coupled to the C3c tail FAIL.
- Unchanged from caiso-111/118: solar is ~98 % absorbed (no $0 rung); the WECC
  border is already cheap and corridor-capped (repricing is a volume lever); zone
  granularity is not the lever.

**Methodological note for the lane.** Both caiso-118 and caiso-118b were
derive-first, no-solve sessions that read as fully-evidenced, and the entire
chain — headline, mechanism diagnosis, redirect charter, guardrails — inherited
one unvalidated series. The cheap defence is the one applied here: before a
measured "actual" is allowed to size a mechanism, check its level against an
independent meter, its shape against the physics, and its fit against the energy
balance. All three were minutes of work and all three failed.
