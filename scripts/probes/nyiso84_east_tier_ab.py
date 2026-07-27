"""nyiso-84 A/B: the EAST-tier reserve arms vs a same-HEAD control.

Compares the nyiso-84 arms — the published EAST spin_10/total_30 ladder
(``nyiso_east_reserve_families``), the published-spin online gate
(``nyiso_spin_reserve_online``), and their composition — against the
zero-delta control replay of the nyiso-81 keeper recipe, on the quantities the
C3c scarcity-formation lane is judged by:

* **C3c price tail** — hours the max zonal dual exceeds ``$300``
  (``TAIL_THRESHOLD["NYISO"]``), any-zone and per-zone, plus the
  load-weighted tail quantiles. The lane's gated metric
  (``docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md`` §0/§4).
* **System reserve dual** — the sidecar's system-wide ``reserve_price``
  series (hours > $0, mean, max). NOTE: this column is BROADCAST across
  zones and carries no locational information (finding §2) — it is the
  tier-binding signal, never a per-zone claim.
* **Class energy mix + diurnal shape** — so a gate-forced commitment change
  (GT/steam up, CC down) or a broad $40-shortfall price shift is visible
  rather than hidden inside a matching total.

A control arm is used rather than the registered keeper metrics because the
replay environment's solver/pandas/pyarrow versions differ from the keeper's
recorded ones (nyiso-83 method note), so only a same-HEAD, same-environment
baseline isolates the mechanisms' own effect.

Usage:
    python scripts/probes/nyiso84_east_tier_ab.py \
        --control results/calibration/nyiso84_control \
        --arm ladder=results/calibration/nyiso84_east_ladder \
        --arm gate=results/calibration/nyiso84_spin_gate \
        --arm ladder+gate=results/calibration/nyiso84_east_gate \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TAIL_THRESHOLD_NYISO = 300.0
EVENING_HOURS = range(14, 22)
OVERNIGHT_HOURS = list(range(0, 7)) + [22, 23]


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """Load a bundle's P1 system hourly sidecar for *year*."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    """Load a bundle's P1 class hourly sidecar for *year*."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def tail_rows(df: pd.DataFrame) -> dict:
    """Return the C3c tail counts (any-zone and per-zone) for one arm-year."""
    p = df.pivot_table(index="hour", columns="zone", values="price")
    out = {"any_zone": int((p.max(axis=1) > TAIL_THRESHOLD_NYISO).sum())}
    for z in p.columns:
        out[z] = int((p[z] > TAIL_THRESHOLD_NYISO).sum())
    load = df.pivot_table(index="hour", columns="zone", values="demand")
    w = (p * load).sum(axis=1) / load.sum(axis=1)
    out["_wtd_mean"] = round(float(w.mean()), 2)
    out["_wtd_p999"] = round(float(w.quantile(0.999)), 1)
    out["_wtd_max"] = round(float(w.max()), 1)
    return out


def reserve_dual(df: pd.DataFrame) -> dict:
    """Summarize the system-wide reserve dual series (broadcast column)."""
    rp = df.groupby("hour")["reserve_price"].first()
    return {
        "h_gt0": int((rp > 1e-6).sum()),
        "mean": round(float(rp.mean()), 3),
        "max": round(float(rp.max()), 1),
    }


def class_profile(df: pd.DataFrame, klass: str) -> dict:
    """Return annual TWh plus the evening/overnight mean MW of one class."""
    s = df[df["klass"] == klass]
    if s.empty:
        return {}
    by_hour = s.groupby("hour")["mw"].sum()
    hod = by_hour.groupby(by_hour.index % 24).mean()
    evening = float(hod.loc[list(EVENING_HOURS)].mean())
    overnight = float(hod.loc[OVERNIGHT_HOURS].mean())
    return {
        "twh": round(float(by_hour.sum()) / 1e6, 3),
        "ev_over_night": (
            round(evening / overnight, 3) if overnight else float("nan")
        ),
    }


def main() -> None:
    """Print the arms-vs-control A/B tables, one block per year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument(
        "--arm",
        action="append",
        required=True,
        metavar="NAME=BUNDLE",
        help="probe arm as name=bundle-dir (repeatable, printed in order)",
    )
    ap.add_argument("--years", nargs="+", type=int, required=True)
    args = ap.parse_args()

    arms = []
    for spec in args.arm:
        name, _, path = spec.partition("=")
        arms.append((name, Path(path)))

    for year in args.years:
        cs = _system(args.control, year)
        ct = tail_rows(cs)
        arm_sys = {n: _system(p, year) for n, p in arms}
        arm_tails = {n: tail_rows(s) for n, s in arm_sys.items()}

        print(f"\n===== {year} =====")
        hdr = f"{'C3c tail (>$300)':<20}{'control':>10}" + "".join(
            f"{n:>13}" for n, _ in arms
        )
        print(hdr)
        for k in ct:
            row = f"{k:<20}{ct[k]:>10}"
            for n, _ in arms:
                row += f"{arm_tails[n].get(k, 0):>13}"
            print(row)

        print(f"{'reserve dual':<20}{'control':>10}" + "".join(
            f"{n:>13}" for n, _ in arms
        ))
        cr = reserve_dual(cs)
        rd = {n: reserve_dual(s) for n, s in arm_sys.items()}
        for k in ("h_gt0", "mean", "max"):
            row = f"{k:<20}{cr[k]:>10}"
            for n, _ in arms:
                row += f"{rd[n][k]:>13}"
            print(row)

        cc = _classes(args.control, year)
        arm_cls = {n: _classes(p, year) for n, p in arms}
        classes = sorted(set(cc["klass"]))
        print(f"{'class TWh (ev/ng)':<20}{'control':>14}" + "".join(
            f"{n:>16}" for n, _ in arms
        ))
        for k in classes:
            a = class_profile(cc, k)
            if not a or abs(a.get("twh", 0.0)) < 0.05:
                continue
            row = f"{k:<20}{a['twh']:>8.3f} ({a['ev_over_night']:>4.2f})"
            for n, _ in arms:
                b = class_profile(arm_cls[n], k)
                row += (
                    f"{b.get('twh', 0.0):>9.3f} ({b.get('ev_over_night', float('nan')):>4.2f})"
                )
            print(row)


if __name__ == "__main__":
    main()
