"""caiso-236 — classify the keeper's residual-identified DOF ledger rows.

THE OBJECT. ``calibration_attestation.json`` on the CAISO keeper
``2026-09-01-caiso-231-b1-ungrounded`` claims ``n_entries=11, n_residual=7``.
Rule 21 ``[R-DOF]`` requires every free parameter to carry an identification
source; rule 26 ``[R-DELETE]`` is explicit that *"a deprecated parameter that
still parses is a re-armable answer key"*. This instrument answers, per row,
**which of the pre-registered three classes the row is in** — so the
classification is reproducible from committed artifacts rather than asserted.

THE TAXONOMY IS PRE-REGISTERED, not chosen here
(``results/calibration/PRECOMMIT-caiso236-dof-residual-ledger-audit-2026-09-02.md``
§1–§2):

* **(a) DEAD FALLBACK** — every read of the CAISO value sits under a gate the
  keeper's own ``run_config.json`` records as OFF. Action: DELETE (rule 26).
* **(b) LIVE BUT IMMATERIAL** — read, but the governed quantity clears BOTH
  arithmetic materiality thresholds of PRECOMMIT §2 in ALL THREE years.
  Action: neutralize, then prove byte-identical.
* **(c) LIVE AND MATERIAL** — everything else. (c) is the FAIL-CLOSED class:
  ties, ambiguity, and any bound that cannot be computed resolve to (c), whose
  action is "report and do not touch".

Two outcomes this instrument is built to be able to return, because the pass is
only worth running if it can surprise its author:

* **(a')  KEEPER-DEAD BUT LANE-LIVE** — dead on the keeper's gates yet read by
  another SHIPPED configuration (in practice: the ``ScenarioConfig`` DEFAULTS,
  which is what a forecast-mode CAISO run solves on). Deleting such a value is
  a mechanism change, not a ledger repair, so it is reported and NOT deleted.
  This class was not in the pre-registered taxonomy; it is disclosed as an
  amendment in the FINDING rather than folded silently into (a) or (c).
* **PHANTOM** — the ledger row attests a surface the code does not contain for
  this ISO at all. Its scalars are not free parameters because they do not
  exist; the honest repair is to the ledger, and it costs no solve.

NOTHING HERE SOLVES, and nothing here reads a year outside 2023-2025. Every
number comes from the keeper's committed bundle
(``run_config.json`` + ``hourly/``) or from importing the code and reading the
registries. Rule 1 ``[R-STRUCT]``: no output of this instrument is a price
residual and none may be argued from one.

Usage::

    uv run python scripts/probes/_caiso236_dof_residual_classifier.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

BUNDLE = _REPO / "results" / "calibration" / "caiso231_b1_ungrounded"
YEARS = (2023, 2024, 2025)

#: PRECOMMIT §2 thresholds, fixed BEFORE measurement and not adjustable here.
MATERIALITY_ENERGY_SHARE_PCT = 0.10
MATERIALITY_HOURS_SHARE_PCT = 1.0


def _run_config() -> dict:
    return json.loads((BUNDLE / "run_config.json").read_text())


def _class_hourly(year: int) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def class_materiality(klass: str) -> dict[int, dict[str, float]]:
    """Return the PRECOMMIT §2 bound inputs for one dispatch class, per year.

    ``energy_share_pct`` is the class's share of total modelled dispatch;
    ``hours_share_pct`` is the share of hours in which the class's modelled
    output is strictly greater than zero — a NECESSARY upper bound on the hours
    in which its offer can enter the energy-balance dual at all (a class at
    exactly zero output in an hour is not an interior column of that hour's
    basis). The bound is necessary, never sufficient: the byte-identity A/B is
    the actual proof.
    """
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        df = _class_hourly(year)
        total = float(df["mw"].sum())
        series = df[df["klass"] == klass].sort_values("hour")["mw"].to_numpy(float)
        out[year] = {
            "energy_twh": float(series.sum()) / 1e6,
            "energy_share_pct": 100.0 * float(series.sum()) / total if total else 0.0,
            "hours_gt0": int((series > 0.0).sum()),
            "hours_share_pct": 100.0 * float((series > 0.0).mean())
            if series.size
            else 0.0,
            "max_mw": float(series.max()) if series.size else 0.0,
        }
    return out


def bound_passes(rows: dict[int, dict[str, float]]) -> bool:
    """True iff BOTH PRECOMMIT §2 thresholds hold in ALL THREE years."""
    return all(
        r["energy_share_pct"] <= MATERIALITY_ENERGY_SHARE_PCT
        and r["hours_share_pct"] <= MATERIALITY_HOURS_SHARE_PCT
        for r in rows.values()
    )


def seam_cap_binding() -> dict[int, dict[str, float]]:
    """Return the PRECOMMIT §2 seam test for ``WECC_import_simultaneous.cap_mw``.

    For a transmission/seam limit the bound is a BINDING-HOUR COUNT, not an
    energy share: the scalar is immaterial only if the modelled quantity it
    caps never attains the capped value. The ``import`` dispatch class is the
    signed net position of the WECC seam (import tranches positive, export legs
    negative generation on the same ``fuel_type``), so ``max`` above the baked
    cap is a direct falsification of that cap having bound.
    """
    baked = 7500.0
    resolved = _run_config()["resolved_inputs"]["seam_import_cap"]["by_year"]
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        series = (
            _class_hourly(year)
            .query("klass == 'import'")
            .sort_values("hour")["mw"]
            .to_numpy(float)
        )
        r = resolved[str(year)]
        out[year] = {
            "baked_cap_mw": baked,
            "recorded_cap_mw": float(r["cap_mw"]),
            "recorded_source": r["source"],
            "import_max_mw": float(series.max()),
            "hours_at_baked_cap": int(np.isclose(series, baked, atol=1e-6).sum()),
            "hours_above_baked_cap": int((series > baked + 1e-6).sum()),
        }
    return out


def coal_sigmoid_surface() -> dict[str, object]:
    """Return what the CAISO coal passthrough surface ACTUALLY resolves to.

    Ledger row 4 is ``COAL_SIGMOID_DEFAULTS[CAISO]``, n_scalars 4. The row is a
    PHANTOM iff the registry holds no ``("CAISO", *)`` key AND the keeper sets
    none of the four ``coal_<supply>_passthrough_*`` overrides — in which case
    ``coal_sigmoid_params`` returns ``None`` for every supply and every coal
    tranche passes the flat fallback, whatever the sigmoid toggle says.
    """
    from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig
    from market_sim.data.fuel.trajectories import coal_sigmoid_params

    sc = _run_config()["scenario_config"]
    supplies = (
        "prb",
        "prb_follower",
        "subbituminous",
        "bituminous",
        "lignite",
        "waste",
    )
    stem = {
        "prb": "prb_passthrough",
        "prb_follower": "prb_follower",
        "subbituminous": "sub_passthrough",
        "bituminous": "bit_passthrough",
        "lignite": "lignite_passthrough",
        "waste": "waste_passthrough",
    }
    cfg = ScenarioConfig(iso="CAISO")
    overrides = {
        f"coal_{stem[s]}_{p}": sc.get(f"coal_{stem[s]}_{p}")
        for s in supplies
        for p in ("floor", "ceil", "gas_mid", "gas_slope")
    }
    return {
        "caiso_registry_keys": [k for k in COAL_SIGMOID_DEFAULTS if k[0] == "CAISO"],
        "registry_isos": sorted({k[0] for k in COAL_SIGMOID_DEFAULTS}),
        "keeper_overrides_all_none": all(v is None for v in overrides.values()),
        "resolved_params_by_supply": {s: coal_sigmoid_params(cfg, s) for s in supplies},
        "keeper_coal_prb_passthrough": sc.get("coal_prb_passthrough"),
        "keeper_coal_prb_passthrough_sigmoid": sc.get("coal_prb_passthrough_sigmoid"),
        "keeper_coal_prb_passthrough_tiered": sc.get("coal_prb_passthrough_tiered"),
    }


def interchange_liveness() -> dict[str, object]:
    """Return which CAISO seam ladders the keeper's gates actually read.

    ``get_interchange_spec`` resolves a mutually-exclusive CAISO builder ladder;
    under ``caiso_per_hub_intertie`` the spec carries ``import_tranches`` and
    ``export_tranches`` as EMPTY (``use_corridors`` short-circuits both), while
    ``IMPORT_TRANCHES['CAISO']`` is still read directly to place the per-hub
    corridor legs. So the two halves of ledger row 7 have DIFFERENT liveness and
    the row cannot be classified as one object.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.spec import (
        EXPORT_TRANCHES,
        IMPORT_TRANCHES,
        get_interchange_spec,
    )

    sc = _run_config()["scenario_config"]
    gates = {
        k: sc.get(k)
        for k in (
            "caiso_reference_price_seam",
            "caiso_per_hub_intertie",
            "caiso_bidir_intertie",
            "reference_price_interface",
        )
    }
    keeper_cfg = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        **{k: bool(v) for k, v in gates.items() if v is not None},
    )
    default_cfg = ScenarioConfig(iso="CAISO")
    out: dict[str, object] = {"keeper_gates": gates}
    for label, cfg in (
        ("keeper", keeper_cfg),
        ("scenarioconfig_defaults", default_cfg),
    ):
        spec = get_interchange_spec(cfg, "CAISO", 2023)
        out[label] = {
            "caiso_mode": spec.caiso_mode,
            "use_corridors": spec.use_corridors,
            "spec_import_tranches": len(spec.import_tranches),
            "spec_export_tranches": len(spec.export_tranches),
            "corridor_import_legs": sum(len(c.import_tranches) for c in spec.corridors),
        }
    out["registry"] = {
        "IMPORT_TRANCHES[CAISO]": IMPORT_TRANCHES.get("CAISO"),
        "EXPORT_TRANCHES[CAISO]": EXPORT_TRANCHES.get("CAISO"),
    }
    return out


def bidir_export_cap_liveness() -> dict[str, object]:
    """Return the reachability of ``CAISO_BIDIR_EXPORT_CAP_MW`` (ledger row 9).

    Classed ``measured-physical`` rather than ``residual``, but audited in the
    same pass: rule 26 is about re-armable DEAD knobs, not about identification
    class, and the ledger's own note already flags it "fallback-only … or
    R5-delete the caiso_bidir_intertie mechanism (rule 26)".
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.caiso import CAISO_BIDIR_EXPORT_CAP_MW
    from market_sim.model.interchange.spec import WECC_EXPORT_CAP_MW

    sc = _run_config()["scenario_config"]
    return {
        "value_mw": CAISO_BIDIR_EXPORT_CAP_MW,
        "keeper_caiso_bidir_intertie": sc.get("caiso_bidir_intertie"),
        "scenarioconfig_default": getattr(
            ScenarioConfig(iso="CAISO"), "caiso_bidir_intertie"
        ),
        "derived_WECC_EXPORT_CAP_MW": WECC_EXPORT_CAP_MW,
    }


def main() -> None:
    rc = _run_config()
    sc = rc["scenario_config"]

    print("=" * 78)
    print("caiso-236 — DOF residual ledger classification")
    print("keeper bundle:", BUNDLE.relative_to(_REPO))
    print("=" * 78)

    print("\n[gates that decide liveness]")
    for k in (
        "mode",
        "capacity_deliverability_limits",
        "caiso_per_hub_intertie",
        "caiso_bidir_intertie",
        "reference_price_interface",
        "use_campd_bins",
        "plant_level_fleet",
    ):
        print(f"  {k} = {sc.get(k)!r}")

    print("\n[rows 1/2 — offer_curve_by_group + the CAISO committed bands]")
    ocg = sc.get("offer_curve_by_group") or {}
    print(f"  groups populated: {len(ocg)}  campd binning: {sc.get('use_campd_bins')}")
    print(
        "  committed bands:",
        {
            g: b.get("committed")
            for g, b in ocg.items()
            if g in ("CC_REGULAR", "CT_PEAKER", "CC_CHP", "CT_CHP", "ST_GAS")
        },
    )

    print("\n[row 3 — offer_curve_smoothing]")
    print(
        f"  n={sc.get('offer_curve_smoothing_n')} exp={sc.get('offer_curve_smoothing_exp')}"
        f" mid={sc.get('offer_curve_smoothing_mid')}"
        "  (n>0 renders the econ ramp as an N-slice rising curve, not 2 flat blocks)"
    )

    print("\n[row 4 — COAL_SIGMOID_DEFAULTS[CAISO]]")
    coal = coal_sigmoid_surface()
    print(f"  registry ISOs: {coal['registry_isos']}")
    print(f"  ('CAISO', *) keys present: {coal['caiso_registry_keys']}")
    print(
        f"  keeper sets any coal_*_passthrough_{{floor,ceil,gas_mid,gas_slope}}: "
        f"{not coal['keeper_overrides_all_none']}"
    )
    print(
        f"  coal_sigmoid_params(CAISO, supply) -> {coal['resolved_params_by_supply']}"
    )
    print(
        f"  flat fallback in force: coal_prb_passthrough="
        f"{coal['keeper_coal_prb_passthrough']} (1.0 = full delivered cost, identity)"
    )
    coal_rows = class_materiality("COAL")
    for y, r in coal_rows.items():
        print(
            f"  COAL {y}: {r['energy_twh']:.4f} TWh  {r['energy_share_pct']:.4f} % of"
            f" dispatch  hours>0 {r['hours_gt0']} ({r['hours_share_pct']:.2f} %)"
            f"  max {r['max_mw']:.1f} MW"
        )
    print(
        f"  PRECOMMIT §2 bound (energy <= {MATERIALITY_ENERGY_SHARE_PCT} % AND hours"
        f" <= {MATERIALITY_HOURS_SHARE_PCT} %, all years): "
        f"{'PASS' if bound_passes(coal_rows) else 'FAIL'}"
    )

    print("\n[row 5 — battery_dispatch_adder]")
    print(f"  value = {sc.get('battery_dispatch_adder')} $/MWh")
    for year in YEARS:
        st = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
        st = st[st["pass"] == "P1"]
        tot = float(_class_hourly(year)["mw"].sum())
        dis = float(st["discharge_mw"].sum())
        print(
            f"  {year}: discharge {dis / 1e6:.4f} TWh  "
            f"{100.0 * dis / tot:.3f} % of modelled dispatch  "
            f"hours>0 {int((st.groupby('hour')['discharge_mw'].sum() > 0).sum())}"
        )

    print("\n[row 6 — WECC_import_simultaneous.cap_mw = 7500]")
    for y, r in seam_cap_binding().items():
        print(
            f"  {y}: run_config resolved cap {r['recorded_cap_mw']:.0f} MW"
            f" (source={r['recorded_source']}); net import max {r['import_max_mw']:.1f} MW;"
            f" hours AT 7500.0: {r['hours_at_baked_cap']};"
            f" hours ABOVE 7500: {r['hours_above_baked_cap']}"
        )

    print("\n[row 7 — IMPORT_TRANCHES / EXPORT_TRANCHES[CAISO]]")
    inter = interchange_liveness()
    print(f"  keeper gates: {inter['keeper_gates']}")
    for label in ("keeper", "scenarioconfig_defaults"):
        print(f"  {label}: {inter[label]}")
    print(f"  IMPORT_TRANCHES[CAISO] = {inter['registry']['IMPORT_TRANCHES[CAISO]']}")
    print(f"  EXPORT_TRANCHES[CAISO] = {inter['registry']['EXPORT_TRANCHES[CAISO]']}")

    print("\n[row 9 — CAISO_BIDIR_EXPORT_CAP_MW (measured-physical, audited anyway)]")
    print(f"  {bidir_export_cap_liveness()}")

    print("\n" + "=" * 78)
    print("Classification is written up in")
    print(
        "results/calibration/FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
