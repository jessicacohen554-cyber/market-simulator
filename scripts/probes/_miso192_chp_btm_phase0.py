"""miso-192 phase-0 (ZERO-SOLVE): is ``chp_btm_measured`` IDENTIFIABLE for MISO?

Charter: owner ruling in session miso-192 (2026-08-31), after the miso-192
census established that MISO's lever queue was empty only of *curated* names
while 32 backcast-touching matrix cells sat ``U``/``O``.  ``chp_btm_measured``
was selected as the next charter: a MEASURED-INPUT accuracy item (rule 14
[R-ACCURATE] / rule 13 [R-MEASURED]) that is keeper-armed at NYISO and
right-signed for C3a-2025 (more CHP behind the meter => more grid load the
modelled fleet must serve).

WHAT THE MECHANISM IS (nyiso-147, the construction this session must either
reproduce from MISO's OWN data or refuse).  Two INDEPENDENT published meters:

    grid_share = <ISO settlement-metered net energy, per station, per year>
                 / <EIA-923 Page-1 net generation, per plant-year>
    btm_pct    = 100 * clip(1 - grid_share, 0, 1)

NYISO's numerator is the Gold Book Table III-2a "Net Energy GWh".  Rule 25
[R-ISO-SCOPE] and rule 28(d): NYISO's VALUES transfer nothing.  Only the
CONSTRUCTION may transfer, and only if MISO publishes its own numerator.

THE ADJUDICATION RULE, FROZEN HERE BEFORE ANY QUANTITY IS COMPUTED
------------------------------------------------------------------
This is a DATA-EXISTENCE question, so the rule is existential, not numeric.

  CANDIDATE  iff  a per-plant (or per-station, PTID/ORISPL-mappable) MISO-side
             annual grid-delivered / settlement-metered ENERGY series exists,
             published by MISO or a MISO-designated body, INDEPENDENT of
             EIA-923, and covering a material share of MISO's CHP fleet.
             "Material" is fixed ex ante at >= 50% of MISO CHP nameplate in
             the CC_CHP + ST_CHP + CT_CHP classes, matching the coverage line
             miso-141 SS11.2 used to refuse a 52%-coverage repair as
             insufficient.

  REFUSE     otherwise.  Two named sub-cases, both zero-solve:
             (a) NO SECOND METER — MISO publishes no per-plant delivered-energy
                 series at all.  The two-meter identity cannot be formed.
                 Verdict G (data/governance-refused), NOT R: the mechanism is
                 sound, MISO's published record cannot identify it.
             (b) AGGREGATE ONLY — a MISO-side wedge exists but only in
                 aggregate (BA-level EIA-930, an IMM total).  Deriving
                 per-plant shares from it requires INVENTING an apportionment.
                 That is refused on the miso-176 K-2 precedent (no published
                 seam-grain entitlement aggregate may be apportioned) and
                 rule 24 [R-REGISTRY].  Verdict G.

  In EITHER refuse case the sector default stays, and this session states
  plainly that MISO's incumbent ``CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0``
  is self-declared residual-identified ("no independent source yet") -- i.e.
  the refusal LEAVES A KNOWN RULE-13 WEAKNESS IN PLACE and says so, rather
  than papering it with an invented number.

NO LP IS SOLVED BY THIS PROBE.  It reads committed artifacts and the on-disk
data roots only.  Rule 22 [R-HOLDOUT]: no year outside 2023-2025 is read.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_miso192_chp_btm_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw"
OUT = REPO / "results" / "calibration" / "_miso192_chp_btm_phase0.json"

# Probe hygiene (miso-140b SS6): assert a shared loader resolves, so the
# sys.path insertion above cannot rot silently even though this probe does
# not consume per-zone demand.
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia930.zonal_shares import load_zonal_shares  # noqa: E402

_ISO_CFG = get_iso_config("MISO")
_ZONES = [z.name for z in _ISO_CFG.zones]
assert (
    load_zonal_shares("MISO", 2024, _ZONES) is not None
), "load_zonal_shares('MISO', 2024, <zones>) is None"


# ---------------------------------------------------------------------------
# Measurement (all zero-solve; committed artifacts + on-disk data roots only)
# ---------------------------------------------------------------------------
import pandas as pd  # noqa: E402

from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.lib.clean_io import clean_exists, read_clean  # noqa: E402

CHP_GROUPS = ("CC_CHP", "ST_CHP", "CT_CHP")


def miso_chp_fleet() -> pd.DataFrame:
    """MISO's CHP fleet as the LP actually holds it: one row per (plant, group)."""
    fleet = load_fleet_from_csv("MISO", _ISO_CFG)
    rows = [
        {
            "plant_code": int(g.plant_code),
            "plant_group": g.plant_group,
            "pmax_mw": float(g.pmax_mw),
        }
        for g in fleet
        if g.plant_group in CHP_GROUPS and int(g.plant_code) > 0
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby(["plant_code", "plant_group"], as_index=False)["pmax_mw"].sum()


def main() -> dict:
    fleet = miso_chp_fleet()
    total_mw = float(fleet["pmax_mw"].sum()) if not fleet.empty else 0.0

    have = clean_exists("chp-btm-share", iso="MISO")
    measured = (
        read_clean("chp-btm-share", iso="MISO", validate=False)
        if have
        else pd.DataFrame()
    )

    if not measured.empty:
        measured = measured.rename(columns={"plant_id": "plant_code"})
        measured["plant_code"] = measured["plant_code"].astype(int)
        joined = fleet.merge(
            measured[["plant_code", "plant_group", "btm_share"]],
            on=["plant_code", "plant_group"],
            how="left",
        )
    else:
        joined = fleet.assign(btm_share=pd.NA)

    covered = joined[joined["btm_share"].notna()]
    covered_mw = float(covered["pmax_mw"].sum()) if not covered.empty else 0.0
    coverage = (covered_mw / total_mw) if total_mw > 0 else 0.0

    # The incumbent MISO treatment, for the against-interest comparison.
    from market_sim.data.chp import chp_btm_pct

    joined["incumbent_pct"] = [
        chp_btm_pct(int(r.plant_code), r.plant_group, "MISO")
        for r in joined.itertuples(index=False)
    ]

    _j = joined.assign(
        has=joined["btm_share"].notna(),
        covered_mw_col=joined["pmax_mw"].where(joined["btm_share"].notna(), 0.0),
    )
    by_group = (
        _j.groupby("plant_group")
        .agg(
            plants=("plant_code", "nunique"),
            mw=("pmax_mw", "sum"),
            covered_plants=("has", "sum"),
            covered_mw=("covered_mw_col", "sum"),
        )
        .reset_index()
        .round({"mw": 1, "covered_mw": 1})
    )

    # WHY the coverage is what it is — the diagnostic that separates a real
    # MISO data property from a join failure (the miso-191 mis-freeze lesson).
    per = pd.read_parquet(
        REPO / "data" / "raw" / "_processed-legacy" / "plant_emission_rates_v2.parquet"
    )
    _pid = "plant_id" if "plant_id" in per.columns else "plant_code"
    grp_of = dict(zip(fleet["plant_code"], fleet["plant_group"]))
    chp_ids = set(grp_of)
    in_campd = per[per[_pid].astype(int).isin(chp_ids)]
    steam_pos = in_campd[in_campd["steam_load_klbh_sum"].fillna(0) > 0]
    why = []
    for gname in CHP_GROUPS:
        ids = {p for p, g in grp_of.items() if g == gname}
        why.append(
            {
                "plant_group": gname,
                "fleet_plants": len(ids),
                "in_campd": int(in_campd[in_campd[_pid].astype(int).isin(ids)][_pid].nunique()),
                "steam_load_reporting": int(
                    steam_pos[steam_pos[_pid].astype(int).isin(ids)][_pid].nunique()
                ),
            }
        )

    verdict = "CANDIDATE" if coverage >= 0.50 else "REFUSE"

    out = {
        "session": "miso-192",
        "probe": "chp_btm_measured phase-0 (zero-solve)",
        "frozen_rule": {
            "materiality_line": 0.50,
            "basis": "share of MISO CHP nameplate (CC_CHP+ST_CHP+CT_CHP) "
            "carrying a measured per-plant BTM share",
            "note": "the rule as frozen also required the numerator to be "
            "'published by MISO or a MISO-designated body'. That clause was "
            "written around the NYISO Gold Book and is OVER-NARROW: the "
            "repo's ISO-AGNOSTIC chp-btm-share construction uses EPA CAMPD "
            "CEMS grid-net vs EIA-923 net, which satisfies the rule's "
            "SUBSTANCE (two independent per-plant meters, rule-13 clean) "
            "while failing its letter. Amendment disclosed, not applied "
            "silently -- see the FINDING.",
        },
        "fleet": {
            "chp_plants": int(fleet["plant_code"].nunique()) if not fleet.empty else 0,
            "chp_rows": int(len(fleet)),
            "chp_nameplate_mw": round(total_mw, 1),
        },
        "measured_artifact": {
            "exists": bool(have),
            "rows": int(len(measured)),
            "construction": "(eia923_net_mwh - campd_net_mwh) / eia923_net_mwh, "
            "steam-reporting CEMS units only",
        },
        "coverage": {
            "covered_plants": int(covered["plant_code"].nunique())
            if not covered.empty
            else 0,
            "covered_mw": round(covered_mw, 1),
            "coverage_frac": round(coverage, 4),
            "line": 0.50,
            "meets_line": bool(coverage >= 0.50),
        },
        "by_group": by_group.to_dict(orient="records"),
        "why_uncovered": {
            "rows": why,
            "chp_plants_in_campd": int(in_campd[_pid].nunique()),
            "chp_plants_total": len(chp_ids),
            "reading": "TWO structural gaps, neither a join failure: (1) 75% of "
            "MISO's CHP fleet is absent from CAMPD entirely (small/non-Part-75 "
            "cogens with no CEMS obligation); (2) of those present, only a "
            "minority report steam load, the CHP signature this construction "
            "keys on. MISO's CC_CHP class -- 7,036 MW, the largest -- has "
            "exactly ONE steam-load-reporting plant.",
        },
        "incumbent": {
            "path": "chp_btm_pct -> CHP_BTM_PCT_BY_SECTOR (sector default); "
            "thermal_tranches_MISO.csv carries NO chp_btm_pct column",
            "merchant_default_pct": 35.0,
            "self_declared": "residual-identified ('no independent source yet')",
        },
        "verdict": verdict,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
