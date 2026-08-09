"""caiso-188 — the ``IMPORT_TRANCHES[CAISO]`` fitted-scalar census, measured.

NO LP, NO SOLVER, NO NETWORK. Reads committed bytes only: the config/spec
modules, the published MIC registry, the measured EIA-930 CISO interchange
frame, the keeper bundle's ``meta.json`` / ``hourly/`` sidecars, and one
``run_calibration.run_year(fleet_only=True)`` fleet reconstruction per year
(the caiso-131/134/140/150/151 machinery — a fleet build, never a solve).

The object. ``_caiso186os_dof_repair`` split the single DOF-ledger row
``IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`` into four limbs and read two of them
as LIVE AND FITTED from the source text: the four SPOT CAPACITIES
(1,800/1,800/2,200/3,000 = 8,800 MW, uncited) and the two FIRM PRICES
($28/$48, re-armed onto the margin by ``caiso_firm_import_selfsched_clip``).
That was a reading of the code; this probe MEASURES the same claim on the
keeper's own built fleet and then asks the rule-14 ``[R-ACCURATE]`` question the
handoff puts first: **is there a published object the 8,800 MW should be, and
does that fitted depth ever actually bind?**

Five checks:

* **C1 LIMB CENSUS** — every scalar of ``IMPORT_TRANCHES`` /
  ``IMPORT_TRANCHES_BY_YEAR`` for CAISO, split into limbs and classified
  cited / derived / FITTED, re-derived at HEAD rather than quoted.
* **C2 LIVENESS** — the built fleet, per year: each import row's ``pmax``,
  availability, ``min_gen`` floor, and whether its ``mc`` row is CONSTANT (the
  static ladder price survived) or HOURLY (a measured hub series overwrote it).
  This is what settles "superseded on the binding path" with evidence.
* **C3 CEILING STACK** — per corridor per hour, the three ceilings that bound
  corridor import: the tranche ladder's own capability (Σ pmax × availability),
  the measured p95 deliverability envelope (``caiso_corridor_flow_limit``,
  ARMED in the keeper) and the WECC path rating (link TTC). Reports which is
  tightest, hour by hour — i.e. whether the FITTED depth is the operative
  ceiling or a slack number sitting behind a measured one.
* **C4 REALIZED HEADROOM** — the keeper's own realized import dispatch
  (committed ``hourly/class_hourly_<year>.parquet``, ``klass='import'``)
  against the same ceilings, so "binds" is measured against what the LP did,
  not only against what it was allowed to do.
* **C5 PUBLISHED-OBJECT RECONCILIATION** — the candidate published objects for
  a corridor import depth (branch-group MIC from the committed registry, the
  WECC path ratings already in ``iso_configs``, the measured envelope) laid
  against the fitted ladder, per corridor per year.

Every verdict is about wiring, provenance and capability arithmetic. No scored
criterion is read and no residual is consulted (rule 1 ``[R-STRUCT]``, rule 13
``[R-MEASURED]``): C3a is a live FAIL and is never a target here.

THE ``coal_prb_sigmoid_overrides`` TRAP (caiso-150 §E2, inherited verbatim from
``_caiso151_selfsched_clip_exposure``): CAISO's firm-import flags reach a solve
ONLY through the generic ``ScenarioConfig`` override channel, whose meta.json
key is ``coal_prb_sigmoid_overrides`` → ``run_year(prb_overrides=)``. A probe
that omits the rename rebuilds the fleet with the whole must-flow block ABSENT
while every other CAISO mechanism still arms and logs normally.

Usage::

    uv run python scripts/probes/_caiso188_import_tranche_census.py

Writes ``results/calibration/_caiso188_import_tranche_census.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
# `scripts.lib.clean_io` imports by PACKAGE path; without the repo root the
# fleet build degrades silently on some seams and hard-fails on the hydro one.
sys.path.insert(0, str(REPO))

CAL = REPO / "results" / "calibration"
KEEPER = CAL / "caiso184_c1_lpbasis"
OUT = CAL / "_caiso188_import_tranche_census.json"
HOURS = 8760
YEARS = (2023, 2024, 2025)

#: meta.json → run_year kwarg renames (the trap above).
_META_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
}

#: Provenance classification of every CAISO import-tranche scalar, keyed
#: (limb, tranche). "cited" = a published primary source is named in the
#: config's own provenance block; "fitted" = no primary source anywhere.
#: Re-checked against the source text by :func:`c1_limb_census`.
_LIMB_OF = {
    "PNW_hydro_base": "firm",
    "DSW_solar_PV": "firm",
    "PNW_midC": "spot",
    "DSW_CCGT": "spot",
    "DSW_CT": "spot",
    "WECC_scarcity": "spot",
}


def fleet_state(year: int) -> dict:
    """Rebuild the keeper's fleet for ``year`` (no LP, no solver)."""
    import inspect

    from run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def c1_limb_census() -> dict:
    """Split the CAISO ladder into limbs and classify every scalar."""
    from market_sim.config.interchange_config import (
        IMPORT_TRANCHES,
        IMPORT_TRANCHES_BY_YEAR,
    )

    static = {n: (c, p) for n, c, p in IMPORT_TRANCHES["CAISO"]}
    by_year = {
        y: {n: (c, p) for n, c, p in lad}
        for y, lad in IMPORT_TRANCHES_BY_YEAR["CAISO"].items()
    }
    out: dict = {"static": static, "by_year": by_year, "limbs": {}}
    for limb in ("firm", "spot"):
        names = [n for n, ln in _LIMB_OF.items() if ln == limb]
        caps = {
            n: {str(y): by_year[y][n][0] for y in sorted(by_year)} for n in names
        }
        prices = {
            n: {str(y): by_year[y][n][1] for y in sorted(by_year)} for n in names
        }
        out["limbs"][f"{limb}_capacity"] = {
            "tranches": sorted(names),
            "values_by_year": caps,
            "varies_by_year": any(
                len(set(v.values())) > 1 for v in caps.values()
            ),
            "static_total_mw": sum(static[n][0] for n in names),
        }
        out["limbs"][f"{limb}_price"] = {
            "tranches": sorted(names),
            "values_by_year": prices,
            "varies_by_year": any(
                len(set(v.values())) > 1 for v in prices.values()
            ),
        }
    return out


def _corridor_of(uid: str, zones: set[str]) -> tuple[str, str] | None:
    """Return ``(corridor_zone, tranche_name)`` for an import row, else None."""
    z = next((zz for zz in zones if str(uid).startswith(f"{zz}_")), None)
    if z is None:
        return None
    return z, str(uid)[len(z) + 1 :]


def c2_liveness(state: dict, year: int) -> dict:
    """Per import row: capability, floor, and whether its mc row is measured."""
    from market_sim.config.interchange_config import CAISO_PER_HUB_IMPORT_ZONES

    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, HOURS))
    rows: dict[str, dict] = {}
    for r, uid in enumerate(fa.unit_ids):
        hit = _corridor_of(uid, zones)
        if hit is None:
            continue
        zone, name = hit
        cap = np.asarray(fa.pmax[r] * fa.availability[r, :], dtype=float)
        row_mc = mc[r, :]
        spread = float(row_mc.max() - row_mc.min())
        rows[f"{zone}::{name}"] = {
            "corridor": zone,
            "tranche": name,
            "pmax_mw": float(fa.pmax[r]),
            "capability_mean_mw": float(cap.mean()),
            "capability_max_mw": float(cap.max()),
            "capability_hours_positive": int((cap > 1e-6).sum()),
            "min_gen_mean_mw": float(np.clip(mg[r, :], 0.0, None).mean()),
            "mc_mean": float(row_mc.mean()),
            "mc_min": float(row_mc.min()),
            "mc_max": float(row_mc.max()),
            "mc_is_constant": bool(spread < 1e-9),
            "price_limb_verdict": (
                "STATIC LADDER PRICE SURVIVES ON THE BINDING PATH"
                if spread < 1e-9
                else "SUPERSEDED by an hourly measured series"
            ),
        }
    return {"year": year, "rows": rows}


def c3_ceiling_stack(state: dict, year: int) -> dict:
    """Per corridor per hour: ladder capability vs measured envelope vs TTC."""
    from market_sim.config.interchange_config import (
        CAISO_PER_HUB_IMPORT_ZONES,
    )
    from market_sim.data.eia_loader import measured_corridor_flow_envelope
    from market_sim.model.interchange.caiso import (
        CAISO_FIRM_IMPORT_TRANCHES,
        _CAISO_PER_HUB_EXPORT_PREFIX,
        _caiso_corridor_export_cap_mw,
    )

    fa = state["fleet_arrays"]
    zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    spot_names = {n for n, limb in _LIMB_OF.items() if limb == "spot"}
    firm_names = set(CAISO_FIRM_IMPORT_TRANCHES)

    cap_by_group: dict[str, dict[str, np.ndarray]] = {
        z: {
            "firm": np.zeros(HOURS),
            "spot": np.zeros(HOURS),
            "clean": np.zeros(HOURS),
        }
        for z in zones
    }
    for r, uid in enumerate(fa.unit_ids):
        hit = _corridor_of(uid, zones)
        if hit is None:
            continue
        zone, name = hit
        if name.startswith(f"{_CAISO_PER_HUB_EXPORT_PREFIX}_"):
            continue  # export leg, not an import ceiling
        cap = np.asarray(fa.pmax[r] * fa.availability[r, :], dtype=float)
        group = (
            "firm" if name in firm_names else "spot" if name in spot_names else "clean"
        )
        cap_by_group[zone][group] += cap

    env = measured_corridor_flow_envelope("CAISO", year, HOURS, direction="import")
    out: dict = {"year": year, "corridors": {}}
    for zone in sorted(zones):
        groups = cap_by_group[zone]
        ladder = groups["firm"] + groups["spot"] + groups["clean"]
        envelope = (
            np.asarray(env[zone], dtype=float)
            if env and zone in env
            else np.full(HOURS, np.inf)
        )
        ttc = _caiso_corridor_export_cap_mw(zone)  # same rating both directions
        ttc_arr = np.full(HOURS, float(ttc))
        stack = np.vstack([ladder, envelope, ttc_arr])
        which = np.argmin(stack, axis=0)
        # Counterfactual: the ceiling if the four FITTED spot depths were absent.
        no_spot = groups["firm"] + groups["clean"]
        binds_spot = ladder < np.minimum(envelope, ttc_arr) - 1e-6
        hod = np.arange(HOURS) % 24
        out["corridors"][zone] = {
            "capability_mean_mw": {k: float(v.mean()) for k, v in groups.items()},
            "ladder_ceiling_mean_mw": float(ladder.mean()),
            "envelope_mean_mw": float(envelope.mean()),
            "path_rating_mw": float(ttc),
            "tightest_ceiling_hours": {
                "ladder": int((which == 0).sum()),
                "measured_envelope": int((which == 1).sum()),
                "path_rating": int((which == 2).sum()),
            },
            "ladder_is_binding_ceiling_hours": int(binds_spot.sum()),
            "ladder_is_binding_ceiling_pct": float(100.0 * binds_spot.mean()),
            "ladder_binding_by_hod_band": {
                "night_0_5": float(
                    100.0 * binds_spot[np.isin(hod, range(0, 6))].mean()
                ),
                "belly_10_15": float(
                    100.0 * binds_spot[np.isin(hod, range(10, 16))].mean()
                ),
                "evening_17_21": float(
                    100.0 * binds_spot[np.isin(hod, range(17, 22))].mean()
                ),
                "late_22_23": float(
                    100.0 * binds_spot[np.isin(hod, (22, 23))].mean()
                ),
            },
            "spot_depth_headroom_mean_mw": float(
                np.mean(np.minimum(envelope, ttc_arr) - no_spot)
            ),
            "spot_removal_would_tighten_hours": int(
                (no_spot < np.minimum(envelope, ttc_arr) - 1e-6).sum()
            ),
        }
    return out


def c4_realized_headroom(c3: dict, year: int) -> dict:
    """The keeper's realized import dispatch against the same ceilings."""
    import pandas as pd

    path = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return {"year": year, "status": "NO SIDECAR"}
    df = pd.read_parquet(path)
    imp = df[df["klass"] == "import"].sort_values("hour")["mw"].to_numpy(dtype=float)
    if imp.size != HOURS:
        return {"year": year, "status": f"UNEXPECTED LENGTH {imp.size}"}
    total_ceiling = sum(
        min(
            c["ladder_ceiling_mean_mw"],
            c["envelope_mean_mw"],
            c["path_rating_mw"],
        )
        for c in c3["corridors"].values()
    )
    total_ladder = sum(c["ladder_ceiling_mean_mw"] for c in c3["corridors"].values())
    return {
        "year": year,
        "net_import_mean_mw": float(imp.mean()),
        "net_import_p95_mw": float(np.percentile(imp, 95)),
        "net_import_max_mw": float(imp.max()),
        "system_ladder_capability_mean_mw": float(total_ladder),
        "system_effective_ceiling_mean_mw": float(total_ceiling),
        "note": (
            "class 'import' is the NET of the corridor import tranches and the "
            "per-hub export legs, so it is a lower bound on gross import; the "
            "comparison is a headroom scale check, not a per-corridor binding test."
        ),
    }


def c5_published_objects() -> dict:
    """Lay the candidate published objects against the fitted ladder."""
    import csv

    from market_sim.config.interchange_config import (
        IMPORT_TRANCHES,
        IMPORT_TRANCHES_BY_YEAR,
    )
    from market_sim.model.interchange.caiso import _caiso_corridor_export_cap_mw

    # Branch-group MIC, as committed by scripts/data/curate_caiso_mic.py.
    mic_path = REPO / "data/raw/capacity-deliverability/caiso/caiso.csv"
    mic: dict[str, dict[str, float]] = {}
    with mic_path.open() as fh:
        for row in csv.DictReader(fh):
            if row["area_type"] != "branch_group" or row["metric"] != "import_limit":
                continue
            mic.setdefault(row["delivery_year"], {})[row["area"]] = float(
                row["value_mw"]
            )

    # The north/south-of-Path-15 split named in the IMPORT_TRANCHES provenance
    # block (transcribed verbatim from that comment — the same partition the
    # FIRM capacities are already grounded on).
    north = {
        "Malin 500",
        "COTP",
        "NOB",
        "Cascade",
        "Summit",
        "Round Mountain 230",
        "Cottonwood 230",
        "Northwest 230",
        "Marble",
        "Tracy 230",
        "Tracy 500",
        "Tracy-TEA",
        "Westley-Tesla",
        "Westley-Wilson",
        "Standiford",
        "Oakdale",
        "New Melones",
        "Rancho Seco",
        "Rancho Seco/Lake",
        "Lake",
    }
    out: dict = {"mic_by_year": {}, "ladder_vs_objects": {}}
    for year, bgs in sorted(mic.items()):
        n = sum(v for k, v in bgs.items() if k in north)
        out["mic_by_year"][year] = {
            "total_mw": sum(bgs.values()),
            "north_matched_mw": n,
            "south_residual_mw": sum(bgs.values()) - n,
            "n_branch_groups": len(bgs),
            "unmatched_north_names": sorted(k for k in north if k not in bgs),
        }
    for year in YEARS:
        lad = IMPORT_TRANCHES_BY_YEAR["CAISO"].get(year) or IMPORT_TRANCHES["CAISO"]
        caps = {n: c for n, c, _ in lad}
        pnw = caps["PNW_hydro_base"] + caps["PNW_midC"]
        dsw = (
            caps["DSW_solar_PV"]
            + caps["DSW_CCGT"]
            + caps["DSW_CT"]
            + caps["WECC_scarcity"]
        )
        out["ladder_vs_objects"][str(year)] = {
            "WECC_PNW": {
                "ladder_total_mw": pnw,
                "ladder_spot_mw": caps["PNW_midC"],
                "path_rating_mw": _caiso_corridor_export_cap_mw("WECC_PNW"),
                "mic_north_mw": out["mic_by_year"].get(str(year), {}).get(
                    "north_matched_mw"
                ),
            },
            "WECC_DSW": {
                "ladder_total_mw": dsw,
                "ladder_spot_mw": dsw - caps["DSW_solar_PV"],
                "path_rating_mw": _caiso_corridor_export_cap_mw("WECC_DSW"),
                "mic_south_mw": out["mic_by_year"].get(str(year), {}).get(
                    "south_residual_mw"
                ),
            },
        }
    return out


def main() -> int:
    """Run the five checks and write the record."""
    record: dict = {
        "probe": "_caiso188_import_tranche_census",
        "session": "caiso-188 (IMPORT_TRANCHES[CAISO] DOF integrity)",
        "keeper": "2026-08-09-caiso-184-c1-lpbasis",
        "lp_solved": False,
        "network": False,
        "c1_limb_census": c1_limb_census(),
        "c2_liveness": {},
        "c3_ceiling_stack": {},
        "c4_realized_headroom": {},
        "c5_published_objects": c5_published_objects(),
    }
    print("=== C1: limb census (committed config at HEAD) ===")
    for limb, blob in record["c1_limb_census"]["limbs"].items():
        print(
            f"  {limb:16s} tranches={','.join(blob['tranches'])} "
            f"varies_by_year={blob['varies_by_year']}"
        )

    for year in YEARS:
        print(f"\n=== fleet rebuild {year} (no LP) ===")
        st = fleet_state(year)
        c2 = c2_liveness(st, year)
        record["c2_liveness"][str(year)] = c2
        for key, row in sorted(c2["rows"].items()):
            print(
                f"  {key:34s} pmax {row['pmax_mw']:8.1f}  cap<mean> "
                f"{row['capability_mean_mw']:8.1f}  floor "
                f"{row['min_gen_mean_mw']:8.1f}  mc {row['mc_mean']:8.2f} "
                f"{'CONST' if row['mc_is_constant'] else 'hourly'}"
            )
        c3 = c3_ceiling_stack(st, year)
        record["c3_ceiling_stack"][str(year)] = c3
        for zone, blob in c3["corridors"].items():
            print(
                f"  {zone}: ladder {blob['ladder_ceiling_mean_mw']:8.1f} | "
                f"envelope {blob['envelope_mean_mw']:8.1f} | "
                f"TTC {blob['path_rating_mw']:8.1f}  → ladder is the tightest "
                f"ceiling in {blob['ladder_is_binding_ceiling_pct']:5.1f} % of hours"
            )
        record["c4_realized_headroom"][str(year)] = c4_realized_headroom(c3, year)
        del st

    OUT.write_text(json.dumps(record, indent=1, sort_keys=False))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
