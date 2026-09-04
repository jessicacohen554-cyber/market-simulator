"""nyiso-189 Step 0: the eGRID GEN-sheet steam-generator collapse census over EVERY NYISO CC.

Threshold-free tests, per (EIA plant, eGRID vintage), on eGRID's own GEN /
UNT / PLNT sheets (PREREG-nyiso189 §3, fixed before this runs):

  T1 (zero test)     an operating CA (steam) generator reports GENNTAN == 0 in
                     a vintage whose CT generators report GENNTAN > 0.
  T2 (share record)  ST / CT = sum(GENNTAN, PRMVR == CA) / sum(GENNTAN, PRMVR == CT)
                     per vintage — reported, never thresholded; the per-plant
                     min / max across vintages is the LOYO-style record.
  T3 (CT-heat identity)  PLHTIAN / sum(GENNTAN, CT) per vintage — the heat per
                     CT-generator MWh; block HR = that / (1 + ST/CT).
  T4 (applied-vintage rate)  the fleet's applied PLHTRT (eGRID 2023) vs the
                     block HR implied at the plant's own median ST/CT over its
                     T1-clean vintages, and vs the EIA-860 nameplate ratio.

Population: every EIA plant the NYISO fleet carries a CC_REGULAR or CC_CHP
generator for (load_fleet_from_csv), that eGRID files a CA generator for.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUT = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else REPO / "results" / "calibration" / "_nyiso189_gen_collapse_census"
)
OUT.mkdir(parents=True, exist_ok=True)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"))
cc_plants: dict[int, str] = {}
for g in fleet:
    if str(getattr(g, "plant_group", "")) in ("CC_REGULAR", "CC_CHP") and g.plant_code:
        cc_plants[int(g.plant_code)] = getattr(g, "plant_name", "") or getattr(
            g, "name", ""
        )
applied_hr = {}
for g in fleet:
    if int(g.plant_code or 0) in cc_plants:
        applied_hr.setdefault(int(g.plant_code), []).append(float(g.heat_rate))

rows = []
for f in sorted(glob.glob(str(REPO / "data/raw/fleet-egrid/*.xlsx"))):
    digits = "".join(c for c in Path(f).name if c.isdigit())[:4]
    year = int(digits)
    xl = pd.ExcelFile(f)
    gen_sheet = [s for s in xl.sheet_names if str(s).upper().startswith("GEN")][0]
    plnt_sheet = [s for s in xl.sheet_names if str(s).upper().startswith("PLNT")][0]
    gen = pd.read_excel(
        f,
        sheet_name=gen_sheet,
        header=1,
        usecols=["ORISPL", "GENID", "PRMVR", "GENNTAN", "NAMEPCAP", "GENSTAT"]
        if True
        else None,
    )
    plnt = pd.read_excel(
        f,
        sheet_name=plnt_sheet,
        header=1,
        usecols=["ORISPL", "PLHTIAN", "PLNGENAN", "PLHTRT"],
    )
    plnt = plnt.set_index(plnt["ORISPL"].astype(int))
    gen = gen[gen["ORISPL"].isin(cc_plants)]
    for oris, g in gen.groupby("ORISPL"):
        oris = int(oris)
        op = (
            g[g["GENSTAT"].astype(str).str.upper().str.strip() == "OP"]
            if "GENSTAT" in g
            else g
        )
        ct = op[op["PRMVR"].astype(str).str.upper() == "CT"]
        ca = op[op["PRMVR"].astype(str).str.upper() == "CA"]
        if ca.empty:
            continue  # single-shaft (CS) or no filed steam generator: outside the test's object
        ct_net = float(pd.to_numeric(ct["GENNTAN"], errors="coerce").fillna(0).sum())
        ca_net = float(pd.to_numeric(ca["GENNTAN"], errors="coerce").fillna(0).sum())
        ca_zero = bool(
            ct_net > 0
            and (pd.to_numeric(ca["GENNTAN"], errors="coerce").fillna(0) == 0).any()
        )
        htian = float(plnt["PLHTIAN"].get(oris, np.nan))
        plhtrt = float(plnt["PLHTRT"].get(oris, np.nan)) / 1e3
        rows.append(
            {
                "plant": oris,
                "name": cc_plants[oris],
                "vintage": year,
                "n_ct": len(ct),
                "n_ca": len(ca),
                "ct_namepcap": float(
                    pd.to_numeric(ct["NAMEPCAP"], errors="coerce").sum()
                ),
                "ca_namepcap": float(
                    pd.to_numeric(ca["NAMEPCAP"], errors="coerce").sum()
                ),
                "ct_net_mwh": ct_net,
                "ca_net_mwh": ca_net,
                "st_ct_ratio": (ca_net / ct_net) if ct_net > 0 else np.nan,
                "T1_ca_zero_with_ct_running": ca_zero,
                "plhtian": htian,
                "plhtrt": plhtrt,
                "heat_per_ct_mwh": (htian / ct_net) if ct_net > 0 else np.nan,
            }
        )
df = pd.DataFrame(rows).sort_values(["plant", "vintage"])
df.to_csv(OUT / "gen_collapse_census_rows.csv", index=False)

# per-plant summary
summ = []
for p, g in df.groupby("plant"):
    clean = g[~g.T1_ca_zero_with_ct_running & g.st_ct_ratio.notna()]
    med = float(clean.st_ct_ratio.median()) if len(clean) else np.nan
    v23 = g[g.vintage == 2023]
    hp23 = float(v23.heat_per_ct_mwh.iloc[0]) if len(v23) else np.nan
    nameplate_ratio = (
        float(g.ca_namepcap.iloc[-1] / g.ct_namepcap.iloc[-1])
        if g.ct_namepcap.iloc[-1] > 0
        else np.nan
    )
    summ.append(
        {
            "plant": p,
            "name": g.name.iloc[0],
            "vintages": len(g),
            "T1_fires_in": ";".join(
                str(int(v)) for v in g[g.T1_ca_zero_with_ct_running].vintage
            ),
            "st_ct_min": round(float(g.st_ct_ratio.min()), 3),
            "st_ct_max": round(float(g.st_ct_ratio.max()), 3),
            "st_ct_median_T1clean": round(med, 3) if med == med else np.nan,
            "nameplate_ca_over_ct": round(nameplate_ratio, 3)
            if nameplate_ratio == nameplate_ratio
            else np.nan,
            "heat_per_ct_mwh_min": round(float(g.heat_per_ct_mwh.min()), 2),
            "heat_per_ct_mwh_max": round(float(g.heat_per_ct_mwh.max()), 2),
            "plhtrt_2023": round(float(v23.plhtrt.iloc[0]), 3) if len(v23) else np.nan,
            "applied_hr_fleet": round(float(np.median(applied_hr.get(p, [np.nan]))), 3),
            "block_hr_2023_at_own_share": round(hp23 / (1 + med), 3)
            if (med == med and hp23 == hp23)
            else np.nan,
            "block_hr_2023_at_nameplate_share": round(hp23 / (1 + nameplate_ratio), 3)
            if (nameplate_ratio == nameplate_ratio and hp23 == hp23)
            else np.nan,
        }
    )
s = pd.DataFrame(summ).sort_values("plant")
s.to_csv(OUT / "gen_collapse_census_summary.csv", index=False)
pd.set_option("display.width", 250)
print(s.to_string(index=False))
print(
    "\nT1 fires at:",
    s[s.T1_fires_in != ""][["plant", "name", "T1_fires_in"]].to_string(index=False),
)
