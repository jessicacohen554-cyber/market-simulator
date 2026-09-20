"""Calibration backcast: solve, persist, and report off persisted parquet.

Each run solves the dispatch for the requested years (and the P2 commitment
pass when ``--commitment`` is set), writes the full hourly per-plant results
to a timestamped parquet bundle, and then computes the comparison report from
that bundle. Nothing is lost: the bundle is the source of truth and can be
re-queried for any ad-hoc analysis, and re-running never overwrites a prior
run (each lands in its own timestamped directory). Bundles are scoped by ISO
so backcasts for different ISOs run in parallel without colliding.

A run bundle lives in ``results/calibration/<iso>/<timestamp>/`` and holds:

  * ``dispatch/<year>_<pass>.parquet`` — every generator's hourly MW (8760h)
    with plant_code / class / fuel / supply / zone metadata, plus wind and
    solar as per-zone pseudo-units. Coal carries its supply class
    (COAL_LIGNITE / COAL_PRB) so mine-mouth and PRB can be separated.
  * ``system.parquet`` — per-zone hourly price, load slack and demand target,
    for every year and pass.
  * ``hourly/class_hourly_<year>.parquet`` + ``hourly/system_<year>.parquet``
    + ``hourly/storage_<year>.parquet`` + ``hourly/unit_hourly_<year>.parquet``
    + ``hourly/network_<year>.parquet`` + ``hourly/reserve_family_<year>.parquet``
    — committable slim sidecars (class-hour
    dispatch aggregate; per-year system slices; per-tech storage; per-unit
    dispatch AND availability cap; per-link/per-group flow, dual and limit;
    per-zone-hour MARGINAL EMISSION RATE (``marginal_emission_rate``, the
    emissions dual on the ``system`` slice — tCO2 per marginal MWh, the basis
    for any marginal-abatement-cost reading; see
    ``DispatchResult.marginal_emission_rate``);
    per-reserve-family balance dual, requirement and ORDC shortfall — the only
    artifact in which a LOCATIONAL reserve family's binding is observable,
    since ``system``'s ``reserve_price`` is the cross-family sum broadcast
    identically to every zone).
    ``dispatch/``, ``system.parquet`` and ``flows.parquet`` are gitignored by
    the slim-bundle rules, so KEEPER bundles commit ``hourly/`` and
    diagnostics read it instead of replaying the solve. Every sidecar is
    write-only and solve-invariant.
  * ``eia930.parquet`` — EIA-930 hourly benchmark series (gas, coal, wind,
    solar, nuclear, net generation).
  * ``eia923.parquet`` — EIA-923 net generation per (plant, class), annual and
    by month.
  * ``btm.parquet`` — behind-the-meter CHP must-run by class (off-grid).
  * ``meta.json`` — run metadata (timestamp, years, passes, flags, prices).

The report ([1]-[6] tables) is then computed entirely from the bundle, so the
same numbers can be reproduced from an old run with ``--report <dir>``.

Usage:
    python scripts/run_calibration_full.py --year 2023 2024
    python scripts/run_calibration_full.py --year 2023 --commitment --no-coal-p2
    python scripts/run_calibration_full.py --report results/calibration/<iso>/<ts>
"""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import inspect
import json
import logging
import os
import pickle
import shutil
import sys
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:  # annotations only — the runtime import stays local
    from market_sim.config.scenarios import ScenarioConfig

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import resolve_reference_price_interface  # noqa: E402
from market_sim.config.interchange_config import (  # noqa: E402
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    resolve_miso_firm_imports,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.config.plant_taxonomy import (  # noqa: E402
    classes_for_fuel930,
    classify_plant,
    coal_code_to_class,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_eia_hourly_benchmark,
    neiso_net_interchange,
    nyiso_net_interchange,
    pjm_net_interchange,
    load_ercot_battery_gen,
    load_ercot_fossil_gen,
    load_ercot_nuclear_gen,
    load_ercot_other_gen,
    load_ercot_renewable_gen,
)
from market_sim.data.hydro import eia930_wat_level_folded  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from market_sim.model.transmission import extend_with_import_node  # noqa: E402
from market_sim.data.coal import coal_supply_class  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    _COAL_SUPPLY_TO_CURVE,
    OTHER_FOSSIL_CLASS,
    apply_other_fossil_scoring,
)
import market_sim.pipeline.persist as _pipeline_persist  # noqa: E402
import market_sim.pipeline.report as _pipeline_report  # noqa: E402
from market_sim.pipeline.flags import (  # noqa: E402
    add_flag_arguments,
    solve_kwargs_from_args,
)
from market_sim.pipeline.backcast_config import backcast_config  # noqa: E402
from market_sim.pipeline.timing import log_year_phase_timing  # noqa: E402
from market_sim.results.calibration import check_cf_band_occupancy  # noqa: E402
from scripts.lib.bundle_io import (  # noqa: E402
    bundle_input_path,
    write_derived_solve_inputs,
    write_shared_input,
)
from scripts.lib.solve_container import (  # noqa: E402
    ensure_solve_container,
    log_peak_memory,
)
from scripts.run_calibration import (  # noqa: E402
    _commitment_pass,
    _henry_hub_actual,
    _load_reference,
    resolve_p1_basis_seed_default,
    resolve_xyear_warmstart_default,
    run_year,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("calibration_full")

#: Container preflight (scripts/lib/solve_container.py): read the BINDING
#: memory ceiling (the nested bash cgroup, 13.34 GiB on a CCR box that
#: advertises 15.7), provision swap up to the 24 GiB target, pin the
#: single-thread solve profile. Runs at the top of solve_and_persist — the
#: one entry both this CLI and replay_keeper reach — so a MISO/PJM shard no
#: longer depends on its prompt remembering prepare_solve_container.py
#: (miso-252/253: five shards OOM-killed at 13.30 GiB for exactly that).
#: Cleared by --no-container-preflight. Not a solve tunable (rule 24): swap
#: and thread count are workspace choices, the LP optimum is identical.
CONTAINER_PREFLIGHT_ENABLED = True

_MWH_PER_TWH: float = 1.0e6
_HOURS_PER_YEAR: int = 8760
# Report/persist halves: PERMANENT same-name aliases of their canonical pipeline
# homes (orchestrator-unification lane, refactor-consolidation plan §5). The
# bodies live in ``market_sim.pipeline.{report,persist}``; this module's
# exported symbol names are a frozen surface (``replay_keeper`` reads
# ``rcf._environment_block`` / ``rcf._parse_offer_curve_json``, probe scripts
# and tests import the rest), so every moved name keeps its ``_``-prefixed
# spelling here and resolves to the SAME object. Verified equivalent before
# conversion by ``inspect.getsource`` diff and constant equality; the two
# genuine drifts found (``basis_sha`` inside ``git_state``, and the two
# ``nyiso_*_reserve_eligible`` calibration_flags keys) were FORWARD-PORTED into
# ``pipeline.persist`` first, so no recorded run_config.json/meta.json key moves.
_DAYS_IN_MONTH: tuple[int, ...] = _pipeline_report.DAYS_IN_MONTH
_MONTH_NAMES: tuple[str, ...] = _pipeline_report.MONTH_NAMES

# Fuel codes that EIA-923 reports for coal-class units.
# All class groupings derive from the canonical taxonomy
# (market_sim.config.plant_taxonomy) — no hardcoded class lists.
_GAS_CLASSES: tuple[str, ...] = classes_for_fuel930("gas")
_COAL_CLASSES: tuple[str, ...] = classes_for_fuel930("coal")
# CHP classes — reported in their own dedicated table and excluded from every
# other comparison.
_CHP_CLASSES: tuple[str, ...] = tuple(c for c in _GAS_CLASSES if c.endswith("_CHP"))
_NONCHP_GAS: tuple[str, ...] = tuple(c for c in _GAS_CLASSES if not c.endswith("_CHP"))
# All thermal classes the [3b] / [4] tables iterate over. OTHER_FOSSIL holds the
# genuinely-mixed gas-thermal plants pulled out of the clean CC/CT/ST classes by
# apply_other_fossil_scoring (a scoring bucket only — dispatch is unchanged).
_THERMAL_CLASSES: tuple[str, ...] = (*_GAS_CLASSES, OTHER_FOSSIL_CLASS, *_COAL_CLASSES)

# Representative plants for the plant-level report. The user picks these
# because they span every operational class the per-plant binning resolves
# (efficient CC, legacy CC, gas steam, CHP, coal, peakers).
_PLANT_PANEL: tuple[tuple[int, str], ...] = (
    (60122, "Colorado Bend II"),
    (59812, "Wolf Hollow II"),
    (3491, "Handley"),
    (55464, "Deer Park Energy Center"),
    (55327, "Baytown Energy Center"),
    (55545, "Hidalgo Energy Center"),
    (298, "Limestone (coal)"),
    (3470, "W A Parish (coal units 5-8)"),
    (3504, "Stryker Creek (gas steam)"),
    (3492, "Morgan Creek (CT peaker)"),
    (63688, "Topaz Generating (CT peaker)"),
)

# Default CF-band width for the per-plant operating-level histogram ([7b]
# panel and plant_cf_bands.parquet): 0.10 -> ten 10%-of-capacity bands. Coarse
# enough to be robust to CAMPD net-vs-gross noise, fine enough to separate a
# CC's committed floor / part-load / duct-fired modes. Override per run with
# ``--cf-band-width`` (e.g. 0.05 for twenty 5% bands when inspecting where a CC
# loses its >90% CF hours); the cf_emd metric reads the width back from the
# parquet, so it stays comparable across band widths.
_CF_BAND_WIDTH: float = 0.10


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _coal_supply_class(plant_code: int, fuel_code: str = "") -> str:
    """Return the coal supply class (``COAL_BIT`` / ``COAL_WC`` /
    ``COAL_LIGNITE`` / ``COAL_PRB``) for a coal plant.

    Uses the authoritative model mapping (:func:`coal_supply_class`, which
    merges the curated ERCOT lignite/PRB map with the EIA-923-derived per-ISO
    ranks) so the model and the EIA-923 benchmark split coal the same way. For
    a plant not in either map, fall back to the EIA-923 receipt fuel code
    (``LIG``/``SUB``/``WC``/``BIT``); unknown -> generic ``COAL``.
    """
    key = _COAL_SUPPLY_TO_CURVE.get(coal_supply_class(int(plant_code)))
    return key or coal_code_to_class(fuel_code) or "COAL"


def _model_class_for_unit(unit_id: str, fuel: str, eff_bin: str) -> str:
    """Return the model class for one generator unit id.

    CAMPD generator ids carry their Plant_Group through ``efficiency_bin``
    (e.g. ``CC_REGULAR_Houston_p60122_econ``). Non-CAMPD generators fall back
    to a class derived from the fuel type. Coal is returned as the bare
    ``COAL`` here; the caller splits it into the supply class.
    """
    if eff_bin in {*_GAS_CLASSES, "COAL"}:
        return eff_bin
    # Non-CAMPD fleets (every non-ERCOT ISO, e.g. PJM's per-plant EIA-860
    # fleet) carry no Plant_Group in ``eff_bin``, so derive the class from the
    # model fuel type — giving each plant its proper class (one plant per bin)
    # instead of collapsing the thermal fleet into OTHER. ERCOT is unaffected:
    # its CAMPD units return at the ``eff_bin`` branch above.
    if fuel == "coal":
        return "COAL"
    if fuel == "import":
        return "import"
    if fuel in {"gas_cc", "gas_cc_ccs"}:
        return "CC_REGULAR"
    if fuel == "gas_ct":
        return "CT_PEAKER"
    if fuel == "gas_st":
        return "ST_GAS"
    if fuel == "nuclear":
        return "nuclear"
    if fuel == "hydro":
        return "hydro"
    if fuel in {"wind", "offshore_wind"}:
        return "wind"
    if fuel == "solar":
        return "solar"
    if fuel == "oil":
        return "oil"
    if fuel == "biomass":
        return "biomass"
    return "OTHER"


def _classify_f923(fuel: str, pm: str, chp: bool, plant_id: int) -> str:
    """Bucket one EIA-923 Page-1 row into a model class.

    Thin wrapper over the canonical
    :func:`market_sim.config.plant_taxonomy.classify_plant` — the single source
    of truth the model fleet uses too, so the benchmark and the model bucket a
    plant identically by construction. Coal is split into its supply class
    (ERCOT lignite/PRB; EIA-923-derived bituminous / sub-bituminous / waste
    elsewhere) via :func:`_coal_supply_class`.
    """
    return classify_plant(
        fuel, pm, chp, plant_id, coal_class_resolver=_coal_supply_class
    )


def _plant_codes_from_unit_ids(
    unit_ids: list[str], numeric_head: bool = False
) -> np.ndarray:
    """Return ``(n_gen,)`` plant codes parsed from the unit id.

    ERCOT CAMPD ids carry the code as a ``..._p{code}_<suffix>`` token. The
    EIA-860 per-plant fleet (every non-ERCOT ISO, e.g. PJM) instead names units
    ``{plant_code}_{generator_id}`` (e.g. ``54_GT1``); with ``numeric_head`` the
    leading all-digit token is used when no ``p{code}`` token is present.
    ``numeric_head`` is off for ERCOT, so its dispatch frame is unchanged (ERCOT
    nuclear shares the ``{code}_{gen}`` shape but is not matched by plant code).
    """
    out = np.zeros(len(unit_ids), dtype=int)
    for i, uid in enumerate(unit_ids):
        for token in uid.split("_"):
            if token.startswith("p") and token[1:].isdigit():
                out[i] = int(token[1:])
                break
        else:
            head = uid.split("_", 1)[0]
            if numeric_head and head.isdigit():
                out[i] = int(head)
    return out


_hour_to_month = _pipeline_report.hour_to_month
_hourly_to_monthly = _pipeline_report.hourly_to_monthly
_pearson_r = _pipeline_report.pearson_r
_nrmse = _pipeline_report.nrmse
_print_table = _pipeline_report.print_table


# ---------------------------------------------------------------------------
# Persistence — build the parquet bundle from a solved dispatch
# ---------------------------------------------------------------------------


def _save_floor_arrays(run_dir: Path, year: int, p2_state: dict, has_p2: bool) -> None:
    """Persist each pass's min-gen floor + mechanism ids to ``floors/``.

    Writes ``floors/<year>_<pass>.npz`` per solved pass with the ``(n_gen, T)``
    ``min_gen`` lower bound the LP actually saw, the parallel int8 mechanism-id
    array (``data.floor_mechanisms``), and the unit alignment metadata
    (``unit_ids`` / ``plant_code`` / ``plant_group``). This is the D-2/D-4
    forced-energy attribution input for ``scripts/legitimacy_diagnostics.py``
    — a bundle solved after this change carries its floors; older bundles are
    reconstructed via ``run_year(fleet_only=True)``. No-op for a fleet with no
    floor matrix (min_gen is None → the LP bound is the scalar pmin).
    """
    fa_p1 = p2_state["fleet_arrays"]
    passes = {"P1": fa_p1}
    if has_p2:
        # _commitment_pass stashes the exact P2 bounds (incl. the RA
        # must-offer floor) back into the state dict.
        passes["P2"] = p2_state.get("fleet_arrays_p2", fa_p1)
    groups = (
        fa_p1.plant_group
        if fa_p1.plant_group is not None
        else np.array([""] * len(fa_p1.unit_ids), dtype=object)
    )
    for label, fa in passes.items():
        if fa is None or fa.min_gen is None:
            continue
        mech = getattr(fa, "min_gen_mechanism", None)
        if mech is None:
            mech = np.zeros(fa.min_gen.shape, dtype=np.int8)
        floors_dir = run_dir / "floors"
        floors_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            floors_dir / f"{year}_{label}.npz",
            min_gen=fa.min_gen.astype(np.float32),
            mechanism=mech.astype(np.int8),
            unit_ids=np.array(list(fa_p1.unit_ids), dtype=str),
            plant_code=np.asarray(fa_p1.plant_code, dtype=np.int64),
            plant_group=np.array([str(g) for g in groups], dtype=str),
            # D-2's plant-class vote weight (nyiso-233): the class carrying the
            # most CAPACITY names the plant, because bands partition a class's
            # capacity however many of them there are — a row count does not,
            # so it let a ladder collapse move a site between class denominators
            # and flip C8. Bundles written before this key are backfilled from a
            # fleet_only rebuild by legitimacy_diagnostics._backfill_pmax.
            pmax=np.asarray(
                fa_p1.pmax if fa_p1.pmax is not None else np.zeros(len(fa_p1.unit_ids)),
                dtype=float,
            ),
        )


def _dispatch_frame(
    year: int,
    pass_label: str,
    result,
    context,
    zone_names: list[str],
    iso: str = "ERCOT",
    must_run: dict[str, np.ndarray] | None = None,
    oil_switch_mask: "np.ndarray | None" = None,
) -> pd.DataFrame:
    """Return the long per-generator-hour dispatch frame for one year-pass.

    One row per (generator, hour) carrying the dispatched MW and the
    generator's class / fuel / supply / zone, plus wind and solar (and any
    injected must-run residual classes) as per-zone pseudo-units so the frame
    reconciles to total grid generation.
    """
    disp = np.asarray(result.dispatch, dtype=np.float32)
    n_gen, T = disp.shape
    unit_ids = list(context.unit_ids)
    fuels = list(context.fuel_types)
    bins = list(context.efficiency_bins)
    zones = list(context.zones)
    pgroups = list(getattr(context, "plant_groups", []) or [])
    is_ercot = iso == "ERCOT"
    plant_codes = _plant_codes_from_unit_ids(unit_ids, numeric_head=not is_ercot)

    klass = []
    supply = []
    for g in range(n_gen):
        # Non-ERCOT fleets carry the real plant group (CC_CHP, CT_CHP, ST_GAS,
        # ... distinct from the merchant variants), so class by it rather than
        # collapsing by fuel. ERCOT keeps the efficiency-bin path. Nuclear /
        # wind / solar carry no group and fall back to the fuel classifier.
        if not is_ercot and g < len(pgroups) and pgroups[g]:
            k = pgroups[g]
        else:
            k = _model_class_for_unit(unit_ids[g], fuels[g], bins[g])
        if k == "COAL":
            # Split coal into its supply class — ERCOT mine-mouth lignite /
            # PRB-by-rail, and the EIA-923-derived bituminous / sub-bituminous /
            # waste ranks for other ISOs (a single COAL only for unclassified
            # plants). The raw supply string rides along in ``supply``.
            k = _coal_supply_class(int(plant_codes[g]))
            supply.append(coal_supply_class(int(plant_codes[g])))
        else:
            supply.append("")
        klass.append(k)

    # Zonal LMP (the dispatch LP's energy-balance dual) carried per
    # generator-hour, so unit revenue (mw x lmp) and commitment economics are
    # queryable straight from this frame. zone_idx maps each generator to its
    # zone's price row.
    prices = np.asarray(result.prices, dtype=np.float32)
    zone_to_idx = {z: i for i, z in enumerate(zone_names)}
    gen_zidx = np.array([zone_to_idx[z] for z in zones], dtype=int)

    hours = np.tile(np.arange(T, dtype=np.int32), n_gen)

    pseudo = [
        ("wind", result.wind_dispatched),
        ("solar", result.solar_dispatched),
    ]
    # Injected must-run residual classes (biomass / hydro / OTHER), re-added per
    # zone so total model generation reconciles to load (they were netted out of
    # the LP's demand). Carry klass == fuel == the class key.
    for mr_klass, arr in (must_run or {}).items():
        pseudo.append((mr_klass, arr))

    # PERF-A prototype (NOT-FOR-MERGE): build every label column as a
    # categorical directly, with the category vocabulary computed up front as
    # the sorted uniques the former post-hoc ``.astype("category")`` derived —
    # so the resulting frame (values, order, categories, dtypes) is identical,
    # but the five 12.8M-element object arrays and their per-element re-hash
    # never exist. Codes are per-generator searchsorted (n_gen-sized) repeated
    # as ints.
    pseudo_names = [name for name, _ in pseudo]
    pseudo_units = [f"{n.upper()}_{z}" for n, _ in pseudo for z in zone_names]
    oil_active = oil_switch_mask is not None and np.asarray(oil_switch_mask).any()
    extra_kf = ["oil"] if oil_active else []

    def _vocab(*groups):
        vals: list = []
        for g_vals in groups:
            vals.extend(g_vals)
        return np.sort(pd.unique(np.asarray(vals, dtype=object)))

    cats_unit = _vocab(unit_ids, pseudo_units)
    cats_klass = _vocab(klass, pseudo_names, extra_kf)
    cats_fuel = _vocab(fuels, pseudo_names, extra_kf)
    cats_supply = _vocab(supply)
    cats_zone = _vocab(zones, zone_names)

    def _codes(cats, values):
        return np.searchsorted(cats, np.asarray(values, dtype=object)).astype(np.int32)

    kcode = np.repeat(_codes(cats_klass, klass), T)
    # Pre-re-attribution plant group, captured BEFORE the dual-fuel overwrite
    # below. ``klass`` alone cannot answer "how much did class X dispatch",
    # because a dual-fuel unit's switched hours are relabelled to ``oil`` — a
    # POOLED class every dual-fuel class relabels into — so a class aggregate
    # keyed on ``klass`` silently UNDERCOUNTS the gas class and the shortfall
    # is not attributable back out of ``oil``. That defect is what made
    # nyiso-179's un-dispatched-in-the-money ST_GAS signature unresolvable
    # from committed artifacts (its §6.1 candidate (c)). Carrying both keys
    # makes the split exact and costs one ~14-category column on a frame that
    # is gitignored anyway.
    kcode_base = kcode.copy()
    fcode = np.repeat(_codes(cats_fuel, fuels), T)
    # Dual-fuel re-attribution: a gas unit that switched to its backup oil this
    # hour (gas price > oil parity; mask from fuel.dual_fuel_switch_mask) burned
    # petroleum, so its dispatched MWh is counted as oil (EIA-930 ``NG: OIL``),
    # not gas — the LP still priced/dispatched it on the gas heat-rate (the
    # switch is objective-only), this only relabels the generation. The mask is
    # ``(n_gen, T)`` over the LP generators, the same (gen, hour) row-major order
    # as ``disp.reshape(-1)``, so flatten and overwrite the codes in place.
    if oil_active:
        flat = np.asarray(oil_switch_mask, dtype=bool)[:n_gen, :T].reshape(-1)
        kcode[flat] = np.searchsorted(cats_klass, "oil")
        fcode[flat] = np.searchsorted(cats_fuel, "oil")

    def _cat(cats, codes):
        return pd.Categorical.from_codes(codes, categories=cats)

    frames = [
        pd.DataFrame(
            {
                "unit_id": _cat(cats_unit, np.repeat(_codes(cats_unit, unit_ids), T)),
                "plant_code": np.repeat(plant_codes.astype(np.int32), T),
                "klass": _cat(cats_klass, kcode),
                "klass_base": _cat(cats_klass, kcode_base),
                "fuel": _cat(cats_fuel, fcode),
                "supply": _cat(cats_supply, np.repeat(_codes(cats_supply, supply), T)),
                "zone": _cat(cats_zone, np.repeat(_codes(cats_zone, zones), T)),
                "hour": hours,
                "mw": disp.reshape(-1).astype(np.float32),
                "lmp": prices[gen_zidx, :].reshape(-1),
            }
        )
    ]

    for name, arr in pseudo:
        a = np.asarray(arr, dtype=np.float32)[:, :T]
        ck = int(np.searchsorted(cats_klass, name))
        cf = int(np.searchsorted(cats_fuel, name))
        cs = int(np.searchsorted(cats_supply, ""))
        for z in range(a.shape[0]):
            zone = zone_names[z]
            frames.append(
                pd.DataFrame(
                    {
                        "unit_id": _cat(
                            cats_unit,
                            np.full(
                                T,
                                np.searchsorted(cats_unit, f"{name.upper()}_{zone}"),
                                dtype=np.int32,
                            ),
                        ),
                        "plant_code": np.full(T, 0, dtype=np.int32),
                        "klass": _cat(cats_klass, np.full(T, ck, dtype=np.int32)),
                        # Pseudo-units never re-attribute, so base == klass.
                        "klass_base": _cat(cats_klass, np.full(T, ck, dtype=np.int32)),
                        "fuel": _cat(cats_fuel, np.full(T, cf, dtype=np.int32)),
                        "supply": _cat(cats_supply, np.full(T, cs, dtype=np.int32)),
                        "zone": _cat(
                            cats_zone,
                            np.full(
                                T, np.searchsorted(cats_zone, zone), dtype=np.int32
                            ),
                        ),
                        "hour": np.arange(T, dtype=np.int32),
                        "mw": a[z],
                        "lmp": prices[z],
                    }
                )
            )

    df = pd.concat(frames, ignore_index=True)
    df.insert(
        0,
        "pass",
        pd.Categorical.from_codes(
            np.zeros(len(df), dtype=np.int8), categories=[pass_label]
        ),
    )
    df.insert(0, "year", np.int16(year))
    df["mw"] = df["mw"].astype(np.float32)
    df["lmp"] = df["lmp"].astype(np.float32)
    return df


def _write_class_hourly_sidecar(run_dir: Path, year: int, labels: list[str]) -> Path:
    """Write the committable class-hour dispatch sidecar for one year.

    Aggregates the (gitignored) unit-hour ``dispatch/<year>_<pass>.parquet``
    frames to ``(year, pass, klass, hour, mw)`` and writes
    ``hourly/class_hourly_<year>.parquet`` — a sub-MB committable summary so
    keeper diagnostics can read class-level dispatch and price series without
    replaying the solve (remote containers are ephemeral; before this sidecar
    every measurement session re-solved the keeper). ``hourly/`` escapes the
    slim-bundle gitignore rules by construction. Returns the path written.
    """
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    frames = [
        pd.read_parquet(
            run_dir / "dispatch" / f"{year}_{label}.parquet",
            columns=["year", "pass", "klass", "hour", "mw"],
        )
        .groupby(["year", "pass", "klass", "hour"], observed=True)["mw"]
        .sum()
        .reset_index()
        for label in labels
    ]
    out = hourly_dir / f"class_hourly_{year}.parquet"
    pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
    return out


#: Exact LP tranche-suffix vocabulary. Same closed set as
#: ``data/fleet/legacy_bins._coal_tranche_rank`` (the assembled order is
#: ``mustrun -> sync -> committed -> commitcyc -> econ ramp -> peak``, built at
#: ``fleet/assembly.py``'s ``tranches`` list); ``econc00..econcNN`` are the econ
#: ramp's smoothing slices and ``peak2`` exists, so those two match by prefix.
_TRANCHE_BANDS_EXACT = frozenset(
    {"mustrun", "committed", "commitcyc", "econlo", "econhi", "econ"}
)
_TRANCHE_BANDS_PREFIX = ("sync", "econc", "peak")


def _tranche_band(unit_id: str) -> str:
    """Return the LP offer-band suffix of ``unit_id``, or ``""`` if it has none.

    A CAMPD-binned thermal unit id is ``f"{bin_id}_{suffix}"`` where the suffix
    is a single token containing no underscore, so the band is the last
    underscore-delimited token. **But most LP columns are not tranches** —
    import pseudo-generators, hydro, wind/solar zone pseudo-units and legacy
    equal-width bins all carry ids whose last token is a zone name, a unit
    number or a corridor label. Splitting those blindly invents bands like
    ``Hudson`` / ``GEN1`` / ``tie`` / ``scarcity``, which is meaningless, and
    fragments the sidecar (it measured 59 distinct "bands" and 893,520 rows for
    one NYISO year before this guard, against 11 real bands).

    Matching against the closed vocabulary instead means a non-tranche column
    buckets to ``""`` and the class aggregate over it is still exact.
    """
    suffix = str(unit_id).rpartition("_")[2]
    if suffix in _TRANCHE_BANDS_EXACT or suffix.startswith(_TRANCHE_BANDS_PREFIX):
        return suffix
    return ""


def _band_categorical(unit_ids: pd.Series) -> pd.Categorical:
    """Return the per-row band ``Categorical`` of a ``unit_id`` column.

    Element-wise identical — values AND categories — to
    ``pd.Categorical([_tranche_band(u) for u in unit_ids.astype(str)])``, the
    per-row construction this replaces, but computed once per DISTINCT id.
    The band is a pure function of ``unit_id`` and a unit-hour frame carries
    ~1–3 k distinct ids against millions of rows (NEISO 2023 P1: 6,718,920
    rows), so the per-row form spent 6.7 M ``_tranche_band`` calls plus a
    14 s list comprehension materialising the strings of an already-categorical
    column. Here the column is read as (or factorised to) a categorical,
    ``_tranche_band`` runs over its categories only, and the band codes are
    looked up by the unit codes (wallclock A-3: 12.7 s → 2.2 s on that frame;
    ``docs/handoffs/wallclock-opportunities-2026-09.md`` §2).

    The categories are the sorted distinct bands PRESENT in the rows — never
    an unused unit category's band — so the result matches the per-row
    ``pd.Categorical(list)`` exactly, and a missing id (code ``-1``) maps to
    ``""`` just as ``str(nan)`` did.

    Args:
        unit_ids: The ``unit_id`` column (categorical or plain).

    Returns:
        A ``pd.Categorical`` of band tokens, one per row.
    """
    if isinstance(unit_ids.dtype, pd.CategoricalDtype):
        unit_cats = unit_ids.cat.categories
        unit_codes = unit_ids.cat.codes.to_numpy()
    else:
        as_cat = pd.Categorical(unit_ids.astype(str))
        unit_cats = as_cat.categories
        unit_codes = np.asarray(as_cat.codes)
    # One _tranche_band call per distinct id. The trailing "" slot is where a
    # missing id (code -1) lands — the non-band ``str(nan)`` produced before.
    band_per_unit = np.array([_tranche_band(u) for u in unit_cats] + [""], dtype=object)
    row_unit = np.where(unit_codes >= 0, unit_codes, len(unit_cats))
    # Categories are the sorted distinct bands the ROWS carry — exactly what
    # ``pd.Categorical(<per-row list>)`` infers — never an unused unit
    # category's band.
    band_cats = sorted(set(band_per_unit[np.unique(row_unit)]))
    band_pos = {b: i for i, b in enumerate(band_cats)}
    unit_to_band = np.array([band_pos.get(b, -1) for b in band_per_unit])
    return pd.Categorical.from_codes(unit_to_band[row_unit], categories=band_cats)


def _write_class_band_hourly_sidecar(
    run_dir: Path, year: int, labels: list[str]
) -> "Path | None":
    """Write the committable class-BAND-hour dispatch sidecar for one year.

    The offer-band refinement of :func:`_write_class_hourly_sidecar`:
    ``(year, pass, klass, band, hour, mw, mw_oil)`` →
    ``hourly/class_band_hourly_<year>.parquet``.

    **Why this exists (the standing nyiso-172 §2.5 / nyiso-173 limit).** No
    keeper bundle in ANY ISO persisted dispatch below the class aggregate, so
    every question of the form "which part of the class's offer stack actually
    ran" required replaying the solve. That limit blocked nyiso-178's G1,
    nyiso-179's G1/G3 and was binding for a third consecutive session; it is
    the only instrument that can settle nyiso-179 §6.1. The per-unit-hour frame
    this aggregates is already written every solve — it is simply gitignored —
    so this is an aggregation choice, not new plumbing.

    Two keys, because one is not enough:

    * ``klass`` is the PRE-re-attribution plant group (``klass_base`` in the
      unit-hour frame), so a class aggregate here counts the class's real
      dispatch. The ``klass`` column of ``class_hourly`` cannot: the dual-fuel
      re-attribution relabels a switched unit-hour to the POOLED ``oil`` class,
      which undercounts every dual-fuel class by an amount not attributable
      back out of ``oil``.
    * ``band`` is the LP tranche suffix — the last underscore token of
      ``unit_id`` (``mustrun``/``sync``/``committed``/``commitcyc``/
      ``econlo``/``econhi``/``econcNN``/``peak``), every one a single token
      containing no underscore, so the split is exact.

    ``mw_oil`` carries the re-attributed portion, so the ``class_hourly`` view
    is reproducible from this frame (a class's ``class_hourly`` MW is
    ``mw - mw_oil``, and the ``oil`` class is ``Σ mw_oil``) and no information
    is lost in either direction.

    Returns the path written, or ``None`` when the unit-hour frames predate the
    ``klass_base`` column (an older bundle being replayed) — the sidecar is
    additive and never fails a run.
    """
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for label in labels:
        src = run_dir / "dispatch" / f"{year}_{label}.parquet"
        # Readability probe, and the sidecar's whole fail-open contract. A
        # reused-year bundle may carry a dispatch frame this process cannot
        # read at all (a placeholder copied by the reuse path, a prune), and a
        # frame written before ``klass_base`` existed carries the column but
        # not the key. Neither is a reason to fail a solve for an ADDITIVE
        # diagnostic sidecar, so both skip it. Scoped to the schema probe
        # alone: once the file reads, a failure in the aggregation below is a
        # real bug and is allowed to raise.
        try:
            cols = pq.ParquetFile(src).schema.names
        except Exception:  # unreadable/placeholder frame — skip, never fail
            return None
        if "klass_base" not in cols:
            return None
        d = pd.read_parquet(
            src,
            columns=["year", "pass", "klass", "klass_base", "unit_id", "hour", "mw"],
        )
        # Once per distinct id, indexed by the categorical codes — see
        # _band_categorical (wallclock A-3); values and categories identical
        # to the former per-row ``pd.Categorical([...])`` construction.
        d["band"] = _band_categorical(d["unit_id"])
        d["mw_oil"] = np.where(
            d["klass"].astype(str).to_numpy() == "oil", d["mw"].to_numpy(), 0.0
        )
        frames.append(
            d.groupby(["year", "pass", "klass_base", "band", "hour"], observed=True)[
                ["mw", "mw_oil"]
            ]
            .sum()
            .reset_index()
            .rename(columns={"klass_base": "klass"})
        )
    out = hourly_dir / f"class_band_hourly_{year}.parquet"
    df = pd.concat(frames, ignore_index=True)
    df["mw"] = df["mw"].astype(np.float32)
    df["mw_oil"] = df["mw_oil"].astype(np.float32)
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        out,
        compression="zstd",
        version="2.6",
        use_dictionary=["pass", "klass", "band"],
        column_encoding={"hour": "DELTA_BINARY_PACKED"},
    )
    return out


def _write_p0_commitment_sidecar(
    run_dir: Path, year: int, p2_state: dict
) -> "list[Path]":
    """Write the OPT-IN P0 commitment sidecars for one year.

    ``--persist-p0-commitment`` only. Writes, into ``hourly/``:

    * ``p0_commitment_<year>.parquet`` — one row per generator,
      ``(year, gen_index, unit_id, on_bits)``, where ``on_bits`` is the
      bit-packed P0 on/off pattern from
      :func:`scripts.run_calibration.p0_commitment_pattern`. That boolean is
      the COMPLETE input ``compute_monthly_markup`` draws from the P0 pass, so
      a later session can rebuild a surrogate dispatch and replay the
      PRODUCTION markup bit-identically instead of reconstructing it.
    * ``startup_run_ratio_<year>.parquet`` — ``(year, hour, run_ratio)``, the
      ``(T,)`` conditional band series the markup was actually called with.
      Omitted when the run is on the v3 basis (``run_ratio_t is None``).

    Why this exists: committed ``hourly/`` sidecars carry ``pass == "P1"``
    only, so the markup's run-length source had to be reconstructed from P1
    prices — an unbounded-in-practice error that measured 18-22 pp on MISO's
    CT_PEAKER, wider than the +/-10 % bar it was being judged against
    (``FINDING-miso154-ct-commitment-instrument-2026-08-12.md`` section 4).

    Write-only and solve-invariant: at default the flag is off, ``p2_state``
    carries neither key, and this is never called. Returns the paths written
    (empty when the state carries no record).
    """
    if "p0_commitment_bits" not in p2_state:
        return []
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    bits = p2_state["p0_commitment_bits"]
    # Direct access, never a 3-arg getattr (T-2): ``Generator.unit_id`` is a
    # required field (``data/fleet/__init__.py:159``), so a default would only
    # ever mask a renamed attribute behind a column of empty strings.
    unit_ids = [str(g.unit_id) for g in p2_state["fleet"]]
    out = hourly_dir / f"p0_commitment_{year}.parquet"
    pd.DataFrame(
        {
            "year": np.int16(year),
            "gen_index": np.arange(bits.shape[0], dtype=np.int32),
            "unit_id": unit_ids,
            "on_bits": [row.tobytes() for row in bits],
        }
    ).to_parquet(out, index=False)
    written.append(out)

    ratio = p2_state.get("startup_run_ratio_t")
    if ratio is not None:
        ratio = np.asarray(ratio, dtype=float)
        out_r = hourly_dir / f"startup_run_ratio_{year}.parquet"
        pd.DataFrame(
            {
                "year": np.int16(year),
                "hour": np.arange(ratio.size, dtype=np.int32),
                "run_ratio": ratio.astype(np.float64),
            }
        ).to_parquet(out_r, index=False)
        written.append(out_r)
    return written


def _write_p0_dispatch_sidecar(
    run_dir: Path, year: int, p2_state: dict
) -> "list[Path]":
    """Write the OPT-IN P0 dispatch / dual sidecars for one year.

    ``--persist-p0-dispatch`` only. Writes, into ``hourly/``:

    * ``p0_dispatch_<year>.parquet`` — one row per generator,
      ``(year, gen_index, unit_id, n_hours, mw)``, where ``mw`` is the
      generator's ``(T,)`` P0 dispatch as raw little-endian ``float64`` bytes.
      Stored packed per row rather than long-form because the array is
      ``n_gen x 8760`` — on CAISO 1,705 x 8,760 — and a long frame would be
      ~15 M rows. ``float64`` and not a narrowed ``float32``: the sidecar
      exists so the screens replay EXACTLY, which makes the reproduction gate
      against the committed ``floors/`` array an equality rather than a
      tolerance; narrowing would buy ~60 MB at the cost of that property.
    * ``p0_prices_<year>.parquet`` — ``(year, zone, hour, price)``, the P0
      zonal duals, long-form (``n_zones x 8760`` is small). ``zone`` is the
      NAME, taken from ``p2_state["zone_names"]`` — the solve's own
      ``iso_config.zone_names``, which is the array's authoritative row
      ordering. It is written rather than left to be re-derived because a
      later ``fleet_only`` rebuild has ``config.zones is None`` and falls
      through to ``sorted(unique)``, which silently reorders the zones and
      reads every price from the wrong one (the defect caiso-286 section 4
      caught in its own probe).

    Why this exists (caiso-287): ``p0_commitment_<year>.parquet`` carries the
    on/off pattern only, which recovers the RA-bridge detector's ``runs`` but
    not the two screens that then act on them — the ``startup_aware`` run
    screen scores runs on ``(price - mc) x dispatch`` and the surplus decommit
    screen derives absorption from the interchange rows' dispatch, both in MW
    and both against the P0 duals. With this pair a later session replays
    :func:`model.commitment.caiso_ra_mustoffer_min_gen` exactly, offline and
    at zero LP, instead of bounding it analytically
    (``docs/RESULT-caiso286-cc-start-cost-2026-09-19.md`` section 7).

    Write-only and solve-invariant: at default the flag is off, ``p2_state``
    carries neither key, and this is never called. Returns the paths written
    (empty when the state carries no record).
    """
    if "p0_dispatch_mw" not in p2_state:
        return []
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    disp = np.asarray(p2_state["p0_dispatch_mw"], dtype=np.float64)
    # Direct access, never a 3-arg getattr (T-2): ``Generator.unit_id`` is a
    # required field, so a default would only mask a renamed attribute.
    unit_ids = [str(g.unit_id) for g in p2_state["fleet"]]
    if disp.shape[0] != len(unit_ids):
        raise ValueError(
            f"p0_dispatch has {disp.shape[0]} rows but the fleet has "
            f"{len(unit_ids)} — row alignment is the whole value of this "
            "sidecar, so a mismatch is a defect, not something to pad."
        )
    out = hourly_dir / f"p0_dispatch_{year}.parquet"
    pd.DataFrame(
        {
            "year": np.int16(year),
            "gen_index": np.arange(disp.shape[0], dtype=np.int32),
            "unit_id": unit_ids,
            "n_hours": np.int32(disp.shape[1]),
            "mw": [row.tobytes() for row in disp],
        }
    ).to_parquet(out, index=False)
    written.append(out)

    prices = p2_state.get("p0_zonal_prices")
    if prices is not None:
        prices = np.asarray(prices, dtype=float)
        zone_names = [str(z) for z in p2_state["zone_names"]]
        if prices.shape[0] != len(zone_names):
            raise ValueError(
                f"p0 prices have {prices.shape[0]} zone rows but the run "
                f"carries {len(zone_names)} zone names — the name map is the "
                "point of this file, so a mismatch is a defect."
            )
        n_z, n_t = prices.shape
        out_p = hourly_dir / f"p0_prices_{year}.parquet"
        pd.DataFrame(
            {
                "year": np.int16(year),
                "zone": np.repeat(np.asarray(zone_names, dtype=object), n_t),
                "zone_index": np.repeat(np.arange(n_z, dtype=np.int32), n_t),
                "hour": np.tile(np.arange(n_t, dtype=np.int32), n_z),
                "price": prices.reshape(-1).astype(np.float64),
            }
        ).to_parquet(out_p, index=False)
        written.append(out_p)
    return written


def _write_storage_hourly_sidecar(
    run_dir: Path, year: int, frames: "list[pd.DataFrame]"
) -> "Path | None":
    """Write the committable per-tech storage-hour sidecar for one year.

    Aggregates this year's (gitignored) ``storage.parquet`` frames to
    ``(year, pass, tech, hour, charge_mw, discharge_mw, soc_mwh,
    energy_cap_mwh)`` and writes ``hourly/storage_<year>.parquet``. The class
    sidecar carries generator classes only, so before this the sole storage
    series a committed slim bundle exposed was the ISO-aggregate net recovered
    from the energy balance — battery and pumped storage inseparable, which is
    exactly the band FINDING-caiso125 §4a/§6.4 flagged as unobservable and
    FINDING-caiso127 §2 needs to attribute the evening-overnight price pin to a
    technology. Write-only and solve-invariant. Returns the path written, or
    ``None`` when the fleet is empty.

    **``soc_mwh`` / ``energy_cap_mwh`` (2026-09-16, caiso-284)** carry through
    from :func:`_storage_frame` — see its docstring for why. SUMMING them over
    a tech's units is the right aggregation and is what makes the pair usable
    at this grain: stored energy is extensive, so ``Σ soc`` is the tech's total
    reservoir content and ``Σ cap - Σ soc`` is its true absorption headroom.
    (That is precisely what a per-unit *reconstruction* from charge/discharge
    cannot recover, because each unit's cyclic constraint binds separately.)
    ``soc_mwh`` sums with ``min_count=1`` so an all-NaN tech-hour — a solve that
    carried no SOC block — stays NaN instead of collapsing to a misleading 0.0.
    """
    rows = [f for f in frames if f is not None and int(f["year"].iloc[0]) == year]
    if not rows:
        return None
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    out = hourly_dir / f"storage_{year}.parquet"
    df = pd.concat(rows, ignore_index=True)
    keys = ["year", "pass", "tech", "hour"]
    # Older frames (a resumed/reused year written before this column existed)
    # may lack the pair; emit NaN rather than raising, so a mixed bundle still
    # writes and the reader sees "not recorded" explicitly.
    for col in ("soc_mwh", "energy_cap_mwh"):
        if col not in df.columns:
            df[col] = np.float32("nan")
    agg = df.groupby(keys, observed=True).agg(
        charge_mw=("charge_mw", "sum"),
        discharge_mw=("discharge_mw", "sum"),
        soc_mwh=("soc_mwh", lambda s: s.sum(min_count=1)),
        energy_cap_mwh=("energy_cap_mwh", lambda s: s.sum(min_count=1)),
    )
    agg.reset_index().to_parquet(out, index=False)
    return out


def _unit_hourly_frame(
    year: int, pass_label: str, result, context, fleet_arrays, iso: str = "ERCOT"
) -> "pd.DataFrame | None":
    """Per-LP-unit hourly dispatch, capacity, OFFER and reduced cost for one year-pass.

    The committed class sidecar sums dispatch to 14 classes and the storage
    sidecar to 3 techs, so a slim bundle exposes **no per-unit series at all** —
    which is why ``docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`` §4 records
    ask A2's D1 (the plant-level ONLINE/synchronized reserve measure PJM already
    uses, ``results.scarcity.reserve_headroom``) as BLOCKED on a data gap. That
    measure needs exactly two per-unit-hour series: the solved ``mw`` and the
    availability-derated cap ``pmax x availability`` the LP bounded it by —
    online status is then the plant-level ``sum(mw) > threshold`` and headroom
    is ``sum(cap_mw) - sum(mw)`` over the online plants (both sums are linear in
    the tranches, so the plant grain is recovered exactly from this frame).

    Attributes ride along raw — ``fuel`` straight from ``context.fuel_types``
    (the RESERVE/QUICK_START masks key on it) and ``plant_group`` from the fleet
    arrays — so nothing here re-derives the ``_dispatch_frame`` classifier and
    the two can never drift. Renewable/must-run pseudo-units are NOT included:
    they carry no LP capacity bound, and their series are already the class
    sidecar's ``wind``/``solar``/must-run rows.

    **``mc`` and ``red_cost`` (nyiso-180)** are the pass's own
    ``DispatchResult.gen_mc`` / ``gen_reduced_cost`` — the marginal-cost array
    the LP installed in its objective and the generation columns' HiGHS
    reduced cost. They are what turns this frame from a dispatch record into
    an OPTIMALITY record, and they exist because three consecutive NYISO
    sessions (172 §2.5, 173, 179 §6.1) closed unable to say why in-the-money
    steam goes un-dispatched: no committed artifact carried a per-generator
    series at all, so every attempt had to RECONSTRUCT the offer outside the
    solve and could never rule out that it was measuring a different object
    than the one that cleared. With both columns here, joined to
    ``hourly/system_<year>.parquet``'s zonal ``price``, the generation
    column's stationarity identity closes per unit-hour,

        red_cost[g,t] = mc[g,t] - price[zone(g),t] + sum_r a(r,g) * y_r,

    so the residual ``red_cost - (mc - price)`` measures, exactly and with no
    free parameter, the net rent every NON-energy row charges that unit-hour
    — and the sign of ``red_cost`` says which bound the column sits at (> 0
    lower, < 0 upper, ~ 0 interior). A unit-hour that is in the money and at
    its lower bound is then not a puzzle but an accounting question with an
    answer in the frame.

    Both are float32 on the result already (see ``DispatchResult.gen_mc``);
    they are the reason this frame is worth its bytes, and they are still
    write-only — every input is a solved output.

    Write-only and solve-invariant: every input is a solved output or an LP
    input the solve already consumed. Returns ``None`` when the pass carried no
    generators or the fleet arrays do not align with the dispatch block.
    """
    disp = np.asarray(result.dispatch, dtype=np.float32)
    if disp.size == 0:
        return None
    n_gen, T = disp.shape
    fa = fleet_arrays
    if fa is None or np.asarray(fa.pmax).shape[0] != n_gen:
        # Misalignment is a bundle-quality problem, never a reason to fail a
        # solve: skip the sidecar and leave the rest of the bundle intact.
        logger.warning(
            "unit_hourly sidecar skipped for %d %s: fleet arrays (%s) do not "
            "align with the dispatch block (%d gens)",
            year,
            pass_label,
            None if fa is None else np.asarray(fa.pmax).shape,
            n_gen,
        )
        return None
    cap = (
        np.asarray(fa.pmax, dtype=np.float32)[:, None]
        * np.asarray(fa.availability, dtype=np.float32)
    )[:, :T]
    # The solve's own offer and reduced cost, aligned to the SAME (n_gen, T)
    # dispatch block. Absent on a legacy/pickled result (the field post-dates
    # it), in which case the two columns are simply not written rather than
    # filled with a placeholder a reader could mistake for a measurement.
    _mc = getattr(result, "gen_mc", None)
    _rc = getattr(result, "gen_reduced_cost", None)
    _mc = None if _mc is None else np.asarray(_mc, dtype=np.float32)[:n_gen, :T]
    _rc = None if _rc is None else np.asarray(_rc, dtype=np.float32)[:n_gen, :T]
    if _mc is not None and _mc.shape != disp.shape:
        _mc = None
    if _rc is not None and _rc.shape != disp.shape:
        _rc = None
    unit_ids = [str(u) for u in context.unit_ids][:n_gen]
    fuels = [str(f) for f in context.fuel_types][:n_gen]
    zones = [str(z) for z in context.zones][:n_gen]
    groups = getattr(fa, "plant_group", None)
    groups = [str(g) for g in groups][:n_gen] if groups is not None else [""] * n_gen
    # Same plant-code convention as _dispatch_frame, so the two frames join.
    plant_codes = _plant_codes_from_unit_ids(unit_ids, numeric_head=iso != "ERCOT")

    # PERF-A prototype (NOT-FOR-MERGE): categorical-from-codes label columns,
    # same mechanics and identity argument as _dispatch_frame above.
    def _vocab(values):
        return np.sort(pd.unique(np.asarray(values, dtype=object)))

    def _repcat(values):
        cats = _vocab(values)
        codes = np.searchsorted(cats, np.asarray(values, dtype=object)).astype(np.int32)
        return pd.Categorical.from_codes(np.repeat(codes, T), categories=cats)

    n_rows = n_gen * T
    df = pd.DataFrame(
        {
            "year": np.full(n_rows, year, dtype=np.int16),
            "pass": pd.Categorical.from_codes(
                np.zeros(n_rows, dtype=np.int8), categories=[pass_label]
            ),
            "unit_id": _repcat(unit_ids),
            "plant_code": np.repeat(plant_codes.astype(np.int32), T),
            "plant_group": _repcat(groups),
            "fuel": _repcat(fuels),
            "zone": _repcat(zones),
            "hour": np.tile(np.arange(T, dtype=np.int32), n_gen),
            "mw": disp.reshape(-1),
            "cap_mw": cap.reshape(-1),
        }
    )
    if _mc is not None:
        df["mc"] = _mc.reshape(-1)
    if _rc is not None:
        df["red_cost"] = _rc.reshape(-1)
    return df


def _network_frame(year: int, pass_label: str, result, links) -> "pd.DataFrame | None":
    """Per-link and per-interface-group hourly flow, dual and limit.

    The committable half of ``flows.parquet`` plus the piece it never carried:
    the **duals**. A binding transmission limit shows up in a slim bundle only
    as a positive zonal spread, and ``FINDING-caiso132`` §2 states the resulting
    limit honestly — the spread says *some* import-direction limit binds but not
    WHICH of the corridor deliverability group, the link's own TTC, or the
    simultaneous-import interface. This frame separates them, because the LP's
    flow-column stationarity gives, exactly,

        lambda_to - lambda_from = -z_link - sum_g s(g,link) * y_g

    with ``z_link`` the link column's reduced cost, ``y_g`` each containing
    group's row dual and ``s`` its signed membership. Every right-hand term is
    the rent charged by ONE limit, so the spread decomposes per leg per hour
    with no replay.

    Two record kinds share the frame, keyed by ``kind``:

    * ``link`` — ``name`` is ``"<from>><to>"``, ``mw`` the signed flow
      (positive = from->to), ``dual`` the column's reduced cost, and
      ``limit_up`` / ``limit_dn`` the flow column's own bounds.
    * ``group`` — ``name`` is ``"grp:"`` + the signed member links joined by
      ``"+"``/``"-"`` (self-describing, so no group-label channel has to be
      threaded through the solve path), ``mw`` the group's signed member sum,
      ``dual`` the row dual, ``limit_up`` / ``limit_dn`` the row bounds.

    ``dual`` is HiGHS-raw in both cases and deliberately NOT sign-normalised: a
    two-sided group row can bind up or down and the reader must be able to tell
    which. In a minimisation a binding upper bound carries a non-positive dual,
    so the identity above reads ``-y >= 0`` for an import-direction bind.

    Write-only and solve-invariant. Returns ``None`` when the solve carried no
    flows (single-zone ISO).
    """
    flows = getattr(result, "flows", None)
    if flows is None or links is None or len(links) == 0:
        return None
    flows = np.asarray(flows, dtype=np.float32)
    n_links, T = flows.shape
    link_names = [f"{ln.from_zone}>{ln.to_zone}" for ln in links][:n_links]

    def _col(arr, fill=np.nan):
        """(n, T) float32 view of an optional result array, else a fill block."""
        if arr is None:
            return np.full((n_links, T), fill, dtype=np.float32)
        return np.asarray(arr, dtype=np.float32)[:n_links, :T]

    hours = np.tile(np.arange(T, dtype=np.int32), n_links)
    frames = [
        pd.DataFrame(
            {
                "kind": "link",
                "name": np.repeat(np.asarray(link_names, dtype=object), T),
                "hour": hours,
                "mw": flows.reshape(-1),
                "dual": _col(getattr(result, "flow_dual", None)).reshape(-1),
                "limit_up": _col(getattr(result, "flow_cap_up", None)).reshape(-1),
                "limit_dn": _col(getattr(result, "flow_cap_dn", None)).reshape(-1),
            }
        )
    ]

    g_dual = getattr(result, "interface_dual", None)
    g_idx = getattr(result, "interface_link_idx", None)
    g_sgn = getattr(result, "interface_signs", None)
    if g_dual is not None and g_idx:
        g_dual = np.asarray(g_dual, dtype=np.float32)
        cap_up = getattr(result, "interface_cap_up", None)
        cap_dn = getattr(result, "interface_cap_dn", None)
        seen_labels: dict[str, int] = {}
        for gi, idx in enumerate(g_idx):
            idx = np.asarray(idx, dtype=int)
            signs = (
                np.ones(idx.size)
                if not g_sgn
                else np.asarray(g_sgn[gi], dtype=float)[: idx.size]
            )
            label = "grp:" + "".join(
                f"{'+' if s > 0 else '-'}{link_names[i]}"
                for i, s in zip(idx, signs)
                if i < n_links
            )
            # Two groups CAN share a signed membership (a static cap plus an
            # hourly overlay on the same links). Suffix the repeat so ``name``
            # stays a key — a reader selecting by label must never silently
            # collect two groups' duals into one 2T-long series.
            seen_labels[label] = seen_labels.get(label, 0) + 1
            if seen_labels[label] > 1:
                label = f"{label}#{seen_labels[label]}"
            member = np.zeros(T, dtype=np.float32)
            for i, s in zip(idx, signs):
                if i < n_links:
                    member += np.float32(s) * flows[i]
            frames.append(
                pd.DataFrame(
                    {
                        "kind": "group",
                        "name": label,
                        "hour": np.arange(T, dtype=np.int32),
                        "mw": member,
                        "dual": g_dual[gi, :T],
                        "limit_up": (
                            np.full(T, np.nan, dtype=np.float32)
                            if cap_up is None
                            else np.asarray(cap_up, dtype=np.float32)[gi, :T]
                        ),
                        "limit_dn": (
                            np.full(T, np.nan, dtype=np.float32)
                            if cap_dn is None
                            else np.asarray(cap_dn, dtype=np.float32)[gi, :T]
                        ),
                    }
                )
            )

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "kind", "name"):
        df[col] = df[col].astype("category")
    return df


def _write_hourly_sidecar(
    run_dir: Path, year: int, name: str, frames: "list[pd.DataFrame]"
) -> "Path | None":
    """Concatenate this year's ``frames`` into ``hourly/<name>_<year>.parquet``.

    Shared tail of the per-year committable sidecars that are already built as
    per-pass frames (``unit_hourly`` / ``network``), the same ``hourly/``
    convention — and the same gitignore escape — as the class/storage/system
    sidecars.

    Two encoding choices, both load-bearing for whether a KEEPER bundle can
    carry these at all (rule 15 ``[R-DASHBOARD]``):

    * **zstd**, because both frames are long runs of repeated per-unit /
      per-link values where it is materially smaller than the snappy default
      at no read cost;
    * **``DELTA_BINARY_PACKED`` on ``hour``**, because these frames are tall
      and narrow and the tiled ``0..8759`` ramp otherwise falls back to PLAIN
      int32 and *dominates the file*. Measured on the CAISO 2023 unit frame
      (14.2 M rows): 12.60 MB total, of which ``hour`` alone was **11.12 MB**
      against 1.04 MB for ``mw`` + ``cap_mw``; delta-packing the ramp takes the
      whole file to **1.74 MB**. Lossless — same rows, values and dtypes.

    Returns the path, or ``None`` when the year produced no frames.
    """
    rows = [f for f in frames if f is not None and int(f["year"].iloc[0]) == year]
    if not rows:
        return None
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    out = hourly_dir / f"{name}_{year}.parquet"
    df = pd.concat(rows, ignore_index=True)
    # pyarrow requires an explicit per-column dictionary list whenever
    # column_encoding is given, so name the low-cardinality label columns.
    dict_cols = [
        c for c in df.columns if str(df[c].dtype) == "category" or df[c].dtype == object
    ]
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        out,
        compression="zstd",
        version="2.6",
        use_dictionary=dict_cols,
        column_encoding=(
            {"hour": "DELTA_BINARY_PACKED"} if "hour" in df.columns else None
        ),
    )
    return out


def _write_system_year_sidecars(run_dir: Path, system_df: pd.DataFrame) -> None:
    """Write per-year committable slices of the system frame to ``hourly/``.

    ``system.parquet`` itself is gitignored by the slim-bundle rules; these
    per-year copies (``hourly/system_<year>.parquet``) are small enough to
    commit for keeper bundles, giving probes the hourly price/demand series
    without a replay.
    """
    hourly_dir = run_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    for year, g in system_df.groupby("year"):
        g.to_parquet(hourly_dir / f"system_{int(year)}.parquet", index=False)


def _flows_frame(year: int, pass_label: str, result, links) -> "pd.DataFrame | None":
    """Per-link hourly flow frame for the bundle (``flows.parquet``).

    One row per (link, hour) with the LP's signed flow (positive = from->to).
    Persisted so interface-binding diagnostics — the MISO zonal-refinement
    structural gates report binding-hour counts per CIL/CEL zone group and
    the RDT — can be computed from the bundle without re-solving. Returns
    ``None`` when the solve carried no flows (single-zone ISO).
    """
    flows = getattr(result, "flows", None)
    if flows is None or links is None or len(links) == 0:
        return None
    n_links, hours = flows.shape
    return pd.DataFrame(
        {
            "year": np.full(n_links * hours, year, dtype="int32"),
            "pass": pass_label,
            "from_zone": np.repeat([ln.from_zone for ln in links], hours),
            "to_zone": np.repeat([ln.to_zone for ln in links], hours),
            "hour": np.tile(np.arange(hours, dtype="int32"), n_links),
            "mw": flows.reshape(-1),
        }
    )


# caiso-110: the external WECC-West zone(s) whose real fleet + demand must be
# excluded from CAISO's scored metrics (the results pipeline is zone-blind). The
# endogenous node keeps the single WECC_import zone (no per-hub split).
_WECC_ENDOGENOUS_EXTERNAL_ZONES: frozenset[str] = frozenset({"WECC_import"})


def _wecc_net_import_row(
    year: int, pass_label: str, result, links, zone_names: list[str], hours: int
) -> "pd.DataFrame | None":
    """Synthetic ``klass='import'`` row carrying the endogenous WECC net import.

    With the endogenous WECC-West node (caiso-110), CAISO's net import is the
    tie FLOW into the CAISO zones (WECC_import->NP15 + WECC_import->SP15_rest,
    positive = West->CA = import), NOT the West fleet's total dispatch. The West
    fleet rows are zone-excluded from the dispatch frame; this single pseudo-unit
    re-injects the net import so the interchange fuelRow + the net-import metric
    (vs actual 28.9/32.4/36.2 TWh) and the C7/C8 total-load denominator stay
    correct. Priced at the NP15 LMP (a CAISO trading zone). Returns ``None`` when
    the solve carried no flows.
    """
    flows = getattr(result, "flows", None)
    if flows is None or not links:
        return None
    net = np.zeros(hours, dtype=np.float32)
    for i, ln in enumerate(links):
        if ln.from_zone == "WECC_import" and ln.to_zone in ("NP15", "SP15_rest"):
            net += np.asarray(flows[i, :hours], dtype=np.float32)
    zidx = {z: i for i, z in enumerate(zone_names)}
    np15 = zidx.get("NP15", 0)
    lmp = np.asarray(result.prices, dtype=np.float32)[np15, :hours]
    return pd.DataFrame(
        {
            "year": np.int16(year),
            "pass": pass_label,
            "unit_id": "WECC_WEST_NET_IMPORT",
            "plant_code": np.int32(0),
            "klass": "import",
            "fuel": "import",
            "supply": "",
            "zone": "NP15",
            "hour": np.arange(hours, dtype=np.int32),
            "mw": net,
            "lmp": lmp,
        }
    )


def _system_frame(
    year: int,
    pass_label: str,
    result,
    demand: np.ndarray,
    zone_names: list[str],
    iso: str | None = None,
    ercot_rtordpa_overlay: bool = False,
    ercot_dam_as_overlay: bool = False,
    ercot_dam_as_overlay_from_year: int = 2024,
    ercot_dam_as_scarcity_threshold: float = 150.0,
    ercot_reserve_supply_cap: bool = False,
    ercot_storage_as_endogenous: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_ordc_cap_dual_adder: bool = False,
    ercot_ordc_adder_published_anchor: bool = False,
    ercot_ordc_adder_family_counterpart: bool = False,
    ordc_voll: "float | None" = None,
    ercot_ordc_realized_adder: "np.ndarray | None" = None,
) -> pd.DataFrame:
    """Return the per-zone hourly price / slack / demand frame.

    Also carries ``marginal_emission_rate`` (tCO2/MWh) when the solve produced
    one — the emissions dual, i.e. the CO2 consequence of a marginal MWh in
    that zone-hour. It is the committable basis for marginal-abatement-cost
    work; ``DispatchResult.marginal_emission_rate`` states what it is and the
    two properties (direction at a degenerate vertex, and the zero-carbon /
    import boundary) a consumer has to carry. Absent for a year restored from
    a cache written before the dual was wired.

    When energy+reserve co-optimization is on, ``result.reserve_price`` is the
    reserve-balance-row dual (the reserve clearing price already folded into the
    energy ``price`` via the shared-headroom constraint); it is persisted as a
    system-wide column (broadcast across zones, matching PJM's RTO-wide reserve
    clearing price) so the residual analysis can separate the energy and reserve
    components. Energy-only runs write 0.0.

    ``ercot_rtordpa_overlay`` adds the measured, regime-gated RTORDPA
    (reliability-deployment price adder) to the energy ``price`` for every zone
    — a post-solve, additive price overlay (no dispatch / volume change), with
    the raw added series persisted in a ``rtordpa_overlay`` column for audit.
    See ``market_sim.results.scarcity.ercot_rtordpa_overlay_series``.

    ``ercot_ordc_cap_dual_adder`` swaps the additive ORDC adder's source from
    the total-family balance dual to the reserve-supply-cap rows' duals
    (summed across headroom tiers) — the uninternalized reserve scarcity
    component. See the inline comment at the adder branch below.

    ``ercot_ordc_adder_published_anchor`` (ercot-213) re-anchors that additive
    component onto the published ``(VOLL - lambda)`` formula and takes a
    SINGLE counterpart (the all-tier / total-reserve cap dual) instead of the
    two-tier sum; ``ordc_voll`` supplies the registered VOLL it needs.

    ``ercot_ordc_adder_family_counterpart`` (ercot-215) decontaminates that
    single counterpart: one capped reserve MW serves an AS-product row and the
    ORDC total row simultaneously, so the all-tier cap dual is the SUM of the
    ORDC total family's own balance-row dual and the AS-product shortfall-ramp
    steps. The armed branch writes ``min(gamma_all, gamma_ordc_family)`` — the
    ORDC component alone — because 2023-25 ERCOT prices no RT per-product
    scarcity (see the inline comment at the branch).

    ``ercot_dam_as_overlay`` likewise adds the measured DAM AS-scarcity overlay
    (the day-ahead co-optimization scarcity rent, gated to scarce hours and scoped
    to ``ercot_dam_as_overlay_from_year``+, default 2024), persisted in a
    ``dam_as_overlay`` column. The two overlays sum into ``price``; they do not
    overlap by year (RTORDPA carries 2023, DAM-AS carries 2024+). See
    ``market_sim.results.scarcity.ercot_dam_as_overlay_series``.
    """
    prices = np.asarray(result.prices, dtype=float)
    slack = np.asarray(result.slack, dtype=float)
    # Per-zone overgeneration dump (LP ``Dump[z,t]``): the MW the LP could
    # neither serve, export, nor absorb and had to spill at ``dump_cost``. A
    # real oversupply signal (distinct from renewable curtailment, which shows
    # as W/S below their CF ceiling); persisted so the curtailment/oversupply
    # diagnostics can see when the negative-MC dump guard actually binds.
    dump = getattr(result, "dump", None)
    dump = np.zeros_like(prices) if dump is None else np.asarray(dump, dtype=float)
    n_zones, T = prices.shape
    reserve_price = getattr(result, "reserve_price", None)
    rp = (
        np.zeros(T, dtype=float)
        if reserve_price is None
        else np.asarray(reserve_price, dtype=float).ravel()[:T]
    )
    overlay = None
    dam_as = None
    ordc_adder = None
    if iso == "ERCOT":
        from market_sim.results.scarcity import (
            ercot_dam_as_overlay_series,
            ercot_market_regime,
            ercot_rtordpa_overlay_series,
        )

        if ercot_rtordpa_overlay:
            overlay = ercot_rtordpa_overlay_series(year, T)
        if ercot_dam_as_overlay:
            dam_as = ercot_dam_as_overlay_series(
                year,
                T,
                scarcity_threshold=ercot_dam_as_scarcity_threshold,
                from_year=ercot_dam_as_overlay_from_year,
            )
        if ercot_ordc_realized_adder is not None:
            # ORDC-only scarcity pricing (ercot57 joint round v2): RTORPA
            # computed post-solve on the P1 result's realized envelope room
            # (scarcity.ercot_ordc_realized_adder — the published
            # SCED-plus-adder settlement construction). Takes precedence over
            # the cap-dual / total-family branches below; rule 19 (one
            # mechanism per phenomenon) is enforced upstream — the in-LP
            # total family cannot coexist with ercot_ordc_only_scarcity.
            ordc_adder = np.asarray(ercot_ordc_realized_adder, dtype=float)[:T].copy()
        elif (
            ercot_reserve_supply_cap
            and not ercot_storage_as_endogenous
            and ercot_market_regime(year, None) == "ordc"
        ):
            # PRE-RTC+B (ORDC-regime) ADDITIVE construction: with the reserve
            # supply capped at measured RTOLCAP, the co-opt reserve dual is the
            # ORDC price adder (RTORPA) ERCOT added to the energy SPP — RTSPP =
            # SPP + ORDC(online reserves). A pure reserve cap prices reserve
            # WITHOUT lifting the energy LMP (energy cancels out of a ΣR cap), so
            # the dual is NOT folded into ``prices`` and is added here, matching
            # the energy-only-SCED-plus-adder design of 2023-2025. The forward
            # RTC+B regime instead co-optimizes (the dual lifts the LMP through
            # the shared-headroom constraint), so this additive step is gated OFF
            # for year >= the RTC+B go-live AND under the G5 endogenous-storage
            # forward co-opt (``ercot_storage_as_endogenous``): there the
            # multi-product co-opt already prices the AS scarcity endogenously, so
            # re-adding the capped reserve dual post-solve would DOUBLE-count it
            # (the broad-month over-fire run161 documented). The cap then acts as a
            # pure reserve-SUPPLY bound — storage's cleared AS counts toward the
            # measured RTOLCAP online capability — while the LMP stays the co-opt's
            # own price, so the acute/tail incidence holds vs the uncapped co-opt.
            # Measured supply + published-rule curve, no price fit.
            # Under the multi-product stack with the lumped ORDC total-reserve
            # family (ercot_ordc_total_reserve), the adder is the TOTAL
            # family's balance dual only — RTORPA is the ORDC on total online
            # reserves; the per-product duals are MCPCs paid to AS providers,
            # never added to the energy price. The total family is appended
            # LAST by reserve_config, so it is the final dual column.
            # ercot_ordc_cap_dual_adder (the ercot52 double-count fix): the
            # balance dual is the RIGHT adder only while the RTOLCAP cap row is
            # the binding reserve constraint — "energy cancels out of a ΣR cap"
            # holds and the energy dual stays clean. When the PHYSICAL shared
            # headroom binds instead (post coal-net-summer-derate summers), the
            # balance dual is already folded into the energy LMP
            # (tests/test_reserve_coopt.py::test_total_shortfall_prices_and_lifts_lmp)
            # and re-adding it double-prices the hour. The supply-cap rows' own
            # dual is exactly the uninternalized component in BOTH regimes (LP
            # reduced cost of a supplying R column: λ_balance = λ_cap + μ_headroom,
            # and only μ passes into the energy dual), so under the flag the
            # additive RTORPA is the cap-row duals summed across tiers. Pure
            # LP-duality rewiring of the same published-ORDC construction — no
            # new parameter, no price fit; default off (keeper-reproducing).
            cap_dual = getattr(result, "reserve_supply_cap_dual", None)
            rpf = getattr(result, "reserve_price_by_family", None)
            if ercot_ordc_cap_dual_adder and cap_dual is not None:
                cd = np.asarray(cap_dual, dtype=float)[:, :T]
                if ercot_ordc_adder_published_anchor:
                    # ercot-213 ANCHORING REPAIR of the cap-additive regime
                    # (docs/FINDING-ercot212-reserve-basis-phase0-2026-08-16.md
                    # §5, the named successor). Two defects of the branch above,
                    # both structural and both visible only once the ercot-212
                    # credit netting makes the regime reachable in more than
                    # 42/2/1 hours a year:
                    #
                    # (a) ANCHOR. The in-LP ORDC demand curve is VOLL-anchored
                    #     (scarcity.ercot_ordc_demand_steps: an LP objective
                    #     coefficient must be a constant, and lambda is
                    #     endogenous) — the co-optimization-correct form, where
                    #     the dual lifts the energy LMP and lambda is already
                    #     carried there. The PUBLISHED ADDITIVE formula this
                    #     branch writes is instead
                    #         RTORPA = 0.5 (VOLL - lambda) (LOLP_f + LOLP_h),
                    #     capped so lambda + adders <= VOLL (the system-wide
                    #     offer cap). Writing the VOLL-anchored dual verbatim
                    #     into an ADDITIVE channel over-prices every hour by
                    #     exactly the missing lambda subtraction.
                    # (b) COUNTERPART. Summing both headroom tiers' cap duals
                    #     adds two ORDC prices for one ORDC. RTORPA is ONE
                    #     number on ONE reserve level; the total-reserve family
                    #     the additive channel prices is bounded by the ALL tier
                    #     (RTOLCAP + RTOFFCAP), so that row is its counterpart.
                    #     Measured consequence of the sum: a maximum written
                    #     adder of 2 x VOLL = $10,000/MWh, which the protocol
                    #     cap makes unreachable in the real market.
                    #
                    # The repair is EXACT and carries zero fitted scalars.
                    # Because the LP step price at the marginal reserve level is
                    #     gamma = 0.5 VOLL (LOLP_f + LOLP_h)
                    # at that same level, gamma * (VOLL - lambda) / VOLL IS the
                    # published adder at that level — a change of anchor, not a
                    # change of curve, of level or of basis. VOLL is the
                    # registered ScenarioConfig ``ordc_voll``; lambda is the LP's
                    # own demand-weighted system energy dual (the model analogue
                    # documented in results/scarcity.py); the final min() is the
                    # published protocol cap. Where the LP step is an OBDRR048
                    # FLOOR step rather than an LOLP step the rescale under-
                    # states the published floor by lambda/VOLL — conservative,
                    # and measured negligible (at the floor's <= 7,000 MW
                    # reserve levels the LOLP price is ~$200+, an order of
                    # magnitude above the $10/$20 floor, so the floor never sets
                    # the step). The published TWO-BASIS form (half-hour term at
                    # the online tier, floor keyed to online) is a separate,
                    # separately-gated increment — not this flag.
                    if ordc_voll is None:
                        raise ValueError(
                            "ercot_ordc_adder_published_anchor needs ordc_voll "
                            "(the registered VOLL the published (VOLL - lambda) "
                            "anchor subtracts from)"
                        )
                    voll = float(ordc_voll)
                    dem = demand[:, :T]
                    tot_dem = dem.sum(axis=0)
                    lam = np.where(
                        tot_dem > 0.0,
                        (prices[:, :T] * dem).sum(axis=0)
                        / np.where(tot_dem > 0.0, tot_dem, 1.0),
                        prices[:, :T].mean(axis=0),
                    )
                    headroom_to_cap = np.maximum(voll - lam, 0.0)
                    # Single counterpart: the ALL tier is the LAST headroom row
                    # (reserves/spec.py builds headroom_eligible as
                    # [fast, all]); a single-row cap (lumped single-product
                    # design) is itself the total-reserve row.
                    gam = cd[-1]
                    if ercot_ordc_adder_family_counterpart:
                        # ercot-215 COUNTERPART DECONTAMINATION (the ercot-214
                        # identification: docs/FINDING-ercot214-gspur-phase0-
                        # 2026-08-17.md §0-§3). One capped reserve MW serves an
                        # AS-product row and the ORDC total row simultaneously,
                        # so the all-tier cap dual is their SUM — measured to
                        # decompose exactly, in 808/808 writing hours across
                        # 2023-25, as
                        #   gamma_all = k x (VOLL / ercot_as_n_ramp)
                        #               + gamma_ordc_family,   k integer
                        # i.e. the AS-product shortfall-ramp step leaking into
                        # the written price. 2023-25 ERCOT has NO real-time
                        # per-product scarcity pricing — a product-vs-
                        # capability squeeze triggers RUC commitment, not a
                        # price (the ercot_ordc_only_scarcity citation block,
                        # model/reserves/spec.py); the ORDC on realized TOTAL
                        # reserves is the only RT adder, and the total
                        # family's own balance-row dual is its faithful mirror
                        # (matches published RTORPA in both regimes,
                        # ercot-214 §1-§2). So write the ORDC component alone:
                        #   gamma' = min(gamma_all, gamma_ordc_family).
                        # The min form (rather than gamma_fam verbatim) keeps
                        # the protocol-capped hours exact: where the written
                        # adder saturates at VOLL - lambda, both operands sit
                        # at or above the cap and the min changes nothing. The
                        # ramp's IN-LP role — physical withholding of the DAM
                        # AS plans — is untouched; only its export into the
                        # written price stops. Zero fitted scalars: both
                        # operands are duals of the same LP solve.
                        if rpf is None:
                            raise ValueError(
                                "ercot_ordc_adder_family_counterpart needs "
                                "reserve_price_by_family (the ORDC total "
                                "family's own balance-row dual) — without "
                                "the multi-product family stack there is no "
                                "decontaminated counterpart to read"
                            )
                        fam = np.asarray(rpf, dtype=float)[:T, -1]
                        gam = np.minimum(gam, fam)
                    ordc_adder = np.minimum(
                        gam * headroom_to_cap / voll, headroom_to_cap
                    )
                else:
                    ordc_adder = cd.sum(axis=0).copy()
            elif ercot_ordc_total_reserve and rpf is not None:
                ordc_adder = np.asarray(rpf, dtype=float)[:T, -1].copy()
            else:
                ordc_adder = rp.copy()
    # Marginal emission rate (tCO2/MWh), the emissions dual -- see
    # ``DispatchResult.marginal_emission_rate``. Written RAW, i.e. against the
    # LP's own energy-balance dual rather than the overlaid ``price`` column
    # below: the ORDC / RTORDPA / DAM-AS adders are POST-SOLVE price adders
    # that leave dispatch untouched by construction, so they cannot move a CO2
    # response and adding them here would only invite a reader to difference
    # two objects that never shared a basis.
    mer = getattr(result, "marginal_emission_rate", None)
    if mer is not None:
        mer = np.asarray(mer, dtype=float)
        if mer.shape != (n_zones, T):
            mer = None
    total_overlay = np.zeros(T, dtype=float)
    if overlay is not None:
        total_overlay = total_overlay + overlay
    if dam_as is not None:
        total_overlay = total_overlay + dam_as
    if ordc_adder is not None:
        total_overlay = total_overlay + ordc_adder
    rows = []
    for z in range(n_zones):
        cols = {
            "year": np.int16(year),
            "pass": pass_label,
            "zone": zone_names[z],
            "hour": np.arange(T, dtype=np.int32),
            "price": prices[z] + total_overlay,
            "slack": slack[z],
            "dump": dump[z, :T],
            "demand": demand[z, :T],
            "reserve_price": rp,
        }
        if mer is not None:
            cols["marginal_emission_rate"] = mer[z]
        if overlay is not None:
            cols["rtordpa_overlay"] = overlay
        if dam_as is not None:
            cols["dam_as_overlay"] = dam_as
        if ordc_adder is not None:
            cols["ordc_adder"] = ordc_adder
        rows.append(pd.DataFrame(cols))
    return pd.concat(rows, ignore_index=True)


def _hydro_cascade_frame(year: int, pass_label: str, result) -> "pd.DataFrame | None":
    """Return the long per-coupled-plant hourly hydraulic-cascade frame.

    One row per (coupled downstream plant, hour): the LP's spill ``S_d(t)``
    (kcfs), pond volume ``V_d(t)`` above the bottom of the operated band
    (kcfs·h), and the water-balance row dual (the marginal water value at that
    plant-hour, $ per kcfs·h). These are the three ``DispatchResult`` arrays
    ``model/lp/hydro_cascade.py`` extracts when ``ScenarioConfig.
    hydro_cascade_coupling`` is armed (NWPP-36, owner ruling N3); until this
    sidecar they were discarded at persist time, so the ONLY evidence of what
    the coupling did in a solved bundle was the coupled plants' generation
    shape — FINDING-nwpp-36 §7 item 5 routed their persistence here
    (NWPP-40). Tiny (n_coupled × 8,760 rows; five plants on the first NWPP
    keeper) and committable under the ``hourly/`` convention (rule 15).

    Returns ``None`` on every run where the mechanism is off or inert (the
    arrays are ``None``), so no unarmed bundle gains a file.
    """
    spill = getattr(result, "hydro_cascade_spill", None)
    if spill is None:
        return None
    storage = getattr(result, "hydro_cascade_storage", None)
    wv = getattr(result, "hydro_cascade_water_value", None)
    codes = getattr(result, "hydro_cascade_plant_codes", None)
    spill = np.asarray(spill, dtype=float)
    if spill.ndim != 2 or spill.shape[0] == 0:
        return None
    n_c, T = spill.shape
    if codes is None or len(codes) != n_c:
        codes = np.arange(n_c)
    frame = pd.DataFrame(
        {
            "year": np.full(n_c * T, int(year), dtype=np.int16),
            "pass": pass_label,
            "plant_code": np.repeat(np.asarray(codes, dtype=np.int64), T),
            "hour": np.tile(np.arange(T, dtype=np.int32), n_c),
            "spill_kcfs": spill.reshape(-1).astype(np.float32),
            "pond_kcfsh": (
                np.asarray(storage, dtype=float).reshape(-1).astype(np.float32)
                if storage is not None
                else np.full(n_c * T, np.nan, dtype=np.float32)
            ),
            "water_value": (
                np.asarray(wv, dtype=float).reshape(-1).astype(np.float32)
                if wv is not None
                else np.full(n_c * T, np.nan, dtype=np.float32)
            ),
        }
    )
    return frame


def _reserve_family_frame(
    year: int,
    pass_label: str,
    result,
    design,
    zone_names=None,
) -> "pd.DataFrame | None":
    """Return the long per-reserve-family hourly dual / requirement frame.

    One row per (reserve family, hour): the family's own balance-row dual, its
    hourly requirement MW, the reserve MW it actually held, its cleared ORDC
    shortfall MW, and the ZONES its requirement is scoped over — so the LP row
    itself, ``held + shortfall >= requirement``, is checkable from the bundle,
    with equality iff the family binds and the slack saying how far a
    non-binding family was from binding.

    **Why this exists (nyiso-113 §8, the standing all-ISO gap).** Until this
    sidecar, NO bundle in ANY ISO persisted a per-family reserve dual.
    ``DispatchResult.reserve_price_by_family`` is ``(T, n_fam)`` in memory (it
    is what ``results/scarcity.py`` consumes) and was discarded at persist
    time, while ``system_<year>.parquet``'s ``reserve_price`` is the per-hour
    SUM across families, a single ``(T,)`` system-level series broadcast
    IDENTICALLY into every zone's rows (:func:`_system_frame`). It therefore
    has no zone index and no family index: a locational family's binding is
    invisible in it *by construction*, and a gate written against it reads
    inert whatever the LP did. nyiso-113's own pre-registered K3/K4 gates were
    invalid for exactly this reason. Any question of the form "does family X
    ever bind, and when" needs this frame or a re-solve.

    The two measured columns answer different questions and are both needed:
    ``dual`` is the family's shadow price (its marginal contribution to the
    energy LMPs of its member zones through the shared-headroom rows), while
    ``shortfall_mw`` says whether the price came from the requirement binding
    against real headroom (shortfall 0) or from an ORDC step clearing
    (shortfall > 0).

    ``requirement_mw`` is read from the ``ReserveDesign``, not the LP — the LP
    reports duals positionally and only the design knows which column is
    ``li_30min_total`` and what its hourly (on/off-peak-stepped) requirement
    was. Returns ``None`` when the co-opt is off, when the design is
    unavailable (an older pickled ``p2_state`` predates the key), or when the
    solved dual's family count disagrees with the design's — a shape mismatch
    would mislabel every row, so no frame is preferable to a wrong one.
    """
    rpf = getattr(result, "reserve_price_by_family", None)
    families = getattr(design, "families", None)
    if rpf is None or not families:
        return None
    duals = np.asarray(rpf, dtype=float)
    if duals.ndim != 2 or duals.shape[1] != len(families):
        logger.warning(
            "reserve-family sidecar skipped (%d, %s): dual shape %s vs %d "
            "design families — refusing to mislabel families",
            year,
            pass_label,
            duals.shape,
            len(families),
        )
        return None
    T = duals.shape[0]

    def _col(name):
        v = getattr(result, name, None)
        return (
            np.zeros_like(duals)
            if v is None
            else np.asarray(v, dtype=float)[:T, : duals.shape[1]]
        )

    sf = _col("reserve_shortfall_by_family")
    held = _col("reserve_held_by_family")
    # The family's own REGION, its zone mask resolved to names. A locational
    # family is only legible with it: `li_30min_total` and `nyca_30min_total`
    # are the same row shape and the same columns, and nothing else in the
    # frame distinguishes a Zone-K requirement from an NYCA-wide one — the
    # name is a convention, the mask is the LP's actual scoping. Empty string
    # when the caller passes no zone list or the mask does not match it, so a
    # shape disagreement degrades this column rather than mislabelling a family.
    zones = list(zone_names or [])
    labels = []
    for fam in families:
        mask = np.asarray(getattr(fam, "zone_mask", np.zeros(0)), dtype=bool)
        labels.append(
            "|".join(z for z, m in zip(zones, mask) if m)
            if zones and mask.size == len(zones)
            else ""
        )
    rows = []
    for f, fam in enumerate(families):
        req = np.asarray(fam.requirement, dtype=float).ravel()[:T]
        rows.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "pass": pass_label,
                    "family": str(fam.name),
                    "reserve_class": np.int8(int(fam.reserve_class)),
                    "zones": labels[f],
                    "hour": np.arange(T, dtype=np.int32),
                    "dual": duals[:, f].astype(np.float32),
                    "requirement_mw": req.astype(np.float32),
                    "held_mw": held[:, f].astype(np.float32),
                    "shortfall_mw": sf[:, f].astype(np.float32),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    for col in ("pass", "family", "zones"):
        df[col] = df[col].astype("category")
    return df


def _storage_frame(
    year: int,
    pass_label: str,
    result,
    storage_units,
) -> pd.DataFrame | None:
    """Return the long per-storage-unit hourly charge/discharge/SOC frame.

    One row per (storage unit, hour) carrying the unit's charge and
    discharge MW plus its tech (li_ion / pumped_storage) and zone, so the
    bundle exposes storage throughput the way ``dispatch/`` exposes
    generator output. Returns ``None`` when the fleet is empty.

    **``soc_mwh`` / ``energy_cap_mwh`` added 2026-09-16 (session caiso-284),
    additive and solve-invariant.** ``DispatchResult.storage_soc`` has always
    been solved — the LP's SOC recursion is one of its core constraints — but
    was the one storage decision variable no artifact persisted, so a committed
    bundle exposed throughput with no reservoir state. The consequence is
    concrete: the CAISO RA-bridge decommit screen
    (``model/commitment._write_economic_bridges``) excludes storage-charge
    headroom from its absorption term on an explicit ENERGY-capacity premise
    (*"the fleet already fills by the belly in P1"*), and caiso-284 phase 0
    could neither confirm nor refute that premise from committed artifacts —
    the tech-aggregated sidecar carries no SOC, and integrating charge/discharge
    to recover it FAILS, because each unit has its own cyclic SOC constraint and
    the aggregation destroys it (the attempt returned a reconstructed span of
    420-4,121 % of implied capacity). Persisting the solved variable removes the
    reconstruction entirely. ``energy_cap_mwh`` rides along because headroom is
    ``cap - soc`` and the cap is per-unit, so a tech-level sum of SOC alone is
    not interpretable. Both are WRITE-ONLY: read after the LP has solved, they
    cannot perturb a solve, and they add no ``ScenarioConfig`` field (rule 24
    ``[R-REGISTRY]`` scopes to tunables that can change a solve).
    ``docs/FINDING-caiso284-belly-commitment-phase0-2026-09-16.md`` §3.
    """
    if not storage_units or result.storage_discharge is None:
        return None
    chg = np.asarray(result.storage_charge, dtype=np.float32)
    dis = np.asarray(result.storage_discharge, dtype=np.float32)
    n_storage, T = dis.shape
    # ``storage_soc`` is Optional on DispatchResult and is None on any path that
    # solved without the SOC block; emit NaN there rather than dropping the
    # column, so the schema is the same shape on every bundle and a reader can
    # tell "not solved" (NaN) from "empty reservoir" (0.0).
    soc = (
        np.asarray(result.storage_soc, dtype=np.float32)
        if getattr(result, "storage_soc", None) is not None
        else np.full((n_storage, T), np.nan, dtype=np.float32)
    )
    hours = np.tile(np.arange(T, dtype=np.int32), n_storage)
    rep = lambda vals: np.repeat(np.asarray(vals, dtype=object), T)  # noqa: E731
    df = pd.DataFrame(
        {
            "unit_id": rep([u.unit_id for u in storage_units]),
            "tech": rep([u.tech_name for u in storage_units]),
            "zone": rep([u.zone for u in storage_units]),
            "hour": hours,
            "charge_mw": chg.reshape(-1),
            "discharge_mw": dis.reshape(-1),
            "soc_mwh": soc.reshape(-1),
            "energy_cap_mwh": np.repeat(
                np.asarray(
                    [float(u.energy_cap_mwh) for u in storage_units], dtype=np.float32
                ),
                T,
            ),
        }
    )
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "unit_id", "tech", "zone"):
        df[col] = df[col].astype("category")
    return df


def _posture_frame(
    year: int,
    pass_label: str,
    result,
    zone_names,
) -> pd.DataFrame | None:
    """Return the commitment-posture hourly frame, one row per (pool, hour).

    The honesty-gate artifact for the commitment-posture lever (design note
    §A) — ``miso_commitment_posture`` or its PJM port ``pjm_commitment_posture``
    (same mechanism, same columns): each postured (zone × fuel-class) pool's
    online capacity ``U`` (MW), startup increments ``SU`` (MW started this
    hour) and cleared reserve ``R`` — the modeled online-headroom /
    cleared-reserve series the gate compares against the measured ISO ASM /
    reserve-market data (``data/raw/MISO-AS``; ``data/raw/PJM-AS``), level +
    event-day direction, never the price-tail residual (rules 1/13). ``None``
    when the posture lever is off.
    """
    u = getattr(result, "posture_online_mw", None)
    if u is None:
        return None
    from market_sim.data.fleet import FUEL_TYPE_NAMES

    zone_idx = result.posture_zone_idx
    fuel_idx = result.posture_fuel_idx
    q, T = np.asarray(u).shape
    zone_lab = np.array([zone_names[z] for z in zone_idx], dtype=object)
    fuel_lab = np.array([FUEL_TYPE_NAMES[f] for f in fuel_idx], dtype=object)
    su = np.asarray(result.posture_startup_mw, dtype=np.float32)
    # Cleared reserve is present only for the pergen posture (MISO/CAISO/PJM);
    # the standalone ERCOT energy-only posture (ercot_commitment_posture) has no
    # reserve coupling, so posture_reserve_mw is None -> report 0.
    r_raw = getattr(result, "posture_reserve_mw", None)
    r = (
        np.zeros(q * T, dtype=np.float32)
        if r_raw is None
        else np.asarray(r_raw, dtype=np.float32).reshape(-1)
    )
    df = pd.DataFrame(
        {
            "zone": np.repeat(zone_lab, T),
            "fuel": np.repeat(fuel_lab, T),
            "hour": np.tile(np.arange(T, dtype=np.int32), q),
            "online_mw": np.asarray(u, dtype=np.float32).reshape(-1),
            "startup_mw": su.reshape(-1),
            "reserve_mw": r,
        }
    )
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "zone", "fuel"):
        df[col] = df[col].astype("category")
    return df


def _storage_as_frame(
    year: int,
    pass_label: str,
    result,
    storage_units,
    zone_names,
) -> pd.DataFrame | None:
    """Return the modeled-vs-measured storage AS-vs-energy split, one row/hour.

    The G5 validation artifact (``ercot_storage_as_endogenous``): for each hour
    it carries the LP's CHOSEN battery split — ``modeled_as_mw`` (cleared upward
    reserve attributed to storage by :func:`market_sim.model.dispatch.storage_reserve_mw`,
    the storage-first opportunity-cost attribution) and ``modeled_discharge_mw``
    (energy) — alongside the **measured** 60-Day DAM battery AS award
    (``measured_as_mw``, the ``storage`` column of the per-resource-type series).
    The measured award is the backcast realization the chosen split is VALIDATED
    against, never pinned to (CLAUDE.md #12). Returns ``None`` when the co-opt is
    off (no ``reserve_dispatch``) or the storage fleet is empty.
    """
    rd = getattr(result, "reserve_dispatch", None)
    if rd is None or not storage_units or result.storage_discharge is None:
        return None
    from market_sim.model.dispatch import storage_reserve_mw
    from market_sim.results.scarcity import ercot_storage_as_reserve_mw

    n_zones = len(zone_names)
    rd = np.asarray(rd, dtype=float)
    n_classes = max(1, rd.shape[0] // n_zones)
    T = rd.shape[1]
    zone_lookup = {z: i for i, z in enumerate(zone_names)}
    s_zone = np.array([zone_lookup.get(u.zone, 0) for u in storage_units], dtype=int)
    power_cap = np.array([float(u.power_cap_mw) for u in storage_units], dtype=float)
    # With the duration gate on, storage AS is an EXACT decision variable
    # (result.storage_reserve_dispatch, the RS[c,z] columns); use it directly.
    # Otherwise storage is pooled in the shared headroom and we fall back to the
    # storage-first min() attribution upper bound (storage_reserve_mw).
    srd = getattr(result, "storage_reserve_dispatch", None)
    if srd is not None:
        as_zone = np.asarray(srd, dtype=float)  # (n_zones, T) exact
    else:
        as_zone = storage_reserve_mw(
            rd,
            np.asarray(result.storage_charge, dtype=float),
            np.asarray(result.storage_discharge, dtype=float),
            power_cap,
            s_zone,
            n_classes,
        )  # (n_zones, T)
    modeled_as = as_zone.sum(axis=0)  # system total MW
    modeled_dis = np.asarray(result.storage_discharge, dtype=float).sum(axis=0)
    measured_as = ercot_storage_as_reserve_mw(int(year), T)
    df = pd.DataFrame(
        {
            "year": np.int16(year),
            "pass": pass_label,
            "hour": np.arange(T, dtype=np.int32),
            "modeled_as_mw": modeled_as.astype(np.float32),
            "modeled_discharge_mw": modeled_dis.astype(np.float32),
            "measured_as_mw": measured_as.astype(np.float32),
        }
    )
    df["pass"] = df["pass"].astype("category")
    return df


def _eia930_frame(year: int, iso: str, iso_config) -> pd.DataFrame | None:
    """Return the EIA-930 hourly benchmark series for a year, long format.

    ERCOT keeps its dedicated full-year fossil/nuclear/renewable loaders (so
    its bundle is unchanged). Every other ISO is served by the generic per-BA
    benchmark loader, which also carries the BA's net generation and net
    interchange and tolerates a BA-year a few hours short of 8760.

    The ERCOT battery series (``battery_discharge`` / ``battery_charge``)
    keep NaN over hours the BA had not yet begun reporting them (the series
    start mid-2024), so a partial year still benchmarks its reported window.
    """
    if iso != "ERCOT":
        return _eia930_frame_generic(year, iso)

    fossil = load_ercot_fossil_gen(year)
    renew = load_ercot_renewable_gen(year)
    if fossil is None or renew is None:
        return None
    nuclear = load_ercot_nuclear_gen(year)
    battery = load_ercot_battery_gen(year)
    # "Other Fuel Sources" (NG: OTH) — carried so the gas fold-in deflation
    # can subtract only the genuinely-folded other/biomass portion from the
    # EIA-930 gas cell (post-Nov-2024 storage breakout, ERCO's Other series
    # is ~biomass alone and the OTHER-class generation sits inside NG: NG);
    # see load_ercot_other_gen and calibration_verdict.score_sysvol.
    other = load_ercot_other_gen(year)
    # net generation = Demand + Interchange = load_demand with no gross-up.
    net_gen = load_demand(iso, year, iso_config, td_loss_factor=0.0).sum(axis=0)
    series = {
        "gas": fossil["gas"],
        "coal": fossil["coal"],
        "wind": renew["wind"],
        "solar": renew["solar"],
        "net_gen": net_gen,
    }
    if nuclear is not None:
        series["nuclear"] = nuclear
    if other is not None:
        series["other"] = other
    if battery is not None:
        series.update(battery)
    out = []
    for name, arr in series.items():
        a = np.asarray(arr, dtype=float)
        out.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "series": name,
                    "hour": np.arange(a.shape[0], dtype=np.int32),
                    "mw": a,
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def _eia930_frame_generic(year: int, iso: str) -> pd.DataFrame | None:
    """Return the EIA-930 hourly benchmark for a non-ERCOT ISO, long format.

    Carries each delivered per-fuel series plus the BA's net generation and
    net interchange, read straight from the per-BA ``<BA> hourly`` extract.

    A POOL region (several EIA-930 balancing authorities under one registry
    key — NWPP is seventeen) names no single ``<BA> hourly`` file, so
    :func:`load_eia_hourly_benchmark` is ``None`` for it by construction
    (FINDING-nwpp-39 §4). Such a region is served by
    ``build_calibration_reference._pool_hourly_benchmark`` — the loader's own
    per-BA construction applied to each member and summed, with ``net_gen`` /
    ``interchange`` read off the registered pool frame — the SAME dict the
    scorer's ``calibration_reference.json`` block is built from, so the bench
    part and the reference cannot disagree. The dispatch is data-driven on
    ``_is_pool_region`` (never an ``iso ==`` ladder); every 1:1 region still
    takes the loader and is byte-identical. Added by lane NWPP-40
    (2026-09-16): without it the first NWPP bundle carried no ``eia930``
    input and ``render_calibration_html.build_payload`` could not register it.
    """
    from scripts.data.build_calibration_reference import (
        _is_pool_region,
        _pool_hourly_benchmark,
    )

    bench = (
        _pool_hourly_benchmark(iso, year)
        if _is_pool_region(iso)
        else load_eia_hourly_benchmark(iso, year)
    )
    if not bench:
        return None
    out = []
    for name, arr in bench.items():
        a = np.asarray(arr, dtype=float)
        out.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "series": name,
                    "hour": np.arange(a.shape[0], dtype=np.int32),
                    "mw": a,
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def _parasitic_factor_map() -> dict[int, float]:
    """Return ``{plant_id: net/gross factor}`` from the derived artifact.

    Empty when the artifact is missing — the per-plant hourly fit then
    falls back to scaling CAMPD gross by 1.0 (treating gross as net), which
    only shifts the level, not the timing the correlation cares about.
    """
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def _fleet_group_by_code(
    iso: str, iso_config, year: int | None = None
) -> dict[int, str]:
    """Return ``{plant_code: plant_group}`` from the EIA-860 per-plant fleet.

    The non-ERCOT analogue of the ERCOT CAMPD bin sheet's plant->group map,
    used to bucket the CAMPD/EIA-923 benchmark backfill. Built from the fleet's
    ``plant_group`` (COAL / CC_REGULAR / CT_PEAKER / ST_GAS / their CHP
    variants), so it matches the dispatch frame's classes. ``year`` selects that
    vintage's EIA-860 CHP designation, so the benchmark backfill buckets a plant
    CHP-vs-merchant the same way the year's dispatch fleet does.
    """
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, str] = {}
    for g in load_fleet_from_csv(iso, iso_config, year=year):
        code = int(g.plant_code)
        if code > 0 and g.plant_group:
            out[code] = g.plant_group
    return out


def _campd_hourly_frame(
    year: int,
    iso: str,
    factors: dict[int, float],
    hours: int,
) -> pd.DataFrame | None:
    """Return the per-plant 8760-hour CAMPD **net** generation frame.

    One row per ``(plant_id, hour)`` carrying net MW (CAMPD gross scaled by
    the plant's parasitic factor). ``None`` when no CAMPD extract covers the
    ISO's states for the year.
    """
    states = campd.states_for_iso(iso)
    if not states:
        return None
    df = campd.load_campd_hourly(states, [year])
    if df.empty:
        return None
    # PJM: reconstruct hourly net MW for grossLoad-blank coal units (CFB /
    # waste-coal / coal cogen — Virginia City, Seward, the PA culm fleet, ...)
    # from their measured heatInput and an EIA-923-anchored effective heat rate.
    # These units report heatInput + steamLoad but no grossLoad, so they would
    # otherwise look offline all year. The proxy is anchored to EIA-923 net
    # generation, so the filled series is already net — those plants take a
    # parasitic factor of 1.0 (gross == net), overriding the class default the
    # zero-gross plant would otherwise pick up.
    if iso == "PJM":
        df, proxy_ids = campd.fill_heatinput_proxy(df, load_monthly_generation(), year)
        if proxy_ids:
            factors = {**factors, **{pid: 1.0 for pid in proxy_ids}}
    net = campd.plant_hourly_net(df, factors, year, hours=hours)
    if not net:
        return None
    frames = [
        pd.DataFrame(
            {
                "year": np.int16(year),
                "plant_id": np.int32(plant_id),
                "hour": np.arange(series.shape[0], dtype=np.int32),
                "net_mw": series.astype(np.float32),
            }
        )
        for plant_id, series in net.items()
    ]
    return pd.concat(frames, ignore_index=True)


@lru_cache(maxsize=32)
def _eia860_vintage_ba_plants(iso: str, year: int) -> frozenset[int]:
    """Plants BA-coded to ``iso`` in the EIA-860 vintage that COVERS ``year``.

    The benchmark's supplement (``zone_assignment._eia860_ba_zones``) reads
    ``_EIA860_PLANT_PATH``, a module-level constant bound at import to the
    CANONICAL ``EIA_860_DIR``. It therefore never follows the solved year,
    and a plant that retired mid-window is absent from the ISO's benchmark
    membership in the very years it demonstrably ran (spp-49).

    This reads ``vintage_<year>/eia860_plant.parquet`` instead, holding last
    to the canonical file for years past the final committed vintage. The
    admission predicate is the SAME one ``zone_assignment`` applies — the
    ISO's own BA codes, and for NWPP the BA-plus-WECC footprint rule — so
    this widens WHICH VINTAGE is read and nothing else.

    Keyed on ``(iso, year)`` and read-only over committed parquet, so it is a
    pure function of the reference data (no ``ScenarioConfig``, no
    ``active_eia860_dir()`` process global).
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.zone_assignment import _iso_ba_codes, _nwpp_admitted

    vintage = EIA_860_DIR / f"vintage_{int(year)}"
    path = vintage / "eia860_plant.parquet"
    if not path.exists():
        # Hold last: years past the final committed vintage read the
        # canonical file, which IS that year's best published snapshot.
        path = EIA_860_DIR / "eia860_plant.parquet"
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(path)
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    if iso == "NWPP":
        nerc = df["NERC Region"] if "NERC Region" in df.columns else None
        mask = _nwpp_admitted(ba, nerc)
    else:
        codes = _iso_ba_codes(iso)
        if not codes:
            return frozenset()
        mask = ba.isin(codes)
    plants = pd.to_numeric(df["Plant Code"], errors="coerce")[mask].dropna()
    return frozenset(int(p) for p in plants)


@lru_cache(maxsize=128)
def _iso_plant_ids(
    iso: str, year: int | None = None, vintage_union: bool = False
) -> frozenset[int]:
    """ORIS codes physically located in ``iso`` (eGRID/EIA-860 BA geography).

    EIA-923's ``generation`` table is national; without restricting to the
    ISO the per-class benchmark totals leak in every other US plant (e.g. PRB
    coal shows the ~639 TWh national figure instead of ERCOT's ~47 TWh).

    ``vintage_union`` (``ScenarioConfig.benchmark_membership_vintage_union``,
    default off, byte-identical off — the base branch is returned unchanged
    and the added arguments only widen the cache key) UNIONS in the solve
    year's own EIA-860 BA cohort via :func:`_eia860_vintage_ba_plants`. See
    that field's comment for the defect, the measurement and why the union is
    additive rather than a replacement (rules 13 / 14).
    """
    base = frozenset(build_zone_lookup(iso))
    if not vintage_union or year is None:
        return base
    return base | _eia860_vintage_ba_plants(iso, int(year))


def _eia923_frame(
    year: int,
    generation: pd.DataFrame,
    iso: str = "ERCOT",
    mustrun_chp_btm_holdout: bool = False,
    benchmark_membership_vintage_union: bool = False,
) -> pd.DataFrame:
    """Return EIA-923 net generation per (plant, class), annual and monthly.

    Restricted to plants in ``iso`` so the per-class totals are the ISO's
    actual generation, not the national EIA-923 sum.

    ``mustrun_chp_btm_holdout`` (``ScenarioConfig.mustrun_chp_btm_holdout``,
    default off, byte-identical off) drops rows whose plant carries the
    published EIA-923 CHP flag from the INJECTED residual classes
    (:data:`_INJECTED_MUSTRUN_CLASSES`) only — the host-steam / behind-the-meter
    partition biomass and OTHER never received, though every fossil cogen class
    has had one since ``classify_plant`` split them into ``*_CHP``. This is the
    SINGLE seam both the injection (:func:`_must_run_profiles`) and the
    benchmark (:func:`_benchmark_eia923_frame`) read, so the two move in
    lockstep and the partition cannot manufacture a benchmark miss. Every other
    class is untouched: gas cogen is already partitioned, coal cogen has
    ``coal_chp_overrides``, and :func:`_plant_class_shares` filters to
    :data:`_BACKFILL_TARGET_KLASSES` before it ever sees these rows.
    Zero free parameters — a partition on one published boolean (rules 21 / 24).

    ``benchmark_membership_vintage_union`` (default off, byte-identical off)
    widens the ISO membership to the solve year's own EIA-860 BA cohort — see
    :func:`_iso_plant_ids` and the ``ScenarioConfig`` field's comment.
    """
    df = generation[generation["year"] == year].copy()
    iso_plants = _iso_plant_ids(iso, year, bool(benchmark_membership_vintage_union))
    if iso_plants:
        df = df[df["plant_id"].isin(iso_plants)].copy()
    df["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
        )
    ]
    if mustrun_chp_btm_holdout:
        # Row grain, not plant grain: a mill may report a chp=Y recovery boiler
        # and a chp=N grid unit at the same plant code, and only the former is
        # behind the host's meter.
        _host = df["chp"].astype(str).str.upper().str.startswith("Y") & df[
            "klass"
        ].isin(_INJECTED_MUSTRUN_CLASSES)
        if bool(_host.any()):
            logger.info(
                "must-run CHP/BTM holdout %d %s: dropping %.3f TWh of chp=Y "
                "host-steam generation from the injected residual classes "
                "(%d of %d rows)",
                year,
                iso,
                float(df.loc[_host, "netgen_annual_mwh"].sum()) / _MWH_PER_TWH,
                int(_host.sum()),
                int(len(df)),
            )
        df = df[~_host].copy()
    cols = monthly_netgen_columns()
    agg = {"netgen_annual_mwh": "sum", **{c: "sum" for c in cols}}
    grouped = df.groupby(["plant_id", "klass"], as_index=False).agg(agg)
    grouped.insert(0, "year", np.int16(year))
    rename = {c: f"m{i + 1:02d}" for i, c in enumerate(cols)}
    rename["netgen_annual_mwh"] = "annual_mwh"
    return grouped.rename(columns=rename)


# Residual / non-fossil classes injected into the dispatch as must-run
# resources: they serve load exogenously (biomass/landfill, refinery process
# gas, purchased steam, ...) rather than clearing the LP merit order. Oil is
# NOT here — it is a price-responsive peaker dispatched in the LP. Hydro is
# NOT here either: conventional hydro is an LP unit with a monthly energy
# budget (run_calibration._hydro_fleet) and pumped storage is a storage
# resource (load_eia860_pumped_storage), so injecting it would double-count.
_INJECTED_MUSTRUN_CLASSES: tuple[str, ...] = ("biomass", "OTHER")


def _hour_months(year: int, hours: int) -> np.ndarray:
    """``(hours,)`` array of 1-based calendar month for each hour-of-year."""
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy()


@lru_cache(maxsize=1)
def _pumped_storage_plant_ids() -> frozenset[int]:
    """EIA plant ids with pumped-storage (prime mover ``PS``) generators.

    Used to hold PS plants out of the injected OTHER must-run profile —
    ``classify_plant`` buckets PS into OTHER, but PS is dispatched as an LP
    storage resource (``load_eia860_pumped_storage``), so leaving its EIA-923
    net generation in the injection would double-count it.

    **THIS GUARD WAS A DEAD NO-OP UNTIL 2026-09-12 and is live only from then**
    (gov-hydro-seam-1; the defect is
    ``docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md`` §5). The
    docstring above described the intended taxonomy, but ``classify_plant``
    carried a ``fuel == "WAT"`` short-circuit ahead of its prime-mover test and
    every ``WAT``/``PS`` row therefore reached ``hydro``, never ``OTHER`` — so
    the filter protected nothing while reading as though the PS question were
    handled. With the classifier repaired the statement is finally true of the
    code. Measured at the repair: the filter is PLANT-GRAIN, not row-grain, so
    it could in principle drop a non-PS ``OTHER`` unit co-located with a PS
    generator — there are **zero** such rows in the EIA-923 record 2019-2026,
    and the injected ``OTHER`` class energy moves by **0.000000 MWh** in all 42
    scored (ISO, year) cells, which is why the repair is not solve-affecting.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(path, columns=["plant_id", "prime_mover"])
    ps = df[df["prime_mover"].astype(str).str.upper() == "PS"]
    return frozenset(int(p) for p in ps["plant_id"].unique())


def _must_run_profiles(
    year: int,
    generation: pd.DataFrame,
    iso: str,
    demand: np.ndarray,
    skip_classes: frozenset[str] = frozenset(),
    e930: pd.DataFrame | None = None,
    mustrun_chp_btm_holdout: bool = False,
    benchmark_membership_vintage_union: bool = False,
) -> dict[str, np.ndarray]:
    """Per-zone hourly must-run MW for each injected residual class.

    Each class's EIA-923 annual generation is shaped by its monthly profile
    (flat within a month, negatives clamped then rescaled to preserve the net
    annual energy) and split across zones by their share of annual demand.
    Biomass uses the vintage-carry-reconciled energy
    (:func:`_reconciled_biomass_class`, needing ``e930`` for the completeness
    probe), so the injected biomass equals the benchmark it is scored against
    even in a partial current-year vintage. ``skip_classes`` drops classes the
    caller does not want injected. Pumped-storage plants are held out of OTHER —
    they dispatch as LP storage. Returns ``{klass: (n_zones, hours) MW}`` for the
    classes with positive net generation in ``iso`` and ``year``.
    """
    n_zones, hours = demand.shape
    months = _hour_months(year, hours)
    hours_per_month = np.array([(months == m).sum() for m in range(1, 13)], dtype=float)
    zone_tot = demand.sum(axis=1)
    grand = zone_tot.sum()
    zone_share = (zone_tot / grand) if grand > 0 else np.full(n_zones, 1.0 / n_zones)
    out: dict[str, np.ndarray] = {}
    for klass in _INJECTED_MUSTRUN_CLASSES:
        if klass in skip_classes:
            continue
        # Vintage-carry-reconciled energy (PS held out of OTHER inside the helper)
        # so the injected class energy == the benchmark it is scored against, even
        # in a partial current-year EIA-923 vintage where biomass AND OTHER are
        # truncated (both absent from CAMPD/EIA-930).
        annual, monthly = _reconciled_mustrun_class(
            klass,
            year,
            generation,
            iso,
            e930,
            mustrun_chp_btm_holdout,
            benchmark_membership_vintage_union,
        )
        monthly = np.clip(monthly, 0.0, None)
        if annual <= 0:
            continue
        if monthly.sum() <= 0:
            monthly = hours_per_month.copy()  # no monthly detail -> flat
        with np.errstate(divide="ignore", invalid="ignore"):
            mw_by_month = np.where(hours_per_month > 0, monthly / hours_per_month, 0.0)
        prof = mw_by_month[months - 1]
        psum = float(prof.sum())
        if psum <= 0:
            continue
        prof = prof * (annual / psum)  # preserve net annual energy
        out[klass] = zone_share[:, None] * prof[None, :]
    return out


# EIA-923 lags for recent years (2025): plants that ran can report ~0 net gen.
# Below this annual threshold, if CAMPD net is above it, the plant is treated
# as under-reported and the benchmark is backfilled with CAMPD net.
_CAMPD_BACKFILL_MIN_MWH: float = 50_000.0  # 50 GWh
# Non-CHP grid groups eligible for CAMPD backfill (CHP kept on EIA-923 — the
# host-steam split is absent from CAMPD net).
_BACKFILL_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "ST_GAS", "CT_PEAKER"}
)
# The fine EIA-923 klasses those groups resolve to — the classes a mixed plant's
# CAMPD net may be split across: the non-CHP gas grid classes (CC_REGULAR /
# CT_PEAKER / ST_GAS) and every coal supply subclass. Derived from the canonical
# taxonomy (no hardcoded lists); CHP is excluded, matching _BACKFILL_GROUPS.
_BACKFILL_TARGET_KLASSES: frozenset[str] = frozenset({*_NONCHP_GAS, *_COAL_CLASSES})


def _plant_klass_annual(e923: pd.DataFrame, plant_id: int, klass: str) -> float:
    """Return the EIA-923 benchmark annual MWh for one ``(plant_id, klass)``."""
    mask = (e923["plant_id"] == plant_id) & (e923["klass"] == klass)
    return float(e923.loc[mask, "annual_mwh"].sum())


def _backfill_eia923_with_campd(
    e923: pd.DataFrame,
    campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str],
    year: int,
    class_shares: dict[int, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Backfill EIA-923 with CAMPD net for model plants it under-reports.

    For each non-CHP grid plant (coal / CC_REGULAR / ST_GAS / CT_PEAKER) whose
    EIA-923 annual for its *mapped* grid class is below
    :data:`_CAMPD_BACKFILL_MIN_MWH` while CAMPD net is above it, set the benchmark
    annual + monthly from CAMPD net (gross x parasitic factor). Plants EIA-923
    already reports (e.g. V H Braunig, R W Miller) are untouched.

    ``class_shares`` (the non-ERCOT plant-level path only; from
    :func:`_plant_class_shares`) buckets the CAMPD net by **unit prime-mover
    class**: a genuinely mixed plant's net is split across the classes physically
    at it (WA-Parish coal+gas, Doswell/Linden CC+CT) in proportion to its measured
    EIA-923 prime-mover class shares, instead of booking the whole plant net to
    the single ``group_by_code`` last-generator-wins class — which mislabels, and
    (when the mapped class is the plant's *minority* fuel) double-counts, large
    energy blocks. When ``class_shares`` is ``None`` (ERCOT, whose curated bin
    sheet drives ``group_by_code``) or has no entry for a plant, that plant keeps
    the exact single-class behavior, so those paths stay byte-identical. The
    *firing test* is unchanged (still the plant's mapped class), so the set of
    plants the backfill touches — and therefore every plant it leaves alone — is
    identical to the pre-split code; only the distribution across a firing plant's
    own classes changes.

    Min-MWH gating once a plant is split: a class EIA-923 already reports
    >= :data:`_CAMPD_BACKFILL_MIN_MWH` is measured and kept as-is (rule 11, never
    overwritten); only the *residual* CAMPD net not already booked to those
    classes is distributed across the under-reported classes by their shares. When
    the whole plant is truncated (every eligible class below the threshold — the
    incomplete-vintage case this fix targets) the residual is the full net, so the
    per-class split sums to the plant's CAMPD net (mass preserved). A single
    eligible class reduces to the old whole-net-to-mapped-class behavior.
    """
    if campd_year is None or campd_year.empty:
        return e923
    e923 = e923.copy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    month1 = _hour_to_month(int(campd_year["hour"].max()) + 1)  # 1-based
    add: list[dict] = []
    fired: set[int] = set()
    n_repl = 0

    def _book(plant_id: int, klass: str, annual: float, net: np.ndarray) -> None:
        """Set the ``(plant_id, klass)`` benchmark row to ``annual`` MWh, shaped by
        the plant's CAMPD net monthly profile scaled to ``annual`` (identity scale
        of 1.0 for a single/whole-net class, so that path is byte-identical)."""
        nonlocal n_repl
        net_total = float(net.sum())
        scale = (annual / net_total) if net_total > 0.0 else 0.0
        monthly = {
            mcols[m]: float(net[month1[: len(net)] == m + 1].sum()) * scale
            for m in range(12)
        }
        cur = e923[(e923["plant_id"] == plant_id) & (e923["klass"] == klass)]
        if len(cur):
            i = cur.index[0]
            e923.at[i, "annual_mwh"] = annual
            for k, v in monthly.items():
                e923.at[i, k] = v
            n_repl += 1
        else:
            add.append(
                {
                    "year": np.int16(year),
                    "plant_id": plant_id,
                    "klass": klass,
                    "annual_mwh": annual,
                    **monthly,
                }
            )
        fired.add(plant_id)

    for pid_raw, sub in campd_year.groupby("plant_id"):
        pid = int(pid_raw)
        group = group_by_code.get(pid)
        if group not in _BACKFILL_GROUPS:
            continue
        net = sub.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        net_total = float(net.sum())
        if net_total < _CAMPD_BACKFILL_MIN_MWH:
            continue
        mapped = _coal_supply_class(pid) if group == "COAL" else group
        # Firing test unchanged from the single-class code: only when the plant's
        # mapped grid class is under-reported. Keeps the touched-plant set (hence
        # every left-alone plant) byte-identical; the split changes only HOW a
        # firing plant's net is distributed.
        if _plant_klass_annual(e923, pid, mapped) >= _CAMPD_BACKFILL_MIN_MWH:
            continue  # EIA-923 reports it adequately
        # Measured prime-mover class shares (non-ERCOT) or the single mapped class
        # (ERCOT / no share info -> byte-identical to the pre-split code).
        shares = (class_shares or {}).get(pid) or {mapped: 1.0}
        reported_mass = 0.0
        under: dict[str, float] = {}
        for klass, share in shares.items():
            cur_ann = _plant_klass_annual(e923, pid, klass)
            if cur_ann >= _CAMPD_BACKFILL_MIN_MWH:
                reported_mass += cur_ann  # adequately reported -> keep measured
            else:
                under[klass] = share
        residual = max(0.0, net_total - reported_mass)
        if not under or residual <= 0.0:
            continue
        wsum = sum(under.values())
        for klass, share in under.items():
            frac = (share / wsum) if wsum > 0.0 else (1.0 / len(under))
            _book(pid, klass, residual * frac, net)
    if fired:
        logger.info(
            "EIA-923 %d: CAMPD-backfilled %d under-reported plant(s) across "
            "%d class-row(s) (%d replaced, %d added)",
            year,
            len(fired),
            n_repl + len(add),
            n_repl,
            len(add),
        )
    if add:
        e923 = pd.concat([e923, pd.DataFrame(add)], ignore_index=True)
    return e923


def _eia923_missing_month_mask(
    generation: pd.DataFrame, year: int
) -> dict[int, np.ndarray]:
    """``{plant_id: (12,) bool}`` — month *m* is NaN in EVERY EIA-923 row of that plant.

    A single reported row makes the month present, so this is the conservative
    reading of "EIA-923 has no data for this plant in this month". The mask cannot
    be recovered downstream: :func:`_eia923_frame` aggregates the monthly columns
    with ``sum``, which renders an all-NaN group as ``0.0`` and makes a withheld
    month indistinguishable from a genuine idle one.
    """
    df = generation[generation["year"] == year]
    if df.empty:
        return {}
    cols = monthly_netgen_columns()
    isna = df[cols].astype(float).isna()
    isna.insert(0, "plant_id", df["plant_id"].to_numpy())
    grouped = isna.groupby("plant_id")[cols].all()
    return {int(p): row.to_numpy(dtype=bool) for p, row in grouped.iterrows()}


def _backfill_eia923_missing_months(
    e923: pd.DataFrame,
    campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str],
    year: int,
    generation: pd.DataFrame,
    class_shares: dict[int, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Fill EIA-923 months a plant did not report at all, from CAMPD net.

    **The annual-floor guard of :func:`_backfill_eia923_with_campd` cannot see this
    defect, by construction**: it fires only when a plant's mapped-class EIA-923
    *annual* is below :data:`_CAMPD_BACKFILL_MIN_MWH`, and a plant that reported ten
    of twelve months clears that floor comfortably. **Ten good months hide two
    missing ones.** EIA's own published annual (``netgen_annual_mwh``, the form's
    *"Net Generation (Megawatthours)"* column) is the sum of the months the
    respondent filed, so a withheld month is absent from the ANNUAL class benchmark
    too — not merely from its shape. Measured instance: Bethlehem Energy Center
    (plant 2539, a 750 MW NYISO combined cycle) filed no February and no November
    2022; CAMPD meters 596.0 GWh there, and `CC_REGULAR`'s 2022 benchmark is short
    by that block (``docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md``
    §2). Census over every committed bench part: 67 plant-years across nine BAs.

    Rule 14 ``[R-ACCURATE]``: the accurate measurement replaces a silently truncated
    one; the estimate it displaces is not an estimate at all but a hole. Rule 21 /
    24: **zero free parameters** — the CAMPD month is scaled by the plant's OWN
    ``sum(EIA-923 reported months) / sum(CAMPD same months)``, measured from the same
    plant in the same year, which is the identical "scale CAMPD's shape to a measured
    target" arithmetic :func:`_backfill_eia923_with_campd._book` already performs.
    That ratio matters because CEMS meters only a combined cycle's *stacked* units:
    Bethlehem's unstacked steam turbine is 34 % of its net, so raw CAMPD is short by a
    measured 32 % and the ratio (1.476) is what makes the two meters commensurable.

    Eligibility is exactly the annual backfill's (:data:`_BACKFILL_GROUPS`, non-CHP
    grid), and a plant the annual backfill already fired on is skipped — its rows are
    CAMPD-derived for all twelve months already, so filling again would double-count.
    Byte-identical fallback: no ``campd_year`` (ERCOT-style extracts without one, and
    every bundle predating the CAMPD frame) is a no-op, as is a plant CAMPD shows
    idle in the missing month.
    """
    if campd_year is None or campd_year.empty:
        return e923
    mask_by_plant = _eia923_missing_month_mask(generation, year)
    if not mask_by_plant:
        return e923
    e923 = e923.copy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    month1 = _hour_to_month(int(campd_year["hour"].max()) + 1)  # 1-based
    add: list[dict] = []
    filled: set[int] = set()
    total_mwh = 0.0

    for pid_raw, sub in campd_year.groupby("plant_id"):
        pid = int(pid_raw)
        group = group_by_code.get(pid)
        if group not in _BACKFILL_GROUPS:
            continue
        mask = mask_by_plant.get(pid)
        if mask is None or not mask.any():
            continue
        mapped = _coal_supply_class(pid) if group == "COAL" else group
        # The annual backfill already rebuilt this plant from CAMPD for all twelve
        # months; a second fill would double-count it.
        if _plant_klass_annual(e923, pid, mapped) < _CAMPD_BACKFILL_MIN_MWH:
            continue
        net = sub.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        months = month1[: len(net)]
        campd_mon = np.array(
            [float(net[months == m + 1].sum()) for m in range(12)], dtype=float
        )
        gap = float(campd_mon[mask].sum())
        if gap <= 0.0:
            continue  # CAMPD says the plant was genuinely idle — nothing to repair
        shares = (class_shares or {}).get(pid) or {mapped: 1.0}
        rows = e923[(e923["plant_id"] == pid) & (e923["klass"].isin(shares))]
        reported = ~mask
        e_rep = float(
            rows[[mcols[m] for m in range(12) if reported[m]]].to_numpy().sum()
        )
        c_rep = float(campd_mon[reported].sum())
        if c_rep <= 0.0 or e_rep <= 0.0:
            continue  # no commensurable window -> no defensible scale, leave it alone
        ratio = e_rep / c_rep
        wsum = sum(shares.values()) or 1.0
        for klass, share in shares.items():
            frac = share / wsum
            monthly = {
                mcols[m]: float(campd_mon[m]) * ratio * frac if mask[m] else 0.0
                for m in range(12)
            }
            annual = float(sum(monthly.values()))
            if annual <= 0.0:
                continue
            total_mwh += annual
            cur = e923[(e923["plant_id"] == pid) & (e923["klass"] == klass)]
            if len(cur):
                i = cur.index[0]
                e923.at[i, "annual_mwh"] = float(e923.at[i, "annual_mwh"]) + annual
                for k, v in monthly.items():
                    if v:
                        e923.at[i, k] = float(e923.at[i, k]) + v
            else:
                add.append(
                    {
                        "year": np.int16(year),
                        "plant_id": pid,
                        "klass": klass,
                        "annual_mwh": annual,
                        **monthly,
                    }
                )
            filled.add(pid)
    if filled:
        logger.info(
            "EIA-923 %d: filled %d plant(s) with EIA-923-withheld month(s) from "
            "CAMPD net (%.3f TWh added to the class benchmark)",
            year,
            len(filled),
            total_mwh / _MWH_PER_TWH,
        )
    if add:
        e923 = pd.concat([e923, pd.DataFrame(add)], ignore_index=True)
    return e923


def _reattribute_dual_fuel_oil(
    e923: pd.DataFrame,
    group_by_code: dict[int, str],
    class_shares: dict[int, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Book a dual-fuel plant's EIA-923 oil MWh to the class its units are MODELLED in.

    :func:`_classify_f923` routes **100 %** of DFO / RFO / JF / KER / WO / PC to the
    ``oil`` class, because EIA-923 books a plant's MWh under the fuel it *burned*. The
    LP does not: ``dual_fuel_switching`` prices a dual-fuel unit at ``min(gas, oil)``
    and the unit keeps dispatching inside its own class, so the model books every MWh
    of Astoria Energy, Astoria II and Zeltmann as ``CC_REGULAR``. Measured at the unit
    layer, the model's ENTIRE ``oil``-fuel fleet in NYISO 2022 is **11.1 GWh across
    four plants** against an ``oil`` class benchmark of **1,843.7 GWh** — so the
    comparison straddles a fuel boundary and reads an **attribution** difference as a
    **level** error in two classes at once.

    This is the same misalignment ``reconcile_vintage_classes`` was repaired for on
    2026-09-17 (nyiso-239: the EIA-930 ``NG: OIL`` cell), one layer lower — there at
    the reconcile *target*, here in the 923 class split itself. Rule 14
    ``[R-ACCURATE]``'s misalignment case: the benchmark class is defined on a **fuel**
    boundary and the model class on a **unit** boundary, and the remedy is the
    reconciled version rather than a guess.

    A plant absent from ``group_by_code`` — not in the model fleet — keeps its ``oil``
    row, which is the right place for it: that residual IS the ISO's genuinely
    oil-only generation. A plant carrying several modelled classes splits by
    ``class_shares`` (the same measured EIA-923 prime-mover split the CAMPD backfill
    uses), so Ravenswood's oil lands across its CC and ST blocks in their own
    proportion. Zero free parameters (rules 21 / 24); byte-identical for an ISO whose
    ``oil`` class is empty.
    """
    oil_rows = e923[e923["klass"] == "oil"]
    if oil_rows.empty:
        return e923
    e923 = e923.copy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    add: list[dict] = []
    moved_mwh = 0.0
    moved_plants: set[int] = set()

    for idx, row in oil_rows.iterrows():
        pid = int(row["plant_id"])
        group = group_by_code.get(pid)
        if not group:
            continue  # not in the model fleet -> genuinely `oil`, leave it
        shares = (class_shares or {}).get(pid) or {group: 1.0}
        shares = {k: v for k, v in shares.items() if v > 0.0}
        if not shares:
            continue
        annual = float(row["annual_mwh"])
        if annual <= 0.0:
            continue
        monthly = {c: float(row[c]) for c in mcols}
        wsum = sum(shares.values())
        for klass, share in shares.items():
            frac = share / wsum
            cur = e923[(e923["plant_id"] == pid) & (e923["klass"] == klass)]
            if len(cur):
                i = cur.index[0]
                e923.at[i, "annual_mwh"] = (
                    float(e923.at[i, "annual_mwh"]) + annual * frac
                )
                for c in mcols:
                    if monthly[c]:
                        e923.at[i, c] = float(e923.at[i, c]) + monthly[c] * frac
            else:
                add.append(
                    {
                        "year": row["year"],
                        "plant_id": pid,
                        "klass": klass,
                        "annual_mwh": annual * frac,
                        **{c: monthly[c] * frac for c in mcols},
                    }
                )
        e923.at[idx, "annual_mwh"] = 0.0
        for c in mcols:
            e923.at[idx, c] = 0.0
        moved_mwh += annual
        moved_plants.add(pid)
    if moved_plants:
        logger.info(
            "EIA-923 dual-fuel oil re-attribution: %.3f TWh across %d modelled "
            "plant(s) moved from the `oil` class into the classes their units "
            "dispatch in",
            moved_mwh / _MWH_PER_TWH,
            len(moved_plants),
        )
    if add:
        e923 = pd.concat([e923, pd.DataFrame(add)], ignore_index=True)
    return e923


# Variable-renewable classes the EIA-923 monthly survey under-reports (no CAMPD
# backfill reaches them) but EIA-930 telemetry measures grid-side — the basis
# the model's grid LP dispatch is judged on. Replaced with the EIA-930 grid
# total whenever the EIA-923 class total falls below this fraction of it (the
# same per-fuel guard build_calibration_reference applies to the reference).
_EIA930_RENEWABLE_CLASSES: tuple[str, ...] = ("wind", "solar", "hydro")
_EIA923_RENEWABLE_COMPLETENESS_FRACTION: float = 0.90
# A whole vintage is a partial release when the ISO's total EIA-923 net gen is
# below this fraction of the EIA-930 grid net generation (the 2025 early monthly
# survey ~73%); only then is biomass — absent from CAMPD and EIA-930 — carried
# from the prior complete year.
_EIA923_VINTAGE_COMPLETENESS_FRACTION: float = 0.90


def _e930_series_annual_monthly(
    e930: pd.DataFrame | None,
    series: str,
    year: int,
) -> tuple[float, list[float]]:
    """Return ``(annual_mwh, [m01..m12])`` for one EIA-930 long-format series."""
    if e930 is None:
        return 0.0, [0.0] * 12
    sub = e930[e930["series"] == series]
    if sub.empty:
        return 0.0, [0.0] * 12
    arr = sub.sort_values("hour")["mw"].to_numpy(dtype=float)
    months = _hour_months(year, len(arr))
    monthly = [float(np.clip(arr[months == m], 0.0, None).sum()) for m in range(1, 13)]
    return float(sum(monthly)), monthly


@lru_cache(maxsize=None)
def _hydro_benchmark_is_923_only(iso: str, year: int) -> bool:
    """Return True when ``(iso, year)``'s hydro ACTUAL must stay on EIA-923 ``HY``.

    The benchmark's default for the variable renewables is to replace an
    under-reported EIA-923 class total with the EIA-930 grid series. For
    ``hydro`` that swap is only legitimate when ``NG: WAT`` measures the SAME
    POPULATION as the model's hydro units, and at some BAs it does not.

    **The mismatch.** A BA in
    :data:`~market_sim.config.constants.EIA930_PS_FOLDED_INTO_WAT` files no
    ``NG: PS`` column at all, and a BA before its
    :data:`~market_sim.config.constants.EIA930_PS_SPLIT_COMPLETE_FROM` year
    files one only part-way through the series; either way that ISO-year's
    ``NG: WAT`` is conventional hydro **plus pumped-storage gross discharge**
    (``data.hydro.eia930_wat_level_folded``). The LP's hydro units are
    conventional inflow hydro ALONE — ``data.hydro._load_hydro_generation``
    filters EIA-923 prime mover ``HY`` **directly**, never through
    ``classify_plant`` — so the swap scores one population's dispatch against
    another population's meter. Measured on PJM it inflates the hydro actual by
    5.96-7.11 TWh/yr in every year and is the whole of that ISO's apparent
    ~44 % hydro "miss"
    (``docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md``). This is the
    BENCHMARK end of the repair ``pjm-143`` already landed on the MODEL end:
    ``hydro_level_923_hy`` moved PJM's hydro budget LEVEL off ``NG: WAT`` and
    onto EIA-923 ``HY`` for exactly this reason, leaving the two sides of one
    comparison on different populations until now. Rule 14 ``[R-ACCURATE]``;
    rule 19 ``[R-ONE-MECH]`` — the SAME already-adjudicated predicate at both
    ends (miso-109 standing fold, miso-110 forward climatology, neiso-72 time
    split), never a second mechanism. The direction is fixed by which population
    ``_load_hydro_generation`` builds and no result can select it.

    **THE SECOND CONDITION IS LOAD-BEARING AND IS WHY THIS IS TWO PREDICATES.**
    Refusing the swap is only a repair when there is a right-population
    measurement to refuse it in favour of. In an EIA-923 early monthly release
    there is not: PJM 2025 files **10 of 72** hydro plants (2.29 TWh against a
    modal ~8.9) and MISO **14 of 160**, so refusing the swap there would replace
    a +74 % error with a -74 % one. The ISO-wide
    :func:`_vintage_completeness` cannot catch this — it reads **0.923** for
    both ISOs in 2025 because the early release covers the large fossil and
    nuclear plants that carry nearly all the MWh — so the class's OWN census
    gate is used instead: ``data.hydro.complete_923_hydro_years``, the
    already-adjudicated data-quality filter behind
    ``climatological_monthly_hydro_923`` (miso-109's "2025 trap", miso-110),
    which admits a year only when its ``HY`` plant census reaches
    :data:`~market_sim.config.constants.EIA923_COMPLETE_FILING_CENSUS_FRACTION`
    of the ISO's modal census AND the vintage is no newer than
    ``EIA923_LATEST_FINAL_VINTAGE``. It can only ever REMOVE a year, so it is a
    filter and never a tune. Measured: complete in 2020-2024 for all seven ISOs,
    incomplete in 2025 for all seven.

    **SELF-HEALING, which is what makes the residue acceptable.** PJM 2025 and
    MISO 2025 are the only cells where the seam is diagnosed and left
    unrepaired; when the final 2025 EIA-923 vintage lands, the census fills, the
    predicate flips and the repair reaches them with **no code change**. The
    rationale, the three candidate scalars that were measured unusable, and the
    cost are ``docs/ADDENDUM-gov-hydro-seam-1-vintage-fallthrough-2026-09-12.md``.

    **Zero new parameters, zero new registry, zero new constants** (rules 21 /
    24): two existing predicates, ANDed.

    Args:
        iso: ISO identifier, e.g. ``"PJM"``.
        year: Calendar year.

    Returns:
        True when the EIA-930 ``NG: WAT`` swap must be refused for this
        ISO-year, leaving the measured EIA-923 ``HY`` class total in place.
    """
    from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS
    from market_sim.data.hydro import complete_923_hydro_years

    if not eia930_wat_level_folded(iso, year):
        return False
    # The census gate needs a reference window to take its modal census over;
    # the shared climatology constant plus the year under test is fixed by
    # construction, so no result can select it (rule 23 [R-FROZEN-DERIVE]).
    window = sorted({*(int(y) for y in HYDRO_CLIMATOLOGY_YEARS), int(year)})
    return int(year) in complete_923_hydro_years(iso, window)


def _replace_class_total(
    e923: pd.DataFrame,
    klass: str,
    year: int,
    annual: float,
    monthly: list[float],
) -> pd.DataFrame:
    """Drop ``klass``'s per-plant rows and insert one synthetic class-total row.

    The variable-renewable / biomass benchmark is a class aggregate (the dashboard
    ``classFull`` sums EIA-923 by class), so a single sentinel row (``plant_id``
    0) carrying the class annual + monthly is sufficient and keeps the by-class
    total exact. No renewable class is matched per-plant downstream.
    """
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    kept = e923[e923["klass"] != klass].copy()
    row = {
        "year": np.int16(year),
        "plant_id": 0,
        "klass": klass,
        "annual_mwh": float(annual),
        **{c: float(monthly[i]) for i, c in enumerate(mcols)},
    }
    return pd.concat([kept, pd.DataFrame([row])], ignore_index=True)


def _vintage_completeness(
    year: int,
    generation: pd.DataFrame,
    iso: str,
    e930: pd.DataFrame | None,
    benchmark_membership_vintage_union: bool = False,
) -> float:
    """ISO EIA-923 total net gen as a fraction of the EIA-930 grid net_gen.

    ~1.0 for a complete vintage; the 2025 early monthly survey reads ~0.73.
    Returns 1.0 when no EIA-930 net_gen is available (no swap then).

    Reads the SAME membership as :func:`_eia923_frame` (spp-49): a completeness
    ratio taken over a narrower plant set than the frame it gates would make
    the vintage look less complete than it is and fire a carry the frame does
    not need.
    """
    ann930_net, _ = _e930_series_annual_monthly(e930, "net_gen", year)
    if ann930_net <= 0.0:
        return 1.0
    iso_plants = _iso_plant_ids(iso, year, bool(benchmark_membership_vintage_union))
    g = generation[generation["year"] == year]
    if iso_plants:
        g = g[g["plant_id"].isin(iso_plants)]
    e923_total = float(g["netgen_annual_mwh"].sum())
    return e923_total / ann930_net


def _reconciled_mustrun_class(
    klass: str,
    year: int,
    generation: pd.DataFrame,
    iso: str,
    e930: pd.DataFrame | None,
    mustrun_chp_btm_holdout: bool = False,
    benchmark_membership_vintage_union: bool = False,
) -> tuple[float, np.ndarray]:
    """Measured injected-class energy ``(annual_mwh, monthly[12])`` with the carry.

    The single source of truth for "how much" of an injected residual class
    (``biomass`` / ``OTHER``) both the benchmark and the must-run injection
    consume, so the model's injected energy is pinned to the exact value it is
    scored against. These classes are absent from CAMPD and EIA-930, so for a
    partial current-year EIA-923 release (vintage completeness below
    :data:`_EIA923_VINTAGE_COMPLETENESS_FRACTION`) the prior complete year's class
    total is carried forward scaled by completeness (its monthly shape reused),
    matching :func:`_backfill_renewables_eia930`. Pumped-storage plants are held
    out of ``OTHER`` (current and prior year) — they dispatch as LP storage. A
    complete vintage returns the raw EIA-923 value unchanged. ``e930 is None``
    disables the carry (the completeness probe needs the EIA-930 grid total). This
    is a legitimate measured physical input: it regenerates per forward year from
    EIA-923 and is a fuel/contract supply limit, not a residual tune.
    """
    mcols = [f"m{i:02d}" for i in range(1, 13)]

    def _rows(yr: int) -> pd.DataFrame:
        df = _eia923_frame(
            yr,
            generation,
            iso,
            mustrun_chp_btm_holdout,
            benchmark_membership_vintage_union,
        )
        df = df[df["klass"] == klass]
        if klass == "OTHER":
            df = df[~df["plant_id"].isin(_pumped_storage_plant_ids())]
        return df

    cur = _rows(year)
    annual = float(cur["annual_mwh"].sum())
    monthly = cur[mcols].sum().to_numpy(dtype=float)
    completeness = _vintage_completeness(
        year, generation, iso, e930, benchmark_membership_vintage_union
    )
    if completeness < _EIA923_VINTAGE_COMPLETENESS_FRACTION:
        prior = _rows(year - 1)
        prior_ann = float(prior["annual_mwh"].sum())
        est = prior_ann * completeness
        if prior_ann > 0.0 and est > annual:
            prior_mon = prior[mcols].sum().to_numpy(dtype=float)
            psum = float(prior_mon.sum())
            monthly = prior_mon * (est / psum) if psum > 0 else np.full(12, est / 12.0)
            annual = est
    return annual, monthly


def _reconciled_biomass_class(
    year: int,
    generation: pd.DataFrame,
    iso: str,
    e930: pd.DataFrame | None,
    mustrun_chp_btm_holdout: bool = False,
) -> tuple[float, np.ndarray]:
    """Measured biomass class energy ``(annual_mwh, monthly[12])`` with the carry.

    Thin wrapper over :func:`_reconciled_mustrun_class` for the biomass class (the
    benchmark's biomass repair and the report's like-for-like total still call it
    by name).
    """
    return _reconciled_mustrun_class(
        "biomass", year, generation, iso, e930, mustrun_chp_btm_holdout
    )


def _backfill_renewables_eia930(
    e923: pd.DataFrame,
    year: int,
    iso: str,
    generation: pd.DataFrame,
    e930: pd.DataFrame | None,
    mustrun_chp_btm_holdout: bool = False,
    benchmark_membership_vintage_union: bool = False,
) -> pd.DataFrame:
    """Source under-counted renewables from EIA-930 and biomass from a prior year.

    For an incomplete EIA-923 vintage (the current-year early monthly survey),
    the variable renewables and biomass are not reached by the CAMPD thermal
    backfill, leaving the per-class benchmark far below the real grid total. This
    repairs them so EVERY class carries a full-year 2025 benchmark:

    * ``wind`` / ``solar`` / ``hydro``: when the EIA-923 class total is below
      :data:`_EIA923_RENEWABLE_COMPLETENESS_FRACTION` of the EIA-930 grid series,
      the class total (annual + monthly shape) is taken from EIA-930 — the
      grid-side authority the model's dispatch is scored against. Complete
      vintages, where the two agree, are unchanged; CAISO wind, under-reported in
      EIA-923 every year, is corrected in every year (matching the reference).
      When a class has NO ADMISSIBLE EIA-930 authority that swap is unavailable
      and the class falls through to the ``biomass`` carry-forward below instead
      of being left truncated -- the BA reports the series as identically zero
      (NYIS ``NG: SUN``, the only such cell across 6 ISOs x {wind, solar, hydro}
      x 2023-2025 -- nyiso-106).
    * ``hydro`` is additionally REFUSED the swap outright, keeping its measured
      EIA-923 ``HY`` total, when this ISO-year's ``NG: WAT`` folds pumped-storage
      discharge into conventional hydro AND the year's own ``HY`` census is
      complete (:func:`_hydro_benchmark_is_923_only`). The folded series is a
      different POPULATION from the LP's conventional-hydro units, so the swap
      compares one population's dispatch against another's meter -- PJM in every
      year, MISO and pre-2025 NEISO in most (gov-hydro-seam-1).
    * ``biomass``: absent from both CAMPD and EIA-930. When the whole vintage is
      a partial release (:func:`_vintage_completeness`), the prior complete
      year's biomass class total is carried forward, scaled by the vintage
      completeness (its monthly shape reused), rather than left truncated.
    """
    if e930 is None:
        return e923
    cls_total = e923.groupby("klass")["annual_mwh"].sum()
    for klass in _EIA930_RENEWABLE_CLASSES:
        if klass == "hydro" and _hydro_benchmark_is_923_only(iso, year):
            # This ISO-year's `NG: WAT` folds pumped-storage discharge into
            # conventional hydro, so it is a different POPULATION from the LP's
            # hydro units, and the year's own EIA-923 `HY` census is complete —
            # i.e. a right-population measurement exists. Keep it and skip the
            # swap. No carry and no estimate: the class total stays exactly the
            # measured EIA-923 `HY` energy (see _hydro_benchmark_is_923_only).
            logger.info(
                "EIA-923 %d %s %.2f TWh kept on EIA-923 HY: %s NG: WAT folds "
                "pumped storage (different population; EIA930_PS_FOLDED_INTO_WAT "
                "/ EIA930_PS_SPLIT_COMPLETE_FROM)",
                year,
                klass,
                float(cls_total.get(klass, 0.0)) / _MWH_PER_TWH,
                iso,
            )
            continue
        ann930, mon930 = _e930_series_annual_monthly(e930, klass, year)
        if ann930 <= 0.0:
            # No EIA-930 authority for this class, so the grid-total swap above
            # is unavailable -- but that is exactly when a partial 923 vintage
            # is MOST dangerous, because nothing else repairs the class. This
            # is not hypothetical: EIA-930 NYIS `NG: SUN` is identically 0.0 in
            # every hour of every year (NY grid solar is overwhelmingly
            # distribution-connected / net-metered, invisible to the BA
            # telemetry) -- the very fact that makes
            # `results.calibration._EIA923_OVERRIDE` route NYISO solar's
            # SCORING to EIA-923. The repair kept keying on EIA-930 and so
            # silently no-opped on the one cell the override exists for: the
            # 2025 vintage carries 8 of 565 NYIS solar plants (0.662 TWh vs
            # 2.901 in 2024), which scored as solar +437% against the model.
            #
            # Such a class is in exactly biomass's position -- absent from
            # CAMPD, absent from EIA-930, truncated by a partial vintage -- so
            # it takes exactly biomass's already-committed repair: the prior
            # complete year's class total scaled by the vintage completeness,
            # reusing that year's monthly shape. No new parameter, no new
            # threshold, and a complete vintage is an exact no-op (2023/2024
            # NYISO read completeness 1.05 / 1.04). Measured throughout, and
            # conservative by construction: a carry-forward under-states a
            # growing class rather than fitting it (rules 13 / 21).
            #
            # Blast radius, measured across 6 ISOs x {wind, solar, hydro} x
            # 2023-2025: NYISO solar is the ONLY cell with a zero EIA-930
            # authority, so this fires nowhere else.
            # Evidence: results/calibration/FINDING-nyiso106-solar-benchmark-
            # vintage-2026-07-31.md.
            ann, mon = _reconciled_mustrun_class(
                klass,
                year,
                generation,
                iso,
                e930,
                mustrun_chp_btm_holdout,
                benchmark_membership_vintage_union,
            )
            cur = float(cls_total.get(klass, 0.0))
            if ann > cur:
                logger.info(
                    "EIA-923 %d %s %.2f TWh incomplete with no admissible "
                    "EIA-930 authority; carrying %d forward x vintage "
                    "completeness -> %.2f TWh",
                    year,
                    klass,
                    cur / _MWH_PER_TWH,
                    year - 1,
                    ann / _MWH_PER_TWH,
                )
                e923 = _replace_class_total(e923, klass, year, ann, list(mon))
            continue
        cur = float(cls_total.get(klass, 0.0))
        if cur < _EIA923_RENEWABLE_COMPLETENESS_FRACTION * ann930:
            logger.info(
                "EIA-923 %d %s %.2f TWh under-counts EIA-930 %.2f TWh; "
                "using EIA-930 grid total",
                year,
                klass,
                cur / _MWH_PER_TWH,
                ann930 / _MWH_PER_TWH,
            )
            e923 = _replace_class_total(e923, klass, year, ann930, mon930)

    completeness = _vintage_completeness(
        year, generation, iso, e930, benchmark_membership_vintage_union
    )
    if completeness < _EIA923_VINTAGE_COMPLETENESS_FRACTION:
        mcols = [f"m{i:02d}" for i in range(1, 13)]
        prior = _eia923_frame(
            year - 1,
            generation,
            iso,
            mustrun_chp_btm_holdout,
            benchmark_membership_vintage_union,
        )
        prior_bio = prior[prior["klass"] == "biomass"]
        prior_ann = float(prior_bio["annual_mwh"].sum())
        cur_bio = float(cls_total.get("biomass", 0.0))
        est = prior_ann * completeness
        if prior_ann > 0.0 and est > cur_bio:
            prior_mon = prior_bio[mcols].sum().to_numpy(dtype=float)
            psum = float(prior_mon.sum())
            monthly = (
                (prior_mon * (est / psum)).tolist() if psum > 0 else [est / 12.0] * 12
            )
            logger.info(
                "EIA-923 %d biomass %.2f TWh incomplete (vintage %.0f%%); "
                "carrying %d biomass %.2f TWh x completeness -> %.2f TWh",
                year,
                cur_bio / _MWH_PER_TWH,
                completeness * 100.0,
                year - 1,
                prior_ann / _MWH_PER_TWH,
                est / _MWH_PER_TWH,
            )
            e923 = _replace_class_total(e923, "biomass", year, est, monthly)
    return e923


# Bounded look-back (years) for a plant's prior-year EIA-923 class shares when its
# current vintage under-reports it. In practice the immediately prior complete year
# resolves it (mirroring _reconciled_mustrun_class's single-year carry); the walk
# only reaches further for a plant sparse in several consecutive vintages.
_CLASS_SHARE_MAX_PRIOR_YEARS: int = 4


def _plant_class_shares(
    iso: str,
    generation: pd.DataFrame,
    year: int,
    benchmark_membership_vintage_union: bool = False,
) -> dict[int, dict[str, float]]:
    """Return ``{plant_id: {klass: share}}`` — each plant's EIA-923 prime-mover
    class split across the CAMPD-backfill-eligible thermal classes, shares summing
    to 1.

    The non-ERCOT plant-level analogue of per-unit-class bucketing: it lets the
    CAMPD backfill split a genuinely mixed plant's net across the classes
    physically at it (WA-Parish coal+gas, Doswell/Linden CC+CT) rather than book
    the whole plant net to one last-generator-wins class. Shares are the EIA-923
    survey's **measured** per-class net energies — rule 11: measured, never a
    nameplate-capacity estimate (which would ignore the very different CC-vs-CT
    capacity factors). They are read from the plant's **current-year** vintage when
    it reports the plant adequately (its eligible-class total clears
    :data:`_CAMPD_BACKFILL_MIN_MWH` — the same threshold the backfill gates on),
    and otherwise from the **most recent prior year** that does: an incomplete
    current vintage — the reason the backfill fires at all — carries an unreliable
    split, so a prior complete year's split is preferred (same prior-year carry
    idea as :func:`_reconciled_mustrun_class`). A plant with no adequate vintage
    anywhere returns no entry, so the backfill falls back to its single-class
    behavior for it (no regression). Deterministic; no residual-tuned constants
    (rule 24). ERCOT never calls this (its curated bin sheet drives the backfill).
    """

    def _vintage(yr: int) -> pd.Series:
        df = _eia923_frame(
            yr,
            generation,
            iso,
            benchmark_membership_vintage_union=(benchmark_membership_vintage_union),
        )
        df = df[df["klass"].isin(_BACKFILL_TARGET_KLASSES)]
        return df.groupby(["plant_id", "klass"])["annual_mwh"].sum()

    cur = _vintage(year)
    prior_cache: dict[int, pd.Series] = {}

    def _prior(yr: int) -> pd.Series:
        if yr not in prior_cache:
            prior_cache[yr] = _vintage(yr)
        return prior_cache[yr]

    cur_tot = cur.groupby(level=0).sum() if not cur.empty else pd.Series(dtype=float)
    # Candidate plants: any with eligible EIA-923 in the current or recent prior
    # vintages, so a plant truncated to ~zero this year but split in a prior year
    # is still splittable.
    pids: set[int] = {int(p) for p in cur_tot.index}
    for back in range(1, _CLASS_SHARE_MAX_PRIOR_YEARS + 1):
        pv = _prior(year - back)
        if not pv.empty:
            pids.update(int(p) for p in pv.index.get_level_values(0).unique())

    out: dict[int, dict[str, float]] = {}
    for pid in pids:
        src: pd.Series | None = None
        if float(cur_tot.get(pid, 0.0)) >= _CAMPD_BACKFILL_MIN_MWH:
            src = cur
        else:
            for back in range(1, _CLASS_SHARE_MAX_PRIOR_YEARS + 1):
                pv = _prior(year - back)
                if pv.empty or pid not in pv.index.get_level_values(0):
                    continue
                if float(pv.loc[pid].sum()) >= _CAMPD_BACKFILL_MIN_MWH:
                    src = pv
                    break
        if src is None:
            continue
        sub = src.loc[pid]
        total = float(sub.sum())
        if total <= 0.0:
            continue
        shares = {str(k): float(v) / total for k, v in sub.items() if float(v) > 0.0}
        if shares:
            out[pid] = shares
    return out


def _backfill_chp_eia923_from_donor(
    e923: pd.DataFrame,
    generation: pd.DataFrame,
    group_by_code: dict[int, str],
    year: int,
    donor_year: int,
    campd_active: set[int] | None = None,
) -> pd.DataFrame:
    """Carry a CHP plant's donor-vintage class total into the **benchmark**.

    The benchmark-side mirror of the ``btm_backfill_year`` repair inside
    :func:`_btm_frame`. The two must move together. ``classFull`` is
    ``EIA-923 class total − BTM host self-supply``; the BTM repair carries a
    plant whose per-(plant, class) total is missing from ``year``'s thin
    EIA-923 vintage (the monthly-survey-only release). Repairing only that
    *subtrahend* subtracts a plant's host share from a class total that never
    received the plant's energy, so the difference can go negative — which is
    exactly what PJM 2025 did: ``classFull.CT_CHP = −0.3726 TWh``, a negative
    metered volume (surfaced by pjm-129 §6, localized and reproduced by
    pjm-130, which recovers the committed ``btmClass`` cells to 4 dp only with
    this backfill armed).

    The CAMPD backfill in :func:`_backfill_eia923_with_campd` cannot cover this:
    it fires on **non-CHP** grid plants by construction, so a CHP plant absent
    from the thin vintage is repaired on neither side without this.

    Same donor vintage, same ``campd_active`` gate (a CEMS-silent plant stays
    dropped on both sides), same per-(plant, class) key as the BTM repair — so
    the repaired benchmark and the repaired BTM describe the same plant
    population and ``btm[k] <= e923[k]`` holds by construction, the host share
    being a fraction <= 1. Rule 11 [R-ACCURATE]: the plant genuinely generated,
    the gap is a reporting artifact of the vintage, so the accurate treatment
    repairs both sides — never one.

    Only the three CHP classes are touched, and only for a (plant, class) the
    benchmark currently reports as zero, so a complete vintage is a no-op and
    every non-CHP class is byte-identical.
    """
    donor = generation[generation["year"] == donor_year].copy()
    if donor.empty:
        return e923
    donor["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            donor["fuel_type"], donor["prime_mover"], donor["chp"], donor["plant_id"]
        )
    ]
    mcols = monthly_netgen_columns()
    donor_ann = donor.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
    donor_mon = donor.groupby(["plant_id", "klass"])[mcols].sum()

    have = (
        set(zip(e923["plant_id"].astype(int), e923["klass"].astype(str)))
        if not e923.empty
        else set()
    )
    reported = (
        e923.groupby(["plant_id", "klass"])["annual_mwh"].sum()
        if not e923.empty
        else pd.Series(dtype=float)
    )
    out_cols = [f"m{i:02d}" for i in range(1, 13)]
    added = []
    for code, grp in group_by_code.items():
        grp = str(grp)
        if grp not in ("CC_CHP", "CT_CHP", "ST_CHP"):
            continue
        code = int(code)
        if float(reported.get((code, grp), 0.0)) > 0.0:
            continue  # measured this year — never overwritten (rule 11)
        if campd_active is not None and code not in campd_active:
            continue  # CEMS-silent: stays dropped on both sides
        carried = float(donor_ann.get((code, grp), 0.0))
        if carried <= 0.0:
            continue
        mon = (
            donor_mon.loc[(code, grp)].to_numpy(dtype=float)
            if (code, grp) in donor_mon.index
            else np.zeros(12)
        )
        row = {
            "year": np.int16(year),
            "plant_id": code,
            "klass": grp,
            "annual_mwh": carried,
            **{c: float(mon[i]) for i, c in enumerate(out_cols)},
        }
        added.append(row)
        logging.info(
            "benchmark 923 CHP backfill %s: plant %s %s carries %s class "
            "netgen %.0f MWh (missing from the %s vintage, CAMPD active) — "
            "mirrors the BTM backfill so classFull stays non-negative",
            year,
            code,
            grp,
            donor_year,
            carried,
            year,
        )
    if not added:
        return e923
    extra = pd.DataFrame(added)
    if have:
        extra = extra[~extra.set_index(["plant_id", "klass"]).index.isin(have)]
        if extra.empty:
            return e923
    return pd.concat([e923, extra], ignore_index=True)


def _benchmark_eia923_frame(
    year: int,
    generation: pd.DataFrame,
    iso: str,
    campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str],
    e930: pd.DataFrame | None,
    btm_backfill_year: int | None = None,
    campd_active: set[int] | None = None,
    mustrun_chp_btm_holdout: bool = False,
    benchmark_membership_vintage_union: bool = False,
) -> pd.DataFrame:
    """The bundle's per-class EIA-923 benchmark: CAMPD thermal backfill + the
    EIA-930 renewable / prior-year biomass repair for incomplete vintages.

    Non-ERCOT plants split the CAMPD backfill by measured prime-mover class shares
    (:func:`_plant_class_shares`); ERCOT keeps the single-class bin-sheet path
    (``class_shares=None``), so its output is byte-identical.

    ``btm_backfill_year`` / ``campd_active`` mirror the BTM repair onto the
    benchmark for the CHP classes the CAMPD backfill does not reach — see
    :func:`_backfill_chp_eia923_from_donor`. Unset (or a complete vintage) is a
    no-op.

    ``benchmark_membership_vintage_union`` (spp-49, default off,
    byte-identical off) reaches EVERY membership read below — the frame, the
    class shares, and the renewable/biomass repair's completeness probe — so
    the benchmark and the must-run injection cannot end up on two different
    plant populations (rule 19 [R-ONE-MECH], the same single-seam discipline
    ``mustrun_chp_btm_holdout`` follows).
    """
    class_shares = (
        None
        if iso == "ERCOT"
        else _plant_class_shares(
            iso, generation, year, benchmark_membership_vintage_union
        )
    )
    e923 = _backfill_eia923_with_campd(
        _eia923_frame(
            year,
            generation,
            iso,
            mustrun_chp_btm_holdout,
            benchmark_membership_vintage_union,
        ),
        campd_year,
        group_by_code,
        year,
        class_shares=class_shares,
    )
    # Two boundary repairs that run AFTER the annual-floor backfill and never
    # change which plants it reaches (nyiso-240, rule 14 [R-ACCURATE]):
    #   1. months EIA-923 withheld entirely — invisible to an annual-grain guard,
    #      and absent from EIA's own published annual, not merely from its shape;
    #   2. a dual-fuel plant's oil MWh, which EIA-923 books under the fuel burned
    #      while the LP keeps the unit dispatching in its own class.
    # Both are benchmark constructions: zero ScenarioConfig fields, zero free
    # parameters, no mechanism-matrix row, and no solve path touched.
    e923 = _backfill_eia923_missing_months(
        e923,
        campd_year,
        group_by_code,
        year,
        generation,
        class_shares=class_shares,
    )
    e923 = _reattribute_dual_fuel_oil(e923, group_by_code, class_shares=class_shares)
    if btm_backfill_year is not None:
        e923 = _backfill_chp_eia923_from_donor(
            e923,
            generation,
            group_by_code,
            year,
            btm_backfill_year,
            campd_active=campd_active,
        )
    return _backfill_renewables_eia930(
        e923,
        year,
        iso,
        generation,
        e930,
        mustrun_chp_btm_holdout,
        benchmark_membership_vintage_union,
    )


def _btm_frame(
    year: int,
    pass_label: str,
    generation: pd.DataFrame,
    btm_backfill_year: int | None = None,
    campd_active: set[int] | None = None,
    iso: str = "ERCOT",
    group_by_code: dict[int, str] | None = None,
    nyiso_chp_btm_measured: bool = False,
) -> pd.DataFrame:
    """Return behind-the-meter CHP must-run by class for one year-pass.

    Measured-input sizing (CLAUDE.md rule #13): each plant's BTM host
    self-supply is its per-(plant, class) EIA-923 net generation times its
    measured host-share — :func:`market_sim.data.chp.chp_btm_pct` (sector
    shares / per-plant overrides, the identical share the LP hold-out uses)
    for the CHP groups, the curated bin sheet's ``pct_mr`` for the few
    non-CHP cogen bins (e.g. San Jacinto). The model's dispatch never enters:
    the earlier sizing (923 class total minus the model's own grid dispatch,
    clipped at zero) made the bench-side grid-delivered "actual"
    (``923 − btm``) equal the model whenever the model under-dispatched a
    CHP class — the C1 gate could not fail (a vacuous pass) — and the
    attribution varied between solves of identical code+data. This frame is
    now a pure function of committed inputs, so two rebuilds are
    byte-identical and the same sizing regenerates for a forward year.

    ``btm_backfill_year``: the BTM add-back is keyed off the plant's EIA-923
    class net generation for ``year``; the most recent 923 vintage is a
    monthly-survey-only release that can miss a plant entirely (e.g. San
    Jacinto, 7325, absent from the 2025 vintage), zeroing its add-back while
    the class *benchmark* keeps the plant via the CAMPD backfill — an
    inconsistent comparison. When set, a plant whose (plant, class) 923
    total is zero for ``year`` borrows its ``btm_backfill_year`` class total
    instead, but ONLY if CAMPD shows the plant actually generating in
    ``year`` (``campd_active``) — a CEMS-silent plant stays dropped on both
    sides. Mirrors ``--hydro-backfill-year``. Unset = no change.

    The plant->class bin source is ISO-specific, mirroring the EIA-923
    benchmark backfill: ERCOT uses the curated CAMPD bin sheet; every other
    ISO uses the year's EIA-860 per-plant fleet group map (``group_by_code``,
    from :func:`_fleet_group_by_code`) so the BTM hold-out is bucketed the
    same way the dispatch frame and the class benchmark are. Only the CHP
    groups (CC_CHP / CT_CHP / ST_CHP) carry a behind-the-meter must-run
    tranche, so the synthetic non-ERCOT frame marks them with ``pct_mr > 0``
    and leaves every other class out of the BTM reconciliation; the
    ``capacity_mw`` / ``hr_weighted`` columns feed only the discarded
    flat-CF / CO2 estimates, never ``btm_twh``.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.chp import chp_btm_pct
    from market_sim.data.coal import coal_chp_overrides
    from market_sim.data.fleet import (
        CHP_BTM_PCT_BY_SECTOR,
        BIN_GROUP_TO_FUEL,
        load_campd_bins,
    )
    from market_sim.results.emissions import compute_must_run_emissions

    is_ercot = iso == "ERCOT"
    # The EIA-923 bins carry the 923-dominant class for the year, so the bin's
    # class is what the plant actually burned (no curated drift). ERCOT reads
    # the curated sheet; every other ISO builds the equivalent one-row-per-plant
    # frame from the year's EIA-860 fleet group map.
    if is_ercot:
        bins = load_campd_bins(ScenarioConfig().campd_bins_path, year=year)
    else:
        gbc = group_by_code or {}
        bins = pd.DataFrame(
            {
                "Plant_Code": list(gbc.keys()),
                "Plant_Group": list(gbc.values()),
            }
        )
        bins["fuel"] = bins["Plant_Group"].map(BIN_GROUP_TO_FUEL)
        bins["pct_mr"] = np.where(
            bins["Plant_Group"].isin(("CC_CHP", "CT_CHP", "ST_CHP")), 100.0, 0.0
        )
        bins["capacity_mw"] = 0.0
        bins["hr_weighted"] = 8.0
    # Key BTM off the plant's PER-CLASS EIA-923 net generation — the 923 total
    # of the bin's own class, not whole-plant netgen. A plant that splits across
    # classes (e.g. a merchant CC block plus a CHP train) then can't lend one
    # class's output to another, so a class total can't exceed its real EIA-923.
    f923 = generation[generation["year"] == year].copy()
    f923["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            f923["fuel_type"], f923["prime_mover"], f923["chp"], f923["plant_id"]
        )
    ]
    class_total = f923.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
    total_by_plant = {
        int(code): float(class_total.get((int(code), str(grp)), 0.0))
        for code, grp in zip(bins["Plant_Code"], bins["Plant_Group"])
    }
    if btm_backfill_year is not None:
        donor = generation[generation["year"] == btm_backfill_year].copy()
        donor["klass"] = [
            _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
            for f, pm, c, pid in zip(
                donor["fuel_type"],
                donor["prime_mover"],
                donor["chp"],
                donor["plant_id"],
            )
        ]
        donor_total = donor.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
        for code, grp in zip(bins["Plant_Code"], bins["Plant_Group"]):
            code = int(code)
            if total_by_plant.get(code, 0.0) > 0.0:
                continue
            if campd_active is not None and code not in campd_active:
                continue
            carried = float(donor_total.get((code, str(grp)), 0.0))
            if carried > 0.0:
                total_by_plant[code] = carried
                logging.info(
                    "BTM 923 backfill %s: plant %s %s carries %s class "
                    "netgen %.0f MWh (missing from the %s vintage, CAMPD "
                    "active)",
                    year,
                    code,
                    grp,
                    btm_backfill_year,
                    carried,
                    year,
                )
    # Measured host-share per plant: chp_btm_pct (sector shares / per-plant
    # overrides — the identical share the LP hold-out removes) for the CHP
    # groups; the curated sheet's pct_mr for the few non-CHP cogen bins the
    # sheet holds out (Lost Pines self-supply, San Jacinto). Coal rows are
    # filtered inside compute_must_run_emissions and are booked below instead.
    share_by_plant = {
        int(code): (
            chp_btm_pct(int(code), str(grp), iso=iso) / 100.0
            if str(grp) in ("CC_CHP", "CT_CHP", "ST_CHP")
            else float(pct) / 100.0
        )
        for code, grp, pct in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["pct_mr"]
        )
        if float(pct) > 0.0
    }
    # nyiso-147: with the measured shares armed, the add-back must size from
    # the SAME per-plant Gold-Book/EIA-923 shares the LP hold-out removed —
    # classFull is EIA-923 minus this frame, so the three legs (capacity
    # carve, add-back, benchmark subtrahend) stay on one share by
    # construction.
    #
    # nyiso-149 [R-ACCURATE]: the BENCHMARK subtrahend is pinned to the
    # measured shares whenever the measured artifact exists, INDEPENDENT of
    # the run's flag. The run-basis map (``share_by_plant`` -> ``btm_twh``)
    # still follows the flag — it describes what THIS run's LP held out (the
    # model-side add-back) — but the shared bench part's "actual grid
    # delivery" is a physical fact that cannot depend on the registering
    # run's config: letting it follow the flag is what flipped the committed
    # NYISO parts between flag-off and flag-on registrations and silently
    # re-armed the ±3% family reconcile (the ×1.07–×1.19 gas-family scale
    # the sector carve forced — FINDING-nyiso149-bench-root-cause-2026-08-22
    # §3). ``btm_bench_twh`` carries the measured-basis class totals; for
    # every ISO without a measured artifact the two maps are identical and
    # the column duplicates ``btm_twh`` byte-for-byte.
    share_bench_by_plant = dict(share_by_plant)
    if iso == "NYISO":
        from market_sim.data.chp import measured_chp_btm_pct_nyiso

        _measured = measured_chp_btm_pct_nyiso()
        _chp_codes = {
            int(code)
            for code, grp in zip(bins["Plant_Code"], bins["Plant_Group"])
            if str(grp) in ("CC_CHP", "CT_CHP", "ST_CHP")
        }
        for _code, _pct in _measured.items():
            if _code in _chp_codes:
                if _code in share_bench_by_plant:
                    share_bench_by_plant[_code] = float(_pct) / 100.0
                if nyiso_chp_btm_measured and _code in share_by_plant:
                    share_by_plant[_code] = float(_pct) / 100.0

    def _class_totals(shares: dict[int, float]) -> dict[str, float]:
        mr = compute_must_run_emissions(
            bins,
            year,
            total_gen_by_plant=total_by_plant,
            btm_share_by_plant=shares,
        )
        out: dict[str, float] = {}
        if not mr.empty:
            for grp, twh in (
                mr.groupby("Plant_Group")["mr_gen_mwh"].sum() / _MWH_PER_TWH
            ).items():
                out[str(grp)] = out.get(str(grp), 0.0) + float(twh)
        return out

    btm_by_class = _class_totals(share_by_plant)
    btm_bench_by_class = (
        dict(btm_by_class)
        if share_bench_by_plant == share_by_plant
        else _class_totals(share_bench_by_plant)
    )
    # Coal cogen (PJM): host self-supply held out of the LP is chp_btm_pct of the
    # plant's measured EIA-923 coal-class net generation, booked under the coal
    # class so render subtracts it from classFull on both sides — the same
    # behind-the-meter treatment the gas cogens get, extended to the chemical /
    # culm coal hosts the dispatch now removes from the economic stack.
    coal_chp = coal_chp_overrides(iso, year) if not is_ercot else {}
    if coal_chp:
        for (pid, klass), tot in class_total.items():
            if int(pid) not in coal_chp or not str(klass).startswith("COAL"):
                continue
            _, sector = coal_chp[int(pid)]
            pct = CHP_BTM_PCT_BY_SECTOR.get(sector, CHP_BTM_PCT_BY_SECTOR["merchant"])
            _add = float(tot) * pct / 100.0 / _MWH_PER_TWH
            btm_by_class[str(klass)] = btm_by_class.get(str(klass), 0.0) + _add
            # No coal measured-share artifact exists, so the bench basis is the
            # same sector share — the two columns stay equal for coal cogens.
            btm_bench_by_class[str(klass)] = (
                btm_bench_by_class.get(str(klass), 0.0) + _add
            )
    if not btm_by_class and not btm_bench_by_class:
        return pd.DataFrame(
            columns=["year", "pass", "klass", "btm_twh", "btm_bench_twh"]
        )
    klasses = sorted(set(btm_by_class) | set(btm_bench_by_class))
    return pd.DataFrame(
        {
            "year": np.int16(year),
            "pass": pass_label,
            "klass": klasses,
            "btm_twh": [btm_by_class.get(k, 0.0) for k in klasses],
            "btm_bench_twh": [btm_bench_by_class.get(k, 0.0) for k in klasses],
        }
    )


_highspy_version = _pipeline_persist.highspy_version


# Packages whose versions can move alternate-optimal vertices (and thus a
# bundle's per-class TWh at an identical objective). Recorded so a byte-identity
# claim is checkable across environments.
_ENVIRONMENT_PACKAGES = _pipeline_persist.ENVIRONMENT_PACKAGES

_environment_block = _pipeline_persist.environment_block


def _malloc_trim() -> bool:
    """Return freed glibc heap to the OS. ``True`` if the trim ran.

    A per-plant ISO-year peaks well over 10 GB inside HiGHS's C++ allocator.
    ``del`` + :func:`gc.collect` free that memory back to glibc, but glibc keeps
    large fragmented arenas rather than unmapping them, so process RSS stays
    elevated into the next year's build even though nothing Python-visible is
    retained. That residual — not the accumulated per-year frames, which measure
    well under 0.1 GB/year — is what pushes a multi-year invocation into the OOM
    killer on a fixed-memory box.

    ``malloc_trim(0)`` releases the free top-of-heap and any fully-free arenas
    back to the kernel. Frees only memory the allocator already considers free,
    so it cannot affect any live object or any solve result. glibc-only; a
    no-op returning ``False`` on musl/macOS or if libc cannot be loaded.
    """
    try:
        import ctypes

        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(ctypes.c_size_t(0))
        return True
    except (OSError, AttributeError):
        return False


def _glibc_arena_gb() -> dict[str, float]:
    """Return glibc allocator accounting in GB, or ``{}`` where unavailable.

    Diagnostic companion to :func:`_malloc_trim` and
    :func:`market_sim.data.cache_control.retained_footprint`. Those two answer
    "how much live *Python* payload is retained"; this answers the complementary
    question the miso-90 attribution could not — of the resident bytes that are
    **not** live Python objects, how many are memory glibc is *holding free*
    versus memory that is genuinely still allocated by C-side code (HiGHS).

    Keys, straight from ``mallinfo2`` (glibc 2.33+):

    * ``arena`` — total non-mmapped bytes obtained from the system.
    * ``in_use`` (``uordblks``) — non-mmapped bytes currently **allocated**. A
      large value with a small ndarray payload means a C++ allocator (HiGHS)
      still owns live memory that Python-side ``del`` never released.
    * ``free_in_arena`` (``fordblks``) — bytes already freed but **retained** by
      glibc rather than returned to the kernel. A large value is allocator
      fragmentation: the fix is arena tuning (``M_ARENA_MAX``/``mallopt``), not
      anything in the model.
    * ``mmapped`` (``hblkhd``) — bytes in mmapped blocks, which glibc returns
      directly on free and ``malloc_trim`` never sees.
    * ``trim_top`` (``keepcost``) — releasable bytes at the top of the heap.

    Read-only accounting: it allocates nothing the solve depends on and can
    never change dispatch. Returns ``{}`` on musl/macOS or pre-2.33 glibc.
    """
    try:
        import ctypes

        class _MallInfo2(ctypes.Structure):
            _fields_ = [
                (name, ctypes.c_size_t)
                for name in (
                    "arena",
                    "ordblks",
                    "smblks",
                    "hblks",
                    "hblkhd",
                    "usmblks",
                    "fsmblks",
                    "uordblks",
                    "fordblks",
                    "keepcost",
                )
            ]

        libc = ctypes.CDLL("libc.so.6")
        libc.mallinfo2.restype = _MallInfo2
        info = libc.mallinfo2()
        gb = 1073741824.0
        return {
            "arena": info.arena / gb,
            "in_use": info.uordblks / gb,
            "free_in_arena": info.fordblks / gb,
            "mmapped": info.hblkhd / gb,
            "trim_top": info.keepcost / gb,
        }
    except (OSError, AttributeError, ValueError):
        return {}


def _proc_mem_kb() -> tuple[int, int]:
    """Return ``(VmRSS, VmHWM)`` in kB from ``/proc/self/status``, or ``(0, 0)``.

    Stdlib-only (no psutil dependency). ``VmHWM`` is the process's peak RSS
    since start, so a year-over-year rise in HWM is the signature of state
    retained across the sequential year loop rather than transient solve
    memory. Returns zeros on any platform without ``/proc``.
    """
    try:
        vals: dict[str, int] = {}
        with open("/proc/self/status", encoding="ascii") as fh:
            for line in fh:
                if line.startswith(("VmRSS:", "VmHWM:")):
                    key, rest = line.split(":", 1)
                    vals[key] = int(rest.split()[0])
        return vals.get("VmRSS", 0), vals.get("VmHWM", 0)
    except OSError:
        return 0, 0


_json_default = _pipeline_persist.json_default
_git_sha = _pipeline_persist.git_sha
_git = _pipeline_persist.git_cmd
_basis_sha = _pipeline_persist.basis_sha


# Paths excluded from the manifest's git state: a run's own outputs (and other
# bundles) are not "model changes" and would just be noise.
_GIT_STATE_EXCLUDE = _pipeline_persist.GIT_STATE_EXCLUDE

_git_state = _pipeline_persist.git_state
_parse_offer_curve_json = _pipeline_persist.parse_offer_curve_json
write_run_config = _pipeline_persist.write_run_config


# ---------------------------------------------------------------------------
# --reuse-solved: opt-in reuse of a prior bundle's per-year solve artifacts
# ---------------------------------------------------------------------------

# solve_and_persist parameters that do NOT change what a year's solve produces
# (destination/provenance plumbing, or handled per-year by plan_reuse_solved).
# Everything else must match the prior bundle's meta-reconstructed kwargs
# exactly for any year to be reused.
_REUSE_KWARG_EXEMPT = frozenset(
    {
        "years",
        "iso",
        "hours",
        "reference",
        "run_dir",
        "note",
        "ablation_of",
        "reuse_solved",
        # Write-only persistence: it is read after both LPs have run and is
        # consumed by nothing downstream, so two runs differing only in this
        # flag have BYTE-IDENTICAL solves and the prior year stays reusable.
        # (Its sibling ``persist_p2_state`` has the same property and is not
        # listed — left alone deliberately, since changing an ARCHIVED-P2 knob's
        # reuse eligibility is another lane's call, not this one's.)
        "persist_p0_commitment",
        # Same property, same reason (caiso-287): its MW-valued sibling is
        # read after both LPs have run and consumed by nothing downstream, so
        # two runs differing only in this flag have BYTE-IDENTICAL solves and
        # the prior year stays reusable.
        "persist_p0_dispatch",
    }
)

_REUSE_WARNING = (
    "Reused years are byte-copies of a prior bundle's solve, NOT fresh "
    "evidence — keeper promotion still requires a full fresh solve of every "
    "year."
)


def _norm_reuse_value(v):
    """Normalize one solve kwarg for reuse comparison across a JSON round-trip.

    The prior side of the comparison comes from ``meta.json`` (tuples became
    lists, frozensets became sorted lists via ``_json_default``, ``None``
    dict entries were dropped by the meta writer), so the live side is
    normalized the same way before equality is tested. ``None``-valued dict
    entries are dropped and an empty dict collapses to ``None`` because both
    sides treat them as "no override".
    """
    if isinstance(v, dict):
        d = {str(k): _norm_reuse_value(x) for k, x in v.items() if x is not None}
        return d or None
    if isinstance(v, (list, tuple)):
        return [_norm_reuse_value(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    if isinstance(v, Path):
        return str(v)
    return v


def _untracked_data_newest_mtime() -> tuple[float, str]:
    """Return (newest mtime, path) over non-git-tracked files under ``data/``.

    Git-tracked data changes are caught by the commit/worktree checks in
    :func:`plan_reuse_solved`; this covers the rest — gitignored raw drops
    and the derived ``data/clean`` store — whose only change signal is the
    filesystem. Returns ``(0.0, "")`` when everything under ``data/`` is
    tracked.
    """
    tracked = set(_git("ls-files", "--", "data").splitlines())
    newest, newest_path = 0.0, ""
    for dirpath, _dirnames, filenames in os.walk(REPO / "data"):
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(REPO).as_posix()
            if rel in tracked:
                continue
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if m > newest:
                newest, newest_path = m, rel
    return newest, newest_path


def plan_reuse_solved(
    prior: Path,
    *,
    iso: str,
    hours: int,
    years: list[int],
    gas_prices: dict[int, float],
    current_kwargs: dict,
    recorded_config_for_year,
) -> "tuple[dict[int, dict], dict]":
    """Decide which requested years may be reused from a prior bundle.

    Returns ``(plan, record)``: ``plan`` maps each reusable year to
    ``{"passes", "cache_key", "scenario_config_sha256"}``; ``record`` is the
    ``meta.json``/``run_config.json`` ``"reuse"`` labeling block (source
    bundle, per-year hashes, refusal reasons, and the not-fresh-evidence
    warning). Any failed check refuses conservatively — the year (or the
    whole bundle) simply solves fresh, with the reason logged and recorded.

    A year is reusable only when ALL of the following hold:

    * the prior bundle's ``meta.json`` kwargs (reconstructed through
      ``replay_keeper.build_kwargs``, the sanctioned recipe channel) equal
      this invocation's solve-affecting kwargs (``_REUSE_KWARG_EXEMPT``
      excluded), and its ``run_config.json`` ``scenario_config`` equals the
      full-field dump of :func:`_recorded_config` for the prior bundle's
      first year — so the per-year effective ``ScenarioConfig`` (and hence
      ``cache_key()``) is identical for every shared year, since per-year
      configs are the same pure function of (kwargs, year, Henry Hub price)
      and the code is pinned by the git checks below;
    * the working tree is CLEAN under ``src/``, ``scripts/`` and ``data/``,
      the prior bundle was solved from a clean tree, and ``git diff`` from
      the prior bundle's recorded commit to HEAD touches nothing under
      ``src/``, ``scripts/`` or ``data/``;
    * no non-git-tracked file under ``data/`` (gitignored raw, derived
      ``data/clean``) has an mtime newer than the prior run's last write
      (the newest file in the prior bundle — its report phase lazily
      re-derives ``data/clean`` caches after ``meta.json`` is stamped, and
      those deterministic re-derivations of git-pinned raw inputs must not
      poison the gate);
    * the installed ``highspy`` version matches the prior bundle's (solver
      upgrades legitimately move alternate-optimal vertices);
    * per year: the year is in the prior bundle, its Henry Hub actual is
      unchanged, and its per-year artifacts (``dispatch/<year>_<pass>``
      files for every recorded pass, ``system.parquet`` rows) exist.

    What the key does NOT cover (documented residual risk, all conservative
    only in the sense that they cannot be detected, not that they refuse):

    * mtime-preserving edits to untracked data (``touch -r`` /
      ``cp --preserve``) and clock skew — the untracked-data gate compares
      file mtimes against the prior run's last bundle write and assumes
      both runs happened on this machine's clock (bundle payload parquets
      are gitignored, so reuse sources are local by construction); a
      concurrent parallel run (rule 13) rewriting a ``data/clean`` cache
      during the prior run's window is likewise invisible — benign, since
      clean caches re-derive deterministically from git-pinned raw data;
    * the Python/numpy/pandas/scipy environment beyond ``highspy`` (only
      the solver version is recorded in bundles);
    * environment variables that are not resolved into the recorded config
      (the recorded env-gated probes ARE covered via the scenario_config
      dump; performance knobs like ``MARKET_SIM_WARMSTART_XYEAR`` are
      basis-neutral by design, see docs/cross-year-warmstart.md).
    """
    import dataclasses

    prior = Path(prior)
    record: dict = {
        "source_bundle": str(prior),
        "requested_years": [int(y) for y in years],
        "reused_years": {},
        "fresh_years": [],
        "refusals": {},
        "warning": _REUSE_WARNING,
    }

    def _refuse_all(reason: str) -> "tuple[dict[int, dict], dict]":
        logger.warning("--reuse-solved: no year reused: %s", reason)
        record["refusals"]["bundle"] = reason
        record["fresh_years"] = [int(y) for y in years]
        return {}, record

    meta_path, rc_path = prior / "meta.json", prior / "run_config.json"
    if not meta_path.exists() or not rc_path.exists():
        return _refuse_all(f"{prior} is missing meta.json/run_config.json")
    try:
        prior_meta = json.loads(meta_path.read_text())
        prior_rc = json.loads(rc_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return _refuse_all(f"unreadable prior bundle metadata: {exc}")
    record["source_timestamp"] = prior_meta.get("timestamp")

    if str(prior_meta.get("iso", "")).upper() != iso.upper():
        return _refuse_all(
            f"prior bundle is {prior_meta.get('iso')!r}, this run is {iso!r}"
        )
    if int(prior_meta.get("hours", -1)) != int(hours):
        return _refuse_all(
            f"prior bundle solved hours={prior_meta.get('hours')}, "
            f"this run wants hours={hours}"
        )
    prior_highs = prior_meta.get("highspy_version", "")
    if prior_highs != _highspy_version():
        return _refuse_all(
            f"highspy version changed (prior {prior_highs!r}, "
            f"current {_highspy_version()!r}) — alternate-optimal vertices "
            "may move; solve fresh"
        )

    # --- solve recipe: kwargs through the sanctioned replay channel --------
    # (deferred: replay_keeper imports this module)
    from scripts import replay_keeper as rk

    try:
        prior_kwargs = rk.build_kwargs(prior_meta)
    except SystemExit as exc:
        return _refuse_all(f"prior meta.json is not kwargs-reconstructable: {exc}")
    sig_params = inspect.signature(solve_and_persist).parameters
    mismatched = []
    for name, p in sig_params.items():
        if name in _REUSE_KWARG_EXEMPT:
            continue
        default = None if p.default is inspect.Parameter.empty else p.default
        cur = _norm_reuse_value(current_kwargs.get(name, default))
        pri = _norm_reuse_value(prior_kwargs.get(name, default))
        if cur != pri:
            mismatched.append(name)
    if mismatched:
        return _refuse_all(
            "solve kwargs differ from the prior bundle: "
            + ", ".join(sorted(mismatched))
        )

    # --- effective per-year ScenarioConfig ---------------------------------
    prior_years = [int(y) for y in prior_meta.get("years", [])]
    if not prior_years:
        return _refuse_all("prior meta.json records no years")
    prior_sc = prior_rc.get("scenario_config")
    if not isinstance(prior_sc, dict):
        return _refuse_all("prior run_config.json has no scenario_config record")

    def _canon(d: dict) -> dict:
        return json.loads(json.dumps(d, sort_keys=True, default=_json_default))

    try:
        probe = _canon(dataclasses.asdict(recorded_config_for_year(prior_years[0])))
    except Exception as exc:  # e.g. config validation under current code
        return _refuse_all(
            f"cannot rebuild the recorded config for year {prior_years[0]}: {exc}"
        )
    prior_sc_canon = _canon(prior_sc)
    if probe != prior_sc_canon:
        diff_keys = sorted(
            k
            for k in set(probe) | set(prior_sc_canon)
            if probe.get(k) != prior_sc_canon.get(k)
        )
        return _refuse_all(
            f"effective ScenarioConfig for year {prior_years[0]} differs from "
            f"the prior bundle's persisted scenario_config: {diff_keys}"
        )

    # --- git state: code + tracked data pinned to the prior solve ----------
    cur_sha = _git("rev-parse", "--short", "HEAD")
    if not cur_sha:
        return _refuse_all("git state unavailable — cannot pin code identity")
    dirty = _git("status", "--porcelain", "--", "src", "scripts", "data")
    if dirty:
        return _refuse_all(
            "working tree is dirty under src/scripts/data — reuse requires a "
            f"clean tree:\n{dirty}"
        )
    prior_git = prior_rc.get("git") or {}
    if prior_git.get("dirty"):
        return _refuse_all(
            "prior bundle was solved from a dirty tree (see its "
            "model_changes.diff) — its code state is not commit-addressable"
        )
    prior_sha = prior_git.get("sha") or prior_meta.get("git_sha") or ""
    record["source_git_sha"] = prior_sha
    if not prior_sha:
        return _refuse_all("prior bundle records no git sha")
    if prior_sha != cur_sha:
        if not _git("rev-parse", "--verify", f"{prior_sha}^{{commit}}"):
            return _refuse_all(
                f"prior bundle's commit {prior_sha} is not resolvable here — "
                "expected for bundles recorded before the 2026-07-22 history "
                "rewrite, which orphaned pre-rewrite SHAs (no mapping was "
                "saved; those bundles are re-solve-only). Refusing is the "
                "gate working correctly — an unresolvable commit cannot "
                "prove src/scripts/data unchanged; see "
                "docs/governance/rule-history.md §6"
            )
        changed = _git(
            "diff", "--name-only", prior_sha, "HEAD", "--", "src", "scripts", "data"
        )
        if changed:
            return _refuse_all(
                f"src/scripts/data changed between the prior bundle's commit "
                f"{prior_sha} and HEAD {cur_sha}: "
                + ", ".join(changed.splitlines()[:8])
                + ("…" if len(changed.splitlines()) > 8 else "")
            )

    # --- untracked/derived data: mtime gate against the prior run's end ----
    # The anchor is the prior run's LAST write into its own bundle, not its
    # meta.json timestamp: the report phase runs after meta/run_config are
    # written and lazily (re)derives data/clean caches, so an artifact the
    # prior run itself produced legitimately postdates its timestamp. Those
    # caches are deterministic re-derivations of git-pinned raw inputs (the
    # diff/status gates above), so they don't invalidate reuse — only a file
    # touched AFTER the prior process finished does.
    try:
        prior_epoch = datetime.fromisoformat(prior_meta["timestamp"]).timestamp()
    except (KeyError, TypeError, ValueError):
        return _refuse_all("prior meta.json has no parseable timestamp")
    for p in prior.rglob("*"):
        if p.is_file():
            try:
                prior_epoch = max(prior_epoch, p.stat().st_mtime)
            except OSError:
                continue
    newest, newest_path = _untracked_data_newest_mtime()
    if newest > prior_epoch:
        return _refuse_all(
            f"untracked/derived data artifact {newest_path} was modified "
            "after the prior run finished — inputs may have changed; "
            "solve fresh"
        )

    # --- per-year artifact + Henry Hub checks ------------------------------
    prior_passes = sorted(prior_meta.get("passes") or [])
    if not prior_passes:
        return _refuse_all("prior meta.json records no solve passes")
    sys_path = prior / "system.parquet"
    if not sys_path.exists():
        return _refuse_all(
            "prior bundle has no system.parquet (payload parquets are "
            "gitignored/pruned — reuse needs the full local bundle)"
        )
    sys_years = set(
        pd.read_parquet(sys_path, columns=["year"])["year"].astype(int).tolist()
    )
    prior_gas = {int(k): v for k, v in (prior_meta.get("gas_prices") or {}).items()}

    plan: dict[int, dict] = {}
    for y in years:
        y = int(y)
        reason = None
        if y not in prior_years:
            reason = "year not solved in the prior bundle"
        elif y not in prior_gas or prior_gas[y] != gas_prices[y]:
            reason = (
                f"Henry Hub actual differs (prior {prior_gas.get(y)!r}, "
                f"current {gas_prices[y]!r})"
            )
        elif y not in sys_years:
            reason = "prior system.parquet has no rows for this year"
        else:
            missing = [
                lb
                for lb in prior_passes
                if not (prior / "dispatch" / f"{y}_{lb}.parquet").exists()
            ]
            if missing:
                reason = f"prior dispatch files missing for passes {missing}"
        if reason:
            record["refusals"][str(y)] = reason
            record["fresh_years"].append(y)
            logger.warning("--reuse-solved: year %d will solve fresh: %s", y, reason)
            continue
        cfg_y = recorded_config_for_year(y)
        try:
            cache_key = cfg_y.cache_key()
        except Exception:  # non-default frozenset fields are not cache_key-able
            cache_key = None
        sc_sha = hashlib.sha256(
            json.dumps(
                dataclasses.asdict(cfg_y), sort_keys=True, default=_json_default
            ).encode()
        ).hexdigest()[:16]
        plan[y] = {
            "passes": prior_passes,
            "cache_key": cache_key,
            "scenario_config_sha256": sc_sha,
        }
        record["reused_years"][str(y)] = dict(plan[y])
    return plan, record


def _load_prior_bundle_tables(prior: Path) -> "dict[str, pd.DataFrame | None]":
    """Load the per-year-sliceable tables of a ``--reuse-solved`` source bundle.

    ``system.parquet`` is required (plan_reuse_solved already checked it);
    the rest are optional — a table the prior bundle lacks would also not
    have been produced by a fresh solve of the identical recipe.
    """
    tables: dict[str, pd.DataFrame | None] = {
        "system": pd.read_parquet(prior / "system.parquet")
    }
    for name in ("storage", "posture", "flows", "storage_as", "btm"):
        p = prior / f"{name}.parquet"
        tables[name] = pd.read_parquet(p) if p.exists() else None
    for name in ("eia930", "eia923", "campd"):
        p = bundle_input_path(prior, name)
        tables[name] = pd.read_parquet(p) if p is not None else None
    return tables


def _copy_reused_year(
    prior: Path,
    run_dir: Path,
    year: int,
    passes: list[str],
    persist_p2_state: bool,
) -> None:
    """Byte-copy one reused year's per-year artifact FILES from the prior bundle.

    Dispatch parquets are copied for every recorded pass (their existence was
    verified by plan_reuse_solved); floors/p2_state are copied when present —
    a fleet with no floor matrix legitimately writes no floors npz.

    The ``hourly/`` sidecars are carried too. They are the *committed* half of a
    bundle (rule 15 ``[R-DASHBOARD]``) and every one of them is a pure function
    of artifacts copied above or of the prior tables the caller splices back in
    — ``class_hourly`` / ``unit_hourly`` / ``network`` aggregate the very
    dispatch frames copied here, ``storage`` aggregates the year's storage rows
    — so byte-copying is exactly what a re-derivation would produce. Without
    this a ``--reuse-solved`` chain (the CLAUDE.md rule 12 per-year invocation
    chain, one fresh year per process) silently produced bundles whose reused
    years carried dispatch but NO class-hour sidecar, so the run registered on
    the dashboard with holes in precisely the years it reused.
    ``system_<year>.parquet`` is regenerated later from the spliced prior slice
    and simply overwrites the copy.
    """
    for label in passes:
        src = prior / "dispatch" / f"{year}_{label}.parquet"
        shutil.copy2(src, run_dir / "dispatch" / src.name)
        floors = prior / "floors" / f"{year}_{label}.npz"
        if floors.exists():
            (run_dir / "floors").mkdir(parents=True, exist_ok=True)
            shutil.copy2(floors, run_dir / "floors" / floors.name)
    prior_hourly = prior / "hourly"
    if prior_hourly.is_dir():
        for src in sorted(prior_hourly.glob(f"*_{year}.parquet")):
            (run_dir / "hourly").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, run_dir / "hourly" / src.name)
    # A prior bundle predating a sidecar (or pruned to dispatch only) carries
    # no copy to take: re-derive the class-hour sidecar from the dispatch
    # frames just copied, so the reused year is never the one with the hole.
    if not (run_dir / "hourly" / f"class_hourly_{year}.parquet").exists():
        _write_class_hourly_sidecar(run_dir, year, passes)
    if not (run_dir / "hourly" / f"class_band_hourly_{year}.parquet").exists():
        _write_class_band_hourly_sidecar(run_dir, year, passes)
    if persist_p2_state:
        p2 = prior / "p2_state" / f"{year}.pkl.gz"
        if p2.exists():
            (run_dir / "p2_state").mkdir(parents=True, exist_ok=True)
            shutil.copy2(p2, run_dir / "p2_state" / p2.name)


def mirror_solve_year_gas_anchors(
    cfg: "ScenarioConfig",
    cfg_year: int,
    hours: int,
    *,
    iso_vintage: bool = False,
    zonal_vintage: bool = False,
) -> "ScenarioConfig":
    """Re-resolve the gas-offer-margin identification point onto ``cfg_year``.

    The MIRROR of ``run_calibration.run_year``'s own two resolution blocks, and
    the ONLY place ``run_config.json``'s copy of them is computed. It exists so
    the recorded config reports the anchor the LP actually solved with rather
    than the frozen-window value it started from (rule 24 ``[R-REGISTRY]``; the
    FFR-2E defect class).

    **CALL IT FUSED TO ``_recorded_config``'s ``return``, never earlier, and do
    not add config-mutating blocks below that return.** ``_gas_series`` — and
    therefore every anchor derived from it — is the series the offer path prices
    against ONLY once the run's whole gas posture is on the config. ``run_year``
    gets that ordering by construction (it sets ``gas_hub_basis_overlay`` at
    ``run_calibration.py:~1960`` and resolves at ``~2572``, and the fleet is not
    built until ``~3791``); the recorded mirror got it wrong, which is the defect
    this function was extracted to close:

        nyiso-230's 2022 arm recorded ``Capital_Hudson 7.0563 $/MMBtu`` while the
        LP priced against ``8.4431`` — a uniform ``-1.3868`` in every zone —
        because the mirror was inlined ~144 lines ABOVE the block that puts
        ``gas_hub_basis_overlay`` on the recorded config. The recorded config was
        internally inconsistent: ``gas_hub_basis_overlay: true`` beside anchors
        that only reproduce at ``overlay=False``. Both of nyiso-230's G-CONF and
        G-PRED screen gates failed on that one line and neither measured the
        mechanism (``docs/RESULT-nyiso231-the-mirror-and-the-2022-rescreen-2026-09-13.md``).

    Fusing the resolution to the ``return`` makes the ordering structural
    instead of positional: a future ``if flag: recorded_cfg = ...`` block lands
    above the return, so it can no longer silently get in front of the mirror.
    The self-consistency invariant is pinned by
    ``tests/unit/scripts/test_recorded_config_gas_anchor_mirror.py``.

    Gating mirrors ``run_year`` exactly — the solve kwarg OR the registered
    ``ScenarioConfig`` field, because ``replay_keeper.py --set`` writes the field
    and never the kwarg (rule 24: a recorded value must not claim a resolution
    the solve did not perform, and a field-armed solve DOES resolve). The two
    flags are alternatives, never stacked (rule 19 ``[R-ONE-MECH]``); ``run_year``
    raises on the combination, so reaching it here is a plumbing bug and raises
    too rather than silently recording one of them.

    Zero free parameters (rule 21 ``[R-DOF]``): only the index the frozen
    derive's own formula is evaluated on moves.
    """
    want_iso = bool(iso_vintage) or bool(
        getattr(cfg, "gas_offer_margin_anchor_vintage", False)
    )
    want_zonal = bool(zonal_vintage) or bool(
        getattr(cfg, "gas_offer_margin_zonal_anchor_vintage", False)
    )
    if want_iso and want_zonal:
        raise SystemExit(
            "gas_offer_margin_anchor_vintage and "
            "gas_offer_margin_zonal_anchor_vintage both re-resolve the SAME "
            "identification point; they are alternatives, never stacked "
            "(rule 19 [R-ONE-MECH]). run_year refuses this combination, so a "
            "recorded config reaching it is a plumbing bug."
        )
    if want_zonal:
        from market_sim.data.fuel.zonal_anchor import zonal_gas_anchors_for_year

        return cfg.with_overrides(
            gas_offer_margin_zonal_anchor_vintage=True,
            gas_offer_margin_anchor_by_zone=zonal_gas_anchors_for_year(
                cfg, int(cfg_year), int(hours)
            ),
        )
    if want_iso:
        from market_sim.data.fuel.trajectories import _gas_series

        return cfg.with_overrides(
            gas_offer_margin_anchor_vintage=True,
            gas_offer_margin_anchor=float(
                np.asarray(
                    _gas_series(cfg, int(cfg_year), int(hours)), dtype=float
                ).mean()
            ),
        )
    return cfg


def solve_and_persist(
    years: list[int],
    iso: str,
    hours: int,
    reference: dict,
    commitment: bool,
    screen_coal: bool,
    run_dir: Path,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    persist_p2_state: bool = False,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    coal_bit_sigmoid: bool = False,
    bit_overrides: dict | None = None,
    coal_econ_srmc_bound: bool = False,
    coal_econ_marginal_hr_bound: bool | None = None,
    committed_band_measured_basis: bool | None = None,
    ercot_offer_hrmult_ep_rebasis: bool | None = None,
    ercot_offer_hrmult_ep_rebasis_bands: "list[str] | None" = None,
    coal_takeorpay_from_data: bool = False,
    coal_mustrun_online_pmin: bool = False,
    coal_sync_srmc_tranche: bool = False,
    ct_intermediate_split: bool = False,
    ct_intermediate_cf_threshold: float | None = None,
    cc_intermediate_split: bool = False,
    cc_intermediate_cf_threshold: float | None = None,
    tranche_startup_amortization: bool = False,
    tranche_startup_measured_runs: bool = False,
    tranche_startup_conditional_runs: bool = False,
    gas_offer_margin: bool = False,
    gas_offer_margin_zonal_anchor: bool = False,
    coal_offer_margin: bool = False,
    cc_committed_offer_margin: bool = False,
    coal_peak_offer_margin: bool = False,
    coal_peak_offer_yearly_level: bool = False,
    coal_perplant_offer_level: bool = False,
    coal_perplant_offer_yearly: bool = False,
    nysdec_peaker_rule_availability: bool = False,
    nyiso_solar_market_generator_basis: bool = False,
    oil_primary_bin_fuel: bool = False,
    st_gas_intermediate: bool = False,
    st_gas_intermediate_cf_threshold: float | None = None,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    storage_vintage_ramp: bool = False,
    strict_demand_profile: bool = False,
    battery_dispatch_adder: float = 0.0,
    as_reserve_withholding: bool = False,
    energy_reserve_coopt: bool = False,
    miso_zonal_reserves: bool = False,
    miso_midwest_subregional_reserves: bool = False,
    miso_reserve_pergen: bool = False,
    miso_commitment_posture: bool = False,
    miso_reserve_online_gated: bool = False,
    miso_measured_reserve_requirements: bool = False,
    miso_south_seam_split: bool = False,
    miso_rdt_tcdc: bool = False,
    miso_zonal_loss_surface: bool = False,
    pjm_zonal_loss_surface: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_ecrs_conservative_deployment: bool = False,
    ercot_nonreleasable_as_withholding: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_ordc_cap_dual_adder: bool = False,
    ercot_ordc_adder_published_anchor: bool = False,
    ercot_ordc_adder_family_counterpart: bool = False,
    ercot_storage_as_product_credit: bool = False,
    gas_hh_monthly_shape: bool = False,
    ercot_as_aware_commitment: bool = False,
    ercot_reserve_supply_cap: bool = False,
    ercot_reserve_supply_cap_from_year: int = 2023,
    ercot_reserve_supply_forward: bool = False,
    pjm_reserve_supply_cap: bool = False,
    pjm_reserve_online_gated: bool = False,
    pjm_reserve_online_rho: float = 1.0,
    pjm_reserve_commitment_scoped: bool = False,
    pjm_reserve_pergen: bool = False,
    pjm_reserve_pergen_sync: bool = False,
    pjm_reserve_pergen_size_split: bool = False,
    pjm_commitment_posture: bool = False,
    measured_ramp_capability: bool = False,
    ercot_as_forward_requirement: bool = False,
    ercot_load_resource_reserve: bool = False,
    ercot_load_resource_reserve_from_year: int = 2023,
    ercot_storage_as_reserve: bool = False,
    ercot_storage_as_reserve_from_year: int = 2025,
    ercot_ecrs_requirement: bool = False,
    ercot_ecrs_requirement_from_year: int = 2023,
    ercot_rtordpa_overlay: bool = False,
    ercot_dam_as_overlay: bool = False,
    ercot_dam_as_overlay_from_year: int = 2024,
    ercot_dam_as_scarcity_threshold: float = 150.0,
    ordc_lolp_params_path: str | None = None,
    as_reserve_formula: bool = False,
    storage_as_commitment: bool = False,
    ercot_storage_as_deployment: bool = False,
    ercot_storage_as_deployment_from_year: int = 2023,
    ercot_storage_as_endogenous: bool = False,
    ercot_storage_as_duration_gate: bool = False,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    pjm_zonal_gas_basis: bool = False,
    miso_zonal_gas_basis: bool = False,
    miso_winter_citygate_daily: bool = False,
    pjm_congestion: bool = False,
    offer_curve_overrides: dict | None = None,
    offer_curve_deltas: dict | None = None,
    curve_smoothing: dict | None = None,
    cc_derate_from_top: bool = False,
    cc_nameplate_summer_derate: bool = False,
    coal_nameplate_summer_derate: bool = False,
    gt_ambient_derate: bool = False,
    gt_ambient_derate_ref_c: float | None = None,
    gt_ambient_derate_slope_cc: float | None = None,
    gt_ambient_derate_slope_ct: float | None = None,
    temp_dependent_derate: bool = False,
    temp_derate_hourly_grain: bool = False,
    temp_derate_mean_anchored: bool = False,
    temp_derate_classes: frozenset[str] | tuple[str, ...] | None = None,
    temp_derate_slope_st_chp: float | None = None,
    temp_derate_slope_ct_chp: float | None = None,
    ercot_offer_surface_conditional: bool = False,
    ercot_offer_surface_midcurve_conditional: bool = False,
    ercot_offer_surface_cleared_share: bool = False,
    ercot_offer_surface_cleared_share_state: bool = False,
    ercot_offer_surface_cleared_share_steam: bool = False,
    ercot_offer_surface_lowcurve: bool = False,
    ercot_offer_surface_lowcurve_floorscoped: bool = False,
    wind_ptc_vintage_offers: bool = False,
    neiso_offer_surface_conditional: bool = False,
    pjm_offer_surface_conditional: bool = False,
    pjm_da_virtual_bids: bool = False,
    pjm_offer_midcurve_conditional: bool = False,
    pjm_offer_midcurve_segments: "tuple[str, ...] | None" = None,
    caiso_offer_surface_measured: bool = False,
    caiso_offer_surface_measured_ungrounded: bool = False,
    caiso_st_gas_committed_measured: bool = False,
    caiso_st_gas_peak_measured: bool = False,
    caiso_ct_peaker_committed_measured: bool = False,
    nyiso_ct_peaker_bands_measured: bool = False,
    nyiso_ct_peaker_committed_measured: bool = False,
    nyiso_st_gas_econ_bands_deleaked: bool = False,
    caiso_offer_surface_conditional: bool = False,
    nearby_fuel_price_zone_donor_guard: bool = False,
    fleet_state_from_eia860: bool = False,
    caiso_citygate_spot_coverage: bool = False,
    ercot_nuclear_unit_availability: bool = False,
    nuclear_unit_availability: bool = False,
    ercot_thermal_dam_availability: bool = False,
    ercot_thermal_dam_availability_hourly: bool = False,
    ercot_thermal_dam_availability_plant: bool = False,
    ercot_wind_zone_shape: bool = False,
    ercot_noncampd_plant_availability: bool = False,
    ercot_storage_capability_measured: bool = False,
    ercot_online_capacity_envelope_measured: bool = False,
    ercot_ordc_only_scarcity: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    hydro_eia930_monthly: bool = False,
    hydro_budget_period_by_instrument: bool = False,
    hydro_forecast_budget: bool = False,
    hydro_year: str = "normal",
    interchange_shaping: bool = False,
    interchange_shaping_export_only: bool = False,
    reference_price_interface: bool = False,
    negative_renewable_offers: bool | None = None,
    caiso_gas_commitment_floor: bool | None = None,
    caiso_gas_floor_frac: float | None = None,
    caiso_ra_mustoffer: bool | None = None,
    caiso_ra_min_load_frac: float | None = None,
    caiso_ra_startup_bridge: bool | None = None,
    caiso_ra_bridge_decommit: bool | None = None,
    ercot_gas_commitment_bridge: bool | None = None,
    carry_operating_mothballs: bool | None = None,
    ercot_gas_bridge_min_load_frac: float | None = None,
    ercot_gas_bridge_startup: bool | None = None,
    ercot_gas_bridge_da_horizon: bool | None = None,
    ercot_gas_bridge_online_hours: bool | None = None,
    ercot_commitment_posture: bool | None = None,
    ercot_commitment_posture_min_load_frac: float | None = None,
    reliability_floor: bool | None = None,
    reliability_floor_plant_exclusions: bool | None = None,
    scarcity_price_overlay: bool | None = None,
    caiso_scarcity_pricing: bool | None = None,
    caiso_lcr_commitment_credit: bool | None = None,
    caiso_solar_deliverability: bool | None = None,
    caiso_solar_deliverability_k: float | None = None,
    caiso_solar_endogenous_spill: bool | None = None,
    caiso_solar_cap_at_delivered: bool | None = None,
    neiso_gas_coldsnap_derate: bool | None = None,
    neiso_coldsnap_derate_dualfuel_unswitched: bool | None = None,
    neiso_oil_burn_budget: bool | None = None,
    neiso_winter_fuel_inventory: bool | None = None,
    neiso_winter_fuel_start_fill_bbl: float | None = None,
    neiso_winter_fuel_mustrun: bool | None = None,
    coal_fuel_inventory: bool | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_perhub_firm_base: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    caiso_reference_price_seam: bool | None = None,
    caiso_per_year_import_caps: bool | None = None,
    caiso_asymmetric_path_ratings: bool | None = None,
    caiso_zonal_loss_surface: bool | None = None,
    capacity_deliverability_limits: bool | None = None,
    unit_outage_lp_capacity_basis: bool | None = None,
    unit_outage_mixed_gas_routing: bool | None = None,
    unit_outage_st_capacity_basis: bool | None = None,
    unit_outage_per_unit_clip: bool | None = None,
    unit_outage_short_windows_gas: bool | None = None,
    unit_outage_window_hour_grain: bool | None = None,
    campd_per_unit_attribution: bool | None = None,
    campd_outage_merit_order_guard: bool | None = None,
    netload_drag_layup_window_mask: bool | None = None,
    netload_drag_merit_allocation: bool | None = None,
    netload_drag_min_run_persistence: bool | None = None,
    vre_curtailment_oversupply_allocation: bool | None = None,
    spp_curtailment_ceiling: bool | None = None,
    spp_curtail_depth_wind: float | None = None,
    cc_winter_capability_basis: bool | None = None,
    ramp_limits: bool | None = None,
    local_capacity_constraints: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_scr_edrp: bool | None = None,
    nyiso_scr_edrp_strike: float | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_import_hub_prices: bool | None = None,
    nyiso_iroquois_winter_spread: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_li_locational_reserve: bool | None = None,
    nyiso_incity_commitment_obligation: bool | None = None,
    nyiso_east_reserve_families: bool | None = None,
    reliability_floor_overrides: dict | None = None,
    nyiso_gas_commitment_bridge: bool | None = None,
    spp_gas_commitment_bridge: bool | None = None,
    soco_gas_st_campaign_commitment: bool | None = None,
    miso_coal_night_floor: bool | None = None,
    nyiso_gas_bridge_cc_min_load_frac: float | None = None,
    nyiso_gas_bridge_st_min_load_frac: float | None = None,
    nyiso_gas_bridge_startup: bool | None = None,
    nyiso_gas_bridge_da_horizon: bool | None = None,
    nyiso_gas_bridge_min_run: bool | None = None,
    nyiso_gas_bridge_plant_exclusions: bool | None = None,
    nyiso_gas_bridge_reserve_duty_exclusions: bool | None = None,
    nyiso_gas_bridge_plant_min_run: bool | None = None,
    nyiso_gas_bridge_online_hours: bool | None = None,
    nyiso_gas_bridge_state_floor_min_run: bool | None = None,
    nyiso_gas_bridge_startup_aware: bool | None = None,
    nyiso_chp_btm_measured: bool | None = None,
    cc_reserve_duty_split: bool | None = None,
    chp_layup_duty_split: bool | None = None,
    chp_layup_duty_curve: bool | None = None,
    egrid_identity_heat_rates: bool | None = None,
    measured_ct_heat_rates: bool | None = None,
    measured_coal_heat_rates: bool | None = None,
    measured_st_heat_rates: bool | None = None,
    egrid_family_heat_rates: bool | None = None,
    egrid_steam_collapse_heat_rates: bool | None = None,
    nyiso_gas_bridge_cc_min_run_hours: float | None = None,
    nyiso_gas_bridge_st_min_run_hours: float | None = None,
    nyiso_spin_reserve_online: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    nyiso_dynamic_reserve_requirements: bool | None = None,
    nyiso_hydro_reserve_eligible: bool | None = None,
    nyiso_scr_edrp_reserve_eligible: bool | None = None,
    neiso_dynamic_reserve_requirements: bool | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    miso_seam_flow_percentile: float | None = None,
    miso_seam_export_limit: bool = False,
    miso_seam_envelope_merit_cap: bool = False,
    miso_seam_envelope_hour_ending_key: bool = False,
    miso_import_sil_measured_envelope: bool = False,
    nyiso_seam_deliverability_envelope: bool = False,
    nyiso_seam_par_attribution: bool = False,
    miso_pjm_border_anchor: bool = False,
    miso_cc_coal_rebalance: bool = False,
    miso_firm_import_floor: bool = False,
    miso_pjm_lmp_import_pricing: bool = False,
    miso_seam_measured_ladder: bool = False,
    pjm_seam_flow_limit: bool = False,
    pjm_seam_flow_percentile: float | None = None,
    pjm_seam_export_limit: bool = False,
    pjm_seam_measured_ladder: bool = False,
    pjm_seam_neighbour_hourly_ladder: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict | None = None,
    ct_netload_drag: bool | None = None,
    pjm_interface_feed_admissibility_gate: bool | None = None,
    gas_offer_margin_anchor_vintage: bool = False,
    gas_offer_margin_zonal_anchor_vintage: bool = False,
    ct_drag_overrides: dict | None = None,
    chp_export_floor_measured: bool = False,
    ercot_gtc_limits_measured: bool = False,
    pjm_measured_interface_limits: bool = False,
    ercot_wtx_curtailment_driver: bool | None = None,
    ercot_wtx_curtail_depth_wind: float | None = None,
    ercot_wtx_curtail_depth_solar: float | None = None,
    mass_cap_enabled: bool = False,
    mass_cap_tons: float | None = None,
    mass_cap_program: str | None = None,
    btm_backfill_year: int | None = None,
    zero_forcing_ablation: bool = False,
    ablation_of: str | None = None,
    reuse_solved: "Path | None" = None,
    note: str = "",
    persist_p0_commitment: bool = False,
    persist_p0_dispatch: bool = False,
) -> Path:
    """Solve every year/pass, write the parquet bundle, return the run dir.

    ``zero_forcing_ablation`` (D-3, CLAUDE.md rule 20): solve the zero-forcing
    ablation twin — every merchant floor/bridge neutralized in ``run_year`` via
    ``ScenarioConfig.as_zero_forcing_ablation`` — and record ``ablation_of`` (the
    base keeper bundle name) at the top of ``run_config.json``.

    ``reuse_solved`` (OPT-IN, ``--reuse-solved``): a prior bundle dir whose
    per-year artifacts are copied instead of re-solved for every year that
    passes :func:`plan_reuse_solved`'s eligibility checks (identical
    effective per-year config, pinned code + data state). Years that fail
    any check solve fresh; the mix is labeled in ``meta.json["reuse"]``.
    Reused years are NOT fresh evidence (see ``_REUSE_WARNING``). Default
    ``None`` keeps behavior byte-identical to a plain fresh run.

    ``persist_p0_commitment`` (OPT-IN, ``--persist-p0-commitment``): also write
    the per-year P0 commitment sidecars (see
    :func:`_write_p0_commitment_sidecar`). WRITE-ONLY and additive-only — at
    the ``False`` default no file is added, no file changes, and the committed
    bundle spec is untouched, so it is a persistence parameter on the
    ``persist_p2_state`` precedent rather than a ``ScenarioConfig`` field
    (CLAUDE.md rule 24 ``[R-REGISTRY]`` scopes to tunables that can change a
    solve; this one is read after both LPs have already run).

    ``persist_p0_dispatch`` (OPT-IN, ``--persist-p0-dispatch``): also write the
    per-year P0 dispatch / dual sidecars (see
    :func:`_write_p0_dispatch_sidecar`) — the MW-valued sibling of
    ``persist_p0_commitment``, with the same WRITE-ONLY and additive-only
    property and the same rationale for not being a ``ScenarioConfig`` field.
    """
    # Snapshot every solve-affecting keyword argument BEFORE any other local
    # is bound (locals() here is exactly the parameter set): plan_reuse_solved
    # compares it against the prior bundle's meta-reconstructed kwargs
    # (replay_keeper.build_kwargs, the sanctioned recipe channel).
    _solve_kwargs_snapshot = {
        k: v for k, v in locals().items() if k not in _REUSE_KWARG_EXEMPT
    }
    # Container preflight BEFORE the first loader allocates anything: binding
    # cgroup ceiling, swap provisioning, solve-profile pins. Once per process;
    # never raises; see CONTAINER_PREFLIGHT_ENABLED.
    if CONTAINER_PREFLIGHT_ENABLED:
        ensure_solve_container(log=logger)
    # caiso-224: arm/disarm the FSNO sub-zonal partition BEFORE this
    # orchestrator's own get_iso_config / load_demand pre-loads. run_year sets
    # the same context from its resolved config, but the demand threaded into
    # it below is loaded HERE — an unset context at this point is exactly the
    # caiso-80/nyiso-87 single-demand-load defect class, and the arm's first
    # launch died on it (8-zone fleet vs 7-zone threaded demand,
    # "axis 0 index 7 exceeds matrix dimension 7"). Read from the generic
    # prb_overrides channel, the same way caiso_endogenous_wecc_node is below.
    from market_sim.config.topology_variant import set_caiso_fsno_partition

    set_caiso_fsno_partition(
        iso == "CAISO"
        and bool((prb_overrides or {}).get("caiso_fsno_subzonal_topology", False))
    )
    iso_config = get_iso_config(iso)
    # caiso-110: the endogenous WECC-West node keeps the SINGLE WECC_import zone
    # (no per-hub split — run_year does not split it either), so this caller's
    # zone_names / report frames must match. Read from the generic prb_overrides
    # channel (the same way run_year receives it).
    _endog_wecc = iso == "CAISO" and bool(
        (prb_overrides or {}).get("caiso_endogenous_wecc_node", False)
    )
    if priced_interchange:
        # Interchange served by the priced import/export node (external zone
        # + import tranches + export sinks) instead of the measured schedule;
        # the bundle's zone set and demand frames follow the extended
        # topology so they match run_year's solve.
        iso_config = extend_with_import_node(iso_config)
        if (
            (caiso_per_hub_intertie or caiso_reference_price_seam)
            and iso == "CAISO"
            and not _endog_wecc
        ):
            # Split WECC_import into the two per-hub corridors so this caller's
            # zone_names / must-run / report frames match run_year's solve
            # (run_year applies the same split idempotently). Both the measured
            # per-hub path and the forward reference-price seam ride the corridor
            # split. See transmission.split_caiso_import_node_per_hub.
            from market_sim.model.transmission import split_caiso_import_node_per_hub

            iso_config = split_caiso_import_node_per_hub(iso_config)
        if miso_south_seam_split and iso == "MISO":
            # Re-home the South seam onto its own external zone so this
            # caller's zone_names / report frames match run_year's solve
            # (run_year applies the same split via apply_interchange_topology).
            from market_sim.model.transmission import split_miso_south_external_node

            iso_config = split_miso_south_external_node(iso_config)
    zone_names = iso_config.zone_names
    (run_dir / "dispatch").mkdir(parents=True, exist_ok=True)

    # Per-plant CAMPD net + EIA-923 benchmarks are built for any ISO whose
    # CAMPD CEMS state extracts are present (ERCOT = TX; PJM = PA/NJ/MD/DE/IL/IN
    # ...). The class map keying the CAMPD/EIA-923 backfill comes from the
    # curated ERCOT bin sheet for ERCOT and from the per-plant EIA-860 fleet's
    # plant_group for every other ISO. BTM CHP (host-steam split) stays
    # ERCOT-only. ISOs with no CAMPD coverage keep the energy-only bundle
    # (dispatch + system prices + EIA-930). ERCOT is unchanged.
    is_ercot = iso == "ERCOT"
    has_campd = bool(campd.states_for_iso(iso))
    generation = load_monthly_generation()
    parasitic_factors = _parasitic_factor_map()
    # ERCOT's plant->group map is the curated, year-independent bin sheet; the
    # per-plant ISOs rebuild it per year inside the loop so the CAMPD backfill
    # buckets a plant with the year's own EIA-860 CHP vintage (see below).
    group_by_code: dict[int, str] = {}
    if is_ercot:
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins

        _bins = load_campd_bins(ScenarioConfig().campd_bins_path)
        group_by_code = dict(zip(_bins["Plant_Code"].astype(int), _bins["Plant_Group"]))
    system_frames, eia930_frames, eia923_frames, btm_frames = [], [], [], []
    campd_frames: list[pd.DataFrame] = []
    storage_frames: list[pd.DataFrame] = []
    posture_frames: list[pd.DataFrame] = []
    flows_frames: list[pd.DataFrame] = []
    storage_as_frames: list[pd.DataFrame] = []
    # Henry Hub actuals for every requested year, computed up front so the
    # per-year recorded config (and the --reuse-solved eligibility check) can
    # be built before the solve loop. Same values the loop used to compute
    # per iteration; _henry_hub_actual is a pure lookup on ``reference``.
    gas_prices: dict[int, float] = {
        year: _henry_hub_actual(reference, year) for year in years
    }
    passes_seen: set[str] = set()
    # First year's pristine backcast_config, retained for the meta block below
    # so it doesn't rebuild the same config (with the same args) several times.
    first_year_cfg = None

    # Single-element holder carrying the prior year's optimal basis across the
    # sequential year loop for cross-year warm-start. Consumed only when
    # MARKET_SIM_WARMSTART_XYEAR!=0 (the calibration CLI sets it ON by default;
    # main() resolves the gate before this call, replay/probe callers leave the
    # global default OFF). Basis-neutral either way — see docs/cross-year-
    # warmstart.md. Years must run chronologically for the basis to line up.
    xyear_cache: list = []

    def _recorded_config(cfg_year: int) -> "ScenarioConfig":
        """Rebuild the as-solved (recorded) config for one backcast year.

        The rule-25 reproducibility record: ``backcast_config`` for
        ``cfg_year`` WITH the same overrides + deltas applied that
        ``run_year`` applies, so ``run_config.json``'s ``scenario_config``
        (built for ``years[0]``) records the exact merged config the LP
        solved against (e.g. ``offer_curve_by_group`` is the merged curve,
        not the bare defaults). ``--reuse-solved`` also calls this per
        candidate year: the full-field dump is the reuse-eligibility config
        comparison against the prior bundle's persisted ``scenario_config``,
        and ``cache_key()`` of the result is the per-year config hash
        recorded for reused years (see :func:`plan_reuse_solved`).
        """
        cfg_gas_price = (
            gas_prices[cfg_year]
            if cfg_year in gas_prices
            else _henry_hub_actual(reference, cfg_year)
        )
        recorded_cfg = backcast_config(
            cfg_year,
            iso,
            hours,
            cfg_gas_price,
            commitment_screen_coal=screen_coal,
            coal_prb_passthrough=coal_prb_passthrough,
            outage_source=outage_source,
            coal_mustrun_per_plant=coal_mustrun_per_plant,
            retiree_cems_cap=retiree_cems_cap,
            ct_mustrun_per_plant=ct_mustrun_per_plant,
            ct_mustrun_floor_frac=ct_mustrun_floor_frac,
            coal_drop_pof=coal_drop_pof,
            offer_curve_overrides=offer_curve_overrides,
            offer_curve_deltas=offer_curve_deltas,
            ercot_offer_surface_conditional=ercot_offer_surface_conditional,
            ercot_offer_surface_midcurve_conditional=(
                ercot_offer_surface_midcurve_conditional
            ),
            neiso_offer_surface_conditional=neiso_offer_surface_conditional,
            pjm_offer_surface_conditional=pjm_offer_surface_conditional,
            pjm_da_virtual_bids=pjm_da_virtual_bids,
            pjm_offer_midcurve_conditional=pjm_offer_midcurve_conditional,
            caiso_offer_surface_measured=caiso_offer_surface_measured,
            caiso_offer_surface_measured_ungrounded=(
                caiso_offer_surface_measured_ungrounded
            ),
            caiso_st_gas_committed_measured=caiso_st_gas_committed_measured,
            caiso_st_gas_peak_measured=caiso_st_gas_peak_measured,
            caiso_ct_peaker_committed_measured=caiso_ct_peaker_committed_measured,
            nyiso_ct_peaker_bands_measured=nyiso_ct_peaker_bands_measured,
            nyiso_ct_peaker_committed_measured=nyiso_ct_peaker_committed_measured,
            nyiso_st_gas_econ_bands_deleaked=nyiso_st_gas_econ_bands_deleaked,
            caiso_offer_surface_conditional=caiso_offer_surface_conditional,
            nearby_fuel_price_zone_donor_guard=nearby_fuel_price_zone_donor_guard,
            fleet_state_from_eia860=fleet_state_from_eia860,
            caiso_citygate_spot_coverage=caiso_citygate_spot_coverage,
        )
        if pjm_offer_midcurve_segments is not None:
            # Meta-writer mirror of run_year's with_overrides (rule 25): the
            # segment scope must land in scenario_config exactly as solved.
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_offer_midcurve_segments=tuple(pjm_offer_midcurve_segments)
            )
        if ercot_offer_surface_cleared_share:
            # Meta-writer mirror of run_year's with_overrides (rule 25): the
            # ERCOT-72 cleared-share boundary flag must land in scenario_config
            # exactly as the LP solved with it.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_surface_cleared_share=True
            )
        if ercot_offer_surface_cleared_share_state:
            # Meta-writer mirror (rule 25): the ERCOT-73 commitment-loading
            # state flag must land in scenario_config exactly as solved.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_surface_cleared_share_state=True
            )
        if ercot_offer_surface_cleared_share_steam:
            # Meta-writer mirror (rule 25): the ERCOT-77 steam-cliff extension
            # flag must land in scenario_config exactly as solved.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_surface_cleared_share_steam=True
            )
        if ercot_offer_surface_lowcurve:
            # Meta-writer mirror of run_year's with_overrides (rule 25): the LOW-leg
            # flag must land in scenario_config exactly as the LP solved with it.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_surface_lowcurve=True
            )
        if ercot_offer_surface_lowcurve_floorscoped:
            # Same rule-25 mirror for the ERCOT-64 floor-scoped LSL markdown.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_surface_lowcurve_floorscoped=True
            )
        if wind_ptc_vintage_offers:
            # Same rule-25 mirror for the ERCOT-65 PTC vintage scoping.
            recorded_cfg = recorded_cfg.with_overrides(wind_ptc_vintage_offers=True)
        # Coal sigmoid flags mirror run_year exactly — run_config.json must
        # record the same enables/params the LP solved with (the prb sigmoid +
        # tiered flags, outage_source, coal_drop_pof, the per-plant must-run and
        # screen flags used to be skipped here, so scenario_config under-reported
        # what the LP actually solved — e.g. coal_drop_pof dumped False while the
        # run used True).
        recorded_cfg = recorded_cfg.with_overrides(
            coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,
            coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,
        )
        if prb_overrides:
            recorded_cfg = recorded_cfg.with_overrides(
                **{k: v for k, v in prb_overrides.items() if v is not None}
            )
        if coal_bit_sigmoid:
            recorded_cfg = recorded_cfg.with_overrides(
                coal_bit_passthrough_sigmoid=True
            )
        if bit_overrides:
            recorded_cfg = recorded_cfg.with_overrides(
                **{k: v for k, v in bit_overrides.items() if v is not None}
            )
        if coal_econ_srmc_bound:
            recorded_cfg = recorded_cfg.with_overrides(coal_econ_srmc_bound=True)
        # Mirror run_year's marginal-HR floor EXACTLY — bool AND curve. Recording
        # only the bool left run_config.json's offer_curve_by_group showing the
        # PRE-floor band (ERCOT COAL_PRB.econ_low 0.400) while the LP solved on
        # 0.886, so a floor-on and a floor-off bundle recorded identical curves
        # and a verifier could not tell them apart from run_config alone
        # (rule 25 — the registry must record what was solved). Tri-state
        # resolution matches run_year: None keeps the per-ISO backcast_config
        # default, True/False force it.
        _rec_marginal_hr_on = (
            bool(recorded_cfg.coal_econ_marginal_hr_bound)
            if coal_econ_marginal_hr_bound is None
            else bool(coal_econ_marginal_hr_bound)
        )
        if _rec_marginal_hr_on:
            from market_sim.data.coal import apply_coal_econ_marginal_hr_floor

            _rec_curve, _ = apply_coal_econ_marginal_hr_floor(
                recorded_cfg.offer_curve_by_group, iso
            )
            recorded_cfg = recorded_cfg.with_overrides(
                coal_econ_marginal_hr_bound=True, offer_curve_by_group=_rec_curve
            )
        elif recorded_cfg.coal_econ_marginal_hr_bound:
            recorded_cfg = recorded_cfg.with_overrides(
                coal_econ_marginal_hr_bound=False
            )
        # Mirror run_year's Route A REPLACE committed-band measured basis
        # EXACTLY — bool AND curve — for the same reason the floor above does:
        # recording only the bool would leave run_config.json showing the
        # REGISTERED committed multipliers while the LP solved on the measured
        # ones, so an armed and a control bundle would record identical curves
        # (rule 25 — the registry records what was solved). Half (b) needs no
        # mirror: it reads the same recorded boolean.
        _rec_committed_basis_on = (
            bool(recorded_cfg.committed_band_measured_basis)
            if committed_band_measured_basis is None
            else bool(committed_band_measured_basis)
        )
        if _rec_committed_basis_on:
            from market_sim.data.offer_curves import (
                apply_committed_band_measured_basis,
            )

            _rec_cb_curve, _ = apply_committed_band_measured_basis(
                recorded_cfg.offer_curve_by_group, iso
            )
            recorded_cfg = recorded_cfg.with_overrides(
                committed_band_measured_basis=True,
                offer_curve_by_group=_rec_cb_curve,
            )
        elif recorded_cfg.committed_band_measured_basis:
            recorded_cfg = recorded_cfg.with_overrides(
                committed_band_measured_basis=False
            )
        # Mirror run_year's ERCOT-118 EP rebasis EXACTLY — bool AND curve AND
        # band scope (ERCOT-119), per year (the rebased tables are per
        # delivery year), with the same tri-state resolution. Recording only
        # the bool would leave run_config.json showing the pooled HH-0.50
        # bands while the LP solved on the rebased ones (rule 25 — the
        # ercot-115 recording-gap lesson); recording the scope without the
        # scoped curve would be the same gap one level down.
        _rec_ep_rebasis_on = (
            bool(recorded_cfg.ercot_offer_hrmult_ep_rebasis)
            if ercot_offer_hrmult_ep_rebasis is None
            else bool(ercot_offer_hrmult_ep_rebasis)
        )
        _rec_ep_bands = (
            recorded_cfg.ercot_offer_hrmult_ep_rebasis_bands
            if ercot_offer_hrmult_ep_rebasis_bands is None
            else list(ercot_offer_hrmult_ep_rebasis_bands)
        )
        if _rec_ep_rebasis_on and iso.upper() == "ERCOT":
            from market_sim.data.offer_curves import (
                apply_ercot_dam_hrmult_ep_rebasis,
            )

            _rec_ep_curve, _, _ = apply_ercot_dam_hrmult_ep_rebasis(
                recorded_cfg.offer_curve_by_group,
                cfg_year,
                offer_curve_deltas,
                bands=_rec_ep_bands,
            )
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_hrmult_ep_rebasis=True,
                ercot_offer_hrmult_ep_rebasis_bands=_rec_ep_bands,
                offer_curve_by_group=_rec_ep_curve,
            )
        elif recorded_cfg.ercot_offer_hrmult_ep_rebasis:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_offer_hrmult_ep_rebasis=False
            )
        if plant_tranche_config:
            recorded_cfg = recorded_cfg.with_overrides(
                plant_tranche_config_path=plant_tranche_config
            )
        if storage_daily_cycling:
            recorded_cfg = recorded_cfg.with_overrides(storage_daily_cycling=True)
        if storage_vintage_ramp:
            recorded_cfg = recorded_cfg.with_overrides(storage_vintage_ramp=True)
        if strict_demand_profile:
            recorded_cfg = recorded_cfg.with_overrides(strict_demand_profile=True)
        if as_reserve_withholding:
            recorded_cfg = recorded_cfg.with_overrides(as_reserve_withholding=True)
        if energy_reserve_coopt:
            recorded_cfg = recorded_cfg.with_overrides(energy_reserve_coopt=True)
        if miso_zonal_reserves:
            recorded_cfg = recorded_cfg.with_overrides(miso_zonal_reserves=True)
        if miso_midwest_subregional_reserves:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_midwest_subregional_reserves=True
            )
        if miso_reserve_pergen:
            recorded_cfg = recorded_cfg.with_overrides(miso_reserve_pergen=True)
        if miso_commitment_posture:
            recorded_cfg = recorded_cfg.with_overrides(miso_commitment_posture=True)
        if miso_reserve_online_gated:
            recorded_cfg = recorded_cfg.with_overrides(miso_reserve_online_gated=True)
        if miso_measured_reserve_requirements:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_measured_reserve_requirements=True
            )
        if miso_south_seam_split:
            recorded_cfg = recorded_cfg.with_overrides(miso_south_seam_split=True)
        if miso_rdt_tcdc:
            recorded_cfg = recorded_cfg.with_overrides(miso_rdt_tcdc=True)
        if miso_zonal_loss_surface:
            recorded_cfg = recorded_cfg.with_overrides(miso_zonal_loss_surface=True)
        if pjm_zonal_loss_surface:
            recorded_cfg = recorded_cfg.with_overrides(pjm_zonal_loss_surface=True)
        if pjm_reserve_supply_cap:
            recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_supply_cap=True)
        if pjm_reserve_pergen:
            recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_pergen=True)
        if pjm_reserve_pergen_sync:
            recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_pergen_sync=True)
        if pjm_reserve_pergen_size_split:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_reserve_pergen_size_split=True
            )
        if pjm_commitment_posture:
            recorded_cfg = recorded_cfg.with_overrides(pjm_commitment_posture=True)
        if measured_ramp_capability:
            recorded_cfg = recorded_cfg.with_overrides(measured_ramp_capability=True)
        if pjm_reserve_online_gated:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_reserve_online_gated=True,
                pjm_reserve_online_rho=pjm_reserve_online_rho,
            )
        if pjm_reserve_commitment_scoped:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_reserve_commitment_scoped=True
            )
        if ercot_multiproduct_as_coopt:
            recorded_cfg = recorded_cfg.with_overrides(ercot_multiproduct_as_coopt=True)
        if ercot_ecrs_conservative_deployment:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_ecrs_conservative_deployment=True
            )
        if ercot_nonreleasable_as_withholding:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_nonreleasable_as_withholding=True
            )
        if ercot_ordc_total_reserve:
            recorded_cfg = recorded_cfg.with_overrides(ercot_ordc_total_reserve=True)
        if ercot_storage_as_product_credit:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_storage_as_product_credit=True
            )
        if gas_hh_monthly_shape:
            recorded_cfg = recorded_cfg.with_overrides(gas_hh_monthly_shape=True)
        if ercot_as_aware_commitment:
            recorded_cfg = recorded_cfg.with_overrides(ercot_as_aware_commitment=True)
        if ercot_reserve_supply_cap:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_reserve_supply_cap=True,
                ercot_reserve_supply_cap_from_year=ercot_reserve_supply_cap_from_year,
            )
        if ercot_reserve_supply_forward:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_reserve_supply_forward=True
            )
        if ercot_as_forward_requirement:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_as_forward_requirement=True
            )
        if ercot_load_resource_reserve:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_load_resource_reserve=True,
                ercot_load_resource_reserve_from_year=int(
                    ercot_load_resource_reserve_from_year
                ),
            )
        if ercot_storage_as_reserve:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_storage_as_reserve=True,
                ercot_storage_as_reserve_from_year=int(
                    ercot_storage_as_reserve_from_year
                ),
            )
        if ercot_ecrs_requirement:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_ecrs_requirement=True,
                ercot_ecrs_requirement_from_year=int(ercot_ecrs_requirement_from_year),
            )
        if as_reserve_formula:
            recorded_cfg = recorded_cfg.with_overrides(as_reserve_formula=True)
        if storage_as_commitment:
            recorded_cfg = recorded_cfg.with_overrides(storage_as_commitment=True)
        if ercot_storage_as_deployment:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_storage_as_deployment=True,
                ercot_storage_as_deployment_from_year=int(
                    ercot_storage_as_deployment_from_year
                ),
            )
        if ercot_storage_as_endogenous:
            recorded_cfg = recorded_cfg.with_overrides(ercot_storage_as_endogenous=True)
        if ercot_storage_as_duration_gate:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_storage_as_duration_gate=True
            )
        # Mirror run_year's effective adder resolution (caiso-100 discovery,
        # rule 24): a prb-carried adder was already applied above and governs;
        # otherwise CAISO's $5 fallback is what the LP actually solves with —
        # it was silently recorded as 0.0 before this fix.
        _recorded_adder = battery_dispatch_adder
        if (prb_overrides or {}).get("battery_dispatch_adder") is not None:
            _recorded_adder = None  # prb channel already recorded above
        elif not _recorded_adder and iso.upper() == "CAISO":
            _recorded_adder = 5.0
        if _recorded_adder:
            recorded_cfg = recorded_cfg.with_overrides(
                battery_dispatch_adder=_recorded_adder
            )
        if gas_offer_curve:
            recorded_cfg = recorded_cfg.with_overrides(gas_offer_curve=True)
        if gas_monthly_actuals:
            recorded_cfg = recorded_cfg.with_overrides(gas_monthly_actuals=True)
        if pjm_zonal_gas_basis:
            recorded_cfg = recorded_cfg.with_overrides(pjm_zonal_gas_basis=True)
        if miso_zonal_gas_basis:
            recorded_cfg = recorded_cfg.with_overrides(miso_zonal_gas_basis=True)
        if miso_winter_citygate_daily:
            recorded_cfg = recorded_cfg.with_overrides(miso_winter_citygate_daily=True)
        if pjm_congestion:
            recorded_cfg = recorded_cfg.with_overrides(pjm_congestion=True)
        if curve_smoothing:
            recorded_cfg = recorded_cfg.with_overrides(
                **{k: v for k, v in curve_smoothing.items() if v is not None}
            )
        if cc_derate_from_top or iso.upper() == "CAISO":
            # Meta-writer audit fix (Stage 7): run_year's condition also defaults
            # this on for CAISO regardless of the flag (narrow per-plant peaking
            # bands crush the committed floor without it) — recorded_cfg dropped
            # the ISO branch, so a CAISO run's scenario_config under-reported
            # cc_outage_derate_from_top as False when the LP actually solved True.
            recorded_cfg = recorded_cfg.with_overrides(cc_outage_derate_from_top=True)
        if cc_nameplate_summer_derate:
            # Meta-writer audit fix (Stage 7): mirrors run_year; previously
            # entirely absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(cc_nameplate_summer_derate=True)
        if coal_nameplate_summer_derate:
            # Coal net-summer derate: mirror cc_nameplate_summer_derate so the
            # recorded scenario_config reflects the LP that actually solved.
            recorded_cfg = recorded_cfg.with_overrides(
                coal_nameplate_summer_derate=True
            )
        if gt_ambient_derate:
            # Mirror run_year so run_config.json records the GT ambient-derate knobs
            # (rule 25: every solve-changing tunable appears in the recorded config).
            _amb_rec = {"gt_ambient_derate": True}
            if gt_ambient_derate_ref_c is not None:
                _amb_rec["gt_ambient_derate_ref_c"] = float(gt_ambient_derate_ref_c)
            if gt_ambient_derate_slope_cc is not None:
                _amb_rec["gt_ambient_derate_slope_cc"] = float(
                    gt_ambient_derate_slope_cc
                )
            if gt_ambient_derate_slope_ct is not None:
                _amb_rec["gt_ambient_derate_slope_ct"] = float(
                    gt_ambient_derate_slope_ct
                )
            recorded_cfg = recorded_cfg.with_overrides(**_amb_rec)
        if temp_dependent_derate:
            # Mirror run_year so run_config.json records the switch (rule 25). The
            # per-class slopes/reference temps live in ScenarioConfig defaults, so
            # recording the boolean captures the full solve-changing configuration
            # EXCEPT where a leg overrides them — those are recorded explicitly
            # below (rule 24 [R-REGISTRY]: no off-registry tuning channel).
            _td_rec: dict = {"temp_dependent_derate": True}
            if temp_derate_hourly_grain:
                _td_rec["temp_derate_hourly_grain"] = True
            if temp_derate_mean_anchored:
                _td_rec["temp_derate_mean_anchored"] = True
            if temp_derate_classes:
                _td_rec["temp_derate_classes"] = frozenset(temp_derate_classes)
            if temp_derate_slope_st_chp is not None:
                _td_rec["temp_derate_slope_st_chp"] = float(temp_derate_slope_st_chp)
            if temp_derate_slope_ct_chp is not None:
                _td_rec["temp_derate_slope_ct_chp"] = float(temp_derate_slope_ct_chp)
            recorded_cfg = recorded_cfg.with_overrides(**_td_rec)
        if coal_mustrun_online_pmin:
            # Meta-writer audit fix (Stage 7): mirrors run_year; previously
            # entirely absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(coal_mustrun_online_pmin=True)
        if coal_sync_srmc_tranche:
            # Meta-writer audit fix (Stage 7): mirrors run_year; previously
            # entirely absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(coal_sync_srmc_tranche=True)
        if gas_st_netload_drag:
            # Meta-writer audit fix (Stage 7): mirrors run_year's
            # config.with_overrides(gas_st_netload_drag=True, **(gas_st_drag_overrides
            # or {})); both the flag and its coefficient-override companion were
            # previously absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(
                gas_st_netload_drag=True, **(gas_st_drag_overrides or {})
            )
        if ordc_lolp_params_path:
            # Meta-writer audit fix (Stage 7): mirrors run_year; previously
            # entirely absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(
                ordc_lolp_params_path=str(ordc_lolp_params_path)
            )
        if ct_netload_drag and ct_drag_overrides:
            # Meta-writer audit fix (Stage 7): mirrors run_year's companion
            # ct_drag_overrides application (dynamic field names, e.g.
            # ct_drag_slope_per_gw) — previously absent from recorded_cfg, so a
            # tuned drag curve solved with different coefficients than the
            # defaults recorded_cfg showed.
            recorded_cfg = recorded_cfg.with_overrides(**ct_drag_overrides)
        if coal_lignite_mustrun is not None or coal_prb_mustrun is not None:
            # Meta-writer audit fix (Stage 7): run_year passes these positionally
            # into backcast_config (-> coal_lignite_mustrun_override /
            # coal_prb_mustrun_override), but the recorded_cfg reconstruction's
            # own backcast_config(...) call above never received them —
            # previously entirely absent from recorded_cfg.
            recorded_cfg = recorded_cfg.with_overrides(
                coal_lignite_mustrun_override=coal_lignite_mustrun,
                coal_prb_mustrun_override=coal_prb_mustrun,
            )
        if ercot_nuclear_unit_availability:
            # Mirror run_year's with_overrides so run_config.json records the
            # window-grain nuclear overlay the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_nuclear_unit_availability=True
            )
        if hydro_budget_period_by_instrument:
            # Mirror run_year's with_overrides so run_config.json records the
            # instrument-derived hydro budget periods the LP solved with
            # (nyiso-220). Without this the recorded config says False while the
            # LP carried the shortened-period rows — a rule 24 [R-REGISTRY]
            # reproducibility gap, caught during the nyiso-220 screen.
            recorded_cfg = recorded_cfg.with_overrides(
                hydro_budget_period_by_instrument=True
            )
        if nuclear_unit_availability:
            # Mirror run_year's with_overrides so run_config.json records the
            # ISO-generic window-grain nuclear overlay the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(nuclear_unit_availability=True)
        if ercot_thermal_dam_availability:
            # Mirror run_year's with_overrides so run_config.json records the
            # measured thermal class-day availability the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_thermal_dam_availability=True
            )
        if ercot_thermal_dam_availability_plant:
            # Mirror run_year's with_overrides so run_config.json records the
            # ERCOT-97 plant grain the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_thermal_dam_availability_plant=True
            )
        if ercot_wind_zone_shape:
            # Mirror run_year's with_overrides so run_config.json records the
            # ERCOT-113 per-zone wind SHAPE the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(ercot_wind_zone_shape=True)
        if ercot_thermal_dam_availability_hourly:
            # Mirror run_year's with_overrides so run_config.json records the
            # ERCOT-96 class-HOUR grain switch the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_thermal_dam_availability_hourly=True
            )
        if ercot_noncampd_plant_availability:
            # Mirror run_year's with_overrides so run_config.json records the
            # measured CAMPD-blind per-plant availability the LP solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_noncampd_plant_availability=True
            )
        if ercot_storage_capability_measured:
            # Mirror run_year's with_overrides so run_config.json records the
            # measured storage-capability re-basis the LP solved with (ERCOT-66).
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_storage_capability_measured=True
            )
        if ercot_online_capacity_envelope_measured:
            # Mirror run_year so run_config.json records the measured-fleet-basis
            # envelope the LP solved with (ercot57 joint round).
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_online_capacity_envelope_measured=True
            )
        if ercot_ordc_only_scarcity:
            # Mirror run_year so run_config.json records the ORDC-only product-
            # ladder design the LP solved with (ercot57 joint round).
            recorded_cfg = recorded_cfg.with_overrides(ercot_ordc_only_scarcity=True)
        if interchange_shaping:
            recorded_cfg = recorded_cfg.with_overrides(interchange_shaping=True)
        if interchange_shaping_export_only:
            recorded_cfg = recorded_cfg.with_overrides(
                interchange_shaping=True, interchange_shaping_export_only=True
            )
        if reference_price_interface:
            recorded_cfg = recorded_cfg.with_overrides(reference_price_interface=True)
        # Tri-state floor / negative-offer overrides — mirror run_year so
        # run_config.json records what the LP solved with (None = the per-ISO base
        # default baked in backcast_config: CAISO floor+negative ON at 0.80).
        if negative_renewable_offers is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                negative_renewable_offers=negative_renewable_offers
            )
        if caiso_gas_commitment_floor is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_gas_commitment_floor=caiso_gas_commitment_floor
            )
        if caiso_gas_floor_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_gas_floor_frac=caiso_gas_floor_frac
            )
        if caiso_ra_mustoffer is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_ra_mustoffer=caiso_ra_mustoffer
            )
        if caiso_ra_min_load_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_ra_min_load_frac=caiso_ra_min_load_frac
            )
        if caiso_ra_startup_bridge is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_ra_startup_bridge=caiso_ra_startup_bridge
            )
        if caiso_ra_bridge_decommit is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_ra_bridge_decommit=caiso_ra_bridge_decommit
            )
        if ercot_gas_commitment_bridge is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_gas_commitment_bridge=ercot_gas_commitment_bridge
            )
        if ercot_commitment_posture is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_commitment_posture=ercot_commitment_posture
            )
        if ercot_commitment_posture_min_load_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_commitment_posture_min_load_frac=(
                    ercot_commitment_posture_min_load_frac
                )
            )
        if carry_operating_mothballs is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                carry_operating_mothballs=carry_operating_mothballs
            )
        if ercot_gas_bridge_min_load_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_gas_bridge_min_load_frac=ercot_gas_bridge_min_load_frac
            )
        if ercot_gas_bridge_startup is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_gas_bridge_startup=ercot_gas_bridge_startup
            )
        if ercot_gas_bridge_da_horizon is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_gas_bridge_da_horizon=ercot_gas_bridge_da_horizon
            )
        if ercot_gas_bridge_online_hours is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ercot_gas_bridge_online_hours=ercot_gas_bridge_online_hours
            )
        if reliability_floor is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                reliability_floor=reliability_floor
            )
        if reliability_floor_plant_exclusions is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                reliability_floor_plant_exclusions=reliability_floor_plant_exclusions
            )
        if chp_export_floor_measured:
            recorded_cfg = recorded_cfg.with_overrides(chp_export_floor_measured=True)
        if ercot_gtc_limits_measured:
            recorded_cfg = recorded_cfg.with_overrides(ercot_gtc_limits_measured=True)
        if pjm_measured_interface_limits:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_measured_interface_limits=True
            )
        # WP-B curtailment driver — tri-state (ct_netload_drag pattern): None keeps
        # the backcast_config per-ISO default (ERCOT keeper default-ON, owner GO
        # 2026-07-07); explicit True/False force it, so ablation arms can scrub it.
        _wtx_over: dict = {}
        if ercot_wtx_curtailment_driver is not None:
            _wtx_over["ercot_wtx_curtailment_driver"] = bool(
                ercot_wtx_curtailment_driver
            )
        if ercot_wtx_curtail_depth_wind is not None:
            _wtx_over["ercot_wtx_curtail_depth_wind"] = float(
                ercot_wtx_curtail_depth_wind
            )
        if ercot_wtx_curtail_depth_solar is not None:
            _wtx_over["ercot_wtx_curtail_depth_solar"] = float(
                ercot_wtx_curtail_depth_solar
            )
        if _wtx_over:
            # RECORD FIDELITY (ERCOT-65 discovery): run_year applies its
            # tri-state _wtx_overrides BEFORE prb_overrides, so when the generic
            # prb_overrides channel carries an ercot_wtx_* key (the keeper-lineage
            # metas do — ``coal_prb_sigmoid_overrides.ercot_wtx_curtailment_driver:
            # true``), the prb value is what the LP actually solves with. This
            # recorder used to apply _wtx_over AFTER prb_overrides, so an explicit
            # kwarg (e.g. the meta-writer's coerced ``False``) overwrote the
            # recorded value while the live solve kept the prb one — run_config.json
            # said driver-off while every solve in the ercot42+ lineage had it ON.
            # Mirror the live order exactly: the prb channel wins the record too,
            # and the conflict is surfaced loudly instead of silently mis-recorded.
            _wtx_prb_conflicts = {
                k: (prb_overrides or {}).get(k)
                for k in _wtx_over
                if (prb_overrides or {}).get(k) is not None
                and (prb_overrides or {}).get(k) != _wtx_over[k]
            }
            if _wtx_prb_conflicts:
                logger.warning(
                    "ercot_wtx_* channel conflict: explicit kwargs %s are stomped "
                    "by prb_overrides %s in the LIVE solve (run_year applies "
                    "prb_overrides last); recording the prb values. Pass the "
                    "driver through ONE channel.",
                    _wtx_over,
                    _wtx_prb_conflicts,
                )
                _wtx_over = {
                    k: v for k, v in _wtx_over.items() if k not in _wtx_prb_conflicts
                }
            if _wtx_over:
                recorded_cfg = recorded_cfg.with_overrides(**_wtx_over)
        if mass_cap_enabled:
            # G-29 wiring: mirrors run_calibration.py::run_year's own
            # mass_cap_enabled block so a mass-cap-enabled backcast config is
            # recorded identically regardless of which script drove the solve.
            recorded_cfg = recorded_cfg.with_overrides(
                mass_cap_enabled=True,
                mass_cap_tons=mass_cap_tons,
                mass_cap_program=mass_cap_program,
            )
        if scarcity_price_overlay is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                scarcity_pricing_enabled=scarcity_price_overlay,
                scarcity_price_overlay=scarcity_price_overlay,
            )
        if caiso_scarcity_pricing is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                scarcity_pricing_enabled=True,
                caiso_scarcity_pricing=caiso_scarcity_pricing,
            )
        if caiso_lcr_commitment_credit is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_lcr_commitment_credit=caiso_lcr_commitment_credit,
            )
        if caiso_solar_deliverability is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_solar_deliverability=caiso_solar_deliverability
            )
        if caiso_solar_deliverability_k is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_solar_deliverability_k=caiso_solar_deliverability_k
            )
        if caiso_solar_endogenous_spill is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_solar_endogenous_spill=caiso_solar_endogenous_spill
            )
        if caiso_solar_cap_at_delivered is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered
            )
        if neiso_gas_coldsnap_derate is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate
            )
        if neiso_coldsnap_derate_dualfuel_unswitched is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_coldsnap_derate_dualfuel_unswitched=neiso_coldsnap_derate_dualfuel_unswitched
            )
        if neiso_oil_burn_budget is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_oil_burn_budget=neiso_oil_burn_budget
            )
        if neiso_winter_fuel_inventory is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_winter_fuel_inventory=neiso_winter_fuel_inventory
            )
        if coal_fuel_inventory is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                coal_fuel_inventory=coal_fuel_inventory
            )
        if neiso_winter_fuel_start_fill_bbl is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl
            )
        if neiso_winter_fuel_mustrun is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_winter_fuel_mustrun=neiso_winter_fuel_mustrun
            )
        if caiso_import_hub_prices is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_import_hub_prices=caiso_import_hub_prices
            )
        if caiso_import_gas_coupling is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_import_gas_coupling=caiso_import_gas_coupling
            )
        if caiso_import_solar_shape is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_import_solar_shape=caiso_import_solar_shape
            )
        if caiso_per_hub_intertie is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_per_hub_intertie=caiso_per_hub_intertie
            )
        if caiso_perhub_firm_base is not None:
            # Meta-writer audit fix (orchestrator-unification Stage 7, G-14
            # residual): applied to the real solve (see the run_year call above)
            # and recorded in meta.json, but never threaded into recorded_cfg —
            # run_config.json's scenario_config silently showed the dataclass
            # default instead of the flag the LP actually solved with.
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_perhub_firm_base=caiso_perhub_firm_base
            )
        if caiso_corridor_flow_limit is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_corridor_flow_limit=caiso_corridor_flow_limit
            )
        if caiso_intertie_reference_price is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_intertie_reference_price=caiso_intertie_reference_price
            )
        if caiso_corridor_atc_forward is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_corridor_atc_forward=caiso_corridor_atc_forward
            )
        if caiso_reference_price_seam is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_reference_price_seam=caiso_reference_price_seam
            )
        if nyiso_local_selfsupply is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_local_selfsupply=nyiso_local_selfsupply
            )
        if nyiso_scr_edrp is not None:
            recorded_cfg = recorded_cfg.with_overrides(nyiso_scr_edrp=nyiso_scr_edrp)
        if nyiso_scr_edrp_strike is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_scr_edrp_strike=nyiso_scr_edrp_strike
            )
        if nyiso_firm_imports is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_firm_imports=nyiso_firm_imports
            )
        if nyiso_import_reconciliation is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_import_reconciliation=nyiso_import_reconciliation
            )
        if nyiso_import_hub_prices is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_import_hub_prices=nyiso_import_hub_prices
            )
        if nyiso_iroquois_winter_spread is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread
            )
        if nyiso_synchronised_reserve is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_synchronised_reserve=nyiso_synchronised_reserve
            )
        if nyiso_li_locational_reserve is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_li_locational_reserve=nyiso_li_locational_reserve
            )
        if nyiso_incity_commitment_obligation is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_incity_commitment_obligation=nyiso_incity_commitment_obligation
            )
        if nyiso_east_reserve_families is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_east_reserve_families=nyiso_east_reserve_families
            )
        if reliability_floor_overrides is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                reliability_floor_overrides=reliability_floor_overrides
            )
        if nyiso_gas_commitment_bridge is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_commitment_bridge=nyiso_gas_commitment_bridge
            )
        if spp_gas_commitment_bridge is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                spp_gas_commitment_bridge=spp_gas_commitment_bridge
            )
        if soco_gas_st_campaign_commitment is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                soco_gas_st_campaign_commitment=soco_gas_st_campaign_commitment
            )
        if miso_coal_night_floor is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_coal_night_floor=miso_coal_night_floor
            )
        if nyiso_gas_bridge_cc_min_load_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_cc_min_load_frac=nyiso_gas_bridge_cc_min_load_frac
            )
        if nyiso_gas_bridge_st_min_load_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_st_min_load_frac=nyiso_gas_bridge_st_min_load_frac
            )
        if nyiso_gas_bridge_startup is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_startup=nyiso_gas_bridge_startup
            )
        if nyiso_gas_bridge_da_horizon is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_da_horizon=nyiso_gas_bridge_da_horizon
            )
        if nyiso_gas_bridge_min_run is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_min_run=nyiso_gas_bridge_min_run
            )
        if nyiso_gas_bridge_plant_exclusions is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_plant_exclusions=nyiso_gas_bridge_plant_exclusions
            )
        if nyiso_gas_bridge_reserve_duty_exclusions is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_reserve_duty_exclusions=(
                    nyiso_gas_bridge_reserve_duty_exclusions
                )
            )
        if nyiso_gas_bridge_plant_min_run is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_plant_min_run=nyiso_gas_bridge_plant_min_run
            )
        if nyiso_gas_bridge_online_hours is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_online_hours=nyiso_gas_bridge_online_hours
            )
        if nyiso_gas_bridge_state_floor_min_run is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_state_floor_min_run=nyiso_gas_bridge_state_floor_min_run
            )
        if nyiso_gas_bridge_startup_aware is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_startup_aware=nyiso_gas_bridge_startup_aware
            )
        if nyiso_chp_btm_measured is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_chp_btm_measured=nyiso_chp_btm_measured
            )
        if chp_layup_duty_split is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                chp_layup_duty_split=chp_layup_duty_split
            )
        if chp_layup_duty_curve is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                chp_layup_duty_curve=chp_layup_duty_curve
            )
        if egrid_identity_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                egrid_identity_heat_rates=egrid_identity_heat_rates
            )
        if measured_ct_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                measured_ct_heat_rates=measured_ct_heat_rates
            )
        if measured_coal_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                measured_coal_heat_rates=measured_coal_heat_rates
            )
        if measured_st_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                measured_st_heat_rates=measured_st_heat_rates
            )
        if egrid_family_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                egrid_family_heat_rates=egrid_family_heat_rates
            )
        if egrid_steam_collapse_heat_rates is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                egrid_steam_collapse_heat_rates=egrid_steam_collapse_heat_rates
            )
        if cc_reserve_duty_split is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                cc_reserve_duty_split=cc_reserve_duty_split
            )
        if nyiso_gas_bridge_cc_min_run_hours is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_cc_min_run_hours=nyiso_gas_bridge_cc_min_run_hours
            )
        if nyiso_gas_bridge_st_min_run_hours is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_gas_bridge_st_min_run_hours=nyiso_gas_bridge_st_min_run_hours
            )
        if nyiso_spin_reserve_online is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_spin_reserve_online=nyiso_spin_reserve_online
            )
        if nyiso_spin_headroom_frac is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_spin_headroom_frac=nyiso_spin_headroom_frac
            )
        if nyiso_dynamic_reserve_requirements is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements
            )
        if nyiso_hydro_reserve_eligible is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_hydro_reserve_eligible=nyiso_hydro_reserve_eligible
            )
        if nyiso_scr_edrp_reserve_eligible is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_scr_edrp_reserve_eligible=nyiso_scr_edrp_reserve_eligible
            )
        if neiso_dynamic_reserve_requirements is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements
            )
        if miso_firm_imports is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_firm_imports=miso_firm_imports
            )
        if miso_seam_flow_limit:
            recorded_cfg = recorded_cfg.with_overrides(miso_seam_flow_limit=True)
        if miso_seam_flow_percentile is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_seam_flow_percentile=float(miso_seam_flow_percentile)
            )
        if miso_seam_export_limit:
            recorded_cfg = recorded_cfg.with_overrides(miso_seam_export_limit=True)
        if miso_seam_envelope_merit_cap:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_seam_envelope_merit_cap=True
            )
        if miso_seam_envelope_hour_ending_key:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_seam_envelope_hour_ending_key=True
            )
        if miso_import_sil_measured_envelope:
            recorded_cfg = recorded_cfg.with_overrides(
                miso_import_sil_measured_envelope=True
            )
        if nyiso_seam_deliverability_envelope:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_seam_deliverability_envelope=True
            )
        if nyiso_seam_par_attribution:
            recorded_cfg = recorded_cfg.with_overrides(nyiso_seam_par_attribution=True)
        if miso_pjm_border_anchor:
            recorded_cfg = recorded_cfg.with_overrides(miso_pjm_border_anchor=True)
        if miso_cc_coal_rebalance:
            recorded_cfg = recorded_cfg.with_overrides(miso_cc_coal_rebalance=True)
        if miso_firm_import_floor:
            recorded_cfg = recorded_cfg.with_overrides(miso_firm_import_floor=True)
        if miso_pjm_lmp_import_pricing:
            recorded_cfg = recorded_cfg.with_overrides(miso_pjm_lmp_import_pricing=True)
        if miso_seam_measured_ladder:
            recorded_cfg = recorded_cfg.with_overrides(miso_seam_measured_ladder=True)
        if pjm_seam_flow_limit:
            recorded_cfg = recorded_cfg.with_overrides(pjm_seam_flow_limit=True)
        if pjm_seam_flow_percentile is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_seam_flow_percentile=float(pjm_seam_flow_percentile)
            )
        if pjm_seam_export_limit:
            recorded_cfg = recorded_cfg.with_overrides(pjm_seam_export_limit=True)
        if pjm_seam_measured_ladder:
            recorded_cfg = recorded_cfg.with_overrides(pjm_seam_measured_ladder=True)
        if pjm_seam_neighbour_hourly_ladder:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_seam_neighbour_hourly_ladder=True
            )
        if ct_intermediate_split:
            recorded_cfg = recorded_cfg.with_overrides(ct_intermediate_split=True)
        if ct_intermediate_cf_threshold is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ct_intermediate_cf_threshold=float(ct_intermediate_cf_threshold)
            )
        if cc_intermediate_split:
            recorded_cfg = recorded_cfg.with_overrides(cc_intermediate_split=True)
        if cc_intermediate_cf_threshold is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                cc_intermediate_cf_threshold=float(cc_intermediate_cf_threshold)
            )
        if tranche_startup_amortization:
            recorded_cfg = recorded_cfg.with_overrides(
                tranche_startup_amortization=True
            )
        if tranche_startup_measured_runs:
            recorded_cfg = recorded_cfg.with_overrides(
                tranche_startup_measured_runs=True
            )
        if tranche_startup_conditional_runs:
            recorded_cfg = recorded_cfg.with_overrides(
                tranche_startup_conditional_runs=True
            )
        if gas_offer_margin:
            # Net-revenue margin form: record the gate AND the resolved
            # delivered-gas anchor (rule 25 — run_config carries the value the
            # solve used, never a lookup indirection).
            from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

            recorded_cfg = recorded_cfg.with_overrides(
                gas_offer_net_revenue_margin=True,
                gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
            )
        if gas_offer_margin_zonal_anchor:
            # Zone-resolved identification point for the SAME mechanism
            # (nyiso-109): record the gate AND the resolved per-zone anchors
            # (rule 21 — run_config carries the values the solve used, never a
            # lookup indirection).
            from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ZONE

            if iso not in GAS_OFFER_MARGIN_ANCHOR_BY_ZONE:
                raise SystemExit(
                    f"--gas-offer-margin-zonal-anchor: {iso} has no zone anchor "
                    "table in constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE — derive "
                    "it from the ISO's own basis with "
                    "scripts/data/derive_gas_offer_margin_anchor.py --by-zone "
                    "(rule 25: never transfer another ISO's zone table)"
                )
            recorded_cfg = recorded_cfg.with_overrides(
                gas_offer_margin_zonal_anchor=True,
                gas_offer_margin_anchor_by_zone=dict(
                    GAS_OFFER_MARGIN_ANCHOR_BY_ZONE[iso]
                ),
            )
        if coal_offer_margin:
            # Coal net-revenue margin form (ERCOT-137): record the gate AND
            # both resolved identification constants (rule 25 — run_config
            # carries the values the solve used, never a lookup indirection).
            from market_sim.config.constants import (
                COAL_OFFER_MARGIN_ANCHOR_BY_ISO,
                COAL_OFFER_MARGIN_LEVEL_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                coal_offer_net_revenue_margin=True,
                coal_offer_margin_anchor=COAL_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
                coal_offer_margin_level=COAL_OFFER_MARGIN_LEVEL_BY_ISO[iso],
            )
        if cc_committed_offer_margin:
            # CC committed-block measured offer level (ERCOT-139): record the
            # gate AND both resolved constants (rule 25 — run_config carries the
            # values the solve used, never a lookup indirection). The anchor is
            # the SHARED gas anchor, so arming this without
            # gas_offer_net_revenue_margin still needs it resolved (rule 19: one
            # identification point for the whole gas offer surface).
            from market_sim.config.constants import (
                CC_COMMITTED_OFFER_LEVEL_BY_ISO,
                GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                cc_committed_offer_margin=True,
                cc_committed_offer_level=CC_COMMITTED_OFFER_LEVEL_BY_ISO[iso],
                gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
            )
        if coal_peak_offer_margin:
            # Coal `_peak`-tranche gas-anchored offer margin (ERCOT-140):
            # record the gate AND all three resolved constants (rule 25 —
            # run_config carries the values the solve used, never a lookup
            # indirection). The anchor is the SHARED gas anchor (rule 19).
            from market_sim.config.constants import (
                COAL_PEAK_OFFER_GAS_HR_BY_ISO,
                COAL_PEAK_OFFER_LEVEL_BY_ISO,
                GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                coal_peak_offer_margin=True,
                coal_peak_offer_level=COAL_PEAK_OFFER_LEVEL_BY_ISO[iso],
                coal_peak_offer_gas_hr=COAL_PEAK_OFFER_GAS_HR_BY_ISO[iso],
                gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
            )
        if coal_perplant_offer_level:
            # Per-plant measured coal offer curves (ERCOT-144): record the
            # gate, the resolved curve registry, AND the rule-19 replacement's
            # disarms — the COAL_* offer_curve_by_group groups stripped, the
            # PRB/lignite sigmoids and the coal econ marginal-HR floor off —
            # exactly as scripts/run_calibration.py::run_year resolves them
            # (rule 25: run_config records what the solve used).
            from market_sim.config.constants import (
                COAL_PERPLANT_OFFER_CURVE_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                coal_perplant_offer_level=True,
                coal_perplant_offer_curves=COAL_PERPLANT_OFFER_CURVE_BY_ISO[iso],
                offer_curve_by_group={
                    g: v
                    for g, v in (recorded_cfg.offer_curve_by_group or {}).items()
                    if not g.startswith("COAL")
                },
                coal_prb_passthrough_sigmoid=False,
                coal_lignite_passthrough_sigmoid=False,
                coal_econ_marginal_hr_bound=False,
            )
        if coal_perplant_offer_yearly:
            # Per-year windowed per-plant coal offer curves (ercot-168):
            # record the gate and the FULL year-keyed table the run used —
            # exactly as scripts/run_calibration.py::run_year resolves it
            # (rule 25: run_config records what the solve used; the consumer
            # indexes the table by solve year, so the recorded value is
            # year-invariant).
            from market_sim.config.constants import (
                COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                coal_perplant_offer_yearly=True,
                coal_perplant_offer_curves_yearly=(
                    COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO[iso]
                ),
            )
        if coal_peak_offer_yearly_level:
            # Per-year coal `_peak` LEVEL (ercot-192, matrix section 5.1 item
            # 13): record the gate and the FULL year-keyed table the run used —
            # exactly as scripts/run_calibration.py::run_year resolves it (rule
            # 25: run_config records what the solve used; the consumer indexes
            # the table by solve year, so the recorded value is year-invariant).
            from market_sim.config.constants import (
                COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO,
            )

            recorded_cfg = recorded_cfg.with_overrides(
                coal_peak_offer_yearly_level=True,
                coal_peak_offer_level_yearly=(COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO[iso]),
            )
        if nysdec_peaker_rule_availability:
            recorded_cfg = recorded_cfg.with_overrides(
                nysdec_peaker_rule_availability=True
            )
        if nyiso_solar_market_generator_basis:
            recorded_cfg = recorded_cfg.with_overrides(
                nyiso_solar_market_generator_basis=True
            )
        if oil_primary_bin_fuel:
            recorded_cfg = recorded_cfg.with_overrides(oil_primary_bin_fuel=True)
        if st_gas_intermediate:
            recorded_cfg = recorded_cfg.with_overrides(
                st_gas_intermediate_split=True,
                gas_st_startup_cost=True,
                gas_st_wefor_base_override=0.10,
            )
        if st_gas_intermediate_cf_threshold is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                st_gas_intermediate_cf_threshold=float(st_gas_intermediate_cf_threshold)
            )
        if gas_hub_basis_overlay is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                gas_hub_basis_overlay=gas_hub_basis_overlay
            )
        if caiso_per_year_import_caps is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_per_year_import_caps=caiso_per_year_import_caps
            )
        if caiso_asymmetric_path_ratings is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_asymmetric_path_ratings=caiso_asymmetric_path_ratings
            )
        if caiso_zonal_loss_surface is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                caiso_zonal_loss_surface=caiso_zonal_loss_surface
            )
        if capacity_deliverability_limits is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                capacity_deliverability_limits=capacity_deliverability_limits
            )
        if unit_outage_lp_capacity_basis is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_lp_capacity_basis=unit_outage_lp_capacity_basis
            )
        if unit_outage_st_capacity_basis is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_st_capacity_basis=unit_outage_st_capacity_basis
            )
        if unit_outage_window_hour_grain is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_window_hour_grain=unit_outage_window_hour_grain
            )
        if unit_outage_per_unit_clip is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_per_unit_clip=unit_outage_per_unit_clip
            )
        if unit_outage_short_windows_gas is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_short_windows_gas=unit_outage_short_windows_gas
            )
        if unit_outage_mixed_gas_routing is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                unit_outage_mixed_gas_routing=unit_outage_mixed_gas_routing
            )
        if campd_per_unit_attribution is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                campd_per_unit_attribution=campd_per_unit_attribution
            )
        if campd_outage_merit_order_guard is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                campd_outage_merit_order_guard=campd_outage_merit_order_guard
            )
        if netload_drag_layup_window_mask is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                netload_drag_layup_window_mask=netload_drag_layup_window_mask
            )
        if netload_drag_merit_allocation is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                netload_drag_merit_allocation=netload_drag_merit_allocation
            )
        if netload_drag_min_run_persistence is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                netload_drag_min_run_persistence=netload_drag_min_run_persistence
            )
        if vre_curtailment_oversupply_allocation is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                vre_curtailment_oversupply_allocation=vre_curtailment_oversupply_allocation
            )
        if spp_curtailment_ceiling is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                spp_curtailment_ceiling=spp_curtailment_ceiling
            )
        if spp_curtail_depth_wind is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                spp_curtail_depth_wind=float(spp_curtail_depth_wind)
            )
        if cc_winter_capability_basis is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                cc_winter_capability_basis=cc_winter_capability_basis
            )
        if ramp_limits is not None:
            recorded_cfg = recorded_cfg.with_overrides(ramp_limits=ramp_limits)
        if local_capacity_constraints is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                local_capacity_constraints=local_capacity_constraints
            )
        # Tri-state mirror of run_year: None keeps the per-ISO base default
        # (CAISO drag ON), True/False force — run_config.json must record what
        # the LP actually solved with (rule 24).
        if ct_netload_drag is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                ct_netload_drag=bool(ct_netload_drag)
            )
        # pjm-169 F2 arm — tri-state mirror of run_year. None keeps the
        # backcast_config per-ISO default (PJM ARMED); True/False force. The
        # recorded config must report the posture the LP actually solved
        # (rule 24 [R-REGISTRY]) — but ONLY when the caller forced one, so an
        # unset PJM run still records the armed default resolved downstream.
        if pjm_interface_feed_admissibility_gate is not None:
            recorded_cfg = recorded_cfg.with_overrides(
                pjm_interface_feed_admissibility_gate=bool(
                    pjm_interface_feed_admissibility_gate
                )
            )
        if zero_forcing_ablation:
            # Record the ablated config so run_config.json's scenario_config matches
            # what the LP actually solved (run_year applied the same transform). The
            # off-list is derived from the D-2 mechanism registry (rule 20).
            from market_sim.config.scenarios import ScenarioConfig

            recorded_cfg = ScenarioConfig.as_zero_forcing_ablation(recorded_cfg)
        # nyiso-231 — the gas-offer-margin vintage anchors are resolved HERE,
        # FUSED TO THE RETURN, and nowhere else. `_gas_series` is only the series
        # the offer path prices against once the run's WHOLE gas posture is on
        # the config (`gas_hub_basis_overlay` is applied ~144 lines above), so a
        # mirror placed mid-function measures a series no unit ever pays — which
        # is exactly what nyiso-230's 2022 arm recorded (Capital_Hudson 7.0563
        # against the 8.4431 the LP priced). Fusing it to the return makes the
        # ordering structural: any new `if flag:` block lands ABOVE this line.
        # DO NOT add config-mutating statements below it (rule 24 [R-REGISTRY]).
        return mirror_solve_year_gas_anchors(
            recorded_cfg,
            cfg_year,
            int(hours),
            iso_vintage=bool(gas_offer_margin_anchor_vintage),
            zonal_vintage=bool(gas_offer_margin_zonal_anchor_vintage),
        )

    # OPT-IN --reuse-solved: decide up front which requested years may be
    # copied from the prior bundle instead of re-solved. Absent the flag this
    # is a no-op and the run is byte-identical to a plain fresh solve.
    reuse_plan: dict[int, dict] = {}
    reuse_record: dict | None = None
    prior_tables: dict[str, pd.DataFrame | None] = {}
    if reuse_solved is not None:
        reuse_plan, reuse_record = plan_reuse_solved(
            Path(reuse_solved),
            iso=iso,
            hours=hours,
            years=years,
            gas_prices=gas_prices,
            current_kwargs=_solve_kwargs_snapshot,
            recorded_config_for_year=_recorded_config,
        )
        logger.info(
            "--reuse-solved %s: reusing years %s, solving fresh %s",
            reuse_solved,
            sorted(reuse_plan) or "none",
            sorted(set(int(y) for y in years) - set(reuse_plan)) or "none",
        )
        if reuse_plan:
            prior_tables = _load_prior_bundle_tables(Path(reuse_solved))

    for year in years:
        _t_year = time.perf_counter()
        gas_price = gas_prices[year]
        if year in reuse_plan:
            info = reuse_plan[year]
            _copy_reused_year(
                Path(reuse_solved),
                run_dir,
                year,
                info["passes"],
                persist_p2_state=persist_p2_state,
            )
            for name, frames in (
                ("system", system_frames),
                ("storage", storage_frames),
                ("posture", posture_frames),
                ("flows", flows_frames),
                ("storage_as", storage_as_frames),
                ("btm", btm_frames),
                ("eia930", eia930_frames),
                ("eia923", eia923_frames),
                ("campd", campd_frames),
            ):
                tbl = prior_tables.get(name)
                if tbl is not None:
                    frames.append(tbl[tbl["year"] == year].copy())
            passes_seen.update(info["passes"])
            if first_year_cfg is None:
                # Pristine per-year config, same construction as the fresh
                # path's ``cfg`` below — only its year-invariant fields feed
                # the meta block.
                first_year_cfg = backcast_config(year, iso, hours, gas_price)
            # No optimal basis crosses a reused year: the next fresh year
            # starts cold instead of warm-starting from a stale earlier
            # year's basis (warm-start is basis-neutral either way; see
            # docs/cross-year-warmstart.md).
            xyear_cache.clear()
            logger.info(
                "year %d REUSED from %s (config hash %s) in %.1fs — copied "
                "artifacts, no solve; NOT fresh evidence",
                year,
                reuse_solved,
                info["cache_key"] or info["scenario_config_sha256"],
                time.perf_counter() - _t_year,
            )
            continue
        if not is_ercot:
            group_by_code = _fleet_group_by_code(iso, iso_config, year)
        cfg = backcast_config(year, iso, hours, gas_price)
        if first_year_cfg is None:
            first_year_cfg = cfg
        # Effective VOLL for the published-anchor additive RTORPA
        # (ercot_ordc_adder_published_anchor). Read through the same
        # prb_overrides-first channel the CAISO demand flags below use
        # (the caiso-80 defect class): the pristine ``cfg`` does NOT carry
        # generic ScenarioConfig overrides, and ``ordc_voll`` is exactly the
        # kind of published parameter a scenario probe would move.
        _ordc_voll_eff = float((prb_overrides or {}).get("ordc_voll", cfg.ordc_voll))

        # Effective CAISO demand flags: they arrive through the generic
        # ``prb_overrides`` ScenarioConfig channel, which run_year's own
        # backcast_config applies but this loop's pristine ``cfg`` does NOT
        # carry — checking ``cfg`` alone silently threaded the RAW demand
        # into a probe-channel realigned/supply-consistent solve (caiso-80
        # fix of the 48ec6b9 threading optimization).
        def _caiso_demand_flag(name: str) -> bool:
            v = (prb_overrides or {}).get(name)
            return bool(v) if v is not None else bool(getattr(cfg, name, False))

        _supply_consistent = _caiso_demand_flag("caiso_supply_consistent_demand")
        _clock_realign = _caiso_demand_flag("caiso_demand_clock_realign")
        # ercot-231: the ERCOT tie-zone attribution flag is the same defect
        # class (a demand-build flag arriving via prb_overrides that the
        # pristine ``cfg`` does not carry — checking cfg alone threads RAW
        # demand into an armed probe, silently inert and misreported).
        _ercot_tie_zonal = _caiso_demand_flag("ercot_tie_zonal_interchange")
        # td_loss_factor is the SAME defect class as the two flags above and
        # needs the same treatment (nyiso-87). It is not a solve_and_persist
        # kwarg, so a `--set td_loss_factor=X` probe can only arrive through
        # prb_overrides — which run_year applies to ITS config but this
        # pristine ``cfg`` does not carry. Reading ``cfg.td_loss_factor`` here
        # therefore threaded RAW demand into the LP while run_config.json
        # recorded the armed value, so the probe was silently inert AND
        # misreported (found when an arm-D td_loss probe came back
        # byte-identical to its control: demand 147.049 TWh either way).
        # Scalar rather than bool, so it cannot reuse _caiso_demand_flag.
        _td_loss = (prb_overrides or {}).get("td_loss_factor")
        _td_loss = (
            float(_td_loss) if _td_loss is not None else float(cfg.td_loss_factor)
        )
        # Under caiso_supply_consistent_demand the honest series is loaded
        # HERE too, so the must-run residual derivation, the persisted
        # system.parquet demand column, and the LP all ride ONE demand basis
        # (the LP-vs-recorded divergence was a caiso-80 STEP-2 discovery).
        # The realign-only path deliberately keeps its historical behavior:
        # this load stays on the raw clock (must_run/system.parquet as in the
        # caiso-75..78 keepers) and run_year loads its own realigned series.
        demand = load_demand(
            iso,
            year,
            iso_config,
            td_loss_factor=_td_loss,
            include_interchange=not priced_interchange,
            strict_demand_profile=strict_demand_profile,
            caiso_supply_consistent_demand=_supply_consistent,
            ercot_tie_zonal_interchange=_ercot_tie_zonal,
        )
        # Must-run residual classes (biomass / other-gas / ...) are netted out
        # of demand for the LP and re-added as pseudo-units in the dispatch
        # frame, so they displace marginal gas and appear as their own classes
        # instead of an invisible OTHER gap. Applies to EVERY ISO now: biomass is
        # fuel-supply / contract limited and price-insensitive in reality, so it
        # is injected from its measured EIA-923 annual+monthly energy (vintage-
        # carry reconciled) exactly like ERCOT, rather than left as a dispatchable
        # LP unit the merit order runs to max when gas rises (which over-dispatched
        # NEISO biomass ~2x in the high-gas 2025). run_year drops the raw biomass
        # LP units (inject_biomass_mustrun) so it is not served twice. Hydro is an
        # LP resource for all ISOs (budget hydro + pumped storage), never injected.
        e930_year = _eia930_frame(year, iso, iso_config)
        # miso-253: the injected residual classes' host-steam partition. Read
        # through the prb_overrides-aware helper for the caiso-80 defect class
        # (a flag arriving on the generic ScenarioConfig channel that this
        # loop's pristine ``cfg`` does not carry) — checking ``cfg`` alone would
        # silently inject the un-partitioned array while run_config.json
        # recorded the armed posture.
        _mustrun_chp_btm = _caiso_demand_flag("mustrun_chp_btm_holdout")
        # spp-49: read through the SAME seam as the benchmark below, so the
        # injected residual and the frame it is scored against share one
        # plant population (rule 19 [R-ONE-MECH]).
        _bench_vintage_union = _caiso_demand_flag("benchmark_membership_vintage_union")
        must_run = _must_run_profiles(
            year,
            generation,
            iso,
            demand,
            skip_classes=frozenset(),
            e930=e930_year,
            mustrun_chp_btm_holdout=_mustrun_chp_btm,
            benchmark_membership_vintage_union=_bench_vintage_union,
        )
        must_run_total = np.sum(list(must_run.values()), axis=0) if must_run else None
        inject_biomass = "biomass" in must_run
        logger.info(
            "solving %s %d (hours=%d, Henry Hub=$%.2f/MMBtu, commitment=%s)",
            iso,
            year,
            hours,
            gas_price,
            commitment,
        )
        _t_pre_solve = time.perf_counter()

        # Thread the demand we already loaded above into run_year to skip its
        # duplicate load_demand — but only when this load is byte-identical to
        # run_year's own: run_year never passes strict_demand_profile (always
        # loads the non-strict series) and reads the CAISO demand flags from
        # its config. Under caiso_supply_consistent_demand the two loads are
        # identical by construction (the honest series supersedes the clock
        # realign inside the loader), so threading is correct; under a
        # realign-ONLY recipe they diverge (this load is raw-clock, run_year's
        # is realigned) and None is passed so run_year loads its own array
        # (historical caiso-75..78 behavior). iso_config / td_loss_factor /
        # include_interchange already match by construction.
        _run_year_demand = (
            demand
            if (
                not strict_demand_profile and (_supply_consistent or not _clock_realign)
            )
            else None
        )
        result, context, result_p1, p2_state = run_year(
            year,
            iso,
            hours,
            gas_price,
            ttc_overrides={},
            commitment_enabled=commitment,
            commitment_screen_coal=screen_coal,
            coal_lignite_mustrun=coal_lignite_mustrun,
            coal_prb_mustrun=coal_prb_mustrun,
            coal_prb_passthrough=coal_prb_passthrough,
            outage_source=outage_source,
            coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,
            coal_mustrun_per_plant=coal_mustrun_per_plant,
            retiree_cems_cap=retiree_cems_cap,
            ct_mustrun_per_plant=ct_mustrun_per_plant,
            ct_mustrun_floor_frac=ct_mustrun_floor_frac,
            coal_drop_pof=coal_drop_pof,
            coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,
            prb_overrides=prb_overrides,
            coal_bit_sigmoid=coal_bit_sigmoid,
            bit_overrides=bit_overrides,
            coal_econ_srmc_bound=coal_econ_srmc_bound,
            coal_econ_marginal_hr_bound=coal_econ_marginal_hr_bound,
            committed_band_measured_basis=committed_band_measured_basis,
            ercot_offer_hrmult_ep_rebasis=ercot_offer_hrmult_ep_rebasis,
            ercot_offer_hrmult_ep_rebasis_bands=ercot_offer_hrmult_ep_rebasis_bands,
            coal_takeorpay_from_data=coal_takeorpay_from_data,
            coal_mustrun_online_pmin=coal_mustrun_online_pmin,
            coal_sync_srmc_tranche=coal_sync_srmc_tranche,
            ct_intermediate_split=ct_intermediate_split,
            ct_intermediate_cf_threshold=ct_intermediate_cf_threshold,
            cc_intermediate_split=cc_intermediate_split,
            cc_intermediate_cf_threshold=cc_intermediate_cf_threshold,
            tranche_startup_amortization=tranche_startup_amortization,
            tranche_startup_measured_runs=tranche_startup_measured_runs,
            tranche_startup_conditional_runs=tranche_startup_conditional_runs,
            gas_offer_margin=gas_offer_margin,
            gas_offer_margin_zonal_anchor=gas_offer_margin_zonal_anchor,
            coal_offer_margin=coal_offer_margin,
            cc_committed_offer_margin=cc_committed_offer_margin,
            coal_peak_offer_margin=coal_peak_offer_margin,
            coal_peak_offer_yearly_level=coal_peak_offer_yearly_level,
            coal_perplant_offer_level=coal_perplant_offer_level,
            coal_perplant_offer_yearly=coal_perplant_offer_yearly,
            nysdec_peaker_rule_availability=nysdec_peaker_rule_availability,
            nyiso_solar_market_generator_basis=nyiso_solar_market_generator_basis,
            oil_primary_bin_fuel=oil_primary_bin_fuel,
            st_gas_intermediate=st_gas_intermediate,
            st_gas_intermediate_cf_threshold=st_gas_intermediate_cf_threshold,
            plant_tranche_config=plant_tranche_config,
            storage_daily_cycling=storage_daily_cycling,
            storage_vintage_ramp=storage_vintage_ramp,
            battery_dispatch_adder=battery_dispatch_adder,
            as_reserve_withholding=as_reserve_withholding,
            energy_reserve_coopt=energy_reserve_coopt,
            miso_zonal_reserves=miso_zonal_reserves,
            miso_midwest_subregional_reserves=miso_midwest_subregional_reserves,
            miso_reserve_pergen=miso_reserve_pergen,
            miso_commitment_posture=miso_commitment_posture,
            miso_reserve_online_gated=miso_reserve_online_gated,
            miso_measured_reserve_requirements=miso_measured_reserve_requirements,
            miso_south_seam_split=miso_south_seam_split,
            miso_rdt_tcdc=miso_rdt_tcdc,
            miso_zonal_loss_surface=miso_zonal_loss_surface,
            pjm_zonal_loss_surface=pjm_zonal_loss_surface,
            ercot_multiproduct_as_coopt=ercot_multiproduct_as_coopt,
            ercot_ecrs_conservative_deployment=ercot_ecrs_conservative_deployment,
            ercot_nonreleasable_as_withholding=ercot_nonreleasable_as_withholding,
            ercot_ordc_total_reserve=ercot_ordc_total_reserve,
            ercot_storage_as_product_credit=ercot_storage_as_product_credit,
            gas_hh_monthly_shape=gas_hh_monthly_shape,
            ercot_as_aware_commitment=ercot_as_aware_commitment,
            ercot_reserve_supply_cap=ercot_reserve_supply_cap,
            ercot_reserve_supply_cap_from_year=ercot_reserve_supply_cap_from_year,
            ercot_reserve_supply_forward=ercot_reserve_supply_forward,
            pjm_reserve_supply_cap=pjm_reserve_supply_cap,
            pjm_reserve_online_gated=pjm_reserve_online_gated,
            pjm_reserve_online_rho=pjm_reserve_online_rho,
            pjm_reserve_commitment_scoped=pjm_reserve_commitment_scoped,
            pjm_reserve_pergen=pjm_reserve_pergen,
            pjm_reserve_pergen_sync=pjm_reserve_pergen_sync,
            pjm_reserve_pergen_size_split=pjm_reserve_pergen_size_split,
            pjm_commitment_posture=pjm_commitment_posture,
            measured_ramp_capability=measured_ramp_capability,
            ercot_as_forward_requirement=ercot_as_forward_requirement,
            ercot_load_resource_reserve=ercot_load_resource_reserve,
            ercot_load_resource_reserve_from_year=ercot_load_resource_reserve_from_year,
            ercot_storage_as_reserve=ercot_storage_as_reserve,
            ercot_storage_as_reserve_from_year=ercot_storage_as_reserve_from_year,
            ercot_ecrs_requirement=ercot_ecrs_requirement,
            ercot_ecrs_requirement_from_year=ercot_ecrs_requirement_from_year,
            ordc_lolp_params_path=ordc_lolp_params_path,
            as_reserve_formula=as_reserve_formula,
            storage_as_commitment=storage_as_commitment,
            ercot_storage_as_deployment=ercot_storage_as_deployment,
            ercot_storage_as_deployment_from_year=ercot_storage_as_deployment_from_year,
            ercot_storage_as_endogenous=ercot_storage_as_endogenous,
            ercot_storage_as_duration_gate=ercot_storage_as_duration_gate,
            gas_offer_curve=gas_offer_curve,
            gas_monthly_actuals=gas_monthly_actuals,
            pjm_zonal_gas_basis=pjm_zonal_gas_basis,
            miso_zonal_gas_basis=miso_zonal_gas_basis,
            miso_winter_citygate_daily=miso_winter_citygate_daily,
            pjm_congestion=pjm_congestion,
            offer_curve_overrides=offer_curve_overrides,
            offer_curve_deltas=offer_curve_deltas,
            curve_smoothing=curve_smoothing,
            cc_derate_from_top=cc_derate_from_top,
            cc_nameplate_summer_derate=cc_nameplate_summer_derate,
            coal_nameplate_summer_derate=coal_nameplate_summer_derate,
            gt_ambient_derate=gt_ambient_derate,
            gt_ambient_derate_ref_c=gt_ambient_derate_ref_c,
            gt_ambient_derate_slope_cc=gt_ambient_derate_slope_cc,
            gt_ambient_derate_slope_ct=gt_ambient_derate_slope_ct,
            temp_dependent_derate=temp_dependent_derate,
            temp_derate_hourly_grain=temp_derate_hourly_grain,
            temp_derate_mean_anchored=temp_derate_mean_anchored,
            temp_derate_classes=temp_derate_classes,
            temp_derate_slope_st_chp=temp_derate_slope_st_chp,
            temp_derate_slope_ct_chp=temp_derate_slope_ct_chp,
            ercot_offer_surface_conditional=ercot_offer_surface_conditional,
            ercot_offer_surface_midcurve_conditional=(
                ercot_offer_surface_midcurve_conditional
            ),
            ercot_offer_surface_cleared_share=ercot_offer_surface_cleared_share,
            ercot_offer_surface_cleared_share_state=(
                ercot_offer_surface_cleared_share_state
            ),
            ercot_offer_surface_cleared_share_steam=(
                ercot_offer_surface_cleared_share_steam
            ),
            ercot_offer_surface_lowcurve=ercot_offer_surface_lowcurve,
            ercot_offer_surface_lowcurve_floorscoped=(
                ercot_offer_surface_lowcurve_floorscoped
            ),
            wind_ptc_vintage_offers=wind_ptc_vintage_offers,
            neiso_offer_surface_conditional=neiso_offer_surface_conditional,
            pjm_offer_surface_conditional=pjm_offer_surface_conditional,
            pjm_da_virtual_bids=pjm_da_virtual_bids,
            pjm_offer_midcurve_conditional=pjm_offer_midcurve_conditional,
            pjm_offer_midcurve_segments=pjm_offer_midcurve_segments,
            caiso_offer_surface_measured=caiso_offer_surface_measured,
            caiso_offer_surface_measured_ungrounded=(
                caiso_offer_surface_measured_ungrounded
            ),
            caiso_st_gas_committed_measured=caiso_st_gas_committed_measured,
            caiso_st_gas_peak_measured=caiso_st_gas_peak_measured,
            caiso_ct_peaker_committed_measured=caiso_ct_peaker_committed_measured,
            nyiso_ct_peaker_bands_measured=nyiso_ct_peaker_bands_measured,
            nyiso_ct_peaker_committed_measured=nyiso_ct_peaker_committed_measured,
            nyiso_st_gas_econ_bands_deleaked=nyiso_st_gas_econ_bands_deleaked,
            caiso_offer_surface_conditional=caiso_offer_surface_conditional,
            nearby_fuel_price_zone_donor_guard=nearby_fuel_price_zone_donor_guard,
            fleet_state_from_eia860=fleet_state_from_eia860,
            caiso_citygate_spot_coverage=caiso_citygate_spot_coverage,
            ercot_nuclear_unit_availability=ercot_nuclear_unit_availability,
            nuclear_unit_availability=nuclear_unit_availability,
            ercot_thermal_dam_availability=ercot_thermal_dam_availability,
            ercot_thermal_dam_availability_hourly=(
                ercot_thermal_dam_availability_hourly
            ),
            ercot_thermal_dam_availability_plant=(ercot_thermal_dam_availability_plant),
            ercot_wind_zone_shape=ercot_wind_zone_shape,
            ercot_noncampd_plant_availability=ercot_noncampd_plant_availability,
            ercot_storage_capability_measured=ercot_storage_capability_measured,
            ercot_online_capacity_envelope_measured=(
                ercot_online_capacity_envelope_measured
            ),
            ercot_ordc_only_scarcity=ercot_ordc_only_scarcity,
            must_run_mw=must_run_total,
            inject_biomass_mustrun=inject_biomass,
            demand=_run_year_demand,
            priced_interchange=priced_interchange,
            hydro_backfill_year=hydro_backfill_year,
            hydro_eia930_monthly=hydro_eia930_monthly,
            hydro_budget_period_by_instrument=hydro_budget_period_by_instrument,
            hydro_forecast_budget=hydro_forecast_budget,
            hydro_year=hydro_year,
            interchange_shaping=interchange_shaping,
            interchange_shaping_export_only=interchange_shaping_export_only,
            reference_price_interface=reference_price_interface,
            negative_renewable_offers=negative_renewable_offers,
            caiso_gas_commitment_floor=caiso_gas_commitment_floor,
            caiso_gas_floor_frac=caiso_gas_floor_frac,
            caiso_ra_mustoffer=caiso_ra_mustoffer,
            caiso_ra_min_load_frac=caiso_ra_min_load_frac,
            caiso_ra_startup_bridge=caiso_ra_startup_bridge,
            caiso_ra_bridge_decommit=caiso_ra_bridge_decommit,
            ercot_gas_commitment_bridge=ercot_gas_commitment_bridge,
            ercot_gas_bridge_min_load_frac=ercot_gas_bridge_min_load_frac,
            ercot_gas_bridge_startup=ercot_gas_bridge_startup,
            ercot_gas_bridge_da_horizon=ercot_gas_bridge_da_horizon,
            ercot_gas_bridge_online_hours=ercot_gas_bridge_online_hours,
            ercot_commitment_posture=ercot_commitment_posture,
            ercot_commitment_posture_min_load_frac=(
                ercot_commitment_posture_min_load_frac
            ),
            carry_operating_mothballs=carry_operating_mothballs,
            reliability_floor=reliability_floor,
            reliability_floor_plant_exclusions=(
                reliability_floor_plant_exclusions
                if reliability_floor_plant_exclusions is not None
                else False
            ),
            scarcity_price_overlay=scarcity_price_overlay,
            caiso_scarcity_pricing=caiso_scarcity_pricing,
            caiso_lcr_commitment_credit=caiso_lcr_commitment_credit,
            caiso_solar_deliverability=caiso_solar_deliverability,
            caiso_solar_deliverability_k=caiso_solar_deliverability_k,
            caiso_solar_endogenous_spill=caiso_solar_endogenous_spill,
            caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered,
            neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate,
            neiso_coldsnap_derate_dualfuel_unswitched=neiso_coldsnap_derate_dualfuel_unswitched,
            neiso_oil_burn_budget=neiso_oil_burn_budget,
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory,
            neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl,
            neiso_winter_fuel_mustrun=neiso_winter_fuel_mustrun,
            coal_fuel_inventory=coal_fuel_inventory,
            caiso_import_hub_prices=caiso_import_hub_prices,
            caiso_import_gas_coupling=caiso_import_gas_coupling,
            caiso_import_solar_shape=caiso_import_solar_shape,
            caiso_per_hub_intertie=caiso_per_hub_intertie,
            caiso_perhub_firm_base=caiso_perhub_firm_base,
            caiso_corridor_flow_limit=caiso_corridor_flow_limit,
            caiso_intertie_reference_price=caiso_intertie_reference_price,
            caiso_corridor_atc_forward=caiso_corridor_atc_forward,
            caiso_reference_price_seam=caiso_reference_price_seam,
            caiso_per_year_import_caps=caiso_per_year_import_caps,
            caiso_asymmetric_path_ratings=caiso_asymmetric_path_ratings,
            caiso_zonal_loss_surface=caiso_zonal_loss_surface,
            capacity_deliverability_limits=capacity_deliverability_limits,
            unit_outage_lp_capacity_basis=unit_outage_lp_capacity_basis,
            unit_outage_mixed_gas_routing=unit_outage_mixed_gas_routing,
            unit_outage_st_capacity_basis=unit_outage_st_capacity_basis,
            unit_outage_per_unit_clip=unit_outage_per_unit_clip,
            unit_outage_short_windows_gas=unit_outage_short_windows_gas,
            unit_outage_window_hour_grain=unit_outage_window_hour_grain,
            campd_per_unit_attribution=campd_per_unit_attribution,
            campd_outage_merit_order_guard=campd_outage_merit_order_guard,
            netload_drag_layup_window_mask=netload_drag_layup_window_mask,
            netload_drag_merit_allocation=netload_drag_merit_allocation,
            netload_drag_min_run_persistence=netload_drag_min_run_persistence,
            vre_curtailment_oversupply_allocation=vre_curtailment_oversupply_allocation,
            spp_curtailment_ceiling=spp_curtailment_ceiling,
            spp_curtail_depth_wind=spp_curtail_depth_wind,
            cc_winter_capability_basis=cc_winter_capability_basis,
            ramp_limits=ramp_limits,
            local_capacity_constraints=local_capacity_constraints,
            nyiso_local_selfsupply=nyiso_local_selfsupply,
            nyiso_scr_edrp=nyiso_scr_edrp,
            nyiso_scr_edrp_strike=nyiso_scr_edrp_strike,
            nyiso_firm_imports=nyiso_firm_imports,
            nyiso_import_reconciliation=nyiso_import_reconciliation,
            nyiso_import_hub_prices=nyiso_import_hub_prices,
            nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread,
            nyiso_synchronised_reserve=nyiso_synchronised_reserve,
            nyiso_li_locational_reserve=nyiso_li_locational_reserve,
            nyiso_incity_commitment_obligation=nyiso_incity_commitment_obligation,
            nyiso_east_reserve_families=nyiso_east_reserve_families,
            reliability_floor_overrides=reliability_floor_overrides,
            nyiso_spin_reserve_online=nyiso_spin_reserve_online,
            nyiso_gas_commitment_bridge=nyiso_gas_commitment_bridge,
            spp_gas_commitment_bridge=spp_gas_commitment_bridge,
            soco_gas_st_campaign_commitment=soco_gas_st_campaign_commitment,
            miso_coal_night_floor=miso_coal_night_floor,
            nyiso_gas_bridge_cc_min_load_frac=nyiso_gas_bridge_cc_min_load_frac,
            nyiso_gas_bridge_st_min_load_frac=nyiso_gas_bridge_st_min_load_frac,
            nyiso_gas_bridge_startup=nyiso_gas_bridge_startup,
            nyiso_gas_bridge_da_horizon=nyiso_gas_bridge_da_horizon,
            nyiso_gas_bridge_min_run=nyiso_gas_bridge_min_run,
            nyiso_gas_bridge_plant_exclusions=nyiso_gas_bridge_plant_exclusions,
            nyiso_gas_bridge_reserve_duty_exclusions=(
                nyiso_gas_bridge_reserve_duty_exclusions
            ),
            nyiso_gas_bridge_plant_min_run=nyiso_gas_bridge_plant_min_run,
            nyiso_gas_bridge_online_hours=nyiso_gas_bridge_online_hours,
            nyiso_gas_bridge_state_floor_min_run=nyiso_gas_bridge_state_floor_min_run,
            nyiso_gas_bridge_startup_aware=nyiso_gas_bridge_startup_aware,
            nyiso_chp_btm_measured=nyiso_chp_btm_measured,
            cc_reserve_duty_split=cc_reserve_duty_split,
            chp_layup_duty_split=chp_layup_duty_split,
            chp_layup_duty_curve=chp_layup_duty_curve,
            egrid_identity_heat_rates=egrid_identity_heat_rates,
            measured_ct_heat_rates=measured_ct_heat_rates,
            measured_coal_heat_rates=measured_coal_heat_rates,
            measured_st_heat_rates=measured_st_heat_rates,
            egrid_family_heat_rates=egrid_family_heat_rates,
            egrid_steam_collapse_heat_rates=egrid_steam_collapse_heat_rates,
            nyiso_gas_bridge_cc_min_run_hours=nyiso_gas_bridge_cc_min_run_hours,
            nyiso_gas_bridge_st_min_run_hours=nyiso_gas_bridge_st_min_run_hours,
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac,
            nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements,
            nyiso_hydro_reserve_eligible=nyiso_hydro_reserve_eligible,
            nyiso_scr_edrp_reserve_eligible=nyiso_scr_edrp_reserve_eligible,
            neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements,
            miso_firm_imports=miso_firm_imports,
            miso_seam_flow_limit=miso_seam_flow_limit,
            miso_seam_flow_percentile=miso_seam_flow_percentile,
            miso_seam_export_limit=miso_seam_export_limit,
            miso_seam_envelope_merit_cap=miso_seam_envelope_merit_cap,
            miso_seam_envelope_hour_ending_key=miso_seam_envelope_hour_ending_key,
            miso_import_sil_measured_envelope=miso_import_sil_measured_envelope,
            nyiso_seam_deliverability_envelope=nyiso_seam_deliverability_envelope,
            nyiso_seam_par_attribution=nyiso_seam_par_attribution,
            miso_pjm_border_anchor=miso_pjm_border_anchor,
            miso_cc_coal_rebalance=miso_cc_coal_rebalance,
            miso_firm_import_floor=miso_firm_import_floor,
            miso_pjm_lmp_import_pricing=miso_pjm_lmp_import_pricing,
            miso_seam_measured_ladder=miso_seam_measured_ladder,
            pjm_seam_flow_limit=pjm_seam_flow_limit,
            pjm_seam_flow_percentile=pjm_seam_flow_percentile,
            pjm_seam_export_limit=pjm_seam_export_limit,
            pjm_seam_measured_ladder=pjm_seam_measured_ladder,
            pjm_seam_neighbour_hourly_ladder=pjm_seam_neighbour_hourly_ladder,
            gas_hub_basis_overlay=gas_hub_basis_overlay,
            gas_st_netload_drag=gas_st_netload_drag,
            gas_st_drag_overrides=gas_st_drag_overrides,
            ct_netload_drag=ct_netload_drag,
            pjm_interface_feed_admissibility_gate=pjm_interface_feed_admissibility_gate,
            gas_offer_margin_anchor_vintage=gas_offer_margin_anchor_vintage,
            gas_offer_margin_zonal_anchor_vintage=gas_offer_margin_zonal_anchor_vintage,
            ct_drag_overrides=ct_drag_overrides,
            chp_export_floor_measured=chp_export_floor_measured,
            ercot_gtc_limits_measured=ercot_gtc_limits_measured,
            pjm_measured_interface_limits=pjm_measured_interface_limits,
            ercot_wtx_curtailment_driver=ercot_wtx_curtailment_driver,
            ercot_wtx_curtail_depth_wind=ercot_wtx_curtail_depth_wind,
            ercot_wtx_curtail_depth_solar=ercot_wtx_curtail_depth_solar,
            mass_cap_enabled=mass_cap_enabled,
            mass_cap_tons=mass_cap_tons,
            mass_cap_program=mass_cap_program,
            zero_forcing_ablation=zero_forcing_ablation,
            xyear_cache=xyear_cache,
            persist_p0_commitment=persist_p0_commitment,
            persist_p0_dispatch=persist_p0_dispatch,
        )
        _t_post_solve = time.perf_counter()
        if persist_p2_state:
            _save_p2_state(run_dir, year, p2_state)
        labelled = [("P2" if result_p1 is not None else "P1", result)]
        if result_p1 is not None:
            labelled.insert(0, ("P1", result_p1))
        # Per-pass min-gen floors + mechanism ids (D-2/D-4 attribution).
        _save_floor_arrays(run_dir, year, p2_state, result_p1 is not None)
        # results_write sub-instrumentation (refactor plan §7-H4): the merged
        # window is split into state sidecars / frame construction / the parquet
        # write / benchmark-scoring frames. The four components are measured on
        # disjoint, exhaustive segments of [_t_post_solve, _t_end], so they sum
        # to results_write exactly — the reported field itself is unchanged.
        _t_state_done = time.perf_counter()
        _parquet_s = 0.0

        # CAMPD hourly is built before the per-pass frames so the BTM 923
        # backfill can gate on "did the plant actually run this year" —
        # it depends only on the year, not the solve result.
        campd_year = (
            _campd_hourly_frame(year, iso, parasitic_factors, hours)
            if has_campd
            else None
        )
        campd_active: set[int] | None = None
        if campd_year is not None:
            _by_plant = campd_year.groupby("plant_id")["net_mw"].sum()
            campd_active = set(_by_plant[_by_plant > 0.0].index.astype(int))
        _t_campd_done = time.perf_counter()

        # Year-LOCAL accumulators for the two per-year diagnostic sidecars.
        # Deliberately not the cross-year lists above: a per-plant unit-hour
        # frame is the largest object in this loop after ``_dispf`` (CAISO 2025
        # = 1,358 gens x 8,760 h), so it is built after ``_dispf`` is freed,
        # written at the end of the year, and released before the next year's
        # fleet build — never carried across the year boundary.
        unit_frames: list[pd.DataFrame] = []
        network_frames: list[pd.DataFrame] = []
        reserve_family_frames: list[pd.DataFrame] = []
        hydro_cascade_frames: list[pd.DataFrame] = []

        for label, res in labelled:
            passes_seen.add(label)
            _dispf = _dispatch_frame(
                year,
                label,
                res,
                context,
                zone_names,
                iso=iso,
                must_run=must_run,
                oil_switch_mask=p2_state.get("dual_fuel_oil_mask"),
            )
            _sysf = _system_frame(
                year,
                label,
                res,
                demand,
                zone_names,
                iso=iso,
                ercot_rtordpa_overlay=ercot_rtordpa_overlay,
                ercot_dam_as_overlay=ercot_dam_as_overlay,
                ercot_dam_as_overlay_from_year=ercot_dam_as_overlay_from_year,
                ercot_dam_as_scarcity_threshold=ercot_dam_as_scarcity_threshold,
                ercot_reserve_supply_cap=ercot_reserve_supply_cap,
                ercot_storage_as_endogenous=ercot_storage_as_endogenous,
                ercot_ordc_total_reserve=ercot_ordc_total_reserve,
                ercot_ordc_cap_dual_adder=ercot_ordc_cap_dual_adder,
                ercot_ordc_adder_published_anchor=(ercot_ordc_adder_published_anchor),
                ercot_ordc_adder_family_counterpart=(
                    ercot_ordc_adder_family_counterpart
                ),
                ordc_voll=_ordc_voll_eff,
                # ORDC-only realized-room RTORPA: computed on the P1
                # result in run_year; None for other passes/configs.
                ercot_ordc_realized_adder=(
                    p2_state.get("ercot_ordc_realized_adder") if label == "P1" else None
                ),
            )
            if _endog_wecc:
                # caiso-110: the results pipeline is zone-blind, so the
                # endogenous WECC-West fleet + demand must be excluded from
                # CAISO's dispatch/system frames (every downstream metric
                # inherits it), and CAISO's net import re-injected from the tie
                # flow (a synthetic klass="import" row) since the West units are
                # no longer klass="import" dispatch. See _wecc_net_import_row.
                _dispf = _dispf[~_dispf["zone"].isin(_WECC_ENDOGENOUS_EXTERNAL_ZONES)]
                _imp = _wecc_net_import_row(
                    year, label, res, p2_state.get("links"), zone_names, hours
                )
                if _imp is not None:
                    _dispf = pd.concat([_dispf, _imp], ignore_index=True)
                _sysf = _sysf[~_sysf["zone"].isin(_WECC_ENDOGENOUS_EXTERNAL_ZONES)]
            _t_pq = time.perf_counter()
            _dispf.to_parquet(
                run_dir / "dispatch" / f"{year}_{label}.parquet", index=False
            )
            # Per-unit capacity listing beside the dispatch frame (miso-191,
            # PREREG-miso191 §4 witness grains): the dispatch parquet is a
            # plain long table with no FleetContext schema metadata, so a
            # capacity-grain witness (cohort pmax vs the exited MW; the leg-2
            # plant capacity deltas) has no committed basis without this.
            # Tiny (n_gen rows), gitignored with the rest of dispatch/,
            # written for every pass of every year — pure instrumentation,
            # nothing in the solve or scoring path reads it.
            pd.DataFrame(
                {
                    "unit_id": [str(u) for u in context.unit_ids],
                    "pmax_mw": np.asarray(context.pmax_mw, dtype=float),
                }
            ).to_parquet(
                run_dir / "dispatch" / f"{year}_{label}_fleet.parquet", index=False
            )
            _parquet_s += time.perf_counter() - _t_pq
            # Free the unit-hour frame the moment it is on disk. It is the
            # single largest object this loop builds — MISO 2023 measures
            # 588.9 MB (24,694,440 gen-hours x 11 cols) — and nothing reads it
            # again after this write. Without the del it stays bound to the
            # loop variable, survives the year-release block (whose del list
            # never named it) and sits under the NEXT year's fleet build and
            # LP, which is 38% of the 1.53 GB cross-year floor that makes a
            # multi-year MISO invocation OOM. Found by the release-seam frame
            # telemetry, not by inspection: miso-92, see
            # results/calibration/FINDING-miso92-solve-memory-attribution-2026-07.md.
            # `_sysf` and `campd_year` are deliberately NOT freed here — both
            # are appended to cross-year accumulators and are still live.
            del _dispf
            # Per-unit dispatch + availability cap (ask A2's D1 input) and the
            # per-link/per-group flow + duals. Built HERE, after ``_dispf`` is
            # freed, so the two large unit-hour frames never coexist.
            _unitf = _unit_hourly_frame(
                year,
                label,
                res,
                context,
                # P2 (archived path) re-bounds the fleet, so its cap series is
                # the P2 arrays' — the same selection _save_floor_arrays makes.
                (
                    p2_state.get("fleet_arrays_p2", p2_state.get("fleet_arrays"))
                    if label == "P2"
                    else p2_state.get("fleet_arrays")
                ),
                iso=iso,
            )
            if _unitf is not None:
                unit_frames.append(_unitf)
            del _unitf
            _netf = _network_frame(year, label, res, p2_state.get("links"))
            if _netf is not None:
                network_frames.append(_netf)
            del _netf
            # Per-family reserve duals + requirement + ORDC shortfall. Always
            # written when the co-opt is on (not env-gated like the npz dump
            # below): a locational reserve family's binding is not observable
            # from any other committed artifact — system.parquet's
            # reserve_price is the cross-family SUM broadcast to every zone
            # (nyiso-113 §8). Tiny (n_fam x 8,760 rows) and committable.
            _rfamf = _reserve_family_frame(
                year, label, res, p2_state.get("reserve_design"), zone_names
            )
            if _rfamf is not None:
                reserve_family_frames.append(_rfamf)
            del _rfamf
            # Hydraulic-cascade spill / pond / water value per coupled plant
            # (NWPP-36 arrays; None -> no frame on every unarmed or inert run).
            _hcf = _hydro_cascade_frame(year, label, res)
            if _hcf is not None:
                hydro_cascade_frames.append(_hcf)
            del _hcf
            system_frames.append(_sysf)
            # Reserve-dual diagnostic sidecar (MARKET_SIM_RESERVE_DUAL_DUMP,
            # default OFF): the per-family reserve balance-row duals
            # (reserve_price_by_family, (T, n_fam)) and the per-zone reserve MW
            # held (reserve_dispatch, (n_zones, T)) are NOT otherwise persisted
            # — system.parquet carries only the summed reserve_price. A
            # reserve-family probe needs an INDIVIDUAL family's dual (e.g. the
            # miso-71 Midwest family's R2/R3 fidelity reads) and its locational
            # reserve allocation (the phantom-parking read). Pure diagnostic:
            # gated default-off, writes only a SEPARATE sidecar, never touches
            # system.parquet or any scored output — the solve and every metric
            # are byte-identical whether it is on or off.
            if os.environ.get("MARKET_SIM_RESERVE_DUAL_DUMP"):
                rpf = getattr(res, "reserve_price_by_family", None)
                rd = getattr(res, "reserve_dispatch", None)
                if rpf is not None or rd is not None:
                    diag_dir = run_dir / "reserve_diag"
                    diag_dir.mkdir(parents=True, exist_ok=True)
                    np.savez(
                        diag_dir / f"{year}_{label}.npz",
                        reserve_price_by_family=(
                            np.asarray(rpf, dtype=float)
                            if rpf is not None
                            else np.zeros((0, 0))
                        ),
                        reserve_dispatch=(
                            np.asarray(rd, dtype=float)
                            if rd is not None
                            else np.zeros((0, 0))
                        ),
                        zone_names=np.array(list(zone_names), dtype=object),
                    )
            storage_frame = _storage_frame(year, label, res, p2_state["storage_units"])
            if storage_frame is not None:
                storage_frames.append(storage_frame)
            posture_frame = _posture_frame(year, label, res, zone_names)
            if posture_frame is not None:
                posture_frames.append(posture_frame)
            flows_frame = _flows_frame(year, label, res, p2_state.get("links"))
            if flows_frame is not None:
                flows_frames.append(flows_frame)
            # G5 validation: the modeled-vs-measured battery AS-vs-energy split
            # (ERCOT endogenous storage AS). Off otherwise (no extra frame).
            if ercot_storage_as_endogenous and iso == "ERCOT":
                sas = _storage_as_frame(
                    year, label, res, p2_state["storage_units"], zone_names
                )
                if sas is not None:
                    storage_as_frames.append(sas)
            # BTM CHP host self-supply is held out of the LP for ALL ISOs, so
            # write btm.parquet for every ISO (not just ERCOT) — render
            # subtracts it from EIA-923 to score the model on the same
            # grid-delivered basis. The bin source is ISO-specific inside
            # _btm_frame (curated sheet for ERCOT, EIA-860 fleet otherwise).
            # Sized from measured inputs only (923 class totals × measured
            # host shares), never from this pass's dispatch — the frame is
            # identical across passes and re-solves (rule #13).
            btm_frames.append(
                _btm_frame(
                    year,
                    label,
                    generation,
                    btm_backfill_year=btm_backfill_year,
                    campd_active=campd_active,
                    iso=iso,
                    group_by_code=group_by_code,
                    nyiso_chp_btm_measured=bool(nyiso_chp_btm_measured),
                )
            )

        _t_frames_done = time.perf_counter()

        e930 = e930_year
        if e930 is not None:
            eia930_frames.append(e930)
        if has_campd:
            eia923_frames.append(
                _benchmark_eia923_frame(
                    year,
                    generation,
                    iso,
                    campd_year,
                    group_by_code,
                    e930,
                    # Mirror the BTM repair onto the benchmark: `classFull` is
                    # this frame minus btm.parquet, so repairing only the
                    # subtrahend can drive a metered class volume negative
                    # (PJM 2025 CT_CHP, pjm-129 §6 / pjm-130).
                    btm_backfill_year=btm_backfill_year,
                    campd_active=campd_active,
                    # Same seam as the injection above, so bench and model move
                    # in lockstep (miso-253).
                    mustrun_chp_btm_holdout=_mustrun_chp_btm,
                    benchmark_membership_vintage_union=_bench_vintage_union,
                )
            )
            if campd_year is not None:
                campd_frames.append(campd_year)

        _t_bench_done = time.perf_counter()

        # Committable hourly/ sidecars (class / class-band / storage / unit /
        # network / reserve-family, plus the opt-in and flag-gated audit
        # series). They ran AFTER the phase-timing line until wallclock A-3,
        # so ~28 s/yr (NEISO) sat between one year's ``_t_end`` and the next
        # year's ``_t_year`` — booked to no phase and no year's ``total``. They
        # now close the results_write window as its ``sidecars`` part.
        _write_class_hourly_sidecar(run_dir, year, [lbl for lbl, _ in labelled])
        _write_class_band_hourly_sidecar(run_dir, year, [lbl for lbl, _ in labelled])
        _write_p0_commitment_sidecar(run_dir, year, p2_state)
        _write_p0_dispatch_sidecar(run_dir, year, p2_state)
        _write_storage_hourly_sidecar(run_dir, year, storage_frames)
        _write_hourly_sidecar(run_dir, year, "unit_hourly", unit_frames)
        _write_hourly_sidecar(run_dir, year, "network", network_frames)
        _write_hourly_sidecar(run_dir, year, "reserve_family", reserve_family_frames)
        _write_hourly_sidecar(run_dir, year, "hydro_cascade", hydro_cascade_frames)
        # ercot-219 stage-2 exhaustion series (ercot_exhaustion_expectation):
        # H margin / sequestered AS / LOLP(H) / within-day P_exhaust — the
        # committed audit trail for G-EXH and the stage-3 offer (PRECOMMIT-
        # ercot219 §3.1). Absent (no file) on every flag-off run.
        _exh = p2_state.get("ercot219_exhaustion")
        if _exh is not None:
            _t_exh = len(_exh["lolp"])
            _exhf = pd.DataFrame(
                {
                    "year": np.full(_t_exh, year, dtype=np.int32),
                    "hour": np.arange(_t_exh, dtype=np.int32),
                    "h_margin_mw": np.asarray(_exh["h_margin_mw"], dtype=float),
                    "as_sequestered_mw": np.asarray(
                        _exh["as_sequestered_mw"], dtype=float
                    ),
                    "lolp": np.asarray(_exh["lolp"], dtype=float),
                    "p_exhaust": np.asarray(_exh["p_exhaust"], dtype=float),
                }
            )
            _write_hourly_sidecar(run_dir, year, "exhaustion", [_exhf])
        # ercot-221 adaptive-expectation series (ercot_storage_adaptive_
        # expectation): the pass-1 model spike indicator, daily P_hat
        # (broadcast hourly) and the applied evening-window floor — the
        # committed audit trail for the mechanism's A/B gates (PRECOMMIT-
        # ercot221 §4). Absent (no file) on every flag-off run.
        # caiso-205: the CAISO leg writes the same audit columns under its
        # own p2_state key; at most one of the two can fire per solve (each
        # is iso-gated), so the first non-None dict is the year's series.
        _ada = p2_state.get("ercot221_adaptive") or p2_state.get("caiso205_adaptive")
        if _ada is not None:
            _t_ada = len(_ada["floor_t"])
            _day_idx = np.minimum(np.arange(_t_ada) // 24, len(_ada["p_hat"]) - 1)
            _adaf = pd.DataFrame(
                {
                    "year": np.full(_t_ada, year, dtype=np.int32),
                    "hour": np.arange(_t_ada, dtype=np.int32),
                    "s_model_day": np.asarray(_ada["s_model"], dtype=float)[_day_idx],
                    "p_hat_day": np.asarray(_ada["p_hat"], dtype=float)[_day_idx],
                    "floor_usd": np.asarray(_ada["floor_t"], dtype=float),
                }
            )
            _write_hourly_sidecar(run_dir, year, "adaptive", [_adaf])
        # ercot-230 fixed-point iteration trajectory (ercot_adaptive_fixed_
        # point): per-pass spike days, floored/released window-hour counts,
        # floor hashes and the stop reason — the committed audit record of
        # the iteration's convergence (PRECOMMIT-ercot230-adaptive-fixed-
        # point-2026-08-23.md §1). Absent (no file) on every flag-off run.
        _fpj = p2_state.get("ercot230_iteration")
        if _fpj is not None:
            _fp_dir = run_dir / "hourly"
            _fp_dir.mkdir(parents=True, exist_ok=True)
            (_fp_dir / f"adaptive_iteration_{year}.json").write_text(
                json.dumps(_fpj, indent=1) + "\n"
            )

        _t_end = time.perf_counter()
        _ti = p2_state.get("_timing", {})
        # The three subtrahends are summed by run_year over EVERY energy-solve
        # pass of the year and EVERY matrix build of each pass (PERF-B session
        # 3, charter C-2; run_calibration._aggregate_pass_timing). ``markup``
        # is therefore the genuine non-solve, non-build residual — before that
        # it carried every earlier adaptive pass's build and both HiGHS runs.
        _solve_p0 = _ti.get("solve_p0_s", 0.0)
        _solve_p1 = _ti.get("solve_p1_s", 0.0)
        _build = _ti.get("build_s", 0.0)
        _energy = _ti.get("energy_solve_s", 0.0)
        _markup = max(0.0, _energy - _build - _solve_p0 - _solve_p1)
        _results_write = _t_end - _t_post_solve
        _total = _t_end - _t_year
        _data_prep = _total - _solve_p0 - _markup - _solve_p1 - _results_write
        # Disjoint, exhaustive segments of the results_write window, so
        # state + frames + parquet + bench + sidecars == _results_write exactly:
        #   state   — p2_state pickle + per-pass min-gen floor arrays
        #   bench   — CAMPD hourly + the EIA-923/930 benchmark frames (scoring)
        #   parquet — the per-pass dispatch parquet writes (accumulated in-loop)
        #   frames  — everything else in the per-pass loop (frame construction)
        #   sidecars— the committable hourly/ sidecar writes (wallclock A-3)
        _bench_s = (_t_campd_done - _t_state_done) + (_t_bench_done - _t_frames_done)
        _frames_s = (_t_frames_done - _t_campd_done) - _parquet_s
        _sidecars_s = _t_end - _t_bench_done
        # markup sub-instrumentation (PERF-B session 2): ``markup`` is a
        # residual, not a phase, so the components come from inside
        # ``run_energy_solve`` (pipeline/solve.py) and are exhaustive over its
        # interior. ``other`` books the remainder — this frame's call/return
        # edges around that function — so the clause sums to ``_markup``
        # exactly. It reads negative only if the ``max(0.0, ...)`` clamp above
        # fired, which is itself the signal worth seeing.
        _markup_parts = dict(_ti.get("markup_parts") or {})
        if _markup_parts:
            _markup_parts["other"] = _markup - sum(_markup_parts.values())
        log_year_phase_timing(
            logger,
            year,
            data_prep=_data_prep,
            solve_p0=_solve_p0,
            markup=_markup,
            solve_p1=_solve_p1,
            results_write=_results_write,
            total=_total,
            markup_parts=_markup_parts,
            results_write_parts={
                "state": _t_state_done - _t_post_solve,
                "frames": _frames_s,
                "parquet": _parquet_s,
                "bench": _bench_s,
                "sidecars": _sidecars_s,
            },
        )

        # Release this year's solve state before the next year allocates its
        # own LP. A PJM per-plant year peaks ~13 GB inside HiGHS; carrying the
        # previous year's result/context/P2-state into the next build pushed a
        # 3-year backcast past 16 GB and into the OOM killer. Only the compact
        # per-year frames accumulated above survive the loop.
        del result, context, result_p1, p2_state, demand, must_run
        del must_run_total, labelled, res
        del unit_frames, network_frames, reserve_family_frames, hydro_cascade_frames
        gc.collect()
        # Hand the freed solve heap back to the kernel. gc.collect() returns the
        # LP's memory to glibc, but glibc holds large fragmented arenas instead
        # of unmapping them, so without this the next year's build starts on top
        # of the previous year's high-water RSS. Frees only already-free heap —
        # it cannot touch a live object, so dispatch is byte-identical.
        _trimmed = _malloc_trim()
        # Post-release memory telemetry. ``resident`` is what this year actually
        # handed on to the next one; ``peak`` is the process high-water mark. A
        # resident figure that climbs year over year is retained state (an
        # unbounded per-year cache, an accumulating frame), which is what pushes
        # a multi-year invocation into the OOM killer even though the year loop
        # is strictly sequential. Logged, never enforced.
        _rss_kb, _hwm_kb = _proc_mem_kb()
        if _rss_kb:
            # Footprint of the cross-year accumulators, so the resident figure
            # can be attributed instead of guessed: these lists are the only
            # per-year state the loop deliberately keeps, and their total is
            # what a spill-to-disk change would have to move.
            _acc = {
                "system": system_frames,
                "eia930": eia930_frames,
                "eia923": eia923_frames,
                "campd": campd_frames,
                "btm": btm_frames,
                "storage": storage_frames,
                "posture": posture_frames,
                "flows": flows_frames,
            }
            _sizes = {
                name: sum(
                    float(f.memory_usage(deep=True).sum())
                    for f in frames
                    if f is not None
                )
                / 1073741824.0
                for name, frames in _acc.items()
            }
            logger.info(
                "year %d memory after release: resident=%.2f GB peak=%.2f GB "
                "(malloc_trim=%s) | accumulators %.2f GB (%s)",
                year,
                _rss_kb / 1048576.0,
                _hwm_kb / 1048576.0,
                "yes" if _trimmed else "no",
                sum(_sizes.values()),
                " ".join(
                    f"{n}={v:.2f}"
                    for n, v in sorted(_sizes.items(), key=lambda kv: -kv[1])
                    if v >= 0.01
                ),
            )
            # Attribute the resident figure instead of leaving it a mystery.
            # Successive sessions guessed at what the cross-year floor was made
            # of — the ~26 module lru_cache memoizations were the standing
            # hypothesis until miso-90 measured them at ~0.02 GB on the MISO
            # path, i.e. near-inert. This logs the live array/frame payload and
            # the populated-cache census every year so the next attempt starts
            # from a measurement. Diagnostic only: it allocates nothing the
            # solve depends on and can never change dispatch.
            try:
                from market_sim.data.cache_control import (
                    cache_report,
                    largest_retained_frames,
                    retained_footprint,
                )

                # The accumulators live in THIS function's locals, which are
                # not reachable from the GC graph (CPython 3.11 lazy frames),
                # so they must be passed as explicit roots.
                _fp = retained_footprint(*_acc.values())
                _caches = cache_report()
                # Complementary half of the attribution: whatever resident is
                # NOT live Python payload is either memory glibc is holding
                # free (fragmentation — an arena-tuning fix) or memory a C++
                # allocator still owns (HiGHS surviving the Python-side del —
                # a destroy-the-model fix). Those two need opposite responses,
                # so logging only the Python side would leave the next session
                # guessing again. Read-only; cannot change dispatch.
                _arena = _glibc_arena_gb()
                if _arena:
                    logger.info(
                        "year %d glibc arena: total=%.2f GB in_use=%.2f GB "
                        "free_retained=%.2f GB mmapped=%.2f GB trim_top=%.2f GB",
                        year,
                        _arena["arena"],
                        _arena["in_use"],
                        _arena["free_in_arena"],
                        _arena["mmapped"],
                        _arena["trim_top"],
                    )
                logger.info(
                    "year %d retained heap: ndarray=%.2f GB (n=%d) "
                    "[pandas=%.2f GB n=%d, sparse=%.2f GB n=%d — slices, not "
                    "additions] | %d populated cache(s), %d entries%s",
                    year,
                    _fp.get("ndarray_gb", 0.0),
                    int(_fp.get("n_ndarray", 0)),
                    _fp.get("pandas_gb", 0.0),
                    int(_fp.get("n_pandas", 0)),
                    _fp.get("sparse_gb", 0.0),
                    int(_fp.get("n_sparse", 0)),
                    len(_caches),
                    sum(c.currsize for c in _caches),
                    (
                        " | top: "
                        + ", ".join(
                            f"{c.qualname.rsplit('.', 1)[-1]}={c.currsize}"
                            for c in _caches[:5]
                        )
                        if _caches
                        else ""
                    ),
                )
                # Name the holding SITE, not just the class. miso-92 measured
                # 0.68 GB across only 17 frames here, of which the accumulators
                # explain 0.07 and the module caches ~0.02 — so ~0.59 GB sat in
                # large frames nobody could point at. A frame's column list
                # identifies its producer on sight.
                _frames = largest_retained_frames(6, *_acc.values())
                for _mb, _rows, _ncol, _cols in _frames:
                    logger.info(
                        "year %d retained frame: %.1f MB  %d x %d  cols=%s",
                        year,
                        _mb,
                        _rows,
                        _ncol,
                        ",".join(_cols),
                    )
                # A quiet reporter and a broken one look identical in a log, and
                # this one WAS broken once (DataFrame-only, so it printed nothing
                # against 17 live pandas objects). Make the disagreement loud
                # rather than let a later reader mistake silence for "nothing
                # retained".
                if not _frames and int(_fp.get("n_pandas", 0)) > 0:
                    logger.warning(
                        "year %d retained-frame telemetry returned NOTHING while "
                        "retained_footprint counted %d pandas object(s) / %.2f GB "
                        "— the two reporters disagree; treat the frame list as "
                        "unreliable for this run",
                        year,
                        int(_fp.get("n_pandas", 0)),
                        _fp.get("pandas_gb", 0.0),
                    )
            except Exception:  # never let telemetry break a calibration run
                logger.warning(
                    "year %d retained-heap telemetry unavailable", year, exc_info=True
                )

    system_all = pd.concat(system_frames, ignore_index=True)
    system_all.to_parquet(run_dir / "system.parquet", index=False)
    _write_system_year_sidecars(run_dir, system_all)
    if flows_frames:
        pd.concat(flows_frames, ignore_index=True).to_parquet(
            run_dir / "flows.parquet", index=False
        )
    if posture_frames:
        pd.concat(posture_frames, ignore_index=True).to_parquet(
            run_dir / "posture.parquet", index=False
        )
    # campd / eia930 / eia923 are deterministic input/benchmark frames shared
    # across an ISO's runs — write them once to the content-addressed shared
    # store and reference them from meta.json instead of duplicating ~6 MB into
    # every bundle. Run outputs (system/dispatch/storage/btm) stay in-bundle.
    shared_inputs: dict[str, str] = {}
    if eia930_frames:
        shared_inputs["eia930"] = write_shared_input(
            pd.concat(eia930_frames, ignore_index=True), "eia930", iso, run_dir
        )
    if eia923_frames:
        shared_inputs["eia923"] = write_shared_input(
            pd.concat(eia923_frames, ignore_index=True), "eia923", iso, run_dir
        )
    if btm_frames:
        pd.concat(btm_frames, ignore_index=True).to_parquet(
            run_dir / "btm.parquet", index=False
        )
    if campd_frames:
        shared_inputs["campd"] = write_shared_input(
            pd.concat(campd_frames, ignore_index=True), "campd", iso, run_dir
        )
    # Derived solve inputs (per-ISO unit-outage extract family + the clean
    # capacity-deliverability partition): pinned into the same store so the
    # bundle records the exact bytes it solved on — the two inputs a bundle
    # previously recorded nothing about (FINDING-caiso124 §7; the caiso-123
    # non-reproducible-extract incident and the RESULTS-neiso65 §2
    # silent-degrade trap). Provenance only — replay ignores shared_inputs.
    try:
        shared_inputs.update(write_derived_solve_inputs(iso, run_dir))
    except Exception:  # provenance capture must never fail a solve
        logger.warning("derived solve-input capture failed", exc_info=True)
    if storage_frames:
        pd.concat(storage_frames, ignore_index=True).to_parquet(
            run_dir / "storage.parquet", index=False
        )
    if storage_as_frames:
        pd.concat(storage_as_frames, ignore_index=True).to_parquet(
            run_dir / "storage_as.parquet", index=False
        )
    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "iso": iso,
        "years": years,
        "hours": hours,
        "passes": sorted(passes_seen),
        "commitment": commitment,
        "commitment_screen_coal": screen_coal,
        "gas_prices": gas_prices,
        "coal_lignite_mustrun": coal_lignite_mustrun,
        "coal_prb_mustrun": coal_prb_mustrun,
        "coal_prb_passthrough": coal_prb_passthrough,
        "outage_source": outage_source,
        "coal_prb_passthrough_sigmoid": coal_prb_passthrough_sigmoid,
        "coal_mustrun_per_plant": coal_mustrun_per_plant,
        "retiree_cems_cap": retiree_cems_cap,
        "ct_mustrun_per_plant": ct_mustrun_per_plant,
        "ct_mustrun_floor_frac": ct_mustrun_floor_frac,
        "coal_drop_pof": coal_drop_pof,
        "coal_mustrun_online_pmin": coal_mustrun_online_pmin,
        "coal_sync_srmc_tranche": coal_sync_srmc_tranche,
        "ct_intermediate_split": ct_intermediate_split,
        "ct_intermediate_cf_threshold": ct_intermediate_cf_threshold,
        "cc_intermediate_split": cc_intermediate_split,
        "cc_intermediate_cf_threshold": cc_intermediate_cf_threshold,
        "tranche_startup_amortization": tranche_startup_amortization,
        "tranche_startup_measured_runs": tranche_startup_measured_runs,
        "tranche_startup_conditional_runs": tranche_startup_conditional_runs,
        "gas_offer_margin": gas_offer_margin,
        "gas_offer_margin_zonal_anchor": gas_offer_margin_zonal_anchor,
        "coal_offer_margin": coal_offer_margin,
        "cc_committed_offer_margin": cc_committed_offer_margin,
        "coal_peak_offer_margin": coal_peak_offer_margin,
        "coal_peak_offer_yearly_level": coal_peak_offer_yearly_level,
        "coal_perplant_offer_level": coal_perplant_offer_level,
        "coal_perplant_offer_yearly": coal_perplant_offer_yearly,
        "nysdec_peaker_rule_availability": nysdec_peaker_rule_availability,
        "nyiso_solar_market_generator_basis": nyiso_solar_market_generator_basis,
        "oil_primary_bin_fuel": oil_primary_bin_fuel,
        "st_gas_intermediate": st_gas_intermediate,
        "st_gas_intermediate_cf_threshold": st_gas_intermediate_cf_threshold,
        "coal_prb_passthrough_tiered": coal_prb_passthrough_tiered,
        "coal_prb_sigmoid_overrides": {
            k: v for k, v in (prb_overrides or {}).items() if v is not None
        },
        "coal_bit_passthrough_sigmoid": coal_bit_sigmoid,
        "coal_bit_sigmoid_overrides": {
            k: v for k, v in (bit_overrides or {}).items() if v is not None
        },
        "coal_econ_srmc_bound": coal_econ_srmc_bound,
        "coal_econ_marginal_hr_bound": coal_econ_marginal_hr_bound,
        "ercot_offer_hrmult_ep_rebasis": ercot_offer_hrmult_ep_rebasis,
        "ercot_offer_hrmult_ep_rebasis_bands": ercot_offer_hrmult_ep_rebasis_bands,
        "coal_plant_monthly_pricing": first_year_cfg.coal_plant_monthly_pricing,
        # EFFECTIVE td_loss_factor, not the pristine cfg's — the same
        # prb_overrides resolution the demand-threading site applies
        # (nyiso-87). Reading first_year_cfg here recorded 0.0 while
        # run_year's own config recorded the armed value in
        # scenario_config, so a --set probe's run_config.json disagreed
        # with itself about what solved (rule 24).
        "td_loss_factor": (
            float(prb_overrides["td_loss_factor"])
            if (prb_overrides or {}).get("td_loss_factor") is not None
            else first_year_cfg.td_loss_factor
        ),
        # ERCOT gas-basis mechanisms: env-var-gated inside backcast_config
        # (ERCOT_ZONAL_GAS / ERCOT_WEST_NETLOAD_GAS / ERCOT_GAS_FLOOR /
        # ERCOT_WEST_GAS_DELIVERED_FLOOR — no solve_and_persist kwarg exists
        # for them, rule 24 exception, plan §4). Meta-writer audit fix
        # (orchestrator-unification Stage 7): record the EFFECTIVE resolved
        # value the same way as coal_plant_monthly_pricing/td_loss_factor
        # above, so a run whose environment enabled one of these probes has
        # it in the reproducibility record instead of silently escaping it.
        "ercot_zonal_gas_basis": first_year_cfg.ercot_zonal_gas_basis,
        "ercot_west_netload_gas_shape": first_year_cfg.ercot_west_netload_gas_shape,
        "ercot_west_gas_delivered_floor": first_year_cfg.ercot_west_gas_delivered_floor,
        "storage_daily_cycling": storage_daily_cycling,
        "storage_vintage_ramp": storage_vintage_ramp,
        "strict_demand_profile": strict_demand_profile,
        "battery_dispatch_adder": battery_dispatch_adder,
        "as_reserve_withholding": as_reserve_withholding,
        "energy_reserve_coopt": energy_reserve_coopt,
        "miso_zonal_reserves": miso_zonal_reserves,
        "miso_midwest_subregional_reserves": miso_midwest_subregional_reserves,
        "miso_reserve_pergen": miso_reserve_pergen,
        "miso_commitment_posture": miso_commitment_posture,
        "miso_reserve_online_gated": miso_reserve_online_gated,
        "miso_measured_reserve_requirements": miso_measured_reserve_requirements,
        "miso_south_seam_split": miso_south_seam_split,
        "miso_rdt_tcdc": miso_rdt_tcdc,
        "miso_zonal_loss_surface": miso_zonal_loss_surface,
        "pjm_zonal_loss_surface": pjm_zonal_loss_surface,
        "ercot_multiproduct_as_coopt": ercot_multiproduct_as_coopt,
        "ercot_ecrs_conservative_deployment": ercot_ecrs_conservative_deployment,
        "ercot_nonreleasable_as_withholding": ercot_nonreleasable_as_withholding,
        "ercot_ordc_total_reserve": ercot_ordc_total_reserve,
        "ercot_ordc_cap_dual_adder": ercot_ordc_cap_dual_adder,
        "ercot_ordc_adder_published_anchor": ercot_ordc_adder_published_anchor,
        "ercot_ordc_adder_family_counterpart": ercot_ordc_adder_family_counterpart,
        "ercot_storage_as_product_credit": ercot_storage_as_product_credit,
        "gas_hh_monthly_shape": gas_hh_monthly_shape,
        "ercot_as_aware_commitment": ercot_as_aware_commitment,
        "ercot_reserve_supply_cap": ercot_reserve_supply_cap,
        "ercot_reserve_supply_cap_from_year": ercot_reserve_supply_cap_from_year,
        "ercot_reserve_supply_forward": ercot_reserve_supply_forward,
        "pjm_reserve_supply_cap": pjm_reserve_supply_cap,
        "pjm_reserve_online_gated": pjm_reserve_online_gated,
        "pjm_reserve_online_rho": pjm_reserve_online_rho,
        "pjm_reserve_commitment_scoped": pjm_reserve_commitment_scoped,
        "pjm_reserve_pergen": pjm_reserve_pergen,
        "pjm_reserve_pergen_sync": pjm_reserve_pergen_sync,
        "pjm_reserve_pergen_size_split": pjm_reserve_pergen_size_split,
        "pjm_commitment_posture": pjm_commitment_posture,
        "measured_ramp_capability": measured_ramp_capability,
        "ercot_as_forward_requirement": ercot_as_forward_requirement,
        "ercot_load_resource_reserve": ercot_load_resource_reserve,
        "ercot_load_resource_reserve_from_year": ercot_load_resource_reserve_from_year,
        "ercot_storage_as_reserve": ercot_storage_as_reserve,
        "ercot_storage_as_reserve_from_year": ercot_storage_as_reserve_from_year,
        "ercot_ecrs_requirement": ercot_ecrs_requirement,
        "ercot_ecrs_requirement_from_year": ercot_ecrs_requirement_from_year,
        "ercot_rtordpa_overlay": ercot_rtordpa_overlay,
        "ercot_dam_as_overlay": ercot_dam_as_overlay,
        "ercot_dam_as_overlay_from_year": ercot_dam_as_overlay_from_year,
        "ercot_dam_as_scarcity_threshold": ercot_dam_as_scarcity_threshold,
        "ordc_lolp_params_path": ordc_lolp_params_path,
        "as_reserve_formula": as_reserve_formula,
        "storage_as_commitment": storage_as_commitment,
        # ERCOT-63 meta-writer gap fix: the ercot59 keeper's defining delta was
        # threaded to run_year and recorded in run_config.json but never in
        # meta.json, so a meta-based reconstruction silently rebuilt the
        # ercot56 recipe (probes reconstruct keepers from meta, rule 15/25).
        "ercot_storage_as_deployment": ercot_storage_as_deployment,
        "ercot_storage_as_deployment_from_year": (
            ercot_storage_as_deployment_from_year
        ),
        "ercot_storage_as_endogenous": ercot_storage_as_endogenous,
        "ercot_storage_as_duration_gate": ercot_storage_as_duration_gate,
        "gas_offer_curve": gas_offer_curve,
        "gas_monthly_actuals": gas_monthly_actuals,
        "pjm_zonal_gas_basis": pjm_zonal_gas_basis,
        "miso_zonal_gas_basis": miso_zonal_gas_basis,
        "miso_winter_citygate_daily": miso_winter_citygate_daily,
        "pjm_congestion": pjm_congestion,
        "offer_curve_overrides": offer_curve_overrides or {},
        "offer_curve_deltas": offer_curve_deltas or {},
        "curve_smoothing": curve_smoothing or {},
        "cc_derate_from_top": cc_derate_from_top,
        "cc_nameplate_summer_derate": cc_nameplate_summer_derate,
        "coal_nameplate_summer_derate": coal_nameplate_summer_derate,
        "temp_dependent_derate": temp_dependent_derate,
        "temp_derate_hourly_grain": temp_derate_hourly_grain,
        "temp_derate_mean_anchored": temp_derate_mean_anchored,
        # JSON has no set type — meta carries the scope as a sorted list, which
        # ``run_year`` re-freezes. Without this the no-LP bundle reconstruction
        # (full_run_year_kwargs) would silently rebuild an UNSCOPED arm.
        "temp_derate_classes": (
            sorted(temp_derate_classes) if temp_derate_classes else None
        ),
        "temp_derate_slope_st_chp": temp_derate_slope_st_chp,
        "temp_derate_slope_ct_chp": temp_derate_slope_ct_chp,
        "ercot_offer_surface_conditional": ercot_offer_surface_conditional,
        "ercot_offer_surface_midcurve_conditional": (
            ercot_offer_surface_midcurve_conditional
        ),
        "ercot_offer_surface_cleared_share": ercot_offer_surface_cleared_share,
        "ercot_offer_surface_cleared_share_state": (
            ercot_offer_surface_cleared_share_state
        ),
        "ercot_offer_surface_cleared_share_steam": (
            ercot_offer_surface_cleared_share_steam
        ),
        "ercot_offer_surface_lowcurve": ercot_offer_surface_lowcurve,
        "ercot_offer_surface_lowcurve_floorscoped": (
            ercot_offer_surface_lowcurve_floorscoped
        ),
        "wind_ptc_vintage_offers": wind_ptc_vintage_offers,
        "neiso_offer_surface_conditional": neiso_offer_surface_conditional,
        "pjm_offer_surface_conditional": pjm_offer_surface_conditional,
        "pjm_da_virtual_bids": pjm_da_virtual_bids,
        "pjm_offer_midcurve_conditional": pjm_offer_midcurve_conditional,
        "caiso_offer_surface_measured": caiso_offer_surface_measured,
        "caiso_offer_surface_measured_ungrounded": (
            caiso_offer_surface_measured_ungrounded
        ),
        "caiso_st_gas_committed_measured": caiso_st_gas_committed_measured,
        "caiso_st_gas_peak_measured": caiso_st_gas_peak_measured,
        "caiso_ct_peaker_committed_measured": caiso_ct_peaker_committed_measured,
        "nyiso_ct_peaker_bands_measured": nyiso_ct_peaker_bands_measured,
        "nyiso_ct_peaker_committed_measured": nyiso_ct_peaker_committed_measured,
        "nyiso_st_gas_econ_bands_deleaked": nyiso_st_gas_econ_bands_deleaked,
        "caiso_offer_surface_conditional": caiso_offer_surface_conditional,
        "nearby_fuel_price_zone_donor_guard": nearby_fuel_price_zone_donor_guard,
        "fleet_state_from_eia860": fleet_state_from_eia860,
        "caiso_citygate_spot_coverage": caiso_citygate_spot_coverage,
        "pjm_offer_midcurve_segments": (
            list(pjm_offer_midcurve_segments)
            if pjm_offer_midcurve_segments is not None
            else None
        ),
        "ercot_nuclear_unit_availability": ercot_nuclear_unit_availability,
        "nuclear_unit_availability": nuclear_unit_availability,
        "ercot_thermal_dam_availability": ercot_thermal_dam_availability,
        "ercot_thermal_dam_availability_hourly": (
            ercot_thermal_dam_availability_hourly
        ),
        "ercot_thermal_dam_availability_plant": (ercot_thermal_dam_availability_plant),
        "ercot_wind_zone_shape": ercot_wind_zone_shape,
        "ercot_noncampd_plant_availability": ercot_noncampd_plant_availability,
        "ercot_storage_capability_measured": ercot_storage_capability_measured,
        "ercot_online_capacity_envelope_measured": (
            ercot_online_capacity_envelope_measured
        ),
        "ercot_ordc_only_scarcity": ercot_ordc_only_scarcity,
        "priced_interchange": priced_interchange,
        "hydro_backfill_year": hydro_backfill_year,
        "hydro_eia930_monthly": hydro_eia930_monthly,
        "hydro_budget_period_by_instrument": hydro_budget_period_by_instrument,
        "hydro_forecast_budget": hydro_forecast_budget,
        "hydro_year": hydro_year,
        "interchange_shaping": interchange_shaping,
        "interchange_shaping_export_only": interchange_shaping_export_only,
        "reference_price_interface": reference_price_interface,
        "negative_renewable_offers": negative_renewable_offers,
        "caiso_gas_commitment_floor": caiso_gas_commitment_floor,
        "caiso_gas_floor_frac": caiso_gas_floor_frac,
        "caiso_ra_mustoffer": caiso_ra_mustoffer,
        "caiso_ra_min_load_frac": caiso_ra_min_load_frac,
        "caiso_ra_startup_bridge": caiso_ra_startup_bridge,
        "caiso_ra_bridge_decommit": caiso_ra_bridge_decommit,
        "ercot_gas_commitment_bridge": ercot_gas_commitment_bridge,
        "ercot_gas_bridge_min_load_frac": ercot_gas_bridge_min_load_frac,
        "ercot_gas_bridge_startup": ercot_gas_bridge_startup,
        "ercot_gas_bridge_da_horizon": ercot_gas_bridge_da_horizon,
        "ercot_gas_bridge_online_hours": ercot_gas_bridge_online_hours,
        "ercot_commitment_posture": ercot_commitment_posture,
        "ercot_commitment_posture_min_load_frac": (
            ercot_commitment_posture_min_load_frac
        ),
        "carry_operating_mothballs": carry_operating_mothballs,
        "reliability_floor": reliability_floor,
        "reliability_floor_plant_exclusions": reliability_floor_plant_exclusions,
        # Net-load deployment drags — persisted so the legitimacy-diagnostics
        # floor reconstruction (run_year(fleet_only=True) from meta.json) applies
        # the SAME drag the solve did. Omitting them silently dropped the drag
        # from D-2/D-4 reconstruction, under-counting CT_PEAKER forced energy for
        # every drag keeper (docs/FINDING-pjm-burndown-2026-07.md). The
        # gas_st_drag_overrides key repeats that finding for the ST_GAS drag:
        # without it a --replay-bundle re-solve of a PJM drag keeper fell back
        # to the ScenarioConfig default hinge and forced ~4x the ST_GAS energy
        # the original run did (pjm-94, 2026-07-09).
        "ct_netload_drag": ct_netload_drag,
        "pjm_interface_feed_admissibility_gate": pjm_interface_feed_admissibility_gate,
        "gas_offer_margin_anchor_vintage": gas_offer_margin_anchor_vintage,
        "gas_offer_margin_zonal_anchor_vintage": gas_offer_margin_zonal_anchor_vintage,
        "gas_st_netload_drag": gas_st_netload_drag,
        "ct_drag_overrides": ct_drag_overrides or {},
        "gas_st_drag_overrides": gas_st_drag_overrides or {},
        "scarcity_price_overlay": scarcity_price_overlay,
        "caiso_scarcity_pricing": caiso_scarcity_pricing,
        "caiso_lcr_commitment_credit": caiso_lcr_commitment_credit,
        "caiso_solar_deliverability": caiso_solar_deliverability,
        "caiso_solar_deliverability_k": caiso_solar_deliverability_k,
        "caiso_solar_endogenous_spill": caiso_solar_endogenous_spill,
        "caiso_solar_cap_at_delivered": caiso_solar_cap_at_delivered,
        "neiso_gas_coldsnap_derate": neiso_gas_coldsnap_derate,
        "neiso_coldsnap_derate_dualfuel_unswitched": neiso_coldsnap_derate_dualfuel_unswitched,
        "neiso_oil_burn_budget": neiso_oil_burn_budget,
        "neiso_winter_fuel_inventory": neiso_winter_fuel_inventory,
        "neiso_winter_fuel_start_fill_bbl": neiso_winter_fuel_start_fill_bbl,
        "neiso_winter_fuel_mustrun": neiso_winter_fuel_mustrun,
        "coal_fuel_inventory": coal_fuel_inventory,
        "caiso_import_hub_prices": caiso_import_hub_prices,
        "caiso_import_gas_coupling": caiso_import_gas_coupling,
        "caiso_import_solar_shape": caiso_import_solar_shape,
        "caiso_per_hub_intertie": caiso_per_hub_intertie,
        "caiso_perhub_firm_base": caiso_perhub_firm_base,
        "caiso_corridor_flow_limit": caiso_corridor_flow_limit,
        "caiso_intertie_reference_price": caiso_intertie_reference_price,
        "caiso_corridor_atc_forward": caiso_corridor_atc_forward,
        "caiso_reference_price_seam": caiso_reference_price_seam,
        "caiso_per_year_import_caps": caiso_per_year_import_caps,
        "caiso_asymmetric_path_ratings": caiso_asymmetric_path_ratings,
        "caiso_zonal_loss_surface": caiso_zonal_loss_surface,
        "capacity_deliverability_limits": capacity_deliverability_limits,
        "unit_outage_lp_capacity_basis": unit_outage_lp_capacity_basis,
        "unit_outage_mixed_gas_routing": unit_outage_mixed_gas_routing,
        "unit_outage_st_capacity_basis": unit_outage_st_capacity_basis,
        "unit_outage_per_unit_clip": unit_outage_per_unit_clip,
        "unit_outage_short_windows_gas": unit_outage_short_windows_gas,
        "unit_outage_window_hour_grain": unit_outage_window_hour_grain,
        "campd_per_unit_attribution": campd_per_unit_attribution,
        "campd_outage_merit_order_guard": campd_outage_merit_order_guard,
        "netload_drag_layup_window_mask": netload_drag_layup_window_mask,
        "netload_drag_merit_allocation": netload_drag_merit_allocation,
        "netload_drag_min_run_persistence": netload_drag_min_run_persistence,
        "vre_curtailment_oversupply_allocation": vre_curtailment_oversupply_allocation,
        "spp_curtailment_ceiling": spp_curtailment_ceiling,
        "spp_curtail_depth_wind": spp_curtail_depth_wind,
        "cc_winter_capability_basis": cc_winter_capability_basis,
        "ramp_limits": ramp_limits,
        "local_capacity_constraints": local_capacity_constraints,
        "nyiso_local_selfsupply": nyiso_local_selfsupply,
        "nyiso_scr_edrp": nyiso_scr_edrp,
        "nyiso_scr_edrp_strike": nyiso_scr_edrp_strike,
        "nyiso_firm_imports": nyiso_firm_imports,
        "nyiso_import_reconciliation": nyiso_import_reconciliation,
        "nyiso_import_hub_prices": nyiso_import_hub_prices,
        "nyiso_iroquois_winter_spread": nyiso_iroquois_winter_spread,
        "nyiso_synchronised_reserve": nyiso_synchronised_reserve,
        "nyiso_li_locational_reserve": nyiso_li_locational_reserve,
        "nyiso_incity_commitment_obligation": nyiso_incity_commitment_obligation,
        "nyiso_east_reserve_families": nyiso_east_reserve_families,
        "reliability_floor_overrides": reliability_floor_overrides,
        "nyiso_gas_commitment_bridge": nyiso_gas_commitment_bridge,
        "spp_gas_commitment_bridge": spp_gas_commitment_bridge,
        "soco_gas_st_campaign_commitment": soco_gas_st_campaign_commitment,
        "miso_coal_night_floor": miso_coal_night_floor,
        "nyiso_gas_bridge_cc_min_load_frac": nyiso_gas_bridge_cc_min_load_frac,
        "nyiso_gas_bridge_st_min_load_frac": nyiso_gas_bridge_st_min_load_frac,
        "nyiso_gas_bridge_startup": nyiso_gas_bridge_startup,
        "nyiso_gas_bridge_da_horizon": nyiso_gas_bridge_da_horizon,
        "nyiso_gas_bridge_min_run": nyiso_gas_bridge_min_run,
        "nyiso_gas_bridge_plant_exclusions": nyiso_gas_bridge_plant_exclusions,
        "nyiso_gas_bridge_reserve_duty_exclusions": (
            nyiso_gas_bridge_reserve_duty_exclusions
        ),
        "nyiso_gas_bridge_plant_min_run": nyiso_gas_bridge_plant_min_run,
        "nyiso_gas_bridge_online_hours": nyiso_gas_bridge_online_hours,
        "nyiso_gas_bridge_state_floor_min_run": nyiso_gas_bridge_state_floor_min_run,
        "nyiso_gas_bridge_startup_aware": nyiso_gas_bridge_startup_aware,
        "nyiso_chp_btm_measured": nyiso_chp_btm_measured,
        "cc_reserve_duty_split": cc_reserve_duty_split,
        "chp_layup_duty_split": chp_layup_duty_split,
        "chp_layup_duty_curve": chp_layup_duty_curve,
        "egrid_identity_heat_rates": egrid_identity_heat_rates,
        "measured_ct_heat_rates": measured_ct_heat_rates,
        "measured_coal_heat_rates": measured_coal_heat_rates,
        "measured_st_heat_rates": measured_st_heat_rates,
        "egrid_family_heat_rates": egrid_family_heat_rates,
        "egrid_steam_collapse_heat_rates": egrid_steam_collapse_heat_rates,
        "nyiso_gas_bridge_cc_min_run_hours": nyiso_gas_bridge_cc_min_run_hours,
        "nyiso_gas_bridge_st_min_run_hours": nyiso_gas_bridge_st_min_run_hours,
        "nyiso_spin_reserve_online": nyiso_spin_reserve_online,
        "nyiso_spin_headroom_frac": nyiso_spin_headroom_frac,
        "nyiso_dynamic_reserve_requirements": nyiso_dynamic_reserve_requirements,
        "nyiso_hydro_reserve_eligible": nyiso_hydro_reserve_eligible,
        "nyiso_scr_edrp_reserve_eligible": nyiso_scr_edrp_reserve_eligible,
        "neiso_dynamic_reserve_requirements": neiso_dynamic_reserve_requirements,
        "miso_firm_imports": miso_firm_imports,
        "miso_seam_flow_limit": miso_seam_flow_limit,
        "miso_seam_flow_percentile": miso_seam_flow_percentile,
        "miso_seam_export_limit": miso_seam_export_limit,
        "miso_seam_envelope_merit_cap": miso_seam_envelope_merit_cap,
        "miso_seam_envelope_hour_ending_key": miso_seam_envelope_hour_ending_key,
        "miso_import_sil_measured_envelope": miso_import_sil_measured_envelope,
        "nyiso_seam_deliverability_envelope": nyiso_seam_deliverability_envelope,
        "nyiso_seam_par_attribution": nyiso_seam_par_attribution,
        "miso_pjm_border_anchor": miso_pjm_border_anchor,
        "miso_cc_coal_rebalance": miso_cc_coal_rebalance,
        "miso_firm_import_floor": miso_firm_import_floor,
        "miso_seam_measured_ladder": miso_seam_measured_ladder,
        "pjm_seam_flow_limit": pjm_seam_flow_limit,
        "pjm_seam_flow_percentile": pjm_seam_flow_percentile,
        "pjm_seam_export_limit": pjm_seam_export_limit,
        "pjm_seam_measured_ladder": pjm_seam_measured_ladder,
        "pjm_seam_neighbour_hourly_ladder": pjm_seam_neighbour_hourly_ladder,
        "gas_hub_basis_overlay": gas_hub_basis_overlay,
        "chp_export_floor_measured": chp_export_floor_measured,
        "ercot_gtc_limits_measured": ercot_gtc_limits_measured,
        "pjm_measured_interface_limits": pjm_measured_interface_limits,
        "committed_band_measured_basis": committed_band_measured_basis,
        "ercot_wtx_curtailment_driver": ercot_wtx_curtailment_driver,
        "ercot_wtx_curtail_depth_wind": ercot_wtx_curtail_depth_wind,
        "ercot_wtx_curtail_depth_solar": ercot_wtx_curtail_depth_solar,
        "mass_cap_enabled": mass_cap_enabled,
        "mass_cap_tons": mass_cap_tons,
        "mass_cap_program": mass_cap_program,
        "btm_backfill_year": btm_backfill_year,
        "shared_inputs": shared_inputs,
        "git_sha": _git_sha(),
        # Basis anchor for "why did this bundle's bytes move?" forensics:
        # the newest origin/main-durable ancestor of the solving tree.
        # git_sha above may die with its session branch (caiso-122 §1);
        # this field survives. replay_keeper NEVER restores it (caiso-123).
        "basis_sha": _basis_sha(),
        # Solver provenance: near-tied offer-curve plateaus (e.g. cheap-gas
        # years putting PRB committed bids on top of gas committed bids)
        # admit alternate optimal vertices, and different HiGHS releases
        # pick different ones — class TWh can move several TWh at an
        # identical objective. Record the version so a non-reproducing
        # bundle can be traced to a solver upgrade.
        "highspy_version": _highspy_version(),
        # Full runtime environment (python/platform + numerics stack versions).
        # replay_keeper warns on a mismatch; --reuse-solved ignores this block.
        "environment": _environment_block(),
    }
    if reuse_record is not None:
        # --reuse-solved labeling (only ever present when the flag was
        # passed; a plain fresh run's meta.json is byte-identical to before
        # the flag existed). replay_keeper._IGNORE carries "reuse" so a
        # kwargs replay of a mixed bundle still reconstructs — the recipe is
        # complete and a replay re-solves every year fresh.
        meta["reuse"] = reuse_record
    (run_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, default=_json_default)
    )
    # Rebuild the recorded config WITH the same overrides + deltas applied, so
    # run_config.json's scenario_config.offer_curve_by_group is the exact
    # merged curve the LP solved against (not the bare defaults).
    recorded_cfg = _recorded_config(years[0])
    write_run_config(run_dir, recorded_cfg, meta, note, ablation_of=ablation_of)
    logger.info("wrote calibration bundle to %s", run_dir)
    # The honest peak: a run that FINISHED reports how much it really needed
    # (cgroup RSS, and RSS+swap where the kernel exposes it). An OOM-killed run
    # can only ever report the ceiling.
    log_peak_memory(log=logger)
    return run_dir


# ---------------------------------------------------------------------------
# Report — computed entirely from the persisted bundle
# ---------------------------------------------------------------------------


def _class_hourly(dispatch: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return ``{class: (T,) MW}`` from a year-pass dispatch frame."""
    piv = (
        dispatch.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack("klass", fill_value=0.0)
        .sort_index()
    )
    return {cls: piv[cls].to_numpy(dtype=float) for cls in piv.columns}


def _e923_annual(e923: pd.DataFrame) -> dict[str, float]:
    """Return ``{class: TWh}`` of EIA-923 annual net generation."""
    s = e923.groupby("klass")["annual_mwh"].sum() / _MWH_PER_TWH
    return {k: float(v) for k, v in s.items()}


def _e923_monthly(e923: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return ``{class: (12,) MWh}`` of EIA-923 monthly net generation."""
    cols = [f"m{i:02d}" for i in range(1, 13)]
    g = e923.groupby("klass")[cols].sum()
    return {k: g.loc[k].to_numpy(dtype=float) for k in g.index}


def _print_chp(year, model_twh, btm, e923_annual) -> float:
    """[1] The one table where CHP appears. Returns CHP grid-delivered TWh."""
    print(
        f"\n  [1] CHP — {year}  (model grid LP + behind-meter must-run "
        "vs EIA-923 total)"
    )
    rows = [("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %")]
    tg = tb = te = 0.0
    for cls in _CHP_CLASSES:
        grid = model_twh.get(cls, 0.0)
        b = btm.get(cls, 0.0)
        m = grid + b
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append(
            (
                cls,
                f"{grid:7.2f}",
                f"{b:6.2f}",
                f"{m:8.2f}",
                f"{e:7.2f}",
                f"{diff:+6.1f}" if e else "    —",
            )
        )
        tg += grid
        tb += b
        te += e
    tm = tg + tb
    rows.append(
        (
            "TOTAL",
            f"{tg:7.2f}",
            f"{tb:6.2f}",
            f"{tm:8.2f}",
            f"{te:7.2f}",
            f"{100.0 * (tm - te) / te:+6.1f}" if te else "—",
        )
    )
    _print_table(rows)
    print(
        "    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded "
        "from every table below.)"
    )
    return tg


def _print_reconciliation(
    year,
    net_gen,
    model_target,
    model_grid,
    unserved,
    btm_total,
) -> None:
    """[2] Grid generation reconciliation — model grid vs EIA-930 net gen."""
    gap = model_grid - net_gen
    print(f"\n  [2] Grid generation reconciliation — {year}")
    rows = [
        ("EIA-930 net generation (Demand + Interchange)", f"{net_gen:7.2f} TWh"),
        ("Model demand target", f"{model_target:7.2f} TWh"),
        ("Model grid generation (LP)", f"{model_grid:7.2f} TWh"),
        ("Gap (model grid − EIA-930 net gen)", f"{gap:+7.2f} TWh"),
        ("Unserved energy / load slack (should be 0)", f"{unserved:7.4f} TWh"),
        (
            "Behind-meter CHP must-run (off-grid; table [1] only)",
            f"{btm_total:7.2f} TWh",
        ),
    ]
    width = max(len(r[0]) for r in rows)
    for label, val in rows:
        print(f"    {label.ljust(width)}  {val}")


def _print_nonchp_grid(year, model_hourly, e930, chp_grid_twh) -> None:
    """[3] Non-CHP grid generation vs EIA-930 (CHP excluded both sides)."""
    coal_m = (
        sum(model_hourly.get(c, np.zeros(1)).sum() for c in _COAL_CLASSES)
        / _MWH_PER_TWH
    )
    gas_m = (
        sum(model_hourly.get(c, np.zeros(1)).sum() for c in _NONCHP_GAS) / _MWH_PER_TWH
    )
    nuc_m = model_hourly.get("nuclear", np.zeros(1)).sum() / _MWH_PER_TWH
    wind_m = model_hourly.get("wind", np.zeros(1)).sum() / _MWH_PER_TWH
    solar_m = model_hourly.get("solar", np.zeros(1)).sum() / _MWH_PER_TWH

    series = [
        ("gas (non-CHP)", gas_m, e930["gas"].sum() / _MWH_PER_TWH - chp_grid_twh),
        ("coal", coal_m, e930["coal"].sum() / _MWH_PER_TWH),
        ("nuclear", nuc_m, e930.get("nuclear", np.zeros(1)).sum() / _MWH_PER_TWH),
        ("wind", wind_m, e930["wind"].sum() / _MWH_PER_TWH),
        ("solar", solar_m, e930["solar"].sum() / _MWH_PER_TWH),
    ]
    model_total = sum(m for _, m, _ in series)
    eia_total = sum(b for _, _, b in series)
    print(
        f"\n  [3] Non-CHP grid generation — {year}  (model LP vs EIA-930, CHP excluded)"
    )
    rows = [("fuel", "model TWh", "model %", "EIA-930 TWh", "EIA-930 %", "Δpp")]
    for fuel, m, b in series:
        mp = 100.0 * m / model_total if model_total else 0.0
        bp = 100.0 * b / eia_total if eia_total else 0.0
        rows.append(
            (
                fuel,
                f"{m:8.2f}",
                f"{mp:6.1f}",
                f"{b:8.2f}",
                f"{bp:6.1f}",
                f"{mp - bp:+6.1f}",
            )
        )
    rows.append(
        (
            "TOTAL",
            f"{model_total:8.2f}",
            " 100.0",
            f"{eia_total:8.2f}",
            " 100.0",
            "      ",
        )
    )
    _print_table(rows)
    print(
        f"    (EIA-930 non-CHP gas = EIA-930 all-gas − {chp_grid_twh:.1f} TWh "
        "model CHP grid-delivered.)"
    )


def _print_thermal_annual(year, model_twh, btm, e923_annual) -> None:
    """[3b] Every thermal class (coal split) — model + BTM vs EIA-923."""
    print(
        f"\n  [3b] Thermal by class — {year}  (model grid LP + behind-meter "
        "must-run vs EIA-923 total; coal split lignite/PRB)"
    )
    rows = [("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %")]
    tg = tb = tm = te = 0.0
    for cls in _THERMAL_CLASSES:
        grid = model_twh.get(cls, 0.0)
        b = btm.get(cls, 0.0)
        m = grid + b
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append(
            (
                cls,
                f"{grid:7.2f}",
                f"{b:6.2f}",
                f"{m:8.2f}",
                f"{e:7.2f}",
                f"{diff:+6.1f}" if e else "    —",
            )
        )
        tg += grid
        tb += b
        tm += m
        te += e
    rows.append(
        (
            "TOTAL",
            f"{tg:7.2f}",
            f"{tb:6.2f}",
            f"{tm:8.2f}",
            f"{te:7.2f}",
            f"{100.0 * (tm - te) / te:+6.1f}" if te else "—",
        )
    )
    _print_table(rows)


# Non-fossil / residual classes surfaced in their own table: the dispatchable
# oil peaker plus the must-run injected classes (biomass, hydro, OTHER).
_NONFOSSIL_REPORT_CLASSES: tuple[str, ...] = ("oil", "biomass", "hydro", "OTHER")


def _print_nonfossil_annual(year, model_twh, e923_annual) -> None:
    """[3c] Oil / biomass / hydro / residual OTHER — model vs EIA-923."""
    print(
        f"\n  [3c] Non-fossil & residual by class — {year}  (oil = LP peaker; "
        "biomass / hydro / OTHER = must-run injected; vs EIA-923 total)"
    )
    rows = [("class", "model", "EIA-923", "diff %")]
    tm = te = 0.0
    for cls in _NONFOSSIL_REPORT_CLASSES:
        m = model_twh.get(cls, 0.0)
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append((cls, f"{m:7.2f}", f"{e:7.2f}", f"{diff:+6.1f}" if e else "    —"))
        tm += m
        te += e
    rows.append(
        (
            "TOTAL",
            f"{tm:7.2f}",
            f"{te:7.2f}",
            f"{100.0 * (tm - te) / te:+6.1f}" if te else "—",
        )
    )
    _print_table(rows)


def _print_storage(year, storage_df, e930) -> None:
    """[3d] Storage throughput — model charge/discharge vs EIA-930 battery.

    The EIA-930 battery benchmark (BAT discharge / UES charge) is NaN over
    hours the BA had not begun reporting it (ERCOT: mid-2024 onward), so the
    model is compared over the benchmark's reported window only and the
    window's coverage is printed alongside.
    """
    if storage_df is None or storage_df.empty:
        return
    by_tech = (
        storage_df.groupby("tech", observed=True)[["discharge_mw", "charge_mw"]].sum()
        / _MWH_PER_TWH
    )
    print(
        f"\n  [3d] Storage throughput — {year}  (model LP vs EIA-930 "
        "battery series where reported)"
    )
    rows = [("tech", "dis TWh", "chg TWh")]
    for tech, r in by_tech.iterrows():
        rows.append((tech, f"{r['discharge_mw']:7.2f}", f"{r['charge_mw']:7.2f}"))
    _print_table(rows)

    bench_dis = (e930 or {}).get("battery_discharge")
    if bench_dis is None:
        print("    EIA-930 battery series: not reported this year")
        return
    bench_chg = e930.get("battery_charge")
    reported = ~np.isnan(bench_dis)
    coverage = 100.0 * reported.sum() / len(bench_dis)
    # Model battery (non-PS) discharge summed over the benchmark's window.
    batt = storage_df[storage_df["tech"] != "pumped_storage"]
    hourly = (
        batt.groupby("hour", observed=True)[["discharge_mw", "charge_mw"]]
        .sum()
        .reindex(np.arange(len(bench_dis)), fill_value=0.0)
    )
    m_dis = hourly["discharge_mw"].to_numpy()[reported].sum() / _MWH_PER_TWH
    m_chg = hourly["charge_mw"].to_numpy()[reported].sum() / _MWH_PER_TWH
    a_dis = np.nansum(bench_dis) / _MWH_PER_TWH
    a_chg = (
        np.nansum(bench_chg) / _MWH_PER_TWH if bench_chg is not None else float("nan")
    )
    rows = [
        ("battery (930 window)", "model", "EIA-930", "diff %"),
        (
            "discharge TWh",
            f"{m_dis:7.2f}",
            f"{a_dis:7.2f}",
            f"{100.0 * (m_dis - a_dis) / a_dis:+6.1f}" if a_dis else "—",
        ),
        (
            "charge TWh",
            f"{m_chg:7.2f}",
            f"{a_chg:7.2f}",
            f"{100.0 * (m_chg - a_chg) / a_chg:+6.1f}" if a_chg else "—",
        ),
    ]
    _print_table(rows)
    print(f"    benchmark coverage: {coverage:.0f}% of hours reported")


def _print_monthly(
    year, model_hourly, e923_monthly, e930_solar_monthly, btm, e923_annual
) -> None:
    """[4] Monthly +/- % bias vs EIA-923 (coal split; solar vs EIA-930)."""
    print(
        f"\n  [4] Monthly bias — {year}   (% of EIA-923 per month; coal split; "
        "CHP incl. behind-meter)"
    )
    rows = [("class",) + _MONTH_NAMES]

    def _row(label, model_monthly, bench_monthly):
        cells = []
        for m in range(12):
            b = bench_monthly[m]
            cells.append(
                f"{100.0 * (model_monthly[m] - b) / b:+5.1f}" if b > 0 else "    ·"
            )
        rows.append((label,) + tuple(cells))

    for cls in _THERMAL_CLASSES:
        grid_monthly = _hourly_to_monthly(
            model_hourly.get(cls, np.zeros(_HOURS_PER_YEAR))
        )
        bench = e923_monthly.get(cls, np.zeros(12))
        btm_annual = btm.get(cls, 0.0) * _MWH_PER_TWH
        if btm_annual > 0 and bench.sum() > 0:
            model_monthly = grid_monthly + btm_annual * (bench / bench.sum())
        else:
            model_monthly = grid_monthly
        _row(cls, model_monthly, bench)
    _row(
        "wind",
        _hourly_to_monthly(model_hourly.get("wind", np.zeros(_HOURS_PER_YEAR))),
        e923_monthly.get("wind", np.zeros(12)),
    )
    _row(
        "solar (930)",
        _hourly_to_monthly(model_hourly.get("solar", np.zeros(_HOURS_PER_YEAR))),
        e930_solar_monthly,
    )
    _row(
        "nuclear",
        _hourly_to_monthly(model_hourly.get("nuclear", np.zeros(_HOURS_PER_YEAR))),
        e923_monthly.get("nuclear", np.zeros(12)),
    )
    _print_table(rows)


def _print_hourly_fit(year, model_hourly, e930, chp_grid_twh) -> None:
    """[5] Hourly Pearson r and NRMSE vs EIA-930 — non-CHP gas, coal combined."""
    print(f"\n  [5] Hourly dispatch fit — {year} (model vs EIA-930, non-CHP gas)")
    rows = [("fuel", "Pearson r", " NRMSE", "model TWh", "EIA-930 TWh")]
    # The model series follow the solved horizon, which on a partial-hours run
    # (``--hours`` below 8760) is shorter than the always-full-year EIA-930
    # observed series. Compare over the overlapping leading window so such a run
    # still reports a fit instead of crashing on a shape mismatch; for a full
    # year model and observed lengths match and the slices are no-ops.
    obs_T = e930["gas"].shape[0]
    model_T = next(
        (v.shape[0] for v in model_hourly.values() if hasattr(v, "shape")), obs_T
    )
    T = min(model_T, obs_T)
    gas_m = sum(model_hourly.get(c, np.zeros(T))[:T] for c in _NONCHP_GAS)
    coal_m = sum(model_hourly.get(c, np.zeros(T))[:T] for c in _COAL_CLASSES)
    flat_chp = chp_grid_twh * _MWH_PER_TWH / T
    nuclear_o = e930.get("nuclear")
    pairs = [
        ("gas (non-CHP)", gas_m, e930["gas"][:T] - flat_chp),
        ("coal", coal_m, e930["coal"][:T]),
        (
            "nuclear",
            model_hourly.get("nuclear", np.zeros(T))[:T],
            None if nuclear_o is None else nuclear_o[:T],
        ),
        ("solar", model_hourly.get("solar", np.zeros(T))[:T], e930["solar"][:T]),
        ("wind", model_hourly.get("wind", np.zeros(T))[:T], e930["wind"][:T]),
    ]
    for fuel, m, o in pairs:
        if o is None:
            continue
        rows.append(
            (
                fuel,
                f"{_pearson_r(m, o):.3f}",
                f"{_nrmse(m, o):.3f}",
                f"{m.sum() / _MWH_PER_TWH:8.2f}",
                f"{o.sum() / _MWH_PER_TWH:8.2f}",
            )
        )
    _print_table(rows)


def _print_plant_level(year, dispatch, e923) -> None:
    """[6] Per-plant model vs EIA-923 annual generation for the panel."""
    model_by_plant = dispatch.groupby("plant_code", observed=True)["mw"].sum().to_dict()
    class_by_plant = (
        dispatch[dispatch["plant_code"] > 0]
        .groupby("plant_code", observed=True)["klass"]
        .first()
        .to_dict()
    )
    f923_by_plant = e923.groupby("plant_id")["annual_mwh"].sum().to_dict()
    print(f"\n  [6] Plant-level annual generation — {year} (EIA-923)")
    rows = [("plant", "EIA code", "model GWh", "EIA-923 GWh", "diff %", "class")]
    for code, label in _PLANT_PANEL:
        model_gwh = model_by_plant.get(code, 0.0) / 1e3
        eia_gwh = f923_by_plant.get(code, 0.0) / 1e3
        diff = 100.0 * (model_gwh - eia_gwh) / eia_gwh if eia_gwh else float("nan")
        rows.append(
            (
                label,
                str(code),
                f"{model_gwh:9.0f}",
                f"{eia_gwh:9.0f}",
                f"{diff:+6.1f}" if eia_gwh else "    —",
                str(class_by_plant.get(code, "—")),
            )
        )
    _print_table(rows)


def _chp_btm_mw_map() -> dict[int, float]:
    """Return ``{plant_code: flat BTM MW}`` for the ERCOT CHP fleet.

    The LP dispatches only the grid-facing share of a CHP plant (the
    host-self-supply share — ``chp_btm_pct``, 35-50% of nameplate — is
    pulled out), while CAMPD measures the whole plant. Without adding the
    BTM share back, a 50%-BTM cogen can never exceed ~0.5 CF on the CAMPD
    scale and the CF-band panel reads a structural measurement asymmetry
    as a dispatch-shape miss. Petra Nova (own parasitic-load treatment,
    not a BTM cogen) is excluded.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import (
        PETRA_NOVA_PLANT_CODE,
        chp_btm_pct,
        load_campd_bins,
    )

    bins = load_campd_bins(ScenarioConfig().campd_bins_path)
    chp = bins[bins["Plant_Group"].isin(("CC_CHP", "CT_CHP", "ST_CHP"))]
    out: dict[int, float] = {}
    for _, row in chp.iterrows():
        code = int(row["Plant_Code"])
        if code <= 0 or code == PETRA_NOVA_PLANT_CODE:
            continue
        pct = chp_btm_pct(code, str(row["Plant_Group"]))
        out[code] = float(row["capacity_mw"]) * pct / 100.0
    return out


def _run_length_starts(series: np.ndarray, online_mw: float = 1.0) -> int:
    """Count off->on transitions in an hourly MW series (vectorized).

    A start is the series crossing ``online_mw`` from at-or-below to above — the
    ``campd._startup_factors`` / ``_ONLINE_MW`` convention (1 MW), applied to the
    in-memory model dispatch so the calibration bundle can persist simulated
    ``model_starts`` for the forward CO2-rate estimator's sim-conditioning. No
    Python loop over hours: a single boolean shift.
    """
    online = np.asarray(series, dtype=float) > online_mw
    if online.size == 0:
        return 0
    prev = np.concatenate([[False], online[:-1]])
    return int((online & ~prev).sum())


def _startup_co2_reporting_enabled(run_dir: Path) -> bool:
    """Return the bundle's ``startup_co2_reporting`` flag (default-OFF, R6).

    Reads the persisted ``run_config.json`` so the reporting-only startup-CO2
    column (:func:`market_sim.results.emissions.startup_co2_tons`) is added only
    when the run opted in; a missing/malformed config or absent flag is OFF.
    """
    cfg_path = run_dir / "run_config.json"
    try:
        cfg = json.loads(cfg_path.read_text())
    except (OSError, ValueError):
        return False
    sc = cfg.get("scenario_config", cfg) if isinstance(cfg, dict) else {}
    return bool(sc.get("startup_co2_reporting", False))


def _startup_co2_kg_map() -> dict[int, float]:
    """Return ``{plant_code: measured startup_co2_kg}`` from the CAMPD artifact.

    The per-start incremental CO2 (kg) is the pooled (``year == 0``) row of the
    committed ``plant_emission_rates`` artifact (``campd._startup_factors``).
    Empty when the artifact is absent, so the R6 adder degrades to zero.
    """
    from market_sim.data.fleet import PLANT_EMISSION_RATES_PATH

    path = Path(PLANT_EMISSION_RATES_PATH)
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    pooled = df[df["year"] == 0] if "year" in df.columns else df
    if "startup_co2_kg" not in pooled.columns:
        return {}
    return {
        int(r["plant_id"]): float(r["startup_co2_kg"])
        for _, r in pooled.iterrows()
        if pd.notna(r["startup_co2_kg"])
    }


def _plant_hourly_fit(
    year: int,
    dispatch: pd.DataFrame,
    campd_year: pd.DataFrame,
    hours: int,
    btm_mw_by_plant: dict[int, float] | None = None,
    band_width: float = _CF_BAND_WIDTH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return per-plant hourly model-vs-CAMPD fit for every resolved plant.

    The model dispatch is summed by ``plant_code`` to an hourly MW series and
    compared against the plant's CAMPD **net** generation. Plants the model
    aggregates into multi-plant bins (``plant_code == 0``) and plants without
    CAMPD coverage are absent.

    ``btm_mw_by_plant`` (CHP plants) adds the plant's flat behind-the-meter
    host-supply MW back onto the model series in every hour the grid share
    is running, so the comparison covers the whole plant like CAMPD does
    (the LP itself sees only the grid-facing share). Hours where the model
    is fully off (outage overlay) stay at zero.

    Returns two frames: ``fit`` — one row per plant with Pearson r, NRMSE,
    annual model / CAMPD GWh and the CF-band occupancy summary
    (``cf_band_overlap`` / ``cf_emd``, see
    :func:`market_sim.results.calibration.check_cf_band_occupancy`), sorted
    worst-fit first — and ``bands`` — one row per plant per CF band with the
    model and CAMPD hours spent in that band (the timing-free operating-level
    histogram).
    """
    model = dispatch[dispatch["plant_code"] > 0].copy()
    # Split-plant remap: a mixed plant is modelled as several bins with
    # synthetic child codes ``parent*10+digit`` (e.g. W A Parish 3470 coal +
    # 34702 gas-steam; see scripts/tag_mixed_plants.py), but CEMS reports the
    # whole physical facility under the single parent plant_id. Fold each
    # child's dispatch back onto its parent before the comparison, so a
    # split plant's model series is its whole-plant output — matching what
    # CAMPD measures. Without this the coal bin alone was compared to the
    # coal+gas CEMS stack, inventing a multi-TWh phantom under-run (the
    # run-97b/98 Parish chase).
    cems_ids = set(int(p) for p in campd_year["plant_id"].unique())

    def _to_cems(code: int) -> int:
        code = int(code)
        return code // 10 if (code not in cems_ids and code // 10 in cems_ids) else code

    model["plant_code"] = model["plant_code"].map(_to_cems)
    piv = (
        model.groupby(["plant_code", "hour"], observed=True)["mw"]
        .sum()
        .unstack("plant_code", fill_value=0.0)
        .sort_index()
    )
    obs = {
        int(pid): g.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        for pid, g in campd_year.groupby("plant_id", observed=True)
    }
    rows = []
    band_rows: list[dict] = []
    for plant_code in piv.columns:
        observed = obs.get(int(plant_code))
        if observed is None:
            continue
        m = piv[plant_code].to_numpy(dtype=float)
        T = min(m.shape[0], observed.shape[0], hours)
        m, o = m[:T], observed[:T]
        btm_mw = (btm_mw_by_plant or {}).get(int(plant_code), 0.0)
        if btm_mw > 0.0:
            m = m + btm_mw * (m > 0.0)
        try:
            occ = check_cf_band_occupancy(m, o, band_width=band_width)
        except ValueError:  # both series identically zero
            occ = None
        rows.append(
            {
                "year": np.int16(year),
                "plant_code": int(plant_code),
                "pearson_r": round(_pearson_r(m, o), 4),
                "nrmse": round(_nrmse(m, o), 4),
                "model_gwh": round(float(m.sum()) / 1e3, 1),
                "campd_gwh": round(float(o.sum()) / 1e3, 1),
                "campd_op_hours": int((o > 0).sum()),
                # Simulated operation for the forward CO2-rate estimator's
                # sim-conditioning (docs/handoffs/emissions-co2-rate-plan-2026-07.md
                # §4.5). Run-length analysis of the in-memory dispatch, vectorized
                # (no hour loop); starts use campd._ONLINE_MW (1 MW) off->on.
                "model_op_hours": int((m > 0.0).sum()),
                "model_starts": _run_length_starts(m),
                "cf_band_overlap": occ["band_overlap"] if occ else float("nan"),
                "cf_emd": occ["cf_emd"] if occ else float("nan"),
                "cap_mw": occ["capacity_mw"] if occ else float("nan"),
            }
        )
        if occ:
            for band in occ["bands"]:
                band_rows.append(
                    {
                        "year": np.int16(year),
                        "plant_code": int(plant_code),
                        "cf_lo": band["lo"],
                        "cf_hi": band["hi"],
                        "model_hours": np.int32(band["model_hours"]),
                        "campd_hours": np.int32(band["actual_hours"]),
                    }
                )
    fit = pd.DataFrame(rows)
    fit = fit.sort_values("pearson_r").reset_index(drop=True) if len(fit) else fit
    return fit, pd.DataFrame(band_rows)


def _print_plant_hourly_fit(year: int, fit: pd.DataFrame) -> None:
    """[7] Per-plant hourly dispatch fit vs CAMPD net — representative panel."""
    by_code = fit.set_index("plant_code") if len(fit) else fit
    print(
        f"\n  [7] Per-plant hourly dispatch fit — {year} "
        "(model vs CAMPD net; representative panel)"
    )
    rows = [
        (
            "plant",
            "EIA code",
            "Pearson r",
            " NRMSE",
            "model GWh",
            "CAMPD GWh",
            "op hrs",
            "band ovlp",
            "CF EMD",
        )
    ]
    for code, label in _PLANT_PANEL:
        if len(by_code) and code in by_code.index:
            r = by_code.loc[code]
            rows.append(
                (
                    label,
                    str(code),
                    f"{r['pearson_r']:.3f}",
                    f"{r['nrmse']:.3f}",
                    f"{r['model_gwh']:9.0f}",
                    f"{r['campd_gwh']:9.0f}",
                    str(int(r["campd_op_hours"])),
                    f"{r['cf_band_overlap']:.3f}",
                    f"{r['cf_emd']:.3f}",
                )
            )
        else:
            rows.append(
                (
                    label,
                    str(code),
                    "    —",
                    "    —",
                    "    —",
                    "    —",
                    "  —",
                    "    —",
                    "    —",
                )
            )
    _print_table(rows)
    if len(fit):
        print(
            f"    (full per-plant fit for all {len(fit)} resolved plants "
            "written to plant_hourly_fit.parquet)"
        )


def _print_plant_cf_bands(year: int, bands: pd.DataFrame) -> None:
    """[7b] Hours per CF band, model vs CAMPD — representative panel.

    The timing-free companion to [7]: for each panel plant, how many hours
    the model and the real plant spent in each capacity-factor band. A plant
    can be hourly-correlated and hit its annual GWh while still parking at
    the wrong operating levels (committed floor too low, ramp top in place
    of duct firing); this is the table that shows it.
    """
    if not len(bands):
        return
    # Band width comes from the data, not the module default, so the header
    # is correct whatever --cf-band-width the run used.
    width = float((bands["cf_hi"] - bands["cf_lo"]).median())
    print(
        f"\n  [7b] Hours per {width:.0%} CF band — {year} "
        "(model / CAMPD net; representative panel)"
    )
    grouped = bands.groupby("plant_code", observed=True)
    edges = sorted(bands["cf_lo"].unique())
    header = ("plant", "", *(f"{lo:.0%}-{lo + width:.0%}" for lo in edges))
    rows = [header]
    for code, label in _PLANT_PANEL:
        if code not in grouped.groups:
            continue
        g = grouped.get_group(code).sort_values("cf_lo")
        rows.append((label, "model", *(str(int(h)) for h in g["model_hours"])))
        rows.append(("", "CAMPD", *(str(int(h)) for h in g["campd_hours"])))
    _print_table(rows)


# p2_state on-disk envelope version. v2 wraps the state dict as
# {'format_version': 2, 'git_sha': ..., 'state': p2_state}; the reader
# (_load_p2_state) treats a bare dict — no 'format_version' key — as v1, the
# pre-envelope format used by the committed 2026-era pickles.
_P2_STATE_FORMAT_VERSION = 2


def _save_p2_state(run_dir: Path, year: int, p2_state: dict) -> None:
    """Pickle the cached P1 inputs so P2 can be re-run as a post-process.

    Wrapped in a versioned envelope (``format_version`` / ``git_sha`` /
    ``state``) so a future reader can branch on the format and trace a pickle to
    the code that wrote it. :func:`_load_p2_state` unwraps a v2 envelope and
    treats a bare dict as v1.
    """
    d = run_dir / "p2_state"
    d.mkdir(parents=True, exist_ok=True)
    envelope = {
        "format_version": _P2_STATE_FORMAT_VERSION,
        "git_sha": _git_sha(),
        "state": p2_state,
    }
    with gzip.open(d / f"{year}.pkl.gz", "wb") as fh:
        pickle.dump(envelope, fh, protocol=pickle.HIGHEST_PROTOCOL)


def _load_p2_state(path: Path) -> dict:
    """Load a p2_state pickle, unwrapping the versioned envelope.

    A v2 payload is ``{'format_version', 'git_sha', 'state'}`` — the inner
    ``state`` dict is returned. A bare dict (no ``format_version`` key) is the v1
    pre-envelope format (the committed 2026-era pickles) and is returned as-is.
    """
    with gzip.open(path, "rb") as fh:
        loaded = pickle.load(fh)
    if isinstance(loaded, dict) and "format_version" in loaded:
        return loaded["state"]
    return loaded


def _rebuild_p2_config(old, *, screen_coal: bool):
    """Rebuild a current ``ScenarioConfig`` from a (possibly stale) pickled one.

    The committed 2026-era p2_state pickles carry a ``ScenarioConfig`` that is
    missing fields added since (and carries a few since-removed ones), so
    ``old.with_overrides(...)`` — i.e. ``dataclasses.replace`` — raises
    ``AttributeError`` on the first ``default_factory`` field it cannot read off
    the stale instance. Reconstruct through ``__init__`` from only the fields
    that still exist (new fields take their current defaults; dropped fields fall
    away), THEN apply the P2 overrides on the valid instance.
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    current = {f.name for f in dataclasses.fields(ScenarioConfig)}
    rebuilt = ScenarioConfig(**{k: v for k, v in vars(old).items() if k in current})
    return rebuilt.with_overrides(
        commitment_enabled=True,
        commitment_screen_coal=screen_coal,
    )


def run_p2_layer(bundle: Path, screen_coal: bool) -> None:
    """Run the P2 commitment pass from a bundle's cached P1 state, then report.

    Loads each year's pickled P1 inputs from ``<bundle>/p2_state/``, runs the
    single P2 LP solve (no P0/P1 re-solve), writes the P2 dispatch / system /
    btm into the bundle, marks P2 in ``meta.json`` and prints the full report.
    The bundle must have been produced with ``--persist-p2-state``.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    iso_config = get_iso_config(meta["iso"])
    zone_names = iso_config.zone_names
    generation = load_monthly_generation()
    states = sorted((bundle / "p2_state").glob("*.pkl.gz"))
    if not states:
        logger.error(
            "no p2_state pickles in %s — re-run the bundle with "
            "--persist-p2-state first",
            bundle / "p2_state",
        )
        return

    system_p2, btm_p2, storage_p2 = [], [], []
    for sp in states:
        state = _load_p2_state(sp)
        year = int(state["year"])
        cfg = _rebuild_p2_config(state["config"], screen_coal=screen_coal)
        logger.info("P2 post-process %d (screen_coal=%s)", year, screen_coal)
        result = _commitment_pass(state, cfg)
        ctx = state["context"]
        must_run = _must_run_profiles(
            year,
            generation,
            meta["iso"],
            state["demand"],
            skip_classes=frozenset(),
            e930=_eia930_frame(year, meta["iso"], iso_config),
            # P2 is archived (never a calibration option, no keeper uses it),
            # but it must still inject the SAME residual array its P1 did.
            mustrun_chp_btm_holdout=bool(
                getattr(cfg, "mustrun_chp_btm_holdout", False)
            ),
            benchmark_membership_vintage_union=bool(
                getattr(cfg, "benchmark_membership_vintage_union", False)
            ),
        )
        _dispatch_frame(
            year,
            "P2",
            result,
            ctx,
            zone_names,
            iso=meta["iso"],
            must_run=must_run,
        ).to_parquet(bundle / "dispatch" / f"{year}_P2.parquet", index=False)
        system_p2.append(_system_frame(year, "P2", result, state["demand"], zone_names))
        btm_p2.append(
            _btm_frame(
                year,
                "P2",
                generation,
                iso=meta["iso"],
                nyiso_chp_btm_measured=bool(meta.get("nyiso_chp_btm_measured")),
            )
        )
        # Older p2_state pickles predate the storage frame; skip them.
        storage_frame = _storage_frame(year, "P2", result, state.get("storage_units"))
        if storage_frame is not None:
            storage_p2.append(storage_frame)

    for name, frames in (
        ("system", system_p2),
        ("btm", btm_p2),
        ("storage", storage_p2),
    ):
        if not frames:
            continue
        path = bundle / f"{name}.parquet"
        new = pd.concat(frames, ignore_index=True)
        if path.exists():
            old = pd.read_parquet(path)
            old = old[old["pass"] != "P2"]  # replace any prior P2
            new = pd.concat([old, new], ignore_index=True)
        new.to_parquet(path, index=False)

    meta["passes"] = sorted(set(meta.get("passes", [])) | {"P2"})
    meta["p2_screen_coal"] = screen_coal
    (bundle / "meta.json").write_text(json.dumps(meta, indent=2, default=_json_default))
    report_run(bundle)


# Model fuel labels that aggregate into the EIA-930 / EIA-923 "gas" series.
_MODEL_GAS_FUELS: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st"})
# Canonical fuel order for the generic fuel-mix table.
_GENERIC_FUEL_ORDER: tuple[str, ...] = (
    "coal",
    "gas",
    "nuclear",
    "wind",
    "solar",
    "hydro",
    "oil",
    "biomass",
    "other",
)

# Energy-balance guard tolerance (ITEM B): model total generation should land on
# the EIA-930 net generation (demand + interchange, both measured) within this
# band. The legitimate residual is behind-the-meter CHP held off-grid plus a
# little dump/curtailment; anything larger (a biomass double-count ~2.4 TWh, a
# benchmark-assembly slip) is flagged so the headline TOTAL is never silently
# apples-to-oranges. Diagnostic only — it prints/warns, never aborts the run.
_ENERGY_BALANCE_TOL_TWH: float = 3.0


def _canon_fuel(fuel: str) -> str:
    """Collapse a model fuel label to its benchmark fuel (gas_* -> gas).

    Non-gas labels are lower-cased so the dispatch frame's upper-case
    must-run class ``OTHER`` (geothermal + misc) matches the lower-case
    ``"other"`` entry in :data:`_GENERIC_FUEL_ORDER` — otherwise it summed
    into the model TOTAL but never printed as a row, making the [1] table
    look ~9 TWh short of its own total.
    """
    return "gas" if fuel in _MODEL_GAS_FUELS else fuel.lower()


def _aggregate_twh(by_fuel: dict[str, float]) -> dict[str, float]:
    """Sum a per-fuel TWh mapping into canonical benchmark fuels."""
    out: dict[str, float] = {}
    for fuel, twh in by_fuel.items():
        out[_canon_fuel(fuel)] = out.get(_canon_fuel(fuel), 0.0) + twh
    return out


def _priced_node_fit_rmse(iso: str, net_export: np.ndarray) -> float | None:
    """Return the offline priced-node duration-curve fit RMSE (MW), or None.

    The lower-bound duration-curve RMSE of ``constants.IMPORT_TRANCHES`` /
    ``EXPORT_TRANCHES[iso]`` against the measured net-export series, free of
    any modeled price (scripts/data/derive_import_tranches.py measured-only mode).
    The node's achievable net-export levels are the partial sums of the
    blocks in price-merit order; each measured hour is placed on its nearest
    level (the optimal price-orthogonal placement). ``None`` when the ISO has
    no priced node configured.
    """
    from market_sim.config.interchange_config import EXPORT_TRANCHES, IMPORT_TRANCHES

    imports = IMPORT_TRANCHES.get(iso, [])
    sinks = EXPORT_TRANCHES.get(iso, [])
    if not imports and not sinks:
        return None
    total_imp = sum(c for _, c, _ in imports)
    levels = [-total_imp]
    running = -total_imp
    for _, c, _ in sorted(imports, key=lambda t: -t[2]):
        running += c
        levels.append(running)
    for _, c, _ in sorted(sinks, key=lambda t: -t[2]):
        running += c
        levels.append(running)
    lv = np.array(sorted(levels), dtype=float)
    mids = (lv[:-1] + lv[1:]) / 2.0
    placed = lv[np.searchsorted(mids, net_export)]
    return float(np.sqrt(((np.sort(placed) - np.sort(net_export)) ** 2).mean()))


def _print_curtailment_vs_reported(
    year: int, iso: str, dispatch: pd.DataFrame, label: str = "1b"
) -> None:
    """Modeled vs reported wind/solar curtailment (HSL-backed ISO-years).

    The headline re-curtailment metric of playbook §8.3: the dispatch was fed
    the *uncurtailed* potential (the HSL analogue — see
    ``market_sim.data.renewables``), so its endogenous curtailment
    ``potential - dispatched`` is directly comparable to the curtailment the
    ISO actually reported (``hsl - gen`` in the same parquet). Annual TWh
    per fuel plus the monthly GWh shape. The model side measures against the
    potential the LP actually consumed — ``hsl_potential_mw``, the HSL
    series with any per-year rescale applied (ERCOT 2023's wind HSL is
    rescaled up; against the raw HSL the model's curtailment would read a
    phantom zero there) — while the reported side keeps the raw
    ``hsl - gen``.

    ISO-years with no HSL parquet print a data-needed note when the ISO has
    an HSL dataset family (ERCOT/CAISO; e.g. ERCOT 2024+ awaits the NP6
    report uploads) and are skipped silently otherwise (those backcasts
    consume the delivered profile and have nothing to re-curtail).

    Caveat: re-reporting a bundle that was *solved* before the year's HSL
    parquet existed overstates model curtailment — that run consumed
    delivered (already-curtailed) profiles, not this potential. Re-solve the
    year after building a new HSL parquet.
    """
    from market_sim.data.renewables import (
        _hsl_file,
        hsl_potential_mw,
        load_hsl_hourly,
    )

    hsl = load_hsl_hourly(iso, year)
    if hsl is None:
        if _hsl_file(iso, year) is not None:
            print(
                f"\n  [{label}] Renewable curtailment — {year}: no {iso} "
                "HSL parquet; build with scripts/build_"
                f"{iso.lower()}_hsl.py (ERCOT 2024+ needs the NP6 report "
                "uploads under data/raw/ercot-hsl/np6/)"
            )
        return

    modeled = {}
    for fuel in ("wind", "solar"):
        rows = dispatch[dispatch["fuel"] == fuel]
        if rows.empty:
            return
        modeled[fuel] = (
            rows.groupby("hour", observed=True)["mw"]
            .sum()
            .sort_index()
            .to_numpy(dtype=float)
        )

    T = min(_HOURS_PER_YEAR, *(len(v) for v in modeled.values()))
    print(
        f"\n  [{label}] Renewable curtailment — {year} "
        "(model re-curtailment vs ISO-reported; potential = uncurtailed "
        "HSL)"
    )
    if T < _HOURS_PER_YEAR:
        print(f"    NOTE: {T}-hour run — reported series truncated to match.")
    rows_out: list[tuple] = [
        (
            "fuel",
            "potential TWh",
            "model TWh",
            "model curt",
            "model %",
            "reported curt",
            "reported %",
        )
    ]
    monthly: dict[str, dict[str, np.ndarray]] = {}
    for fuel in ("wind", "solar"):
        # The potential the LP saw is the CF-floored, per-year-rescaled HSL
        # (negative EIA-930 night-time values clamp to zero in the profile),
        # so floor the consumed series here too; otherwise modeled
        # curtailment picks up phantom night-time slack.
        potential = np.maximum(hsl_potential_mw(iso, year, fuel)[:T], 0.0)
        reported_potential = np.maximum(
            hsl[f"{fuel}_hsl_mw"].to_numpy(dtype=float)[:T], 0.0
        )
        delivered = np.minimum(
            np.maximum(hsl[f"{fuel}_gen_mw"].to_numpy(dtype=float)[:T], 0.0),
            reported_potential,
        )
        model_curt = np.maximum(potential - modeled[fuel][:T], 0.0)
        reported_curt = reported_potential - delivered
        monthly[fuel] = {"model": model_curt, "reported": reported_curt}
        pot_twh = potential.sum() / _MWH_PER_TWH
        rows_out.append(
            (
                fuel,
                f"{pot_twh:.2f}",
                f"{modeled[fuel][:T].sum() / _MWH_PER_TWH:.2f}",
                f"{model_curt.sum() / _MWH_PER_TWH:.3f}",
                f"{100.0 * model_curt.sum() / potential.sum():.2f}",
                f"{reported_curt.sum() / _MWH_PER_TWH:.3f}",
                f"{100.0 * reported_curt.sum() / reported_potential.sum():.2f}",
            )
        )
    _print_table(rows_out)

    month_idx = _hour_to_month(T)
    month_rows: list[tuple] = [
        (
            "month",
            "wind mdl",
            "wind rep",
            "solar mdl",
            "solar rep",
        )
    ]
    for m in range(1, 13):
        sel = month_idx == m
        if not sel.any():
            break
        month_rows.append(
            (
                _MONTH_NAMES[m - 1],
                *(
                    f"{monthly[fuel][kind][sel].sum() / 1e3:.1f}"
                    for fuel in ("wind", "solar")
                    for kind in ("model", "reported")
                ),
            )
        )
    print("\n    Monthly curtailment (GWh):")
    _print_table(month_rows)


# Local hours-of-day of the evening net-load peak window, used to summarize
# the battery discharge shape (CAISO's duck-curve discharge concentrates in
# HE18-23, i.e. hours 17-22 0-based). Both the model and the EIA-930 series
# index hour 0 at local midnight Jan 1, so ``hour % 24`` is the local hour.
_EVENING_HOURS: tuple[int, int] = (17, 22)


def _evening_share_pct(discharge: np.ndarray) -> float:
    """Share (%) of total discharge falling in the evening-peak window."""
    total = float(discharge.sum())
    if total <= 0.0:
        return float("nan")
    hod = np.arange(discharge.shape[0]) % 24  # hour of local day
    lo, hi = _EVENING_HOURS
    return 100.0 * float(discharge[(hod >= lo) & (hod <= hi)].sum()) / total


def _print_storage_cycling(
    year: int,
    storage: pd.DataFrame,
    e930: dict | None,
) -> None:
    """[2b] Battery throughput + evening-discharge shape vs EIA-930.

    The model side is the bundle's storage frame (battery vs pumped-storage
    techs split out). The benchmark side is the EIA-930 ``battery`` /
    ``pumped_storage`` net series, present only when the BA extract carries
    the storage fuel codes (the current CISO extract folds batteries into
    ``OTH``); absent benchmarks print as ``—`` so the model throughput is
    still on the record.
    """
    batt = storage[storage["tech"] != "pumped_storage"]
    if batt.empty:
        return
    hourly = batt.groupby("hour")[["charge_mw", "discharge_mw"]].sum().sort_index()
    dis = hourly["discharge_mw"].to_numpy(dtype=float)
    chg = hourly["charge_mw"].to_numpy(dtype=float)
    obs = e930.get("battery") if e930 is not None else None

    lo, hi = _EVENING_HOURS
    print(f"\n  [2b] Battery cycling — {year} (model EIA-860 fleet vs EIA-930 BAT)")
    rows: list[tuple] = [("metric", "model", "EIA-930")]
    if obs is not None:
        T = min(dis.shape[0], obs.shape[0])
        dis, chg, obs = dis[:T], chg[:T], obs[:T]
        # EIA-930 BAT is a net series: + = discharging, - = charging.
        o_dis = np.clip(obs, 0.0, None)
        o_chg = np.clip(-obs, 0.0, None)
        rows.append(
            (
                "discharge TWh",
                f"{dis.sum() / _MWH_PER_TWH:.2f}",
                f"{o_dis.sum() / _MWH_PER_TWH:.2f}",
            )
        )
        rows.append(
            (
                "charge TWh",
                f"{chg.sum() / _MWH_PER_TWH:.2f}",
                f"{o_chg.sum() / _MWH_PER_TWH:.2f}",
            )
        )
        rows.append(
            (
                f"evening (h{lo}-{hi}) discharge share %",
                f"{_evening_share_pct(dis):.1f}",
                f"{_evening_share_pct(o_dis):.1f}",
            )
        )
        rows.append(("hourly net Pearson r", f"{_pearson_r(dis - chg, obs):.3f}", ""))
    else:
        rows.append(("discharge TWh", f"{dis.sum() / _MWH_PER_TWH:.2f}", "—"))
        rows.append(("charge TWh", f"{chg.sum() / _MWH_PER_TWH:.2f}", "—"))
        rows.append(
            (
                f"evening (h{lo}-{hi}) discharge share %",
                f"{_evening_share_pct(dis):.1f}",
                "—",
            )
        )
    _print_table(rows)
    if obs is None:
        print(
            "    (no EIA-930 battery series in this BA extract — model "
            "throughput reported alone)"
        )

    ps = storage[storage["tech"] == "pumped_storage"]
    if not ps.empty:
        ps_dis = float(ps["discharge_mw"].sum()) / _MWH_PER_TWH
        ps_obs = e930.get("pumped_storage") if e930 is not None else None
        bench = (
            f"{np.clip(ps_obs, 0.0, None).sum() / _MWH_PER_TWH:.2f}"
            if ps_obs is not None
            else "—"
        )
        print(f"    pumped-storage discharge: model {ps_dis:.2f} TWh; EIA-930 {bench}")


def _report_generic(
    run_dir: Path,
    iso: str,
    meta: dict,
    system: pd.DataFrame,
    e930_all: pd.DataFrame | None,
) -> None:
    """Print the generic energy-only calibration report for a non-ERCOT ISO.

    Compares modeled annual generation by fuel against the EIA-930 hourly
    delivered mix and the EIA-923 reference benchmark, summarizes the zonal
    and system price level and duration, and contrasts the (zero) modeled net
    interchange against the EIA-930 actual. This is the Stage G comparison the
    energy-only PJM backcast supports today; the ERCOT-specific plant-level,
    CHP and CAMPD diagnostics are skipped.
    """
    reference = _load_reference()
    generation = load_monthly_generation()
    storage_path = run_dir / "storage.parquet"
    storage_all = pd.read_parquet(storage_path) if storage_path.exists() else None
    for year in meta["years"]:
        ref_year = reference.get("isos", {}).get(iso, {}).get(str(year), {})
        ref_gen = _aggregate_twh(ref_year.get("generation_twh", {}))
        ey_long = e930_all[e930_all["year"] == year] if e930_all is not None else None
        # Renewables are judged against EIA-930 grid-delivered generation (the
        # 930 column), not EIA-923 — the same basis the ERCOT report uses
        # (_print_nonchp_grid compares solar/wind to e930). EIA-923's solar/wind
        # totals fold in behind-the-meter / distributed output that never
        # reaches the wholesale grid (PJM 2024: 20.6 TWh 923 solar vs ~16 on the
        # grid), so the 923 cell is blanked for solar/wind in the print loop
        # below. The value is kept in ref_gen here so the 923 system total (and
        # thus the thermal 923% shares) still reflect the full reported mix.

        e930 = None
        if e930_all is not None:
            ey = e930_all[e930_all["year"] == year]
            e930 = {
                s: ey[ey["series"] == s].sort_values("hour")["mw"].to_numpy()
                for s in ey["series"].unique()
            }

        pass_label = meta["passes"][-1]
        disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
        if not disp_path.exists():
            continue
        dispatch = pd.read_parquet(disp_path)
        sysd = system[(system["year"] == year) & (system["pass"] == pass_label)]

        print(f"\n{'=' * 80}\n  {iso} {year} BACKCAST  (energy-only)\n{'=' * 80}")

        # --- [1] Generation by fuel: model vs EIA-930 vs EIA-923 reference ---
        model = _aggregate_twh(
            (dispatch.groupby("fuel")["mw"].sum() / _MWH_PER_TWH).to_dict()
        )
        # The priced import/export node's net position is interchange, not
        # generation — excluding it keeps the model TOTAL (gross internal
        # generation) comparable to the EIA-930 generation total. It is carried
        # out of the generation rows here and reported as its own "import"
        # category below the total (net interchange-served energy), as well as
        # in the [2] net-interchange reconciliation.
        import_net_twh = model.pop("import", None)
        # The model's injected residual class is keyed "OTHER" (process gas /
        # landfill / purchased steam from EIA-923); fold it into the lowercase
        # "other" benchmark bucket so it shows as its own row instead of vanishing
        # into the TOTAL only.
        if "OTHER" in model:
            model["other"] = model.get("other", 0.0) + model.pop("OTHER")
        e930_twh = (
            {
                f: float(e930[f].sum()) / _MWH_PER_TWH
                for f in _GENERIC_FUEL_ORDER
                if e930 is not None and f in e930
            }
            if e930 is not None
            else {}
        )
        # Like-for-like "actual total" basis (ITEM B). The headline gap used to
        # flip sign year-to-year because the "actual total" was assembled from
        # inconsistent pieces: EIA-930's itemized BA series omit biomass AND an
        # unspecified residual (so a raw itemized TOTAL undercounts true in-region
        # generation), while the model TOTAL carries both. Anchor the EIA-930
        # column to its measured grid total — net generation = demand + net
        # interchange, the physically meaningful invariant — every year:
        #   (1) fold in the vintage-carry-reconciled biomass (the exact measured
        #       energy the model injects), and
        #   (2) surface net_gen − Σ(itemized + biomass) as an explicit "other"
        #       (unspecified) residual so the column sums to the true grid total.
        # model TOTAL − EIA-930 TOTAL is then model gen − measured net gen — the
        # same small, consistent number the energy-balance guard prints — and
        # reflects only real fuel-mix differences, never which vintage was
        # complete. Imports stay a separate "serves load, not generation" line.
        net_gen_930 = (
            _e930_series_annual_monthly(ey_long, "net_gen", year)[0] / _MWH_PER_TWH
            if ey_long is not None
            else None
        )
        bio_actual = (
            _reconciled_biomass_class(year, generation, iso, ey_long)[0] / _MWH_PER_TWH
            if e930_twh
            else 0.0
        )
        if bio_actual > 0.0:
            e930_twh["biomass"] = bio_actual
        if net_gen_930 and e930_twh:
            resid = net_gen_930 - sum(e930_twh.values())
            if resid > 0.05:
                e930_twh["other"] = e930_twh.get("other", 0.0) + resid
        model_total = sum(model.values())
        e930_total = (
            net_gen_930
            if net_gen_930
            else (sum(e930_twh.values()) if e930_twh else None)
        )
        ref_total = sum(ref_gen.values()) if ref_gen else None

        def _twh(v: float | None) -> str:
            return "      —" if v is None else f"{v:7.2f}"

        def _pct(v: float | None, total: float | None) -> str:
            return "    —" if not v or not total else f"{100 * v / total:5.1f}"

        print("\n  [1] Generation by fuel (TWh; share of own total)")
        print(
            "    (EIA-930 column = measured grid total (net gen = demand + "
            "interchange): itemized fuels + repaired renewables + carried biomass"
        )
        print(
            "     + unspecified 'other' residual — the like-for-like actual total. "
            "EIA-923 column = raw reference vintage, biomass/other incomplete in a"
        )
        print("     partial current-year release.)")
        print(
            f"    {'fuel':<9} {'model':>7} {'mdl%':>5} "
            f"{'EIA-930':>7} {'930%':>5} {'EIA-923':>7} {'923%':>5}"
        )
        for fuel in _GENERIC_FUEL_ORDER:
            m, g, r = model.get(fuel), e930_twh.get(fuel), ref_gen.get(fuel)
            # Solar/wind compared vs EIA-930 only (see note above); blank the
            # BTM-inflated 923 cell while leaving it in the total.
            if fuel in ("solar", "wind"):
                r = None
            if m is None and g is None and r is None:
                continue
            print(
                f"    {fuel:<9} {_twh(m)} {_pct(m, model_total)} "
                f"{_twh(g)} {_pct(g, e930_total)} "
                f"{_twh(r)} {_pct(r, ref_total)}"
            )
        print(
            f"    {'TOTAL':<9} {_twh(model_total)} {'100.0':>5} "
            f"{_twh(e930_total)} {'100.0' if e930_total else '    —':>5} "
            f"{_twh(ref_total)} {'100.0' if ref_total else '    —':>5}"
        )

        # Imports as their own category: net interchange-served energy (+ = net
        # import into the ISO), shown below the generation total since it serves
        # load but is not in-state generation. The model figure is the priced
        # node's net position; the EIA-930 figure is the measured net import
        # (the interchange series carries + = net export, so net import is its
        # negation). Shares are of total load served (generation + net import).
        ix_930 = e930.get("interchange") if e930 is not None else None
        import_net_930 = (
            -float(ix_930.sum()) / _MWH_PER_TWH if ix_930 is not None else None
        )
        if import_net_twh is not None or import_net_930 is not None:
            served_m = model_total + (import_net_twh or 0.0)
            served_g = (
                e930_total + (import_net_930 or 0.0) if e930_total is not None else None
            )
            print(
                f"    {'import':<9} {_twh(import_net_twh)} "
                f"{_pct(import_net_twh, served_m)} "
                f"{_twh(import_net_930)} {_pct(import_net_930, served_g)} "
                f"{_twh(None)} {_pct(None, None)}"
                "   (net; serves load, not in generation total)"
            )

        # Energy-balance guard (ITEM B): the physically meaningful invariant is
        # model generation + net imports ≈ measured load. Net interchange is
        # pinned to the measured EIA-930 schedule and demand is measured, so the
        # only slack is unserved energy — this asserts the LP actually served
        # load and flags any reconciliation drift so the headline TOTAL is never
        # silently apples-to-oranges. EIA-930 net_gen = demand + interchange (the
        # same grid total the EIA-930 column above is anchored to), so model_total
        # should land on it within a small tolerance.
        if net_gen_930:
            bal = model_total - net_gen_930
            flag = "" if abs(bal) <= _ENERGY_BALANCE_TOL_TWH else "  ⚠ exceeds tol"
            print(
                f"    energy balance: model gen {model_total:7.2f} − EIA-930 net "
                f"gen {net_gen_930:7.2f} = {bal:+6.2f} TWh"
                f" (tol ±{_ENERGY_BALANCE_TOL_TWH:.1f}){flag}"
            )
            if abs(bal) > _ENERGY_BALANCE_TOL_TWH:
                logger.warning(
                    "%s %d energy-balance drift: model gen %.2f vs EIA-930 net gen "
                    "%.2f (%+.2f TWh) exceeds ±%.1f tol",
                    iso,
                    year,
                    model_total,
                    net_gen_930,
                    bal,
                    _ENERGY_BALANCE_TOL_TWH,
                )

        # Apples-to-apples caveat for the EIA-930 "gas" column: for some BAs
        # (CAISO is the live case) EIA-930 folds geothermal and biomass into
        # its Natural Gas aggregate, so the EIA-930 gas cell above is inflated
        # by roughly the model's geothermal (the "other" row) + biomass. Model
        # gas should be judged against the EIA-923 gas cell, which is clean.
        other_m = model.get("other")
        bio_m = model.get("biomass")
        if e930_twh.get("gas") and (other_m or bio_m):
            folded = (other_m or 0.0) + (bio_m or 0.0)
            print(
                f"    note: EIA-930 'gas' ({e930_twh['gas']:.1f}) folds in "
                f"geothermal+biomass (~{folded:.1f} TWh here); compare model "
                "gas to the EIA-923 cell, not EIA-930."
            )

        # --- [1b] Curtailment: model re-curtailment vs ISO-reported ---
        _print_curtailment_vs_reported(year, iso, dispatch)

        # --- [2] Net interchange: model vs EIA-930 ---
        if e930 is not None and "interchange" in e930:
            ix = e930["interchange"]
            ix_twh = float(ix.sum()) / _MWH_PER_TWH
            print("\n  [2] Net interchange (EIA sign: + = net export)")
            print(f"    actual (EIA-930): {ix_twh:+.2f} TWh ({ix.mean():+.0f} MW avg)")
            # Offline priced-node fit RMSE (the P9 deliverable): the lowest
            # duration-curve RMSE the configured tranche capacities can reach
            # against this measured series, free of the modeled price. The
            # modeled line below should approach this once the price level is
            # calibrated (P11/P12); a gap means the modeled price, not the
            # tranche capacities, is off.
            fit_rmse = _priced_node_fit_rmse(iso, np.asarray(ix, dtype=float))
            if fit_rmse is not None:
                print(
                    f"    priced-node fit  : duration RMSE {fit_rmse:.0f} MW "
                    "(offline tranche fit, optimal placement; P9)"
                )
            # Three interchange representations, in order of preference:
            # the priced import/export node when its units are in the
            # dispatch (net export = -(import tranches + export sinks));
            # PJM's measured tie-line schedule added to demand; else the
            # energy-only zero.
            node = dispatch[dispatch["fuel"] == "import"]
            if len(node):
                model_ix = -(
                    node.groupby("hour", observed=True)["mw"]
                    .sum()
                    .sort_index()
                    .to_numpy(dtype=float)
                )
                how = "priced import/export node"
            else:
                # No priced node in dispatch → the measured net-interchange
                # schedule was folded into demand by default (load_demand,
                # include_interchange=True). PJM is a net exporter; NYISO/NEISO
                # are net importers — all three serve the measured EIA-930
                # schedule the same way (P9 / playbook §8.2).
                measured_ix = {
                    "PJM": pjm_net_interchange,
                    "NYISO": nyiso_net_interchange,
                    "NEISO": neiso_net_interchange,
                }.get(iso)
                model_ix = measured_ix(year) if measured_ix is not None else None
                how = "served as a scheduled interchange added to demand"
            if model_ix is not None:
                m_twh = float(model_ix.sum()) / _MWH_PER_TWH
                print(
                    f"    model            : {m_twh:+.2f} TWh "
                    f"({model_ix.mean():+.0f} MW avg; {how})"
                )
                n = min(model_ix.shape[0], ix.shape[0])
                dur_m = np.sort(model_ix[:n])
                dur_a = np.sort(np.asarray(ix, dtype=float)[:n])
                rmse = float(np.sqrt(((dur_m - dur_a) ** 2).mean()))
                pcts = [1, 10, 50, 90, 99]
                qm = np.percentile(model_ix[:n], pcts)
                qa = np.percentile(np.asarray(ix, dtype=float)[:n], pcts)
                print(
                    f"    duration curve   : RMSE {rmse:.0f} MW; "
                    "p01/p10/p50/p90/p99 model "
                    + "/".join(f"{v:+.0f}" for v in qm)
                    + " vs actual "
                    + "/".join(f"{v:+.0f}" for v in qa)
                )
                print(
                    f"    import hours     : model "
                    f"{100.0 * float((model_ix[:n] < 0).mean()):.1f}% vs "
                    f"actual "
                    f"{100.0 * float((np.asarray(ix)[:n] < 0).mean()):.1f}%"
                )
                # Diurnal shape: the average 24-hour net-interchange profile.
                # The duration curve scores the magnitude distribution; the
                # diurnal correlation scores whether the model imports/exports
                # at the right hours of the day (neighbor demand is the driver,
                # so the priced node tracks shape only loosely — see §8.2).
                whole = n - n % 24
                if whole >= 24:
                    d24m = model_ix[:whole].reshape(-1, 24).mean(axis=0)
                    d24a = (
                        np.asarray(ix, dtype=float)[:whole].reshape(-1, 24).mean(axis=0)
                    )
                    corr = float(np.corrcoef(d24m, d24a)[0, 1])
                    print(
                        f"    diurnal shape    : corr {corr:+.2f}; "
                        f"model peak->trough {d24m.max() - d24m.min():.0f} MW "
                        f"vs actual {d24a.max() - d24a.min():.0f} MW"
                    )
            else:
                print(
                    "    model            :    0.00 TWh "
                    "(energy-only; no external interchange node)"
                )

        # --- [2b] Battery cycling: throughput + evening-discharge shape ---
        if storage_all is not None:
            s = storage_all[
                (storage_all["year"] == year) & (storage_all["pass"] == pass_label)
            ]
            if not s.empty:
                _print_storage_cycling(year, s, e930)

        # --- [3] Price level + duration ---
        zones = sorted(sysd["zone"].unique())
        print("\n  [3] Zonal price level ($/MWh)")
        print(f"    {'zone':<14} {'avg':>8} {'neg-hrs':>8}")
        for zone in zones:
            zp = sysd[sysd["zone"] == zone]["price"].to_numpy()
            print(f"    {zone:<14} {zp.mean():8.2f} {int((zp < 0).sum()):>8}")
        sysprice = sysd.groupby("hour")["price"].mean().sort_index().to_numpy()
        pct = np.percentile(sysprice, [100, 90, 50, 10, 0])
        print("\n  [3] System price duration ($/MWh)")
        print(
            f"    avg {sysprice.mean():8.2f}   max {pct[0]:8.2f}   "
            f"p90 {pct[1]:7.2f}   p50 {pct[2]:7.2f}   "
            f"p10 {pct[3]:7.2f}   min {pct[4]:8.2f}"
        )
        print(f"    negative-price hours: {int((sysprice < 0).sum())}")


# cf_emd / pearson-r operating-shape regression gate (audit §D3 — the volume
# gate is blind to operating shape; a class can pass on annual TWh while
# missing its CF distribution, e.g. CC_REGULAR's >90% CF hours). The baseline
# is the keeper of record's per-class best-achieved value; a tuning run FAILS
# if it degrades shape beyond the margins. Pure post-processing over the fit
# frame — never gates volumes.
CF_EMD_GATE_MARGIN = 0.02  # cf_emd may rise at most this much vs baseline
CF_R_GATE_MARGIN = 0.02  # pearson_r may fall at most this much vs baseline


def _cf_emd_baseline_path(iso: str) -> Path:
    return CALIBRATION_DIR / f"cf_emd_baseline_{iso.upper()}.json"


def _print_cf_emd_gate(fit: pd.DataFrame, iso: str) -> None:
    """Print the per-class operating-shape regression gate vs the keeper baseline.

    Capacity-weights each class-year's per-plant ``cf_emd`` / ``pearson_r`` and
    compares against ``data/raw/_validation-source/cf_emd_baseline_<ISO>.json`` (the
    keeper of record). No baseline file => the gate is SKIPPED (never a silent
    pass), exactly as the audit's metrics-process fix requires.
    """
    path = _cf_emd_baseline_path(iso)
    if not path.exists():
        print(
            f"\n  [7c] operating-shape gate (cf_emd / r): SKIPPED — no "
            f"baseline at {path.relative_to(REPO)}"
        )
        return
    base = json.loads(path.read_text()).get("classes", {})

    def wmean(g: pd.DataFrame, col: str) -> float:
        w = g["cap_mw"].clip(lower=0.0)
        return float((g[col] * w).sum() / w.sum()) if w.sum() else float("nan")

    cmap = _class_map_for_gate(iso)
    fit = fit.copy()
    fit["group"] = fit["plant_code"].astype(int).map(cmap)
    fit = fit[fit["group"].notna()]

    print(
        "\n  [7c] operating-shape regression gate vs keeper baseline "
        f"(cf_emd <= base+{CF_EMD_GATE_MARGIN}; r >= base-{CF_R_GATE_MARGIN})"
    )
    print(
        f"  {'class':<12} {'year':>4}  {'cf_emd':>7} {'base':>6} {'gate':>5}"
        f"  {'r':>6} {'base':>6} {'gate':>5}"
    )
    n_fail = 0
    for (grp, year), g in fit.groupby(["group", "year"]):
        b = base.get(str(grp), {}).get(str(int(year)))
        if not b:
            continue
        emd, r = wmean(g, "cf_emd"), wmean(g, "pearson_r")
        emd_ok = emd <= b["cf_emd"] + CF_EMD_GATE_MARGIN
        r_ok = r >= b["pearson_r"] - CF_R_GATE_MARGIN
        n_fail += (not emd_ok) + (not r_ok)
        print(
            f"  {grp:<12} {int(year):>4}  {emd:>7.3f} {b['cf_emd']:>6.3f} "
            f"{'PASS' if emd_ok else 'FAIL':>5}  {r:>6.3f} "
            f"{b['pearson_r']:>6.3f} {'PASS' if r_ok else 'FAIL':>5}"
        )
    verdict = "PASS" if n_fail == 0 else f"{n_fail} regression(s)"
    print(f"  [7c] operating-shape gate: {verdict}")


def _class_map_for_gate(iso: str) -> dict[int, str]:
    """Plant_Code -> dispatch class for the shape gate (ERCOT: the bin sheet)."""
    if iso.upper() != "ERCOT":
        return {}
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_campd_bins

    b = load_campd_bins(ScenarioConfig().campd_bins_path)
    return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"].astype(str)))


def report_run(run_dir: Path, band_width: float = _CF_BAND_WIDTH) -> None:
    """Print the full calibration report from a persisted bundle.

    ERCOT prints the full plant-level / CHP / CAMPD diagnostic. Other ISOs
    (PJM energy-only) print the generic fuel-mix / price / interchange report,
    which is all their bundle carries (see :func:`solve_and_persist`).

    ``band_width`` sets the CF-band resolution of the ``[7b]`` panel and
    ``plant_cf_bands.parquet`` (default :data:`_CF_BAND_WIDTH`); pass 0.05 for
    twenty 5%-of-capacity bands.
    """
    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    system = pd.read_parquet(run_dir / "system.parquet")
    e930_path = bundle_input_path(run_dir, "eia930")
    e930_all = pd.read_parquet(e930_path) if e930_path is not None else None

    print(f"\n{'=' * 80}")
    print(
        f"  CALIBRATION REPORT  ({iso}; run {meta['timestamp']}; "
        f"git {meta.get('git_sha', '?')})"
    )
    print(f"  bundle: {run_dir}")
    reused = (meta.get("reuse") or {}).get("reused_years") or {}
    if reused:
        print(
            "  NOTE: mixed --reuse-solved bundle — years "
            f"{sorted(int(y) for y in reused)} were byte-copied from "
            f"{meta['reuse'].get('source_bundle')}; reused years are NOT "
            "fresh evidence (keeper promotion requires a full fresh solve)."
        )
    print(f"{'=' * 80}")

    if iso != "ERCOT":
        _report_generic(run_dir, iso, meta, system, e930_all)
        return

    e923_all = pd.read_parquet(bundle_input_path(run_dir, "eia923"))
    btm_all = pd.read_parquet(run_dir / "btm.parquet")
    campd_path = bundle_input_path(run_dir, "campd")
    campd_all = pd.read_parquet(campd_path) if campd_path is not None else None
    storage_all = (
        pd.read_parquet(run_dir / "storage.parquet")
        if (run_dir / "storage.parquet").exists()
        else None
    )
    plant_fit_frames: list[pd.DataFrame] = []
    plant_band_frames: list[pd.DataFrame] = []

    for year in meta["years"]:
        # Re-bucket genuinely-mixed gas-thermal plants (no class >= 60% of the
        # plant's EIA-923 generation) into OTHER_FOSSIL — the same transform is
        # applied to the model dispatch frame below, so a coin-flip plant lands
        # in the same bucket on both sides and stops distorting the clean classes.
        e923 = apply_other_fossil_scoring(
            e923_all[e923_all["year"] == year], year, plant_col="plant_id"
        )
        e923_annual = _e923_annual(e923)
        e923_monthly = _e923_monthly(e923)
        e930 = None
        e930_solar_monthly = np.zeros(12)
        if e930_all is not None:
            ey = e930_all[e930_all["year"] == year]
            e930 = {
                s: ey[ey["series"] == s].sort_values("hour")["mw"].to_numpy()
                for s in ey["series"].unique()
            }
            e930_solar_monthly = _hourly_to_monthly(e930["solar"])

        print(f"\n{'=' * 80}\n  {iso} {year} BACKCAST\n{'=' * 80}")
        for pass_label in meta["passes"]:
            disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
            if not disp_path.exists():
                continue
            if len(meta["passes"]) > 1:
                tag = "P1 (pre-commitment)" if pass_label == "P1" else "P2 (committed)"
                print(f"\n  ----- {tag} -----")
            dispatch = apply_other_fossil_scoring(
                pd.read_parquet(disp_path), year, plant_col="plant_code"
            )
            sysd = system[(system["year"] == year) & (system["pass"] == pass_label)]
            btm = dict(
                zip(
                    btm_all[
                        (btm_all["year"] == year) & (btm_all["pass"] == pass_label)
                    ]["klass"],
                    btm_all[
                        (btm_all["year"] == year) & (btm_all["pass"] == pass_label)
                    ]["btm_twh"],
                )
            )
            model_hourly = _class_hourly(dispatch)
            model_twh = {k: v.sum() / _MWH_PER_TWH for k, v in model_hourly.items()}

            chp_grid_twh = _print_chp(year, model_twh, btm, e923_annual)

            model_grid = dispatch["mw"].sum() / _MWH_PER_TWH
            net_gen = (
                e930["net_gen"].sum() / _MWH_PER_TWH
                if e930 is not None
                else float("nan")
            )
            model_target = sysd["demand"].sum() / _MWH_PER_TWH
            unserved = sysd["slack"].sum() / _MWH_PER_TWH
            _print_reconciliation(
                year,
                net_gen,
                model_target,
                model_grid,
                unserved,
                sum(btm.values()),
            )
            if e930 is not None:
                _print_nonchp_grid(year, model_hourly, e930, chp_grid_twh)
            _print_thermal_annual(year, model_twh, btm, e923_annual)
            _print_nonfossil_annual(year, model_twh, e923_annual)
            if storage_all is not None:
                _print_storage(
                    year,
                    storage_all[
                        (storage_all["year"] == year)
                        & (storage_all["pass"] == pass_label)
                    ],
                    e930,
                )
            _print_curtailment_vs_reported(year, iso, dispatch, label="3e")
            _print_monthly(
                year, model_hourly, e923_monthly, e930_solar_monthly, btm, e923_annual
            )
            if e930 is not None:
                _print_hourly_fit(year, model_hourly, e930, chp_grid_twh)
            _print_plant_level(year, dispatch, e923)
            if campd_all is not None:
                campd_year = campd_all[campd_all["year"] == year]
                if not campd_year.empty:
                    hours = int(dispatch["hour"].max()) + 1
                    btm_mw_map = _chp_btm_mw_map() if iso == "ERCOT" else None
                    fit, cf_bands = _plant_hourly_fit(
                        year,
                        dispatch,
                        campd_year,
                        hours,
                        btm_mw_map,
                        band_width=band_width,
                    )
                    _print_plant_hourly_fit(year, fit)
                    _print_plant_cf_bands(year, cf_bands)
                    if len(fit):
                        fit = fit.copy()
                        fit["pass"] = pass_label
                        plant_fit_frames.append(fit)
                    if len(cf_bands):
                        cf_bands = cf_bands.copy()
                        cf_bands["pass"] = pass_label
                        plant_band_frames.append(cf_bands)

    if plant_fit_frames:
        all_fit = pd.concat(plant_fit_frames, ignore_index=True)
        if _startup_co2_reporting_enabled(run_dir):
            # EM-5 / plan §5 R6 (reporting-only, default-OFF): the measured
            # per-start CO2 (startup_co2_tons formula) times the model's simulated
            # start count, per row so each (pass, year) keeps its own starts.
            # Never in the dispatch LP; a diagnostic column only, bounded
            # <=0.2% of annual CO2.
            kg_map = _startup_co2_kg_map()
            all_fit["startup_co2_tons"] = (
                all_fit["model_starts"].astype(float)
                * all_fit["plant_code"].map(kg_map).fillna(0.0)
                / 1000.0
            )
        all_fit.to_parquet(run_dir / "plant_hourly_fit.parquet", index=False)
        _print_cf_emd_gate(all_fit, iso)
    if plant_band_frames:
        pd.concat(plant_band_frames, ignore_index=True).to_parquet(
            run_dir / "plant_cf_bands.parquet", index=False
        )


def rebuild_benchmark(bundle: Path) -> None:
    """Rebuild a bundle's benchmark parquets off its meta, then re-report.

    The benchmark frames — EIA-923 (with CAMPD backfill), EIA-930 and CAMPD
    net — are pure functions of ``(year, iso)`` and the reference data;
    they do not depend on the model dispatch. So refreshing them after a
    benchmark-logic change (e.g. the CAMPD backfill) is a post-processing
    step over the persisted dispatch parquets — no LP re-solve needed.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_campd_bins

    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    is_ercot = iso == "ERCOT"
    years = meta["years"]
    hours = int(meta.get("hours", _HOURS_PER_YEAR))
    iso_config = get_iso_config(iso)
    generation = load_monthly_generation()
    parasitic_factors = _parasitic_factor_map()
    # Plant -> group map for the CAMPD backfill: ERCOT's curated bin sheet,
    # the per-plant EIA-860 fleet for every other ISO — the same sources the
    # solve path uses, so a rebuilt benchmark groups plants identically.
    group_by_code: dict[int, str] = {}
    if is_ercot:
        bins = load_campd_bins(ScenarioConfig().campd_bins_path)
        group_by_code = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))

    # The BTM 923 backfill is a benchmark input (it repairs BOTH classFull's
    # minuend and btm.parquet — see _backfill_chp_eia923_from_donor), so a
    # rebuild has to reproduce it. Recovered from the bundle's own run_config
    # when it recorded one; absent, the repair is simply not applied, which is
    # the pre-flag behaviour.
    # meta.json is checked FIRST and is the authoritative source: it is written
    # from the solve kwargs, which is exactly where the BTM side reads the flag
    # from. run_config.json does NOT record `btm_backfill_year` on any bundle in
    # the tree (checked pjm-121 / pjm-129 / pjm-132), so a run_config-only
    # lookup silently recovered None on an armed keeper and the benchmark mirror
    # never fired — leaving precisely the ONE-SIDED repair pjm-130 diagnosed and
    # believed it had closed (the subtrahend repaired, the minuend not), which
    # is what kept `classFull.CT_CHP` at a NEGATIVE metered volume (-0.3726 TWh)
    # in the committed PJM 2025 bench across every registration since. The fix
    # was correct in substance and inert in practice because it looked for its
    # trigger in the wrong file. run_config is kept as a fallback so a bundle
    # that does record it there still works.
    _btm_backfill_year = None
    _meta_bf = meta.get("btm_backfill_year")
    if _meta_bf is not None:
        _btm_backfill_year = int(_meta_bf)
    else:
        _rc = bundle / "run_config.json"
        if _rc.exists():
            _cfg = json.loads(_rc.read_text())
            for _blk in (_cfg, _cfg.get("calibration_flags") or {}):
                if isinstance(_blk, dict) and _blk.get("btm_backfill_year") is not None:
                    _btm_backfill_year = int(_blk["btm_backfill_year"])
                    break

    # miso-253: a rebuild must reproduce the bundle's OWN must-run partition,
    # or an armed bundle silently regains the un-partitioned benchmark while
    # its dispatch keeps the partitioned one -- a bench/model basis split, which
    # is the defect class the single-seam design exists to prevent.
    _mustrun_chp_btm = False
    # spp-49: a rebuild must likewise reproduce the bundle's OWN benchmark
    # membership, or an armed bundle silently regains the canonical-only
    # population while its dispatch keeps the vintage-union one -- the same
    # bench/model basis split the miso-253 recovery above exists to prevent.
    # meta.json is checked FIRST for the same reason it is there: it is
    # written from the solve kwargs.
    _bench_vintage_union = bool(meta.get("benchmark_membership_vintage_union"))
    _rc = bundle / "run_config.json"
    if _rc.exists():
        _cfg = json.loads(_rc.read_text())
        for _blk in (_cfg, _cfg.get("calibration_flags") or {}):
            if isinstance(_blk, dict) and _blk.get("mustrun_chp_btm_holdout"):
                _mustrun_chp_btm = True
                break
        if not _bench_vintage_union:
            for _blk in (_cfg, _cfg.get("calibration_flags") or {}):
                if isinstance(_blk, dict) and _blk.get(
                    "benchmark_membership_vintage_union"
                ):
                    _bench_vintage_union = True
                    break

    e923f, e930f, campdf = [], [], []
    for year in years:
        if not is_ercot:
            group_by_code = _fleet_group_by_code(iso, iso_config, year)
        campd_year = _campd_hourly_frame(year, iso, parasitic_factors, hours)
        _campd_active = None
        if campd_year is not None:
            _bp = campd_year.groupby("plant_id")["net_mw"].sum()
            _campd_active = set(_bp[_bp > 0.0].index.astype(int))
        e930 = _eia930_frame(year, iso, iso_config)
        e923f.append(
            _benchmark_eia923_frame(
                year,
                generation,
                iso,
                campd_year,
                group_by_code,
                e930,
                btm_backfill_year=_btm_backfill_year,
                campd_active=_campd_active,
                mustrun_chp_btm_holdout=_mustrun_chp_btm,
                benchmark_membership_vintage_union=_bench_vintage_union,
            )
        )
        if e930 is not None:
            e930f.append(e930)
        if campd_year is not None:
            campdf.append(campd_year)

    # Rebuild into the content-addressed shared store and re-point the bundle's
    # meta (so a rebuilt benchmark dedupes like a fresh solve's). Any legacy
    # in-bundle copy is left as-is; report_run resolves the shared ref first.
    shared_inputs = dict(meta.get("shared_inputs", {}))
    shared_inputs["eia923"] = write_shared_input(
        pd.concat(e923f, ignore_index=True), "eia923", iso, bundle
    )
    if e930f:
        shared_inputs["eia930"] = write_shared_input(
            pd.concat(e930f, ignore_index=True), "eia930", iso, bundle
        )
    if campdf:
        shared_inputs["campd"] = write_shared_input(
            pd.concat(campdf, ignore_index=True), "campd", iso, bundle
        )
    meta["shared_inputs"] = shared_inputs
    (bundle / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    logger.info("rebuilt benchmark parquets in %s (no re-solve)", bundle)
    report_run(bundle)


def apply_statistical_mode(args) -> None:
    """Force the out-of-sample (forecast-machinery) overlay set when ``args.

    statistical_mode`` is set. One switch turns off every per-hour / per-year
    answer-injection overlay — the historic outage overlay (-> statistical
    WEFOR/POF), the CT AS/RUC-deployment floor, the spatial
    reliability-deployment floor, the ST WEFOR-residual relief, and per-plant
    EIA-923 monthly coal pricing (the coal-monthly disable rides the
    ``prb_overrides`` channel via ``args.no_coal_monthly_pricing``). Structural
    levers (offer curves, coal passthrough sigmoids, cc-duct band, storage
    daily cycling) and the realized annual Henry Hub gas price are untouched,
    so the run measures forecast machinery rather than calibration plumbing.
    Mutates ``args`` in place; a no-op when ``statistical_mode`` is False.
    """
    if not getattr(args, "statistical_mode", False):
        return
    args.outage_source = "statistical"
    args.ct_deployment = False
    args.reliability_deployment = False
    args.wefor_residual = None
    args.wefor_relief_groups = None
    args.no_coal_monthly_pricing = True


# G-18 / CLAUDE.md rule 22: the in-sample calibration window. Any --year
# outside this set is a designated holdout (2022, H1-2026) and requires
# --holdout-authorized plus a calibration-complete marker for the target ISO
# (frontend/data/backcast/calibration-complete.json) — the one-shot frozen-
# config holdout score. Mirrored the workflow_dispatch gate of calibration-run.yml
# (the GH-Actions UI path, removed 2026-07-14) and legitimacy_diagnostics.py's D6_CALIBRATION_YEARS
# / audit_keepers.py's CALIBRATION_YEARS (kept as separate literals per this
# repo's existing convention; a parity test asserts they agree).
HOLDOUT_CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})
HOLDOUT_MARKER_FILE = "frontend/data/backcast/calibration-complete.json"
# Holdout SPEND FREEZE (CLAUDE.md rule 22, declared 2026-07-25). A freeze
# SUSPENDS the authorization a calibration-complete marker grants without
# withdrawing the marker: while a tier is within the active freeze's scope, no
# year of that tier may be solved for ANY ISO, even with --holdout-authorized
# and a marker present. TIER-SCOPED since the 2026-08-26 owner ruling
# (program-director sitting card 6): the VALIDATION tier is lifted for ISOs
# holding a `complete` marker (the marker check below still governs them) and
# the LOCKED TEST stays frozen; the scope is read by the single fail-closed
# reader holdout_policy.frozen_tiers, under which a freeze file with no
# parseable scope covers every tier (the pre-2026-08-26 behaviour).
# Deliberately additive — calibration-complete.json is untouched, so already-
# registered out-of-training bundles stay CI-legal and no prior one-shot is
# invalidated. Checked BEFORE the marker test below (fail closed).


def _enforce_legacy_p2_gate(parser: argparse.ArgumentParser, args) -> None:
    """Fail unless the ARCHIVED P2 flags are unlocked with --enable-legacy-p2.

    P2 is a legacy artifact: P0/P1 are the only production passes and every run
    is scored on P1 (CLAUDE.md "Dispatch & Commitment"). The P2 triggers/knobs
    are hidden from ``--help`` and inert; reaching for one without the explicit
    ``--enable-legacy-p2`` unlock is a hard error so P2 is never a silent
    calibration option. The CAISO RA must-offer bridge is NOT gated here — it is
    a P1-native mechanism (``--caiso-ra-mustoffer``), not a P2 pass.
    """
    if getattr(args, "enable_legacy_p2", False):
        return
    used = []
    if getattr(args, "commitment", False):
        used.append("--commitment")
    if getattr(args, "ercot_as_aware_commitment", False):
        used.append("--ercot-as-aware-commitment")
    if getattr(args, "run_p2", None):
        used.append("--run-p2")
    if getattr(args, "no_coal_p2", False):
        used.append("--no-coal-p2")
    if getattr(args, "persist_p2_state", False):
        used.append("--persist-p2-state")
    if getattr(args, "class_commitment_overrides", None):
        used.append("--class-commitment-overrides")
    if used:
        parser.error(
            "the P2 commitment pass is ARCHIVED (P0/P1 only; runs are scored on "
            "P1). "
            + ", ".join(used)
            + " require --enable-legacy-p2 to run P2 as a last resort. See "
            'CLAUDE.md "Dispatch & Commitment".'
        )


# The ARCHIVED-P2 solve kwargs, by the name they carry in a bundle's meta.json
# and in solve_and_persist's signature. Kept next to the recipe-replay gate that
# reads it so the two can never drift apart.
LEGACY_P2_KWARGS: tuple[str, ...] = (
    "commitment",
    "ercot_as_aware_commitment",
    "persist_p2_state",
    "run_p2",
    "no_coal_p2",
    "class_commitment_overrides",
)


def enforce_legacy_p2_kwargs(kwargs: dict, enable_legacy_p2: bool) -> None:
    """Fail unless a RECONSTRUCTED recipe's archived-P2 kwargs are explicitly unlocked.

    :func:`_enforce_legacy_p2_gate` guards the ``--commitment`` family on
    *parsed CLI args*, which is blind to the OTHER way P2 gets armed: a recipe
    replay rebuilds its kwargs from a committed ``meta.json`` AFTER that gate has
    already run, so a bundle recorded with ``commitment=true`` re-armed the
    archived pass silently on every replay — a keeper carrying P2 propagated it
    to each successor generation with no operator decision anywhere in the chain
    (audit row O5; ASSESSMENT-neiso98 §4.1). Both replay entry points
    (:func:`run_replay_bundle` and ``scripts/replay_keeper.py``) call this on the
    reconstructed kwargs, so the unlock is required on the path that actually
    arms the pass.

    HARD FAIL rather than a silent drop: quietly rewriting the recipe would make
    the replay solve something other than the bundle it names, which is the
    miso-50..53 lossy-reconstruction regression class ``build_kwargs`` exists to
    prevent. The operator either keeps P2 deliberately (``--enable-legacy-p2``)
    or moves the recipe to the production basis (``--set commitment=false``).
    """
    if enable_legacy_p2:
        return
    armed = [k for k in LEGACY_P2_KWARGS if kwargs.get(k)]
    if not armed:
        return
    raise SystemExit(
        "the replayed recipe arms the ARCHIVED P2 commitment pass ("
        + ", ".join(f"{k}={kwargs[k]!r}" for k in armed)
        + "). P0/P1 are the only production passes and every run is scored on "
        'P1 (CLAUDE.md "Dispatch & Commitment"), so a recipe reconstructed from '
        "meta.json may not re-arm P2 implicitly. Pass --enable-legacy-p2 to "
        "keep it as a last resort, or --set commitment=false (replay_keeper) to "
        "move the recipe onto the production basis."
    )


def run_replay_bundle(
    bundle: Path,
    out_dir: Path | None,
    years: list[int] | None,
    note: str,
    zero_forcing_ablation: bool = False,
    reliability_floor_plant_exclusions: bool | None = None,
    caiso_offer_surface_measured_ungrounded: bool | None = None,
    caiso_st_gas_committed_measured: bool | None = None,
    caiso_st_gas_peak_measured: bool | None = None,
    caiso_dsw_lateevening_clean: bool | None = None,
    mustrun_chp_btm_holdout: bool | None = None,
    caiso_ct_peaker_committed_measured: bool | None = None,
    nyiso_ct_peaker_bands_measured: bool | None = None,
    nyiso_ct_peaker_committed_measured: bool | None = None,
    nyiso_st_gas_econ_bands_deleaked: bool | None = None,
    gas_offer_margin: bool | None = None,
    nearby_fuel_price_zone_donor_guard: bool | None = None,
    fleet_state_from_eia860: bool | None = None,
    caiso_citygate_spot_coverage: bool | None = None,
    unit_outage_mixed_gas_routing: bool | None = None,
    unit_outage_st_capacity_basis: bool | None = None,
    unit_outage_per_unit_clip: bool | None = None,
    unit_outage_short_windows_gas: bool | None = None,
    unit_outage_window_hour_grain: bool | None = None,
    campd_per_unit_attribution: bool | None = None,
    campd_outage_merit_order_guard: bool | None = None,
    netload_drag_layup_window_mask: bool | None = None,
    netload_drag_merit_allocation: bool | None = None,
    netload_drag_min_run_persistence: bool | None = None,
    vre_curtailment_oversupply_allocation: bool | None = None,
    spp_curtailment_ceiling: bool | None = None,
    spp_curtail_depth_wind: float | None = None,
    egrid_family_heat_rates: bool | None = None,
    egrid_steam_collapse_heat_rates: bool | None = None,
    caiso_dsw_daytime_evening_trim: bool | None = None,
    cc_summer_derate_reconciled_basis: bool | None = None,
    ercot_reserve_supply_cap_from_year: int | None = None,
    ercot_load_resource_reserve_from_year: int | None = None,
    enable_legacy_p2: bool = False,
) -> None:
    """Re-solve a committed bundle's recipe (its ``meta.json``) end-to-end.

    The CI-dispatchable form of ``scripts/replay_keeper.py``: the bundle's
    ``meta.json`` is the authoritative snapshot of every ``solve_and_persist``
    kwarg, so a keeper/probe recipe reproduces exactly at the dispatched ref —
    including single-delta A/B arms whose delta is a code change — without
    expressing the recipe through the workflow input surface. The dashboard
    job needs only the written bundle (``dashboard_add_run.py`` computes
    metrics itself), so this solves and prints the standard report.

    Args:
        bundle: Committed bundle dir whose ``meta.json`` carries the recipe.
        out_dir: Destination bundle root (``None`` re-solves in place).
        years: Optional solve-span override (defaults to the bundle's years).
            Any year may be solved: ``[R-HOLDOUT]`` was REMOVED 2026-09-09, so
            no marker, freeze or authorization gate remains here.
        note: Provenance note recorded in ``run_config.json`` (empty keeps
            the replay default).
        zero_forcing_ablation: Solve the recipe's D-3 zero-forcing ablation
            twin instead (composes exactly like the flag on a direct solve).
        reliability_floor_plant_exclusions: Override the bundle's setting for the
            reliability-floor per-plant membership exclusion (``None`` keeps the
            recipe's own value). Composes like ``zero_forcing_ablation`` so a
            single-delta A/B arm can be solved from a committed control recipe
            without re-expressing it flag-by-flag (nyiso-140).
        caiso_offer_surface_measured_ungrounded: Override the bundle's setting
            for the un-grounded-class measured band re-grounding (``None``
            keeps the recipe's own value). Composes exactly like the override
            above, so the caiso-231 structural A/B solves both arms from the
            SAME committed control recipe.
        caiso_st_gas_committed_measured: Override the bundle's setting for the
            measured ST_GAS committed band at the ``ST_GAS_PEAKER_PLANTS``
            bypass (``None`` keeps the recipe's own value). Composes exactly
            like the override above, so the caiso-239 structural arm is
            provably the committed keeper recipe plus ONE flag.
        caiso_st_gas_peak_measured: Override the bundle's setting for the
            measured ST_GAS PEAK band at the same ``ST_GAS_PEAKER_PLANTS``
            bypass (``None`` keeps the recipe's own value). The band-disjoint
            sibling of the override above (rule 19 ``[R-ONE-MECH]``), so the
            caiso-240 structural arm is provably the committed keeper recipe
            plus ONE flag.
        campd_per_unit_attribution: Override the bundle's setting for the
            CAMPD per-unit attribution gate (nyiso-176), which selects the
            '-perunit-' tranche and unit-outage companions together.
        unit_outage_mixed_gas_routing: Override the bundle's setting for the
            mixed-gas-facility unit-outage class routing (``None`` keeps the
            recipe's own value). Composes exactly like the two overrides above,
            so the miso-200 A/B solves BOTH legs from the same committed keeper
            recipe and the delta is provably the single flag.
        gas_offer_margin: Override the bundle's setting for the gas-offer
            NET-REVENUE MARGIN form
            (``ScenarioConfig.gas_offer_net_revenue_margin``; ``None`` keeps
            the recipe's own value). Composes exactly like the overrides
            above, so the caiso-251 fuel-coupling-form A/B solves BOTH arms
            from the SAME committed control recipe rather than re-expressing a
            keeper flag-by-flag (caiso-243 §10.4 / caiso-244 §7.7 — a recipe is
            never rebuilt by parameter name).
        ercot_reserve_supply_cap_from_year: Override the bundle's recorded
            ``ercot_reserve_supply_cap_from_year`` (``None`` keeps the recipe's
            own value). A from_year is a data-availability gate, not a fitted
            value: the ercot-252 owner ruling (2026-09-06) moves it 2023 -> 2020
            on the 2022 validation touchpoint because the measured RTOLCAP
            series exists back to 2020. Composes exactly like the overrides
            above, so the arm is provably the committed recipe plus this value.
        ercot_load_resource_reserve_from_year: Override the bundle's recorded
            ``ercot_load_resource_reserve_from_year`` (``None`` keeps the
            recipe's own value) — the paired half of the same ercot-252 ruling
            (the ercot-212 ``net_credits`` construction nets the LR series off
            the cap rows, so the two gates move together); the back-year
            series come from ``scripts/data/build_ercot_as_backyear.py``.
        caiso_dsw_daytime_evening_trim: Override the bundle's recorded
            ``caiso_dsw_daytime_evening_trim`` (the caiso-97 hod 6-21 -> 6-17
            trim of the daytime WEIM clean-transfer window; ``None`` keeps
            the recipe's own value). The flag rides the recorded generic
            override bag (``coal_prb_sigmoid_overrides`` ->
            ``prb_overrides``), so the edit lands on the SAME channel the
            keeper set it through and the caiso-252 arm is provably the
            committed keeper recipe plus this ONE value (caiso-243 §10.4 /
            caiso-244 §7.7 — a recipe is never rebuilt by parameter name).
        cc_summer_derate_reconciled_basis: Override the bundle's recorded
            ``cc_summer_derate_reconciled_basis`` (nyiso-212: the CC summer
            derate divided by the capacity the plant actually carries at every
            cc_capacity_reconcile-listed plant; ``None`` keeps the recipe's own
            value). Rides the SAME recorded generic override bag as
            ``caiso_dsw_daytime_evening_trim`` above, so a rule-29 arm is
            provably the committed keeper recipe plus this ONE value.
        enable_legacy_p2: Unlock the ARCHIVED P2 commitment pass when the
            REPLAYED RECIPE arms it (see :func:`enforce_legacy_p2_kwargs`).
            Without it a bundle recorded with ``commitment=true`` is a hard
            error rather than a silent re-arm.
    """
    from scripts import replay_keeper as rk

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    enforce_legacy_p2_kwargs(kwargs, enable_legacy_p2)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = _load_reference()
    # COMPOSITE per-year recipe (ercot-260), the SAME consumer replay_keeper.main
    # calls so the two replay entry points cannot diverge: meta.json carries ONE
    # config, and a composite bundle's other years solved under a recorded
    # overlay. Consume it for the requested span — or refuse a span that mixes
    # recipes — BEFORE the per-flag overrides below, so an explicit override
    # still wins. A bundle with no overlay block is unaffected.
    rk.enforce_single_recipe_partition(meta, kwargs["years"], kwargs)
    if out_dir is not None:
        kwargs["run_dir"] = out_dir
    if note:
        kwargs["note"] = note
    kwargs["zero_forcing_ablation"] = zero_forcing_ablation
    if reliability_floor_plant_exclusions is not None:
        kwargs["reliability_floor_plant_exclusions"] = (
            reliability_floor_plant_exclusions
        )
    if caiso_offer_surface_measured_ungrounded is not None:
        kwargs["caiso_offer_surface_measured_ungrounded"] = (
            caiso_offer_surface_measured_ungrounded
        )
    if caiso_st_gas_committed_measured is not None:
        kwargs["caiso_st_gas_committed_measured"] = caiso_st_gas_committed_measured
    if caiso_st_gas_peak_measured is not None:
        kwargs["caiso_st_gas_peak_measured"] = caiso_st_gas_peak_measured
    if caiso_ct_peaker_committed_measured is not None:
        kwargs["caiso_ct_peaker_committed_measured"] = (
            caiso_ct_peaker_committed_measured
        )
    if nyiso_ct_peaker_bands_measured is not None:
        kwargs["nyiso_ct_peaker_bands_measured"] = nyiso_ct_peaker_bands_measured
    if nyiso_ct_peaker_committed_measured is not None:
        kwargs["nyiso_ct_peaker_committed_measured"] = (
            nyiso_ct_peaker_committed_measured
        )
    if nyiso_st_gas_econ_bands_deleaked is not None:
        kwargs["nyiso_st_gas_econ_bands_deleaked"] = nyiso_st_gas_econ_bands_deleaked
    if gas_offer_margin is not None:
        kwargs["gas_offer_margin"] = gas_offer_margin
    # ercot-252: the two reserve from_year gates are data-availability gates
    # (owner ruling 2026-09-06, 2023 -> 2020 on the 2022 touchpoint); ``None``
    # keeps the recipe's own value so every existing replay is byte-identical.
    if ercot_reserve_supply_cap_from_year is not None:
        kwargs["ercot_reserve_supply_cap_from_year"] = int(
            ercot_reserve_supply_cap_from_year
        )
    if ercot_load_resource_reserve_from_year is not None:
        kwargs["ercot_load_resource_reserve_from_year"] = int(
            ercot_load_resource_reserve_from_year
        )
    # caiso-243: the two F923 fallback guards compose exactly like the
    # overrides above, so the structural arm is provably the committed keeper
    # recipe plus these flags (``None`` keeps the recipe's own value).
    if nearby_fuel_price_zone_donor_guard is not None:
        kwargs["nearby_fuel_price_zone_donor_guard"] = (
            nearby_fuel_price_zone_donor_guard
        )
    if fleet_state_from_eia860 is not None:
        kwargs["fleet_state_from_eia860"] = fleet_state_from_eia860
    if caiso_citygate_spot_coverage is not None:
        kwargs["caiso_citygate_spot_coverage"] = caiso_citygate_spot_coverage
    if unit_outage_mixed_gas_routing is not None:
        kwargs["unit_outage_mixed_gas_routing"] = unit_outage_mixed_gas_routing
    if unit_outage_st_capacity_basis is not None:
        # miso-201: arm/disarm the ST-side unit-outage capacity BASIS alignment
        # over a committed keeper's recipe, so the A/B solves BOTH legs from the
        # same recipe and the delta is provably the single flag.
        kwargs["unit_outage_st_capacity_basis"] = unit_outage_st_capacity_basis
    if unit_outage_window_hour_grain is not None:
        # nyiso-229: arm/disarm the DETECTED-HOUR outage window grain over a
        # committed keeper's recipe, so the A/B solves BOTH legs from the same
        # recipe and the delta is provably the single flag.
        kwargs["unit_outage_window_hour_grain"] = unit_outage_window_hour_grain
    if unit_outage_per_unit_clip is not None:
        # miso-202: arm/disarm the per-unit removal clip over a committed
        # keeper's recipe, so the A/B solves BOTH legs from the same recipe and
        # the delta is provably the single flag.
        kwargs["unit_outage_per_unit_clip"] = unit_outage_per_unit_clip
    if unit_outage_short_windows_gas is not None:
        # pjm-d4-4: arm/disarm the GAS-side sub-5-day outage scope over a
        # committed keeper's recipe, so the A/B solves BOTH legs from the same
        # recipe and the delta is provably the single flag.
        kwargs["unit_outage_short_windows_gas"] = unit_outage_short_windows_gas
    if campd_per_unit_attribution is not None:
        # nyiso-176: arm/disarm the CAMPD per-unit attribution gate over a
        # committed keeper's recipe, so the re-baseline A/B is a single delta
        # against a byte-faithful control leg.
        kwargs["campd_per_unit_attribution"] = campd_per_unit_attribution
    if campd_outage_merit_order_guard is not None:
        # nyiso-177: the lay-up guard rides the SAME replay path, so a
        # vintage-matched availability basis is reachable from a keeper recipe.
        kwargs["campd_outage_merit_order_guard"] = campd_outage_merit_order_guard
    if netload_drag_layup_window_mask is not None:
        # ercot-256: the net-load drag's lay-up WINDOW MASK rides the same
        # replay path, so the single-field A/B arm is the keeper's recorded
        # recipe plus one flag.
        kwargs["netload_drag_layup_window_mask"] = netload_drag_layup_window_mask
    if netload_drag_merit_allocation is not None:
        # ercot-259: the net-load drag's MERIT ALLOCATION rides the same
        # replay path, so the single-field A/B arm is the keeper's recorded
        # recipe plus exactly this one flag.
        kwargs["netload_drag_merit_allocation"] = netload_drag_merit_allocation
    if netload_drag_min_run_persistence is not None:
        # pjm-177: the net-load drag's MIN-RUN HOUR ELIGIBILITY rides the same
        # replay path, so the single-field A/B arm is the keeper's recorded
        # recipe plus exactly this one flag.
        kwargs["netload_drag_min_run_persistence"] = netload_drag_min_run_persistence
    if vre_curtailment_oversupply_allocation is not None:
        # SPP-51c: the curtailment ALLOCATION arm is the keeper's recorded
        # recipe plus exactly this one flag.
        kwargs["vre_curtailment_oversupply_allocation"] = (
            vre_curtailment_oversupply_allocation
        )
    if spp_curtailment_ceiling is not None:
        # SPP-58: the SPP wind curtailment CEILING arm is the keeper's recorded
        # recipe plus exactly this one flag (it disarms the allocation in
        # data.renewables itself, rule 19 [R-ONE-MECH]).
        kwargs["spp_curtailment_ceiling"] = spp_curtailment_ceiling
    if spp_curtail_depth_wind is not None:
        kwargs["spp_curtail_depth_wind"] = float(spp_curtail_depth_wind)
    if egrid_family_heat_rates is not None:
        # nyiso-184: the eGRID family heat-rate construction rides the same
        # replay path, so the single-field A/B arm is the keeper's recorded
        # recipe plus exactly this one field.
        kwargs["egrid_family_heat_rates"] = egrid_family_heat_rates
    if egrid_steam_collapse_heat_rates is not None:
        # nyiso-189: the steam-collapse identity rides the same replay path, so
        # the single-field A/B arm is the keeper's recorded recipe plus exactly
        # this one field.
        kwargs["egrid_steam_collapse_heat_rates"] = egrid_steam_collapse_heat_rates
    if caiso_dsw_lateevening_clean is not None:
        # caiso-269: the late-evening clean flag is NOT a direct
        # solve_and_persist kwarg — backcast_config carries no parameter for
        # ANY of the CAISO DSW clean-depth flags (the keeper arms
        # caiso_dsw_surplus_clean / _overnight_clean / _daytime_clean through
        # the recorded generic override bag), so the override edits that bag in
        # place (a COPY; the recipe dict is never mutated) exactly as the
        # caiso-252 evening-trim override below does. The arm is therefore the
        # keeper recipe plus this one value.
        _bag_key = next(
            (k for k in ("prb_overrides", "coal_prb_sigmoid_overrides") if k in kwargs),
            "prb_overrides",
        )
        _bag = dict(kwargs.get(_bag_key) or {})
        _bag["caiso_dsw_lateevening_clean"] = bool(caiso_dsw_lateevening_clean)
        kwargs[_bag_key] = _bag
    if mustrun_chp_btm_holdout is not None:
        # miso-253: the injected-must-run host-steam partition is not a direct
        # solve_and_persist kwarg -- it is read at the LP seam through the
        # recorded generic override bag (the caiso-80-safe channel), so the
        # override edits that bag in place (a COPY; the recipe dict is never
        # mutated) exactly as its neighbours here do. The arm is therefore the
        # keeper recipe plus this ONE boolean.
        _bag_key = next(
            (k for k in ("prb_overrides", "coal_prb_sigmoid_overrides") if k in kwargs),
            "prb_overrides",
        )
        _bag = dict(kwargs.get(_bag_key) or {})
        _bag["mustrun_chp_btm_holdout"] = bool(mustrun_chp_btm_holdout)
        kwargs[_bag_key] = _bag
    if caiso_dsw_daytime_evening_trim is not None:
        # caiso-252: the evening-trim flag is not a direct solve_and_persist
        # kwarg — the keeper carries it in the recorded generic override bag —
        # so the override edits that bag in place (a COPY, the recipe dict is
        # never mutated) and the arm is the keeper recipe plus this one value.
        _bag_key = next(
            (k for k in ("prb_overrides", "coal_prb_sigmoid_overrides") if k in kwargs),
            "prb_overrides",
        )
        _bag = dict(kwargs.get(_bag_key) or {})
        _bag["caiso_dsw_daytime_evening_trim"] = bool(caiso_dsw_daytime_evening_trim)
        kwargs[_bag_key] = _bag
    if cc_summer_derate_reconciled_basis is not None:
        # nyiso-212: same channel, same discipline as the caiso-252 override
        # directly above — the recorded bag is COPIED and edited, never the
        # recipe dict, so the arm is the keeper recipe plus this one value.
        _bag_key = next(
            (k for k in ("prb_overrides", "coal_prb_sigmoid_overrides") if k in kwargs),
            "prb_overrides",
        )
        _bag = dict(kwargs.get(_bag_key) or {})
        _bag["cc_summer_derate_reconciled_basis"] = bool(
            cc_summer_derate_reconciled_basis
        )
        kwargs[_bag_key] = _bag
    if zero_forcing_ablation:
        # D-3 linkage: the twin's run_config must name its base bundle
        # (the dashboard and audit_keepers pair twins by ablation_of).
        kwargs["ablation_of"] = bundle.name
    run_dir = solve_and_persist(**kwargs)
    report_run(run_dir)


def main() -> None:
    """Solve + persist a timestamped bundle and report it, or report an old one."""
    parser = argparse.ArgumentParser(
        description="Calibration backcast (ERCOT full; other ISOs energy-only): "
        "solve, persist, report."
    )
    parser.add_argument("--year", nargs="+", type=int, default=[2023, 2024])
    parser.add_argument(
        "--iso",
        default="ERCOT",
        help="ISO to backcast. ERCOT runs the full plant-level diagnostic; "
        "other ISOs (e.g. PJM) run energy-only (generic fuel-mix / price "
        "/ interchange report; ERCOT-only steps skipped).",
    )
    parser.add_argument("--hours", type=int, default=_HOURS_PER_YEAR)
    parser.add_argument(
        "--no-xyear-warmstart",
        action="store_true",
        help="Disable cross-year LP warm-start (MARKET_SIM_WARMSTART_XYEAR). "
        "It is ON by default for a fresh calibration solve — each year's "
        "optimal basis warm-starts the next year's P0 (~2.3x faster on warm "
        "years, basis-neutral; see docs/cross-year-warmstart.md). Pass this "
        "for the cold path (e.g. a basis-independent A/B baseline). An "
        "explicit MARKET_SIM_WARMSTART_XYEAR env var is honored over the "
        "default; this flag overrides both. No effect on --report / "
        "--replay-bundle / --rebuild-benchmark (those stay at the global "
        "default OFF for reproducibility).",
    )
    parser.add_argument(
        "--no-p1-basis-seed",
        action="store_true",
        help="Disable the same-year P1 basis seed (MARKET_SIM_P1_BASIS_SEED). "
        "It is ON by default for a fresh calibration solve — on the ISOs "
        "whose keeper carries a P1-native floor bridge (ERCOT / NYISO gas "
        "commitment bridges, CAISO RA must-offer) the P1 cold-rebuilds a "
        "second model on the floored fleet, and the seed hands it the P0 "
        "model's optimal basis instead of starting from nothing (ERCOT 2025 "
        "P1 287 -> 139 s; warm-start class, marginal-tie only; see "
        "docs/cross-year-warmstart.md 'Same-year P1 basis seed'). Inert "
        "wherever the P1 re-solves the live P0 model, and hard-OFF under "
        "--no-xyear-warmstart / MARKET_SIM_WARMSTART_XYEAR=0 (the goldens "
        "pin) — the seed lives inside the cross-year gate. An explicit "
        "MARKET_SIM_P1_BASIS_SEED env var is honored over the default; this "
        "flag overrides both. No effect on --report / --replay-bundle / "
        "--rebuild-benchmark (global default OFF).",
    )
    parser.add_argument(
        "--cf-band-width",
        type=float,
        default=_CF_BAND_WIDTH,
        help="CF-band width for the [7b] per-plant operating-level histogram "
        "and plant_cf_bands.parquet, as a fraction of capacity "
        f"(default {_CF_BAND_WIDTH}). Use 0.05 for twenty bands of 5 "
        "points each to see where an efficient CC loses its high-CF hours.",
    )
    parser.add_argument(
        "--enable-legacy-p2",
        action="store_true",
        help="Unlock the ARCHIVED P2 commitment pass (last resort). P0/P1 are the "
        "only production passes and every run is scored on P1 (CLAUDE.md "
        '"Dispatch & Commitment"). The P2 flags (--commitment, '
        "--ercot-as-aware-commitment, --run-p2, --no-coal-p2, --persist-p2-state, "
        "--class-commitment-overrides) are hidden and inert unless this is passed; "
        "using any of them without it is an error. Not part of any keeper config.",
    )
    parser.add_argument(
        "--commitment",
        action="store_true",
        # ARCHIVED P2 trigger — hidden from --help, gated behind --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-coal-p2",
        action="store_true",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    # Locked calibration config ("tier pass 2"): per-plant CAMPD coal must-run,
    # gas-keyed PRB passthrough sigmoid (tiered baseload/follower), POF dropped
    # on coal. All on by default; use the --no-* form to disable.
    #
    # Coal flag family: generated from the declarative registry
    # (market_sim.pipeline.flags.FLAG_REGISTRY['coal']) instead of 15
    # hand-written add_argument calls — the single encoding that closes the
    # ERCOT-65 drift class (CLI spelling / solve kwarg / recorded name).
    # Option strings, dests, actions and help text are byte-equivalent to
    # the definitions this replaced; only their position in --help moves
    # (the family now renders as one contiguous run).
    add_flag_arguments(parser, "coal")
    parser.add_argument(
        "--outage-source",
        choices=["historic", "statistical"],
        default="historic",
        help="Coal/CC availability: 'historic' overlays actual >10-day ERCOT "
        "outages (default backcast); 'statistical' uses WEFOR/POF only.",
    )
    parser.add_argument(
        "--ct-mustrun-per-plant",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Inject a per-plant CT_PEAKER reliability must-run floor from each "
        "peaker's observed EIA-923 monthly net generation "
        "(fleet.ct_mustrun_floor_mwh_by_plant). The energy-only LP prices "
        "simple-cycle peakers out (~0%% CF) where the actuals show a ~4%% "
        "reserve/reliability run; the floor recovers that energy. WEFOR and "
        "the planned-outage derate are exempt for floor units (the floor is "
        "observed generation and already nets out real outages). Backcast-"
        "only; off by default.",
    )
    parser.add_argument(
        "--ct-mustrun-floor-frac",
        type=float,
        default=1.0,
        help="Fraction of observed monthly CT_PEAKER net generation forced as "
        "the reliability floor (default 1.0 = full observed energy). "
        "Requires --ct-mustrun-per-plant.",
    )
    parser.add_argument(
        "--ercot-ep-gas-basis-monthly",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="ERCOT only (ercot-254). Resolve the measured TX "
        "electric-power delivered-gas LEVEL anchor at its native MONTHLY "
        "resolution (EP[m]/1.036 - HH[m]) instead of collapsing it to one "
        "annual mean. The annual form is a resolution mismatch and fails "
        "outright when a year's within-year distribution is extreme "
        "(February 2021 is 30.7 sigma above the other eleven months, so the "
        "2021 annual mean lifts every ordinary hour by +5.78 $/MMBtu). "
        "No-op unless the ERCOT zonal gas basis is also on. Off by default.",
    )
    parser.add_argument(
        "--ercot-ep-gas-basis-corroborated",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="ERCOT only (ercot-261). CORROBORATION sub-gate on the monthly "
        "level above: use a month's own measured basis only where a second, "
        "independent measurement of the same quantity (EIA-923 Schedule-5 TX "
        "quantity-weighted plant receipts) confirms the N3045TX3 survey print "
        "within ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU; otherwise fall back to "
        "the mean over that year's corroborated months. The EIA print is a "
        "monthly cost/volume RATIO, not a price, in a month whose within-month "
        "distribution is extreme -- applied at monthly resolution the cheapest "
        "February 2021 day still prices gas at $31.26/MMBtu. Measured "
        "2019-2025 the two series agree within $0.85/MMBtu in 82 of 84 months, "
        "so this fires in no year but 2021. Requires "
        "--ercot-ep-gas-basis-monthly. Off by default.",
    )
    parser.add_argument(
        "--ercot-ep-gas-basis-receipts-fallback",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="ERCOT only (ercot-265). RECEIPTS FALLBACK sub-gate inside the "
        "corroboration filter above: when the two independent measurements "
        "disagree, fill the held-out month from the EIA-923 Schedule-5 receipt "
        "series (what the plants ACTUALLY PAID, quantity-weighted over the same "
        "population) instead of from the year's corroborated mean, which "
        "discards BOTH measurements and prices an extraordinary month at an "
        "ordinary level. Feb-2021 receipts are $45.96/MMBtu across 36 plants on "
        "28.4 million MMBtu, the year's largest burn month. Rule 14 "
        "[R-ACCURATE]; zero free parameters (the tolerance, the admissibility "
        "test and the fail-closed discipline are untouched). Fires in no year "
        "but 2021, so the 2023-2025 train tier is byte-identical. Requires "
        "--ercot-ep-gas-basis-corroborated. Off by default.",
    )
    parser.add_argument(
        "--ct-deployment",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Inject the per-plant CT_PEAKER AS/RUC-deployment hourly floor "
        "(outages.ct_deployment_floor_for_year, built by "
        "scripts/data/derive_ct_deployment.py): in the measured out-of-merit "
        "hours where the RT price was below a peaker's marginal cost, floor "
        "it to its observed CEMS output, recovering the ~1.4-2.3 TWh/yr of "
        "AS/reliability deployment energy the energy-only LP omits — WITHOUT "
        "flooring CT to its full CEMS output (in-merit hours stay "
        "economic). A pure LP min-gen bound (no MIP). Backcast-only; off by "
        "default.",
    )
    parser.add_argument(
        "--ct-deployment-floor-frac",
        type=float,
        default=1.0,
        help="Fraction of the measured deployment energy forced (default 1.0). "
        "Lower it if a year would overshoot its CT class bar. Requires "
        "--ct-deployment.",
    )
    parser.add_argument(
        "--reliability-deployment",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Inject the spatial reliability-deployment hourly floor "
        "(outages.reliability_deployment_floor_for_year, built by "
        "scripts/data/derive_reliability_deployment.py): the generalization of "
        "--ct-deployment to the load-pocket thermal fleet "
        "(CC_REGULAR/COAL/ST_GAS/CC_CHP in South_Central/West/Northeast). "
        "In the hours where a pocket plant was economic at its LOCAL "
        "load-zone price yet out of merit at the system hub, floor it to "
        "its observed CEMS output, recovering the ~2.7-5.2 TWh/yr of "
        "intra-zonal congestion energy the single-system-price LP omits — "
        "reducing the North over-run and the SC/West/NE under-run WITHOUT "
        "flooring to full CEMS. A pure LP min-gen bound (no MIP). "
        "Backcast-only; off by default.",
    )
    parser.add_argument(
        "--reliability-deployment-floor-frac",
        type=float,
        default=1.0,
        help="Fraction of the measured congestion energy forced (default 1.0). "
        "Lower it if a year would overshoot a pocket class bar. Requires "
        "--reliability-deployment.",
    )
    parser.add_argument(
        "--statistical-mode",
        action="store_true",
        help="Out-of-sample (forecast-machinery) backcast: disable every "
        "per-hour / per-year answer-injection overlay in one switch — "
        "historic outage overlay (->statistical WEFOR/POF), the CT "
        "AS/RUC-deployment floor, the spatial reliability-deployment "
        "floor, the ST WEFOR-residual relief, and per-plant EIA-923 "
        "monthly coal pricing (->fall back to the supply-class "
        "trajectory). Keeps the STRUCTURAL model (per-plant heat rates, "
        "committed floors, offer curves, gas-keyed coal passthrough "
        "sigmoids, cc-duct band, storage daily cycling) and the realized "
        "annual Henry Hub gas price (the 'realized-fuel' variant, "
        "isolating dispatch machinery from fuel-forecast error). "
        "Residual backcast devices that have no clean toggle and stay on "
        "(documented small-order): the 2023-only ERCOT wind HSL rescale, "
        "the nuclear monthly-CF overlay, and per-plant CEMS emission "
        "rates (the latter does not affect dispatch at carbon_price=0). "
        "Overrides any conflicting overlay flag.",
    )
    parser.add_argument(
        "--no-coal-monthly-pricing",
        dest="no_coal_monthly_pricing",
        action="store_true",
        help="Disable per-plant EIA-923 monthly delivered coal pricing "
        "(coal_plant_monthly_pricing) so every coal plant falls back to "
        "its supply-class trajectory. A single-overlay ablation knob "
        "(implied by --statistical-mode).",
    )
    parser.add_argument(
        "--ct-intermediate-split",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Route intermediate-duty simple-cycle CTs (measured CAMPD median "
        "CF >= the threshold; EIA-860-confirmed genuine GT/IC, not mislabeled "
        "CCs) to the flatter CT_INTERMEDIATE offer curve so their always-on "
        "energy clears, instead of the steep true-peaker curve that holds them "
        "idle and over-runs CC_REGULAR. MISO cohort "
        "(fleet.ct_intermediate_plants).",
    )
    parser.add_argument(
        "--ct-intermediate-cf-threshold",
        type=float,
        default=None,
        help="Median-CF cut (percent) for the --ct-intermediate-split cohort "
        "(default 50.0): CT_PEAKER units at or above this measured CAMPD median "
        "capacity factor are treated as intermediate-duty.",
    )
    parser.add_argument(
        "--cc-intermediate-split",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Route baseload-duty combined-cycle plants (measured CAMPD median "
        "CF >= the threshold) to the flatter CC_INTERMEDIATE offer curve so the "
        "upper operating-range tranches clear, instead of the CC_REGULAR curve "
        "(fit to ERCOT's duct-fire-heavy peaker CCs) whose rising econ ramp "
        "over-prices an already-committed baseload CC and under-runs the fleet "
        "(the MISO 2023/2024 gas-CC under-run). Flattens only the econ ramp to "
        "the measured near-baseload incremental cost; the physical duct-burner "
        "peak is unchanged. MISO cohort (fleet.cc_intermediate_plants).",
    )
    parser.add_argument(
        "--cc-intermediate-cf-threshold",
        type=float,
        default=None,
        help="Median-CF cut (percent) for the --cc-intermediate-split cohort "
        "(default 50.0): CC_REGULAR units at or above this measured CAMPD median "
        "capacity factor are treated as baseload-duty.",
    )
    parser.add_argument(
        "--tranche-startup-amortization",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fast-start tranche pricing (ISO-NE Order 825 analogue): the "
        "fast-start-capable tranches (CT_PEAKER/CT_CHP econ+peak; the CC "
        "duct/quick-response peak band) carry the same NREL start cost "
        "(fleet.BIN_STARTUP_COST_PER_MW) as the committed anchor, so the P1 "
        "markup amortizes each tranche's own P0 run lengths into its bid. "
        "Prices the fuel-price-invariant commitment-cost component of the "
        "real offer stack (a peak block run 4 evening hours bids "
        "+startup/4 per MWh; a block marginal around the clock bids ~+0), "
        "which the heat-rate-multiplier curve cannot express. CC econ blocks "
        "are excluded: block-loading a committed CC is not a fast start; its "
        "start costs are NCPC uplift, not LMP. Default OFF -> prior keepers "
        "byte-identical.",
    )
    parser.add_argument(
        "--tranche-startup-measured-runs",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fast-start amortization v3 (requires "
        "--tranche-startup-amortization): the simple-cycle CT tranches "
        "amortize the NREL start cost over the unit's CAMPD-MEASURED median "
        "start-to-stop run length (scripts/data/derive_campd_ct_run_lengths.py "
        "artifact, pooled 2023-2025, ISO-class fallback) as the horizon "
        "ceiling - the endogenous P0 run may only SHORTEN it. Removes the v2 "
        "circularity where too-cheap offers -> long P0 blocks -> ~0 markup "
        "-> the lever self-disables (nyiso-44 probe finding). CC peak bands "
        "keep the v2 P0 basis. Default OFF.",
    )
    parser.add_argument(
        "--tranche-startup-conditional-runs",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fast-start amortization v4 (requires "
        "--tranche-startup-amortization --tranche-startup-measured-runs): "
        "the v3 measured run-length ceiling scales per hour by the "
        "CAMPD-measured net-load-percentile band ratio "
        "(derive_campd_ct_run_lengths.py --condition-bands -> "
        "campd_ct_run_bands_<ISO>.csv) - a tight-hour engagement is a "
        "shorter commitment block, so its start recovery amortizes over "
        "fewer hours (the ELMP evening-timing element; MISO measures 6 h "
        "top-band vs 10 h pooled). Forward-native trigger (within-year "
        "net-load percentile); per-ISO artifact, no cross-ISO fallback; "
        "no-op without the artifact. Default OFF.",
    )
    parser.add_argument(
        "--gas-offer-margin",
        dest="gas_offer_margin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Gas-offer NET-REVENUE MARGIN form (markup compression, "
        "ScenarioConfig.gas_offer_net_revenue_margin): each CAMPD gas band's "
        "markup ABOVE its measured physical heat-rate basis (the offer "
        "curve's phys_* keys, CAMPD marginal-HR artifact) is repriced from "
        "the fuel-scaled multiplier to a fixed $/MWh margin identified at "
        "the ISO's training-window delivered-gas anchor "
        "(constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO, "
        "derive_gas_offer_margin_anchor.py). Offers reduce EXACTLY to the "
        "registered multipliers at anchor gas and compress toward true MC "
        "off-distribution (the 2022 NEISO holdout rotation). ISOs without a "
        "derived anchor hard-fail; ISOs without phys_* keys are inert. "
        "Design: docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md. "
        "Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--caiso-dsw-daytime-evening-trim",
        dest="caiso_dsw_daytime_evening_trim",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="REPLAY-ONLY override (--replay-bundle) of the recorded "
        "ScenarioConfig.caiso_dsw_daytime_evening_trim: --no-... restores the "
        "caiso-94 daytime WEIM clean-transfer window to hod 6-21 with the "
        "committed untrimmed depth; --... forces the caiso-97 trimmed window. "
        "Absent (default None) keeps the bundle's own value, so the replay "
        "path is byte-identical (caiso-252).",
    )
    parser.add_argument(
        "--cc-summer-derate-reconciled-basis",
        dest="cc_summer_derate_reconciled_basis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="REPLAY-ONLY override (--replay-bundle) of the recorded "
        "ScenarioConfig.cc_summer_derate_reconciled_basis (nyiso-212): --... "
        "makes the cc_nameplate_summer_derate Jun-Sep multiplier "
        "min(1, net_summer / carried capacity) at every "
        "cc_capacity_reconcile-listed CC plant instead of net_summer / "
        "nameplate applied to an already-reconciled capacity; --no-... forces "
        "the incumbent nameplate ratio. Absent (default None) keeps the "
        "bundle's own value, so the replay path is byte-identical.",
    )
    parser.add_argument(
        "--gas-offer-margin-zonal-anchor",
        dest="gas_offer_margin_zonal_anchor",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Resolve --gas-offer-margin's identification anchor PER ZONE "
        "(nyiso-109, ScenarioConfig.gas_offer_margin_zonal_anchor). The "
        "mechanism's identity is that at fuel == anchor the reformed offer "
        "reduces EXACTLY to the registered band multiplier — a statement "
        "about a unit's OWN delivered fuel — but the ISO anchor is derived "
        "from the ISO-level _gas_series, which does NOT carry the per-zone "
        "basis the solve applies afterwards. On an ISO with a zonal basis "
        "(NYISO: the reference zone keeps Iroquois Z2 and every other zone "
        "shifts DOWN to its own hub) a unit outside the reference zone "
        "therefore prices its markup at a fuel level it never pays. When "
        "set, each gas tranche prices its markup at ITS ZONE's anchor "
        "(constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE, "
        "derive_gas_offer_margin_anchor.py --by-zone). Requires "
        "--gas-offer-margin; a band-scoped rebasis anchor still wins "
        "(rule 19). ISOs without a zone table hard-fail. Default OFF -> "
        "prior keepers byte-identical.",
    )
    parser.add_argument(
        "--coal-offer-margin",
        dest="coal_offer_margin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Coal-offer NET-REVENUE MARGIN form (ERCOT-137, "
        "ScenarioConfig.coal_offer_net_revenue_margin — the gas form's coal "
        "analogue): the CAMPD coal _mustrun (take-or-pay) band is repriced "
        "from the fitted VOM-only sunk-fuel discount ($4.50/MWh, refuted by "
        "ERCOT-136 — the real fleet offers only 5.8-8.4 %% of capability at "
        "or below $4.50) to full delivered-fuel tracking plus a "
        "fuel-invariant measured margin: at the training-window "
        "delivered-coal anchor the bid lands EXACTLY on the measured RT "
        "curve bottom (SCED Submitted TPO-Price1 cap-wtd p50, 98.8-100 %% "
        "coverage). Identification constants: "
        "constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO / _LEVEL_BY_ISO "
        "(derive_coal_offer_margin_anchor.py). ISOs without a derived pair "
        "hard-fail (rule 24); the committed/econ supply sigmoids above the "
        "block are untouched (rule 19). Default OFF -> prior keepers "
        "byte-identical.",
    )
    parser.add_argument(
        "--cc-committed-offer-margin",
        dest="cc_committed_offer_margin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="CC committed-block MEASURED offer level (ERCOT-139, "
        "ScenarioConfig.cc_committed_offer_margin — the coal min-load form's "
        "gas-CC analogue): the CC_REGULAR _committed tranche is repriced from "
        "its band multiplier (0.998 x base HR) to full delivered-fuel "
        "tracking plus a fuel-invariant measured margin, so at the SHARED "
        "delivered-gas anchor the bid lands EXACTLY on the measured RT curve "
        "bottom (SCED Submitted TPO-Price1 cap-wtd p50, 95.1-98.0 %% curve "
        "coverage). Repairs the defect ERCOT-138 sized: the model's CC bands "
        "bid +$2.8-6.6/MWh too DEAR through the crossing band while coal's "
        "are exonerated, because the model has no below-cost committed-CC "
        "block at all. Identification constant: "
        "constants.CC_COMMITTED_OFFER_LEVEL_BY_ISO "
        "(derive_cc_committed_offer_margin.py); the anchor is the shared "
        "GAS_OFFER_MARGIN_ANCHOR_BY_ISO (rule 19 — one identification point "
        "for the whole gas offer surface). ISOs without a derived level "
        "hard-fail (rule 24); econ/peak bands and every other class are "
        "untouched (rule 19). Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--coal-peak-offer-margin",
        dest="coal_peak_offer_margin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Coal _peak-tranche MEASURED gas-anchored offer margin "
        "(ERCOT-140, ScenarioConfig.coal_peak_offer_margin — the coal "
        "offer-curve UPPER-TAIL successor ERCOT-123 section 7.2 chartered): "
        "the CAMPD coal _peak tranche is repriced from its band-multiplier x "
        "sigmoid composition to the measured top-decile level (SCED "
        "Submitted TPO-Price1 cap-wtd p90 of above-min-load capability) at "
        "the SHARED delivered-gas anchor, with the corpus's own measured GAS "
        "slope. Repairs the defect ERCOT-138 section 5.6 sized: at p90 the "
        "model's coal curve runs $9.6-15.5/MWh UNDER measured in all four "
        "subsets (fully offered by ~$32-34 vs a real top needing $500). The "
        "slope basis is GAS, not coal (the measured top tracks gas while "
        "delivered coal moved the other way - gas-parity opportunity "
        "pricing); coal-fuel tracking is REMOVED on the repriced rows by "
        "measurement. Identification constants: "
        "constants.COAL_PEAK_OFFER_LEVEL_BY_ISO / "
        "COAL_PEAK_OFFER_GAS_HR_BY_ISO (derive_coal_peak_offer_margin.py); "
        "the anchor is the shared GAS_OFFER_MARGIN_ANCHOR_BY_ISO (rule 19). "
        "ISOs without derived values hard-fail (rule 24); every other coal "
        "row, every gas curve and the measured availability envelope are "
        "untouched (rules 14/19). Default OFF -> prior keepers "
        "byte-identical.",
    )
    parser.add_argument(
        "--coal-perplant-offer-level",
        dest="coal_perplant_offer_level",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PER-PLANT measured coal offer curves (ERCOT-144, "
        "ScenarioConfig.coal_perplant_offer_level — the DOF-retirement lane "
        "ERCOT-143 section 2 chartered): every CAMPD coal _committed/_econ* "
        "tranche is repriced to the capacity-weighted measured price of its "
        "capacity window on its own plant's merged modal 60-Day SCED "
        "Submitted TPO supply curve. The measured finding is CROSS-PLANT "
        "LEVEL DISPERSION of near-flat per-plant curves — the object the "
        "residual-identified COAL_* offer_curve_by_group multipliers and "
        "the gas-keyed supply sigmoids were standing in for — so arming "
        "this is a rule-19 REPLACEMENT: COAL_* groups are stripped from "
        "offer_curve_by_group and the PRB/lignite sigmoids + coal econ "
        "marginal-HR floor are disarmed. _mustrun (ERCOT-137) and _peak "
        "(ERCOT-140) rows keep their own measured owners. Identification: "
        "constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO "
        "(derive_coal_perplant_offer.py); ISOs without derived curves "
        "hard-fail (rule 24). Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--coal-perplant-offer-yearly",
        dest="coal_perplant_offer_yearly",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PER-YEAR windowed per-plant coal offer curves (ercot-168, "
        "ScenarioConfig.coal_perplant_offer_yearly — matrix section 5.1 "
        "item 12's rule-23 re-derivation of the armed ERCOT-144 "
        "identification from the delivery-2023 NP3-965 corpus, replacing "
        "the DOF ledger's declared 2024/25->2023 extrapolation). Requires "
        "--coal-perplant-offer-level. For a solve year PRESENT in "
        "constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO (only 2023), "
        "committed/econ tranches of listed plants are priced per "
        "(months x hours) window on the window's own merged measured curve "
        "— the same window mapping, per cell; _mustrun/_peak keep their "
        "ERCOT-137/ERCOT-140 owners; a year ABSENT from the table falls "
        "through to the static registry unchanged (2024/2025 "
        "byte-identical — the ercot-168 precommit's G-BIT kill gate). "
        "Identification: derive_coal_perplant_offer.py --year 2023. "
        "Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--coal-peak-offer-yearly-level",
        dest="coal_peak_offer_yearly_level",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PER-YEAR coal `_peak`-tranche offer LEVEL (ercot-192, "
        "ScenarioConfig.coal_peak_offer_yearly_level — matrix section 5.1 "
        "item 13, owner signature B1 on DECISION-CARD-ercot188 card B: the "
        "rule-23 re-derivation of the armed ERCOT-140 level from the "
        "delivery-2023 NP3-965 corpus, replacing its declared 2024/25->2023 "
        "extrapolation). Requires --coal-peak-offer-margin. For a solve year "
        "PRESENT in constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO (only 2023, "
        "71.3378 $/MWh) the `_peak` bid is level_year + GAS_HR x (gas_cc(t) - "
        "anchor); the SLOPE and the SHARED gas anchor are untouched (rule 19). "
        "A year ABSENT from the table falls through to the static "
        "COAL_PEAK_OFFER_LEVEL_BY_ISO unchanged (2024/2025 byte-identical — "
        "the ercot-192 precommit's G-BIT kill gate). Identification: the "
        "constant's own ERCOT-138 p90 instrument on the delivery-2023 rows "
        "(75.00 $/MWh), whose coverage objection is closed by an exact "
        "identification BOUND rather than any repair "
        "(scripts/probes/ercot192_coal_limbs_bound_phase0.py). "
        "Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--nyiso-solar-market-generator-basis",
        dest="nyiso_solar_market_generator_basis",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="NYISO front-of-meter solar capacity basis (rule 14 [R-ACCURATE] "
        "input correction, NYISO-only). EIA-860's NY utility-scale solar "
        "population includes ~2 GW of distribution-connected NY-Sun community "
        "solar that is not a NYISO market generator and is already netted out "
        "of the EIA-930 NYIS demand series used as load (NYIS 'NG: SUN' is "
        "identically zero, nyiso-106), so carrying it as grid supply "
        "double-counts it. When set, NYISO solar capacity comes from NYISO's "
        "own Gold Book Table III-2a market-generator registry "
        "(data/raw/reference/nyiso-market-solar-capacity.csv). Zero free "
        "parameters. Default OFF -> prior keepers byte-identical.",
    )
    parser.add_argument(
        "--nysdec-peaker-rule",
        dest="nysdec_peaker_rule_availability",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="NYSDEC 6 NYCRR Subpart 227-3 peaker-rule availability overlay "
        "(NYISO): the curated unit-level compliance schedule "
        "(data/raw/reference/nysdec-227-3-peaker-compliance.csv, NYISO Gold "
        "Book Tables IV-3..IV-6 2023-2025) zeroes/derates each restricted "
        "unit's availability inside its effective ozone-season (May 1-Sep 30) "
        "windows. Availability ONLY, never an offer/price change (rule-#12 "
        "class of the CAMPD outage windows). STAR-designated barges "
        "(Gowanus 2&3 / Narrows 1&2) are documented but never restricted. "
        "Default OFF.",
    )
    parser.add_argument(
        "--oil-primary-bin-fuel",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Measured EIA-860 oil-primary fuel correction: gas-CT bins of "
        "plants whose plant-registry primary fuel OR generator-level EIA-860 "
        "Energy Source 1 majority (DFO/RFO/KER/JF, GT/IC prime movers) is "
        "oil/kerosene are repriced on distillate. CLI-explicit counterpart "
        "of the legacy ERCOT_OIL_PRIMARY env gate. Default OFF.",
    )
    parser.add_argument(
        "--st-gas-intermediate",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="MISO intermediate gas-steam structure (one consolidated lever, "
        "default OFF → prior keepers / other ISOs byte-identical). The legacy "
        "ST_GAS fleet (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine, "
        "...) runs intermediate-duty, not as peakers. Routes the measured "
        "median-CF cohort (fleet.st_gas_intermediate_plants) to the flatter "
        "ST_GAS_INTERMEDIATE offer curve; feeds the ST_GAS startup cost + "
        "min-run into the P1 bid markup so steam drags rather than cycling like "
        "a peaker; and replaces the ERCOT-fitted ST_GAS WEFOR base (0.21) with a "
        "realistic gas-steam EFOR (0.10). Fixes the Moselle / Lewis Creek "
        "under-run. (The net-load reliability-drag floor / Little Gypsy "
        "weather-dependent must-run is NOT bundled in — the ScenarioConfig drag "
        "coefficients are ERCOT-derived and saturate at MISO's net-load scale; "
        "enable separately via --gas-st-netload-drag only once MISO-specific "
        "coefficients are derived.)",
    )
    parser.add_argument(
        "--st-gas-intermediate-cf-threshold",
        type=float,
        default=None,
        help="Median-CF cut (percent) for the --st-gas-intermediate cohort "
        "(default 50.0): ST_GAS units at or above this measured CAMPD median "
        "capacity factor are routed to the flatter ST_GAS_INTERMEDIATE curve.",
    )
    parser.add_argument(
        "--wefor-residual",
        type=float,
        default=None,
        help="Historic-backcast WEFOR residual: cap the statistical "
        "forced-outage rate of the overlay-covered classes (coal + "
        "CC_REGULAR/CC_CHP/ST_GAS/ST_CHP) at this short-outage floor "
        "(e.g. 0.015) — the CAMPD overlay + unit derate already carry "
        "every >=5-day outage, so the full WEFOR double-counts them. "
        "Default None keeps the full statistical WEFOR (prior "
        "behavior). CTs are unaffected.",
    )
    parser.add_argument(
        "--prb-sigmoid-tiered",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use a separate follower-tier PRB passthrough sigmoid for "
        "low-must-run load-follower plants (coal_prb_follower_*).",
    )
    parser.add_argument(
        "--report",
        metavar="DIR",
        default=None,
        help="Skip solving; print the report from an existing bundle directory.",
    )
    parser.add_argument(
        "--replay-bundle",
        metavar="DIR",
        default=None,
        help="Re-solve a committed bundle's exact recipe: DIR/meta.json "
        "supplies every solve kwarg (scripts/replay_keeper.py's mapping), so "
        "a keeper/probe recipe reproduces without expressing it flag-by-flag "
        "— the CI-dispatchable replay recipe, formerly the removed calibration-run.yml (extra_flags). "
        "--out-dir/--note override the destination and provenance note; "
        "--year (if given) overrides the solved span, still holdout-gated; "
        "--zero-forcing-ablation composes to solve the recipe's D-3 ablation "
        "twin. All other solve flags are ignored on this path (the bundle IS "
        "the config).",
    )
    parser.add_argument(
        "--rebuild-benchmark",
        metavar="DIR",
        default=None,
        help="Rebuild a bundle's benchmark parquets (EIA-923 w/ CAMPD "
        "backfill, EIA-930, CAMPD) off its meta and re-report — no "
        "dispatch re-solve.",
    )
    parser.add_argument(
        "--persist-p2-state",
        action="store_true",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--persist-p0-commitment",
        action="store_true",
        help=(
            "Also write hourly/p0_commitment_<year>.parquet (bit-packed P0 "
            "on/off pattern) and hourly/startup_run_ratio_<year>.parquet. "
            "WRITE-ONLY and additive — cannot change a solve. Lets a later "
            "session replay the PRODUCTION P1 startup amortization "
            "bit-identically instead of reconstructing it from P1 prices."
        ),
    )
    parser.add_argument(
        "--persist-p0-dispatch",
        action="store_true",
        help=(
            "Also write hourly/p0_dispatch_<year>.parquet (the P0 dispatch in "
            "MW, float64, packed per generator) and "
            "hourly/p0_prices_<year>.parquet (the P0 zonal duals, with their "
            "zone NAMES). WRITE-ONLY and additive — cannot change a solve. "
            "The MW-valued sibling of --persist-p0-commitment: the on/off "
            "pattern recovers the RA-bridge detector's runs, this pair "
            "recovers the two screens that act on them, so a later session "
            "can replay caiso_ra_mustoffer_min_gen exactly at zero LP."
        ),
    )
    parser.add_argument(
        "--run-p2",
        metavar="DIR",
        default=None,
        # ARCHIVED P2 post-process — hidden; gated behind --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Bundle root (default results/calibration/<iso>/<timestamp>).",
    )
    parser.add_argument(
        "--reuse-solved",
        default=None,
        metavar="PRIOR_BUNDLE",
        help="OPT-IN: copy per-year solve artifacts from PRIOR_BUNDLE (a "
        "local bundle dir) instead of re-solving each --year whose effective "
        "per-year ScenarioConfig (cache_key) and full solve recipe exactly "
        "match this invocation's, with code + data pinned: refuses whenever "
        "the working tree is dirty under src/scripts/data, src/scripts/data "
        "changed since the prior bundle's commit, any untracked/derived file "
        "under data/ is newer than the prior bundle, the highspy version "
        "moved, or a year's Henry Hub actual / artifacts differ (see "
        "plan_reuse_solved for what the key does and does NOT cover). Years "
        "failing any check solve fresh; the mix is labeled in meta.json "
        "under 'reuse'. REUSED YEARS ARE NOT FRESH EVIDENCE — they are "
        "byte-copies of the prior solve; keeper promotion still requires a "
        "full fresh solve of every year. Absent this flag, behavior is "
        "byte-identical to today: a fresh timestamped bundle with every "
        "year solved.",
    )
    parser.add_argument(
        "--zero-forcing-ablation",
        action="store_true",
        help="Solve the D-3 zero-forcing ablation TWIN of this config: every "
        "merchant floor/bridge is neutralized (keeping only nuclear must-run, "
        "CHP steam-following and coal take-or-pay) via "
        "ScenarioConfig.as_zero_forcing_ablation. The bundle lands in "
        "<out-dir>-ablation (or the default path with an '-ablation' suffix), "
        "covers the SAME full year span as the keeper, and records "
        '"ablation_of": <base bundle> in run_config.json. Register it beside '
        "its keeper (registry/<id>-ablation.json, linked from the keeper "
        'sidecar\'s "ablation_twin"); audit_keepers E9 requires it. Solve as a '
        "concurrent separate invocation from the keeper (rule 12).",
    )
    parser.add_argument(
        "--note",
        default="",
        help="Free-text note describing pre-run model changes; recorded in "
        "the bundle's run_config.json alongside the full config and git "
        "provenance.",
    )
    # PRB passthrough sigmoid floor/ceiling tune (baseload + follower tiers).
    # None leaves the ScenarioConfig default in place.
    parser.add_argument(
        "--prb-floor",
        type=float,
        default=None,
        help="Baseload PRB sigmoid cheap-gas floor.",
    )
    parser.add_argument(
        "--prb-ceil",
        type=float,
        default=None,
        help="Baseload PRB sigmoid dear-gas ceiling.",
    )
    # Coal flag family: generated from the declarative registry
    # (market_sim.pipeline.flags.FLAG_REGISTRY['coal']) further up — the three
    # coal add_argument calls that used to sit here (--coal-bit-sigmoid,
    # --coal-econ-srmc-bound, --coal-econ-marginal-hr-bound) moved into it.
    # ERCOT-118 EP-basis rebasis of the measured CC DAM band multipliers:
    # replace the pooled HH-0.50-derived CC_REGULAR/CC_CHP override bands with
    # the committed PER-YEAR tables normalized on the EP-anchored delivered-gas
    # series dispatch actually prices gas at (offer_curve_dam_hrmults_ep_yearly
    # .json, rule-23 derive citation in its _provenance), re-applying the run's
    # offer_curve_deltas on the rebased base. TRI-STATE (default None, the
    # ercot-115 seam lesson): None = keep the ScenarioConfig/prb-resolved
    # value; the --no- form forces it off for ablation arms.
    # ROUTE A "REPLACE" — the COMMITTED band's MEASURED basis (pjm-h6,
    # chartered by docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md
    # §4/§10a). ONE mechanism, TWO coupled halves, never armed apart (rule 19
    # [R-ONE-MECH]). TRI-STATE (default None, the ercot-115 seam pattern):
    # None = keep the config-resolved value (False for every ISO and every
    # lane); --no- forces it off so a control arm can scrub it.
    parser.add_argument(
        "--committed-band-measured-basis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="REPLACE every offer-curve class's `committed` band multiplier "
        "with that class's own MEASURED avg_committed_p50 "
        "(data/raw/reference/<iso>_campd_marginal_hr_summary.csv) AND drop the "
        "gas-keyed coal supply passthrough sigmoid from the coal `committed` "
        "band only, so the min-load block's effective basis IS the measured "
        "value in every hour. Non-selective (every covered class, never one); "
        "econ*/peak bands and mustrun keep the sigmoid. Zero free parameters.",
    )
    parser.add_argument(
        "--ercot-offer-hrmult-ep-rebasis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Rebase the measured CC DAM band multipliers (committed/econ_low/"
        "econ_high/peak, CC_REGULAR+CC_CHP) onto the EP-anchored dispatch "
        "gas basis with per-year tables (ERCOT-118; ERCOT-only, rule 25).",
    )
    # ERCOT-119 leg-split of the EP rebasis: restrict it to the named artifact
    # bands (e.g. econ_low econ_high), keeping the peak standing wall (and its
    # ladder rungs and window margin anchor) at the run's resolved values.
    # TRI-STATE (default None): None = keep the ScenarioConfig/prb-resolved
    # scope, whose own default None rebases every artifact band (ERCOT-118).
    parser.add_argument(
        "--ercot-offer-hrmult-ep-rebasis-bands",
        nargs="+",
        default=None,
        metavar="BAND",
        help="Band scope for --ercot-offer-hrmult-ep-rebasis (ERCOT-119 "
        "leg-split), e.g. econ_low econ_high. Unknown band names hard-fail; "
        "omit to rebase every artifact band.",
    )
    parser.add_argument(
        "--bit-floor", type=float, default=None, help="Bit sigmoid cheap-gas floor."
    )
    parser.add_argument(
        "--bit-ceil", type=float, default=None, help="Bit sigmoid dear-gas ceiling."
    )
    parser.add_argument(
        "--bit-gas-mid",
        type=float,
        default=None,
        help="Bit sigmoid logistic midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--bit-gas-slope",
        type=float,
        default=None,
        help="Bit sigmoid logistic slope (per $/MMBtu).",
    )
    # Gas-keyed lignite passthrough sigmoid (ERCOT mine-mouth fleet). Off by
    # default — turning it on replaces full fuel cost on lignite
    # above-must-run tranches with a logistic of the monthly delivered gas
    # price (the bid discounts; the measured ~$1.45/MMBtu delivered price
    # stays the full-cost anchor).
    parser.add_argument(
        "--lignite-floor",
        type=float,
        default=None,
        help="Lignite sigmoid cheap-gas floor.",
    )
    parser.add_argument(
        "--lignite-ceil",
        type=float,
        default=None,
        help="Lignite sigmoid dear-gas ceiling.",
    )
    parser.add_argument(
        "--lignite-gas-mid",
        type=float,
        default=None,
        help="Lignite sigmoid logistic midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--lignite-gas-slope",
        type=float,
        default=None,
        help="Lignite sigmoid logistic slope (per $/MMBtu).",
    )
    # Subbituminous passthrough sigmoid: the derived EIA-923 rank tag
    # (e.g. PJM's two PRB-by-rail plants delivered into PJM market
    # conditions) — a separate supply chain from the curated ERCOT "prb"
    # tag, with its own per-ISO curve. Off by default = full fuel cost.
    parser.add_argument(
        "--sub-floor",
        type=float,
        default=None,
        help="Subbituminous sigmoid cheap-gas floor.",
    )
    parser.add_argument(
        "--sub-ceil",
        type=float,
        default=None,
        help="Subbituminous sigmoid dear-gas ceiling.",
    )
    parser.add_argument(
        "--sub-gas-mid",
        type=float,
        default=None,
        help="Subbituminous sigmoid logistic midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--sub-gas-slope",
        type=float,
        default=None,
        help="Subbituminous sigmoid logistic slope (per $/MMBtu).",
    )
    # Waste-coal passthrough sigmoid (culm/gob, the PJM COAL_WC class).
    # Near-free reclamation fuel: no cheap-gas discount, only a dear-gas
    # bid markup to suppress high-gas-year over-run. Off by default =
    # full fuel cost.
    parser.add_argument(
        "--waste-floor",
        type=float,
        default=None,
        help="Waste-coal sigmoid cheap-gas floor.",
    )
    parser.add_argument(
        "--waste-ceil",
        type=float,
        default=None,
        help="Waste-coal sigmoid dear-gas ceiling.",
    )
    parser.add_argument(
        "--waste-gas-mid",
        type=float,
        default=None,
        help="Waste-coal sigmoid logistic midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--waste-gas-slope",
        type=float,
        default=None,
        help="Waste-coal sigmoid logistic slope (per $/MMBtu).",
    )
    parser.add_argument(
        "--prb-follower-floor",
        type=float,
        default=None,
        help="Follower-tier PRB sigmoid floor.",
    )
    parser.add_argument(
        "--prb-follower-ceil",
        type=float,
        default=None,
        help="Follower-tier PRB sigmoid ceiling.",
    )
    parser.add_argument(
        "--prb-gas-mid",
        type=float,
        default=None,
        help="Baseload PRB sigmoid gas-price midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--prb-gas-slope",
        type=float,
        default=None,
        help="Baseload PRB sigmoid slope (per $/MMBtu).",
    )
    parser.add_argument(
        "--prb-follower-gas-mid",
        type=float,
        default=None,
        help="Follower-tier PRB sigmoid gas-price midpoint ($/MMBtu).",
    )
    parser.add_argument(
        "--prb-follower-gas-slope",
        type=float,
        default=None,
        help="Follower-tier PRB sigmoid slope (per $/MMBtu).",
    )
    parser.add_argument(
        "--chp-startup-covered",
        action="store_true",
        help="Exempt CHP classes (CC_CHP/CT_CHP/ST_CHP) from the P1 startup"
        "-amortization markup: a steam-host-obligated cogen never pays "
        "a cold start on its own account, so its energy bid carries no "
        "startup component.",
    )
    parser.add_argument(
        "--wefor-relief-groups",
        default=None,
        help="Comma-separated plant groups the --wefor-residual cap applies "
        "to (e.g. 'ST_GAS,ST_CHP'). Default (unset) keeps the legacy "
        "scope: every CAMPD-covered class (coal + CC/ST + CHP). Use to "
        "relieve only the class with a measured availability deficit "
        "(ST_GAS) while leaving CC/coal on the full statistical model.",
    )
    parser.add_argument(
        "--committed-ramp-spread",
        type=float,
        default=None,
        help="Render the per-plant committed band as an n-slice rising ramp "
        "spanning committed_mult x (1 +/- this fraction) instead of one "
        "flat block, so a plant clears its committed capacity "
        "progressively with price rather than snapping to the full "
        "committed share in one hour. Targets the under-populated "
        "mid-CF-band (bimodal dispatch). Mean bid unchanged. Unset = "
        "flat block (no change).",
    )
    parser.add_argument(
        "--storage-daily-cycling",
        action="store_true",
        help="Cap storage to within-day arbitrage: each unit's SOC must "
        "return to its day-start level every 24h (bounds the single-LP "
        "perfect-foresight advantage). Off = annual-cyclic (default).",
    )
    parser.add_argument(
        "--storage-vintage-ramp",
        action="store_true",
        help="Force the EIA-860 storage COD/retirement vintage ramp on: "
        "battery and pumped-storage dispatch caps step up at each unit's "
        "Operating Month and out again at its Planned Retirement Month, "
        "instead of a flat year-end fleet. On by default for CAISO/ERCOT/"
        "NEISO backcasts; this flag forces it for any ISO.",
    )
    parser.add_argument(
        "--strict-demand-profile",
        action="store_true",
        help="Fail closed instead of silently falling back to the corrupted "
        "legacy eia_demand_profiles/eia_demand_meta series when the "
        "repaired demand-profile clean partition is missing for an (iso, "
        "year) the repair covers (raises DemandProfileNotRepairedError). "
        "Off by default (warn-and-fall-back, byte-identical to prior "
        "behavior).",
    )
    parser.add_argument(
        "--as-reserve-withholding",
        action="store_true",
        help="ERCOT upper-bound probe: remove the hourly cleared DAM up-AS MW "
        "(RegUp/RRS/ECRS/Non-Spin, from "
        "scripts/data/build_ercot_as_withholding.py) from thermal headroom "
        "before the supply curve clears. Books all AS to thermal (no "
        "storage/load split). Off = no withholding (default).",
    )
    parser.add_argument(
        "--energy-reserve-coopt",
        action="store_true",
        help="PJM energy+reserve co-optimization inside the LP: add a per-unit "
        "reserve variable sharing each unit's headroom with energy, a "
        "reserve-balance constraint at the structural 1.5x-MSSC Primary "
        "Reserve requirement, and the published two-step ORDC demand curve "
        "as priced shortfall steps, so the reserve clearing price emerges "
        "as a dual and lifts the energy LMP. Replaces the post-solve ORDC "
        "overlay. PJM-only. Off = energy-only LP (default).",
    )
    parser.add_argument(
        "--ercot-multiproduct-as-coopt",
        action="store_true",
        help="ERCOT MULTI-PRODUCT AS co-optimization: replace the single lumped "
        "contingency-reserve co-opt product with one additive, cascading demand "
        "curve per AS product (RegUp/RRS/ECRS/NonSpin), so the binding product's "
        "reserve dual is the MCPC the measured DAM-AS overlay reads, formed "
        "endogenously. Requires --energy-reserve-coopt; pair with --commitment "
        "for the phantom-headroom fix. ERCOT-only. Off (default).",
    )
    parser.add_argument(
        "--miso-zonal-reserves",
        action="store_true",
        help="MISO locational reserve families on top of the market-wide RBDC "
        "co-opt: one zonal operating-reserve family per zone (default "
        "MISO-South), requirement = within-zone MSSC (BPM-002 3.3.2 zonal "
        "minimum, the pre-determined largest zonal event), priced at the "
        "published Zonal Operating Reserve Demand Curve (BPM-002 5.2.1.2 / "
        "Schedule 28-A: $200 / $1,100 / VOLL-minus-zonal-reg steps). "
        "Requires --energy-reserve-coopt. MISO-only; default off.",
    )
    parser.add_argument(
        "--miso-midwest-subregional-reserves",
        action="store_true",
        help="MISO Midwest sub-regional reserve-holding family on top of the "
        "market-wide RBDC co-opt: the measured North+Central operating-reserve "
        "reservation held IN the 5 physical Midwest zones "
        "(reserve_config.MISO_MIDWEST_ZONES), reserve_class 0 nested inside the "
        "market-wide requirement. Requirement = the measured hourly Midwest "
        "cleared series when --miso-measured-reserve-requirements is on, else "
        "the within-region MSSC; a single shortfall step prices at the "
        "published Reserve Procurement Enhancement demand value ($200/MWh, 2024 "
        "SOM III.B — the per-Reserve-Zone ORDC ladder is NOT used, it is "
        "measured-refuted). Closes the congestion-blind market-wide family's "
        "phantom-South-parking gap; energy-side, does not make the reserve "
        "curves fire. Zero fitted scalars. Requires --energy-reserve-coopt. "
        "MISO-only; default off (miso-71 engagement-depth lane).",
    )
    parser.add_argument(
        "--ercot-ecrs-conservative-deployment",
        action="store_true",
        help="ERCOT: represent the PUBLISHED pre-reform ECRS deployment design "
        "on the multi-product co-opt's ECRS demand curve — from ECRS go-live "
        "(2023-06-10, data-carried) through 2024-07-31 ECRS had NO price-based "
        "release to SCED (manual reliability deployment only; IMM 2023 SOM: "
        "'artificial shortage pricing … doubled average energy prices' Jun-Dec "
        "2023, >$12B), so the ECRS family prices as a single step AT THE OFFER "
        "CAP; from 2024-08-01 (operating-procedure release trigger; PUCT "
        "rejected NPRR1224's $750 floor 2024-07-25) it reverts to the standing "
        "VOLL-anchored ramp. Published market-design dates, no fitted "
        "parameter. Requires --energy-reserve-coopt + "
        "--ercot-multiproduct-as-coopt. ERCOT-only. Off (default).",
    )
    parser.add_argument(
        "--ercot-nonreleasable-as-withholding",
        action="store_true",
        help="ERCOT: represent the PUBLISHED pre-RTC+B RRS + Reg-Up deployment "
        "design as rigid at-cap reserve demand — capacity awarded RRS/Reg-Up "
        "is carved out of the SCED-dispatchable range (HASL − AS Resource "
        "Responsibility, Nodal Protocols §6.5.7.6.2.3 / §3.17) with NO "
        "price-based SCED release in any pre-RTC+B year (RRS deploys on "
        "under-frequency / EEA events, Reg-Up through LFC only; the "
        "2024-08-01 release reform applied to ECRS alone), so each family "
        "prices as a single step AT THE OFFER CAP through RTC+B go-live "
        "(2025-12-05) and reverts to the standing VOLL-anchored ramp (the "
        "ASDC representation) after. Published market-design dates, no "
        "fitted parameter. Requires --energy-reserve-coopt + "
        "--ercot-multiproduct-as-coopt. ERCOT-only. Off (default).",
    )
    parser.add_argument(
        "--ercot-ordc-total-reserve",
        action="store_true",
        help="ERCOT: layer the lumped ORDC TOTAL-reserve demand curve (the "
        "published RTORPA mechanism, NPRR568/OBDRR048) on top of the "
        "multi-product AS families — one extra all-class reserve-balance "
        "family drawing on the SUM of every product's cleared reserve, so "
        "product withholding AND the total-reserve LOLPxVOLL curve price "
        "together (the faithful pre-RTC+B stack). No new reserve columns, "
        "no new headroom; published market design, zero fitted parameters. "
        "Requires --energy-reserve-coopt + --ercot-multiproduct-as-coopt. "
        "ERCOT-only. Off (default).",
    )
    parser.add_argument(
        "--ercot-ordc-cap-dual-adder",
        action="store_true",
        help="ERCOT: source the post-solve additive RTORPA from the "
        "reserve-supply-cap rows' own duals instead of the total-family "
        "balance dual. The balance dual is already folded into the energy "
        "LMP whenever the physical shared headroom (not the RTOLCAP cap "
        "row) is the binding reserve constraint, so re-adding it "
        "double-prices those hours; the cap-row dual is exactly the "
        "uninternalized component in both regimes (LP duality: "
        "lambda_balance = lambda_cap + mu_headroom, and only mu passes "
        "into the energy dual). Same published-ORDC construction, no new "
        "parameter, no price fit. Requires --ercot-reserve-supply-cap. "
        "ERCOT-only. Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-ordc-adder-published-anchor",
        action="store_true",
        help="ERCOT (ercot-213): price the cap-additive RTORPA on the "
        "PUBLISHED (VOLL - lambda) anchor and from a SINGLE counterpart. "
        "The in-LP ORDC demand curve is VOLL-anchored (an LP objective "
        "coefficient must be a constant), which is the co-optimization-"
        "correct form; the published additive formula is "
        "RTORPA = 0.5 (VOLL - lambda) (LOLP_full + LOLP_half), capped so "
        "lambda + adder <= VOLL. Adding the VOLL-anchored dual verbatim, "
        "summed over BOTH headroom tiers, can therefore write up to "
        "2 x VOLL - a price the market design cannot produce. Under this "
        "flag the additive component is the ALL-tier (total-reserve) cap "
        "dual alone, rescaled by (VOLL - lambda)/VOLL and capped at "
        "VOLL - lambda. Exact re-anchoring, zero new scalars (VOLL is the "
        "registered ordc_voll; lambda is the LP's own demand-weighted "
        "energy dual). Requires --ercot-ordc-cap-dual-adder. ERCOT-only. "
        "Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-ordc-adder-family-counterpart",
        action="store_true",
        help="ERCOT (ercot-215): decontaminate the published-anchor adder's "
        "single counterpart. One capped reserve MW serves an AS-product "
        "row and the ORDC total row simultaneously, so the all-tier cap "
        "dual is the SUM of the ORDC total family's own balance-row dual "
        "and the AS-product shortfall-ramp steps (measured exact, "
        "gamma_all = k x VOLL/ercot_as_n_ramp + gamma_fam, in 808/808 "
        "writing hours 2023-25). 2023-25 ERCOT prices no RT per-product "
        "scarcity (a product-vs-capability squeeze triggers RUC, not a "
        "price), so under this flag the written component is "
        "min(gamma_all, gamma_fam) — the ORDC component alone; the ramp's "
        "in-LP withholding role is untouched. Zero fitted scalars (both "
        "operands are LP duals). Requires "
        "--ercot-ordc-adder-published-anchor. ERCOT-only. Off (default, "
        "keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-storage-as-product-credit",
        action="store_true",
        help="ERCOT multi-product co-opt, measured storage path: net the "
        "measured hourly battery AS award (60-Day DAM per-resource-type "
        "series) pro-rata off the fast products' (RegUp/RRS/ECRS) "
        "requirements, so the products do not pull the batteries' awarded "
        "MW from thermal headroom. The multi-product analogue of "
        "--ercot-storage-as-reserve's requirement netting; same from-year "
        "gate. No-op under --ercot-storage-as-endogenous. Off (default).",
    )
    parser.add_argument(
        "--ercot-nuclear-unit-availability",
        action="store_true",
        help="ERCOT backcast: replace the NUCLEAR_MONTHLY_CF_BY_YEAR "
        "fleet-month smear with the measured per-reactor DAILY refuel "
        "availability from the 60-Day DAM disclosure NUC Resource Status "
        "(data/raw/ercot-nuclear-availability.csv, monthly energy "
        "reconciled to the same EIA-923 anchor; "
        "scripts/data/derive_ercot_nuclear_availability.py). Window-grain "
        "measured availability — the nuclear analogue of the CAMPD fossil "
        "outage windows (rule 14); uncovered dates keep the monthly smear. "
        "Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--nuclear-unit-availability",
        action="store_true",
        help="Backcast, non-ERCOT ISOs: replace the "
        "NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month smear with the measured "
        "per-reactor DAILY availability from the NRC daily Power Reactor "
        "Status reports (data/raw/nuclear-availability-<ISO>.csv, monthly "
        "energy reconciled to the same EIA-923 anchor — the anchor owns the "
        "LEVEL, NRC owns the TIMING; "
        "scripts/data/derive_nuclear_availability.py). The ISO-generic "
        "sibling of --ercot-nuclear-unit-availability (which keeps ERCOT's "
        "own flag/file); a reactor power state is a physical availability "
        "event (rule 13), zero fitted scalars. Uncovered reactors/dates — "
        "including any month the deriver drops for the thermal-vs-net wedge "
        "— keep the monthly smear. Off (default, keeper-reproducing); an "
        "ISO with no derived extract is a no-op.",
    )
    parser.add_argument(
        "--ercot-thermal-dam-availability",
        action="store_true",
        help="ERCOT backcast: rescale the CC_REGULAR/CT_PEAKER classes' "
        "availability so each class-day mean equals the measured 60-Day DAM "
        "disclosure fraction (config-collapsed live Gen_Resource HSL over "
        "site ratings; data/raw/ercot-thermal-dam-availability.csv, "
        "scripts/data/derive_ercot_thermal_dam_availability.py). Replaces the "
        "statistical WEFOR/EFOR estimate of the same quantity with its "
        "measured realization (rule 14; the thermal analogue of "
        "--ercot-nuclear-unit-availability); uncovered dates keep the "
        "statistical model. Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-thermal-dam-availability-hourly",
        action="store_true",
        help="ERCOT backcast: apply the measured DAM thermal availability at "
        "class-HOUR grain (per-Hour-Ending fraction from the same 60-Day DAM "
        "disclosure rows; data/raw/ercot-thermal-dam-availability-hourly.csv) "
        "instead of the day-flat block — the ERCOT-96 grain switch keeping "
        "the afternoon ambient-derate dip the day mean discards (ERCOT-95 "
        "Finding 6: +216 MW mean phantom CC+CT on the 181 actual 2023 tail "
        "hours). No effect unless --ercot-thermal-dam-availability is also "
        "on. Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-thermal-dam-availability-plant",
        action="store_true",
        help="ERCOT backcast: redistribute the measured DAM availability to the "
        "PLANT grain (ERCOT-97) — pin each accepted DAM-site->EIA-plant "
        "crosswalk plant (data/raw/reference/ercot-dam-plant-crosswalk.csv, "
        "build_ercot_dam_resource_crosswalk.py) to its own measured site-hour "
        "fraction and water-fill the unmapped remainder so the class-HOUR total "
        "is unchanged (within-class redistribution, ~259 MW-mean per-plant "
        "misallocation the class grain smears; zero fitted parameters). "
        "Requires --ercot-thermal-dam-availability-hourly. Off (default, "
        "keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-wind-zone-shape",
        action="store_true",
        help="ERCOT: give each zone its own MERRA-2 reanalysis wind SHAPE "
        "(NASA POWER WS50M at the zone's EIA-860 wind-plant locations through "
        "a turbine power curve, data/raw/ercot-wind-shape/) instead of one "
        "ISO-wide hourly profile on every zone — the ERCOT-113 analogue of "
        "MISO's per-zone wind shape. The measured night/afternoon ratio "
        "separates the nocturnal-jet West/North/Panhandle from the "
        "Gulf-sea-breeze South, which one ISO-wide profile averages together. "
        "Purely SPATIAL: the ISO aggregate is preserved exactly every hour, so "
        "annual wind energy and the ISO-wide bound cannot move — only WHICH "
        "ZONE holds the wind, hence when the West/Panhandle curtailment "
        "ceiling and the zonal links bind. Off (default, keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-storage-capability-measured",
        action="store_true",
        help="ERCOT backcast: re-base the battery fleet's hourly power cap on "
        "the measured 60-Day DAM disclosure registered non-OUT storage HSL "
        "(PWRSTR rows; ESR rows post-RTC+B), replacing the EIA-860 COD-ramped "
        "power basis (~2 GW low in both audited summers — "
        "docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md). EIA-860 "
        "stays the zone-split and duration basis; uncovered dates (Oct-2023 "
        "hole) keep EIA-860 (rule 14; the storage analogue of "
        "--ercot-thermal-dam-availability). data/raw/ercot-storage-capability.csv, "
        "scripts/data/derive_ercot_storage_capability.py. Off (default, "
        "keeper-reproducing).",
    )
    parser.add_argument(
        "--ercot-online-capacity-envelope-measured",
        action="store_true",
        help="ERCOT: MEASURED-FLEET-BASIS G-22 on-line-capacity envelope (the "
        "ercot57 joint round, owner-sanctioned 2026-07-11): the extreme "
        "14-bin envelope row with the share re-derived as committed on-line "
        "HSL over MEASURED AVAILABLE capacity for the disclosure-covered "
        "classes (CC_REGULAR/CT_PEAKER) and the LP basis switched to the "
        "fleet's finished availability (measured under "
        "--ercot-thermal-dam-availability), separating commitment choice "
        "from outage state (ERCOT_ONLINE_CAP_SHARE_MEASURED / "
        "_DELIV_PROFILE_MEASURED; scripts/data/derive_ercot_rtolcap_forward.py "
        "--emit online-cap-measured-constant; gate "
        "scripts/validate_ercot_online_capacity.py --measured). Mutually "
        "exclusive with the other envelope flags. Off (default).",
    )
    parser.add_argument(
        "--ercot-ordc-only-scarcity",
        action="store_true",
        help="ERCOT: pre-RTC+B ORDC-ONLY reserve-scarcity pricing (the "
        "ercot57 product-ladder design, owner-sanctioned 2026-07-11): the "
        "per-product NYISO-imported kxVOLL/12 shortfall ladders become a "
        "single plan-hold epsilon step (products held when headroom exists, "
        "released along the ORDC total curve — Nodal Protocols §6.5.7.5: RT "
        "reserve scarcity prices only via the ORDC; a product squeeze "
        "triggers RUC, not a price). The pre-reform ECRS_withheld family "
        "keeps its rigid VOLL step (IMM-documented no-release design). "
        "Requires --ercot-ordc-total-reserve. Off (default).",
    )
    parser.add_argument(
        "--gas-hh-monthly-shape",
        action="store_true",
        help="Replace the generic climatological monthly gas SHAPE with the "
        "measured Henry Hub monthly shape for the year, hour-weight-"
        "normalized so the annual mean stays exactly the trusted annual "
        "level (fuel.gas_seasonal_shape). Measured commodity-price shape "
        "(rule #12 delivered fuel prices) — the reconciled variant the "
        "Run-77 postmortem named; the raw EIA-923 receipt LEVEL swap "
        "remains rejected for ERCOT. Forward years keep the generic shape. "
        "Off (default).",
    )
    parser.add_argument(
        "--miso-reserve-pergen",
        action="store_true",
        help="MISO PER-ASSET reserve co-optimization: one R column per "
        "(zone, fuel-class) pool of reserve-eligible units, joint P+R <= cap "
        "per pool-hour, R bounded by the 10-min deliverable class ramp "
        "(FleetArrays.ramp10, NREL/TP-5500-55588). Reserve competes with "
        "energy on the marginal pool and cleared reserve is capped at what "
        "converts to energy in MISO's 10-minute contingency window, so the "
        "RBDC / zonal ORDC families can genuinely run short. Class-level "
        "pooling is the documented 15 GB memory tier. Requires "
        "--energy-reserve-coopt. MISO-only; default off.",
    )
    parser.add_argument(
        "--miso-reserve-online-gated",
        action="store_true",
        help="MISO online-gated reserve SUPPLY (PREREG-miso167 S2): split "
        "each pergen pool's R column into a GATED Reg+Spin product (coupling "
        "row R <= online_rho * sum P over the pool's members — idle capacity "
        "backs none of the synchronised products; measured CAMPD rho, "
        "data.online_reserve_rho) and an UNGATED Supplemental product, with "
        "one NESTED market-wide Reg+Spin family (measured cleared reg+spin "
        "requirement, published Schedule-28 $65/$98 two-step curve) and a "
        "pool-shared 10-min ramp row. Requires --energy-reserve-coopt + "
        "--miso-reserve-pergen + --miso-measured-reserve-requirements; "
        "mutually exclusive with --miso-commitment-posture (rule 19). "
        "MISO-only; default off.",
    )
    parser.add_argument(
        "--miso-commitment-posture",
        action="store_true",
        help="MISO pooled linear commitment-posture lever (design note "
        "docs/multi-iso/miso-scarcity-posture-design-2026-07.md SA): per "
        "non-fast-start pergen pool, an online-capacity variable U with "
        "joint P+R <= U, CEMS-measured min-load coupling P >= mlf*U, an "
        "NREL-class startup charge on dU+, and the reserve cap online-gated "
        "R <= rho*U. Zero fitted parameters; honesty-gated on the measured "
        "MISO ASM cleared-reserve/MCP series (data/raw/MISO-AS), never the "
        "tail residual. Requires --energy-reserve-coopt --miso-reserve-"
        "pergen. MISO-only; default off.",
    )
    parser.add_argument(
        "--miso-measured-reserve-requirements",
        action="store_true",
        help="MISO measured hourly OR requirement basis: the market-wide "
        "RBDC family takes the measured hourly cleared reg+spin+supp series "
        "(data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet) in place of "
        "the flat fleet-MSSC+400 estimate, and the South zonal family takes "
        "the measured South reservation in place of the within-zone-MSSC "
        "static (which overstates the real ~0.3-0.5 GW South holding "
        "several-fold). Rule-13 measured AS power reservation, rule-14 "
        "mandatory swap; shortfall steps keep the published shape and "
        "translate with the hourly requirement (NYISO #1344 convention). "
        "Backcast-only; hard-errors when the intake parquet is absent. "
        "Requires --energy-reserve-coopt. MISO-only; default off.",
    )
    parser.add_argument(
        "--miso-south-seam-split",
        action="store_true",
        help="MISO South-seam external-zone split: host the South seam's "
        "reference-price bands in their own external zone instead of the "
        "shared MISO_external bus, severing the free "
        "South→external→Midwest wheel that bypasses the RDT contract path "
        "(2025 probe: 1.26 GW mean summer wheel vs an RDT S→N that binds "
        "13 h/yr). Structural topology fix (rule 1); requires "
        "--reference-price-interface (default on for MISO). MISO-only; "
        "default off.",
    )
    parser.add_argument(
        "--miso-rdt-tcdc",
        action="store_true",
        help="MISO RDT derate + TCDC pricing: replace the static JOA "
        "contract limits on the RDT pair (3,000 N→S / 2,500 S→N) with the "
        "published 92%% default operating derate and the two-step RDT "
        "Transmission Constraint Demand Curve ($40/MWh at the modeled "
        "limit, $500/MWh from 102%%, hard bound at contract) as priced "
        "one-way tiers (2024 MISO SOM §III.B; MISO/SPP JOA Attach. A). "
        "All parameters published; zero fitted scalars. MISO-only; "
        "default off.",
    )
    parser.add_argument(
        "--miso-zonal-loss-surface",
        action="store_true",
        help="MISO marginal transmission-loss physics (miso-76 M3): split "
        "the Midwest L1-L6 links into one-way pairs whose receiving-end "
        "energy-balance coefficient is 1 - eps(month), eps derived from "
        "MISO's published per-hub MLC record (the dimensionless marginal "
        "delivery-factor deviation surface, frozen derive "
        "scripts/data/derive_miso_loss_surface.py). Zonal duals then "
        "separate by the measured delivery-factor ratio — losses consume "
        "MWh, prices stay duals, zero fitted scalars (charter "
        "docs/handoffs/miso-nc-price-separation-design-2026-07.md §4). "
        "MISO-only; default off.",
    )
    parser.add_argument(
        "--pjm-zonal-loss-surface",
        action="store_true",
        help="PJM marginal transmission-loss physics (pjm-136 M2): split the "
        "internal PJM links into one-way pairs whose receiving-end "
        "energy-balance coefficient is 1 - eps(month), eps derived from "
        "PJM's OWN published per-zone MLC record (the dimensionless marginal "
        "delivery-factor deviation surface, frozen derive "
        "scripts/data/derive_pjm_loss_surface.py). Zonal duals then separate "
        "by the measured delivery-factor ratio — losses consume MWh, prices "
        "stay duals, zero fitted scalars. Addresses the measured copper-plate: "
        "the model's eight PJM zones clear at ONE dual in ~95-96 %% of hours "
        "while PJM's own DA prices separate DOM from AEP-DAYTON in 100 %%, "
        "~20-24 %% of it the loss component. PJM-only; default off.",
    )
    parser.add_argument(
        "--pjm-reserve-pergen",
        action="store_true",
        help="PJM PER-GENERATOR reserve co-optimization "
        "(docs/multi-iso/pjm-reserve-ordc.md Phase 2): pooled R columns for "
        "the reserve-eligible fleet, joint P+R <= cap per pool-hour, R "
        "bounded by the 10-min deliverable ramp (FleetArrays.ramp10), and "
        "the two measured Manual-11 balance families (RTO + MAD subzone) "
        "priced by the published two-step ORDC. Reserve competes with energy "
        "on the marginal pool, so the sub-shortage opportunity cost enters "
        "the LMP endogenously. Requires --energy-reserve-coopt. PJM-only; "
        "default off.",
    )
    parser.add_argument(
        "--pjm-reserve-pergen-sync",
        action="store_true",
        help="PJM per-gen OPPORTUNITY-COST reserve co-opt (the G-20b "
        "successor; pjm-84/85 verdict): adds the SYNCHRONIZED sub-product as "
        "its own measured balance families (RTO sr_req_mw + MAD mad_sr_req_mw"
        ", published Synchronized ORDC rows as filed) and splits each pergen "
        "pool's R column into a SYNC product (online 10-min ramp only — "
        "scoped at the P0->P1 seam from the model's own P0 run pattern, the "
        "pjm-85 plant-online derivation) and a NON-SYNC product (offline "
        "fast-start ramp, Manual 11 sec 4.2), sharing the pool's joint P+R "
        "headroom row. Energy availability is NOT masked — P1's redispatch "
        "around the held reserve prices the sub-shortage opportunity cost. "
        "Requires --energy-reserve-coopt --pjm-reserve-pergen "
        "(--measured-ramp-capability recommended). PJM-only; default off.",
    )
    parser.add_argument(
        "--pjm-reserve-pergen-size-split",
        action="store_true",
        help="PJM pergen SIZE-SPLIT pooling tier (the pjm-87 diagnosis "
        "remedy): splits each base (zone, fuel-class) pool's large plants "
        "(capacity > 1.5x the pool's own mean plant capacity, self-"
        "normalizing threshold, reserve_config."
        "PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE) into individual reserve "
        "columns; smaller plants stay pooled as the base tier. Sharpens the "
        "opportunity-cost signal (pjm-87 found none of the 4 balance rows "
        "ever binds; the pooled-dilution lets the LP source the small "
        "measured requirement from any idle pool) without the memory-"
        "infeasible cost of a full per-plant tier. Requires "
        "--energy-reserve-coopt --pjm-reserve-pergen; composes with "
        "--pjm-reserve-pergen-sync. PJM-only; default off. Profile memory "
        "first (CLAUDE.md #12/#45).",
    )
    parser.add_argument(
        "--pjm-commitment-posture",
        action="store_true",
        help="PJM pooled linear commitment-posture lever — the SAME mechanism "
        "as --miso-commitment-posture, ported not forked (design note "
        "docs/multi-iso/miso-scarcity-posture-design-2026-07.md §A; PJM port "
        "docs/handoffs/pjm-commitment-posture-port-2026-07.md). Per "
        "non-fast-start pergen pool, an online-capacity variable U with joint "
        "P+R <= U, CEMS-measured min-load coupling P >= mlf*U, an NREL-class "
        "startup charge on dU+, and the pergen reserve cap online-gated "
        "R <= ramp10*U, so PJM's published Manual-11 Primary/MAD ORDC families "
        "can run short instead of drawing on ~14 GW of free online headroom "
        "(the pjm-81 blocker). Zero fitted parameters; honesty-gated on the "
        "measured PJM reserve-market series (data/raw/PJM-AS), never the tail "
        "residual (scripts/report_pjm_posture_gate.py). Requires "
        "--energy-reserve-coopt --pjm-reserve-pergen (--measured-ramp-"
        "capability recommended). PJM-only; default off.",
    )
    parser.add_argument(
        "--measured-ramp-capability",
        action="store_true",
        help="Reconcile FleetArrays.ramp10's class 10-minute fractions "
        "against the measured ramp-capability datatype (EIA-860 '10M' "
        "fast-start floor + CAMPD CEMS hourly-envelope ceiling; "
        "data/clean/ramp-capability). Uncovered plants keep the class "
        "estimate. Feeds --pjm-reserve-pergen / --miso-reserve-pergen. "
        "Default off.",
    )
    parser.add_argument(
        "--ercot-as-aware-commitment",
        action="store_true",
        # ARCHIVED P2 trigger — hidden from --help, gated behind --enable-legacy-p2.
        # ERCOT AS-aware commitment: run a P2 commitment screen that values AS
        # revenue (P1 reserve dual x reserve-eligible headroom), not energy margin
        # alone. Requires --energy-reserve-coopt + --ercot-multiproduct-as-coopt.
        # ERCOT-only.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--ercot-reserve-supply-cap",
        action="store_true",
        help="ERCOT reserve-supply re-scope: cap each multi-product co-opt "
        "headroom tier's cleared reserve at the MEASURED online-responsive "
        "capability (RTOLCAP for the fast/spinning tier, RTOLCAP+RTOFFCAP for the "
        "all tier) instead of the over-counted full-fleet headroom, so modeled "
        "reserve tightens into the ~8-12 GW band where ERCOT's ORDC adder fires "
        "(broad-month phantom-headroom fix, Finding 1/G1). Exogenous measured "
        "series, not a price fit. Requires --energy-reserve-coopt + "
        "--ercot-multiproduct-as-coopt; pair with --ordc-lolp-params-path (the "
        "published-ORDC curve). ERCOT-only. Off (default).",
    )
    parser.add_argument(
        "--ercot-reserve-supply-cap-from-year",
        type=int,
        default=2023,
        help="First weather year the ERCOT reserve-supply cap applies "
        "(default 2023; the measured RTOLCAP series exists 2023+).",
    )
    parser.add_argument(
        "--ercot-as-forward-requirement",
        action="store_true",
        help="ERCOT: set each multi-product AS requirement (RegUp/RRS/ECRS/"
        "NonSpin) from a FORWARD formula of forecast drivers (net-load, ramp, "
        "VRE-share, net-load forecast-error, largest-contingency / load-ratio) "
        "per ERCOT's published AS Methodology, instead of reading the measured AS "
        "Plan (ASPLANNP433). The forward analogue of the measured requirement "
        "(G3); the measured series stays the backcast validation target "
        "(modeled-vs-measured requirement MW, not a price fit). Requires "
        "--energy-reserve-coopt + --ercot-multiproduct-as-coopt. ERCOT-only. Off "
        "(default → measured fallback).",
    )
    parser.add_argument(
        "--ercot-load-resource-reserve",
        action="store_true",
        help="ERCOT energy+reserve co-opt only: credit the measured "
        "Load-Resource responsive reserve (RRS-UFR, the under-frequency-"
        "relay RRS only Load Resources provide; ~0.8-0.9 GW, "
        "build_ercot_as_withholding.py for 2024/2025, build_ercot_as_2023.py "
        "for 2023) into the reserve balance by lowering its RHS, so the LP "
        "stops pricing a scarcity adder in non-scarce hours from omitting "
        "load-side reserve. 2023 is now covered (~884 MW). GATED: alters "
        "volumes. Off = no load credit (default).",
    )
    parser.add_argument(
        "--ercot-load-resource-reserve-from-year",
        type=int,
        default=2023,
        help="First weather year the --ercot-load-resource-reserve credit "
        "applies to (default 2023 = every backcast year). The measured load "
        "reserve is real supply the co-opt LP omits, correct every year; on "
        "the measured-storage baseline (storage_as_commitment over-tightens "
        "2023 to 58.4 uncredited) the ~884 MW 2023 load credit corrects the "
        "2023 MAE 16.0->12.1 (run139). Raise it to exclude early years.",
    )
    parser.add_argument(
        "--ercot-storage-as-reserve",
        action="store_true",
        help="ERCOT energy+reserve co-opt + --storage-as-commitment only: credit "
        "the measured battery-provided AS (RegUp/RRS/ECRS, the storage "
        "column of the per-resource-type 60-Day DAM AS awards; ~0.8 GW 2023 "
        "→ ~2.8 GW 2025) back into the reserve balance. --storage-as-"
        "commitment subtracts this MW from the storage power cap and the "
        "reserve block derives reserve room from that reduced cap, so the "
        "committed battery AS is otherwise dropped from reserve supply even "
        "though it is held responsive reserve (in ERCOT's RTOLCAP/RTOFFCAP). "
        "Self-targeting (negligible 2023, largest 2025). GATED: alters "
        "volumes. Off = no storage-AS credit (default).",
    )
    parser.add_argument(
        "--ercot-storage-as-reserve-from-year",
        type=int,
        default=2025,
        help="First weather year the --ercot-storage-as-reserve credit applies "
        "to (default 2025). A modeling scope, not a measured fact: the "
        "credit is physically correct every year, but 2023/2024 each carry "
        "genuine scarcity the ORDC-only model can only reach THROUGH the "
        "reserve over-fire, so crediting them collapses their real tail "
        "(2024 probe: tail 49→7 h >$200, MAE 10.5→12.7). Set to 2023 only "
        "to probe a global credit alongside a genuine scarcity-price "
        "mechanism (see docs/ercot-run131-lmp-decomposition-2026-06.md).",
    )
    parser.add_argument(
        "--ercot-ecrs-requirement",
        action="store_true",
        help="ERCOT energy+reserve co-opt only: ADD the measured ECRS "
        "procurement (~2 GW from 2023-06-10, ASPLANNP433 ECRS rows) to the "
        "reserve-balance requirement. The co-opt models one contingency-reserve "
        "product and never grew when ECRS launched mid-2023, so it under-prices "
        "the broad mid-range across 2023-H2 and 2024/25 (bimodal monthly shape: "
        "VOLL spikes over, moderate months under). Demand-side mirror of the "
        "load/storage supply credits; exogenous ERCOT quantity, NOT a price fit; "
        "the June-2023 onset is carried by the data. GATED: tightens every active "
        "hour, watch the tail. Off (default) = no ECRS requirement.",
    )
    parser.add_argument(
        "--ercot-ecrs-requirement-from-year",
        type=int,
        default=2023,
        help="First weather year the --ercot-ecrs-requirement applies to "
        "(default 2023 = launch year; the data zeroes pre-June-2023 hours).",
    )
    parser.add_argument(
        "--ercot-rtordpa-overlay",
        action="store_true",
        help="ERCOT only: add the measured, regime-gated RTORDPA (Real-Time ORDC "
        "+ Reliability-Deployment Price Adder) to the model system price as a "
        "post-solve, additive overlay (no dispatch/volume change). Read PER YEAR "
        "from data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet (rtordpa "
        "column) — never a 2023 hard-code, so it is backcast-able on any year. "
        "The co-opt already produces an ORDC adder ≈ RTORPA; RTORDPA is the "
        "reliability-deployment component the model has no mechanism for, so it "
        "is additive, not double-counting. Gated to the pre-RTC+B regime "
        "(<= 2025-12-04); near-inert in 2024/25 (tiny measured rtordpa), lifts "
        "2023's out-of-market tail toward actual. Exogenous, NOT a price fit. "
        "Off (default) = byte-identical baseline.",
    )
    parser.add_argument(
        "--ercot-dam-as-overlay",
        action="store_true",
        help="ERCOT only: add the measured DAM AS-scarcity overlay (day-ahead "
        "analogue of --ercot-rtordpa-overlay) to the model system price as a "
        "post-solve, additive overlay (no dispatch/volume change). Read PER YEAR "
        "from data/raw/ercot/ercot_<year>_dam_as_mcpc_hourly.parquet (binding_mcpc "
        "= per-hour max of the cleared RegUp/RRS/ECRS/NonSpin MCPCs, from the "
        "60-Day DAM Disclosure). On hours where ERCOT's DAM co-optimized energy "
        "and AS INTO SCARCITY (binding MCPC above the scarcity threshold), the AS "
        "scarcity rent lifts the day-ahead energy price (DAM SPP = LMP + reserve "
        "price) — the acute May-2024 days (May 8/24/26) the energy+reserve LP, "
        "not reserve-thin there, cannot form. Exogenous ERCOT quantity, NOT a "
        "price fit; gated to the pre-RTC+B regime and scoped to "
        "--ercot-dam-as-overlay-from-year+ (2023 is carried by RTORDPA, not "
        "double-counted). Off (default) = byte-identical baseline.",
    )
    parser.add_argument(
        "--ercot-dam-as-overlay-from-year",
        type=int,
        default=2024,
        help="First weather year the --ercot-dam-as-overlay applies to (default "
        "2024). 2023's day-ahead AS scarcity is the same event the RTORDPA "
        "overlay already carries, so applying both in 2023 double-counts it and "
        "over-fires 2023-H2 (Aug binding-MCPC scarce-hour mean ~$222 >> actual DA "
        "~$147); RTORDPA is near-inert in 2024/25, where DAM-AS co-opt is the "
        "unrepresented channel. Same scoping logic as "
        "--ercot-storage-as-reserve-from-year.",
    )
    parser.add_argument(
        "--ercot-dam-as-scarcity-threshold",
        type=float,
        default=150.0,
        help="AS clearing price ($/MWh) above which --ercot-dam-as-overlay treats "
        "the DAM as having cleared into scarcity (default 150). Competitive DAM AS "
        "clears single-to-low-double digits (2024 product means $6-13); >$150 is "
        "the AS scarcity demand curve, not competitive offers. Not a price fit — "
        "the May-2024 lift is robust ($18-23) across $75-200; the gate only keeps "
        "the overlay inert in non-scarce hours.",
    )
    parser.add_argument(
        "--ordc-lolp-params-path",
        default=None,
        help="Path to ERCOT's published NP6-576-ER LOLP table (season/tod_block/"
        "mu_mw/sigma_mw CSV, e.g. data/raw/_validation-source/"
        "ercot_ordc_lolp_params.csv). Replaces the neutral flat fallback "
        "(mu=0, sigma=1400) in the co-opt ORDC demand curve with the published "
        "mu/sigma. Grounded input, not fitted; the curve then begins pricing "
        "reserve at the real reserve level rather than ~920 MW too low.",
    )
    parser.add_argument(
        "--as-reserve-formula",
        action="store_true",
        help="CAISO formula-based operating-reserve withholding: remove "
        "R(t) = max(MSSC, 0.067*load) + 0.01*load (WECC MORC contingency + "
        "1%% regulation-up; fleet.caiso_operating_reserve_mw) from the gas "
        "top-of-merit headroom before the supply curve clears, lifting the "
        "evening tail. CAISO-only, no-fitted-constants scaffold until OASIS "
        "cleared-AS data can be pulled. Off = no withholding (default).",
    )
    parser.add_argument(
        "--storage-as-commitment",
        action="store_true",
        help="ERCOT: reserve the measured hourly storage up-AS MW from the "
        "battery dispatch power cap (per-resource-type series), so AS-"
        "committed capacity cannot also arbitrage energy. Off (default).",
    )
    parser.add_argument(
        "--ercot-storage-as-deployment",
        action="store_true",
        help="ERCOT: measured-award AS->energy co-participation — force the "
        "measured evening storage-award draw-down as a battery discharge floor "
        "at the net-load ramp (the storage-cycling-lane fix). Requires "
        "--storage-as-commitment. Off (default).",
    )
    parser.add_argument(
        "--ercot-storage-as-endogenous",
        action="store_true",
        help="ERCOT multi-product co-opt (G5): the battery CHOOSES energy vs "
        "upward-AS endogenously (full cap to the co-opt, priced by the per-product "
        "AS demand curves), REPLACING the measured-award reservation "
        "(--storage-as-commitment). Cleared storage AS counts toward the RTOLCAP "
        "supply cap. Off (default); takes precedence over --storage-as-commitment.",
    )
    parser.add_argument(
        "--ercot-storage-as-duration-gate",
        action="store_true",
        help="ERCOT (G5 follow-up): add the published per-product SOC-duration "
        "requirements (RegUp/RRS 1h, ECRS 2h, Non-Spin 4h) to the endogenous "
        "storage split, so a short-duration battery cannot sell long-duration AS "
        "on its full power (LP-linear gate Σ_c dur_c·RS[c,z] ≤ Σ SOC). Requires "
        "--ercot-storage-as-endogenous. Fixes the 2.1–2.4× over-hold vs the "
        "measured DAM award. Off (default).",
    )
    parser.add_argument(
        "--battery-adder",
        type=float,
        default=0.0,
        help="Grid-battery throughput/cycling cost in $/MWh discharged "
        "(ScenarioConfig.battery_dispatch_adder): degradation + "
        "ancillary-service opportunity cost the energy-only LP "
        "otherwise ignores, taming BESS over-cycling. 0 = off "
        "(default; pumped storage keeps its own adder).",
    )
    parser.add_argument(
        "--gas-offer-curve",
        action="store_true",
        help="Give the non-ERCOT per-plant gas fleet a stepped offer curve "
        "(committed/economic/peaking heat-rate bands) via "
        "split_gas_tranches, instead of a single flat block. Off by "
        "default.",
    )
    parser.add_argument(
        "--gas-monthly-actuals",
        action="store_true",
        help="Price gas at the ISO's measured EIA-923 monthly volume-weighted "
        "delivered cost (one hub-level price per month) instead of the "
        "annual Henry Hub + basis x generic seasonality shape, so real "
        "winter gas events reach the merit order. Off by default.",
    )
    parser.add_argument(
        "--gas-electric-power-monthly-level",
        action="store_true",
        help="Price gas at the MEASURED MONTHLY delivered level for this "
        "ISO's own footprint — the EIA N3045 'gas sold to electric power "
        "consumers' state series blended by the ISO's installed gas capacity "
        "per state — instead of one annual scalar times a mean-preserving "
        "shape. REPLACES the level (rule 19): supersedes the annual x shape "
        "construction and --gas-monthly-actuals, and is itself superseded in "
        "covered months by the measured hub index under "
        "--gas-hub-basis-overlay. Inert in any year whose footprint states do "
        "not all print twelve months and carry a majority of the ISO's gas "
        "capacity. Off by default.",
    )
    parser.add_argument(
        "--gas-hub-basis-daily",
        action="store_true",
        help="Diagnostic (off by default): replace the flat monthly hub-basis "
        "overlay with a daily within-month shape, mean-preserving so the "
        "monthly hub level and annual burn are unchanged. NEISO: real measured "
        "Algonquin Citygate daily prints (EIA NG Weekly narrative, "
        "algonquin_citygate_daily.csv), falling back to the measured Transco Z6 "
        "NY daily-basis shape in sparse-print months. NYISO: real measured "
        "Transco Z6 NY daily spot (EIA NG Weekly, transco_z6_ny_daily.csv). "
        "CAISO: real measured California Composite Average citygate daily spot "
        "(EIA NG Weekly, caiso_citygate_daily.csv). No fitted proxy on any ISO "
        "— the cold-day spike a monthly mean smears flat (e.g. Jan-2023 CAISO, "
        "Jan-2025 NYISO) reaches the merit order on its true calendar day. Pair "
        "with --gas-hub-basis-overlay.",
    )
    parser.add_argument(
        "--plant-tranche-config",
        default=None,
        help="Per-plant tranche-config CSV (one row per plant "
        "with its tranche shares + per-band HR mults). "
        "Each listed plant's offer comes from the sheet, "
        "bypassing offer_curve_by_group. Generate/edit "
        "with scripts/export_tranche_config.py.",
    )
    parser.add_argument(
        "--offer-curve-json",
        default=None,
        metavar="JSON",
        help="Per-class/per-band heat-rate multiplier overrides as a JSON "
        "object, deep-merged onto the calibrated offer_curve_by_group "
        "defaults. Each top-level key is a fleet class (CC_REGULAR, "
        "CC_CHP, CT_PEAKER, ST_GAS, ST_CHP, COAL_LIGNITE, COAL_PRB); the "
        "nested object overrides only the named bands (committed, "
        "econ_low, econ_high, peak, econ_low_share, pct_peaking). "
        'E.g. \'{"CT_PEAKER":{"committed":1.40,"econ_low":1.27},'
        '"COAL_PRB":{"committed":0.95}}\'. May also be a path to a '
        ".json file. The merged curve is recorded in run_config.json.",
    )
    parser.add_argument(
        "--cc-derate-from-top",
        action="store_true",
        help="Reallocate CC_REGULAR outage derates top-of-stack: a partial "
        "outage truncates the duct-fire/high-econ end of the plant's "
        "offer curve instead of scaling every tranche (incl. the cheap "
        "committed floor) pro-rata. Plant hourly available MW unchanged.",
    )
    parser.add_argument(
        "--cc-nameplate-summer-derate",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Raise each CC plant's LP capacity to its demonstrated CAMPD "
        "peak and derate to EIA-860 net summer capacity during cooling "
        "months, correcting plants whose nameplate understates actual "
        "capability (the Hinds / Zeeland 131%% CF issue).",
    )
    parser.add_argument(
        "--pjm-offer-surface-conditional",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PJM G-22 lever A: post the MEASURED condition-binned top-of-curve "
        "offer surface (PJM DataMiner2 energy_market_offers, "
        "scripts/data/derive_pjm_offer_surface.py) onto the CC_REGULAR + CT_PEAKER "
        "peak-band rungs in the P1 clearing solve only, keyed by within-year "
        "net-load percentile. Loose hours and P0 run lengths stay "
        "byte-identical (ladder clamped >= the resolved peak height). "
        "PJM-gated; reads the frozen "
        "data/raw/_validation-source/pjm_offer_surface_condbinned.json.",
    )
    parser.add_argument(
        "--caiso-offer-surface-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="C1 lane WP-A (static half): REPLACE the fitted _CAISO_OFFER_CURVE "
        "gas band multipliers (CC_REGULAR/CT_PEAKER econ_low, econ_high, peak) "
        "with the MEASURED cap-weighted medians of CAISO's own DAM energy bids "
        "(OASIS Public Bid Data, scripts/data/derive_caiso_offer_surface.py; "
        "carbon/VOM-netted round-trip). CAISO-gated; reads the frozen "
        "data/raw/_validation-source/caiso_offer_curve_measured.json.",
    )
    parser.add_argument(
        "--caiso-offer-surface-measured-ungrounded",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rule 25 [R-ISO-SCOPE], caiso-231): "
        "extend the static half above to CAISO's THREE UN-GROUNDED gas "
        "classes. _CAISO_OFFER_CURVE records that CC_CHP / CT_CHP / ST_GAS "
        "carry ERCOT-lineage band multipliers preserved verbatim only so the "
        "generic fallback would not change the caiso-51 keeper; this re-grounds "
        "each on the measured bucket derive_caiso_offer_surface.py says it "
        "falls inside (CC_CHP -> the CC bucket; CT_CHP and the three OTC/RMR "
        "ST_GAS steamers -> the CT bucket), arming the same three bands "
        "(econ_low/econ_high/peak) and leaving every committed band unarmed. "
        "Zero free parameters. DISCLOSED: it makes C3a WORSE by a measured "
        "+0.235/+0.344/+0.421 $/MWh (caiso-230 §H) and is NEVER a C3a lever. "
        "Requires --caiso-offer-surface-measured.",
    )
    parser.add_argument(
        "--caiso-st-gas-committed-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rules 14/24/25, caiso-239): ground "
        "the ST_GAS committed band at the scalar that ACTUALLY prices it. "
        "_offer_curve_for_group bypasses offer_curve_by_group for every "
        "ST_GAS_PEAKER_PLANTS member, and that frozenset names CAISO plants "
        "315/335/350, so the whole 2,858.8 MW OTC steam fleet takes the "
        "uncited ERCOT-lineage class default "
        "_DEFAULT_HR_MULT_BY_GROUP['ST_GAS']['mc'] = 1.15 -- an off-registry "
        "channel absent from every run_config.json. Armed, the band takes the "
        "ISO's own measured min-load block-average burn ratio "
        "(constants.ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO; CAISO 1.683 = "
        "avg_committed_p50 over the ten CAMPD units of exactly those three "
        "plants). Exactly one band moves; zero free parameters. DISCLOSED: it "
        "makes C3a WORSE by a bounded +0.0003/+0.0265/+0.0000 $/MWh "
        "(caiso-230 §H form on the caiso-231 keeper) and is NEVER a C3a lever. "
        "An ISO with no registry entry is a hard error.",
    )
    parser.add_argument(
        "--mustrun-chp-btm-holdout",
        dest="mustrun_chp_btm_holdout",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Partition the INJECTED must-run residual classes (biomass, "
        "OTHER) on the published EIA-923 CHP flag, holding host-steam / "
        "behind-the-meter cogeneration out of grid supply "
        "(ScenarioConfig.mustrun_chp_btm_holdout, miso-253). The injection "
        "takes each class's EIA-923 NET GENERATION as price-insensitive "
        "must-run grid supply with NO host-steam carve-out -- unlike every "
        "fossil cogen class, which classify_plant splits into its own *_CHP "
        "class and then holds a measured host share out of. Biomass and OTHER "
        "have no CHP counterpart class, and they are the two classes where "
        "cogeneration DOMINATES: MISO 2023 is 71.4%% chp=Y across the pair "
        "(12.514 of 18.453 TWh) -- black-liquor and wood-solids recovery "
        "boilers at paper mills, blast-furnace and coke-oven gas at steel "
        "mills, waste heat, purchased steam -- electricity that powers the "
        "host and never reaches the ISO grid. Rule 14 [R-ACCURATE]; zero free "
        "parameters (a partition on one published boolean, rules 21/24); "
        "forward-native (rule 13 -- EIA-923 carries the flag per plant per "
        "vintage). Applied at the single _eia923_frame seam BOTH the injection "
        "and the benchmark read, so the two move in lockstep and no artificial "
        "miss is created -- which also means biomass/OTHER stay SELF-SCORED; "
        "this flag does not close that validation gap. ISO-generic; default "
        "off, byte-identical off -- every keeper replays unchanged.",
    )
    parser.add_argument(
        "--benchmark-membership-vintage-union",
        dest="benchmark_membership_vintage_union",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Union the solve year's OWN EIA-860 BA cohort into the "
        "benchmark's ISO plant membership "
        "(ScenarioConfig.benchmark_membership_vintage_union, spp-49). The "
        "benchmark's membership is zone_assignment.build_zone_lookup, whose "
        "EIA-860 supplement reads a module-level path bound at import to the "
        "CANONICAL (2025 Early Release) directory -- so it never follows the "
        "solved year, and a plant that retired mid-window is absent from the "
        "ACTUAL in the very years it demonstrably ran. Measured: SPP's "
        "benchmark plant set is 830 under EVERY vintage, with Oklaunion "
        "(plant 127, retired 9/2020) absent from all of them, although "
        "vintage_2019/2020's own plant file carries it BA-coded SWPP. The "
        "LP FLEET has a fallback-zone path for such a plant; the benchmark "
        "has a hard isin with none -- so a mid-window retiree is IN the model "
        "and OUT of the actual at once. ADDITIVE by construction: the union "
        "never removes a plant, so it can only ADD real metered generation, "
        "and each plant contributes exactly what EIA-923 reports for that "
        "year. The REPLACE variant was built and REFUSED on measurement "
        "(it deletes real generation in 7 of 9 regions -- SOCO 2024 -7,275.9 "
        "GWh, PJM 2020 -9,077.7, SPP -828.8..-893.1 every year 2019-2023 -- "
        "rules 13/14). No double count: the CAMPD backfill skips any plant "
        "EIA-923 already reports at/above 50,000 MWh. Applied at the single "
        "_iso_plant_ids seam BOTH the injection and the benchmark read, so "
        "the two move in lockstep (rule 19). Zero free parameters (rules "
        "21/24). SHARED AND CROSS-ISO, so default OFF and armed per ISO by an "
        "explicit recipe (rule 25) -- byte-identical off; every keeper "
        "replays unchanged.",
    )
    parser.add_argument(
        "--caiso-dsw-lateevening-clean",
        dest="caiso_dsw_lateevening_clean",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="REPLAY-ONLY override (--replay-bundle), the caiso-252 channel: "
        "WINDOW-GAP CLOSURE (caiso-269, rules 14/17/19; "
        "ScenarioConfig.caiso_dsw_lateevening_clean). The three DSW "
        "clean-depth constructions do not tile the clock: caiso-93 runs hod "
        "0-5, caiso-94 runs hod 6-21, and caiso-87's surplus trigger is "
        "coverage-STARVED at hod 22-23 (ON in 0.3/0.8 %% of 2024 and 1.6/1.9 "
        "%% of 2025 hod 22/23 - caiso-253's G-WINDOW leg). On the live keeper "
        "the armed clean capability falls 3,420 MW at hod 21 to 33 MW at hod "
        "22 (2025) while the measured WECC_DSW corridor net import RISES "
        "across the boundary, against a measured EIA-930 import deficit of "
        "1.0-1.8 GW there. Arms ONE tranche at the measured hod 22-23 p95 "
        "corridor depth (CV 0.037 / LOYO 6.8 %%), net of the shaped firm "
        "block and all three sibling clean tranches (rule 19 [R-ONE-MECH]), "
        "ONLY in (month x hod) buckets clearing caiso-253's PRE-REGISTERED "
        "raw-hub band (-2, +4) on the measured DA CAISO-PaloVerde spread - "
        "that session's own refusal criterion, re-used unchanged, so 2023 "
        "stays dark by construction. Zero new free parameters. Default OFF "
        "Absent (default None) keeps the bundle's own value, so the replay path "
        "is byte-identical.",
    )
    parser.add_argument(
        "--caiso-st-gas-peak-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rules 14/24/25, caiso-240): the "
        "BAND-DISJOINT sibling of --caiso-st-gas-committed-measured (rule 19 "
        "[R-ONE-MECH]). The caiso-240 census measured all 28 "
        "_DEFAULT_HR_MULT_BY_GROUP literals on all six designated keepers and "
        "found that after caiso-239 exactly TWO cells stay live on the CAISO "
        "keeper -- ST_GAS['econ'] = 1.00 and ST_GAS['peak'] = 1.10 -- both on "
        "the same three bypassed OTC steamers (315/335/350). This arms the "
        "peak one, the only one whose measured counterpart is at the model's "
        "own grain. Armed, the band takes the ISO's own measured peak-band "
        "offer multiplier (constants.ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO; "
        "CAISO 1.166 = CT_PEAKER.bands.peak in caiso_offer_curve_measured.json "
        "-- ALREADY the value the CAISO ST_GAS class band carries, armed at "
        "caiso-231, which the bypass keeps from reaching the very plants the "
        "CT bucket contains). Exactly one band moves; zero new measurement and "
        "zero free parameters. DISCLOSED: 1.10 -> 1.166 RAISES the peak band "
        "(+6.0 %%), so it makes C3a WORSE, and it is NEVER a C3a lever. An ISO "
        "with no registry entry is a hard error.",
    )
    parser.add_argument(
        "--caiso-ct-peaker-committed-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rules 14/19/21/25, caiso-241): "
        "ground CAISO CT_PEAKER's fitted `committed` band (1.35) on the "
        "measured physical counterpart its OWN band dict already carries, "
        "phys_committed = 0.991 (avg_committed_p50, "
        "caiso_campd_marginal_hr_summary.csv, n=75). Zero new numbers, zero "
        "free parameters; exactly one band moves. This is the PHYSICAL route, "
        "NOT the Lever-A-refused measured BID (1.166), which stays unarmed. "
        "Rule 19: the _committed tranche is the only tranche carrying the "
        "bin's start cost and P1 already amortizes it ($20/MW NREL "
        "SR-5500-55433 / P0 run length), so the 1.35 'start hurdle' is a "
        "SECOND unidentified start-cost mechanism on the same tranche. Rule "
        "25: 1.35 appears in the CAISO/NYISO/NEISO curves each citing the "
        "others and none citing a measurement. It also un-inverts the class "
        "(the keeper reads committed 1.350 > peak 1.166 -- the min-load block "
        "is the class's most expensive MW). DISCLOSED: the direction is "
        "FAVOURABLE to C3a, which is the session's hazard, not its argument; "
        "this is NEVER a C3a lever. Non-CAISO, or a band with no "
        "phys_committed, is a hard error.",
    )
    parser.add_argument(
        "--nyiso-st-gas-econ-bands-deleaked",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="RULE-25 [R-ISO-SCOPE] DE-LEAK (nyiso-232): NYISO ST_GAS's "
        "`econ_low` (1.08) / `econ_high` (1.13) were DERIVED as the measured "
        "steam marginal (~0.830) x `_NYISO_OFFER_CURVE`'s own cited 'CC class "
        "reach ratio (CC econ_high 1.21 / native CC marginal 0.925 = 1.31x)' -- "
        "and 1.08 reproduces that construction to 0.08-0.53%% on the file's own "
        "recorded native-steam triples (every reading within 1%%). But "
        "CC_REGULAR.econ_high "
        "1.21 is the ERCOT keeper value the same file records as REMOVED under "
        "rule 25, so ST_GAS carries it MULTIPLICATIVELY: the de-leak removed the "
        "value where it was written and left it where it had been multiplied in "
        "(rule 26). This sets both econ bands to the rule-24/25 NEUTRAL 1.0 -- "
        "the identical remedy applied to CC_REGULAR.econ_high and CT_PEAKER's "
        "econ bands in the SAME audit. Zero new literals, zero free parameters, "
        "no DOF entry. `committed` and `peak` are EXCLUDED (peak 4.20 is the "
        "$-cap scarcity wall; committed 1.05 already sits below phys_committed "
        "1.104 so its markup clips to 0 in both legs, and moving it would price "
        "steam min-load 9.4%% below its own measured burn). It does NOT identify "
        "the markup -- that stays an OPEN ROOT CAUSE against NYISO "
        "scarcity/reserve (RCPF/AS) price formation, issue #1344. Measured "
        "pre-solve: econ offer -$8.61/-$3.17/-$2.80/-$5.41 per MWh in "
        "2022/23/24/25, non-ST_GAS offer max|d| EXACTLY $0.00. NYISO-only; "
        "arming it elsewhere is a hard error. MUST NEVER be proposed as a C1 "
        "or C3a lever.",
    )
    parser.add_argument(
        "--nyiso-ct-peaker-bands-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rules 14/19/21/25, nyiso-199, owner "
        "ruling 2026-09-06): ground NYISO CT_PEAKER's `committed` (1.35) and "
        "`econ_low`/`econ_high` (1.0/1.0, a DE-LEAK placeholder) on the "
        "measured physical counterparts its OWN band dict already carries -- "
        "phys_committed 0.843 / phys_econ_low 0.661 / phys_econ_high 0.658 "
        "(nyiso_campd_marginal_hr_summary.csv p50s, n=70). Zero new numbers, "
        "zero free parameters, no DOF entry. `peak` is NOT grounded: NYISO's "
        "4.0 is the $1,000-offer-cap scarcity wall, not a physics claim. Rule "
        "19: tranche_startup_amortization is ARMED on the NYISO keeper, so P1 "
        "already amortizes $20/MW (NREL SR-5500-55433) over the measured P0 "
        "run length onto the very _committed tranche the 1.35 'start hurdle' "
        "charges a second time. Rule 1: the econ limb closes the OPEN ROOT "
        "CAUSE _NYISO_OFFER_CURVE's own comment declares by name. DISCLOSED: "
        "the direction is FAVOURABLE to CT_PEAKER volume and moves C3a DOWN "
        "(crossing indicator -2.75/-2.40/-2.74 %%), which is the hazard, not "
        "the argument; this is NEVER a C3a lever. Non-NYISO, or a band missing "
        "any of the three phys_* keys, is a hard error.",
    )
    parser.add_argument(
        "--nyiso-ct-peaker-committed-measured",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="STRUCTURAL-INTEGRITY REPAIR (rules 14/19/21/25, nyiso-241): the "
        "COMMITTED-ONLY limb of the repair above -- the mechanism-matrix cell "
        "`ct_peaker_committed_measured` (U), which the caiso-241 cross-ISO "
        "census recorded as 'an ASK FOR THE NYISO LANE, never an arm from "
        "here'. Grounds NYISO CT_PEAKER's `committed` 1.35 on the class's OWN "
        "registered phys_committed 0.843 (avg_committed_p50, "
        "nyiso_campd_marginal_hr_summary.csv, n=70) and touches nothing else: "
        "`econ_low`/`econ_high` stay at the registered neutral 1.0 and `peak` "
        "at the $1,000-offer-cap wall 4.0. Zero new numbers, zero free "
        "parameters, no DOF entry. THE DEFECT is a citation ring, not a "
        "residual: 1.35 reads 'NYISO/CAISO-grounded' here, 'NYISO-grounded' in "
        "CAISO and 'NYISO/CAISO-grounded' in NEISO, and no ISO cites a "
        "measurement; 1.35/0.843 = 1.60 is the largest such ratio in the "
        "model. SECOND GROUND (rule 19): tranche_startup_amortization is ARMED "
        "on the NYISO keeper, so the _committed rows already pay a real start "
        "recovery of $11.97/$16.48/$15.78/$13.22 per MWh in 2022/23/24/25 and "
        "the 1.35 'start hurdle' charges the same phenomenon twice. SIZED "
        "BEFORE PROPOSED and reported against itself: 346.7 MW of the class's "
        "3,034.0 MW (11.4%%), 22 LP rows move with max|d| EXACTLY $0.00 "
        "elsewhere, and a GENEROUS upper bound against the keeper's own prices "
        "reaches only 16-41%% of metered CT_PEAKER energy in 2023-2025 -- a "
        "grounding repair, NOT the fix for the CT_PEAKER merit collapse. "
        "MUTUALLY EXCLUSIVE with --nyiso-ct-peaker-bands-measured (rule 19); "
        "arming both is a hard error, as is arming it on any other ISO or on a "
        "band carrying no phys_committed. MUST NEVER be proposed as a C1 or "
        "C3a lever.",
    )
    parser.add_argument(
        "--nearby-fuel-price-zone-donor-guard",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="DATA-INTEGRITY GUARD (caiso-243, repair form (a) of "
        "FINDING-caiso242 §5): the F923 nearby-plant fallback's ZONE tier "
        "requires the SAME distinct-reporter floor the state tier already "
        "carries (nearby_fuel_price_min_state_plants), so a zone-month whose "
        "donor pool is ONE reporting plant is not trusted (a pool of one "
        "returned that plant's price verbatim — plant 55077's 96.161 $/MMBtu "
        "on 2.6 %% of its normal volume priced 2,446 MW of CAISO neighbours at "
        "~$736/MWh for all of Nov-2025). No new constant. ISO-generic guard; "
        "the ARM is per lane (rule 25). Off by default, byte-identical.",
    )
    parser.add_argument(
        "--fleet-state-from-eia860",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="DATA-COMPLETENESS REPAIR (caiso-243, repair form (c), the ROOT "
        "CAUSE of defect D1): stamp each CAMPD-bin / plant-level generator's "
        "USPS state from the EIA-860 plant table so the F923 fallback's "
        "documented state-first donor tier — the only tier with a "
        "donor-count guard — is reachable. bins_to_fleet never set state, so "
        "every plant-level fleet (CAISO/PJM/MISO/NYISO/NEISO) skipped that "
        "tier fleet-wide. No new constant; rule 14 [R-ACCURATE]. Off by "
        "default, byte-identical; armed per lane (rule 25).",
    )
    parser.add_argument(
        "--caiso-citygate-spot-coverage",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="COVERAGE-GATE REPAIR (caiso-246): under --caiso-citygate-spot-level "
        "the hub overlay prices every covered month from the MEASURED CA "
        "Composite daily citygate spot, but a month counts as covered only "
        "where the EIA N3050CA3 monthly SURVEY has a basis row — and EIA "
        "publishes that survey as NA for 2025-09/10/11, so those months fell "
        "to the F923 plant layer while the daily spot carried 21/22/12 prints. "
        "When set, a month with daily prints of its own is covered even "
        "without a survey row (its day series is built exactly as every other "
        "spot-level month; months with neither stay uncovered). No new "
        "constant; rule 14 [R-ACCURATE]. Off by default, byte-identical; "
        "CAISO-only (rule 25). Pre-registered: "
        "PRECOMMIT-caiso246-spot-coverage-2026-09-04.md.",
    )
    parser.add_argument(
        "--caiso-offer-surface-conditional",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="C1 lane WP-A (conditional half): post the MEASURED condition-binned "
        "top-of-curve bid surface onto the CAISO CC_REGULAR + CT_PEAKER "
        "peak-band rungs in the P1 clearing solve only, keyed by within-year "
        "net-load percentile (the PJM/NEISO mechanism ported; loose hours "
        "byte-identical). CAISO-gated; reads the frozen "
        "data/raw/_validation-source/caiso_offer_surface_condbinned.json.",
    )
    parser.add_argument(
        "--pjm-da-virtual-bids",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PJM G-22 lever B: carry the Day-Ahead market's virtual bid "
        "layer as measured SUBMITTED INC/DEC bid curves (PJM DataMiner2 "
        "hrl_da_incs_decs, scripts/data/derive_pjm_da_virtual_surface.py) posted "
        "into the LP as pseudo-units with ENDOGENOUS clearing — the DA "
        "procurement depth at peaks (net cleared DEC-INC ~ +7-11 GW at the "
        "2024 top hours) becomes real market structure instead of the dual "
        "being read ~9-10 GW too shallow into the stack. PJM-gated; reads "
        "the frozen "
        "data/raw/_validation-source/pjm_da_virtual_surface_condbinned.json.",
    )
    parser.add_argument(
        "--pjm-offer-midcurve-conditional",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="PJM G-22 lever A': floor the COAL/CT_PEAKER/ST_GAS/CC econ-"
        "tranche P1 bids at the MEASURED mid-curve offer level of their "
        "physics segment at each row's own within-plant capacity share "
        "(PJM DataMiner2 energy_market_offers full-curve sampling, "
        "scripts/data/derive_pjm_offer_midcurve.py), keyed by within-year "
        "net-load percentile. P1-only (P0 run lengths unperturbed); the "
        "floor only raises bids. PJM-gated; reads the frozen "
        "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json.",
    )
    parser.add_argument(
        "--temp-dependent-derate",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Replace the flat EIA-860 net-summer derate with a per-class "
        "TEMPERATURE-dependent capacity derate driven by measured hourly zone "
        "dry-bulb temperature (CC/CT air-density mass-flow loss; coal/gas-steam "
        "condenser loss). CC/CT reproduce their net-summer summer-mean "
        "(capacity-neutral reshape so heatwave hours sit below net-summer); "
        "coal/gas-steam gain an additive hot-hour derate. Physical slopes live "
        "in ScenarioConfig.temp_derate_slope_*; forward-reproducible (rule 11).",
    )
    parser.add_argument(
        "--temp-derate-hourly-grain",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Feed the temperature derate an HOUR-GRAIN dry-bulb series "
        "(daily TMIN/TMAX reconstructed by the standard climatological cosine "
        "bridge) instead of the day-flat TMAX, so the curve carries an "
        "hour-of-day capability wave. Input-grain refinement of the existing "
        "mechanism, not a new floor (rule 19). Requires "
        "--temp-dependent-derate.",
    )
    parser.add_argument(
        "--temp-derate-mean-anchored",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Evaluate the derate curve about the zone's own ANNUAL-MEAN "
        "dry-bulb with NO onset hinge (annual mean exactly 1.0), composing as a "
        "pure SHAPE overlay on top of the existing level treatment instead of "
        "replacing it. Claims only the within-day/seasonal shape the "
        "within-day estimator identifies, never the class level. Requires "
        "--temp-dependent-derate.",
    )
    parser.add_argument(
        "--temp-derate-classes",
        default=None,
        help="Comma-separated plant groups to scope the temperature derate to "
        "(e.g. 'ST_CHP,CT_CHP'). Default: every class the mechanism knows. An "
        "ISO arms only the classes it has identified on its own fleet "
        "(rule 25 [R-ISO-SCOPE]; pjm-95 refuted the literature slopes on PJM).",
    )
    parser.add_argument(
        "--temp-derate-slope-st-chp",
        type=float,
        default=None,
        help="ST_CHP fractional capability loss per deg C. Defaults to the "
        "ST_GAS slope. MISO measured value 0.00141 "
        "(scripts/data/derive_campd_temp_derate_params.py --iso MISO).",
    )
    parser.add_argument(
        "--temp-derate-slope-ct-chp",
        type=float,
        default=None,
        help="CT_CHP fractional capability loss per deg C. Defaults to the "
        "CT_PEAKER slope. MISO measured value 0.00141 (same derivation — the "
        "CEMS meter spans both cogen tranches, so they identify jointly).",
    )
    parser.add_argument(
        "--cc-capacity-reconcile",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Reconcile listed CC plants' LP capacity to their demonstrated "
        "CAMPD value from the per-ISO table "
        "data/raw/_processed-legacy/cc_capacity_reconcile_<ISO>.csv "
        "(scripts/data/derive_cc_capacity_reconcile.py; mode=cap rows bound a "
        "plant AT its measured sustained peak, raise rows lift it). Fixes "
        "the EIA-860 CA-row block-level summer-capacity double-count "
        "(e.g. MISO Union Power 3,457 MW modeled vs 2,428 nameplate / "
        "2,318 CAMPD p99.9). Same ScenarioConfig.cc_capacity_reconcile "
        "seam the PJM keeper uses (fleet._reconcile_cc_capacity).",
    )
    parser.add_argument(
        "--cc-duct-peaking",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Size each CC plant's peaking (duct-burner) tranche from its "
        "EIA-860 nameplate-vs-net-summer capability gap (duct-fired "
        "plants only; non-duct CCs get no peak band) — a per-plant, "
        "manufacturer-spec share replacing the class-wide pct_peaking AND "
        "the 4-plant hardcoded ERCOT override (sets cc_duct_peaking on, "
        "cc_peaking_per_plant off). fleet.cc_duct_peaking_pct.",
    )
    parser.add_argument(
        "--cc-duct-peaking-row-scoped",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Take the --cc-duct-peaking capability gap over the EIA-860 "
        "generator rows the filing FLAGS as duct-fired, instead of over "
        "every combined-cycle row of the plant. The column reads Y/N only "
        "on CA/CS (steam) rows and X on every CT row, so the plant-level "
        "sum books the CT rows' ambient derate as duct capability. Zero "
        "free parameters — the numerator's row set changes, nothing else. "
        "ScenarioConfig.cc_duct_peaking_row_scoped (nyiso-198).",
    )
    parser.add_argument(
        "--curve-n",
        type=int,
        default=None,
        help="Override offer_curve_smoothing_n (default 6): the number of "
        "equal-capacity slices the econ ramp is rendered into. Sweep "
        "knob for testing finer offer-curve granularity (e.g. 12).",
    )
    parser.add_argument(
        "--curve-mid",
        type=float,
        default=None,
        help="Override offer_curve_smoothing_mid: fraction of the econ "
        "ramp's lo->pk rise reached at its capacity midpoint "
        "(piecewise-linear shape anchor; <0.5 = cheap middle, steep "
        "top). Unset keeps the t**exp power shape.",
    )
    parser.add_argument(
        "--curve-exp",
        type=float,
        default=None,
        help="Override offer_curve_smoothing_exp (default 1.0 = linear "
        "ramp): exponent of the econ-ramp heat-rate rise. >1 convex "
        "(cheap-bottomed), <1 concave (cheap mid/top).",
    )
    parser.add_argument(
        "--priced-interchange",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Serve interchange through the priced import/export node "
        "(import tranches + export sinks in the ISO's external zone, "
        "the forward-scenario mechanism) instead of the measured "
        "schedule added to demand. Used to validate the node's tranche "
        "calibration against the EIA-930 net-interchange duration "
        "curve. Default per ISO: on for "
        f"{', '.join(sorted(PRICED_INTERCHANGE_DEFAULT_ISOS))} "
        "(no measured-schedule mode), off elsewhere; pass "
        "--no-priced-interchange to force the measured schedule.",
    )
    parser.add_argument(
        "--hydro-backfill-year",
        type=int,
        default=None,
        help="Carry conventional-hydro plants that reported in this prior "
        "year but not in the backcast year at their prior-year monthly "
        "net generation (load_hydro_budget early-release path). The most "
        "recent EIA-923 vintage is a monthly-survey-only release that "
        "under-counts hydro until the final annual file lands (NEISO "
        "2025: 5 of ~166 plants, 0.09 of ~6 TWh), and the missing inflow "
        "is otherwise served by gas, inflating the modeled gas level. "
        "Unset (default) loads the backcast year exactly as reported and "
        "changes no existing run.",
    )
    parser.add_argument(
        "--hydro-eia930-monthly",
        action="store_true",
        help="Repin the conventional-hydro monthly energy budget to the "
        "measured EIA-930 NG: WAT monthly total for the ISO/year "
        "(per-plant within-month shares preserved). Corrects both the "
        "level and the monthly shape when the backfilled early-release "
        "923 vintage misstates an off-inflow year (NEISO 2025: the 2024 "
        "backfill yields 6.65 TWh, flat, vs measured 5.12 TWh). No-op "
        "when EIA-930 hydro for the ISO/year is unavailable. Off "
        "(default) changes no existing run. Pairs with "
        "--hydro-backfill-year, which supplies the per-plant coverage.",
    )
    parser.add_argument(
        "--hydro-cascade-coupling",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Arm ScenarioConfig.hydro_cascade_coupling (NWPP-36, owner ruling "
        "N3): couple the plants of a MEASURED hydraulic chain with one hourly "
        "water-balance equality per coupled downstream plant (spill S >= 0, "
        "pond 0 <= V <= B_d; model/lp/hydro_cascade.py), on top of -- never in "
        "place of -- the EIA-923 monthly energy budget, which stays the sole "
        "quantity mechanism (rule 19 [R-ONE-MECH]). Reads the per-ISO artifact "
        "data/raw/<iso>-hydro/<iso>_hydro_cascade_{links,monthly}.csv through "
        "pipeline/kwargs.py::resolve_hydro_cascade; an ISO-year with no "
        "artifact, or no coupled plant on its LP hydro fleet, is armed-but-"
        "INERT and its LP is byte-identical. Tri-state: unset (default) keeps "
        "the recipe / per-ISO value, --no- forces it off. Rides the generic "
        "prb_overrides ScenarioConfig channel so run_config.json and meta.json "
        "record it (rule 24 [R-REGISTRY]); the field is on "
        "_CACHE_KEY_OPTIONAL_FIELDS, so an unset flag moves no cache key. "
        "Added by lane NWPP-40 (2026-09-16): NWPP-36 built the field with no "
        "CLI surface, and the first NWPP keeper arms it (plan §8 W4).",
    )
    # --- The three pre-existing hydro gates, given a CLI surface (hydro-1) ---
    # RULE 24 [R-REGISTRY] GAP CLOSED. hydro_dispatch_envelope (caiso-72),
    # hydro_min_flow_floor (caiso-124) and hydro_ror_split (caiso-126) are
    # solve-affecting ScenarioConfig gates that keepers carry ARMED (the NYISO
    # keeper 2026-09-20-nyiso247-fuel-invariance-disarm records
    # hydro_dispatch_envelope=True and hydro_min_flow_floor=True in its
    # run_config.json scenario_config) and that this CLI had NO flag for, so a
    # lane could not state the posture it was solving and a kwargs replay from
    # meta.json could not carry it. These three tri-state flags ride the same
    # generic prb_overrides channel as --hydro-cascade-coupling, so the value
    # reaches BOTH run_year's config and recorded_cfg and is therefore
    # replayable from run_config.json / meta.json. All default None (unset =
    # keep the recipe / per-ISO value), so no existing run moves.
    parser.add_argument(
        "--hydro-dispatch-envelope",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Arm ScenarioConfig.hydro_dispatch_envelope (caiso-72 STEP-2): "
        "cap the conventional-hydro fleet's hourly dispatch at the measured "
        "per-(month x hour-of-day) percentile of the ISO's EIA-930 NG:WAT — "
        "the head/flow/scheduling deliverability ceiling nameplate pmax "
        "ignores. REFUSE for a BA in constants.EIA930_PS_FOLDED_INTO_WAT "
        "(MISO, PJM), whose NG:WAT folds pumped-storage discharge and so "
        "measures a different population than the LP's conventional-only "
        "hydro units (rule 14 [R-ACCURATE]); the level pin already refuses "
        "there and this reader does not, which is a known gap. Tri-state.",
    )
    parser.add_argument(
        "--hydro-min-flow-floor",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Arm ScenarioConfig.hydro_min_flow_floor (caiso-124): hold each "
        "conventional-hydro plant at a MONTH-CONSTANT minimum-generation "
        "floor, its pro-rata share of the fleet's measured monthly Q95 "
        "sustained level. The LOWER half of the two-sided measured capability "
        "envelope. Same EIA-930 NG:WAT PS-fold caveat as "
        "--hydro-dispatch-envelope. Tri-state.",
    )
    parser.add_argument(
        "--hydro-ror-split",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Arm ScenarioConfig.hydro_ror_split (caiso-126): plants the "
        "EXTERNAL ORNL-EHA hydro-plant-modes classifier marks run-of-river / "
        "canal-conduit dispatch FLAT at their own measured monthly water "
        "(min_gen == availability cap == budget[g,m]/hours[m]); reservoir-"
        "class plants keep the full shaping machinery. This is the FLOOR half "
        "of the hydro family — it is what stops the budget LP parking a "
        "run-of-river plant at 0 MW, which it has no reservoir to do. "
        "Complementary to --hydro-pondage-bound, which bounds concentration "
        "and imposes no floor; a RoR-flat plant carries no pondage row. "
        "Requires the per-ISO clean partition (scripts/data/"
        "curate_hydro_plant_modes.py); an ISO with none is armed-but-INERT "
        "with a byte-identical LP and a warning. Tri-state.",
    )
    parser.add_argument(
        "--hydro-pondage-bound",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Arm ScenarioConfig.hydro_pondage_bound (hydro-1, 2026-09-20): "
        "bound each conventional-hydro plant's WITHIN-MONTH energy "
        "reallocation by its own MEASURED usable forebay storage — one hourly "
        "water-balance row per plant in MWh, P + Spill + V(t) - V(t-1) = "
        "inflow(t) with 0 <= V <= B, assembled by the SAME link-free "
        "model/lp/hydro_cascade.py builder the cascade uses. B is "
        "data/raw/<iso>-hydro/<iso>_hydro_pondage.csv (USACE NID volume x NID "
        "head at efficiency 1.0, an upper bound); inflow is the plant's own "
        "monthly budget over the month's hours, so no new energy datum "
        "enters. It bounds CONCENTRATION and imposes NO floor (spill is "
        "unbounded, so every row is feasible at P=0) — the trough is "
        "--hydro-ror-split / --hydro-min-flow-floor's half. MUTUALLY "
        "EXCLUSIVE with --hydro-cascade-coupling (same row family; the "
        "resolver raises on both). An ISO with no artifact, or whose every "
        "plant holds a whole month, is armed-but-INERT with a byte-identical "
        "LP. Tri-state: unset (default) keeps the recipe / per-ISO value, "
        "--no- forces it off. Rides the generic prb_overrides ScenarioConfig "
        "channel so run_config.json and meta.json record it (rule 24 "
        "[R-REGISTRY]); the field is on _CACHE_KEY_OPTIONAL_FIELDS, so an "
        "unset flag moves no cache key.",
    )
    parser.add_argument(
        "--hydro-budget-period-by-instrument",
        action="store_true",
        help="Shorten the conventional-hydro energy-budget period, PER PLANT, "
        "to the period that project's own governing instrument -- or, where "
        "the instrument states none, its measured pondage -- permits energy to "
        "be reallocated over (registry "
        "constants.HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT, which carries every "
        "entry's citation). A plant absent from that registry keeps the "
        "calendar month, so this is a strict opt-in refinement and a "
        "byte-identical no-op for every ISO with no entry. NYISO: Robert Moses "
        "St. Lawrence 168 h (stated in words by the IJC peaking-and-ponding "
        "directive) and Robert Moses Niagara 24 h (derived -- its instruments "
        "state no conservation period and its measured pondage is 0.244 h, "
        "i.e. use it or lose it). Reconciled with --hydro-dispatch-envelope "
        "on disjoint windows (rule 19), never stacked. Off (default) changes "
        "no existing run. See nyiso-220.",
    )
    parser.add_argument(
        "--hydro-forecast-budget",
        action="store_true",
        help="Forward analogue of --hydro-eia930-monthly: set the "
        "conventional-hydro monthly budget LEVEL to the normal-water-year "
        "climatology (the multi-year mean of measured EIA-930 NG: WAT) "
        "scaled by --hydro-year, instead of a single measured year. The "
        "per-plant within-month shares still come from the run year's "
        "EIA-923, so only the level is forecast (the within-month dispatch "
        "mechanism is unchanged). Mutually exclusive with "
        "--hydro-eia930-monthly. No-op when no climatology exists for the "
        "ISO. Off (default) changes no existing run.",
    )
    parser.add_argument(
        "--hydro-year",
        choices=("dry", "normal", "wet"),
        default="normal",
        help="Forecast wet/dry water-year lever on the hydro monthly budget "
        "level (constants.HYDRO_YEAR_MULTIPLIER: dry 0.85, normal 1.0, wet "
        "1.15). Only bites with --hydro-forecast-budget. Default 'normal'.",
    )
    parser.add_argument(
        "--interchange-shaping",
        action="store_true",
        help="Shape the priced import/export node by the measured EIA-930 "
        "month x hour-of-day net-interchange envelope, so it imports "
        "overnight and EXPORTS the midday solar glut instead of clearing "
        "a flat all-hours import. Targets CAISO's over-priced midday "
        "floor. Requires --priced-interchange; no-op without a measured "
        "envelope. Off (default) changes no existing run.",
    )
    parser.add_argument(
        "--interchange-shaping-export-only",
        action="store_true",
        help="Like --interchange-shaping but shapes ONLY the export side, "
        "leaving every import tranche available in every hour. The full "
        "both-sided shape caps gross import availability to the net-import "
        "envelope (net << gross), starving baseload imports and "
        "substituting gas (inflating gas TWh and the mean LMP); export-only "
        "keeps just the midday-export cap (surplus beyond the measured "
        "export curtails and prices negative) without that regression. "
        "Implies --interchange-shaping. Requires --priced-interchange; off "
        "(default) changes no existing run.",
    )
    parser.add_argument(
        "--reference-price-interface",
        action="store_true",
        help="Serve the priced-interchange seam through the forecast-grade "
        "reference-price interface (per-neighbor gas x heat-rate x "
        "load-shape, cleared on the spread vs the ISO LMP with a hurdle) "
        "instead of the fitted IMPORT_TRANCHES/EXPORT_TRANCHES. Implies "
        "--priced-interchange; gated to ISOs in INTERFACE_NEIGHBORS (PJM). "
        "See docs/reference-price-interface.md.",
    )
    parser.add_argument(
        "--negative-renewable-offers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Floor the curtailable wind/solar dispatch offer at the negative "
        "keep-running (REC/PTC) value (ScenarioConfig."
        "renewable_keep_running_value, default $20/MWh) so curtailed "
        "renewables set a sub-$0 marginal price in oversupply, "
        "reproducing CAISO's negative midday LMPs. Pushes the floor below "
        "the existing $0 export/curtailment sink; only bites once the "
        "model is long midday (the RA must-offer commitment workstream). "
        "Default (unset) keeps the per-ISO base config value — ON for "
        "CAISO (the keeper), off elsewhere; --no-negative-renewable-offers "
        "forces it off (e.g. a baseline probe).",
    )
    parser.add_argument(
        "--wind-ptc-vintage-offers",
        action="store_true",
        help="ERCOT-65 PTC vintage scoping: replace the flat -ira_ptc_wind "
        "wind dispatch offer with the per-zone-month measured EIA-860 "
        "vintage blend -PTC_statutory(year) x eligible_share[z, month] "
        "(only vintages inside their 10-year federal section-45 window "
        "carry the credit; expired vintages bid ~$0). ISO-agnostic "
        "mechanism, probed on ERCOT; default off (byte-identical). Full "
        "adjudication at the ScenarioConfig.wind_ptc_vintage_offers "
        "field docstring.",
    )
    parser.add_argument(
        "--caiso-gas-commitment-floor",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO Resource-Adequacy must-offer floor: hold the gas fleet "
        "(gas_cc/gas_ct/gas_st) online over the midday solar-glut window "
        "at the measured EIA-930 NG: NG profile (scaled by "
        "--caiso-gas-floor-frac), via FleetArrays.min_gen. RA gas can't "
        "economically cycle off for the evening ramp, so it over-generates "
        "midday and CAISO exports/curtails the surplus at ~$0; the floor "
        "makes the model LONG midday so its surplus prices at ~$0 "
        "(collapsing the over-priced spring-midday LMP floor). CAISO-only; "
        "pair with --interchange-shaping (export side). Default (unset) "
        "keeps the per-ISO base config value — ON for CAISO (the keeper "
        "at frac 0.80), off elsewhere; --no-caiso-gas-commitment-floor "
        "forces it off (the no-floor baseline probe).",
    )
    parser.add_argument(
        "--caiso-ra-mustoffer",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO Resource-Adequacy must-offer COMMITMENT — applied P1-NATIVE "
        "(NOT a P2 pass; P2 is archived). Before the single P1 clearing solve, "
        "hold each merchant gas CC/CT unit that the base-cost P0 dispatch runs "
        "before AND after a midday idle gap shorter than its physical min-down "
        "time at --caiso-ra-min-load-frac x available capacity across the gap (it "
        "cannot economically cycle off and restart for the evening ramp). The "
        "unit is online at min-load and free to dispatch DOWN to it — not "
        "pinned to measured output. Detected from the model's own P0 run pattern "
        "+ min-down (forward-derivable, no measured-outcome pin), so the RA "
        "structure rides the scored P1 pass. CAISO-only. Default (unset) keeps "
        "the per-ISO base config value — ON for CAISO, off elsewhere; "
        "--no-caiso-ra-mustoffer forces it off (the floor-off baseline probe).",
    )
    parser.add_argument(
        "--caiso-ra-min-load-frac",
        type=float,
        default=None,
        help="Minimum stable load of a committed gas unit as a fraction of "
        "available capacity, for --caiso-ra-mustoffer (default 0.40 — typical "
        "CC/CT minimum generation). A physical turn-down limit, not a fit.",
    )
    parser.add_argument(
        "--caiso-ra-startup-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Startup-cost-aware extension of --caiso-ra-mustoffer (caiso-44): "
        "also hold a merchant CC/CT online at min-load across a midday gap "
        "LONGER than its min-down time when cycling off is uneconomic, per the "
        "restart inequality startup_per_mw > (MC - LMP_gap) x min_load_frac x "
        "gap_hours. MC is the unit's own marginal cost and LMP_gap the model's "
        "own P1 dual — both forward-derivable, no measured-generation pin, so "
        "keeper-eligible (unlike the removed NG:NG floor). Requires "
        "--caiso-ra-mustoffer; CAISO-only; default off (byte-identical).",
    )
    parser.add_argument(
        "--caiso-ra-bridge-decommit",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Solar-proportional / seasonal DECOMMITMENT control on "
        "--caiso-ra-startup-bridge (caiso-48). (1) Day-ahead horizon: only a "
        "gap <= 24 h (one DAM operating day, CAISO IFM/RUC) can be an "
        "intra-day min-load hold — longer idles are next-day decommit/"
        "re-offer decisions, never bridged. (2) Over-generation repricing: "
        "gap hours where the candidate min-load floors exceed the P1 "
        "import-dispatch + export-sink absorption reprice the held energy to "
        "the curtailable-renewable keep-running offer, and uneconomic bridges "
        "decommit cheapest-startup-first (RUC order). All inputs are the "
        "model's own P1 solution + physical constants — no residual fit. "
        "Requires --caiso-ra-startup-bridge; CAISO-only; default off "
        "(byte-identical caiso-45 bridge).",
    )
    parser.add_argument(
        "--ercot-gas-commitment-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="ERCOT gas-CC COMMITMENT BRIDGE (ERCOT-63, the committed-state "
        "mechanism promoted from the ERCOT-62b probe — diagnosis "
        "docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §5-6). "
        "P1-native: before the single scored P1 solve, hold each merchant "
        "gas-CC that the base-cost P0 pattern runs before AND after an idle "
        "gap at min-load across the gap, when the gap is shorter than its "
        "physical min-down OR (with --ercot-gas-bridge-startup, default on) "
        "re-paying its published startup cost exceeds the net hold cost at "
        "the model's own P0 duals. min-load = the MEASURED committed-CC "
        "LSL/HSL capacity-weighted p50 (60-Day DAM disclosure 2023-25). "
        "CC-only (CT physics-inert, ST_GAS rule-19-excluded — see the "
        "ScenarioConfig field). ERCOT-only; default off (byte-identical).",
    )
    parser.add_argument(
        "--ercot-gas-bridge-min-load-frac",
        type=float,
        default=None,
        help="Min-load fraction for --ercot-gas-commitment-bridge (default "
        "0.574 — the measured ERCOT committed-CC LSL/HSL capacity-weighted "
        "p50, 60-Day DAM disclosure 2023-2025; frozen, rule 21/23). In "
        "practice clips at the plant's committed-tranche capacity.",
    )
    parser.add_argument(
        "--ercot-gas-bridge-startup",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Economic (>= min-down) leg of --ercot-gas-commitment-bridge on "
        "the startup-restart inequality — the overnight-between-run-days "
        "carrier (default on with the gate; --no-ercot-gas-bridge-startup = "
        "the physical-restart-bar-only probe arm).",
    )
    parser.add_argument(
        "--ercot-gas-bridge-da-horizon",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Cap economic bridges at one DA operating day (24 h, "
        "DA_COMMITMENT_HORIZON_HOURS — a longer idle is a next-day "
        "decommit/re-offer decision, never an intra-day hold). Default on "
        "with the gate; --no-ercot-gas-bridge-da-horizon reproduces the "
        "ERCOT-62b monkeypatch construction (any gap length).",
    )
    parser.add_argument(
        "--ercot-gas-bridge-online-hours",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="ERCOT-141: extend the gas bridge's min-load floor from the idle "
        "GAPS between P0-detected runs to EVERY hour the P0 pattern has the "
        "plant ONLINE. A synchronized CC cannot run below its LSL, so the "
        "committed band is must-take whenever it is online; without this the "
        "band is a free LP variable at part load and a cheap committed offer "
        "sets the margin (the ERCOT-139 trough flood). Same detector, same "
        "measured level, same D-2 id — a wider window, not a new mechanism "
        "(rule 19). Requires --ercot-gas-commitment-bridge; default off.",
    )
    parser.add_argument(
        "--ercot-commitment-posture",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="ERCOT COMMITMENT POSTURE (the commitment-thinness lane, "
        "docs/handoffs/ercot-commitment-thinness-2026-07.md): the STANDALONE "
        "energy-only port of the pooled-linear posture lever (design note §A). "
        "Per (zone x gas-class) merchant-gas pool, an online-capacity variable "
        "U with energy headroom (sum P <= U), CEMS-measured min-load coupling "
        "(sum P >= mlf*U), and an NREL-table cyclic startup charge on dU+ — "
        "reserve-decoupled (ERCOT's ORDC co-opt has no pergen substrate), so "
        "it thins the online cheap CC and shifts peaks to fast-start CT "
        "without touching the reserve design. Fast-start CT exempt by physics "
        "(rule 18); coal/gas_st/CHP excluded by rule 19. ERCOT-only; default "
        "off (byte-identical).",
    )
    parser.add_argument(
        "--ercot-commitment-posture-min-load-frac",
        type=float,
        default=None,
        help="Min-load fraction for the postured gas-CC pools "
        "(--ercot-commitment-posture; default 0.574 — the measured ERCOT "
        "committed-CC LSL/HSL capacity-weighted p50, 60-Day DAM disclosure "
        "2023-2025; frozen, rule 23, never swept to move the residual).",
    )
    parser.add_argument(
        "--carry-operating-mothballs",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Mothballed-but-operating re-carry (the Cottonwood lane, "
        "docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md): re-carry "
        "each OA (mothballed) unit the canonical snapshot's OP filter drops "
        "for backcast solve year Y iff it is OP in the year-matched EIA-860 "
        "vintage_<Y> — EIA's own contemporaneous status, the zero-DOF "
        "availability oracle (a unit truly idle in Y is OA in vintage_<Y> "
        "too). Per-unit (a partial mothball leaves surviving OP units "
        "untouched), ISO-agnostic, backcast-only; a solve year with no "
        "committed vintage (2025) carries nothing. Default off "
        "(byte-identical).",
    )
    parser.add_argument(
        "--reliability-floor",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Generic registry-driven temperature-reliability floor: look up "
        "the ISO in RELIABILITY_FLOOR_REGISTRY (iso_configs.py) and apply all "
        "limb specs via the single generic engine "
        "(transmission.inject_reliability_floor). Replaces the per-ISO flags "
        "below. Default (unset) keeps the per-ISO base config value. ON for "
        "ERCOT/CAISO/NYISO/NEISO/MISO calibration keepers; new ISOs need ONLY this "
        "flag + a registry entry + a weather file.",
    )
    parser.add_argument(
        "--reliability-floor-plant-exclusions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Honour each reliability-floor limb's exclude_plant_codes membership "
        "correction (the coefficient CSV's optional column). A persistent-baseline "
        "limb is IDENTIFIED on a fleet-aggregate capacity factor but APPLIED per "
        "unit (pro_rata), so an economically laid-up plant — idle in its own "
        "metered conduct, yet fully available because lay-up is correctly not "
        "booked as a forced outage — is held at the fleet baseline in all 8,760 h "
        "and manufactures energy it never produced (CLAUDE.md rule 17 "
        "[R-FLOOR-WINDOW]). Identified for NYISO Long_Island ST_GAS by nyiso-140 "
        "(Port Jefferson 2517). Default (unset) = OFF, byte-identical.",
    )
    parser.add_argument(
        "--scarcity-price-overlay",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Post-solve ORDC scarcity-price overlay: compute a reserve-shortage "
        "adder from the solved headroom and add it to the prices capacity "
        "economics see (retirement, new-entry, CCS screens). Sets both "
        "scarcity_pricing_enabled (master switch) and scarcity_price_overlay "
        "(ISO eligibility gate) on ScenarioConfig. ORDC/LOLP parameters use "
        "the per-ISO defaults from ISOConfig.default_scenario_overrides "
        "(ERCOT: VOLL $5,000, MCL 3,000 MW, sigma 1,400 MW; NEISO: VOLL "
        "$2,000, MCL 1,200 MW, sigma 900 MW — ISO-NE-grounded). Dispatch, "
        "volumes and emissions are untouched. Default (unset) keeps the per-ISO "
        "base config value.",
    )
    parser.add_argument(
        "--caiso-scarcity-pricing",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO post-solve scarcity overlay: LOLP-based adder using CAISO "
        "tariff parameters (VOLL $2,000, MCL 1,400 MW, sigma 2,500 MW). "
        "Adds the scarcity adder to scored energy prices (result.prices). "
        "Automatically enables scarcity_pricing_enabled. Mutually exclusive "
        "with the in-LP reserve co-opt (caiso_reserve_coopt). CAISO only.",
    )
    parser.add_argument(
        "--caiso-lcr-commitment-credit",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO LCR commitment credit: credit the LCR constraint dual "
        "(local-commitment value, $/MWh) in the P2 commitment margin, "
        "analogous to the AS-revenue credit. Requires "
        "local_capacity_constraints. CAISO only.",
    )
    parser.add_argument(
        "--caiso-solar-deliverability",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO Lever-D local solar deliverability derate: re-curtail the "
        "uncurtailed HSL solar potential the dispatch is handed for the local / "
        "sub-area congestion the reduced 3-zone topology can't see (~70%% of real "
        "CAISO curtailment). Caps the per-zone solar CF upper bound at "
        "clip(1 - k x solar_frac(t), floor, 1) — the solar analogue of the "
        "accepted WECC corridor ATC derate, driven by the FORWARD solar-"
        "penetration signal (CISO solar/demand) so the curtailed VOLUME emerges "
        "per-year from that year's own build, not a pin to actuals "
        "(docs/caiso-lever-audit-2026-06.md, Lever D). CAISO-only. Default "
        "(unset) keeps the per-ISO base config value — ON for CAISO; "
        "--no-caiso-solar-deliverability forces it off (the over-run baseline).",
    )
    parser.add_argument(
        "--caiso-solar-deliverability-k",
        type=float,
        default=None,
        help="Local-deliverability sensitivity to solar penetration for "
        "--caiso-solar-deliverability (default 0.15 — the reference-year midday "
        "curtailment-rate / solar-penetration ratio, stable across CAISO 2023/24).",
    )
    parser.add_argument(
        "--caiso-solar-endogenous-spill",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CAISO midday price fix: skip the pre-LP solar CF derate and pass "
        "the full solar potential to the LP. The LP endogenously curtails in "
        "oversupply hours (solar not fully dispatched → solar marginal → "
        "energy-balance dual = solar_mc ≈ $0 or negative via the keep-running "
        "value offer). Overrides --caiso-solar-deliverability when on. "
        "CAISO-only. Default (unset) keeps the per-ISO base config value.",
    )
    parser.add_argument(
        "--caiso-solar-cap-at-delivered",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="INTERIM STOPGAP DIAGNOSTIC (default-off): cap the backcast solar "
        "potential at the measured EIA-930 delivered solar profile. This PINS "
        "solar to the measured outcome (no forward analogue) and must NEVER feed "
        "a keeper or be quoted as forecast skill (CLAUDE.md #11) — it exists only "
        "as an A/B reference for --caiso-solar-deliverability. CAISO-only.",
    )
    parser.add_argument(
        "--neiso-coldsnap-derate-dualfuel-unswitched",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Condition the NEISO cold-snap derate's dual-fuel exemption on its own premise (rule 19 scope correction; NEISO-only, inert unless --neiso-gas-coldsnap-derate is on). The derate exempts every EIA-860 dual-fuel unit because apply_dual_fuel_pricing is said to switch it to oil; that switch is mc=min(gas,oil), so it fires only where delivered gas has reached the oil parity. With this on, a dual-fuel unit is exempt in the hours its oil limb is actually active and derated like any other gas unit in the hours it is not. Adds no floor, no curve and no scalar; every coefficient and the window are unchanged. Default off (byte-identical).",
    )
    parser.add_argument(
        "--neiso-gas-coldsnap-derate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NEISO winter gas-availability derate (temperature-dependent forced "
        "outage): on deep-winter cold snaps the gas-electric constraint makes "
        "non-dual-fuel gas-CC/CT capacity physically UNAVAILABLE (the pipeline "
        "diverts to heating), so the fleet goes operating-reserve-short and the "
        "RCPF reserve co-opt prices the >$300 cold-hour scarcity tail (and widens "
        "the storage arbitrage spread). Cuts non-dual-fuel gas-CC/CT availability "
        "by clip(slope*(t0-TMIN),0,cap) over the cold-snap window, keyed to the "
        "NEISO load-weighted daily TMIN; magnitude anchored to NERC cold-weather "
        "forced-outage data (Winter Storm Elliott), not the price residual. "
        "Pair with --energy-reserve-coopt. NEISO-only; default off.",
    )
    parser.add_argument(
        "--neiso-oil-burn-budget",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NEISO oil-burn inventory budget: cap monthly oil-fueled generation "
        "(oil-primary + dual-fuel-switched MWh) at the measured EIA-923 "
        "Schedule 5 Petroleum receipt quantity (MMBtu -> MWh via fleet heat "
        "rates). When the budget binds in a cold-snap month, the LP shadow "
        "price IS the scarcity rent — the marginal oil MWh is priced at "
        "SRMC + shadow price, lifting the cleared LMP above the flat "
        "dual-fuel oil-parity cap (~$258) and producing >$300 hours "
        "endogenously. A reproducible physical deliverability input "
        "(CLAUDE.md #10); NOT sized to land a target tail-hour count. "
        "NEISO-only; default ON for NEISO (the keeper). "
        "--no-neiso-oil-burn-budget disables it for the no-budget A/B probe.",
    )
    parser.add_argument(
        "--neiso-winter-fuel-inventory",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NEISO winter (Nov-Mar) oil-burn inventory budget (Component A). "
        "Same LP mechanism as --neiso-oil-burn-budget, but the budget is "
        "DERIVED from forward-regenerable capacity/logistics quantities "
        "(tank start-fill + re-supply delivery rate + boiler firing rate, "
        "from the winter-fuel-inventory clean datatype / ISO-NE OFSA + WRP "
        "studies), NOT from measured EIA-923 receipts (a rule-#13-inadmissible "
        "OUTCOME). Scope is the oil-primary fleet PLUS the dual-fuel oil limb, "
        "the limb gated to its exogenous oil-switch hours so gas generation is "
        "never capped. One pooled fleet row per winter month; the binding dual "
        "is the endogenous winter scarcity rent in the persisted P1 prices. "
        "Takes precedence over --neiso-oil-burn-budget. NEISO-only, default off.",
    )
    parser.add_argument(
        "--coal-fuel-inventory",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Coal fuel-inventory monthly energy budget (miso-259) — the "
        "missing CEILING on coal. Coal carries take-or-pay and must-run FLOORS "
        "and nothing caps its energy, so the LP cannot represent a fleet that "
        "drew its stockpile down one year and could only burn what it received "
        "the next. One pooled fleet row per month caps coal energy INPUT "
        "(sum heat_rate * P, MMBtu) at (opening stock + prior-years delivery "
        "rate) x heat content / 12. RULE-13 ADMISSIBLE: every sizing quantity "
        "predates the solved year — opening stock is the footprint's December "
        "ending stock of Y-1 (coal-stocks), the rate is mean receipts over Y-2 "
        "and Y-1 (coal-receipts). Year Y's own stock path and receipts are "
        "never read. Minimum operating stock is ZERO (a floor tuned to the "
        "residual is the fitted mechanism rule 1 forbids). MISO-only, "
        "backcast-only, default off.",
    )
    parser.add_argument(
        "--neiso-winter-fuel-start-fill-bbl",
        type=float,
        default=None,
        help="Start-of-winter fleet oil inventory (barrels) sizing the "
        "--neiso-winter-fuel-inventory budget. Default (None) uses the WRP "
        "2014/15 low target (2.8M bbl); the sensitivity pair also solves the "
        "high target (3.8M bbl). A program-design logistics target "
        "(CLAUDE.md #13), NOT tuned to the price/volume residual.",
    )
    parser.add_argument(
        "--neiso-winter-fuel-mustrun",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NEISO winter fuel-security must-run (Component B): posture the "
        "fuel-secure steam fleet (COAL_BIT + oil-capable ST_GAS) at "
        "minimum-stable on winter (Nov-Mar) cold days (zone daily TMIN < "
        "-7 C, the NERC cold-weather onset) under the ISO-NE winter-"
        "reliability program posture (WRP FERC ER14-2407 / IEP ER19-1428 / "
        "OFSA). The seasonal-reliability commitment coupled to "
        "--neiso-winter-fuel-inventory: it supplies the winter commitment the "
        "energy-only LP lacks so the fuel-secure fleet burns to the program "
        "level, the dual-fuel oil limb draws the seasonal stock, and the "
        "Component-A budget can bind (endogenous C3c tail / C5b spread). "
        "REPLACES the disabled COAL/ST_GAS tmin reliability limbs (rule 19); "
        "floor depth = commit_frac x min_stable_pct, a physical constant NOT "
        "tuned to the residual (rule 24). Tags MECH_WINTER_FUELSEC for D-2. "
        "NEISO-only, backcast-only, default off.",
    )
    parser.add_argument(
        "--caiso-import-hub-prices",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Price the CAISO priced-import tranches at the MEASURED WECC "
        "neighbor-hub LMP each proxies (Mid-C/Malin for the PNW blocks, "
        "Palo Verde for the desert-SW blocks), by hour, instead of the "
        "static bundle-fitted ladder in IMPORT_TRANCHES['CAISO']. The real "
        "delivered cost of the imported energy: seasonal (spring-runoff "
        "crash) and negative in the desert-SW solar glut, so it lowers the "
        "over-high body AND reproduces the negative midday tail "
        "(DIAGNOSIS-caiso-import-ladder-2026-06-19). CAISO-only; no-op "
        "(byte-identical) without the measured intertie parquet "
        "(data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet, "
        "fetched by the fetch-caiso-oasis workflow). Default (unset) keeps "
        "the base config value (currently off pending the measured data).",
    )
    parser.add_argument(
        "--caiso-import-gas-coupling",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Shift the gas-set CAISO import tranches (DSW_CCGT, DSW_CT) by the "
        "measured commodity-gas delta (Henry Hub month + CA citygate basis, less "
        "the EIA-923 delivered gas) x heat rate, so the desert-SW gas imports "
        "track the same commodity spot --gas-hub-basis-overlay applies to "
        "in-state gas. Forecast-consistent, no-OASIS replacement for the "
        "desert-SW leg of --caiso-import-hub-prices (lever A): keeps imports "
        "competitive when the overlay cheapens in-state gas, so gas TWh stays "
        "disciplined instead of over-running ~+12%% (PLAN-caiso-gas-coupled-"
        "imports-2026-06-20). CAISO-only; pair with --gas-hub-basis-overlay; "
        "no-op (byte-identical) for forecast years (no measured gas basis). "
        "Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-import-solar-shape",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Restore the CAISO negative midday tail: collapse the desert-SW "
        "solar import block (DSW_solar_PV / Palo Verde hub) — the marginal CAISO "
        "import midday — from its flat gas-coupled level toward "
        "-renewable_keep_running_value as CAISO net load (load less utility "
        "solar/wind) drops into its annual belly, so the marginal import bids "
        "sub-$0 in the spring solar glut and sets a negative LMP (model ~14 hrs "
        "<=$0 vs actual ~868, 2024). Net-load-gated (spring-midday, not summer); "
        "depth is the existing REC/PTC keep-running constant (no new fitted price "
        "level). CAISO-only; applies on top of the gas coupling. Default (unset) "
        "keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-per-hub-intertie",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Model CAISO's WECC tie as TWO per-hub signed corridors — COI/"
        "Path-66 at the Malin hub (→ NP15, north) and Path-46/WOR at the Palo "
        "Verde hub (→ SP15, south) — each a single net direction over its OWN "
        "real link, priced at its OWN measured intertie hub. The unification of "
        "the retired single-signed-flow bidir node (per-hub netting, fixed the "
        "inverted diurnal sign; DELETED caiso-236, rule 26) and "
        "--caiso-import-hub-prices (per-hub basis): "
        "the bidir node had to average the two hubs into one price; the hub-price "
        "node kept the basis but pooled both legs onto one bubble (cheap Palo "
        "Verde midday fills the whole 8.3 GW budget, never nets → over-import + "
        "inverted diurnal). Two per-hub legs recover both, so the Palo Verde "
        "corridor reverses to EXPORT midday instead of over-importing. The 8.3 GW "
        "simultaneous-import cap stays as the WECC_import_simultaneous interface "
        "limit re-homed to the two links. Supersedes --caiso-import-hub-prices / "
        "--caiso-import-solar-shape (measured per-hub "
        "Palo Verde already prints the negative midday tail); --caiso-import-gas-"
        "coupling still applies to the desert-SW gas legs. CAISO-only; pure LP; "
        "2023 falls back to the static ladder. Default (unset) keeps the base "
        "config value (off).",
    )
    parser.add_argument(
        "--caiso-perhub-firm-base",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="With --caiso-per-hub-intertie: keep the firm/contracted import "
        "tranches (PNW_hydro_base = BPA firm hydro, DSW_solar_PV = desert-SW "
        "solar PPAs) at their static contract-cost estimates instead of the "
        "measured hourly spot hub. The real market schedules the specified/"
        "contracted majority of CAISO imports at contract cost (inframarginal), "
        "so CAISO clears domestic while the tie flows; pricing every tranche at "
        "spot transplants hub spikes into CAISO whenever the tie is marginal. "
        "Spot tranches (Mid-C economy, DSW thermal, scarcity) and both export "
        "legs stay at the measured hub. Default (unset) keeps the base config "
        "value (off).",
    )
    parser.add_argument(
        "--caiso-corridor-flow-limit",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Cap each CAISO per-hub corridor's import-direction flow at the "
        "MEASURED diurnal deliverability envelope (an ATC proxy): the per-(month "
        "× hour-of-day) p95 net import on COI/Path-66 and Path-46/WOR from EIA-930 "
        "BA-to-BA interchange. The WECC neighbors are themselves long on solar "
        "midday, so deliverable transfer into a long CAISO collapses ~6→~3.6 GW "
        "(DSW) and ~2.3→~0.8 GW (PNW) midday; without this ceiling the per-hub "
        "injector's cheap midday hub price lets the LP pull the neighbors' idle "
        "thermal tranches up to the 8.3 GW simultaneous cap (the spurious ~5 GW "
        "midday over-import behind the inverted-diurnal residual). One-sided "
        "hourly upper bound on the corridor link (export keeps the physical TTC); "
        "the LP still clears its merit order below the ceiling. Requires "
        "--caiso-per-hub-intertie. CAISO-only. Default (unset) keeps the base "
        "config value (off).",
    )
    parser.add_argument(
        "--caiso-intertie-reference-price",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Price each CAISO per-hub WECC corridor from the FORWARD reference-"
        "price formula — (henry_hub[year] + gas_basis) × neighbor marginal heat "
        "rate × load-shape — instead of the measured OASIS hub LMP. The SAME "
        "forecast-native construction PJM/MISO use, specialized to the two ties: "
        "COI/Path-66 proxies the Pacific-NW at Malin (gross-load shape), Path-46/"
        "WOR the desert-SW at Palo Verde (net-load shape, so its midday price dips "
        "with the solar glut). The level rides the forward Henry Hub trajectory "
        "and the shape rides the neighbor's tightness, so the seam stays live in a "
        "forecast year where the measured hub series is absent. The measured hub "
        "LMP is kept only as the backcast realization the formula is validated "
        "against (scripts/compare_caiso_intertie_formula_vs_measured.py); nothing "
        "is pinned to it (CLAUDE.md #10/#12). Requires --caiso-per-hub-intertie; "
        "supersedes the measured per-hub injector. CAISO-only. Default (unset) "
        "keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-corridor-atc-forward",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Cap each CAISO per-hub corridor's import flow at a FORWARD ATC "
        "deliverability ceiling instead of the measured p95 envelope: ATC(t) = "
        "corridor TTC × posted-ATC base fraction × clip(1 − k × solar_frac(t), "
        "floor, 1), where solar_frac is CISO solar / demand (a forward driver). "
        "The solar derate reproduces the structural midday deliverability collapse "
        "off a capability limit, never the measured corridor flow (CLAUDE.md #12). "
        "One-sided on the import direction (export keeps the physical TTC). "
        "Requires --caiso-per-hub-intertie; supersedes --caiso-corridor-flow-"
        "limit. CAISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-reference-price-seam",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Price BOTH legs of CAISO's two WECC corridors with the forward-"
        "native reference-price seam (the PJM/MISO INTERFACE_NEIGHBORS "
        "construction, INTERFACE_NEIGHBORS['CAISO']): per corridor, import + "
        "export flow tranches priced from (henry_hub[year] + gas_basis) × "
        "marginal heat rate × load-shape ± hurdle, with the CARB border carbon "
        "added to the import leg. The export tranches clear at hub − hurdle (the "
        "price a WECC neighbor pays for CAISO's midday solar surplus), the "
        "structural fix for the over-import / never-export bias; and the seam "
        "stays live in every year (no OASIS gap, e.g. 2023). The per-hub corridor "
        "split + the corridor ATC envelope (--caiso-corridor-flow-limit) still "
        "apply — the reference price sets the PRICE, the ATC envelope the FLOW "
        "LIMIT. Supersedes --caiso-per-hub-intertie (mutually exclusive). "
        "CAISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-per-year-import-caps",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Swap the two internal SP15-pocket import-link TTCs "
        "(SP15_rest->LA_BASIN, SP15_rest->SDGE) from the static 2023 "
        "tightest-year value baked in by the SP15 split to EACH SOLVE YEAR's "
        "own published CAISO LCT import_cap = peak_load - requirement "
        "(ScenarioConfig.caiso_per_year_import_caps). LA_BASIN "
        "12,008/15,224/15,174 and SDGE 1,436/2,074/2,071 MW for 2023/24/25, "
        "read from data/raw/capacity-deliverability/caiso/caiso.csv via "
        "data.local_capacity.load_lcr_parameters. Same convention as the "
        "static bake, never the reserve-margin gross-up, zero free parameters "
        "(CLAUDE.md #24). Measured limit over frozen estimate (CLAUDE.md #14); "
        "per-year was the deferred end state of the 2026-07-09 SP15 split. "
        "2023's published row EQUALS the static default, so 2023 is a "
        "byte-identical no-op and serves as the same-head zero-delta control. "
        "A year with no published row keeps the static default. CAISO-only. "
        "Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-asymmetric-path-ratings",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Bound CAISO's two INTERNAL north-south paths at their published "
        "WECC directional ratings instead of the symmetric TTC estimate the "
        "reduced topology ships (ScenarioConfig.caiso_asymmetric_path_ratings). "
        "Each link's baked ttc_mw is only ONE direction's rating -- Path 15 "
        "(Midway-Los Banos) 5,400 MW is its S->N limit and Path 26 "
        "(Midway-Vincent) 4,000 MW its N->S limit -- so the reverse direction "
        "runs up to 65%% too loose. When on, appends one directional "
        "InterfaceLimit per path: Path 15 3,265 N->S / 5,400 S->N and Path 26 "
        "4,000 N->S / 3,000 S->N (WECC Path Rating Catalog, "
        "interchange.caiso.CAISO_PATH_DIRECTIONAL_RATINGS). Measured "
        "directional data over a symmetric estimate (CLAUDE.md #14); zero free "
        "parameters, nothing swept (#24). CAISO-only and internal-links-only, "
        "so it composes with the import-node/corridor steps. Default (unset) "
        "keeps the base config value (off).",
    )
    parser.add_argument(
        "--caiso-zonal-loss-surface",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Represent CAISO marginal transmission losses on the internal links: "
        "split each internal CAISO link into a one-way loss pair and charge each "
        "direction the measured receiving-side marginal delivery-factor loss "
        "fraction from CAISO's own published DAM component record "
        "(data/raw/iso-specific-transmission/CAISO_loss_surface.csv, derived by "
        "scripts/data/derive_caiso_loss_surface.py as dev_z = sum(MCL_z)/sum(MCE); "
        "per-year rows for a backcast train year, pooled rows for a forecast "
        "year). The LP is otherwise LOSSLESS, i.e. it currently carries the "
        "ESTIMATE that losses are zero; caiso-164 measured that 13-20%% of the "
        "observed NP15-ZP26 basis is this component (rule 14 [R-ACCURATE]). "
        "CAISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--capacity-deliverability-limits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable the published capacity-deliverability parameter set "
        "(ScenarioConfig.capacity_deliverability_limits). In a backcast only "
        "Part A fires: the calibrated simultaneous-import scalar (CAISO's "
        "7,500 MW WECC_import_simultaneous) is replaced by the ISO's published "
        "per-area SEAM import limit (CAISO branch-group MIC summed to the WECC "
        "boundary), resolved per delivery year from the curated "
        "capacity-deliverability data. Part B (locational capacity-payment "
        "collapse) lives in capacity evolution, which the backcast never "
        "reaches. Measured limit over calibrated scalar (CLAUDE.md #14); "
        "validated by the caiso-46/47 A/B probes. Default (unset) keeps the "
        "base config value (off).",
    )
    parser.add_argument(
        "--unit-outage-lp-capacity-basis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Take the CAMPD unit-outage derate share against the capacity the "
        "multiplier is APPLIED TO in the LP "
        "(ScenarioConfig.unit_outage_lp_capacity_basis). A consistency repair, "
        "not a market feature: the extract's unit_capacity_mw numerator is the "
        "EIA-860 NAMEPLATE, while outages._iso_plant_capacity supplies a "
        "NET-SUMMER denominator; with cc_nameplate_summer_derate armed the LP "
        "additionally carries the CC bin at full nameplate, so the removed "
        "fraction is inflated by nameplate/net_summer and the model removes more "
        "MW than went out. Raises the denominator's CC bins by the same "
        "published cc_summer_derate_ratio fleet_to_bins uses — the identical "
        "invariant _iso_plant_capacity already enforces for cc_steam_part_reclass. "
        "MEASURED (EIA-860 nameplate / net summer), zero fitted scalars, and "
        "monotone (a removed fraction can only fall). caiso-184. Default (unset) "
        "keeps the base config value (off).",
    )
    parser.add_argument(
        "--campd-outage-merit-order-guard",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Take ECONOMIC LAY-UP out of the availability envelope on the "
        "per-unit CAMPD companions (ScenarioConfig."
        "campd_outage_merit_order_guard; REQUIRES "
        "--campd-per-unit-attribution and is inert without it). Selects the "
        "'-perunitmerit-' pair -- the same per-unit attribution, derived with "
        "derive_campd_unit_outages --merit-order-guard, in which a detected "
        "full-stop window whose unit's measured SRMC sat above the revealed "
        "clearing cost of the capacity that WAS running is classified as "
        "economic lay-up and leaves the outage overlay, so the LP keeps the "
        "capacity and declines it on its own economics. Zero free parameters "
        "(MERIT_OOM_FRAC / MERIT_RCC_PCTL are the deriver's committed "
        "constants). It does NOT repair the overlay's over-booking -- see "
        "PREREG-nyiso177 gates G2/G3, which record that object as open.",
    )
    parser.add_argument(
        "--campd-per-unit-attribution",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Attribute a MIXED plant's measured CAMPD conduct to the bin that "
        "CONTAINS each unit, in BOTH CAMPD-derived solve inputs at once "
        "(ScenarioConfig.campd_per_unit_attribution). Selects the '-perunit-' "
        "companions written by derive_thermal_tranches --per-unit-attribution "
        "and derive_campd_unit_outages --per-unit-crosswalk, which route through "
        "the SAME scripts/lib/campd_measured_classes crosswalk, so the two "
        "artifacts cannot disagree about which bin a machine is in. A "
        "consistency repair, not a market feature, and the WIDER form of "
        "--unit-outage-mixed-gas-routing (which reaches only the mixed-GAS "
        "subset and is measurably wrong where the two disagree, nyiso-175b K3). "
        "The incumbent derivers attribute by two different proxies: the tranche "
        "deriver gives a plant's facility-summed CAMPD net to 'the group holding "
        "the most nameplate', and the outage deriver short-circuits on a "
        "last-writer-wins facility group. Measured at NYISO (nyiso-175b/176): "
        "13.7577 TWh of 2023-2025 conduct is re-seated across six plants, and "
        "E F Barrett's 16 combustion turbines alone carry 610 of the outage "
        "extract's 1,137 spurious 2023-2025 windows. ONE gate over both "
        "artifacts by design (rule 19 [R-ONE-MECH]): a tranche row's "
        "online/committed statistics are computed over an outage-derated "
        "denominator, so repairing one artifact alone is internally "
        "inconsistent. Zero free parameters; falls back to the incumbent "
        "artifact wherever a companion has not been derived, so the off path is "
        "byte-inert and only NYISO is reachable today. See "
        "docs/FINDING-nyiso176-input-artifact-reproducibility-2026-09-02.md.",
    )
    parser.add_argument(
        "--unit-outage-mixed-gas-routing",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Route each CAMPD unit's outage window to the model bin matching "
        "the UNIT's own class at a facility carrying two or more model gas bins "
        "(ScenarioConfig.unit_outage_mixed_gas_routing). A consistency repair, "
        "not a market feature, and the ADDRESS sibling of "
        "--unit-outage-lp-capacity-basis (which fixes the derate's denominator) "
        "and --unit-outage-fleet-status-scope (its event set). "
        "derive_campd_unit_outages._resolve_unit_group short-circuits on the "
        "FACILITY's group, whose own pjm-75 premise is that the facility carries "
        "ONE gas group; but that group is last-writer-wins over the fleet, so at "
        "a mixed CC+ST facility every unit is handed to whichever bin came last. "
        "Measured at MISO (miso-200): Ninemile Point 1403 sends its two "
        "'Tangentially-fired' gas-steam boilers (1,651.1 MW) onto its 649.5 MW "
        "CC bin — pre-clip removed share up to 3.556, above 1.0 for 4,920-6,192 "
        "h/yr — while the ST_GAS bin that actually holds them receives ZERO rows "
        "and reads availability identically 1.0. Selects the '-unitroute-' "
        "companion extracts for BOTH the >=5-day std layer and the declared-event "
        "maxgen layer. Zero free parameters; CAMPD's published unitType is the "
        "discriminator. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--unit-outage-window-hour-grain",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Read each CAMPD unit-outage window at its DETECTED HOUR grain "
        "(ScenarioConfig.unit_outage_window_hour_grain). REQUIRES "
        "--campd-per-unit-attribution AND --campd-outage-merit-order-guard and "
        "is inert without either. The detector has always worked in hours while "
        "the extract stored DATES, so data/outages.py re-expanded every window "
        "to outage_start 00:00 -> outage_end 23:00 and asserted up to 23 h at "
        "EACH EDGE that the detector never detected -- exactly where the "
        "event-based contract guarantees the neighbouring hour was RUNNING. "
        "Selects the '-perunitmerithour-' extract derived with "
        "derive_campd_unit_outages --hour-grain, whose two in-process "
        "stop-the-line assertions prove the grain cannot MOVE a detected "
        "window, only narrow it. MEASURED on NYISO's own CAMPD (nyiso-229): "
        "8,144-10,167 unit-hours per year asserted unavailable while the meter "
        "shows grossLoad > 0, carrying 0.95-1.38 TWh, ~95 %% of them within 23 h "
        "of a window boundary. ZERO fitted scalars, zero free parameters. "
        "Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--unit-outage-st-capacity-basis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Put each STEAM bin's unit-outage removed MW on the LP's own "
        "capacity basis — the fleet unit's pmax_mw "
        "(ScenarioConfig.unit_outage_st_capacity_basis). A consistency repair, "
        "not a market feature, and the steam-side sibling of "
        "--unit-outage-lp-capacity-basis, which is CC-ONLY "
        "(outages._CC_NAMEPLATE_BASIS_GROUPS) and so can never reach an "
        "ST_GAS/ST_CHP bin. The accumulator derates a bin by "
        "unit_capacity_mw / cap[bin], where for a steam bin the numerator is the "
        "extract's per-unit EIA-860 NAMEPLATE (or a CEMS observed peak) while the "
        "denominator is the fleet's NET-SUMMER pmax sum, so the removed FRACTION "
        "is inflated by nameplate/net_summer and the model removes more MW than "
        "went out. Measured at MISO (miso-201): Ninemile Point 1403 generator 5 "
        "is nameplate 895.1 MW against net summer 742.6 MW, so unit 5 alone out "
        "removes 0.611 of the bin against a correct 0.507. Applied "
        "ALL-OR-NOTHING per bin (a bin whose extract units do not resolve 1-1 "
        "onto distinct fleet units keeps the production basis entirely), zero "
        "fitted scalars, non-ERCOT only, byte-inert while off. Covers the std "
        ">=5-day, short, partial and LAY-UP layers together (their shares are "
        "contractually additive); the declared-event maxgen layer is out of "
        "scope by construction, its rows carrying a measured derate_mw rather "
        "than a unit capacity. See "
        "results/calibration/PREREG-miso201-st-basis-alignment-2026-09-02.md.",
    )
    parser.add_argument(
        "--unit-outage-short-windows-gas",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Extend the sub-5-day short-window unit-outage overlay from its "
        "coal-only scope to the GAS classes "
        "(ScenarioConfig.unit_outage_short_windows_gas), reading "
        "campd-unit-outages-shortgas-<ISO>.csv alongside the coal extract. "
        "outages.UNIT_OUTAGE_MIN_DAYS discards every window under 5 days and "
        "the sub-floor companion re-filters to COAL, so the 0-5 d family is "
        "captured for coal and thrown away for CC_REGULAR / CC_CHP / ST_GAS / "
        "ST_CHP. Widens a DISCARD; disjoint from the coal scope by plant group "
        "and from the >= 5-day overlay by duration, so it stacks on neither "
        "(rule 19 [R-ONE-MECH]). The gas scope's economic-idling separator is "
        "the MERIT-ORDER guard, not the coal SHORT_BASELOAD_CF baseload guard "
        "a cycling combined cycle cannot pass (rule 18 [R-PHYSICS]). Zero free "
        "parameters; byte-inert while off. An ISO with no gas extract on disk "
        "gets the coal scope unchanged.",
    )
    parser.add_argument(
        "--unit-outage-per-unit-clip",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enforce, in the shared unit-outage accumulator, the invariant that "
        "ONE UNIT CANNOT BE MORE THAN 100 %% OUT OF SERVICE "
        "(ScenarioConfig.unit_outage_per_unit_clip). A defect repair, not a "
        "market feature. outages.unit_outage_event_window reconstructs a "
        "day-granular extract row as [outage_start, outage_end + 1 day), so two "
        "windows of the SAME unit that share a boundary date both cover that "
        "day; the accumulator SUMS row shares rather than unioning them, and "
        "subtracts the unit's capacity TWICE for 24 h. Measured at MISO "
        "(miso-202 phase 0): every one of the 845 same-unit window overlaps is "
        "EXACTLY 24.0 h (std5d 648, lay-up 197, short 0) — a single-bin "
        "histogram, the fingerprint of the '+ 1 day' artifact and of nothing "
        "else — and a per-unit clip restores 91.1 / 77.6 / 103.4 GWh of "
        "capability in 2023 / 2024 / 2025 across CC_REGULAR, ST_GAS, COAL, "
        "CC_CHP and ST_CHP bins. Each unit's removed MW is accumulated into its "
        "own array and capped at that unit's own capacity before the units sum "
        "into the bin: a ceiling on a sum, not a window-merging heuristic, so it "
        "is the identity except in the physically impossible case and can only "
        "ever remove LESS. Zero free parameters, byte-inert while off. Covers "
        "the std >=5-day, short, partial and LAY-UP layers together (their "
        "shares are contractually additive); the declared-event maxgen layer is "
        "out of scope BY MEASUREMENT — its windows are already hour-granular and "
        "carry zero same-unit overlaps over 544 unit-series. See "
        "results/calibration/PREREG-miso202-boundary-day-double-count-2026-09-03.md.",
    )
    parser.add_argument(
        "--cc-winter-capability-basis",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Carry combined cycles on the PUBLISHED seasonal capability "
        "envelope B = max(net_summer, winter) instead of nameplate, with each "
        "season's availability taking its OWN EIA-860 published rating "
        "(ScenarioConfig.cc_winter_capability_basis; requires "
        "cc_nameplate_summer_derate). That flag is a ONE-season instrument on a "
        "TWO-season published record: it derates Jun-Sep to the published "
        "net-summer rating but leaves OFF-summer capability on nameplate, a "
        "premise EIA-860 never publishes and CEMS refutes (off-summer p999 is "
        "0.73-0.89 of nameplate but 0.906-1.001 of the published WINTER "
        "rating). Two-directional, not a haircut: 8 of the 67 California CC "
        "plants publish a winter rating ABOVE nameplate (358 Mountainview "
        "1110.0 vs 1036.8, demonstrated off-summer peak 1111.0). A basis swap, "
        "not a second derate; ZERO fitted scalars and zero DOF (every value is "
        "an EIA-860 published rating or a ratio of two of them, and the CEMS "
        "record enters only as a check). caiso-186. Default (unset) keeps the "
        "base config value (off).",
    )
    parser.add_argument(
        "--ramp-limits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Plant-group hourly ramp-envelope rows in the dispatch LP "
        "(ScenarioConfig.ramp_limits, GATED default off). Bounds each ramp-"
        "constrained plant group's hourly dispatch delta by its CAMPD-"
        "measured max observed 1-h up/down move (derive_campd_ramp_envelopes"
        ".py; design docs/ramp-locational-design-2026-07.md §1) — a measured "
        "physical-capability input, zero fitted DOF. In ramp-bound evening "
        "hours the marginal unit becomes the fast resource, so CT clears on "
        "merit. No-op for ISOs without the committed envelope artifact. "
        "Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--local-capacity-constraints",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Local-capacity (LCR-area) minimum-generation rows in the "
        "dispatch LP (ScenarioConfig.local_capacity_constraints, GATED "
        "default off). One >= row per covered LCR area per hour: in-area "
        "thermal (+ in-area storage share) must cover max(0, share*zone_load"
        " - import_cap), all parameters from the ISO's published LCR study "
        "(CAISO LCT report; design docs/ramp-locational-design-2026-07.md "
        "§3). The dual is uplift-like out-of-market commitment — the zonal "
        "hub LMP benchmark is untouched. No-op for ISOs without covered "
        "areas / the membership crosswalk. Default (unset) keeps the base "
        "config value (off).",
    )
    parser.add_argument(
        "--gas-offer-margin-anchor-vintage",
        action="store_true",
        help="Resolve the gas-offer net-revenue margin's identification anchor "
        "(ScenarioConfig.gas_offer_margin_anchor) on the SOLVE YEAR's own mean "
        "delivered-gas series instead of the frozen 2023-2025 training-window "
        "mean — the same measurement, evaluated on the year being solved "
        "(pjm-169 F4). The mechanism's own identity is that at fuel == anchor "
        "the reformed offer reduces EXACTLY to the registered band multiplier; "
        "markup_hr x (anchor - fuel) is a linear unsaturated extrapolation, so "
        "outside the identification window that identity fails proportionally "
        "— and when fuel > anchor it marks gas offers DOWN. Zero free "
        "parameters; requires --gas-offer-margin; refuses to stack with "
        "--gas-offer-margin-zonal-anchor (rule 19). Default off, "
        "byte-identical off.",
    )
    parser.add_argument(
        "--gas-offer-margin-zonal-anchor-vintage",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Resolve the gas-offer net-revenue margin's PER-ZONE "
        "identification anchors (ScenarioConfig.gas_offer_margin_anchor_by_zone) "
        "on the SOLVE YEAR's own mean delivered-gas series instead of the "
        "frozen 2023-2025 training-window means — the same measurement, "
        "evaluated on (zone, year) rather than on (zone) (nyiso-230). Closes "
        "the gap left by --gas-offer-margin-anchor-vintage, which resolves the "
        "ISO-level anchor and refuses to stack with the zonal gate, leaving an "
        "ISO that carries a zonal basis with no route to the year index at "
        "all. Zero free parameters; the identity is pinned by test (averaging "
        "the runtime resolution over 2023-2025 reproduces the registered "
        "GAS_OFFER_MARGIN_ANCHOR_BY_ZONE table). Requires --gas-offer-margin "
        "AND --gas-offer-margin-zonal-anchor; refuses to stack with "
        "--gas-offer-margin-anchor-vintage (rule 19). Default off, "
        "byte-identical off.",
    )
    parser.add_argument(
        "--pjm-interface-feed-admissibility-gate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="PJM interface-feed admissibility gate "
        "(ScenarioConfig.pjm_interface_feed_admissibility_gate): judge each "
        "published transfer-limit series against its OWN posted limit before "
        "letting it bound a link, and fall through to the static per-link TTC "
        "— loudly, with the arithmetic logged at WARNING — when it is "
        "inadmissible. Tri-state: unset keeps the per-ISO backcast default "
        "(PJM ARMED default-ON since pjm-169, owner decision 2026-09-06; every "
        "other ISO off); --no-pjm-interface-feed-admissibility-gate forces the "
        "PRE-ARM posture, enforcing every posted series verbatim. Only read "
        "under --pjm-measured-interface-limits. Rule 14 [R-ACCURATE] "
        "named-exception: PJM's pre-2023 Average Eastern / Average Western "
        "postings are a different time/area aggregation under one series name.",
    )
    parser.add_argument(
        "--vre-curtailment-oversupply-allocation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Allocate the reference-rate curtailment energy onto the "
        "OVERSUPPLY hours instead of flat across all 8,760 "
        "(ScenarioConfig.vre_curtailment_oversupply_allocation, SPP-51c). A "
        "high-curtailment fallback ISO's renewable bound is today "
        "delivered/(1-rate) -- a FLAT per-hour gross-up. Delivered is already "
        "NET of curtailment, so the measured annual spill is spread uniformly, "
        "i.e. everywhere except where it happened: SPP's keeper re-curtails "
        "0.0003-0.0017%% against a measured 9.65%%, and prices below zero in "
        "0-7 hours a year against ~1,000 measured. This flag water-fills the "
        "SAME frozen annual energy onto the lowest-net-load hours, capped by "
        "the fleet's own online-capacity headroom, at the level that makes the "
        "annual identity hold. Annual potential is unchanged in every year, so "
        "the measured reference rate (rule 23) is untouched; zero new free "
        "parameters (rule 21); forward-native (rule 13); ISO-agnostic "
        "(rule 25). Default off -- every keeper replays byte-identical.",
    )
    parser.add_argument(
        "--spp-curtailment-ceiling",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Apply the SPP wind curtailment CEILING to the CF upper bound "
        "(ScenarioConfig.spp_curtailment_ceiling, SPP-58). SPP's wind bound is "
        "delivered/(1-rate) -- a gross-up whose own stated precondition is "
        "'real headroom, ENDOGENOUSLY RE-CURTAILED'. It is not: measured on "
        "keeper 2026-09-09-spp-52a-fossil-offer's committed sidecars the LP "
        "re-curtails 0.261/0.223/0.174%% in 2023/2024/2025 against the 9.65%% "
        "the gross-up applies, because the 2-zone reduction collapses the SPS "
        "/ Texas-Panhandle and western Kansas / Oklahoma export pockets that "
        "do the real curtailing. This flag multiplies the wind bound by "
        "1 - depth * congestion_share(net-load decile, hour, season), the "
        "share read off SPP's own published RTBM binding-constraint archive "
        "and the depth (--spp-curtail-depth-wind) centred on SPP's own "
        "published curtailment MW. It SUPERSEDES "
        "--vre-curtailment-oversupply-allocation in data.renewables rather "
        "than stacking on it (rule 19 [R-ONE-MECH]), takes no solar (SPP "
        "solar is delivered-pinned), carries zero free parameters (rule 21) "
        "and is forward-native (rule 13). SPP only; default off -- every "
        "keeper replays byte-identical.",
    )
    parser.add_argument(
        "--spp-curtail-depth-wind",
        type=float,
        default=None,
        help="Level coefficient for --spp-curtailment-ceiling "
        "(ScenarioConfig.spp_curtail_depth_wind, default 0.288137 -- the "
        "energy-weighted value that centres all three scored years on SPP's "
        "published curtailment MW at once). 0.0 is the inert ablation. Do NOT "
        "sweep it against a gate: it is identified on measured published "
        "curtailment, and selecting it by which value makes a criterion pass "
        "is the fitted-mechanism selection rule 1 [R-STRUCT] forbids.",
    )
    parser.add_argument(
        "--netload-drag-merit-allocation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fill the net-load reliability-drag mandate CHEAPEST-FIRST instead "
        "of pro-rata (ScenarioConfig.netload_drag_merit_allocation, ercot-259). "
        "The driver curve produces a FLEET capacity factor; the applier spreads "
        "it across every non-peak tranche's own pmax, which asserts that every "
        "plant is committed at that fraction in every hour — a level below any "
        "boiler's minimum stable load, and a uniform answer to a lumpy "
        "question. Measured consequence on the ERCOT keeper's own committed D-4 "
        "conduct rows: the plant convicted of being floored while its meter "
        "reads zero is that year's LEAST-committed plant in all five scored "
        "years, and in 2021 the floor holds Lake Hubbard at 1.22 TWh against "
        "0.36 TWh measured while holding V H Braunig at 1.50 against 3.72. "
        "This flag keeps the SAME hourly mandate over the SAME rows and only "
        "changes its distribution: commitment blocks (mustrun, then committed) "
        "before any economic tranche, ascending bid heat rate within a rank, "
        "the marginal row taking the remainder and rows past the fill point "
        "carrying no floor. Same mechanism id and still a per-row min_gen, so "
        "D-2/D-4 attribution and the C8 forced share stay measurable. Zero free "
        "parameters. Forward-native (not backcast-gated).",
    )
    parser.add_argument(
        "--netload-drag-min-run-persistence",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Persist the net-load reliability-drag mandate across each unit's "
        "own MINIMUM RUN LENGTH instead of reading it off the curve hour by "
        "hour (ScenarioConfig.netload_drag_min_run_persistence, pjm-177). The "
        "drag's floor_frac collapses to zero whenever net-load crosses below "
        "the curve's own zero-crossing and returns when it rises, so the "
        "mechanism representing a gas-steam boiler's COMMITMENT cycles that "
        "boiler on the diurnal net-load wave; ST_GAS_COMMITMENT_PARAMS "
        "(NREL/SR-5500-55433) says in this same repo that it cannot -- min-run "
        "24 h efficient / 48 h older-subcritical. Measured on PJM 2023-25 raw "
        "CAMPD opTime, the fleet's ONLINE capacity is flat across the day "
        "(hour-of-day max/min 1.19 / 1.07 / 1.05; hour-of-day R^2 "
        "0.003 / 0.001 / 0.001) with median run lengths of 25 / 28 / 57 h, "
        "while the drag's binding excursions run a median 7-8 h. This flag "
        "keeps the SAME rows, coefficients and mechanism id and changes only "
        "WHICH HOURS the mandate lands in, via a centred circular moving "
        "average over each row's table min-run (rule 19 [R-ONE-MECH]). Zero "
        "free parameters (rule 21); the coefficients never move (rule 23); "
        "forward-native (rule 13); inert on a WINDOWED floor, so the CT "
        "evening-ramp limb is never persisted. Default off -- every keeper "
        "replays byte-identical.",
    )
    parser.add_argument(
        "--netload-drag-layup-window-mask",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Mask the ST_GAS / CT_PEAKER net-load reliability-drag floors "
        "with the MEASURED economic-lay-up windows "
        "(ScenarioConfig.netload_drag_layup_window_mask, ercot-256). The "
        "merit-order guard already removes a >=5-day full stop from the "
        "AVAILABILITY envelope when the unit sat out of merit, on the express "
        "charter that an economically idle unit stays available; without this "
        "mask the drag floor forces the plant on inside those very windows "
        "(rule 17 [R-FLOOR-WINDOW]). When armed the floor's clip basis becomes "
        "pmax x max(0, availability - layup_share); availability itself is "
        "untouched. BACKCAST ONLY (rule 13) and zero free parameters (rule 21) "
        "— the windows and shares are the frozen derive layer's. Tri-state: "
        "unset keeps the per-ISO default (off everywhere).",
    )
    parser.add_argument(
        "--ct-netload-drag",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force the CT_PEAKER net-load reliability-drag floor on or off "
        "(ScenarioConfig.ct_netload_drag). Tri-state: unset keeps the per-"
        "ISO calibration default (CAISO keeper default-ON, others off); "
        "--ct-netload-drag forces it on; --no-ct-netload-drag forces it off "
        "— the ramp+LCR A/B arms run CAISO with the drag scrubbed without "
        "touching the keeper default.",
    )
    parser.add_argument(
        "--nyiso-local-selfsupply",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO Long Island (zone K) local self-supply floor: force the "
        "cable-islanded LI pocket to meet a forward fraction of its own hourly "
        "load (NYISO_LOCAL_SELFSUPPLY_FRAC) with in-zone dispatchable thermal "
        "generation rather than importing the full cable rating of cheap NYC "
        "gas — NYISO's LMIC / local-reliability rule. Recovers the under-run LI "
        "fleet (model 3.7 vs EIA-923 8.52 TWh, 2023) and separates the LI "
        "premium. Scales with load (forward-reproducible), NOT pinned to "
        "measured generation. NYISO-only. Default (unset) keeps the base config "
        "value (off).",
    )
    parser.add_argument(
        "--nyiso-scr-edrp",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO SCR/EDRP emergency demand response as endogenous "
        "price-responsive supply blocks: add one pseudo-generator per model "
        "zone at the zone's Gold-Book-registered DR MW and the EDRP-floor "
        "strike (--nyiso-scr-edrp-strike), clearing the energy balance only "
        "when the zone LBMP would exceed the strike (endogenous scarcity "
        "trigger, never pinned to event dates). Caps the downstate scarcity "
        "tail. Gold-Book-registered capability + market-design strike, "
        "forward-reproducible (rule 13/17). NYISO-only. Default (unset) keeps "
        "the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-scr-edrp-strike",
        type=float,
        default=None,
        help="Marginal cost ($/MWh) of the NYISO SCR/EDRP demand-response "
        "blocks (default: the published EDRP $500/MWh compensation floor). "
        "Only consumed when --nyiso-scr-edrp is on.",
    )
    parser.add_argument(
        "--nyiso-firm-imports",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO firm import baseload: floor the cheap Hydro-Québec / Ontario "
        "priced-node tranches (NYISO_FIRM_IMPORT_FLOOR_FRAC) as must-flow, "
        "price-insensitive baseload that flows regardless of NY's hourly price, "
        "instead of pricing them as economy energy that backs off in cheap "
        "hours/years. Requires --priced-interchange; no-op on the served-wedge "
        "path. NYISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-import-reconciliation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO priced import-node boundary-flow reconciliation: pin the "
        "priced node's MONTHLY net interchange to the measured EIA-930 schedule "
        "(nyiso_net_interchange) via a per-month band constraint in the LP. The "
        "near-static economic tranche ladder clears a near-flat ~18.5-21.6 TWh "
        "that does not track the metered schedule's 23.45 -> 20.35 -> 19.09 TWh "
        "decline (under-imports 2023, over-imports 2024/25); the band replaces "
        "that economic estimate with the authoritative measurement (rule #11), "
        "priced tranches still setting the marginal price within each month's "
        "envelope. Standard production-cost boundary-flow calibration. Requires "
        "--priced-interchange; NYISO-only. Default (unset) keeps the base config "
        "value (off).",
    )
    parser.add_argument(
        "--nyiso-import-hub-prices",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO measured-neighbor import pricing: reprice the priced node's "
        "PJM_west / ISONE_tie tranches at the MEASURED hourly PJM / ISO-NE "
        "Day-Ahead system LMP (+$1 wheeling hurdle), the residual "
        "import_scarcity block at the hourly max of the two, and the "
        "export_surplus sink at the hourly min − hurdle, replacing the static "
        "per-year fitted IMPORT_TRANCHES_BY_YEAR ladder (a backcast fit, blind "
        "to neighbor fundamentals) with a measured neighbor price-formation "
        "input (rule #12). The NYISO analogue of --caiso-import-hub-prices / "
        "--miso-pjm-lmp-import-pricing. HQ/IESO contract tranches, the monthly "
        "EIA-930 reconciliation band, HQ firm floor and SIL cap are unchanged. "
        "Requires --priced-interchange; NYISO-only; no-op without the measured "
        "neighbor LMP parquets. Default (unset) keeps the base config value "
        "(off).",
    )
    parser.add_argument(
        "--nyiso-seam-deliverability-envelope",
        action="store_true",
        help="NYISO external-seam deliverability envelope (nyiso-125): the two "
        "border links whose external ties land unambiguously in ONE NYISO load "
        "zone -- NYC (Zone J: HTP + Linden VFT) and Long_Island (Zone K: "
        "Neptune + Cross Sound + Northport-Norwalk 1385) -- trade their flat "
        "symmetric static rating for NYISO's own measured p90 DIRECTIONAL "
        "HOURLY envelope off the MIS P-32 posting. Upstate_West and "
        "Capital_Hudson keep their statics (refused on identification, rule 20). "
        "Superseded by --nyiso-seam-par-attribution; NYISO-only, default off.",
    )
    parser.add_argument(
        "--nyiso-seam-par-attribution",
        action="store_true",
        help="NYISO FULL-SEAM PAR attribution (nyiso-127): rebuild ALL FOUR "
        "border-link caps from the measured MIS P-32 per-neighbour schedules, "
        "attributing each posted row to the model zone its ties physically land "
        "in, and splitting the one row that does not land in a single zone -- "
        "SCH - PJ - NY -- by NYISO's own published NY-NJ PAR interchange "
        "percentages conditioned on published PAR availability (MIS P-33 "
        "outSched). SUPERSEDES --nyiso-seam-deliverability-envelope rather than "
        "stacking on it (rule 19). Zero free parameters. NYISO-only, default "
        "off. Pre-registration: results/calibration/"
        "PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md.",
    )
    parser.add_argument(
        "--nyiso-iroquois-winter-spread",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO eastern (Iroquois Z2) winter gas premium reconciled from "
        "measured data (rule #13): keep the measured SOM ANNUAL Iroquois-"
        "Transco spread exactly but allocate it across months in proportion "
        "to the measured Algonquin (MA-citygate) monthly basis (the New "
        "England scarcity signal that physically causes the premium; zero in "
        "unconstrained months). Zonal offsets become monthly hub ratios (NYC "
        "resolves to its own measured Transco Z6 NY monthly; Upstate to its "
        "SOM annual level on the Henry Hub shape). No fitted constant. "
        "Requires the NYISO zonal basis + hub overlay; NYISO-only. Default "
        "(unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-synchronised-reserve",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO online-gated SPINNING reserve (downstate-reserve frontier "
        "path A): a NYC locational 10-minute spinning family on a reserve class "
        "whose headroom counts only ONLINE quick-start generation, not idle "
        "capacity — so offline peakers no longer count as phantom deliverable "
        "reserve. Forces NYC peakers to commit (CT_PEAKER up) and binds the "
        "family so the RCPF >$300 tail fires endogenously (C3c/C3a up). Requires "
        "--energy-reserve-coopt; NYISO-only. Default (unset) keeps the base "
        "config value (off). With --commitment this becomes PATH B: the spinning "
        "family rides the ordinary class-1 headroom and the P2 commitment screen "
        "(+ reserve_adequacy_commit) is the online gate, so the class-1 NYC "
        "headroom equals the physically-correct Sum_online(pmax - P).",
    )
    parser.add_argument(
        "--nyiso-li-locational-reserve",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO Long Island (Zone K) published locational reserve ladder. "
        "The model carried NO Zone-K family at all (NYISO_RCPF_LOCATIONAL stops "
        "at NYC and the measured #1344 intake has no LI region), so this is a "
        "rule-14 omission of a PUBLISHED requirement, not a new assumption. Adds "
        "the two printed LI cells of the same Locational Reserve Requirements "
        "posting that grounds the NYC families: 10-minute total 120 MW all "
        "hours, and 30-minute total 270 MW OFF-peak / 540 MW ON-peak (the one "
        "diurnal in-pocket instrument the Zone-J/K survey found). Demand curve "
        "$25/MW per Ancillary Services Manual sec 6.8 items 10/15; the on/off-peak "
        "boundary the posting leaves undefined resolves to the tariff's own MST "
        "sec 2.15 On-Peak definition (7am-11pm EPT, Mon-Fri, ex-NERC holidays) - a "
        "published calendar rule that regenerates for any forward year. Requires "
        "--energy-reserve-coopt; NYISO-only. Default (unset) keeps the base "
        "config value (off).",
    )
    parser.add_argument(
        "--nyiso-incity-commitment-obligation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO in-city (Zone J/K) load-pocket COMMITMENT OBLIGATION - the "
        "in-city must-run lane's mechanism, armed by the owner's 2026-07-26 "
        "adjudication reopening the closed C3a 'reserve' lever (closed as a "
        "PRICING lever, measured delta $0.00 on the 2023 trough; this is a "
        "COMMITMENT driver, a different phenomenon). Re-classes the published "
        "NYC + LI 10-minute families onto an ONLINE-GATED in-pocket obligation "
        "class (steam + fast-start GT): headroom becomes R <= rho * sum P over "
        "that fleet, so idle capacity backs nothing and meeting the published "
        "requirement forces in-pocket units to be DISPATCHED rather than merely "
        "present. Per rule 19 it SUPERSEDES the NYC/LI ST_GAS reliability-floor "
        "limbs automatically (they are dropped, never stacked on). Mutually "
        "exclusive with --nyiso-synchronised-reserve (hard error: same "
        "phenomenon). Requires --energy-reserve-coopt; NYISO-only. Default "
        "(unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-east-reserve-families",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO published EAST spin_10 (330 MW) + total_30 (1,200 MW) "
        "reserve families - the nyiso-84 rule-14 omission fix, one tier up "
        "from the Zone-K one: only the EAST 10-minute-total row (1,200 MW / "
        "$775) of the three printed EAST rows in the Locational Reserve "
        "Requirements posting was represented. Demand-curve values pinned "
        "from Ancillary Services Manual sec 6.8 items 2 and 12: BOTH $40/MW "
        "(NOT the $775 of item 7, the 10-minute total; $25 before the "
        "July-2021 procurement enhancements). Requires --energy-reserve-coopt; "
        "NYISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-spin-reserve-online",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO online-gated PUBLISHED spinning families (nyiso-84 "
        "mechanism arm): re-classes nyca_10min_spin (655 MW, $775) - and "
        "east_10min_spin (330 MW, $40) when --nyiso-east-reserve-families "
        "adds it - onto the ONLINE-gated reserve class (R <= rho * sum online "
        "quick-start P), the same class-2 machinery the in-city obligation "
        "and path A use. Driver: the product definition - spinning reserve "
        "is synchronized supply, so idle capacity backs none of it. Mutually "
        "exclusive with --nyiso-synchronised-reserve (hard error: same "
        "phenomenon); composes with --nyiso-incity-commitment-obligation. "
        "Requires --energy-reserve-coopt; NYISO-only. Default (unset) keeps "
        "the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-spin-headroom-frac",
        type=float,
        default=None,
        help="Path-B committed-capacity target multiplier for the NYISO "
        "reserve-adequacy commit: force-commit NYC quick-start until committed "
        "capacity covers the measured NYC spinning requirement (250 MW) times "
        "this factor. Default (unset) keeps the config value (1.0 = commit to the "
        "measured requirement). A coverage multiple on the measured requirement, "
        "NOT a price-residual fit.",
    )
    parser.add_argument(
        "--nyiso-dynamic-reserve-requirements",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO condition-varying reserve requirements (issue #1344, Ask B): "
        "replace the in-LP co-opt families' static published requirements with "
        "the MEASURED hourly series derived from the published LRR schedule "
        "(SENY 30-min hourly steps 1,300/1,550/1,800 MW) and logged "
        "Thunderstorm-Alert windows (data/raw/NYISO-AS/requirements/"
        "NYISO_reserve_requirements_{year}.csv, scripts/"
        "derive_nyiso_reserve_requirements_hourly.py). A market-design input "
        "(rule 13); measured reserve PRICES stay validation-only. Hard-errors "
        "when the derived series is absent. Requires --energy-reserve-coopt; "
        "NYISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-hydro-reserve-eligible",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO conventional-hydro reserve-SUPPLY eligibility (issue #1344, "
        "lever 3): the in-fleet conventional hydro (~4.6 GW — NYPA "
        "Niagara/St-Lawrence + Capital) joins the co-opt reserve-eligible set "
        "alongside thermal in both the full (30-min) and quick-start (10-min) "
        "classes, so it supplies the operating reserve the thermal+storage-only "
        "co-opt lacks in tight summer hours (the East-10min/NYCA-30min ORDC "
        "over-spike that over-prices 2023 under dynamic requirements). Held "
        "reserve spends no water (budget bounds dispatched energy only); the "
        "CAISO_HYDRO_RAMP10_FRAC hydro-reserve basis. A structural mechanism "
        "(rule 1), not a residual tune. Requires --energy-reserve-coopt; "
        "NYISO-only. Default (unset) keeps the base config value (off).",
    )
    parser.add_argument(
        "--nyiso-scr-edrp-reserve-eligible",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO SCR/EDRP demand-response reserve-SUPPLY eligibility (issue "
        "#1344, lever 3 step 2 — the SENY tail): the in-fleet SCR/EDRP "
        "demand-response blocks (already energy-only $500-strike pseudo-gens) "
        "join the co-opt reserve-eligible set in the FULL (30-min) class only, "
        "scoped to the downstate zones NYC + Long_Island + Lower_Hudson. SCR is "
        "a NYISO-certified 30-min operating-reserve provider (Ancillary Services "
        "Manual §4 / MST §15), so this supplies the SENY/NYC 30-min reserve the "
        "hydro union (East/NYCA) cannot reach — the driver of the unclosed 2023 "
        "downstate >$300 tail. Held reserve forces no energy (the per-zone "
        "headroom row trades it against the $500 strike). A structural mechanism "
        "(rule 1), not a residual tune. Requires --energy-reserve-coopt and "
        "--nyiso-scr-edrp; NYISO-only. Default (unset) keeps the base value (off).",
    )
    parser.add_argument(
        "--neiso-dynamic-reserve-requirements",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NEISO condition-varying reserve requirements (winter scarcity "
        "charter Limb A): replace the in-LP co-opt families' static published "
        "1,800/1,200/600 MW with the MEASURED as-enforced hourly requirement "
        "series from ISO Express 'Hourly Reserve Requirements' (system ROS "
        "row; the measured 30-min total exceeds the static 1,800 MW in every "
        "2023-2025 hour, peaking 3,167 MW in the Jan-2025 cold snap). A "
        "market-design input (rule 13); measured reserve PRICES stay "
        "validation-only. Hard-errors when the clean series is absent; "
        "mutually exclusive with the post-solve RCPF overlay (rule 19). "
        "Requires --energy-reserve-coopt; NEISO-only. Default (unset) keeps "
        "the base config value (off).",
    )
    parser.add_argument(
        "--miso-firm-imports",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Manitoba Hydro firm-hydro import block: add ~10-15 TWh/yr of FIRM "
        "contracted hydro into MISO-North as a SEPARATE import block priced as "
        "firm hydro (a low, near-constant offer reflecting the contract), "
        "OUTSIDE the gas-margin reference-price seam. Manitoba is MISO's single "
        "largest import source and the structural reason MISO is a net importer. "
        "The block lands directly in MISO-North and is floored as must-flow firm "
        "baseload. Forward-reproducible (the contract regenerates for any year), "
        "NOT fitted to the net-interchange residual. Requires --priced-interchange. "
        "MISO-only. Default (unset) = the per-ISO default (ON for MISO via "
        "constants.resolve_miso_firm_imports).",
    )
    parser.add_argument(
        "--miso-seam-flow-limit",
        action="store_true",
        help="MISO reference-price seam deliverability cap: bound each seam's "
        "(PJM/SPP/South) import-band availability at the MEASURED EIA-930 "
        "BA-to-BA net-import envelope (per (month x hour-of-day) p90 of the "
        "directed flow over the seam's DIBAs). Fixes the structural over-import: "
        "the priced seam imports at the interface limit on all three borders, but "
        "MISO only net-imports over the eastern PJM seam — it nets ~0 over SPP and "
        "net-EXPORTS over the southern TVA-dominated seam. The one-sided import "
        "cap clips SPP/South toward ~0 import while export bands keep their priced "
        "economics. A transfer-capability proxy from the directed-flow series, "
        "reproducible for a forward year and flow-responsive, NOT fitted to the "
        "net-MWh residual. Requires --reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-seam-flow-percentile",
        type=float,
        default=None,
        help="Override the per-seam import deliverability percentile used by "
        "--miso-seam-flow-limit (default keeps p90). Raising it (e.g. 95) lifts "
        "the deliverability envelope toward the measured upper-tail transfer so "
        "the priced seam clears MORE import in tight hours — the round-2 "
        "import-lift knob for the 2024/2025 structural under-import. Still a "
        "measured-duration-curve ceiling, NOT a flow pinned to the net-MWh "
        "residual; only bites with --miso-seam-flow-limit. MISO-only.",
    )
    parser.add_argument(
        "--miso-seam-export-limit",
        action="store_true",
        help="MISO reference-price seam EXPORT cap — the symmetric mirror of "
        "--miso-seam-flow-limit. Bound each seam's (PJM/SPP/South) net EXPORT at "
        "the MEASURED EIA-930 BA-to-BA net-export envelope (per (month x hour-of-"
        "day) p90 of the directed flow). Fixes the structural over-export: the "
        "priced seam exports cheap MISO coal back over every border whenever a "
        "neighbor's price exceeds MISO's, but MISO reliably net-IMPORTS over the "
        "eastern PJM seam and cannot net-export there. Raising the export bands' "
        "lower bound clips the PJM seam toward ~0 export while SPP/South keep "
        "their measured export headroom. A transfer-capability proxy from the "
        "directed-flow series, reproducible for a forward year and flow-"
        "responsive, NOT fitted to the net-MWh residual. Shares "
        "--miso-seam-flow-percentile with the import cap. Requires "
        "--reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-seam-envelope-merit-cap",
        action="store_true",
        help="MISO seam envelope COMPOSITION fix (miso-73, G-23 residual root "
        "cause): apply the measured (month x hour-of-day) deliverability "
        "envelope with MERIT-ORDER (waterfall) band bounds — band k keeps "
        "clip(cap - (k-1)*step, 0, step), cheap base rungs full-width, seam "
        "total capped at min(cap, limit) exactly — instead of the uniform "
        "per-band derate under which the seam reaches its cap only when the "
        "price clears the MOST EXPENSIVE Q-Q rung (measured suppression: PJM "
        "imports -5.6/-8.3/-8.9 TWh, South exports +2.8/+2.6/+3.1 TWh vs "
        "ceiling semantics, 2023/24/25). Zero new parameters; envelope values, "
        "percentile, ladder rungs and band grid byte-unchanged. Only bites "
        "with --miso-seam-flow-limit / --miso-seam-export-limit. See "
        "docs/handoffs/miso-g23-seam-envelope-composition-design-2026-07.md.",
    )
    parser.add_argument(
        "--miso-import-sil-measured-envelope",
        action="store_true",
        help="MISO aggregate simultaneous-transfer limit (miso-255, rule 14 "
        "[R-ACCURATE]): REPLACE the 8,700 MW bidirectional "
        "MISO_simultaneous_import scalar with MISO's own MEASURED coincident "
        "boundary transfer envelope, per direction. The scalar is MISO's "
        "published CAPACITY IMPORT LIMIT, a PRA/LOLE resource-adequacy "
        "accreditation construct, applied as the HOURLY energy bound in BOTH "
        "directions; the meter falsifies it both ways (net import exceeds it "
        "in 583/106/69/118/4/14 h of 2020-2025; net export has never reached "
        "it, deepest -5,415 MW). With the priced seam wanting import in nearly "
        "every hour the scalar becomes the schedule: the model rails it for "
        "3,730/8,650/2,609/3/0/0 h of 2020-2025. Zero new parameters -- same "
        "estimator, percentile and hour key as the per-seam envelopes, "
        "aggregated coincidently. REPLACES the scalar, never stacks (rule 19). "
        "MISO-only and inert where no envelope resolves, so every other ISO "
        "and every forecast year is byte-identical. Default off.",
    )
    parser.add_argument(
        "--miso-seam-envelope-hour-ending-key",
        action="store_true",
        help="MISO seam envelope HOUR-KEY repair (miso-175, rule 14): read the "
        "EIA-930 DIBA local_time stamp as hour-ENDING on MISO's local standard "
        "clock — its measured convention, solved at r = 1.0000 against the "
        "independently-keyed BALANCE TI series — when bucketing the seam "
        "deliverability envelopes, so the (month x hour-of-day) cap applied at "
        "model hour h is built from the measured population of hour h instead "
        "of hour h-1 (the legacy raw-stamp key rotates the whole diurnal cap "
        "profile +1 h; measured mean |Δ| ~241 MW on the PJM seam, annual mean "
        "level unchanged). Pure key repair, zero new parameters; the same "
        "conversion the seam LADDER derivation already applies to the same "
        "parquet. Affects both directions; only bites with "
        "--miso-seam-flow-limit / --miso-seam-export-limit. MISO-only.",
    )
    parser.add_argument(
        "--pjm-seam-flow-limit",
        action="store_true",
        help="PJM reference-price seam deliverability cap: bound each of PJM's "
        "5 seams' (MISO/NYISO/Carolinas/TVA/LGEE) import-band availability at "
        "the MEASURED PJM tie-line per-neighbor net-import envelope (border "
        "zones summed to neighbor level, per (month x hour-of-day) p90). Fixes "
        "the structural over-export: the model exports ~38 TWh every year at "
        "full TTC on all 5 seams, but the actual net export drops from 40 to "
        "18 TWh 2023-2025. A transfer-capability proxy from the measured "
        "tie-line series, forward-reproducible, NOT fitted to the net-MWh "
        "residual. Requires --reference-price-interface; PJM-only.",
    )
    parser.add_argument(
        "--pjm-seam-flow-percentile",
        type=float,
        default=None,
        help="Override the per-seam deliverability percentile used by "
        "--pjm-seam-flow-limit (default keeps p90). Raising it lifts the "
        "deliverability envelope so the LP clears more flow in tight hours. "
        "Still a measured-duration-curve ceiling, NOT a flow pinned to the "
        "net-MWh residual; only bites with --pjm-seam-flow-limit. PJM-only.",
    )
    parser.add_argument(
        "--pjm-seam-export-limit",
        action="store_true",
        help="PJM reference-price seam EXPORT cap — the symmetric mirror of "
        "--pjm-seam-flow-limit. Bound each seam's net EXPORT at the measured "
        "PJM tie-line per-neighbor net-export envelope. Raises each neighbor's "
        "export bands' lower bound toward 0 so the LP's deliverable net export "
        "is capped at the measured per-neighbor capability. Shares "
        "--pjm-seam-flow-percentile with the import cap. Requires "
        "--reference-price-interface; PJM-only.",
    )
    parser.add_argument(
        "--pjm-seam-measured-ladder",
        action="store_true",
        help="Price every PJM seam band (MISO/NYISO/Carolinas/TVA/LGEE, "
        "import + export) at the MEASURED per-year Q-Q band ladder "
        "(interchange_config.PJM_SEAM_LADDER_BY_YEAR, derived by "
        "scripts/data/derive_pjm_seam_ladders.py: PJM settlement-grade tie-line "
        "flow duration curves quantile-coupled with the measured PJM DA "
        "system LMP — the MISO --miso-seam-measured-ladder / NEISO "
        "audit-C-6 pattern), replacing the gas x HR x load-shape band "
        "prices + hurdle for backcast years. Fixes the pjm-95 2023 "
        "interchange duration miss: the measured PJM interchange is "
        "direction-structural (export to MISO/NYISO ~97-100 percent of "
        "hours, import from Carolinas/TVA/LGEE 77-97 percent — firm PTP "
        "schedules revealed only statistically), which spot-spread pricing "
        "inverts (model imports 46 percent of 2023 hours vs measured ~2, "
        "displacing CC_REGULAR dispatch). Bands still clear economically "
        "on the model's own hourly price; envelopes and band capacities "
        "unchanged. DISPLACES the firm scheduled-export floor on ladder "
        "years (alternatives, never stacked). Requires "
        "--reference-price-interface; PJM-only.",
    )
    parser.add_argument(
        "--pjm-seam-neighbour-hourly-ladder",
        action="store_true",
        help="pjm-174. Make the PJM seam ladder HOURLY on the seams a measured "
        "neighbour price covers: band k's offer becomes neighbour(t) + "
        "offset_k, so it clears on the seam SPREAD rather than on PJM's "
        "absolute price level "
        "(interchange_config.PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR, derived "
        "by scripts/data/derive_pjm_seam_ladders.py --neighbour-hourly on the "
        "IDENTICAL Q-Q duration coupling read off the spread; zero fitted "
        "parameters). A SUB-GATE of --pjm-seam-measured-ladder, refused "
        "without it; it DISPLACES the parent's scalar band price on the seams "
        "it covers and degrades to the parent elsewhere (rule 19). Repairs the "
        "own-hub anchoring pjm-174 measured: the parent reproduces its own "
        "basis to 0.05 TWh but loses 5.7 (2022) / 12.7 (2021) TWh of net "
        "export when fed the model's own price. MISO/NYISO only "
        "(SERC publishes no hub); default off, byte-identical off.",
    )
    parser.add_argument(
        "--pjm-measured-interface-limits",
        action="store_true",
        help="Backcast overlay (PJM-only, default off): the internal links "
        "whose static ttc_mw was seeded from the PJM Data Miner 2 "
        "transfer-limit postings follow the measured HOURLY published "
        "series (transfer-interface-limits clean datatype; "
        "constants.PJM_INTERFACE_LINK_MAP — AEP/DOM, AP-South, "
        "Bedington-BlackOak min(pre,post), and the Average West/Central/"
        "Eastern interfaces) in the forward west->east direction, static "
        "rating kept on the reverse. Supersedes pjm_congestion's static "
        "medians on mapped links (same feed, hourly). The ERCOT "
        "--ercot-gtc-limits-measured pattern; forecast years keep the "
        "static seeds. Run scripts/data/curate_transfer_interface_limits.py "
        "first.",
    )
    parser.add_argument(
        "--miso-pjm-border-anchor",
        action="store_true",
        help="Re-anchor the MISO eastern PJM seam from PJM's SYSTEM-average "
        "realized LMP to its MISO-facing WESTERN border hubs (ComEd / AEP-Ohio / "
        "ATSI; constants.MISO_PJM_BORDER_HR_BY_YEAR). The import mirror of the "
        "pjm58 NYISO-WEST re-anchor: the MISO-Central seam clears against western "
        "PJM, which prices below the eastern-load-weighted system average, so the "
        "system anchor over-prices the import and MISO under-imports over its "
        "largest seam (2024 -15 vs measured -23, 2025 -3 vs -19 TWh). The per-year "
        "border HR is system_HR x (mean border-hub LMP / system LMP); the discount "
        "deepens in tight years so 2023 (already matched) barely moves while "
        "2024/2025 clear more import up to the measured deliverability cap. "
        "Measured neighbor price-formation (rule #12), blind to MISO's flow "
        "(rule #11). Requires --reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-cc-coal-rebalance",
        action="store_true",
        help="MISO CC_REGULAR / COAL_BIT offer-curve rebalance: raise the MISO "
        "combined-cycle committed/econ-high bands and the bituminous-coal "
        "econ-high band so the MARGINAL CC / coal-bit MWh sits ABOVE the "
        "priced-import hurdle (and the under-running CT_PEAKER / ST_GAS), rather "
        "than being the cheapest fill. Structural correction for the round-2 "
        "conservation-of-energy miss (imports too low -> cheap domestic CC/coal "
        "over-run and price out the peakers/steam). An offer-SHAPE correction, "
        "ISO-gated to MISO (other ISOs / forecasts byte-identical), validated by "
        "the import-up / CC-down / coal-down / CT-up / ST-up response.",
    )
    parser.add_argument(
        "--miso-firm-import-floor",
        action="store_true",
        help="Firm (must-flow) import floor on the reference-price seam — the "
        "import-direction mirror of the PJM firm-export floor and the Manitoba/HQ "
        "firm-import blocks. MISO net-imports from the PJM seam (PJM + IESO/"
        "Ontario) in ~99-100%% of hours at a stable multi-GW base (cheap Ontario "
        "nuclear/hydro surplus + firm PJM-east scheduled transfers) that flows "
        "regardless of the hourly spread, but the gas x heat-rate economic seam "
        "prices the PJM border above MISO's cheap coal and so wrongly net-EXPORTS "
        "over it (the 2024 -8.3 vs -23.1 net-import miss, the 2025 +18 vs -19 sign "
        "flip, and the 2025 +20 TWh energy-balance overshoot). Forces the cheapest "
        "import tranches on at the measured firm base "
        "(NeighborInterface.firm_import_floor_by_year, p10 of the seam's net "
        "import) so the inframarginal must-flow import displaces the over-running "
        "domestic coal/CC, the economic tranches clearing on top. Requires "
        "--reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-pjm-lmp-import-pricing",
        action="store_true",
        help="Price each PJM import/export tranche on MISO's reference-price "
        "seam at the MEASURED hourly PJM Day-Ahead LMP at the MISO-facing "
        "western border hubs (equal-weight mean of CHICAGO GEN / AEP GEN / "
        "ATSI GEN) + hurdle, replacing the synthetic gas x heat-rate x "
        "load-shape ladder. The gas x HR ladder is too FLAT: its off-peak "
        "price never dips below MISO's own cheap coal, so the model wrongly "
        "under-imports in 2024/2025. The real PJM border LMP dips well below "
        "the flat gas x HR average in off-peak hours, pulling import into "
        "those cheap hours. DISPLACES miso_pjm_border_anchor for the PJM "
        "seam (the two are alternatives; don't stack). SPP/South seams keep "
        "their gas x HR pricing. Measured neighbor price-formation "
        "(rule #12), blind to MISO's flow (rule #11). Requires "
        "--reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-seam-measured-ladder",
        action="store_true",
        help="Price every MISO seam band (PJM/SPP/South, import + export) at "
        "the MEASURED per-year Q-Q band ladder "
        "(interchange_config.MISO_SEAM_LADDER_BY_YEAR, derived by "
        "scripts/data/derive_miso_seam_ladders.py: EIA-930 per-seam flow duration "
        "curves quantile-coupled with the measured MISO DA hub LMP — the "
        "NEISO audit-C-6 measured-ladder pattern), replacing the gas x HR x "
        "load-shape band prices + hurdle for backcast years. Fixes the G-23 "
        "2025 import starvation: the measured PJM+IESO seam is a "
        "firm/scheduled base flowing in ~98-100 percent of hours "
        "uncorrelated with the hourly spread, which spot-spread pricing "
        "structurally deletes in a zero-spread year. Bands still clear "
        "economically on the model's own hourly price; envelopes and band "
        "capacities unchanged. DISPLACES --miso-pjm-border-anchor / "
        "--miso-pjm-lmp-import-pricing on the rows it prices (alternatives, "
        "never stacked; this overwrite runs last). Requires "
        "--reference-price-interface; MISO-only.",
    )
    parser.add_argument(
        "--miso-zonal-gas-basis",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Shift each MISO gas unit's fuel price by its zone's measured "
        "regional gas basis vs Henry Hub (data/raw/miso_zonal_gas_hub.csv). "
        "MISO-North on MidCon/Northern Natural (IA), Central on Chicago "
        "Citygate (IL), South on Gulf Coast (LA). Capacity-weighted "
        "mean-zero (fleet-aggregate gas level preserved). MISO-only.",
    )
    parser.add_argument(
        "--miso-winter-citygate-daily",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="MISO winter fuel security (miso-72): in Dec/Jan/Feb, reprice the "
        "Chicago-hub zones' gas units (MISO-Illinois/Indiana/East) at the "
        "measured Chicago Citygate daily shape (data/raw/gas-prices/"
        "miso_citygate_daily.csv), flow-date-placed and mean-preserving, "
        "superseding the national HH gas_daily_shape in those cells. Closes "
        "the Jan-14-17-2024 Winter Storm Heather gas tail. MISO-only.",
    )
    parser.add_argument(
        "--gas-hub-basis-overlay",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Reprice gas at the measured trading-hub spot (Henry Hub month + "
        "the ISO's citygate basis from data/raw/gas_basis_by_iso_month.csv) "
        "instead of the EIA-923 ISO-month DELIVERED cost. The marginal "
        "commodity a dispatched CC bids is the hub spot; the firm pipeline "
        "reservation in the delivered cost is sunk (DIAGNOSIS-caiso-import-"
        "ladder-2026-06-19 lever B). The citygate basis for all ISOs is "
        "refreshed by the fetch-eia-gas-prices workflow. On by default only "
        "for NEISO (the keeper); use this to validate CAISO (or others) once "
        "the fetched citygate basis lands — it is a keeper-changing run, so "
        "validate before flipping the backcast_config default. No-op "
        "(byte-identical) for any ISO/year with no basis rows.",
    )
    parser.add_argument(
        "--caiso-gas-floor-frac",
        type=float,
        default=None,
        help="Fraction of the measured EIA-930 NG: NG (month x hour-of-day "
        "median) the --caiso-gas-commitment-floor targets. Default (unset) "
        "keeps the base config value (0.80 for CAISO = EIA-923 gas / "
        "EIA-930 NG: NG, stripping geo+bio). Lower keeps modeled gas TWh "
        "nearer EIA-923 — forcing commitment can inflate gas, and the "
        "surplus must export/curtail, not pad the mix.",
    )
    parser.add_argument(
        "--btm-backfill-year",
        type=int,
        default=None,
        help="Carry a plant's behind-the-meter (must-run share) EIA-923 "
        "class netgen from this prior year when the backcast year's "
        "923 vintage has no row for the plant AND CAMPD shows it "
        "generating — the early monthly-survey-only 923 release "
        "otherwise zeroes the model-side add-back while the class "
        "benchmark keeps the plant via the CAMPD backfill (e.g. San "
        "Jacinto 7325 in 2025). Unset (default) changes no existing "
        "run.",
    )
    parser.add_argument(
        "--mass-cap-enabled",
        action="store_true",
        help="Thread the unified carbon resolver's power-sector mass-cap "
        "ROW (policy.cap_and_trade.resolve_carbon_program) into every "
        "solved year instead of the default measured-price adder (G-29, "
        "docs/handoffs/emissions-mass-cap-plan-2026-07.md); mirrors "
        "run_calibration.py's own --mass-cap-enabled. Diagnostic-only "
        "(e.g. the RGGI dual-vs-auction-price validation probe); never a "
        "keeper default. No effect on ISOs with no cap-and-trade program "
        "or no published budget for a requested year.",
    )
    parser.add_argument(
        "--mass-cap-tons",
        type=float,
        default=None,
        help="Explicit annual mass-cap budget (metric tons CO2), overriding "
        "the ISO program's published schedule. Only meaningful with "
        "--mass-cap-enabled.",
    )
    parser.add_argument(
        "--mass-cap-program",
        default=None,
        help="Label override for the mass-cap row's reported allowance "
        "price. Only meaningful with --mass-cap-enabled.",
    )
    parser.add_argument(
        "--offer-curve-delta-json",
        default=None,
        metavar="JSON",
        help="Like --offer-curve-json but each value is ADDED to the current "
        "band rather than replacing it, so a re-tune need not restate the "
        "prior absolute. Same shape (class -> band -> number); the number "
        'is a signed delta. E.g. \'{"CT_PEAKER":{"committed":0.05},'
        '"COAL_PRB":{"committed":-0.05}}\' nudges committed +0.05 / -0.05. '
        "Applied on top of --offer-curve-json when both are given. The "
        "resolved absolute curve is recorded in run_config.json.",
    )
    parser.add_argument(
        "--miso-coal-night-floor",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MISO P1-native regulated-coal WITHIN-RUN NIGHT floor (miso-113): "
        "hold each regulated PRB/subbituminous plant at its OWN measured "
        "within-run night level (night_p50, frozen artifact "
        "coal_prb_committed_split_MISO.csv) over the P0-detected committed "
        "run, NET of that plant's own _mustrun band so the plant total is "
        "exactly night_p50 x capacity and never mustrun + night (rule 19). "
        "The successor to the rejected offer-side arms "
        "coal_prb_committed_dispatchable (miso-111) and "
        "coal_prb_committed_split (miso-112) - a floor, not a second price.",
    )
    parser.add_argument(
        "--nyiso-gas-commitment-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="NYISO P1-native gas commitment bridge (nyiso-87): hold the "
        "merchant slow-start gas fleet (CC_REGULAR + ST_GAS, by unit physics) "
        "at measured minimum stable load across idle gaps its own commitment "
        "physics says it cannot cycle through. The REPLACEMENT for the h14-21 "
        "peak-window reliability floors (owner directive 2026-07-27) - run it "
        "WITH those limbs disabled via --reliability-floor-overrides, never "
        "stacked on them (rule 19).",
    )
    parser.add_argument(
        "--spp-gas-commitment-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="SPP P1-native gas commitment bridge (SPP-44): hold SPP's merchant "
        "slow-start gas fleet (CC_REGULAR + ST_GAS by unit physics; the CT "
        "classes fail on their own 1 h min-down) at its MEASURED plant-basis "
        "minimum stable load (constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC: CC 0.209 "
        "/ ST_GAS 0.090, CAMPD 2023-2025) across P0 idle gaps its own "
        "commitment physics says it cannot cycle through, with the measured "
        "minimum-run extension (15 / 5 h) and the commitment-real run screen. "
        "Rule 19: SPP's gas classes carry no other floor, so nothing is "
        "stacked or replaced. Default off (byte-identical).",
    )
    parser.add_argument(
        "--soco-gas-st-campaign-commitment",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="SOCO P1-native gas-steam CAMPAIGN commitment floor (SOCO-53d): "
        "hold SOCO's campaign-duty gas boilers at their OWN measured "
        "plant-basis minimum stable load through the campaigns the model's own "
        "P0 pattern starts, using the measured minimum-run extension and the "
        "online-hours LSL state floor. The restart legs are NOT armed - SOCO's "
        "boilers do not two-shift (98.6 %% of their downtime-hours sit in gaps "
        "longer than 72 h), which is why gas_commitment_bridge is recorded R "
        "for this ISO. Level, horizon and membership are per-plant measured "
        "rows of campd_gas_st_campaign_params_SOCO.csv (rules 21/23/25); a "
        "plant synchronized less than half the year is standby iron and is "
        "never floored (rule 17). Rule 19: SOCO's gas and coal classes carry "
        "no other floor, so nothing is stacked or replaced. Default off "
        "(byte-identical).",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-cc-min-load-frac",
        type=float,
        default=None,
        help="Override the measured CC_REGULAR minimum-load fraction "
        "(default 0.523, CAMPD 2023-2025 capacity-weighted p50). Probe only - "
        "a keeper must cite the derive artifact (rule 23).",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-st-min-load-frac",
        type=float,
        default=None,
        help="Override the measured ST_GAS minimum-load fraction "
        "(default 0.239, same artifact). Probe only.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-startup",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Economic (>= min-down) bridging on the startup-restart "
        "inequality. Default on with the bridge; --no-... is the "
        "physical-restart-bar-only arm.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-da-horizon",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Cap economic bridges at one DA operating day (24 h). Default on.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-plant-exclusions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MEMBERSHIP correction: skip plants in economic LAY-UP (median "
        "gross load zero in every year x 4-hour-block cell of 2023-2025, "
        "data/raw/_processed-legacy/campd_bridge_layup_exclusions_NYISO.csv). "
        "The bridge's half of the correction that previously existed only on "
        "the reliability floor (--reliability-floor-plant-exclusions).",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-reserve-duty-exclusions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MEMBERSHIP correction, reserve-duty channel (nyiso-152): also "
        "skip plants in the measured capacity-only CC cohort "
        "(data/raw/_processed-legacy/reserve_duty_cc_NYISO.csv, pooled "
        "online-share/CF <= 0.1). Reaches the CEMS-invisible plants the "
        "CAMPD lay-up criterion cannot test (rule 17 [R-FLOOR-WINDOW]).",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-plant-min-run",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="PER-PLANT minimum-run identification (nyiso-146): fill each "
        "slow-start row's minimum-run duration from its own plant's measured "
        "CAMPD run-length p25 "
        "(data/raw/_processed-legacy/campd_perplant_min_run_NYISO.csv), "
        "replacing the per-class scalar for covered plants; uncovered plants "
        "keep the class fallback.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-online-hours",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="ONLINE-HOURS LSL floor (the ercot141 detector leg, NYISO leg — "
        "nyiso-146 successor): floor the base tranche at measured min-load in "
        "EVERY hour the P0 pattern has the plant online, not only across idle "
        "gaps. Same detector, same measured fractions, same D-2 id.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-state-floor-min-run",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="DUTY SCOPING for the online-hours state floor: hold it only for "
        "plants whose measured run-length p25 clears the population gap "
        "(constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS; membership from "
        "campd_perplant_min_run_NYISO.csv). Requires "
        "--nyiso-gas-bridge-online-hours.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-startup-aware",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="COMMITMENT-REAL RUN SCREEN for the NYISO bridge (nyiso-200; the "
        "detector's G-61 path (b) leg): a detected P0 run anchors the min-run "
        "extension / online-hours floor / gap bridges only when its P0 energy "
        "margin per MW repays the unit's own published startup cost "
        "(_ra_bridge_unit_params). Zero new parameters; removes the "
        "P0-pattern dependence nyiso-199 measured.",
    )
    parser.add_argument(
        "--nyiso-chp-btm-measured",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Measured NYISO CHP behind-the-meter electric share (nyiso-147): "
        "replace the sector-keyed CHP_BTM_PCT_BY_SECTOR default with the "
        "plant's own Gold-Book/EIA-923 grid-delivery share "
        "(chp_btm_share_measured_NYISO.csv) in the fleet capacity carve, the "
        "BTM add-back and the benchmark classFull subtrahend.",
    )
    parser.add_argument(
        "--chp-layup-duty-split",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CHP LAY-UP duty split (nyiso-148): route the measured laid-up "
        "cogeneration cohort (chp_layup_census_<ISO>.csv — median gross load "
        "zero in every (year, 4h block) cell AND a non-degenerate CAMPD "
        "series) to the class offer curve's peak band. The cogeneration "
        "sibling of --cc-reserve-duty-split, disjoint from it by class scope; "
        "zero new scalars.",
    )
    parser.add_argument(
        "--chp-layup-duty-curve",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="CHP LAY-UP duty CURVE (nyiso-149): the GRADED successor to "
        "--chp-layup-duty-split (rejected nyiso-148 — bang-bang where the "
        "meters are graded). Each frozen-census plant offers its measured "
        "price-conditional duty (chp_duty_curve_<ISO>.csv: pct_econ at the "
        "class econ band, pct_peak at the class peak band, derived from "
        "CAMPD on-share x loading conditional on envelope-live hours) and "
        "WITHHOLDS the remainder from energy and reserves. Mutually "
        "exclusive with --chp-layup-duty-split (rule 19); zero new price "
        "constants.",
    )
    parser.add_argument(
        "--measured-ct-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MEASURED CT_PEAKER loaded heat rates (nyiso-89; wired to this "
        "orchestrator by soco-53). A CT_PEAKER generator whose plant the "
        "committed artifact covers (campd_ct_heat_rates_<ISO>.csv, "
        "scripts/data/derive_campd_ct_heat_rates.py) takes its plant's "
        "CAMPD-measured LOADED heat rate (MMBtu per net MWh, pooled over "
        "unitType == 'Combustion turbine' hours at load) ahead of the eGRID "
        "plant-average ANNUAL rate. eGRID publishes ONE rate per plant, so a "
        "mixed facility's turbines inherit its steam boilers' rate; the error "
        "is source noise in BOTH directions, so no multiplier substitutes for "
        "the measurement (rule 14 [R-ACCURATE]). Applied per generator by "
        "class, so only the turbines of a mixed plant are repriced. Zero "
        "fitted parameters; no-op for an ISO with no artifact. The field and "
        "its consumer predate this flag — ScenarioConfig.measured_ct_heat_rates "
        "was reachable only by constructing a config directly, so no run "
        "driven by this orchestrator could arm it.",
    )
    parser.add_argument(
        "--measured-coal-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MEASURED COAL steady-state operating heat rates (nwpp-42). A "
        "COAL generator whose plant the committed artifact covers "
        "(campd_coal_heat_rates_<ISO>.csv, "
        "scripts/data/derive_campd_coal_heat_rates.py) takes its plant's "
        "CAMPD-measured OPERATING heat rate (MMBtu per net MWh, pooled over "
        "the units whose primaryFuelInfo is a coal, on hours with opTime >= "
        "0.99) ahead of the eGRID plant-average ANNUAL rate. The coal sibling "
        "of --measured-ct-heat-rates, on the identical seam and artifact "
        "schema. eGRID's annual average folds startup fuel, shutdown tails "
        "and the offline hours' fuel into the number that sets the plant's "
        "offer, and its level moves with the plant's capacity factor in the "
        "vintage year; the error is per-plant source noise, not a uniform "
        "bias, so no multiplier substitutes for the measurement (rule 14 "
        "[R-ACCURATE]). Applied per generator by class, so a coal site's "
        "gas-converted boilers are untouched. Zero fitted parameters; no-op "
        "for an ISO with no artifact.",
    )
    parser.add_argument(
        "--measured-st-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MEASURED ST_GAS steady-state operating heat rates (soco-53e). An "
        "ST_GAS generator whose plant the committed artifact covers "
        "(campd_st_heat_rates_<ISO>.csv, "
        "scripts/data/derive_campd_gas_st_heat_rates.py) takes its plant's "
        "CAMPD-measured OPERATING heat rate (MMBtu per net MWh, pooled over "
        "the plant's own boiler units, on hours with opTime >= 0.99) ahead of "
        "the eGRID plant-average ANNUAL rate. The gas-steam sibling of "
        "--measured-ct-heat-rates and --measured-coal-heat-rates, on the "
        "identical seam and artifact schema. Both of their reasons apply, plus "
        "one only a per-UNIT meter can reach: a mixed coal/gas STEAM station "
        "sits behind one ORIS code and both boilers are prime mover ST, so the "
        "plant rate AND the prime-mover-family rate blend them (SOCO's "
        "E C Gaston: an 832 MW coal boiler blended with four ~255 MW gas "
        "boilers). The error is per-plant, not a bias -- SOCO measures -0.476 "
        "at Gaston and +1.374 at Barry -- so no multiplier substitutes for the "
        "measurement (rule 14 [R-ACCURATE]). Applied per generator by class, "
        "so the coal boiler beside it is untouched. Zero fitted parameters; "
        "no-op for an ISO with no artifact.",
    )
    parser.add_argument(
        "--egrid-identity-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="eGRID IDENTITY-RECONCILED heat rates (nyiso-151): a CAMPD-less "
        "fossil plant whose measured eGRID history lives under a DIFFERENT "
        "ORISPL (a proven two-registry identity split, e.g. Allegany EIA "
        "7784 <-> eGRID 10619) takes its pooled PLHTIAN/PLNGENAN rate from "
        "the committed per-ISO artifact "
        "(egrid_identity_heat_rates_<ISO>.csv, "
        "scripts/data/derive_egrid_identity_heat_rates.py) instead of the "
        "HEAT_RATE_BINS vintage class default. Threshold-free discovery "
        "rule; zero fitted parameters; no-op for an ISO with no artifact.",
    )
    parser.add_argument(
        "--egrid-family-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="eGRID PRIME-MOVER-FAMILY heat rates (nyiso-184): at a plant "
        "hosting two or more prime-mover families (steam beside a combined "
        "cycle, e.g. Ravenswood 2500) each family takes its own eGRID "
        "UNT.HTIAN / GEN.GENNTAN rate from the same vintage the plant-grain "
        "join reads, instead of the plant blend, and the hand number in "
        "fleet.models.MIXED_FACILITY_STEAM_HR is skipped there. Committed "
        "per-ISO artifact egrid_family_heat_rates_<ISO>.csv "
        "(scripts/data/derive_egrid_family_heat_rates.py); zero fitted "
        "parameters; no-op for an ISO with no artifact. Composes with "
        "--replay-bundle.",
    )
    parser.add_argument(
        "--egrid-steam-collapse-heat-rates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="eGRID STEAM-COLLAPSE identity heat rates (nyiso-189, owner ruling "
        "2026-09-05 form B2): a combined cycle whose eGRID steam-generator "
        "filing collapsed in the applied vintage (the CA generator at exactly "
        "zero net generation while the CTs run, or a steam share below the "
        "plant's own T1-clean record by more than the record's range, with the "
        "heat per CT-MWh inside that record) takes the CT-heat identity "
        "PLHTIAN / sum GENNTAN(CT) / (1 + the plant's own median steam share) "
        "instead of the inflated plant-grain PLHTRT (Bethlehem 2539: 9.665 -> "
        "6.877). Committed per-ISO artifact egrid_steam_collapse_heat_rates_"
        "<ISO>.csv (scripts/data/derive_egrid_steam_collapse_heat_rates.py); "
        "zero fitted parameters; no-op for an ISO with no artifact. Composes "
        "with --replay-bundle.",
    )
    parser.add_argument(
        "--cc-reserve-duty-split",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="RESERVE-DUTY CC offer split (nyiso-146): route the measured "
        "capacity-only CC cohort (reserve_duty_cc_<ISO>.csv, on-share/CF <= "
        "0.10 population-gap ceiling) to the class offer curve's peak band — "
        "the duty-role mirror of --cc-intermediate-split; zero new scalars.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-min-run",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="MINIMUM RUN DURATION extension: extend a detected P0 run shorter "
        "than the unit's minimum run and floor the extension at minimum stable "
        "load. Values from the published class table unless the two "
        "--nyiso-gas-bridge-*-min-run-hours flags override.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-cc-min-run-hours",
        type=float,
        default=None,
        help="Minimum run hours for bridged CC_REGULAR (default: class table, "
        "5-10 h). Measured CAMPD capacity-weighted p25/p50/p75 = 11/21/133 h.",
    )
    parser.add_argument(
        "--nyiso-gas-bridge-st-min-run-hours",
        type=float,
        default=None,
        help="Minimum run hours for bridged ST_GAS (default: class table, "
        "24-48 h). Measured CAMPD capacity-weighted p25/p50/p75 = 3/13/89 h.",
    )
    parser.add_argument(
        "--reliability-floor-overrides",
        default=None,
        metavar="JSON",
        help="Per-limb reliability-floor overrides applied to "
        "RELIABILITY_FLOOR_REGISTRY[iso] at run time (the existing registry "
        "field ScenarioConfig.reliability_floor_overrides, so the value lands "
        "in run_config.json — rule 24). Keyed "
        '"<ZONE>:<CLASS>:<driver>" or, to select ONE ramp family within a '
        '(zone, class, driver), "<ZONE>:<CLASS>:<driver>:<ramp_group>" '
        '("_none" selects the limbs with no ramp group). Value: '
        '{"enabled"?: bool, "floor_pct"?: float, "threshold"?: float}. '
        'e.g. \'{"NYC:ST_GAS:tmax:NYC_ST_ev": {"enabled": false}}\' turns the '
        "h14-21 evening ramp off while leaving the persistent 24 h base on.",
    )
    parser.add_argument(
        "--class-commitment-overrides",
        default=None,
        metavar="JSON",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        # Per-class P2 commitment-screen overrides, keyed by plant_group (e.g.
        # '{"ST_GAS":{"min_run_hours":48,"min_down_hours":12}}').
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-container-preflight",
        action="store_true",
        help="Skip the container preflight (scripts/lib/solve_container.py): "
        "the binding-cgroup memory ceiling read, the swapfile provisioning up "
        "to 24 GiB, and the single-thread solve-profile pins. On by default "
        "because a per-plant MISO/PJM year exceeds the 13.34 GiB CCR bash "
        "cgroup and is OOM-killed without swap. Does not change the LP.",
    )
    args = parser.parse_args()
    apply_statistical_mode(args)
    _enforce_legacy_p2_gate(parser, args)
    if args.no_container_preflight:
        global CONTAINER_PREFLIGHT_ENABLED
        CONTAINER_PREFLIGHT_ENABLED = False

    offer_curve_overrides = _parse_offer_curve_json(args.offer_curve_json)
    offer_curve_deltas = _parse_offer_curve_json(
        args.offer_curve_delta_json, flag="--offer-curve-delta-json"
    )
    class_commitment_overrides = None
    if args.class_commitment_overrides:
        import json as _json

        class_commitment_overrides = _json.loads(args.class_commitment_overrides)

    reliability_floor_overrides = None
    if args.reliability_floor_overrides:
        import json as _json

        reliability_floor_overrides = _json.loads(args.reliability_floor_overrides)

    if args.report:
        report_run(Path(args.report), band_width=args.cf_band_width)
        return

    if args.rebuild_benchmark:
        rebuild_benchmark(Path(args.rebuild_benchmark))
        return

    if args.run_p2:
        run_p2_layer(Path(args.run_p2), screen_coal=not args.no_coal_p2)
        return

    if args.replay_bundle:
        run_replay_bundle(
            Path(args.replay_bundle),
            out_dir=Path(args.out_dir) if args.out_dir else None,
            years=args.year if "--year" in sys.argv else None,
            note=args.note,
            zero_forcing_ablation=args.zero_forcing_ablation,
            reliability_floor_plant_exclusions=(
                args.reliability_floor_plant_exclusions
            ),
            caiso_offer_surface_measured_ungrounded=(
                args.caiso_offer_surface_measured_ungrounded
                if "--caiso-offer-surface-measured-ungrounded" in sys.argv
                else None
            ),
            caiso_st_gas_committed_measured=(
                args.caiso_st_gas_committed_measured
                if "--caiso-st-gas-committed-measured" in sys.argv
                or "--no-caiso-st-gas-committed-measured" in sys.argv
                else None
            ),
            caiso_st_gas_peak_measured=(
                args.caiso_st_gas_peak_measured
                if "--caiso-st-gas-peak-measured" in sys.argv
                or "--no-caiso-st-gas-peak-measured" in sys.argv
                else None
            ),
            caiso_dsw_lateevening_clean=(
                args.caiso_dsw_lateevening_clean
                if "--caiso-dsw-lateevening-clean" in sys.argv
                or "--no-caiso-dsw-lateevening-clean" in sys.argv
                else None
            ),
            mustrun_chp_btm_holdout=(
                args.mustrun_chp_btm_holdout
                if "--mustrun-chp-btm-holdout" in sys.argv
                or "--no-mustrun-chp-btm-holdout" in sys.argv
                else None
            ),
            benchmark_membership_vintage_union=(
                args.benchmark_membership_vintage_union
                if "--benchmark-membership-vintage-union" in sys.argv
                or "--no-benchmark-membership-vintage-union" in sys.argv
                else None
            ),
            nyiso_ct_peaker_bands_measured=args.nyiso_ct_peaker_bands_measured,
            nyiso_ct_peaker_committed_measured=(
                args.nyiso_ct_peaker_committed_measured
            ),
            nyiso_st_gas_econ_bands_deleaked=args.nyiso_st_gas_econ_bands_deleaked,
            caiso_ct_peaker_committed_measured=(
                args.caiso_ct_peaker_committed_measured
                if "--caiso-ct-peaker-committed-measured" in sys.argv
                or "--no-caiso-ct-peaker-committed-measured" in sys.argv
                else None
            ),
            gas_offer_margin=(
                args.gas_offer_margin
                if "--gas-offer-margin" in sys.argv
                or "--no-gas-offer-margin" in sys.argv
                else None
            ),
            caiso_dsw_daytime_evening_trim=args.caiso_dsw_daytime_evening_trim,
            cc_summer_derate_reconciled_basis=args.cc_summer_derate_reconciled_basis,
            ercot_reserve_supply_cap_from_year=(
                args.ercot_reserve_supply_cap_from_year
                if "--ercot-reserve-supply-cap-from-year" in sys.argv
                else None
            ),
            ercot_load_resource_reserve_from_year=(
                args.ercot_load_resource_reserve_from_year
                if "--ercot-load-resource-reserve-from-year" in sys.argv
                else None
            ),
            nearby_fuel_price_zone_donor_guard=(
                args.nearby_fuel_price_zone_donor_guard
                if "--nearby-fuel-price-zone-donor-guard" in sys.argv
                or "--no-nearby-fuel-price-zone-donor-guard" in sys.argv
                else None
            ),
            fleet_state_from_eia860=(
                args.fleet_state_from_eia860
                if "--fleet-state-from-eia860" in sys.argv
                or "--no-fleet-state-from-eia860" in sys.argv
                else None
            ),
            caiso_citygate_spot_coverage=(
                args.caiso_citygate_spot_coverage
                if "--caiso-citygate-spot-coverage" in sys.argv
                or "--no-caiso-citygate-spot-coverage" in sys.argv
                else None
            ),
            unit_outage_mixed_gas_routing=(
                args.unit_outage_mixed_gas_routing
                if "--unit-outage-mixed-gas-routing" in sys.argv
                or "--no-unit-outage-mixed-gas-routing" in sys.argv
                else None
            ),
            campd_per_unit_attribution=(
                args.campd_per_unit_attribution
                if "--campd-per-unit-attribution" in sys.argv
                or "--no-campd-per-unit-attribution" in sys.argv
                else None
            ),
            netload_drag_layup_window_mask=args.netload_drag_layup_window_mask,
            netload_drag_merit_allocation=args.netload_drag_merit_allocation,
            netload_drag_min_run_persistence=args.netload_drag_min_run_persistence,
            vre_curtailment_oversupply_allocation=args.vre_curtailment_oversupply_allocation,
            spp_curtailment_ceiling=args.spp_curtailment_ceiling,
            spp_curtail_depth_wind=args.spp_curtail_depth_wind,
            campd_outage_merit_order_guard=(
                args.campd_outage_merit_order_guard
                if "--campd-outage-merit-order-guard" in sys.argv
                or "--no-campd-outage-merit-order-guard" in sys.argv
                else None
            ),
            egrid_family_heat_rates=(
                args.egrid_family_heat_rates
                if "--egrid-family-heat-rates" in sys.argv
                or "--no-egrid-family-heat-rates" in sys.argv
                else None
            ),
            egrid_steam_collapse_heat_rates=(
                args.egrid_steam_collapse_heat_rates
                if "--egrid-steam-collapse-heat-rates" in sys.argv
                or "--no-egrid-steam-collapse-heat-rates" in sys.argv
                else None
            ),
            unit_outage_st_capacity_basis=(
                args.unit_outage_st_capacity_basis
                if "--unit-outage-st-capacity-basis" in sys.argv
                or "--no-unit-outage-st-capacity-basis" in sys.argv
                else None
            ),
            unit_outage_per_unit_clip=(
                args.unit_outage_per_unit_clip
                if "--unit-outage-per-unit-clip" in sys.argv
                or "--no-unit-outage-per-unit-clip" in sys.argv
                else None
            ),
            unit_outage_short_windows_gas=(
                args.unit_outage_short_windows_gas
                if "--unit-outage-short-windows-gas" in sys.argv
                or "--no-unit-outage-short-windows-gas" in sys.argv
                else None
            ),
            unit_outage_window_hour_grain=(
                args.unit_outage_window_hour_grain
                if "--unit-outage-window-hour-grain" in sys.argv
                or "--no-unit-outage-window-hour-grain" in sys.argv
                else None
            ),
            enable_legacy_p2=args.enable_legacy_p2,
        )
        return

    iso = args.iso.upper()
    # Resolve the reference-price interface: explicit CLI flag OR the per-ISO
    # default-on set (MISO). Drives both the node selection and priced
    # interchange below, so MISO's plain run command activates the import node
    # without a flag while PJM/ERCOT stay byte-identical.
    reference_price_interface = resolve_reference_price_interface(
        args.reference_price_interface, iso
    )
    # Manitoba firm-hydro import block: explicit CLI flag OR the per-ISO
    # default-on set (MISO). Activates the separate firm-hydro block for the MISO
    # backcast without a flag; non-MISO ISOs are byte-identical regardless.
    miso_firm_imports = resolve_miso_firm_imports(args.miso_firm_imports, iso)
    if iso != "ERCOT":
        has_campd = bool(campd.states_for_iso(iso))
        logger.info(
            "%s backcast: NP6 HSL and coal must-run tuning are ERCOT-only and "
            "skipped; per-plant CAMPD + EIA-923 benchmark %s; the report "
            "compares fuel mix, prices and net interchange.",
            iso,
            "built for the covered states"
            if has_campd
            else "skipped (no CAMPD coverage)",
        )
    reference = _load_reference()
    if args.out_dir:
        run_dir = Path(args.out_dir)
    else:
        # Scope the default bundle by ISO so parallel multi-ISO backcasts each
        # land in their own subtree and never collide on a shared timestamp
        # directory (the persist mkdir is exist_ok=True, so two ISOs starting
        # in the same second would otherwise intermix their files into one
        # bundle). It also makes a bundle's ISO obvious from its path.
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = REPO / "results" / "calibration" / iso / ts
        # Same-ISO runs launched within the same second still resolve to one
        # timestamp dir; disambiguate with the PID (distinct per parallel
        # process) so concurrent runs of one ISO stay isolated too.
        if run_dir.exists():
            run_dir = run_dir.with_name(f"{ts}-{os.getpid()}")
    # D-3 zero-forcing ablation twin: land it beside its keeper with an
    # "-ablation" suffix and record which base bundle it ablates (rule 20).
    ablation_of = None
    if args.zero_forcing_ablation:
        ablation_of = run_dir.name
        run_dir = run_dir.with_name(f"{run_dir.name}-ablation")
    # Cross-year warm-start defaults ON for a fresh calibration solve
    # (--no-xyear-warmstart to opt out, explicit env var honored). Resolved here
    # — only on the fresh-solve path, so --report / --replay-bundle /
    # --rebuild-benchmark returned above and stay at the global default OFF.
    # Forecast (runner.py) is unaffected (xyear_cache=None).
    _xwarm = resolve_xyear_warmstart_default(args.no_xyear_warmstart)
    logger.info("cross-year LP warm-start: %s", "ON" if _xwarm else "OFF")
    # Same-year P1 basis seed (wallclock item B): default ON on the same
    # fresh-solve path, --no-p1-basis-seed to opt out, explicit env var
    # honored; the solve core arms it only inside the cross-year gate above.
    _p1_seed = resolve_p1_basis_seed_default(args.no_p1_basis_seed)
    logger.info("P1 basis seed: %s", "ON" if (_p1_seed and _xwarm) else "OFF")
    # Coal family solve kwargs, generated from the same registry rows that
    # generated the parser above (rows riding the prb_overrides channel are
    # excluded there and keep their hand-written plumbing below). One encoding
    # of the CLI dest -> solve kwarg journey, so a rename cannot drift them
    # apart — the ERCOT-65 defect class.
    _coal_kwargs = solve_kwargs_from_args(args, "coal")
    run_dir = solve_and_persist(
        args.year,
        iso,
        args.hours,
        reference,
        **_coal_kwargs,
        commitment=args.commitment,
        screen_coal=not args.no_coal_p2,
        run_dir=run_dir,
        persist_p2_state=args.persist_p2_state,
        persist_p0_commitment=args.persist_p0_commitment,
        persist_p0_dispatch=args.persist_p0_dispatch,
        outage_source=args.outage_source,
        ct_mustrun_per_plant=args.ct_mustrun_per_plant,
        ct_mustrun_floor_frac=args.ct_mustrun_floor_frac,
        coal_prb_passthrough_tiered=args.prb_sigmoid_tiered,
        prb_overrides={
            "coal_prb_passthrough_floor": args.prb_floor,
            "coal_prb_passthrough_ceil": args.prb_ceil,
            "coal_prb_follower_floor": args.prb_follower_floor,
            "coal_prb_follower_ceil": args.prb_follower_ceil,
            "coal_prb_passthrough_gas_mid": args.prb_gas_mid,
            "coal_prb_passthrough_gas_slope": args.prb_gas_slope,
            "coal_prb_follower_gas_mid": args.prb_follower_gas_mid,
            "coal_prb_follower_gas_slope": args.prb_follower_gas_slope,
            # The dict is a generic ScenarioConfig override channel
            # (None entries are dropped); non-PRB calibration toggles
            # ride along here.
            "gas_hub_basis_daily": True if args.gas_hub_basis_daily else None,
            "gas_electric_power_monthly_level": (
                True if args.gas_electric_power_monthly_level else None
            ),
            # NEISO-only per the ScenarioConfig spec: the re-attribution
            # relabels switched generator-hours gas->oil so the model matches
            # the benchmark feed's fuel attribution, and only ISNE's EIA-930
            # feed tracks dual-fuel switching that way. NYIS demonstrably does
            # not (Jan-2025: parity switching relabelled 0.80 TWh while the
            # measured NYIS ``NG: OIL`` carried 0.031 TWh; 2023 the feed shows
            # 2.17 TWh OIL against a 0.42 TWh EIA-923 oil class - a static
            # plant-primary attribution parity hours cannot reproduce), so
            # enabling it for NYISO scored a basis mismatch, not a dispatch
            # error. The daily-basis override channel previously switched it
            # on for every ISO, contradicting the documented NEISO-only spec.
            "dual_fuel_oil_reattribution": (
                True if (args.gas_hub_basis_daily and iso == "NEISO") else None
            ),
            "chp_startup_covered": True if args.chp_startup_covered else None,
            # miso-253: the injected-must-run host-steam partition rides the
            # generic channel, so ONE read path serves the fresh solve, the
            # replay override and a recipe -- and run_config.json records it
            # (rule 24 [R-REGISTRY]) because prb_overrides is applied to
            # recorded_cfg. None keeps the config/recipe value untouched.
            "mustrun_chp_btm_holdout": args.mustrun_chp_btm_holdout,
            # spp-49: the benchmark's vintage-aware membership union rides the
            # same generic channel for the same reasons -- ONE read path for a
            # fresh solve, a replay override and a recipe, and
            # run_config.json records it (rule 24 [R-REGISTRY]) because
            # prb_overrides is applied to recorded_cfg, which is what
            # rebuild_benchmark later recovers it from. None keeps the
            # config/recipe value untouched.
            "benchmark_membership_vintage_union": (
                args.benchmark_membership_vintage_union
            ),
            "coal_warm_committed": True if args.coal_warm_committed else None,
            "committed_ramp_spread": args.committed_ramp_spread,
            "cc_duct_peaking": True if args.cc_duct_peaking else None,
            "cc_duct_peaking_row_scoped": (
                True if args.cc_duct_peaking_row_scoped else None
            ),
            # Per-plant EIA-860 duct-burner shares supersede the 4-plant
            # hardcoded ERCOT peaking override, so turn it off when on.
            "cc_peaking_per_plant": False if args.cc_duct_peaking else None,
            # ercot-254 / ercot-261 (ERCOT-only; no-ops elsewhere). The monthly
            # resolution of the measured delivered-gas LEVEL anchor, and the
            # corroboration sub-gate that decides per month whether the survey
            # print is a price or a monthly cost ratio.
            "ercot_ep_gas_basis_monthly": (
                True if args.ercot_ep_gas_basis_monthly else None
            ),
            "ercot_ep_gas_basis_corroborated": (
                True if args.ercot_ep_gas_basis_corroborated else None
            ),
            "ercot_ep_gas_basis_receipts_fallback": (
                True if args.ercot_ep_gas_basis_receipts_fallback else None
            ),
            "ct_deployment_overlay": True if args.ct_deployment else None,
            "ct_deployment_floor_frac": (
                args.ct_deployment_floor_frac if args.ct_deployment else None
            ),
            "reliability_deployment_overlay": (
                True if args.reliability_deployment else None
            ),
            "reliability_deployment_floor_frac": (
                args.reliability_deployment_floor_frac
                if args.reliability_deployment
                else None
            ),
            "wefor_residual_groups": (
                frozenset(g.strip() for g in args.wefor_relief_groups.split(","))
                if args.wefor_relief_groups
                else None
            ),
            "wefor_residual": args.wefor_residual,
            # Backcast-only per-plant F923 coal price: off in statistical mode
            # / under the ablation flag (falls back to the supply-class
            # trajectory, exactly as a forward year does).
            "coal_plant_monthly_pricing": (
                False if args.no_coal_monthly_pricing else None
            ),
            "coal_lignite_passthrough_sigmoid": True
            if args.coal_lignite_sigmoid
            else None,
            "coal_lignite_passthrough_floor": args.lignite_floor,
            "coal_lignite_passthrough_ceil": args.lignite_ceil,
            "coal_lignite_passthrough_gas_mid": args.lignite_gas_mid,
            "coal_lignite_passthrough_gas_slope": args.lignite_gas_slope,
            "class_commitment_overrides": class_commitment_overrides,
            "coal_sub_passthrough_sigmoid": True if args.coal_sub_sigmoid else None,
            "coal_sub_passthrough_floor": args.sub_floor,
            "coal_sub_passthrough_ceil": args.sub_ceil,
            "coal_sub_passthrough_gas_mid": args.sub_gas_mid,
            "coal_sub_passthrough_gas_slope": args.sub_gas_slope,
            "coal_waste_passthrough_sigmoid": True if args.coal_waste_sigmoid else None,
            "coal_waste_passthrough_floor": args.waste_floor,
            "coal_waste_passthrough_ceil": args.waste_ceil,
            "coal_waste_passthrough_gas_mid": args.waste_gas_mid,
            "coal_waste_passthrough_gas_slope": args.waste_gas_slope,
            # Hydraulic-cascade coupling (NWPP-36 / NWPP-40). Tri-state: None
            # is dropped by the channel and keeps the recipe value; True/False
            # reach run_year's config AND recorded_cfg, so the arming is
            # replayable from meta.json / run_config.json (rule 24).
            "hydro_cascade_coupling": args.hydro_cascade_coupling,
            # Measured per-plant forebay-storage bound (hydro-1). Same
            # tri-state channel and same replayability contract as the
            # cascade flag above (rule 24).
            "hydro_pondage_bound": args.hydro_pondage_bound,
            # The three pre-existing hydro gates, given a CLI surface by
            # hydro-1 (rule 24 gap — see the parser block). Same tri-state
            # channel: None keeps the recipe / per-ISO value untouched.
            "hydro_dispatch_envelope": args.hydro_dispatch_envelope,
            "hydro_min_flow_floor": args.hydro_min_flow_floor,
            "hydro_ror_split": args.hydro_ror_split,
            # Per-plant CC demonstrated-capacity reconciliation (mode=cap
            # bounds a plant AT its CAMPD sustained peak — the EIA-860
            # CA-row block-summer double-count fix). Per-ISO table; never
            # crosses ISO boundaries (rule 25).
            "cc_capacity_reconcile": True if args.cc_capacity_reconcile else None,
            "cc_capacity_reconcile_path": (
                str(
                    REPO
                    / "data"
                    / "raw"
                    / "_processed-legacy"
                    / f"cc_capacity_reconcile_{iso}.csv"
                )
                if args.cc_capacity_reconcile
                else None
            ),
        },
        ct_intermediate_split=args.ct_intermediate_split,
        ct_intermediate_cf_threshold=args.ct_intermediate_cf_threshold,
        cc_intermediate_split=args.cc_intermediate_split,
        tranche_startup_amortization=args.tranche_startup_amortization,
        tranche_startup_measured_runs=args.tranche_startup_measured_runs,
        tranche_startup_conditional_runs=args.tranche_startup_conditional_runs,
        gas_offer_margin=args.gas_offer_margin,
        gas_offer_margin_zonal_anchor=args.gas_offer_margin_zonal_anchor,
        coal_offer_margin=args.coal_offer_margin,
        cc_committed_offer_margin=args.cc_committed_offer_margin,
        coal_peak_offer_margin=args.coal_peak_offer_margin,
        coal_peak_offer_yearly_level=args.coal_peak_offer_yearly_level,
        coal_perplant_offer_level=args.coal_perplant_offer_level,
        coal_perplant_offer_yearly=args.coal_perplant_offer_yearly,
        nysdec_peaker_rule_availability=args.nysdec_peaker_rule_availability,
        nyiso_solar_market_generator_basis=(args.nyiso_solar_market_generator_basis),
        oil_primary_bin_fuel=args.oil_primary_bin_fuel,
        cc_intermediate_cf_threshold=args.cc_intermediate_cf_threshold,
        st_gas_intermediate=args.st_gas_intermediate,
        st_gas_intermediate_cf_threshold=args.st_gas_intermediate_cf_threshold,
        committed_band_measured_basis=args.committed_band_measured_basis,
        ercot_offer_hrmult_ep_rebasis=args.ercot_offer_hrmult_ep_rebasis,
        ercot_offer_hrmult_ep_rebasis_bands=(args.ercot_offer_hrmult_ep_rebasis_bands),
        bit_overrides={
            "coal_bit_passthrough_floor": args.bit_floor,
            "coal_bit_passthrough_ceil": args.bit_ceil,
            "coal_bit_passthrough_gas_mid": args.bit_gas_mid,
            "coal_bit_passthrough_gas_slope": args.bit_gas_slope,
        },
        plant_tranche_config=args.plant_tranche_config,
        storage_daily_cycling=args.storage_daily_cycling,
        storage_vintage_ramp=args.storage_vintage_ramp,
        strict_demand_profile=args.strict_demand_profile,
        battery_dispatch_adder=args.battery_adder,
        as_reserve_withholding=args.as_reserve_withholding,
        energy_reserve_coopt=args.energy_reserve_coopt,
        miso_zonal_reserves=args.miso_zonal_reserves,
        miso_midwest_subregional_reserves=args.miso_midwest_subregional_reserves,
        miso_reserve_pergen=args.miso_reserve_pergen,
        miso_commitment_posture=args.miso_commitment_posture,
        miso_reserve_online_gated=args.miso_reserve_online_gated,
        miso_measured_reserve_requirements=args.miso_measured_reserve_requirements,
        miso_south_seam_split=args.miso_south_seam_split,
        miso_rdt_tcdc=args.miso_rdt_tcdc,
        miso_zonal_loss_surface=args.miso_zonal_loss_surface,
        pjm_zonal_loss_surface=args.pjm_zonal_loss_surface,
        pjm_reserve_pergen=args.pjm_reserve_pergen,
        pjm_reserve_pergen_sync=args.pjm_reserve_pergen_sync,
        pjm_reserve_pergen_size_split=args.pjm_reserve_pergen_size_split,
        pjm_commitment_posture=args.pjm_commitment_posture,
        measured_ramp_capability=args.measured_ramp_capability,
        ercot_multiproduct_as_coopt=args.ercot_multiproduct_as_coopt,
        ercot_ordc_total_reserve=args.ercot_ordc_total_reserve,
        ercot_ordc_cap_dual_adder=args.ercot_ordc_cap_dual_adder,
        ercot_ordc_adder_published_anchor=args.ercot_ordc_adder_published_anchor,
        ercot_ordc_adder_family_counterpart=(args.ercot_ordc_adder_family_counterpart),
        ercot_storage_as_product_credit=args.ercot_storage_as_product_credit,
        ercot_nuclear_unit_availability=args.ercot_nuclear_unit_availability,
        nuclear_unit_availability=args.nuclear_unit_availability,
        ercot_thermal_dam_availability=args.ercot_thermal_dam_availability,
        ercot_thermal_dam_availability_hourly=(
            args.ercot_thermal_dam_availability_hourly
        ),
        ercot_thermal_dam_availability_plant=(
            args.ercot_thermal_dam_availability_plant
        ),
        ercot_wind_zone_shape=args.ercot_wind_zone_shape,
        ercot_storage_capability_measured=args.ercot_storage_capability_measured,
        ercot_online_capacity_envelope_measured=(
            args.ercot_online_capacity_envelope_measured
        ),
        ercot_ordc_only_scarcity=args.ercot_ordc_only_scarcity,
        gas_hh_monthly_shape=args.gas_hh_monthly_shape,
        ercot_as_aware_commitment=args.ercot_as_aware_commitment,
        ercot_reserve_supply_cap=args.ercot_reserve_supply_cap,
        ercot_reserve_supply_cap_from_year=args.ercot_reserve_supply_cap_from_year,
        ercot_as_forward_requirement=args.ercot_as_forward_requirement,
        ercot_load_resource_reserve=args.ercot_load_resource_reserve,
        ercot_load_resource_reserve_from_year=(
            args.ercot_load_resource_reserve_from_year
        ),
        ercot_storage_as_reserve=args.ercot_storage_as_reserve,
        ercot_storage_as_reserve_from_year=(args.ercot_storage_as_reserve_from_year),
        ercot_ecrs_requirement=args.ercot_ecrs_requirement,
        ercot_ecrs_requirement_from_year=(args.ercot_ecrs_requirement_from_year),
        ercot_rtordpa_overlay=args.ercot_rtordpa_overlay,
        ercot_dam_as_overlay=args.ercot_dam_as_overlay,
        ercot_dam_as_overlay_from_year=args.ercot_dam_as_overlay_from_year,
        ercot_dam_as_scarcity_threshold=args.ercot_dam_as_scarcity_threshold,
        ordc_lolp_params_path=args.ordc_lolp_params_path,
        as_reserve_formula=args.as_reserve_formula,
        storage_as_commitment=args.storage_as_commitment,
        ercot_storage_as_deployment=args.ercot_storage_as_deployment,
        ercot_storage_as_endogenous=args.ercot_storage_as_endogenous,
        ercot_storage_as_duration_gate=args.ercot_storage_as_duration_gate,
        ercot_ecrs_conservative_deployment=args.ercot_ecrs_conservative_deployment,
        ercot_nonreleasable_as_withholding=args.ercot_nonreleasable_as_withholding,
        gas_offer_curve=args.gas_offer_curve,
        gas_monthly_actuals=args.gas_monthly_actuals,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
        curve_smoothing={
            "offer_curve_smoothing_n": args.curve_n,
            "offer_curve_smoothing_exp": args.curve_exp,
            "offer_curve_smoothing_mid": args.curve_mid,
        },
        cc_derate_from_top=args.cc_derate_from_top,
        cc_nameplate_summer_derate=args.cc_nameplate_summer_derate,
        temp_dependent_derate=args.temp_dependent_derate,
        temp_derate_hourly_grain=args.temp_derate_hourly_grain,
        temp_derate_mean_anchored=args.temp_derate_mean_anchored,
        temp_derate_classes=(
            frozenset(
                c.strip() for c in args.temp_derate_classes.split(",") if c.strip()
            )
            if args.temp_derate_classes
            else None
        ),
        temp_derate_slope_st_chp=args.temp_derate_slope_st_chp,
        temp_derate_slope_ct_chp=args.temp_derate_slope_ct_chp,
        pjm_offer_surface_conditional=args.pjm_offer_surface_conditional,
        pjm_da_virtual_bids=args.pjm_da_virtual_bids,
        pjm_offer_midcurve_conditional=args.pjm_offer_midcurve_conditional,
        caiso_offer_surface_measured=args.caiso_offer_surface_measured,
        caiso_offer_surface_measured_ungrounded=(
            args.caiso_offer_surface_measured_ungrounded
        ),
        caiso_st_gas_committed_measured=args.caiso_st_gas_committed_measured,
        caiso_st_gas_peak_measured=args.caiso_st_gas_peak_measured,
        caiso_ct_peaker_committed_measured=args.caiso_ct_peaker_committed_measured,
        nyiso_ct_peaker_bands_measured=args.nyiso_ct_peaker_bands_measured,
        nyiso_ct_peaker_committed_measured=args.nyiso_ct_peaker_committed_measured,
        nyiso_st_gas_econ_bands_deleaked=args.nyiso_st_gas_econ_bands_deleaked,
        caiso_offer_surface_conditional=args.caiso_offer_surface_conditional,
        nearby_fuel_price_zone_donor_guard=args.nearby_fuel_price_zone_donor_guard,
        fleet_state_from_eia860=args.fleet_state_from_eia860,
        caiso_citygate_spot_coverage=args.caiso_citygate_spot_coverage,
        priced_interchange=(
            True
            if reference_price_interface and args.priced_interchange is not False
            else resolve_priced_interchange(args.priced_interchange, iso)
        ),
        hydro_backfill_year=args.hydro_backfill_year,
        hydro_eia930_monthly=args.hydro_eia930_monthly,
        hydro_budget_period_by_instrument=args.hydro_budget_period_by_instrument,
        hydro_forecast_budget=args.hydro_forecast_budget,
        hydro_year=args.hydro_year,
        interchange_shaping=args.interchange_shaping,
        interchange_shaping_export_only=args.interchange_shaping_export_only,
        reference_price_interface=reference_price_interface,
        negative_renewable_offers=args.negative_renewable_offers,
        wind_ptc_vintage_offers=args.wind_ptc_vintage_offers,
        caiso_gas_commitment_floor=args.caiso_gas_commitment_floor,
        caiso_gas_floor_frac=args.caiso_gas_floor_frac,
        caiso_ra_mustoffer=args.caiso_ra_mustoffer,
        caiso_ra_min_load_frac=args.caiso_ra_min_load_frac,
        caiso_ra_startup_bridge=args.caiso_ra_startup_bridge,
        caiso_ra_bridge_decommit=args.caiso_ra_bridge_decommit,
        ercot_gas_commitment_bridge=args.ercot_gas_commitment_bridge,
        carry_operating_mothballs=args.carry_operating_mothballs,
        ercot_gas_bridge_min_load_frac=args.ercot_gas_bridge_min_load_frac,
        ercot_gas_bridge_startup=args.ercot_gas_bridge_startup,
        ercot_gas_bridge_da_horizon=args.ercot_gas_bridge_da_horizon,
        ercot_gas_bridge_online_hours=args.ercot_gas_bridge_online_hours,
        ercot_commitment_posture=args.ercot_commitment_posture,
        ercot_commitment_posture_min_load_frac=(
            args.ercot_commitment_posture_min_load_frac
        ),
        reliability_floor=args.reliability_floor,
        reliability_floor_plant_exclusions=args.reliability_floor_plant_exclusions,
        scarcity_price_overlay=args.scarcity_price_overlay,
        caiso_scarcity_pricing=args.caiso_scarcity_pricing,
        caiso_lcr_commitment_credit=args.caiso_lcr_commitment_credit,
        caiso_solar_deliverability=args.caiso_solar_deliverability,
        caiso_solar_deliverability_k=args.caiso_solar_deliverability_k,
        caiso_solar_endogenous_spill=args.caiso_solar_endogenous_spill,
        caiso_solar_cap_at_delivered=args.caiso_solar_cap_at_delivered,
        neiso_gas_coldsnap_derate=args.neiso_gas_coldsnap_derate,
        neiso_coldsnap_derate_dualfuel_unswitched=args.neiso_coldsnap_derate_dualfuel_unswitched,
        neiso_oil_burn_budget=args.neiso_oil_burn_budget,
        neiso_winter_fuel_inventory=args.neiso_winter_fuel_inventory,
        neiso_winter_fuel_start_fill_bbl=args.neiso_winter_fuel_start_fill_bbl,
        neiso_winter_fuel_mustrun=args.neiso_winter_fuel_mustrun,
        coal_fuel_inventory=args.coal_fuel_inventory,
        caiso_import_hub_prices=args.caiso_import_hub_prices,
        caiso_import_gas_coupling=args.caiso_import_gas_coupling,
        caiso_import_solar_shape=args.caiso_import_solar_shape,
        caiso_per_hub_intertie=args.caiso_per_hub_intertie,
        caiso_perhub_firm_base=args.caiso_perhub_firm_base,
        caiso_corridor_flow_limit=args.caiso_corridor_flow_limit,
        caiso_intertie_reference_price=args.caiso_intertie_reference_price,
        caiso_corridor_atc_forward=args.caiso_corridor_atc_forward,
        caiso_reference_price_seam=args.caiso_reference_price_seam,
        caiso_per_year_import_caps=args.caiso_per_year_import_caps,
        caiso_asymmetric_path_ratings=args.caiso_asymmetric_path_ratings,
        caiso_zonal_loss_surface=args.caiso_zonal_loss_surface,
        capacity_deliverability_limits=args.capacity_deliverability_limits,
        unit_outage_lp_capacity_basis=args.unit_outage_lp_capacity_basis,
        unit_outage_mixed_gas_routing=args.unit_outage_mixed_gas_routing,
        unit_outage_st_capacity_basis=args.unit_outage_st_capacity_basis,
        unit_outage_per_unit_clip=args.unit_outage_per_unit_clip,
        unit_outage_short_windows_gas=args.unit_outage_short_windows_gas,
        unit_outage_window_hour_grain=args.unit_outage_window_hour_grain,
        campd_per_unit_attribution=args.campd_per_unit_attribution,
        campd_outage_merit_order_guard=args.campd_outage_merit_order_guard,
        cc_winter_capability_basis=args.cc_winter_capability_basis,
        ramp_limits=args.ramp_limits,
        local_capacity_constraints=args.local_capacity_constraints,
        ct_netload_drag=args.ct_netload_drag,
        netload_drag_layup_window_mask=args.netload_drag_layup_window_mask,
        netload_drag_merit_allocation=args.netload_drag_merit_allocation,
        netload_drag_min_run_persistence=args.netload_drag_min_run_persistence,
        vre_curtailment_oversupply_allocation=args.vre_curtailment_oversupply_allocation,
        spp_curtailment_ceiling=args.spp_curtailment_ceiling,
        spp_curtail_depth_wind=args.spp_curtail_depth_wind,
        pjm_interface_feed_admissibility_gate=args.pjm_interface_feed_admissibility_gate,
        gas_offer_margin_anchor_vintage=args.gas_offer_margin_anchor_vintage,
        gas_offer_margin_zonal_anchor_vintage=args.gas_offer_margin_zonal_anchor_vintage,
        nyiso_local_selfsupply=args.nyiso_local_selfsupply,
        nyiso_scr_edrp=args.nyiso_scr_edrp,
        nyiso_scr_edrp_strike=args.nyiso_scr_edrp_strike,
        nyiso_firm_imports=args.nyiso_firm_imports,
        nyiso_import_reconciliation=args.nyiso_import_reconciliation,
        nyiso_import_hub_prices=args.nyiso_import_hub_prices,
        nyiso_iroquois_winter_spread=args.nyiso_iroquois_winter_spread,
        nyiso_synchronised_reserve=args.nyiso_synchronised_reserve,
        nyiso_li_locational_reserve=args.nyiso_li_locational_reserve,
        nyiso_incity_commitment_obligation=args.nyiso_incity_commitment_obligation,
        nyiso_east_reserve_families=args.nyiso_east_reserve_families,
        reliability_floor_overrides=reliability_floor_overrides,
        nyiso_spin_reserve_online=args.nyiso_spin_reserve_online,
        nyiso_gas_commitment_bridge=args.nyiso_gas_commitment_bridge,
        spp_gas_commitment_bridge=args.spp_gas_commitment_bridge,
        soco_gas_st_campaign_commitment=args.soco_gas_st_campaign_commitment,
        miso_coal_night_floor=args.miso_coal_night_floor,
        nyiso_gas_bridge_cc_min_load_frac=args.nyiso_gas_bridge_cc_min_load_frac,
        nyiso_gas_bridge_st_min_load_frac=args.nyiso_gas_bridge_st_min_load_frac,
        nyiso_gas_bridge_startup=args.nyiso_gas_bridge_startup,
        nyiso_gas_bridge_da_horizon=args.nyiso_gas_bridge_da_horizon,
        nyiso_gas_bridge_min_run=args.nyiso_gas_bridge_min_run,
        nyiso_gas_bridge_plant_exclusions=args.nyiso_gas_bridge_plant_exclusions,
        nyiso_gas_bridge_reserve_duty_exclusions=(
            args.nyiso_gas_bridge_reserve_duty_exclusions
        ),
        nyiso_gas_bridge_plant_min_run=args.nyiso_gas_bridge_plant_min_run,
        nyiso_gas_bridge_online_hours=args.nyiso_gas_bridge_online_hours,
        nyiso_gas_bridge_state_floor_min_run=args.nyiso_gas_bridge_state_floor_min_run,
        nyiso_gas_bridge_startup_aware=args.nyiso_gas_bridge_startup_aware,
        nyiso_chp_btm_measured=args.nyiso_chp_btm_measured,
        cc_reserve_duty_split=args.cc_reserve_duty_split,
        chp_layup_duty_split=args.chp_layup_duty_split,
        chp_layup_duty_curve=args.chp_layup_duty_curve,
        egrid_identity_heat_rates=args.egrid_identity_heat_rates,
        measured_ct_heat_rates=args.measured_ct_heat_rates,
        measured_coal_heat_rates=args.measured_coal_heat_rates,
        measured_st_heat_rates=args.measured_st_heat_rates,
        egrid_family_heat_rates=args.egrid_family_heat_rates,
        egrid_steam_collapse_heat_rates=args.egrid_steam_collapse_heat_rates,
        nyiso_gas_bridge_cc_min_run_hours=args.nyiso_gas_bridge_cc_min_run_hours,
        nyiso_gas_bridge_st_min_run_hours=args.nyiso_gas_bridge_st_min_run_hours,
        nyiso_spin_headroom_frac=args.nyiso_spin_headroom_frac,
        nyiso_dynamic_reserve_requirements=args.nyiso_dynamic_reserve_requirements,
        nyiso_hydro_reserve_eligible=args.nyiso_hydro_reserve_eligible,
        nyiso_scr_edrp_reserve_eligible=args.nyiso_scr_edrp_reserve_eligible,
        neiso_dynamic_reserve_requirements=args.neiso_dynamic_reserve_requirements,
        miso_firm_imports=miso_firm_imports,
        miso_seam_flow_limit=args.miso_seam_flow_limit,
        miso_seam_flow_percentile=args.miso_seam_flow_percentile,
        miso_seam_export_limit=args.miso_seam_export_limit,
        miso_seam_envelope_merit_cap=args.miso_seam_envelope_merit_cap,
        miso_seam_envelope_hour_ending_key=args.miso_seam_envelope_hour_ending_key,
        miso_import_sil_measured_envelope=args.miso_import_sil_measured_envelope,
        nyiso_seam_deliverability_envelope=args.nyiso_seam_deliverability_envelope,
        nyiso_seam_par_attribution=args.nyiso_seam_par_attribution,
        miso_pjm_border_anchor=args.miso_pjm_border_anchor,
        miso_cc_coal_rebalance=args.miso_cc_coal_rebalance,
        miso_firm_import_floor=args.miso_firm_import_floor,
        miso_pjm_lmp_import_pricing=args.miso_pjm_lmp_import_pricing,
        miso_seam_measured_ladder=args.miso_seam_measured_ladder,
        miso_zonal_gas_basis=args.miso_zonal_gas_basis,
        miso_winter_citygate_daily=args.miso_winter_citygate_daily,
        pjm_seam_flow_limit=args.pjm_seam_flow_limit,
        pjm_seam_flow_percentile=args.pjm_seam_flow_percentile,
        pjm_seam_export_limit=args.pjm_seam_export_limit,
        pjm_seam_measured_ladder=args.pjm_seam_measured_ladder,
        pjm_seam_neighbour_hourly_ladder=args.pjm_seam_neighbour_hourly_ladder,
        pjm_measured_interface_limits=args.pjm_measured_interface_limits,
        gas_hub_basis_overlay=args.gas_hub_basis_overlay,
        btm_backfill_year=args.btm_backfill_year,
        mass_cap_enabled=args.mass_cap_enabled,
        mass_cap_tons=args.mass_cap_tons,
        mass_cap_program=args.mass_cap_program,
        zero_forcing_ablation=args.zero_forcing_ablation,
        ablation_of=ablation_of,
        reuse_solved=Path(args.reuse_solved) if args.reuse_solved else None,
        note=args.note,
    )
    report_run(run_dir, band_width=args.cf_band_width)


if __name__ == "__main__":
    main()
