"""nwpp-45 phase 0 (ZERO LP): why CC_REGULAR is short, on its own terms.

Rebuilds the NWPP-44 designated keeper (``nwpp44_takeorpay_reg``) fleet through
the sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
path (``run_year(..., fleet_only=True)``), for every year of the keeper's span,
and reports the CC_REGULAR capacity/availability envelope against the dispatch
the keeper's committed ``hourly/`` sidecars already carry.

The charter's own diagnostic rule (lane NWPP-45): a UNIFORM shortfall points at
capacity/availability; a PEAK shortfall at commitment or offer level. The
committed sidecars say the 2023 miss is uniform across every load quintile, so
this probe measures the envelope rather than the offer.

Run: ``python3 scripts/probes/_nwpp45_ccregular_phase0.py [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp44_takeorpay_reg")
ISO = "NWPP"
KLASS = "CC_REGULAR"


def build(year: int):
    """Rebuild the keeper fleet for ``year`` on the keeper's own recipe."""
    import scripts.run_calibration as RC
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    return RC.run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _band(unit_id: str) -> str:
    suffix = str(unit_id).rpartition("_")[2]
    known = ("mustrun", "sync", "committed", "econlo", "econhi", "econ", "peak")
    return suffix if suffix in known or suffix.startswith("econc") else "<none>"


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    for year in years:
        out = build(year)
        fa = out["fleet_arrays"]
        avail = np.asarray(fa.availability, dtype=float)
        mc = np.asarray(out["mc_base"], dtype=float)
        if mc.ndim == 2:
            mc = mc.mean(axis=1)
        groups = [str(x) for x in np.asarray(fa.plant_group)]
        idx = [i for i, gname in enumerate(groups) if gname == KLASS]
        pmax = np.asarray(fa.pmax, dtype=float)[idx]
        av = avail[idx] if avail.ndim == 2 else np.tile(avail[idx][:, None], (1, 8760))
        env = (pmax[:, None] * av).sum(axis=0)  # hourly class upper bound, MW
        print(f"\n{'=' * 78}\nYEAR {year} — {KLASS}\n{'=' * 78}")
        print(f"  LP rows                : {len(idx)}")
        dem = np.asarray(out["demand"], dtype=float)
        print(f"  model demand           : {dem.sum() / 1e6:.3f} TWh")
        print(f"  Σ pmax (nameplate-ish) : {pmax.sum():,.1f} MW")
        print(
            f"  envelope mean / min / max : "
            f"{env.mean():,.0f} / {env.min():,.0f} / {env.max():,.0f} MW"
        )
        print(f"  mean availability       : {env.mean() / pmax.sum():.4f}")
        print(f"  envelope energy         : {env.sum() / 1e6:.3f} TWh")
        agg: dict[str, list] = defaultdict(lambda: [0.0, 0.0, 0.0])
        for k, i in enumerate(idx):
            b = _band(fa.unit_ids[i])
            agg[b][0] += pmax[k]
            agg[b][1] += float((pmax[k] * av[k]).sum()) / 1e6
            agg[b][2] += float(mc[i]) * pmax[k]
        print(f"\n  {'band':<12}{'Σpmax MW':>11}{'env TWh':>10}{'cap-wtd mc':>12}")
        for b, (p, e, mcw) in sorted(agg.items()):
            print(f"  {b:<12}{p:>11,.1f}{e:>10.3f}{mcw / p if p else 0:>12.2f}")


if __name__ == "__main__":
    main()
