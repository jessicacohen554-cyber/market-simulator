"""pjm-161 Phase-0 probe: close the PJM 2022 energy balance (no LP).

Reads committed artifacts ONLY — the 2022 touchpoint bundle's hourly sidecars,
the committed bench actuals, and the raw PJM interchange CSV. Never solves.

Question it answers: the 2022 touchpoint burns +18.28 TWh of extra CC_REGULAR
(+22.33 TWh of extra gas family) while coal lands dead-on. Where does that
energy GO? Every MWh the model produces must leave through load, exports, or
storage charging. This closes the balance term by term against 2023-2025, so a
2022-specific term is separable from the standing in-sample defect.

Usage: uv run python scripts/probes/_pjm161_energy_balance.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"
XCHG = REPO / "data" / "raw" / "iso-specific-transmission"

# Bundle -> the year its hourly sidecars cover.
BUNDLES = {
    2022: REPO / "results" / "calibration" / "pjm2022_touchpoint",
    2023: REPO / "results" / "calibration" / "pjm152_collapse_A",
    2024: REPO / "results" / "calibration" / "pjm152_collapse_A",
    2025: REPO / "results" / "calibration" / "pjm152_collapse_A",
}

# EIA-930 fuel families -> the model classes that make them up, so the model
# side is aggregated on exactly the bench's own definition.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC")


def _model_class_twh(year: int) -> pd.Series:
    """Annual P1 TWh by class from a bundle's committed class_hourly sidecar."""
    path = BUNDLES[year] / "hourly" / f"class_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum().div(1e6)


def _model_system(year: int) -> pd.DataFrame:
    path = BUNDLES[year] / "hourly" / f"system_{year}.parquet"
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"]


def _model_storage_twh(year: int) -> dict[str, float]:
    path = BUNDLES[year] / "hourly" / f"storage_{year}.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    out = {}
    for col in ("charge_mw", "discharge_mw", "charge", "discharge", "mw"):
        if col in df.columns:
            out[col] = float(df[col].sum()) / 1e6
    return out


E930 = REPO / "data" / "raw" / "eia-930-hourly" / "PJM hourly.parquet"


def _e930_year(year: int) -> dict[str, float]:
    """EIA-930 BA-level annual TWh on ONE internally consistent system.

    EIA-930's own identity is ``Demand = Net generation - Total interchange``
    (interchange EXPORT-positive), so demand, net generation, the fuel
    breakdown and the seam all come from the same book — which the bench's
    mixed 930/923/CEMS blocks do not.
    """
    df = pd.read_parquet(E930)
    df = df[pd.to_datetime(df["Local date"]).dt.year == year]
    if df.empty:
        return {}
    g = lambda c: float(pd.to_numeric(df[c], errors="coerce").sum()) / 1e6  # noqa: E731
    return {
        "demand": g("Demand"),
        "netgen": g("Net generation"),
        "net_export": g("Total interchange"),  # 930 sign: export-positive
        "coal": g("NG: COL"),
        "gas": g("NG: NG"),
        "nuclear": g("NG: NUC"),
        "hydro": g("NG: WAT"),
        "solar": g("NG: SUN"),
        "wind": g("NG: WND"),
        "oil": g("NG: OIL"),
        "other": g("NG: OTH"),
    }


def _bench(year: int) -> dict:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]


def _actual_interchange_twh(year: int) -> dict[str, float]:
    """Actual PJM net interchange (TWh) from the ISO's own published file.

    Sign convention returned: ``net`` is POSITIVE for net IMPORT, matching the
    model's ``import`` pseudo-class, so the two are directly comparable.
    """
    path = XCHG / f"PJM_{year}_import_export_act_sch_interchange.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
    )
    df["actual_flow"] = pd.to_numeric(df["actual_flow"], errors="coerce")
    # `actual_flow` is already import-positive into PJM (see
    # scripts/data/derive_pjm_seam_ladders.py). Sum every tie line per hour to
    # get total net interchange, then integrate.
    hourly = df.groupby("datetime_beginning_ept")["actual_flow"].sum()
    return {
        "net_twh": float(hourly.sum()) / 1e6,
        "import_twh": float(hourly.clip(lower=0).sum()) / 1e6,
        "export_twh": float(-hourly.clip(upper=0).sum()) / 1e6,
        "n_hours": float(len(hourly)),
        "n_ties": float(df["tie_line"].nunique()),
    }


def main() -> None:
    rows = []
    for year in (2022, 2023, 2024, 2025):
        model = _model_class_twh(year)
        bench = _bench(year)
        actual = bench["classFull"]
        sysdf = _model_system(year)

        model_gas = sum(float(model.get(c, 0.0)) for c in GAS_CLASSES)
        model_coal = sum(float(model.get(c, 0.0)) for c in COAL_CLASSES)
        e930 = bench.get("e930", {})

        # Everything the model physically injected (excludes the virtual
        # bid pseudo-classes, which are a DA financial overlay, and excludes
        # the `import` pseudo-class, which is the seam).
        physical = [k for k in model.index if not k.startswith("VIRTUAL_") and k != "import"]
        model_gen = float(model[physical].sum())
        model_net_import = float(model.get("import", 0.0))
        model_load = float(sysdf["demand"].sum()) / 1e6
        model_slack = float(sysdf["slack"].sum()) / 1e6
        model_dump = float(sysdf["dump"].sum()) / 1e6
        virt = {
            k: float(model.get(k, 0.0)) for k in ("VIRTUAL_INC", "VIRTUAL_DEC")
        }
        storage = _model_storage_twh(year)
        xchg = _actual_interchange_twh(year)

        rows.append(
            dict(
                year=year,
                model_gen=model_gen,
                model_net_import=model_net_import,
                model_load=model_load,
                model_slack=model_slack,
                model_dump=model_dump,
                model_gas=model_gas,
                actual_gas=e930.get("gas"),
                model_coal=model_coal,
                actual_coal=e930.get("coal"),
                model_hydro=float(model.get("hydro", 0.0)),
                actual_hydro=actual.get("hydro"),
                model_nuclear=float(model.get("nuclear", 0.0)),
                actual_nuclear=actual.get("nuclear"),
                model_oil=float(model.get("oil", 0.0)),
                actual_oil=actual.get("oil"),
                model_other=float(model.get("OTHER", 0.0)),
                actual_other=actual.get("OTHER"),
                model_biomass=float(model.get("biomass", 0.0)),
                actual_biomass=actual.get("biomass"),
                actual_net_import=xchg.get("net_twh"),
                actual_import=xchg.get("import_twh"),
                actual_export=xchg.get("export_twh"),
                **virt,
                **{f"stor_{k}": v for k, v in storage.items()},
            )
        )

    df = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 200, "display.max_columns", 60)

    print("=" * 78)
    print("PJM ENERGY BALANCE — model (P1) vs actual, TWh")
    print("=" * 78)
    print(df.T.round(3).to_string())

    print()
    print("=" * 78)
    print("DERIVED: net export and the family residuals")
    print("=" * 78)
    out = pd.DataFrame(index=df.index)
    out["model_net_export"] = -df["model_net_import"]
    out["actual_net_export"] = -df["actual_net_import"]
    out["export_gap(model-actual)"] = out["model_net_export"] - out["actual_net_export"]
    out["gas_resid"] = df["model_gas"] - df["actual_gas"]
    out["coal_resid"] = df["model_coal"] - df["actual_coal"]
    out["hydro_resid"] = df["model_hydro"] - df["actual_hydro"]
    out["oil_resid"] = df["model_oil"] - df["actual_oil"]
    out["nuclear_resid"] = df["model_nuclear"] - df["actual_nuclear"]
    out["thermal_resid_sum"] = (
        out["gas_resid"] + out["coal_resid"] + out["hydro_resid"] + out["oil_resid"]
        + out["nuclear_resid"]
    )
    print(out.T.round(3).to_string())

    print()
    print("=" * 78)
    print("SINGLE-BASIS CLOSURE — EIA-930 BA book vs model (TWh)")
    print("  930 identity: Demand = NetGen - TotalInterchange (export-positive)")
    print("=" * 78)
    e = pd.DataFrame({y: _e930_year(y) for y in df.index}).T
    e.index.name = "year"
    m = pd.DataFrame(index=df.index)
    # Model side, put on the 930 book: virtual INC/DEC are a DA financial
    # overlay, so physical net generation is the class sum minus them; storage
    # is a net consumer.
    m["model_netgen"] = df["model_gen"] + df["VIRTUAL_INC"] + df["VIRTUAL_DEC"]
    m["model_net_export"] = -df["model_net_import"]
    m["model_demand"] = df["model_load"]
    m["model_storage_net_charge"] = df["stor_charge_mw"] - df["stor_discharge_mw"]
    m["implied_losses"] = (
        m["model_netgen"] - m["model_net_export"] - m["model_demand"]
        - m["model_storage_net_charge"]
    )
    comp = pd.DataFrame(index=df.index)
    comp["demand   model"] = m["model_demand"]
    comp["demand   930"] = e["demand"]
    comp["demand   Δ"] = m["model_demand"] - e["demand"]
    comp["netgen   model"] = m["model_netgen"]
    comp["netgen   930"] = e["netgen"]
    comp["netgen   Δ"] = m["model_netgen"] - e["netgen"]
    comp["netexp   model"] = m["model_net_export"]
    comp["netexp   930"] = e["net_export"]
    comp["netexp   Δ"] = m["model_net_export"] - e["net_export"]
    comp["gas      Δ"] = df["model_gas"] - e["gas"]
    comp["coal     Δ"] = df["model_coal"] - e["coal"]
    comp["nuclear  Δ"] = df["model_nuclear"] - e["nuclear"]
    comp["hydro+PS Δ"] = (
        df["model_hydro"] + df["stor_discharge_mw"] - df["stor_charge_mw"]
    ) - e["hydro"]
    comp["oil      Δ"] = df["model_oil"] - e["oil"]
    comp["other    Δ"] = (df["model_other"] + df["model_biomass"]) - e["other"]
    comp["renew    Δ"] = 0.0  # wind/solar are pinned to measured CF by design
    print(comp.T.round(3).to_string())

    print()
    print("balance identity check  gen + net_import - load - net_charge = 0")
    ident = df["model_gen"] + df["model_net_import"] - df["model_load"]
    print(ident.round(3).to_string())

    payload = {
        "balance": json.loads(df.reset_index().to_json(orient="records")),
        "derived": json.loads(out.reset_index().to_json(orient="records")),
        "e930_closure": json.loads(comp.reset_index().to_json(orient="records")),
    }
    dest = REPO / "results" / "calibration" / "_pjm161_energy_balance.json"
    dest.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
