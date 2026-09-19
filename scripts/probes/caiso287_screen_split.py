"""caiso-287: split the 270.3 mean-belly-MW between the two RA-bridge screens.

ZERO LP. Everything here is arithmetic over one instrumented bundle's committed
sidecars plus a ``fleet_only`` rebuild, exactly as caiso-285 and caiso-286 were.

THE OBJECT (``docs/RESULT-caiso286-cc-start-cost-2026-09-19.md`` section 7):
270.279 mean-belly-MW pass the RA bridge's restart inequality at the incumbent
$50/MW, and the committed floor array shows those gen-hours floored by nothing.
Two screens can remove them and caiso-286 could not tell which did --

  (A) the ``startup_aware`` run screen's GAP-MERGING side effect: ``runs`` is
      rebound to ``kept_runs`` (``model/commitment.py:1114``), so a dropped run
      BETWEEN two kept runs fuses two short gaps into one long one, which raises
      ``hold_cost`` linearly in ``gap`` and, past
      ``DA_COMMITMENT_HORIZON_HOURS``, excludes the gap outright; and
  (B) the surplus DECOMMIT screen in ``_apply_economic_bridges``.

Both read the P0 dispatch in MW and the P0 duals, and no committed artifact
carried either -- which is why caiso-286's number is an upper bound. The
``--persist-p0-dispatch`` sidecar closes that, so this probe calls the
PRODUCTION detector, unmodified, in four configurations and reads the answer off
the floors it returns.

Pre-registration: ``docs/PRECOMMIT-caiso287-startup-decommit-split-2026-09-19.md``.
Every metric, gate, cut and verdict word below is fixed there, before the
instrumented replay was solved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER  # noqa: E402
from market_sim.model.commitment import (  # noqa: E402
    caiso_ra_mustoffer_min_gen,
)
from market_sim.pipeline.commitment import cc_startup_lead_hours  # noqa: E402

YEAR = 2024
T = 8760

# The keeper's armed posture, read from its own run_config.json and re-asserted
# against the probe bundle's at runtime rather than trusted (PRECOMMIT 2(d)).
KEEPER_POSTURE: dict[str, object] = {
    "caiso_ra_mustoffer": True,
    "caiso_ra_startup_bridge": True,
    "caiso_ra_bridge_decommit": True,
    "caiso_ra_bridge_startup_aware": True,
    "caiso_ra_startup_trajectory": True,
    "caiso_ra_min_load_frac": 0.26,
    "caiso_ra_mustoffer_quantity_gate": False,
    "caiso_ra_bridge_curtailment_release": False,
    # ON for this keeper, which is WHY the surplus reprice is -$20 and not 0.
    # Asserted here because the value it selects is an input to the decommit
    # screen this probe exists to measure: an early draft of this file assumed
    # 0.0 and the posture gate below caught it.
    "negative_renewable_offers": True,
    "renewable_keep_running_value": 20.0,
}
MIN_LOAD_FRAC = 0.26


def surplus_floor_value(cfg: dict) -> float:
    """The keeper's surplus reprice value, derived as production derives it.

    Mirrors ``pipeline/commitment.py:189-193`` rather than hard-coding a
    number, so the probe cannot drift from the code it is replaying.
    """
    if not cfg.get("negative_renewable_offers", False):
        return 0.0
    return -float(cfg["renewable_keep_running_value"])

BELLY = REPO / "results/calibration/_caiso285_belly_2024.json"
BELLY_SHA16 = "c5948fb0d43620a1"

# caiso-286's published census, which this rebuild must reproduce (G-R1).
EXPECT_FLEET_ROWS = 1705
#: the published actual RA min_gen belly mean, $ MW (G-R3).
EXPECT_BELLY_RA_MEAN_MW = 670.470
G_R3_TOL_MW = 0.05
#: PRE-REGISTERED cut (PRECOMMIT section 5, G-S): dominance at 70 % of R_total.
DOMINANCE_FRAC = 0.70
#: PRE-REGISTERED degenerate guard (G-0).
NO_OBJECT_MW = 10.0


def load_belly() -> np.ndarray:
    """The frozen 876-hour belly, re-verified by its own sha recipe."""
    rec = json.loads(BELLY.read_bytes())
    hours = np.asarray(rec["hours"], dtype=int)
    sha16 = hashlib.sha256(
        np.asarray(rec["hours"], dtype=np.int32).tobytes()
    ).hexdigest()[:16]
    if hours.size != 876 or sha16 != BELLY_SHA16:
        raise SystemExit(
            f"G-R1 FAIL: belly is {hours.size} h / sha {sha16}, "
            f"expected 876 / {BELLY_SHA16}"
        )
    return hours


def read_p0_dispatch(bundle: Path) -> tuple[np.ndarray, list[str]]:
    """The ``(n_gen, T)`` P0 dispatch in MW, plus its unit-id order."""
    path = bundle / "hourly" / f"p0_dispatch_{YEAR}.parquet"
    if not path.exists():
        raise SystemExit(
            f"MISSING {path}. This bundle was not solved with "
            "--persist-p0-dispatch, so the two screens cannot be replayed; "
            "that is the whole reason caiso-287 spent a shard."
        )
    df = pd.read_parquet(path).sort_values("gen_index")
    hours = int(df["n_hours"].iloc[0])
    mw = np.stack([np.frombuffer(b, dtype=np.float64) for b in df["mw"]])
    if mw.shape[1] != hours or hours != T:
        raise SystemExit(f"G-R1 FAIL: p0_dispatch is {mw.shape}, expected (*, {T})")
    return mw, [str(u) for u in df["unit_id"]]


def read_p0_prices(bundle: Path, zone_names: list[str]) -> np.ndarray:
    """The ``(n_zones, T)`` P0 duals, rows ordered to match ``zone_names``.

    The zone NAMES are read from the file rather than re-derived: on a
    ``fleet_only`` rebuild ``config.zones`` is ``None`` and a consumer that
    falls through to ``sorted(unique)`` reads every price from the wrong zone
    (the defect caiso-286 section 4 caught in its own probe).
    """
    path = bundle / "hourly" / f"p0_prices_{YEAR}.parquet"
    if not path.exists():
        raise SystemExit(f"MISSING {path} (see read_p0_dispatch).")
    df = pd.read_parquet(path)
    out = np.zeros((len(zone_names), T), dtype=float)
    for z, name in enumerate(zone_names):
        sub = df[df["zone"] == name].sort_values("hour")
        if len(sub) != T:
            raise SystemExit(
                f"G-R1 FAIL: zone {name} has {len(sub)} P0 price hours, want {T}"
            )
        idx = sub["zone_index"].unique()
        if len(idx) != 1 or int(idx[0]) != z:
            raise SystemExit(
                f"G-R1 FAIL: zone {name} carries zone_index {idx}, expected {z} "
                "— the sidecar's own row order disagrees with the fleet's."
            )
        out[z, :] = sub["price"].to_numpy()
    return out


def zone_names_from_fleet(generators, zone_idx: np.ndarray) -> list[str]:
    """The index->name map, derived from the fleet and asserted one-to-one."""
    mapping: dict[int, str] = {}
    for gen, z in zip(generators, np.asarray(zone_idx)):
        z = int(z)
        name = str(gen.zone)
        if mapping.setdefault(z, name) != name:
            raise SystemExit(
                f"G-R1 FAIL: zone index {z} carries both "
                f"{mapping[z]!r} and {name!r} — the map is not one-to-one."
            )
    if sorted(mapping) != list(range(len(mapping))):
        raise SystemExit(f"G-R1 FAIL: zone index map is not dense: {sorted(mapping)}")
    return [mapping[i] for i in range(len(mapping))]


def run_detector(
    p0_dispatch: np.ndarray,
    fleet_arrays,
    generators,
    prices: np.ndarray,
    mc_base: np.ndarray,
    startup_lead: np.ndarray | None,
    surplus_value: float,
    *,
    startup_aware: bool,
    bridge_decommit: bool,
) -> np.ndarray:
    """One call of the PRODUCTION detector, with the keeper's own arguments.

    Mirrors :func:`pipeline.commitment.caiso_ra_p1_floor_fleet` exactly --
    ``release_hours`` is ``None`` because ``caiso_ra_bridge_curtailment_release``
    is off on this keeper, and the quantity gate is off, so nothing downstream
    of the detector touches the floor.
    """
    return caiso_ra_mustoffer_min_gen(
        p0_dispatch,
        fleet_arrays,
        generators,
        MIN_LOAD_FRAC,
        p1_prices=prices,
        base_mc=mc_base,
        startup_bridge=True,
        bridge_decommit=bridge_decommit,
        surplus_floor_value=surplus_value,
        startup_aware=startup_aware,
        release_hours=None,
        startup_lead_hours=startup_lead,
    )


def belly_mean_mw(floor: np.ndarray, belly: np.ndarray, rows: np.ndarray) -> float:
    """The pre-registered metric: mean over belly hours of the CC floor total."""
    return float(floor[np.ix_(rows, belly)].sum(axis=0).mean())


def main(bundle: Path, out_path: Path) -> None:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    belly = load_belly()

    # ---- posture, re-asserted from the probe bundle's OWN run_config --------
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    posture = {k: cfg.get(k) for k in KEEPER_POSTURE}
    if posture != KEEPER_POSTURE:
        diff = {k: (KEEPER_POSTURE[k], posture[k]) for k in KEEPER_POSTURE
                if posture[k] != KEEPER_POSTURE[k]}
        raise SystemExit(f"G-R1 FAIL: posture drift (want, got): {diff}")

    # ---- the sanctioned zero-LP fleet rebuild ------------------------------
    state, meta = reconstruct_bundle_fleet(bundle, YEAR)
    generators = state["fleet"]
    fa = state["fleet_arrays"]
    mc_base = np.asarray(state["mc_base"], dtype=float)
    n_gen = len(generators)
    if n_gen != EXPECT_FLEET_ROWS:
        raise SystemExit(
            f"G-R1 FAIL: rebuilt {n_gen} rows, caiso-286 published "
            f"{EXPECT_FLEET_ROWS}"
        )

    uid = [str(g.unit_id) for g in generators]
    p0_dispatch, p0_uid = read_p0_dispatch(bundle)
    if p0_uid != uid:
        raise SystemExit("G-R1 FAIL: p0_dispatch unit ids are not the fleet's")

    zone_names = zone_names_from_fleet(generators, fa.zone_idx)
    prices = read_p0_prices(bundle, zone_names)

    fz = np.load(bundle / "floors" / f"{YEAR}_P1.npz", allow_pickle=False)
    if [str(u) for u in fz["unit_ids"]] != uid:
        raise SystemExit("G-R1 FAIL: floors unit ids are not the fleet's")
    min_gen = fz["min_gen"].astype(float)
    ra_hours = fz["mechanism"] == MECH_RA_MUSTOFFER

    startup_lead = cc_startup_lead_hours(generators, fa, "CAISO")
    surplus_value = surplus_floor_value(cfg)
    cc_rows = np.array(
        [i for i, g in enumerate(generators) if g.plant_group == "CC_REGULAR"]
    )

    # ---- the 2x2 -----------------------------------------------------------
    floors: dict[str, np.ndarray] = {}
    for label, (sa, dc) in {
        "M_both": (True, True),
        "M_sa": (True, False),
        "M_dc": (False, True),
        "M_none": (False, False),
    }.items():
        floors[label] = run_detector(
            p0_dispatch, fa, generators, prices, mc_base, startup_lead,
            surplus_value, startup_aware=sa, bridge_decommit=dc,
        )
    M = {k: belly_mean_mw(v, belly, cc_rows) for k, v in floors.items()}

    # ---- G-R2: the keeper configuration reproduces the committed floor ------
    keeper = floors["M_both"]
    on_ra = ra_hours
    exact = bool(np.array_equal(keeper[on_ra], min_gen[on_ra]))
    max_abs = float(np.max(np.abs(keeper[on_ra] - min_gen[on_ra]))) if on_ra.any() else 0.0
    # Off the RA-attributed hours another mechanism wrote the winning value, so
    # the detector's own floor may only be LOWER, never higher.
    off = ~on_ra
    n_exceed = int(np.sum(keeper[off] > min_gen[off] + 1e-9))
    g_r2 = exact and n_exceed == 0

    # ---- G-R3 --------------------------------------------------------------
    belly_ra_mean = float(np.where(ra_hours, min_gen, 0.0)[:, belly].sum(axis=0).mean())
    g_r3 = abs(belly_ra_mean - EXPECT_BELLY_RA_MEAN_MW) <= G_R3_TOL_MW

    # ---- G-S ---------------------------------------------------------------
    R_SA = M["M_none"] - M["M_sa"]
    R_DC = M["M_none"] - M["M_dc"]
    R_total = M["M_none"] - M["M_both"]
    bar = DOMINANCE_FRAC * R_total
    if R_total < NO_OBJECT_MW:
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
        "bundle": str(bundle.relative_to(REPO)),
        "year": YEAR,
        "git_sha_of_bundle": meta.get("git_sha"),
        "posture_reasserted": posture,
        "fleet_rows": n_gen,
        "cc_regular_rows": int(cc_rows.size),
        "zone_index_map": dict(enumerate(zone_names)),
        "surplus_floor_value": surplus_value,
        "belly_hours": int(belly.size),
        "belly_sha256_16": BELLY_SHA16,
        "gates": {
            "G_R1": "PASS",
            "G_R2": "PASS" if g_r2 else "FAIL",
            "G_R2_exact_on_ra_hours": exact,
            "G_R2_max_abs_diff_on_ra_hours_mw": max_abs,
            "G_R2_gen_hours_exceeding_elsewhere": n_exceed,
            "G_R3": "PASS" if g_r3 else "FAIL",
            "G_R3_belly_ra_mean_mw": belly_ra_mean,
            "G_R3_expected_mw": EXPECT_BELLY_RA_MEAN_MW,
        },
        "M_mean_belly_mw": M,
        "removals_mean_belly_mw": {
            "R_SA_startup_aware_solo": R_SA,
            "R_DC_decommit_solo": R_DC,
            "R_total_joint": R_total,
            "dominance_bar_70pct": bar,
        },
        "VERDICT": verdict,
    }
    out_path.write_text(json.dumps(rec, indent=2, default=float))

    print(json.dumps(rec["gates"], indent=2, default=float))
    print()
    for k in ("M_both", "M_sa", "M_dc", "M_none"):
        print(f"  {k:8s} = {M[k]:12.3f} mean-belly-MW")
    print()
    print(f"  R_SA (startup_aware solo) = {R_SA:10.3f}")
    print(f"  R_DC (decommit solo)      = {R_DC:10.3f}")
    print(f"  R_total (joint)           = {R_total:10.3f}   bar@70% = {bar:.3f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "bundle",
        type=Path,
        nargs="?",
        default=REPO / "results/calibration/caiso287_instr_2024",
        help="the instrumented bundle (needs hourly/p0_dispatch_<year>.parquet)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO / "results/calibration/_caiso287_screen_split.json",
    )
    a = ap.parse_args()
    main(a.bundle, a.out)
