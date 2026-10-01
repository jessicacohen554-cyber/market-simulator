# FINDING R-CAISO-30: OASIS TRNS_USAGE intertie OTC intake (link 12)

2026-10-01. **DATA INTAKE ONLY: zero LP, nothing armed, keeper unchanged** (`2026-09-30-caiso-r20-overnight`).

## 1. What landed

| piece | path |
|---|---|
| fetcher (Pacific-day windows, lossless wide fold) | `scripts/data/fetch_caiso_trns_usage.py` |
| raw, **committed** (OASIS retention rolls) | `data/raw/caiso-trns-usage/caiso_trns_usage_dam_{2023,2024,2025}.parquet` + README + SHA256SUMS (5.0 MB) |
| clean datatype | `transfer-interface-limits`, new CAISO spec `scripts/lib/transfer_interface_limits/caiso.py` |
| shared-code change | `IsoSpec.max_fill_hours`: `None` keeps PJM's dense fill unchanged; CAISO = 1, so hours with no data are absent rather than filled in |
| test | `tests/curation/test_curate_transfer_interface_limits.py::CurateCaisoTrnsUsageTest` |
| probe | `scripts/probes/_rcaiso30_otc_vs_envelope.py` |

- **Series:** four per ITC and direction, named `<ti_id>|<I|E>|<OTC|TTC|TRM|MTC>`. Counts: 408 (2023), 448 (2024), 464 (2025).
- **`transfer_mw` = DAM scheduled net import** (`ENE_IMPORT_MW`). This is a diagnostic only, not a metered flow.
- **Coverage:** every UTC hour is present from 2023-06-19 to 2025-12-31, with no NaN.
- **ITC set changes over time:** 51 ITCs (2023), 56 (2024), 58 (2025). New ITCs include SUNZIA and PINALCENT500 (from 2025-09-19) and RDMTEA (from 2025-05).
- **Only consumer:** the PJM reader, which reads only `iso="PJM"`. The CAISO partition is therefore inert.

## 2. Retention: what was lost

- **Earliest trade date served (measured 2026-10-01): 2023-06-19.** 06-17 and 06-18 return ERR 1000.
- **Gone from OASIS:**
  - 2022, the keeper's first training year
  - the 2019–21 fold years
  - 2023-01-01 to 2023-06-18
- **Committed here:** 2023-06-19 to 2025-12-31. This is now the only copy as those months roll off OASIS.

## 3. What the data says (zero LP, descriptive)

**DAM TRM is 0 on every major ITC in every year.** So in the DAM, OTC minus TRM is just OTC.

**Import-direction derates, OTC vs seasonal TTC:**

| ITC | year | TTC median (MW) | OTC median (MW) | % hours derated | mean derate (MW) |
|---|---|--:|--:|--:|--:|
| MALIN500_ISL (COI) | 2023* | 2,989 | 2,967 | 74 | 270 |
| MALIN500_ISL (COI) | 2024 | 3,200 | 3,003 | 69 | 398 |
| MALIN500_ISL (COI) | 2025 | 3,400 | 2,750 | 86 | 634 |
| PALOVRDE_ITC | 2023–25 | 3,628 | 3,628 | 1–3 | 30–58 |
| ADLANTOVICTVL-SP_ITC | 2024 / 2025 | 6,619 | 6,741 | 35 / 24 | 125 / 164 |
| SYLMAR-AC_ITC | 2024 / 2025 | 2,600 | 2,600 | 35 / 22 | 166 / 191 |

\*2023 covers 2023-06-19 to 2023-12-31 only.

**PNW import OTC vs the armed corridor envelope.** The envelope is the p95 of EIA-930 net imports by month × hour of day (`caiso_corridor_flow_limit`). The ITC set is **provisional and not identified**: MALIN500_ISL + NOB_ITC + CASCADE_ITC. ITCs are tie points, while the envelope is built from BA-to-BA net interchange.

| year | OTC sum mean (MW) | OTC p05 (MW) | envelope mean (MW) | envelope max (MW) | % hours envelope > OTC | DAM schedule > envelope |
|---|--:|--:|--:|--:|--:|--:|
| 2023* | 4,123 | 2,293 | 1,290 | 3,128 | 0.4 % | 41 % |
| 2024 | 4,188 | 2,300 | 1,589 | 2,951 | 3.7 % | 36 % |
| 2025 | 4,154 | 2,750 | 1,714 | 3,238 | 0.3 % | 35 % |

What this table supports:

- The armed envelope is **not a transfer-capability limit**. It sits about 2.5 GW under the published OTC on average.
- It measures how much the neighbours net-deliver, not how much the wires can carry. That is consistent with how its docstring describes it (an "ATC proxy").
- A rule-14 OTC cap would be **far looser** than the envelope and would almost never bind. Expect no change in fit, consistent with caiso-280 ("envelope binds above actuals").
- Under rule 14, OTC is the accurate measure of *capability*. It does not replace the envelope, which caps something different: neighbour net supply, not wire capacity.
- Using OTC on the PNW corridor would need an **identified ITC → corridor crosswalk**. That would be its own scoping lane.

The DAM-schedule column is diagnostic only. Gross ITC schedules and BA net interchange are not like-for-like, so "schedule > envelope 35–41 %" is **not** evidence that the envelope is wrong.

## 4. Not done (stated)

- `TRNS_OUTAGE` was not intaken. It is offered on the decision card.
- No DSW comparison was made, because the DSW ITC set (Palo Verde, North Gila, Eldorado, Mead, McCullough, SunZia, …) has no identified crosswalk.
- The matrix cell `measured_interface_limits` is unchanged at K; a NOTE was prepended.

## 5. Owner ruling (decision card, 2026-10-01)

**"None, report-only."** TRNS_USAGE stays a measured record with no consumer. The owner queued neither follow-up:

- no ITC→corridor crosswalk scoping
- no TRNS_OUTAGE intake

Do not re-ask either. Links 13–15 proceed as planned.
