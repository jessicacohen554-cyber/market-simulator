"""miso-255 phase 0 (arm selection): the COINCIDENT boundary transfer envelope.

Decides, at zero LP and BEFORE any arm is built, whether replacing the
bidirectional 8,700 MW ``EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]`` planning scalar
with MISO's OWN measured coincident boundary-transfer envelope (a) has a
footprint, (b) has one LARGEST IN 2021 (the rule-29 screen-year test), and
(c) is a CEILING the LP can clear below rather than a pin.

The estimator is IDENTICAL to the one already armed and adjudicated K for the
per-seam bands (``measured_seam_import_envelope``): the per-(month x hour-of-day)
percentile of the MEASURED EIA-930 directed flow, at the already-registered
``MISO_SEAM_FLOW_PERCENTILE``, on the hour-ENDING key the keeper runs
(``miso_seam_envelope_hour_ending_key=True``). The ONLY difference is the
aggregation order: the boundary total is summed over every seam's DIBAs at the
SAME TIMESTAMP and the percentile is taken of that coincident total, instead of
per-seam percentiles being summed afterward (which over-counts, because the
seams do not peak together).

NOT the object ``miso_seam_coincident_envelope`` (**R**, miso-181): that
conditioned the PER-SEAM envelope on the NEIGHBOUR'S OWN LOAD STATE and was
killed because the conditional p90 was flat in the driver. This changes no
conditioning variable and adds no driver — it replaces one unsourced scalar with
the same unconditional estimator the K cell already uses, taken at the boundary
the scalar itself governs.

**Zero LP. Reads committed artifacts and the measured EIA-930 parquet only.**
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402
from market_sim.model.interchange.spec import (  # noqa: E402
    EXTERNAL_SIMULTANEOUS_LIMITS,
    MISO_SEAM_DIBA,
)

T = 8760
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
BUNDLES = {
    2020: "miso251_tp2020",
    2021: "miso251_tp2021",
    2022: "miso251_screen2022",
    2023: "miso_fuelvintage_A",
    2024: "miso_fuelvintage_A",
    2025: "miso_fuelvintage_A",
}
CIL = EXTERNAL_SIMULTANEOUS_LIMITS["MISO"][1]


def _month_index() -> np.ndarray:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:T]


def coincident_envelope(
    year: int, direction: str, percentile: float | None = None
) -> np.ndarray:
    """Per-(month x hod) percentile of the MEASURED coincident boundary flow, MW.

    Same estimator, same percentile, same hour-ending key as the armed per-seam
    envelope; the aggregation is coincident (sum first, percentile second).
    """
    pct = MISO_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)
    path = RAW_DIR / "eia-930-interchange" / "MISO interchange hourly.parquet"
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"]) - pd.Timedelta(hours=1)
    keep = local.year == year
    frame, local = frame[keep], local[keep]
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    seam = frame["diba"].astype(str).map(diba_to_seam)
    work = pd.DataFrame(
        {
            "seam": seam.to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["seam", "mw"])
    # BOUNDARY total per timestamp: net import = -sum(interchange) over every
    # seam's DIBAs at that timestamp — the quantity the SIL itself governs.
    per_ts = work.groupby(["ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")
    tab = np.full((12, 24), np.nan)
    for (m, h), g in per_ts.groupby(["month", "hod"], observed=True):
        vals = g["net_import"].to_numpy()
        if direction == "export":
            vals = -vals
        tab[m - 1, h] = np.percentile(vals, pct)
    for m in range(12):
        row = tab[m]
        if not np.all(np.isnan(row)):
            tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
    if np.any(np.isnan(tab)):
        tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
    tab = np.clip(tab, 0.0, None)
    mo, hod = _month_index(), np.arange(T) % 24
    return tab[mo - 1, hod]


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
    print("=" * 100)
    print(f"COINCIDENT boundary envelope at p{MISO_SEAM_FLOW_PERCENTILE:g} vs the "
          f"{CIL:.0f} MW bidirectional planning scalar")
    print("=" * 100)
    print(
        f"{'yr':>6s}{'imp env mean':>14s}{'imp env max':>13s}{'exp env mean':>14s}"
        f"{'exp env max':>13s}{'h imp<CIL':>11s}{'h exp<CIL':>11s}"
        f"{'imp TWh ceil':>14s}"
    )
    env = {}
    for y in YEARS:
        ei = coincident_envelope(y, "import")
        ee = coincident_envelope(y, "export")
        env[y] = (ei, ee)
        print(
            f"{y:>6d}{ei.mean():>14.1f}{ei.max():>13.1f}{ee.mean():>14.1f}"
            f"{ee.max():>13.1f}{int((ei < CIL).sum()):>11d}"
            f"{int((ee < CIL).sum()):>11d}{ei.sum() / 1e6:>14.2f}"
        )

    print("\nFOOTPRINT — hours the model's OWN solved import violates the new envelope")
    print("(the pre-solve delta: where the arm would bite, and by how much)")
    print(
        f"{'yr':>6s}{'model TWh':>11s}{'h over imp env':>16s}{'h over exp env':>16s}"
        f"{'excess TWh':>12s}{'CIL rail h':>12s}"
    )
    for y in YEARS:
        m = model_import(y)
        ei, ee = env[y]
        over_i = np.clip(m - ei, 0.0, None)
        over_e = np.clip(-m - ee, 0.0, None)
        print(
            f"{y:>6d}{m.sum() / 1e6:>11.2f}{int((over_i > 0).sum()):>16d}"
            f"{int((over_e > 0).sum()):>16d}"
            f"{(over_i.sum() + over_e.sum()) / 1e6:>12.2f}"
            f"{int((np.abs(m) >= CIL - 1.0).sum()):>12d}"
        )

    print("\nPIN TEST — is the envelope a CEILING the measured flow clears below,")
    print("or is it the flow itself? (measured/envelope by decile of the envelope)")
    print(f"{'yr':>6s}" + "".join(f"{'D' + str(k + 1):>8s}" for k in range(10)))
    for y in YEARS:
        ei, _ = env[y]
        meas = -np.asarray(load_eia_hourly_benchmark("MISO", y)["interchange"], float)[:T]
        q = np.quantile(ei, np.linspace(0, 1, 11))
        q[0] -= 1.0
        dec = np.clip(np.searchsorted(q, ei, side="left") - 1, 0, 9)
        print(
            f"{y:>6d}"
            + "".join(
                f"{np.nanmean(meas[dec == k] / ei[dec == k]):>8.3f}" for k in range(10)
            )
        )

    print("\nHEADROOM — the envelope against the measured flow it is built from")
    print(
        f"{'yr':>6s}{'meas mean':>11s}{'env mean':>11s}{'headroom':>11s}"
        f"{'meas h>env':>12s}{'% of year':>11s}"
    )
    for y in YEARS:
        ei, _ = env[y]
        meas = -np.asarray(load_eia_hourly_benchmark("MISO", y)["interchange"], float)[:T]
        print(
            f"{y:>6d}{meas.mean():>11.1f}{ei.mean():>11.1f}"
            f"{ei.mean() - meas.mean():>11.1f}{int((meas > ei).sum()):>12d}"
            f"{100.0 * (meas > ei).mean():>10.1f}%"
        )


if __name__ == "__main__":
    main()
