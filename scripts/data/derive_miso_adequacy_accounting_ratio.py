#!/usr/bin/env python
"""Derive MISO's internal-supply accounting ratio — the D31 value and its
dates-ON re-identification (capx D51) — from committed operands only.

The registry constant ``ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]``
(``src/market_sim/config/capacity_market.py``, capx D31 2026-09-02) is the
Planning Resource Auction's Summer offered Generation ZRC over the model's
own census internal firm capacity on the two clean overlap years
(PY2023-24 ↔ the 2023 entering fleet, PY2024-25 ↔ the 2024 entering fleet):

    r0 = (122,375.6 + 123,395.6) / (143,822.1 + 143,749.5) = 0.8546

**Why a second value exists (rule 23 ``[R-FROZEN-DERIVE]`` — a POSTURE change
of the fleet the ratio was identified on, never a residual).** D31's
denominators are the committed D27 T1-H entering-fleet ledgers, a census that
still carried the 2021–2023 real exits (St Clair, Schahfer, Meramec, Edwards,
Trenton Channel, Dolet Hills, River Rouge, Gallagher …) which the PRA had
already dropped, so ``r0`` absorbed them. Since owner ruling Q30 / capx D44
(``fossil_announced_exits_enabled`` default ON, 2026-09-03) the fossil-dates
channel removes those same plants explicitly at step 1b, and ``r0`` still
applies — the same MW netted twice (FINDING-capx-d49-2026-09-04.md §2.6). The
re-identification moves ONE term of D31's arithmetic, the denominators, to the
fleet in the SAME posture the run applies:

    r1 = Σ offered / Σ (D31 denominator − accredited dated exits)

where the accredited dated exits are the per-fuel difference between the D27
and the D46 (dates-ON) ledgers' ``fleet_by_fuel_before`` at the class
accreditation ``1 − EFORd`` — measured on the committed ledgers, not retyped
from any finding (the D27 − D46 difference is exactly the pre-start backlog +
the step-1b drops + the step-1b derates, verified in the D51 pre-declaration;
the non-fossil announced channel is identical in both and is NOT part of the
moved term). Everything else is held: the PRA numerators, the class bases
(1 − EFORd; wind 0.166; solar 0.3875; hydro 0.62; storage firm), the run's
prior-solved-year pool convention, the Summer season, the two-year
capacity-weighted mean, the D27 pools (a model outcome — D33's VRE additions —
must not enter, exactly as D31 held), and the external tie.

Three committed inputs, nothing else:

* ``data/raw/capacity-market/auction-supply/miso/miso.csv`` — Summer offered
  Generation ZRC rows (the numerators; ``capacity-market-auction-supply``).
* ``results/hindcast/miso-2021-2025-realized-t1h-d27/MISO/<key>/evolution_{2023,2024}.json``
  and ``…/evolution_{2021,2023}.json`` — D31's denominators, REPRODUCED from
  the ledgers (the known-answer check: 143,822.1 / 143,749.5 to the decimal).
* ``results/hindcast/miso-2021-2025-realized-t1h-d46/MISO/<key>/evolution_{2023,2024}.json``
  — the dates-ON ``fleet_by_fuel_before``.

Zero free parameters. The reconciliation test
(``tests/curation/test_derive_miso_adequacy_accounting_ratio.py``) asserts
both registry constants equal this derivation, so neither can drift from the
committed data. Run ``python scripts/data/derive_miso_adequacy_accounting_ratio.py``
to print the derivation table; ``--json`` for the operands. Re-derive only when
a source updates (a PRA re-anchor, a fleet-vintage or posture change) — never
on a residual.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:  # resolve ``scripts.lib`` when run as a plain script
    sys.path.insert(0, str(REPO))

from scripts.lib import capacity_market_auction_supply as asup  # noqa: E402

# The two clean overlap years: planning year ↔ the model's entering fleet year,
# and the PRIOR solved year whose pools the runner's position consumed
# (2022 is the quarantined bridge, so 2023's pools are 2021's).
OVERLAP: tuple[tuple[str, int, int], ...] = (
    ("2023-2024", 2023, 2021),
    ("2024-2025", 2024, 2023),
)

# Class accreditation bases D31 documented (capacity_market.py citation block):
# wind / solar at the MISO published credits, hydro at the published 0.62.
WIND_CREDIT = 0.166
SOLAR_CREDIT = 0.3875
HYDRO_CREDIT = 0.62

D27_BUNDLE = REPO / "results" / "hindcast" / "miso-2021-2025-realized-t1h-d27"
D46_BUNDLE = REPO / "results" / "hindcast" / "miso-2021-2025-realized-t1h-d46"


def _ledger_dir(bundle: Path) -> Path:
    """The single ``MISO/<cache_key>/`` directory of a committed bundle."""
    dirs = sorted(glob.glob(str(bundle / "MISO" / "*")))
    if len(dirs) != 1:
        raise FileNotFoundError(
            f"expected one MISO/<key>/ dir under {bundle}, found {dirs}"
        )
    return Path(dirs[0])


def load_ledger(bundle: Path, year: int) -> dict:
    """Load one committed ``evolution_<year>.json`` ledger."""
    return json.loads((_ledger_dir(bundle) / f"evolution_{year}.json").read_text())


def offered_generation(raw_root: Path | None = None) -> dict[str, float]:
    """Summer offered Generation ZRC by planning year from the committed PRA rows."""
    df = asup.parse_iso("MISO", raw_root or (REPO / "data" / "raw"))
    gen = df[
        (df["metric"] == "offered")
        & (df["category"] == "generation")
        & (df["season"] == "summer")
    ].set_index("planning_year")["value_mw"]
    return {py: float(gen.loc[py]) for py, _y, _p in OVERLAP}


def thermal_accredited_mw(
    fleet_by_fuel: dict[str, float], eford: dict[str, float]
) -> float:
    """Σ nameplate × (1 − EFORd) over a per-fuel fleet total (the UCAP ledger basis)."""
    return sum(float(mw) * (1.0 - eford[f]) for f, mw in fleet_by_fuel.items())


def census_denominator(
    bundle: Path, year: int, pools_year: int, eford: dict[str, float]
) -> float:
    """The model's entering internal firm capacity on D31's documented bases."""
    d = load_ledger(bundle, year)
    p = load_ledger(bundle, pools_year)
    return (
        thermal_accredited_mw(d["fleet_by_fuel_before"], eford)
        + float(p["wind_cap_mw"]) * WIND_CREDIT
        + float(p["solar_cap_mw"]) * SOLAR_CREDIT
        + float(d["firm_clean_mw"]) * HYDRO_CREDIT
        + float(p["storage_firm_mw"])
    )


def dated_exits_accredited_mw(
    year: int, eford: dict[str, float]
) -> tuple[float, dict[str, float]]:
    """Accredited MW of the dated-channel exits entering ``year``: D27 − D46 by fuel."""
    a = load_ledger(D27_BUNDLE, year)["fleet_by_fuel_before"]
    b = load_ledger(D46_BUNDLE, year)["fleet_by_fuel_before"]
    by_fuel = {f: float(a[f]) - float(b.get(f, 0.0)) for f in a}
    return sum(mw * (1.0 - eford[f]) for f, mw in by_fuel.items()), by_fuel


def derive(raw_root: Path | None = None) -> dict:
    """Return the full derivation: numerators, both denominator sets, both ratios."""
    from market_sim.config.constants import EFORD  # lazy: keep the CLI import-light

    offered = offered_generation(raw_root)
    rows = []
    for py, year, pools_year in OVERLAP:
        den0 = census_denominator(D27_BUNDLE, year, pools_year, EFORD)
        dated, by_fuel = dated_exits_accredited_mw(year, EFORD)
        rows.append(
            {
                "planning_year": py,
                "fleet_year": year,
                "pools_year": pools_year,
                "offered_generation_mw": offered[py],
                "d31_denominator_mw": den0,
                "dated_exits_nameplate_by_fuel_mw": by_fuel,
                "dated_exits_accredited_mw": dated,
                "dated_net_denominator_mw": den0 - dated,
                "ratio_d31_year": offered[py] / den0,
                "ratio_dated_net_year": offered[py] / (den0 - dated),
            }
        )
    num = sum(r["offered_generation_mw"] for r in rows)
    return {
        "rows": rows,
        "ratio_d31": num / sum(r["d31_denominator_mw"] for r in rows),
        "ratio_dated_net": num / sum(r["dated_net_denominator_mw"] for r in rows),
    }


def main(argv: list[str] | None = None) -> int:
    """Print the derivation table (or ``--json``)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="emit the operands as JSON")
    args = ap.parse_args(argv)
    out = derive()
    if args.json:
        print(json.dumps(out, indent=1))
        return 0
    print(
        "planning_year  fleet_yr  offered_gen   D31 denom   dated acc.   dated-net denom   r(D31)    r(dated-net)"
    )
    for r in out["rows"]:
        print(
            f"{r['planning_year']:>13}  {r['fleet_year']:>8}  {r['offered_generation_mw']:>11,.1f}"
            f"  {r['d31_denominator_mw']:>10,.1f}  {r['dated_exits_accredited_mw']:>10,.1f}"
            f"  {r['dated_net_denominator_mw']:>15,.1f}  {r['ratio_d31_year']:.5f}   {r['ratio_dated_net_year']:.5f}"
        )
    print(
        f"combined (capacity-weighted): r0 = {out['ratio_d31']:.6f}   r1 = {out['ratio_dated_net']:.6f}"
    )
    print("ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO = {")
    a, b = out["rows"]
    print(
        f'    "MISO": ({a["offered_generation_mw"]:_.1f} + {b["offered_generation_mw"]:_.1f})'
        f" / ({a['dated_net_denominator_mw']:_.1f} + {b['dated_net_denominator_mw']:_.1f}),"
    )
    print("}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
