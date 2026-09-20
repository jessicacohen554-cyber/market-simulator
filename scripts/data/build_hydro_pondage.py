"""Derive each conventional-hydro plant's USABLE FOREBAY STORAGE, in MWh.

The measured input behind ``ScenarioConfig.hydro_pondage_bound`` (lane
hydro-1, 2026-09-20). The dispatch LP's hydro family caps each plant's
MONTHLY energy and imposes no bound at all on how that energy is distributed
inside the month, so a plant may bank ~730 hours of water at zero cost and
land it on the peak. nyiso-219 measured what the fleet can physically hold
(``docs/FINDING-nyiso219-pondage-duration-2026-09-07.md``): **72.01 % of
NYISO's scored hydro MW cannot hold even ONE DAY of its own full output** and
98.31 % cannot hold a month. This script turns that measurement into the LP's
bound.

**Construction — zero fitted constants, every term a published datum.**

* **Volume.** USACE National Inventory of Dams ``Max Storage (Acre-Ft)``,
  summed over the plant's DISTINCT ``NID ID`` impoundments. Distinctness is
  load-bearing and is not a choice: NID files one ROW PER STRUCTURE, so a
  multi-dike impoundment repeats the same volume on every dike (Robert Moses
  St. Lawrence carries eight rows, all 803,000 acre-ft). Summing rows would
  multiply one reservoir eightfold; summing distinct NID IDs counts each
  impoundment once and still adds a genuinely separate second reservoir
  (Niagara's forebay NY16253 *plus* the Lewiston Reservoir NY00689).
* **Head.** NID ``Hydraulic Height (Ft)`` where the dam reports one, else its
  ``NID Height (Ft)`` as the labelled proxy — nyiso-219's committed rule,
  frozen under rule 21 ``[R-FROZEN-DERIVE]`` and re-derived only when NID
  publishes a new vintage.
* **Energy.** ``E = rho g V h`` with turbine efficiency taken as **1.0**, the
  same deliberately GENEROUS upper-bound convention nyiso-219 used: the
  conclusion is that the bound is orders of magnitude below a month, so an
  upper bound settles it and no efficiency needs to be assumed.

**Plant -> dam linkage** is ORNL HILARRI v4 (``eia_ptid`` -> ``nidid``), plus
the small cited cross-reference registry
:data:`market_sim.config.constants.HYDRO_PONDAGE_EXTRA_NID_BY_PLANT` for
impoundments HILARRI does not link. A plant with no linkage gets **no row**
and the LP leaves it on its monthly budget exactly as today — never a
substituted value (rule 13 ``[R-MEASURED]``).

Output: ``data/raw/<iso>-hydro/<iso>_hydro_pondage.csv``, one row per
(plant_id) with ``storage_mwh``, ``n_impoundments``, ``storage_af``,
``head_ft_basis`` and ``pondage_hours`` (reported for the record; the LP
consumes ``storage_mwh``).

Usage::

    uv run --no-sync python3 scripts/data/build_hydro_pondage.py --iso NYISO PJM
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.data.fleet import ba_codes  # noqa: E402

DEFAULT_ISOS: tuple[str, ...] = ("NYISO", "PJM")

HILARRI_CSV = "hilarri/HILARRI_v4.csv"
EHA_XLSX = "ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx"

# Unit conversions — all exact definitions, no estimate enters.
ACRE_FT_M3 = 1233.4818375475  # 1 acre-foot in m^3 (exact, from the US survey foot)
FT_M = 0.3048  # 1 international foot in m (exact)
RHO_WATER = 1000.0  # kg/m^3
G = 9.80665  # m/s^2, standard gravity (BIPM)
J_PER_MWH = 3.6e9


def potential_energy_mwh(storage_af: float, head_ft: float) -> float:
    """Return the gravitational potential energy of a stored volume, in MWh.

    ``E = rho g V h`` at turbine efficiency 1.0 — a deliberate UPPER bound
    (nyiso-219 §1), so the derived storage can only over-state what the plant
    can hold and the bound it feeds can only be too loose, never too tight.
    """
    return (
        RHO_WATER
        * G
        * (float(storage_af) * ACRE_FT_M3)
        * (float(head_ft) * FT_M)
        / J_PER_MWH
    )


def load_nid(nid_csv: Path) -> pd.DataFrame:
    """Return the NID national export, one row per dam structure.

    The file's first line is a vintage banner (``Data Last Updated:,...``), so
    the header is on line 2.
    """
    df = pd.read_csv(nid_csv, skiprows=1, low_memory=False)
    keep = [
        "Dam Name",
        "NID ID",
        "State",
        "Owner Names",
        "Primary Purpose",
        "Normal Storage (Acre-Ft)",
        "Max Storage (Acre-Ft)",
        "Hydraulic Height (Ft)",
        "NID Height (Ft)",
        "Surface Area (Acres)",
    ]
    return df[[c for c in keep if c in df.columns]].copy()


def plant_dam_links(iso: str, raw_root: Path) -> pd.DataFrame:
    """Return ``(plant_id, nid_id, source)`` for one ISO's conventional hydro.

    HILARRI links EHA plants to NID dams; the EHA Operational sheet supplies
    the BA filter and the EIA plant id. The cited cross-reference registry is
    appended with ``source='registry'`` so provenance stays visible in the
    artifact.
    """
    from market_sim.config.constants import HYDRO_PONDAGE_EXTRA_NID_BY_PLANT

    eha = pd.read_excel(raw_root / EHA_XLSX, sheet_name="Operational")
    eha = eha[
        eha["BACode"].isin(ba_codes(iso)) & (eha["CH_MW"] > 0) & eha["EIA_PtID"].notna()
    ]
    eha["EHA_PtID"] = eha["EHA_PtID"].astype(str)
    hil = pd.read_csv(raw_root / HILARRI_CSV, dtype={"eha_ptid": str}, low_memory=False)
    hil = hil[hil["eha_ptid"].isin(set(eha["EHA_PtID"])) & hil["nidid"].notna()]
    eia_of = dict(zip(eha["EHA_PtID"], eha["EIA_PtID"].astype(int)))
    rows = [
        {"plant_id": eia_of[p], "nid_id": str(n).strip(), "source": "hilarri"}
        for p, n in zip(hil["eha_ptid"], hil["nidid"])
        if p in eia_of
    ]
    for pid, nids in HYDRO_PONDAGE_EXTRA_NID_BY_PLANT.get(iso.upper(), {}).items():
        rows += [
            {"plant_id": int(pid), "nid_id": str(n), "source": "registry"} for n in nids
        ]
    out = pd.DataFrame(rows)
    return out.drop_duplicates(subset=["plant_id", "nid_id"])


def build(iso: str, nid_csv: Path, raw_root: Path | None = None) -> pd.DataFrame:
    """Return the per-plant pondage table for one ISO."""
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    from market_sim.data.hydro import _load_hydro_nameplate

    nid = load_nid(nid_csv)
    # One row per impoundment: NID files one row per STRUCTURE and repeats the
    # impoundment's volume on every dike (see the module docstring). Take each
    # NID ID once, at its largest reported volume and its best-reported head.
    per_dam = nid.groupby("NID ID").agg(
        dam_name=("Dam Name", "first"),
        storage_af=("Max Storage (Acre-Ft)", "max"),
        hyd_ft=("Hydraulic Height (Ft)", "max"),
        nid_ft=("NID Height (Ft)", "max"),
    )
    links = plant_dam_links(iso, raw_root)
    nameplate = _load_hydro_nameplate(iso)

    recs = []
    for pid, grp in links.groupby("plant_id"):
        dams = per_dam.reindex([n for n in grp["nid_id"] if n in per_dam.index])
        dams = dams[dams["storage_af"].notna() & (dams["storage_af"] > 0)]
        if dams.empty:
            continue  # no inventoried storage -> no row, plant stays unbounded
        head = dams["hyd_ft"].where(dams["hyd_ft"].notna(), dams["nid_ft"])
        basis = np.where(dams["hyd_ft"].notna(), "hydraulic", "nid_height_proxy")
        ok = head.notna() & (head > 0)
        if not ok.any():
            continue  # no head for any impoundment -> unidentifiable, no row
        e = float(
            sum(
                potential_energy_mwh(v, h)
                for v, h in zip(dams["storage_af"][ok], head[ok])
            )
        )
        pmax = float(nameplate.get(int(pid), 0.0))
        recs.append(
            {
                "plant_id": int(pid),
                "storage_mwh": round(e, 3),
                "n_impoundments": int(ok.sum()),
                "storage_af": round(float(dams["storage_af"][ok].sum()), 1),
                "head_ft_basis": "|".join(sorted(set(basis[ok.to_numpy()]))),
                "nid_ids": "|".join(dams.index[ok].astype(str)),
                "link_source": "|".join(sorted(set(grp["source"]))),
                "nameplate_mw": round(pmax, 1),
                "pondage_hours": round(e / pmax, 4) if pmax > 0 else None,
            }
        )
    return pd.DataFrame(recs).sort_values("plant_id").reset_index(drop=True)


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(DEFAULT_ISOS))
    ap.add_argument(
        "--nid-csv",
        required=True,
        help="USACE NID national CSV export (https://nid.sec.usace.army.mil/api/nation/csv)",
    )
    args = ap.parse_args()
    for iso in args.iso:
        df = build(iso, Path(args.nid_csv))
        out_dir = paths.RAW_DATA_DIR / f"{iso.lower()}-hydro"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{iso.lower()}_hydro_pondage.csv"
        df.to_csv(path, index=False)
        mw = df["nameplate_mw"].sum()
        under_day = df[df["pondage_hours"] < 24]["nameplate_mw"].sum()
        print(
            f"[{iso}] {len(df)} plants / {mw:.0f} MW with identified storage; "
            f"{under_day / max(mw, 1):.1%} of that MW holds < 24 h; "
            f"median pondage {df['pondage_hours'].median():.2f} h -> {path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
