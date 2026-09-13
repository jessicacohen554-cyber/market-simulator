"""pjm-h5 task 2 (ZERO LP): quantify the bituminous sigmoid's `gas_mid` mis-grounding.

`derive_coal_sigmoid.py` constructs the coal-vs-gas-CC merit crossover as

    deliv    = ACR regional f.o.b. / COAL_DELIVERY_COMMODITY_SHARE[supply]
    gas_mid  = deliv * COAL_HR / CC_HR

so `gas_mid` is grounded in an ANNUAL regional f.o.b. commodity price, while the
model's own committed coal tranches are priced off MEASURED per-plant EIA-923
monthly receipts. pjm-170 §2.1 measured the gap and left it open. This probe
re-measures it at HEAD and prices what it is worth on the passthrough, at each of
the three candidate centres:

* **3.40** — the LIVE registered value (`COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]`)
* **4.58** — the MODEL-CONSISTENT crossover, from the model's own delivered coal
* **7.08** — what `derive_coal_sigmoid.py` ITSELF produces at HEAD (h2b §1.1)

Run: ``python3 scripts/probes/_pjm_h5_gasmid.py 2020 2021 ...``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}
CANDIDATES = {
    "live 3.40": 3.40,
    "model-consistent 4.58": 4.58,
    "derive-at-HEAD 7.08": 7.08,
}


def main() -> None:
    from market_sim.data.fuel.trajectories import (
        _gas_series,
        _sigmoid_passthrough,
        coal_sigmoid_params,
    )
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    years = [int(a) for a in sys.argv[1:]] or [2020]
    rows = []
    for y in years:
        bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[y]
        meta = json.loads((bundle / "meta.json").read_text())
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(bundle, y))
        kw["pjm_da_virtual_bids"] = False
        out = run_year(
            y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
        cfg = out["config"]
        p = coal_sigmoid_params(cfg, "bituminous")
        gas = np.asarray(_gas_series(cfg, y, 8760), dtype=float)
        row = {"year": y, "gas_mean": float(gas.mean()), "params": dict(p)}
        for name, gm in CANDIDATES.items():
            pt = _sigmoid_passthrough(gas, p["floor"], p["ceil"], gm, p["gas_slope"])
            row[name] = float(np.mean(pt))
        rows.append(row)
        print(
            f"{y}: gas mean {gas.mean():.3f} $/MMBtu  params "
            f"floor={p['floor']} ceil={p['ceil']} gas_mid={p['gas_mid']} "
            f"slope={p['gas_slope']}"
        )

    print("\n" + "=" * 78)
    print("MEAN BITUMINOUS PASSTHROUGH under each candidate gas_mid")
    print("=" * 78)
    hdr = f"{'yr':<6}{'gas $/MMBtu':>13}"
    for name in CANDIDATES:
        hdr += f"{name:>24}"
    print(hdr)
    for r in rows:
        line = f"{r['year']:<6}{r['gas_mean']:>13.3f}"
        for name in CANDIDATES:
            line += f"{r[name]:>24.4f}"
        print(line)

    print(
        "\nREAD: the live centre 3.40 sits BELOW both defensible crossovers, so the\n"
        "curve rises EARLY in gas-price space — coal's committed block is marked\n"
        "toward `ceil` in years the model's own fuel prices say it should still be\n"
        "near `floor`. Worth the column spread above, per year, on 12.55 GW."
    )
    out_p = REPO / "results/calibration/_pjm_h5_gasmid.json"
    out_p.write_text(json.dumps(rows, indent=2))
    print(f"\nwrote {out_p}")


if __name__ == "__main__":
    main()
