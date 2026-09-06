"""miso-229 phase 0 — does MISO's CT_PEAKER reliability DRIVER exist at all? Zero LP.

miso-228 established the CT_PEAKER root cause: the class is OFFER-limited, the
LP already dispatches everything in merit (8.752 TWh dispatched vs 7.158 in
merit, 0.020 TWh of in-merit headroom), and the real fleet's 17.0 TWh is not
energy-merit-driven — real MISO cleared $10-20 in 1,765 hours of 2023 while its
CTs ran. It also killed the obvious lever: ``ct_mustrun_per_plant`` pins each
plant to its **observed EIA-923 net generation**, which is rule 13
``[R-MEASURED]``'s named forbidden case and is already **D-9 QUARANTINED**
(``scripts/legitimacy_diagnostics.py``, machine-asserted False).

The code names the admissible successor itself: ``ct_netload_drag`` /
``apply_ct_netload_drag_floor``, *"the forward-native replacement for the
``ct_mustrun_per_plant`` actuals pin"* — a min-gen floor
``clip(slope*netGW + intercept, 0, cap)`` gated to the afternoon-evening ramp
window, whose TRIGGER (net load) and MAGNITUDE (a physical min-gen) both
regenerate for a forward year and respond to changed conditions. It is the
ERCOT and PJM keeper mechanism; MISO's matrix cell reads **U** (untested), so
there is no rule-28 DO-NOT-REDO bar.

**But the mechanism's defaults are ERCOT-fitted, and rule 25 ``[R-ISO-SCOPE]``
forbids carrying another ISO's curve.** Before MISO derives its own, rule 17
``[R-FLOOR-WINDOW]`` demands the DRIVER be shown to exist: a floor needs (a) an
external driver, (b) the hours it may bind and why, (c) a forward story. ERCOT's
and CAISO's driver is solar collapse producing a sharp evening net-load ramp.
**MISO in 2023-2025 carries far less solar, so the driver may simply not be
there** — and if the ramp-window relationship is absent, flat or
year-unstable, the lever is REFUSED at phase 0 and no LP is ever spent.

This probe answers exactly that, porting ``derive_pjm_ct_netload_drag.py``'s
construction to MISO byte-for-byte in method and changing only the ISO and its
clock:

  1. Pure-play CT_PEAKER plants from the MODEL fleet (>= 90 % of the plant's
     model capacity is CT_PEAKER), so the plant-summed CAMPD series measures CT
     units only and the CF numerator and denominator sit on the same units.
  2. Measured CT MW from CAMPD hourly gross over those plants, netted by the
     simple-cycle parasitic factor.
  3. MISO hourly net load = EIA-930 ``MISO`` Demand − solar − wind on the
     model's naive local-standard clock (**CST = UTC − 6**, no DST — MISO's
     model clock, not PJM's EST).
  4. Per-time-block CF tables, and Spearman rho of ramp-window CF on net load
     **per year**. The honesty checks are the PJM script's own: the fit is
     usable only if the relationship is monotonic AND year-stable.

**It fits nothing and licenses nothing.** No curve is committed, no field is
flipped, no derive is frozen — this only says whether a MISO derive is worth
writing. Zero LP. Rule 22: 2023-2025 only. Writes ``_miso229_ct_drag_driver.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

OUT = REPO / "results/calibration/_miso229_ct_drag_driver.json"
HOURS = 8760
YEARS = (2023, 2024, 2025)
#: MISO model dispatch clock is local STANDARD time: CST = UTC - 6, no DST.
_UTC_TO_LST_HOURS = 6
_MISO_HOURLY = RAW_DIR / "eia-930-hourly" / "MISO hourly.parquet"
#: Identical to the PJM/ERCOT derives — carried, not re-chosen.
CT_EVENING_HOURS = (15, 22)
_PURE_PLAY_CT_SHARE = 0.90
_CT_NET_OF_GROSS = 0.99
_MONTH_START_HOUR = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]


def _hoy(date: pd.Series, hour: pd.Series) -> np.ndarray:
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR)[m - 1]
    idx = base + (d - 1) * 24 + h
    return np.where((m == 2) & (d == 29), -1, idx)


def model_ct_plants(year: int) -> tuple[dict[int, float], float, float]:
    """Pure-play MISO CT_PEAKER plants, their nameplate, and the class total."""
    cfg = get_iso_config("MISO")
    gens = load_fleet_from_csv("MISO", cfg, year=year)
    plant_cap: dict[int, float] = {}
    ct_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "CT_PEAKER":
            ct_cap[pc] = ct_cap.get(pc, 0.0) + float(g.pmax_mw)
    pure = {
        pc: cap for pc, cap in ct_cap.items()
        if cap / plant_cap[pc] >= _PURE_PLAY_CT_SHARE
    }
    return pure, float(sum(pure.values())), float(sum(ct_cap.values()))


def measured_ct_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    states = campd.states_for_iso("MISO")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _CT_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plant_codes:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet


def miso_net_load_mw(year: int) -> np.ndarray:
    df = pd.read_parquet(_MISO_HOURLY)
    utc = pd.to_datetime(df["UTC time"])
    lst = utc - pd.Timedelta(hours=_UTC_TO_LST_HOURS)
    mask = lst.dt.year == year
    df = df[mask].reset_index(drop=True)
    lst = lst[mask].reset_index(drop=True)
    hoy = _hoy(lst.dt.normalize(), lst.dt.hour)
    ok = (hoy >= 0) & (hoy < HOURS)
    dem = pd.to_numeric(df["Demand"], errors="coerce").to_numpy()[ok]
    sun = pd.to_numeric(df.get("NG: SUN"), errors="coerce").to_numpy()[ok]
    wnd = pd.to_numeric(df.get("NG: WND"), errors="coerce").to_numpy()[ok]
    out = np.full(HOURS, np.nan)
    out[hoy[ok]] = dem - np.nan_to_num(sun) - np.nan_to_num(wnd)
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def analyse(year: int) -> dict:
    plants, pure_mw, class_mw = model_ct_plants(year)
    ct = measured_ct_mw(year, set(plants))
    nl = miso_net_load_mw(year) / 1000.0            # GW
    cf = ct / max(pure_mw, 1e-9)
    hod = np.arange(HOURS) % 24
    ev = (hod >= CT_EVENING_HOURS[0]) & (hod < CT_EVENING_HOURS[1])
    night = (hod < 6) | (hod >= 22)

    blocks = {}
    for lbl, m in (
        ("overnight_22_06", night),
        ("morning_06_11", (hod >= 6) & (hod < 11)),
        ("midday_11_15", (hod >= 11) & (hod < 15)),
        ("evening_15_22", ev),
    ):
        blocks[lbl] = {
            "mean_cf": round(float(cf[m].mean()), 4),
            "p95_cf": round(float(np.percentile(cf[m], 95)), 4),
            "spearman_cf_vs_netload": round(_spearman(nl[m], cf[m]), 3),
        }

    edges = np.percentile(nl[ev], np.arange(0, 101, 10))
    binned = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = (nl[ev] >= lo) & (nl[ev] < hi)
        if int(s.sum()) >= 30:
            binned.append(
                {
                    "netload_gw_mid": round(0.5 * (lo + hi), 2),
                    "n": int(s.sum()),
                    "median_cf": round(float(np.median(cf[ev][s])), 4),
                }
            )
    return {
        "year": year,
        "n_pure_play_plants": len(plants),
        "pure_play_nameplate_mw": round(pure_mw, 0),
        "class_nameplate_mw": round(class_mw, 0),
        "pure_play_share_of_class": round(pure_mw / max(class_mw, 1e-9), 3),
        "measured_ct_twh_pure_play": round(float(ct.sum()) / 1e6, 3),
        "netload_gw_mean": round(float(nl.mean()), 2),
        "netload_gw_p95": round(float(np.percentile(nl, 95)), 2),
        "by_time_block": blocks,
        "evening_cf_vs_netload_deciles": binned,
        "evening_spearman": blocks["evening_15_22"]["spearman_cf_vs_netload"],
    }


def main() -> int:
    rec = {
        "probe": (
            "miso-229 phase 0 — does MISO's CT_PEAKER net-load reliability DRIVER "
            "exist? (rule 17 [R-FLOOR-WINDOW] gate, zero LP, fits nothing)"
        ),
        "method": "port of scripts/data/derive_pjm_ct_netload_drag.py to MISO (CST clock)",
        "ct_mustrun_per_plant": (
            "REFUSED at miso-228: pins each plant to its observed EIA-923 net "
            "generation (rule 13's named forbidden case) and is D-9 QUARANTINED"
        ),
        "by_year": {},
    }
    for y in YEARS:
        r = analyse(y)
        rec["by_year"][str(y)] = r
        b = r["by_time_block"]
        print(
            f"{y}: pure-play {r['n_pure_play_plants']} plants / "
            f"{r['pure_play_nameplate_mw']:.0f} MW ({r['pure_play_share_of_class']:.2f} of class) "
            f"| measured {r['measured_ct_twh_pure_play']:.3f} TWh"
        )
        for k, v in b.items():
            print(f"     {k:<16} meanCF {v['mean_cf']:.4f}  p95 {v['p95_cf']:.4f}  "
                  f"rho(CF,netload) {v['spearman_cf_vs_netload']:+.3f}")
    rhos = [rec["by_year"][str(y)]["evening_spearman"] for y in YEARS]
    rec["evening_spearman_by_year"] = rhos
    rec["driver_verdict"] = (
        "PRESENT and year-stable" if min(rhos) >= 0.45
        else ("WEAK / unstable — a MISO derive is not justified on this evidence"
              if min(rhos) >= 0.2 else "ABSENT — rule 17 refuses the floor")
    )
    print("\nevening Spearman by year:", rhos, "->", rec["driver_verdict"])
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
