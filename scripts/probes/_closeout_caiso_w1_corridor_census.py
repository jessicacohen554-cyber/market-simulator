"""Close-out CAISO wave 1, step 0b (ZERO LP): PNW / DSW net import vs EIA-930 by corridor and month.

The R-CAISO-7 Object-1 table (``_rcaiso7_dsw_import_census.py``) re-taken on the
CURRENT fold: the R-CAISO-20 fold legs (``rcaiso20_A_<year>``, keeper fold
``2026-09-30-caiso-r20-overnight-touchpoints``), read straight from their shard
commits (rule 33 provenance SHAs, ``docs/records/caiso/r-caiso-20/RESULT-r-caiso-20-2026-09-30.md``)
because the committed fold bundle carries no per-unit P1 sidecar. Model corridor
net import = the P1 sum of every unit in the corridor's WECC zone (imports
positive, the export sink negative), the same construction R-CAISO-7 used; the
measured side is ``derive_caiso_import_tranches.corridor_net_import`` (EIA-930
CISO interchange by DIBA, model clock).

Reports per year: corridor TWh model / EIA-930, the monthly gap per corridor,
per-tranche TWh, and the closure arithmetic against the C1 CC_REGULAR miss.
Writes JSON to the path given by ``--out`` (default: stdout only).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_closeout_caiso_w1_corridor_census.py [--out PATH]
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

LEGS = {  # R-CAISO-20 RESULT, "Leg provenance"
    2019: "fe270e64e6ba0ce82786f37e6baa0e7bc0394693",
    2020: "616bef4e01e8bf6468336cfd9f9a94caedede279",
    2021: "c1040fa26244dc5624eb421d4e2a56795e8886f7",
}
CORRIDORS = ("WECC_PNW", "WECC_DSW")
_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), np.array(_MONTH_DAYS) * 24)


def _extract(tmp: Path, year: int) -> Path:
    """Unpack one fold-leg bundle's hourly sidecars from its shard commit."""
    path = f"results/calibration/rcaiso20_A_{year}/hourly"
    arc = subprocess.run(
        ["git", "archive", LEGS[year], path], check=True, capture_output=True
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp)], input=arc, check=True)
    return tmp / path


def census_year(h: Path, year: int, meas: pd.DataFrame) -> dict:
    """Return the corridor census for one fold year."""
    u = pd.read_parquet(
        h / f"unit_hourly_{year}.parquet",
        columns=["unit_id", "zone", "hour", "mw"],
        filters=[("zone", "in", list(CORRIDORS))],
    )
    out: dict = {"corridors": {}, "tranches_twh": {}}
    for z in CORRIDORS:
        uz = u[u.zone == z]
        m = uz.groupby("hour").mw.sum().reindex(range(8760)).fillna(0).to_numpy()
        a = meas.loc[year][z].reindex(range(8760)).to_numpy()
        monthly = {}
        for mo in range(1, 13):
            k = MONTH_OF_HOUR == mo
            monthly[mo] = {
                "model_twh": round(float(m[k].sum()) / 1e6, 2),
                "eia930_twh": round(float(np.nansum(a[k])) / 1e6, 2),
            }
            monthly[mo]["gap_twh"] = round(
                monthly[mo]["model_twh"] - monthly[mo]["eia930_twh"], 2
            )
        out["corridors"][z] = {
            "model_twh": round(float(m.sum()) / 1e6, 2),
            "eia930_twh": round(float(np.nansum(a)) / 1e6, 2),
            "eia930_missing_hours": int(np.isnan(a).sum()),
            "monthly": monthly,
        }
        out["corridors"][z]["gap_twh"] = round(
            out["corridors"][z]["model_twh"] - out["corridors"][z]["eia930_twh"], 2
        )
        for uid, g in uz.groupby("unit_id"):
            out["tranches_twh"][uid] = round(float(g.mw.sum()) / 1e6, 2)
    out["total_gap_twh"] = round(
        sum(out["corridors"][z]["gap_twh"] for z in CORRIDORS), 2
    )
    return out


def main() -> None:
    """Run the census over the three fold years; print and optionally write JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    meas = corridor_net_import(years=tuple(LEGS))
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for y in LEGS:
            res[str(y)] = census_year(_extract(Path(tmp), y), y, meas)
    text = json.dumps(res, indent=1, default=float)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
