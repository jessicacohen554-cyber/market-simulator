"""Derive the regulated-PRB committed-band split levels (miso-112).

Measures, per PREREG-miso112-prb-committed-split-2026-07-31.md §4 (committed
before this script ran), the within-run loading levels that size the
``coal_prb_committed_split`` hold-through / cycling slices:

1. ``night_p50`` — p50 of plant load / HSL over ONLINE hours h0-5, pooled
   2023-2025. The ONE value the model consumes: the hold-through slice is
   ``min(committed_cap, max(0, night_p50 - pct_mr/100) * nameplate)``.
2. ``day_p50`` — p50 over ONLINE hours h13-18, pooled. Diagnostic only
   (PREREG §3: the band top stays the tranche artifact's committed_pct).

PLANT basis, WP-3 loading-when-on construction verbatim (HSL = p99.5 of
pooled plant gross load, online = load >= max(10 MW, 2% x HSL)) — the same
identification as `scripts/probes/_miso111_prb_conduct.py` and the NYISO
gas-bridge params. Source-data conduct derivation only (rule 13
[R-MEASURED] / 23 [R-FROZEN-DERIVE]): re-derive ONLY when the CAMPD
unit-level source updates, never against a residual.

Writes:
- ``data/raw/_processed-legacy/coal_prb_committed_split_<ISO>.csv`` — the
  model artifact (pooled levels, REG and MER legs; the model consumes REG).
- ``results/calibration/miso112_prb_conduct.csv`` — session record with
  per-year night/day p50s.

Prints the PREREG §5 kill-rule readout (K1 whole-band degenerate / K2
keeper degenerate) using the model's own tranche artifact values.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(
    0, str(REPO)
)  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_campd_gas_commitment_params import (  # noqa: E402
    UNIT_LEVEL_DIR,
    class_plant_codes,
    states_for_iso,
)
from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants  # noqa: E402

ISO = "MISO"
YEARS = [2023, 2024, 2025]
ONLINE_MW = 10.0
ONLINE_FRAC = 0.02
NIGHT_H = range(0, 6)  # h0-5 (PREREG §4)
DAY_H = range(13, 19)  # h13-18 (PREREG §4)
OUT_ARTIFACT = REPO / f"data/raw/_processed-legacy/coal_prb_committed_split_{ISO}.csv"
OUT_RECORD = REPO / "results/calibration/miso112_prb_conduct.csv"


def _load_plant_hours() -> dict[int, dict[int, tuple[np.ndarray, np.ndarray]]]:
    """Return ``{plant: {year: (hour_of_day, load_mw)}}`` for MISO COAL_PRB."""
    from market_sim.data.coal import _coal_class_for

    mapping, ambiguous = class_plant_codes(ISO, ("COAL",))
    if ambiguous:
        print(f"(dropping {len(ambiguous)} mixed-class plants: {ambiguous})")
    codes = {c for c in mapping if _coal_class_for(c) == "COAL_PRB"}
    print(f"{ISO} COAL_PRB plants (resolver): {len(codes)}")

    plant_year: dict[int, dict[int, tuple[np.ndarray, np.ndarray]]] = {}
    for state in states_for_iso(ISO):
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path, columns=["facilityId", "date", "hour", "grossLoad"]
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce").astype(
                "Int64"
            )
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df["grossLoad"] = df["grossLoad"].fillna(0.0)
            for fac, sub in df.groupby("facilityId"):
                ts = sub.groupby(["date", "hour"])["grossLoad"].sum().reset_index()
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
    return plant_year


def _window_p50(
    hod: np.ndarray, frac: np.ndarray, online: np.ndarray, hours
) -> tuple[float, int]:
    """p50 of ``frac`` over online hours whose hour-of-day is in ``hours``."""
    sel = online & np.isin(hod, list(hours))
    if not sel.any():
        return float("nan"), 0
    return float(np.percentile(frac[sel], 50)), int(sel.sum())


def main() -> None:
    reg = eia860_selfcommit_scope_plants()
    plant_year = _load_plant_hours()

    artifact_rows = []
    record_rows = []
    for fac, by_year in sorted(plant_year.items()):
        leg = "REG" if fac in reg else "MER"
        pooled = np.concatenate([by_year[y][1] for y in YEARS if y in by_year])
        hsl = float(np.percentile(pooled, 99.5))
        if hsl <= ONLINE_MW:
            continue
        thresh = max(ONLINE_MW, ONLINE_FRAC * hsl)

        hod_all = np.concatenate([by_year[y][0] for y in YEARS if y in by_year])
        frac_all = pooled / hsl
        on_all = pooled >= thresh
        night_p50, n_night = _window_p50(hod_all, frac_all, on_all, NIGHT_H)
        day_p50, n_day = _window_p50(hod_all, frac_all, on_all, DAY_H)
        if not np.isfinite(night_p50) or not np.isfinite(day_p50):
            continue
        artifact_rows.append(
            dict(
                plant_code=fac,
                leg=leg,
                hsl_mw=round(hsl, 1),
                night_p50=round(night_p50, 4),
                day_p50=round(day_p50, 4),
                n_night=n_night,
                n_day=n_day,
            )
        )
        for y in YEARS:
            if y not in by_year:
                continue
            hod, load = by_year[y]
            frac = load / hsl
            on = load >= thresh
            np50, nn = _window_p50(hod, frac, on, NIGHT_H)
            dp50, nd = _window_p50(hod, frac, on, DAY_H)
            record_rows.append(
                dict(
                    plant_code=fac,
                    leg=leg,
                    year=y,
                    hsl_mw=round(hsl, 1),
                    night_p50=round(np50, 4) if np.isfinite(np50) else np.nan,
                    day_p50=round(dp50, 4) if np.isfinite(dp50) else np.nan,
                    n_night=nn,
                    n_day=nd,
                )
            )

    art = pd.DataFrame(artifact_rows)
    art.to_csv(OUT_ARTIFACT, index=False)
    rec = pd.DataFrame(record_rows)
    rec.to_csv(OUT_RECORD, index=False)
    print(f"wrote {OUT_ARTIFACT} ({len(art)} plants)")
    print(f"wrote {OUT_RECORD} ({len(rec)} plant-years)\n")

    # ---- PREREG §5 kill-rule readout: the model's own tranche basis ----
    # (thermal_tranches artifact, keeper basis coal_mustrun_online_pmin=False)
    from market_sim.data.fleet.campd_bins import thermal_tranche_overrides

    tr = thermal_tranche_overrides(ISO, coal_online_pmin=False)
    hold_sum = cyc_sum = band_sum = 0.0
    print("== per-plant split (REG leg, model tranche basis) ==")
    print("plant     hsl_MW  night  day    mr%    mc%   hold_cap  cyc_cap")
    for r in art[art["leg"] == "REG"].itertuples(index=False):
        ov = tr.get((int(r.plant_code), "COAL"))
        if ov is None:
            print(
                f"{r.plant_code:>6}  (no tranche row — model default shares; excluded from readout)"
            )
            continue
        pct_mc, pct_mr = ov
        nameplate = r.hsl_mw  # HSL ≈ capability basis (PREREG §4, WP-3)
        committed_cap = nameplate * pct_mc / 100.0
        hold_cap = min(
            committed_cap, max(0.0, r.night_p50 - pct_mr / 100.0) * nameplate
        )
        cyc_cap = committed_cap - hold_cap
        hold_sum += hold_cap
        cyc_sum += cyc_cap
        band_sum += committed_cap
        print(
            f"{r.plant_code:>6}  {nameplate:7.0f}  {r.night_p50:.3f}  {r.day_p50:.3f}"
            f"  {pct_mr:5.1f}  {pct_mc:5.1f}  {hold_cap:8.0f}  {cyc_cap:7.0f}"
        )
    hold_share = hold_sum / band_sum if band_sum else float("nan")
    cyc_share = cyc_sum / band_sum if band_sum else float("nan")
    print(f"\ncap-weighted hold share of committed band: {hold_share:.3f}")
    print(f"cap-weighted cycling share of committed band: {cyc_share:.3f}")
    print(f"K1 (hold share < 0.05 → whole-band degenerate, DEAD): {hold_share < 0.05}")
    print(f"K2 (cycling share < 0.05 → keeper degenerate, DEAD): {cyc_share < 0.05}")


if __name__ == "__main__":
    main()
