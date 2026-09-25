"""R-SOCO-B: layer the SOCO boundary repairs onto ``calibration_attestation.json``.

Runs LAST, after ``build_dof_ledger.py``, ``gen_soco60b_attestation.py`` and
``gen_rsoco_attestation.py`` have written and re-verified the inherited claims on
the composed 2019-2025 bundle. This module then verifies the lane's own delta against
the keeper ``2026-09-24-r-soco-corrected-inputs``
(``docs/handoffs/r-soco/PRECOMMIT-r-soco-b-2026-09-25.md``), by execution:

* the three registries hold exactly the measured values — R1
  ``EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC``, R2
  ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` (now also reaching the LP fleet), R3
  ``ISO_BA_JOINS``;
* the bundle's ``solve_surface.moved`` carries both new rows at their LIVE hashes, and
  every leg was solved at the PRECOMMIT's pinned SHA;
* R1 is live in the solved 2019 year: the composite's 2019 demand-with-interchange
  equals the phase-0 census value;
* no offer-curve override / delta, every band 1.0 (no price tuning; SOCO has no
  price reference).

It adds three ledger entries (categorical registry repairs onto published records,
``n_scalars`` 0) and replaces the inherited 2023-2025-only scope disclosure.

Usage::

    python3 scripts/gen_rsocob_attestation.py --bundle results/calibration/<bundle> \\
        --pinned-sha <40-char sha>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.probes.rsocob_compose_span import (  # noqa: E402
    DEMAND_2019_TWH,
    NEW_SURFACE_ROWS,
)

WINDOWS = {"SOCO": (("2019-01-01 07:00", "2019-09-11 05:00"),)}
JOINS = {"SOCO": {"AEC": (2021, 9)}}

#: The lane's ledger entries: each a categorical registry repair onto a published
#: record, zero scalars (rules 21/24).
NEW_ENTRIES = {
    "EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC": (
        "R1. EIA's published SOCO Total interchange is the exact negative of NG - D in "
        "every hour UTC 2019-01-01 07:00..2019-09-11 05:00 (6,071 h; the nine-DIBA book "
        "corroborates at corr -1.0000); negated at the frame seam. Owner ruling (A)."
    ),
    "ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE (LP fleet)": (
        "R2. The SOCO-60 membership partition (plants the current EIA-860 codes to "
        "another BA) now also reaches the vintage LP fleet: the former Gulf Power "
        "plants, 1,826.6 MW in 2019-2020, 2,760.8 MW in 2021, 2,524.9 MW in 2022-2023."
    ),
    "ISO_BA_JOINS": (
        "R3. PowerSouth (AEC) joined the SOCO BA on 2021-09-01 (its interchange leg "
        "stops; EIA-860 and EIA-923 book it AEC through 2021, SOCO from 2022). Fleet "
        "admitted from September 2021; benchmark excludes it before. Owner ruling (B)."
    ),
}


def verify(bundle: Path, pinned_sha: str) -> dict:
    """Raise unless the bundle carries exactly the lane's repairs; return evidence."""
    import market_sim.config.constants as K
    from market_sim.config.solve_surface import surface_rows

    if K.EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC != WINDOWS:
        raise SystemExit("EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC drifted")
    if K.ISO_BA_JOINS != JOINS:
        raise SystemExit("ISO_BA_JOINS drifted")
    if K.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE != {"SOCO": True}:
        raise SystemExit("ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE drifted")
    cfg = json.loads((bundle / "run_config.json").read_text())
    moved = (cfg.get("solve_surface") or {}).get("moved") or {}
    live = surface_rows("SOCO")
    for name in NEW_SURFACE_ROWS:
        if moved.get(name) != live.get(name):
            raise SystemExit(
                f"{name}: bundle moved hash {moved.get(name)!r} != live {live.get(name)!r}"
            )
    legs = cfg.get("per_leg_provenance") or {}
    bad = {
        y: (p.get("git") or {}).get("basis_sha")
        for y, p in legs.items()
        if (p.get("git") or {}).get("basis_sha") != pinned_sha
    }
    if not legs or bad:
        raise SystemExit(
            f"legs not solved at the pinned SHA {pinned_sha}: {bad or legs}"
        )
    flags = cfg.get("calibration_flags") or {}
    for k in ("offer_curve_overrides", "offer_curve_deltas"):
        if flags.get(k) not in (None, {}):
            raise SystemExit(f"{k} is not empty: {flags.get(k)}")
    sysf = pd.read_parquet(bundle / "hourly" / "system_2019.parquet")
    dem = float(sysf.loc[sysf["pass"] == "P1", "demand"].sum()) / 1e6
    if abs(dem - DEMAND_2019_TWH) > 0.01:
        raise SystemExit(f"2019 demand-with-interchange {dem:.4f} != {DEMAND_2019_TWH}")
    return {
        "moved_rows": {n: moved[n] for n in NEW_SURFACE_ROWS},
        "legs_at_pinned_sha": sorted(legs),
        "demand_2019_twh": round(dem, 4),
    }


def main() -> None:
    """Verify the repairs, then extend the governance text and ledger entries."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--pinned-sha", required=True)
    a = ap.parse_args()
    bundle = Path(a.bundle)
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text())
    if "free_parameters" not in att or "R-SOCO (lane" not in (
        att.get("governance", {}).get("attested_by", "")
    ):
        raise SystemExit(
            "run gen_soco60b_attestation.py and gen_rsoco_attestation.py first"
        )
    ev = verify(bundle, a.pinned_sha)
    print(json.dumps(ev, indent=1))
    att["governance"]["attested_by"] = (
        "R-SOCO-B (lane; owner rulings (A)/(B) 2026-09-25). Against keeper "
        "2026-09-24-r-soco-corrected-inputs the recipe is UNCHANGED; the only changes "
        "are three boundary repairs, machine-verified by execution in "
        "scripts/gen_rsocob_attestation.py: R1 the 2019 EIA-930 SOCO Total interchange "
        "sign window (constants.EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC); R2 the "
        "SOCO-60 current-BA-recode partition extended to the LP fleet (former Gulf "
        "Power plants); R3 PowerSouth's 2021-09-01 join (constants.ISO_BA_JOINS). Every "
        f"leg solved at {a.pinned_sha[:12]}; both new solve-surface rows present at "
        f"their live hashes; 2019 demand-with-interchange {ev['demand_2019_twh']} TWh. "
        "RULES 13/14: each is a published record reconciled to the boundary EIA-930 "
        "measures SOCO's load on; nothing measured about dispatch is fed back. RULES "
        "21/24/25: registry rows, zero scalars, SOCO only. RULE 1(c): no offer-curve "
        "band moved; AUTHORIZED PRICE TUNING IS DECLARED NONE. INHERITED: "
        + att["governance"]["attested_by"]
    )
    att["disclosures"]["precommit"] = (
        "docs/handoffs/r-soco/PRECOMMIT-r-soco-b-2026-09-25.md"
    )
    att["disclosures"]["rsoco_scope"] = (
        "2019-2025, one year-isolated shard per year (rule 36). The 2019-2022 inputs "
        "landed in I-SOCO (FINDING-i-soco-2019-2022-intake-2026-09-24). Recorded, not "
        "repaired: the 2019 hour 7148/7149 demand spike/dropout pair (35,329 / 6,913 MW); "
        "PowerSouth's Sep-Dec 2021 hydro budget (EIA-923 books it AEC, <= 0.01 TWh). "
        "Residual class-table heat rates Dahlberg (7709) / Hartwell (54538), 1,045 MW CT, "
        "an EPA-EIA facility-id crosswalk defect, routed."
    )
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    for name, basis in NEW_ENTRIES.items():
        if name not in names:
            fp["entries"].append(
                {
                    "name": name,
                    "value": True,
                    "identification": "measured-physical",
                    "n_scalars": 0,
                    "basis": basis,
                }
            )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {att_path} (n_entries={fp['n_entries']}, n_residual={fp['n_residual']})"
    )


if __name__ == "__main__":
    main()
