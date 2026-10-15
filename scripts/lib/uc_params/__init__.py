"""The ``uc-params`` datatype: measured per-plant commitment physics (lane UC-1).

Registry-driven, ISO-agnostic derivation of the integer-cluster parameters the
MILP unit-commitment stage reads (``ScenarioConfig.unit_commitment_milp``;
``docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-engine-2026-10-03.md``
section 1.2-1.3). Per-ISO scoping is a sibling module
(``scripts/lib/uc_params/<iso>.py``) that registers an :class:`IsoSpec` naming
the CAMPD state footprint; the derivation itself is the one generic path in
this module, so adding an ISO never touches shared code.

Construction (the plant-basis convention of every CAMPD commitment derive in
the repo, ``campd_gas_commitment_params_plant_<ISO>.csv``, and the no-load
regression of closeout-PJM-decommit B0 / UC-0 F7):

* every unit is classed by its CAMPD ``unitType`` / ``primaryFuelInfo`` into a
  family token (:data:`UC_CLASS_BY_UNIT_TYPE`, :func:`classify_unit`);
* each CEMS unit is mapped to the EIA plant the fleet keys on
  (:func:`market_sim.data.campd_crosswalk.camd_to_eia_plant`: the operative
  remap, then the crosswalk of record at unit then facility grain). Grouping
  by the raw CAMD facility id missed every plant whose CEMS id differs from
  its EIA id (UC-1-FIX-3; FINDING-ucmilp-fix2-floor-mindown-2026-10-10 §7);
* the plant's units of one family are summed to ONE hourly plant series;
  HSL = p99.5 of that series, online = load >= max(1 MW, 0.05 x HSL), LSL = p5
  of the online-hour load, ``mlf = LSL / HSL``;
* ``ut_h`` / ``dt_h`` / ``n_runs`` are measured per UNIT, never on the plant
  series (UC-DATA-UT, owner ruling r13 2026-10-15, rule 23): each unit's own
  series is online at load >= max(1 MW, 0.05 x the unit's own HSL), its on-runs
  and off-gaps are taken inside contiguous reported stretches only (an
  ozone-season reporter's winter is no gap), and ``ut_h`` / ``dt_h`` are p25 of
  the runs / gaps pooled over the cluster's units. A plant series is "on" while
  ANY unit is on, so its runs measured how long the plant stayed dispatched,
  an economic run length, and applying that per unit as a physical min-up was
  the derivation defect (FINDING-ucmilp-diag-undercommit-2026-10-14 cause 3);
* the plant no-load heat input is the sum of per-unit OLS intercepts of
  ``heatInput`` on ``grossLoad`` over online hours (fit screen: >= 200 points
  spanning >= 10 % of the unit peak; intercept floored at 0);
* a class-fallback row (``plant_code = 0``) per family pools the fitted plants.

Vintage span :data:`POOLED_VINTAGES` (2023-2025). Reads only ``data/raw``;
re-derived only when the CAMPD source updates (rule 23).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.campd_crosswalk import camd_to_eia_plant, load_crosswalk
from scripts.lib.datatype_registry import make_registry

DATATYPE = "uc-params"

#: Pooled CAMPD vintages (the span every CAMPD commitment derive uses).
POOLED_VINTAGES: tuple[int, ...] = (2023, 2024, 2025)

#: Canonical column order (the schema's key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "plant_code",
    "uc_class",
    "n_units",
    "hsl_mw",
    "lsl_mw",
    "mlf",
    "ut_h",
    "dt_h",
    "noload_mmbtu_h",
    "noload_units_fitted",
    "noload_r2_median",
    "online_frac",
    "n_runs",
    "years",
    "source",
)

#: The family vocabulary (schema header). Order is the fallback-row order.
UC_CLASSES: tuple[str, ...] = ("cc", "ct", "coal", "st_gas")

#: CAMPD ``unitType`` values that name a family directly; every other unit
#: type is a boiler, classed by fuel (coal vs. everything else -> st_gas).
UC_CLASS_BY_UNIT_TYPE: dict[str, str] = {
    "Combined cycle": "cc",
    "Combustion turbine": "ct",
}

#: Online threshold: a plant-hour is online when its summed gross load is at
#: least max(ONLINE_MIN_MW, ONLINE_FRAC_OF_HSL x HSL) — the WP-3 / SPP-97
#: convention of the existing CAMPD commitment derives.
ONLINE_MIN_MW: float = 1.0
ONLINE_FRAC_OF_HSL: float = 0.05
#: HSL and LSL percentiles of the plant series (the existing derives' p99.5 /
#: p5 construction).
HSL_PERCENTILE: float = 99.5
LSL_PERCENTILE: float = 5.0
#: Minimum-run / minimum-down duration percentile of the measured runs/gaps.
DURATION_PERCENTILE: float = 25.0
#: No-load regression fit screen (closeout-PJM-decommit B0; UC-0 F7).
NOLOAD_MIN_POINTS: int = 200
NOLOAD_MIN_RANGE_FRAC: float = 0.10

_CAMPD_DIR = Path("campd-unit-level")
#: The crosswalk of record under the raw root (``data.campd_crosswalk``).
_CROSSWALK_CSV = Path("reference") / "camd-eia-crosswalk" / "epa_eia_crosswalk.csv"
_CROSSWALK_PUDL = Path("pudl") / "core_epa__assn_eia_epacamd_subplant_ids.parquet"
_COLUMNS = (
    "facilityId",
    "unitId",
    "date",
    "hour",
    "opTime",
    "grossLoad",
    "heatInput",
    "primaryFuelInfo",
    "unitType",
)

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [("iso", str), ("campd_states", tuple), ("extra_facilities", tuple, ())],
    package=__name__,
    iso_modules=(
        "caiso",
        "ercot",
        "miso",
        "neiso",
        "nwpp",
        "nyiso",
        "pjm",
        "soco",
        "spp",
    ),
    raw_subpath=(str(_CAMPD_DIR),),
    string_cols=("uc_class", "years", "source"),
    float_cols=(
        "hsl_mw",
        "lsl_mw",
        "mlf",
        "noload_mmbtu_h",
        "noload_r2_median",
        "online_frac",
    ),
    sort_by=("uc_class", "plant_code"),
)
IsoSpec, REGISTRY, register = _R.IsoSpec, _R.REGISTRY, _R.register
load_registry, raw_dir_for, finalize = _R.load_registry, _R.raw_dir_for, _R.finalize


def classify_unit(unit_type: str, fuel: str) -> str:
    """Return the family token of one CAMPD unit (schema header vocabulary)."""
    fam = UC_CLASS_BY_UNIT_TYPE.get(str(unit_type))
    if fam is not None:
        return fam
    return "coal" if "coal" in str(fuel).lower() else "st_gas"


def _runs_and_gaps(online: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Lengths of the on-runs and of the off-gaps BETWEEN them (bool mask)."""
    if online.size == 0 or not online.any():
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    padded = np.concatenate([[False], online, [False]])
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    starts, ends = edges[0::2], edges[1::2]
    runs = ends - starts
    gaps = starts[1:] - ends[:-1]
    return runs, gaps


def _unit_runs_and_gaps(cluster: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """On-runs and off-gaps of every UNIT of one cluster, pooled (hours).

    A unit is keyed by its CEMS ``(facilityId, unitId)`` (two CEMS facilities
    mapped to one EIA plant may reuse a unit id). Each unit's series is online
    at ``load >= max(ONLINE_MIN_MW, ONLINE_FRAC_OF_HSL x its own HSL)`` and is
    cut at every hour it did not report, so a run or gap never bridges a
    reporting hole (a May-September ozone-season reporter's off-season).
    """
    runs: list[np.ndarray] = []
    gaps: list[np.ndarray] = []
    one_hour = np.timedelta64(1, "h")
    for _, unit in cluster.groupby(["facilityId", "unitId"], sort=False):
        series = unit.groupby("ts", sort=True)["grossLoad"].sum()
        load = series.to_numpy(dtype=float)
        if load.size == 0 or float(load.max()) <= 0.0:
            continue
        hsl = float(np.percentile(load, HSL_PERCENTILE))
        if hsl <= 0.0:
            continue
        online = load >= max(ONLINE_MIN_MW, ONLINE_FRAC_OF_HSL * hsl)
        ts = series.index.to_numpy(dtype="datetime64[ns]")
        cuts = np.flatnonzero(np.diff(ts) != one_hour) + 1
        for seg in np.split(online, cuts):
            r, g = _runs_and_gaps(seg)
            runs.append(r)
            gaps.append(g)
    if not runs:
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    return np.concatenate(runs), np.concatenate(gaps)


def _noload_fit(unit: pd.DataFrame) -> tuple[float | None, float | None]:
    """Per-unit OLS intercept of heatInput on grossLoad over online hours.

    Returns ``(intercept_mmbtu_h, r2)`` or ``(None, None)`` when the fit screen
    (:data:`NOLOAD_MIN_POINTS` points spanning :data:`NOLOAD_MIN_RANGE_FRAC`
    of the unit peak) is not met. The intercept is floored at zero.
    """
    load = unit["grossLoad"].to_numpy(dtype=float)
    heat = unit["heatInput"].to_numpy(dtype=float)
    optime = unit["opTime"].to_numpy(dtype=float)
    mask = (optime >= 1.0) & (load > 0.0) & (heat > 0.0)
    x, y = load[mask], heat[mask]
    peak = float(np.nanmax(load)) if load.size else 0.0
    if peak <= 0.0 or x.size < NOLOAD_MIN_POINTS:
        return None, None
    if np.ptp(x) < NOLOAD_MIN_RANGE_FRAC * peak:
        return None, None
    slope, intercept = np.polyfit(x, y, 1)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    resid = y - (intercept + slope * x)
    r2 = 1.0 - float(np.sum(resid**2)) / ss_tot if ss_tot > 0.0 else 0.0
    return max(float(intercept), 0.0), r2


def _load_state_year(path: Path) -> pd.DataFrame:
    """One CAMPD extract with a plant-hour timestamp and the family token."""
    df = pd.read_parquet(path, columns=list(_COLUMNS))
    if df.empty:
        return df
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df["facilityId"] = df["facilityId"].astype("int64")
    df["ts"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
    df["grossLoad"] = df["grossLoad"].astype(float).fillna(0.0)
    df["heatInput"] = df["heatInput"].astype(float).fillna(0.0)
    df["opTime"] = df["opTime"].astype(float).fillna(0.0)
    ut = df["unitType"].astype(str)
    fuel = df["primaryFuelInfo"].astype(str)
    fam = ut.map(UC_CLASS_BY_UNIT_TYPE)
    coal = fuel.str.contains("coal", case=False, na=False)
    df["uc_class"] = fam.where(fam.notna(), np.where(coal, "coal", "st_gas"))
    return df[
        ["facilityId", "unitId", "uc_class", "ts", "opTime", "grossLoad", "heatInput"]
    ]


def _plant_stats(cluster: pd.DataFrame) -> dict | None:
    """Plant-basis statistics of one (facility, family) cluster frame."""
    units = cluster.groupby("unitId", sort=False)
    plant = cluster.groupby("ts", sort=True)["grossLoad"].sum()
    load = plant.to_numpy(dtype=float)
    if load.size == 0 or float(load.max()) <= 0.0:
        return None
    hsl = float(np.percentile(load, HSL_PERCENTILE))
    if hsl <= 0.0:
        return None
    online = load >= max(ONLINE_MIN_MW, ONLINE_FRAC_OF_HSL * hsl)
    if not online.any():
        return None
    lsl = float(np.percentile(load[online], LSL_PERCENTILE))
    # Durations per unit (rule 23 defect fix, UC-DATA-UT): the plant mask's
    # runs are how long ANY unit stayed on, not how long a unit must.
    runs, gaps = _unit_runs_and_gaps(cluster)
    ut_h = (
        int(max(1, round(np.percentile(runs, DURATION_PERCENTILE)))) if runs.size else 1
    )
    dt_h = (
        int(max(1, round(np.percentile(gaps, DURATION_PERCENTILE)))) if gaps.size else 1
    )
    n_units = 0
    intercepts: list[float] = []
    r2s: list[float] = []
    for _, unit in units:
        uload = unit["grossLoad"].to_numpy(dtype=float)
        if uload.size == 0 or float(uload.max()) <= 0.0:
            continue
        n_units += 1
        intercept, r2 = _noload_fit(unit)
        if intercept is not None:
            intercepts.append(intercept)
            r2s.append(float(r2))
    if n_units == 0:
        return None
    return {
        "n_units": n_units,
        "hsl_mw": hsl,
        "lsl_mw": lsl,
        "mlf": float(np.clip(lsl / hsl, 0.0, 1.0)),
        "ut_h": ut_h,
        "dt_h": dt_h,
        "noload_mmbtu_h": float(sum(intercepts)) if intercepts else np.nan,
        "noload_units_fitted": len(intercepts),
        "noload_r2_median": float(np.median(r2s)) if r2s else np.nan,
        "online_frac": float(online.mean()),
        "n_runs": int(runs.size),
    }


def _fallback_rows(rows: pd.DataFrame, years: str, source: str) -> list[dict]:
    """One ``plant_code = 0`` row per family pooling the fitted plants."""
    out: list[dict] = []
    for fam in UC_CLASSES:
        sub = rows[(rows["uc_class"] == fam) & rows["noload_mmbtu_h"].notna()]
        if sub.empty:
            continue
        cap = sub["hsl_mw"].to_numpy(dtype=float)
        w = cap / cap.sum()
        out.append(
            {
                "plant_code": 0,
                "uc_class": fam,
                "n_units": int(len(sub)),
                "hsl_mw": float(cap.sum()),
                "lsl_mw": float(sub["lsl_mw"].sum()),
                "mlf": float(np.clip((sub["mlf"].to_numpy() * w).sum(), 0.0, 1.0)),
                "ut_h": int(max(1, round((sub["ut_h"].to_numpy() * w).sum()))),
                "dt_h": int(max(1, round((sub["dt_h"].to_numpy() * w).sum()))),
                "noload_mmbtu_h": float(sub["noload_mmbtu_h"].sum()),
                "noload_units_fitted": int(sub["noload_units_fitted"].sum()),
                "noload_r2_median": float(sub["noload_r2_median"].median()),
                "online_frac": float((sub["online_frac"].to_numpy() * w).sum()),
                "n_runs": int(sub["n_runs"].sum()),
                "years": years,
                "source": source
                + "; CLASS FALLBACK: the fitted plants of the family pooled",
            }
        )
    return out


def derive_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Build the schema-shaped ``uc-params`` frame for one registered ISO.

    Scans ``<raw_root>/campd-unit-level/<ST>_<year>.parquet`` for the spec's
    states over :data:`POOLED_VINTAGES` (a missing extract is skipped, so
    coverage widens as extracts land) and returns one row per (facility,
    family) cluster plus the class-fallback rows. Empty when nothing was read.
    """
    spec = REGISTRY[iso.upper()]
    campd = raw_root / _CAMPD_DIR
    frames: list[pd.DataFrame] = []
    read: list[str] = []
    extra: dict[str, set[int]] = {}
    for state, fac in spec.extra_facilities:
        if state not in spec.campd_states:
            extra.setdefault(str(state), set()).add(int(fac))
    for state in (*spec.campd_states, *sorted(extra)):
        for year in POOLED_VINTAGES:
            path = campd / f"{state}_{year}.parquet"
            if not path.is_file():
                continue
            df = _load_state_year(path)
            if state in extra:
                df = df[df["facilityId"].isin(sorted(extra[state]))]
            if not df.empty:
                frames.append(df)
                read.append(path.name)
    if not frames:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    data = pd.concat(frames, ignore_index=True)
    # Group by the EIA plant the fleet keys on, not the raw CEMS facility id.
    crosswalk = load_crosswalk(raw_root / _CROSSWALK_CSV, raw_root / _CROSSWALK_PUDL)
    data["plant_code"] = camd_to_eia_plant(
        data["facilityId"].to_numpy(), data["unitId"].to_numpy(), crosswalk
    )
    years = f"{POOLED_VINTAGES[0]}-{POOLED_VINTAGES[-1]}"
    source = (
        f"EPA CAMPD unit-level hourly grossLoad/heatInput ({len(read)} extracts: "
        f"{', '.join(read)}); plant basis per (EIA plant, unit-type family), CEMS "
        "units mapped to EIA plants by campd_crosswalk.camd_to_eia_plant: "
        f"HSL = p{HSL_PERCENTILE} of the summed load, online >= max({ONLINE_MIN_MW} MW, "
        f"{ONLINE_FRAC_OF_HSL} x HSL), LSL = p{LSL_PERCENTILE} of online-hour load, "
        f"ut_h/dt_h = p{DURATION_PERCENTILE} of per-UNIT on-runs/off-gaps (unit online "
        f">= max({ONLINE_MIN_MW} MW, {ONLINE_FRAC_OF_HSL} x unit HSL), cut at reporting "
        "holes, pooled over the cluster's units), no-load = sum of "
        f"per-unit OLS intercepts of heatInput on grossLoad over online hours "
        f"(>= {NOLOAD_MIN_POINTS} points, range >= {NOLOAD_MIN_RANGE_FRAC} x peak)"
    )
    rows: list[dict] = []
    for (fac, fam), cluster in data.groupby(["plant_code", "uc_class"], sort=True):
        stats = _plant_stats(cluster)
        if stats is None:
            continue
        rows.append(
            {
                "plant_code": int(fac),
                "uc_class": str(fam),
                **stats,
                "years": years,
                "source": source,
            }
        )
    if not rows:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    frame = pd.DataFrame(rows)
    frame = pd.concat(
        [frame, pd.DataFrame(_fallback_rows(frame, years, source))], ignore_index=True
    )
    frame = finalize(frame)
    for col in (
        "plant_code",
        "n_units",
        "ut_h",
        "dt_h",
        "noload_units_fitted",
        "n_runs",
    ):
        frame[col] = frame[col].astype("int64")
    return frame[list(CANONICAL_COLUMNS)]
