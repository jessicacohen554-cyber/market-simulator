# `ferc-714`: FERC Form 714 hourly planning-area demand and system lambda

Lane **NWPP-NEXT** opened this store on 2026-09-25. Its record is
`docs/handoffs/FINDING-nwpp-next-psei-ferc714-gap-guard-2026-09-25.md`.

**What it is.** FERC Form 714 Part III Schedule 2 is the hourly load each
planning area reports to FERC every year. It is filed independently of EIA-930.
The NWPP pool frame (`market_sim.data.eia930.frames._pool_hourly_frame`) uses it
as the **measured substitute** when a member balancing authority's EIA-930
`Demand (Adjusted)` has a hole longer than `_HOURLY_FRAME_MAX_GAP` (72 h). Without
a substitute, the pool is refused rather than interpolated. The loader is
`market_sim.data.ferc714.load_ferc714_hourly_demand`, and the path constant is
`config.paths.FERC_714_DIR`.

## Files

| File | Rows | What |
|---|---:|---|
| `psei_hourly_planning_area_demand_2018_2024.csv` | 61,344 | Puget Sound Energy, Inc. (respondent_id 129 / csv 240 / XBRL C000171 / EIA utility 15500). Report years 2018–2024. Columns: `report_year, datetime_utc, demand_reported_mwh, respondent ids`. **Zero** NaN `demand_reported_mwh`. |
| `soco_hourly_system_lambda_2019_2025.csv` | 61,368 | Southern Company Part II Schedule 6 hourly **system lambda**, report years 2019–2025. REPORTED-ONLY. See [the section below](#soco-hourly-system-lambda-part-ii-schedule-6). |
| `SHA256SUMS.txt` | — | Identity record for both CSVs. |

## Source and how to re-fetch

- **Table.** Catalyst Cooperative PUDL, `out_ferc714__hourly_planning_area_demand`,
  `stable` release:
  `https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/out_ferc714__hourly_planning_area_demand.parquet`.
  Retrieved 2026-09-25 with `Last-Modified: Sat, 12 Sep 2026 05:18:12 GMT`.
  The whole-table parquet sha256 is
  `1b970ec0fb8fd7292706d6f316b1e92c74d451354b31f63353475769b179db95`
  (339,165,452 bytes; not committed).
- **Respondent crosswalk.** `.../stable/core_ferc714__respondent_id.parquet`, sha256
  `643fb50505266e200033ea8f03e60a3bdcf9df6004bb9c08612ad923419dcd66`.
- **Extraction.** Filter to `respondent_id_ferc714 == 129` and
  `report_date.year ∈ [2018, 2024]`. Keep **`demand_reported_mwh` only**. PUDL's
  `demand_imputed_pudl_mwh` is a model output and is never read (rule 13).
- **The primary FERC host is blocked here.** `www.ferc.gov` returns 403 through
  this environment's proxy (measured 2026-09-25), so the PUDL build of the same
  filing is the reachable copy.

## Alignment with EIA-930, measured

This is why the pool frame reconciles the series before using it. Comparing PSEI
EIA-930 `Demand (Adjusted)` with this series on the same UTC stamp:

| Period | Best clock offset | Median EIA-930 / FERC 714 |
|---|---|---|
| 2019 (8,367 h) | −1 h (first-diff r 0.96–0.99 vs 0.69–0.81 at 0) | 1.205–1.218 in every sub-period |
| 2020 (≈100 reported EIA h) | −1 h | 1.15–1.23 |
| 2021-01-01 onward | 0 h (r 0.956–0.972 vs 0.79–0.83 at ±1) | 0.996–0.999 |

PSEI's EIA-930 series changed basis and clock at the 2020/2021 year boundary. The
fill therefore takes the member's **same-year** offset and median ratio, both
measured from its overlapping hours, so the filled hours match the basis of
PSEI's own net generation and interchange.

**Also found and not repaired here:** EIA-930 PSEI demand for 2021-08-02 → 08-15
runs about 1,700 MW below FERC 714 (≈ 0.6 TWh). No NaN is involved, so the gap
guard does not see it. Routed in the FINDING.

---

## SOCO hourly system lambda (Part II Schedule 6)

Lane **soco-83** added this file on 2026-09-28. The source was verified by
soco-82 (`docs/handoffs/r-soco/FINDING-soco-82-2026-09-27.md` §2).

**Status: REPORTED-ONLY.** Owner ruling 2026-09-27: "Intake, reported-only". The
series feeds **no gate, no scorer and no LP**. It is Southern Company's own
reported marginal cost of serving load, the only hourly measured price reference
for SOCO, which has no LMP market. It is a measured *outcome*, so rule 13
`[R-MEASURED]` forbids pinning any solve to it. The loader is
`market_sim.data.ferc714.load_ferc714_system_lambda` (default respondent 253).

### File

`soco_hourly_system_lambda_2019_2025.csv`, one row per hour, 61,368 rows.

| Column | Meaning |
|---|---|
| `report_year` | FERC 714 report year |
| `datetime_utc` | Naive UTC, **hour-beginning** (the PUDL convention the PSEI file already uses) |
| `system_lambda_usd_mwh` | Reported system lambda, $/MWh, exactly as filed |
| `respondent_id_ferc714` | `253`, FERC's **native** Form 714 respondent id for Southern Company. This is not PUDL's surrogate id. XBRL-era filer CID is `C003610` |
| `eia_utility_id` | `18195` |
| `source` | `csv` (2019–2020) or `xbrl` (2021–2025) |

| Year | Rows | NaN | Zero | Negative | Missing hours | Mean $/MWh | Median $/MWh | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 8,760 | 0 | 0 | 0 | 0 | 25.72 | 26.265 | 10.81 | 195.91 |
| 2020 | 8,784 | 0 | 0 | 0 | 0 | 20.90 | 18.75 | 9.44 | 132.58 |
| 2021 | 8,760 | 0 | 0 | 0 | 0 | 37.65 | 32.815 | 15.44 | 310.29 |
| 2022 | 8,760 | 0 | 0 | 0 | 0 | 74.26 | 60.835 | 23.51 | 1,657.16 |
| 2023 | 8,760 | 0 | 0 | 0 | 0 | 29.35 | 25.79 | 11.91 | 346.57 |
| 2024 | 8,784 | 0 | 0 | 0 | 0 | 27.97 | 23.76 | 7.97 | 434.09 |
| 2025 | 8,760 | 0 | 0 | 0 | 0 | 38.11 | 34.755 | 18.06 | 429.65 |

The 2019 and 2020 means and medians reproduce soco-82's scratch measurement
exactly: $25.72 / $26.27 and $20.90 / $18.75.

### Source

The source is Catalyst Cooperative's **PUDL raw FERC-714 archive**, Zenodo record
**21738524** (v32.0.0): `https://zenodo.org/api/records/21738524`. These are the
filers' own submissions, repackaged without transformation. `www.ferc.gov`
returns 403 through this environment's proxy, so this is the reachable copy.
**No PUDL-processed or PUDL-imputed table is read.**

| Archive file | Bytes | sha256 | Used for |
|---|---:|---|---|
| `ferc714.zip` | 57,293,468 | `a2797ab2fdc3900d14930ab2b6436d49a2522ededa9069208df75cc7fb9d2d67` | 2019, 2020 (CSV era, 2006–2020) |
| `ferc714-xbrl-2021.zip` | 42,691,093 | `f1efc570d1476caa1664cc19c9de51eb4d10b7a70ab98463a4a4381cd7627060` | 2021 |
| `ferc714-xbrl-2022.zip` | 46,012,024 | `a210091233942bdf6b1b204732efe0065e8d8604815d449d310d3aa6b84cb1e4` | 2022 |
| `ferc714-xbrl-2023.zip` | 27,088,997 | `44a57e807ba5080c3dc5a41082f973bb7793de865deeaff31b41bc5cb6ac9bf8` | 2023 |
| `ferc714-xbrl-2024.zip` | 20,433,977 | `5cf2c5b60a29d7aba5480c1455e95ec9faf468498f15358daeccb899b15a75fa` | 2024 |
| `ferc714-xbrl-2025.zip` | 33,554,421 | `72aa79b0358e154fa767f6212234ea42de4a65191445699a2b4df4919324530b` | 2025 |

The zips are **not committed**. Each file's md5 also matches the Zenodo record's
`checksum` field. For context, `ferc714-xbrl-2019.zip` and `-2020.zip` contain no
Southern filing, and `ferc714-xbrl-2026.zip` contains only one unrelated
respondent. **2026 is therefore not available.**

### Extraction

- **CSV era, 2019–2020.** Member `Part 2 Schedule 6 - Balancing Authority Hourly
  System Lambda.csv`, rows where `respondent_id == 253`. There is one row per day
  (365 or 366 per year, `spplmnt_num` 0 throughout), with columns `hour01`..`hour24`.
  `hour25` is 0 on every Southern row.
- **XBRL era, 2021–2025.** Use the instance document named
  `Southern_Company_Services,_Inc._(as_Agent)_form714_Q4_<epoch>.xbrl`. Its entity
  CID must be `C003610`. Read every `ferc:SystemLambda` fact (unit `USDPerMWh`) on
  its instant context. That gives 8,760 facts per year, or 8,784 in 2024.
  - The 2023 zip holds two filings, epochs `1717156030` and `1717159291`. The later
    one is used. Its values are **identical** to the earlier one's.
  - The concept namespace changes with the taxonomy (`ferc/2022-01-01`,
    `2024-04-01`, `2025-04-01`, `2026-04-01`). The script matches the local name
    `SystemLambda`.

### Clock handling (explicit)

1. **Hours are labeled by their END in both eras.** CSV `hourNN` is the hour
   ending at NN:00. The XBRL instant `YYYY-MM-DDTHH:00` is the hour ending at
   HH:00, so a year runs from `Jan-01T01:00` to the next year's `Jan-01T00:00`.
   The extract re-labels each hour by its **beginning**.
2. **Timezone field.** It reads `CPT` (Central *Prevailing* Time) on every day of
   2019–2022 and `CST` on every day of 2023–2025.
3. **Southern's clock is a fixed UTC−6 in every year, including 2019–2022.** On a
   prevailing clock the spring-forward day has 23 hours and the fall-back day
   has 25. Southern instead files **exactly 24 values on every day of all seven
   years**, including both transition days:
   - The CSV era's `hour25` is never populated.
   - The XBRL era has 24 instants per day, 8,760 or 8,784 per year, and includes
     the non-existent `02:00→03:00` hour on spring-forward days.

   A prevailing clock cannot produce that pattern, but a fixed offset can. From
   2023 onward the filings name the fixed offset directly as `CST`. So every year
   is converted as `datetime_utc = local_hour_ending + 6 h − 1 h`. The first hour
   of each year, 00:00–01:00 CST, becomes `YYYY-01-01 06:00:00` UTC.
4. **The script refuses to build if this reading could be wrong.** It exits if:
   - any day carries a count other than 24;
   - `hour25` is populated;
   - a timezone code outside {CPT, CST} appears;
   - an XBRL year's instants fail to span `Jan-01T01:00`..`next Jan-01T00:00`.
5. **Measured, and inconclusive on its own.** I cross-correlated the
   intraday-demeaned lambda with EIA-930 SOCO demand (UTC). The best lag in DST
   months varies from 0 to +2 h across 2019–2025, and the lag across the
   14 days either side of each transition is also mixed. Solar and other
   intraday price drivers blur the load–lambda alignment too much to separate
   a 1-hour clock question. The structural argument in (3) is therefore the
   basis for the clock reading, and this correlation test is not.

### Re-fetch

```bash
python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714          # rebuild
python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --check  # prove it regenerates
```

The script downloads the six zips from Zenodo into `--cache-dir` if they are
absent and verifies each sha256 against the table above. It then rebuilds the
CSV. `--check` rebuilds the table and compares it with the committed one; it returned `IDENTICAL` on 2026-09-28. The CSV's own
sha256 is in `SHA256SUMS.txt`.
