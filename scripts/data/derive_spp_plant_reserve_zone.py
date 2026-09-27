"""Derive the SPP plant -> reserve-zone -> West/East bubble map (SPP-93, PRECOMMIT §1.3).

The rule, fixed in ``docs/handoffs/PRECOMMIT-spp-93-west-east-2026-09-27.md`` §1.3 before any
model output existed:

1. **Node.** Each SWPP generator's EIA-860 ``RTO/ISO LMP Node Designation`` (every vintage
   2018-2024 plus HEAD), normalised (upper-case, alphanumerics only, trailing ``_RA`` stripped), is
   matched against every ``SETLOCNAME`` / ``PARENTPNODE`` / ``CHILDPNODE`` / ``ENODE`` of the
   non-External rows of SPP's settlement-location registry
   (``data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv``). An exact match is tried first,
   else a >= 8-character prefix match in either direction. The generator's RZ set is the union over
   its matches.
2. A generator is **West** if its RZ set is contained in {1,2,3,5} and **East** if it is {4}. A
   mixed set resolves through the matched ``NODE_AREA`` under the §1.2 load rule; if the areas also
   straddle, the generator stays unlabelled. The plant's bubble is the capacity-majority bubble over
   its labelled generators.
3. **No node, or no match:** 1-nearest-neighbour (haversine) on plant coordinates among the labelled
   plants. There is no parameter.

Output: ``data/raw/reference/spp_plant_reserve_zone.csv`` (``plant_code, lat, lon, bubble, source,
rz_set, labelled_mw``), read by ``zone_assignment`` when ``ScenarioConfig.spp_west_east_topology``
is armed. Plants absent from the table are placed at runtime by the same 1-NN
(:func:`market_sim.data.zone_assignment._spp_we_nearest`).

Usage: ``python scripts/data/derive_spp_plant_reserve_zone.py``
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EIA = ROOT / "data" / "raw" / "eia-860"
SL = ROOT / "data" / "raw" / "spp-planning" / "SL_to_Pnode_to_Zone_with_Area.csv"
OUT = ROOT / "data" / "raw" / "reference" / "spp_plant_reserve_zone.csv"

WEST_RZ = {"1", "2", "3", "5"}
EAST_RZ = {"4"}
# PRECOMMIT §1.2: sub-BA (== SPP NODE_AREA) -> bubble, by majority RZ of its LOAD settlement locations.
AREA_BUBBLE = {a: "West" for a in ("LES", "NPPD", "OPPD", "SECI", "SPS", "WAUE")} | {
    a: "East"
    for a in (
        "CSWS",
        "EDE",
        "GRDA",
        "INDN",
        "KACY",
        "KCPL",
        "MPS",
        "OKGE",
        "SPRM",
        "WFEC",
        "WR",
    )
}


def _norm(x: str) -> str:
    """Upper-case alphanumerics only."""
    return re.sub(r"[^A-Z0-9]", "", str(x).upper())


def load_registry() -> dict[str, set[tuple[str, str]]]:
    """Normalised registry key -> set of (RESZONE, NODE_AREA), non-External rows only."""
    s = pd.read_csv(SL, dtype=str)
    s = s[s.RESZONE != "External"]
    keys: dict[str, set[tuple[str, str]]] = {}
    for col in ("SETLOCNAME", "PARENTPNODE", "CHILDPNODE", "ENODE"):
        for k, rz, area in zip(s[col], s.RESZONE, s.NODE_AREA):
            for kk in {_norm(k), _norm(re.sub(r"_RA$", "", str(k)))}:
                if kk:
                    keys.setdefault(kk, set()).add((rz, area))
    return keys


def match(
    node: object, keys: dict[str, set[tuple[str, str]]], long_keys: list[str]
) -> set | None:
    """Match one EIA-860 node string: exact, then _RA-stripped, then >= 8-char prefix either way."""
    if not isinstance(node, str) or not node.strip():
        return None
    k = _norm(node)
    if not k:
        return None
    if k in keys:
        return keys[k]
    k2 = _norm(re.sub(r"_RA$", "", node.strip()))
    if k2 in keys:
        return keys[k2]
    hits = [
        keys[kk]
        for kk in long_keys
        if k.startswith(kk) or (len(k) >= 8 and kk.startswith(k))
    ]
    return set().union(*hits) if hits else None


def gen_bubble(m: set[tuple[str, str]] | None) -> str | None:
    """Bubble of one generator's match set (rule step 2)."""
    if not m:
        return None
    rz = {r for r, _ in m}
    if rz <= WEST_RZ:
        return "West"
    if rz <= EAST_RZ:
        return "East"
    b = {AREA_BUBBLE.get(a) for _, a in m} - {None}
    return b.pop() if len(b) == 1 else None


def haversine_nn(
    lat: np.ndarray, lon: np.ndarray, lat0: np.ndarray, lon0: np.ndarray
) -> np.ndarray:
    """Index into (lat0, lon0) of each point's nearest neighbour (great-circle)."""
    p1, p2 = np.radians(lat)[:, None], np.radians(lat0)[None, :]
    dl = np.radians(lon)[:, None] - np.radians(lon0)[None, :]
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return np.argmin(a, axis=1)


def main() -> None:
    """Build and write the plant map."""
    keys = load_registry()
    long_keys = [k for k in keys if len(k) >= 8]
    dirs = sorted(EIA.glob("vintage_*")) + [EIA]
    plants, gens = [], []
    for d in dirs:
        p = pd.read_parquet(d / "eia860_plant.parquet")
        p = p[p["Balancing Authority Code"] == "SWPP"]
        plants.append(p[["Plant Code", "Latitude", "Longitude"]].assign(v=d.name))
        g = pd.read_parquet(d / "eia860_generator_operable.parquet")
        g = g[g["Plant Code"].isin(set(p["Plant Code"]))]
        gens.append(
            g[
                [
                    "Plant Code",
                    "Generator ID",
                    "RTO/ISO LMP Node Designation",
                    "Nameplate Capacity (MW)",
                ]
            ].assign(v=d.name)
        )
    P = pd.concat(plants)
    P["lat"] = pd.to_numeric(P.Latitude, errors="coerce")
    P["lon"] = pd.to_numeric(P.Longitude, errors="coerce")
    # latest vintage with coordinates wins (HEAD dir name 'eia-860' sorts after 'vintage_*' by list order)
    P = P.dropna(subset=["lat", "lon"]).groupby("Plant Code").last()[["lat", "lon"]]
    G = pd.concat(gens)
    G["mw"] = pd.to_numeric(G["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
    G = (
        G.groupby(["Plant Code", "Generator ID"])
        .agg(
            node=(
                "RTO/ISO LMP Node Designation",
                lambda s: next(
                    (x for x in reversed(list(s)) if isinstance(x, str) and x.strip()),
                    None,
                ),
            ),
            mw=("mw", "last"),
        )
        .reset_index()
    )
    G["m"] = G.node.map(lambda n: match(n, keys, long_keys))
    G["b"] = G.m.map(gen_bubble)
    G["rz"] = G.m.map(lambda m: ",".join(sorted({r for r, _ in m})) if m else "")
    lab = (
        G.dropna(subset=["b"])
        .groupby(["Plant Code", "b"])
        .mw.sum()
        .unstack(fill_value=0.0)
    )
    for c in ("West", "East"):
        if c not in lab:
            lab[c] = 0.0
    lab_b = pd.Series(np.where(lab.West >= lab.East, "West", "East"), index=lab.index)
    lab_mw = lab.West + lab.East
    rzset = (
        G[G.rz != ""]
        .groupby("Plant Code")
        .rz.agg(lambda s: ",".join(sorted(set(",".join(s).split(",")))))
    )
    out = P.copy()
    out["bubble"] = lab_b.reindex(out.index)
    out["source"] = np.where(out.bubble.notna(), "node", "1nn")
    L = out[out.source == "node"]
    U = out[out.source == "1nn"]
    idx = haversine_nn(U.lat.values, U.lon.values, L.lat.values, L.lon.values)
    out.loc[U.index, "bubble"] = L.bubble.values[idx]
    out["rz_set"] = rzset.reindex(out.index).fillna("")
    out["labelled_mw"] = lab_mw.reindex(out.index).fillna(0.0).round(1)
    out.index.name = "plant_code"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.reset_index()[
        ["plant_code", "lat", "lon", "bubble", "source", "rz_set", "labelled_mw"]
    ].to_csv(OUT, index=False)
    print(
        f"{len(out)} SWPP plants: {(out.source == 'node').sum()} node-labelled, {(out.source == '1nn').sum()} by 1-NN; "
        f"bubbles {out.bubble.value_counts().to_dict()}; generators with a node {G.node.notna().sum()} of {len(G)}, "
        f"matched {G.m.notna().sum()}, labelled {G.b.notna().sum()}"
    )


if __name__ == "__main__":
    main()
