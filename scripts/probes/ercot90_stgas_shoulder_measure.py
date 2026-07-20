"""ERCOT-90 measure-first probe: CAMPD hourly ST_GAS vs the keeper's ST_GAS
class dispatch in the shoulder mid-band residual hours.

The ERCOT-89 charter (`docs/handoffs/ercot-shoulder-online-envelope-2026-07.md`
§8.3) named this measurement as its follow-up: in the residual $150-500 band
hours the keeper rides ST_GAS ~4.1 -> 6.1 GW (control -> residual) while the
*inferred* real non-CHP steam-gas contribution is ~1-2 GW — but that inference
was indirect (the NP3-965 corpus lacks ST restypes; the number came from
EIA-930 gas-total minus measured merchant CC/CT Base Points). This probe
measures it DIRECTLY: CAMPD/CEMS hourly gross load for the model's own 17
ERCOT ST_GAS plants (unit-resolved at the two split facilities), netted by the
class parasitic factor, against the keeper's hourly ST_GAS class dispatch —
per hour set (residual / formed / bin-matched control) and per conditioning
cell (net-load bin x season x 4h block), the ERCOT-89 conventions.

MEASUREMENT ONLY — no apply seam, no mechanism, nothing here feeds the model.
Model side reads the committed ercot86 keeper hourly sidecars
(`results/calibration/ercot86_rtwall_fullspan/hourly/`) — NO keeper replay.

Adjudication axes (rule-19 seam ownership — where would a step-2 fix land?):

* **Drag-shape miss** — the `gas_st_netload_drag` min-gen floor
  (`clip(slope*netGW + intercept, 0, cap) x pmax` on non-peaker, non-peak-
  tranche ST_GAS; the ONLY floor mechanism on the class, keeper D-2) binds in
  the residual hours at a level the drag's own driver evidence (CAMPD
  *overnight* low-price CF, `docs/ercot-st-gas-netload-drag-2026-06.md`) does
  not support. The floor is reconstructed here from the keeper's own hourlies:
  `NL_hat = demand - wind - solar dispatch` >= the runner's potential-
  convention net-load (dispatch <= potential), so `floor_ub = frac(NL_hat) x
  base` is an UPPER bound on the true floor — if model dispatch in the
  residual hours materially exceeds even the upper-bound floor, the
  over-dispatch is NOT floor-forced, and the drag is not the owning seam.
* **Committed-offer level miss** — the over-dispatch is economic (model MW >>
  floor_ub): the LP clears ST_GAS mid-merit at its committed/economic offers
  (`gas_st_committed_hr_mult` / `gas_st_econ_hr_mult`) in hours where the real
  units were not even committed. Owning seam: the ST_GAS committed offer
  levels (offer_curve_by_group), or the default-off
  `ercot_offer_surface_cleared_share_steam` conditional.
* **Availability-basis miss** — the model carries ST_GAS capability in those
  hours that reality did not have online or startable (class-day only-OUT-is-
  out DAM availability x nameplate vs the measured concurrent maximum).

Rule 22 note: the drag curve re-derives ONLY on a source-data update. This
probe checks the applied floor against the drag's OWN driver evidence (the
overnight CF-vs-net-load relationship, recomputed from the same CAMPD source)
— a mismatch is a bug fix with citation, never a residual re-tune; the curve
is never re-fit here.

Usage::

    python scripts/probes/ercot90_stgas_shoulder_measure.py \
        [--years 2024 2025] \
        [--keeper results/calibration/ercot86_rtwall_fullspan] \
        [--out data/raw/_validation-source/ercot90_stgas_shoulder_measurement.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HOURS,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _netload_pct,
)
from derive_ercot_shoulder_online_span import (  # noqa: E402
    HOUR_BLOCK_H,
    SEASON_OF_MONTH,
)

from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    ST_GAS_PEAKER_PLANTS,
    _WAP_COAL_UNITS,
)

DEFAULT_KEEPER = REPO / "results" / "calibration" / "ercot86_rtwall_fullspan"
DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot90_stgas_shoulder_measurement.json"
)
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
ERCOT89_JSON = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot89_shoulder_online_measurement.json"
)
BIN_CSV = REPO / "data" / "raw" / "reference" / "custom-bin-assignments.csv"
DAM_AVAIL_CSV = REPO / "data" / "raw" / "ercot-thermal-dam-availability.csv"
CAMPD_UNIT_DIR = REPO / "data" / "raw" / "campd-unit-level"

MID_BAND = (150.0, 500.0)  # the ERCOT-86/87/88/89 moderate-tightness band, $/MWh

# CAMPD reports gross; the model dispatches net (campd.plant_hourly_net
# convention, same factor the sibling ST_GAS drag derives use).
_ST_NET_OF_GROSS = 1.0 - DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]

# The drag's driver-evidence window: CAMPD *overnight* low-price hours
# (23h-05h local standard), docs/ercot-st-gas-netload-drag-2026-06.md.
OVERNIGHT_START_H, OVERNIGHT_END_H = 23, 6

# Split facilities: the model's ST_GAS bins 34702 / 49392 are unit subsets of
# CAMPD facilities 3470 (W A Parish; WAP5-8 are the coal units) and 4939
# (Barney M Davis; unit "1" is the steamer) — data.outages._unit_outage_target.
_SPLIT_PARENT = {34702: 3470, 49392: 4939}

# Month number (1-12) per model hour-of-year, for the season axis.
_MONTH_OF_HOY = np.searchsorted(
    np.asarray(_MONTH_START_HOUR), np.arange(HOURS), side="right"
)


def _st_gas_plants() -> pd.DataFrame:
    """The model's ERCOT ST_GAS plant set from the CAMPD bin-assignment CSV.

    One row per plant: code, name, nameplate, peak-tranche %, and whether the
    plant is drag-covered (non-peaker: not in ST_GAS_PEAKER_PLANTS — peaker-
    class plants dispatch purely economically, no floor).
    """
    df = pd.read_csv(BIN_CSV)
    st = df[df["Plant_Group"] == "ST_GAS"].copy()
    st = st[
        [
            "Plant_Code",
            "Plant_Name",
            "Nameplate_MW",
            "Pct_Peaking",
            "ERCOT_Zone",
        ]
    ].reset_index(drop=True)
    st["drag_covered"] = ~st["Plant_Code"].isin(ST_GAS_PEAKER_PLANTS)
    return st


def _campd_st_hourly(
    year: int, plants: pd.DataFrame
) -> tuple[np.ndarray, dict[int, np.ndarray], list[str]]:
    """Measured net MW per hour for the model's ST_GAS plants, from CAMPD.

    Reads the unit-level TX extract (unit grain is REQUIRED here: two model
    bins are unit subsets of mixed facilities), keeps only steam units (drops
    any unitType naming a combustion turbine or combined cycle — catches the
    CC->CT conversion strings too), routes the split facilities per the model's
    own unit rules, sums to the plant per hour on the fixed local-standard
    non-leap clock (Feb 29 dropped, the campd.py convention), and nets by the
    class parasitic factor. NaN gross = offline unit-hour = 0 MW.

    Returns (fleet_total_8760, {plant_code: 8760}, notes).
    """
    path = CAMPD_UNIT_DIR / f"TX_{year}.parquet"
    raw = pd.read_parquet(
        path,
        columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType"],
    )
    fid = pd.to_numeric(raw["facilityId"], errors="coerce").fillna(-1).astype(int)
    ut = raw["unitType"].astype(str).str.lower()
    is_ct_cc = ut.str.contains("combustion turbine") | ut.str.contains("combined cycle")

    notes: list[str] = []
    per_plant: dict[int, np.ndarray] = {}
    fleet = np.zeros(HOURS)
    for row in plants.itertuples(index=False):
        code = int(row.Plant_Code)
        parent = _SPLIT_PARENT.get(code, code)
        m = (fid == parent).to_numpy() & ~is_ct_cc.to_numpy()
        if code == 34702:  # W A Parish gas steamers = non-coal, non-CT units
            m &= ~raw["unitId"].astype(str).isin(_WAP_COAL_UNITS).to_numpy()
        elif parent == 3470:  # never double-count Parish under another code
            m &= np.zeros(len(raw), dtype=bool)
        if code == 49392:  # Barney M Davis steam unit 1
            m &= (raw["unitId"].astype(str) == "1").to_numpy()
        elif parent == 4939:
            m &= np.zeros(len(raw), dtype=bool)
        sub = raw.loc[m]
        series = np.zeros(HOURS)
        if len(sub):
            dt = pd.to_datetime(sub["date"])
            mo = dt.dt.month.to_numpy()
            dy = dt.dt.day.to_numpy()
            hh = pd.to_numeric(sub["hour"], errors="coerce").to_numpy(int)
            ok = ~((mo == 2) & (dy == 29))
            hoy = np.asarray(_MONTH_START_HOUR)[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
            gross = np.nan_to_num(sub["grossLoad"].to_numpy(float), nan=0.0)[ok]
            valid = (hoy >= 0) & (hoy < HOURS)
            np.add.at(series, hoy[valid], gross[valid])
            series *= _ST_NET_OF_GROSS
        else:
            notes.append(f"plant {code} ({row.Plant_Name}): no CAMPD rows in {year}")
        per_plant[code] = series
        fleet += series
    return fleet, per_plant, notes


def _model_side(keeper: Path, year: int) -> dict[str, np.ndarray]:
    """Keeper P1 hourlies: ST_GAS MW, VRE dispatch, demand, dw price, NL_hat."""
    ch = pd.read_parquet(keeper / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["year"] == year) & (ch["pass"].astype(str) == "P1")]
    piv = (
        ch.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack("klass")
        .reindex(range(HOURS))
        .fillna(0.0)
    )
    sy = pd.read_parquet(keeper / "hourly" / f"system_{year}.parquet")
    sy = sy[(sy["year"] == year) & (sy["pass"].astype(str) == "P1")]
    demand = sy.groupby("hour")["demand"].sum().reindex(range(HOURS)).to_numpy(float)
    w = sy["price"] * sy["demand"]
    price = (
        (w.groupby(sy["hour"]).sum() / sy.groupby("hour")["demand"].sum())
        .reindex(range(HOURS))
        .to_numpy(float)
    )
    vre = piv.get("wind", 0.0) + piv.get("solar", 0.0)
    vre = np.asarray(vre, dtype=float)
    return {
        "st_mw": piv["ST_GAS"].to_numpy(float),
        "price": price,
        "demand": demand,
        # Upper bound on the runner's potential-convention net-load: VRE
        # dispatch <= potential, so demand - dispatch >= demand - potential.
        "nl_hat": demand - vre,
    }


def _dam_avail_st(year: int) -> np.ndarray:
    """ST_GAS class-day DAM availability fraction per hour (NaN uncovered)."""
    df = pd.read_csv(DAM_AVAIL_CSV)
    df = df[df["class"] == "ST_GAS"].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    arr = np.full(HOURS, np.nan)
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue
        lo = int(np.asarray(_MONTH_START_HOUR)[mo - 1]) + (dy - 1) * 24
        arr[lo : lo + 24] = float(r.avail)
    return arr


def _drag_params(keeper: Path) -> dict[str, float]:
    """The keeper's armed drag-curve coefficients, from its run_config."""
    rc = json.loads((keeper / "run_config.json").read_text())
    sc = rc["scenario_config"]
    if not sc.get("gas_st_netload_drag", False):
        raise SystemExit("keeper does not arm gas_st_netload_drag — probe is moot")
    return {
        "slope_per_gw": float(sc["gas_st_drag_slope_per_gw"]),
        "intercept": float(sc["gas_st_drag_intercept"]),
        "cap": float(sc["gas_st_drag_cap"]),
        "committed_hr_mult": sc.get("gas_st_committed_hr_mult"),
        "econ_hr_mult": sc.get("gas_st_econ_hr_mult"),
        "cleared_share_steam": sc.get("ercot_offer_surface_cleared_share_steam"),
    }


def _floor_series(
    nl_hat_mw: np.ndarray,
    base_mw: float,
    params: dict[str, float],
    avail: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reconstructed drag floor per hour: (frac, floor_ub, floor_avail).

    ``floor_ub = frac(NL_hat) x base`` is an upper bound (NL_hat >= true
    net-load; no availability cap). ``floor_avail = min(frac, avail_day) x
    base`` refines with the class-day DAM availability (the per-tranche cap is
    ``avail x pmax``; at fleet grain ``sum_g min(frac, avail_g) x pmax_g ~=
    min(frac, avail_class) x base``) — still an estimate, disclosed.
    """
    frac = np.clip(
        params["slope_per_gw"] * (nl_hat_mw / 1000.0) + params["intercept"],
        0.0,
        params["cap"],
    )
    floor_ub = frac * base_mw
    floor_avail = np.minimum(frac, np.nan_to_num(avail, nan=1.0)) * base_mw
    return frac, floor_ub, floor_avail


def _med(x: np.ndarray, mask: np.ndarray) -> float | None:
    """Median of ``x`` over ``mask`` hours, rounded, None when empty."""
    v = x[mask]
    v = v[np.isfinite(v)]
    return round(float(np.median(v)), 1) if v.size else None


def _set_summary(
    mask: np.ndarray,
    meas: np.ndarray,
    model: np.ndarray,
    floor_ub: np.ndarray,
    floor_avail: np.ndarray,
    price: np.ndarray,
    rt: np.ndarray,
    nl_hat: np.ndarray,
) -> dict:
    """One hour-set's measured-vs-model ST_GAS summary."""
    n = int(mask.sum())
    if n == 0:
        return {"n": 0}
    over = model - meas
    econ_excess = model - floor_ub
    # "economic" = dispatch above even the upper-bound floor (2% tolerance);
    # only these hours could NOT be explained by the drag floor.
    economic = mask & (model > floor_ub * 1.02)
    return {
        "n": n,
        "meas_net_med": _med(meas, mask),
        "model_med": _med(model, mask),
        "model_minus_meas_med": _med(over, mask),
        "model_over_meas_ratio_med": (
            round(float(np.median((model[mask] + 1.0) / (meas[mask] + 1.0))), 2)
        ),
        "floor_ub_med": _med(floor_ub, mask),
        "floor_avail_med": _med(floor_avail, mask),
        "model_minus_floor_ub_med": _med(econ_excess, mask),
        "share_hours_model_above_floor_ub": round(float(economic.sum() / n), 3),
        "meas_minus_floor_ub_med": _med(meas - floor_ub, mask),
        "model_price_med": _med(price, mask),
        "actual_rt_med": _med(rt, mask),
        "nl_hat_med": _med(nl_hat, mask),
    }


def measure_year(year: int, keeper: Path, params: dict[str, float]) -> dict:
    """Measure the ST_GAS shoulder-hour displacement for one year."""
    plants = _st_gas_plants()
    base_mw = float(
        (
            plants.loc[plants["drag_covered"], "Nameplate_MW"]
            * (1.0 - plants.loc[plants["drag_covered"], "Pct_Peaking"] / 100.0)
        ).sum()
    )
    nameplate = float(plants["Nameplate_MW"].sum())

    meas, per_plant, notes = _campd_st_hourly(year, plants)
    ms = _model_side(keeper, year)
    avail = _dam_avail_st(year)
    frac, floor_ub, floor_avail = _floor_series(ms["nl_hat"], base_mw, params, avail)

    actual = pd.read_parquet(ACTUAL_LMP)
    act = actual[actual["year"] == year].set_index("hour")["rt"]
    rt = act.reindex(range(HOURS)).to_numpy(float)

    price = ms["price"]
    st_model = ms["st_mw"]

    in_band = (rt >= MID_BAND[0]) & (rt <= MID_BAND[1])
    model_below = price < MID_BAND[0]
    model_in_band = (price >= MID_BAND[0]) & (price <= MID_BAND[1])

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")
    season = np.asarray(SEASON_OF_MONTH)[_MONTH_OF_HOY - 1]
    block = (np.arange(HOURS) % 24) // HOUR_BLOCK_H

    resid_mask = in_band & model_below  # FULL residual set (CAMPD covers 8760)
    formed_mask = in_band & model_in_band
    control_mask = (rt < MID_BAND[0]) & (rt > 0) & model_below
    resid_bins = set(hour_bin[resid_mask].tolist())
    control_mask &= np.isin(hour_bin, list(resid_bins))  # bin-matched controls

    args = (meas, st_model, floor_ub, floor_avail, price, rt, ms["nl_hat"])
    out: dict = {
        "campd_source": f"campd-unit-level/TX_{year}.parquet",
        "n_plants": int(len(plants)),
        "nameplate_mw": round(nameplate, 1),
        "floor_base_mw": round(base_mw, 1),
        "n_band_hours_actual": int(in_band.sum()),
        "n_residual": int(resid_mask.sum()),
        "n_formed": int(formed_mask.sum()),
        "n_control": int(control_mask.sum()),
        "residual_summary": _set_summary(resid_mask, *args),
        "formed_summary": _set_summary(formed_mask, *args),
        "control_summary": _set_summary(control_mask, *args),
        "all_hours_summary": _set_summary(np.ones(HOURS, dtype=bool), *args),
        "notes": notes,
    }

    # Conditioning: residual vs control per (season, block) and per net-load
    # bin — where does the displacement live, and is it condition-specific?
    by_cell: dict[str, dict] = {}
    for s in sorted(set(season[resid_mask].tolist())):
        for k in sorted(set(block[resid_mask & (season == s)].tolist())):
            cell = (season == s) & (block == k)
            r, c = resid_mask & cell, control_mask & cell
            if not r.any():
                continue
            by_cell[f"s{s}_b{k}"] = {
                "resid_n": int(r.sum()),
                "control_n": int(c.sum()),
                "resid_model_med": _med(st_model, r),
                "resid_meas_med": _med(meas, r),
                "resid_floor_ub_med": _med(floor_ub, r),
                "control_model_med": _med(st_model, c),
                "control_meas_med": _med(meas, c),
            }
    out["by_season_block"] = by_cell

    # Season-resolved CONTROL-hour decomposition (all sub-$150 bin-matched
    # hours, not just the band): quantifies the drag's seasonal shape — in a
    # control hour where the model price sits below the ST_GAS committed
    # offer, any dispatch is either floor-forced or startup-bridged, so the
    # floor comparison plus the price median carries the attribution.
    by_season_control: dict[str, dict] = {}
    for s in range(4):
        c = control_mask & (season == s)
        if not c.any():
            continue
        econ = c & (st_model > floor_ub * 1.02)
        by_season_control[f"s{s}"] = {
            "n": int(c.sum()),
            "meas_net_med": _med(meas, c),
            "model_med": _med(st_model, c),
            "floor_ub_med": _med(floor_ub, c),
            "model_minus_meas_med": _med(st_model - meas, c),
            "share_hours_model_above_floor_ub": round(float(econ.sum() / c.sum()), 3),
            "model_price_med": _med(price, c),
        }
    out["by_season_control"] = by_season_control

    by_bin: dict[str, dict] = {}
    for b in sorted(resid_bins):
        r = resid_mask & (hour_bin == b)
        c = control_mask & (hour_bin == b)
        by_bin[str(b)] = {
            "resid_n": int(r.sum()),
            "control_n": int(c.sum()),
            "resid_model_med": _med(st_model, r),
            "resid_meas_med": _med(meas, r),
            "resid_floor_ub_med": _med(floor_ub, r),
            "control_model_med": _med(st_model, c),
            "control_meas_med": _med(meas, c),
        }
    out["by_netload_bin"] = by_bin

    # Drag-on-its-own-terms check (rule 22 — validation against the SOURCE,
    # never a re-fit): measured overnight CF vs the armed curve, per 2-GW
    # net-load bin over ALL overnight hours of the year.
    hod = np.arange(HOURS) % 24
    overnight = (hod >= OVERNIGHT_START_H) | (hod < OVERNIGHT_END_H)
    meas_cf = meas / (base_mw)  # CF on the drag-covered net basis
    nl_gw = ms["nl_hat"] / 1000.0
    curve_rows = []
    for lo in range(14, 56, 2):
        m = overnight & (nl_gw >= lo) & (nl_gw < lo + 2)
        if m.sum() < 12:
            continue
        curve_rows.append(
            {
                "nl_gw_bin": f"{lo}-{lo + 2}",
                "n": int(m.sum()),
                "meas_overnight_cf_med": round(float(np.median(meas_cf[m])), 3),
                "curve_frac_med": round(float(np.median(frac[m])), 3),
                "model_cf_med": round(float(np.median(st_model[m] / base_mw)), 3),
            }
        )
    on_rho = float(
        pd.Series(nl_gw[overnight]).corr(
            pd.Series(meas_cf[overnight]), method="spearman"
        )
    )
    out["overnight_drag_check"] = {
        "spearman_nl_vs_meas_cf": round(on_rho, 3),
        "per_nl_bin": curve_rows,
    }
    # The same comparison inside the residual hours: what the drag's own
    # driver evidence supports THERE vs what the model runs there.
    out["residual_drag_check"] = {
        "resid_meas_cf_med": _med(meas_cf * 100.0, resid_mask),
        "resid_curve_frac_med": (
            round(float(np.median(frac[resid_mask]) * 100.0), 1)
            if resid_mask.any()
            else None
        ),
        "resid_model_cf_med": _med(st_model / base_mw * 100.0, resid_mask),
        "units": "percent of drag-covered net base",
    }

    # Annual level + per-plant attribution (who actually ran).
    dead = [
        f"{int(r.Plant_Code)} ({r.Plant_Name})"
        for r in plants.itertuples(index=False)
        if float(per_plant[int(r.Plant_Code)].max()) < 5.0
    ]
    out["annual"] = {
        "meas_net_twh": round(float(meas.sum()) / 1e6, 2),
        "model_twh": round(float(st_model.sum()) / 1e6, 2),
        "meas_max_concurrent_mw": round(float(meas.max()), 1),
        "model_max_mw": round(float(st_model.max()), 1),
        "dam_avail_st_mean": round(float(np.nanmean(avail)), 4),
        "plants_never_running": dead,
    }
    out["per_plant_residual_med_mw"] = {
        f"{int(r.Plant_Code)} ({r.Plant_Name})": _med(
            per_plant[int(r.Plant_Code)], resid_mask
        )
        for r in plants.itertuples(index=False)
    }

    # Cross-check against the ERCOT-89 covered residual subset (its §8.3
    # model-side medians were computed on these hours).
    if ERCOT89_JSON.exists():
        e89 = json.loads(ERCOT89_JSON.read_text())
        hoys = [int(h["hoy"]) for h in e89.get(str(year), {}).get("residual_hours", [])]
        if hoys:
            m89 = np.zeros(HOURS, dtype=bool)
            m89[hoys] = True
            out["ercot89_covered_subset"] = {
                "n": len(hoys),
                "n_also_residual_here": int((m89 & resid_mask).sum()),
                "model_med": _med(st_model, m89),
                "meas_net_med": _med(meas, m89),
                "floor_ub_med": _med(floor_ub, m89),
            }
    return out


def main() -> None:
    """Run the measurement and write the JSON artifact + console summary."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--keeper", type=Path, default=DEFAULT_KEEPER)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    params = _drag_params(args.keeper)
    result: dict = {
        "_provenance": {
            "probe": "ercot90_stgas_shoulder_measure",
            "charter": "docs/handoffs/ercot-stgas-shoulder-2026-07.md",
            "named_by": (
                "docs/handoffs/ercot-shoulder-online-envelope-2026-07.md §8.3 "
                "(the CAMPD-based ST_GAS hourly check)"
            ),
            "role": (
                "MEASUREMENT ONLY — direct CAMPD/CEMS measurement of the "
                "non-CHP steam-gas fleet's hourly output vs the keeper's "
                "ST_GAS class dispatch in the shoulder residual/control hour "
                "sets; adjudicates which seam (drag shape / committed offer "
                "level / availability basis) owns the §8.3 displacement "
                "wedge. Not a model input, no apply seam. The drag curve is "
                "validated against its own source evidence, never re-fit "
                "(rule 22)."
            ),
            "mid_band_usd_mwh": list(MID_BAND),
            "keeper": str(args.keeper),
            "model_side": (
                "committed keeper hourly sidecars (class_hourly/system) — "
                "no keeper replay"
            ),
            "drag_params_from_keeper_run_config": params,
            "st_net_of_gross": _ST_NET_OF_GROSS,
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "season_of_month": list(SEASON_OF_MONTH),
            "hour_block_h": HOUR_BLOCK_H,
            "overnight_window_h": [OVERNIGHT_START_H, OVERNIGHT_END_H],
            "caveat_floor_reconstruction": (
                "floor_ub = frac(NL_hat) x base with NL_hat = keeper demand "
                "- VRE DISPATCH (>= the runner's potential-convention "
                "net-load) and no availability cap — an UPPER bound on the "
                "true applied floor; floor_avail refines with the class-day "
                "DAM availability. Model MW above floor_ub is therefore "
                "PROVABLY economic (not floor-forced)."
            ),
            "caveat_hourly_lambda": (
                "actual RT is hourly (mean of SCED intervals); intra-hour "
                "spikes are smoothed"
            ),
        }
    }
    for y in args.years:
        result[str(y)] = measure_year(y, args.keeper, params)
        r = result[str(y)]
        rs, cs = r["residual_summary"], r["control_summary"]
        print(
            f"\n=== {y}: resid n={r['n_residual']} formed n={r['n_formed']} "
            f"control n={r['n_control']} | fleet {r['n_plants']} plants "
            f"{r['nameplate_mw']:.0f} MW, floor base {r['floor_base_mw']:.0f} MW ==="
        )
        print(
            f"  resid : meas {rs['meas_net_med']} vs model {rs['model_med']} MW "
            f"(x{rs['model_over_meas_ratio_med']}) | floor_ub {rs['floor_ub_med']} "
            f"| model-floor_ub {rs['model_minus_floor_ub_med']} | "
            f"econ-hours share {rs['share_hours_model_above_floor_ub']}"
        )
        print(
            f"  contr : meas {cs['meas_net_med']} vs model {cs['model_med']} MW "
            f"(x{cs['model_over_meas_ratio_med']}) | floor_ub {cs['floor_ub_med']} "
            f"| model-floor_ub {cs['model_minus_floor_ub_med']}"
        )
        print(
            f"  annual: meas {r['annual']['meas_net_twh']} vs model "
            f"{r['annual']['model_twh']} TWh | meas max "
            f"{r['annual']['meas_max_concurrent_mw']:.0f} vs model max "
            f"{r['annual']['model_max_mw']:.0f} MW | overnight rho "
            f"{r['overnight_drag_check']['spearman_nl_vs_meas_cf']}"
        )
        if r["annual"]["plants_never_running"]:
            print(f"  never-running plants: {r['annual']['plants_never_running']}")

    args.out.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
