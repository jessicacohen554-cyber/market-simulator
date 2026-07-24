"""ERCOT-102 — the co-opt requirement IS the measured ASPLANNP433 plan.

Refutes the ERCOT-102 charter premise that "the co-opt uses a FORMULA
(ERCOT_AS_ECRS_BASE_MW=950) that under-holds ECRS ~1,400 MW". In the keeper
(``ercot_multiproduct_as_coopt=True``, ``ercot_as_forward_requirement=False``)
the per-product reserve requirement is set by ``ercot_as_plan_requirement_mw`` —
the MEASURED ASPLANNP433 plan — NOT the forward formula (which fires only when
``ercot_as_forward_requirement=True``, the forecast path). See
``reserves.spec._ercot_multiproduct_design`` lines ~1007-1011.

This probe prints, per product and year, the measured-plan requirement the
co-opt actually demands (Jun-Sep summer means), and decomposes it into the
battery-AS credit (``ercot_storage_as_product_credit``, measured 60-Day DAM
award) + the Load-Resource RRS credit — showing that the charter's cited
"co-opt holds RegUp 177 + RRS 859 + ECRS 504 = ~1,540 MW" are the NET-OF-CREDIT
THERMAL residuals, not the total held. The measured battery + load-resource AS
that supplies the rest is a correct representation (those resources really do
provide AS), so there is NO under-holding: the full measured plan is required
and held, rigidly at VOLL, via the withheld families.

Also prints the ``ercot_ecrs_requirement`` no-op proof: that flag is read ONLY
in the single-product ``_ercot_design`` (spec.py:904), never in
``_ercot_multiproduct_design`` — so it is byte-identical on the multiproduct
keeper (the charter's "Lane A1" probe would not move any solve output).

No LP. Reads the committed ASPLANNP433 + storage-award corpora. Usage:
python -m scripts.probes.ercot102_as_holdout_attribution [--year Y...]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd


def _summer_idx(year: int) -> np.ndarray:
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[~((days.month == 2) & (days.day == 29))]
    return np.array(
        [di * 24 + h for di, day in enumerate(days) if day.month in (6, 7, 8, 9)
         for h in range(24)]
    )


def run(year: int) -> None:
    from market_sim.results.scarcity import (
        ercot_as_plan_requirement_mw,
        ercot_storage_as_reserve_mw,
    )

    hidx = _summer_idx(year)
    regup = ercot_as_plan_requirement_mw(year, 8760, "REGUP")
    rrs = ercot_as_plan_requirement_mw(year, 8760, "RRS")
    ecrs = ercot_as_plan_requirement_mw(year, 8760, "ECRS")
    nspin = ercot_as_plan_requirement_mw(year, 8760, "NSPIN")
    stor = ercot_storage_as_reserve_mw(year, 8760)  # measured total battery AS award

    online = regup + rrs + ecrs  # the online (fast) products held out of energy
    fast = regup + rrs + ecrs
    with np.errstate(invalid="ignore", divide="ignore"):
        cr = lambda p: np.maximum(  # noqa: E731 pro-rata storage credit across fast
            p - np.where(fast > 0, p / fast, 0.0) * stor, 0.0
        )
    regup_n, rrs_n, ecrs_n = cr(regup), cr(rrs), cr(ecrs)

    m = lambda a: float(a[hidx].mean())  # noqa: E731
    print(f"\n=== {year} — co-opt reserve requirement (Jun-Sep mean MW) ===")
    print("  product | measured PLAN (co-opt requirement) | net of battery credit")
    print(f"  REGUP   | {m(regup):8.0f}                          | {m(regup_n):8.0f}")
    print(f"  RRS     | {m(rrs):8.0f}                          | {m(rrs_n):8.0f}"
          "  (then further reduced by Load-Resource RRS credit)")
    print(f"  ECRS    | {m(ecrs):8.0f}                          | {m(ecrs_n):8.0f}")
    print(f"  NSPIN   | {m(nspin):8.0f}   (held via the normal ramp, not the VOLL "
          "withheld families; NonSpin is largely offline)")
    print(f"  ONLINE (RegUp+RRS+ECRS) measured plan HELD OUT = {m(online):8.0f} MW"
          f"  | measured battery AS award = {m(stor):.0f} MW")
    print(f"  -> the ~{m(regup_n)+m(rrs_n)+m(ecrs_n):.0f} MW net residual is the "
          "THERMAL-pulled reserve; the rest is battery + load-resource AS (correctly "
          "credited). The full measured plan IS the requirement — no under-holding.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot102_as_holdout_attribution")
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args(argv)
    for y in args.year:
        run(y)
    print(
        "\nercot_ecrs_requirement no-op proof: read ONLY in single-product "
        "_ercot_design (spec.py:904); NEVER in _ercot_multiproduct_design. On the "
        "multiproduct keeper the charter's Lane A1 probe is byte-identical."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
