"""NYISO-NEXT-16 G-2 / G-3 / G-4 / G-6 / G-7 and reported diagnostics (ZERO LP), per arm leg.

``docs/PRECOMMIT-nyiso-next16-winter-spread-2026-09-30.md`` sec. 4:

G-2: (a) each zone's annual mean of the flag's monthly construction equals its
     measured SOM annual within $0.005/MMBtu (recomputed from the pinned code);
     (b) DJF mean |dLMP| vs the keeper > $1/MWh in at least one zone.
G-3: the ``Upstate_West>Capital_Hudson`` link sits at its forward bound in
     >= 1 % and <= 50 % of P1 hours.
G-4: Upstate_West P1 hours at <= $0 are <= 100.
G-6: P1 load-slack energy exceeds the keeper's by <= 1 GWh.
G-7: no D-4 failure row keyed (year, check, floor, plant) in the arm that is
     absent from the keeper.
Reported: NEXT-14's reported block (lift, spread, hydro, zonal LW price vs the
keeper) and the DJF downstate - Upstate_West spread, arm / keeper / measured DA.
Record: ``results/calibration/_nyisonext16_gates.json``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (
    REPO / "src",
    REPO,
    REPO / "scripts",
    REPO / "scripts" / "probes",
    REPO / "scripts" / "data",
):
    sys.path.insert(0, str(p))

import nyisonext13_ch_pricing_phase0 as p13  # noqa: E402

from market_sim.data.fuel.basis import nyiso as nb  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEP = {2021: "nyisonext15_2021", **{y: "nyisonext15_span" for y in range(2022, 2026)}}
G2_TOL, G2_LIVE, G6_GWH = 0.005, 1.0, 1.0
OUT = CAL / "_nyisonext16_gates.json"
DOWN = ("Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")

_spec = importlib.util.spec_from_file_location(
    "g14", REPO / "scripts" / "probes" / "nyisonext14_gates.py"
)
_g14 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g14)


class _Cfg:
    """Minimal config the flag's construction reads."""

    iso = "NYISO"
    nyiso_iroquois_winter_spread = True


def _som_annual(y: int) -> dict[str, float]:
    f = pd.read_csv(REPO / "data" / "raw" / "nyiso_zonal_gas_hub.csv")
    f = f[f.year == y]
    return {str(r.zone): float(r.hub_usd_mmbtu) for r in f.itertuples()}


def _prices(bundle: str, y: int) -> pd.DataFrame:
    s = pd.read_parquet(CAL / bundle / "hourly" / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    return s.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )


def _d4_fail_keys(bundle: str, y: int) -> set[tuple]:
    d = json.loads((CAL / bundle / "legitimacy_diagnostics.json").read_text())[
        "diagnostics"
    ]["D4"]
    rows = d.get("failures") or [
        r for r in d.get("rows", []) if r.get("verdict") not in ("pass", None)
    ]
    return {
        (r.get("year"), r.get("check"), r.get("floor"), str(r.get("plant")))
        for r in rows
        if isinstance(r, dict) and int(r.get("year", y)) == y
    }


def year(y: int) -> dict:
    """All gates and the reported block for one leg."""
    leg = CAL / f"nyisonext16_{y}"
    with tempfile.TemporaryDirectory() as tmp:
        shim = Path(tmp)
        (shim / f"nyisonext14_{y}").symlink_to(leg.resolve())
        (shim / "k").symlink_to((CAL / KEEP[y]).resolve())
        _g14.CAL, _g14.KEEP = shim, {y: "k"}
        rep = _g14.year(y)

    rec = nb.nyiso_reconciled_reference_monthly(y)
    ratios = nb.nyiso_zonal_gas_ratios_monthly(_Cfg(), y)
    som = _som_annual(y)
    cons = {
        z: round(float((ratios[z] * rec[0]).mean()) - som[z], 4)
        for z in ratios
        if z in som
    }

    pa, pk = _prices(f"nyisonext16_{y}", y), _prices(KEEP[y], y)
    hrs = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    djf = np.isin(hrs.month, (1, 2, 12))
    zones = [z for z in pa.columns if z in ("Upstate_West", *DOWN)]
    live = {
        z: round(float(np.abs(pa[z].to_numpy() - pk[z].to_numpy())[djf].mean()), 2)
        for z in zones
    }

    meas = p13.meas_da(y)
    up_m = meas[list(p13.UPSTATE)].mean(axis=1).to_numpy()
    spread = {}
    for z in DOWN:
        cols = list(p13.MODEL_TO_MEAS[z])
        mz = meas[cols].mean(axis=1).to_numpy()
        spread[z] = {
            "arm": round(
                float(np.nanmean((pa[z] - pa["Upstate_West"]).to_numpy()[djf])), 2
            ),
            "keeper": round(
                float(np.nanmean((pk[z] - pk["Upstate_West"]).to_numpy()[djf])), 2
            ),
            "measured_da": round(float(np.nanmean((mz - up_m)[djf])), 2),
        }

    s = pd.read_parquet(leg / "hourly" / f"system_{y}.parquet")
    sk = pd.read_parquet(CAL / KEEP[y] / "hourly" / f"system_{y}.parquet")
    slack = float(s[s["pass"] == "P1"].slack.sum()) / 1e3
    slack_k = float(sk[sk["pass"] == "P1"].slack.sum()) / 1e3

    new_d4 = sorted(
        map(str, _d4_fail_keys(f"nyisonext16_{y}", y) - _d4_fail_keys(KEEP[y], y))
    )
    return {
        "G2_conservation_delta": cons,
        "G2_djf_abs_dlmp": live,
        "G2_pass": all(abs(v) <= G2_TOL for v in cons.values())
        and max(live.values()) > G2_LIVE,
        "G3_link_binding_share": rep["G2_link_binding_share"],
        "G3_pass": rep["G2_pass"],
        "G4_upstate_h_le_0": rep["G3_upstate_h_le_0"],
        "G4_pass": rep["G3_pass"],
        "G6_slack_gwh": {"arm": round(slack, 3), "keeper": round(slack_k, 3)},
        "G6_pass": slack - slack_k <= G6_GWH,
        "G7_new_d4_failures": new_d4,
        "G7_pass": not new_d4,
        "djf_spread_vs_upstate": spread,
        "reported": {k: v for k, v in rep.items() if not k.startswith(("G2", "G3"))},
    }


def main() -> None:
    """All legs; write the record."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2021, 2026)))
    a = ap.parse_args()
    out = {str(y): year(y) for y in a.years}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, {k: d[k] for k in d if k.endswith("_pass")})
        print("   G2", d["G2_conservation_delta"], d["G2_djf_abs_dlmp"])
        print(
            "   G3",
            d["G3_link_binding_share"],
            "G4",
            d["G4_upstate_h_le_0"],
            "G6",
            d["G6_slack_gwh"],
            "G7",
            d["G7_new_d4_failures"],
        )
        print("   DJF spread", d["djf_spread_vs_upstate"])


if __name__ == "__main__":
    main()
