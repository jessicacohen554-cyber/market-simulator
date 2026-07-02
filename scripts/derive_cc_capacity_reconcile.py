#!/usr/bin/env python3
"""Derive the per-plant CC capacity reconciliation (backcast).

Two directions, both anchored on the plant's **demonstrated CAMPD peak**
(99.9th percentile of net MW across the backcast years, robust to single-hour
glitches):

* ``--mode raise`` (default, the original ERCOT artifact): several
  grid-serving combined cycles produced **more** than their curated bin
  nameplate in the CEMS record — the cold-weather (winter) over-rating an
  F-class CC delivers when the air is dense, which the standard nameplate
  omits — so the LP cannot reach the output the real plant did and logs zero
  hours in its top CF band (see `docs/cc-high-cf-investigation.md`,
  Freestone). Each CC_REGULAR plant's LP capacity is lifted to the larger of
  its current nameplate and its demonstrated peak. It never lowers a
  nameplate — a plant that simply never dispatched to its rating keeps it;
  only demonstrated, measured headroom is added.
* ``--mode cap`` (the opposite-direction twin, PJM first —
  `docs/handoffs/pjm-cc-overgen-recommendation-2026-06.md` Rank 4): plants
  whose **model** nameplate exceeds anything they ever sustained in the CEMS
  record over-run the top CF bands purely on phantom capacity. Each
  CC_REGULAR plant whose model capacity exceeds its demonstrated peak by more
  than the ``--cap-margin`` (default 1.1x, so an economically-idle top band is
  never mistaken for missing capability) is capped AT the demonstrated peak.
  Rows carry ``mode=cap`` so the loader applies ``min()`` instead of
  ``max()``; the ERCOT raise table has no ``mode`` column and is untouched.

EIA-860 winter capacity is carried alongside as corroborating provenance.

Output: ``data/raw/_processed-legacy/cc_capacity_reconcile_<ISO>.csv``
(`plant_code, plant_name, current_mw, campd_p999_mw, eia860_winter_mw,
reconciled_mw, delta_pct, source[, mode]`), consumed by ``load_campd_bins``
(ERCOT) or ``fleet_to_bins`` (synthesized-bins ISOs) under
``ScenarioConfig.cc_capacity_reconcile``.

    uv run python scripts/derive_cc_capacity_reconcile.py \
        --campd results/calibration/run115b_ccduct_prb73_relief06/campd.parquet
    uv run python scripts/derive_cc_capacity_reconcile.py --iso PJM --mode cap
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# Minimum fractional change to bother writing a row (avoid float noise).
_MIN_DELTA = 0.01
# Cap mode: only cap when model capacity exceeds the demonstrated peak by this
# factor (Rank 4 caution — a plant that merely never dispatched high for
# economic reasons must not be mistaken for one that cannot).
_CAP_MARGIN = 1.10
# CAMPD reports gross; the model dispatches net. CC parasitic load ~2.5%
# (campd._CLASS_PARASITIC_LOAD_PCT["CC_REGULAR"] = 0.025).
_CC_NET_OF_GROSS = 0.975
# Only pure-play CC plants (>= this share of the plant's model capacity is
# CC_REGULAR) are screened in cap mode: CAMPD's non-ERCOT extracts are summed
# per ORIS plant, so a co-located CT/coal unit would inflate the plant series
# and hide a real cap. Excluding mixed sites can only make the cap
# conservative (fewer plants capped), never wrong.
_PURE_PLAY_CC_SHARE = 0.90
# Cap-mode cross-source feasibility guard: a candidate is dropped when its
# EIA-923 annual net generation in ANY backcast year implies a capacity factor
# above this at the capped level. A real CC tops out near ~90% annual CF
# (planned outages); an implied CF above it means the CEMS series understates
# the plant (units missing from the extract — e.g. Hunterstown reads 595 MW
# peak in CAMPD yet EIA-923 shows 6.1 TWh/yr, CF 1.17), so the "demonstrated
# peak" is a telemetry artifact, not a capability (CLAUDE.md #13 misalignment
# exception: using it literally would make results less real).
_CAP_FEASIBLE_CF = 0.90


def _model_cc_capacity(iso: str, year: int) -> dict[int, tuple[str, float]]:
    """Per-plant model CC_REGULAR capacity (MW) as the LP will carry it.

    Sums the fleet's per-generator net-summer ratings per plant and, when the
    ISO runs ``cc_nameplate_summer_derate`` (PJM/NYISO/NEISO/CAISO), rescales
    to full nameplate by the plant's measured summer-derate ratio — the exact
    transform ``fleet_to_bins`` applies — so the cap screen compares the
    demonstrated peak against the same number the reconcile hook will cap.
    Restricted to pure-play CC plants (see ``_PURE_PLAY_CC_SHARE``).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import cc_summer_derate_ratio, load_fleet_from_csv

    gens = load_fleet_from_csv(iso, get_iso_config(iso), year=year)
    plant_cap: dict[int, float] = {}
    cc_cap: dict[int, float] = {}
    names: dict[int, str] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "CC_REGULAR":
            cc_cap[pc] = cc_cap.get(pc, 0.0) + float(g.pmax_mw)
            names[pc] = g.name
    summer_derate_isos = ("PJM", "NYISO", "NEISO", "CAISO")
    out: dict[int, tuple[str, float]] = {}
    for pc, cap in cc_cap.items():
        if cap / plant_cap[pc] < _PURE_PLAY_CC_SHARE:
            continue
        if iso.upper() in summer_derate_isos:
            ratio = cc_summer_derate_ratio(pc)
            if ratio is not None and ratio > 0.0:
                cap = cap / ratio
        out[pc] = (names[pc], cap)
    return out


def _campd_p999(iso: str, plant_codes: set[int], years: list[int]) -> pd.Series:
    """Demonstrated peak (p99.9 of net MW, all years pooled) per CAMPD plant."""
    from market_sim.data import campd

    states = campd.states_for_iso(iso)
    series: dict[int, list[np.ndarray]] = {}
    for year in years:
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(
            df, {pid: _CC_NET_OF_GROSS for pid in plant_codes}, year
        )
        for pid, arr in net.items():
            if pid in plant_codes:
                series.setdefault(pid, []).append(arr)
    return pd.Series(
        {
            pid: float(np.quantile(np.concatenate(arrs), 0.999))
            for pid, arrs in series.items()
        }
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--campd",
        type=Path,
        default=REPO
        / "results/calibration/run115b_ccduct_prb73_relief06"
        / "campd.parquet",
        help="a calibration bundle's campd.parquet (CEMS net MW, all years); "
        "raise mode only — cap mode reads the raw CAMPD state extracts",
    )
    ap.add_argument("--iso", default="ERCOT", help="ISO fleet to reconcile")
    ap.add_argument(
        "--mode",
        choices=("raise", "cap"),
        default="raise",
        help="raise: lift nameplate to demonstrated peak (ERCOT artifact); "
        "cap: bound model capacity at the demonstrated peak (PJM Rank 4)",
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="backcast years pooled into the demonstrated peak (cap mode)",
    )
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    iso = args.iso.upper()
    out_path = args.out or (
        REPO / "data/raw/_processed-legacy" / f"cc_capacity_reconcile_{iso}.csv"
    )

    if args.mode == "raise":
        # Original ERCOT path, unchanged: curated bin nameplates vs a solved
        # bundle's campd.parquet.
        csv = pd.read_csv(REPO / "data/raw/reference/custom-bin-assignments.csv")
        cc = csv[csv["Plant_Group"] == "CC_REGULAR"]
        plants = {
            int(r["Plant_Code"]): (str(r["Plant_Name"]), float(r["Nameplate_MW"]))
            for _, r in cc.iterrows()
        }
        campd = pd.read_parquet(args.campd)
        # Demonstrated peak = 99.9th pct of net MW across every backcast year,
        # so a plant that only hit its cold-weather rating in one year still
        # gets credited for it.
        p999 = campd.groupby("plant_id")["net_mw"].quantile(0.999)
    else:
        # Cap mode: the model fleet's per-plant CC capacity (as the LP will
        # carry it) vs the demonstrated peak from the raw CAMPD extracts.
        plants = _model_cc_capacity(iso, max(args.years))
        p999 = _campd_p999(iso, set(plants), args.years)
        # Cross-source feasibility guard (see _CAP_FEASIBLE_CF).
        from market_sim.data.eia923 import load_monthly_generation

        gen = load_monthly_generation()
        gen = gen[gen["year"].isin(args.years)]
        annual = gen.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()

    e860 = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    e860["Winter Capacity (MW)"] = pd.to_numeric(
        e860["Winter Capacity (MW)"], errors="coerce"
    )
    winter = e860.groupby("Plant Code")["Winter Capacity (MW)"].sum()

    rows = []
    for code, (name, cur) in plants.items():
        peak = float(p999.get(code, np.nan))
        win = float(winter.get(code, np.nan))
        if np.isnan(peak) or peak <= 0.0:
            continue
        if args.mode == "raise":
            reconciled = max(cur, peak)
            delta = (reconciled - cur) / cur
            if delta < _MIN_DELTA:  # raise-only; skip no-ops and (never) cuts
                continue
        else:
            if cur <= _CAP_MARGIN * peak:  # inside the margin: not capped
                continue
            implied_cf = max(
                (
                    float(annual.get((code, y), 0.0)) / (peak * 8760.0)
                    for y in args.years
                ),
                default=0.0,
            )
            if implied_cf > _CAP_FEASIBLE_CF:
                print(
                    f"SKIP {name} ({code}): EIA-923 implies CF "
                    f"{implied_cf:.2f} at the {peak:.0f} MW demonstrated peak "
                    "— CEMS series incomplete, cap would be a telemetry "
                    "artifact"
                )
                continue
            reconciled = peak
            delta = (reconciled - cur) / cur
        rows.append(
            {
                "plant_code": code,
                "plant_name": name,
                "current_mw": round(cur, 1),
                "campd_p999_mw": round(peak, 1),
                "eia860_winter_mw": round(win, 1) if not np.isnan(win) else "",
                "reconciled_mw": round(reconciled, 1),
                "delta_pct": round(100 * delta, 1),
                "source": "campd_demonstrated_peak",
                **({"mode": "cap"} if args.mode == "cap" else {}),
            }
        )

    out = pd.DataFrame(rows).sort_values("delta_pct", ascending=(args.mode == "cap"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    verb = "raised" if args.mode == "raise" else "capped"
    print(f"wrote {out_path}  ({len(out)} CC_REGULAR plants {verb})")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
