"""miso-202 phase 0 — the ADJACENT-WINDOW BOUNDARY-DAY DOUBLE-COUNT: how big, and where?

The charter (miso-202, queue item 1) inherits its object from FINDING-miso201 section 7
item 1: with the ST-side numerator aligned, the adjacent-window boundary-day double-count
is the ONLY mechanism still producing steam overflow, at four measured bins (170, 1104,
2070, 6639).

**THE DEFECT.** ``outages.unit_outage_event_window`` reconstructs a day-granular row as
the half-open window ``[outage_start, outage_end + 1 day)``. Two windows of the SAME unit
where the first row's ``outage_end`` equals (or precedes by less than a day) the second
row's ``outage_start`` therefore both cover that boundary day, and
``_unit_outage_factors_from_events`` SUMS row shares rather than unioning them. The unit's
capacity is subtracted TWICE for 24 h: the bin's pre-clip removed share carries
``2 x unit_cap / plant_cap`` on a day the unit can be at most 100 % out.

**WHY THIS PROBE EXISTS AND WHAT IT MUST NOT ASSUME.** FINDING-miso201 met the defect only
where it OVERFLOWED a steam bin, and sized it there as "small (24-72 h/yr per bin)". That
is the view from a steam-scoped instrument. The accumulator is class-agnostic, so the
census here is run over EVERY bin and EVERY layer that shares it, and the magnitude is
measured post-clip against the fleet's own LP capacity rather than counted in bin-hours.
An overflowing cell is exactly the case where the double-count is INERT (the correct
answer is 0.0 and the clip already delivers it); the live cases are the ones that never
overflow, which is why a census scoped to overflow could not see them.

Measurements
------------
* **N-1 REPRODUCTION (a gate, not a report).** The production entry points return
  ``clip(1 - v, 0, 1)`` and so HIDE the pre-clip share ``v``. ``v`` is reconstructed here
  from the production code path -- same ``cap`` denominator, same routing, same
  fleet-status filter, same ``st_capacity_basis`` pairmap, same window reconstruction --
  and every reconstructed bin is ASSERTED to reproduce the production array EXACTLY. A
  reconstruction that does not reproduce production measures nothing (the charter's
  instrument note; the discipline miso-200/201 applied on 121 / 988 bins).
* **N-2 THE OVERLAP CENSUS.** Every same-unit window pair whose reconstructed windows
  intersect, per layer and year, with the intersection length. Reported against the
  production row filters (``duration_days >= 5`` for the std layer, ``< 5`` + COAL for the
  short layer), NOT the raw CSV.
* **N-3 THE COUNTERFACTUAL (the deliverable).** The availability a PER-UNIT CLIP produces
  -- each unit's cumulative removed MW clipped at its own capacity before the bin sums --
  integrated against the bin's LP capacity, in GWh, per year, per bin, per class.
  Positive = capability the double-count wrongly removes.
* **N-4 WHERE IT LANDS (the charter's own question).** The month, the Jun-Sep share and
  the top-load-decile share of the N-3 delta. MISO's open rubric failure is C3a-2025
  summer scarcity, and a repair that RESTORES availability moves that residual the wrong
  way; this measures how much of the restoration actually falls in the hours C3a scores,
  so the A/B's K-1 risk cells are named from measurement rather than from expectation.
* **N-5 THE MAXGEN TWIN.** The maxgen layer does NOT share the std accumulator (measured
  ``derate_mw`` over hour-granular windows, class-agnostic, no status filter). It gets its
  own faithful reconstruction and its own overlap census, so the scope decision is
  measured rather than inherited.

Nothing here is fitted and nothing is tuned: every quantity is either the committed
extract, the committed fleet, or the production code's own output.

Run:  PYTHONPATH=src python3 scripts/probes/_miso202_boundary_day_phase0.py
Writes: results/calibration/_miso202_boundary_day_phase0.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.data import outages
from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760

# The keeper recipe (results/calibration/miso201_stbasis_B/run_config.json).
# Read off the committed keeper, never chosen here.
KEEPER = dict(
    cc_steam_part_reclass=False,  # cc_steam_part_capacity is a separate offer-side flag
    cc_nameplate_basis=False,  # unit_outage_lp_capacity_basis
    fleet_status_scope=True,  # unit_outage_fleet_status_scope
    mixed_gas_routing=True,  # unit_outage_mixed_gas_routing
    per_unit_crosswalk=False,  # campd_per_unit_attribution
    st_capacity_basis=True,  # unit_outage_st_capacity_basis (miso-201)
    short_windows=True,  # unit_outage_short_windows
    maxgen_events=True,  # unit_outage_maxgen_events
    partial_windows=False,  # unit_partial_outage_windows
    layup_mask=True,  # mustrun_layup_window_mask
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_miso202_boundary_day_phase0.json"


# --------------------------------------------------------------------------
# The production frames, loaded exactly as production loads them
# --------------------------------------------------------------------------
def std_frame() -> pd.DataFrame:
    """The >= 5-day full-stop frame, with the production loader and filter."""
    path = outages.unit_outage_csv_for_iso(
        ISO, KEEPER["mixed_gas_routing"], KEEPER["per_unit_crosswalk"], False
    )
    df = outages._load_unit_outage_events(path, ISO)
    return df[df["duration_days"] >= outages.UNIT_OUTAGE_MIN_DAYS]


def short_frame() -> pd.DataFrame:
    """The < 5-day COAL frame, with the production filter."""
    path = outages.unit_outage_short_csv_for_iso(ISO)
    df = pd.read_csv(path)
    return df[
        (df["duration_days"] < outages.UNIT_OUTAGE_MIN_DAYS)
        & (df["plant_group"] == "COAL")
    ]


def layup_frame() -> pd.DataFrame:
    """The economic-lay-up frame, with the production filter."""
    path = outages.unit_layup_csv_for_iso(ISO)
    df = pd.read_csv(path)
    return df[df["duration_days"] >= outages.UNIT_OUTAGE_MIN_DAYS]


def maxgen_frame() -> pd.DataFrame:
    """The declared-event-window (maxgen) frame."""
    path = outages.unit_outage_maxgen_csv_for_iso(ISO, KEEPER["mixed_gas_routing"])
    return pd.read_csv(path)


# --------------------------------------------------------------------------
# Reconstruction of the shared accumulator, line for line
# --------------------------------------------------------------------------
def reconstruct(df: pd.DataFrame, year: int, cap: dict, st_pairmap: dict) -> dict:
    """Return per-bin ``{"sum": v, "units": {unit_id: (removed_mw_arr, ucap)}}``.

    Reproduces ``outages._unit_outage_factors_from_events`` for the non-ERCOT
    branch (production returns ``clip(1 - v, 0, 1)``, which N-1 asserts against),
    additionally recording each unit's own cumulative removed MW so the per-unit
    clip counterfactual can be built without re-reading the frame.
    """
    has_derate = "derate_factor" in df.columns
    has_hours = outages._has_hour_grain(df)
    status_idx = (
        outages._fleet_status_index(ISO) if KEEPER["fleet_status_scope"] else None
    )
    out: dict = {}
    for r in df.itertuples(index=False):
        tgt = outages._generic_unit_outage_target(
            int(r.facility_id),
            r.unit_id,
            r.plant_group,
            per_unit_crosswalk=KEEPER["per_unit_crosswalk"],
        )
        if tgt is None or tgt not in cap:
            continue
        if status_idx is not None:
            st = status_idx.get(int(r.facility_id), {}).get(
                str(r.unit_id).strip().upper()
            )
            if st is not None and st != "OP":
                continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        aligned = st_pairmap.get((tgt[0], tgt[1], str(r.unit_id)))
        if aligned is not None:
            ucap = aligned
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        w_start, w_stop = outages.unit_outage_event_window(r, has_hours)
        mask = outages.outage_hour_mask(w_start, w_stop, year, HOURS)
        if not mask.any():
            continue
        cell = out.setdefault(tgt, {"sum": np.zeros(HOURS), "units": {}})
        cell["sum"][mask] += removed_frac * float(ucap) / cap[tgt]
        uid = str(r.unit_id)
        u = cell["units"].setdefault(uid, {"mw": np.zeros(HOURS), "cap": 0.0})
        u["mw"][mask] += removed_frac * float(ucap)
        u["cap"] = max(u["cap"], float(ucap))
    return out


def reconstruct_maxgen(df: pd.DataFrame, year: int, cap: dict) -> dict:
    """``reconstruct``'s maxgen twin — a SEPARATE accumulator, faithfully.

    ``unit_outage_maxgen_derate_factors`` does NOT share the std accumulator: its
    rows carry a measured ``derate_mw`` (removed MW, not a unit capacity) over an
    hour-granular half-open ``[window_start, window_end)``, it is class-agnostic
    (no CT exclusion) and it applies no fleet-status filter. Reproducing it with
    the std accumulator would silently measure the wrong object.
    """
    out: dict = {}
    for r in df.itertuples(index=False):
        code = int(r.facility_id)
        g = (
            ""
            if r.plant_group is None
            or (isinstance(r.plant_group, float) and np.isnan(r.plant_group))
            else str(r.plant_group)
        )
        if code in outages._FLEET_GROUP_OVERRIDE:
            tgt = (code, outages._FLEET_GROUP_OVERRIDE[code])
        elif not g or g == "OTHER":
            continue
        else:
            tgt = (code, g)
        if tgt not in cap:
            continue
        removed = float(r.derate_mw)
        if pd.isna(removed) or not removed > 0.0:
            continue
        mask = outages.outage_hour_mask(r.window_start, r.window_end, year, HOURS)
        if not mask.any():
            continue
        cell = out.setdefault(tgt, {"sum": np.zeros(HOURS), "units": {}})
        cell["sum"][mask] += removed / cap[tgt]
        uid = str(r.unit_id)
        u = cell["units"].setdefault(uid, {"mw": np.zeros(HOURS), "cap": 0.0})
        u["mw"][mask] += removed
    return out


# --------------------------------------------------------------------------
# N-2: the overlap census
# --------------------------------------------------------------------------
def maxgen_overlap_census(df: pd.DataFrame) -> dict:
    """The maxgen layer's own overlap census — its windows are already hourly.

    Separate from :func:`overlap_census` because the maxgen frame carries
    ``[window_start, window_end)`` directly rather than the day-granular
    ``outage_start``/``outage_end`` pair the reconstruction inflates, so it
    cannot have a boundary-DAY defect by construction. Measured rather than
    assumed: a same-unit overlap here would be a different defect.
    """
    series: dict = defaultdict(list)
    for r in df.itertuples(index=False):
        series[(int(r.facility_id), str(r.unit_id), str(r.plant_group))].append(
            (pd.Timestamp(r.window_start), pd.Timestamp(r.window_end), float(r.derate_mw))
        )
    pairs = []
    for key, ws in series.items():
        ws.sort(key=lambda t: t[0])
        for a, b in zip(ws, ws[1:], strict=False):
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi > lo:
                pairs.append(
                    {
                        "plant": key[0],
                        "unit": key[1],
                        "group": key[2],
                        "overlap_start": str(lo),
                        "overlap_hours": (hi - lo).total_seconds() / 3600.0,
                    }
                )
    return {
        "layer": "maxgen",
        "n_unit_series": len(series),
        "n_overlapping_pairs": len(pairs),
        "pairs": pairs[:50],
    }


def overlap_census(df: pd.DataFrame, layer: str) -> dict:
    """Same-unit window pairs whose reconstructed windows intersect.

    Grouped by ``(facility_id, unit_id, plant_group)`` — the identity the
    accumulator keys a removal on — and measured on the RECONSTRUCTED windows
    ``unit_outage_event_window`` produces, not on the raw date columns, so the
    census sees exactly what the accumulator sees.
    """
    has_hours = outages._has_hour_grain(df)
    series: dict = defaultdict(list)
    for r in df.itertuples(index=False):
        w0, w1 = outages.unit_outage_event_window(r, has_hours)
        series[(int(r.facility_id), str(r.unit_id), str(r.plant_group))].append(
            (w0, w1, float(r.unit_capacity_mw) if "unit_capacity_mw" in df.columns else 0.0)
        )
    pairs: list[dict] = []
    for key, ws in series.items():
        ws.sort(key=lambda t: t[0])
        for a, b in zip(ws, ws[1:], strict=False):
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi > lo:
                pairs.append(
                    {
                        "plant": key[0],
                        "unit": key[1],
                        "group": key[2],
                        "overlap_start": str(lo),
                        "overlap_hours": (hi - lo).total_seconds() / 3600.0,
                        "unit_mw": a[2],
                    }
                )
    by_year: dict = defaultdict(lambda: {"pairs": 0, "hours": 0.0})
    hist: dict = defaultdict(int)
    for p in pairs:
        y = int(p["overlap_start"][:4])
        by_year[y]["pairs"] += 1
        by_year[y]["hours"] += p["overlap_hours"]
        hist[p["overlap_hours"]] += 1
    return {
        "layer": layer,
        "n_unit_series": len(series),
        "n_overlapping_pairs": len(pairs),
        "overlap_hours_histogram": {str(k): v for k, v in sorted(hist.items())},
        "by_year": {
            str(y): dict(v) for y, v in sorted(by_year.items()) if 2019 <= y <= 2026
        },
        "distinct_bins": sorted({(p["plant"], p["group"]) for p in pairs}),
    }


# --------------------------------------------------------------------------
# N-3 / N-4: the counterfactual and where it lands
# --------------------------------------------------------------------------
def per_unit_clipped(cell: dict, cap_mw: float) -> np.ndarray:
    """Availability under the PER-UNIT CLIP: each unit at most 100 % out."""
    v = np.zeros(HOURS)
    for u in cell["units"].values():
        ucap = u["cap"]
        if ucap <= 0.0:
            continue
        v += np.minimum(u["mw"], ucap) / cap_mw
    return np.clip(1.0 - v, 0.0, 1.0)


def main() -> None:
    cap = outages._iso_plant_capacity(
        ISO, KEEPER["cc_steam_part_reclass"], KEEPER["cc_nameplate_basis"]
    )
    iso_config = get_iso_config(ISO)
    fleet = load_fleet_from_csv(
        ISO, iso_config, cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"]
    ) + load_retired_within_window(ISO, iso_config)
    bin_class = {}
    for g in fleet:
        code = int(g.plant_code)
        if code > 0 and g.plant_group:
            bin_class[(code, str(g.plant_group))] = str(g.plant_group)

    frames = {
        "std5d": std_frame(),
        "short": short_frame(),
        "layup": layup_frame(),
    }
    maxgen = maxgen_frame()

    report: dict = {
        "iso": ISO,
        "years": list(YEARS),
        "keeper_args": KEEPER,
        "extracts": {
            "std5d": str(
                outages.unit_outage_csv_for_iso(
                    ISO, KEEPER["mixed_gas_routing"], KEEPER["per_unit_crosswalk"], False
                ).relative_to(REPO)
            ),
            "short": str(outages.unit_outage_short_csv_for_iso(ISO).relative_to(REPO)),
            "layup": str(outages.unit_layup_csv_for_iso(ISO).relative_to(REPO)),
            "maxgen": str(
                outages.unit_outage_maxgen_csv_for_iso(
                    ISO, KEEPER["mixed_gas_routing"]
                ).relative_to(REPO)
            ),
        },
        "n1_reproduction": {},
        "n2_overlap_census": {},
        "n3_counterfactual": {"by_year": {}, "bins": []},
        "n4_where_it_lands": {},
        "n5_maxgen": {},
    }

    # ---- N-2 --------------------------------------------------------------
    for name, df in frames.items():
        report["n2_overlap_census"][name] = overlap_census(df, name)
    report["n5_maxgen"]["overlap_census"] = maxgen_overlap_census(maxgen)

    # ---- N-1 + N-3 + N-4 --------------------------------------------------
    n1 = {"checked": 0, "mismatches": []}
    delta_by_year: dict = {}
    bin_rows: dict = defaultdict(lambda: defaultdict(float))
    hourly_delta: dict = {}

    for year in YEARS:
        st_pairmaps = {}
        for name, df in frames.items():
            st_pairmaps[name] = (
                outages._st_basis_pairmap(
                    df, cap, ISO, KEEPER["cc_steam_part_reclass"]
                )
                if KEEPER["st_capacity_basis"]
                else {}
            )
        prod = {
            "std5d": outages.unit_outage_derate_factors(
                year,
                HOURS,
                outages.BINS_CSV_DEFAULT,
                iso=ISO,
                cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
                cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
                fleet_status_scope=KEEPER["fleet_status_scope"],
                st_capacity_basis=KEEPER["st_capacity_basis"],
                mixed_gas_routing=KEEPER["mixed_gas_routing"],
                per_unit_crosswalk=KEEPER["per_unit_crosswalk"],
            ),
            "short": outages.unit_outage_short_derate_factors(
                year,
                HOURS,
                outages.BINS_CSV_DEFAULT,
                iso=ISO,
                cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
                cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
                fleet_status_scope=KEEPER["fleet_status_scope"],
                st_capacity_basis=KEEPER["st_capacity_basis"],
            ),
            "layup": {
                k: 1.0 - v
                for k, v in outages.unit_layup_removed_fractions(
                    year,
                    HOURS,
                    outages.BINS_CSV_DEFAULT,
                    iso=ISO,
                    cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
                    cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
                    st_capacity_basis=KEEPER["st_capacity_basis"],
                ).items()
            },
        }
        year_delta = defaultdict(float)
        year_hours = np.zeros(HOURS)
        for name, df in frames.items():
            rec = reconstruct(df, year, cap, st_pairmaps[name])
            for tgt, cell in rec.items():
                prod_arr = prod[name].get(tgt)
                mine = np.clip(1.0 - cell["sum"], 0.0, 1.0)
                n1["checked"] += 1
                if prod_arr is None or not np.allclose(
                    prod_arr, mine, rtol=0.0, atol=1e-12
                ):
                    n1["mismatches"].append(
                        {
                            "layer": name,
                            "year": year,
                            "bin": [tgt[0], tgt[1]],
                            "max_abs_diff": (
                                None
                                if prod_arr is None
                                else float(np.max(np.abs(prod_arr - mine)))
                            ),
                        }
                    )
                    continue
                fixed = per_unit_clipped(cell, cap[tgt])
                d = fixed - mine  # availability restored (>= 0 by construction)
                if not d.any():
                    continue
                gwh = float(d.sum() * cap[tgt] / 1000.0)
                cls = bin_class.get(tgt, tgt[1])
                year_delta[cls] += gwh
                # The lay-up layer is NOT an availability layer (its sole
                # consumer is the must-run floor mask), so its delta is
                # reported apart from the availability total.
                if name != "layup":
                    year_hours += d * cap[tgt]
                bin_rows[(tgt[0], tgt[1], name)][year] = gwh
        delta_by_year[str(year)] = {
            "by_class_gwh": {k: round(v, 3) for k, v in sorted(year_delta.items())},
            "total_gwh": round(sum(year_delta.values()), 3),
        }
        hourly_delta[year] = year_hours

    report["n1_reproduction"] = n1
    report["n3_counterfactual"]["by_year"] = delta_by_year
    report["n3_counterfactual"]["bins"] = [
        {
            "plant": k[0],
            "group": k[1],
            "layer": k[2],
            "gwh": {str(y): round(v, 4) for y, v in sorted(yr.items())},
        }
        for k, yr in sorted(
            bin_rows.items(), key=lambda kv: -sum(kv[1].values())
        )
    ]

    # ---- N-4: where the restored capability lands -------------------------
    # Measured against the KEEPER'S OWN committed hourly sidecar (rule 15: a
    # keeper's hourlies are read, never re-solved, for a question like this), so
    # "scarcity hour" means the hour the scored keeper actually priced high --
    # not a proxy.
    keeper_hourly = REPO / "results" / "calibration" / "miso201_stbasis_B" / "hourly"
    for year in YEARS:
        d = hourly_delta[year]
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        by_month = {
            str(m): round(float(d[idx.month == m].sum() / 1000.0), 3)
            for m in range(1, 13)
            if d[idx.month == m].any()
        }
        jun_sep = float(d[np.isin(idx.month, (6, 7, 8, 9))].sum() / 1000.0)
        tot = float(d.sum() / 1000.0)
        entry = {
            "total_gwh": round(tot, 3),
            "by_month_gwh": by_month,
            "jun_sep_gwh": round(jun_sep, 3),
            "jun_sep_share": round(jun_sep / tot, 4) if tot else None,
        }
        sc = keeper_hourly / f"system_{year}.parquet"
        if sc.exists() and tot:
            sysdf = pd.read_parquet(sc)
            sysdf = sysdf[sysdf["pass"] == "P1"]
            agg = sysdf.groupby("hour").agg(
                demand=("demand", "sum"), price=("price", "mean")
            )
            agg = agg.reindex(range(HOURS))
            load = agg["demand"].to_numpy()
            price = agg["price"].to_numpy()
            top_load = load >= np.nanquantile(load, 0.9)
            top_price = price >= np.nanquantile(price, 0.99)  # the ~88 scarcity hours
            entry["top_load_decile_gwh"] = round(float(d[top_load].sum() / 1000.0), 3)
            entry["top_load_decile_share"] = round(
                float(d[top_load].sum() / 1000.0) / tot, 4
            )
            entry["top_price_pct1_gwh"] = round(float(d[top_price].sum() / 1000.0), 4)
            entry["top_price_pct1_share"] = round(
                float(d[top_price].sum() / 1000.0) / tot, 4
            )
            entry["top_price_pct1_n_hours"] = int(top_price.sum())
        report["n4_where_it_lands"][str(year)] = entry

    # ---- N-5: the maxgen twin --------------------------------------------
    mg_delta = {}
    for year in YEARS:
        rec = reconstruct_maxgen(maxgen, year, cap)
        prod_mg = outages.unit_outage_maxgen_derate_factors(
            year,
            HOURS,
            iso=ISO,
            cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
            cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
            mixed_gas_routing=KEEPER["mixed_gas_routing"],
        )
        checked = 0
        bad = []
        gwh = 0.0
        for tgt, cell in rec.items():
            mine = np.clip(1.0 - cell["sum"], 0.0, 1.0)
            pa = prod_mg.get(tgt)
            checked += 1
            if pa is None or not np.allclose(pa, mine, rtol=0.0, atol=1e-12):
                bad.append([tgt[0], tgt[1]])
                continue
            over = np.clip(cell["sum"] - 1.0, 0.0, None)
            if over.any():
                gwh += float(over.sum() * cap[tgt] / 1000.0)
        mg_delta[str(year)] = {
            "bins_checked": checked,
            "mismatches": bad,
            "overflow_gwh": round(gwh, 3),
        }
    report["n5_maxgen"]["by_year"] = mg_delta

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    print(
        "N-1 reproduction:",
        n1["checked"],
        "bins checked,",
        len(n1["mismatches"]),
        "mismatches",
    )
    for y, v in delta_by_year.items():
        print(f"  N-3 {y}: {v['total_gwh']} GWh restored  {v['by_class_gwh']}")
    for y, v in report["n4_where_it_lands"].items():
        print(
            f"  N-4 {y}: Jun-Sep {v['jun_sep_gwh']} GWh"
            f" ({v['jun_sep_share']}), top-decile share {v.get('top_load_decile_share')}"
        )


if __name__ == "__main__":
    main()
