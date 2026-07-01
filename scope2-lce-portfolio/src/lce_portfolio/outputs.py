"""Serialization and reporting of sweep results.

Writes two artifacts per sweep: a compact ``frontier`` table (one row per
setpoint: matching%, premium, shadow price) and a ``build_mix`` table (build MW
per resource per setpoint), both as Parquet — mirroring the market-sim
one-file-per-result convention. Also renders a plain-text summary for the CLI.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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
                "net_cost": r.net_cost,
                "bau_cost": r.bau_cost,
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


def write_outputs(sweep: SweepResult, out_dir: str | Path) -> dict[str, Path]:
    """Write frontier and build-mix Parquet files under ``out_dir``.

    Returns a dict of the written paths keyed by ``"frontier"`` / ``"build_mix"``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "frontier": out_dir / f"{sweep.iso}_frontier.parquet",
        "build_mix": out_dir / f"{sweep.iso}_build_mix.parquet",
    }
    frontier_table(sweep).to_parquet(paths["frontier"], index=False)
    build_mix_table(sweep).to_parquet(paths["build_mix"], index=False)
    return paths


def summarize(sweep: SweepResult) -> str:
    """Render a human-readable summary of the sweep frontier and mix."""
    setpoint_label = "premium$/MWh" if sweep.mode == "premium_cap" else "target"
    lines = [
        f"LCE portfolio sweep — ISO={sweep.iso} mode={sweep.mode}",
        f"{'set(' + setpoint_label + ')':>18} | {'matching%':>10} | {'premium$/MWh':>13} | mix (MW)",
        "-" * 78,
    ]
    for r in sweep.results:
        mix = ", ".join(
            f"{n}={mw:,.0f}" for n, mw in zip(r.resource_names, r.build_mw) if mw > 1e-3
        )
        lines.append(
            f"{r.setpoint:>18.3g} | {r.matching_pct * 100:>9.2f}% | "
            f"{r.premium:>13.2f} | {mix or '(grid only)'}"
        )
    return "\n".join(lines)
