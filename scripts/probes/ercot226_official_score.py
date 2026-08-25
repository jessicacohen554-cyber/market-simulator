"""ercot-226: OFFICIAL-basis C3a/C3b/C3c scorer for an UNREGISTERED bundle.

Reproduces, to the printed digit, the registered pipeline's official price
criteria for a bundle that has NOT been through ``dashboard_add_run`` —
so 2023-only probes can be adjudicated on the determination currency
(PRECOMMIT-ercot226-held-sequestration-2026-08-22 §5.1) without violating
the W-2 no-probe-registration waiver.

Replication chain (verbatim constructions, never re-derived conceptually):

* payload ``lmp`` block — ``scripts/render_calibration_html.py`` (~:2140-2260):
  per zone, ``p = round(sum(price*demand)/sum(demand), 2)``,
  ``d = round(sum(demand)/1e6, 4)``, ``pMon[m]``/``dMon[m]`` the same per
  month via the non-leap cumulative month-hour edges; the model series is the
  system sidecar's ``price`` column of the PRIMARY pass (P1 here — the
  keeper is P1-only), which already carries the model's own adder columns.
* C3a — ``calibration_verdict.score_price_mean``: ``_wmean`` of the zone
  ``(p, d)`` pairs vs bench ``avgLMP.rt_lw``; magnitude ``{err*100:+.1f}%``.
* C3b — ``calibration_verdict.score_price_shape``: monthly ``_wmean`` of
  ``(pMon, dMon)`` vs ``rt_lw_mon``; ``_nrmse`` printed ``.3f``.
* C3c — ``render_calibration_html._tail_hours``: hours whose MAX zonal
  ``price`` exceeds $200 (NaN -> -inf), vs
  ``frontend/data/backcast/tail/actual_tail.json`` ``isos.ERCOT.<y>.rt_gt``.
  (No post-solve scarcity overlay sidecar exists on this lineage's bundles —
  verified on the keeper — so the payload's gated count is the ``model``
  count; a bundle that DID carry ``scarcity*.parquet`` would need the G-20a
  overlay branch this scorer deliberately refuses rather than mis-scores.)

VALIDATION GATE (precommit §5.1): ``--validate-keeper`` runs the scorer on
``results/calibration/ercot231_tiegtc_full`` and hard-asserts the keeper's
registered values: 2023 −38.0 % / 0.696 / 93 h; 2024 +0.4 % / 0.130 / 22 h;
2025 −7.7 % / 0.099 / 1 h. No probe may be scored before this passes.
(Re-pointed at ercot-234 from the superseded ``ercot223_release_arm``
expectations, which the ercot-231 promotion left stale; the scorer itself is
unchanged and reproduced both keepers' registered values exactly.)

Run:
    python scripts/probes/ercot226_official_score.py --validate-keeper
    python scripts/probes/ercot226_official_score.py --bundle <dir> --years 2023
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT"
TAIL_JSON = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot231_tiegtc_full"

#: Non-leap cumulative month-start hours (render_calibration_html._CUM).
_CUM = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
TAIL_THRESHOLD = 200.0  # ERCOT (calibration_verdict.TAIL_THRESHOLD default)

#: The keeper's registered official values (frontend payload + bench,
#: reproduced 2026-08-25 on ercot231_tiegtc_full): {year: (c3a magnitude,
#: c3b nrmse, c3c model h)}.
KEEPER_EXPECT = {
    2023: ("-38.0%", "0.696", 93),
    2024: ("+0.4%", "0.130", 22),
    2025: ("-7.7%", "0.099", 1),
}


def _wmean(pairs):
    """Demand-weighted mean of (value, weight) pairs (calibration_verdict)."""
    w = sum(wt for _, wt in pairs)
    if w <= 0:
        return None
    return sum(v * wt for v, wt in pairs) / w


def _nrmse(model, actual):
    """Normalised RMSE over non-None monthly cells (calibration_verdict)."""
    cells = [(m, a) for m, a in zip(model, actual) if m is not None and a is not None]
    if not cells:
        return None
    mean_a = sum(a for _, a in cells) / len(cells)
    if abs(mean_a) < 1e-9:
        return None
    rmse = math.sqrt(sum((m - a) ** 2 for m, a in cells) / len(cells))
    return rmse / mean_a


def _bench(year: int) -> dict:
    import gzip

    with gzip.open(BENCH_DIR / f"{year}.json.gz") as f:
        return json.load(f)["bench"]


def score_year(bundle: Path, year: int, hours: int = 8760) -> dict:
    """One bundle-year's official C3a/C3b/C3c, replicating the payload chain."""
    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sy = sy[sy["year"] == year]
    passes = set(sy["pass"].unique())
    if "P2" in passes:  # this lineage is P1-only; refuse rather than mis-score
        raise SystemExit(f"{bundle}: P2 frame present — _primary_pass would "
                         "select it; this scorer only handles P1-only bundles")
    sy = sy[sy["pass"] == "P1"]
    for name in ("scarcity_reldeploy2500.parquet", "scarcity.parquet"):
        if (bundle / name).exists():
            raise SystemExit(f"{bundle}: {name} present — G-20a overlay branch "
                             "not implemented here; score via registration")

    pairs, mon_pairs = [], [[] for _ in range(12)]
    price_by_zone = {}
    for zone, zg in sy.groupby("zone", observed=True):
        price = zg["price"].to_numpy(float)
        dem = zg["demand"].to_numpy(float)
        hr = zg["hour"].to_numpy()
        full = np.full(hours, np.nan)
        full[hr] = price
        price_by_zone[str(zone)] = full
        d_tot = float(dem.sum())
        p = float((price * dem).sum()) / d_tot if d_tot > 0 else float(price.mean())
        pairs.append((round(p, 2), round(d_tot / 1e6, 4)))
        midx = np.clip(np.searchsorted(_CUM, hr, side="right") - 1, 0, 11)
        for m in range(12):
            sel = midx == m
            if not sel.any():
                continue
            dd = float(dem[sel].sum())
            pm = (
                round(float((price[sel] * dem[sel]).sum()) / dd, 2)
                if dd > 0
                else round(float(price[sel].mean()), 2)
            )
            mon_pairs[m].append((pm, round(dd / 1e6, 4)))

    model_mean = _wmean(pairs)
    rt_lw = _bench(year)["avgLMP"]["rt_lw"]
    err = (model_mean - rt_lw) / rt_lw
    model_mon = [_wmean(mp) if mp else None for mp in mon_pairs]
    rt_lw_mon = _bench(year)["avgLMP"]["rt_lw_mon"]
    nrmse = _nrmse(model_mon, rt_lw_mon)
    stack = np.vstack([v for v in price_by_zone.values()])
    stack = np.nan_to_num(stack, nan=-np.inf)
    tail_model = int((stack.max(axis=0) > TAIL_THRESHOLD).sum())
    tail_actual = json.loads(TAIL_JSON.read_text())["isos"]["ERCOT"][str(year)][
        "rt_gt"
    ]
    return {
        "year": year,
        "c3a_model": round(model_mean, 2),
        "c3a_actual": round(rt_lw, 2),
        "c3a_magnitude": f"{err * 100:+.1f}%",
        "c3b_nrmse": f"{nrmse:.3f}",
        "c3c_model_h": tail_model,
        "c3c_actual_rt_h": int(tail_actual),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, default=KEEPER_BUNDLE)
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--validate-keeper", action="store_true")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    if args.validate_keeper:
        args.bundle, args.years = KEEPER_BUNDLE, sorted(KEEPER_EXPECT)
    rows = [score_year(args.bundle, y) for y in args.years]
    for r in rows:
        print(
            f"[{r['year']}] C3a {r['c3a_magnitude']} "
            f"(model {r['c3a_model']} vs RT lw {r['c3a_actual']}) | "
            f"C3b NRMSE {r['c3b_nrmse']} | "
            f"C3c {r['c3c_model_h']} h vs RT {r['c3c_actual_rt_h']} h"
        )
    if args.validate_keeper:
        ok = True
        for r in rows:
            e = KEEPER_EXPECT[r["year"]]
            got = (r["c3a_magnitude"], r["c3b_nrmse"], r["c3c_model_h"])
            if got != e:
                ok = False
                print(f"VALIDATION MISMATCH {r['year']}: got {got}, expect {e}")
        if not ok:
            raise SystemExit("scorer validation FAILED — fix before any probe")
        print("VALIDATION OK: scorer reproduces the keeper's registered "
              "official values exactly")
    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=1))
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
