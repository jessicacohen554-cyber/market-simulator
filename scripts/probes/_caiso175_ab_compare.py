"""caiso-175 A/B scorer — the CAISO TAC load-series intake.

Reads COMMITTED artifacts only (``hourly/system_<year>.parquet``,
``hourly/class_hourly_<year>.parquet``, ``metrics.json``,
``calibration_attestation.json``). **No LP, no replay.**

It reports exactly what ``PRECHECK-caiso175-tac-load-intake-2026-08-05.md``
pre-registered, and it is deliberately built as a **THREE-state** comparison:

===== ==================== ==================== =====================
year   keeper (caiso-174)   Arm A (this head)    Arm B (corrected)
===== ==================== ==================== =====================
2023   5 TACs, 744 h        5 TACs, 744 h        6 TACs, 8,759 h
2024   5 TACs, full         5 TACs, full         6 TACs, full
2025   5 TACs, full         5 TACs, full         6 TACs, full
===== ==================== ==================== =====================

so it prints **both** differences, because conflating them is the trap:

* **A − keeper** = *incidental code drift* between head ``ae7658d0`` and this
  one. Nothing to do with the intake.
* **B − A** = *the input correction alone*. This is the only quantity the
  session's claim rests on.

**THE ATTRIBUTION SEPARATES BY YEAR, FOR FREE** (PRECHECK §3a): 2024 and 2025
were already fully covered, so their ``B − A`` is **MWD-TAC alone**; 2023
carries MWD **plus** the coverage restoration, so its ``B − A`` is the sum and
the coverage leg is the remainder.

**GATED:** the determination, and only the determination (PRECHECK §2).
**REPORTED, NEVER GATED:** C3a/C3c movement in either direction, the Path-15
basis (KNOWN-OPEN 1), zonal price/flow movement and class energy. The corrected
input stays whichever way these move — rule 14 ``[R-ACCURATE]``.

Usage::

    PYTHONPATH=.:src python scripts/probes/_caiso175_ab_compare.py
    PYTHONPATH=.:src python scripts/probes/_caiso175_ab_compare.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/caiso174_measured_fleet"
CONTROL = REPO / "results/calibration/caiso175_control"
ARM = REPO / "results/calibration/caiso175_tac_intake"
YEARS = (2023, 2024, 2025)

BUNDLES = {"keeper": KEEPER, "A": CONTROL, "B": ARM}

#: Measured CAISO NP15-ZP26 annual-mean basis ($/MWh) — ASSESSMENT-caiso171 §4,
#: re-measured at caiso-173 F3. KNOWN-OPEN 1; reported, never gated.
MEASURED_BASIS = {2023: 5.947, 2024: 8.576, 2025: 5.727}

#: caiso-173 §C's PREDICTED share of ISO load misplaced north of Path 15 by the
#: MWD omission. This probe checks the realised NP15 share delta against it in
#: the MWD-only years, so §C is confirmed on data rather than re-asserted.
CAISO173_PREDICTED_NP15_PP = {2023: 0.241, 2024: 0.297, 2025: 0.243}


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def _classes(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def load_weighted_price(df: pd.DataFrame) -> float:
    """Load-weighted mean price ($/MWh) — the C3a basis."""
    return float((df["price"] * df["demand"]).sum() / df["demand"].sum())


def basis(df: pd.DataFrame, a: str = "NP15", b: str = "ZP26") -> float:
    """Annual-mean price basis a - b ($/MWh), clock-invariant simple mean."""
    p = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")
    if a not in p.columns or b not in p.columns:
        return float("nan")
    return float((p[a] - p[b]).mean())


def zone_share(df: pd.DataFrame, zone: str) -> float:
    """Annual demand share of ``zone`` as the LP saw it."""
    tot = df.groupby("zone")["demand"].sum()
    return float(tot.get(zone, 0.0) / tot.sum())


def zone_price(df: pd.DataFrame, zone: str) -> float:
    """Simple annual-mean price in ``zone`` ($/MWh)."""
    z = df[df["zone"] == zone]
    return float(z["price"].mean()) if len(z) else float("nan")


def class_twh(df: pd.DataFrame, needle: str) -> float:
    """Annual TWh for classes whose name contains ``needle`` (case-insensitive)."""
    m = df[df["klass"].str.contains(needle, case=False, na=False)]
    return float(m["mw"].sum() / 1e6)


def determination(bundle: Path) -> dict:
    """The scored determination and its caveat/FAIL counts, off metrics.json."""
    p = bundle / "metrics.json"
    if not p.exists():
        return {"determination": "(absent)", "n_fail": None, "n_scored": None}
    m = json.loads(p.read_text())
    crit = m.get("criteria", {})
    rows = list(crit.values()) if isinstance(crit, dict) else list(crit)
    fails = [r for r in rows if str(r.get("status", "")).upper().startswith("FAIL")]
    skipped = [r for r in rows if str(r.get("status", "")).upper() == "SKIPPED"]
    return {
        "determination": m.get("determination"),
        "n_fail": len(fails),
        "n_scored": len(rows) - len(skipped),
        "n_skipped": len(skipped),
        "caveats": (m.get("caveats") or {}).get("ledgered"),
    }


def dof(bundle: Path) -> dict:
    """The DOF ledger counts — PRECHECK §2's pre-registered invariant."""
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return {}
    fp = json.loads(p.read_text()).get("free_parameters", {})
    return {"n_entries": fp.get("n_entries"), "n_residual": fp.get("n_residual")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    rec: dict = {"years": list(YEARS), "determination": {}, "dof": {}, "rows": []}

    print("=" * 78)
    print("caiso-175 A/B — the CAISO TAC load-series intake")
    print("  A = as-committed series (5 TACs; 2023 = 744/8760 h)")
    print("  B = corrected series    (6 TACs incl. MWD-TAC; 2023 = 8759/8760 h)")
    print("=" * 78)

    print("\n-- GATED: determination (PRECHECK §2) " + "-" * 40)
    for name, b in BUNDLES.items():
        d = determination(b)
        rec["determination"][name] = d
        rec["dof"][name] = dof(b)
        print(
            f"  {name:<7} {d['determination']:<26} FAILs={d['n_fail']}  "
            f"scored={d['n_scored']}  skipped={d['n_skipped']}  "
            f"DOF={rec['dof'][name].get('n_entries')}/"
            f"{rec['dof'][name].get('n_residual')}"
        )

    print("\n-- The intake reached the LP: zonal demand share (pp) " + "-" * 24)
    print(
        f"  {'year':<6}{'zone':<11}{'A':>10}{'B':>10}{'B-A (pp)':>11}"
        f"{'caiso-173 §C':>14}"
    )
    for y in YEARS:
        a, b = _system(CONTROL, y), _system(ARM, y)
        for z in ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"):
            sa, sb = zone_share(a, z), zone_share(b, z)
            pred = (
                f"{-CAISO173_PREDICTED_NP15_PP[y]:+.3f}"
                if z == "NP15"
                else ""
            )
            row = {
                "year": y,
                "zone": z,
                "share_A": sa,
                "share_B": sb,
                "d_pp": (sb - sa) * 100,
            }
            rec["rows"].append(row)
            print(
                f"  {y:<6}{z:<11}{sa:>10.5f}{sb:>10.5f}{(sb - sa) * 100:>11.3f}"
                f"{pred:>14}"
            )

    print("\n-- REPORTED, NEVER GATED: C3a load-weighted mean LMP ($/MWh) " + "-" * 17)
    print(
        f"  {'year':<6}{'keeper':>10}{'A':>10}{'B':>10}"
        f"{'A-keeper':>11}{'B-A':>9}{'B-A %':>9}"
    )
    for y in YEARS:
        k, a, b = _system(KEEPER, y), _system(CONTROL, y), _system(ARM, y)
        pk, pa, pb = (
            load_weighted_price(k),
            load_weighted_price(a),
            load_weighted_price(b),
        )
        rec.setdefault("c3a", {})[y] = {
            "keeper": pk,
            "A": pa,
            "B": pb,
            "drift": pa - pk,
            "treat": pb - pa,
        }
        print(
            f"  {y:<6}{pk:>10.3f}{pa:>10.3f}{pb:>10.3f}"
            f"{pa - pk:>11.3f}{pb - pa:>9.3f}{(pb - pa) / pa * 100:>8.2f}%"
        )

    print("\n-- REPORTED: zonal mean price ($/MWh), B - A " + "-" * 33)
    print(f"  {'year':<6}" + "".join(f"{z:>13}" for z in
          ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")))
    for y in YEARS:
        a, b = _system(CONTROL, y), _system(ARM, y)
        cells = "".join(
            f"{zone_price(b, z) - zone_price(a, z):>13.3f}"
            for z in ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
        )
        print(f"  {y:<6}{cells}")

    print("\n-- REPORTED: KNOWN-OPEN 1, NP15-ZP26 basis ($/MWh) " + "-" * 27)
    print(
        f"  {'year':<6}{'measured':>10}{'A':>9}{'B':>9}{'B-A':>9}"
        f"{'A % of meas':>13}{'B % of meas':>13}"
    )
    for y in YEARS:
        a, b = _system(CONTROL, y), _system(ARM, y)
        ba, bb, m = basis(a), basis(b), MEASURED_BASIS[y]
        rec.setdefault("basis", {})[y] = {"measured": m, "A": ba, "B": bb}
        print(
            f"  {y:<6}{m:>10.3f}{ba:>9.3f}{bb:>9.3f}{bb - ba:>9.3f}"
            f"{ba / m * 100:>12.1f}%{bb / m * 100:>12.1f}%"
        )

    print("\n-- REPORTED: class energy (TWh), B - A " + "-" * 39)
    needles = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "hydro", "solar", "wind")
    print(f"  {'year':<6}" + "".join(f"{n:>13}" for n in needles))
    for y in YEARS:
        a, b = _classes(CONTROL, y), _classes(ARM, y)
        if a is None or b is None:
            continue
        cells = "".join(
            f"{class_twh(b, n) - class_twh(a, n):>13.4f}" for n in needles
        )
        print(f"  {y:<6}{cells}")

    if args.json:
        args.json.write_text(json.dumps(rec, indent=2) + "\n")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
