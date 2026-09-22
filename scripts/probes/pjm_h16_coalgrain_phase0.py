"""pjm-h16 phase 0 — PJM's OWN coal commitment-grain census. ZERO LP.

The object is the window's GRAIN, not its size. pjm-h15 repaired the window's
VINTAGE (which year's measured share sizes it) and proved at the solver that it
cannot reach three of the four D-4 coal conduct failures: 1040/2020, 7213/2021
and 1384/2023 all carry an own-year fraction that is NOT lower than pooled, so
the plant RAN that year — just not in the top-system-load hours
``arrays.py::_compose_min_gen_floors`` selects. That is PLACEMENT.

The incumbent coal synchronization window is ``load_rank[:k]`` — the top ``k``
INDIVIDUAL HOURS by system load — so the floor carries the diurnal shape of
LOAD. A coal unit's synchronization is a whole-operating-day decision. This
probe measures, from PJM's own CAMPD record and the keeper's own committed
system load, whether that is true of PJM coal (rule 28(d): SPP's ST_GAS census
fills no PJM cell, and its verdict is not transferable).

Sections
 1. ONLINE HOUR-OF-DAY PROFILE, per covered coal plant x year — peak-to-mean
    of P(online | hour-of-day). Flat => a synchronized coal unit runs through
    the overnight trough, and an hour-ranked window is the wrong shape.
 2. IMPLIED STARTS — contiguous blocks in the incumbent window, against the
    plant's OWN metered starts (rule 18 [R-PHYSICS]). A day-grain window's
    implied starts are reported beside them.
 3. THE SHARP TEST, actuals only — what the real plant generates in the hours
    the hour-grain window HOLDS but a day-grain window RELEASES, against the
    hours the day grain HOLDS but the hour grain RELEASES.
 4. D-4 CONDUCT under both windows on the committed failing rows — the
    statistic the rule-17 rider actually scores.

Usage:
    python3 scripts/probes/pjm_h16_coalgrain_phase0.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

POOLED = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
BY_YEAR = (
    REPO / "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_PJM.csv"
)
SPAN = REPO / "results/calibration/pjm_h15_coalwindow_span"
TOUCH = REPO / "results/calibration/pjm_h15_coalwindow_touchpoint"
YEARS = list(range(2020, 2026))
FORCE_ALL = 0.99  # withholding._COAL_SYNC_FORCE_ALL


def bundle_for(year: int) -> Path:
    return SPAN if year >= 2023 else TOUCH


def system_load(year: int) -> np.ndarray:
    """The keeper's own hourly system load — zonal demand summed, P1.

    The identical series ``_compose_min_gen_floors`` ranks hours by (the PJM
    keeper does not arm ``commitment_floor_window_netload``, so
    ``_window_shape`` resolves to ``load_shape``).
    """
    df = pd.read_parquet(bundle_for(year) / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    s = df.groupby("hour")["demand"].sum().sort_index()
    return s.to_numpy(dtype=float)


def hour_window(load: np.ndarray, frac: float) -> np.ndarray:
    """The INCUMBENT window: the top-k hours by system load."""
    if frac >= FORCE_ALL:
        return np.arange(len(load))
    k = int(round(frac * len(load)))
    return np.argsort(-load, kind="stable")[:k] if k > 0 else np.empty(0, dtype=int)


def day_window(load: np.ndarray, frac: float) -> np.ndarray:
    """The DAY-GRAIN window: round(k/24) whole days by day-MEAN system load.

    The mechanical lift of ``_mustrun_window_hours`` / ``_commitment_day_order``
    (spp-27) to the coal seam — same signal, same ordering statistic, one grain
    coarser.
    """
    hours = len(load)
    if frac >= FORCE_ALL:
        return np.arange(hours)
    k = int(round(frac * hours))
    if k <= 0:
        return np.empty(0, dtype=int)
    days = hours // 24
    key = load[: days * 24].reshape(days, 24).mean(axis=1)
    order = np.argsort(-key, kind="stable")
    n_days = int(min(days, max(1, round(k / 24.0))))
    starts = order[:n_days] * 24
    return (starts[:, None] + np.arange(24)[None, :]).ravel()


def hod_peak_to_mean(mask: np.ndarray) -> float:
    """peak-to-mean of a boolean hourly mask's hour-of-day profile."""
    n = len(mask) // 24 * 24
    prof = mask[:n].reshape(-1, 24).mean(axis=0)
    m = prof.mean()
    return float(prof.max() / m) if m > 0 else float("nan")


def night_afternoon_share(mask: np.ndarray) -> float:
    """Overnight (00-05) on-share / afternoon (14-19) on-share.

    spp-27's second diurnal statistic. ~1.0 => the unit runs through the
    trough; << 1.0 => it two-shifts.
    """
    n = len(mask) // 24 * 24
    prof = mask[:n].reshape(-1, 24).mean(axis=0)
    aft = prof[14:20].mean()
    return float(prof[0:6].mean() / aft) if aft > 0 else float("nan")


def starts(mask: np.ndarray) -> int:
    """Off -> on transitions in a boolean hourly mask (linear, not circular)."""
    m = np.asarray(mask, dtype=bool)
    return int(m[0]) + int(np.count_nonzero(m[1:] & ~m[:-1]))


def to_mask(hrs: np.ndarray, hours: int) -> np.ndarray:
    m = np.zeros(hours, dtype=bool)
    if hrs.size:
        m[hrs] = True
    return m


def conduct(series: np.ndarray, hrs: np.ndarray) -> tuple[float, float]:
    """(median measured MW, zero-share) over ``hrs`` — the D-4 conduct operand."""
    if hrs.size == 0:
        return float("nan"), float("nan")
    v = series[hrs]
    return float(np.median(v)), float((v <= 0.0).mean())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--years", nargs="+", type=int, default=YEARS)
    args = ap.parse_args()

    pooled = pd.read_csv(POOLED)
    pooled = pooled[pooled.plant_group == "COAL"]
    pmap: dict[int, float] = {}
    npl: dict[int, float] = {}
    for r in pooled.itertuples(index=False):
        try:
            f = float(r.online_frac)
        except (TypeError, ValueError):
            continue
        if f == f:
            pmap[int(r.plant_code)] = f
            npl[int(r.plant_code)] = float(r.nameplate_mw)

    by = pd.read_csv(BY_YEAR)
    by = by[by.plant_group == "COAL"]
    omap = {
        (int(r.plant_code), int(r.year)): float(r.online_frac)
        for r in by.itertuples(index=False)
        if float(r.online_frac) == float(r.online_frac)
    }

    states = campd.states_for_iso("PJM")
    factors = dtt._parasitic_factor_map()

    rows: list[dict] = []
    for year in args.years:
        load = system_load(year)
        hours = len(load)
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, factors, year)
        for code, pf in sorted(pmap.items()):
            # THE ARMED KEEPER's window size: coal_sync_online_frac_per_year is
            # True on 2026-09-20-pjm-h15-coalwindow-span, so the SIZE is the
            # solve year's own measured share. The grain question is asked at
            # that size (rule 19 [R-ONE-MECH]: size is not re-opened).
            frac = omap.get((code, year), pf)
            series = net.get(code)
            if series is None:
                continue
            series = np.asarray(series, dtype=float)[:hours]
            if len(series) < hours:
                series = np.pad(series, (0, hours - len(series)))
            online = series > 0.0
            if frac <= 0.0 or frac >= FORCE_ALL:
                # frac >= FORCE_ALL floors all 8760 h and has no window to
                # place; frac == 0 carries no floor. Both are out of reach and
                # are reported so the unreachable population is named, not
                # quietly dropped (rule 1 / the charter's reach clause).
                rows.append(
                    dict(
                        year=year,
                        plant=code,
                        nameplate_mw=round(npl[code], 1),
                        frac=round(frac, 3),
                        k=0,
                        reach=False,
                        metered_twh=round(float(series.sum()) / 1e6, 4),
                        online_share=round(float(online.mean()), 4),
                        p2m_online=round(hod_peak_to_mean(online), 4),
                        na_online=round(night_afternoon_share(online), 4),
                        starts_meter=starts(online),
                    )
                )
                continue
            hw = hour_window(load, frac)
            dw = day_window(load, frac)
            hm, dm = to_mask(hw, hours), to_mask(dw, hours)
            only_h = hm & ~dm
            only_d = dm & ~hm
            mh, zh = conduct(series, hw)
            md, zd = conduct(series, dw)
            rows.append(
                dict(
                    year=year,
                    plant=code,
                    nameplate_mw=round(npl[code], 1),
                    frac=round(frac, 3),
                    k=int(hw.size),
                    k_day=int(dw.size),
                    reach=True,
                    metered_twh=round(float(series.sum()) / 1e6, 4),
                    online_share=round(float(online.mean()), 4),
                    # --- 1. diurnal shape: the plant vs the window it gets ---
                    p2m_online=round(hod_peak_to_mean(online), 4),
                    na_online=round(night_afternoon_share(online), 4),
                    p2m_hourwin=round(hod_peak_to_mean(hm), 4),
                    p2m_daywin=round(hod_peak_to_mean(dm), 4),
                    # --- 2. implied starts ---
                    starts_meter=starts(online),
                    starts_hourwin=starts(hm),
                    starts_daywin=starts(dm),
                    # --- 3. the sharp test ---
                    n_only_h=int(only_h.sum()),
                    n_only_d=int(only_d.sum()),
                    mw_only_h=round(
                        float(series[only_h].mean()) if only_h.any() else np.nan, 1
                    ),
                    mw_only_d=round(
                        float(series[only_d].mean()) if only_d.any() else np.nan, 1
                    ),
                    on_only_h=round(
                        float(online[only_h].mean()) if only_h.any() else np.nan, 4
                    ),
                    on_only_d=round(
                        float(online[only_d].mean()) if only_d.any() else np.nan, 4
                    ),
                    # --- 4. D-4 conduct operand ---
                    med_hour=round(mh, 2),
                    zero_hour=round(zh, 4),
                    med_day=round(md, 2),
                    zero_day=round(zd, 4),
                )
            )

    d = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 60)

    r = d[d.reach]
    nr = d[~d.reach]

    print("### 0. POPULATION — what the grain gate can and cannot reach\n")
    print(f"    covered coal plant-years in the artifact : {len(d)}")
    print(f"    REACHABLE (0 < frac < {FORCE_ALL}, a window exists)  : {len(r)}")
    print(f"    UNREACHABLE (frac >= {FORCE_ALL}: floored all 8760 h): {len(nr)}")
    if len(nr):
        print("\n    unreachable plant-years (no window to place):")
        print(
            nr[
                [
                    "year",
                    "plant",
                    "nameplate_mw",
                    "frac",
                    "metered_twh",
                    "online_share",
                    "p2m_online",
                ]
            ].to_string(index=False)
        )

    print(
        "\n\n### 1. DIURNAL SHAPE — the plant's own online profile vs the window it is given\n"
    )
    print(
        "    p2m_online  = peak-to-mean of P(online | hour-of-day), from the plant's OWN meter"
    )
    print("    na_online   = overnight(00-05) on-share / afternoon(14-19) on-share")
    print("    p2m_hourwin = the same statistic for the INCUMBENT top-k-hours window")
    print("    p2m_daywin  = the same statistic for a whole-operating-day window\n")
    print(
        r[
            [
                "year",
                "plant",
                "nameplate_mw",
                "frac",
                "k",
                "online_share",
                "p2m_online",
                "na_online",
                "p2m_hourwin",
                "p2m_daywin",
            ]
        ].to_string(index=False)
    )

    print("\n    FLEET SUMMARY (reachable plant-years):")
    print(
        f"      p2m_online : min {r.p2m_online.min():.3f}  median {r.p2m_online.median():.3f}"
        f"  max {r.p2m_online.max():.3f}"
    )
    print(
        f"      na_online  : min {r.na_online.min():.3f}  median {r.na_online.median():.3f}"
        f"  max {r.na_online.max():.3f}"
    )
    print(
        f"      p2m_hourwin: min {r.p2m_hourwin.min():.3f}  median {r.p2m_hourwin.median():.3f}"
        f"  max {r.p2m_hourwin.max():.3f}"
    )
    print(
        f"      p2m_daywin : min {r.p2m_daywin.min():.3f}  median {r.p2m_daywin.median():.3f}"
        f"  max {r.p2m_daywin.max():.3f}"
    )
    flat = int((r.p2m_online <= 1.25).sum())
    print(
        f"      plant-years with a FLAT own profile (p2m_online <= 1.25): {flat}/{len(r)}"
    )
    worse = int((r.p2m_hourwin > r.p2m_online).sum())
    print(
        f"      plant-years where the WINDOW is more peaked than the PLANT: {worse}/{len(r)}"
    )

    print("\n\n### 2. IMPLIED STARTS — rule 18 [R-PHYSICS]\n")
    s = r.groupby("year").agg(
        plant_years=("plant", "count"),
        starts_meter=("starts_meter", "sum"),
        starts_hourwin=("starts_hourwin", "sum"),
        starts_daywin=("starts_daywin", "sum"),
    )
    s["hour_x_meter"] = (s.starts_hourwin / s.starts_meter.clip(lower=1)).round(2)
    s["day_x_meter"] = (s.starts_daywin / s.starts_meter.clip(lower=1)).round(2)
    print(s.to_string())
    print("\n    WORST per-plant-year over-implication under the incumbent window:")
    w = r.assign(ratio=(r.starts_hourwin / r.starts_meter.clip(lower=1)).round(2))
    print(
        w.nlargest(10, "ratio")[
            [
                "year",
                "plant",
                "nameplate_mw",
                "k",
                "starts_meter",
                "starts_hourwin",
                "starts_daywin",
                "ratio",
            ]
        ].to_string(index=False)
    )

    print(
        "\n\n### 3. THE SHARP TEST — actuals only, in the hours the two grains DISAGREE\n"
    )
    print("    only_h = the incumbent window HOLDS the floor, a day window RELEASES it")
    print("    only_d = a day window HOLDS the floor, the incumbent RELEASES it")
    print(
        "    mw_* = the plant's OWN mean metered MW there; on_* = its online frequency\n"
    )
    t = r.dropna(subset=["mw_only_h", "mw_only_d"])
    agg = t.groupby("year").apply(
        lambda g: pd.Series(
            dict(
                plant_years=len(g),
                n_only_h=int(g.n_only_h.sum()),
                n_only_d=int(g.n_only_d.sum()),
                mw_only_h=float(
                    (g.mw_only_h * g.n_only_h).sum() / max(1, g.n_only_h.sum())
                ),
                mw_only_d=float(
                    (g.mw_only_d * g.n_only_d).sum() / max(1, g.n_only_d.sum())
                ),
                on_only_h=float(
                    (g.on_only_h * g.n_only_h).sum() / max(1, g.n_only_h.sum())
                ),
                on_only_d=float(
                    (g.on_only_d * g.n_only_d).sum() / max(1, g.n_only_d.sum())
                ),
            )
        ),
        include_groups=False,
    )
    agg["d_mw"] = (agg.mw_only_d - agg.mw_only_h).round(1)
    print(agg.round(4).to_string())
    win = int((t.mw_only_d > t.mw_only_h).sum())
    print(
        f"\n    plant-years where the DAY-only hours carry MORE real output: {win}/{len(t)}"
    )
    print(
        f"    fleet-weighted mean MW  only_h {float((t.mw_only_h * t.n_only_h).sum() / t.n_only_h.sum()):.1f}"
        f"   only_d {float((t.mw_only_d * t.n_only_d).sum() / t.n_only_d.sum()):.1f}"
    )
    print(
        f"    fleet-weighted on-freq  only_h {float((t.on_only_h * t.n_only_h).sum() / t.n_only_h.sum()):.4f}"
        f"   only_d {float((t.on_only_d * t.n_only_d).sum() / t.n_only_d.sum()):.4f}"
    )
    print(
        f"    hour-set overlap: {100.0 * (1 - t.n_only_h.sum() / t.k.sum()):.1f}% of the incumbent "
        f"window's hours are shared with the day window"
    )

    print("\n\n### 4. D-4 CONDUCT on the committed failing rows, both grains\n")
    dj = json.loads((SPAN / "legitimacy_diagnostics.json").read_text())
    dj2 = json.loads((TOUCH / "legitimacy_diagnostics.json").read_text())
    d4 = [
        rr
        for src in (dj, dj2)
        for rr in src["diagnostics"]["D4"]["rows"]
        if rr.get("floor") == "coal_mustrun" and rr.get("check") == "unit-conduct"
    ]
    chk = []
    for rr in d4:
        code, yr = int(rr["plant"]), int(rr["year"])
        m = d[(d.plant == code) & (d.year == yr)]
        if m.empty:
            continue
        m = m.iloc[0]
        chk.append(
            dict(
                year=yr,
                plant=code,
                verdict=rr.get("verdict"),
                binding_hours=int(rr.get("binding_hours", 0)),
                d4_median=float(rr.get("measured_median_mw", float("nan"))),
                reach=bool(m.reach),
                frac=float(m.frac),
                med_hour=float(m.get("med_hour", float("nan"))),
                med_day=float(m.get("med_day", float("nan"))),
                zero_hour=float(m.get("zero_hour", float("nan"))),
                zero_day=float(m.get("zero_day", float("nan"))),
            )
        )
    c = pd.DataFrame(chk).sort_values(["verdict", "year", "plant"])
    print(c.to_string(index=False))
    f = c[c.verdict != "pass"]
    if len(f):
        print(
            f"\n    FAILING rows: {len(f)}; reachable by a grain change: {int(f.reach.sum())}"
        )
        print(
            f"    of the reachable failing rows, median moves UP under the day grain on "
            f"{int((f[f.reach].med_day > f[f.reach].med_hour).sum())}/{int(f.reach.sum())}"
        )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(dict(rows=rows, d4=chk), indent=1, default=float)
        )
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
