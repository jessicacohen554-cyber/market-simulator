"""NYISO-NEXT-14 G-2 / G-3 and reported diagnostics (ZERO LP), per arm leg.

``docs/records/nyiso/PRECOMMIT-nyiso-next14-total-east-cutset-2026-09-30.md`` sec. 5 / 7:

G-2: in P1 the ``Upstate_West>Capital_Hudson`` link sits at its forward bound
     (flow >= limit_up - 1 MW) in >= 1 % and <= 50 % of hours.
G-3: Upstate_West P1 hours at <= $0 are <= 100.
Reported: the link's binding-hour coincidence with the market's CENTRAL EAST
binding hours (flow >= 95 % of the posted limit; lift, precision, recall), the
Capital_Hudson - Upstate_West spread in the link's binding hours vs the measured
(F,G) - (A-E) DA basis in the market's; hydro vs EIA-923; load-weighted P1 price
delta vs the keeper by zone. Record: ``results/phase0/nyiso/_nyisonext14_gates.json``.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO):
    sys.path.insert(0, str(p))

from scripts.lib.clean_io import read_clean  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEP = {2021: "nyisonext13_2021", **{y: "nyisonext13_span" for y in range(2022, 2026)}}
LINK = "Upstate_West>Capital_Hudson"
G2_LO, G2_HI, G3_MAX = 0.01, 0.50, 100
CE_BIND_FRAC = 0.95
A_E = ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"]
F_G = ["CAPITL", "HUD VL"]
OUT = CAL.parent / "phase0" / "nyiso" / "_nyisonext14_gates.json"

_spec = importlib.util.spec_from_file_location(
    "p13", REPO / "scripts" / "probes" / "nyisonext13_ch_pricing_phase0.py"
)
_p13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_p13)


def _lw(s: pd.DataFrame) -> dict:
    """Load-weighted P1 price by zone and system (external nodes excluded)."""
    s = s[(s["pass"] == "P1") & ~s.zone.astype(str).isin(["NYISO_external", "NYISO_NE_AC"])]
    out = {str(z): float(np.average(g.price, weights=g.demand)) for z, g in s.groupby(s.zone.astype(str))}
    out["system"] = float(np.average(s.price, weights=s.demand))
    return out


def _market_ce_bind(y: int) -> np.ndarray:
    """Market CENTRAL EAST at >= 95 % of its posted limit, on the model's 8,760-hour clock."""
    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y)
    f = f[f.interface == "CENTRAL EAST - VC"].copy()
    f["lh"] = pd.to_datetime(f.interval_start_local).dt.floor("h")
    g = f.groupby("lh")[["flow_mw", "positive_limit_mw"]].mean()
    idx = pd.date_range(f"{y}-01-01", f"{y + 1}-01-01", freq="h", inclusive="left")
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    g = g.reindex(idx).ffill().bfill()
    return (g.flow_mw >= CE_BIND_FRAC * g.positive_limit_mw).to_numpy()[:8760]


def year(y: int) -> dict:
    """G-2, G-3 and the reported block for one leg."""
    leg = CAL / f"nyisonext14_{y}"
    s = pd.read_parquet(leg / "hourly" / f"system_{y}.parquet")
    sk = pd.read_parquet(CAL / KEEP[y] / "hourly" / f"system_{y}.parquet")
    p1 = s[s["pass"] == "P1"]
    uw = p1[p1.zone.astype(str) == "Upstate_West"].set_index("hour").price.sort_index()
    ch = p1[p1.zone.astype(str) == "Capital_Hudson"].set_index("hour").price.sort_index()

    n = pd.read_parquet(leg / "hourly" / f"network_{y}.parquet")
    if "pass" in n.columns:
        n = n[n["pass"] == "P1"]
    lk = n[(n["kind"] == "link") & (n["name"] == LINK)].sort_values("hour")
    bind = (lk.mw.to_numpy() >= lk.limit_up.to_numpy() - 1.0)[:8760]
    share = float(bind.mean())

    mkt = _market_ce_bind(y)
    both = int((bind & mkt).sum())
    exp = float(bind.sum() * mkt.sum() / len(bind))
    da = _p13.meas_da(y)
    basis = (da[F_G].mean(axis=1) - da[A_E].mean(axis=1)).to_numpy()[:8760]
    spread = (ch - uw).to_numpy()[:8760]

    c = pd.read_parquet(leg / "hourly" / f"class_hourly_{y}.parquet")
    hydro = float(c[(c["pass"] == "P1") & (c.klass.astype(str) == "hydro")].mw.sum()) / 1e6
    bench = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{y}.json.gz"))["bench"]
    la, lk_ = _lw(s), _lw(sk)
    uw_le0 = int((uw <= 0).sum())
    return {
        "G2_link_binding_share": round(share, 4),
        "G2_pass": G2_LO <= share <= G2_HI,
        "G3_upstate_h_le_0": uw_le0,
        "G3_pass": uw_le0 <= G3_MAX,
        "link_limit_up_mean_mw": round(float(lk.limit_up.mean()), 1),
        "link_flow_mean_mw": round(float(lk.mw.mean()), 1),
        "market_ce_binding_share": round(float(mkt.mean()), 4),
        "coincidence": {
            "both_h": both,
            "expected_if_independent": round(exp, 1),
            "lift": round(both / exp, 2) if exp else None,
            "precision": round(both / max(int(bind.sum()), 1), 3),
            "recall": round(both / max(int(mkt.sum()), 1), 3),
        },
        "spread_model_in_link_binding_h": round(float(np.nanmean(spread[bind])), 2) if bind.any() else None,
        "basis_measured_in_market_ce_binding_h": round(float(np.nanmean(basis[mkt])), 2),
        "hydro_twh": {"arm": round(hydro, 2), "eia923": round(float(bench["classFull"]["hydro"]), 2)},
        "upstate_h_at_pooled_node_price": int(
            (abs(uw - p1[p1.zone.astype(str) == "NYISO_external"].set_index("hour").price.sort_index()) < 0.5).sum()
        ),
        "lw_price": {z: {"keeper": round(lk_[z], 2), "arm": round(la[z], 2)} for z in la},
    }


def main() -> None:
    """All legs; write the record."""
    out = {str(y): year(y) for y in range(2021, 2026)}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, "G2", d["G2_link_binding_share"], d["G2_pass"], "G3", d["G3_upstate_h_le_0"], d["G3_pass"],
              "lift", d["coincidence"]["lift"], "hydro", d["hydro_twh"], "UW", d["lw_price"]["Upstate_West"])


if __name__ == "__main__":
    main()
