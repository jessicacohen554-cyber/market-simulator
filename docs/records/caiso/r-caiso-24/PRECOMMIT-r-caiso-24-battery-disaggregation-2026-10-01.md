# PRECOMMIT (scoping) — R-CAISO-24: battery disaggregation for the RT h18 ramp peak. The bound says no.

Keeper: `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged. **Zero LP, no
build, no shard, no `ScenarioConfig` field, no cell moved.**
Probe: `scripts/probes/_rcaiso24_h18_bound.py` (Part A, plus `--stack` for Part B; ~90 s per year).
Outputs (gitignored scratch): `results/calibration/_rcaiso24/partA_h18.json`, `partB_stack.json`. Every number
cited is below. Clock and hub mapping as R-CAISO-21 (`_rcaiso21_evening_phase0.py`).

## 0. Result

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| SP15_rest RT h18 residual, model − measured ($/MWh) | +1.1 | **−13.9** | **−6.0** | −1.1 |
| … from the measured top-5 % h18 hours (C3c tail) | −10.9 | −8.6 | −4.7 | −1.6 |
| … from the body (other 95 %) | +12.0 | **−5.3** | **−1.3** | +0.5 |
| Body median hourly residual | +12.2 | −1.4 | −1.0 | +0.9 |
| Model − measured battery net discharge at h18, body mean (MW) | +426 | +149 | −131 | −766 |
| **Price lift if model h18 battery = measured (gas-stack bound)** | +2.1 | **+0.5** | **−0.2** | **−1.5** |

**The payoff left to buy is the body: ≤ $5.3 (2023), ≤ $1.3 (2024), nothing in 2025.** The rest of the h18
gap is the C3c tail, which a battery representation does not price (R-CAISO-21 §2, R-CAISO-22).

**A battery fix cannot buy even the body.** Moving the model's h18 battery output exactly onto the measured
fleet's lifts price by **+$0.5 in 2023** and **lowers it in 2024–25**: there the model already discharges
*less* than measured at h18 (−131 / −766 MW), so a more faithful fleet would deepen the under-price.

## 1. What the model carries today

`model/storage.py::load_eia860_storage` pools every EIA-860 battery in a zone into **one `StorageUnit` per
zone**, with summed power and summed energy (2023 fleet: 27.1 GWh; 2025: 53.0 GWh). A 1-hour and a 4-hour
battery share one state of charge, so the pool's duration is the MWh-weighted blend. Disaggregation would
split each zone's pool by EIA-860 duration class and coupling type.

Pooling is a **relaxation** of the disaggregated fleet: every disaggregated schedule is feasible for the pool,
not the reverse. A split can only remove flexibility. Mostly that means short units can no longer borrow
energy from long ones to stay at full power through the shoulders. That moves discharge toward the single
peak hour, which pushes h18 price **down**. The sign is not proved without a solve, but nothing in the
structure points toward the needed lift. §0 bounds the outcome either way.

## 2. Bound construction (Part B)

For each h18 body hour (measured RT below that year's h18 p95, so 344–346 h/yr), take
Δ = model net discharge − Outlook measured net discharge. Read the keeper's own zero-LP in-state gas stack
(`mc_base × pmax × availability`, the R-CAISO-22 `--stack` construction) at the model's gas dispatch and at
dispatch + Δ. The price difference is the lift. Only gas responds here; imports, hydro and PS are held fixed.
That makes the stack steeper than the system's real one, so **|lift| is an over-statement**: the bound is
generous to the lever and still near zero.

Comparator basis: CAISO Today's Outlook "Total batteries" (stand-alone + the battery half of hybrids;
`data/raw/storage-dispatch-actuals`). The same basis gives gross h17–21 discharge as model 1,809 / 3,316 /
4,328 MW against measured 1,768 / 3,499 / 5,095 MW (2023–25). Earlier windowed comparisons on a different
comparator report an evening *over*-discharge (caiso-170 §5). On the Outlook total-batteries basis, h18 is
at or under measured from 2024 on. Both are reported; the bound uses Outlook because it is the only
whole-fleet series.

## 3. Measured inputs a disaggregation would need

| Input | Needed for | Held? |
|---|---|---|
| Per-unit MW, MWh (duration), COD, coupling (AC / DC / DC-tight) | Duration classes; DC-coupled charge-from-PV-only limit | **Held**: EIA-860 3_4 (`eia860_energy_storage_operable.parquet`). The CA 2025 vintage has 14.9 GW / 50.4 GWh: ≈72 % of MW at ~4 h and ≈16 % at ≤1.5 h. Coupling is flagged on ~40 % of MW. |
| SOC bounds / SOC trajectory | Per-class SOC min/max; validation | **Partial**: CAISO DESR `SOC`, hourly 2023–25, **stand-alone only and system-level**. No per-class or per-resource SOC. |
| RA must-offer window | Storage offer obligation (AAH 4–9 pm; slice-of-day from 2025) | **Not held** as data. Not encoded for storage in `config/`. A CPUC/CAISO tariff intake would be needed. |
| Battery bid curves | Per-class offer shape | **Partial**: OASIS `PUB_DAM_GRP` is gitignored (re-fetch ~2 h, 2023–25). Resources are masked, with no fuel tag. caiso-176/178 committed derived artifacts and found the bid stack **does not identify** a battery offer parameter. |
| Per-class hourly dispatch | Validation of the split | **Not published.** Outlook and DESR are fleet totals (DESR splits LESR/HYBD only). |

So a split by duration and coupling is **buildable from measured data** (EIA-860), and is structural rather
than a fitted shape. What is missing is any **per-class behavioural** input (SOC, bids, must-offer window),
so the split's behaviour would come from LP arbitrage alone. That is the same operator that already places
h18 discharge at or under measured.

## 4. Matrix check (rule 28)

CAISO storage cells: `caiso_da_rt_two_settlement` R (caiso-170), `storage_daily_cycling` G (caiso-169),
`ercot_storage_adaptive_expectation` I (caiso-204), `battery_dispatch_adder` K at 0, `storage_measured_anchors`
K (the shape envelope), `caiso_ps_charge_shape_anchor` G, `storage_measured_base_fleet` I. None is re-tested
here. The aggregated-representation pointer (caiso-170 §5) was handed forward **as a pointer, not a verdict**.
This session measures its reach and finds it ≤ $0.5/MWh, of the wrong sign in 2 of 3 years. No field exists,
so there is no cell to set. The pointer is recorded as **spent on reach**, in the caiso-170 pattern
(refused on measured reach, not on structure).

## 5. DO-NOT-REDO (new)

- **Building a disaggregated battery fleet to raise the RT h18 price.** §0: a perfect placement match buys
  ≤ $0.5 (2023) and the wrong sign in 2024–25. New evidence would be a per-class behavioural input
  (§3: per-resource SOC or unmasked battery bids). A re-cut of the same Outlook comparison is not new evidence.
- Quoting the h18 −13.9 (2023) as a storage object without its tail split: −8.6 of it is C3c.

## 6. Decision

Nothing to promote. The next step was put to the owner as a decision card (§7).

## 7. Owner ruling

Decision card, 2026-10-01. Three of four options selected:

1. **Close link 6 and go to link 7** (R-CAISO-25, same-day gas scoping). The aggregated-battery pointer is
   **spent on reach**: no field, no cell.
2. **Ledger the h18 body residual.** The 2023 body residual (−$5.3 mean, −$1.4 median; 2024 −$1.3 / −$1.0) is
   recorded on the CAISO shard as a **known shape residual, not a lever**.
3. **Scope per-resource battery data** as a later link (**link 10, R-CAISO-28**, queued after link 9). It looks
   for a per-class behavioural input: per-resource SOC or unmasked battery bids. That is the only new evidence
   that could re-open §5.

Not selected: building the split anyway.
