"""nyiso-247 G-D — the per-year criterion table, keeper beside arm, at full magnitude.

The PRECOMMIT's duty (d) is that **C1 and C2 are reported at full magnitude
beside C3a / C3b / C3c for every scored year**, and duty P3 is that a C1/C2
degradation is REPORTED, never traded for price. This prints exactly that from
``scripts/calibration_verdict.py --json``, whose per-criterion ``records`` carry
each year's model value, actual, tolerance and signed magnitude — so both legs
are read out of the same scorer and nothing is re-derived here.

Usage::

    python3 scripts/calibration_verdict.py <run-id> --json > keeper.json
    python3 scripts/calibration_verdict.py <arm-id> --json > arm.json
    python3 scripts/probes/nyiso247_gate_table.py keeper.json arm.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: Scorer key -> the rubric label the PRECOMMIT names it by, in report order.
ROWS = (
    ("fuelmix", "C1 fuel-mix"),
    ("sysvol", "C2 system volume"),
    ("price_mean", "C3a mean LMP"),
    ("price_shape", "C3b price shape"),
    ("price_tail", "C3c price tail"),
    ("dispatch_corr", "C4 dispatch corr"),
    ("forced_share", "C8 forced share"),
)


def gated(crit: dict) -> list[dict]:
    """The GATED per-year records — diagnostic/skipped companions dropped."""
    return [
        r
        for r in crit.get("records", [])
        if r.get("status") in {"PASS", "FAIL", "CAVEAT"} and r.get("year") is not None
    ]


def main() -> None:
    legs = [(Path(p).stem, json.loads(Path(p).read_text())) for p in sys.argv[1:]]
    for name, d in legs:
        print(
            f"\n=== {name}  |  DETERMINATION {d.get('determination')}"
            f"  |  scorable {d.get('scorable_years')}"
        )
        for key, label in ROWS:
            crit = d.get("criteria", {}).get(key)
            if not isinstance(crit, dict):
                continue
            recs = gated(crit)
            print(f"  [{crit.get('status','?'):<6}] {label}")
            for r in recs:
                k = f" {r['key']}" if r.get("key") else ""
                cls = f"  [{r['classification']}]" if r.get("classification") else ""
                print(
                    f"        {r['status']:<7} {r['year']}{k}: {r.get('magnitude')}"
                    f"   (model {r.get('model')} vs {r.get('benchmark')} {r.get('actual')};"
                    f" tol {r.get('tol')}){cls}"
                )
    if len(legs) == 2:
        (kn, k), (an, a) = legs
        print(f"\n=== DELTA  {kn} -> {an} ===")
        for key, label in ROWS:
            kc, ac = k.get("criteria", {}).get(key), a.get("criteria", {}).get(key)
            if not isinstance(kc, dict) or not isinstance(ac, dict):
                continue
            km = {(r["year"], r.get("key")): r for r in gated(kc)}
            am = {(r["year"], r.get("key")): r for r in gated(ac)}
            flip = "" if kc.get("status") == ac.get("status") else \
                f"   *** {kc.get('status')} -> {ac.get('status')} ***"
            print(f"  {label}{flip}")
            for kk in sorted(set(km) | set(am), key=lambda x: (x[0], x[1] or "")):
                kr, ar = km.get(kk), am.get(kk)
                mark = "" if (kr and ar and kr["status"] == ar["status"]) else "  <<< STATUS MOVED"
                print(
                    f"        {kk[0]}{(' ' + kk[1]) if kk[1] else ''}: "
                    f"{(kr or {}).get('status','-')} {(kr or {}).get('magnitude','-')}"
                    f"  ->  {(ar or {}).get('status','-')} {(ar or {}).get('magnitude','-')}{mark}"
                )


if __name__ == "__main__":
    main()
