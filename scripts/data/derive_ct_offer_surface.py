"""Derive the MEASURED condition-responsive CT/peaker offer surface (ERCOT G-22).

The gated, measured successor direction filed as structural conclusion #1 of
``docs/FINDING-ercot-priceshape-2026-07.md`` §6 and specified in
``docs/handoffs/ercot-g22-offer-surface-2026-07.md``. Where the model prices
every online CT/peaker MW at its flat marginal cost ``heat_rate x gas + VOM``
(~$50-150/MWh), the real fleet's peakers self-withhold to the ERCOT offer-cap
band (~$1,500/MWh) in the high-net-load hours where they are marginal -- the
"phantom sub-$200 spare" that caps the model's energy dual in the missed tail
hours (the G-22 wedge, calibration-log 2026-07-06).

This script measures that self-withholding offer directly from the 60-Day DAM
disclosure, indexed by a **net-load percentile** driver, and freezes it into a
condition-responsive two/three-regime surface the LP applies to the CT/peaker
tranches only.

Method (measured, NOT fit to the LMP residual -- rule 13)
---------------------------------------------------------
For each year in {2023, 2024, 2025}, over the 60-Day DAM Gen Resource Data:

1. Per (Delivery Date, Hour Ending): ``net_load = sum(Awarded Quantity)`` over
   non-renewable dispatchable resources (all Resource Types except WIND/PVGR/
   RENEW), ranked within the year to a percentile ``q in [0,1]`` -- the same
   demand driver the West/Waha gas-shape and the ST_GAS/CT reliability drags
   key off, forward-native (a load forecast plus a VRE build regenerates it).
2. Per CT/peaker resource-hour (Resource Type in SCGT90/SCLE90), status ON*:
   the **offer price at 90% of HSL** -- the price on the unit's last economic
   MW (the first submitted curve point whose MW >= 0.9*HSL, else the curve's
   top price). This is the self-withholding offer, read straight from the QSE
   curve; no fuel/heat-rate division, no VOM subtraction, no residual.
3. Aggregate the CT/peaker offer@90%HSL by net-load percentile bin, per year and
   pooled 2023-2025 (median + p25/p75 + N).
4. Reduce to the frozen regime surface: the **hinge** is the pooled net-load
   percentile at which the CT median offer@90%HSL first crosses the structural
   high-offer threshold ``--high-threshold`` (default $500, midway between the
   competitive body ~$150 and the cap band ~$1,500 -- a fixed structural line,
   not swept against any backcast). The **high level** is the pooled median of
   offers in q >= hinge, ERCOT-cap-clamped. The low regime is **inert** (0):
   the LP applies ``max(mc, level)``, so a 0 low level leaves slack hours
   byte-identical and touches only the tail.

Outputs
-------
* ``data/raw/_processed-legacy/ercot_ct_offer_surface_summary.csv`` -- the full
  measured per-bin distribution per year and pooled (always written).
* ``data/raw/_validation-source/ercot_ct_offer_surface.json`` -- the frozen
  regime surface the mechanism reads (written with ``--write-json``): a list of
  ``[q_lo, q_hi, offer_level]`` regimes, ERCOT-only, plus provenance.

Usage::

    python scripts/data/derive_ct_offer_surface.py                 # report only
    python scripts/data/derive_ct_offer_surface.py --write-json    # freeze the surface
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "src"))
from market_sim.config import paths  # noqa: E402

DAM_DIR = paths.RAW_DIR / "ercot"
DAM_PREFIX = "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_"
OUT_SUMMARY = paths.PROCESSED_DIR / "ercot_ct_offer_surface_summary.csv"
OUT_JSON = paths.CALIBRATION_DIR / "ercot_ct_offer_surface.json"

# Resource-Type -> model class. CT/peaker is the only class this surface touches
# (CC/COAL/ST_GAS offer@90%HSL are ~marginal-cost and flat in net-load -- their
# scarcity rent lives in the peak tranche, out of scope; see the design note).
CT_TYPES = {"SCGT90", "SCLE90"}
RENEWABLE_TYPES = {"WIND", "PVGR", "RENEW"}
# Committed/online statuses whose submitted curve is a live dispatchable offer.
ONLINE_STATUS = {"ON", "ONOS", "ONRR", "ONEMR", "ONTEST"}
ERCOT_OFFER_CAP = 5000.0  # ERCOT system-wide offer cap (HCAP), $/MWh.

PRICE_COLS = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
MW_COLS = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]

# The DAM files are quarter/season-sharded; map each shard tag to its year.
FILE_TAGS: dict[int, list[str]] = {
    2023: ["2023_Jan-Mar", "2023_Apr-Jun", "2023_Jul-Sep", "2023_Oct-Nov"],
    2024: [
        "2024_Jan-Mar",
        "2024_Apr-Jun",
        "2024_Jul-Sep",
        "2024_Oct-Nov",
        "2024_Dec",
    ],
    2025: [
        "2025_Jan-Feb",
        "2025_Mar-Apr",
        "2025_May-Jun",
        "2025_Jul",
        "2025_Aug-Sep",
        "2025_Oct-Nov",
        "2025_Dec",
    ],
}


def _offer_at_90_hsl(price: np.ndarray, mw: np.ndarray, hsl: np.ndarray) -> np.ndarray:
    """Return the submitted offer price at 90% of HSL, per resource-hour.

    The first curve point whose MW reaches ``0.9*HSL`` (a monotone step curve),
    falling back to the top submitted price when the curve does not reach 90%.
    Fully vectorised over the ``(n, 10)`` price/MW arrays.
    """
    target = 0.9 * hsl
    out = np.full(len(price), np.nan)
    for k in range(price.shape[1]):
        hit = (mw[:, k] >= target) & np.isnan(out) & (mw[:, k] > 0)
        out[hit] = price[hit, k]
    top = np.nanmax(np.where(mw > 0, price, np.nan), axis=1)
    out = np.where(np.isnan(out), top, out)
    return out


def _load_year(year: int) -> pd.DataFrame:
    """Load one year's CT/peaker online offer@90%HSL with its net-load percentile.

    Returns a frame with columns ``[year, q, offer90]`` (one row per CT
    resource-hour). Net-load percentile ``q`` is ranked within the year over
    the distinct (date, hour) system net-load.
    """
    cols = (
        [
            "Delivery Date",
            "Hour Ending",
            "Resource Type",
            "HSL",
            "Resource Status",
            "Awarded Quantity",
        ]
        + PRICE_COLS
        + MW_COLS
    )
    parts = []
    for tag in FILE_TAGS[year]:
        fn = DAM_DIR / f"{DAM_PREFIX}{tag}.parquet"
        if not fn.exists():
            print(f"  [warn] missing shard {fn.name}")
            continue
        parts.append(pd.read_parquet(fn, columns=cols))
    if not parts:
        raise FileNotFoundError(f"no DAM shards found for {year} under {DAM_DIR}")
    df = pd.concat(parts, ignore_index=True)

    key = ["Delivery Date", "Hour Ending"]
    disp = df[~df["Resource Type"].isin(RENEWABLE_TYPES)]
    net = disp.groupby(key)["Awarded Quantity"].sum().rename("net_load").reset_index()
    net["q"] = net["net_load"].rank(pct=True)

    ct = df[
        df["Resource Type"].isin(CT_TYPES) & df["Resource Status"].isin(ONLINE_STATUS)
    ].merge(net[key + ["q"]], on=key, how="left")
    ct = ct[ct["HSL"] > 0]

    offer90 = _offer_at_90_hsl(
        ct[PRICE_COLS].to_numpy(float),
        ct[MW_COLS].to_numpy(float),
        ct["HSL"].to_numpy(float),
    )
    return pd.DataFrame({"year": year, "q": ct["q"].to_numpy(), "offer90": offer90})


def _bin_summary(df: pd.DataFrame, n_bins: int = 20) -> pd.DataFrame:
    """Median/p25/p75/N of CT offer@90%HSL per net-load percentile bin, per year+pooled."""
    df = df.copy()
    df["bin"] = np.clip((df["q"] * n_bins).astype(int), 0, n_bins - 1)
    rows = []
    for label, sub in [("pooled", df)] + [(str(y), g) for y, g in df.groupby("year")]:
        for b, gb in sub.groupby("bin"):
            v = gb["offer90"].to_numpy()
            rows.append(
                {
                    "scope": label,
                    "nl_bin": b,
                    "nl_pct_lo": b / n_bins,
                    "nl_pct_hi": (b + 1) / n_bins,
                    "n": len(v),
                    "p25": float(np.nanpercentile(v, 25)),
                    "median": float(np.nanmedian(v)),
                    "p75": float(np.nanpercentile(v, 75)),
                }
            )
    return pd.DataFrame(rows)


def _fit_regimes(pooled: pd.DataFrame, high_threshold: float) -> dict:
    """Reduce the pooled per-bin distribution to the frozen condition-responsive surface.

    The hinge is keyed on the **lower quartile (p25)**, not the median. Pooled
    2023-2025, the CT median offer@90%HSL is already cap-band ($1,500) in every
    net-load bin -- >50% of peaker MW self-withholds even in slack (the 2024/25
    tails dominate). But the *p25* steps from ~$150 to $1,500 only near the top
    of the net-load distribution: below that a material competitive body (>25% of
    peaker MW) is still offered near marginal cost. The **hinge** is therefore the
    lowest net-load percentile at which the pooled p25 itself crosses
    ``high_threshold`` -- the point above which the peaker fleet's offer is
    unambiguously cap-band across essentially its whole distribution. Posting the
    cap-band level below that hinge would over-withhold the still-competitive body
    -- the exact ercot33 static-wall failure this design avoids (rule 1 /
    FINDING §6). The **high level** is the pooled median offer in the q>=hinge
    regime, ERCOT-cap-clamped; the low regime is inert (0), so the LP applies
    ``max(mc, 0) = mc`` and slack hours stay byte-identical.
    """
    p = pooled[pooled["scope"] == "pooled"].sort_values("nl_bin")
    crossed = p[p["p25"] >= high_threshold]
    if crossed.empty:
        raise ValueError(
            f"no net-load bin's p25 reaches the ${high_threshold:.0f} high-offer "
            "threshold -- a competitive peaker body persists at every net-load "
            "state; posting a universal cap-band offer would over-withhold"
        )
    hinge = float(crossed["nl_pct_lo"].min())
    high_bins = p[p["nl_pct_lo"] >= hinge]
    high_level = float(
        min(np.nanmedian(high_bins["median"].to_numpy()), ERCOT_OFFER_CAP)
    )
    return {
        "hinge_net_load_pct": round(hinge, 4),
        "high_offer_level": round(high_level, 1),
        "high_threshold": high_threshold,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--high-threshold",
        type=float,
        default=500.0,
        help="structural $/MWh line separating body from cap-band "
        "self-withholding (default 500; fixed, not swept)",
    )
    ap.add_argument("--n-bins", type=int, default=20)
    ap.add_argument(
        "--write-json",
        action="store_true",
        help="freeze the regime surface to the calibration JSON",
    )
    args = ap.parse_args()

    frames = []
    for year in (2023, 2024, 2025):
        print(f"[derive] loading {year} DAM Gen Resource Data ...")
        frames.append(_load_year(year))
    allct = pd.concat(frames, ignore_index=True)
    print(
        f"[derive] {len(allct):,} CT/peaker online resource-hours "
        f"across {allct['year'].nunique()} years"
    )

    summary = _bin_summary(allct, n_bins=args.n_bins)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"[derive] wrote {OUT_SUMMARY}")

    regimes = _fit_regimes(summary, args.high_threshold)
    print("[derive] frozen CT offer surface (measured, not residual-fit):")
    print(f"          hinge net-load pct = {regimes['hinge_net_load_pct']:.2f}")
    print(f"          high offer level   = ${regimes['high_offer_level']:.0f}/MWh")

    # show the pooled per-bin medians for the record
    piv = summary[summary["scope"] == "pooled"][["nl_bin", "median", "n"]]
    print("[derive] pooled CT offer@90%HSL median by net-load ventile:")
    print(piv.to_string(index=False))

    if args.write_json:
        payload = {
            "iso": "ERCOT",
            "driver": "net_load_percentile_within_year",
            "class": "CT_PEAKER",
            "metric": "offer_at_90pct_HSL",
            "source": f"{DAM_PREFIX}* 2023-2025 (60-Day DAM disclosure)",
            "note": (
                "Measured self-withholding CT/peaker offer. Low regime inert "
                "(LP applies max(mc, level)); high regime posts the measured "
                "cap-band offer above the hinge. Frozen against residuals "
                "(rule 20); re-derive only on a disclosure-data update."
            ),
            "hinge_net_load_pct": regimes["hinge_net_load_pct"],
            "regimes": [
                [0.0, regimes["hinge_net_load_pct"], 0.0],
                [regimes["hinge_net_load_pct"], 1.0, regimes["high_offer_level"]],
            ],
        }
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"[derive] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
