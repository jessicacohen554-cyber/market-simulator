"""capx D43: the dispersion-carrying entry expectation replayed at the screen grain.

The D39 object (``docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md``
§0/§3.1): the zone-flat tail-free stack re-price five ISOs share discards the
energy leg's DISPERSION, handing a new CAISO peaker 0-7 % and a new CC 7-92 %
of the energy margin the model's own realized surface pays. This probe replays
the entry/storage screens' own value arithmetic (the L-1 replay's functions,
``scripts/probes/entry_signal_l1_dual_replay.py`` — the instrument D39 §3
validated) on FOUR constructions of the screens' price object per CAISO
decision step, holding everything else identical, and scores each against the
entering year's REALIZED surface (D39 §2's expected-vs-realized instrument):

* ``shipped_signal`` — the committed ``screen_signal_diag`` dump (the D39
  basis; must reproduce the committed L-1 replay's rows).
* ``dual_prior_solve`` — the prior year's realized zonal duals hour-aligned
  (the disarm corner: naive expectations).
* ``fwd_expectation_prior_solve`` — the hour-aligned composition
  ``duals[z,t] + (S_next[t] - S_curr[t])`` (``entry_forward_expectation_signal``),
  with ``S_curr`` evaluated OFFLINE on the dump's own merit stack at the
  reconstructed current-year net load (no adder: CAISO's screens are
  tail-free).
* ``dispersion_prior_solve`` — the D43 construction
  (``runner._dispersion_expectation_signal``): each zone's realized
  price-duration curve indexed by the entering year's headroom rank on the
  current year's headroom distribution.

Two dump modes for the headroom terms:

* ``--mode basis`` (pre-solve, the D39 basis dumps): ``headroom_next`` is the
  dump's own ``installed_headroom_mw``; ``headroom_curr`` is RECONSTRUCTED on
  the seam's own basis — the hindcast's current-year demand (the same
  ``load_demand`` call the seam makes) minus the prior-year VRE the dump
  netted (``demand_next(loader) - net_load_mw(dump)``, exact), against the
  dump's own top of stack. The reconstruction is gated: the implied VRE must
  be non-negative and shaped like the dump's VRE potential.
* ``--mode arm`` (post-solve): the ARM run's dumps carry both headroom terms,
  the duals and the composed signal (the L-5 extension), so the construction
  is validated in-run (offline == the signal the screens consumed, to the
  float) and the expected-vs-realized closure is EXACT for the entering year
  whose realized duals the next dump carries — no keeper stand-in.

Realized surfaces: the run's own next-year duals when the dump carries them
(``--mode arm``), else the designated keeper's P1 hourly sidecar for the
entering year (D39 §2's stand-in, labelled). Prior-year duals for the
constructions come from the same source.

MEASUREMENT ONLY — no mechanism armed here, no solve, no LP. Zero DOF: the
constructions carry no coefficient. Usage::

    uv run python scripts/probes/entry_signal_d43_dispersion_replay.py \
        --mode basis --bundle results/hindcast/caiso-2021-2025-realized-dumps \
        --duals-bundle results/calibration/caiso231_b1_ungrounded \
        --out results/calibration/entry_signal_d43_dispersion_replay_caiso.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia930.demand import load_demand  # noqa: E402
from market_sim.data.fuel import resolve_annual_gas_price  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.runner import (  # noqa: E402
    _dispersion_expectation_signal,
    _forward_expectation_signal,
    _headroom_rank,
)
from scripts.probes.entry_signal_l1_dual_replay import (  # noqa: E402
    ISO_DUAL_ZONE_EXCLUDE,
    ISO_STEPS,
    _THERMAL,
    dual_price_array,
    load_dump,
    shape_stats,
    storage_screen,
    thermal_margins,
    vre_capture,
)

STORAGE_REF = ("li_ion_4hr", "iron_air")


def load_config_filtered(bundle: Path) -> tuple[ScenarioConfig, bool]:
    """Rebuild the run's ScenarioConfig, dropping fields deleted since (rule 26).

    Returns ``(config, key_reproduced)``: the committed D39 basis predates the
    2026-09-02 ``caiso_bidir_intertie`` deletion, so its run_config no longer
    reconstructs verbatim; the screens' arithmetic reads none of the dropped
    keys. Whether the cache key still reproduces is REPORTED, never assumed.
    """
    rc = json.loads((bundle / "run_config.json").read_text())
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    dropped = sorted(k for k in rc["scenario_config"] if k not in valid)
    cfg = ScenarioConfig(
        **{k: v for k, v in rc["scenario_config"].items() if k in valid}
    )
    meta = json.loads((bundle / "meta.json").read_text())
    return cfg, cfg.cache_key() == meta["cache_key"], dropped


def seam_demand_total(cfg: ScenarioConfig, iso: str, year: int) -> np.ndarray:
    """The hindcast seam's own entering/current-year demand total ``(T,)``.

    Mirrors the two ``load_demand`` calls in ``runner.py`` (the realized
    per-year loader, ``include_interchange=False`` for an ISO with an import
    node — CAISO's WECC seam is a priced interchange fleet).
    """
    iso_config = get_iso_config(iso)
    has_import_node = any(z.endswith("_import") for z in iso_config.zone_names)
    dem = load_demand(
        iso,
        year,
        iso_config,
        td_loss_factor=cfg.td_loss_factor,
        include_interchange=not has_import_node,
        strict_demand_profile=cfg.strict_demand_profile,
        ercot_tie_zonal_interchange=cfg.ercot_tie_zonal_interchange,
    )
    if cfg.hours < dem.shape[1]:
        dem = dem[:, : cfg.hours]
    return dem.sum(axis=0)


def stack_price(dump: dict, net_load: np.ndarray) -> np.ndarray:
    """Re-price a net load on the dump's own merit stack (the non-hourly path).

    ``np.searchsorted`` into the cumulative availability-derated capacity,
    exactly as ``_lookahead_reprice_signal`` does; validated by reproducing
    the dump's own ``price_base_usd_mwh`` from its own ``net_load_mw``.
    """
    mc_sorted = np.asarray(dump["mc_sorted_usd_mwh"], dtype=float)
    cum_cap = np.cumsum(np.asarray(dump["cap_sorted_mean_mw"], dtype=float))
    idx = np.searchsorted(cum_cap, np.clip(net_load, 0.0, None), side="left")
    return mc_sorted[np.minimum(idx, mc_sorted.size - 1)]


def realized_energy_legs(prices: np.ndarray, gas: float, carbon: float, cfg) -> dict:
    """``sum_t max(mean_z(price) - vc, 0)`` per thermal tech at the screen's vc."""
    return {
        t: r["energy_margin_per_mw_yr"]
        for t, r in thermal_margins(prices, gas, carbon, cfg, None).items()
    }


def ratio(a: float, b: float) -> float | None:
    """Expected / realized, ``None`` when the realized leg is zero."""
    return None if b == 0 else round(a / b, 3)


def main() -> None:
    """CLI entry point: emit the four arms, the closure table and the gates."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="CAISO", choices=sorted(ISO_STEPS))
    ap.add_argument("--mode", choices=("basis", "arm"), default="basis")
    ap.add_argument("--bundle", required=True, help="dumps bundle (basis or arm run)")
    ap.add_argument(
        "--duals-bundle", required=True, help="keeper bundle (hourly sidecars)"
    )
    ap.add_argument(
        "--committed-replay",
        default="results/calibration/entry_signal_l1_dual_replay_caiso.json",
        help="the committed L-1 replay the shipped arm must reproduce (basis mode)",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    iso = args.iso.upper()
    bundle = REPO / args.bundle
    duals_bundle = REPO / args.duals_bundle
    step_prior, step_driver = ISO_STEPS[iso]
    cfg, key_ok, dropped = load_config_filtered(bundle)
    all_zone_names = list(get_iso_config(iso).zone_names)
    excluded = [z for z in ISO_DUAL_ZONE_EXCLUDE.get(iso, ()) if z in all_zone_names]
    zone_names = [z for z in all_zone_names if z not in excluded]
    # Every zone row of the run's own dumps (arm mode) — the keeper's
    # in-state rows are matched by name; the seam node is dropped from both.
    run_zone_idx = [all_zone_names.index(z) for z in zone_names]

    result: dict = {
        "probe": "entry_signal_d43_dispersion_replay",
        "finding": "docs/handoffs/FINDING-capx-d43-caiso-dispersion-2026-09-02.md",
        "object": "docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md §0/§3.1/§7.2",
        "iso": iso,
        "mode": args.mode,
        "bundle": str(args.bundle),
        "duals_bundle": str(args.duals_bundle),
        "bundle_cache_key_reproduced_at_head": bool(key_ok),
        "run_config_fields_dropped_since_solve": dropped,
        "zone_names": zone_names,
        "zones_excluded_from_all_arms": excluded,
        "cost_state": "entry seed (cumulative_gw=None), identical across arms",
        "steps": {},
        "gates": {},
    }
    committed = None
    if args.mode == "basis":
        committed = json.loads((REPO / args.committed_replay).read_text())["steps"]

    gate_rows: list[dict] = []
    for step, prior in step_prior.items():
        dump = load_dump(bundle, prior, step, iso)
        sig_flat = dump["price_base_usd_mwh"] + dump["adder_usd_mwh"]
        shipped = np.tile(sig_flat[None, :], (len(zone_names), 1))
        storage_mw = float(dump["storage_power_mw"])
        gas = float(resolve_annual_gas_price(cfg, step_driver[step]))
        carbon = float(resolve_carbon_price(cfg, step_driver[step]))
        h_next = np.asarray(dump["installed_headroom_mw"], dtype=float)
        top = np.asarray(dump["top_of_stack_mw"], dtype=float)
        # --- the prior-year duals + the current-year headroom ------------
        duals_source = "keeper sidecar (D39 §2 stand-in)"
        if args.mode == "arm" and "econ_prices_usd_mwh" in dump:
            duals = np.asarray(dump["econ_prices_usd_mwh"], dtype=float)[run_zone_idx]
            duals_source = "the run's own prior-year duals (dump econ_prices_usd_mwh)"
        else:
            duals = dual_price_array(duals_bundle, prior, zone_names)
        if duals is None:
            result["steps"][str(step)] = {
                "blocked": f"no duals for prior solve {prior}"
            }
            continue
        if args.mode == "arm" and "fwd_curr_installed_headroom_mw" in dump:
            h_curr = np.asarray(dump["fwd_curr_installed_headroom_mw"], dtype=float)
            s_curr = np.asarray(dump["fwd_curr_price_base_usd_mwh"], dtype=float)
            nl_curr = np.asarray(dump["fwd_curr_net_load_mw"], dtype=float)
            headroom_source = "the run's own S_current diagnostics"
            recon_gate = {"skipped": "arm dump carries the seam's own S_current terms"}
        else:
            dem_next = seam_demand_total(cfg, iso, step)
            dem_curr = seam_demand_total(cfg, iso, prior)
            vre_prior = dem_next - np.asarray(dump["net_load_mw"], dtype=float)
            nl_curr = dem_curr - vre_prior
            h_curr = top - nl_curr
            s_curr = stack_price(dump, nl_curr)
            headroom_source = (
                "reconstructed: seam load_demand(prior) - (load_demand(step) - "
                "dump net_load_mw), against the dump's top of stack"
            )
            pot = np.asarray(
                dump["wind_potential_mw"] + dump["solar_potential_mw"], float
            )
            recon_gate = {
                "implied_prior_vre_min_mw": round(float(vre_prior.min()), 1),
                "implied_prior_vre_mean_mw": round(float(vre_prior.mean()), 1),
                "corr_with_dump_vre_potential": round(
                    float(np.corrcoef(vre_prior, pot)[0, 1]), 4
                ),
                "stack_reprices_own_net_load": bool(
                    np.allclose(
                        stack_price(dump, np.asarray(dump["net_load_mw"], float)),
                        np.asarray(dump["price_base_usd_mwh"], float),
                    )
                ),
            }
            recon_gate["pass"] = bool(
                recon_gate["implied_prior_vre_min_mw"] >= -1.0
                and recon_gate["corr_with_dump_vre_potential"] > 0.9
                and recon_gate["stack_reprices_own_net_load"]
            )
        # --- the four constructions -------------------------------------
        fwd = _forward_expectation_signal(duals, sig_flat, s_curr)
        disp = _dispersion_expectation_signal(duals, h_next, h_curr)
        u = _headroom_rank(h_next, h_curr)
        arms_prices = {
            "shipped_signal": shipped,
            "dual_prior_solve": duals,
            "fwd_expectation_prior_solve": fwd,
            "dispersion_prior_solve": disp,
        }
        # --- the realized surface of the entering year -------------------
        realized_source = "keeper sidecar, entering year (D39 §2 stand-in)"
        realized = None
        if args.mode == "arm":
            nxt = step_prior.get(step + 1)
            if nxt == step:
                try:
                    d2 = load_dump(bundle, step, step + 1, iso)
                    if "econ_prices_usd_mwh" in d2:
                        realized = np.asarray(d2["econ_prices_usd_mwh"], float)[
                            run_zone_idx
                        ]
                        realized_source = "the run's OWN realized duals for the entering year (next dump)"
                except SystemExit:
                    realized = None
        if realized is None:
            realized = dual_price_array(duals_bundle, step, zone_names)
        arms: dict = {}
        for label, prices in arms_prices.items():
            arms[label] = {
                "shape": shape_stats(prices),
                "h_ge_100_system": int((prices.mean(axis=0) >= 100.0).sum()),
                "neg_hour_frac_system": round(
                    float((prices.mean(axis=0) < 0.0).mean()), 4
                ),
                "thermal_r_none": thermal_margins(prices, gas, carbon, cfg, None),
                "vre": vre_capture(prices, dump, cfg, step, zone_names, iso),
                "storage": storage_screen(prices, cfg, step, storage_mw, iso),
            }
        body: dict = {
            "prior_solve": prior,
            "driver_year": step_driver[step],
            "gas_price_per_mmbtu": round(gas, 4),
            "carbon_price": carbon,
            "storage_power_entering_mw": round(storage_mw, 1),
            "duals_source": duals_source,
            "headroom_source": headroom_source,
            "headroom_reconstruction_gate": recon_gate,
            "headroom_rank": {
                "mean_shift_vs_0.5": round(float(u.mean() - 0.5), 4),
                "frac_next_tighter_than_all_current": round(
                    float((u == 0.0).mean()), 4
                ),
                "frac_next_looser_than_all_current": round(float((u == 1.0).mean()), 4),
                "net_load_next_mean_mw": round(float(dump["net_load_mw"].mean()), 1),
                "net_load_curr_mean_mw": round(float(nl_curr.mean()), 1),
                "top_of_stack_mw": round(float(top.mean()), 1),
            },
            "arms": arms,
        }
        # --- the construction's own fixed-point / permutation gates ------
        same = _dispersion_expectation_signal(duals, h_curr, h_curr)
        # Exact up to TIES: hours with identical headroom share one mid-rank
        # and therefore one quantile (two equal-headroom hours are priced
        # equally, by design), so the multiset is reproduced to the tie
        # groups' interpolation width — reported, and gated at $0.05/MWh.
        n_ties = int(h_curr.size - np.unique(h_curr).size)
        multiset_dev = float(
            np.abs(np.sort(same, axis=1) - np.sort(duals, axis=1)).max()
        )
        body["construction_gates"] = {
            "unchanged_headroom_reproduces_each_zone_multiset": bool(
                multiset_dev <= 0.05
                and np.allclose(same.mean(axis=1), duals.mean(axis=1), atol=1e-6)
            ),
            "tied_headroom_hours_current_year": n_ties,
            "multiset_max_abs_deviation_usd_mwh": round(multiset_dev, 4),
            "entering_signal_is_within_realized_range_per_zone": bool(
                np.all(disp.max(axis=1) <= duals.max(axis=1) + 1e-9)
                and np.all(disp.min(axis=1) >= duals.min(axis=1) - 1e-9)
            ),
        }
        if args.mode == "arm" and "signal_zonal_usd_mwh" in dump:
            consumed = np.asarray(dump["signal_zonal_usd_mwh"], float)[run_zone_idx]
            body["construction_gates"]["offline_reproduces_consumed_signal"] = bool(
                np.allclose(consumed, disp)
            )
        # --- the closure table (expected vs realized) --------------------
        closure: dict = {"realized_source": realized_source}
        if realized is not None:
            real_legs = realized_energy_legs(realized, gas, carbon, cfg)
            real_shape = shape_stats(realized)
            real_stor = storage_screen(realized, cfg, step, storage_mw, iso)["techs"]
            real_vre = vre_capture(realized, dump, cfg, step, zone_names, iso)
            closure["realized"] = {
                "shape": real_shape,
                "h_ge_100_system": int((realized.mean(axis=0) >= 100.0).sum()),
                "energy_leg_per_mw_yr": real_legs,
                "storage_arbitrage_per_mw_yr": {
                    t: real_stor[t]["arbitrage_per_mw_yr"] for t in STORAGE_REF
                },
                "solar_capture_ratio_zone_row": (
                    real_vre["solar"]["capture_ratio_zone_row"]
                    if "solar" in real_vre
                    else None
                ),
            }
            rows = {}
            for label, a in arms.items():
                rows[label] = {
                    "energy_leg_ratio": {
                        t: ratio(
                            a["thermal_r_none"][t]["energy_margin_per_mw_yr"],
                            real_legs[t],
                        )
                        for t in _THERMAL
                    },
                    "energy_leg_per_mw_yr": {
                        t: a["thermal_r_none"][t]["energy_margin_per_mw_yr"]
                        for t in _THERMAL
                    },
                    "storage_arbitrage_ratio": {
                        t: ratio(
                            a["storage"]["techs"][t]["arbitrage_per_mw_yr"],
                            real_stor[t]["arbitrage_per_mw_yr"],
                        )
                        for t in STORAGE_REF
                    },
                    "solar_capture_ratio": (
                        a["vre"]["solar"]["capture_ratio_zone_row"]
                        if "solar" in a["vre"]
                        else None
                    ),
                    "daily_top4_bot4_spread": a["shape"][
                        "daily_top4_bot4_spread_system"
                    ],
                    "h_ge_100_system": a["h_ge_100_system"],
                    "margin_signs": {
                        **{t: a["thermal_r_none"][t]["sign"] for t in _THERMAL},
                        **{t: a["vre"][t]["sign"] for t in a["vre"]},
                        "storage_profitable": a["storage"]["profitable"],
                    },
                }
            closure["by_arm"] = rows
        body["closure"] = closure
        # --- basis-mode reproduction gate vs the committed L-1 replay ----
        if committed is not None and str(step) in committed:
            c = committed[str(step)]["arms"]["shipped_signal"]
            mine = arms["shipped_signal"]
            checks = []
            for t in _THERMAL:
                checks.append(
                    abs(
                        c["thermal_r_none"][t]["energy_margin_per_mw_yr"]
                        - mine["thermal_r_none"][t]["energy_margin_per_mw_yr"]
                    )
                    <= 0.1
                )
            for t, row in c["storage"]["techs"].items():
                checks.append(
                    abs(
                        row["margin_per_mw_yr"]
                        - mine["storage"]["techs"][t]["margin_per_mw_yr"]
                    )
                    <= 1.0
                )
            gate_rows.append(
                {"step": step, "shipped_reproduces_committed_l1": all(checks)}
            )
        result["steps"][str(step)] = body

    result["gates"]["shipped_vs_committed_l1"] = gate_rows
    result["gates"]["all_pass"] = bool(
        all(r["shipped_reproduces_committed_l1"] for r in gate_rows)
        and all(
            b.get("construction_gates", {}).get(
                "unchanged_headroom_reproduces_each_zone_multiset", False
            )
            and b.get("headroom_reconstruction_gate", {}).get("pass", True)
            for b in result["steps"].values()
            if "blocked" not in b
        )
    )
    out_path = Path(args.out) if Path(args.out).is_absolute() else REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {out_path}  gates_all_pass={result['gates']['all_pass']}")
    if not result["gates"]["all_pass"]:
        raise SystemExit("gates FAILED — the arm rows are not reportable")


if __name__ == "__main__":
    main()
