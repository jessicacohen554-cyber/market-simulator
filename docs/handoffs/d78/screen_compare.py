"""capx D78 three-leg differencing — control-P / D58's arm / the repaired arm,
read off three bundles' committed ledgers. Zero LP. Grades the PRECOMMIT §3
screen gates G0-G6 and writes every number the FINDING cites (rule 29(c): the
bundles are deleted before merge; this JSON and the FINDING are the record).

    uv run python docs/handoffs/d78/screen_compare.py \
        --ctl  results/hindcast/pjm-2021-2023-realized-t1h-d78-control-P \
        --d58  results/hindcast/pjm-2021-2023-realized-t1h-d78-d58-arm \
        --arm  results/hindcast/pjm-2021-2023-realized-t1h-d78-arm \
        [--years 2022 2023] [--out docs/handoffs/d78/screen_compare.json]

The sector map is the EIA-860 2020-vintage plant table (the gate's own key,
``plant_code``), joined exactly as D58's ``ab_compare.py`` did.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V2020 = ROOT / "data/raw/eia-860/vintage_2020"

_PLANT_RE = re.compile(r"_p(\d+)_")
_LEGACY_RE = re.compile(r"^(\d+)_")

# D58's measured 2022 screen, control and arm (FINDING-capx-d58 §2.1, §3.2):
# the G0 known answers, to the MW.
D58_2022 = {
    "control": {
        "failing_rows": 677,
        "failing_mw": 29727.9,
        "n_offers": 1370,
        "offered_mw": 150857.2,
        "price_takers_mw": 30577.9,
        "price": 67.760,
    },
    "arm": {
        "failing_rows": 677 - 226 + 41,
        "failing_mw": round(29727.9 - 566.3, 1),
        "n_offers": 1000,
        "offered_mw": 116684.8,
        "price_takers_mw": 64750.2,
        "price": 61.207,
        "only_in_arm_rows": 41,
        "only_in_arm_mw": 2910.2,
    },
    "sector1_only_in_control": {"rows": 226, "mw": 3476.5},
    "shared": {"rows": 451, "mw": 26251.4},
    "sector_gated": {"units": 384, "mw": 41221.6},
}
D58_EXITS = {
    2022: {"control": 7333.7, "arm": 7790.9},
    2023: {"control": 3105.5, "arm": 3310.9},
}

FOOTPRINT_KEYS = (
    "thermal_additions",
    "renewable_additions",
    "storage_additions",
    "announced_derates",
    "confirmed_derates",
    "ccs_retrofits",
    "entry_decided_mw_by_tech",
    "peak_demand_mw",
    "screen_peak_demand_mw",
    "screen_adequacy_requirement_mw",
)


def plant_code(unit_id: str) -> int | None:
    m = _PLANT_RE.search(unit_id)
    if m:
        return int(m.group(1))
    m = _LEGACY_RE.match(unit_id)
    return int(m.group(1)) if m else None


def sectors() -> dict[int, int]:
    df = pd.read_parquet(
        V2020 / "eia860_plant.parquet", columns=["Plant Code", "Sector"]
    )
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def bundle_dir(out_dir: Path) -> Path:
    hits = glob.glob(str(out_dir / "PJM" / "*" / ""))
    assert len(hits) == 1, (out_dir, hits)
    return Path(hits[0])


def ledger(b: Path, year: int) -> dict | None:
    p = b / f"evolution_{year}.json"
    return json.loads(p.read_text()) if p.exists() else None


def fail_rows(led: dict) -> dict[str, float]:
    return {
        e["unit_id"]: float(e.get("mw") or 0.0)
        for e in led.get("pipeline_events") or []
        if e.get("event") in ("decided", "entry_capped")
    }


def sector_of(uid: str, sec: dict[int, int]) -> str:
    c = plant_code(uid)
    return str(sec[c]) if c in sec else "unknown"


def stack_rows(led: dict) -> dict[str, tuple]:
    cc = led.get("capacity_clearing") or {}
    return {r[0]: tuple(r) for r in cc.get("offer_stack", [])}


def year_summary(led: dict, sec: dict[int, int]) -> dict:
    cc = led.get("capacity_clearing") or {}
    fails = fail_rows(led)
    by_sec: dict[str, float] = defaultdict(float)
    rows_by_sec: dict[str, int] = defaultdict(int)
    for uid, mw in fails.items():
        s = sector_of(uid, sec)
        by_sec[s] += mw
        rows_by_sec[s] += 1
    ev = led.get("pipeline_events") or []
    stack = stack_rows(led)
    s1_in_stack = [r for u, r in stack.items() if sector_of(u, sec) == "1"]
    s1_uncleared = [r for r in s1_in_stack if not r[4]]
    return {
        "failing_rows": len(fails),
        "failing_mw": round(sum(fails.values()), 3),
        "failing_mw_by_sector": {k: round(v, 3) for k, v in sorted(by_sec.items())},
        "failing_rows_by_sector": dict(sorted(rows_by_sec.items())),
        "admitted_mw": round(
            sum(float(e.get("mw") or 0.0) for e in ev if e.get("event") == "decided"), 3
        ),
        "capped_mw": round(
            sum(
                float(e.get("mw") or 0.0)
                for e in ev
                if e.get("event") == "entry_capped"
            ),
            3,
        ),
        "sector1_pipeline_rows": sum(
            1 for e in ev if sector_of(e["unit_id"], sec) == "1"
        ),
        "unknown_pipeline_rows": sum(
            1 for e in ev if sector_of(e["unit_id"], sec) == "unknown"
        ),
        "event_counts": {
            k: sum(1 for e in ev if e.get("event") == k)
            for k in ("decided", "entry_capped", "executed", "re_confirmed", "reversed")
        },
        "clearing": {k: v for k, v in cc.items() if not isinstance(v, (list, dict))},
        "uncleared_mw_by_fuel": cc.get("uncleared_mw_by_fuel"),
        "sector1_in_stack": {
            "units": len(s1_in_stack),
            "accredited_mw": round(sum(r[3] for r in s1_in_stack), 3),
        },
        "sector1_uncleared_retained": {
            "units": len(s1_uncleared),
            "accredited_mw": round(sum(r[3] for r in s1_uncleared), 3),
            "by_fuel": {
                f: round(sum(r[3] for r in s1_uncleared if r[1] == f), 3)
                for f in sorted({r[1] for r in s1_uncleared})
            },
        },
        "sector_gated": led.get("sector_gated"),
        "retirements_economic_mw": round(
            sum(
                float(r.get("mw") or 0.0)
                for r in (led.get("retirements") or [])
                if r.get("reason") == "economic"
            ),
            3,
        ),
        "retirements_mw": round(
            sum(float(r.get("mw") or 0.0) for r in (led.get("retirements") or [])), 3
        ),
        "footprint": {k: led.get(k) for k in FOOTPRINT_KEYS},
    }


def set_diff(a: dict, b: dict, sec: dict[int, int]) -> dict:
    """Rows in a not b / b not a / shared, with sector composition and MW."""

    def side(ids: set[str], src: dict) -> dict:
        comp: dict[str, int] = defaultdict(int)
        for u in ids:
            comp[sector_of(u, sec)] += 1
        return {
            "rows": len(ids),
            "mw": round(sum(src[u] for u in ids), 3),
            "sectors": dict(sorted(comp.items())),
        }

    only_a, only_b, both = set(a) - set(b), set(b) - set(a), set(a) & set(b)
    return {
        "only_first": side(only_a, a),
        "only_second": side(only_b, b),
        "shared": {
            "rows": len(both),
            "mw_first": round(sum(a[u] for u in both), 3),
            "mw_second": round(sum(b[u] for u in both), 3),
            "mw_identical": all(abs(a[u] - b[u]) <= 1e-6 for u in both),
        },
    }


def stack_diff(a: dict, b: dict) -> dict:
    """Offer-stack rows: identical (unit, fuel, offer≤1e-9, A_g≤1e-6, cleared)."""
    sa, sb = stack_rows(a), stack_rows(b)
    same = [
        u
        for u in sa
        if u in sb
        and sa[u][1] == sb[u][1]
        and abs(sa[u][2] - sb[u][2]) <= 1e-9
        and abs(sa[u][3] - sb[u][3]) <= 1e-6
        and sa[u][4] == sb[u][4]
    ]
    changed = [u for u in sa if u in sb and u not in same]
    return {
        "identical": len(same),
        "changed": len(changed),
        "only_first": len(set(sa) - set(sb)),
        "only_second": len(set(sb) - set(sa)),
        "changed_ids": sorted(changed)[:20],
        "only_first_ids": sorted(set(sa) - set(sb))[:20],
        "only_second_ids": sorted(set(sb) - set(sa))[:20],
    }


def near(x, y, tol) -> bool:
    return x is not None and y is not None and abs(float(x) - float(y)) <= tol


def gates(
    ctl: dict, d58: dict, arm: dict, ctl_led: dict, d58_led: dict, arm_led: dict, sec
) -> dict:
    """PRECOMMIT §3 G0-G6 on the 2022 screen; 2023 in fleet-delta form."""
    g: dict = {}
    c22, d22, a22 = ctl["2022"], d58["2022"], arm["2022"]
    # G0 — D58 reproduced to the MW (control AND D58's arm).
    kc, ka = D58_2022["control"], D58_2022["arm"]
    fc, fa = fail_rows(ctl_led["2022"]), fail_rows(d58_led["2022"])
    diff_cd = set_diff(fc, fa, sec)
    g0 = {
        "control": {
            "failing_rows": (c22["failing_rows"], kc["failing_rows"]),
            "failing_mw": (c22["failing_mw"], kc["failing_mw"]),
            "n_offers": (c22["clearing"].get("n_offers"), kc["n_offers"]),
            "offered_mw": (c22["clearing"].get("offered_mw"), kc["offered_mw"]),
            "price_takers_mw": (
                c22["clearing"].get("price_takers_mw"),
                kc["price_takers_mw"],
            ),
            "price": (c22["clearing"].get("price_usd_per_mw_day"), kc["price"]),
        },
        "d58_arm": {
            "failing_rows": (d22["failing_rows"], ka["failing_rows"]),
            "failing_mw": (d22["failing_mw"], ka["failing_mw"]),
            "n_offers": (d22["clearing"].get("n_offers"), ka["n_offers"]),
            "offered_mw": (d22["clearing"].get("offered_mw"), ka["offered_mw"]),
            "price_takers_mw": (
                d22["clearing"].get("price_takers_mw"),
                ka["price_takers_mw"],
            ),
            "price": (d22["clearing"].get("price_usd_per_mw_day"), ka["price"]),
            "only_in_arm": (
                diff_cd["only_second"]["rows"],
                diff_cd["only_second"]["mw"],
            ),
        },
        "control_minus_d58arm": diff_cd,
    }
    ok = (
        c22["failing_rows"] == kc["failing_rows"]
        and near(c22["failing_mw"], kc["failing_mw"], 0.06)
        and c22["clearing"].get("n_offers") == kc["n_offers"]
        and near(c22["clearing"].get("offered_mw"), kc["offered_mw"], 0.06)
        and near(c22["clearing"].get("price_takers_mw"), kc["price_takers_mw"], 0.06)
        and near(c22["clearing"].get("price_usd_per_mw_day"), kc["price"], 0.0006)
        and d22["failing_rows"] == ka["failing_rows"]
        and near(d22["failing_mw"], ka["failing_mw"], 0.06)
        and d22["clearing"].get("n_offers") == ka["n_offers"]
        and near(d22["clearing"].get("offered_mw"), ka["offered_mw"], 0.06)
        and near(d22["clearing"].get("price_takers_mw"), ka["price_takers_mw"], 0.06)
        and near(d22["clearing"].get("price_usd_per_mw_day"), ka["price"], 0.0006)
        and diff_cd["only_second"]["rows"] == ka["only_in_arm_rows"]
        and near(diff_cd["only_second"]["mw"], ka["only_in_arm_mw"], 0.06)
    )
    g0["pass"] = ok
    g["G0_d58_reproduced_to_the_mw"] = g0
    # G1 — the stack identity (arm vs control, 2022).
    sd = stack_diff(arm_led["2022"], ctl_led["2022"])
    g["G1_stack_identity"] = {
        "n_offers": (a22["clearing"].get("n_offers"), c22["clearing"].get("n_offers")),
        "offered_mw": (
            a22["clearing"].get("offered_mw"),
            c22["clearing"].get("offered_mw"),
        ),
        "price_takers_mw": (
            a22["clearing"].get("price_takers_mw"),
            c22["clearing"].get("price_takers_mw"),
        ),
        "requirement_mw": (
            a22["clearing"].get("requirement_mw"),
            c22["clearing"].get("requirement_mw"),
        ),
        "census_mw": (
            a22["clearing"].get("census_mw"),
            c22["clearing"].get("census_mw"),
        ),
        "stack_rows": sd,
        "pass": (
            a22["clearing"].get("n_offers") == c22["clearing"].get("n_offers")
            and near(
                a22["clearing"].get("offered_mw"),
                c22["clearing"].get("offered_mw"),
                1e-3,
            )
            and near(
                a22["clearing"].get("price_takers_mw"),
                c22["clearing"].get("price_takers_mw"),
                1e-3,
            )
            and near(
                a22["clearing"].get("requirement_mw"),
                c22["clearing"].get("requirement_mw"),
                1e-3,
            )
            and near(
                a22["clearing"].get("census_mw"), c22["clearing"].get("census_mw"), 1e-3
            )
            and sd["changed"] == 0
            and sd["only_first"] == 0
            and sd["only_second"] == 0
        ),
    }
    # G2 — the price identity.
    g["G2_price_identity"] = {
        "price": (
            a22["clearing"].get("price_usd_per_mw_day"),
            c22["clearing"].get("price_usd_per_mw_day"),
        ),
        "position": (
            a22["clearing"].get("cleared_position"),
            c22["clearing"].get("cleared_position"),
        ),
        "how": (a22["clearing"].get("how"), c22["clearing"].get("how")),
        "pass": (
            near(
                a22["clearing"].get("price_usd_per_mw_day"),
                c22["clearing"].get("price_usd_per_mw_day"),
                1e-6,
            )
            and near(
                a22["clearing"].get("cleared_position"),
                c22["clearing"].get("cleared_position"),
                1e-6,
            )
            and a22["clearing"].get("how") == c22["clearing"].get("how")
        ),
    }
    # G3 — the partition, exact.
    fa_arm = fail_rows(arm_led["2022"])
    diff_ca = set_diff(fc, fa_arm, sec)
    s1 = D58_2022["sector1_only_in_control"]
    g["G3_partition_exact"] = {
        "control_minus_arm": diff_ca,
        "arm_failing": (a22["failing_rows"], a22["failing_mw"]),
        "expected_arm_failing": (D58_2022["shared"]["rows"], D58_2022["shared"]["mw"]),
        "pass": (
            diff_ca["only_second"]["rows"] == 0
            and diff_ca["only_first"]["rows"] == s1["rows"]
            and near(diff_ca["only_first"]["mw"], s1["mw"], 0.06)
            and set(diff_ca["only_first"]["sectors"]) <= {"1"}
            and diff_ca["shared"]["mw_identical"]
            and a22["failing_rows"] == D58_2022["shared"]["rows"]
            and near(a22["failing_mw"], D58_2022["shared"]["mw"], 0.06)
        ),
    }
    # G4 — the convention's own identity.
    s1_rows_all = sum(arm[y]["sector1_pipeline_rows"] for y in arm)
    unk_rows_all = sum(arm[y]["unknown_pipeline_rows"] for y in arm)
    sg = a22.get("sector_gated") or {}
    g["G4_gated_units_offer_and_never_decide"] = {
        "sector1_pipeline_rows_2021_2023": s1_rows_all,
        "unknown_pipeline_rows_2021_2023": unk_rows_all,
        "sector1_in_2022_stack": a22["sector1_in_stack"],
        "sector1_uncleared_retained_2022": a22["sector1_uncleared_retained"],
        "sector_gated_2022": {
            k: sg.get(k)
            for k in ("units", "mw", "unknown_sector_units", "unknown_sector_mw")
        },
        "d58_sector_gated": D58_2022["sector_gated"],
        "pass": (
            s1_rows_all == 0
            and unk_rows_all == 0
            and a22["sector1_in_stack"]["units"] > 0
            and sg.get("units") == D58_2022["sector_gated"]["units"]
            and near(sg.get("mw"), D58_2022["sector_gated"]["mw"], 0.06)
        ),
    }
    # G5 — non-target footprint, 2022 identical; 2023 fleet-delta form.
    diffs22 = [
        k for k in FOOTPRINT_KEYS if a22["footprint"].get(k) != c22["footprint"].get(k)
    ]
    g5 = {"2022_differing_keys": diffs22}
    if "2023" in arm and "2023" in ctl:
        a23, c23 = arm["2023"], ctl["2023"]
        sd23 = stack_diff(arm_led["2023"], ctl_led["2023"])
        g5["2023"] = {
            "stack_rows_shared": sd23,
            "n_offers": (
                a23["clearing"].get("n_offers"),
                c23["clearing"].get("n_offers"),
                d58["2023"]["clearing"].get("n_offers"),
            ),
            "price": (
                a23["clearing"].get("price_usd_per_mw_day"),
                c23["clearing"].get("price_usd_per_mw_day"),
            ),
            "requirement_mw": (
                a23["clearing"].get("requirement_mw"),
                c23["clearing"].get("requirement_mw"),
            ),
            "census_mw": (
                a23["clearing"].get("census_mw"),
                c23["clearing"].get("census_mw"),
            ),
            "differing_keys": [
                k
                for k in FOOTPRINT_KEYS
                if a23["footprint"].get(k) != c23["footprint"].get(k)
            ],
        }
        g5["2023_pass"] = sd23["changed"] == 0 and near(
            a23["clearing"].get("requirement_mw"),
            c23["clearing"].get("requirement_mw"),
            1e-3,
        )
    g5["pass"] = not diffs22 and g5.get("2023_pass", True)
    g["G5_footprint"] = g5
    # G6 — the sign line restored.
    g6 = {}
    for y in ("2022", "2023"):
        if y in arm and y in ctl:
            g6[y] = {
                "arm_economic_exits_mw": arm[y]["retirements_economic_mw"],
                "control": ctl[y]["retirements_economic_mw"],
                "d58_arm": d58[y]["retirements_economic_mw"] if y in d58 else None,
                "d58_recorded": D58_EXITS[int(y)],
            }
    g6["pass"] = all(
        arm[y]["retirements_economic_mw"] <= ctl[y]["retirements_economic_mw"] + 1e-6
        for y in g6
        if y in ("2022", "2023")
    )
    g["G6_sign_line"] = g6
    g["ALL_PASS"] = all(v.get("pass") for k, v in g.items() if isinstance(v, dict))
    return g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl", required=True, type=Path)
    ap.add_argument("--d58", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023])
    ap.add_argument(
        "--out", type=Path, default=Path(__file__).with_name("screen_compare.json")
    )
    a = ap.parse_args()
    sec = sectors()
    legs = {
        "control": bundle_dir(a.ctl),
        "d58_arm": bundle_dir(a.d58),
        "arm": bundle_dir(a.arm),
    }
    leds = {k: {str(y): ledger(b, y) for y in a.years} for k, b in legs.items()}
    summ = {
        k: {y: year_summary(led, sec) for y, led in yl.items() if led is not None}
        for k, yl in leds.items()
    }
    out = {
        "legs": {k: str(v) for k, v in legs.items()},
        "meta": {
            k: json.loads((b.parent.parent / "meta.json").read_text())
            if (b.parent.parent / "meta.json").exists()
            else None
            for k, b in legs.items()
        },
        "summary": summ,
        "screen_gates": gates(
            summ["control"],
            summ["d58_arm"],
            summ["arm"],
            leds["control"],
            leds["d58_arm"],
            leds["arm"],
            sec,
        ),
    }
    a.out.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out["screen_gates"], indent=2, default=str))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
