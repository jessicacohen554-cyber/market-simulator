# Clean-data solve profiles

`data/clean` is gitignored, so every fresh solve container rebuilds it. A bare
`scripts/regenerate_clean.py` runs all ~59 curate scripts for every ISO and
year (measured 39–95 min; `curate_emissions` alone ~25 min at ~9 GiB). The
backcast solve reads only a small subset, so a shard should run:

```
python scripts/regenerate_clean.py --solve-profile <ISO>     # or: all
    [--years 2023 2024 2025] [--with-forecast] [--force] [--dry-run]
```

**What a profile contains** — `scripts/lib/clean_profiles.py::SOLVE_SOURCES`,
one entry per datatype a solve-path loader reads from `data/clean` with **no**
`MARKET_SIM_USE_CLEAN` gate and **no** raw fallback (absent ⇒ the mechanism
silently no-ops). Backcast lane: capacity-deliverability, hydro-plant-modes,
coal-stocks, coal-receipts, transfer-interface-limits, ramp-capability,
gtc-limits, reserve-requirements, storage-as-awards, maxgen-events,
winter-fuel-inventory, chp-btm-share, nyiso-interface-flows,
seam-neighbour-price. Forecast lane (`--with-forecast`): confirmed-retirements,
transmission-expansion, capacity-market-avoidable-cost-rate. Each entry names
its consumer, the ISOs it can build (read at run time from the curate script's
own registry), and the ISO/year flags forwarded. Solve years are **never**
forwarded to the coal tables (year Y reads Y-1 stocks and earlier receipts).

| ISO | datatypes | ISO | datatypes | ISO | datatypes |
|---|---|---|---|---|---|
| ERCOT | 4 | PJM | 7 | NEISO | 7 |
| CAISO | 7 | MISO | 7 | SPP | 4 |
| NYISO | 7 | NWPP | 4 | SOCO | 3 |

**Manifest key** — `data/clean/<datatype>/.manifest.json`: sha256 over the git
blob shas of the curate script, `clean_io.py` and every `scripts.lib` module it
imports (transitively); the schema YAML's blob sha; and, per declared raw input,
`git rev-parse HEAD:<path>` plus size+mtime of any untracked/ignored/modified
file under it (stat walk if git does not know the path). The `--isos`/`--years`
scope is stored beside the key; a datatype is kept iff key unchanged, scope
covered and a parquet still present. `market_sim` imports are not in the key —
use `--force` after changing one. A bare run is unchanged (no skip, no manifest);
`--incremental` opts a bare/positional run in.

**Measured** (2026-10-01, 4 vCPU, 13.4 GiB cgroup, empty clean tree):

| step | wall |
|---|---|
| `--solve-profile SPP` (4 datatypes, 1.1 MB) | 46 s cold / 2 s warm |
| `--solve-profile NEISO` (7 datatypes, 1.2 MB) | 46 s cold / 1 s warm |
| all 17 profile scripts, every ISO | 156 s |
| bare default run (59 datatypes) | measuring — see PR |

Per-datatype (all ISOs): coal-receipts 41.5 s · ramp-capability 49.6 s (1.1 GiB) ·
gtc-limits 26.6 s · hydro-plant-modes 13.2 s · transfer-interface-limits 5.8 s ·
nyiso-interface-flows 5.1 s · seam-neighbour-price 4.9 s · chp-btm-share 2.6 s ·
coal-stocks 1.3 s · the other eight < 1.2 s each.

**Caveats.** Entries whose raw inputs default to all of `data/raw` are
invalidated by any new untracked file there (e.g. eGRID mirrors a solve writes)
— conservative by design. A per-ISO build creates `confirmed-retirements/`,
which that loader reads as "curated, zero rows" for other ISOs — never share a
per-ISO clean tree across ISOs on the forecast lane.

**Extending.** A new clean-only solve-path loader appends one `CleanSource`;
`tests/curation/test_clean_profiles.py` checks its script, schema and flags,
and add it to that test's `SOLVE_PATH_CLEAN_ONLY` list.
