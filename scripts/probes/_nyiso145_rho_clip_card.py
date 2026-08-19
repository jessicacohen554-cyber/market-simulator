#!/usr/bin/env python3
"""nyiso-145 — the RHO_CLIP owner decision card, measured on committed artifacts.

Session nyiso-145, job 2. nyiso-144 measured ``online_rho`` for the first time
and found BOTH NYISO values below the code's own ``RHO_CLIP`` floor of 0.5, a
band that carries no primary citation anywhere in the repo, so ``rho_used``
returns the FLOOR rather than the measurement. The band was deliberately left
unchanged and escalated to the owner (rule 22 D-5(b)). This probe assembles the
evidence the ruling needs. It DOES NOT re-band anything and DOES NOT arm either
gated flag.

Three questions, all answered from committed artifacts with NO solve:

1. **Is 0.5 a physical floor?** Reported against every measured ``online_rho``
   row in the repo — NYISO's two family sets and MISO's, three independent
   fleets — together with each row's own ``rho_minload`` sensitivity. The
   min-load column is the direct successor of the LEGACY estimand the band was
   written for (``(pmax-pmin)/pmin`` evaluated at minimum stable load); the
   headline column is the AS-OPERATED estimand the measured seam introduced.

2. **What band would admit the measurement?** The smallest floor change that
   stops clipping every measured row, reported as a number rather than a
   recommendation.

3. **What does each of NYISO's two mutually-exclusive gated flags do at the
   measurement vs at the floor?** The gated row is
   ``R[c,z] <= rho * sum_{g eligible in z} P[g,t]``, so at a given rho the row
   binds in the hours ``rho * sum P < requirement``. Evaluated on the DESIGNATED
   KEEPER's own committed per-plant model hourlies (the run payload's ``m``
   series), reusing the nyiso-143 liveness construction:

   * ``nyiso_synchronised_reserve`` (path A) — one NYC row, requirement
     ``NYISO_SPIN_FRACTION x nyc_10min_total`` = 250 MW, eligible set = the
     quick-start (10-minute-capable) groups in NYC.
   * ``nyiso_incity_commitment_obligation`` — the NYC (500 MW) and Long Island
     (120 MW) 10-minute families move from class 1 to class 2, eligible set =
     quick-start UNION ST_GAS steam in each pocket.

Usage::

    python scripts/probes/_nyiso145_rho_clip_card.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.legitimacy_diagnostics import _decode_cf_bytes, load_bench  # noqa: E402

RUN_ID = "2026-08-18-nyiso-144-layup-exclusion"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/_nyiso145_rho_clip_card.json"
RHO_CLIP = (0.5, 4.0)
# The quick-start (10-minute-capable) groups, deliberately WIDE — the nyiso-143
# liveness set verbatim, so the two probes' eligible sets are comparable.
QUICK_GROUPS = {"CT_PEAKER", "CT_CHP", "ST_OIL", "OIL", "IC_OIL", "GT_OIL"}
STEAM_GROUPS = {"ST_GAS"}
# The rho ladder every family row is evaluated on. 0.5 is the clip FLOOR (what
# a run arming a gated flag today actually solves at); 1.0 is the legacy
# unidentified fallback; 4.0 is the clip CEILING.
LADDER = (0.2011, 0.3014, 0.5, 1.0, 4.0)

# (flag, family_set, [(zone, requirement_mw)], eligible groups)
FAMILIES = (
    (
        "nyiso_synchronised_reserve",
        "nyc_spin",
        (("NYC", 250.0),),
        QUICK_GROUPS,
    ),
    (
        "nyiso_incity_commitment_obligation",
        "incity_obligation",
        (("NYC", 500.0), ("Long_Island", 120.0)),
        QUICK_GROUPS | STEAM_GROUPS,
    ),
)


def _measured_rows() -> list[dict]:
    """Return every committed measured-``online_rho`` row, across all ISOs."""
    rows = []
    for path in sorted(
        (REPO / "data/raw/_processed-legacy").glob("campd_online_reserve_rho_*.csv")
    ):
        if path.name.endswith("_units.csv"):
            continue
        with path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                rho = float(r["rho"])
                rows.append(
                    {
                        "iso": r["iso"],
                        "family_set": r["family_set"],
                        "mechanism": r["mechanism"],
                        "rho": round(rho, 4),
                        "rho_minload": round(float(r["rho_minload"]), 4),
                        "rho_fullhour": round(float(r["rho_fullhour"]), 4),
                        "online_unit_hours": int(r["online_unit_hours"]),
                        "campd_coverage_frac": round(
                            float(r["campd_coverage_frac"]), 4
                        ),
                        "rho_used_today": round(
                            min(max(rho, RHO_CLIP[0]), RHO_CLIP[1]), 4
                        ),
                        "clipped_by_floor": rho < RHO_CLIP[0],
                        "minload_inside_band": RHO_CLIP[0]
                        <= float(r["rho_minload"])
                        <= RHO_CLIP[1],
                    }
                )
    return rows


def _pocket_online_mw(run: dict, bench: dict, year: int, zone: str, groups: set[str]):
    """Return the keeper's own hourly model MW online in *zone* for *groups*."""
    total = None
    used: list[str] = []
    for pid, p in run["years"][str(year)]["plants"].items():
        b = bench.get(pid)
        if b is None or not p.get("m"):
            continue
        if str(b.get("zone") or "") != zone or str(b.get("group") or "") not in groups:
            continue
        mw = _decode_cf_bytes(p["m"], p.get("m_ann"), float(b.get("npl") or 0.0))
        total = np.asarray(mw, dtype=float) if total is None else total + mw
        used.append(pid)
    return total, used


def main() -> int:
    """Assemble and write the decision card record."""
    measured = _measured_rows()
    floors_needed = [r["rho"] for r in measured]
    card: dict = {
        "run_id": RUN_ID,
        "rho_clip_today": list(RHO_CLIP),
        "measured_rows": measured,
        "band_that_admits_every_measurement": [
            round(min(floors_needed), 4),
            RHO_CLIP[1],
        ],
        "families": {},
    }
    print("MEASURED online_rho ROWS (every one in the repo)")
    print(
        f'{"iso":6s} {"family_set":20s} {"rho":>7s} {"minload":>8s} '
        f'{"used":>6s} {"clip?":>6s} {"cover":>6s} {"unit-h":>10s}'
    )
    for r in measured:
        print(
            f'{r["iso"]:6s} {r["family_set"]:20s} {r["rho"]:7.4f} '
            f'{r["rho_minload"]:8.4f} {r["rho_used_today"]:6.2f} '
            f'{("FLOOR" if r["clipped_by_floor"] else "-"):>6s} '
            f'{r["campd_coverage_frac"]:6.3f} {r["online_unit_hours"]:10d}'
        )
    print(
        "\nband that admits every measurement: "
        f'[{card["band_that_admits_every_measurement"][0]}, {RHO_CLIP[1]}]'
    )

    side = json.loads(
        (REPO / f"frontend/data/backcast/registry/{RUN_ID}.json").read_text()
    )
    run = ba.decode_run_js((REPO / side["file"]).read_text())
    for flag, family_set, zone_reqs, groups in FAMILIES:
        print(f"\n{flag}  (family_set {family_set})")
        entry: dict = {"family_set": family_set, "zones": {}}
        for zone, req in zone_reqs:
            entry["zones"][zone] = {"requirement_mw": req, "years": {}}
            print(f'  zone {zone}  requirement {req:.0f} MW')
            print(
                f'    {"year":6s} {"plants":>6s} {"onlineMW p50":>12s} '
                + "".join(f"{'rho=' + str(x):>13s}" for x in LADDER)
            )
            for year in YEARS:
                bench = load_bench(REPO, "NYISO", year)
                total, used = _pocket_online_mw(run, bench, year, zone, groups)
                if total is None:
                    entry["zones"][zone]["years"][str(year)] = {
                        "error": "no eligible plants"
                    }
                    continue
                row: dict = {
                    "n_plants": len(used),
                    "online_mw_p50": round(float(np.median(total)), 1),
                    "online_mw_p05": round(float(np.percentile(total, 5)), 1),
                    "bind": {},
                }
                cells = []
                for rho in LADDER:
                    short = rho * total < req
                    row["bind"][str(rho)] = {
                        "binding_hours": int(short.sum()),
                        "binding_share": round(float(short.mean()), 4),
                        "worst_deficit_mw": round(
                            float(np.max(req - rho * total[short]))
                            if short.any()
                            else 0.0,
                            1,
                        ),
                    }
                    cells.append(f"{int(short.sum()):6d}h {short.mean():5.1%}")
                entry["zones"][zone]["years"][str(year)] = row
                print(
                    f'    {year:6d} {len(used):6d} {row["online_mw_p50"]:12.1f} '
                    + "".join(f"{c:>13s}" for c in cells)
                )
        card["families"][flag] = entry
    OUT.write_text(json.dumps(card, indent=1) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
