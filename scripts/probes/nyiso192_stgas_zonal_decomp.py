"""nyiso-192 PHASE 0 (NO LP) — the ST_GAS zonal placement error, decomposed to an owner.

nyiso-191 §6 item 3 measured the pattern (NYC over, Long Island / Capital-Hudson
under, sign stable in every zone and year) and named three candidate carriers
without choosing: zonal price formation, the Long Island import limit, and the
zonal delivered-gas basis — with unit offer cost as the fourth. This probe
separates them on committed bytes and the no-LP fleet reconstruction:

* **Offer anatomy** per downstate steam plant: capacity-weighted heat rate,
  delivered fuel, VOM and the residual (CO2 + margin) of the P0 offer, by zone.
* **Price formation**: model vs actual zonal RT price means and the downstate
  spreads (NYC-CH, LI-CH, LI-NYC).
* **In-merit ladder** for the committed tranche of each plant — S0 model offer
  vs model price (as solved); S1 model offer vs ACTUAL price (isolates price
  formation); S2 model offer with NYC on the Iroquois reference basis vs model
  price (isolates the zonal gas basis) — against each plant's measured
  online share.
* **Ex-ante arm**: the one lever the decomposition points at — the NYC steam
  fleet on the LDC-delivered daily index the CT_PEAKER leg already uses
  (``nyiso_downstate_ct_gas_daily``) — evaluated WITHOUT a solve: the shift,
  the resulting in-merit shares, and the class energy the reliability floor
  would hold regardless (the rule-20 forced-energy consequence).

Nothing here is adopted or rejected; the pre-registration fixes what follows.
"""

from __future__ import annotations

import pandas as pd

from _nyiso192_common import (
    KEEPER_ID,
    YEARS,
    actual_zone_price,
    bench_plants,
    keeper_payload,
    model_zone_price,
    plant_series,
    reconstructed,
    write_json,
)

DOWNSTATE = ("NYC", "Long_Island", "Capital_Hudson")
REFERENCE_ZONE = (
    "Capital_Hudson"  # the Iroquois Z2 reference of nyiso_zonal_gas_offsets
)
STEAM = {
    2500: "Ravenswood",
    2490: "Arthur Kill",
    8906: "Astoria",
    2516: "Northport",
    2511: "E F Barrett",
    2517: "Port Jefferson",
    2625: "Bowline Point",
    8006: "Roseton",
    2480: "Danskammer",
}
ON_MW = 1.0


def main() -> int:
    run = keeper_payload()
    rec = {
        "session": "nyiso-192",
        "object": "2 — ST_GAS zonal placement decomposition (phase 0, no LP)",
        "run": KEEPER_ID,
        "by_year": {},
    }
    for year in YEARS:
        rc = reconstructed(year)
        st = rc["static"]
        stg = st[st.plant_group == "ST_GAS"].copy()
        stg["tranche"] = stg.unit_id.str.rsplit("_", n=1).str[-1]
        stg["mc_mean"] = rc["mc"][stg.index.to_numpy()].mean(1)
        stg["fuel_mean"] = rc["fuel"][stg.index.to_numpy()].mean(1)
        stg["other"] = stg.mc_mean - stg.heat_rate * stg.fuel_mean - stg.vom
        anatomy = []
        for (code, zone), x in stg.groupby(["plant_code", "zone"]):
            w = x.pmax / x.pmax.sum()
            anatomy.append(
                {
                    "plant_code": int(code),
                    "name": STEAM.get(int(code), ""),
                    "zone": zone,
                    "cap_mw": round(float(x.pmax.sum()), 1),
                    "hr_cap_weighted": round(float((x.heat_rate * w).sum()), 3),
                    "hr_committed": round(
                        float(x.loc[x.tranche == "committed", "heat_rate"].mean()), 3
                    ),
                    "fuel_usd_mmbtu": round(float(x.fuel_mean.mean()), 3),
                    "vom": round(float(x.vom.mean()), 2),
                    "co2_plus_margin": round(float((x.other * w).sum()), 2),
                    "mc_cap_weighted": round(float((x.mc_mean * w).sum()), 2),
                    "mc_committed": round(
                        float(x.loc[x.tranche == "committed", "mc_mean"].mean()), 2
                    ),
                }
            )
        anatomy = sorted(anatomy, key=lambda r: r["mc_cap_weighted"])
        fuel_by_zone = {
            z: float(stg[stg.zone == z].fuel_mean.mean()) for z in DOWNSTATE
        }
        ct_nyc = st[
            (st.zone == "NYC") & (st.plant_group == "CT_PEAKER")
        ].index.to_numpy()
        ct_fuel_nyc = rc["fuel"][ct_nyc].mean(
            0
        )  # the LDC-delivered daily index, hourly

        mp = model_zone_price(year)
        ap = actual_zone_price(year)
        price = {"zones": {}, "spreads": {}}
        for z in (
            "Upstate_West",
            "Capital_Hudson",
            "Lower_Hudson",
            "NYC",
            "Long_Island",
        ):
            price["zones"][z] = {
                "actual_mean": round(float(ap[z].mean()), 2),
                "model_mean": round(float(mp[z].mean()), 2),
                "model_minus_actual": round(float(mp[z].mean() - ap[z].mean()), 2),
            }
        for a, b in (
            ("NYC", "Capital_Hudson"),
            ("Long_Island", "Capital_Hudson"),
            ("Long_Island", "NYC"),
            ("NYC", "Upstate_West"),
        ):
            price["spreads"][f"{a}-{b}"] = {
                "actual": round(float(ap[a].mean() - ap[b].mean()), 2),
                "model": round(float(mp[a].mean() - mp[b].mean()), 2),
            }

        bench = bench_plants(year)
        plants = run["years"][str(year)]["plants"]
        ladder, arm = [], []
        floor_nyc = rc["min_gen"][stg.index[stg.zone == "NYC"].to_numpy()].sum(0)
        for code, name in STEAM.items():
            key = f"{code}:ST_GAS" if f"{code}:ST_GAS" in plants else str(code)
            if key not in plants:
                continue
            x = stg[(stg.plant_code == code) & (stg.tranche == "committed")]
            if x.empty:
                continue
            i = int(x.index[0])
            zone = x.zone.iloc[0]
            hr = float(x.heat_rate.iloc[0])
            mc = rc["mc"][i]
            mpz, apz = mp[zone].to_numpy(), ap[zone].to_numpy()
            s2 = mc + (fuel_by_zone[REFERENCE_ZONE] - fuel_by_zone[zone]) * hr
            m, c = plant_series(run, bench, key, year)
            ladder.append(
                {
                    "plant_code": code,
                    "name": name,
                    "zone": zone,
                    "mc_committed": round(float(mc.mean()), 2),
                    "S0_model_offer_vs_model_price": round(float((mc < mpz).mean()), 3),
                    "S1_model_offer_vs_actual_price": round(
                        float((mc < apz).mean()), 3
                    ),
                    "S2_reference_basis_vs_model_price": round(
                        float((s2 < mpz).mean()), 3
                    ),
                    "model_on_share": round(float((m > ON_MW).mean()), 3),
                    "campd_on_share": round(float((c > ON_MW).mean()), 3),
                    "model_twh": round(float(m.sum()) / 1e6, 3),
                    "campd_twh": round(float(c.sum()) / 1e6, 3),
                }
            )
            if zone == "NYC":
                mc_arm = mc + (ct_fuel_nyc - rc["fuel"][i]) * hr
                arm.append(
                    {
                        "plant_code": code,
                        "name": name,
                        "mc_committed_keeper": round(float(mc.mean()), 2),
                        "mc_committed_arm": round(float(mc_arm.mean()), 2),
                        "in_merit_keeper": round(float((mc < mpz).mean()), 3),
                        "in_merit_arm": round(float((mc_arm < mpz).mean()), 3),
                    }
                )
        yrec = {
            "offer_anatomy": anatomy,
            "st_gas_fuel_by_zone": {k: round(v, 3) for k, v in fuel_by_zone.items()},
            "nyc_ct_peaker_ldc_index_mean": round(float(ct_fuel_nyc.mean()), 3),
            "price_formation": price,
            "in_merit_ladder": ladder,
            "ex_ante_nyc_steam_ldc_arm": {
                "shift_usd_mmbtu_mean": round(
                    float(ct_fuel_nyc.mean() - fuel_by_zone["NYC"]), 3
                ),
                "plants": arm,
                "nyc_st_gas_model_twh": round(
                    float(sum(r["model_twh"] for r in ladder if r["zone"] == "NYC")), 3
                ),
                "nyc_st_gas_campd_twh": round(
                    float(sum(r["campd_twh"] for r in ladder if r["zone"] == "NYC")), 3
                ),
                "nyc_st_gas_floor_energy_twh": round(float(floor_nyc.sum()) / 1e6, 3),
                "nyc_st_gas_floor_mean_mw": round(float(floor_nyc.mean()), 0),
            },
        }
        rec["by_year"][str(year)] = yrec
        print(
            year,
            "fuel by zone",
            yrec["st_gas_fuel_by_zone"],
            "NYC CT LDC index",
            yrec["nyc_ct_peaker_ldc_index_mean"],
        )
        print(pd.DataFrame(ladder).to_string(index=False))
        print("  spreads:", price["spreads"])
        print(
            "  ex-ante arm:",
            {
                k: v
                for k, v in yrec["ex_ante_nyc_steam_ldc_arm"].items()
                if k != "plants"
            },
            [(a["name"], a["in_merit_keeper"], a["in_merit_arm"]) for a in arm],
        )
    write_json("_nyiso192_stgas_zonal_decomp.json", rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
