"""NYISO-NEXT-6 leg acceptance + span composition (zero LP).

The arm is the incumbent keeper's recipe (``2026-09-26-nyisonext3-tranche-basis-span``)
plus ``nyiso_li_seam_posted_limit_cap``, solved year-isolated (rule 36). Checks, per
``docs/PRECOMMIT-nyiso-next5-li-tie-posted-limit-2026-09-27.md`` §6 and its §9 addendum:

* S0 -- every leg solved at the pin (``--pin``);
* S1 -- the keeper's flags plus ``nyiso_li_seam_posted_limit_cap`` true, and the
  keeper's offer-curve block (nothing re-tuned);
* S2 -- the keeper's CAMPD outage extract and thermal-tranche bytes (NEXT-3's);
* S5 -- the keeper's armed footprint lines, PLUS G-1: the clip's own log line
  carries exactly the addendum §9.2 hours and TWh for the leg's year.

Usage::

    python3 scripts/probes/nyisonext6_compose_span.py --pin <sha> --check-only \\
        --legs results/calibration/nyisonext6_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext6_compose_span.py --pin <sha> \\
        --legs results/calibration/nyisonext6_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext6_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import nyisonext3_compose_span as n3  # noqa: E402
from scripts.probes import nyisonext_compose_span as prev  # noqa: E402
from scripts.probes import rnyiso_compose_span as base  # noqa: E402

EXPECTED = prev.EXPECTED + (("nyiso_li_seam_posted_limit_cap", True),)

#: G-1 reference (PRECOMMIT §4; 2024 per the §9.2 addendum): (hours, TWh).
G1 = {
    2021: (860, "0.160"),
    2022: (1468, "0.343"),
    2023: (1688, "0.268"),
    2024: (969, "0.269"),
    2025: (1734, "0.308"),
}


def check_g1(legs: list[Path]) -> None:
    """G-1: each leg's log carries the clip line with the pre-registered footprint."""
    bad = []
    for leg in legs:
        rc = json.loads((leg / "run_config.json").read_text())
        years = [int(y) for y in (rc.get("years") or [])] or [
            int(leg.name.rsplit("_", 1)[-1])
        ]
        text = (leg / "solve.log").read_text(errors="replace")
        for y in years:
            h, twh = G1[y]
            line = (
                f"nyiso_li_seam_posted_limit_cap {y}: Long_Island import cap falls "
                f"in {h} hours, {twh} TWh removed"
            )
            ok = line in text
            print(f"  {leg.name}: G-1 {y} {'OK' if ok else 'MISSING: ' + line}")
            if not ok:
                bad.append(f"{leg.name}:{y}")
    if bad:
        raise SystemExit(f"legs {bad} fail G-1; refusing to compose")


def check_g1_zero_lp(legs: list[Path]) -> None:
    """G-1 on each leg's OWN recorded config, zero LP (used when a leg has no solve.log).

    Rebuilds the NYISO topology under the leg's ``scenario_config``, applies the
    PAR-attributed envelope and the clip, and requires the §9.2 footprint with no
    other link moving. The shard's own hard stop already gated its push on the log line.
    """
    import dataclasses

    import numpy as np

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.nyiso_par_attribution import nyiso_par_attributed_ttc_hourly
    from market_sim.data.nyiso_seam_envelope import nyiso_li_posted_limit_cap
    from market_sim.model.interchange import spec as sp

    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    bad = []
    for leg in legs:
        rc = json.loads((leg / "run_config.json").read_text())
        sc = rc["scenario_config"]
        cfg = ScenarioConfig().with_overrides(
            **{
                k: v
                for k, v in sc.items()
                if k in names and k != "reliability_floor_overrides"
            }
        )
        y = int(leg.name.rsplit("_", 1)[-1])
        ic = sp.apply_interchange_topology(
            get_iso_config("NYISO"), sp.get_interchange_spec(cfg, "NYISO", y), cfg, year=y
        )
        static = np.array([ln.ttc_mw for ln in ic.links], dtype=float)
        fwd, _ = nyiso_par_attributed_ttc_hourly(static, ic, y, 8760)
        arm = nyiso_li_posted_limit_cap(fwd, ic, y, 8760)
        i = [(ln.from_zone, ln.to_zone) for ln in ic.links].index(
            ("NYISO_external", "Long_Island")
        )
        cut = fwd[:, i] - arm[:, i]
        other = float(np.abs(np.delete(arm - fwd, i, axis=1)).max())
        got = (int((cut > 0).sum()), f"{cut.sum() / 1e6:.3f}")
        ok = got == G1[y] and other == 0.0 and not (cut < 0).any()
        print(f"  {leg.name}: G-1 zero-LP {got} other={other} {'OK' if ok else 'FAIL'}")
        if not ok:
            bad.append(leg.name)
    if bad:
        raise SystemExit(f"legs {bad} fail G-1; refusing to compose")


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", required=True, help="the arm commit SHA (40 hex)")
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument(
        "--no-log",
        action="store_true",
        help="legs carry no solve.log: verify G-1 at zero LP from each leg's config",
    )
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    base.PIN = args.pin
    base.EXPECTED = EXPECTED
    base.INPUT_SHA = n3.INPUT_SHA
    base.KEEPER = _REPO / "results" / "calibration" / "nyisonext3_span"
    base.check_legs(legs)
    if args.no_log:
        check_g1_zero_lp(legs)
    else:
        prev.check_footprint(legs)
        check_g1(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
