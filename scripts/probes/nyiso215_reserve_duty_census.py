"""nyiso-215 phase 0 — the seven single-``_peak`` ``CC_REGULAR`` plants.

Measures the five bars pre-registered in
``results/calibration/PREREG-nyiso215-reserve-duty-single-peak.md`` (committed
and pushed before any number below was read):

* **P1** reproduction — the set of ``CC_REGULAR`` plants carried 100 % in
  ``_peak``-suffixed unit ids, and their summed ``pmax``, against nyiso-214
  section 7's committed ``441.7 MW`` census. Carries a declared VOID.
* **P2** causation — the same rebuild with ``cc_reserve_duty_split=False``
  alone, to separate the nyiso-146 duty split from the bin builder's
  small-band filter (nyiso-198's Riverbay 52168 defect).
* **P3** basis asymmetry — the cohort's single ``0.10`` threshold is applied to
  a CAMPD plant-summed ONLINE SHARE at most plants and to an EIA-923 pooled net
  CAPACITY FACTOR where no CEMS record exists. Both statistics are recomputed
  here with ``derive_reserve_duty_cc``'s OWN constructions, for every plant
  that carries both, so the fallback's bias is measured rather than asserted.
  ``derive_reserve_duty_cc.py`` is AUDITED, never re-derived (rule 23
  ``[R-FROZEN-DERIVE]``): this probe writes no artifact of its own.
* **P4** conduct — each cohort plant's implied ECONOMIC ON-SHARE: the share of
  hours in which its ``_peak`` band base marginal cost sits at or below its own
  zone's committed keeper P1 LMP. An UPPER bound on model duty (it ignores
  reserves, ramping, min-up and outages, and ``mc_base`` excludes the P1
  startup markup), compared against the mechanism's own measured duty target.
* **P5** realised dispatch — the ``CC_REGULAR`` ``peak`` band's own hourly MW
  from the keeper's committed ``class_band_hourly`` sidecar. No solve: the
  keeper's committed bundle IS the control (rule 29(b) form 4).

ZERO LP: every fleet rebuild is ``fleet_only=True``.

Usage::

    uv run python scripts/probes/nyiso215_reserve_duty_census.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

BUNDLE = ROOT / "results/calibration/nyiso213_summer_seam"
OUT = ROOT / "results/calibration/_nyiso215_reserve_duty_census.json"
YEARS = (2023, 2024, 2025)

# nyiso-214 section 7's committed census — the P1 reproduction target.
SEVEN = {10621, 54034, 7784, 10620, 54592, 50744, 54593}
NYISO214_MW = 441.7

# nyiso-214 section 6 form A: the duct population's own peak-band MW. P5's
# exceedance bound uses it as the strict ceiling on non-reserve-duty peak MW.
DUCT_BAND_MW = 716.8

CLASS = "CC_REGULAR"


def _build(year: int, meta: dict, **over: object) -> dict:
    """Rebuild the keeper's fleet for ``year`` (no LP), with optional overrides."""
    import scripts.run_calibration as rc

    kwargs = full_run_year_kwargs(meta)
    kwargs.update(over)
    clear_fleet_caches()
    return rc.run_year(year, "NYISO", 8760, bundle_gas_price(meta, year), **kwargs)


def _cc_frame(built: dict) -> pd.DataFrame:
    """Return one row per ``CC_REGULAR`` LP unit: uid, plant, zone, pmax, mc."""
    fa = built["fleet_arrays"]
    gens = built["fleet"]
    if len(gens) != len(fa.unit_ids):
        raise SystemExit("fleet / fleet_arrays misalignment — instrument invalid")
    mc = np.asarray(built["mc_base"], dtype=float)
    # mc_base is (n_gen,) when fuel is flat and (n_gen, T) when hourly; keep
    # the full hourly vector where it exists so P4 never flattens a shape.
    hourly = mc.ndim == 2
    frame = pd.DataFrame(
        {
            "uid": list(fa.unit_ids),
            "plant": np.asarray(fa.plant_code, dtype=int),
            "group": list(fa.plant_group),
            "zone": [g.zone for g in gens],
            "pmax": np.asarray(fa.pmax, dtype=float),
            "row": np.arange(len(fa.unit_ids)),
        }
    )
    frame = frame[frame["group"] == CLASS].reset_index(drop=True)
    frame.attrs["mc"] = mc
    frame.attrs["mc_hourly"] = hourly
    return frame


def _peak_only_plants(cc: pd.DataFrame) -> tuple[set[int], float, dict[int, float]]:
    """Plants whose whole carried capacity sits in ``_peak`` unit ids."""
    carried = cc.groupby("plant")["pmax"].sum()
    peak = (
        cc[cc["uid"].str.endswith("_peak")]
        .groupby("plant")["pmax"]
        .sum()
        .reindex(carried.index)
        .fillna(0.0)
    )
    share = (peak / carried.replace(0.0, np.nan)) * 100.0
    codes = {int(c) for c in share.index[share > 99.9]}
    return codes, float(carried[list(codes)].sum()), {
        int(c): float(carried[c]) for c in codes
    }


def _zone_price(year: int) -> dict[str, np.ndarray]:
    """Committed keeper P1 hourly LMP per zone."""
    df = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        str(z): g.sort_values("hour")["price"].to_numpy(dtype=float)
        for z, g in df.groupby("zone", observed=True)
    }


def _p3_dual_basis() -> dict:
    """Recompute BOTH duty statistics with the derive script's own constructions."""
    sys.path.insert(0, str(ROOT / "scripts" / "data"))
    import derive_reserve_duty_cc as drd
    from derive_campd_gas_commitment_params import (
        _HSL_PCTILE,
        _ONLINE_FRAC,
        class_plant_codes,
    )

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.campd import _ONLINE_MW, states_for_iso
    from market_sim.data.fleet import load_fleet_from_csv

    mapping, _amb = class_plant_codes("NYISO", (CLASS,))
    codes = set(mapping)

    by_plant: dict[int, dict[int, list[np.ndarray]]] = {}
    for state in states_for_iso("NYISO"):
        for year in YEARS:
            path = drd.UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                by_plant.setdefault(int(fid), {}).setdefault(year, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )

    fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"))
    pmax_by_code: dict[int, float] = {}
    for g in fleet:
        c = int(g.plant_code or 0)
        if c in codes and g.plant_group == CLASS:
            pmax_by_code[c] = pmax_by_code.get(c, 0.0) + float(g.pmax_mw)
    e923 = pd.read_parquet(drd.E923_PATH)
    e923 = e923[e923["year"].isin(YEARS)]
    gen_by_code = e923.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()

    rows = []
    for code in sorted(codes):
        cap = pmax_by_code.get(code, 0.0)
        cf = (
            float(gen_by_code.get(code, 0.0)) / (cap * 8760.0 * len(YEARS))
            if cap > 0.0
            else None
        )
        on = None
        if code in by_plant:
            yearly = []
            for year in sorted(by_plant[code]):
                chunks = by_plant[code][year]
                n = min(c.size for c in chunks)
                yearly.append(np.sum([c[:n] for c in chunks], axis=0))
            pooled = np.concatenate(yearly)
            hsl = float(np.percentile(pooled, _HSL_PCTILE))
            if hsl > _ONLINE_MW:
                thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
                on = float((pooled >= thresh).mean())
        rows.append(
            {
                "plant_code": code,
                "model_pmax_mw": round(cap, 3),
                "campd_online_share": round(on, 5) if on is not None else None,
                "e923_pooled_cf": round(cf, 5) if cf is not None else None,
                "ratio_cf_over_onshare": (
                    round(cf / on, 4) if (on and cf is not None and on > 0.0) else None
                ),
                "has_campd": code in by_plant,
            }
        )
    return {"threshold": drd._ONLINE_SHARE_MAX, "plants": rows}


def main() -> None:
    """Measure P1-P5 and write the machine record."""
    ensure_probe_path()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    rec: dict = {
        "session": "nyiso-215",
        "keeper": "2026-09-07-nyiso-213-summer-seam",
        "prereg": "results/calibration/PREREG-nyiso215-reserve-duty-single-peak.md",
        "zero_lp": True,
    }

    # ---- P1 / P2 (2025 fleet) -------------------------------------------
    built = _build(2025, meta)
    cc = _cc_frame(built)
    codes, mw, carried = _peak_only_plants(cc)
    rec["P1"] = {
        "peak_only_plants": sorted(codes),
        "summed_pmax_mw": round(mw, 3),
        "per_plant_mw": {str(k): round(v, 3) for k, v in sorted(carried.items())},
        "nyiso214_target_mw": NYISO214_MW,
        "set_matches": codes == SEVEN,
        "abs_pct_diff_mw": round(abs(mw - NYISO214_MW) / NYISO214_MW * 100.0, 3),
        "void": (codes != SEVEN) or abs(mw - NYISO214_MW) / NYISO214_MW > 0.05,
    }
    keeper_peak_mw = float(cc[cc["uid"].str.endswith("_peak")]["pmax"].sum())

    off = _build(2025, meta, cc_reserve_duty_split=False)
    cc_off = _cc_frame(off)
    tranches_off = {
        int(c): int(n)
        for c, n in cc_off[cc_off["plant"].isin(SEVEN)]
        .groupby("plant")["uid"]
        .nunique()
        .items()
    }
    off_peak_mw = float(cc_off[cc_off["uid"].str.endswith("_peak")]["pmax"].sum())
    multi = sum(1 for n in tranches_off.values() if n >= 2)
    rec["P2"] = {
        "tranche_count_with_split_off": tranches_off,
        "n_plants_multi_tranche": multi,
        "class_peak_mw_keeper": round(keeper_peak_mw, 3),
        "class_peak_mw_split_off": round(off_peak_mw, 3),
        "class_peak_mw_fall": round(keeper_peak_mw - off_peak_mw, 3),
        "fires": multi >= 5 and (keeper_peak_mw - off_peak_mw) >= 400.0,
        "refutes": sum(1 for n in tranches_off.values() if n < 2) >= 3,
    }
    del off, cc_off

    # ---- P3 --------------------------------------------------------------
    dual = _p3_dual_basis()
    ratios = [
        r["ratio_cf_over_onshare"]
        for r in dual["plants"]
        if r["ratio_cf_over_onshare"] is not None
    ]
    med = float(np.median(ratios)) if ratios else float("nan")
    low = [
        r["ratio_cf_over_onshare"]
        for r in dual["plants"]
        if r["ratio_cf_over_onshare"] is not None
        and r["campd_online_share"] is not None
        and r["campd_online_share"] <= 0.10
    ]
    cf_7784 = next(
        (r["e923_pooled_cf"] for r in dual["plants"] if r["plant_code"] == 7784), None
    )
    implied = cf_7784 / med if (cf_7784 and med == med and med > 0) else None
    rec["P3"] = {
        "dual_basis": dual,
        "n_plants_with_both": len(ratios),
        "median_ratio_cf_over_onshare": round(med, 4),
        "median_ratio_low_duty_subset": (
            round(float(np.median(low)), 4) if low else None
        ),
        "n_low_duty_subset": len(low),
        "a_fires_bias_material": med < 0.85,
        "plant_7784_e923_cf": cf_7784,
        "plant_7784_implied_online_share": (
            round(implied, 5) if implied is not None else None
        ),
        "b_holds_membership_survives": (
            implied is not None and implied < dual["threshold"]
        ),
    }

    # ---- P4 / P5 ---------------------------------------------------------
    duty = pd.read_csv(ROOT / "data/raw/_processed-legacy/reserve_duty_cc_NYISO.csv")
    duty_stat = dict(zip(duty["plant_code"].astype(int), duty["duty_stat"].astype(float)))
    per_year: dict[str, dict] = {}
    for year in YEARS:
        b = _build(year, meta) if year != 2025 else built
        f = _cc_frame(b) if year != 2025 else cc
        mc = f.attrs["mc"]
        hourly = f.attrs["mc_hourly"]
        prices = _zone_price(year)
        rows = []
        for code in sorted(SEVEN):
            sub = f[(f["plant"] == code) & f["uid"].str.endswith("_peak")]
            if sub.empty:
                rows.append({"plant_code": code, "error": "no _peak tranche"})
                continue
            zone = str(sub["zone"].iloc[0])
            p = prices.get(zone)
            if p is None:
                rows.append({"plant_code": code, "error": f"no price for {zone}"})
                continue
            r = int(sub["row"].iloc[0])
            m = mc[r, : p.size] if hourly else np.full(p.size, float(mc[r]))
            rows.append(
                {
                    "plant_code": code,
                    "zone": zone,
                    "pmax_mw": round(float(sub["pmax"].sum()), 3),
                    "mc_peak_mean_usd_mwh": round(float(np.mean(m)), 3),
                    "zone_lmp_mean_usd_mwh": round(float(np.mean(p)), 3),
                    "implied_on_share": round(float((m <= p).mean()), 5),
                    "measured_duty_stat": duty_stat.get(code),
                }
            )
        ok = [r for r in rows if "error" not in r]
        w = np.array([r["pmax_mw"] for r in ok], dtype=float)
        imp = float(np.average([r["implied_on_share"] for r in ok], weights=w))
        meas = float(np.average([r["measured_duty_stat"] for r in ok], weights=w))
        band = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
        band = band[
            (band["pass"] == "P1") & (band["klass"] == CLASS) & (band["band"] == "peak")
        ].sort_values("hour")
        bmw = band["mw"].to_numpy(dtype=float)
        per_year[str(year)] = {
            "plants": rows,
            "cap_weighted_implied_on_share": round(imp, 5),
            "cap_weighted_measured_duty": round(meas, 5),
            "ratio_implied_over_measured": round(imp / meas, 3) if meas > 0 else None,
            "band_peak_mean_mw": round(float(np.mean(bmw)), 3),
            "band_peak_max_mw": round(float(np.max(bmw)), 3),
            "band_peak_p95_mw": round(float(np.percentile(bmw, 95)), 3),
            "band_hours_above_duct_ceiling_pct": round(
                float((bmw > DUCT_BAND_MW).mean()) * 100.0, 4
            ),
        }
        if year != 2025:
            del b, f
    rec["P4_P5_by_year"] = per_year
    ratios_y = [
        v["ratio_implied_over_measured"]
        for v in per_year.values()
        if v["ratio_implied_over_measured"] is not None
    ]
    rec["P4"] = {
        "ratio_by_year": ratios_y,
        "fires_under_correction": sum(1 for r in ratios_y if r > 3.0) >= 2,
        "refutes_right_sized": sum(1 for r in ratios_y if r <= 1.5) >= 2,
    }
    y25 = per_year["2025"]
    rec["P5"] = {
        "mean_mw_2025": y25["band_peak_mean_mw"],
        "hours_above_716_8_pct_2025": y25["band_hours_above_duct_ceiling_pct"],
        "fires": (
            y25["band_peak_mean_mw"] >= 120.0
            and y25["band_hours_above_duct_ceiling_pct"] >= 2.0
        ),
        "refutes": (
            y25["band_peak_mean_mw"] < 40.0
            and y25["band_hours_above_duct_ceiling_pct"] < 0.5
        ),
    }

    OUT.write_text(json.dumps(rec, indent=1, sort_keys=False) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "P3"}, indent=1)[:4000])
    print("P3 summary:", json.dumps({k: v for k, v in rec["P3"].items() if k != "dual_basis"}, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
