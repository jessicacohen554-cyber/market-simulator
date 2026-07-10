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
import json
import logging
import os
import pickle
import subprocess
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

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
    fossil_classes,
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
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from market_sim.model.transmission import extend_with_import_node  # noqa: E402
from market_sim.data.coal import coal_supply_class  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    _COAL_SUPPLY_TO_CURVE,
    OTHER_FOSSIL_CLASS,
    apply_other_fossil_scoring,
)
from market_sim.pipeline.backcast_config import backcast_config  # noqa: E402
from market_sim.results.calibration import check_cf_band_occupancy  # noqa: E402
from scripts.lib.bundle_io import (  # noqa: E402
    bundle_input_path,
    write_shared_input,
)
from scripts.run_calibration import (  # noqa: E402
    _commitment_pass,
    _henry_hub_actual,
    _load_reference,
    run_year,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("calibration_full")

_MWH_PER_TWH: float = 1.0e6
_HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)
_MONTH_NAMES: tuple[str, ...] = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

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


def _hour_to_month(hours: int) -> np.ndarray:
    """Return ``(hours,)`` mapping each hour to a 1-based month."""
    month = np.empty(hours, dtype=int)
    h = 0
    for m, days in enumerate(_DAYS_IN_MONTH, start=1):
        end = min(h + days * 24, hours)
        month[h:end] = m
        h = end
        if h >= hours:
            break
    return month


def _hourly_to_monthly(hourly_mw: np.ndarray) -> np.ndarray:
    """Return ``(12,) MWh`` for a length-8760 hourly MW array."""
    months = _hour_to_month(hourly_mw.shape[0])
    return np.array([hourly_mw[months == m].sum() for m in range(1, 13)], dtype=float)


def _pearson_r(model: np.ndarray, observed: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series."""
    m = model - model.mean()
    o = observed - observed.mean()
    denom = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / denom) if denom > 0.0 else float("nan")


def _nrmse(model: np.ndarray, observed: np.ndarray) -> float:
    """Return RMSE divided by mean observed."""
    rmse = float(np.sqrt(((model - observed) ** 2).mean()))
    denom = float(observed.mean())
    return rmse / denom if denom > 0.0 else float("nan")


def _print_table(rows: list[tuple]) -> None:
    """Print a column-aligned text table from a header + rows tuple list."""
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


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

    rep = lambda a: np.repeat(np.asarray(a, dtype=object), T)  # noqa: E731
    hours = np.tile(np.arange(T, dtype=np.int32), n_gen)
    klass_col = rep(klass)
    fuel_col = rep(fuels)
    # Dual-fuel re-attribution: a gas unit that switched to its backup oil this
    # hour (gas price > oil parity; mask from fuel.dual_fuel_switch_mask) burned
    # petroleum, so its dispatched MWh is counted as oil (EIA-930 ``NG: OIL``),
    # not gas — the LP still priced/dispatched it on the gas heat-rate (the
    # switch is objective-only), this only relabels the generation. The mask is
    # ``(n_gen, T)`` over the LP generators, the same (gen, hour) row-major order
    # as ``disp.reshape(-1)`` and ``rep(...)``, so flatten and overwrite in place.
    if oil_switch_mask is not None and np.asarray(oil_switch_mask).any():
        flat = np.asarray(oil_switch_mask, dtype=bool)[:n_gen, :T].reshape(-1)
        klass_col = np.asarray(klass_col, dtype=object)
        fuel_col = np.asarray(fuel_col, dtype=object)
        klass_col[flat] = "oil"
        fuel_col[flat] = "oil"
    frames = [
        pd.DataFrame(
            {
                "unit_id": rep(unit_ids),
                "plant_code": np.repeat(plant_codes.astype(np.int32), T),
                "klass": klass_col,
                "fuel": fuel_col,
                "supply": rep(supply),
                "zone": rep(zones),
                "hour": hours,
                "mw": disp.reshape(-1),
                "lmp": prices[gen_zidx, :].reshape(-1),
            }
        )
    ]

    pseudo = [
        ("wind", result.wind_dispatched),
        ("solar", result.solar_dispatched),
    ]
    # Injected must-run residual classes (biomass / hydro / OTHER), re-added per
    # zone so total model generation reconciles to load (they were netted out of
    # the LP's demand). Carry klass == fuel == the class key.
    for klass, arr in (must_run or {}).items():
        pseudo.append((klass, arr))
    for name, arr in pseudo:
        a = np.asarray(arr, dtype=np.float32)[:, :T]
        for z in range(a.shape[0]):
            zone = zone_names[z]
            frames.append(
                pd.DataFrame(
                    {
                        "unit_id": f"{name.upper()}_{zone}",
                        "plant_code": np.int32(0),
                        "klass": name,
                        "fuel": name,
                        "supply": "",
                        "zone": zone,
                        "hour": np.arange(T, dtype=np.int32),
                        "mw": a[z],
                        "lmp": prices[z],
                    }
                )
            )

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "unit_id", "klass", "fuel", "supply", "zone"):
        df[col] = df[col].astype("category")
    df["mw"] = df["mw"].astype(np.float32)
    df["lmp"] = df["lmp"].astype(np.float32)
    return df


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
) -> pd.DataFrame:
    """Return the per-zone hourly price / slack / demand frame.

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
        if (
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
                ordc_adder = np.asarray(cap_dual, dtype=float)[:, :T].sum(axis=0).copy()
            elif ercot_ordc_total_reserve and rpf is not None:
                ordc_adder = np.asarray(rpf, dtype=float)[:T, -1].copy()
            else:
                ordc_adder = rp.copy()
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
        if overlay is not None:
            cols["rtordpa_overlay"] = overlay
        if dam_as is not None:
            cols["dam_as_overlay"] = dam_as
        if ordc_adder is not None:
            cols["ordc_adder"] = ordc_adder
        rows.append(pd.DataFrame(cols))
    return pd.concat(rows, ignore_index=True)


def _storage_frame(
    year: int,
    pass_label: str,
    result,
    storage_units,
) -> pd.DataFrame | None:
    """Return the long per-storage-unit hourly charge/discharge frame.

    One row per (storage unit, hour) carrying the unit's charge and
    discharge MW plus its tech (li_ion / pumped_storage) and zone, so the
    bundle exposes storage throughput the way ``dispatch/`` exposes
    generator output. Returns ``None`` when the fleet is empty.
    """
    if not storage_units or result.storage_discharge is None:
        return None
    chg = np.asarray(result.storage_charge, dtype=np.float32)
    dis = np.asarray(result.storage_discharge, dtype=np.float32)
    n_storage, T = dis.shape
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
    r = np.asarray(result.posture_reserve_mw, dtype=np.float32)
    df = pd.DataFrame(
        {
            "zone": np.repeat(zone_lab, T),
            "fuel": np.repeat(fuel_lab, T),
            "hour": np.tile(np.arange(T, dtype=np.int32), q),
            "online_mw": np.asarray(u, dtype=np.float32).reshape(-1),
            "startup_mw": su.reshape(-1),
            "reserve_mw": r.reshape(-1),
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
    """
    bench = load_eia_hourly_benchmark(iso, year)
    if bench is None:
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


@lru_cache(maxsize=8)
def _iso_plant_ids(iso: str) -> frozenset[int]:
    """ORIS codes physically located in ``iso`` (eGRID/EIA-860 BA geography).

    EIA-923's ``generation`` table is national; without restricting to the
    ISO the per-class benchmark totals leak in every other US plant (e.g. PRB
    coal shows the ~639 TWh national figure instead of ERCOT's ~47 TWh).
    """
    return frozenset(build_zone_lookup(iso))


def _eia923_frame(
    year: int,
    generation: pd.DataFrame,
    iso: str = "ERCOT",
) -> pd.DataFrame:
    """Return EIA-923 net generation per (plant, class), annual and monthly.

    Restricted to plants in ``iso`` so the per-class totals are the ISO's
    actual generation, not the national EIA-923 sum.
    """
    df = generation[generation["year"] == year].copy()
    iso_plants = _iso_plant_ids(iso)
    if iso_plants:
        df = df[df["plant_id"].isin(iso_plants)].copy()
    df["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
        )
    ]
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
        annual, monthly = _reconciled_mustrun_class(klass, year, generation, iso, e930)
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


def _backfill_eia923_with_campd(
    e923: pd.DataFrame,
    campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str],
    year: int,
) -> pd.DataFrame:
    """Backfill EIA-923 with CAMPD net for model plants it under-reports.

    For each non-CHP grid plant (coal / CC_REGULAR / ST_GAS / CT_PEAKER) whose
    EIA-923 annual is below :data:`_CAMPD_BACKFILL_MIN_MWH` while CAMPD net is
    above it, set the benchmark annual + monthly to CAMPD net (gross x
    parasitic factor), keyed to the plant's class. Plants EIA-923 already
    reports (e.g. V H Braunig, R W Miller) are untouched.
    """
    if campd_year is None or campd_year.empty:
        return e923
    e923 = e923.copy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    month1 = _hour_to_month(int(campd_year["hour"].max()) + 1)  # 1-based
    add, n_repl = [], 0
    for pid, sub in campd_year.groupby("plant_id"):
        group = group_by_code.get(int(pid))
        if group not in _BACKFILL_GROUPS:
            continue
        net = sub.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        if net.sum() < _CAMPD_BACKFILL_MIN_MWH:
            continue
        if group == "COAL":
            klass = _coal_supply_class(int(pid))
        else:
            klass = group
        cur = e923[(e923["plant_id"] == int(pid)) & (e923["klass"] == klass)]
        if float(cur["annual_mwh"].sum()) >= _CAMPD_BACKFILL_MIN_MWH:
            continue  # EIA-923 reports it adequately
        monthly = {
            mcols[m]: float(net[month1[: len(net)] == m + 1].sum()) for m in range(12)
        }
        if len(cur):
            i = cur.index[0]
            e923.at[i, "annual_mwh"] = float(net.sum())
            for k, v in monthly.items():
                e923.at[i, k] = v
            n_repl += 1
        else:
            add.append(
                {
                    "year": np.int16(year),
                    "plant_id": int(pid),
                    "klass": klass,
                    "annual_mwh": float(net.sum()),
                    **monthly,
                }
            )
    if add or n_repl:
        logger.info(
            "EIA-923 %d: CAMPD-backfilled %d under-reported plants "
            "(%d replaced, %d added)",
            year,
            n_repl + len(add),
            n_repl,
            len(add),
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
) -> float:
    """ISO EIA-923 total net gen as a fraction of the EIA-930 grid net_gen.

    ~1.0 for a complete vintage; the 2025 early monthly survey reads ~0.73.
    Returns 1.0 when no EIA-930 net_gen is available (no swap then).
    """
    ann930_net, _ = _e930_series_annual_monthly(e930, "net_gen", year)
    if ann930_net <= 0.0:
        return 1.0
    iso_plants = _iso_plant_ids(iso)
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
        df = _eia923_frame(yr, generation, iso)
        df = df[df["klass"] == klass]
        if klass == "OTHER":
            df = df[~df["plant_id"].isin(_pumped_storage_plant_ids())]
        return df

    cur = _rows(year)
    annual = float(cur["annual_mwh"].sum())
    monthly = cur[mcols].sum().to_numpy(dtype=float)
    completeness = _vintage_completeness(year, generation, iso, e930)
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
) -> tuple[float, np.ndarray]:
    """Measured biomass class energy ``(annual_mwh, monthly[12])`` with the carry.

    Thin wrapper over :func:`_reconciled_mustrun_class` for the biomass class (the
    benchmark's biomass repair and the report's like-for-like total still call it
    by name).
    """
    return _reconciled_mustrun_class("biomass", year, generation, iso, e930)


def _backfill_renewables_eia930(
    e923: pd.DataFrame,
    year: int,
    iso: str,
    generation: pd.DataFrame,
    e930: pd.DataFrame | None,
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
    * ``biomass``: absent from both CAMPD and EIA-930. When the whole vintage is
      a partial release (:func:`_vintage_completeness`), the prior complete
      year's biomass class total is carried forward, scaled by the vintage
      completeness (its monthly shape reused), rather than left truncated.
    """
    if e930 is None:
        return e923
    cls_total = e923.groupby("klass")["annual_mwh"].sum()
    for klass in _EIA930_RENEWABLE_CLASSES:
        ann930, mon930 = _e930_series_annual_monthly(e930, klass, year)
        if ann930 <= 0.0:
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

    completeness = _vintage_completeness(year, generation, iso, e930)
    if completeness < _EIA923_VINTAGE_COMPLETENESS_FRACTION:
        mcols = [f"m{i:02d}" for i in range(1, 13)]
        prior = _eia923_frame(year - 1, generation, iso)
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


def _benchmark_eia923_frame(
    year: int,
    generation: pd.DataFrame,
    iso: str,
    campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str],
    e930: pd.DataFrame | None,
) -> pd.DataFrame:
    """The bundle's per-class EIA-923 benchmark: CAMPD thermal backfill + the
    EIA-930 renewable / prior-year biomass repair for incomplete vintages.
    """
    e923 = _backfill_eia923_with_campd(
        _eia923_frame(year, generation, iso),
        campd_year,
        group_by_code,
        year,
    )
    return _backfill_renewables_eia930(e923, year, iso, generation, e930)


def _btm_frame(
    year: int,
    pass_label: str,
    generation: pd.DataFrame,
    btm_backfill_year: int | None = None,
    campd_active: set[int] | None = None,
    iso: str = "ERCOT",
    group_by_code: dict[int, str] | None = None,
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
    mr = compute_must_run_emissions(
        bins,
        year,
        total_gen_by_plant=total_by_plant,
        btm_share_by_plant=share_by_plant,
    )
    btm_by_class: dict[str, float] = {}
    if not mr.empty:
        for grp, twh in (
            mr.groupby("Plant_Group")["mr_gen_mwh"].sum() / _MWH_PER_TWH
        ).items():
            btm_by_class[str(grp)] = btm_by_class.get(str(grp), 0.0) + float(twh)
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
            btm_by_class[str(klass)] = btm_by_class.get(str(klass), 0.0) + (
                float(tot) * pct / 100.0 / _MWH_PER_TWH
            )
    if not btm_by_class:
        return pd.DataFrame(columns=["year", "pass", "klass", "btm_twh"])
    return pd.DataFrame(
        {
            "year": np.int16(year),
            "pass": pass_label,
            "klass": list(btm_by_class.keys()),
            "btm_twh": list(btm_by_class.values()),
        }
    )


def _highspy_version() -> str:
    """Return the installed highspy version, or '' if unavailable."""
    try:
        from importlib.metadata import version

        return version("highspy")
    except Exception:
        return ""


def _json_default(obj: object) -> object:
    """JSON encoder fallback for bundle metadata.

    ``set``/``frozenset`` (e.g. ``ScenarioConfig.wefor_residual_groups``,
    carried through the generic prb_overrides channel) serialize as a sorted
    list; anything else falls back to ``str`` so the dump never crashes
    mid-bundle (the run-104..106 failure mode: a frozenset in the override
    record aborted meta.json after the parquets were already written).
    """
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    return str(obj)


def _git_sha() -> str:
    """Return the current git short SHA, or '' if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def _git(*args: str) -> str:
    """Run a git command in REPO and return stripped stdout (or '')."""
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


# Paths excluded from the manifest's git state: a run's own outputs (and other
# bundles) are not "model changes" and would just be noise.
_GIT_STATE_EXCLUDE = (":(exclude)results", ":(exclude)outputs")


def _git_state() -> dict:
    """Capture git provenance so a bundle records exactly which code ran.

    Returns the short SHA, branch, a ``dirty`` flag, the list of changed model
    files, and a diffstat. ``results/`` and ``outputs/`` are excluded so the
    state reflects model/source edits, not the run's own artifacts. When dirty
    the run included uncommitted model changes; the caller snapshots the diff.
    """
    porcelain = _git("status", "--porcelain", "--", *_GIT_STATE_EXCLUDE)
    changed = [ln[3:] for ln in porcelain.splitlines()] if porcelain else []
    return {
        "sha": _git("rev-parse", "--short", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(porcelain),
        "changed_files": changed,
        "diffstat": _git("diff", "--stat", "HEAD", "--", *_GIT_STATE_EXCLUDE),
    }


def _parse_offer_curve_json(
    raw: str | None, flag: str = "--offer-curve-json"
) -> dict | None:
    """Parse an offer-curve JSON argument, failing fast on bad input.

    Accepts an inline JSON object, a path to a ``.json`` file, or ``None``.
    Returns the parsed ``{class: {band: number}}`` mapping, or ``None`` when
    nothing was given. Used for both the absolute ``--offer-curve-json`` and
    the relative ``--offer-curve-delta-json`` (same shape: class -> band ->
    number). Raises ``SystemExit`` with a clear, ``flag``-tagged message on
    malformed JSON or the wrong shape so a CI run fails loudly rather than
    silently solving against the wrong curve.
    """
    if raw is None or not str(raw).strip():
        return None
    text = raw
    candidate = Path(raw)
    if not raw.lstrip().startswith("{") and candidate.exists():
        text = candidate.read_text()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{flag}: invalid JSON ({exc}). Expected an object "
            'like {"CT_PEAKER":{"committed":1.40,"econ_low":1.27}}.'
        )
    if not isinstance(parsed, dict):
        raise SystemExit(
            f"{flag}: top level must be a JSON object keyed by "
            f"fleet class, got {type(parsed).__name__}."
        )
    valid_classes = set(fossil_classes())
    for cls, bands in parsed.items():
        # Fail loudly on a class key the offer-curve router will never read
        # (e.g. COAL_SUB after the SUB -> COAL_PRB taxonomy rename): a dead
        # knob silently tunes nothing, which is worse than an error.
        if cls not in valid_classes:
            raise SystemExit(
                f"{flag}: unknown fleet class {cls!r} — the offer-curve "
                f"router only reads {sorted(valid_classes)}. (Sub-bituminous "
                "coal is COAL_PRB; COAL_SUB no longer exists.)"
            )
        if not isinstance(bands, dict):
            raise SystemExit(
                f"{flag}: value for {cls!r} must be an object of "
                f"band->number, got {type(bands).__name__}."
            )
        for band, val in bands.items():
            if band == "peak_ladder":
                # Measured peak-band quantile ladder: a list of
                # [capacity_share, multiplier] rungs (derive_dam_offer_hrmults
                # --peak-ladder). Shares must be positive and sum to ~1 so the
                # rungs exactly re-partition the peak tranche's capacity.
                if not (
                    isinstance(val, list)
                    and val
                    and all(
                        isinstance(r, (list, tuple))
                        and len(r) == 2
                        and all(
                            isinstance(x, (int, float)) and not isinstance(x, bool)
                            for x in r
                        )
                        and r[0] > 0
                        for r in val
                    )
                ):
                    raise SystemExit(
                        f"{flag}: {cls}.peak_ladder must be a non-empty list of "
                        f"[capacity_share, multiplier] pairs, got {val!r}."
                    )
                total = sum(float(r[0]) for r in val)
                if not 0.99 <= total <= 1.01:
                    raise SystemExit(
                        f"{flag}: {cls}.peak_ladder capacity shares must sum to "
                        f"1.0 (±0.01), got {total:.3f}."
                    )
                continue
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SystemExit(f"{flag}: {cls}.{band} must be a number, got {val!r}.")
    return parsed


def write_run_config(
    run_dir: Path, cfg, meta: dict, note: str = "", ablation_of: str | None = None
) -> None:
    """Write ``run_config.json`` (and ``model_changes.diff`` if dirty).

    A discrete, self-contained record of what was run: the full resolved
    ``ScenarioConfig`` (every knob), the calibration flags, git provenance,
    and any free-text note describing pre-run model changes. The companion
    ``model_changes.diff`` snapshots uncommitted edits so the exact code is
    reproducible from the bundle alone.

    ``ablation_of`` (D-3, CLAUDE.md rule 20): when this bundle is a zero-forcing
    ablation twin, the base keeper bundle name it ablates is recorded at the top
    level so the twin is self-identifying and the calibration-report skill can
    link it from the keeper's sidecar ``ablation_twin`` field.
    """
    import dataclasses

    git = _git_state()
    payload = {
        "timestamp": meta.get("timestamp"),
        "git": git,
        "model_changes_note": note,
        "ablation_of": ablation_of,
        "calibration_flags": {
            k: meta.get(k)
            for k in (
                "iso",
                "years",
                "hours",
                "passes",
                "commitment",
                "commitment_screen_coal",
                "gas_prices",
                "outage_source",
                "coal_lignite_mustrun",
                "coal_prb_mustrun",
                "coal_prb_passthrough",
                "coal_prb_passthrough_sigmoid",
                "coal_mustrun_per_plant",
                "retiree_cems_cap",
                "ct_mustrun_per_plant",
                "ct_mustrun_floor_frac",
                "coal_drop_pof",
                "coal_prb_passthrough_tiered",
                "coal_prb_sigmoid_overrides",
                "coal_bit_passthrough_sigmoid",
                "coal_bit_sigmoid_overrides",
                "coal_plant_monthly_pricing",
                "td_loss_factor",
                "offer_curve_overrides",
                "offer_curve_deltas",
                "priced_interchange",
                "ercot_rtordpa_overlay",
                "ercot_dam_as_overlay",
                "ercot_dam_as_overlay_from_year",
                "ercot_dam_as_scarcity_threshold",
                "temp_dependent_derate",
                "git_sha",
            )
        },
        "scenario_config": dataclasses.asdict(cfg),
    }
    (run_dir / "run_config.json").write_text(
        json.dumps(payload, indent=2, default=_json_default)
    )
    if git["dirty"]:
        diff = _git("diff", "HEAD", "--", *_GIT_STATE_EXCLUDE)
        if diff:
            (run_dir / "model_changes.diff").write_text(diff)


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
    coal_takeorpay_from_data: bool = False,
    coal_mustrun_online_pmin: bool = False,
    coal_sync_srmc_tranche: bool = False,
    ct_intermediate_split: bool = False,
    ct_intermediate_cf_threshold: float | None = None,
    cc_intermediate_split: bool = False,
    cc_intermediate_cf_threshold: float | None = None,
    tranche_startup_amortization: bool = False,
    tranche_startup_measured_runs: bool = False,
    nysdec_peaker_rule_availability: bool = False,
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
    miso_reserve_pergen: bool = False,
    miso_commitment_posture: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_ecrs_conservative_deployment: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_ordc_cap_dual_adder: bool = False,
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
    ercot_storage_as_endogenous: bool = False,
    ercot_storage_as_duration_gate: bool = False,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    pjm_zonal_gas_basis: bool = False,
    miso_zonal_gas_basis: bool = False,
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
    ercot_offer_surface_conditional: bool = False,
    neiso_offer_surface_conditional: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    hydro_eia930_monthly: bool = False,
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
    reliability_floor: bool | None = None,
    scarcity_price_overlay: bool | None = None,
    caiso_scarcity_pricing: bool | None = None,
    caiso_lcr_commitment_credit: bool | None = None,
    caiso_solar_deliverability: bool | None = None,
    caiso_solar_deliverability_k: float | None = None,
    caiso_solar_endogenous_spill: bool | None = None,
    caiso_solar_cap_at_delivered: bool | None = None,
    neiso_gas_coldsnap_derate: bool | None = None,
    neiso_oil_burn_budget: bool | None = None,
    neiso_winter_fuel_inventory: bool | None = None,
    neiso_winter_fuel_start_fill_bbl: float | None = None,
    neiso_winter_fuel_mustrun: bool | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_bidir_intertie: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_perhub_firm_base: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    caiso_reference_price_seam: bool | None = None,
    capacity_deliverability_limits: bool | None = None,
    ramp_limits: bool | None = None,
    local_capacity_constraints: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_import_hub_prices: bool | None = None,
    nyiso_iroquois_winter_spread: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    nyiso_dynamic_reserve_requirements: bool | None = None,
    neiso_dynamic_reserve_requirements: bool | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    miso_seam_flow_percentile: float | None = None,
    miso_seam_export_limit: bool = False,
    miso_pjm_border_anchor: bool = False,
    miso_cc_coal_rebalance: bool = False,
    miso_firm_import_floor: bool = False,
    miso_pjm_lmp_import_pricing: bool = False,
    miso_seam_measured_ladder: bool = False,
    pjm_seam_flow_limit: bool = False,
    pjm_seam_flow_percentile: float | None = None,
    pjm_seam_export_limit: bool = False,
    pjm_seam_measured_ladder: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict | None = None,
    ct_netload_drag: bool | None = None,
    ct_drag_overrides: dict | None = None,
    chp_export_floor_measured: bool = False,
    ercot_gtc_limits_measured: bool = False,
    ercot_wtx_curtailment_driver: bool | None = None,
    ercot_wtx_curtail_depth_wind: float | None = None,
    ercot_wtx_curtail_depth_solar: float | None = None,
    mass_cap_enabled: bool = False,
    mass_cap_tons: float | None = None,
    mass_cap_program: str | None = None,
    btm_backfill_year: int | None = None,
    zero_forcing_ablation: bool = False,
    ablation_of: str | None = None,
    note: str = "",
) -> Path:
    """Solve every year/pass, write the parquet bundle, return the run dir.

    ``zero_forcing_ablation`` (D-3, CLAUDE.md rule 20): solve the zero-forcing
    ablation twin — every merchant floor/bridge neutralized in ``run_year`` via
    ``ScenarioConfig.as_zero_forcing_ablation`` — and record ``ablation_of`` (the
    base keeper bundle name) at the top of ``run_config.json``.
    """
    iso_config = get_iso_config(iso)
    if priced_interchange:
        # Interchange served by the priced import/export node (external zone
        # + import tranches + export sinks) instead of the measured schedule;
        # the bundle's zone set and demand frames follow the extended
        # topology so they match run_year's solve.
        iso_config = extend_with_import_node(iso_config)
        if (caiso_per_hub_intertie or caiso_reference_price_seam) and iso == "CAISO":
            # Split WECC_import into the two per-hub corridors so this caller's
            # zone_names / must-run / report frames match run_year's solve
            # (run_year applies the same split idempotently). Both the measured
            # per-hub path and the forward reference-price seam ride the corridor
            # split. See transmission.split_caiso_import_node_per_hub.
            from market_sim.model.transmission import split_caiso_import_node_per_hub

            iso_config = split_caiso_import_node_per_hub(iso_config)
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
    gas_prices: dict[int, float] = {}
    passes_seen: set[str] = set()

    for year in years:
        gas_price = _henry_hub_actual(reference, year)
        gas_prices[year] = gas_price
        if not is_ercot:
            group_by_code = _fleet_group_by_code(iso, iso_config, year)
        cfg = backcast_config(year, iso, hours, gas_price)
        demand = load_demand(
            iso,
            year,
            iso_config,
            td_loss_factor=cfg.td_loss_factor,
            include_interchange=not priced_interchange,
            strict_demand_profile=strict_demand_profile,
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
        must_run = _must_run_profiles(
            year,
            generation,
            iso,
            demand,
            skip_classes=frozenset(),
            e930=e930_year,
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
            coal_takeorpay_from_data=coal_takeorpay_from_data,
            coal_mustrun_online_pmin=coal_mustrun_online_pmin,
            coal_sync_srmc_tranche=coal_sync_srmc_tranche,
            ct_intermediate_split=ct_intermediate_split,
            ct_intermediate_cf_threshold=ct_intermediate_cf_threshold,
            cc_intermediate_split=cc_intermediate_split,
            cc_intermediate_cf_threshold=cc_intermediate_cf_threshold,
            tranche_startup_amortization=tranche_startup_amortization,
            tranche_startup_measured_runs=tranche_startup_measured_runs,
            nysdec_peaker_rule_availability=nysdec_peaker_rule_availability,
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
            miso_reserve_pergen=miso_reserve_pergen,
            miso_commitment_posture=miso_commitment_posture,
            ercot_multiproduct_as_coopt=ercot_multiproduct_as_coopt,
            ercot_ecrs_conservative_deployment=ercot_ecrs_conservative_deployment,
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
            ercot_storage_as_endogenous=ercot_storage_as_endogenous,
            ercot_storage_as_duration_gate=ercot_storage_as_duration_gate,
            gas_offer_curve=gas_offer_curve,
            gas_monthly_actuals=gas_monthly_actuals,
            pjm_zonal_gas_basis=pjm_zonal_gas_basis,
            miso_zonal_gas_basis=miso_zonal_gas_basis,
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
            ercot_offer_surface_conditional=ercot_offer_surface_conditional,
            neiso_offer_surface_conditional=neiso_offer_surface_conditional,
            must_run_mw=must_run_total,
            inject_biomass_mustrun=inject_biomass,
            priced_interchange=priced_interchange,
            hydro_backfill_year=hydro_backfill_year,
            hydro_eia930_monthly=hydro_eia930_monthly,
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
            reliability_floor=reliability_floor,
            scarcity_price_overlay=scarcity_price_overlay,
            caiso_scarcity_pricing=caiso_scarcity_pricing,
            caiso_lcr_commitment_credit=caiso_lcr_commitment_credit,
            caiso_solar_deliverability=caiso_solar_deliverability,
            caiso_solar_deliverability_k=caiso_solar_deliverability_k,
            caiso_solar_endogenous_spill=caiso_solar_endogenous_spill,
            caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered,
            neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate,
            neiso_oil_burn_budget=neiso_oil_burn_budget,
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory,
            neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl,
            neiso_winter_fuel_mustrun=neiso_winter_fuel_mustrun,
            caiso_import_hub_prices=caiso_import_hub_prices,
            caiso_import_gas_coupling=caiso_import_gas_coupling,
            caiso_import_solar_shape=caiso_import_solar_shape,
            caiso_bidir_intertie=caiso_bidir_intertie,
            caiso_per_hub_intertie=caiso_per_hub_intertie,
            caiso_perhub_firm_base=caiso_perhub_firm_base,
            caiso_corridor_flow_limit=caiso_corridor_flow_limit,
            caiso_intertie_reference_price=caiso_intertie_reference_price,
            caiso_corridor_atc_forward=caiso_corridor_atc_forward,
            caiso_reference_price_seam=caiso_reference_price_seam,
            capacity_deliverability_limits=capacity_deliverability_limits,
            ramp_limits=ramp_limits,
            local_capacity_constraints=local_capacity_constraints,
            nyiso_local_selfsupply=nyiso_local_selfsupply,
            nyiso_firm_imports=nyiso_firm_imports,
            nyiso_import_reconciliation=nyiso_import_reconciliation,
            nyiso_import_hub_prices=nyiso_import_hub_prices,
            nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread,
            nyiso_synchronised_reserve=nyiso_synchronised_reserve,
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac,
            nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements,
            neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements,
            miso_firm_imports=miso_firm_imports,
            miso_seam_flow_limit=miso_seam_flow_limit,
            miso_seam_flow_percentile=miso_seam_flow_percentile,
            miso_seam_export_limit=miso_seam_export_limit,
            miso_pjm_border_anchor=miso_pjm_border_anchor,
            miso_cc_coal_rebalance=miso_cc_coal_rebalance,
            miso_firm_import_floor=miso_firm_import_floor,
            miso_pjm_lmp_import_pricing=miso_pjm_lmp_import_pricing,
            miso_seam_measured_ladder=miso_seam_measured_ladder,
            pjm_seam_flow_limit=pjm_seam_flow_limit,
            pjm_seam_flow_percentile=pjm_seam_flow_percentile,
            pjm_seam_export_limit=pjm_seam_export_limit,
            pjm_seam_measured_ladder=pjm_seam_measured_ladder,
            gas_hub_basis_overlay=gas_hub_basis_overlay,
            gas_st_netload_drag=gas_st_netload_drag,
            gas_st_drag_overrides=gas_st_drag_overrides,
            ct_netload_drag=ct_netload_drag,
            ct_drag_overrides=ct_drag_overrides,
            chp_export_floor_measured=chp_export_floor_measured,
            ercot_gtc_limits_measured=ercot_gtc_limits_measured,
            ercot_wtx_curtailment_driver=ercot_wtx_curtailment_driver,
            ercot_wtx_curtail_depth_wind=ercot_wtx_curtail_depth_wind,
            ercot_wtx_curtail_depth_solar=ercot_wtx_curtail_depth_solar,
            mass_cap_enabled=mass_cap_enabled,
            mass_cap_tons=mass_cap_tons,
            mass_cap_program=mass_cap_program,
            zero_forcing_ablation=zero_forcing_ablation,
        )
        if persist_p2_state:
            _save_p2_state(run_dir, year, p2_state)
        labelled = [("P2" if result_p1 is not None else "P1", result)]
        if result_p1 is not None:
            labelled.insert(0, ("P1", result_p1))
        # Per-pass min-gen floors + mechanism ids (D-2/D-4 attribution).
        _save_floor_arrays(run_dir, year, p2_state, result_p1 is not None)

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

        for label, res in labelled:
            passes_seen.add(label)
            _dispatch_frame(
                year,
                label,
                res,
                context,
                zone_names,
                iso=iso,
                must_run=must_run,
                oil_switch_mask=p2_state.get("dual_fuel_oil_mask"),
            ).to_parquet(run_dir / "dispatch" / f"{year}_{label}.parquet", index=False)
            system_frames.append(
                _system_frame(
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
                )
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
                )
            )

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
                )
            )
            if campd_year is not None:
                campd_frames.append(campd_year)

        # Release this year's solve state before the next year allocates its
        # own LP. A PJM per-plant year peaks ~13 GB inside HiGHS; carrying the
        # previous year's result/context/P2-state into the next build pushed a
        # 3-year backcast past 16 GB and into the OOM killer. Only the compact
        # per-year frames accumulated above survive the loop.
        del result, context, result_p1, p2_state, demand, must_run
        del must_run_total, labelled, res
        gc.collect()

    pd.concat(system_frames, ignore_index=True).to_parquet(
        run_dir / "system.parquet", index=False
    )
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
        "nysdec_peaker_rule_availability": nysdec_peaker_rule_availability,
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
        "coal_plant_monthly_pricing": backcast_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).coal_plant_monthly_pricing,
        "td_loss_factor": backcast_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).td_loss_factor,
        # ERCOT gas-basis mechanisms: env-var-gated inside backcast_config
        # (ERCOT_ZONAL_GAS / ERCOT_WEST_NETLOAD_GAS / ERCOT_GAS_FLOOR /
        # ERCOT_WEST_GAS_DELIVERED_FLOOR — no solve_and_persist kwarg exists
        # for them, rule 24 exception, plan §4). Meta-writer audit fix
        # (orchestrator-unification Stage 7): record the EFFECTIVE resolved
        # value the same way as coal_plant_monthly_pricing/td_loss_factor
        # above, so a run whose environment enabled one of these probes has
        # it in the reproducibility record instead of silently escaping it.
        "ercot_zonal_gas_basis": backcast_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).ercot_zonal_gas_basis,
        "ercot_west_netload_gas_shape": backcast_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).ercot_west_netload_gas_shape,
        "ercot_west_gas_delivered_floor": backcast_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).ercot_west_gas_delivered_floor,
        "storage_daily_cycling": storage_daily_cycling,
        "storage_vintage_ramp": storage_vintage_ramp,
        "strict_demand_profile": strict_demand_profile,
        "battery_dispatch_adder": battery_dispatch_adder,
        "as_reserve_withholding": as_reserve_withholding,
        "energy_reserve_coopt": energy_reserve_coopt,
        "miso_zonal_reserves": miso_zonal_reserves,
        "miso_reserve_pergen": miso_reserve_pergen,
        "miso_commitment_posture": miso_commitment_posture,
        "ercot_multiproduct_as_coopt": ercot_multiproduct_as_coopt,
        "ercot_ecrs_conservative_deployment": ercot_ecrs_conservative_deployment,
        "ercot_ordc_total_reserve": ercot_ordc_total_reserve,
        "ercot_ordc_cap_dual_adder": ercot_ordc_cap_dual_adder,
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
        "ercot_storage_as_endogenous": ercot_storage_as_endogenous,
        "ercot_storage_as_duration_gate": ercot_storage_as_duration_gate,
        "gas_offer_curve": gas_offer_curve,
        "gas_monthly_actuals": gas_monthly_actuals,
        "pjm_zonal_gas_basis": pjm_zonal_gas_basis,
        "miso_zonal_gas_basis": miso_zonal_gas_basis,
        "pjm_congestion": pjm_congestion,
        "offer_curve_overrides": offer_curve_overrides or {},
        "offer_curve_deltas": offer_curve_deltas or {},
        "curve_smoothing": curve_smoothing or {},
        "cc_derate_from_top": cc_derate_from_top,
        "cc_nameplate_summer_derate": cc_nameplate_summer_derate,
        "coal_nameplate_summer_derate": coal_nameplate_summer_derate,
        "temp_dependent_derate": temp_dependent_derate,
        "ercot_offer_surface_conditional": ercot_offer_surface_conditional,
        "neiso_offer_surface_conditional": neiso_offer_surface_conditional,
        "priced_interchange": priced_interchange,
        "hydro_backfill_year": hydro_backfill_year,
        "hydro_eia930_monthly": hydro_eia930_monthly,
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
        "reliability_floor": reliability_floor,
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
        "neiso_oil_burn_budget": neiso_oil_burn_budget,
        "neiso_winter_fuel_inventory": neiso_winter_fuel_inventory,
        "neiso_winter_fuel_start_fill_bbl": neiso_winter_fuel_start_fill_bbl,
        "neiso_winter_fuel_mustrun": neiso_winter_fuel_mustrun,
        "caiso_import_hub_prices": caiso_import_hub_prices,
        "caiso_import_gas_coupling": caiso_import_gas_coupling,
        "caiso_import_solar_shape": caiso_import_solar_shape,
        "caiso_bidir_intertie": caiso_bidir_intertie,
        "caiso_per_hub_intertie": caiso_per_hub_intertie,
        "caiso_perhub_firm_base": caiso_perhub_firm_base,
        "caiso_corridor_flow_limit": caiso_corridor_flow_limit,
        "caiso_intertie_reference_price": caiso_intertie_reference_price,
        "caiso_corridor_atc_forward": caiso_corridor_atc_forward,
        "caiso_reference_price_seam": caiso_reference_price_seam,
        "capacity_deliverability_limits": capacity_deliverability_limits,
        "ramp_limits": ramp_limits,
        "local_capacity_constraints": local_capacity_constraints,
        "nyiso_local_selfsupply": nyiso_local_selfsupply,
        "nyiso_firm_imports": nyiso_firm_imports,
        "nyiso_import_reconciliation": nyiso_import_reconciliation,
        "nyiso_import_hub_prices": nyiso_import_hub_prices,
        "nyiso_iroquois_winter_spread": nyiso_iroquois_winter_spread,
        "nyiso_synchronised_reserve": nyiso_synchronised_reserve,
        "nyiso_spin_headroom_frac": nyiso_spin_headroom_frac,
        "nyiso_dynamic_reserve_requirements": nyiso_dynamic_reserve_requirements,
        "neiso_dynamic_reserve_requirements": neiso_dynamic_reserve_requirements,
        "miso_firm_imports": miso_firm_imports,
        "miso_seam_flow_limit": miso_seam_flow_limit,
        "miso_seam_flow_percentile": miso_seam_flow_percentile,
        "miso_seam_export_limit": miso_seam_export_limit,
        "miso_pjm_border_anchor": miso_pjm_border_anchor,
        "miso_cc_coal_rebalance": miso_cc_coal_rebalance,
        "miso_firm_import_floor": miso_firm_import_floor,
        "miso_seam_measured_ladder": miso_seam_measured_ladder,
        "pjm_seam_flow_limit": pjm_seam_flow_limit,
        "pjm_seam_flow_percentile": pjm_seam_flow_percentile,
        "pjm_seam_export_limit": pjm_seam_export_limit,
        "pjm_seam_measured_ladder": pjm_seam_measured_ladder,
        "gas_hub_basis_overlay": gas_hub_basis_overlay,
        "chp_export_floor_measured": chp_export_floor_measured,
        "ercot_gtc_limits_measured": ercot_gtc_limits_measured,
        "ercot_wtx_curtailment_driver": ercot_wtx_curtailment_driver,
        "ercot_wtx_curtail_depth_wind": ercot_wtx_curtail_depth_wind,
        "ercot_wtx_curtail_depth_solar": ercot_wtx_curtail_depth_solar,
        "mass_cap_enabled": mass_cap_enabled,
        "mass_cap_tons": mass_cap_tons,
        "mass_cap_program": mass_cap_program,
        "btm_backfill_year": btm_backfill_year,
        "shared_inputs": shared_inputs,
        "git_sha": _git_sha(),
        # Solver provenance: near-tied offer-curve plateaus (e.g. cheap-gas
        # years putting PRB committed bids on top of gas committed bids)
        # admit alternate optimal vertices, and different HiGHS releases
        # pick different ones — class TWh can move several TWh at an
        # identical objective. Record the version so a non-reproducing
        # bundle can be traced to a solver upgrade.
        "highspy_version": _highspy_version(),
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, default=_json_default)
    )
    # Rebuild the recorded config WITH the same overrides + deltas applied, so
    # run_config.json's scenario_config.offer_curve_by_group is the exact
    # merged curve the LP solved against (not the bare defaults).
    recorded_cfg = backcast_config(
        years[0],
        iso,
        hours,
        gas_prices[years[0]],
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
        neiso_offer_surface_conditional=neiso_offer_surface_conditional,
    )
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
        recorded_cfg = recorded_cfg.with_overrides(coal_bit_passthrough_sigmoid=True)
    if bit_overrides:
        recorded_cfg = recorded_cfg.with_overrides(
            **{k: v for k, v in bit_overrides.items() if v is not None}
        )
    if coal_econ_srmc_bound:
        recorded_cfg = recorded_cfg.with_overrides(coal_econ_srmc_bound=True)
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
    if miso_reserve_pergen:
        recorded_cfg = recorded_cfg.with_overrides(miso_reserve_pergen=True)
    if miso_commitment_posture:
        recorded_cfg = recorded_cfg.with_overrides(miso_commitment_posture=True)
    if pjm_reserve_supply_cap:
        recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_supply_cap=True)
    if pjm_reserve_pergen:
        recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_pergen=True)
    if pjm_reserve_pergen_sync:
        recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_pergen_sync=True)
    if pjm_reserve_pergen_size_split:
        recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_pergen_size_split=True)
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
        recorded_cfg = recorded_cfg.with_overrides(pjm_reserve_commitment_scoped=True)
    if ercot_multiproduct_as_coopt:
        recorded_cfg = recorded_cfg.with_overrides(ercot_multiproduct_as_coopt=True)
    if ercot_ecrs_conservative_deployment:
        recorded_cfg = recorded_cfg.with_overrides(
            ercot_ecrs_conservative_deployment=True
        )
    if ercot_ordc_total_reserve:
        recorded_cfg = recorded_cfg.with_overrides(ercot_ordc_total_reserve=True)
    if ercot_storage_as_product_credit:
        recorded_cfg = recorded_cfg.with_overrides(ercot_storage_as_product_credit=True)
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
        recorded_cfg = recorded_cfg.with_overrides(ercot_reserve_supply_forward=True)
    if ercot_as_forward_requirement:
        recorded_cfg = recorded_cfg.with_overrides(ercot_as_forward_requirement=True)
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
            ercot_storage_as_reserve_from_year=int(ercot_storage_as_reserve_from_year),
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
    if ercot_storage_as_endogenous:
        recorded_cfg = recorded_cfg.with_overrides(ercot_storage_as_endogenous=True)
    if ercot_storage_as_duration_gate:
        recorded_cfg = recorded_cfg.with_overrides(ercot_storage_as_duration_gate=True)
    if battery_dispatch_adder:
        recorded_cfg = recorded_cfg.with_overrides(
            battery_dispatch_adder=battery_dispatch_adder
        )
    if gas_offer_curve:
        recorded_cfg = recorded_cfg.with_overrides(gas_offer_curve=True)
    if gas_monthly_actuals:
        recorded_cfg = recorded_cfg.with_overrides(gas_monthly_actuals=True)
    if pjm_zonal_gas_basis:
        recorded_cfg = recorded_cfg.with_overrides(pjm_zonal_gas_basis=True)
    if miso_zonal_gas_basis:
        recorded_cfg = recorded_cfg.with_overrides(miso_zonal_gas_basis=True)
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
        recorded_cfg = recorded_cfg.with_overrides(coal_nameplate_summer_derate=True)
    if gt_ambient_derate:
        # Mirror run_year so run_config.json records the GT ambient-derate knobs
        # (rule 25: every solve-changing tunable appears in the recorded config).
        _amb_rec = {"gt_ambient_derate": True}
        if gt_ambient_derate_ref_c is not None:
            _amb_rec["gt_ambient_derate_ref_c"] = float(gt_ambient_derate_ref_c)
        if gt_ambient_derate_slope_cc is not None:
            _amb_rec["gt_ambient_derate_slope_cc"] = float(gt_ambient_derate_slope_cc)
        if gt_ambient_derate_slope_ct is not None:
            _amb_rec["gt_ambient_derate_slope_ct"] = float(gt_ambient_derate_slope_ct)
        recorded_cfg = recorded_cfg.with_overrides(**_amb_rec)
    if temp_dependent_derate:
        # Mirror run_year so run_config.json records the switch (rule 25). The
        # per-class slopes/reference temps live in ScenarioConfig defaults, so
        # recording the boolean captures the full solve-changing configuration.
        recorded_cfg = recorded_cfg.with_overrides(temp_dependent_derate=True)
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
    if reliability_floor is not None:
        recorded_cfg = recorded_cfg.with_overrides(reliability_floor=reliability_floor)
    if chp_export_floor_measured:
        recorded_cfg = recorded_cfg.with_overrides(chp_export_floor_measured=True)
    if ercot_gtc_limits_measured:
        recorded_cfg = recorded_cfg.with_overrides(ercot_gtc_limits_measured=True)
    # WP-B curtailment driver — tri-state (ct_netload_drag pattern): None keeps
    # the backcast_config per-ISO default (ERCOT keeper default-ON, owner GO
    # 2026-07-07); explicit True/False force it, so ablation arms can scrub it.
    _wtx_over: dict = {}
    if ercot_wtx_curtailment_driver is not None:
        _wtx_over["ercot_wtx_curtailment_driver"] = bool(ercot_wtx_curtailment_driver)
    if ercot_wtx_curtail_depth_wind is not None:
        _wtx_over["ercot_wtx_curtail_depth_wind"] = float(ercot_wtx_curtail_depth_wind)
    if ercot_wtx_curtail_depth_solar is not None:
        _wtx_over["ercot_wtx_curtail_depth_solar"] = float(
            ercot_wtx_curtail_depth_solar
        )
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
    if neiso_oil_burn_budget is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            neiso_oil_burn_budget=neiso_oil_burn_budget
        )
    if neiso_winter_fuel_inventory is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory
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
    if caiso_bidir_intertie is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            caiso_bidir_intertie=caiso_bidir_intertie
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
    if nyiso_spin_headroom_frac is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac
        )
    if nyiso_dynamic_reserve_requirements is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements
        )
    if neiso_dynamic_reserve_requirements is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements
        )
    if miso_firm_imports is not None:
        recorded_cfg = recorded_cfg.with_overrides(miso_firm_imports=miso_firm_imports)
    if miso_seam_flow_limit:
        recorded_cfg = recorded_cfg.with_overrides(miso_seam_flow_limit=True)
    if miso_seam_flow_percentile is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            miso_seam_flow_percentile=float(miso_seam_flow_percentile)
        )
    if miso_seam_export_limit:
        recorded_cfg = recorded_cfg.with_overrides(miso_seam_export_limit=True)
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
        recorded_cfg = recorded_cfg.with_overrides(tranche_startup_amortization=True)
    if tranche_startup_measured_runs:
        recorded_cfg = recorded_cfg.with_overrides(tranche_startup_measured_runs=True)
    if nysdec_peaker_rule_availability:
        recorded_cfg = recorded_cfg.with_overrides(nysdec_peaker_rule_availability=True)
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
    if capacity_deliverability_limits is not None:
        recorded_cfg = recorded_cfg.with_overrides(
            capacity_deliverability_limits=capacity_deliverability_limits
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
    if zero_forcing_ablation:
        # Record the ablated config so run_config.json's scenario_config matches
        # what the LP actually solved (run_year applied the same transform). The
        # off-list is derived from the D-2 mechanism registry (rule 20).
        from market_sim.config.scenarios import ScenarioConfig

        recorded_cfg = ScenarioConfig.as_zero_forcing_ablation(recorded_cfg)
    write_run_config(run_dir, recorded_cfg, meta, note, ablation_of=ablation_of)
    logger.info("wrote calibration bundle to %s", run_dir)
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


def _save_p2_state(run_dir: Path, year: int, p2_state: dict) -> None:
    """Pickle the cached P1 inputs so P2 can be re-run as a post-process."""
    d = run_dir / "p2_state"
    d.mkdir(parents=True, exist_ok=True)
    with gzip.open(d / f"{year}.pkl.gz", "wb") as fh:
        pickle.dump(p2_state, fh, protocol=pickle.HIGHEST_PROTOCOL)


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
        with gzip.open(sp, "rb") as fh:
            state = pickle.load(fh)
        year = int(state["year"])
        cfg = state["config"].with_overrides(
            commitment_enabled=True,
            commitment_screen_coal=screen_coal,
        )
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
        btm_p2.append(_btm_frame(year, "P2", generation, iso=meta["iso"]))
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
    any modeled price (scripts/derive_import_tranches.py measured-only mode).
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

    e923f, e930f, campdf = [], [], []
    for year in years:
        if not is_ercot:
            group_by_code = _fleet_group_by_code(iso, iso_config, year)
        campd_year = _campd_hourly_frame(year, iso, parasitic_factors, hours)
        e930 = _eia930_frame(year, iso, iso_config)
        e923f.append(
            _benchmark_eia923_frame(
                year,
                generation,
                iso,
                campd_year,
                group_by_code,
                e930,
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
# config holdout score. Mirrors calibration-run.yml's workflow_dispatch gate
# (the GH-Actions UI path) and legitimacy_diagnostics.py's D6_CALIBRATION_YEARS
# / audit_keepers.py's CALIBRATION_YEARS (kept as separate literals per this
# repo's existing convention; a parity test asserts they agree).
HOLDOUT_CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})
HOLDOUT_MARKER_FILE = "frontend/data/backcast/calibration-complete.json"


def enforce_holdout_year_gate(
    years: list[int], iso: str, holdout_authorized: bool, repo: Path = REPO
) -> None:
    """Hard-fail a solve over a holdout year unless explicitly authorized.

    docs/handoffs/holdout-policy-memo-2026-07.md (b)(2): direct invocation of
    this script with ``--year 2022``/``--year 2026`` solved today with no
    code-level gate — only the GH-Actions ``workflow_dispatch`` wrapper
    (calibration-run.yml) validated the year. This closes that gap at the
    script entry point itself. Authorization requires BOTH ``--holdout-
    authorized`` on the command line AND the target ISO already carrying a
    ``calibration-complete`` marker (the marker is what turns a holdout year
    into an authorized one-shot score, never the flag alone).
    """
    breach = sorted(set(years) - HOLDOUT_CALIBRATION_YEARS)
    if not breach:
        return
    marker_path = repo / HOLDOUT_MARKER_FILE
    complete = {}
    if marker_path.exists():
        complete = json.loads(marker_path.read_text()).get("complete", {})
    marked = iso in complete
    if holdout_authorized and marked:
        logger.warning(
            "%s: solving designated holdout year(s) %s under "
            "--holdout-authorized (calibration-complete marker present) — "
            "the one-shot frozen-config holdout score (CLAUDE.md rule 22).",
            iso,
            breach,
        )
        return
    reason = (
        "--holdout-authorized not passed"
        if not holdout_authorized
        else f"no calibration-complete marker for {iso} in {HOLDOUT_MARKER_FILE}"
    )
    raise SystemExit(
        f"error: --year {breach} falls outside the calibration window "
        f"{sorted(HOLDOUT_CALIBRATION_YEARS)} for {iso} — {reason}. "
        "2022 and H1-2026 are under full quarantine (CLAUDE.md rule 22): no "
        "solves until the ISO's calibration-complete marker exists, and even "
        "then only the one-shot frozen-config score, authorized with both "
        "--holdout-authorized and the marker. See "
        "docs/handoffs/holdout-policy-memo-2026-07.md."
    )


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


def run_replay_bundle(
    bundle: Path,
    out_dir: Path | None,
    years: list[int] | None,
    note: str,
    holdout_authorized: bool,
    zero_forcing_ablation: bool = False,
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
        years: Optional solve-span override (defaults to the bundle's years);
            holdout-gated either way (rule 22).
        note: Provenance note recorded in ``run_config.json`` (empty keeps
            the replay default).
        holdout_authorized: Forwarded to :func:`enforce_holdout_year_gate`.
        zero_forcing_ablation: Solve the recipe's D-3 zero-forcing ablation
            twin instead (composes exactly like the flag on a direct solve).
    """
    import replay_keeper as rk

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], holdout_authorized)
    kwargs["reference"] = _load_reference()
    if out_dir is not None:
        kwargs["run_dir"] = out_dir
    if note:
        kwargs["note"] = note
    kwargs["zero_forcing_ablation"] = zero_forcing_ablation
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
        "--holdout-authorized",
        action="store_true",
        help="Authorize a solve over a designated holdout year (2022, "
        "H1-2026) outside the 2023-2025 calibration window. Also requires "
        "the target ISO to already carry a calibration-complete marker in "
        "frontend/data/backcast/calibration-complete.json — the one-shot "
        "frozen-config holdout score (CLAUDE.md rule 22). Without both, "
        "--year outside 2023-2025 hard-fails. See "
        "docs/handoffs/holdout-policy-memo-2026-07.md.",
    )
    parser.add_argument(
        "--iso",
        default="ERCOT",
        help="ISO to backcast. ERCOT runs the full plant-level diagnostic; "
        "other ISOs (e.g. PJM) run energy-only (generic fuel-mix / price "
        "/ interchange report; ERCOT-only steps skipped).",
    )
    parser.add_argument("--hours", type=int, default=_HOURS_PER_YEAR)
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
    parser.add_argument(
        "--coal-lignite-mustrun",
        type=float,
        default=None,
        help="Override mine-mouth lignite coal must-run %% (sweep knob).",
    )
    parser.add_argument(
        "--coal-prb-mustrun",
        type=float,
        default=None,
        help="Override PRB coal must-run %% (sweep knob).",
    )
    parser.add_argument(
        "--coal-prb-passthrough",
        type=float,
        default=1.0,
        help="PRB above-must-run fuel passthrough (1.0 = off).",
    )
    parser.add_argument(
        "--outage-source",
        choices=["historic", "statistical"],
        default="historic",
        help="Coal/CC availability: 'historic' overlays actual >10-day ERCOT "
        "outages (default backcast); 'statistical' uses WEFOR/POF only.",
    )
    # Locked calibration config ("tier pass 2"): per-plant CAMPD coal must-run,
    # gas-keyed PRB passthrough sigmoid (tiered baseload/follower), POF dropped
    # on coal. All on by default; use the --no-* form to disable.
    parser.add_argument(
        "--coal-prb-sigmoid",
        "--prb-passthrough-sigmoid",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="coal_prb_sigmoid",
        help="Gas-key the PRB passthrough: a logistic of the monthly gas "
        "price replaces the flat --coal-prb-passthrough (deep discount "
        "when gas is cheap, none/markup when dear). Params resolve "
        "from the per-ISO COAL_SIGMOID_DEFAULTS curve; no curve for "
        "the ISO = flat passthrough. (--prb-passthrough-sigmoid is "
        "the legacy spelling.)",
    )
    parser.add_argument(
        "--coal-mustrun-per-plant",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use per-plant CAMPD-derived coal must-run floors "
        "(fleet.COAL_MUSTRUN_BY_PLANT) instead of uniform lignite/PRB "
        "must-run overrides.",
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
        "--ct-deployment",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Inject the per-plant CT_PEAKER AS/RUC-deployment hourly floor "
        "(outages.ct_deployment_floor_for_year, built by "
        "scripts/derive_ct_deployment.py): in the measured out-of-merit "
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
        "scripts/derive_reliability_deployment.py): the generalization of "
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
        "--coal-drop-pof",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Drop the statistical planned-outage (POF) derate on coal "
        "(planned maintenance comes from the historic outage overlay); "
        "keep WEFOR in non-summer months and the derate all year.",
    )
    parser.add_argument(
        "--coal-mustrun-online-pmin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Size the coal must-run band to the measured online-net-MW "
        "synchronization Pmin (thermal_tranches mustrun_online_pct) instead "
        "of the take-or-pay contract floor. Pairs with "
        "--coal-sync-srmc-tranche to hold units synchronized at their "
        "measured online minimum.",
    )
    parser.add_argument(
        "--coal-sync-srmc-tranche",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Split the coal online-Pmin band into a fuel-free contracted "
        "_mustrun tranche and a full-SRMC _sync tranche, and force both on "
        "(scaled by the measured online fraction) so coal holds at its "
        "measured synchronization floor instead of price-following to zero. "
        "Requires --coal-mustrun-online-pmin.",
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
        "start-to-stop run length (scripts/derive_campd_ct_run_lengths.py "
        "artifact, pooled 2023-2025, ISO-class fallback) as the horizon "
        "ceiling - the endogenous P0 run may only SHORTEN it. Removes the v2 "
        "circularity where too-cheap offers -> long P0 blocks -> ~0 markup "
        "-> the lever self-disables (nyiso-44 probe finding). CC peak bands "
        "keep the v2 P0 basis. Default OFF.",
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
        "— the CI-dispatchable replay for calibration-run.yml (extra_flags). "
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
    # Gas-keyed bituminous passthrough sigmoid (PJM coal fleet). Off by
    # default — turning it on replaces full fuel cost on bituminous
    # above-must-run tranches with a logistic of the monthly delivered gas
    # price (the measured EIA-923 series when --gas-monthly-actuals is on).
    parser.add_argument(
        "--coal-bit-sigmoid",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Gas-key the bituminous coal passthrough: above-must-run bit "
        "tranches get a fuel discount when gas is cheap and a markup "
        "when dear (coal_bit_passthrough_* params), tracking the "
        "bit-vs-gas-CC merit-order crossover. Off = full fuel cost.",
    )
    # Marginal-coal measured-SRMC offer bound: the econ*/peak coal tranches
    # buy fuel at market, so their offers are clamped to >= full measured
    # delivered fuel cost (passthrough >= 1.0); the committed/must-run bands
    # keep the contracted take-or-pay discount. Removes the sigmoid's fitted
    # discount from the marginal tranches (FINDING-miso-burndown-2026-07.md
    # Evidence 2). Off by default (existing keepers unchanged).
    parser.add_argument(
        "--coal-econ-srmc-bound",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Clamp marginal (econ*/peak) coal tranche fuel passthrough to "
        ">= 1.0 so no marginal coal offer sits below the plant's measured "
        "incremental delivered SRMC. Committed/must-run bands keep their "
        "take-or-pay discount.",
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
        "--coal-lignite-sigmoid",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Gas-key the lignite coal passthrough: above-must-run lignite "
        "tranches get a fuel discount when gas is cheap (mine-mouth "
        "take-or-pay fixed costs are sunk) rising to full cost when "
        "dear (coal_lignite_passthrough_* params), tracking the "
        "lignite-vs-gas-CC merit-order crossover. Off = full fuel cost.",
    )
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
        "--coal-sub-sigmoid",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Gas-key the subbituminous coal passthrough on its own curve "
        "(coal_sub_passthrough_* params / per-ISO defaults). "
        "Off = full fuel cost.",
    )
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
        "--coal-waste-sigmoid",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Gas-key the waste-coal passthrough on its own curve "
        "(coal_waste_passthrough_* params / per-ISO defaults). "
        "Off = full fuel cost.",
    )
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
        "--coal-warm-committed",
        action="store_true",
        help="Exempt CAMPD coal committed tranches from the P1 startup"
        "-amortization markup when the plant has a must-run floor: the "
        "mustrun tranche keeps the boiler online, so committed-band "
        "dispatch is a hot-unit ramp, not a cold start. Off (default) "
        "keeps the legacy $100/MW coal start markup, which prices the "
        "committed band above the econ ramp (the run-97b inversion).",
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
        "scripts/build_ercot_as_withholding.py) from thermal headroom "
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
        "--cc-capacity-reconcile",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Reconcile listed CC plants' LP capacity to their demonstrated "
        "CAMPD value from the per-ISO table "
        "data/raw/_processed-legacy/cc_capacity_reconcile_<ISO>.csv "
        "(scripts/derive_cc_capacity_reconcile.py; mode=cap rows bound a "
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
        "--caiso-bidir-intertie",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Model CAISO's WECC tie as a SINGLE signed flow (one net direction "
        "per hour over a shared directional cap, import ≤ ~8.3 GW / export ≤ "
        "~3.5 GW) instead of the legacy two independent one-way mechanisms "
        "(priced import tranches + separate export sinks on the same external "
        "node, which let the LP import the cheap midday hub AND stay long on its "
        "own solar — 2024 diurnal interchange corr −0.65). Both legs are priced "
        "off the same measured hub: import = hub + per-tranche border carbon, "
        "export = hub, so they are arbitrage-free by construction and the tie "
        "reverses to export in the midday solar glut (positive diurnal sign). "
        "Supersedes --caiso-import-hub-prices / --caiso-import-gas-coupling / "
        "--caiso-import-solar-shape when set. CAISO-only; pure LP; 2023 falls "
        "back to the static ladder (no measured hub). Default (unset) keeps the "
        "base config value (off).",
    )
    parser.add_argument(
        "--caiso-per-hub-intertie",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Model CAISO's WECC tie as TWO per-hub signed corridors — COI/"
        "Path-66 at the Malin hub (→ NP15, north) and Path-46/WOR at the Palo "
        "Verde hub (→ SP15, south) — each a single net direction over its OWN "
        "real link, priced at its OWN measured intertie hub. The unification of "
        "--caiso-bidir-intertie (single signed flow → per-hub netting, fixes the "
        "inverted diurnal sign) and --caiso-import-hub-prices (per-hub basis): "
        "the bidir node had to average the two hubs into one price; the hub-price "
        "node kept the basis but pooled both legs onto one bubble (cheap Palo "
        "Verde midday fills the whole 8.3 GW budget, never nets → over-import + "
        "inverted diurnal). Two per-hub legs recover both, so the Palo Verde "
        "corridor reverses to EXPORT midday instead of over-importing. The 8.3 GW "
        "simultaneous-import cap stays as the WECC_import_simultaneous interface "
        "limit re-homed to the two links. Supersedes --caiso-import-hub-prices / "
        "--caiso-bidir-intertie / --caiso-import-solar-shape (measured per-hub "
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
        "scripts/derive_pjm_seam_ladders.py: PJM settlement-grade tie-line "
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
        "scripts/derive_miso_seam_ladders.py: EIA-930 per-seam flow duration "
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
        "--class-commitment-overrides",
        default=None,
        metavar="JSON",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        # Per-class P2 commitment-screen overrides, keyed by plant_group (e.g.
        # '{"ST_GAS":{"min_run_hours":48,"min_down_hours":12}}').
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    apply_statistical_mode(args)
    _enforce_legacy_p2_gate(parser, args)

    offer_curve_overrides = _parse_offer_curve_json(args.offer_curve_json)
    offer_curve_deltas = _parse_offer_curve_json(
        args.offer_curve_delta_json, flag="--offer-curve-delta-json"
    )
    class_commitment_overrides = None
    if args.class_commitment_overrides:
        import json as _json

        class_commitment_overrides = _json.loads(args.class_commitment_overrides)

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
            holdout_authorized=args.holdout_authorized,
            zero_forcing_ablation=args.zero_forcing_ablation,
        )
        return

    iso = args.iso.upper()
    enforce_holdout_year_gate(args.year, iso, args.holdout_authorized)
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
    run_dir = solve_and_persist(
        args.year,
        iso,
        args.hours,
        reference,
        commitment=args.commitment,
        screen_coal=not args.no_coal_p2,
        run_dir=run_dir,
        coal_lignite_mustrun=args.coal_lignite_mustrun,
        coal_prb_mustrun=args.coal_prb_mustrun,
        coal_prb_passthrough=args.coal_prb_passthrough,
        persist_p2_state=args.persist_p2_state,
        outage_source=args.outage_source,
        coal_prb_passthrough_sigmoid=args.coal_prb_sigmoid,
        coal_mustrun_per_plant=args.coal_mustrun_per_plant,
        ct_mustrun_per_plant=args.ct_mustrun_per_plant,
        ct_mustrun_floor_frac=args.ct_mustrun_floor_frac,
        coal_drop_pof=args.coal_drop_pof,
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
            "coal_warm_committed": True if args.coal_warm_committed else None,
            "committed_ramp_spread": args.committed_ramp_spread,
            "cc_duct_peaking": True if args.cc_duct_peaking else None,
            # Per-plant EIA-860 duct-burner shares supersede the 4-plant
            # hardcoded ERCOT peaking override, so turn it off when on.
            "cc_peaking_per_plant": False if args.cc_duct_peaking else None,
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
        coal_mustrun_online_pmin=args.coal_mustrun_online_pmin,
        coal_sync_srmc_tranche=args.coal_sync_srmc_tranche,
        ct_intermediate_split=args.ct_intermediate_split,
        ct_intermediate_cf_threshold=args.ct_intermediate_cf_threshold,
        cc_intermediate_split=args.cc_intermediate_split,
        tranche_startup_amortization=args.tranche_startup_amortization,
        tranche_startup_measured_runs=args.tranche_startup_measured_runs,
        nysdec_peaker_rule_availability=args.nysdec_peaker_rule_availability,
        oil_primary_bin_fuel=args.oil_primary_bin_fuel,
        cc_intermediate_cf_threshold=args.cc_intermediate_cf_threshold,
        st_gas_intermediate=args.st_gas_intermediate,
        st_gas_intermediate_cf_threshold=args.st_gas_intermediate_cf_threshold,
        coal_bit_sigmoid=args.coal_bit_sigmoid,
        coal_econ_srmc_bound=args.coal_econ_srmc_bound,
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
        miso_reserve_pergen=args.miso_reserve_pergen,
        miso_commitment_posture=args.miso_commitment_posture,
        pjm_reserve_pergen=args.pjm_reserve_pergen,
        pjm_reserve_pergen_sync=args.pjm_reserve_pergen_sync,
        pjm_reserve_pergen_size_split=args.pjm_reserve_pergen_size_split,
        pjm_commitment_posture=args.pjm_commitment_posture,
        measured_ramp_capability=args.measured_ramp_capability,
        ercot_multiproduct_as_coopt=args.ercot_multiproduct_as_coopt,
        ercot_ordc_total_reserve=args.ercot_ordc_total_reserve,
        ercot_ordc_cap_dual_adder=args.ercot_ordc_cap_dual_adder,
        ercot_storage_as_product_credit=args.ercot_storage_as_product_credit,
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
        ercot_storage_as_endogenous=args.ercot_storage_as_endogenous,
        ercot_storage_as_duration_gate=args.ercot_storage_as_duration_gate,
        ercot_ecrs_conservative_deployment=args.ercot_ecrs_conservative_deployment,
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
        priced_interchange=(
            True
            if reference_price_interface and args.priced_interchange is not False
            else resolve_priced_interchange(args.priced_interchange, iso)
        ),
        hydro_backfill_year=args.hydro_backfill_year,
        hydro_eia930_monthly=args.hydro_eia930_monthly,
        hydro_forecast_budget=args.hydro_forecast_budget,
        hydro_year=args.hydro_year,
        interchange_shaping=args.interchange_shaping,
        interchange_shaping_export_only=args.interchange_shaping_export_only,
        reference_price_interface=reference_price_interface,
        negative_renewable_offers=args.negative_renewable_offers,
        caiso_gas_commitment_floor=args.caiso_gas_commitment_floor,
        caiso_gas_floor_frac=args.caiso_gas_floor_frac,
        caiso_ra_mustoffer=args.caiso_ra_mustoffer,
        caiso_ra_min_load_frac=args.caiso_ra_min_load_frac,
        caiso_ra_startup_bridge=args.caiso_ra_startup_bridge,
        caiso_ra_bridge_decommit=args.caiso_ra_bridge_decommit,
        reliability_floor=args.reliability_floor,
        scarcity_price_overlay=args.scarcity_price_overlay,
        caiso_scarcity_pricing=args.caiso_scarcity_pricing,
        caiso_lcr_commitment_credit=args.caiso_lcr_commitment_credit,
        caiso_solar_deliverability=args.caiso_solar_deliverability,
        caiso_solar_deliverability_k=args.caiso_solar_deliverability_k,
        caiso_solar_endogenous_spill=args.caiso_solar_endogenous_spill,
        caiso_solar_cap_at_delivered=args.caiso_solar_cap_at_delivered,
        neiso_gas_coldsnap_derate=args.neiso_gas_coldsnap_derate,
        neiso_oil_burn_budget=args.neiso_oil_burn_budget,
        neiso_winter_fuel_inventory=args.neiso_winter_fuel_inventory,
        neiso_winter_fuel_start_fill_bbl=args.neiso_winter_fuel_start_fill_bbl,
        neiso_winter_fuel_mustrun=args.neiso_winter_fuel_mustrun,
        caiso_import_hub_prices=args.caiso_import_hub_prices,
        caiso_import_gas_coupling=args.caiso_import_gas_coupling,
        caiso_import_solar_shape=args.caiso_import_solar_shape,
        caiso_bidir_intertie=args.caiso_bidir_intertie,
        caiso_per_hub_intertie=args.caiso_per_hub_intertie,
        caiso_perhub_firm_base=args.caiso_perhub_firm_base,
        caiso_corridor_flow_limit=args.caiso_corridor_flow_limit,
        caiso_intertie_reference_price=args.caiso_intertie_reference_price,
        caiso_corridor_atc_forward=args.caiso_corridor_atc_forward,
        caiso_reference_price_seam=args.caiso_reference_price_seam,
        capacity_deliverability_limits=args.capacity_deliverability_limits,
        ramp_limits=args.ramp_limits,
        local_capacity_constraints=args.local_capacity_constraints,
        ct_netload_drag=args.ct_netload_drag,
        nyiso_local_selfsupply=args.nyiso_local_selfsupply,
        nyiso_firm_imports=args.nyiso_firm_imports,
        nyiso_import_reconciliation=args.nyiso_import_reconciliation,
        nyiso_import_hub_prices=args.nyiso_import_hub_prices,
        nyiso_iroquois_winter_spread=args.nyiso_iroquois_winter_spread,
        nyiso_synchronised_reserve=args.nyiso_synchronised_reserve,
        nyiso_spin_headroom_frac=args.nyiso_spin_headroom_frac,
        nyiso_dynamic_reserve_requirements=args.nyiso_dynamic_reserve_requirements,
        neiso_dynamic_reserve_requirements=args.neiso_dynamic_reserve_requirements,
        miso_firm_imports=miso_firm_imports,
        miso_seam_flow_limit=args.miso_seam_flow_limit,
        miso_seam_flow_percentile=args.miso_seam_flow_percentile,
        miso_seam_export_limit=args.miso_seam_export_limit,
        miso_pjm_border_anchor=args.miso_pjm_border_anchor,
        miso_cc_coal_rebalance=args.miso_cc_coal_rebalance,
        miso_firm_import_floor=args.miso_firm_import_floor,
        miso_pjm_lmp_import_pricing=args.miso_pjm_lmp_import_pricing,
        miso_seam_measured_ladder=args.miso_seam_measured_ladder,
        miso_zonal_gas_basis=args.miso_zonal_gas_basis,
        pjm_seam_flow_limit=args.pjm_seam_flow_limit,
        pjm_seam_flow_percentile=args.pjm_seam_flow_percentile,
        pjm_seam_export_limit=args.pjm_seam_export_limit,
        pjm_seam_measured_ladder=args.pjm_seam_measured_ladder,
        gas_hub_basis_overlay=args.gas_hub_basis_overlay,
        btm_backfill_year=args.btm_backfill_year,
        mass_cap_enabled=args.mass_cap_enabled,
        mass_cap_tons=args.mass_cap_tons,
        mass_cap_program=args.mass_cap_program,
        zero_forcing_ablation=args.zero_forcing_ablation,
        ablation_of=ablation_of,
        note=args.note,
    )
    report_run(run_dir, band_width=args.cf_band_width)


if __name__ == "__main__":
    main()
