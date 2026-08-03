"""nyiso-118: EX-ANTE construction probe for ``nyiso_ordc_measured_step_span``.

Builds the NYISO ``ReserveDesign`` twice — flag OFF (control) and flag ON
(treatment) — on the designated keeper's reserve configuration, and diffs every
family's ``requirement`` vector and ORDC step vectors (``ordc_penalties``,
``ordc_step_widths``). No LP is solved and no dual is read.

Why a construction probe, and why it is the *kill* instrument: the scope
question this session must answer — "does arming the global flag double-apply
the span translation to Long Island, whose ladder already applies it
family-scoped?" — is a question about how the curve is BUILT. ``dual`` and
``held_mw`` are solved outputs of a co-optimization; gating byte-identity on
them can only pass when the mechanism does nothing (the nyiso-115 G2 error).
The width vector and the requirement vector are the construction, so they are
what the gate reads (nyiso-117 PREREG §3.1).

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso118_span_construction_probe.py \\
        --json-out results/calibration/nyiso118_span_construction_probe.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays
from market_sim.model.reserves.spec import _nyiso_design

# The designated keeper's NYISO zone list and its armed reserve flags
# (results/calibration/nyiso117_nyc_stepcurve/run_config.json).
ZONES = ["West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
KEEPER_RESERVE_FLAGS = {
    "energy_reserve_coopt": True,
    "nyiso_dynamic_reserve_requirements": True,
    "nyiso_li_locational_reserve": True,
    "nyiso_nyc_rcpf_step_curve": True,
    "nyiso_hydro_reserve_eligible": True,
    "nyiso_scr_edrp_reserve_eligible": True,
    "nyiso_east_reserve_families": False,
    "nyiso_spin_reserve_online": False,
    "nyiso_synchronised_reserve": False,
    "nyiso_incity_commitment_obligation": False,
    "nyiso_rcpf_enabled": False,
}
YEARS = (2023, 2024, 2025)


def _minimal_fleet(n_zones: int) -> FleetArrays:
    """One synthetic generator per zone.

    Family CONSTRUCTION (requirement + ORDC step vectors) is independent of the
    fleet — the fleet only drives the eligibility masks, which this probe does
    not read. A minimal fleet keeps the probe a pure construction measurement.
    """
    n = n_zones
    return FleetArrays(
        pmax=np.full(n, 100.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n),
        fuel_type_idx=np.zeros(n, dtype=int),
        availability=np.ones(n),
        unit_ids=np.array([f"u{i}" for i in range(n)]),
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.arange(n),
        plant_group=np.array(["CC_REGULAR"] * n),
    )


def _cfg(year: int, span: bool) -> ScenarioConfig:
    return ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        weather_year=year,
        start_year=year,
        end_year=year,
        nyiso_ordc_measured_step_span=span,
        **KEEPER_RESERVE_FLAGS,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--hours", type=int, default=8760)
    args = ap.parse_args()

    out: dict = {
        "probe": "nyiso-118 ex-ante ORDC span construction diff (no solve)",
        "mechanism": "nyiso_ordc_measured_step_span",
        "instrument": (
            "ReserveDesign family requirement + ordc_penalties + "
            "ordc_step_widths, built twice at one HEAD; no dual, no held_mw"
        ),
        "keeper_reserve_flags": KEEPER_RESERVE_FLAGS,
        "years": {},
    }

    fleet = _minimal_fleet(len(ZONES))
    for year in YEARS:
        d_off = _nyiso_design(
            _cfg(year, False), fleet, args.hours, list(ZONES), sim_year=year
        )
        d_on = _nyiso_design(
            _cfg(year, True), fleet, args.hours, list(ZONES), sim_year=year
        )
        fam_off = {f.name: f for f in d_off.families}
        fam_on = {f.name: f for f in d_on.families}
        assert set(fam_off) == set(fam_on), (set(fam_off), set(fam_on))

        rows = {}
        for name in sorted(fam_off):
            a, b = fam_off[name], fam_on[name]
            w_a = np.asarray(a.ordc_step_widths, dtype=float)
            w_b = np.asarray(b.ordc_step_widths, dtype=float)
            req_a = np.asarray(a.requirement, dtype=float)
            req_b = np.asarray(b.requirement, dtype=float)
            p_a = np.asarray(a.ordc_penalties, dtype=float)
            p_b = np.asarray(b.ordc_penalties, dtype=float)
            # Broadcast to (n_steps, T) so a (n_steps,) static vector and an
            # hourly one are compared on the same grid.
            wa = np.broadcast_to(
                w_a if w_a.ndim == 2 else w_a[:, None], (w_a.shape[0], args.hours)
            )
            wb = np.broadcast_to(
                w_b if w_b.ndim == 2 else w_b[:, None], (w_b.shape[0], args.hours)
            )
            # DECISIVE construction test: does the demand curve's PRICE change
            # anywhere the LP can actually reach? Shortfall is bounded above by
            # the hour's requirement (held >= 0), so the reachable domain is
            # [0, requirement[t]] — widths beyond it are unreachable padding and
            # a width delta there is representational, not economic. Compare the
            # marginal price on a fixed grid over that domain.
            n_probe = 64
            frac = (np.arange(n_probe) + 0.5) / n_probe  # band midpoints
            s_grid = req_a[None, :] * frac[:, None]  # (n_probe, T)
            price = {}
            for tag, (ww, pp) in (("off", (wa, p_a)), ("on", (wb, p_b))):
                edges = np.cumsum(ww, axis=0)  # (n_steps, T)
                # band index of each probe point = # of edges strictly below it
                idx = (s_grid[None, :, :] > edges[:, None, :]).sum(axis=0)
                idx = np.clip(idx, 0, pp.shape[0] - 1)
                price[tag] = pp[idx]  # (n_probe, T)
            same_price = bool(np.array_equal(price["off"], price["on"]))
            signed = price["on"] - price["off"]  # <0 == the flag prices LOWER
            dp = np.abs(signed)

            rows[name] = {
                "reachable_price_identical": same_price,
                "reachable_max_abs_price_delta": float(dp.max()),
                "reachable_hours_price_differs": int((dp.max(axis=0) > 0).sum()),
                # Direction: the span fix widens rungs, so at a given shortfall
                # MW the curve should price the SAME or LOWER, never higher.
                "reachable_price_never_increases": bool((signed <= 0).all()),
                "reachable_probe_points_priced_lower": int((signed < 0).sum()),
                "reachable_probe_points_priced_higher": int((signed > 0).sum()),
                "min_penalty_off": float(p_a.min()),
                "min_penalty_on": float(p_b.min()),
                "n_steps_off": int(w_a.shape[0]),
                "n_steps_on": int(w_b.shape[0]),
                "widths_hourly_off": bool(w_a.ndim == 2),
                "widths_hourly_on": bool(w_b.ndim == 2),
                "requirement_identical": bool(np.array_equal(req_a, req_b)),
                "penalties_identical": bool(np.array_equal(p_a, p_b)),
                "widths_identical": bool(np.array_equal(wa, wb)),
                "max_abs_width_delta": float(np.abs(wa - wb).max()),
                "total_width_off_mean": float(wa.sum(axis=0).mean()),
                "total_width_on_mean": float(wb.sum(axis=0).mean()),
                "requirement_mean": float(req_a.mean()),
                # The construction-consistency identity the flag exists to
                # restore: total step width == the hour's requirement.
                "hours_totalwidth_ne_requirement_off": int(
                    (~np.isclose(wa.sum(axis=0), req_a)).sum()
                ),
                "hours_totalwidth_ne_requirement_on": int(
                    (~np.isclose(wb.sum(axis=0), req_b)).sum()
                ),
            }
        out["years"][str(year)] = {
            "n_families": len(fam_off),
            "families": rows,
            "changed_families": sorted(
                n for n, r in rows.items() if not r["widths_identical"]
            ),
            "unchanged_families": sorted(
                n for n, r in rows.items() if r["widths_identical"]
            ),
            # The economically meaningful split: a family whose widths move but
            # whose reachable price does not has been re-REPRESENTED, not
            # re-priced.
            "price_changed_families": sorted(
                n for n, r in rows.items() if not r["reachable_price_identical"]
            ),
            "width_changed_price_identical": sorted(
                n
                for n, r in rows.items()
                if not r["widths_identical"] and r["reachable_price_identical"]
            ),
        }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=2))
    for y, blk in out["years"].items():
        print(f"{y}: changed={blk['changed_families']}")
        print(f"      unchanged={blk['unchanged_families']}")
    print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
