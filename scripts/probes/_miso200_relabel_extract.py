"""miso-200 -- build the arm's extract by RELABELLING the committed one.

===============================================================================
WHY A RELABEL AND NOT A RE-DERIVATION
===============================================================================
The object under test is the ROUTING -- which model bin a detected outage window
is charged to -- not the DETECTOR. Re-running the full deriver to produce the
arm's extract would fold in every change to the detector and its source data
since the committed extract was built, and that drift is real and large:
measured at this HEAD, a fresh unrepaired derivation of
``campd-unit-outages-MISO.csv`` does NOT reproduce the committed file (row
counts differ materially in years this session does not even touch). An A/B on
a re-derived extract would therefore carry the routing repair AND that drift
together, and could not attribute either.

So the arm's extract is the COMMITTED extract with exactly one column rewritten:
``plant_group``, on exactly the rows the production resolver re-routes. That
makes the delta a single object by construction, keeps the control leg reading
byte-identical committed input (gate S-0), and lets the frozen L-3b line mean
what it says.

**The routing decision is never made here.** It is delegated to the production
:func:`scripts.data.derive_campd_unit_outages._resolve_unit_group` with
``mixed_gas_routing=True``, called with the SAME facility-group maps the deriver
builds (last-writer-wins reproduced, not corrected) and the SAME CAMPD unit
attributes. This script only decides WHICH FILE the answer is written into.

``plant_group`` is the only column the overlay reads for routing: the derate
denominator is the FLEET bin capacity ``cap[tgt]``
(``outages._iso_plant_capacity``), never the extract's own
``plant_capacity_mw``, which -- with ``unit_pct_of_plant`` -- is informational.
They are rewritten anyway wherever they are functions of the changed group, and
the frozen probe's L-3b treats all three as one object.

The ``--mixed-gas-routing`` flag added to both derivers in the same commit is
the FORWARD path: a future re-derivation reproduces this routing from source.
This script exists so that THIS session's A/B isolates the object.

Usage:
    python3 scripts/probes/_miso200_relabel_extract.py --iso MISO
    python3 scripts/probes/_miso200_relabel_extract.py --iso MISO --maxgen
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import pandas as pd  # noqa: E402

from market_sim.data import campd  # noqa: E402
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    _resolve_unit_group,
)

GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP")


def fleet_group_maps(iso: str):
    """The DERIVER's own maps, last-writer-wins reproduced (never corrected)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

    cfg = get_iso_config(iso)
    fleet = load_fleet_from_csv(iso, cfg) + load_retired_within_window(iso, cfg)
    group_by_code: dict[int, str] = {}
    groups_by_code: dict[int, set[str]] = {}
    for g in fleet:
        if int(g.plant_code) > 0 and g.plant_group:
            group_by_code[int(g.plant_code)] = g.plant_group
            groups_by_code.setdefault(int(g.plant_code), set()).add(g.plant_group)
    return group_by_code, groups_by_code


def unit_attributes(iso: str, years: range) -> dict[tuple[int, str], tuple[str, str]]:
    """``{(facilityId, unitId): (unitType, primaryFuelInfo)}`` from raw CAMPD."""
    out: dict[tuple[int, str], tuple[str, str]] = {}
    for st in campd.states_for_iso(iso):
        for y in years:
            p = _REPO / "data" / "raw" / "campd-unit-level" / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            df = pd.read_parquet(
                p, columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
            ).drop_duplicates(subset=["facilityId", "unitId"])
            for r in df.itertuples(index=False):
                out.setdefault(
                    (int(r.facilityId), str(r.unitId)),
                    (str(r.unitType), str(r.primaryFuelInfo)),
                )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument(
        "--maxgen",
        action="store_true",
        help="Relabel the declared-event maxgen extract instead of the std one.",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    raw = _REPO / "data" / "raw"
    if args.maxgen:
        src = raw / f"campd-unit-outages-maxgen-{iso}.csv"
        dst = raw / f"campd-unit-outages-maxgen-unitroute-{iso}.csv"
    else:
        src = raw / f"campd-unit-outages-{iso}.csv"
        dst = raw / f"campd-unit-outages-unitroute-{iso}.csv"
    df = pd.read_csv(src)
    gbc, gsbc = fleet_group_maps(iso)
    attrs = unit_attributes(iso, range(2019, 2027))

    new_groups: list[str] = []
    changed = 0
    unresolved: set[tuple[int, str]] = set()
    for r in df.itertuples(index=False):
        fac, uid = int(r.facility_id), str(r.unit_id)
        cur = str(r.plant_group)
        key = (fac, uid)
        fac_groups = gsbc.get(fac, set())
        multi = len([g for g in fac_groups if g in GAS_GROUPS]) >= 2
        if not multi or key not in attrs:
            # Not in scope, or the unit has no CAMPD attribute row to route by
            # (a pre-2019 vintage whose source parquet is untracked). FAIL
            # CLOSED: keep the committed group rather than guess.
            if multi and key not in attrs:
                unresolved.add(key)
            new_groups.append(cur)
            continue
        ut, fuel = attrs[key]
        rep = _resolve_unit_group(
            str(fuel).strip().lower() in ("coal", "coal refuse"),
            ut,
            fac_groups,
            gbc.get(fac),
            fuel,
            mixed_gas_routing=True,
        )
        if rep != cur:
            changed += 1
        new_groups.append(rep)
    df["plant_group"] = new_groups
    df.to_csv(dst, index=False)
    print(f"{src.name} -> {dst.name}")
    print(f"  rows {len(df)}   plant_group rewritten on {changed} row(s)")
    if unresolved:
        print(
            f"  {len(unresolved)} in-scope unit(s) had no CAMPD attribute row "
            f"and kept the committed group (fail-closed): "
            f"{sorted(unresolved)[:10]}"
        )


if __name__ == "__main__":
    main()
