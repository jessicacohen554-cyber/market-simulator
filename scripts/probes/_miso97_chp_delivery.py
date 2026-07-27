"""miso-97 TASK 2 derive — MISO CHP grid delivery vs EIA-923 on a SOURCED BTM basis.

Measurement only: **no LP is built and nothing is solved.** The model side is
read from the committed keeper bundle's own sidecars
(``results/calibration/miso88_egrid_hr``), the actual side is rebuilt from
EIA-923 exactly the way the calibration bench builds it.

THE QUESTION. ``data/chp._correct_chp_steam_credit_hr``'s docstring records the
2026-07-08 decision not to correct MISO's steam-credited CHP heat rates:

    "MISO 2026-07-08: audited but NOT added — its HRs are equally sub-physical
     yet its CHP does not over-deliver (BTM-dominated, CT_CHP already
     under-runs), so the correction only worsens CT_CHP."

Both halves rest on a BTM share that is itself the UNSOURCED
``CHP_BTM_PCT_BY_SECTOR["merchant"]`` = 35.0 default, because MISO is the only
ISO with no ``chp_sector`` data at all (miso-97 TASK 1,
``scripts/probes/_miso97_chp_sector_btm.py``). This instrument re-measures the
delivery comparison on the sourced share.

WHY THE DIRECTION IS DECIDABLE WITHOUT A SOLVE. The BTM share enters the model
in exactly three places, and all three are the SAME linear factor
``(1 - s)`` on the SAME per-plant nameplate:

1. **LP capacity.** ``offer_curves.plant_cf_bands`` / ``fleet.assembly``:
   ``grid_cap = nameplate x (1 - s)``, and ``committed_cap`` / ``econ_cap`` /
   ``peak_cap`` are all shares of ``grid_cap`` — so every tranche of the
   plant's offer curve scales by ``f = (1 - s_new)/(1 - s_old)`` at UNCHANGED
   prices (heat rates, VOM and carbon are untouched by ``s``).
2. **The steam-following floor.** ``fleet/assembly.py``:
   ``grid_mr_cf = pmin_cf x (1 - s)``, ``floor_mw = grid_mr_cf/100 x
   nameplate`` — the same factor ``f``.
3. **The benchmark subtrahend.** ``run_calibration_full._btm_frame`` holds out
   ``chp_btm_pct`` of the plant's measured EIA-923 class net generation, so the
   grid-facing ACTUAL is ``netgen_923 x (1 - s)`` — again ``f``.

So raising ``s`` is a pure horizontal rescaling of the whole CHP problem. The
actual falls by exactly ``f``. The model falls by ``f`` where it is capacity- or
floor-bound and by LESS than ``f`` where it is economic (a smaller cheap-CHP
supply raises lambda, so the now-smaller capacity is dispatched at least as
hard). Writing the model response ``rho = model_new/model_old``, that is
``rho >= f``, hence

    ratio_new = (model_old x rho)/(actual_old x f) >= model_old/actual_old
              = ratio_old.

**Raising the BTM share can only move a class UP relative to its meter.** It
cannot deepen an under-run, and it cannot relieve an over-delivery. That is a
structural bound, not an estimate, and it is what makes the 2026-07-08
"BTM-dominated, so CT_CHP already under-runs" premise testable without a solve.

The table therefore brackets the model side between ``rho = f`` (fully
capacity/floor-bound — the ratio is invariant) and ``rho = 1`` (no response at
all — the ratio moves by the full ``1/f``). D-2 mechanism attribution in the
keeper's ``legitimacy_diagnostics.json`` puts the floor-forced share of MISO
CHP at 17.6 % (CC_CHP) / 30.9 % (CT_CHP), so neither endpoint is the truth and
both are reported rather than a fitted interpolation between them.

TWO MEASUREMENT TRAPS this instrument encodes, both hit while building it:

* **The 2025 meter is the EIA-923 MONTHLY early release.** It carries ~3 400
  respondents against ~13 200 in the annual 2024 vintage, so it reports only
  83 %/65 %/52 % of MISO CC_CHP/CT_CHP/ST_CHP capacity. The model side is the
  WHOLE class, so a class-total comparison in 2025 divides a full numerator by
  a partial denominator and fabricates a **+28 % CT_CHP over-delivery** that is
  pure coverage artifact. Every row therefore carries ``meter_cov_%`` and rows
  under 90 % are excluded from the verdict rather than quietly averaged in.
* **The dashboard payload's per-plant ``m_ann`` is a PLANT total, not a
  per-class one.** Using it to restrict the model side to metered plants
  attributes a mixed plant's whole output to whichever class the CHP fleet
  assigns it, which inflated ST_CHP from 0.49 to 11.9 TWh — 24x the class's own
  reported total. There is no committed per-(plant, class) model series, so the
  matched-set restriction is NOT available and coverage-gating is the honest
  substitute.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso97_chp_delivery.py
    ... --iso MISO --run-id 2026-07-25-miso-88-egrid-hr
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(1, str(ROOT / "src"))

from scripts.probes._miso97_chp_sector_btm import (  # noqa: E402
    _CHP_GROUPS,
    artifact_codes,
    baseline_sector_by_code,
    chp_fleet,
    eia860_sector_class,
    proposed_btm_pct,
)

_MWH_PER_TWH = 1e6


def model_class_twh(run_id: str) -> dict[int, dict[str, float]]:
    """Return ``{year: {class: grid-delivered TWh}}`` from the run's dashboard payload.

    Reads the committed ``frontend/data/backcast/runs/<id>.js`` gzip payload's
    ``gmModel`` block — the keeper's own reported grid-delivered class energy,
    i.e. already net of the BTM hold-out. Using the committed payload rather
    than replaying the solve is the rule-15 posture for a diagnostic session.
    """
    path = ROOT / "frontend/data/backcast/runs" / f"{run_id}.js"
    blob = re.search(r'="([A-Za-z0-9+/=]+)"', path.read_text()).group(1)
    payload = json.loads(gzip.decompress(base64.b64decode(blob)))
    return {
        int(y): {k: float(v) for k, v in blk["gmModel"].items()}
        for y, blk in payload["years"].items()
    }


def actual_class_mwh(iso: str, year: int, codes: set[int]) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, class): EIA-923 net MWh}`` for the ISO's CHP plants.

    Uses :func:`market_sim.data.chp.chp_class_netgen_mwh`, the same per-(plant,
    class) EIA-923 Page-1 aggregation on the same canonical taxonomy that
    ``_btm_frame`` books the bench subtrahend against.
    """
    from market_sim.data.chp import chp_class_netgen_mwh

    return {
        (pid, klass): mwh
        for (pid, klass), mwh in chp_class_netgen_mwh(year).items()
        if pid in codes and klass in _CHP_GROUPS
    }


def build(iso: str, run_id: str, years: list[int], vintage: int | None) -> pd.DataFrame:
    """Per (year, class): model TWh, and the actual on both BTM bases."""
    sector = eia860_sector_class()
    art_codes = artifact_codes(iso)
    # Baseline read from git HEAD, not from a live chp_btm_pct call: once TASK 1
    # has patched the working-tree artifact that function returns the SOURCED
    # share for both sides and every delta collapses to zero.
    base = baseline_sector_by_code(iso)
    # One fleet vintage for BOTH sides: the CHP class a plant lands in is
    # vintage-dependent, so mixing vintages would mis-key the (plant, class)
    # shares against each other rather than measure the share change.
    fleet = chp_fleet(iso, vintage)
    codes = {int(c) for c in fleet["plant_code"]}
    model = model_class_twh(run_id)

    share_old: dict[tuple[int, str], float] = {}
    share_new: dict[tuple[int, str], float] = {}
    for c, g in zip(fleet["plant_code"], fleet["plant_group"]):
        c, g = int(c), str(g)
        share_old[(c, g)] = proposed_btm_pct(g, base.get(c), iso) / 100.0
        sec = sector.get(c) if c in art_codes else None
        share_new[(c, g)] = proposed_btm_pct(g, sec, iso) / 100.0

    cap_by_key = {
        (int(c), str(g)): float(p)
        for c, g, p in zip(fleet["plant_code"], fleet["plant_group"], fleet["pmax"])
    }

    rows = []
    for year in years:
        actual = actual_class_mwh(iso, year, codes)
        metered = {(pid, k) for (pid, k) in actual}
        for klass in _CHP_GROUPS:
            a_old = a_new = 0.0
            for (pid, k), mwh in actual.items():
                if k != klass:
                    continue
                a_old += mwh * (1.0 - share_old.get((pid, k), 0.35))
                a_new += mwh * (1.0 - share_new.get((pid, k), 0.35))
            m_old = model.get(year, {}).get(klass, 0.0)
            # Meter coverage: the model side is the WHOLE class, so a year whose
            # EIA-923 vintage reports only part of the fleet is not comparable
            # at class grain. The 2025 vintage is the monthly early release
            # (~3 400 respondents vs ~13 200 in 2024), which is exactly this.
            cap_tot = sum(v for k, v in cap_by_key.items() if k[1] == klass)
            cap_met = sum(
                v for k, v in cap_by_key.items() if k[1] == klass and k in metered
            )
            a_old /= _MWH_PER_TWH
            a_new /= _MWH_PER_TWH
            f = a_new / a_old if a_old > 0 else float("nan")
            rows.append(
                {
                    "year": year,
                    "class": klass,
                    "meter_cov_%": 100.0 * cap_met / cap_tot if cap_tot else float("nan"),
                    "model_twh": m_old,
                    "actual_today_twh": a_old,
                    "err_today_%": 100.0 * (m_old - a_old) / a_old if a_old else float("nan"),
                    "actual_sourced_twh": a_new,
                    "f": f,
                    # rho = f: fully capacity/floor-bound, ratio invariant.
                    "err_bound_lo_%": 100.0 * (m_old - a_old) / a_old if a_old else float("nan"),
                    # rho = 1: no model response, the full 1/f moves onto the ratio.
                    "err_bound_hi_%": 100.0 * (m_old - a_new) / a_new if a_new else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--run-id", default="2026-07-25-miso-88-egrid-hr")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--vintage", type=int, default=2024, help="EIA-860 CHP vintage")
    args = ap.parse_args()

    df = build(args.iso, args.run_id, args.years, args.vintage)
    print(f"\n=== {args.iso}: CHP grid delivery, model vs EIA-923 ===")
    print("err_today   = model vs the actual held out at TODAY's (default) share")
    print("bound_lo    = rho=f, class fully capacity/floor-bound -> ratio invariant")
    print("bound_hi    = rho=1, no model response -> the whole 1/f lands on the ratio")
    print("the truth lies between; both endpoints are reported, neither is fitted\n")
    print(df.round(3).to_string(index=False))

    bad = df["meter_cov_%"] < 90.0
    if bad.any():
        rows = ", ".join(
            f"{int(y)} {k} ({c:.0f} %)"
            for y, k, c in zip(
                df.loc[bad, "year"], df.loc[bad, "class"], df.loc[bad, "meter_cov_%"]
            )
        )
        print(
            f"\nCOVERAGE-BLOCKED (meter reports <90 % of class capacity): {rows}\n"
            "  — excluded from the verdict below. The model side is the WHOLE "
            "class, so a partial meter divides a full numerator by a partial\n"
            "  denominator and fabricates over-delivery. The 2025 rows are the "
            "EIA-923 monthly early release (~3 400 respondents vs ~13 200)."
        )
    ok = df[~bad]

    print("\n=== the 2026-07-08 premise, per class (comparable years only) ===")
    for klass, g in ok.groupby("class"):
        lo = g["err_bound_lo_%"].mean()
        hi = g["err_bound_hi_%"].mean()
        verdict = (
            "UNDER-RUNS on both bounds"
            if hi < 0
            else "OVER-DELIVERS on both bounds"
            if lo > 0
            else "straddles zero"
        )
        print(f"  {klass:7s} mean err {lo:+7.1f} % -> {hi:+7.1f} %   {verdict}")


if __name__ == "__main__":
    main()
