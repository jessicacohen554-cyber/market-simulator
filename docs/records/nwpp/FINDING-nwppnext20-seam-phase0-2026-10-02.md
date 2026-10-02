# FINDING — NWPP-NEXT-20 phase 0 (ZERO LP): the priced interface re-registered — CAISO net-load, BC on its own price, WECC_SW served, one zone per seam

Lane NWPP-NEXT-20 · 2026-10-02 · branch `claude/nwppnext20` · base main `d1aa1dce` · keeper #20
`2026-10-01-nwppnext16c-combined-vintage` (unchanged; it does not arm the interface). **No LP was run; no shard was
launched** (owner, in session: "Give me a handoff prompt when done don't launch a shard"). The 7-shard solve is
NWPP-NEXT-21's.

Probe: `scripts/probes/_nwppnext20_seam_phase0.py <leg root>` (keeper #20 legs by full SHA, as NEXT-19). §A–§B read
measured data only; §C–§D read the registry. The "at d1aa1dce" tables below are that probe's output against NEXT-19's
registry before this branch changed it; the "this commit" tables are its output now.

## Owner cards (2026-10-02, in order)

| card | ruling |
|---|---|
| WECC_CAN anchor | **BCHA ELAP** — BC Hydro/Powerex's own WEIM price replaces the peak-only Mid-C Peak proxy |
| WECC_SW (fails the gate) | **Schedule as residual** — served = measured pool net − the priced seams' measured legs |
| One-bus wheel | **Per-seam external zones** |
| Scope | Code, then 7 shards → superseded by "don't launch a shard; hand off" |
| Canada 2019–2022 (new evidence, §D) | **Price only anchored years** — BC leg served measured in 2019–2022 |

## §A. SPP-51 P0-b, copied as a method (rule 28(d)): does the measured flow follow the measured spread?

Spread = counterparty price − the reporting BA's WEIM ELAP; hurdle = the seam's registered hurdle (CAISO 3, others 2);
sign vs the measured EIA-930 per-DIBA leg (export-positive). Gate ≥ 0.55 over non-hold hours. 2023 = Jun–Dec (WEIM
retention).

| leg (counterparty price) | sign agree, non-hold 2023 / 24 / 25 | always-export baseline | corr(spread, flow) | verdict |
|---|---|---|---|---|
| BPAT→CISO (MALIN) | 0.757 / 0.735 / 0.793 | 0.68 / 0.69 / 0.71 | +0.33…+0.46 | **pass** |
| NEVP→CISO (CAISO RT) | 0.756 / 0.722 / 0.788 | 0.76 / 0.73 / 0.79 | +0.15…+0.25 | pass, **≈ baseline** (one-way export 98–99.7 % of hours) |
| PACW→CISO (MALIN) | 0.496 / 0.641 / 0.742 | — | +0.13…+0.36 | small leg (≤ 0.03 TWh) |
| BPAT→BCHA (BCHA ELAP) | 0.885 / 0.819 / 0.751 | 0.95 / 0.78 / 0.60 | +0.13…+0.31 | pass (2023 below baseline) |
| **NEVP→LDWP** (PALOVRDE) | **0.282 / 0.332 / 0.308** | — | **−0.18…−0.28** | **FAIL** (largest WECC_SW leg, −7.5…−9.3 TWh) |
| **PACE→WACM** (PALOVRDE) | **0.270 / 0.332 / 0.399** | — | +0.01…+0.06 | **FAIL** |
| BPAT→LDWP / PDCI (PALOVRDE) | 0.761 / 0.757 / 0.798 | — | +0.37…+0.58 | pass |

WECC_SW's two largest legs move against or independently of the spread — SPP-51's MISO finding (a scheduled,
spread-blind seam). It is deleted as a priced block and served measured.

## §B. WECC_CAN anchor: `ELAP_BCHA-APND`

Fetched by the committed producer (`build_nwpp_weim_price_index.py fetch-counterparty` →
`data/raw/nwpp-weim/weim_hourly_counterparty.parquet`).

| | 2023 (4,633 h, Jun 22–Dec) | 2024 | 2025 |
|---|---|---|---|
| BCHA mean $/MWh | 88.47 | 41.21 | 34.99 |
| BPAT same hours | 51.04 | 44.95 | 34.43 |
| r(BCHA, BPAT) hourly | 0.33 | 0.52 | 0.62 |
| HR = mean / (HH + NWPP basis) | **37.64** | **20.60** | **10.51** |
| Mid-C Peak HR (NEXT-19 registry) | 37.11 | 30.73 | 13.90 |

Structural (forward) HR = mean 22.92. **Caveat stated, not corrected:** 2023's anchor is a Jun 22–Dec mean applied to
the whole year (OASIS retention). Those months include the drought-driven BC import period (measured BPAT→BCHA
+9.5 TWh in 2023), so the high level is consistent with the measured flow, but Jan–Jun 22 is unobserved.

## §C. Wheel exposure

At d1aa1dce every NWPP seam sat in one pooled bus `NWPP_external`; hours in which two seams' prices differ by more
than their two hurdles (a free trade through the bus, touching no NWPP zone):

| pair | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CAISO\|WECC_CAN | 8398 | 7427 | 8759 | 8760 | 8756 | 8333 | 5967 |
| CAISO\|WECC_SW | 4655 | 6444 | 4887 | 4670 | 4713 | 6837 | 6288 |
| WECC_SW\|WECC_CAN | 8615 | 8419 | 8652 | 8739 | 8715 | 8735 | 7530 |

The pooled bus also linked NW, OR and SNV directly, a bypass of the 500–600 MW internal SNV links.
**Fix:** one zone per seam (`IMPORT_SEAM_ZONES`), each linked only to its own border zone(s) at its own registered limit.
CAISO is split at the two summands of NWPP-20's 6,733 MW: COI 4,800 (NW, OR — joined internally by 43,600 MW) and
NEVP 1,933 (SNV). WECC_CAN = Path 3, 3,150 MW into NW. AESO (Path 83, 325 MW) has no tested price and stays served.

**What remains, stated:** CAISO_COI and WECC_CAN both land in NWPP-NW, so the LP can import from one and export to the
other through NW: the physical BC↔CA wheel through BPAT, bounded by the real path ratings and the hurdles. It is now
priced against NW's own balance only through the links, and its size depends on two synthetic reference prices
(this commit, 2023–25 only since BC is unpriced before 2023): |P_COI − P_CAN| > 5 in 8,276 / 6,740 / 7,349 h, BC
dearer in 8,187 / 3,367 / 2,831. **NEXT-21 must report simultaneous COI-import + BC-export hours** in the solve.

## §D. Price-taker seam flows against keeper #20's price (this commit's registry, before anchored-year gating)

| TWh, export + | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CAISO_COI price-taker / measured | 26.5 / 7.0 | 28.0 / 15.3 | 25.0 / 12.1 | 25.7 / 12.5 | 12.3 / 1.1 | 21.3 / 2.2 | 11.2 / 3.0 |
| CAISO_NEVP | 11.2 / −0.3 | 11.1 / 3.1 | 11.0 / 8.6 | 8.3 / 8.6 | 4.4 / 7.6 | 9.2 / 9.1 | 5.2 / 9.4 |
| WECC_CAN | 24.5 / 3.9 | 21.5 / **−5.0** | 24.6 / **−3.9** | 26.4 / **−3.7** | 21.4 / 9.5 | 16.7 / 7.5 | 3.7 / 2.8 |
| hourly r, COI | 0.65 | 0.53 | 0.47 | 0.62 | 0.30 | 0.51 | 0.50 |

- The net-load CAISO shape raises the hourly r of the price-taker flow against the measured CAISO flow in every year
  (at d1aa1dce, gross: 0.38 / −0.11 / 0.03 / 0.40 / −0.07 / 0.14 / −0.22).
- **WECC_CAN 2019–2022 on the flat 22.92 × gas fallback ($54 / 42 / 85 / 143) exports at the limit 3,300–7,300 h/yr where
  the measured BC leg is a net import in 2020–2022.** Owner card: price BC only in anchored years
  (`anchored_years_only`); in 2019–2022 the BC leg stays in the served residual.
- **Level gap, the main risk for the solve:** keeper #20's NW price sits $2–35/MWh below every seam (it is UNSCORED).
  At price-taker the priced seams export 20–62 TWh/yr against 10–19 TWh measured. The LP will close that by raising
  NWPP's price and its thermal output, by an amount only a solve shows. Watch C1/C2 gas and coal, CT_PEAKER (NEXT-19
  §3: 2–2.7× at a West-shaped price), rule 20 forced energy.

## §E. The served residual (rule 19)

`eia930.envelopes.nwpp_unpriced_residual_interchange` = keeper #20's served schedule (`nwpp_net_interchange`, same
flags) − the priced seams' measured legs (`NWPP_PRICED_SEAM_LEGS`: CAISO legs from CAISO's own book, NWPP-34 showed
BPAT mirrors it to ≤ 0.06 TWh; BC leg from BPAT's). Keeper flags (grid-carried wind + plant basis), TWh export-positive:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| pool (keeper schedule) | 4.76 | 22.64 | 10.33 | 11.78 | −3.95 | −0.32 | 9.05 |
| − COI (CISO book) | 7.03 | 15.26 | 12.11 | 12.50 | 1.13 | 2.15 | 3.03 |
| − NEVP (CISO book) | −0.31 | 3.11 | 8.60 | 8.56 | 7.56 | 9.08 | 9.40 |
| − BC (BPAT book; priced 2023–25 only) | — | — | — | — | 9.48 | 7.51 | 2.77 |
| **served residual** | **−1.96** | **4.27** | **−10.39** | **−9.28** | **−22.12** | **−19.06** | **−6.15** |

(2019–2022 rows: residual with the BC leg left in, since BC is unpriced there. Hour coverage of the CISO legs
0.978–1.000; uncovered hours keep their energy in the schedule.) The 2023–24 residual is a large net import
(Desert-SW / LDWP / WACM legs plus BPAT's reporting non-closure, NWPP-11 §4.3), served as measured.

## §F. Code (default-off; keeper path byte-identical)

- `model/interchange/spec.py`: NWPP seams = `CAISO_COI`, `CAISO_NEVP` (net load), `WECC_CAN` (BCHA anchor,
  `anchored_years_only`); `WECC_SW` deleted (rule 26); `IMPORT_SEAM_ZONES`, `seam_zone_links`, `seam_priced_in_year`,
  `NWPP_PRICED_SEAM_LEGS`; `seam_derived_border_links` and `IMPORT_NODE_LINKS["NWPP"]` deleted (replaced).
- `model/interchange/import_nodes.py`: `extend_with_import_node` builds per-seam zones; `build_reference_price_node`
  hosts each seam in its zone and skips a seam not priced in the solve year.
- `data/eia930/envelopes.py`: `_diba_legs_export`, `nwpp_unpriced_residual_interchange`; `data/eia930/demand.py`:
  NWPP with priced seams serves the residual (fails closed when it has none), never zero.
- Data: `data/raw/nwpp-weim/weim_hourly_counterparty.parquet` (new); BPAT per-DIBA back-filled 2019–2022
  (`fetch_eia930_interchange.py --ba BPAT --source bulk --years 2019 2020 2021 2022 --merge`; every committed row kept).
- G-DRIFT for these hunks against keeper #20: **INERT** — every new branch runs only under
  `reference_price_interface` / `priced_interchange` for NWPP, which no keeper arms; the BPAT file change adds rows
  only, and the keeper path reads BPAT's per-DIBA file nowhere. Other ISOs: `anchored_years_only` defaults False,
  `IMPORT_SEAM_ZONES` carries NWPP only (1,141 interchange/demand/seam tests green).

## Routed / open

- **Card N4 / R-a (CAISO double-count):** unruled by the CAISO lane. Path 66's 4,800 MW appears on both sides. This
  matters for a joint solve, not NWPP's single-ISO solve, where CAISO is an exogenous price. Still routed.
- NEVP→CISO passes the gate but sits at its always-export baseline: the spread barely informs it. Read the solve's
  NEVP flow against measured before crediting it.
