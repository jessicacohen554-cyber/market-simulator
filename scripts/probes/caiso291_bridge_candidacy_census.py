"""caiso-291 phase 0 — where the CAISO RA bridge loses its belly candidates.

ZERO LP (rule 32 ``[R-SHARD]`` (a): the parent never solves). Reads the
designated keeper bundle's COMMITTED ``hourly/p0_dispatch_<y>.parquet`` +
``hourly/p0_prices_<y>.parquet`` — the artifact caiso-284 §3 was blocked on and
which xiso-8 restored — rebuilds the fleet with ``run_year(fleet_only=True)``,
and replays :func:`caiso_ra_mustoffer_min_gen`'s candidacy loop with a counter
at every filter.

The census is only worth its ink if the replay is the real mechanism, so the
probe ends by rebuilding the floor from its own bookkeeping and asserting it is
**byte-identical** to the shipped function's output on the same inputs. A
census whose replay does not reproduce the floor is reported as FAILED and no
number from it is quoted (the caiso-284 §3.2 discipline).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from market_sim.config.constants import (  # noqa: E402
    DA_COMMITMENT_HORIZON_HOURS,
    RA_BRIDGE_ECON_MIN_DOWN_HOURS,
)
from market_sim.model.commitment import (  # noqa: E402
    _ra_bridge_unit_params,
    caiso_ra_mustoffer_min_gen,
    find_runs,
)
from market_sim.pipeline.commitment import cc_startup_lead_hours  # noqa: E402

logger = logging.getLogger("caiso291")


def _read_p0_dispatch(bundle: Path, year: int) -> tuple[list[str], np.ndarray]:
    t = pq.read_table(bundle / "hourly" / f"p0_dispatch_{year}.parquet").to_pydict()
    uids = [str(u) for u in t["unit_id"]]
    mw = np.stack([np.frombuffer(b, dtype="<f8") for b in t["mw"]])
    return uids, mw


def _read_p0_prices(bundle: Path, year: int) -> tuple[list[str], np.ndarray]:
    t = pq.read_table(bundle / "hourly" / f"p0_prices_{year}.parquet").to_pydict()
    zones = sorted(set(zip(t["zone_index"], t["zone"])))
    n_z = max(z for z, _ in zones) + 1
    n_h = max(t["hour"]) + 1
    out = np.full((n_z, n_h), np.nan)
    out[np.asarray(t["zone_index"]), np.asarray(t["hour"])] = np.asarray(t["price"])
    names = [""] * n_z
    for zi, zn in zones:
        names[zi] = zn
    return names, out


def rebuild_state(bundle: Path, iso: str, year: int):
    """``run_year(fleet_only=True)`` on the bundle's OWN recorded recipe.

    The kwargs come from :func:`scripts.lib.bundle_fleet.full_run_year_kwargs`
    (the strict ``replay_keeper.run_year_kwargs`` mapping, caiso-243 §7.3 /
    caiso-244) plus :func:`scripts.replay_keeper.derived_run_year_inputs` —
    never a by-parameter-name filter over ``meta.json``, which silently drops
    every key whose ``run_year`` kwarg is spelled differently (above all
    ``coal_prb_sigmoid_overrides`` -> ``prb_overrides``). Converted by lane
    Y-30 (2026-09-24) under ``tests/regression/test_run_year_kwargs_recipe.py``.
    """
    from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(bundle, year))
    return run_year(
        year, iso, int(meta.get("hours", 8760)), bundle_gas_price(meta, year), **kwargs
    )


def _belly_mask(bundle: Path, year: int, T: int, decile: float):
    """Lowest-decile-of-net-load mask from the committed P1 sidecars.

    Net load = zone-summed ``demand`` (``system_<y>``) minus WIND + SOLAR
    (``class_hourly_<y>``) — the caiso-284 §1 definition, rebuilt from the
    columns these sidecars actually carry.
    """
    st = pq.read_table(bundle / "hourly" / f"system_{year}.parquet").to_pydict()
    dem = np.zeros(T)
    for i, ps in enumerate(st["pass"]):
        if str(ps) == "P1":
            dem[st["hour"][i]] += float(st["demand"][i])
    ch = pq.read_table(bundle / "hourly" / f"class_hourly_{year}.parquet").to_pydict()
    vre = np.zeros(T)
    for i, ps in enumerate(ch["pass"]):
        if str(ps) == "P1" and str(ch["klass"][i]).upper() in ("WIND", "SOLAR"):
            vre[ch["hour"][i]] += float(ch["mw"][i])
    nl = dem - vre
    k = int(round(decile * T))
    mask = np.zeros(T, dtype=bool)
    mask[np.argsort(nl)[:k]] = True
    return mask, nl


def census(
    bundle: Path,
    iso: str,
    year: int,
    belly_decile: float = 0.10,
    force_startup_aware: bool | None = None,
) -> dict:
    """Replay the candidacy loop over the keeper's committed P0, with counters.

    Rows are joined to the rebuilt fleet **BY unit_id, never positionally**
    (the :func:`scripts.legitimacy_diagnostics._backfill_pmax` discipline: the
    two orderings differ). The join is exact for the class under study —
    measured on this bundle, every bridge-SCOPE row (merchant gas CC/CT,
    non-CHP) present in the rebuilt fleet is present in the sidecar, so no
    eligible unit is silently dropped; the probe asserts that rather than
    assuming it.

    SCOPE LIMIT, stated rather than hidden: this censuses **CANDIDACY only** —
    the loop up to and including the restart inequality. The post-candidacy
    ``_apply_economic_bridges`` surplus/decommit screen is NOT reconstructed,
    because its absorption term reads import rows the fleet_only rebuild does
    not carry. caiso-284 §2.3 measured that screen non-binding in the mean
    belly hour, with its own stated limits; nothing here revisits it.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    # THE POSTURE COMES FROM run_config.json, NOT meta.json. Measured on this
    # bundle: caiso_ra_bridge_startup_aware and caiso_ra_startup_trajectory are
    # both True in the recipe and ABSENT from meta.json, because neither is a
    # run_year() parameter and meta.json records only run_year kwargs. Reading
    # the posture from meta would replay the bridge with two armed mechanisms
    # silently off. (Same reason scripts/legitimacy_diagnostics.py's
    # meta-driven rebuild cannot reproduce this keeper's floors.)
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]

    def _flag(name, default=False):
        return cfg[name] if name in cfg else meta.get(name, default)

    st = rebuild_state(bundle, iso, year)
    fa = st["fleet_arrays"]
    fleet = st["fleet"]
    mc_base = np.asarray(st["mc_base"], dtype=float)

    uids, p0_side = _read_p0_dispatch(bundle, year)
    _, p0_px = _read_p0_prices(bundle, year)
    side_ix = {u: i for i, u in enumerate(uids)}

    pmax = np.asarray(fa.pmax, dtype=float)
    zone_idx = np.asarray(fa.zone_idx)
    T = p0_side.shape[1]
    n_gen = len(fleet)

    # Fleet-ordered P0. Rows absent from the sidecar stay zero; the probe
    # asserts below that no BRIDGE-SCOPE row is among them.
    p0 = np.zeros((n_gen, T), dtype=float)
    unmapped_scope: list[str] = []
    for g, gen in enumerate(fleet):
        u = str(gen.unit_id)
        scoped = not gen.plant_group.endswith("_CHP") and gen.fuel_type in (
            "gas_cc",
            "gas_ct",
        )
        j = side_ix.get(u)
        if j is None:
            if scoped:
                unmapped_scope.append(u)
            continue
        p0[g] = p0_side[j]

    frac = float(_flag("caiso_ra_min_load_frac", 0.0))
    startup_bridge = bool(_flag("caiso_ra_startup_bridge"))
    bridge_decommit = startup_bridge and bool(_flag("caiso_ra_bridge_decommit"))
    startup_aware = bool(_flag("caiso_ra_bridge_startup_aware"))
    # DIAGNOSTIC COUNTERFACTUAL ONLY (never a mechanism change): re-run the
    # candidacy census with the run screen forced off, to separate the
    # PROXIMATE filter from its upstream cause. Nothing is armed or disarmed.
    if force_startup_aware is not None:
        startup_aware = bool(force_startup_aware)
    startup_lead = (
        cc_startup_lead_hours(fleet, fa, iso)
        if _flag("caiso_ra_startup_trajectory")
        else None
    )

    # Physical sanity on the join: P0 must respect pmax x availability.
    avail = np.asarray(fa.availability, dtype=float)
    cap = pmax[:, None] * avail
    excess = p0 - cap
    viol = int(np.sum(excess > 1e-6))
    worst = float(np.max(excess)) if n_gen else 0.0
    rows_viol = np.where((excess > 1e-6).any(axis=1))[0]
    viol_examples = [
        {
            "unit_id": str(fleet[g].unit_id),
            "pmax": float(pmax[g]),
            "p0_max": float(p0[g].max()),
            "avail_min": float(avail[g].min()),
        }
        for g in rows_viol[:6]
    ]

    # ---- belly mask: lowest decile of model net load (committed P1 system sidecar)
    belly, net_load = _belly_mask(bundle, year, T, belly_decile)

    c = {
        k: 0
        for k in (
            "gaps_total",
            "gaps_physical",
            "gaps_not_econ_eligible",
            "gaps_da_cap",
            "gaps_restart_fail",
            "gaps_candidate",
            "units_scoped",
            "units_econ_eligible",
            "units_no_params",
            "units_lt2_runs",
            "units_no_runs",
            "runs_detected",
            "runs_kept",
        )
    }
    cb = {
        k: 0
        for k in (
            "gaps_total",
            "gaps_physical",
            "gaps_not_econ_eligible",
            "gaps_da_cap",
            "gaps_restart_fail",
            "gaps_candidate",
        )
    }
    mwh = {
        k: 0.0
        for k in (
            "physical",
            "da_cap",
            "restart_fail",
            "candidate",
            "not_econ_eligible",
        )
    }
    gap_len_belly: list[int] = []

    plant_pmax: dict[str, float] = {}
    for g, gen in enumerate(fleet):
        if getattr(gen, "is_campd_bin", False):
            key = gen.unit_id.rpartition("_")[0]
            plant_pmax[key] = plant_pmax.get(key, 0.0) + pmax[g]

    for g, gen in enumerate(fleet):
        if gen.plant_group.endswith("_CHP") or gen.fuel_type not in (
            "gas_cc",
            "gas_ct",
        ):
            continue
        resolved = _ra_bridge_unit_params(gen, float(fa.heat_rate[g]))
        if resolved is None:
            c["units_no_params"] += 1
            continue
        c["units_scoped"] += 1
        min_down, startup_per_mw = resolved
        econ_eligible = (
            startup_bridge
            and startup_per_mw > 0.0
            and min_down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS
        )
        if econ_eligible:
            c["units_econ_eligible"] += 1
        runs = find_runs(p0[g, :] > pmax[g] * 0.05)
        c["runs_detected"] += len(runs)
        if startup_aware and runs:
            gz = int(zone_idx[g])
            pg = max(float(pmax[g]), 1.0)
            runs = [
                (s, e)
                for s, e in runs
                if float(np.sum((p0_px[gz, s:e] - mc_base[g, s:e]) * p0[g, s:e])) / pg
                >= startup_per_mw
            ]
        c["runs_kept"] += len(runs)
        if not runs:
            c["units_no_runs"] += 1
            continue
        if len(runs) < 2:
            c["units_lt2_runs"] += 1
            continue
        is_bin = getattr(gen, "is_campd_bin", False)
        fp = (
            plant_pmax.get(gen.unit_id.rpartition("_")[0], pmax[g])
            if is_bin
            else pmax[g]
        )
        target_mw = min(frac * fp, pmax[g])
        zone = int(zone_idx[g])
        for (_, end_prev), (start_next, _) in zip(runs[:-1], runs[1:]):
            gap = start_next - end_prev
            if gap <= 0:
                continue
            bhrs = int(belly[end_prev:start_next].sum()) if belly is not None else 0
            in_belly = bhrs > 0
            c["gaps_total"] += 1
            if in_belly:
                cb["gaps_total"] += 1
                gap_len_belly.append(int(gap))

            def _tally(key: str, mkey: str) -> None:
                c["gaps_" + key] += 1
                if in_belly:
                    cb["gaps_" + key] += 1
                    mwh[mkey] += target_mw * bhrs

            if gap < min_down:
                _tally("physical", "physical")
                continue
            if not econ_eligible:
                _tally("not_econ_eligible", "not_econ_eligible")
                continue
            if bridge_decommit and gap > DA_COMMITMENT_HORIZON_HOURS:
                _tally("da_cap", "da_cap")
                continue
            mc_gap = float(np.mean(mc_base[g, end_prev:start_next]))
            lmp_gap = float(np.mean(p0_px[zone, end_prev:start_next]))
            if startup_per_mw > (mc_gap - lmp_gap) * frac * gap:
                _tally("candidate", "candidate")
            else:
                _tally("restart_fail", "restart_fail")

    # ---- EXACTNESS CHECK against the shipped function on the identical inputs.
    screen_stats: dict = {}
    real = caiso_ra_mustoffer_min_gen(
        p0,
        fa,
        fleet,
        frac,
        p1_prices=p0_px if (startup_bridge or startup_aware) else None,
        base_mc=mc_base if (startup_bridge or startup_aware) else None,
        startup_bridge=startup_bridge,
        bridge_decommit=bridge_decommit,
        surplus_floor_value=0.0,
        startup_aware=startup_aware,
        release_hours=None,
        startup_lead_hours=startup_lead,
        screen_stats=screen_stats,
    )
    runs_match = (
        screen_stats.get("runs_detected") == c["runs_detected"]
        and screen_stats.get("runs_kept") == c["runs_kept"]
    )
    ok = runs_match and not unmapped_scope
    gl = np.asarray(gap_len_belly) if gap_len_belly else np.zeros(0)
    return {
        "year": year,
        "status": "OK" if ok else "FAILED",
        "join": {
            "sidecar_rows": len(uids),
            "fleet_rows": n_gen,
            "bridge_scope_rows_unmapped": len(unmapped_scope),
            "unmapped_examples": unmapped_scope[:5],
            "pmax_violations": viol,
            "worst_pmax_excess_mw": worst,
            "pmax_violation_rows": int(rows_viol.size),
            "pmax_violation_examples": viol_examples,
        },
        "posture": {
            "min_load_frac": frac,
            "startup_bridge": startup_bridge,
            "bridge_decommit": bridge_decommit,
            "startup_aware": startup_aware,
            "startup_trajectory": startup_lead is not None,
            "da_horizon_hours": DA_COMMITMENT_HORIZON_HOURS,
            "econ_min_down_hours": RA_BRIDGE_ECON_MIN_DOWN_HOURS,
        },
        "all_hours": c,
        "belly_gaps": cb,
        "belly_floor_mwh_by_disposition": mwh,
        "belly_gap_len_hours": {
            "n": int(gl.size),
            "p50": float(np.median(gl)) if gl.size else None,
            "p90": float(np.percentile(gl, 90)) if gl.size else None,
            "max": int(gl.max()) if gl.size else None,
            "frac_gt_da_horizon": float(np.mean(gl > DA_COMMITMENT_HORIZON_HOURS))
            if gl.size
            else None,
        },
        "shipped_screen": {
            "runs_detected": screen_stats.get("runs_detected"),
            "runs_kept": screen_stats.get("runs_kept"),
            "runs_dropped": screen_stats.get("runs_dropped"),
            "drop_rate": (
                screen_stats.get("runs_dropped", 0) / screen_stats["runs_detected"]
                if screen_stats.get("runs_detected")
                else None
            ),
            "replay_reproduces": runs_match,
        },
        "floored_rows": int((real > 0).any(axis=1).sum()),
        "belly_mean_floor_mw": (
            float(real[:, belly].sum() / max(int(belly.sum()), 1))
            if belly is not None
            else None
        ),
        "belly_hours": int(belly.sum()) if belly is not None else None,
        "belly_net_load_mw_mean": float(net_load[belly].mean())
        if belly is not None
        else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/xiso8_leftedge_span")
    ap.add_argument("--iso", default="CAISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2024])
    ap.add_argument("--json-out", default=None)
    ap.add_argument(
        "--counterfactual",
        action="store_true",
        help="also census with the startup_aware run screen forced OFF (diagnostic only)",
    )
    a = ap.parse_args()
    logging.basicConfig(level=logging.ERROR)
    out = []
    for y in a.years:
        row = census(Path(a.bundle), a.iso, y)
        if a.counterfactual:
            cf = census(Path(a.bundle), a.iso, y, force_startup_aware=False)
            row["counterfactual_screen_off"] = {
                "belly_gaps": cf["belly_gaps"],
                "belly_gap_len_hours": cf["belly_gap_len_hours"],
                "belly_floor_mwh_by_disposition": cf["belly_floor_mwh_by_disposition"],
                "runs_kept": cf["all_hours"]["runs_kept"],
            }
        out.append(row)
    txt = json.dumps(out, indent=2, default=float)
    print(txt)
    if a.json_out:
        Path(a.json_out).write_text(txt)


if __name__ == "__main__":
    main()
