"""PJM-NEXT-28 phase 0 (ZERO LP): size the "sunk no-load in the committed rung" hypothesis.

Hypothesis under test. In P1 the committed tranche of a CC (and of coal) carries no-load
folded into its offer ``mc`` (average HR including no-load). Once P0 fixes commitment,
no-load is sunk and PJM's LMP excludes it (it is paid through make-whole). Pricing the
committed rung at the plant's measured CAMPD INCREMENTAL heat rate would lower the
low-end price floor, which (PJM-NEXT-17 card 1b) drives the COAL_BIT over-loading.

Inputs (all read-only):

* W0 keeper bundle ``results/calibration/w0_pjm_span/hourly/``:
  ``unit_marginal_<Y>.parquet`` (per LP unit-hour ``mw``, ``cap_mw``, P1 offer ``mc``,
  int8 ``marginal`` = interior and zero reduced cost, ``scripts/lib/unit_marginal.py``)
  and ``system_<Y>.parquet`` (zonal P1 ``price`` and ``demand``). When the working tree
  lacks a file it is read straight from the ``origin/main`` blob (no file is written).
  Class = ``plant_group``; tranche = the unit-id suffix (``committed``, ``econcNN``,
  ``econlo``/``econhi``, ``peak``, ``mustrun``, ``sync``, ...).
* L2 incremental-HR artifact (422 CC plant-years), read from commit
  ``d8cf825a`` (branch ``claude/closeout-pjm-l2``, never merged):
  ``data/raw/_validation-source/pjm_cc_incremental_hr.csv`` ``inc_hr_net``; the year's
  row, else the plant's mean over its years (the L2 probe's own lookup).
* Committed-rung HR per CC plant: the measured CC artifact the keeper fleet carries
  (``campd_cc_heat_rates_PJM.csv``, the solve year's ``ok`` row else pooled — the
  ``campd_bins._measured_rate_map`` rule), else its eGRID fallback, else the year's
  capacity-weighted committed HR from the L2 RESULT (an APPROXIMATION, flagged).
  The keeper's CC_REGULAR ``committed`` band is 1.0, so ``mc_c - VOM_cc = HR_c x
  (gas + RGGI)``.
* Gas: the NEXT-11 series — Henry Hub daily (ffill) + ``GAS_BASIS_DIFFERENTIAL['PJM']``.

Price attribution. Zone prices differ every hour by loss/hurdle spreads, so a zone-hour
is usually priced by a marginal unit in another zone. Each zone-hour is anchored to the
hour's marginal unit (``marginal == 1``, any zone) whose ``mc`` is nearest to the zone
price in ratio, if within :data:`ANCHOR_TOL` (the observed intra-PJM spread); a zone
with no such unit is "unanchored" (storage, hydro, slack, a binding limit) and its price
is left unchanged. A zone price moves one-for-one (times ``price/mc``) with its anchor.

Coal. The keeper prices the COAL_* committed rung at band multiplier 0.512-0.684 of
average HR (``offer_curve_overrides``), already BELOW any measured incremental HR, so
it carries no folded no-load to remove: its drop is 0 by construction. (PJM coal CAMPD
unit-level hourly 2019-25 is not on disk either; no coal ratio is derived.)

Readings (pre-fixed, PJM-NEXT-28 charter):

* R1 — load-weighted share of zone-hours whose anchor is a CC or coal COMMITTED tranche.
* R2 — price-drop bound in those hours: ``(mc_c - VOM_cc) x (1 - HR_incr/HR_c)`` (VOM
  unchanged; CC_REGULAR plants covered by the artifact; CC_CHP / coal / uncovered = 0),
  signed; mean over anchored-committed zone-hours, and the shift of the p10 implied HR
  (load-weighted system price / gas). PASS iff p10 shift >= 0.5 in 2019, 2020 and 2021.
* R3 — COAL_BIT econ/peak MWh in zone-hours where ``p_new < mc <= p_old`` (TWh/yr).
  PASS iff >= 3 TWh in 2019 and 2021 AND 2023 and 2024 each below both 2019 and 2021.
* Verdict CHARTER iff R2 and R3 pass.

Writes ``results/phase0/pjm/_pjmnext28_sunk_noload.json``.
Run: ``python3 scripts/probes/_pjmnext28_sunk_noload.py [YEAR ...]``
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL, VOM  # noqa: E402

BUNDLE_REL = "results/calibration/w0_pjm_span"
OUT = REPO / "results/phase0/pjm/_pjmnext28_sunk_noload.json"
L2_SHA = "d8cf825a90939b5c73da77d98d938e4dc4ae831a"
L2_ART = "data/raw/_validation-source/pjm_cc_incremental_hr.csv"
CC_HR = REPO / "data/raw/_processed-legacy/campd_cc_heat_rates_PJM.csv"
HH = REPO / "data/raw/gas-prices/henry_hub_daily.csv"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
VOM_CC = float(VOM["gas_cc"])
#: Max |price/mc - 1| for anchoring a zone to a marginal unit: the observed intra-PJM
#: zonal spread (~4.7 % between the cheapest and dearest internal zone, 2019) plus margin.
ANCHOR_TOL = 0.06
#: Year cap-weighted committed HR, L2 RESULT (fallback approximation only).
COMMITTED_HR_YEAR = {
    2019: 7.317,
    2020: 7.319,
    2021: 7.345,
    2022: 7.325,
    2023: 7.279,
    2024: 7.262,
    2025: 7.335,
}
CC_CLASSES = ("CC_REGULAR", "CC_CHP")
COAL_PREFIX = "COAL_"
R2_MIN_SHIFT = 0.5
R2_YEARS = (2019, 2020, 2021)
R3_MIN_TWH = 3.0
# Real reference (NEXT-11 §5, NEXT-12): actual p10 implied HR; share of hours < 6.5 x gas.
REAL_P10 = {2019: 5.2, 2020: 4.8, 2021: 5.1, 2022: 5.5, 2023: 4.9, 2024: 5.0, 2025: 5.1}
REAL_BELOW_65 = {2019: 0.36, 2020: 0.45}


def _parquet(name: str, **kw) -> pd.DataFrame:
    """Read a keeper sidecar from the tree, else from the origin/main blob in memory."""
    p = REPO / BUNDLE_REL / "hourly" / name
    if p.exists():
        return pq.read_table(p, **kw).to_pandas()
    blob = subprocess.run(
        ["git", "-C", str(REPO), "show", f"origin/main:{BUNDLE_REL}/hourly/{name}"],
        check=True,
        capture_output=True,
    ).stdout
    return pq.read_table(io.BytesIO(blob), **kw).to_pandas()


def gas_daily() -> pd.Series:
    """NEXT-11 delivered gas: HH daily ffilled + the PJM delivered basis."""
    s = pd.read_csv(HH, parse_dates=["date"]).set_index("date")["price_usd_mmbtu"]
    s = s.sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    return s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])


def incremental_hr(year: int) -> dict[int, float]:
    """L2 artifact slope for ``year`` (plant mean where the year is absent)."""
    txt = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{L2_SHA}:{L2_ART}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    df = pd.read_csv(io.StringIO(txt))
    df = df[np.isfinite(df["inc_hr_net"])]
    out = df.groupby("plant_code")["inc_hr_net"].mean().to_dict()
    out.update(df[df["year"] == year].set_index("plant_code")["inc_hr_net"].to_dict())
    return {int(k): float(v) for k, v in out.items()}


def committed_hr(year: int) -> tuple[dict[int, float], dict[int, float]]:
    """(measured CC HR by the keeper's year-else-pooled rule, eGRID fallback)."""
    a = pd.read_csv(CC_HR)
    rate = pd.to_numeric(a["heat_rate"], errors="coerce")
    ok = a[a["flag"].astype(str).isin({"ok", "eia923_identity"}) & (rate > 0)]
    meas = ok[ok["year"] == 0].set_index("plant_code")["heat_rate"].to_dict()
    meas.update(ok[ok["year"] == year].set_index("plant_code")["heat_rate"].to_dict())
    fb = a[a["year"] == 0].set_index("plant_code")["model_heat_rate_egrid"].to_dict()
    fb.update(a[a["year"] == year].set_index("plant_code")["model_heat_rate_egrid"].to_dict())
    clean = lambda d: {int(k): float(v) for k, v in d.items() if np.isfinite(v)}  # noqa: E731
    return clean(meas), clean(fb)


def _tranche(uid: pd.Series) -> pd.Series:
    """Tranche kind from the unit-id suffix (econ*, peak, committed, mustrun, sync, other)."""
    sfx = uid.str.rsplit("_", n=1).str[-1]
    kind = np.where(sfx.str.startswith("econ"), "econ", sfx)
    kind = np.where(pd.Series(kind).str.startswith("peak"), "peak", kind)
    keep = {"econ", "peak", "committed", "mustrun", "sync"}
    return pd.Series([k if k in keep else "other" for k in kind], index=uid.index)


def p10_hr(price: np.ndarray, gas: np.ndarray) -> float:
    """p10 of the implied heat rate price / gas."""
    return float(np.nanquantile(price / gas, 0.10))


def run_year(year: int, gas: pd.Series) -> dict:
    """All three readings for one year."""
    sysd = _parquet(f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"][["zone", "hour", "price", "demand"]].copy()
    sysd["zone"] = sysd["zone"].astype(str)
    cols = ["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"]
    m = _parquet(
        f"unit_marginal_{year}.parquet", columns=cols, filters=[("marginal", "=", 1)]
    )
    for c in ("unit_id", "plant_group", "zone"):
        m[c] = m[c].astype(str)
    m["kind"] = _tranche(m["unit_id"])

    # --- R2 per-unit drop -------------------------------------------------------
    inc = incremental_hr(year)
    meas, fb = committed_hr(year)
    is_cc_com = (m["plant_group"] == "CC_REGULAR") & (m["kind"] == "committed")
    pc = m["plant_code"].astype(int)
    hr_c = pc.map(meas)
    src = np.where(hr_c.notna(), "measured", "")
    hr_fb = pc.map(fb)
    src = np.where((src == "") & hr_fb.notna(), "egrid", src)
    hr_c = hr_c.fillna(hr_fb)
    src = np.where(src == "", "year_capw_approx", src)
    hr_c = hr_c.fillna(COMMITTED_HR_YEAR[year])
    hr_i = pc.map(inc)
    covered = is_cc_com & hr_i.notna()
    m["drop"] = np.where(
        covered, (m["mc"] - VOM_CC) * (1.0 - hr_i / hr_c), 0.0
    ).astype(float)
    m["cc_coal_com"] = (m["kind"] == "committed") & (
        m["plant_group"].isin(CC_CLASSES) | m["plant_group"].str.startswith(COAL_PREFIX)
    )

    # --- anchor every zone-hour to the hour's nearest-in-ratio marginal unit ----
    x = sysd.merge(
        m[["hour", "unit_id", "plant_group", "kind", "mc", "drop", "cc_coal_com"]],
        on="hour",
    )
    x = x[x["mc"] > 0]
    x["dev"] = (x["price"] / x["mc"] - 1.0).abs()
    x = x[x["dev"] <= ANCHOR_TOL]
    a = x.loc[x.groupby(["zone", "hour"])["dev"].idxmin()]
    a = a.assign(dz=a["drop"] * a["price"] / a["mc"])
    z = sysd.merge(
        a[["zone", "hour", "plant_group", "kind", "cc_coal_com", "dz"]],
        on=["zone", "hour"],
        how="left",
    )
    z["anchored"] = z["kind"].notna()
    z["cc_coal_com"] = z["cc_coal_com"].fillna(False).astype(bool)
    z["dz"] = z["dz"].fillna(0.0)
    z["price_new"] = z["price"] - z["dz"]
    # sensitivity: the hypothesis' one-sided form (a rung whose incremental HR exceeds
    # its committed HR is left unchanged rather than raised) - an upper bound on the drop
    z["price_new_clip"] = z["price"] - z["dz"].clip(lower=0.0)
    w = z["demand"].to_numpy(float)
    W = w.sum()
    r1 = float(w[z["cc_coal_com"].to_numpy()].sum() / W)
    cc_com = z["cc_coal_com"] & z["plant_group"].isin(CC_CLASSES)
    coal_com = z["cc_coal_com"] & z["plant_group"].fillna("").str.startswith(COAL_PREFIX)
    zcov = z[z["dz"] != 0.0]

    # load-weighted system price per hour -> implied HR
    z["pw"], z["pnw"] = z["price"] * z["demand"], z["price_new"] * z["demand"]
    z["pcw"] = z["price_new_clip"] * z["demand"]
    h = z.groupby("hour")[["pw", "pnw", "pcw", "demand"]].sum().sort_index()
    p_old = (h["pw"] / h["demand"]).to_numpy()
    p_new = (h["pnw"] / h["demand"]).to_numpy()
    p_clip = (h["pcw"] / h["demand"]).to_numpy()
    days = pd.date_range(f"{year}-01-01", periods=len(h), freq="h").normalize()
    g = gas.reindex(days).to_numpy(float)
    p10_old, p10_new = p10_hr(p_old, g), p10_hr(p_new, g)
    p10_clip = p10_hr(p_clip, g)

    # sanity: CC committed rung's implied fuel (+RGGI) vs delivered gas
    ccc = m[is_cc_com].copy()
    ccc["fuel"] = (ccc["mc"] - VOM_CC) / hr_c[is_cc_com]
    ccc["gas"] = gas.reindex(
        (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(ccc["hour"], "h")).dt.normalize()
    ).to_numpy()

    # --- R3 COAL_BIT econ/peak unloading bound -----------------------------------
    cb = _parquet(
        f"unit_marginal_{year}.parquet",
        columns=["unit_id", "zone", "hour", "mw", "mc"],
        filters=[("plant_group", "=", "COAL_BIT"), ("mw", ">", 0.0)],
    )
    cb["unit_id"], cb["zone"] = cb["unit_id"].astype(str), cb["zone"].astype(str)
    cb = cb[_tranche(cb["unit_id"]).isin(["econ", "peak"]).to_numpy()]
    cb = cb.merge(
        z[["zone", "hour", "price", "price_new", "price_new_clip"]], on=["zone", "hour"]
    )
    band = (cb["mc"] > cb["price_new"]) & (cb["mc"] <= cb["price"] + 1e-6)
    r3_twh = float(cb.loc[band, "mw"].sum() / 1e6)
    bandc = (cb["mc"] > cb["price_new_clip"]) & (cb["mc"] <= cb["price"] + 1e-6)
    r3_clip = float(cb.loc[bandc, "mw"].sum() / 1e6)

    is_cc = m["plant_group"] == "CC_REGULAR"
    return {
        "year": year,
        "zone_hours": int(len(z)),
        "anchored_load_share": round(float(w[z["anchored"].to_numpy()].sum() / W), 4),
        "R1_cc_or_coal_committed_load_share": round(r1, 4),
        "R1_cc_committed_load_share": round(float(w[cc_com.to_numpy()].sum() / W), 4),
        "R1_coal_committed_load_share": round(float(w[coal_com.to_numpy()].sum() / W), 4),
        "R2_covered_load_share": round(float(zcov["demand"].sum() / W), 4),
        "R2_mean_drop_in_cc_coal_committed_hours": round(
            float(np.average(z.loc[z["cc_coal_com"], "dz"], weights=z.loc[z["cc_coal_com"], "demand"]))
            if z["cc_coal_com"].any() and z.loc[z["cc_coal_com"], "demand"].sum() > 0
            else 0.0,
            3,
        ),
        "R2_mean_drop_in_covered_hours": round(
            float(np.average(zcov["dz"], weights=zcov["demand"]))
            if len(zcov) and zcov["demand"].sum() > 0
            else 0.0,
            3,
        ),
        "R2_mean_drop_all_hours": round(float(np.average(z["dz"], weights=w)), 4),
        "p10_implied_hr_old": round(p10_old, 3),
        "p10_implied_hr_new": round(p10_new, 3),
        "R2_p10_shift": round(p10_old - p10_new, 3),
        "share_hours_below_6p5_gas_old": round(float(np.mean(p_old / g < 6.5)), 4),
        "share_hours_below_6p5_gas_new": round(float(np.mean(p_new / g < 6.5)), 4),
        "real_p10_implied_hr": REAL_P10.get(year),
        "real_share_below_6p5_gas": REAL_BELOW_65.get(year),
        "R3_coal_bit_unload_twh": round(r3_twh, 3),
        "sens_clip_p10_shift": round(p10_old - p10_clip, 3),
        "sens_clip_R3_twh": round(r3_clip, 3),
        "sens_clip_mean_drop_all_hours": round(float(np.average(z["dz"].clip(lower=0.0), weights=w)), 4),
        "cc_committed_marginal_unit_hours": int(is_cc_com.sum()),
        "cc_committed_covered_unit_hours": int(covered.sum()),
        "cc_committed_hr_source_unit_hours": {
            k: int(v) for k, v in pd.Series(src[is_cc_com.to_numpy()]).value_counts().items()
        },
        "cc_committed_mean_hr_c": round(float(hr_c[covered].mean()), 3) if covered.any() else None,
        "cc_committed_mean_hr_incr": round(float(hr_i[covered].mean()), 3) if covered.any() else None,
        "cc_committed_share_incr_below_committed": round(
            float((hr_i[covered] < hr_c[covered]).mean()), 3
        )
        if covered.any()
        else None,
        "cc_committed_mean_unit_drop": round(float(m.loc[covered, "drop"].mean()), 3)
        if covered.any()
        else None,
        "sanity_cc_committed_fuel_over_gas_median": round(
            float(np.nanmedian(ccc["fuel"] / ccc["gas"])), 3
        )
        if len(ccc)
        else None,
        "marginal_unit_hours_cc_regular": int(is_cc.sum()),
    }


def main(years: list[int]) -> None:
    """Run the readings, apply the pre-fixed gates, write the JSON."""
    gas = gas_daily()
    rows = []
    for y in years:
        r = run_year(y, gas)
        rows.append(r)
        print(
            f"{y}: R1={r['R1_cc_or_coal_committed_load_share']:.3f} "
            f"(cc {r['R1_cc_committed_load_share']:.3f} coal {r['R1_coal_committed_load_share']:.3f}) "
            f"R2 mean={r['R2_mean_drop_in_cc_coal_committed_hours']:+.3f} "
            f"p10 {r['p10_implied_hr_old']:.2f}->{r['p10_implied_hr_new']:.2f} "
            f"shift={r['R2_p10_shift']:+.3f} R3={r['R3_coal_bit_unload_twh']:.3f} TWh "
            f"anch={r['anchored_load_share']:.3f}",
            flush=True,
        )
    by = {r["year"]: r for r in rows}
    r2 = None
    if all(y in by for y in R2_YEARS):
        r2 = all(by[y]["R2_p10_shift"] >= R2_MIN_SHIFT for y in R2_YEARS)
    r3 = None
    if all(y in by for y in (2019, 2021, 2023, 2024)):
        t = {y: by[y]["R3_coal_bit_unload_twh"] for y in (2019, 2021, 2023, 2024)}
        r3 = (
            t[2019] >= R3_MIN_TWH
            and t[2021] >= R3_MIN_TWH
            and max(t[2023], t[2024]) < min(t[2019], t[2021])
        )
    verdict = "CHARTER" if (r2 and r3) else "NOT CHARTERED"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "probe": "PJM-NEXT-28 phase 0: sunk no-load in the committed rung (zero LP)",
                "keeper_bundle": BUNDLE_REL,
                "l2_artifact": f"{L2_SHA}:{L2_ART}",
                "anchor_tol": ANCHOR_TOL,
                "method": __doc__,
                "gates": {
                    "R2": f"p10 implied-HR shift >= {R2_MIN_SHIFT} in {list(R2_YEARS)}",
                    "R3": f">= {R3_MIN_TWH} TWh in 2019 and 2021; 2023, 2024 < both",
                },
                "R2_pass": r2,
                "R3_pass": r3,
                "verdict": verdict,
                "years": rows,
            },
            indent=2,
        )
    )
    print(f"R2 pass={r2} R3 pass={r3} -> {verdict}; wrote {OUT}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
