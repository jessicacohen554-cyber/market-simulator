"""caiso-72 STEP-0 analysis: SoCal evening supply stack + link flows.

Reads the throwaway 2024 diagnostic bundle
(results/calibration/caiso72_step0_diag2024) and answers, with numbers:
in the evening hours (hod 17-22) where reality runs SoCal CT peakers, what
does the model serve that load with instead, and over which link does it
arrive?

Outputs (stdout):
  1. SoCal (LA_BASIN+SDGE+SP15_rest) mean MW by class x hour-of-day 16-23.
  2. Per-link mean flow by hour-of-day + share of evening hours at >=99% of
     the static link TTC (which limits actually bind).
  3. LA_BASIN / SDGE pocket balance (load vs local gen vs pocket import).
  4. Model vs CAMPD-actual CT_PEAKER evening profile (the displacement gap).

Usage: python scripts/probes/_caiso72_step0_analyze.py [run_dir]
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else ROOT / "results" / "calibration" / "caiso72_step0_diag2024"
)
EVENING = range(17, 23)  # hod 17-22, the CT displacement window
YEAR = 2024
SOCAL = ["LA_BASIN", "SDGE", "SP15_rest"]


def hod(df: pd.DataFrame) -> pd.Series:
    return df["hour"] % 24


def main() -> None:
    disp = pd.read_parquet(RUN / "dispatch" / f"{YEAR}_P1.parquet")
    disp["hod"] = hod(disp)

    # --- 1. SoCal supply stack by class x hod -------------------------------
    soc = disp[disp["zone"].isin(SOCAL)]
    stack = (
        soc.groupby(["klass", "hod"], observed=True)["mw"].sum().unstack("hod") / 365.0
    ).round(0)
    ev_cols = [h for h in range(14, 24)]
    print("=== SoCal (LA_BASIN+SDGE+SP15_rest) mean MW by class, hod 14-23 ===")
    big = stack[ev_cols]
    print(big[big.max(axis=1) > 50].sort_values(20, ascending=False).to_string())

    # Storage by zone (charge/discharge)
    st_path = RUN / "storage.parquet"
    if st_path.exists():
        st = pd.read_parquet(st_path)
        st = st[(st["year"] == YEAR) & (st["pass"] == "P1")]
        st["hod"] = st["hour"] % 24
        st_soc = st[st["zone"].isin(SOCAL)]
        prof = (
            st_soc.groupby("hod")[["charge_mw", "discharge_mw"]].sum() / 365.0
        ).round(0)
        print("\n=== SoCal storage charge/discharge mean MW by hod ===")
        print(prof.loc[list(range(14, 24))].T.to_string())

    # --- 2. link flows ------------------------------------------------------
    flows = pd.read_parquet(RUN / "flows.parquet")
    flows = flows[(flows["year"] == YEAR) & (flows["pass"] == "P1")]
    flows["hod"] = flows["hour"] % 24
    flows["link"] = flows["from_zone"].astype(str) + "->" + flows["to_zone"].astype(str)
    prof = (flows.groupby(["link", "hod"])["mw"].mean().unstack("hod")).round(0)
    print("\n=== link mean flow MW by hod 14-23 (positive = from->to) ===")
    print(prof[[h for h in range(14, 24)]].to_string())

    # evening binding shares vs each link's max observed |flow| (proxy for cap)
    ev = flows[flows["hod"].isin(EVENING)]
    cap = flows.groupby("link")["mw"].max()
    share = (
        ev.assign(at_cap=lambda d: d["mw"] >= 0.99 * d["link"].map(cap))
        .groupby("link")["at_cap"]
        .mean()
    )
    peak = ev.groupby("link")["mw"].max()
    print(
        "\n=== evening (hod17-22): max flow, share of evening hours at >=99% of annual-max flow ==="
    )
    out = pd.DataFrame(
        {
            "annual_max_mw": cap.round(0),
            "evening_max_mw": peak.round(0),
            "evening_share_at_annual_max": share.round(3),
        }
    )
    print(out.to_string())

    # --- 3. pocket balances -------------------------------------------------
    print("\n=== pocket balance, mean MW by hod (evening) ===")
    demand_by_zone_hod = None
    sys_path = RUN / "system.parquet"
    if sys_path.exists():
        system = pd.read_parquet(sys_path)
        system = system[(system["year"] == YEAR) & (system["pass"] == "P1")]
        if "demand_mw" in system.columns and "zone" in system.columns:
            system["hod"] = system["hour"] % 24
            demand_by_zone_hod = system.groupby(["zone", "hod"], observed=True)[
                "demand_mw"
            ].mean()
        else:
            print("system.parquet columns:", list(system.columns))
    for zone in ("LA_BASIN", "SDGE"):
        gen = disp[disp["zone"] == zone].groupby("hod")["mw"].sum() / 365.0
        imp = flows[flows["to_zone"] == zone].groupby("hod")["mw"].mean()
        exp = flows[flows["from_zone"] == zone].groupby("hod")["mw"].mean()
        row = pd.DataFrame({"local_gen": gen, "import": imp, "export": exp})
        if (
            demand_by_zone_hod is not None
            and zone in demand_by_zone_hod.index.get_level_values(0)
        ):
            row["demand"] = demand_by_zone_hod.loc[zone]
        print(f"\n-- {zone} --")
        print(row.loc[list(range(14, 24))].round(0).T.to_string())

    # --- 4. model vs actual CT_PEAKER evening -------------------------------
    meta = json.loads((RUN / "meta.json").read_text())
    shared = meta.get("shared_inputs", {})
    campd_ref = shared.get("campd")
    if campd_ref:
        campd_path = ROOT / "results" / "calibration" / "_shared" / campd_ref
        if not campd_path.exists():
            campd_path = Path(campd_ref)
        if campd_path.exists():
            campd = pd.read_parquet(campd_path)
            print("\ncampd columns:", list(campd.columns))
            camp = campd[campd["year"] == YEAR] if "year" in campd.columns else campd
            # model CT klass by plant: use dispatch frame's plant->klass map
            pk = (
                disp[["plant_code", "klass"]]
                .drop_duplicates()
                .set_index("plant_code")["klass"]
            )
            camp = camp.assign(klass=camp["plant_id"].map(pk))
            ct_act = camp[camp["klass"] == "CT_PEAKER"]
            if "hour" in ct_act.columns:
                ct_act = ct_act.assign(hod=ct_act["hour"] % 24)
                actual_prof = ct_act.groupby("hod")["net_mw"].sum() / 365.0
                model_prof = (
                    disp[disp["klass"] == "CT_PEAKER"].groupby("hod")["mw"].sum()
                    / 365.0
                )
                cmp_df = pd.DataFrame(
                    {"model_CT": model_prof, "actual_CT": actual_prof}
                ).round(0)
                print(
                    "\n=== CT_PEAKER (all CAISO): model vs CAMPD actual, mean MW by hod ==="
                )
                print(cmp_df.T.to_string())
                print(
                    f"\nannual: model {model_prof.sum() * 365 / 1e6:.2f} TWh"
                    f" vs actual {actual_prof.sum() * 365 / 1e6:.2f} TWh"
                )


if __name__ == "__main__":
    main()
