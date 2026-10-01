"""NYISO-NEXT-15 G-2 / G-3 / G-4 / G-6 and reported diagnostics (ZERO LP), per arm leg.

``docs/records/nyiso/PRECOMMIT-nyiso-next15-landing-band-2026-09-30.md`` sec. 4 / 6:

G-2: each pooled border link's P1 annual mean flow is within max(3 % of
     |measured|, 25 MW) of its measured P-32 attributed mean.
G-3: the ``Upstate_West>Capital_Hudson`` link sits at its forward bound in
     >= 1 % and <= 50 % of P1 hours.
G-4: Upstate_West P1 hours at <= $0 are <= 100.
G-6: P1 load-slack energy exceeds the keeper's by <= 1 GWh.
Reported: NEXT-14's reported block (coincidence lift, spread, hydro, zonal
load-weighted price vs the keeper) plus the link's mean flow in the market's
CE-binding hours vs measured TOTAL EAST. The keeper's network sidecars are read
from ``--keeper-legs`` (the NEXT-14 leg commits). Record:
``results/phase0/nyiso/_nyisonext15_gates.json``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO):
    sys.path.insert(0, str(p))

from market_sim.data.nyiso_par_attribution import attributed_zone_net  # noqa: E402
from scripts.lib.clean_io import read_clean  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEP = {2021: "nyisonext14_2021", **{y: "nyisonext14_span" for y in range(2022, 2026)}}
ZONES = ["Capital_Hudson", "Long_Island", "NYC", "Upstate_West"]
G2_FRAC, G2_MW, G6_GWH = 0.03, 25.0, 1.0
OUT = CAL.parent / "phase0" / "nyiso" / "_nyisonext15_gates.json"

_spec = importlib.util.spec_from_file_location(
    "g14", REPO / "scripts" / "probes" / "nyisonext14_gates.py"
)
_g14 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g14)


def _net(path: Path) -> pd.DataFrame:
    n = pd.read_parquet(path)
    return n[n["pass"] == "P1"] if "pass" in n.columns else n


def year(y: int, keeper_legs: Path) -> dict:
    """All gates and the reported block for one leg."""
    leg = CAL / f"nyisonext15_{y}"
    # NEXT-14's reported block, pointed at this leg through a shim dir: its
    # year() reads CAL/nyisonext14_<y> as the arm and CAL/KEEP[y] as the keeper.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        shim = Path(tmp)
        (shim / f"nyisonext14_{y}").symlink_to(leg.resolve())
        (shim / "k").symlink_to((CAL / KEEP[y]).resolve())
        _g14.CAL, _g14.KEEP = shim, {y: "k"}
        rep = _g14.year(y)
    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y, validate=False)
    an = attributed_zone_net(f[f.interface != "SCH - NE - NY"], y)
    an = an[~((an.local_hour.dt.month == 2) & (an.local_hour.dt.day == 29))]
    meas = an.groupby("zone").flow_mw.mean()
    n = _net(leg / "hourly" / f"network_{y}.parquet")
    nk = _net(keeper_legs / f"network_{y}.parquet")
    g2 = {}
    for z in ZONES:
        name = f"NYISO_external>{z}"
        mdl = float(n[n.name == name].mw.mean())
        tol = max(G2_FRAC * abs(float(meas[z])), G2_MW)
        g2[z] = {
            "arm_mw": round(mdl, 1),
            "keeper_mw": round(float(nk[nk.name == name].mw.mean()), 1),
            "measured_mw": round(float(meas[z]), 1),
            "tol_mw": round(tol, 1),
            "pass": abs(mdl - float(meas[z])) <= tol,
        }
    s = pd.read_parquet(leg / "hourly" / f"system_{y}.parquet")
    sk = pd.read_parquet(CAL / KEEP[y] / "hourly" / f"system_{y}.parquet")
    slack = float(s[s["pass"] == "P1"].slack.sum()) / 1e3
    slack_k = float(sk[sk["pass"] == "P1"].slack.sum()) / 1e3

    fl = f.copy()
    fl["lh"] = pd.to_datetime(fl.interval_start_local).dt.floor("h")
    te = fl[fl.interface == "TOTAL EAST"].groupby("lh").flow_mw.mean()
    idx = pd.date_range(f"{y}-01-01", f"{y + 1}-01-01", freq="h", inclusive="left")
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    te = te.reindex(idx).ffill().bfill().to_numpy()[:8760]
    mkt = _g14._market_ce_bind(y)
    lk = n[n.name == _g14.LINK].sort_values("hour").mw.to_numpy()[:8760]
    lkk = nk[nk.name == _g14.LINK].sort_values("hour").mw.to_numpy()[:8760]
    return {
        "G2_landing": g2,
        "G2_pass": all(v["pass"] for v in g2.values()),
        "G3_link_binding_share": rep["G2_link_binding_share"],
        "G3_pass": rep["G2_pass"],
        "G4_upstate_h_le_0": rep["G3_upstate_h_le_0"],
        "G4_pass": rep["G3_pass"],
        "G6_slack_gwh": {"arm": round(slack, 3), "keeper": round(slack_k, 3)},
        "G6_pass": slack - slack_k <= G6_GWH,
        "link_flow_in_mkt_ce_binding_h": {
            "arm": round(float(lk[mkt].mean()), 0),
            "keeper": round(float(lkk[mkt].mean()), 0),
            "measured_total_east": round(float(te[mkt].mean()), 0),
        },
        "reported": {k: v for k, v in rep.items() if not k.startswith(("G2", "G3"))},
    }


def main() -> None:
    """All legs; write the record."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--keeper-legs", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2021, 2026)))
    a = ap.parse_args()
    out = {str(y): year(y, a.keeper_legs) for y in a.years}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(
            y,
            "G2",
            d["G2_pass"],
            {z: (v["arm_mw"], v["measured_mw"]) for z, v in d["G2_landing"].items()},
            "G3",
            d["G3_link_binding_share"],
            d["G3_pass"],
            "G4",
            d["G4_upstate_h_le_0"],
            d["G4_pass"],
            "G6",
            d["G6_slack_gwh"],
            d["G6_pass"],
        )


if __name__ == "__main__":
    main()
