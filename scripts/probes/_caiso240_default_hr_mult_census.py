"""caiso-240 — the CENSUS of ``campd_bins._DEFAULT_HR_MULT_BY_GROUP``: which LP
units, in which ISOs, each of the 28 uncited class heat-rate multipliers actually
prices, measured on each ISO's OWN designated keeper.

NO LP, NO SOLVE. Every input is committed: each keeper bundle's ``meta.json`` +
``run_config.json`` + ``hourly/`` sidecars, the committed CAMPD marginal-HR
reference artifacts, and the caiso-105/121/131 ``run_year(fleet_only=True)``
offer reconstruction (assembles the fleet, availability and the P0 objective;
builds no matrix, calls no solver). The rebuild harness is the caiso-239
``_caiso239_st_gas_committed_footprint.py`` form; the marginal-rung attribution
and the §H bounding form come from ``_caiso230_abovefloor_decomposition.py``.

PRE-REGISTERED IN ``PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md``
(pushed to origin before this file was run). The method, its two falsifiers, the
grading taxonomy and the predictions are fixed there.

WHAT THIS MEASURES.

  M-1  NULL PASS — a baseline->baseline rebuild is byte-identical in every row.
  M-2  TWO-POINT VALIDATION — on the caiso-231 predecessor recipe the
       ``ST_GAS.mc`` cell is responsive on exactly the 3 tranches caiso-239
       measured (plants 315 / 335 / 350); on the caiso-239 keeper the SAME cell
       is responsive on ZERO tranches, because ``caiso_st_gas_committed_measured``
       retired it.
  C-1  FOOTPRINT — per (ISO, group, band): which LP tranches the cell prices, at
       what capacity, on that ISO's own keeper, in each of 2023 / 2024 / 2025.
       Established by rebuilding the offer surface with EVERY one of the 28
       cells scaled by its OWN unique factor and reading each row's heat-rate
       ratio back: the ratio IDENTIFIES the cell, so attribution is measured,
       never inferred from a row's group or name.
  C-2  MATERIALITY — available capacity-hours and distinct plants per live cell.
  C-3  COUNTERPART — the population-matched measured candidate for each live
       cell, from ``data/raw/reference/<iso>_campd_marginal_hr_summary.csv``.
  C-4  ADVERSE BOUND — the first-order C3a bound of moving each live CAISO cell
       to its counterpart, caiso-230 §H form on the caiso-239 keeper, reported
       under BOTH the full CAISO estimator (with import legs) and the
       ISO-agnostic fleet-rung-only variant, so the variant's bias is visible.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso240_default_hr_mult_census.py
    (optional) --isos CAISO PJM ...   --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import inspect
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

HOURS = 8760
YEARS = (2023, 2024, 2025)

#: Each ISO's DESIGNATED keeper (frontend/data/backcast/keepers/<ISO>.json) and
#: its committed bundle. Rule 25 [R-ISO-SCOPE]: every measurement for an ISO is
#: taken on THAT ISO's own keeper; nothing is transferred between them.
KEEPERS: dict[str, tuple[str, str]] = {
    "ERCOT": (
        "2026-08-25-234-eastex-identity",
        "results/calibration/ercot234_eastex_identity",
    ),
    "PJM": (
        "2026-08-15-pjm-162-inputclock",
        "results/calibration/pjm_debugb_inputclock_A",
    ),
    "CAISO": (
        "2026-09-02-caiso-239-b1-stgas",
        "results/calibration/caiso239_b1_stgas_committed_measured",
    ),
    "NYISO": (
        "2026-09-02-nyiso-177-vintage-matched",
        "results/calibration/nyiso177_vintage_B1p",
    ),
    "NEISO": ("2026-08-17-neiso-99-joint-p1", "results/calibration/neiso99_joint_B"),
    "MISO": ("2026-09-02-miso-201-stbasis", "results/calibration/miso201_stbasis_B"),
}

#: The caiso-231 predecessor recipe, used ONLY by the M-2 two-point validation.
CAISO_PRIOR = (
    "2026-09-01-caiso-231-b1-ungrounded",
    "results/calibration/caiso231_b1_ungrounded",
)

GROUPS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "COAL")
BANDS = ("mr", "mc", "econ", "peak")
CELLS: list[tuple[str, str]] = [(g, b) for g in GROUPS for b in BANDS]

#: Unique per-cell probe factor. Spaced 1e-4 apart so a rebuilt row's heat-rate
#: ratio identifies its cell UNIQUELY and EXACTLY (float64 resolves 1e-4 spacing
#: with ~12 orders of margin), and small enough that no band ordering, clip or
#: merit-order position can flip -- the perturbation is a MEASUREMENT INSTRUMENT,
#: not a candidate value.
FACTORS: dict[tuple[str, str], float] = {
    c: 1.0 + (i + 1) * 1e-4 for i, c in enumerate(CELLS)
}
#: Second, LARGE uniform pass. A cell live here but dead at the small factor is
#: reported as CLIP-SUPPRESSED, never silently merged (PRECOMMIT §3.2).
BIG_FACTOR = 1.25

OUT = REPO / "results/calibration/_caiso240_default_hr_mult_census.json"
HR_SUMMARY = REPO / "data/raw/reference/{iso}_campd_marginal_hr_summary.csv"


#: Tranche-suffix -> band. The ``bins_to_fleet`` vocabulary (assembly.py):
#: mustrun/sync take ``hr_mr``; committed*/commitcyc take ``hr_mc``; econ* take
#: the econ tranche(s); peak* take ``hr_peak``. Used for REPORTING only -- the
#: cell attribution itself comes from the measured ratio.
def band_of(uid: str) -> str:
    tag = uid.split("_")[-1]
    if tag in ("mustrun", "sync"):
        return "mr"
    if tag.startswith("committed") or tag.startswith("commitcyc"):
        return "mc"
    if tag.startswith("econ"):
        return "econ"
    if tag.startswith("peak"):
        return "peak"
    return tag


# ---------------------------------------------------------------------------
# Rebuild harness
# ---------------------------------------------------------------------------


def _clear_fleet_caches() -> None:
    """Drop every cache that would defeat an in-place literal mutation.

    ``campd_bins._CAMPD_BINS_CACHE`` memoizes the ERCOT curated-CSV bin frame
    (site A) on (csv_path, year, reconcile_path) -- a key that does not see the
    literals -- and several loaders in the same module are ``lru_cache``d. Both
    are cleared between passes. PRECOMMIT §3.3 declares this hazard and the M-1
    null pass is its falsifier.
    """
    from market_sim.data.fleet import campd_bins as cb

    cb._CAMPD_BINS_CACHE.clear()
    for mod in (cb,):
        for name in dir(mod):
            fn = getattr(mod, name, None)
            if callable(fn) and hasattr(fn, "cache_clear"):
                fn.cache_clear()


def rebuild(
    bundle: Path, year: int, mutation: dict[tuple[str, str], float] | None
) -> dict:
    """Rebuild one keeper's offer surface, optionally with the literals scaled.

    ``mutation`` maps (group, band) -> multiplicative factor applied IN PLACE to
    ``campd_bins._DEFAULT_HR_MULT_BY_GROUP``; the dict is restored before
    returning, so the process-global literal table is never left perturbed.
    """
    from market_sim.data.fleet import campd_bins as cb
    from run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
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
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}

    original = {g: dict(v) for g, v in cb._DEFAULT_HR_MULT_BY_GROUP.items()}
    try:
        if mutation:
            for (g, b), f in mutation.items():
                if g in cb._DEFAULT_HR_MULT_BY_GROUP:
                    cb._DEFAULT_HR_MULT_BY_GROUP[g][b] *= f
        _clear_fleet_caches()
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            st = run_year(
                year,
                meta["iso"],
                HOURS,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kwargs,
            )
    finally:
        for g, v in original.items():
            cb._DEFAULT_HR_MULT_BY_GROUP[g] = dict(v)
        _clear_fleet_caches()

    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    pg = getattr(fa, "plant_group", None)
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "hr": np.asarray(fa.heat_rate, dtype=float),
        "mc": mc,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": avail,
        "plant_code": np.asarray(fa.plant_code, dtype=int),
        "group": (
            np.array([str(g) for g in np.asarray(pg)])
            if pg is not None
            else np.array([""] * len(fa.unit_ids))
        ),
        "zone_idx": np.asarray(fa.zone_idx, dtype=int),
    }


def attribute(base: dict, arm: dict, factors: dict[tuple[str, str], float]) -> dict:
    """Map every responsive row to the CELL that prices it, by measured ratio.

    Returns ``{cell_key: [row indices]}`` for rows whose heat-rate ratio equals a
    cell's own probe factor exactly, plus ``_indirect`` for rows that moved at
    some OTHER ratio (a downstream interaction, reported separately and never
    counted as a cell's footprint) and ``_rowset`` diagnostics.
    """
    out: dict[str, list[int]] = {}
    if base["uid"].shape != arm["uid"].shape or not np.array_equal(
        base["uid"], arm["uid"]
    ):
        common = np.intersect1d(base["uid"], arm["uid"])
        out["_rowset_mismatch"] = [
            int(len(base["uid"])),
            int(len(arm["uid"])),
            int(len(common)),
        ]
        return out
    ratio = np.divide(
        arm["hr"], base["hr"], out=np.ones_like(base["hr"]), where=base["hr"] > 0
    )
    inv = {round(f, 12): c for c, f in factors.items()}
    moved = np.flatnonzero(np.abs(ratio - 1.0) > 1e-12)
    indirect: list[int] = []
    for i in moved:
        cell = inv.get(round(float(ratio[i]), 12))
        if cell is None:
            # tolerate float noise: nearest factor within 1e-9
            cand = min(factors.items(), key=lambda kv: abs(kv[1] - float(ratio[i])))
            if abs(cand[1] - float(ratio[i])) < 1e-9:
                cell = cand[0]
        if cell is None:
            indirect.append(int(i))
        else:
            out.setdefault(f"{cell[0]}:{cell[1]}", []).append(int(i))
    if indirect:
        out["_indirect"] = indirect
    return out


def row_stats(d: dict, idx: list[int]) -> dict:
    """Materiality of a set of rows on the rebuilt fleet."""
    if not idx:
        return {"n_tranches": 0, "pmax_mw": 0.0, "available_gwh": 0.0, "plants": []}
    ii = np.asarray(idx, dtype=int)
    cap_mwh = float((d["pmax"][ii, None] * d["avail"][ii]).sum())
    plants = sorted({int(p) for p in d["plant_code"][ii] if int(p) > 0})
    return {
        "n_tranches": int(ii.size),
        "pmax_mw": round(float(d["pmax"][ii].sum()), 1),
        "available_gwh": round(cap_mwh / 1000.0, 1),
        "avail_mean": round(float(d["avail"][ii].mean()), 4),
        "n_plants": len(plants),
        "plants": plants[:40],
        "bands_seen": sorted({band_of(str(u)) for u in d["uid"][ii]}),
        "groups_seen": sorted({str(g) for g in d["group"][ii] if str(g)}),
        "uids": [str(u) for u in d["uid"][ii]][:60],
    }


# ---------------------------------------------------------------------------
# M-1 / M-2 — the two pre-registered method falsifiers
# ---------------------------------------------------------------------------


def method_checks(years) -> dict:
    print("=" * 78)
    print("M-1 / M-2 — PRE-REGISTERED METHOD FALSIFIERS (PRECOMMIT §3.3)")
    print("=" * 78)
    out: dict = {}

    y = years[0]
    kb = REPO / KEEPERS["CAISO"][1]
    a = rebuild(kb, y, None)
    b = rebuild(kb, y, None)
    same = (
        np.array_equal(a["uid"], b["uid"])
        and np.array_equal(a["hr"], b["hr"])
        and np.array_equal(a["mc"], b["mc"])
    )
    print(
        f"  M-1 null pass  ({y}, CAISO keeper): "
        f"{'PASS — byte-identical' if same else 'FAIL — rows moved'}"
    )
    out["M1_null_pass"] = {
        "year": y,
        "identical": bool(same),
        "n_rows": int(a["uid"].size),
    }

    # M-2: the ST_GAS.mc cell alone, on both recipes.
    m2: dict = {}
    for label, (run_id, bdir) in (
        ("caiso231_prior", CAISO_PRIOR),
        ("caiso239_keeper", KEEPERS["CAISO"]),
    ):
        bp = REPO / bdir
        per_year = {}
        for yy in years:
            base = rebuild(bp, yy, None)
            arm = rebuild(bp, yy, {("ST_GAS", "mc"): FACTORS[("ST_GAS", "mc")]})
            hits = attribute(base, arm, {("ST_GAS", "mc"): FACTORS[("ST_GAS", "mc")]})
            idx = hits.get("ST_GAS:mc", [])
            st = row_stats(base, idx)
            per_year[str(yy)] = {
                "n_responsive": st["n_tranches"],
                "plants": st["plants"],
                "uids": [str(u) for u in base["uid"][np.asarray(idx, dtype=int)]]
                if idx
                else [],
                "indirect": len(hits.get("_indirect", [])),
            }
            print(
                f"  M-2 {label:<16} {yy}: ST_GAS.mc responsive tranches = "
                f"{st['n_tranches']}  plants={st['plants']}"
            )
        m2[label] = {"run_id": run_id, "bundle": bdir, "per_year": per_year}
    out["M2_two_point"] = m2
    prior_ok = all(
        v["n_responsive"] == 3 for v in m2["caiso231_prior"]["per_year"].values()
    )
    keeper_ok = all(
        v["n_responsive"] == 0 for v in m2["caiso239_keeper"]["per_year"].values()
    )
    out["M2_verdict"] = {
        "prior_is_3_in_every_year": bool(prior_ok),
        "keeper_is_0_in_every_year": bool(keeper_ok),
        "PASS": bool(prior_ok and keeper_ok),
    }
    print(
        f"  M-2 verdict: prior==3 {prior_ok}, keeper==0 {keeper_ok} -> "
        f"{'PASS' if prior_ok and keeper_ok else 'FAIL'}"
    )
    return out


# ---------------------------------------------------------------------------
# C-1 / C-2 — the census proper
# ---------------------------------------------------------------------------


def census(isos, years) -> dict:
    print("\n" + "=" * 78)
    print("C-1 / C-2 — the 28-cell FOOTPRINT census, per ISO, per year")
    print("=" * 78)
    out: dict = {}
    for iso in isos:
        run_id, bdir = KEEPERS[iso]
        bp = REPO / bdir
        print(f"\n### {iso}  keeper {run_id}")
        per_year: dict = {}
        for year in years:
            t0 = time.time()
            base = rebuild(bp, year, None)
            arm_small = rebuild(bp, year, FACTORS)
            big = {c: BIG_FACTOR for c in CELLS}
            arm_big = rebuild(bp, year, big)
            hits = attribute(base, arm_small, FACTORS)
            # the large pass can only be attributed by band/group (one factor),
            # so it is used ONLY as a liveness cross-check per row.
            big_moved = set()
            if base["uid"].shape == arm_big["uid"].shape and np.array_equal(
                base["uid"], arm_big["uid"]
            ):
                r = np.divide(
                    arm_big["hr"],
                    base["hr"],
                    out=np.ones_like(base["hr"]),
                    where=base["hr"] > 0,
                )
                big_moved = {int(i) for i in np.flatnonzero(np.abs(r - 1.0) > 1e-12)}
            # Heat-rate response is STRUCTURAL liveness; marginal-cost response
            # is ECONOMIC liveness. They can differ: the coal ``_mustrun``
            # tranche's fuel is sunk under take-or-pay, so its heat rate can move
            # with the literal while its assembled mc does not. A row in the
            # first set but not the second is PRICED-BUT-INERT and is reported as
            # its own category, never counted as a live economic footprint.
            mc_moved: set[int] = set()
            if base["mc"].shape == arm_big["mc"].shape:
                dmc = np.abs(arm_big["mc"] - base["mc"]).max(axis=1)
                mc_moved = {int(i) for i in np.flatnonzero(dmc > 1e-9)}
            cells: dict = {}
            for cell in CELLS:
                key = f"{cell[0]}:{cell[1]}"
                idx = hits.get(key, [])
                st = row_stats(base, idx)
                st["n_mc_responsive"] = int(len([i for i in idx if i in mc_moved]))
                st["n_priced_but_inert"] = int(st["n_tranches"] - st["n_mc_responsive"])
                cells[key] = st
            # clip-suppression: rows live at BIG but not attributed at small
            small_rows = {
                i for k, v in hits.items() if not k.startswith("_") for i in v
            }
            clip_only = sorted(big_moved - small_rows)
            n_rows = int(base["uid"].size)
            live = {k: v for k, v in cells.items() if v["n_tranches"] > 0}
            print(
                f"  [{year}] fleet rows {n_rows:>5}   live cells {len(live):>2}/28   "
                f"responsive rows {len(small_rows):>5}   clip-only {len(clip_only)}   "
                f"indirect {len(hits.get('_indirect', []))}   ({time.time() - t0:.0f}s)"
            )
            for k, v in sorted(live.items(), key=lambda kv: -kv[1]["available_gwh"]):
                print(
                    f"       {k:<20} tranches {v['n_tranches']:>5}  "
                    f"mc-live {v['n_mc_responsive']:>5}  "
                    f"pmax {v['pmax_mw']:>9.1f} MW  avail {v['available_gwh']:>10.1f} GWh  "
                    f"plants {v['n_plants']:>4}  bands {','.join(v['bands_seen'])}"
                )
            per_year[str(year)] = {
                "n_fleet_rows": n_rows,
                "n_responsive_rows": len(small_rows),
                "n_live_cells": len(live),
                "clip_only_rows": len(clip_only),
                "indirect_rows": len(hits.get("_indirect", [])),
                "rowset_mismatch": hits.get("_rowset_mismatch"),
                "cells": cells,
            }
        out[iso] = {"run_id": run_id, "bundle": bdir, "per_year": per_year}
    return out


# ---------------------------------------------------------------------------
# C-3 — the population-matched measured counterpart
# ---------------------------------------------------------------------------


def counterparts(isos) -> dict:
    print("\n" + "=" * 78)
    print("C-3 — the committed measured counterpart artifact, per ISO x class")
    print("=" * 78)
    out: dict = {}
    for iso in isos:
        p = Path(str(HR_SUMMARY).format(iso=iso.lower()))
        if not p.exists():
            out[iso] = {"artifact": None}
            print(f"  {iso}: NO ARTIFACT")
            continue
        rows = {}
        for r in csv.DictReader(p.open()):
            rows[r["class"]] = {
                "n_units": int(r["n_units"]),
                "base_hr": float(r["base_hr"]),
                "avg_committed_p25": float(r["avg_committed_p25"]),
                "avg_committed_p50": float(r["avg_committed_p50"]),
                "avg_committed_p75": float(r["avg_committed_p75"]),
                "avg_econ_low_p50": float(r["avg_econ_low_p50"]),
                "avg_econ_high_p50": float(r["avg_econ_high_p50"]),
                "iqr_ratio": round(
                    float(r["avg_committed_p75"]) / float(r["avg_committed_p25"]), 3
                )
                if float(r["avg_committed_p25"])
                else None,
            }
        # POPULATION, where the committed per-unit artifact exists. The
        # caiso-239 F-3 refusal turned on this test -- a counterpart measured on
        # a population DISJOINT from the cell's footprint is refused under rule
        # 14's own representation-boundary exception. The test is performable
        # only where a per-unit artifact is committed; where it is not, the
        # census records NOT ESTABLISHED rather than assuming a match.
        up = (
            REPO
            / f"data/raw/_processed-legacy/campd_gas_commitment_params_{iso}_units.csv"
        )
        pop: dict[str, list[int]] = {}
        if up.exists():
            for r in csv.DictReader(up.open()):
                pop.setdefault(str(r["plant_class"]), []).append(int(r["plant_code"]))
            pop = {k: sorted(set(v)) for k, v in pop.items()}
        out[iso] = {
            "artifact": str(p.relative_to(REPO)),
            "classes": rows,
            "unit_population_artifact": str(up.relative_to(REPO))
            if up.exists()
            else None,
            "measured_plant_population": pop or None,
        }
        print(
            f"  {iso}: classes {sorted(rows)}   population artifact: "
            f"{'YES ' + str({k: len(v) for k, v in pop.items()}) if pop else 'NOT COMMITTED'}"
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--isos", nargs="*", default=list(KEEPERS))
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    ap.add_argument("--skip-method-checks", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    years = tuple(a.years)

    result: dict = {
        "_provenance": {
            "session": "caiso-240",
            "precommit": "results/calibration/PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md",
            "keepers": {k: v[0] for k, v in KEEPERS.items()},
            "years": list(years),
            "cells": [f"{g}:{b}" for g, b in CELLS],
            "probe_factors": {f"{g}:{b}": v for (g, b), v in FACTORS.items()},
            "big_factor": BIG_FACTOR,
            "solves": 0,
        }
    }
    if not a.skip_method_checks:
        result["method_checks"] = method_checks(years)
    result["census"] = census(a.isos, years)
    result["counterparts"] = counterparts(a.isos)

    outp = Path(a.out)
    outp.write_text(json.dumps(result, indent=1, sort_keys=True))
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
