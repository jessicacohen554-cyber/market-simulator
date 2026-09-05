#!/usr/bin/env python3
"""Derive CT-heat identity heat rates for combined cycles whose eGRID steam
generator filing collapsed (the nyiso-189 "steam-collapse" artifact).

THE OBJECT (FINDING-nyiso188 §4, DECISION-CARD-nyiso189, owner ruling
2026-09-05 = form B2 with the plant's own T1-clean median share): the fleet's
base heat rate is eGRID ``PLHTRT`` at plant grain, one vintage for every
backcast year (``process_eia860._join_egrid_heat_rate``, ``APPLIED_VINTAGE``).
``PLHTRT = PLHTIAN / PLNGENAN`` and ``PLNGENAN`` is the sum of the plant's
EIA-923 generator filings. At a combined cycle the heat is burned by the
combustion turbines alone — the steam turbine burns nothing — so when the
steam generator's filed net generation vanishes while the CTs keep running,
``PLNGENAN`` is understated by the steam share and ``PLHTRT`` inflates in
step. Bethlehem 2539: steam share 0.49–0.52 of CT output in 2018–2022 →
0.065 (2023) → 0.000 (2024) while its three CTs report ~8,000 operating
hours each; ``PLHTRT`` 6.87 → 9.665 → 10.44 against a block three
independent bases put at 6.9–7.0 MMBtu/MWh (+40 %).

THE CONSTRUCTION — every constant a published eGRID field or the plant's
own record; run over the ISO's whole population (rule 24, never a carve):

* population: every EIA plant the ISO's fleet carries a ``CC_REGULAR`` or
  ``CC_CHP`` generator for, that eGRID files >= 1 operating ``CA`` (steam)
  generator AND >= 1 operating ``CT`` generator for (the nyiso-189 census
  population; single-shaft ``CS`` and steam-less plants are outside);
* per (plant, vintage) over every on-disk eGRID vintage: ``ct_net`` /
  ``ca_net`` (Σ ``GENNTAN`` by ``PRMVR``), ``st_ct = ca_net / ct_net``,
  ``T1`` (an operating CA generator at EXACTLY zero net generation while
  ``ct_net > 0`` — the zero test), ``heat_per_ct = PLHTIAN / ct_net``;
* the plant's own record ``R(v)`` = its T1-clean vintages other than ``v``
  (``ref_n`` members; the LOYO posture of the identity derive);
* ``below_ref_fence``: ``st_ct(v) < min(R) - (max(R) - min(R))`` — the
  vintage lies below the record's minimum by MORE THAN THE RECORD'S OWN
  RANGE. The literal "below the record's minimum" (``below_ref_min``) is
  recorded alongside but not read: with ``v`` excluded from ``R`` it fires
  at the minimum-share vintage of EVERY plant (35 of 38 in NYISO), so it is
  not a test; the record's own variability is the unit that makes it one
  (PREREG-nyiso189-steam-collapse-identity-ab.md §0);
* ``ct_side_intact``: ``heat_per_ct(v)`` within ``[min(R), max(R)]`` of the
  record — the identity holds only where the CT generators' filing is
  intact; a plant whose filing moved the steam output INTO the CT row
  (Flynn 7314: 12.74 → 8.3–8.7 per CT-MWh with ``PLHTRT`` flat) already
  carries the block rate and is left alone;
* ``admitted = (T1 or below_ref_fence) and ct_side_intact and ref_n >= 2``
  (two points define a range — definitional, not a threshold);
* ``identity_hr = heat_per_ct / (1 + median(st_ct over R))`` — written for
  EVERY row so the finding can quote what the rule declines;
* ``applied = vintage == APPLIED_VINTAGE`` — the only rows the fleet reads.

Output: ``data/raw/_processed-legacy/egrid_steam_collapse_heat_rates_<ISO>.csv``.
Consumed by ``market_sim.data.fleet.eia860.apply_egrid_steam_collapse_heat_rates``
under ``ScenarioConfig.egrid_steam_collapse_heat_rates`` (default off).

Rule 23: re-derives only when its sources update (a new eGRID vintage, a new
EIA-860 fleet snapshot); nothing here reads a model output or a residual.
``--check`` re-derives and byte-compares against the committed artifact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import FLEET_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.data.egrid import _EGRID_FILES  # noqa: E402

#: The eGRID vintage the plant-grain join reads for every backcast year
#: (``process_eia860._join_egrid_heat_rate``: ``egrid2023_data_rev2.xlsx`` /
#: ``PLNT23``) — the same constant ``derive_egrid_family_heat_rates`` carries.
APPLIED_VINTAGE: int = 2023

#: Fleet plant groups whose plants form the population (a combined cycle with
#: a filed steam generator). Only ISOs a lane has derived for appear; adding
#: one is adding a name (rule 25 — each ISO's lane derives its own artifact).
CC_GROUPS: tuple[str, ...] = ("CC_REGULAR", "CC_CHP")
ISO_SCOPE: tuple[str, ...] = ("NYISO",)

#: Two points define a range: the fence and the CT-side guard both read the
#: record's [min, max], so a record needs two members. Definitional.
MIN_REFERENCE_VINTAGES: int = 2

SOURCE = (
    "eGRID GEN<yy>.GENNTAN by PRMVR (CT / CA) and PLNT<yy>.PLHTIAN, every "
    "on-disk vintage; identity_hr = PLHTIAN / sum GENNTAN(CT) / (1 + median "
    "ST/CT over the plant's own T1-clean vintages other than this one); "
    "admitted iff (T1: an operating CA generator at exactly zero net generation "
    "while the CTs run, OR st_ct below the record's minimum by more than the "
    "record's own range) AND heat_per_ct inside the record's [min, max] AND "
    ">= 2 reference vintages; applied = the plant-grain join's vintage "
    "(nyiso-189, owner ruling 2026-09-05 form B2)"
)

COLUMNS = [
    "plant_id",
    "plant_name",
    "vintage",
    "applied",
    "n_ct",
    "n_ca",
    "ct_net_mwh",
    "ca_net_mwh",
    "st_ct",
    "t1_zero",
    "plhtian_mmbtu",
    "plhtrt",
    "heat_per_ct",
    "ref_vintages",
    "ref_n",
    "ref_st_ct_min",
    "ref_st_ct_max",
    "ref_st_ct_median",
    "ref_heat_per_ct_min",
    "ref_heat_per_ct_max",
    "below_ref_min",
    "below_ref_fence",
    "ct_side_intact",
    "admitted",
    "identity_hr",
    "source",
]


def _cc_population(iso: str) -> dict[int, str]:
    """``{plant_id: name}`` of the fleet's combined-cycle plants for ``iso``."""
    import logging

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    logging.disable(logging.CRITICAL)
    try:
        fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    finally:
        logging.disable(logging.NOTSET)
    out: dict[int, str] = {}
    for g in fleet:
        if str(getattr(g, "plant_group", "")) in CC_GROUPS and g.plant_code:
            out[int(g.plant_code)] = str(getattr(g, "name", "") or "")
    return out


def _egrid_rows(iso: str, population: dict[int, str]) -> pd.DataFrame:
    """One row per (plant, vintage) with the GEN-sheet split and the PLNT heat."""
    rows = []
    for year, fname in sorted(_EGRID_FILES.items()):
        path = FLEET_DIR / fname
        if not path.exists():
            continue
        xl = pd.ExcelFile(path)
        gen_sheet = [s for s in xl.sheet_names if str(s).upper().startswith("GEN")]
        plnt_sheet = [s for s in xl.sheet_names if str(s).upper().startswith("PLNT")]
        if not gen_sheet or not plnt_sheet:
            continue
        gen = pd.read_excel(
            path,
            sheet_name=gen_sheet[0],
            header=1,
            usecols=["ORISPL", "PRMVR", "GENNTAN", "GENSTAT"],
        )
        plnt = pd.read_excel(
            path,
            sheet_name=plnt_sheet[0],
            header=1,
            usecols=["ORISPL", "PLHTIAN", "PLHTRT"],
        )
        plnt = plnt.set_index(plnt["ORISPL"].astype(int))
        gen = gen[gen["ORISPL"].isin(population)]
        for oris, g in gen.groupby("ORISPL"):
            oris = int(oris)
            op = g[g["GENSTAT"].astype(str).str.upper().str.strip() == "OP"]
            prmvr = op["PRMVR"].astype(str).str.upper().str.strip()
            ct = op[prmvr == "CT"]
            ca = op[prmvr == "CA"]
            if ct.empty or ca.empty:
                continue
            ct_gen = pd.to_numeric(ct["GENNTAN"], errors="coerce").fillna(0.0)
            ca_gen = pd.to_numeric(ca["GENNTAN"], errors="coerce").fillna(0.0)
            ct_net, ca_net = float(ct_gen.sum()), float(ca_gen.sum())
            htian = float(plnt["PLHTIAN"].get(oris, np.nan))
            plhtrt = float(plnt["PLHTRT"].get(oris, np.nan)) / 1e3
            rows.append(
                {
                    "plant_id": oris,
                    "plant_name": population[oris],
                    "vintage": int(year),
                    "n_ct": int(len(ct)),
                    "n_ca": int(len(ca)),
                    "ct_net_mwh": ct_net,
                    "ca_net_mwh": ca_net,
                    "st_ct": (ca_net / ct_net) if ct_net > 0 else np.nan,
                    "t1_zero": bool(ct_net > 0 and (ca_gen == 0.0).any()),
                    "plhtian_mmbtu": htian,
                    "plhtrt": plhtrt,
                    "heat_per_ct": (htian / ct_net) if ct_net > 0 else np.nan,
                }
            )
    return pd.DataFrame(rows)


def derive(iso: str) -> pd.DataFrame:
    """Run the construction for one ISO; return the artifact frame."""
    population = _cc_population(iso)
    df = _egrid_rows(iso, population)
    out = []
    for plant, g in df.groupby("plant_id"):
        g = g.sort_values("vintage")
        clean = g[~g["t1_zero"] & g["st_ct"].notna() & g["heat_per_ct"].notna()]
        for _, r in g.iterrows():
            ref = clean[clean["vintage"] != r["vintage"]]
            n = int(len(ref))
            rec = {k: r[k] for k in df.columns}
            rec["applied"] = bool(int(r["vintage"]) == APPLIED_VINTAGE)
            rec["ref_vintages"] = ";".join(str(int(v)) for v in ref["vintage"])
            rec["ref_n"] = n
            if n:
                smin, smax = float(ref["st_ct"].min()), float(ref["st_ct"].max())
                smed = float(ref["st_ct"].median())
                hmin, hmax = (
                    float(ref["heat_per_ct"].min()),
                    float(ref["heat_per_ct"].max()),
                )
            else:
                smin = smax = smed = hmin = hmax = np.nan
            st = float(r["st_ct"]) if pd.notna(r["st_ct"]) else np.nan
            hp = float(r["heat_per_ct"]) if pd.notna(r["heat_per_ct"]) else np.nan
            below_min = bool(n and pd.notna(st) and st < smin)
            below_fence = bool(n and pd.notna(st) and st < smin - (smax - smin))
            intact = bool(n and pd.notna(hp) and hmin <= hp <= hmax)
            admitted = bool(
                (bool(r["t1_zero"]) or below_fence)
                and intact
                and n >= MIN_REFERENCE_VINTAGES
            )
            rec.update(
                {
                    "ref_st_ct_min": smin,
                    "ref_st_ct_max": smax,
                    "ref_st_ct_median": smed,
                    "ref_heat_per_ct_min": hmin,
                    "ref_heat_per_ct_max": hmax,
                    "below_ref_min": below_min,
                    "below_ref_fence": below_fence,
                    "ct_side_intact": intact,
                    "admitted": admitted,
                    "identity_hr": (hp / (1.0 + smed))
                    if (n and pd.notna(hp))
                    else np.nan,
                    "source": SOURCE,
                }
            )
            out.append(rec)
    res = pd.DataFrame(out, columns=COLUMNS).sort_values(["plant_id", "vintage"])
    for c in ("ct_net_mwh", "ca_net_mwh", "plhtian_mmbtu"):
        res[c] = res[c].round(1)
    for c in (
        "st_ct",
        "plhtrt",
        "heat_per_ct",
        "ref_st_ct_min",
        "ref_st_ct_max",
        "ref_st_ct_median",
        "ref_heat_per_ct_min",
        "ref_heat_per_ct_max",
        "identity_hr",
    ):
        res[c] = res[c].round(4)
    return res.reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="NYISO", choices=sorted(ISO_SCOPE))
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and byte-compare against the committed artifact",
    )
    args = ap.parse_args()
    df = derive(args.iso)
    out = PROCESSED_DIR / f"egrid_steam_collapse_heat_rates_{args.iso}.csv"
    text = df.to_csv(index=False)
    if args.check:
        if not out.exists():
            print(f"CHECK FAIL: {out} does not exist")
            return 1
        if out.read_text() != text:
            print(f"CHECK FAIL: {out} does not reproduce")
            return 1
        print(f"CHECK OK: {out} reproduces byte-identically ({len(df)} row(s))")
        return 0
    out.write_text(text)
    print(f"wrote {out} ({len(df)} row(s), {df.plant_id.nunique()} plant(s))")
    t1 = df[df["t1_zero"]].groupby("plant_id")["vintage"].apply(list)
    print(f"T1 fires at {len(t1)} plant(s):")
    for p, ys in t1.items():
        print(f"  {p} {df[df.plant_id == p].plant_name.iloc[0]}: {ys}")
    adm = df[df["admitted"]]
    print(f"admitted plant-vintages: {len(adm)}")
    for r in adm.itertuples():
        print(
            f"  {r.plant_id} {r.plant_name} {r.vintage}"
            f"{' [APPLIED]' if r.applied else ''}: PLHTRT {r.plhtrt} -> "
            f"identity {r.identity_hr} (st_ct {r.st_ct}, ref median "
            f"{r.ref_st_ct_median}, T1={r.t1_zero}, fence={r.below_ref_fence})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
