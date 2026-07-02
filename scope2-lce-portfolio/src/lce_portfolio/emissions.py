"""Per-ISO marginal CO2 emission rate table and config resolution (ADR 0007).

ADR 0007 attributes residual carbon to unmatched grid purchases at the ISO
**marginal** emission rate: ``residual_co2_tons = grid_buy_mwh × rate``. The LP
(``lp.py``) already reads the scalar off ``config.marginal_co2_ton_per_mwh``,
which defaults to ``0.0`` (reporting off). This module supplies the other half:
a per-ISO rate table (``data/emissions/marginal_co2.csv``, provisional EPA
eGRID non-baseload proxy — see the CSV header) and the loader/resolution logic
that turns it into the config scalar the LP consumes, mirroring the
``load_resource_caps``/``load_hydro_budgets`` loader pattern in
``resources.py``.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from lce_portfolio.config import PortfolioConfig

# Resolve the packaged data table the same way resources.py resolves its tables
# (no dependence on market_sim paths).
_PKG_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARGINAL_CO2_TABLE = _PKG_ROOT / "data" / "emissions" / "marginal_co2.csv"


def _read_csv_skip_comments(path: Path) -> list[dict[str, str]]:
    """Read a CSV into row dicts, skipping leading ``#``-prefixed comment lines.

    The marginal-CO2 table carries a multi-line provenance comment above its
    header (EPA eGRID vintage, subregion mapping, unit conversion); plain
    ``csv.DictReader`` would otherwise treat the first comment line as the
    header row.
    """
    text = path.read_text()
    body = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    return list(csv.DictReader(io.StringIO(body)))


def load_marginal_co2(iso: str, path: Path | None = None) -> float | None:
    """Return the marginal CO2 rate (tCO2/MWh) for ``iso``, or ``None`` if unknown.

    Reads ``data/emissions/marginal_co2.csv`` (EPA eGRID non-baseload output
    emission rate proxy, provisional per ADR 0007). An ISO absent from the
    table — e.g. the ``SAMPLE`` demo ISO — returns ``None`` rather than raising,
    letting callers fall back to ``0.0`` (reporting off).
    """
    src = path or DEFAULT_MARGINAL_CO2_TABLE
    for row in _read_csv_skip_comments(src):
        if row["iso"].strip() == iso:
            return float(row["rate_ton_per_mwh"])
    return None


def resolve_marginal_co2_rate(
    config: PortfolioConfig, path: Path | None = None
) -> float:
    """Resolve the marginal CO2 rate to use for ``config`` (ADR 0007 precedence).

    Precedence: an explicitly-set ``config.marginal_co2_ton_per_mwh > 0`` wins;
    else the ``data/emissions/marginal_co2.csv`` table value for ``config.iso``;
    else ``0.0`` (residual-carbon reporting stays off, e.g. for ``SAMPLE``).
    """
    if config.marginal_co2_ton_per_mwh > 0:
        return config.marginal_co2_ton_per_mwh
    table_rate = load_marginal_co2(config.iso, path)
    return table_rate if table_rate is not None else 0.0


def apply_marginal_co2(
    config: PortfolioConfig, path: Path | None = None
) -> PortfolioConfig:
    """Return ``config`` with ``marginal_co2_ton_per_mwh`` resolved (ADR 0007).

    The run-time seam between config and the LP: callers (``cli.run_one_iso``)
    invoke this once per ISO run so the LP always receives an already-resolved
    scalar via ``config.with_overrides`` — ``lp.py`` itself stays table-agnostic.
    """
    return config.with_overrides(
        marginal_co2_ton_per_mwh=resolve_marginal_co2_rate(config, path)
    )
