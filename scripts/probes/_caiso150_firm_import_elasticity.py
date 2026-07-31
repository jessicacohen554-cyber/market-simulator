"""caiso-150 — design gates for FIRM-BLOCK ELASTICITY (mechanism-matrix §5.2 item 2).

Design-first, kill-before-solve (the caiso-129/140/142/143/144/149 discipline).
**No LP is built and no solver runs** — the one expensive call is the keeper-fleet
reconstruction (``run_calibration.run_year(fleet_only=True)``, the
caiso-131/134/140/142/143 machinery), which composes the real floors without a
matrix.

THE LEVER. ``caiso-143`` §H inverted the export-lane dependency and left exactly
one live prerequisite for lever-queue item 2: **caiso-138 §C firm-block
elasticity** — the question of whether the forced firm-import injection ``F``
must be price-insensitive at all. ``F`` is built by
:func:`market_sim.model.interchange.caiso.inject_caiso_firm_import_selfschedule`
(caiso-77), which floors both firm tranches' ``min_gen`` at their FULL shaped
capability ``pmax × availability`` in **every hour of the year**.

THE IDENTIFICATION GAP THIS PROBE CLOSES. The floor's rule-17 declaration cites
two things: (a) the CPUC D.20-06-028 RA import **must-offer** obligation, and
(b) "the DMM revealed self-scheduled base" of 4.3–5.9 GW. But (b) is an
*inference from realised flow*, not a measurement of bid conduct — it is the
EIA-930 corridor net-import series (``measured_firm_import_shape``), i.e. the
same series that supplies the floor's shape. Nothing in the mechanism's evidence
base measures whether those imports were actually submitted **price-insensitively**.

THE INDEPENDENT SOURCE. CAISO OASIS **Public Bid Data** (``PUB_DAM_GRP``,
tariff §6.5.2.2, 90-day lag) publishes every DAM bid as submitted, including
``RESOURCE_TYPE == "INTERTIE"`` rows carrying ``SELFSCHEDMW`` (price-insensitive
quantity) and full piecewise economic bid curves. That is a direct measurement of
the exact claim the floor makes, and it is independent of **both** inputs the
floor consumes — the DMM RA capacity table (level) and EIA-930 interchange
(shape). Same shape as caiso-149, where CAISO's own DMM decided the session
against the OASIS/CAMPD derives.

GATES.

* §A — the mechanism **as built**: how much energy ``F`` forces, in which hours,
  and its gate exposure (``MECH_FIRM_IMPORT`` is in both ``NON_THERMAL_MECHS``
  and ``MECH_ABLATION_KEPT`` and carries **no ``D4_WINDOWS`` entry**, so the D-4
  off-window-binding check has never run on it).
* §B — the **measured** price-insensitive position from OASIS DAM public bids,
  and the identification WALL it carries: intertie resources classify import vs
  export only by bid-curve monotonicity, and a self-scheduling resource submits
  no curve, so the direction split is unavailable and only a one-sided CEILING
  is measurable.
* §C — the **confrontation**: ``F[t]`` against that ceiling on the model's own
  (month × hod) grid, by year. Deliberately one-sided, so the wall in §B cannot
  overturn the conclusion.

The rule-17 form reading and the identification of a replacement mechanism are
argued in the finding (``FINDING-caiso150-firm-import-elasticity-2026-07-31.md``
§D/§F) from these three sections' numbers; they add no computation of their own
and so carry no section here.

Usage::

    python scripts/probes/_caiso150_firm_import_elasticity.py --sections B
    python scripts/probes/_caiso150_firm_import_elasticity.py            # A, B, C
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
# `scripts.lib.clean_io` (hydro modes, capacity deliverability) imports by
# PACKAGE path, so the repo root must be importable too — without it the fleet
# build degrades silently on some seams and hard-fails on the hydro one.
sys.path.insert(0, str(REPO_ROOT))

HOURS = 8760
YEARS = (2023, 2024, 2025)
KEEPER = REPO_ROOT / "results" / "calibration" / "caiso148_nucavail_B"
BID_ZIPS = REPO_ROOT / "data" / "raw" / "caiso-public-bids" / "zips"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "c7ac314c-7587-584c-8a2c-b9b4ded009a3/scratchpad/caiso150"
)

#: meta.json -> run_year kwarg renames (mirrors the caiso-143 probe).
#:
#: ``coal_prb_sigmoid_overrides`` is NOT a coal key: it is the meta.json name of
#: the GENERIC ``ScenarioConfig`` override channel (``run_year(prb_overrides=)``,
#: the channel ``replay_keeper --set`` writes to). CAISO's three firm-import
#: flags — ``caiso_firm_import_shape`` / ``_selfschedule`` / ``_envelope_clip``
#: — have no CLI flag and no top-level meta key, and reach the solve ONLY
#: through it. Dropping this rename silently rebuilds the fleet with the whole
#: firm must-flow block absent (27.2 TWh in 2024) while every other CAISO
#: mechanism still arms, which looks like a correct fleet.
_META_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
}

#: Raw OASIS columns actually used (the rest are redundant renderings).
#:
#: NOTE the STOP columns: OASIS publishes bids RUN-LENGTH ENCODED — one row
#: covers the whole span over which a resource's bid is unchanged
#: (``TIMEINTERVALSTART_GMT`` .. ``TIMEINTERVALEND_GMT``), spans of 1-24 h.
#: Every row must be expanded to its hour slots before any hourly statistic is
#: taken. (The repo's canonical parser, ``scripts/lib/dam_public_bids/caiso.py``,
#: keys rows by their START stamp only and never expands — see §B's note.)
_RAW_COLS = [
    "STARTDATE",
    "RESOURCE_TYPE",
    "RESOURCEBID_SEQ",
    "TIMEINTERVALSTART_GMT",
    "TIMEINTERVALEND_GMT",
    "MARKETPRODUCTTYPE",
    "SELFSCHEDMW",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTOP_GMT",
    "SCH_BID_XAXISDATA",
    "SCH_BID_Y1AXISDATA",
]


# --------------------------------------------------------------------------- #
# shared loaders
# --------------------------------------------------------------------------- #
def fleet_state(year: int) -> dict:
    """Reconstruct the keeper's fleet for ``year`` (no LP, no solve)."""
    import inspect

    from run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def _parse_bid_day(path: Path) -> pd.DataFrame:
    """Reduce one PUB_BID_DAM zip to per-(intertie resource, HOUR) records.

    Run-length ranges are expanded to their hour slots first (see ``_RAW_COLS``),
    then each (resource, hour) is summarized as:

    ``ss_mw``       self-scheduled MW (price-insensitive quantity), 0 if none;
    ``econ_mw``     top MW step of the economic bid curve, 0 if none;
    ``mw_le0``      cumulative MW the curve offers at a price **at or below
                    $0/MWh** — the second half of the floor's own definition of
                    price-taking conduct ("self-scheduled OR bid at/below
                    $0/MWh"), which is an ECONOMIC bid and so would otherwise be
                    invisible in ``ss_mw``;
    ``curve``       ``import`` / ``export`` / ``flat`` from the curve's own
                    price-vs-MW monotonicity (supply offers rise, demand bids
                    fall), ``""`` when the resource-hour carries no curve.
    """
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            df = pd.read_csv(fh, usecols=_RAW_COLS, low_memory=False)
    df = df[
        (df["RESOURCE_TYPE"] == "INTERTIE") & (df["MARKETPRODUCTTYPE"] == "EN")
    ].copy()
    df = df[df["RESOURCEBID_SEQ"].notna()]
    if df.empty:
        return pd.DataFrame(
            columns=["res", "utc", "ss_mw", "econ_mw", "mw_le0", "curve"]
        ).astype({"res": "int64"})

    is_seg = df["SCH_BID_XAXISDATA"].notna()
    seg = df[is_seg]
    ss = df[~is_seg & df["SELFSCHEDMW"].notna()]

    # --- self-schedule: expand each RLE range, sum per (resource, hour) ---
    ss_rows = _expand(
        ss["RESOURCEBID_SEQ"].astype("int64").to_numpy(),
        ss["TIMEINTERVALSTART_GMT"],
        ss["TIMEINTERVALEND_GMT"],
        ss["SELFSCHEDMW"].astype("float64").to_numpy(),
    )
    ss_h = (
        ss_rows.groupby(["res", "utc"], sort=False)["val"].sum().rename("ss_mw")
        if len(ss_rows)
        else pd.Series(dtype="float64", name="ss_mw")
    )

    # --- curves: classify per (resource, range), then expand ---
    if len(seg):
        key = ["RESOURCEBID_SEQ", "SCH_BID_TIMEINTERVALSTART_GMT"]
        s = seg.sort_values(key + ["SCH_BID_XAXISDATA"], kind="mergesort")
        g = s.groupby(key, sort=False)
        le0 = s["SCH_BID_XAXISDATA"].where(s["SCH_BID_Y1AXISDATA"] <= 0.0)
        summary = pd.DataFrame(
            {
                "top_mw": g["SCH_BID_XAXISDATA"].max(),
                "mw_le0": le0.groupby([s[k] for k in key], sort=False).max(),
                "inc": g["SCH_BID_Y1AXISDATA"].apply(
                    lambda v: bool((np.diff(v.to_numpy()) > 0).any())
                ),
                "dec": g["SCH_BID_Y1AXISDATA"].apply(
                    lambda v: bool((np.diff(v.to_numpy()) < 0).any())
                ),
                "stop": g["SCH_BID_TIMEINTERVALSTOP_GMT"].first(),
            }
        ).reset_index()
        summary["mw_le0"] = summary["mw_le0"].fillna(0.0)
        summary["curve"] = np.where(
            summary["inc"] & ~summary["dec"],
            "import",
            np.where(summary["dec"] & ~summary["inc"], "export", "flat"),
        )
        seg_rows = _expand(
            summary["RESOURCEBID_SEQ"].astype("int64").to_numpy(),
            summary["SCH_BID_TIMEINTERVALSTART_GMT"],
            summary["stop"],
            summary["top_mw"].astype("float64").to_numpy(),
            extra=summary["curve"].to_numpy(),
            extra2=summary["mw_le0"].astype("float64").to_numpy(),
        )
        seg_h = seg_rows.groupby(["res", "utc"], sort=False).agg(
            econ_mw=("val", "sum"),
            mw_le0=("extra2", "sum"),
            curve=("extra", "first"),
        )
    else:
        seg_h = pd.DataFrame(columns=["econ_mw", "mw_le0", "curve"])

    out = pd.concat([ss_h, seg_h], axis=1).reset_index()
    if "index" in out.columns:  # empty-frame edge case
        out = out.drop(columns=["index"])
    for col, fill in (
        ("ss_mw", 0.0),
        ("econ_mw", 0.0),
        ("mw_le0", 0.0),
        ("curve", ""),
    ):
        if col not in out.columns:
            out[col] = fill
        out[col] = out[col].fillna(fill)
    return out[["res", "utc", "ss_mw", "econ_mw", "mw_le0", "curve"]]


def _expand(
    res: np.ndarray,
    start: pd.Series,
    stop: pd.Series,
    val: np.ndarray,
    extra: np.ndarray | None = None,
    extra2: np.ndarray | None = None,
) -> pd.DataFrame:
    """Expand run-length-encoded [start, stop) rows into one row per hour."""
    if not len(res):
        return pd.DataFrame(columns=["res", "utc", "val", "extra", "extra2"])
    s = pd.to_datetime(pd.Series(start).to_numpy(), utc=True, format="mixed")
    e = pd.to_datetime(pd.Series(stop).to_numpy(), utc=True, format="mixed")
    span = np.clip(((e - s).total_seconds() // 3600).to_numpy().astype(int), 1, None)
    rep = np.repeat(np.arange(len(res)), span)
    offs = np.concatenate([np.arange(n) for n in span]) if len(span) else np.array([])
    return pd.DataFrame(
        {
            "res": res[rep],
            "utc": s.to_numpy()[rep] + pd.to_timedelta(offs, unit="h"),
            "val": val[rep],
            "extra": (extra[rep] if extra is not None else ""),
            "extra2": (extra2[rep] if extra2 is not None else 0.0),
        }
    )


def load_bids(refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) every fetched daily zip as per-(resource, hour) rows."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE / "intertie_hourly.parquet"
    files = sorted(BID_ZIPS.glob("*_PUB_BID_DAM_v3_csv.zip"))
    frames: list[pd.DataFrame] = []
    if cache_file.exists() and not refresh:
        cached = pd.read_parquet(cache_file)
        have = set(cached["day"].unique())
        files = [f for f in files if f.name[:8] not in have]
        if not files:
            return cached
        frames.append(cached)
    for f in files:
        d = _parse_bid_day(f)
        if not d.empty:
            d["day"] = f.name[:8]
            frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(cache_file, index=False)
    return out


def classify_interties(bids: pd.DataFrame) -> pd.Series:
    """Classify each masked intertie resource as import / export / unknown.

    A CAISO **import** intertie submits a SUPPLY offer (price non-decreasing in
    MW); an **export** submits a DEMAND bid (price non-increasing). The
    classification is longitudinal over the whole corpus — the masked
    ``RESOURCEBID_SEQ`` is persistent across days and years (verified
    2026-07-16, the fetcher's README) — so a resource that only self-schedules
    on some days is still classified from the days it bids economically.
    Resources that NEVER submit an economic curve stay ``unknown`` and are
    reported as an explicit coverage bound, never imputed.
    """
    seen = bids[bids["curve"].isin(("import", "export"))]
    if seen.empty:
        return pd.Series(dtype="object")
    return seen.groupby("res")["curve"].agg(lambda s: s.value_counts().idxmax())


def bids_hourly(bids: pd.DataFrame, votes: pd.Series) -> pd.DataFrame:
    """Aggregate the corpus to one row per (model-clock) hour.

    Clock: OASIS stamps are exact UTC, converted to US/Pacific wall time — the
    model's own clock (``envelopes._caiso_interchange_model_clock`` exists only
    to undo an EIA-930 publication lag, which this source does not carry).
    """
    b = bids.copy()
    b["cls"] = b["res"].map(votes).fillna("unknown")
    local = pd.to_datetime(b["utc"], utc=True).dt.tz_convert("US/Pacific")
    b["ts"] = local.dt.tz_localize(None)
    b["year"] = local.dt.year
    b["month"] = local.dt.month
    b["hod"] = local.dt.hour
    keys = ["ts", "year", "month", "hod"]
    ss_h = b.pivot_table(
        index=keys, columns="cls", values="ss_mw", aggfunc="sum", fill_value=0.0
    ).add_prefix("ss_")
    econ_h = b.pivot_table(
        index=keys, columns="cls", values="econ_mw", aggfunc="sum", fill_value=0.0
    ).add_prefix("econ_")
    le0_h = b.pivot_table(
        index=keys, columns="cls", values="mw_le0", aggfunc="sum", fill_value=0.0
    ).add_prefix("le0_")
    out = ss_h.join(econ_h, how="outer").join(le0_h, how="outer").fillna(0.0)
    out["ss_all"] = out[[c for c in out.columns if c.startswith("ss_")]].sum(axis=1)
    # The floor's OWN definition of price-taking conduct is "self-scheduled OR
    # bid at/below $0/MWh", so the measured price-insensitive IMPORT position is
    # bounded above by (all self-schedule, both directions) + (import-classified
    # economic MW offered at <= $0). Deliberately generous on both limbs.
    out["pi_upper"] = out["ss_all"] + out.get("le0_import", 0.0)
    return out.reset_index()


# --------------------------------------------------------------------------- #
# §A — the mechanism as built
# --------------------------------------------------------------------------- #
def section_a() -> dict:
    """What ``F`` forces, in which hours, and which gates can see it."""
    from market_sim.data.floor_mechanisms import (
        MECH_ABLATION_KEPT,
        MECH_FIRM_IMPORT,
        NON_THERMAL_MECHS,
    )
    from market_sim.model.interchange.caiso import (
        CAISO_FIRM_IMPORT_TRANCHES,
        CAISO_PER_HUB_IMPORT_ZONES,
    )

    print("\n" + "=" * 78)
    print("§A  the firm must-flow block AS BUILT (keeper fleet, no LP)")
    print("=" * 78)

    zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    out: dict = {"years": {}}
    for year in YEARS:
        st = fleet_state(year)
        fa = st["fleet_arrays"] if isinstance(st, dict) else st.fleet_arrays
        mg = fa.min_gen
        if mg is None:
            mg = np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, HOURS))
        total = np.zeros(HOURS)
        rows = []
        for r, uid in enumerate(fa.unit_ids):
            z = next((zz for zz in zones if str(uid).startswith(f"{zz}_")), None)
            if z is None:
                continue
            name = str(uid)[len(z) + 1 :]
            if name not in CAISO_FIRM_IMPORT_TRANCHES:
                continue
            floor = np.clip(np.asarray(mg[r, :], dtype=float), 0.0, None)
            shaped = float(fa.pmax[r]) * fa.availability[r, :]
            total += floor
            rows.append(
                {
                    "uid": str(uid),
                    "twh": float(floor.sum() / 1e6),
                    "mean_mw": float(floor.mean()),
                    "hours_forced": int((floor > 1e-9).sum()),
                    "mustflow_hours": int(
                        ((floor >= shaped - 1e-6) & (shaped > 1e-9)).sum()
                    ),
                }
            )
        hod = total.reshape(-1, 24).mean(axis=0)
        out["years"][year] = {
            "rows": rows,
            "total_twh": float(total.sum() / 1e6),
            "mean_mw": float(total.mean()),
            "hours_forced": int((total > 1e-9).sum()),
            "hod_mw": hod.tolist(),
            "F": total,
        }
        print(f"\n  {year}:")
        for d in rows:
            print(
                f"    {d['uid']:28s} {d['twh']:7.3f} TWh  mean {d['mean_mw']:7.1f} MW  "
                f"forced {d['hours_forced']:5d} h  must-flow {d['mustflow_hours']:5d} h"
            )
        print(
            f"    {'TOTAL':28s} {out['years'][year]['total_twh']:7.3f} TWh  "
            f"mean {out['years'][year]['mean_mw']:7.1f} MW  "
            f"forced {out['years'][year]['hours_forced']:5d} h of {HOURS}"
        )
        print(
            "    hod mean MW: "
            + " ".join(f"{v:5.0f}" for v in hod[::3])
            + "   (h0,3,6,...,21)"
        )

    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(
        CACHE / "forced.npz",
        **{str(y): out["years"][y]["F"] for y in YEARS},
    )
    exempt_d2 = MECH_FIRM_IMPORT in NON_THERMAL_MECHS
    exempt_abl = MECH_FIRM_IMPORT in MECH_ABLATION_KEPT
    d4 = _has_d4_window()
    print("\n  gate exposure of MECH_FIRM_IMPORT:")
    print(f"    D-2 exempt (NON_THERMAL_MECHS):   {exempt_d2}")
    print(f"    ablation-kept (MECH_ABLATION_KEPT): {exempt_abl}")
    print(f"    D4_WINDOWS entry present:           {d4}")
    print(
        "    => the floor is invisible to the C8 forced-share budget AND to the\n"
        "       D-4 off-window-binding check. No gate has ever window-tested it."
    )
    out["gates"] = {"d2_exempt": exempt_d2, "ablation_kept": exempt_abl, "d4": d4}
    return out


def _has_d4_window() -> bool:
    """True when ``legitimacy_diagnostics.D4_WINDOWS`` declares firm_import."""
    from legitimacy_diagnostics import D4_WINDOWS  # type: ignore

    from market_sim.data.floor_mechanisms import MECH_FIRM_IMPORT

    return any(k[0] == MECH_FIRM_IMPORT for k in D4_WINDOWS)


# --------------------------------------------------------------------------- #
# §B — the measured price-insensitive import position
# --------------------------------------------------------------------------- #
def section_b(refresh: bool = False) -> dict:
    """Measure hourly self-scheduled INTERTIE import MW from OASIS DAM bids."""
    print("\n" + "=" * 78)
    print("§B  measured price-insensitive import (OASIS PUB_BID_DAM, INTERTIE/EN)")
    print("=" * 78)

    bids = load_bids(refresh=refresh)
    votes = classify_interties(bids)
    days = bids["day"].nunique()
    print(f"\n  corpus: {days} trade days, {len(bids):,} (resource x hour) records")
    print(f"  resources: {bids['res'].nunique()} masked seqs")
    print(f"    classified import: {(votes == 'import').sum()}")
    print(f"    classified export: {(votes == 'export').sum()}")
    unk = bids.loc[~bids["res"].isin(votes.index), "res"].nunique()
    print(f"    unclassified (never bid an economic curve): {unk}")

    hourly = bids_hourly(bids, votes)
    ss_cols = [c for c in hourly.columns if c.startswith("ss_") and c != "ss_all"]
    tot_ss = hourly[ss_cols].sum().sort_values(ascending=False)
    print("\n  self-scheduled MWh by class (corpus total):")
    for k, v in tot_ss.items():
        print(f"    {k:16s} {v / 1e6:10.3f} TWh")
    share_unk = (
        float(tot_ss.get("ss_unknown", 0.0)) / float(tot_ss.sum())
        if tot_ss.sum()
        else 0.0
    )
    print(f"  unclassified share of all self-schedule MW: {share_unk * 100:.2f} %")
    print(
        "\n  => DIRECTION IS NOT IDENTIFIABLE for the self-scheduling population:\n"
        "     a resource that self-schedules submits NO economic curve, and the\n"
        "     masked feed carries no direction field (PRODUCTBID_DESC /\n"
        "     MARKETPRODUCT_DESC are entirely NaN on INTERTIE rows). So the\n"
        "     measurement that IS available is the UPPER BOUND ss_all =\n"
        "     import + export self-schedule, unsigned:  ss_all[t] >= SS_import[t]."
    )

    print("\n  TOTAL intertie self-schedule ss_all by hour-of-day (MW, corpus mean):")
    prof = hourly.groupby("hod")["ss_all"].mean()
    for lo in (0, 8, 16):
        print(
            f"    h{lo:02d}-{lo + 7:02d}  "
            + " ".join(f"{prof.get(h, 0.0):6.0f}" for h in range(lo, lo + 8))
        )
    print(
        f"\n  ss_all: mean {hourly['ss_all'].mean():.0f} MW   "
        f"p50 {hourly['ss_all'].median():.0f}   "
        f"min {hourly['ss_all'].min():.0f}   max {hourly['ss_all'].max():.0f}"
    )
    return {"hourly": hourly, "votes": votes, "unclassified_share": share_unk}


# --------------------------------------------------------------------------- #
# §C — the confrontation, on the model's own (month x hod) bucketing
# --------------------------------------------------------------------------- #
def section_c(hourly: pd.DataFrame) -> dict:
    """Model-forced ``F`` vs the measured price-insensitive ceiling.

    Compared on the model's OWN (month x hod) grid — the bucketing
    ``measured_firm_import_shape`` uses to build the floor's shape — because the
    bid corpus samples days while the model runs every hour.

    The comparison is deliberately ONE-SIDED and direction-free. ``ss_all``
    sums intertie self-schedules in BOTH directions, and ``pi_upper`` adds the
    import-classified economic MW bid at or below $0/MWh, so
    ``pi_upper >= (true price-insensitive IMPORT position)`` in every hour
    whatever the unidentifiable import/export split turns out to be. Any hour
    with ``F > pi_upper`` therefore forces more price-insensitive import than
    CAISO's entire measured price-insensitive intertie position — a conclusion
    the masking cannot overturn.
    """
    print("\n" + "=" * 78)
    print("§C  model-forced F vs the measured price-insensitive CEILING")
    print("=" * 78)

    forced = np.load(CACHE / "forced.npz")
    meas = hourly.groupby(["month", "hod"])[["ss_all", "pi_upper"]].mean()
    out: dict = {}
    for year in YEARS:
        F = forced[str(year)]
        idx = pd.date_range(f"{year}-01-01", periods=len(F), freq="h")
        grid = pd.DataFrame({"F": F, "month": idx.month, "hod": idx.hour})
        j = grid.join(meas, on=["month", "hod"])
        cov = j["pi_upper"].notna()
        over = cov & (j["F"] > j["pi_upper"])
        excess = float((j.loc[over, "F"] - j.loc[over, "pi_upper"]).sum() / 1e6)
        out[year] = {
            "covered_hours": int(cov.sum()),
            "over_hours": int(over.sum()),
            "over_share": float(over.sum() / max(1, cov.sum())),
            "excess_twh": excess,
            "forced_twh": float(j.loc[cov, "F"].sum() / 1e6),
        }
        print(
            f"\n  {year}: {int(cov.sum())} h with bid coverage; "
            f"F > measured ceiling in {int(over.sum())} h "
            f"({100 * over.sum() / max(1, cov.sum()):.1f} %)"
        )
        print(
            f"    forced energy above the measured ceiling: {excess:.3f} TWh "
            f"of {out[year]['forced_twh']:.3f} TWh forced "
            f"({100 * excess / max(1e-9, out[year]['forced_twh']):.1f} %)"
        )
        prof = j[cov].groupby("hod")[["F", "pi_upper", "ss_all"]].mean()
        print(f"    {'hod':>4s} {'F':>8s} {'ceiling':>9s} {'ratio':>7s}")
        for h in range(0, 24, 2):
            if h not in prof.index:
                continue
            r = prof.loc[h]
            print(
                f"    {h:4d} {r['F']:8.0f} {r['pi_upper']:9.0f} "
                f"{r['F'] / max(1e-9, r['pi_upper']):7.2f}"
            )
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sections", default="ABC", help="subset of section letters")
    ap.add_argument("--refresh", action="store_true", help="re-parse every zip")
    args = ap.parse_args(argv)
    if "A" in args.sections:
        section_a()
    res_b = section_b(refresh=args.refresh) if "B" in args.sections else None
    if "C" in args.sections:
        if res_b is None:
            res_b = section_b(refresh=args.refresh)
        section_c(res_b["hourly"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
