"""caiso-154 — is the caiso-153 OLS-attenuation failure mode LIVE in PJM/NEISO?

Adjudicates the FINDING-caiso153 §H cross-ISO flag under
``PREREG-caiso154-xiso-ols-attenuation-2026-08-02.md``. No LP on any branch.

L0 (disclosed in the prereg): neither ``derive_pjm_offer_surface.py``,
``derive_pjm_offer_midcurve.py`` nor ``derive_neiso_offer_surface.py``
contains a regression estimator — all three are per-unit median-of-ratio
ladders with PHYSICS segmentation, so the caiso-153 family (per-resource
daily bid-on-fuel regression, pooled-OLS slope consumed as a marginal heat
rate) is structurally absent and L1 is false ex ante. What this probe
measures:

* ``m2``  — the counterfactual classifier grid (PREREG §4 M2): 4 body probes
  (P035/BAND/P060 — the caiso-153 axis — plus TOP, the statistic these ISOs'
  shipped derives actually consume) x 3 estimators (OLS/TS/TRIM), on the
  ISO's own corpus and its own fuel series, REUSING the caiso-153 core
  (``_fit`` / ``_score_resources``) and the CAISO derive's family constants.
  Descriptive only: no winner, no selection rule, nothing derived from it.
* ``m34`` — the shipped-estimator arms (PREREG §4 M3/M4): run each shipped
  deriver's own ``main()`` with outputs REDIRECTED (consumed artifacts are
  never rewritten), the fleet basis INJECTED from the committed artifact's
  provenance (the recorded bundles/caches are absent in this container), and
  — for the ``tailx`` arm — the top-1%-of-2023-25-fuel-price days masked out
  of the fuel series (NaN days drop at the derives' own ``fuel > 0`` filter).
* ``compare`` — the M3/M4 verdicts at the PREREG-fixed tolerances
  (reproduced-after-rounding / <=2 % noise / >10 % defect-class).

Usage::

    python scripts/probes/_caiso154_ols_attenuation_xiso.py m2 --iso NEISO
    python scripts/probes/_caiso154_ols_attenuation_xiso.py m2 --iso PJM
    python scripts/probes/_caiso154_ols_attenuation_xiso.py m34 --iso PJM \\
        --artifact top --arm baseline
    python scripts/probes/_caiso154_ols_attenuation_xiso.py compare
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

OUT_ROOT = REPO / "results" / "calibration"
ARMS_ROOT = OUT_ROOT / "caiso154_arms"

#: The caiso-153 grid axes, + TOP (the statistic the PJM/NEISO derives consume).
BODY_PROBES = ("P035", "BAND", "P060", "TOP")
SLOPE_ESTIMATORS = ("OLS", "TS", "TRIM")
BAND_WINDOW = (0.35, 0.85)

#: Committed artifacts (comparison targets; NEVER written by this probe).
COMMITTED = {
    ("PJM", "top"): REPO
    / "data/raw/_validation-source/pjm_offer_surface_condbinned.json",
    ("PJM", "midcurve"): REPO
    / "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json",
    ("NEISO", "top"): REPO
    / "data/raw/_validation-source/neiso_offer_surface_condbinned.json",
}


# --------------------------------------------------------------------------- #
# fuel series + tail-day sets (PREREG §3/§4: the exact series the derives use)
# --------------------------------------------------------------------------- #
def _fuel_series(iso: str):
    """The shipped derive's own daily fuel series for ``iso``."""
    if iso == "PJM":
        from derive_pjm_offer_surface import _pjm_fuel_daily

        return _pjm_fuel_daily()
    if iso == "NEISO":
        from derive_neiso_offer_surface import _load_algonquin_daily

        return _load_algonquin_daily()
    raise ValueError(iso)


def _tail_days(iso: str):
    """The top ceil(1 %) of 2023-25 days by fuel level (ties included)."""
    import numpy as np

    s = _fuel_series(iso).loc["2023-01-01":"2025-12-31"].dropna()
    v = s.to_numpy(float)
    n1 = max(1, int(np.ceil(0.01 * len(v))))
    thresh = float(np.sort(v)[::-1][n1 - 1])
    days = set(s.index[v >= thresh].normalize())
    return days, thresh


# --------------------------------------------------------------------------- #
# body-probe math on a wide cumulative curve (rows x k breakpoints)
# --------------------------------------------------------------------------- #
def _probe_stats(bids, cums, cap):
    """Per-row P035/BAND/P060/TOP from cumulative-MW offer curves.

    ``bids``/``cums``: (n, k) float arrays — step prices and CUMULATIVE MW
    breakpoints (NaN-padded); ``cap``: (n,) fraction basis. P-at-frac reads
    the first step whose cumulative MW covers ``frac x cap`` (falling back to
    the last valid step when the curve stops short — the curve's top). BAND
    is the capacity-weighted mean step price over ``BAND_WINDOW x cap``
    (NaN when the curve never overlaps the window).
    """
    import numpy as np

    valid = np.isfinite(bids) & np.isfinite(cums)
    any_v = valid.any(axis=1)
    n, k = bids.shape
    ar = np.arange(n)
    last_v = np.where(any_v, k - 1 - np.argmax(valid[:, ::-1], axis=1), 0)

    top = np.where(any_v, np.nanmax(np.where(valid, bids, -np.inf), axis=1), np.nan)

    out = {"TOP": top}
    cums_v = np.where(valid, cums, -np.inf)
    for name, frac in (("P035", 0.35), ("P060", 0.60)):
        target = frac * cap
        covered = cums_v >= target[:, None]
        first = np.argmax(covered, axis=1)
        idx = np.where(covered.any(axis=1), first, last_v)
        p = bids[ar, idx]
        out[name] = np.where(any_v, p, np.nan)

    lo, hi = BAND_WINDOW[0] * cap, BAND_WINDOW[1] * cap
    prev = np.concatenate([np.zeros((n, 1)), np.where(valid, cums, np.nan)], axis=1)
    prev = np.asarray(
        __import__("pandas").DataFrame(prev).ffill(axis=1).to_numpy()[:, :-1]
    )
    seg_lo = np.maximum(prev, lo[:, None])
    seg_hi = np.minimum(np.where(valid, cums, -np.inf), hi[:, None])
    ov = np.clip(seg_hi - seg_lo, 0.0, None)
    ov = np.where(valid, ov, 0.0)
    wsum = ov.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        band = np.where(
            wsum > 0, np.nansum(np.where(valid, bids, 0.0) * ov, axis=1) / wsum, np.nan
        )
    out["BAND"] = band
    return out


# --------------------------------------------------------------------------- #
# per-ISO corpus adapters -> per-(resource, day) probe frames + physics
# --------------------------------------------------------------------------- #
def _pjm_daily(months_limit: int | None = None):
    """PJM: per (unit, EPT day) median probe prices + day-level physics."""
    import numpy as np
    import pandas as pd

    from derive_pjm_offer_surface import _BID_COLS, _month_files, _MW_COLS

    files, coverage = _month_files([2023, 2024, 2025])
    if months_limit:
        files = files[:months_limit]
    unit_ids: dict[str, int] = {}
    probe_parts, phys_parts = [], []
    for p in files:
        df = pd.read_parquet(
            p,
            columns=[
                "bid_datetime_beginning_ept",
                "unit_code",
                "min_runtime",
                "avg_ecomin",
                "avg_ecomax",
            ]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        if df.empty:
            continue
        bids = df[_BID_COLS].to_numpy(float)
        mws = df[_MW_COLS].to_numpy(float)
        has_curve = np.isfinite(bids).any(axis=1) & (np.nan_to_num(mws) > 0.0).any(
            axis=1
        )
        df = df[has_curve]
        bids, mws = bids[has_curve], mws[has_curve]
        if df.empty:
            continue
        cap = df["avg_ecomax"].to_numpy(float)
        stats = _probe_stats(bids, mws, cap)  # PJM mw cols are cumulative
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        day = ts.dt.normalize().to_numpy()
        for u in df["unit_code"].astype(str).unique():
            unit_ids.setdefault(u, len(unit_ids))
        uid = df["unit_code"].astype(str).map(unit_ids).to_numpy("int32")
        base = pd.DataFrame({"resource_seq": uid, "day": day})
        probe_parts.append(
            base.assign(**{k.lower(): v.astype("float32") for k, v in stats.items()})
            .groupby(["resource_seq", "day"], as_index=False)
            .median()
        )
        phys_parts.append(
            base.assign(
                mr=df["min_runtime"].to_numpy("float32"),
                ratio=(df["avg_ecomin"] / df["avg_ecomax"]).to_numpy("float32"),
                ecomax=df["avg_ecomax"].to_numpy("float32"),
                topp=stats["TOP"].astype("float32"),
            )
            .groupby(["resource_seq", "day"], as_index=False)
            .median()
        )
        print(f"  {p.name}: {len(df)} rows", flush=True)
    daily = pd.concat(probe_parts, ignore_index=True)
    phys = (
        pd.concat(phys_parts, ignore_index=True)
        .groupby("resource_seq")
        .median(numeric_only=True)
    )
    return daily, phys, coverage, unit_ids


def _pjm_physics_segments(phys):
    """The shipped pjm-99 physics segmentation, unit-level (confusion basis)."""
    from derive_pjm_offer_surface import (
        CC_MAX_MIN_RUNTIME_H,
        CC_MIN_ECOMIN_RATIO,
        FAST_START_MAX_MIN_RUNTIME_H,
        NUCLEAR_ECOMIN_RATIO,
        NUCLEAR_MIN_ECOMAX_MW,
        ZERO_TOP_FLOOR_USD,
    )

    nuclear_like = (phys["ratio"] >= NUCLEAR_ECOMIN_RATIO) & (
        phys["ecomax"] >= NUCLEAR_MIN_ECOMAX_MW
    )
    zero_top = phys["topp"] < ZERO_TOP_FLOOR_USD
    lab = phys["mr"].map(lambda _: "OTHER")
    lab[(phys["mr"] <= FAST_START_MAX_MIN_RUNTIME_H)] = "CT_FAST"
    lab[
        (phys["mr"] > FAST_START_MAX_MIN_RUNTIME_H)
        & (phys["mr"] <= CC_MAX_MIN_RUNTIME_H)
        & (phys["ratio"] > CC_MIN_ECOMIN_RATIO)
    ] = "CC_LIKE"
    lab[(phys["mr"] > CC_MAX_MIN_RUNTIME_H)] = "LONG_RUN"
    lab[nuclear_like | zero_top] = "EXCLUDED"
    return lab


def _neiso_daily():
    """NEISO: per (asset, day) median probe prices + physics.

    Segment MW columns are INCREMENTAL block sizes (measured on the corpus:
    per-row sum/EcoMax p50 = 1.000, monotone in only ~15 % of multi-segment
    rows), so the cumulative curve is their cumsum. The fraction basis is
    EcoMax (the shipped cap convention); rows whose blocks sum past EcoMax
    are counted and reported (``n_over_ecomax``).
    """
    import numpy as np
    import pandas as pd

    from derive_neiso_offer_surface import _day_files, FAST_START_CLAIM30_FRAC

    files, coverage = _day_files([2023, 2024, 2025])
    rows = []
    n_over = 0
    for path in files:
        with path.open(newline="") as fh:
            for r in csv.reader(fh):
                if not r or r[0] != "D":
                    continue
                try:
                    emax = float(r[7] or 0.0)
                    claim30 = float(r[34] or 0.0)
                except (ValueError, IndexError):
                    continue
                status = r[35].strip() if len(r) > 35 else ""
                if emax <= 0.0 or status not in ("ECONOMIC", "MUST_RUN"):
                    continue
                prices, sizes = [], []
                for k in range(13, 33, 2):
                    pv = r[k] if k < len(r) else ""
                    mv = r[k + 1] if k + 1 < len(r) else ""
                    if pv not in ("", None) and mv not in ("", None):
                        prices.append(float(pv))
                        sizes.append(float(mv))
                if not prices:
                    continue
                cum = np.cumsum(sizes)
                if cum[-1] > 1.5 * emax:
                    n_over += 1
                rows.append(
                    (r[1], int(r[4]), emax, claim30 / emax, tuple(prices), tuple(cum))
                )
    df = pd.DataFrame(
        rows, columns=["day", "asset_id", "ecomax", "c30r", "prices", "cums"]
    )
    df["day"] = pd.to_datetime(df["day"], format="%m/%d/%Y")
    kmax = max(len(p) for p in df["prices"])
    bids = np.full((len(df), kmax), np.nan)
    cums = np.full((len(df), kmax), np.nan)
    for i, (p, c) in enumerate(zip(df["prices"], df["cums"])):
        bids[i, : len(p)] = p
        cums[i, : len(p)] = c
    stats = _probe_stats(bids, cums, df["ecomax"].to_numpy(float))
    base = df[["asset_id", "day"]].rename(columns={"asset_id": "resource_seq"})
    daily = (
        base.assign(**{k.lower(): v.astype("float32") for k, v in stats.items()})
        .groupby(["resource_seq", "day"], as_index=False)
        .median()
    )
    phys = (
        base.assign(
            ecomax=df["ecomax"].to_numpy("float32"), c30r=df["c30r"].to_numpy("float32")
        )
        .groupby("resource_seq")
        .median(numeric_only=True)
    )
    phys["fast_start"] = phys["c30r"] >= FAST_START_CLAIM30_FRAC
    print(
        f"  {len(files)} day files, {len(df)} offer rows, "
        f"{daily.resource_seq.nunique()} assets, {n_over} rows over 1.5x EcoMax",
        flush=True,
    )
    return daily, phys, coverage, n_over


# --------------------------------------------------------------------------- #
# m2 — the counterfactual grid
# --------------------------------------------------------------------------- #
def cmd_m2(args: argparse.Namespace) -> int:
    """Score the 4x3 counterfactual grid on one ISO's own corpus + fuel."""
    import numpy as np
    import pandas as pd

    import derive_caiso_offer_surface as D
    from scripts.probes._caiso153_offer_classifier_reid import _score_resources

    iso = args.iso
    fuel = _fuel_series(iso)
    fuel = fuel[fuel.index <= pd.Timestamp("2025-12-31")]

    print(f"building {iso} per-(resource, day) probe frames ...", flush=True)
    if iso == "PJM":
        daily, phys, coverage, _ = _pjm_daily(args.months_limit)
        phys_label = _pjm_physics_segments(phys)
        cap = phys["ecomax"]
    else:
        daily, phys, coverage, n_over = _neiso_daily()
        phys_label = phys["fast_start"].map({True: "FAST_START", False: "OTHER"})
        cap = phys["ecomax"]

    keep = cap[cap >= D.MIN_CAP_MW].index
    daily = daily[daily.resource_seq.isin(keep)]
    print(
        f"  {len(daily):,} resource-days, {len(keep)} resources at cap >= "
        f"{D.MIN_CAP_MW} MW",
        flush=True,
    )

    gas_map = fuel.dropna()
    grid: dict[str, dict] = {}
    frames = []
    for probe in BODY_PROBES:
        bd = daily[["resource_seq", "day", probe.lower()]].rename(
            columns={probe.lower(): "p_body"}
        )
        bd = bd.dropna(subset=["p_body"])
        bd["gas"] = bd.day.map(gas_map)
        bd = bd.dropna(subset=["gas"])
        for est in SLOPE_ESTIMATORS:
            name = f"{probe}_{est}"
            # basis = gas only (PREREG §4 M2: the RGGI caveat is declared —
            # carbon is estimator-invariant inside L and left in place).
            try:
                res = _score_resources(bd, gas_map, cap, D, est)
            except KeyError:
                # the caiso-153 core indexes an empty frame when nothing
                # clears GAS_MIN_DAYS — record the cell, don't crash
                grid[name] = {"admissible": None, "note": "no scoreable resource"}
                print(f"{name}: no scoreable resource", flush=True)
                continue
            gl = res[res.is_gas]
            w = gl.cap.to_numpy(float)
            if len(gl) == 0:
                rec = {"admissible": None, "note": "no resource passes the gas gate"}
            else:
                lvl = float(
                    D._wquantile(np.abs(gl.level_adder.to_numpy(float)), w, 0.5)
                )
                ok = np.isfinite(gl.slope_a) & np.isfinite(gl.slope_b)
                half = gl[ok]
                stab = (
                    float(
                        D._wquantile(
                            np.abs(
                                half.slope_a.to_numpy(float)
                                - half.slope_b.to_numpy(float)
                            ),
                            half.cap.to_numpy(float),
                            0.5,
                        )
                    )
                    if len(half)
                    else float("nan")
                )
                lab = phys_label.reindex(gl.index).fillna("OTHER")
                conf = (
                    gl.assign(phys=lab, cls=np.where(gl.slope < 8.5, "CC", "CT"))
                    .groupby(["phys", "cls"])
                    .cap.sum()
                    .round(0)
                )
                rec = {
                    "level_adder_cwmed_abs": round(lvl, 2),
                    "admissible_le_20": bool(lvl <= 20.0),
                    "splithalf_slope_cwmed_abs_dev": round(stab, 3),
                    "n_gas_pass": int(len(gl)),
                    "gas_pass_mw": round(float(gl.cap.sum()), 0),
                    "slope_p25_p50_p75": [
                        round(float(np.percentile(gl.slope, q)), 2)
                        for q in (25, 50, 75)
                    ],
                    "bucket_mw_hrcut_8p5": {
                        "CC_lt_8p5": round(float(gl[gl.slope < 8.5].cap.sum()), 0),
                        "CT_ge_8p5": round(float(gl[gl.slope >= 8.5].cap.sum()), 0),
                    },
                    "impossible_r06_slope_lt4": {
                        "n": int(((res.r >= D.GAS_MIN_R) & (res.slope < 4.0)).sum()),
                        "mw": round(
                            float(
                                res[
                                    (res.r >= D.GAS_MIN_R) & (res.slope < 4.0)
                                ].cap.sum()
                            ),
                            0,
                        ),
                    },
                    "confusion_capMW_phys_x_slopebucket": {
                        f"{p}|{c}": float(v) for (p, c), v in conf.items()
                    },
                }
            grid[name] = rec
            frames.append(res.assign(estimator=name).reset_index())
            print(f"{name}: {json.dumps(rec)[:240]}", flush=True)
        del bd

    out = {
        "iso": iso,
        "prereg": "PREREG-caiso154-xiso-ols-attenuation-2026-08-02.md §4 M2",
        "population": f"all corpus resources, cap >= {D.MIN_CAP_MW} MW",
        "family_constants": {
            "GAS_MIN_DAYS": D.GAS_MIN_DAYS,
            "GAS_MIN_R": D.GAS_MIN_R,
            "GAS_SLOPE_RANGE": list(D.GAS_SLOPE_RANGE),
            "hr_cut": 8.5,
            "level_adder_bar": 20.0,
            "basis": "gas only (RGGI caveat declared in PREREG)",
        },
        "coverage": coverage,
        "grid": grid,
        "note": "DESCRIPTIVE ONLY - no winner, no selection, nothing derived",
    }
    out_path = OUT_ROOT / f"caiso154_grid_{iso}.json"
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    csv_path = OUT_ROOT / f"caiso154_slopes_{iso}.csv"
    __import__("pandas").concat(frames, ignore_index=True).to_csv(csv_path, index=False)
    print(f"-> {out_path}\n-> {csv_path}")
    return 0


# --------------------------------------------------------------------------- #
# m34 — shipped-estimator arms (baseline = M4 reproduction, tailx = M3)
# --------------------------------------------------------------------------- #
def _inject_pjm_fleet_basis(P):
    """Patch the fleet replay with the committed artifact's recorded basis.

    The recorded bundle (``pjm98_cc_mustrun``) is not on disk in this
    container, so the fleet-replay leg is BLOCKED (reported in the finding);
    what the arm tests is corpus + parser + estimator + ladder.
    """
    committed = json.loads(COMMITTED[("PJM", "top")].read_text())
    basis = {
        cls: dict(committed["_provenance"]["fleet_basis"][cls])
        for cls in ("CC_REGULAR", "CT_PEAKER")
    }
    P._class_base_hr = lambda bundle, year: basis


def _mask_fuel(fn, days):
    """Wrap a fuel-series fn: masked days go NaN (drop at the fuel>0 filter)."""

    def _wrapped():
        s = fn()
        s = s.copy()
        s[s.index.normalize().isin(days)] = float("nan")
        return s

    return _wrapped


def cmd_m34(args: argparse.Namespace) -> int:
    """Run one shipped deriver, redirected, on one arm."""
    out_dir = ARMS_ROOT / f"{args.iso}_{args.artifact}_{args.arm}"
    out_dir.mkdir(parents=True, exist_ok=True)
    tail_note = None
    if args.arm == "tailx":
        days, thresh = _tail_days(args.iso)
        tail_note = {
            "n_days": len(days),
            "threshold_usd_mmbtu": round(thresh, 3),
            "days": sorted(str(d.date()) for d in days),
        }
        (out_dir / "tail_days.json").write_text(json.dumps(tail_note, indent=1))
        print(f"tailx: masking {len(days)} days >= ${thresh:.2f}/MMBtu")

    if args.iso == "PJM" and args.artifact == "top":
        import derive_pjm_offer_surface as P

        _inject_pjm_fleet_basis(P)
        P._out_paths = lambda conditioning: (
            out_dir / "pjm_offer_surface_condbinned.json",
            out_dir / "pjm_offer_surface_summary.csv",
        )
        if args.arm == "tailx":
            P._pjm_fuel_daily = _mask_fuel(P._pjm_fuel_daily, days)
        rc = P.main(["--years", "2023", "2024", "2025"])
    elif args.iso == "PJM" and args.artifact == "midcurve":
        import derive_pjm_offer_midcurve as M

        M._out_paths = lambda conditioning: (
            out_dir / "pjm_offer_midcurve_condbinned.json",
            out_dir / "pjm_offer_midcurve_summary.csv",
        )
        if args.arm == "tailx":
            M._pjm_fuel_daily = _mask_fuel(M._pjm_fuel_daily, days)
        rc = M.main(["--years", "2023", "2024", "2025"])
    elif args.iso == "NEISO" and args.artifact == "top":
        import derive_neiso_offer_surface as N

        committed = json.loads(COMMITTED[("NEISO", "top")].read_text())
        base_hr = float(committed["_provenance"]["base_hr_mmbtu_mwh"])
        N._ct_peaker_base_hr = lambda: base_hr
        N.OUT_JSON = out_dir / "neiso_offer_surface_condbinned.json"
        N.OUT_CSV = out_dir / "neiso_offer_surface_summary.csv"
        if args.arm == "tailx":
            N._load_algonquin_daily = _mask_fuel(N._load_algonquin_daily, days)
        rc = N.main(["--years", "2023", "2024", "2025"])
    else:
        raise SystemExit(f"unknown arm target {args.iso}/{args.artifact}")
    print(f"arm {args.iso}/{args.artifact}/{args.arm}: rc={rc} -> {out_dir}")
    return int(rc)


# --------------------------------------------------------------------------- #
# compare — M3/M4 verdicts at the PREREG-fixed tolerances
# --------------------------------------------------------------------------- #
def _numeric_leaves(obj, path=""):
    """Flatten consumed numeric leaves, skipping provenance blocks."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "_provenance":
                continue
            out.update(_numeric_leaves(v, f"{path}/{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_numeric_leaves(v, f"{path}[{i}]"))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[path] = float(obj)
    return out


def _delta_report(a: dict, b: dict, label: str) -> dict:
    """Relative deltas of b vs a over shared numeric leaves."""
    import numpy as np

    la, lb = _numeric_leaves(a), _numeric_leaves(b)
    shared = sorted(set(la) & set(lb))
    rel = {}
    for k in shared:
        va, vb = la[k], lb[k]
        if va == vb:
            rel[k] = 0.0
        elif abs(va) < 1e-9:
            rel[k] = float("inf") if vb != va else 0.0
        else:
            rel[k] = abs(vb - va) / abs(va)
    vals = np.array([v for v in rel.values() if np.isfinite(v)])
    worst = sorted(rel.items(), key=lambda kv: -kv[1])[:8]
    return {
        "comparison": label,
        "n_leaves_shared": len(shared),
        "n_leaves_only_a": len(set(la) - set(lb)),
        "n_leaves_only_b": len(set(lb) - set(la)),
        "identical": bool(len(vals) and (vals == 0).all()),
        "max_rel_delta": round(float(vals.max()), 5) if len(vals) else None,
        "n_gt_2pct": int((vals > 0.02).sum()),
        "n_gt_10pct": int((vals > 0.10).sum()),
        "worst_leaves": [[k, round(v, 4)] for k, v in worst if v > 0],
    }


def cmd_compare(args: argparse.Namespace) -> int:
    """M4 (committed vs baseline) + M3 (tailx vs committed and baseline)."""
    fname = {
        ("PJM", "top"): "pjm_offer_surface_condbinned.json",
        ("PJM", "midcurve"): "pjm_offer_midcurve_condbinned.json",
        ("NEISO", "top"): "neiso_offer_surface_condbinned.json",
    }
    report = {}
    for (iso, art), committed_path in COMMITTED.items():
        committed = json.loads(committed_path.read_text())
        entry: dict = {"committed": str(committed_path)}
        arms = {}
        for arm in ("baseline", "tailx"):
            p = ARMS_ROOT / f"{iso}_{art}_{arm}" / fname[(iso, art)]
            if p.exists():
                arms[arm] = json.loads(p.read_text())
        if "baseline" in arms:
            entry["M4_committed_vs_baseline"] = _delta_report(
                committed, arms["baseline"], "committed -> baseline (repro)"
            )
        if "tailx" in arms:
            entry["M3_committed_vs_tailx"] = _delta_report(
                committed, arms["tailx"], "committed -> tailx"
            )
            if "baseline" in arms:
                entry["M3_baseline_vs_tailx"] = _delta_report(
                    arms["baseline"], arms["tailx"], "baseline -> tailx"
                )
        report[f"{iso}/{art}"] = entry
    out = OUT_ROOT / "caiso154_m34_report.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    print(f"-> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("m2")
    p.add_argument("--iso", required=True, choices=["PJM", "NEISO"])
    p.add_argument("--months-limit", type=int, default=None, help="smoke only")
    p = sub.add_parser("m34")
    p.add_argument("--iso", required=True, choices=["PJM", "NEISO"])
    p.add_argument("--artifact", required=True, choices=["top", "midcurve"])
    p.add_argument("--arm", required=True, choices=["baseline", "tailx"])
    sub.add_parser("compare")
    args = ap.parse_args(argv)
    return {"m2": cmd_m2, "m34": cmd_m34, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
