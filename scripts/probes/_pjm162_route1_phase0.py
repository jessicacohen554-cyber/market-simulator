"""pjm-162 Phase 0: is pjm-145 route (1) correctly SIGNED before it is built?

WHY THIS PROBE EXISTS. pjm-161 refuted route (3) (`pjm_measured_outage_event
_cap`, remove-only, TOTAL basis) on its own pre-registered predictions and named
route (1) — "restore ceiling composed with the structural-derate registry (port
the ercot137 fix)" — as the successor selected by measurement. Route (1) is the
`pjm_dam_availability` water-fill (matrix `G`, pjm-145) with an ercot137-style
per-unit ceiling added so a restore can never resurrect a unit the finer
measured record holds at zero.

The ceiling repairs pjm-145's REFUSAL GROUND (ii) — structural-zero
resurrection, 66-68 % of the restore lift. It says NOTHING about whether the
water-fill's target is correctly signed in the hours the defect lives in. That
is what this probe measures, BEFORE any flag is written and before any solve.

THE PREREGISTERED PREREQUISITE (session prompt): "the model's envelope carries
NO planned/forced split, which is why neither the total nor the forced basis
works as a comparison basis. Decide whether route (1) needs that split first."

The test that decides it, stated so it can fail:

  A bidirectional water-fill fixes a SHAPE defect only if its target moves the
  envelope the RIGHT WAY in the hours the shape is wrong. pjm-161 measured the
  defect: the CAMPD envelope is anti-correlated with net load (r = -0.68..-0.77)
  and asserts too LITTLE outage in scarcity. So on high-net-load days route (1)
  must REMOVE (target below model). If instead it RESTORES on those days, the
  mechanism is ANTI-TARGETED — it would deepen the very inversion it is built to
  repair — and the planned/forced split is a hard prerequisite, not an option.

Measured here, per year x per candidate target basis (`total` = forced +
maintenance + planned; `unplanned` = the shipped PJM_OUTAGE_DEFAULT_TYPES):

  1. DIRECTION BY NET-LOAD RANK — the restore/remove split and the signed MW the
     water-fill would move, on all covered days, the top-10 %, the top-1 % of
     net-load days, and the named winter-event window. This is the decisive row.
  2. LEVEL ON THOSE DAYS — model fossil-thermal outage MW vs PJM's published
     total AND published forced, so the direction result is attributable.
  3. CEILING CONTENT — the pjm-145 SS5 decomposition (structural-zero
     resurrection vs living-unit lift) recomputed on this envelope, and what an
     ercot137-style structural ceiling removes from it, so route (1)'s repair of
     ground (ii) is a number rather than a claim.

No LP: `fleet_only=True` exits before the matrix builder. Nothing is solved,
scored or registered; every year is in-training (2023-2025).

Run:  PYTHONPATH=. uv run python scripts/probes/_pjm162_route1_phase0.py
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/pjm152_collapse_A"
OUT_PATH = REPO / "results/calibration/_pjm162_route1_phase0.json"
E930 = REPO / "data" / "raw" / "eia-930-hourly" / "PJM hourly.parquet"
YEARS = (2023, 2024, 2025)

ALL_TYPES = ("forced", "maintenance", "planned")
UNPLANNED = ("forced", "maintenance")

#: Named PJM winter stress events (same windows as _pjm161_outage_inversion.py,
#: so the two probes' event rows are directly comparable).
EVENTS = {
    2023: ("2023-02-03", "2023-02-04", "Feb cold snap"),
    2024: ("2024-01-15", "2024-01-17", "Heather"),
    2025: ("2025-01-21", "2025-01-23", "Enzo"),
}


def _run_year_kwargs(meta: dict) -> dict:
    """Map the keeper meta onto ``run_calibration.run_year``'s signature.

    The same lossy-but-logged reconstruction ``_pjm161_removeonly_exante`` used,
    so this probe's fleet build is the keeper's fleet build.
    """
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs, dropped = {}, []
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    print(f"[map] {len(kwargs)} kwargs bound; dropped: {len(dropped)}")
    return kwargs


def net_load_by_day(year: int, n_days: int) -> np.ndarray:
    """Return (n_days,) daily-MAX net load (demand - wind - solar) from EIA-930.

    Daily MAX rather than mean: the water-fill's grain is the DAY, and a day's
    scarcity exposure is set by its peak hour, not its average.
    """
    d = pd.read_parquet(E930)
    d = d[pd.to_datetime(d["Local date"]).dt.year == year].copy()
    d["lt"] = pd.to_datetime(d["Local time"])
    d = d.set_index("lt").sort_index()
    dem = pd.to_numeric(d["Demand"], errors="coerce")
    vre = pd.to_numeric(d["NG: WND"], errors="coerce").fillna(0) + pd.to_numeric(
        d["NG: SUN"], errors="coerce"
    ).fillna(0)
    nl = (dem - vre).dropna()
    # Model clock is non-leap; drop Feb 29 so day indices align with the arrays.
    nl = nl[~((nl.index.month == 2) & (nl.index.day == 29))]
    daily = nl.resample("D").max()
    out = np.full(n_days, np.nan)
    out[: min(n_days, len(daily))] = daily.to_numpy()[:n_days]
    return out


def event_day_mask(year: int, n_days: int) -> np.ndarray:
    """Boolean (n_days,) mask of the named winter-event days for ``year``."""
    mask = np.zeros(n_days, dtype=bool)
    if year not in EVENTS:
        return mask
    s, e, _ = EVENTS[year]
    days = pd.date_range(f"{year}-01-01", periods=n_days, freq="D")
    days = days[~((days.month == 2) & (days.day == 29))][:n_days]
    sel = (days >= pd.Timestamp(s)) & (days <= pd.Timestamp(e))
    mask[: len(sel)] = sel[:n_days]
    return mask


def main() -> None:
    from market_sim.data.pjm_outages import (
        PJM_OUTAGE_COVERED_GROUPS,
        pjm_dam_availability_series,
        pjm_outage_mw_series,
    )
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    base_kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})

    result: dict = {"years": {}, "_meta": {"keeper": str(KEEPER.name), "years": YEARS}}

    for yr in YEARS:
        gas = float(gas_prices.get(str(yr), gas_prices.get(yr, 0.0)))
        state = run_year(yr, "PJM", 8760, gas, {}, fleet_only=True, **base_kwargs)
        fa = state["fleet_arrays"]
        groups = np.array([str(g) for g in fa.plant_group])
        pmax = np.asarray(fa.pmax, dtype=float)
        av = np.asarray(fa.availability, dtype=float)
        n_days = av.shape[1] // 24

        nl = net_load_by_day(yr, n_days)
        ev = event_day_mask(yr, n_days)
        finite_nl = np.isfinite(nl)
        rank = np.full(n_days, np.nan)
        rank[finite_nl] = pd.Series(nl[finite_nl]).rank(pct=True).to_numpy()
        top10 = finite_nl & (rank >= 0.90)
        top1 = finite_nl & (rank >= 0.99)

        # ---- model-side outage MW on the covered (fossil-thermal) classes ----
        cov_mask = np.isin(groups, sorted(PJM_OUTAGE_COVERED_GROUPS))
        ad_all = av[:, : n_days * 24].reshape(av.shape[0], n_days, 24).mean(axis=2)
        model_out_cov = ((1.0 - ad_all) * pmax[:, None])[cov_mask].sum(axis=0)

        pub_tot = pjm_outage_mw_series(yr, 8760, "PJM RTO", ALL_TYPES)
        pub_frc = pjm_outage_mw_series(yr, 8760, "PJM RTO", ("forced",))
        pub_tot_d = pub_tot[: n_days * 24].reshape(n_days, 24).mean(axis=1)
        pub_frc_d = pub_frc[: n_days * 24].reshape(n_days, 24).mean(axis=1)

        yr_out: dict = {"n_days": int(n_days)}

        def _slice_stats(m: np.ndarray) -> dict:
            fin = m & np.isfinite(pub_tot_d)
            if not fin.any():
                return {}
            return {
                "days": int(fin.sum()),
                "model_fossil_out_MW": float(model_out_cov[fin].mean()),
                "published_total_MW": float(pub_tot_d[fin].mean()),
                "published_forced_MW": float(pub_frc_d[fin].mean()),
            }

        yr_out["level"] = {
            "all": _slice_stats(np.ones(n_days, dtype=bool)),
            "top10pct_netload": _slice_stats(top10),
            "top1pct_netload": _slice_stats(top1),
            "event_window": _slice_stats(ev),
        }

        # ---- direction of the bidirectional water-fill, by net-load rank ----
        for basis, types in (("total", ALL_TYPES), ("unplanned", UNPLANNED)):
            meas = pjm_dam_availability_series(yr, outage_types=types)
            # Signed MW the water-fill would move, summed over covered classes.
            # + = RESTORE (target says MORE available than the model asserts)
            # - = REMOVE  (target says LESS available -> deepens the envelope)
            signed = np.zeros(n_days)
            restore_d = np.zeros(n_days, dtype=bool)
            remove_d = np.zeros(n_days, dtype=bool)
            covered_any = np.zeros(n_days, dtype=bool)
            for cls in sorted(PJM_OUTAGE_COVERED_GROUPS):
                idx = np.flatnonzero(groups == cls)
                if idx.size == 0 or cls not in meas:
                    continue
                cap = pmax[idx]
                cap_sum = float(cap.sum())
                if cap_sum <= 0:
                    continue
                ad = av[idx, : n_days * 24].reshape(idx.size, n_days, 24).mean(axis=2)
                cur = (ad * cap[:, None]).sum(axis=0) / cap_sum
                t = meas[cls][: n_days * 24].reshape(n_days, 24).mean(axis=1)
                cov = np.isfinite(t)
                covered_any |= cov
                signed += np.where(cov, (t - cur) * cap_sum, 0.0)
                restore_d |= cov & (t >= cur)
                remove_d |= cov & (t < cur)

            def _dir(m: np.ndarray) -> dict:
                fin = m & covered_any
                if not fin.any():
                    return {}
                return {
                    "days": int(fin.sum()),
                    "restore_days": int((restore_d & fin).sum()),
                    "remove_days": int((remove_d & fin).sum()),
                    "signed_MW_mean": float(signed[fin].mean()),
                    "verdict": "RESTORE" if signed[fin].mean() > 0 else "REMOVE",
                }

            yr_out.setdefault("direction", {})[basis] = {
                "all": _dir(np.ones(n_days, dtype=bool)),
                "top10pct_netload": _dir(top10),
                "top1pct_netload": _dir(top1),
                "event_window": _dir(ev),
            }

        # ---- ceiling content: pjm-145 SS5 decomposition on THIS envelope ----
        # Structural-zero resurrection = day-mean availability ~0 lifted by the
        # water-fill's `_flat` branch. An ercot137-style structural ceiling
        # (cap the restore at the unit's own pre-overlay envelope) sets the
        # ceiling to 0 for exactly these unit-days, so the lift they carry is
        # what route (1)'s repair removes.
        meas_tot = pjm_dam_availability_series(yr, outage_types=ALL_TYPES)
        zero_lift = 0.0
        live_lift = 0.0
        for cls in sorted(PJM_OUTAGE_COVERED_GROUPS):
            idx = np.flatnonzero(groups == cls)
            if idx.size == 0 or cls not in meas_tot:
                continue
            cap = pmax[idx]
            cap_sum = float(cap.sum())
            if cap_sum <= 0:
                continue
            ad = av[idx, : n_days * 24].reshape(idx.size, n_days, 24).mean(axis=2)
            cur = (ad * cap[:, None]).sum(axis=0) / cap_sum
            t = meas_tot[cls][: n_days * 24].reshape(n_days, 24).mean(axis=1)
            res = np.isfinite(t) & (t >= cur)
            if not res.any():
                continue
            lam = np.clip((t - cur) / np.maximum(1.0 - cur, 1e-9), 0.0, 1.0)
            lift = lam[None, :] * (1.0 - ad) * cap[:, None]  # (n, days) MW
            isz = ad <= 1e-9
            zero_lift += float(lift[:, res][isz[:, res]].sum()) / max(int(res.sum()), 1)
            zl = lift[:, res].copy()
            zl[isz[:, res]] = 0.0
            live_lift += float(zl.sum()) / max(int(res.sum()), 1)
        tot_lift = zero_lift + live_lift
        yr_out["ceiling_content"] = {
            "restore_day_zero_lift_MW": zero_lift,
            "restore_day_live_lift_MW": live_lift,
            "zero_share": (zero_lift / tot_lift) if tot_lift > 0 else None,
        }

        # ---- attribution: what KIND of outage MW does the envelope assert? ----
        # A family rebasis rescales an outage DEPTH, so it can only act on
        # capacity that is partially derated. A unit-day held at hard zero
        # (layup window, retiree CEMS cap, COD mask, a full outage window) has
        # no depth to rescale and is exactly what the ercot137 structural
        # ceiling must refuse to revive. Splitting the asserted MW into the two
        # tells the successor session how much of the envelope is reachable.
        ad_cov = ad_all[cov_mask]
        cap_cov = pmax[cov_mask]
        hard_zero = ad_cov <= 1e-9
        mw_zero = float((hard_zero * cap_cov[:, None]).sum(axis=0).mean())
        mw_partial = float(
            ((1.0 - ad_cov) * (~hard_zero) * cap_cov[:, None]).sum(axis=0).mean()
        )
        # NOT MEASURED HERE, and stated so rather than approximated: PJM's
        # published record is WHOLE-FLEET, so any non-fossil forced MW inside it
        # is charged to the fossil classes (pjm-145's rule-14 misalignment
        # ground / route-(1) re-open condition 2). The obvious proxy — the
        # model's own asserted NON-fossil unavailability — is NOT a measure of
        # it, because wind/solar "1 - availability" is capacity FACTOR, not
        # outage, and swamps the dispatchable non-fossil outage by an order of
        # magnitude. That contamination therefore remains pjm-145's open ground,
        # unquantified. It does not affect this probe's verdict: the direction
        # result below is driven by the CAPACITY BASE gap (hard_zero_share),
        # which is measured, and which is the larger term.
        fin_p = np.isfinite(pub_frc_d)
        yr_out["attribution"] = {
            "fossil_cap_MW": float(cap_cov.sum()),
            "model_fossil_out_MW_mean": float(model_out_cov.mean()),
            "model_fossil_out_frac_of_fossil_cap": float(
                model_out_cov.mean() / max(float(cap_cov.sum()), 1.0)
            ),
            "model_fossil_out_HARD_ZERO_MW_mean": mw_zero,
            "model_fossil_out_PARTIAL_MW_mean": mw_partial,
            "hard_zero_share_of_asserted_outage": mw_zero
            / max(mw_zero + mw_partial, 1e-9),
            "hard_zero_frac_of_fossil_cap": mw_zero / max(float(cap_cov.sum()), 1.0),
            "published_total_MW_mean": float(pub_tot_d[fin_p].mean()),
            "published_forced_MW_mean": float(pub_frc_d[fin_p].mean()),
        }

        result["years"][str(yr)] = yr_out
        print(f"[{yr}] fleet built: {av.shape[0]} units, {n_days} days")

    OUT_PATH.write_text(json.dumps(result, indent=2))

    # ------------------------------- report -------------------------------
    print()
    print("=" * 100)
    print("pjm-162 PHASE 0 — is route (1) correctly SIGNED in scarcity? (no LP)")
    print("=" * 100)
    print()
    print("LEVEL — model fossil-thermal outage MW vs PJM's published record")
    print(f"{'year':>6} {'slice':>18} {'days':>5} {'model MW':>10} {'pub TOTAL':>10} {'pub FORCED':>11}")
    for yr in YEARS:
        for slc, v in result["years"][str(yr)]["level"].items():
            if not v:
                continue
            print(
                f"{yr:>6} {slc:>18} {v['days']:>5} {v['model_fossil_out_MW']:>10,.0f} "
                f"{v['published_total_MW']:>10,.0f} {v['published_forced_MW']:>11,.0f}"
            )
    print()
    print("DIRECTION — signed MW the bidirectional water-fill would move")
    print("  (+ = RESTORE = gives capacity BACK; - = REMOVE = deepens the envelope)")
    print(f"{'year':>6} {'basis':>10} {'slice':>18} {'days':>5} {'res d':>6} {'rem d':>6} {'signed MW':>11} {'verdict':>8}")
    for yr in YEARS:
        for basis, blk in result["years"][str(yr)]["direction"].items():
            for slc, v in blk.items():
                if not v:
                    continue
                print(
                    f"{yr:>6} {basis:>10} {slc:>18} {v['days']:>5} "
                    f"{v['restore_days']:>6} {v['remove_days']:>6} "
                    f"{v['signed_MW_mean']:>11,.0f} {v['verdict']:>8}"
                )
    print()
    print("CEILING CONTENT — what an ercot137 structural ceiling removes (pjm-145 SS5)")
    print(f"{'year':>6} {'zero-lift MW':>13} {'live-lift MW':>13} {'zero share':>11}")
    for yr in YEARS:
        v = result["years"][str(yr)]["ceiling_content"]
        zs = v["zero_share"]
        print(
            f"{yr:>6} {v['restore_day_zero_lift_MW']:>13,.0f} "
            f"{v['restore_day_live_lift_MW']:>13,.0f} "
            f"{(f'{zs:.1%}' if zs is not None else '-'):>11}"
        )
    print()
    print("ATTRIBUTION — the CAPACITY-BASE gap, which is what sets the direction")
    print(
        f"{'year':>6} {'fossil cap':>11} {'fossil out':>11} {'as % cap':>9} "
        f"{'hard-zero':>10} {'% of cap':>9} {'partial':>9} {'pub TOTAL':>10}"
    )
    for yr in YEARS:
        v = result["years"][str(yr)]["attribution"]
        print(
            f"{yr:>6} {v['fossil_cap_MW']:>11,.0f} "
            f"{v['model_fossil_out_MW_mean']:>11,.0f} "
            f"{v['model_fossil_out_frac_of_fossil_cap']:>8.1%} "
            f"{v['model_fossil_out_HARD_ZERO_MW_mean']:>10,.0f} "
            f"{v['hard_zero_frac_of_fossil_cap']:>8.1%} "
            f"{v['model_fossil_out_PARTIAL_MW_mean']:>9,.0f} "
            f"{v['published_total_MW_mean']:>10,.0f}"
        )
    print()
    print(f"written: {OUT_PATH}")


if __name__ == "__main__":
    main()
