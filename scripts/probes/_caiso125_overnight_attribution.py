"""caiso-125 derive-first probe: attribute the overnight hydro over-supply (no solve).

Both caiso-124 arms run hydro 150-310 MW above the measured EIA-930 ``NG: WAT``
level in the overnight hours (arm A hod 0, 2025: 3354 vs 3044 MW) — a
pre-existing defect the min-flow floor cannot touch (FINDING-caiso124 §5). This
probe measures, from the two committed caiso-124 bundles and raw EIA-930 alone,
which of the three caiso-125 candidate drivers carries the defect:

(i)   the p95 (month x hod) hydro ceiling is mis-bucketed overnight — measured
      by the ceiling's overnight binding share and headroom, and by where the
      model's overnight dispatch sits inside the measured per-bucket
      distribution (its mean percentile rank);
(ii)  a missing water-value / opportunity-cost term on hydro discharge —
      adjudicated structurally: with the monthly energy budget BINDING, a
      constant per-MWh discharge adder shifts the LP objective by
      ``adder x budget`` and cannot re-allocate within the month, and where the
      budget is slack it *declines* water starting with the lowest-lambda
      (belly) hours — the measured section is the per-month budget utilisation
      and the lambda ordering by window;
(iii) the overnight surplus is not hydro's — the model's overnight class stack
      vs the measured EIA-930 stack shows which class's deviation offsets the
      hydro excess (the caiso-111 attribution form, pointed overnight).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso125_overnight_attribution.py \
        --control results/calibration/caiso124_control_A \
        --arm results/calibration/caiso124_minflow_B
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
WINDOWS: dict[str, range] = {
    "overnight": range(0, 7),  # hod 0-6, the caiso-125 target window
    "morning": range(7, 9),
    "belly": range(9, 16),  # hod 9-15, the caiso-124 floor window
    "shoulder": range(16, 17),
    "evening": range(17, 22),  # hod 17-21, the net-load peak
    "late": range(22, 24),
}
# Fraction of the hourly ceiling at which a fleet-hour counts as binding.
CEIL_BIND_FRAC = 0.995
# Months whose model energy consumes at least this share of the measured
# monthly budget count as budget-BOUND for the adder-inertness argument.
BUDGET_BIND_FRAC = 0.995

# Model dispatch classes summed as "gas" in the stack attribution.
GAS_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS")


def hydro_hourly(bundle: Path, year: int) -> np.ndarray:
    """Return the bundle's P1 hydro-class hourly dispatch (MW), model clock."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    rows = frame[(frame["klass"] == "hydro") & (frame["pass"] == "P1")]
    return rows.sort_values("hour")["mw"].to_numpy(dtype=float)


def class_pivot(bundle: Path, year: int) -> pd.DataFrame:
    """Return the bundle's P1 class dispatch as an (hour x class) pivot (MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot_table(
        index="hour", columns="klass", values="mw", observed=True
    ).sort_index()


def system_frame(bundle: Path, year: int) -> pd.DataFrame:
    """Return the bundle's P1 system frame (zone, hour, price, demand, ...)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def ca_lambda(sys_frame: pd.DataFrame) -> np.ndarray:
    """Return the CA demand-weighted hourly lambda (WECC seam zones excluded)."""
    ca = sys_frame[~sys_frame["zone"].str.startswith("WECC")]
    num = (ca["price"] * ca["demand"]).groupby(ca["hour"]).sum()
    den = ca["demand"].groupby(ca["hour"]).sum()
    return (num / den).sort_index().to_numpy(dtype=float)


def storage_net(sys_frame: pd.DataFrame, piv: pd.DataFrame) -> np.ndarray:
    """Return net storage injection (discharge - charge, MW) per hour.

    The class sidecar carries generator classes only; storage is recovered from
    the hourly energy balance: ``demand = sum(classes) + net_storage + slack -
    dump`` summed across zones (net link flow cancels ISO-wide).
    """
    by_hour = sys_frame.groupby("hour")[["demand", "slack", "dump"]].sum().sort_index()
    total_gen = piv.sum(axis=1)
    return (
        by_hour["demand"] - by_hour["slack"] + by_hour["dump"] - total_gen
    ).to_numpy(dtype=float)


def measured_frame(year: int) -> pd.DataFrame:
    """Return the EIA-930 CISO hourly frame on the model clock, long-form."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    return _eia_hourly_frame_filled("CISO", year)


def measured_hydro(year: int, hours: int) -> np.ndarray:
    """Return measured EIA-930 ``NG: WAT`` on the model clock (MW)."""
    from market_sim.data.eia930.envelopes import _hydro_wat_month_hod

    return _hydro_wat_month_hod("CAISO", year)["mw"].to_numpy(dtype=float)[:hours]


def window_means(series: np.ndarray) -> dict[str, float]:
    """Return the mean of an hourly series over each hour-of-day window."""
    hod = np.arange(len(series)) % 24
    return {
        name: float(np.nanmean(series[np.isin(hod, list(win))]))
        for name, win in WINDOWS.items()
    }


def month_index(hours: int) -> np.ndarray:
    """Return the 0-based model-calendar month of each hour."""
    from market_sim.data.fleet import _hour_to_month_index

    return _hour_to_month_index(hours)


def section_a_windows(a_dir: Path, b_dir: Path) -> None:
    """A. Hydro window means: arm A / arm B / measured, and the gaps."""
    print("=== A. hydro by hour-of-day window (mean MW): model vs measured ===")
    for year in YEARS:
        ha, hb = hydro_hourly(a_dir, year), hydro_hourly(b_dir, year)
        hm = measured_hydro(year, len(ha))
        wa, wb, wm = window_means(ha), window_means(hb), window_means(hm)
        print(f"  {year}  {'window':>10} {'meas':>6} {'A':>6} {'B':>6} "
              f"{'A-meas':>7} {'B-meas':>7}")
        for name in WINDOWS:
            print(
                f"        {name:>10} {wm[name]:>6.0f} {wa[name]:>6.0f} "
                f"{wb[name]:>6.0f} {wa[name] - wm[name]:>+7.0f} "
                f"{wb[name] - wm[name]:>+7.0f}"
            )


def section_b_months(a_dir: Path) -> None:
    """B. Where the overnight excess concentrates by month (arm A)."""
    print("\n=== B. arm A overnight (hod 0-6) gap by month (model - meas, MW) ===")
    print(f"  {'yr':>4} " + " ".join(f"{m:>5}" for m in range(1, 13)))
    for year in YEARS:
        ha = hydro_hourly(a_dir, year)
        hm = measured_hydro(year, len(ha))
        hod = np.arange(len(ha)) % 24
        mon = month_index(len(ha))
        sel = np.isin(hod, list(WINDOWS["overnight"]))
        row = []
        for m in range(12):
            pick = sel & (mon == m)
            row.append(float(np.nanmean(ha[pick] - hm[pick])))
        print(f"  {year:>4} " + " ".join(f"{v:>+5.0f}" for v in row))


def section_c_ceiling(a_dir: Path, b_dir: Path) -> None:
    """C. Candidate (i): the p95 ceiling overnight — binding share + rank."""
    from market_sim.data.eia930.envelopes import (
        _hydro_wat_month_hod,
        measured_hydro_hourly_envelope,
    )

    print("\n=== C. candidate (i): p95 (month x hod) ceiling vs the model ===")
    print("  binding share = frac of window hours with model >= "
          f"{CEIL_BIND_FRAC:.3f} x ceiling")
    for year in YEARS:
        ha, hb = hydro_hourly(a_dir, year), hydro_hourly(b_dir, year)
        cap = measured_hydro_hourly_envelope("CAISO", year, len(ha))
        hod = np.arange(len(ha)) % 24
        print(f"  {year}  {'window':>10} {'bindA':>6} {'bindB':>6} "
              f"{'headroomA(MW)':>13}")
        for name, win in WINDOWS.items():
            sel = np.isin(hod, list(win))
            ba = float((ha[sel] >= CEIL_BIND_FRAC * cap[sel]).mean())
            bb = float((hb[sel] >= CEIL_BIND_FRAC * cap[sel]).mean())
            head = float(np.mean(cap[sel] - ha[sel]))
            print(f"        {name:>10} {ba:>6.3f} {bb:>6.3f} {head:>13.0f}")

        # Where does arm A's overnight dispatch sit inside the measured
        # per-(month, hod) distribution? Mean percentile rank ~0.5 would be the
        # measured typical level; ~0.8+ means the model lives near the top of
        # the measured distribution every night.
        meas = _hydro_wat_month_hod("CAISO", year).dropna(subset=["mw"])
        mon = month_index(len(ha))
        sel = np.isin(hod, list(WINDOWS["overnight"]))
        ranks: list[float] = []
        stats: list[tuple[float, float, float, float]] = []
        for m in range(12):
            for h in WINDOWS["overnight"]:
                bucket = meas[(meas["month"] == m + 1) & (meas["hod"] == h)][
                    "mw"
                ].to_numpy(dtype=float)
                if bucket.size == 0:
                    continue
                pick = sel & (mon == m) & (hod == h)
                for v in ha[pick]:
                    ranks.append(float((bucket <= v).mean()))
                stats.append(
                    (
                        float(np.mean(bucket)),
                        float(np.percentile(bucket, 50)),
                        float(np.percentile(bucket, 75)),
                        float(np.percentile(bucket, 95)),
                    )
                )
            arr = np.array(stats)
        print(
            f"        arm A overnight mean percentile-rank in measured bucket: "
            f"{np.mean(ranks):.3f}"
        )
        print(
            f"        measured overnight bucket means: mean {arr[:, 0].mean():.0f}"
            f"  p50 {arr[:, 1].mean():.0f}  p75 {arr[:, 2].mean():.0f}"
            f"  p95 {arr[:, 3].mean():.0f} MW"
        )


def section_d_budget(a_dir: Path, b_dir: Path) -> None:
    """D. Candidate (ii): per-month budget utilisation (adder inertness)."""
    from market_sim.data.eia930.envelopes import measured_monthly_hydro

    print("\n=== D. candidate (ii): monthly budget utilisation "
          "(model energy / measured budget) ===")
    print(f"  a month is BOUND at >= {BUDGET_BIND_FRAC:.3f}")
    for year in YEARS:
        budget = measured_monthly_hydro("CAISO", year)
        for tag, bundle in (("A", a_dir), ("B", b_dir)):
            h = hydro_hourly(bundle, year)
            mon = month_index(len(h))
            use = np.array([h[mon == m].sum() for m in range(12)])
            util = np.divide(use, budget, out=np.zeros(12), where=budget > 0)
            bound = int((util >= BUDGET_BIND_FRAC).sum())
            print(
                f"  {year} {tag}: " + " ".join(f"{u:>5.3f}" for u in util)
                + f"   bound {bound}/12"
            )


def section_e_lambda(a_dir: Path) -> None:
    """E. Candidate (ii) continued: the lambda ordering the LP allocates against."""
    print("\n=== E. arm A CA demand-weighted lambda by window ($/MWh) ===")
    print("  (the LP puts marginal water in the highest-lambda unconstrained "
          "hours; where slack water is declined it is declined from the "
          "lowest-lambda hours)")
    for year in YEARS:
        sys_a = system_frame(a_dir, year)
        lam = ca_lambda(sys_a)
        w = window_means(lam)
        line = " ".join(f"{name} {w[name]:>6.2f}" for name in WINDOWS)
        print(f"  {year}: {line}")
        # Hydro-interior overnight share: fleet strictly between 0 and the
        # ceiling means some unit is interior, i.e. hydro is the marginal
        # (price-setting) resource there and lambda equals the month's water
        # value.
        from market_sim.data.eia930.envelopes import measured_hydro_hourly_envelope

        ha = hydro_hourly(a_dir, year)
        cap = measured_hydro_hourly_envelope("CAISO", year, len(ha))
        hod = np.arange(len(ha)) % 24
        sel = np.isin(hod, list(WINDOWS["overnight"]))
        interior = (ha[sel] > 10.0) & (ha[sel] < CEIL_BIND_FRAC * cap[sel])
        lam_int = lam[sel][interior]
        mon = month_index(len(ha))[sel][interior]
        spread = [
            float(np.std(lam_int[mon == m])) for m in range(12) if (mon == m).any()
        ]
        print(
            f"        overnight hydro-interior share {interior.mean():.3f}; "
            f"lambda std within interior month-hours "
            f"median {np.median(spread):.2f} $/MWh"
        )


def section_f_stack(a_dir: Path) -> None:
    """F. Candidate (iii): the overnight class stack, model vs measured."""
    print("\n=== F. overnight (hod 0-6) stack, arm A model vs measured (mean MW) ===")
    print("  measured gas is the EIA-930 NG cell — LEVEL-corrupt for CISO "
          "2023+ (caiso-121), shown for shape context only; the honest "
          "closure is the OTHER+GAS composite line")
    for year in YEARS:
        piv = class_pivot(a_dir, year)
        sys_a = system_frame(a_dir, year)
        hours = len(piv)
        hod = np.arange(hours) % 24
        sel = np.isin(hod, list(WINDOWS["overnight"]))

        meas = measured_frame(year)
        ti = pd.to_numeric(meas["Total interchange"], errors="coerce").to_numpy()[
            :hours
        ]
        cols = {
            "hydro": "NG: WAT",
            "nuclear": "NG: NUC",
            "wind": "NG: WND",
            "solar": "NG: SUN",
            "gas(930)": "NG: NG",
            "geo": "NG: GEO",
            "oth": "NG: OTH",
        }
        m_series = {
            k: pd.to_numeric(meas[c], errors="coerce").to_numpy()[:hours]
            for k, c in cols.items()
        }
        m_series["import"] = -ti
        m_demand = pd.to_numeric(meas["Demand"], errors="coerce").to_numpy()[:hours]

        gas_model = piv[[c for c in GAS_CLASSES if c in piv.columns]].sum(axis=1)
        rows = {
            "hydro": piv["hydro"].to_numpy(),
            "import": piv["import"].to_numpy(),
            "gas": gas_model.to_numpy(),
            "nuclear": piv["nuclear"].to_numpy(),
            "wind": piv["wind"].to_numpy(),
            "solar": piv["solar"].to_numpy(),
            "other+bio+coal+oil": (
                piv[[c for c in ("OTHER", "biomass", "COAL", "oil") if c in piv]]
                .sum(axis=1)
                .to_numpy()
            ),
            "storage_net": storage_net(sys_a, piv),
        }
        mdl_demand = (
            sys_a.groupby("hour")["demand"].sum().sort_index().to_numpy()[:hours]
        )

        print(f"  {year}  {'class':>18} {'model':>7} {'meas':>7} {'gap':>7}")
        for name in ("hydro", "import", "nuclear", "wind", "solar"):
            gm = float(np.nanmean(rows[name][sel]))
            mm = float(np.nanmean(m_series[name][sel]))
            print(f"        {name:>18} {gm:>7.0f} {mm:>7.0f} {gm - mm:>+7.0f}")
        # gas + other composite: the model splits gas/OTHER/biomass differently
        # from the 930 fuel cells (and 930's NG cell is level-corrupt), so the
        # honest comparison is the composite thermal-other block.
        gm = float(np.nanmean((rows["gas"] + rows["other+bio+coal+oil"])[sel]))
        mm = float(
            np.nanmean(
                (m_series["gas(930)"] + m_series["geo"] + m_series["oth"])[sel]
            )
        )
        print(f"        {'gas+geo+other':>18} {gm:>7.0f} {mm:>7.0f} {gm - mm:>+7.0f}")
        gm = float(np.nanmean(rows["storage_net"][sel]))
        # measured storage net is inside NG: OTH for CISO — no separate cell;
        # report the model's own storage draw for scale.
        print(f"        {'storage_net(model)':>18} {gm:>7.0f} {'-':>7} {'':>7}")
        gm = float(np.nanmean(mdl_demand[sel]))
        mm = float(np.nanmean(m_demand[sel]))
        print(f"        {'demand':>18} {gm:>7.0f} {mm:>7.0f} {gm - mm:>+7.0f}")


def _split_weeks_within_months(mon: np.ndarray, hours: int) -> np.ndarray:
    """Return a week id per hour: 7-day chunks that nest inside months."""
    day = np.arange(hours) // 24
    week = np.zeros(hours, dtype=int)
    wid = 0
    for m in range(12):
        mdays = np.unique(day[mon == m])
        for c0 in range(0, len(mdays), 7):
            week[np.isin(day, mdays[c0 : c0 + 7])] = wid
            wid += 1
    return week


def _greedy(
    lam: np.ndarray,
    cap: np.ndarray,
    budgets: dict[int, float],
    groups: np.ndarray,
    base: np.ndarray | None = None,
) -> np.ndarray:
    """Fill each group's budget into its highest-lambda hours up to the cap.

    A first-order proxy for the budget LP's own allocation (fixed prices — no
    feedback), optionally on top of a flat ``base`` (whose energy the caller
    must already have excluded from ``budgets``). Water is declined once the
    remaining hours price negative, mirroring the LP's decline margin.
    """
    h = np.zeros(len(lam)) if base is None else base.copy()
    room = cap if base is None else np.maximum(cap - base, 0.0)
    for g, energy in budgets.items():
        idx = np.where(groups == g)[0]
        order = idx[np.argsort(-lam[idx])]
        rem = energy
        for i in order:
            if rem <= 0 or lam[i] < 0:
                break
            take = min(room[i], rem)
            h[i] += take
            rem -= take
    return h


def section_g_mobility(a_dir: Path) -> None:
    """G. Cross-week water mobility + nightly hydrograph tracking (arm A)."""
    print("\n=== G. weekly water mobility and nightly tracking (arm A) ===")
    for year in YEARS:
        h = hydro_hourly(a_dir, year)
        meas = measured_hydro(year, len(h))
        n = len(h)
        mon = month_index(n)
        week = _split_weeks_within_months(mon, n)
        wm = np.array([h[week == w].sum() for w in np.unique(week)]) / 1e3
        ww = np.array([np.nansum(meas[week == w]) for w in np.unique(week)]) / 1e3
        d = np.abs(wm - ww)
        hod = np.arange(n) % 24
        night = np.isin(hod, list(WINDOWS["overnight"]))
        day = np.arange(n) // 24
        nm = pd.DataFrame({"d": day[night], "mw": h[night]}).groupby("d")["mw"].mean()
        nn = (
            pd.DataFrame({"d": day[night], "mw": meas[night]}).groupby("d")["mw"].mean()
        )
        ok = nn.notna()
        r = float(np.corrcoef(nm[ok], nn[ok])[0, 1])
        print(
            f"  {year}: weekly |model-meas| mean {d.mean():.0f} GWh "
            f"(p90 {np.percentile(d, 90):.0f}, max {d.max():.0f}; meas weekly "
            f"mean {ww.mean():.0f}); nightly across-day r {r:.3f} "
            f"(nightly std model {nm.std():.0f} / meas {nn[ok].std():.0f} MW)"
        )


def section_h_greedy(a_dir: Path, b_dir: Path, ror_cf_cut: float = 0.45) -> None:
    """H. Greedy allocation proxies: weekly grain, RoR split, floor-base check."""
    from market_sim.data.eia930.envelopes import (
        measured_hydro_hourly_envelope,
        measured_monthly_hydro,
    )
    from market_sim.data.eia_loader import measured_hydro_min_flow_level
    from market_sim.data.hydro import hours_per_month, load_hydro_budget

    print("\n=== H. greedy allocation proxies (fixed arm-A lambda, no feedback) ===")
    print(
        "  validation rows first: greedy(month) vs arm A and greedy(floor-base)"
        " vs arm B calibrate the proxy's bias before reading the candidates"
    )
    for year in YEARS:
        ha, hb = hydro_hourly(a_dir, year), hydro_hourly(b_dir, year)
        meas = measured_hydro(year, len(ha))
        sys_a = system_frame(a_dir, year)
        lam = ca_lambda(sys_a)
        n = len(ha)
        cap = measured_hydro_hourly_envelope("CAISO", year, n)
        mon = month_index(n)
        hod = np.arange(n) % 24
        night = np.isin(hod, list(WINDOWS["overnight"]))
        belly = np.isin(hod, list(WINDOWS["belly"]))
        eve = np.isin(hod, list(WINDOWS["evening"]))
        hpm = hours_per_month().astype(float)
        week = _split_weeks_within_months(mon, n)

        def rep(tag: str, h: np.ndarray) -> None:
            print(
                f"   {tag:<22} overnight {np.mean(h[night]):>5.0f}"
                f"  belly {np.mean(h[belly]):>5.0f}"
                f"  evening {np.mean(h[eve]):>5.0f}"
            )

        print(
            f"  {year}: measured overnight {np.nanmean(meas[night]):.0f}"
            f"  belly {np.nanmean(meas[belly]):.0f}"
            f"  evening {np.nanmean(meas[eve]):.0f}"
        )
        rep("arm A (LP)", ha)
        mon_budget = {m: float(ha[mon == m].sum()) for m in range(12)}
        rep("greedy month [valid]", _greedy(lam, cap, mon_budget, mon))
        wk_budget: dict[int, float] = {}
        for w in np.unique(week):
            m = mon[week == w][0]
            meas_m = float(np.nansum(meas[mon == m]))
            share = float(np.nansum(meas[week == w])) / meas_m if meas_m > 0 else 0.0
            wk_budget[int(w)] = share * mon_budget[m]
        rep("greedy week", _greedy(lam, cap, wk_budget, week))

        budget = load_hydro_budget(
            "CAISO",
            year,
            backfill_year=(2024 if year == 2025 else None),
            monthly_target_mwh=measured_monthly_hydro("CAISO", year),
        )
        cf = budget.monthly_energy.sum(axis=1) / np.maximum(
            budget.max_mw * 8760.0, 1e-9
        )
        ror = cf >= ror_cf_cut
        fleet_m = budget.monthly_energy.sum(axis=0)
        scale = np.divide(
            np.array([mon_budget[m] for m in range(12)]),
            fleet_m,
            out=np.ones(12),
            where=fleet_m > 0,
        )
        monthly_energy = budget.monthly_energy * scale[np.newaxis, :]
        ror_flat = (monthly_energy[ror].sum(axis=0) / hpm)[mon]
        res_budget = {m: float(monthly_energy[~ror][:, m].sum()) for m in range(12)}
        share = monthly_energy[ror].sum() / monthly_energy.sum()
        rep(f"greedy RoR cf>={ror_cf_cut}", _greedy(lam, cap, res_budget, mon, ror_flat))
        print(
            f"   (RoR share of budget {share:.1%}; {int(ror.sum())}/{len(cf)} plants)"
        )

        rep("arm B (LP, floor)", hb)
        floor_m = measured_hydro_min_flow_level("CAISO", year)
        b_budget = {
            m: float(hb[mon == m].sum()) - float(floor_m[m] * hpm[m])
            for m in range(12)
        }
        rep("greedy floor [valid]", _greedy(lam, cap, b_budget, mon, floor_m[mon]))


def section_i_ps(a_dir: Path) -> None:
    """I. Monthly overnight gap vs EIA-923 CISO pumped-storage net (the PS
    pollution of the ``NG: WAT`` boundary)."""
    from market_sim.data.eia923 import load_monthly_generation, monthly_netgen_columns

    print("\n=== I. overnight gap vs EIA-923 pumped-storage net (monthly) ===")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    ps = gen[(gen["prime_mover"] == "PS") & (gen["ba_code"] == "CISO")]
    gaps_all, nets_all = [], []
    for year in YEARS:
        h = hydro_hourly(a_dir, year)
        meas = measured_hydro(year, len(h))
        mon = month_index(len(h))
        hod = np.arange(len(h)) % 24
        sel = np.isin(hod, list(WINDOWS["overnight"]))
        net_m = ps[ps["year"] == year][mcols].sum().to_numpy(dtype=float)
        hpm = np.bincount(mon, minlength=12).astype(float)
        gaps = [
            float(np.nanmean(h[sel & (mon == m)] - meas[sel & (mon == m)]))
            for m in range(12)
        ]
        nets = list(net_m / hpm)
        b, a = np.polyfit(nets, gaps, 1)
        r = float(np.corrcoef(nets, gaps)[0, 1])
        print(
            f"  {year}: PS net {net_m.sum() / 1e3:+.0f} GWh/yr; slope {b:+.2f}, "
            f"intercept {a:+.0f} MW, r {r:+.3f}"
        )
        gaps_all += gaps
        nets_all += nets
    b, a = np.polyfit(nets_all, gaps_all, 1)
    print(
        f"  pooled: slope {b:+.2f}, intercept {a:+.0f} MW, "
        f"r {np.corrcoef(nets_all, gaps_all)[0, 1]:+.3f} (n={len(gaps_all)})"
    )


def main() -> None:
    """Run every section of the overnight attribution."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, help="arm A bundle (no delta)")
    ap.add_argument("--arm", required=True, help="arm B bundle (floor on)")
    args = ap.parse_args()
    a_dir, b_dir = Path(args.control), Path(args.arm)

    section_a_windows(a_dir, b_dir)
    section_b_months(a_dir)
    section_c_ceiling(a_dir, b_dir)
    section_d_budget(a_dir, b_dir)
    section_e_lambda(a_dir)
    section_f_stack(a_dir)
    section_g_mobility(a_dir)
    section_h_greedy(a_dir, b_dir)
    section_i_ps(a_dir)


if __name__ == "__main__":
    main()
