# NYISO uncurtailed-potential basis — re-examination finding (2026-07-21)

Branch: `claude/forecast-nyiso-uncurtailed-hsl`. Scope: re-examine, on its own,
whether NYISO wind/solar should move off the EIA-930 *delivered* CF (which
embeds historical curtailment) onto an *uncurtailed-potential* basis — an hourly
HSL parquet or the forecast-uncurtailed reference-rate gross-up. This follows
the multi-ISO pass in `forecast-uncurtailed-hsl-finding-2026-07.md`, which wired
MISO wind and deferred NYISO with a one-line "immaterial + too coarse for even a
reliable rate" note. That note was imprecise; this session sharpens the basis.

**Outcome: deferral re-confirmed.** NYISO stays OUT of
`_UNCURTAILED_FALLBACK_ISOS` on the EIA-930 NYIS delivered default — but for a
sharper, cited basis than "no hourly series." Rule 22 respected: **no holdout
year was solved or scored**; this is a comment + docs change only (behaviour is
byte-identical — verified: NYISO wind/solar provenance stays `delivered_pinned`,
`_reference_curtailment_rate("NYISO", ·)` stays `None`, the fallback set is
unchanged `{ERCOT, CAISO, MISO}`).

## Step 0 — what is on disk

| Source | Granularity | Hourly? |
|---|---|---|
| `data/raw/nyiso-renewable-curtailment/nyiso_curtailment_annual.csv` | annual NYCA % + zonal GWh | no |
| `data/raw/nyiso-renewable-curtailment/nyiso_curtailment_monthly.csv` | monthly NYCA % + zonal GWh | no |
| `data/raw/nyiso-hsl/` | **does not exist** (stub marker only) | — |

An hourly per-plant/zonal HSL parquet **cannot** be built — no hourly source
exists. That settles the *HSL-parquet* question (same as MISO). But it does NOT
by itself settle the *reference-rate gross-up*, because that path needs only an
annual RATE × the EIA-930 hourly delivered shape — exactly how MISO wind was
wired. So the granularity argument alone is not the discriminator.

## Step 1 — research: does NYISO publish anything hourly-resolvable?

No. Confirmed against the committed primary-source record
(`data/raw/nyiso-renewable-curtailment/README.md`, an exhaustive prior search of
the NYISO "NYCA Renewables" deck series) and refreshed by web search
(2026-07-21):

- NYISO's curtailment reporting lives entirely in the annual **"NYCA
  Renewables"** presentation to ICAPWG/MIWG (nyiso.com/reports-information):
  annual + monthly + zonal **aggregates** only. No hourly curtailment or
  uncurtailed-potential product.
- NYISO's hourly public products (Real-Time Dashboard, energy-market operational
  data, OASIS fuel-mix) report **delivered** generation — which we already
  ingest via EIA-930 NYIS. None is an uncurtailed/HSL series.
- The Potomac Economics NYISO State-of-the-Market reports carry curtailment as
  annual/aggregate figures, not an hourly series (same posture as the MISO IMM
  reports).
- Web coverage corroborates that NYISO curtailment is transmission-constraint
  driven and "not yet an issue" — i.e. immaterial in magnitude.

Sources:
- <https://www.nyiso.com/energy-market-operational-data>
- <https://www.nyiso.com/real-time-dashboard>
- <https://www.potomaceconomics.com/wp-content/uploads/2026/05/NYISO-2025-SOM-Report__5-19-2026-final.pdf>
- <https://pragmaticenvironmentalistofnewyork.blog/2026/04/11/nyiso-2025-renewables-summary/>
- committed primary-source transcription: `data/raw/nyiso-renewable-curtailment/README.md`

## Step 2 vs 3 — is a reference-rate gross-up defensible for NYISO?

**No — deferral is the correct call**, on two grounds sharper than granularity:

1. **Immaterial magnitude.** NYCA wind curtailment (firm printed %): 3.4% (2023),
   1.1% (2024), 1.1% (2025) — mean ~1.9% over the training window, well under
   1 TWh/yr. FTM solar: 0.2% (2024), 2.1% (2025), volatile, no zonal detail.
   This is below the threshold where explicit re-curtailment moves dispatch.
   MISO qualifies for the gross-up at ~4.9% / multi-TWh; NYISO does not.

2. **Driver misaligned to the reduced network (CLAUDE.md #12 exception).** NYISO
   wind curtailment is dominated by **North/Central Zone local
   transmission-upgrade outages** — North+Central is 72–93% of zonal curtailment
   every reported year (2020 North alone = 85%), and the 2021 deck annotates
   North curtailment as "coincident with several long-term facility outages
   related to transmission upgrades." That is a sub-zonal physical event the
   reduced 5-zone NYISO network does not represent. Grossing the delivered NYIS
   shape up by a uniform ~1% (`delivered / (1 − rate)`) and handing it to the LP
   would inject wind the model **cannot endogenously re-curtail** — phantom
   energy that makes results *less* reflective of reality. The forecast-
   uncurtailed construction assumes the LP re-curtails the headroom under
   *modeled* limits; here it can't, so the gross-up degrades rather than
   improves fidelity.

   | year | zonal total (GWh) | North % | North+Central % |
   |---|---|---|---|
   | 2020 | 61.6 | 85 | 87 |
   | 2021 | 83.0 | 68 | 72 |
   | 2022 | 161.4 | 49 | 75 |
   | 2023 | 160.7 | 42 | 91 |
   | 2025 | 74.4 | 29 | 93 |

The NYCA-wide annual rate is a real, forward-reproducible number, but it is the
**wrong instrument** for a locally-driven, immaterial curtailment. Using it
literally is precisely the CLAUDE.md #12 "accurate data misaligned to our
representation" case, where the measured delivered series is preferred and the
misalignment is documented — not a residual dodge.

FTM solar is a clearer deferral still: immaterial and volatile, with no
zonal/monthly breakdown published at all.

## Correction to the prior note

The multi-ISO finding said NYISO was "too coarse for even a reliable rate." That
is inaccurate — a NYCA-wide annual wind rate is directly published (more directly
than MISO's, which is derived from `curtailed / (delivered + curtailed)`). The
real reasons are **materiality** and **driver-network misalignment**, now stated
in `renewables.py` (module docstring, `_NYISO_HSL_DIR`, `_hsl_file` NYISO branch,
`renewable_bound_provenance`).

## DATA NEEDED to move NYISO onto an uncurtailed path

An **hourly** wind/solar curtailment or HSL series at NP6 / CAISO-workbook
granularity (per-plant or per-zone, so the local North/Central driver can be
placed on the network). Absent that, delivered EIA-930 NYIS remains the
documented, honest default. Do not fabricate an hourly proxy from the aggregate.

## Files touched

- `src/market_sim/data/renewables.py` — comment-only (module docstring +
  `_NYISO_HSL_DIR` + `_hsl_file` NYISO branch + `renewable_bound_provenance`);
  no behaviour change.
- `data/raw/nyiso-renewable-curtailment/README.md` — Consumer/DATA-NEEDED note
  updated to record the re-examination outcome.
- `docs/multi-iso/nyiso-uncurtailed-hsl-finding-2026-07.md` — this doc.
