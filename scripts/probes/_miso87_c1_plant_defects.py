"""miso-87 probe — localize the C1 CC_REGULAR FAIL on the miso-86 keeper.

Reproduces, from COMMITTED artifacts only (no LP re-solve), the evidence that
the keeper's C1 ``CC_REGULAR 2023 -8.62 TWh`` band exceedance is dominated by
two PER-PLANT input defects in the derived bin-assignment table
``data/raw/_processed-legacy/bin_assignments_MISO.csv`` -- not by the offer
bands, the committed/economic tranche split, or class availability:

* **Riverside Energy Center (ORIS 55641, MISO-East)** carries
  ``Plant_Avg_HR_MMBtu_MWh = 14.96`` -- roughly 2x the physical heat rate of
  its own 2004 F-class combined-cycle technology, and 2.1-2.4x every other
  MISO CC in the same table. At that heat rate the plant's offer sits above
  most of the MISO coal fleet, so the LP never commits it: model CF 0.01 /
  0.05 / 0.01 against an EIA-923 actual CF of 0.60 / 0.57 / 0.56.
* **Cottonwood Energy Company LP (ORIS 55358, MISO-South)** carries
  ``Nameplate_MW = 580.4`` against an EIA-860 operable nameplate of 1433.6 MW
  (40.5 %). The truncation is self-refuting inside the model's own inputs: the
  benchmark's CAMPD series for the plant records MORE energy in 2023 than
  580.4 MW can physically produce over 8760 h.

Both are read straight off measured records (EIA-860 nameplate, EIA-923 net
generation, the plant's own technology vintage), so calling them defects never
appeals to the price or volume residual -- CLAUDE.md rules 1/10 are not in
play, and rule 11 (prefer accurate data over an estimate) applies directly.

The systemic gap both slip through: ``cc_capacity_reconcile_<ISO>.csv`` is a
ONE-SIDED guard. It trims CC plants whose CAMPD-derived capacity EXCEEDS the
EIA-860 trusted bound (7 MISO plants in 2023) and has no counterpart for
capacity far BELOW nameplate; there is no plausibility guard on the derived
heat rate at all.

Usage:
    python scripts/probes/_miso87_c1_plant_defects.py
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

RUN_ID = "2026-07-24-miso-86-netrev-margin"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
RUN_JS = REPO / f"frontend/data/backcast/runs/{RUN_ID}.js"
BINS = RAW_DATA_DIR / "_processed-legacy/bin_assignments_MISO.csv"
YEARS = (2023, 2024, 2025)

# A combined-cycle heat rate above this is not physically attainable by any
# CC configuration in service (best-in-class H frame ~6.3, oldest MISO F/GE
# 7000-series frames ~7.7 HHV). Used ONLY to flag rows for inspection.
CC_HR_IMPLAUSIBLE_MMBTU_MWH = 9.0
# Flag a CC whose derived bin capacity falls below this share of its EIA-860
# operable nameplate. The existing reconciler guards the other direction only.
CC_CAP_SHORTFALL_RATIO = 0.75


def _run_payload() -> dict:
    """Return the committed run payload for :data:`RUN_ID`, decoded."""
    text = RUN_JS.read_text()
    blob = re.search(r'"(H4sI[^"]+)"', text)
    if blob is None:  # pragma: no cover - committed payload is always present
        raise SystemExit(f"no gzip payload in {RUN_JS}")
    return json.loads(gzip.decompress(base64.b64decode(blob.group(1))))


def _eia860_cc_nameplate() -> pd.Series:
    """Return EIA-860 operable NGCC nameplate MW per plant code."""
    gen = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    gen["cap"] = pd.to_numeric(gen["Nameplate Capacity (MW)"], errors="coerce")
    ngcc = gen[gen["Technology"] == "Natural Gas Fired Combined Cycle"]
    return ngcc.groupby("Plant Code")["cap"].sum()


def per_plant_gap() -> pd.DataFrame:
    """Return per-plant model-vs-actual CC_REGULAR energy for 2023-2025."""
    payload = _run_payload()
    rows: dict[tuple[str, str, str], dict] = {}
    for year in YEARS:
        with gzip.open(BENCH / f"{year}.json.gz") as fh:
            plants = json.load(fh)["bench"]["plants"]
        model = payload["years"][str(year)]["plants"]
        for code, meta in plants.items():
            if meta["group"] != "CC_REGULAR":
                continue
            key = (code, meta["name"], meta["zone"])
            mdl = float((model.get(code) or {}).get("m_ann", 0.0))
            act = float(meta["e_ann"]) * (1.0 - float(meta.get("btm", 0.0)))
            cap = float(meta["npl"]) or 1.0
            rec = rows.setdefault(key, {"cap_mw": cap})
            rec[f"mdl_{year}"] = mdl
            rec[f"act_{year}"] = act
            rec[f"cf_m_{year}"] = mdl * 1e6 / (cap * 8760.0)
            rec[f"cf_a_{year}"] = act * 1e6 / (cap * 8760.0)
    out = pd.DataFrame(
        [{"plant_code": k[0], "plant_name": k[1], "zone": k[2], **v} for k, v in rows.items()]
    )
    out["gap_3yr"] = sum(
        out.get(f"mdl_{y}", 0.0) - out.get(f"act_{y}", 0.0) for y in YEARS
    )
    return out.sort_values("gap_3yr")


def main() -> None:
    """Print the C1 localization evidence."""
    gap = per_plant_gap()
    print("=" * 78)
    print("miso-87 / C1 CC_REGULAR localization  (keeper %s)" % RUN_ID)
    print("=" * 78)
    print("\n-- worst 6 plants by 2023-2025 model-minus-actual energy (TWh) --")
    head = f"{'plant':30s}{'MW':>6s}"
    for year in YEARS:
        head += f" |{year} CFm  CFa   dTWh"
    print(head)
    for _, r in gap.head(6).iterrows():
        line = f"{r.plant_name[:28]:28s}{r.cap_mw:8.0f}"
        for year in YEARS:
            line += (
                f" | {r[f'cf_m_{year}']:.2f} {r[f'cf_a_{year}']:.2f}"
                f" {r[f'mdl_{year}'] - r[f'act_{year}']:+6.2f}"
            )
        print(line + f"  [{r.zone}] 3yr {r.gap_3yr:+.2f}")
    worst2 = gap.head(2).gap_3yr.sum()
    print(
        f"\n  two worst plants = {worst2:+.2f} TWh over three years "
        f"({worst2 / 3:+.2f} TWh/yr) against a C1 band of +/-8.0 TWh."
    )

    bins = pd.read_csv(BINS)
    cc = bins[bins.Plant_Group == "CC_REGULAR"].copy()
    nameplate = _eia860_cc_nameplate()
    cc["eia860_mw"] = cc.Plant_Code.map(nameplate)
    cc["cap_ratio"] = cc.Nameplate_MW / cc.eia860_mw

    print("\n-- defect 1: implausible derived heat rate (CC_REGULAR) --")
    hr_bad = cc[cc.Plant_Avg_HR_MMBtu_MWh > CC_HR_IMPLAUSIBLE_MMBTU_MWH]
    print(
        hr_bad[["Plant_Code", "Plant_Name", "Zone", "Nameplate_MW", "Plant_Avg_HR_MMBtu_MWh"]]
        .sort_values("Plant_Avg_HR_MMBtu_MWh", ascending=False)
        .to_string(index=False)
    )
    ok = cc[cc.Plant_Avg_HR_MMBtu_MWh <= CC_HR_IMPLAUSIBLE_MMBTU_MWH].Plant_Avg_HR_MMBtu_MWh
    print(
        f"  rest of the MISO CC fleet: min {ok.min():.2f}  median {ok.median():.2f}"
        f"  max {ok.max():.2f} MMBtu/MWh"
    )

    print("\n-- defect 2: derived capacity far below EIA-860 nameplate (>400 MW) --")
    cap_bad = cc[(cc.eia860_mw > 400) & (cc.cap_ratio < CC_CAP_SHORTFALL_RATIO)]
    print(
        cap_bad[["Plant_Code", "Plant_Name", "Zone", "Nameplate_MW", "eia860_mw", "cap_ratio"]]
        .round(3)
        .to_string(index=False)
    )

    print("\n-- Cottonwood self-refutation (model input vs model capacity) --")
    with gzip.open(BENCH / "2023.json.gz") as fh:
        cw = json.load(fh)["bench"]["plants"]["55358"]
    cap = float(cc[cc.Plant_Code == 55358].Nameplate_MW.iloc[0])
    print(
        f"  bin capacity {cap:.1f} MW -> max attainable {cap * 8760 / 1e6:.3f} TWh/yr;"
        f"  benchmark CAMPD series for the plant records {cw['c_ann']:.3f} TWh in 2023."
    )
    print("  the model's own measured input exceeds what its capacity for the plant allows.")


if __name__ == "__main__":
    main()
