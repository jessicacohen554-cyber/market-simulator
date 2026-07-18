"""Driver: PJM 95 — pjm-94 ST_GAS net-load drag + temperature-dependent derate.

The pjm-94 recipe (pjm-90 verbatim + all-hours ST_GAS net-load reliability drag,
#1483/G-21) with ``temp_dependent_derate=True`` added — the one lever pjm-94
does not carry that targets its single remaining load-bearing FAIL (C3c price
tail: 2025 model 0h vs actual 51h > $200).

``temp_dependent_derate`` is a physically-derived per-class dry-bulb temperature
capacity curve (arXiv:2311.07001, CPUC R.21-10-002): it REPLACES the flat
EIA-860 net-summer derate for CC/CT with a capacity-neutral reshape (heatwave
hours below net-summer, cooler hours toward full rating) and adds a pure
additive hot-hour derate for COAL/ST_GAS — coefficients in
ScenarioConfig.temp_derate_slope_*, forward-reproducible (rule 11). On the
pjm-90 recipe it improved the 2025 C3c DA-expressible scarcity tail 0h -> 19h
(vs 51h actual; pjm-93). This run pairs it with the pjm-94 ST_GAS drag to test
whether the two compose (drag closes the ST_GAS/CC_REGULAR volume gap; temp
derate tightens the summer-peak capacity so scarcity prices form).

Everything else is the pjm-94 recipe VERBATIM. Full span 2023-2025 one bundle
(rule 16), years sequential (rule 1/12). MEMORY: run with MALLOC_ARENA_MAX=2
(one process, ~12.7 GB peak; without it the 2nd year OOMs on a 15 GB host) —
run ONE year per process into the SAME --out-dir, then --report-only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.archive.run_pjm94_stgas_netload_drag import _solve  # noqa: E402

NOTE = (
    "PJM 95 ST_GAS net-load drag (pjm-94) + temperature-dependent derate: the "
    "pjm-94 recipe verbatim with temp_dependent_derate=True added to target the "
    "one remaining load-bearing FAIL (C3c price tail, 2025 0h vs 51h >$200). "
    "temp_dependent_derate is a physically-derived per-class dry-bulb capacity "
    "curve (arXiv:2311.07001, CPUC R.21-10-002; capacity-neutral CC/CT reshape + "
    "additive hot-hour COAL/ST_GAS derate) that improved the 2025 C3c tail "
    "0h->19h on the pjm-90 recipe (pjm-93). Tests whether the ST_GAS drag and "
    "the temp derate compose. Otherwise pjm-94 verbatim."
)


def main() -> int:
    """CLI: solve ``--years`` into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/calibration/pjm95_stgas_drag_tempderate"),
    )
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        _solve(args.years, args.out_dir, temp_dependent_derate=True, note=NOTE)
    report_run(args.out_dir, band_width=0.10)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
