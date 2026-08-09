"""caiso-188 — forensics on the CAISO aggregate seam cap: which value actually bound?

NO LP, NO SOLVER, NO NETWORK. Committed bytes only: every CAISO bundle's
``hourly/class_hourly_<year>.parquet``, the EIA-930 CISO interchange frame, the
published branch-group MIC registry, and the committed topology code.

The object. The DOF ledger row ``WECC_import_simultaneous.cap_mw`` carries value
**7,500 MW**, identification *residual*, and the source text *"fitted aggregate
WECC import cap — SUPERSEDED in the caiso-51 keeper by the published
branch-group MIC seam limit"*; ``_caiso186os_dof_repair`` re-verified it at HEAD
and returned ``on_backcast_binding_path: false`` — *"the ledger text already says
this and it CHECKS OUT"*. ``FINDING-caiso133`` §3/§4 independently proved the
seam row unreachable (Σ corridor envelope caps 9,631/9,557/10,777 MW < the MIC
16,055/16,452/16,148 MW) and measured its solved dual as exactly 0.000 in all
26,280 hours.

Every one of those statements is conditional on the MIC replacement having
actually happened in the solve. This probe tests that conditional against the
committed dispatch, four ways:

* **F1 PIN CENSUS** — per bundle, per year: the maximum of the ``import`` class
  and the count of hours sitting at exactly 7,500.0 MW. A hard pin at a value
  that appears nowhere in the CAISO import path except
  ``WECC_import_simultaneous`` is the signature of that row binding.
* **F2 ONSET** — the same statistic ordered over the CAISO bundle lineage, so
  the regime change is dated from artifacts rather than inferred.
* **F3 REACHABILITY, recomputed against the value that actually bound** — the
  caiso-133 §3 test is exact given its assumed cap; re-run it against 7,500 and
  against the MIC, and count the hours the two corridors' measured p95 envelopes
  would jointly exceed each.
* **F4 RULE-14 FALSIFICATION** — the measured EIA-930 total CISO net import
  against both candidate caps. A cap the real system routinely exceeds is not a
  physical bound (the ``retire_misattributed_sil`` / nyiso-100 pattern).

No scored criterion is read and no residual is consulted (rule 1 ``[R-STRUCT]``,
rule 13 ``[R-MEASURED]``).

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso188_seam_cap_forensics.py

Writes ``results/calibration/_caiso188_seam_cap_forensics.json``.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CAL = REPO / "results" / "calibration"
OUT = CAL / "_caiso188_seam_cap_forensics.json"
HOURS = 8760
YEARS = (2023, 2024, 2025)

#: The baked CAISO aggregate cap (``iso_configs._caiso_config``), which that
#: module's own comment labels "a fitted scalar".
FITTED_SEAM_MW = 7500.0

#: The published branch-group Maximum Import Capability sum per delivery year
#: (``data/raw/capacity-deliverability/caiso/caiso.csv``), i.e. the value
#: ``capacity_deliverability_limits`` Part A is supposed to install.
MIC_SEAM_MW = {2023: 16055.0, 2024: 16452.0, 2025: 16148.0}


def _import_series(path: Path) -> np.ndarray | None:
    """Return the hourly ``import``-class MW series of a bundle sidecar."""
    try:
        df = pd.read_parquet(path)
    except Exception:
        return None
    sub = df[df["klass"] == "import"]
    if sub.empty:
        return None
    return sub.sort_values("hour")["mw"].to_numpy(dtype=float)


def f1_f2_pin_census() -> dict:
    """Per bundle-year: import max and the count of hours pinned at 7,500 MW."""
    out: dict[str, dict] = {}
    for path in sorted(CAL.glob("caiso*/hourly/class_hourly_*.parquet")):
        imp = _import_series(path)
        if imp is None:
            continue
        bundle = path.parent.parent.name
        year = int(path.stem.split("_")[-1])
        pinned = int(np.isclose(imp, FITTED_SEAM_MW, atol=1e-3).sum())
        out.setdefault(bundle, {})[str(year)] = {
            "import_max_mw": round(float(imp.max()), 1),
            "hours_pinned_at_fitted_cap": pinned,
            "pinned_pct": round(100.0 * pinned / imp.size, 2),
            "regime": (
                "FITTED 7,500 IN FORCE"
                if float(imp.max()) <= FITTED_SEAM_MW + 1e-3 and pinned > 0
                else "cap above 7,500 (MIC in force or unreached)"
            ),
        }
    return out


def _measured_total_net_import(year: int) -> np.ndarray:
    """Measured hourly total CISO net import (MW) on the model clock."""
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.config.paths import RAW_DATA_DIR
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock

    frame = pd.read_parquet(
        RAW_DATA_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    )
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    frame = frame.assign(_t=local)
    frame["_corridor"] = frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    frame = frame.dropna(subset=["_corridor"])
    sub = frame[frame["_t"].dt.year == year]
    return (-sub.groupby("_t")["mw"].sum()).to_numpy(dtype=float)


def f3_reachability() -> dict:
    """Re-run the caiso-133 §3 reachability test against BOTH candidate caps."""
    from market_sim.data.eia_loader import measured_corridor_flow_envelope

    out: dict[str, dict] = {}
    for year in YEARS:
        env = measured_corridor_flow_envelope("CAISO", year, HOURS, direction="import")
        if not env:
            continue
        total = sum(np.asarray(v, dtype=float) for v in env.values())
        out[str(year)] = {
            "corridor_envelope_sum_max_mw": round(float(total.max()), 1),
            "vs_MIC": {
                "cap_mw": MIC_SEAM_MW[year],
                "hours_envelope_sum_ge_cap": int((total >= MIC_SEAM_MW[year]).sum()),
                "verdict": (
                    "UNREACHABLE — caiso-133 §3 reproduces"
                    if (total >= MIC_SEAM_MW[year]).sum() == 0
                    else "reachable"
                ),
            },
            "vs_fitted": {
                "cap_mw": FITTED_SEAM_MW,
                "hours_envelope_sum_ge_cap": int((total >= FITTED_SEAM_MW).sum()),
                "verdict": (
                    "UNREACHABLE"
                    if (total >= FITTED_SEAM_MW).sum() == 0
                    else "REACHABLE — the caiso-133 §3 conclusion does NOT carry "
                    "over to the value that actually bound"
                ),
            },
        }
    return out


def f4_rule14_falsification() -> dict:
    """The measured total CISO net import against both candidate caps."""
    out: dict[str, dict] = {}
    for year in YEARS:
        tot = _measured_total_net_import(year)
        out[str(year)] = {
            "measured_hours": int(tot.size),
            "measured_mean_mw": round(float(tot.mean()), 0),
            "measured_p95_mw": round(float(np.percentile(tot, 95)), 0),
            "measured_p99_mw": round(float(np.percentile(tot, 99)), 0),
            "measured_max_mw": round(float(tot.max()), 0),
            "hours_above_fitted_cap": int((tot > FITTED_SEAM_MW).sum()),
            "hours_above_MIC": int((tot > MIC_SEAM_MW[year]).sum()),
            "verdict": (
                "the FITTED cap is falsified as a physical bound (the real "
                "system exceeds it); the published MIC envelopes the measured "
                "maximum"
                if (tot > FITTED_SEAM_MW).sum() > 0
                and (tot > MIC_SEAM_MW[year]).sum() == 0
                else "inconclusive"
            ),
        }
    return out


def f5_pin_alignment(keeper_bundle: str = "caiso184_c1_lpbasis") -> dict:
    """In the keeper's pinned hours: was the pin reachable, and what did reality do?"""
    from market_sim.data.eia_loader import measured_corridor_flow_envelope

    out: dict[str, dict] = {}
    for year in YEARS:
        imp = _import_series(
            CAL / keeper_bundle / "hourly" / f"class_hourly_{year}.parquet"
        )
        if imp is None:
            continue
        pinned = np.isclose(imp, FITTED_SEAM_MW, atol=1e-3)
        env = measured_corridor_flow_envelope("CAISO", year, HOURS, direction="import")
        total_env = sum(np.asarray(v, dtype=float) for v in env.values())
        meas = _measured_total_net_import(year)
        n = min(meas.size, HOURS)
        hod = np.arange(HOURS) % 24
        out[str(year)] = {
            "pinned_hours": int(pinned.sum()),
            "pinned_hours_where_envelope_sum_exceeds_cap": int(
                (total_env[pinned] > FITTED_SEAM_MW).sum()
            ),
            "max_import_in_unpinned_hours_mw": round(float(imp[~pinned].max()), 1),
            "pinned_share_by_hod_band": {
                "night_0_5": round(
                    float(100.0 * pinned[np.isin(hod, range(0, 6))].mean()), 1
                ),
                "belly_10_15": round(
                    float(100.0 * pinned[np.isin(hod, range(10, 16))].mean()), 1
                ),
                "evening_17_21": round(
                    float(100.0 * pinned[np.isin(hod, range(17, 22))].mean()), 1
                ),
                "late_22_23": round(
                    float(100.0 * pinned[np.isin(hod, (22, 23))].mean()), 1
                ),
            },
            "measured_net_import_in_pinned_hours_mean_mw": round(
                float(meas[: n][pinned[: n]].mean()), 0
            ),
            "model_minus_measured_in_pinned_hours_mw": round(
                float(imp[: n][pinned[: n]].mean() - meas[: n][pinned[: n]].mean()), 0
            ),
        }
    return out


def main() -> int:
    """Run the forensics and write the record."""
    record = {
        "probe": "_caiso188_seam_cap_forensics",
        "session": "caiso-188 (IMPORT_TRANCHES[CAISO] DOF integrity)",
        "lp_solved": False,
        "network": False,
        "fitted_seam_mw": FITTED_SEAM_MW,
        "published_mic_seam_mw": {str(k): v for k, v in MIC_SEAM_MW.items()},
        "f1_f2_pin_census": f1_f2_pin_census(),
        "f3_reachability": f3_reachability(),
        "f4_rule14_falsification": f4_rule14_falsification(),
        "f5_pin_alignment": f5_pin_alignment(),
    }
    print("=== F1/F2: pin census over the CAISO bundle lineage ===")
    for bundle, years in record["f1_f2_pin_census"].items():
        line = "  ".join(
            f"{y}: max {b['import_max_mw']:>8} pin {b['hours_pinned_at_fitted_cap']:>4}"
            for y, b in sorted(years.items())
        )
        print(f"  {bundle:32s} {line}")
    print("\n=== F3: reachability against each candidate cap ===")
    for year, blob in record["f3_reachability"].items():
        print(
            f"  {year}: Σ env max {blob['corridor_envelope_sum_max_mw']:8.1f} | "
            f"vs MIC {blob['vs_MIC']['cap_mw']:.0f}: "
            f"{blob['vs_MIC']['hours_envelope_sum_ge_cap']:5d} h | "
            f"vs fitted {blob['vs_fitted']['cap_mw']:.0f}: "
            f"{blob['vs_fitted']['hours_envelope_sum_ge_cap']:5d} h"
        )
    print("\n=== F4: rule-14 falsification (measured EIA-930 total net import) ===")
    for year, blob in record["f4_rule14_falsification"].items():
        print(
            f"  {year}: measured max {blob['measured_max_mw']:8.0f} MW | "
            f"h > 7,500: {blob['hours_above_fitted_cap']:4d} | "
            f"h > MIC: {blob['hours_above_MIC']:3d} — {blob['verdict']}"
        )
    print("\n=== F5: the keeper's pinned hours ===")
    for year, blob in record["f5_pin_alignment"].items():
        print(
            f"  {year}: {blob['pinned_hours']:4d} pinned, "
            f"{blob['pinned_hours_where_envelope_sum_exceeds_cap']:4d} of them "
            f"reachable-by-envelope; model−measured "
            f"{blob['model_minus_measured_in_pinned_hours_mw']:+.0f} MW"
        )
    OUT.write_text(json.dumps(record, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
