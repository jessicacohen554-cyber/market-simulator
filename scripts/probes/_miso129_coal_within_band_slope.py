"""miso-129 — does MISO's coal offer band lack a within-band incremental cost slope?

Adjudicates the pre-registration
``results/calibration/PREREG-miso129-coal-within-band-incremental-slope-2026-08-05.md``.

The object under test is the one miso-128 §6.4 NAMED BUT DID NOT CHARTER:

    "the model's coal offer band has no WITHIN-BAND INCREMENTAL COST SLOPE.
     Each CAMPD bin bids one price, so a plant is bang-bang in whichever band
     is marginal and SATURATES FLAT once loading clears a step."

**P1 is the premise check and it runs FIRST**, because a false premise kills the
lane with no derive output and no LP at all. It is measured at two grains (the
miso-126(a) duty), on the CAMPD limb (``fleet_to_bins`` / ``bins_to_fleet`` /
``_offer_curve_for_group``) — never ``split_coal_tranches``, which is inert by
wiring at MISO (miso-128 §4) and is evidence of nothing here.

* **Grain 1 — config resolution.** ``offer_curve_by_group`` COAL entries,
  ``econ_split_by_group``, and the ``offer_curve_smoothing_{n,exp,mid}`` fields
  that drive :func:`market_sim.data.offer_curves._econ_curve_steps`.
* **Grain 2 — assembled fleet.** The real MISO 2025 dispatch fleet built at HEAD
  under the keeper's own committed config: per coal plant, the number of econ
  tranches, the number of DISTINCT marginal-cost bases among them, and the
  max/min ratio of those bases.

P0 (construction validity) reproduces miso-128's actual-side amplitude-vs-loading
fit from the committed bench, so the step-width-vs-amplitude observation in §OBS
is expressed in the same units D-1 gates on.

No LP is solved, no bundle is produced, no year outside 2023-2025 is read
(rule 22 ``[R-HOLDOUT]``; MISO holds no ``calibration-complete`` marker).

Usage::

    uv run python scripts/probes/_miso129_coal_within_band_slope.py
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from probes import _miso128_c7_diurnal_organization as M128  # noqa: E402

REPO = M128.REPO
YEARS = (2023, 2024, 2025)
GRAIN2_YEAR = 2025
TARGET = "COAL_PRB"
OUT = REPO / "results" / "calibration" / "_miso129_coal_within_band_slope.json"

# Pre-registered P1 bars (PREREG §3 P1).
P1_HOLDS_FLAT_SHARE = (
    0.90  # premise HOLDS if >=90% of coal capacity bids ONE econ price
)
P1_FALSE_LADDER_SHARE = 0.50  # premise FALSE if >=50% of coal capacity is laddered

# Pre-registered P0 bars (PREREG §3 P0) — miso-128's committed actual-side fit.
P0_SLOPE = 0.0558
P0_SLOPE_TOL = 0.005
P0_WR2 = 0.429
P0_WR2_TOL = 0.05

# A relative tolerance for "distinct" marginal-cost bases: two tranches count as
# the same price only if their heat rates agree to this relative precision.
MC_DISTINCT_RTOL = 1e-9


# ---------------------------------------------------------------------------
# P1 grain 1 — config resolution
# ---------------------------------------------------------------------------


def grain1_config() -> dict:
    """Resolve the offer-curve config that decides whether a coal econ band ramps."""
    cfg = M128._keeper_config()
    curves = getattr(cfg, "offer_curve_by_group", None) or {}
    coal_curves = {k: dict(v) for k, v in curves.items() if "COAL" in k.upper()}
    n_curve = int(getattr(cfg, "offer_curve_smoothing_n", 0) or 0)
    return {
        "iso": str(getattr(cfg, "iso", "")),
        "use_campd_bins": bool(getattr(cfg, "use_campd_bins", False)),
        "plant_level_fleet": bool(getattr(cfg, "plant_level_fleet", False)),
        "offer_curve_by_group_coal": coal_curves,
        "econ_split_by_group": dict(getattr(cfg, "econ_split_by_group", None) or {}),
        "offer_curve_smoothing_n": n_curve,
        "offer_curve_smoothing_exp": float(
            getattr(cfg, "offer_curve_smoothing_exp", 1.0)
        ),
        "offer_curve_smoothing_mid": getattr(cfg, "offer_curve_smoothing_mid", None),
        "coal_econ_srmc_bound": bool(getattr(cfg, "coal_econ_srmc_bound", False)),
        "coal_mustrun_online_pmin": bool(
            getattr(cfg, "coal_mustrun_online_pmin", False)
        ),
        "predicted_econ_steps": n_curve if n_curve > 0 else 2,
        "ramp_builder": (
            "market_sim.data.offer_curves._econ_curve_steps via "
            "fleet/assembly.py bins_to_fleet (offer is not None limb)"
        ),
    }


# ---------------------------------------------------------------------------
# P1 grain 2 — the assembled fleet
# ---------------------------------------------------------------------------


def assemble_coal(year: int) -> dict[int, list[dict]]:
    """Return ``{plant_code: [tranche, ...]}`` for the real MISO coal fleet at HEAD.

    Built under the keeper's OWN committed config through the CAMPD limb, the
    same construction miso-128 §4 grain 2 used.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        build_base_fleet,
        build_dispatch_fleet,
        fleet_to_bins,
        load_fleet_from_csv,
    )

    cfg = M128._keeper_config()
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    raw = load_fleet_from_csv(
        "MISO",
        iso_config,
        year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw, "MISO", cfg)
    base = build_base_fleet(
        bins,
        "MISO",
        iso_config,
        zone_names,
        cfg,
        [],
        [],
        year,
        None,
        vintage_year=year,
        legacy_n_bins=0,
    )
    fleet, fuel_fracs, _, _ = build_dispatch_fleet(
        base, bins, [], "MISO", year, zone_names, cfg
    )

    by_plant: dict[int, list[dict]] = collections.defaultdict(list)
    for i, g in enumerate(fleet):
        if getattr(g, "fuel_type", None) != "coal":
            continue
        uid = str(g.unit_id)
        by_plant[int(getattr(g, "plant_code", 0))].append(
            {
                "unit_id": uid,
                "suffix": uid.rsplit("_", 1)[-1],
                "pmax_mw": float(g.pmax_mw),
                "heat_rate": float(g.heat_rate),
                "fuel_frac": float(fuel_fracs[i]),
                "coal_supply": str(getattr(g, "coal_supply", "") or ""),
                "bin_nameplate_mw": float(getattr(g, "bin_nameplate_mw", 0.0) or 0.0),
            }
        )
    return dict(by_plant)


def _n_distinct(values: list[float]) -> int:
    """Count distinct values at :data:`MC_DISTINCT_RTOL` relative precision."""
    out: list[float] = []
    for v in sorted(values):
        if not out or abs(v - out[-1]) > MC_DISTINCT_RTOL * max(abs(v), 1.0):
            out.append(v)
    return len(out)


def grain2_ladder_census(by_plant: dict[int, list[dict]]) -> dict:
    """Per coal plant: econ tranche count, distinct econ prices, and price span."""
    rows: list[dict] = []
    for code, tr in by_plant.items():
        econ = [t for t in tr if t["suffix"].startswith("econ")]
        if not econ:
            continue
        hrs = [t["heat_rate"] for t in econ]
        # The bid basis is heat_rate x fuel_frac (+ VOM); every econ tranche
        # carries fuel_frac 1.0 under coal_econ_srmc_bound, but multiply anyway
        # so the count is a MARGINAL-COST count, not a heat-rate count.
        mcs = [t["heat_rate"] * t["fuel_frac"] for t in econ]
        econ_cap = sum(t["pmax_mw"] for t in econ)
        plant_cap = sum(t["pmax_mw"] for t in tr)
        rows.append(
            {
                "plant_code": code,
                "coal_supply": econ[0]["coal_supply"],
                "plant_cap_mw": plant_cap,
                "econ_cap_mw": econ_cap,
                "n_econ_tranches": len(econ),
                "n_distinct_econ_mc": _n_distinct(mcs),
                "econ_hr_min": min(hrs),
                "econ_hr_max": max(hrs),
                "econ_hr_ratio": max(hrs) / min(hrs) if min(hrs) > 0 else float("nan"),
                "n_tranches_total": len(tr),
                "n_distinct_mc_total": _n_distinct(
                    [t["heat_rate"] * t["fuel_frac"] for t in tr]
                ),
                "suffixes": [t["suffix"] for t in tr],
                # econ step width as a share of the plant's LP capacity — the
                # granularity of the ladder, in the units D-1's std_frac uses.
                "econ_step_frac_of_cap": (
                    (econ_cap / len(econ)) / plant_cap if plant_cap > 0 else 0.0
                ),
            }
        )
    rows.sort(key=lambda r: -r["plant_cap_mw"])

    def _share(pred, subset=None) -> float:
        sel = rows if subset is None else [r for r in rows if r["plant_code"] in subset]
        tot = sum(r["plant_cap_mw"] for r in sel)
        if tot <= 0:
            return 0.0
        return sum(r["plant_cap_mw"] for r in sel if pred(r)) / tot

    return {
        "rows": rows,
        "n_plants": len(rows),
        "total_coal_cap_mw": sum(r["plant_cap_mw"] for r in rows),
        "cap_share_flat_econ": _share(lambda r: r["n_distinct_econ_mc"] == 1),
        "cap_share_laddered_econ": _share(lambda r: r["n_distinct_econ_mc"] > 1),
    }


# ---------------------------------------------------------------------------
# P0 — reproduce miso-128's actual-side amplitude-vs-loading fit
# ---------------------------------------------------------------------------


def p0_actual_fit() -> dict:
    """Cap-weighted LS of measured per-plant off-peak amplitude on loading.

    Same construction as ``_miso128_c7_diurnal_organization.amplitude_vs_level``
    on the committed bench, so this session's numbers are directly comparable to
    the finding's ``std_frac = +0.0558 x cf_off + 0.0289`` (wR2 0.429).
    """
    sidecar = M128.LD.find_registry_sidecar(REPO, M128.KEEPER_BUNDLE)
    if sidecar is None or sidecar.get("id") != M128.KEEPER_RUN:
        raise SystemExit(
            f"keeper sidecar for {M128.KEEPER_BUNDLE} not found / not {M128.KEEPER_RUN}"
        )
    plant_rows: list[dict] = []
    per_plant: dict[tuple[int, int], dict] = {}
    for year in YEARS:
        bench, model = M128.load_sides(year, sidecar)
        keys = M128.matched_keys(bench, model, TARGET)
        for k in keys:
            npl = bench[k]["npl"]
            prof = (
                np.asarray(bench[k]["mw"], float)[: M128._T]
                .reshape(-1, 24)
                .mean(axis=0)
            )
            row = {
                "year": year,
                "key": k,
                "npl": npl,
                "side": "actual",
                "cf_off": float(prof[M128.OFF].mean() / npl),
                "std_frac": float(prof[M128.OFF].std() / npl),
            }
            plant_rows.append(row)
            # Bench keys are plant codes, optionally class-qualified for a plant
            # that spans several coal classes ("1393:COAL_PRB").
            per_plant[(year, int(str(k).split(":", 1)[0]))] = row
    fit = M128.amplitude_vs_level(plant_rows, "actual")
    fit["verdict"] = (
        "PASS"
        if (
            abs(fit["slope"] - P0_SLOPE) <= P0_SLOPE_TOL
            and abs(fit["weighted_r2"] - P0_WR2) <= P0_WR2_TOL
        )
        else "FAIL"
    )
    fit["bars"] = {
        "slope": [P0_SLOPE - P0_SLOPE_TOL, P0_SLOPE + P0_SLOPE_TOL],
        "weighted_r2": [P0_WR2 - P0_WR2_TOL, P0_WR2 + P0_WR2_TOL],
    }
    return {"fit": fit, "plant_rows": plant_rows, "per_plant": per_plant}


# ---------------------------------------------------------------------------
# OBS — step granularity against the amplitude D-1 actually gates on
# ---------------------------------------------------------------------------


def obs_step_vs_amplitude(census: dict, p0: dict) -> dict:
    """Compare the model's econ STEP WIDTH to the amplitude D-1 measures.

    Reported as an OBSERVATION only. The pre-registration kills this lane at P1
    and KILL-5 forbids manufacturing a successor, so this is written down for the
    next session exactly as miso-128 §6.4 wrote down this lane's object — NAMED,
    NOT CHARTERED.

    Both quantities are expressed in **MW**, not as fractions of a capacity
    basis: the measured amplitude is normalised by the bench nameplate while the
    LP step width is a share of the plant's assembled LP capacity, and those two
    denominators are not the same number. Comparing them in MW is
    denominator-free and is the only honest way to put them side by side.
    """
    per_plant = p0["per_plant"]
    by_code = {r["plant_code"]: r for r in census["rows"]}
    pairs: list[dict] = []
    for (year, code), meas in per_plant.items():
        row = by_code.get(code)
        if row is None or row["n_econ_tranches"] == 0:
            continue
        step_mw = row["econ_cap_mw"] / row["n_econ_tranches"]
        amp_mw = meas["std_frac"] * meas["npl"]
        if step_mw <= 0.0:
            continue
        pairs.append(
            {
                "year": year,
                "plant_code": code,
                "npl": meas["npl"],
                "lp_cap_mw": row["plant_cap_mw"],
                "measured_amplitude_mw": amp_mw,
                "measured_cf_off": meas["cf_off"],
                "econ_step_mw": step_mw,
                "amplitude_per_step": amp_mw / step_mw,
            }
        )
    if not pairs:
        return {"n": 0}
    w = np.array([p["npl"] for p in pairs], float)
    step = np.array([p["econ_step_mw"] for p in pairs], float)
    amp = np.array([p["measured_amplitude_mw"] for p in pairs], float)
    ratio = np.array([p["amplitude_per_step"] for p in pairs], float)
    order = np.argsort(ratio)
    cw = np.cumsum(w[order]) / w.sum()
    median_ratio = float(ratio[order][int(np.searchsorted(cw, 0.5))])
    return {
        "n": len(pairs),
        "capw_econ_step_mw": float(np.average(step, weights=w)),
        "capw_measured_amplitude_mw": float(np.average(amp, weights=w)),
        # Ratio of the cap-weighted aggregates (NOT the mean of per-plant
        # ratios, which Jensen-inflates on plants with tiny steps; both are
        # reported so neither can be quoted alone -- miso-127 gross/net duty).
        "ratio_of_capw_aggregates": float(
            np.average(amp, weights=w) / np.average(step, weights=w)
        ),
        "capw_mean_of_plant_ratios": float(np.average(ratio, weights=w)),
        "capw_median_of_plant_ratios": median_ratio,
        "share_amplitude_below_one_step": float(w[ratio < 1.0].sum() / w.sum()),
    }


# ---------------------------------------------------------------------------


def main() -> int:
    res: dict = {
        "session": "miso-129",
        "prereg": (
            "results/calibration/"
            "PREREG-miso129-coal-within-band-incremental-slope-2026-08-05.md"
        ),
        "keeper": M128.KEEPER_RUN,
        "years": list(YEARS),
        "grain2_year": GRAIN2_YEAR,
        "no_lp_solved": True,
    }

    g1 = grain1_config()
    res["P1_grain1_config"] = g1

    by_plant = assemble_coal(GRAIN2_YEAR)
    census = grain2_ladder_census(by_plant)
    res["P1_grain2_census"] = {k: v for k, v in census.items() if k != "rows"}
    res["P1_grain2_rows"] = census["rows"]

    laddered = census["cap_share_laddered_econ"]
    flat = census["cap_share_flat_econ"]
    if flat >= P1_HOLDS_FLAT_SHARE:
        verdict, premise = "PREMISE HOLDS", True
    elif laddered >= P1_FALSE_LADDER_SHARE:
        verdict, premise = "PREMISE FALSE — LANE DIES", False
    else:
        verdict, premise = "PREMISE PARTIAL", None
    res["P1_verdict"] = {
        "cap_share_flat_econ": flat,
        "cap_share_laddered_econ": laddered,
        "bars": {
            "holds_if_flat_share_ge": P1_HOLDS_FLAT_SHARE,
            "false_if_laddered_share_ge": P1_FALSE_LADDER_SHARE,
        },
        "premise_holds": premise,
        "verdict": verdict,
    }

    p0 = p0_actual_fit()
    res["P0_reproduction"] = p0["fit"]
    res["OBS_step_vs_amplitude"] = obs_step_vs_amplitude(census, p0)

    res["derive_ran"] = False
    res["arms_solved"] = 0
    res["runs_registered"] = 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, default=str))

    v = res["P1_verdict"]
    print("=" * 72)
    print("miso-129 P1 — PREMISE: 'the coal offer band has no within-band slope'")
    print("=" * 72)
    print(f"  offer_curve_smoothing_n      : {g1['offer_curve_smoothing_n']}")
    print(f"  offer_curve_smoothing_exp    : {g1['offer_curve_smoothing_exp']}")
    print(
        f"  COAL_PRB curve               : {g1['offer_curve_by_group_coal'].get('COAL_PRB')}"
    )
    print(f"  coal plants assembled        : {census['n_plants']}")
    print(f"  total coal cap (MW)          : {census['total_coal_cap_mw']:,.1f}")
    print(f"  cap share ONE econ price     : {flat:.4f}")
    print(f"  cap share LADDERED econ      : {laddered:.4f}")
    print(f"  VERDICT                      : {v['verdict']}")
    print()
    f = res["P0_reproduction"]
    print(
        f"  P0 actual-side fit: slope {f['slope']:+.4f} (bar {P0_SLOPE:+.4f}"
        f"+-{P0_SLOPE_TOL}), wR2 {f['weighted_r2']:.3f}, n {f['n']} -> {f['verdict']}"
    )
    o = res["OBS_step_vs_amplitude"]
    if o.get("n"):
        print()
        print("  OBS (named, NOT chartered):")
        print(f"    cap-wtd econ step width      : {o['capw_econ_step_mw']:.1f} MW")
        print(
            f"    cap-wtd measured amplitude   : {o['capw_measured_amplitude_mw']:.1f} MW"
        )
        print(f"    ratio of cap-wtd aggregates  : {o['ratio_of_capw_aggregates']:.3f}")
        print(
            f"    cap-wtd MEDIAN plant ratio   : {o['capw_median_of_plant_ratios']:.3f}"
        )
        print(
            f"    cap-wtd MEAN plant ratio     : {o['capw_mean_of_plant_ratios']:.3f}"
        )
        print(
            f"    cap share amplitude < 1 step : "
            f"{o['share_amplitude_below_one_step']:.4f}"
        )
    print()
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
