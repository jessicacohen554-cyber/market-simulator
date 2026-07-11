"""Sweep the plant-level group map (drives CAMPD backfill + per-plant displays)
for mixed-fuel plants bucketed wholly to one class. Two patterns:
  - coal+gas at one plant (WA Parish)
  - CC+CT at one plant (Doswell/Linden)
Report per-ISO the TWh that the single-bucket map mis-assigns vs the row-level
EIA-923 prime-mover split (the correct actual)."""

import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, ".")
import run_calibration_full as rcf
from market_sim.data.eia923 import load_monthly_generation
from market_sim.config.iso_configs import get_iso_config

gen = load_monthly_generation()


def group_map(iso, cfg, yr):
    if iso == "ERCOT":
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins

        b = load_campd_bins(ScenarioConfig().campd_bins_path)
        return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"]))
    return rcf._fleet_group_by_code(iso, cfg, yr)


COAL = {"COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL"}
GAS = {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"}


def fam(k):
    return "coal" if k in COAL else ("gas" if k in GAS else "other")


YR = 2024
for iso in ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]:
    try:
        cfg = get_iso_config(iso)
        ids = rcf._iso_plant_ids(iso)
        e923 = rcf._benchmark_eia923_frame(YR, gen, iso, None, {}, None)
        gbc = group_map(iso, cfg, YR)
        bp = e923.groupby(["plant_id", "klass"])["annual_mwh"].sum() / 1e6
        crossfuel = []
        crossccct = []
        for pid in e923["plant_id"].unique():
            if pid not in ids:
                continue
            if pid not in bp.index.get_level_values(0):
                continue
            ks = bp.loc[pid]
            bucket = str(gbc.get(int(pid), "?"))
            # material classes (>0.1 TWh)
            mats = {k: float(v) for k, v in ks.items() if v > 0.1}
            if len(mats) < 2:
                continue
            fams = {fam(k) for k in mats}
            # coal+gas cross
            if "coal" in fams and "gas" in fams:
                # energy in the family the bucket does NOT belong to
                bfam = fam(bucket)
                mis = sum(
                    v
                    for k, v in mats.items()
                    if fam(k) != bfam and fam(k) in ("coal", "gas")
                )
                crossfuel.append((int(pid), bucket, mis, dict(mats)))
            # CC+CT cross (both gas but different class, bucket is single)
            elif fams == {"gas"} and len({k for k in mats}) > 1:
                mis = sum(v for k, v in mats.items() if k != bucket)
                if mis > 0.1:
                    crossccct.append((int(pid), bucket, mis, dict(mats)))
        tf = sum(x[2] for x in crossfuel)
        tc = sum(x[2] for x in crossccct)
        print(
            f"=== {iso} {YR}: coal<->gas mis-bucket {tf:.2f} TWh ({len(crossfuel)} plants); CC<->CT mis-bucket {tc:.2f} TWh ({len(crossccct)} plants)"
        )
        for pid, bk, mis, mats in sorted(crossfuel, key=lambda x: -x[2])[:4]:
            print(f"    coal/gas p{pid} bucket={bk} mis={mis:.2f}  {mats}")
        for pid, bk, mis, mats in sorted(crossccct, key=lambda x: -x[2])[:4]:
            print(f"    CC/CT   p{pid} bucket={bk} mis={mis:.2f}  {mats}")
    except Exception as ex:
        print(iso, "ERR", ex)
