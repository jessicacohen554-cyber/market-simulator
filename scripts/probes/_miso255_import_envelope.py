"""miso-255 phase 0 addendum: the MISO import balance, year by year.

Phase 0 items 1-4 found that MISO's CC_REGULAR capacity factor TRACKS the meter
(r = +0.817), so ``pjm-h1``'s object is absent here — and that the C4 gas
residual is flat in month and in load decile, i.e. a LEVEL substitution rather
than a timing failure. This probe measures the substitution's counterparty.

Compares, per year and hour: the model's own ``import`` class (committed
``hourly/class_hourly_<year>.parquet``), MISO's MEASURED net import
(``load_eia_hourly_benchmark``'s ``interchange``, sign-flipped), and the armed
``miso_seam_flow_limit`` p90 deliverability envelope the keeper solves under
(``measured_seam_import_envelope`` at the keeper's own settings —
``miso_seam_flow_percentile: None`` -> the p90 default,
``miso_seam_envelope_hour_ending_key: True``). **Zero LP.**
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402
from market_sim.data.eia930.envelopes import measured_seam_import_envelope  # noqa: E402

T = 8760
BUNDLES = {
    2020: "miso251_tp2020",
    2021: "miso251_tp2021",
    2022: "miso251_screen2022",
    2023: "miso_fuelvintage_A",
    2024: "miso_fuelvintage_A",
    2025: "miso_fuelvintage_A",
}
YEARS = tuple(sorted(BUNDLES))


def model_import(year: int) -> np.ndarray:
    ch = pd.read_parquet(
        REPO
        / "results/calibration"
        / BUNDLES[year]
        / "hourly"
        / f"class_hourly_{year}.parquet"
    )
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == "import")]
    return (
        ch.groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .fillna(0.0)
        .to_numpy(dtype=float)
    )


def main() -> None:
    print("=" * 104)
    print(
        "MISO net import — model vs measured vs the armed p90 deliverability envelope"
    )
    print("  envelope = sum over priced seams of measured_seam_import_envelope(p90,")
    print("  hour_ending_key=True), the keeper's own miso_seam_flow_limit setting")
    print("=" * 104)
    print(
        f"{'yr':>6s}{'model TWh':>11s}{'meter TWh':>11s}{'OVER TWh':>10s}"
        f"{'envlp TWh':>11s}{'model/env':>11s}{'meter/env':>11s}"
        f"{'h>=95% env':>12s}{'h>=99% env':>12s}"
    )
    rows = {}
    for y in YEARS:
        m = model_import(y)
        bench = load_eia_hourly_benchmark("MISO", y)
        meter = -np.asarray(bench["interchange"], dtype=float)[:T]
        env = measured_seam_import_envelope(
            "MISO", y, T, percentile=None, direction="import", hour_ending_key=True
        )
        tot = (
            np.sum([v[:T] for v in env.values()], axis=0) if env else np.full(T, np.nan)
        )
        pos = tot > 0.0
        util = np.where(pos, m / np.where(pos, tot, 1.0), np.nan)
        rows[y] = (m, meter, tot, util)
        print(
            f"{y:>6d}{m.sum() / 1e6:>11.2f}{meter.sum() / 1e6:>11.2f}"
            f"{(m - meter).sum() / 1e6:>10.2f}{tot.sum() / 1e6:>11.2f}"
            f"{m.sum() / tot.sum():>11.3f}{meter.sum() / tot.sum():>11.3f}"
            f"{int(np.nansum(util >= 0.95)):>12d}{int(np.nansum(util >= 0.99)):>12d}"
        )

    print("\nSeam composition of the p90 import envelope (TWh):")
    seams = ("PJM", "SPP", "South", "Manitoba")
    print(f"{'yr':>6s}" + "".join(f"{s:>12s}" for s in seams))
    for y in YEARS:
        env = (
            measured_seam_import_envelope(
                "MISO", y, T, percentile=None, direction="import", hour_ending_key=True
            )
            or {}
        )
        print(
            f"{y:>6d}"
            + "".join(
                f"{env.get(s, np.zeros(T))[:T].sum() / 1e6:>12.2f}" for s in seams
            )
        )

    print("\nModel import utilisation of the envelope, by decile of the envelope hour:")
    print(f"{'yr':>6s}" + "".join(f"{'D' + str(k + 1):>8s}" for k in range(10)))
    for y in YEARS:
        m, meter, tot, util = rows[y]
        q = np.quantile(tot, np.linspace(0, 1, 11))
        q[0] -= 1.0
        dec = np.clip(np.searchsorted(q, tot, side="left") - 1, 0, 9)
        print(
            f"{y:>6d}"
            + "".join(f"{np.nanmean(util[dec == k]):>8.3f}" for k in range(10))
        )

    print(
        "\nMeasured import utilisation of the SAME envelope (the like-for-like control):"
    )
    print(f"{'yr':>6s}" + "".join(f"{'D' + str(k + 1):>8s}" for k in range(10)))
    for y in YEARS:
        m, meter, tot, util = rows[y]
        q = np.quantile(tot, np.linspace(0, 1, 11))
        q[0] -= 1.0
        dec = np.clip(np.searchsorted(q, tot, side="left") - 1, 0, 9)
        mu = np.where(tot > 0, meter / np.where(tot > 0, tot, 1.0), np.nan)
        print(
            f"{y:>6d}" + "".join(f"{np.nanmean(mu[dec == k]):>8.3f}" for k in range(10))
        )


if __name__ == "__main__":
    main()
