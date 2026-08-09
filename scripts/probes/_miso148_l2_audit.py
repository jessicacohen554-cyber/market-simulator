"""miso-148 G-L2 — the CC fleet/rating audit (PREREG §5 "G-L2").

Decomposes the model's CC ``pmax`` against CAMPD demonstrated ratings into
NAMED components, universes registered before any subtraction, so the L1 summer
repair is known to sit on a valid population/rating base (PREREG §3: the audit
runs BEFORE the derate arm).

Gates, each with its pre-committed branch (PREREG §5 "G-L2"):

* **G-L2a POPULATION** -- CC plants in CAMPD MISO with no model counterpart and
  vice versa, in MW and unit count.
* **G-L2b BASIS** -- the gross<->net and nameplate<->net-summer conversions,
  applied and reported explicitly (TRAP T5: CAMPD p99 is GROSS, model ``pmax``
  is NET; reading them directly against each other manufactures a fake gap).
* **G-L2c VINTAGE** -- the EIA-860 release the fleet actually loads vs the
  newest committed on disk.
* **G-L2d RECONCILE** -- the MW ``cc_capacity_reconcile`` removes, reported as a
  DELIBERATE MEASURED CAP and never counted into a "missing capacity" total
  (TRAP T6).

Branches: ``basis_explained`` (B-1) -> L1 proceeds; ``population_defect`` (B-2)
or ``vintage_defect`` (B-3) -> L1 is SUSPENDED and the data correction is the
session's deliverable.

Probe hygiene (miso-140b §6): ``hygiene()`` at the entry point; the CAMPD unit
loader and strata come from ``_miso147_strata`` (never ``load_campd_hourly``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

from _miso143_stack import YEARS, fleet_state, hygiene  # noqa: E402
from _miso147_strata import campd_units, parasitic_map  # noqa: E402

OUT = REPO / "results" / "calibration" / "_miso148_l2_audit.json"

CC_KLASSES = ("CC_REGULAR", "CC_CHP")
#: PREREG §5 G-L2 B-2 bar: >= 1 GW of CC plants missing from the model fleet.
POPULATION_BAR_MW = 1000.0


def model_all(year: int) -> pd.DataFrame:
    """Per-TRANCHE model fleet for ``year`` — EVERY class, not just CC.

    The pre-registered G-L2a text asks for CAMPD CC plants "with no model
    counterpart". A plant the model carries under CT_CHP/ST_CHP *has* a
    counterpart; it is a CLASSIFICATION difference, not a population hole. The
    first implementation of this gate compared against model **CC classes
    only**, which is narrower than the gate's own wording and mis-scored the
    industrial-CHP boundary as missing capacity — reported against interest in
    the finding. Both views are now measured and reported separately.
    """
    st = fleet_state(year)
    gens = st["fleet"]
    pmax = np.asarray(st["fleet_arrays"].pmax, dtype=float)
    return pd.DataFrame(
        [
            {
                "plant_code": int(getattr(g, "plant_code", -1)),
                "klass": getattr(g, "plant_group", None),
                "pmax": float(pmax[i]),
            }
            for i, g in enumerate(gens)
        ]
    )


def model_cc(year: int) -> tuple[pd.DataFrame, dict]:
    """Per-PLANT model CC capacity for ``year`` (NET basis, the LP's own pmax)."""
    df = model_all(year)
    df = df[df["klass"].isin(CC_KLASSES)]
    per_plant = (
        df.groupby("plant_code")
        .agg(pmax_mw=("pmax", "sum"), n_tranches=("pmax", "size"))
        .reset_index()
    )
    meta = {
        "year": year,
        "n_lp_tranches": int(len(df)),
        "n_plants": int(per_plant["plant_code"].nunique()),
        "pmax_gw": round(float(df["pmax"].sum()) / 1000.0, 3),
        "universe": "keeper fleet_state (fleet_only, no LP), plant_group in CC_REGULAR/CC_CHP; NET basis",
    }
    return per_plant, meta


def campd_cc_ratings(year: int) -> tuple[pd.DataFrame, dict]:
    """Per-PLANT CAMPD demonstrated CC ratings (GROSS p99 of unit hourly)."""
    units, umeta = campd_units(year)
    cc = units[units["family"] == "CC"]
    per_unit = cc.groupby("unit").agg(
        p99_gross=("gross", lambda s: float(np.percentile(s.to_numpy(float), 99))),
        plant_id=("plant_id", "first"),
    )
    per_plant = (
        per_unit.groupby("plant_id")
        .agg(p99_gross_mw=("p99_gross", "sum"), n_units=("p99_gross", "size"))
        .reset_index()
        .rename(columns={"plant_id": "plant_code"})
    )
    meta = {
        "year": year,
        "n_cc_units": int(per_unit.shape[0]),
        "n_cc_plants": int(per_plant.shape[0]),
        "p99_gross_gw": round(float(per_plant["p99_gross_mw"].sum()) / 1000.0, 3),
        "campd_universe": umeta,
        "basis": "GROSS, Sum unit p99 of hourly grossLoad (the miso-147 G-F3 construction)",
    }
    return per_plant, meta


def eia860_cc_rows() -> pd.DataFrame:
    """EIA-860 Operable CC generator rows, per plant, from the ACTIVE release."""
    from market_sim.config.paths import active_eia860_dir

    df = pd.read_parquet(
        active_eia860_dir() / "eia860_generator_operable.parquet",
        columns=[
            "Plant Code",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
            "Winter Capacity (MW)",
        ],
    )
    cc = df[df["Technology"].astype(str).str.contains("Combined Cycle", na=False)]
    out = cc.rename(
        columns={
            "Plant Code": "plant_code",
            "Nameplate Capacity (MW)": "np_mw",
            "Summer Capacity (MW)": "ns_mw",
            "Winter Capacity (MW)": "nw_mw",
        }
    )[["plant_code", "np_mw", "ns_mw", "nw_mw"]]
    for c in ("np_mw", "ns_mw", "nw_mw"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(subset=["np_mw", "ns_mw"])


def gate_l2a_population(year: int) -> dict:
    """CC plants present in one universe and absent from the other.

    TWO views, because they answer different questions and only the first is
    the pre-registered B-2 test quantity:

    * **absent_from_fleet** — CAMPD CC plants with no model counterpart in ANY
      class. This is the gate's own wording and the B-2 quantity.
    * **cc_classified_elsewhere** — carried by the model, but under a non-CC
      class (industrial CHP, peaker). A classification/boundary difference.
    """
    mod, mmeta = model_cc(year)
    cam, cmeta = campd_cc_ratings(year)
    allm = model_all(year)
    fleet_plants = set(allm["plant_code"])
    cc_plants = set(mod["plant_code"])

    absent = cam[~cam["plant_code"].isin(fleet_plants)]
    elsewhere = cam[
        cam["plant_code"].isin(fleet_plants) & ~cam["plant_code"].isin(cc_plants)
    ]
    only_model = mod[~mod["plant_code"].isin(set(cam["plant_code"]))]
    absent_mw = float(absent["p99_gross_mw"].sum())

    def _detail(sub: pd.DataFrame) -> list[dict]:
        out = []
        for r in sub.itertuples():
            pc = int(r.plant_code)
            k = sorted(
                str(x) for x in allm.loc[allm["plant_code"] == pc, "klass"].unique()
            )
            out.append(
                {
                    "plant_code": pc,
                    "campd_p99_gross_mw": round(float(r.p99_gross_mw), 1),
                    "model_klasses": k,
                    "model_pmax_mw": round(
                        float(allm.loc[allm["plant_code"] == pc, "pmax"].sum()), 1
                    ),
                }
            )
        return out

    return {
        "model": mmeta,
        "campd": cmeta,
        "n_plants_both": len(cc_plants & set(cam["plant_code"])),
        "absent_from_fleet": {
            "n_plants": int(len(absent)),
            "p99_gross_mw": round(absent_mw, 1),
            "detail": _detail(absent),
        },
        "cc_classified_elsewhere": {
            "n_plants": int(len(elsewhere)),
            "p99_gross_mw": round(float(elsewhere["p99_gross_mw"].sum()), 1),
            "detail": _detail(elsewhere),
        },
        "model_only": {
            "n_plants": int(len(only_model)),
            "pmax_mw": round(float(only_model["pmax_mw"].sum()), 1),
            "plants": sorted(int(p) for p in only_model["plant_code"]),
        },
        "bar_mw": POPULATION_BAR_MW,
        "population_defect": bool(absent_mw >= POPULATION_BAR_MW),
        "note": (
            "B-2 is scored on absent_from_fleet ONLY (the gate's own wording: "
            "'no model counterpart'). cc_classified_elsewhere is the "
            "industrial-CHP / BTM boundary miso-147 §1 already named, not "
            "missing capacity. campd_only MW is GROSS (its own basis)."
        ),
    }


def gate_l2b_basis(year: int) -> dict:
    """The explicit gross<->net and nameplate<->net-summer conversions (T5)."""
    mod, _ = model_cc(year)
    cam, _ = campd_cc_ratings(year)
    factors = parasitic_map()
    both = mod.merge(cam, on="plant_code", how="inner")
    f = both["plant_code"].map(lambda p: factors.get(int(p), 1.0)).astype(float)
    both = both.assign(p99_net_mw=both["p99_gross_mw"] * f, pf=f)
    e = eia860_cc_rows().groupby("plant_code").sum(numeric_only=True).reset_index()
    j = both.merge(e, on="plant_code", how="left")
    clean = j["ns_mw"] <= j["np_mw"]
    tot_gross = float(both["p99_gross_mw"].sum())
    tot_net = float(both["p99_net_mw"].sum())
    tot_pmax = float(both["pmax_mw"].sum())

    # Split MERCHANT CC from CHP: an industrial-CHP plant is carried at its
    # grid-exporting fraction only (host steam is held out behind the meter),
    # so its model pmax is BY DESIGN far below the CAMPD meter's gross. Mixing
    # the two makes the merchant CC rating question unreadable.
    allm = model_all(year)
    chp_plants = set(
        allm.loc[allm["klass"].astype(str).str.contains("CHP", na=False), "plant_code"]
    )
    split = {}
    for tag, sub in (
        ("merchant_cc", both[~both["plant_code"].isin(chp_plants)]),
        ("chp_boundary", both[both["plant_code"].isin(chp_plants)]),
    ):
        g = float(sub["p99_gross_mw"].sum())
        n = float(sub["p99_net_mw"].sum())
        p = float(sub["pmax_mw"].sum())
        split[tag] = {
            "n_plants": int(len(sub)),
            "model_pmax_gw": round(p / 1000.0, 3),
            "campd_p99_net_gw": round(n / 1000.0, 3),
            "gap_gw": round((p - n) / 1000.0, 3),
            "gap_pct": round(100.0 * (p - n) / n, 2) if n else None,
        }

    return {
        "matched_plants": int(len(both)),
        "split_merchant_vs_chp": split,
        "campd_p99_gross_gw": round(tot_gross / 1000.0, 3),
        "campd_p99_net_gw": round(tot_net / 1000.0, 3),
        "model_pmax_gw": round(tot_pmax / 1000.0, 3),
        "cap_weighted_parasitic_factor": round(tot_net / tot_gross, 4) if tot_gross else None,
        "gap_vs_gross_gw": round((tot_pmax - tot_gross) / 1000.0, 3),
        "gap_vs_net_gw": round((tot_pmax - tot_net) / 1000.0, 3),
        "gap_vs_net_pct": round(100.0 * (tot_pmax - tot_net) / tot_net, 2) if tot_net else None,
        "eia860_on_matched": {
            "nameplate_gw": round(float(j["np_mw"].sum()) / 1000.0, 3),
            "net_summer_gw": round(float(j["ns_mw"].sum()) / 1000.0, 3),
            "net_winter_gw": round(float(j["nw_mw"].sum()) / 1000.0, 3),
            "ns_over_np_all": round(float(j["ns_mw"].sum() / j["np_mw"].sum()), 4),
            "ns_over_np_clean": round(
                float(j.loc[clean, "ns_mw"].sum() / j.loc[clean, "np_mw"].sum()), 4
            ),
            "clean_gap_pct": round(
                100.0 * (1.0 - float(j.loc[clean, "ns_mw"].sum() / j.loc[clean, "np_mw"].sum())), 2
            ),
            "n_plants_corrupt_ns_gt_np": int((~clean).sum()),
            "corrupt_np_mw": round(float(j.loc[~clean, "np_mw"].sum()), 1),
            "corrupt_ns_mw": round(float(j.loc[~clean, "ns_mw"].sum()), 1),
        },
        "note": (
            "TRAP T5 discharged: CAMPD p99 is GROSS, model pmax is NET. Both "
            "bases are quoted side by side and the pipeline's own per-plant "
            "parasitic factor supplies the conversion."
        ),
    }


def gate_l2c_vintage(year: int) -> dict:
    """Which EIA-860 release the fleet actually loads for this solve year."""
    from market_sim.config.paths import EIA_860_DIR, active_eia860_dir, set_eia860_vintage

    default_dir = active_eia860_dir()
    resolved = set_eia860_vintage(year)
    set_eia860_vintage(None)
    on_disk = sorted(p.name for p in EIA_860_DIR.glob("vintage_*") if p.is_dir())
    return {
        "solve_year": year,
        "canonical_dir": str(default_dir.relative_to(REPO)),
        "resolves_to": str(resolved.relative_to(REPO)),
        "year_matched_vintage_exists": resolved != EIA_860_DIR,
        "vintages_on_disk": on_disk,
        "newest_vintage_on_disk": on_disk[-1] if on_disk else None,
        "note": (
            "set_eia860_vintage(year) is the loader's own resolver; a year with "
            "no committed vintage_<year>/ falls back to the canonical release."
        ),
    }


def gate_l2d_reconcile() -> dict:
    """The MW cc_capacity_reconcile deliberately caps (T6: never a defect)."""
    from market_sim.config.paths import cc_capacity_reconcile_path

    p = cc_capacity_reconcile_path("MISO")
    if not p.exists():
        return {"exists": False, "path": str(p)}
    df = pd.read_csv(p)
    capped = df[df["reconciled_mw"] < df["current_mw"]]
    return {
        "exists": True,
        "path": str(p.relative_to(REPO)),
        "n_rows": int(len(df)),
        "n_capped": int(len(capped)),
        "current_mw_total": round(float(df["current_mw"].sum()), 1),
        "reconciled_mw_total": round(float(df["reconciled_mw"].sum()), 1),
        "mw_removed": round(float((df["current_mw"] - df["reconciled_mw"]).clip(lower=0).sum()), 1),
        "modes": sorted(df["mode"].astype(str).unique().tolist()),
        "sources": sorted(df["source"].astype(str).unique().tolist()),
        "top5_by_mw_removed": [
            {
                "plant_code": int(r.plant_code),
                "name": str(r.plant_name),
                "current_mw": float(r.current_mw),
                "reconciled_mw": float(r.reconciled_mw),
                "delta_pct": float(r.delta_pct),
            }
            for r in capped.assign(d=capped["current_mw"] - capped["reconciled_mw"])
            .nlargest(5, "d")
            .itertuples()
        ],
        "note": (
            "TRAP T6 discharged: this is a DELIBERATE measured cap to CAMPD "
            "demonstrated peak (rule 13 admissible input), never counted into a "
            "'missing capacity' total."
        ),
    }


def run() -> dict:
    hygiene()
    res: dict = {
        "session": "miso-148",
        "prereg": "results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md",
        "gate": "G-L2 CC fleet/rating audit (runs BEFORE the L1 arm, PREREG §3)",
        "years": {},
        "G_L2d_reconcile": gate_l2d_reconcile(),
    }
    for y in YEARS:
        res["years"][str(y)] = {
            "G_L2a_population": gate_l2a_population(y),
            "G_L2b_basis": gate_l2b_basis(y),
            "G_L2c_vintage": gate_l2c_vintage(y),
        }
    defect = any(
        res["years"][str(y)]["G_L2a_population"]["population_defect"] for y in YEARS
    )
    res["branch"] = "B-2 population_defect" if defect else "B-1 basis_explained"
    res["L1_proceeds"] = not defect
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    for y in YEARS:
        a = r["years"][str(y)]["G_L2a_population"]
        b = r["years"][str(y)]["G_L2b_basis"]
        s = b["split_merchant_vs_chp"]
        print(
            f"{y}: model CC {a['model']['pmax_gw']} GW ({a['model']['n_plants']} plants) | "
            f"ABSENT from fleet {a['absent_from_fleet']['n_plants']}p/"
            f"{a['absent_from_fleet']['p99_gross_mw']} MW | "
            f"CC-classified-elsewhere {a['cc_classified_elsewhere']['n_plants']}p/"
            f"{a['cc_classified_elsewhere']['p99_gross_mw']} MW"
        )
        print(
            f"      merchant CC: pmax {s['merchant_cc']['model_pmax_gw']} GW vs "
            f"CAMPD p99 net {s['merchant_cc']['campd_p99_net_gw']} GW "
            f"-> gap {s['merchant_cc']['gap_gw']} GW ({s['merchant_cc']['gap_pct']}%) | "
            f"CHP boundary gap {s['chp_boundary']['gap_gw']} GW"
        )
    print(f"RECONCILE removes {r['G_L2d_reconcile']['mw_removed']} MW over "
          f"{r['G_L2d_reconcile']['n_capped']} capped plants")
    print(f"BRANCH: {r['branch']}  (L1 proceeds: {r['L1_proceeds']})")
    print(f"-> {OUT}")
