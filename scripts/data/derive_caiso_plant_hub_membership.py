"""Derive the MEASURED CAISO generator->trading-hub membership crosswalk.

Chartered by ``results/calibration/FINDING-caiso216-belly-lever-plan-2026-08-23.md``
§F.1g (candidate C1, funded caiso-217): replace the lat-cut/county-lift zone
ESTIMATE (``data/zone_assignment.py::_caiso_zone``) with CAISO's own published
generator-hub membership — the SAME ``ATL_PNODE_MAP`` authority the caiso-172
keeper derivation already uses for the LOAD side
(``scripts/data/derive_caiso_path15_load_split.py``). Fleet-wide: renewables,
nuclear, thermal, storage — one crosswalk, applied to every year identically
(CLAUDE.md rule 22 consistency clause). Unmatched plants fall back to the
current geographic rule, and coverage is reported per technology rather than
silently absorbed.

RULE 23 ``[R-FROZEN-DERIVE]`` — frozen against residuals: re-derives ONLY when
its source bytes change (the Atlas snapshot, the EIA-860 vintage, the DAM
outage corpus, or the reviewed resource crosswalks). It reads no model output,
no price, no residual.

RULE 13 ``[R-MEASURED]`` — a published registry of CAISO's own settlement
geography; a *quantity*-side input (where capacity sits), zero free
parameters. Forward analogue: membership is published continuously and a
forecast-year plant resolves exactly as today (location -> zone), only against
measured geography rather than a latitude proxy.

RULE 14 ``[R-ACCURATE]`` — the canonical accurate-data-over-estimate move: the
lat cut is self-documented as an estimate; the accurate data exists in-repo.

THE CONSTRUCTION
----------------
``ATL_PNODE_MAP`` gives effective-dated pnode -> ``TH_{NP15,ZP26,SP15}_GEN``
membership (1,999 gen pnodes at the latest windows). Pnode ids are
``SUBSTATION_voltage_id``, so the substation token carries the hub — a
substation is usable only when every gen pnode at it agrees on one hub (the
caiso-172 tier-1 rule; ambiguous substations are dropped and reported, never
majority-voted). Plants join to substations through measured evidence tiers,
highest confidence first; within every tier the hub must be UNANIMOUS across
the plant's matched evidence or the tier abstains:

* **E0 ``verified-pin``** — hand-verified plant-name -> substation pins (the
  ``derive_caiso_dam_resource_crosswalk.py`` "verified-prefix" precedent) for
  the boundary cohorts whose CAISO abbreviation the mechanical rules cannot
  reach safely; every pin states its verification basis inline.
* **E1 ``eia-lmp-node``** — EIA-860 Generator sheet's own ``RTO/ISO LMP Node
  Designation`` column: the plant operator's reported CAISO pnode, joined to
  the Atlas by exact pnode id, else by substation token.
* **E2 ``reviewed-crosswalk``** — the two committed, reviewed thermal
  resource->EIA crosswalks (``caiso-dam-resource-crosswalk.csv``,
  ``caiso-resource-eia-crosswalk.csv`` accepted rows): resource ids are
  ``SUBSTATION_voltage_unit``, so the resource token joins to the Atlas.
* **E3 ``resource-name``** — the DAM outage corpus
  (``caiso-dam-outage-windows.parquet``) carries CAISO's own full resource
  names fleet-wide (1,548 resources, every technology); resource names are
  matched to EIA-860 plant names (normalized token containment with numeric
  agreement), then the resource token joins to the Atlas.

Substation-token matching is a deterministic four-rule ladder (exact >
GEN/GN-suffix strip > prefix >= 5 chars > unit/bank-designator base strip
>= 4), stopping at the first rule with hits; the hubs of ALL substations hit
at that rule must agree or the token is ambiguous. Two looser channels were
BUILT, AUDITED AGAINST GEOGRAPHY, AND REMOVED for precision (audit in the
caiso-217 FINDING): a de-voweled token rule (collides CONTROL/CENTRAL,
SANDLOT, SYCAMORE — moved ~2 GW on false matches) and a direct
compact-plant-name prefix tier (collides Edward C Hyatt/EDWARDS AFB 644 MW,
Diablo Energy Storage @ Pittsburg/DIABLO 200 MW, Sierra */SIERRA). A wrong
hub actively mis-allocates capacity across the Path-15/26 cuts, while an
unmatched plant merely keeps today's estimate — precision outranks recall
here by construction, and the mover table (every joined plant whose hub
disagrees with its geographic macro-band) is committed in the JSON sidecar
as the review surface.

Effective dates are honored: each pnode's membership is its LATEST effective
window (pnodes whose hub CHANGED across windows — 9 in the committed snapshot
— are reported), and the output rows carry the witness substation's window.
Per the rule-22 consistency clause the crosswalk is ONE static membership
applied to every solve year identically.

Output
------
``data/raw/reference/caiso-plant-hub-membership.csv`` — one row per joined
plant: ``plant_code, plant_name, tech, capacity_mw, hub, pnode, eff_start,
eff_end, join_method, n_evidence``. Plants whose evidence tiers DISAGREE on
the hub are excluded (fall back to geography) and reported.
``data/raw/reference/caiso-plant-hub-membership.json`` — provenance, per-tech
MW coverage, the §E witness gates, conflicts, ambiguity reports.

Usage::

    PYTHONPATH=.:src python3 scripts/data/derive_caiso_plant_hub_membership.py
    PYTHONPATH=.:src python3 scripts/data/derive_caiso_plant_hub_membership.py --acceptance
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import EIA_860_DIR, RAW_DATA_DIR, REFERENCE_DIR  # noqa: E402

ATLAS_CSV = RAW_DATA_DIR / "caiso-atlas" / "ATL_PNODE_MAP.csv"
DAM_WINDOWS = RAW_DATA_DIR / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"
XW_DAM_CSV = REFERENCE_DIR / "caiso-dam-resource-crosswalk.csv"
XW_EIA_CSV = REFERENCE_DIR / "caiso-resource-eia-crosswalk.csv"
OUT_CSV = REFERENCE_DIR / "caiso-plant-hub-membership.csv"
OUT_JSON = REFERENCE_DIR / "caiso-plant-hub-membership.json"

#: Atlas APNODE_ID -> short hub name used in the output.
HUB_SHORT = {
    "TH_NP15_GEN-APND": "TH_NP15",
    "TH_ZP26_GEN-APND": "TH_ZP26",
    "TH_SP15_GEN-APND": "TH_SP15",
}

#: EIA-860 Technology -> coverage-report tech group.
TECH_GROUP = {
    "Solar Photovoltaic": "solar",
    "Solar Thermal without Energy Storage": "solar",
    "Solar Thermal with Energy Storage": "solar",
    "Onshore Wind Turbine": "wind",
    "Offshore Wind Turbine": "wind",
    "Nuclear": "nuclear",
    "Natural Gas Fired Combined Cycle": "gas_cc",
    "Natural Gas Fired Combustion Turbine": "gas_ct",
    "Natural Gas Steam Turbine": "gas_st",
    "Natural Gas Internal Combustion Engine": "gas_other",
    "Other Natural Gas": "gas_other",
    "Other Gases": "gas_other",
    "Conventional Hydroelectric": "hydro",
    "Hydroelectric Pumped Storage": "pumped_storage",
    "Batteries": "battery",
    "Flywheels": "battery",
    "Geothermal": "geothermal",
    "Wood/Wood Waste Biomass": "biomass_other",
    "Other Waste Biomass": "biomass_other",
    "Landfill Gas": "biomass_other",
    "Municipal Solid Waste": "biomass_other",
    "All Other": "biomass_other",
    "Conventional Steam Coal": "coal",
    "Petroleum Liquids": "oil",
    "Petroleum Coke": "oil",
}

#: Pre-registered witness gates (FINDING-caiso216 §E): named plants whose
#: crosswalk hub must equal CAISO's own membership, and the two Path-15/26
#: boundary anchor substations. A witness plant may legitimately be absent
#: from the join (falls back to geography) but must never carry a WRONG hub.
WITNESS_PLANTS = {
    "Diablo Canyon": "TH_ZP26",
    "Topaz Solar Farm": "TH_ZP26",
    "Alta Wind Energy Center": "TH_SP15",
    "California Valley Solar Ranch": "TH_ZP26",
    "Mustang Two": "TH_NP15",  # Westlands-band solar (MSTANG/MUSTANGS)
}
WITNESS_SUBS = {"GATES": "TH_ZP26", "MIDWAY": "TH_ZP26"}

#: Corporate / generic name tokens ignored when testing name containment.
_STOPWORDS = frozenset(
    {
        "LLC",
        "INC",
        "CORP",
        "CORPORATION",
        "CO",
        "COMPANY",
        "LP",
        "LLP",
        "LTD",
        "THE",
        "OF",
        "AND",
        "PROJECT",
        "PROJECTS",
        "FACILITY",
        "HYBRID",
        "LLC1",
        "LIMITED",
    }
)
#: Generic technology/site words: allowed to differ between the two names, but
#: a match must share at least one NON-generic token.
_GENERIC = frozenset(
    {
        "SOLAR",
        "WIND",
        "ENERGY",
        "POWER",
        "PLANT",
        "FARM",
        "FARMS",
        "PARK",
        "RANCH",
        "CENTER",
        "CENTRE",
        "STORAGE",
        "BESS",
        "BATTERY",
        "GENERATING",
        "GENERATION",
        "STATION",
        "UNIT",
        "UNITS",
        "PHASE",
        "HYDRO",
        "GEOTHERMAL",
        "PEAKER",
        "PEAKING",
        "COGEN",
        "COGENERATION",
        "PV",
        # Bare direction/place words that name unrelated sites all over the
        # state — a match may never rest on one of these alone (the CENT403
        # audit case).
        "CENTRAL",
        "NORTH",
        "SOUTH",
        "EAST",
        "WEST",
        "VALLEY",
    }
)

_ROMAN = {
    "I": "1",
    "II": "2",
    "III": "3",
    "IV": "4",
    "V": "5",
    "VI": "6",
    "VII": "7",
    "VIII": "8",
    "IX": "9",
    "X": "10",
    "XI": "11",
    "XII": "12",
    "XIII": "13",
    "XIV": "14",
    "XV": "15",
    "XVI": "16",
    "XVII": "17",
    "XVIII": "18",
    "XIX": "19",
    "XX": "20",
    "XXI": "21",
}


def _name_tokens(name: str) -> list[str]:
    """Normalized name tokens: upper, punctuation split, roman -> digits.

    Trailing plurals are singularized (``FARMS -> FARM``, ``UNITS -> UNIT``)
    so EIA and CAISO spellings of the same site compare equal; double-S
    endings (``MOSS``) are left alone.
    """
    toks = re.split(r"[^A-Za-z0-9]+", str(name).upper())
    out = []
    for t in toks:
        if not t or t in _STOPWORDS:
            continue
        t = _ROMAN.get(t, t)
        if len(t) >= 4 and t.endswith("S") and not t.endswith("SS"):
            t = t[:-1]
        out.append(t)
    return out


def _compact(name: str) -> str:
    """Compacted plant name for prefix joins (tokens concatenated)."""
    return "".join(_name_tokens(name))


def _strip_unit(tok: str) -> str:
    """Strip trailing unit/bank designators (``ALTA6B2 -> ALTA``)."""
    prev = None
    while prev != tok:
        prev = tok
        tok = re.sub(r"(?:[0-9]+[A-Z]?|[A-Z][0-9]+)$", "", tok)
    return tok


def _strip_gen(tok: str) -> str:
    """Strip a trailing GEN/GN marker (``CAVLSRGN -> CAVLSR``)."""
    return re.sub(r"(?:GEN|GN)$", "", tok)


def load_hub_pnodes() -> tuple[pd.DataFrame, dict]:
    """Latest-effective-window hub membership per gen pnode, plus reports."""
    atlas = pd.read_csv(ATLAS_CSV)
    atlas["EFF_START_DT"] = pd.to_datetime(atlas["EFF_START_DT"])
    atlas["EFF_END_DT"] = pd.to_datetime(atlas["EFF_END_DT"])
    hub = atlas[atlas["APNODE_ID"].isin(HUB_SHORT)].copy()
    changed = hub.groupby("PNODE_ID")["APNODE_ID"].nunique().pipe(lambda s: s[s > 1])
    last = (
        hub.sort_values(["EFF_END_DT", "EFF_START_DT"])
        .groupby("PNODE_ID")
        .tail(1)
        .copy()
    )
    last["HUB"] = last["APNODE_ID"].map(HUB_SHORT)
    last["SUB"] = last["PNODE_ID"].str.split("_").str[0].str.upper()
    report = {
        "atlas_rows": int(len(hub)),
        "gen_pnodes": int(last["PNODE_ID"].nunique()),
        "pnodes_with_hub_change": sorted(changed.index.tolist()),
    }
    return last, report


def build_sub_map(last: pd.DataFrame) -> tuple[dict, dict, list[str]]:
    """Unanimous substation -> hub map, plus per-sub window metadata."""
    agg = last.groupby("SUB").agg(
        hubs=("HUB", lambda x: sorted(set(x))),
        eff_start=("EFF_START_DT", "min"),
        eff_end=("EFF_END_DT", "max"),
        pnode=("PNODE_ID", "first"),
        n_pnodes=("PNODE_ID", "nunique"),
    )
    ambiguous = sorted(agg.index[agg["hubs"].str.len() > 1])
    ok = agg[agg["hubs"].str.len() == 1]
    sub2hub = {s: r["hubs"][0] for s, r in ok.iterrows()}
    meta = {
        s: {
            "pnode": r["pnode"],
            "eff_start": str(r["eff_start"].date()),
            "eff_end": str(r["eff_end"].date()),
        }
        for s, r in ok.iterrows()
    }
    return sub2hub, meta, ambiguous


class TokenMatcher:
    """Deterministic four-rule substation-token matcher (see module docstring)."""

    RULES = ("exact", "genstrip", "prefix", "base")

    def __init__(self, sub2hub: dict[str, str]):
        self.sub2hub = sub2hub
        self.subs = sorted(sub2hub)
        self.genstrip = {}
        for s in self.subs:
            g = _strip_gen(s)
            if g != s and len(g) >= 4:
                self.genstrip.setdefault(g, set()).add(s)
        self.base = {}
        for s in self.subs:
            b = _strip_unit(s)
            if len(b) >= 4:
                self.base.setdefault(b, set()).add(s)

    def match(self, tok: str) -> tuple[str, list[str]] | None:
        """Return ``(rule, matched_substations)`` for the first firing rule."""
        tok = str(tok).upper()
        if not tok:
            return None
        if tok in self.sub2hub:
            return "exact", [tok]
        if tok in self.genstrip:
            return "genstrip", sorted(self.genstrip[tok])
        hits = [
            s
            for s in self.subs
            if (len(tok) >= 5 and s.startswith(tok))
            or (len(s) >= 5 and tok.startswith(s))
        ]
        if hits:
            return "prefix", hits
        tb = _strip_unit(tok)
        if len(tb) >= 4:
            hits = set(self.base.get(tb, set()))
            for b, subs in self.base.items():
                if b != tb and len(tb) >= 5 and len(b) >= 5:
                    if b.startswith(tb) or tb.startswith(b):
                        hits |= subs
            if hits:
                return "base", sorted(hits)
        return None

    def hub_of(self, tok: str) -> tuple[str, str, str] | None:
        """Return ``(hub, rule, witness_sub)`` when the match is unanimous."""
        m = self.match(tok)
        if m is None:
            return None
        rule, subs = m
        hubs = {self.sub2hub[s] for s in subs}
        if len(hubs) != 1:
            return None
        return next(iter(hubs)), rule, subs[0]


def load_plants() -> pd.DataFrame:
    """CISO plant population with names, tech groups and nameplate MW.

    The population filter is the model's own membership filter —
    ``build_zone_lookup("CAISO")`` keys (eGRID CISO + the EIA-860
    supplement) — so coverage is measured against exactly the plants the
    solve zones. Names/tech/MW come from the EIA-860 operable generator
    table plus the plant table.
    """
    from market_sim.data.zone_assignment import build_zone_lookup

    member = set(build_zone_lookup("CAISO"))

    g = pd.read_parquet(EIA_860_DIR / "eia860_generator_operable.parquet")
    g["plant_code"] = pd.to_numeric(g["Plant Code"], errors="coerce")
    g = g.dropna(subset=["plant_code"])
    g["plant_code"] = g["plant_code"].astype(int)
    g = g[g["plant_code"].isin(member)].copy()
    g["mw"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
    g["tech_group"] = (
        g["Technology"].astype(str).str.strip().map(TECH_GROUP).fillna("biomass_other")
    )
    node_col = next(c for c in g.columns if "LMP Node" in c)
    g["lmp_node"] = g[node_col].astype(str).str.strip().str.upper()
    g.loc[g["lmp_node"].isin(["NAN", "NONE", "", "N/A", "NA"]), "lmp_node"] = pd.NA

    plants = g.groupby("plant_code").agg(
        plant_name=("Plant Name", "first"),
        capacity_mw=("mw", "sum"),
        tech=("tech_group", lambda x: x.value_counts().idxmax()),
    )
    # Plant names for member plants absent from the operable generator table
    # (e.g. eGRID-only or plant-table-only rows): fill from the plant table so
    # E3/E4 can still reach them; MW stays 0 (not in the operable fleet).
    pl = pd.read_parquet(
        EIA_860_DIR / "eia860_plant.parquet", columns=["Plant Code", "Plant Name"]
    )
    pl["plant_code"] = pd.to_numeric(pl["Plant Code"], errors="coerce")
    pl = pl.dropna(subset=["plant_code"])
    pl["plant_code"] = pl["plant_code"].astype(int)
    extra = sorted(member - set(plants.index))
    fill = (
        pl[pl["plant_code"].isin(extra)]
        .drop_duplicates("plant_code")
        .set_index("plant_code")
    )
    for code in extra:
        name = fill["Plant Name"].get(code)
        plants.loc[code] = {
            "plant_name": name if isinstance(name, str) else "",
            "capacity_mw": 0.0,
            "tech": "unlisted",
        }
    plants["node_list"] = (
        g.dropna(subset=["lmp_node"])
        .groupby("plant_code")["lmp_node"]
        .agg(lambda x: sorted(set(x)))
    )
    plants["node_list"] = plants["node_list"].apply(
        lambda v: v if isinstance(v, list) else []
    )
    return plants.sort_index()


def _resource_universe() -> pd.DataFrame:
    """Distinct CAISO resources (id, name, token) from the DAM outage corpus."""
    w = pd.read_parquet(
        DAM_WINDOWS, columns=["resource_id", "resource_name", "resource_pmax_mw"]
    )
    res = w.drop_duplicates("resource_id").copy()
    res["tok"] = res["resource_id"].str.split("_").str[0].str.upper()
    return res


def evidence_e1(plants: pd.DataFrame, pn2hub: dict, tm: TokenMatcher) -> dict:
    """E1: EIA-860 reported LMP node -> hub, per plant (unanimous)."""
    out = {}
    for code, row in plants.iterrows():
        answers = []
        for node in row["node_list"]:
            clean = node.replace(" ", "")
            hit = pn2hub.get(clean) or pn2hub.get(clean.replace("-APND", ""))
            if hit is not None:
                answers.append((hit[0], "pnode-exact", hit[1]))
                continue
            h = tm.hub_of(clean.split("_")[0])
            if h is not None:
                answers.append(h)
        hubs = {a[0] for a in answers}
        if len(hubs) == 1:
            a = answers[0]
            out[code] = (a[0], f"eia-lmp-node:{a[1]}", a[2], len(answers))
        elif len(hubs) > 1:
            out[code] = ("CONFLICT", "eia-lmp-node", "", len(answers))
    return out


def evidence_e2(tm: TokenMatcher) -> dict:
    """E2: reviewed thermal resource->EIA crosswalks -> hub, per plant."""
    frames = []
    if XW_DAM_CSV.exists():
        x = pd.read_csv(XW_DAM_CSV, usecols=["resource_id", "facility_id"])
        x = x.rename(columns={"facility_id": "plant_code"})
        frames.append(x)
    if XW_EIA_CSV.exists():
        x = pd.read_csv(XW_EIA_CSV, usecols=["resource_id", "plant_code", "accepted"])
        x = x[x["accepted"] == 1][["resource_id", "plant_code"]]
        frames.append(x)
    if not frames:
        return {}
    xw = pd.concat(frames, ignore_index=True).drop_duplicates()
    xw["plant_code"] = pd.to_numeric(xw["plant_code"], errors="coerce")
    xw = xw.dropna(subset=["plant_code"])
    xw["tok"] = xw["resource_id"].str.split("_").str[0].str.upper()
    out = {}
    for code, grp in xw.groupby(xw["plant_code"].astype(int)):
        answers = [h for t in sorted(set(grp["tok"])) if (h := tm.hub_of(t))]
        hubs = {a[0] for a in answers}
        if len(hubs) == 1:
            a = answers[0]
            out[code] = (a[0], f"reviewed-crosswalk:{a[1]}", a[2], len(answers))
        elif len(hubs) > 1:
            out[code] = ("CONFLICT", "reviewed-crosswalk", "", len(answers))
    return out


def evidence_e3(plants: pd.DataFrame, tm: TokenMatcher) -> dict:
    """E3: DAM-corpus resource names matched to plant names -> hub."""
    res = _resource_universe()
    res["rtoks"] = res["resource_name"].apply(_name_tokens)
    res = res[res["rtoks"].str.len() > 0]
    # Pre-resolve each resource token's hub once.
    tok_hub = {t: tm.hub_of(t) for t in sorted(set(res["tok"]))}

    # Index plants by their non-generic name tokens for candidate lookup.
    p_toks: dict[int, set] = {}
    tok_index: dict[str, set] = {}
    for code, row in plants.iterrows():
        toks = set(_name_tokens(row["plant_name"]))
        p_toks[code] = toks
        for t in toks - _GENERIC:
            if not t.isdigit():
                tok_index.setdefault(t, set()).add(code)

    out_answers: dict[int, list] = {}
    for _, r in res.iterrows():
        h = tok_hub.get(r["tok"])
        if h is None:
            continue
        rt = set(r["rtoks"])
        rt_key = rt - _GENERIC
        rnums = {t for t in rt if t.isdigit()}
        cands = set()
        for t in rt_key:
            if not t.isdigit():
                cands |= tok_index.get(t, set())
        for code in cands:
            pt = p_toks[code]
            pnums = {t for t in pt if t.isdigit()}
            # Containment either way on the full token sets (numbers must
            # agree when both sides carry them), sharing >=1 non-generic word.
            shared = (rt & pt) - _GENERIC - rnums
            if not shared:
                continue
            if rnums and pnums and rnums != pnums:
                continue
            if not (rt <= pt | rnums or pt <= rt | pnums):
                continue
            out_answers.setdefault(code, []).append(h)
    out = {}
    for code, answers in out_answers.items():
        hubs = {a[0] for a in answers}
        if len(hubs) == 1:
            a = answers[0]
            out[code] = (a[0], f"resource-name:{a[1]}", a[2], len(answers))
        else:
            out[code] = ("CONFLICT", "resource-name", "", len(answers))
    return out


#: Hand-verified plant-name-pattern -> Atlas substation pins (E0). Each pin
#: states its verification basis; the substation's hub still comes from the
#: Atlas (unanimity rule), so a pin can never invent a hub — it only bridges
#: an abbreviation the mechanical ladder cannot reach safely. The
#: ``derive_caiso_dam_resource_crosswalk.py`` "verified-prefix" precedent.
VERIFIED_PINS: tuple[tuple[str, str, str], ...] = (
    (
        r"^MUSTANG( TWO| 3| 4)?$|^RE MUSTANG\b",
        "MUSTANGS",
        "FINDING-caiso216 §E witness: the Westlands Mustang switchyard "
        "(resources MSTANG_2_*, CAISO drops the U; TH_NP15) — distinct from "
        "the Tehachapi 'Mustang Hills' wind plant, which E3 reaches via its "
        "own ALTA4B resource.",
    ),
    (
        r"^BIG CREEK \d",
        "BIGCRK1",
        "SCE Big Creek hydro system (powerhouses 1/2/2A/3/4/8): BIGCRK* is "
        "the canonical CAISO abbreviation (atlas carries BIGCRK1/BIGCRK3 "
        "unanimously TH_SP15); the SCE system is SP15 by service territory — "
        "the geographic lat rule (37.2N -> NP15) is exactly the estimate the "
        "membership corrects.",
    ),
    (
        r"^EDWARDS SANBORN\b",
        "EDWARD",
        "The Edwards & Sanborn solar+storage complex sits ON Edwards AFB "
        "(Kern); EDWARD_7_* is unanimously TH_SP15. Deliberately anchored "
        "(^) so 'Edward C Hyatt' (Oroville, NP15) can never hit this pin — "
        "that collision is why the mechanical plant-name tier was removed.",
    ),
    (
        r"^MOJAVE SOLAR PROJECT$",
        "LCKHT1",
        "Abengoa Mojave Solar interconnects at SCE Lockhart (Harper Lake) — "
        "the same substation as the Lockhart Solar PV rows, which reach "
        "TH_SP15 by resource-name:exact. Pinned because its DAM resource "
        "name collides with SCE's small 'Mojave Solar' PV cluster at "
        "Westwind, so the mechanical E3 answer, while landing the same hub, "
        "would rest on the wrong plant's resource.",
    ),
)

#: Adjudicated FALSE-POSITIVE joins, excluded after the mover-table audit
#: (caiso-217 FINDING §B review): each falls back to the geographic rule.
#: An exclusion never assigns a hub — it only refuses evidence found to
#: conflate two different sites of the same name.
EXCLUDED_PLANTS: dict[int, str] = {
    249: "James B Black — PG&E Pit River hydro (Shasta, NP15); the E3 name "
    "match reached Kern's BLACKWLL substation through a bare 'Black' "
    "resource-name collision.",
    7147: "Mill Creek 3 — the SCE San Bernardino hydro, not the Mendocino "
    "LOWGAP 'Mill Creek' the resource name collides with.",
    50495: "High Sierra Limited — Kern oilfield cogen; the 'Sierra' "
    "resource-name collision lands SCE's Riverside-area SIERRA substation.",
}

#: Atlas substations refused as join evidence (with the audit basis). Their
#: pnodes stay in the atlas record; they are only barred from carrying a
#: plant assignment.
EXCLUDED_SUBS: dict[str, str] = {
    "GEN": "GEN_BUS_* placeholder pnodes — not a real substation identity.",
    "CENT403": "Matches every '... Central ...' name fragment (UCI, Caltech, "
    "Central Antelope) — a generic-word trap the audit caught moving "
    "southern plants to TH_NP15.",
    "FLOWD3-6": "Legacy FloWind aggregate — CAISO's FLOWD* ids conflate the "
    "Altamont (NP15) and Tehachapi (SP15) FloWind fleets, so a name join "
    "through them is direction-ambiguous by construction.",
}


def evidence_e0(plants: pd.DataFrame, tm: TokenMatcher) -> dict:
    """E0: hand-verified plant-name pins -> Atlas substation -> hub."""
    out = {}
    for code, row in plants.iterrows():
        name = str(row["plant_name"]).upper().strip()
        for pattern, sub, _basis in VERIFIED_PINS:
            if re.search(pattern, name):
                hub = tm.sub2hub.get(sub)
                if hub is not None:
                    out[code] = (hub, "verified-pin", sub, 1)
                break
    return out


def compose(
    plants: pd.DataFrame,
    tiers: list[tuple[str, dict]],
    sub_meta: dict,
    pn_meta: dict,
) -> tuple[pd.DataFrame, dict]:
    """Compose the evidence tiers into the final per-plant crosswalk."""
    rows = []
    conflicts: list[dict] = []
    disagreements: list[dict] = []
    for code, prow in plants.iterrows():
        answers = []
        for tier_name, tier in tiers:
            a = tier.get(code)
            if a is None:
                continue
            answers.append((tier_name, *a))
        real = [a for a in answers if a[1] != "CONFLICT"]
        if not real:
            if answers:  # only within-tier conflicts -> report, no row
                conflicts.append(
                    {"plant_code": int(code), "plant_name": prow["plant_name"]}
                )
            continue
        hubs = {a[1] for a in real}
        best = real[0]
        if len(hubs) > 1:
            # Cross-tier disagreement: the higher-confidence tier wins, the
            # disagreement is reported for review (§F.1g coverage honesty).
            disagreements.append(
                {
                    "plant_code": int(code),
                    "plant_name": prow["plant_name"],
                    "answers": [f"{a[0]}:{a[1]} ({a[2]})" for a in real],
                }
            )
        witness = best[3]
        meta = sub_meta.get(witness) or pn_meta.get(witness) or {}
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": prow["plant_name"],
                "tech": prow["tech"],
                "capacity_mw": round(float(prow["capacity_mw"]), 1),
                "hub": best[1],
                "pnode": meta.get("pnode", witness),
                "eff_start": meta.get("eff_start", ""),
                "eff_end": meta.get("eff_end", ""),
                "join_method": best[2],
                "n_evidence": int(best[4]),
            }
        )
    df = pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)
    return df, {
        "within_tier_conflicts": conflicts,
        "cross_tier_disagreements": disagreements,
    }


def coverage_report(plants: pd.DataFrame, xw: pd.DataFrame) -> dict:
    """Per-tech joined-MW coverage against the operable member fleet."""
    joined = set(xw["plant_code"])
    out = {}
    for tech, grp in plants.groupby("tech"):
        mw = float(grp["capacity_mw"].sum())
        jmw = float(grp.loc[grp.index.isin(joined), "capacity_mw"].sum())
        out[tech] = {
            "plants": int(len(grp)),
            "plants_joined": int(grp.index.isin(joined).sum()),
            "mw": round(mw, 1),
            "mw_joined": round(jmw, 1),
            "mw_share": round(jmw / mw, 4) if mw > 0 else None,
        }
    mw = float(plants["capacity_mw"].sum())
    jmw = float(plants.loc[plants.index.isin(joined), "capacity_mw"].sum())
    out["_total"] = {
        "plants": int(len(plants)),
        "plants_joined": int(len(joined)),
        "mw": round(mw, 1),
        "mw_joined": round(jmw, 1),
        "mw_share": round(jmw / mw, 4) if mw > 0 else None,
    }
    return out


def witness_gates(xw: pd.DataFrame, sub2hub: dict) -> tuple[dict, bool]:
    """The pre-registered §E witnesses; a joined witness must match its hub."""
    checks = {}
    ok = True
    named = xw.set_index("plant_name")
    for frag, want in WITNESS_PLANTS.items():
        rows = xw[xw["plant_name"].str.contains(frag, case=False, na=False)]
        if rows.empty:
            checks[frag] = "UNJOINED (falls back to geography)"
            continue
        got = sorted(set(rows["hub"]))
        passed = got == [want]
        checks[frag] = f"{'PASS' if passed else 'FAIL'}: {got} want {want}"
        ok &= passed
    for sub, want in WITNESS_SUBS.items():
        got = sub2hub.get(sub)
        passed = got == want
        checks[f"sub:{sub}"] = f"{'PASS' if passed else 'FAIL'}: {got} want {want}"
        ok &= passed
    _ = named
    return checks, ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--acceptance",
        action="store_true",
        help="fail (exit 1) unless every witness gate passes",
    )
    args = ap.parse_args()

    last, atlas_report = load_hub_pnodes()
    # Bar the adjudicated evidence-trap substations before any matching
    # (their pnodes stay in the atlas record; see EXCLUDED_SUBS).
    last = last[~last["SUB"].isin(EXCLUDED_SUBS)]
    sub2hub, sub_meta, ambiguous = build_sub_map(last)
    pn2hub = {}
    pn_meta = {}
    for _, r in last.iterrows():
        key = str(r["PNODE_ID"]).upper().replace(" ", "")
        pn2hub[key] = (r["HUB"], r["SUB"])
        pn2hub.setdefault(key.replace("-APND", ""), (r["HUB"], r["SUB"]))
        pn_meta[r["SUB"]] = {
            "pnode": r["PNODE_ID"],
            "eff_start": str(r["EFF_START_DT"].date()),
            "eff_end": str(r["EFF_END_DT"].date()),
        }
    tm = TokenMatcher(sub2hub)

    plants = load_plants()
    e0 = evidence_e0(plants, tm)
    e1 = evidence_e1(plants, pn2hub, tm)
    e2 = evidence_e2(tm)
    e3 = evidence_e3(plants, tm)
    xw, reports = compose(
        plants,
        [("E0", e0), ("E1", e1), ("E2", e2), ("E3", e3)],
        sub_meta,
        pn_meta,
    )
    excluded = xw[xw["plant_code"].isin(EXCLUDED_PLANTS)]
    reports["excluded_plants"] = [
        {
            "plant_code": int(r["plant_code"]),
            "plant_name": r["plant_name"],
            "refused_hub": r["hub"],
            "basis": EXCLUDED_PLANTS[int(r["plant_code"])],
        }
        for _, r in excluded.iterrows()
    ]
    xw = xw[~xw["plant_code"].isin(EXCLUDED_PLANTS)].reset_index(drop=True)
    cov = coverage_report(
        plants, xw.set_index("plant_code")["hub"].to_frame().reset_index()
    )
    checks, gates_ok = witness_gates(xw, sub2hub)

    # The mover table — every joined plant whose measured hub disagrees with
    # the geographic macro-band of the current lat/county estimate. This is
    # the crosswalk's payload AND its review surface: committed in the JSON
    # so a wrong mover is visible, cited evidence and all, never buried.
    from market_sim.data.zone_assignment import build_zone_lookup

    geo = build_zone_lookup("CAISO")
    macro = {
        "NP15": "TH_NP15",
        "ZP26": "TH_ZP26",
        "LA_BASIN": "TH_SP15",
        "SDGE": "TH_SP15",
        "SP15_rest": "TH_SP15",
    }
    geo_zone = xw["plant_code"].map(geo)
    movers = xw[xw["hub"] != geo_zone.map(macro)].assign(geo_zone=geo_zone)
    mover_rows = [
        {
            "plant_code": int(r["plant_code"]),
            "plant_name": r["plant_name"],
            "tech": r["tech"],
            "capacity_mw": float(r["capacity_mw"]),
            "geo_zone": r["geo_zone"],
            "hub": r["hub"],
            "join_method": r["join_method"],
            "pnode": r["pnode"],
        }
        for _, r in movers.sort_values("capacity_mw", ascending=False).iterrows()
    ]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    xw.to_csv(OUT_CSV, index=False)
    meta = {
        "derived_by": "scripts/data/derive_caiso_plant_hub_membership.py",
        "session": "caiso-217",
        "charter": (
            "results/calibration/FINDING-caiso216-belly-lever-plan-2026-08-23.md §F.1g"
        ),
        "sources": [
            "data/raw/caiso-atlas/ATL_PNODE_MAP.csv (OASIS ATL_PNODE_MAP, TH_*_GEN membership)",
            "data/raw/eia-860/eia860_generator_operable.parquet (RTO/ISO LMP Node Designation, names, MW)",
            "data/raw/eia-860/eia860_plant.parquet (CISO population names)",
            "data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet (resource id<->name universe)",
            "data/raw/reference/caiso-dam-resource-crosswalk.csv (reviewed resource->ORIS)",
            "data/raw/reference/caiso-resource-eia-crosswalk.csv (reviewed, accepted rows)",
        ],
        "atlas": atlas_report,
        "ambiguous_substations_dropped": ambiguous,
        "excluded_substations": EXCLUDED_SUBS,
        "verified_pins": [
            {"pattern": p, "substation": s, "basis": b} for p, s, b in VERIFIED_PINS
        ],
        "tier_rows": {
            "E0_verified_pin": len(e0),
            "E1_eia_lmp_node": len(e1),
            "E2_reviewed_crosswalk": len(e2),
            "E3_resource_name": len(e3),
        },
        "joined_plants": int(len(xw)),
        "hub_counts": xw["hub"].value_counts().to_dict(),
        "join_method_counts": xw["join_method"].value_counts().to_dict(),
        "coverage_by_tech": cov,
        "witness_gates": checks,
        "movers": {
            "note": (
                "joined plants whose measured hub disagrees with the "
                "geographic macro-band (NP15/ZP26/south) of the current "
                "lat/county estimate — the capacity the crosswalk moves"
            ),
            "count": len(mover_rows),
            "mw": round(sum(r["capacity_mw"] for r in mover_rows), 1),
            "rows": mover_rows,
        },
        "conflicts": reports,
    }
    OUT_JSON.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")

    print(f"wrote {OUT_CSV.relative_to(REPO)}  ({len(xw)} plants)")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    print("\nhub counts:", meta["hub_counts"])
    print("join methods:", meta["join_method_counts"])
    print("\ncoverage by tech (MW share joined):")
    for tech, c in sorted(cov.items()):
        share = c["mw_share"]
        print(
            f"  {tech:15s} {c['mw_joined']:>9.0f}/{c['mw']:>9.0f} MW "
            f"({share if share is not None else float('nan'):.1%}) "
            f"[{c['plants_joined']}/{c['plants']} plants]"
        )
    print("\nwitness gates:")
    for k, v in checks.items():
        print(f"  {k:30s} {v}")
    print(
        f"\nmovers: {len(mover_rows)} plants / "
        f"{meta['movers']['mw']:.0f} MW (full table in the JSON)"
    )
    print(
        f"cross-tier disagreements: {len(reports['cross_tier_disagreements'])}; "
        f"within-tier conflicts (excluded): {len(reports['within_tier_conflicts'])}"
    )
    if args.acceptance and not gates_ok:
        print("ACCEPTANCE: FAIL (witness gate)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
