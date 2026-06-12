"""Session helper: score a bundle against the size-aware bar vs run 85.

Usage: python scripts/_session_score.py <bundle> [<base bundle>=run85_coal_soft]

Prints the [3b]-style class table with TWh + %, the size-aware pass/fail
per class-year (>=20 TWh classes +/-5%, <20 TWh +/-1 TWh abs, CT_CHP
excluded), the in-scope fail count vs the base, the 2024 TWh ledger
(who gave/took vs the base), and the Martin Lake / Limestone plant guard.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "results" / "calibration"
CLASSES = ["CC_REGULAR", "CC_CHP", "COAL_PRB", "ST_GAS", "COAL_LIGNITE",
           "CT_PEAKER", "CT_CHP"]
GUARD_PLANTS = {6146: "Martin Lake", 298: "Limestone"}


def class_table(run: str) -> pd.DataFrame:
    d = ROOT / run
    e923 = pd.read_parquet(d / "eia923.parquet")
    btm = pd.read_parquet(d / "btm.parquet")
    rows = []
    for f in sorted((d / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6
        b = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = (e923[e923["year"] == year].groupby("klass")["annual_mwh"]
                 .sum() / 1e6)
        for cls in CLASSES:
            m = grid.get(cls, 0.0) + bt.get(cls, 0.0)
            a = bench.get(cls, 0.0)
            rows.append({"year": year, "class": cls, "model": m, "bench": a})
    return pd.DataFrame(rows)


def judge(row) -> str:
    if row["class"] == "CT_CHP":
        return "excl"
    if row["bench"] >= 20.0:
        return "PASS" if abs(row["model"] / row["bench"] - 1) <= 0.05 else "FAIL"
    return "PASS" if abs(row["model"] - row["bench"]) <= 1.0 else "FAIL"


def main() -> None:
    run = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else "run85_coal_soft"
    t = class_table(run)
    tb = class_table(base).rename(columns={"model": "base_model"})
    t = t.merge(tb[["year", "class", "base_model"]], on=["year", "class"])
    t["pct"] = (t["model"] / t["bench"] - 1) * 100
    t["dTWh"] = t["model"] - t["bench"]
    t["verdict"] = t.apply(judge, axis=1)
    t["base_pct"] = (t["base_model"] / t["bench"] - 1) * 100
    t["vs_base_TWh"] = t["model"] - t["base_model"]
    pd.set_option("display.width", 200)
    for yr in sorted(t["year"].unique()):
        s = t[t["year"] == yr].copy()
        for c in ("model", "bench", "base_model", "dTWh", "vs_base_TWh"):
            s[c] = s[c].round(2)
        for c in ("pct", "base_pct"):
            s[c] = s[c].round(1)
        print(f"\n== {yr} ==")
        print(s[["class", "model", "bench", "pct", "dTWh", "verdict",
                 "base_pct", "vs_base_TWh"]].to_string(index=False))
    fails = t[t["verdict"] == "FAIL"]
    base_t = class_table(base)
    base_t["model"], base_t["bench"] = base_t["model"], base_t["bench"]
    base_t["verdict"] = base_t.apply(judge, axis=1)
    print(f"\nin-scope fails: {run}={len(fails)}  "
          f"{base}={len(base_t[base_t['verdict'] == 'FAIL'])}")
    if len(fails):
        print(fails[["year", "class", "pct", "dTWh"]].round(2)
              .to_string(index=False))
    led = t[t["year"] == 2024].copy()
    led = led[led["vs_base_TWh"].abs() > 0.05]
    print(f"\n2024 ledger vs {base} (TWh):")
    print(led[["class", "vs_base_TWh"]].round(2).to_string(index=False))
    fit = pd.read_parquet(ROOT / run / "plant_hourly_fit.parquet")
    g = fit[fit["plant_code"].isin(GUARD_PLANTS)].copy()
    g["plant"] = g["plant_code"].map(GUARD_PLANTS)
    g["model-campd_GWh"] = (g["model_gwh"] - g["campd_gwh"]).round(0)
    print("\nplant guard (keep < ~+1000 GWh):")
    print(g[["year", "plant", "model_gwh", "campd_gwh", "model-campd_GWh"]]
          .to_string(index=False))
    gas = {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"}
    coal = {"COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL"}
    e923 = pd.read_parquet(ROOT / run / "eia923.parquet")
    e930 = pd.read_parquet(ROOT / run / "eia930.parquet")
    t930 = e930.groupby(["year", "series"])["mw"].sum() / 1e6
    btm = pd.read_parquet(ROOT / run / "btm.parquet")
    print("\nfuel split gate (gas and coal totals within +/-2.5% per year;"
          " 2023/2024 model incl. BTM vs EIA-923, the fossil source of"
          " truth; 2025 model grid-only vs EIA-930, the 923 vintage being"
          " incomplete; solar/wind are benchmarked against 930 only and are"
          " outside this gate. PRB year-spread inside +/-5% is accepted"
          " when its multi-year mean is centered):")
    for f in sorted((ROOT / run / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        yr = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6
        b = btm[(btm["year"] == yr) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = (e923[e923["year"] == yr].groupby("klass")["annual_mwh"]
                 .sum() / 1e6)
        for name, fam in (("GAS", gas), ("COAL", coal)):
            if yr >= 2025:
                m = sum(grid.get(c, 0.0) for c in fam)
                a = t930.get((yr, name.lower()), float("nan"))
                src = "930 grid-only"
            else:
                m = sum(grid.get(c, 0.0) + bt.get(c, 0.0) for c in fam)
                a = sum(bench.get(c, 0.0) for c in fam)
                src = "923 incl. BTM"
            pct = (m / a - 1) * 100
            tag = "PASS" if abs(pct) <= 2.5 else "FAIL"
            print(f"  {yr} {name:4s} {pct:+5.1f}%  {tag}  (vs {src})")


if __name__ == "__main__":
    main()
