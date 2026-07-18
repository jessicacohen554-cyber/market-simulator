"""miso-73 per-seam interchange validation (the miso72_perzone_validate pattern).

Scores a solved MISO calibration bundle's PER-SEAM interchange against the
measured EIA-930 BA-to-BA flows pooled onto the model's seams
(``interchange_config.MISO_SEAM_DIBA`` + the Manitoba MHEB firm block) — the
pre-named deliverable of the G-23 seam-envelope composition-fix charter
(``docs/handoffs/miso-g23-seam-envelope-composition-design-2026-07.md`` §6).
Validates mechanisms against MEASURED per-seam data, never by the scored
residual alone (CLAUDE.md keeper protocol).

Per seam and year:
  1. annual net TWh, model vs measured (charter band B2);
  2. monthly net-flow fidelity — mean |model − measured| monthly GWh;
  3. flow-duration RMSE (MW) — sorted hourly net flow, model vs measured.

Hourly correlation is reported but NOT a target: the measured flow is
price-decorrelated (r ≈ +0.06), so the duration curve is the honest
reproducible structure (miso-import-starvation-rootcause-2026-07.md §3).

Model seam flow = Σ dispatch of the seam's ``_refimp_``/``_refexp_`` band rows
(imports positive, export sinks negative) from ``dispatch/{year}_P1.parquet``;
the Manitoba row adds the firm block (``Manitoba_firmhydro``).

Usage:
    python scripts/miso73_perseam_validate.py --run-dir <bundle> \\
        [--base-dir <bundle>] [--json-out <path>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

RAW = _REPO / "data" / "raw"
INTERCHANGE_PARQUET = RAW / "eia-930-interchange" / "MISO interchange hourly.parquet"

YEARS = (2023, 2024, 2025)
HOURS = 8760

# Fixed non-leap calendar (the LP clock; mirrors derive_miso_seam_ladders).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """1-based month per model hour on the fixed non-leap calendar."""
    edges = np.asarray([*_MONTH_START_HOUR, hours])
    return np.searchsorted(edges, np.arange(hours), side="right").astype(int)


def measured_seam_flows() -> dict[int, dict[str, np.ndarray]]:
    """Measured per-seam hourly net-import MW on the model clock, per year.

    Seams are ``MISO_SEAM_DIBA`` pools plus ``Manitoba`` (the MHEB DIBA, which
    the priced-seam map deliberately excludes). Hour-ending local is shifted to
    hour-beginning; Feb 29 drops; isolated gaps interpolate (limit 3).
    """
    from market_sim.config.interchange_config import MISO_SEAM_DIBA

    ix = pd.read_parquet(INTERCHANGE_PARQUET)
    t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    ix = ix.assign(year=t.dt.year.to_numpy(), hour=hr)
    ix.loc[(t.dt.month == 2) & (t.dt.day == 29), "hour"] = -1
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < HOURS)]
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    diba_to_seam["MHEB"] = "Manitoba"
    ix = ix.assign(seam=ix["diba"].astype(str).map(diba_to_seam))
    ix = ix.dropna(subset=["seam"])
    flows = -ix.pivot_table(
        index=["year", "hour"],
        columns="seam",
        values="mw",
        aggfunc="sum",
        observed=True,
    )
    out: dict[int, dict[str, np.ndarray]] = {}
    for year in YEARS:
        sub = flows.loc[year].reindex(range(HOURS)).interpolate(limit=3)
        out[year] = {s: sub[s].to_numpy(dtype=float) for s in sub.columns}
    return out


def model_seam_flows(run_dir: Path) -> dict[int, dict[str, np.ndarray]]:
    """Model per-seam hourly net-import MW from the bundle's P1 dispatch."""
    from market_sim.model.transmission import _REF_EXPORT_MARK, _REF_IMPORT_MARK

    out: dict[int, dict[str, np.ndarray]] = {}
    for year in YEARS:
        path = run_dir / "dispatch" / f"{year}_P1.parquet"
        df = pd.read_parquet(path, columns=["unit_id", "hour", "mw"])
        uid = df["unit_id"].astype(str)
        seams: dict[str, np.ndarray] = {}
        for mark in (_REF_IMPORT_MARK, _REF_EXPORT_MARK):
            sel = df[uid.str.contains(mark, regex=False)]
            if sel.empty:
                continue
            name = (
                sel["unit_id"]
                .astype(str)
                .str.rsplit(mark, n=1)
                .str[1]
                .str.partition("#")[0]
            )
            per = sel.assign(seam=name.to_numpy()).pivot_table(
                index="hour",
                columns="seam",
                values="mw",
                aggfunc="sum",
                observed=True,
            )
            per = per.reindex(range(HOURS)).fillna(0.0)
            for s in per.columns:
                seams[s] = seams.get(s, np.zeros(HOURS)) + per[s].to_numpy(dtype=float)
        firm = df[uid.str.contains("Manitoba_firmhydro", regex=False)]
        if not firm.empty:
            manitoba = (
                firm.groupby("hour", observed=True)["mw"]
                .sum()
                .reindex(range(HOURS))
                .fillna(0.0)
                .to_numpy(dtype=float)
            )
            seams["Manitoba"] = seams.get("Manitoba", np.zeros(HOURS)) + manitoba
        out[year] = seams
    return out


def score(
    model: dict[int, dict[str, np.ndarray]],
    measured: dict[int, dict[str, np.ndarray]],
) -> dict:
    """Per (year, seam): annual net TWh, monthly MAE (GWh), duration RMSE, corr."""
    months = _hour_month()
    rows: dict = {}
    for year in YEARS:
        rows[year] = {}
        for seam, act in sorted(measured[year].items()):
            sim = model[year].get(seam)
            if sim is None:
                continue
            ok = ~np.isnan(act)
            monthly_sim = np.array(
                [sim[ok & (months == m)].sum() / 1e3 for m in range(1, 13)]
            )
            monthly_act = np.array(
                [act[ok & (months == m)].sum() / 1e3 for m in range(1, 13)]
            )
            rows[year][seam] = {
                "model_twh": round(sim[ok].sum() / 1e6, 3),
                "meas_twh": round(act[ok].sum() / 1e6, 3),
                "monthly_mae_gwh": round(
                    float(np.mean(np.abs(monthly_sim - monthly_act))), 1
                ),
                "duration_rmse_mw": round(
                    float(np.sqrt(np.mean((np.sort(sim[ok]) - np.sort(act[ok])) ** 2))),
                    1,
                ),
                "hourly_corr": round(float(np.corrcoef(sim[ok], act[ok])[0, 1]), 3),
            }
    return rows


def _print(tag: str, rows: dict) -> None:
    print(f"\n=== {tag} ===")
    for year in YEARS:
        print(f"  {year}:")
        for seam, s in rows[year].items():
            print(
                f"    {seam:9s} net {s['model_twh']:+8.2f} vs {s['meas_twh']:+8.2f} "
                f"TWh (err {s['model_twh'] - s['meas_twh']:+6.2f}) | monthly MAE "
                f"{s['monthly_mae_gwh']:7.1f} GWh | duration RMSE "
                f"{s['duration_rmse_mw']:6.0f} MW | corr {s['hourly_corr']:+.2f}"
            )
        tot_m = sum(s["model_twh"] for s in rows[year].values())
        tot_a = sum(s["meas_twh"] for s in rows[year].values())
        print(
            f"    {'TOTAL':9s} net {tot_m:+8.2f} vs {tot_a:+8.2f} TWh "
            f"(err {tot_m - tot_a:+6.2f})"
        )


def main() -> int:
    """CLI: score --run-dir (and optionally --base-dir) against measured seams."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--base-dir", type=Path, default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    measured = measured_seam_flows()
    result = {"run": score(model_seam_flows(args.run_dir), measured)}
    _print(str(args.run_dir), result["run"])
    if args.base_dir:
        result["base"] = score(model_seam_flows(args.base_dir), measured)
        _print(str(args.base_dir), result["base"])
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
