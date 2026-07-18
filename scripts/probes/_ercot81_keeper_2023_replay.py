"""ERCOT-81 leg 0: single-year 2023 replay of the ercot80 keeper (A-leg baseline).

Reconstructs the promoted keeper's exact recipe from its committed meta.json
(`results/calibration/ercot80_unit_only_outages_fullspan`) via the STRICT
`replay_keeper.build_kwargs` channel and solves 2023 only, into a throwaway
probe bundle. Rule-16 single-year diagnostic — never registered, never a keeper.

Purpose (this lane's leg 0): the August-2023 under-formation anatomy needs the
model's hourly price / room / cleared-reserve series, which the committed slim
bundle does not carry. The 2023 replay is also the same-machine A-leg for any
subsequent single-delta B probe.

Usage::

    uv run python scripts/probes/_ercot81_keeper_2023_replay.py \
        [--out-dir results/calibration/_ercot81_keeper_2023] [--set KEY=JSON ...]
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Basis-independence pin, mirroring replay_keeper.py (set BEFORE importing the
# solve core so pipeline.solve reads the pinned value).
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "ercot80_unit_only_outages_fullspan"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out-dir",
        default=str(REPO / "results" / "calibration" / "_ercot81_keeper_2023"),
    )
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=JSON",
        help="ScenarioConfig override via the prb_overrides channel "
        "(single-delta B probe), e.g. --set ercot_rrs_conservative_withholding=true",
    )
    ap.add_argument("--years", nargs="+", type=int, default=[2023])
    ap.add_argument(
        "--kwarg-true",
        dest="kwarg_true",
        action="append",
        default=[],
        metavar="KWARG",
        help="set a solve_and_persist boolean kwarg to True directly (the real "
        "kwarg channel, recorded top-level in meta.json — NOT prb_overrides), "
        "e.g. --kwarg-true ercot_nonreleasable_as_withholding",
    )
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    for spec in args.overrides:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"][key] = json.loads(raw)
    for key in args.kwarg_true:
        kwargs[key] = True
    if args.kwarg_true and len(args.years) > 1:
        deltas = ", ".join(args.kwarg_true)
        kwargs["note"] = (
            f"ercot81 nonreleasable-AS: the ercot80 keeper recipe + {deltas} — "
            "the published pre-RTC+B RRS/Reg-Up HASL carve-out (no price-based "
            "SCED release until RTC+B go-live 2025-12-05; the 2024-08-01 "
            "release reform was ECRS-only) priced as rigid at-cap reserve "
            "demand, so tight-hour energy duals climb the offer surface "
            "instead of shedding withheld reserve down an RTC+B-era ramp the "
            "2023-2025 market did not have. Zero fitted parameters; published "
            "design dates only."
        )
    else:
        kwargs["note"] = (
            "ERCOT-81 rule-16 single-year throwaway probe: keeper recipe replay "
            f"(years {kwargs['years']}, overrides {args.overrides or 'none'}) "
            "for the Aug-2023 under-formation anatomy. NEVER registered."
        )
    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
