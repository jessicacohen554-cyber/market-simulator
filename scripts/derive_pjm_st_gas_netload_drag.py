#!/usr/bin/env python
"""Derive the PJM ST_GAS net-load-driven reliability-commitment drag (#1483).

PJM's legacy gas-steam boilers (ST_GAS — dominated by the Marcellus-belt
coal-to-gas conversions Brunner Island / Montour / Martins Creek / Shawville /
New Castle plus Chalk Point) run far more energy than a pure-efficiency merit
order clears for them: measured CAMPD gross generation for the model's ST_GAS
plant set is ~12-16 TWh/yr while the SRMC-grounded keeper clears 3.4-5.8 TWh
(issue #1483, ``docs/calibration-log.md`` 2026-07-06 / gap-register G-21). The
measured signature (this script prints it) is NOT an RMR story — the RMR/202(c)
steamers Wagner 3-4 and Eddystone 3-4 carry only ~0.1-0.2 TWh/yr each — and NOT
a load-pocket story: the volume carriers sit in the export-heavy Central-PA
Marcellus belt. It is the same phenomenon the ERCOT keeper's ST_GAS drag models
(``docs/ercot-st-gas-netload-drag-2026-06.md``): boilers committed in multi-day
blocks when system net-load is high (RUC-style reliability commitment; NREL
gas-steam min-run 24-48 h), then held online at part load through the low-price
overnight trough rather than cycling — flat diurnal profile, strongly seasonal.
The hourly energy-only LP, free to de-commit each hour, never sees it.

This derives PJM's OWN curve — the ERCOT-fitted hinge must not cross ISO
boundaries (CLAUDE.md rule 25) — with the same measured-operating-rule
construction (rule 23; re-derives only when CAMPD/EIA-930 source data update):

  1. PJM hourly net-load = EIA-930 ``PJM`` Demand − solar − wind on the model's
     naive local-standard 8760 clock (UTC−5, EST, no DST) — the same net-load
     convention ``fleet.apply_gas_st_netload_drag_floor`` consumes.
  2. Regress the measured OVERNIGHT (23-05h local, the low-price hours where
     ST_GAS generation is non-economic hour-by-hour, so any output is held
     commitment, not merit dispatch — the ERCOT ST_GAS recipe) fleet capacity
     factor on contemporaneous net-load. CF = CAMPD gross × (1 − ST_GAS
     station-service 5%) ÷ the model ST_GAS pure-play nameplate, so the fitted
     fraction reproduces the measured MW when multiplied back onto the model
     fleet's available capacity.
  3. Hinge fit ``clip(slope·netGW + intercept, 0, cap)`` — the exact functional
     form ``apply_gas_st_netload_drag_floor`` applies (all-hours; the boiler
     drag has no ramp window — the printed diurnal blocks are the honesty
     check that the commitment really is around-the-clock).

Both the trigger (net-load) and the magnitude (a physical min-gen commitment
level) regenerate for a forward year and respond to changed conditions, so the
mechanism is admissible in backcast AND forecast (CLAUDE.md rules 13/17) —
window (all-hours, net-load-hinged), driver (RUC reliability commitment,
measured operating rule), forward story (net-load from load forecast + VRE
build). Zero parameters fitted to a price or volume residual.

Run with no arguments to re-derive from the committed CAMPD + EIA-930 archives;
the per-year Spearman rho and per-block tables are the honesty gates (usable
only if monotonic and year-stable). Apply via ``gas_st_netload_drag=True`` +
``gas_st_drag_overrides={...}`` in a run driver (the pjm-75 CT pattern).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

from scripts.derive_pjm_ct_netload_drag import (  # noqa: E402
    HOURS,
    _binned_median,
    pjm_net_load_mw,
)

# Overnight local hours isolating the pure reliability drag (the ERCOT ST_GAS
# derivation window, docs/ercot-st-gas-netload-drag-2026-06.md): prices sit
# below the boiler's min-gen MC there, so measured output is held commitment.
# Half-open wrap-around block [23, 24) ∪ [0, 6).
OVERNIGHT_END_H = 6
OVERNIGHT_START_H = 23

# Same pure-play gate as the CT derive script: CAMPD extracts are plant-summed
# by ORIS code, so a mixed site would contribute non-ST_GAS units' generation
# to the class signature. The fitted fraction then applies to the whole class.
_PURE_PLAY_ST_SHARE = 0.90

# CAMPD reports gross; the model dispatches net. Gas-steam station service is
# ~5% (campd.DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"] = 0.050).
_ST_NET_OF_GROSS = 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]


def model_st_gas_plants(year: int) -> tuple[dict[int, float], float]:
    """Return the model's pure-play PJM ST_GAS plants + class nameplate (MW).

    Same construction as ``derive_pjm_ct_netload_drag.model_ct_peaker_plants``:
    plant_group == "ST_GAS" (the fleet builder's own classing, so the CF
    denominator matches the class the floor multiplies onto — and matches the
    EIA-923 C1 benchmark classing), restricted to plants ≥ 90% ST_GAS by model
    capacity so the plant-summed CAMPD series measures gas-steam units only.
    """
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    plant_cap: dict[int, float] = {}
    st_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "ST_GAS":
            st_cap[pc] = st_cap.get(pc, 0.0) + float(g.pmax_mw)
    plants = {
        pc: cap
        for pc, cap in st_cap.items()
        if cap / plant_cap[pc] >= _PURE_PLAY_ST_SHARE
    }
    return plants, float(sum(plants.values()))


def measured_st_gas_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    """Measured PJM ST_GAS fleet net MW per hour (8760), from CAMPD CEMS."""
    states = campd.states_for_iso("PJM")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _ST_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plant_codes:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet


def main() -> None:
    """CLI entry: re-derive and print the PJM ST_GAS net-load drag coefficients."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    overnight = (hod >= OVERNIGHT_START_H) | (hod < OVERNIGHT_END_H)

    onl, ocf = [], []
    per_year = {}
    for year in years:
        plants, nameplate = model_st_gas_plants(year)
        mw = measured_st_gas_mw(year, set(plants))
        nl = pjm_net_load_mw(year)
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
        # Diurnal-block honesty check: the ALL-HOURS application is only right
        # if the commitment really is around-the-clock (flat blocks), unlike
        # the CT drag's evening-ramp concentration.
        edges5 = np.arange(40, 145, 10)
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
    # signature), same estimator as the PJM CT drag: grid-search the hinge knee
    # over the 2-GW bin centers, least-squares on the bins at/above the knee,
    # keep the (knee, slope, intercept) minimizing SSE of the CLIPPED
    # prediction over ALL bins. No scipy.optimize (forbidden).
    onl_all = np.concatenate(onl)
    ocf_all = np.concatenate(ocf)
    edges = np.arange(40, 145, 2)
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

    print("\n=== POOLED overnight fit (median per 2-GW bin) ===")
    print("Binned CF vs net-load (GW: median CF):")
    print("  " + "  ".join(f"{c:.0f}:{m:.3f}" for c, m in binned))
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
