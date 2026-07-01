"""Serialization and reporting of sweep results.

Writes two artifacts per sweep: a compact ``frontier`` table (one row per
setpoint: matching%, premium, shadow price) and a ``build_mix`` table (build MW
per resource per setpoint), both as Parquet — mirroring the market-sim
one-file-per-result convention. Also renders a plain-text summary for the CLI.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.sweep import SweepResult


def frontier_table(sweep: SweepResult) -> pd.DataFrame:
    """Return the matching%-vs-premium frontier as a DataFrame."""
    rows = []
    for r in sweep.results:
        rows.append(
            {
                "iso": sweep.iso,
                "mode": sweep.mode,
                "setpoint": r.setpoint,
                "matching_pct": r.matching_pct,
                "premium_per_mwh": r.premium,
                "premium_per_year": r.premium_total_per_year,
                "pct_over_bau": r.pct_over_bau,
                "net_cost": r.net_cost,
                "bau_cost": r.bau_cost,
                "capital_cost": r.capital_cost,
                "avoided_purchase_cost": r.avoided_purchase_cost,
                "surplus_mwh": r.surplus_mwh,
                "surplus_revenue": r.surplus_revenue,
                "grid_buy_mwh": r.grid_buy_mwh,
                "total_load_mwh": r.total_load_mwh,
                "residual_co2_tons": r.residual_co2_tons,
                "shadow_price": r.shadow_price,
                "status": r.status,
            }
        )
    return pd.DataFrame(rows)


def build_mix_table(sweep: SweepResult) -> pd.DataFrame:
    """Return build MW per resource per setpoint (long form)."""
    rows = []
    for r in sweep.results:
        for name, mw in zip(r.resource_names, r.build_mw):
            rows.append(
                {
                    "iso": sweep.iso,
                    "setpoint": r.setpoint,
                    "resource": name,
                    "build_mw": float(mw),
                }
            )
    return pd.DataFrame(rows)


def write_run_metadata(
    sweep: SweepResult,
    config: PortfolioConfig,
    out_dir: str | Path,
) -> Path:
    """Write a ``<iso>_run_metadata.json`` capturing config + per-setpoint status.

    Provenance for reproducibility: the full config, tool version, and the
    solver status / headline metrics of each solve.
    """
    from lce_portfolio import __version__

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "tool_version": __version__,
        "iso": sweep.iso,
        "mode": sweep.mode,
        "config": asdict(config),
        "solves": [
            {
                "setpoint": r.setpoint,
                "status": r.status,
                "matching_pct": r.matching_pct,
                "premium_per_mwh": r.premium,
            }
            for r in sweep.results
        ],
    }
    path = out_dir / f"{sweep.iso}_run_metadata.json"
    path.write_text(json.dumps(meta, indent=2))
    return path


def write_outputs(
    sweep: SweepResult,
    out_dir: str | Path,
    config: PortfolioConfig | None = None,
) -> dict[str, Path]:
    """Write frontier and build-mix Parquet files under ``out_dir``.

    If ``config`` is given, also writes a run-metadata JSON. Returns a dict of the
    written paths keyed by ``"frontier"`` / ``"build_mix"`` / ``"metadata"``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "frontier": out_dir / f"{sweep.iso}_frontier.parquet",
        "build_mix": out_dir / f"{sweep.iso}_build_mix.parquet",
    }
    frontier_table(sweep).to_parquet(paths["frontier"], index=False)
    build_mix_table(sweep).to_parquet(paths["build_mix"], index=False)
    if config is not None:
        paths["metadata"] = write_run_metadata(sweep, config, out_dir)
    return paths


def summarize(sweep: SweepResult) -> str:
    """Render a human-readable summary of the sweep frontier and mix.

    A residual-carbon column (tCO₂/yr from unmatched grid purchases, ADR 0007) is
    shown only when the marginal emission rate produced a nonzero residual for at
    least one sweep point; otherwise the layout matches the pre-carbon summary.
    """
    setpoint_label = "premium$/MWh" if sweep.mode == "premium_cap" else "target"
    show_co2 = any(r.residual_co2_tons > 0 for r in sweep.results)
    co2_head = f" | {'residualCO2(t)':>15}" if show_co2 else ""
    lines = [
        f"LCE portfolio sweep — ISO={sweep.iso} mode={sweep.mode}",
        f"{'set(' + setpoint_label + ')':>18} | {'matching%':>10} | "
        f"{'premium$/MWh':>13}{co2_head} | mix (MW)",
        "-" * (78 + (len(co2_head))),
    ]
    for r in sweep.results:
        mix = ", ".join(
            f"{n}={mw:,.0f}" for n, mw in zip(r.resource_names, r.build_mw) if mw > 1e-3
        )
        co2_cell = f" | {r.residual_co2_tons:>15,.0f}" if show_co2 else ""
        lines.append(
            f"{r.setpoint:>18.3g} | {r.matching_pct * 100:>9.2f}% | "
            f"{r.premium:>13.2f}{co2_cell} | {mix or '(grid only)'}"
        )
    return "\n".join(lines)
