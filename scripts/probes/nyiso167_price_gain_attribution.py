"""nyiso-167 — attribute NYISO's C3a-2025 miss from committed artifacts (zero solve).

The C3a-2025 failure (model load-weighted mean LMP $58.81 vs actual RT $66.43,
**-11.5 %**) has been carried as a *year-specific* object: a "winter face"
(Jan+Feb-2025 downstate premium) plus a "summer face" (the ledgered C3c
scarcity days), with the winter half identification-blocked behind the MyNYISO
AORR table (``docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md``).

This probe tests that framing against the keeper's own committed record and
finds it does not survive. Measured on the designated keeper
``2026-08-30-nyiso-159-loss-surface`` (its committed run payload, the committed
per-ISO bench parts, its ``hourly/system_<year>.parquet`` sidecars and the
committed hourly actual-LMP reference), the model's price response is a single
two-parameter affine law that is STABLE ACROSS ALL THREE TRAINING YEARS::

    model_month = GAIN x actual_month + OFFSET      (GAIN ~ 0.70, OFFSET ~ $11)

`GAIN < 1` is a *price-response gain deficiency*: the model reproduces only
about two thirds of the market's price gradient — in load (the decile ladder),
in gas price (the passthrough slope) and in calendar month alike. Because the
law is year-invariant, C3a's pass/fail is decided almost entirely by where the
year's actual mean price falls relative to the law's crossover: the model's
error is ``(GAIN - 1) x A + OFFSET`` in a year whose actual load-weighted mean
is ``A``, which is inside a +/-10 % band only for ``A`` in a bounded window.
2023 ($32.25) and 2024 ($38.12) sit inside that window; 2025 ($66.43) is 1.7x
its lower edge, and fails.

Five measurements, each written to the JSON record:

1. ``monthly_gain`` — the load-weighted affine fit over all 36 training months,
   against both the RT (gated) and DA (like-for-like, the model being a
   perfect-foresight RT/DA analogue) actual, with the implied C3a pass window.
2. ``load_decile`` — the model's reproduction of the measured price-vs-load
   gradient, per year, from the hourly sidecars.
3. ``gas_passthrough`` — the price-on-delivered-gas slope ($/MWh per $/MMBtu),
   system and per zone, model vs actual.
4. ``face_residuals`` — the per-month residual off the pooled law, which is the
   decisive test of the winter/summer face decomposition: a face that is a
   *separate* component must appear as a large negative residual off a law fit
   to every other month.
5. ``cross_iso_gain`` — the same fit on every ISO's designated keeper. The gain
   deficiency is not NYISO's; NEISO's keeper is the in-repo counterexample.

Rules: 13 ``[R-MEASURED]`` (committed measured artifacts only, read-only),
22 ``[R-HOLDOUT]`` (2023-2025 only; no out-of-training year is read, scored or
registered), 25 ``[R-ISO-SCOPE]`` (the cross-ISO scan is a MEASUREMENT and
fills no other ISO's matrix cell). No solve, no LP, no config field.

Usage::

    python scripts/probes/nyiso167_price_gain_attribution.py
    python scripts/probes/nyiso167_price_gain_attribution.py --run-id <id>
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from calibration_verdict import (  # noqa: E402
    BENCH_DIR,
    RUNS_DIR,
    _decode_run_js,
)

#: The designated NYISO keeper and its committed bundle (rule 15 — the hourly
#: sidecars a keeper commits exist precisely so a later diagnostic session
#: reads them instead of replaying the solve).
KEEPER_RUN_ID = "2026-08-30-nyiso-159-loss-surface"
KEEPER_BUNDLE = REPO / "results/calibration/nyiso159_lossarm_B"

#: Every ISO's designated keeper (``frontend/data/backcast/keepers/<ISO>.json``)
#: at this session's HEAD, for the cross-ISO gain scan.
KEEPERS: dict[str, str] = {
    "ERCOT": "2026-08-25-234-eastex-identity",
    "CAISO": "2026-08-26-caiso-220-c1-crosswalk",
    "PJM": "2026-08-15-pjm-162-inputclock",
    "MISO": "2026-08-30-miso-191-bexit",
    "NYISO": KEEPER_RUN_ID,
    "NEISO": "2026-08-17-neiso-99-joint-p1",
}

#: The training window, and the ONLY years this probe may read (rule 22).
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: C3a's target band (``calibration_verdict.PRICE_MEAN_TOL``), restated here so
#: the pass-window arithmetic is explicit rather than implied.
PRICE_MEAN_TOL = 0.10

#: The measured NYISO merit-order gas driver: EIA Natural Gas Weekly Update
#: "New York" spot = Transco Zone 6 NY (NGI Daily GPI), the same daily series
#: ``data.fuel.hubs`` reads for the within-month shape. Used here only as the
#: REGRESSOR for the passthrough slope; nothing is priced off it.
GAS_DAILY_PATH = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"

#: The committed hourly actual-LMP reference (``derive_actual_lmp.py``), dense
#: on the model's chronological standard-time calendar so it pairs hour-for-hour
#: with the bundle's ``system_<year>.parquet``.
ACTUAL_HOURLY_PATH = (
    REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
)

#: The committed per-zone monthly actual (same builder), for the zonal slopes.
ACTUAL_LMP_JSON = REPO / "data/raw/_validation-source/actual_lmp.json"

OUT_PATH = REPO / "results/calibration/_nyiso167_price_gain_attribution.json"


def _wls(
    x: np.ndarray, y: np.ndarray, w: np.ndarray | None = None
) -> tuple[float, float, float]:
    """Return ``(slope, intercept, r2)`` of a (optionally weighted) linear fit."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.ones_like(x) if w is None else np.asarray(w, dtype=float)
    root = np.sqrt(w)
    design = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(design * root[:, None], y * root, rcond=None)[0]
    resid = y - (slope * x + intercept)
    r2 = 1.0 - (resid.var() / y.var()) if y.var() > 0 else float("nan")
    return float(slope), float(intercept), float(r2)


def _pass_window(gain: float, offset: float, tol: float = PRICE_MEAN_TOL) -> dict:
    """The band of annual actual mean price for which C3a passes under the law.

    Under ``model = gain x A + offset`` the relative error is
    ``(gain - 1) + offset / A``, so C3a (``|err| <= tol``) holds exactly when
    ``offset / (tol + 1 - gain) <= A <= offset / (1 - gain - tol)`` (the upper
    edge is unbounded when ``1 - gain <= tol``, i.e. a near-unit gain never
    fails low).
    """
    lo_den = tol + 1.0 - gain
    hi_den = 1.0 - gain - tol
    return {
        "low_edge_usd_mwh": round(offset / lo_den, 2) if lo_den > 0 else None,
        "high_edge_usd_mwh": (round(offset / hi_den, 2) if hi_den > 0 else None),
        "note": (
            "annual actual load-weighted mean below the low edge fails C3a HIGH; "
            "above the high edge fails C3a LOW. A high edge of null means the "
            "gain is within tol of 1.0 and the law never fails low."
        ),
    }


def _model_monthly(payload_year: dict) -> tuple[list[float | None], list[float]]:
    """Load-weighted model monthly price and its monthly demand weights.

    Mirrors ``calibration_verdict.score_price_mean``'s model side exactly: the
    per-zone ``pMon`` weighted by the same ``dMon`` the scorer uses.
    """
    lmp = payload_year.get("lmp") or {}
    prices: list[float | None] = []
    weights: list[float] = []
    for month in range(12):
        num = den = 0.0
        for zone in lmp.values():
            p_mon = (zone.get("pMon") or [None] * 12)[month]
            d_mon = (zone.get("dMon") or [0.0] * 12)[month]
            if p_mon is not None:
                num += float(p_mon) * float(d_mon)
                den += float(d_mon)
        prices.append(num / den if den > 0 else None)
        weights.append(den)
    return prices, weights


def _bench_avg_lmp(iso: str, year: int) -> dict | None:
    """The committed bench part's ``avgLMP`` block for one ISO-year."""
    part = BENCH_DIR / iso / f"{year}.json.gz"
    if not part.exists():
        return None
    with gzip.open(part) as handle:
        return (json.load(handle).get("bench") or {}).get("avgLMP")


def _gas_daily() -> dict[dt.date, float]:
    """The measured Transco Z6 NY daily spot, keyed by trade date."""
    out: dict[dt.date, float] = {}
    with GAS_DAILY_PATH.open() as handle:
        for row in csv.DictReader(handle):
            try:
                out[dt.date.fromisoformat(row["date"])] = float(
                    row["transco_z6_ny_usd_mmbtu"]
                )
            except (KeyError, ValueError):
                continue
    return out


def _gas_monthly(daily: dict[dt.date, float]) -> dict[str, float]:
    """Calendar-month means of the daily quotes (the monthly hub level)."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for day, price in daily.items():
        buckets[f"{day.year}-{day.month:02d}"].append(price)
    return {key: statistics.mean(vals) for key, vals in buckets.items()}


def _gas_hourly(daily: dict[dt.date, float], year: int, hours: int) -> np.ndarray:
    """Broadcast the daily quotes onto the model's standard-time hour index.

    The model's hour ``k`` is the k-th hour after local standard-time midnight
    Jan 1 with Feb 29 dropped (``derive_actual_lmp``'s calendar). Non-trading
    days carry the most recent prior quote — the flow-date convention the hub
    series itself uses.
    """
    days: list[dt.date] = []
    cursor = dt.date(year, 1, 1)
    while cursor.year == year:
        if not (cursor.month == 2 and cursor.day == 29):
            days.append(cursor)
        cursor += dt.timedelta(days=1)
    series: list[float] = []
    carried: float | None = None
    for day in days:
        price = daily.get(day)
        if price is None:
            probe = day
            for _ in range(12):
                probe -= dt.timedelta(days=1)
                if probe in daily:
                    price = daily[probe]
                    break
        if price is None:
            price = carried
        carried = price
        series.extend([price] * 24)
    return np.asarray(series[:hours], dtype=float)


def _system_hourly(year: int) -> pd.DataFrame:
    """The keeper's own P1 load-weighted system price and load, per hour."""
    frame = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"].copy()
    frame["pw"] = frame["price"] * frame["demand"]
    grouped = frame.groupby("hour").agg(pw=("pw", "sum"), load=("demand", "sum"))
    grouped["price"] = grouped["pw"] / grouped["load"]
    return grouped[["price", "load"]]


def measure_monthly_gain(payload: dict, iso: str = "NYISO") -> dict:
    """Measurement 1 — the pooled monthly affine law, RT and DA bases."""
    rows: list[dict] = []
    for year in TRAIN_YEARS:
        year_payload = payload["years"].get(str(year))
        avg = _bench_avg_lmp(iso, year)
        if year_payload is None or not avg:
            continue
        prices, weights = _model_monthly(year_payload)
        rt_mon = avg.get("rt_lw_mon") or avg.get("rt_mon")
        da_mon = avg.get("da_lw_mon") or avg.get("da_mon")
        for month in range(12):
            model = prices[month]
            if model is None or weights[month] <= 0:
                continue
            rows.append(
                {
                    "month": f"{year}-{month + 1:02d}",
                    "model": round(model, 3),
                    "rt": (
                        None
                        if not rt_mon or rt_mon[month] is None
                        else round(float(rt_mon[month]), 3)
                    ),
                    "da": (
                        None
                        if not da_mon or da_mon[month] is None
                        else round(float(da_mon[month]), 3)
                    ),
                    "weight_mwh": round(weights[month], 3),
                }
            )
    out: dict = {"months": rows, "fits": {}}
    for basis in ("rt", "da"):
        usable = [r for r in rows if r[basis] is not None]
        if len(usable) < 12:
            continue
        actual = np.array([r[basis] for r in usable], dtype=float)
        model = np.array([r["model"] for r in usable], dtype=float)
        weight = np.array([r["weight_mwh"] for r in usable], dtype=float)
        gain, offset, r2 = _wls(actual, model, weight)
        resid = model - (gain * actual + offset)
        out["fits"][basis] = {
            "n_months": len(usable),
            "gain": round(gain, 4),
            "offset_usd_mwh": round(offset, 3),
            "r2": round(r2, 4),
            "resid_sd_usd_mwh": round(float(resid.std()), 3),
            "crossover_usd_mwh": (
                round(offset / (1.0 - gain), 2) if gain < 1 else None
            ),
            "c3a_pass_window": _pass_window(gain, offset),
        }
    return out


def measure_load_decile(iso: str = "NYISO") -> dict:
    """Measurement 2 — reproduction of the measured price-vs-load gradient."""
    actual = pd.read_parquet(ACTUAL_HOURLY_PATH)
    out: dict = {}
    for year in TRAIN_YEARS:
        model = _system_hourly(year)
        act = actual[actual["year"] == year].sort_values("hour")
        n = min(len(model), len(act))
        frame = pd.DataFrame(
            {
                "model": model["price"].to_numpy()[:n],
                "load": model["load"].to_numpy()[:n],
                "rt": act["rt"].to_numpy()[:n],
                "da": act["da"].to_numpy()[:n],
            }
        ).dropna()
        decile = pd.qcut(frame["load"], 10, labels=False)
        ladder = [
            {
                "decile": int(k),
                "load_mw": round(float(frame[decile == k]["load"].mean()), 1),
                "model": round(float(frame[decile == k]["model"].mean()), 2),
                "da": round(float(frame[decile == k]["da"].mean()), 2),
                "rt": round(float(frame[decile == k]["rt"].mean()), 2),
            }
            for k in range(10)
        ]
        x = np.array([r["da"] for r in ladder])
        y = np.array([r["model"] for r in ladder])
        gain, offset, r2 = _wls(x, y)
        out[str(year)] = {
            "n_hours": int(len(frame)),
            "ladder": ladder,
            "gradient_gain_vs_da": round(gain, 4),
            "gradient_offset_usd_mwh": round(offset, 3),
            "r2": round(r2, 4),
            "spread_model_usd_mwh": round(ladder[9]["model"] - ladder[0]["model"], 2),
            "spread_da_usd_mwh": round(ladder[9]["da"] - ladder[0]["da"], 2),
            "spread_ratio": round(
                (ladder[9]["model"] - ladder[0]["model"])
                / (ladder[9]["da"] - ladder[0]["da"]),
                4,
            ),
        }
    return out


def measure_gas_passthrough(payload: dict) -> dict:
    """Measurement 3 — price-on-gas slope, model vs actual, system and zonal."""
    daily = _gas_daily()
    monthly = _gas_monthly(daily)
    actual_json = json.loads(ACTUAL_LMP_JSON.read_text())["NYISO"]
    gas: list[float] = []
    model: list[float] = []
    act_rt: list[float] = []
    act_da: list[float] = []
    weights: list[float] = []
    zonal: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"gas": [], "model": [], "rt": [], "da": []}
    )
    for year in TRAIN_YEARS:
        year_payload = payload["years"].get(str(year))
        avg = _bench_avg_lmp("NYISO", year)
        if year_payload is None or not avg:
            continue
        prices, month_weights = _model_monthly(year_payload)
        for month in range(12):
            key = f"{year}-{month + 1:02d}"
            if key not in monthly or prices[month] is None:
                continue
            gas.append(monthly[key])
            model.append(prices[month])
            act_rt.append(float(avg["rt_lw_mon"][month]))
            act_da.append(float(avg["da_lw_mon"][month]))
            weights.append(month_weights[month])
        zones_actual = actual_json[str(year)]["zones"]
        for zone, zone_payload in (year_payload.get("lmp") or {}).items():
            if zone not in zones_actual:
                continue  # external proxy buses carry no measured zonal actual
            p_mon = zone_payload.get("pMon") or []
            for month in range(12):
                key = f"{year}-{month + 1:02d}"
                if key not in monthly or month >= len(p_mon) or p_mon[month] is None:
                    continue
                bucket = zonal[zone]
                bucket["gas"].append(monthly[key])
                bucket["model"].append(float(p_mon[month]))
                bucket["rt"].append(float(zones_actual[zone]["rt_mon"][month]))
                bucket["da"].append(float(zones_actual[zone]["da_mon"][month]))
    out: dict = {
        "driver": "Transco Zone 6 NY daily spot, calendar-month mean ($/MMBtu)",
        "system": {},
        "zones": {},
    }
    g = np.array(gas)
    for name, series in (
        ("model", model),
        ("actual_rt", act_rt),
        ("actual_da", act_da),
    ):
        slope, intercept, r2 = _wls(g, np.array(series))
        out["system"][name] = {
            "slope_usd_mwh_per_mmbtu": round(slope, 4),
            "intercept_usd_mwh": round(intercept, 3),
            "r2": round(r2, 4),
        }
    out["system"]["model_over_actual_da"] = round(
        out["system"]["model"]["slope_usd_mwh_per_mmbtu"]
        / out["system"]["actual_da"]["slope_usd_mwh_per_mmbtu"],
        4,
    )
    for zone, bucket in zonal.items():
        zg = np.array(bucket["gas"])
        slopes = {
            name: round(_wls(zg, np.array(bucket[key]))[0], 4)
            for name, key in (
                ("model", "model"),
                ("actual_rt", "rt"),
                ("actual_da", "da"),
            )
        }
        slopes["model_over_actual_da"] = round(slopes["model"] / slopes["actual_da"], 4)
        slopes["n_months"] = len(zg)
        out["zones"][zone] = slopes
    return out


def measure_face_residuals(monthly: dict, basis: str = "da") -> dict:
    """Measurement 4 — the winter/summer faces as residuals off the pooled law.

    The decomposition on the record (``DECISION-CARD-nyiso156`` §4, restated by
    ``DECISION-CARD-nyiso161`` §2) treats the Jan+Feb-2025 "winter face" as a
    SEPARATE, identification-blocked component of the C3a-2025 miss. A separate
    component must show up as a large negative residual off a law fitted to
    every month; a month that is merely a high-price sample of the same gain
    deficiency will not.
    """
    fit = monthly["fits"].get(basis)
    if fit is None:
        return {}
    gain = fit["gain"]
    offset = fit["offset_usd_mwh"]
    rows = [r for r in monthly["months"] if r[basis] is not None]
    resid = {
        r["month"]: round(r["model"] - (gain * r[basis] + offset), 3) for r in rows
    }
    sd = fit["resid_sd_usd_mwh"]
    faces = {
        "winter_face_2025": ["2025-01", "2025-02"],
        "summer_face_2025": ["2025-06", "2025-07"],
    }
    # Annual load-weighted CONTRIBUTIONS, which is the unit the decision card's
    # face arithmetic is stated in ("winter face -$3.92 of the -$7.62 miss").
    # Splitting each face's contribution into the part the pooled law already
    # predicts and the part that is genuinely month-specific is the direct test
    # of whether the face is a SEPARATE component or a high-price sample of the
    # one gain deficiency.
    year_rows = [r for r in rows if r["month"].startswith("2025")]
    total_weight = sum(r["weight_mwh"] for r in year_rows) or 1.0

    def _contrib(months: list[str] | None) -> dict:
        subset = [r for r in year_rows if months is None or r["month"] in months]
        raw = sum(
            (r["weight_mwh"] / total_weight) * (r["model"] - r[basis]) for r in subset
        )
        res = sum((r["weight_mwh"] / total_weight) * resid[r["month"]] for r in subset)
        return {
            "raw_contribution_usd_mwh": round(raw, 3),
            "law_explained_usd_mwh": round(raw - res, 3),
            "residual_contribution_usd_mwh": round(res, 3),
            "share_explained_by_gain": (round(1.0 - res / raw, 4) if raw else None),
        }

    verdict = {}
    for name, months in faces.items():
        vals = [resid[m] for m in months if m in resid]
        verdict[name] = {
            "months": months,
            "residuals_usd_mwh": vals,
            "residual_z": [round(v / sd, 2) for v in vals],
            "raw_error_usd_mwh": [
                round(r["model"] - r[basis], 2) for r in rows if r["month"] in months
            ],
            "annual_2025_contribution": _contrib(months),
        }
    return {
        "basis": basis,
        "law": {"gain": gain, "offset_usd_mwh": offset, "resid_sd_usd_mwh": sd},
        "residuals": resid,
        "faces": verdict,
        "year_2025_total": _contrib(None),
    }


def measure_cross_iso_gain() -> dict:
    """Measurement 5 — the same monthly law on every ISO's designated keeper."""
    out: dict = {}
    for iso, run_id in KEEPERS.items():
        run_js = RUNS_DIR / f"{run_id}.js"
        if not run_js.exists():
            out[iso] = {"run_id": run_id, "status": "payload absent at HEAD"}
            continue
        payload = _decode_run_js(run_js.read_text())
        monthly = measure_monthly_gain(payload, iso=iso)
        fit = monthly["fits"].get("rt") or monthly["fits"].get("da")
        out[iso] = {
            "run_id": run_id,
            "basis": "rt" if "rt" in monthly["fits"] else "da",
            **({} if fit is None else fit),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id", default=KEEPER_RUN_ID, help="NYISO run to attribute"
    )
    parser.add_argument("--out", default=str(OUT_PATH), help="JSON record path")
    args = parser.parse_args(argv)

    payload = _decode_run_js((RUNS_DIR / f"{args.run_id}.js").read_text())
    monthly = measure_monthly_gain(payload)
    record = {
        "probe": "nyiso167_price_gain_attribution",
        "run_id": args.run_id,
        "iso": "NYISO",
        "years": list(TRAIN_YEARS),
        "solve": "NONE — committed artifacts only",
        "monthly_gain": monthly,
        "load_decile": measure_load_decile(),
        "gas_passthrough": measure_gas_passthrough(payload),
        "face_residuals": measure_face_residuals(monthly, basis="rt"),
        "face_residuals_da": measure_face_residuals(monthly, basis="da"),
        "cross_iso_gain": measure_cross_iso_gain(),
    }
    Path(args.out).write_text(json.dumps(record, indent=1) + "\n")

    rt = monthly["fits"]["rt"]
    da = monthly["fits"]["da"]
    print(f"NYISO {args.run_id} — C3a price-response gain (zero solve)")
    print(
        f"  monthly law vs RT: model = {rt['gain']:.4f} x actual + {rt['offset_usd_mwh']:.2f}"
        f"   R2 {rt['r2']:.4f}  resid sd ${rt['resid_sd_usd_mwh']:.2f}"
    )
    print(
        f"  monthly law vs DA: model = {da['gain']:.4f} x actual + {da['offset_usd_mwh']:.2f}"
        f"   R2 {da['r2']:.4f}  resid sd ${da['resid_sd_usd_mwh']:.2f}"
    )
    win = rt["c3a_pass_window"]
    print(
        f"  C3a pass window (RT basis): ${win['low_edge_usd_mwh']} .. "
        f"${win['high_edge_usd_mwh']}/MWh of annual actual mean"
    )
    for year, block in record["load_decile"].items():
        print(
            f"  {year}: load-gradient gain {block['gradient_gain_vs_da']:.3f} "
            f"(R2 {block['r2']:.4f}); decile spread model ${block['spread_model_usd_mwh']}"
            f" vs DA ${block['spread_da_usd_mwh']}"
        )
    for label in ("face_residuals", "face_residuals_da"):
        block_all = record[label]
        print(f"  faces on the {block_all['basis'].upper()} basis:")
        total = block_all["year_2025_total"]
        print(
            f"    2025 whole year: raw ${total['raw_contribution_usd_mwh']:+.3f}"
            f" = law ${total['law_explained_usd_mwh']:+.3f}"
            f" + residual ${total['residual_contribution_usd_mwh']:+.3f}"
        )
        for name, block in block_all["faces"].items():
            c = block["annual_2025_contribution"]
            print(
                f"    {name}: raw ${c['raw_contribution_usd_mwh']:+.3f}"
                f" = law ${c['law_explained_usd_mwh']:+.3f}"
                f" + residual ${c['residual_contribution_usd_mwh']:+.3f}"
                f"  (gain explains {c['share_explained_by_gain']:.1%});"
                f" month z {block['residual_z']}"
            )
    print("  cross-ISO gain:")
    for iso, block in record["cross_iso_gain"].items():
        if "gain" in block:
            print(
                f"    {iso:6s} {block['gain']:.3f}  offset ${block['offset_usd_mwh']:6.2f}"
                f"  R2 {block['r2']:.3f}"
            )
    print(f"  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
