"""NWPP-NEXT-28 zero-LP phase 0: can BA reserve holding (BAL-002-WECC) explain the SNV/EAST CC loading gap?

Reads only committed artifacts — no LP, no fleet build:
  - keeper bundle results/calibration/nwppnext27_span/hourly/unit_marginal_<Y>.parquet (per-unit P1 mw / cap_mw)
  - EIA-930 hourly per BA (data/raw/eia-930-hourly/<BA> hourly.parquet): Demand, Net generation
  - the NWPP bench frontend/data/backcast/bench/NWPP/<Y>.json.gz (CAMPD hourly CF per plant)

Per zone (SNV = NEVP, EAST = PACE) and year it compares:
  - the BAL-002-WECC-2a contingency floor 3 % load + 3 % net generation (half spinning), per BA, hourly;
  - the model's existing online thermal headroom in the zone (cap - mw on units with mw > 1 MW);
  - the CC loading the requirement would displace if held on the zone's own online units
    (sum over hours of max(0, spin_req - model_headroom)), against the CC loading excess vs CAMPD;
  - the measured CAMPD online headroom at the zone's CCs, against the requirement.
Writes results/phase0/nwpp/_nwppnext28_reserve_headroom.json. Record: docs/records/nwpp/FINDING-nwppnext28-*.md.
"""

from __future__ import annotations

import base64
import gzip
import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

BUNDLE = REPO_ROOT / "results/calibration/nwppnext27_span/hourly"
EIA = REPO_ROOT / "data/raw/eia-930-hourly"
ZONE_BA = {
    "NWPP-NW": ("BPAT", "PSEI", "SCL", "TPWR", "CHPD", "DOPD", "GCPD", "AVRN"),
    "NWPP-OR": ("PGE", "PACW", "GRID"),
    "NWPP-INLAND": ("IPCO", "AVA", "NWMT", "WAUW"),
    "NWPP-EAST": ("PACE",),
    "NWPP-SNV": ("NEVP",),
}  # zone_assignment._NWPP_BA_ZONES
CONT_FRAC = 0.03  # BAL-002-WECC-2a R1: 3 % of load + 3 % of net generation
SPIN_SHARE = 0.5  # BAL-002-WECC-2a R1.1: at least half spinning
OFF_PCT = 5.0  # CAMPD hour counted "off" below 5 % of nameplate


def ba_hourly(ba: str, year: int) -> pd.DataFrame:
    """EIA-930 demand / net generation for one BA, Pacific-local year, 8760 rows."""
    d = pd.read_parquet(EIA / f"{ba} hourly.parquet")
    t = pd.to_datetime(d["UTC time"]) - pd.Timedelta(hours=8)
    d = d[t.dt.year == year].copy()
    d = d[["Demand (Adjusted)", "Net generation (Adjusted)"]].astype(float)
    d = d.iloc[:8760].reset_index(drop=True)
    return d.reindex(range(8760)).ffill().bfill()


def decode(b64: str) -> np.ndarray:
    """Decode a bench CAMPD CF series (uint8 percent of nameplate)."""
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def zone_year(zone: str, year: int, um: pd.DataFrame, bench: dict) -> dict:
    """Requirement vs model headroom vs CC loading gap for one zone-year."""
    req = np.zeros(8760)
    for code in ZONE_BA[zone]:  # BAL-002-WECC is a per-BA obligation: sum the members' own requirements
        ba = ba_hourly(code, year).fillna(0.0)
        req += CONT_FRAC * (ba.iloc[:, 0].clip(lower=0) + ba.iloc[:, 1].clip(lower=0)).to_numpy()
    spin = SPIN_SHARE * req
    z = um[(um["zone"] == zone) & (~um["fuel"].isin(["", "import"]))]  # hydro holds spinning reserve too
    on = z[z["mw"] > 1.0]
    head = (
        (on["cap_mw"] - on["mw"]).groupby(on["hour"]).sum().reindex(range(8760), fill_value=0).to_numpy()
    )
    cc = z[z["plant_group"] == "CC_REGULAR"]
    excess = np.zeros(8760)
    meas_head = np.zeros(8760)
    for code, g in cc.groupby("plant_code", observed=True):
        mw = g.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0).to_numpy(float)
        cap = g.groupby("hour")["cap_mw"].sum().reindex(range(8760), fill_value=0).to_numpy(float)
        b = bench.get(str(code)) or bench.get(f"{code}|CC_REGULAR")
        if b is None:
            continue
        cf = decode(b["campd"])[:8760]
        act = cf / 100.0 * b["npl"]
        both = (mw > 1.0) & (cf >= OFF_PCT)
        excess += np.where(both, mw - act, 0.0)
        meas_head += np.where(cf >= OFF_PCT, np.clip(cap - act, 0, None), 0.0)
    disp_spin = np.clip(spin - head, 0, None)
    disp_full = np.clip(req - head, 0, None)
    return {
        "bas": list(ZONE_BA[zone]),
        "req_mean_mw": round(float(req.mean()), 1),
        "req_p95_mw": round(float(np.percentile(req, 95)), 1),
        "spin_mean_mw": round(float(spin.mean()), 1),
        "model_online_headroom_mean_mw": round(float(head.mean()), 1),
        "hours_headroom_below_spin": int((head < spin).sum()),
        "hours_headroom_below_full": int((head < req).sum()),
        "displaced_twh_spin": round(float(disp_spin.sum()) / 1e6, 3),
        "displaced_twh_full": round(float(disp_full.sum()) / 1e6, 3),
        "cc_loading_excess_twh": round(float(excess.sum()) / 1e6, 3),
        "campd_cc_online_headroom_mean_mw": round(float(meas_head.mean()), 1),
        "campd_headroom_over_req": round(float(meas_head.mean() / req.mean()), 2),
    }


def main() -> None:
    """Run every zone-year and write the JSON."""
    out = {}
    for year in (2019, 2023, 2024, 2025):
        um = pd.read_parquet(BUNDLE / f"unit_marginal_{year}.parquet")
        um = um[um["pass"] == "P1"]
        bench = json.load(gzip.open(REPO_ROOT / f"frontend/data/backcast/bench/NWPP/{year}.json.gz"))["bench"]["plants"]
        for zone in ZONE_BA:
            out[f"{zone}|{year}"] = zone_year(zone, year, um, bench)
            print(zone, year, out[f"{zone}|{year}"])
    p = REPO_ROOT / "results/phase0/nwpp/_nwppnext28_reserve_headroom.json"
    p.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
