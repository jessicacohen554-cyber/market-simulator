"""Derive the ERCOT measured RT (SCED) storage discharge-offer surface.

The identification phase of the ercot-162 chartered successor
(``ScenarioConfig.ercot_storage_rt_offer_surface``): a measured multi-tranche
RT discharge-offer ladder for ERCOT battery storage, per net-load-percentile
bin, absolute $/MWh, year-scoped. It is the storage analogue of
``derive_ercot_sced_offer_wall`` (the merchant-gas RT spare wall) built on the
population the ercot-161 Phase 0 FINDING attributed the ~100-hour afternoon
price to: PWRSTR — grid batteries — a class the model prices at a flat
``battery_dispatch_adder`` = $10 with no offer instrument (FINDING
``results/calibration/FINDING-ercot161-afternoon-wall-phase0-2026-08-04.md``
§3–§4).

Construction (the ercot-161 ``_ercot161_pwrstr_conduct.json`` probe promoted to
a derive — same edges, quantiles and CPT->CST clock, imported not
re-implemented so they cannot drift):

* Population: ``Resource Type == PWRSTR``, telemetered ``ON*``
  (ON/ONREG/ONFFRRRS/…), with ``ONTEST`` EXCLUDED (units under commissioning
  test are not offering commercially — the ERCOT-154 population discipline).
* Increment: per interval-resource, the SCED2 (as-dispatched) curve segmented
  ABOVE ``max(LSL, 0)`` and capped at ``HASL`` — the energy headroom the
  telemetered AS stack leaves to energy (``HASL`` is ``HSL`` net of the
  resource's AS responsibility, so this ladder prices ONLY the energy-side
  discharge; the AS-side capability keeps its own co-opt owners — rule 19
  ``[R-ONE-MECH]``).
* Price basis: ABSOLUTE $/MWh (clipped to the $5,000 HCAP). The gas-multiple
  basis is REFUTED for storage — a battery has no heat rate (ERCOT-154 §1).
* Bin each interval by its hour's within-year net-load percentile (EIA-930
  demand − wind − solar), on the SHARED ``NETLOAD_PCT_EDGES`` geometry (the
  same edges the DAM/RT gas walls use), and emit the MW-weighted absolute-$
  quantile ladder per (net-load bin).

Year scope (rule 13, the RT wall's precedent): the artifact is YEAR-SCOPED with
NO cross-year pooled fallback — each year's ladder is derived only from that
year's own posted RT offers, and a year absent from the artifact gets NO
surface (the flat adder is retained). The 2023 block is derived from the
full-year delivery-2023 corpus (``data/raw/ercot/SCED/``, the ERCOT-157
NP3-965 landing, 315 shards); the 2024/2025 blocks from the committed
sample-day extracts (the RT wall's own 2024/2025 basis — full-year 2024/2025
PWRSTR is not on disk, a disclosed limitation, not a blocker: the conduct is
STANDING, measured flat across all seven net-load bins). A per-bin
``within_year_pool`` fallback (that YEAR's all-hours pooled ladder — same
instrument, same year, NOT a cross-year pool) backfills a bin whose own
coverage is below ``MIN_BIN_INTERVALS``; it is disclosed per bin.

The LP tranche construction is fixed A PRIORI (never selected on model
absorption — the ERCOT-154 DO-NOT-REDO discipline): ``K = 3`` discharge
tranches per battery unit, cumulative-power-fraction edges
``TRANCHE_CUM_EDGES = (0.10, 0.30)`` (plus the implicit 0 and 1), widths
``(0.10, 0.20, 0.70)`` of the hour's power cap, priced at the RIGHT-edge
quantile of each slice — ``(Q(0.10), Q(0.30), Q(0.99))`` — the conservative
rising step function. The p10–p30 toe is the live question the year-pair
stability test targets; p50+ is HCAP-degenerate by measurement (p50–p99 =
$5,000 in every bin), so the top tranche is the $5,000 cap block. The
LEFT-edge (lower-bound) variant is also computed and disclosed but NOT used.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Zero fitted scalars.

Usage::

    PYTHONPATH=.:src python3 scripts/data/derive_ercot_storage_rt_offer_surface.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_storage_rt_offer_condbinned.json] \
        [--verify]   # reproduce the ercot-161 census reference numbers
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

from scripts.data.derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    _MONTH_START_HOUR,
    _netload_pct,
    _weighted_quantiles,
)
from scripts.data.derive_ercot_sced_offer_wall import (  # noqa: E402
    _NUMERIC_COLS,
    _SCED2_MW,
    _SCED2_PR,
    NETLOAD_PCT_EDGES,
    _delivery_year_rows,
    _sced_source_files,
)

DEFAULT_OUT = CALIBRATION_DIR / "ercot_storage_rt_offer_condbinned.json"
_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (matches the probe)

#: Disclosure quantiles of the discharge-offer ladder (MW-weighted, absolute $).
#: Identical to the ercot-161 conduct probe so the census reproduces exactly.
QUANTS: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99)

#: $/MWh rungs for the offered-MW census (reproduces the FINDING's ≥$500 GW).
USD_RUNGS: tuple[float, ...] = (100.0, 300.0, 500.0, 1000.0, 2000.0, 4000.0)

#: A-PRIORI LP tranche construction (fixed before any solve; never selected on
#: model absorption). K = 3 discharge tranches per battery unit. The interior
#: cumulative-power-fraction edges partition the hour's power cap into slices of
#: width (0.10, 0.20, 0.70); each slice is priced at the quantile of its
#: RIGHT (upper) cumulative edge — the conservative rising step function. The
#: top slice's price uses Q(0.99), the deep-cap rung (p50–p99 all measure the
#: $5,000 HCAP), rather than Q(1.0), which is undefined.
TRANCHE_CUM_EDGES: tuple[float, ...] = (0.10, 0.30)
TRANCHE_WIDTHS: tuple[float, ...] = (0.10, 0.20, 0.70)
#: Right-edge quantile of each of the K slices [0,0.1], [0.1,0.3], [0.3,1.0].
TRANCHE_RIGHT_Q: tuple[float, ...] = (0.10, 0.30, 0.99)
#: Left-edge quantile of each slice — the lower-bound variant, disclosed only.
TRANCHE_LEFT_Q: tuple[float, ...] = (0.10, 0.10, 0.30)

#: A bin whose own coverage is below this many SCED intervals borrows that
#: YEAR's all-hours pooled ladder (within-year, same-instrument — NOT a
#: cross-year pool). Disclosed per bin via ``source: "within_year_pool"``.
MIN_BIN_INTERVALS: int = 200

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "Base Point",
    "LSL",
] + [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]


def _pwrstr_segments(year: int) -> tuple[pd.DataFrame, dict[str, float]]:
    """Above-LSL, HASL-capped PWRSTR discharge segments for a delivery year.

    Returns ``(seg, status_mw)`` where ``seg`` has columns
    ``hoy, mw, price, ts, status`` (one row per interval-resource curve step of
    above-LSL energy headroom, price clipped to HCAP) and ``status_mw`` is the
    MW mass per telemetered status (for the ONTEST/ONREG share disclosure).
    The construction is byte-for-byte the ercot-161 conduct probe's.
    """
    seg_acc: list[pd.DataFrame] = []
    status_mw: dict[str, float] = {}
    n_files = 0
    for path in _sced_source_files(year):
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"] == "PWRSTR"]
        n_files += 1
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON")].copy()
        df["status"] = stat[stat.str.startswith("ON")]
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert(_STD_TZ)
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))  # drop Feb 29 to match the 8760 clock
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        cols = [c for c in _NUMERIC_COLS if c in df.columns]
        df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

        MW = df[_SCED2_MW].to_numpy(float)
        PR = df[_SCED2_PR].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        hasl = df["HASL"].to_numpy(float)
        hoy = df["hoy"].to_numpy(int)
        tskey = df["SCED Time Stamp"].to_numpy()
        status = df["status"].to_numpy()

        seg = {k: [] for k in ("hoy", "mw", "price", "ts", "status")}
        prev = lsl.copy()
        for k in range(MW.shape[1]):  # k: SCED2 curve step (vectorized over rows)
            q = MW[:, k]
            p = PR[:, k]
            valid = np.isfinite(q) & np.isfinite(p)
            cap = np.minimum(q, hasl)
            mw = np.where(valid, np.maximum(cap - np.maximum(prev, lsl), 0.0), 0.0)
            take = mw > 0
            if take.any():
                seg["hoy"].append(hoy[take])
                seg["mw"].append(mw[take])
                # Absolute $/MWh clipped to the HCAP (real offers never exceed it;
                # the clip matches the wall convention and guards a stray datum).
                seg["price"].append(np.minimum(p[take], HCAP_USD_MWH))
                seg["ts"].append(tskey[take])
                seg["status"].append(status[take])
            prev = np.where(valid, np.maximum(prev, q), prev)
        if seg["mw"]:
            sdf = pd.DataFrame({key: np.concatenate(v) for key, v in seg.items()})
            for st_name, grp in sdf.groupby("status"):
                status_mw[st_name] = status_mw.get(st_name, 0.0) + float(
                    grp["mw"].sum()
                )
            seg_acc.append(sdf)

    if not seg_acc:
        return pd.DataFrame(columns=["hoy", "mw", "price", "ts", "status"]), status_mw
    seg = pd.concat(seg_acc, ignore_index=True)
    seg = seg[seg["status"] != "ONTEST"]  # ERCOT-154 population discipline
    seg.attrs["n_files"] = n_files
    return seg, status_mw


def _ladder(sub: pd.DataFrame) -> dict:
    """MW-weighted absolute-$ quantile ladder + rung census for one hour set."""
    if sub.empty:
        return {}
    price = sub["price"].to_numpy(float)
    mw = sub["mw"].to_numpy(float)
    qs = _weighted_quantiles(price, mw, QUANTS)
    per_iv = sub.groupby("ts")["mw"].sum()
    rungs = {
        f"gw_ge_{int(r)}": round(
            float(
                sub[sub["price"] >= r]
                .groupby("ts")["mw"]
                .sum()
                .reindex(per_iv.index)
                .fillna(0.0)
                .mean()
                / 1e3
            ),
            3,
        )
        for r in USD_RUNGS
    }
    return {
        "usd_quantiles": {
            f"p{int(q * 100)}": round(float(v), 1) for q, v in zip(QUANTS, qs)
        },
        "n_intervals": int(sub["ts"].nunique()),
        "n_hours": int(sub["hoy"].nunique()),
        "mean_offered_gw": round(float(per_iv.mean() / 1e3), 3),
        "mean_gw_at_usd_rungs": rungs,
    }


def _quantile_price(ladder: dict, q: float) -> float:
    """Return the MW-weighted absolute-$ price at cumulative fraction ``q``.

    Reads the disclosure ladder's stored quantile when ``q`` is one of
    ``QUANTS``; the tranche edge set is a subset of ``QUANTS`` by construction,
    so no interpolation is needed.
    """
    key = f"p{int(round(q * 100))}"
    return float(ladder["usd_quantiles"][key])


def _tranches(ladder: dict, right_q: tuple[float, ...]) -> list[dict]:
    """K-tranche (width, price) construction from a bin's quantile ladder."""
    return [
        {"width": float(w), "price": round(_quantile_price(ladder, q), 1)}
        for w, q in zip(TRANCHE_WIDTHS, right_q)
    ]


def derive_year(year: int) -> dict:
    """Per-(net-load bin) ladders + K-tranche construction for one delivery year."""
    seg, status_mw = _pwrstr_segments(year)
    n_files = int(seg.attrs.get("n_files", 0))
    if seg.empty:
        return {"_coverage": {"n_files": n_files, "n_segments": 0}, "bins": {}}

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,) bin per hour
    n_bins = len(edges) + 1

    # Within-year pooled ladder (all hours this year) — the same-instrument,
    # same-year backfill for an under-covered bin. NOT a cross-year pool.
    pool = _ladder(seg)

    bins: dict[str, dict] = {}
    for b in range(n_bins):
        hrs = set(int(h) for h in np.where(hour_bin == b)[0])
        own = _ladder(seg[seg["hoy"].isin(hrs)])
        if own and own["n_intervals"] >= MIN_BIN_INTERVALS:
            entry = dict(own)
            entry["source"] = "own_bin"
            entry["tranches"] = _tranches(own, TRANCHE_RIGHT_Q)
            entry["tranches_left_edge"] = _tranches(own, TRANCHE_LEFT_Q)
        elif pool:
            entry = dict(pool)
            entry["source"] = "within_year_pool"
            entry["own_bin_intervals"] = int(own.get("n_intervals", 0))
            entry["tranches"] = _tranches(pool, TRANCHE_RIGHT_Q)
            entry["tranches_left_edge"] = _tranches(pool, TRANCHE_LEFT_Q)
        else:
            continue
        bins[f"bin{b}"] = entry

    total_mw = sum(status_mw.values()) or 1.0
    return {
        "_coverage": {
            "n_files": n_files,
            "n_segments": int(len(seg)),
            "status_mw_share": {
                k: round(v / total_mw, 4)
                for k, v in sorted(status_mw.items(), key=lambda kv: -kv[1])
            },
            "within_year_pool": pool,
            # The LP-consumable tranche form of the within-year pool — the
            # same-instrument, same-year backfill an apply-time hour uses when
            # its own net-load bin is absent from ``bins`` (never a cross-year
            # pool). Empty when the year has no segments at all.
            "within_year_pool_tranches": _tranches(pool, TRANCHE_RIGHT_Q)
            if pool
            else [],
        },
        "bins": bins,
    }


def main() -> None:
    """Derive and write the ERCOT storage RT discharge-offer surface JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--verify",
        action="store_true",
        help="reproduce the ercot-161 census reference numbers (2023) and exit",
    )
    args = ap.parse_args()

    if args.verify:
        _verify()
        return

    per_year: dict[str, dict] = {}
    for y in args.years:
        per_year[str(y)] = derive_year(y)
        cov = per_year[str(y)]["_coverage"]
        print(
            f"{y}: {cov['n_segments']} segments from {cov['n_files']} files; "
            f"bins covered {sorted(per_year[str(y)]['bins'])}"
        )
        for b, entry in per_year[str(y)]["bins"].items():
            tp = [t["price"] for t in entry["tranches"]]
            print(
                f"   {b} [{entry['source']}] p10/p30/p50={entry['usd_quantiles']['p10']}"
                f"/{entry['usd_quantiles']['p30']}/{entry['usd_quantiles']['p50']} "
                f"offered {entry['mean_offered_gw']} GW | tranche prices {tp}"
            )

    result = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965); PWRSTR "
                "rows, telemetered ON* with ONTEST excluded, above-LSL segments "
                "capped at HASL, absolute $/MWh clipped to HCAP. 2023 from the "
                "full-year delivery-2023 corpus (data/raw/ercot/SCED/, 315 shards, "
                "the ERCOT-157 landing); 2024/2025 from the committed sample-day "
                "extracts (the RT wall's 2024/2025 basis — full-year 2024/2025 "
                "PWRSTR is not on disk, a disclosed limitation)."
            ),
            "method": (
                "MW-weighted absolute-$ quantile ladder of the discharge-offer "
                "segments per within-year net-load-percentile bin (the shared "
                "NETLOAD_PCT_EDGES geometry). The energy-side headroom only (HASL "
                "nets the AS award), so this is rule-19 clean against the co-opt "
                "reserve owners."
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand − wind − "
                "solar), forward-native — a forecast year's bins regenerate from "
                "its own load+VRE. The conduct is standing (flat across bins), so "
                "it scales with the evolving fleet through the LP's own crossing "
                "depth (FINDING §4)."
            ),
            "population": (
                "ONTEST excluded; ON/ONREG/ONFFRRRS included (online AS-carrying "
                "states whose HASL cap already nets the AS award). Gas-multiple "
                "basis REFUTED for storage (ERCOT-154); absolute $ only."
            ),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "disclosure_quantiles": list(QUANTS),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "year_scoped": (
                "Per-year ladders, NO cross-year pooled fallback (rule 13): each "
                "year uses only its own posted RT offers; a year absent gets NO "
                "surface (the flat battery_dispatch_adder is retained). An "
                "under-covered bin (< %d intervals) borrows that YEAR's all-hours "
                "pooled ladder (within-year, same-instrument), disclosed per bin "
                "via source=within_year_pool." % MIN_BIN_INTERVALS
            ),
            "tranche_construction": {
                "K": len(TRANCHE_WIDTHS),
                "cum_edges": list(TRANCHE_CUM_EDGES),
                "widths": list(TRANCHE_WIDTHS),
                "right_edge_quantiles": list(TRANCHE_RIGHT_Q),
                "left_edge_quantiles": list(TRANCHE_LEFT_Q),
                "primary": "right_edge",
                "note": (
                    "Fixed A PRIORI (ercot-161 precommit discipline); never "
                    "selected on model absorption. Right-edge is the primary "
                    "(conservative rising step); left-edge is the disclosed "
                    "lower-bound variant, not used. p50+ is HCAP-degenerate by "
                    "measurement, so the top tranche is the $5,000 cap block."
                ),
            },
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data update, "
                "never because a residual moved."
            ),
        },
        "years": per_year,
    }
    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")
    _print_year_pair_stability(per_year)


def _print_year_pair_stability(per_year: dict[str, dict]) -> None:
    """Report the p10–p30 toe's year-pair rung stability (the live question)."""
    years = sorted(per_year)
    if len(years) < 2:
        return
    print("\nYear-pair rung stability (own-bin ladders; the p10–p30 toe):")
    for q in ("p10", "p30", "p50"):
        print(f"  {q}:")
        for b in [f"bin{i}" for i in range(len(NETLOAD_PCT_EDGES) + 1)]:
            vals = []
            for y in years:
                e = per_year[y]["bins"].get(b)
                vals.append(
                    e["usd_quantiles"][q]
                    if (e and e.get("source") == "own_bin")
                    else None
                )
            if any(v is not None for v in vals):
                shown = "/".join("—" if v is None else f"{v:g}" for v in vals)
                print(f"    {b}: {shown}   ({', '.join(years)})")


def _verify() -> None:
    """Reproduce the ercot-161 conduct-census reference numbers on 2023."""
    phase0 = REPO / "results/calibration/_ercot161_wall_phase0.json"
    seg, status_mw = _pwrstr_segments(2023)
    total = sum(status_mw.values()) or 1.0
    shares = {
        k: round(v / total, 4)
        for k, v in sorted(status_mw.items(), key=lambda kv: -kv[1])
    }
    print("status MW share:", shares)
    print("  expect ~ ON 0.564 / ONTEST 0.260 / ONREG 0.160 / ONFFRRRS 0.016")
    if phase0.exists():
        top = set(int(h) for h in json.loads(phase0.read_text())["hour_set"]["hours"])
        gap = _ladder(seg[seg["hoy"].isin(top)])
        print("gap-hour ladder (ONTEST excluded):")
        print("  usd_quantiles:", gap["usd_quantiles"])
        print("  mean_offered_gw:", gap["mean_offered_gw"], "(expect 0.711)")
        print(
            "  ge_500 GW:", gap["mean_gw_at_usd_rungs"]["gw_ge_500"], "(expect 0.556)"
        )
    else:
        print(f"(phase0 hour set {phase0} absent — skipping gap-hour cross-check)")


if __name__ == "__main__":
    main()
