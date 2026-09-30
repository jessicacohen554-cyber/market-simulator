"""NYISO-NEXT-17 gates G-2 / G-3 / G-4 / G-6 / G-7 and the reported block (ZERO LP).

``docs/PRECOMMIT-nyiso-next17-fg-split-2026-09-30.md`` sec. 3, every value anchored
to the keeper (``nyisonext16_2021`` / ``nyisonext16_span``):

G-2: total NYCA P1 demand equal within 0.1 GWh; Capital_Hudson + Lower_Hudson
     within 0.1 %; Upstate_West, NYC and Long_Island each within 0.1 %.
G-3: ``Upstate_West>Capital_Hudson`` at its forward bound in >= 1 % of P1 hours,
     and ``Upstate_West>Lower_Hudson`` carries positive flow in >= 50 % of them.
G-4: Upstate_West P1 hours at <= $0 are <= 100.
G-6: P1 load-slack energy exceeds the keeper's by <= 1 GWh.
G-7: no D-4 failure row keyed (year, mechanism, plant) in the arm's COMPOSED
     ``legitimacy_diagnostics.json`` absent from the keeper's.
Reported: zone load-weighted P1 prices (arm / keeper / measured DA), the
CENTRAL-EAST-regime Capital - Upstate spread (arm / keeper / measured), and the
upstate links' binding shares.

Usage::

    python3 scripts/probes/nyisonext17_gates.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

import nyisonext13_ch_pricing_phase0 as p13  # noqa: E402
import nyisonext17_phase0 as p0  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEP = {2021: "nyisonext16_2021", **{y: "nyisonext16_span" for y in range(2022, 2026)}}
ARM = {2021: "nyisonext17_2021", **{y: "nyisonext17_span" for y in range(2022, 2026)}}
ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")


def _sys(bundle: str, y: int) -> pd.DataFrame:
    s = pd.read_parquet(CAL / bundle / "hourly" / f"system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _net(leg: str, y: int) -> pd.DataFrame:
    n = pd.read_parquet(CAL / leg / "hourly" / f"network_{y}.parquet")
    return n[(n["pass"] == "P1") & (n.kind == "link")]


def _link(n: pd.DataFrame, name: str) -> dict:
    ln = n[n.name == name].sort_values("hour")
    if ln.empty:
        return {"present": False}
    mw, lim = ln.mw.to_numpy(), ln.limit_up.to_numpy()
    return {
        "present": True,
        "mean_mw": round(float(mw.mean()), 1),
        "at_bound_pct": round(float(np.mean(mw >= lim - 1.0)) * 100, 2),
        "positive_pct": round(float(np.mean(mw > 0.0)) * 100, 2),
    }


def _d4_fail_keys(bundle: str, y: int) -> set[tuple]:
    """D-4 failures keyed (year, mechanism x class, plant); the rows are prose strings."""
    d = json.loads((CAL / bundle / "legitimacy_diagnostics.json").read_text())[
        "diagnostics"
    ]["D4"]
    keys = set()
    for r in d.get("failures") or []:
        m = re.match(r"(\d{4}) (.+?): plant (\S+) ", str(r))
        if m and int(m.group(1)) == y:
            keys.add((int(m.group(1)), m.group(2), m.group(3)))
    return keys


def _lw(s: pd.DataFrame, z: str, mask: np.ndarray | None = None) -> float:
    d = s[s.zone == z].sort_values("hour")
    p, w = d.price.to_numpy(), d.demand.to_numpy()
    if mask is not None:
        p, w = p[mask], w[mask]
    return round(float((p * w).sum() / w.sum()), 2)


def year(y: int) -> dict:
    """All gates and the reported block for one year."""
    sa, sk = _sys(ARM[y], y), _sys(KEEP[y], y)
    da = sa.groupby("zone").demand.sum() / 1e3
    dk = sk.groupby("zone").demand.sum() / 1e3
    tot_a, tot_k = float(da[list(ZONES)].sum()), float(dk[list(ZONES)].sum())
    fg_a = float(da["Capital_Hudson"] + da["Lower_Hudson"])
    fg_k = float(dk["Capital_Hudson"] + dk["Lower_Hudson"])
    rel = {
        z: round(abs(float(da[z]) / float(dk[z]) - 1.0) * 100, 4)
        for z in ("Upstate_West", "NYC", "Long_Island")
    }
    g2 = {
        "total_gwh": {"arm": round(tot_a, 2), "keeper": round(tot_k, 2)},
        "ch_plus_lh_gwh": {"arm": round(fg_a, 2), "keeper": round(fg_k, 2)},
        "zone_gwh_arm": {z: round(float(da[z]), 1) for z in ZONES},
        "zone_gwh_keeper": {z: round(float(dk[z]), 1) for z in ZONES},
        "other_zone_rel_pct": rel,
    }
    g2_pass = (
        abs(tot_a - tot_k) <= 0.1
        and abs(fg_a / fg_k - 1.0) <= 0.001
        and all(v <= 0.1 for v in rel.values())
    )

    leg = f"nyisonext17_{y}"
    na = _net(leg, y)
    ce = _link(na, "Upstate_West>Capital_Hudson")
    nonce = _link(na, "Upstate_West>Lower_Hudson")
    g3_pass = bool(
        ce.get("present")
        and nonce.get("present")
        and ce["at_bound_pct"] >= 1.0
        and nonce["positive_pct"] >= 50.0
    )

    uw = sa[sa.zone == "Upstate_West"]
    n_le0 = int((uw.price <= 0.0).sum())
    slack_a, slack_k = float(sa.slack.sum()) / 1e3, float(sk.slack.sum()) / 1e3
    new_d4 = sorted(map(str, _d4_fail_keys(ARM[y], y) - _d4_fail_keys(KEEP[y], y)))
    gone_d4 = sorted(map(str, _d4_fail_keys(KEEP[y], y) - _d4_fail_keys(ARM[y], y)))

    meas = p13.meas_da(y)
    ratio = p0._ce_ratio(y)
    hi = ratio >= 0.85
    pa = sa.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )
    pk = sk.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )
    up_m = meas[list(p13.UPSTATE)].mean(axis=1).to_numpy()
    cap_m = meas["CAPITL"].to_numpy()
    reported = {
        "zone_lw_price": {
            z: {
                "arm": _lw(sa, z),
                "keeper": _lw(sk, z),
                "meas_da": round(
                    float(np.nanmean(meas[list(p13.MODEL_TO_MEAS[z])].mean(axis=1))),
                    2,
                ),
            }
            for z in ZONES
        },
        "ce_hi_share_pct": round(float(hi.mean()) * 100, 1),
        "ce_hi_capital_minus_upstate": {
            "arm": round(
                float(np.nanmean((pa["Capital_Hudson"] - pa["Upstate_West"])[hi])), 2
            ),
            "keeper": round(
                float(np.nanmean((pk["Capital_Hudson"] - pk["Upstate_West"])[hi])), 2
            ),
            "measured_da": round(float(np.nanmean((cap_m - up_m)[hi])), 2),
        },
        "keeper_link_uw_ch": (
            _link(nk, "Upstate_West>Capital_Hudson")
            if (nk := _net_keeper(y)) is not None
            else "unavailable (keeper leg branch deleted; rule 33 (f))"
        ),
        "d4_cleared": gone_d4,
    }
    return {
        "G2": g2,
        "G2_pass": g2_pass,
        "G3_ce_link": ce,
        "G3_nonce_link": nonce,
        "G3_pass": g3_pass,
        "G4_upstate_h_le_0": n_le0,
        "G4_pass": n_le0 <= 100,
        "G6_slack_gwh": {"arm": round(slack_a, 3), "keeper": round(slack_k, 3)},
        "G6_pass": slack_a - slack_k <= 1.0,
        "G7_new_d4_failures": new_d4,
        "G7_pass": not new_d4,
        "reported": reported,
    }


def _net_keeper(y: int) -> pd.DataFrame | None:
    """Keeper's per-year network sidecar, extracted by the caller (None if gone)."""
    p = Path(_KEEPER_NET_DIR) / f"network_{y}.parquet"
    if not p.exists():
        return None
    n = pd.read_parquet(p)
    return n[(n["pass"] == "P1") & (n.kind == "link")]


_KEEPER_NET_DIR = "."


def main() -> None:
    """All years; write the record."""
    global _KEEPER_NET_DIR
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2021, 2026)))
    ap.add_argument("--keeper-net-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    _KEEPER_NET_DIR = a.keeper_net_dir
    out = {str(y): year(y) for y in a.years}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, {k: d[k] for k in d if k.endswith("_pass")})
        print("   G2", d["G2"]["total_gwh"], d["G2"]["ch_plus_lh_gwh"])
        print("   G3", d["G3_ce_link"], d["G3_nonce_link"])
        print("   G4", d["G4_upstate_h_le_0"], "G6", d["G6_slack_gwh"])
        print("   G7", d["G7_new_d4_failures"], "cleared", d["reported"]["d4_cleared"])
        print("   CE-hi spread", d["reported"]["ce_hi_capital_minus_upstate"])


if __name__ == "__main__":
    main()
