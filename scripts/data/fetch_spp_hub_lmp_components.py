"""Fetch SPP hub LMP *components* (energy / congestion / loss), hourly, 2019-2025.

Lane SPP-80 (``docs/handoffs/CHARTER-spp-80-upper-tercile-premium-intake-2026-09-25.md``).
The committed hub sidecars (``actual_lmp_hourly{,_zonal}_SPP.parquet``) keep only
``Price Type == LMP``. SPP's monthly wide settlement-location files carry two more
price types for every hub, ``MCC`` (marginal congestion component) and ``MLC``
(marginal loss component); the marginal energy component is the identity
``MEC = LMP - MCC - MLC`` (SPP publishes LMP as the sum of the three). That split
is what separates *internal congestion* from *system energy price* in the
upper-tercile premium SPP-79 left unmeasured.

Everything below reuses ``build_spp_lmp_reference.py`` unmodified: the same
monthly source files (``{DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv``), the same
archive fall-back, the same Date parser, the same non-leap 8760 calendar and the
SAME GMT -> fixed-CST re-index (:func:`gmt_dense_to_model_clock`, SPP-51c). The
only difference is that all three price types are kept instead of LMP alone, so
the emitted ``lmp`` column reproduces the committed zonal sidecar's ``rt``/``da``
(checked by ``--verify`` against it).

Output: ``data/raw/_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet``,
long form: ``year`` int16, ``hour`` int16 (0..8759, model clock), ``zone``
(SPP settlement-location name, as in the zonal sidecar), ``market`` (``rt``/``da``),
``lmp``/``mcc``/``mlc``/``mec`` float32 ($/MWh).

Usage:
    python scripts/data/fetch_spp_hub_lmp_components.py [--years 2019 ... 2025] [--verify]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_spp_lmp_reference as ref  # noqa: E402  (the unmodified SPP builder)
from market_sim.config import paths  # noqa: E402

PRICE_TYPES = ("LMP", "MCC", "MLC")  # as published by SPP; MEC is derived
MARKETS = {"rt": (ref.FS_RT, "RTBM-LMP"), "da": (ref.FS_DA, "DA-LMP")}
OUT_NAME = "actual_lmp_components_hourly_zonal_SPP.parquet"


def _hub_rows(bytes_by_month: dict[int, bytes]) -> pd.DataFrame:
    """Hub rows of every published price type from a year's monthly wide files."""
    frames = []
    for data in bytes_by_month.values():
        df = pd.read_csv(io.BytesIO(data), skipinitialspace=True)
        df.columns = [c.strip() for c in df.columns]
        frames.append(
            df[
                df["Settlement Location Name"].isin(ref.HUBS)
                & df["Price Type"].isin(PRICE_TYPES)
            ]
        )
    return pd.concat(frames, ignore_index=True)


def fetch(years: list[int]) -> pd.DataFrame:
    """Return the long component frame for ``years`` on the model clock."""
    # GMT-clock dense arrays keyed [market][ptype][hub][year]
    gmt: dict = {}
    for mkt, (fs, prefix) in MARKETS.items():
        for year in years:
            rows = _hub_rows(ref._monthly_bytes(fs, prefix, year))
            for pt in PRICE_TYPES:
                for hub in ref.HUBS:
                    sub = rows[
                        (rows["Price Type"] == pt)
                        & (rows["Settlement Location Name"] == hub)
                    ]
                    dense = (
                        ref._dense_from_daily(
                            sub.groupby("Date")[ref.HE_COLS].mean(), year
                        )
                        if len(sub)
                        else np.full(ref._HOURS_PER_YEAR, np.nan)
                    )
                    gmt.setdefault(mkt, {}).setdefault(pt, {}).setdefault(hub, {})[
                        year
                    ] = dense
            print(f"  fetched {mkt} {year}", flush=True)
    frames = []
    for mkt in MARKETS:
        model = {
            pt: {
                hub: ref.gmt_dense_to_model_clock(gmt[mkt][pt][hub]) for hub in ref.HUBS
            }
            for pt in PRICE_TYPES
        }
        for year in years:
            for hub in ref.HUBS:
                lmp = model["LMP"][hub][year]
                mcc = model["MCC"][hub][year]
                mlc = model["MLC"][hub][year]
                frames.append(
                    pd.DataFrame(
                        {
                            "year": np.int16(year),
                            "hour": np.arange(ref._HOURS_PER_YEAR, dtype=np.int16),
                            "zone": hub,
                            "market": mkt,
                            "lmp": lmp.astype(np.float32),
                            "mcc": mcc.astype(np.float32),
                            "mlc": mlc.astype(np.float32),
                            "mec": (lmp - mcc - mlc).astype(np.float32),
                        }
                    )
                )
    return pd.concat(frames, ignore_index=True)


def verify(frame: pd.DataFrame) -> float:
    """Max |lmp - committed zonal sidecar| over shared non-NaN cells (should be 0)."""
    ref_df = pd.read_parquet(
        paths.CALIBRATION_DIR / "actual_lmp_hourly_zonal_SPP.parquet"
    )
    worst = 0.0
    for mkt in MARKETS:
        a = frame[frame.market == mkt].merge(ref_df, on=["year", "hour", "zone"])
        d = (a["lmp"] - a[mkt]).abs().dropna()
        worst = max(worst, float(d.max()) if len(d) else 0.0)
    return worst


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", type=Path, default=paths.CALIBRATION_DIR / OUT_NAME)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    frame = fetch(args.years)
    if args.verify:
        print(f"  max |lmp - committed zonal sidecar| = {verify(frame):.6f} $/MWh")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(args.out, index=False)
    print(f"wrote {args.out} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
