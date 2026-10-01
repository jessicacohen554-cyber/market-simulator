# FINDING — miso-281 phase 0: 2019 MISO-South gas steam ran out of merit, not below its economics. No solve earned.

```
LANE    : miso-281 (owner pick on the miso-280 card "Probe 2019 South steam (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025) — unchanged
TARGET  : C1 ST_GAS 2019 −8.003 TWh (band ±8.00). Not tuned against (rule 1).
LP      : none (zero-LP: fleet-only rebuilds + CEMS hourly + EIA-923 + measured hub LMP)
PROBES  : scripts/probes/_miso281_south_steam_2019.py  (fleet-only rebuild, per-unit offer/floor/price-taker envelope)
          scripts/probes/_miso281_south_steam_oom.py   (out-of-merit classification of measured conduct)
          -> results/calibration/_miso281_south_steam_oom.json (2019-2025)
```

## 1. Answer

The floored MISO-South gas-steam plants do **not** under-run because their offers are too high or the model's price
is too low. In 2019 the real plants produced **85 % of their energy in hours when the measured hub LMP was below
their own measured marginal cost**. The model reproduces the in-merit part and the floor part. What it lacks is
the **extra out-of-merit commitment** the real system ran in 2019–2020 above what the 2023–25-measured floors carry.
That is a load-pocket / VLR commitment object (`scuc_load_pocket_commitment`, `·`), already routed to RO-2.

## 2. The model is consistent with its own economics

2019, MISO-South ST_GAS, fleet-only rebuild of the keeper recipe (TWh):

| available | floor | price-taker envelope at model price | model ST_GAS (all zones, class-hourly) |
|---:|---:|---:|---:|
| 56.2 | 9.5 | 13.0 (all zones 14.6) | 14.1 |

Realized ≈ envelope: the LP runs ST_GAS whenever its own clearing price covers the P0 offer. Nothing is withheld.

**Inputs are not the cause:**
- **Price.** Model MISO-South mean **$28.26** vs measured RT hubs LA **$24.86**, MS $24.29, AR $23.22, TX $26.51
  (DA LA $26.45). The model price is *above* the real one.
- **Offers.** Model offers (non-peak tranches) sit within about ±$3/MWh of each plant's measured full cost
  (CEMS hourly heat rate on a net basis × delivered gas + non-fuel), e.g. Ninemile $31.4–35.8 vs $31.9,
  Little Gypsy $34.6 vs $35.9, Lewis Creek from $29.2 vs $30.8.
- **Availability.** 56 TWh available vs 20 TWh actual. Not binding.

## 3. The real plants ran out of merit

Plant-hour classified OUT OF MERIT when the measured RT hub LMP of the plant's state hub is below the plant's
measured marginal cost. 2019, top plants (TWh; $/MWh):

| plant | EIA-923 net | out-of-merit | model floor | model envelope | on-hours | measured cost | hub LMP when on |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ninemile Point 1403 | 5.84 | 4.87 | 5.50 | 5.69 | 8194 | 31.9 | 25.0 |
| Sabine 3459 | 3.25 | 2.78 | 1.82 | 2.46 | 8276 | 33.3 | 26.4 |
| Little Gypsy 1402 | 2.71 | 2.30 | 0.20 | 0.94 | 7749 | 35.9 | 25.1 |
| Lewis Creek 3457 | 2.19 | 1.76 | 0.82 | 1.33 | 8760 | 30.8 | 26.5 |
| Baxter Wilson 2050 | 1.54 | 1.38 | 0.52 | 0.71 | 4067 | 33.7 | 24.3 |
| Big Cajun 2 6055 | 1.48 | 1.32 | 0.22 | 0.34 | 4300 | 35.4 | 24.7 |
| Teche 1400 | 0.99 | 0.83 | 0.27 | 0.83 | 6553 | 32.8 | 25.2 |
| Waterford 1&2 8056 | 0.66 | 0.59 | 0.00 | 0.03 | 3298 | 40.7 | 25.8 |
| Brame 6190 | 0.59 | 0.46 | 0.12 | 0.18 | 3360 | 32.3 | 25.4 |
| Gerald Andrus 8054 | 0.54 | 0.51 | 0.00 | 0.32 | 1862 | 90.7 | 25.0 |

South total 2019: **20.2 TWh actual, 17.1 out of merit**. Robust to the cost definition:

| definition | out-of-merit TWh (2019) |
|---|---:|
| full measured cost vs hub | 17.1 |
| fuel only vs hub | 14.4 |
| fuel only vs hub + $5/MWh nodal allowance | 7.9 |

Signature of commitment, not economics: 7,700–8,760 on-hours at Ninemile, Sabine, Little Gypsy and Lewis Creek, at
LMPs ~$5–10 below cost. 35–67 % of their energy was produced below half of observed max load (min-load operation).

**Decomposition, 2019 South:** in-merit actual 3.0 vs model above-floor envelope 3.5 (economics matches);
out-of-merit actual 17.1 vs model floor 9.5 → **~7.6 TWh missing**, the same size as C1 (−8.0 TWh; C1 is on the
grid-delivered basis, 8.4 vs 16.4, so the two bases do not reconcile to the MWh).

## 4. Across the span: explains 2019–2020, not 2021–2022

South, plant-net basis, TWh:

| year | actual | out-of-merit | model floor | OOM − floor | C1 ST_GAS |
|---|---:|---:|---:|---:|---:|
| 2019 | 20.2 | 17.1 | 9.5 | **+7.6** | −8.00 FAIL |
| 2020 | 19.2 | 16.4 | 9.6 | +6.8 | −6.40 |
| 2021 | 11.3 | 8.5 | 8.1 | +0.4 | −5.24 |
| 2022 | 13.2 | 6.7 | 9.0 | −2.3 | −5.11 |
| 2023 | 13.2 | 8.8 | 7.8 | +1.0 | −0.23 |
| 2024 | 16.0 | 11.9 | 8.2 | +3.7 | −1.90 |
| 2025 | 13.0 | 10.0 | 8.7 | +1.4 | skipped |

- The 2023–25 floors carry the out-of-merit volume of their own window roughly. 2019–2020 ran ~7 TWh/yr more.
- 2021–2022 residuals are **not** this object: out-of-merit ≈ floor there. Those years carry a separate in-merit
  shortfall (high-gas years). Not investigated here; stated so it is not over-claimed.
- Coincident structure, not proven cause: South CC_REGULAR grows 12.3 → 14.9 GW in the fleet 2019 → 2023,
  including Lake Charles Power Station (60927, 2020) and Montgomery County Power Station (60925, 2021), both in the
  WOTAB area. New local CC would reduce the need to commit legacy steam for local reliability.

## 5. Levers considered

| lever | verdict |
|---|---|
| Correct ST_GAS heat rate / gas price / offer | **No.** Model offers ≈ measured cost; model price already above measured. |
| Own-year floor level/window from 2019 CEMS conduct | **Refused (rule 13).** Pins the year's own outcome; no forward driver regenerates it. `mustrun_online_frac_per_year` is already `R`. |
| ST_GAS `offer_curve_by_group` band multiplier | **Refused.** One config across all years (rule 1(b)) would lift 2023–25, where C1 already passes; and it would buy out-of-merit energy through a price channel, which is the wrong mechanism. |
| Load-pocket / VLR commitment with requirement from physics | **Right mechanism, not buildable now.** No public commitment MW/hours (miso-280 §2); requirement needs pocket load vs import capability under N-1-G-1 — the RO-2 reduced-network class, with C3a 2022. |

**Verdict: no solve earned.** Cell `scuc_load_pocket_commitment` stays `·` with this sizing added as evidence: the
object is ~7 TWh/yr of 2019–2020 out-of-merit South steam above the pooled floors.

## 6. Owner rulings (2026-09-28)

1. **C1 ST_GAS 2019:** "Routed miss (Recommended)". Recorded with C3a 2022 and C3b 2021 as known limitations. It
   reopens only with a load-pocket / VLR commitment mechanism (RO-2 class).
2. **Frontier: NOT declared.** The owner's standing direction allows frontier only when the rubric clears for all
   years. Routed misses are still failures. MISO stays NOT-YET on the full span 2019–2025 (train 2023–2025
   CALIBRATED). This session briefly recommended a frontier call, and the owner corrected it.
3. **Next lane:** "2021–22 ST_GAS in-merit gap (Recommended)". This is a zero-LP phase 0 on the 2021–2022 ST_GAS
   shortfall, which §4 shows is **not** this out-of-merit object.
