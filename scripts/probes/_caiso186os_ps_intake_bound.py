"""caiso-186 (OWNER SITTING) — the BOUNDED C3a movement of the WALLED hourly
pumped-storage water-state intake, derived from the CURRENT keeper's committed
hourly sidecars.

NO LP, NO SOLVE, NO SOLVER CALL, NO NETWORK. Every number below comes from
bytes already committed to the repository:

* the keeper bundle ``results/calibration/caiso184_c1_lpbasis/hourly/``
  (``system_<y>.parquet``, ``storage_<y>.parquet``) — keeper
  ``2026-08-09-caiso-184-c1-lpbasis``;
* the committed actual hourly RT LMP reference
  ``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``;
* the committed benchmark ``frontend/data/backcast/bench/CAISO/<y>.json.gz``
  (``avgLMP.rt_lw``), used only to CHECK the reproduction.

This is a DECISION INSTRUMENT for owner packet (a): what is the largest C3a
movement the intake could possibly buy, and does that bound reach the band?

Construction, in the order the answers stack. Each leg is an UPPER bound on
the favourable direction, so their composition is an upper bound too.

* **L0 REPRODUCTION** — the C3a statistic is rebuilt from the sidecars and must
  reproduce the keeper's registered +3.7 / +10.5 / +13.1 %. If it does not, no
  later number is trustworthy and the probe says so.
* **L1 THE REQUIRED MOVE** — the ``$/MWh`` fall in the model's load-weighted
  mean price needed to bring each year inside the rubric's ±10 % C3a band.
* **L2 THE SIZE THE INTAKE CAN MOVE** — the intake grounds the model's hourly
  PS water state and nothing else. The most favourable resolution it could
  return is that the whole FINDING-caiso140 §B water wedge is model PS
  OVER-pumping. The model cannot be corrected to pump less than zero, so the
  ceiling on added price-taking CA supply is the model's OWN PS charge, hour by
  hour. L2 measures it: annual, Sep–Dec, and in the caiso-120/121 belly band.
* **L3 THE ENERGY-NEUTRALITY OFFSET** — the leg the caiso-140 §C λ(S) walkdown
  structurally omits. That walkdown priced S MW of *added price-taking supply*,
  i.e. free energy. Pumped storage is not free energy: SOC is cyclic, so
  removing X MWh of pumping obliges removing ~ηX MWh of discharge. L3 measures
  where the model's PS discharge sits in the price distribution and what the
  paired removal is worth at the model's own λ, on the rubric's own weights.
  Sign matters more than magnitude: charge removal pushes LOW-price hours
  lower, discharge removal pushes HIGH-price hours HIGHER.
* **L4 THE ADDRESSABLE SHARE OF THE GAP** — the share of today's C3a gap that
  lives in hours where the model's PS is even active. A correction to the water
  state cannot reach a gap that sits in hours the mechanism does not touch.

The λ(S) → Δλ conversion is NOT re-derived here: FINDING-caiso140 §C is the
committed instrument for it and its curve is quoted as-is, with the staleness
disclosed (it was measured against a SMALLER C3a-2025 gap, so quoting it can
only OVERSTATE the intake's sufficiency — which is conservative for an
insufficiency finding, and disqualifying for a sufficiency one).

Usage::

    uv run python scripts/probes/_caiso186os_ps_intake_bound.py

Writes ``results/calibration/_caiso186os_ps_intake_bound.json``.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760

BUNDLE = REPO / "results/calibration/caiso184_c1_lpbasis"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
OUT = REPO / "results/calibration/_caiso186os_ps_intake_bound.json"

# rubric C3a band, docs/calibration-determination-rubric.md
C3A_BAND = 0.10

# caiso-120/121 belly convention, reused verbatim for composability with
# FINDING-caiso140 §A/§B (do not redefine — rule 28 DO-NOT-REDO)
BELLY_MONTHS = (9, 10, 11, 12)
BELLY_HODS = (10, 11, 12, 13, 14, 15)

# FINDING-caiso140 §C, the committed λ(S) walkdown (2025 defect hours, upper
# bounds by that finding's own statement). S MW of ADDED PRICE-TAKING supply
# in the Sep–Dec belly → annual C3a move in $/MWh.
CAISO140_WALKDOWN_BELLY = {
    500: -0.048,
    1000: -0.157,
    1500: -0.313,
    2000: -0.511,
    3000: -0.731,
}
# the C3a-2025 gap the walkdown was measured against (FINDING-caiso140 §A)
CAISO140_GAP_2025 = 2.904
# FINDING-caiso140 §B: the Sep-Dec belly WATER wedge (model vs measured, both
# sides net of PS), near-constant across the three years. This is the branch-B
# ceiling: if the wedge is entirely CONVENTIONAL-HYDRO under-allocation rather
# than PS over-pumping, the correctable supply is the whole wedge, not just the
# model's own pumping.
CAISO140_WATER_WEDGE_BELLY_MW = {2023: 769.0, 2024: 803.0, 2025: 793.0}


def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT price ($/MWh), NaN where uncovered."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def sidecars(year: int) -> dict:
    """P1 pivots from the keeper's committed hourly sidecars."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    s = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return {
        "price": d.pivot_table(index="hour", columns="zone", values="price"),
        "demand": d.pivot_table(index="hour", columns="zone", values="demand"),
        "chg": s.pivot_table(index="hour", columns="tech", values="charge_mw"),
        "dis": s.pivot_table(index="hour", columns="tech", values="discharge_mw"),
    }


def ca_lambda_and_weight(sc: dict) -> tuple[np.ndarray, np.ndarray]:
    """Hourly CA demand-weighted model λ and its weight — the C3a construction.

    The WECC import nodes carry zero demand and are excluded, exactly as the
    scored statistic does.
    """
    ca = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
    w = sc["demand"][ca].sum(axis=1)
    lam = (sc["price"][ca] * sc["demand"][ca]).sum(axis=1) / w
    return lam.to_numpy(), w.to_numpy()


def rubric_weights(year: int) -> np.ndarray:
    """The rubric's rt_lw weights: measured system load (eia_loader).

    Reused verbatim from ``_caiso140_belly_supply_state.py`` so the L4
    decomposition composes with FINDING-caiso140 §A (rule 28 DO-NOT-REDO).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def bench_rt_lw(year: int) -> float:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return float(json.load(fh)["bench"]["avgLMP"]["rt_lw"])


def month_of_hour(year: int) -> np.ndarray:
    """Month (1–12) per hour-of-year on the non-leap 8760 calendar."""
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def interp_walkdown(s_mw: float) -> float:
    """Linear interpolation of the committed caiso-140 §C belly λ(S) curve.

    The curve is CONVEX in S (|Δλ| grows faster than S over the measured
    range), so linear interpolation between bracketing knots OVERSTATES the
    magnitude at interior points — conservative for an insufficiency finding.
    """
    ks = sorted(CAISO140_WALKDOWN_BELLY)
    if s_mw <= ks[0]:
        return CAISO140_WALKDOWN_BELLY[ks[0]] * s_mw / ks[0]
    for lo, hi in zip(ks, ks[1:]):
        if s_mw <= hi:
            f = (s_mw - lo) / (hi - lo)
            return CAISO140_WALKDOWN_BELLY[lo] + f * (
                CAISO140_WALKDOWN_BELLY[hi] - CAISO140_WALKDOWN_BELLY[lo]
            )
    return CAISO140_WALKDOWN_BELLY[ks[-1]]


def main() -> None:
    out: dict = {
        "probe": "_caiso186os_ps_intake_bound",
        "session": "caiso-186 owner sitting (dispatched label; see handoff §0 on the "
        "session-number collision with the landed caiso-186 seasonal-capability session)",
        "keeper": "2026-08-09-caiso-184-c1-lpbasis",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "lp_solved": False,
        "network": False,
        "years": {},
    }

    print("=" * 78)
    print(
        "caiso-186 owner sitting — BOUNDED C3a movement of the walled PS water-state intake"
    )
    print("keeper 2026-08-09-caiso-184-c1-lpbasis · committed sidecars only · NO LP")
    print("=" * 78)

    for year in YEARS:
        sc = sidecars(year)
        lam, w = ca_lambda_and_weight(sc)
        chg = sc["chg"]["pumped_storage"].reindex(range(HOURS)).to_numpy()
        dis = sc["dis"]["pumped_storage"].reindex(range(HOURS)).to_numpy()
        bat_chg = sc["chg"]["li_ion"].reindex(range(HOURS)).to_numpy()
        act = actual_rt(year)
        mon = month_of_hour(year)
        hod = np.arange(HOURS) % 24

        # ---- L0 reproduction of the scored C3a statistic --------------------
        model_lw = float((lam * w).sum() / w.sum())
        ref = bench_rt_lw(year)
        pct = 100.0 * (model_lw / ref - 1.0)

        # ---- L1 the required move ------------------------------------------
        band_top = ref * (1.0 + C3A_BAND)
        required = float(model_lw - band_top)  # $/MWh the model must SHED
        required = max(required, 0.0)

        # ---- L2 the size the intake can move -------------------------------
        belly = np.isin(mon, BELLY_MONTHS) & np.isin(hod, BELLY_HODS)
        sepdec = np.isin(mon, BELLY_MONTHS)
        pumping = chg > 0.0

        l2 = {
            "annual_mean_charge_mw": float(chg.mean()),
            "annual_mean_discharge_mw": float(dis.mean()),
            "implied_rte": float(dis.sum() / chg.sum()) if chg.sum() else None,
            "sepdec_mean_charge_mw": float(chg[sepdec].mean()),
            "belly_mean_charge_mw": float(chg[belly].mean()),
            "belly_mean_charge_over_pumping_hours_mw": (
                float(chg[belly & pumping].mean()) if (belly & pumping).any() else 0.0
            ),
            "belly_hours": int(belly.sum()),
            "belly_pumping_hours": int((belly & pumping).sum()),
            "annual_pumping_hours": int(pumping.sum()),
            "fleet_mw_eia860": 2077.6,
        }

        # ---- L3 the energy-neutrality offset --------------------------------
        # Where does PS sit in the price distribution? Charge hours are the
        # hours the intake would relieve; discharge hours are the hours the
        # paired removal would tighten.
        chg_w = chg  # MW of load the correction could remove, per hour
        dis_w = dis  # MW of supply the correction is OBLIGED to remove
        lam_chg = (
            float((lam * chg_w).sum() / chg_w.sum()) if chg_w.sum() else float("nan")
        )
        lam_dis = (
            float((lam * dis_w).sum() / dis_w.sum()) if dis_w.sum() else float("nan")
        )
        act_ok = ~np.isnan(act)
        a_chg = (
            float((act[act_ok] * chg_w[act_ok]).sum() / chg_w[act_ok].sum())
            if chg_w[act_ok].sum()
            else float("nan")
        )
        a_dis = (
            float((act[act_ok] * dis_w[act_ok]).sum() / dis_w[act_ok].sum())
            if dis_w[act_ok].sum()
            else float("nan")
        )
        # rubric-weight mass sitting on each side
        l3 = {
            "ps_charge_mwh": float(chg.sum()),
            "ps_discharge_mwh": float(dis.sum()),
            "model_lambda_at_ps_charge": lam_chg,
            "model_lambda_at_ps_discharge": lam_dis,
            "actual_rt_at_ps_charge": a_chg,
            "actual_rt_at_ps_discharge": a_dis,
            "model_spread_dis_minus_chg": lam_dis - lam_chg,
            "note": (
                "SOC is cyclic: removing X MWh of pumping obliges removing ~eta*X MWh "
                "of discharge. The charge-side relief lands on LOW-price hours; the "
                "obliged discharge-side removal lands on HIGH-price hours and pushes "
                "them UP. The caiso-140 walkdown priced only the charge side."
            ),
        }

        # ---- L4 the addressable share of the gap ----------------------------
        # gap contribution on the RUBRIC's rt_lw weights (measured system load),
        # applied to BOTH sides — the caiso-131 §2 / caiso-140 §A common-weight
        # convention, under which the cells sum exactly to the printed gap.
        ok = act_ok
        rw = rubric_weights(year)
        contrib = np.where(ok, rw * (lam - np.nan_to_num(act)), 0.0)
        denom = rw[ok].sum()
        total_gap = float(contrib.sum() / denom)
        share = lambda m: float(contrib[m & ok].sum() / denom)  # noqa: E731
        l4 = {
            "weights": "rubric rt_lw (measured system load), common to both sides",
            "gap_reconstructed_hourly": total_gap,
            "gap_from_annual_means": float(model_lw - ref),
            "gap_in_ps_pumping_hours": share(pumping),
            "gap_in_ps_discharge_hours": share(dis > 0.0),
            "gap_in_belly": share(belly),
            "gap_in_sepdec": share(sepdec),
            "gap_in_no_ps_activity_hours": share((chg <= 0.0) & (dis <= 0.0)),
            "coverage_hours_actual": int(ok.sum()),
        }

        # ---- the composed bound ---------------------------------------------
        # Branch A ceiling: the whole wedge is model PS OVER-pumping, so the
        # correctable supply is the model's OWN belly pumping (it cannot pump
        # less than zero). Branch B ceiling: the whole wedge is CONVENTIONAL-
        # HYDRO under-allocation, so the correctable supply is the whole
        # measured wedge. The bound takes the LARGER of the two — the most
        # favourable resolution the intake could possibly return.
        s_a = l2["belly_mean_charge_mw"]
        s_b = float(CAISO140_WATER_WEDGE_BELLY_MW[year])
        s_belly = max(s_a, s_b)
        dlam_upper = interp_walkdown(s_belly)
        bound = {
            "S_branchA_model_ps_belly_pumping_mw": s_a,
            "S_branchB_caiso140_water_wedge_mw": s_b,
            "S_belly_mw_max": s_belly,
            "walkdown_dlambda_upper_usd_per_mwh": dlam_upper,
            "required_usd_per_mwh": required,
            "closes_band": bool(abs(dlam_upper) >= required) if required > 0 else True,
            "coverage_of_required_pct": (
                float(100.0 * abs(dlam_upper) / required) if required > 0 else None
            ),
            "walkdown_staleness_note": (
                f"the caiso-140 §C curve was measured against a C3a-2025 gap of "
                f"{CAISO140_GAP_2025:+.3f} $/MWh; this keeper's gap is "
                f"{model_lw - ref:+.3f} $/MWh, so the quoted curve OVERSTATES the "
                f"intake's sufficiency."
            ),
        }

        out["years"][str(year)] = {
            "L0": {
                "model_lw_usd_per_mwh": model_lw,
                "bench_rt_lw_usd_per_mwh": ref,
                "c3a_pct": pct,
                "gap_usd_per_mwh": model_lw - ref,
            },
            "L1_required_move_usd_per_mwh": required,
            "L2_size": l2,
            "L3_energy_neutrality": l3,
            "L4_addressable": l4,
            "bound": bound,
            "context_battery_mean_charge_mw": float(bat_chg.mean()),
        }

        print(f"\n--- {year} " + "-" * 62)
        print(
            f"L0  model lw {model_lw:8.3f}  ref {ref:7.2f}  C3a {pct:+6.2f} %"
            f"   gap {model_lw - ref:+7.3f} $/MWh"
        )
        print(
            f"L1  required fall to reach the +10 % band: {required:7.3f} $/MWh"
            f"   ({'FAIL' if required > 0 else 'PASS'})"
        )
        print(
            f"L2  model PS: annual chg {l2['annual_mean_charge_mw']:7.1f} MW  "
            f"dis {l2['annual_mean_discharge_mw']:7.1f} MW  RTE {l2['implied_rte']:.3f}"
        )
        print(
            f"    Sep-Dec chg {l2['sepdec_mean_charge_mw']:7.1f} MW   "
            f"BELLY chg {l2['belly_mean_charge_mw']:7.1f} MW "
            f"({l2['belly_pumping_hours']}/{l2['belly_hours']} h pumping)"
        )
        print(
            f"L3  model λ at PS charge {lam_chg:7.3f}  at PS discharge {lam_dis:7.3f}"
            f"   spread {lam_dis - lam_chg:+7.3f}"
        )
        print(f"    actual RT at PS charge {a_chg:7.3f}  at PS discharge {a_dis:7.3f}")
        print(
            f"L4  gap {total_gap:+7.3f} total | in PS-pumping h {l4['gap_in_ps_pumping_hours']:+7.3f}"
            f" | in belly {l4['gap_in_belly']:+7.3f} | no-PS-activity h "
            f"{l4['gap_in_no_ps_activity_hours']:+7.3f}"
        )
        print(
            f"BND S=max(A {s_a:6.1f}, B {s_b:6.1f})={s_belly:6.1f} MW -> "
            f"caiso-140 λ(S) upper bound {dlam_upper:+7.3f} $/MWh"
            f"  vs required {required:7.3f}  -> "
            f"{'CLOSES' if bound['closes_band'] else 'DOES NOT CLOSE'}"
            + (
                f" ({bound['coverage_of_required_pct']:.1f} % of it)"
                if bound["coverage_of_required_pct"] is not None
                else ""
            )
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
