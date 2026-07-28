"""pjm-135 M1/M2/M3 (no LP): the external star-node import into PJM_Dominion.

Chartered by ``FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md`` §7: the
``PJM_external -> PJM_Dominion`` star-node link carries **+2,266 MW / +19.9
TWh/yr** in the keeper-lineage arm A — larger than Dominion's entire 12.1 TWh
fossil deficit, and governed by the seam/import-envelope family
(``pjm_seam_flow_limit``, ``priced_interchange``,
``PJM_EXTERNAL_FLOW_PERCENTILE``), not by ``PJM_INTERFACE_LINK_MAP``.

Three measurements, every input already committed, no LP solved:

* **M1 border attribution** -- how PJM's measured tie-line file is attributed to
  the model's five border zones (``eia930.envelopes._PJM_TIE_ZONE``), what
  import band that attribution hands each border zone
  (``pjm_zonal_interchange_envelope`` at ``PJM_EXTERNAL_FLOW_PERCENTILE``), and
  how that band compares with the **measured** flow on the very same ties.
* **M2 shape** -- the envelope is a (month x hour-of-day) percentile table: 288
  distinct values tiled over 8760 hours. Measured how much of the measured
  hourly import variation such a table can carry, how often the band sits above
  the measured flow, and what annual energy riding the band delivers against the
  measured annual net.
* **M3 degeneracy guard** -- ``FINDING-pjm134`` §7 measured internal links pinned
  at their bounds with **exactly zero** price difference. Before any flow number
  is believed, the same test is run on the star node: the per-zone LP duals in
  the committed ``pjm134_control_A/hourly/system_<year>.parquet`` sidecars say
  whether ``PJM_external`` is price-separated from each border zone at all.

Nothing is written outside ``results/probes/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
from market_sim.config.interchange_config import (
    IMPORT_NODE_LINKS,
    IMPORT_ZONE,
    INTERFACE_NEIGHBORS,
)
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.envelopes import (
    _PJM_TIE_ZONE,
    _PJM_TIE_ZONE_DEFAULT,
    pjm_zonal_interchange,
    pjm_zonal_interchange_envelope,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760

# The control arm whose flows FINDING-pjm134 §7 decomposed. Its committed
# hourly/ sidecars carry the per-zone energy-balance duals used by M3.
ARM_A_DIR = Path("results/calibration/pjm134_control_A")

# FINDING-pjm134 §7, arm A 2025 flows.parquet (committed table, not re-derived
# here -- flows.parquet is gitignored, so this is the published reference).
FINDING_EXTERNAL_TO_DOM_MW_2025 = 2266.0
FINDING_EXTERNAL_TO_DOM_TWH_2025 = 19.9

PJM_ZONES = [
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
]

INTERCHANGE_DIR = RAW_DATA_DIR / "iso-specific-transmission"

OUT_PATH = Path("results/probes/pjm135_star_node_import.json")


def _measured_tie_frame(year: int) -> pd.DataFrame:
    """Return the per-tie hourly measured flow on the model's 8760 clock.

    Mirrors :func:`pjm_zonal_interchange`'s parse exactly (mixed datetime
    format, Feb-29 dropped, month-start hour offsets) so the tie-level numbers
    below are the *same* rows the envelope is built from. ``actual_flow`` is
    PJM's import-positive convention; ``export`` is its negation, matching the
    export-positive convention of :func:`pjm_zonal_interchange`.
    """
    from market_sim.data.eia930.envelopes import _MONTH_START_HOUR

    path = INTERCHANGE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    df = pd.read_csv(path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"])
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    df = df.assign(
        hoy=hoy,
        zone=df["tie_line"]
        .map(lambda t: _PJM_TIE_ZONE.get(str(t), _PJM_TIE_ZONE_DEFAULT))
        .to_numpy(),
    )
    return df[(df["hoy"] >= 0) & (df["hoy"] < HOURS) & df["actual_flow"].notna()]


def _climatology(series: np.ndarray, year: int, stat: str) -> np.ndarray:
    """Return the (month x hour-of-day) ``stat`` of ``series`` tiled over 8760 h.

    ``stat`` is ``"mean"`` or a numeric percentile string (e.g. ``"p95"``). The
    bucketing is byte-identical to :func:`pjm_zonal_interchange_envelope`'s.
    """
    clock = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    month = clock.month.to_numpy()
    hod = clock.hour.to_numpy()
    table = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            if not sel.any():
                continue
            vals = series[sel]
            table[m - 1, h] = (
                float(np.mean(vals))
                if stat == "mean"
                else float(np.percentile(vals, float(stat[1:])))
            )
    return table[month - 1, hod]


def _r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Return the coefficient of determination of ``predicted`` against ``actual``."""
    ss_res = float(np.sum((actual - predicted) ** 2))
    ss_tot = float(np.sum((actual - np.mean(actual)) ** 2))
    return float("nan") if ss_tot <= 0 else 1.0 - ss_res / ss_tot


def measure_m1_m2(year: int) -> dict:
    """Return the M1 attribution and M2 shape measurements for ``year``."""
    zonal = pjm_zonal_interchange(year, PJM_ZONES)  # export-positive, (n_zones, T)
    env = pjm_zonal_interchange_envelope(
        year, PJM_ZONES, HOURS, PJM_EXTERNAL_FLOW_PERCENTILE
    )
    assert zonal is not None and env is not None
    import_cap, export_cap = env
    ties = _measured_tie_frame(year)

    star_zones = {z for z, _ in IMPORT_NODE_LINKS["PJM"]}
    borders: dict[str, dict] = {}
    for zi, zone in enumerate(PJM_ZONES):
        export = zonal[zi]
        imp = np.clip(-export, 0.0, None)  # measured import at this border
        cap = import_cap[zi]
        exp_cap = export_cap[zi]
        net_import_twh = float(-export.sum()) / 1.0e6
        cap_twh = float(cap.sum()) / 1.0e6
        borders[zone] = {
            "has_star_link": zone in star_zones,
            "star_link_ttc_mw": next(
                (t for z, t in IMPORT_NODE_LINKS["PJM"] if z == zone), None
            ),
            "ties": sorted(t for t, z in _PJM_TIE_ZONE.items() if z == zone),
            # --- measured, on the model's own attribution -------------------
            "measured_net_import_mw_mean": float(-export.mean()),
            "measured_net_import_twh": net_import_twh,
            "measured_import_side_mw_mean": float(imp.mean()),
            "measured_import_side_p50": float(np.percentile(imp, 50)),
            "measured_import_side_p95": float(np.percentile(imp, 95)),
            "measured_hours_importing_pct": float(100.0 * (export < 0).mean()),
            # --- the band the envelope hands the LP -------------------------
            "import_cap_mw_mean": float(cap.mean()),
            "import_cap_mw_min": float(cap.min()),
            "import_cap_mw_max": float(cap.max()),
            "export_cap_mw_mean": float(exp_cap.mean()),
            "import_cap_twh_if_ridden": cap_twh,
            # --- M1's headline ratios ---------------------------------------
            "band_over_measured_import_side": (
                float(cap.mean() / imp.mean()) if imp.mean() > 0 else None
            ),
            "band_twh_minus_measured_net_twh": cap_twh - net_import_twh,
            # --- M2 shape ----------------------------------------------------
            "cap_r2_vs_measured_import": _r2(imp, cap),
            "clim_mean_r2_vs_measured_import": _r2(imp, _climatology(imp, year, "mean")),
            "hours_cap_above_measured_import_pct": float(100.0 * (cap > imp).mean()),
            "cap_cv": (
                float(cap.std() / cap.mean()) if cap.mean() > 0 else None
            ),
            "measured_import_cv": (
                float(imp.std() / imp.mean()) if imp.mean() > 0 else None
            ),
            "cap_distinct_values": int(np.unique(np.round(cap, 6)).size),
        }

    # Per-tie decomposition of the zones that carry a star link, so the
    # attribution can be checked tie by tie against the real interconnections.
    per_tie = {}
    for tie, grp in ties.groupby("tie_line"):
        flow = grp["actual_flow"].to_numpy(dtype=float)  # import-positive
        per_tie[str(tie)] = {
            "attributed_to": _PJM_TIE_ZONE.get(str(tie), _PJM_TIE_ZONE_DEFAULT),
            "mean_import_mw": float(flow.mean()),
            "net_import_twh": float(flow.sum()) / 1.0e6,
            "hours_importing_pct": float(100.0 * (flow > 0).mean()),
            "p95_import_mw": float(np.percentile(np.clip(flow, 0.0, None), 95)),
        }

    return {
        "percentile": PJM_EXTERNAL_FLOW_PERCENTILE,
        "borders": borders,
        "per_tie": per_tie,
        "iso_wide": {
            "measured_net_import_twh": float(-zonal.sum()) / 1.0e6,
            "sum_import_cap_twh_if_ridden": float(import_cap.sum()) / 1.0e6,
            "sum_export_cap_twh_if_ridden": float(export_cap.sum()) / 1.0e6,
        },
    }


def measure_m3(year: int) -> dict:
    """Return the star-node degeneracy guard for ``year`` (arm A duals)."""
    path = ARM_A_DIR / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return {"available": False, "reason": f"missing {path}"}
    frame = pd.read_parquet(path)
    frame = frame[frame["pass"] == "P1"]
    wide = frame.pivot_table(index="hour", columns="zone", values="price")
    ext = IMPORT_ZONE["PJM"]
    if ext not in wide.columns:
        return {"available": False, "reason": f"{ext} absent from sidecar"}
    ext_price = wide[ext].to_numpy(dtype=float)
    out: dict[str, dict] = {}
    for zone in PJM_ZONES:
        if zone not in wide.columns:
            continue
        delta = wide[zone].to_numpy(dtype=float) - ext_price
        out[zone] = {
            "hours_tied_exact_pct": float(100.0 * (np.abs(delta) < 1e-9).mean()),
            "hours_tied_1e_6_pct": float(100.0 * (np.abs(delta) < 1e-6).mean()),
            "hours_zone_dearer_pct": float(100.0 * (delta > 1e-6).mean()),
            "hours_zone_cheaper_pct": float(100.0 * (delta < -1e-6).mean()),
            "mean_delta": float(delta.mean()),
            "max_abs_delta": float(np.abs(delta).max()),
        }
    return {
        "available": True,
        "external_zone": ext,
        "external_price_mean": float(ext_price.mean()),
        "vs_border": out,
    }


def main() -> None:
    """Run M1/M2/M3 for every scored year and write the machine output."""
    out = {
        "probe": "pjm135_star_node_import",
        "charter": "FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md §7",
        "no_lp": True,
        "arm_a_dir": str(ARM_A_DIR),
        "finding_reference_2025": {
            "external_to_dominion_mw": FINDING_EXTERNAL_TO_DOM_MW_2025,
            "external_to_dominion_twh": FINDING_EXTERNAL_TO_DOM_TWH_2025,
        },
        "interface_neighbors": {
            n.name: list(n.border_zones) for n in INTERFACE_NEIGHBORS.get("PJM", [])
        },
        "years": {},
    }
    for year in YEARS:
        m12 = measure_m1_m2(year)
        m3 = measure_m3(year)
        out["years"][str(year)] = {"m1_m2": m12, "m3": m3}

        dom = m12["borders"]["PJM_Dominion"]
        print(f"\n===== {year} =====")
        print(
            f"  Dominion measured net import   {dom['measured_net_import_mw_mean']:8.1f} MW"
            f"   ({dom['measured_net_import_twh']:+6.2f} TWh)"
        )
        print(
            f"  Dominion measured import side  {dom['measured_import_side_mw_mean']:8.1f} MW"
            f"   (importing {dom['measured_hours_importing_pct']:.1f} % of hours)"
        )
        print(
            f"  Dominion model import band     {dom['import_cap_mw_mean']:8.1f} MW"
            f"   ({dom['import_cap_twh_if_ridden']:+6.2f} TWh if ridden)"
        )
        print(
            f"  band / measured import side    {dom['band_over_measured_import_side']:8.2f} x"
            f"   | band above measured in {dom['hours_cap_above_measured_import_pct']:.1f} % of hours"
        )
        print(
            f"  band R2 vs measured hourly     {dom['cap_r2_vs_measured_import']:8.3f}"
            f"   | {dom['cap_distinct_values']} distinct band values over 8760 h"
        )
        if m3.get("available"):
            d = m3["vs_border"]["PJM_Dominion"]
            print(
                f"  M3 external vs Dominion dual   tied in {d['hours_tied_exact_pct']:.2f} % of hours"
                f"   (max |Δ| = {d['max_abs_delta']:.4f} $/MWh)"
            )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
