"""Session helper: score a bundle against the size-aware bar vs run 85.

Usage: python scripts/_session_score.py <bundle> [<base bundle>=run85_coal_soft]

GRID-DELIVERED basis (2026-06-14, user directive): the gate judges what the LP
actually dispatches to the grid against what actually reached the grid — model
= the grid LP dispatch (NO behind-the-meter CHP add-back), actual = EIA-923
whole-plant MINUS the per-class BTM host supply (= grid-delivered generation by
class). The BTM host steam is held out of the LP, so crediting the model for it
would score generation the model never optimized; gating grid-vs-grid removes
that. (The absolute miss is identical to the old whole-plant basis — the BTM
cancels — but the percentages are now honest grid-delivered errors.)

Prints the [3b]-style class table with TWh + %, the size-aware pass/fail
per class-year (>=20 TWh classes +/-5%, <20 TWh +/-1 TWh abs, CT_CHP
excluded), the in-scope fail count vs the base, the 2024 TWh ledger
(who gave/took vs the base), and the Martin Lake / Limestone plant guard.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
CLASSES = [
    "CC_REGULAR",
    "CC_CHP",
    "COAL_PRB",
    "ST_GAS",
    "COAL_LIGNITE",
    "CT_PEAKER",
    "CT_CHP",
]
GUARD_PLANTS = {6146: "Martin Lake", 298: "Limestone"}


def class_table(run: str) -> pd.DataFrame:
    d = ROOT / run
    e923 = pd.read_parquet(bundle_input_path(d, "eia923"))
    btm = pd.read_parquet(d / "btm.parquet")
    rows = []
    for f in sorted((d / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6
        b = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = e923[e923["year"] == year].groupby("klass")["annual_mwh"].sum() / 1e6
        # System grid-delivered totals for the 2026-06-15 universal class gate:
        # model = Σ grid-LP over every class; actual = Σ (EIA-923 − BTM). (The
        # authoritative gate, scripts/calibration_verdict.py, takes non-fossil
        # nuclear/wind/solar from EIA-930; this diagnostic stays on the 923 basis
        # it already loads — a sub-percent difference in the system total.)
        m_tot = float(grid.sum())
        a_tot = float(bench.sum()) - sum(bt.values())
        for cls in CLASSES:
            # Grid-delivered: model = grid LP only; actual = 923 whole-plant
            # minus the class's BTM host supply.
            m = grid.get(cls, 0.0)
            a = bench.get(cls, 0.0) - bt.get(cls, 0.0)
            rows.append(
                {
                    "year": year,
                    "class": cls,
                    "model": m,
                    "bench": a,
                    "m_tot": m_tot,
                    "a_tot": a_tot,
                }
            )
    return pd.DataFrame(rows)


# C1 fuel-mix — the universal class gate (matches
# calibration_verdict.score_fuelmix and the run explorer's classInTol,
# docs/codebase-site/backcast-runs.html): a class
# passes iff BOTH its grid-delivered volume miss is within min(2.0% of ISO annual
# generation, 8 TWh) AND its share of total generation is within 3.0 pp of actual.
# (2026-07-02 rubric re-balance: loosened from 1.0%/5 TWh/1.5 pp — must stay in
# lockstep with calibration_verdict.FUELMIX_* constants.)
VOL_GEN_FRAC = 0.02
VOL_CAP_TWH = 8.0
SHARE_PP = 3.0


def judge(row) -> str:
    if row["class"] == "CT_CHP":
        return "excl"
    vol_ok = abs(row["model"] - row["bench"]) <= min(
        VOL_GEN_FRAC * row["a_tot"], VOL_CAP_TWH
    )
    share_pp = 100.0 * row["model"] / row["m_tot"] - 100.0 * row["bench"] / row["a_tot"]
    share_ok = abs(share_pp) <= SHARE_PP
    return "PASS" if vol_ok and share_ok else "FAIL"


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
        print(
            s[
                [
                    "class",
                    "model",
                    "bench",
                    "pct",
                    "dTWh",
                    "verdict",
                    "base_pct",
                    "vs_base_TWh",
                ]
            ].to_string(index=False)
        )
    fails = t[t["verdict"] == "FAIL"]
    base_t = class_table(base)
    base_t["model"], base_t["bench"] = base_t["model"], base_t["bench"]
    base_t["verdict"] = base_t.apply(judge, axis=1)
    print(
        f"\nin-scope fails: {run}={len(fails)}  "
        f"{base}={len(base_t[base_t['verdict'] == 'FAIL'])}"
    )
    if len(fails):
        print(fails[["year", "class", "pct", "dTWh"]].round(2).to_string(index=False))
    led = t[t["year"] == 2024].copy()
    led = led[led["vs_base_TWh"].abs() > 0.05]
    print(f"\n2024 ledger vs {base} (TWh):")
    print(led[["class", "vs_base_TWh"]].round(2).to_string(index=False))
    fit = pd.read_parquet(ROOT / run / "plant_hourly_fit.parquet")
    g = fit[fit["plant_code"].isin(GUARD_PLANTS)].copy()
    g["plant"] = g["plant_code"].map(GUARD_PLANTS)
    g["model-campd_GWh"] = (g["model_gwh"] - g["campd_gwh"]).round(0)
    print("\nplant guard (keep < ~+1000 GWh):")
    print(
        g[["year", "plant", "model_gwh", "campd_gwh", "model-campd_GWh"]].to_string(
            index=False
        )
    )
    gas = {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"}
    coal = {"COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL"}
    e923 = pd.read_parquet(bundle_input_path(ROOT / run, "eia923"))
    e930 = pd.read_parquet(bundle_input_path(ROOT / run, "eia930"))
    t930 = e930.groupby(["year", "series"])["mw"].sum() / 1e6
    btm = pd.read_parquet(ROOT / run / "btm.parquet")
    print(
        "\nfuel split gate (GRID-DELIVERED: gas and coal grid totals within"
        " +/-2.5% per year; model = grid LP, actual = EIA-923 whole-plant"
        " minus the per-class BTM host supply. EIA-930 grid totals are shown"
        " alongside as the independent grid check. solar/wind sit outside"
        " this gate. PRB year-spread inside +/-5% is accepted when its"
        " multi-year mean is centered):"
    )
    for f in sorted((ROOT / run / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        yr = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6
        b = btm[(btm["year"] == yr) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = e923[e923["year"] == yr].groupby("klass")["annual_mwh"].sum() / 1e6
        for name, fam in (("GAS", gas), ("COAL", coal)):
            m = sum(grid.get(c, 0.0) for c in fam)
            a930 = t930.get((yr, name.lower()), float("nan"))
            if yr >= 2025:
                # 2025 EIA-923 is the incomplete monthly-survey vintage, so the
                # grid-delivered actual comes from EIA-930 (itself grid-side);
                # 923-BTM is shown as the secondary reference.
                a = a930
                a_alt = sum(bench.get(c, 0.0) - bt.get(c, 0.0) for c in fam)
                src, alt = "930 grid", "923-BTM"
            else:
                a = sum(bench.get(c, 0.0) - bt.get(c, 0.0) for c in fam)
                a_alt = a930
                src, alt = "923-BTM grid", "930 grid"
            pct = (m / a - 1) * 100 if a == a and a else float("nan")
            tag = "PASS" if abs(pct) <= 2.5 else "FAIL"
            d_alt = (m / a_alt - 1) * 100 if a_alt == a_alt and a_alt else float("nan")
            print(
                f"  {yr} {name:4s} {pct:+5.1f}%  {tag}  (vs {src};"
                f" vs {alt} {d_alt:+.1f}%)"
            )


if __name__ == "__main__":
    main()
