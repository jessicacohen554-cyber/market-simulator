"""NYISO-NEXT-18 gates G-2 / G-3 / G-4 / G-6 and the reported block (ZERO LP).

``docs/PRECOMMIT-nyiso-next18-retiree-carry-2026-09-30.md`` sec. 3, every value
anchored to the keeper (``nyisonext16_2021`` / ``nyisonext16_span``) or to the
NYISO RT fuel mix:

G-2: per year and per zone, P1 demand equals the keeper's within 0.1 GWh.
G-3: 2021 NYCA nuclear P1 energy Jan-Apr within +/-5 % of the fuel-mix nuclear
     energy for Jan-Apr; every other month of 2021-2025 equal to the keeper's within
     1 GWh.
G-4: P1 load-slack energy exceeds the keeper's by <= 1 GWh.
G-6: no D-4 failure row keyed (year, mechanism, plant) in the arm's COMPOSED
     ``legitimacy_diagnostics.json`` absent from the keeper's.
Reported: zone load-weighted P1 prices (arm / keeper / measured DA) and the
CENTRAL-EAST-regime Capital - Upstate spread (arm / keeper / measured).
G-1 is ``nyisonext18_compose_span.py --check-only``; G-5 is the scorer's C6 / C8.

Usage::

    python3 scripts/probes/nyisonext18_gates.py --out results/calibration/_nyisonext18_gates.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

import nyisonext13_ch_pricing_phase0 as p13  # noqa: E402
import nyisonext17_gates as g17  # noqa: E402
import nyisonext17_phase0 as p0  # noqa: E402
import nyisonext18_phase0 as p18  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEP = g17.KEEP
ARM = {2021: "nyisonext18_2021", **{y: "nyisonext18_span" for y in range(2022, 2026)}}
ZONES = g17.ZONES
g17.CAL = CAL


def _monthly_nuclear_gwh(bundle: str, y: int) -> np.ndarray:
    """NYCA nuclear P1 energy by month, GWh (the scorer's month edges)."""
    c = pd.read_parquet(CAL / bundle / "hourly" / f"class_hourly_{y}.parquet")
    c = c[(c["pass"] == "P1") & (c.klass == "nuclear")].sort_values("hour")
    mon = p0._mon()[c.hour.to_numpy()]
    return np.array([c.mw.to_numpy()[mon == m].sum() / 1e3 for m in range(12)])


def year(y: int) -> dict:
    """All gates and the reported block for one year."""
    sa, sk = g17._sys(ARM[y], y), g17._sys(KEEP[y], y)
    da = sa.groupby("zone").demand.sum() / 1e3
    dk = sk.groupby("zone").demand.sum() / 1e3
    dz = {z: round(float(da[z] - dk[z]), 4) for z in ZONES}
    g2_pass = all(abs(v) <= 0.1 for v in dz.values())

    na, nk = _monthly_nuclear_gwh(ARM[y], y), _monthly_nuclear_gwh(KEEP[y], y)
    mix = p18._fuel_mix(y)["Nuclear"].to_numpy()
    mon = p0._mon()
    meas = np.array([np.nansum(mix[mon == m]) / 1e3 for m in range(12)])
    g3 = {
        "arm_gwh": np.round(na, 1).tolist(),
        "keeper_gwh": np.round(nk, 1).tolist(),
        "fuel_mix_gwh": np.round(meas, 1).tolist(),
    }
    if y == 2021:
        ja, jm, jk = na[:4].sum(), meas[:4].sum(), nk[:4].sum()
        g3["jan_apr_arm_vs_mix_pct"] = round((ja / jm - 1) * 100, 2)
        g3["jan_apr_keeper_vs_mix_pct"] = round((jk / jm - 1) * 100, 2)
        rest = range(4, 12)
        g3_pass = abs(ja / jm - 1) <= 0.05 and all(
            abs(na[m] - nk[m]) <= 1.0 for m in rest
        )
    else:
        g3_pass = bool(np.all(np.abs(na - nk) <= 1.0))

    slack_a, slack_k = float(sa.slack.sum()) / 1e3, float(sk.slack.sum()) / 1e3
    new_d4 = sorted(
        map(str, g17._d4_fail_keys(ARM[y], y) - g17._d4_fail_keys(KEEP[y], y))
    )
    gone_d4 = sorted(
        map(str, g17._d4_fail_keys(KEEP[y], y) - g17._d4_fail_keys(ARM[y], y))
    )

    meas_da = p13.meas_da(y)
    hi = p0._ce_ratio(y) >= 0.85
    pa = sa.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )
    pk = sk.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )
    up_m = meas_da[list(p13.UPSTATE)].mean(axis=1).to_numpy()
    cap_m = meas_da["CAPITL"].to_numpy()
    jan_apr = p0._mon() < 4
    reported = {
        "zone_lw_price": {
            z: {"arm": g17._lw(sa, z), "keeper": g17._lw(sk, z)} for z in ZONES
        },
        "zone_lw_price_jan_apr": {
            z: {"arm": g17._lw(sa, z, jan_apr), "keeper": g17._lw(sk, z, jan_apr)}
            for z in ZONES
        },
        "ce_hi_capital_minus_upstate": {
            "arm": round(
                float(np.nanmean((pa.Capital_Hudson - pa.Upstate_West)[hi])), 2
            ),
            "keeper": round(
                float(np.nanmean((pk.Capital_Hudson - pk.Upstate_West)[hi])), 2
            ),
            "measured_da": round(float(np.nanmean((cap_m - up_m)[hi])), 2),
        },
        "d4_cleared": gone_d4,
    }
    return {
        "G2_zone_demand_delta_gwh": dz,
        "G2_pass": g2_pass,
        "G3_nuclear": g3,
        "G3_pass": bool(g3_pass),
        "G4_slack_gwh": {"arm": round(slack_a, 3), "keeper": round(slack_k, 3)},
        "G4_pass": slack_a - slack_k <= 1.0,
        "G6_new_d4_failures": new_d4,
        "G6_pass": not new_d4,
        "reported": reported,
    }


def main() -> None:
    """All years; write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2021, 2026)))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {str(y): year(y) for y in a.years}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, {k: d[k] for k in d if k.endswith("_pass")})
        print("   G3", {k: v for k, v in d["G3_nuclear"].items() if "pct" in k})
        print("   G4", d["G4_slack_gwh"], "G6 new", d["G6_new_d4_failures"])
        print(
            "   LW",
            d["reported"]["zone_lw_price"]["Upstate_West"],
            "CE-hi",
            d["reported"]["ce_hi_capital_minus_upstate"],
        )


if __name__ == "__main__":
    main()
