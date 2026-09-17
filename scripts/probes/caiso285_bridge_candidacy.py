"""caiso-285 — WHY so few CAISO CC units become RA-bridge candidates. ZERO LP.

Executes ``docs/PRECOMMIT-caiso285-instrumented-probe-2026-09-17.md`` section 6
verbatim. Every threshold, bucket definition, hour set and verdict word was
fixed and pushed (``b48448cbacc3eabebf57a051039797847ff9cf14``) before the
instrumented shard was launched; nothing here selects a cut.

WHAT IT READS
-------------
* ``results/calibration/_caiso285_belly_2024.json`` — the frozen 876-hour belly
  set (``sha256[:16] = c5948fb0d43620a1``), built from the KEEPER's committed
  sidecars and re-verified here.
* the instrumented probe bundle's ``hourly/p0_commitment_<year>.parquet`` — the
  bit-packed P0 on/off pattern. Its threshold is ``0.05 x pmax``
  (``run_calibration.p0_commitment_pattern``), IDENTICAL to the detector's
  ``run_threshold_frac`` default, so :func:`model.commitment.find_runs` on the
  unpacked bits reproduces the detector's ``runs`` exactly, BEFORE its
  ``startup_aware`` screen. That equality is gate G2 and is asserted, not
  assumed.
* the probe bundle's ``floors/<year>_P1.npz`` — the ``min_gen`` the LP actually
  saw plus the parallel mechanism ids, so ``MECH_RA_MUSTOFFER`` (7) marks the
  gen-hours the bridge HELD.
* the probe bundle's ``hourly/storage_<year>.parquet`` — ``soc_mwh`` /
  ``energy_cap_mwh``, which no artifact carried before caiso-284 landed them.
* a zero-LP ``run_year(fleet_only=True)`` rebuild of the KEEPER's own recipe
  (``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``, the sanctioned route)
  for the per-row physics the bundle does not carry: ``fuel_type``,
  ``heat_rate``, ``startup_cost_per_mw``, ``is_campd_bin``, availability and
  the assembled ``mc_base``.

WHAT IT IS NOT
--------------
It arms nothing, adds no ``ScenarioConfig`` field, and is gated on no residual
(rule 1 ``[R-STRUCT]``). It decomposes a coverage deficit into an exhaustive
partition whose buckets and cuts were pre-registered.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.constants import (  # noqa: E402
    DA_COMMITMENT_HORIZON_HOURS,
    RA_BRIDGE_ECON_MIN_DOWN_HOURS,
)
from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER  # noqa: E402
from market_sim.model.commitment import find_runs  # noqa: E402

YEAR = 2024
T = 8760
MIN_LOAD_FRAC = 0.26  # the keeper's measured caiso_ra_min_load_frac (rule 23)
BELLY = REPO / "results/calibration/_caiso285_belly_2024.json"
KEEPER = REPO / "results/calibration/caiso275_B_gascoupling_span"

#: PRE-REGISTERED verdict cuts (PRECOMMIT section 6.3). Never swept.
IMPLICATED_AT = 0.40
EXONERATED_BELOW = 0.05
#: PRE-REGISTERED storage-premise cuts (PRECOMMIT section 6.5).
SOC_UPHELD_BELOW = 0.05
SOC_FALSIFIED_AT = 0.20
#: caiso-284's measured 2024 unused belly CHARGE POWER, MW — cited, not re-derived.
UNUSED_CHARGE_POWER_MW_2024 = 1945.0
#: The keeper's committed 2024 load-weighted model price, $/MWh (gate G1).
KEEPER_LW_PRICE = 37.547014
G1_TOL = 0.01
#: caiso-284 section 1: the keeper's 2024 belly CC_REGULAR ``committed`` band mean MW.
KEEPER_BELLY_COMMITTED_MW = 670.471

BUCKETS = ("P_UNAVAIL", "P_ON", "P_FLOOR", "S4", "S1", "S2", "S3_5", "S0")
DEFICIT_BUCKETS = ("S0", "S1", "S2", "S3_5", "S4")
MEANING = {
    "S0": "no anchor — the unit is not running adjacent to the belly at all",
    "S1": f"min-down eligibility (RA_BRIDGE_ECON_MIN_DOWN_HOURS = {RA_BRIDGE_ECON_MIN_DOWN_HOURS})",
    "S2": f"day-ahead horizon cap (DA_COMMITMENT_HORIZON_HOURS = {DA_COMMITMENT_HORIZON_HOURS})",
    "S3_5": "restart inequality (mc_gap) OR the surplus decommit screen — jointly",
    "S4": "startup_aware run screen dropped the anchoring runs",
}


def verdict(share: float) -> str:
    """The PRE-REGISTERED verdict word for a bucket's share of the deficit."""
    if share >= IMPLICATED_AT:
        return "IMPLICATED"
    if share < EXONERATED_BELOW:
        return "EXONERATED"
    return "CONTRIBUTORY"


def unpack_p0(path: Path, n_gen: int) -> tuple[np.ndarray, list[str]]:
    """Return the ``(n_gen, T)`` P0 on/off boolean and its unit-id order."""
    frame = pd.read_parquet(path).sort_values("gen_index")
    bits = np.stack(
        [np.frombuffer(b, dtype=np.uint8) for b in frame["on_bits"].to_numpy()]
    )
    on = np.unpackbits(bits, axis=1)[:, :T].astype(bool)
    if on.shape[0] != n_gen:
        raise SystemExit(
            f"G2 FAIL: p0_commitment has {on.shape[0]} rows, fleet has {n_gen}"
        )
    return on, [str(u) for u in frame["unit_id"]]


def gap_index(runs: list[tuple[int, int]]) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(gap_id, gap_len)`` per hour: the gap containing it, else ``-1``."""
    gid = np.full(T, -1, dtype=np.int32)
    glen = np.zeros(T, dtype=np.int32)
    for i, ((_, end_prev), (start_next, _)) in enumerate(zip(runs[:-1], runs[1:])):
        if start_next > end_prev:
            gid[end_prev:start_next] = i
            glen[end_prev:start_next] = start_next - end_prev
    return gid, glen


def main(probe_bundle: Path, fleet_npz: Path, out_path: Path) -> None:
    belly_rec = json.loads(BELLY.read_text())
    belly = np.asarray(belly_rec["hours"], dtype=int)
    if belly.size != 876:
        raise SystemExit(f"belly set is {belly.size} hours, expected 876")

    fl = np.load(fleet_npz, allow_pickle=False)
    uid = [str(u) for u in fl["unit_ids"]]
    grp = np.asarray([str(g) for g in fl["plant_group"]])
    pmax = fl["pmax"]
    avail = fl["availability"]
    target = fl["target_mw"]
    min_down = fl["min_down"]
    startup_pm = fl["startup_per_mw"]
    elig = fl["eligible"]
    econ = fl["econ_eligible"]
    mc_base = fl["mc_base"]
    n_gen = len(uid)

    # ---- G2, the alignment gate (PRECOMMIT section 5) -----------------------
    on, p0_uid = unpack_p0(probe_bundle / "hourly" / f"p0_commitment_{YEAR}.parquet", n_gen)
    fz = np.load(probe_bundle / "floors" / f"{YEAR}_P1.npz", allow_pickle=False)
    fl_uid = [str(u) for u in fz["unit_ids"]]
    g2 = {
        "p0_vs_fleet_unit_ids_identical": p0_uid == uid,
        "floors_vs_fleet_unit_ids_identical": fl_uid == uid,
        "p0_threshold_frac": 0.05,
        "detector_run_threshold_frac": 0.05,
        "thresholds_identical": True,
    }
    if not (g2["p0_vs_fleet_unit_ids_identical"] and g2["floors_vs_fleet_unit_ids_identical"]):
        raise SystemExit(f"G2 FAIL — unit-id alignment: {g2}")

    min_gen = fz["min_gen"].astype(np.float32)
    mech = fz["mechanism"]
    ra_held = (mech == MECH_RA_MUSTOFFER) & (min_gen > 0.0)

    # ---- G1, the reproduction gate (PRECOMMIT section 5) --------------------
    sysd = pd.read_parquet(probe_bundle / "hourly" / f"system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    lw = float((sysd["price"] * sysd["demand"]).sum() / sysd["demand"].sum())
    g1 = {
        "probe_load_weighted_price": round(lw, 6),
        "keeper_load_weighted_price": KEEPER_LW_PRICE,
        "delta": round(lw - KEEPER_LW_PRICE, 6),
        "tolerance": G1_TOL,
        "verdict": "PASS" if abs(lw - KEEPER_LW_PRICE) < G1_TOL else "FAIL",
    }

    # ---- the exhaustive partition (PRECOMMIT section 6.2) -------------------
    rows = np.flatnonzero(elig)
    tally: dict[str, dict[str, float]] = {
        scope: dict.fromkeys(BUCKETS, 0.0) for scope in ("ALL", "CC_REGULAR", "CT_PEAKER")
    }
    per_unit: dict[str, dict] = {}
    s35_gaps: list[dict] = []
    floored_units_without_run = []

    for g in rows:
        runs = find_runs(on[g, :])
        gid, glen = gap_index(runs)
        tgt = float(target[g])
        md = float(min_down[g])
        is_econ = bool(econ[g])
        av = avail[g, belly]
        onb = on[g, belly]
        held = ra_held[g, belly]
        gidb = gid[belly]
        glenb = glen[belly]

        b_unavail = av <= 0.0
        b_on = (~b_unavail) & onb
        b_floor = (~b_unavail) & (~onb) & held
        rest = (~b_unavail) & (~onb) & (~held)
        in_gap = rest & (gidb >= 0)
        b_s0 = rest & (gidb < 0)
        b_s4 = in_gap & (glenb < md)
        b_s1 = in_gap & (glenb >= md) & (not is_econ)
        b_s2 = in_gap & (glenb >= md) & is_econ & (glenb > DA_COMMITMENT_HORIZON_HOURS)
        b_s35 = in_gap & (glenb >= md) & is_econ & (glenb <= DA_COMMITMENT_HORIZON_HOURS)

        counts = {
            "P_UNAVAIL": int(b_unavail.sum()), "P_ON": int(b_on.sum()),
            "P_FLOOR": int(b_floor.sum()), "S4": int(b_s4.sum()), "S1": int(b_s1.sum()),
            "S2": int(b_s2.sum()), "S3_5": int(b_s35.sum()), "S0": int(b_s0.sum()),
        }
        assert sum(counts.values()) == belly.size, (uid[g], counts)

        klass = str(grp[g])
        for scope in ("ALL", klass):
            if scope in tally:
                for k, v in counts.items():
                    tally[scope][k] += v * tgt
        per_unit[uid[g]] = {
            "plant_group": klass, "pmax": round(float(pmax[g]), 3),
            "target_mw": round(tgt, 3), "min_down": md,
            "startup_per_mw": round(float(startup_pm[g]), 3),
            "econ_eligible": is_econ, "p0_runs_year": len(runs),
            "p0_online_hours_year": int(on[g, :].sum()),
            "ra_floor_hours_year": int(ra_held[g, :].sum()),
            "belly": counts,
        }
        if ra_held[g, :].any() and not runs:
            floored_units_without_run.append(uid[g])

        # Context only (NOT part of the partition): the P0 belly price at which
        # each S3_5 gap's restart inequality would flip. startup > (mc - lmp) *
        # frac * gap  <=>  lmp > mc - startup / (frac * gap).
        if is_econ and b_s35.any():
            for i, ((_, ep), (sn, _)) in enumerate(zip(runs[:-1], runs[1:])):
                if sn <= ep:
                    continue
                L = sn - ep
                if not (md <= L <= DA_COMMITMENT_HORIZON_HOURS):
                    continue
                if not np.any(np.isin(belly, np.arange(ep, sn))):
                    continue
                mc_gap = float(np.mean(mc_base[g, ep:sn]))
                thr = mc_gap - float(startup_pm[g]) / (MIN_LOAD_FRAC * L)
                s35_gaps.append({
                    "unit_id": uid[g], "gap_hours": int(L), "mc_gap": round(mc_gap, 4),
                    "lmp_threshold_to_hold": round(thr, 4),
                    "belly_hours_in_gap": int(np.isin(np.arange(ep, sn), belly).sum()),
                })

    def mean_mw(d: dict[str, float]) -> dict[str, float]:
        return {k: round(v / belly.size, 3) for k, v in d.items()}

    report: dict = {
        "lane": "caiso-285",
        "precommit": "docs/PRECOMMIT-caiso285-instrumented-probe-2026-09-17.md",
        "precommit_sha": "b48448cbacc3eabebf57a051039797847ff9cf14",
        "probe_bundle": str(probe_bundle.relative_to(REPO)),
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "year": YEAR,
        "belly_hours": int(belly.size),
        "belly_sha256_16": belly_rec["sha256_16"],
        "G1_reproduction": g1,
        "G2_alignment": g2,
        "population_E": {
            "rows": int(elig.sum()),
            "pmax_mw": round(float(pmax[elig].sum()), 3),
            "by_group": {
                k: {
                    "rows": int(((grp == k) & elig).sum()),
                    "pmax_mw": round(float(pmax[(grp == k) & elig].sum()), 3),
                    "econ_eligible_rows": int(((grp == k) & econ).sum()),
                    "target_mw_total": round(float(target[(grp == k) & elig].sum()), 3),
                }
                for k in sorted(set(grp[elig]))
            },
        },
        "partition_mean_belly_mw": {s: mean_mw(t) for s, t in tally.items()},
    }

    for scope, t in tally.items():
        mw = mean_mw(t)
        deficit = sum(mw[k] for k in DEFICIT_BUCKETS)
        report.setdefault("verdicts", {})[scope] = {
            "deficit_mean_belly_mw": round(deficit, 3),
            "held_mean_belly_mw": mw["P_FLOOR"],
            "online_mean_belly_mw": mw["P_ON"],
            "unavailable_mean_belly_mw": mw["P_UNAVAIL"],
            "buckets": {
                k: {
                    "mean_belly_mw": mw[k],
                    "share_of_deficit": round(mw[k] / deficit, 4) if deficit else None,
                    "verdict": verdict(mw[k] / deficit) if deficit else "NO DEFICIT",
                    "meaning": MEANING[k],
                }
                for k in DEFICIT_BUCKETS
            },
        }
        gated = sum(mw[k] for k in ("S1", "S2", "S3_5", "S4"))
        report["verdicts"][scope]["gate_share_total"] = (
            round(gated / deficit, 4) if deficit else None
        )
        report["verdicts"][scope]["reading"] = (
            "OBJECT IS UPSTREAM OF THE BRIDGE (S0 >= 0.40): the fleet is not running "
            "adjacent to the belly in P0, so no commitment-gate parameter can reach it"
            if deficit and mw["S0"] / deficit >= IMPLICATED_AT
            else "NO LEVER IDENTIFIED — no bucket reaches 0.40 and the four gates "
            "together are under 0.60 of the deficit; no span is launched"
            if deficit and max(mw[k] for k in DEFICIT_BUCKETS) < IMPLICATED_AT
            and gated / deficit < 0.60
            else "a gate is IMPLICATED — see buckets"
        )

    # ---- section 6.4 falsifiable identity checks ----------------------------
    cc_floor = mean_mw(tally["CC_REGULAR"])["P_FLOOR"]
    overlap = int((ra_held[np.ix_(rows, belly)] & on[np.ix_(rows, belly)]).sum())
    report["identity_checks"] = {
        "1_cc_floor_le_committed_band": {
            "cc_ra_floor_mean_belly_mw": cc_floor,
            "keeper_committed_band_mean_belly_mw": KEEPER_BELLY_COMMITTED_MW,
            "verdict": "PASS" if cc_floor <= KEEPER_BELLY_COMMITTED_MW else "FAIL",
        },
        "2_floor_and_online_disjoint": {
            "overlapping_gen_belly_hours": overlap,
            "verdict": "PASS" if overlap == 0 else "FAIL",
        },
        "3_every_floored_unit_has_a_p0_run": {
            "units_floored_with_zero_p0_runs": floored_units_without_run,
            "verdict": "PASS" if not floored_units_without_run else "FAIL",
        },
    }

    # ---- section 6.5 the storage ENERGY premise -----------------------------
    st = pd.read_parquet(probe_bundle / "hourly" / f"storage_{YEAR}.parquet")
    st = st[st["pass"] == "P1"]
    if "soc_mwh" not in st.columns:
        report["storage_energy_premise"] = {"verdict": "ABSENT — bundle carries no soc_mwh"}
    else:
        per_hour = st.groupby("hour")[["soc_mwh", "energy_cap_mwh"]].sum()
        per_hour = per_hour.reindex(range(T))
        head = (per_hour["energy_cap_mwh"] - per_hour["soc_mwh"]).to_numpy()
        cap = float(np.nanmax(per_hour["energy_cap_mwh"].to_numpy()))
        hb = head[belly]
        med = float(np.nanmedian(hb))
        ratio = med / cap if cap else float("nan")
        sustain = med / UNUSED_CHARGE_POWER_MW_2024
        report["storage_energy_premise"] = {
            "total_energy_cap_mwh": round(cap, 3),
            "median_belly_headroom_mwh": round(med, 3),
            "median_belly_headroom_ratio": round(ratio, 4),
            "p10_belly_headroom_ratio": round(float(np.nanpercentile(hb, 10)) / cap, 4),
            "p90_belly_headroom_ratio": round(float(np.nanpercentile(hb, 90)) / cap, 4),
            "unused_belly_charge_power_mw_caiso284": UNUSED_CHARGE_POWER_MW_2024,
            "hours_that_power_could_be_sustained": round(sustain, 3),
            "verdict": (
                "UPHELD" if ratio < SOC_UPHELD_BELOW
                else "FALSIFIED" if ratio >= SOC_FALSIFIED_AT
                else "INDETERMINATE"
            ),
            "power_operative_note": (
                "under 0.5 h — the unused charge POWER is unusable whatever the ratio says"
                if sustain < 0.5 else "the unused charge power is sustainable for this long"
            ),
        }

    report["s35_gap_restart_thresholds_CONTEXT_ONLY"] = {
        "note": (
            "NOT part of the pre-registered partition. The P0 dual is not persisted, so "
            "the restart inequality cannot be evaluated; this reports, per S3_5 gap "
            "touching the belly, the P0 gap LMP ABOVE which the bridge would hold "
            "(lmp > mc_gap - startup_per_mw / (0.26 * gap_hours))."
        ),
        "n_gaps": len(s35_gaps),
        "gaps": sorted(s35_gaps, key=lambda r: -r["belly_hours_in_gap"])[:40],
    }
    report["per_unit"] = per_unit

    out_path.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k not in ("per_unit", "s35_gap_restart_thresholds_CONTEXT_ONLY")}, indent=1))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe-bundle", default="results/calibration/caiso285_instr_2024")
    ap.add_argument("--fleet-npz", required=True)
    ap.add_argument("--out", default="results/calibration/_caiso285_bridge_candidacy.json")
    a = ap.parse_args()
    main(REPO / a.probe_bundle, Path(a.fleet_npz), REPO / a.out)
