"""miso-265 — WHICH plants the full-derate zeroing selects, and on what property. ZERO LP.

:mod:`scripts.probes._miso265_hard_zero_hours` shows that 33 MISO coal plants are
driven to ``availability == 0`` in hours their own meter says they ran, and that
the unit-outage derate alone produces it. This script asks the next question: what
distinguishes those 33 from the coal plants that are clean?

Two candidate properties are measured side by side, because the obvious one is not
the answer:

* **the capacity basis** — the extract's ``plant_capacity_mw`` over the LP's own
  coal capacity for that plant. The accumulator's docstring names this failure
  mode explicitly (*"sum to 1.23 of the modeled OP half and clip it to 0.0"*), and
  at R M Schahfer the ratio really is 1.236;
* **window mass** — the sum of ``unit_pct_of_plant`` over every window the year's
  extract carries for the plant. A plant's units can only sum to 100 % at any one
  instant, so a large annual sum means many separate detected windows per unit,
  i.e. a heavily cycled plant.

Measured on MISO 2020, the capacity ratio is ~1.06–1.10 in BOTH groups and the
window mass differs by more than 2x, so the selection is by window mass. The
script prints both so the conclusion is checkable rather than asserted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.probes._miso265_ceiling_vs_meter_hourly import decode_plant_mw  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _assert_partition_leg,
    load_bench,
)

#: The extract the keeper actually reads (``unit_outage_mixed_gas_routing=True``).
DEFAULT_EXTRACT = "data/raw/campd-unit-outages-unitroute-MISO.csv"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--extract", default=DEFAULT_EXTRACT)
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    bundle = REPO / args.bundle
    _assert_partition_leg(json.loads((bundle / "meta.json").read_text()), args.year)
    state, _ = reconstruct_bundle_fleet(bundle, args.year, verbose=False)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    lp_cap: dict[str, float] = {}
    ceil: dict[str, np.ndarray] = {}
    for i in np.nonzero(is_coal)[0]:
        c = str(codes[i])
        lp_cap[c] = lp_cap.get(c, 0.0) + pmax[i]
        ceil[c] = ceil.get(c, np.zeros(avail.shape[1])) + pmax[i] * avail[i]

    ext = pd.read_csv(REPO / args.extract)
    ext["outage_start"] = pd.to_datetime(ext["outage_start"])
    ext["outage_end"] = pd.to_datetime(ext["outage_end"])
    ext = ext[
        (ext["outage_start"] < f"{args.year + 1}-01-01")
        & (ext["outage_end"] >= f"{args.year}-01-01")
    ]
    ext = ext[ext["plant_group"].astype(str).str.upper().str.contains("COAL")]
    ext_cap = ext.groupby("facility_id")["plant_capacity_mw"].max()
    win_mass = ext.groupby("facility_id")["unit_pct_of_plant"].sum()
    n_win = ext.groupby("facility_id").size()

    bench = load_bench(args.iso, args.year)
    rows = []
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        if base not in ceil:
            continue
        meter = decode_plant_mw(rec, key)
        if meter is None:
            continue
        c = ceil[base]
        n = min(len(c), len(meter))
        step = float(rec.get("npl") or 0.0) / 100.0
        contra = int(((c[:n] <= 1e-9) & (meter[:n] > step)).sum())
        fid = int(base)
        rows.append(
            {
                "name": rec.get("name", "?")[:24],
                "lp_mw": lp_cap[base],
                "ext_mw": float(ext_cap.get(fid, np.nan)),
                "win_mass": float(win_mass.get(fid, np.nan)),
                "n_win": int(n_win.get(fid, 0)),
                "contra_h": contra,
            }
        )
    df = pd.DataFrame(rows).dropna(subset=["ext_mw"])
    df["ratio"] = df["ext_mw"] / df["lp_mw"]
    bad = df[df.contra_h > 0].sort_values("contra_h", ascending=False)
    good = df[df.contra_h == 0]

    fmt = lambda x: f"{x:8.3f}"  # noqa: E731
    print(f"=== {args.iso} {args.year} — what selects the zeroed plants (ZERO LP) ===")
    print(f"extract: {args.extract}")
    print()
    print(f"--- CONTRADICTED (n={len(bad)}) ---")
    print(bad.head(args.top).to_string(index=False, float_format=fmt))
    print()
    print(f"--- CLEAN (n={len(good)}) ---")
    print(good.head(args.top).to_string(index=False, float_format=fmt))
    print()
    print("MEDIANS                       contradicted     clean")
    print(f"  extract MW / LP coal MW  {bad.ratio.median():14.3f} {good.ratio.median():9.3f}")
    print(f"  summed unit_pct_of_plant {bad.win_mass.median():14.1f} {good.win_mass.median():9.1f}")
    print(f"  window count             {bad.n_win.median():14.1f} {good.n_win.median():9.1f}")
    print()
    print("  The capacity ratio is a systematic ~6-10% share inflation present in BOTH")
    print("  groups. WINDOW MASS is what separates them — many detected windows per unit,")
    print("  the signature of a cycled plant, summing past a full-derate clip.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
