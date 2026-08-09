# miso-energy-offers — raw (contents gitignored)

`<market>/<YYYYMMDD>_<market>_co.zip` — MISO Market Reports **masked submitted
energy-offer corpus**, one zip per operating day per market:

```
https://docs.misoenergy.org/marketreports/YYYYMMDD_da_co.zip   (Day-Ahead)
https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_co.zip   (Real-Time)
```

Each zip holds a single CSV: **one row per masked `Unit Code` × operating
hour**, carrying the full ten-segment cumulative-MW/price offer curve
(`MW1`/`Price1` … `MW10`/`Price10`), economic and emergency limits, the
economic / emergency / must-run / unit-available declarations, self-scheduled
MW, the curtailment offer price, the slope flag, and (for storage) energy-level
bounds. Published on a **~90-day lag** — the Order-719-family conduct
transparency publication.

**Identity is masked and there is NO fuel or technology attribute.** The masked
`Unit Code` *is* persistent across days and years (92–99 % overlap across
2023↔2024↔2025, measured at miso-136), so per-unit longitudinal statistics are
meaningful — but the offer-side **class** bridge (coal vs CC vs CT) was built
and **REFUTED** at miso-138, so no class crosswalk may be asserted from this
corpus. Locational information is limited to `Region` ∈ {North, Central,
South}, which is a MISO market region and **not** a model zone.

**Timezone:** the reports are published on fixed **EST (UTC−5)** year-round —
24 rows per unit-day across both DST transitions, no localisation applied.

**Rule 13 `[R-MEASURED]`.** The offer columns are participant declarations
recorded ex ante and are admissible measured inputs. The files also carry
dispatch **awards** — RT `Cleared MW1`–`Cleared MW12`, DA `MW`, and
`Target MW Reduction` — which are OUTCOMES (the answer class). They are dropped
at curation, have no column in the `energy-offers` schema, and can never be
read downstream (`scripts/data/curate_miso_energy_offers.py::OUTCOME_COLS`).

**This directory's contents are gitignored** (see `.gitignore`; the
`pjm-energy-offers` / `caiso-public-bids` precedent) — the JJA 2023–2025 corpus
is 552 daily zips ≈ 430 MB. Only this README is tracked; `manifest.json`
records each landed file's sha256, byte size and fetch status and is regenerated
by the fetcher.

**Landed span (miso-145, 2026-08-09):** June 1 – August 31 of **2023, 2024 and
2025**, both markets — 276 days × 2 = **552 files, 429.6 MB, 552/552 fetched
OK**. Rule 22 `[R-HOLDOUT]`: MISO holds no `calibration-complete` marker, so the
fetcher refuses any year outside 2023–2025 without `--allow-out-of-train`.

**Regeneration:**

```bash
python scripts/data/fetch_miso_energy_offers.py                    # JJA 2023-2025, both markets
python scripts/data/fetch_miso_energy_offers.py --markets rt
python scripts/data/fetch_miso_energy_offers.py --years 2025 --months 6 7 8
python scripts/data/curate_miso_energy_offers.py                   # -> data/clean/energy-offers/MISO/<MARKET>/
```
