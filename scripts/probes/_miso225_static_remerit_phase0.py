"""miso-225 phase 0 (A3) — the PRE-SOLVE arithmetic for the OWNER-RULED form.

miso-224 measured the static re-merit of gas at the BARE traded hub and the LP
then killed that arm on its dispatch gates (coal -13.3 TWh, imports -11.85 TWh,
two C1 flips).  The owner ruled on 2026-09-06 that the offer is marginal
commodity **plus variable transport**, and miso-225 phase 0 (A1/A2) measured that
transport per plant from the receipts.  This instrument re-runs miso-224's own
static clearing with the ruled offer basis, so the screen's gates are set on the
arithmetic of the arm that will actually be solved — not on its predecessor's.

It reuses miso-224 part 4 wholesale (fleet build, hour sets, static clearing,
instrument self-error) and changes exactly one thing: the gas rows move to
``hub + v[plant]`` instead of ``hub``, with ``v`` resolved down the same declared
own -> zone|group -> group -> MISO ladder the applier walks.  Reporting both
bases side by side is the point: the difference between them is the whole content
of the ruling.

Zero-LP.  Rule 22 ``[R-HOLDOUT]``: 2023-2025 only.  Writes
``_miso225_static_remerit.json``.

Usage::

    MISO225_YEARS=2023 PYTHONPATH=src python3 scripts/probes/_miso225_static_remerit_phase0.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso224_static_remerit_phase0 as _m224  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso221_peak_shape_phase0 import _r  # noqa: E402
from _miso224_floor_anatomy_phase0 import actual_mec, actual_zone_price  # noqa: E402
from _miso224_marginal_frequency_phase0 import keeper_prices  # noqa: E402
from _miso224_offer_decomposition_phase0 import _month_of_hour, spot_gas_by_month  # noqa: E402
from _miso224_static_remerit_phase0 import (  # noqa: E402
    COAL_CLASSES,
    HOURS,
    ZONE,
    fleet_dispatch,
    hh_by_month,
    static_clear,
)
from market_sim.data.fuel.basis.miso import (  # noqa: E402
    _miso_gas_variable_transport_vector,
)

OUT = REPO / "results/calibration/_miso225_static_remerit.json"
YEARS = tuple(int(v) for v in os.environ.get("MISO225_YEARS", "2023").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"


def analyse_year(year: int) -> dict:
    """Clear the static stack three ways: keeper basis, bare hub, hub + transport."""
    cfg = keeper_config()
    raw_fleet, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, year)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel_name = np.array([str(getattr(g, "fuel_type", "") or "").lower() for g in fleet])
    is_gas = np.array([f.startswith("gas") for f in fuel_name])
    is_coal = np.isin(klass, COAL_CLASSES) | (fuel_name == "coal")
    south = np.array([str(g.zone) for g in fleet]) == "MISO-South"

    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fp = np.asarray(fuel_prices, float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    hr = np.asarray(arrays.heat_rate, float)

    moh = _month_of_hour() - 1
    spot = np.where(
        south[:, None],
        hh_by_month(year)[moh][None, :],
        spot_gas_by_month(year)[moh][None, :],
    )
    # The ruled adder, on the gas rows only, through the applier's own ladder.
    gas_rows = np.flatnonzero(is_gas)
    v = np.zeros(len(fleet))
    v[gas_rows] = _miso_gas_variable_transport_vector(
        arrays, gas_rows, tuple(zone_names)
    )

    mc_bare = mc + np.where(is_gas[:, None], (spot - fp) * hr[:, None], 0.0)
    mc_ruled = mc + np.where(
        is_gas[:, None], (spot + v[:, None] - fp) * hr[:, None], 0.0
    )

    q = fleet_dispatch(year)
    p_keeper = keeper_prices(year)[ZONE].to_numpy(float)
    mec, _, _ = actual_mec(year)
    act = actual_zone_price(year)[ZONE].to_numpy(float)

    bases = {"keeper": mc, "bare_hub": mc_bare, "ruled": mc_ruled}
    price = {k: np.full(HOURS, np.nan) for k in bases}
    marg = {k: np.full(HOURS, "", dtype=object) for k in bases}
    gasmw = {k: np.zeros(HOURS) for k in bases}
    coalmw = {k: np.zeros(HOURS) for k in bases}
    for h in range(HOURS):
        cap_h = pmax * avail[:, h]
        idx = np.flatnonzero(cap_h > 1.0)
        for name, basis in bases.items():
            (
                price[name][h],
                marg[name][h],
                gasmw[name][h],
                coalmw[name][h],
            ) = static_clear(
                basis[idx, h], cap_h[idx], q[h], klass[idx], is_gas[idx], is_coal[idx]
            )

    ok = np.isfinite(mec)
    sets = {
        "all": ok,
        "body": ok & (p_keeper <= np.percentile(p_keeper, 90)),
        "tail_top10": ok & (p_keeper > np.percentile(p_keeper, 90)),
        "actual_hub_lt_20": ok & np.isfinite(act) & (act < 20.0),
    }
    pct = np.percentile(mec[ok], np.arange(0, 101, 10))
    for d in range(10):
        hi = (mec < pct[d + 1]) if d < 9 else (mec <= pct[d + 1])
        sets[f"mec_d{d + 1}"] = ok & (mec >= pct[d]) & hi

    rec: dict[str, object] = {
        "zone": ZONE,
        "n_tranches": int(len(fleet)),
        "transport": {
            "n_gas_rows": int(gas_rows.size),
            "mean": _r(float(v[gas_rows].mean())),
            "min": _r(float(v[gas_rows].min())),
            "max": _r(float(v[gas_rows].max())),
            "capacity_weighted": _r(
                float((v[gas_rows] * pmax[gas_rows]).sum() / pmax[gas_rows].sum())
            ),
        },
        "by_set": {},
    }
    by_set: dict[str, dict] = {}
    for name, m in sets.items():
        if not m.any():
            by_set[name] = {"n": 0}
            continue
        d_bare = (price["bare_hub"] - price["keeper"])[m]
        d_ruled = (price["ruled"] - price["keeper"])[m]
        by_set[name] = {
            "n": int(m.sum()),
            "keeper_p1_mean": _r(p_keeper[m].mean()),
            "mec_mean": _r(mec[m].mean()),
            "static_at_keeper_basis_mean": _r(price["keeper"][m].mean()),
            "instrument_error_static_minus_p1": _r((price["keeper"] - p_keeper)[m].mean()),
            "predicted_delta_bare_hub_mean": _r(d_bare.mean()),
            "predicted_delta_ruled_mean": _r(d_ruled.mean()),
            "predicted_delta_ruled_p10": _r(np.percentile(d_ruled, 10)),
            "predicted_delta_ruled_p50": _r(np.median(d_ruled)),
            "predicted_delta_ruled_p90": _r(np.percentile(d_ruled, 90)),
            "ruled_share_of_bare_move": (
                _r(float(d_ruled.mean() / d_bare.mean()), 3) if d_bare.mean() else None
            ),
            "gap_to_mec_before": _r((p_keeper - mec)[m].mean()),
            "gap_to_mec_after_ruled": _r((p_keeper + (price["ruled"] - price["keeper"]) - mec)[m].mean()),
            "coal_in_merit_mw_delta_bare": _r((coalmw["bare_hub"] - coalmw["keeper"])[m].mean(), 0),
            "coal_in_merit_mw_delta_ruled": _r((coalmw["ruled"] - coalmw["keeper"])[m].mean(), 0),
            "gas_in_merit_mw_delta_bare": _r((gasmw["bare_hub"] - gasmw["keeper"])[m].mean(), 0),
            "gas_in_merit_mw_delta_ruled": _r((gasmw["ruled"] - gasmw["keeper"])[m].mean(), 0),
            "marginal_gas_share_keeper": _r(
                float(np.mean([str(k).startswith(("CC", "CT", "ST_GAS")) for k in marg["keeper"][m]])), 3
            ),
            "marginal_gas_share_ruled": _r(
                float(np.mean([str(k).startswith(("CC", "CT", "ST_GAS")) for k in marg["ruled"][m]])), 3
            ),
        }
    rec["by_set"] = by_set
    del raw_fleet, fleet, arrays, fuel_prices, mc, mc_bare, mc_ruled, fp
    gc.collect()
    return rec


def main() -> int:
    rec = {
        "probe": "miso-225 phase 0 A3 - static re-merit of the OWNER-RULED gas offer (hub + measured variable transport)",
        "keeper": "2026-09-05-miso-220-nonsteam-lift",
        "bundle": str(_m224.KEEPER.relative_to(REPO)),
        "solved": False,
        "by_year": {},
    }
    if OUT.exists():
        try:
            rec["by_year"] = json.loads(OUT.read_text()).get("by_year", {})
        except Exception:  # noqa: BLE001
            pass
    for year in YEARS:
        rec["by_year"][str(year)] = analyse_year(year)
        print(json.dumps(rec["by_year"][str(year)]["transport"], indent=1), flush=True)
        for s in ("body", "tail_top10", "actual_hub_lt_20", "mec_d1", "mec_d5", "mec_d9"):
            r = rec["by_year"][str(year)]["by_set"][s]
            print(
                f"  {year} {s:18s} n={r['n']:5d} P1 {r['keeper_p1_mean']:>7} "
                f"dP bare {r['predicted_delta_bare_hub_mean']:>7} ruled {r['predicted_delta_ruled_mean']:>7} "
                f"({r['ruled_share_of_bare_move']} of it) | coal dMW bare {r['coal_in_merit_mw_delta_bare']:>7} "
                f"ruled {r['coal_in_merit_mw_delta_ruled']:>7} | gas dMW ruled {r['gas_in_merit_mw_delta_ruled']:>7}",
                flush=True,
            )
        OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
