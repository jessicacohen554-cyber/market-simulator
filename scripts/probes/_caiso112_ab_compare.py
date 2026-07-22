"""caiso-112 A/B comparison: net import, belly export, and C-gate verdicts.

Usage: .venv/bin/python scripts/probes/_caiso112_ab_compare.py A_BUNDLE B_BUNDLE
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ACTUAL_NET_TWH = {2023: 28.9, 2024: 32.4, 2025: 36.2}  # from the finding/task
GAS_TARGET_TWH = {2023: 74.2, 2024: 61.0, 2025: 51.6}


def net_and_export(bundle: Path, year: int):
    dp = bundle / "dispatch" / f"{year}_P1.parquet"
    if not dp.exists():
        return None
    df = pd.read_parquet(dp)
    T = int(df["hour"].max()) + 1
    hod = np.arange(T) % 24
    belly = (hod >= 10) & (hod <= 15)
    wecc = df[df.unit_id.astype(str).str.startswith("WECC_")]
    net = wecc.groupby("hour")["mw"].sum().reindex(range(T)).fillna(0).to_numpy(float)
    exp = df[df.unit_id.astype(str).str.contains("export")]
    exp_h = exp.groupby("hour")["mw"].sum().reindex(range(T)).fillna(0).to_numpy(float)
    # gas TWh (CC/CT/ST classes)
    gasmask = df.klass.astype(str).str.contains("CC|CT|ST_GAS", regex=True)
    gas = df[gasmask].groupby("hour")["mw"].sum().reindex(range(T)).fillna(0).to_numpy(float)
    return {
        "net_twh": net.sum() / 1e6,
        "net_hours_export": int((net < 0).sum()),
        "belly_export_hrs": int((net[belly] < 0).sum()),
        "export_leg_twh": exp_h.sum() / 1e6,
        "gas_twh": gas.sum() / 1e6,
    }


def gates(bundle: Path):
    mp = bundle / "metrics.json"
    if not mp.exists():
        return None, None
    m = json.load(open(mp))
    crit = {k: v.get("status") for k, v in (m.get("criteria") or {}).items()}
    return m.get("determination"), crit


def main():
    A, B = Path(sys.argv[1]), Path(sys.argv[2])
    print(f"\n===== caiso-112 A/B: A={A.name} (flag off)  vs  B={B.name} (flag on) =====")
    for det_label, bundle in (("A", A), ("B", B)):
        d, c = gates(bundle)
        print(f"\n  {det_label} determination: {d}")
        if c:
            fails = [k for k, v in c.items() if v not in ("PASS", "N/A", None)]
            print(f"    criteria: {c}")
            print(f"    FAIL set: {fails}")
    print("\n  Per-year net import (TWh) / export hrs / belly-export hrs / export-leg TWh / gas TWh:")
    print(f"  {'year':6} {'actual_net':>10} | {'A_net':>7} {'A_expH':>6} {'A_bE':>5} {'A_gas':>7} | {'B_net':>7} {'B_expH':>6} {'B_bE':>5} {'B_gas':>7} {'gas_tgt':>7}")
    for y in (2023, 2024, 2025):
        a = net_and_export(A, y)
        b = net_and_export(B, y)
        if a is None or b is None:
            print(f"  {y}: A={'?' if a is None else 'ok'} B={'?' if b is None else 'ok'} (missing dispatch)")
            continue
        print(f"  {y:6} {ACTUAL_NET_TWH.get(y,0):10.1f} | "
              f"{a['net_twh']:7.1f} {a['net_hours_export']:6d} {a['belly_export_hrs']:5d} {a['gas_twh']:7.1f} | "
              f"{b['net_twh']:7.1f} {b['net_hours_export']:6d} {b['belly_export_hrs']:5d} {b['gas_twh']:7.1f} {GAS_TARGET_TWH.get(y,0):7.1f}")


if __name__ == "__main__":
    main()
