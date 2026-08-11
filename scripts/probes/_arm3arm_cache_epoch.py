#!/usr/bin/env python
"""ARM-3-ARM — measure the MISO forecast lane's cache epoch across the Arm-3 arming.

Per-run probe / calibration record for owner card **D-29** (signed 2026-08-11,
sitting Addendum AK.8): arming ``miso_clean_tier_rows`` as the MISO forecast
default via ``ISOConfig.default_scenario_overrides``.

It computes cache keys off the LIVE config and solves nothing. Three reads:

* **The GLOBAL pin must not move.** ``ScenarioConfig().cache_key()`` is computed
  with ``iso="ERCOT"`` and no ISO override applied, and ``miso_clean_tier_rows``
  stays a registered ``_CACHE_KEY_OPTIONAL_FIELDS`` member at field-default
  ``False`` — so the pinned ``603c2498bf71d21d`` is unmoved by the arming. This
  is the CI verdict the lane waits on.
* **The MISO forecast lane's default key MOVES.** That move is the declared cache
  epoch: every MISO forecast bundle under the pre-arm key is superseded, and none
  is silently re-used (the armed value differs from the registered default and so
  enters the digest).
* **The two poles are the SIGNED pair's keys.** Pre-arm reproduces the ARM3-FIX
  control and post-arm reproduces its armed leg, byte-exactly — proof that the
  armed default resolves to the very scenario the signed evidence measured.

POSTURE NOTE (this is the reproduction trap): the ARM3-FIX pair ran
``--golden-posture`` with the **scalar** ``capacity_market_clearing`` left False;
the golden posture supplies the per-ISO ``capacity_market_clearing_by_iso`` seam
instead. The sidecars' ``capacity_market_clearing: true`` is MISO's *resolved*
per-ISO value, not the scalar. Passing ``cmc=True`` yields a different key.

Usage::

    uv run python scripts/probes/_arm3arm_cache_epoch.py
    uv run python scripts/probes/_arm3arm_cache_epoch.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_SRC), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from scripts.run_full_horizon import reference_config  # noqa: E402

# The pinned default-config cache key (tests/regression/test_persisted_identity).
PINNED_DEFAULT_KEY = "603c2498bf71d21d"
# The signed ARM3-FIX pair (docs/handoffs/arm3-fix-zone-mask-2026-08-09.md §4/§5).
ARM3FIX_CTRL_KEY = "cd2403cc031515db"
ARM3FIX_ARMED_KEY = "9337e00504e1e72a"
# That pair's window and posture.
WINDOW = (2031, 2035)


def measure() -> dict:
    """Return the three cache-epoch reads as a plain dict.

    Returns:
        Mapping with the global pin, both MISO forecast-lane poles, the signed
        pair's keys, and the boolean verdicts derived from them.
    """
    global_default = ScenarioConfig().cache_key()

    base = reference_config(
        iso="MISO",
        start_year=WINDOW[0],
        end_year=WINDOW[1],
        cmc=False,  # see the POSTURE NOTE in the module docstring
        golden_posture=True,
    )
    resolved = apply_iso_scenario_defaults(base, "MISO")
    pre = resolved.with_overrides(miso_clean_tier_rows=False).cache_key()
    post = resolved.with_overrides(miso_clean_tier_rows=True).cache_key()

    return {
        "window": list(WINDOW),
        "global_default_key": global_default,
        "global_default_key_pinned": PINNED_DEFAULT_KEY,
        "global_pin_unmoved": global_default == PINNED_DEFAULT_KEY,
        "field_default_miso_clean_tier_rows": bool(
            ScenarioConfig().miso_clean_tier_rows
        ),
        "resolved_miso_clean_tier_rows": bool(resolved.miso_clean_tier_rows),
        "resolved_miso_rps_compliance_regions": bool(
            resolved.miso_rps_compliance_regions
        ),
        "miso_forecast_key_pre_arm": pre,
        "miso_forecast_key_post_arm": post,
        "arm3fix_ctrl_key": ARM3FIX_CTRL_KEY,
        "arm3fix_armed_key": ARM3FIX_ARMED_KEY,
        "pre_arm_reproduces_signed_control": pre == ARM3FIX_CTRL_KEY,
        "post_arm_reproduces_signed_armed": post == ARM3FIX_ARMED_KEY,
        "epoch_moves": pre != post,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the reads, optionally persist them as JSON.

    Args:
        argv: Argument vector, defaulting to ``sys.argv[1:]``.

    Returns:
        0 when every verdict holds, 1 otherwise, so a shell can gate on it.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None, help="write the reads here")
    args = ap.parse_args(argv)

    reads = measure()
    text = json.dumps(reads, indent=2)
    print(text)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n")

    ok = (
        reads["global_pin_unmoved"]
        and reads["epoch_moves"]
        and reads["pre_arm_reproduces_signed_control"]
        and reads["post_arm_reproduces_signed_armed"]
    )
    if not ok:
        print("\nFAIL — a cache-epoch verdict did not hold.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
