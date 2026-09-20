"""pjm-h14 phase 0e — what each solve year's OWN CAMPD says about PJM's coal
commitment shares, against the pooled 2023-2025 artifact the run actually uses.

Zero LP. The per-year tables are produced by the FROZEN deriver
``scripts/data/derive_thermal_tranches.py`` (unmodified, one ``--years <y>``
invocation per year), so nothing here re-derives or re-tunes a committed value:
it measures what the existing estimator says about years the committed artifact's
own derive window (2023-2025, identified in this session by re-running that window
and getting a BYTE-EQUAL key set) never saw.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
POOLED = ROOT / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
PERYEAR = Path("/tmp/claude-0/h14/tranches_PJM_{year}.csv")
BENCH = ROOT / "frontend/data/backcast/bench/PJM"
RUNS = {
    "t": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-touchpoint.js",
    "s": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-span.js",
}
DEFAULT_MR, DEFAULT_MC = 45.0, 5.0
YEARS = list(range(2020, 2026))


def load_run(path: Path) -> dict:
    import base64
    import re

    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', path.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def coal_rows(path: Path) -> pd.DataFrame:
    t = pd.read_csv(path)
    t = t[t["plant_group"].astype(str) == "COAL"].copy()
    t["plant_code"] = t["plant_code"].astype(str)
    return t.set_index("plant_code")


def main() -> None:
    pooled = coal_rows(POOLED)
    peryear = {y: coal_rows(Path(str(PERYEAR).format(year=y))) for y in YEARS}

    payloads: dict[int, dict] = {}
    for p in RUNS.values():
        for y, rec in load_run(p)["years"].items():
            payloads[int(y)] = rec

    print("### 1. COVERAGE: rows the pooled artifact has vs rows each YEAR's own CAMPD supports\n")
    rows = []
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        fleet = {k for k, b in bench.items() if b.get("group") == "COAL_BIT"}
        rows.append(dict(
            year=y, bench_coal_plants=len(fleet),
            covered_pooled=len(fleet & set(pooled.index)),
            covered_own_year=len(fleet & set(peryear[y].index)),
            gained=len(fleet & set(peryear[y].index) - set(pooled.index)),
            still_missing=len(fleet - set(peryear[y].index) - set(pooled.index)),
        ))
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n### 2. THE ASSERTED MUST-RUN LEVEL, three ways, for the plants the pooled file MISSES\n")
    print("    default = the hard-coded 45 % the run uses today "
          "(campd_bins._DEFAULT_TRANCHE_PCT_BY_GROUP['COAL'])\n"
          "    own-year = mustrun_online_pct the FROZEN deriver reads off that plant's own CAMPD that year\n")
    ledger = []
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        mp = payloads[y]["plants"]
        py = peryear[y]
        for k, b in bench.items():
            if b.get("group") != "COAL_BIT" or k in pooled.index:
                continue
            npl = float(b.get("npl") or 0.0)
            own = py.loc[k] if k in py.index else None
            ledger.append(dict(
                year=y, key=k, name=b.get("name", "?")[:24], npl=npl,
                default_mr=DEFAULT_MR,
                own_mr=float(own["mustrun_online_pct"]) if own is not None and not pd.isna(own["mustrun_online_pct"]) else np.nan,
                own_mc=float(own["committed_pct"]) if own is not None and not pd.isna(own["committed_pct"]) else np.nan,
                own_status=(own["status"] if own is not None else "ABSENT"),
                campd=float(b.get("c_ann") or 0.0),
                model=float((mp.get(k) or {}).get("m_ann") or 0.0),
            ))
    L = pd.DataFrame(ledger)
    L["delta"] = L["model"] - L["campd"]
    L["floor_default_TWh"] = L["default_mr"] / 100 * L["npl"] * 8760 / 1e6
    L["floor_own_TWh"] = L["own_mr"].fillna(0.0) / 100 * L["npl"] * 8760 / 1e6
    for y in YEARS:
        s = L[L["year"] == y].sort_values("delta", ascending=False)
        if not len(s):
            continue
        print(f"  --- {y}  ({len(s)} plants, {s['npl'].sum():.0f} MW, C1 Δ {s['delta'].sum():+.2f} TWh)")
        print(s[["name", "npl", "own_status", "default_mr", "own_mr", "own_mc",
                 "floor_default_TWh", "floor_own_TWh", "campd", "model", "delta"]]
              .head(10).to_string(index=False, float_format=lambda v: f"{v:8.2f}"))

    print("\n### 3. THE FOOTPRINT — asserted must-run block, pooled-artifact run vs own-year run\n")
    out = []
    for y in YEARS:
        s = L[L["year"] == y]
        out.append(dict(
            year=y, n_missing=len(s), MW=s["npl"].sum(),
            floor_today_TWh=s["floor_default_TWh"].sum(),
            floor_ownyear_TWh=s["floor_own_TWh"].sum(),
            release_TWh=s["floor_default_TWh"].sum() - s["floor_own_TWh"].sum(),
            measured_TWh=s["campd"].sum(), model_TWh=s["model"].sum(),
            C1_delta=s["delta"].sum(),
        ))
    print(pd.DataFrame(out).to_string(index=False, float_format=lambda v: f"{v:9.3f}"))

    print("\n### 4. THE COVERED COHORT — does its OWN-YEAR share differ from the pooled one?\n")
    print("    (this is the second, separable limb: 22 plants the artifact DOES cover, whose\n"
          "     pooled 2023-2025 shares are asserted on 2020-2022 as well)\n")
    cov = []
    for y in YEARS:
        py = peryear[y]
        both = [k for k in pooled.index if k in py.index]
        d_mr = (py.loc[both, "mustrun_online_pct"].astype(float)
                - pooled.loc[both, "mustrun_online_pct"].astype(float))
        d_mc = (py.loc[both, "committed_pct"].astype(float)
                - pooled.loc[both, "committed_pct"].astype(float))
        cov.append(dict(year=y, n=len(both),
                        mr_mean_delta=d_mr.mean(), mr_max_abs=d_mr.abs().max(),
                        mc_mean_delta=d_mc.mean(), mc_max_abs=d_mc.abs().max()))
    print(pd.DataFrame(cov).to_string(index=False, float_format=lambda v: f"{v:9.3f}"))

    print("\n### 5. RULE-17 STATEMENT — asserted always-on block vs the plant's WHOLE metered output\n")
    for y in (2020, 2021, 2022):
        s = L[(L["year"] == y) & (L["floor_default_TWh"] > L["campd"])].sort_values(
            "floor_default_TWh", ascending=False)
        tot_f, tot_c = s["floor_default_TWh"].sum(), s["campd"].sum()
        print(f"  {y}: {len(s)} uncovered plants assert {tot_f:.2f} TWh of must-run against "
              f"{tot_c:.2f} TWh of TOTAL measured output ({tot_f/max(tot_c,1e-9):.1f}x)")


if __name__ == "__main__":
    main()
