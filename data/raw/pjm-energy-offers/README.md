# pjm-energy-offers — raw (gitignored)

`pjm_energy_offers_<year>_<month>.parquet` — PJM DataMiner2 `energy_market_offers`
feed: one row per (unit_code × operating-hour), with each unit's offer curve
as up to twenty MW/price breakpoints in parallel wide columns
(`mw1`/`bid1` … `mw20`/`bid20`) plus cost parameters
(`no_load_cost`, `avg_ecomin`, `avg_ecomax`, etc.).

**This directory's contents are gitignored** (see `.gitignore`) — the 3-year
corpus (2023–2025) is ≈1–2 GB compressed at ~29,000 rows/day × 365 days, far
past what's practical to commit. Only this README is tracked.

**Source:** PJM DataMiner2 REST API, `https://api.pjm.com/api/v1`
(`energy_market_offers` feed). See `docs/data-licensing.md` §4 — PJM
DataMiner2 data carries a non-member redistribution restriction; this
directory is gitignored partly *because of* that restriction, not only
because of size.

**Regeneration:**

```bash
python scripts/fetch_pjm_energy_offers.py               # 2023–2025, all months
python scripts/fetch_pjm_energy_offers.py --years 2024
python scripts/fetch_pjm_energy_offers.py --years 2023 2024 --months 1 2 3
python scripts/fetch_pjm_energy_offers.py --force        # re-download existing files
```

Auth uses the public `Ocp-Apim-Subscription-Key` published in DataMiner2's
own `settings.json`; results are posted monthly, four months in arrears
(2023–2025 data is fully available as of mid-2026); retention is indefinite
from 2017-11-01 onward. See the script's own docstring for pagination and
rate-limit details.

**Curate into the clean tree:**

```bash
python scripts/curate_energy_offers.py
```

Reads the monthly wide-format parquets here and writes one clean long-format
Parquet per year to `data/clean/energy-offers/PJM/` (wide → long pivot: one
row per unit_code × operating-hour × offer-step index) through the frozen
`scripts.lib.clean_io.write_clean` seam.
