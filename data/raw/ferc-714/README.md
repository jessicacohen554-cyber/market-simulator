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
| `soco_neighbor_hourly_system_lambda_2019_2025.csv` | 552,286 | Part II Schedule 6 hourly **system lambda** of SOCO's nine neighbours (TVA, DUK, CPLE, FPC, FPL, SC, TAL, JEA, MISO), long form, report years 2019–2025. REPORTED-ONLY. See [the neighbours section](#soco-neighbour-hourly-system-lambdas-part-ii-schedule-6). |
| `SHA256SUMS.txt` | — | Identity record for all three CSVs. |

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

---

## SOCO neighbour hourly system lambdas (Part II Schedule 6)

Lane **soco-97** added this file on 2026-10-01, under owner ruling soco-97
option (d), data step 1 of
`docs/records/soco/r-soco/FINDING-soco-97-interchange-rule14-phase0-2026-10-01.md` §5.

**Status: REPORTED-ONLY.** The series feeds **no gate, no scorer and no LP**. A
neighbour's lambda is a measured *outcome*, so rule 13 `[R-MEASURED]` forbids
pinning any solve to it. Its one admissible later use is as a per-year
`hr_by_year` anchor, which is a forecast-lane input. That use would need its own
ruling. The loader is `market_sim.data.ferc714.load_ferc714_system_lambda(respondent_id=…)`.
The respondent registry is `SOCO_NEIGHBOR_LAMBDA_RESPONDENTS` in the same module.

### File

`soco_neighbor_hourly_system_lambda_2019_2025.csv` has 552,286 rows and is
sorted by `ba_code`, then `datetime_utc`. Its columns are `ba_code` (the EIA-930
BA code) followed by the Southern file's six columns, which have the same
meanings: `datetime_utc` is naive UTC, **hour-beginning**, and the value is
exactly as filed. A row exists only where the filer reported a value. Hours
the filer did not report are absent, never filled.

| `ba_code` | Respondent | FERC id | EIA id | XBRL CID | Rows | NaN | Zero | Mean $/MWh | Max $/MWh | Elliott mean | Elliott max |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| TVA | Tennessee Valley Authority | 263 | 18642 | C004480 | 61,361 | 0 | 1 | 30.55 | 3,300.00 | 529.43 | 3,300.00 |
| DUK | Duke Energy Carolinas | 157 | 5416 | C000290 | 61,363 | 0 | 0 | 34.58 | 990.48 | 387.87 | 990.48 |
| CPLE | Duke Energy Progress (CSV: "Progress Energy (Carolina Power & Light)") | 233 | 3046 | C000135 | 61,363 | 0 | 0 | 31.53 | 623.66 | 271.03 | 623.66 |
| FPC | Duke Energy Florida (CSV: "Progress Energy (Florida Power Corp.)") | 234 | 6455 | C000136 | 61,361 | 0 | 0 | 29.08 | 292.70 | 53.48 | 104.30 |
| FPL | Florida Power & Light | 171 | 6452 | C001030 | 61,367 | 0 | 0 | 19.62 | 127.00 | 38.72 | 50.00 |
| SC | Santee Cooper (South Carolina Public Service Authority) | 251 | 17543 | C011420 | 61,368 | 0 | 0 | 38.87 | 6,219.37 | 350.04 | 909.95 |
| TAL | City of Tallahassee | 140 | 18445 | C011474 | 61,368 | 0 | 79 | 22.21 | 86.60 | 53.12 | 64.25 |
| JEA | JEA | 186 | 9617 | C011421 | 61,368 | 0 | 0 | 30.42 | 246.24 | 70.42 | 141.19 |
| MISO | MISO | 321 | 56669 | C001344 | 61,367 | 0 | 1 | 34.66 | 2,167.66 | 236.26 | 2,167.66 |

Notes on the table:

- **Elliott** is the 96 UTC hours from 2022-12-23 00:00 through 2022-12-26 23:00.
  Every respondent reports all 96.
- **Rows.** A full 2019–2025 span is 61,368 hours. A respondent read as
  prevailing in a year is one hour short in that year (see the clock section).
  MISO 2023 also omits HE04 on 2023-08-17.
- **Zeros are kept as filed.** Tallahassee's 79 zeros are scattered
  filing gaps, some of them multi-hour, in every year. TVA's one zero is on
  2022-10-09, and MISO's is on 2020-06-02 (MISO also files 23 negative hours).
- **Santee Cooper's maximum** is $6,219.37 on 2022-05-12 19:00 UTC. It is
  the first of three hours above $5,900. The value is as filed and has not
  been checked against another source.

Per-year means reproduce the soco-97 phase-0 probe to within $0.02.

### Flags

- **Dominion Energy South Carolina (SCEG; FERC id 250, CID C000241) is NOT
  shipped.** Its Sch. 6 is **0.00 in every hour of every year it filed**:
  - the CSV era 2020 (366 days, blank timezone code);
  - every XBRL year 2021–2025.

  It filed no Sch. 6 for 2019. This is the largest SOCO export seam, and it
  has no usable lambda.
- **FPL's lambda runs about 40 % below SOCO's**, for example $17.31 against
  $25.72 in 2019. FPL files it in whole dollars from 2021. **The basis is
  unresolved.** Do not read FPL's level as comparable to the others until
  that is explained.
- **Fall-back-day sums.** Duke Carolinas and Duke Progress (2023–2025) and
  Duke Florida (every XBRL year) file the repeated 01:00–02:00 hour on the
  fall-back day as about **twice** its neighbours. That is the two
  occurrences summed into one slot. The value is kept as filed (see clock
  handling, point 4).
- **MISO CSV era.** The CSV archive holds MISO (FERC id 321) Sch. 6 rows for
  every report year 2009–2020, coded `EST`. They are **not** XBRL-only, so
  2019–2020 come from the CSV like the others.
- **Resubmissions.** The latest filing (largest epoch) is used. Earlier
  filings whose values differ are FPL 2022, Santee Cooper 2022 and JEA 2023.
  All other earlier filings are identical. The build prints which is which.

### Clock handling (per respondent-year, explicit)

Southern's fixed UTC−6 reading was proven for Southern only, so it is **not
transferred**. Instead, `classify_clock` classifies each respondent-year from
its **own** filing pattern. The test is the one Southern's reading rests on:
on the spring-forward day, a prevailing clock has 23 hours and a fixed clock
has 24.

| Pattern on the spring-forward day | Verdict | Conversion |
|---|---|---|
| 24 real (non-zero, non-blank) values | **fixed** | `utc = local − standard offset` (EST −5, CST −6). |
| 23 real values: the HE02 or HE03 instant is omitted, or present as a 0/blank placeholder | **prevailing** | The placeholder is **dropped**, never published as a lambda. Each hour-ending instant is localized in the respondent's IANA zone. On the spring-forward day, the non-existent 02:00 shifts forward to 03:00. On the fall-back day, the ambiguous 01:00 is read as daylight time. |
| Anything else | **REFUSE** | The build exits. |

The build also refuses if any of these hold:

- `hour25` is populated;
- a day carries more than 24 values;
- the fall-back day does not carry exactly 24 values;
- a timezone code falls outside the respondent's registered set.

**No filer ever uses `hour25`.** A prevailing filer reports 24 values on the
fall-back day, so one UTC hour, the first 01:00–02:00, is unreported in each
prevailing year. The filed value lands on the second occurrence.

| `ba_code` | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Codes filed |
|---|---|---|---|---|---|---|---|---|
| TVA | P | P | P | P | P | P | P | CST/CDT per day (2021: `CST` every day) |
| DUK | P | P | **F** | **F** | P | P | P | 2019 EST/EDT; 2020–22 `EPT`; 2023–25 EST/EDT |
| CPLE | P | P | **F** | **F** | P | P | P | 2019–22 `EPT`; 2023–25 EST/EDT |
| FPC | P | P | P | P | P | P | P | EST/EDT per day (transition days `EST/EDT`, `EDT/EST`) |
| FPL | F | F | F | **P** | F | F | F | `EST` (2020: EST/EDT per day) |
| SC | F | F | F | F | F | F | F | 2019–20 EST/EDT per day; 2021–25 `EST` |
| TAL | F | F | F | F | F | F | F | EST/EDT per day; 2021 `UTC`; 2022 `EST` |
| JEA | F | F | F | F | F | F | F | `EST` (2021: `EDT` every day) |
| MISO | F | F | F | F | F | F | F | `EST` |

P = prevailing, F = fixed standard time.

**Prevailing evidence** (the slot that was empty on the spring-forward day):

- TVA: HE03 zero in 2019–20, HE03 omitted in 2021, HE02 omitted in 2022–25.
- Duke Carolinas and Duke Progress: HE03 zero in 2019 and 2023–25, HE02 zero in 2020.
- Duke Florida: HE03 zero in 2019–20; omitted instant in every XBRL year.
- FPL 2022: HE03 zero.

**Where the codes disagree with the pattern, the pattern decides.** This is
the same rule Southern's CPT-coded years follow. A per-day EST/EDT code with
24 values on every day is impossible on a literal reading: a 24-hour
EST-coded spring day followed by an EDT-coded day overlaps one UTC hour.

**Residual uncertainties.** Each of these is a possible ±1 h on DST-season
hours. Winter hours, and Elliott, are unaffected.

- **Duke Carolinas and Duke Progress 2021–22** read fixed by the pattern. Their
  other five years are prevailing. Their spring-forward HE03 repeats an
  adjacent hour's value (DUK 2021 12.96 = HE02; CPLE 2022 73.14 = HE04), which
  may be a filled placeholder. Repeated adjacent values are common on
  ordinary nights, though, so this is not decisive.
- **FPL 2022** reads prevailing because HE03 is 0.00, its only zero in seven
  years. Every other FPL year reads fixed.
- **JEA** reads fixed in every year. However, it files an off-level value in
  **both** HE02 and HE03 on every spring-forward day (8.09 in 2019, 15.00 in
  2020–22, 10.00 in 2023–25, against 20–40 on either side). That is a
  DST-aware artifact the count test cannot resolve. JEA 2021's `EDT` code is
  read as EST, the same as its other six years.
- **Tallahassee 2021's `UTC` code is measured not literal.** Its Jun–Aug
  hour-of-day lambda profile matches its own `EST`-coded 2022 at lag 0
  (r 0.978). A literal UTC clock would need a 5-hour shift, and r there is
  ≤ 0.29.
- **The diurnal-profile cross-check is otherwise inconclusive.** Year-to-year
  summer-profile lags wander 0–2 h even for Southern's proven-fixed series,
  because solar growth moves the evening peak. Like Southern's demand
  correlation, it is not the basis for any verdict.

### Source and extraction

The source is the same six Zenodo record 21738524 archive files as the Southern
section, verified against the same sha256 table.

- **CSV era (2019–2020).** `ferc714.zip`, member `Part 2 Schedule 6 - Balancing
  Authority Hourly System Lambda.csv`, filtered on the FERC id. `spplmnt_num` is
  0 throughout, and there are no duplicate days.
- **XBRL era (2021–2025).** The instance document whose filename starts with
  the registered prefix (e.g. `Duke_Energy_Carolinas,_LLC_form714`) and whose
  entity CID matches. Every `SystemLambda` fact is read.
- **Hour-24 spellings.** Filers spell the day's 24th hour three ways, and all
  three are parsed as midnight ending the day:
  - `<next day>T00:00` (Southern);
  - `<day>T24:00` (JEA, TAL, MISO);
  - a date-only `<day>` (TVA, Duke, FPL, Santee Cooper). An XBRL date-only
    instant is the end of that day.

  The year must span local `Jan-01T01:00`..`next Jan-01T00:00`.

### Re-fetch

```bash
python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --set neighbors          # rebuild
python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --set neighbors --check  # prove it regenerates
```

`--check` returned `IDENTICAL` on 2026-10-01. On the same day, the Southern
`--check` (default `--set soco`) still returned `IDENTICAL` after the script
was extended. The prints include the per-respondent-year clock table above.
The CSV's sha256 is in `SHA256SUMS.txt`.
