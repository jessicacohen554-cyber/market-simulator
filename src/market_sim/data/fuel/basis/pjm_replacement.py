"""PJM REPLACEMENT-COST fuel for dispatch offers (PJM-NEXT-13; owner ruling 2026-09-29).

Gated on ``ScenarioConfig.pjm_replacement_cost_fuel`` (default off, byte-identical off).
When armed, every PJM gas row and every priceable coal row is re-priced at
**replacement cost**: the traded commodity plus measured variable transport. The
average delivered EIA-923 print is no longer used as the price. That print carries
reservation/demand charges and contract commodity prices amortized over the month's
takes, which is an average cost on a basis misaligned to a dispatch offer (rule 14
``[R-ACCURATE]`` misalignment clause; ``docs/FINDING-pjm-next-13-...``, card 2).

* **Gas.** ``(hub[region, month] + v[plant])`` times the row's own incoming within-month
  shape (mean-preserving, so the daily Henry Hub shape the incoming series carries is
  kept and only the monthly LEVEL is replaced).
  * ``hub``: the IMM's digitized Platts monthly spot for the owner-ruled region of the
    row's zone (east / west / production gas).
  * ``v``: the plant's measured variable transport, from
    ``data/raw/reference/pjm_gas_variable_transport.csv`` (frozen derive,
    ``scripts/data/derive_pjm_replacement_fuel.py``). The ladder is own -> (zone, class)
    -> class -> PJM-wide.
* **Coal (COAL_BIT / COAL_PRB rows).** ``sum_b s_b (spot_b[month] + t_b) + s_u x
  current``, times the same within-month shape.
  * ``s_b`` / ``t_b``: the plant-year's measured basin shares and EIA transport per MMBtu
    (``data/raw/reference/pjm_coal_replacement.csv``).
  * ``s_u``: the unpriced share (a basin with no IMM spot, a mine-mouth or untabulated
    mode, an unmatched mine). It keeps the plant's own price, so the construction is
    never extended where no measured commodity exists.
  * A plant absent from the table is untouched.

Rule 19 ``[R-ONE-MECH]``: this REPLACES the level channels it covers, never stacks.
* The written-cell mask it returns joins the print-derived mask, so the mean-zero PJM
  zonal basis is not added on top: the regional hub already carries the gradient. The
  PJM basis applier honours the mask under this flag.
* The gas-keyed coal passthrough sigmoids are the incumbent proxy for coal's
  opportunity cost against gas, so arming this with any of them on is a HARD ERROR.

Rule 25: PJM-only, and arming on another ISO is a hard error. Rule 13: a traded hub
plus a measured tariff wedge regenerates for a forward year from forward drivers. It
is also the forecast path's own hub + basis convention. This backcast overlay fails
CLOSED for a year the IMM series does not cover (never a silent no-op).
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _COAL_FUEL_IDX,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _month_index,
    logger,
)

#: The IMM's digitized Platts monthly spot rows (``som-competitive-conduct``).
IMM_SPOT_PATH: Path = (
    RAW_DATA_DIR / "som-competitive-conduct/som_competitive_conduct.csv"
)
IMM_SPOT_METRIC = "spot_price_digitized_usd_per_mmbtu"
GAS_TRANSPORT_PATH: Path = RAW_DATA_DIR / "reference/pjm_gas_variable_transport.csv"
COAL_REPLACEMENT_PATH: Path = RAW_DATA_DIR / "reference/pjm_coal_replacement.csv"

#: The owner-ruled zone -> IMM gas region map (PJM-NEXT-13 decision card, 2026-09-29).
#: Identical to ``scripts/data/derive_pjm_replacement_fuel.ZONE_GAS_REGION`` (pinned by
#: test), so ``v`` is measured against the very hub it is added to.
PJM_ZONE_GAS_REGION: dict[str, str] = {
    "PJM_EMAAC": "east_gas",
    "PJM_SWMAAC": "east_gas",
    "PJM_Dominion": "east_gas",
    "PJM_ComEd": "west_gas",
    "PJM_AEP_Ohio": "west_gas",
    "PJM_ATSI": "west_gas",
    "PJM_West_APS": "production_gas",
    "PJM_Central_PA": "production_gas",
}
#: Coal classes the coal leg prices (COAL_WC waste coal has no traded commodity).
PJM_REPLACEMENT_COAL_GROUPS: tuple[str, ...] = ("COAL_BIT", "COAL_PRB")
#: The gas-keyed coal passthrough gates this mechanism supersedes (rule 19).
_SUPERSEDED_COAL_GATES: tuple[str, ...] = (
    "coal_bit_passthrough_sigmoid",
    "coal_prb_passthrough_sigmoid",
    "coal_prb_passthrough_tiered",
)

_CACHE: dict[tuple, object] = {}


def _rows(path: Path) -> list[dict[str, str]]:
    """CSV rows of a reference table, ``#`` comment lines skipped."""
    with Path(path).open() as handle:
        return list(csv.DictReader(ln for ln in handle if not ln.startswith("#")))


def imm_spot_monthly(year: int, path: Path | None = None) -> dict[str, np.ndarray]:
    """``{segment: length-12 $/MMBtu}`` for every IMM spot segment complete in ``year``."""
    key = ("imm", str(path or IMM_SPOT_PATH), year)
    if key not in _CACHE:
        out: dict[str, np.ndarray] = {}
        for r in _rows(path or IMM_SPOT_PATH):
            if (
                r["iso"] != "PJM"
                or r["metric"] != IMM_SPOT_METRIC
                or int(r["year"]) != year
                or not r["period"].startswith("month_")
            ):
                continue
            arr = out.setdefault(r["fleet_segment"], np.full(12, np.nan))
            arr[int(r["period"][-2:]) - 1] = float(r["value"])
        _CACHE[key] = {k: v for k, v in out.items() if np.isfinite(v).all()}
    return _CACHE[key]  # type: ignore[return-value]


def _gas_transport(path: Path | None = None) -> tuple[dict, dict, dict, float]:
    """``(by (plant, group), by zone|group, by group, PJM-wide)`` transport rungs."""
    p = Path(path or GAS_TRANSPORT_PATH)
    key = ("gas", str(p))
    if key not in _CACHE:
        by_pg = {
            (int(r["plant_id"]), r["group"]): float(r["v_usd_mmbtu"]) for r in _rows(p)
        }
        by_p: dict[int, float] = {}
        for (pid, _g), v in by_pg.items():
            by_p.setdefault(pid, v)
        zg: dict[str, float] = {}
        gr: dict[str, float] = {}
        wide = 0.0
        for r in _rows(p.with_suffix(".pool.csv")):
            v = float(r["v_usd_mmbtu"])
            if r["rung"] == "zone_group":
                zg[r["key"]] = v
            elif r["rung"] == "group":
                gr[r["key"]] = v
            else:
                wide = v
        _CACHE[key] = ((by_pg, by_p), zg, gr, wide)
    return _CACHE[key]  # type: ignore[return-value]


def gas_transport_vector(
    fleet: FleetArrays, rows: np.ndarray, zone_names, path: Path | None = None
) -> np.ndarray:
    """Per-row gas variable transport ($/MMBtu), the declared ladder applied."""
    (by_pg, by_p), zg, gr, wide = _gas_transport(path)
    groups = getattr(fleet, "plant_group", None)
    out = np.empty(rows.size, dtype=float)
    for i, g in enumerate(rows):
        group = str(groups[g]) if groups is not None else ""
        try:
            code = int(fleet.plant_code[g]) if fleet.plant_code is not None else 0
        except (TypeError, ValueError):
            code = 0
        if (code, group) in by_pg:
            out[i] = by_pg[(code, group)]
        elif code in by_p:
            out[i] = by_p[code]
        else:
            zone = zone_names[int(fleet.zone_idx[g])]
            out[i] = zg.get(f"{zone}|{group}", gr.get(group, wide))
    return out


def coal_replacement_terms(year: int, path: Path | None = None) -> dict[int, tuple]:
    """``{plant: ([(segment, share, transport $/MMBtu)], unpriced share)}`` for ``year``."""
    p = Path(path or COAL_REPLACEMENT_PATH)
    key = ("coal", str(p), year)
    if key not in _CACHE:
        out: dict[int, list] = {}
        for r in _rows(p):
            if int(r["year"]) != year:
                continue
            ent = out.setdefault(int(r["plant_id"]), [[], 0.0])
            if r["spot_segment"] == "UNPRICED":
                ent[1] = max(0.0, float(r["share"]))
            else:
                ent[0].append(
                    (
                        r["spot_segment"],
                        float(r["share"]),
                        float(r["transport_usd_mmbtu"]),
                    )
                )
        _CACHE[key] = {k: (v[0], v[1]) for k, v in out.items()}
    return _CACHE[key]  # type: ignore[return-value]


def _month_means(block: np.ndarray, month: np.ndarray) -> np.ndarray:
    """Row-wise mean of ``block`` within each calendar month -> ``(n, 12)``."""
    out = np.zeros((block.shape[0], 12))
    for m in range(12):
        sel = month == m
        if sel.any():
            out[:, m] = block[:, sel].mean(axis=1)
    return out


def _reshape_level(
    block: np.ndarray, level: np.ndarray, month: np.ndarray
) -> np.ndarray:
    """Replace each row's monthly LEVEL by ``level`` (n, 12), keeping its within-month shape."""
    mm = _month_means(block, month)
    ratio = np.divide(
        block, mm[:, month], out=np.ones_like(block), where=mm[:, month] > 0
    )
    return level[:, month] * ratio


def apply_pjm_replacement_cost_fuel(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
) -> np.ndarray | None:
    """Re-price PJM gas and priceable coal at replacement cost; return the written mask.

    Returns ``None`` (nothing written, byte-identical) when the flag is off. Mutates
    ``fuel_prices`` in place. Raises ``ValueError``:
    * when armed on a non-PJM config (rule 25);
    * when armed with a superseded coal passthrough gate on (rule 19);
    * when ``year`` has no complete IMM monthly spot for a region a row needs (fail
      closed).
    """
    if not getattr(config, "pjm_replacement_cost_fuel", False):
        return None
    if config.iso != "PJM":
        raise ValueError(
            f"pjm_replacement_cost_fuel is PJM-only (rule 25); armed on {config.iso}"
        )
    live = [g for g in _SUPERSEDED_COAL_GATES if getattr(config, g, False)]
    if live:
        raise ValueError(
            "pjm_replacement_cost_fuel supersedes the gas-keyed coal passthrough "
            f"(rule 19); disarm {live} to arm it"
        )
    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    spot = imm_spot_monthly(year)
    n, hours = fuel_prices.shape
    month = _month_index(hours)
    mask = np.zeros(fuel_prices.shape, dtype=bool)
    # Rows in a zone outside the topology's named zones (the external/import
    # node) carry no region and are never repriced.
    zone_of = np.array(
        [
            zone_names[int(z)] if 0 <= int(z) < len(zone_names) else ""
            for z in fleet.zone_idx
        ],
        dtype=object,
    )

    # Gas leg.
    region = np.array([PJM_ZONE_GAS_REGION.get(z, "") for z in zone_of], dtype=object)
    gas = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX) & (region != ""))[0]
    if gas.size:
        need = sorted(set(region[gas]))
        missing = [r for r in need if r not in spot]
        if missing:
            raise ValueError(
                f"pjm_replacement_cost_fuel {year}: no complete IMM monthly spot for "
                f"{missing} (fail closed; data/raw/som-competitive-conduct)"
            )
        v = gas_transport_vector(fleet, gas, zone_names)
        level = np.vstack([spot[r] for r in region[gas]]) + v[:, None]
        new = _reshape_level(fuel_prices[gas, :], level, month)
        fuel_prices[gas, :] = np.maximum(new, _GAS_PRICE_FLOOR)
        mask[gas, :] = True

    # Coal leg.
    groups = np.asarray(getattr(fleet, "plant_group", np.full(n, "")), dtype=object)
    coal = np.nonzero(
        (np.asarray(fleet.fuel_type_idx) == _COAL_FUEL_IDX)
        & np.isin(groups, PJM_REPLACEMENT_COAL_GROUPS)
    )[0]
    terms = coal_replacement_terms(year)
    written_coal = []
    for g in coal:
        try:
            code = int(fleet.plant_code[g])
        except (TypeError, ValueError):
            continue
        if code not in terms:
            continue
        parts, unpriced = terms[code]
        if not parts:
            continue
        miss = [s for s, _sh, _t in parts if s not in spot]
        if miss:
            raise ValueError(
                f"pjm_replacement_cost_fuel {year}: no complete IMM coal spot for {miss}"
            )
        row = fuel_prices[g : g + 1, :]
        cur = _month_means(row, month)[0]
        lvl = sum(sh * (spot[s] + t) for s, sh, t in parts) + unpriced * cur
        fuel_prices[g, :] = _reshape_level(row, lvl[None, :], month)[0]
        mask[g, :] = True
        written_coal.append(g)
    logger.info(
        "PJM replacement-cost fuel (%d): %d gas rows repriced (regions %s), "
        "%d coal rows repriced",
        year,
        gas.size,
        sorted(set(region[gas])) if gas.size else [],
        len(written_coal),
    )
    return mask
