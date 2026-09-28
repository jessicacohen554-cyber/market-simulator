"""R-CAISO-11 (ZERO LP): pumped storage at the EIA-930 ``NG: WAT`` boundary.

EIA-930 CISO ``NG: WAT`` FOLDS pumped storage (net: discharge adds, pumping
subtracts; constants carry no CISO PS split). The keeper caps the conventional
hydro fleet alone at a percentile of that folded series
(``measured_hydro_hourly_envelope``) and carries pumped storage as a separate,
unrestrained storage column. This probe measures, on the keeper's own per-year
legs, what that boundary mismatch does:

1. like-for-like level: model (conventional hydro + PS net) vs EIA-930 WAT by
   window (midday h8-16, evening h17-22);
2. how often the conventional fleet sits AT the WAT envelope, and by how much
   conventional + PS discharge - PS charge would exceed the same envelope --
   the footprint of applying the existing cap on the measured object's own
   boundary (no split of WAT, no PS proxy, no new parameter).

Legs are extracted from the R-CAISO-10 shard commits (gitignored; rule 31).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso11_ps_boundary_footprint.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia930.envelopes import measured_hydro_hourly_envelope
from market_sim.data.eia930.frames import _eia_hourly_frame_filled

LEG = "results/calibration/rcaiso10_A_{y}"
OUT = Path("results/calibration/_rcaiso11/ps_boundary_footprint.json")
T = 8760
HOD = np.arange(T) % 24
WIN = {"mid_h8_16": (HOD >= 8) & (HOD <= 16), "eve_h17_22": (HOD >= 17) & (HOD <= 22)}
ON = 1.0  # MW tolerance for "at the envelope"


def footprint(y: int) -> dict:
    """Boundary census for one year."""
    leg = Path(LEG.format(y=y))
    c = pd.read_parquet(leg / f"hourly/class_hourly_{y}.parquet")
    hyd = c[c.klass == "hydro"].groupby("hour").mw.sum().reindex(range(T)).to_numpy()
    st = pd.read_parquet(leg / f"hourly/storage_{y}.parquet")
    ps = st[st.tech == "pumped_storage"].set_index("hour").reindex(range(T))
    dis, chg = ps.discharge_mw.to_numpy(), ps.charge_mw.to_numpy()
    env = measured_hydro_hourly_envelope("CAISO", y, T)
    frame = _eia_hourly_frame_filled("CISO", y)
    wat = frame["NG: WAT"].to_numpy(dtype=float)[:T] if frame is not None else np.full(T, np.nan)
    ok = np.isfinite(wat)
    joint = hyd + dis - chg
    out: dict = {"wat_rows_finite": int(ok.sum())}
    for k, w in WIN.items():
        m = w & ok
        out[k] = {
            "model_conv_mw": round(float(hyd[m].mean())),
            "model_ps_net_mw": round(float((dis - chg)[m].mean())),
            "model_joint_mw": round(float(joint[m].mean())),
            "eia930_wat_mw": round(float(wat[m].mean())),
            "joint_minus_wat_mw": round(float((joint - wat)[m].mean())),
        }
        if env is not None:
            e = env[w]
            at = hyd[w] >= e - ON
            over = np.maximum(joint[w] - e, 0.0)
            out[k] |= {
                "conv_at_envelope_share": round(float(at.mean()), 3),
                "joint_over_envelope_share": round(float((over > ON).mean()), 3),
                "joint_over_envelope_mean_mw_when_over": round(float(over[over > ON].mean()) if (over > ON).any() else 0.0),
                "joint_over_envelope_mean_mw_all": round(float(over.mean())),
            }
    return out


def main() -> None:
    """Run 2019-2025 and write the JSON."""
    res = {str(y): footprint(y) for y in range(2019, 2026)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
