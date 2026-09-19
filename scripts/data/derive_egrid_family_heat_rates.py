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

THE BOUNDARY-IDENTITY GUARD (soco-53c, 2026-09-19). The paragraph above
makes a checkable CLAIM — that the family rate lands on the plant rate's own
boundary — and the construction can now CHECK it instead of asserting it.
Because ``PLHTRT`` is the same ratio over the union of the families, a
decomposition on that boundary must RECOMPOSE to it:

    Σ_families HTIAN ÷ Σ_families GENNTAN  ==  PLHTRT

A plant that fails this identity is flagged ``boundary_mismatch`` and NOT
applied, whatever its individual family rates look like. Measured over every
covered plant in the three ISOs that have an artifact, the test partitions
them with three orders of magnitude to spare (soco-53c PRECOMMIT §1.3):
**twenty plants recompose at ratio 1.000** and **six do not, at ratio
2.80–8.40**. The six that fail are cogeneration plants, and the reason is
eGRID's own published convention: ``PLHTRT``'s numerator is STEAM-CREDITED at
a CHP plant (the useful thermal output's heat input is netted out), while the
unit sheet's ``HTIAN`` is raw fuel. So a family rate there charges the host's
process steam to the electric output — at Pensacola Florida Plant (10416) the
families recompose to 22.537 against a published 5.568. That is rule 14
``[R-ACCURATE]``'s misalignment exception exactly: accurate data on a
different boundary than our representation, which used literally makes
results LESS reflective of reality, so it is refused rather than applied. The
model already owns the CHP boundary through its own chain
(``_correct_chp_steam_credit_hr``, ``measured_chp_heat_rates``), and
``_apply_simple_cycle_hr_floor`` carves CHP out on the identical ground.

The guard REPLACES no existing check and stacks on none (rule 19
``[R-ONE-MECH]``): ``out_of_window`` is a per-FAMILY physical-plausibility
test, this is a per-PLANT boundary test, and a plant failing it has every one
of its rows flagged — if the decomposition does not recompose, no family of
it is on the plant rate's boundary. The window guard alone was NOT
sufficient, which is why this exists: at four of the six failing plants the
steam half exceeds the window and is caught, while the turbine half lands
INSIDE 3,000–30,000 Btu/kWh and was applied. It is a consumer-invisible
change — the artifact schema is unchanged and
``eia860.egrid_family_heat_rates_for`` already reads only ``flag == "ok"`` —
so no solve-path file moves and an ISO whose committed artifact is not
re-derived is byte-identical.

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

#: Relative tolerance on the boundary-identity check (soco-53c) — the
#: allowance for ``PLHTRT`` being PUBLISHED ROUNDED, nothing else. It is not a
#: tuned threshold and cannot be one: measured over all 26 covered plants in
#: the three ISOs carrying an artifact, the passing side sits at ratio 1.0000
#: (max observed deviation 5e-6, Jack Watson 2049) and the failing side starts
#: at 2.800 (Torrance Refining 50624), so EVERY value in (0.001, 1.8) produces
#: the identical partition — three orders of magnitude of margin, and no
#: result can select it. Declared ex ante in PRECOMMIT-soco-53c §1.3 and never
#: swept (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
BOUNDARY_IDENTITY_TOL: float = 0.005

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
    every family rate flagged ``ok``, ``out_of_window`` or
    ``boundary_mismatch``. Only ``ok`` rows are read by the consumer.
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
        phr = plant_hr.get(pid)
        # BOUNDARY IDENTITY (soco-53c): a decomposition of PLHTRT must
        # recompose to PLHTRT, because PLHTRT is that same ratio over the
        # union of the families. Where it does not, the family sums are on a
        # different boundary from the number they would replace — at a CHP
        # plant, eGRID steam-credits PLHTIAN and does not steam-credit the
        # unit sheet's HTIAN — and the rows are written but NOT applied (rule
        # 14 [R-ACCURATE]'s misalignment exception). PER PLANT, not per
        # family: if the decomposition does not recompose, no family of it is
        # on the plant rate's boundary. FAIL-CLOSED on a plant with no
        # published PLHTRT, since the identity is then unverifiable — inert
        # today (every covered plant in all three ISOs publishes one).
        recomposed = sum(v[0] for v in live.values()) / sum(v[1] for v in live.values())
        boundary_ok = (
            phr is not None
            and phr > 0.0
            and abs(recomposed / phr - 1.0) <= BOUNDARY_IDENTITY_TOL
        )
        for fam, (htian, genntan, n_units, n_gens) in live.items():
            hr = htian / genntan
            if not boundary_ok:
                flag = "boundary_mismatch"
            else:
                flag = "ok" if lo <= hr * 1000.0 <= hi else "out_of_window"
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
