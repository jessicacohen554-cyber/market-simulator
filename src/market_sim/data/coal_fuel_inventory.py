"""Coal fuel-inventory monthly energy budget (MISO-gated, backcast, default off).

The missing CEILING on coal. Coal units in this model carry take-or-pay and
must-run **floors** and nothing whatever caps their energy, and until this
module the only fuel-inventory mechanism in the codebase was NEISO winter oil
(:mod:`market_sim.data.winter_fuel_inventory`). So the LP cannot represent *"the
fleet drew its stockpile down in one year and could only burn what it received
in the next"* — and that, not a price or an offer curve, is what
``docs/FINDING-miso256-2022-passthrough-inversion-2026-09-13.md`` §4 identifies
behind MISO's flat **+4.3 GW coal block in every hour of 2022**.

Rule 19 ``[R-ONE-MECH]`` is clean by inspection: this is a **missing limb**, not
a competing mechanism. Nothing in the model caps coal energy today, so there is
no incumbent to reconcile with and this must never be stacked on a coal floor.

**The falsification it implements** (``FINDING-miso258-coal-stock-falsification-
2026-09-14.md``, reproduced by ``scripts/probes/_miso259_coal_budget_phase0.py``):
MISO's modelled coal fleet opened 2022 holding 25.0 Mt, the lowest January stock
in the published record, after funding 2021's burn out of inventory (−10.99 Mt).
Run the model's own 2022 coal dispatch against that opening stock plus a
prior-years delivery rate and the fleet closes the year at a **negative
stockpile** — infeasible against the fuel that physically existed. That
statement contains no price, no residual and no benchmark, only tons.

Design, every choice pinned before the first solve
--------------------------------------------------

* **Monthly rows, no carry.** Twelve independent pooled-fleet rows per year:
  the opening stock amortized over the year plus each month's uniform share of
  the delivery rate. Structurally the NEISO Component-A shape
  (:func:`~market_sim.data.winter_fuel_inventory.build_winter_fuel_budget`) and
  the hydro monthly-energy budget before it. Monthly-independent rows **cannot
  carry stock across months** — a stated limitation, not a defect: a fleet that
  under-burns in April gets no extra July budget for it. The alternative, a
  true SOC-style carry, is a new LP row family and is deliberately not this
  arm.
* **Uniform delivery rate.** The re-supply is spread evenly across the year and
  is deliberately NOT timed to the month the budget binds in — timing it would
  be tuning the mechanism to the residual (rule 1 ``[R-STRUCT]``). This is the
  same choice, for the same reason, that the NEISO oil budget makes.
* **Minimum operating stock = ZERO.** A real fleet never runs its piles to
  zero, so this budget is looser than physics. It is left at zero anyway,
  because any non-zero floor chosen to close the remaining residual is exactly
  the fitted mechanism rule 1 forbids. A floor may be added later only from a
  cited days-of-burn source.
* **MMBtu-correct.** The row sums ``heat_rate[g] * P[g,t]`` (energy INPUT,
  MMBtu) against an MMBtu budget, so a heterogeneous-heat-rate fleet is priced
  on the fuel it actually consumes rather than on undifferentiated MWh.

Rule 13 ``[R-MEASURED]`` — why this is admissible
--------------------------------------------------

Every quantity sizing year *Y*'s budget **predates year Y**:

* opening stock = the footprint's **December ending stock of Y-1**
  (:func:`market_sim.data.coal_stocks.opening_stock_tons`);
* delivery rate = mean annual receipts over **Y-2 and Y-1**
  (:func:`market_sim.data.coal_receipts.prior_years_delivery_rate`), with the
  heat content quantity-weighted over those same years.

Year *Y*'s own stock path is inadmissible because it embeds the burn being
reproduced (``ending[m] = ending[m-1] + receipts[m] - burn[m]``), and year *Y*'s
own receipts are inadmissible because the NEISO precedent rejected exactly that
quantity as "a measured deliveries-to-tank OUTCOME". Neither is read here.

**The forward story**, which is the actual rule-13 test ("could this same
quantity be produced for a forward year from forward drivers, and would it
respond to changed conditions?"): in a forecast year the opening stock is the
model's **own carried inventory from the prior simulated year** — the same role
a storage SOC boundary plays — and the delivery rate is a trailing or
contracted volume over the years already simulated. Both regenerate from
forward drivers with no measured input at all, and both respond to changed
conditions: a fleet that retires units, or a year that burns harder, carries a
different stock into the next. That is why the mechanism is admissible rather
than a backcast overlay, and it is also why it matters in a forecast — a model
that cannot deplete a coal stockpile will over-predict coal in exactly the
high-gas scenarios a decarbonization study is run to answer.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from market_sim.config import paths
from market_sim.data.coal_receipts import prior_years_delivery_rate
from market_sim.data.coal_stocks import opening_stock_tons
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays, _hour_to_month_index

_COAL_FUEL_IDX: int = FUEL_TYPE_MAP["coal"]

#: Calendar months in the annual horizon. The budget is annual with a uniform
#: monthly grain, unlike NEISO's five-month winter season.
_N_MONTHS: int = 12

#: Crosswalk of third-party coal shared-storage / terminal entities to the
#: modelled generator plants they serve. See the file's own header for why it
#: exists (a rule 14 ``[R-ACCURATE]`` entity-grain misalignment, not missing
#: data) and for what it deliberately omits.
_SHARED_STORAGE_CSV = "coal-shared-storage-crosswalk.csv"


@dataclass(frozen=True)
class CoalFuelBudget:
    """Provenance for one year's coal fuel budget, for the run log and DOF ledger.

    Attributes:
        opening_stock_tons: Footprint December ending stock of ``year - 1``.
        delivery_rate_tons_per_year: Mean annual receipts over the source years.
        mmbtu_per_ton: Quantity-weighted heat content over the source years.
        rate_source_years: The years the delivery rate averaged.
        annual_budget_mmbtu: ``(stock + rate) * heat content``.
        monthly_budget_mmbtu: ``annual_budget_mmbtu / 12``.
        n_plants: Footprint size, storage entities included.
        n_storage_entities: How many of those are shared-storage entities.
        n_generators: Coal generators the row constrains.
    """

    opening_stock_tons: float
    delivery_rate_tons_per_year: float
    mmbtu_per_ton: float
    rate_source_years: tuple[int, ...]
    annual_budget_mmbtu: float
    monthly_budget_mmbtu: float
    n_plants: int
    n_storage_entities: int
    n_generators: int


def _shared_storage_map(reference_dir: Path | None = None) -> dict[int, set[int]]:
    """Return ``{storage_plant_id: {served generator plant ids}}``.

    Reads the committed crosswalk CSV rather than carrying a per-plant dict in
    code (rule 24 ``[R-REGISTRY]``). Returns an empty map when the file is
    absent, so the mechanism degrades to the generator-only footprint instead of
    failing — a tighter budget, and one whose omission is stated.
    """
    root = reference_dir or (paths.RAW_DATA_DIR / "reference")
    path = root / _SHARED_STORAGE_CSV
    if not path.is_file():
        return {}
    out: dict[int, set[int]] = {}
    with path.open(encoding="utf-8") as fh:
        rows = csv.DictReader(line for line in fh if not line.startswith("#"))
        for row in rows:
            try:
                sid = int(str(row["storage_plant_id"]).strip())
            except (KeyError, TypeError, ValueError):
                continue
            served = {
                int(tok)
                for tok in str(row.get("served_plant_ids", "")).split()
                if tok.strip().isdigit()
            }
            if served:
                out.setdefault(sid, set()).update(served)
    return out


def coal_gen_idx(fleet: FleetArrays) -> np.ndarray:
    """Return the thermal-block indices of the fleet's coal generators.

    Selection is on ``fuel_type_idx``, i.e. unit physics, never on a plant-class
    name tuple (rule 18 ``[R-PHYSICS]``), so every coal taxonomy label a fleet
    can wear — ``COAL_PRB``, ``COAL_BIT``, ``COAL_LIGNITE`` — is covered without
    enumerating them.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    return np.nonzero(fuel_idx == _COAL_FUEL_IDX)[0].astype(int)


def coal_footprint_plant_ids(
    fleet: FleetArrays, reference_dir: Path | None = None
) -> tuple[set[int], int]:
    """Return ``(plant ids whose coal this fleet can burn, n storage entities)``.

    The fleet's own coal plant codes, plus any shared-storage entity in the
    crosswalk that serves at least one of them. The membership test is the
    point: a storage entity contributes fuel only to a fleet that contains a
    plant it feeds, so the crosswalk adds nothing to an ISO whose fleet holds
    none of the served plants and needs no per-ISO branch (rule 25
    ``[R-ISO-SCOPE]``).
    """
    gen_idx = coal_gen_idx(fleet)
    codes = np.asarray(fleet.plant_code)
    plants = {int(codes[g]) for g in gen_idx}
    storage = {
        sid
        for sid, served in _shared_storage_map(reference_dir).items()
        if served & plants
    }
    return plants | storage, len(storage)


def build_coal_fuel_budget(
    fleet: FleetArrays,
    year: int,
    *,
    hours: int | None = None,
    n_rate_years: int = 2,
    reference_dir: Path | None = None,
) -> (
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, CoalFuelBudget]
    | None
):
    """Build the annual coal fuel-inventory budget LP inputs for ``year``.

    Returns the tuple consumed by
    :func:`market_sim.model.lp.rows._build_oil_budget_rows` via the ``coal_*``
    dispatch kwargs — the same builder the NEISO oil budget and the hydro
    monthly-energy budget use, reached through its own kwarg family so the two
    fuel budgets can never silently stack. One pooled fleet row per month
    enforces::

        sum_{g in coal fleet, t in month m} HR[g] * P[g, t]
            <= (opening_stock + delivery_rate) * mmbtu_per_ton / 12     (MMBtu)

    Returns ``None`` — leaving the solve byte-identical — when the fleet has no
    coal generators, or when either measured input is missing for ``year``. A
    missing input is never substituted: a budget sized on a guess would be a
    tuned cap wearing a measured label.

    Args:
        fleet: Vectorized fleet arrays (``fuel_type_idx``, ``heat_rate``,
            ``plant_code``).
        year: The backcast year being solved.
        hours: LP horizon (defaults to the fleet availability width, else 8760).
        n_rate_years: Prior years averaged for the delivery rate (default 2).
        reference_dir: Optional override of the reference-crosswalk directory
            (tests).

    Returns:
        ``(coal_gen_idx, budget_mmbtu, month_index, gen_hour_coeff,
        group_index, provenance)`` or ``None``.
    """
    gen_idx = coal_gen_idx(fleet)
    if gen_idx.size == 0:
        return None

    plant_ids, n_storage = coal_footprint_plant_ids(fleet, reference_dir=reference_dir)
    stock_tons = opening_stock_tons(plant_ids, year)
    rate = prior_years_delivery_rate(plant_ids, year, n_years=n_rate_years)
    if stock_tons is None or rate is None:
        return None

    annual_mmbtu = (float(stock_tons) + rate.tons_per_year) * rate.mmbtu_per_ton
    if not np.isfinite(annual_mmbtu) or annual_mmbtu <= 0.0:
        return None
    monthly_mmbtu = annual_mmbtu / _N_MONTHS

    if hours is None:
        avail = getattr(fleet, "availability", None)
        hours = int(avail.shape[1]) if avail is not None and avail.ndim == 2 else 8760
    T = int(hours)
    month_index = _hour_to_month_index(T)

    # Per-generator coefficient = heat rate (MMBtu/MWh), so HR * P is the coal
    # energy INPUT. Broadcast to (n_coal, T) by the row builder; a degenerate
    # zero heat rate is guarded the way the oil budget guards it, so a bad fleet
    # row cannot silently drop out of the constraint.
    hr = np.asarray(fleet.heat_rate, dtype=float)[gen_idx]
    coeff = np.where(hr > 0, hr, 10.0)

    budget_mmbtu = np.full((1, _N_MONTHS), monthly_mmbtu, dtype=float)
    group_index = np.zeros(gen_idx.size, dtype=int)

    provenance = CoalFuelBudget(
        opening_stock_tons=float(stock_tons),
        delivery_rate_tons_per_year=rate.tons_per_year,
        mmbtu_per_ton=rate.mmbtu_per_ton,
        rate_source_years=rate.source_years,
        annual_budget_mmbtu=annual_mmbtu,
        monthly_budget_mmbtu=monthly_mmbtu,
        n_plants=len(plant_ids),
        n_storage_entities=n_storage,
        n_generators=int(gen_idx.size),
    )
    return gen_idx, budget_mmbtu, month_index, coeff, group_index, provenance


@dataclass(frozen=True)
class CoalPlantBudget:
    """Provenance for one year's per-coal-yard annual budget rows.

    Attributes:
        n_entities: Coal yards that carry a row (a plant, or a shared-storage
            entity pooled with every modelled plant it serves).
        n_generators: Coal generators the rows constrain.
        n_unrowed_generators: Coal generators at yards with NO curated stock or
            receipt record in the source window — left unconstrained, never
            sized on a substitute.
        annual_budget_mmbtu: Sum of the per-yard budgets.
        rate_source_years: The prior years the delivery rates averaged.
    """

    n_entities: int
    n_generators: int
    n_unrowed_generators: int
    annual_budget_mmbtu: float
    rate_source_years: tuple[int, ...]


def coal_yard_groups(
    fleet: FleetArrays, reference_dir: Path | None = None
) -> dict[int, set[int]]:
    """Group the fleet's coal plants into the physical coal yards they draw on.

    Returns ``{yard key: EIA ids whose stocks and receipts fund that yard}``.
    A plant is its own yard unless a shared-storage entity in the crosswalk
    serves it, in which case every modelled plant that entity serves, and the
    entity itself, form ONE yard (union over overlapping entities). The key is
    the smallest modelled plant code in the yard. Coal at one yard cannot fuel
    a unit at another; coal in a shared yard can fuel any unit it serves.
    """
    gen_idx = coal_gen_idx(fleet)
    codes = np.asarray(fleet.plant_code)
    plants = sorted({int(codes[g]) for g in gen_idx})
    parent = {p: p for p in plants}

    def find(p: int) -> int:
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    storage_of: dict[int, set[int]] = {}
    for sid, served in _shared_storage_map(reference_dir).items():
        members = sorted(served & set(plants))
        if not members:
            continue
        for p in members[1:]:
            ra, rb = find(members[0]), find(p)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
        storage_of.setdefault(members[0], set()).add(int(sid))
    yards: dict[int, set[int]] = {}
    for p in plants:
        yards.setdefault(find(p), set()).add(p)
    for anchor, sids in storage_of.items():
        yards[find(anchor)].update(sids)
    return yards


def build_coal_plant_budget(
    fleet: FleetArrays,
    year: int,
    *,
    hours: int | None = None,
    n_rate_years: int = 2,
    reference_dir: Path | None = None,
) -> (
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, CoalPlantBudget]
    | None
):
    """Build the per-coal-yard ANNUAL fuel budget rows for ``year`` (miso-268).

    The plant grain of :func:`build_coal_fuel_budget`'s annual identity. The
    pooled rows sum every yard's stock and receipts into one fleet pile, so the
    LP may burn coal at a yard that never held it against tons sitting at
    another — which no rail car makes true. One row per yard enforces::

        sum_{g at yard y, t in year} HR[g] * P[g, t]
            <= (Dec(Y-1) stock_y + prior-years receipts rate_y) * mmbtu_per_ton_y

    Same measured inputs, same rule-13 admissibility and same forward story as
    the pooled budget (every sizing quantity predates ``year``); only the
    partition changes. The pooled MONTHLY rows are untouched and remain the
    timing limb — these rows add no month grain, so the no-carry limitation is
    not extended to the yard level. Summed over yards the annual budgets equal
    the pooled annual budget for the covered footprint, so this is a refinement
    of one identity, never a second mechanism (rule 19 ``[R-ONE-MECH]``).

    A yard with no stock AND no receipt record in the source window (Dec of
    ``Y-1`` and the ``n_rate_years`` prior years) gets NO row: a missing input
    is never substituted. A yard that files and reports zero gets a zero budget,
    because that is what it reported. Heat content is the yard's own
    quantity-weighted prior-years value, else the covered fleet's.

    Returns:
        ``(gen_idx, budget (n_yards, 1), month_index zeros (T,), coeff,
        group_index, provenance)`` for :func:`_build_oil_budget_rows`, or
        ``None`` when no yard carries a row.
    """
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    gen_idx = coal_gen_idx(fleet)
    if gen_idx.size == 0:
        return None
    yards = coal_yard_groups(fleet, reference_dir=reference_dir)
    source = [year - k for k in range(1, int(n_rate_years) + 1)]
    stocks = load_coal_stocks([year - 1])
    receipts = load_coal_receipts(source)
    if stocks.empty and receipts.empty:
        return None
    dec = (
        stocks[stocks["month"] == 12].groupby("plant_id")["ending_stock_tons"].sum()
        if not stocks.empty
        else None
    )
    stock_filers = set(int(p) for p in stocks["plant_id"]) if not stocks.empty else set()
    if not receipts.empty:
        rc = receipts.assign(
            _mmbtu=receipts["quantity_tons"] * receipts["heat_content_mmbtu_per_ton"]
        )
        rtons = rc.groupby("plant_id")["quantity_tons"].sum()
        rmmbtu = rc.groupby("plant_id")["_mmbtu"].sum()
        n_src = max(int(rc["year"].nunique()), 1)
        src_years = tuple(sorted(int(y) for y in rc["year"].unique()))
    else:
        rtons = rmmbtu = None
        n_src, src_years = 1, ()

    def _get(s, ids):
        return float(sum(s.get(i, 0.0) for i in ids)) if s is not None else 0.0

    rowed: list[tuple[int, float, float, float]] = []
    for key, ids in yards.items():
        filed = bool(ids & stock_filers) or (
            rtons is not None and any(i in rtons.index for i in ids)
        )
        if not filed:
            continue
        rowed.append((key, _get(dec, ids), _get(rtons, ids) / n_src, _get(rmmbtu, ids)))
    if not rowed:
        return None
    fleet_tons = sum(r[2] for r in rowed) * n_src
    fleet_mmbtu = sum(r[3] for r in rowed)
    fleet_hc = fleet_mmbtu / fleet_tons if fleet_tons > 0 else float("nan")

    codes = np.asarray(fleet.plant_code)
    yard_of_plant = {p: key for key, ids in yards.items() for p in ids}
    key_pos = {key: i for i, (key, *_rest) in enumerate(rowed)}
    budget = np.zeros((len(rowed), 1), dtype=float)
    for i, (_key, stock, rate, mmbtu) in enumerate(rowed):
        tons_src = rate * n_src
        hc = mmbtu / tons_src if tons_src > 0 else fleet_hc
        if not np.isfinite(hc) or hc <= 0.0:
            return None
        budget[i, 0] = (stock + rate) * hc
    pos = np.array(
        [key_pos.get(yard_of_plant.get(int(codes[g]), -1), -1) for g in gen_idx],
        dtype=int,
    )
    keep = pos >= 0
    if not keep.any():
        return None
    g_rows = gen_idx[keep]
    hr = np.asarray(fleet.heat_rate, dtype=float)[g_rows]
    coeff = np.where(hr > 0, hr, 10.0)
    if hours is None:
        avail = getattr(fleet, "availability", None)
        hours = int(avail.shape[1]) if avail is not None and avail.ndim == 2 else 8760
    month_index = np.zeros(int(hours), dtype=int)
    prov = CoalPlantBudget(
        n_entities=len(rowed),
        n_generators=int(keep.sum()),
        n_unrowed_generators=int((~keep).sum()),
        annual_budget_mmbtu=float(budget.sum()),
        rate_source_years=src_years,
    )
    return g_rows, budget, month_index, coeff, pos[keep], prov
