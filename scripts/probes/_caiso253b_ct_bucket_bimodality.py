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

INSTRUMENT CORRECTION (caiso-254, 2026-09-06 — made by CODE INSPECTION, before
any statistic of the bid population was scored, and disclosed rather than
silently applied)
------------------------------------------------------------------------------
As first written this probe did not reproduce the derive on three points. All
three were found by reading ``derive_caiso_offer_surface.py`` against this file
— never by comparing a number to the 46 CC / 100 CT target, which would have
made the instrument a thing fitted to its own answer:

1. **``cap``.** The derive computes
   ``bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)`` — the
   p98 of EVERY segment row in the resource-year. This probe computed the p98
   of the HOURLY MAXIMA, which is systematically higher and therefore shifted
   both the ``cap >= 20 MW`` admission and the ``0.35 x cap`` body rung. (The
   derive's own module docstring says "p98 of hourly max cumulative bid MW";
   its code says otherwise, and code is the source of truth.)
2. **Pooling ``cap`` across years.** The derive takes
   ``seg.groupby("resource_seq").cap.first()`` on the frame sorted by
   ``(resource_seq, interval_start_utc, segment_mw)`` — the resource's EARLIEST
   year's cap. This probe took the MAX across years.
3. **``min_mw``.** The derive reduces it on the CAP-FILTERED frame; this probe
   reduced it over the unfiltered store.

The corpus is only ~57 M segment rows (~1.2 GB at these dtypes), so the fix is
also the simpler construction: load the reduced store as ONE frame and follow
the derive's own line order. No streaming approximation survives, and P-2 now
tests the corpus and the construction rather than this file's transcription.

MEMORY: ``curate_dam_public_bids.py`` needs ~14.3 GB for one CAISO year against
15 GB of RAM (the corpus README's measured limit), so this probe never touches
the clean tree. ``pass1`` streams ``dam_public_bids.caiso.parse_day`` day-by-day
into a slim gitignored per-day store (the ``derive_caiso_battery_bid_floor.py``
precedent), applying the derive's three row filters as it goes; only that
already-slim store is loaded whole. Pass 1 is resumable: re-running skips days
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


def _load_bids() -> pd.DataFrame:
    """The reduced store as ONE frame, shaped exactly like the derive's.

    Mirrors ``derive_caiso_offer_surface._load_bids``: the same four columns,
    the same three row filters (applied in ``pass1``), the same ``price``
    rename, the same ``year`` column and the SAME final sort key. The whole
    corpus is ~57 M segment rows (~1.2 GB at these dtypes), so it fits in one
    frame and no streaming approximation is needed anywhere below.
    """
    frames = []
    for f in sorted(STORE.glob("*.parquet")):
        y = int(f.stem[:4])
        if y not in YEARS:
            continue
        d = pd.read_parquet(f)
        d = d.rename(columns={"segment_price_usd_per_mwh": "price"})
        d["year"] = np.int16(y)
        d["segment_mw"] = d.segment_mw.astype("float32")
        d["price"] = d.price.astype("float32")
        frames.append(d)
    out = pd.concat(frames, ignore_index=True, copy=False)
    frames.clear()
    return out.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])


def _with_cap(bids: pd.DataFrame) -> pd.DataFrame:
    """Attach the derive's OWN ``cap`` and apply its ``MIN_CAP_MW`` row filter.

    ``derive_caiso_offer_surface.main``:

        cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
        bids   = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
        bids   = bids[bids.cap >= MIN_CAP_MW]

    i.e. the p98 of **every segment row** in the resource-year — NOT of the
    hourly maxima. (The derive's module docstring says "p98 of hourly max
    cumulative bid MW"; its code says the above, and CODE IS THE SOURCE OF
    TRUTH. See this module's INSTRUMENT CORRECTION note.)
    """
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(
        CAP_PCTILE / 100.0
    )
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    return bids[bids.cap >= MIN_CAP_MW]


def _body_daily(bids: pd.DataFrame) -> pd.DataFrame:
    """Per (resource, local day) median body price — the derive's ``_classify``.

    ``_price_at_frac(seg, BODY_FRAC)`` then a per-(resource, Pacific day)
    median, reproduced line for line on the cap-filtered frame.
    """
    below = bids[bids.segment_mw <= BODY_FRAC * bids.cap]
    p = below.groupby(["resource_seq", "interval_start_utc"]).price.last()
    first = bids.groupby(["resource_seq", "interval_start_utc"]).price.first()
    body = p.reindex(first.index).fillna(first).rename("p_body").reset_index()
    body["day"] = (
        body.interval_start_utc.dt.tz_convert("US/Pacific")
        .dt.normalize()
        .dt.tz_localize(None)
    )
    return body.groupby(["resource_seq", "day"], as_index=False).p_body.median()


def _kde(x: np.ndarray, w: np.ndarray, grid: np.ndarray, bw: float) -> np.ndarray:
    """Capacity-weighted Gaussian KDE — a smoother for locating an antimode."""
    z = (grid[:, None] - x[None, :]) / bw
    return (np.exp(-0.5 * z**2) * w[None, :]).sum(axis=1) / (bw * np.sqrt(2 * np.pi))


def _coverage() -> tuple[int, dict[int, int], list[str]]:
    """(store days, days per year, missing trade dates) over the 2023-25 span."""
    have = {f.stem for f in STORE.glob("*.parquet") if int(f.stem[:4]) in YEARS}
    span = pd.date_range(f"{YEARS[0]}-01-01", f"{YEARS[-1]}-12-31", freq="D")
    want = {d.strftime("%Y%m%d") for d in span}
    per_year = {y: sum(1 for t in have if int(t[:4]) == y) for y in YEARS}
    return len(have), per_year, sorted(want - have)


def gate() -> None:
    """Score G-BIMODAL — but only against a COMPLETE corpus.

    The registered design (PRECOMMIT §5, P-1) is that the gate "REFUSES to
    score an under-covered corpus rather than reporting a number". As first
    written the only refusal was the ``GAS_MIN_DAYS`` emptiness check, which a
    partial corpus clears as soon as ~120 days of ONE year are present — so a
    mid-fetch run scored and wrote a verdict instead of refusing. That is the
    defect this guard closes; see the caiso-254 FINDING's disclosure.

    ``MAX_MISSING_DAYS`` is a corpus-adequacy tolerance, not a gate threshold:
    P-1 registers that exactly one trade date (2023-06-01) is a genuine OASIS
    archive hole, so the span admits a handful of absences and nothing more.
    """
    #: 1,096 calendar days in the 2023-25 span; P-1 expects 1,095 present.
    MAX_MISSING_DAYS = 6

    store_days, per_year, missing = _coverage()
    if not store_days:
        raise SystemExit("no reduced days in the store — run --pass1 first")
    if len(missing) > MAX_MISSING_DAYS or any(per_year[y] == 0 for y in YEARS):
        raise SystemExit(
            f"REFUSED: corpus is under-covered — {store_days} reduced day(s), "
            f"per-year {per_year}, {len(missing)} missing of "
            f"{store_days + len(missing)} (tolerance {MAX_MISSING_DAYS}). "
            f"First missing: {missing[:5]}. G-BIMODAL is scored on the POOLED "
            "2023-25 population only (PRECOMMIT §2.1); a partial corpus is a "
            "different population and its verdict is not this gate's. Finish "
            "the fetch, re-run --pass1, then --gate."
        )
    bids = _load_bids()
    bids = _with_cap(bids)
    daily = _body_daily(bids)
    gas = _gas_staircase()
    daily["gas"] = daily.day.map(gas)
    daily = daily.dropna(subset=["gas"])

    # The derive's own two per-resource reductions, on the CAP-FILTERED frame:
    #     cap    = seg.groupby("resource_seq").cap.first()
    #     min_mw = seg.groupby("resource_seq").segment_mw.min()
    # `.first()` after the (resource_seq, interval_start_utc, segment_mw) sort
    # is the resource's EARLIEST year's cap — not a max or a mean across years.
    cap_pooled = bids.groupby("resource_seq").cap.first()
    min_mw = bids.groupby("resource_seq").segment_mw.min()
    years_covered = sorted({int(y) for y in bids.year.unique()})

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
        "store_days": store_days,
        "days_per_year": per_year,
        "missing_trade_dates": missing,
        "years_covered": years_covered,
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
