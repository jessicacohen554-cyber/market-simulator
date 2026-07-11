"""Verify the combined-fossil reconcile design vs the current per-family one,
per ISO/year: does it fire, and what does scored CC_REGULAR / coal / gas become."""

import sys
import json
import gzip

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, ".")
import pandas as pd
import run_calibration_full as rcf
from market_sim.data.eia923 import load_monthly_generation
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.plant_taxonomy import classes_for_fuel930

OTHER_FOSSIL = "OTHER_FOSSIL"
gen = load_monthly_generation()
GAS = list(classes_for_fuel930("gas")) + [OTHER_FOSSIL]
COAL = list(classes_for_fuel930("coal"))
FRAC = 0.97


def foldin(cf, e930, iso):
    mob = float(cf.get("OTHER", 0)) + float(cf.get("biomass", 0))
    if "other" in e930:
        return max(0.0, mob - float(e930.get("other", 0)))
    return mob if iso == "CAISO" else 0.0


def recon_perfamily(cf, e930, iso):
    cf = dict(cf)
    for fuel, ks in (("gas", GAS), ("coal", COAL)):
        pres = [g for g in ks if g in cf]
        cur = sum(cf[g] for g in pres)
        tgt = float(e930.get(fuel, 0)) - (foldin(cf, e930, iso) if fuel == "gas" else 0)
        if tgt > 0 and cur > 0 and not (FRAC * tgt <= cur <= tgt / FRAC):
            s = tgt / cur
            for g in pres:
                cf[g] = cf[g] * s
    return cf


def recon_combined(cf, e930, iso):
    cf = dict(cf)
    pres = [g for g in GAS + COAL if g in cf]
    cur = sum(cf[g] for g in pres)
    tgt = float(e930.get("gas", 0)) + float(e930.get("coal", 0)) - foldin(cf, e930, iso)
    if tgt > 0 and cur > 0 and not (FRAC * tgt <= cur <= tgt / FRAC):
        s = tgt / cur
        for g in pres:
            cf[g] = cf[g] * s
    return cf


for iso in ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]:
    try:
        cfg = get_iso_config(iso)
        for yr in (2023, 2024, 2025):
            e923 = rcf._benchmark_eia923_frame(yr, gen, iso, None, {}, None)
            gbc = None if iso == "ERCOT" else rcf._fleet_group_by_code(iso, cfg, yr)
            btmf = rcf._btm_frame(
                yr,
                "P1",
                gen,
                btm_backfill_year=2024,
                campd_active=None,
                iso=iso,
                group_by_code=gbc,
            )
            btm = (
                btmf.groupby("klass")["btm_twh"].sum()
                if len(btmf)
                else pd.Series(dtype=float)
            )
            e = e923.groupby("klass")["annual_mwh"].sum() / 1e6
            # classFull (923 grid) = 923 - btm, per class
            cf = {
                k: float(e.get(k, 0)) - float(btm.get(k, 0))
                for k in set(e.index) | set(GAS) | set(COAL)
            }
            b = json.loads(
                gzip.open(f"frontend/data/backcast/bench/{iso}/{yr}.json.gz").read()
            )["bench"]
            e930 = {**b["e930"]}
            old = recon_perfamily(cf, e930, iso)
            new = recon_combined(cf, e930, iso)

            def fam(d, ks):
                return sum(d.get(k, 0) for k in ks if k in d)

            cc_old = old.get("CC_REGULAR", 0)
            cc_new = new.get("CC_REGULAR", 0)
            coal_old = fam(old, COAL)
            coal_new = fam(new, COAL)
            fired_old = abs(cc_old - cf.get("CC_REGULAR", 0)) > 0.05
            fired_new = abs(cc_new - cf.get("CC_REGULAR", 0)) > 0.05
            print(
                f"{iso:<6}{yr}  CC 923g {cf.get('CC_REGULAR', 0):6.1f}  old {cc_old:6.1f}  new {cc_new:6.1f} | coal 923g {fam(cf, COAL):6.1f} old {coal_old:6.1f} new {coal_new:6.1f} | fire old={fired_old} new={fired_new}"
            )
    except Exception as ex:
        print(iso, "ERR", ex)
