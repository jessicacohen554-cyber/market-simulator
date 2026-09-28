"""NYISO-NEXT-9 G-1 leg acceptance + span composition (zero LP).

The arm is the NEXT-8 keeper's recipe replayed at the pin with ONE delta,
``nyiso_firm_imports: false`` (``docs/PRECOMMIT-nyiso-next9-hq-floor-2026-09-28.md``
sec. 6). Per leg:

* S0 -- solved at the pin (``git.basis_sha``);
* S1 -- ``scenario_config`` equals the keeper bundle's except exactly
  ``nyiso_firm_imports`` True -> False (keys ``replay_keeper`` translates for
  the control too -- ``retiree_cems_cap`` -- are ignored); offer-curve block equal;
* S2 -- ``resolved_inputs`` byte-identical to the keeper bundle's;
* S3 -- no D-2 ``firm_import`` row in the leg's ``legitimacy_diagnostics.json``.

Usage::

    python3 scripts/probes/nyisonext9_compose_span.py --check-only \\
        --legs results/calibration/nyisonext9_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext9_compose_span.py \\
        --legs results/calibration/nyisonext9_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext9_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.nyiso238_compose_span import compose as _compose  # noqa: E402
from scripts.probes.rnyiso_compose_span import _offer_block  # noqa: E402

PIN = "7900ac511f710940bc039aa4de354646d4e10f26"
CAL = _REPO / "results" / "calibration"
DELTA = {"nyiso_firm_imports": (True, False)}
#: keys the replay path translates identically for control and arm (rule 26 deletions)
IGNORED = {"retiree_cems_cap"}


def _keeper(year: int) -> Path:
    """The keeper bundle carrying ``year``."""
    return CAL / ("nyisonext8_2021" if year == 2021 else "nyisonext8_span")


def check_legs(legs: list[Path]) -> None:
    """Fail loud if any leg misses S0-S3."""
    bad: list[str] = []
    for leg in legs:
        y = int(leg.name.rsplit("_", 1)[-1])
        rc = json.loads((leg / "run_config.json").read_text())
        kc = json.loads((_keeper(y) / "run_config.json").read_text())
        errs: list[str] = []
        basis = (rc.get("git") or {}).get("basis_sha") or ""
        if basis != PIN:
            errs.append(f"S0 basis_sha {basis!r}")
        sa, sk = rc["scenario_config"], kc["scenario_config"]
        diff = {
            k: (sk.get(k), sa.get(k))
            for k in set(sa) | set(sk)
            if k not in IGNORED and sa.get(k) != sk.get(k)
        }
        if diff != DELTA:
            errs.append(f"S1 scenario_config delta {diff}")
        if _offer_block(rc) != _offer_block(kc):
            errs.append("S1 offer-curve block differs from the keeper")
        if rc.get("resolved_inputs") != kc.get("resolved_inputs"):
            errs.append("S2 resolved_inputs differ from the keeper")
        ld = json.loads((leg / "legitimacy_diagnostics.json").read_text())
        rows = ld["diagnostics"]["D2"]["rows"]
        if any(r.get("mechanism") == "firm_import" for r in rows):
            errs.append("S3 D-2 firm_import row present")
        print(f"  {leg.name}: {'OK' if not errs else errs}")
        if errs:
            bad.append(leg.name)
    if bad:
        raise SystemExit(f"legs {bad} fail G-1; refusing to compose")


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    check_legs(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
