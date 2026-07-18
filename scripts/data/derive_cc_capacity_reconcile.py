#!/usr/bin/env python3
"""Derive the per-plant CC capacity reconciliation (backcast).

Every mode is anchored on the plant's **demonstrated CAMPD peak** (99.9th
percentile of net MW across the backcast years, robust to single-hour glitches)
— a measured capability (CLAUDE.md rule 13; re-derives only on CAMPD vintage
change, rule 23), not a residual fit:

* ``--mode both`` (recommended for the synthesized-bins ISOs): FULL bidirectional
  coverage — every CC_REGULAR plant whose demonstrated peak differs from its
  (un-guarded) model capacity in EITHER direction gets a row, so the reconcile
  is the primary measured bound and the nameplate summer-capacity guard
  (``fleet._reconcile_cc_pmax_to_nameplate``) is a pure fallback. Caps a plant
  whose model capacity exceeds its peak by more than ``_CAP_MARGIN`` (phantom),
  raises one whose peak exceeds its model capacity by up to ``_CAP_MARGIN`` (a
  cold-weather over-rating nameplate omits). A raise *more* than ``_CAP_MARGIN``
  above model capacity is NOT a cold-weather over-rating — it is a data artifact
  (CAMPD contamination from co-located non-CC units, or a fleet-loading
  under-carry) and is skipped and flagged for separate root-cause (rule 11).
* ``--mode raise`` (the original ERCOT artifact): lift the curated bin nameplate
  to the demonstrated peak from a solved bundle's ``campd.parquet``. Raise-only.
* ``--mode cap`` (legacy, cap-only): bound model capacity at the demonstrated
  peak; no raise rows.

CT-only exclusion (``--mode cap``/``both``): a plant whose EIA-923 net exceeds
1.1x its CAMPD gross submits only its combustion-turbine block (the 2x1 CC
signature), so its demonstrated peak understates it — it is excluded and falls
back to the nameplate guard (rule-13 misalignment exception; same detector as
``render_calibration_html._flag_ct_only_reporters``).

Model capacity is measured on the **un-guarded** fleet
(``apply_cc_summer_guard=False``): the guard reads THIS table's demonstrated
peaks, so guarding the derive's input would make the table self-referential.

EIA-860 winter capacity is carried alongside as corroborating provenance.

Output: ``data/raw/_processed-legacy/cc_capacity_reconcile_<ISO>.csv``
(`plant_code, plant_name, current_mw, campd_p999_mw, eia860_winter_mw,
reconciled_mw, delta_pct, source[, mode]`), consumed by ``load_campd_bins``
(ERCOT) or ``fleet_to_bins`` (synthesized-bins ISOs) under
``ScenarioConfig.cc_capacity_reconcile``, and by the guard for its
``max(nameplate, demonstrated_peak)`` bound.

    uv run python scripts/data/derive_cc_capacity_reconcile.py \
        --campd results/calibration/run115b_ccduct_prb73_relief06/campd.parquet
    uv run python scripts/data/derive_cc_capacity_reconcile.py --iso PJM --mode both
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
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

    # Un-guarded fleet (apply_cc_summer_guard=False): the derive must measure the
    # RAW model capacity the guard clips, not the guard's output. The guard reads
    # THIS table's demonstrated peaks, so guarding the derive's input would make
    # the table self-referential — a plant the guard restores to its peak would
    # read here as "at capacity" and drop from the next re-derive, then the guard
    # would lose the peak and clip it back to nameplate (an oscillation).
    gens = load_fleet_from_csv(
        iso, get_iso_config(iso), year=year, apply_cc_summer_guard=False
    )
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


def _campd_p999_and_annual(
    iso: str, plant_codes: set[int], years: list[int]
) -> tuple[pd.Series, pd.Series]:
    """Per CAMPD plant: (demonstrated peak p999 net MW, pooled annual net MWh).

    Both from a single CAMPD load. The peak (99.9th pct of net MW across all
    pooled years) is the reconcile authority; the pooled annual net MWh feeds
    the CT-only exclusion (:func:`_ct_only_codes`) — a plant whose EIA-923 net
    exceeds ~1.1x its CAMPD gross is an incomplete (CT-only) reporter whose
    demonstrated peak understates it.
    """
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
    p999 = pd.Series(
        {
            pid: float(np.quantile(np.concatenate(arrs), 0.999))
            for pid, arrs in series.items()
        }
    )
    annual_net = pd.Series(
        {pid: float(np.concatenate(arrs).sum()) for pid, arrs in series.items()}
    )
    return p999, annual_net


def _ct_only_codes(campd_annual_net: pd.Series, e923_annual_net: pd.Series) -> set[int]:
    """Plant codes whose CEMS record is incomplete (CT-only 2x1 signature).

    A complete CEMS record's GROSS generation exceeds the plant's EIA-923 NET
    generation. A plant whose EIA-923 net exceeds :data:`_CT_ONLY_RATIO` x its
    CAMPD gross (``campd_net / _CC_NET_OF_GROSS``) is therefore submitting only
    the combustion-turbine block (steam MWh absent), so its demonstrated CAMPD
    peak understates its true capability. These are excluded from the reconcile
    entirely and fall back to the nameplate guard (rule-13 misalignment
    exception: using the understated peak literally would make results *less*
    real). Same detector as
    :func:`scripts.render_calibration_html._flag_ct_only_reporters`.
    """
    ct_only: set[int] = set()
    for code, campd_net in campd_annual_net.items():
        gross = campd_net / _CC_NET_OF_GROSS if _CC_NET_OF_GROSS > 0.0 else campd_net
        e923 = float(e923_annual_net.get(code, 0.0))
        if gross > 0.0 and e923 > _CT_ONLY_RATIO * gross:
            ct_only.add(int(code))
    return ct_only


# 923-net / CAMPD-gross above which a CC plant is an incomplete (CT-only) CEMS
# reporter — the 2x1 signature where only the combustion-turbine block reports
# (net/gross ~ 1.5). Matches render_calibration_html._CT_ONLY_RATIO.
_CT_ONLY_RATIO = 1.1


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
        choices=("raise", "cap", "both"),
        default="raise",
        help="raise: lift nameplate to demonstrated peak (ERCOT artifact, "
        "curated-bin basis); cap: bound model capacity at the demonstrated peak "
        "(cap-only, legacy); both: FULL bidirectional coverage — every "
        "CC_REGULAR plant whose demonstrated peak differs from model capacity in "
        "either direction (the unified measured-capability stack; the "
        "recommended non-ERCOT mode)",
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="backcast years pooled into the demonstrated peak (cap/both mode)",
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
        ct_only: set[int] = set()
        annual = pd.Series(dtype=float)
    else:
        # cap / both: the model fleet's per-plant CC capacity (as the LP will
        # carry it, un-guarded) vs the demonstrated peak from the raw CAMPD
        # extracts. ``both`` additionally emits raise rows where the model
        # under-rates a plant (cold-weather over-rating), for full coverage.
        plants = _model_cc_capacity(iso, max(args.years))
        p999, campd_annual = _campd_p999_and_annual(iso, set(plants), args.years)
        from market_sim.data.eia923 import load_monthly_generation

        gen = load_monthly_generation()
        gen = gen[gen["year"].isin(args.years)]
        annual = gen.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
        # CT-only exclusion (rule-13 misalignment): plants whose EIA-923 net >
        # 1.1x CAMPD gross report only their CT block, so their demonstrated
        # peak understates them — never cap (or raise) them to it.
        e923_pooled = gen.groupby("plant_id")["netgen_annual_mwh"].sum()
        ct_only = _ct_only_codes(campd_annual, e923_pooled)

    e860 = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    e860["Winter Capacity (MW)"] = pd.to_numeric(
        e860["Winter Capacity (MW)"], errors="coerce"
    )
    winter = e860.groupby("Plant Code")["Winter Capacity (MW)"].sum()

    rows = []
    for code, (name, cur) in plants.items():
        peak = float(p999.get(code, np.nan))
        win = float(winter.get(code, np.nan))
        if np.isnan(peak) or peak <= 0.0 or cur <= 0.0:
            continue
        if args.mode == "raise":
            reconciled = max(cur, peak)
            delta = (reconciled - cur) / cur
            if delta < _MIN_DELTA:  # raise-only; skip no-ops and (never) cuts
                continue
            row_mode = None  # ERCOT raise table has no mode column
        else:
            if code in ct_only:
                print(
                    f"SKIP {name} ({code}): CT-only CEMS reporter (EIA-923 net "
                    f"> {_CT_ONLY_RATIO}x CAMPD gross) — demonstrated peak "
                    f"{peak:.0f} MW understates the plant; falls back to the "
                    "nameplate guard"
                )
                continue
            if cur > _CAP_MARGIN * peak:
                # Model over-rates beyond the margin: cap to the demonstrated
                # peak — but only if the CEMS series is feasibly complete.
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
                        f"{implied_cf:.2f} at the {peak:.0f} MW demonstrated "
                        "peak — CEMS series incomplete, cap would be a "
                        "telemetry artifact"
                    )
                    continue
                reconciled = peak
                row_mode = "cap"
            elif args.mode == "both" and cur < peak * (1.0 - _MIN_DELTA):
                # Model under-rates: raise to the demonstrated peak (the
                # cold-weather over-rating nameplate omits). Full-coverage only.
                # Symmetric with the cap margin: a genuine cold-weather
                # over-rating is a few percent above the model capacity, never a
                # large jump. A peak more than _CAP_MARGIN above the model
                # capacity is a data artifact — the CAMPD plant series is
                # contaminated by co-located non-CC units (Chesterfield 3797:
                # peak 993 vs 447 model, coal+CC summed) or the model
                # *under-carries* the plant (CPV Fairview 60589: model 725 MW vs
                # EIA-860 net-summer 1057 MW, a fleet-loading gap). Neither is a
                # reconcile target: raising to it would paper over a distinct bug
                # (rule 11 — root-cause the fleet/attribution gap, don't bury it
                # in a capacity value). Skip and flag.
                if peak > _CAP_MARGIN * cur:
                    print(
                        f"SKIP {name} ({code}): demonstrated peak {peak:.0f} MW "
                        f"exceeds model capacity {cur:.0f} MW by "
                        f">{(_CAP_MARGIN - 1) * 100:.0f}% — not a cold-weather "
                        "over-rating; CAMPD contamination or a fleet-loading "
                        "under-carry (root-cause separately, do not reconcile)"
                    )
                    continue
                reconciled = peak
                row_mode = "raise"
            else:
                continue  # within margin in both directions: no row
            delta = (reconciled - cur) / cur
        row = {
            "plant_code": code,
            "plant_name": name,
            "current_mw": round(cur, 1),
            "campd_p999_mw": round(peak, 1),
            "eia860_winter_mw": round(win, 1) if not np.isnan(win) else "",
            "reconciled_mw": round(reconciled, 1),
            "delta_pct": round(100 * delta, 1),
            "source": "campd_demonstrated_peak",
        }
        if row_mode is not None:
            row["mode"] = row_mode
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("delta_pct", ascending=(args.mode != "raise"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    if args.mode == "both":
        n_cap = int((out["mode"] == "cap").sum()) if not out.empty else 0
        n_raise = int((out["mode"] == "raise").sum()) if not out.empty else 0
        print(
            f"wrote {out_path}  ({len(out)} CC_REGULAR plants: {n_cap} capped, "
            f"{n_raise} raised)"
        )
    else:
        verb = "raised" if args.mode == "raise" else "capped"
        print(f"wrote {out_path}  ({len(out)} CC_REGULAR plants {verb})")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
