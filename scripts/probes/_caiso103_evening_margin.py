"""CAISO-103 priority-2 probe: WHAT SERVES THE MARGIN in the Q1 evening hours.

FINDING-caiso102 §4/§9 established the evening residual (-5.8/-4.9/-1.1) is a
CT-rung merit-composition defect on the aligned clock: in the deepest
resid-quartile (Q1) evening hours the measured fleet runs 1.33/1.19/0.51 GW of
CT_PEAKER while the model runs 0.58/0.31/0.12 GW, model gas sits ~2-3 GW under
the measured stack, and model imports are AT or ABOVE measured. The model's
tight-hour clearing never climbs to the CT rung. This probe decomposes the Q1
hours' MARGINAL ECONOMICS on the same-machine keeper repro (caiso102_repro_A
recipe = the caiso-102-hourfix keeper bytes): what is at the margin instead,
and how much cheaper-than-CT supply depth the model has in exactly those hours.

Per year, on the aligned model clock (interval-beginning, the
_caiso102_evening_merit convention), evening = hod 17-21, Q1 = deepest
resid-quartile of evening hours (resid = model CA demand-wtd lambda - actual RT):

  1. MARGINAL-CLASS ATTRIBUTION - for each Q1 hour, the classes with a unit at
     interior dispatch (0.02-0.98 of its unit-year p99 MW - an LP unit strictly
     inside its bounds is price-setting); share of Q1 hours each class is
     marginal, vs the same share across ALL evening hours.
  2. IMPORT RUNG DEPTH - per CA-inbound link, headroom = (link-year p99.5 flow
     proxy for the binding limit) - flow, summed; share of Q1 hours the total
     import is saturated (>= 98 % of its p99.5); the import-rung price context
     (CA lambda vs the WECC-node lambda spread).
  3. COMMITTED-CC HEADROOM - online CC_REGULAR units' remaining capability
     (unit p98 - mw | mw > 0), the headroom the LP can serve the margin from
     WITHOUT climbing to the CT rung.
  4. CT RUNG ENTRY PRICE (empirical) - per month, the p10 of the unit-zone
     lambda over plant-hours where a CT_PEAKER unit dispatches > 5 % of its
     p99 (the lambda level that actually clears the model's CT rung); the gap
     between Q1 lambda and that entry price is the depth the margin would have
     to climb.
  5. BATTERY TIMING - fleet discharge vs the caiso-99 envelope cap
     (dis_frac_p95[hod] x EIA-860 monthly fleet MW) in Q1 hours: is the
     envelope exhausted (timing bound) or is discharge economically idle?
  6. HUB SEPARATION - actual CAISO RT minus the measured intertie hub LMP
     (MALIN / PALOVRDE, wecc_intertie_lmp_hourly_CAISO.parquet) in Q1 hours,
     against the model's lambda minus the same hubs: does reality price the
     tight evening ABOVE the hubs (an exhausted/inelastic RT intertie margin)
     while the model equalizes to them (an elastic import margin)?

NO LP is built or solved by this probe; NO mechanism is armed (rule 12/19 -
any mechanism goes to the owner ask). NO CT floor (caiso-91b), no import
throttling (rule 1) - this probe only measures.

Usage: python scripts/probes/_caiso103_evening_margin.py <bundle_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso102_evening_merit import (  # noqa: E402
    CA_ZONES,
    EVENING,
    MONTH_OF_HOUR,
    actual_rt,
    model_hourly,
)

YEARS = (2023, 2024, 2025)


def unit_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Per-unit hourly dispatch with lambda (thermal + pseudo rows)."""
    return pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["unit_id", "klass", "zone", "hour", "mw", "lmp"],
    )


def envelope_dis_cap(year: int, hours: int = 8760) -> np.ndarray:
    """(8760,) caiso-99 envelope discharge cap MW = dis_frac_p95 x fleet MW."""
    from market_sim.config.paths import RAW_DIR, set_eia860_vintage
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import load_eia860_storage

    env = pd.read_csv(RAW_DIR / "reference" / "caiso-storage-shape-envelope.csv")
    env_years = sorted(env["year"].unique())
    use_year = max((y for y in env_years if y <= year), default=env_years[0])
    ey = env[env["year"] == use_year].sort_values("hod")
    dis_frac = ey["dis_frac_p95"].to_numpy(dtype=float)

    set_eia860_vintage(None)
    cfg = ScenarioConfig(mode="backcast", storage_vintage_ramp=True)
    units = load_eia860_storage("CAISO", year, cfg)
    fleet = np.zeros(12)
    for u in units:
        if u.tech_name == "pumped_storage":
            continue
        fleet += np.array(
            u.monthly_power_mw
            if u.monthly_power_mw is not None
            else [u.power_cap_mw] * 12,
            dtype=float,
        )
    fleet_h = fleet[MONTH_OF_HOUR - 1]
    return dis_frac[np.arange(hours) % 24] * fleet_h


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    hod = np.arange(8760) % 24
    ev_mask = np.isin(hod, EVENING)

    for y in YEARS:
        m = model_hourly(bundle, y)
        rt = actual_rt(y)
        resid = m["lambda"] - rt
        ok = ev_mask & np.isfinite(resid) & (np.abs(rt) > 1e-9)
        q1_edge = np.nanquantile(resid[ok], 0.25)
        q1 = ok & (resid <= q1_edge)

        u = unit_hourly(bundle, y)
        # unit-year capability proxy + interior-dispatch flags, vectorized
        cap = u.groupby("unit_id", observed=True).mw.quantile(0.99)
        u = u.assign(cap=u.unit_id.map(cap).astype(float))
        u = u[u.cap > 1.0]
        interior = (u.mw > 0.02 * u.cap) & (u.mw < 0.98 * u.cap)

        print(f"\n===================== {y} =====================")
        print(
            f"Q1 = {int(q1.sum())} evening hours, resid <= {q1_edge:+.1f}; "
            f"mean resid {np.average(resid[q1], weights=m['demand'][q1]):+.1f} "
            f"(all-evening {np.average(resid[ok], weights=m['demand'][ok]):+.1f}); "
            f"mean model lam {m['lambda'][q1].mean():.1f} vs actual "
            f"{rt[q1].mean():.1f}"
        )

        # -- 1. marginal-class attribution ----------------------------------
        print("1. marginal-class share of hours (Q1 | all-evening), interior MW:")
        q1_hours = set(np.flatnonzero(q1))
        ev_hours = set(np.flatnonzero(ok))
        ui = u[interior]
        marg = ui.groupby(["klass", "hour"], observed=True).mw.sum().reset_index()
        for k, sub in marg.groupby("klass", observed=True):
            hs = set(sub.hour)
            s_q1 = len(hs & q1_hours) / max(len(q1_hours), 1)
            s_ev = len(hs & ev_hours) / max(len(ev_hours), 1)
            if s_ev < 0.02:
                continue
            mw_q1 = sub[sub.hour.isin(q1_hours)].mw.mean()
            print(
                f"    {str(k):16s}: {s_q1:5.2f} | {s_ev:5.2f}"
                f"  (interior {0 if np.isnan(mw_q1) else mw_q1:6.0f} MW in Q1)"
            )

        # -- 2. import rung depth -------------------------------------------
        f = pd.read_parquet(bundle / "flows.parquet")
        f = f[(f["pass"] == "P1") & (f.year == y)]
        into = f[(~f.from_zone.isin(CA_ZONES)) & (f.to_zone.isin(CA_ZONES))]
        link = into.assign(
            link=into.from_zone.astype(str) + ">" + into.to_zone.astype(str)
        )
        headroom = np.zeros(8760)
        at_limit_links = np.zeros(8760)
        n_links = 0
        for _, sub in link.groupby("link"):
            v = np.zeros(8760)
            np.add.at(v, sub.hour.to_numpy(int), sub.mw.to_numpy(float))
            cap995 = np.quantile(v, 0.995)
            if cap995 <= 1.0:
                continue
            n_links += 1
            headroom += np.clip(cap995 - v, 0.0, None)
            at_limit_links += (v >= 0.98 * cap995).astype(float)
        tot_imp = m["imports"]
        imp_cap = np.quantile(tot_imp, 0.995)
        sat = tot_imp >= 0.98 * imp_cap
        print(
            f"2. import rung: {n_links} CA-inbound links; Q1 mean headroom "
            f"{headroom[q1].mean() / 1e3:.1f} GW (all-evening "
            f"{headroom[ok].mean() / 1e3:.1f}); links-at-limit Q1 mean "
            f"{at_limit_links[q1].mean():.1f}; TOTAL import saturated in "
            f"{sat[q1].mean():.0%} of Q1 hours (all-evening {sat[ok].mean():.0%})"
        )

        # -- 3. committed-CC headroom ---------------------------------------
        cc = u[u.klass == "CC_REGULAR"]
        on = cc[cc.mw > 0]
        hr = (
            on.assign(hd=np.clip(on.cap * 0.98 - on.mw, 0.0, None))
            .groupby("hour")
            .hd.sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy()
        )
        print(
            f"3. online-CC headroom: Q1 mean {hr[q1].mean() / 1e3:.2f} GW "
            f"(all-evening {hr[ok].mean() / 1e3:.2f} GW)"
        )

        # -- 4. empirical CT rung entry price -------------------------------
        ct = u[u.klass == "CT_PEAKER"]
        cton = ct[ct.mw > 0.05 * ct.cap]
        if len(cton):
            mo_h = MONTH_OF_HOUR[cton.hour.to_numpy(int)]
            entry = (
                pd.DataFrame({"mo": mo_h, "lmp": cton.lmp.to_numpy(float)})
                .groupby("mo")
                .lmp.quantile(0.10)
            )
            mo_q1 = MONTH_OF_HOUR[np.flatnonzero(q1)]
            gap = [
                entry.get(mm, np.nan) - m["lambda"][h]
                for mm, h in zip(mo_q1, np.flatnonzero(q1))
            ]
            gap = np.array(gap, dtype=float)
            print(
                f"4. CT rung entry lam (monthly p10 over CT-active plant-hours): "
                f"ann-mean {entry.mean():.1f}; Q1 lam sits "
                f"{np.nanmean(gap):+.1f} $/MWh BELOW the rung entry "
                f"(p25/p50/p75 {np.nanpercentile(gap, 25):+.1f}/"
                f"{np.nanpercentile(gap, 50):+.1f}/{np.nanpercentile(gap, 75):+.1f})"
            )
        else:
            print("4. CT rung never active this year")

        # -- 5. battery envelope timing -------------------------------------
        env_cap = envelope_dis_cap(y)
        st = pd.read_parquet(bundle / "storage.parquet")
        st = st[(st["pass"] == "P1") & (st.year == y) & (st.tech != "pumped_storage")]
        dis = (
            st.groupby("hour")
            .discharge_mw.sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy()
        )
        env_bind = dis >= 0.98 * env_cap
        print(
            f"5. battery: Q1 mean discharge {dis[q1].mean() / 1e3:.2f} GW vs "
            f"envelope cap {env_cap[q1].mean() / 1e3:.2f} GW; envelope binding "
            f"in {env_bind[q1].mean():.0%} of Q1 hours "
            f"(all-evening {env_bind[ok].mean():.0%})"
        )
        # -- 6. hub separation (actual vs model, same measured hubs) --------
        hubp = pd.read_parquet(
            REPO
            / "data"
            / "raw"
            / "_validation-source"
            / "wecc_intertie_lmp_hourly_CAISO.parquet"
        )
        hy = hubp[hubp.year == y]
        hubs = {}
        for hname, sub in hy.groupby("hub"):
            v = np.full(8760, np.nan)
            s = sub.sort_values("hour")
            v[s.hour.to_numpy(int)] = s.price.to_numpy(float)
            hubs[str(hname)] = v
        hub_hi = np.nanmax(np.stack(list(hubs.values())), axis=0)
        fin = q1 & np.isfinite(hub_hi)
        print(
            f"6. hub separation in Q1 (n={int(fin.sum())}): actual RT - "
            f"max(MALIN,PALOVRDE) mean {np.nanmean(rt[fin] - hub_hi[fin]):+.1f} "
            f"(p25/p50/p75 "
            f"{np.nanpercentile(rt[fin] - hub_hi[fin], 25):+.1f}/"
            f"{np.nanpercentile(rt[fin] - hub_hi[fin], 50):+.1f}/"
            f"{np.nanpercentile(rt[fin] - hub_hi[fin], 75):+.1f}); "
            f"model lam - same hub mean "
            f"{np.nanmean(m['lambda'][fin] - hub_hi[fin]):+.1f} (p50 "
            f"{np.nanpercentile(m['lambda'][fin] - hub_hi[fin], 50):+.1f})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
