#!/usr/bin/env python3
"""nyiso-148 phase 0 — per-plant CHP operating conduct, measured mechanism-blind.

WHY. nyiso-147 armed the measured Gold-Book/EIA-923 CHP behind-the-meter
shares (``ScenarioConfig.nyiso_chp_btm_measured``) and PROVED the 2023 upstate
price object with them (lw C3a-2023 +8.7 % -> +1.5 %), but the arm was
REJECTED-AS-ARMED because restoring the plants' true grid capacity exposed two
CONDUCT defects the carve had been masking: Selkirk (10725) dispatching 730 GWh
against a 92 GWh meter, and CC_CHP over-running its own corrected bench by
+5.0 TWh because the LP runs the restored plants at their offers' implied
capacity factor.

This probe measures the conduct itself, BEFORE any construction is proposed
(the nyiso-147 phase-0 shape). It reads only two meters and the model's own
population; it reads NO price residual, NO D-4 verdict and NO A/B gate, which
is what makes any later agreement between its verdicts and the model's failures
evidence rather than circularity (rule 23 ``[R-FROZEN-DERIVE]``).

WHAT IT MEASURES, per NYISO CHP plant (model classes CC_CHP / CT_CHP / ST_CHP):

1. **Lay-up membership** — the nyiso-140/144 census criterion VERBATIM
   (``median(grossLoad) == 0`` in every (year, 4-hour block) cell), applied
   for the first time beyond the commitment bridge's ``(CC_REGULAR, ST_GAS)``
   population. Reported pooled (18 cells) and per year (6 cells), so a
   part-year idling is visible where the pooled test cannot see it.
2. **Run structure** — starts, median/p90/max run length, online share, on the
   same ``max(1 MW, 5 % of HSL)`` online convention as the sibling derivations.
3. **Duty / loading** — the WP-3 loading-when-on statistic
   (mean and p50 of ``grossLoad / HSL`` over online hours) that
   ``derive_campd_gas_commitment_params.py`` uses to identify min-load
   fractions, here read as a DUTY statistic for the cogen fleet.
4. **Energy and capacity factor** — EIA-923 net generation per plant-year
   against the model's grid capacity under BOTH BTM conventions (the 35 %
   sector carve the control runs, and the measured per-plant share the
   nyiso-147 artifact supplies), so the CF a restored plant would have to run
   at is explicit.

Output: ``results/calibration/_nyiso148_chp_conduct_phase0.json`` (+ a CSV
companion). No LP is solved and nothing is written to ``data/``.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso148_chp_conduct_phase0.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: The cogeneration model classes — the population the bridge census
#: deliberately excludes ("Cogens (*_CHP) follow their steam host and are
#: never bridged").
CHP_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")

YEARS: tuple[int, ...] = (2023, 2024, 2025)
BLOCK_HOURS: int = 4
_HSL_PCTILE: float = 99.5
_ONLINE_FRAC: float = 0.05

#: The sector default the control run carves off merchant CHP grid capacity
#: (constants.CHP_BTM_PCT_BY_SECTOR["merchant"]).
CONTROL_MERCHANT_BTM_PCT: float = 35.0


def population(iso: str) -> dict[int, dict]:
    """Return ``{plant_code: {...}}`` for the ISO's CHP plants.

    Keyed by EIA plant code (a CAMPD facility carries no model class), with
    the model's own per-class capacity split so a plant spanning CT_CHP and
    ST_CHP is reported whole. ``pmax_mw`` is the capacity the CONTROL fleet
    carries, i.e. already net of whatever BTM carve the build applied.

    Args:
        iso: The ISO name.
    """
    out: dict[int, dict] = {}
    for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
        group = getattr(gen, "plant_group", None) or ""
        if group not in CHP_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        row = out.setdefault(
            code,
            {"classes": {}, "zone": gen.zone, "pmax_mw": 0.0, "name": gen.name},
        )
        row["classes"][group] = row["classes"].get(group, 0.0) + float(gen.pmax_mw)
        row["pmax_mw"] += float(gen.pmax_mw)
    for row in out.values():
        row["class"] = max(row["classes"], key=row["classes"].get)
    return out


def plant_series(iso: str, codes: set[int]) -> pd.DataFrame:
    """Return the pooled hourly PLANT gross-load series for *codes*.

    Units are summed to one plant series per hour before any statistic is
    taken, because lay-up is a property of the SITE (the census convention).

    Args:
        iso: The ISO name.
        codes: EIA plant codes to keep.
    """
    frames: list[pd.DataFrame] = []
    for state in states_for_iso(iso):
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=["facilityId", "facilityName", "date", "hour", "grossLoad"],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            plant = df.groupby(
                ["facilityId", "facilityName", "date", "hour"], as_index=False
            )["grossLoad"].sum()
            plant["year"] = year
            frames.append(plant)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD hours for the CHP population")
    return pd.concat(frames, ignore_index=True)


def run_structure(online: np.ndarray) -> dict:
    """Return start count and run-length statistics for a boolean on-series.

    Args:
        online: Chronologically ordered per-hour online flags.
    """
    if online.size == 0 or not online.any():
        return {"starts": 0, "run_median_h": 0.0, "run_p90_h": 0.0, "run_max_h": 0}
    padded = np.concatenate(([False], online, [False]))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    lengths = (stops - starts).astype(float)
    return {
        "starts": int(lengths.size),
        "run_median_h": round(float(np.median(lengths)), 1),
        "run_p90_h": round(float(np.percentile(lengths, 90)), 1),
        "run_max_h": int(lengths.max()),
    }


def eia923_by_plant(codes: set[int]) -> dict[tuple[int, int], float]:
    """Return ``{(plant_code, year): net generation GWh}`` for *codes*.

    Args:
        codes: EIA plant codes to keep.
    """
    path = PROCESSED_DIR / "eia923_monthly_generation.parquet"
    df = pd.read_parquet(path, columns=["plant_id", "netgen_annual_mwh", "year"])
    df = df[df["plant_id"].isin(codes) & df["year"].isin(YEARS)]
    grp = df.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum() / 1000.0
    return {(int(k[0]), int(k[1])): round(float(v), 1) for k, v in grp.items()}


def lp_capacity() -> dict[int, dict]:
    """Return ``{plant_code: {"lp_grid_mw", "avail_mean", "offer_mean"}}``.

    The LP's OWN grid capacity per CHP plant, read from the committed
    nyiso-147 phase-0c record (``_nyiso147_chp_grid_capacity.json``, the
    control keeper's 2023 fleet rebuilt ``fleet_only``). The raw fleet CSV
    carries a different capacity basis (summer capability before the build's
    derates), so a capacity factor taken against it would not be the CF the
    LP faces; this is the basis that matters and it costs no solve.
    """
    path = REPO / "results" / "calibration" / "_nyiso147_chp_grid_capacity.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    out: dict[int, dict] = {}
    for code, d in raw.items():
        rows = d["rows"]
        cap = float(d["grid_pmax_sum"])
        out[int(code)] = {
            "lp_grid_mw": round(cap, 1),
            "avail_mean": round(
                sum(r["avail_mean"] * r["pmax"] for r in rows) / cap if cap else 0.0, 3
            ),
            "offer_min": round(min(r["offer_mean"] for r in rows), 2),
            "offer_cap_wtd": round(
                sum(r["offer_mean"] * r["pmax"] for r in rows) / cap if cap else 0.0, 2
            ),
        }
    return out


def measured_shares() -> dict[int, float]:
    """Return ``{plant_code: measured grid share}`` from the nyiso-147 artifact."""
    path = PROCESSED_DIR / "chp_btm_share_measured_NYISO.csv"
    df = pd.read_csv(path)
    return {int(r.plant_code): float(r.grid_share) for r in df.itertuples()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", default="NYISO")
    ap.add_argument(
        "--out", default="results/calibration/_nyiso148_chp_conduct_phase0.json"
    )
    args = ap.parse_args()
    iso = args.iso

    pop = population(iso)
    print(f"{iso}: {len(pop)} CHP plants in the model fleet")
    series = plant_series(iso, set(pop))
    e923 = eia923_by_plant(set(pop))
    shares = measured_shares()
    lpcap = lp_capacity()

    series = series.sort_values(["facilityId", "year", "date", "hour"])
    series["block"] = (series["hour"] // BLOCK_HOURS).astype(int)

    rows: list[dict] = []
    for code, grp in series.groupby("facilityId"):
        code = int(code)
        meta = pop[code]
        load = grp["grossLoad"].to_numpy(dtype=float)
        hsl = float(np.percentile(load, _HSL_PCTILE))
        on_thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        online = load >= on_thresh

        cell_median = grp.groupby(["year", "block"])["grossLoad"].median()
        cells, cells_zero = int(cell_median.size), int((cell_median <= 0.0).sum())

        per_year: dict[str, dict] = {}
        for year, sub in grp.groupby("year"):
            yl = sub["grossLoad"].to_numpy(dtype=float)
            yon = yl >= on_thresh
            ycell = sub.groupby("block")["grossLoad"].median()
            # Grid capacity under each BTM convention (measured share missing
            # -> the plant keeps the sector default, so control == measured).
            share = shares.get(code)
            ctl_cap = meta["pmax_mw"]
            if share is None:
                meas_cap = ctl_cap
            else:
                # control cap = nameplate x (1 - 0.35) for merchant rows; the
                # measured cap re-bases it on the plant's own grid share.
                meas_cap = ctl_cap / (1.0 - CONTROL_MERCHANT_BTM_PCT / 100.0) * share
            e = e923.get((code, int(year)))
            campd_gwh = float(yl.sum()) / 1000.0
            per_year[str(int(year))] = {
                "campd_gross_gwh": round(campd_gwh, 1),
                "campd_over_e923": (
                    round(campd_gwh / e, 3) if e not in (None, 0) else None
                ),
                "online_share": round(float(yon.mean()), 4),
                "cells_zero_of_6": int((ycell <= 0.0).sum()),
                "mean_mw_when_on": round(
                    float(yl[yon].mean()) if yon.any() else 0.0, 1
                ),
                "load_frac_when_on_p50": round(
                    float(np.median(yl[yon] / hsl)) if yon.any() and hsl > 0 else 0.0, 3
                ),
                "e923_net_gwh": e,
                "metered_cf_on_control_cap": (
                    round(e * 1000.0 / (ctl_cap * 8760.0), 3)
                    if e is not None and ctl_cap > 0
                    else None
                ),
                "metered_cf_on_measured_cap": (
                    round(e * 1000.0 / (meas_cap * 8760.0), 3)
                    if e is not None and meas_cap > 0
                    else None
                ),
                **run_structure(yon),
            }

        share = shares.get(code)
        ctl_cap = meta["pmax_mw"]
        meas_cap = (
            ctl_cap
            if share is None
            else ctl_cap / (1.0 - CONTROL_MERCHANT_BTM_PCT / 100.0) * share
        )
        # PAIRWISE pooling: a year enters the coverage ratio only when BOTH
        # meters carry the plant, so a thin EIA-923 vintage cannot masquerade
        # as a CAMPD over-report (the nyiso-147 share derivation's convention).
        _campd_by_year = {
            int(y): float(sub["grossLoad"].sum()) / 1000.0
            for y, sub in grp.groupby("year")
        }
        _pairs = [
            (_campd_by_year.get(y, 0.0), e923[(code, y)])
            for y in YEARS
            if (code, y) in e923 and y in _campd_by_year
        ]
        _pooled_e923 = sum(e for _, e in _pairs) if _pairs else None
        _pooled_campd = sum(c for c, _ in _pairs) if _pairs else None
        _cov_years = [y for y in YEARS if (code, y) in e923 and y in _campd_by_year]
        lp = lpcap.get(code, {})
        lp_ctl = lp.get("lp_grid_mw")
        lp_meas = (
            None
            if lp_ctl is None
            else round(
                lp_ctl
                if share is None
                else lp_ctl / (1.0 - CONTROL_MERCHANT_BTM_PCT / 100.0) * share,
                1,
            )
        )
        # The CF the LP would have to run the RESTORED plant at to reproduce
        # the plant's own metered grid energy, and the CF its measured
        # availability envelope leaves open to it.
        _grid_e = (
            None
            if _pooled_e923 is None or share is None
            else _pooled_e923 * share / max(len(_cov_years), 1)
        )
        rows.append(
            {
                "plant_code": code,
                "plant_name": str(grp["facilityName"].iloc[0]),
                "model_class": meta["class"],
                "zone": meta["zone"],
                "control_grid_mw": round(ctl_cap, 1),
                "measured_grid_mw": round(meas_cap, 1),
                "measured_grid_share": share,
                "observed_hsl_mw": round(hsl, 1),
                "lp_grid_mw_control": lp_ctl,
                "lp_grid_mw_measured": lp_meas,
                "lp_avail_mean": lp.get("avail_mean"),
                "lp_offer_min": lp.get("offer_min"),
                "lp_offer_cap_wtd": lp.get("offer_cap_wtd"),
                "metered_grid_gwh_per_covered_year": (
                    None if _grid_e is None else round(_grid_e, 1)
                ),
                "metered_cf_on_lp_measured_cap": (
                    round(_grid_e * 1000.0 / (lp_meas * 8760.0), 3)
                    if _grid_e is not None and lp_meas
                    else None
                ),
                "metered_cf_on_lp_measured_cap_available": (
                    round(
                        _grid_e * 1000.0 / (lp_meas * 8760.0 * lp["avail_mean"]), 3
                    )
                    if _grid_e is not None and lp_meas and lp.get("avail_mean")
                    else None
                ),
                "cells": cells,
                "cells_zero": cells_zero,
                "laid_up_pooled": bool(cells_zero == cells and cells > 0),
                "campd_gross_gwh_pooled": round(_pooled_campd, 1)
                if _pooled_campd is not None
                else None,
                "e923_net_gwh_pooled": round(_pooled_e923, 1)
                if _pooled_e923 is not None
                else None,
                "campd_coverage_years": _cov_years,
                "campd_coverage": (
                    round(_pooled_campd / _pooled_e923, 3) if _pooled_e923 else None
                ),
                "online_share": round(float(online.mean()), 4),
                "load_frac_when_on_mean": round(
                    float((load[online] / hsl).mean()) if online.any() and hsl > 0 else 0.0,
                    3,
                ),
                "load_frac_when_on_p50": round(
                    float(np.median(load[online] / hsl))
                    if online.any() and hsl > 0
                    else 0.0,
                    3,
                ),
                **run_structure(online),
                "by_year": per_year,
            }
        )

    table = pd.DataFrame(rows).sort_values("control_grid_mw", ascending=False)
    out = {
        "iso": iso,
        "years": list(YEARS),
        "criterion": (
            "nyiso-140/144 census verbatim: laid_up iff median(grossLoad) == 0 "
            "in EVERY (year, 4h block) cell; online iff grossLoad >= "
            "max(1 MW, 5% of p99.5 HSL); PLANT series (units summed)"
        ),
        "population": (
            "model plant_group in CC_CHP/CT_CHP/ST_CHP — the population the "
            "bridge lay-up census (CC_REGULAR, ST_GAS) excludes by design"
        ),
        "sources": {
            "conduct": "EPA CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level)",
            "energy": "EIA-923 Page-1 net generation (eia923_monthly_generation.parquet)",
            "grid_share": "chp_btm_share_measured_NYISO.csv (nyiso-147, frozen)",
        },
        "n_plants_model": len(pop),
        "n_plants_campd": int(len(rows)),
        "plants": rows,
    }
    outp = REPO / args.out
    outp.write_text(json.dumps(out, indent=1))
    csvp = outp.with_suffix(".csv")
    table.drop(columns=["by_year"]).to_csv(csvp, index=False)
    print(f"wrote {outp.relative_to(REPO)} and {csvp.name}")

    cols = [
        "plant_code",
        "plant_name",
        "model_class",
        "control_grid_mw",
        "measured_grid_mw",
        "cells_zero",
        "online_share",
        "load_frac_when_on_p50",
        "starts",
        "run_median_h",
        "campd_coverage",
        "lp_grid_mw_control",
        "lp_grid_mw_measured",
        "lp_avail_mean",
        "lp_offer_min",
        "metered_cf_on_lp_measured_cap_available",
    ]
    with pd.option_context(
        "display.width", 250, "display.max_columns", 40, "display.max_rows", 60
    ):
        print(table[cols].to_string(index=False))


if __name__ == "__main__":
    main()
