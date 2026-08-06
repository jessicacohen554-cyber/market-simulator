"""miso-134 — the ``CT_PEAKER`` July-night ORDER screen. NO LP; the fleet is
assembled at HEAD under the keeper's own ``run_config.json`` and priced against
the keeper's own committed P1 zonal prices.

Pre-registration (pushed at ``06918ca1`` BEFORE this probe ran):
``results/calibration/PREREG-miso134-ct-peaker-night-order-screen-2026-08-05.md``.

The object: MISO's ``CT_PEAKER`` econ band is offered at a residual-identified
1.0 x base heat rate while the class's own measured incremental burn is
0.687/0.691 (``miso_campd_marginal_hr_summary.csv``, n = 249 units). Under the
armed ``gas_offer_net_revenue_margin`` form the gap is a fuel-INVARIANT $/MWh
net-revenue margin on the BASE marginal cost, so per tranche the full measured
swap removes exactly ``offer_markup_hr x gas_offer_margin_anchor`` $/MWh — no
fuel-path assumption enters the removal.

Statistics, in the pre-registered order:

  S-0  construction validity (GATING): assembled CT capacity vs the keeper's
       published basis (+-2 %), and cap-weighted plant-grain base heat rate vs
       the published 12.0351 (3 dp). Reported alongside: a price-taking
       reconstruction of the keeper's own July-night CT dispatch, which
       calibrates how far the price-taking bound sits from the LP.
  S-1  the markup census: physical burn / residual margin / VOM / (separately)
       the P1 startup amortization, cap-weighted $/MWh.
  S-2  THE SLACK / REACHABILITY BAR: R(delta) = MW of CT capacity that comes
       into merit when delta $/MWh is removed, at the keeper's own July-night
       zonal prices; the bar is R(delta_max) vs the miso-133 §4 shortfall
       (854 / 691 / 666 MW) in >= 2 of 3 years.
  S-3  the C1 counter-risk: the same at delta_max over all 8760 hours.
  S-4  the identification comparison (DECLARED UNGATED, descriptive): the
       residual margin vs MISO's own measured start recovery
       (startup_cost / fast_start_run_hours).
  S-5  two grains: tranche/plant (the LP's own grain, governing) and class.
  S-6  the displacement target: the entering CT band vs the COAL_PRB econ
       ladder at the same hours — gates the C7 CLAIM, not the arm.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    .venv/bin/python scripts/probes/_miso134_ct_night_order_screen.py
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    assemble_mc,
    build_base_fleet,
    build_dispatch_fleet,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.fleet.legacy_bins import apply_coal_tranches  # noqa: E402
from market_sim.data.fuel import (  # noqa: E402
    apply_coal_supply_pricing,
    resolve_fuel_prices,
)
from market_sim.data.offer_curves import apply_gas_offer_margin  # noqa: E402

BUNDLE = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso134_ct_night_order_screen.json"
YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years touched anywhere below

MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])
HOD = np.arange(8760) % 24
JULY_NIGHT = (MO == 7) & (HOD < 6)  # the miso-130/133 window, verbatim

# Pre-registered S-2 bar: the miso-133 §4 matched-set July-night shortfall.
SHORTFALL_MW = {2023: 854.0, 2024: 691.0, 2025: 666.0}
# Pre-registered S-0 reference points (miso-133 §6 / miso-117b).
S0_CT_CAP_REF_2025 = 20932.0 / 0.939  # headroom / idle share => assembled MW
S0_BASE_HR_REF = 12.0351
# Keeper C1 CT_PEAKER volumes (payload `volErr` zoneMon sums, EIA-923 basis) —
# the S-3 band the arm must not blow through.
CT_MODEL_TWH = {2023: 14.496, 2024: 19.062, 2025: 17.479}
CT_ACTUAL_TWH = {2023: 19.199, 2024: 19.296, 2025: 18.425}


def keeper_config() -> ScenarioConfig:
    """Rebuild the keeper's own ScenarioConfig from its committed run_config."""
    raw = json.loads((BUNDLE / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(
        **{k: v for k, v in raw["scenario_config"].items() if k in names}
    )


def keeper_prices(year: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Return the keeper's P1 (zone x hour) price frame and (T,) ISO demand."""
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"] if "pass" in sysf else sysf
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    demand = (
        sysf.pivot_table(index="hour", columns="zone", values="demand")
        .sum(axis=1)
        .to_numpy()
    )
    return price, demand


def keeper_class_mw(year: int, klass: str) -> np.ndarray:
    """Return the keeper's own (T,) P1 dispatch MW for one reporting class."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == klass)]
    out = np.zeros(8760)
    out[ch["hour"].to_numpy()] = ch["mw"].to_numpy()
    return out


def build_year(cfg: ScenarioConfig, year: int):
    """Assemble the keeper's own dispatch fleet and offer basis for ``year``.

    Reproduces ``runner.py``'s chain exactly: fleet -> arrays -> resolved
    delivered fuel prices -> ``assemble_mc`` -> the coal-tranche and gas
    net-revenue-margin offer adjustments. Returns the bid basis ``mc_base``
    (no startup markup — that is the P1 adder, reported separately in S-1).
    """
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    _, demand = keeper_prices(year)

    raw_fleet = load_fleet_from_csv(
        "MISO", iso_config, year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw_fleet, "MISO", cfg)
    base = build_base_fleet(bins, "MISO", iso_config, zone_names, cfg, [], [],
                            year, None, vintage_year=year, legacy_n_bins=0)
    fleet, fuel_fracs, _, _ = build_dispatch_fleet(
        base, bins, [], "MISO", year, zone_names, cfg)

    overlay = HISTORIC_OUTAGE_OVERLAY_BY_ISO.get("MISO", cfg.historic_outage_overlay)
    fleet_cfg = (cfg if overlay == cfg.historic_outage_overlay
                 else dataclasses.replace(cfg, historic_outage_overlay=overlay))
    arrays = generators_to_fleet_arrays(
        fleet, zone_names, hours=8760, iso="MISO", config=fleet_cfg,
        load_shape=demand, year=year)

    fuel_prices = resolve_fuel_prices(cfg, arrays, year)
    apply_coal_supply_pricing(fuel_prices, fleet, cfg, year)
    mc_base = assemble_mc(
        arrays, fuel_prices, 0.0, cfg.nox_price,
        so2=(arrays.so2_rate, cfg.so2_price),
    )
    apply_coal_tranches(mc_base, fleet, arrays, fuel_fracs, fuel_prices, cfg,
                        year=year)
    apply_gas_offer_margin(mc_base, fleet, fuel_prices, cfg)
    return raw_fleet, fleet, arrays, fuel_prices, mc_base, zone_names


def _tranche_frame(fleet, arrays, zone_names) -> pd.DataFrame:
    """Per-tranche static table: class, band suffix, zone index, cap, markup."""
    rows = []
    z_of = {n: i for i, n in enumerate(zone_names)}
    for i, g in enumerate(fleet):
        uid = str(g.unit_id)
        m = re.search(r"_p(\d+)_([a-z0-9]+)$", uid)
        rows.append({
            "i": i,
            "klass": str(getattr(g, "plant_group", "") or ""),
            "fuel": str(getattr(g, "fuel_type", "") or ""),
            "plant": int(m.group(1)) if m else -1,
            "band": m.group(2) if m else "",
            "zi": z_of.get(str(g.zone), 0),
            "pmax": float(arrays.pmax[i]),
            "markup_hr": float(getattr(g, "offer_markup_hr", 0.0) or 0.0),
            "startup_per_mw": float(getattr(g, "startup_cost_per_mw", 0.0) or 0.0),
            "run_h": float(getattr(g, "fast_start_run_hours", 0.0) or 0.0),
            "coal_supply": str(getattr(g, "coal_supply", "") or ""),
        })
    return pd.DataFrame(rows)


def screen() -> dict:
    cfg = keeper_config()
    anchor = float(cfg.gas_offer_margin_anchor)
    out = {"anchor_per_mmbtu": anchor, "years": {}}

    for year in YEARS:
        raw_fleet, fleet, arrays, fuel_prices, mc_base, zone_names = build_year(
            cfg, year)
        price_df, _ = keeper_prices(year)
        price = price_df.reindex(columns=zone_names).to_numpy()      # (T, Z)
        tf = _tranche_frame(fleet, arrays, zone_names)

        # ---- S-0 construction validity -----------------------------------
        ct_raw = [p for p in raw_fleet if str(p.plant_group) == "CT_PEAKER"]
        cap_r = np.array([float(p.pmax_mw) for p in ct_raw])
        hr_r = np.array([float(p.heat_rate) for p in ct_raw])
        base_hr = float((cap_r * hr_r).sum() / cap_r.sum())

        ct = tf[tf.klass == "CT_PEAKER"]
        ct_cap = float(ct.pmax.sum())

        # ---- offers and per-tranche delta ---------------------------------
        idx = ct.i.to_numpy()
        offer = mc_base[idx]                                          # (n, T)
        zi = ct.zi.to_numpy()
        zprice = price[:, zi].T                                       # (n, T)
        avail = arrays.availability[idx]                              # (n, T)
        cap = ct.pmax.to_numpy()[:, None]
        availcap = cap * avail
        # The full measured swap removes exactly markup_hr x anchor $/MWh,
        # fuel-invariant by the margin form's construction (K5: no tuned delta).
        # BAND-SCOPED to the ECON tranches, which is the only band PREREG §5's
        # arm moves: the `peak` band's markup is the DELIBERATE MISO-cap
        # scarcity wall (peak 4.0 vs phys_peak 1.0, adjudicated in
        # backcast_config.py) and the committed band is already measured-
        # grounded at 1.025 = phys_committed. Removing either would be a
        # different, un-pre-registered arm.
        econ_band = ct.band.str.startswith("econ").to_numpy()
        dmax = ct.markup_hr.to_numpy() * anchor * econ_band           # (n,)

        # price-taking reconstruction of the keeper's own July-night dispatch
        below0 = offer <= zprice
        recon_night = float((availcap * below0)[:, JULY_NIGHT].sum(axis=0).mean())
        keeper_night = float(keeper_class_mw(year, "CT_PEAKER")[JULY_NIGHT].mean())

        # ---- S-1 markup census (July night, cap-weighted) ------------------
        mk_all = ct.markup_hr.to_numpy() * anchor                     # $/MWh
        mk_dollars = dmax                                             # $/MWh
        w = ct.pmax.to_numpy()
        pos = mk_dollars > 0
        band_key = np.where(ct.band.str.startswith("econ").to_numpy(), "econ",
                            ct.band.to_numpy())
        band_census = {}
        for b in sorted(set(band_key)):
            m = band_key == b
            band_census[str(b)] = {
                "cap_mw": round(float(w[m].sum()), 1),
                "markup_capwtd_per_mwh": round(
                    float((mk_all[m] * w[m]).sum() / max(w[m].sum(), 1e-9)), 3),
                "moved_by_arm": bool(b == "econ"),
            }
        # measured start recovery on the same tranches (S-4)
        start_rec = np.where(ct.run_h.to_numpy() > 0,
                             ct.startup_per_mw.to_numpy()
                             / np.maximum(ct.run_h.to_numpy(), 1.0), np.nan)
        s4_ok = np.isfinite(start_rec) & (w > 0)

        # ---- S-2 reachability curve ---------------------------------------
        def R(delta_vec, mask):
            """Mean MW newly at-or-below price over ``mask`` hours."""
            below_d = (offer - delta_vec[:, None]) <= zprice
            gained = (availcap * (below_d & ~below0))[:, mask].sum(axis=0)
            return float(gained.mean())

        grid = {}
        step = 1.0
        dmax_cap = float(np.nanmax(dmax)) if dmax.size else 0.0
        for d in np.arange(0.0, dmax_cap + step, step):
            grid[round(float(d), 1)] = round(
                R(np.minimum(dmax, d), JULY_NIGHT), 1)
        r_full_night = R(dmax, JULY_NIGHT)
        r_full_all = R(dmax, np.ones(8760, dtype=bool))

        # ---- S-3 annual energy at price-taking ----------------------------
        below_full = (offer - dmax[:, None]) <= zprice
        annual_twh = float((availcap * (below_full & ~below0)).sum() / 1e6)
        # S-3b, DISCLOSED REFINEMENT (not pre-registered): the raw bound above
        # ignores the demand constraint entirely and is very loose. The RATIO
        # E_pt(delta_max) / E_pt(0) carries the same price-taking bias in
        # numerator and denominator, so it cancels; applied to the keeper's OWN
        # annual CT_PEAKER energy it is a far tighter read of the same object.
        e_pt_0 = float((availcap * below0).sum())
        e_pt_d = float((availcap * below_full).sum())
        ratio_ann = e_pt_d / max(e_pt_0, 1e-9)
        n_pt_0 = float((availcap * below0)[:, JULY_NIGHT].sum())
        n_pt_d = float((availcap * below_full)[:, JULY_NIGHT].sum())
        ratio_night = n_pt_d / max(n_pt_0, 1e-9)

        # ---- S-5 class grain ----------------------------------------------
        lw = price_df.reindex(columns=zone_names).to_numpy().mean(axis=1)
        econ_m = econ_band
        cls_offer = (offer[econ_m] * availcap[econ_m]).sum(axis=0) / np.maximum(
            availcap[econ_m].sum(axis=0), 1e-9)
        cls_d = float((dmax[econ_m] * w[econ_m]).sum() / max(w[econ_m].sum(), 1e-9))
        cls_gap_night = float((cls_offer - lw)[JULY_NIGHT].mean())

        # ---- S-6 displacement target ---------------------------------------
        prb = tf[(tf.fuel == "coal") & (tf.coal_supply == "prb")
                 & (tf.band.str.startswith("econc"))]
        prb_offer = mc_base[prb.i.to_numpy()]
        prb_marg = np.nanmax(
            np.where(prb_offer <= price[:, prb.zi.to_numpy()].T, prb_offer, np.nan),
            axis=0)
        ct_entering = np.where(below_full & ~below0, offer - dmax[:, None], np.nan)
        ct_entering_p50 = np.nanmedian(ct_entering[:, JULY_NIGHT])
        # MW-weighted share of the NEWLY-ENTERING capacity that prices below
        # the hour's OWN marginal PRB offer — i.e. the share that could
        # actually displace coal rather than land above it. Restricted to
        # entering (gained) tranche-hours; non-entering cells are excluded,
        # not counted as False (the defect in the first construction).
        gained = below_full & ~below0
        gmw = (availcap * gained)[:, JULY_NIGHT]
        under = ((offer - dmax[:, None])[:, JULY_NIGHT]
                 < prb_marg[JULY_NIGHT][None, :]) & gained[:, JULY_NIGHT]
        entering_below_share = float(
            (availcap[:, JULY_NIGHT] * under).sum() / max(gmw.sum(), 1e-9))

        out["years"][str(year)] = {
            "S0": {
                "assembled_ct_pmax_mw": round(ct_cap, 1),
                "assembled_ct_plants": int(len(ct_raw)),
                "cap_wtd_plant_base_hr": round(base_hr, 4),
                "ref_base_hr": S0_BASE_HR_REF,
                "ref_ct_cap_mw_2025": round(S0_CT_CAP_REF_2025, 1),
                "keeper_july_night_ct_mw": round(keeper_night, 1),
                "price_taking_recon_july_night_ct_mw": round(recon_night, 1),
                "price_taking_over_keeper_ratio": round(
                    recon_night / max(keeper_night, 1e-9), 3),
            },
            "S1": {
                "band_census": band_census,
                "availability_capwtd_july_night": round(
                    float(availcap[:, JULY_NIGHT].sum()
                          / max((cap * np.ones_like(avail))[:, JULY_NIGHT].sum(),
                                1e-9)), 4),
                "ct_cap_with_markup_mw": round(float(w[pos].sum()), 1),
                "ct_cap_with_markup_share": round(
                    float(w[pos].sum() / w.sum()), 4),
                "residual_margin_econ_capwtd_per_mwh": round(
                    float((mk_dollars[econ_band] * w[econ_band]).sum()
                          / max(w[econ_band].sum(), 1e-9)), 3),
                "residual_margin_capwtd_per_mwh": round(
                    float((mk_dollars * w).sum() / w.sum()), 3),
                "residual_margin_p50_per_mwh": round(
                    float(np.median(mk_dollars[pos])) if pos.any() else 0.0, 3),
                "july_night_offer_capwtd_per_mwh": round(
                    float(((offer * availcap)[:, JULY_NIGHT].sum())
                          / max(availcap[:, JULY_NIGHT].sum(), 1e-9)), 2),
            },
            "S2": {
                "delta_max_capwtd_per_mwh": round(cls_d, 3),
                "delta_max_max_per_mwh": round(dmax_cap, 3),
                "R_full_july_night_mw": round(r_full_night, 1),
                "shortfall_mw": SHORTFALL_MW[year],
                "PASS": bool(r_full_night >= SHORTFALL_MW[year]),
                "reachability_curve_mw_by_delta": grid,
            },
            "S3": {
                "R_full_all_hours_mw": round(r_full_all, 1),
                "annual_newly_in_merit_twh_upper_bound": round(annual_twh, 3),
                "ratio_estimator_annual_multiple": round(ratio_ann, 4),
                "ratio_estimator_july_night_multiple": round(ratio_night, 4),
                "keeper_ct_peaker_twh": CT_MODEL_TWH[year],
                "actual_ct_peaker_twh": CT_ACTUAL_TWH[year],
                "keeper_c1_ratio": round(
                    CT_MODEL_TWH[year] / CT_ACTUAL_TWH[year], 4),
                "predicted_arm_ct_twh_ratio_estimator": round(
                    CT_MODEL_TWH[year] * ratio_ann, 3),
                "predicted_arm_c1_ratio": round(
                    CT_MODEL_TWH[year] * ratio_ann / CT_ACTUAL_TWH[year], 4),
                "headroom_to_parity_twh": round(
                    CT_ACTUAL_TWH[year] - CT_MODEL_TWH[year], 3),
            },
            "S4": {
                "measured_start_recovery_capwtd_per_mwh": round(
                    float((start_rec[s4_ok] * w[s4_ok]).sum() / w[s4_ok].sum())
                    if s4_ok.any() else float("nan"), 3),
                "n_tranches_with_measured_run": int(s4_ok.sum()),
                "residual_over_measured_multiple": None,
            },
            "S5": {
                "class_grain_capwtd_offer_july_night": round(
                    float(cls_offer[JULY_NIGHT].mean()), 2),
                "class_grain_lw_price_july_night": round(
                    float(lw[JULY_NIGHT].mean()), 2),
                "class_grain_offer_minus_price": round(cls_gap_night, 2),
                "class_grain_delta_max": round(cls_d, 3),
                "class_grain_PASS": bool(cls_d >= cls_gap_night),
            },
            "S6": {
                "prb_econ_marginal_offer_july_night_p50": round(
                    float(np.nanmedian(prb_marg[JULY_NIGHT])), 2),
                "entering_ct_offer_july_night_p50": (
                    None if not np.isfinite(ct_entering_p50)
                    else round(float(ct_entering_p50), 2)),
                "entering_ct_offer_july_night_p25": round(float(np.nanpercentile(
                    ct_entering[:, JULY_NIGHT], 25)), 2),
                "entering_ct_offer_july_night_p75": round(float(np.nanpercentile(
                    ct_entering[:, JULY_NIGHT], 75)), 2),
                "entering_mw_share_below_hourly_marginal_prb": round(
                    entering_below_share, 4),
                "prb_econ_cap_mw": round(float(prb.pmax.sum()), 1),
            },
        }
        s1 = out["years"][str(year)]["S1"]
        s4 = out["years"][str(year)]["S4"]
        if s4["measured_start_recovery_capwtd_per_mwh"] > 0:
            s4["residual_over_measured_multiple"] = round(
                s1["residual_margin_econ_capwtd_per_mwh"]
                / s4["measured_start_recovery_capwtd_per_mwh"], 2)
        # Release the big (n_gen, T) blocks before the next year is built.
        # Rebound to None rather than `del`ed: the nested R() closes over
        # `offer` / `zprice` / `availcap`, and deleting them leaves the closure
        # referencing unbound names.
        del avail, mc_base, fuel_prices
        offer = zprice = availcap = below0 = below_full = None
        print(f"  {year} done", flush=True)
    return out


def main() -> None:
    record = {
        "session": "miso-134",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "bundle": "results/calibration/miso132_ccmin_B",
        "prereg": ("results/calibration/"
                   "PREREG-miso134-ct-peaker-night-order-screen-2026-08-05.md"),
        "prereg_pushed_at": "06918ca1",
        "note": ("pre-registered ORDER screen; NO LP solved. S-4 declared "
                 "UNGATED (descriptive). S-6 gates the C7 claim only."),
        "screen": screen(),
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
