"""Driver: MISO 47 — ST_GAS overnight + CT_PEAKER evening reliability drag keeper candidate.

The miso-46-seam-ladder keeper recipe (bundle
``results/calibration/MISO/miso_46_seam_ladder``), re-solved on the current data
tree so it absorbs the structural corrections landed on this branch — all of
which live in base config / base data, so the *recipe* (the exact
``solve_and_persist`` kwargs recorded in the keeper's ``meta.json``, replayed
verbatim via :func:`scripts.replay_keeper.build_kwargs`) is byte-unchanged and
every delta vs miso-46 is one of these mechanisms:

1. **ST_GAS extreme-day OVERNIGHT drag** (headline). Within the
   ``reliability_floor`` engine (already ``reliability_floor=True`` in the miso-46
   recipe), MISO ST_GAS carries overnight-windowed [0,6] tmax/tmin/netload limbs
   at its physical min-stable level (0.12): on an extreme-temperature or
   high-net-load day the gas-steam boiler is held warm at Pmin overnight to ramp
   for the next peak instead of cycling off. 4 limbs enabled where the overnight
   pre-positioning is real in the CAMPD data (Indiana tmax+netload, Plains tmax,
   West netload); the rest ship disabled and visible (rule 12). Forced overnight
   energy 0.3-0.4% of class energy (rule 20).
2. **CT_PEAKER evening net-load drag**. The simple-cycle peakers carry
   evening-windowed [15,21] netload limbs (the afternoon-evening duck-neck ramp,
   the CAISO precedent) — enabled in all 6 zones (Spearman rho 0.49-0.71). This
   replaces the miso-46 temperature-only CT limbs (rule 14: one mechanism, the
   netload driver unifies the hot/cold/stress commitment far better than
   temperature). Forced evening energy ~18-20% of CT energy — above the 15%
   peaker budget, so it rides the rule-20 v2.2 grounded-above-budget path
   (D-4 window [15,21] ⊂ the (MECH_RELIABILITY_FLOOR, CT_PEAKER) [14,22)
   justified window; D-1 diurnal shape scored in the bundle).
3. **CHP steam-credit power-only HR correction extended to MISO**: CC_CHP/CT_CHP
   no longer clear on physically-impossible steam-credited HRs (cap-weighted
   CT_CHP ~6.62 / CC_CHP ~6.76, median CT_CHP 5.50, min CC_CHP 4.49 MMBtu/MWh) —
   universal turbine physics (rule 24 clean), the same correction landed for
   CAISO/PJM.

All three limbs live in the ``reliability_floor`` engine + base fleet config; the
separate ``gas_st_netload_drag`` / ``ct_netload_drag`` mechanisms stay OFF (rule
14/19: one mechanism per phenomenon).

Memory note (CLAUDE.md rule 1/12): the MISO per-plant multi-zone energy+reserve
co-opt LP peaks ~14-16 GB per year; run this SOLO (never concurrent with another
per-plant solve) with ``MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=2`` so glibc returns
freed heap between years — this is what lets all three years fit in ONE process
on a 15 GB host. Years solve SEQUENTIALLY inside ``solve_and_persist`` (never
parallelized). Holdout (rule 22): 2023-2025 only — MISO has no
calibration-complete marker, so 2022/2019/H1-2026 are quarantined.

Usage:
    MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=2 \\
      python scripts/run_miso47_steamgas_ct_drag.py
    python scripts/run_miso47_steamgas_ct_drag.py --report-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

import run_calibration_full as rcf  # noqa: E402
from scripts.replay_keeper import build_kwargs  # noqa: E402
from scripts.run_calibration_full import report_run  # noqa: E402

_KEEPER_BUNDLE = _REPO / "results/calibration/MISO/miso_46_seam_ladder"
_OUT_DIR = _REPO / "results/calibration/MISO/miso_47_steamgas_ct_drag"

NOTE = (
    "MISO 47 steam-gas overnight + CT evening drag keeper candidate: miso-46 "
    "seam-ladder recipe re-solved at HEAD, absorbing three base-config/base-data "
    "structural corrections vs miso-46 — (1) ST_GAS extreme-day overnight [0,6] "
    "drag in the reliability_floor engine (tmax/tmin/netload, min-stable 0.12, 4 "
    "limbs enabled where the CAMPD overnight pre-positioning is real, forced "
    "0.3-0.4%), (2) CT_PEAKER evening [15,21] netload drag replacing the "
    "temperature-only CT limbs (6 zones, rho 0.49-0.71, forced ~18-20% — rule-20 "
    "v2.2 grounded-above-budget, D-4 [15,21]⊂[14,22)), (3) CHP steam-credit "
    "power-only HR correction extended to MISO (CT_CHP ~6.62 / CC_CHP ~6.76 "
    "sub-physical). Recipe byte-unchanged vs miso-46; every delta is one of these "
    "three structural mechanisms in base config/data."
)


def _solve(out_dir: Path, ablation: bool = False) -> Path:
    """Replay the miso-46 keeper recipe verbatim into ``out_dir`` (all 3 years).

    With ``ablation=True`` the D-3 zero-forcing twin is solved instead: every
    merchant floor/bridge/drag (incl. the new ST_GAS/CT reliability limbs) is
    neutralized via ``ScenarioConfig.as_zero_forcing_ablation`` inside
    ``run_year`` while the structural protected set (nuclear must-run, CHP steam,
    coal take-or-pay) stays — the keeper config is otherwise byte-identical
    (CLAUDE.md rule 20 / audit D-3).
    """
    meta = json.loads((_KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out_dir
    kwargs["note"] = NOTE + (" [ZERO-FORCING ABLATION TWIN]" if ablation else "")
    if ablation:
        kwargs["zero_forcing_ablation"] = True
    print(
        f"replaying {_KEEPER_BUNDLE.name} recipe -> {out_dir} "
        f"(years {kwargs['years']}, ablation={ablation})"
    )
    return rcf.solve_and_persist(**kwargs)


def main() -> int:
    """CLI: solve all three years into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument(
        "--ablation",
        action="store_true",
        help="Solve the zero-forcing ablation twin (out-dir defaults to "
        "<bundle>-ablation).",
    )
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Skip solving; just score the existing bundle over all years.",
    )
    args = ap.parse_args()

    out_dir = args.out_dir or (
        Path(str(_OUT_DIR) + "-ablation") if args.ablation else _OUT_DIR
    )
    if not args.report_only:
        _solve(out_dir, ablation=args.ablation)
    report_run(out_dir, band_width=0.10)
    print(f"DONE: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
