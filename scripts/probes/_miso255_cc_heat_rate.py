"""miso-255 phase 0, item 3(b): is MISO's CC_REGULAR heat rate too CHEAP?

Re-measures ``pjm-h1`` §3's heat-rate falsification on **MISO's own data**
(rule 28(d) ``[R-MECH-MATRIX]``: a PJM verdict fills no MISO cell). The
asymmetry that motivates it is the same in MISO: ``measured_ct_heat_rates``
(**K**) and ``measured_chp_heat_rates`` (**K**) are armed mechanisms, while
CC_REGULAR carries the eGRID plant-average ANNUAL rate and has no measured
artifact at all.

Model side: :func:`market_sim.data.fleet.eia860.load_fleet_from_csv` at the
KEEPER's own heat-rate flags (``measured_ct_heat_rates=True``,
``measured_chp_heat_rates=True``, ``cc_steam_part_capacity=True``, every
eGRID variant off — ``results/calibration/miso_fuelvintage_A/run_config.json``).
Measured side: CAMPD unit-level ``heatInput / grossLoad`` over operating hours
only, pooled 2023-2025, on ``unitType`` rows naming a combined cycle, converted
gross -> net at a STATED (not fitted) 2.2 % own-use, the same figure pjm-h1
used. **Zero LP.**
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import legitimacy_diagnostics as L  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

OWN_USE = 0.022  # stated, not fitted — pjm-h1 §3's own figure, reused verbatim
POOL_YEARS = (2023, 2024, 2025)


def bench_cc_plants() -> dict[str, float]:
    """CC_REGULAR plant codes -> matched bench nameplate, union over the pool."""
    out: dict[str, float] = {}
    for y in POOL_YEARS:
        for k, b in L.load_bench(REPO, "MISO", y).items():
            if b["group"] == "CC_REGULAR":
                code = k.split(":")[0]
                out[code] = max(out.get(code, 0.0), float(b["npl"]))
    return out


def measured_rates(codes: set[str]) -> pd.DataFrame:
    """Per-plant CAMPD gross heat rate over operating hours, pooled."""
    frames = []
    for path in sorted((REPO / "data/raw/campd-unit-level").glob("*.parquet")):
        year = int(path.stem.split("_")[1])
        if year not in POOL_YEARS:
            continue
        d = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "opTime",
                "grossLoad",
                "heatInput",
                "unitType",
            ],
        )
        d = d[d["facilityId"].astype(str).isin(codes)]
        if d.empty:
            continue
        d = d[d["unitType"].astype(str).str.contains("ombined cycle", na=False)]
        d = d[(d["opTime"] > 0) & (d["grossLoad"] > 0) & (d["heatInput"] > 0)]
        if not d.empty:
            frames.append(d[["facilityId", "grossLoad", "heatInput"]])
    if not frames:
        return pd.DataFrame(columns=["gross_mwh", "heat_mmbtu", "hr_gross"])
    d = pd.concat(frames, ignore_index=True)
    g = d.groupby(d["facilityId"].astype(str)).agg(
        gross_mwh=("grossLoad", "sum"), heat_mmbtu=("heatInput", "sum")
    )
    g["hr_gross"] = g["heat_mmbtu"] / g["gross_mwh"]
    g["hr_net"] = g["hr_gross"] / (1.0 - OWN_USE)
    g["rows"] = d.groupby(d["facilityId"].astype(str)).size()
    return g


def model_rates(codes: set[str]) -> pd.DataFrame:
    """Per-plant capacity-weighted model heat rate for the CC_REGULAR class."""
    fleet = load_fleet_from_csv(
        "MISO",
        year=2023,
        measured_ct_heat_rates=True,
        measured_chp_heat_rates=True,
        cc_steam_part_capacity=True,
    )
    rows = []
    for g in fleet:
        klass = getattr(g, "plant_group", "") or ""
        code = str(getattr(g, "plant_code", "") or "")
        if klass != "CC_REGULAR" or code not in codes:
            continue
        rows.append(
            {
                "facilityId": code,
                "pmax": float(g.pmax_mw),
                "hr": float(g.heat_rate),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["pmax", "hr_model"])
    d = pd.DataFrame(rows)
    d["w"] = d["pmax"] * d["hr"]
    out = d.groupby("facilityId").agg(pmax=("pmax", "sum"), w=("w", "sum"))
    out["hr_model"] = out["w"] / out["pmax"]
    return out[["pmax", "hr_model"]]


def main() -> None:
    npl = bench_cc_plants()
    codes = set(npl)
    print(f"bench CC_REGULAR plants over {POOL_YEARS}: {len(codes)}")

    meas = measured_rates(codes)
    print(
        f"CAMPD combined-cycle operating rows matched: {int(meas['rows'].sum()):,}"
        f" on {len(meas)} plants; {meas['gross_mwh'].sum() / 1e6:.1f} TWh gross"
    )
    mod = model_rates(codes)
    print(f"model CC_REGULAR plants assembled: {len(mod)}")

    j = mod.join(meas, how="inner")
    j["delta"] = j["hr_model"] - j["hr_net"]
    print(f"paired plants: {len(j)}")
    if j.empty:
        return

    cw_model = float((j["hr_model"] * j["pmax"]).sum() / j["pmax"].sum())
    cw_meas = float((j["hr_net"] * j["pmax"]).sum() / j["pmax"].sum())
    n_cheap = int((j["delta"] < 0).sum())
    n_dear = int((j["delta"] > 0).sum())
    print("\n" + "=" * 78)
    print("MISO CC_REGULAR heat rate — model vs CAMPD measured (MMBtu/MWh, NET)")
    print("=" * 78)
    print(f"  capacity-weighted model     {cw_model:8.4f}")
    print(f"  capacity-weighted measured  {cw_meas:8.4f}   (gross / (1 - {OWN_USE}))")
    print(
        f"  delta                       {cw_model - cw_meas:+8.4f}"
        f"  ({100.0 * (cw_model - cw_meas) / cw_meas:+.2f} %)"
    )
    print(f"  median per-plant delta      {float(j['delta'].median()):+8.4f}")
    print(f"  plants model CHEAP          {n_cheap:4d} / {len(j)}")
    print(f"  plants model DEAR           {n_dear:4d} / {len(j)}")
    print("\n  largest model-CHEAP outliers (model - measured):")
    for code, r in j.nsmallest(6, "delta").iterrows():
        print(
            f"    {code:>8s}  model {r['hr_model']:7.3f}  meas {r['hr_net']:7.3f}"
            f"  delta {r['delta']:+7.3f}  pmax {r['pmax']:8.1f}"
        )
    print("\n  largest model-DEAR outliers:")
    for code, r in j.nlargest(6, "delta").iterrows():
        print(
            f"    {code:>8s}  model {r['hr_model']:7.3f}  meas {r['hr_net']:7.3f}"
            f"  delta {r['delta']:+7.3f}  pmax {r['pmax']:8.1f}"
        )


if __name__ == "__main__":
    main()
