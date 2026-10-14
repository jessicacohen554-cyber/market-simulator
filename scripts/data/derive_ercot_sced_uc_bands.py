"""Derive ERCOT gas offer-band multipliers from 60-Day SCED offers, UC basis.

UC-BANDS-ERCOT phase 1a (PRECOMMIT ``docs/records/ercot/ucmilp/
PRECOMMIT-ucmilp-bands-ercot-2026-10-14.md`` §2, authorized by UC-DESK on owner
decision 8, 2026-10-14). This is the measured successor the PRECOMMIT names for
an ERCOT configuration that commits gas units with ``unit_commitment_milp``. It
produces an artifact only. No ScenarioConfig field reads it yet, so nothing that
solves changes.

Method. It mirrors ``derive_dam_offer_hrmults.derive_class`` point for point and
changes only what the UC basis requires.

* **Source.** The NP3-965 60-Day SCED Gen Resource Data corpus. Shards are
  selected and rows are filtered to the delivery year by the same helpers as
  ``derive_ercot_sced_offer_wall``. The curve is the submitted Three-Part
  energy offer (``Submitted TPO`` MW/price points, piecewise linear), read on
  rows whose telemetered status is ON*. Rows are taken at one SCED interval per
  resource-hour, because a TPO is submitted hourly and the extra intervals only
  repeat it.
* **Committed** is the TPO price interpolated at the telemetered LSL. That is
  the incremental energy price at minimum load. The DAM lineage instead
  anchored committed on the three-part Min Gen Cost, an all-in $/MWh that
  includes no-load. The UC pays no-load and start in its own objective (DESIGN
  §1.2, D-3), so the all-in anchor would count no-load twice
  (FINDING-ucmilp-bands-ercot-2026-10-14 §2).
* **econ_low / econ_high / peak** follow the DAM lineage exactly. Points are
  placed on the operating range by ``rel = (MW − LSL)/(HSL − LSL)``. econ_low
  uses ``rel ≤ 0.33`` and econ_high uses ``rel ≥ 0.67``, both on the competitive
  body (price < $1,000). Peak is mode B, the top of the curve including
  near-cap points (the adopted cconly lineage's mode).
* **Aggregation.** Each resource contributes its own median per band. The
  bands are then capacity-weighted (HSL) to p25 / p50 / p75 across resources,
  pooled over every delivery year in ``--years``. One value covers every scored
  year: no year partition, no × k and no deltas.
* **Divisor (dispatch basis).** The band is price ÷ (delivered gas of the day ×
  the output group's cap-weighted fleet heat rate). Gas is Henry Hub daily plus
  the measured monthly EP basis (``ep_gas_day_series``), the series dispatch
  pays. The heat rate is the CAMPD-measured operating rate the fleet
  multiplies (``fleet_class_hr``). So ``band × fleet HR × dispatch gas``
  reproduces the posted offer. The DAM lineage's ``HH − 0.50`` × bin
  ``Plant_Avg_HR`` divisor is the inconsistency ERCOT-117 proved causal
  (FINDING-ucmilp-bands-ercot-rule14-2026-10-14: window gas ratio 0.885, 2023
  0.797). ``--gas-basis hh --hr-basis bin`` keeps it only as a reported
  comparison.
* **Incremental equivalent.** The UC prices no-load separately, so the
  committed / econ energy belongs on the incremental heat rate. For each output
  group the derive measures the ratio (incremental ÷ average heat rate) from
  CAMPD unit hours. The incremental rate is the OLS slope of heatInput on
  grossLoad, the regression whose intercept is the UC's ``noload_mmbtu_h``; the
  average is Σ heatInput ÷ Σ grossLoad. Both are capacity-weighted over the
  group's plants. The derive reports ``band ÷ ratio`` as the incremental-basis
  value. The model's offer is ``base_HR × band × fuel = (base_HR × ratio) ×
  (band ÷ ratio) × fuel``, so carrying the incremental rate as its own fleet
  field (PRECOMMIT §5 Q2) changes no offer. This derive does not add that field.
* **CT_PEAKER committed** is reported as a variant only, measured with the start
  proxy removed. The stacked-proxy decision is the owner's.

Admissibility: measured posted offers (rule 13). Frozen against residuals
(rule 23): re-derive only when the SCED corpus or the CAMPD year changes. Zero
fitted scalars. The constants below are the DAM lineage's own (imported).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.paths import CALIBRATION_DIR, RAW_DIR  # noqa: E402

from scripts.data.derive_dam_offer_hrmults import (  # noqa: E402
    CAMPD_BINS,
    ERCOT_GAS_BASIS,
    PCTS,
    SCARCITY_THRESH,
    _wquantile,
    output_base_hr,
)
from scripts.data.derive_ercot_dam_cleared_share import _gas_day_series  # noqa: E402
from scripts.data.derive_ercot_sced_offer_wall import (  # noqa: E402
    _delivery_year_rows,
    _sced_source_files,
)

DEFAULT_OUT = CALIBRATION_DIR / "ercot_sced_uc_bands.json"
CAMPD_UNIT_DIR = RAW_DIR / "campd-unit-level"

#: SCED Resource Type -> measured class (``parse_ercot_dam_offers`` mapping).
CLASS_OF_RESTYPE: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSNONR": "ST_GAS",
    "GSSUP": "ST_GAS",
}
#: Measured class -> the offer_curve_by_group output groups it grounds (DAM lineage).
CLASS_TO_OUTPUT: dict[str, tuple[str, ...]] = {
    "CC": ("CC_REGULAR", "CC_CHP"),
    "CT_PEAKER": ("CT_PEAKER",),
    "ST_GAS": ("ST_GAS",),
}
#: Bands each output group publishes in the main curve; CT committed is a variant.
MAIN_BANDS: dict[str, tuple[str, ...]] = {
    "CC_REGULAR": ("committed", "econ_low", "econ_high", "peak"),
    "CC_CHP": ("committed", "econ_low", "econ_high", "peak"),
    "ST_GAS": ("committed", "econ_low", "econ_high", "peak"),
    "CT_PEAKER": ("econ_low", "econ_high", "peak"),
}
N_TPO = 10
_TPO_MW = [f"Submitted TPO-MW{i}" for i in range(1, N_TPO + 1)]
_TPO_PR = [f"Submitted TPO-Price{i}" for i in range(1, N_TPO + 1)]
_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "LSL",
    "HSL",
    *_TPO_MW,
    *_TPO_PR,
]
#: Minimum CAMPD operating hours (grossLoad > 0) for a unit's OLS to count.
MIN_UNIT_HOURS = 200


def ep_gas_day_series(years: tuple[int, ...]) -> pd.Series:
    """Delivered gas on the dispatch basis: HH daily + the measured monthly EP basis.

    This is the level ``apply_ercot_zonal_gas_basis`` moves every ERCOT gas unit
    to under the keeper's armed ``ercot_zonal_gas_basis`` /
    ``ercot_ep_gas_basis_monthly`` / ``_corroborated`` / ``_receipts_fallback``
    flags. It is the same construction as ERCOT-118's
    ``derive_dam_offer_hrmults.derive_ep_basis_yearly``, at monthly grain. The
    lineage's ``HH − 0.50`` divisor (``_gas_day_series``) is the basis ERCOT-117
    proved inconsistent with dispatch, so ``--gas-basis hh`` keeps it only as a
    reported comparison.
    """
    from market_sim.data.fuel.basis.ercot import ercot_electric_power_gas_basis_monthly

    hh = _gas_day_series() - float(ERCOT_GAS_BASIS)  # back to plain HH daily
    out = []
    for y in years:
        basis = ercot_electric_power_gas_basis_monthly(
            y, corroborated=True, receipts_fallback=True
        )
        if basis is None:
            raise SystemExit(f"EP monthly gas basis unavailable for {y}")
        idx = pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D")
        out.append(
            pd.Series(
                hh.reindex(idx).to_numpy() + np.asarray(basis)[idx.month - 1], index=idx
            )
        )
    return pd.concat(out)


def fleet_class_hr(group: str, year: int) -> float:
    """Cap-weighted heat rate the fleet multiplies for ``group`` in ``year``.

    The value is the CAMPD-measured operating rate
    (``campd_bins.measured_{cc,ct,st}_heat_rates``, the keeper's armed
    ``measured_*_heat_rates``) where it exists, falling back to the bin
    ``Plant_Avg_HR`` where it does not. The fleet loader resolves a plant's base
    rate the same way, so ``band × fleet HR`` reproduces the measured offer.
    CC_CHP carries no measured rate because ``measured_chp_heat_rates`` is off.
    """
    from market_sim.data.fleet import campd_bins as cb

    meas = {
        "CC_REGULAR": cb.measured_cc_heat_rates,
        "CT_PEAKER": cb.measured_ct_heat_rates,
        "ST_GAS": cb.measured_st_heat_rates,
    }
    bins = pd.read_csv(CAMPD_BINS)
    d = bins[(bins["Plant_Group"] == group) & (bins["Plant_Avg_HR_MMBtu_MWh"] > 0)]
    hr = d["Plant_Avg_HR_MMBtu_MWh"].astype(float)
    if group in meas:
        hr = d["Plant_Code"].map(meas[group]("ERCOT", year)).astype(float).fillna(hr)
    return float(np.average(hr, weights=d["Nameplate_MW"].astype(float)))


def load_sced(
    years: tuple[int, ...], gas_basis: str = "ep"
) -> tuple[pd.DataFrame, list[str]]:
    """One ON-status row per gas resource-hour, numeric, with delivery date + gas."""
    frames, names = [], []
    gas = ep_gas_day_series(years) if gas_basis == "ep" else _gas_day_series()
    for y in years:
        for path in _sced_source_files(y):
            df = pd.read_parquet(path, columns=_COLS)
            df = _delivery_year_rows(df, y)
            df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
            stat = df["Telemetered Resource Status"].astype(str).str.strip()
            df = df[stat.str.startswith("ON")]
            ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
            df = df.assign(_hr=ts.dt.floor("h"), _date=ts.dt.normalize())
            df = df.drop_duplicates(["Resource Name", "_hr"])
            num = [c for c in ("LSL", "HSL", *_TPO_MW, *_TPO_PR)]
            df[num] = df[num].apply(pd.to_numeric, errors="coerce")
            frames.append(
                df.drop(columns=["SCED Time Stamp", "Telemetered Resource Status"])
            )
            names.append(path.name)
    d = pd.concat(frames, ignore_index=True)
    d["cls"] = d["Resource Type"].map(CLASS_OF_RESTYPE)
    d["gas"] = d["_date"].map(gas).to_numpy(float)
    d = d[(d["gas"] > 0) & (d["HSL"] > d["LSL"]) & (d["LSL"] >= 0)]
    return d.reset_index(drop=True), names


def per_resource_bands(d: pd.DataFrame) -> pd.DataFrame:
    """Per-resource median $/MMBtu-equivalent price by band (divided by gas only)."""
    mw = d[_TPO_MW].to_numpy(float)
    pr = d[_TPO_PR].to_numpy(float)
    ok = np.isfinite(mw) & np.isfinite(pr)
    lsl = d["LSL"].to_numpy(float)
    hsl = d["HSL"].to_numpy(float)
    gas = d["gas"].to_numpy(float)
    # committed: TPO price interpolated at LSL (vectorised piecewise-linear; the
    # curve is monotone in MW, so the first point at or above LSL brackets it).
    mw_f = np.where(ok, mw, np.inf)
    k = np.argmax(mw_f >= lsl[:, None] - 1e-6, axis=1)
    has = (mw_f >= lsl[:, None] - 1e-6).any(axis=1) & ok.any(axis=1)
    rows = np.arange(len(d))
    km1 = np.clip(k - 1, 0, None)
    x0, x1 = mw[rows, km1], mw[rows, k]
    y0, y1 = pr[rows, km1], pr[rows, k]
    w = np.where((k > 0) & (x1 > x0), (lsl - x0) / np.where(x1 > x0, x1 - x0, 1.0), 1.0)
    p_lsl = np.where(k > 0, y0 + np.clip(w, 0, 1) * (y1 - y0), y1)
    committed = np.where(has & (p_lsl > 0), p_lsl / gas, np.nan)
    rel = np.clip((mw - lsl[:, None]) / (hsl - lsl)[:, None], 0.0, 1.0)
    pos = ok & (pr > 0)
    body = pos & (pr < SCARCITY_THRESH)
    pg = pr / gas[:, None]
    lo = np.where(body & (rel <= 0.33), pg, np.nan)
    hi = np.where(body & (rel >= 0.67), pg, np.nan)
    with np.errstate(all="ignore"):
        econ_low = np.nanmedian(lo, axis=1)
        econ_high = np.nanmedian(hi, axis=1)
        peak = np.nanmax(np.where(pos, pg, np.nan), axis=1)
    f = pd.DataFrame(
        {
            "res": d["Resource Name"].to_numpy(),
            "cls": d["cls"].to_numpy(),
            "cap": hsl,
            "committed": committed,
            "econ_low": econ_low,
            "econ_high": econ_high,
            "peak": peak,
        }
    )
    return f.groupby(["cls", "res"]).median().reset_index()


def capwt(per_res: pd.DataFrame, band: str, divisor: float) -> dict:
    """Cap-weighted p25/p50/p75 of ``band`` (÷ divisor) across resources, with n."""
    s = per_res[np.isfinite(per_res[band]) & (per_res["cap"] > 0)]
    v = s[band].to_numpy(float) / divisor
    w = s["cap"].to_numpy(float)
    out = {f"p{int(p * 100)}": round(_wquantile(v, w, p), 3) for p in PCTS}
    out["n_resources"] = int(len(s))
    return out


def incremental_ratio(groups: tuple[str, ...], campd_year: int) -> dict:
    """Cap-weighted incremental÷average heat-rate ratio over a group's CAMPD units."""
    bins = pd.read_csv(CAMPD_BINS)
    plants = set(bins.loc[bins["Plant_Group"].isin(groups), "Plant_Code"].astype(int))
    cm = pd.read_parquet(
        CAMPD_UNIT_DIR / f"TX_{campd_year}.parquet",
        columns=["facilityId", "unitId", "opTime", "grossLoad", "heatInput"],
    )
    cm["plant"] = pd.to_numeric(cm["facilityId"], errors="coerce")
    cm = cm[cm["plant"].isin(plants)]
    cm = cm[
        (cm["opTime"].fillna(0) >= 1.0) & (cm["grossLoad"] > 0) & (cm["heatInput"] > 0)
    ]
    rows = []
    for (_, _), u in cm.groupby(["plant", "unitId"]):
        if len(u) < MIN_UNIT_HOURS:
            continue
        x = u["grossLoad"].to_numpy(float)
        y = u["heatInput"].to_numpy(float)
        b, a = np.polyfit(x, y, 1)
        avg = y.sum() / x.sum()
        if b > 0 and avg > 0:
            rows.append((b, avg, a, float(np.quantile(x, 0.99))))
    r = np.array(rows)
    w = r[:, 3]
    slope = float(np.average(r[:, 0], weights=w))
    avg = float(np.average(r[:, 1], weights=w))
    return {
        "ratio": round(slope / avg, 4),
        "slope_hr": round(slope, 3),
        "avg_hr": round(avg, 3),
        "noload_share_at_p99": round(
            float(np.average(r[:, 2] / (r[:, 1] * w), weights=w)), 4
        ),
        "n_units": int(len(r)),
        "campd_year": campd_year,
    }


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--campd-year", type=int, default=2023)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--gas-basis", choices=("ep", "hh"), default="ep")
    ap.add_argument("--hr-basis", choices=("fleet", "bin"), default="fleet")
    args = ap.parse_args()

    d, files = load_sced(tuple(args.years), args.gas_basis)
    per_res = per_resource_bands(d)
    groups: dict = {}
    for cls, outs in CLASS_TO_OUTPUT.items():
        pr = per_res[per_res["cls"] == cls]
        for og in outs:
            bhr = (
                fleet_class_hr(og, max(args.years))
                if args.hr_basis == "fleet"
                else output_base_hr({}, (og,))
            )
            inc = incremental_ratio((og,), args.campd_year)
            bands = {
                b: capwt(pr, b, bhr)
                for b in ("committed", "econ_low", "econ_high", "peak")
            }
            groups[og] = {
                "base_hr": round(bhr, 3),
                "incremental": inc,
                "bands": bands,
                "bands_incremental_basis_p50": {
                    b: round(v["p50"] / inc["ratio"], 3) for b, v in bands.items()
                },
                "n_resource_hours": int((d["cls"] == cls).sum()),
            }
    curve = {
        og: {b: groups[og]["bands"][b]["p50"] for b in MAIN_BANDS[og]} for og in groups
    }
    out = {
        "_provenance": {
            "derive": "scripts/data/derive_ercot_sced_uc_bands.py",
            "precommit": "docs/records/ercot/ucmilp/PRECOMMIT-ucmilp-bands-ercot-2026-10-14.md",
            "ruling": "UC-DESK phase-1a authorization on owner decision 8 (2026-10-14)",
            "derived_on": date.today().isoformat(),
            "sced_delivery_years": args.years,
            "n_source_files": len(files),
            "gas_basis": (
                "HH daily + measured monthly EP basis (dispatch basis; ERCOT-117/118)"
                if args.gas_basis == "ep"
                else "HH daily - 0.50 (lineage basis, ERCOT-117-inconsistent)"
            ),
            "hr_basis": (
                "fleet CAMPD-measured operating HR, bin fallback"
                if args.hr_basis == "fleet"
                else "bin Plant_Avg_HR (lineage)"
            ),
            "rule_23": "re-derive only on a SCED corpus or CAMPD-year change",
        },
        "offer_curve_by_group": curve,
        "variants": {
            "CT_PEAKER": {"committed": groups["CT_PEAKER"]["bands"]["committed"]["p50"]}
        },
        "detail": groups,
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
