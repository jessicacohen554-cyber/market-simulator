#!/usr/bin/env python3
"""pjm-146 A/B scorer — the gated PJM RGGI allowance adder.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-pjm146-rggi-allowance-2026-08-02.md`` (K1-K5 in
§4) and reports **only** the quantities §3 declares reportable. Modeled on
``_pjm144_zonal_anchor_ab.py``: every scored criterion — C3c included — is
taken from each bundle's own ``metrics.json``, never re-derived; the only
quantities this file computes itself are construction/delta statistics
(membership audit, mc-identity, per-zone / load-weighted λ deltas,
member-state energy attribution), none of which is a scored criterion.

K1/K3 run the pjm-145 ex-ante pattern: both arms' fleets rebuilt through the
REAL ``run_calibration.run_year(fleet_only=True)`` path (keeper meta via
``replay_keeper.build_kwargs``), so the audited ``mc_base`` is byte-what the
LP solved on. The membership expectation is REIMPLEMENTED from first
principles here (EIA-860 plant state x RGGI_MEMBER_STATES_BY_YEAR x committed
zone-share fallback) so the audit is independent of
``per_generator_membership``'s internals.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_pjm146_rggi_ab.py
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
ARM_A = REPO / "results/calibration/pjm146_control_A"
ARM_B = REPO / "results/calibration/pjm146_rggi_B"
OUT_PATH = REPO / "results/calibration/_pjm146_rggi_ab.json"

YEARS = (2023, 2024, 2025)
FLAG = "pjm_rggi_allowance_pricing"

#: PREREG §4 thresholds.
K1_MIN_UNITS = 50
K1_TOL = 1e-9
K5_LIVENESS_LW_PRICE = 0.10

EXTERNAL_PREFIX = "PJM_external"

MEMBER_ALL_YEARS = frozenset({"NJ", "MD", "DE"})


# ── committed-artifact readers (the _pjm144 conventions) ────────────────────


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    return frame[~frame["zone"].astype(str).str.startswith(EXTERNAL_PREFIX)]


def _lw_price(bundle: Path, year: int) -> float:
    pj = _system(bundle, year)
    return float((pj["price"] * pj["demand"]).sum() / pj["demand"].sum())


def _zone_price(bundle: Path, year: int) -> dict[str, float]:
    pj = _system(bundle, year)
    return {
        str(k): round(float(v), 6)
        for k, v in pj.groupby("zone")["price"].mean().items()
    }


def _pairwise(a: Path, b: Path, year: int) -> dict:
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
        },
    }


def _class_energy_delta(year: int) -> dict[str, float]:
    """Arm B minus arm A annual class energy, TWh."""
    a = _class_hourly(ARM_A, year).groupby("klass")["mw"].sum() / 1e6
    b = _class_hourly(ARM_B, year).groupby("klass")["mw"].sum() / 1e6
    joined = b.subtract(a, fill_value=0.0)
    return {
        str(k): round(float(v), 4)
        for k, v in joined.items()
        if abs(float(v)) > 5e-5
    }


def _scenario_block(bundle: Path) -> dict:
    path = bundle / "run_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("scenario_config", {}) or {}


def _metrics(bundle: Path) -> dict | None:
    path = bundle / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else None


def _criteria(bundle: Path) -> dict[str, str]:
    m = _metrics(bundle)
    if not m:
        return {}
    return {
        k: (v.get("status") if isinstance(v, dict) else v)
        for k, v in (m.get("criteria") or {}).items()
    }


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


# ── fleet reconstruction through the real path (pjm-145 pattern) ────────────


def _run_year_kwargs(meta: dict) -> dict:
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {
        "commitment": "commitment_enabled",
        "screen_coal": "commitment_screen_coal",
    }
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs, dropped = {}, []
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    print(f"[map] {len(kwargs)} kwargs bound; dropped: {sorted(dropped)}")
    return kwargs


def _zone_names_from(fa, generators) -> list[str]:
    """Rebuild the runtime zone-name list from the (generator, ``zone_idx``) pairing.

    ``FleetArrays`` stores only ``zone_idx``; the names live in the caller's
    ``zone_names`` argument to ``generators_to_fleet_arrays``, which
    ``run_year(fleet_only=True)`` does not return in its state dict. The
    reconstruction is exact because ``zone_idx`` is built as
    ``[zone_to_idx[g.zone] for g in generators]`` (``fleet/arrays.py``), so the
    generator list and the index array are 1:1 by construction — and the list
    ``run_year`` hands back is the same post-``apply_interchange_topology``,
    virtual/DR-extended ``fleet`` object that built the arrays, which is the
    interchange-extended list PREREG-pjm146 sec.2.4 requires.
    """
    idx = np.asarray(fa.zone_idx, dtype=int)
    if idx.size == 0:
        return []
    names: dict[int, str] = {}
    for gen, j in zip(generators, idx):
        zone = getattr(gen, "zone", None)
        if zone is not None:
            names[int(j)] = str(zone)
    return [names.get(j, "") for j in range(int(idx.max()) + 1)]


def _expected_membership(fa, year: int, zone_names: list[str]) -> np.ndarray:
    """First-principles member mask: plant state test + committed zone fallback."""
    from market_sim.config.capacity_market import (
        PJM_RGGI_ZONE_SHARE,
        RGGI_MEMBER_STATES_BY_YEAR,
    )
    from market_sim.data.zone_assignment import plant_state_lookup

    states = plant_state_lookup("PJM")
    members = RGGI_MEMBER_STATES_BY_YEAR[year]
    zone_fallback = np.array(
        [
            float(PJM_RGGI_ZONE_SHARE.get(z, {}).get(year, 0.0))
            for z in zone_names
        ],
        dtype=float,
    )
    m = zone_fallback[np.asarray(fa.zone_idx, dtype=int)]
    codes = np.asarray(fa.plant_code, dtype=int)
    for i, code in enumerate(codes):
        if code <= 0:
            continue
        st = states.get(int(code))
        if st is None:
            continue
        m[i] = 1.0 if st in members else 0.0
    return m


def k1_k3_mc_and_membership() -> dict:
    """K1 (mc identity, live count) + K3 (membership audit), both arms, per year."""
    from market_sim.config.fuel_trajectories import (
        PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE,
    )
    from market_sim.data.zone_assignment import plant_state_lookup
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    base_kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})
    states = plant_state_lookup("PJM")

    out: dict = {"years": {}, "passed_k1": True, "passed_k3": True}
    for yr in YEARS:
        price = float(PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE[yr])
        gas = float(gas_prices.get(str(yr), gas_prices.get(yr, 0.0)))
        mc_by_arm: dict[str, np.ndarray] = {}
        fa = None
        for arm in ("control", "arm"):
            kw = dict(base_kwargs)
            if arm == "arm":
                prb = dict(kw.get("prb_overrides") or {})
                prb[FLAG] = True
                kw["prb_overrides"] = prb
            state = run_year(yr, "PJM", 8760, gas, {}, fleet_only=True, **kw)
            mc_by_arm[arm] = np.asarray(state["mc_base"], dtype=float)
            if arm == "arm":
                fa = state["fleet_arrays"]
                gens = state["fleet"]
            else:
                del state
        rate = np.asarray(fa.emission_rate, dtype=float)
        codes = np.asarray(fa.plant_code, dtype=int)
        m_expect = _expected_membership(fa, yr, _zone_names_from(fa, gens))
        delta = mc_by_arm["arm"] - mc_by_arm["control"]
        # The adder is hour-invariant; audit on the per-unit max/min spread.
        d_lo, d_hi = delta.min(axis=1), delta.max(axis=1)
        hour_invariant = float(np.max(d_hi - d_lo))
        expected = rate * m_expect * price
        mismatch = np.abs(d_hi - expected)
        worst = float(mismatch.max())
        n_live = int(np.sum(expected > 0.5))  # units with a >$0.5/MWh adder
        n_nonzero = int(np.sum(expected > 0.0))

        # K3 named sub-audits, per-unit path only (codes > 0, state resolved).
        resolved = np.array(
            [codes[i] > 0 and int(codes[i]) in states for i in range(len(codes))]
        )
        st_arr = np.array(
            [states.get(int(c), "") if c > 0 else "" for c in codes]
        )
        va = resolved & (st_arr == "VA")
        nonmember = resolved & ~np.isin(st_arr, sorted(MEMBER_ALL_YEARS | {"VA"}))
        member_core = resolved & np.isin(st_arr, sorted(MEMBER_ALL_YEARS))
        va_ok = bool(
            np.all(m_expect[va] == (1.0 if yr == 2023 else 0.0)) if va.any() else True
        )
        nonmember_ok = bool(np.all(m_expect[nonmember] == 0.0))
        member_ok = bool(np.all(m_expect[member_core] == 1.0))

        k1_ok = worst <= K1_TOL and hour_invariant <= K1_TOL and n_live >= K1_MIN_UNITS
        k3_ok = va_ok and nonmember_ok and member_ok
        out["passed_k1"] &= k1_ok
        out["passed_k3"] &= k3_ok
        out["years"][str(yr)] = {
            "price_per_tonne": price,
            "n_units_nonzero_adder": n_nonzero,
            "n_units_adder_gt_0p5": n_live,
            "member_capacity_mw": round(
                float(np.asarray(fa.pmax, dtype=float)[m_expect > 0].sum()), 1
            ),
            "mc_identity_worst_abs_err": worst,
            "mc_hour_invariance_worst": hour_invariant,
            "adder_by_class_capwtd": _capwtd_adder_by_class(fa, expected),
            "k3": {
                "va_membership_ok": va_ok,
                "va_expected": 1.0 if yr == 2023 else 0.0,
                "n_va_units": int(va.sum()),
                "nonmember_zero_ok": nonmember_ok,
                "member_core_one_ok": member_ok,
                "n_member_core_units": int(member_core.sum()),
                "n_zone_fallback_rows": int(np.sum(~resolved)),
            },
            "k1_ok": k1_ok,
        }
        del mc_by_arm, delta
    return out


def _capwtd_adder_by_class(fa, expected: np.ndarray) -> dict[str, float]:
    groups = np.array([str(g) for g in fa.plant_group])
    pmax = np.asarray(fa.pmax, dtype=float)
    out = {}
    for cls in sorted(set(groups)):
        idx = (groups == cls) & (expected > 0)
        if idx.any():
            out[cls] = round(float((expected[idx] * pmax[idx]).sum() / pmax[idx].sum()), 3)
    return out


# ── member-state energy attribution from the solved year parquets ───────────


def _member_energy_twh(bundle: Path, year: int) -> float | None:
    """Annual energy on member-state fossil units, TWh, from the year parquet.

    Uses the parquet's fleet-context unit ids mapped to plant codes and the
    same first-principles state test. Returns None when the bundle lacks a
    readable per-unit year parquet (the scorer then reports class-grain only).
    """
    try:
        import pyarrow.parquet as pq

        path = bundle / f"year_{year}.parquet"
        if not path.exists():
            return None
        table = pq.read_table(path, columns=["dispatch"])
        meta = pq.read_schema(path).metadata or {}
        ctx = json.loads(meta.get(b"fleet_context", b"{}"))
        unit_plant = ctx.get("plant_code") or ctx.get("plant_codes")
        if not unit_plant:
            return None
        from market_sim.config.capacity_market import RGGI_MEMBER_STATES_BY_YEAR
        from market_sim.data.zone_assignment import plant_state_lookup

        states = plant_state_lookup("PJM")
        members = RGGI_MEMBER_STATES_BY_YEAR[year]
        mask = np.array(
            [
                int(c) > 0 and states.get(int(c)) in members
                for c in unit_plant
            ]
        )
        disp = np.asarray(table["dispatch"].combine_chunks().to_numpy(zero_copy_only=False).tolist())
        return round(float(disp[:, mask].sum()) / 1e6, 4)
    except Exception as exc:  # reported, never fatal — class grain remains
        print(f"[member-energy] {bundle.name} {year}: unreadable ({exc})")
        return None


# ── assembly ────────────────────────────────────────────────────────────────


def main() -> None:
    a_cfg, b_cfg = _scenario_block(ARM_A), _scenario_block(ARM_B)
    flag_fidelity = {
        "passed": a_cfg.get(FLAG) in (False, None) and b_cfg.get(FLAG) is True,
        "A": a_cfg.get(FLAG),
        "B": b_cfg.get(FLAG),
    }

    k13 = k1_k3_mc_and_membership()

    keeper_c, a_c, b_c = _criteria(KEEPER), _criteria(ARM_A), _criteria(ARM_B)
    km, am, bm = _metrics(KEEPER), _metrics(ARM_A), _metrics(ARM_B)
    k2 = {
        "passed": bool(
            keeper_c
            and a_c
            and keeper_c == a_c
            and (km or {}).get("determination") == (am or {}).get("determination")
        ),
        "basis": "scorecard (gate); strict byte basis reported below",
        "byte": {str(y): _pairwise(KEEPER, ARM_A, y) for y in YEARS},
        "keeper_criteria": keeper_c,
        "control_criteria": a_c,
    }

    price_deltas, k4_sign_ok, k5_live = {}, True, False
    for y in YEARS:
        lw_a, lw_b = _lw_price(ARM_A, y), _lw_price(ARM_B, y)
        d = lw_b - lw_a
        za, zb = _zone_price(ARM_A, y), _zone_price(ARM_B, y)
        price_deltas[str(y)] = {
            "lw_control": round(lw_a, 4),
            "lw_arm": round(lw_b, 4),
            "lw_delta": round(d, 4),
            "zone_delta": {
                z: round(zb[z] - za[z], 4) for z in sorted(za) if z in zb
            },
        }
        if d < 0:
            k4_sign_ok = False
        if abs(d) >= K5_LIVENESS_LW_PRICE:
            k5_live = True

    member_energy = {}
    for y in YEARS:
        ea, eb = _member_energy_twh(ARM_A, y), _member_energy_twh(ARM_B, y)
        member_energy[str(y)] = {
            "control_twh": ea,
            "arm_twh": eb,
            "delta_twh": (None if ea is None or eb is None else round(eb - ea, 4)),
        }
        if (
            member_energy[str(y)]["delta_twh"] is not None
            and member_energy[str(y)]["delta_twh"] > 0
        ):
            k4_sign_ok = False

    report = {
        "prereg": "results/calibration/PREREG-pjm146-rggi-allowance-2026-08-02.md",
        "arms": {"control": str(ARM_A), "arm": str(ARM_B), "keeper": str(KEEPER)},
        "flag_fidelity": flag_fidelity,
        "K1_mechanism_live": {
            "passed": bool(k13["passed_k1"]),
            "years": {y: v for y, v in k13["years"].items()},
        },
        "K2_control_integrity": k2,
        "K3_membership_audit": {"passed": bool(k13["passed_k3"])},
        "K4_sign": {"passed": bool(k4_sign_ok)},
        "K5_liveness": {
            "passed": bool(k5_live),
            "rule": f"lw |delta| >= ${K5_LIVENESS_LW_PRICE} in >=1 year; all-years miss => verdict I",
        },
        "price_deltas": price_deltas,
        "member_state_energy": member_energy,
        "class_energy_delta_twh": {str(y): _class_energy_delta(y) for y in YEARS},
        "criteria": {
            "keeper": keeper_c,
            "control": a_c,
            "arm": b_c,
            "determinations": {
                "keeper": (km or {}).get("determination"),
                "control": (am or {}).get("determination"),
                "arm": (bm or {}).get("determination"),
            },
        },
        "slack_dump": {
            str(y): {"control": _slack_dump(ARM_A, y), "arm": _slack_dump(ARM_B, y)}
            for y in YEARS
        },
    }
    OUT_PATH.write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({k: report[k] for k in (
        "flag_fidelity", "K2_control_integrity", "K4_sign", "K5_liveness"
    ) if k in report}, indent=1, default=str)[:2000])
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    main()
