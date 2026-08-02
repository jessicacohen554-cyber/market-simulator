"""caiso-156 pre-registration measurement: size the hour-grain physical-band
screen on the shared CT heat-rate derive, BOTH sides, all committed ISOs.

Context. caiso-146 §2.4 measured (read-only, low side only) that loaded meter
hours with an hourly implied heat rate BELOW the derive's own declared physical
floor (6.0 MMBtu/MWh) bias ``derive_campd_ct_heat_rates.py`` LOW in every ISO
measured — CAISO 3.46 % of loaded hours / +0.114, NYISO 2.45 % / +0.122, PJM
1.55 % / +0.081, MISO 0.30 % / +0.014 energy-weighted — and filed the
hour-grain screen as a cross-cutting item because it moves committed keepers'
inputs (probe ``_caiso146_hourly_hr_integrity.py``). caiso-156 is that item's
charter session.

This probe extends the caiso-146 measurement for the pre-registration:

1. BOTH sides of the band: hours below ``_HR_MIN`` (6.0) AND above ``_HR_MAX``
   (25.0) — the screen under pre-registration is the derive's own declared
   physical band applied per loaded hour, not a new low-side-only rule.
2. All six committed artifacts (adds NEISO — armed in its keeper at neiso-70,
   AFTER the caiso-146 measurement — and ERCOT, whose artifact is
   evidence-only, inert by wiring per ERCOT-146).
3. The valid-hours consequence: under the screen a unit's loaded rate rests on
   its IN-BAND loaded hours, so the existing ``_MIN_LOADED_HOURS`` (50) trust
   gate is evaluated on in-band hours; units falling below it drop, and a
   plant losing all units falls back to eGRID. Both consequences are counted
   here before the rule is frozen.
4. A faithfulness check: the probe's "as-is" reconstruction must reproduce the
   committed per-plant ``heat_rate_gross`` values (tolerance 1e-3), proving
   the screened preview column is computed by the same recipe the derive uses.

Read-only: changes nothing, derives nothing, solves nothing. Its numbers are
frozen into ``PREREG-caiso156-ct-heat-rate-meter-screen-2026-08-02.md`` BEFORE
the derive is edited (caiso-139..155 house rule).

Usage::

    PYTHONPATH=.:src .venv/bin/python \
        scripts/probes/_caiso156_hourly_band_screen.py \
        --iso CAISO NYISO PJM MISO NEISO ERCOT
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

YEARS = (2023, 2024, 2025)
TARGET_CLASS = "CT_PEAKER"
CT_UNIT_TYPE = "combustion turbine"
UNIT_DIR = RAW_DIR / "campd-unit-level"

#: Mirrors of the derive's own declared constants
#: (scripts/data/derive_campd_ct_heat_rates.py) — the probe adds NO parameter.
HR_MIN, HR_MAX = 6.0, 25.0
_LOADED_FRAC, _CAP_PCTILE, _MIN_LOADED_HOURS = 0.80, 95.0, 50


def class_codes(iso: str) -> set[int]:
    """Plant codes carrying any CT_PEAKER generator in the ISO's model fleet."""
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    return {
        int(g.plant_code)
        for g in fleet
        if g.plant_group == TARGET_CLASS and int(g.plant_code or 0)
    }


def unit_frame(iso: str) -> pd.DataFrame:
    """One row per (unit) with as-is and band-screened loaded rates."""
    codes = class_codes(iso)
    frames = []
    for state in campd.states_for_iso(iso):
        for year in YEARS:
            path = UNIT_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "unitType",
                    "grossLoad",
                    "heatInput",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            df = df[
                df["unitType"].astype(str).str.strip().str.casefold() == CT_UNIT_TYPE
            ]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame()
    p = pd.concat(frames, ignore_index=True).dropna(subset=["grossLoad", "heatInput"])
    p = p[(p["grossLoad"] > 0.0) & (p["heatInput"] > 0.0)]

    rows = []
    for (code, unit), g in p.groupby(["facilityId", "unitId"], sort=True):
        cap = float(np.percentile(g["grossLoad"], _CAP_PCTILE))
        ld = g[g["grossLoad"] >= _LOADED_FRAC * cap]
        if len(ld) < _MIN_LOADED_HOURS:
            continue  # unit already outside the derive today; screen can't add it
        hr_h = (ld["heatInput"] / ld["grossLoad"]).to_numpy(float)
        low = hr_h < HR_MIN
        high = hr_h > HR_MAX
        keep = ld[~(low | high)]
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": str(g["facilityName"].iloc[0]),
                "unit_id": str(unit),
                "gross_mwh": float(g["grossLoad"].sum()),
                "loaded_h": int(len(ld)),
                "low_h": int(low.sum()),
                "high_h": int(high.sum()),
                "valid_h": int(len(keep)),
                "hr_as_is": float(ld["heatInput"].sum() / ld["grossLoad"].sum()),
                "hr_screened": (
                    float(keep["heatInput"].sum() / keep["grossLoad"].sum())
                    if len(keep)
                    else float("nan")
                ),
                "drops_under_screen": bool(len(keep) < _MIN_LOADED_HOURS),
            }
        )
    d = pd.DataFrame(rows)
    if not d.empty:
        d["delta"] = d["hr_screened"] - d["hr_as_is"]
        d["iso"] = iso
    return d


def plant_preview(units: pd.DataFrame, iso: str) -> pd.DataFrame:
    """Preview the fixed derive's plant table against the committed artifact.

    Joins the committed plant CSV (as-is truth: parasitic_factor, applied flag,
    class capacity, eGRID model rate) and recomputes the generation-weighted
    plant rate twice — from the probe's as-is unit rates (faithfulness check)
    and from the screened unit rates (the preview). Units dropping below the
    valid-hours trust gate leave the screened aggregate exactly as they will
    leave the fixed derive.
    """
    art = pd.read_csv(PROCESSED_DIR / f"campd_ct_heat_rates_{iso}.csv")
    rows = []
    for code, g in units.groupby("plant_code", sort=True):
        w = g["gross_mwh"].to_numpy(float)
        asis = float(np.average(g["hr_as_is"], weights=w))
        kept = g[~g["drops_under_screen"]]
        scr = (
            float(np.average(kept["hr_screened"], weights=kept["gross_mwh"]))
            if len(kept)
            else float("nan")
        )
        rows.append(
            {
                "plant_code": int(code),
                "hr_gross_asis_probe": asis,
                "hr_gross_screened": scr,
                "n_units": int(len(g)),
                "n_units_dropped": int(g["drops_under_screen"].sum()),
            }
        )
    prev = pd.DataFrame(rows).merge(art, on="plant_code", how="right")
    prev["repro_err"] = (prev["hr_gross_asis_probe"] - prev["heat_rate_gross"]).abs()
    # The committed net conversion divides the gross rate by the plant's own
    # parasitic factor; the screened net rate uses the identical factor.
    prev["heat_rate_screened_net"] = (
        prev["hr_gross_screened"] / prev["parasitic_factor"]
    )
    prev["delta_net"] = prev["heat_rate_screened_net"] - prev["heat_rate"]
    return prev


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--iso", nargs="+", default=["CAISO", "NYISO", "PJM", "MISO", "NEISO", "ERCOT"]
    )
    args = ap.parse_args()

    for iso in args.iso:
        d = unit_frame(iso)
        print("=" * 78)
        if d.empty:
            print(f"{iso}: no qualifying CT units")
            continue
        loaded = int(d["loaded_h"].sum())
        print(
            f"{iso} — {len(d)} qualifying CT units, "
            f"{loaded:,} pooled loaded hours"
        )
        print(
            f"  hours below {HR_MIN}: {int(d['low_h'].sum()):,} "
            f"({100 * d['low_h'].sum() / loaded:.2f} %)   "
            f"hours above {HR_MAX}: {int(d['high_h'].sum()):,} "
            f"({100 * d['high_h'].sum() / loaded:.3f} %)"
        )
        print(
            f"  units with any out-of-band loaded hour: "
            f"{int(((d['low_h'] > 0) | (d['high_h'] > 0)).sum())} / {len(d)}; "
            f"units dropping below {_MIN_LOADED_HOURS} valid hours: "
            f"{int(d['drops_under_screen'].sum())}"
        )
        kept = d[~d["drops_under_screen"]]
        print(
            "  energy-wt unit HR  as-is "
            f"{np.average(d['hr_as_is'], weights=d['gross_mwh']):.4f}"
            "  screened "
            f"{np.average(kept['hr_screened'], weights=kept['gross_mwh']):.4f}"
        )
        moved = d[d["delta"].abs() > 0.25].sort_values("delta", ascending=False)
        if len(moved):
            print(f"  units moving > 0.25 MMBtu/MWh: {len(moved)}")
            print(
                moved[
                    [
                        "plant_code",
                        "plant_name",
                        "unit_id",
                        "loaded_h",
                        "low_h",
                        "high_h",
                        "valid_h",
                        "hr_as_is",
                        "hr_screened",
                        "delta",
                    ]
                ].to_string(index=False)
            )

        prev = plant_preview(d, iso)
        ok = prev[prev["flag"] == "ok"]
        max_repro = float(ok["repro_err"].max())
        print(
            f"  faithfulness: max |probe as-is − committed hr_gross| over "
            f"{len(ok)} applied rows = {max_repro:.5f}"
            + ("  ** RECIPE MISMATCH **" if max_repro > 1e-3 else "  (reproduces)")
        )
        w_cap = ok["class_capacity_mw"].to_numpy(float)
        w_gen = ok["gross_mwh"].to_numpy(float)
        fin = np.isfinite(ok["heat_rate_screened_net"].to_numpy(float))
        print(
            "  APPLIED plant map (flag==ok, net basis): "
            f"cap-wt {np.average(ok['heat_rate'], weights=w_cap):.4f} -> "
            f"{np.average(ok['heat_rate_screened_net'][fin], weights=w_cap[fin]):.4f}, "
            f"gen-wt {np.average(ok['heat_rate'], weights=w_gen):.4f} -> "
            f"{np.average(ok['heat_rate_screened_net'][fin], weights=w_gen[fin]):.4f}"
        )
        big = prev[prev["delta_net"].abs() > 0.10].sort_values(
            "delta_net", ascending=False
        )
        if len(big):
            print("  plants whose APPLIED net rate moves > 0.10 MMBtu/MWh:")
            print(
                big[
                    [
                        "plant_code",
                        "plant_name",
                        "class_capacity_mw",
                        "heat_rate",
                        "heat_rate_screened_net",
                        "delta_net",
                        "n_units_dropped",
                        "flag",
                    ]
                ].to_string(index=False)
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
