"""ERCOT-146 Phase 1 probe — measured_ct_heat_rates on ERCOT's CT fleet (no LP).

Matrix §5.1 item 6. Quantifies, on the committed artifact just derived
(``campd_ct_heat_rates_ERCOT.csv``) and the ercot145 keeper's own bundle,
everything the adjudication needs WITHOUT building an LP:

  Leg 1 — wiring: does ``ScenarioConfig.measured_ct_heat_rates`` reach the
          fleet ERCOT actually dispatches (the curated CAMPD bin sheet)?
          Proven by building the base fleet flag-on vs flag-off and diffing.
  Leg 2 — the delta on the DISPATCHED basis: measured loaded HR vs the
          curated sheet's ``Plant_Avg_HR_MMBtu_MWh`` (what the LP prices),
          alongside the eGRID basis the artifact's own column records.
  Leg 3 — coverage: share of curated CT_PEAKER capacity AND of metered TX
          CT energy; adverse-selection check (covered vs uncovered rates,
          the caiso-146 template).
  Leg 4 — reach: CT_PEAKER share of ISO load on the keeper's sidecars and
          the fitted-band margins the swap would ride through.

Run: python scripts/probes/ercot146_ct_heat_rates_phase1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

ARTIFACT = PROCESSED_DIR / "campd_ct_heat_rates_ERCOT.csv"
UNITS = PROCESSED_DIR / "campd_ct_heat_rates_ERCOT_units.csv"
BINS_CSV = RAW_DIR / "reference" / "custom-bin-assignments.csv"
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
KEEPER = REPO / "results" / "calibration" / "ercot145_gas_daily_arm"


def leg1_wiring() -> None:
    """Prove whether the flag reaches the dispatched ERCOT fleet (no LP)."""
    print("=" * 72)
    print("LEG 1 — wiring: does the flag touch the fleet ERCOT dispatches?")
    print("=" * 72)
    from market_sim.data.fleet import assembly

    cfg_off = ScenarioConfig(iso="ERCOT")
    cfg_on = ScenarioConfig(iso="ERCOT", measured_ct_heat_rates=True)
    iso_cfg = get_iso_config("ERCOT")

    fleets = {}
    for tag, cfg in [("off", cfg_off), ("on", cfg_on)]:
        zone_names = [z.name for z in iso_cfg.zones]
        bins = assembly.load_or_synthesize_bins(cfg, "ERCOT", iso_cfg, [])
        fleet = assembly.build_base_fleet(
            bins, "ERCOT", iso_cfg, zone_names, cfg, [], [],
            year=cfg.start_year,
        )
        rows = sorted(
            (g.name, int(g.plant_code or 0), g.plant_group,
             round(float(g.heat_rate), 6), round(float(g.pmax_mw), 3))
            for g in fleet
        )
        fleets[tag] = rows
        print(f"  flag={tag}: {len(rows)} generators")

    if fleets["off"] == fleets["on"]:
        print("  VERDICT: BYTE-IDENTICAL fleet (name, plant, group, HR, pmax)")
        print("  -> measured_ct_heat_rates is a STRUCTURAL NO-OP on ERCOT")
    else:
        diff = [
            (a, b) for a, b in zip(fleets["off"], fleets["on"]) if a != b
        ]
        print(f"  VERDICT: {len(diff)} rows differ; flag IS live on ERCOT")
        for a, b in diff[:10]:
            print(f"    off={a}\n     on={b}")


def leg2_dispatched_basis() -> pd.DataFrame:
    """Delta of measured loaded HR vs the curated sheet the LP prices."""
    print()
    print("=" * 72)
    print("LEG 2 — measured vs the DISPATCHED basis (curated Plant_Avg_HR)")
    print("=" * 72)
    art = pd.read_csv(ARTIFACT)
    sheet = pd.read_csv(BINS_CSV)
    ct = sheet[sheet["Plant_Group"] == "CT_PEAKER"][
        ["Plant_Code", "Plant_Name", "Nameplate_MW", "Plant_Avg_HR_MMBtu_MWh"]
    ].rename(columns={"Plant_Code": "plant_code"})
    ct["plant_code"] = ct["plant_code"].astype(int)

    j = art.merge(ct, on="plant_code", how="outer", indicator=True)
    both = j[j["_merge"] == "both"].copy()
    art_only = j[j["_merge"] == "left_only"]
    sheet_only = j[j["_merge"] == "right_only"]

    both["delta_vs_sheet"] = both["heat_rate"] - both["Plant_Avg_HR_MMBtu_MWh"]
    both["ratio_vs_sheet"] = both["heat_rate"] / both["Plant_Avg_HR_MMBtu_MWh"]
    print(f"  artifact rows matched to curated CT_PEAKER bins: {len(both)}")
    print(f"  artifact-only (eia860 CT_PEAKER, not curated CT bin): "
          f"{len(art_only)} rows, "
          f"{art_only['class_capacity_mw'].sum():.0f} MW")
    if len(art_only):
        print(art_only[["plant_code", "plant_name", "class_capacity_mw",
                        "heat_rate"]].to_string(index=False))
    print(f"  curated-CT-bins with NO measured row: {len(sheet_only)}, "
          f"{sheet_only['Nameplate_MW'].sum():.0f} MW")

    w = both["Nameplate_MW"].to_numpy(float)
    print(f"\n  cap-weighted curated Plant_Avg_HR "
          f"{np.average(both['Plant_Avg_HR_MMBtu_MWh'], weights=w):.3f} "
          f"-> measured {np.average(both['heat_rate'], weights=w):.3f}  "
          f"({100 * (np.average(both['heat_rate'], weights=w) / np.average(both['Plant_Avg_HR_MMBtu_MWh'], weights=w) - 1):+.1f} %)")
    gw = both["gross_mwh"].to_numpy(float)
    print(f"  gen-weighted  curated "
          f"{np.average(both['Plant_Avg_HR_MMBtu_MWh'], weights=gw):.3f} "
          f"-> measured {np.average(both['heat_rate'], weights=gw):.3f}  "
          f"({100 * (np.average(both['heat_rate'], weights=gw) / np.average(both['Plant_Avg_HR_MMBtu_MWh'], weights=gw) - 1):+.1f} %)")
    cheaper = both[both["delta_vs_sheet"] < -0.5]
    dearer = both[both["delta_vs_sheet"] > 0.5]
    print(f"  moved >0.5 MMBtu/MWh vs sheet: {len(cheaper) + len(dearer)}/"
          f"{len(both)}  (cheaper {len(cheaper)} / "
          f"{cheaper['Nameplate_MW'].sum():.0f} MW, dearer {len(dearer)} / "
          f"{dearer['Nameplate_MW'].sum():.0f} MW)")
    cols = ["plant_code", "plant_name", "Nameplate_MW", "Plant_Avg_HR_MMBtu_MWh", "heat_rate", "delta_vs_sheet",
            "model_heat_rate_egrid"]
    print()
    print(both.sort_values("delta_vs_sheet")[cols].to_string(index=False))
    return both


def leg3_coverage(both: pd.DataFrame) -> None:
    """Coverage of class capacity + metered CT energy; adverse selection."""
    print()
    print("=" * 72)
    print("LEG 3 — coverage + adverse selection (caiso-146 template)")
    print("=" * 72)
    sheet = pd.read_csv(BINS_CSV)
    ct = sheet[sheet["Plant_Group"] == "CT_PEAKER"]
    total_cap = float(ct["Nameplate_MW"].sum())
    cov_cap = float(both["Nameplate_MW"].sum())
    print(f"  curated CT_PEAKER bins: {len(ct)} plants, {total_cap:.0f} MW")
    print(f"  covered by measured artifact: {len(both)} plants, "
          f"{cov_cap:.0f} MW = {100 * cov_cap / total_cap:.1f} % of curated "
          f"class capacity")

    # Metered CT energy coverage: all TX CAMPD 'Combustion turbine' unit
    # energy 2023-2025 at ANY curated CT_PEAKER plant vs covered plants.
    frames = []
    for year in (2023, 2024, 2025):
        df = pd.read_parquet(
            UNIT_LEVEL_DIR / f"TX_{year}.parquet",
            columns=["facilityId", "unitType", "grossLoad"],
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[
            df["unitType"].astype(str).str.strip().str.casefold()
            == "combustion turbine"
        ]
        frames.append(df.dropna(subset=["grossLoad"]))
    ctu = pd.concat(frames)
    ct_codes = set(ct["Plant_Code"].astype(int))
    in_class = ctu[ctu["facilityId"].isin(ct_codes)]
    cov_codes = set(both["plant_code"].astype(int))
    covered_e = float(in_class[in_class["facilityId"].isin(cov_codes)]["grossLoad"].sum())
    total_e = float(in_class["grossLoad"].sum())
    print(f"  metered TX CT-unit energy at curated CT_PEAKER plants "
          f"2023-25: {total_e / 1e6:.3f} TWh gross")
    print(f"  ...at covered plants: {covered_e / 1e6:.3f} TWh = "
          f"{100 * covered_e / max(total_e, 1e-9):.1f} % of metered class CT energy")

    unc = ct[~ct["Plant_Code"].astype(int).isin(cov_codes)]
    unc_hr = unc.dropna(subset=["Plant_Avg_HR_MMBtu_MWh", "Nameplate_MW"])
    print(f"\n  adverse selection (dispatched basis): covered cap-wt "
          f"Plant_Avg_HR "
          f"{np.average(both['Plant_Avg_HR_MMBtu_MWh'], weights=both['Nameplate_MW']):.3f}"
          f" vs uncovered "
          f"{(np.average(unc_hr['Plant_Avg_HR_MMBtu_MWh'], weights=unc_hr['Nameplate_MW']) if len(unc_hr) else float('nan')):.3f}"
          f"  ({len(unc)} plants, {unc['Nameplate_MW'].sum():.0f} MW; "
          f"{len(unc) - len(unc_hr)} rows no sheet HR)")
    # Metered energy of the uncovered big four (Morgan Creek / Denton /
    # Red Gate / Pearsall) — are they CTs CAMPD sees under another unitType?
    big = unc.sort_values("Nameplate_MW", ascending=False).head(6)
    frames2 = []
    for year in (2023, 2024, 2025):
        d2 = pd.read_parquet(
            UNIT_LEVEL_DIR / f"TX_{year}.parquet",
            columns=["facilityId", "unitType", "grossLoad"],
        )
        d2["facilityId"] = pd.to_numeric(d2["facilityId"], errors="coerce")
        frames2.append(d2[d2["facilityId"].isin(set(big["Plant_Code"].astype(int)))])
    d2 = pd.concat(frames2).dropna(subset=["grossLoad"])
    print("  top uncovered plants — CAMPD presence by unitType:")
    if d2.empty:
        print("    (no CAMPD hours at all — outside Part-75 CEMS)")
    else:
        print(d2.groupby(["facilityId", "unitType"])["grossLoad"]
              .agg(["count", "sum"]).to_string())
    print("  uncovered curated CT bins (largest first):")
    print(unc.sort_values("Nameplate_MW", ascending=False)[
        ["Plant_Code", "Plant_Name", "Nameplate_MW", "Plant_Avg_HR_MMBtu_MWh"]
    ].head(12).to_string(index=False))


def leg4_reach() -> None:
    """CT_PEAKER materiality + the fitted margins on the keeper's bundle."""
    print()
    print("=" * 72)
    print("LEG 4 — reach on the ercot145 keeper's own sidecars")
    print("=" * 72)
    import json

    cfg = json.loads((KEEPER / "run_config.json").read_text())
    sc = cfg.get("scenario_config", cfg)
    oc = sc["offer_curve_by_group"]["CT_PEAKER"]
    print("  keeper CT_PEAKER offer_curve_by_group (FITTED incumbents):")
    for k in ("committed", "econ_low", "econ_high", "peak"):
        print(f"    {k:10s} fitted {oc[k]:>6}  phys {oc.get('phys_' + k, 'n/a')}")

    for year in (2023, 2024, 2025):
        df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        df = df[df["pass"] == "P1"]
        ct_e = float(df.loc[df["klass"] == "CT_PEAKER", "mw"].sum())
        s = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        tot = float(s["demand"].sum())
        print(f"  {year}: CT_PEAKER energy {ct_e / 1e6:.3f} TWh, ISO load "
              f"{tot / 1e6:.3f} TWh -> {100 * ct_e / tot:.2f} % of load")


if __name__ == "__main__":
    leg1_wiring()
    both = leg2_dispatched_basis()
    leg3_coverage(both)
    leg4_reach()
