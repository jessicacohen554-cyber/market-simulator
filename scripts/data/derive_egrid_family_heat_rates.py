#!/usr/bin/env python3
"""Derive eGRID PRIME-MOVER-FAMILY heat rates at multi-family plants.

THE OBJECT (nyiso-183 §7–§8, nyiso-184 PREREG §1–§3): the fleet's heat rate
is joined from eGRID at PLANT grain (``process_eia860._join_egrid_heat_rate``
reads ``PLNT<yy>.PLHTRT``), so every generator at a plant inherits one
generation-weighted blend. At a plant that hosts more than one prime-mover
family — a 1960s steam station beside a 2003 combined cycle (Ravenswood 2500:
plant blend 8.80 MMBtu/MWh, the steam units' own meter ~11) — that blend is
the wrong rate for BOTH halves: the steam is priced with the combined cycle's
efficiency leaking in, and the combined cycle with the steam's inefficiency
leaking in. The model then repaired the steam half of ONE such plant with a
hand number (``fleet.models.MIXED_FACILITY_STEAM_HR[2500] = 9.5``, derived by
its own comment from ASSUMED capacity factors that put two-thirds of the
site's energy on the steam where the meter puts one-third).

THE CONSTRUCTION — zero free parameters, the same eGRID source at a finer
grain. eGRID publishes per-UNIT heat input (``UNT<yy>.HTIAN``, keyed by
``PRMVR``) and per-GENERATOR net generation (``GEN<yy>.GENNTAN``, keyed by
``PRMVR``), so for each prime-mover family F at a plant

    HR_family = Σ HTIAN over UNT rows with PRMVR ∈ F
              ÷ Σ GENNTAN over GEN rows with PRMVR ∈ F

on the identical net-annual boundary as the plant rate every single-family
peer carries. Families (``EGRID_PRIME_MOVER_FAMILIES``): ``ST`` = {ST},
``CC`` = {CT, CA, CS, CC}, ``GT`` = {GT, IC}. A plant is COVERED when at
least two families each carry HTIAN > 0 and GENNTAN > 0 in the applied
vintage; a single-family plant's plant rate already IS its family rate and
is never touched. The applied vintage is the one the plant-grain join reads
(``APPLIED_VINTAGE`` = 2023, ``egrid2023_data_rev2.xlsx``), so the family
rate replaces the blend on the same boundary and year; a family rate outside
the join's own physical window (``process_eia860.EGRID_HR_WINDOW_BTU_KWH``,
3,000–30,000 Btu/kWh) is written with a ``flag`` and NOT applied. Every other
on-disk vintage's family value is written to a companion ``_vintages.csv``
for the record; none is applied and no pooling rule is chosen from them
(PREREG-nyiso184 §5 F9).

Output: ``data/raw/_processed-legacy/egrid_family_heat_rates_<ISO>.csv`` (+
``_vintages.csv``). Consumed by
``market_sim.data.fleet.eia860._apply_egrid_family_heat_rates`` under
``ScenarioConfig.egrid_family_heat_rates`` (default off, byte-identical off).

Rule 13 ``[R-MEASURED]``: regenerates for any year from whichever eGRID
vintage the fleet join reads, from published fields alone, responds to changed
conditions (a re-powering or a changed duty moves it), reads no model output
and no residual. Rule 23 ``[R-FROZEN-DERIVE]``: re-derives only when eGRID or
EIA-860 updates. Rule 25: per-ISO artifact — an ISO with no artifact is a
no-op. ``--check`` re-derives and byte-compares against the committed file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.paths import EIA_860_DIR, FLEET_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.data.egrid import _EGRID_FILES  # noqa: E402
from market_sim.data.fleet.eia860 import EIA_860_PARQUET_NAME  # noqa: E402
from market_sim.data.fleet.models import (  # noqa: E402
    EGRID_PRIME_MOVER_FAMILIES,
    ba_codes,
    egrid_prime_mover_family,
)
from scripts.data.process_eia860 import EGRID_HR_WINDOW_BTU_KWH  # noqa: E402

#: The eGRID vintage the plant-grain join reads (``process_eia860``'s
#: ``egrid2023_data_rev2.xlsx`` / ``PLNT23``). The applied family rate comes
#: from THIS vintage so it replaces the blend on the identical boundary.
APPLIED_VINTAGE: int = 2023

#: Minimum live families for a plant to be covered (a single-family plant's
#: plant rate is already its family rate).
MIN_LIVE_FAMILIES: int = 2

SOURCE = (
    "eGRID UNT<yy>.HTIAN summed over the family's PRMVR codes / GEN<yy>.GENNTAN "
    "summed over the same codes, per plant; families ST={ST} CC={CT,CA,CS,CC} "
    "GT={GT,IC}; covered iff >= 2 families each with HTIAN>0 and GENNTAN>0; "
    "applied vintage = the plant-grain join's own; window = the join's own "
    "3,000-30,000 Btu/kWh; zero free parameters (PREREG-nyiso184 §3 R1)"
)

COLUMNS = [
    "plant_id",
    "plant_name",
    "family",
    "egrid_prime_movers",
    "heat_rate_mmbtu_mwh",
    "htian_mmbtu",
    "genntan_mwh",
    "n_units",
    "n_gens",
    "plant_plhtrt_mmbtu_mwh",
    "delta_vs_plant",
    "vintage",
    "live_families",
    "flag",
    "iso",
    "source",
]


def _sheets(vintage: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return the ``(PLNT, UNT, GEN)`` sheets of one on-disk eGRID vintage."""
    path = FLEET_DIR / _EGRID_FILES[vintage]
    yy = f"{vintage % 100:02d}"
    plnt = pd.read_excel(
        path,
        sheet_name=f"PLNT{yy}",
        skiprows=1,
        usecols=["ORISPL", "PNAME", "PLHTIAN", "PLNGENAN", "PLHTRT"],
    )
    unt = pd.read_excel(
        path,
        sheet_name=f"UNT{yy}",
        skiprows=1,
        usecols=["ORISPL", "UNITID", "PRMVR", "HTIAN"],
    )
    gen = pd.read_excel(
        path,
        sheet_name=f"GEN{yy}",
        skiprows=1,
        usecols=["ORISPL", "GENID", "PRMVR", "GENNTAN"],
    )
    for df in (plnt, unt, gen):
        df["ORISPL"] = pd.to_numeric(df["ORISPL"], errors="coerce")
        df.dropna(subset=["ORISPL"], inplace=True)
        df["ORISPL"] = df["ORISPL"].astype(int)
    return plnt, unt, gen


def iso_plant_ids(iso: str) -> dict[int, str]:
    """``{plant_id: plant_name}`` for the ISO's operable EIA-860 thermal plants."""
    df = pd.read_parquet(
        EIA_860_DIR / EIA_860_PARQUET_NAME,
        columns=["plant_id", "plant_name", "balancing_authority_code", "status"],
    )
    # Membership over every BA the region comprises (NWPP is seventeen).
    df = df[
        df["balancing_authority_code"].astype(str).str.strip().isin(ba_codes(iso))
        & (df["status"].astype(str).str.strip().str.upper() == "OP")
    ]
    return {
        int(p): str(n) for p, n in zip(df["plant_id"], df["plant_name"]) if pd.notna(p)
    }


def family_heat_rates(vintage: int, plants: dict[int, str], iso: str) -> pd.DataFrame:
    """The R1 construction for one vintage over ``plants``.

    Returns one row per (covered plant, live family) in :data:`COLUMNS`,
    every family rate flagged ``ok`` or ``out_of_window``.
    """
    plnt, unt, gen = _sheets(vintage)
    lo, hi = EGRID_HR_WINDOW_BTU_KWH
    unt = unt[unt["ORISPL"].isin(plants)].copy()
    gen = gen[gen["ORISPL"].isin(plants)].copy()
    unt["family"] = unt["PRMVR"].map(egrid_prime_mover_family)
    gen["family"] = gen["PRMVR"].map(egrid_prime_mover_family)
    unt["HTIAN"] = pd.to_numeric(unt["HTIAN"], errors="coerce")
    gen["GENNTAN"] = pd.to_numeric(gen["GENNTAN"], errors="coerce")
    plant_hr = {
        int(r.ORISPL): float(r.PLHTRT) / 1000.0
        for r in plnt.itertuples()
        if pd.notna(r.PLHTRT)
    }
    heat = (
        unt.dropna(subset=["family"])
        .groupby(["ORISPL", "family"])["HTIAN"]
        .agg(["sum", "count"])
    )
    net = (
        gen.dropna(subset=["family"])
        .groupby(["ORISPL", "family"])["GENNTAN"]
        .agg(["sum", "count"])
    )
    pms = (
        unt.dropna(subset=["family"])
        .groupby(["ORISPL", "family"])["PRMVR"]
        .agg(lambda s: "+".join(sorted(set(map(str, s)))))
    )
    rows: list[dict] = []
    for pid in sorted(plants):
        live: dict[str, tuple[float, float, int, int]] = {}
        for fam in EGRID_PRIME_MOVER_FAMILIES:
            h = heat.loc[(pid, fam)] if (pid, fam) in heat.index else None
            n = net.loc[(pid, fam)] if (pid, fam) in net.index else None
            if h is None or n is None:
                continue
            htian, genntan = float(h["sum"]), float(n["sum"])
            if not (htian > 0.0 and genntan > 0.0):
                continue
            live[fam] = (htian, genntan, int(h["count"]), int(n["count"]))
        if len(live) < MIN_LIVE_FAMILIES:
            continue
        for fam, (htian, genntan, n_units, n_gens) in live.items():
            hr = htian / genntan
            flag = "ok" if lo <= hr * 1000.0 <= hi else "out_of_window"
            phr = plant_hr.get(pid)
            rows.append(
                {
                    "plant_id": pid,
                    "plant_name": plants[pid],
                    "family": fam,
                    "egrid_prime_movers": pms.get((pid, fam), ""),
                    "heat_rate_mmbtu_mwh": round(hr, 4),
                    "htian_mmbtu": round(htian, 1),
                    "genntan_mwh": round(genntan, 1),
                    "n_units": n_units,
                    "n_gens": n_gens,
                    "plant_plhtrt_mmbtu_mwh": None if phr is None else round(phr, 4),
                    "delta_vs_plant": None if phr is None else round(hr - phr, 4),
                    "vintage": vintage,
                    "live_families": "+".join(sorted(live)),
                    "flag": flag,
                    "iso": iso.upper(),
                    "source": SOURCE,
                }
            )
    return pd.DataFrame(rows, columns=COLUMNS)


def derive(iso: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(applied artifact, per-vintage companion)`` for one ISO."""
    plants = iso_plant_ids(iso)
    applied = family_heat_rates(APPLIED_VINTAGE, plants, iso)
    frames = [applied]
    for v in sorted(_EGRID_FILES):
        if v == APPLIED_VINTAGE:
            continue
        if not (FLEET_DIR / _EGRID_FILES[v]).exists():
            continue
        frames.append(family_heat_rates(v, plants, iso))
    vintages = pd.concat(frames, ignore_index=True)
    vintages = vintages.sort_values(["plant_id", "family", "vintage"]).reset_index(
        drop=True
    )
    return applied, vintages


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and byte-compare against the committed artifact",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    applied, vintages = derive(iso)
    out = args.out_dir / f"egrid_family_heat_rates_{iso}.csv"
    out_v = args.out_dir / f"egrid_family_heat_rates_{iso}_vintages.csv"
    if args.check:
        have = pd.read_csv(out)
        same = have.to_csv(index=False) == applied.to_csv(index=False)
        print("MATCH" if same else "DIFFERS", out)
        sys.exit(0 if same else 1)
    applied.to_csv(out, index=False)
    vintages.to_csv(out_v, index=False)
    print(
        f"{iso}: {len(applied)} (plant, family) rows over "
        f"{applied['plant_id'].nunique()} covered plants, vintage {APPLIED_VINTAGE} "
        f"({int((applied['flag'] == 'ok').sum())} applied) -> {out}"
    )
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(applied.drop(columns=["source", "iso"]).to_string(index=False))


if __name__ == "__main__":
    main()
