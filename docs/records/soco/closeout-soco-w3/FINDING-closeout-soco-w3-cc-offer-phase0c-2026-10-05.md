# FINDING closeout-SOCO-w3 phase 0c: CC-below-coal at night is measured economics — NOT CHARTERED

Lane closeout-SOCO-w3, 2026-10-05. Zero LP. Desk direction (2026-10-04): take the residual the diagnostic named (CC
offer position and heat rate against coal), stacked on the holdout recipe with the holdout probe as control. Check the
measured inputs that set CC below coal at night before any PRECOMMIT. The desk agreed with the conduct reading
(2026-10-05).

- Control: `results/calibration/closeout_soco_w3_span`.
- Probe: `scripts/probes/_closeout_socow3_cc_offer_decomp.py`. Each year is one `fleet_only` rebuild of the control
  through `scripts/lib/bundle_fleet.reconstruct_bundle_fleet` (fidelity-guarded).
- Per-year output: `phase0c_<year>.json`.
- Census: `parasitic_census_all_iso.csv`.

## 1. Offer build-up (what the LP sees)

Every coal and CC tranche's `mc_base` = HR × fuel + VOM. The implied VOM is 4.50 $/MWh for coal and 2.00 for CC in
every year (cited constants).

Example, 2021 night:

| Unit | HR | Fuel | Offer |
|---|---|---|---|
| Bowen committed | 10.13 | $2.83 | $33.17 |
| Scherer committed | 10.82 | $2.65 | $33.20 |
| CC McDonough (710) | 6.80 | $4.02 | $29.35 |

## 2. Heat rates: the model's are the plants' own CEMS rates

The tranche HRs are the measured artifacts (`campd_coal_heat_rates_SOCO.csv`, `campd_cc_heat_rates_SOCO.csv`, K):

- Bowen 2021: CEMS gross 9.777 → net 10.51 at factor 0.93.
- Scherer 2021: CEMS gross 10.506 → net 11.30.
- Committed bands carry the frozen incremental ratio.

No input error here.

## 3. Fuel vs each plant's own EIA-923 Schedule-2 delivered price

Capacity-weighted. Plant-months whose ratio falls outside [0.67, 1.5] are F923 print outliers, reported and excluded
from the robust gap.

| Year | CC gas robust gap $/MMBtu ($/MWh) | F923 gas outliers | Coal gap |
|---|---|---|---|
| 2019 | +0.04 (+0.29) | 2 | 0.00 |
| 2020 | +0.04 (+0.28) | 4 | 0.00 |
| 2021 | **+0.15 (+1.06)** | 3 (incl. plant 57037, May, $34.07/MMBtu) | 0.00 |
| 2022 | −0.33 (−2.30) | 11 | 0.00 |
| 2023 | +0.07 (+0.51) | 8 | 0.00 |
| 2024 | −0.06 (−0.39) | 6 | 0.00 |
| 2025 | −0.08 (−0.58) | 6 | 0.00 |

- **Coal** is priced at its own F923 delivered cost exactly.
- **CC gas** (HH monthly plus the measured SE basis, `gas_basis_measured_by_year` K) is within about ±$0.15/MMBtu of
  the plants' own receipts, except 2022, where the model is above F923.
- **2021**, the one year whose CC record stays FAIL, has CC under-priced by about $1.1/MWh. The sign is right, but it
  is small against what is needed (§6).
- The Transco Z4/Z5-vs-Henry question is the SE basis, already measured.

## 4. Parasitic coverage gap (new; wrong sign for this object)

`parasitic_load_factors.parquet` carries **no SOCO plant**. Every SOCO measured-HR artifact therefore converts CEMS
gross to net on the class default: coal 0.93, CC 0.975, CT 0.99, ST 0.95.

The plant's own factor, computed by the frozen construction (`campd.compute_parasitic_factors`, EIA-923 net / CAMPD
gross, nothing written):

| Year | Coal measured (vs 0.93) | Coal offer change | CC measured (vs 0.975) | CC offer change |
|---|---|---|---|---|
| 2019 | 0.929 | +0.05 | 0.974 | +0.03 |
| 2020 | 0.913 | +0.62 | 0.965 | +0.20 |
| 2021 | 0.912 | +0.65 | 0.973 | +0.06 |
| 2022 | 0.909 | +0.97 | 0.975 | +0.03 |
| 2023 | 0.904 | +1.42 | 0.960 | +0.38 |
| 2024 | 0.925 | +0.33 | 0.979 | −0.08 |
| 2025 | 0.917 | +0.53 | 0.969 | +0.21 |

Pooled plant values: Scherer 0.883, Bowen 0.915, Gaston 0.914, Miller 0.937; McDonough CC 0.987, McIntosh CC 0.988.

- The correction widens the coal-minus-CC spread by **+$0.02 to +$1.04/MWh**. It deepens the CC over-run.
- It is a rule-14 repair, not a lever for this residual. The desk chartered it as its own structural lane
  (2026-10-05), with the expected worsening declared ex ante.
- Cross-ISO census (zero LP, nothing fixed outside SOCO): CAISO, NWPP and SOCO carry no row at all. NYISO is missing
  48 of 49 plants, SPP 95/109, MISO 145/194, PJM 12/199 and ERCOT 2/91; NEISO is complete
  (`parasitic_census_all_iso.csv`).

## 5. CC commitment physics

Already adjudicated:

- **soco-85:** CC incremental HR on the frozen construction.
- **soco-92:** sunk LSL block plus measured incremental segments at measured night loading. Coal becomes marginal and
  night prices rise; no status moved. The owner ruled "Close the reopen".

A minimum load cannot lower in-merit CC: CC sits below coal at night on measured costs. Re-opening needs the owner.

## 6. Reach

Idle non-must-run coal headroom (TWh/yr) whose P1 offer is within $x above the hour's LMP:

| Year | $1 | $2 | $3 | $4 | $6 |
|---|---|---|---|---|---|
| 2019 | 2.96 | 5.91 | 9.44 | 11.43 | 14.81 |
| 2021 | 1.37 | 2.45 | 3.13 | 3.78 | 5.16 |
| 2023 | 0.77 | 1.80 | 2.87 | 3.56 | 4.73 |

CC 2021 needs about −1.53 TWh, which is about $1–2/MWh of coal-vs-CC movement (static, before the CC share). The
measured inputs net to about +$0.4/MWh in 2021 in the wrong direction:

- gas: +$1.06 toward coal;
- parasitic: −$0.59 against.

## 7. Verdict

- Every measured input that sets the night ordering is faithful: HR, coal fuel, and gas within its robust noise.
- The one coverage gap (parasitic) corrects in the wrong direction.
- The commitment-physics route is adjudicated and closed by the owner.
- VOM is a cited constant that free data cannot identify, and tuning it is forbidden (rules 1, 13).
- **NOT CHARTERED; no solve PRECOMMIT.** The residual is Southern dispatching coal against its own measured
  economics: frontier row SOCO-F1 (conduct / lambda fuel basis). The re-open condition (Georgia PSC FCR / Alabama ECR
  burn-plan testimony) is unchanged.
