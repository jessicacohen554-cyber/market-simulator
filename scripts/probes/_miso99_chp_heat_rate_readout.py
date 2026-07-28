"""miso-99 A/B readout: measured power-only CHP heat rates, arm A (off) vs B (on).

No-LP. Reads the two solved bundles and prints, in the order the pre-registered
prediction (``results/calibration/FINDING-miso99-chp-heat-rate-2026-07-28.md``
§3) states it:

1. **The A-arm control check** — arm A's model class energies against the
   registered keeper's ``hourly/class_hourly_*.parquet``. miso-92 §7 records
   that post-CAMPD-envelope-correction replays do not reproduce a keeper's
   registered numbers, so this is a structural-agreement check, not an equality
   check: a mis-specified arm shows up here as a class moving far more than the
   envelope drift, and the B arm must not be trusted until A is read.
2. **The benchmark-invariance assertion.** Unlike the miso-98 sector A/B, this
   delta must NOT move the benchmark — ``_btm_frame`` is EIA-923 class totals x
   measured host shares and a heat rate does not enter it, so the miso-98 §5
   shared-``bench/`` trap cannot bite. That is ASSERTED here against the arms'
   own ``btm.parquet``, not assumed.
3. **The CHP class table** — model vs bench TWh per class-year in both arms.
   Only the MODEL side may move.
4. **The non-CHP control** — every other scored class; the delta reaches them
   only as an indirect merit/price response.
5. **Headline criteria** — the statuses each arm's own scorer wrote, with C3b
   called out: it is the kill guard (miso-98b passes at 0.198 vs a <=0.20 bound).

Usage::

    python scripts/probes/_miso99_chp_heat_rate_readout.py \
        results/calibration/miso99_chp_hr_A results/calibration/miso99_chp_hr_B
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

KEEPER = REPO / "results" / "calibration" / "miso98_chp_sector_B"
KEEPER_ID = "2026-07-27-miso-98b-sectormeasured"
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
    merged = arm_a.merge(keeper, on=["year", "class"], how="left").rename(
        columns={"class": "klass"}
    )
    print(f"=== 1. A-ARM CONTROL vs registered keeper {KEEPER_ID}")
    print("    (structural agreement, NOT equality — miso-92 §7 envelope drift)")
    print(
        f"    {'year':<6}{'class':<14}{'keeper TWh':>12}{'arm A TWh':>12}{'drift %':>10}"
    )
    for r in merged.sort_values(["year", "klass"]).itertuples(index=False):
        if r.keeper != r.keeper:  # nan — class absent from the keeper sidecar
            continue
        drift = _pct(r.model, r.keeper)
        mark = "  <-- CHECK" if abs(drift) > 5.0 else ""
        print(
            f"    {r.year:<6}{r.klass:<14}{r.keeper:12.3f}"
            f"{r.model:12.3f}{drift:10.2f}{mark}"
        )


def bench_invariance(arm_a: Path, arm_b: Path) -> None:
    """Assert the two arms carry an identical BTM hold-out frame."""
    print("\n=== 2. BENCHMARK INVARIANCE (the miso-98 §5 trap must not apply here)")
    pa, pb = arm_a / "btm.parquet", arm_b / "btm.parquet"
    if not (pa.exists() and pb.exists()):
        print("    btm.parquet missing in one arm — cannot assert")
        return
    a, b = pd.read_parquet(pa), pd.read_parquet(pb)
    same = a.shape == b.shape and a.reset_index(drop=True).equals(
        b.reset_index(drop=True)
    )
    print(
        f"    btm.parquet identical across arms: {same}  "
        f"(A {a.shape}, B {b.shape})"
        + ("" if same else "   <-- INVESTIGATE: the delta moved the benchmark")
    )


def class_block(title: str, a: pd.DataFrame, b: pd.DataFrame, classes) -> None:
    """Print the model/bench/%-error table for ``classes`` in both arms."""
    merged = (
        a.merge(b, on=["year", "class"], suffixes=("_a", "_b"), how="outer")
        .sort_values(["class", "year"])
        .rename(columns={"class": "klass"})
    )
    print(f"\n=== {title}")
    print(
        f"    {'class':<14}{'year':<6}"
        f"{'A model':>10}{'A bench':>10}{'A err%':>9}"
        f"{'B model':>10}{'B bench':>10}{'B err%':>9}{'|err| move':>12}"
    )
    for r in merged.itertuples(index=False):
        if r.klass not in classes:
            continue
        ea, eb = _pct(r.model_a, r.bench_a), _pct(r.model_b, r.bench_b)
        move = abs(eb) - abs(ea)
        verdict = "worse" if move > 0.5 else ("better" if move < -0.5 else "flat")
        print(
            f"    {r.klass:<14}{r.year:<6}"
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
    crit = m.get("criteria") or {}
    print(
        f"    {tag}: {m.get('determination')}  "
        + "  ".join(f"{k}={v.get('status')}" for k, v in crit.items())
    )
    for key in ("C3a", "C3b"):
        if key in crit:
            print(f"      {key}: {json.dumps(crit[key])[:400]}")


def main() -> int:
    """Print the full A/B readout for the two bundles."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arm_a", type=Path)
    ap.add_argument("arm_b", type=Path)
    args = ap.parse_args()

    a = class_table(args.arm_a.name)
    b = class_table(args.arm_b.name)

    control_check(a)
    bench_invariance(args.arm_a, args.arm_b)
    class_block("3. CHP CLASSES — the pre-registered lines", a, b, CHP_CLASSES)
    others = sorted(set(a["class"]) - set(CHP_CLASSES))
    class_block("4. NON-CHP CONTROL", a, b, others)

    print("\n=== 5. HEADLINE CRITERIA (each arm's own scorer; C3b is the kill guard)")
    criteria(args.arm_a, "arm A")
    criteria(args.arm_b, "arm B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
