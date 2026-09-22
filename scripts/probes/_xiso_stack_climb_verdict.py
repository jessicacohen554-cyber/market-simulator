"""xiso phase 0 — apply the PRE-REGISTERED verdict rule. ZERO LP, no re-measurement.

Reads the per-ISO-year blobs written by ``_xiso_stack_climb_phase0.py`` and
applies, mechanically, the test declared in
``docs/PRECOMMIT-xiso-stack-climb-attribution-2026-09-22.md`` §4 BEFORE any
number was computed:

  An ISO SHOWS THE SIGNATURE iff the MEDIAN over its scored years of
  "% availability-aware idle thermal in the top-1 % window" is >= 10 %.

    UNIVERSAL  iff >= 6 of 9 ISOs show it   (primary, as chartered)
    PER-ISO    otherwise

  Robustness leg, equally pre-registered: the same test over the 7
  PRICE-SCORED ISOs (the actual C3c population — SOCO and NWPP are
  price-unscored by owner registration and carry no C3c at all), at >= 5 of 7.
  If the two legs disagree the verdict is SPLIT and both are reported;
  neither is selected after the fact.

The threshold is READ FROM THIS MODULE'S CONSTANTS, which mirror the PRECOMMIT.
Nothing here is tunable by a result.

Run: python3 scripts/probes/_xiso_stack_climb_verdict.py --out <dir>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

# PRECOMMIT §4 — fixed before measuring, not moved after.
IDLE_PCT_THRESHOLD = 10.0
PRIMARY_MIN_ISOS, PRIMARY_N = 6, 9
ROBUST_MIN_ISOS, ROBUST_N = 5, 7
NO_PRICE_ISOS = ("SOCO", "NWPP")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    rows = [
        json.loads(p.read_text())
        for p in sorted(out.glob("*.json"))
        if not p.name.startswith("_")
    ]

    by_iso: dict[str, list] = {}
    for r in rows:
        by_iso.setdefault(r["iso"], []).append(r)

    unrec = [(r["iso"], r["year"], r["gates"]) for r in rows if not r["reconciled"]]

    print(f"{'ISO':6s} {'yr':>5s} {'avail GW':>9s} {'idle GW':>8s} {'idle %':>7s} "
          f"{'>clear %':>9s} {'model $':>8s} {'market $':>9s} {'max offer $':>11s}  basis")
    summary = {}
    for iso in sorted(by_iso):
        yrs = sorted(by_iso[iso], key=lambda r: r["year"])
        pcts = []
        for r in yrs:
            if not r["reconciled"]:
                print(f"{iso:6s} {r['year']:>5d}  UNRECONCILED — excluded")
                continue
            t, p = r["thermal_top1pct"], r["prices"]
            pcts.append(t["idle_pct"])
            mkt = f"{p['market_rt']:9.1f}" if p["market_rt"] is not None else "      n/a"
            print(f"{iso:6s} {r['year']:>5d} {t['available_mw']/1000:9.1f} "
                  f"{t['idle_mw']/1000:8.1f} {t['idle_pct']:7.1f} "
                  f"{t['above_clearing_pct']:9.1f} {p['model_clearing']:8.1f} {mkt} "
                  f"{p['highest_available_offer']:11.1f}  "
                  f"{'RT' if p['market_rt'] is not None else 'LOAD*'}")
        if pcts:
            med = median(pcts)
            summary[iso] = {"median_idle_pct": med, "years": len(pcts),
                            "shows": med >= IDLE_PCT_THRESHOLD,
                            "priced": iso not in NO_PRICE_ISOS}
            print(f"{iso:6s}   ->  median idle {med:.1f} %  "
                  f"{'SHOWS' if med >= IDLE_PCT_THRESHOLD else 'does not show'}"
                  f"{'' if iso not in NO_PRICE_ISOS else '   (price-unscored, load window)'}")
        print()

    shows = [i for i, v in summary.items() if v["shows"]]
    priced = [i for i, v in summary.items() if v["priced"]]
    shows_p = [i for i in shows if i in priced]

    print("=" * 78)
    print(f"PRE-REGISTERED THRESHOLD: median idle >= {IDLE_PCT_THRESHOLD:.0f} % of "
          f"availability-aware thermal, in the top-1 % window")
    prim = len(shows) >= PRIMARY_MIN_ISOS
    rob = len(shows_p) >= ROBUST_MIN_ISOS
    print(f"PRIMARY   {len(shows)}/{len(summary)} ISOs show it "
          f"(bar {PRIMARY_MIN_ISOS}/{PRIMARY_N})  -> "
          f"{'UNIVERSAL' if prim else 'PER-ISO'}")
    print(f"          shows: {', '.join(sorted(shows)) or '(none)'}")
    print(f"          not:   {', '.join(sorted(set(summary) - set(shows))) or '(none)'}")
    print(f"ROBUST    {len(shows_p)}/{len(priced)} price-scored ISOs show it "
          f"(bar {ROBUST_MIN_ISOS}/{ROBUST_N})  -> "
          f"{'UNIVERSAL' if rob else 'PER-ISO'}")
    verdict = ("UNIVERSAL" if prim and rob else
               "PER-ISO" if not prim and not rob else "SPLIT")
    print(f"VERDICT   {verdict}")
    if unrec:
        print(f"UNRECONCILED ISO-years (excluded): {[(i, y) for i, y, _ in unrec]}")
    print("=" * 78)

    (out / "_verdict.json").write_text(json.dumps(
        {"threshold_pct": IDLE_PCT_THRESHOLD, "per_iso": summary,
         "primary": {"shows": len(shows), "of": len(summary),
                     "bar": PRIMARY_MIN_ISOS, "result": "UNIVERSAL" if prim else "PER-ISO"},
         "robustness": {"shows": len(shows_p), "of": len(priced),
                        "bar": ROBUST_MIN_ISOS, "result": "UNIVERSAL" if rob else "PER-ISO"},
         "verdict": verdict,
         "unreconciled": [{"iso": i, "year": y} for i, y, _ in unrec]}, indent=1))


if __name__ == "__main__":
    main()
