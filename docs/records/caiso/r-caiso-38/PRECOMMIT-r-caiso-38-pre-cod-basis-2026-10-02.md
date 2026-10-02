# PRECOMMIT — R-CAISO-38 (link 20): pre-COD basis note for the battery outage census

Written and committed **before** any number below is computed. Zero LP, no shard, no `ScenarioConfig` field, no
constant, no consumer, no matrix verdict moved. Owner selection: R-CAISO-37 FINDING §6 point 2. The closeout-CAISO
lane's arms are not touched. T1 (CARRIED, 0.548 %) is adjudicated and **not re-opened**; this is a sensitivity
beside it.

## 0. Question

The census `o_860(t) = offline_MW(t) / fleet_860(t)` draws its numerator from every battery resource in the CNOG
episodes and its denominator from the EIA-860 fleet by COD month (`monthly_battery_fleet_mw`). How much offline MW
belongs to resources whose plant is **not in that denominator** in the hour's month, and what do `o_860`, T1 and T2
read with it removed?

## 1. Measure (fixed now)

- **Denominator membership, per plant and month:** rebuilt from the same inputs and the same filters as
  `storage.load_eia860_storage` (canonical vintage, status `OP`, compressed air excluded, `Operating Year ≤ year`,
  `_unit_monthly_mask`, CAISO zone lookup), kept per `Plant Code` instead of per zone. Gate: the per-plant sum must
  equal `monthly_battery_fleet_mw(year)` for every month (|Δ| < 1e-6 MW), or the probe stops.
- A census resource at hour t is **in the denominator** iff it is crosswalk-accepted and its plant has > 0 MW in the
  denominator in month(t). Otherwise it falls in exactly one class:
  - **A — accepted, pre-COD:** accepted plant whose COD (annual schedule `Operating Year/Month`; for
    `reviewed_eia860m` rows the EIA-860M COD, which is after 2025 by construction) is after month(t).
  - **B — accepted, absent for another reason** (zone, status, missing row). Reported if non-empty.
  - **U — unaccepted (unknown identity):** no accepted crosswalk row. Not labelled pre-COD.
- Resolution is the denominator's: the calendar month on the EIA-930 row clock (the census grain).
- Partial plants (some generators in, some not) count as in; the resource-vs-plant MW gap is not measured here.

## 2. Reported

Per year 2023–25: mean / p99 MW and MW-h share of offline in A, B, U; and three readings side by side:

| Reading | Numerator |
|---|---|
| **R0 adjudicated** | all census offline MW (the default probe output, byte-identical) |
| **R1 pre-COD removed** | minus class A (and B, named) |
| **R2 not-in-denominator removed** | minus A, B and U (an upper bound; U's share is unknown identity, not pre-COD) |

For each: `o_860` mean / p99 / max, T1 primary bind share and hours per direction, T2 share per direction.

## 3. Pre-registered expectations and their use

- Removing numerator MW can only raise `a(t)`, so R1/R2 T1 and T2 are ≤ R0 hour by hour. Any increase is a bug.
- 2025 class A ≈ 142 MW mean (≈ 1.07 pp of `o_860`), the R-CAISO-37 observation; 2023–24 class A depends on
  in-year CODs of annual-schedule plants.
- The R-CAISO-35 PRECOMMIT §4 bands apply as written to R0 only. R1/R2 are descriptive. Whatever they read, the
  adjudicated reading stays CARRIED and no consumer, field or verdict follows; options go to the owner as a card.

## 4. Implementation

`scripts/probes/_rcaiso35_battery_outage_census.py` gains an opt-in `--pre-cod-basis` flag that adds a
`pre_cod_basis` block. Without the flag the output is byte-identical (checked against the committed R-CAISO-37
JSON). The envelope, its derive and the crosswalk thresholds are not edited.
