"""Derive PJM's firm (must-flow) scheduled-export floor per seam and year.

PJM exports to MISO and NYISO in ~87-100% of hours, at a mean spread (~$1.5/MWh
PJM-MISO) far too thin for a pure hourly energy-spread seam to clear in every
hour. The reason is structural: a large share of PJM's net export to these RTOs
is FIRM, long-term SCHEDULED capacity/energy that flows regardless of the hourly
price — the same reason Hydro-Quebec/Manitoba firm imports floor NYISO/MISO
(``inject_nyiso_firm_imports`` / ``inject_miso_firm_imports``). The reference-
price seam prices every export band economically, so it backs the firm base off
in the cheap/low-spread hours the schedule actually keeps flowing — the PJM
2023 NYISO under-export (+4.3 vs +18.5 TWh).

This script reads PJM's OWN published per-tie SCHEDULED interchange (the Data
Miner ``import_export_act_sch_interchange`` ``sched_flow`` column, the firm/
day-ahead scheduled transactions, NOT the realized ``actual_flow`` that is the
EIA-930 validation target) and reports, per seam and year, the firm export floor
as the robust low quantile (p10) of the seam's scheduled export — i.e. the
export level scheduled in >=90% of hours, the firm contractual base that does not
respond to that hour's price.

Rule compliance:
  * #11 (never tune to the net-MWh target): the floor comes from the SCHEDULED-
    transaction series, never from the realized net interchange that is scored.
    p10 isolates the always-scheduled firm base from the price-responsive
    economic schedule on top, so it carries no information about the realized
    flow it is validated against.
  * #12 (measured over estimate): the firm floor is a measured market-operations
    input with a forward analogue — firm capacity/energy contract positions are
    a forward driver, and the floor would regenerate for a forward year from the
    contracted schedule. Years with no scheduled-export data fall back to no
    floor (the economic seam alone), so forecast runs are byte-identical.

Only seams PJM net-EXPORTS over (MISO, NYISO) get a floor; the net-IMPORT seams
(Carolinas, TVA, LGEE) schedule net import and get none. Run::

    python scripts/data/derive_firm_export_floor.py

and paste the emitted ``firm_export_floor_by_year`` blocks into constants.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO / "data" / "raw" / "iso-specific-transmission"
YEARS = (2023, 2024, 2025)
# Robust low quantile defining the firm (always-scheduled) export base.
FIRM_PCTL = 0.10

# PJM external tie -> registry seam (mirrors derive_interface_limits.SEAM_TIES,
# now including the south-west import seams TVA/LGEE).
SEAM_TIES: dict[str, list[str]] = {
    "MISO": [
        "ALTE",
        "ALTW",
        "AMIL",
        "CWLP",
        "IPL",
        "MEC",
        "MECS",
        "NIPS",
        "SIGE",
        "WEC",
        "MDU",
        "CIN",
    ],
    "NYISO": ["NYIS", "HUDS", "NEPT", "LIND"],
    "Carolinas": ["CPLE", "CPLW", "DUK"],
    "TVA": ["TVA"],
    "LGEE": ["LGEE"],
}
# Seams PJM net-exports over (the only ones that carry a firm-export floor).
EXPORT_SEAMS = ("MISO", "NYISO")


def _seam_scheduled_export(year: int) -> pd.DataFrame:
    """Return hourly simultaneous SCHEDULED export (MW, +=export) per seam."""
    tie_to_seam = {t: s for s, ts in SEAM_TIES.items() for t in ts}
    path = DATA_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    df = pd.read_csv(path, usecols=["datetime_beginning_utc", "tie_line", "sched_flow"])
    df["seam"] = df["tie_line"].map(tie_to_seam)
    mapped = df.dropna(subset=["seam"])
    piv = mapped.pivot_table(
        index="datetime_beginning_utc",
        columns="seam",
        values="sched_flow",
        aggfunc="sum",
    )
    # PJM sign convention: negative = export. Flip so +=export.
    return -piv


def derive() -> dict[str, dict[int, float]]:
    """Return ``{seam: {year: firm_floor_mw}}`` for the export seams."""
    out: dict[str, dict[int, float]] = {s: {} for s in EXPORT_SEAMS}
    print(
        f"PJM firm scheduled-export floor = p{int(FIRM_PCTL * 100)} of seam "
        f"scheduled export (MW, +=export):\n"
    )
    print(
        f"{'seam':8s} {'year':>5s} {'p10':>7s} {'p25':>7s} {'mean':>7s} "
        f"{'exp_hr%':>8s} -> floor_mw"
    )
    for year in YEARS:
        sched = _seam_scheduled_export(year)
        for seam in EXPORT_SEAMS:
            if seam not in sched:
                continue
            x = sched[seam].dropna()
            p10 = float(x.quantile(FIRM_PCTL))
            floor = max(0.0, round(p10 / 50.0) * 50.0)
            out[seam][year] = floor
            print(
                f"{seam:8s} {year:5d} {p10:7.0f} {x.quantile(0.25):7.0f} "
                f"{x.mean():7.0f} {100 * (x > 0).mean():8.0f} -> {floor:.0f}"
            )
    return out


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    table = derive()
    print("\n# Paste into INTERFACE_NEIGHBORS['PJM'] per neighbor:")
    for seam, per_year in table.items():
        cells = ", ".join(f"{y}: {int(f)}" for y, f in sorted(per_year.items()))
        print(f"    # {seam}: firm_export_floor_by_year={{{cells}}}")


if __name__ == "__main__":
    main()
