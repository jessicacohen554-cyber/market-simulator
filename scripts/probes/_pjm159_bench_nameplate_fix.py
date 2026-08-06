#!/usr/bin/env python3
"""pjm-159 task C: prove the cross-ISO bench ``npl = 1 MW`` defect and its fix.

The defect (found by pjm-158 §1.1, fixed here): the bench payload's nameplate
lookup read only the OPERABLE EIA-860 vintage, so a plant that ran through part
of the backcast window and retired before that vintage was absent from it and
fell through the ``or 1.0`` guard to ``npl = 1 MW``. The per-plant hourly series
is stored as ``uint8 round(100 * mw / nameplate)`` clipped at 250, so a 1 MW
denominator saturates every real generation hour and the blob collapses to
``{0, 250}``.

What that costs, precisely — the finding said "destroyed", and this probe
sharpens it:

* **Energy is EXACT.** Consumers rescale by the committed ``c_ann``
  (``legitimacy_diagnostics._decode_cf_bytes``), so every annual sum is right.
  That is why no gate ever caught it.
* **The commitment pattern SURVIVES.** ``{0, 250}`` still says which hours the
  plant ran.
* **The loading profile inside committed hours is LOST.** The series is flat at
  one level whenever on, so part-load, ramping and within-run modulation are
  gone for that plant.

The fix unions the within-window retiree vintage — the same
``eia860_generator_retired_within_window.parquet`` the MODEL side already
consumes via ``fleet.load_retired_within_window`` for exactly this gap — with
the operable pass winning on conflict, so the change is purely additive.

Two checks, both no-LP, over every committed bench part:

1. **Population + recovery.** Every ``(ISO, year, plant)`` with ``npl <= 1`` and
   ``c_ann > 0.05 TWh``, the TWh stranded, and whether the union resolves it.
2. **Severity.** The byte histogram of each stranded blob, showing the
   collapse to a run indicator and the energy-exactness after rescaling.

Rule 25: this is a shared DATA-BUILDER defect, not a mechanism verdict — fixing
it transfers no verdict between ISOs. Rule 22: reads committed artifacts only;
no year is solved, scored or registered.

Usage::

    python scripts/probes/_pjm159_bench_nameplate_fix.py
    python scripts/probes/_pjm159_bench_nameplate_fix.py --json
"""

from __future__ import annotations

import argparse
import base64
import collections
import gzip
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BENCH = REPO / "frontend/data/backcast/bench"
#: A plant is "stranded" at this nameplate or below with material energy behind
#: it. 1 MW is the ``or 1.0`` guard's own value; the 0.05 TWh floor keeps genuine
#: 1 MW test/aux entries out of the population.
NPL_FLOOR_MW = 1.0
C_ANN_FLOOR_TWH = 0.05
#: ``render_calibration_html._b64``'s clip.
B64_CLIP = 250


def stranded_rows() -> list[dict]:
    """Every committed (ISO, year, plant key) carrying the defect signature."""
    rows: list[dict] = []
    for path in sorted(BENCH.glob("*/*.json.gz")):
        iso = path.parent.name
        year = int(path.stem.split(".")[0])
        with gzip.open(path) as fh:
            data = json.load(fh)
        for key, p in ((data.get("bench") or {}).get("plants") or {}).items():
            npl = float(p.get("npl") or 0.0)
            c_ann = float(p.get("c_ann") or 0.0)
            if npl > NPL_FLOOR_MW or c_ann <= C_ANN_FLOOR_TWH:
                continue
            rows.append(
                {
                    "iso": iso,
                    "year": year,
                    "key": str(key),
                    "code": int(str(key).split(":")[0]),
                    "bench_name": str(p.get("name") or "?"),
                    "group": str(p.get("group") or "?"),
                    "npl": npl,
                    "c_ann_twh": c_ann,
                    "campd": p.get("campd"),
                }
            )
    return rows


def severity(campd_b64: str, c_ann_twh: float) -> dict:
    """Byte histogram of a stranded blob + the energy-exactness check."""
    raw = np.frombuffer(base64.b64decode(campd_b64), dtype=np.uint8).astype(float)
    hist = collections.Counter(raw.astype(int).tolist())
    tot = raw.sum()
    # What the consumer actually reconstructs (legitimacy_diagnostics rescale).
    rebuilt_twh = (
        float((raw * (c_ann_twh * 1e6 / tot)).sum() / 1e6) if tot > 0 else 0.0
    )
    return {
        "distinct_bytes": len(hist),
        "pct_at_clip": round(100.0 * hist.get(B64_CLIP, 0) / raw.size, 1),
        "pct_zero": round(100.0 * hist.get(0, 0) / raw.size, 1),
        "n_partial": int(sum(v for k, v in hist.items() if 0 < k < B64_CLIP)),
        "run_hours": int((raw > 0).sum()),
        "rebuilt_twh": round(rebuilt_twh, 4),
        "energy_exact": abs(rebuilt_twh - c_ann_twh) < 1e-6,
    }


def main() -> None:
    """Print the population, the recovery and the severity characterization."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    import scripts.render_calibration_html as rch

    npl_map, nm_map = rch._eia860_plant_info()
    rows = stranded_rows()
    for r in rows:
        r["union_npl_mw"] = round(float(npl_map.get(r["code"], 0.0)), 1)
        r["union_name"] = str(nm_map.get(r["code"], "?"))
        r["recovered"] = r["union_npl_mw"] > NPL_FLOOR_MW
        r["severity"] = severity(r.pop("campd"), r["c_ann_twh"])

    before = sum(r["c_ann_twh"] for r in rows)
    after = sum(r["c_ann_twh"] for r in rows if not r["recovered"])
    by_iso: dict[str, float] = {}
    for r in rows:
        by_iso[r["iso"]] = by_iso.get(r["iso"], 0.0) + r["c_ann_twh"]

    result = {
        "probe": "pjm-159 task C: bench nameplate retiree-vintage fix",
        "union_plants": len(npl_map),
        "stranded_plant_years": len(rows),
        "twh_stranded_before": round(before, 2),
        "twh_stranded_after": round(after, 2),
        "twh_by_iso": {k: round(v, 2) for k, v in sorted(by_iso.items())},
        "all_recovered": after == 0.0,
        "rows": rows,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("=" * 78)
    print("pjm-159 task C — cross-ISO bench npl=1MW defect: population & recovery")
    print("=" * 78)
    print(f"EIA-860 union covers {len(npl_map)} plants (operable + within-window retiree)")
    print()
    print("ISO   yr   code  group        c_ann TWh  union npl MW  recovered  plant")
    for r in rows:
        print(
            f"{r['iso']:<6}{r['year']}  {r['code']:>5}  {r['group']:<12}"
            f"{r['c_ann_twh']:>9.2f}  {r['union_npl_mw']:>12.1f}  "
            f"{'YES' if r['recovered'] else 'NO ':>9}  {r['union_name'][:30]}"
        )
    print()
    print(f"stranded TWh by ISO: {result['twh_by_iso']}")
    print(
        f"TOTAL stranded {before:.2f} TWh  ->  after union {after:.2f} TWh"
        f"   ({'ALL RECOVERED' if after == 0 else 'RESIDUAL REMAINS'})"
    )

    print()
    print("=" * 78)
    print("severity — what the mis-denominated blob costs")
    print("=" * 78)
    print("ISO   yr   code  distinct  %at250  %zero  partial  run_h  energy exact?")
    for r in rows:
        s = r["severity"]
        print(
            f"{r['iso']:<6}{r['year']}  {r['code']:>5}  {s['distinct_bytes']:>8}"
            f"  {s['pct_at_clip']:>6}  {s['pct_zero']:>5}  {s['n_partial']:>7}"
            f"  {s['run_hours']:>5}  {'YES' if s['energy_exact'] else 'NO'}"
        )
    print()
    print(
        "Read: 3-4 distinct bytes means the series collapsed to a RUN INDICATOR.\n"
        "Energy is exact after the consumer's c_ann rescale (which is why no\n"
        "annual gate caught it) and the commitment pattern survives, but the\n"
        "loading profile inside committed hours is gone."
    )


if __name__ == "__main__":
    main()
