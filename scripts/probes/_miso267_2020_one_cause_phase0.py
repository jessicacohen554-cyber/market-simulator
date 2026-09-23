#!/usr/bin/env python3
"""miso-267 STEP 2, phase 0: do MISO 2020's coal shortfall and price bias share ONE cause?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The keeper ``2026-09-22-hydro-5-miso-ror``
fails two held-out 2020 cells at once — C1 ``COAL_BIT`` ~ -10.7 TWh (model short)
and C3a mean LMP ~ +14.7 % (model high). ``RESULT-miso264`` §7 found the two
demand OPPOSITE offer moves and named a quantity / commitment object;
``FINDING-miso265`` §2 found the coal availability envelope below the CEMS meter.
Neither measured WHEN in the year the two residuals sit, which is the one test
that separates a shared cause from two coincident ones: a single cause puts the
missing coal and the excess price in the SAME hours.

Everything read is committed or rebuilt without a solve:

* the keeper's hourly sidecars — ``class_hourly`` (model MW per class),
  ``class_band_hourly`` (per tranche band) and ``system`` (zonal price, demand);
* the committed bench part's per-plant CEMS series (``plants[*].campd``, uint8
  percent of the slice nameplate, decoded exactly as the payload encodes it) —
  the actual per class per hour on the SAME plant->class map the keeper scores on;
* the committed hourly real-time price
  (``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``).

2023 is reported beside 2020 as the in-regime year (train tier CALIBRATED): a
pattern that appears in both is a standing trait of the keeper, one confined to
2020 is the held-out object.

Reported, never tuned: no mechanism is armed, no parameter moves.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BUNDLE = REPO / "results/calibration/hydro5_miso_ror_span"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
RT = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
INTERNAL = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)
COAL = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE")
T = 8760
MONTH_OF_HOUR = pd.date_range("2021-01-01", periods=T, freq="h").month.to_numpy()
HOUR_OF_DAY = np.arange(T) % 24


def _decode(blob: str, cap: float) -> np.ndarray:
    """Invert ``render_calibration_html._b64``: uint8 percent of ``cap`` -> MW.

    Kept for reference only: the uint8 percent-of-nameplate encoding LOSES
    energy (MISO 2020 COAL_BIT decodes to 57.0 TWh against an exact
    ``sum(c_ann)`` of 63.1), so it is fit for timing and never for levels.
    """
    a = np.frombuffer(base64.b64decode(blob), dtype=np.uint8).astype(float)
    return a[:T] * float(cap) / 100.0


def actual_class_hourly(year: int, bench_root: Path = BENCH) -> dict[str, np.ndarray]:
    """CEMS MW per hour per coal class, on the committed part's own class map.

    The hourly series is the raw CAMPD net frame, rebuilt zero-LP through the
    builder's own ``_campd_hourly_frame`` (same parasitic scaling the bench
    uses); a multi-class plant's series is split across its slices by the
    slices' exact annual ``c_ann`` shares, so every class's annual total equals
    the committed part's ``sum(c_ann)`` to rounding.
    """
    import scripts.run_calibration_full as rcf

    part = ba.load_bench_part(bench_root / f"{year}.json.gz")["bench"]
    campd = rcf._campd_hourly_frame(year, "MISO", rcf._parasitic_factor_map(), T)
    series = {
        int(pid): g.sort_values("hour")["net_mw"].to_numpy(float)[:T]
        for pid, g in campd.groupby("plant_id")
    }
    slices: dict[int, list[tuple[str, float]]] = {}
    for key, rec in part["plants"].items():
        code = int(str(key).split(":")[0])
        slices.setdefault(code, []).append((rec["group"], float(rec["c_ann"])))
    out = {k: np.zeros(T) for k in COAL}
    for code, parts in slices.items():
        s = series.get(code)
        if s is None:
            continue
        tot = sum(max(c, 0.0) for _, c in parts)
        for g, c in parts:
            if g in out and tot > 0.0:
                out[g] += np.nan_to_num(s) * max(c, 0.0) / tot
    return out


def model_hourly(year: int) -> tuple[dict[str, np.ndarray], np.ndarray, pd.DataFrame]:
    """Model coal MW per class, load-weighted internal price, and band MW."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    cls = {
        k: ch[ch["klass"] == k].sort_values("hour")["mw"].to_numpy(float)[:T]
        for k in COAL
    }
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"].isin(INTERNAL))]
    p = s.pivot(index="hour", columns="zone", values="price").to_numpy(float)
    d = s.pivot(index="hour", columns="zone", values="demand").to_numpy(float)
    price = (p * d).sum(axis=1) / d.sum(axis=1)
    bands = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{year}.parquet")
    bands = bands[(bands["pass"] == "P1") & (bands["klass"].isin(COAL))]
    return cls, price[:T], bands


def summarize(year: int, bench_root: Path = BENCH) -> dict:
    """Every table the phase-0 question needs, for one year."""
    act = actual_class_hourly(year, bench_root)
    mod, price, bands = model_hourly(year)
    rt = pd.read_parquet(RT)
    rt = rt[rt["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:T]
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"].isin(INTERNAL))]
    load = s.groupby("hour")["demand"].sum().to_numpy(float)[:T]

    coal_def = sum(mod[k] - act[k] for k in COAL)
    bit_def = mod["COAL_BIT"] - act["COAL_BIT"]
    perr = price - rt
    lw = load / load.sum()

    def by(keys: np.ndarray, n: int, base: int = 0) -> list[dict]:
        rows = []
        for k in range(base, base + n):
            m = keys == k
            if not m.any():
                continue
            rows.append(
                {
                    "k": int(k),
                    "hours": int(m.sum()),
                    "bit_def_twh": round(float(bit_def[m].sum()) / 1e6, 3),
                    "coal_def_twh": round(float(coal_def[m].sum()) / 1e6, 3),
                    "model_price": round(
                        float(np.average(price[m], weights=load[m])), 2
                    ),
                    "rt": round(float(np.average(rt[m], weights=load[m])), 2),
                    "price_err": round(float(np.average(perr[m], weights=load[m])), 2),
                }
            )
        return rows

    rt_decile = np.minimum(
        (pd.Series(rt).rank(pct=True).to_numpy() * 10).astype(int), 9
    )
    load_decile = np.minimum(
        (pd.Series(load).rank(pct=True).to_numpy() * 10).astype(int), 9
    )
    # Band shares of the model's COAL_BIT energy (which tranche carries it).
    bit = bands[bands["klass"] == "COAL_BIT"]
    band_twh = (bit.groupby("band", observed=True)["mw"].sum() / 1e6).round(3)

    def corr(a: np.ndarray, b: np.ndarray) -> float:
        return round(float(np.corrcoef(a, b)[0, 1]), 3)

    return {
        "year": year,
        "annual": {
            "model_bit_twh": round(float(mod["COAL_BIT"].sum()) / 1e6, 3),
            "cems_bit_twh": round(float(act["COAL_BIT"].sum()) / 1e6, 3),
            "model_coal_twh": round(float(sum(mod.values()).sum()) / 1e6, 3),
            "cems_coal_twh": round(float(sum(act.values()).sum()) / 1e6, 3),
            "model_price_lw": round(float((price * lw).sum()), 2),
            "rt_lw": round(float((rt * lw).sum()), 2),
        },
        "corr_hourly": {
            "bit_def_vs_price_err": corr(bit_def, perr),
            "coal_def_vs_price_err": corr(coal_def, perr),
            "price_err_vs_load": corr(perr, load),
            "coal_def_vs_load": corr(coal_def, load),
        },
        "by_month": by(MONTH_OF_HOUR, 12, 1),
        "by_hour_of_day": by(HOUR_OF_DAY, 24),
        "by_rt_decile": by(rt_decile, 10),
        "by_load_decile": by(load_decile, 10),
        "model_bit_band_twh": {str(k): float(v) for k, v in band_twh.items() if v},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2020, 2023])
    ap.add_argument("--bench-root", type=Path, default=BENCH)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    res = {y: summarize(y, args.bench_root) for y in args.years}
    for y, r in res.items():
        print(f"== {y}: {r['annual']}")
        print(f"   hourly correlations: {r['corr_hourly']}")
        print(f"   model COAL_BIT by band (TWh): {r['model_bit_band_twh']}")
        for name in ("by_month", "by_rt_decile", "by_load_decile"):
            print(f"   {name}:")
            for row in r[name]:
                print(f"     {row}")
    if args.out:
        args.out.write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
