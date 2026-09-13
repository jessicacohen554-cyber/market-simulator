# SOCO zonal-load provenance — FERC Form 714, not EIA-930 sub-BAs

`soco_ferc714_hourly_planning_area_demand_2023-2025.parquet` — **hourly
planning-area demand by FERC Form 714 respondent**, 2023-01-01T00 ..
2025-12-31T23 UTC, 210,431 rows over eight respondents. Landed by lane
SOCO-11 (`docs/handoffs/FINDING-soco-11-2026-09-13.md`; charter
`docs/multi-iso/soco-addition-plan-2026-09.md` §2.5, §6 row 2).

## Why this product and not the one every other ISO uses

Every prior addition — MISO's six zones, SPP's seventeen — took its zonal
load from **EIA-930 sub-BA demand**. SOCO cannot: it has no sub-BAs. Measured
at the SOCO charter by listing every `(Balancing Authority, Sub-Region)` pair
in `EIA930_SUBREGION_2023_Jan_Jun.csv`, the product covers
`CISO ERCO ISNE MISO NYIS PJM PNM SWPP` and nothing else.

The substitute is **FERC Form 714, Part 3 Schedule 2 — hourly planning-area
demand**, which each operating company files as its own respondent. That is a
*measured hourly* series per planning area, so it is strictly better than the
annual retail-sales share a lesser source would give, and it is rule-13
`[R-MEASURED]` admissible: it regenerates for a forward year from the
then-current filing and responds to changed conditions.

## Source and route

FERC's own bulk CSV host was probed **403** at the SOCO charter and **403
again from this lane's egress** (exact URLs in the FINDING's blocked table).
The series is taken instead from **PUDL's ETL of the same form**, which
publishes the filed values with a UTC stamp already attached:

    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet
    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/core_ferc714__respondent_id.parquet
    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__respondents_with_fips.parquet

Pulled **2026-09-13** (nightly build `Last-Modified: 2026-09-11T08:27:22Z`,
339,150,766 bytes). No key, no registration. Respondent names and `eia_code`
are joined from `core_ferc714__respondent_id`; nothing else is added and no
value is modified.

**Schema is the source's own**, sliced to the eight respondents and the
window:

    datetime_utc, respondent_id_ferc714, respondent_name_ferc714, eia_code,
    timezone, demand_reported_mwh, demand_imputed_pudl_mwh,
    demand_imputed_pudl_mwh_imputation_code

`demand_reported_mwh` is FERC's filed value and is the series to use.
`demand_imputed_pudl_mwh` is **PUDL's derived column**, carried for
transparency rather than for consumption: across the window it is flagged on
**550 rows** (`identical_run` 346, `double_delta` 97, `local_outlier_low` 42,
`anomalous_region` 40, `local_outlier_high` 13, `single_delta` 12) and differs
from the reported value by more than 0.01 MWh on **720 of 210,431 rows**
(max 3,479 MWh). No reported value is null.

## The eight respondents, and what each is

| id | respondent | eia_code | role |
|---:|---|---:|---|
| 2 | Alabama Power Company | 195 | Southern operating company — charter spine |
| 183 | Georgia Power Company | 7140 | Southern operating company — charter spine |
| 184 | Mississippi Power Company | 12686 | Southern operating company — charter spine |
| 186 | Southern Power Company | 16687 | Southern's merchant generation arm |
| 107 | Oglethorpe Power Company | 13994 | Georgia G&T cooperative, Georgia ITS co-owner |
| 210 | Municipal Electric Authority of Georgia | 13100 | Georgia joint-action agency, Georgia ITS co-owner |
| 1 | PowerSouth Energy Cooperative | 189 | **own BA (`AEC`)** — carried as a falsifier, see below |
| 34 | City of Tallahassee | 18445 | **own BA (`TAL`)** — carried as a falsifier, see below |

The SOCO **balancing authority** is itself a Form 714 respondent
(id 142, `eia_code` 18195, "Southern company") and PUDL attributes it 252
counties across AL/FL/GA/MS — but **it has filed no hourly demand since 2006**
(8,760 rows, all 2006). There is therefore no BA-level 714 series to check
against; the reconciliation below uses EIA-930 instead.

## Clock — Central, measured on two independent sources

The three Southern operating companies span two civil zones (Alabama and
Mississippi are Central, Georgia is Eastern), so this had to be established
rather than assumed. Two sources agree on **`America/Chicago`**:

* the committed `data/raw/eia-930-hourly/SOCO hourly.parquet` carries exactly
  two UTC-minus-local offsets, **6 h on 9,171 rows and 5 h on 17,133**,
  switching on the US DST dates — CST/CDT, never EST/EDT;
* the `timezone` column here reads `America/Chicago` for Alabama Power,
  Georgia Power, Mississippi Power, Southern Power, PowerSouth **and** the
  SOCO BA respondent. (MEAG and Tallahassee report `America/New_York`; PUDL's
  `datetime_utc` already resolves each respondent's own zone, so the UTC join
  below is unaffected either way.)

Georgia Power's *operating* clock is Eastern; Central is its *reporting*
clock on these two products, and that is what every SOCO series must adopt.
A `"SOCO": "America/Chicago"` key was added to
`scripts/data/fetch_eia930_hourly.py::BA_TIMEZONE` on that basis.

**Alignment is zero-shift UTC, measured not assumed.** Correlating the three
chartered respondents' hourly sum against `SOCO hourly.parquet::Demand` over
shifts −4 h .. +4 h peaks sharply at **k = 0 (r = 0.9935)** and falls away
monotonically either side (±1 h → 0.975/0.973, ±4 h → 0.749/0.737). So
`datetime_utc` here and `UTC time` there are the same stamp.

## THE RECONCILIATION GATE — IT FAILS AS CHARTERED

The charter's gate is that the three Southern operating companies' hourly sum
must reconcile against `SOCO hourly.parquet::Demand`. **It does not.** The
three account for **73.2 %** of the BA's metered demand:

| year | 714 three TWh | 930 BA TWh | residual TWh | residual % | pearson r | max abs Δ MW |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 168.059 | 229.436 | 61.377 | 26.75 | 0.995967 | 13,155 |
| 2024 | 173.123 | 239.349 | 66.226 | 27.67 | 0.995795 | 13,386 |
| 2025 | 175.357 | 239.518 | 64.161 | 26.79 | 0.990045 | 14,706 |

The *shape* is right (r ≈ 0.99) and the *level* is short by a quarter, every
hour of every year — the signature of whole planning areas being absent from
the sum, not of a scaling error.

**Nothing is rescaled to close it** (rule 13 `[R-MEASURED]`). The raw data is
landed with the failure documented and the lane stops, exactly as chartered.
The diagnostic below is offered to the desk as evidence, **not** applied.

### Diagnostic: two more planning areas file the same schedule inside the BA

Oglethorpe Power and MEAG are the Georgia Integrated Transmission System's
other two co-owners, and both file Form 714 hourly demand:

| sum | 2023 resid % | 2024 resid % | 2025 resid % |
|---|---:|---:|---:|
| three operating companies *(the gate)* | **26.75** | **27.67** | **26.79** |
| + Oglethorpe + MEAG | 3.03 | 2.92 | 1.26 |
| + Southern Power Co | 1.63 | 1.50 | −0.03 |
| + PowerSouth + Tallahassee *(falsifier)* | **−2.28** | **−2.41** | **−4.15** |

The last row is the point: PowerSouth and Tallahassee run their **own**
balancing authorities (`AEC`, `TAL`), and adding them **overshoots**. The
enumeration is therefore discriminating on BA membership rather than on
whichever combination minimises the residual — which is what would make it a
fitted choice and is why the falsifier is carried in the file.

**What this lane could NOT establish, and routes to the desk:** PUDL gives
100 % county containment inside the SOCO BA footprint for Alabama Power
(59/59), Georgia Power (155/155) and Mississippi Power (23/23), and 0/1 for
Tallahassee — the test works where it has data. But it carries **no county
attribution at all** for Oglethorpe, MEAG, Southern Power or PowerSouth (G&T
cooperatives and joint-action agencies have no retail territory of their own),
so containment for the two that matter cannot be settled from this source.
A documented BA-membership citation is needed before any load share is built
on the five- or six-respondent sum.

### One more thing a consumer must know: the 930 side has the defects

The largest hourly residuals are **EIA-930 dropouts, not 714 defects**. At
2025-10-23T21 UTC the BA series reads 12,638 MW while all five respondents
behave normally and sum to 24,694 MW; 2025-09-19T17 and 2025-09-06T15 are the
same class. Those hours drive the 2025 `max abs Δ` of 12,560 MW in every row
of the diagnostic table. Under rule 14 `[R-ACCURATE]` the 714 series is the
better-behaved one in those hours.

## Not derived here

No load share, no zone map, no rescaling — this lane fetches (rule 23
`[R-FROZEN-DERIVE]`). The share derivation is SOCO-32's, and it is blocked on
the membership citation above.

## Widening

The source table spans **2006-01-01 .. 2026-01-01** for all eight respondents,
so the holdout years 2019-2022 need only a re-slice of the same pull, with no
new route and no key.

**Licensing:** FERC Form 714 is a public filing; PUDL is CC-BY-4.0. See
`docs/data-licensing.md`.
