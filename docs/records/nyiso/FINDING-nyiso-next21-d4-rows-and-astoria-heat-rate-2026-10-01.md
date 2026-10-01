# FINDING — NYISO-NEXT-21 phase 0: the D-4 rows are commitment symptoms, and Astoria's measured heat rate is a stack-duplicate artifact — 2026-10-01

Zero LP. Keeper `2026-09-30-nyisonext18-retiree-carry-span` + stamped `-2021`, untouched.

## 1. Open item 1 — the D-4 unit-conduct FAIL rows

Probe `scripts/probes/nyisonext21_d4_conduct_phase0.py` → `results/calibration/_nyisonext21_d4_conduct_phase0.json`. It decodes each failing plant's hourly model output (registered run payload) and its hourly CAMPD output (committed bench part), both % of nameplate.

**The keeper fails 11 rows**, together < 15 GWh of floored energy: `reliability_floor × ST_GAS` at Danskammer 2480 (every year) and Roseton 8006 (2025); `nyiso_gas_commitment_bridge` at Astoria 8906 ST_GAS (2021, 2024), Saranac 54574 CC (2021, 2024) and Athens 55405 CC (2025).

For every model-on / meter-zero hour, the probe measures the length of the **measured** off-stretch that contains it:

| plant (year) | model-on, meter-zero h | share inside a measured outage > 24 h |
|---|---|---|
| Danskammer 2480 (2021–2025) | 467–1,460 | **99–100 %** |
| Astoria 8906 ST (2021 / 2024) | 1,201 / 1,130 | **98 % / 98 %** |
| Roseton 8006 (2025) | 154 | 88 % |
| Saranac 54574 CC (2021 / 2024) | 233 / 1,320 | 83 % / 58 % |
| Athens 55405 CC (2025) | 880 | 46 % (51 % in 6–24 h) |

**Verdict: neither the window nor the eligibility is the main defect.** The floors land on days the real unit was decommitted for more than a day. The model's own run pattern is wrong upstream of any floor; the bridge only fills gaps between runs that should not exist.

- **Steam rows (Astoria, Danskammer, Roseton): a merit/commitment defect.** Astoria is the large one (§2).
- **CC rows (Saranac, Athens): partly physics.** Their measured runs are short (median 10.5–19 h; 60–77 % shorter than the bridge's class min-run of 21 h). Per-plant min-run is already adjudicated `R` (nyiso-146: shortening the min-run moved floor hours onto meter-zero hours and *created* the Saranac 2024 row). Not re-tested.

## 2. Open item 3 — NYC steam over-dispatch: Astoria's heat rate

Model vs CAMPD ST_GAS energy, TWh (keeper):

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Astoria 8906 | 2.08 / 0.72 | 3.05 / 0.89 | 2.88 / 0.77 | 2.40 / 0.92 | 2.92 / 1.35 |
| Ravenswood 2500 | 0.78 / 0.51 | 0.77 / 0.55 | 3.49 / 0.85 | 1.63 / 0.68 | 1.20 / 1.07 |
| Northport 2516 | 2.18 / 4.17 | 1.98 / 3.09 | 1.57 / 2.56 | 2.92 / 3.92 | 2.99 / 4.31 |

Astoria runs 2.2–3.7× its meter every year while Long Island steam runs short. Fleet rebuild (2023): Astoria's econ tranche offers at **$32.76/MWh** on a heat rate of **9.449**; Long Island / Hudson steam sits at $43–50 on 10.1–11.5.

**9.449 is a measurement artifact.** It comes from `campd_st_heat_rates_NYISO.csv` (armed by `measured_st_heat_rates`, F1 2026-09-24). CEMS reports each Astoria boiler on two monitored paths (`31RH`/`32SH`, `51RH`/`52SH`) and repeats the **full** gross load on both rows while each row carries only its own path's heat input. The derive scored the paths as separate units:

- each path's own rate is ~5.6 MMBtu/MWh, below any steam boiler, so the per-hour band [7, 25] rejected 98 % of hours;
- the 264–464 surviving hours per path are the minority where one path carried most of the fuel, a biased sample → 8.98 gross / 9.45 net.

Merged per hour (heat input summed, gross load counted once): **31RH 11.02, 51RH 11.04 gross** on ~24,000 steady hours each → plant **11.645 net** pooled, per-year 11.18–12.18. eGRID's independent annual rate is 11.75.

This is the same stack-duplicate defect nyiso-192 repaired in the outage merit-order panel (`campd.CAMPD_STACK_DUPLICATE_UNITS`, `stack_duplicate_mask`, `merge_stack_duplicate_units`). The heat-rate derive never got the repair.

## 3. The repair (rule 14, rule 23 — zero free parameters)

`scripts/data/derive_campd_gas_st_heat_rates.py::merge_stack_duplicates` applies the existing helpers before the screens. Re-derived under the committed invocation (`--iso NYISO`, loader defaults, `--check-pairing` passes):

- `campd_st_heat_rates_NYISO.csv`: sha256 `d5aaf4d8…` → `4bfe3747…`. **Every non-8906 line byte-identical.** 8906 pooled 9.4493 → 11.6452; seven per-year rows added (2019–2025), where none existed.
- `_units.csv`: the three 8906 path rows become two merged boilers plus unit 20; every other line byte-identical.
- Rule 23 trigger: the stack-duplicate identity defect (nyiso-141/192), not a residual.
- Tests: `tests/unit/data/test_measured_st_heat_rates.py::TestStackDuplicateMerge` (4 new; 22 pass).

**G-1 offer delta (fleet-only rebuild, all five years, control vs repaired artifact)** → `results/calibration/_nyisonext21_g1_offer_delta.json`:

- Exactly **4 rows move per year**, all Astoria 8906 ST_GAS. pmax and availability byte-identical everywhere.
- Econ-tranche offer, mean $/MWh: 2021 45.25 → 55.05; 2022 78.88 → 93.85; 2023 32.76 → 37.31; 2024 38.11 → 42.70; 2025 53.48 → 60.22.

## 4. Open item 2 — 2025 peak formation (C3a −8.6 %)

Not a lever this lane. The dual-fuel cap is `min(gas, oil)` with oil on the measured EIA-923 monthly receipt, shaped daily (`dual_fuel_oil_daily_parity` armed). The cap carries the gas CO2 rate (oil's is ~40 % higher), but that moves only switched hours, worth well under $0.1/MWh on the annual mean. nyiso-242 already sized the missed RT tail at ~4.9 pts of 2025 C3a, and that object is ledgered (C3c). 2025 passes its band.

## 5. Next

PRECOMMIT `docs/PRECOMMIT-nyiso-next21-astoria-heat-rate-2026-10-01.md`: one replay of the keeper's recipe on the repaired artifact, one shard per year.
