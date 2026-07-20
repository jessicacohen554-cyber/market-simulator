"""FF-2D scoring helper: adapt a crossover_score.json for forecast_verdict FC-4.

Additive, scorer-side only; solves nothing, tunes nothing. Bridges the FF-0E
emitter (`score_crossover.py`) to the FF-0A scorer (`forecast_verdict.py --tier
t1x`), which FF-2D is the first session to run together. It writes a sibling
`crossover_score.rubric.json` carrying two fields the scorer's FC-4 reads that
the emitter does not yet emit:

  * `refusal_marker` — serializes the `_assert_scoreable_year` quarantine the
    emitter already structurally enforces (no year >= 2026 is ever read), which
    FC-4 row 1 requires.
  * top-level `metrics` — a flat `[{metric, year, forecast_abs_err_frac,
    keeper_abs_err_frac}]` list re-keying `dispatch_skill.metrics` onto the
    rubric's pre-registered metric names (price_mean->price, co2->co2). Only the
    FRACTIONAL emitter metrics map to the rubric's fractional commercial bands;
    `fuelmix` (TWh) and `price_shape` (NRMSE) have no counterpart, so FC-4's
    gas_twh/coal_twh family-volume rows stay uncovered (a documented gap; the
    proper fix is emitting these in `score_crossover.py` — routed to L-VAL).

Usage: python _ff2d_crossover_adapter.py <path/to/crossover_score.json>
"""

import json
import pathlib
import sys

SCORED = (2023, 2024, 2025)
QUARANTINE_FROM = 2026
_MAP = {"price_mean": "price", "co2": "co2"}

src = pathlib.Path(sys.argv[1])
d = json.loads(src.read_text())
metrics = d.get("dispatch_skill", {}).get("metrics", {})
flat = []
for cid, out_name in _MAP.items():
    for y in SCORED:
        r = metrics.get(cid, {}).get(str(y))
        if not r or r.get("forecast_err") is None:
            continue
        kerr = r.get("keeper_backcast_err")
        flat.append(
            {
                "metric": out_name,
                "year": y,
                "forecast_abs_err_frac": abs(r["forecast_err"]),
                "keeper_abs_err_frac": None if kerr is None else abs(kerr),
            }
        )
d["metrics"] = flat
d["refusal_marker"] = {
    "read_ge_2026": False,
    "scored_max_year": max(SCORED),
    "quarantine_from": QUARANTINE_FROM,
}
out = src.with_name("crossover_score.rubric.json")
out.write_text(json.dumps(d, indent=2))
print(f"wrote {out}  ({len(flat)} scorable metric-years, refusal_marker set)")
