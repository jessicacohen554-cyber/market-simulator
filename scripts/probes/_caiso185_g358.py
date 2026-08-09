"""caiso-185 G-358 — does arming the table remove plant 358's ``f_CEMS > 1`` excess?

PRECHECK-caiso185 §8, verbatim: *"arming must REMOVE >= 80 % of plant 358's ``f_CEMS > 1``
excess capacity-year, measured on the LP's own basis, in every year"*, with the honesty
note that the gate is a **WIRING test, not corroboration of the capability value** —
because ``reconciled_mw`` IS the plant's own p999, ``f_CEMS -> 1`` is close to arithmetic.
It fails if the raise row does not reach the bin, if the live bin capacity is not the
``current_mw`` the table assumes, if the guard interferes, or if group routing misses.

Measured on **exactly caiso-184's definition** so the two sessions' numbers are
commensurable: ``X = Sum_t (CEMS_net - D2)^+`` per bin, with ``CEMS_net`` the census's
gross->net-corrected CAMPD series and ``D2`` the LP's own bin capacity (net-summer sum
raised to nameplate by ``cc_summer_derate_ratio`` under ``cc_nameplate_summer_derate``).
**No availability multiplier enters either side** — that is caiso-184's basis and this
gate does not move it. (The availability-basis question this session discovered is a
SEPARATE measurement, ``_caiso185_arm_capability.py``; it is deliberately not smuggled
into a pre-registered bar.)

Instruments are REUSED, never re-implemented: ``_caiso184_capacity_basis_census._bin_cems``
/ ``_net_factor`` / ``_d2_for_bin`` / ``_parasitic_factors``.

Usage::

    python scripts/probes/_caiso185_g358.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import cc_capacity_reconcile_path  # noqa: E402
from market_sim.data.outages import _iso_plant_capacity  # noqa: E402

from scripts.probes._caiso184_capacity_basis_census import (  # noqa: E402
    _bin_cems,
    _d2_for_bin,
    _net_factor,
    _parasitic_factors,
)

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
PLANT = 358
BAR = 0.80  # PRECHECK §8 G-358
OUT = REPO / "results" / "calibration" / "_caiso185_g358.json"


def _armed_capacity() -> dict[int, float]:
    """``{plant_code: reconciled_mw}`` from the committed CAISO table."""
    t = pd.read_csv(cc_capacity_reconcile_path(ISO))
    return {int(c): float(m) for c, m in zip(t["plant_code"], t["reconciled_mw"])}


def main() -> None:
    """Score G-358 (and, for context, every other row of the table)."""
    d1 = _iso_plant_capacity(ISO, False, True)  # keeper basis: LP-capacity denominator on
    measured = _parasitic_factors()
    recon = _armed_capacity()

    per_year: dict[str, dict] = {}
    for year in YEARS:
        cems = _bin_cems(year)
        rows: dict[str, dict] = {}
        for target, gross in cems.items():
            code, group = int(target[0]), str(target[1])
            if code not in recon:
                continue
            base = d1.get(target)
            if base is None or base <= 0.0:
                continue
            d2_off, _ = _d2_for_bin(target, float(base))
            factor, prov = _net_factor(code, group, measured)
            net = np.asarray(gross, dtype=float) * factor
            # The hook writes reconciled_mw straight into the bin's capacity_mw,
            # i.e. it REPLACES D2 (min/max per mode) — measured directly rather
            # than modelled as a ratio.
            d2_on = (
                min(d2_off, recon[code])
                if recon[code] < d2_off
                else max(d2_off, recon[code])
            )
            x_off = float(np.clip(net - d2_off, 0.0, None).sum())
            x_on = float(np.clip(net - d2_on, 0.0, None).sum())
            rows[f"{code}:{group}"] = {
                "plant_code": code,
                "plant_group": group,
                "d2_off_mw": round(d2_off, 2),
                "d2_on_mw": round(d2_on, 2),
                "net_factor": round(factor, 5),
                "net_factor_provenance": prov,
                "f_cems_max_off": round(float(net.max() / d2_off), 4),
                "f_cems_max_on": round(float(net.max() / d2_on), 4),
                "excess_mwh_off": round(x_off, 1),
                "excess_mwh_on": round(x_on, 1),
                "reduction": None if x_off <= 0 else round(1.0 - x_on / x_off, 4),
            }
        per_year[str(year)] = rows

    key = None
    for rows in per_year.values():
        for k, r in rows.items():
            if r["plant_code"] == PLANT:
                key = k
    reductions = {
        y: (per_year[y][key]["reduction"] if key and key in per_year[y] else None)
        for y in per_year
    }
    passed = all(r is not None and r >= BAR for r in reductions.values())

    out = {
        "iso": ISO,
        "years": list(YEARS),
        "basis": "caiso-184 X(N2,D2): CEMS gross->net vs the LP's own bin capacity; "
        "no availability multiplier on either side",
        "plant": PLANT,
        "bar": BAR,
        "g358_reduction_by_year": reductions,
        "g358_pass": passed,
        "per_year": per_year,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nG-358 reduction {reductions}  bar {BAR}  -> {'PASS' if passed else 'FAIL'}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
