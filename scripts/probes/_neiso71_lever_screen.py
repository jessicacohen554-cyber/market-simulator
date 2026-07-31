"""neiso-71 PRE-SOLVE lever screen — Lever A block + Lever B fidelity.

Run BEFORE any solve. Produces the two pre-registration facts that decided
this session's arm (``results/calibration/PREREG-neiso71-nuclear-availability-2026-07-31.md``):

* **Lever A — ``measured_chp_heat_rates`` companion host-steam floor
  (matrix §5.6 item 6): MEASUREMENT-BLOCKED.** The committed WP-3 statistic
  (``steam_level_cf``, ``scripts/data/derive_thermal_tranches.py``) run on
  NEISO's OWN CAMPD returns **146.1 %** of nameplate for Kendall Square
  (EIA 1595) — 42 % of the CC_CHP class — because CAMPD unit "4"
  (unitType "Combined cycle") meters 278-299 MW median against an EIA-860
  CHP nameplate of 213.4 MW (206.0 summer), saturating the derivation's 1.5
  available-CF clip guard in 50-75 % of online hours. Armed, that level
  floors Kendall at 195.6 MW against a 206.0 MW pmax — 95 % of capacity
  forced flat year-round, ~1.71 TWh/yr — which would MORE than close
  neiso-70's 0.34-0.68 TWh CC_CHP shortfall. That is a fitted parameter
  (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``), so the lever stops here.
  The other two CAMPD-visible CC_CHP plants measure 2.2 % / 3.6 % — the
  statistic self-targeting genuine cyclers (5-7 % on-frequency), i.e. NEISO's
  merchant cogens really do carry no host-steam obligation. Non-Kendall
  CC_CHP floor total: 15.0 MW.
* **Lever B — ``nuclear_unit_availability`` flag fidelity: LIVE.** The
  ERCOT-146 hazard (a flag that never reaches the ISO's fleet, stamped ``I``
  with no solve spent) is discharged here: all three NEISO reactors match the
  derived extract by ``(plant_code, unit_no)`` with 100 % date coverage.

No LP, no bundle, no scoring — screens only. Years 2023-2025 (rule 22).

Usage::

    PYTHONPATH=src python3 scripts/probes/_neiso71_lever_screen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)
TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_NEISO.csv"

# The 1.5 available-CF clip in derive_thermal_tranches.main (guard against
# multi-unit CEMS noise). A level at/above it is saturated, not measured.
ACF_CLIP = 1.5


def lever_a_chp_steam_level() -> None:
    """Screen the WP-3 host-steam level for NEISO's CC_CHP class."""
    from market_sim.data import campd
    from market_sim.data.fleet import CHP_BTM_PCT_BY_SECTOR
    from market_sim.data.outages import unit_outage_derate_factors

    import data.derive_thermal_tranches as dt  # scripts/data on sys.path

    print("=" * 78)
    print("LEVER A — CC_CHP host-steam floor (matrix §5.6 item 6)")
    print("=" * 78)

    old = pd.read_csv(TRANCHES)
    print(f"committed artifact columns: {list(old.columns)}")
    print(
        "  -> pre-WP-3 vintage: no `steam_level_cf` AND no `p25_allhr_cf`, so "
        "`chp_steam_floor_p25` is INERT for NEISO today "
        "(fleet.campd_bins.thermal_tranche_chp_steam_level returns {})."
    )
    cc = old[old.plant_group == "CC_CHP"]
    print(
        f"  committed chp_pmin_cf for the 3 CAMPD-visible CC_CHP plants: "
        f"{list(cc[cc.status == 'ok'].chp_pmin_cf)} — the p2-of-all-hours "
        "statistic FINDING-caiso95 §5 showed mixes offline zeros into the level."
    )

    states = campd.states_for_iso("NEISO")
    factors = dt._parasitic_factor_map()
    cap, primary = dt._fleet_nameplate_and_group("NEISO")
    sect = dict(zip(old.plant_code, old.chp_sector))

    print("\nper-plant re-derivation on NEISO's own CAMPD (2023-2025 pooled):")
    for code, group in sorted(k for k in cap if k[1] == "CC_CHP"):
        if primary.get(code) != group:
            continue
        nameplate = cap[(code, group)]
        on_cat, all_cat = [], []
        for year in YEARS:
            df = campd.load_campd_hourly(states, [year])
            if df.empty:
                continue
            net = campd.plant_hourly_net(df, factors, year)
            series = net.get(code)
            if series is None:
                continue
            derate = unit_outage_derate_factors(year, iso="NEISO")
            avail_cap = nameplate * derate.get((code, group), np.ones(len(series)))
            with np.errstate(divide="ignore", invalid="ignore"):
                acf = np.where(avail_cap > 0.0, series / avail_cap, 0.0)
            acf = np.clip(acf, 0.0, ACF_CLIP)
            finite = np.isfinite(acf) & (avail_cap > 0.0)
            online = finite & (series > dt._ONLINE_FRAC * avail_cap)
            on_cat.append(acf[online])
            all_cat.append(acf[finite])
        if not all_cat:
            continue
        on_cat = np.concatenate(on_cat)
        all_cat = np.concatenate(all_cat)
        if not len(on_cat):
            continue
        on_freq = len(on_cat) / len(all_cat)
        level = 100.0 * on_freq * float(np.percentile(on_cat, 50))
        sat = float(np.mean(on_cat >= ACF_CLIP - 1e-9))
        btm = CHP_BTM_PCT_BY_SECTOR.get(
            sect.get(code) or "merchant", CHP_BTM_PCT_BY_SECTOR["merchant"]
        )
        floor = level / 100.0 * nameplate * (1.0 - btm / 100.0)
        flag = "  <== SATURATED, NOT MEASURED" if sat > 0.25 else ""
        print(
            f"  {code:6d} {group}  nameplate={nameplate:7.1f} MW  "
            f"on_freq={on_freq:.3f}  steam_level_cf={level:6.1f}%  "
            f"clip_frac={sat:.3f}  -> floor {floor:7.1f} MW "
            f"({100 * floor / nameplate:5.1f}% of pmax){flag}"
        )

    print(
        "\nVERDICT: BLOCKED. Any capacity-factor floor for Kendall inherits the "
        "same broken denominator (EIA-923 CF divides by the same nameplate), so "
        "no admissible NEISO measurement of the obligation exists until the "
        "plant's capacity basis is fixed — its own lane, and it sits in the "
        "miso-95 provenance-orphaned `nameplate_mw` column."
    )


def lever_b_flag_fidelity() -> None:
    """Discharge the ERCOT-146 hazard for ``nuclear_unit_availability``."""
    from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR
    from market_sim.data.fleet import load_fleet_from_csv
    from market_sim.data.outages import nuclear_unit_availability_series

    print("\n" + "=" * 78)
    print("LEVER B — nuclear_unit_availability flag fidelity + liveness")
    print("=" * 78)

    gens = load_fleet_from_csv(iso="NEISO")
    mo_of_hour = np.repeat(
        np.arange(12), [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    )
    for year in YEARS:
        daily = nuclear_unit_availability_series("NEISO", year)
        anchor = np.array(NUCLEAR_MONTHLY_CF_BY_YEAR["NEISO"][year], dtype=float)
        smear = np.zeros(8760)
        arm = np.zeros(8760)
        matched = []
        for gen in gens:
            if gen.fuel_type != "nuclear":
                continue
            tail = str(gen.unit_id).rsplit("_", 1)[-1]
            if not tail.isdigit():
                continue
            series = daily.get((int(gen.plant_code), int(tail)))
            if series is None:
                continue
            pmax = float(gen.pmax_mw)
            sm = anchor[mo_of_hour] * pmax
            smear += sm
            arm += np.where(np.isnan(series), anchor[mo_of_hour], series) * pmax
            matched.append((gen.unit_id, gen.zone, pmax, float(np.isfinite(series).mean())))
        delta = arm - smear
        print(
            f"  {year}: {len(matched)} reactor(s) matched, "
            f"{sum(m[2] for m in matched):.1f} MW | "
            f"max|Δ|={np.abs(delta).max():7.1f} MW  mean|Δ|={np.abs(delta).mean():6.1f} MW  "
            f"energy Δ={delta.sum() / 1e6:+.4f} TWh"
        )
        for uid, zone, pmax, cov in matched:
            print(f"        {uid:8s} {zone:12s} {pmax:8.2f} MW  date coverage={cov:.3f}")

    print(
        "\nVERDICT: LIVE. Energy is anchor-neutral by construction (the EIA-923 "
        "anchor owns the LEVEL, NRC owns the TIMING); the whole delta is "
        "per-reactor timing and its Connecticut/North zonal split."
    )


def main() -> int:
    lever_a_chp_steam_level()
    lever_b_flag_fidelity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
