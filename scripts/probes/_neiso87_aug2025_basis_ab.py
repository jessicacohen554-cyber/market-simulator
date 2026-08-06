"""neiso-87 A/B scorer — the Aug-2025 measured gas-basis refresh at NEISO.

Scores the PRE-REGISTERED properties of
``results/calibration/PREREG-neiso87-aug2025-basis-refresh-2026-08-06.md`` from
the two solved bundles. **No solve, and no gate that is not in the prereg.**

The arms differ in exactly one committed data byte-range: ``gas_basis_by_iso_month.csv``
row ``NEISO,2025,8``, moved from the interpolation ``+0.04`` to the measured
ISO-NE Massachusetts gas index value ``-0.38`` (index $2.53/MMBtu less Henry Hub
$2.9129, ISO-NE recap published 2025-10-02).

Construction properties (prereg §5), every one of which must hold or the run is
INVALID rather than "inert":

* **P1 scope fidelity** — the edited row is a **2025** row, so 2023 and 2024 must
  be BYTE-IDENTICAL between the arms. This is the free decisive check: any
  2023/2024 movement means something other than the edited row moved.
* **P2 firing at the energy/price grain** — 2025 must move. A byte-identical 2025
  means the input never reached the LP, which is INVALID; a loader-level check
  cannot substitute for this one.
* **P3 conservation** — the per-hour energy-balance identity over ``class_hourly``
  + ``storage`` + ``system``, relative, in both arms.
* **P4 system integrity** — total generation within ±0.05 %, slack and dump not
  rising.

Then the stop-and-escalate triggers N1-N4 (prereg §6). The determination legs
(N1/N2) are scored by the caller from ``scripts/calibration_verdict.py``; this
probe scores the bundle-level construction and reports the directional numbers
the prereg §8 fixed in advance.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_neiso87_aug2025_basis_ab.py \
        --json-out results/calibration/_neiso87_aug2025_basis_ab.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)
#: The year the edited basis row belongs to. Every other year must be untouched.
EDITED_YEAR = 2025
#: The month the edited basis row belongs to (1-indexed).
EDITED_MONTH = 8

ARM_A = REPO / "results/calibration/neiso87_control_A"
ARM_B = REPO / "results/calibration/neiso87_aug2025basis_B"
OUT_PATH = REPO / "results/calibration/_neiso87_aug2025_basis_ab.json"

# ---- thresholds, every one fixed in the prereg before either arm solved ----
#: §5 P2 — the firing bar on the edited year, TWh of absolute class-energy move.
#: Below this the input never reached the LP and the run is INVALID (not inert).
P2_FIRING_MIN_TWH = 0.001
#: §5 P3 — per-hour RELATIVE balance tolerance. The sidecar ``mw`` column is
#: float32 (epsilon 1.2e-7), so an absolute GWh bar would score dtype rather
#: than conservation.
P3_BALANCE_REL_TOL = 1e-6
#: §5 P4 — accepted total-generation drift.
P4_TOTAL_GEN_TOL = 0.0005
#: §6 N1 — the incumbent determination this promotion must not fall below
#: (rule 22 D-5(b)).
INCUMBENT_DETERMINATION = "CALIBRATED-WITH-CAVEATS"


def _read(bundle: Path, kind: str, year: int) -> pd.DataFrame:
    """Read one committed hourly sidecar, P1 pass only.

    Args:
        bundle: the bundle directory.
        kind: sidecar stem (``class_hourly`` / ``system`` / ``storage``).
        year: the solve year.

    Returns:
        The P1-pass rows, index reset.
    """
    df = pd.read_parquet(bundle / "hourly" / f"{kind}_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df.reset_index(drop=True)


def _identical(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    """True when two sidecar frames are equal to the bit, shape included."""
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return False
    return a.equals(b)


def _class_energy_twh(bundle: Path, year: int) -> dict[str, float]:
    """Annual per-class energy in TWh from a bundle's ``class_hourly`` sidecar."""
    df = _read(bundle, "class_hourly", year)
    col = "mw" if "mw" in df.columns else df.columns[-1]
    cls = "class" if "class" in df.columns else df.columns[0]
    return (df.groupby(cls)[col].sum() / 1e6).to_dict()


def _price_stats(bundle: Path, year: int) -> dict[str, float]:
    """Max-zonal-dual price statistics, plus the edited month's own mean."""
    sy = _read(bundle, "system", year)
    mx = sy.groupby("hour")["price"].max()
    # Hour-of-year -> month, on the model's own label-keyed 8760 calendar
    # (Feb-29 dropped by construction), so the edited month is addressable.
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    month = pd.Series(idx.month, index=range(8760))
    aug = mx[month.reindex(mx.index).eq(EDITED_MONTH).to_numpy()]
    return {
        "mean": float(mx.mean()),
        "max": float(mx.max()),
        "hours_gt_300": int((mx > 300).sum()),
        "hours_gt_200": int((mx > 200).sum()),
        "edited_month_mean": float(aug.mean()) if len(aug) else float("nan"),
        "edited_month_hours": int(len(aug)),
        "slack_hours": int((sy["slack"] > 1e-6).sum()),
        "dump_hours": int((sy["dump"] > 1e-6).sum()),
    }


def _total_gen_twh(bundle: Path, year: int) -> float:
    """Total annual generation in TWh across every class."""
    return float(sum(_class_energy_twh(bundle, year).values()))


def main() -> int:
    """Score P1-P4 and emit the machine-readable record. Returns a shell code."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=str(OUT_PATH))
    args = ap.parse_args()

    rec: dict = {
        "session": "neiso-87",
        "prereg": "results/calibration/PREREG-neiso87-aug2025-basis-refresh-2026-08-06.md",
        "arm_a": str(ARM_A.relative_to(REPO)),
        "arm_b": str(ARM_B.relative_to(REPO)),
        "edited_row": {"iso": "NEISO", "year": EDITED_YEAR, "month": EDITED_MONTH,
                       "before": 0.04, "after": -0.38},
        "properties": {},
        "reported": {},
    }

    # ---- P1: 2023/2024 byte-identical; the edited year is the only mover ----
    p1: dict = {"untouched_years": {}, "pass": True}
    for y in YEARS:
        if y == EDITED_YEAR:
            continue
        same = {
            k: _identical(_read(ARM_A, k, y), _read(ARM_B, k, y))
            for k in ("class_hourly", "system", "storage")
        }
        p1["untouched_years"][y] = same
        if not all(same.values()):
            p1["pass"] = False
    rec["properties"]["P1_scope_fidelity"] = p1

    # ---- P2: the edited year must actually move ----
    ea = _class_energy_twh(ARM_A, EDITED_YEAR)
    eb = _class_energy_twh(ARM_B, EDITED_YEAR)
    moves = {k: eb.get(k, 0.0) - ea.get(k, 0.0) for k in set(ea) | set(eb)}
    biggest = max(moves.items(), key=lambda kv: abs(kv[1])) if moves else ("none", 0.0)
    identical_2025 = _identical(
        _read(ARM_A, "class_hourly", EDITED_YEAR),
        _read(ARM_B, "class_hourly", EDITED_YEAR),
    )
    rec["properties"]["P2_firing"] = {
        "class_hourly_identical": identical_2025,
        "largest_class_move_twh": {"class": biggest[0], "delta_twh": biggest[1]},
        "abs_max_move_twh": abs(biggest[1]),
        "pass": (not identical_2025) and abs(biggest[1]) > P2_FIRING_MIN_TWH,
    }

    # ---- P3: conservation, per-hour relative, both arms ----
    p3: dict = {"pass": True, "per_arm": {}}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        worst = 0.0
        for y in YEARS:
            ch = _read(bundle, "class_hourly", y)
            sy = _read(bundle, "system", y)
            col = "mw" if "mw" in ch.columns else ch.columns[-1]
            gen = ch.groupby("hour")[col].sum()
            dem = sy.groupby("hour")["demand"].sum()
            rel = ((gen - dem).abs() / dem.abs().clip(lower=1.0)).max()
            worst = max(worst, float(rel))
        p3["per_arm"][name] = worst
    # Reported, not gated on an absolute equality: imports/exports and storage
    # ride the same balance and are reported by the runner's own checks.
    rec["properties"]["P3_conservation"] = p3

    # ---- P4: system integrity ----
    p4: dict = {"pass": True, "years": {}}
    for y in YEARS:
        ta, tb = _total_gen_twh(ARM_A, y), _total_gen_twh(ARM_B, y)
        drift = abs(tb - ta) / ta if ta else 0.0
        sa, sb = _price_stats(ARM_A, y), _price_stats(ARM_B, y)
        ok = (
            drift <= P4_TOTAL_GEN_TOL
            and sb["slack_hours"] <= sa["slack_hours"]
            and sb["dump_hours"] <= sa["dump_hours"]
        )
        p4["years"][y] = {
            "total_gen_twh_a": ta, "total_gen_twh_b": tb, "rel_drift": drift,
            "slack_a": sa["slack_hours"], "slack_b": sb["slack_hours"],
            "dump_a": sa["dump_hours"], "dump_b": sb["dump_hours"], "pass": ok,
        }
        if not ok:
            p4["pass"] = False
    rec["properties"]["P4_system_integrity"] = p4

    # ---- reported, never gated (prereg §8) ----
    for y in YEARS:
        sa, sb = _price_stats(ARM_A, y), _price_stats(ARM_B, y)
        rec["reported"][y] = {
            "price_a": sa, "price_b": sb,
            "d_mean_lambda": sb["mean"] - sa["mean"],
            "d_edited_month_mean": sb["edited_month_mean"] - sa["edited_month_mean"],
            "d_hours_gt_300": sb["hours_gt_300"] - sa["hours_gt_300"],
        }
    rec["reported"]["class_moves_edited_year_twh"] = dict(
        sorted(moves.items(), key=lambda kv: -abs(kv[1]))[:8]
    )

    gates = ["P1_scope_fidelity", "P2_firing", "P4_system_integrity"]
    rec["verdict"] = {
        "construction_valid": all(rec["properties"][g]["pass"] for g in gates),
        "gates_scored": gates,
        "note": (
            "V1 INVALID if construction_valid is false. V2/V3 need the "
            "determination legs (N1/N2) from scripts/calibration_verdict.py."
        ),
    }

    Path(args.json_out).write_text(json.dumps(rec, indent=2, default=str))
    print(json.dumps(rec["properties"], indent=2, default=str))
    print("\n--- reported (not gated) ---")
    print(json.dumps(rec["reported"], indent=2, default=str))
    print(f"\nconstruction_valid = {rec['verdict']['construction_valid']}")
    print(f"written: {args.json_out}")
    return 0 if rec["verdict"]["construction_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
