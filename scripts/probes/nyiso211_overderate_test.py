"""nyiso-211 POST-HOC (NOT pre-registered) — is the repaired CC availability
deeper than the meter?

Zero-LP. The instrument is the same on-recipe ``fleet_only`` rebuild
``scripts/probes/nyiso196_rebuild_checks.py`` uses (its cached arrays are reused
verbatim), so the availability read here is exactly the availability the LP was
given, under both bases of ``unit_outage_extract_basis_share``:

* ``keeper`` — the pre-nyiso-196 basis (flag OFF).
* ``arm``    — the basis every keeper has carried since nyiso-196 (flag ON).

For each CC_REGULAR plant the probe forms the plant's **available energy** —
``sum_h sum_tranches pmax x availability[h]`` — and compares it against the
committed bench's measured CAMPD energy for the same plant, month and year.

A ratio ``measured / available > 1`` is a **proof of over-derate**: the meter
recorded more energy than the LP was physically able to produce, so the derate
is deeper than the plant's own operating record, whatever it does to any
residual.

**This test is POST-HOC.** It is not among the predictions declared in
``results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md``
and no pre-registered verdict is decided by it; it is reported as
characterization of the mechanism P1/P2/P3 attribute, at full magnitude in both
directions.

Run (after ``nyiso196_rebuild_checks.py --year {2023,2024,2025}`` has populated
the rebuild cache)::

    uv run python scripts/probes/nyiso211_overderate_test.py
"""

from __future__ import annotations

import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

YEARS = (2023, 2024, 2025)
KLASS = "CC_REGULAR"
T = 8760
# Rule 8 [R-8760]: a flat non-leap 8,760-hour calendar in every year.
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24

CACHE = ROOT / ".cache/nyiso196"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
TARGET = 57185  # Cricket Valley Energy


def available_energy_gwh(year: int, basis: str) -> dict[int, dict]:
    """Per-plant available energy (GWh) by month and year, for the CC_REGULAR class."""
    st = pickle.load(open(CACHE / f"rebuild_{year}_{basis}.pkl", "rb"))
    units, avail = st["units"], st["avail"]
    out: dict[int, dict] = {}
    for plant, grp in units[units.group == KLASS].groupby("plant"):
        idx = grp.i.to_numpy()
        pmax = grp.pmax.to_numpy()[:, None]
        energy_h = (avail[idx][:, :T] * pmax).sum(axis=0)  # MW per hour, plant total
        months = [
            float(energy_h[MONTH_STARTS[m] : MONTH_STARTS[m + 1]].sum()) / 1e3
            for m in range(12)
        ]
        out[int(plant)] = {
            "pmax_mw": round(float(grp.pmax.sum()), 1),
            "tranches": int(len(grp)),
            "mean_avail": round(
                float((avail[idx][:, :T] * pmax).sum() / (pmax.sum() * T)), 4
            ),
            "available_gwh_by_month": [round(v, 2) for v in months],
            "available_gwh": round(sum(months), 2),
        }
    return out


def measured_gwh(year: int) -> dict[int, dict]:
    """Measured CAMPD plant energy (GWh) by month, from the committed bench."""
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
    # The bench keys a plant that splits across groups as ``<code>:<group>``;
    # the rebuild keys by plain plant code. Folded onto the plain code.
    return {
        int(str(code).split(":", 1)[0]): {
            "name": bp.get("name"),
            "zone": bp.get("zone"),
            "npl_mw": bp.get("npl"),
            "campd_gwh_by_month": [round(float(v), 2) for v in (bp.get("c_mon") or [0.0] * 12)],
            "campd_gwh": round(float(bp.get("c_ann") or 0.0) * 1e3, 2),
        }
        for code, bp in bench.items()
        if bp.get("group") == KLASS
    }


def main() -> None:
    rows: dict[str, dict] = {}
    for year in YEARS:
        meas = measured_gwh(year)
        per_basis = {b: available_energy_gwh(year, b) for b in ("keeper", "arm")}
        year_rows = {}
        for plant, m in meas.items():
            entry = {
                "name": m["name"],
                "zone": m["zone"],
                "npl_mw": m["npl_mw"],
                "campd_gwh": m["campd_gwh"],
            }
            for basis, table in per_basis.items():
                a = table.get(plant)
                if a is None:
                    entry[basis] = None
                    continue
                ratio_m = [
                    (round(m["campd_gwh_by_month"][i] / a["available_gwh_by_month"][i], 4)
                     if a["available_gwh_by_month"][i] > 0 else None)
                    for i in range(12)
                ]
                over = [i + 1 for i, r in enumerate(ratio_m) if r is not None and r > 1.0]
                entry[basis] = {
                    "pmax_mw": a["pmax_mw"],
                    "mean_avail": a["mean_avail"],
                    "available_gwh": a["available_gwh"],
                    "measured_over_available": round(
                        m["campd_gwh"] / a["available_gwh"], 4
                    )
                    if a["available_gwh"] > 0
                    else None,
                    "monthly_ratio": ratio_m,
                    "months_over_1": over,
                    "OVER_DERATED": bool(
                        over or (a["available_gwh"] > 0 and m["campd_gwh"] > a["available_gwh"])
                    ),
                }
            year_rows[str(plant)] = entry
        rows[str(year)] = year_rows

    # ---- class-wide census: who is over-derated on the CURRENT (arm) basis ----
    census = {}
    for year in YEARS:
        yr = rows[str(year)]
        flagged = [
            {
                "plant": p,
                "name": e["name"],
                "zone": e["zone"],
                "mean_avail": e["arm"]["mean_avail"],
                "measured_over_available": e["arm"]["measured_over_available"],
                "months_over_1": e["arm"]["months_over_1"],
            }
            for p, e in yr.items()
            if e.get("arm") and e["arm"]["OVER_DERATED"]
        ]
        ranked = sorted(
            (
                {"plant": p, "name": e["name"], "mean_avail": e["arm"]["mean_avail"]}
                for p, e in yr.items()
                if e.get("arm")
            ),
            key=lambda r: r["mean_avail"],
        )
        census[str(year)] = {
            "n_plants": len(ranked),
            "over_derated_on_arm_basis": flagged,
            "availability_ranked_ascending": ranked,
        }

    # ---- which plants GAIN an over-ceiling month from the repair? ----------
    # The one-sidedness test: pre-196 (keeper basis, flag OFF) vs the current
    # keeper (arm basis, flag ON), per plant per year.
    repair_month_delta = {}
    for year in YEARS:
        yr = rows[str(year)]
        gained, lost = [], []
        for plant, e in yr.items():
            if not (e.get("keeper") and e.get("arm")):
                continue
            before = set(e["keeper"]["months_over_1"])
            after = set(e["arm"]["months_over_1"])
            if after - before:
                gained.append(
                    {
                        "plant": plant,
                        "name": e["name"],
                        "before": sorted(before),
                        "after": sorted(after),
                    }
                )
            if before - after:
                lost.append(
                    {
                        "plant": plant,
                        "name": e["name"],
                        "n_before": len(before),
                        "n_after": len(after),
                    }
                )
        repair_month_delta[str(year)] = {"gained": gained, "lost": lost}

    target = {
        str(y): {
            "keeper_basis": rows[str(y)][str(TARGET)]["keeper"],
            "arm_basis": rows[str(y)][str(TARGET)]["arm"],
            "campd_gwh": rows[str(y)][str(TARGET)]["campd_gwh"],
        }
        for y in YEARS
    }

    out = {
        "session": "nyiso-211",
        "status": "POST-HOC — not pre-registered; decides no declared verdict",
        "instrument": "on-recipe fleet_only rebuild (scripts/probes/nyiso196_rebuild_checks.py cache)",
        "basis": "CAMPD (bench c_mon/c_ann) measured side; model available energy = sum_h sum_tranches pmax x availability",
        "target_plant": TARGET,
        "target": target,
        "class_census": census,
        "repair_month_delta": repair_month_delta,
        "plants": rows,
    }
    dest = ROOT / "results/calibration/_nyiso211_overderate_test.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(target, indent=1))
    print(json.dumps(repair_month_delta, indent=1))
    print(json.dumps(census, indent=1)[:2000])
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
