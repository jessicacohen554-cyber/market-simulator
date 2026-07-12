"""G-22 idle-supply audit: WHY is the PJM summer peak never tight?

At the top-N system-load hours of each solved year, decompose the model's
supply position against the measured DA price actuals:

  1. Load-weighted model price vs actual DA at the top hours.
  2. Net interchange (the PJM_external node's import tranches minus export
     sinks) — is the model exporting through measured scarcity hours?
  3. Idle-but-offered thermal supply by class: available (pmax x availability)
     minus dispatched, and where each idle MW's OFFER (the LP's own mc_base,
     returned by run_year(fleet_only=True)) sits relative to (a) the model's
     clearing price and (b) the ACTUAL DA price of the same hour.
  4. The offer-stack depth in the price band between the model's clearing
     price and the actual DA price — the "phantom sub-actual spare" that caps
     the energy dual (which class it belongs to, and at what offer heights).

Reads a solved run_dir (dispatch/{year}_P1.parquet + system.parquet) and the
bundle meta.json; rebuilds fleet arrays + mc through the bundle's own config
(no LP re-solve — the derive_pjm_ordc_overlay pattern). Pure diagnostic
(rule 16): writes ``idle_supply_audit_<year>.json`` + a per-class CSV into the
run_dir and prints the tables.

Usage:
    python scripts/probes/_g22_idle_supply_audit.py \
        results/calibration/pjm97_baseline_20260711 [--years 2024] [--top 150]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.interchange_config import IMPORT_ZONE  # noqa: E402

CAL_DIR = REPO / "data" / "raw" / "_validation-source"

# Thermal classes reported individually; everything else pools into "other".
_CLASSES = (
    "CC_REGULAR",
    "CT_PEAKER",
    "CT_INTERMEDIATE",
    "ST_GAS",
    "COAL_BIT",
    "COAL_PRB",
    "COAL",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "oil",
    "nuclear",
)


def _actual_da(year: int, hours: int) -> np.ndarray:
    """Hourly measured PJM DA system LMP ($/MWh) from the validation source."""
    df = pd.read_parquet(CAL_DIR / "actual_lmp_hourly_PJM.parquet")
    df = df[df["year"] == year]
    out = np.full(hours, np.nan)
    idx = df["hour"].to_numpy(dtype=int)
    keep = (idx >= 0) & (idx < hours)
    out[idx[keep]] = df["da"].to_numpy(dtype=float)[keep]
    return out


def audit_year(bundle: Path, year: int, top_n: int, meta: dict) -> dict:
    """Run the idle-supply decomposition for one solved year."""
    from derive_pjm_ordc_overlay import _run_year_kwargs
    from run_calibration import run_year

    hours = int(meta["hours"])
    state = run_year(
        year,
        meta["iso"],
        hours,
        meta["gas_prices"][str(year)],
        **_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T)
    avail = fa.pmax[:, None] * fa.availability  # (n_gen, T)
    uids = np.asarray(fa.unit_ids, dtype=object)
    ext_zone = IMPORT_ZONE.get(meta["iso"], "")

    sysf = pd.read_parquet(bundle / "system.parquet")
    sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == "P1")]
    internal = sysf[sysf["zone"] != ext_zone]
    load = internal.groupby("hour")["demand"].sum().to_numpy()  # (T,)
    pxd = (internal["price"] * internal["demand"]).groupby(internal["hour"]).sum()
    lw_price = (pxd / internal.groupby("hour")["demand"].sum()).to_numpy()  # (T,)

    da = _actual_da(year, hours)
    top = np.argsort(load)[-top_n:]  # top-N hours by system load
    top = top[np.isfinite(da[top])]

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    disp = disp[disp["pass"] == "P1"]
    # Net interchange from the external-node units: imports inject (+mw),
    # export sinks withdraw (-mw); net model EXPORT = -(sum of node mw).
    ext_units = disp[disp["zone"] == ext_zone]
    net_export = np.zeros(hours)
    if len(ext_units):
        s = ext_units.groupby("hour", observed=True)["mw"].sum()
        net_export[s.index.to_numpy(dtype=int)] = -s.to_numpy(dtype=float)

    # Unit x hour dispatch matrix aligned to fleet order (thermal LP units only).
    dmat = (
        disp[disp["unit_id"].isin(set(map(str, uids)))]
        .pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )

    grp = (
        np.asarray(fa.plant_group, dtype=object)
        if fa.plant_group is not None
        else np.array([""] * len(uids), dtype=object)
    )
    # External-node pseudo units ride in fleet_arrays too — exclude them from
    # the thermal idle accounting (they are the interchange, reported above).
    zone_names = (
        list(state["config"].zones) if hasattr(state["config"], "zones") else []
    )
    del zone_names  # zone-of-unit resolved via the dispatch frame instead
    unit_zone = (
        disp.drop_duplicates("unit_id")
        .set_index("unit_id")["zone"]
        .reindex(uids)
        .astype(object)
        .fillna("")
        .to_numpy()
    )
    is_ext = unit_zone == ext_zone

    rows = []
    t = top
    idle = np.clip(avail[:, t] - dmat[:, t], 0.0, None)  # (n_gen, |top|)
    below_actual = mc[:, t] < da[t][None, :]
    below_model = mc[:, t] <= lw_price[t][None, :] + 0.01
    for cls in _CLASSES:
        m = (grp == cls) & ~is_ext
        if not m.any():
            continue
        rows.append(
            {
                "class": cls,
                "avail_gw": float(avail[m][:, t].sum(axis=0).mean() / 1e3),
                "disp_gw": float(dmat[m][:, t].sum(axis=0).mean() / 1e3),
                "idle_gw": float(idle[m].sum(axis=0).mean() / 1e3),
                "idle_below_actual_gw": float(
                    (idle[m] * below_actual[m]).sum(axis=0).mean() / 1e3
                ),
                "idle_below_model_gw": float(
                    (idle[m] * below_model[m]).sum(axis=0).mean() / 1e3
                ),
                "idle_mc_p50": float(
                    np.median(mc[m][:, t][idle[m] > 0.5])
                    if (idle[m] > 0.5).any()
                    else np.nan
                ),
                "idle_mc_p90": float(
                    np.quantile(mc[m][:, t][idle[m] > 0.5], 0.9)
                    if (idle[m] > 0.5).any()
                    else np.nan
                ),
            }
        )
    per_class = pd.DataFrame(rows).sort_values("idle_gw", ascending=False)

    # Offer-stack depth between the model clearing price and the actual DA
    # price, per hour: MW of available supply whose offer lands inside the gap.
    thermal = ~is_ext
    gap_mw = np.zeros(len(t))
    for j in range(len(t)):
        h = t[j]
        in_gap = (mc[thermal, h] > lw_price[h]) & (mc[thermal, h] < da[h])
        gap_mw[j] = avail[thermal, h][in_gap].sum()

    out = {
        "year": year,
        "top_n": int(len(t)),
        "load_gw_mean": float(load[t].mean() / 1e3),
        "model_lw_price": float(lw_price[t].mean()),
        "actual_da_lw": float(da[t].mean()),
        "actual_da_max": float(np.nanmax(da[t])),
        "model_price_max": float(lw_price[t].max()),
        "net_export_gw_mean": float(net_export[t].mean() / 1e3),
        "net_export_gw_all_year": float(net_export.mean() / 1e3),
        "idle_thermal_gw_mean": float(idle[thermal].sum(axis=0).mean() / 1e3),
        "idle_below_actual_gw_mean": float(
            (idle[thermal] * below_actual[thermal]).sum(axis=0).mean() / 1e3
        ),
        "stack_mw_between_model_and_actual_mean": float(gap_mw.mean()),
        "per_class": per_class.to_dict(orient="records"),
    }

    print(
        f"\n=== {year} top-{len(t)} load hours (mean load {out['load_gw_mean']:.1f} GW) ==="
    )
    print(
        f"model LW price ${out['model_lw_price']:.1f} vs actual DA ${out['actual_da_lw']:.1f} "
        f"(max model ${out['model_price_max']:.0f} / actual ${out['actual_da_max']:.0f})"
    )
    print(
        f"net export mean {out['net_export_gw_mean']:.2f} GW (all-year "
        f"{out['net_export_gw_all_year']:.2f}); idle thermal {out['idle_thermal_gw_mean']:.1f} GW, "
        f"of which {out['idle_below_actual_gw_mean']:.1f} GW offered BELOW the actual DA price"
    )
    print(
        f"stack depth between model price and actual price: "
        f"{out['stack_mw_between_model_and_actual_mean'] / 1e3:.1f} GW mean"
    )
    print(per_class.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=None)
    ap.add_argument("--top", type=int, default=150)
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    years = args.years or meta["years"]
    results = []
    for year in years:
        if not (args.bundle / "dispatch" / f"{year}_P1.parquet").exists():
            print(f"{year}: no dispatch parquet yet — skipping")
            continue
        results.append(audit_year(args.bundle, int(year), args.top, meta))

    out_path = args.bundle / "idle_supply_audit.json"
    out_path.write_text(json.dumps(results, indent=1))
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    main()
