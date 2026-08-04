#!/usr/bin/env python3
"""nyiso-120 — which meter is wrong about East River's boundary? (no LP)

Scores **only** the no-LP kill rules pre-registered in
``results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md`` §4
(KE1, KE2, KE3), on **NYISO's own data** (rule 25 ``[R-ISO-SCOPE]`` — miso-122's
verdict fills no NYISO cell).

THE QUESTION, as miso-122 §7 handed it over
===========================================
The hybrid-cogen scope gate measures 37.5 % of ORIS 2493 East River's metered
2023 fuel burning in units with **zero gross load all year**. Removing that
share takes the plant's power-only heat rate to 7.3763, which is **below**
eGRID's own credited ``PLHTRT`` of 7.4205 — so the gate flags it
``below_credited`` and excludes it, and the plant reverts from the applied
all-fuel rate 11.8032 to 7.4205. miso-122 could not say **why** the two sources
disagree, because that is not answerable from MISO's data.

THREE READINGS, DISCRIMINATED BY MEASUREMENT (prereg §2)
--------------------------------------------------------
* **H (double-count)** — eGRID's ``CHPCHTI`` at East River *is* the direct-fired
  boiler fuel, not a topping-cycle useful-thermal credit. Then ``PLHTIAN`` is
  already the power train's fuel, ``PLHTRT`` is already the power-only rate, and
  the ``measured_chp_heat_rates`` add-back double-counts boiler fuel into a
  power tranche. Sharp predictions: dark MMBtu ≈ ``CHPCHTI`` (KE1) **and**
  power-train MMBtu ÷ ``PLNGENAN`` ≈ ``PLHTRT`` (KE2).
* **R1 (genuine ambiguity)** — both a real steam credit *and* separate dark
  fuel; the true rate lies between 7.4205 and 11.8032 and the exclusion is a
  fallback, not a correction.
* **R2 (selection artifact)** — the behavioural dark-set selection picked up a
  generating unit with no gross-load channel (KE3).

WHAT THIS PROBE DELIBERATELY DOES NOT DO
----------------------------------------
It does not re-implement the derive's dark-set selection: it calls
:func:`derive_chp_power_only_heat_rates.cems_annual_heat` directly, so the
number scored is the number the artifact is built from. It reads ``unitType``
**only to check** the behavioural selection (KE3) and never to make it — a
``unitType`` allowlist would be the off-registry hand map rule 24
``[R-REGISTRY]`` forbids. Both agreement bands are miso-118's committed
``[0.90, 1.10]``, reused rather than reinvented (prereg §3.3).

    python scripts/probes/_nyiso120_eastriver_boundary.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import derive_chp_power_only_heat_rates as drv  # noqa: E402

ISO = "NYISO"
PLANT = 2493
#: The artifact's own eGRID vintage — KE1/KE2 are scored here and nowhere else,
#: because CHPCHTI/PLNGENAN are published for this year only (prereg §3.2).
VINTAGE = 2023
YEARS = (2023, 2024, 2025)

#: miso-118's committed two-meter agreement band, reused (prereg §3.3).
BAND = drv._CEMS_RECONCILE_BAND
#: KE3 bars, taken from miso-122's own K1/K2 and re-scored on NYISO's data.
KE3_BOILER_SHARE = 0.90
KE3_PERSISTENCE_MAXMIN = 2.0

ARTIFACT = drv.RAW_DIR / "_processed-legacy" / f"chp_power_only_heat_rates_{ISO}.csv"
OUT_PATH = REPO / "results/calibration/_nyiso120_eastriver_boundary.json"


def unit_detail(year: int) -> pd.DataFrame:
    """Return per-unit annual fuel/gross-load/`unitType` at the plant.

    ``unitType`` is carried for the KE3 **check** only. The dark flag here
    reproduces the derive's behavioural rule (fuel > 0, gross load ≤ 0 over the
    whole year) so the per-unit table and the scored share come from the same
    definition; the scored share itself is taken from
    :func:`drv.cems_annual_heat`, never from this table.
    """
    frames = []
    for state in drv.campd.states_for_iso(ISO):
        path = drv.UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "unitType", "heatInput", "grossLoad"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        frames.append(df[df["facilityId"] == PLANT])
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = df.assign(
        heatInput=df["heatInput"].fillna(0.0), grossLoad=df["grossLoad"].fillna(0.0)
    )
    agg = (
        df.groupby(["unitId", "unitType"], dropna=False)[["heatInput", "grossLoad"]]
        .sum()
        .reset_index()
    )
    agg["dark"] = (agg["grossLoad"] <= 0.0) & (agg["heatInput"] > 0.0)
    return agg.sort_values("heatInput", ascending=False)


def main() -> int:
    """Score KE1-KE3 and write the machine record."""
    art = pd.read_csv(ARTIFACT)
    row = art[(art["plant_code"] == PLANT) & (art["plant_group"] == "CT_CHP")].iloc[0]
    chpchti = float(row["heat_input_thermal_mmbtu"])
    plhtian = float(row["heat_input_electric_mmbtu"])
    plngenan = float(row["net_mwh"])
    credited = float(row["heat_rate_credited"])
    applied_now = float(row["heat_rate"])

    per_year: dict[str, dict] = {}
    units_by_year: dict[str, list[dict]] = {}
    for year in YEARS:
        totals, dark = drv.cems_annual_heat(ISO, year, {PLANT})
        total = totals.get(PLANT, 0.0)
        dark_mmbtu = dark.get(PLANT, 0.0)
        detail = unit_detail(year)
        dark_fuel = float(detail.loc[detail["dark"], "heatInput"].sum())
        boiler_dark = float(
            detail.loc[
                detail["dark"] & detail["unitType"].str.contains("boiler", case=False, na=False),
                "heatInput",
            ].sum()
        )
        per_year[str(year)] = {
            "cems_total_mmbtu": round(total, 1),
            "cems_dark_mmbtu": round(dark_mmbtu, 1),
            "dark_share": round(dark_mmbtu / total, 6) if total else None,
            "power_train_mmbtu": round(total - dark_mmbtu, 1),
            "boiler_share_of_dark": round(boiler_dark / dark_fuel, 6) if dark_fuel else None,
            "n_units": int(len(detail)),
            "n_dark_units": int(detail["dark"].sum()),
        }
        units_by_year[str(year)] = [
            {
                "unitId": str(u.unitId),
                "unitType": str(u.unitType),
                "heat_mmbtu": round(float(u.heatInput), 1),
                "gross_mwh": round(float(u.grossLoad), 1),
                "dark": bool(u.dark),
            }
            for u in detail.itertuples(index=False)
        ]

    v = per_year[str(VINTAGE)]

    # ---- KE1: is eGRID's CHP credit the same object as the dark boiler fuel?
    ke1_ratio = v["cems_dark_mmbtu"] / chpchti
    ke1_pass = BAND[0] <= ke1_ratio <= BAND[1]

    # ---- KE2: basis-matched two-meter power-only comparator.
    #      CAMPD fuel (power train only) over eGRID net MWh, against eGRID's own
    #      credited rate. Both meters independent; the ratio is the test.
    ke2_hr = v["power_train_mmbtu"] / plngenan
    ke2_ratio = ke2_hr / credited
    ke2_pass = BAND[0] <= ke2_ratio <= BAND[1]

    # ---- KE3: the dark set is boilers, and it is machinery not a spike.
    shares = [per_year[str(y)]["dark_share"] for y in YEARS]
    boiler = [per_year[str(y)]["boiler_share_of_dark"] for y in YEARS]
    maxmin = max(shares) / min(shares) if all(shares) else None
    ke3_pass = (
        all(s is not None and s > 0.0 for s in shares)
        and all(b is not None and b >= KE3_BOILER_SHARE for b in boiler)
        and maxmin is not None
        and maxmin <= KE3_PERSISTENCE_MAXMIN
    )

    verdict = {
        "session": "nyiso-120",
        "iso": ISO,
        "plant_code": PLANT,
        "plant_name": str(row["plant_name"]),
        "class": "CT_CHP",
        "class_capacity_mw": float(row["class_capacity_mw"]),
        "egrid_vintage": VINTAGE,
        "egrid": {
            "PLHTIAN_mmbtu": plhtian,
            "CHPCHTI_mmbtu": chpchti,
            "PLNGENAN_mwh": plngenan,
            "thermal_share": float(row["thermal_share"]),
            "heat_rate_credited": credited,
            "heat_rate_applied_on_keeper": applied_now,
        },
        "per_year": per_year,
        "units": units_by_year,
        "KE1_credit_is_dark_fuel": {
            "dark_mmbtu_over_CHPCHTI": round(ke1_ratio, 6),
            "band": list(BAND),
            "pass": bool(ke1_pass),
        },
        "KE2_two_meter_power_only": {
            "campd_power_train_over_PLNGENAN": round(ke2_hr, 4),
            "egrid_credited": credited,
            "ratio": round(ke2_ratio, 6),
            "band": list(BAND),
            "pass": bool(ke2_pass),
        },
        "KE3_dark_set_is_boilers_and_persistent": {
            "dark_share_by_year": shares,
            "boiler_share_of_dark_by_year": boiler,
            "max_over_min": round(maxmin, 4) if maxmin else None,
            "pass": bool(ke3_pass),
        },
        "hypothesis": (
            "H (double-count)"
            if (ke1_pass and ke2_pass and ke3_pass)
            else "NOT H — see per-kill detail"
        ),
    }
    OUT_PATH.write_text(json.dumps(verdict, indent=2) + "\n")

    print(f"=== nyiso-120 — ORIS {PLANT} {row['plant_name']} ({ISO}) ===")
    print(
        f"eGRID {VINTAGE}: PLHTIAN {plhtian:,.0f}  CHPCHTI {chpchti:,.0f}  "
        f"PLNGENAN {plngenan:,.0f} MWh"
    )
    print(f"  credited PLHTRT {credited:.4f}   applied on keeper {applied_now:.4f}")
    for year in YEARS:
        p = per_year[str(year)]
        print(
            f"  {year}: CEMS {p['cems_total_mmbtu']:,.0f} MMBtu, dark "
            f"{p['cems_dark_mmbtu']:,.0f} ({p['dark_share']:.2%}) in "
            f"{p['n_dark_units']}/{p['n_units']} units, boiler share of dark "
            f"{p['boiler_share_of_dark']:.1%}"
        )
    print(f"\nKE1 dark ÷ CHPCHTI      = {ke1_ratio:.4f}  {'PASS' if ke1_pass else 'FIRE'}")
    print(
        f"KE2 power-train HR      = {ke2_hr:.4f} vs credited {credited:.4f} "
        f"(ratio {ke2_ratio:.4f})  {'PASS' if ke2_pass else 'FIRE'}"
    )
    print(f"KE3 boilers+persistent  = {'PASS' if ke3_pass else 'FIRE'}")
    print(f"\n=> {verdict['hypothesis']}")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
