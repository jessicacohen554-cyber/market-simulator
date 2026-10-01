"""PJM-NEXT-8 card 1 zero-LP phase 0: which CC_REGULAR plants carry 2023's surplus, and why.

Rule 32 ``[R-SHARD]`` (a): no LP. For each year a ``fleet_only`` rebuild of the
keeper recipe (``pjmnext7_vs_span`` via ``replay_keeper.run_year_kwargs``)
supplies the per-unit delivered ``fuel_prices``, ``heat_rate``, ``mc_base`` and
``availability`` the LP solved on. Joined per plant to the registered payload
(model MWh) and the bench (EIA-923 annual, CAMPD hourly), it prints per plant
and per zone: model vs EIA-923 energy, the cap-weighted delivered gas price and
mc_base, and availability, so the 2023 surplus can be attributed to a measured
input (fuel, heat rate, outage) or to dispatch.

Run: ``uv run python scripts/probes/_pjmnext8_cc2023_phase0.py 2023 2024``
Writes ``results/phase0/pjm/_pjmnext8_cc2023_phase0.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext7_vs_span"
RUN_JS = REPO / "frontend/data/backcast/runs/2026-09-28-pjm-next-7-virtual.js"
KLASS = "CC_REGULAR"


def load_payload() -> dict:
    """Decode the registered keeper run payload."""
    s = RUN_JS.read_text()
    b64 = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b64)))["years"]


def main() -> None:
    """Rebuild the fleet per year and print the per-plant CC table."""
    logging.disable(logging.CRITICAL)
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    pay = load_payload()
    out: dict = {"bundle": BUNDLE.name, "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or [2023, 2024]:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = (
            False  # demand-side overlay, inert for offers (pjm-h8 §2)
        )
        r = run_year(
            y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
        fa = r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        mc = np.asarray(r["mc_base"], float)
        T = mc.shape[1]
        fuel = np.asarray(r["fuel_prices"], float)
        if fuel.ndim == 1:
            fuel = fuel[:, None] * np.ones((1, T))
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, T))
        pmax = np.asarray(fa.pmax, float)
        cls = np.asarray(fa.plant_group).astype(str)
        pc = np.asarray(fa.plant_code).astype(str)
        hr = np.asarray(fa.heat_rate, float)
        bench = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/PJM/{y}.json.gz")
        )["bench"]["plants"]
        mp = pay[str(y)]["plants"]
        rows = []
        for k, b in bench.items():
            if b["group"] != KLASS or b.get("nodata") or k not in mp:
                continue
            code = k.split(":")[0]
            g = np.where((pc == code) & (cls == KLASS))[0]
            if not len(g):
                continue
            w = pmax[g][:, None] * avail[g]
            rows.append(
                {
                    "key": k,
                    "name": b["name"][:22],
                    "zone": zn[int(np.asarray(fa.zone_idx)[g[0]])],
                    "npl": b["npl"],
                    "model_twh": float(mp[k]["m_ann"]),
                    "e923_twh": float(b.get("e_ann") or 0),
                    "fuel": float((fuel[g] * w).sum() / w.sum()),
                    "hr": float((hr[g] * pmax[g]).sum() / pmax[g].sum()),
                    "mc": float((mc[g] * w).sum() / w.sum()),
                    "avail": float(w.sum() / (pmax[g].sum() * T)),
                    "pmax": float(pmax[g].sum()),
                }
            )
        out["years"][str(y)] = rows
        print(f"== {y}")
        zs: dict = {}
        for rw in rows:
            z = zs.setdefault(rw["zone"], [0, 0, 0, 0, 0])
            z[0] += rw["model_twh"]
            z[1] += rw["e923_twh"]
            z[2] += rw["fuel"] * rw["pmax"]
            z[3] += rw["mc"] * rw["pmax"]
            z[4] += rw["pmax"]
        for zname, z in sorted(zs.items(), key=lambda kv: kv[1][0] - kv[1][1]):
            print(
                f"  {zname:16s} model {z[0]:6.2f} e923 {z[1]:6.2f} d {z[0] - z[1]:+6.2f}  fuel {z[2] / z[4]:5.2f}  mc {z[3] / z[4]:6.2f}  GW {z[4] / 1e3:5.1f}"
            )
        for rw in sorted(rows, key=lambda r_: r_["model_twh"] - r_["e923_twh"]):
            print(
                f"  {rw['key']:18s} {rw['name']:22s} {rw['zone'][4:]:10s} d {rw['model_twh'] - rw['e923_twh']:+5.2f} "
                f"fuel {rw['fuel']:5.2f} hr {rw['hr']:6.0f} mc {rw['mc']:6.2f} av {rw['avail']:.2f}"
            )
    dest = REPO / "results/phase0/pjm/_pjmnext8_cc2023_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
