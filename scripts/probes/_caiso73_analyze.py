"""caiso-73 outcome extraction: pre-registered directions vs solved bundles.

Reads the caiso-73 main (and optionally ablation) bundle and prints, per year
(2023-2025): CT_PEAKER / CC_REGULAR TWh, LA_BASIN mean LMP, hours > $200
(zonal max), summer evening (h17-22) and deep-evening (h19-22) corridor
import means, and the h14 midday import mean — the quantities the probe
docstring pre-registers (scripts/probes/_caiso73_firm_shape_ab.py).

Usage: python scripts/probes/_caiso73_analyze.py [bundle_dir]
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else ROOT / "results" / "calibration" / "caiso73_firm_shape"
)


def main() -> None:
    for year in (2023, 2024, 2025):
        p = RUN / "dispatch" / f"{year}_P1.parquet"
        if not p.exists():
            print(f"{year}: no dispatch parquet yet")
            continue
        disp = pd.read_parquet(p)
        disp["hod"] = disp["hour"] % 24
        ct = disp[disp["klass"] == "CT_PEAKER"]["mw"].sum() / 1e6
        cc = disp[disp["klass"] == "CC_REGULAR"]["mw"].sum() / 1e6
        print(f"\n===== {year} =====")
        print(f"CT_PEAKER {ct:.2f} TWh | CC_REGULAR {cc:.2f} TWh")

        prices = pd.read_parquet(RUN / "system.parquet")
        pr = prices[(prices["year"] == year) & (prices["pass"] == "P1")]
        la = pr[pr["zone"] == "LA_BASIN"]["price"].mean()
        zmax = pr.groupby("hour")["price"].max()
        print(f"LA_BASIN mean LMP {la:.2f} | hrs>$200 (zonal max) {(zmax > 200).sum()}")

        flows = pd.read_parquet(RUN / "flows.parquet")
        fl = flows[(flows["year"] == year) & (flows["pass"] == "P1")]
        fl = fl.assign(hod=fl["hour"] % 24)
        imp = fl[fl["from_zone"].isin(["WECC_PNW", "WECC_DSW"])]
        tot = imp.groupby(["hour", "hod"])["mw"].sum().reset_index()
        for label, hods in (
            ("h14", [14]),
            ("h17-22", range(17, 23)),
            ("h19-22", range(19, 23)),
        ):
            sel = tot[tot["hod"].isin(list(hods))]["mw"].mean()
            print(f"corridor import mean {label}: {sel:.0f} MW")
        by_corr = (
            imp[imp["hod"].isin(range(19, 23))]
            .groupby("from_zone")["mw"]
            .mean()
            .round(0)
        )
        print("deep-evening (h19-22) by corridor:", dict(by_corr))


if __name__ == "__main__":
    main()
