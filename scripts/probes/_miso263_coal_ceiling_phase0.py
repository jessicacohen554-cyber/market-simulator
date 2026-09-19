#!/usr/bin/env python3
"""Phase 0 (ZERO LP): is MISO's coal fuel-inventory ceiling BINDING, and was it ENFORCED?

The object handed to miso-263. At its true (cold, year-isolated) optimum the
designated keeper ``2026-09-19-miso-262-cold-year`` fills the gap 2022's $6.45
gas leaves with **+32.08 TWh of surplus COAL_PRB** and **+10.42 TWh COAL_BIT**
the real market did not burn, against **-28.20 TWh CC_REGULAR**. The named
hypothesis was that the model has *no binding coal SUPPLY ceiling*.
``coal_fuel_inventory`` exists for exactly that ("the missing CEILING on coal")
and IS armed in the keeper's ``run_config_2022.json`` -- so the question is not
whether the mechanism is declared but whether its cap actually **bit**.

THE DECISIVE STATISTIC, and why it needs no class crosswalk
------------------------------------------------------------

The bundle persists no dual for the budget rows, so "did it bind" cannot be
read off directly. It can be **proved** instead. The LP row for month ``m`` is::

    sum_{g in coal fleet, t in m} HR[g] * P[g, t]  <=  CAP[m]      (MMBtu)

subject to ``0 <= P[g,t] <= pmax[g] * availability[g,t]``. So the MOST coal
ENERGY the fleet can deliver in month ``m`` without violating the row is got by
spending the MMBtu budget on the most efficient units first::

    max_mwh[m] = greedy fill of CAP[m] over units sorted by heat rate ascending,
                 each unit capped at sum_t pmax[g] * availability[g,t]

``max_mwh[m]`` is an **upper bound that holds for every feasible dispatch**,
whatever the class mix, whatever the offers, whatever else binds. It is
therefore a one-sided proof: if the committed sidecar's own P1 coal MWh for
that month EXCEEDS ``max_mwh[m]``, no dispatch satisfying the row could have
produced it, and the row was **not enforced in the solve that wrote the
sidecar**. (The converse is not claimed: coal under the bound proves nothing
either way, which is why the bound is reported beside the physical ceiling.)

Everything here is read from committed bytes plus a ``fleet_only`` rebuild
(rule 32 ``[R-SHARD]`` (a): the parent never solves; rule 29 ``[R-SCREEN]``
clause 0: a zero-LP answer is preferred to a solve). The budget itself comes
from :func:`market_sim.data.coal_fuel_inventory.build_coal_fuel_budget` called
on the fleet the solve built -- the identical call
``scripts/run_calibration.py`` makes, so the MMBtu here is the bound the
constraint carried, not a re-derivation.

The warm comparison
--------------------

The superseded keeper ``2026-09-16-miso-260-seam-ladder`` was removed from the
working tree by this session's rule-35 prune, so its side of the contrast is
read out of git history (``--warm-ref``). miso-259 measured the binding
signature on that run -- implied heat rate 11.056-11.621 across seven 2022
months, tight around the fleet's dispatch-weighted 11.320 -- and read the
tightness as each row binding exactly at its cap. Both runs declare
``coal_fuel_inventory: true``.

Usage::

    python scripts/probes/_miso263_coal_ceiling_phase0.py
    python scripts/probes/_miso263_coal_ceiling_phase0.py --years 2022
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.coal_fuel_inventory import (  # noqa: E402
    build_coal_fuel_budget,
    coal_gen_idx,
)
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402
from scripts.replay_keeper import (  # noqa: E402
    derived_run_year_inputs,
    run_year_kwargs,
)
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso262_cold_span"
WARM_BUNDLE = "results/calibration/miso260_seam_span"
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)


def _monthly_coal_mwh(df: pd.DataFrame) -> np.ndarray:
    """Collapse a class sidecar to 12 monthly P1 coal MWh totals."""
    df = df[(df["pass"] == "P1") & df["klass"].str.upper().str.startswith("COAL")]
    month = _hour_to_month_index(8760)
    m = month[df["hour"].to_numpy().astype(int)]
    out = np.zeros(12)
    np.add.at(out, m, df["mw"].to_numpy(dtype=float))
    return out


def model_coal_monthly_mwh(bundle: Path, year: int) -> np.ndarray:
    """Per-month P1 coal MWh from a committed class sidecar on disk."""
    return _monthly_coal_mwh(
        pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    )


def warm_coal_monthly_mwh(ref: str, year: int) -> np.ndarray | None:
    """The same table for the SUPERSEDED warm keeper, read out of git history."""
    path = f"{ref}:{WARM_BUNDLE}/hourly/class_hourly_{year}.parquet"
    try:
        blob = subprocess.run(
            ["git", "show", path], cwd=REPO, capture_output=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return _monthly_coal_mwh(pd.read_parquet(io.BytesIO(blob)))


def max_mwh_under_cap(hr: np.ndarray, cap_mwh: np.ndarray, budget: float) -> float:
    """Greatest coal MWh deliverable in a month without exceeding ``budget`` MMBtu.

    Efficiency-ordered greedy fill: the cheapest MMBtu-per-MWh capacity is spent
    first, so no feasible dispatch can beat it. ``cap_mwh[g]`` is unit ``g``'s
    energy headroom for the month (``sum_t pmax * availability``).
    """
    order = np.argsort(hr)
    remaining = float(budget)
    mwh = 0.0
    for g in order:
        if remaining <= 0.0:
            break
        take = min(float(cap_mwh[g]), remaining / float(hr[g]))
        mwh += take
        remaining -= take * float(hr[g])
    return mwh


def fleet_side(year: int) -> dict:
    """``fleet_only`` rebuild -> the LP's own budget, heat rates and monthly headroom."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(KEEPER, year))
    # The composite's meta.json carries the FIRST leg's gas price for every year
    # (the known audit_keepers E3 provenance defect), so the PER-YEAR run_config
    # is the authority: it is what that year's single-year shard solved on.
    cfg = json.loads((KEEPER / f"run_config_{year}.json").read_text())
    sc = cfg.get("scenario_config", cfg)
    gas = sc.get("gas_price_override", meta.get("gas_price"))
    payload = run_year(year, "MISO", 8760, gas, {}, fleet_only=True, **kw)

    fa = payload["fleet_arrays"]
    idx = coal_gen_idx(fa)
    hr = np.asarray(fa.heat_rate, dtype=float)[idx]
    pmax = np.asarray(fa.pmax, dtype=float)[idx]
    avail = np.asarray(fa.availability, dtype=float)[idx]
    month_index = _hour_to_month_index(8760)

    # Per-unit monthly energy headroom, (n_coal, 12).
    head = np.zeros((idx.size, 12))
    for m in range(12):
        head[:, m] = (pmax[:, None] * avail[:, month_index == m]).sum(axis=1)

    built = build_coal_fuel_budget(fa, year, hours=8760)
    return {
        "year": year,
        "gas": gas,
        "built": built,
        "hr": hr,
        "pmax": pmax,
        "head": head,
        "declared": bool(sc.get("coal_fuel_inventory", False)),
        "hr_capwt": float((hr * pmax).sum() / pmax.sum()),
        "hr_min": float(hr.min()),
        "hr_max": float(hr.max()),
        "n": int(idx.size),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    ap.add_argument(
        "--warm-ref",
        default="6d696984",
        help="commit that still carries the superseded warm keeper bundle",
    )
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    out: dict[str, dict] = {}
    for year in args.years:
        fs = fleet_side(year)
        print(f"\n{'=' * 104}\n{year}   gas ${fs['gas']}   "
              f"coal_fuel_inventory declared={fs['declared']}\n{'=' * 104}")
        if fs["built"] is None:
            print("  build_coal_fuel_budget -> None: the constraint adds ZERO rows")
            out[str(year)] = {"budget": None, "declared": fs["declared"]}
            continue
        _, budget_mmbtu, _, _, _, p = fs["built"]
        cap = np.asarray(budget_mmbtu).reshape(-1)
        print(
            f"  footprint {p.n_plants} plants ({p.n_storage_entities} shared-storage), "
            f"{p.n_generators} coal gens; opening stock "
            f"{p.opening_stock_tons / 1e6:.2f} Mt + delivery "
            f"{p.delivery_rate_tons_per_year / 1e6:.2f} Mt/yr "
            f"(from {'+'.join(str(y) for y in p.rate_source_years)}) "
            f"@ {p.mmbtu_per_ton:.3f} MMBtu/ton"
        )
        print(
            f"  annual cap {p.annual_budget_mmbtu / 1e6:>9.1f} M MMBtu   monthly "
            f"{p.monthly_budget_mmbtu / 1e6:>7.1f} M MMBtu   fleet HR cap-wt "
            f"{fs['hr_capwt']:.3f} (units {fs['hr_min']:.3f}-{fs['hr_max']:.3f})"
        )

        cold = model_coal_monthly_mwh(KEEPER, year)
        warm = warm_coal_monthly_mwh(args.warm_ref, year)

        print(
            f"\n  {'mo':>3} {'COLD GWh':>9} {'MAX-under':>10} {'over?':>8} "
            f"{'phys GWh':>9} {'WARM GWh':>9} {'w over?':>8}  verdict (COLD)"
        )
        rows = []
        n_viol = 0
        for m in range(12):
            mx = max_mwh_under_cap(fs["hr"], fs["head"][:, m], cap[m])
            phys = float(fs["head"][:, m].sum())
            over = cold[m] - mx
            wover = (warm[m] - mx) if warm is not None else float("nan")
            if over > 0:
                verdict = "VIOLATES cap -> NOT ENFORCED"
                n_viol += 1
            elif mx < phys * 0.999:
                verdict = "cap below phys, not violated"
            else:
                verdict = "cap above phys -> inert"
            print(
                f"  {m + 1:>3} {cold[m] / 1e3:>9.1f} {mx / 1e3:>10.1f} "
                f"{over / 1e3:>+8.1f} {phys / 1e3:>9.1f} "
                f"{(warm[m] / 1e3 if warm is not None else float('nan')):>9.1f} "
                f"{wover / 1e3:>+8.1f}  {verdict}"
            )
            rows.append(
                {
                    "month": m + 1,
                    "cold_mwh": float(cold[m]),
                    "max_mwh_under_cap": float(mx),
                    "cold_excess_mwh": float(over),
                    "phys_mwh": phys,
                    "warm_mwh": float(warm[m]) if warm is not None else None,
                    "warm_excess_mwh": float(wover) if warm is not None else None,
                    "verdict": verdict,
                }
            )

        ann_cold = float(cold.sum())
        ann_warm = float(warm.sum()) if warm is not None else float("nan")
        ann_max = sum(r["max_mwh_under_cap"] for r in rows)
        print(
            f"\n  ANNUAL coal: COLD {ann_cold / 1e6:.2f} TWh · WARM "
            f"{ann_warm / 1e6:.2f} TWh · max under the 12 monthly caps "
            f"{ann_max / 1e6:.2f} TWh"
        )
        print(
            f"  MONTHS THE COLD KEEPER VIOLATES ITS OWN DECLARED CAP: "
            f"{n_viol}/12   (excess {sum(max(0, r['cold_excess_mwh']) for r in rows) / 1e6:+.2f} TWh)"
        )
        if warm is not None:
            wv = sum(1 for r in rows if (r["warm_excess_mwh"] or 0) > 0)
            print(f"  same for the WARM keeper: {wv}/12")
        out[str(year)] = {
            "gas": fs["gas"],
            "declared": fs["declared"],
            "annual_cap_mmbtu": p.annual_budget_mmbtu,
            "monthly_cap_mmbtu": p.monthly_budget_mmbtu,
            "opening_stock_tons": p.opening_stock_tons,
            "delivery_rate_tons_per_year": p.delivery_rate_tons_per_year,
            "rate_source_years": list(p.rate_source_years),
            "n_plants": p.n_plants,
            "n_generators": p.n_generators,
            "hr_capwt": fs["hr_capwt"],
            "months": rows,
            "annual_cold_mwh": ann_cold,
            "annual_warm_mwh": ann_warm,
            "n_months_cold_violates": n_viol,
        }

    if args.json_out:
        args.json_out.write_text(json.dumps(out, indent=2, default=str))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
