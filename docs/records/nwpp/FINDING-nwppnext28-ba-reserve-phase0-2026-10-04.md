# FINDING — NWPP-NEXT-28 phase 0: BA contingency reserve holding explains at most a third of the SNV/EAST CC loading gap

This phase 0 was run on keeper `2026-10-03-nwpp-next-27-path76` (bundle `results/calibration/nwppnext27_span`) with
zero LP. The probe is `scripts/probes/_nwppnext28_reserve_headroom.py`, and it writes
`results/phase0/nwpp/_nwppnext28_reserve_headroom.json`. It reads:

- the keeper's per-unit P1 `unit_marginal_<Y>`;
- the member BAs' EIA-930 hourly Demand / Net generation (Adjusted);
- the NWPP bench CAMPD hourly CF.

## A. The obligation (BAL-002-WECC-2a)

Under BAL-002-WECC-2a, each Reserve Sharing Group or Source BA holds Contingency Reserve of at least the greater of
two quantities:

- its most severe single contingency;
- 3 % of hourly load plus 3 % of hourly net generation (R1).

At least half of it must be spinning (R2).

Over the footprint the 3 % + 3 % term is 2.6–3.0 GW at peak, which is above any single footprint contingency, so it is
the binding branch. The NWPP RSG allocates the obligation to its members, and each member carries its share on its own
resources.

There is no NWPP AS market, AS price or published demand curve. The requirement is a published rule over measured load
and generation (rule 13: forward-producible).

**Zone mean requirement, MW** (the sum of member BAs, `envelopes.nwpp_ba_contingency_basis`):

| year | NW | OR | INLAND | EAST | SNV |
|---|---:|---:|---:|---:|---:|
| 2019 | 801.6 | 220.6 | 295.0 | 329.2 | 236.5 |
| 2020 | 858.5 | 222.1 | 266.9 | 321.8 | 234.8 |
| 2021 | 808.5 | 264.4 | 276.2 | 348.7 | 242.8 |
| 2022 | 860.0 | 248.6 | 283.0 | 364.9 | 247.7 |
| 2023 | 782.3 | 251.0 | 292.5 | 352.7 | 245.4 |
| 2024 | 791.3 | 258.0 | 297.7 | 364.0 | 268.4 |
| 2025 | 805.2 | 262.1 | 301.5 | 393.3 | 266.4 |

## B. How much CC loading the requirement could displace (keeper dispatch, upper bound before re-dispatch)

Method:

- "Model headroom" is the zone's online thermal and hydro headroom, `cap − mw` over units with mw > 1 MW.
- "Displaced" is Σ_t max(0, requirement_t − headroom_t), taken for the spinning half (the BAL-002 online obligation)
  and for the full requirement held online.
- "CC excess" is the model minus CAMPD energy at CC_REGULAR plants in hours both are online. This is the loading
  component of FINDING-nwppnext27 §A.

| zone-year | spin MW | model headroom MW | displaced, spin TWh | displaced, full TWh | CC loading excess TWh | CAMPD CC headroom / req |
|---|---:|---:|---:|---:|---:|---:|
| SNV 2019 | 118 | 44 | 0.75 | 1.71 | 1.97 | 2.70 |
| EAST 2019 | 165 | 220 | 0.44 | 1.41 | 2.90 | 1.74 |
| SNV 2023 | 123 | 36 | 0.83 | 1.85 | 2.95 | 3.27 |
| EAST 2023 | 176 | 206 | 0.52 | 1.61 | 0.89 | 1.30 |
| **SNV 2024** | 134 | 29 | **0.96** | 2.10 | 3.34 | 2.31 |
| **EAST 2024** | 182 | 101 | **0.86** | 2.32 | 3.30 | 1.42 |
| SNV 2025 | 133 | 31 | 0.95 | 2.07 | 2.27 | 2.36 |
| EAST 2025 | 197 | 97 | 1.00 | 2.60 | 3.00 | 1.22 |

NW, OR and INLAND displace ≤ 0.02 TWh in every year. The NW zone alone carries 18–19 GW of online hydro and thermal
headroom.

**Reading.**

- The keeper runs the SNV and EAST CCs at the cap with 30–100 MW of online headroom in the zone. Holding the spinning
  half on the zone's own online fleet opens ≤ 1.8 TWh of CC loading in 2024 (≈ 1.2 TWh in 2019). That is at most about
  a third of the 6.6 TWh SNV+EAST loading excess, and well short of the ≈ 4.2 TWh that C1 CC_REGULAR 2024
  (+12.15 TWh) needs to pass.
- The non-spinning half can sit on offline quick-start CTs and hydro, so the "full online" column is not the BAL-002
  construction. It is reported only as a bound.
- Measured CAMPD CC online headroom is 1.2–3.3× the requirement. So the reserve obligation is part of the measured
  conduct, not all of it. The rest is the native-load / base-schedule conduct in FINDING-nwppnext27 §C.

## C. Lever (owner card 2026-10-04, "Build reserve, solve")

The lever is `nwpp_ba_contingency_reserve`: default off, NWPP-only, backcast-measured requirement basis, zero fitted
scalars. It requires `energy_reserve_coopt`.

- **Families.** Each zone gets two families: a contingency family (3 % + 3 %) and a spinning family (half of it).
- **Pools.** The families draw on (zone, fuel-class) pergen pools of thermal plus hydro, using the
  `miso_reserve_online_gated` product split:
  - the gated spinning column carries `R − rho·ΣP ≤ 0`;
  - the ungated offline column counts only for quick-start CTs, oil and hydro;
  - both columns share the pool's joint `ΣP + R ≤ Σcap` row and its 10-minute ramp.
- **rho.** It is the CAMPD-measured as-operated statistic of the NWPP thermal members: **0.2130**, family set
  `nwpp_spin`, from 1,977,017 online unit-hours, with CAMPD covering 93.7 % of 27.9 GW eligible
  (`data/raw/_processed-legacy/campd_online_reserve_rho_NWPP.csv`). Hydro has no CEMS, so it shares rho, which is
  conservative.
- **Hydro ramp.** The hydro 10-minute ramp is full nameplate (`NWPP_HYDRO_RAMP10_FRAC`, the CAISO hydro class
  physics).
- **Shortfall.** A shortfall is priced at the region's `voll` ($2,000) in one step. No demand curve exists, so this adds
  no number.
- **Rule 19.** NWPP arms no other reserve, floor or commitment bridge.
- **Forward story.** The forward requirement is 3 % of forecast load plus 3 % of model generation. It is not wired, so
  the runner and forecast mode refuse the key.

Not modelled, and declared:

- **Regulation reserve.** There is no WECC numeric standard and no measured NWPP series.
- **Storage eligibility.**
- **The MSSC branch.** It is non-binding at the RSG level.
