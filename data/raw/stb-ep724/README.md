# STB EP 724 rail service data (consolidated workbook)

**Source.** Surface Transportation Board, Docket EP 724 (Sub-No. 4), "United States Rail Service Issues -
Performance Data Reporting". Every Class I railroad files weekly service metrics. The STB consolidates all
carriers and weeks (2017-03-29 onward) into one workbook on
<https://www.stb.gov/reports-data/rail-service-data/>:

- `EP724_Consolidated_Data_through_2026-09-30.xlsx`, fetched 2026-10-02 (SPP-108) from
  `https://www.stb.gov/wp-content/uploads/files/rsir/All%20Class%201%20Railroads/EP724%20Consolidated%20Data%20through%202026-09-30.xlsx`.
  Its SHA-256 is in `SHA256SUMS.txt`.

Public domain (US Government work), keyless.

**Layout.** One sheet, `Sheet1`. Row 0 is the header: `Railroad/Region`, `Category No.`, `Sub-Category`,
`Measure`, `Variable`, `Sub-Variable`, then one column per reporting week, dated by the filing Wednesday.
Each following row is one carrier x metric x variable x sub-variable series.

**Curated subset.** Category 9, "Coal Unit Train Loadings or Carloadings by Coal Production Region
(Count)". `Variable` is the production region and `Sub-Variable` is `Loadings Plan` or `Loadings Average`.
This becomes the `stb-coal-loadings` clean datatype (`scripts/data/curate_stb_coal_loadings.py`). The other
categories (train speed, dwell, cars online, carloads by commodity) stay raw-only.

**Refresh.** Download the newer consolidated workbook from the page above and add it next to this one,
updating `SHA256SUMS.txt`. The curator reads the newest `EP724_Consolidated_Data_through_*.xlsx`.

DATA NEEDED: none.
