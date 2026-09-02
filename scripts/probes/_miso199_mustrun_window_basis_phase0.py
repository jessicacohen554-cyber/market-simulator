"""miso-199 PHASE 0 — the per-plant must-run floor's WINDOW BASIS: is it the binding defect?

ZERO-SOLVE CENSUS. **The rule below is frozen in this docstring and the file is
pushed + blob-verified BEFORE any adjudicating quantity is computed** (the
standing session pattern; miso-198 §2, miso-197 §10, miso-196 §7). Nothing here
is weighed against a price residual (rule 1 ``[R-STRUCT]``): C3a does not appear
in this probe at all, not even as a direction — the window question is settled
on conduct reproduction alone.

CHARTER (miso-199). FINDING-miso198 §4 named the WINDOW BASIS the binding defect
and handed it on as the successor lever (§7 item 1). The mechanism-level result
it proved: a level that is non-pinning INSIDE ITS OWN SAMPLE over-asserts ONCE
PLACED IN THE FLOOR'S WINDOW, because the floor's window is the top-
``online_frac`` fraction of hours ranked by SYSTEM LOAD (arrays.py:2842-2866)
while the conduct's own hour set is the plant's COMMITMENT STATE. The two sets
only partly overlap. The census's W channel (0.197/0.163/0.153 of the gap)
UNDERSTATES this, because W counts only measured energy OUTSIDE the window and
never the window's MISPLACEMENT, which surfaces as over-assertion INSIDE it.

**This census does not assume that premise — it tests it, and is prepared to
refute it.** If the LEVEL channel of the over-assertion partition dominates
instead, the charter's premise is wrong, the window family is refused, and the
session escalates WITHOUT SOLVING rather than building a lever the measurement
does not support.

Keeper: ``2026-09-01-miso-198-oomlevel`` (bundle ``results/calibration/miso198_oom_B``).
Rule 22: 2023-2025 only, committed artifacts + raw CAMPD, no marker touched, no
solve. Rule 15: nothing runs, nothing to register.

===============================================================================
BASES (inherited VERBATIM from the miso-198 census; imported, never restated)
===============================================================================

**B1 — the LOAD-BEARING fleet basis: ``run_year``'s OWN chain**
(``ph0.build_run_year_fleet``). Per the miso-197 §6 instrument note a probe's
fleet basis must be ``fleet_to_bins(load_fleet_from_csv(...) + retired_units)``
-> ``build_base_fleet`` -> ``build_dispatch_fleet`` ->
``generators_to_fleet_arrays``, NOT ``fleet.assembly.load_or_synthesize_bins``
(the two diverge at Cottonwood 55358). The ``ScenarioConfig`` is rebuilt from
THIS session's keeper (``miso198_oom_B``), so the floors read here are the
floors the CURRENT keeper solved with.

**B2 — the MEASURED basis: raw CAMPD unit-level hourly through the FROZEN
deriver's own helpers** (``ph0.measured_year``), rule 23 ``[R-FROZEN-DERIVE]``.
The plant-online mask is the frozen one: ``net > _ONLINE_FRAC x nameplate x
avail_mult`` (5 % of AVAILABLE capacity). **The measured online mask IS the
commitment-state object this census is about** — no model dispatch, no price.

**B3 — the COMMITTED keeper artifacts.** ``run_config.json`` and the
``hourly/system_<year>`` sidecar. The sidecar supplies BOTH the SYSTEM
``load_shape`` the incumbent window is ranked by (``demand.sum(axis=0)``,
run_calibration.py:3176 — supplying it is not optional, see below) AND, because
it is stored PER ZONE, the per-zone demand series N-3(iv) reads. The
``class_hourly_<year>`` sidecar supplies the solved ``wind``/``solar`` series.

**THE INSTRUMENT DEFECT THAT MUST NOT RECUR** (miso-198 §3, inherited): with
``load_shape=None`` the runtime's floor block falls through to ``target[:] =
level`` (arrays.py:2861) and spans ALL 8,760 hours instead of the plant's
measured window — which would make the window channel of THIS census identically
empty and silently confirm nothing. ``ph0.build_run_year_fleet`` passes the
sidecar vector; this probe inherits it and re-asserts the resulting floor
against the solve's own logged figure in ``--satisfiability``.

===============================================================================
THE FROZEN RULE
===============================================================================

Every quantity below is restricted to the floored ST_GAS plants — the plants
that actually carry ``MECH_ST_GAS_MUSTRUN_PER_PLANT``. The POPULATION channel
(plants carrying no floor) is miso-198 §3 L-3b's object, is NOT this charter's
(constraint (a): no membership change), and is excluded here by construction.

**N-1 THE WINDOW OBJECT** (measurement, no pass/fail). Per floored plant x year,
with ``H_floor`` = hours the plant's armed floor is > 0 and ``H_meas`` = the
plant's measured-online hours:
  * ``k`` = ``|H_floor|``;  ``m`` = ``|H_meas|``;
  * ``hit``    = ``|H_floor n H_meas| / |H_floor|`` — the share of floored hours
    the plant was measurably RUNNING (the floor's precision);
  * ``cov``    = ``|H_floor n H_meas| / |H_meas|`` — the share of the plant's
    real commitment the window covers (its recall);
  * ``chance`` = ``m / 8760`` — the hit rate an ARBITRARY window achieves by
    construction, so ``lift = hit / chance`` is the information the SYSTEM-LOAD
    ranking actually carries about this plant's commitment state.
  * **L-1a** the window is INFORMATIVE iff ``lift > 1.0``; **L-1b** it is
    WELL-PLACED iff ``hit >= 0.80``. Reported per plant and energy-weighted.

**N-2 THE OVER-ASSERTION PARTITION — the load-bearing identity.** miso-198 §4
measured the keeper's fleet over-assertion share ``O / raw_assertion`` at
0.070 / 0.067 / 0.057 but never said WHERE it comes from. With ``flr`` the armed
floor MW and ``meas`` the measured net MW, ``O = SUM max(0, flr - meas)`` over
floored plant-hours partitions EXACTLY by whether the hour is a measured
commitment hour:
  * **O_mis (MISPLACEMENT)** = ``SUM_{h in H_floor \\ H_meas} max(0, flr - meas)``
    — energy asserted in hours the plant's own meter says it was NOT RUNNING.
    This is rule 17 ``[R-FLOOR-WINDOW]``'s "binding in hours its own driver
    evidence says the class is offline", i.e. a bug by definition.
  * **O_lvl (LEVEL)** = ``SUM_{h in H_floor n H_meas} max(0, flr - meas)`` —
    energy asserted ABOVE what the plant made in hours it WAS running.
  * identity: ``O_mis + O_lvl == O``, asserted to **1e-9** relative.
  * **L-2a DOMINANT** = the channel holding >= **0.45** of ``O`` in >= **2 of 3**
    years.
  * **L-2b THE CHARTER'S PREMISE HOLDS** iff the dominant channel is ``O_mis``.
    **If it is ``O_lvl``, the premise is REFUTED**: the over-assertion is a
    residual level effect inside correctly-placed hours, the window family is
    REFUSED, and the session escalates WITHOUT SOLVING. This line is declared
    before any number is computed and is not revisited.

**N-3 THE STRUCTURE OF THE MISPLACEMENT** (measurement; it tells the candidate
FAMILIES apart, and it does NOT select among them — selection is a separate
probe under its own frozen criterion, the miso-198 census/selection split).
Over the symmetric difference of ``H_floor`` and ``H_meas``, energy-weighted by
the floor MW where the floor is what is misplaced:
  * **(i) SEASONAL** — ``|H_floor \\ H_meas|`` and ``|H_meas \\ H_floor|`` by
    MONTH. Concentration is measured as the share of the total symmetric
    difference carried by the worst 4 calendar months.
  * **(ii) DIURNAL** — the same by HOUR-OF-DAY, worst 8 hours.
  * **(iii) RUN STRUCTURE** — mean contiguous run length and run COUNT of
    ``H_floor`` vs ``H_meas``. A commitment state is made of long runs; a
    top-k-by-load hour set need not be. Reported as ``runlen_ratio =
    mean_run(H_floor) / mean_run(H_meas)``.
  * **(iv) DRIVER / GEOGRAPHY** — the point-biserial correlation of the plant's
    measured online indicator with each of: SYSTEM load, the plant's OWN ZONE's
    load, SYSTEM NET load (load - wind - solar). **Descriptive and IN-SAMPLE**:
    it says which driver the commitment state tracks, never which candidate
    wins. Any out-of-sample claim belongs to the selection probe.
  * **L-3a THE DOMINANT AXIS** is named mechanically: SEASONAL if (i)'s worst-4-
    month concentration >= **0.60**; DIURNAL if (ii)'s worst-8-hour
    concentration >= **0.60**; FRAGMENTATION if ``runlen_ratio <= 0.50``;
    DRIVER if the best alternative ranking in (iv) beats SYSTEM load by >=
    **0.10** absolute correlation. Axes are NOT exclusive — every axis that
    clears its line is named, because a window repair may have to address more
    than one.

===============================================================================
Usage
===============================================================================
    python3 scripts/probes/_miso199_mustrun_window_basis_phase0.py --satisfiability
    python3 scripts/probes/_miso199_mustrun_window_basis_phase0.py

Record: ``results/calibration/_miso199_mustrun_window_basis_phase0.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso198_stgas_oom_conduct_phase0 as ph0  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
GROUP = "ST_GAS"

# THIS session's keeper — the miso-198 helpers are imported verbatim (rule 23)
# and re-pointed at it, so every basis is the frozen one and only the bundle
# under test changes.
KEEPER = _REPO / "results" / "calibration" / "miso198_oom_B"
RUN_ID = "2026-09-01-miso-198-oomlevel"
ph0.KEEPER = KEEPER
ph0.RUN_ID = RUN_ID

OUT = _REPO / "results" / "calibration" / "_miso199_mustrun_window_basis_phase0.json"

# ---- frozen ex-ante lines (the docstring is the authority; these mirror it) --
L1A_INFORMATIVE_LIFT = 1.0
L1B_WELL_PLACED_HIT = 0.80
L2A_DOMINANT_SHARE = 0.45
L2A_MIN_YEARS = 2
L3A_SEASONAL_CONC = 0.60      # worst-4-month share of the symmetric difference
L3A_DIURNAL_CONC = 0.60       # worst-8-hour share
L3A_RUNLEN_RATIO = 0.50       # mean_run(H_floor) / mean_run(H_meas)
L3A_DRIVER_GAIN = 0.10        # absolute point-biserial gain over SYSTEM load
IDENTITY_TOL = 1e-9


# ------------------------------------------------------------------ B3 shapes
def zone_load_shapes(year: int) -> dict[str, np.ndarray]:
    """B3: per-zone P1 demand from the keeper's committed system sidecar."""
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    out: dict[str, np.ndarray] = {}
    for zone, g in df.groupby("zone"):
        arr = np.asarray(
            g.sort_values("hour")["demand"].to_numpy(), dtype=float
        )
        assert arr.shape == (HOURS,), f"{zone} {year}: {arr.shape}"
        out[str(zone)] = arr
    return out


def renewable_shape(year: int) -> np.ndarray:
    """B3: solved wind+solar MW by hour from the committed class sidecar."""
    df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"].isin(["wind", "solar"]))]
    s = df.groupby("hour")["mw"].sum().sort_index()
    arr = np.asarray(s.to_numpy(), dtype=float)
    assert arr.shape == (HOURS,), f"renewables {year}: {arr.shape}"
    return arr


def plant_zones(fleet) -> dict[int, str]:
    """{plant_code: zone} for the floored plants (majority pmax wins)."""
    by: dict[int, dict[str, float]] = {}
    for g in fleet:
        code = int(getattr(g, "plant_code", 0) or 0)
        zone = getattr(g, "zone", None)
        if code <= 0 or not zone:
            continue
        by.setdefault(code, {})
        by[code][str(zone)] = by[code].get(str(zone), 0.0) + float(g.pmax_mw or 0.0)
    return {c: max(d, key=d.get) for c, d in by.items() if d}


# ------------------------------------------------------------------- helpers
def runs(mask: np.ndarray) -> tuple[float, int]:
    """(mean contiguous run length, run count) of a boolean 8760 mask."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return 0.0, 0
    d = np.diff(np.concatenate(([0], m.view(np.int8), [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    lens = ends - starts
    return float(lens.mean()), int(lens.size)


def point_biserial(indicator: np.ndarray, x: np.ndarray) -> float:
    """Correlation of a 0/1 commitment indicator with a continuous driver."""
    a = np.asarray(indicator, dtype=float)
    b = np.asarray(x, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def month_index() -> np.ndarray:
    """Calendar month (1-12) for each of the 8760 hours of a non-leap year."""
    dl = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in dl])


def concentration(counts: np.ndarray, worst: int) -> float:
    """Share of the total carried by the ``worst`` largest bins."""
    tot = float(counts.sum())
    if tot <= 0:
        return 0.0
    return float(np.sort(counts)[::-1][:worst].sum() / tot)


# --------------------------------------------------------------------- census
def census() -> dict:
    """Run N-1..N-3 and return the record."""
    rec: dict = {
        "probe": Path(__file__).name,
        "run_id": RUN_ID,
        "keeper_bundle": str(KEEPER.relative_to(_REPO)),
        "frozen_lines": {
            "L1A_INFORMATIVE_LIFT": L1A_INFORMATIVE_LIFT,
            "L1B_WELL_PLACED_HIT": L1B_WELL_PLACED_HIT,
            "L2A_DOMINANT_SHARE": L2A_DOMINANT_SHARE,
            "L2A_MIN_YEARS": L2A_MIN_YEARS,
            "L3A_SEASONAL_CONC": L3A_SEASONAL_CONC,
            "L3A_DIURNAL_CONC": L3A_DIURNAL_CONC,
            "L3A_RUNLEN_RATIO": L3A_RUNLEN_RATIO,
            "L3A_DRIVER_GAIN": L3A_DRIVER_GAIN,
        },
        "n1": {"rows": []},
        "n2": {"by_year": {}},
        "n3": {},
    }
    mon = month_index()
    hod = np.tile(np.arange(24), 365)

    per_year: dict[int, dict] = {}
    for year in YEARS:
        print(f"  [{year}] building B1 fleet through run_year's own chain …")
        fleet, fa, _cfg = ph0.build_run_year_fleet(year)
        floors = ph0.plant_floor_series(fleet, fa)
        zones = plant_zones(fleet)
        print(f"  [{year}] loading B2 measured CAMPD …")
        net, online = ph0.measured_year(year)
        sysload = ph0.system_load_shape(year)
        per_year[year] = {
            "floors": floors,
            "net": net,
            "online": online,
            "zones": zones,
            "sysload": sysload,
            "zoneload": zone_load_shapes(year),
            "renew": renewable_shape(year),
        }
        print(f"  [{year}] {len(floors)} plant(s) carry the ST_GAS floor")

    # -------------------------------------------------------------------- N-1
    for year in YEARS:
        d = per_year[year]
        for code in sorted(d["floors"]):
            flr = d["floors"][code]
            h_floor = flr > 0.0
            h_meas = d["online"].get(code)
            if h_meas is None:
                h_meas = np.zeros(HOURS, dtype=bool)
            k = int(h_floor.sum())
            m = int(h_meas.sum())
            inter = int((h_floor & h_meas).sum())
            chance = m / HOURS
            hit = inter / k if k else None
            rec["n1"]["rows"].append(
                {
                    "plant_code": code,
                    "year": year,
                    "zone": d["zones"].get(code),
                    "k_floor_hours": k,
                    "m_measured_online_hours": m,
                    "intersection_hours": inter,
                    "hit": round(hit, 4) if hit is not None else None,
                    "cov": round(inter / m, 4) if m else None,
                    "chance": round(chance, 4),
                    "lift": (
                        round(hit / chance, 4)
                        if hit is not None and chance > 0
                        else None
                    ),
                    "floor_twh": round(float(flr.sum()) / 1e6, 4),
                    "L1a_informative": (
                        bool(hit is not None and chance > 0
                             and hit / chance > L1A_INFORMATIVE_LIFT)
                    ),
                    "L1b_well_placed": bool(hit is not None and hit >= L1B_WELL_PLACED_HIT),
                }
            )
    # energy-weighted fleet summary
    n1_sum: dict[int, dict] = {}
    for year in YEARS:
        rows = [r for r in rec["n1"]["rows"] if r["year"] == year]
        w = np.array([r["floor_twh"] for r in rows], dtype=float)
        hits = np.array([r["hit"] or 0.0 for r in rows], dtype=float)
        lifts = np.array([r["lift"] or 0.0 for r in rows], dtype=float)
        n1_sum[year] = {
            "n_floored_plants": len(rows),
            "energy_weighted_hit": round(float((w * hits).sum() / w.sum()), 4)
            if w.sum() > 0 else None,
            "energy_weighted_lift": round(float((w * lifts).sum() / w.sum()), 4)
            if w.sum() > 0 else None,
            "n_informative": sum(1 for r in rows if r["L1a_informative"]),
            "n_well_placed": sum(1 for r in rows if r["L1b_well_placed"]),
        }
    rec["n1"]["summary"] = n1_sum

    # -------------------------------------------------------------------- N-2
    for year in YEARS:
        d = per_year[year]
        O = O_mis = O_lvl = raw = 0.0
        for code, flr in d["floors"].items():
            meas = d["net"].get(code)
            if meas is None:
                meas = np.zeros(HOURS, dtype=float)
            h_meas = d["online"].get(code)
            if h_meas is None:
                h_meas = np.zeros(HOURS, dtype=bool)
            over = np.maximum(0.0, flr - meas)
            over = np.where(flr > 0.0, over, 0.0)
            raw += float(flr.sum())
            O += float(over.sum())
            O_mis += float(over[~h_meas].sum())
            O_lvl += float(over[h_meas].sum())
        resid = abs((O_mis + O_lvl) - O) / O if O > 0 else 0.0
        rec["n2"]["by_year"][year] = {
            "raw_assertion_twh": round(raw / 1e6, 4),
            "O_overassertion_twh": round(O / 1e6, 4),
            "over_share": round(O / raw, 4) if raw > 0 else None,
            "O_mis_misplacement_twh": round(O_mis / 1e6, 4),
            "O_lvl_level_twh": round(O_lvl / 1e6, 4),
            "shares": {
                "MIS": round(O_mis / O, 4) if O > 0 else None,
                "LVL": round(O_lvl / O, 4) if O > 0 else None,
            },
            "identity_residual_rel": round(resid, 12),
            "identity_ok": bool(resid <= IDENTITY_TOL),
        }
    dom = {"MIS": 0, "LVL": 0}
    for year in YEARS:
        sh = rec["n2"]["by_year"][year]["shares"]
        for ch in dom:
            if sh[ch] is not None and sh[ch] >= L2A_DOMINANT_SHARE:
                dom[ch] += 1
    winners = [c for c, n in dom.items() if n >= L2A_MIN_YEARS]
    channel = winners[0] if len(winners) == 1 else None
    rec["n2"]["L2a_dominant_channel"] = channel
    rec["n2"]["L2a_years_over_line"] = dom
    rec["n2"]["L2b_premise_holds"] = bool(channel == "MIS")
    rec["n2"]["L2b_verdict"] = (
        "PREMISE HOLDS — the over-assertion is MISPLACEMENT: the floor binds in "
        "hours the plant's own meter says it was not running (rule 17). The "
        "window basis is the binding defect and the window family proceeds."
        if channel == "MIS"
        else (
            "PREMISE REFUTED — the over-assertion is a LEVEL effect inside "
            "correctly-placed hours. The window family is REFUSED; escalate "
            "WITHOUT SOLVING."
            if channel == "LVL"
            else "DISPERSED — neither channel clears the dominance line; a "
            "window repair alone cannot be justified on this measurement."
        )
    )

    # -------------------------------------------------------------------- N-3
    # (i) seasonal / (ii) diurnal concentration of the symmetric difference,
    # pooled over years and floored plants, floor-MW weighted on the
    # false-positive side (that is the part a window repair can move).
    fp_month = np.zeros(12)
    fn_month = np.zeros(12)
    fp_hod = np.zeros(24)
    fn_hod = np.zeros(24)
    runlen_floor: list[float] = []
    runlen_meas: list[float] = []
    nruns_floor: list[int] = []
    nruns_meas: list[int] = []
    drivers = {"system_load": [], "zone_load": [], "system_net_load": []}
    driver_rows: list[dict] = []
    for year in YEARS:
        d = per_year[year]
        netload = d["sysload"] - d["renew"]
        for code, flr in d["floors"].items():
            h_floor = flr > 0.0
            h_meas = d["online"].get(code)
            if h_meas is None:
                h_meas = np.zeros(HOURS, dtype=bool)
            fp = h_floor & ~h_meas   # floored but not running — misplacement
            fn = h_meas & ~h_floor   # running but not floored — the W channel
            for mth in range(1, 13):
                sel = mon == mth
                fp_month[mth - 1] += float(flr[fp & sel].sum())
                fn_month[mth - 1] += float(sel[fn].sum())
            for h in range(24):
                sel = hod == h
                fp_hod[h] += float(flr[fp & sel].sum())
                fn_hod[h] += float(sel[fn].sum())
            rl_f, nr_f = runs(h_floor)
            rl_m, nr_m = runs(h_meas)
            runlen_floor.append(rl_f)
            runlen_meas.append(rl_m)
            nruns_floor.append(nr_f)
            nruns_meas.append(nr_m)
            zl = d["zoneload"].get(d["zones"].get(code, ""))
            ind = h_meas.astype(float)
            r_sys = point_biserial(ind, d["sysload"])
            r_zone = point_biserial(ind, zl) if zl is not None else float("nan")
            r_net = point_biserial(ind, netload)
            drivers["system_load"].append(r_sys)
            drivers["zone_load"].append(r_zone)
            drivers["system_net_load"].append(r_net)
            driver_rows.append(
                {
                    "plant_code": code,
                    "year": year,
                    "zone": d["zones"].get(code),
                    "r_system_load": round(r_sys, 4) if r_sys == r_sys else None,
                    "r_zone_load": round(r_zone, 4) if r_zone == r_zone else None,
                    "r_system_net_load": round(r_net, 4) if r_net == r_net else None,
                }
            )
    mean_rl_floor = float(np.mean(runlen_floor)) if runlen_floor else 0.0
    mean_rl_meas = float(np.mean(runlen_meas)) if runlen_meas else 0.0
    runlen_ratio = (mean_rl_floor / mean_rl_meas) if mean_rl_meas > 0 else None
    r_means = {
        k: (round(float(np.nanmean(v)), 4) if v else None) for k, v in drivers.items()
    }
    base_r = r_means["system_load"] or 0.0
    alts = {k: v for k, v in r_means.items() if k != "system_load" and v is not None}
    best_alt = max(alts, key=lambda k: alts[k]) if alts else None
    driver_gain = (alts[best_alt] - base_r) if best_alt else 0.0

    seasonal_conc = concentration(fp_month, 4)
    diurnal_conc = concentration(fp_hod, 8)
    axes: list[str] = []
    if seasonal_conc >= L3A_SEASONAL_CONC:
        axes.append("SEASONAL")
    if diurnal_conc >= L3A_DIURNAL_CONC:
        axes.append("DIURNAL")
    if runlen_ratio is not None and runlen_ratio <= L3A_RUNLEN_RATIO:
        axes.append("FRAGMENTATION")
    if driver_gain >= L3A_DRIVER_GAIN:
        axes.append("DRIVER")

    rec["n3"] = {
        "seasonal": {
            "false_positive_floor_mwh_by_month": [round(v, 1) for v in fp_month],
            "false_negative_hours_by_month": [int(v) for v in fn_month],
            "worst4_month_concentration": round(seasonal_conc, 4),
            "clears_line": bool(seasonal_conc >= L3A_SEASONAL_CONC),
        },
        "diurnal": {
            "false_positive_floor_mwh_by_hod": [round(v, 1) for v in fp_hod],
            "false_negative_hours_by_hod": [int(v) for v in fn_hod],
            "worst8_hour_concentration": round(diurnal_conc, 4),
            "clears_line": bool(diurnal_conc >= L3A_DIURNAL_CONC),
        },
        "run_structure": {
            "mean_run_len_floor_h": round(mean_rl_floor, 2),
            "mean_run_len_measured_h": round(mean_rl_meas, 2),
            "mean_runs_floor": round(float(np.mean(nruns_floor)), 1) if nruns_floor else None,
            "mean_runs_measured": round(float(np.mean(nruns_meas)), 1) if nruns_meas else None,
            "runlen_ratio": round(runlen_ratio, 4) if runlen_ratio is not None else None,
            "clears_line": bool(runlen_ratio is not None and runlen_ratio <= L3A_RUNLEN_RATIO),
        },
        "driver": {
            "mean_point_biserial": r_means,
            "best_alternative": best_alt,
            "gain_over_system_load": round(driver_gain, 4),
            "clears_line": bool(driver_gain >= L3A_DRIVER_GAIN),
            "rows": driver_rows,
        },
        "L3a_dominant_axes": axes,
        "L3a_verdict": (
            "AXES: " + ", ".join(axes) if axes
            else "NO AXIS clears its line — the misplacement is structureless on "
                 "every measured axis, and no window basis is indicated."
        ),
    }
    return rec


def satisfiability() -> None:
    """Verify every basis loads and every witness is computable — NO adjudication."""
    print("SATISFIABILITY (no adjudicating quantity computed)")
    cfg = ph0.keeper_config(2024)
    assert cfg.mode == "backcast"
    for f in (
        "st_gas_mustrun_per_plant",
        "st_gas_mustrun_p25_level",
        "st_gas_mustrun_oom_level",
        "mustrun_plant_exclusions",
    ):
        print(f"  keeper {f} = {getattr(cfg, f, None)}")
    assert cfg.st_gas_mustrun_per_plant, "premise: the keeper arms the ST_GAS floor"
    assert getattr(cfg, "st_gas_mustrun_oom_level", False), (
        "premise: THIS keeper is the miso-198 oom-level arm"
    )
    for year in YEARS:
        zl = zone_load_shapes(year)
        rn = renewable_shape(year)
        print(
            f"  B3 {year}: {len(zl)} zone series, renewables mean "
            f"{rn.mean() / 1e3:.2f} GW"
        )
        assert zl, "premise: the system sidecar carries per-zone demand"
    fleet, fa, _ = ph0.build_run_year_fleet(2023)
    floors = ph0.plant_floor_series(fleet, fa)
    tot = sum(float(v.sum()) for v in floors.values()) / 1e6
    print(f"  B1 2023 floored plants {sorted(floors)}; raw assertion {tot:.4f} TWh")
    assert floors, "premise: the ST_GAS floor is present in the B1 fleet"
    # miso-198 §3's byte-faithfulness check, re-asserted on THIS keeper: the
    # arm's own solve logged 9.9319 TWh for 2023 under the oom level.
    assert abs(tot - 9.9319) < 0.01, (
        f"premise: the rebuilt floor matches the keeper's own logged assertion "
        f"(9.9319 TWh); got {tot:.4f} — the load_shape basis is wrong"
    )
    print("  floor matches the keeper's own logged 2023 assertion (9.9319 TWh)")
    zmap = plant_zones(fleet)
    print(f"  zone map covers {len([c for c in floors if c in zmap])}/{len(floors)} floored plants")
    net, online = ph0.measured_year(2023)
    print(f"  B2 CAMPD plants {len(net)}; online masks {len(online)}")
    rl, nr = runs(online[next(iter(floors))] if next(iter(floors)) in online else np.zeros(HOURS, bool))
    print(f"  run-structure helper OK (sample: mean run {rl:.1f} h over {nr} runs)")
    print("SATISFIABLE — every basis loads and every witness is computable.")


def main() -> None:
    ap = argparse.ArgumentParser(description="miso-199 phase-0 window-basis census")
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return
    rec = census()
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(_REPO)}")
    print("\n== N-1 window placement (energy-weighted over floored plants) ==")
    for y in YEARS:
        s = rec["n1"]["summary"][y]
        print(
            f"  {y}: hit {s['energy_weighted_hit']}  lift {s['energy_weighted_lift']}"
            f"  informative {s['n_informative']}/{s['n_floored_plants']}"
            f"  well-placed {s['n_well_placed']}/{s['n_floored_plants']}"
        )
    print("\n== N-2 over-assertion partition ==")
    for y in YEARS:
        r = rec["n2"]["by_year"][y]
        print(
            f"  {y}: raw {r['raw_assertion_twh']:7.3f}  O {r['O_overassertion_twh']:6.3f}"
            f"  ({r['over_share']:.3f})   MIS {r['O_mis_misplacement_twh']:6.3f}"
            f" ({r['shares']['MIS']:.3f})   LVL {r['O_lvl_level_twh']:6.3f}"
            f" ({r['shares']['LVL']:.3f})   resid {r['identity_residual_rel']:.2e}"
        )
    print(f"  L-2a dominant: {rec['n2']['L2a_dominant_channel']}")
    print(f"  L-2b {rec['n2']['L2b_verdict']}")
    print("\n== N-3 structure of the misplacement ==")
    n3 = rec["n3"]
    print(
        f"  seasonal worst-4-month conc {n3['seasonal']['worst4_month_concentration']}"
        f"  diurnal worst-8-hour conc {n3['diurnal']['worst8_hour_concentration']}"
    )
    print(
        f"  run length floor {n3['run_structure']['mean_run_len_floor_h']} h vs "
        f"measured {n3['run_structure']['mean_run_len_measured_h']} h "
        f"(ratio {n3['run_structure']['runlen_ratio']})"
    )
    print(f"  driver correlations {n3['driver']['mean_point_biserial']} "
          f"-> best alt {n3['driver']['best_alternative']} "
          f"gain {n3['driver']['gain_over_system_load']}")
    print(f"  L-3a {n3['L3a_verdict']}")


if __name__ == "__main__":
    main()
