"""miso-145 probe — measure the universe crossing instead of inferring it.

FINDING `results/calibration/FINDING-miso145-offer-conduct-2026-08-09.md` §5.
Gate **G-F2** reconciles the corpus's offered capability against the model's
available capability and PASSES on its number — but the pass is a cancellation
of two large, opposite composition differences:

* the model's fleet carries import tranches the offer corpus has no analogue
  for (an offer book of MISO-internal resources), and
* the corpus carries MISO's wind and solar as offer rows, which the model does
  not represent as generator rows at all (they are LP decision variables with
  MC = 0).

This probe **measures both sides of that cancellation** rather than asserting
it, so §5's disqualification of the level leg rests on numbers:

* corpus MW offered at or below $0 / $5 / $10 per MWh in the window, per market;
* the keeper's own sidecar wind + solar dispatch in the same hours.

Window means are UNWEIGHTED (a composition statistic, not a price statistic),
which is why they differ slightly from the load-weighted capability totals in
``_miso145_offer_conduct.json``; both are reported in the finding.

**No LP solve.** Reuses ``_miso145_offer_conduct.load_real_segments`` and the
keeper's committed class sidecar. Probe hygiene (miso-140b §6) comes in through
``_miso143_stack.hygiene``.

Usage::

    python scripts/probes/_miso145_cheap_mass.py [--out results/calibration/_miso145_cheap_mass.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import hygiene, sidecar_classes, windows  # noqa: E402
from _miso145_offer_conduct import load_real_segments  # noqa: E402

#: Price bands at which the corpus's near-zero-priced mass is counted.
BANDS = (0.0, 5.0, 10.0)


def run(year: int = 2025, window: str = "JJA_h12_17", out_path: Path | None = None) -> dict:
    """Measure the corpus's cheap mass and the model's variable-renewable dispatch."""
    hygiene()
    hours = np.nonzero(windows()[window])[0]
    n = int(hours.size)

    out: dict = {
        "finding": "results/calibration/FINDING-miso145-offer-conduct-2026-08-09.md",
        "gate": "G-F2 addendum -- measures the universe crossing behind the gate's numeric pass",
        "year": year,
        "window": window,
        "n_hours": n,
        "basis": "UNWEIGHTED window means (a composition statistic, not a price statistic)",
        "corpus": {},
    }
    for market in ("RT", "DA"):
        segs = load_real_segments(year, market, hours)
        row = {
            f"mw_le_{thr:g}_gw": round(
                float(segs.loc[segs["seg_price"] <= thr, "seg_mw"].sum() / n / 1000.0), 3
            )
            for thr in BANDS
        }
        row["total_gw"] = round(float(segs["seg_mw"].sum() / n / 1000.0), 3)
        out["corpus"][market] = row

    piv = sidecar_classes(year)
    model = {
        c: round(float(piv[c].to_numpy(float)[hours].mean() / 1000.0), 3)
        for c in ("wind", "solar")
        if c in piv.columns
    }
    model["wind_plus_solar_gw"] = round(sum(model.values()), 3)
    out["model_sidecar_variable_renewables"] = model

    if out_path:
        out_path.write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", default="results/calibration/_miso145_cheap_mass.json", type=Path
    )
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()
    res = run(year=args.year, out_path=args.out)
    print(json.dumps(res["corpus"], indent=1))
    print(json.dumps(res["model_sidecar_variable_renewables"], indent=1))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
