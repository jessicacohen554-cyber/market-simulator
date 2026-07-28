"""nyiso-92 characterization: where NYISO's per-class hourly r is lost.

Decomposes each fossil class's hourly model-vs-actual correlation for a
bundle into the layers that carry it — diurnal profile (the D-1 statistic),
day-to-day energy, within-day residual, month level — and attributes the
non-fossil side against the measured EIA-930 component series (imports,
nuclear, hydro, oil, demand). This is the measurement that motivated the
nyiso-92 hydro capability-envelope arm:

* Per-class hourly r is far below the total-fossil hourly r (0.79-0.86),
  and the cross-class residual correlations are POSITIVE — the gas classes'
  errors move together, so the driver is a common non-fossil component, not
  merit-order shuffling among them.
* The day-to-day layer, not the diurnal profile, carries the loss
  (CC_REGULAR r_day 0.74/0.57/0.53 vs profile r 0.95+), and it collapses in
  winter (DJF daily r 0.02-0.55 vs JJA 0.75-0.93).
* Component attribution: hydro is the worst-tracking material component
  (r_day 0.19-0.41 on 24-28 TWh) with the CAISO parks-at-zero signature
  (model 349/405/1098 hours < 100 MW vs measured 0/15/15; model day-to-day
  std 21-23 GWh vs measured 6-8), nuclear r_day drops to ~0.50 in 2024-25
  (outage timing), imports r_hr 0.40-0.49 (the nyiso-86 §3 open defect).
* The cold-snap gas-vs-oil swaps (2024-01-15/16, 2025-01-17/19: model oil
  +115-149 GWh/day where measured NYIS ``NG: OIL`` is ~flat) are the
  dual-fuel parity relabeling the run recorded under
  ``dual_fuel_oil_reattribution`` — a basis artifact for NYISO (the NYIS
  feed does not track switching; the CLI has since pinned the
  re-attribution NEISO-only), not a dispatch error of the same size.

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso92_hourly_r_decomposition.py \
        --bundle results/calibration/nyiso89_hrmeas_ctloaded
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import legitimacy_diagnostics as ld  # noqa: E402

ISO = "NYISO"
BA = "NYIS"
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP")
SEASONS = (("DJF", (12, 1, 2)), ("MAM", (3, 4, 5)), ("JJA", (6, 7, 8)), ("SON", (9, 10, 11)))


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, 0.0 when either side is constant (no shape to correlate)."""
    if a.std() <= 0.0 or b.std() <= 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def bench_class_hourly(year: int) -> dict[str, np.ndarray]:
    """Measured per-class hourly MW from the committed CAMPD bench."""
    bench = ld.load_bench(REPO, ISO, year)
    out: dict[str, np.ndarray] = {}
    for b in bench.values():
        out.setdefault(b["group"], np.zeros(8760))
        out[b["group"]] += np.asarray(b["mw"], float)[:8760]
    return out


def model_class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Model per-class hourly MW from the bundle's P1 class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        k: g.sort_values("hour")["mw"].to_numpy()[:8760]
        for k, g in df.groupby("klass")
    }


def layer_rows(model: np.ndarray, actual: np.ndarray, year: int) -> dict[str, float]:
    """The r decomposition layers for one aligned series pair."""
    md, ad = model.reshape(365, 24), actual.reshape(365, 24)
    rows = {
        "r_hourly": _r(model, actual),
        "r_daily": _r(md.sum(1), ad.sum(1)),
        "r_profile": _r(md.mean(0), ad.mean(0)),
        "r_withinday": _r(
            (md - md.mean(1, keepdims=True)).ravel(),
            (ad - ad.mean(1, keepdims=True)).ravel(),
        ),
    }
    dates = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    for name, months in SEASONS:
        sel = dates.month.isin(months)
        rows[f"r_day_{name}"] = _r(md.sum(1)[sel], ad.sum(1)[sel])
    return rows


def main(argv: list[str] | None = None) -> int:
    """Print the per-class r decomposition and the component attribution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = parser.parse_args(argv)

    from market_sim.data.eia930 import frames as fr

    for year in args.years:
        act = bench_class_hourly(year)
        mod = model_class_hourly(args.bundle, year)
        print(f"\n=== {year} — per-class r decomposition (model vs CAMPD bench) ===")
        hdr = (
            f"{'class':<12}{'modTWh':>8}{'actTWh':>8}{'r_hr':>7}{'r_day':>7}"
            f"{'r_prof':>7}{'r_wday':>7}" + "".join(f"{s:>7}" for s, _ in SEASONS)
        )
        print(hdr)
        residuals: dict[str, np.ndarray] = {}
        for klass in GAS_CLASSES:
            if klass not in act or klass not in mod:
                continue
            m, a = mod[klass], act[klass]
            residuals[klass] = m - a
            lay = layer_rows(m, a, year)
            print(
                f"{klass:<12}{m.sum() / 1e6:>8.2f}{a.sum() / 1e6:>8.2f}"
                f"{lay['r_hourly']:>7.3f}{lay['r_daily']:>7.3f}"
                f"{lay['r_profile']:>7.3f}{lay['r_withinday']:>7.3f}"
                + "".join(f"{lay[f'r_day_{s}']:>7.3f}" for s, _ in SEASONS)
            )
        tot_m = sum(mod[k] for k in residuals)
        tot_a = sum(act[k] for k in residuals)
        lay = layer_rows(tot_m, tot_a, year)
        print(
            f"{'TOTAL_FOSSIL':<12}{tot_m.sum() / 1e6:>8.2f}{tot_a.sum() / 1e6:>8.2f}"
            f"{lay['r_hourly']:>7.3f}{lay['r_daily']:>7.3f}"
            f"{lay['r_profile']:>7.3f}{lay['r_withinday']:>7.3f}"
            + "".join(f"{lay[f'r_day_{s}']:>7.3f}" for s, _ in SEASONS)
        )
        kls = list(residuals)
        R = np.corrcoef(np.vstack([residuals[k] for k in kls]))
        print("hourly residual cross-corr (positive = common driver):")
        print("            " + "".join(f"{k[:9]:>10}" for k in kls))
        for i, k in enumerate(kls):
            print(f"{k:<12}" + "".join(f"{R[i, j]:>10.2f}" for j in range(len(kls))))

        frame = fr._eia_hourly_frame_filled(BA, year)
        if frame is None:
            print("(no EIA-930 frame — component attribution skipped)")
            continue
        sysm = pd.read_parquet(args.bundle / "hourly" / f"system_{year}.parquet")
        sysm = sysm[sysm["pass"] == "P1"].groupby("hour")["demand"].sum()
        comp = {
            "gas(NG:NG)": (tot_m, np.nan_to_num(frame["NG: NG"].to_numpy(float))),
            "import": (
                mod.get("import", np.zeros(8760)),
                -np.nan_to_num(frame["Total interchange"].to_numpy(float)),
            ),
            "nuclear": (
                mod.get("nuclear", np.zeros(8760)),
                np.nan_to_num(frame["NG: NUC"].to_numpy(float)),
            ),
            "hydro": (
                mod.get("hydro", np.zeros(8760)),
                np.nan_to_num(frame["NG: WAT"].to_numpy(float)),
            ),
            "oil": (
                mod.get("oil", np.zeros(8760)),
                np.nan_to_num(frame["NG: OIL"].to_numpy(float)),
            ),
            "demand": (
                sysm.reindex(range(8760)).to_numpy(float),
                np.nan_to_num(frame["Demand"].to_numpy(float)),
            ),
        }
        print("component attribution vs EIA-930 (TWh model/measured, r_day, r_hr):")
        for name, (m, a) in comp.items():
            m = np.nan_to_num(np.asarray(m, float)[:8760])
            print(
                f"  {name:<11}{m.sum() / 1e6:>7.2f}/{a.sum() / 1e6:>7.2f}"
                f"  r_day {_r(m.reshape(365, 24).sum(1), a.reshape(365, 24).sum(1)):>6.3f}"
                f"  r_hr {_r(m, a):>6.3f}"
            )
        hyd_m = np.nan_to_num(np.asarray(mod.get("hydro", np.zeros(8760)), float))
        hyd_a = np.nan_to_num(frame["NG: WAT"].to_numpy(float))
        print(
            f"  hydro pathology: model hours<100MW {(hyd_m < 100).sum()} vs "
            f"measured {(hyd_a < 100).sum()}; model p5 {np.percentile(hyd_m, 5):.0f} "
            f"vs measured p5 {np.percentile(hyd_a, 5):.0f} MW; day-to-day std "
            f"{hyd_m.reshape(365, 24).sum(1).std() / 1000:.1f} vs "
            f"{hyd_a.reshape(365, 24).sum(1).std() / 1000:.1f} GWh"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
