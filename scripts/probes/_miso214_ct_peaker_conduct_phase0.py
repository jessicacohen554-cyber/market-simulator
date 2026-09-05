"""miso-214 — THE MIDWEST CT_PEAKER FLEET AT ITS OWN DELIVERED COST (phase 0, zero-solve).

Executes ``results/calibration/PREREG-miso214-ct-peaker-conduct-2026-09-05.md``
(pushed BLIND at ``067a305a``) on the miso-213 keeper's committed sidecars, the
miso-210 control's committed sidecars, and the HEAD fleet chain. **No LP is
solved.**

  L-1  where the 3.3 / 2.3 / 3.6 TWh went: (a) BAND, from the LP's own
       ``class_band_hourly`` control-vs-arm delta; (b) ZONE, from the
       price-taking static screen (``class_band_hourly`` carries no zone and
       neither bundle ships ``unit_hourly``); (c) DIURNAL, from the LP delta.
  L-2  THE DISCRIMINATOR. Every missed plant-hour — a model ``CT_PEAKER``
       plant CAMPD shows running that the static screen has out of merit at
       the keeper's own P1 zone price — split MWh-weighted on the plant's OWN
       delivered cost (its own EIA-923 monthly print x its own CAMPD-measured
       burn heat rate + VOM + emission adders) against two prices:
         A price-reachable   cost <= ACTUAL RT and cost > MODEL P1
         B market-OOM        cost >  ACTUAL RT           <- the K-a statistic
         C model-internal    cost <= MODEL P1 and the model is still idle
       plus the CAMPD run-block anatomy of the B hours and the K-b offer-level
       flip test (the miso-134 full measured swap, econ bands only).
  L-3  the 2023 question: is the CT under-dispatch a summer tail or all-hours?
       Month and hour-of-day mass of the CAMPD-minus-model gap, all years.
  L-4  the rule-19 census: every mechanism already flooring or bridging MISO
       ``CT_PEAKER`` — the bundle's own D-2 / D-4 rows, the C8 forced share,
       the armed ``RELIABILITY_FLOOR_REGISTRY`` limbs, the class's ``min_gen``
       mechanism attribution, and the offer-band construction.

INSTRUMENT LIMITS, DISCLOSED (PREREG §2): neither bundle ships ``unit_hourly/``
or ``dispatch/``, so plant- and zone-grain model merit is a PRICE-TAKING STATIC
SCREEN on ``mc_base`` (no P1 startup adder) against the keeper's own committed
P1 zone prices — a BOUND, not the LP; N-1 reports the bound beside the LP's own
class total. CAMPD facility-level extracts are absent for 12 of the 14 MISO
states here, so every CAMPD read uses ``prefer_unit_level=True``. CAMPD gross MW
is compared to the model's net tranches without adjustment. The plant's own 923
print is a MONTHLY average applied to an HOURLY decision (the
average-vs-marginal convention, miso-212 §8, OWNER-COURT and untouched).

Usage::

    PYTHONPATH=src .venv/bin/python scripts/probes/_miso214_ct_peaker_conduct_phase0.py

Record: ``results/calibration/_miso214_ct_peaker_conduct.json``.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso207_bound_the_shoulder as m207  # noqa: E402
import _miso208_find_the_supply as m208  # noqa: E402
import _miso211_rdt_binding_state as _m211  # noqa: E402  (re-points to miso-210 at import)

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso212_south_gas_cost_basis import hh_daily_on_clock  # noqa: E402
from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet.campd_bins import ct_intermediate_plants  # noqa: E402

# T-1: re-point EVERY module global to the miso-213 keeper, AFTER the last
# import, because `_miso211` (pulled in transitively by `_miso212`) re-points
# `_m134.BUNDLE` to ITS OWN keeper, `miso210_clock_B`, at module scope. Doing
# this before the imports silently ran the whole probe on the CONTROL config —
# caught by the assert below, which is why it is here and not there.
KEEPER = REPO / "results/calibration/miso213_layering_B"
CONTROL = REPO / "results/calibration/miso210_clock_B"
_m134.BUNDLE = KEEPER
m207.KEEPER = KEEPER
m208.KEEPER = KEEPER
_m211.KEEPER = KEEPER
assert _m134.BUNDLE == KEEPER and m207.KEEPER == KEEPER and m208.KEEPER == KEEPER
assert _m134.keeper_config().miso_zonal_gas_basis_skip_923_priced, (
    "T-1 re-point failed: the probe would run on the control config"
)

OUT = REPO / "results/calibration/_miso214_ct_peaker_conduct.json"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
# rule 22 [R-HOLDOUT]: MISO holds no marker, so 2023-2025 are the ONLY years
# this probe may touch. The env override exists for a single-year smoke test and
# is hard-gated to the training window.
YEARS = tuple(
    int(v) for v in os.environ.get("MISO214_YEARS", "2023,2024,2025").split(",")
)
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
KLASS = "CT_PEAKER"
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MO = np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[:HOURS]
HOD = np.arange(HOURS) % 24
# The armed MISO CT_PEAKER limbs all carry start_hour=15 / end_hour=21, and
# interchange/core.py applies them as ``hod >= sh & hod <= eh`` on
# ``arange(hours) % 24`` — so the window is HOD 15..21 inclusive. Derived from
# the registry rather than hardcoded, and asserted below.
_CT_LIMBS = [r for r in RELIABILITY_FLOOR_REGISTRY["MISO"] if r.plant_class == "CT_PEAKER" and r.enabled]
_SH = {int(r.start_hour) for r in _CT_LIMBS}
_EH = {int(r.end_hour) for r in _CT_LIMBS}
assert len(_SH) == 1 and len(_EH) == 1, "MISO CT_PEAKER limbs disagree on window"
FLOOR_SH, FLOOR_EH = _SH.pop(), _EH.pop()
FLOOR_WINDOW = (HOD >= FLOOR_SH) & (HOD <= FLOOR_EH)
SUMMER = np.isin(MO, (6, 7, 8))

# miso-204 TRAP-4 basis, verbatim: MISO's eight trading hubs onto six model
# zones. MISO-Plains has no hub of its own, so MINN.HUB carries West AND Plains.
HUB_TO_ZONES = {
    "MINN.HUB": ("MISO-West", "MISO-Plains"),
    "ILLINOIS.HUB": ("MISO-Illinois",),
    "INDIANA.HUB": ("MISO-Indiana",),
    "MICHIGAN.HUB": ("MISO-East",),
    "ARKANSAS.HUB": ("MISO-South",),
    "LOUISIANA.HUB": ("MISO-South",),
    "MS.HUB": ("MISO-South",),
    "TEXAS.HUB": ("MISO-South",),
}
MIDWEST = ("MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East")
# MISO's three MARKET REGIONS (the grain data/raw/MISO-AS/asm_rt_cleared_mw_*
# publishes) by state, on the published Local Resource Zone map: North = LRZ 1,
# Central = LRZ 2-7, South = LRZ 8-10. Iowa spans LRZ 1 and LRZ 3 and is
# assigned to Central here — declared, not tuned.
MISO_REGION_BY_STATE = {
    "MN": "North", "ND": "North", "SD": "North",
    "WI": "Central", "MI": "Central", "IA": "Central", "IL": "Central",
    "MO": "Central", "IN": "Central", "KY": "Central",
    "AR": "South", "LA": "South", "TX": "South", "MS": "South",
}
ASM_DIR = REPO / "data/raw/MISO-AS"
IIE = ("MISO-Illinois", "MISO-Indiana", "MISO-East")
WP = ("MISO-West", "MISO-Plains")
CT_UNIT_PREFIX = "Combustion turbine"  # CAMPD unitType; excludes "Combined cycle"
IO_MIN_HOURS = 50        # a unit needs this many operating hours for an I-O fit
IO_MIN_OPTIME = 0.98     # ...all of them STEADY-STATE (no start/stop part-hours)
IO_MIN_RANGE_FRAC = 0.10  # ...and this much load range, or its slope is unusable
# Class-measured incremental/average ratio, the FALLBACK for a plant whose
# units have no usable I-O fit: data/raw/reference/miso_campd_marginal_hr_
# summary.csv, CT_PEAKER marg_econ_low_p50 0.687 / avg_econ_low_p50 1.002
# (n = 249 units, the same frozen derivation the offer bands are built on).
CT_MARG_OVER_AVG = 0.687 / 1.002
EPS = 1e-9
# PREREG §4 kill thresholds, fixed before any number below.
K_A_BAR = 0.40  # B share of missed MWh, in >= 2 of 3 years
K_B_BAR = 0.60  # share of bucket A that flips in-merit when the margin is removed
K_E_BAR = 0.60  # CEMS-covered share of model CT_PEAKER capacity


def _band(unit_id: str) -> str:
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", str(unit_id))
    suf = m.group(2) if m else ""
    for k in ("mustrun", "sync", "committed", "econ", "peak"):
        if suf.startswith(k):
            return k
    return suf or "?"


def _r(x, n=4):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(v) else round(v, n)


def keeper_price(bundle: Path, year: int, zones: list[str]) -> np.ndarray:
    """(Z, T) P1 zone price from a bundle's own committed ``system_`` sidecar."""
    sysf = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"] if "pass" in sysf else sysf
    pv = sysf.pivot_table(index="hour", columns="zone", values="price")
    return pv.reindex(columns=zones).to_numpy().T


def class_hourly(bundle: Path, year: int, klass: str) -> np.ndarray:
    ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == klass)]
    out = np.zeros(HOURS)
    out[ch["hour"].to_numpy(int)] = ch["mw"].to_numpy(float)
    return out


def class_band_hourly(bundle: Path, year: int, klass: str) -> dict[str, np.ndarray]:
    ch = pd.read_parquet(bundle / f"hourly/class_band_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == klass)]
    out: dict[str, np.ndarray] = {}
    for band, sub in ch.groupby("band", observed=True):
        fam = str(band)
        fam = "econ" if fam.startswith("econ") else fam
        arr = out.setdefault(fam, np.zeros(HOURS))
        np.add.at(arr, sub["hour"].to_numpy(int), sub["mw"].to_numpy(float))
    return out


def actual_lmp_by_zone(year: int, zones: list[str], col: str = "rt") -> np.ndarray:
    """(Z, T) measured LMP per model zone (South = mean of its four hubs).

    ``col`` selects the settlement: ``rt`` (the headline basis) or ``da`` — a
    day-ahead-committed unit is paid the DA price for its scheduled energy, so
    the DA leg is the robustness check on any "out of merit" reading.
    """
    zon = pd.read_parquet(ZONAL)
    zon = zon[zon["year"] == year]
    per_zone: dict[str, list[np.ndarray]] = {z: [] for z in zones}
    for hub, zs in HUB_TO_ZONES.items():
        s = zon[zon["hub"] == hub].sort_values("hour")
        arr = np.full(HOURS, np.nan)
        idx = s["hour"].to_numpy(int)
        keep = idx < HOURS
        arr[idx[keep]] = s[col].to_numpy(float)[keep]
        for z in zs:
            if z in per_zone:
                per_zone[z].append(arr)
    out = np.full((len(zones), HOURS), np.nan)
    for i, z in enumerate(zones):
        if per_zone[z]:
            out[i] = np.nanmean(np.vstack(per_zone[z]), axis=0)
    return out


def asm_cleared_by_region(year: int) -> dict[str, np.ndarray]:
    """(T,) hourly cleared reserve MW (reg+spin+supp+str) per MISO market region.

    ``data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet`` — Hour-Ending EST
    year-round (MISO market reports never observe DST). Read onto the model's
    fixed 8760 clock with the same no-shift convention used for CAMPD above,
    so the two measured series share one clock; disclosed, not corrected.
    """
    f = ASM_DIR / f"asm_rt_cleared_mw_{year}.parquet"
    if not f.exists():
        return {}
    df = pd.read_parquet(f)
    d = pd.to_datetime(df["date"])
    hoy = campd._hour_index_8760(d.dt.month, d.dt.day, df["hour_end_est"].astype(int) - 1)
    df = df.assign(hoy=hoy)
    df = df[(df["hoy"] >= 0) & (d.dt.year == year)]
    out: dict[str, np.ndarray] = {}
    for reg, sub in df.groupby("region"):
        arr = np.zeros(HOURS)
        g = sub.groupby("hoy")["cleared_mw"].sum()
        arr[g.index.to_numpy(int)] = g.to_numpy(float)
        out[str(reg)] = arr
    return out


def campd_ct(year: int, plant_ids: set[int]) -> pd.DataFrame:
    """CAMPD **unit-level** hours for ``plant_ids``, SIMPLE-CYCLE CT units only.

    Read straight from ``data/raw/campd-unit-level/{ST}_{YEAR}.parquet`` — not
    through ``campd.load_campd_hourly`` — for one reason: the model-facing
    loader drops ``opTime``, and the input-output fit below needs the
    STEADY-STATE hours the frozen ``scripts/data/derive_campd_marginal_hr.py``
    also selects on (a peaker's start/stop part-hours carry a full start's fuel
    against a fraction of an hour's MWh and would bias the slope upward). The
    facility-level extracts are absent for 12 of the 14 MISO states in this
    container, so the unit-level tree is the only complete source anyway.
    Clock: CAMPD local standard time is read onto the model's fixed non-leap
    8760 clock with no shift — the established convention of every prior MISO
    CAMPD probe (miso-208/209/212), disclosed rather than corrected.
    """
    cols = ["facilityId", "unitId", "stateCode", "date", "hour", "opTime",
            "grossLoad", "heatInput", "unitType"]
    frames = []
    for st in campd.states_for_iso("MISO"):
        f = REPO / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not f.exists():
            continue
        df = pd.read_parquet(f, columns=cols)
        df = df[df["facilityId"].astype("int64").isin(plant_ids)]
        if df.empty:
            continue
        df = df[df["unitType"].astype(str).str.startswith(CT_UNIT_PREFIX)]
        if df.empty:
            continue
        d = pd.to_datetime(df["date"])
        hoy = campd._hour_index_8760(d.dt.month, d.dt.day, df["hour"].astype(int))
        df = df.assign(hour_of_year=hoy)
        df = df[df["hour_of_year"] >= 0]
        frames.append(
            pd.DataFrame({
                "plant_id": df["facilityId"].astype("int64").to_numpy(),
                "unit_id": df["unitId"].astype(str).to_numpy(),
                "state": df["stateCode"].astype(str).to_numpy(),
                "hour_of_year": df["hour_of_year"].astype("int32").to_numpy(),
                "gross_mw": pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0).to_numpy(),
                "heat_mmbtu": pd.to_numeric(df["heatInput"], errors="coerce").fillna(0.0).to_numpy(),
                "op_time": pd.to_numeric(df["opTime"], errors="coerce").fillna(0.0).to_numpy(),
            })
        )
    if not frames:
        return pd.DataFrame(
            columns=["plant_id", "unit_id", "hour_of_year", "gross_mw",
                     "heat_mmbtu", "op_time"]
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(
        ["plant_id", "unit_id", "hour_of_year"], observed=True, as_index=False
    ).agg({"gross_mw": "sum", "heat_mmbtu": "sum", "op_time": "max",
           "state": "first"})


def io_fit(mw: np.ndarray, heat: np.ndarray, optime: np.ndarray) -> tuple[float, float, int]:
    """Least-squares input-output line for ONE unit: ``heat = a + b x mw``.

    ``b`` is the unit's measured **incremental** heat rate (MMBtu/MWh) and
    ``a`` its no-load fuel (MMBtu/h) — the standard CEMS input-output
    construction, the same physical quantity the frozen
    ``derive_campd_marginal_hr.py`` reports per class as ``marg_*``. Fit over
    the unit's STEADY-STATE operating hours only (``opTime >= 0.98``, load
    inside its own p3-p97 envelope), because a peaker's start/stop part-hours
    carry a start's fuel against a fraction of an hour's MWh. Returns
    ``(a, b, n)``; ``b`` is NaN when the unit lacks a usable load range.
    """
    on = (mw > 0.0) & (heat > 0.0) & (optime >= IO_MIN_OPTIME)
    n = int(on.sum())
    if n < IO_MIN_HOURS:
        return float("nan"), float("nan"), n
    x, yv = mw[on], heat[on]
    lo, hi = np.percentile(x, [3.0, 97.0])
    keep = (x >= lo) & (x <= hi)
    if keep.sum() < IO_MIN_HOURS:
        return float("nan"), float("nan"), n
    x, yv = x[keep], yv[keep]
    if float(x.max() - x.min()) < IO_MIN_RANGE_FRAC * float(max(x.max(), EPS)):
        return float("nan"), float("nan"), n
    b, a = np.polyfit(x, yv, 1)
    if not np.isfinite(b) or b <= 0.0:
        return float("nan"), float("nan"), n
    return float(a), float(b), n


def _run_blocks(on: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per hour: length of the contiguous ``on`` block it belongs to, and its
    position (0 = first hour, 1 = middle, 2 = last, 3 = a one-hour block)."""
    n = on.size
    length = np.zeros(n, dtype=np.int32)
    pos = np.full(n, -1, dtype=np.int8)
    if not on.any():
        return length, pos
    d = np.diff(np.concatenate(([0], on.view(np.int8), [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)  # exclusive
    for s, e in zip(starts, ends):
        length[s:e] = e - s
        if e - s == 1:
            pos[s] = 3
        else:
            pos[s:e] = 1
            pos[s] = 0
            pos[e - 1] = 2
    return length, pos


def _implied_hr(mc: np.ndarray, fp: np.ndarray, adders: np.ndarray, cap: np.ndarray) -> float:
    """Capacity-weighted implied heat rate ``(mc - adders) / F`` (miso-212 §6)."""
    hr = (mc - adders[:, None]) / np.maximum(fp, EPS)
    per_row = np.nanmean(hr, axis=1)
    ok = np.isfinite(per_row) & (cap > 0)
    return float((per_row[ok] * cap[ok]).sum() / cap[ok].sum()) if ok.any() else float("nan")


def _capw_hr(hr_annual, plant_list, p_row, cap_by_plant) -> float:
    """Capacity-weighted annual CAMPD burn heat rate over plants that ran."""
    num = den = 0.0
    for p in plant_list:
        h = hr_annual[p_row[p]]
        c = cap_by_plant.get(int(p), 0.0)
        if np.isfinite(h) and c > 0:
            num += h * c
            den += c
    return num / den if den > 0 else float("nan")


def _wshare(mask: np.ndarray, w: np.ndarray) -> float:
    tot = float(w.sum())
    return float(w[mask].sum() / tot) if tot > EPS else float("nan")


def main() -> None:  # noqa: PLR0912, PLR0915
    cfg_arm = keeper_config()
    cfg_ctl = dataclasses.replace(cfg_arm, miso_zonal_gas_basis_skip_923_priced=False)
    anchor = float(cfg_arm.gas_offer_margin_anchor)

    # ---- footing: the two bundles' recorded configs differ ONLY in the field
    a_raw = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    c_raw = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    shared = set(a_raw) & set(c_raw)
    diffs = sorted(k for k in shared if a_raw[k] != c_raw[k])

    rep: dict = {
        "charter": "miso-214 phase 0 — the Midwest CT_PEAKER fleet at its own delivered cost; zero-solve.",
        "prereg": "results/calibration/PREREG-miso214-ct-peaker-conduct-2026-09-05.md @ 067a305a",
        "keeper": "2026-09-05-miso-213-layering",
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "control_bundle": str(CONTROL.relative_to(REPO)),
        "anchor_usd_mmbtu": anchor,
        "instrument": {
            "model_plant_grain": "PRICE-TAKING STATIC SCREEN on mc_base (no P1 startup adder) at the keeper's own committed P1 zone price — neither bundle ships unit_hourly/ or dispatch/. A BOUND, not the LP; N-1 reports it beside the LP's own class_hourly total.",
            "control_leg": "miso210_clock_B committed class_band_hourly / class_hourly / system (the pre-repair keeper); the class x band x hour delta is LP output, not reconstructed.",
            "campd": "load_campd_hourly(prefer_unit_level=True), SIMPLE-CYCLE units only (unitType startswith 'Combustion turbine'); facility-level extracts absent for 12 of 14 MISO states here.",
            "own_cost": "plant's own resolved delivered fuel price (the 923 print path, cap-weighted over its CT tranches, MONTHLY) x its own CAMPD burn heat rate (sum heat / sum gross, same month) + cap-weighted VOM + nox/so2 adders.",
            "actual_price": "measured RT LMP, miso-204 TRAP-4 HUB_TO_ZONES (South = mean of ARKANSAS/LOUISIANA/MS/TEXAS; MINN.HUB carries West AND Plains).",
            "gross_vs_net": "CAMPD GROSS MW against the model's NET tranches; reported, never adjusted.",
            "monthly_923": "a MONTHLY average print applied to an HOURLY decision — the average-vs-marginal convention (miso-212 §8) is OWNER-COURT and untouched; it biases 'out-of-merit' upward.",
        },
        "config_footing": {
            "fields_in_both": len(shared),
            "diffs_arm_vs_control": {k: [c_raw[k], a_raw[k]] for k in diffs},
            "arm_only_fields": sorted(set(a_raw) - set(c_raw)),
            "control_only_fields": sorted(set(c_raw) - set(a_raw)),
        },
        "kill_bars": {"K_a_B_share": K_A_BAR, "K_b_A_flip": K_B_BAR, "K_e_cems_cov": K_E_BAR},
        "years": {},
    }

    zones: list[str] = []
    for year in YEARS:
        y: dict = {}
        fleet_a = build_year(cfg_arm, year)
        raw_fleet, fleet, arrays, fp_a, mc_a, zones = fleet_a
        _fl_c = build_year(cfg_ctl, year)
        mc_c = _fl_c[4]
        assert mc_c.shape == mc_a.shape, "control/arm fleet rows disagree"
        del _fl_c
        gc.collect()
        z_of = {n: i for i, n in enumerate(zones)}

        klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
        uids = np.array([str(g.unit_id) for g in fleet])
        bands = np.array([_band(u) for u in uids])
        pcode = np.asarray(arrays.plant_code)
        zi = np.asarray(arrays.zone_idx)
        pmax = np.asarray(arrays.pmax, float)
        avail = np.asarray(arrays.availability, float)
        vom = np.asarray(arrays.vom, float)
        markup = np.array(
            [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet]
        )
        nox_r = np.asarray(arrays.nox_rate, float)
        so2_r = np.asarray(arrays.so2_rate, float)

        ct = np.flatnonzero(klass == KLASS)
        price = keeper_price(KEEPER, year, zones)                    # (Z, T)
        zp = price[zi[ct], :]                                        # (n, T)
        availcap = pmax[ct][:, None] * avail[ct]                     # (n, T)

        merit_a = mc_a[ct] <= zp
        merit_c = mc_c[ct] <= zp
        mw_a = availcap * merit_a
        mw_c = availcap * merit_c

        # ---------------- N-1 footing --------------------------------------
        lp_arm = class_hourly(KEEPER, year, KLASS)
        lp_ctl = class_hourly(CONTROL, year, KLASS)
        ct_plants = {int(p) for p in np.unique(pcode[ct]) if int(p) > 0}
        cap_by_plant = {
            int(k): float(v)
            for k, v in pd.Series(pmax[ct], index=pcode[ct])
            .groupby(level=0)
            .sum()
            .items()
        }
        cm = campd_ct(year, ct_plants)
        seen = {int(p) for p in cm["plant_id"].unique()} if not cm.empty else set()
        cov_cap = sum(v for k, v in cap_by_plant.items() if int(k) in seen)
        tot_cap = sum(cap_by_plant.values())
        y["N1_footing"] = {
            "n_ct_tranches": int(ct.size),
            "n_ct_plants_model": len(ct_plants),
            "n_ct_plants_cems": len(seen),
            "ct_capacity_mw_model": _r(tot_cap, 1),
            "ct_capacity_mw_cems_covered": _r(cov_cap, 1),
            "cems_covered_capacity_share": _r(cov_cap / tot_cap if tot_cap else np.nan),
            "lp_class_twh_arm": _r(lp_arm.sum() / 1e6, 3),
            "lp_class_twh_control": _r(lp_ctl.sum() / 1e6, 3),
            "screen_class_twh_arm": _r(mw_a.sum() / 1e6, 3),
            "screen_class_twh_control": _r(mw_c.sum() / 1e6, 3),
            "screen_over_lp_arm": _r(mw_a.sum() / lp_arm.sum() if lp_arm.sum() else np.nan),
            "campd_ct_twh_gross": _r(
                (cm["gross_mw"].sum() / 1e6) if not cm.empty else np.nan, 3
            ),
        }

        # ---------------- L-1 (a) band, (c) diurnal — LP output -------------
        cb_a = class_band_hourly(KEEPER, year, KLASS)
        cb_c = class_band_hourly(CONTROL, year, KLASS)
        fams = sorted(set(cb_a) | set(cb_c))
        band_rows = {}
        for f in fams:
            a = cb_a.get(f, np.zeros(HOURS))
            c = cb_c.get(f, np.zeros(HOURS))
            band_rows[f] = {
                "control_twh": _r(c.sum() / 1e6, 3),
                "arm_twh": _r(a.sum() / 1e6, 3),
                "delta_twh": _r((a - c).sum() / 1e6, 3),
            }
        d_tot = sum(
            (cb_a.get(f, np.zeros(HOURS)) - cb_c.get(f, np.zeros(HOURS))).sum()
            for f in fams
        )
        d_econ = (cb_a.get("econ", np.zeros(HOURS)) - cb_c.get("econ", np.zeros(HOURS))).sum()
        d_hr = lp_arm - lp_ctl
        loss = np.maximum(0.0, -d_hr)  # MWh the class LOST, per hour
        y["L1_band"] = {
            "bands": band_rows,
            "class_delta_twh": _r(d_tot / 1e6, 3),
            "econ_share_of_delta": _r(d_econ / d_tot if abs(d_tot) > EPS else np.nan),
            "P1a_bar": 0.70,
        }
        y["L1_diurnal"] = {
            "lost_mwh": _r(loss.sum(), 0),
            "share_outside_h15_21": _r(_wshare(~FLOOR_WINDOW, loss)),
            "share_in_h15_21": _r(_wshare(FLOOR_WINDOW, loss)),
            "share_summer_JJA": _r(_wshare(SUMMER, loss)),
            "by_hod_mwh": [_r(loss[HOD == h].sum(), 0) for h in range(24)],
            "by_month_mwh": [_r(loss[MO == m].sum(), 0) for m in range(1, 13)],
            "P1c_bar": 0.60,
        }

        # ---------------- L-1 (b) zone — static screen ----------------------
        dz = {}
        d_screen = (mw_c - mw_a).sum(axis=1)  # MWh the screen loses, per tranche
        for zn, i in z_of.items():
            sel = zi[ct] == i
            dz[zn] = _r(float(d_screen[sel].sum()) / 1e6, 4)
        pos = {k: max(0.0, v or 0.0) for k, v in dz.items()}
        tot_pos = sum(pos.values()) or np.nan
        y["L1_zone_screen"] = {
            "delta_twh_by_zone_screen_loss": dz,
            "loss_share_IIE": _r(sum(pos[z] for z in IIE) / tot_pos),
            "loss_share_WestPlains": _r(sum(pos[z] for z in WP) / tot_pos),
            "loss_share_South": _r(pos.get("MISO-South", 0.0) / tot_pos),
            "P1b_bar": {2023: "IIE>=0.60", 2024: "IIE>=0.50", 2025: "WP>=0.50"}[year],
        }

        # ---------------- L-2 the discriminator -----------------------------
        # model plant-hour MW from the screen; a plant is "idle" at 0.
        plant_list = sorted(ct_plants)
        p_row = {p: i for i, p in enumerate(plant_list)}
        rows_of: dict[int, list[int]] = {p: [] for p in plant_list}
        for j, gi in enumerate(ct):
            pc = int(pcode[gi])
            if pc in rows_of:
                rows_of[pc].append(j)
        model_mw = np.zeros((len(plant_list), HOURS))
        for p, js in rows_of.items():
            if js:
                model_mw[p_row[p]] = mw_a[js].sum(axis=0)
        # margin-free model merit (K-b): the miso-134 full measured swap,
        # ECON bands only (the committed band is measured-grounded at 1.025 and
        # the peak band's 4.0 is the deliberate MISO-cap scarcity wall).
        econ_sel = np.char.startswith(bands[ct], "econ")
        mc_nm = mc_a[ct].copy()
        mc_nm[econ_sel] -= (markup[ct][econ_sel] * anchor)[:, None]
        mw_nm = availcap * (mc_nm <= zp)
        model_mw_nm = np.zeros_like(model_mw)
        for p, js in rows_of.items():
            if js:
                model_mw_nm[p_row[p]] = mw_nm[js].sum(axis=0)

        actual = actual_lmp_by_zone(year, zones, "rt")                # (Z, T)
        actual_da = actual_lmp_by_zone(year, zones, "da")             # (Z, T)
        pz: dict[int, int] = {}
        for gi in ct:
            pz.setdefault(int(pcode[gi]), int(zi[gi]))
        # The plant's measured PHYSICAL (incremental) burn as the model itself
        # holds it: under gas_offer_net_revenue_margin the tranche's
        # arrays.heat_rate is the FULL offered HR and offer_markup_hr is the
        # residual-margin part of it, so the physical leg — the plant's own
        # measured base HR times the frozen class marginal multiplier
        # (0.687 / 0.691, miso_campd_marginal_hr_summary.csv, n = 249) — is
        # heat_rate - offer_markup_hr. This is the algebra apply_gas_offer_margin
        # documents: mc = phys x HR_base x F + markup_hr x anchor.
        hr_all = np.asarray(arrays.heat_rate)
        hr_phys = np.full(len(plant_list), np.nan)
        for p, js in rows_of.items():
            e = [j for j in js if bands[ct][j].startswith("econ")]
            if e:
                w = pmax[ct][e]
                hr_phys[p_row[p]] = float(
                    ((hr_all[ct][e] - markup[ct][e]) * w).sum() / w.sum()
                )
        capw = {}
        for p, js in rows_of.items():
            w = pmax[ct][js]
            capw[p] = {
                "vom": float((vom[ct][js] * w).sum() / w.sum()) if w.sum() else 0.0,
                "nox": float((nox_r[ct][js] * w).sum() / w.sum()) if w.sum() else 0.0,
                "so2": float((so2_r[ct][js] * w).sum() / w.sum()) if w.sum() else 0.0,
            }
        # plant x month delivered fuel price (cap-weighted over its tranches)
        fmonth = np.zeros((len(plant_list), 12))
        for p, js in rows_of.items():
            if not js:
                continue
            w = pmax[ct][js]
            f = (fp_a[ct][js] * w[:, None]).sum(axis=0) / w.sum()
            for m in range(1, 13):
                fmonth[p_row[p], m - 1] = float(f[MO == m].mean())

        if cm.empty:
            y["L2"] = {"skipped": "no CAMPD CT rows for the model CT_PEAKER plant set"}
            rep["years"][str(year)] = y
            continue

        # ---- unit-grain CAMPD arrays, and the per-unit input-output fit ----
        units = list(
            cm[["plant_id", "unit_id"]].drop_duplicates().itertuples(index=False, name=None)
        )
        u_row = {k: i for i, k in enumerate(units)}
        u_mw = np.zeros((len(units), HOURS))
        u_heat = np.zeros((len(units), HOURS))
        u_op = np.zeros((len(units), HOURS))
        ui = np.array([u_row[(int(a_), str(b_))] for a_, b_ in zip(cm["plant_id"], cm["unit_id"])])
        hh = cm["hour_of_year"].to_numpy(int)
        u_mw[ui, hh] = cm["gross_mw"].to_numpy(float)
        u_heat[ui, hh] = cm["heat_mmbtu"].to_numpy(float)
        u_op[ui, hh] = cm["op_time"].to_numpy(float)

        g_mw = np.zeros((len(plant_list), HOURS))
        g_heat = np.zeros((len(plant_list), HOURS))
        for (pid, _uid), i in u_row.items():
            r = p_row.get(int(pid))
            if r is not None:
                g_mw[r] += u_mw[i]
                g_heat[r] += u_heat[i]

        # per-unit incremental HR (slope) and no-load fuel (intercept)
        u_a = np.full(len(units), np.nan)
        u_b = np.full(len(units), np.nan)
        u_cap = np.zeros(len(units))
        for (pid, _uid), i in u_row.items():
            a_, b_, _n = io_fit(u_mw[i], u_heat[i], u_op[i])
            u_a[i], u_b[i] = a_, b_
            u_cap[i] = float(u_mw[i].max())
        hr_marg = np.full(len(plant_list), np.nan)   # MMBtu/MWh, cap-weighted
        noload = np.zeros(len(plant_list))           # MMBtu/h at full commitment
        fit_cov = np.zeros(len(plant_list))          # capacity share with a fit
        for (pid, _uid), i in u_row.items():
            r = p_row.get(int(pid))
            if r is None:
                continue
            noload[r] += 0.0 if not np.isfinite(u_a[i]) else max(0.0, u_a[i])
        for r, p in enumerate(plant_list):
            idx = [i for (pid, _u), i in u_row.items() if int(pid) == p]
            if not idx:
                continue
            ok = [i for i in idx if np.isfinite(u_b[i]) and u_cap[i] > 0]
            capt = sum(u_cap[i] for i in idx)
            fit_cov[r] = (sum(u_cap[i] for i in ok) / capt) if capt > 0 else 0.0
            if ok:
                hr_marg[r] = sum(u_b[i] * u_cap[i] for i in ok) / sum(u_cap[i] for i in ok)

        # per-plant-month AVERAGE burn heat rate (sum heat / sum gross)
        hr_avg = np.full((len(plant_list), 12), np.nan)
        for m in range(1, 13):
            sel = MO == m
            gsum = g_mw[:, sel].sum(axis=1)
            hsum = g_heat[:, sel].sum(axis=1)
            ok = gsum > 1.0
            hr_avg[ok, m - 1] = hsum[ok] / gsum[ok]
        hr_avg_ann = np.where(
            g_mw.sum(axis=1) > 1.0,
            g_heat.sum(axis=1) / np.maximum(g_mw.sum(axis=1), EPS),
            np.nan,
        )
        for m in range(12):  # a month a plant never ran keeps its annual average
            miss = ~np.isfinite(hr_avg[:, m])
            hr_avg[miss, m] = hr_avg_ann[miss]
        # a plant with no usable I-O fit falls back to the class-measured
        # marginal/average ratio applied to its OWN average burn (measured, not
        # tuned): miso_campd_marginal_hr_summary.csv CT_PEAKER
        # marg_econ_low 0.687 / avg_econ_low 1.002.
        miss_b = ~np.isfinite(hr_marg)
        hr_marg[miss_b] = hr_avg_ann[miss_b] * CT_MARG_OVER_AVG

        own_avg = np.full((len(plant_list), HOURS), np.nan)
        own_inc = np.full((len(plant_list), HOURS), np.nan)
        own_fit = np.full((len(plant_list), HOURS), np.nan)
        mprice = np.zeros((len(plant_list), HOURS))
        aprice = np.full((len(plant_list), HOURS), np.nan)
        dprice = np.full((len(plant_list), HOURS), np.nan)
        for p in plant_list:
            i = p_row[p]
            zidx = pz.get(p, 0)
            mprice[i] = price[zidx]
            aprice[i] = actual[zidx]
            dprice[i] = actual_da[zidx]
            f_h = fmonth[i][MO - 1]
            c = capw[p]
            adders = (
                c["vom"]
                + c["nox"] * float(cfg_arm.nox_price)
                + c["so2"] * float(cfg_arm.so2_price)
            )
            own_avg[i] = f_h * hr_avg[i][MO - 1] + adders
            own_inc[i] = f_h * hr_phys[i] + adders
            own_fit[i] = f_h * hr_marg[i] + adders

        running = g_mw > 0.0
        missed = (
            running & (model_mw <= EPS) & np.isfinite(own_avg) & np.isfinite(aprice)
        )
        w = g_mw * missed
        tot = float(w.sum())
        # PREREG's literal buckets, on the plant's own ALL-IN (average burn) cost
        b_raw = own_avg > aprice
        a_raw = (own_avg <= aprice) & (own_avg > mprice)
        c_raw_ = own_avg <= mprice
        ex_c = c_raw_
        ex_a = (~ex_c) & (own_avg <= aprice)
        ex_b = (~ex_c) & (~ex_a)
        # the INSTRUMENT SPLIT of B (disclosed correction, finding §"instrument"):
        #   B1 out of merit even on the plant's own measured INCREMENTAL burn
        #   B2 above incremental, below all-in — the commitment / make-whole band
        b1 = b_raw & (own_inc > aprice)
        b2 = b_raw & (own_inc <= aprice)
        b1_fit = b_raw & (own_fit > aprice)  # the independent I-O sensitivity

        # ---- INSTRUMENT SENSITIVITY (PREREG §2 / §5.2): the plant's own 923
        # print is an ALL-IN delivered cost — commodity plus firm-transport
        # demand charges, which are FIXED and do not enter an hourly offer.
        # Re-price the same buckets on the Henry Hub daily spot (the pure
        # commodity floor, the miso-213 L-2 comparator) so the size of that
        # convention's contribution to B is visible. The convention itself is
        # OWNER-COURT (miso-212 §8) and is NOT adjudicated here.
        hh = hh_daily_on_clock(year)                                  # (T,)
        own_avg_hh = np.full_like(own_avg, np.nan)
        own_inc_hh = np.full_like(own_inc, np.nan)
        for p in plant_list:
            i = p_row[p]
            c = capw[p]
            adders = (
                c["vom"]
                + c["nox"] * float(cfg_arm.nox_price)
                + c["so2"] * float(cfg_arm.so2_price)
            )
            own_avg_hh[i] = hh * hr_avg[i][MO - 1] + adders
            own_inc_hh[i] = hh * hr_phys[i] + adders
        print_excess = np.full(len(plant_list), np.nan)
        for p in plant_list:
            i = p_row[p]
            print_excess[i] = float(np.mean(fmonth[i][MO - 1] - hh))

        margin_act = (aprice - own_avg)[missed]
        margin_act_i = (aprice - own_inc)[missed]
        margin_mod = (mprice - own_avg)[missed]
        wm = g_mw[missed]

        def _wq(x, ww, qs=(0.10, 0.50, 0.90)):
            ok = np.isfinite(x) & (ww > 0)
            if not ok.any():
                return {}
            xx, w2 = x[ok], ww[ok]
            o = np.argsort(xx)
            xx, w2 = xx[o], w2[o]
            cw = np.cumsum(w2) / w2.sum()
            return {f"p{int(q * 100)}": _r(xx[np.searchsorted(cw, q)], 2) for q in qs}

        capsum = sum(cap_by_plant.get(int(p), 0.0) for p in plant_list)
        y["L2"] = {
            "missed_plant_hours": int(missed.sum()),
            "missed_mwh_campd_gross": _r(tot, 0),
            "missed_share_of_campd_ct_mwh": _r(tot / max(g_mw.sum(), EPS)),
            "actual_price_nan_hours": int((~np.isfinite(actual)).sum()),
            "B_share_literal": _r(_wshare(b_raw & missed, w) if tot > EPS else np.nan),
            "A_share_literal": _r(_wshare(a_raw & missed, w) if tot > EPS else np.nan),
            "C_share_literal": _r(_wshare(c_raw_ & missed, w) if tot > EPS else np.nan),
            "exclusive_C_A_B": {
                "C": _r(_wshare(ex_c & missed, w)),
                "A": _r(_wshare(ex_a & missed, w)),
                "B": _r(_wshare(ex_b & missed, w)),
            },
            "B1_share_incremental_oom": _r(_wshare(b1 & missed, w)),
            "B2_share_commitment_band": _r(_wshare(b2 & missed, w)),
            "B1_share_on_io_fit_sensitivity": _r(_wshare(b1_fit & missed, w)),
            "settlement_sensitivity_day_ahead": {
                "B_share_allin_vs_DA": _r(_wshare((own_avg > dprice) & missed, w)),
                "B1_share_incremental_vs_DA": _r(_wshare((own_inc > dprice) & missed, w)),
                "B_share_allin_vs_max_DA_RT": _r(
                    _wshare((own_avg > np.fmax(dprice, aprice)) & missed, w)
                ),
                "mean_DA_price_missed": _r(
                    float((dprice[missed] * wm).sum() / max(wm.sum(), EPS)), 2
                ),
                "note": "a DA-committed unit is paid the DA price for its scheduled energy; the RT leg is the headline, this is the robustness check.",
            },
            "fuel_convention_sensitivity_henry_hub": {
                "B_share_allin_at_HH": _r(_wshare((own_avg_hh > aprice) & missed, w)),
                "B1_share_incremental_at_HH": _r(_wshare((own_inc_hh > aprice) & missed, w)),
                "print_excess_over_HH_capw_usd_mmbtu": _r(
                    _capw_hr(print_excess, plant_list, p_row, cap_by_plant), 3
                ),
                "print_excess_by_zone_capw": {
                    zn: _r(
                        _capw_hr(
                            np.where(
                                np.array([pz.get(p, -1) == i for p in plant_list]),
                                print_excess,
                                np.nan,
                            ),
                            plant_list, p_row, cap_by_plant,
                        ),
                        3,
                    )
                    for zn, i in z_of.items()
                },
                "note": "OWNER-COURT (miso-212 §8): the 923 print is an all-in delivered cost including fixed firm-transport demand charges; HH daily spot is the pure commodity floor. Reported as the bound on the convention's contribution, never adjudicated here.",
            },
            "margin_actual_minus_allin": _wq(margin_act, wm),
            "margin_actual_minus_incremental": _wq(margin_act_i, wm),
            "margin_actual_minus_incremental_io_fit": _wq((aprice - own_fit)[missed], wm),
            "margin_model_minus_allin": _wq(margin_mod, wm),
            "mean_actual_price_missed": _r(
                float((aprice[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "mean_model_price_missed": _r(
                float((mprice[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "mean_price_gap_actual_minus_model_missed": _r(
                float(((aprice - mprice)[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "mean_allin_cost_missed": _r(
                float((own_avg[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "mean_incremental_cost_missed": _r(
                float((own_inc[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "mean_incremental_cost_missed_io_fit": _r(
                float((own_fit[missed] * wm).sum() / max(wm.sum(), EPS)), 2
            ),
            "heat_rate_mmbtu_per_mwh": {
                "campd_average_burn_capw": _r(
                    _capw_hr(hr_avg_ann, plant_list, p_row, cap_by_plant), 3
                ),
                "measured_incremental_offer_basis_capw": _r(
                    _capw_hr(hr_phys, plant_list, p_row, cap_by_plant), 3
                ),
                "campd_io_fit_incremental_capw": _r(
                    _capw_hr(hr_marg, plant_list, p_row, cap_by_plant), 3
                ),
                "model_offer_implied_econ_capw": _r(
                    _implied_hr(
                        mc_a[ct][econ_sel],
                        fp_a[ct][econ_sel],
                        markup[ct][econ_sel] * anchor
                        + vom[ct][econ_sel]
                        + nox_r[ct][econ_sel] * float(cfg_arm.nox_price)
                        + so2_r[ct][econ_sel] * float(cfg_arm.so2_price),
                        pmax[ct][econ_sel],
                    ),
                    3,
                ),
                "io_fit_capacity_coverage": _r(
                    float((fit_cov * np.array([cap_by_plant.get(int(p), 0.0) for p in plant_list])).sum()
                          / max(capsum, EPS))
                ),
                "class_measured_marg_over_avg": CT_MARG_OVER_AVG,
            },
            "noload_fuel_mmbtu_per_h_fleet": _r(float(noload.sum()), 0),
            "K_a_bar": K_A_BAR,
        }

        # K-b: how much of bucket A flips in-merit when the econ margin goes
        a_hours = a_raw & missed
        flip = a_hours & (model_mw_nm > EPS)
        y["L2"]["K_b_offer_level_flip"] = {
            "A_mwh": _r(float(w[a_hours].sum()), 0),
            "A_flipped_mwh": _r(float(w[flip].sum()), 0),
            "flip_share": _r(
                _wshare(flip, w * a_hours) if float(w[a_hours].sum()) > EPS else np.nan
            ),
            "margin_removed_usd_mwh_capw": _r(
                float(
                    (markup[ct][econ_sel] * anchor * pmax[ct][econ_sel]).sum()
                    / max(pmax[ct][econ_sel].sum(), EPS)
                ),
                2,
            ),
            "K_b_bar": K_B_BAR,
        }

        # ---- run-block anatomy, UNIT grain ---------------------------------
        u_len = np.zeros((len(units), HOURS), dtype=np.int32)
        u_pos = np.full((len(units), HOURS), -1, dtype=np.int8)
        for i in range(len(units)):
            u_len[i], u_pos[i] = _run_blocks(u_mw[i] > 0.0)
        # lift the unit-grain block label to the plant grain the buckets use by
        # MW-weighting the units running in that hour
        lens = np.zeros((len(plant_list), HOURS))
        firsth = np.zeros((len(plant_list), HOURS))
        lasth = np.zeros((len(plant_list), HOURS))
        for (pid, _uid), i in u_row.items():
            r = p_row.get(int(pid))
            if r is None:
                continue
            lens[r] += u_len[i] * u_mw[i]
            firsth[r] += (u_pos[i] == 0) * u_mw[i]
            lasth[r] += (u_pos[i] == 2) * u_mw[i]
        with np.errstate(invalid="ignore", divide="ignore"):
            lens = np.where(g_mw > 0, lens / np.maximum(g_mw, EPS), 0.0)
            firsth = np.where(g_mw > 0, firsth / np.maximum(g_mw, EPS), 0.0)
            lasth = np.where(g_mw > 0, lasth / np.maximum(g_mw, EPS), 0.0)

        def _blockstats(sel):
            ww = g_mw * sel
            t = float(ww.sum())
            if t <= EPS:
                return {}
            return {
                "mwh": _r(t, 0),
                "mw_w_mean_block_len_h": _r(float((lens * ww).sum() / t), 2),
                "share_len_le_4h": _r(float(ww[(lens > 0) & (lens <= 4) & sel].sum() / t)),
                "share_len_ge_12h": _r(float(ww[(lens >= 12) & sel].sum() / t)),
                "first_hour_mw_share": _r(float((firsth * ww).sum() / t)),
                "last_hour_mw_share": _r(float((lasth * ww).sum() / t)),
            }

        y["L2"]["block_anatomy_unit_grain"] = {
            "n_units": len(units),
            "all_running": _blockstats(running),
            "missed": _blockstats(missed),
            "B_hours": _blockstats(b_raw & missed),
            "B1_hours": _blockstats(b1 & missed),
            "B2_hours": _blockstats(b2 & missed),
        }
        bsel = b_raw & missed
        y["L2"]["B_by_zone_mwh"] = {
            zn: _r(
                float(
                    (g_mw * bsel)[
                        [p_row[p] for p in plant_list if pz.get(p, -1) == i]
                    ].sum()
                ),
                0,
            )
            for zn, i in z_of.items()
        }
        bt = max(float((g_mw * bsel).sum()), EPS)
        y["L2"]["B_diurnal"] = {
            "share_in_floor_window": _r(float((g_mw * bsel)[:, FLOOR_WINDOW].sum() / bt)),
            "share_summer_JJA": _r(float((g_mw * bsel)[:, SUMMER].sum() / bt)),
        }
        # ---- what the B hours look like: load factor and the measured
        # reserve state. A peaker held at MIN LOAD in reserve-tight hours is
        # the commitment/AS signature; one at full load is not.
        u_cap_arr = np.maximum(u_mw.max(axis=1), EPS)
        u_lf = u_mw / u_cap_arr[:, None]
        lf = np.zeros((len(plant_list), HOURS))
        for (pid, _uid), i in u_row.items():
            r = p_row.get(int(pid))
            if r is not None:
                lf[r] += u_lf[i] * u_mw[i]
        with np.errstate(invalid="ignore", divide="ignore"):
            lf = np.where(g_mw > 0, lf / np.maximum(g_mw, EPS), 0.0)
        asm = asm_cleared_by_region(year)
        # plant STATE from the CAMPD extract: arrays.state is blank on many
        # CT rows, so the measured source is used and the gap disclosed.
        st_of = {
            int(k): str(v)
            for k, v in cm.groupby("plant_id")["state"].first().items()
        }
        reg_of_row = np.array(
            [MISO_REGION_BY_STATE.get(st_of.get(p, ""), "") for p in plant_list]
        )
        asm_row = np.zeros((len(plant_list), HOURS))
        for r, reg in enumerate(reg_of_row):
            if reg in asm:
                asm_row[r] = asm[reg]
        asm_p90 = {k: float(np.percentile(v, 90)) for k, v in asm.items()}
        tight = np.zeros((len(plant_list), HOURS), dtype=bool)
        for r, reg in enumerate(reg_of_row):
            if reg in asm:
                tight[r] = asm[reg] >= asm_p90[reg]

        def _drv(sel):
            ww = g_mw * sel
            t = float(ww.sum())
            if t <= EPS:
                return {}
            return {
                "mwh": _r(t, 0),
                "mw_w_load_factor": _r(float((lf * ww).sum() / t)),
                "mw_w_region_cleared_reserve_mw": _r(float((asm_row * ww).sum() / t), 0),
                "share_in_region_reserve_top_decile": _r(float(ww[tight & sel].sum() / t)),
            }

        y["L2"]["B_driver_screen"] = {
            "region_of_zone_note": "MISO market region by plant STATE on the published LRZ map (North = LRZ 1; Central = LRZ 2-7; South = LRZ 8-10; Iowa assigned Central, declared).",
            "asm_regions_found": sorted(asm),
            "all_running": _drv(running),
            "missed": _drv(missed),
            "B_hours": _drv(b_raw & missed),
            "B1_hours": _drv(b1 & missed),
            "A_hours": _drv(a_raw & missed),
        }
        # top plants by missed energy — the successor session's own worklist
        miss_by_p = (g_mw * missed).sum(axis=1)
        order = np.argsort(-miss_by_p)[:15]
        y["L2"]["top15_missed_plants"] = [
            {
                "plant": int(plant_list[r]),
                "zone": zones[pz.get(plant_list[r], 0)],
                "state": st_of.get(plant_list[r], ""),
                "cap_mw": _r(cap_by_plant.get(int(plant_list[r]), 0.0), 1),
                "missed_mwh": _r(float(miss_by_p[r]), 0),
                "campd_mwh": _r(float(g_mw[r].sum()), 0),
                "B_share": _r(
                    float((g_mw * b_raw * missed)[r].sum())
                    / max(float(miss_by_p[r]), EPS)
                ),
                "burn_hr": _r(hr_avg_ann[r], 2),
                "incremental_hr": _r(hr_phys[r], 2),
                "print_excess_over_HH": _r(print_excess[r], 3),
            }
            for r in order
            if miss_by_p[r] > 0
        ]

        # ---- L-4/L-1: THE OFFER-FORM COHORT CENSUS. ct_intermediate_split
        # routes a CT_PEAKER plant whose measured median CF >= the threshold to
        # the flatter CT_INTERMEDIATE offer curve. That curve carries NO phys_*
        # keys, so bins_to_fleet gives its tranches offer_markup_hr = 0 and
        # apply_gas_offer_margin (gas_offer_net_revenue_margin, armed) SKIPS
        # them — the cohort's offer stays in the fully fuel-scaled multiplier
        # form the mechanism exists to replace. Measured here, per cohort.
        inter = ct_intermediate_plants(
            "MISO",
            float(cfg_arm.ct_intermediate_cf_threshold),
            bool(cfg_arm.campd_per_unit_attribution),
            bool(cfg_arm.campd_outage_merit_order_guard),
        )
        is_inter = np.array([int(p) in inter for p in plant_list])
        curves = dict(cfg_arm.offer_curve_by_group or {})

        def _cohort(rows_mask, _fp=fp_a):
            # ``fp_a`` is bound as a default so the closure does not read a
            # name the year loop deletes at its end (ruff F821).
            ps = [p for r, p in enumerate(plant_list) if rows_mask[r]]
            js = [j for j in range(ct.size) if int(pcode[ct[j]]) in set(ps)]
            e = [j for j in js if bands[ct][j].startswith("econ")]
            capf = pmax[ct][e] if e else np.array([])
            rr = [p_row[p] for p in ps]
            return {
                "n_plants": len(ps),
                "capacity_mw": _r(sum(cap_by_plant.get(int(p), 0.0) for p in ps), 1),
                "econ_tranches": len(e),
                "cap_w_offer_hr_econ": _r(
                    float((hr_all[ct][e] * capf).sum() / max(capf.sum(), EPS)), 3
                ) if e else None,
                "cap_w_physical_leg_hr_econ": _r(
                    float(((hr_all[ct][e] - markup[ct][e]) * capf).sum()
                          / max(capf.sum(), EPS)), 3
                ) if e else None,
                "cap_w_markup_hr_econ": _r(
                    float((markup[ct][e] * capf).sum() / max(capf.sum(), EPS)), 3
                ) if e else None,
                "campd_avg_burn_hr_capw": _r(
                    _capw_hr(
                        np.where(rows_mask, hr_avg_ann, np.nan),
                        plant_list, p_row, cap_by_plant,
                    ), 3
                ),
                "cap_w_delivered_fuel_usd_mmbtu": _r(
                    float((_fp[ct][e] * capf[:, None]).sum()
                          / max(capf.sum() * HOURS, EPS)), 3
                ) if e else None,
                "econ_cap_hour_share_fuel_above_anchor": _r(
                    float(((_fp[ct][e] > anchor) * capf[:, None]).sum()
                          / max(capf.sum() * HOURS, EPS))
                ) if e else None,
                "campd_mwh": _r(float(g_mw[rr].sum()), 0) if rr else 0.0,
                "screen_mwh": _r(float(model_mw[rr].sum()), 0) if rr else 0.0,
                "missed_mwh": _r(float((g_mw * missed)[rr].sum()), 0) if rr else 0.0,
                "B_mwh": _r(float((g_mw * b_raw * missed)[rr].sum()), 0) if rr else 0.0,
            }

        y["L4_offer_form_cohorts"] = {
            "ct_intermediate_split": bool(cfg_arm.ct_intermediate_split),
            "ct_intermediate_cf_threshold": float(cfg_arm.ct_intermediate_cf_threshold),
            "n_plants_in_iso_cohort": len(inter),
            "gas_offer_margin_anchor": anchor,
            "curve_has_phys_keys": {
                k: sorted(x for x in (curves.get(k) or {}) if x.startswith("phys_"))
                for k in ("CT_PEAKER", "CT_INTERMEDIATE", "CC_REGULAR",
                          "CC_INTERMEDIATE", "ST_GAS", "ST_GAS_INTERMEDIATE")
            },
            "CT_INTERMEDIATE_cohort": _cohort(is_inter),
            "CT_PEAKER_true_cohort": _cohort(~is_inter),
        }

        # ---- CANDIDATE STATIC REACH (the miso-213 L-3 instrument; NOT an arm).
        # Reprice the CT_INTERMEDIATE cohort's ECON tranches into the SAME
        # net-revenue-margin form the rest of the MISO gas fleet already
        # carries, using the SAME frozen measured p50s CT_PEAKER uses
        # (miso_campd_marginal_hr_summary.csv, n = 249: marg_econ_low 0.687 /
        # marg_econ_high 0.691). By the margin form's own algebra
        #   mc' = mc + (heat_rate - phys x HR_base) x (anchor - F),
        # so at fuel == anchor it is byte-identical to today. HR_base per plant
        # is the raw fleet heat rate (this curve's committed multiplier is 1.00).
        hr_base = {}
        for g in raw_fleet:
            if str(getattr(g, "plant_group", "")) == KLASS:
                hr_base.setdefault(int(g.plant_code), float(g.heat_rate))
        cim = curves.get("CT_INTERMEDIATE") or {}
        lo_m, hi_m = float(cim.get("econ_low", 1.0)), float(cim.get("econ_high", 1.0))
        PHYS_LO, PHYS_HI = 0.687, 0.691   # frozen class p50s, CT_PEAKER's own
        mc_cand = mc_a[ct].copy()
        n_repriced = 0
        cand_rows = []
        for j in range(ct.size):
            pc = int(pcode[ct[j]])
            if pc not in inter or not bands[ct][j].startswith("econ"):
                continue
            hb = hr_base.get(pc)
            if not hb or markup[ct][j] > 0.0:   # already in the margin form
                continue
            mult = hr_all[ct][j] / hb
            frac = 0.0 if hi_m <= lo_m else min(1.0, max(0.0, (mult - lo_m) / (hi_m - lo_m)))
            phys = PHYS_LO + frac * (PHYS_HI - PHYS_LO)
            mk_new = hr_all[ct][j] - phys * hb
            if mk_new <= 0.0:
                continue
            mc_cand[j] = mc_a[ct][j] + mk_new * (anchor - fp_a[ct][j])
            n_repriced += 1
            cand_rows.append((float(pmax[ct][j]), float(mk_new * anchor)))
        mw_cand = availcap * (mc_cand <= zp)
        model_mw_cand = np.zeros_like(model_mw)
        for p_, js in rows_of.items():
            if js:
                model_mw_cand[p_row[p_]] = mw_cand[js].sum(axis=0)
        cand_flip = missed & (model_mw_cand > EPS)
        capsum_c = sum(c for c, _ in cand_rows) or EPS
        y["L4_candidate_static_reach"] = {
            "what": "CT_INTERMEDIATE econ tranches repriced into the net-revenue-margin form at the frozen class p50s; zero free parameters; byte-identical at fuel == anchor.",
            "tranches_repriced": n_repriced,
            "cap_w_fixed_margin_usd_mwh": _r(
                sum(c * m for c, m in cand_rows) / capsum_c, 2
            ),
            "screen_twh_arm": _r(float(mw_a.sum()) / 1e6, 3),
            "screen_twh_candidate": _r(float(mw_cand.sum()) / 1e6, 3),
            "screen_delta_twh": _r(float((mw_cand - mw_a).sum()) / 1e6, 3),
            "missed_mwh_flipped_in": _r(float((g_mw * cand_flip).sum()), 0),
            "missed_flip_share": _r(_wshare(cand_flip, w)),
            "flip_share_of_bucket_C": _r(
                _wshare(cand_flip & c_raw_ & missed, w * (c_raw_ & missed))
                if float(w[c_raw_ & missed].sum()) > EPS else np.nan
            ),
            "flip_share_of_bucket_A": _r(
                _wshare(cand_flip & a_raw & missed, w * (a_raw & missed))
                if float(w[a_raw & missed].sum()) > EPS else np.nan
            ),
            "flip_share_of_bucket_B": _r(
                _wshare(cand_flip & b_raw & missed, w * (b_raw & missed))
                if float(w[b_raw & missed].sum()) > EPS else np.nan
            ),
        }
        # bucket C by offer-form cohort — C is the offer-form bucket by
        # construction (own all-in cost <= the MODEL's own price, model idle)
        r_int = [p_row[p_] for p_ in plant_list if int(p_) in inter]
        r_true = [p_row[p_] for p_ in plant_list if int(p_) not in inter]
        cmask = c_raw_ & missed
        y["L2"]["bucket_C_by_cohort_mwh"] = {
            "CT_INTERMEDIATE": _r(float((g_mw * cmask)[r_int].sum()), 0) if r_int else 0.0,
            "CT_PEAKER_true": _r(float((g_mw * cmask)[r_true].sum()), 0) if r_true else 0.0,
        }

        # symmetry: hours the MODEL runs the plant and CAMPD shows it off
        over = (model_mw > EPS) & ~running
        y["L2"]["over_dispatch"] = {
            "plant_hours": int(over.sum()),
            "screen_mwh": _r(float((model_mw * over).sum()), 0),
        }

        # ---------------- L-3 the gap's shape -------------------------------
        campd_h = g_mw.sum(axis=0)
        gap = campd_h - lp_arm
        under = np.maximum(gap, 0.0)
        y["L3_gap_shape"] = {
            "campd_twh": _r(campd_h.sum() / 1e6, 3),
            "lp_class_twh": _r(lp_arm.sum() / 1e6, 3),
            "net_gap_twh": _r(gap.sum() / 1e6, 3),
            "under_mwh": _r(under.sum(), 0),
            "under_share_summer_JJA": _r(_wshare(SUMMER, under)),
            "under_share_h15_21": _r(_wshare(FLOOR_WINDOW, under)),
            "under_by_month_mwh": [_r(under[MO == m].sum(), 0) for m in range(1, 13)],
            "under_by_hod_mwh": [_r(under[HOD == h].sum(), 0) for h in range(24)],
            "hours_share_JJA": _r(float(SUMMER.sum()) / HOURS, 3),
            "P3_bar": 0.55,
        }
        rep["years"][str(year)] = y
        del mc_a, mc_c, fp_a, arrays, fleet, raw_fleet, fleet_a
        gc.collect()

    # ---------------- L-4 the rule-19 census --------------------------------
    lg = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    d2 = [r for r in lg["diagnostics"]["D2"]["rows"] if r.get("class") == KLASS]
    # D-4 labels a floor as "<mechanism> x <class>", so match on the stem
    ct_mechs = {x.get("mechanism") for x in d2} | {"reliability_floor"}
    d4 = [
        r
        for r in lg["diagnostics"]["D4"]["rows"]
        if str(r.get("floor")).split(" ")[0] in ct_mechs
        and (KLASS in str(r.get("floor")) or " " not in str(r.get("floor")))
    ]
    d1 = [r for r in lg["diagnostics"]["D1"]["rows"] if r.get("class") == KLASS]
    limbs = [
        {
            "zone": r.zone, "driver": r.driver, "enabled": bool(r.enabled),
            "threshold": r.threshold, "floor_pct": r.floor_pct,
            "window": f"h{r.start_hour}-{r.end_hour}", "min_event_hours": r.min_event_hours,
        }
        for r in RELIABILITY_FLOOR_REGISTRY["MISO"]
        if r.plant_class == KLASS
    ]
    ob = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    rep["L4_census"] = {
        "D2_rows_CT_PEAKER": d2,
        "D2_mechanisms": sorted({r["mechanism"] for r in d2}),
        "D2_max_share_of_class": _r(max([r["share_of_class"] for r in d2], default=0.0)),
        "D2_summary_CT_PEAKER": [
            r for r in lg["diagnostics"]["D2"]["summary"] if r.get("class") == KLASS
        ],
        "D2_failures_all": lg["diagnostics"]["D2"].get("failures"),
        "D2_notes": lg["diagnostics"]["D2"].get("notes"),
        "d2_peaker_max_share_gate": lg["gates"]["d2_peaker_max_share"],
        "D4_rows_touching_those_mechanisms": d4,
        "D1_rows_CT_PEAKER": d1,
        "reliability_floor_limbs": limbs,
        "reliability_floor_armed": bool(ob.get("reliability_floor")),
        "reliability_floor_overrides": ob.get("reliability_floor_overrides"),
        "offer_band_CT_PEAKER": ob.get("offer_curve_by_group", {}).get(KLASS),
        "ct_knobs": {
            k: ob.get(k)
            for k in (
                "ct_intermediate_split", "ct_intermediate_cf_threshold",
                "ct_committed_hr_mult", "ct_econ_hr_mult", "ct_peak_hr_penalty",
                "ct_mustrun_floor_frac", "ct_mustrun_per_plant", "ct_netload_drag",
                "ct_deployment_overlay", "ct_deployment_floor_frac",
                "measured_ct_heat_rates", "tranche_startup_amortization",
                "miso_commitment_posture", "gas_offer_net_revenue_margin",
                "gas_offer_margin_anchor",
            )
        },
        "commitment_bridges_armed_for_MISO": [
            k for k in ("caiso_ra_mustoffer", "ercot_gas_commitment_bridge",
                        "nyiso_gas_commitment_bridge", "miso_commitment_posture")
            if ob.get(k)
        ],
        "P4_bar": {"only_mechanism": "reliability_floor", "c8_share_max": 0.15},
    }

    # ---------------- the decision ------------------------------------------
    bs = [rep["years"][str(y_)]["L2"].get("B_share_literal") for y_ in YEARS]
    b1s = [rep["years"][str(y_)]["L2"].get("B1_share_incremental_oom") for y_ in YEARS]
    b2s = [rep["years"][str(y_)]["L2"].get("B2_share_commitment_band") for y_ in YEARS]
    fl = [
        rep["years"][str(y_)]["L2"].get("K_b_offer_level_flip", {}).get("flip_share")
        for y_ in YEARS
    ]
    cov = [rep["years"][str(y_)]["N1_footing"]["cems_covered_capacity_share"] for y_ in YEARS]
    n_b = sum(1 for v in bs if v is not None and v >= K_A_BAR)
    n_f = sum(1 for v in fl if v is not None and v >= K_B_BAR)
    n_b1 = sum(1 for v in b1s if v is not None and v >= K_A_BAR)
    rep["decision"] = {
        "B_share_by_year": dict(zip(map(str, YEARS), bs)),
        "B1_share_by_year_incremental_oom": dict(zip(map(str, YEARS), b1s)),
        "B2_share_by_year_commitment_band": dict(zip(map(str, YEARS), b2s)),
        "K_a_on_incremental_years_over_bar": n_b1,
        "K_a_on_incremental_pass": n_b1 >= 2,
        "K_a_years_over_bar": n_b,
        "K_a_pass": n_b >= 2,
        "A_flip_share_by_year": dict(zip(map(str, YEARS), fl)),
        "K_b_years_over_bar": n_f,
        "K_b_kill_fires": n_f >= 2,
        "cems_cov_by_year": dict(zip(map(str, YEARS), cov)),
        "K_e_pass": all(v is not None and v >= K_E_BAR for v in cov),
        "charter_ab": bool(n_b >= 2 and n_f < 2 and all(v is not None and v >= K_E_BAR for v in cov)),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("DECISION:", json.dumps(rep["decision"], indent=1))


if __name__ == "__main__":
    main()
