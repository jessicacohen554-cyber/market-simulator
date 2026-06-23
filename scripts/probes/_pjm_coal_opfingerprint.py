"""Thread A (no LP solve): per-plant OPERATIONAL FINGERPRINT of PJM coal from
EPA CAMPD/CEMS hourly + PJM hourly hub LMP — the first-principles ground truth
for how PJM bituminous (and, with --rank waste/subbituminous, the rest of the
coal fleet) ACTUALLY operates, independent of the model.

For each plant (and the bituminous fleet aggregate) and year it answers the
Thread-A questions from docs/multi-iso/pjm-coal-economics-handoff-2026-06.md:

  1. Pmax proxy        — P99.5 of gross MW over the year (per unit, summed).
  2. Min sustained load— P5 of gross MW over ONLINE hours, as % of Pmax (real Pmin).
  3. Annual CF, and the CF duration curve (P95/P75/P50/P25/P5 of hourly CF).
  4. Cycling           — starts (offline->online transitions), median run-length
                         (consecutive online hrs), % hours < 50% / < 40% of Pmax,
                         and whether it two-shifts to zero.
  5. Diurnal / weekly  — overnight (00-05 ET) vs afternoon (13-18 ET) mean CF;
                         weekday vs weekend mean CF (the load-following signature).
  6. Price-conditional — mean CF in the lowest- vs highest-LMP quartile of hours
                         (Western Hub RT), and corr(hourly CF, LMP). The acid test
                         of "baseload price-taker" (ratio ~1, corr ~0) vs
                         "gas-following swing fuel" (ratio << 1, corr > 0).
  7. Ramp              — P99 of |hour-to-hour MW change| as % of Pmax.
  8. Part-load heat rate — CEMS heatInput / grossLoad across load-fraction bins
                         (the incremental HR(load) that should shape the offer slope).

Usage:
  .venv/bin/python scripts/probes/_pjm_coal_opfingerprint.py \
      [--rank bituminous] [--years 2023 2024 2025] [--top 12] [--out FILE.md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

CAMPD_UNIT_DIR = ROOT / "data" / "raw" / "campd-unit-level"

PJM_STATES = [
    "DC",
    "DE",
    "IL",
    "IN",
    "KY",
    "MD",
    "MI",
    "NC",
    "NJ",
    "OH",
    "PA",
    "TN",
    "VA",
    "WV",
]
COAL_SUPPLY_CSV = ROOT / "data" / "raw" / "_processed-legacy" / "coal_supply_PJM.csv"
LMP_CSV = ROOT / "data" / "raw" / "lmp-data" / "PJM_{year}_rt_da_monthly_lmps.csv"
LMP_HUB = "WESTERN HUB"  # liquid PJM trading hub; the coal belt sits in/near it


def _bit_plants(rank: str) -> set[int]:
    cs = pd.read_csv(COAL_SUPPLY_CSV)
    return set(int(p) for p in cs.loc[cs["supply_class"] == rank, "plant_code"])


def _campd_coal(year: int, cc: bool = False) -> pd.DataFrame:
    """Raw CAMPD unit-level rows for PJM states, year, with a timestamp.

    ``cc=False`` (default) keeps coal-fired units; ``cc=True`` keeps gas
    combined-cycle units (the Thread-E characterization).
    """
    frames = []
    for st in PJM_STATES:
        p = CAMPD_UNIT_DIR / f"{st}_{year}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
    df = pd.concat(frames, ignore_index=True)
    fuel = df["primaryFuelInfo"].astype(str)
    if cc:
        utype = df["unitType"].astype(str).str.lower()
        df = df[
            utype.str.contains("combined cycle")
            & fuel.str.contains("Gas", case=False, na=False)
        ].copy()
    else:
        df = df[fuel.str.contains("Coal", case=False, na=False)].copy()
    df["facilityId"] = df["facilityId"].astype(int)
    df["ts"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
    df["gross"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    df["heat"] = pd.to_numeric(df["heatInput"], errors="coerce").fillna(0.0)
    df["op"] = pd.to_numeric(df["opTime"], errors="coerce").fillna(0.0)
    return df


def _hub_lmp(year: int) -> pd.Series:
    """Western Hub RT total LMP indexed by EPT timestamp (hourly)."""
    df = pd.read_csv(str(LMP_CSV).format(year=year))
    df = df[df["pnode_name"] == LMP_HUB].copy()
    df["ts"] = pd.to_datetime(df["datetime_beginning_ept"])
    s = df.groupby("ts")["total_lmp_rt"].mean()
    return s.sort_index()


def _online_starts(online: np.ndarray) -> tuple[int, list[int]]:
    """# of offline->online transitions and the list of online run-lengths."""
    online = online.astype(bool)
    if not online.any():
        return 0, []
    padded = np.concatenate([[False], online, [False]])
    diff = np.diff(padded.astype(int))
    starts_idx = np.where(diff == 1)[0]
    ends_idx = np.where(diff == -1)[0]
    runs = (ends_idx - starts_idx).tolist()
    return int(len(starts_idx)), runs


def _plant_metrics(g: pd.DataFrame, lmp: pd.Series) -> dict:
    """Operational fingerprint for one plant-year. ``g`` = its CAMPD coal rows."""
    # Per-unit Pmax (P99.5 of gross), then plant gross MW per timestamp.
    units = g["unitId"].unique()
    pmax = 0.0
    for u in units:
        gu = g.loc[g["unitId"] == u, "gross"]
        if (gu > 0).any():
            pmax += float(np.nanpercentile(gu[gu > 0], 99.5))
    if pmax <= 0:
        return {}
    ts = g.groupby("ts").agg(
        gross=("gross", "sum"), heat=("heat", "sum"), op=("op", "sum")
    )
    ts = ts.sort_index()
    gross = ts["gross"].to_numpy(float)
    cf = gross / pmax
    online = gross > 0.02 * pmax

    # Min sustained load (real Pmin): P5 of gross over online hours, %Pmax.
    pmin_pct = (
        100.0 * np.nanpercentile(gross[online], 5) / pmax if online.any() else np.nan
    )
    n_online = int(online.sum())
    n_tot = len(gross)

    starts, runs = _online_starts(online)
    runs_arr = np.array(runs) if runs else np.array([0])

    # Diurnal / weekly.
    hod = ts.index.hour.to_numpy()
    dow = ts.index.dayofweek.to_numpy()
    overnight = cf[(hod >= 0) & (hod <= 5)].mean()
    afternoon = cf[(hod >= 13) & (hod <= 18)].mean()
    weekday = cf[dow < 5].mean()
    weekend = cf[dow >= 5].mean()

    # Price-conditional CF (merge on timestamp with the hub price).
    lp = lmp.reindex(ts.index)
    valid = lp.notna().to_numpy() & np.isfinite(cf)
    cfv, lpv = cf[valid], lp.to_numpy()[valid]
    if valid.sum() > 100:
        q1 = np.nanpercentile(lpv, 25)
        q4 = np.nanpercentile(lpv, 75)
        cf_lowp = cfv[lpv <= q1].mean()
        cf_hip = cfv[lpv >= q4].mean()
        corr = np.corrcoef(cfv, lpv)[0, 1]
    else:
        cf_lowp = cf_hip = corr = np.nan

    # Ramp: P99 of |delta gross| as %Pmax.
    dramp = 100.0 * np.nanpercentile(np.abs(np.diff(gross)), 99) / pmax

    # Part-load heat rate: heatInput(MMBtu)/gross(MWh) by load-fraction bin.
    hr_bins = {}
    online_mask = gross > 0.05 * pmax
    hr = np.where(
        gross > 0, ts["heat"].to_numpy(float) / np.maximum(gross, 1e-9), np.nan
    )
    frac = cf
    for lo, hi, lbl in [
        (0.30, 0.45, "30-45%"),
        (0.45, 0.60, "45-60%"),
        (0.60, 0.80, "60-80%"),
        (0.80, 1.01, "80-100%"),
    ]:
        m = online_mask & (frac >= lo) & (frac < hi) & np.isfinite(hr)
        hr_bins[lbl] = float(np.nanmedian(hr[m])) if m.sum() > 20 else np.nan

    annual_cf = gross.sum() / (pmax * n_tot)
    return {
        "pmax": pmax,
        "twh": gross.sum() / 1e6,
        "ann_cf": annual_cf,
        "pmin_pct": pmin_pct,
        "online_pct": 100.0 * n_online / n_tot,
        "starts": starts,
        "run_med": float(np.median(runs_arr)),
        "run_p90": float(np.percentile(runs_arr, 90)),
        "pct_lt50": 100.0 * np.mean((cf < 0.50) & online),
        "pct_lt40": 100.0 * np.mean((cf < 0.40) & online),
        "cf_p95": np.nanpercentile(cf, 95),
        "cf_p50": np.nanpercentile(cf, 50),
        "cf_p5": np.nanpercentile(cf, 5),
        "overnight": overnight,
        "afternoon": afternoon,
        "weekday": weekday,
        "weekend": weekend,
        "cf_lowp": cf_lowp,
        "cf_hip": cf_hip,
        "pc_ratio": cf_lowp / cf_hip if cf_hip and np.isfinite(cf_hip) else np.nan,
        "corr_lmp": corr,
        "ramp_p99": dramp,
        "hr_bins": hr_bins,
    }


def _fmt(x, nd=2):
    return f"{x:,.{nd}f}" if x is not None and np.isfinite(x) else "—"


def report(rank: str, years: list[int], top: int, cc: bool = False) -> str:
    plants = None if cc else _bit_plants(rank)
    label = "gas combined-cycle" if cc else f"{rank} coal"
    L: list[str] = [
        f"# PJM {label} — operational fingerprint (CAMPD/CEMS, no solve)",
        "",
    ]
    L += [f"Price reference: PJM {LMP_HUB} RT LMP. Pmax = P99.5 of unit gross MW.", ""]

    for year in years:
        cd = _campd_coal(year, cc=cc)
        if plants is not None:
            cd = cd[cd["facilityId"].isin(plants)]
        lmp = _hub_lmp(year)
        names = cd.groupby("facilityId")["facilityName"].first()

        rows = {}
        for pid, g in cd.groupby("facilityId"):
            m = _plant_metrics(g, lmp)
            if m:
                rows[pid] = m
        order = sorted(rows, key=lambda p: -rows[p]["twh"])[:top]

        L += [f"## {year}", ""]
        L += [
            "**Operation & cycling** (CF=capacity factor; Pmin=P5 online gross %Pmax)",
            "",
        ]
        L += [
            "| plant | id | Pmax MW | TWh | ann CF | Pmin% | online% | starts | run_med h | %hrs<50% | %hrs<40% |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for pid in order:
            m = rows[pid]
            L.append(
                f"| {names[pid]} | {pid} | {_fmt(m['pmax'], 0)} | {_fmt(m['twh'])} | "
                f"{_fmt(m['ann_cf'])} | {_fmt(m['pmin_pct'], 0)} | {_fmt(m['online_pct'], 0)} | "
                f"{m['starts']} | {_fmt(m['run_med'], 0)} | {_fmt(m['pct_lt50'], 0)} | {_fmt(m['pct_lt40'], 0)} |"
            )

        L += [
            "",
            "**Diurnal / weekly / PRICE-conditional** (the baseload-vs-swing test)",
            "",
        ]
        L += [
            "| plant | overnight CF | afternoon CF | wkday CF | wkend CF | CF lowP-q | CF hiP-q | low/hi | corr(CF,LMP) | ramp P99 %Pmax |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for pid in order:
            m = rows[pid]
            L.append(
                f"| {names[pid]} | {_fmt(m['overnight'])} | {_fmt(m['afternoon'])} | "
                f"{_fmt(m['weekday'])} | {_fmt(m['weekend'])} | {_fmt(m['cf_lowp'])} | "
                f"{_fmt(m['cf_hip'])} | {_fmt(m['pc_ratio'])} | {_fmt(m['corr_lmp'])} | "
                f"{_fmt(m['ramp_p99'], 0)} |"
            )

        # Fleet aggregate of the named plants.
        tot_twh = sum(rows[p]["twh"] for p in rows)
        w = {p: rows[p]["twh"] for p in rows}
        wsum = sum(w.values()) or 1.0

        def wavg(k):
            return (
                sum(rows[p][k] * w[p] for p in rows if np.isfinite(rows[p][k])) / wsum
            )

        L += [
            "",
            f"**Fleet ({len(rows)} plants, {_fmt(tot_twh)} TWh) GWh-weighted:** "
            f"ann CF {_fmt(wavg('ann_cf'))}, Pmin {_fmt(wavg('pmin_pct'), 0)}%, "
            f"overnight/afternoon CF {_fmt(wavg('overnight'))}/{_fmt(wavg('afternoon'))}, "
            f"low/hi-price CF ratio {_fmt(wavg('pc_ratio'))}, corr(CF,LMP) {_fmt(wavg('corr_lmp'))}.",
            "",
        ]

        # Part-load HR for the top few.
        L += [
            "**Part-load heat rate** (CEMS heatInput/gross, median MMBtu/MWh by load band)",
            "",
        ]
        L += [
            "| plant | 30-45% | 45-60% | 60-80% | 80-100% | Pmin penalty |",
            "|---|---|---|---|---|---|",
        ]
        for pid in order[:8]:
            hb = rows[pid]["hr_bins"]
            full = hb.get("80-100%")
            low = hb.get("30-45%") or hb.get("45-60%")
            pen = (
                (low / full - 1) * 100
                if full and low and np.isfinite(full) and np.isfinite(low)
                else np.nan
            )
            L.append(
                f"| {names[pid]} | {_fmt(hb.get('30-45%'))} | {_fmt(hb.get('45-60%'))} | "
                f"{_fmt(hb.get('60-80%'))} | {_fmt(hb.get('80-100%'))} | {_fmt(pen, 0)}% |"
            )
        L += [""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rank", default="bituminous")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument(
        "--cc",
        action="store_true",
        help="characterize gas combined-cycle units (Thread E) instead of coal",
    )
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    md = report(args.rank, args.years, args.top, cc=args.cc)
    if args.out:
        args.out.write_text(md)
        print(f"wrote {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
