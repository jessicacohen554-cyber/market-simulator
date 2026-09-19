"""caiso-286 — what the MEASURED CC start cost would hold in the belly. ZERO LP.

Executes ``docs/PRECOMMIT-caiso286-cc-start-cost-2026-09-19.md`` section 7
verbatim. The declared value, the mapping rule, the escalation index and both
verdict words were fixed and pushed
(``7562f345d25eb96c7785f82b201c230f00f7402f``) **before this script was
written**; nothing here selects a cut.

THE QUESTION
------------
caiso-285 closed the CAISO RA-bridge belly deficit down to one term:
``BIN_STARTUP_COST_PER_MW["CC_REGULAR"] = 50.0`` $/MW, flat across all 30 CC
plants and every gap length. Inverting the restart inequality set an arithmetic
BAR of $96.9/MW (crediting the gap energy at $0) or $115.4/MW (at the belly's
actual price). This script asks what the MEASURED value — NREL/SR-5500-55433
Table 1-1's Gas-CC **warm** median, the row the belly's own 8–22 h gap
distribution selects — actually holds.

WHAT IT READS
-------------
* ``results/calibration/_caiso285_belly_2024.json`` — the frozen 876-hour belly
  set (``sha256[:16] = c5948fb0d43620a1``), re-verified here.
* the caiso-285 instrumented bundle, recovered from its immutable SHA
  ``203124e310f7be4f806ad968d6cf5755f96bbc00``: the bit-packed P0 on/off
  pattern, the ``floors/<year>_P1.npz`` the LP actually saw, and the P1 zonal
  duals in ``hourly/system_<year>.parquet``.
* a zero-LP ``run_year(fleet_only=True)`` rebuild of the KEEPER's own 2024
  recipe through ``scripts.lib.bundle_fleet.reconstruct_bundle_fleet`` — the
  sanctioned route, as repaired at caiso-285.

WHAT IT IS AND IS NOT
---------------------
It is an UPPER BOUND, declared as one in PRECOMMIT section 7: it omits the
``startup_aware`` run screen (measured at 0.0 MW of belly coverage by
caiso-285) and the surplus decommit screen, which can only REMOVE bridges.
Both omissions push the answer UP, so an immaterial upper bound is immaterial
a fortiori.

It arms nothing, adds no ``ScenarioConfig`` field, changes no constant and is
gated on no residual (rule 1 ``[R-STRUCT]``). The response curve it prints over
other start-cost values is CONTEXT ONLY — the declared value is section 5's and
is not selected from the curve.
"""

from __future__ import annotations

import argparse
import hashlib
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
from market_sim.model.commitment import (  # noqa: E402
    _ra_bridge_unit_params,
    find_runs,
)

YEAR = 2024
T = 8760
#: the keeper's measured caiso_ra_min_load_frac (rule 23 [R-FROZEN-DERIVE])
MIN_LOAD_FRAC = 0.26
#: the keeper's armed posture, read from the bundle's own run_config
FUEL_TYPES = ("gas_cc", "gas_ct")
BRIDGE_DECOMMIT = True

BELLY = REPO / "results/calibration/_caiso285_belly_2024.json"
BELLY_SHA16 = "c5948fb0d43620a1"
PROBE_BUNDLE = REPO / "results/calibration/caiso285_instr_2024"
PROBE_BUNDLE_SHA = "203124e310f7be4f806ad968d6cf5755f96bbc00"

# --------------------------------------------------------------------------
# PRE-REGISTERED, PRECOMMIT section 5. Fixed ex ante; NEVER swept (section 8.3).
# --------------------------------------------------------------------------
#: NREL/SR-5500-55433 Table 1-1, "Gas - CC [GT+HRSG+ST]", C&M $/MW cap, CY2011$.
NREL_CC_CM_2011: dict[str, dict[str, float]] = {
    "hot": {"p25": 28.0, "median": 35.0, "p75": 56.0},
    "warm": {"p25": 32.0, "median": 55.0, "p75": 93.0},
    "cold": {"p25": 46.0, "median": 79.0, "p75": 101.0},
}
#: NREL/SR-5500-55433 Table 1-3, same column, startup fuel MMBtu/MW cap.
NREL_CC_START_FUEL_MMBTU_PER_MW: dict[str, float] = {
    "hot": 0.19,
    "warm": 0.20,
    "cold": 0.24,
}
#: Table 1-1 "Typical (Warm Start Offline Hours)", Gas-CC: 5 to 40 h.
WARM_BAND_LO_H, WARM_BAND_HI_H = 5.0, 40.0
#: CPI-U annual averages, BLS series CUUR0000SA0 (cross-checked vs FRED CPIAUCNS).
CPI_2011, CPI_2024 = 224.939, 313.689
#: the keeper's own 2024 CAISO gas price, $/MMBtu (bundle meta.json).
GAS_PRICE_2024 = 2.19
#: the caiso-285 bar, by inversion of the restart inequality. NOT a target.
BAR_AT_ZERO = 96.9
BAR_AT_PRICE = 115.4
#: PRE-REGISTERED materiality cut (PRECOMMIT section 7): 10 % of the deficit.
CC_BELLY_DEFICIT_MW = 1921.4
MATERIAL_AT_MW = 192.1
#: the model's incumbent flat value, for the G-C reproduction leg.
INCUMBENT_STARTUP_PER_MW = 50.0
#: caiso-285 section 6's UNIFORM gap prices, re-evaluated on the same gap set so
#: its "share of belly MW that fails" can be compared with the per-gap basis the
#: model code actually uses. Its published shares are 0.9988 and 1.0000.
UNIFORM_PRICES: dict[str, float] = {"at_zero": 0.0, "at_belly_mean_-6.71": -6.71}


def start_type_for_gap(gap_hours: float) -> str:
    """PRECOMMIT section 5 mapping rule, fixed before the arithmetic was run."""
    if gap_hours < WARM_BAND_LO_H:
        return "hot"
    if gap_hours <= WARM_BAND_HI_H:
        return "warm"
    return "cold"


def declared_value(
    start_type: str, centile: str = "median", escalate: bool = True
) -> float:
    """The PRECOMMIT section 5 construction: C&M (escalated) + start fuel."""
    cm = NREL_CC_CM_2011[start_type][centile]
    if escalate:
        cm *= CPI_2024 / CPI_2011
    fuel = NREL_CC_START_FUEL_MMBTU_PER_MW[start_type] * GAS_PRICE_2024
    return cm + fuel


def unpack_p0(path: Path, n_gen: int) -> tuple[np.ndarray, list[str]]:
    """Return the ``(n_gen, T)`` P0 on/off boolean and its unit-id order."""
    frame = pd.read_parquet(path).sort_values("gen_index")
    bits = np.stack(
        [np.frombuffer(b, dtype=np.uint8) for b in frame["on_bits"].to_numpy()]
    )
    on = np.unpackbits(bits, axis=1)[:, :T].astype(bool)
    if on.shape[0] != n_gen:
        raise SystemExit(
            f"G-C FAIL: p0_commitment has {on.shape[0]} rows, fleet has {n_gen}"
        )
    return on, [str(u) for u in frame["unit_id"]]


def zone_names_by_index(generators, zone_idx: np.ndarray) -> list[str]:
    """Return zone names positionally indexed by ``zone_idx``.

    Derived from the generators' OWN ``zone`` attribute rather than from any
    sorted or configured list. An earlier draft of this probe read
    ``config.zones``, which is ``None`` on a ``fleet_only`` rebuild, and fell
    through to ``sorted(unique)`` — putting ``LA_BASIN`` at index 0 where the
    fleet means ``NP15``, so every gap LMP came from the wrong zone. The
    mapping is asserted one-to-one here so that failure mode cannot recur.
    """
    seen: dict[int, set[str]] = {}
    for i, gen in enumerate(generators):
        z = getattr(gen, "zone", None)
        if z:
            seen.setdefault(int(zone_idx[i]), set()).add(str(z))
    if not seen or any(len(v) != 1 for v in seen.values()):
        raise SystemExit(f"G-C FAIL — zone_idx is not one-to-one with zone: {seen}")
    if sorted(seen) != list(range(len(seen))):
        raise SystemExit(f"G-C FAIL — zone_idx is not dense from 0: {sorted(seen)}")
    return [next(iter(seen[i])) for i in range(len(seen))]


def zonal_prices(bundle: Path, zone_names: list[str]) -> np.ndarray:
    """Return the ``(n_zones, T)`` P1 dual, rows ordered by ``zone_names``."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{YEAR}.parquet")
    df = df[df["pass"] == "P1"]
    missing = set(zone_names) - set(df["zone"].unique())
    if missing:
        raise SystemExit(
            f"G-C FAIL: zones {sorted(missing)} absent from system parquet"
        )
    out = np.zeros((len(zone_names), T), dtype=float)
    for z, name in enumerate(zone_names):
        sub = df[df["zone"] == name].sort_values("hour")
        if len(sub) != T:
            raise SystemExit(f"G-C FAIL: zone {name} has {len(sub)} P1 hours, want {T}")
        out[z, :] = sub["price"].to_numpy()
    return out


def main(out_path: Path) -> None:
    # ---- the frozen belly, re-verified rather than trusted ------------------
    raw = BELLY.read_bytes()
    belly_rec = json.loads(raw)
    belly = np.asarray(belly_rec["hours"], dtype=int)
    if belly.size != 876:
        raise SystemExit(f"belly set is {belly.size} hours, expected 876")
    # the recipe the belly record itself names: ``sha256_int32_le``
    sha16 = hashlib.sha256(
        np.asarray(belly_rec["hours"], dtype=np.int32).tobytes()
    ).hexdigest()[:16]

    # ---- the sanctioned zero-LP fleet rebuild (PRECOMMIT section 7 step 2) --
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, meta = reconstruct_bundle_fleet(PROBE_BUNDLE, YEAR)
    generators = state["fleet"]
    fa = state["fleet_arrays"]
    mc_base = np.asarray(state["mc_base"], dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    zone_idx = np.asarray(fa.zone_idx)
    heat_rate = np.asarray(fa.heat_rate, dtype=float)
    n_gen = len(generators)

    # ---- G-C: row alignment, re-asserted not assumed -----------------------
    on, p0_uid = unpack_p0(
        PROBE_BUNDLE / "hourly" / f"p0_commitment_{YEAR}.parquet", n_gen
    )
    uid = [str(g.unit_id) for g in generators]
    fz = np.load(PROBE_BUNDLE / "floors" / f"{YEAR}_P1.npz", allow_pickle=False)
    fl_uid = [str(u) for u in fz["unit_ids"]]
    gc = {
        "fleet_rows": n_gen,
        "p0_vs_fleet_unit_ids_identical": p0_uid == uid,
        "floors_vs_fleet_unit_ids_identical": fl_uid == uid,
        "belly_sha256_16": sha16,
        "belly_sha_matches_caiso285": sha16 == BELLY_SHA16,
    }
    if not (
        gc["p0_vs_fleet_unit_ids_identical"]
        and gc["floors_vs_fleet_unit_ids_identical"]
    ):
        raise SystemExit(f"G-C FAIL — unit-id alignment: {gc}")

    min_gen = fz["min_gen"].astype(np.float32)
    mech = fz["mechanism"]
    ra_held = (mech == MECH_RA_MUSTOFFER) & (min_gen > 0.0)

    zone_names = zone_names_by_index(generators, zone_idx)
    gc["zone_index_map"] = dict(enumerate(zone_names))
    prices = zonal_prices(PROBE_BUNDLE, zone_names)

    # ---- the exhaustive gap scan (PRECOMMIT section 7 steps 3-4) -----------
    # Candidate start costs. The DECLARED value is `warm/median/escalated`
    # (PRECOMMIT section 5); everything else on this list is CONTEXT ONLY and
    # is never selected from (PRECOMMIT section 8.3).
    candidates: dict[str, float] = {
        "incumbent_flat_50": INCUMBENT_STARTUP_PER_MW,
        "DECLARED_warm_median_2024usd": declared_value("warm"),
        "context_warm_median_2011usd": declared_value("warm", escalate=False),
        "context_hot_median_2024usd": declared_value("hot"),
        "context_cold_median_2024usd": declared_value("cold"),
        "context_warm_p25_2024usd": declared_value("warm", "p25"),
        "context_warm_p75_2024usd": declared_value("warm", "p75"),
        "context_bar_at_zero": BAR_AT_ZERO,
        "context_bar_at_price": BAR_AT_PRICE,
    }
    held = {k: 0.0 for k in candidates}
    held_cc = {k: 0.0 for k in candidates}
    uniform_fail_mw = {k: 0.0 for k in UNIFORM_PRICES}
    at_stake_mw = 0.0
    incumbent_pass_mw = [0.0]
    incumbent_pass_other_floor_mw = [0.0]
    gaps_rows: list[dict] = []
    belly_set = np.zeros(T, dtype=bool)
    belly_set[belly] = True

    n_elig = n_cc_elig = 0
    for g, gen in enumerate(generators):
        if gen.plant_group.endswith("_CHP") or gen.fuel_type not in FUEL_TYPES:
            continue
        resolved = _ra_bridge_unit_params(gen, float(heat_rate[g]))
        if resolved is None:
            continue
        min_down, startup_incumbent = resolved
        econ_eligible = (
            startup_incumbent > 0.0 and min_down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS
        )
        n_elig += 1
        is_cc = gen.plant_group == "CC_REGULAR"
        if is_cc:
            n_cc_elig += 1
        if not econ_eligible:
            continue

        is_bin = getattr(gen, "is_campd_bin", False)
        if is_bin:
            key = gen.unit_id.rpartition("_")[0]
            floor_pmax = sum(
                float(pmax[j])
                for j, gg in enumerate(generators)
                if getattr(gg, "is_campd_bin", False)
                and gg.unit_id.rpartition("_")[0] == key
            )
        else:
            floor_pmax = float(pmax[g])
        target_mw = min(MIN_LOAD_FRAC * floor_pmax, float(pmax[g]))
        zone = int(zone_idx[g])

        runs = find_runs(on[g, :])
        if len(runs) < 2:
            continue
        for (_, end_prev), (start_next, _) in zip(runs[:-1], runs[1:]):
            gap = start_next - end_prev
            if gap <= 0 or gap < min_down:
                continue  # sub-min-down gaps are physically bridged already
            if BRIDGE_DECOMMIT and gap > DA_COMMITMENT_HORIZON_HOURS:
                continue  # S2: the DA horizon, a separate closed object
            sl = slice(end_prev, start_next)
            in_belly = belly_set[sl]
            if not in_belly.any():
                continue
            mc_gap = float(np.mean(mc_base[g, sl]))
            lmp_gap = float(np.mean(prices[zone, sl]))
            hold_cost = (mc_gap - lmp_gap) * MIN_LOAD_FRAC * gap
            # the MW the LP would actually write, on belly hours the unit is
            # available and neither already held nor already online
            newly = in_belly & (avail[g, sl] > 0.0) & ~ra_held[g, sl] & ~on[g, sl]
            mw = float(np.sum(target_mw * avail[g, sl][newly]))
            # Does another mechanism already floor these hours? ``mechanism``
            # records ONE winning id per gen-hour, so an hour the bridge acted
            # on could be attributed to a higher-writing mechanism instead.
            # Measured rather than waved at, because the whole "the solve held
            # none of it" claim below turns on it.
            other = newly & (min_gen[g, sl] > 0.0)
            if INCUMBENT_STARTUP_PER_MW > hold_cost:
                incumbent_pass_mw[0] += mw
                incumbent_pass_other_floor_mw[0] += float(
                    np.sum(target_mw * avail[g, sl][other])
                )
            for name, val in candidates.items():
                if val > hold_cost:
                    held[name] += mw
                    if is_cc:
                        held_cc[name] += mw
            # caiso-285 section 6 cross-check: its threshold table applied ONE
            # uniform price to every gap (the belly mean), where the code uses
            # each gap's OWN mean LMP. Recomputed here on the same gap set so
            # the two statistics can be compared rather than conflated.
            at_stake_mw += mw
            for uname, uprice in UNIFORM_PRICES.items():
                u_hold = (mc_gap - uprice) * MIN_LOAD_FRAC * gap
                if INCUMBENT_STARTUP_PER_MW <= u_hold:
                    uniform_fail_mw[uname] += mw
            gaps_rows.append(
                {
                    "unit_id": gen.unit_id,
                    "plant_group": gen.plant_group,
                    "gap_hours": int(gap),
                    "start_type": start_type_for_gap(gap),
                    "mc_gap": round(mc_gap, 4),
                    "lmp_gap": round(lmp_gap, 4),
                    "hold_cost_per_mw": round(hold_cost, 4),
                    "belly_mw_at_stake": round(mw, 4),
                }
            )

    n_belly = float(belly.size)
    report = {
        "lane": "caiso-286",
        "precommit": "docs/PRECOMMIT-caiso286-cc-start-cost-2026-09-19.md",
        "precommit_sha": "7562f345d25eb96c7785f82b201c230f00f7402f",
        "probe_bundle": str(PROBE_BUNDLE.relative_to(REPO)),
        "probe_bundle_recovered_from_sha": PROBE_BUNDLE_SHA,
        "year": YEAR,
        "G_C_reproduction": gc,
        "population": {
            "bridge_eligible_rows": n_elig,
            "econ_eligible_CC_REGULAR_rows": n_cc_elig,
        },
        "declared_value_usd_per_mw": round(declared_value("warm"), 4),
        "bar_at_zero_usd_per_mw": BAR_AT_ZERO,
        "bar_at_price_usd_per_mw": BAR_AT_PRICE,
        "G_A_bar_test": (
            "CLEARS" if declared_value("warm") >= BAR_AT_ZERO else "BELOW THE BAR"
        ),
        "candidate_start_costs_usd_per_mw": {
            k: round(v, 4) for k, v in candidates.items()
        },
        "G_B_mean_belly_mw_held_UPPER_BOUND": {
            k: round(v / n_belly, 4) for k, v in held.items()
        },
        "G_B_mean_belly_mw_held_CC_REGULAR_UPPER_BOUND": {
            k: round(v / n_belly, 4) for k, v in held_cc.items()
        },
        "G_B_materiality": {
            "cc_belly_deficit_mw": CC_BELLY_DEFICIT_MW,
            "material_at_mw": MATERIAL_AT_MW,
            "declared_held_cc_mw": round(
                held_cc["DECLARED_warm_median_2024usd"] / n_belly, 4
            ),
            "verdict": (
                "MATERIAL"
                if held_cc["DECLARED_warm_median_2024usd"] / n_belly >= MATERIAL_AT_MW
                else "IMMATERIAL"
            ),
        },
        # --- DISCLOSED, NOT SUBSTITUTED (the caiso-285 precedent) -----------
        # The pre-registered statistic above is a LEVEL. The bound's looseness
        # is measurable at the incumbent value, where the solve's own floors
        # say the true answer is zero, so both are reported and neither is
        # quietly swapped for the other.
        "bound_looseness_calibration": {
            "note": (
                "At the INCUMBENT $50 the same upper bound scores a non-zero "
                "level, while the committed floors show the solve held none of "
                "it. That difference is the combined effect of the two screens "
                "this bound omits (startup_aware gap-merging and the surplus "
                "decommit screen), measured rather than assumed."
            ),
            "upper_bound_at_incumbent_mw": round(
                held_cc["incumbent_flat_50"] / n_belly, 4
            ),
            "actual_ra_held_mean_belly_mw": round(
                float(np.sum(min_gen[:, belly][ra_held[:, belly]])) / n_belly, 4
            ),
            "s35_belly_mw_at_stake_availability_weighted": round(
                at_stake_mw / n_belly, 4
            ),
            "increment_over_incumbent_mw": round(
                (held_cc["DECLARED_warm_median_2024usd"] - held_cc["incumbent_flat_50"])
                / n_belly,
                4,
            ),
            "incumbent_pass_mw_floored_by_ANOTHER_mechanism": round(
                incumbent_pass_other_floor_mw[0] / n_belly, 4
            ),
            "incumbent_pass_mw_floored_by_NOTHING": round(
                (incumbent_pass_mw[0] - incumbent_pass_other_floor_mw[0]) / n_belly, 4
            ),
        },
        "caiso285_uniform_price_crosscheck": {
            "note": (
                "caiso-285 section 6 applied ONE uniform price to every gap; the "
                "code uses each gap's own mean LMP. Same gap set, both bases."
            ),
            "published_share_failing": {"at_zero": 0.9988, "at_belly_mean_-6.71": 1.0},
            "reproduced_share_failing_uniform_basis": {
                k: (round(v / at_stake_mw, 4) if at_stake_mw else None)
                for k, v in uniform_fail_mw.items()
            },
            "share_failing_PER_GAP_basis_at_incumbent": (
                round(1.0 - held_cc["incumbent_flat_50"] / at_stake_mw, 4)
                if at_stake_mw
                else None
            ),
        },
        "gap_start_type_census": {
            st: {
                "n_gaps": sum(1 for r in gaps_rows if r["start_type"] == st),
                "belly_mw_at_stake": round(
                    sum(
                        r["belly_mw_at_stake"]
                        for r in gaps_rows
                        if r["start_type"] == st
                    )
                    / n_belly,
                    4,
                ),
            }
            for st in ("hot", "warm", "cold")
        },
        "n_gaps_scanned": len(gaps_rows),
        "gaps_CONTEXT_ONLY": sorted(gaps_rows, key=lambda r: -r["belly_mw_at_stake"])[
            :60
        ],
    }
    out_path.write_text(json.dumps(report, indent=1))
    printable = {k: v for k, v in report.items() if k != "gaps_CONTEXT_ONLY"}
    print(json.dumps(printable, indent=1))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out", default="results/calibration/_caiso286_start_cost_coverage.json"
    )
    a = ap.parse_args()
    main(REPO / a.out)
