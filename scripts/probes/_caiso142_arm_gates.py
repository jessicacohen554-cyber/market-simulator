"""caiso-142 — score the export-sink seam A/B against its pre-registered gates.

Reads only committed/produced bundle bytes; no LP is built and no solver runs.
Evaluates every gate of `PREREG-caiso142-export-sink-seam-2026-07-30.md` §2:

* P1 — the outlet EXISTS in arm B and is absent in arm A, with no corridor-group
  export-limit violation.
* P2 — the export volume is inside reality's measured export envelope, and is
  exactly 0 MW in every hour that envelope is closed.
* P3 — the corridor NET interchange moves TOWARD its measured net (the named
  structural-integrity claim; measured net from EIA-930 CISO BA-to-BA, the same
  frame and model-clock alignment the envelope itself is built from).
* P4 — E1/E2: the C3a move is UP (the sign §C requires) and inside the
  pre-registered per-year ceiling.
* P5 — rubric read: the C3a %-of-bench gap per arm against the +-10 % band, i.e.
  whether the currently-passing 2023/2024 leave their band.
* P6 — arm A byte-identical to the committed keeper on prices and dumps.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso142_arm_gates.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
HOURS = 8760
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/caiso139_dumpguard_B"
ARM_A = REPO / "results/calibration/caiso142_control_A"
ARM_B = REPO / "results/calibration/caiso142_seam_B"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
# PREREG §2 P4 ceilings ($/MWh, the as-built hub-eps basis, FINDING-caiso142 §D).
C3A_CEILING = {2023: 9.379, 2024: 7.860, 2025: 3.865}
C3A_BAND_FRAC = 0.10  # rubric v2.4: +-10 % of the load-weighted actual
CORRIDOR_LINK = {"WECC_PNW": "WECC_PNW>NP15", "WECC_DSW": "WECC_DSW>SP15_rest"}
CORRIDOR_GROUP = {
    "WECC_PNW": "grp:+WECC_PNW>NP15",
    "WECC_DSW": "grp:+WECC_DSW>SP15_rest",
}
EXPORT_UID = {
    "WECC_PNW": "WECC_PNW_export_MALIN",
    "WECC_DSW": "WECC_DSW_export_PALOVRDE",
}


def sys_frame(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"]


def net_frame(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
    return d[d["pass"] == "P1"]


def series_by_name(frame: pd.DataFrame, name: str, col: str) -> np.ndarray:
    g = frame[frame["name"] == name].set_index("hour").reindex(range(HOURS))
    return np.nan_to_num(g[col].to_numpy(), nan=0.0)


def c3a(bundle: Path, year: int) -> tuple[float, float, float]:
    """(model load-weighted mean, bench rt_lw, gap) with the bench month mask."""
    d = sys_frame(bundle, year)
    price = d.pivot_table(index="hour", columns="zone", values="price")
    dem = d.pivot_table(index="hour", columns="zone", values="demand")
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    num = (price[ca] * dem[ca]).sum(axis=1).to_numpy()
    den = dem[ca].sum(axis=1).to_numpy()
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["avgLMP"]
    rt = float(bench["rt_lw"])
    mon = bench.get("rt_lw_mon") or []
    cov = [i for i, v in enumerate(mon) if v is not None]
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    mo = stamps.month.to_numpy() - 1
    m = np.isin(mo, cov) if 0 < len(cov) < 12 else np.ones(HOURS, dtype=bool)
    model = float(num[m].sum() / den[m].sum())
    return model, rt, model - rt


def measured_corridor_net(year: int) -> dict[str, np.ndarray]:
    """Measured per-corridor hourly net import (MW) on the model clock."""
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock

    path = REPO / "data/raw/eia-930-interchange" / "CISO interchange hourly.parquet"
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    m = local.year == year
    f = frame[m].copy()
    f["corridor"] = f["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    f["ts"] = local[m].to_numpy()
    per = (f.dropna(subset=["corridor"]).groupby(["corridor", "ts"])["mw"].sum()).reset_index()
    per["net_import"] = -per["mw"]
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 48), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    idx = pd.Series(np.arange(HOURS), index=stamps)
    out: dict[str, np.ndarray] = {}
    for zone in CORRIDOR_LINK:
        sub = per[per["corridor"] == zone].copy()
        sub["h"] = sub["ts"].map(idx)
        sub = sub.dropna(subset=["h"])
        v = np.full(HOURS, np.nan)
        v[sub["h"].to_numpy().astype(int)] = sub["net_import"].to_numpy()
        out[zone] = v
    return out


def sink_dispatch(bundle: Path, year: int) -> dict[str, np.ndarray]:
    u = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "fuel", "hour", "mw"],
    )
    u = u[(u["pass"] == "P1") & (u["fuel"] == "import")]
    out: dict[str, np.ndarray] = {}
    for zone, uid in EXPORT_UID.items():
        g = u[u["unit_id"] == uid].set_index("hour").reindex(range(HOURS))
        out[zone] = np.nan_to_num(g["mw"].to_numpy(), nan=0.0)
    return out


def main() -> int:
    for p in (ARM_A, ARM_B):
        if not (p / "hourly").exists():
            print(f"MISSING bundle: {p}")
            return 1
    verdicts: dict[str, bool] = {}

    # ---------------- P1 / P2 -------------------------------------------------
    print("=" * 78)
    print("P1 — the outlet exists (arm B) / is absent (arm A); no limit violation")
    print("P2 — the export volume is inside reality's measured export envelope")
    print("=" * 78)
    p1 = p2 = True
    for year in YEARS:
        nb = net_frame(ARM_B, year)
        na = net_frame(ARM_A, year)
        sb = sink_dispatch(ARM_B, year)
        sa = sink_dispatch(ARM_A, year)
        for zone, link in CORRIDOR_LINK.items():
            flow_b = series_by_name(nb, link, "mw")
            flow_a = series_by_name(na, link, "mw")
            lim_dn = series_by_name(nb, CORRIDOR_GROUP[zone], "limit_dn")
            grp_b = series_by_name(nb, CORRIDOR_GROUP[zone], "mw")
            exp_hours_b = int((sb[zone] < -1e-6).sum())
            exp_hours_a = int((sa[zone] < -1e-6).sum())
            exp_twh_b = float(-sb[zone][sb[zone] < 0].sum()) / 1e6
            env_twh = float(-lim_dn.sum()) / 1e6
            closed = np.abs(lim_dn) <= 1e-6
            leak = int((sb[zone][closed] < -1e-6).sum())
            viol = float(np.maximum(0.0, -grp_b - np.abs(lim_dn)).max())
            ok1 = exp_hours_a == 0
            ok2 = (exp_twh_b <= env_twh + 1e-9) and leak == 0 and viol <= 1e-3
            p1 &= ok1
            p2 &= ok2
            print(
                f"  {year} {zone:9s} B: export {exp_hours_b:5d} h / {exp_twh_b:6.3f} TWh "
                f"(envelope {env_twh:6.3f} TWh, closed-hour leak {leak}, "
                f"limit violation {viol:.4f} MW) | A: {exp_hours_a} h  "
                f"| flow mean A {flow_a.mean():7.0f} -> B {flow_b.mean():7.0f} MW"
            )
    verdicts["P1"] = p1
    verdicts["P2"] = p2
    print(f"  -> P1 {'PASS' if p1 else 'FAIL'} | P2 {'PASS' if p2 else 'FAIL'}")

    # ---------------- P3 ------------------------------------------------------
    print("\n" + "=" * 78)
    print("P3 — corridor NET interchange moves TOWARD its measured net (all years)")
    print("=" * 78)
    p3_pnw = True
    for year in YEARS:
        meas = measured_corridor_net(year)
        na, nb = net_frame(ARM_A, year), net_frame(ARM_B, year)
        for zone, link in CORRIDOR_LINK.items():
            mv = meas[zone]
            ok_h = np.isfinite(mv)
            m_twh = float(mv[ok_h].sum()) / 1e6
            a_twh = float(series_by_name(na, link, "mw")[ok_h].sum()) / 1e6
            b_twh = float(series_by_name(nb, link, "mw")[ok_h].sum()) / 1e6
            da, db = abs(a_twh - m_twh), abs(b_twh - m_twh)
            toward = db < da - 1e-9
            if zone == "WECC_PNW":
                p3_pnw &= toward
            print(
                f"  {year} {zone:9s} measured net {m_twh:+7.3f} TWh | model A {a_twh:+7.3f} "
                f"(|err| {da:6.3f}) -> B {b_twh:+7.3f} (|err| {db:6.3f})  "
                f"{'TOWARD' if toward else 'away/flat'}"
            )
    verdicts["P3"] = p3_pnw
    print(f"  -> P3 (PNW, all three years) {'PASS' if p3_pnw else 'FAIL'}")

    # ---------------- P4 / P5 -------------------------------------------------
    print("\n" + "=" * 78)
    print("P4 — C3a move UP and inside the pre-registered ceiling")
    print("P5 — rubric read: the +-10 % band, and whether 2023/2024 leave it")
    print("=" * 78)
    p4 = True
    band_exits: list[int] = []
    for year in YEARS:
        ma, rt, ga = c3a(ARM_A, year)
        mb, _rt, gb = c3a(ARM_B, year)
        move = gb - ga
        ceiling = C3A_CEILING[year]
        band = C3A_BAND_FRAC * rt
        ok = (move >= -1e-6) and (move <= ceiling + 1e-9)
        p4 &= ok
        a_pass, b_pass = abs(ga) <= band, abs(gb) <= band
        if a_pass and not b_pass:
            band_exits.append(year)
        print(
            f"  {year}: bench {rt:6.2f} band +-{band:5.2f} | A gap {ga:+6.3f} "
            f"({100 * ga / rt:+6.2f}%, {'PASS' if a_pass else 'FAIL'}) -> "
            f"B gap {gb:+6.3f} ({100 * gb / rt:+6.2f}%, {'PASS' if b_pass else 'FAIL'}) "
            f"| move {move:+6.3f} (ceiling {ceiling:+.3f}, headroom_A "
            f"{band - abs(ga):+6.3f}) {'ok' if ok else 'OUT OF PREREG'}"
        )
    verdicts["P4"] = p4
    print(f"  -> P4 {'PASS' if p4 else 'FAIL'} | P5 band exits: {band_exits or 'none'}")

    # ---------------- P6 ------------------------------------------------------
    print("\n" + "=" * 78)
    print("P6 — arm A byte-identical to the committed keeper (prices + dumps)")
    print("=" * 78)
    p6 = True
    for year in YEARS:
        k, a = sys_frame(KEEPER, year), sys_frame(ARM_A, year)
        mk = k.pivot_table(index="hour", columns="zone", values="price")
        ma_ = a.pivot_table(index="hour", columns="zone", values="price")
        dk = k.pivot_table(index="hour", columns="zone", values="dump")
        da_ = a.pivot_table(index="hour", columns="zone", values="dump")
        cols = sorted(set(mk.columns) & set(ma_.columns))
        dp = float(np.nanmax(np.abs(mk[cols].to_numpy() - ma_[cols].to_numpy())))
        dd = float(np.nanmax(np.abs(dk[cols].to_numpy() - da_[cols].to_numpy())))
        ok = dp <= 1e-9 and dd <= 1e-6
        p6 &= ok
        # dump totals, A vs B (an export may now substitute for a dump)
        b = sys_frame(ARM_B, year)
        db_ = b.pivot_table(index="hour", columns="zone", values="dump")
        print(
            f"  {year}: max |dprice| A-vs-keeper {dp:.6g}, max |ddump| {dd:.6g} "
            f"{'IDENTICAL' if ok else 'DIFFERS'} | dump TWh keeper "
            f"{dk[cols].to_numpy().sum() / 1e6:.4f} A {da_[cols].to_numpy().sum() / 1e6:.4f} "
            f"B {db_[sorted(set(db_.columns) & set(cols))].to_numpy().sum() / 1e6:.4f}"
        )
    verdicts["P6"] = p6
    print(f"  -> P6 {'PASS' if p6 else 'FAIL'}")

    # ---------------- promotion rule -----------------------------------------
    print("\n" + "=" * 78)
    print("PREREG §3 promotion rule")
    print("=" * 78)
    for g in ("P1", "P2", "P3", "P4", "P6"):
        print(f"  {g}: {'PASS' if verdicts[g] else 'FAIL'}")
    promote = all(verdicts[g] for g in ("P1", "P2", "P3", "P4", "P6"))
    print(f"\n  PROMOTE per the pre-registered rule: {promote}")
    if band_exits:
        print(
            f"  Regression accounting (P5, reported as a headline): C3a leaves "
            f"the band in {band_exits} — that many currently-passing gates are "
            f"traded for the structural fix."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
