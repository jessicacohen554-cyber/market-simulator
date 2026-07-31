"""miso-111 Phase-2 probe: MISO regulated-PRB committed-window conduct (CAMPD).

Measures, per PREREG-miso111-prb-committed-flex-2026-07-31.md §4 (committed
before this script ran):

1. Plant-basis loading-when-on ``lsl_frac`` (WP-3 construction verbatim:
   HSL_proxy = p99.5 of plant gross load, online = load >= max(10 MW,
   2% x HSL), LSL_proxy = p5 of online hours), regulated vs merchant.
2. The ONLINE-conditioned hour-of-day profile of plant load / HSL_proxy —
   the committed-window within-day profile — capacity-weighted per class
   leg, with off-peak (h0-14) CV and amplitude, per year.
3. Capacity-weighted p50 of ``lsl_frac`` (regulated, plant basis), per year
   and pooled — the candidate ``min_load_frac`` identification.

Kill rules K1 (flat committed band), K2 (no headroom), K3 (merchant
artifact) bind on these outputs. Source-data conduct derivation only
(rule 13 [R-MEASURED] / 23 [R-FROZEN-DERIVE]); no model output enters.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_campd_gas_commitment_params import (  # noqa: E402
    UNIT_LEVEL_DIR,
    class_plant_codes,
    states_for_iso,
    weighted_percentile,
)
from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants  # noqa: E402

YEARS = [2023, 2024, 2025]
ONLINE_MW = 10.0
ONLINE_FRAC = 0.02
OFFPEAK_H = 15  # h0-14, the D-1 window


def main() -> None:
    # The fleet CSV's plant_group is bare COAL; the PRB/BIT/LIGNITE split is
    # the coal-rank resolver's job (mirrors the calibration bench grouping).
    from market_sim.data.coal import _coal_class_for

    mapping, ambiguous = class_plant_codes("MISO", ("COAL",))
    if ambiguous:
        print(f"(dropping {len(ambiguous)} mixed-class plants: {ambiguous})")
    codes = {c for c in mapping if _coal_class_for(c) == "COAL_PRB"}
    print(f"MISO COAL_PRB plants (resolver): {len(codes)}")
    reg = eia860_selfcommit_scope_plants()

    # plant -> year -> hourly plant-total gross load
    plant_year: dict[int, dict[int, np.ndarray]] = {}
    for state in states_for_iso("MISO"):
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path, columns=["facilityId", "date", "hour", "grossLoad"]
            )
            # facilityId is a string column in the raw extracts
            df["facilityId"] = pd.to_numeric(
                df["facilityId"], errors="coerce"
            ).astype("Int64")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df["grossLoad"] = df["grossLoad"].fillna(0.0)
            for fac, sub in df.groupby("facilityId"):
                ts = (
                    sub.groupby(["date", "hour"])["grossLoad"].sum().reset_index()
                )
                ts["date"] = pd.to_datetime(ts["date"])
                ts = ts.sort_values(["date", "hour"])
                hod = ts["hour"].to_numpy()
                load = ts["grossLoad"].to_numpy(dtype=float)
                d = plant_year.setdefault(int(fac), {})
                if year in d:
                    # same facility across two state files: sum aligned hours
                    prev = d[year]
                    n = min(len(prev[0]), len(load))
                    d[year] = (prev[0][:n], prev[1][:n] + load[:n])
                else:
                    d[year] = (hod, load)

    rows = []
    profiles: dict[tuple[str, int], list[tuple[float, np.ndarray]]] = {}
    for fac, by_year in sorted(plant_year.items()):
        leg = "REG" if fac in reg else "MER"
        pooled = np.concatenate([by_year[y][1] for y in YEARS if y in by_year])
        hsl = float(np.percentile(pooled, 99.5))
        if hsl <= ONLINE_MW:
            continue
        thresh = max(ONLINE_MW, ONLINE_FRAC * hsl)
        online_pool = pooled[pooled >= thresh]
        lsl = float(np.percentile(online_pool, 5)) if online_pool.size else 0.0
        lsl_frac = lsl / hsl
        for y in YEARS:
            if y not in by_year:
                continue
            hod, load = by_year[y]
            on = load >= thresh
            if on.sum() < 100:
                continue
            prof = np.zeros(24)
            for h in range(24):
                sel = on & (hod == h)
                prof[h] = load[sel].mean() / hsl if sel.any() else np.nan
            if np.isnan(prof).any():
                continue
            off = prof[:OFFPEAK_H]
            rows.append(
                dict(
                    plant=fac,
                    leg=leg,
                    year=y,
                    hsl=hsl,
                    lsl_frac=lsl_frac,
                    online_h=int(on.sum()),
                    off_cv=float(off.std() / off.mean()),
                    amp=float(prof.max() - prof.min()),
                )
            )
            profiles.setdefault((leg, y), []).append((hsl, prof))

    df = pd.DataFrame(rows)
    out = REPO / "results/calibration/miso111_prb_conduct.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} plant-years)\n")

    print("== per-leg capacity-weighted committed-window profile ==")
    for (leg, y), items in sorted(profiles.items()):
        w = np.array([h for h, _ in items])
        p = np.array([pr for _, pr in items])
        cls = np.average(p, axis=0, weights=w)
        off = cls[:OFFPEAK_H]
        print(
            f"{leg} {y}: n={len(items):2d} cap={w.sum():7.0f} MW  "
            f"offpeak CV={off.std() / off.mean():.4f}  "
            f"amp={cls.max() - cls.min():.4f}  "
            f"trough@h{int(cls.argmin())} peak@h{int(cls.argmax())}"
        )

    print("\n== lsl_frac capacity-weighted p50 (plant basis) ==")
    for leg in ("REG", "MER"):
        sub = df[df["leg"] == leg].drop_duplicates("plant")
        if sub.empty:
            continue
        p50 = weighted_percentile(
            sub["lsl_frac"].to_numpy(), sub["hsl"].to_numpy(), 50
        )
        print(
            f"{leg}: pooled p50={p50:.3f}  n={len(sub)}  "
            f"range [{sub['lsl_frac'].min():.3f}, {sub['lsl_frac'].max():.3f}]"
        )

    print("\n== kill-rule readout ==")
    reg_cvs = {
        y: (
            lambda items: (
                lambda w, p: (
                    lambda cls: cls[:OFFPEAK_H].std() / cls[:OFFPEAK_H].mean()
                )(np.average(p, axis=0, weights=w))
            )(
                np.array([h for h, _ in items]),
                np.array([pr for _, pr in items]),
            )
        )(profiles[("REG", y)])
        for y in YEARS
        if ("REG", y) in profiles
    }
    k1 = all(cv < 0.04 for cv in reg_cvs.values())
    sub = df[df["leg"] == "REG"].drop_duplicates("plant")
    p50 = weighted_percentile(sub["lsl_frac"].to_numpy(), sub["hsl"].to_numpy(), 50)
    k2 = p50 >= 0.85
    print(f"K1 (flat committed band, all-year REG offpeak CV < 0.04): {k1}  {reg_cvs}")
    print(f"K2 (no headroom, REG plant-basis lsl_frac p50 >= 0.85): {k2}  p50={p50:.3f}")


if __name__ == "__main__":
    main()
