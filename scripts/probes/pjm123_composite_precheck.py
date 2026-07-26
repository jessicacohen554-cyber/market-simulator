"""pjm-123 no-LP pre-check: does the three-leg dispersion composite move bids the way it must?

The pjm-122 finding (`docs/FINDING-pjm122-marginal-ownership-2026-07.md` §4)
proposes a measured re-ownership of the $40-150 region in three legs, each
using the construction its refuted predecessor taught:

  1. COAL econ -> LEVEL form  (``pjm_offer_midcurve_level_segments=("LONG_RUN",)``)
  2. CC PEAK rows -> measured belt (``pjm_offer_midcurve_peak_segments=("CC_LIKE",)``)
  3. CT_FAST -> max()-seam reprice (``pjm_ct_measured_max_reprice``)

Following the pjm-121 §5 pattern, the composite is BUILT AND TESTED BEFORE A
SOLVE IS SPENT: this probe calls the real builders on the real fleet and offer
arrays reconstructed from the keeper bundle's own meta.json (``fleet_only``, no
LP), assembles the full P1 bid the LP would clear on, and diffs each arm
against the keeper.

PRE-REGISTERED KILL CRITERIA (written before the probe was first run; the
composite is REFUTED if any fails, and no solve is spent):

  K1 DISPERSION SIGN. The MW-weighted bid must FALL in the low net-load bins
     (bin0/bin1) AND RISE in bin3. A same-sign level shift either way — down
     everywhere (the pjm-121 §5 level-form signature) or up everywhere (the
     pjm-121 keeper's own level lift) — kills the composite: the C3a-2025
     residual is a monotone dispersion COMPRESSION and only a mechanism that
     widens it can close the tight strata without re-inflating the 6,771 cheap
     hours already $4-10/MWh too high (pjm-120).

  K2 SPREAD. The CC econ offer spread (p90-p10 across rows, per net-load bin)
     must NOT narrow in any bin versus the keeper. Narrowing is the exact
     refutation signature of the pjm-121 §5 arm.

  K3 CT STRICTNESS. Leg 3 must be a strict max() against the FULL P1 bid. Any
     row-hour where the composite bid exceeds ``max(bid_without_leg3, target)``
     — i.e. the measured level ADDING on top of the pjm-103 startup
     amortization rather than reconciling with it — kills that leg (rule 19;
     the additive form is the pjm-101/102 failure, CT -12 TWh).

WHAT THE STARTUP MARKUP DOES AND DOESN'T KNOW. The P1 bid is ``mc_base +
startup_markup + mc_bid_adjust``, and the startup markup is amortized over the
P0 run lengths — which only an LP produces. Rather than guess it, this probe
BRACKETS it with the real :func:`compute_monthly_markup` evaluated at the two
endpoints of its own construction:

  * ``lo`` — a synthetic all-idle P0: every fast-start row amortizes over its
    full CAMPD-measured run-length ceiling (the v3/v4 no-P0-run branch), the
    SMALLEST markup the model can produce, so the leg-3 max() has the MOST
    room to bind. This is the composite's best case.
  * ``hi`` — a synthetic every-run-is-one-hour P0: every row amortizes over a
    single hour, the LARGEST markup, so leg 3 has the LEAST room to bind. This
    is the composite's worst case.

The truth is between them, so a criterion is only reported as PASSED when it
holds at BOTH endpoints, and as FAILED when it fails at both; a split verdict
is reported as INDETERMINATE and escalates to the owner rather than silently
buying a solve.

Pure diagnostic, no LP. Usage:

    python scripts/probes/pjm123_composite_precheck.py \
        results/calibration/pjm121_ccbelt --year 2025 \
        --json-out results/calibration/pjm123_precheck_2025.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# REPO itself must be on the path so ``scripts.lib.clean_io`` resolves as a
# package — without it the data/clean readers silently fall back and the
# measured overlays (east interface cut, ramp capability) refuse to load.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

#: The composite's arms. Each is (level_segments, peak_segments, ct_leg).
ARMS: dict[str, tuple[tuple[str, ...], tuple[str, ...], bool]] = {
    "A_keeper": ((), (), False),
    "L1_coal_level": (("LONG_RUN",), (), False),
    "L2_cc_peak_belt": ((), ("CC_LIKE",), False),
    "L3_ct_max": ((), (), True),
    "COMPOSITE": (("LONG_RUN",), ("CC_LIKE",), True),
}

def full_run_year_kwargs(meta: dict) -> dict:
    """Rebuild the bundle's fleet from EVERY flag its meta.json records.

    Thin delegation to the shared
    :func:`scripts.lib.bundle_fleet.full_run_year_kwargs` — this probe is where
    the widened reconstruction was first written; pjm-124 promoted it to
    ``scripts/lib`` (frontier handoff §5) so every no-LP pre-check measures the
    same fleet. Kept as a name here so this probe's calibration record still
    runs unchanged.

    Args:
        meta: The bundle's ``meta.json``.

    Returns:
        The ``run_year`` kwargs, ``fleet_only=True``.
    """
    from scripts.lib.bundle_fleet import full_run_year_kwargs as _shared

    return _shared(meta)


def _startup_markup_bracket(state, config, net_load):
    """Return ``{"lo": markup, "hi": markup}`` bracketing the P1 startup markup.

    Both endpoints come from the REAL :func:`compute_monthly_markup` — only the
    synthetic P0 dispatch handed to it differs (see the module docstring). The
    v4 condition-keyed horizon ratio is rebuilt exactly as
    ``run_calibration.run_year`` builds it, so the ceiling the ``lo`` endpoint
    amortizes over is the same one the solve would use.
    """
    from market_sim.model.commitment import compute_monthly_markup

    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], dtype=float)
    n_gen, hours = mc.shape

    # v4 condition-keyed amortization-horizon ratio (the run_calibration block).
    run_ratio_t = None
    if getattr(config, "tranche_startup_conditional_runs", False):
        from market_sim.data.fleet import campd_ct_run_band_ratios

        bands = campd_ct_run_band_ratios(getattr(config, "iso", "PJM"))
        if bands is not None:
            edges, ratios = bands
            pct = (np.argsort(np.argsort(net_load)) + 1.0) / float(net_load.shape[0])
            idx = np.searchsorted(np.asarray(edges, dtype=float), pct, side="right")
            run_ratio_t = np.asarray(ratios, dtype=float)[idx]

    kw = dict(
        gas_st_season_spread=getattr(config, "gas_st_startup_spread", False),
        gas_st_startup_cost=getattr(config, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(config, "chp_startup_covered", False),
        coal_warm_committed=getattr(config, "coal_warm_committed", False),
        run_ratio_t=run_ratio_t,
    )
    idle = np.zeros((n_gen, hours))  # no P0 runs -> full measured ceiling
    # Alternating on/off at full Pmax -> every run is exactly one hour.
    flicker = np.zeros((n_gen, hours))
    flicker[:, ::2] = fa.pmax[:, None]
    return {
        "lo": compute_monthly_markup(fleet, fa, idle, hours, **kw),
        "hi": compute_monthly_markup(fleet, fa, flicker, hours, **kw),
    }


def _arm_bid(state, config, net_load, year, base_markup, level, peak, ct_leg):
    """Assemble one arm's full P1 bid.

    Returns ``(bid, bid_before_leg3, ct_target, n_midcurve_rows_priced)`` — the
    pre-leg-3 bid and the target are what K3 checks the max() seam against, and
    the priced-row count is the engagement guard.
    """
    from market_sim.data.fleet import (
        build_pjm_ct_measured_max_target,
        build_pjm_offer_midcurve_conditional_markup,
    )
    from market_sim.pipeline.solve import apply_bid_max_target

    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], dtype=float)
    cfg = config.with_overrides(
        pjm_offer_midcurve_level_segments=list(level) or None,
        pjm_offer_midcurve_peak_segments=list(peak) or None,
        pjm_ct_measured_max_reprice=bool(ct_leg),
    )
    midcurve = build_pjm_offer_midcurve_conditional_markup(
        fa, fleet, mc, net_load, cfg, year
    )
    bid = mc + base_markup + (0.0 if midcurve is None else midcurve)
    n_priced = 0 if midcurve is None else int((midcurve != 0.0).any(axis=1).sum())
    target = build_pjm_ct_measured_max_target(fa, fleet, mc, net_load, cfg, year)
    pre_ct = bid.copy()
    if target is not None:
        bid = apply_bid_max_target(bid, target)
    return bid, pre_ct, target, n_priced


def _bin_edges(net_load, hours):
    """The mechanism's own net-load conditioning bins (80/90/97th pct)."""
    q = np.quantile(net_load[:hours], [0.80, 0.90, 0.97])
    return np.searchsorted(q, net_load[:hours], side="right")


def _mw_weighted_by_bin(delta, caps, hour_bin):
    """MW-weighted mean bid delta per net-load bin, ``$/MWh``."""
    if caps.sum() <= 0:
        return {f"bin{b}": float("nan") for b in range(4)}
    w = caps[:, None] / caps.sum()
    out = {}
    for b in range(4):
        sel = hour_bin == b
        out[f"bin{b}"] = (
            float((delta[:, sel] * w).sum() / sel.sum()) if sel.any() else float("nan")
        )
    return out


def _spread_by_bin(bid, hour_bin):
    """p90-p10 of the offer stack across rows, per net-load bin."""
    out = {}
    for b in range(4):
        sel = hour_bin == b
        if not sel.any() or bid.shape[0] == 0:
            out[f"bin{b}"] = float("nan")
            continue
        v = bid[:, sel]
        out[f"bin{b}"] = float(np.quantile(v, 0.9) - np.quantile(v, 0.1))
    return out


def _verdict(lo_ok: bool, hi_ok: bool) -> str:
    """Collapse the two markup endpoints into one reported verdict."""
    if lo_ok and hi_ok:
        return "PASS"
    if not lo_ok and not hi_ok:
        return "FAIL"
    return "INDETERMINATE"


def main() -> int:
    """Build every arm on one fleet, evaluate K1-K3, print and persist."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    from run_calibration import run_year

    meta = json.loads((args.bundle / "meta.json").read_text())
    year, hours = args.year, int(meta["hours"])
    # A year-chain bundle's merged meta records ``gas_prices`` for the LAST
    # invocation only, so an earlier year falls back to the same Henry Hub
    # actual ``run_calibration_full`` itself resolves for that year — the
    # value the chain solved on, not a guess.
    gas_price = (meta.get("gas_prices") or {}).get(str(year))
    if gas_price is None:
        import run_calibration_full as rcf

        gas_price = rcf._henry_hub_actual(rcf._load_reference(), year)
        print(f"  meta carries no {year} gas price; Henry Hub actual {gas_price}")
    print(f"reconstructing {meta['iso']} {year} fleet from {args.bundle} (no LP) ...")
    state = run_year(
        year,
        meta["iso"],
        hours,
        float(gas_price),
        **full_run_year_kwargs(meta),
    )
    fleet, fa = state["fleet"], state["fleet_arrays"]
    config = state["config"]
    # Fidelity guard: a silent reconstruction drift must be a hard error, not a
    # quiet null result that makes every arm's delta meaningless. Both the
    # mid-curve seam (the keeper arm IS the floored surface) and the pjm-103
    # start-cost pricing (the term leg 3 reconciles with) must have survived.
    for field in (
        "pjm_offer_midcurve_conditional",
        "tranche_startup_amortization",
        "tranche_startup_measured_runs",
        "tranche_startup_conditional_runs",
    ):
        if bool(meta.get(field, False)) and not bool(getattr(config, field, False)):
            raise SystemExit(
                f"reconstruction dropped {field} (bundle records it ON) — the "
                "keeper arm would not be the keeper"
            )
    if list(getattr(config, "pjm_offer_midcurve_segments", None) or ()) != list(
        meta.get("pjm_offer_midcurve_segments") or ()
    ):
        raise SystemExit(
            "reconstructed mid-curve scope "
            f"{getattr(config, 'pjm_offer_midcurve_segments', None)!r} != the bundle's "
            f"{meta.get('pjm_offer_midcurve_segments')!r} — the keeper arm would not "
            "be the keeper"
        )
    mc = np.asarray(state["mc_base"], dtype=float)
    # Same LP-served net-load convention as the builders' call site
    # (run_calibration.py::run_year) so the hour->bin mapping is identical.
    net_load = (
        state["demand"].sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )
    hour_bin = _bin_edges(net_load, mc.shape[1])

    groups = np.array([getattr(g, "plant_group", None) or "" for g in fleet])
    sfx = np.array([g.unit_id.rpartition("_")[2] for g in fleet])
    econ = np.char.startswith(sfx.astype(str), "econ")
    peak = np.char.startswith(sfx.astype(str), "peak")
    # The whole re-ownable merit region: every row any leg can touch.
    touched = ((econ | peak) & np.isin(groups, ["CC_REGULAR", "CT_PEAKER"])) | (
        (econ | (sfx == "peak"))
        & np.isin(groups, ["COAL", "COAL_BIT", "COAL_PRB", "ST_GAS"])
    )
    cc_econ = econ & (groups == "CC_REGULAR")
    print(
        f"rows: {int(touched.sum())} touchable ({fa.pmax[touched].sum() / 1e3:.2f} GW), "
        f"{int(cc_econ.sum())} CC econ ({fa.pmax[cc_econ].sum() / 1e3:.2f} GW)"
    )

    markups = _startup_markup_bracket(state, config, net_load)
    if np.array_equal(markups["lo"], markups["hi"]):
        raise SystemExit(
            "the startup-markup bracket COLLAPSED (lo == hi) — no fast-start row "
            "carries a measured run-length horizon, so the reconstruction is not "
            "carrying the pjm-103 amortization and leg 3 would be tested against "
            "a CT stack that is missing its own pricing mechanism"
        )
    report: dict = {
        "bundle": str(args.bundle),
        "year": year,
        "rows_touchable": int(touched.sum()),
        "gw_touchable": float(fa.pmax[touched].sum() / 1e3),
        "endpoints": {},
    }

    for end, base_markup in markups.items():
        bids, pre_cts, targets, priced = {}, {}, {}, {}
        for name, (level, pk, ct) in ARMS.items():
            bids[name], pre_cts[name], targets[name], priced[name] = _arm_bid(
                state, config, net_load, year, base_markup, level, pk, ct
            )
        if priced["A_keeper"] == 0:
            raise SystemExit(
                "the keeper arm priced ZERO mid-curve rows — the surface is not "
                "engaged and every delta below would be meaningless"
            )
        keeper = bids["A_keeper"]
        ent: dict = {"arms": {}}
        for name in ARMS:
            d = bids[name] - keeper
            ent["arms"][name] = {
                "mw_wtd_delta_touched": _mw_weighted_by_bin(
                    d[touched], fa.pmax[touched], hour_bin
                ),
                "mw_wtd_delta_cc_econ": _mw_weighted_by_bin(
                    d[cc_econ], fa.pmax[cc_econ], hour_bin
                ),
                "cc_econ_spread": _spread_by_bin(bids[name][cc_econ], hour_bin),
                "midcurve_rows_priced": priced[name],
                "ct_rows_targeted": (
                    0
                    if targets[name] is None
                    else int((targets[name] > 0).any(axis=1).sum())
                ),
            }

        comp = ent["arms"]["COMPOSITE"]["mw_wtd_delta_touched"]
        base_spread = ent["arms"]["A_keeper"]["cc_econ_spread"]
        comp_spread = ent["arms"]["COMPOSITE"]["cc_econ_spread"]
        # K3: the composite bid may never exceed max(pre-leg-3 bid, target).
        tgt = targets["COMPOSITE"]
        if tgt is None:
            add_rows = -1  # leg 3 built nothing — reported, not silently passed
        else:
            expected = np.where(
                tgt > 0.0, np.maximum(pre_cts["COMPOSITE"], tgt), pre_cts["COMPOSITE"]
            )
            add_rows = int((~np.isclose(bids["COMPOSITE"], expected)).sum())
        ent["criteria"] = {
            "K1_falls_low_bins": bool(comp["bin0"] < 0.0 and comp["bin1"] < 0.0),
            "K1_rises_bin3": bool(comp["bin3"] > 0.0),
            # Restatement of K1 as a single weighting-robust number: a
            # dispersion mechanism must move the TIGHT bin further up than the
            # slack bin, whatever the absolute level does. Unlike the two
            # sign tests it does not depend on where the arms' common level
            # shift happens to sit, nor on how much idle capacity the
            # MW-weighting picks up. Must be > 0.
            "K1_gradient_bin3_minus_bin0": float(comp["bin3"] - comp["bin0"]),
            "K1_gradient_positive": bool(comp["bin3"] - comp["bin0"] > 0.0),
            "K2_spread_not_narrowed": bool(
                all(
                    comp_spread[f"bin{b}"] >= base_spread[f"bin{b}"] - 1e-9
                    for b in range(4)
                )
            ),
            "K3_ct_strict_max": bool(add_rows == 0),
            "K3_additive_row_hours": add_rows,
        }
        report["endpoints"][end] = ent

    lo, hi = (
        report["endpoints"]["lo"]["criteria"],
        report["endpoints"]["hi"]["criteria"],
    )
    report["verdict"] = {
        k: _verdict(bool(lo[k]), bool(hi[k]))
        for k in (
            "K1_falls_low_bins",
            "K1_rises_bin3",
            "K1_gradient_positive",
            "K2_spread_not_narrowed",
            "K3_ct_strict_max",
        )
    }
    report["k1_gradient"] = {
        end: report["endpoints"][end]["criteria"]["K1_gradient_bin3_minus_bin0"]
        for end in ("lo", "hi")
    }
    report["composite_survives"] = all(v == "PASS" for v in report["verdict"].values())

    for end in ("lo", "hi"):
        ent = report["endpoints"][end]
        print(f"\n=== startup-markup endpoint '{end}' ===")
        print(f"    {'arm':<18}{'bin0':>9}{'bin1':>9}{'bin2':>9}{'bin3':>9}")
        for name in ARMS:
            row = ent["arms"][name]["mw_wtd_delta_touched"]
            print(
                f"    {name:<18}"
                + "".join(f"{row[f'bin{b}']:>9.3f}" for b in range(4))
                + "   MW-wtd bid delta vs keeper ($/MWh), touchable rows"
            )
        print(
            f"\n    {'cc econ spread':<18}{'bin0':>9}{'bin1':>9}{'bin2':>9}{'bin3':>9}"
        )
        for name in ("A_keeper", "COMPOSITE"):
            s = ent["arms"][name]["cc_econ_spread"]
            print(
                f"    {name:<18}" + "".join(f"{s[f'bin{b}']:>9.2f}" for b in range(4))
            )
        print(f"    criteria: {ent['criteria']}")

    print("\n=== VERDICT (must hold at BOTH endpoints) ===")
    for k, v in report["verdict"].items():
        print(f"    {k:<30} {v}")
    g = report["k1_gradient"]
    print(
        f"    {'K1 gradient bin3-bin0 ($/MWh)':<30} lo {g['lo']:+.3f}  hi {g['hi']:+.3f}"
        "   (must be > 0)"
    )
    print(
        f"    composite survives the pre-check: "
        f"{'YES — the A/B solve is justified' if report['composite_survives'] else 'NO — refuted, no solve spent'}"
    )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
