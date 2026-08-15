"""miso-158 Phase 0: the CROSS-ISO blast radius of the ``_commission_year`` defect.

**This is a SCOPING census, not an adjudicating statistic.** It computes NO
price, NO residual and NO lever effect, and it solves NOTHING. Its only job is
to answer the rule-25 ``[R-ISO-SCOPE]`` question that must be settled *before*
a construction is proposed and *before* the session's PREREG is written: how
many ISOs does ``data/fleet/assembly.py::_commission_year`` mis-stamp, and by
how much?

The defect (measured and root-caused at miso-157,
``results/calibration/FINDING-miso157-the-ct-fleet-is-stamped-one-vintage-2026-08-14.md``
section 7): ``_commission_year`` looks each plant up in
``master-plant-registry.csv`` and falls through to a **hardcoded
``return 2010``** on a miss. That registry is ERCOT-only, so for every
non-ERCOT ISO the miss is total and the whole plant-group-tagged thermal fleet
is stamped one vintage -- which makes the age-escalation limb of
``THERMAL_AVAILABILITY`` (WEFOR ``+w_rate``/yr past ``w_onset``; DERATE
``+d_rate``/yr past ``d_onset``) identically inert.

**Instrument.** The per-ISO bin sheet is the exact input ``bins_to_fleet``
consumes (``data/raw/reference/custom-bin-assignments.csv`` for ERCOT;
``data/raw/_processed-legacy/bin_assignments_<ISO>.csv`` for the five per-plant
ISOs -- see ``assembly.py:1400-1445``), so the census is computed from the bin
sheet + the registry + ``COAL_PLANT_COMMISSION_YEAR`` + EIA-860 ``vintage_2024``
WITHOUT building a fleet or touching an LP. Gate **V-C1** proves the instrument
by reproducing miso-157's committed MISO census (per-class capacity and the
``n_distinct_model_online_year == 1`` result) from the bin sheet alone.

Rule 22 ``[R-HOLDOUT]``: no year is solved, scored or registered here. The
census is year-parameterized only because ``age = year - online_year``; the
reported years are the training years 2023/2024/2025 only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.fuel_trajectories import (  # noqa: E402
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)
from market_sim.data.fleet.eia860 import (  # noqa: E402
    COAL_PLANT_COMMISSION_YEAR,
)

# T-8: the census must price age against the PRODUCTION availability table.
assert THERMAL_AVAILABILITY["CT_PEAKER"] == (0.03, 0.07, 0.003, 20, 0.05, 0.002, 20), (
    "T-8: THERMAL_AVAILABILITY['CT_PEAKER'] is not the table miso-157 measured"
)

YEARS = (2023, 2024, 2025)
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

REGISTRY_CSV = REPO / "data/raw/reference/master-plant-registry.csv"
ERCOT_BINS = REPO / "data/raw/reference/custom-bin-assignments.csv"
EIA860_GENS = REPO / "data/raw/eia-860/vintage_2024/eia860_generators.parquet"

# The hardcoded fall-through under test (assembly.py:280-285).
FALLBACK_YEAR = 2010


def _bin_sheet(iso: str) -> pd.DataFrame:
    """Return ``(Plant_Code, Plant_Group, Nameplate_MW)`` for ``iso``'s bin sheet.

    ERCOT's curated sheet and the five per-plant ISOs' synthesized sheets carry
    the same three columns under the same names; nothing else is read.
    """
    path = (
        ERCOT_BINS
        if iso == "ERCOT"
        else REPO / f"data/raw/_processed-legacy/bin_assignments_{iso}.csv"
    )
    if not path.is_file():
        raise SystemExit(f"bin sheet missing for {iso}: {path}")
    df = pd.read_csv(path, usecols=["Plant_Code", "Plant_Group", "Nameplate_MW"])
    df["Plant_Code"] = df["Plant_Code"].astype(int)
    df["Plant_Group"] = df["Plant_Group"].astype(str)
    df["Nameplate_MW"] = df["Nameplate_MW"].astype(float)
    return df


def _model_online_year(reg: dict[int, float]) -> callable:
    """Return the production ``online_year`` rule, transcribed from assembly.py.

    ``assembly.py:280-285`` (``_commission_year``) plus ``assembly.py:560-566``
    (coal's curated ``COAL_PLANT_COMMISSION_YEAR`` precedence). Transcribed
    rather than imported because ``bins_to_fleet`` closes over the registry
    dict inside a 1,200-line builder; the transcription is proved against the
    production fleet by gate V-C1.
    """

    def f(plant_code: int, group: str) -> int:
        if group == "COAL" and plant_code in COAL_PLANT_COMMISSION_YEAR:
            return int(COAL_PLANT_COMMISSION_YEAR[plant_code])
        y = reg.get(plant_code)
        if y is not None and not pd.isna(y):
            return int(y)
        return FALLBACK_YEAR

    return f


def _true_online_year() -> dict[int, float]:
    """Per-plant capacity-weighted EIA-860 ``operating_year`` (vintage_2024)."""
    e = pd.read_parquet(
        EIA860_GENS, columns=["plant_id", "operating_year", "nameplate_capacity_mw"]
    ).dropna()
    e["plant_id"] = e["plant_id"].astype(int)
    return (
        e.groupby("plant_id")
        .apply(
            lambda d: float(
                np.average(
                    d["operating_year"].astype(float),
                    weights=d["nameplate_capacity_mw"].astype(float),
                )
            ),
            include_groups=False,
        )
        .to_dict()
    )


def _priced(group: str, ages: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """WEFOR and DERATE for ``ages`` under ``THERMAL_AVAILABILITY[group]``."""
    _pof, wb, wr, won, db, dr, don = THERMAL_AVAILABILITY[group]
    wefor = wb + np.maximum(0.0, ages - won) * wr
    derate = db + np.maximum(0.0, ages - don) * dr
    return wefor, derate


def census_iso(iso: str, reg: dict[int, float], true_y: dict[int, float]) -> dict:
    """The full per-ISO exposure census, all three training years."""
    df = _bin_sheet(iso)
    model_of = _model_online_year(reg)
    df["model_online_year"] = [
        model_of(pc, g) for pc, g in zip(df["Plant_Code"], df["Plant_Group"])
    ]
    df["true_online_year"] = [true_y.get(int(pc), np.nan) for pc in df["Plant_Code"]]

    # Registry reach: the rule-25 question in one number.
    codes = set(df["Plant_Code"].tolist())
    hit = {c for c in codes if c in reg and not pd.isna(reg[c])}
    out: dict = {
        "bin_sheet_rows": int(len(df)),
        "distinct_plant_codes": int(len(codes)),
        "registry_hits": int(len(hit)),
        "registry_hit_share": float(len(hit) / len(codes)) if codes else 0.0,
        "cap_gw_total": float(df["Nameplate_MW"].sum() / 1000.0),
        "eia860_cap_coverage": float(
            df.loc[df["true_online_year"].notna(), "Nameplate_MW"].sum()
            / df["Nameplate_MW"].sum()
        ),
        "classes": {},
        "years": {},
    }

    # Per-class vintage census (the miso-157 table, ISO-generalized).
    for grp, d in df.groupby("Plant_Group"):
        if grp not in THERMAL_AVAILABILITY:
            continue  # only classes the age model actually prices
        oy = d["model_online_year"].to_numpy()
        ty = d["true_online_year"].to_numpy()
        w = d["Nameplate_MW"].to_numpy()
        ok = ~np.isnan(ty)
        out["classes"][grp] = {
            "rows": int(len(d)),
            "cap_gw": float(w.sum() / 1000.0),
            "n_distinct_model_online_year": int(len(set(oy.tolist()))),
            "model_online_year_min": int(oy.min()),
            "model_online_year_max": int(oy.max()),
            "model_capwt_online_year": float(np.average(oy, weights=w)),
            "true_capwt_online_year": (
                float(np.average(ty[ok], weights=w[ok])) if ok.any() else None
            ),
            "eia860_cap_coverage": float(w[ok].sum() / w.sum()),
        }

    # Per-year availability re-pricing, per class and ISO-wide.
    for year in YEARS:
        per_class: dict = {}
        tot_cap = 0.0
        tot_over_summer = 0.0
        tot_over_annual = 0.0
        for grp, d in df.groupby("Plant_Group"):
            if grp not in THERMAL_AVAILABILITY:
                continue
            w = d["Nameplate_MW"].to_numpy()
            ty = d["true_online_year"].to_numpy()
            oy = d["model_online_year"].to_numpy().astype(float)
            ok = ~np.isnan(ty)
            if not ok.any():
                continue
            ww, ay_t, ay_m = w[ok], year - ty[ok], year - oy[ok]
            wt, dt = _priced(grp, ay_t)
            wm, dm = _priced(grp, ay_m)
            _pof, _wb, _wr, won, _db, _dr, don = THERMAL_AVAILABILITY[grp]
            # Summer capability overstatement: the DERATE leg is flat
            # year-round; the WEFOR leg enters summer at SUMMER_WEFOR_SHARE
            # (arrays.py:773-791). Annual uses the full WEFOR.
            d_der = float(np.average(dt - dm, weights=ww))
            d_wef = float(np.average(wt - wm, weights=ww))
            cap = float(ww.sum())
            per_class[grp] = {
                "cap_gw_priced": cap / 1000.0,
                "capwt_age_true": float(np.average(ay_t, weights=ww)),
                "capwt_age_model": float(np.average(ay_m, weights=ww)),
                "cap_past_wefor_onset_gw_true": float(ww[ay_t > won].sum() / 1000.0),
                "cap_past_wefor_onset_gw_model": float(ww[ay_m > won].sum() / 1000.0),
                "cap_past_derate_onset_gw_true": float(ww[ay_t > don].sum() / 1000.0),
                "cap_past_derate_onset_gw_model": float(ww[ay_m > don].sum() / 1000.0),
                "wefor_capwt_true": float(np.average(wt, weights=ww)),
                "wefor_capwt_model": float(np.average(wm, weights=ww)),
                "derate_capwt_true": float(np.average(dt, weights=ww)),
                "derate_capwt_model": float(np.average(dm, weights=ww)),
                "summer_capability_overstatement_gw": (
                    (d_der + d_wef * SUMMER_WEFOR_SHARE) * cap / 1000.0
                ),
                "annual_capability_overstatement_gw": (d_der + d_wef) * cap / 1000.0,
            }
            tot_cap += cap
            tot_over_summer += per_class[grp]["summer_capability_overstatement_gw"]
            tot_over_annual += per_class[grp]["annual_capability_overstatement_gw"]
        # DUAL TOTALS, and the reason is disclosed rather than buried (V-C1).
        # The three CHP classes' bin-sheet NAMEPLATE overstates their LP
        # capacity by 2-3x because ``chp_steam_following`` removes host
        # self-supply from the LP; the four non-CHP classes reproduce the
        # production fleet to <=0.2 %. So the CHP-inclusive total is an UPPER
        # BOUND on nameplate scope, and the non-CHP total is the one measured
        # on a scope proved against the production fleet.
        nc = {k: v for k, v in per_class.items() if not k.endswith("_CHP")}
        out["years"][str(year)] = {
            "by_class": per_class,
            "cap_gw_priced_total": tot_cap / 1000.0,
            "summer_capability_overstatement_gw_total": tot_over_summer,
            "annual_capability_overstatement_gw_total": tot_over_annual,
            "cap_gw_priced_total_nonchp": sum(
                v["cap_gw_priced"] for v in nc.values()
            ),
            "summer_capability_overstatement_gw_nonchp": sum(
                v["summer_capability_overstatement_gw"] for v in nc.values()
            ),
            "annual_capability_overstatement_gw_nonchp": sum(
                v["annual_capability_overstatement_gw"] for v in nc.values()
            ),
        }
    return out


def v_c1_gate(miso: dict) -> dict:
    """**V-C1** -- prove the bin-sheet instrument against miso-157's committed census.

    miso-157 measured the census off the PRODUCTION fleet
    (``generators_to_fleet_arrays``); this probe measures it off the bin sheet.
    Reproducing miso-157's per-class capacity and its
    ``n_distinct_model_online_year == 1`` result is what licenses the bin-sheet
    shortcut for the five ISOs whose fleets are not built here.
    """
    ref = REPO / "results/calibration/_miso157_ct_summer_wefor.json"
    published = json.loads(ref.read_text())["years"]["2025"]["S_AGE_rederivation"]
    pub_census = published["vintage_census_by_class"]
    rows = []
    ok = True
    for cls, pc in pub_census.items():
        if cls not in miso["classes"]:
            continue
        mine = miso["classes"][cls]
        d_gw = mine["cap_gw"] - pc["cap_gw"]
        rel = abs(d_gw) / pc["cap_gw"] if pc["cap_gw"] else 0.0
        same_n = mine["n_distinct_model_online_year"] == pc["n_distinct_model_online_year"]
        # 2 % capacity bar: the production fleet drops retired/zone-unmatched
        # plants the raw sheet still carries.
        #
        # THE THREE ``*_CHP`` CLASSES ARE GATED ON ``n_distinct`` ONLY, and the
        # reason is measured, not assumed: the MISO keeper carries
        # ``chp_steam_following = True`` (+ ``chp_btm_floor_pct = 40``), which
        # removes the CHP host's behind-the-meter self-supply from the LP, so
        # the production fleet's CHP capacity is a FRACTION of the bin sheet's
        # nameplate by construction (measured here: 1.9-2.9x). It is a scope
        # difference in a known direction, not an instrument defect -- and it
        # is disclosed and carried in the record rather than deleted. The four
        # non-CHP classes, which is where every load-bearing number in this
        # census lives, reproduce the production fleet to <= 0.2 %.
        is_chp = cls.endswith("_CHP")
        good = same_n and (is_chp or rel <= 0.02)
        ok = ok and good
        rows.append(
            {
                "class": cls,
                "cap_gw_bin_sheet": mine["cap_gw"],
                "cap_gw_miso157_fleet": pc["cap_gw"],
                "rel_diff": rel,
                "n_distinct_bin_sheet": mine["n_distinct_model_online_year"],
                "n_distinct_miso157": pc["n_distinct_model_online_year"],
                "capacity_gated": not is_chp,
                "capacity_scope_note": (
                    "chp_steam_following holdout: LP capacity < nameplate"
                    if is_chp
                    else ""
                ),
                "pass": bool(good),
            }
        )
    # The CT_PEAKER re-pricing leg, against miso-157's committed 2025 numbers.
    ct = miso["years"]["2025"]["by_class"].get("CT_PEAKER", {})
    ct_check = {
        "true_capwt_online_year_bin_sheet": miso["classes"]["CT_PEAKER"][
            "true_capwt_online_year"
        ],
        "true_capwt_online_year_miso157": published["true_capwt_online_year"],
        "wefor_capwt_true_bin_sheet": ct.get("wefor_capwt_true"),
        "wefor_capwt_true_miso157": published["wefor_capwt_true"],
        "derate_capwt_true_bin_sheet": ct.get("derate_capwt_true"),
        "derate_capwt_true_miso157": published["derate_capwt_true"],
        "summer_overstatement_gw_bin_sheet": ct.get(
            "summer_capability_overstatement_gw"
        ),
        "summer_overstatement_gw_miso157": published[
            "summer_capability_overstatement_gw"
        ],
    }
    ct_ok = (
        abs(ct_check["wefor_capwt_true_bin_sheet"] - ct_check["wefor_capwt_true_miso157"])
        <= 0.005
        and abs(
            ct_check["derate_capwt_true_bin_sheet"]
            - ct_check["derate_capwt_true_miso157"]
        )
        <= 0.005
    )
    return {"per_class": rows, "ct_repricing": ct_check, "pass": bool(ok and ct_ok)}


def main() -> dict:
    reg_df = pd.read_csv(REGISTRY_CSV, usecols=["plantid", "year_built", "ba_code"])
    reg = dict(zip(reg_df["plantid"].astype(int), reg_df["year_built"]))
    true_y = _true_online_year()

    rec: dict = {
        "object": (
            "assembly.py::_commission_year hardcoded fall-through to "
            f"{FALLBACK_YEAR} when master-plant-registry.csv misses"
        ),
        "registry": {
            "path": str(REGISTRY_CSV),
            "rows": int(len(reg_df)),
            "ba_codes": {
                str(k): int(v) for k, v in reg_df["ba_code"].value_counts().items()
            },
        },
        "summer_wefor_share": float(SUMMER_WEFOR_SHARE),
        "isos": {},
    }
    for iso in ISOS:
        rec["isos"][iso] = census_iso(iso, reg, true_y)
    rec["V_C1"] = v_c1_gate(rec["isos"]["MISO"])

    out = REPO / "results/calibration/_miso158_vintage_census.json"
    out.write_text(json.dumps(rec, indent=2, default=float))
    print(f"wrote {out}")
    return rec


if __name__ == "__main__":
    main()
