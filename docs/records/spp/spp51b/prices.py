"""SPP-51b phase 0 instrument (ZERO LP): recover each registered run's hourly ISO
price from its committed dashboard payload and decompose the C3a level residual.

``lmpDeltaHr`` in a run payload is ``model_iso_price - actual_rt`` as signed int16
(1 $/MWh resolution, ``-32768`` = NaN), written by
``render_calibration_html._b64_i16``; the model side is the demand-weighted mean
over the ISO's zones, which is the same construction C3a scores.  So

    model_iso[h] = actual_rt[h] + delta[h]

recovers the hourly model price of a run whose bundle no longer exists -- which is
the only route to SPP-50's price surface (its 119 MB bundle died with its session;
the sidecar and payload are committed, the ``hourly/`` sidecars were never written).

Outputs (per run x year): the load-weighted level error by system-load percentile
band and by month, beside the measured surface.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "frontend/data/backcast/runs"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_SPP.parquet"
KEEPER_HOURLY = REPO / "results/calibration/spp43_screened_B/hourly"

YEARS = (2023, 2024, 2025)
BANDS = [(0, 10), (10, 25), (25, 50), (50, 75), (75, 90), (90, 95), (95, 98), (98, 100)]


def load_payload(run_id: str) -> dict:
    blob = re.search(
        r'runGz\["[^"]+"\]="([^"]+)"', (RUNS / f"{run_id}.js").read_text()
    ).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def decode_i16(blob: str) -> np.ndarray:
    v = np.frombuffer(base64.b64decode(blob), dtype="<i2").astype(float)
    v[v == -32768] = np.nan
    return v


def actual_rt(year: int) -> np.ndarray:
    df = pd.read_parquet(ACTUAL)
    s = df[df["year"] == year].sort_values("hour")["rt"].to_numpy(dtype=float)
    return s


def model_price(run_id: str, year: int) -> np.ndarray:
    pay = load_payload(run_id)["years"][str(year)]
    d = decode_i16(pay["lmpDeltaHr"])
    a = actual_rt(year)
    n = min(len(d), len(a))
    return a[:n] + d[:n]


def system_demand(year: int) -> np.ndarray:
    """Model system demand (MW) per hour, from keeper-3's committed system sidecar.

    Demand is an INPUT (the same measured load array in both runs -- SPP-50's own
    array census found ``demand`` bit-identical), so keeper-3's sidecar supplies
    the load axis for both runs without re-solving anything.
    """
    df = pd.read_parquet(KEEPER_HOURLY / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.groupby("hour")["demand"].sum().sort_index().to_numpy(dtype=float)


def keeper_price(year: int) -> np.ndarray:
    """Keeper-3 demand-weighted ISO price from its own committed sidecar (exact)."""
    df = pd.read_parquet(KEEPER_HOURLY / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    p = df.pivot(index="hour", columns="zone", values="price").sort_index()
    d = df.pivot(index="hour", columns="zone", values="demand").sort_index()
    return ((p * d).sum(axis=1) / d.sum(axis=1)).to_numpy(dtype=float)


def band_table(model: np.ndarray, act: np.ndarray, load: np.ndarray) -> pd.DataFrame:
    n = min(len(model), len(act), len(load))
    model, act, load = model[:n], act[:n], load[:n]
    ok = np.isfinite(model) & np.isfinite(act) & np.isfinite(load)
    pct = pd.Series(load[ok]).rank(pct=True).to_numpy() * 100.0
    m, a, l = model[ok], act[ok], load[ok]
    rows = []
    for lo, hi in BANDS:
        sel = (pct >= lo) & (pct < hi) if hi < 100 else (pct >= lo)
        if not sel.any():
            continue
        w = l[sel]
        mm, aa = (
            float(np.average(m[sel], weights=w)),
            float(np.average(a[sel], weights=w)),
        )
        rows.append(
            {
                "band": f"{lo}-{hi}",
                "hrs": int(sel.sum()),
                "load_GW": round(float(w.mean()) / 1000.0, 2),
                "model": round(mm, 3),
                "actual": round(aa, 3),
                "err_%": round(100.0 * (mm - aa) / aa, 2),
                "err_$": round(mm - aa, 3),
                "err_TWh_wtd_M$": round(float(np.sum((m[sel] - a[sel]) * w)) / 1e6, 1),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    runs = {
        "spp50": "2026-09-08-spp-50-rebaseline",
        "keeper3": "2026-09-07-spp-3-screened-input",
    }
    for tag, rid in runs.items():
        for year in YEARS:
            m = model_price(rid, year)
            a = actual_rt(year)
            load = system_demand(year)
            n = min(len(m), len(a), len(load))
            ok = np.isfinite(m[:n]) & np.isfinite(a[:n]) & np.isfinite(load[:n])
            lw_m = float(np.average(m[:n][ok], weights=load[:n][ok]))
            lw_a = float(np.average(a[:n][ok], weights=load[:n][ok]))
            print(
                f"\n### {tag} {year}  LW model {lw_m:.3f}  actual {lw_a:.3f}  "
                f"err {100 * (lw_m - lw_a) / lw_a:+.2f}%   (n={int(ok.sum())})"
            )
            print(band_table(m, a, load).to_string(index=False))
        if tag == "keeper3":
            for year in YEARS:
                kp, mp = keeper_price(year), model_price(runs[tag], year)
                n = min(len(kp), len(mp))
                d = np.abs(kp[:n] - mp[:n])
                d = d[np.isfinite(d)]
                print(
                    f"[check] keeper3 {year}: payload-recovered vs sidecar price, "
                    f"max|Δ| {d.max():.3f} mean|Δ| {d.mean():.4f} $/MWh "
                    f"(int16 quantization floor 0.5)"
                )


if __name__ == "__main__":
    main()


def steepening() -> None:
    """The merit-order lane's own gate metric on the REPAIRED surface.

    ``MHR(>95 pct) / MHR(25-75 pct)`` where MHR = price / SPP's own KS+OK delivered
    gas -- the statistic ``FINDING-spp-merit-order-2026-09-07.md`` §1 measured at
    2.3375 / 2.0993 / 2.1069 (measured) against 1.5620 / 1.5163 / 1.6187 (keeper-3).
    """
    ref = pd.read_csv(
        Path(__file__).resolve().parents[3]
        / "data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
    )
    print(
        "\n### steepening ratio  MHR(>95pct)/MHR(25-75pct)   (gas = KS+OK N3045 / 1.036)"
    )
    for year in YEARS:
        g = (
            float(
                ref[(ref["state"].isin(["KS", "OK"])) & (ref["year"] == year)][
                    "price_usd_mcf"
                ].mean()
            )
            / 1.036
        )
        act = actual_rt(year)
        load = system_demand(year)
        out = {}
        for tag, rid in (
            ("keeper3", "2026-09-07-spp-3-screened-input"),
            ("SPP-50", "2026-09-08-spp-50-rebaseline"),
        ):
            m = model_price(rid, year)
            n = min(len(m), len(act), len(load))
            ok = np.isfinite(m[:n]) & np.isfinite(act[:n]) & np.isfinite(load[:n])
            pct = np.full(n, np.nan)
            pct[ok] = pd.Series(load[:n][ok]).rank(pct=True).to_numpy() * 100
            mid, top = ok & (pct >= 25) & (pct < 75), ok & (pct >= 95)
            for lbl, series in (("", m[:n]), ("_meas", act[:n])):
                r = np.average(series[top], weights=load[:n][top]) / np.average(
                    series[mid], weights=load[:n][mid]
                )
                out[tag + lbl] = r / 1.0
        print(
            f"  {year}: measured {out['keeper3_meas']:.4f}   "
            f"keeper-3 {out['keeper3']:.4f}   SPP-50 {out['SPP-50']:.4f}   "
            f"(gas ${g:.3f})"
        )
