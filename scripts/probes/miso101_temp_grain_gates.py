"""Score the miso-101 pre-registered gates from the two committed arm bundles.

Reads ONLY the committed bundle artifacts (the ``hourly/class_hourly_<year>``
sidecars plus the per-plant ``dispatch/<year>_P1.parquet``) and the CAMPD meter
— no LP, no re-solve. Every gate below is quoted verbatim from
``results/calibration/PREREG-miso101-stchp-temp-grain-2026-07-28.md`` §4; a gate
that prereg does not contain is not scored here.

* **G1 phase** — the Beaumont ST_CHP slice model profile troughs in h14-h16.
* **G2 level neutrality** — ST_CHP / CT_CHP annual energy moves < 1.0 %.
* **G3 scope containment** — ST_GAS / COAL / CC_* annual energy moves < 0.1 %.
* **G4 direction** — the Beaumont-level correlation against its measured
  hour-of-day profile improves.

Usage::

    python scripts/probes/miso101_temp_grain_gates.py \
        --control results/calibration/miso101_control_A \
        --arm     results/calibration/miso101_tempgrain_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.campd import states_for_iso  # noqa: E402

YEARS = (2023, 2024, 2025)
BEAUMONT = 50625
#: In scope for the arm — these MAY move (G2 bounds how much).
IN_SCOPE = ("ST_CHP", "CT_CHP")
#: Out of scope — the arm must not touch their CAPABILITY (verified 0.000 % on
#: the reconstructed fleet, no LP). Their dispatched energy may still move a
#: little: when the in-scope cogens' hourly capability changes, the LP rebalances
#: and other classes fill the gap. That is a legitimate dispatch response, not a
#: scope leak — G3's 0.1 % bound is sized to catch a leak, not to forbid it.
#: Coal is three separate model classes in the hourly sidecar, never "COAL".
OUT_SCOPE = (
    "ST_GAS",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
)


def _class_energy(bundle: Path, year: int) -> pd.Series:
    """Annual TWh by class from the committed hourly sidecar."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum() / 1e6


def _class_profile(bundle: Path, year: int, klass: str) -> np.ndarray:
    """Hour-of-day mean MW for one class."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    hod = df["hour"].to_numpy() % 24
    mw = df["mw"].to_numpy()
    return np.array([mw[hod == h].mean() for h in range(24)])


def _plant_profile(bundle: Path, year: int, plant: int, klass: str) -> np.ndarray | None:
    """Hour-of-day mean MW for one plant-class slice from the dispatch parquet.

    Reads with predicate push-down: the file is ~24.5 M rows / 80 MB per year and
    this probe may run alongside an LP, so the whole frame is never materialized.
    Sums the plant's tranches within the class before taking the profile — a
    plant is several LP units and the slice is their total.
    """
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(
        path,
        columns=["plant_code", "klass", "hour", "mw", "pass"],
        filters=[("plant_code", "==", plant), ("klass", "==", klass)],
    )
    if df.empty:
        return None
    df = df[df["pass"] == "P1"]
    if df.empty:
        return None
    tot = df.groupby("hour")["mw"].sum()  # tranches -> plant slice
    hod = tot.index.to_numpy() % 24
    mw = tot.to_numpy(dtype=float)
    return np.array([mw[hod == h].mean() for h in range(24)])


def _measured_profile(year: int, plant: int) -> np.ndarray | None:
    """Measured CAMPD hour-of-day mean gross load for a plant."""
    unit_dir = REPO / "data" / "raw" / "campd-unit-level"
    frames = []
    for state in states_for_iso("MISO"):
        path = unit_dir / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=["facilityId", "hour", "grossLoad"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"] == plant]
        if not df.empty:
            frames.append(df)
    if not frames:
        return None
    raw = pd.concat(frames, ignore_index=True)
    raw["grossLoad"] = pd.to_numeric(raw["grossLoad"], errors="coerce").fillna(0.0)
    grp = raw.groupby("hour")["grossLoad"].mean()
    return grp.reindex(range(24)).to_numpy(dtype=float)


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    report: dict = {"years": list(YEARS), "gates": {}, "detail": {}}
    verdicts: dict[str, bool] = {}

    # ---- G2 / G3: annual energy movement by class -------------------------
    print("=== class annual energy, TWh (control -> arm) ===")
    moves: dict[str, list[float]] = {}
    for year in YEARS:
        a = _class_energy(args.control, year)
        b = _class_energy(args.arm, year)
        print(f"\n{year}")
        for klass in sorted(set(a.index) | set(b.index)):
            ea, eb = float(a.get(klass, 0.0)), float(b.get(klass, 0.0))
            pct = 100.0 * (eb / ea - 1.0) if ea else 0.0
            moves.setdefault(klass, []).append(pct)
            tag = ""
            if klass in IN_SCOPE:
                tag = "  <- in scope (G2)"
            elif klass in OUT_SCOPE:
                tag = "  <- OUT of scope (G3)"
            print(f"  {klass:12s} {ea:9.4f} -> {eb:9.4f}  ({pct:+7.3f} %){tag}")

    g2 = {k: max(abs(v) for v in moves.get(k, [0.0])) for k in IN_SCOPE if k in moves}
    g3 = {k: max(abs(v) for v in moves.get(k, [0.0])) for k in OUT_SCOPE if k in moves}
    verdicts["G2_level_neutrality"] = all(v < 1.0 for v in g2.values())
    verdicts["G3_scope_containment"] = all(v < 0.1 for v in g3.values())
    report["detail"]["max_abs_move_pct"] = {**g2, **g3}

    print("\n=== G2 level neutrality (in-scope classes, bound 1.0 %) ===")
    for k, v in g2.items():
        print(f"  {k:12s} max |move| {v:6.3f} %   {'PASS' if v < 1.0 else 'FAIL'}")
    print("=== G3 scope containment (out-of-scope classes, bound 0.1 %) ===")
    for k, v in g3.items():
        print(f"  {k:12s} max |move| {v:6.3f} %   {'PASS' if v < 0.1 else 'FAIL'}")

    # ---- G1 / G4: Beaumont slice phase + direction ------------------------
    print("\n=== G1 phase / G4 direction: Beaumont 50625 ST_CHP slice ===")
    g1_ok, g4_ok = [], []
    for year in YEARS:
        pa = _plant_profile(args.control, year, BEAUMONT, "ST_CHP")
        pb = _plant_profile(args.arm, year, BEAUMONT, "ST_CHP")
        meas = _measured_profile(year, BEAUMONT)
        if pb is None or meas is None:
            print(f"  {year}: per-plant slice unavailable — falling back to class")
            pa = _class_profile(args.control, year, "ST_CHP")
            pb = _class_profile(args.arm, year, "ST_CHP")
        trough = int(np.argmin(pb))
        ok1 = trough in (14, 15, 16)
        ra = float(np.corrcoef(pa, meas)[0, 1]) if meas is not None and pa.std() > 0 else float("nan")
        rb = float(np.corrcoef(pb, meas)[0, 1]) if meas is not None and pb.std() > 0 else float("nan")
        ok4 = (not np.isnan(rb)) and (np.isnan(ra) or rb > ra)
        g1_ok.append(ok1)
        g4_ok.append(ok4)
        amp_a = float(pa.max() - pa.min())
        amp_b = float(pb.max() - pb.min())
        print(
            f"  {year}: trough h{trough:02d} ({'PASS' if ok1 else 'FAIL'})  "
            f"amp {amp_a:.3f} -> {amp_b:.3f} MW  "
            f"corr vs meter {ra:+.3f} -> {rb:+.3f} ({'PASS' if ok4 else 'FAIL'})"
        )
        report["detail"].setdefault("beaumont", {})[str(year)] = {
            "trough_hour": trough,
            "amp_control": amp_a,
            "amp_arm": amp_b,
            "corr_control": ra,
            "corr_arm": rb,
        }
    verdicts["G1_phase"] = all(g1_ok)
    verdicts["G4_direction"] = all(g4_ok)

    report["gates"] = verdicts
    print("\n=== PRE-REGISTERED GATE VERDICTS ===")
    for name, ok in verdicts.items():
        print(f"  {name:24s} {'PASS' if ok else 'FAIL'}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
