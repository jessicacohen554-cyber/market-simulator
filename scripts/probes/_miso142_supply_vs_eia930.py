"""miso-142 gate G-C — model class dispatch vs measured EIA-930, hour by hour.

No solve.  Tests PREREG ``results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md``
predictions **P4** (O2 coal), **P6** (O3 hydro), **P8** (O5 imports) and the
quantity half of **P9** (H1), by comparing the keeper's committed
``hourly/class_hourly_<year>.parquet`` against EIA-930's measured MISO
generation-by-fuel and interchange on ONE clock and ONE sign convention.

**Conventions, all fixed in the PREREG before any number here was seen:**

* **Clock (PREREG §2.3).**  EIA-930 rows come through the repo's own
  ``eia930.frames._eia_hourly_frame_filled("MISO", y)`` — 8760 rows, row *k* =
  local hour *k*, Feb 29 dropped, the same clock as the keeper's sidecars.  Not
  hand-rolled: the loader's own docstring records that its HE->interval-beginning
  correction is the fix for a +1 h shift that hit **MISO-2025 specifically**.
* **Interchange sign (PREREG §2.2, TRAP 2).**  EIA-930 ``Total interchange`` is
  the standard convention, positive = net EXPORT, established from the 74,390-row
  identity ``NG - D - TI ~ 0``.  So
  ``actual_net_import_MW := -(Total interchange)``, compared against the model's
  ``import`` klass which is already net-import-positive.  **G-C0** re-verifies the
  direction on the summer months before any shape is compared.
* **Summer (PREREG §2.4).**  Price windows are miso-137's Jun-Aug; the miso-139
  cushion basis is Jun-Sep.  Both are reported wherever they could be confused.
* **TRAP 5, the coal alias.**  The sidecar splits coal into
  ``COAL_BIT``/``COAL_LIGNITE``/``COAL_PRB``; every mapping below is explicit and
  asserted, so an unmapped class fails loudly instead of silently reading zero.
* **TRAP 7, the EIA-930 adjustment residual.**  The BA identity does NOT close
  (median |NG - D - TI| ~ 1.6 GW).  The residual is reported for every window
  alongside the deltas, and no delta below it is asserted.

**A basis caveat stated rather than buried:** the model's class dispatch is
GRID-DELIVERED (no behind-the-meter CHP host add-back) while EIA-930 ``Net
generation`` is BA-reported.  That gap lands almost entirely on the CHP classes,
so the gas comparison is reported BOTH with and without CHP and the difference
is shown.  hydro / OTHER / import carry no material CHP component, which is why
the H1 test rests on those three.

Probe hygiene (miso-140b §6): REPO ROOT on ``sys.path``, ``load_zonal_shares``
asserted non-None.

Usage::

    .venv/bin/python scripts/probes/_miso142_supply_vs_eia930.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso137_c3a_gap_decomposition import HOURS, month_of_hour  # noqa: E402

KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso142_supply_vs_eia930.json"
YEARS = (2023, 2024, 2025)  # rule 22

# PREREG §2.4 -- the two summer definitions, both carried.
SUMMER_JJA = (6, 7, 8)  # miso-137 SEASONS, the price basis
SUMMER_JJAS = (6, 7, 8, 9)  # miso-139 cushion basis
W1_MONTHS, W1_HOD = (6, 7), (8, 21)  # the owner's O1 window
AFT_HOD = (12, 13, 14, 15, 16, 17)  # the G-B price window's hours

# TRAP 5: EXPLICIT map, asserted below.  A missing sidecar column is an error,
# never a silent zero (miso-141: an unmapped COAL lookup handed back ~32 GW of
# phantom headroom).
MODEL_GROUPS: dict[str, tuple[str, ...]] = {
    "coal": ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB"),
    "gas_merchant": ("CC_REGULAR", "CT_PEAKER", "ST_GAS"),
    "gas_chp": ("CC_CHP", "CT_CHP", "ST_CHP"),
    "hydro": ("hydro",),
    "nuclear": ("nuclear",),
    "solar": ("solar",),
    "wind": ("wind",),
    "other": ("OTHER",),
    "biomass": ("biomass",),
    "oil": ("oil",),
    "import": ("import",),
}
EIA_COL = {
    "coal": "NG: COL",
    "gas": "NG: NG",
    "hydro": "NG: WAT",
    "nuclear": "NG: NUC",
    "solar": "NG: SUN",
    "wind": "NG: WND",
    "other": "NG: OTH",
    "battery": "NG: BAT",
}


def model_classes(year: int) -> pd.DataFrame:
    """P1 class dispatch as an (8760 x klass) frame on the model's clock."""
    df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    piv = df.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(HOURS)).fillna(0.0)
    piv.columns = [str(c) for c in piv.columns]
    for name, cols in MODEL_GROUPS.items():
        missing = [c for c in cols if c not in piv.columns]
        assert not missing, (
            f"group {name!r}: sidecar columns {missing} absent (have "
            f"{sorted(piv.columns)}) -- an unmapped class reads ZERO and would "
            "silently understate the model side (TRAP 5, miso-141)"
        )
    return piv


def eia930(year: int) -> pd.DataFrame:
    """Measured EIA-930 MISO rows on the model's own 8760 clock (PREREG §2.3)."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    f = _eia_hourly_frame_filled("MISO", year)
    assert f is not None and len(f) == HOURS, f"EIA-930 MISO {year} not on clock"
    return f.reset_index(drop=True)


def cv(x: np.ndarray) -> float:
    """Coefficient of variation of a 24-point hour-of-day profile."""
    m = float(np.nanmean(x))
    return float(np.nanstd(x) / abs(m)) if m else float("nan")


def hod_profile(v: np.ndarray, sel: np.ndarray, hod: np.ndarray) -> list[float]:
    """Mean of ``v`` by hour-of-day over the hours in ``sel`` (NaN-safe)."""
    return [
        round(float(np.nanmean(v[sel & (hod == h)])), 2) if (sel & (hod == h)).any()
        else float("nan")
        for h in range(24)
    ]


def pearson(a: list[float], b: list[float]) -> float:
    x, y = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    return round(float(np.corrcoef(x[ok], y[ok])[0, 1]), 4)


def main() -> None:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, (
        "load_zonal_shares returned None -- repo root is off sys.path (miso-140b §6)"
    )

    hr = np.arange(HOURS)
    mon, hod = month_of_hour(hr), hr % 24
    w1 = np.isin(mon, W1_MONTHS) & (hod >= W1_HOD[0]) & (hod < W1_HOD[1])
    jja = np.isin(mon, SUMMER_JJA)
    jjas = np.isin(mon, SUMMER_JJAS)
    jja_aft = jja & np.isin(hod, AFT_HOD)

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "gate": "G-C (H1 vs H0: quantity)",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "conventions": {
            "interchange": "actual_net_import_MW = -(EIA-930 'Total interchange'); "
            "positive = net import into MISO (PREREG §2.2)",
            "clock": "eia930.frames._eia_hourly_frame_filled (PREREG §2.3)",
            "summer_price_basis": "Jun-Aug (miso-137)",
            "summer_cushion_basis": "Jun-Sep (miso-139)",
            "model_basis": "grid-delivered P1 class dispatch, no BTM CHP add-back",
        },
        "years": {},
    }

    for year in YEARS:
        mdl = model_classes(year)
        act = eia930(year)

        m = {k: mdl[list(c)].sum(axis=1).to_numpy(float) for k, c in MODEL_GROUPS.items()}
        m["gas_all"] = m["gas_merchant"] + m["gas_chp"]
        a = {k: act[c].to_numpy(float) for k, c in EIA_COL.items()}
        a["net_import"] = -act["Total interchange"].to_numpy(float)
        # TRAP 7: the BA identity's own residual, the instrument's noise floor.
        resid = (
            act["Net generation"].to_numpy(float)
            - act["Demand"].to_numpy(float)
            - act["Total interchange"].to_numpy(float)
        )

        # ---- G-C0: the direction verification (PREREG §2.2) ---------------
        gc0_mean = float(np.nanmean(a["net_import"][jja]))
        yr: dict = {
            "G_C0_direction": {
                "window": "Jun-Aug, all hours",
                "actual_net_import_mean_mw": round(gc0_mean, 1),
                "pass": bool(gc0_mean > 0),
                "rule": "must be POSITIVE (net import) or the sign convention is "
                "wrong and the session stops",
            },
            "eia930_adjustment_residual_mw": {
                "median_abs_year": round(float(np.nanmedian(np.abs(resid))), 1),
                "median_abs_W1": round(float(np.nanmedian(np.abs(resid[w1]))), 1),
                "mean_W1": round(float(np.nanmean(resid[w1])), 1),
            },
            "windows": {},
            "hod_profiles_JJA": {},
            "annual_twh": {},
        }

        # ---- annual level (P6's level leg) --------------------------------
        for name, mv, av in (
            ("coal", m["coal"], a["coal"]),
            ("gas_merchant_only", m["gas_merchant"], a["gas"]),
            ("gas_all_incl_chp", m["gas_all"], a["gas"]),
            ("hydro", m["hydro"], a["hydro"]),
            ("nuclear", m["nuclear"], a["nuclear"]),
            ("wind", m["wind"], a["wind"]),
            ("solar", m["solar"], a["solar"]),
            ("other_vs_NG_OTH", m["other"], a["other"]),
            ("other_plus_bio_oil_vs_NG_OTH", m["other"] + m["biomass"] + m["oil"], a["other"]),
            ("import", m["import"], a["net_import"]),
        ):
            mt, at = float(np.nansum(mv)) / 1e6, float(np.nansum(av)) / 1e6
            yr["annual_twh"][name] = {
                "model": round(mt, 4),
                "actual": round(at, 4),
                "delta": round(mt - at, 4),
                "pct": round(100.0 * (mt - at) / at, 1) if at else None,
            }

        # ---- window means (P4 / P9) ---------------------------------------
        for wname, sel in (
            ("W1_jun_jul_h8_20", w1),
            # The G-B price window, carried here so G-C2 can multiply a deltaQ
            # and a deficit measured on the SAME hours -- pairing them across
            # different windows would be exactly the basis crossing this
            # session's PREREG §2.4 warns about.
            ("JJA_h12_17", jja_aft),
            ("JJA_all_hours", jja),
            ("JJAS_all_hours", jjas),
        ):
            rec = {"n_hours": int(sel.sum())}
            for name, mv, av in (
                ("coal", m["coal"], a["coal"]),
                ("gas_merchant_only", m["gas_merchant"], a["gas"]),
                ("gas_all_incl_chp", m["gas_all"], a["gas"]),
                ("hydro", m["hydro"], a["hydro"]),
                ("other_vs_NG_OTH", m["other"], a["other"]),
                ("import", m["import"], a["net_import"]),
                ("wind", m["wind"], a["wind"]),
                ("solar", m["solar"], a["solar"]),
                ("nuclear", m["nuclear"], a["nuclear"]),
            ):
                mm, am = float(np.nanmean(mv[sel])), float(np.nanmean(av[sel]))
                rec[name] = {
                    "model_mw": round(mm, 1),
                    "actual_mw": round(am, 1),
                    "delta_mw": round(mm - am, 1),
                    "pct": round(100.0 * (mm - am) / am, 1) if am else None,
                }
            # P9: the H1 quantity -- the three non-thermal objects together.
            dq = sum(
                rec[k]["delta_mw"] for k in ("hydro", "other_vs_NG_OTH", "import")
            )
            rec["H1_deltaQ_hydro_other_import_mw"] = round(dq, 1)
            rec["H1_deltaQ_vs_residual_floor"] = round(
                dq / max(1e-9, float(np.nanmedian(np.abs(resid[sel])))), 2
            )
            yr["windows"][wname] = rec

        # ---- hour-of-day shapes (P6 / P8) ---------------------------------
        for name, mv, av in (
            ("hydro", m["hydro"], a["hydro"]),
            ("import", m["import"], a["net_import"]),
            ("other_vs_NG_OTH", m["other"], a["other"]),
            ("coal", m["coal"], a["coal"]),
            ("gas_all_incl_chp", m["gas_all"], a["gas"]),
        ):
            mp, ap = hod_profile(mv, jja, hod), hod_profile(av, jja, hod)
            yr["hod_profiles_JJA"][name] = {
                "model": mp,
                "actual": ap,
                "r": pearson(mp, ap),
                "model_cv": round(cv(np.asarray(mp)), 4),
                "actual_cv": round(cv(np.asarray(ap)), 4),
                "cv_ratio_model_over_actual": round(
                    cv(np.asarray(mp)) / cv(np.asarray(ap)), 4
                )
                if cv(np.asarray(ap))
                else None,
            }
        yr["hod_profiles_JJA"]["eia930_residual_control"] = {
            "actual": hod_profile(resid, jja, hod)
        }
        out["years"][str(year)] = yr

    OUT.write_text(json.dumps(out, indent=1))

    # ---- console ---------------------------------------------------------
    print("=" * 78)
    print("miso-142 G-C -- model vs EIA-930 supply, MISO")
    print("=" * 78)
    for year in YEARS:
        y = out["years"][str(year)]
        g0 = y["G_C0_direction"]
        print(
            f"\n{year}  G-C0 direction: actual net import (JJA) "
            f"{g0['actual_net_import_mean_mw']:+.0f} MW -> "
            f"{'PASS' if g0['pass'] else 'FAIL -- STOP'}"
            f"   | EIA-930 residual floor: median |.| year "
            f"{y['eia930_adjustment_residual_mw']['median_abs_year']:.0f} MW, "
            f"W1 {y['eia930_adjustment_residual_mw']['median_abs_W1']:.0f} MW"
        )
        w = y["windows"]["W1_jun_jul_h8_20"]
        print(f"  W1 (Jun+Jul h8-20, {w['n_hours']} h) model vs EIA-930, mean MW:")
        for k in (
            "coal",
            "gas_merchant_only",
            "gas_all_incl_chp",
            "hydro",
            "other_vs_NG_OTH",
            "import",
            "wind",
            "solar",
            "nuclear",
        ):
            r = w[k]
            print(
                f"    {k:24s} model {r['model_mw']:9.1f}  actual {r['actual_mw']:9.1f}"
                f"  delta {r['delta_mw']:+9.1f}"
                + (f"  ({r['pct']:+.1f}%)" if r["pct"] is not None else "")
            )
        print(
            f"    {'H1 deltaQ (hydro+other+import)':24s} "
            f"{w['H1_deltaQ_hydro_other_import_mw']:+9.1f} MW"
            f"   = {w['H1_deltaQ_vs_residual_floor']:+.2f}x the EIA-930 residual floor"
        )
        print("  JJA hour-of-day shape:")
        for k, r in y["hod_profiles_JJA"].items():
            if k == "eia930_residual_control":
                continue
            print(
                f"    {k:24s} r {r['r']:+.3f}   CV model {r['model_cv']:.3f} / "
                f"actual {r['actual_cv']:.3f}  ratio {r['cv_ratio_model_over_actual']}"
            )
        at = y["annual_twh"]
        print("  annual TWh (model / actual / delta%):")
        for k in ("hydro", "other_vs_NG_OTH", "import", "coal", "gas_all_incl_chp"):
            r = at[k]
            print(
                f"    {k:30s} {r['model']:8.2f} / {r['actual']:8.2f}  "
                f"({r['pct']:+.1f}%)" if r["pct"] is not None else f"    {k}"
            )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
