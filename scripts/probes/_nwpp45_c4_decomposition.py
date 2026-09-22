"""Decompose NWPP's C4 coal miss into level, shape and amplitude. ZERO LP.

Reads only committed artifacts — the keeper's ``hourly/class_hourly_<year>``
and ``hourly/class_band_hourly_<year>`` sidecars (rule 15 ``[R-DASHBOARD]``)
and its EIA-930 benchmark frame — so it reproduces every number in
``docs/handoffs/FINDING-nwpp-45-c4-is-an-amplitude-defect-2026-09-22.md``
without a solve. The benchmark frame lives in the gitignored shared store and
is recovered first with::

    python3 scripts/run_calibration_full.py --restore-shared-inputs <bundle>

The model/actual pair built here is the SAME pair ``render_calibration_html``
puts in ``fuelRows`` and ``calibration_verdict.score_dispatch_corr`` scores, so
the printed ``r``/``NRMSE`` reproduce the committed C4 numbers exactly — which
is the check that the decomposition is of the scored quantity and not a
lookalike.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp45_c4_decomposition.py \
        [--bundle results/calibration/nwpp44_takeorpay_reg]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.bundle_io import require_bundle_input  # noqa: E402

COAL_CLASSES: tuple[str, ...] = ("COAL_BIT", "COAL_PRB", "COAL_WC")
FLAT_BANDS: tuple[str, ...] = ("mustrun", "committed")
HOURS_PER_DAY = 24


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, or NaN when either vector is constant."""
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _nrmse(model: np.ndarray, actual: np.ndarray) -> float:
    """RMSE normalised by the actual series' mean — the C4 convention."""
    return float(np.sqrt(((model - actual) ** 2).mean()) / actual.mean())


def coal_hourly(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(model_mw, actual_mw)`` hourly coal vectors, equal length."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(COAL_CLASSES))]
    model = ch.groupby("hour")["mw"].sum().sort_index().to_numpy(float)
    e930 = pd.read_parquet(require_bundle_input(bundle, "eia930"))
    actual = (
        e930[(e930["year"] == year) & (e930["series"] == "coal")]
        .sort_values("hour")["mw"]
        .to_numpy(float)
    )
    n = min(len(model), len(actual))
    return model[:n], actual[:n]


def flat_band_share(bundle: Path, year: int) -> float:
    """Share (%) of model coal energy sitting in the price-insensitive bands."""
    bd = pd.read_parquet(bundle / "hourly" / f"class_band_hourly_{year}.parquet")
    bd = bd[(bd["pass"] == "P1") & (bd["klass"].isin(COAL_CLASSES))]
    return 100.0 * bd[bd["band"].isin(FLAT_BANDS)]["mw"].sum() / bd["mw"].sum()


def report(bundle: Path, years: tuple[int, ...]) -> None:
    """Print the level / shape / amplitude decomposition for each year."""
    print(f"NWPP C4 coal decomposition — {bundle}")
    print(
        f"{'year':6}{'r':>7}{'NRMSE':>8}{'r_daily':>9}{'r_intra':>9}"
        f"{'prof_r':>8}{'mdl swing':>11}{'act swing':>11}{'ratio':>8}{'flat %':>8}"
    )
    print("-" * 83)
    for year in years:
        model, actual = coal_hourly(bundle, year)
        days = len(model) // HOURS_PER_DAY * HOURS_PER_DAY
        md = model[:days].reshape(-1, HOURS_PER_DAY)
        ad = actual[:days].reshape(-1, HOURS_PER_DAY)
        # Daily level vs within-day deviation: which timescale loses the fit.
        r_daily = _pearson(md.mean(1), ad.mean(1))
        r_intra = _pearson(
            (md - md.mean(1, keepdims=True)).ravel(),
            (ad - ad.mean(1, keepdims=True)).ravel(),
        )
        mp, ap = md.mean(0), ad.mean(0)  # mean diurnal profiles
        m_swing, a_swing = (mp.max() - mp.min()) / 1e3, (ap.max() - ap.min()) / 1e3
        print(
            f"{year:<6}{_pearson(model, actual):7.3f}{_nrmse(model, actual):8.3f}"
            f"{r_daily:9.3f}{r_intra:9.3f}{_pearson(mp, ap):8.3f}"
            f"{m_swing:11.3f}{a_swing:11.3f}{m_swing / a_swing:8.2f}"
            f"{flat_band_share(bundle, year):8.1f}"
        )
    print("-" * 83)
    print("r_daily = corr of daily means · r_intra = corr of within-day deviation")
    print("prof_r  = corr of the two MEAN diurnal profiles (shape only)")
    print("ratio   = model peak-trough swing as a fraction of the measured swing")
    print("flat %  = share of model coal energy in the mustrun+committed bands")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", default="results/calibration/nwpp44_takeorpay_reg")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    report(Path(args.bundle), tuple(args.years))


if __name__ == "__main__":
    main()
