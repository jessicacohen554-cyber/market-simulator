"""Derive the ERCOT ORDC scarcity-price overlay for a solved bundle.

Post-solve only: reads a persisted calibration bundle (dispatch + system
parquets), reconstructs the hourly fleet availability the LP solved
against (same config, same outage overlay — no LP is re-solved), computes
the hourly netted reserve headroom and applies ERCOT's published ORDC
adder formula (market_sim.results.scarcity). Volumes, dispatch parquets
and emissions are untouched; the overlay is written as a separate
``scarcity.parquet`` series next to the energy-only LMP.

Steps:
  1. ``availability.parquet`` — hourly system thermal available MW,
     thermal dispatch MW and storage power cap, cached in the bundle
     (rebuilt with ``--rebuild-availability``).
  2. ``scarcity.parquet`` (or ``scarcity_<tag>.parquet``) — per
     (year, hour): reserves_mw, lolp, scarcity_adder, lmp, lmp_scarcity.
  3. A stdout report: adder incidence per year, LMP MAE vs the actual RT
     series with and without the adder, tail-hour counts, and (with
     ``--revenue-report``) per-class energy revenue with/without the
     adder.

The diagnostic that motivates the overlay (is the model thin when reality
was thin?) is printed with ``--diagnostic``.

Usage:
    python scripts/data/derive_ordc_overlay.py results/calibration/run92_kiamichi
        [--years 2023 2024 2025] [--voll 5000] [--mcl 3000]
        [--sigma 1400] [--mu 0] [--shift 0.5] [--as-plan 8100]
        [--no-floor] [--lolp-params CSV] [--tag voll9000]
        [--diagnostic] [--revenue-report] [--rebuild-availability]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    RESERVE_FUEL_TYPES,
    effective_reliability_deployment_mw,
    reserve_headroom,
    scarcity_prices,
)

# Validation-source dir (actual_lmp_hourly_ERCOT.parquet). W1 relocated the old
# inputs/calibration tree to data/raw/_validation-source (paths.CALIBRATION_DIR);
# the stale inputs/ path silently produced an empty actual RT series.
CAL_DIR = REPO / "data" / "raw" / "_validation-source"

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])


def _month_of_hour(hours: np.ndarray) -> np.ndarray:
    """Map non-leap hour-of-year indices to months 1-12."""
    return np.searchsorted(_MONTH_START_HOUR, hours, side="right").clip(1, 12)


def _run_year_kwargs(meta: dict, year: int) -> dict:
    """Mirror solve_and_persist's run_year call from a bundle's meta.json."""
    return dict(
        ttc_overrides={},
        commitment_enabled=False,  # availability is pass-independent
        commitment_screen_coal=meta.get("commitment_screen_coal", True),
        coal_lignite_mustrun=meta.get("coal_lignite_mustrun"),
        coal_prb_mustrun=meta.get("coal_prb_mustrun"),
        coal_prb_passthrough=meta.get("coal_prb_passthrough", 1.0),
        outage_source=meta.get("outage_source", "historic"),
        coal_prb_passthrough_sigmoid=meta.get("coal_prb_passthrough_sigmoid", False),
        coal_mustrun_per_plant=meta.get("coal_mustrun_per_plant", False),
        coal_drop_pof=meta.get("coal_drop_pof", False),
        coal_prb_passthrough_tiered=meta.get("coal_prb_passthrough_tiered", False),
        prb_overrides=meta.get("coal_prb_sigmoid_overrides") or None,
        coal_bit_sigmoid=meta.get("coal_bit_passthrough_sigmoid", False),
        bit_overrides=meta.get("coal_bit_sigmoid_overrides") or None,
        storage_daily_cycling=meta.get("storage_daily_cycling", False),
        battery_dispatch_adder=meta.get("battery_dispatch_adder", 0.0),
        gas_offer_curve=meta.get("gas_offer_curve", False),
        gas_monthly_actuals=meta.get("gas_monthly_actuals", False),
        offer_curve_overrides=meta.get("offer_curve_overrides") or None,
        offer_curve_deltas=meta.get("offer_curve_deltas") or None,
        curve_smoothing=meta.get("curve_smoothing") or None,
        cc_derate_from_top=meta.get("cc_derate_from_top", False),
        priced_interchange=meta.get("priced_interchange", False),
        hydro_backfill_year=meta.get("hydro_backfill_year"),
        fleet_only=True,
    )


def build_availability(
    bundle: Path, years: list[int], meta: dict, force: bool = False
) -> pd.DataFrame:
    """Reconstruct (or load) hourly system availability for the bundle.

    Returns a frame with columns ``year``, ``hour``, ``thermal_avail_mw``
    (sum of pmax x availability over reserve-providing thermal units),
    ``thermal_dispatch_mw`` (the same units' solved P1 dispatch),
    ``renewable_avail_mw`` / ``renewable_dispatch_mw`` (wind + solar
    potential cf x cap and their solved dispatch — curtailed renewable
    headroom counts toward reserves, mirroring ERCOT's HSL-minus-output
    convention for intermittent resources) and ``storage_power_cap_mw``.
    Cached as ``availability.parquet`` in the bundle; the rebuild loads
    the fleet through the exact configuration recorded in meta.json (no
    LP solve).
    """
    out_path = bundle / "availability.parquet"
    _required = {"thermal_online_mw", "thermal_offline_mw"}
    if out_path.exists() and not force:
        cached = pd.read_parquet(out_path)
        if set(cached["year"].unique()) >= set(years) and _required.issubset(
            cached.columns
        ):
            return cached

    from run_calibration import run_year  # late import: heavy module

    frames = []
    for year in years:
        state = run_year(
            year,
            meta["iso"],
            meta["hours"],
            meta["gas_prices"][str(year)],
            **_run_year_kwargs(meta, year),
        )
        fa = state["fleet_arrays"]
        fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
        thermal = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
        avail = (fa.pmax[thermal, None] * fa.availability[thermal]).sum(axis=0)
        thermal_units = set(np.asarray(fa.unit_ids, dtype=object)[thermal])

        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
        disp_t = (
            disp[disp["unit_id"].astype(str).isin(thermal_units)]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(meta["hours"]), fill_value=0.0)
            .to_numpy()
        )

        # Online/offline reserve split (results.scarcity): a cold slow-start
        # unit does not back reserve. Rebuild the per-unit (n_gen, T) dispatch
        # matrix aligned to the reconstructed fleet, then take the thermal-only
        # split (zero storage / no AS here — storage, renewable headroom and
        # the AS plan are layered on in main, where they are available).
        dm = (
            disp.pivot_table(
                index="unit_id",
                columns="hour",
                values="mw",
                aggfunc="sum",
                fill_value=0.0,
            )
            .reindex(
                index=[str(u) for u in fa.unit_ids],
                columns=range(meta["hours"]),
                fill_value=0.0,
            )
            .to_numpy()
        )
        r_on_th, r_off_th = reserve_headroom(
            fa, dm, np.zeros(0), None, None, as_plan_mw=0.0
        )

        # Renewable potential (cf x cap summed over zones) and dispatch:
        # the difference is curtailed headroom, which ERCOT's reserve
        # telemetry counts (HSL - output) — it suppresses spurious
        # scarcity in curtailment hours and is ~0 in real scarcity hours,
        # when renewables run at their full potential.
        ren_avail = np.zeros(meta["hours"])
        for cf, cap2 in (
            (state["wind_cf"], state["wind_cap"]),
            (state["solar_cf"], state["solar_cap"]),
        ):
            cf = np.asarray(cf, dtype=float)
            cap2 = np.asarray(cap2, dtype=float)
            ren_avail += (cf * cap2[:, None]).sum(axis=0)
        ren_disp = (
            disp[disp["klass"].isin(["wind", "solar"])]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(meta["hours"]), fill_value=0.0)
            .to_numpy()
        )

        cap = np.asarray(state["storage_power_cap"], dtype=float)
        cap_t = cap.sum(axis=0) if cap.ndim == 2 else np.full(meta["hours"], cap.sum())

        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(meta["hours"], dtype=np.int32),
                    "thermal_avail_mw": avail.astype(np.float32),
                    "thermal_dispatch_mw": disp_t.astype(np.float32),
                    "thermal_online_mw": r_on_th.astype(np.float32),
                    "thermal_offline_mw": r_off_th.astype(np.float32),
                    "renewable_avail_mw": ren_avail.astype(np.float32),
                    "renewable_dispatch_mw": ren_disp.astype(np.float32),
                    "storage_power_cap_mw": cap_t.astype(np.float32),
                }
            )
        )
        print(
            f"  {year}: thermal avail mean "
            f"{avail.mean():,.0f} MW, dispatch mean {disp_t.mean():,.0f} "
            f"MW, renewable headroom mean "
            f"{(ren_avail - ren_disp).mean():,.0f} MW, storage cap mean "
            f"{cap_t.mean():,.0f} MW"
        )
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(out_path, index=False)
    print(f"wrote {out_path}")
    return df


def _system_lambda(bundle: Path, year: int, hours: int) -> np.ndarray:
    """Demand-weighted hourly system price (P1) — the model system lambda."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    g = (
        sy.assign(pd_=sy["price"] * sy["demand"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean"))
    )
    lam = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    out = np.full(hours, np.nan)
    out[g.index.to_numpy()] = lam
    return out


def _storage_headroom(
    bundle: Path, year: int, hours: int, cap_t: np.ndarray
) -> np.ndarray:
    """Storage headroom: power cap - discharge + charge (ESR convention)."""
    p = bundle / "storage.parquet"
    if not p.exists():
        return cap_t
    st = pd.read_parquet(p)
    st = st[st["year"] == year]
    if "pass" in st.columns and (st["pass"] == "P1").any():
        st = st[st["pass"] == "P1"]
    g = (
        st.groupby("hour")[["charge_mw", "discharge_mw"]]
        .sum()
        .reindex(range(hours), fill_value=0.0)
    )
    return cap_t - g["discharge_mw"].to_numpy() + g["charge_mw"].to_numpy()


def _actual_rt(year: int, hours: int) -> np.ndarray:
    """Actual hub-mean hourly RT price for ERCOT, NaN-padded."""
    p = CAL_DIR / "actual_lmp_hourly_ERCOT.parquet"
    if not p.exists():
        return np.full(hours, np.nan)
    act = pd.read_parquet(p)
    act = act[act["year"] == year]
    out = np.full(hours, np.nan)
    out[act["hour"].to_numpy()] = act["rt"].to_numpy()
    return out


def _mae(
    model: np.ndarray, actual: np.ndarray, weights: np.ndarray | None = None
) -> float:
    """Weighted mean absolute error, NaNs dropped."""
    ok = np.isfinite(model) & np.isfinite(actual)
    if weights is None:
        weights = np.ones_like(model)
    w = weights[ok]
    return float(np.sum(np.abs(model[ok] - actual[ok]) * w) / w.sum())


def _monthly_mae(model: np.ndarray, rt: np.ndarray, demand: np.ndarray) -> float:
    """The LMP gate metric: monthly LMP MAE, demand-weighted.

    Per month, demand-weighted model mean vs plain actual-RT mean; the
    twelve |residuals| averaged with monthly demand weights — matches the
    calibration log's headline (e.g. run92_kiamichi 32.1 / 7.3 / 2.2).
    """
    mon = _month_of_hour(np.arange(len(model)))
    diffs, weights = [], []
    for m in range(1, 13):
        sel = (mon == m) & np.isfinite(rt) & np.isfinite(model)
        if not sel.any():
            continue
        mm = float(np.average(model[sel], weights=demand[sel]))
        diffs.append(abs(mm - float(np.nanmean(rt[sel]))))
        weights.append(float(demand[sel].sum()))
    return float(np.average(diffs, weights=weights)) if diffs else np.nan


def _demand_weights(bundle: Path, year: int, hours: int) -> np.ndarray:
    """Hourly total demand, the weight series for demand-weighted MAE."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    g = sy.groupby("hour")["demand"].sum().reindex(range(hours))
    return g.to_numpy()


def diagnostic(avail: pd.DataFrame, bundle: Path, years: list[int], hours: int) -> None:
    """Print residual-vs-headroom localization (pre-adder sanity gate).

    If the model is NOT thin in the hours reality was thin, the LMP gap is
    an availability/load-shape problem and the overlay must not be used to
    paper over it.
    """
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        headroom = (
            a["thermal_avail_mw"].to_numpy(float)
            - a["thermal_dispatch_mw"].to_numpy(float)
            + _storage_headroom(bundle, year, hours, cap_t)
        )
        lam = _system_lambda(bundle, year, hours)
        rt = _actual_rt(year, hours)
        resid = rt - lam
        ok = np.isfinite(resid)
        bins = [-np.inf, 4e3, 6e3, 8e3, 10e3, 12e3, 15e3, 20e3, np.inf]
        labels = ["<4G", "4-6G", "6-8G", "8-10G", "10-12G", "12-15G", "15-20G", ">20G"]
        df = pd.DataFrame(
            {
                "bin": pd.cut(headroom[ok], bins, labels=labels),
                "resid": resid[ok],
                "rt": rt[ok],
            }
        )
        tbl = df.groupby("bin", observed=True).agg(
            hours=("resid", "size"),
            resid_mean=("resid", "mean"),
            rt_mean=("rt", "mean"),
        )
        print(
            f"\n=== {year} actual-minus-model residual by model "
            f"headroom (pre-AS-netting) ==="
        )
        print(tbl.round(1).to_string())
        tail_sel = df["rt"].to_numpy() >= 200
        if tail_sel.any():
            print(
                f"actual >=$200 hours: {int(tail_sel.sum())}; their "
                f"headroom p25/p50/p75 = "
                f"{np.percentile(headroom[ok][tail_sel], [25, 50, 75]).round(0)}"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--voll", type=float, default=None, help="override ordc_voll ($/MWh)"
    )
    ap.add_argument("--mcl", type=float, default=None, help="override ordc_mcl_mw (MW)")
    ap.add_argument(
        "--sigma", type=float, default=None, help="override ordc_lolp_sigma_mw (MW)"
    )
    ap.add_argument(
        "--mu", type=float, default=None, help="override ordc_lolp_mu_mw (MW)"
    )
    ap.add_argument(
        "--shift", type=float, default=None, help="override ordc_lolp_shift_sigma"
    )
    ap.add_argument(
        "--as-plan", type=float, default=None, help="override ordc_as_plan_mw (MW)"
    )
    ap.add_argument(
        "--no-floor", action="store_true", help="disable the OBDRR048 multi-step floor"
    )
    ap.add_argument(
        "--lolp-params",
        type=Path,
        default=None,
        help="seasonal/TOD-block mu/sigma CSV (NP6-576-ER)",
    )
    ap.add_argument(
        "--tag", default=None, help="write scarcity_<tag>.parquet (scenario runs)"
    )
    ap.add_argument(
        "--diagnostic",
        action="store_true",
        help="print the residual-vs-headroom localization only",
    )
    ap.add_argument(
        "--revenue-report",
        action="store_true",
        help="per-class energy revenue with/without the adder",
    )
    ap.add_argument("--rebuild-availability", action="store_true")
    args = ap.parse_args()

    bundle = args.bundle.resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    if meta["iso"] != "ERCOT":
        raise SystemExit("ORDC scarcity overlay is ERCOT-only")
    years = args.years or meta["years"]
    hours = meta["hours"]

    overrides = {"scarcity_pricing_enabled": True, "mode": "backcast", "iso": "ERCOT"}
    if args.voll is not None:
        overrides["ordc_voll"] = args.voll
    if args.mcl is not None:
        overrides["ordc_mcl_mw"] = args.mcl
    if args.sigma is not None:
        overrides["ordc_lolp_sigma_mw"] = args.sigma
    if args.mu is not None:
        overrides["ordc_lolp_mu_mw"] = args.mu
    if args.shift is not None:
        overrides["ordc_lolp_shift_sigma"] = args.shift
    if args.as_plan is not None:
        overrides["ordc_as_plan_mw"] = args.as_plan
    if args.no_floor:
        overrides["ordc_multistep_floor"] = False
    if args.lolp_params is not None:
        overrides["ordc_lolp_params_path"] = str(args.lolp_params)
    config = ScenarioConfig(**overrides)

    print(f"bundle {bundle.name}: years {years}")
    avail = build_availability(bundle, years, meta, force=args.rebuild_availability)

    if args.diagnostic:
        diagnostic(avail, bundle, years, hours)
        return

    frames = []
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        ren_headroom = a["renewable_avail_mw"].to_numpy(float) - a[
            "renewable_dispatch_mw"
        ].to_numpy(float)
        # Online/offline reserve split — the grounded mechanism (mirrors
        # runner.run_scenario_iso). Online tier = spinning thermal headroom +
        # curtailed-renewable + storage; offline tier = quick-start non-spin
        # headroom (cold slow-start excluded). The AS plan is NOT netted —
        # ERCOT's RTOLCAP already counts online AS-held capacity as reserve, so
        # subtracting it double-counts (confirmed: it overshoots ~6x). The
        # legacy fitted offset only subtracts when explicitly set (default 0).
        r_offline = a["thermal_offline_mw"].to_numpy(float)
        r_online = (
            a["thermal_online_mw"].to_numpy(float)
            + ren_headroom
            + _storage_headroom(bundle, year, hours, cap_t)
            - effective_reliability_deployment_mw(year, config)
        )
        lam = _system_lambda(bundle, year, hours)
        res = scarcity_prices(
            config,
            year,
            r_online + r_offline,
            np.nan_to_num(lam),
            reserves_online_mw=r_online,
        )
        adder = res["scarcity_adder"]
        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(hours, dtype=np.int32),
                    "reserves_mw": (r_online + r_offline).astype(np.float32),
                    "reserves_online_mw": r_online.astype(np.float32),
                    "lolp": res["lolp"].astype(np.float32),
                    "scarcity_adder": adder.astype(np.float32),
                    "lmp": lam.astype(np.float32),
                    "lmp_scarcity": (lam + adder).astype(np.float32),
                }
            )
        )

        # Report: incidence + gate metrics vs the actual RT series.
        rt = _actual_rt(year, hours)
        w = _demand_weights(bundle, year, hours)
        mae0 = _monthly_mae(lam, rt, w)
        mae1 = _monthly_mae(lam + adder, rt, w)
        mon = _month_of_hour(np.arange(hours))
        summer = np.isin(mon, [6, 7, 8, 9])
        ok = np.isfinite(rt)
        gap0 = float(np.nansum((rt - lam)[summer & ok]))
        gap1 = float(np.nansum((rt - lam - adder)[summer & ok]))
        print(
            f"\n{year}: adder>$1 in {(adder > 1).sum()} h, >$10 in "
            f"{(adder > 10).sum()} h, >$100 in {(adder > 100).sum()} h, "
            f"max ${adder.max():,.0f}; mean ${adder.mean():.2f}"
        )
        print(
            f"  monthly LMP MAE (gate metric) {mae0:.1f} -> {mae1:.1f} "
            f"$/MWh; hourly dw-MAE {_mae(lam, rt, w):.1f} -> "
            f"{_mae(lam + adder, rt, w):.1f}"
        )
        print(
            f"  hours >$200: actual {int(np.nansum(rt > 200))}, model "
            f"{int(np.nansum(lam > 200))} -> {int(np.nansum((lam + adder) > 200))}; "
            f">$500: actual {int(np.nansum(rt > 500))}, model "
            f"{int(np.nansum(lam > 500))} -> "
            f"{int(np.nansum((lam + adder) > 500))}"
        )
        print(
            f"  Jun-Sep $.h gap (actual - model): {gap0:+,.0f} -> "
            f"{gap1:+,.0f} ({(1 - gap1 / gap0) * 100 if gap0 else 0:.0f}% closed)"
        )

    out = pd.concat(frames, ignore_index=True)
    name = f"scarcity_{args.tag}.parquet" if args.tag else "scarcity.parquet"
    out.to_parquet(bundle / name, index=False)
    print(f"\nwrote {bundle / name}")

    if args.revenue_report:
        revenue_report(bundle, out, years)


def revenue_report(bundle: Path, scarcity: pd.DataFrame, years: list[int]) -> None:
    """Per-class energy revenue with and without the scarcity adder.

    The delta is the scarcity revenue (variable cost is unchanged, so the
    delta is identical on a gross or net basis). The adder is system-wide,
    so each unit's scarcity revenue is adder x dispatch summed hourly.
    """
    print("\n=== per-class energy revenue, $M (energy-only -> with adder) ===")
    for year in years:
        sc = scarcity[scarcity["year"] == year].set_index("hour")
        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
        disp = disp.assign(adder=sc["scarcity_adder"].reindex(disp["hour"]).to_numpy())
        disp = disp.assign(
            rev0=disp["mw"] * disp["lmp"],
            rev_add=disp["mw"] * disp["adder"],
        )
        g = disp.groupby("klass", observed=True)[["rev0", "rev_add"]].sum()
        g = g / 1e6
        g["with_adder"] = g["rev0"] + g["rev_add"]
        g["pct"] = 100.0 * g["rev_add"] / g["rev0"].where(g["rev0"] != 0)
        g = g.sort_values("rev_add", ascending=False)
        print(f"\n{year}:")
        print(
            g.rename(columns={"rev0": "energy_only", "rev_add": "scarcity_rev"})[
                ["energy_only", "scarcity_rev", "with_adder", "pct"]
            ]
            .round(1)
            .head(14)
            .to_string()
        )

        # Storage discharge revenue (storage is not in the dispatch frame).
        p = bundle / "storage.parquet"
        if p.exists():
            st = pd.read_parquet(p)
            st = st[st["year"] == year]
            if "pass" in st.columns and (st["pass"] == "P1").any():
                st = st[st["pass"] == "P1"]
            st = st.assign(
                adder=sc["scarcity_adder"].reindex(st["hour"]).to_numpy(),
                lmp=sc["lmp"].reindex(st["hour"]).to_numpy(),
            )
            dis_rev0 = float((st["discharge_mw"] * st["lmp"]).sum()) / 1e6
            dis_add = float((st["discharge_mw"] * st["adder"]).sum()) / 1e6
            print(
                f"  STORAGE discharge: {dis_rev0:,.1f} -> "
                f"{dis_rev0 + dis_add:,.1f} (+{dis_add:,.1f})"
            )


if __name__ == "__main__":
    main()
