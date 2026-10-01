"""capx D74 full-window A/B instrument (zero LP): per delivery year the clearing
of arm / control-P / control-B at HEAD beside the published record; economic
exits by fuel; the FC-3 / FC-2 / CO2 rows of each leg's score.json; the
no-default-cap ledger block per year; STOP 5's R / non-screened-Q_0 identity.

Usage: PYTHONPATH=.:src .venv/bin/python full-window-2026-09-06.py --arm A --ctlp P --ctlb B [--out o.json]
"""

from __future__ import annotations
import argparse
import glob
import json
from collections import defaultdict

PUB = {
    2022: (50.00, 1.0510),
    2023: (34.13, 1.0552),
    2024: (28.92, 1.0555),
    2025: (269.92, 1.0049),
}


def bundle(d):
    h = glob.glob(f"{d}/PJM/*/")
    assert len(h) == 1, (d, h)
    return h[0]


def load(b, y):
    return json.load(open(f"{b}/evolution_{y}.json"))


def leg(b):
    out = {"years": {}, "exec_by_fuel": defaultdict(float)}
    for y in (2022, 2023, 2024, 2025):
        d = load(b, y)
        cc = d["capacity_clearing"]
        class_mw = sum(r[3] for r in cc["offer_stack"] if r[1] in ("gas_st", "oil"))
        ndc = d.get("no_default_cap_price_takers")
        pe = defaultdict(float)
        for r in d.get("pipeline_events", []):
            pe[(r["event"], r["fuel"])] += r["mw"]
            if r["event"] == "executed":
                out["exec_by_fuel"][r["fuel"]] += r["mw"]
        out["years"][y] = {
            "price": cc["price_usd_per_mw_day"],
            "ratio": cc["price_usd_per_mw_day"] / PUB[y][0],
            "pos": cc["cleared_position"],
            "dpos_pt": 100 * (cc["cleared_position"] - PUB[y][1]),
            "how": cc["how"],
            "R": cc["requirement_mw"],
            "Q0": cc["price_takers_mw"],
            "Q0_nonclass": cc["price_takers_mw"]
            - (ndc["accredited_mw"] if ndc else 0.0),
            "class_in_stack_mw": class_mw,
            "census": cc["census_mw"],
            "census_pos": cc["census_position"],
            "n_offers": cc["n_offers"],
            "n_uncleared": cc["n_uncleared"],
            "uncleared": {
                k: round(v, 1) for k, v in cc["uncleared_mw_by_fuel"].items()
            },
            "ndc_block": None
            if ndc is None
            else {k: ndc[k] for k in ("units", "mw", "accredited_mw", "mw_by_fuel")},
            "pipeline": {f"{e}:{f}": round(v, 1) for (e, f), v in sorted(pe.items())},
            "screen_peak": d.get("screen_peak_demand_mw"),
            "entry": d.get("entry_decided_mw_by_tech"),
        }
    out["exec_by_fuel"] = {
        k: round(v / 1000, 3) for k, v in sorted(out["exec_by_fuel"].items())
    }
    try:
        s = json.load(open(f"{b}/score.json"))
        r = s["retirements"]
        a = s["additions"]
        out["fc3"] = {
            "total_gw": r["total_gw"],
            "per_fuel": {
                k: (v["model_gw"], v["actual_gw"], v.get("err_frac"), v.get("band"))
                for k, v in r["per_fuel"].items()
            },
            "recall": r["unit_recall_gt300"],
            "false_retire": r.get("false_retire"),
            "release_precision": r.get("plant_release_precision"),
        }
        out["fc2"] = {
            "by_tech": {
                k: (v.get("model_gw"), v.get("actual_gw"), v.get("band"))
                for k, v in a["by_tech"].items()
            }
            if "by_tech" in a
            else a,
            "shares": a.get("shares"),
        }
        out["co2"] = s.get("co2")
        out["loyo"] = s.get("loyo", {}).get("holds_2of3")
        out["tr10"] = s.get("tr10")
        out["blk10"] = s.get("blk10_backstop")
    except FileNotFoundError:
        out["fc3"] = "no score.json"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--ctlp")
    ap.add_argument("--ctlb")
    ap.add_argument("--out")
    a = ap.parse_args()
    legs = {"arm": leg(bundle(a.arm))}
    if a.ctlp:
        legs["ctlP"] = leg(bundle(a.ctlp))
    if a.ctlb:
        legs["ctlB"] = leg(bundle(a.ctlb))
    for y in (2022, 2023, 2024, 2025):
        print(f"\nDY {y}/{y + 1 - 2000:02d} (pub {PUB[y][0]} @ {PUB[y][1]})")
        for n, L in legs.items():
            r = L["years"][y]
            print(
                f"  {n:5s} price {r['price']:8.2f} ({r['ratio']:.3f}x) pos {r['pos']:.4f} ({r['dpos_pt']:+.2f}pt) {r['how']:34s} R {r['R']:.1f} Q0 {r['Q0']:.1f} (non-class {r['Q0_nonclass']:.1f}) census {r['census']:.1f} unc {r['uncleared']}"
            )
        for n, L in legs.items():
            print(f"  {n:5s} pipeline {L['years'][y]['pipeline']}")
    print(
        "\nexecuted economic exits GW by fuel:",
        {n: L["exec_by_fuel"] for n, L in legs.items()},
    )
    for n, L in legs.items():
        print(f"\n{n} FC-3:", L.get("fc3"))
        print(f"{n} FC-2:", L.get("fc2"))
        print(
            f"{n} CO2:",
            L.get("co2"),
            "LOYO",
            L.get("loyo"),
            "TR10",
            L.get("tr10"),
            "BLK10",
            L.get("blk10"),
        )
    if a.out:
        json.dump(legs, open(a.out, "w"), indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    main()
