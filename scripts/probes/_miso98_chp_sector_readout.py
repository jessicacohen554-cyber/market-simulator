"""miso-98 A/B readout: the CHP sector correction, arm A (absent) vs arm B (measured).

No-LP. Reads the two solved bundles and prints, in the order the pre-registered
prediction (``results/calibration/FINDING-miso97-chp-sector-btm-2026-07.md``
§5.1) states it:

1. **The A-arm control check** — arm A's model class energies against the
   registered keeper's ``hourly/class_hourly_*.parquet``. miso-92 §7 records
   that post-CAMPD-envelope-correction replays do not reproduce the keeper's
   registered numbers, so this is a structural-agreement check, not an equality
   check: a mis-specified arm shows up here as a class moving by far more than
   the envelope drift, and the B arm must not be trusted until A is read.
2. **The CHP class table** — grid-delivered model vs bench TWh per class-year in
   both arms.  BOTH sides move by construction: the sector share rescales LP
   capacity, the steam-following floor AND the benchmark's BTM subtrahend by the
   same ``(1 - s)`` (§2.1), so a bench that did not move would be the bug.
3. **The non-CHP control** — every other scored class. The delta enters only
   through ``chp_btm_pct``, so a large non-CHP move is an indirect price/merit
   response worth naming, not a direct effect.
4. **Headline criteria** — the C1/C2/C3 statuses each arm's own scorer wrote.

Usage::

    python scripts/probes/_miso98_chp_sector_readout.py \
        results/calibration/miso98_chp_sector_A results/calibration/miso98_chp_sector_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.session_score import class_table  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso88_egrid_hr"
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")


def keeper_class_energy() -> pd.DataFrame:
    """Return the registered keeper's P1 model TWh per (year, class)."""
    rows = []
    for path in sorted((KEEPER / "hourly").glob("class_hourly_*.parquet")):
        df = pd.read_parquet(path)
        df = df[df["pass"] == "P1"]
        for (year, klass), g in df.groupby(["year", "klass"]):
            rows.append(
                {"year": int(year), "class": str(klass), "keeper": g["mw"].sum() / 1e6}
            )
    return pd.DataFrame(rows)


def _pct(model: float, bench: float) -> float:
    """Percent error of ``model`` against ``bench`` (nan when bench is zero)."""
    return (model / bench - 1.0) * 100.0 if bench else float("nan")


def control_check(arm_a: pd.DataFrame) -> None:
    """Print arm A's class energies against the registered keeper's."""
    keeper = keeper_class_energy()
    # ``class`` is a keyword, so itertuples renames it — work on ``klass``.
    merged = arm_a.merge(keeper, on=["year", "class"], how="left").rename(
        columns={"class": "klass"}
    )
    print("=== 1. A-ARM CONTROL vs registered keeper 2026-07-25-miso-88-egrid-hr")
    print("    (structural agreement, NOT equality — miso-92 §7 envelope drift)")
    print(f"    {'year':<6}{'class':<14}{'keeper TWh':>12}{'arm A TWh':>12}{'drift %':>10}")
    for r in merged.sort_values(["year", "klass"]).itertuples(index=False):
        if r.keeper != r.keeper:  # nan — class not in the keeper sidecar
            continue
        drift = _pct(r.model, r.keeper)
        mark = "  <-- CHECK" if abs(drift) > 5.0 else ""
        print(
            f"    {r.year:<6}{r.klass:<14}{r.keeper:12.3f}"
            f"{r.model:12.3f}{drift:10.2f}{mark}"
        )


def class_block(title: str, a: pd.DataFrame, b: pd.DataFrame, classes) -> None:
    """Print the model/bench/%-error table for ``classes`` in both arms."""
    merged = (
        a.merge(b, on=["year", "class"], suffixes=("_a", "_b"), how="outer")
        .sort_values(["class", "year"])
        .rename(columns={"class": "klass"})  # keyword — see control_check
    )
    print(f"\n=== {title}")
    print(
        f"    {'class':<14}{'year':<6}"
        f"{'A model':>10}{'A bench':>10}{'A err%':>9}"
        f"{'B model':>10}{'B bench':>10}{'B err%':>9}{'|err| move':>12}"
    )
    for r in merged.itertuples(index=False):
        klass = r.klass
        if klass not in classes:
            continue
        ea, eb = _pct(r.model_a, r.bench_a), _pct(r.model_b, r.bench_b)
        move = abs(eb) - abs(ea)
        verdict = "worse" if move > 0.5 else ("better" if move < -0.5 else "flat")
        print(
            f"    {klass:<14}{r.year:<6}"
            f"{r.model_a:10.3f}{r.bench_a:10.3f}{ea:9.1f}"
            f"{r.model_b:10.3f}{r.bench_b:10.3f}{eb:9.1f}"
            f"{move:+9.1f} {verdict}"
        )


def criteria(bundle: Path, tag: str) -> None:
    """Print the criteria statuses the bundle's own scorer wrote."""
    path = bundle / "metrics.json"
    if not path.exists():
        print(f"    {tag}: no metrics.json")
        return
    m = json.loads(path.read_text())
    stat = {k: v.get("status") for k, v in (m.get("criteria") or {}).items()}
    print(f"    {tag}: {m.get('determination')}  " + "  ".join(
        f"{k}={v}" for k, v in stat.items()
    ))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arm_a", type=Path)
    ap.add_argument("arm_b", type=Path)
    args = ap.parse_args()

    a = class_table(args.arm_a.name)
    b = class_table(args.arm_b.name)

    control_check(a)
    class_block("2. CHP CLASSES — the pre-registered lines", a, b, CHP_CLASSES)
    others = sorted(set(a["class"]) - set(CHP_CLASSES))
    class_block("3. NON-CHP CONTROL", a, b, others)

    print("\n=== 4. HEADLINE CRITERIA (each arm's own scorer)")
    criteria(args.arm_a, "arm A")
    criteria(args.arm_b, "arm B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
