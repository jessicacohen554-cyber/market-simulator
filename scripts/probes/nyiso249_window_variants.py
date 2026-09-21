"""nyiso-249 — G-6: is there a measured upper-tail object in the hours the DEFICIT lives in?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Routing instrument for the successor.
PRECOMMIT addendum A2.

G-3 killed this lane's form as a C3c route: the P-27 book's registered TIGHT
window (``gas_bin >= 2 AND load_bin >= 2``) contains only **7 of 153** missed
hours. G-4 then measured **why** -- the missed hours sit at the top of the LOAD
distribution and NOT the gas one (2024: load-percentile p50 0.99 with 69 % at or
above p90, and **0.0 %** of the same hours reaching the gas p90).

**The obvious counter-argument to G-3 must be tested rather than dismissed:**
*"then condition the form on LOAD alone, where the deficit is."* It is refused
for this lane on identification grounds -- borrowing magnitudes measured in
gas-tight hours and applying them in load-tight hours is the
"measured here, applied there" error the derive's own PRECOMMIT section 1.1
rules on -- but that refusal only says the EXISTING numbers cannot be reused.
It says nothing about whether the object EXISTS under a load conditioner, and
that is a measurement, not an argument.

So this probe re-measures the book under three window variants, holding the
denominator at nyiso-248's corrected DAILY array throughout and changing only
the conditioner:

    W1  gas_bin >= 2 AND load_bin >= 2     the registered window (= ladder arm D)
    W2  load_bin >= 2 alone                the coordinate the DEFICIT lives on
    W3  gas_bin  >= 2 alone                the gas leg on its own, for attribution

Ordinary is each variant's own complement on the same axes (``bin == 0``), so
each variant is internally consistent rather than differenced against a window
built on a different coordinate.

**THIS LANE DOES NOT BUILD ON W2.** Whatever it measures, a form conditioned on
load needs its own PRECOMMIT, its own identification and its own gates -- a form
chosen in the session that found the evidence is precisely the selection
discipline this lane family exists to prevent (nyiso-246 section 6's own words).
The output here is a ROUTING number for a successor and is labelled as one.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_window_variants.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso249_window_variants.json"
REPORT_AT = (0.10, 0.25, 0.50, 0.75, 0.90, 0.99)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    from scripts.data.derive_nyiso_offer_level_dispersion import (
        QUANTILE_GRID,
        per_unit_delta,
        weighted_quantiles,
        year_unit_rows,
    )
    from scripts.data.derive_nyiso_offer_surface import (
        NETLOAD_PCTS,
        YEARS,
        net_load_by_year,
    )
    from scripts.probes.nyiso242_tail_reachability import missed_mask
    from scripts.probes.nyiso248_book_daily_regrain import daily_gas

    years = args.year or list(YEARS)
    nl = net_load_by_year()
    idx = {p: int(np.argmin(np.abs(QUANTILE_GRID - p))) for p in REPORT_AT}

    result: dict = {"gate": "G-6", "session": "nyiso-249", "variants": {}}
    frames: dict[str, list[pd.DataFrame]] = {"W1": [], "W2": [], "W3": []}
    per_year_meta: dict[str, dict] = {"W1": {}, "W2": {}, "W3": {}}

    for y in years:
        gas = daily_gas(y)
        load = np.asarray(nl[y], float)
        gb = np.searchsorted(np.quantile(gas, NETLOAD_PCTS), gas, side="right")
        lb = np.searchsorted(np.quantile(load, NETLOAD_PCTS), load, side="right")
        variants = {
            "W1": ((gb >= 2) & (lb >= 2), (gb == 0) & (lb == 0)),
            "W2": (lb >= 2, lb == 0),
            "W3": (gb >= 2, gb == 0),
        }
        # ONE corpus pass per year -- the rows depend only on the denominator.
        rows = year_unit_rows(y, gas)
        missed, _ = missed_mask(y)
        n = min(len(missed), 8760)

        for name, (t, o) in variants.items():
            d = per_unit_delta(rows, t, o)
            frames[name].append(d)
            cov = int((missed[:n] & t[:n]).sum())
            per_year_meta[name][str(y)] = {
                "tight_hours": int(t.sum()),
                "ordinary_hours": int(o.sum()),
                "n_gen_windows": int(len(d)),
                "n_missed": int(missed[:n].sum()),
                "n_missed_inside": cov,
                "coverage_of_missed": round(
                    float(cov / max(1, int(missed[:n].sum()))), 4
                ),
            }

    for name in ("W1", "W2", "W3"):
        pooled = pd.concat(frames[name], ignore_index=True)
        vec = weighted_quantiles(
            pooled["delta"].to_numpy(), pooled["w"].to_numpy(), QUANTILE_GRID
        )
        q = {f"p{int(p * 100)}": round(float(vec[idx[p]]), 4) for p in REPORT_AT}
        tot_missed = sum(v["n_missed"] for v in per_year_meta[name].values())
        tot_inside = sum(v["n_missed_inside"] for v in per_year_meta[name].values())
        result["variants"][name] = {
            "n_gen_windows": int(len(pooled)),
            "per_year": per_year_meta[name],
            "pooled_coverage_of_missed": round(
                float(tot_inside / max(1, tot_missed)), 4
            ),
            "quantiles": q,
            "full_vector": [round(float(x), 6) for x in vec],
        }

    label = {
        "W1": "gas>=p90 AND load>=p90 (registered)",
        "W2": "load>=p90 alone (the deficit's coordinate)",
        "W3": "gas>=p90 alone",
    }
    hdr = "  ".join(f"{'p' + str(int(p * 100)):>9}" for p in REPORT_AT)
    print(f"\n{'variant':<44} {'n':>6}  {hdr}   missed-coverage")
    for name, v in result["variants"].items():
        q = v["quantiles"]
        row = "  ".join(f"{q['p' + str(int(p * 100))]:>9.3f}" for p in REPORT_AT)
        print(
            f"{name + ' ' + label[name]:<44} {v['n_gen_windows']:>6}  {row}"
            f"   {v['pooled_coverage_of_missed']:.1%}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
