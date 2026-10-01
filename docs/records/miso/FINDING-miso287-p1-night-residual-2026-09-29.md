# FINDING — miso-287: the P1-over-P0 night residual is the coal fuel-budget dual. The stock-carry successor is killed by its pre-check. No solve.

```
LANE    : miso-287 (owner ruling "P1 vs P0 residual (Recommended)", miso-286 §6)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Keeper committed P1 hourly sidecars + run payload, fleet-only rebuilds
PRECOMMIT: docs/PRECOMMIT-miso287-coal-carry-precheck-2026-09-29.md (5d7aac49, pushed before the probe existed)
PROBES  : scripts/probes/_miso287_p1_residual.py    P0 stack vs rebuilt P1 bid stack (base + startup markup)
          scripts/probes/_miso287_class_gap.py      summer-night class MW, P1 vs merit clear
          scripts/probes/_miso287_carry_precheck.py  FLAT vs CARRY coal-row emulation (the pre-check)
OUTPUTS : results/calibration/_miso287_{p1_residual,class_gap,carry_precheck}.json
CELLS   : diurnal_price_amplitude stays G; coal_fuel_inventory stays K (carry successor: pre-check KILLED)
```

## 1. Answer

The night residual P1 carries above the P0 stack is almost all **the coal fuel-inventory rows'
dual** (`coal_fuel_inventory`, miso-259, K). In 2022 the fleet's fuel is short for the whole year.
The LP prices that shortage into coal offers in every hour, so coal leaves summer nights and gas
sets the price. The named successor, a pooled stock carry, **makes 2022 nights worse** (+$3.04),
because the annual quantity binds, not the monthly shape. It is killed by its pre-registered rule.
No admissible lever. No shards.

## 2. Correction to miso-285 §4 (the stack quantity)

miso-285 cleared the P0 stack at the keeper's non-VRE generation. That total includes **biomass and
OTHER**: must-run residual classes that `run_calibration_full` injects from EIA-923 and **nets out of
LP demand** (`_INJECTED_MUSTRUN_CLASSES`). They are not LP rows. So every "P0 stack at model Q"
number in miso-285 §4 was cleared ~2.4 GW too far up the stack.

At the corrected quantity (night h0–5 medians, $/MWh):

| year | hub (IL) | P1 | P0 stack | + startup markup | residual (P1 − bid stack) |
|---|---:|---:|---:|---:|---:|
| 2019 | 18.95 | 23.67 | 22.15 | +0.58 | +0.94 |
| 2020 | 15.80 | 19.88 | 19.09 | +0.44 | +0.35 |
| 2021 | 23.41 | 29.52 | 28.69 | +0.32 | +0.51 |
| **2022** | 42.68 | 48.05 | 41.28 | +0.48 | **+6.29** |
| 2023 | 19.35 | 27.12 | 25.87 | +0.58 | +0.67 |
| 2024 | 17.31 | 23.76 | 22.83 | +0.66 | +0.27 |
| **2025** | 24.20 | 34.69 | 32.38 | +0.38 | **+1.93** |

- "The P0 stack reproduces P1 within ±$0.3 in 5 of 7 years" does **not** survive. P1 sits $0.8–1.5
  above the corrected stack in every year.
- The stack-to-hub gap that miso-285 attributed to the real night offer book is **smaller** by
  ~$1–1.5 (2023: $6.5, was $7.8). The direction of that reading stands.
- The miso-286 CF4 pre-check shares the quantity error. It measured a Δ between two clears at the
  same Q, so its < $0.5 verdict is not moved in kind. The cell stays I.

## 3. Attribution of the residual

| candidate | verdict | evidence |
|---|---|---|
| (a) P1 startup markup | **+$0.3–0.7 every year**; not the 2022/2025 driver | `compute_monthly_markup` on the stack's own run pattern (the miso-286 validated proxy), keeper flags and v4 run ratio |
| (b) Network / congestion | **No** | Midwest is one price at night in all years. The 2022 gap is larger in hours with South *not* separated (median +7.9 vs +2.4, measured at the miso-285 quantity). South separating upward can only push the Midwest *below* a copperplate clear |
| (c) P0→P1 seam floors | **None armed** | MISO's two P1 floor hooks are off; no MISO P1 bid adjustment exists |
| (d) Reserve co-optimization | **No** | Every reserve-family dual is $0.00 at night, every year (re-verified) |
| (e) Intertemporal: **coal fuel budget** | **Yes: the 2022/2025 object** | below |
| (e) Intertemporal: hydro | small, every year | P1 runs ~1 GW less hydro at night than the stack puts on (−0.9 to −1.2 GW); part of the uniform +$0.3–0.9 |

**The coal budget, measured:**

- **2022 summer nights (Jun–Aug), P1 vs the merit clear at the same Q:** coal −16.6 GW (PRB −12.3,
  BIT −4.1), CC_REGULAR +13.4 GW, imports +3.4 GW. Night median $65.19 vs $48.02. 2025: coal −2.2 GW.
  2023: ~0.
- **The keeper's monthly coal sits flat on the cap.** 2022: 20.2–20.9 TWh every month May–Sep
  (bench, EIA-923 basis: Jul 24.3, Aug 23.2), then over the bench in the shoulder months. 2021: flat 24.0–24.5 Jun–Sep
  (bench 27.9 / 28.5 Jul/Aug). miso-263 and miso-270 already recorded both signatures.
- The mechanism's flat `annual/12` grain with no carry is its **stated limitation**. The matrix names
  an SOC-style carry as successor. That carry is what §4 tested.

## 4. The pre-check (pre-registered, 5d7aac49)

Emulator: a binding coal row acts as a uniform $/MMBtu adder `λ × HR` on coal over the row's hours.
Clear the rebuilt P1 bid stack at the keeper Q with coal raised by `λ_m`. **FLAT** is the incumbent
(`B/12` per month). **CARRY** is cumulative month-end rows `S_dec·hc + (m/12)·R·hc`, pooled-block
solution. The per-yard annual rows (K) are not emulated.

| year | P1 | FLAT | CARRY | CARRY − FLAT | annual budget / unconstrained burn (M MMBtu) | CARRY coal Jul / Aug vs bench (TWh) |
|---|---:|---:|---:|---:|---|---|
| 2021 | 29.52 | 30.10 | 29.01 | −1.09 | 3,325 / 3,178 (ample) | 29.1 / 30.8 vs 27.9 / 28.5 |
| **2022** | 48.05 | **49.73** | **52.77** | **+3.04** | **2,792 / 3,482 (short 20 %)** | 27.7 / 28.5 vs 24.3 / 23.2 |
| 2023 | 27.12 | 26.48 | 26.45 | −0.03 | 2,793 / 2,076 (ample) | 20.5 / 20.5 vs 20.7 / 20.6 |
| 2025 | 34.69 | 33.59 | 32.76 | −0.83 | 2,691 / 2,449 (ample) | 23.1 / 20.8 vs 21.4 / 19.2 |

**Kill rule, as registered:**

1. Gate V (FLAT reproduces P1 2022 within ±$1.5): **FAIL**, $1.68. The emulator's gap sits in the
   shoulder months, where the un-emulated per-yard rows cut P1 coal below FLAT (Mar–Apr, Oct–Nov).
2. CARRY moves the 2022 night median down by ≥ $2.0: **FAIL**, it moves it **up $3.04**.
3. No year up by more than $0.5: **FAIL** (2022).

**KILLED.** In 2022 the fleet opened on the lowest January stock on record (miso-258). The annual
fuel is 20 % short of what the fleet would burn at base cost. A carry spreads that scarcity as one
~$1.8/MMBtu (~$20/MWh) adder over **every** month, and pushes it into spring and fall nights. It also
moves summer coal *above* the bench in every binding year. In 2021 and 2025, where only the monthly shape
binds, the carry would lower nights by ~$1, but it over-runs summer coal against the bench. That is not a
case this lane can promote on.

## 5. Where MISO stands

- Keeper unchanged. Train tier 2023–2025 **CALIBRATED** (C3c ledgered).
- Full span **NOT-YET** on three routed misses: C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.**
  Routed misses are still failures.
- The 2022 night overshoot is the price of a physical fuel shortage, and in 2022 the model already
  burns *more* coal than the bench (234.5 vs 226.3 TWh, coal classes) and less gas (159 vs 195). So the quantity the
  budget allows is not too tight. The open question is how the real fleet **expressed** 2022 coal
  scarcity (offer adders vs derates/outages/deferred burn), which this lane cannot answer from
  committed artifacts.
- **Cells:** `diurnal_price_amplitude` stays **G** (now decomposed; §2 corrects miso-285).
  `coal_fuel_inventory` stays **K**; its named carry successor is recorded as **pre-check killed**.

## 6. Owner ruling (2026-09-30)

*"2022 coal-scarcity study"*. The next lane (miso-288) runs a zero-LP, data-first study of how the real 2022 MISO
fleet expressed its coal shortage: offer adders (fuel-conservation opportunity cost) vs derates, outages and
deferred burn. The question it answers is whether the LP's uniform coal dual on 2022 nights is realistic. It may
find nothing admissible.
