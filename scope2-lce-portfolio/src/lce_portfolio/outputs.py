"""Serialization and reporting of sweep results.

Writes two artifacts per sweep: a compact ``frontier`` table (one row per
setpoint: matching%, premium, shadow price) and a ``build_mix`` table (build MW
per resource per setpoint), both as Parquet — mirroring the market-sim
one-file-per-result convention. Also renders a plain-text summary for the CLI.

Since PP-09 (ADR 0014 §6) this is also the payload-assembly seam: the
``write_outputs`` chain emits ``report.json`` + ``report.html`` **by default**
(callers opt out with ``report=False`` / the CLI's ``--no-report``), and
:func:`write_report` writes one report for a whole run — single-ISO or an
``--all-isos`` batch (which is what makes the §2.6 multi-ISO table possible).
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
                "grid_co2_tons": r.grid_co2_tons,
                "resource_co2_tons": r.resource_co2_tons,
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
    extra: dict | None = None,
) -> Path:
    """Write a ``<iso>_run_metadata.json`` capturing config + per-setpoint status.

    Provenance for reproducibility: the full config, tool version, and the
    solver status / headline metrics of each solve. ``extra`` merges
    additional provenance blocks in verbatim (e.g. the ``profile_source``
    real-vs-synthetic label, audit finding DL-8).
    """
    from lce_portfolio import __version__

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "tool_version": __version__,
        "iso": sweep.iso,
        "mode": sweep.mode,
        "config": asdict(config),
        **(extra or {}),
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


def write_report(
    sweeps: list[SweepResult],
    configs: list[PortfolioConfig],
    out_dir: str | Path,
    *,
    run_id: str | None = None,
    report_hourly: str = "selected",
) -> dict[str, Path]:
    """Write ``report.json`` + ``report.html`` for one run (ADR 0014 §1/§3/§6).

    One report per run: a single-ISO run passes one sweep/config pair, an
    ``--all-isos`` batch passes one per ISO (yielding the §2.6 multi-ISO
    table). ``report_hourly`` selects which setpoints carry §2.7 hourly series
    (``"selected"``/``"all"``, §3 size discipline). Returns the written paths
    keyed by ``"report_json"`` / ``"report_html"``.
    """
    # Local import: report.py imports frontier_table from this module, so the
    # emission seam must not create an import cycle at module load.
    from lce_portfolio.report import build_report_payload, render_report

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_report_payload(
        sweeps, configs, run_id=run_id, report_hourly=report_hourly
    )
    paths = {
        "report_json": out_dir / "report.json",
        "report_html": out_dir / "report.html",
    }
    paths["report_json"].write_text(json.dumps(payload, separators=(",", ":")))
    paths["report_html"].write_text(render_report(payload))
    return paths


def write_outputs(
    sweep: SweepResult,
    out_dir: str | Path,
    config: PortfolioConfig | None = None,
    *,
    report: bool = True,
    run_id: str | None = None,
    report_hourly: str = "selected",
    metadata_extra: dict | None = None,
) -> dict[str, Path]:
    """Write frontier and build-mix Parquet files under ``out_dir``.

    If ``config`` is given, also writes a run-metadata JSON and — by default
    (ADR 0014 §6) — the single-ISO ``report.json`` + ``report.html`` via
    :func:`write_report`; pass ``report=False`` to suppress the report (the
    CLI's ``--no-report``, and what the CLI batch path does per-ISO before
    writing one combined report). Returns a dict of the written paths keyed by
    ``"frontier"`` / ``"build_mix"`` / ``"metadata"`` / ``"report_json"`` /
    ``"report_html"``.
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
        paths["metadata"] = write_run_metadata(
            sweep, config, out_dir, extra=metadata_extra
        )
        if report:
            paths.update(
                write_report(
                    [sweep],
                    [config],
                    out_dir,
                    run_id=run_id,
                    report_hourly=report_hourly,
                )
            )
    return paths


def summarize(sweep: SweepResult) -> str:
    """Render a human-readable summary of the sweep frontier and mix.

    A residual-carbon column (tCO₂/yr = unmatched grid purchases at the hourly
    fossil-average rate, ADR 0013, plus partial-capture resource residuals,
    ADR 0012; the grid/resource split lives in the frontier Parquet) is shown
    only when at least one sweep point has a nonzero residual; otherwise the
    layout matches the pre-carbon summary.
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
        # A failed setpoint must not read like a solved "0% at $0" row
        # (audit finding CL-4): flag the solver status inline.
        flag = "" if r.status == "Optimal" else f"  << {r.status.upper()} — no solution"
        lines.append(
            f"{r.setpoint:>18.3g} | {r.matching_pct * 100:>9.2f}% | "
            f"{r.premium:>13.2f}{co2_cell} | {mix or '(grid only)'}{flag}"
        )
    return "\n".join(lines)
