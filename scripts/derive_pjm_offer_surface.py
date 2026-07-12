"""Derive the MEASURED PJM energy-offer surface (G-22 lever A).

The PJM analogue of ``scripts/derive_neiso_offer_surface.py`` (itself the
ISO-NE analogue of ``derive_dam_offer_hrmults.py --condition-binned``): from
PJM's public DataMiner2 ``energy_market_offers`` feed
(``data/raw/pjm-energy-offers/``, ``scripts/fetch_pjm_energy_offers.py``),
measure the CC-like and fast-start CT-like fleets' TOP-OF-CURVE offer
distributions, condition-binned by a forward-reproducible tightness driver,
and freeze them into a condbinned JSON the P1-only markup mechanism reads
(``ScenarioConfig.pjm_offer_surface_conditional``).

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/21)
--------------------------------------------------------------------
1. Population: per (unit_code x operating-hour) offer rows with
   ``avg_ecomax`` > 0. Segments are selected by unit PHYSICS, never fuel
   labels (docs/handoffs/pjm-summer-peak-price-formation-g22-2026-07.md §2):

   * ``CT_PEAKER``  <- fast-start units, per-unit median ``min_runtime`` <= 2 h
     (PJM's fast-start eligibility concept: the whole unit is deliverable
     within a short start + minimum-run commitment).
   * ``CC_REGULAR`` <- mid-runtime block-loaded units, median ``min_runtime``
     in (2, 16] h AND median ``avg_ecomin/avg_ecomax`` > 0.2 (a CC's
     min-stable block is a large share of its capability; the >16 h tail is
     the long-run coal/ST-like segment, deliberately excluded).
   * Excluded from both: $0-top resources (per-unit median top-of-curve
     < $1/MWh — hydro / pumped storage / storage / renewables posting zero)
     and nuclear-like baseload (median ecomin/ecomax >= 0.95 AND median
     EcoMax >= 800 MW — self-scheduled near-inflexible blocks).

   Segment MW totals are validated against the model's PJM fleet classes and
   recorded in the provenance block.
2. Per unit-hour, the TOP-OF-CURVE offer price = the highest-priced offer
   breakpoint (``bid1..bid20``). The heat-rate multiplier basis mirrors the
   ERCOT/NEISO derives::

       mult = (top_price / fuel_price_day) / base_HR(class)

   ``fuel_price_day`` is the model's OWN PJM delivered-gas day series (Henry
   Hub daily spot, ``data.fuel.HENRY_HUB_DAILY_PATH``, forward-filled, plus
   the PJM delivered basis ``constants.GAS_BASIS_DIFFERENTIAL['PJM']``), and
   ``base_HR`` is the cap-weighted class base heat rate from the model's OWN
   PJM plant-level fleet build (the keeper recipe's fleet — the same HR the
   mechanism later multiplies, so the multiplier round-trips: the peak-rung
   row's HR is ``base_HR_plant x resolved_peak`` and the mechanism reprices
   it by ``mult / resolved_peak``).
3. Tightness driver: system net load (EIA-930 PJM ``Demand − NG:WND −
   NG:SUN``), percentile-ranked within each year — the identical
   forward-native construction the mechanism applies at solve time (a
   forecast year's own load/VRE forecast regenerates it).
4. Ladder: within each net-load bin (edges default 0.80/0.90/0.97 — the
   ERCOT/NEISO precedent), each unit contributes its own MEDIAN top-of-curve
   multiplier (so a frequently-offering unit cannot dominate), then units
   are capacity-weighted (median EcoMax) into 5 equal-capacity quantile
   rungs (cap shares 0.2). Rungs are clamped below by the class's all-hours
   p50 (a loose bin never lowers an offer below the body). PJM's $1,000 soft
   / $2,000 hard energy offer cap is already IN the measured offers; no
   synthetic cap is imposed here.
5. Output: ``data/raw/_validation-source/pjm_offer_surface_condbinned.json``
   (the exact ``offer_curve_dam_hrmults_condbinned.json`` schema, CC_REGULAR
   + CT_PEAKER entries) + a per-bin summary CSV next to it, with full
   provenance (edges, month coverage, segment MW validation).

Pre-committed honesty gate (G-22 §5 discipline): these parameters are frozen
against residuals (rule 20 — they re-derive only when the source data
updates); if the A/B degrades the backcast the surface does NOT move and the
probe registers as REJECTED; measured OFFER prices are the input — clearing
prices stay validation-only (rule 13). The raw offer files are gitignored
(PJM DataMiner2 non-member redistribution restriction): only this derived
multiplier JSON — never prices — is committable.

Usage:
    python scripts/derive_pjm_offer_surface.py [--years 2023 2024 2025]
        [--edges 0.80 0.90 0.97] [--rungs 5]
        [--fleet-bundle results/calibration/pjm98_cc_mustrun]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

RAW_DIR = REPO / "data" / "raw" / "pjm-energy-offers"
OUT_JSON = (
    REPO / "data" / "raw" / "_validation-source" / "pjm_offer_surface_condbinned.json"
)
OUT_CSV = REPO / "data" / "raw" / "_validation-source" / "pjm_offer_surface_summary.csv"

#: Fast-start selection: per-unit median min_runtime at or under this (hours).
#: Physics, not a tuned value (the G-22 §2 segmentation).
FAST_START_MAX_MIN_RUNTIME_H = 2.0
#: CC-like selection: median min_runtime in (FAST_START, this] hours ...
CC_MAX_MIN_RUNTIME_H = 16.0
#: ... AND median ecomin/ecomax above this (a CC's min-stable block share).
CC_MIN_ECOMIN_RATIO = 0.2
#: Nuclear-like exclusion: median ecomin/ecomax >= ratio AND EcoMax >= MW.
NUCLEAR_ECOMIN_RATIO = 0.95
NUCLEAR_MIN_ECOMAX_MW = 800.0
#: $0-top exclusion: per-unit median top-of-curve below this ($/MWh) is a
#: hydro/PS/storage/renewable zero-offer resource, not a priced thermal unit.
ZERO_TOP_FLOOR_USD = 1.0

_BID_COLS = [f"bid{i}" for i in range(1, 21)]
_MW_COLS = [f"mw{i}" for i in range(1, 21)]


def _pjm_fuel_daily() -> pd.Series:
    """The model's PJM delivered-gas day series (HH daily + PJM basis).

    Mirrors the model-side convention (``data.fuel``): Henry Hub daily spot,
    forward-filled between publication days, plus the PJM annual delivered
    basis ``GAS_BASIS_DIFFERENTIAL['PJM']`` (EIA-923 delivered-gas basis).
    """
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    df = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = df.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    return s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])


def _class_base_hr(bundle: Path, year: int) -> dict[str, dict[str, float]]:
    """Cap-weighted class base heat rates + class MW from the model's fleet.

    Rebuilds the PJM plant-level fleet through the keeper recipe
    (``run_year(fleet_only=True)`` off the bundle's ``meta.json`` — the
    ``_g22_idle_supply_audit`` pattern) and recovers each class's per-plant
    base HR from its peak-tranche row (``heat_rate == base_HR x
    resolved_peak``), so the divided-by HR here is exactly the HR the P1
    mechanism later multiplies (the round-trip convention).
    """
    from derive_pjm_ordc_overlay import _run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        meta["gas_prices"][str(year)],
        **_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    curves = state["config"].offer_curve_by_group or {}
    uids = np.asarray(fa.unit_ids, dtype=object)
    grp = np.asarray(fa.plant_group, dtype=object)
    out: dict[str, dict[str, float]] = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        pk = float(curves.get(cls, {}).get("peak", 0.0))
        if pk <= 0.0:
            raise SystemExit(f"{cls}: no resolved peak multiplier in the fleet config")
        cls_rows = grp == cls
        # Peak-tranche rows carry base_HR x pk; suffix 'peak' (single flat
        # band — the ladder split is a solve-time no-op not present here).
        peak_rows = cls_rows & np.array(
            [str(u).rpartition("_")[2].startswith("peak") for u in uids]
        )
        if not peak_rows.any():
            raise SystemExit(f"{cls}: no peak-tranche rows in the PJM fleet build")
        base_hr = fa.heat_rate[peak_rows] / pk
        w = fa.pmax[peak_rows]
        out[cls] = {
            "base_hr": float(np.average(base_hr, weights=w)),
            "resolved_peak": pk,
            "class_mw": float(fa.pmax[cls_rows].sum()),
            "n_plants": int(peak_rows.sum()),
        }
    return out


def _netload_pct(years: list[int]) -> pd.DataFrame:
    """(local day, hour-ending) -> within-year net-load percentile (PJM)."""
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    frames = []
    for year in years:
        # The PJM extract is missing a handful of hours (first local hour +
        # the 2023 fall-back day), so use the gap-bridging frame and
        # interpolate the NaN rows — a percentile rank is insensitive to a
        # few interpolated hours.
        df = _eia_hourly_frame_filled("PJM", year)
        if df is None:
            raise SystemExit(f"EIA-930 PJM {year}: no clean 8760 frame")
        net = (
            pd.to_numeric(df["Demand"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: WND"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: SUN"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
        )
        q = pd.Series(net).rank(pct=True).to_numpy()
        local = pd.DatetimeIndex(df["Local time"])
        frames.append(
            pd.DataFrame(
                {
                    "day": local.normalize(),
                    "he": local.hour + 1,  # hour-ending label basis
                    "q": q,
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    # DST fall-back repeats (day, he) — keep the mean percentile for the join.
    return out.groupby(["day", "he"], as_index=False).agg(q=("q", "mean"))


def _month_files(years: list[int]) -> tuple[list[Path], dict]:
    files, coverage = [], {}
    for year in years:
        present = sorted(RAW_DIR.glob(f"pjm_energy_offers_{year:04d}_*.parquet"))
        coverage[year] = {"months_expected": 12, "files": len(present)}
        missing = sorted(
            {f"{m:02d}" for m in range(1, 13)}
            - {p.stem.rpartition("_")[2] for p in present}
        )
        if missing:
            raise SystemExit(
                f"{year}: missing raw offer month(s) {missing}; run "
                "scripts/fetch_pjm_energy_offers.py first"
            )
        files.extend(present)
    return files, coverage


def _parse_month(
    path: Path, nl: pd.DataFrame, fuel: pd.Series, unit_ids: dict[str, int]
) -> pd.DataFrame | None:
    """One month's slim per-row frame: (uid, bin q, mult, physics columns)."""
    cols = (
        ["bid_datetime_beginning_ept", "unit_code", "min_runtime"]
        + ["avg_ecomin", "avg_ecomax"]
        + _BID_COLS
        + _MW_COLS
    )
    df = pd.read_parquet(path, columns=cols)
    df = df[df["avg_ecomax"] > 0.0]
    if df.empty:
        return None
    bids = df[_BID_COLS].to_numpy(dtype=float)
    mws = df[_MW_COLS].to_numpy(dtype=float)
    has_curve = np.isfinite(bids).any(axis=1) & (np.nan_to_num(mws) > 0.0).any(axis=1)
    df = df[has_curve]
    if df.empty:
        return None
    top = np.nanmax(df[_BID_COLS].to_numpy(dtype=float), axis=1)

    # DataMiner2 EPT timestamps ("1/1/2023 12:00:00 AM"); only ~744 unique
    # values per month, so the cached parse is effectively free.
    ts = pd.to_datetime(
        df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
    )
    day = ts.dt.normalize()
    out = pd.DataFrame(
        {
            "day": day.to_numpy(),
            "he": (ts.dt.hour + 1).astype("int8").to_numpy(),
            "unit": df["unit_code"].astype(str).to_numpy(),
            "top": top.astype("float32"),
            "ecomax": df["avg_ecomax"].astype("float32").to_numpy(),
            "ratio": (df["avg_ecomin"] / df["avg_ecomax"]).astype("float32").to_numpy(),
            "mr": df["min_runtime"].astype("float32").to_numpy(),
        }
    )
    out["fuel"] = fuel.reindex(pd.DatetimeIndex(out["day"])).to_numpy(dtype="float32")
    out = out.merge(nl, on=["day", "he"], how="left")
    for u in out["unit"].unique():
        unit_ids.setdefault(u, len(unit_ids))
    out["uid"] = out["unit"].map(unit_ids).astype("int32")
    return out.drop(columns=["day", "he", "unit"])


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    ap.add_argument("--rungs", type=int, default=5)
    ap.add_argument(
        "--fleet-bundle",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm98_cc_mustrun",
        help="keeper bundle whose recipe supplies the model fleet for the "
        "base-HR round-trip basis (meta.json replay, fleet_only)",
    )
    ap.add_argument(
        "--fleet-year",
        type=int,
        default=2024,
        help="fleet vintage year for the base-HR basis (middle train year)",
    )
    args = ap.parse_args(argv)

    files, coverage = _month_files(args.years)
    print(f"model fleet base-HR basis: {args.fleet_bundle} ({args.fleet_year}) ...")
    basis = _class_base_hr(args.fleet_bundle, args.fleet_year)
    for cls, b in basis.items():
        print(
            f"  {cls}: base_HR {b['base_hr']:.3f} MMBtu/MWh (cap-weighted, "
            f"{b['n_plants']} plants, {b['class_mw'] / 1e3:.1f} GW), "
            f"resolved peak x{b['resolved_peak']:.1f}"
        )

    nl = _netload_pct(args.years)
    fuel = _pjm_fuel_daily()
    unit_ids: dict[str, int] = {}
    parts = []
    print(f"parsing {len(files)} month files ...", flush=True)
    for p in files:
        part = _parse_month(p, nl, fuel, unit_ids)
        if part is not None:
            parts.append(part)
        print(f"  {p.name}: {0 if part is None else len(part)} rows", flush=True)
    offers = pd.concat(parts, ignore_index=True)
    del parts
    n_unmatched = int(offers["q"].isna().sum())
    offers = offers.dropna(subset=["q"])
    offers = offers[offers["fuel"] > 0.0]
    print(
        f"offer rows: {len(offers)} ({len(unit_ids)} units, "
        f"{n_unmatched} net-load-unmatched dropped)",
        flush=True,
    )

    # Unit-level physics (medians across every offered hour) -> segments.
    per_unit = offers.groupby("uid").agg(
        top_med=("top", "median"),
        ecomax=("ecomax", "median"),
        ratio=("ratio", "median"),
        mr=("mr", "median"),
    )
    nuclear_like = (per_unit["ratio"] >= NUCLEAR_ECOMIN_RATIO) & (
        per_unit["ecomax"] >= NUCLEAR_MIN_ECOMAX_MW
    )
    zero_top = per_unit["top_med"] < ZERO_TOP_FLOOR_USD
    seg_ct = (
        (per_unit["mr"] <= FAST_START_MAX_MIN_RUNTIME_H) & ~nuclear_like & ~zero_top
    )
    seg_cc = (
        (per_unit["mr"] > FAST_START_MAX_MIN_RUNTIME_H)
        & (per_unit["mr"] <= CC_MAX_MIN_RUNTIME_H)
        & (per_unit["ratio"] > CC_MIN_ECOMIN_RATIO)
        & ~nuclear_like
        & ~zero_top
    )
    segments = {"CT_PEAKER": seg_ct, "CC_REGULAR": seg_cc}

    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    offers["bin"] = np.searchsorted(
        np.asarray(edges), offers["q"].to_numpy(), side="right"
    ).astype("int8")

    # Hour counts per net-load bin across the derive span (for the per-hour
    # offered-MW validation below: total offered rows are unit-hours, so the
    # honest comparison against the model's class MW is MW per HOUR, not the
    # multi-year union of ever-offering units).
    nl_bin = np.searchsorted(np.asarray(edges), nl["q"].to_numpy(), side="right")
    hours_per_bin = np.bincount(nl_bin, minlength=n_bins).astype(float)

    seg_validation = {}
    for cls, mask in segments.items():
        seg_uids = per_unit.index[mask]
        seg_rows = offers[offers["uid"].isin(seg_uids)]
        model_mw = basis[cls]["class_mw"]
        # Mean simultaneous offered MW: all hours, and in the tightest bin —
        # the per-hour footprint the ladder actually represents.
        per_hour_mw = float(seg_rows["ecomax"].sum() / hours_per_bin.sum())
        top_bin_mw = float(
            seg_rows.loc[seg_rows["bin"] == n_bins - 1, "ecomax"].sum()
            / hours_per_bin[n_bins - 1]
        )
        seg_validation[cls] = {
            "n_units": int(mask.sum()),
            "union_mw_all_units": round(float(per_unit.loc[mask, "ecomax"].sum()), 0),
            "offered_mw_per_hour_mean": round(per_hour_mw, 0),
            "offered_mw_per_hour_top_bin": round(top_bin_mw, 0),
            "model_class_mw": round(model_mw, 0),
            "mw_ratio_top_bin_over_model": round(top_bin_mw / model_mw, 3),
        }
        print(
            f"  segment {cls}: {int(mask.sum())} units; offered "
            f"{per_hour_mw / 1e3:.1f} GW/h mean, {top_bin_mw / 1e3:.1f} GW/h in "
            f"the top bin, vs model class {model_mw / 1e3:.1f} GW "
            f"(top-bin x{top_bin_mw / model_mw:.2f})"
        )

    cap_share = 1.0 / args.rungs
    qs = [(i + 0.5) * cap_share for i in range(args.rungs)]
    out: dict = {}
    summary_rows = []
    for cls, mask in segments.items():
        seg_uids = per_unit.index[mask]
        sub_all = offers[offers["uid"].isin(seg_uids)].copy()
        base_hr = basis[cls]["base_hr"]
        sub_all["mult"] = (sub_all["top"] / sub_all["fuel"]) / base_hr

        # all-hours class p50 (per-unit median, cap-weighted): the ladder floor.
        pa = sub_all.groupby("uid").agg(m=("mult", "median"), cap=("ecomax", "median"))
        body_p50 = _wquantile(pa["m"].to_numpy(), pa["cap"].to_numpy(), 0.50)

        binned_ladder = []
        for b in range(n_bins):
            pab = (
                sub_all[sub_all["bin"] == b]
                .groupby("uid")
                .agg(m=("mult", "median"), cap=("ecomax", "median"))
            )
            if len(pab) < 5:  # degenerate bin: hold the body
                ladder = [[cap_share, round(body_p50, 3)] for _ in qs]
            else:
                v, w = pab["m"].to_numpy(), pab["cap"].to_numpy()
                ladder = [
                    [cap_share, max(round(body_p50, 3), round(_wquantile(v, w, q), 3))]
                    for q in qs
                ]
            binned_ladder.append(ladder)
            summary_rows.append(
                {
                    "class": cls,
                    "bin": b,
                    "n_units": len(pab),
                    "n_rows": int((sub_all["bin"] == b).sum()),
                    **{f"rung{i + 1}_mult": ladder[i][1] for i in range(args.rungs)},
                    **{
                        f"rung{i + 1}_usd_at_gas3": round(
                            ladder[i][1] * base_hr * 3.0, 1
                        )
                        for i in range(args.rungs)
                    },
                }
            )
        out[cls] = {
            "base_hr": round(base_hr, 3),
            "peak_p50": round(body_p50, 3),
            "binned_ladder": binned_ladder,
        }

    out_doc = {
        "_provenance": {
            "source": (
                "PJM DataMiner2 energy_market_offers feed (monthly raw "
                f"parquets, data/raw/pjm-energy-offers/), delivery years "
                f"{args.years}"
            ),
            "method": (
                "per-unit median top-of-curve heat-rate multiplier by "
                "physics-selected segment (fast-start CT-like: median "
                f"min_runtime <= {FAST_START_MAX_MIN_RUNTIME_H} h; CC-like: "
                f"min_runtime in ({FAST_START_MAX_MIN_RUNTIME_H}, "
                f"{CC_MAX_MIN_RUNTIME_H}] h and ecomin/ecomax > "
                f"{CC_MIN_ECOMIN_RATIO}; excl. $0-top and nuclear-like), "
                "capacity-weighted equal-capacity quantile rungs within "
                "net-load-percentile bins; rungs clamped >= all-hours p50; "
                "fuel = Henry Hub daily + PJM delivered basis (model "
                "series), base_HR = model PJM plant-level fleet cap-weighted "
                "(peak-tranche HR / resolved peak — round-trip basis)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 PJM Demand "
                "- WND - SUN), forward-native"
            ),
            "netload_pct_edges": list(edges),
            "peak_ladder_qs": qs,
            "fleet_basis": {
                "bundle": str(args.fleet_bundle),
                "year": args.fleet_year,
                **{
                    cls: {k: round(v, 3) for k, v in b.items()}
                    for cls, b in basis.items()
                },
            },
            "segment_validation": seg_validation,
            "month_coverage": coverage,
            "n_month_files_parsed": len(files),
            "n_rows_unmatched_netload": n_unmatched,
        },
        **out,
    }
    OUT_JSON.write_text(json.dumps(out_doc, indent=1))
    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    print(pd.DataFrame(summary_rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
