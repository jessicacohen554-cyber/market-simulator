#!/usr/bin/env python3
"""Phase-0 (ZERO LP): can MISO's measured seam ladder be derived for 2020-2022?

``docs/FINDING-miso252-seam-fallback-and-the-923-block-2026-09-10.md`` §3(a)
recorded the 2020-2022 seam ladder as BLOCKED on inputs, with
``eia-930-interchange/MISO interchange hourly.parquet`` covering "2023-2025"
as the binding blocker. **Both halves of that blocker were landed three days
later, on 2026-09-13**, and nothing re-checked it:

* the interchange extract now carries 2020-2026 (commit ``00249712``);
* ``_validation-source/actual_lmp_hourly_MISO.parquet`` gained MISO's 2020 and
  2021 hourly DA/RT hub LMPs (commit ``f9259f91``).

Those are the only two series ``scripts/data/derive_miso_seam_ladders.py``
reads to build the PRIMARY ladder (the PJM western-border series is a
diagnostic anchor for the *neighbour* overlays, not an input to the primary
Q-Q construction). This probe calls the FROZEN derive script's own functions —
it never re-implements them — and reports, per year:

* the derived primary ladder for every seam and direction;
* the frozen script's own ``offline_score`` P9 diagnostic, which simulates the
  band clearing on the MEASURED DA price and compares it to the MEASURED seam
  flow (volume, duration RMSE, import-hour share, hourly correlation);
* the incumbent's realized seam behaviour, read off the keeper's committed
  ``flows.parquet`` — the bang-bang signature miso-252 §2.4 measured.

Nothing here reads a price residual or a benchmark. It answers only "does the
mechanism's own arithmetic hold in these years", which is the rule 29
``[R-SCREEN]`` phase-0 question.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_miso_seam_ladders as D  # noqa: E402


def keeper_seam_flows(bundle: Path, year: int) -> dict[str, dict[str, float]]:
    """Bang-bang signature of the incumbent, from a committed ``flows.parquet``."""
    path = bundle / "flows.parquet"
    if not path.is_file():
        return {}
    f = pd.read_parquet(path)
    col = "link" if "link" in f.columns else f.columns[0]
    mwcol = "mw" if "mw" in f.columns else ("flow_mw" if "flow_mw" in f.columns else None)
    if mwcol is None:
        return {}
    out: dict[str, dict[str, float]] = {}
    for name, g in f.groupby(col):
        v = g[mwcol].to_numpy(dtype=float)
        if v.size == 0:
            continue
        hi = float(np.nanmax(np.abs(v)))
        if hi <= 0:
            continue
        at_max = float((np.abs(v) >= 0.99 * hi).mean())
        out[str(name)] = {
            "twh": float(v.sum() / 1e6),
            "max_abs_mw": hi,
            "pct_hours_within_1pct_of_max": 100.0 * at_max,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2020, 2021, 2022])
    ap.add_argument("--bundles", nargs="*", default=[])
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    df = D.load_joined()
    have = sorted(set(df.index.get_level_values("year")))
    print(f"joined (year, hour) frame covers: {have}")

    record: dict[str, dict] = {}
    for year in args.years:
        if year not in have:
            print(f"\n=== {year} === NOT COVERED by the joined frame")
            continue
        g = df.loc[[year]]
        gg = g.dropna(subset=["da"])
        ladders, notes = D.derive(g)
        print(f"\n=== {year} ===   MISO hub DA mean ${float(gg['da'].mean()):.2f}"
              f"  ({len(gg)} priced hours)")
        for seam, lad in ladders.items():
            print(f'    "{seam}": {{')
            print(f'        "import": {tuple(round(x, 2) for x in lad["import"])},')
            print(f'        "export": {tuple(round(x, 2) for x in lad["export"])},')
            print("    },")
        for n in notes:
            print(f"  note: {n}")
        scores = D.offline_score(g, ladders)
        for seam, s in scores.items():
            print(
                f"  offline P9 {seam}: {s['sim_twh']:+.2f} TWh vs {s['act_twh']:+.2f} "
                f"actual; duration RMSE {s['dur_rmse']:.0f} MW; import hours "
                f"{s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
                f"hourly corr {s['hourly_corr']:+.2f}"
            )
        record[str(year)] = {
            "ladders": {k: {d: list(v[d]) for d in ("import", "export")}
                        for k, v in ladders.items()},
            "notes": notes,
            "offline_score": scores,
        }

    for b in args.bundles:
        bp = Path(b)
        year = int(bp.name.rsplit("_", 1)[-1]) if bp.name.rsplit("_", 1)[-1].isdigit() else None
        if year is None:
            continue
        flows = keeper_seam_flows(bp, year)
        if not flows:
            continue
        print(f"\n--- incumbent realized seam flows, {bp.name} ({year}) ---")
        for name, v in sorted(flows.items()):
            print(f"  {name:<28} {v['twh']:+8.2f} TWh  max {v['max_abs_mw']:8.1f} MW  "
                  f"at-max {v['pct_hours_within_1pct_of_max']:5.1f}% of hours")
        record.setdefault(str(year), {})["incumbent_flows"] = flows

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
