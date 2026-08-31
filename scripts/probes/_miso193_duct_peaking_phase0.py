"""miso-193 phase-0 census: ``cc_duct_peaking`` on the MISO keeper (zero-solve).

Charter: the miso-192-corrected queue's first named candidate — matrix row
``cc_duct_peaking`` (+ companion ``cc_duct_peaking_cap_pct``), MISO cell U with
no evidence note. This probe is the rule-frozen phase-0 census the charter
requires committed and pushed BEFORE any adjudicating quantity is computed.

PREMISE CORRECTION (measured before this rule froze, from committed artifacts
only — no census quantity was computed):
  - The handoff charters the lever as un-armed in MISO ("replacing the offer
    curve's class-wide pct_peaking") with A/B arm = ``cc_duct_peaking`` only.
    That premise is STALE: the designated keeper ``2026-08-30-miso-191-bexit``
    (bundle ``results/calibration/miso191_bax_B``) records
    ``cc_duct_peaking=True``, ``cc_duct_peaking_cap_pct=None`` and
    ``cc_peaking_per_plant=True`` in its ``run_config.json`` — the mechanism
    has been armed on every MISO default run since the 2026-07 G-26/C-12
    generalization (``pipeline/backcast_config.py``). The handoff's arm is
    value-identical to its own control and impossible as a single delta.
  - NYISO's K on this row is a REGISTRATION K (nyiso-115 shared-field census:
    "armed on NYISO's own designated keeper... registration, not
    adjudication"). MISO's U therefore means armed-but-never-EXAMINED, and
    what phase 0 adjudicates is (a) whether the armed mechanism is LIVE and
    MATERIAL on MISO's own fleet, and (b) whether the one genuinely untested
    single delta — the charter's own ~8% F-class supplementary-firing physical
    cap, ``cc_duct_peaking_cap_pct=8.0``, armed at PJM and None here — is
    worth an A/B. The cap is not a fit: the raw EIA-860 nameplate-vs-net-summer
    gap conflates the ambient summer derate with the duct increment (the
    field's own docstring, scenarios.py), and MISO already carries the ambient
    half through the armed ``summer_derate_basis_aware`` (miso-148), so the
    uncapped band sizes the expensive tranche from a conflated quantity.

FROZEN ADJUDICATION RULE (ex ante; the miso-191 mis-freeze lesson applied —
every quantity derives from the SAME bases the mechanism reads at solve time,
witnesses are RELATIONAL and procedurally selected, no plant is named and no
numeric witness is frozen from a foreign basis):

  Bases: (i) ``fleet.cc_duct_peaking_pct()`` — the exact map the load-bearing
  seam reads (``eia860_generator_operable.parquet``, Technology == "Natural
  Gas Fired Combined Cycle"); (ii) the load-bearing fleet build itself under
  the keeper's reconstructed ``ScenarioConfig`` (``load_fleet_from_csv`` →
  ``fleet_to_bins`` → ``bins_to_fleet``, MISO topology zones), run three ways:
  KEEPER (as recorded), NODUCT (``cc_duct_peaking=False``; the CAMPD
  tranche-artifact / class-default counterfactual the seam falls back to) and
  CAPPED (``cc_duct_peaking_cap_pct=8.0``). Per-(plant, group) peak-band MW is
  the Σ pmax of tranches whose band suffix starts with "peak".

  A1 LIVENESS: for every model CC row (CC_REGULAR/CC_CHP) whose plant_code is
  in the duct map, require |Σ peak-tranche MW − capacity_mw × duct_pct/100|
  ≤ max(1.0 MW, 0.6% of capacity_mw) on the KEEPER build. LIVE iff conforming
  MW ≥ 99% of covered CC MW. NOT LIVE ⇒ the armed flag is seam-clobbered (the
  nyiso-146b/148 defect class): the session pivots to a bug finding; no lever
  A/B is chartered.

  A2 COVERAGE (the miso-141 §11.2 / miso-192 50% line, declared ex ante): the
  duct map must cover ≥ 50% of MISO CC class MW (CC_REGULAR + CC_CHP,
  bins capacity basis). Below the line ⇒ no A/B; the cell is stamped from this
  census alone (armed but reaching under half the class) and the finding says
  so at full magnitude.

  A3 CAP-ARM MATERIALITY: the A/B (control = keeper replay; arm =
  ``cc_duct_peaking_cap_pct=8.0``, single delta) is chartered iff A1 ∧ A2 AND
  the cap's static clip — Σ over duct-flagged covered rows of
  capacity_mw × max(0, duct_pct − 8.0)/100, equivalently the KEEPER→CAPPED
  peak-band MW fall — is ≥ 1% of duct-flagged covered CC MW. Below ⇒ the cap
  arm is statically ≈inert: mint I for the cap leg zero-solve (miso-179
  precedent), stamp the cell from the census, STOP.

  DIRECTIONAL PREREG (miso-148 P5 pattern, declared before any quantity):
  if the A/B is chartered, prediction = model mean LMP moves DOWN (C3a-2025
  more negative, ADVERSE to the −12.3405% gap), confidence 0.8. Mechanism:
  the cap only ever shrinks the expensive top band (monotone softening of the
  supply curve top; the miso-186 Leg M above-clearing tranche MW re-prices
  into the econ band). Reported at full magnitude whichever way it goes.

  Reported, never gated: MW moved in each direction vs NODUCT (zero-band
  plants where the class default currently gives a band; band-growth plants),
  the gap distribution, and the count of plants the 8% cap clips.

Rule 21 [R-DOF]: this probe has zero free parameters; the 50% / 1% / 99% /
0.6%-or-1MW lines are ex-ante adjudication thresholds of the census, not solve
inputs. Rule 13: every input regenerates for a forward year from the same
published EIA-860 sheet.

Output: ``results/calibration/_miso193_duct_peaking_phase0.json``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    bins_to_fleet,
    fleet_to_bins,
    load_fleet_from_csv,
)
from market_sim.data.fleet.campd_bins import cc_duct_peaking_pct  # noqa: E402

_BUNDLE = _REPO / "results" / "calibration" / "miso191_bax_B"
_OUT = _REPO / "results" / "calibration" / "_miso193_duct_peaking_phase0.json"
_CC_GROUPS = ("CC_REGULAR", "CC_CHP")


def keeper_config() -> tuple[ScenarioConfig, list[str]]:
    """Reconstruct the keeper's ScenarioConfig from its committed run_config."""
    sc = json.load(open(_BUNDLE / "run_config.json"))["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    dropped = sorted(set(sc) - fields)
    cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})
    assert cfg.cc_duct_peaking is True, "premise: keeper arms cc_duct_peaking"
    assert cfg.cc_duct_peaking_cap_pct is None, "premise: keeper is uncapped"
    return cfg, dropped


def peak_mw_by_row(cfg: ScenarioConfig, bins: pd.DataFrame, zones: list[str]):
    """Per-(plant_code, group) Σ peak-tranche pmax on the load-bearing path."""
    fleet, _ = bins_to_fleet(bins, zones, cfg)
    out: dict[tuple[int, str], float] = {}
    for g in fleet:
        grp = getattr(g, "plant_group", None)
        if grp not in _CC_GROUPS:
            continue
        suffix = g.name.rsplit(" ", 1)[-1]
        if suffix.startswith("peak"):
            key = (int(g.plant_code), str(grp))
            out[key] = out.get(key, 0.0) + float(g.pmax_mw)
    return out


def main() -> dict:
    cfg, dropped_keys = keeper_config()
    iso_cfg = get_iso_config("MISO")
    zones = [getattr(z, "name", z) for z in iso_cfg.zones]

    gens = load_fleet_from_csv(
        "MISO",
        iso_cfg,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        egrid_identity_heat_rates=cfg.egrid_identity_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
        cc_steam_part_reclass=cfg.cc_steam_part_reclass,
    )
    bins = fleet_to_bins(gens, "MISO", cfg)
    cc = bins[bins["Plant_Group"].isin(_CC_GROUPS)].copy()
    duct = cc_duct_peaking_pct()

    cfg_noduct = dataclasses.replace(cfg, cc_duct_peaking=False)
    cfg_capped = dataclasses.replace(cfg, cc_duct_peaking_cap_pct=8.0)
    pk_keeper = peak_mw_by_row(cfg, bins, zones)
    pk_noduct = peak_mw_by_row(cfg_noduct, bins, zones)
    pk_capped = peak_mw_by_row(cfg_capped, bins, zones)

    rows = []
    for b in cc.itertuples(index=False):
        code = int(b.Plant_Code)
        grp = str(b.Plant_Group)
        cap = float(b.capacity_mw)
        key = (code, grp)
        dpk = duct.get(code)
        rows.append(
            {
                "plant_code": code,
                "plant_name": str(getattr(b, "Plant_Name", "")),
                "group": grp,
                "capacity_mw": round(cap, 1),
                "covered": dpk is not None,
                "duct_pct": dpk,
                "peak_mw_keeper": round(pk_keeper.get(key, 0.0), 2),
                "peak_mw_noduct": round(pk_noduct.get(key, 0.0), 2),
                "peak_mw_capped": round(pk_capped.get(key, 0.0), 2),
            }
        )
    df = pd.DataFrame(rows)
    df["duct_pct"] = pd.to_numeric(df["duct_pct"], errors="coerce")
    total_mw = float(df["capacity_mw"].sum())
    cov = df[df["covered"]]
    cov_mw = float(cov["capacity_mw"].sum())
    flagged = cov[cov["duct_pct"] > 0.0]
    zeroed = cov[cov["duct_pct"] == 0.0]

    # A1 liveness: covered rows must realize capacity*duct_pct/100 as peak MW.
    a1 = cov.assign(
        expected=cov["capacity_mw"] * cov["duct_pct"] / 100.0,
        tol=(0.006 * cov["capacity_mw"]).clip(lower=1.0),
    )
    a1_ok = (a1["peak_mw_keeper"] - a1["expected"]).abs() <= a1["tol"]
    live_mw = float(a1.loc[a1_ok, "capacity_mw"].sum())
    a1_live_share = live_mw / cov_mw if cov_mw > 0 else 0.0
    a1_pass = a1_live_share >= 0.99

    # A2 coverage of the class.
    a2_share = cov_mw / total_mw if total_mw > 0 else 0.0
    a2_pass = a2_share >= 0.50

    # A3 static clip of the 8% cap.
    flagged_mw = float(flagged["capacity_mw"].sum())
    clip_mw = float(
        (flagged["capacity_mw"] * (flagged["duct_pct"] - 8.0).clip(lower=0.0) / 100.0).sum()
    )
    clip_mw_lp = float((cov["peak_mw_keeper"] - cov["peak_mw_capped"]).sum())
    a3_share = clip_mw / flagged_mw if flagged_mw > 0 else 0.0
    a3_pass = a1_pass and a2_pass and (a3_share >= 0.01)

    zero_band_moved = zeroed[zeroed["peak_mw_noduct"] > 0.0]
    grew = cov[cov["peak_mw_keeper"] > cov["peak_mw_noduct"] + 0.01]
    shrank = cov[cov["peak_mw_keeper"] < cov["peak_mw_noduct"] - 0.01]

    out = {
        "session": "miso-193",
        "keeper": "2026-08-30-miso-191-bexit",
        "config_keys_dropped_at_reconstruction": dropped_keys,
        "fleet": {
            "cc_rows": int(len(df)),
            "cc_mw": round(total_mw, 1),
            "by_group_mw": {
                g: round(float(df[df["group"] == g]["capacity_mw"].sum()), 1)
                for g in _CC_GROUPS
            },
        },
        "census": {
            "covered_rows": int(len(cov)),
            "covered_mw": round(cov_mw, 1),
            "duct_flagged_rows": int(len(flagged)),
            "duct_flagged_mw": round(flagged_mw, 1),
            "explicit_zero_rows": int(len(zeroed)),
            "explicit_zero_mw": round(float(zeroed["capacity_mw"].sum()), 1),
            "zero_band_rows_that_had_noduct_band": int(len(zero_band_moved)),
            "zero_band_mw_removed_vs_noduct": round(
                float((zero_band_moved["peak_mw_noduct"]).sum()), 2
            ),
            "band_grew_rows": int(len(grew)),
            "band_grew_mw_delta": round(
                float((grew["peak_mw_keeper"] - grew["peak_mw_noduct"]).sum()), 2
            ),
            "band_shrank_rows": int(len(shrank)),
            "band_shrank_mw_delta": round(
                float((shrank["peak_mw_noduct"] - shrank["peak_mw_keeper"]).sum()), 2
            ),
            "gap_pct_distribution_flagged": {
                q: round(float(flagged["duct_pct"].quantile(p)), 2)
                for q, p in (("p10", 0.1), ("p50", 0.5), ("p90", 0.9), ("max", 1.0))
            }
            if len(flagged)
            else {},
            "flagged_rows_gap_gt_8": int((flagged["duct_pct"] > 8.0).sum()),
            "flagged_mw_gap_gt_8": round(
                float(flagged.loc[flagged["duct_pct"] > 8.0, "capacity_mw"].sum()), 1
            ),
        },
        "gates": {
            "A1_liveness": {
                "live_mw_share_of_covered": round(a1_live_share, 4),
                "threshold": 0.99,
                "pass": bool(a1_pass),
            },
            "A2_coverage": {
                "covered_share_of_class_mw": round(a2_share, 4),
                "threshold": 0.50,
                "pass": bool(a2_pass),
            },
            "A3_cap_materiality": {
                "clip_mw_static": round(clip_mw, 2),
                "clip_mw_lp_realized": round(clip_mw_lp, 2),
                "clip_share_of_flagged_mw": round(a3_share, 4),
                "threshold": 0.01,
                "pass": bool(a3_pass),
            },
        },
        "directional_prereg": {
            "arm": "cc_duct_peaking_cap_pct=8.0 (single delta vs keeper)",
            "prediction": "C3a mean LMP DOWN (adverse to the -12.3405% 2025 gap)",
            "confidence": 0.8,
        },
        "plants": rows,
    }
    _OUT.write_text(json.dumps(out, indent=1))
    v = json.loads(json.dumps(out))
    v.pop("plants")
    print(json.dumps(v, indent=1))
    return out


if __name__ == "__main__":
    main()
