"""nyiso-119: EX-ANTE construction probe for ``nyiso_seny_rcpf_increment_step``.

Builds the NYISO ``ReserveDesign`` twice at ONE HEAD — flag OFF (the designated
keeper's own recipe, ``nyiso_ordc_measured_step_span`` already armed) and flag
ON — and diffs every family's ``requirement`` vector and ORDC step vectors
(``ordc_penalties``, ``ordc_step_widths``). **No LP is solved and no dual is
read.**

Why a construction probe, and why it is the *kill* instrument: every question
this session must settle ex ante is about how the SENY demand curve is BUILT —
does the published $40 increment tier appear, does the total-step-width ==
requirement identity nyiso-118 restored survive, and does anything outside SENY
move? ``dual`` and ``held_mw`` are solved outputs of a co-optimization, and
gating byte-identity on them can only pass when the mechanism does nothing (the
nyiso-115 G2 error; nyiso-118 is the live proof that a provably-unchanged curve
can still move its dual through general equilibrium). The width vector and the
penalty vector ARE the construction, so they are what the gate reads.

Run:
    PYTHONPATH=.:src python \\
      scripts/probes/_nyiso119_seny_increment_construction_probe.py \\
      --json-out results/calibration/nyiso119_seny_increment_construction_probe.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays
from market_sim.model.reserves.spec import (
    NYISO_RCPF_LOCATIONAL,
    NYISO_SENY_30MIN_FAMILY,
    NYISO_SENY_30MIN_INCREMENT_RCPF,
    _nyiso_design,
)

# The DESIGNATED KEEPER's NYISO zone list and its armed reserve flags
# (results/calibration/nyiso118_seny_span/run_config.json, scenario_config).
# Note nyiso_ordc_measured_step_span=True — the control is the keeper as it is,
# not a pre-nyiso-118 recipe.
ZONES = ["West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
KEEPER_RESERVE_FLAGS = {
    "energy_reserve_coopt": True,
    "nyiso_dynamic_reserve_requirements": True,
    "nyiso_ordc_measured_step_span": True,
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

#: Published SENY base MW — READ from the registry, never re-typed (rule 5).
SENY_BASE_MW = float(NYISO_RCPF_LOCATIONAL["SENY"]["products"][0][1])

#: The keeper's own SENY binding hours (results/calibration/nyiso118_seny_span/
#: hourly/reserve_family_<year>.parquet, dual > 0) and their shortfall MW. Used
#: ONLY to evaluate the CONSTRUCTED price function at those shortfalls — the
#: probe reads no dual and re-solves nothing; it asks "what would the new curve
#: have charged for the shortfall the keeper actually had?".
KEEPER_BINDING_SHORTFALL_MW: dict[int, list[float]] = {
    2023: [5.866163, 61.307205],
    2024: [],
    2025: [
        0.0,
        157.054855,
        48.922409,
        225.0,
        0.0,
        70.199242,
        199.911301,
        225.0,
    ],
}


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


def _cfg(year: int, increment: bool) -> ScenarioConfig:
    return ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        weather_year=year,
        start_year=year,
        end_year=year,
        nyiso_seny_rcpf_increment_step=increment,
        **KEEPER_RESERVE_FLAGS,
    )


def _price_at(widths: np.ndarray, penalties: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Marginal demand-curve price at shortfall ``s`` on a stepped curve.

    ``widths`` is ``(n_steps, T)``, ``penalties`` ``(n_steps,)`` ascending
    cheapest-first; ``s`` is ``(n_probe, T)``. Band index = number of cumulative
    band edges strictly below the probe point.
    """
    edges = np.cumsum(widths, axis=0)  # (n_steps, T)
    idx = (s[None, :, :] > edges[:, None, :]).sum(axis=0)
    idx = np.clip(idx, 0, penalties.shape[0] - 1)
    return penalties[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--hours", type=int, default=8760)
    args = ap.parse_args()

    out: dict = {
        "probe": "nyiso-119 ex-ante SENY increment-tier construction diff (no solve)",
        "mechanism": "nyiso_seny_rcpf_increment_step",
        "instrument": (
            "ReserveDesign family requirement + ordc_penalties + "
            "ordc_step_widths, built twice at one HEAD; no dual, no held_mw"
        ),
        "control_is": (
            "the DESIGNATED KEEPER's own recipe "
            "(2026-08-03-nyiso-118-seny-span), nyiso_ordc_measured_step_span "
            "already ARMED"
        ),
        "published_increment_rcpf": NYISO_SENY_30MIN_INCREMENT_RCPF,
        "published_base_mw": SENY_BASE_MW,
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
            wa = np.broadcast_to(
                w_a if w_a.ndim == 2 else w_a[:, None], (w_a.shape[0], args.hours)
            )
            wb = np.broadcast_to(
                w_b if w_b.ndim == 2 else w_b[:, None], (w_b.shape[0], args.hours)
            )
            # DECISIVE construction test: does the demand curve's PRICE change
            # anywhere the LP can actually reach? Shortfall is bounded above by
            # the hour's requirement (held >= 0), so the reachable domain is
            # [0, requirement[t]] — width beyond it is unreachable padding and a
            # width delta there is representational, not economic.
            n_probe = 64
            frac = (np.arange(n_probe) + 0.5) / n_probe  # band midpoints
            s_grid = req_a[None, :] * frac[:, None]  # (n_probe, T)
            price_off = _price_at(wa, p_a, s_grid)
            price_on = _price_at(wb, p_b, s_grid)
            same_price = bool(np.array_equal(price_off, price_on))
            signed = price_on - price_off  # <0 == the increment tier prices LOWER
            dp = np.abs(signed)

            rows[name] = {
                "reachable_price_identical": same_price,
                "reachable_max_abs_price_delta": float(dp.max()),
                "reachable_hours_price_differs": int((dp.max(axis=0) > 0).sum()),
                # Direction: adding a CHEAPER tier below the base can only price
                # the same or lower at a given shortfall MW, never higher.
                "reachable_price_never_increases": bool((signed <= 0).all()),
                "reachable_probe_points_priced_lower": int((signed < 0).sum()),
                "reachable_probe_points_priced_higher": int((signed > 0).sum()),
                "min_penalty_off": float(p_a.min()),
                "min_penalty_on": float(p_b.min()),
                "max_penalty_off": float(p_a.max()),
                "max_penalty_on": float(p_b.max()),
                "n_steps_off": int(w_a.shape[0]),
                "n_steps_on": int(w_b.shape[0]),
                "widths_hourly_off": bool(w_a.ndim == 2),
                "widths_hourly_on": bool(w_b.ndim == 2),
                "requirement_identical": bool(np.array_equal(req_a, req_b)),
                "penalties_identical": bool(np.array_equal(p_a, p_b)),
                "widths_identical": bool(
                    wa.shape == wb.shape and np.array_equal(wa, wb)
                ),
                "requirement_mean": float(req_a.mean()),
                # The construction-consistency identity nyiso-118 restored:
                # total step width == the hour's requirement. It must SURVIVE.
                "hours_totalwidth_ne_requirement_off": int(
                    (~np.isclose(wa.sum(axis=0), req_a)).sum()
                ),
                "hours_totalwidth_ne_requirement_on": int(
                    (~np.isclose(wb.sum(axis=0), req_b)).sum()
                ),
            }

        # --- SENY-specific construction detail -----------------------------
        seny_off, seny_on = fam_off[NYISO_SENY_30MIN_FAMILY], fam_on[
            NYISO_SENY_30MIN_FAMILY
        ]
        req = np.asarray(seny_off.requirement, dtype=float)
        w_on = np.asarray(seny_on.ordc_step_widths, dtype=float)
        p_on = np.asarray(seny_on.ordc_penalties, dtype=float)
        w_off = np.asarray(seny_off.ordc_step_widths, dtype=float)
        p_off = np.asarray(seny_off.ordc_penalties, dtype=float)
        increment_expected = np.maximum(0.0, req - SENY_BASE_MW)
        base_expected = np.minimum(SENY_BASE_MW, req)

        # What the two curves charge for the shortfalls the KEEPER actually had.
        short = np.asarray(KEEPER_BINDING_SHORTFALL_MW[year], dtype=float)
        keeper_hours: dict = {}
        if short.size:
            # Evaluate at a requirement of 1,800 MW — every keeper binding hour
            # sat at exactly that requirement (read from the keeper sidecar).
            peak_h = int(np.argmax(req))
            wo = w_off[:, peak_h] if w_off.ndim == 2 else w_off
            wn = w_on[:, peak_h] if w_on.ndim == 2 else w_on
            po = _price_at(wo[:, None], p_off, short[:, None])[:, 0]
            pn = _price_at(wn[:, None], p_on, short[:, None])[:, 0]
            keeper_hours = {
                "requirement_mw_at_probe": float(req[peak_h]),
                "shortfall_mw": short.tolist(),
                "price_off": po.tolist(),
                "price_on": pn.tolist(),
                "all_on_at_or_below_published_increment": bool(
                    (pn <= NYISO_SENY_30MIN_INCREMENT_RCPF + 1e-9).all()
                ),
                "all_shortfalls_inside_increment_band": bool(
                    (short <= float(req[peak_h]) - SENY_BASE_MW + 1e-9).all()
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
            "price_changed_families": sorted(
                n for n, r in rows.items() if not r["reachable_price_identical"]
            ),
            "width_changed_price_identical": sorted(
                n
                for n, r in rows.items()
                if not r["widths_identical"] and r["reachable_price_identical"]
            ),
            "seny_construction": {
                "n_steps_off": int(w_off.shape[0]),
                "n_steps_on": int(w_on.shape[0]),
                "steps_gained": int(w_on.shape[0] - w_off.shape[0]),
                "penalties_off": p_off.tolist(),
                "penalties_on": p_on.tolist(),
                "first_rung_off": float(p_off[0]),
                "first_rung_on": float(p_on[0]),
                "base_ramp_penalties_unchanged": bool(
                    np.array_equal(p_on[1:], p_off)
                ),
                "increment_band_width_matches_published": bool(
                    np.allclose(w_on[0, :], increment_expected)
                ),
                "base_band_total_matches_published": bool(
                    np.allclose(w_on[1:, :].sum(axis=0), base_expected)
                ),
                "hours_increment_band_positive": int((increment_expected > 0).sum()),
                "increment_band_max_mw": float(increment_expected.max()),
                "requirement_min_mw": float(req.min()),
                "requirement_max_mw": float(req.max()),
                "keeper_binding_hours": keeper_hours,
            },
        }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=2))
    for y, blk in out["years"].items():
        s = blk["seny_construction"]
        print(f"{y}: changed={blk['changed_families']}")
        print(f"      price_changed={blk['price_changed_families']}")
        print(
            f"      SENY steps {s['n_steps_off']} -> {s['n_steps_on']}, "
            f"first rung ${s['first_rung_off']:.2f} -> ${s['first_rung_on']:.2f}, "
            f"increment>0 in {s['hours_increment_band_positive']} h"
        )
        if s["keeper_binding_hours"]:
            k = s["keeper_binding_hours"]
            print(f"      keeper binding shortfalls priced {k['price_off']}")
            print(f"                                    -> {k['price_on']}")
    print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
