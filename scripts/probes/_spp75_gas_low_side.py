"""SPP-75: which gas units run when SPP RT < 0, and why? (zero LP)

Pre-registered in ``docs/handoffs/PRECOMMIT-spp-75-gas-low-side-2026-09-23.md`` (pushed at
``ecfbda5a`` before any number below was read). Attributes the SPP-74 §3a gas deficit
(EIA-930 NG − model gas in measured RT<=0 hours) to CAMPD SWPP-BA gas units tagged by EIA-860
CHP flag / sector / prime mover, against the rung's class_hourly and a fleet_only membership
dump (``_spp75_fleet_membership.py``, one interpreter per year).

Usage: ``uv run python scripts/probes/_spp75_gas_low_side.py --fleet-dir <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp72_demand_tightness import (  # noqa: E402
    CST_OFFSET_H,
    model_clock_index,
)
from scripts.probes._spp73_commitment_reach import (  # noqa: E402
    MST_STATES,
    SPP_STATES,
    classify,
    swpp_gas_units,
)
from scripts.probes._spp74_body_decomposition import (  # noqa: E402
    fueltype,
    hour_types,
    model_class_mw,
)

YEARS = (2019, 2020, 2021, 2022)
DECIDE = (2020, 2022)  # PRECOMMIT §1
FLAT = 0.8  # PRECOMMIT §1 price-insensitivity threshold
MINLOAD_TOL = 1.2  # PRECOMMIT §2 (ii) "at or near min load"
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
GAS_PREFIX = ("CC_", "CT_", "ST_")


def plant_tags() -> pd.DataFrame:
    """Per-plant EIA-860 tags: CHP, sector, min-load MW (gas generators)."""
    plant = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_plant.parquet")
    plant["pc"] = pd.to_numeric(plant["Plant Code"], errors="coerce")
    plant = plant.dropna(subset=["pc"]).astype({"pc": int}).set_index("pc")
    gen = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    gen["pc"] = pd.to_numeric(gen["Plant Code"], errors="coerce")
    gen = gen.dropna(subset=["pc"]).astype({"pc": int})
    chp_gen = (
        (
            gen["Associated with Combined Heat and Power System"]
            .astype(str)
            .str.upper()
            == "Y"
        )
        .groupby(gen["pc"])
        .any()
    )
    ng = gen[gen["Energy Source 1"].astype(str).str.upper() == "NG"]
    minload = (
        pd.to_numeric(ng["Minimum Load (MW)"], errors="coerce")
        .groupby(ng["pc"])
        .sum(min_count=1)
    )
    nameplate = (
        pd.to_numeric(ng["Nameplate Capacity (MW)"], errors="coerce")
        .groupby(ng["pc"])
        .sum()
    )
    t = pd.DataFrame(
        {
            "chp": chp_gen.reindex(plant.index).fillna(False)
            | (plant["FERC Cogeneration Status"].astype(str).str.upper() == "Y"),
            "sector": plant["Sector Name"].astype(str),
            "state": plant["State"].astype(str),
            "name": plant["Plant Name"].astype(str),
        }
    )
    t["ng_minload_mw"] = minload.reindex(t.index)
    t["ng_nameplate_mw"] = nameplate.reindex(t.index)
    return t


def campd_units(
    y: int, ids: set[int], pm: dict[int, set[str]]
) -> tuple[pd.DataFrame, np.ndarray]:
    """Per gas unit meta + (n_units, 8760) gross MW on the model clock."""
    clock = model_clock_index(y)
    local_cst = (clock - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None)
    slot = pd.Series(np.arange(8760), index=local_cst)
    frames = []
    for st in SPP_STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p,
            columns=[
                "stateCode",
                "facilityId",
                "unitId",
                "date",
                "hour",
                "grossLoad",
                "primaryFuelInfo",
                "unitType",
            ],
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["facilityId"].isin(ids)]
        if len(d):
            frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    ts = ts + pd.to_timedelta(d["stateCode"].isin(MST_STATES).astype(int), unit="h")
    d["slot"] = slot.reindex(ts.to_numpy()).to_numpy()
    d = d[np.isfinite(d["slot"])]
    d["slot"] = d["slot"].astype(int)
    d["u"] = d["facilityId"].astype(int).astype(str) + "|" + d["unitId"].astype(str)
    meta = d.groupby("u").agg(
        fid=("facilityId", "first"),
        ut=("unitType", "first"),
        fu=("primaryFuelInfo", "first"),
    )
    meta["fid"] = meta["fid"].astype(int)
    meta["cls"] = [
        classify(r.ut, r.fu, pm.get(int(r.fid), set())) for r in meta.itertuples()
    ]
    meta = meta[meta["cls"].notna()]
    d = d[d["u"].isin(meta.index)]
    mw = np.zeros((len(meta), 8760))
    r = meta.index.get_indexer(d["u"])
    np.add.at(mw, (r, d["slot"].to_numpy()), d["grossLoad"].fillna(0).to_numpy())
    return meta, mw


def eia923_chp_flat(y: int) -> float:
    """EIA-923 SWPP-BA gas CHP=Y annual net generation / 8760 (MW): flat-CHP reach bound."""
    g = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    g = g[(g["year"] == y) & (g["ba_code"] == "SWPP") & (g["fuel_type"] == "NG")]
    return {
        "chp_Y_mw": float(g.loc[g["chp"] == "Y", "netgen_annual_mwh"].sum() / 8760),
        "chp_N_mw": float(g.loc[g["chp"] == "N", "netgen_annual_mwh"].sum() / 8760),
    }


def group_of(row: pd.Series) -> str:
    """PRECOMMIT §2 object label for a CAMPD unit."""
    sec = row["sector"].lower()
    if row["chp"] or "industrial" in sec or "commercial" in sec:
        return "i_chp_industrial"
    if row["cls"] == "CT":
        return "ct_nonchp"
    return "ii_utility_ipp_cc_st"


def year_block(y: int, tags: pd.DataFrame, ids, pm, fleet: list | None) -> dict:
    """Everything PRECOMMIT §2 asks for, one year."""
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    a = lmp[lmp["year"] == y].sort_values("hour")["rt"].to_numpy(float)
    lab = hour_types(a)
    neg, mid2 = lab == "NEG", lab == "MID2"
    cm = model_class_mw(y)
    gas_cols = [c for c in cm.columns if c.startswith(GAS_PREFIX)]
    ft = pd.read_parquet(RAW_DATA_DIR / "SWPP_fueltype.parquet")
    ng930 = fueltype(ft, "NG", y)
    model_gas = cm[gas_cols].sum(axis=1).to_numpy()
    G = float(ng930[neg].mean() - model_gas[neg].mean())
    meta, mw = campd_units(y, ids, pm)
    meta = meta.join(tags, on="fid")
    meta["chp"] = meta["chp"].fillna(False).astype(bool)
    meta["sector"] = meta["sector"].fillna("?")
    meta["grp"] = meta.apply(group_of, axis=1)
    meta["neg_mw"] = mw[:, neg].mean(1)
    meta["mid2_mw"] = mw[:, mid2].mean(1)
    campd_neg = float(meta["neg_mw"].sum())
    kappa = campd_neg / float(ng930[neg].mean())
    # min-load signature for group (ii): unit-hours at <= 1.2 x its plant's share of min load
    pl_units = meta.groupby("fid")["neg_mw"].transform("size")
    unit_min = meta["ng_minload_mw"] / pl_units
    on_neg = mw[:, neg] > 0
    near_min = on_neg & (mw[:, neg] <= (MINLOAD_TOL * unit_min.to_numpy())[:, None])
    meta["neg_mw_nearmin"] = np.where(near_min, mw[:, neg], 0).mean(1)
    meta["neg_on_share"] = on_neg.mean(1)
    mod = {
        k: float(cm[k].to_numpy()[neg].mean()) if k in cm else 0.0
        for k in ("CC_CHP", "CT_CHP", "ST_CHP", "CC_REGULAR", "ST_GAS", "CT_PEAKER")
    }
    mod_mid2 = {
        k: float(cm[k].to_numpy()[mid2].mean()) if k in cm else 0.0 for k in mod
    }
    model_match = {
        "i_chp_industrial": mod["CC_CHP"] + mod["CT_CHP"] + mod["ST_CHP"],
        "ii_utility_ipp_cc_st": mod["CC_REGULAR"] + mod["ST_GAS"],
        "ct_nonchp": mod["CT_PEAKER"],
    }
    grp = {}
    for g, sub in meta.groupby("grp"):
        m_neg = float(sub["neg_mw"].sum())
        grp[g] = {
            "n_units": int(len(sub)),
            "meas_neg_mw": m_neg,
            "meas_mid2_mw": float(sub["mid2_mw"].sum()),
            "flat_ratio": m_neg / float(sub["mid2_mw"].sum())
            if sub["mid2_mw"].sum()
            else None,
            "model_neg_mw": model_match[g],
            "gap_mw": m_neg - model_match[g],
            "share_of_G": (m_neg - model_match[g]) / G,
            "share_of_G_kappa_scaled": (m_neg / kappa - model_match[g]) / G,
            "meas_neg_mw_near_minload": float(sub["neg_mw_nearmin"].sum()),
            "minload_known_units": int(sub["ng_minload_mw"].notna().sum()),
        }
    # (iii) membership
    iii = None
    if fleet is not None:
        fl = pd.DataFrame(fleet)
        gas_pl = set(fl.loc[fl["klass"].str.startswith(GAS_PREFIX), "plant"])
        any_pl = set(fl["plant"])
        absent = ~meta["fid"].isin(any_pl)
        nongas = meta["fid"].isin(any_pl) & ~meta["fid"].isin(gas_pl)
        cls_by_plant = fl.groupby("plant")["klass"].agg(lambda s: sorted(set(s)))
        iii = {
            "absent_units": int(absent.sum()),
            "absent_neg_mw": float(meta.loc[absent, "neg_mw"].sum()),
            "absent_share_of_G": float(meta.loc[absent, "neg_mw"].sum()) / G,
            "nongas_class_units": int(nongas.sum()),
            "nongas_class_neg_mw": float(meta.loc[nongas, "neg_mw"].sum()),
            "absent_top": meta.loc[absent]
            .sort_values("neg_mw", ascending=False)
            .head(10)[["fid", "name", "state", "cls", "sector", "chp", "neg_mw"]]
            .to_dict("records"),
            "chp_plants_model_class": {
                str(int(f)): cls_by_plant.get(int(f), ["ABSENT"])
                for f in meta.loc[meta["grp"] == "i_chp_industrial", "fid"].unique()
            },
        }
    # flat (price-insensitive) units: on >= 90 % of H_neg and ratio >= FLAT (PRECOMMIT §1)
    meta["flat_unit"] = (meta["neg_on_share"] >= 0.9) & (
        meta["neg_mw"] >= FLAT * meta["mid2_mw"]
    )
    flat_split = meta[meta["flat_unit"]].groupby("grp")["neg_mw"].sum().to_dict()
    ii = meta[meta["grp"] == "ii_utility_ipp_cc_st"]
    ii_split = {
        "CC": {
            "meas": float(ii.loc[ii["cls"] == "CC", "neg_mw"].sum()),
            "model_CC_REGULAR": mod["CC_REGULAR"],
        },
        "ST_GAS": {
            "meas": float(ii.loc[ii["cls"] == "ST_GAS", "neg_mw"].sum()),
            "model_ST_GAS": mod["ST_GAS"],
        },
        "by_sector": ii.groupby("sector")["neg_mw"].sum().to_dict(),
        "on_share_mw_weighted": float(
            np.average(ii["neg_on_share"], weights=ii["neg_mw"] + 1e-9)
        ),
        "neg_over_mid2": float(ii["neg_mw"].sum() / ii["mid2_mw"].sum()),
    }
    if fleet is not None:
        fl = pd.DataFrame(fleet)
        chp_fids = meta.loc[meta["grp"] == "i_chp_industrial", "fid"].unique()
        sub = fl[fl["plant"].isin(chp_fids)]
        iii["chp_plants_model_pmax_by_class"] = (
            sub.groupby("klass")["pmax"].sum().to_dict()
        )
        iii["chp_group_meas_by_model_class"] = {
            k: float(
                meta.loc[
                    (meta["grp"] == "i_chp_industrial")
                    & meta["fid"].isin(set(fl.loc[fl["klass"] == k, "plant"])),
                    "neg_mw",
                ].sum()
            )
            for k in sorted(sub["klass"].unique())
        }
    top = meta.sort_values("neg_mw", ascending=False).head(25)
    return {
        "n_neg": int(neg.sum()),
        "ng930_neg": float(ng930[neg].mean()),
        "model_gas_neg": float(model_gas[neg].mean()),
        "G": G,
        "campd_gas_neg": campd_neg,
        "kappa": kappa,
        "model_class_neg": mod,
        "model_class_mid2": mod_mid2,
        "groups": grp,
        "flat_units_neg_mw_by_group": flat_split,
        "ii_split": ii_split,
        "cls_split_meas_neg": meta.groupby("cls")["neg_mw"].sum().to_dict(),
        "sector_split_meas_neg": meta.groupby("sector")["neg_mw"].sum().to_dict(),
        "eia923": eia923_chp_flat(y),
        "model_chp_annual_mw": float(
            cm[[c for c in CHP_CLASSES if c in cm]].sum(axis=1).mean()
        ),
        "iii": iii,
        "top_units": top[
            [
                "fid",
                "name",
                "state",
                "cls",
                "sector",
                "chp",
                "grp",
                "neg_mw",
                "mid2_mw",
                "neg_on_share",
                "neg_mw_nearmin",
                "ng_minload_mw",
                "ng_nameplate_mw",
            ]
        ].to_dict("records"),
    }


def main() -> None:
    """Run PRECOMMIT §2 for every year and write the JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tags = plant_tags()
    ids, pm = swpp_gas_units()
    out = {}
    for y in YEARS:
        fp = Path(a.fleet_dir) / f"fleet_{y}.json"
        fleet = json.loads(fp.read_text()) if fp.exists() else None
        out[y] = year_block(y, tags, ids, pm, fleet)
        b = out[y]
        print(f"{y}: n_neg {b['n_neg']}  G {b['G']:.0f} MW  kappa {b['kappa']:.2f}")
        for g, v in b["groups"].items():
            print(
                f"   {g:<22} meas {v['meas_neg_mw']:7.0f} model {v['model_neg_mw']:7.0f} "
                f"share {v['share_of_G']:+.2f} (k {v['share_of_G_kappa_scaled']:+.2f}) "
                f"flat {v['flat_ratio'] if v['flat_ratio'] is None else round(v['flat_ratio'], 2)} "
                f"nearmin {v['meas_neg_mw_near_minload']:.0f}"
            )
        if b["iii"]:
            print(
                f"   iii absent {b['iii']['absent_units']} units {b['iii']['absent_neg_mw']:.0f} MW "
                f"share {b['iii']['absent_share_of_G']:+.2f}; nongas-class {b['iii']['nongas_class_neg_mw']:.0f} MW"
            )
        print(f"   flat units {b['flat_units_neg_mw_by_group']}  ii {b['ii_split']}")
        if b["iii"]:
            print(
                f"   CHP plants in model: pmax {b['iii']['chp_plants_model_pmax_by_class']} "
                f"meas-NEG by model class {b['iii']['chp_group_meas_by_model_class']}"
            )
        print(
            f"   EIA-923 CHP flat {b['eia923']['chp_Y_mw']:.0f} MW vs model CHP {b['model_chp_annual_mw']:.0f} MW"
        )
    Path(a.out).write_text(
        json.dumps(
            out,
            indent=1,
            default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o),
        )
    )


if __name__ == "__main__":
    main()
