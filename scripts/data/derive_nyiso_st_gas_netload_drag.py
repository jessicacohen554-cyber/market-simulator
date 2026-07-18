#!/usr/bin/env python
"""Derive the NYISO ST_GAS net-load-driven reliability-commitment drag.

NYISO's downstate steam fleet (ST_GAS — Ravenswood/Astoria-area NYC boilers plus
the Long Island Northport / E.F. Barrett / Port Jefferson steamers) runs a
genuine persistent 24h reliability base: measured CAMPD overnight CF 0.11-0.17
with the NYC/LI plants online 100 % of the year (G-05 adjudication,
``docs/handoffs/g05-forced-energy-caiso-ct-nyiso-stgas-2026-07.md``). The
nyiso-56 keeper carries that base as fixed ``reliability_floor`` limbs
(``reliability_floor_coeffs_NYISO.csv``: NYC persistent 0.391, LI 0.289 —
flat all-day fractions plus a hard HB14-21 evening step), which is why its C8
ST_GAS forced share (30/45/38 %) scores "above cap, NOT grounded — no declared
D-4 window" under rubric v2.2.

G-05 rejected switching the class onto ``gas_st_netload_drag`` when that drag
was windowed [15,22) — a window that would under-commit the measured overnight
base. Since then the drag became ALL-HOURS (``fleet.apply_gas_st_netload_drag_
floor``, ``ramp_window=None``; ERCOT-46 / PJM-94 keepers), i.e. exactly a
persistent base whose LEVEL flexes with system net-load instead of sitting at a
fixed calendar fraction. That removes the G-05 objection: the all-hours drag
can carry a 24/7 base and is the class's grounded mechanism (declared
``D4_WINDOWS`` (MECH_ST_NETLOAD_DRAG, None) = (0, 24) with the CAMPD
never-fully-off evidence base).

This derives NYISO's OWN hinge — the ERCOT/PJM-fitted curves must not cross ISO
boundaries (CLAUDE.md rule 25) — with the same measured-operating-rule
construction as ``derive_pjm_st_gas_netload_drag.py`` (rule 23; re-derives only
when CAMPD/EIA-930 source data update):

  1. NYISO hourly net-load = EIA-930 ``NYIS`` Demand − solar − wind on the
     model's naive local-standard 8760 clock (UTC−5, EST, no DST) — the same
     net-load convention ``fleet.apply_gas_st_netload_drag_floor`` consumes.
  2. Regress the measured OVERNIGHT (23-05h local, the low-price hours where
     ST_GAS output is held commitment, not merit dispatch) fleet capacity
     factor on contemporaneous net-load. CF = CAMPD gross × (1 − ST_GAS
     station-service 5%) ÷ the model ST_GAS pure-play nameplate.
  3. Hinge fit ``clip(slope·netGW + intercept, 0, cap)`` — the exact functional
     form ``apply_gas_st_netload_drag_floor`` applies (all-hours; the printed
     diurnal blocks are the honesty check that the commitment really is
     around-the-clock, and the per-zone table checks the NYC/LI persistent-base
     signature against the part-year Capital_Hudson tail).

Both the trigger (net-load) and the magnitude (a physical min-gen commitment
level) regenerate for a forward year and respond to changed conditions, so the
mechanism is admissible in backcast AND forecast (CLAUDE.md rules 13/17) —
window (all-hours, net-load-hinged), driver (DARU/SRE-style downstate
reliability commitment, measured operating rule), forward story (net-load from
load forecast + VRE build). Zero parameters fitted to a price or volume
residual.

Run with no arguments to re-derive from the committed CAMPD + EIA-930 archives;
the per-year Spearman rho and per-block tables are the honesty gates (usable
only if monotonic and year-stable). Apply via ``gas_st_netload_drag=True`` +
``gas_st_drag_overrides={...}`` in a run driver (the pjm-94 pattern); enabling
the drag auto-drops the reliability-floor ST_GAS limbs
(``iso_configs.drop_drag_owned_reliability_specs``, rule 19 — no stacking).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

from scripts.data.derive_pjm_ct_netload_drag import (  # noqa: E402
    HOURS,
    _binned_median,
    _hoy_from_date_hour,
)
from scripts.data.derive_pjm_st_gas_netload_drag import (  # noqa: E402
    OVERNIGHT_END_H,
    OVERNIGHT_START_H,
    _PURE_PLAY_ST_SHARE,
    _ST_NET_OF_GROSS,
)

_NYIS_HOURLY: Path = RAW_DIR / "eia-930-hourly" / "NYIS hourly.parquet"
# NYISO model dispatch clock is local STANDARD time: EST = UTC - 5, no DST
# (same convention as the PJM derive and the runner's 8760 grid).
_UTC_TO_LST_HOURS = 5


def nyiso_net_load_mw(year: int) -> np.ndarray:
    """NYISO hourly net-load = EIA-930 NYIS Demand − solar − wind (MW, 8760).

    Same construction as ``derive_pjm_ct_netload_drag.pjm_net_load_mw``: the
    EIA-930 ``UTC time`` stamps shift by a fixed −5 h to local standard time
    (EST, no DST) and lay onto the model's non-leap 8760-hour grid, so the CF
    and the net-load it is regressed on are time-aligned.
    """
    df = pd.read_parquet(_NYIS_HOURLY)
    utc = pd.to_datetime(df["UTC time"])
    lst = utc - pd.Timedelta(hours=_UTC_TO_LST_HOURS)
    mask = lst.dt.year == year
    df = df[mask].reset_index(drop=True)
    lst = lst[mask].reset_index(drop=True)
    hoy = _hoy_from_date_hour(lst.dt.normalize(), lst.dt.hour)
    ok = (hoy >= 0) & (hoy < HOURS)
    dem = pd.to_numeric(df["Demand"], errors="coerce").to_numpy()[ok]
    sun = pd.to_numeric(df.get("NG: SUN"), errors="coerce").to_numpy()[ok]
    wnd = pd.to_numeric(df.get("NG: WND"), errors="coerce").to_numpy()[ok]
    out = np.full(HOURS, np.nan)
    out[hoy[ok]] = dem - np.nan_to_num(sun) - np.nan_to_num(wnd)
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def model_st_gas_plants(year: int) -> tuple[dict[int, float], float, dict[int, str]]:
    """Return the model's pure-play NYISO ST_GAS plants, nameplate, and zones.

    Same construction as the PJM derive: plant_group == "ST_GAS" (the fleet
    builder's own classing, so the CF denominator matches the class the floor
    multiplies onto), restricted to plants ≥ 90 % ST_GAS by model capacity so
    the plant-summed CAMPD series measures gas-steam units only.
    """
    cfg = get_iso_config("NYISO")
    gens = load_fleet_from_csv("NYISO", cfg, year=year)
    plant_cap: dict[int, float] = {}
    st_cap: dict[int, float] = {}
    zone: dict[int, str] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "ST_GAS":
            st_cap[pc] = st_cap.get(pc, 0.0) + float(g.pmax_mw)
            zone[pc] = str(g.zone)
    plants = {
        pc: cap
        for pc, cap in st_cap.items()
        if cap / plant_cap[pc] >= _PURE_PLAY_ST_SHARE
    }
    return plants, float(sum(plants.values())), zone


def measured_st_gas_mw(
    year: int, plant_codes: set[int]
) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """Measured NYISO ST_GAS net MW per hour (8760), fleet total + per plant."""
    states = campd.states_for_iso("NYISO")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _ST_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    per_plant: dict[int, np.ndarray] = {}
    for pid, series in net.items():
        if pid in plant_codes:
            arr = np.zeros(HOURS)
            arr[: series.shape[0]] = series[:HOURS]
            per_plant[pid] = arr
            fleet += arr
    return fleet, per_plant


def main() -> None:
    """CLI entry: re-derive and print the NYISO ST_GAS net-load drag coefficients."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    overnight = (hod >= OVERNIGHT_START_H) | (hod < OVERNIGHT_END_H)

    onl, ocf = [], []
    per_year = {}
    for year in years:
        plants, nameplate, zones = model_st_gas_plants(year)
        mw, per_plant = measured_st_gas_mw(year, set(plants))
        nl = nyiso_net_load_mw(year)
        cf = mw / nameplate
        rho_on = pd.Series(nl[overnight]).corr(
            pd.Series(cf[overnight]), method="spearman"
        )
        rho_all = pd.Series(nl).corr(pd.Series(cf), method="spearman")
        print(
            f"\n=== {year}: {len(plants)} pure-play ST_GAS plants, nameplate "
            f"{nameplate / 1000:.2f} GW, measured {mw.sum() / 1e6:.2f} TWh "
            f"(CF {mw.mean() / nameplate:.3f}); Spearman(netload,CF) "
            f"overnight rho={rho_on:.2f}, all-hours rho={rho_all:.2f} ==="
        )
        # Per-zone persistent-base honesty table (the G-05 signature): the
        # NYC/LI base should show high online share and a non-zero overnight
        # CF; a part-year zone (Capital_Hudson) dilutes the pooled fit and is
        # printed so the dilution is visible, not hidden.
        by_zone: dict[str, list[int]] = {}
        for pid in plants:
            by_zone.setdefault(zones.get(pid, "?"), []).append(pid)
        for zn, pids in sorted(by_zone.items()):
            zcap = sum(plants[p] for p in pids)
            zmw = np.sum([per_plant.get(p, np.zeros(HOURS)) for p in pids], axis=0)
            zcf = zmw / max(zcap, 1e-9)
            daily_on = zmw.reshape(365, 24).max(axis=1) > 0.01 * zcap
            print(
                f"  zone {zn:<15} {zcap:7.0f} MW  overnight CF "
                f"{float(zcf[overnight].mean()):.3f}  all-hours CF "
                f"{float(zcf.mean()):.3f}  online {daily_on.mean():.0%} of days"
            )
        # Diurnal-block honesty check: the ALL-HOURS application is only right
        # if the commitment really is around-the-clock (flat blocks), unlike
        # the CT drag's evening-ramp concentration.
        edges5 = np.arange(8, 33, 2)
        for label, mask in [
            ("overnight 23-05", overnight),
            ("morning 06-09", (hod >= 6) & (hod < 10)),
            ("midday 10-14", (hod >= 10) & (hod < 15)),
            ("ramp 15-21", (hod >= 15) & (hod < 22)),
            ("late 22", hod == 22),
        ]:
            rows = _binned_median(nl[mask] / 1000.0, cf[mask], edges5)
            s = "  ".join(f"{int(c)}:{m:.3f}" for c, m in rows)
            print(f"  {label:<16} CFbyNL(GW)  {s}")
        onl.append(nl[overnight] / 1000.0)
        ocf.append(cf[overnight])
        per_year[year] = (mw, nl, nameplate)

    # Pooled hinge fit on the overnight block (the pure held-commitment
    # signature), same estimator as the PJM ST_GAS drag: grid-search the hinge
    # knee over the bin centers, least-squares on the bins at/above the knee,
    # keep the (knee, slope, intercept) minimizing SSE of the CLIPPED
    # prediction over ALL bins. No scipy.optimize (forbidden).
    onl_all = np.concatenate(onl)
    ocf_all = np.concatenate(ocf)
    # NYISO net-load spans ~9-30 GW (vs PJM's 40-145): 1-GW bins.
    edges = np.arange(8, 33, 1)
    binned = _binned_median(onl_all, ocf_all, edges)
    cap = float(np.percentile(ocf_all, 95))

    best = None
    for knee_i in range(len(binned) - 3):  # >= 4 bins in the active segment
        seg = binned[knee_i:]
        s, b = np.polyfit(seg[:, 0], seg[:, 1], 1)
        if s <= 0.0:
            continue
        pred = np.clip(s * binned[:, 0] + b, 0.0, cap)
        sse = float(((pred - binned[:, 1]) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, float(s), float(b))
    sse_hinge, slope, intercept = best

    s_lin, b_lin = np.polyfit(binned[:, 0], binned[:, 1], 1)
    pred_lin = np.clip(s_lin * binned[:, 0] + b_lin, 0.0, cap)
    sse_lin = float(((pred_lin - binned[:, 1]) ** 2).sum())

    print("\n=== POOLED overnight fit (median per 1-GW bin) ===")
    print("Binned CF vs net-load (GW: median CF):")
    print("  " + "  ".join(f"{c:.1f}:{m:.3f}" for c, m in binned))
    print(
        f"unclipped-line fit: slope {s_lin:.5f}, intercept {b_lin:+.4f}, "
        f"SSE(clipped pred) {sse_lin:.4f}"
    )
    print(f"hinge fit (functional form of the applied floor): SSE {sse_hinge:.4f}")
    coeffs = {
        "gas_st_drag_slope_per_gw": round(float(slope), 5),
        "gas_st_drag_intercept": round(float(intercept), 4),
        "gas_st_drag_cap": round(cap, 2),
        "zero_crossing_gw": round(float(-intercept / slope), 1),
    }
    print(json.dumps(coeffs, indent=2))

    # Energy cross-check: the ALL-HOURS floor energy at the fitted curve should
    # sit at or below the measured class total (a minimum the LP exceeds
    # economically), never overshoot it.
    print("\nPer-year floor energy vs measured (all hours):")
    for year, (mw, nl, nameplate) in per_year.items():
        frac = np.clip(slope * nl / 1000.0 + intercept, 0.0, cap)
        floor_twh = float((frac * nameplate).sum() / 1e6)
        meas_twh = float(mw.sum() / 1e6)
        print(
            f"  {year}: floor {floor_twh:.2f} TWh vs measured {meas_twh:.2f} TWh "
            f"({floor_twh / max(meas_twh, 1e-9):.0%} of measured)"
        )


if __name__ == "__main__":
    main()
