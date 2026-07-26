"""ERCOT-117 Task A: locate the coal-vs-gas mid-merit ranking bias (no LP).

ERCOT-116 (``FINDING-ercot116-coal-seasonal-availability-2026-07-26.md``)
established that with the measured coal DAM envelope armed, coal over-runs
+6.8/+9.2/+12.9 TWh at MATCHED absolute price — +9-29 pp in the $15-25 bands,
both seasons, all years — and the surplus coal is the missing gas
(corr(dCoal,dGas) = -0.93..-0.97). A season-invariant RANKING bias between coal
and gas-CC in the band where they cross expresses seasonally because summer has
more mid-merit hours. This probe measures the ranking's two sides directly,
before any mechanism is written (the ERCOT-111..116 discipline):

**A. MEASURED DAM supply curves.** From the raw 60-Day DAM disclosure
(``data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet``),
the committed (online-status) COAL and CC fleets' incremental-offer supply at
each absolute price x: per resource-hour the QSE-submitted 10-point curve gives
``MW offered at price <= x`` (the curve is monotone, so it is the last point at
or below x); summed per delivery hour, averaged within summer (Jun-Sep) vs
shoulder. LSL (the committed min-load the market price-takes) is reported
alongside so the curve's price-taking base is visible.

**B. MODEL P1 supply curves.** The ERCOT-99/113 capture technique (monkeypatch
``run_energy_solve``, grab the built fleet + ``mc_base``/``mc_bid_adjust``,
abort before HiGHS): deliverable MW (pmax x availability) whose P1 bid is <= x,
same price grid, same seasons — the exact array the LP ranks on. The measured
(A) and model (B) curves are then directly comparable per year: whichever side
of the $15-25 crossing carries the displaced MW is the bias's owner.

**C. Coal price basis (the F923 receipts lead).** EIA-923 monthly delivered
coal cost per ERCOT plant (quantity-weighted) against the basis the model
dispatches on: the PRB reporter-proxy monthly series / flat trajectory and the
flat lignite constant. If the real fleet pays materially more (less) than the
model's basis, the model's coal curve is shifted cheap (dear) at every band
before the sigmoid even applies.

**D. Model coal offer decomposition.** Per coal tranche band: capacity, HR
multiplier, effective gas-keyed passthrough and the resulting $/MWh by season —
which factor (band mult, fuel basis, passthrough floor) puts model coal under
the measured curve, band by band.

**E. Measured RT (SCED TPO) supply curves.** From the 60-Day SCED disclosure
probe-day subsets on disk (2024/2025 tail + control day families): the online
coal fleet's RT three-part-offer supply at each price, floored at LSL for
curve-carrying units and at the output schedule for output-scheduled units,
against telemetered HASL and base points. This is the curve SCED actually
dispatches — it settles whether the committed coal capability the DAM never
sees (QSE self-supply) is withheld, telemetered-down, or simply priced.

**F. Crossing-band price formation.** From committed keeper/arm ``hourly/``
sidecars: the model's load-weighted P1 price (with ORDC/RTORDPA adders, the
ercot112-scorer construction) inside fixed ACTUAL-price bands ($10-15, $15-25,
$25-40) — whether the model's clearing level in the coal-vs-CC crossing band
sits on the measured level or above it, per year and season.

No LP is solved; nothing is written to the repo. Usage::

    python scripts/probes/ercot117_coal_gas_ranking.py --all-years
    python scripts/probes/ercot117_coal_gas_ranking.py --year 2024 --skip-model
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
SUMMER = (6, 7, 8, 9)

# Absolute-price grid ($/MWh) spanning the coal/CC crossing; the $15-25 bands
# are where ERCOT-116 localized the displacement.
PRICE_GRID = (5.0, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0, 27.5, 30.0, 35.0, 40.0, 60.0)

# Resource Type -> comparison class (parse_ercot_dam_offers.RESOURCE_TYPE_TO_CLASS).
_TYPE_TO_CLASS = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "CLLIG": "COAL",
    "SCGT90": "CT",
    "SCLE90": "CT",
    "GSREH": "ST_GAS",
    "GSNONR": "ST_GAS",
    "GSSUP": "ST_GAS",
}
# DAM statuses meaning online/committed (parse_ercot_dam_offers.ONLINE_STATUSES).
_ONLINE = {"ON", "ONOS", "ONRR", "ONTEST", "ONEMR", "ONREG", "EMR", "EMRSWGR"}

_RAW_DIR = REPO / "data/raw/ercot"
_E923_COSTS = REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
_DEFAULT_BUNDLE = "results/calibration/ercot115_coal_floor_only"


class _StopAfterCapture(BaseException):
    """Abort the run after the fleet build is captured (dodges except Exception)."""


def _month_of_hour(hours: int) -> np.ndarray:
    """Month index (1-12) for each model hour (non-leap 8760 clock)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:hours]


# =============================================================================
# A - measured DAM committed supply at price <= x
# =============================================================================


def _year_files(year: int) -> list[Path]:
    """The raw Gen_Resource_Data parquets covering one delivery year."""
    pat = str(_RAW_DIR / f"60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet")
    return [Path(p) for p in sorted(globmod.glob(pat))]


def measured_supply(year: int, classes: tuple[str, ...] = ("COAL", "CC")) -> pd.DataFrame | None:
    """Committed-fleet MW offered at <= x, per (class, month), hour-mean.

    For each committed resource-hour the 10-point QSE curve is evaluated at
    every grid price (monotone curve: the max MW among points priced <= x,
    clipped to [0, HSL]) and floored at the unit's LSL — a committed unit's
    min-load energy is bought regardless of the energy curve (the three-part
    Min Gen Cost floor; ERCOT-111 measured the fleet price-taking to LSL), so
    the committed supply at any price is at least LSL. ``lsl`` / ``hsl`` carry
    the committed min-load and capability alongside, and ``reach`` the highest
    supply the curve makes available at ANY price (``max(LSL, curve top)``) —
    committed capability above it is never offered into DAM energy.
    """
    files = _year_files(year)
    if not files:
        return None
    mw_cols = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
    pr_cols = [f"QSE submitted Curve-Price{k}" for k in range(1, 11)]
    cols = ["Delivery Date", "Hour Ending", "Resource Type", "Resource Status",
            "HSL", "LSL"] + mw_cols + pr_cols

    per_hour_frames = []
    for path in files:
        df = pd.read_parquet(path, columns=cols)
        df["cls"] = df["Resource Type"].map(_TYPE_TO_CLASS)
        df = df[df["cls"].isin(classes)]
        df = df[df["Resource Status"].str.strip().isin(_ONLINE)]
        if df.empty:
            continue
        dt = pd.to_datetime(df["Delivery Date"])
        df = df.assign(_month=dt.dt.month.to_numpy(), _date=dt.dt.normalize())
        P = df[pr_cols].to_numpy(float)
        M = df[mw_cols].to_numpy(float)
        hsl = df["HSL"].to_numpy(float)
        lsl = np.clip(df["LSL"].to_numpy(float), 0.0, hsl)
        ok = np.isfinite(P) & np.isfinite(M)
        out = {"month": df["_month"], "date": df["_date"], "he": df["Hour Ending"],
               "cls": df["cls"], "lsl": lsl, "hsl": hsl}
        top = np.max(np.where(ok, M, -np.inf), axis=1)
        out["reach"] = np.maximum(
            lsl, np.clip(np.where(np.isfinite(top), top, 0.0), 0.0, hsl)
        )
        for x in PRICE_GRID:
            sel = ok & (P <= x)
            sup = np.max(np.where(sel, M, -np.inf), axis=1)
            out[f"le_{x:g}"] = np.maximum(
                lsl, np.clip(np.where(np.isfinite(sup), sup, 0.0), 0.0, hsl)
            )
        per_hour_frames.append(
            pd.DataFrame(out)
            .groupby(["cls", "month", "date", "he"], observed=True)
            .sum(numeric_only=True)
            .reset_index()
        )
    if not per_hour_frames:
        return None
    hourly = pd.concat(per_hour_frames, ignore_index=True)
    monthly = (
        hourly.groupby(["cls", "month"], observed=True)
        .mean(numeric_only=True)
        .drop(columns=["he"], errors="ignore")
    )
    return monthly


def season_view(monthly: pd.DataFrame) -> pd.DataFrame:
    """Collapse a per-(class, month) table to summer / shoulder means."""
    t = monthly.reset_index()
    t["season"] = np.where(t["month"].isin(SUMMER), "summer", "shoulder")
    return t.groupby(["cls", "season"], observed=True).mean(numeric_only=True).drop(
        columns=["month"]
    )


# =============================================================================
# B - model P1 supply at bid <= x (capture, no solve)
# =============================================================================


def capture(bundle: Path, year: int) -> dict:
    """Build the bundle's fleet for one year and grab the P1 offer inputs.

    The ERCOT-113 technique: patch ``run_energy_solve`` inside the calibration
    runner, let ``solve_and_persist`` drive the full fleet/mc assembly, and
    abort before the LP is constructed.
    """
    import replay_keeper  # noqa: F401  (adds scripts to path, pins warmstart)
    import run_calibration_full as rcf

    rc_mod = sys.modules[rcf.run_year.__module__]
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = REPO / "scratch" / "ercot117_capture_junk"
    kwargs["note"] = "ERCOT-117 ranking capture (aborts before solve)"

    grabbed: dict = {}
    real = rc_mod.run_energy_solve

    def _patched(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
        grabbed["fleet"] = fleet
        grabbed["fa"] = fleet_arrays
        grabbed["config"] = config
        grabbed["mc_base"] = np.asarray(mc_base)
        adj = kw.get("mc_bid_adjust")
        grabbed["mc_bid_adjust"] = None if adj is None else np.asarray(adj)
        raise _StopAfterCapture()

    rc_mod.run_energy_solve = _patched
    try:
        rcf.solve_and_persist(**kwargs)
    except _StopAfterCapture:
        pass
    finally:
        rc_mod.run_energy_solve = real
    if "fleet" not in grabbed:
        raise SystemExit(f"{year}: capture failed (run_energy_solve never reached)")
    return grabbed


def _class_masks(fleet) -> dict[str, np.ndarray]:
    """COAL / CC row masks over the built fleet (CC = CC_REGULAR + CC_CHP)."""
    grp = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    return {
        "COAL": np.char.startswith(grp.astype(str), "COAL"),
        "CC": np.isin(grp, ("CC_REGULAR", "CC_CHP")),
    }


def model_supply(g: dict) -> pd.DataFrame:
    """Deliverable MW at P1 bid <= x per (class, month), hour-mean."""
    fleet, fa = g["fleet"], g["fa"]
    mc = g["mc_base"]
    if g["mc_bid_adjust"] is not None:
        mc = mc + g["mc_bid_adjust"]
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)
    deliverable = np.asarray(fa.pmax, float)[:, None] * avail
    mo = _month_of_hour(mc.shape[1])

    rows = []
    for cls, mask in _class_masks(fleet).items():
        d, o = deliverable[mask], mc[mask]
        for m in range(1, 13):
            sel = mo == m
            r = {"cls": cls, "month": m,
                 "deliv_mw": float(d[:, sel].sum(axis=0).mean())}
            for x in PRICE_GRID:
                r[f"le_{x:g}"] = float((d[:, sel] * (o[:, sel] <= x)).sum(axis=0).mean())
            rows.append(r)
    return pd.DataFrame(rows).set_index(["cls", "month"])


# =============================================================================
# C - coal price basis: F923 receipts vs the model's dispatch basis
# =============================================================================


def coal_price_basis(year: int) -> pd.DataFrame | None:
    """Measured EIA-923 delivered coal $/MMBtu per ERCOT plant vs model basis."""
    if not _E923_COSTS.exists():
        return None
    from market_sim.data.coal import COAL_PLANT_SUPPLY
    from market_sim.data.fuel.coal import (
        COAL_PRICE_LIGNITE_BY_YEAR,
        COAL_PRICE_PRB_BY_YEAR,
        _prb_monthly_actuals,
    )

    costs = pd.read_parquet(_E923_COSTS)
    sub = costs[
        (costs["year"] == year)
        & (costs["fuel_group"] == "Coal")
        & costs["plant_id"].isin(COAL_PLANT_SUPPLY)
        & costs["price_per_mmbtu"].notna()
        & (costs["quantity"] > 0)
    ]
    monthly = _prb_monthly_actuals().get(year)
    prb_proxy = float(np.mean(monthly)) if monthly is not None else float(
        COAL_PRICE_PRB_BY_YEAR[year]
    )
    rows = []
    for plant, supply in sorted(COAL_PLANT_SUPPLY.items()):
        p = sub[sub["plant_id"] == plant]
        measured = (
            float(np.average(p["price_per_mmbtu"], weights=p["quantity"]))
            if not p.empty
            else np.nan
        )
        model = (
            float(COAL_PRICE_LIGNITE_BY_YEAR[year]) if supply == "lignite" else prb_proxy
        )
        rows.append(
            {
                "plant": plant,
                "supply": supply,
                "n_months": int(len(p)),
                "f923_pmmbtu": measured,
                "model_basis": model,
                "gap": measured - model if np.isfinite(measured) else np.nan,
            }
        )
    return pd.DataFrame(rows).set_index("plant")


# =============================================================================
# D - model coal band decomposition
# =============================================================================


def _band_of(unit_id: str) -> str:
    """Tranche band label from the bins_to_fleet unit-id suffix."""
    for band in ("mustrun", "sync", "committed", "econlo", "econhi", "peak"):
        if f"_{band}" in unit_id:
            return band
    if "_econc" in unit_id:
        return "econ_ramp"
    return "other"


def coal_band_table(g: dict) -> pd.DataFrame:
    """Per-(supply, band): capacity and season-mean P1 bid of the coal fleet."""
    fleet, fa = g["fleet"], g["fa"]
    mc = g["mc_base"]
    if g["mc_bid_adjust"] is not None:
        mc = mc + g["mc_bid_adjust"]
    mo = _month_of_hour(mc.shape[1])
    su = np.isin(mo, SUMMER)

    rows = []
    for i, gen in enumerate(fleet):
        grp = str(getattr(gen, "plant_group", "") or "")
        if not grp.startswith("COAL"):
            continue
        rows.append(
            {
                "supply": getattr(gen, "coal_supply", "") or "?",
                "band": _band_of(gen.unit_id),
                "pmax_mw": float(gen.pmax_mw),
                "hr": float(gen.heat_rate),
                "summer_bid": float(mc[i, su].mean()),
                "shoulder_bid": float(mc[i, ~su].mean()),
            }
        )
    t = pd.DataFrame(rows)
    agg = t.groupby(["supply", "band"], observed=True).apply(
        lambda d: pd.Series(
            {
                "pmax_mw": d["pmax_mw"].sum(),
                "hr_capwt": np.average(d["hr"], weights=d["pmax_mw"]),
                "summer_bid": np.average(d["summer_bid"], weights=d["pmax_mw"]),
                "shoulder_bid": np.average(d["shoulder_bid"], weights=d["pmax_mw"]),
            }
        ),
        include_groups=False,
    )
    return agg


def passthrough_view(g: dict, year: int) -> pd.DataFrame:
    """Monthly effective gas-keyed passthrough per coal supply tier."""
    from market_sim.data.fuel import (
        coal_passthrough_by_supply,
        prb_follower_passthrough_series,
    )

    config = g["config"]
    hours = g["mc_base"].shape[1]
    mo = _month_of_hour(hours)
    series = coal_passthrough_by_supply(config, year, hours)
    if getattr(config, "coal_prb_passthrough_tiered", False):
        series["prb_follower"] = prb_follower_passthrough_series(config, year, hours)
    rows = {}
    for supply, s in series.items():
        arr = np.full(hours, float(s)) if np.isscalar(s) else np.asarray(s, float)
        rows[supply] = [float(arr[mo == m].mean()) for m in range(1, 13)]
    return pd.DataFrame(rows, index=pd.RangeIndex(1, 13, name="month")).T


# =============================================================================
# E - measured RT (SCED TPO) supply curves, probe-day subsets
# =============================================================================

_SCED_FILES: tuple[tuple[str, str], ...] = (
    ("2024 control days", "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2024_ercot75_control_days.parquet"),
    ("2024 tail days", "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2024_ercot74_tail_days.parquet"),
    ("2025 control days", "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2025_ercot75_control_days.parquet"),
    ("2025 tail days", "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2025_ercot86_tail_days.parquet"),
)
_RT_GRID = (10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 60.0, 100.0, 200.0, 1000.0)


def rt_supply(path: Path, restypes: frozenset[str]) -> pd.Series | None:
    """Fleet-mean online RT supply at <= x from the SCED TPO curves.

    Curve-carrying units floor at LSL (min-load energy is not price-released);
    output-scheduled units (no TPO points) price-take at their clipped output
    schedule. Supply clips to telemetered HASL. Returns the interval-mean
    fleet totals: HASL, base point, and MW at each ``_RT_GRID`` price.
    """
    if not path.exists():
        return None
    mw_cols = [f"Submitted TPO-MW{k}" for k in range(1, 11)]
    pr_cols = [f"Submitted TPO-Price{k}" for k in range(1, 11)]
    df = pd.read_parquet(
        path,
        columns=["SCED Time Stamp", "Resource Type", "Telemetered Resource Status",
                 "Base Point", "Output Schedule", "HASL", "LSL"] + mw_cols + pr_cols,
    )
    df = df[df["Resource Type"].isin(restypes)]
    df = df[~df["Telemetered Resource Status"].isin(("OUT", "OFF", "OFFNS"))]
    if df.empty:
        return None
    P = df[pr_cols].to_numpy(float)
    M = df[mw_cols].to_numpy(float)
    hasl = df["HASL"].to_numpy(float)
    lsl = np.clip(df["LSL"].to_numpy(float), 0.0, hasl)
    ok = np.isfinite(P) & np.isfinite(M)
    has_curve = ok.any(axis=1)
    osched = np.clip(np.nan_to_num(df["Output Schedule"].to_numpy(float)), lsl, hasl)
    base = np.where(has_curve, 0.0, osched)
    out = {"ts": df["SCED Time Stamp"],
           "hasl": hasl, "bp": df["Base Point"].to_numpy(float)}
    for x in _RT_GRID:
        sel = ok & (P <= x)
        sup = np.max(np.where(sel, M, -np.inf), axis=1)
        sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), 0.0, hasl)
        out[f"le_{x:g}"] = np.where(has_curve, np.maximum(lsl, sup), base)
    return pd.DataFrame(out).groupby("ts").sum().mean()


# =============================================================================
# F - crossing-band price formation (committed sidecars)
# =============================================================================


def crossing_band_prices(bundle: Path, year: int) -> pd.DataFrame | None:
    """Model load-weighted P1 price inside fixed ACTUAL-price bands."""
    from ercot114_coal_quantity_drivers import _actual_price, _system_price

    act = _actual_price(year)
    mp = _system_price(bundle, year)
    if act is None or mp is None:
        return None
    mo = _month_of_hour(len(mp))
    rows = []
    for lo, hi in ((10.0, 15.0), (15.0, 25.0), (25.0, 40.0)):
        m = (act >= lo) & (act < hi) & np.isfinite(mp)
        su = m & np.isin(mo, SUMMER)
        rows.append(
            {
                "band": f"[{lo:g},{hi:g})",
                "hours": int(m.sum()),
                "actual_mean": float(act[m].mean()),
                "model_mean": float(mp[m].mean()),
                "summer_hours": int(su.sum()),
                "summer_model": float(np.nanmean(mp[su])) if su.any() else np.nan,
            }
        )
    return pd.DataFrame(rows).set_index("band")


# =============================================================================


def main(argv: list[str] | None = None) -> int:
    """Run the four measurements and print the comparison tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=_DEFAULT_BUNDLE)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--all-years", action="store_true")
    ap.add_argument("--skip-model", action="store_true",
                    help="only the measured (A) and price-basis (C) reads")
    args = ap.parse_args(argv)

    years = list(YEARS) if args.all_years else [args.year or 2024]
    bundle = REPO / args.bundle
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 40)

    le_cols = [f"le_{x:g}" for x in PRICE_GRID]

    for year in years:
        print("=" * 100)
        print(f"### {year}")
        print("=" * 100)

        print("\n--- A. MEASURED committed DAM supply at price <= x ($/MWh), hour-mean MW ---")
        meas = measured_supply(year)
        if meas is None:
            print("  raw 60-day files unavailable")
        else:
            sv = season_view(meas)
            print(sv[["lsl", "hsl", "reach"] + le_cols].round(0).to_string())

        if not args.skip_model:
            print(f"\n[capture] {year} — building model fleet (no solve)...", flush=True)
            g = capture(bundle, year)

            print("\n--- B. MODEL deliverable supply at P1 bid <= x ($/MWh), hour-mean MW ---")
            ms = model_supply(g)
            t = ms.reset_index()
            t["season"] = np.where(t["month"].isin(SUMMER), "summer", "shoulder")
            msv = t.groupby(["cls", "season"], observed=True).mean(
                numeric_only=True
            ).drop(columns=["month"])
            print(msv[["deliv_mw"] + le_cols].round(0).to_string())

            if meas is not None:
                print("\n--- A-B DELTA (model minus measured), MW at price <= x ---")
                delta = msv[le_cols].sub(sv[le_cols], axis=0)
                print(delta.round(0).to_string())

            print("\n--- D. MODEL coal bands (cap-weighted P1 bid $/MWh) ---")
            print(coal_band_table(g).round(2).to_string())

            print("\n--- D2. effective gas-keyed passthrough by month ---")
            print(passthrough_view(g, year).round(3).to_string())

        print("\n--- C. Coal delivered-price basis: F923 vs model ($/MMBtu) ---")
        basis = coal_price_basis(year)
        if basis is None:
            print("  F923 costs unavailable")
        else:
            print(basis.round(3).to_string())

        print("\n--- F. Model price inside fixed ACTUAL-price bands ($/MWh) ---")
        f = crossing_band_prices(bundle, year)
        if f is None:
            print("  sidecars/actuals unavailable")
        else:
            print(f.round(2).to_string())

    print("\n" + "=" * 100)
    print("### E. MEASURED RT (SCED TPO) coal supply, probe-day families")
    print("=" * 100)
    for label, name in _SCED_FILES:
        s = rt_supply(_RAW_DIR / name, frozenset({"CLLIG"}))
        if s is None:
            print(f"  {label}: unavailable")
            continue
        shares = "  ".join(f"${x:g}:{s[f'le_{x:g}'] / s['hasl']:.2f}" for x in _RT_GRID)
        print(f"  COAL {label}: HASL {s['hasl']:.0f} MW, base point {s['bp']:.0f} MW")
        print(f"       supply share of HASL at <=x: {shares}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
