"""Coal fuel-inventory monthly energy budget (MISO-gated, backcast, default off).

The missing CEILING on coal. Coal units in this model carry take-or-pay and
must-run **floors** and nothing whatever caps their energy, and until this
module the only fuel-inventory mechanism in the codebase was NEISO winter oil
(:mod:`market_sim.data.winter_fuel_inventory`). So the LP cannot represent *"the
fleet drew its stockpile down in one year and could only burn what it received
in the next"* — and that, not a price or an offer curve, is what
``docs/records/miso/FINDING-miso256-2022-passthrough-inversion-2026-09-13.md`` §4 identifies
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
from dataclasses import dataclass, field
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
        yard_keys: Yard key of each row, in row order.
        stock_mmbtu: Each row's Dec(Y-1) opening stock in MMBtu (the
            ``stock * hc`` term of its budget), in row order — what
            :func:`build_coal_monthly_pile` needs to split the annual ceiling
            into its opening pile and its receipts.
    """

    n_entities: int
    n_generators: int
    n_unrowed_generators: int
    annual_budget_mmbtu: float
    rate_source_years: tuple[int, ...]
    yard_keys: tuple[int, ...] = ()
    stock_mmbtu: tuple[float, ...] = ()


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
    stock_filers = (
        set(int(p) for p in stocks["plant_id"]) if not stocks.empty else set()
    )
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
    stock_mmbtu = np.zeros(len(rowed), dtype=float)
    for i, (_key, stock, rate, mmbtu) in enumerate(rowed):
        tons_src = rate * n_src
        hc = mmbtu / tons_src if tons_src > 0 else fleet_hc
        if not np.isfinite(hc) or hc <= 0.0:
            return None
        budget[i, 0] = (stock + rate) * hc
        stock_mmbtu[i] = stock * hc
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
        yard_keys=tuple(int(r[0]) for r in rowed),
        stock_mmbtu=tuple(float(v) for v in stock_mmbtu),
    )
    return g_rows, budget, month_index, coeff, pos[keep], prov


#: EIA-923 Page 5 purchase types that carry a forward commitment to take coal:
#: ``C`` contract, ``NC`` new contract, ``T`` tolling. The same set the owner-
#: ruled census used (``scripts/probes/_nwppnext5_coal_contract_census.py``
#: ``CONTRACT_TYPES``); ``S`` spot is excluded because a spot lot obliges nothing.
TAKE_PURCHASE_TYPES: tuple[str, ...] = ("C", "NC", "T")


@dataclass(frozen=True)
class CoalTakeFloor:
    """Provenance for one year's per-yard coal take floor (NWPP-NEXT-7).

    Attributes:
        n_binding_rows: Yard rows carrying a positive floor.
        floor_mmbtu: Sum of the (clipped) per-yard floors.
        clipped_to_budget: Rows whose floor was cut to the yard's own ceiling.
        clipped_to_capacity: Rows whose floor was cut to what the yard's rowed
            units can physically burn in the year.
        per_yard: ``{yard key: (floor MMBtu before clip, after clip)}``.
        parts: ``{row index: (C * hc, (S_dec - S_max) * hc)}`` MMBtu — the
            contract take and the pile headroom term of each floored row's
            unclipped floor, for :func:`build_coal_monthly_pile`.
    """

    n_binding_rows: int
    floor_mmbtu: float
    clipped_to_budget: int
    clipped_to_capacity: int
    per_yard: dict[int, tuple[float, float]]
    parts: dict[int, tuple[float, float]] = field(default_factory=dict)


def build_coal_take_floor(
    fleet: FleetArrays,
    year: int,
    gen_idx: np.ndarray,
    group_index: np.ndarray,
    coeff: np.ndarray,
    budget: np.ndarray,
    yard_keys: tuple[int, ...],
    reference_dir: Path | None = None,
) -> tuple[np.ndarray, CoalTakeFloor]:
    """Per-yard annual coal TAKE floor on the yard budget rows (NWPP-NEXT-7).

    The LOWER bound of the same annual identity whose upper bound is
    :func:`build_coal_plant_budget` (owner rulings Q1-Q5, 2026-09-27, on
    ``docs/records/nwpp/FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md``
    §5: generalise the yard row, annual period, a floor not an equality,
    estimator B net, incumbent per-hour take-or-pay discounts retired)::

        take_net_y = max(0, C_y + S_dec_y - S_max_y) * hc_y
        take_net_y <= sum_{g at yard y, t} HR[g] * P[g, t] <= budget_y

    * ``C_y`` — the yard's contract tonnage received in ``year - 1``
      (EIA-923 Page 5, purchase types :data:`TAKE_PURCHASE_TYPES`), assumed
      renewed at the same volume (estimator B).
    * ``S_dec_y`` — the yard's December ``year - 1`` ending stock (Page 2).
    * ``S_max_y`` — the yard's largest month-end stock in any curated year
      ``<= year - 1``: the take may be absorbed into the pile up to the most it
      has ever held, so only the remainder must be burned (the ``_net`` form).
    * ``hc_y`` — the yard's own ``year - 1`` quantity-weighted heat content.

    Every quantity predates ``year`` (rule 13 [R-MEASURED]); zero free
    parameters (rule 21 [R-DOF]). A yard with no December stock record gets no
    floor (never substituted). Two FEASIBILITY clips, fixed ex ante and not
    tunable: the floor never exceeds the yard's own ceiling row, and never
    exceeds ``sum coeff * pmax * availability`` of its rowed units, i.e. what
    they can physically burn.

    Returns:
        ``(floor (n_rows, 1) MMBtu, provenance)``, rows aligned with ``budget``.
    """
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    yards = coal_yard_groups(fleet, reference_dir=reference_dir)
    n_rows = budget.shape[0]
    floor = np.zeros((n_rows, 1), dtype=float)
    rec = load_coal_receipts([year - 1])
    stocks = load_coal_stocks()
    if not stocks.empty:
        stocks = stocks[stocks["year"] <= year - 1]
    gen_idx = np.asarray(gen_idx, dtype=int)
    group_index = np.asarray(group_index, dtype=int)
    coeff = np.asarray(coeff, dtype=float)
    pmax = np.asarray(fleet.pmax, dtype=float)[gen_idx]
    avail = getattr(fleet, "availability", None)
    if avail is not None and np.ndim(avail) == 2:
        mwh = pmax * np.asarray(avail, dtype=float)[gen_idx].sum(axis=1)
        cap_mmbtu = np.bincount(group_index, weights=coeff * mwh, minlength=n_rows)
    else:  # no hourly availability: the capacity clip has nothing to read
        cap_mmbtu = np.full(n_rows, np.inf)
    per_yard: dict[int, tuple[float, float]] = {}
    parts: dict[int, tuple[float, float]] = {}
    n_bud = n_cap = 0
    for i, key in enumerate(yard_keys):
        ids = yards.get(int(key), {int(key)})
        st = stocks[stocks["plant_id"].isin(ids)] if not stocks.empty else stocks
        if st.empty or not ((st["year"] == year - 1) & (st["month"] == 12)).any():
            continue
        by_month = st.groupby(["year", "month"])["ending_stock_tons"].sum()
        s_dec = float(by_month.get((year - 1, 12), 0.0))
        s_max = float(by_month.max())
        r = rec[rec["plant_id"].isin(ids)] if not rec.empty else rec
        if r.empty:
            continue
        tons_all = float(r["quantity_tons"].sum())
        hc = (
            float((r["quantity_tons"] * r["heat_content_mmbtu_per_ton"]).sum())
            / tons_all
            if tons_all > 0
            else float("nan")
        )
        c_tons = float(
            r.loc[r["purchase_type"].isin(TAKE_PURCHASE_TYPES), "quantity_tons"].sum()
        )
        if not np.isfinite(hc) or hc <= 0.0:
            continue
        raw = max(c_tons + s_dec - s_max, 0.0) * hc
        parts[i] = (c_tons * hc, (s_dec - s_max) * hc)
        val = raw
        if val > float(budget[i, 0]):
            val, n_bud = float(budget[i, 0]), n_bud + 1
        if val > float(cap_mmbtu[i]):
            val, n_cap = float(cap_mmbtu[i]), n_cap + 1
        floor[i, 0] = max(val, 0.0)
        per_yard[int(key)] = (raw, floor[i, 0])
    prov = CoalTakeFloor(
        n_binding_rows=int((floor[:, 0] > 0).sum()),
        floor_mmbtu=float(floor.sum()),
        clipped_to_budget=n_bud,
        clipped_to_capacity=n_cap,
        per_yard=per_yard,
        parts=parts,
    )
    return floor, prov


@dataclass(frozen=True)
class CoalMonthlyPile:
    """Provenance for one year's monthly-grain yard pile rows (NWPP-NEXT-8).

    Attributes:
        n_rows: Yard rows (each now carries one cumulative row per month).
        n_months: Month-end rows per yard.
        floor_clipped_to_ceiling: (row, month) cells whose cumulative floor was
            cut to the same month's cumulative ceiling.
        floor_clipped_to_capacity: (row, month) cells whose cumulative floor was
            cut to what the yard's rowed units can burn through that month.
    """

    n_rows: int
    n_months: int
    floor_clipped_to_ceiling: int
    floor_clipped_to_capacity: int


def build_coal_monthly_pile(
    fleet: FleetArrays,
    gen_idx: np.ndarray,
    group_index: np.ndarray,
    coeff: np.ndarray,
    budget: np.ndarray,
    stock_mmbtu: tuple[float, ...],
    floor_parts: dict[int, tuple[float, float]] | None,
    hours: int,
    measured: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray, CoalMonthlyPile]:
    """Split the per-yard annual pile identity into cumulative month-end rows.

    NWPP-NEXT-8 (owner decision cards 2026-09-28). The annual yard row bounds a
    whole year's burn, so the LP may place the contracted take in whichever
    months are cheapest — measured on keeper #14, it banked the obligated burn
    in winter, when NW delivered gas is dear, and let the yards idle through
    spring and summer. A real yard cannot: its pile holds between zero and the
    most it has ever held, and contract coal arrives through the year. One
    cumulative row per month-end ``m`` (1-based) enforces::

        max(0, (S_dec - S_max) + m/12 * C) * hc
            <= sum_{g at yard, t <= end of m} HR[g] * P[g, t]  (+ shortfall)
            <= S_dec * hc + m/12 * (budget - S_dec * hc)

    Receipts are FLAT RATABLE (``m/12``), the owner-carded standard take-or-pay
    delivery form, so no year ``Y-1`` delivery timing is carried into ``Y``. At
    ``m = 12`` both sides are EXACTLY the annual rows
    (:func:`build_coal_plant_budget`, :func:`build_coal_take_floor`), clips
    included, so this is the same identity at a finer grain, never a second
    mechanism (rule 19 ``[R-ONE-MECH]``). Zero free parameters (rule 21): every
    term is one the annual rows already read. The two feasibility clips are the
    annual ones applied per month: a month's floor never exceeds that month's
    ceiling, nor what the yard's rowed units can physically burn by then.

    Args:
        fleet: The fleet (``pmax``, ``availability``).
        gen_idx: Rowed coal generator indices.
        group_index: Yard row of each rowed generator.
        coeff: Per-rowed-generator MMBtu/MWh.
        budget: ``(n_rows, 1)`` annual ceilings, MMBtu.
        stock_mmbtu: Each row's Dec(Y-1) stock term, MMBtu
            (``CoalPlantBudget.stock_mmbtu``).
        floor_parts: ``CoalTakeFloor.parts`` (``{row: (C*hc, (S_dec-S_max)*hc)}``),
            or ``None`` when no take floor is armed (ceiling only).
        hours: LP horizon.
        measured: ``(cum_receipts, cum_contract)`` from
            :func:`build_coal_measured_receipts` (NWPP-NEXT-9,
            ``coal_monthly_pile_measured_receipts``), each ``(n_rows, 12)``
            cumulative same-year MMBtu. A finite row replaces that yard's
            ratable ``m/12`` receipts on the ceiling (all lots) and the floor
            (contract lots); a NaN row keeps the ratable profile. ``None`` (the
            default) leaves every row ratable, byte-identical to NEXT-8.

    Returns:
        ``(ceiling (n_rows, n_months), floor (n_rows, n_months) or None,
        month_index (hours,), provenance)``, cumulative MMBtu.
    """
    budget = np.asarray(budget, dtype=float)
    n_rows = budget.shape[0]
    month_index = _hour_to_month_index(int(hours))
    n_months = int(month_index.max()) + 1 if month_index.size else 1
    frac = np.arange(1, n_months + 1, dtype=float) / 12.0
    stock = np.asarray(stock_mmbtu, dtype=float)
    if stock.shape != (n_rows,):
        raise ValueError(
            f"stock_mmbtu has {stock.shape} entries for {n_rows} yard rows"
        )
    ceiling = stock[:, None] + frac[None, :] * (budget[:, 0] - stock)[:, None]
    meas_r = meas_c = None
    if measured is not None:
        meas_r = np.asarray(measured[0], dtype=float)[:, :n_months]
        meas_c = np.asarray(measured[1], dtype=float)[:, :n_months]
        if meas_r.shape != (n_rows, n_months) or meas_c.shape != meas_r.shape:
            raise ValueError(
                f"measured receipts have {meas_r.shape} / {meas_c.shape} cells "
                f"for {n_rows} yard rows x {n_months} months"
            )
        # A finite row is the yard's own same-year Page 5 record; NaN keeps
        # the ratable profile (a missing input is never substituted).
        has = np.isfinite(meas_r).all(axis=1)
        ceiling[has] = stock[has, None] + meas_r[has]
    if floor_parts is None:
        prov = CoalMonthlyPile(n_rows, n_months, 0, 0)
        return ceiling, None, month_index, prov
    gen_idx = np.asarray(gen_idx, dtype=int)
    group_index = np.asarray(group_index, dtype=int)
    coeff = np.asarray(coeff, dtype=float)
    pmax = np.asarray(fleet.pmax, dtype=float)[gen_idx]
    avail = getattr(fleet, "availability", None)
    if avail is not None and np.ndim(avail) == 2:
        a = np.asarray(avail, dtype=float)[gen_idx][:, : month_index.size]
        # MWh each rowed unit can make in each month, then cumulative MMBtu.
        by_month = np.zeros((gen_idx.size, n_months), dtype=float)
        np.add.at(by_month.T, month_index, a.T)
        w = coeff * pmax
        cap = np.zeros((n_rows, n_months), dtype=float)
        np.add.at(cap, group_index, w[:, None] * by_month)
        cap = np.cumsum(cap, axis=1)
    else:
        cap = np.full((n_rows, n_months), np.inf)
    floor = np.zeros((n_rows, n_months), dtype=float)
    for i, (c_mmbtu, head_mmbtu) in floor_parts.items():
        take = frac * c_mmbtu
        if meas_c is not None and np.isfinite(meas_c[int(i)]).all():
            take = meas_c[int(i)]
        floor[int(i)] = np.maximum(head_mmbtu + take, 0.0)
    n_ceil = int((floor > ceiling).sum())
    floor = np.minimum(floor, ceiling)
    n_cap = int((floor > cap).sum())
    floor = np.maximum(np.minimum(floor, cap), 0.0)
    prov = CoalMonthlyPile(n_rows, n_months, n_ceil, n_cap)
    return ceiling, floor, month_index, prov


@dataclass(frozen=True)
class CoalMeasuredReceipts:
    """Provenance for one year's same-year measured pile receipts (NWPP-NEXT-9).

    Attributes:
        n_measured: Yard rows carrying their own same-year Page 5 record.
        n_ratable: Yard rows kept on the ratable profile (no same-year row).
        receipts_mmbtu: Sum of the measured rows' annual receipts, MMBtu.
        contract_mmbtu: Sum of the measured rows' annual contract lots, MMBtu.
    """

    n_measured: int
    n_ratable: int
    receipts_mmbtu: float
    contract_mmbtu: float


def build_coal_measured_receipts(
    fleet: FleetArrays,
    year: int,
    yard_keys: tuple[int, ...],
    reference_dir: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, CoalMeasuredReceipts] | None:
    """Cumulative same-year monthly coal receipts per yard row (NWPP-NEXT-9).

    Owner decision card 2026-09-28 (``coal_monthly_pile_measured_receipts``).
    The monthly pile (:func:`build_coal_monthly_pile`) spreads each yard's
    receipts flat across the year at the prior-years rate, so a year whose
    deliveries fall short — 2023 at PacifiCorp's Bridger, Hunter and
    Huntington, where EIA-923 Page 5 receipts fell 18-53 % below 2022 with
    December stocks at record lows — is modelled with coal the yard never
    received. This returns the year's OWN receipts, month by month: every lot
    (the ceiling's inflow) and the contract lots of :data:`TAKE_PURCHASE_TYPES`
    (the floor's take), each at its own reported heat content.

    A realised physical fuel-supply input from the same Page 5 table the F923
    delivered-price overlay reads — a backcast overlay under rule 13
    ``[R-MEASURED]``, like the pile itself backcast-only, never a forecast
    methodology. Zero free parameters (rule 21). A yard with no same-year row
    gets a NaN row (it keeps the ratable profile: a missing input is never
    substituted with zero).

    Returns:
        ``(cum_receipts (n_rows, 12), cum_contract (n_rows, 12), provenance)``
        in MMBtu, rows aligned with ``yard_keys``, or ``None`` when the year has
        no curated receipts at all (every row stays ratable).
    """
    from market_sim.data.coal_receipts import load_coal_receipts

    rec = load_coal_receipts([year])
    if rec.empty:
        return None
    yards = coal_yard_groups(fleet, reference_dir=reference_dir)
    rec = rec.assign(
        _mmbtu=rec["quantity_tons"] * rec["heat_content_mmbtu_per_ton"],
        _c=rec["purchase_type"].isin(TAKE_PURCHASE_TYPES),
    )
    n = len(yard_keys)
    cum_r = np.full((n, 12), np.nan)
    cum_c = np.full((n, 12), np.nan)
    for i, key in enumerate(yard_keys):
        ids = yards.get(int(key), {int(key)})
        r = rec[rec["plant_id"].isin(ids)]
        if r.empty:
            continue
        mo = r["month"].astype(int).to_numpy() - 1
        allm = np.bincount(mo, weights=r["_mmbtu"].to_numpy(), minlength=12)[:12]
        conm = np.bincount(
            mo, weights=(r["_mmbtu"] * r["_c"]).to_numpy(), minlength=12
        )[:12]
        cum_r[i] = np.cumsum(allm)
        cum_c[i] = np.cumsum(conm)
    has = np.isfinite(cum_r).all(axis=1)
    prov = CoalMeasuredReceipts(
        n_measured=int(has.sum()),
        n_ratable=int((~has).sum()),
        receipts_mmbtu=float(cum_r[has, -1].sum()),
        contract_mmbtu=float(cum_c[has, -1].sum()),
    )
    return cum_r, cum_c, prov


def reconcile_floors_to_yard_budget(
    min_gen: np.ndarray,
    gen_idx: np.ndarray,
    budget: np.ndarray,
    coeff: np.ndarray,
    group_index: np.ndarray,
    month_index: np.ndarray | None = None,
) -> list[tuple[int, float, float]]:
    """Scale each coal yard's must-run floors so they fit inside its fuel budget.

    A floor cannot demand coal the yard does not hold (rule 19 [R-ONE-MECH]: the
    yard budget and a coal floor both act on the same units' energy, so they are
    reconciled rather than stacked; rule 17 [R-FLOOR-WINDOW]: a floor binding
    where its own driver's premise — fuel on site — is false is a bug). neiso-117
    found the case: Schiller 2367 in 2025 carries the NEISO winter fuel-security
    floor while its EIA-923 yard reported zero stock and zero receipts, so the
    budget row and the floor made the LP infeasible.

    For each budget row ``i`` the floor's annual fuel draw is
    ``E_i = sum_{g in i} coeff[g] * sum_t min_gen[g, t]`` (MMBtu). Where
    ``E_i > budget_i`` every floor at that yard is scaled by ``budget_i / E_i``
    (to zero for a zero budget) — the floor's hourly shape is kept, its level is
    capped at what the pile can fund. Where the floor already fits, nothing is
    touched, so every feasible solve is byte-identical. Zero free parameters.

    Args:
        min_gen: ``(n_gen, T)`` floor array; modified IN PLACE.
        gen_idx: Rowed generator indices (``build_coal_plant_budget``'s first return).
        budget: ``(n_rows, 1)`` annual budgets, MMBtu; or ``(n_rows, n_months)``
            CUMULATIVE month-end ceilings (the monthly pile) with ``month_index``.
        coeff: Per-rowed-generator MMBtu/MWh coefficients.
        group_index: Budget row of each rowed generator.
        month_index: ``(T,)`` month of each hour, required when ``budget`` has
            more than one column. Each yard's floors are then scaled by the
            smallest month-end ratio ``ceiling(m) / cumulative floor draw(m)``
            over the months it exceeds (closeout-L1, ERCOT ceiling-only pile),
            so the floor fits under every month-end row; a yard that already
            fits is untouched.

    Returns:
        ``[(row, floor_mmbtu, scale), ...]`` for every row whose floor was scaled
        (``floor_mmbtu`` is the draw at the binding month-end on the monthly grain).
    """
    gen_idx = np.asarray(gen_idx, dtype=int)
    group_index = np.asarray(group_index, dtype=int)
    coeff = np.asarray(coeff, dtype=float)
    budget = np.asarray(budget, dtype=float)
    scaled: list[tuple[int, float, float]] = []
    if budget.shape[1] > 1:
        if month_index is None:
            raise ValueError("a multi-month budget needs month_index")
        mi = np.asarray(month_index, dtype=int)[: min_gen.shape[1]]
        n_m = budget.shape[1]
        by_month = np.zeros((gen_idx.size, n_m), dtype=float)
        np.add.at(by_month.T, mi, min_gen[gen_idx][:, : mi.size].T)
        draw_m = np.zeros((budget.shape[0], n_m), dtype=float)
        np.add.at(draw_m, group_index, coeff[:, None] * by_month)
        cum = np.cumsum(draw_m, axis=1)
        for i in range(budget.shape[0]):
            over = cum[i] > budget[i]
            if not over.any():
                continue
            ratio = np.maximum(budget[i, over], 0.0) / cum[i, over]
            k = int(np.argmin(ratio))
            s = float(ratio[k])
            min_gen[gen_idx[group_index == i]] *= s
            scaled.append((i, float(cum[i, over][k]), s))
        return scaled
    draw = coeff * min_gen[gen_idx].sum(axis=1)
    for i in range(budget.shape[0]):
        sel = group_index == i
        e = float(draw[sel].sum())
        b = float(budget[i, 0])
        if e <= b or e <= 0.0:
            continue
        s = max(b, 0.0) / e
        min_gen[gen_idx[sel]] *= s
        scaled.append((i, e, s))
    return scaled


def coal_take_shortfall_price(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    gen_idx: np.ndarray,
    group_index: np.ndarray,
    coeff: np.ndarray,
    n_rows: int,
) -> np.ndarray:
    """Per-yard $/MMBtu price of an unmet coal take (NWPP-NEXT-7 soft floor).

    Owner ruling 2026-09-27: the take floor is SOFT, its shortfall priced at the
    yard's own delivered coal cost — contracted coal left unburned is paid for
    anyway (take-or-pay), so no yard row is ever infeasible and the row's dual
    is capped at that price. The price is the one the model already charges
    those units for fuel (``fuel_prices``, the resolved EIA-923 plant-monthly /
    coal-supply chain), averaged over the year and weighted across the yard's
    rowed units by ``coeff * pmax`` (fuel-burn capability). Zero free
    parameters: it reads no quantity the fuel pricing does not already set.

    Args:
        fuel_prices: ``(n_gen, T)`` delivered fuel price, $/MMBtu.
        fleet: The fleet (for ``pmax``).
        gen_idx: Rowed coal generator indices.
        group_index: Yard row of each rowed generator.
        coeff: Per-rowed-generator MMBtu/MWh.
        n_rows: Number of yard rows.

    Returns:
        ``(n_rows,)`` $/MMBtu, rows aligned with the yard budget.
    """
    fp = np.asarray(fuel_prices, dtype=float)
    if fp.shape[0] != np.asarray(fleet.pmax).shape[0]:
        raise ValueError(
            f"fuel_prices rows {fp.shape[0]} != fleet generators "
            f"{np.asarray(fleet.pmax).shape[0]}: the price would read the wrong units"
        )
    gen_idx = np.asarray(gen_idx, dtype=int)
    group_index = np.asarray(group_index, dtype=int)
    w = np.asarray(coeff, dtype=float) * np.asarray(fleet.pmax, dtype=float)[gen_idx]
    p = fp[gen_idx].mean(axis=1)
    num = np.bincount(group_index, weights=w * p, minlength=n_rows)
    den = np.bincount(group_index, weights=w, minlength=n_rows)
    fleet_mean = float((w * p).sum() / w.sum()) if w.sum() > 0 else 0.0
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), fleet_mean)
