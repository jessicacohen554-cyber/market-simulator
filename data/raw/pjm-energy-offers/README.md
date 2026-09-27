# pjm-energy-offers — raw (gitignored)

`pjm_energy_offers_<year>_<month>.parquet` — PJM DataMiner2 `energy_market_offers`
feed: one row per (unit_code × operating-hour), with each unit's offer curve
as up to twenty MW/price breakpoints in parallel wide columns
(`mw1`/`bid1` … `mw20`/`bid20`) plus cost parameters
(`no_load_cost`, `avg_ecomin`, `avg_ecomax`, etc.).

**This directory's contents are gitignored** (see `.gitignore`) — the corpus is
≈1–2 GB compressed at ~29,000 rows/day × 365 days over three years, far past
what's practical to commit. Only this README is tracked.

**THE LIVE CORPUS IS SIX YEARS, 2020–2025 (72 month-files), NOT three.** It was
extended from 36 files (2023–2025) by session pjm-h9c on 2026-09-16 as a rule 23
`[R-FROZEN-DERIVE]` source-data change (commit `73a68234`), and
`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json` — the committed
surface the PJM keeper solves on — now declares `n_month_files_parsed: 72` with
12-of-12 month coverage in every one of those years. Re-fetching fewer years
regenerates a three-year surface that prices 2020/2021/2022 from a blend of
2023–2025, which is the estimate rule 14 `[R-ACCURATE]` says to replace with the
publisher's own data. **Both `fetch_pjm_energy_offers.py` and
`derive_pjm_offer_midcurve.py` still default to `--years 2023 2024 2025`, so pass
the six years explicitly** (see below) until that default pair is moved —
`docs/FINDING-pjm-h12-the-midcurve-rebuild-is-a-clean-rederivation-2026-09-20.md`
§5 records why this lane did not move it and §2 verifies the re-derivation.

**2019 WAS ADDED BY MERGE, NOT BY RE-DERIVATION (PJM-NEXT-4, 2026-09-26).** The 12
2019 month-files were fetched and derived alone with
`derive_pjm_offer_midcurve.py --years 2019 --merge-into-existing`, which inserts the
2019 ladders and leaves every 2020–2025 entry and the pooled forward ladder
byte-identical (recorded under `_provenance.merged_year_derives`). A full re-derive
over 2019–2025 would re-segment and re-pool the other years; do not run one unless
their source data changed (rule 23). **Publisher gap, carried as published:** from
2019-11-08 through 2019-12-05 the feed serves ~1,081 units/hour instead of ~1,220
(the API's own row count for 2019-11-12 is 25,944 vs 29,256 on 2019-11-07).
Regenerate 2019 with `fetch_pjm_energy_offers.py --years 2019`.

**Source:** PJM DataMiner2 REST API, `https://api.pjm.com/api/v1`
(`energy_market_offers` feed). See `docs/data-licensing.md` §4 — PJM
DataMiner2 data carries a non-member redistribution restriction; this
directory is gitignored partly *because of* that restriction, not only
because of size.

**Regeneration:**

```bash
# THE LIVE CORPUS — what the committed mid-curve surface was derived from:
python scripts/data/fetch_pjm_energy_offers.py --years 2020 2021 2022 2023 2024 2025

python scripts/data/fetch_pjm_energy_offers.py           # DEFAULT = 2023–2025 ONLY (see note above)
python scripts/data/fetch_pjm_energy_offers.py --years 2024
python scripts/data/fetch_pjm_energy_offers.py --years 2023 2024 --months 1 2 3
python scripts/data/fetch_pjm_energy_offers.py --force   # re-download existing files
```

Auth uses the public `Ocp-Apim-Subscription-Key` published in DataMiner2's
own `settings.json`; results are posted monthly, four months in arrears
(2023–2025 data is fully available as of mid-2026); retention is indefinite
from 2017-11-01 onward. See the script's own docstring for pagination and
rate-limit details.

**Curate into the clean tree:**

```bash
python scripts/data/curate_energy_offers.py
```

Reads the monthly wide-format parquets here and writes one clean long-format
Parquet per year to `data/clean/energy-offers/PJM/` (wide → long pivot: one
row per unit_code × operating-hour × offer-step index) through the frozen
`scripts.lib.clean_io.write_clean` seam.
