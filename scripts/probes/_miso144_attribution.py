"""miso-144 G-A — attribute the miso-143 in-merit idle block.

PREREG ``results/calibration/PREREG-miso144-inmerit-idle-attribution-2026-08-08.md``
(pushed at ``017f6bee``, blob ``5599ba80``, BEFORE any adjudicating statistic).

Reuses the miso-143 harness verbatim (``_miso143_stack``: hygiene guard,
asserted coal alias, ``klass_of``, ``run_year(fleet_only=True)`` reconstruction,
P1-markup bracket).  NO SOLVE.  Every dispatch/price number is the keeper's own
committed sidecar; the offer stack is the orchestrator's own reconstruction.

The ledger (PREREG §3), per year × window × offer bracket:

* **G-A0** — replicate miso-143's ``excess`` byte-for-byte (its own mixed
  weighting: load-weighted ``below`` minus unweighted thermal mean), and assert
  the six committed values to ≤ 5 MW.  Then restate A0 on ONE weight (TRAP 7)
  for the ledger.
* **G-A1** — the universe split: ``T_universe`` (per non-thermal fleet class),
  ``T_injected`` (OTHER + biomass 12-value injections), identity CC-1.
* **G-A2** — per-thermal-class in-merit idle / out-of-merit lower bounds
  (cheapest-first within class; identity CC-2 exact per hour), the zonal-anchor
  term, the tie band at δ ∈ {0.01, 0.10, 0.50, 1.00}, the lo→hi offer-basis
  term, the reserve holding (rbdc = the physical total; partition asserted),
  and the floor-based unit-grain OOM measure (``min_gen`` × offer>anchor, split
  by ``min_gen_mechanism`` id).
* **G-A3** — ``T_resid`` = strict-zonal-``hi`` in-merit idle − reserve held,
  against the pre-registered stop |T_resid| > 3.0 GW.

Usage::

    .venv/bin/python scripts/probes/_miso144_attribution.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import (  # noqa: E402
    COAL_COLS,
    GAS_COLS,
    HOURS,
    KEEPER,
    THERMAL_COLS,
    YEARS,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    sidecar_classes,
    sidecar_price,
    windows,
)

OUT = REPO / "results/calibration/_miso144_attribution.json"

# Fleet-class universes (PREREG §3).  The fleet's bare "COAL" aliases to the
# sidecar's three coal columns (TRAP 5, asserted in _miso143_stack).
THERMAL_FLEET = ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP", "oil")
NONTHERMAL_FLEET = ("nuclear", "hydro", "import", "biomass")
SIDECAR_FOR_FLEET = {k: (COAL_COLS if k == "COAL" else (k,)) for k in THERMAL_FLEET}
INJECTED = ("OTHER", "biomass")  # 12-value must-run injections (miso-142 §O4)
TIE_DELTAS = (0.01, 0.10, 0.50, 1.00)
TIE_PRIMARY = 0.10
# Committed miso-143 excess values (results/calibration/_miso143_ladder.json,
# footing_failure_diagnostic) -- the G-A0 replication targets, ≤ 5 MW each.
MISO143_EXCESS = {
    (2023, "lo"): 21951.2, (2023, "hi"): 20966.2,
    (2024, "lo"): 20001.0, (2024, "hi"): 19031.5,
    (2025, "lo"): 19330.1, (2025, "hi"): 18210.2,
}
REPLICATION_TOL_MW = 5.0


def zone_price_matrix(year: int) -> tuple[dict[str, int], np.ndarray]:
    """Per-zone committed P1 price, (n_zones, HOURS), keyed by zone name."""
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    piv = df.pivot_table(index="zone", columns="hour", values="price", aggfunc="first")
    piv = piv.reindex(columns=range(HOURS))
    names = {str(z): i for i, z in enumerate(piv.index)}
    return names, piv.to_numpy(float)


def reserve_held(year: int) -> tuple[np.ndarray, float]:
    """rbdc family held_mw per hour (the PHYSICAL withheld total; TRAP 9).

    Asserts the partition midwest + south = rbdc per hour, so summing families
    can never be smuggled in as the reserve term.
    """
    df = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    piv = df.pivot_table(index="hour", columns="family", values="held_mw", aggfunc="first")
    piv = piv.reindex(range(HOURS))
    rbdc = piv["miso_rbdc"].to_numpy(float)
    parts = piv["miso_subregional_or_midwest"].to_numpy(float) + piv[
        "miso_zonal_or_miso_south"
    ].to_numpy(float)
    dev = float(np.nanmax(np.abs(parts - rbdc)))
    assert dev <= 1.0, f"reserve family partition broken: max |midwest+south-rbdc| = {dev} MW"
    return rbdc, dev


def year_block(year: int) -> dict:
    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    mk = markup_ceiling(gens, fa, st["config"])
    cap = fa.pmax[:, None] * fa.availability
    kl = klass_of(gens)

    # TRAP 6 -- non-empty classes; and the universe is CLOSED: any fleet class
    # outside the two pre-registered sets fails loudly rather than being
    # silently absorbed into either side of the subtraction.
    seen = sorted(set(kl.tolist()))
    unexpected = [k for k in seen if k not in THERMAL_FLEET + NONTHERMAL_FLEET]
    assert not unexpected, f"unexpected fleet classes {unexpected} (universe not closed)"
    for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
        assert (kl == k).sum() > 0, f"class {k!r} has ZERO fleet rows (TRAP 6)"

    piv = sidecar_classes(year)
    thermal_all = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    price, den = sidecar_price(year)

    # TRAP 10 -- the injections really are 12-value profiles, asserted.
    for c in INJECTED:
        nv = int(piv[c].round(3).nunique())
        assert nv <= 12, f"injected class {c} has {nv} distinct values (expected ≤12)"

    # C3a's own weight, byte-consistent with miso-143 (`model_hourly`'s w).
    from _miso137_c3a_gap_decomposition import model_hourly

    _h, _p, w_model, _z = model_hourly(year)
    w_vs_den = float(np.nanmax(np.abs(w_model - den)))

    znames, zprice = zone_price_matrix(year)
    from market_sim.config.iso_configs import get_iso_config

    cfg_zones = [z.name for z in get_iso_config("MISO").zones]
    # The LP zone order = config zones + appended external seam buses; the
    # authoritative order is committed in the run's own reserve sidecar zones
    # string (the rbdc family spans every LP zone in LP order).
    rf = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
    lp_zones = str(rf.loc[rf["family"] == "miso_rbdc", "zones"].iloc[0]).split("|")
    assert lp_zones[: len(cfg_zones)] == cfg_zones, (
        f"LP zone order {lp_zones} does not start with config zones {cfg_zones}"
    )
    assert set(lp_zones) <= set(znames), (
        f"LP zones {lp_zones} not all in system parquet zones {sorted(znames)}"
    )
    zrow = np.array([znames[z] for z in lp_zones], dtype=int)
    assert int(fa.zone_idx.max()) < len(lp_zones), (
        f"zone_idx max {int(fa.zone_idx.max())} exceeds LP zone list {lp_zones}"
    )
    unit_zone_row = zrow[fa.zone_idx]  # (n_gen,) row into zprice

    held, held_partition_dev = reserve_held(year)

    min_gen = fa.min_gen  # (n_gen, T) or None
    mech_id = fa.min_gen_mechanism

    # Sidecar dispatch per fleet-thermal class (COAL aliased; TRAP 5).
    disp_c = {
        k: sum(piv[c].to_numpy(float) for c in cols)
        for k, cols in SIDECAR_FOR_FLEET.items()
    }
    inj_disp = sum(piv[c].to_numpy(float) for c in INJECTED)

    is_class = {k: (kl == k) for k in seen}
    thermal_rows = np.isin(kl, THERMAL_FLEET)

    yr: dict = {"n_gen": len(gens), "w_model_vs_den_max_abs": round(w_vs_den, 6),
                "reserve_partition_max_dev_mw": round(held_partition_dev, 4),
                "has_min_gen": min_gen is not None,
                "has_min_gen_mechanism": mech_id is not None}

    for wname, sel in windows().items():
        ok = sel & np.isfinite(price) & np.isfinite(thermal_all) & (thermal_all > 0)
        hrs = np.nonzero(ok)[0]
        wgt = w_model[hrs] / max(1e-9, w_model[hrs].sum())

        def lwm(x: np.ndarray) -> float:
            """ONE window weight for every ledger mean (TRAP 7)."""
            return float(np.dot(np.asarray(x, dtype=float), wgt))

        blk: dict = {
            "n_hours": int(hrs.size),
            "anchor_lw_price": round(lwm(price[hrs]), 3),
            "thermal_served_unweighted_mw": round(float(np.mean(thermal_all[hrs])), 1),
            "thermal_served_lw_mw": round(lwm(thermal_all[hrs]), 1),
        }

        for tag, off in (("lo", mc0), ("hi", mc0 + mk[:, None])):
            n = hrs.size
            below_all = np.zeros(n)
            cb_sys = {k: np.zeros(n) for k in seen}       # capbelow at system anchor
            cb_zon = {k: np.zeros(n) for k in seen}       # capbelow at own-zone price
            cb_strict = {d: {k: np.zeros(n) for k in THERMAL_FLEET} for d in TIE_DELTAS}
            floor_oom = np.zeros(n)                        # min_gen on offer>anchor rows
            floor_oom_by_mech: dict[int, np.ndarray] = {}

            for j, t in enumerate(hrs):
                o_t, c_t, a = off[:, t], cap[:, t], float(price[t])
                pz = zprice[unit_zone_row, t]              # own-zone price per row
                sel_sys = o_t <= a
                below_all[j] = float(c_t[sel_sys].sum())
                sel_zon = o_t <= pz
                for k in seen:
                    m = is_class[k]
                    cb_sys[k][j] = float(c_t[m & sel_sys].sum())
                    cb_zon[k][j] = float(c_t[m & sel_zon].sum())
                for d in TIE_DELTAS:
                    sel_s = o_t <= (pz - d)
                    for k in THERMAL_FLEET:
                        cb_strict[d][k][j] = float(c_t[is_class[k] & sel_s].sum())
                if min_gen is not None:
                    fl = np.minimum(min_gen[:, t], c_t)
                    oomrow = thermal_rows & (o_t > a) & (fl > 0)
                    floor_oom[j] = float(fl[oomrow].sum())
                    if mech_id is not None and oomrow.any():
                        for mid in np.unique(mech_id[oomrow, t]):
                            arr = floor_oom_by_mech.setdefault(int(mid), np.zeros(n))
                            arr[j] = float(fl[oomrow & (mech_id[:, t] == mid)].sum())

            # ---- G-A0: byte-for-byte replication of miso-143's construction
            excess_143 = lwm(below_all) - float(np.mean(thermal_all[hrs]))
            rep = None
            if wname == "JJA_h12_17":
                target = MISO143_EXCESS[(year, tag)]
                rep = {
                    "committed_mw": target,
                    "replicated_mw": round(excess_143, 1),
                    "delta_mw": round(excess_143 - target, 2),
                    "pass": bool(abs(excess_143 - target) <= REPLICATION_TOL_MW),
                }

            # ---- ledger on ONE weight -----------------------------------
            a0_lw = lwm(below_all) - lwm(thermal_all[hrs])
            t_universe = {k: lwm(cb_sys[k]) for k in NONTHERMAL_FLEET if k in cb_sys}
            t_universe_total = float(sum(t_universe.values()))
            t_injected = lwm(inj_disp[hrs])
            thermal_gap = a0_lw - t_universe_total + t_injected
            # CC-1: direct thermal-side recompute must equal thermal_gap.
            direct_gap = lwm(
                sum(cb_sys[k] for k in THERMAL_FLEET)
                - sum(disp_c[k][hrs] for k in THERMAL_FLEET)
            )
            cc1_dev = abs(thermal_gap - direct_gap)

            idle_sys = {k: np.maximum(0.0, cb_sys[k] - disp_c[k][hrs]) for k in THERMAL_FLEET}
            oom_sys = {k: np.maximum(0.0, disp_c[k][hrs] - cb_sys[k]) for k in THERMAL_FLEET}
            idle_zon = {k: np.maximum(0.0, cb_zon[k] - disp_c[k][hrs]) for k in THERMAL_FLEET}
            idle_strict = {
                d: {
                    k: np.maximum(0.0, cb_strict[d][k] - disp_c[k][hrs])
                    for k in THERMAL_FLEET
                }
                for d in TIE_DELTAS
            }
            idle_sys_tot = lwm(sum(idle_sys.values()))
            oom_sys_tot = lwm(sum(oom_sys.values()))
            cc2_dev = abs((idle_sys_tot - oom_sys_tot) - thermal_gap)
            idle_zon_tot = lwm(sum(idle_zon.values()))
            strict_tot = {d: lwm(sum(idle_strict[d].values())) for d in TIE_DELTAS}
            t_zonal = idle_sys_tot - idle_zon_tot
            t_tie = idle_zon_tot - strict_tot[TIE_PRIMARY]
            t_reserve = lwm(held[hrs])

            blk[tag] = {
                "replication_g_a0": rep,
                "excess_miso143_construction_mw": round(excess_143, 1),
                "A0_oneweight_mw": round(a0_lw, 1),
                "T_universe_by_class_mw": {k: round(v, 1) for k, v in t_universe.items()},
                "T_universe_total_mw": round(t_universe_total, 1),
                "T_injected_mw": round(t_injected, 1),
                "thermal_gap_mw": round(thermal_gap, 1),
                "cc1_identity_dev_mw": round(cc1_dev, 6),
                "idle_sys_LB_by_class_mw": {k: round(lwm(v), 1) for k, v in idle_sys.items()},
                "idle_sys_LB_total_mw": round(idle_sys_tot, 1),
                "oom_sys_LB_by_class_mw": {k: round(lwm(v), 1) for k, v in oom_sys.items()},
                "oom_sys_LB_total_mw": round(oom_sys_tot, 1),
                "cc2_identity_dev_mw": round(cc2_dev, 6),
                "floor_oom_mw": round(lwm(floor_oom), 1) if min_gen is not None else None,
                "floor_oom_by_mechanism_mw": {
                    str(mid): round(lwm(arr), 1)
                    for mid, arr in sorted(floor_oom_by_mech.items())
                },
                "T_zonal_mw": round(t_zonal, 1),
                "idle_zonal_LB_total_mw": round(idle_zon_tot, 1),
                "T_tie_mw_at_delta": {
                    str(d): round(idle_zon_tot - strict_tot[d], 1) for d in TIE_DELTAS
                },
                "idle_strict_total_mw_at_delta": {
                    str(d): round(v, 1) for d, v in strict_tot.items()
                },
                "T_reserve_mw": round(t_reserve, 1),
                "T_resid_mw_strict_primary_minus_reserve": round(
                    strict_tot[TIE_PRIMARY] - t_reserve, 1
                ),
                "idle_strict_by_class_primary": {
                    k: round(lwm(v), 1) for k, v in idle_strict[TIE_PRIMARY].items()
                },
            }
        yr[wname] = blk
    return yr


def main() -> None:
    hygiene()
    res = {
        "prereg": "results/calibration/PREREG-miso144-inmerit-idle-attribution-2026-08-08.md",
        "prereg_commit": "017f6bee",
        "gate": "G-A0..G-A3 -- attribution of the miso-143 in-merit idle block",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": "NO SOLVE -- run_year(fleet_only=True) offer stack vs the keeper's "
        "own committed sidecars; miso-143 anchor reused",
        "notes": {
            "T_resid_semantics": "strict-zonal idle at delta=0.10 minus rbdc held; "
            "held is the PHYSICAL total (partition asserted) and over-subtracts by "
            "any non-thermal/storage-backed holding, so T_resid is biased DOWN by "
            "that share",
            "instrument_limit": "fleet_only availability is the reconstruction's, "
            "not re-verifiable against the solve's own draw from committed "
            "artifacts (PREREG §6 stop 2 successor if the residual blows)",
        },
        "years": {},
    }
    for y in YEARS:
        res["years"][str(y)] = year_block(y)
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
