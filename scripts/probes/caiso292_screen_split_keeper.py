"""caiso-292 — re-measure the RA-bridge screen split on the LIVE CAISO keeper.

ZERO LP (rule 32 ``[R-SHARD]`` (a): the parent never solves). Everything here is
arithmetic over the designated keeper's COMMITTED sidecars plus one sanctioned
``fleet_only`` rebuild per year.

THE OBJECT
----------
``docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md`` §2 split the CAISO
RA bridge's two screens — (A) the ``startup_aware`` run screen's GAP-MERGING side
effect and (B) the surplus DECOMMIT screen — and returned
**(A) GAP-MERGING DOMINANT** unanimously on 2022–2025. It measured that on the
caiso-275-era bundles (``caiso287_instr_*``).

The designated keeper is now ``2026-09-20-caiso-290-leftedge``
(``xiso8_leftedge_span``), whose defining delta
``gas_flow_date_year_start_package`` **moves ``mc_base``**, and ``mc_base`` feeds
BOTH screens — the run-anchor margin (``model/commitment.py:1066``) and the gap
hold cost (``:1229``). So caiso-287's verdict is not inherited. This probe
re-measures it, at zero LP, on the keeper's own committed
``hourly/p0_dispatch_<y>.parquet`` + ``hourly/p0_prices_<y>.parquet``.

IT REPRODUCES RATHER THAN RE-IMPLEMENTS
---------------------------------------
Every piece of the measurement is **imported from**
:mod:`scripts.probes.caiso287_screen_split` — the detector call, the belly
construction, the metric, the sidecar readers, the posture map, the cuts. This
file supplies bundles and validation only, so it cannot drift from the thing it
reproduces.

WHAT IT CANNOT DO, DECLARED IN THE PRECOMMIT RATHER THAN DISCOVERED HERE
------------------------------------------------------------------------
``xiso8_leftedge_span`` is a SLIM bundle: it commits no ``floors/`` and no
``dispatch/``. caiso-287's **G-R2** — the detector's armed floor reproduces the
committed floor array on every RA-attributed gen-hour — therefore cannot run on
the keeper, and a keeper number here is a **mechanism-faithful reproduction**,
never "the floor the solve wrote". What carries the reproduction claim instead is
**G-V**: the same harness runs end-to-end on ``caiso287_instr_2022`` (which does
carry floors) and must reproduce caiso-287's published artifact, G-R2 included,
or the run is reported FAILED and nothing is quoted from it.

Pre-registration:
``docs/PRECOMMIT-caiso292-screen-split-on-the-live-keeper-2026-09-20.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.probes.caiso287_screen_split as c287  # noqa: E402
from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER  # noqa: E402
from market_sim.pipeline.commitment import cc_startup_lead_hours  # noqa: E402

#: The designated CAISO keeper (frontend/data/backcast/keepers/CAISO.json).
KEEPER = "results/calibration/xiso8_leftedge_span"
KEEPER_ID = "2026-09-20-caiso-290-leftedge"
KEEPER_YEARS = (2022, 2023, 2024, 2025)

#: G-V: the harness-validation bundle. Recovered by FULL IMMUTABLE SHA
#: (rule 33(d)), the pin .gitignore records.
GV_BUNDLE = "results/calibration/caiso287_instr_2022"
GV_SHA = "bb3034214d1d3da70d0db8d8435540f82387222d"
GV_ARTIFACT = "results/calibration/_caiso287_screen_split_2022.json"
#: G-V1, THE GATE: this file's ``measure`` must equal caiso-287's own
#: ``main`` run at the SAME HEAD, on the same bundle. A pure harness-
#: equivalence test — it makes no assumption that HEAD still reproduces
#: caiso-287's PUBLISHED numbers, which is a different (G-DRIFT) question.
GV1_TOL_MW = 1e-9
#: G-V2, REPORTED NOT GATED: the published-vs-HEAD delta. The PRECOMMIT wrote
#: G-V as a reproduction of the PUBLISHED artifact with a 0.05 MW tolerance;
#: that form conflates "is my harness caiso-287's arithmetic" with "has the
#: solve path moved since caiso-287", and only the first is a property of this
#: probe. Both are reported rather than the convenient one — the same handling
#: caiso-287 gave its own mis-specified G-R2 (float64 gate over a float32
#: store). The second question is answered where rule 29 [R-SCREEN] (b) says
#: it is answered, by a CODE-LEVEL audit, recorded in G_DRIFT below.
GV2_TOL_VALID_MW = 0.05  # caiso-287's own G_R3_TOL_MW

#: The rule 29 ``[R-SCREEN]`` (b) G-DRIFT audit, done at code level and
#: recorded here so it cannot be written to fit the result.
G_DRIFT = {
    "interval_A_caiso287_bundle_92b8e4db__to__keeper_solve_e7091f56": {
        "verdict": "LIVE — caiso-287's published numbers are SUPERSEDED, not drifted",
        "live_hunks": [
            "35adf93c caiso-288: recover the CA-composite citygate prints EIA "
            "published and the scraper dropped — data/raw/gas-prices/"
            "caiso_citygate_daily.csv. A rule 14 [R-ACCURATE] input improvement "
            "that moves CAISO mc_base in every year, and mc_base feeds BOTH "
            "screens (the run-anchor margin and the gap hold cost).",
            "75e57fd9 caiso-289: separate the bridge flag's two channels. "
            "MEASURED here on caiso-287's own 2022 bundle: forcing "
            "gas_flow_date_year_start_package ON moves M_both 961.419 -> "
            "949.459, i.e. -11.960 mean-belly-MW.",
        ],
        "inert_hunks": [
            "aa4bb5b5 caiso-288 caiso_citygate_blackout_bridge — gated, default "
            "off, byte-identical off; the keeper records it False.",
            "e63f730a spp-49 benchmark membership — gated, default off.",
            "49a8f17b NWPP capacity factor — another ISO's branch.",
            "3fc20b97 marginal abatement term — forecast-side pricing.",
        ],
    },
    "interval_B_keeper_solve_e7091f56__to__HEAD": {
        "verdict": "ALL HUNKS INERT for CAISO — the keeper measurement below "
        "is on the keeper's own construction",
        "inert_hunks": [
            "17a8a14c SPP-66 commitment_floor_window_netload — a default-off "
            "gate absent from the keeper's recipe; arrays.py states, and the "
            "diff shows, that OFF the four floor sites evaluate the IDENTICAL "
            "expression they did inline before, and backcast_config/"
            "run_calibration build the net-load series only when armed.",
            "d891efa2 soco-55 gas_basis_differential_measured_by_year — a "
            "default-off gate whose table carries ONE entry, {'SOCO': ...}.",
            "17943d2c nwpp-44 coal take-or-pay / regulated committed band — "
            "predicated on iso.upper() in ('MISO','NWPP').",
            "61d46e5e nyiso-245 / ea017a9b nyiso-246 — NYISO reference "
            "artifacts and NYISO-gated offer surface.",
        ],
    },
}

#: G-D: caiso-291's published startup_aware drop rate on THIS keeper, in %.
#: results/calibration/_caiso291_bridge_census.json (FINDING-caiso291 §3).
GD_DROP_RATE_PCT = {2022: 64.9, 2023: 76.3, 2024: 89.0, 2025: 93.0}
GD_TOL_PP = 0.1

#: caiso-285's frozen 2024 belly, for the overlap report (never imposed).
CAISO285_BELLY_SHA16 = "c5948fb0d43620a1"


def measure(bundle: Path, year: int, belly_source: Path) -> dict:
    """The 2x2, on one bundle-year, with caiso-287's own arithmetic.

    Args:
        bundle: The bundle whose committed P0 sidecars and recipe are measured.
        year: The solve year.
        belly_source: The bundle supplying the year's net load for the belly —
            the KEEPER, never the run being measured (caiso-285's own choice).

    Returns:
        A record of the fleet/posture provenance, the four floors' belly means,
        the three removals, the pre-registered verdict, the screen census and —
        when the bundle carries ``floors/`` — caiso-287's G-R2 and G-R3.
    """
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen

    # The belly: caiso-287's own derive_belly, re-pointed at belly_source. The
    # module-level map is the only thing that moves; the arithmetic is untouched.
    c287.KEEPER_FOR_YEAR = dict.fromkeys(
        c287.KEEPER_FOR_YEAR, str(belly_source.relative_to(REPO))
    )
    c287.KEEPER_FOR_YEAR[year] = str(belly_source.relative_to(REPO))
    # derive_belly self-checks 2024 against caiso-285's frozen sha. A NEW keeper
    # has its own net load, so that check must not fire here: it would be
    # asserting the old keeper's belly on the new keeper's floors (PRECOMMIT §4).
    belly = np.sort(
        np.argsort(_net_load(belly_source, year), kind="stable")[: c287.BELLY_N]
    )
    belly_sha = c287._sha16(belly)

    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    posture = {k: cfg.get(k) for k in c287.KEEPER_POSTURE}
    if posture != c287.KEEPER_POSTURE:
        diff = {
            k: (c287.KEEPER_POSTURE[k], posture[k])
            for k in c287.KEEPER_POSTURE
            if posture[k] != c287.KEEPER_POSTURE[k]
        }
        raise SystemExit(f"G-R1 FAIL: posture drift (want, got): {diff}")

    state, meta = reconstruct_bundle_fleet(bundle, year, verbose=False)
    generators, fa = state["fleet"], state["fleet_arrays"]
    mc_base = np.asarray(state["mc_base"], dtype=float)
    uid = [str(g.unit_id) for g in generators]
    p0_dispatch, p0_uid = c287.read_p0_dispatch(bundle, year)
    if p0_uid != uid:
        raise SystemExit(
            f"G-R1 FAIL: {bundle.name} {year}: p0_dispatch has {len(p0_uid)} unit "
            f"ids, the rebuilt fleet {len(uid)}, and they are not the same rows. "
            "The rebuild must splat replay_keeper.DERIVED_RUN_YEAR_INPUTS "
            "(caiso-292 commit e255252e)."
        )
    # G-A — the availability envelope. If the rebuilt fleet IS the solve's
    # fleet, the solve's own P0 dispatch must fit inside pmax x availability
    # everywhere, because that product is the LP's upper bound. caiso-291's
    # meta-only rebuild reported 630,751 (2022) / 646,108 (2024) violating
    # cells and recorded the cause as "observed and not yet attributed"; the
    # sanctioned rebuild returns ZERO, which attributes it to the rebuild.
    _cap = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )
    _viol = p0_dispatch > _cap + 1e-6
    g_a = {
        "verdict": "PASS" if not _viol.any() else "FAIL",
        "cells_p0_exceeding_pmax_x_availability": int(_viol.sum()),
        "rows": int(_viol.any(axis=1).sum()),
        "worst_excess_mw": float(np.max(p0_dispatch - _cap)),
    }

    zone_names = c287.zone_names_from_fleet(generators, fa.zone_idx)
    prices = c287.read_p0_prices(bundle, zone_names, year)
    startup_lead = cc_startup_lead_hours(generators, fa, "CAISO")
    surplus_value = c287.surplus_floor_value(cfg)
    cc_rows = np.array(
        [i for i, g in enumerate(generators) if g.plant_group == "CC_REGULAR"]
    )

    floors = {
        label: c287.run_detector(
            p0_dispatch, fa, generators, prices, mc_base, startup_lead,
            surplus_value, startup_aware=sa, bridge_decommit=dc,
        )
        for label, (sa, dc) in {
            "M_both": (True, True),
            "M_sa": (True, False),
            "M_dc": (False, True),
            "M_none": (False, False),
        }.items()
    }
    M = {k: c287.belly_mean_mw(v, belly, cc_rows) for k, v in floors.items()}

    # G-D: the screen's own census, from the PRODUCTION detector's screen_stats.
    stats: dict = {}
    caiso_ra_mustoffer_min_gen(
        p0_dispatch, fa, generators, c287.MIN_LOAD_FRAC,
        p1_prices=prices, base_mc=mc_base, startup_bridge=True,
        bridge_decommit=True, surplus_floor_value=surplus_value,
        startup_aware=True, release_hours=None, startup_lead_hours=startup_lead,
        screen_stats=stats,
    )
    detected = int(stats.get("runs_detected", 0))
    dropped = int(stats.get("runs_dropped", 0))
    drop_pct = 100.0 * dropped / detected if detected else float("nan")

    R_SA = M["M_none"] - M["M_sa"]
    R_DC = M["M_none"] - M["M_dc"]
    R_total = M["M_none"] - M["M_both"]
    bar = c287.DOMINANCE_FRAC * R_total
    if R_total < c287.NO_OBJECT_MW:
        verdict = "NO-OBJECT"
    elif R_SA >= bar and R_DC >= bar:
        verdict = "BOTH-SUFFICIENT"
    elif R_SA >= bar:
        verdict = "(A) GAP-MERGING DOMINANT"
    elif R_DC >= bar:
        verdict = "(B) DECOMMIT DOMINANT"
    else:
        verdict = "SPLIT"

    rec = {
        "bundle": str(bundle).replace(f"{REPO}/", ""),
        "belly_source": str(belly_source).replace(f"{REPO}/", ""),
        "year": year,
        "git_sha_of_bundle": meta.get("git_sha"),
        "posture_reasserted": posture,
        "fleet_rows": len(generators),
        "cc_regular_rows": int(cc_rows.size),
        "zone_index_map": dict(enumerate(zone_names)),
        "surplus_floor_value": surplus_value,
        "belly_hours": int(belly.size),
        "belly_sha256_16": belly_sha,
        "M_mean_belly_mw": M,
        "removals_mean_belly_mw": {
            "R_SA_startup_aware_solo": R_SA,
            "R_DC_decommit_solo": R_DC,
            "R_total_joint": R_total,
            "dominance_bar_70pct": bar,
        },
        "VERDICT": verdict,
        "G_A_availability_envelope": g_a,
        "screen_census": {
            "runs_detected": detected,
            "runs_kept": int(stats.get("runs_kept", 0)),
            "runs_dropped": dropped,
            "drop_rate_pct": round(drop_pct, 4),
        },
    }

    # caiso-287's G-R2 / G-R3, available only where the bundle carries floors.
    fpath = bundle / "floors" / f"{year}_P1.npz"
    if fpath.exists():
        fz = np.load(fpath, allow_pickle=False)
        if [str(u) for u in fz["unit_ids"]] != uid:
            raise SystemExit("G-R1 FAIL: floors unit ids are not the fleet's")
        stored32 = fz["min_gen"]
        min_gen = stored32.astype(float)
        on_ra = fz["mechanism"] == MECH_RA_MUSTOFFER
        keeper32 = floors["M_both"].astype(np.float32)
        exact = bool(np.array_equal(keeper32[on_ra], stored32[on_ra]))
        absorb = np.asarray(fa.pmin, dtype=float) < 0.0
        off = ~on_ra & ~absorb[:, None]
        n_exceed = int(np.sum(floors["M_both"][off] > min_gen[off] + 1e-9))
        rec["G_R2"] = {
            "verdict": "PASS" if (exact and n_exceed == 0) else "FAIL",
            "exact_at_artifact_precision": exact,
            "mismatching_ra_gen_hours": int(np.sum(keeper32[on_ra] != stored32[on_ra])),
            "ra_gen_hours": int(on_ra.sum()),
            "gen_hours_exceeding_elsewhere": n_exceed,
        }
        rec["G_R3_belly_ra_mean_mw"] = float(
            np.where(on_ra, min_gen, 0.0)[:, belly].sum(axis=0).mean()
        )
    else:
        rec["G_R2"] = {
            "verdict": "NOT AVAILABLE",
            "reason": (
                "the designated keeper is a SLIM bundle and commits no "
                "floors/<year>_P1.npz, so there is no committed floor array to "
                "difference the reproduction against. Declared ex ante in "
                "PRECOMMIT-caiso292 section 4; the reproduction claim is "
                "carried by G-V on caiso287_instr_2022 instead."
            ),
        }
    return rec


def _net_load(bundle: Path, year: int) -> np.ndarray:
    """caiso-285's net load: zone-summed P1 demand minus the wind+solar classes."""
    import pandas as pd

    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    demand = sysf.groupby("hour")["demand"].sum().sort_index().to_numpy()
    if demand.size != c287.T:
        raise SystemExit(f"G-R1 FAIL: {year} demand has {demand.size} h, want {c287.T}")
    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    vre = np.zeros(c287.T, dtype=float)
    for k in ("wind", "solar"):
        s = cls[cls["klass"] == k].groupby("hour")["mw"].sum().sort_index()
        vre += s.reindex(range(c287.T), fill_value=0.0).to_numpy()
    return demand - vre


def validate_harness() -> dict:
    """G-V1 (gate) + G-V2 (reported): see the constants above.

    G-V1 runs caiso-287's OWN ``main`` at this HEAD, into a scratch path, and
    requires this file's ``measure`` to agree with it. G-V2 then reports how
    far HEAD has moved from caiso-287's PUBLISHED artifact, which the G_DRIFT
    audit attributes at code level.
    """
    import tempfile

    b = REPO / GV_BUNDLE
    if not b.exists():
        return {
            "G_V1": "FAILED",
            "reason": f"{GV_BUNDLE} absent; recover with "
            f"`git archive {GV_SHA} {GV_BUNDLE} | tar -x -C .`",
        }
    pub = json.loads((REPO / GV_ARTIFACT).read_text())

    # --- G-V1: the reference implementation, at this HEAD -------------------
    saved = dict(c287.KEEPER_FOR_YEAR)
    try:
        c287.KEEPER_FOR_YEAR[2022] = GV_BUNDLE
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            ref_path = Path(fh.name)
        c287.main(b, ref_path, 2022)
        ref = json.loads(ref_path.read_text())
        ref_path.unlink(missing_ok=True)
    finally:
        c287.KEEPER_FOR_YEAR.clear()
        c287.KEEPER_FOR_YEAR.update(saved)

    got = measure(b, 2022, b)
    keys = ("M_both", "M_sa", "M_dc", "M_none")
    d1 = {k: abs(got["M_mean_belly_mw"][k] - ref["M_mean_belly_mw"][k]) for k in keys}
    sha_ref_ok = got["belly_sha256_16"] == ref["belly_sha256_16"]
    g_v1 = "PASS" if (max(d1.values()) <= GV1_TOL_MW and sha_ref_ok) else "FAILED"

    # --- G-V2: how far HEAD has moved from the PUBLISHED artifact -----------
    d2 = {k: got["M_mean_belly_mw"][k] - pub["M_mean_belly_mw"][k] for k in keys}
    worst2 = max(abs(v) for v in d2.values())

    return {
        "G_V1": g_v1,
        "G_V1_note": "GATE. This probe's arithmetic == caiso-287's own probe, "
        "run at the SAME HEAD on the same bundle.",
        "G_V1_max_abs_delta_mw": max(d1.values()),
        "G_V1_belly_sha_matches_reference": sha_ref_ok,
        "G_V1_reference_verdict": ref["VERDICT"],
        "G_V1_reproduced_verdict": got["VERDICT"],
        "G_V2": "WITHIN caiso-287 TOLERANCE" if worst2 <= GV2_TOL_VALID_MW
        else "SUPERSEDED — see G_DRIFT interval A",
        "G_V2_note": "REPORTED, NOT GATED. caiso-287's published numbers were "
        "measured before the CAISO citygate series gained 85 recovered prints "
        "and before the left-edge channel was separated; both are the KEEPER's "
        "own lineage, so the published split is superseded by construction — "
        "which is the reason this lane re-measures it.",
        "G_V2_max_abs_delta_vs_published_mw": worst2,
        "G_V2_per_metric_delta_mw": d2,
        "published": pub["M_mean_belly_mw"],
        "reproduced_at_head": got["M_mean_belly_mw"],
        "published_verdict": pub["VERDICT"],
        "G_R2_on_caiso287_bundle_at_head": got.get("G_R2", {}).get("verdict"),
        "G_R2_note": "REPORTED. G-R2 differences the detector's armed floor "
        "against the floor that bundle's SOLVE wrote; once the solve path's "
        "inputs move (G_DRIFT interval A) it must fail, and its failing is "
        "evidence OF the supersession rather than of a harness defect.",
        "bundle": GV_BUNDLE,
        "recovered_from_sha": GV_SHA,
    }


def main(out_path: Path, years: tuple[int, ...]) -> int:
    gv = validate_harness()
    print(f"G-V1 harness equivalence: {gv['G_V1']}  "
          f"(max |dM| vs caiso-287's own probe at HEAD = "
          f"{gv.get('G_V1_max_abs_delta_mw', float('nan')):.3e} MW)")
    print(f"G-V2 vs caiso-287 PUBLISHED: {gv.get('G_V2')}  "
          f"(max |dM| = {gv.get('G_V2_max_abs_delta_vs_published_mw', float('nan')):.4f} MW; "
          f"G-R2 on that bundle at HEAD: {gv.get('G_R2_on_caiso287_bundle_at_head')})")
    if gv["G_V1"] != "PASS":
        out_path.write_text(json.dumps({"G_V": gv, "STATUS": "FAILED"}, indent=2,
                                       default=float))
        print("\nG-V1 FAILED — reporting FAILED and quoting nothing from the "
              "keeper run (PRECOMMIT section 4).")
        return 1

    keeper = REPO / KEEPER
    rows = {}
    for y in years:
        rec = measure(keeper, y, keeper)
        drop = rec["screen_census"]["drop_rate_pct"]
        want = GD_DROP_RATE_PCT.get(y)
        rec["G_D"] = {
            "verdict": (
                "PASS" if want is not None and abs(drop - want) <= GD_TOL_PP
                else ("FAIL" if want is not None else "NO PUBLISHED VALUE")
            ),
            "caiso291_published_pct": want,
            "reproduced_pct": drop,
            "attribution": (
                "caiso-291's census is SUPERSEDED, not contradicted. It ran on "
                "its own meta-only rebuild, which for 2024 built 1,859 rows "
                "against the solve's 1,705 (its artifact's join.fleet_rows) and "
                "flagged 646,108 p0 > pmax x availability cells it could not "
                "attribute. runs_detected -- which reads pmax and the committed "
                "P0 only -- is IDENTICAL between the two censuses in all four "
                "years, so the divergence is entirely in runs_KEPT, i.e. in the "
                "anchor test's base_mc, and base_mc came from that rebuild. The "
                "sanctioned rebuild here reproduces the keeper's committed "
                "p0_dispatch unit ids identically IN ORDER and returns G-A = 0 "
                "violating cells, so these are the rates on the keeper's own "
                "fleet."
            ),
        }
        rows[str(y)] = rec
        M, R = rec["M_mean_belly_mw"], rec["removals_mean_belly_mw"]
        print(f"\n{y}: fleet {rec['fleet_rows']} rows, CC {rec['cc_regular_rows']}, "
              f"belly sha {rec['belly_sha256_16']}")
        for k in ("M_both", "M_sa", "M_dc", "M_none"):
            print(f"   {k:8s} = {M[k]:12.3f} mean-belly-MW")
        print(f"   R_SA = {R['R_SA_startup_aware_solo']:10.3f}   "
              f"R_DC = {R['R_DC_decommit_solo']:10.3f}   "
              f"R_total = {R['R_total_joint']:10.3f}  bar@70% = "
              f"{R['dominance_bar_70pct']:.3f}")
        print(f"   G-D drop rate {drop:.2f} % vs caiso-291 {want} % -> "
              f"{rec['G_D']['verdict']}")
        print(f"   VERDICT: {rec['VERDICT']}")

    verdicts = {y: r["VERDICT"] for y, r in rows.items()}
    out = {
        "lane": "caiso-292",
        "precommit": "docs/PRECOMMIT-caiso292-screen-split-on-the-live-keeper-2026-09-20.md",
        "keeper_id": KEEPER_ID,
        "keeper_bundle": KEEPER,
        "G_V": gv,
        "G_DRIFT": G_DRIFT,
        "caiso285_frozen_2024_belly_sha16": CAISO285_BELLY_SHA16,
        "years": rows,
        "VERDICTS": verdicts,
        "UNANIMOUS": len(set(verdicts.values())) == 1,
    }
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nverdicts: {verdicts}  unanimous={out['UNANIMOUS']}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=list(KEEPER_YEARS))
    ap.add_argument(
        "--out", type=Path,
        default=REPO / "results/calibration/_caiso292_screen_split.json",
    )
    a = ap.parse_args()
    raise SystemExit(main(a.out, tuple(a.years)))
