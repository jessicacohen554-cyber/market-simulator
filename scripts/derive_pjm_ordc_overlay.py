"""Derive the PJM stepped-ORDC reserve-scarcity overlay for a solved bundle.

Post-solve only, mirroring ``scripts/derive_ordc_overlay.py`` (ERCOT). Reads a
persisted PJM calibration bundle, reconstructs the hourly fleet availability the
LP solved against (same config / outage overlay — no LP re-solve), measures the
PLANT-LEVEL online (synchronized-basis) reserve, applies PJM's published two-step
ORDC cascade (market_sim.results.scarcity + data/raw/_validation-source/pjm_ordc_curve.csv)
against the MEASURED reserve requirement (``as_req_mw`` from the PJM-AS parquets),
adds the binding reserve price to the energy LMP, and writes ``scarcity.parquet``.
Dispatch/system parquets are untouched; volumes are never gated on the adder.

Modes:
  (default)      build availability + scarcity.parquet + incidence report
  --diagnostic   the HONESTY GATE — model online/total reserve vs the measured
                 requirement, and the actual-minus-model residual by online
                 headroom (is the model thin when reality was thin?)
  --validate-mcp the PRIMARY measured check — the curve vs measured RT/DA reserve
                 MCP, from the parquets, independent of the model dispatch.

Usage:
    python scripts/derive_pjm_ordc_overlay.py results/calibration/pjm_26
        [--years 2023 2024 2025] [--curve data/raw/_validation-source/pjm_ordc_curve.csv]
        [--as-plan MW] [--diagnostic] [--validate-mcp] [--rebuild-availability]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    RESERVE_FUEL_TYPES,
    load_pjm_ordc_curve,
    pjm_reserve_cascade_mcp,
    pjm_reserve_demand_price,
)

# W1 relocated the old inputs/ tree: inputs/calibration -> data/raw/_validation-source
# (paths.CALIBRATION_DIR, holds pjm_ordc_curve.csv + actual_lmp_hourly_PJM.parquet)
# and inputs/raw-data/PJM-AS -> data/raw/PJM-AS (measured reserve requirements).
CAL_DIR = REPO / "data" / "raw" / "_validation-source"
RAW_DIR = REPO / "data" / "raw" / "PJM-AS"
DEFAULT_CURVE = CAL_DIR / "pjm_ordc_curve.csv"

# PJM data `service` code -> curve product name. The RT/DA reserve parquets use
# short codes (SR/PR/30MIN); the curve and cascade use the product names.
_RT_SERVICE_TO_PRODUCT = {"SR": "Synchronized", "PR": "Primary", "30MIN": "Secondary"}
_DA_SERVICE_TO_PRODUCT = {
    "Synchronized Reserve": "Synchronized",
    "Primary Reserve": "Primary",
    "Thirty Minutes Reserve": "Secondary",
}

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])


def _run_year_kwargs(meta: dict) -> dict:
    """Mirror solve_and_persist's run_year call from a bundle's meta.json."""
    return dict(
        ttc_overrides={},
        commitment_enabled=False,
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
        # Reconstruct the SAME fleet the dispatch was solved against: when the
        # bundle withheld reserve from energy, the availability the
        # online-reserve primitive measures must carry that withdrawal too, or
        # it reports full headroom against a withheld dispatch and over-states
        # the reserve by the withdrawn MW.
        as_reserve_withholding=meta.get("as_reserve_withholding", False),
        # DA virtual-bid layer (G-22 lever B): a bundle solved with the
        # pseudo-units must rebuild them here too, or the diagnostics'
        # fleet/mc reconstruction drops the virtual rows the dispatch
        # parquet carries.
        pjm_da_virtual_bids=meta.get("pjm_da_virtual_bids", False),
        fleet_only=True,
    )


def build_availability(
    bundle: Path, years: list[int], meta: dict, force: bool = False
) -> pd.DataFrame:
    """Reconstruct (or load) hourly model reserve series for the bundle.

    Returns a frame ``year, hour, online_reserve_mw, total_reserve_mw`` where
    ``online_reserve_mw`` is the PLANT-LEVEL synchronized thermal reserve
    (headroom of plants with any tranche dispatching) and ``total_reserve_mw``
    is the whole thermal fleet's headroom (including idle plants). Cached as
    ``pjm_availability.parquet``; rebuilt through the bundle's meta.json config
    (no LP solve). See the honesty gate in docs/multi-iso/pjm-reserve-ordc.md.
    """
    out_path = bundle / "pjm_availability.parquet"
    if out_path.exists() and not force:
        cached = pd.read_parquet(out_path)
        if set(cached["year"].unique()) >= set(years):
            return cached

    from run_calibration import run_year  # late import: heavy module

    hours = meta["hours"]
    frames = []
    for year in years:
        state = run_year(
            year,
            meta["iso"],
            hours,
            meta["gas_prices"][str(year)],
            **_run_year_kwargs(meta),
        )
        fa = state["fleet_arrays"]
        fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
        thermal = np.isin(fuel, sorted(RESERVE_FUEL_TYPES))
        avail = fa.pmax[:, None] * fa.availability  # (n_unit, T)
        uids = np.asarray(fa.unit_ids, dtype=object)

        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
        dmat = (
            disp.pivot_table(
                index="unit_id", columns="hour", values="mw", aggfunc="sum"
            )
            .reindex(uids)
            .fillna(0.0)
            .to_numpy()
        )
        # plant_code per unit (a plant's tranches share it).
        pc = (
            disp.drop_duplicates("unit_id")
            .set_index("unit_id")
            .reindex(uids)["plant_code"]
            .fillna(-1)
            .to_numpy()
        )

        th_avail, th_disp, th_pc = avail[thermal], dmat[thermal], pc[thermal]
        total_reserve = (th_avail - th_disp).sum(axis=0)
        codes, inv = np.unique(th_pc, return_inverse=True)
        pa = np.zeros((len(codes), hours))
        pd_ = np.zeros((len(codes), hours))
        np.add.at(pa, inv, th_avail)
        np.add.at(pd_, inv, th_disp)
        online = pd_ > 0.5
        online_reserve = np.where(online, pa - pd_, 0.0).sum(axis=0)

        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(hours, dtype=np.int32),
                    "online_reserve_mw": online_reserve.astype(np.float32),
                    "total_reserve_mw": total_reserve.astype(np.float32),
                }
            )
        )
        print(
            f"  {year}: online reserve mean {online_reserve.mean():,.0f} MW "
            f"(median {np.median(online_reserve):,.0f}); total reserve mean "
            f"{total_reserve.mean():,.0f} MW"
        )
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(out_path, index=False)
    print(f"wrote {out_path}")
    return df


def _measured_requirement(
    year: int, hours: int, locale: str = "PJM_RTO", da: bool = False
) -> dict[str, np.ndarray]:
    """Hourly measured reserve requirement (MW) per product, NaN-padded.

    Aggregates the 5-minute RT reserve-market parquet (or the hourly DA one) to
    the model's non-leap hour-of-year clock. Returns ``{product: (hours,)}``
    for Synchronized / Primary / Secondary.
    """
    fname = (
        f"da_reserve_market_results_{year}.parquet"
        if da
        else f"reserve_market_results_{year}.parquet"
    )
    df = pd.read_parquet(RAW_DIR / fname)
    loc = (
        locale
        if not da
        else (
            "PJM RTO Reserve Zone"
            if locale == "PJM_RTO"
            else "Mid-Atlantic/Dominion Reserve Subzone"
        )
    )
    df = df[df["locale"] == loc].copy()
    fmt = None if da else "%m/%d/%Y %I:%M:%S %p"
    df["dt"] = pd.to_datetime(df["datetime_beginning_ept"], format=fmt, errors="coerce")
    df["hoy"] = (
        (df["dt"] - pd.Timestamp(f"{year}-01-01")).dt.total_seconds() // 3600
    ).astype("Int64")
    svc_map = _DA_SERVICE_TO_PRODUCT if da else _RT_SERVICE_TO_PRODUCT
    out: dict[str, np.ndarray] = {}
    for code, product in svc_map.items():
        s = df[df["service"] == code].groupby("hoy")["as_req_mw"].mean()
        arr = np.full(hours, np.nan)
        idx = s.index.dropna().astype(int)
        keep = idx[(idx >= 0) & (idx < hours)]
        arr[keep] = s.loc[keep].to_numpy()
        out[product] = arr
    return out


def _system_lambda(bundle: Path, year: int, hours: int) -> np.ndarray:
    """Demand-weighted hourly system price (P1) — the model system lambda."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    g = (
        sy.assign(pd_=sy["price"] * sy["demand"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), d=("demand", "sum"))
    )
    lam = np.full(hours, np.nan)
    lam[g.index.to_numpy()] = np.where(g["d"] > 0, g["pd_"] / g["d"], np.nan)
    return lam


def _actual_rt(year: int, hours: int) -> np.ndarray:
    """Actual hub-mean hourly RT LMP for PJM, NaN-padded."""
    p = CAL_DIR / "actual_lmp_hourly_PJM.parquet"
    if not p.exists():
        return np.full(hours, np.nan)
    act = pd.read_parquet(p)
    act = act[act["year"] == year]
    out = np.full(hours, np.nan)
    out[act["hour"].to_numpy()] = act["rt"].to_numpy()
    return out


def validate_mcp(years: list[int], curve: dict) -> None:
    """PRIMARY measured check: the curve vs measured MCP, from the parquets.

    Uses MEASURED cleared reserves (``total_mw``) and MEASURED requirement
    (``as_req_mw``) — no model dispatch. The reserve MCP is
    ``min(marginal reserve offer, penalty factor)``: in normal conditions a
    resource's opportunity-cost offer (below the penalty factor) sets the price,
    and the penalty factor only sets it in a genuine shortage. The energy-only
    overlay can only represent the PENALTY-FACTOR (shortage) component, so this
    validates the curve there, two honest ways:

    1. Penalty LEVELS: the measured RT maxima are exact multiples of $850 — the
       Synchronized/Primary/Secondary cascade (1x/2x/3x), Manual 11 sec 4.4.1.
    2. Deficiency -> shortage price: in intervals where cleared ``total_mw`` is
       below the requirement, the measured mcp is at the penalty level.

    The heavy-load requirement EXTENSION (Manual 11 sec 4.3 Step 2) means some
    penalty-priced intervals show cleared MW above the *posted* ``as_req_mw``
    (the binding curve used an extended requirement) — reported as a caveat.
    """
    print("\n=== PRIMARY measured validation: curve vs measured MCP (PJM_RTO) ===")
    print("(1) Penalty LEVELS — measured RT maxima vs the $850 cascade:")
    for year in years:
        df = pd.read_parquet(RAW_DIR / f"reserve_market_results_{year}.parquet")
        rto = df[df["locale"] == "PJM_RTO"]
        mx = {s: rto[rto["service"] == s]["mcp"].max() for s in ("SR", "PR", "30MIN")}
        print(
            f"  {year}: SR ${mx['SR']:,.0f} (={mx['SR'] / 850:.0f}x850), "
            f"PR ${mx['PR']:,.0f} (={mx['PR'] / 850:.0f}x850), "
            f"30MIN ${mx['30MIN']:,.0f} (={mx['30MIN'] / 850:.0f}x850)"
        )

    print("(2) Deficiency -> shortage price (Synchronized own curve):")
    steps = curve[("Synchronized", "RTO")]
    for da in (False, True):
        tag = "DA hourly" if da else "RT 5-min"
        for year in years:
            fname = (
                f"da_reserve_market_results_{year}.parquet"
                if da
                else f"reserve_market_results_{year}.parquet"
            )
            df = pd.read_parquet(RAW_DIR / fname)
            loc = "PJM RTO Reserve Zone" if da else "PJM_RTO"
            code = "Synchronized Reserve" if da else "SR"
            sub = df[(df["locale"] == loc) & (df["service"] == code)].dropna(
                subset=["as_req_mw", "total_mw", "mcp"]
            )
            if sub.empty:
                continue
            total = sub["total_mw"].to_numpy()
            req = sub["as_req_mw"].to_numpy()
            meas = sub["mcp"].to_numpy()
            pred = pjm_reserve_demand_price(total, req, steps)
            defi = total < req - 0.5  # genuine cleared deficiency
            n = int(defi.sum())
            priced = (meas[defi] >= 300.0).mean() * 100 if n else float("nan")
            # extension caveat: penalty-priced but cleared above posted req.
            hi = meas >= 850.0
            ext = int(((total >= req) & hi).sum())
            print(
                f"  {tag} {year}: cleared-deficient intervals {n}; of those "
                f"measured mcp>=$300 in {priced:.0f}%; curve step (own) median "
                f"${np.median(pred[defi]) if n else 0:,.0f}; "
                f"penalty-priced-via-extension intervals {ext}"
            )


def diagnostic(avail: pd.DataFrame, bundle: Path, years: list[int], hours: int) -> None:
    """HONESTY GATE: is the model thin (online) when reality was thin?

    Prints, per year, the model's online vs total reserve, how often the step
    curve would bite against the measured requirement, and the actual-minus-
    model LMP residual by online-reserve band.
    """
    for year in years:
        a = avail[avail["year"] == year]
        online = a["online_reserve_mw"].to_numpy(float)
        total = a["total_reserve_mw"].to_numpy(float)
        req = _measured_requirement(year, hours)
        lam = _system_lambda(bundle, year, hours)
        rt = _actual_rt(year, hours)
        resid = rt - lam

        pr = req["Primary"]
        m = np.isfinite(pr)
        step1 = int((online[m] < pr[m]).sum())
        step2 = int(((online[m] >= pr[m]) & (online[m] < pr[m] + 190)).sum())
        tot_short = int((total[m] < pr[m]).sum())
        print(f"\n=== {year} HONESTY GATE (PJM_RTO) ===")
        print(
            f"  online reserve: mean {online.mean():,.0f} MW, median "
            f"{np.median(online):,.0f} MW"
        )
        print(f"  total  reserve: mean {total.mean():,.0f} MW")
        print(
            f"  measured Primary requirement: mean {np.nanmean(pr):,.0f} MW "
            f"(+190 step-2 breakpoint ~{np.nanmean(pr) + 190:,.0f} MW)"
        )
        print(
            f"  curve bites on ONLINE reserve: step1(<req) {step1} h, "
            f"step2(req..+190) {step2} h of {int(m.sum())}"
        )
        print(
            f"  curve bites on TOTAL reserve:  step1 {tot_short} h "
            f"(total headroom never goes short)"
        )

        # measured RT shortage hours: was the model thin there?
        rtres = pd.read_parquet(RAW_DIR / f"reserve_market_results_{year}.parquet")
        rtres = rtres[(rtres.locale == "PJM_RTO") & (rtres.service == "SR")]
        rtres = rtres.copy()
        rtres["dt"] = pd.to_datetime(
            rtres["datetime_beginning_ept"],
            format="%m/%d/%Y %I:%M:%S %p",
            errors="coerce",
        )
        rtres["hoy"] = (
            (rtres["dt"] - pd.Timestamp(f"{year}-01-01")).dt.total_seconds() // 3600
        ).astype("Int64")
        sh = rtres[rtres["mcp"] >= 300]["hoy"].dropna().astype(int)
        sh = sh[(sh >= 0) & (sh < hours)].unique()
        if len(sh):
            print(
                f"  measured RT SR shortage hours (mcp>=$300): {len(sh)}; "
                f"their model online reserve median {np.median(online[sh]):,.0f}"
                f" MW vs overall {np.median(online):,.0f} MW"
            )

        ok = np.isfinite(resid)
        bins = [-np.inf, 4e3, 6e3, 8e3, 10e3, 13e3, 16e3, 20e3, np.inf]
        labels = ["<4G", "4-6G", "6-8G", "8-10G", "10-13G", "13-16G", "16-20G", ">20G"]
        tbl = (
            pd.DataFrame(
                {
                    "bin": pd.cut(online[ok], bins, labels=labels),
                    "resid": resid[ok],
                    "rt": rt[ok],
                }
            )
            .groupby("bin", observed=True)
            .agg(
                hours=("resid", "size"),
                resid_mean=("resid", "mean"),
                rt_mean=("rt", "mean"),
            )
        )
        print("  actual-minus-model residual by ONLINE reserve band:")
        print("    " + tbl.round(1).to_string().replace("\n", "\n    "))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--curve", type=Path, default=DEFAULT_CURVE)
    ap.add_argument(
        "--as-plan",
        type=float,
        default=0.0,
        help="AS-plan MW netted from the model online reserve",
    )
    ap.add_argument(
        "--diagnostic",
        action="store_true",
        help="honesty gate only (no overlay written)",
    )
    ap.add_argument(
        "--validate-mcp",
        action="store_true",
        help="reproduce measured MCP from the curve (no model)",
    )
    ap.add_argument("--rebuild-availability", action="store_true")
    args = ap.parse_args()

    curve = load_pjm_ordc_curve(args.curve)

    if args.validate_mcp:
        years = args.years or [2023, 2024, 2025]
        validate_mcp(years, curve)
        return

    bundle = args.bundle.resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    if meta["iso"] != "PJM":
        raise SystemExit("PJM ORDC overlay is PJM-only")
    years = args.years or meta["years"]
    hours = meta["hours"]

    print(f"bundle {bundle.name}: years {years}")
    avail = build_availability(bundle, years, meta, force=args.rebuild_availability)

    if args.diagnostic:
        diagnostic(avail, bundle, years, hours)
        return

    frames = []
    for year in years:
        a = avail[avail["year"] == year]
        online = a["online_reserve_mw"].to_numpy(float) - args.as_plan
        req = _measured_requirement(year, hours)
        # One online-reserve pool measured against each product requirement
        # (the model has no 10-/30-min ramp state to split synchronized from
        # quick-start; using the same pool is the documented upper bound — it
        # OVERSTATES reserves and so understates the adder).
        reserves = {p: online for p in ("Synchronized", "Primary", "Secondary")}
        # Forward-fill measured requirement gaps (NaN hours from DST/clock).
        reqs = {
            p: pd.Series(req[p]).ffill().bfill().to_numpy()
            for p in ("Synchronized", "Primary", "Secondary")
        }
        cb = {p: curve[(p, "RTO")] for p in ("Synchronized", "Primary", "Secondary")}
        mcp = pjm_reserve_cascade_mcp(reserves, reqs, cb)
        adder = mcp["energy_adder"]
        lam = _system_lambda(bundle, year, hours)
        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(hours, dtype=np.int32),
                    "reserves_mw": online.astype(np.float32),
                    "srmcp": mcp["SR"].astype(np.float32),
                    "nsrmcp": mcp["PR"].astype(np.float32),
                    "secmcp": mcp["30MIN"].astype(np.float32),
                    "scarcity_adder": adder.astype(np.float32),
                    "lmp": lam.astype(np.float32),
                    "lmp_scarcity": (lam + adder).astype(np.float32),
                }
            )
        )
        rt = _actual_rt(year, hours)
        print(
            f"\n{year}: scarcity adder >$0 in {(adder > 0).sum()} h, "
            f">$300 in {(adder >= 300).sum()} h, max ${adder.max():,.0f}, "
            f"mean ${adder.mean():.3f}"
        )
        print(
            f"  energy-only hours >$75: {int(np.nansum(lam > 75))} -> "
            f"+overlay {int(np.nansum((lam + adder) > 75))} "
            f"(actual {int(np.nansum(rt > 75))})"
        )

    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(bundle / "scarcity.parquet", index=False)
    print(f"\nwrote {bundle / 'scarcity.parquet'}")


if __name__ == "__main__":
    main()
