"""pjm-h7 phase 0 — the JOINT arm (committed measured basis + re-centred gas_mid), ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.
Rebuilds the PJM keeper's fleet on its own ``meta.json`` recipe via
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
(``run_year(..., fleet_only=True)``) FOUR times per year and measures the gates on
the assembled P0 objective array ``mc_base``:

* **CTL**   — the keeper recipe as registered.
* **ARM_C** — ``committed_band_measured_basis=True`` (the pjm-h6 arm, KILLED alone
  at the 2023 screen by G-4; re-measured here only as the joint arm's first half).
* **ARM_G** — ``coal_bit_passthrough_gas_mid = 4.58`` alone (the re-centring).
* **ARM_J** — BOTH. This is the arm under test.

WHY THE JOINT FORM IS THE OBJECT (rule 19 ``[R-ONE-MECH]``): pjm-h6 measured that
the registered committed multiplier 0.548 was silently carrying 26.3 TWh, and named
the econ-band sigmoid's mis-grounded centre as what it was carrying. The two halves
move coal in OPPOSITE directions -- the measured committed basis makes the min-load
block DEARER, the re-centred sigmoid makes the incremental bands CHEAPER -- so
neither can be screened alone. h6 proved that empirically by screening one alone.

THE OPERAND IS DERIVED, NEVER CHOSEN (rule 21 ``[R-DOF]``). 4.58 is the
model-consistent coal-vs-gas-CC merit crossover implied by the model's OWN measured
EIA-923 delivered coal (2.786 $/MMBtu, 243 DIRECT rows cap-wtd, pjm-170 2.1) through
``derive_coal_sigmoid.py``'s own construction ``gas_mid = deliv x COAL_HR / CC_HR``.
The other two candidates are refused on stated grounds, not on score: the LIVE 3.40
has NO derivation anywhere in the codebase, and the derive-script-at-HEAD 7.08 rests
on an ACR f.o.b. reconstruction pjm-170 measured +54.6% over the model's own
receipts (rule 14 ``[R-ACCURATE]`` bars transcribing it). Nothing here is swept.

Run: ``python3 scripts/probes/_pjm_h7_gasmid_joint.py 2020 2021 ...``
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]

#: PJM's keeper is PARTITIONED: 2020-2022 solve the `pjm_d4_4_TP` recipe,
#: 2023-2025 the `pjm_d4_4_A` carve-out. Each leg is built on its OWN year's
#: recipe, so no cross-partition config ever enters a diff.
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}

#: The DERIVED operand. Not a candidate among several -- see the module docstring.
GAS_MID_ARM = 4.58
GAS_MID_LIVE = 3.40

ARMS = ("CTL", "ARM_C", "ARM_G", "ARM_J")


def build(year: int, arm: str) -> dict:
    """Build the keeper's fleet for *year* under one *arm*. ZERO LP."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    # Declared simplification, inherited from pjm-h4 2 / pjm-h6 2 where it was
    # VERIFIED rather than asserted: self-cancelling because every leg of every
    # diff below carries it identically.
    kw["pjm_da_virtual_bids"] = False

    if arm in ("ARM_C", "ARM_J"):
        kw["committed_band_measured_basis"] = True
    if arm in ("ARM_G", "ARM_J"):
        bo = dict(kw.get("bit_overrides") or {})
        bo["coal_bit_passthrough_gas_mid"] = GAS_MID_ARM
        kw["bit_overrides"] = bo

    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _band(unit_id: str) -> str:
    tail = unit_id.rsplit("_", 1)[-1]
    return "econ" if tail.startswith("econc") else tail


def _frame(res: dict) -> pd.DataFrame:
    mc = np.asarray(res["mc_base"], dtype=float)
    fleet = res["fleet"]
    return pd.DataFrame(
        {
            "unit_id": [g.unit_id for g in fleet],
            "plant": [int(g.plant_code) for g in fleet],
            "group": [g.efficiency_bin for g in fleet],
            "fuel": [g.fuel_type for g in fleet],
            "band": [_band(g.unit_id) for g in fleet],
            "cap": [float(g.pmax_mw) for g in fleet],
            "hr": [float(g.heat_rate) for g in fleet],
            "mc_mean": mc.mean(axis=1) if mc.ndim == 2 else mc,
        }
    )


def _capwtd(df: pd.DataFrame, col: str) -> float:
    if df.empty or df["cap"].sum() == 0:
        return 0.0
    return float((df[col] * df["cap"]).sum() / df["cap"].sum())


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023]
    out: dict = {"gas_mid_live": GAS_MID_LIVE, "gas_mid_arm": GAS_MID_ARM, "years": {}}

    for y in years:
        t0 = time.time()
        res = {a: build(y, a) for a in ARMS}
        frames = {a: _frame(res[a]) for a in ARMS}
        ctl = frames["CTL"]

        # ---- G-0: the resolved sigmoid params, read off the model's OWN resolver.
        from market_sim.data.fuel.trajectories import (
            _gas_series,
            _sigmoid_passthrough,
            coal_sigmoid_params,
        )

        p_ctl = coal_sigmoid_params(res["CTL"]["config"], "bituminous")
        p_arm = coal_sigmoid_params(res["ARM_J"]["config"], "bituminous")
        gas = np.asarray(_gas_series(res["CTL"]["config"], y, 8760), dtype=float)
        pt_ctl = _sigmoid_passthrough(
            gas, p_ctl["floor"], p_ctl["ceil"], p_ctl["gas_mid"], p_ctl["gas_slope"]
        )
        pt_arm = _sigmoid_passthrough(
            gas, p_arm["floor"], p_arm["ceil"], p_arm["gas_mid"], p_arm["gas_slope"]
        )

        yr: dict = {
            "bundle": BUNDLE_FOR_YEAR[y],
            "gas_mean": float(gas.mean()),
            "params_ctl": dict(p_ctl),
            "params_arm": dict(p_arm),
            # G-2 leg (i): the arm resolves the DERIVED operand exactly, and
            # nothing else in the curve moves.
            "identity_gas_mid_dev": abs(float(p_arm["gas_mid"]) - GAS_MID_ARM),
            "identity_other_params_move": {
                k: abs(float(p_arm[k]) - float(p_ctl[k]))
                for k in ("floor", "ceil", "gas_slope")
            },
            "passthrough_mean_ctl": float(pt_ctl.mean()),
            "passthrough_mean_arm": float(pt_arm.mean()),
            "passthrough_mean_delta": float(pt_arm.mean() - pt_ctl.mean()),
            "arms": {},
        }

        # ---- structural invariants shared by every leg (fleet identity)
        for a in ARMS[1:]:
            f = frames[a]
            assert list(f["unit_id"]) == list(ctl["unit_id"]), (y, a, "unit_id order")
            assert np.allclose(f["cap"], ctl["cap"], atol=0, rtol=0), (y, a, "pmax")

        # ---- per-arm confinement + magnitude
        for a in ARMS[1:]:
            f = frames[a]
            d = f["mc_mean"].to_numpy() - ctl["mc_mean"].to_numpy()
            moved = np.abs(d) > 1e-9
            sub = ctl.assign(d=d)[moved]
            by_band = {
                str(b): {
                    "rows": int(len(g)),
                    "mw": round(float(g["cap"].sum()), 3),
                    "d_capwtd": round(_capwtd(g, "d"), 4),
                }
                for b, g in sub.groupby("band")
            }
            coal = ctl.assign(d=d)[ctl["fuel"] == "coal"]
            yr["arms"][a] = {
                "rows_moved": int(moved.sum()),
                "rows_total": int(len(ctl)),
                "bands_moved": sorted(sub["band"].unique().tolist()),
                "groups_moved": sorted(sub["group"].unique().tolist()),
                "by_band": by_band,
                "coal_all_capwtd": round(_capwtd(coal, "d"), 4),
                "fleet_capwtd": round(_capwtd(ctl.assign(d=d), "d"), 4),
                # absolute $-MW footprint: the rule-29 screen-year metric
                "footprint_mw_dollar": round(
                    float((np.abs(d) * ctl["cap"].to_numpy()).sum()), 1
                ),
            }

        # ---- G-2 leg (ii): THE ORTHOGONALITY IDENTITY, pre-registered.
        # Under REPLACE the committed band has NO sigmoid, so the re-centred
        # gas_mid CANNOT reach it; and gas_mid touches only the sigmoid, so it
        # cannot reach a committed row under ARM_J. The exact predictions are:
        #   ARM_J == ARM_C on every `committed` row   (gas_mid is inert there)
        #   ARM_J == ARM_G on every non-committed row (the basis is inert there)
        dJ = frames["ARM_J"]["mc_mean"].to_numpy() - ctl["mc_mean"].to_numpy()
        dC = frames["ARM_C"]["mc_mean"].to_numpy() - ctl["mc_mean"].to_numpy()
        dG = frames["ARM_G"]["mc_mean"].to_numpy() - ctl["mc_mean"].to_numpy()
        is_c = (ctl["band"] == "committed").to_numpy()
        # The two legs above are the PASS/FAIL identity. Superposition is
        # DELIBERATELY expected to FAIL, and its residual is the mechanism's own
        # overlap: ARM_G reaches the coal `committed` rows (the sigmoid is still
        # live there without REPLACE) while ARM_J cannot, so dC + dG
        # double-counts exactly those rows. The exact prediction, checked:
        #     dJ - (dC + dG) == -dG on coal committed rows, 0.0 everywhere else.
        # That is the arithmetic statement of rule 19 [R-ONE-MECH]: the halves
        # are not separable, which is why h6 could not screen one alone.
        is_coal_c = is_c & (ctl["fuel"] == "coal").to_numpy()
        resid = dJ - (dC + dG)
        yr["orthogonality"] = {
            "max_dev_J_vs_C_on_committed": float(np.abs(dJ - dC)[is_c].max()),
            "max_dev_J_vs_G_off_committed": float(np.abs(dJ - dG)[~is_c].max()),
            "max_dev_superposition_all": float(np.abs(resid).max()),
            "overlap_resid_vs_minus_dG_on_coal_committed": float(
                np.abs(resid[is_coal_c] + dG[is_coal_c]).max()
            ),
            "overlap_resid_off_coal_committed": float(np.abs(resid[~is_coal_c]).max()),
            "overlap_rows": int(is_coal_c.sum()),
            "overlap_mw": round(float(ctl["cap"].to_numpy()[is_coal_c].sum()), 3),
        }
        yr["seconds"] = round(time.time() - t0, 1)
        out["years"][y] = yr
        print(
            f"{y}: gas {gas.mean():6.3f}  passthrough {pt_ctl.mean():.4f} -> "
            f"{pt_arm.mean():.4f}  |  ARM_J coal {yr['arms']['ARM_J']['coal_all_capwtd']:+8.4f} "
            f"(C {yr['arms']['ARM_C']['coal_all_capwtd']:+8.4f}  G "
            f"{yr['arms']['ARM_G']['coal_all_capwtd']:+8.4f})  "
            f"ortho {max(yr['orthogonality'].values()):.2e}  [{yr['seconds']}s]",
            flush=True,
        )

    dest = REPO / "results/calibration/_pjm_h7_joint_phase0.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # MERGE, never clobber. Reported by the pjm-h7 screen shard: a single-year
    # invocation used to overwrite a full six-year artifact at this fixed path,
    # silently destroying evidence a rule-31 [R-RETAIN] lane still needed. Years
    # this run re-measured win; every other year already on disk survives.
    if dest.exists():
        try:
            prior = json.loads(dest.read_text())
        except (OSError, json.JSONDecodeError):
            prior = {}
        merged = dict(prior.get("years") or {})
        merged.update({str(k): v for k, v in out["years"].items()})
        out["years"] = merged
    out["years"] = {str(k): out["years"][k] for k in sorted(out["years"], key=int)}
    dest.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"\nwrote {dest.relative_to(REPO)} (years {sorted(out['years'], key=int)})")


if __name__ == "__main__":
    main()
