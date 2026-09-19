"""SPP-48 (ZERO LP): why the BENCHMARK drops a mid-window retiree, and why the
fleet repair does NOT fix it.

SPP-47 §2.2 predicted that once the LP fleet carries Oklaunion (plant 127), the
benchmark question becomes moot "because the plant is then in the fleet map the
builder keys on". **That prediction is FALSE as implemented**, and this probe is
the measurement that refutes it.

Measured 2026-09-19 by rebuilding the benchmark on two copies of the committed
2019-2022 rung bundle whose metas differ ONLY in ``mid_vintage_exit_carry``:
both legs wrote the SAME content-addressed EIA-923 frame
(``eia923-78357736757d.parquet``), so the benchmark is **invariant** to the
fleet repair. Against the committed frame (``eia923-cda580e2f71c.parquet``):

    plant 127, 2020 | COMMITTED 1,209,201 MWh (m05-m09 86,240 / 219,325 /
                    | 289,823 / 329,299 / 284,514 -- the CAMPD shape)
                    | HEAD REBUILD: 0 rows
    2020 COAL_PRB   | COMMITTED 67.0581 TWh -> HEAD REBUILD 65.8489 TWh

THE ROOT CAUSE, and it is a DIFFERENT defect from the fleet gap: the benchmark's
ISO membership is ``run_calibration_full._iso_plant_ids`` ->
``zone_assignment.build_zone_lookup``, whose plant set comes from **eGRID 2023
coordinates**, supplemented for the ``_EIA860_SUPPLEMENT_ISOS`` (SPP included)
from the **canonical** EIA-860 plant file -- the 2025 Early Release. NEITHER
source knows a plant that retired in 2020, and the lookup does **not** follow
``eia860_vintage_tracks_solve_year``: this probe measures the SPP plant set at
830 with 127 ABSENT under every vintage (canonical, 2019, 2020, 2022, 2023),
each in its own interpreter. The supplement is forward-only by its own
docstring -- it "covers plants too new for the eGRID vintage".

WHY IT MATTERS, stated as an asymmetry rather than a magnitude: the LP fleet has
a fallback-zone path for a plant eGRID lacks (the loader logs "N of M SPP
generators not in eGRID lookup - assigned fallback zone"), while the benchmark
applies a hard ``isin`` filter with no fallback. So a mid-window retiree can be
IN the model and OUT of the actual at the same time -- which is worse than being
missing from both, because it makes C1 read a miss that is partly an artifact of
two different membership rules.

CONSEQUENCE FOR SCORING THE SPP-48 ARM, pre-declared: the arm bundle carries a
FRESHLY REBUILT benchmark (no plant 127 -> 2020 COAL_PRB actual 65.8489), while
the committed control carries the older one (with plant 127 -> 67.0581). Scoring
the arm against its own benchmark would move C1-2020 by BOTH the model-side
repair AND a 1.2092 TWh deletion from the actual -- and the second half is
"rescaling an input so the model's output lands on the actuals" (rule 13
[R-MEASURED]) and "burying the error back inside an inaccurate input" (rule 14
[R-ACCURATE]). **The arm must therefore be scored against the COMMITTED
benchmark**, and the benchmark regression reported as its own object.

Run: PYTHONPATH=src python3 scripts/probes/_spp48_benchmark_membership.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OKLAUNION = 127


def membership_leg(vintage: str) -> dict:
    """SPP's benchmark plant set under one EIA-860 vintage, in THIS process.

    Forked one-per-vintage by :func:`main` because ``build_zone_lookup`` and the
    EIA-860 directory resolver both carry process-level caches.
    """
    from market_sim.config.paths import active_eia860_dir, set_eia860_vintage

    set_eia860_vintage(None if vintage == "none" else int(vintage))
    from market_sim.data.zone_assignment import build_zone_lookup

    z = build_zone_lookup("SPP")
    return {
        "vintage": vintage,
        "active_dir": active_eia860_dir().name,
        "n_plants": len(z),
        "oklaunion_present": OKLAUNION in z,
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--leg":
        print("<<<JSON>>>" + json.dumps(membership_leg(sys.argv[2])))
        return

    rows = []
    for v in ("none", "2019", "2020", "2021", "2022", "2023"):
        r = subprocess.run(
            [sys.executable, __file__, "--leg", v],
            capture_output=True, text=True, cwd=str(REPO),
        )
        if "<<<JSON>>>" not in r.stdout:
            raise SystemExit(f"leg {v} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        rows.append(json.loads(r.stdout.split("<<<JSON>>>", 1)[1]))

    print("SPP benchmark plant membership (run_calibration_full._iso_plant_ids)")
    print(f"{'vintage':>8} {'active dir':>16} {'n_plants':>9} {'plant 127?':>11}")
    for r in rows:
        print(f"{r['vintage']:>8} {r['active_dir']:>16} {r['n_plants']:>9} "
              f"{str(r['oklaunion_present']):>11}")

    invariant = len({r["n_plants"] for r in rows}) == 1
    never = not any(r["oklaunion_present"] for r in rows)
    print()
    print(f"membership INVARIANT across vintages: {invariant}")
    print(f"plant 127 absent from EVERY vintage:  {never}")
    print()
    print("=> The benchmark's ISO membership does NOT follow")
    print("   eia860_vintage_tracks_solve_year, so a plant that retired before the")
    print("   eGRID-2023 / EIA-860-2025ER sources is structurally absent from the")
    print("   ACTUAL even in the years it demonstrably ran. This is a DIFFERENT")
    print("   defect from the fleet gap and mid_vintage_exit_carry does not fix it.")

    out = REPO / "results/calibration/_spp48_benchmark_membership.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"rows": rows, "membership_invariant": invariant, "oklaunion_never_present": never},
        indent=1,
    ))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
