"""caiso-253b: G-BIMODAL — is the measured offer surface's CT bucket contaminated?

Registered in ``results/calibration/PRECOMMIT-caiso253b-offer-surface-contamination-2026-09-06.md``
(pushed before any bid data was fetched and before any statistic was computed).

The derive discloses that its CT bucket "may include the 2.9 GW OTC/RMR ST_GAS
steamers and priced CT_CHP", whose fleet heat rate (~11.85) sits ~9 % ABOVE the
CT_PEAKER base HR (10.862) the multiplier divides by. This probe rebuilds the
derive's OWN per-resource Theil-Sen slope population with its OWN frozen gates
and asks the one registered question: does the CT-side capacity density carry a
second antimode separating an aero-CT mode from a steam mode?

**Nothing here is re-derived and no threshold is retuned.** The estimator, the
body probe (0.35), the gas gates, the capacity statistic and ``hr_cut`` = 8.5
are read from the derive and used as-is.

MEMORY: ``curate_dam_public_bids.py`` needs ~14.3 GB for one CAISO year against
15 GB of RAM (the corpus README's measured limit), so this probe never touches
the clean tree. It streams ``dam_public_bids.caiso.parse_day`` day-by-day into a
slim gitignored per-day store (the ``derive_caiso_battery_bid_floor.py``
precedent) and reduces as it goes. Pass 1 is resumable: re-running skips days
already reduced, so it can be run against a fetch still in flight.

Output: ``results/calibration/_caiso253b_ct_bucket_bimodality.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso253b_ct_bucket_bimodality.py --pass1
    PYTHONPATH=.:src uv run python scripts/probes/_caiso253b_ct_bucket_bimodality.py --gate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import GAS_PRICES_DIR  # noqa: E402
from scripts.lib.dam_public_bids.caiso import parse_day  # noqa: E402

ZIPS = REPO / "data/raw/caiso-public-bids/zips"
STORE = REPO / "data/raw/caiso-public-bids/_caiso253b_reduced"  # gitignored dir
OUT = REPO / "results/calibration/_caiso253b_ct_bucket_bimodality.json"
YEARS = (2023, 2024, 2025)

# --- the derive's OWN frozen constants, imported by value, NOT retuned -------
MIN_CAP_MW = 20.0
GAS_SLOPE_RANGE = (4.0, 18.0)
GAS_MIN_R = 0.6
GAS_MIN_DAYS = 120
BODY_FRAC = 0.35
HR_CUT = 8.5
CAP_PCTILE = 98.0

# --- G-BIMODAL, fixed in the PRECOMMIT before the population was built -------
ANTIMODE_WINDOW = (10.9, 12.5)  # CT_PEAKER fleet base HR -> above the steamers
CAP_ABOVE_BRACKET_GW = (1.5, 4.5)  # 2.9 GW of OTC/RMR steamers + priced CT_CHP
KDE_BW = 0.35  # MMBtu/MWh; a density smoother, not a gate threshold


def _gas_staircase() -> pd.Series:
    """CA-composite citygate on gas FLOW days — the derive's construction."""
    gas = pd.read_csv(GAS_PRICES_DIR / "caiso_citygate_daily.csv", parse_dates=["date"])
    gas = gas.sort_values("date")
    gas["flow"] = gas["date"] + pd.Timedelta(days=1)
    cal = pd.date_range(gas["flow"].min(), gas["flow"].max() + pd.Timedelta(days=7))
    s = gas.set_index("flow")["ca_composite_usd_mmbtu"].reindex(cal).ffill()
    s.index.name = "day"
    return s


def pass1() -> None:
    """Stream each daily zip to a slim per-day parquet. Resumable."""
    STORE.mkdir(parents=True, exist_ok=True)
    zips = sorted(ZIPS.glob("*_PUB_BID_DAM_v3_csv.zip"))
    done = skipped = 0
    for z in zips:
        tag = z.name[:8]
        out = STORE / f"{tag}.parquet"
        if out.exists():
            skipped += 1
            continue
        try:
            df = parse_day(z)
        except Exception as exc:  # a corrupt/short zip is reported, never silent
            print(f"  !! {tag}: {type(exc).__name__} {exc}")
            continue
        df = df[
            (df.resource_type == "GENERATOR")
            & (df["product"] == "EN")
            & (df.row_kind == "segment")
        ]
        df[
            [
                "interval_start_utc",
                "resource_seq",
                "segment_mw",
                "segment_price_usd_per_mwh",
            ]
        ].to_parquet(out, index=False)
        done += 1
        if done % 50 == 0:
            print(f"  reduced {done} (skipped {skipped}) … latest {tag}")
    print(
        f"pass1: reduced {done} new day(s), {skipped} already present, "
        f"{len(list(STORE.glob('*.parquet')))} total in store"
    )


def _cap_by_resource_year() -> dict[int, pd.Series]:
    """cap = p98 of hourly max cumulative bid MW, per resource per year."""
    acc: dict[int, dict[int, list]] = {y: {} for y in YEARS}
    for f in sorted(STORE.glob("*.parquet")):
        y = int(f.stem[:4])
        if y not in acc:
            continue
        d = pd.read_parquet(
            f, columns=["interval_start_utc", "resource_seq", "segment_mw"]
        )
        h = d.groupby(
            ["resource_seq", "interval_start_utc"], sort=False
        ).segment_mw.max()
        for rid, vals in h.groupby(level=0):
            acc[y].setdefault(rid, []).append(vals.to_numpy(float))
    out = {}
    for y, per in acc.items():
        if not per:
            continue
        out[y] = pd.Series(
            {
                rid: float(np.percentile(np.concatenate(v), CAP_PCTILE))
                for rid, v in per.items()
            }
        )
    return out


def _body_daily(caps: dict[int, pd.Series]) -> pd.DataFrame:
    """Per (resource, local day) median body price at BODY_FRAC x cap."""
    rows = []
    for f in sorted(STORE.glob("*.parquet")):
        y = int(f.stem[:4])
        if y not in caps:
            continue
        cap = caps[y]
        d = pd.read_parquet(f)
        d = d.rename(columns={"segment_price_usd_per_mwh": "price"})
        d["cap"] = d.resource_seq.map(cap)
        d = d.dropna(subset=["cap"])
        d = d[d.cap >= MIN_CAP_MW]
        if d.empty:
            continue
        d = d.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])
        below = d[d.segment_mw <= BODY_FRAC * d.cap]
        p = below.groupby(["resource_seq", "interval_start_utc"]).price.last()
        first = d.groupby(["resource_seq", "interval_start_utc"]).price.first()
        body = p.reindex(first.index).fillna(first).rename("p_body").reset_index()
        body["day"] = (
            body.interval_start_utc.dt.tz_convert("US/Pacific")
            .dt.normalize()
            .dt.tz_localize(None)
        )
        rows.append(
            body.groupby(["resource_seq", "day"], as_index=False).p_body.median()
        )
    return pd.concat(rows, ignore_index=True)


def _min_mw() -> pd.Series:
    """Per-resource minimum segment MW — the derive's NGR withdrawal exclusion."""
    acc: dict[int, float] = {}
    for f in sorted(STORE.glob("*.parquet")):
        d = pd.read_parquet(f, columns=["resource_seq", "segment_mw"])
        m = d.groupby("resource_seq").segment_mw.min()
        for rid, v in m.items():
            acc[rid] = min(acc.get(rid, np.inf), float(v))
    return pd.Series(acc)


def _kde(x: np.ndarray, w: np.ndarray, grid: np.ndarray, bw: float) -> np.ndarray:
    """Capacity-weighted Gaussian KDE — a smoother for locating an antimode."""
    z = (grid[:, None] - x[None, :]) / bw
    return (np.exp(-0.5 * z**2) * w[None, :]).sum(axis=1) / (bw * np.sqrt(2 * np.pi))


def gate() -> None:
    caps = _cap_by_resource_year()
    if not caps:
        raise SystemExit("no reduced days in the store — run --pass1 first")
    daily = _body_daily(caps)
    gas = _gas_staircase()
    daily["gas"] = daily.day.map(gas)
    daily = daily.dropna(subset=["gas"])

    cap_pooled = pd.concat(caps.values(), axis=1).max(axis=1)
    min_mw = _min_mw()

    rows = []
    for rid, g in daily.groupby("resource_seq"):
        if len(g) < GAS_MIN_DAYS or g.gas.std() < 0.5:
            continue
        x, y = g.gas.to_numpy(float), g.p_body.to_numpy(float)
        slope, _, _, _ = theilslopes(y, x)
        rows.append(
            {
                "resource_seq": rid,
                "slope": float(slope),
                "r": float(np.corrcoef(x, y)[0, 1]),
                "n_days": len(g),
            }
        )
    if not rows:
        raise SystemExit(
            f"no resource cleared the derive's own GAS_MIN_DAYS={GAS_MIN_DAYS} gate "
            f"over {len(list(STORE.glob('*.parquet')))} reduced day(s). The gate REFUSES "
            "to score an under-covered corpus (PRECOMMIT P-1/P-2): finish the fetch, "
            "re-run --pass1, then --gate."
        )
    res = pd.DataFrame(rows).set_index("resource_seq")
    res["cap"] = cap_pooled.reindex(res.index)
    res["min_mw"] = min_mw.reindex(res.index)
    res["is_gas"] = (
        res.slope.between(*GAS_SLOPE_RANGE)
        & (res.r >= GAS_MIN_R)
        & (res.min_mw >= -1.0)
    )
    res["cls"] = np.where(res.slope < HR_CUT, "CC_REGULAR", "CT_PEAKER")
    res.loc[~res.is_gas, "cls"] = ""

    gasres = res[res.is_gas]
    out: dict = {
        "store_days": len(list(STORE.glob("*.parquet"))),
        "years_covered": sorted(caps),
        "n_resources_regressed": int(len(res)),
        "buckets": {
            cls: {
                "n_units": int((gasres.cls == cls).sum()),
                "cap_gw": round(
                    float(gasres.loc[gasres.cls == cls, "cap"].sum() / 1e3), 3
                ),
                "slope_p50": round(
                    float(gasres.loc[gasres.cls == cls, "slope"].median()), 3
                ),
            }
            for cls in ("CC_REGULAR", "CT_PEAKER")
        },
        "frozen_artifact_populations": {"CC_REGULAR": 46, "CT_PEAKER": 100},
    }

    ct = gasres[gasres.cls == "CT_PEAKER"]
    if len(ct) >= 5:
        x = ct.slope.to_numpy(float)
        w = ct.cap.to_numpy(float)
        grid = np.linspace(HR_CUT, GAS_SLOPE_RANGE[1], 400)
        dens = _kde(x, w, grid, KDE_BW)
        lo, hi = ANTIMODE_WINDOW
        win = (grid >= lo) & (grid <= hi)
        # an antimode is an interior local minimum of the capacity density
        interior = np.r_[
            False, (dens[1:-1] < dens[:-2]) & (dens[1:-1] < dens[2:]), False
        ]
        cands = grid[interior & win]
        anti = float(cands[np.argmin(dens[interior & win])]) if cands.size else None
        cap_above = float(w[x >= anti].sum() / 1e3) if anti is not None else None
        out["G_BIMODAL"] = {
            "antimode_window": list(ANTIMODE_WINDOW),
            "cap_above_bracket_gw": list(CAP_ABOVE_BRACKET_GW),
            "antimode_mmbtu_per_mwh": round(anti, 3) if anti is not None else None,
            "cap_above_antimode_gw": round(cap_above, 3)
            if cap_above is not None
            else None,
            "ct_slope_deciles": [
                round(float(np.percentile(x, q)), 2) for q in range(10, 100, 10)
            ],
            "ct_cap_gw": round(float(w.sum() / 1e3), 3),
            "density_grid_step": round(float(grid[1] - grid[0]), 4),
            "verdict": (
                "PASS"
                if anti is not None
                and CAP_ABOVE_BRACKET_GW[0]
                <= (cap_above or 0)
                <= CAP_ABOVE_BRACKET_GW[1]
                else "FAIL"
            ),
        }
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--pass1", action="store_true", help="reduce daily zips to the slim store"
    )
    ap.add_argument(
        "--gate", action="store_true", help="build the population and score G-BIMODAL"
    )
    a = ap.parse_args()
    if a.pass1:
        pass1()
    if a.gate:
        gate()
    if not (a.pass1 or a.gate):
        ap.error("choose --pass1 and/or --gate")
