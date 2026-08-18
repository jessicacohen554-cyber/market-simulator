"""nyiso-143 — is `nyiso_synchronised_reserve` inert on NYISO's designated keeper?

The matrix (NYISO shard, cell ``U``) argues the mechanism is inert by
construction, on the ground that it "is a construction of exactly the class-2
online-gate family nyiso-110 measured EXHAUSTED at NYISO: the class-2 row is an
AGGREGATE rho*output row that reserve-eligible hydro's own 2-5 GW of output
keeps slack in every hour".

This probe tests that claim against the committed code and the keeper's own
committed dispatch. It spends NO solve and reads only committed artifacts.

The armed family is ``nyc_spin_online``: ``zone_mask`` = NYC ONLY, requirement
``NYISO_SPIN_FRACTION x nyc_10min_total`` = 0.5 x 500 = 250 MW static
(``results/scarcity.py::nyiso_spin_requirement_mw``). The online-gated headroom
row it draws on is written PER ZONE — ``R[c,z] - rho * sum_{elig g in z} P[g]
<= 0`` (``model/lp/reserve_rows.py``, the ``headroom_products is None and
gated[h]`` branch) — so the family can only be backed by NYC-zone online
quick-start output. ``rho`` is clipped to [0.5, 4.0].

INERTNESS TEST (sufficient, and the same shape as nyiso-110's own E4 liveness
census): if the keeper's incumbent dispatch already satisfies
``rho * P_NYC_quickstart(t) >= 250`` in EVERY hour, the added row is slack at
the incumbent optimum, the incumbent stays feasible and optimal for the
augmented LP, and arming the flag is bit-identical. If it is violated in any
hour, the family BINDS there and the mechanism is live.

The eligible set is over-stated on purpose (every CT / oil / peaking group in
the bench, whatever its taxonomy) and ``rho`` is set to its MAXIMUM admissible
4.0, so the screen is biased HARD toward finding inertness. A violation under
those settings is therefore decisive; a pass would not be, and is reported as
the weaker statement it is.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.legitimacy_diagnostics import (  # noqa: E402
    _decode_cf_bytes,
    load_bench,
)

RUN_ID = "2026-08-17-nyiso-142-stackdup"
YEARS = (2023, 2024, 2025)
REQUIREMENT_MW = 250.0  # NYISO_SPIN_FRACTION (0.5) x nyc_10min_total (500 MW)
RHO_MAX = 4.0  # the clip ceiling in reserves/spec.py — the generous end
# THE MEASURED VALUE (_nyiso143_online_rho.py): rho falls through to the
# hard-coded `else: online_rho = 1.0` branch in EVERY year, because ZERO of
# the 363 / 355 / 211 quick-start-eligible NYISO units carry pmin > 0 under
# the keeper's CAMPD-binned plant-level fleet — so the declared
# "(pmax-pmin)/pmin fleet property" identification never evaluates here.
RHO_MEASURED = 1.0
SPIN_ZONE = "NYC"
# Deliberately WIDE: every group that could plausibly carry a gas_ct / oil
# fuel type. QUICK_START_FUEL_TYPES is {gas_ct, oil}; hydro joins the class
# only under nyiso_hydro_reserve_eligible and NYISO has no NYC hydro.
QUICK_GROUPS = {"CT_PEAKER", "CT_CHP", "ST_OIL", "OIL", "IC_OIL", "GT_OIL"}


def main() -> int:
    side = json.loads(
        (REPO / f"frontend/data/backcast/registry/{RUN_ID}.json").read_text()
    )
    run = ba.decode_run_js((REPO / side["file"]).read_text())
    out: dict = {
        "run_id": RUN_ID,
        "requirement_mw": REQUIREMENT_MW,
        "rho_used": RHO_MEASURED,
        "rho_clip_ceiling_for_reference": RHO_MAX,
        "spin_zone": SPIN_ZONE,
        "quick_groups": sorted(QUICK_GROUPS),
        "years": {},
    }
    for year in YEARS:
        bench = load_bench(REPO, "NYISO", year)
        # plant code -> (zone, groups)
        zone_of: dict[str, str] = {}
        groups_of: dict[str, set[str]] = {}
        for key, b in bench.items():
            code = key.split(":")[0]
            zone_of[code] = str(b.get("zone") or "")
            groups_of.setdefault(code, set()).add(str(b.get("group") or ""))
        plants = run["years"][str(year)]["plants"]
        total = None
        used: list[str] = []
        for pid, p in plants.items():
            if not p.get("m"):
                continue
            code = pid.split(":")[0]
            if zone_of.get(code) != SPIN_ZONE:
                continue
            # Match the PAYLOAD KEY'S OWN class slice, not the plant's union:
            # a multi-class plant's steam slice is not quick-start capacity
            # just because the plant also owns a CT slice.
            b_self = bench.get(pid)
            own_group = str((b_self or {}).get("group") or "")
            if not own_group and ":" not in pid:
                own_group = next(iter(groups_of.get(code, {""})))
            if own_group not in QUICK_GROUPS:
                continue
            npl = float((b_self or {}).get("npl") or 0.0)
            mw = _decode_cf_bytes(p["m"], p.get("m_ann"), npl)
            total = mw.astype(float) if total is None else total + mw.astype(float)
            used.append(pid)
        if total is None:
            out["years"][str(year)] = {"error": "no NYC quick-start plants found"}
            continue
        backed = RHO_MEASURED * total
        short = backed < REQUIREMENT_MW
        backed_ceiling = RHO_MAX * total
        short_ceiling = backed_ceiling < REQUIREMENT_MW
        out["years"][str(year)] = {
            "n_plants": len(used),
            "plants": sorted(used),
            "hours": int(total.size),
            "nyc_quickstart_mw_p0": round(float(np.min(total)), 3),
            "nyc_quickstart_mw_p50": round(float(np.median(total)), 3),
            "nyc_quickstart_mw_p100": round(float(np.max(total)), 3),
            "binding_hours": int(short.sum()),
            "binding_share": round(float(short.mean()), 4),
            "worst_deficit_mw": round(
                float(np.max(REQUIREMENT_MW - backed[short])) if short.any() else 0.0, 3
            ),
            "binding_hours_at_rho_ceiling_4.0": int(short_ceiling.sum()),
            "verdict": "BINDS (mechanism is LIVE)"
            if short.any()
            else "slack in every hour",
            # THE DECISIVE NUMBER: the family is inert iff the solve's actual
            # rho is at least this. rho is a fleet property clipped to
            # [0.5, 4.0], so a rho* above 4.0 means the mechanism binds for
            # EVERY admissible rho and inertness is impossible.
            "rho_star_for_inertness": round(
                float(REQUIREMENT_MW / max(float(np.min(total)), 1e-9)), 4
            ),
        }
    print(json.dumps(out, indent=1))
    (REPO / "results/calibration/_nyiso143_nyc_spin_liveness.json").write_text(
        json.dumps(out, indent=1) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
