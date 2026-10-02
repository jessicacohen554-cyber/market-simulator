# FINDING — NWPP-NEXT-22 phase 0 (zero LP): the seam headroom the market actually had

Probe: `scripts/probes/_nwppnext22_headroom_phase0.py` (sections A–E below). Inputs: measured data only, plus keeper
#20's committed `hourly/system_<Y>.parquet` and the NEXT-21 2023 / 2024 `flows.parquet` (read by full leg SHA
`3f52175627fcda2c1cf1c3b093ea96929413319c` / `8ffeaed04b7bdf5a1c79b794f6f9121574ab772c`).

**Owner card (2026-10-02): "CAISO share + BPA BC".** Each priced seam is capped at its measured hourly operating limit:

- CAISO_COI takes CAISO's share of Path 66. That is CAISO's own MALIN500_ISL + CASCADE_ITC OTC where OASIS has the
  hour, and 2/3 × BPA's whole-path limit before that.
- WECC_CAN takes BPA's BC Intertie operating limit.
- CAISO_NEVP is unchanged at 1,933 MW.

This is registered as the default-off key `nwpp_seam_measured_limits`.

## New measured source: BPA OPI intertie operating limits (intake this session)

The CAISO OASIS feed (`data/raw/caiso-trns-usage`) starts on 2023-06-19, so the handoff expected 2019–2022 to have only
a seasonal TTC.

BPA Transmission's "OPI Interties & Flowgates" archive covers that gap. It publishes monthly files from 1996 to now,
with 15-minute rows of actual loading and the N-S / S-N operating limits (the SOL BPA monitors, for all owners) for
the AC Intertie (COI) and the BC Intertie (Path 3). The 2019–2025 files are folded into
`data/raw/nwpp-intertie-otc/` (fetcher `scripts/data/fetch_bpa_intertie_otc.py`, README there). They are curated as the
`NWPP` partition of `transfer-interface-limits` on NWPP's fixed-PST clock.

**So no year is left on a seasonal TTC, and the owner card the handoff anticipated ("headroom only in measured years
vs seasonal TTC elsewhere") is moot.**

## §A. CAISO's share of COI

CAISO's hourly OTC (MALIN500_ISL + CASCADE_ITC) divided by BPA's whole-path COI operating limit, per direction:

| year | export (N-S): median / p10 / p90 | import (S-N): median / p10 / p90 | hours |
|---|---|---|---:|
| 2023 (from 06-19) | 0.684 / 0.667 / 0.691 | 0.670 / 0.667 / 0.714 | 4,705 |
| 2024 | 0.667 / 0.667 / 0.690 | 0.667 / 0.667 / 0.692 | 8,747 |
| 2025 | 0.667 / 0.667 / 0.691 | 0.667 / 0.667 / 0.691 | 8,760 |

The ratio is an ownership allocation:

- PG&E's two Malin–Round Mountain 500 kV lines (3,200 MW) are what CAISO schedules as MALIN500_ISL.
- TANC's COTP carries the other 1,600 MW of Path 66's 4,800 MW. COTP flows go to BANC/TIDC, which are counterparties
  in the measured residual NWPP already serves (rule 19), so their share of the path is not available to the priced
  CAISO trade.

`constants.NWPP_COI_CAISO_SHARE = 2/3` is cited to that ownership split, and this table is the measured check. It is
never fitted to a flow.

## §B. Which CAISO ITC carries each priced CAISO leg

The table gives the hourly r of each ITC's DAM schedule against the measured EIA-930 leg. The schedule is used as a
diagnostic only.

| year | measured leg (mean MW) | top ITCs (r) |
|---|---|---|
| 2024 | CISO←BPAT+PACW (244) | MALIN500_ISL 0.80, COTPISO 0.61, IPPDCADLN 0.58, ADLANTO-SP 0.54 |
| 2025 | CISO←BPAT+PACW (346) | MALIN500_ISL 0.80, NOB 0.66, COTPISO 0.54, TRACY500 0.52 |
| 2024 | CISO←NEVP (1,037) | PALOVRDE 0.47, ADLANTOVICTVL-SP 0.41, MEAD 0.37 |
| 2025 | CISO←NEVP (1,073) | ADLANTOVICTVL-SP 0.55, PALOVRDE 0.51, ADLANTO-SP 0.49 |

- COI maps to MALIN500_ISL.
- NEVP's metered leg maps to no CAISO scheduling point. It reads as Southwest flow through NEVP's system, not a
  scheduled NEVP↔CAISO trade.
- No published limit sits on NEVP's boundary, so CAISO_NEVP keeps its registered 1,933 MW. That is the NWPP-11
  measured hourly maximum, which this lane does not re-derive (rule 23).
- NOB (PDCI) is not in CAISO_COI: it lands at Sylmar, on LDWP's system.

## §C. Crosswalk: BPA path loading against the measured seam legs (mean MW, export +)

| year | COI path / CISO leg | BC path / BPAT–BCHA leg |
|---|---|---|
| 2019 | 1,536 / 803 | 448 / 445 |
| 2020 | 2,663 / 1,742 | −564 / −566 |
| 2021 | 2,186 / 1,382 | −448 / −448 |
| 2022 | 2,248 / 1,427 | −414 / −417 |
| 2023 | 255 / 129 | 1,087 / 1,082 |
| 2024 | 485 / 245 | 862 / 857 |
| 2025 | 662 / 346 | 320 / 316 |

- The BC Intertie is the BC leg: they agree within 5 MW in every year. Its operating limit is therefore the right cap.
- COI carries about 1.6–2× the CISO leg. The difference is COTP and other non-CAISO use of the path, which supports
  §A's share.

## §D. Price-taker re-run (NEXT-20 §D construction) against keeper #20's price

All values are TWh, export positive.

| seam / year | registered | measured caps | actual |
|---|---:|---:|---:|
| COI 2019 | 26.51 | 14.90 | 7.03 |
| COI 2020 | 28.04 | 16.87 | 15.26 |
| COI 2021 | 25.03 | 15.45 | 12.11 |
| COI 2022 | 25.69 | 17.33 | 12.50 |
| COI 2023 | 12.32 | 8.68 | 1.13 |
| COI 2024 | 21.25 | 12.99 | 2.15 |
| COI 2025 | 11.16 | 7.72 | 3.03 |
| BC 2023 | 21.39 | 16.12 | 9.48 |
| BC 2024 | 16.72 | 14.35 | 7.51 |
| BC 2025 | 3.66 | 3.61 | 2.77 |
| NEVP (unchanged) | 11.16 / 11.06 / 11.01 / 8.26 / 4.37 / 9.22 / 5.23 | same | −0.30 / 3.11 / 8.60 / 8.56 / 7.56 / 9.08 / 9.40 |
| **sum, 2019–2025** | 37.7 / 39.1 / 36.0 / 34.0 / 38.1 / 47.2 / 20.0 | **26.1 / 27.9 / 26.5 / 25.6 / 29.2 / 36.6 / 16.6** | 6.7 / 18.4 / 20.7 / 21.1 / 18.2 / 18.7 / 15.2 |

**Reading.** The measured limits move the price-taker seams down in every year.

- 2020, 2021, 2022 and 2025 come within 1.1–1.4× of actual.
- **2019, 2023 and 2024 stay 1.6–3.9× actual.** COI alone is still 2.1×, 7.7× and 6.0× actual in those years.

That residual is not headroom. It is the price level: keeper #20's NW price sits below CAISO's MALIN anchor (NEXT-20
§D). The card asked "if they do not fall, the overshoot is a price-level problem — card it". The answer is that they
fall partly. The price-level remainder is routed below.

## §E. NEXT-21's realized flows clipped at the measured caps (prices held)

| year | seam | NEXT-21 arm TWh | clipped TWh | hours export > cap | hours import > cap |
|---|---|---:|---:|---:|---:|
| 2023 | COI | 4.69 | 4.58 | 2,569 | 2,159 |
| 2023 | BC | 22.48 | 18.07 | 5,952 | 0 |
| 2024 | COI | 17.38 | 11.29 | 4,049 | 791 |
| 2024 | BC | 10.97 | 10.06 | 1,515 | 18 |

The arm exceeded the measured limit in 2,500–6,000 hours per seam-year.

## Rule tests

- **Rule 13.** An operating transfer limit is a physical operating condition, the same kind of input as an outage
  window. It regenerates for any year from the same feed, responds to outages and re-ratings, and its forward analogue
  is the seasonal path rating. Nothing reads a flow, a schedule or a model output. The `transfer_mw` columns and the
  DAM schedules appear only in §B / §C as crosswalk diagnostics.
- **Rule 14.** The measured operating limit replaces the nameplate path rating.
- **Rule 19.** The cap is one aggregate row per seam on the seam's net flow. It is the only bound added. The bands
  still sum to the registered rating, and the cap binds only where it is tighter.
- **Rule 5.** Every number is a cited constant or a measured series (`constants.NWPP_SEAM_LIMIT_SERIES`,
  `NWPP_COI_PATH_SERIES`, `NWPP_COI_CAISO_SHARE`).

## Routed / open

- **Price level (next lever).** After headroom, COI 2019/2023/2024 still over-exports at price-taker. Trace why
  keeper #20's NW price sits below the MALIN anchor before touching the seam again:
  - the CAISO anchor construction (annual mean MALIN ÷ HH + basis);
  - the 3.0 hurdle;
  - the NW hydro and gas offer level.
- **Card N4 / R-a (CAISO lane).** CAISO's WECC_import→NP15 link also carries Path 66's full 4,800 MW. §A and §C show
  that CAISO's market sees about 2/3 of it, the CAISO-owned lines. Still unruled at NEXT-22.
- **Hydration.** The NWPP solve now reads the CAISO partition of `transfer-interface-limits`.
  `scripts/lib/clean_profiles.py` gains `also_reads={"NWPP": ("CAISO",)}` so `regenerate_clean.py --solve-profile NWPP`
  builds both. A partial clone hydrating only `--profile nwpp` lacks `data/raw/caiso-trns-usage` (it carries the CAISO
  token). Shards are full clones today; a blobless NWPP lane must also hydrate that one directory.
