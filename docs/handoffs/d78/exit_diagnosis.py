"""capx D78 — WHY G6 fired: decompose the executed economic exits of each
screen year across the three legs, unit by unit, from the committed ledgers
(zero LP). Writes ``exit_diagnosis.json`` beside this file.

    uv run python docs/handoffs/d78/exit_diagnosis.py --ctl <dir> --d58 <dir> --arm <dir>
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

from screen_compare import plant_code, sectors  # noqa: E402  (same directory)


def bundle_dir(out_dir: Path) -> Path:
    hits = glob.glob(str(out_dir / "PJM" / "*" / ""))
    assert len(hits) == 1, (out_dir, hits)
    return Path(hits[0])


def led(b: Path, y: int) -> dict:
    return json.loads((b / f"evolution_{y}.json").read_text())


def econ_exits(L: dict) -> dict[str, dict]:
    return {
        r["unit_id"]: r
        for r in L.get("retirements") or []
        if r.get("reason") == "economic"
    }


def events_by_unit(L: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for e in L.get("pipeline_events") or []:
        out[e["unit_id"]].append(e)
    return out


def by_fuel(rows: dict[str, dict]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in rows.values():
        out[r["fuel"]] += float(r["mw"])
    return {k: round(v, 3) for k, v in sorted(out.items())}


def decomposition(
    a: dict, b: dict, label_a: str, label_b: str, sec, ev_a, ev_b
) -> dict:
    only_a = {u: r for u, r in a.items() if u not in b}
    only_b = {u: r for u, r in b.items() if u not in a}
    both = {u: r for u, r in a.items() if u in b}

    def status(u: str, ev: dict) -> str:
        kinds = [e["event"] for e in ev.get(u, [])]
        return "+".join(kinds) if kinds else "none"

    def side(rows: dict, ev_self, ev_other) -> dict:
        comp: dict[str, int] = defaultdict(int)
        for u in rows:
            c = plant_code(u)
            comp[str(sec[c]) if c in sec else "unknown"] += 1
        return {
            "rows": len(rows),
            "mw": round(sum(float(r["mw"]) for r in rows.values()), 3),
            "by_fuel": by_fuel(rows),
            "sectors": dict(sorted(comp.items())),
            "units": [
                {
                    "unit_id": u,
                    "fuel": r["fuel"],
                    "mw": round(float(r["mw"]), 3),
                    "self_events": status(u, ev_self),
                    "other_leg_events": status(u, ev_other),
                }
                for u, r in sorted(rows.items())
            ],
        }

    return {
        f"only_{label_a}": side(only_a, ev_a, ev_b),
        f"only_{label_b}": side(only_b, ev_b, ev_a),
        "shared": {
            "rows": len(both),
            "mw": round(sum(float(r["mw"]) for r in both.values()), 3),
        },
    }


def admitted(L: dict) -> dict:
    ev = L.get("pipeline_events") or []
    dec = [e for e in ev if e["event"] == "decided"]
    cap = [e for e in ev if e["event"] == "entry_capped"]
    exe = [e for e in ev if e["event"] == "executed"]
    return {
        "decided_rows": len(dec),
        "decided_mw": round(sum(e["mw"] for e in dec), 3),
        "decided_by_fuel": by_fuel({e["unit_id"]: e for e in dec}),
        "decided_by_execute_year": {
            str(y): round(sum(e["mw"] for e in dec if e.get("execute_year") == y), 3)
            for y in sorted({e.get("execute_year") for e in dec})
        },
        "capped_rows": len(cap),
        "capped_mw": round(sum(e["mw"] for e in cap), 3),
        "capped_by_fuel": by_fuel({e["unit_id"]: e for e in cap}),
        "executed_rows": len(exe),
        "executed_mw": round(sum(e["mw"] for e in exe), 3),
        "executed_by_fuel": by_fuel({e["unit_id"]: e for e in exe}),
        "floor_retained_mw": round(
            sum(r["mw"] for r in L.get("floor_retained") or []), 3
        ),
        "throughput_deferred_mw": round(
            sum(r["mw"] for r in L.get("throughput_deferred") or []), 3
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl", required=True, type=Path)
    ap.add_argument("--d58", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument(
        "--out", type=Path, default=Path(__file__).with_name("exit_diagnosis.json")
    )
    a = ap.parse_args()
    sec = sectors()
    legs = {
        "ctl": bundle_dir(a.ctl),
        "d58": bundle_dir(a.d58),
        "arm": bundle_dir(a.arm),
    }
    out: dict = {}
    for y in (2022, 2023):
        L = {k: led(b, y) for k, b in legs.items()}
        ex = {k: econ_exits(v) for k, v in L.items()}
        ev = {k: events_by_unit(v) for k, v in L.items()}
        out[str(y)] = {
            "economic_exits_mw": {
                k: round(sum(float(r["mw"]) for r in v.values()), 3)
                for k, v in ex.items()
            },
            "economic_exits_by_fuel": {k: by_fuel(v) for k, v in ex.items()},
            "admission": {k: admitted(v) for k, v in L.items()},
            "arm_vs_ctl": decomposition(
                ex["arm"], ex["ctl"], "arm", "ctl", sec, ev["arm"], ev["ctl"]
            ),
            "d58_vs_ctl": decomposition(
                ex["d58"], ex["ctl"], "d58", "ctl", sec, ev["d58"], ev["ctl"]
            ),
        }
    a.out.write_text(json.dumps(out, indent=2))
    for y, d in out.items():
        print(f"== {y}: economic exits {d['economic_exits_mw']}")
        for k, v in d["admission"].items():
            print(
                f"   {k}: decided {v['decided_mw']} ({v['decided_rows']}) by exec year {v['decided_by_execute_year']}; "
                f"capped {v['capped_mw']} ({v['capped_rows']}); executed {v['executed_mw']} ({v['executed_rows']}) {v['executed_by_fuel']}; "
                f"floor_retained {v['floor_retained_mw']}; deferred {v['throughput_deferred_mw']}"
            )
        dd = d["arm_vs_ctl"]
        print(
            f"   arm-only exits: {dd['only_arm']['rows']} rows / {dd['only_arm']['mw']} MW {dd['only_arm']['by_fuel']} sectors {dd['only_arm']['sectors']}"
        )
        for u in dd["only_arm"]["units"][:12]:
            print(
                f"      {u['unit_id']} {u['fuel']} {u['mw']} arm:{u['self_events']} ctl:{u['other_leg_events']}"
            )
        print(
            f"   ctl-only exits: {dd['only_ctl']['rows']} rows / {dd['only_ctl']['mw']} MW {dd['only_ctl']['by_fuel']} sectors {dd['only_ctl']['sectors']}"
        )
        for u in dd["only_ctl"]["units"][:12]:
            print(
                f"      {u['unit_id']} {u['fuel']} {u['mw']} ctl:{u['self_events']} arm:{u['other_leg_events']}"
            )
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
