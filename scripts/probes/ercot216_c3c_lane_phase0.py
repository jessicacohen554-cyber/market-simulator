"""ercot-216 Phase-0 (read-only, no LP): is the C3c ledger's OPEN RESIDUAL LANE
still open on the CURRENT keeper?

The ERCOT C3c caveat (`calibration_attestation.json`, the rubric-v3.0
model-class exception carried since 2026-08-05) names two candidates in its
own ``OPEN RESIDUAL LANE`` clause — *"the AS-vs-energy split of storage
capability at scarcity (FINDING-ercot162 §2) and the CC headroom/capability
identification (calibration-log/ercot.md ercot-163 close-out); a mechanism
that lands there simply PASSes this criterion and this entry goes inert."*
This probe measures whether either lane has room LEFT on the designated
keeper, from committed artifacts only. It solves nothing and writes nothing
outside its own JSON.

Sections:

1. **Lane (a) armed-state audit.** The storage AS family's flags as the keeper
   actually resolved them (``run_config.json``) — the mechanism the lane
   names is already armed (built ercot-167, promoted the same day, standing
   re-gate discharged RG-PASS at ercot-193).
2. **The C3c miss population** on the keeper's committed sidecars: actual
   RT > $200 (rubric §5 ERCOT tail threshold) vs the demand-weighted P1
   system price (the standing ``_ercot173_ab`` convention), split
   caught / missed / phantom, with the model's price distribution at the
   missed hours.
3. **Reality's own price formation at those hours** — published RTORPA, PRC
   and SCED system lambda (the NP6-905 curation) — is the miss reserve-made
   or energy-offer-made?
4. **The physical balance at those hours**: model class dispatch and storage
   net discharge vs EIA-930 ERCO actuals. This is the lane test: a quantity
   mechanism has room only if the model is LONG where reality was short.
5. **Clock verification** for §4's join, reported not asserted (see below).
6. **Sub-hourly concentration of the actual tail** from the 15-minute RTM
   settlement-point workbook: how much of an actual tail hour's hourly mean
   is carried by single intervals an hourly LP cannot represent (rule 8
   ``[R-8760]`` is hourly by mandate).

**Two clock conventions this probe fixes and verifies** (both are silent
+GW-scale errors in a tail-hour comparison, and §5 measures them rather than
asserting them):

* EIA-930's ``period`` is the hour **ENDING** stamp; the model's hour index is
  hour-**beginning** CST. Model hour ``h`` therefore joins the 930 CST stamp
  ``h + 1``.
* The model runs a fixed **non-leap** 8760 clock (rule 8; the ercot-214 probe's
  ``MONTH_DAYS`` table is the same fact), so in a leap year every model hour
  from March 1 on carries a real date 24 h later than a naive
  ``date_range(periods=8760)`` label. Uncorrected, that mis-dates all of
  2024's tail hours.

Usage::

    python scripts/probes/ercot216_c3c_lane_phase0.py \
        [--bundle results/calibration/ercot215_decontam_B] \
        [--out results/calibration/ercot216_c3c_lane_phase0.json]
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = REPO / "results/calibration/ercot215_decontam_B"
DEFAULT_OUT = REPO / "results/calibration/ercot216_c3c_lane_phase0.json"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
EIA930 = REPO / "data/raw/ERCO_fueltype.parquet"
YEARS = (2023, 2024, 2025)
TAIL = 200.0  # rubric §5 ERCOT scarcity threshold, $/MWh
GAS_KLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
COAL_KLASSES = ("COAL_LIGNITE", "COAL_PRB")
# The keeper's own scored C3c counts (calibration_verdict on the registered
# run) — the scorer basis differs from this probe's demand-weighted basis and
# both are reported rather than reconciled.
SCORED_C3C = {2023: (68, 181), 2024: (22, 53), 2025: (1, 31)}
STORAGE_AS_FLAGS = (
    "storage_as_commitment",
    "ercot_storage_as_deployment",
    "ercot_storage_as_soc_reserve",
    "ercot_storage_as_reserve",
    "ercot_storage_as_product_credit",
    "ercot_storage_capability_measured",
    "ercot_storage_rt_offer_surface",
    "ercot_storage_as_endogenous",
    "ercot_storage_as_duration_gate",
)


def model_calendar(year: int) -> pd.DatetimeIndex:
    """Real CST hour-beginning stamps for the model's fixed non-leap clock."""
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    h = np.arange(8760)
    offset = h + (24 * (h >= 1416) if leap else 0)  # 1416 h = Jan 1 -> Feb 28
    return pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(offset, unit="h")


def _eia930_pivot() -> pd.DataFrame:
    eia = pd.read_parquet(EIA930)
    ts = (
        pd.to_datetime(eia["period"], utc=True)
        .dt.tz_convert("Etc/GMT+6")  # fixed UTC-6 == CST, the fleet clock
        .dt.tz_localize(None)
    )
    return eia.assign(ts=ts).pivot_table(
        index="ts", columns="fueltype", values="value_mwh", aggfunc="sum"
    )


def _actual_930(pivot: pd.DataFrame, year: int) -> pd.DataFrame:
    """930 rows aligned to the model's hour index (hour-ending -> beginning)."""
    frame = pivot.reindex(model_calendar(year) + pd.Timedelta(hours=1))
    return frame.reset_index(drop=True)


def _model(bundle: Path, year: int) -> dict[str, pd.Series]:
    sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = sysdf[sysdf["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    demand = p1.pivot(index="hour", columns="zone", values="demand")
    hub = (price * demand).sum(axis=1) / demand.sum(axis=1)
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    klass = ch.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum"
    ).fillna(0.0)
    st = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    st = st[st["pass"] == "P1"].groupby("hour")[["charge_mw", "discharge_mw"]].sum()
    return {
        "hub": hub,
        "demand": demand.sum(axis=1),
        "gas": klass[[k for k in GAS_KLASSES if k in klass]].sum(axis=1),
        "coal": klass[[k for k in COAL_KLASSES if k in klass]].sum(axis=1),
        "nuc": klass["nuclear"],
        "re": klass["wind"] + klass["solar"],
        "storage_net": st["discharge_mw"] - st["charge_mw"],
    }


def _clock_check(model_demand: np.ndarray, pivot: pd.DataFrame, year: int) -> dict:
    """Correlate model demand against the 930 generation sum at four offsets.

    The model's demand series is a measured input with a clock verified
    astronomically (ercot-166); the offset that maximises the correlation is
    therefore the 930 stamp convention, measured rather than assumed.
    """
    cal = model_calendar(year)
    out = {}
    for shift in (-1, 0, 1, 2):
        frame = pivot.reindex(cal + pd.Timedelta(hours=shift))
        gen = frame[["NG", "COL", "NUC", "SUN", "WND", "WAT", "OTH"]].sum(axis=1)
        gen = gen.to_numpy(dtype=float)
        ok = ~np.isnan(gen)
        out[str(shift)] = round(float(np.corrcoef(model_demand[ok], gen[ok])[0, 1]), 5)
    return out


def _subhourly(year: int) -> dict:
    """15-minute dispersion inside the actual tail hours (HB_BUSAVG)."""
    path = REPO / f"data/raw/lmp-data/RTMLZHBSPP_{year}.zip"
    if not path.exists():
        return {"available": False}
    with zipfile.ZipFile(path) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            book = pd.ExcelFile(io.BytesIO(fh.read()))
        frame = pd.concat(
            [book.parse(sheet) for sheet in book.sheet_names], ignore_index=True
        )
    frame = frame[frame["Settlement Point Name"] == "HB_BUSAVG"]
    agg = frame.groupby(["Delivery Date", "Delivery Hour"])[
        "Settlement Point Price"
    ].agg(["mean", "max", "min", "median", "count"])
    tail = agg[agg["mean"] > TAIL]
    if tail.empty:
        return {"available": True, "tail_hours": 0}
    return {
        "available": True,
        "basis": "HB_BUSAVG 15-min RTM settlement point prices",
        "tail_hours": int(len(tail)),
        "median_max_over_mean": round(float((tail["max"] / tail["mean"]).median()), 3),
        "hours_median_interval_below_threshold": int((tail["median"] <= TAIL).sum()),
        "hours_min_interval_below_100": int((tail["min"] < 100.0).sum()),
        "hours_with_interval_above_1000": int((tail["max"] > 1000.0).sum()),
        "p50_hourly_mean": round(float(tail["mean"].median()), 2),
        "p50_max_interval": round(float(tail["max"].median()), 2),
        "p50_min_interval": round(float(tail["min"].median()), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ercot216_c3c_lane_phase0")
    parser.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--skip-subhourly",
        action="store_true",
        help="skip §6 (parses three 15-minute workbooks; minutes, not seconds)",
    )
    args = parser.parse_args(argv)
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle

    run_config = json.loads((bundle / "run_config.json").read_text())
    resolved = run_config.get("scenario_config", {})
    lane_a = {flag: resolved.get(flag) for flag in STORAGE_AS_FLAGS}

    pivot = _eia930_pivot()
    lmp = pd.read_parquet(ACTUAL_LMP)
    ordc_missing: list[str] = []
    years: dict[str, dict] = {}

    for year in YEARS:
        model = _model(bundle, year)
        hub = model["hub"]
        rt = lmp[lmp["year"] == year].set_index("hour")["rt"]
        tail = (rt > TAIL).to_numpy()
        missed = tail & (hub.to_numpy() <= TAIL)
        caught = tail & (hub.to_numpy() > TAIL)
        phantom = (~tail) & (hub.to_numpy() > TAIL)
        actual = _actual_930(pivot, year)

        balance = {}
        for name, actual_col in (
            ("gas", "NG"),
            ("coal", "COL"),
            ("nuc", "NUC"),
        ):
            m = float(model[name][missed].mean())
            a = float(actual[actual_col][missed].mean())
            balance[name] = {
                "model": round(m, 1),
                "actual": round(a, 1),
                "delta": round(m - a, 1),
            }
        re_a = float(
            (actual["WND"].fillna(0.0) + actual["SUN"].fillna(0.0))[missed].mean()
        )
        re_m = float(model["re"][missed].mean())
        balance["renewables"] = {
            "model": round(re_m, 1),
            "actual": round(re_a, 1),
            "delta": round(re_m - re_a, 1),
        }
        bat = actual["BAT"][missed] if "BAT" in actual else pd.Series(dtype=float)
        bat_mean = float(bat.mean()) if len(bat) and not bat.isna().all() else None
        st_m = float(model["storage_net"][missed].mean())
        balance["storage_net"] = {
            "model": round(st_m, 1),
            "actual": None if bat_mean is None else round(bat_mean, 1),
            "delta": None if bat_mean is None else round(st_m - bat_mean, 1),
            "note": (
                "EIA-930 ERCO BAT reporting starts 2024-11-06; earlier hours "
                "carry no measured battery series"
            ),
        }
        gen_sum = float(
            actual[["NG", "COL", "NUC", "SUN", "WND", "WAT", "OTH"]]
            .sum(axis=1)[missed]
            .mean()
        )
        balance["demand_vs_930_gen_sum"] = {
            "model_demand": round(float(model["demand"][missed].mean()), 1),
            "actual_gen_sum": round(gen_sum, 1),
        }

        reality = {}
        ordc_path = REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        if ordc_path.exists():
            ordc = pd.read_parquet(ordc_path).set_index("hour")
            for label, mask in (("missed", missed), ("caught", caught)):
                if not mask.any():
                    continue
                sub = ordc.iloc[mask.nonzero()[0]]
                lam = sub["system_lambda"]
                prc = sub["prc"].to_numpy(dtype=float)
                reality[label] = {
                    "rtorpa_p50": round(float(sub["rtorpa"].median()), 2),
                    "rtorpa_max": round(float(sub["rtorpa"].max()), 2),
                    "prc_p50_mw": round(float(sub["prc"].median()), 0),
                    "prc_min_mw": round(float(np.nanmin(prc)), 0),
                    # ERCOT declares EEA Level 1 at PRC < 2,300 MW (Nodal
                    # Protocols §6.5.9.4.2): the count is the WINDOW an
                    # emergency-tier price mechanism would need in order to
                    # have anything to declare at these hours.
                    "hours_prc_below_eea1_2300mw": int((prc < 2300.0).sum()),
                    "system_lambda_p50": round(float(lam.median()), 2),
                    "lambda_over_80pct_of_rt_share": round(
                        float((lam.to_numpy() > 0.8 * rt.to_numpy()[mask]).mean()), 3
                    ),
                }
        else:
            ordc_missing.append(str(ordc_path.relative_to(REPO)))

        years[str(year)] = {
            "tail_hours_actual": int(tail.sum()),
            "caught": int(caught.sum()),
            "missed": int(missed.sum()),
            "phantom": int(phantom.sum()),
            "scored_c3c_model_over_actual": list(SCORED_C3C[year]),
            "model_price_at_missed": {
                "p10": round(float(hub[missed].quantile(0.10)), 2),
                "p50": round(float(hub[missed].quantile(0.50)), 2),
                "p90": round(float(hub[missed].quantile(0.90)), 2),
            },
            "actual_price_at_missed_p50": round(float(rt[missed].quantile(0.50)), 2),
            "reality_at_hours": reality,
            "physical_balance_at_missed_mw": balance,
            "clock_check_corr_by_930_shift": _clock_check(
                model["demand"].to_numpy(dtype=float), pivot, year
            ),
            "subhourly_actual_tail": (
                {"skipped": True} if args.skip_subhourly else _subhourly(year)
            ),
        }

    payload = {
        "probe": "ercot216_c3c_lane_phase0",
        "bundle": str(bundle.relative_to(REPO)),
        "keeper": "2026-08-17-ercot215-arm-decontam",
        "read_only": True,
        "lane_a_storage_as_flags_on_keeper": lane_a,
        "conventions": {
            "price_basis": "demand-weighted P1 system price (_ercot173_ab)",
            "tail_threshold_usd_mwh": TAIL,
            "eia930_join": "930 period is hour-ENDING; model hour h joins CST stamp h+1",
            "model_clock": "fixed non-leap 8760; leap years skip Feb 29 (+24 h from Mar 1)",
        },
        "years": years,
    }
    if ordc_missing:
        payload["missing_inputs"] = ordc_missing

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
