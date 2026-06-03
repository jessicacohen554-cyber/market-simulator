# market-sim

LP-based electricity market dispatch and policy simulator. Forecasts hourly
(8760) generation, prices, emissions and capacity evolution across U.S. ISOs
from 2026→2050, with a historical-backcast mode for calibration against EIA-930,
CAMPD, eGRID and EIA-923 actuals.

- **Solver:** HiGHS via `highspy` (pure LP, no MIP). Prices are LP duals.
- **ISOs:** ERCOT (calibrated reference) plus CAISO, PJM, MISO, SPP, NYISO, NEISO.
- **Methodology:** see [`model-methodology-spec.md`](model-methodology-spec.md).
- **Working instructions / conventions:** see [`claude.md`](claude.md) and
  [`CONVENTIONS.md`](CONVENTIONS.md).

Docs are kept in sync with the code via the `/sync-docs` skill — run it at the
end of a session once an approach has settled.
