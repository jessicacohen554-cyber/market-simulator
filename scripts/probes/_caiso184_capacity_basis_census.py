"""caiso-184 P0-2 — the CAISO capacity-basis census (`f_CEMS > 1`), decomposed.

Pre-registered in ``results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md``
(pushed and blob-verified, 313 lines, sha256 ``33fa2093...``, remote SHA identical to
local, BEFORE any measurement here was taken).

**The question.** caiso-181 §2a split the envelope-grain "impossible MW" into an
ENVELOPE-EXCESS term (which caiso-183's grain repair removed 69/75/75 % of) and a
**BASIS** term — CEMS gross above the bin's *entire* capacity, ``f_CEMS`` up to
1.146/1.098/1.130 — which no availability envelope can represent. Post-repair the basis
term DOMINATES what is left. This census asks what that term actually is.

**The three capacity quantities** (PRECHECK §1), which caiso-181 did not distinguish:

* **D1** ``outages._iso_plant_capacity`` — the outage-derate denominator AND caiso-181's
  ``f_CEMS`` denominator. ``fleet/eia860.py:1007`` sets ``pmax = net_summer_capacity_mw``,
  so D1 is **NET SUMMER** (caiso-181 called it "nameplate"; that is corrected here).
* **D2** the binned fleet's actual **LP** ``pmax`` sum per ``(plant_code, plant_group)``.
  The CAISO keeper runs ``cc_nameplate_summer_derate=True``
  (``pipeline/backcast_config.py:1744``), under which ``fleet_to_bins`` divides the CC bin
  capacity by ``cc_summer_derate_ratio`` so the LP carries **full NAMEPLATE**
  (``fleet/campd_bins.py:1684-1694``).
* **D3** ``pmax x availability(t)`` — the LP's hourly ceiling. Reconstructed here from its
  two CAISO-material multiplicative components (the CC seasonal re-derate and the CAMPD
  unit-outage derate) and labelled ``d3_partial`` so the partial reconstruction is visible.

**The numerator** is CAMPD ``grossLoad`` (N1). N2 converts it to **NET** with the
committed measured artifact ``parasitic_load_factors.parquet``
(``campd.compute_parasitic_factors``), class defaults ``campd.DEFAULT_PARASITIC_LOAD_PCT``
where a plant is missing or out-of-band.

Attribution, fixed in PRECHECK §3 before measurement, as shares of ``X(N1,D1)``::

    H_GROSS   = [X(N1,D1) - X(N2,D1)] / X(N1,D1)
    H_NPBASIS = [X(N2,D1) - X(N2,D2)] / X(N1,D1)
    RESIDUAL  =  X(N2,D2)            / X(N1,D1)

**H-DENOM** is measured separately: the extract's ``removed_mw`` is EIA-860 **NAMEPLATE**
(``derive_campd_unit_outages.build_capacity_index``, whose own docstring at line 244 claims
it is "the same basis as the model bin denominator the derate divides into"), while the
denominator it divides into is D1 = net summer. Over-removal MW-h is measured against the
year's committed envelope depth.

Instruments are **REUSED, never re-implemented**: ``_caiso181_cems_confrontation._year_grids``
(NaN preserved — a missing CAMPD hour is never a contradiction), ``campd.CAMPD_UNIT_PLANT_REMAP``,
``outages._generic_unit_outage_target`` / ``_iso_plant_capacity`` / ``unit_outage_derate_factors``,
``fleet.cc_summer_derate_ratio``. **No LP. No new intake. No data file written.**

Usage::

    python scripts/probes/_caiso184_capacity_basis_census.py

Writes ``results/calibration/_caiso184_capacity_basis_census.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT  # noqa: E402
from market_sim.data.fleet.campd_bins import cc_summer_derate_ratio  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    HOURS_PER_YEAR,
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _has_hour_grain,
    _hour_of_year,
    _iso_plant_capacity,
    outage_hour_mask,
    unit_outage_csv_for_iso,
    unit_outage_derate_factors,
    unit_outage_event_window,
)

from scripts.probes._caiso181_cems_confrontation import _year_grids  # noqa: E402

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results" / "calibration" / "_caiso184_capacity_basis_census.json"

# Committed envelope depth per year (caiso-180 census, day-grain A0) and the
# caiso-183 hour-grain repaired depth. The B-DENOM / B-ARTIFACT denominator is
# the HOUR-GRAIN depth, because that is what the current keeper holds.
DEPTH_MWH_HOURGRAIN: dict[int, float] = {
    2023: 34.836e6,
    2024: 41.042e6,
    2025: 52.955e6,
}

# The CC groups whose LP capacity is raised to nameplate under
# cc_nameplate_summer_derate (fleet/campd_bins.py:1690).
_CC_GROUPS = ("CC_REGULAR", "CC_CHP")

# Summer months the CC re-derate covers (fleet/arrays.py summer mask).
_SUMMER_MONTHS = (6, 7, 8, 9)

# PRECHECK §4 bars, fixed before measurement.
B_ATTRIB_BAR = 0.50  # H_GROSS + H_NPBASIS + H_REMAP must exceed this, every year
B_ARTIFACT_DEPTH_BAR = 0.005  # RESIDUAL < 0.5 % of committed depth
B_ARTIFACT_CAPYEAR_BAR = 0.002  # RESIDUAL < 0.2 % of thermal capacity-year
B_DENOM_BAR = 0.02  # over-removal >= 2 % of depth in >= 2 of 3 years

# The two CAMPD_UNIT_PLANT_REMAP plants caiso-181 §5 item 2 named.
_REMAP_PLANTS = (62115, 62116)


def _parasitic_factors() -> dict[int, float]:
    """Return ``{plant_code: net/gross factor}`` from the committed artifact.

    Pooled (``year == 0``) rows of ``parasitic_load_factors.parquet`` — annual
    EIA-923 NET over annual CAMPD GROSS per plant, with that derive's own
    class default already substituted for out-of-band reconciliations. Same
    read as ``fleet.campd_bins._ramp_parasitic_factor_map``; empty when absent.
    """
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    pooled = df[df["year"] == 0]
    return {
        int(p): float(f)
        for p, f in zip(pooled["plant_id"], pooled["parasitic_factor"])
        if float(f) > 0.0
    }


def _net_factor(plant_code: int, group: str, measured: dict[int, float]) -> tuple[float, str]:
    """Return ``(net/gross factor, provenance)`` for a bin."""
    f = measured.get(int(plant_code))
    if f is not None and 0.0 < f <= 1.0:
        return f, "measured"
    pct = DEFAULT_PARASITIC_LOAD_PCT.get(group)
    if pct is None:
        return 1.0 - campd._DEFAULT_PARASITIC_LOAD_PCT, "class_default_unknown_group"
    return 1.0 - pct, "class_default"


def _d2_for_bin(target: tuple[int, str], d1: float) -> tuple[float, float | None]:
    """Return ``(D2, cc_ratio)`` — the LP's own capacity for this bin.

    Reproduces ``fleet/campd_bins.py:1690-1694`` exactly: under
    ``cc_nameplate_summer_derate`` a CC bin's summed net-summer capacity is
    divided by ``cc_summer_derate_ratio`` (net_summer / nameplate) so the LP
    carries full nameplate. Every other group is unchanged, so D2 == D1.
    """
    code, group = target
    if group not in _CC_GROUPS:
        return d1, None
    ratio = cc_summer_derate_ratio(int(code))
    if ratio is None or ratio <= 0.0:
        return d1, None
    return d1 / ratio, ratio


def _bin_cems(year: int) -> dict[tuple[int, str], np.ndarray]:
    """Aggregate CAMPD gross onto the model 8760 clock, per LP bin.

    Identical construction to ``_caiso181_cems_confrontation.run_l2``: the CAMPD
    year clock is mapped with ``outages._hour_of_year`` (the same non-leap
    mapping the loader uses), Feb 29 is dropped from BOTH sides, and units are
    routed with the shipped ``_generic_unit_outage_target``.
    """
    grids, _ = _year_grids(year)
    clock = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    hoy = np.array([_hour_of_year(t.month, t.day, t.hour) for t in clock], dtype=int)
    is_feb29 = np.array([(t.month == 2 and t.day == 29) for t in clock])
    keep = ~is_feb29

    csv = pd.read_csv(unit_outage_csv_for_iso(ISO))
    group_by_unit = {
        (int(r.facility_id), str(r.unit_id)): str(r.plant_group)
        for r in csv.itertuples(index=False)
    }
    out: dict[tuple[int, str], np.ndarray] = {}
    for (fac, uid), gross in grids.items():
        group = group_by_unit.get((fac, uid))
        if group is None:
            continue
        tgt = _generic_unit_outage_target(fac, uid, group)
        if tgt is None:
            continue
        arr = out.setdefault(tgt, np.zeros(HOURS_PER_YEAR))
        np.add.at(arr, hoy[keep], np.nan_to_num(gross)[keep])
    return out


def _summer_mask(year: int) -> np.ndarray:
    """Boolean 8760 mask of the CC re-derate's summer months, model clock."""
    clock = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h")
    return np.isin(clock.month.to_numpy(), _SUMMER_MONTHS)


def run_census(year: int) -> dict:
    """Measure X(N,D) for the four (numerator, denominator) pairs, per bin."""
    cap_d1 = _iso_plant_capacity(ISO)
    measured = _parasitic_factors()
    cems = _bin_cems(year)
    factors = unit_outage_derate_factors(year, hours=HOURS_PER_YEAR, iso=ISO)
    summer = _summer_mask(year)

    tot = {"n1d1": 0.0, "n2d1": 0.0, "n2d2": 0.0, "n2d3": 0.0}
    hours_over = {"n1d1": 0, "n2d1": 0, "n2d2": 0, "n2d3": 0}
    remap_residual = 0.0
    thermal_capyear_d2 = 0.0
    rows = []
    n_measured = 0

    for tgt, gross in cems.items():
        d1 = cap_d1.get(tgt)
        if d1 is None or d1 <= 0.0:
            continue
        code, group = tgt
        f_net, prov = _net_factor(code, group, measured)
        n_measured += prov == "measured"
        net = gross * f_net
        d2, ratio = _d2_for_bin(tgt, d1)
        thermal_capyear_d2 += d2

        # D3-partial: the LP ceiling rebuilt from its two CAISO-material
        # multiplicative components — the CC seasonal re-derate that the
        # nameplate raise is paired with (arrays.py:738-748) and the CAMPD
        # unit-outage derate (arrays.py:929). Labelled partial: the statistical
        # WEFOR/POF/age block is dropped for CC in a historic backcast, and the
        # remaining classes' flat _SUMMER_CLASS_DERATE is NOT reconstructed here.
        d3 = np.full(HOURS_PER_YEAR, d2, dtype=float)
        if ratio is not None and ratio < 1.0:
            d3[summer] *= ratio
        ufac = factors.get(tgt)
        if ufac is not None:
            d3 = d3 * ufac

        x = {
            "n1d1": float(np.clip(gross - d1, 0.0, None).sum()),
            "n2d1": float(np.clip(net - d1, 0.0, None).sum()),
            "n2d2": float(np.clip(net - d2, 0.0, None).sum()),
            "n2d3": float(np.clip(net - d3, 0.0, None).sum()),
        }
        h = {
            "n1d1": int((gross > d1).sum()),
            "n2d1": int((net > d1).sum()),
            "n2d2": int((net > d2).sum()),
            "n2d3": int((net > d3).sum()),
        }
        for k in tot:
            tot[k] += x[k]
            hours_over[k] += h[k]
        if int(code) in _REMAP_PLANTS:
            remap_residual += x["n2d2"]
        if x["n1d1"] > 0.0 or x["n2d2"] > 0.0:
            rows.append(
                {
                    "plant_code": int(code),
                    "plant_group": group,
                    "d1_net_summer_mw": round(d1, 3),
                    "d2_lp_mw": round(d2, 3),
                    "cc_summer_ratio": round(ratio, 6) if ratio is not None else None,
                    "net_over_gross": round(f_net, 6),
                    "net_factor_source": prov,
                    "max_f_cems_n1d1": round(float((gross / d1).max()), 6),
                    "max_f_cems_n2d2": round(float((net / d2).max()), 6),
                    "x_n1d1_mwh": round(x["n1d1"], 1),
                    "x_n2d1_mwh": round(x["n2d1"], 1),
                    "x_n2d2_mwh": round(x["n2d2"], 1),
                    "x_n2d3_mwh": round(x["n2d3"], 1),
                    "hours_over_n2d2": h["n2d2"],
                }
            )

    rows.sort(key=lambda d: -d["x_n1d1_mwh"])
    base = tot["n1d1"]
    attrib = {
        "h_gross": (base - tot["n2d1"]) / base if base > 0 else 0.0,
        "h_npbasis": (tot["n2d1"] - tot["n2d2"]) / base if base > 0 else 0.0,
        "residual": tot["n2d2"] / base if base > 0 else 0.0,
    }
    depth = DEPTH_MWH_HOURGRAIN[year]
    return {
        "year": year,
        "n_bins": len(cems),
        "n_bins_with_measured_parasitic": n_measured,
        "excess_mwh": {k: round(v, 1) for k, v in tot.items()},
        "excess_share_of_depth": {k: round(v / depth, 6) for k, v in tot.items()},
        "bin_hours_over": hours_over,
        "attribution": {k: round(v, 6) for k, v in attrib.items()},
        "h_remap_share_of_residual": (
            round(remap_residual / tot["n2d2"], 6) if tot["n2d2"] > 0 else 0.0
        ),
        "h_remap_share_of_base": round(remap_residual / base, 6) if base > 0 else 0.0,
        "thermal_capyear_mwh_d2": round(thermal_capyear_d2 * HOURS_PER_YEAR, 1),
        "residual_share_of_thermal_capyear": (
            round(tot["n2d2"] / (thermal_capyear_d2 * HOURS_PER_YEAR), 8)
            if thermal_capyear_d2 > 0
            else 0.0
        ),
        "committed_depth_mwh": depth,
        "worst_15_bins": rows[:15],
    }


def _availability_both_bases(year: int) -> dict[tuple[int, str], tuple[np.ndarray, np.ndarray, float, float]]:
    """Rebuild the unit-outage availability arrays under BOTH denominators.

    Reproduces ``outages._unit_outage_factors_from_events`` exactly — same row
    filter, same ``unit_outage_event_window`` / ``outage_hour_mask``, same
    concurrent-row summation and same ``clip(1 - v, 0, 1)`` — once with the
    shipped denominator D1 (net summer) and once with D2 (the LP's own capacity,
    nameplate for CC). Returns ``{bin: (avail_now, avail_fix, d1, d2)}``.
    """
    cap_d1 = _iso_plant_capacity(ISO)
    df = pd.read_csv(unit_outage_csv_for_iso(ISO))
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    has_hours = _has_hour_grain(df)
    has_derate = "derate_factor" in df.columns

    sums_now: dict[tuple[int, str], np.ndarray] = {}
    sums_fix: dict[tuple[int, str], np.ndarray] = {}
    caps: dict[tuple[int, str], tuple[float, float]] = {}
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap_d1:
            continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        w_start, w_stop = unit_outage_event_window(r, has_hours)
        mask = outage_hour_mask(w_start, w_stop, year, HOURS_PER_YEAR)
        if not mask.any():
            continue
        d1 = cap_d1[tgt]
        d2, _ = _d2_for_bin(tgt, d1)
        caps[tgt] = (d1, d2)
        sums_now.setdefault(tgt, np.zeros(HOURS_PER_YEAR))[mask] += (
            removed_frac * float(ucap) / d1
        )
        sums_fix.setdefault(tgt, np.zeros(HOURS_PER_YEAR))[mask] += (
            removed_frac * float(ucap) / d2
        )
    return {
        tgt: (
            np.clip(1.0 - sums_now[tgt], 0.0, 1.0),
            np.clip(1.0 - sums_fix[tgt], 0.0, 1.0),
            caps[tgt][0],
            caps[tgt][1],
        )
        for tgt in sums_now
    }


def run_h_denom(year: int) -> dict:
    """H-DENOM — over-removal from the nameplate-numerator / net-summer-denominator mix.

    The extract's ``unit_capacity_mw`` is EIA-860 **NAMEPLATE**
    (``derive_campd_unit_outages.build_capacity_index``; ``observed_peak`` rows carry
    the unit's CAMPD peak **gross** instead — a third basis, counted separately). The
    denominator it divides into is D1 = **net summer**. This measures the MW-h that
    basis mix removes beyond the extract's own documented same-basis invariant, EXACTLY
    (not as a bound): both availability arrays are rebuilt with the shipped accumulator,
    including concurrent-row summation and the clip, and the difference is valued at the
    LP capacity D2 the multiplier is actually applied to.
    """
    arrays = _availability_both_bases(year)
    over_mwh = 0.0
    depth_now = 0.0
    depth_fix = 0.0
    n_hours_increase = 0
    by_group: dict[str, float] = {}
    by_bin = []
    for tgt, (a_now, a_fix, d1, d2) in arrays.items():
        removed_now = (1.0 - a_now) * d2
        removed_fix = (1.0 - a_fix) * d2
        delta = removed_now - removed_fix
        n_hours_increase += int((delta < -1e-9).sum())
        d = float(delta.sum())
        over_mwh += d
        depth_now += float(removed_now.sum())
        depth_fix += float(removed_fix.sum())
        if d > 0:
            by_group[tgt[1]] = by_group.get(tgt[1], 0.0) + d
            by_bin.append(
                {
                    "plant_code": tgt[0],
                    "plant_group": tgt[1],
                    "d1_net_summer_mw": round(d1, 3),
                    "d2_lp_mw": round(d2, 3),
                    "over_removal_mwh": round(d, 1),
                }
            )
    by_bin.sort(key=lambda x: -x["over_removal_mwh"])
    return {
        "year": year,
        "n_bins_with_windows": len(arrays),
        "recomputed_depth_mwh_shipped_denominator": round(depth_now, 1),
        "recomputed_depth_mwh_lp_denominator": round(depth_fix, 1),
        "caiso183_published_depth_mwh": DEPTH_MWH_HOURGRAIN[year],
        "over_removal_mwh": round(over_mwh, 1),
        "over_removal_share_of_depth": (
            round(over_mwh / depth_now, 6) if depth_now > 0 else 0.0
        ),
        "n_bin_hours_removal_would_increase": n_hours_increase,
        "by_plant_group_mwh": {k: round(v, 1) for k, v in sorted(by_group.items())},
        "worst_10_bins": by_bin[:10],
    }


def run_noncc_basis(year: int) -> dict:
    """Size the leg the LP-consistency repair does NOT cover (rule 11 honesty).

    The repair puts the derate denominator on the capacity the multiplier is applied
    to, which under ``cc_nameplate_summer_derate`` moves ONLY the CC bins (every other
    group has D2 == D1). At a non-CC bin the numerator stays EIA-860 **nameplate**
    (``unit_capacity_mw``) while the denominator stays **net summer** — the same basis
    mix, unrepaired. Its size is measured here from the committed extract's own
    ``plant_capacity_mw`` column, which the deriver builds as the sum of the SAME
    ``derate_mw`` capacities as the numerator (``derive_campd_unit_outages.py:1384``),
    so ``plant_capacity_mw / D1`` IS the basis gap.

    Restricted to facilities whose extract rows are all one ``plant_group``: at a mixed
    facility ``plant_capacity_mw`` spans groups the group-scoped D1 does not, so the
    ratio would not be a basis measurement. The excluded facilities are counted.
    """
    cap_d1 = _iso_plant_capacity(ISO)
    df = pd.read_csv(unit_outage_csv_for_iso(ISO))
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    groups_per_fac = df.groupby("facility_id")["plant_group"].nunique()
    single = set(groups_per_fac[groups_per_fac == 1].index)

    arrays = _availability_both_bases(year)
    by_group: dict[str, dict] = {}
    n_mixed_skipped = 0
    src_counts: dict[str, int] = {}
    for r in df.drop_duplicates(subset=["facility_id", "unit_id"]).itertuples(
        index=False
    ):
        src_counts[str(r.capacity_source)] = src_counts.get(str(r.capacity_source), 0) + 1

    seen: set[tuple[int, str]] = set()
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt in seen or tgt[1] in _CC_GROUPS:
            continue
        if int(r.facility_id) not in single:
            n_mixed_skipped += 1
            continue
        d1 = cap_d1.get(tgt)
        if d1 is None or d1 <= 0.0:
            continue
        seen.add(tgt)
        fac_cap = float(r.plant_capacity_mw)
        if fac_cap <= 0.0:
            continue
        g = by_group.setdefault(
            tgt[1], {"n_bins": 0, "ratio_sum": 0.0, "unrepaired_mwh": 0.0}
        )
        g["n_bins"] += 1
        g["ratio_sum"] += fac_cap / d1
        # The unrepaired over-removal, valued the same way H-DENOM values the CC
        # leg: the extra removed fraction times the bin capacity over its outage
        # hours, using the extract's own same-basis denominator as the target.
        arr = arrays.get(tgt)
        if arr is not None:
            a_now, _, _, d2 = arr
            scale = min(1.0, d1 / fac_cap) if fac_cap > 0 else 1.0
            removed_now = (1.0 - a_now) * d2
            removed_fix = np.clip(1.0 - (1.0 - a_now) * scale, 0.0, 1.0)
            removed_fix = (1.0 - removed_fix) * d2
            g["unrepaired_mwh"] += float((removed_now - removed_fix).sum())

    depth = sum(
        float(((1.0 - a_now) * d2).sum()) for a_now, _, _, d2 in arrays.values()
    )
    return {
        "year": year,
        "capacity_source_counts": src_counts,
        "n_mixed_group_facility_rows_skipped": n_mixed_skipped,
        "by_group": {
            k: {
                "n_bins": v["n_bins"],
                "mean_nameplate_over_net_summer": round(v["ratio_sum"] / v["n_bins"], 4),
                "unrepaired_over_removal_mwh": round(v["unrepaired_mwh"], 1),
                "share_of_depth": round(v["unrepaired_mwh"] / depth, 6) if depth else 0.0,
            }
            for k, v in sorted(by_group.items())
        },
        "total_unrepaired_share_of_depth": (
            round(sum(v["unrepaired_mwh"] for v in by_group.values()) / depth, 6)
            if depth
            else 0.0
        ),
    }


def main() -> None:
    out: dict = {
        "iso": ISO,
        "years": list(YEARS),
        "precheck": "results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md",
        "precheck_sha256": (
            "33fa2093a8a253982f816a56c420515d4a5ddebbcf2ad1432974a15ccbce9a23"
        ),
        "bars": {
            "B_ATTRIB": B_ATTRIB_BAR,
            "B_ARTIFACT_depth": B_ARTIFACT_DEPTH_BAR,
            "B_ARTIFACT_capyear": B_ARTIFACT_CAPYEAR_BAR,
            "B_DENOM": B_DENOM_BAR,
        },
        "census": {},
        "h_denom": {},
        "noncc_basis": {},
    }
    for year in YEARS:
        out["census"][str(year)] = run_census(year)
        out["h_denom"][str(year)] = run_h_denom(year)
        out["noncc_basis"][str(year)] = run_noncc_basis(year)

    # Pre-registered verdicts, evaluated mechanically (PRECHECK §4).
    attrib_pass = all(
        (
            out["census"][str(y)]["attribution"]["h_gross"]
            + out["census"][str(y)]["attribution"]["h_npbasis"]
            + out["census"][str(y)]["h_remap_share_of_base"]
        )
        > B_ATTRIB_BAR
        for y in YEARS
    )
    artifact_pass = all(
        out["census"][str(y)]["excess_share_of_depth"]["n2d2"] < B_ARTIFACT_DEPTH_BAR
        and out["census"][str(y)]["residual_share_of_thermal_capyear"]
        < B_ARTIFACT_CAPYEAR_BAR
        for y in YEARS
    )
    denom_years = sum(
        out["h_denom"][str(y)]["over_removal_share_of_depth"] >= B_DENOM_BAR
        for y in YEARS
    )
    out["verdicts"] = {
        "B_ATTRIB": "PASS" if attrib_pass else "FAIL",
        "B_ARTIFACT": "FIRES" if artifact_pass else "does not fire",
        "B_DENOM_years_at_or_above_bar": denom_years,
        "B_DENOM": "licenses an arm" if denom_years >= 2 else "no arm",
        "G_MONO_violations": sum(
            out["h_denom"][str(y)]["n_bin_hours_removal_would_increase"] for y in YEARS
        ),
        "branch": (
            "A (not identified, STOP)"
            if not attrib_pass
            else ("C (build the repair)" if denom_years >= 2 else "B (no arm, file)")
        ),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["verdicts"], indent=2))
    for y in YEARS:
        c = out["census"][str(y)]
        d = out["h_denom"][str(y)]
        print(
            f"{y}: X(N1,D1)={c['excess_mwh']['n1d1']:,.0f}  "
            f"X(N2,D1)={c['excess_mwh']['n2d1']:,.0f}  "
            f"X(N2,D2)={c['excess_mwh']['n2d2']:,.0f}  "
            f"X(N2,D3p)={c['excess_mwh']['n2d3']:,.0f}  "
            f"| gross={c['attribution']['h_gross']:.3f} "
            f"npbasis={c['attribution']['h_npbasis']:.3f} "
            f"resid={c['attribution']['residual']:.3f} "
            f"| H-DENOM={d['over_removal_share_of_depth']:.4f} of depth"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
