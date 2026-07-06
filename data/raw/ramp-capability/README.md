# ramp-capability (raw sources)

Measured per-plant 10-minute ramp / fast-start capability inputs for the
reserve co-optimization deliverability bound (`FleetArrays.ramp10`).

**This datatype has no raw files of its own.** Both sources already live in
the immutable raw tree and are read in place by
`scripts/curate_ramp_capability.py`:

| source | location | quantity |
|---|---|---|
| EIA-860 Schedule 3.1 generator table | `data/raw/eia-860/eia860_generator_operable.parquet` (+ `eia860_generators.parquet` for the balancing-authority scoping) | `Time from Cold Shutdown to Full Load` category per generator — `10M` (full load within 10 minutes) is the measured fast-start flag; nameplate capacity |
| EPA CAMPD (CEMS) unit-level hourly extracts | `data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` | hourly unit gross load → maximum observed 1-hour plant-level up-ramp (the operating envelope), pooled 2023–2025 |

Authoritative sources: EIA Form 860 annual generator file
(https://www.eia.gov/electricity/data/eia860/) and EPA Clean Air Markets
Program Data custom hourly emissions extracts (https://campd.epa.gov/).

Vintage policy: the CEMS envelope pools **2023–2025 only** — 2022 and 2026
are the designated holdout periods (CLAUDE.md rule 22) and are not read.

Registered ISOs: PJM, MISO (`scripts/lib/ramp_capability/<iso>.py`). Other
ISOs are additive drops (a module + `register(...)`) when their per-asset
reserve co-optimization needs the measured bound.

DATA NEEDED: none for PJM/MISO — every listed state's 2023–2025 unit-level
CAMPD extract is present. A state extract added later widens coverage on the
next `regenerate_clean.py ramp-capability` run automatically.
