"""capx D50 — whole-fleet census of the CCS retrofit screen's HOUR CEILING under the
capex-scaling repair, per ISO, zero solve.

For every gas-CC unit in an ISO's rebuilt base fleet (the repo's own ``build_base_fleet``:
tranche heat rate, measured plant CO2 rate, EFORd, VOM, vintage) this probe evaluates the
screen's own clearing arithmetic (``ccs.py::apply_ccs_retrofit``; D49 §1.2) at the hour
ceiling — every hour in merit at the per-hour uplift Δ — on THREE bars:

* ``flat``   — the shipped screen: ``capex_learned/12`` charged per MW to every host;
* ``scaled`` — capx D50 seam 1: the same bar × ``captured / captured_ref``
  (``ccs.py::ccs_retrofit_captured_ref_t_per_mwh``, 0.32319 t/MWh);
* ``scaled + CHP excluded`` — seams 1 and 2 together (``plant_group == "CC_CHP"`` removed).

The learned capex is the tracker's path with NO own conversions fed back (what an arm
that converts nothing sees), and each ISO's gas and RGGI/CARB carbon come from the same
resolved golden-posture config the t1f legs solve. A ceiling clearance is a NECESSARY
condition for conversion, never a prediction of it (the surface decides the rest), so the
census bounds the arm from above and measures how much of the shipped screen's candidate
pool each seam removes — the PREDECL-capx-d50 §2.5 instrument.

Usage::

    uv run python scripts/probes/_capxd50_scaled_ceiling_census.py \\
        --isos ERCOT NEISO PJM MISO --out results/calibration/capxd50_scaled_ceiling_census.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_full_horizon import reference_config  # noqa: E402

from market_sim.config.constants import FUEL_CO2_FACTOR_PER_MMBTU  # noqa: E402
from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config  # noqa: E402
from market_sim.data.fleet.assembly import build_base_fleet, load_or_synthesize_bins  # noqa: E402
from market_sim.data.fuel.trajectories import resolve_annual_gas_price  # noqa: E402
from market_sim.model.capacity_evolution.ccs import (  # noqa: E402
    _adjust_retrofit_capex,
    _is_cogeneration_host,
    ccs_retrofit_captured_ref_t_per_mwh,
)
from market_sim.model.capacity_evolution.new_entry import CumulativeDeployment  # noqa: E402
from market_sim.model.capacity_evolution.retirements import _THERMAL_PLANT_LIFE_YEARS  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.ira import CCUS_45Q_CREDIT_PER_TON  # noqa: E402

HOURS = 8760


def _capex_path_no_own(cfg, years: list[int]) -> dict[int, float]:
    """The tracker's learned capex with no own conversions fed back."""
    cum = CumulativeDeployment.initial()
    out: dict[int, float] = {}
    for y in years:
        out[y] = _adjust_retrofit_capex(
            cfg.ccs_retrofit_capex_kw, cum.get("gas_cc_ccs")
        )
        cum.advance_year({})
    return out


def _ceiling_terms(gen, cfg, gas: float, carbon: float) -> dict:
    """Δ, the ceiling uplift and the flat bar denominator terms for one host."""
    hr, er = float(gen.heat_rate), float(gen.emission_rate_co2)
    captured = er * cfg.ccs_retrofit_capture_rate
    q45 = CCUS_45Q_CREDIT_PER_TON * captured
    b_unab = hr * gas + gen.vom + er * carbon
    b_post = (
        hr * (1.0 + cfg.ccs_retrofit_hr_penalty) * gas
        + gen.vom
        + cfg.ccs_retrofit_vom_adder
        + er * (1.0 - cfg.ccs_retrofit_capture_rate) * carbon
        + captured * cfg.co2_transport_storage_cost
        - q45
    )
    delta = b_unab - b_post
    avail = max(0.0, 1.0 - float(gen.eford))
    dfom = (
        cfg.fixed_om_gas_cc_ccs * cfg.retirement_fom_multiplier_gas_cc_ccs
        - cfg.fixed_om_gas_cc * cfg.retirement_fom_multiplier_gas_cc
    ) * 1000.0
    return {
        "hr": hr,
        "er": er,
        "captured": captured,
        "delta": delta,
        "avail": avail,
        "ceiling_uplift": delta * avail * HOURS - dfom,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--isos", nargs="*", default=["ERCOT", "NEISO", "PJM", "MISO"])
    ap.add_argument("--years", nargs="*", type=int, default=[2028, 2029, 2030])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    report: dict = {"isos": {}}
    fac = FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"]
    for iso in args.isos:
        cfg = apply_iso_scenario_defaults(
            reference_config(iso, 2026, 2030, False, golden_posture=True), iso
        )
        iso_config = get_iso_config(iso)
        zone_names = list(iso_config.zone_names)
        bins = load_or_synthesize_bins(cfg, iso, iso_config, [])
        fleet = build_base_fleet(
            bins, iso, iso_config, zone_names, cfg, [], [], int(cfg.start_year)
        )
        cc = [g for g in fleet if g.fuel_type == "gas_cc"]
        capex = _capex_path_no_own(
            cfg, list(range(int(cfg.start_year), int(cfg.end_year) + 1))
        )
        captured_ref = ccs_retrofit_captured_ref_t_per_mwh(cfg)
        print(
            f"\n===== {iso}: {len(cc)} gas_cc units / {sum(g.pmax_mw for g in cc) / 1000:.1f} GW;"
            f" captured_ref {captured_ref:.5f}; key {cfg.cache_key()}"
        )
        iso_rep = {
            "cache_key_control": cfg.cache_key(),
            "captured_ref": captured_ref,
            "years": {},
        }
        for y in args.years:
            gas = resolve_annual_gas_price(cfg, y)
            carbon = resolve_carbon_price(cfg, y)
            bar_flat = capex[y] * 1000.0 / float(cfg.ira_45q_credit_window_years)
            rows = []
            for g in cc:
                remaining = max(0, _THERMAL_PLANT_LIFE_YEARS - (y - int(g.online_year)))
                if remaining < cfg.ccs_retrofit_min_remaining_life:
                    continue
                t = _ceiling_terms(g, cfg, gas, carbon)
                bar_scaled = bar_flat * t["captured"] / captured_ref
                rows.append(
                    {
                        "unit_id": g.unit_id,
                        "mw": float(g.pmax_mw),
                        "chp": _is_cogeneration_host(g),
                        "hr": t["hr"],
                        "er": t["er"],
                        "er_over_phys": (t["er"] / (t["hr"] * fac))
                        if t["hr"] > 0
                        else None,
                        "delta": t["delta"],
                        "ceiling_uplift": t["ceiling_uplift"],
                        "bar_flat": bar_flat,
                        "bar_scaled": bar_scaled,
                        "ratio_scaled": (t["ceiling_uplift"] / bar_scaled)
                        if bar_scaled > 0
                        else None,
                        "clears_flat": bool(t["ceiling_uplift"] >= bar_flat),
                        "clears_scaled": bool(t["ceiling_uplift"] >= bar_scaled),
                    }
                )

            def mw(pred):
                return sum(r["mw"] for r in rows if pred(r))

            summ = {
                "gas": gas,
                "carbon": carbon,
                "capex_kw": capex[y],
                "bar_flat": bar_flat,
                "eligible_mw": mw(lambda r: True),
                "flat_mw": mw(lambda r: r["clears_flat"]),
                "flat_n": sum(1 for r in rows if r["clears_flat"]),
                "scaled_mw": mw(lambda r: r["clears_scaled"]),
                "scaled_n": sum(1 for r in rows if r["clears_scaled"]),
                "scaled_nochp_mw": mw(lambda r: r["clears_scaled"] and not r["chp"]),
                "scaled_nochp_n": sum(
                    1 for r in rows if r["clears_scaled"] and not r["chp"]
                ),
                "chp_eligible_mw": mw(lambda r: r["chp"]),
                "min_er_clearing_scaled_nochp": min(
                    (r["er"] for r in rows if r["clears_scaled"] and not r["chp"]),
                    default=None,
                ),
            }
            top = sorted(
                (r for r in rows if r["clears_scaled"] and not r["chp"]),
                key=lambda r: -r["ratio_scaled"],
            )[:12]
            print(
                f"-- {y}: gas {gas:.2f} carbon {carbon:.2f} capex {capex[y]:.1f} | eligible {summ['eligible_mw'] / 1000:.2f} GW"
                f" | flat {summ['flat_n']} / {summ['flat_mw'] / 1000:.2f} GW | scaled {summ['scaled_n']} / {summ['scaled_mw'] / 1000:.2f} GW"
                f" | scaled+noCHP {summ['scaled_nochp_n']} / {summ['scaled_nochp_mw'] / 1000:.2f} GW (min er {summ['min_er_clearing_scaled_nochp']})"
            )
            for r in top:
                print(
                    f"     {r['unit_id']:46s} {r['mw']:7.1f} MW er={r['er']:.3f} hr={r['hr']:5.2f} ratio={r['ratio_scaled']:.3f}"
                )
            iso_rep["years"][y] = {"summary": summ, "rows": rows}
        report["isos"][iso] = iso_rep
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=1, default=float))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
