"""SOCO-60: write ``calibration_attestation.json`` for the merged-hydro + boundary-repair span.

Built on :mod:`scripts.gen_soco58_attestation` (``_verify`` re-asserts every
inherited posture: price-tuning bands at the identity, no overrides / deltas /
smoothing, historic outages, ``coal_warm_committed`` with no second coal-committed
mechanism, SOCO-55's measured gas basis) and on :mod:`scripts.gen_soco_h4_attestation`
(the run-of-river entry basis and the offer-curve re-tag).

THE DELTA against the keeper on ``main`` (``2026-09-22-soco-h4-hydro-ror``), each
claim checked BY EXECUTION in :func:`verify_scope`, raising otherwise:

* **hydro** (owner ruling 2026-09-23, "merge the two recipes"):
  ``hydro_eia930_monthly=True`` with ``hydro_backfill_year=2024`` on every leg and
  ``EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025`` — SOCO-59's repair — on top of
  the keeper's ``hydro_ror_split``. The 2023 / 2024 budgets are byte-identical to
  the keeper's; 2025 equals 2025's own EIA-930 level.
* **B1, plant boundary** — ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE['SOCO']``:
  the plants the current EIA-860 recodes to FPL leave SOCO's membership, and
  EIA-930 SOCO's fossil total matches the 923 total WITHOUT them.
* **B2, gas fold** — ``EIA930_GAS_FOLD_REFUTED``: SOCO's 930 gas is at or below
  its 923 gas classes in every scored year, so no fold is subtracted.

Pre-registration: ``docs/handoffs/PRECOMMIT-soco-60b-2026-09-23.md`` (§4 and
addendum B). Usage::

    python3 scripts/gen_soco60b_attestation.py --bundle results/calibration/soco60_hydro_merged
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_soco_h4_attestation as h4  # noqa: E402
from gen_soco58_attestation import _verify as _verify_inherited  # noqa: E402

ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
#: Former Gulf Power plants that must leave SOCO's membership (B1).
GULF = {643, 641, 7715, 57502}


def verify(sc: dict, meta: dict) -> None:
    """Raise unless the bundle is the declared merged recipe off the keeper."""
    _verify_inherited(sc)
    if sc.get("hydro_ror_split") is not True or sc.get("hydro_min_flow_floor"):
        raise SystemExit("expected hydro_ror_split=True, hydro_min_flow_floor=False")
    for name in (
        "hydro_pondage_bound",
        "hydro_dispatch_envelope",
        "hydro_budget_period_by_instrument",
        "hydro_cascade_coupling",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} armed alongside hydro_ror_split (rule 19)")
    for k, v in ARM_META.items():
        if meta.get(k) != v:
            raise SystemExit(f"meta {k}={meta.get(k)!r}, expected {v!r}")


def verify_scope(
    bundle: Path,
    years: list[int],
    inert_moved: frozenset[str] = frozenset(),
    lane_added: frozenset[str] = frozenset(),
    main_rows_added: int = 0,
) -> dict:
    """Raise unless the hydro budgets, B1 and B2 are as claimed; return the evidence.

    ``inert_moved`` names extra solve-surface keys a LATER lane has classified
    INERT for SOCO in its own G-DRIFT (rule 29(b)); each must be passed
    explicitly, so the surface check never widens silently.

    ``lane_added`` names solve-surface keys a LATER lane ADDED as its own LIVE,
    declared delta (e.g. R-SOCO-B's two boundary registries): each adds one SOCO
    row and must appear in ``moved``. They are attested by that lane's own layer
    (``gen_rsocob_attestation.py``), never as inert.
    """
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    import market_sim.config.constants as K  # noqa: PLC0415
    import run_calibration_full as rcf  # noqa: PLC0415
    from lib import benchmark_semantics as bs  # noqa: PLC0415
    from market_sim.data.eia_loader import measured_monthly_hydro  # noqa: PLC0415
    from market_sim.data.hydro import build_hydro_fleet  # noqa: PLC0415
    from market_sim.data.zone_assignment import build_zone_lookup  # noqa: PLC0415

    if K.EIA930_PS_SPLIT_COMPLETE_FROM.get("SOCO") != 2025:
        raise SystemExit("EIA930_PS_SPLIT_COMPLETE_FROM['SOCO'] is not 2025")
    budgets = {}
    for y in years:
        _, ctrl = build_hydro_fleet(
            "SOCO", y, ZONES, backfill_year=2024, ror_split=True
        )
        _, arm = build_hydro_fleet(
            "SOCO", y, ZONES, backfill_year=2024, eia930_monthly=True, ror_split=True
        )
        ctrl, arm = np.asarray(ctrl, float), np.asarray(arm, float)
        if y < 2025 and not np.array_equal(ctrl, arm):
            raise SystemExit(f"{y}: merged hydro budget differs from the keeper's")
        if y >= 2025:
            target = float(np.nansum(measured_monthly_hydro("SOCO", y)))
            if abs(arm.sum() - target) > 1.0:
                raise SystemExit(
                    f"{y}: budget {arm.sum():.0f} != EIA-930 {target:.0f} MWh"
                )
        budgets[str(y)] = {
            "keeper_TWh": round(ctrl.sum() / 1e6, 4),
            "merged_TWh": round(arm.sum() / 1e6, 4),
        }

    # B1 — membership and the EIA-930 boundary test
    if K.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE != {"SOCO": True}:
        raise SystemExit("ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE is not {'SOCO': True}")
    base = set(build_zone_lookup("SOCO"))
    members = rcf._iso_plant_ids("SOCO")
    if not GULF <= base or GULF & members:
        raise SystemExit("the Gulf plants are not removed from SOCO's membership")
    dropped = sorted(base - members)
    gen = rcf.load_monthly_generation()
    boundary = {}
    for y in [y for y in years if y < 2025]:
        fs = glob.glob(str(_ROOT / f"data/raw/eia-930/EIA930_BALANCE_{y}_*.parquet"))
        cols = [
            "Balancing Authority",
            "Net Generation (MW) from Coal",
            "Net Generation (MW) from Natural Gas",
        ]
        d = pd.concat([pd.read_parquet(f, columns=cols) for f in fs])
        d = d[d["Balancing Authority"] == "SOCO"]

        def _twh(c: str) -> float:
            return float(
                pd.to_numeric(
                    d[c].astype(str).str.replace(",", ""), errors="coerce"
                ).sum()
                / 1e6
            )

        gas930, coal930 = _twh(cols[2]), _twh(cols[1])
        with_ = rcf._eia923_frame(y, gen, "SOCO")
        fos = with_[with_["klass"].str.match("^(CC_|CT_|ST_|COAL)")]
        tot = float(fos["annual_mwh"].sum()) / 1e6
        gas923 = (
            float(fos[~fos["klass"].str.startswith("COAL")]["annual_mwh"].sum()) / 1e6
        )
        ratio = (gas930 + coal930) / tot
        if not 0.97 <= ratio <= 1.03:
            raise SystemExit(
                f"{y}: 930/923 fossil {ratio:.3f} after B1 — boundary claim fails"
            )
        # B2 — 930 gas must not exceed 923 gas (no room for a fold)
        if gas930 > gas923 * 1.01:
            raise SystemExit(
                f"{y}: 930 gas {gas930:.2f} > 923 gas {gas923:.2f} — a fold is possible"
            )
        boundary[str(y)] = {
            "930_over_923_fossil": round(ratio, 3),
            "930_gas_TWh": round(gas930, 2),
            "923_gas_TWh": round(gas923, 2),
        }
    if (
        bs.gas_foldin_deflation({"OTHER": 1.0, "biomass": 9.0}, {"other": 2.0}, "SOCO")
        != 0.0
    ):
        raise SystemExit("gas_foldin_deflation is not 0 for SOCO")

    rows = (
        json.loads((bundle / "run_config.json").read_text()).get("solve_surface") or {}
    )
    if rows.get("rows") != 185 + len(lane_added) + main_rows_added or set(
        rows.get("moved") or {}
    ) != {"ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE"} | set(inert_moved) | set(
        lane_added
    ):
        raise SystemExit(
            f"bundle solve_surface {rows.get('rows')} / {rows.get('moved')}"
        )
    return {"budgets": budgets, "dropped": dropped, "boundary": boundary}


def main() -> None:
    """Verify the bundle and write its attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument(
        "--declared-inert-moved",
        action="append",
        default=[],
        metavar="KEY",
        help="a solve-surface key a later lane's G-DRIFT classified INERT for "
        "SOCO (e.g. R-SOCO: RGGI_MEMBER_STATES_BY_YEAR, no SOCO state is a "
        "member); repeatable, never implied",
    )
    ap.add_argument(
        "--lane-added-moved",
        action="append",
        default=[],
        metavar="KEY",
        help="a solve-surface key a later lane ADDED as its own live, declared "
        "delta (R-SOCO-B: EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC, "
        "ISO_BA_JOINS); adds one SOCO row each; attested by that lane's layer",
    )
    ap.add_argument(
        "--main-rows-added",
        type=int,
        default=0,
        metavar="N",
        help="solve-surface rows a cross-ISO change on main ADDED that this lane "
        "did not (soco-67: COAL-SUB added 2); each such change's moved keys are "
        "declared with --declared-inert-moved after a measured G-DRIFT; never implied",
    )
    a = ap.parse_args()
    bundle = Path(a.bundle)
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    meta = json.loads((bundle / "meta.json").read_text())
    verify(sc, meta)
    years = sorted(int(y) for y in meta["years"])
    ev = verify_scope(
        bundle,
        years,
        frozenset(a.declared_inert_moved),
        frozenset(a.lane_added_moved),
        a.main_rows_added,
    )
    print(json.dumps(ev, indent=1))
    b, bd = ev["budgets"], ev["boundary"]
    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-60 (lane). Against keeper 2026-09-22-soco-h4-hydro-ror, THREE "
            "things move, each machine-verified by execution in this script. "
            "(1) HYDRO, owner ruling 2026-09-23 ('merge the two recipes'): "
            "hydro_eia930_monthly=True with hydro_backfill_year=2024 and "
            "EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025 (SOCO-59's repair) on top of "
            "the keeper's hydro_ror_split — one pipeline, the RoR flat level read off "
            "the repinned budget (rule 19). Budgets: 2023/2024 byte-identical to the "
            f"keeper's ({b['2023']['merged_TWh']} / {b['2024']['merged_TWh']} TWh; "
            "their EIA-930 column folds pumped-storage discharge and the pin is "
            f"refused); 2025 {b['2025']['keeper_TWh']} -> {b['2025']['merged_TWh']} "
            "TWh, 2025's own clean EIA-930 level. "
            "(2) B1 PLANT BOUNDARY: ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE['SOCO'] "
            f"drops {len(ev['dropped'])} plants the current EIA-860 recodes to FPL "
            "(the former Gulf Power fleet) at the single membership seam the "
            "benchmark and the must-run injection both read. EIA-930 SOCO excludes "
            "them: 930/923 fossil after the drop reads "
            f"{bd['2023']['930_over_923_fossil']} / {bd['2024']['930_over_923_fossil']} "
            "(2023/2024); the model's own fleet census (current EIA-860 BA == SOCO) "
            "and its demand (EIA-930 SOCO demand + metered net exports = 930 SOCO net "
            "generation) never carried them. Solve-affecting only via the injection "
            "(Perdido landfill gas, ~0.015 TWh/yr biomass); SOCO's cache key moves. "
            "(3) B2 GAS FOLD: EIA930_GAS_FOLD_REFUTED={'SOCO'} — 930 SOCO gas "
            f"{bd['2023']['930_gas_TWh']} / {bd['2024']['930_gas_TWh']} TWh vs 923 gas "
            f"classes {bd['2023']['923_gas_TWh']} / {bd['2024']['923_gas_TWh']}: no "
            "room for the 6-7 TWh of biomass the deflation assumed folded; "
            "benchmark-only. "
            "RULE 1 / CHECK F: B1 and B2 are benchmark repairs that flip the sole "
            "failing row; if that were their only argument they would not be taken. "
            "They rest on six years of EIA-930 SOCO accounting, and they make three "
            "rows WORSE (COAL_PRB, COAL_BIT, 2024 CT_PEAKER) — reported at full "
            "magnitude, not absorbed. RULE 13: nothing measured about dispatch is fed "
            "back; the membership is a published plant attribute and the fold test "
            "reads EIA-930's own gas cell. RULES 21/24/25: zero free parameters, two "
            "per-ISO registry rows, no other ISO moves. GATE G17: SOCO has no price "
            "benchmark; every offer_curve_by_group band is 1.0, AUTHORIZED PRICE "
            "TUNING IS DECLARED NONE (no authorized_price_tuning key, SOCO convention)."
        ),
    }
    att["disclosures"] = {
        "precommit": "docs/handoffs/PRECOMMIT-soco-60b-2026-09-23.md",
        "benchmark_repair_moves_every_soco_run": (
            "B1/B2 change SOCO's shared bench parts, so every SOCO run's C1 reads "
            "move with this registration, not only this run's."
        ),
        "rows_made_worse": "COAL_PRB, COAL_BIT and 2024 CT_PEAKER move away from their actuals on the repaired benchmark.",
        "ror_clip_2025": "5 RoR plant-months clipped to nameplate after the 2025 repin: 5.4 GWh.",
        "eia930_wat_gap": "SOCO NG: WAT missing 2024-11-25..12-31 (1,343 h).",
        "d79_note": "ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE declared at False so SOCO's key moves.",
    }
    h4.retag(att, sc, "ror")
    fp = att["free_parameters"]
    have = {e["name"] for e in fp["entries"]}
    for name, basis in (
        (
            "ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE['SOCO']",
            "Categorical partition on the current EIA-860 plant BA code; n_scalars=0. "
            "Measured admissibility: EIA-930 SOCO fossil = 923 fossil without the "
            "recoded plants, 2019-2024.",
        ),
        (
            "EIA930_GAS_FOLD_REFUTED['SOCO']",
            "Benchmark-only; n_scalars=0. Measured: SOCO 930 gas <= 923 gas classes "
            "2019-2024, so the fold deflation's premise fails.",
        ),
        (
            "hydro_eia930_monthly",
            "SOCO-59 repair; n_scalars=0. 2025's own EIA-930 hydro-ex-PS monthly level; "
            "refused in the PS-folded years 2023/2024 by EIA930_PS_SPLIT_COMPLETE_FROM.",
        ),
    ):
        if name not in have:
            fp["entries"].append(
                {
                    "name": name,
                    "value": True,
                    "identification": "measured-physical",
                    "n_scalars": 0,
                    "basis": basis,
                }
            )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path} (n_residual={fp['n_residual']})")


if __name__ == "__main__":
    main()
