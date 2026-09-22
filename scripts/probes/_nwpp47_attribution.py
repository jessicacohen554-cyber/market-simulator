"""nwpp-47 (ZERO LP): plant-level attribution of the NWPP demand-basis gap.

Owner ruling on FINDING-nwpp-45 §8 = framing 1: resolve the GRID / generation-
only-BA attribution from plant-level evidence and rebuild the subtrahend.
Reproduces every table in ``docs/handoffs/FINDING-nwpp-47-2026-09-22.md``:

  A. GRID's four export legs against GRID's own EIA-930 fuel book and CAMPD
     hourly plant output: PNM == GRID NG: WND (hour by hour), BPAT == Centralia
     + Hermiston, SRP + WALC == Desert-Southwest gas.
  B. Per footprint BA: EIA-930 fossil net generation against the CEMS gross
     output of the plants eGRID hosts there (control BAs close at 0.95-1.0).
  C. Is the missing NW gas booked in CAISO / BANC? Their own-plant residual,
     regressed on footprint plants.
  D. The footprint's external legs, member-reported vs the counterparty's own
     mirror (national EIA-930 INTERCHANGE bulk files, keyless; ``--ic-dir``
     caches them, ~100 MB per half-year).
  E. Where the arm's energy goes: model wind vs the pool wind it carries.

Non-negative least squares here is a small numpy active-set loop (the stack
forbids ``scipy.optimize``); it is a diagnostic attribution, not an estimator
anything downstream consumes.

Run: ``PYTHONPATH=.:src python3 scripts/probes/_nwpp47_attribution.py
--ic-dir /tmp/eia930-ic``   (DATA PROFILE: nwpp, plus AZ/NM/CA CAMPD)
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

YEARS = (2023, 2024, 2025)
CAMPD = Path("data/raw/campd-unit-level")
BAL = Path("data/raw/eia-930")
GRID_IC = Path("data/raw/eia-930-interchange/GRID interchange hourly.parquet")
#: CAMPD hour is hour-BEGINNING local STANDARD time; offset to UTC by state.
STATE_UTC_OFFSET = {"WA": 8, "OR": 8, "NV": 8, "CA": 8, "ID": 7, "MT": 7,
                    "UT": 7, "WY": 7, "AZ": 7, "NM": 7}
IC_URL = ("https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
          "EIA930_INTERCHANGE_{y}_{h}.csv")


def nnls(x: np.ndarray, y: np.ndarray, iters: int = 200) -> np.ndarray:
    """Active-set non-negative least squares (drop the most negative, re-solve)."""
    active = np.ones(x.shape[1], dtype=bool)
    beta = np.zeros(x.shape[1])
    for _ in range(iters):
        if not active.any():
            break
        b, *_ = np.linalg.lstsq(x[:, active], y, rcond=None)
        if (b >= 0).all():
            beta[:] = 0.0
            beta[active] = b
            break
        idx = np.flatnonzero(active)
        active[idx[np.argmin(b)]] = False
    return beta


def campd_hourly(year: int, fuel: str | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Plant-hourly CEMS gross MW on the UTC hour-ending clock, and plant names."""
    frames = []
    for st, off in STATE_UTC_OFFSET.items():
        path = CAMPD / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        d = pd.read_parquet(path, columns=["facilityName", "facilityId", "date",
                                           "hour", "grossLoad", "primaryFuelInfo"])
        d["u"] = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"] + off + 1, unit="h")
        frames.append(d)
    d = pd.concat(frames)
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d["facilityId"] = d["facilityId"].astype(int)
    coal = d["primaryFuelInfo"].str.contains("Coal", na=False)
    if fuel == "COL":
        d = d[coal]
    elif fuel == "GAS":
        d = d[~coal]
    wide = d.groupby(["u", "facilityId"])["grossLoad"].sum().unstack().fillna(0.0)
    return wide, d.groupby("facilityId")["facilityName"].first()


def balance(year: int) -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(BAL / f"EIA930_BALANCE_{year}_{h}.parquet")
                   for h in ("Jan_Jun", "Jul_Dec")])
    b["u"] = pd.to_datetime(b["UTC Time at End of Hour"])
    return b[b["u"].dt.year == year]


def member(ba: str, year: int) -> pd.DataFrame:
    """A footprint member's committed hourly extract (what the model reads), UTC-indexed.

    Preferred over the national BALANCE files for fuel columns: EIA renamed the
    wind / solar columns in the 2024-H2+ BALANCE halves ("with / without
    Integrated Battery Storage"), and the NWPP-11 extracts already reconcile
    both halves.
    """
    x = pd.read_parquet(Path("data/raw/eia-930-hourly") / f"{ba} hourly.parquet")
    x = x.drop_duplicates("UTC time").set_index(pd.DatetimeIndex(x["UTC time"]))
    return x[x.index.year == year]


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")


def grid_legs(year: int) -> pd.DataFrame:
    f = pd.read_parquet(GRID_IC)
    out = {}
    for diba, leg in f.groupby("diba"):
        st = pd.DatetimeIndex(leg["local_time"])
        try:
            u = st.tz_localize("America/Los_Angeles", ambiguous="infer",
                               nonexistent="shift_forward")
        except Exception:
            u = st.tz_localize("America/Los_Angeles", ambiguous=False,
                               nonexistent="shift_forward")
        s = pd.Series(leg["mw"].to_numpy(float), index=u.tz_convert("UTC").tz_localize(None))
        out[diba] = s[~s.index.duplicated()]
    legs = pd.DataFrame(out)
    return legs[legs.index.year == year].fillna(0.0)


def section_a(year: int) -> None:
    """GRID's legs against its own fuel book and CEMS plant output."""
    legs = grid_legs(year)
    g = member("GRID", year)
    fuel = pd.DataFrame({k: g[f"NG: {v}"].astype(float)
                         for k, v in {"COL": "COL", "GAS": "NG",
                                      "WND": "WND", "SUN": "SUN"}.items()})
    j = legs.join(fuel, how="inner").fillna(0.0)
    print(f"\n[A] {year} GRID legs (TWh): " + "  ".join(
        f"{c} {j[c].sum() / 1e6:.3f}" for c in legs.columns))
    print(f"    fuel book: COL {j.COL.sum()/1e6:.3f}  GAS {j.GAS.sum()/1e6:.3f}  "
          f"WND {j.WND.sum()/1e6:.3f}  SUN {j.SUN.sum()/1e6:.3f}")
    print(f"    PNM leg vs GRID wind: r={np.corrcoef(j.PNM, j.WND)[0, 1]:.5f}  "
          f"max|diff| {np.abs(j.PNM - j.WND).max():.1f} MW")
    plants, names = campd_hourly(year)
    plants = plants.reindex(j.index).fillna(0.0)
    if 3845 in plants.columns:
        print(f"    GRID coal vs Centralia (3845) gross: "
              f"r={np.corrcoef(j.COL, plants[3845])[0, 1]:.4f}")
    x = plants.loc[:, plants.sum() > 2e5]
    for label, target in (("SRP+WALC", j.SRP + j.WALC),
                          ("BPAT - coal - solar", j.BPAT - j.COL - j.SUN)):
        beta = nnls(x.to_numpy(), target.to_numpy())
        fit = x.to_numpy() @ beta
        print(f"    {label}: {target.sum()/1e6:.3f} TWh, NNLS r={np.corrcoef(fit, target)[0, 1]:.3f}")
        contrib = pd.Series(beta * x.sum().to_numpy() / 1e6, index=x.columns)
        for fid, v in contrib.sort_values(ascending=False).head(6).items():
            if v > 0.05:
                print(f"      {fid:>6} {names[fid][:30]:30} {v:.3f}")


def section_b(year: int, egrid_host: dict[int, str]) -> None:
    """Per footprint BA: 930 fossil NG vs hosted-plant CEMS gross."""
    from market_sim.data.fleet.models import NWPP_BAS

    g = pd.DataFrame({ba: {"COL": member(ba, year)["NG: COL"].sum() / 1e6,
                           "GAS": member(ba, year)["NG: NG"].sum() / 1e6}
                      for ba in sorted(NWPP_BAS)}).T
    rows = []
    for fuel in ("COL", "GAS"):
        w, _ = campd_hourly(year, fuel)
        tot = w.sum() / 1e6
        by_ba = tot.groupby(tot.index.map(lambda f: egrid_host.get(int(f)))).sum()
        rows.append(by_ba.rename(fuel))
    cem = pd.concat(rows, axis=1).fillna(0.0)
    print(f"\n[B] {year} 930 net / hosted CEMS gross (TWh)")
    t = np.zeros(4)
    for ba in sorted(NWPP_BAS):
        r = [g.loc[ba, "COL"] if ba in g.index else 0.0,
             cem.loc[ba, "COL"] if ba in cem.index else 0.0,
             g.loc[ba, "GAS"] if ba in g.index else 0.0,
             cem.loc[ba, "GAS"] if ba in cem.index else 0.0]
        t += r
        if max(r) > 0.05:
            ratio = r[2] / r[3] if r[3] else float("nan")
            print(f"    {ba:5} COL {r[0]:6.2f}/{r[1]:6.2f}   GAS {r[2]:6.2f}/{r[3]:6.2f}  ratio {ratio:4.2f}")
    print(f"    TOTAL COL {t[0]:.2f}/{t[1]:.2f} ({t[0]/t[1]:.3f})   GAS {t[2]:.2f}/{t[3]:.2f} ({t[2]/t[3]:.3f})")


def section_c(year: int, egrid_host: dict[int, str]) -> None:
    """Is footprint gas booked in CISO / BANC? Own-plant fit, residual vs NWPP plants."""
    from market_sim.data.fleet.models import NWPP_BAS

    w, _ = campd_hourly(year, "GAS")
    b = balance(year)
    nw = [c for c in w.columns if egrid_host.get(int(c)) in NWPP_BAS and w[c].sum() > 2e5]
    for ba in ("CISO", "BANC"):
        y = num(b[b["Balancing Authority"] == ba].set_index("u")[
            "Net Generation (MW) from Natural Gas (Adjusted)"]).dropna()
        idx = y.index.intersection(w.index)
        own = [c for c in w.columns if egrid_host.get(int(c)) == ba and w[c].sum() > 1e4]
        xo = w.loc[idx, own].to_numpy()
        res = y.loc[idx].to_numpy() - xo @ nnls(xo, y.loc[idx].to_numpy())
        xn = w.loc[idx, nw].to_numpy()
        fit = xn @ nnls(xn, np.clip(res, 0, None))
        print(f"\n[C] {year} {ba}: 930 gas {y.sum()/1e6:.2f}; own-plant residual "
              f"{res.sum()/1e6:+.2f} TWh; residual vs NWPP plants r={np.corrcoef(fit, res)[0, 1]:.3f}")


def section_d(year: int, ic_dir: Path) -> None:
    """External legs: member-reported vs counterparty mirror."""
    from market_sim.data.fleet.models import NWPP_BAS

    ic_dir.mkdir(parents=True, exist_ok=True)
    parts = []
    for h in ("Jan_Jun", "Jul_Dec"):
        path = ic_dir / f"EIA930_INTERCHANGE_{year}_{h}.csv"
        if not path.exists():
            urllib.request.urlretrieve(IC_URL.format(y=year, h=h), path)
        parts.append(pd.read_csv(path, usecols=[0, 3, 4, 6], thousands=","))
    ic = pd.concat(parts)
    ic.columns = ["ba", "diba", "mw", "utc"]
    ic["utc"] = pd.to_datetime(ic["utc"], format="%m/%d/%Y %I:%M:%S %p")
    ic = ic[ic["utc"].dt.year == year]
    ic["mw"] = pd.to_numeric(ic["mw"], errors="coerce")
    m = set(NWPP_BAS)
    own = ic[ic.ba.isin(m) & ~ic.diba.isin(m)].groupby(["ba", "diba"]).mw.sum() / 1e6
    mir = -ic[~ic.ba.isin(m) & ic.diba.isin(m)].groupby(["diba", "ba"]).mw.sum() / 1e6
    mir.index.names = ["ba", "diba"]
    t = pd.concat([own.rename("member"), mir.rename("mirror")], axis=1)
    best = t["mirror"].where(t["mirror"].notna(), t["member"])
    print(f"\n[D] {year} external legs (+ = footprint export), TWh")
    print(t.assign(diff=t.member - t.mirror).round(3).to_string())
    print(f"    member-reported {t.member.sum():.3f}  mirror-first {best.sum():.3f}  "
          f"unmirrored (Canada) {t.loc[t.mirror.isna(), 'member'].sum():.3f}")


def section_e() -> None:
    """The arm's energy: GRID's pool-carried wind, and the model supply that carries it."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.demand import load_demand
    from market_sim.data.eia930.envelopes import _nwpp_grid_pool_carried_wind
    from market_sim.data.eia930.frames import _pool_hourly_frame

    cfg = get_iso_config("NWPP")
    for year in YEARS:
        base = load_demand("NWPP", year, cfg).sum() / 1e6
        arm = load_demand("NWPP", year, cfg, nwpp_grid_carried_wind_served=True).sum() / 1e6
        pool_wind = float(_pool_hourly_frame("NWPP", year)["NG: WND"].sum()) / 1e6
        grid_wind = float(_nwpp_grid_pool_carried_wind(year).sum()) / 1e6
        print(f"\n[E] {year} LP demand {base:.3f} -> {arm:.3f} (+{arm - base:.3f});"
              f" pool wind {pool_wind:.3f} of which GRID {grid_wind:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ic-dir", default="/tmp/eia930-ic")
    ap.add_argument("--sections", default="ABCDE")
    args = ap.parse_args()
    host = {}
    for vint, sheet in ((2023, "PLNT23"),):
        e = pd.read_excel(f"data/raw/fleet-egrid/egrid{vint}_data_rev2.xlsx",
                          sheet_name=sheet, header=1, usecols=["ORISPL", "BACODE"]).dropna()
        host = dict(zip(e["ORISPL"].astype(int), e["BACODE"]))
    for year in YEARS:
        if "A" in args.sections:
            section_a(year)
        if "B" in args.sections:
            section_b(year, host)
        if "C" in args.sections and year == 2023:
            section_c(year, host)
        if "D" in args.sections:
            section_d(year, Path(args.ic_dir))
    if "E" in args.sections:
        section_e()


if __name__ == "__main__":
    main()
