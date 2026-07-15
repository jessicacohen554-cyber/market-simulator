"""miso-67 probe: ST_GAS p25-LEVEL commitment floor (the VLR level swap).

Replays the MISO keeper (``miso66_coalconduct``) meta.json STRICTLY via
``replay_keeper.build_kwargs`` (the sanctioned single-source recipe
reconstruction — no lossy channel; miso-50..53 regression closure) and applies
ONE single-delta override through the generic ``prb_overrides`` channel:

    main : st_gas_mustrun_p25_level = True   (the level swap under test)
    base : (nothing added)                   same-box unchanged-recipe replica

The base is the DRIFT CONTROL: the mechanism-only footprint is probe - base
(both solved in THIS box / code state), never probe - the registered miso-66
bundle (the miso-66 drift lesson — a raw probe-vs-registered comparison once
mis-read solver-box drift as mechanism). No zero-forcing ablation twin
(rule 20 as amended 2026-07-14).

PER-YEAR + REUSE (RAM <=16 GB, design doc §8): each invocation solves exactly
ONE new LP. Pass the accumulating year list, the destination dir, and the prior
step's dir as ``--reuse-solved``; the years already present are byte-copied and
only the newest year is solved. Sequence (per variant):

    python scripts/probes/_miso67_stgas_vlr_level.py <main|base> \\
        --out-dir <acc>/y2023 --years 2023
    python scripts/probes/_miso67_stgas_vlr_level.py <main|base> \\
        --out-dir <acc>/y2024 --years 2023,2024 --reuse-solved <acc>/y2023
    python scripts/probes/_miso67_stgas_vlr_level.py <main|base> \\
        --out-dir <acc>/final --years 2023,2024,2025 --reuse-solved <acc>/y2024

The final 3-year bundle is ``<acc>/final`` (rule 16 — one bundle, all years).
Years ALWAYS sequential within a run (rule 12).

Rule 22: MISO has no calibration-complete marker -> 2023/2024/2025 ONLY.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Reproducibility pin (mirrors replay_keeper.py): force cross-year LP warm-start
# OFF so per-year processes are basis-independent and the main/base pair is a
# clean same-box comparison. Set BEFORE importing the solve core.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso66_coalconduct"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["main", "base"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--years", required=True, help="comma-separated, e.g. 2023,2024")
    ap.add_argument("--reuse-solved", default=None)
    args = ap.parse_args()

    years = [int(y) for y in args.years.split(",")]
    for y in years:
        if y not in (2023, 2024, 2025):
            raise SystemExit(f"rule 22: MISO year {y} is out of the 2023-2025 window")

    meta = json.loads((KEEPER / "meta.json").read_text())
    if meta.get("iso") != "MISO":
        raise SystemExit(f"wrong base bundle iso={meta.get('iso')!r} (expected MISO)")

    kwargs = build_kwargs(meta)
    # Sanity: the base recipe MUST already arm the ST_GAS floor whose LEVEL we
    # swap — it rides the prb_overrides channel (coal_prb_sigmoid_overrides).
    prb = kwargs.setdefault("prb_overrides", {})
    if not prb.get("st_gas_mustrun_per_plant"):
        raise SystemExit(
            "miso-66 meta missing st_gas_mustrun_per_plant in prb_overrides — "
            "wrong base (the level swap needs the floor it swaps)"
        )

    if args.mode == "main":
        # The single delta under test: swap the ST_GAS floor level to p25.
        prb["st_gas_mustrun_p25_level"] = True

    note = (
        f"miso-67 ({args.mode}) -- ST_GAS p25-LEVEL commitment floor: the "
        "miso-66 keeper recipe with the st_gas_mustrun_per_plant floor LEVEL "
        "swapped from the committed tranche (P5-of-online = LSL) to the "
        "plant's measured p25-of-online available-CF x nameplate "
        "(thermal_tranches_MISO.csv p25_cf; same frozen estimator, same "
        "window, same mechanism id -- rule 19 level replace). The measured "
        "25th-percentile dispatch level of the Entergy MISO-South VLR steam "
        "fleet (Sabine 32.9%, Harding Street 36.7%, Nine Mile 49.4%), which "
        "ran 30-67% CF despite local LMP at/below SRMC (out-of-market VLR -- "
        "Amite South / DSG / WOTAB, MISO SOM). Zero fitted scalars. "
        "base = unchanged-recipe same-box drift control (mechanism-only = "
        "main - base). No ablation twin (rule 20 amended 2026-07-14). "
        "Design: docs/handoffs/miso-run66-triage-design-2026-07.md Issue-2."
    )

    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["reuse_solved"] = Path(args.reuse_solved) if args.reuse_solved else None
    kwargs["note"] = note

    print(
        f"miso-67 {args.mode}: years={years} out={args.out_dir} "
        f"reuse={args.reuse_solved} p25={'ON' if args.mode == 'main' else 'off'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
