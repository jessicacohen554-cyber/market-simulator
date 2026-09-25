# `ferc-714`: FERC Form 714 hourly planning-area demand

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
| `SHA256SUMS.txt` | — | Identity record for the CSV. |

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
