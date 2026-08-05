"""ERCOT-170 Phase 0 — per-unit adjudication of the ~2.7 GW CC headroom object.

NO LP, no solve, no mechanism armed, keeper UNCHANGED
(``2026-08-05-run168b-year-curves``). Charter: mechanism-testing-matrix §5.1
**item 11** (the ERCOT-163 close-out). Decision rule pre-registered and pushed
before this file ran: ``docs/PRECOMMIT-ercot170-cc-headroom-crosswalk-2026-08-05.md``.

**The question.** ERCOT-163 refuted the "~8 GW cheap CC offline block" and left a
real, smaller residual: at the committed top-100 2023 gap hours the model leaves
**3.07 GW** of CC undispatched where the market had **0.35 GW**, while model CC
*dispatch* is right to +0.30 GW. ERCOT-163 named the provenance *capability, not
commitment* — 38.83 GW of model CC nameplate against a 35.26 GW SCED CC universe
— and handed it forward unchartered because neither of its probes could
attribute it to units. This probe does the attribution.

**Construction (precommit §1).** Everything is imported, never re-implemented:
``scripts.lib.sced_corpus_instruments.capability_census`` (which itself imports
``ercot163_cc_commitment_state_census``'s ``_cap_ref`` / ``_train`` /
``_state_of`` / ``_hoy`` verbatim) for the reality side;
``scripts.lib.bundle_fleet.reconstruct_bundle_fleet`` on the keeper bundle for
the model side; the keeper's committed ``class_hourly_2023.parquet`` for
dispatch. The crosswalk spine is ERCOT MIS NP4-160-SG (published), the accepted
rows of ``ercot-dam-plant-crosswalk.csv`` and ``ercot_noncampd_dam_crosswalk.csv``
(hand-adjudicated under ERCOT-97/110), and nothing else — **no row is accepted
on model recall of ERCOT mnemonics** (precommit §1b).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot170_cc_headroom_phase0.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    REPO,
    REPO / "src",
    REPO / "scripts",
    REPO / "scripts" / "data",
    Path(__file__).resolve().parent,
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/ercot168_yearcurves_B"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
NETWORK = REPO / "data/raw/ercot-network-model"
XWALK = REPO / "data/raw/reference/ercot-dam-plant-crosswalk.csv"
NONCAMPD = REPO / "data/raw/reference/ercot_noncampd_dam_crosswalk.csv"
EIA860_PLANT = REPO / "data/raw/eia-860/eia860_plant.parquet"
DEFAULT_OUT = REPO / "results/calibration/ercot170_cc_headroom_phase0.json"
YEAR = 2023

#: Model classes forming the CC universe (ERCOT-163's ``MODEL_GROUPS["CC"]``).
MODEL_CC_GROUPS = ("CC_REGULAR", "CC_CHP")

#: Pre-registered coverage licence (precommit §1b). NOT movable after measuring.
L1_SCED_CLOSURE = 0.90
L2_AMBIGUITY_BUDGET = 0.10

#: Pre-registered decision thresholds (precommit §2).
A_DOMINANCE_BAR = 0.60
A_NAMED_BAR = 0.60

#: Capacity-ratio windows, pre-registered (precommit §1b): X2 lexical accept and
#: the tighter X3/E1 unique-survivor window.
X2_RATIO = (0.70, 1.30)
E1_RATIO = (0.90, 1.10)

#: Construction-error stop on the attribution identity (precommit §1c), GW.
IDENTITY_TOL_GW = 0.01

_CC_SUFFIX = re.compile(r"_CC\d+$")
_TOKEN = re.compile(r"[^A-Z0-9]+")


def _site_of_train(train: str) -> str:
    """``RIONOG_CC1`` -> ``RIONOG``; the ERCOT site mnemonic behind a CC train."""
    return _CC_SUFFIX.sub("", str(train))


def _norm(s: str) -> str:
    """Upper-case, non-alphanumerics stripped — the precommit §1b normalisation."""
    return _TOKEN.sub("", str(s).upper())


def _tokens(s: str) -> list[str]:
    """Upper-case alphanumeric tokens of a plant name."""
    return [t for t in _TOKEN.split(str(s).upper()) if t]


def _token_prefix_cover(mnemonic: str, name: str) -> bool:
    """Precommit §1b X2: can ``mnemonic`` be cut into prefixes of name tokens?

    The mnemonic is segmented into >= 1 consecutive pieces, each of which must
    be a PREFIX of a distinct name token, taken in the name's own order. So
    ``RIONOG`` clears ``RIO NOGALES`` (RIO|NOG) and ``BASTEN`` clears
    ``BASTROP ENERGY CENTER`` (BAST|EN); ``CVC`` does not clear
    ``CHANNELVIEW COGENERATION PLANT`` (no token begins with ``V``).
    """
    m = _norm(mnemonic)
    toks = _tokens(name)
    if not m or not toks:
        return False

    def rec(pos: int, ti: int) -> bool:
        if pos == len(m):
            return True
        for j in range(ti, len(toks)):
            t = toks[j]
            for take in range(min(len(t), len(m) - pos), 0, -1):
                if t.startswith(m[pos : pos + take]) and rec(pos + take, j + 1):
                    return True
        return False

    return rec(0, 0)


# --------------------------------------------------------------------------
# Model side (no LP)
# --------------------------------------------------------------------------


def model_cc_plants(hours: np.ndarray) -> tuple[pd.DataFrame, dict]:
    """Per-plant model CC capability over ``hours``, from the keeper bundle.

    Returns the plant frame (``plant_code``, ``plant``, ``zone``,
    ``plant_group``, ``pmax_mw``, ``avail_mw`` = the interval-mean of
    ``pmax x availability`` over ``hours``) and a totals block. No LP: the fleet
    is rebuilt by :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` with
    the fidelity guard asserted.
    """
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, meta = reconstruct_bundle_fleet(BUNDLE, YEAR, verbose=False)
    fa, fleet = state["fleet_arrays"], state["fleet"]
    pg = np.asarray([str(getattr(g, "plant_group", "") or "") for g in fleet])
    sel = np.flatnonzero(np.isin(pg, list(MODEL_CC_GROUPS)))
    pmax = np.asarray(fa.pmax, dtype=float)[sel]
    avail = np.asarray(fa.availability, dtype=float)[sel][:, hours]
    avail_mw = pmax[:, None] * avail  # (n, H)

    rows = []
    for k, i in enumerate(sel):
        g = fleet[i]
        rows.append(
            {
                "plant_code": int(g.plant_code),
                # The tranche name is "<plant> <tranche>"; the plant is the
                # name minus its trailing tranche token (assembly's convention).
                "plant": str(g.name).rsplit(" ", 1)[0],
                "zone": str(g.zone),
                "plant_group": str(g.plant_group),
                "pmax_mw": float(pmax[k]),
                "avail_mw": float(avail_mw[k].mean()),
            }
        )
    df = pd.DataFrame(rows)
    plants = (
        df.groupby(["plant_code", "plant", "zone", "plant_group"], as_index=False)
        .agg(pmax_mw=("pmax_mw", "sum"), avail_mw=("avail_mw", "sum"), n_rows=("pmax_mw", "size"))
        .sort_values("pmax_mw", ascending=False)
        .reset_index(drop=True)
    )
    totals = {
        "n_lp_rows": int(len(df)),
        "n_plants": int(len(plants)),
        "pmax_gw": round(float(plants["pmax_mw"].sum()) / 1e3, 4),
        "avail_gw": round(float(plants["avail_mw"].sum()) / 1e3, 4),
        "bundle": BUNDLE.name,
        "meta_keys": len(meta),
    }
    return plants, totals


def model_cc_dispatch(hours: np.ndarray) -> float:
    """Mean model CC (P1) dispatch MW over ``hours``, from the committed sidecar."""
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    tot = np.zeros(8760, dtype=float)
    for klass, d in ch.groupby("klass"):
        if str(klass) in MODEL_CC_GROUPS:
            tot += d.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0).to_numpy(float)
    return float(tot[hours].mean())


# --------------------------------------------------------------------------
# The crosswalk (precommit §1b)
# --------------------------------------------------------------------------


def published_spine() -> pd.DataFrame:
    """SCED CC site -> published network-model attributes (no judgement).

    ERCOT MIS NP4-160-SG: ``CCP_Resource_Names`` (the CC logical-resource
    universe) -> site mnemonic -> ``Resource_Node_to_Unit`` (``UNIT_SUBSTATION``,
    ``UNIT_NAME``) -> ``Settlement_Points`` (``SETTLEMENT_LOAD_ZONE``).
    """
    ccp = pd.read_csv(next(NETWORK.glob("CCP_Resource_Names_*.csv")))
    rn = pd.read_csv(next(NETWORK.glob("Resource_Node_to_Unit_*.csv")))
    sp = pd.read_csv(next(NETWORK.glob("Settlement_Points_*.csv")))
    ccp["site"] = ccp["CCP_NAME"].map(_site_of_train)

    units = (
        rn.groupby("UNIT_SUBSTATION")["UNIT_NAME"]
        .agg(lambda s: ";".join(sorted(set(map(str, s)))))
        .rename("unit_names")
    )
    subcol = "SUBSTATION" if "SUBSTATION" in sp.columns else None
    zcol = "SETTLEMENT_LOAD_ZONE" if "SETTLEMENT_LOAD_ZONE" in sp.columns else None
    zones = pd.Series(dtype=object)
    if subcol and zcol:
        zones = (
            sp.dropna(subset=[subcol, zcol])
            .groupby(subcol)[zcol]
            .agg(lambda s: ";".join(sorted(set(map(str, s)))))
            .rename("load_zone")
        )
    out = pd.DataFrame({"site": sorted(set(ccp["site"]))})
    out["unit_names"] = out["site"].map(units).fillna("")
    out["load_zone"] = out["site"].map(zones).fillna("")
    out["in_resource_node_file"] = out["site"].isin(set(rn["UNIT_SUBSTATION"]))
    return out


def committed_pairs() -> tuple[dict, dict]:
    """X1 — the two committed, hand-adjudicated crosswalk artifacts.

    Returns ``site -> plant_code`` and ``site -> evidence string`` for rows the
    repo has already accepted (``ercot-dam-plant-crosswalk.csv`` ``accepted=1``
    and every row of ``ercot_noncampd_dam_crosswalk.csv``).
    """
    site_to_plant: dict[str, int] = {}
    why: dict[str, str] = {}
    xw = pd.read_csv(XWALK)
    for _, r in xw[
        (xw["class"].astype(str).str.startswith("CC")) & (xw["accepted"] == 1)
    ].iterrows():
        site_to_plant[str(r["site"])] = int(r["plant_code"])
        why[str(r["site"])] = (
            f"X1 ercot-dam-plant-crosswalk.csv accepted=1 "
            f"({r['match_method']}, score {r['match_score']})"
        )
    nc = pd.read_csv(NONCAMPD)
    for _, r in nc.iterrows():
        for sp_name in str(r["dam_settlement_points"]).split(";"):
            s = _site_of_train(sp_name.strip())
            site_to_plant.setdefault(s, int(r["plant_code"]))
            why.setdefault(s, f"X1 ercot_noncampd_dam_crosswalk.csv ({r['confidence']})")
    return site_to_plant, why


def eia_plant_meta(codes: list[int]) -> pd.DataFrame:
    """EIA-860 ``County`` / ``City`` for the model's plant codes (E3 evidence).

    ``County`` is the admissible E3 field. ``City`` is read and reported ONLY as
    a disclosed near-miss diagnostic — the precommit admitted plant name and
    county, and the bar is not widened after measuring.
    """
    p = pd.read_parquet(EIA860_PLANT, columns=["Plant Code", "Plant Name", "County", "City"])
    p["Plant Code"] = pd.to_numeric(p["Plant Code"], errors="coerce")
    p = p[p["Plant Code"].isin(codes)].drop_duplicates("Plant Code")
    p["plant_code"] = p["Plant Code"].astype(int)
    return p[["plant_code", "Plant Name", "County", "City"]]


def build_crosswalk(
    plants: pd.DataFrame, sites: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict]]:
    """Assign SCED CC sites to model plants under the pre-registered tiers.

    Tiers are applied in order X1 -> X2 -> X3(E1/E2/E3); a model plant may take
    several sites (a plant whose trains ERCOT registers separately), but a site
    is assigned at most once. Everything unresolved stays ``SCED_ONLY`` /
    ``MODEL_ONLY`` / ``AMBIGUOUS`` and is reported at MW grain.
    """
    assign: dict[str, int] = {}
    tier: dict[str, str] = {}
    why: dict[str, str] = {}
    notes: list[dict] = []

    # ---- X1: committed artifacts -------------------------------------------
    x1, x1_why = committed_pairs()
    known = set(plants["plant_code"])
    for s, pc in x1.items():
        if s in set(sites["site"]) and pc in known:
            assign[s], tier[s], why[s] = pc, "X1", x1_why[s]

    # ---- X2: lexical identity on the published spine ------------------------
    meta = eia_plant_meta(plants["plant_code"].tolist()).set_index("plant_code")
    for _, srow in sites.iterrows():
        s = srow["site"]
        if s in assign:
            continue
        cands = []
        for _, prow in plants.iterrows():
            names = [prow["plant"]]
            nm = meta["Plant Name"].get(prow["plant_code"])
            if isinstance(nm, str):
                names.append(nm)
            if not any(_token_prefix_cover(s, n) for n in names):
                continue
            ratio = srow["cap_ref_mw"] / max(prow["pmax_mw"], 1e-9)
            if X2_RATIO[0] <= ratio <= X2_RATIO[1]:
                cands.append((prow["plant_code"], prow["plant"], ratio))
        if len(cands) == 1:
            pc, pname, ratio = cands[0]
            assign[s], tier[s] = int(pc), "X2"
            why[s] = f"X2 token-prefix cover of '{pname}', cap ratio {ratio:.2f}"
        elif len(cands) > 1:
            notes.append(
                {"site": s, "bucket": "AMBIGUOUS", "reason": "X2 multi-candidate",
                 "candidates": [c[1] for c in cands]}
            )

    # ---- X3: published-evidence adjudication --------------------------------
    # E2 -- UNIT_NAME set == the plant's EIA-860 generator-ID set (exact multiset)
    gens = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generators.parquet")
    gcol = "Generator ID" if "Generator ID" in gens.columns else None
    pcol = "Plant Code" if "Plant Code" in gens.columns else None
    gen_ids: dict[int, set] = {}
    if gcol and pcol:
        gens[pcol] = pd.to_numeric(gens[pcol], errors="coerce")
        for pc, d in gens[gens[pcol].isin(plants["plant_code"])].groupby(pcol):
            gen_ids[int(pc)] = {_norm(x) for x in d[gcol].astype(str)}

    taken = set(assign.values())
    for _, srow in sites.iterrows():
        s = srow["site"]
        if s in assign:
            continue
        uset = {_norm(u) for u in str(srow["unit_names"]).split(";") if u}
        hits = [pc for pc, g in gen_ids.items() if g and uset and g == uset]
        if len(hits) == 1:
            assign[s], tier[s] = int(hits[0]), "X3/E2"
            why[s] = f"X3/E2 UNIT_NAME set == EIA-860 generator-ID set {sorted(uset)}"
            continue
        # E3 -- substation name is a normalised sub/superstring of the EIA plant
        # name or of its EIA-860 county
        e3 = []
        for _, prow in plants.iterrows():
            pc = int(prow["plant_code"])
            if pc in taken:
                continue
            county = str(meta["County"].get(pc, "") or "")
            targets = [prow["plant"], str(meta["Plant Name"].get(pc, "") or ""), county]
            ns = _norm(s)
            if any(nt and (ns in _norm(t) or _norm(t) in ns) for t in targets for nt in [_norm(t)]):
                ratio = srow["cap_ref_mw"] / max(prow["pmax_mw"], 1e-9)
                if X2_RATIO[0] <= ratio <= X2_RATIO[1]:
                    e3.append((pc, prow["plant"], ratio))
        if len(e3) == 1:
            pc, pname, ratio = e3[0]
            assign[s], tier[s] = int(pc), "X3/E3"
            why[s] = f"X3/E3 substation-name identity with '{pname}', cap ratio {ratio:.2f}"
            taken.add(pc)
            continue
        # E1 -- qse + capacity window + zone agreement leave exactly one plant
        e1 = []
        for _, prow in plants.iterrows():
            pc = int(prow["plant_code"])
            if pc in taken:
                continue
            if str(prow["zone"]) != str(srow["zone_xwalk"]):
                continue
            ratio = srow["cap_ref_mw"] / max(prow["pmax_mw"], 1e-9)
            if E1_RATIO[0] <= ratio <= E1_RATIO[1]:
                e1.append((pc, prow["plant"], ratio))
        if len(e1) == 1:
            pc, pname, ratio = e1[0]
            assign[s], tier[s] = int(pc), "X3/E1"
            why[s] = (
                f"X3/E1 unique survivor in zone {srow['zone_xwalk']} at cap ratio "
                f"{ratio:.2f} (qse {srow['qse']})"
            )
            taken.add(pc)
        elif len(e1) > 1:
            notes.append(
                {"site": s, "bucket": "AMBIGUOUS", "reason": "E1 multi-survivor",
                 "candidates": [c[1] for c in e1]}
            )
        else:
            notes.append({"site": s, "bucket": "SCED_ONLY", "reason": "no admissible evidence"})

    sites = sites.copy()
    sites["plant_code"] = sites["site"].map(assign)
    sites["tier"] = sites["site"].map(tier).fillna("")
    sites["evidence"] = sites["site"].map(why).fillna("")
    return sites, notes


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from scripts.lib import sced_corpus_instruments as sci

    t0 = time.time()
    gap = np.array(
        sorted(int(h) for h in json.loads(PHASE0_JSON.read_text())["hour_set"]["hours"])
    )

    # ---- the two sides ------------------------------------------------------
    plants, mtot = model_cc_plants(gap)
    d_m = model_cc_dispatch(gap)
    census = sci.capability_census(YEAR, gap)

    trains = pd.DataFrame(census["trains"]).T.reset_index().rename(columns={"index": "train"})
    for c in ("cap_ref_mw", "hsl_mw", "hasl_mw", "basepoint_mw", "hsl_mw_out"):
        trains[c] = pd.to_numeric(trains[c], errors="coerce").fillna(0.0)
    trains["site"] = trains["train"].map(_site_of_train)
    sites = (
        trains.groupby("site", as_index=False)[
            ["cap_ref_mw", "hsl_mw", "hasl_mw", "basepoint_mw", "hsl_mw_out"]
        ]
        .sum()
        .sort_values("cap_ref_mw", ascending=False)
    )

    spine = published_spine()
    sites = sites.merge(spine, on="site", how="left")
    xw = pd.read_csv(XWALK)
    xw_cc = xw[xw["class"].astype(str).str.startswith("CC")].drop_duplicates("site")
    sites = sites.merge(
        xw_cc[["site", "zone", "qse"]].rename(columns={"zone": "zone_xwalk"}),
        on="site",
        how="left",
    )
    sites["zone_xwalk"] = sites["zone_xwalk"].fillna("Unknown")
    sites["qse"] = sites["qse"].fillna("")
    sites["unit_names"] = sites["unit_names"].fillna("")

    # ---- the attribution identity (precommit §1c) ---------------------------
    C_m = float(plants["avail_mw"].sum())
    H_r = float(sites["hsl_mw"].sum())
    C_r = float(sites["hasl_mw"].sum())
    D_r = float(sites["basepoint_mw"].sum())
    A = C_m - H_r
    B = H_r - C_r
    C = d_m - D_r
    lhs = (C_m - d_m) - (C_r - D_r)
    identity_err_gw = abs(lhs - (A + B - C)) / 1e3

    # ---- the crosswalk ------------------------------------------------------
    sites, notes = build_crosswalk(plants, sites)
    matched = sites[sites["plant_code"].notna()].copy()
    matched["plant_code"] = matched["plant_code"].astype(int)
    per_plant = matched.groupby("plant_code", as_index=False).agg(
        sced_cap_ref_mw=("cap_ref_mw", "sum"),
        sced_hsl_mw=("hsl_mw", "sum"),
        n_sites=("site", "size"),
        sites=("site", lambda s: ";".join(sorted(s))),
        tiers=("tier", lambda s: ";".join(sorted(set(s)))),
    )
    pl = plants.merge(per_plant, on="plant_code", how="left")
    for c in ("sced_cap_ref_mw", "sced_hsl_mw", "n_sites"):
        pl[c] = pl[c].fillna(0.0)
    pl["sites"] = pl["sites"].fillna("")
    pl["tiers"] = pl["tiers"].fillna("")
    pl["matched"] = pl["n_sites"] > 0
    pl["term_a_mw"] = pl["avail_mw"] - pl["sced_hsl_mw"]

    amb_sites = {n["site"] for n in notes if n["bucket"] == "AMBIGUOUS"}
    amb_plants = {c for n in notes if n["bucket"] == "AMBIGUOUS" for c in n.get("candidates", [])}
    pl["bucket"] = np.where(
        ~pl["matched"],
        np.where(pl["plant"].isin(amb_plants), "AMBIGUOUS", "A_absent"),
        np.where(pl["term_a_mw"] >= 0, "A_derate", "A_short"),
    )

    sced_only = sites[sites["plant_code"].isna() & ~sites["site"].isin(amb_sites)]
    sced_amb = sites[sites["plant_code"].isna() & sites["site"].isin(amb_sites)]

    buckets = {
        "A_absent": float(pl.loc[pl["bucket"] == "A_absent", "term_a_mw"].sum()),
        "A_derate": float(pl.loc[pl["bucket"] == "A_derate", "term_a_mw"].sum()),
        "A_short": float(pl.loc[pl["bucket"] == "A_short", "term_a_mw"].sum()),
        "A_ambiguous": float(pl.loc[pl["bucket"] == "AMBIGUOUS", "term_a_mw"].sum()),
        "A_sced_only": -float(sced_only["hsl_mw"].sum() + sced_amb["hsl_mw"].sum()),
    }
    A_named = buckets["A_absent"] + buckets["A_derate"] + buckets["A_short"]

    # ---- the pre-registered licence + decision rule (precommit §§1b/2) ------
    sced_total = float(sites["cap_ref_mw"].sum())
    l1 = float(matched["cap_ref_mw"].sum()) / max(sced_total, 1e-9)
    l2 = float(pl.loc[pl["bucket"] == "AMBIGUOUS", "pmax_mw"].sum()) / max(
        float(pl["pmax_mw"].sum()), 1e-9
    )
    a_dom = A / max(lhs, 1e-9)
    a_named_share = A_named / max(A, 1e-9)

    if identity_err_gw > IDENTITY_TOL_GW:
        verdict = "CONSTRUCTION-ERROR"
    elif l1 < L1_SCED_CLOSURE or l2 > L2_AMBIGUITY_BUDGET:
        verdict = "FILED-UNLICENSED"
    elif a_dom < A_DOMINANCE_BAR:
        verdict = "REDIRECTED"
    elif a_named_share >= A_NAMED_BAR:
        verdict = "ACTIONABLE"
    else:
        verdict = "FILED-NULL"

    # ---- the all-hours control (precommit §1: reported, NON-GATING) ---------
    allh = np.arange(8760)
    plants_all, _ = model_cc_plants(allh)
    census_all = sci.capability_census(YEAR, allh)
    tr_all = pd.DataFrame(census_all["trains"]).T
    control = {
        "hours": 8760,
        "C_m_model_available_gw": round(float(plants_all["avail_mw"].sum()) / 1e3, 4),
        "D_m_model_dispatch_gw": round(model_cc_dispatch(allh) / 1e3, 4),
        "H_r_reality_hsl_gw": round(float(census_all["totals"]["hsl_mw"]) / 1e3, 4),
        "C_r_reality_hasl_gw": round(float(census_all["totals"]["hasl_mw"]) / 1e3, 4),
        "D_r_reality_basepoint_gw": round(
            float(census_all["totals"]["basepoint_mw"]) / 1e3, 4
        ),
        "n_intervals": census_all["n_intervals"],
        "note": "NON-GATING control (precommit §1). Verdict is scored on the gap hours.",
    }
    control["A_capability_gw"] = round(
        control["C_m_model_available_gw"] - control["H_r_reality_hsl_gw"], 4
    )
    control["B_as_reservation_gw"] = round(
        control["H_r_reality_hsl_gw"] - control["C_r_reality_hasl_gw"], 4
    )
    control["C_dispatch_diff_gw"] = round(
        control["D_m_model_dispatch_gw"] - control["D_r_reality_basepoint_gw"], 4
    )
    control["gap_U_m_minus_U_r_gw"] = round(
        (control["C_m_model_available_gw"] - control["D_m_model_dispatch_gw"])
        - (control["C_r_reality_hasl_gw"] - control["D_r_reality_basepoint_gw"]),
        4,
    )
    _ = tr_all  # kept for provenance of the per-train all-hours read

    # ---- post-measurement adjudication (§"reported against interest") ------
    # The pre-registered X3/E1 and X3/E3 tiers are RETRACTED by inspection in
    # session. Cause: E1's "zone agreement" leg consumes the ``zone`` column of
    # ``ercot-dam-plant-crosswalk.csv``, which is the UNACCEPTED auto-matcher's
    # PROPOSED PLANT's zone -- not the site's own zone. The published spine
    # falsifies it directly (FRNYPP zone_xwalk South_Central vs published
    # LZ_NORTH; CBEC North vs LZ_SOUTH; TGCCS Northeast vs LZ_NORTH), and the
    # resulting matches are wrong on their face (Paris Energy Center <- the
    # Ingleside cogen site; Wolf Hollow II <- DDPEC; Magic Valley <- PANDA_S).
    # Retracting them LOWERS L1 (0.5111 -> the X1+X2 value), i.e. it moves the
    # verdict FURTHER from its bar, never toward it -- the only direction in
    # which a post-measurement change to a pre-registered rule is admissible.
    defensible = sites[sites["tier"].isin(["X1", "X2"])]
    l1_defensible = float(defensible["cap_ref_mw"].sum()) / max(sced_total, 1e-9)

    # X2's ceiling: sites carrying a token-prefix cover that failed ONLY the
    # pre-registered capacity window. Reported because that window conditions on
    # the very quantity being measured (a plant the model over-rates fails the
    # ratio test and is pushed from A_derate into A_absent), so it can only
    # understate A_derate. The window is NOT moved.
    meta2 = eia_plant_meta(plants["plant_code"].tolist()).set_index("plant_code")
    ratio_blocked = []
    for _, srow in sites[sites["tier"] == ""].iterrows():
        for _, prow in plants.iterrows():
            names = [prow["plant"], str(meta2["Plant Name"].get(int(prow["plant_code"]), "") or "")]
            if any(_token_prefix_cover(srow["site"], n) for n in names if n):
                ratio_blocked.append(
                    {
                        "site": srow["site"],
                        "plant": prow["plant"],
                        "cap_ratio": round(
                            float(srow["cap_ref_mw"]) / max(float(prow["pmax_mw"]), 1e-9), 3
                        ),
                        "sced_cap_ref_mw": round(float(srow["cap_ref_mw"]), 1),
                        "model_pmax_mw": round(float(prow["pmax_mw"]), 1),
                    }
                )

    # Grain artifact: a MATCHED plant whose |term A| would be explained by ONE
    # unmatched sibling site. This is the site-grain crosswalk failing to hold a
    # plant ERCOT registers as several sites -- not a capability excess.
    unmatched_caps = sites.loc[sites["tier"] == "", ["site", "cap_ref_mw", "hsl_mw"]]
    grain = []
    for _, r in pl[pl["matched"] & (pl["term_a_mw"].abs() >= 100.0)].iterrows():
        for _, u in unmatched_caps.iterrows():
            newratio = (r["sced_cap_ref_mw"] + u["cap_ref_mw"]) / max(r["pmax_mw"], 1e-9)
            if E1_RATIO[0] <= newratio <= E1_RATIO[1]:
                grain.append(
                    {
                        "plant": r["plant"],
                        "term_a_mw": round(float(r["term_a_mw"]), 1),
                        "sibling_site_would_close": u["site"],
                        "cap_ratio_with_sibling": round(float(newratio), 3),
                    }
                )

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot170_cc_headroom_phase0.py",
            "session": "ercot-170 Phase 0 (no LP, no solve, keeper unchanged)",
            "keeper": "2026-08-05-run168b-year-curves",
            "bundle": BUNDLE.name,
            "precommit": "docs/PRECOMMIT-ercot170-cc-headroom-crosswalk-2026-08-05.md",
            "year": YEAR,
            "hour_set": f"committed top-{len(gap)} 2023 gap hours ({PHASE0_JSON.name})",
            "n_intervals": census["n_intervals"],
            "row_filter": census["row_filter"],
            "elapsed_s": None,
        },
        "model_totals": mtot,
        "identity": {
            "C_m_model_available_gw": round(C_m / 1e3, 4),
            "D_m_model_dispatch_gw": round(d_m / 1e3, 4),
            "H_r_reality_hsl_gw": round(H_r / 1e3, 4),
            "C_r_reality_hasl_gw": round(C_r / 1e3, 4),
            "D_r_reality_basepoint_gw": round(D_r / 1e3, 4),
            "U_m_gw": round((C_m - d_m) / 1e3, 4),
            "U_r_gw": round((C_r - D_r) / 1e3, 4),
            "gap_U_m_minus_U_r_gw": round(lhs / 1e3, 4),
            "A_capability_gw": round(A / 1e3, 4),
            "B_as_reservation_gw": round(B / 1e3, 4),
            "C_dispatch_diff_gw": round(C / 1e3, 4),
            "identity_error_gw": round(identity_err_gw, 6),
            "identity_tol_gw": IDENTITY_TOL_GW,
        },
        "crosswalk": {
            "n_sced_sites": int(len(sites)),
            "n_matched_sites": int(len(matched)),
            "by_tier": matched["tier"].value_counts().to_dict(),
            "sced_cap_ref_gw": round(sced_total / 1e3, 4),
            "matched_cap_ref_gw": round(float(matched["cap_ref_mw"].sum()) / 1e3, 4),
            "L1_sced_closure": round(l1, 4),
            "L1_bar": L1_SCED_CLOSURE,
            "L1_pass": bool(l1 >= L1_SCED_CLOSURE),
            "L2_ambiguity_share": round(l2, 4),
            "L2_bar": L2_AMBIGUITY_BUDGET,
            "L2_pass": bool(l2 <= L2_AMBIGUITY_BUDGET),
            "L3_zone_frame": "REPORTED, NOT A GATE (precommit §1b)",
            "notes": notes,
        },
        "attribution": {
            "buckets_gw": {k: round(v / 1e3, 4) for k, v in buckets.items()},
            "A_named_gw": round(A_named / 1e3, 4),
            "A_named_share_of_A": round(a_named_share, 4),
            "A_share_of_gap": round(a_dom, 4),
            "bars": {
                "A_dominance": A_DOMINANCE_BAR,
                "A_named": A_NAMED_BAR,
            },
        },
        "all_hours_control": control,
        "post_measurement_adjudication": {
            "retracted_tiers": ["X3/E1", "X3/E3"],
            "cause": (
                "E1's zone-agreement leg consumes ercot-dam-plant-crosswalk.csv's "
                "`zone`, which is the UNACCEPTED auto-matcher's PROPOSED PLANT's "
                "zone, not the site's own. The published SETTLEMENT_LOAD_ZONE "
                "falsifies it directly and the resulting matches are wrong on "
                "their face."
            ),
            "direction": (
                "RETRACTION LOWERS L1 (further from its bar), the only direction "
                "in which a post-measurement change to a pre-registered rule is "
                "admissible; the verdict is unchanged and strengthened."
            ),
            "L1_as_preregistered": round(l1, 4),
            "L1_defensible_tiers_only": round(l1_defensible, 4),
            "defensible_matched_cap_ref_gw": round(
                float(defensible["cap_ref_mw"].sum()) / 1e3, 4
            ),
            "x2_ratio_window_blocked": ratio_blocked,
            "grain_artifacts": grain,
            "class_split_licensed": {
                "model_cc_regular_pmax_gw": round(
                    float(pl.loc[pl["plant_group"] == "CC_REGULAR", "pmax_mw"].sum()) / 1e3, 4
                ),
                "model_cc_regular_avail_gw": round(
                    float(pl.loc[pl["plant_group"] == "CC_REGULAR", "avail_mw"].sum()) / 1e3, 4
                ),
                "model_cc_chp_pmax_gw": round(
                    float(pl.loc[pl["plant_group"] == "CC_CHP", "pmax_mw"].sum()) / 1e3, 4
                ),
                "model_cc_chp_avail_gw": round(
                    float(pl.loc[pl["plant_group"] == "CC_CHP", "avail_mw"].sum()) / 1e3, 4
                ),
                "sced_hsl_minus_model_cc_regular_avail_gw": round(
                    (H_r - float(pl.loc[pl["plant_group"] == "CC_REGULAR", "avail_mw"].sum()))
                    / 1e3,
                    4,
                ),
            },
        },
        "verdict": verdict,
        "plants": pl.sort_values("term_a_mw", ascending=False).round(3).to_dict("records"),
        "sites": sites.sort_values("cap_ref_mw", ascending=False).round(3).to_dict("records"),
    }
    out["_provenance"]["elapsed_s"] = round(time.time() - t0, 1)
    args.out.write_text(json.dumps(out, indent=1))

    print(json.dumps(out["identity"], indent=1))
    print(json.dumps(out["crosswalk"]["by_tier"], indent=1))
    print(
        f"L1 {l1:.4f} (bar {L1_SCED_CLOSURE}) | L2 {l2:.4f} (bar {L2_AMBIGUITY_BUDGET}) | "
        f"A/gap {a_dom:.4f} | A_named/A {a_named_share:.4f}"
    )
    print("VERDICT:", verdict)
    print(f"wrote {args.out} ({out['_provenance']['elapsed_s']} s)")


if __name__ == "__main__":
    main()
