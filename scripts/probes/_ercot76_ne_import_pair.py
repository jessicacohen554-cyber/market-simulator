"""ERCOT-76 NE-boundary asymmetric import rating — full-span bundle.

Byte-faithful reconstruction of the promoted ERCOT keeper
(2026-07-16-ercot73-state-wall) from its bundle meta.json, solved on the
ERCOT-76 topology correction (config/iso_configs.py): the Northeast<->North
boundary becomes a one-way pair — export keeps the measured NE_LOB stability
limit (1,300 MW); import carries the boundary's measured dark-hour carrying
capability (1,788 MW, pooled 2023-2025 maximum of EAST-zone load minus CAMPD
NE-plant net gross). ZERO ScenarioConfig deltas: the mechanism is topology
structure, like the NE_LOB carve-out itself.

The measured refutation of the old symmetric bound (ERCOT-76 leg 0): on
2024-05-07 h19/20 the keeper printed Northeast VOLL with 43/4.4 MW shed
against the 1,300 MW import wall while reality imported >= 1,317 MW into the
lobe and printed $37/$15.

FULL-SPAN 2023-2025 bundle (rule 16) intended for the backcast dashboard
(rule 15). Keeper promotion is the OWNER's, never this script's.

Usage::

    uv run python scripts/probes/_ercot76_ne_import_pair.py \
        --years 2023 2024 2025 --out-name ercot76_ne_import_fullspan
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from replay_keeper import build_kwargs  # noqa: E402
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot73_state_wall_fullspan"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-name", default="ercot76_ne_import_fullspan")
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["note"] = (
        "ERCOT-76 NE-boundary asymmetric import rating on the ercot73-state-"
        "wall keeper recipe (zero ScenarioConfig deltas — the change is the "
        "iso_configs one-way link pair: NE_LOB export 1,300 MW measured "
        "limit-at-bind unchanged; import 1,788 MW = pooled 2023-2025 "
        "dark-hour maximum of measured EAST-zone load minus CAMPD NE local "
        "gross, the boundary's demonstrated carrying capability). Kills the "
        "2024-05-07 h19/20 invented Northeast VOLL pair for the measured "
        "reason (reality imported >= 1,317 MW that evening; a GTC is an "
        "export stability limit, never an import rating). Zero fitted "
        "scalars (rules 13/14/23/26). Full-span 2023-2025 (rule 16)."
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = _load_reference()
    kwargs["run_dir"] = out
    solve_and_persist(**kwargs)
    print(f"DONE -> {out} (years: {args.years})")


if __name__ == "__main__":
    main()
