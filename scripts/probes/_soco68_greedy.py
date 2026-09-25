"""soco-68 greedy restack (ZERO LP): what does the arm's added CC availability displace?

Reads the keeper's committed ``class_band_hourly_<y>`` (soco67_span) and the
control/arm fleet rebuilds written by ``_soco68_cc_capability.py``
(``fleet_<y>_{ctl,arm}.npz``). In every hour where keeper CC_REGULAR sits at its
control ceiling (dispatch >= 0.99 x ctl availability), CC gains up to
``arm - ctl`` availability and displaces the running (class, band) blocks whose
capacity-weighted hourly mc exceeds CC's, highest mc first -- the soco-67
FINDING §4 construction. Committed / must-run bands are never displaced. CT
availability gains are reported (hours CT sits at its own ceiling) but not
restacked. An estimate only: it ignores commitment, ramping and transmission.

Usage::

    .venv/bin/python scripts/probes/_soco68_greedy.py --cap-dir <dir> --years 2019 ... 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/soco67_span"
T = 8760
NEVER = ("committed", "mustrun", "must_run")
DISPLACEABLE = (
    "CT_PEAKER",
    "ST_GAS",
    "oil",
    "CT_CHP",
    "COAL_BIT",
    "COAL_PRB",
    "ST_CHP",
)


def band_of(uid: str) -> str:
    """The tranche suffix of a fleet unit id (``..._econlo`` -> ``econlo``)."""
    return uid.rsplit("_", 1)[-1]


def main() -> None:
    """Greedy restack per year; prints class deltas (TWh)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cap-dir", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024])
    a = ap.parse_args()
    for y in a.years:
        c = np.load(a.cap_dir / f"fleet_{y}_ctl.npz")
        r = np.load(a.cap_dir / f"fleet_{y}_arm.npz")
        assert (c["unit_ids"] == r["unit_ids"]).all()
        cls, uid = c["cls"], c["unit_ids"]
        dav = r["avail"].astype(float) - c["avail"].astype(float)
        moved = np.abs(dav).sum(axis=1) > 1e-3
        by_cls = pd.Series(dav.sum(axis=1) / 1e6, index=cls).groupby(level=0).sum()
        print(
            f"\n=== {y}: arm - ctl availability TWh by class:",
            {k: round(v, 3) for k, v in by_cls.items() if abs(v) > 1e-4},
            f"| units moved {int(moved.sum())}; other columns identical:",
            bool(
                np.array_equal(c["pmax"], r["pmax"])
                and np.array_equal(c["mc"], r["mc"])
            ),
        )
        bh = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{y}.parquet")
        bh = bh[bh["pass"] == "P1"]
        disp = {
            (k, b): g.sort_values("hour").mw.to_numpy()
            for (k, b), g in bh.groupby(["klass", "band"], observed=True)
        }
        # capacity-weighted hourly mc per (class, band)
        mc = c["mc"].astype(float)
        if mc.ndim == 1:
            mc = np.repeat(mc[:, None], T, axis=1)
        bands = np.array([band_of(u) for u in uid])
        cb_mc = {}
        for k in set(cls):
            for b in set(bands[cls == k]):
                ii = np.where((cls == k) & (bands == b))[0]
                w = c["pmax"][ii]
                cb_mc[(k, b)] = (mc[ii] * w[:, None]).sum(0) / max(w.sum(), 1e-9)
        cc_i = np.where(cls == "CC_REGULAR")[0]
        cc_ctl = c["avail"][cc_i].astype(float).sum(0)
        cc_arm = r["avail"][cc_i].astype(float).sum(0)
        cc_d = sum(v for (k, b), v in disp.items() if k == "CC_REGULAR")
        cc_mc = (mc[cc_i] * c["pmax"][cc_i][:, None]).sum(0) / c["pmax"][cc_i].sum()
        pinned = cc_d >= 0.99 * cc_ctl
        room = np.where(pinned, np.maximum(0.0, cc_arm - cc_ctl), 0.0)
        cands = [(k, b) for (k, b) in disp if k in DISPLACEABLE and b not in NEVER]
        delta = {k: 0.0 for k in set(cls)}
        gain = np.zeros(T)
        for t in np.where(room > 0)[0]:
            left = room[t]
            order = sorted(cands, key=lambda kb: -cb_mc.get(kb, np.zeros(T))[t])
            for kb in order:
                if left <= 0:
                    break
                if cb_mc.get(kb, np.zeros(T))[t] <= cc_mc[t]:
                    continue
                take = min(left, disp[kb][t])
                if take > 0:
                    delta[kb[0]] -= take
                    left -= take
                    gain[t] += take
        delta["CC_REGULAR"] += gain.sum()
        ct_i = np.where(cls == "CT_PEAKER")[0]
        ct_d = sum(v for (k, b), v in disp.items() if k == "CT_PEAKER")
        ct_pin = int((ct_d >= 0.99 * c["avail"][ct_i].astype(float).sum(0)).sum())
        print(
            f"  CC pinned hours {int(pinned.sum())}; hours with room {int((room > 0).sum())}; "
            f"room TWh {room.sum() / 1e6:.3f}; CT-at-ceiling hours {ct_pin}"
        )
        print(
            "  greedy class delta TWh:",
            {k: round(v / 1e6, 3) for k, v in delta.items() if abs(v) > 1e3},
        )


if __name__ == "__main__":
    main()
