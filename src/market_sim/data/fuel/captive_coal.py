"""Captive-mine coal: the marginal (non-captive) delivered price at mixed-source plants.

``ScenarioConfig.coal_captive_marginal_fuel_price`` (NWPP-NEXT-15, owner ruling
2026-09-30 "Build, no threshold"; design
``docs/records/nwpp/DESIGN-nwppnext14-captive-mine-marginal-fuel-2026-09-30.md``,
identification rule and census
``docs/records/nwpp/PHASE0-nwppnext15-captive-mine-2026-09-30.md`` §1-§3).

**The phenomenon.** A coal plant fed partly by a DEDICATED mine (mine-mouth,
cost-of-service) and partly by third-party contract / spot coal books a
*blended* delivered cost on EIA-923. The dedicated mine's booked $/MMBtu is an
AVERAGE cost -- its fixed cost spread over the tons it happened to deliver --
while an incremental MWh at the plant is fuelled by (or displaces) a
non-captive ton. So the plant's ECON and PEAKING tranches, which are the
incremental loading of a running unit, price at the non-captive delivered cost;
its must-run / committed tranches keep the blend. The captive mine's fixed cost
stays carried once, by the take-or-pay / yard take-floor machinery, and never
becomes a per-MWh price (rule 19 ``[R-ONE-MECH]``).

**Captive identification (PHASE0 §1, fixed before the census was read, incl.
its ERRATUM).** A Page 5 receipt lot is CAPTIVE iff all three hold:

1. ``Primary Transportation Mode`` is a mine-mouth mode -- ``TC`` (tramway /
   conveyor / slurry pipeline) or ``TR`` (truck): no common carrier;
2. ``Coalmine State`` == ``Plant State``;
3. ``Purchase Type`` != ``S`` (a spot buy is by definition not dedicated).

Every other coal lot is NON-CAPTIVE. Zero DOF: every input is a filed field.
The EIA codes below are definitional vocabulary of the EIA-923 form (the
``coal_receipts.CONTRACT_PURCHASE_TYPES`` precedent), not tunable numbers, so
they live here beside the reader rather than in ``constants.py`` (rule 5
``[R-NO-MAGIC]``: each carries its citation).

**Rule 13 ``[R-MEASURED]``.** Page 5 is filed monthly for every year, so the
construction regenerates for any backcast year from that year's filing and
responds to a changed supply mix. It is a same-year measured delivered-price
overlay of exactly the kind its host seam
(:func:`~market_sim.data.fuel.plant_prices.apply_plant_monthly_fuel_prices`)
already is, and it inherits that seam's mode gate: a no-op in forecast mode.

**Rule 25 ``[R-ISO-SCOPE]``.** National data, plant-keyed at read time; no
per-ISO number, nothing transferred between ISOs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import COAL_RECEIPTS_RAW_DIR

#: EIA-923 ``Primary Transportation Mode`` codes for a mine-mouth delivery:
#: ``TC`` tramway / conveyor / slurry pipeline, ``TR`` truck (EIA-923
#: instructions, Schedule 2 transportation-mode codes; PHASE0 §1 erratum --
#: EIA has no ``CV`` code, the codes on disk 2019-2024 are
#: ``GL OP RR RV TC TP TR WT``).
MINE_MOUTH_TRANSPORT_MODES: frozenset[str] = frozenset({"TC", "TR"})

#: EIA-923 ``Purchase Type`` code for a spot purchase (EIA-923 instructions:
#: C contract, NC new contract, S spot, T tolling).
SPOT_PURCHASE_TYPE: str = "S"

#: EIA-923 Page 5 reports ``FUEL_COST`` in cents per MMBtu (EIA-923
#: instructions, Schedule 2 "cost of fuel ... in cents per million Btu").
FUEL_COST_CENTS_PER_DOLLAR: float = 100.0

#: Tranche-suffix prefixes of the ECON and PEAKING tranches a CAMPD bin emits
#: (``data/fleet/assembly.py::bins_to_fleet``: ``econ`` / ``econlo`` /
#: ``econhi`` / ``econcNN`` ramp slices, ``peak`` / ``peakN`` ladder). Every
#: other suffix -- ``mustrun``, ``sync``, ``committed*``, ``commitcyc`` -- is
#: must-run / committed and keeps the host seam's blended price.
MARGINAL_TRANCHE_PREFIXES: tuple[str, ...] = ("econ", "peak")

_RECEIPTS_CACHE: dict[tuple[Path, int], pd.DataFrame | None] = {}


@dataclass(frozen=True)
class CaptivePlantPrice:
    """One plant-year's captive split and non-captive delivered price.

    Attributes:
        plant_code: EIA plant id.
        captive_share: Captive MMBtu / all coal MMBtu over the year (rows with
            a withheld ``FUEL_COST`` included -- they count toward shares).
        annual_noncaptive: MMBtu-weighted non-captive delivered price over the
            year's non-captive lots with a reported cost ($/MMBtu), or ``None``
            when every non-captive cost is withheld.
        monthly_noncaptive: ``(12,)`` month-of-year non-captive price, NaN in
            months with no non-captive lot carrying a cost.
    """

    plant_code: int
    captive_share: float
    annual_noncaptive: float | None
    monthly_noncaptive: np.ndarray

    @property
    def mixed(self) -> bool:
        """True when the plant burned both captive and non-captive coal."""
        return 0.0 < self.captive_share < 1.0

    def month_prices(self) -> np.ndarray | None:
        """``(12,)`` price per month: the month's own, else the year's.

        ``None`` when the year's non-captive price is unavailable (the plant is
        then left untouched).
        """
        if self.annual_noncaptive is None:
            return None
        out = self.monthly_noncaptive.copy()
        out[np.isnan(out)] = self.annual_noncaptive
        return out


def receipts_path(year: int, raw_dir: str | Path | None = None) -> Path:
    """Return the Page 5 coal-receipts CSV path for ``year``."""
    root = Path(raw_dir) if raw_dir is not None else COAL_RECEIPTS_RAW_DIR
    return root / f"coal_receipts_{int(year)}.csv"


def load_page5_coal_receipts(
    year: int, raw_dir: str | Path | None = None
) -> pd.DataFrame | None:
    """Read one year's verbatim EIA-923 Page 5 coal lots, or ``None`` if absent.

    Cached per ``(path, year)``. The clean ``coal-receipts`` datatype cannot be
    used: it aggregates lots to (plant, month, purchase type, mode) and drops
    the mine state the captive rule needs.

    Args:
        year: Calendar year of the filing.
        raw_dir: Optional override of the raw ``coal-receipts`` directory.

    Returns:
        The raw frame (verbatim EIA columns), or ``None`` when no file exists.
    """
    path = receipts_path(year, raw_dir)
    key = (path, int(year))
    if key not in _RECEIPTS_CACHE:
        _RECEIPTS_CACHE[key] = (
            pd.read_csv(path, low_memory=False) if path.is_file() else None
        )
    return _RECEIPTS_CACHE[key]


def classify_captive(df: pd.DataFrame) -> pd.Series:
    """Return a boolean Series: True where a Page 5 lot is CAPTIVE (PHASE0 §1).

    Captive iff mine-mouth transport (``TC``/``TR``), ``Coalmine State`` ==
    ``Plant State``, and ``Purchase Type`` is not spot.
    """
    mode = df["Primary Transportation Mode"].astype(str).str.strip().str.upper()
    same_state = (
        df["Coalmine State"].astype(str).str.strip()
        == df["Plant State"].astype(str).str.strip()
    )
    not_spot = (
        df["Purchase Type"].astype(str).str.strip().str.upper() != SPOT_PURCHASE_TYPE
    )
    return mode.isin(MINE_MOUTH_TRANSPORT_MODES) & same_state & not_spot


def _wavg_dollars(mmbtu: pd.Series, cost_cents: pd.Series) -> float | None:
    """MMBtu-weighted $/MMBtu over rows with a reported cost and positive MMBtu."""
    ok = cost_cents.notna() & (mmbtu > 0)
    if not ok.any():
        return None
    w = mmbtu[ok]
    return float((cost_cents[ok] * w).sum() / w.sum()) / FUEL_COST_CENTS_PER_DOLLAR


def captive_plant_prices(
    receipts: pd.DataFrame, plant_codes: set[int] | None = None
) -> dict[int, CaptivePlantPrice]:
    """Per-plant captive share and non-captive delivered price for one year.

    Args:
        receipts: One year's verbatim Page 5 coal lots
            (:func:`load_page5_coal_receipts`).
        plant_codes: Restrict to these EIA plant ids (``None`` for all).

    Returns:
        ``{plant_code: CaptivePlantPrice}`` for every plant with positive coal
        MMBtu in the year.
    """
    r = receipts
    pid = pd.to_numeric(r["Plant Id"], errors="coerce")
    if plant_codes is not None:
        r = r[pid.isin({int(p) for p in plant_codes})]
        pid = pid[r.index]
    mmbtu = pd.to_numeric(r["QUANTITY"], errors="coerce").fillna(0.0) * pd.to_numeric(
        r["Average Heat Content"], errors="coerce"
    ).fillna(0.0)
    cost = pd.to_numeric(r["FUEL_COST"], errors="coerce")
    month = pd.to_numeric(r["MONTH"], errors="coerce")
    captive = classify_captive(r)
    frame = pd.DataFrame(
        {
            "pid": pid,
            "mmbtu": mmbtu,
            "cost": cost,
            "month": month,
            "captive": captive,
        }
    ).dropna(subset=["pid"])
    out: dict[int, CaptivePlantPrice] = {}
    for p, g in frame.groupby("pid"):
        total = float(g["mmbtu"].sum())
        if total <= 0.0:
            continue
        cap = float(g.loc[g["captive"], "mmbtu"].sum())
        nc = g[~g["captive"]]
        monthly = np.full(12, np.nan)
        for m, gm in nc.groupby("month"):
            mi = int(m) - 1
            if 0 <= mi < 12:
                v = _wavg_dollars(gm["mmbtu"], gm["cost"])
                if v is not None:
                    monthly[mi] = v
        out[int(p)] = CaptivePlantPrice(
            plant_code=int(p),
            captive_share=cap / total,
            annual_noncaptive=_wavg_dollars(nc["mmbtu"], nc["cost"]),
            monthly_noncaptive=monthly,
        )
    return out


def is_marginal_tranche(unit_id: str) -> bool:
    """True when a CAMPD tranche row is an ECON or PEAKING tranche.

    The tranche is the last ``_``-separated token of the unit id
    (``f"{bin_id}_{suffix}"``, ``data/fleet/assembly.py``).
    """
    return str(unit_id).rsplit("_", 1)[-1].startswith(MARGINAL_TRANCHE_PREFIXES)


def apply_captive_marginal_coal_price(
    fuel_prices: np.ndarray,
    written: np.ndarray,
    unit_ids: list[str],
    plant_code: np.ndarray,
    is_coal: np.ndarray,
    month_idx: np.ndarray,
    year: int,
    raw_dir: str | Path | None = None,
) -> dict[str, object]:
    """Reprice ECON / PEAKING coal tranches at mixed-source plants (in place).

    For each coal row whose plant is MIXED-SOURCE in ``year``
    (``0 < captive_share < 1`` on Page 5, **no minimum-share threshold** --
    owner ruling NWPP-NEXT-15) and whose tranche is ECON or PEAKING, every cell
    the host seam WROTE (``written``) is REPLACED by the plant's non-captive
    delivered price. Must-run / committed tranches, cells the seam did not
    write, 100 %-captive and 100 %-non-captive plants are untouched, as is a
    plant whose non-captive cost is withheld all year.

    **Granularity: plant-MONTHLY, matching the host seam.** A month with
    non-captive lots carrying a cost takes that month's MMBtu-weighted
    non-captive price; a month without takes the year's non-captive price.
    Shares (and so the mixed test) are ANNUAL; lots with ``FUEL_COST``
    withheld count toward the share but never toward a price.

    **Data-source coherence (PHASE0 §3 open issue, stated here).** The host
    seam's blended price comes from the legacy
    ``eia923_monthly_fuel_costs.parquet``; this overlay's non-captive price
    comes from Page 5. Only the econ/peak rows of mixed plants are
    overwritten, so the two sources meet only in the econ-vs-committed spread
    of those plants: that spread is the Page-5 non-captive price minus the
    legacy-parquet blend, and part of it can be a source difference rather
    than the captive/non-captive gap. Migrating the whole seam to Page 5 is a
    separate rule-14 repair and is NOT done here.

    Args:
        fuel_prices: ``(n_gen, T)`` fuel prices, mutated in place.
        written: ``(n_gen, T)`` mask of cells the host seam wrote.
        unit_ids: Per-row unit ids (tranche suffix is the last token).
        plant_code: ``(n_gen,)`` EIA plant codes.
        is_coal: ``(n_gen,)`` boolean coal-row mask (rows the host seam priced
            as coal).
        month_idx: ``(T,)`` month-of-year index (0-11) per hour.
        year: Solve year (selects the Page 5 file).
        raw_dir: Optional override of the raw ``coal-receipts`` directory.

    Returns:
        A report dict: ``status`` (``"applied"`` / ``"no_receipts"``),
        ``plants`` ``{plant: {captive_share, annual_noncaptive, rows,
        cells}}`` for every plant it repriced, and ``skipped_withheld`` (mixed
        plants left untouched because every non-captive cost is withheld).
    """
    report: dict[str, object] = {
        "status": "applied",
        "plants": {},
        "skipped_withheld": [],
    }
    rows = np.nonzero(is_coal)[0]
    rows = np.array([g for g in rows if is_marginal_tranche(unit_ids[g])], dtype=int)
    if rows.size == 0:
        return report
    receipts = load_page5_coal_receipts(year, raw_dir)
    if receipts is None:
        report["status"] = "no_receipts"
        return report
    plants = {int(plant_code[g]) for g in rows if int(plant_code[g]) > 0}
    prices = captive_plant_prices(receipts, plants)
    for g in rows:
        pc = int(plant_code[g])
        info = prices.get(pc)
        if info is None or not info.mixed:
            continue
        mp = info.month_prices()
        if mp is None:
            if pc not in report["skipped_withheld"]:
                report["skipped_withheld"].append(pc)
            continue
        cells = written[g]
        if not cells.any():
            continue
        fuel_prices[g, cells] = mp[month_idx[cells]]
        entry = report["plants"].setdefault(
            pc,
            {
                "captive_share": round(info.captive_share, 4),
                "annual_noncaptive": round(float(info.annual_noncaptive), 4),
                "rows": 0,
                "cells": 0,
            },
        )
        entry["rows"] += 1
        entry["cells"] += int(cells.sum())
    return report
