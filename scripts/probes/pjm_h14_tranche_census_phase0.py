"""pjm-h14 phase 0d — the COAL tranche-artifact COVERAGE census. Zero LP.

``data/raw/_processed-legacy/thermal_tranches_PJM.csv`` carries ONE pooled row per
``(plant_code, plant_group)`` with no ``year`` column, so the same measured
commitment shares are asserted for every solve year 2020-2025. A coal plant ABSENT
from it falls through to ``campd_bins._DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"]``
= ``(must_run 45 %, committed 5 %, peaking 2 %)`` of nameplate
(``campd_bins.py:2480-2484``).

This census answers, per year and per plant: which benchmarked COAL_BIT plants are
covered, which fall through, and what each cohort contributes to C1's miss.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
BENCH = ROOT / "frontend/data/backcast/bench/PJM"
RUNS = {
    "touchpoint": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-touchpoint.js",
    "span": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-span.js",
}
DEFAULT_MR, DEFAULT_MC, DEFAULT_PK = 45.0, 5.0, 2.0


def load_run(path: Path) -> dict:
    import base64
    import re

    t = path.read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', t)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def main() -> None:
    art = pd.read_csv(ART)
    coal_art = art[art["plant_group"].astype(str) == "COAL"].set_index(
        art[art["plant_group"].astype(str) == "COAL"]["plant_code"].astype(str)
    )
    covered = set(coal_art.index)

    payloads: dict[int, dict] = {}
    for p in RUNS.values():
        for y, rec in load_run(p)["years"].items():
            payloads[int(y)] = rec
    years = sorted(payloads)

    print("### 1. COVERAGE of the pooled tranche artifact against each year's benchmarked COAL_BIT fleet\n")
    detail: dict[int, pd.DataFrame] = {}
    for y in years:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        mp = payloads[y]["plants"]
        rows = []
        for key, b in bench.items():
            if b.get("group") != "COAL_BIT":
                continue
            m = mp.get(key, {})
            npl = float(b.get("npl") or 0.0)
            campd = float(b.get("c_ann") or 0.0)
            model = float(m.get("m_ann") or 0.0)
            rows.append(dict(
                key=key, name=b.get("name", "?")[:26], npl=npl,
                covered=key in covered,
                mr_pct=float(coal_art.loc[key, "mustrun_online_pct"]) if key in covered else DEFAULT_MR,
                mc_pct=float(coal_art.loc[key, "committed_pct"]) if key in covered else DEFAULT_MC,
                campd=campd, model=model, delta=model - campd,
                meas_cf=(campd * 1e6 / (npl * 8760)) if npl else np.nan,
                mod_cf=(model * 1e6 / (npl * 8760)) if npl else np.nan,
            ))
        detail[y] = pd.DataFrame(rows)

    summ = []
    for y in years:
        t = detail[y]
        for cov in (True, False):
            s = t[t["covered"] == cov]
            summ.append(dict(
                year=y, cohort="COVERED" if cov else "FALLBACK",
                n=len(s), MW=s["npl"].sum(),
                campd=s["campd"].sum(), model=s["model"].sum(), delta=s["delta"].sum(),
                mean_meas_cf=s["meas_cf"].mean(), mean_mod_cf=s["mod_cf"].mean(),
                mean_mr_pct=s["mr_pct"].mean(),
            ))
    print(pd.DataFrame(summ).to_string(index=False, float_format=lambda v: f"{v:9.3f}"))

    print("\n### 2. The FALLBACK cohort, named (plants absent from the artifact)\n")
    for y in (2020, 2021, 2022, 2025):
        t = detail[y]
        f = t[~t["covered"]].sort_values("delta", ascending=False)
        print(f"  --- {y}: {len(f)} plants, {f['npl'].sum():.0f} MW, Δ {f['delta'].sum():+.2f} TWh")
        print(f[["name", "npl", "campd", "model", "delta", "meas_cf", "mod_cf"]]
              .head(12).to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    print("\n### 3. The asserted must-run floor vs what the meter says the plant did\n")
    print("    floor_TWh = mr_pct/100 x npl x 8760 (the asserted ALWAYS-ON block, before the LP)\n")
    for y in years:
        t = detail[y].copy()
        t["floor_TWh"] = t["mr_pct"] / 100.0 * t["npl"] * 8760 / 1e6
        cov = t[t["covered"]]
        fb = t[~t["covered"]]
        over = t[t["floor_TWh"] > t["campd"]]
        print(f"  {y}: asserted must-run block  COVERED {cov['floor_TWh'].sum():7.2f} TWh  "
              f"FALLBACK {fb['floor_TWh'].sum():7.2f} TWh  | plants whose asserted floor EXCEEDS their "
              f"whole measured output: {len(over)} ({over['npl'].sum():.0f} MW, "
              f"floor {over['floor_TWh'].sum():.2f} vs measured {over['campd'].sum():.2f} TWh)")

    print("\n### 4. THE RULE-17 ROSTER — plants whose asserted must-run floor exceeds their ENTIRE metered output\n")
    for y in (2020, 2021, 2022, 2023, 2024, 2025):
        t = detail[y].copy()
        t["floor_TWh"] = t["mr_pct"] / 100.0 * t["npl"] * 8760 / 1e6
        o = t[t["floor_TWh"] > t["campd"]].sort_values("floor_TWh", ascending=False)
        if not len(o):
            print(f"  {y}: none")
            continue
        print(f"  --- {y}")
        print(o[["name", "npl", "covered", "mr_pct", "floor_TWh", "campd", "model", "delta"]]
              .to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    print("\n### 5. Artifact vintage check — pooled online_hours vs a single year\n")
    c = coal_art.copy()
    print(f"  COAL rows: {len(c)}   online_hours min {c['online_hours'].min():.0f} "
          f"max {c['online_hours'].max():.0f} median {c['online_hours'].median():.0f}")
    print(f"  8760 h = one year; {int((c['online_hours'] > 8760).sum())} of {len(c)} coal rows exceed one year "
          f"=> the artifact POOLS multiple years and carries NO year column.")


if __name__ == "__main__":
    main()
