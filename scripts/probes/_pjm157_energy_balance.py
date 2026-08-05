"""pjm-157 §1 — PJM four-year energy-balance reconciliation, model vs EIA-930.

Phase-0 step 1 of the pjm-156 hand-back: establish which term absorbs the
apparent 2022 fossil surplus before any offer-stack work is proposed.  Reads
committed artifacts ONLY — the P1 hourly sidecars of the ``pjm2022_touchpoint``
bundle (2022) and the ``pjm152_collapse_A`` keeper bundle (2023-2025), plus the
raw EIA-930 ``PJM_region`` frames.  **No LP is solved and no year is scored**, so
this is legal under the active holdout freeze (CLAUDE.md rule 22).

The model side is put on the same footing as EIA-930's ``NG`` / ``D`` cells:
930 ``NG`` includes pumped-storage gross discharge and 930 ``D`` includes PS
pumping load, so the model's storage discharge is added to its generation and
its storage charge to its demand before differencing.

Caveat surfaced by the run: 2025's 930 ``TI`` cell fails its own identity
(``NG - TI - D = +14.68`` TWh against <= 0.04 in the other three years), so the
2025 interchange delta must be read against pjm-135's PJM tie-line measurement
(32.93 TWh) rather than the 930 cell.

The final section covers §5 question C — the bench's coal COVERAGE basis.  On an
identical 42-plant / 38,003 MW census in 2022 and 2023, 930 ``COL`` minus the
bench's CAMPD grid-delivered coal is +19.49 TWh in 2022 against +7.26 / +7.05 /
+11.02 in-sample.  That gap is why the two available bases disagree about the
SIGN of the model's 2022 coal error, and it must be resolved before the 2022 C1
and C2 coal rows are read.
"""

from __future__ import annotations

import gzip
import json
import os
from collections import defaultdict

import pandas as pd

TWH = 1e6

BUNDLES = {
    2022: "results/calibration/pjm2022_touchpoint",
    2023: "results/calibration/pjm152_collapse_A",
    2024: "results/calibration/pjm152_collapse_A",
    2025: "results/calibration/pjm152_collapse_A",
}

#: Non-physical LP pseudo-classes (the measured DA virtual layer) and the seam
#: class.  Both sit on the energy balance but neither is generation, so they are
#: split out of the "physical generation" aggregate.
VIRTUAL = {"VIRTUAL_INC", "VIRTUAL_DEC"}
SEAM = {"import"}


def read_model_year(year: int, bundle: str) -> dict:
    """Return one year's P1 model energy-balance terms in TWh.

    Args:
        year: solve year whose sidecars to read.
        bundle: bundle directory holding ``hourly/``.

    Returns:
        Mapping with the per-class totals (``cls``) plus the scalar balance
        terms: physical generation, virtual INC/DEC, seam net, zonal demand,
        slack, dump, storage charge and storage discharge.
    """
    ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    sy = pd.read_parquet(f"{bundle}/hourly/system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    st = pd.read_parquet(f"{bundle}/hourly/storage_{year}.parquet")
    st = st[st["pass"] == "P1"]

    cls = ch.groupby("klass")["mw"].sum() / TWH
    physical = cls[[k for k in cls.index if k not in VIRTUAL and k not in SEAM]]
    return {
        "cls": cls,
        "gen_phys": physical.sum(),
        "vinc": cls.get("VIRTUAL_INC", 0.0),
        "vdec": cls.get("VIRTUAL_DEC", 0.0),
        "seam": cls.get("import", 0.0),
        "demand": sy["demand"].sum() / TWH,
        "slack": sy["slack"].sum() / TWH,
        "dump": sy["dump"].sum() / TWH,
        "chg": st["charge_mw"].sum() / TWH,
        "dis": st["discharge_mw"].sum() / TWH,
    }


def read_measured_year(year: int) -> dict:
    """Return EIA-930 ``PJM_region`` demand / net generation / interchange, TWh.

    Args:
        year: calendar year to aggregate.

    Returns:
        Mapping with ``a_D``, ``a_NG`` and ``a_TI`` (positive ``TI`` = net export).
    """
    path = f"data/raw/eia-930/PJM_region_{year}.parquet"
    if not os.path.exists(path):
        path = "data/raw/PJM_region.parquet"
    df = pd.read_parquet(path)
    df = df[df["period"].dt.year == year]
    g = df.groupby("type")["value_mwh"].sum() / TWH
    return {"a_D": g.get("D"), "a_NG": g.get("NG"), "a_TI": g.get("TI")}


def coal_basis(year: int) -> dict:
    """Return the bench coal census and its coverage gap against EIA-930 ``COL``.

    Args:
        year: bench / 930 year to compare.

    Returns:
        Mapping with the bench coal plant count, nameplate MW and grid-delivered
        TWh, the 930 ``COL`` cell and their difference.
    """
    coal_groups = {"COAL_BIT", "COAL_PRB", "COAL_WC"}
    bench = json.load(gzip.open(f"frontend/data/backcast/bench/PJM/{year}.json.gz"))
    plants = [v for v in bench["bench"]["plants"].values() if v["group"] in coal_groups]

    path = f"data/raw/eia-930/PJM_fueltype_{year}.parquet"
    if not os.path.exists(path):
        path = "data/raw/PJM_fueltype.parquet"
    df = pd.read_parquet(path)
    df = df[df["period"].dt.year == year]
    col = df[df["fueltype"] == "COL"]["value_mwh"].sum() / TWH

    bench_twh = sum(v.get("c_ann") or 0.0 for v in plants)
    return {
        "n": len(plants),
        "mw": sum(v["npl"] for v in plants),
        "bench_twh": bench_twh,
        "col_930": col,
        "gap": col - bench_twh,
    }


def main() -> None:
    """Print the four-year balance table, the deltas and the model class totals."""
    rows = {y: {**read_model_year(y, b), **read_measured_year(y)} for y, b in BUNDLES.items()}
    years = sorted(rows)

    def line(label: str, fn, fmt: str = "{:>14.2f}") -> None:
        print(f"{label:<44}" + "".join(fmt.format(fn(rows[y])) for y in years))

    print("=" * 104)
    print("PJM ENERGY BALANCE — model (committed P1 sidecars) vs measured (EIA-930), TWh")
    print("=" * 104)
    print(f"{'term':<44}" + "".join(f"{y:>14}" for y in years))

    print("-- MODEL " + "-" * 94)
    line("physical generation (excl. virtuals/seam)", lambda r: r["gen_phys"])
    line("  + storage discharge", lambda r: r["dis"])
    line("  = model NG-equivalent", lambda r: r["gen_phys"] + r["dis"])
    line("zonal demand (LP RHS)", lambda r: r["demand"])
    line("  + storage charge", lambda r: r["chg"])
    line("  = model D-equivalent", lambda r: r["demand"] + r["chg"])
    line("net export via `import` class (+=export)", lambda r: -r["seam"])
    line("net virtual withdrawal (DEC-INC, +=sink)", lambda r: -(r["vinc"] + r["vdec"]))
    line("slack (unserved)", lambda r: r["slack"], "{:>14.4f}")
    line("dump", lambda r: r["dump"], "{:>14.4f}")

    print("-- MEASURED (EIA-930) " + "-" * 82)
    line("D  demand", lambda r: r["a_D"])
    line("NG net generation", lambda r: r["a_NG"])
    line("TI total interchange (+=net export)", lambda r: r["a_TI"])

    print("-- DELTA model - measured " + "-" * 78)
    line("NG-equivalent", lambda r: r["gen_phys"] + r["dis"] - r["a_NG"])
    line("D-equivalent", lambda r: r["demand"] + r["chg"] - r["a_D"])
    line("net export", lambda r: -r["seam"] - r["a_TI"])
    line("virtual (+ = phantom demand)", lambda r: -(r["vinc"] + r["vdec"]))

    print()
    print("-- closure checks (both should be ~0; 2025's 930 TI cell does NOT close)")
    line(
        "model LP residual",
        lambda r: (
            r["gen_phys"] + r["dis"] - r["chg"] + r["vinc"] + r["vdec"]
            + r["seam"] + r["slack"] - r["dump"] - r["demand"]
        ),
        "{:>14.4f}",
    )
    line("measured residual (NG-TI-D)", lambda r: r["a_NG"] - r["a_TI"] - r["a_D"], "{:>14.4f}")

    print()
    print("=" * 104)
    print("MODEL CLASS TOTALS, TWh")
    print("=" * 104)
    keys = sorted(set().union(*[set(rows[y]["cls"].index) for y in years]))
    print(f"{'class':<20}" + "".join(f"{y:>12}" for y in years))
    for k in keys:
        print(f"{k:<20}" + "".join(f"{rows[y]['cls'].get(k, 0.0):>12.2f}" for y in years))

    print()
    print("=" * 104)
    print("§5 QUESTION C — the bench's coal COVERAGE basis (930 COL vs CAMPD grid-delivered)")
    print("=" * 104)
    basis = {y: coal_basis(y) for y in years}
    print(f"{'term':<44}" + "".join(f"{y:>14}" for y in years))
    print(f"{'bench coal plants':<44}" + "".join(f"{basis[y]['n']:>14}" for y in years))
    print(f"{'bench coal nameplate MW':<44}" + "".join(f"{basis[y]['mw']:>14.0f}" for y in years))
    print(f"{'bench CAMPD coal (c_ann), TWh':<44}" + "".join(f"{basis[y]['bench_twh']:>14.2f}" for y in years))
    print(f"{'EIA-930 COL, TWh':<44}" + "".join(f"{basis[y]['col_930']:>14.2f}" for y in years))
    print(f"{'GAP (930 - bench), TWh':<44}" + "".join(f"{basis[y]['gap']:>14.2f}" for y in years))
    print(f"{'gap / 930 COL':<44}" + "".join(
        f"{basis[y]['gap'] / basis[y]['col_930'] * 100:>13.1f}%" for y in years))
    print()
    print("The census is IDENTICAL in 2022 and 2023, so this is not a missing-plant")
    print("effect. In-sample the gap runs 6-8 % of coal output; at 2022's output that")
    print("predicts 10-13 TWh against an observed 19.5. Until that ~7-9 TWh excess is")
    print("explained, the two bases disagree on the SIGN of the model's 2022 coal error")
    print("(+5.1 TWh against the bench's own 42 plants; -14.2 TWh against 930 COL).")


if __name__ == "__main__":
    main()
