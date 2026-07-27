"""Compare the MODEL's CT_PEAKER run-length distribution against the measured one.

The characterization behind nyiso-90's block-commitment arm. nyiso-88 and
nyiso-89 closed price formation, non-energy obligations and the measured heat
rate as candidates for CT_PEAKER's 1.8-2.1 TWh level gap; what remains is the
observation that the real fleet RUNS MANY MORE HOURS than any hourly SRMC
screen implies — the ordinary signature of multi-hour day-ahead commitment.
This probe measures that directly, so the mechanism is judged against the RUN
LENGTH DISTRIBUTION rather than against the volume gap.

**Both sides are computed at PLANT level**, which is the only apples-to-apples
comparison available: the measured artifact counts physical CAMPD turbines,
while the model carries one LP row per plant TRANCHE (committed / econ / peak)
of the same iron. A plant is "online" in hour t when any of its tranches (model)
or any of its CT units (CAMPD) is loaded — the convention
``_pjm_plant_online_pattern`` already uses ("a plant is synchronized when any of
its tranches dispatch"). The same online threshold is applied to both sides:
``max(1.0 MW, 0.05 x plant capacity)``, the CAMPD ``_ONLINE_MW`` /
``_ONLINE_FRAC`` convention.

The per-tranche model distribution is reported too, because that is the object
the ``min_run_hours`` constraint is actually applied to.

Usage::

    python scripts/probes/nyiso90_ct_run_lengths.py \
        --bundle results/calibration/nyiso90_ctrl_zerodelta \
        [--arm results/calibration/nyiso90_ctblock_minrun]
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

from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

CT_UNIT_TYPE = "combustion turbine"
ONLINE_FRAC = 0.05
PCTILES = (10, 25, 50, 75, 90)


def run_lengths(on: np.ndarray) -> list[int]:
    """Return the lengths (hours) of maximal True-blocks in ``on``."""
    if not on.any():
        return []
    d = np.diff(np.concatenate([[0], on.astype(np.int8), [0]]))
    return (np.where(d == -1)[0] - np.where(d == 1)[0]).tolist()


def describe(name: str, runs: list[float], weights: list[float] | None = None) -> dict:
    """Return the summary row for a pooled run-length distribution."""
    a = np.asarray(runs, dtype=float)
    if a.size == 0:
        return {"series": name, "n_runs": 0}
    row = {
        "series": name,
        "n_runs": int(a.size),
        "mean": float(a.mean()),
        "hours_total": float(a.sum()),
        "frac_1h": float((a <= 1).mean()),
        "frac_le2h": float((a <= 2).mean()),
    }
    for p in PCTILES:
        row[f"p{p}"] = float(np.percentile(a, p))
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        order = np.argsort(a)
        cw = np.cumsum(w[order]) / w.sum()
        for p in PCTILES:
            row[f"p{p}_capwtd"] = float(a[order][np.searchsorted(cw, p / 100.0)])
    return row


def model_runs(bundle: Path, year: int) -> tuple[list[float], list[float], dict]:
    """Return ``(plant_runs, plant_weights, tranche_summary)`` for the bundle-year."""
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "unit_id", "plant_code", "klass", "hour", "mw"],
    )
    df = df[(df["klass"] == "CT_PEAKER") & (df["pass"] == "P1")]
    if df.empty:
        return [], [], {}

    # Per-tranche distribution (the object min_run_hours constrains).
    tr_runs: list[float] = []
    for _uid, g in df.groupby("unit_id", observed=True):
        mw = g.sort_values("hour")["mw"].to_numpy(dtype=float)
        cap = mw.max()
        if cap <= _ONLINE_MW:
            continue
        tr_runs.extend(run_lengths(mw >= max(_ONLINE_MW, ONLINE_FRAC * cap)))

    # Plant-level: any tranche loaded.
    plant = df.groupby(["plant_code", "hour"], observed=True)["mw"].sum().unstack("hour")
    runs: list[float] = []
    weights: list[float] = []
    for code, row in plant.iterrows():
        mw = row.to_numpy(dtype=float)
        cap = np.nanmax(mw)
        if not np.isfinite(cap) or cap <= _ONLINE_MW:
            continue
        rl = run_lengths(mw >= max(_ONLINE_MW, ONLINE_FRAC * cap))
        runs.extend(rl)
        weights.extend([cap] * len(rl))
    return runs, weights, describe(f"model tranche {year}", tr_runs)


def measured_runs(
    iso: str, year: int, codes: set[int]
) -> tuple[list[float], list[float]]:
    """Return ``(plant_runs, plant_weights)`` from CAMPD for the same plants."""
    frames = []
    for state in states_for_iso(iso):
        path = RAW_DIR / "campd-unit-level" / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        d = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "grossLoad",
                "unitType",
            ],
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["facilityId"].isin(codes)]
        d = d[d["unitType"].astype(str).str.strip().str.casefold() == CT_UNIT_TYPE]
        if not d.empty:
            frames.append(d)
    if not frames:
        return [], []
    d = pd.concat(frames, ignore_index=True).sort_values(
        ["facilityId", "date", "hour"]
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    plant = (
        d.groupby(["facilityId", "date", "hour"], observed=True)["grossLoad"]
        .sum()
        .reset_index()
        .sort_values(["facilityId", "date", "hour"])
    )
    runs: list[float] = []
    weights: list[float] = []
    for _code, g in plant.groupby("facilityId", observed=True):
        mw = g["grossLoad"].to_numpy(dtype=float)
        cap = float(np.percentile(mw, 99.5))
        if cap <= _ONLINE_MW:
            continue
        rl = run_lengths(mw >= max(_ONLINE_MW, ONLINE_FRAC * cap))
        runs.extend(rl)
        weights.extend([cap] * len(rl))
    return runs, weights


def main() -> None:
    """Print the model-vs-measured CT_PEAKER run-length comparison."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="control (or keeper) bundle dir")
    ap.add_argument("--arm", default=None, help="optional arm bundle to compare")
    ap.add_argument("--iso", default="NYISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    rows: list[dict] = []
    for year in args.years:
        ctrl = Path(args.bundle) / "dispatch" / f"{year}_P1.parquet"
        if not ctrl.exists():
            print(f"  (skip {year}: {ctrl} not on disk)")
            continue
        c_runs, c_w, c_tr = model_runs(Path(args.bundle), year)
        codes = set(
            pd.read_parquet(ctrl, columns=["klass", "plant_code"])
            .query("klass == 'CT_PEAKER'")["plant_code"]
            .unique()
            .tolist()
        )
        m_runs, m_w = measured_runs(args.iso, year, codes)
        rows.append(describe(f"MEASURED plant {year}", m_runs, m_w))
        rows.append(describe(f"control  plant {year}", c_runs, c_w))
        if args.arm:
            a_runs, a_w, a_tr = model_runs(Path(args.arm), year)
            rows.append(describe(f"ARM      plant {year}", a_runs, a_w))
        if c_tr:
            rows.append(c_tr)
        if args.arm and a_tr:
            rows.append(a_tr)

    out = pd.DataFrame(rows)
    cols = [
        "series",
        "n_runs",
        "mean",
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "frac_1h",
        "frac_le2h",
        "hours_total",
    ]
    cols = [c for c in cols if c in out.columns]
    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(out[cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
