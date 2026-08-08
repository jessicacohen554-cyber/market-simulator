"""caiso-182 P0-3 — the coverage/contamination census and the two identification tests.

Pre-registered in ``results/calibration/PRECHECK-caiso182-offer-coverage-2026-08-08.md``
§3c, **before** any value existed on this session's re-fetched corpus. Nothing here
chooses a cut, a band or a stratification from a residual: every constant it uses is
either already registered (the class base heat rates, the deriver's frozen classifier
constants) or is the deriver's **own** frozen tolerance.

Three deliverables:

* **CENSUS** — per class and year: MW and resource count the measured surface covers, the
  MW currently mis-bucketed, and the model MW that would newly take a measured rung.
* **IT-2 SEPARABILITY** — does a defensible additional cut exist on the recovered-HR axis?
  A candidate boundary (the midpoint between adjacent registered class base HRs — existing
  constants, not new ones) passes only if the cap-weighted slope density shows an
  **antimode within ±1.0 MMBtu/MWh** of it (the G2 standard the incumbent 8.5 cut had to
  meet) **and** the resulting sub-bucket reconciles inside the registered G1 bounds.
* **IT-1 CONDUCT HOMOGENEITY** — is a bucket's measured band transferable to every model
  class in that bucket? Measured by re-normalising each resource's band multiplier by its
  **own** recovered heat rate instead of the class constant, stratifying into terciles of
  recovered slope, and requiring the tercile spread to sit inside the deriver's own frozen
  G3 tolerance ``max(LOYO_ABS, LOYO_REL)`` = ``max(0.08, 10 %)``.

The instrument REUSES the deriver's own machinery (``_load_bids``, ``_classify``,
``_band_price``, ``_fleet_geometry``, ``_gas_staircase``, ``_wquantile``, and its frozen
constants) rather than re-implementing it, so a divergence between this census and the
shipped derive cannot come from a second implementation.

Usage:
    python scripts/probes/_caiso182_offer_coverage_census.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from scripts.data.derive_caiso_offer_surface import (  # noqa: E402
    CO2_FACTOR,
    ECON_LOW_SHARE,
    GAS_MIN_R,
    LOYO_ABS,
    LOYO_REL,
    MIN_CAP_MW,
    VOM_BY_CLASS,
    _band_price,
    _carbon_price,
    _classify,
    _fleet_geometry,
    _gas_staircase,
    _load_bids,
    _wquantile,
)

OUT = REPO / "results/calibration/_caiso182_offer_coverage_census.json"

#: The measured surface's current membership.
COVERED = ("CC_REGULAR", "CT_PEAKER")
#: The classes running on 100% fitted, ERCOT-inherited multipliers.
UNCOVERED = ("CC_CHP", "CT_CHP", "ST_GAS")
#: Which measured bucket each uncovered class falls into under the shipped
#: hr_cut of 8.5, by its own registered cap-weighted base heat rate.
BUCKET_OF = {"CC_CHP": "CC_REGULAR", "CT_CHP": "CT_PEAKER", "ST_GAS": "CT_PEAKER"}
#: G1 bounds exactly as the deriver registers them.
G1_BOUNDS = {"CC_REGULAR": (0.5, 1.3), "CT_PEAKER": (0.5, 1.6)}
#: PRECHECK §3c: an antimode must lie within this distance of a candidate cut.
IT2_WINDOW_MMBTU = 1.0


def _class_base_hrs() -> dict[str, float]:
    """Cap-weighted Plant_Avg_HR per model class — the registered constants."""
    df = pd.read_csv(PROCESSED_DIR / "bin_assignments_CAISO.csv")
    out = {}
    for cls, d in df.groupby("Plant_Group"):
        w = d.Nameplate_MW.to_numpy(float)
        out[cls] = float((d.Plant_Avg_HR_MMBtu_MWh.to_numpy(float) * w).sum() / w.sum())
    return out


def _fleet_census() -> tuple[dict, pd.DataFrame]:
    df = pd.read_csv(PROCESSED_DIR / "bin_assignments_CAISO.csv")
    total = float(df.Nameplate_MW.sum())
    rows = {}
    for cls, d in df.groupby("Plant_Group"):
        w = d.Nameplate_MW.to_numpy(float)
        rows[cls] = {
            "plants": int(len(d)),
            "nameplate_mw": round(float(w.sum()), 1),
            "share_of_thermal_pct": round(100.0 * w.sum() / total, 2),
            "cap_wt_base_hr": round(
                float((d.Plant_Avg_HR_MMBtu_MWh.to_numpy(float) * w).sum() / w.sum()), 2
            ),
            "measured_surface": (
                "COVERED"
                if cls in COVERED
                else ("UNCOVERED" if cls in UNCOVERED else "n/a")
            ),
        }
    return {"total_thermal_mw": round(total, 1), "by_class": rows}, df


def _candidate_cuts(base_hr: dict[str, float]) -> list[dict]:
    """Midpoints between adjacent registered class base HRs (no new constants)."""
    members = [c for c in (*COVERED, *UNCOVERED) if c in base_hr]
    ordered = sorted(members, key=lambda c: base_hr[c])
    cuts = []
    for lo_cls, hi_cls in zip(ordered, ordered[1:]):
        cuts.append(
            {
                "below": lo_cls,
                "above": hi_cls,
                "below_base_hr": round(base_hr[lo_cls], 3),
                "above_base_hr": round(base_hr[hi_cls], 3),
                "cut": round(0.5 * (base_hr[lo_cls] + base_hr[hi_cls]), 3),
                "separation_mmbtu": round(base_hr[hi_cls] - base_hr[lo_cls], 3),
            }
        )
    return cuts


def _density(slopes: np.ndarray, caps: np.ndarray, lo: float, hi: float, width: float):
    """Cap-weighted histogram of recovered slope on a fixed 0.25 MMBtu/MWh grid.

    0.25 is the deriver's own G2 perturbation step, reused rather than chosen:
    the incumbent cut had to be robust to +/-0.25, so 0.25 is the resolution at
    which a 'valley' is already defined for this axis.
    """
    edges = np.arange(lo, hi + width, width)
    hist, _ = np.histogram(slopes, bins=edges, weights=caps)
    centres = 0.5 * (edges[:-1] + edges[1:])
    return centres, hist


def _is_antimode(centres: np.ndarray, hist: np.ndarray, cut: float, window: float):
    """True iff some bin within +/-window of cut is a strict local minimum."""
    hits = []
    for i in range(1, len(hist) - 1):
        if abs(centres[i] - cut) > window:
            continue
        if hist[i] < hist[i - 1] and hist[i] < hist[i + 1]:
            hits.append(
                {
                    "bin_centre": round(float(centres[i]), 3),
                    "bin_mw": round(float(hist[i]), 1),
                    "left_mw": round(float(hist[i - 1]), 1),
                    "right_mw": round(float(hist[i + 1]), 1),
                    "distance_from_cut": round(float(abs(centres[i] - cut)), 3),
                }
            )
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--hr-cut", type=float, default=8.5)
    args = ap.parse_args(argv)
    years = list(args.years)

    base_hr = _class_base_hrs()
    census, fleet = _fleet_census()
    geom = _fleet_geometry()
    gas = _gas_staircase()

    print("loading clean dam-public-bids ...", flush=True)
    bids = _load_bids(years)
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    bids = bids[bids.cap >= MIN_CAP_MW]
    print(f"  {len(bids):,} rows, {bids.resource_seq.nunique()} resources", flush=True)

    res, _ = _classify(bids, gas, args.hr_cut)
    gaslike = res[res.is_gas].copy()
    print(
        f"  gas-classified: {len(gaslike)} resources, "
        f"{gaslike.cap.sum():,.0f} MW",
        flush=True,
    )

    # ---------------------------------------------------------------- #
    # CENSUS — coverage and the contamination arithmetic                #
    # ---------------------------------------------------------------- #
    buckets = {c: gaslike[gaslike.cls == c] for c in COVERED}
    contamination = {}
    for cls in COVERED:
        members = [cls] + [u for u, b in BUCKET_OF.items() if b == cls]
        combined = sum(census["by_class"][m]["nameplate_mw"] for m in members)
        bucket_mw = float(buckets[cls].cap.sum())
        lo, hi = G1_BOUNDS[cls]
        contamination[cls] = {
            "bucket_resources": int(len(buckets[cls])),
            "bucket_mw": round(bucket_mw, 1),
            "reachable_members": members,
            "fleet_mw_named_class_only": census["by_class"][cls]["nameplate_mw"],
            "fleet_mw_all_reachable": round(combined, 1),
            "ratio_vs_named_class": round(bucket_mw / geom[cls]["fleet_mw"], 3),
            "ratio_vs_all_reachable": round(bucket_mw / combined, 3),
            "g1_bounds": [lo, hi],
        }
    newly_priced_mw = round(
        sum(census["by_class"][u]["nameplate_mw"] for u in UNCOVERED), 1
    )

    # ---------------------------------------------------------------- #
    # IT-2 — SEPARABILITY on the recovered-HR axis                      #
    # ---------------------------------------------------------------- #
    slopes = gaslike.slope.to_numpy(float)
    caps = gaslike.cap.to_numpy(float)
    centres, hist = _density(slopes, caps, 4.0, 18.0, 0.25)
    it2 = {
        "slope_quantiles": {
            q: round(float(np.quantile(slopes, q)), 3)
            for q in (0.05, 0.25, 0.5, 0.75, 0.95)
        },
        "cap_weighted_density_grid_mmbtu": 0.25,
        "density_mw_by_bin": {
            str(round(float(c), 3)): round(float(h), 1)
            for c, h in zip(centres, hist)
            if h > 0
        },
        "candidates": [],
    }
    for cand in _candidate_cuts(base_hr):
        anti = _is_antimode(centres, hist, cand["cut"], IT2_WINDOW_MMBTU)
        cand = {**cand, "antimodes_within_window": anti, "antimode_found": bool(anti)}
        cand["pass"] = bool(anti)
        it2["candidates"].append(cand)
    it2["any_candidate_passes"] = any(c["pass"] for c in it2["candidates"])

    # ---------------------------------------------------------------- #
    # IT-1 — CONDUCT HOMOGENEITY on the own-HR normalisation            #
    # ---------------------------------------------------------------- #
    bids["day"] = (
        bids.interval_start_utc.dt.tz_convert("US/Pacific")
        .dt.normalize()
        .dt.tz_localize(None)
    )
    bids["gas"] = bids.day.map(gas)
    carbon = {y: _carbon_price(y) for y in years}
    tol_note = f"max({LOYO_ABS}, {LOYO_REL:.0%}) — the deriver's own frozen G3 tolerance"

    it1: dict[str, dict] = {"tolerance": tol_note, "buckets": {}}
    for cls, sub in buckets.items():
        rows = bids[bids.resource_seq.isin(sub.index)]
        c = geom[cls]["pct_committed"] / 100.0
        p = geom[cls]["pct_peaking"] / 100.0
        e_lo, e_hi = c, 1.0 - p
        e_mid = e_lo + (e_hi - e_lo) * ECON_LOW_SHARE[cls]
        windows = {
            "econ_low": (e_lo, e_mid),
            "econ_high": (e_mid, e_hi),
            "peak": (e_hi, 1.0),
        }
        # Terciles of recovered slope, cap-weighted-median compared. The
        # stratification is a TEST INSTRUMENT: it enters no LP value, no
        # artifact and no config (PRECHECK §3c).
        edges = np.quantile(sub.slope.to_numpy(float), [1 / 3, 2 / 3])
        tercile = pd.Series(
            np.digitize(sub.slope.to_numpy(float), edges), index=sub.index, name="terc"
        )
        band_out = {}
        for band, (lo, hi) in windows.items():
            bp = _band_price(rows, lo, hi).rename("p").reset_index()
            bp = bp.merge(
                rows[["resource_seq", "interval_start_utc", "day", "gas", "year"]]
                .drop_duplicates(["resource_seq", "interval_start_utc"]),
                on=["resource_seq", "interval_start_utc"],
                how="left",
            ).dropna(subset=["gas"])
            # OWN recovered HR in the denominator, not the class constant.
            bp["own_hr"] = bp.resource_seq.map(sub.slope)
            bp["denom"] = bp.own_hr * (bp.gas + CO2_FACTOR * bp.year.map(carbon))
            bp["m"] = (bp.p - VOM_BY_CLASS[cls]) / bp.denom
            ry = bp.groupby(["resource_seq", "year"]).m.median().reset_index()
            ry["cap"] = ry.resource_seq.map(sub.cap)
            ry["terc"] = ry.resource_seq.map(tercile)
            pooled = _wquantile(ry.m.to_numpy(float), ry.cap.to_numpy(float), 0.5)
            per_t = {}
            for t in sorted(ry.terc.dropna().unique()):
                g = ry[ry.terc == t]
                per_t[int(t)] = {
                    "n_resource_years": int(len(g)),
                    "slope_range": [
                        round(float(sub.slope[sub.index.isin(g.resource_seq)].min()), 2),
                        round(float(sub.slope[sub.index.isin(g.resource_seq)].max()), 2),
                    ],
                    "conduct_ratio_capwt_median": round(
                        _wquantile(g.m.to_numpy(float), g.cap.to_numpy(float), 0.5), 4
                    ),
                }
            vals = [v["conduct_ratio_capwt_median"] for v in per_t.values()]
            spread = float(max(vals) - min(vals)) if vals else float("nan")
            tol = max(LOYO_ABS, LOYO_REL * abs(pooled))
            band_out[band] = {
                "pooled_conduct_ratio": round(float(pooled), 4),
                "terciles": per_t,
                "spread": round(spread, 4),
                "tolerance": round(float(tol), 4),
                "pass": bool(spread <= tol),
            }
        it1["buckets"][cls] = {
            "bands": band_out,
            "pass": all(b["pass"] for b in band_out.values()),
        }
    it1["all_buckets_pass"] = all(b["pass"] for b in it1["buckets"].values())

    rec = {
        "years": years,
        "hr_cut": args.hr_cut,
        "gas_min_r": GAS_MIN_R,
        "census": census,
        "contamination": contamination,
        "model_mw_newly_taking_a_measured_rung": newly_priced_mw,
        "IT2_separability": it2,
        "IT1_conduct_homogeneity": it1,
        "route": (
            "SEPARATION"
            if it2["any_candidate_passes"]
            else ("BUCKET_BAND" if it1["all_buckets_pass"] else "REFUSED")
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print()
    print(f"IT-2 separability : any candidate passes = {it2['any_candidate_passes']}")
    for c in it2["candidates"]:
        print(
            f"   cut {c['cut']:6.3f} ({c['below']} {c['below_base_hr']} | "
            f"{c['above']} {c['above_base_hr']}, sep {c['separation_mmbtu']}) "
            f"-> antimode {c['antimode_found']}"
        )
    print(f"IT-1 homogeneity  : all buckets pass = {it1['all_buckets_pass']}")
    for cls, b in it1["buckets"].items():
        for band, d in b["bands"].items():
            print(
                f"   {cls:11s} {band:10s} pooled {d['pooled_conduct_ratio']:.4f} "
                f"spread {d['spread']:.4f} tol {d['tolerance']:.4f} "
                f"-> {'PASS' if d['pass'] else 'FAIL'}"
            )
    print()
    print(f"ROUTE = {rec['route']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
