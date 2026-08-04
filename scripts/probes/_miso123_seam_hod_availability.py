"""miso-123 Phase-0 probe — hour-of-day-resolved MISO seam band AVAILABILITY.

NO LP IS SOLVED. Every number is read from committed artifacts or rebuilt
offline from the model's own seam construction:

* the keeper bundle ``results/calibration/miso122_scopegate_B/hourly/``
  (``system_<year>.parquet`` P1 duals, ``class_hourly_<year>.parquet`` class
  dispatch),
* ``data/raw/eia-930-interchange/MISO interchange hourly.parquet`` — the
  directed BA-to-BA series the armed envelope is ALREADY built from,
* ``data/raw/eia-930-hourly/MISO hourly.parquet`` — total interchange,
* the model's own seam objects: ``INTERFACE_NEIGHBORS["MISO"]``,
  ``MISO_MANITOBA_SEAM_SPEC``, ``MISO_SEAM_DIBA``, ``MISO_SEAM_LADDER_BY_YEAR``,
  ``measured_seam_import_envelope``, and the merit-cap waterfall semantics of
  ``inject_miso_seam_flow_limit``.

Pre-registration: ``results/calibration/PREREG-miso123-seam-hod-band-availability
-2026-08-04.md`` (committed BEFORE this file was written).

Questions, in the pre-registered order:

Q0  Reconstruction fidelity — does the offline band-clearing reconstruction
    reproduce the keeper's own solved ``import`` class hourly MW?  Everything
    downstream is conditional on this.
Q1  Is availability ALREADY hour-of-day-resolved, and does its shape point the
    right way?  (This question can dissolve the lever: miso-114 attributed the
    mis-shape to the hour-invariant PRICE ladder, and the armed p90 envelope is
    already per-(month x hour-of-day).)
Q2  Does the envelope BIND?  Binding share AND the marginal share of binding
    hours (miso-121's standing lesson: binding is not marginality), split
    overnight vs peak.
Q3  The candidate C1 construction's own effect, HELD-PRICE — the upper bound on
    the achievable hour-of-day correction.
Q4  KILL-13 — the pre-registered rule 13 [R-MEASURED] test: (a) headroom
    collapse against the cell-conditional mean, (b) choice extinguished.
Q5  Annual-energy integrity under the candidate.
Q6  Night/peak decomposition — how much of the measured mis-shape an
    availability CEILING can reach at all, and the unreachable remainder.

Rule 22 [R-HOLDOUT]: 2023-2025 only; MISO holds no calibration-complete marker
and no out-of-training year is solved, scored or read.  Rule 15: this probe
produces no run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/miso122_scopegate_B"
YEARS = (2023, 2024, 2025)
NIGHT = [0, 1, 2, 3, 4, 5, 22, 23]
PEAK = [16, 17, 18, 19]
# Zone hosting each seam's bands. The keeper runs miso_south_seam_split, which
# re-homes the South seam onto its own external node; every other seam stays in
# the shared MISO_external node (import_nodes.build_reference_price_node).
SEAM_ZONE = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}


def seam_limits() -> dict[str, float]:
    """Return each priced seam's interface limit (MW) as the keeper builds it."""
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )

    out = {n.name: float(n.interface_limit_mw) for n in INTERFACE_NEIGHBORS["MISO"]}
    # miso_manitoba_seam is armed on the keeper, so the MHEB seam's bands exist.
    out[MISO_MANITOBA_SEAM_SPEC.name] = float(MISO_MANITOBA_SEAM_SPEC.interface_limit_mw)
    return out


def measured_seam_flow(year: int, hours: int = 8760) -> dict[str, np.ndarray]:
    """Per-seam MEASURED hourly net import (MW) on the model's 8760 clock.

    The same source, seam pooling and sign convention as
    ``eia930.envelopes.measured_seam_import_envelope`` — this returns the raw
    hourly series that function reduces to a per-(month x hour-of-day)
    percentile, so the two are guaranteed to describe the same object.
    """
    from market_sim.config.interchange_config import MISO_SEAM_DIBA
    from market_sim.config.paths import RAW_DIR

    path = RAW_DIR / "eia-930-interchange" / "MISO interchange hourly.parquet"
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"])
    frame = frame[local.year == year]
    local = pd.DatetimeIndex(frame["local_time"])
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    work = pd.DataFrame(
        {
            "seam": frame["diba"].astype(str).map(diba_to_seam).to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["seam", "mw"])
    # Net import per seam per timestamp = -sum(interchange over its DIBAs).
    per_ts = (-work.groupby(["seam", "ts"], observed=True)["mw"].sum()).reset_index(
        name="net_import"
    )
    # Model clock: fixed non-leap calendar, 8760 chronological hours.
    idx = pd.date_range(f"{year}-01-01", periods=8784, freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))][:hours]
    out: dict[str, np.ndarray] = {}
    for name in MISO_SEAM_DIBA:
        sub = per_ts[per_ts["seam"] == name].set_index("ts")["net_import"]
        if sub.empty:
            continue
        sub = sub[~sub.index.duplicated()]
        out[name] = sub.reindex(idx).interpolate(limit_direction="both").to_numpy()
    return out


def keeper_prices(year: int) -> dict[str, np.ndarray]:
    """P1 duals per external zone on the keeper's own 8760 (the seam's signal)."""
    s = pd.read_parquet(f"{BUNDLE}/hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    wide = s.pivot_table(index="hour", columns="zone", values="price").sort_index()
    return {z: wide[z].to_numpy() for z in wide.columns}


def keeper_import_class(year: int) -> np.ndarray:
    """The keeper's own solved hourly net ``import``-class MW."""
    c = pd.read_parquet(f"{BUNDLE}/hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == "import")]
    return c.sort_values("hour")["mw"].to_numpy()


def actual_net_import(year: int, hours: int = 8760) -> np.ndarray:
    """EIA-930 measured MISO net import (MW), trimmed to the model's 8760."""
    g = pd.read_parquet("data/raw/eia-930-hourly/MISO hourly.parquet")
    g["ts"] = pd.to_datetime(g["Local time"])
    g = g.loc[
        (g["ts"] >= pd.Timestamp(f"{year}-01-01"))
        & (g["ts"] < pd.Timestamp(f"{year + 1}-01-01"))
    ].copy()
    g = g[~((g.ts.dt.month == 2) & (g.ts.dt.day == 29))].reset_index(drop=True)
    ti = pd.to_numeric(g["Total interchange"], errors="coerce").interpolate(
        limit_direction="both"
    )
    return (-ti).to_numpy()[:hours]


def month_hod(hours: int = 8760) -> tuple[np.ndarray, np.ndarray]:
    """The model's own (0-based month, hour-of-day) index for each model hour."""
    from market_sim.data.fleet import _hour_to_month_index

    return _hour_to_month_index(hours), np.arange(hours) % 24


def current_availability(cap: np.ndarray, width: float, n: int) -> np.ndarray:
    """Merit-cap waterfall availability, exactly as inject_miso_seam_flow_limit.

    Band k (1-indexed) keeps ``clip((cap - (k-1)*width) / width, 0, 1)`` — the
    ``miso_seam_envelope_merit_cap`` semantics armed on the keeper.
    """
    depth = np.arange(n)[:, None] * width
    return np.clip((cap[None, :] - depth) / width, 0.0, 1.0)


def candidate_availability(
    flow: np.ndarray, width: float, n: int, rm: np.ndarray, rh: np.ndarray
) -> np.ndarray:
    """Candidate C1 — per-band per-(month x hod) cell SURVIVAL availability.

    ``avail[k, h] = fraction of measured hours in cell (month, hod) whose
    directed flow exceeded band k's lower depth edge (k-1)*width``.  Same
    source, same cell grain and same 8-band grid as the armed envelope; zero
    free parameters, zero thresholds, a strict ceiling in [0, 1].
    """
    edges = np.arange(n) * width  # lower depth edge of each band
    tab = np.zeros((n, 12, 24))
    for m in range(12):
        for h in range(24):
            sel = flow[(rm == m) & (rh == h)]
            if sel.size == 0:
                continue
            tab[:, m, h] = (sel[None, :] > edges[:, None]).mean(axis=1)
    return tab[:, rm, rh]


def cleared(avail: np.ndarray, width: float, price: np.ndarray, rungs) -> np.ndarray:
    """Held-price cleared MW per hour: sum over bands in the money.

    A positive-output import band with marginal cost ``pi_k`` clears at its full
    available width when the zone dual exceeds ``pi_k`` — the same
    bands-in-the-money reconstruction miso-114 used.
    """
    pi = np.asarray(rungs, dtype=float)[:, None]
    return (avail * width * (price[None, :] > pi)).sum(axis=0)


def cleared_export(avail_width: np.ndarray, price: np.ndarray, rungs) -> np.ndarray:
    """Held-price cleared EXPORT MW per hour (positive = export)."""
    pi = np.asarray(rungs, dtype=float)[:, None]
    return (avail_width * (price[None, :] < pi)).sum(axis=0)


def hod_corr(model: np.ndarray, actual: np.ndarray) -> float:
    """Correlation of the two 24-point hour-of-day mean profiles.

    Returns NaN when either profile is flat (zero variance) — the South seam
    clears identically 0 MW in some years, and a flat series has no hour-of-day
    shape to correlate. Guarded explicitly so the degenerate case is reported
    rather than raised as a divide warning.
    """
    rh = np.arange(model.size) % 24
    mm = np.array([model[rh == h].mean() for h in range(24)])
    aa = np.array([actual[rh == h].mean() for h in range(24)])
    if mm.std() < 1e-9 or aa.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(mm, aa)[0, 1])


def main() -> None:
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    n = SEAM_FLOW_TRANCHES
    limits = seam_limits()
    rm, rh = month_hod()

    print("=" * 78)
    print("miso-123 Phase-0 — hour-of-day-resolved MISO seam band availability")
    print(f"keeper bundle: {BUNDLE}   (NO LP SOLVED)")
    print(f"seams: {limits}   bands: {n}")
    print("=" * 78)

    summary = {}
    for year in YEARS:
        print(f"\n{'#' * 78}\n## {year}\n{'#' * 78}")
        prices = keeper_prices(year)
        flow = measured_seam_flow(year)
        env_i = measured_seam_import_envelope("MISO", year, 8760, None, "import") or {}
        env_e = measured_seam_import_envelope("MISO", year, 8760, None, "export") or {}
        ladder = MISO_SEAM_LADDER_BY_YEAR.get(year, {})
        keeper_imp = keeper_import_class(year)
        act = actual_net_import(year)

        rec_cur = np.zeros(8760)
        rec_can = np.zeros(8760)
        per_seam = {}
        for seam, limit in limits.items():
            if seam not in ladder or seam not in flow:
                continue
            width = limit / n
            zone = SEAM_ZONE[seam]
            if zone not in prices:
                print(f"  !! seam {seam}: zone {zone} absent from duals — skipped")
                continue
            p = prices[zone]
            cap_i = env_i.get(seam)
            cap_e = env_e.get(seam)
            if cap_i is None:
                continue
            av_cur = current_availability(cap_i, width, n)
            av_can = candidate_availability(flow[seam], width, n, rm, rh)
            imp_cur = cleared(av_cur, width, p, ladder[seam]["import"])
            imp_can = cleared(av_can, width, p, ladder[seam]["import"])
            # Export side: the armed export cap raises min_gen (a ceiling on
            # export). Held-price export clears when the dual is below the rung.
            if cap_e is not None:
                ew = current_availability(cap_e, width, n) * width
                exp_cur = cleared_export(ew, p, ladder[seam]["export"])
            else:
                exp_cur = np.zeros(8760)
            rec_cur += imp_cur - exp_cur
            rec_can += imp_can - exp_cur  # candidate changes the IMPORT side only
            per_seam[seam] = dict(
                width=width,
                cap_i=cap_i,
                av_cur=av_cur,
                av_can=av_can,
                imp_cur=imp_cur,
                imp_can=imp_can,
                flow=flow[seam],
            )

        # ---- Q0 reconstruction fidelity ---------------------------------
        r = float(np.corrcoef(rec_cur, keeper_imp)[0, 1])
        print(
            f"\nQ0  reconstruction vs keeper solved import class:  r = {r:+.3f}   "
            f"mean {rec_cur.mean():8.1f} vs {keeper_imp.mean():8.1f} MW   "
            f"bias {rec_cur.mean() - keeper_imp.mean():+8.1f} MW"
        )
        print(
            f"    hod-profile corr of reconstruction vs keeper: "
            f"{hod_corr(rec_cur, keeper_imp):+.3f}   "
            "(the reconstruction omits border-link TTCs and the LP's zonal "
            "network, so it is an ACCOUNTING of band availability x price, not "
            "a resolve)"
        )

        # ---- Q1 is availability already hod-resolved? --------------------
        print("\nQ1  hour-of-day profile: armed p90 cap vs measured flow vs model")
        print(
            f"    {'seam':>9} {'cap night':>10} {'cap peak':>9} {'n/p':>6} | "
            f"{'meas night':>11} {'meas peak':>10} {'n/p':>6} | "
            f"{'mdl night':>10} {'mdl peak':>9} {'n/p':>6}"
        )
        for seam, d in per_seam.items():
            cn = d["cap_i"][np.isin(rh, NIGHT)].mean()
            cp = d["cap_i"][np.isin(rh, PEAK)].mean()
            fn = d["flow"][np.isin(rh, NIGHT)].mean()
            fp = d["flow"][np.isin(rh, PEAK)].mean()
            mn = d["imp_cur"][np.isin(rh, NIGHT)].mean()
            mp = d["imp_cur"][np.isin(rh, PEAK)].mean()
            print(
                f"    {seam:>9} {cn:10.0f} {cp:9.0f} {cn / max(cp, 1e-9):6.2f} | "
                f"{fn:11.0f} {fp:10.0f} {fn / max(abs(fp), 1e-9):6.2f} | "
                f"{mn:10.0f} {mp:9.0f} {mn / max(mp, 1e-9):6.2f}"
            )
        # Sharper than the night/peak ratio: correlate each channel's own
        # 24-point hour-of-day profile against the MEASURED flow's. This is the
        # statistic that decides whether the AVAILABILITY channel already
        # carries the right hour-of-day shape (in which case "hour-of-day-
        # resolved band availability" is a premise that is already satisfied).
        print(
            f"    hod-profile corr vs MEASURED flow:  "
            f"{'seam':>9} {'armed p90 cap':>14} {'model cleared':>14}"
        )
        for seam, d in per_seam.items():
            print(
                f"    {'':>36}{seam:>9} "
                f"{hod_corr(d['cap_i'], d['flow']):14.3f} "
                f"{hod_corr(d['imp_cur'], d['flow']):14.3f}"
            )

        # ---- Q2 binding share and MARGINAL binding share ----------------
        print(
            "\nQ2  envelope binding (miso-121: the predictive statistic is the "
            "MARGINAL share)"
        )
        print(
            f"    {'seam':>9} {'bind all':>9} {'bind ngt':>9} {'bind pk':>8} | "
            f"{'MARG all':>9} {'MARG ngt':>9} {'MARG pk':>8}"
        )
        q2 = {}
        for seam, d in per_seam.items():
            pi = np.asarray(ladder[seam]["import"], dtype=float)[:, None]
            zone = SEAM_ZONE[seam]
            inmoney = prices[zone][None, :] > pi
            # Binding: cleared import equals the envelope ceiling (the waterfall
            # sum) while at least one further band is in the money.
            ceiling = (d["av_cur"] * d["width"]).sum(axis=0)
            bind = (d["imp_cur"] >= ceiling - 1e-6) & (ceiling > 1e-6)
            # MARGINAL: a band that is in the money but whose availability the
            # envelope has zeroed — the envelope, not the price, is what stops
            # the next MW.
            marg = (inmoney & (d["av_cur"] <= 1e-9)).any(axis=0)
            q2[seam] = (bind, marg)
            print(
                f"    {seam:>9} {100 * bind.mean():8.1f}% "
                f"{100 * bind[np.isin(rh, NIGHT)].mean():8.1f}% "
                f"{100 * bind[np.isin(rh, PEAK)].mean():7.1f}% | "
                f"{100 * marg.mean():8.1f}% "
                f"{100 * marg[np.isin(rh, NIGHT)].mean():8.1f}% "
                f"{100 * marg[np.isin(rh, PEAK)].mean():7.1f}%"
            )

        # ---- Q3 candidate held-price effect ------------------------------
        c_cur = hod_corr(rec_cur, act)
        c_can = hod_corr(rec_can, act)
        print("\nQ3  candidate C1, HELD-PRICE (upper bound on the correction)")
        print(
            f"    hour-of-day corr vs measured net interchange: "
            f"current {c_cur:+.3f}  ->  candidate {c_can:+.3f}   "
            f"(delta {c_can - c_cur:+.3f})"
        )
        for seam, d in per_seam.items():
            dn = (d["imp_can"] - d["imp_cur"])[np.isin(rh, NIGHT)].mean()
            dp = (d["imp_can"] - d["imp_cur"])[np.isin(rh, PEAK)].mean()
            print(
                f"    {seam:>9}  night {dn:+8.0f} MW   peak {dp:+8.0f} MW   "
                f"energy {(d['imp_can'].sum() - d['imp_cur'].sum()) / 1e6:+7.3f} TWh"
            )

        # ---- Q4 KILL-13 --------------------------------------------------
        print("\nQ4  KILL-13 (rule 13 [R-MEASURED])")
        for seam, d in per_seam.items():
            ceil_can = (d["av_can"] * d["width"]).sum(axis=0)
            # (a) headroom collapse: does the candidate's band sum reproduce the
            #     cell-conditional MEAN measured flow?
            cell_mean = np.zeros(8760)
            for m in range(12):
                for h in range(24):
                    sel = (rm == m) & (rh == h)
                    if sel.any():
                        cell_mean[sel] = max(d["flow"][sel].mean(), 0.0)
            ok = cell_mean > 1e-6
            near = np.abs(ceil_can[ok] - cell_mean[ok]) / cell_mean[ok] < 0.05
            share_a = 100 * near.mean() if ok.any() else 0.0
            # (b) choice extinguished: candidate ceiling binds in > 70 % of hours
            bind_can = (d["imp_can"] >= ceil_can - 1e-6) & (ceil_can > 1e-6)
            print(
                f"    {seam:>9}  (a) candidate ceiling within 5% of the cell MEAN "
                f"in {share_a:5.1f}% of cells   "
                f"(b) ceiling binds {100 * bind_can.mean():5.1f}% of hours"
            )
            # Also report the p90 ceiling's own headroom, for contrast.
            ceil_cur = (d["av_cur"] * d["width"]).sum(axis=0)
            print(
                f"    {'':>9}      armed p90 ceiling mean {ceil_cur.mean():8.0f} MW "
                f"vs candidate {ceil_can.mean():8.0f} MW "
                f"vs measured mean {max(d['flow'].mean(), 0):8.0f} MW"
            )

        # ---- Q5 annual energy integrity ----------------------------------
        ratio_cur = rec_cur.sum() / act.sum()
        ratio_can = rec_can.sum() / act.sum()
        print(
            f"\nQ5  annual net-import energy ratio (reconstruction/measured): "
            f"current {ratio_cur:.3f}  ->  candidate {ratio_can:.3f}"
        )
        print(
            f"    keeper solved import class ratio: "
            f"{keeper_imp.sum() / act.sum():.3f}  (the scored number)"
        )

        # ---- Q6 reachable vs unreachable mis-shape ------------------------
        mis_n = rec_cur[np.isin(rh, NIGHT)].mean() - act[np.isin(rh, NIGHT)].mean()
        mis_p = rec_cur[np.isin(rh, PEAK)].mean() - act[np.isin(rh, PEAK)].mean()
        d_n = (rec_can - rec_cur)[np.isin(rh, NIGHT)].mean()
        d_p = (rec_can - rec_cur)[np.isin(rh, PEAK)].mean()
        print("\nQ6  reachable share of the measured mis-shape (a CEILING can only cut)")
        print(
            f"    night mis-shape {mis_n:+8.0f} MW   candidate moves {d_n:+8.0f} MW   "
            f"({'toward' if mis_n * d_n < 0 else 'AWAY FROM'} reality)"
        )
        print(
            f"    peak  mis-shape {mis_p:+8.0f} MW   candidate moves {d_p:+8.0f} MW   "
            f"({'toward' if mis_p * d_p < 0 else 'AWAY FROM'} reality)"
        )

        # ---- Q6b bound over the ENTIRE ceiling class ----------------------
        # An availability ceiling can only REDUCE cleared flow. The best any
        # ceiling whatsoever could do, holding price fixed, is to cut exactly
        # down to the measured flow in every hour the model is long and cut
        # nothing where it is short: cleared = min(current, measured). That
        # construction is an OUTCOME PIN and is forbidden by rule 13 — it is
        # computed here ONLY as an unattainable upper bound, never armed, so
        # the result bounds the whole ceiling class rather than candidate C1
        # alone.
        rec_bound = np.minimum(rec_cur, act)
        print(
            f"    CEILING-CLASS BOUND (forbidden outcome pin, diagnostic only): "
            f"hod corr {hod_corr(rec_bound, act):+.3f}   "
            f"energy ratio {rec_bound.sum() / act.sum():.3f}"
        )
        summary[year] = dict(
            r0=r, c_cur=c_cur, c_can=c_can, ratio_cur=ratio_cur, ratio_can=ratio_can
        )

    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}")
    for year, s in summary.items():
        print(
            f"  {year}: recon r={s['r0']:+.3f}  hod corr {s['c_cur']:+.3f} -> "
            f"{s['c_can']:+.3f}   energy ratio {s['ratio_cur']:.3f} -> "
            f"{s['ratio_can']:.3f}"
        )


if __name__ == "__main__":
    main()
