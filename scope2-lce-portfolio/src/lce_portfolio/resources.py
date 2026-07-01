"""Resource catalog, cost resolution, per-ISO caps, and hydro budgets.

Loads the clean/low-carbon resource table (``data/lcoe/resource_costs.csv``) and
converts each row into the representation the LP consumes, at the chosen
low/mid/high sensitivity. There are three cost bases (ADRs 0004/0006/0008):

  * ``capex_fixed`` — generation and fixed-duration Li-ion storage. Overnight
    capex ($/kW) from NREL ATB 2024 is annualized with a capital-recovery factor
    (CRF) and added to FOM to give ``fixed_mwyr`` ($/MW-yr), a pay-for-capacity
    cost paid whether or not the unit runs. Storage rows carry a fixed
    ``duration_h`` and round-trip efficiency.
  * ``split_storage`` — LDES and hydrogen. Power ($/kW) and energy ($/kWh) capex
    are annualized separately (``cost_power_mwyr`` and ``cost_energy_mwhyr``) so
    the LP can size power and energy independently within ``[duration_min_h,
    duration_max_h]``. These are marked ``is_split=True``; the PP-02 LP raises on
    them (split support lands in PP-02b).
  * ``ppa_mwh`` — existing nuclear/hydro. A going-forward, per-MWh PPA cost plus a
    clean-attribute premium; ``fixed_mwyr=0`` and the effective VOM is
    ``cost + eac_premium``, so existing resources pay only when dispatched and are
    capped by the contractable MW (ADR 0008).

The CRF is ``r(1+r)^n / ((1+r)^n - 1)`` with ``r = config.discount_rate`` and
``n = life_yr``; this finally wires ``config.discount_rate`` into the tool.

Per-ISO caps come from ``data/caps/resource_caps.csv`` (ADR 0009): an ISO with any
rows there restricts eligibility to the resources it lists (cap_mw>0); an ISO
absent from the table falls back to the table's ``cap_max_default_mw``. The
override precedence is ``config.resource_caps_mw`` > caps table > default.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from lce_portfolio.config import PortfolioConfig

# Resolve the packaged data tables without any dependence on market_sim paths.
_PKG_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COST_TABLE = _PKG_ROOT / "data" / "lcoe" / "resource_costs.csv"
DEFAULT_CAPS_TABLE = _PKG_ROOT / "data" / "caps" / "resource_caps.csv"
DEFAULT_HYDRO_BUDGETS = _PKG_ROOT / "data" / "hydro" / "monthly_budgets.csv"


@dataclass(frozen=True)
class ResourceArrays:
    """Struct-of-arrays view of the active resources, indexed by resource ``r``.

    Parallel arrays (length ``n_res``) plus a storage mask. Mirrors the
    market-sim ``FleetArrays`` pattern so the LP builder touches only numpy.
    Split-storage resources set ``is_split=True`` and carry ``cost_energy_mwhyr``
    and ``duration_min_h``/``duration_max_h`` (0 for non-split resources, whose
    energy sizing is fixed by ``duration_h``).
    """

    names: list[str]
    is_storage: np.ndarray  # (n_res,) bool
    fixed_mwyr: np.ndarray  # (n_res,) annualized $/MW-yr (0 for ppa_mwh)
    vom: np.ndarray  # (n_res,) $/MWh (ppa_mwh: cost + eac_premium)
    cap_max_mw: np.ndarray  # (n_res,) upper build bound
    cap_min_mw: np.ndarray  # (n_res,) lower build bound (existing floor)
    cf_assumed: np.ndarray  # (n_res,) placeholder CF (generation only)
    duration_h: np.ndarray  # (n_res,) fixed storage energy/power hours (0 if not)
    rte: np.ndarray  # (n_res,) round-trip efficiency (1.0 if not storage)
    # --- split-storage extensions (ADR 0006) ------------------------------
    is_split: np.ndarray = None  # (n_res,) bool; power/energy-split storage
    cost_energy_mwhyr: np.ndarray = None  # (n_res,) annualized $/MWh-yr energy capex
    duration_min_h: np.ndarray = None  # (n_res,) min hours (0 if not split)
    duration_max_h: np.ndarray = None  # (n_res,) max hours (0 if not split)

    def __post_init__(self) -> None:
        """Default the split-storage arrays to zeros/False when omitted.

        Keeps existing callers that build :class:`ResourceArrays` with only the
        original fields working (the split extensions become all-zero).
        """
        n = len(self.names)
        if self.is_split is None:
            object.__setattr__(self, "is_split", np.zeros(n, dtype=bool))
        if self.cost_energy_mwhyr is None:
            object.__setattr__(self, "cost_energy_mwhyr", np.zeros(n, dtype=float))
        if self.duration_min_h is None:
            object.__setattr__(self, "duration_min_h", np.zeros(n, dtype=float))
        if self.duration_max_h is None:
            object.__setattr__(self, "duration_max_h", np.zeros(n, dtype=float))

    @property
    def n_res(self) -> int:
        """Number of active resources."""
        return len(self.names)

    @property
    def storage_idx(self) -> np.ndarray:
        """Indices ``r`` of storage resources, in resource order."""
        return np.flatnonzero(self.is_storage)


def capital_recovery_factor(rate: float, life_yr: float) -> float:
    """Return the capital-recovery factor ``r(1+r)^n / ((1+r)^n - 1)``.

    Annualizes an overnight capital cost into a level payment over ``life_yr``
    years at real discount ``rate``. At ``rate == 0`` this degenerates to the
    straight-line ``1/life_yr``.
    """
    if life_yr <= 0:
        raise ValueError("life_yr must be positive")
    if rate == 0:
        return 1.0 / life_yr
    growth = (1.0 + rate) ** life_yr
    return rate * growth / (growth - 1.0)


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV into a list of row dicts."""
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    """Parse a possibly-blank CSV cell as float, defaulting when empty."""
    val = row.get(key, "")
    if val is None or str(val).strip() == "":
        return default
    return float(val)


def _req(row: dict[str, str], key: str, name: str) -> float:
    """Parse a REQUIRED numeric cell; a missing column or blank cell is an error.

    Guards against a misspelled/absent cost column silently producing a
    zero-cost ("free") resource via :func:`_f`'s default.
    """
    val = row.get(key)
    if val is None or str(val).strip() == "":
        raise ValueError(
            f"resource {name!r}: required cost column {key!r} is missing or blank"
        )
    return float(val)


def load_resource_caps(
    caps_table: Path | None = None,
) -> dict[str, dict[str, float]]:
    """Load the per-ISO cap table into ``{iso: {resource: cap_mw}}``.

    An ISO that appears in the returned mapping restricts eligibility to the
    resources it lists with ``cap_mw > 0`` (ADR 0009); an ISO absent from the
    mapping falls back to the cost table's ``cap_max_default_mw`` for every
    resource.
    """
    path = caps_table or DEFAULT_CAPS_TABLE
    caps: dict[str, dict[str, float]] = {}
    for row in _read_csv(path):
        iso = row["iso"].strip()
        caps.setdefault(iso, {})[row["resource"].strip()] = _f(row, "cap_mw")
    return caps


def load_hydro_budgets(iso: str, path: Path | None = None) -> np.ndarray:
    """Return the (12,) monthly hydro energy budget (GWh) for ``iso``.

    Reads ``data/hydro/monthly_budgets.csv``. Raises if the ISO is unknown or if
    the twelve calendar months are not all present. The LP energy-budget
    constraint that consumes this lands in PP-02b; this loader is the input seam.
    """
    src = path or DEFAULT_HYDRO_BUDGETS
    budget = np.full(12, np.nan)
    for row in _read_csv(src):
        if row["iso"].strip() != iso:
            continue
        month = int(row["month"])
        if not 1 <= month <= 12:
            raise ValueError(f"hydro budget month out of range: {month}")
        budget[month - 1] = _f(row, "budget_gwh")
    if np.isnan(budget).any():
        raise ValueError(f"no complete hydro monthly budget for iso {iso!r}")
    return budget


def _resolve_cap(
    name: str,
    config: PortfolioConfig,
    iso_caps: dict[str, float] | None,
    table_default: float,
) -> float:
    """Resolve the max build cap with precedence config > caps table > default."""
    if name in config.resource_caps_mw:
        return float(config.resource_caps_mw[name])
    if iso_caps is not None and name in iso_caps:
        return float(iso_caps[name])
    return table_default


def load_resource_arrays(
    config: PortfolioConfig,
    cost_table: Path | None = None,
    caps_table: Path | None = None,
) -> ResourceArrays:
    """Build :class:`ResourceArrays` for the resources active under ``config``.

    Selects rows by ``config.active_resources`` (or the table's
    ``active_minimal`` flag when unset), then filters by per-ISO eligibility from
    the caps table: if ``config.iso`` has any rows in the caps table, a resource
    with no row (or ``cap_mw == 0``) for that ISO is excluded; an ISO absent from
    the caps table keeps all selected resources at their table default cap.

    Costs are resolved per ``cost_basis`` at the ``config.lcoe_sensitivity``
    column (see the module docstring), and caps follow the precedence
    ``config.resource_caps_mw`` > caps table > ``cap_max_default_mw``.
    """
    path = cost_table or DEFAULT_COST_TABLE
    rows = _read_csv(path)

    sens = config.lcoe_sensitivity
    if sens not in ("low", "mid", "high"):
        raise ValueError(f"lcoe_sensitivity must be low/mid/high, got {sens!r}")

    # --- select the candidate rows (explicit list or active_minimal flag) ---
    if config.active_resources is not None:
        wanted = set(config.active_resources)
        rows = [r for r in rows if r["resource"] in wanted]
        missing = wanted - {r["resource"] for r in rows}
        if missing:
            raise ValueError(f"unknown resources requested: {sorted(missing)}")
    else:
        rows = [r for r in rows if r["active_minimal"].strip() == "1"]

    # --- per-ISO eligibility filter (ADR 0009) ------------------------------
    all_caps = load_resource_caps(caps_table)
    iso_caps = all_caps.get(config.iso)  # None => ISO absent => fall back to default
    if iso_caps is not None:
        rows = [
            r
            for r in rows
            if iso_caps.get(r["resource"], 0.0) > 0.0
            or r["resource"] in config.resource_caps_mw
        ]

    if not rows:
        raise ValueError(
            f"no active resources selected for iso {config.iso!r} — the per-ISO "
            "eligibility filter (caps table, ADR 0009) may have excluded every "
            "requested resource; check active_resources against "
            "data/caps/resource_caps.csv or override via resource_caps_mw"
        )

    crf_cache: dict[float, float] = {}

    def _crf(life: float) -> float:
        if life not in crf_cache:
            crf_cache[life] = capital_recovery_factor(config.discount_rate, life)
        return crf_cache[life]

    names: list[str] = []
    is_storage, is_split = [], []
    fixed_mwyr, vom, cost_energy_mwhyr = [], [], []
    cap_max, cap_min, cf_assumed = [], [], []
    duration_h, duration_min_h, duration_max_h, rte = [], [], [], []

    for row in rows:
        name = row["resource"]
        basis = row["cost_basis"]
        stor = row["category"] in ("storage", "storage_split")
        split = row["cost_basis"] == "split_storage"

        row_fixed = 0.0
        row_vom = _f(row, "vom")
        row_energy = 0.0
        row_dur = _f(row, "duration_h")
        row_dmin = _f(row, "duration_min_h")
        row_dmax = _f(row, "duration_max_h")

        if basis == "capex_fixed":
            # ATB overnight capex ($/kW) -> $/MW-yr via CRF, plus FOM ($/kW-yr).
            capex_kw = _req(row, f"capex_kw_{sens}", name)
            fom_kw_yr = _req(row, "fom_kw_yr", name)
            life = _f(row, "life_yr", 30.0)
            row_fixed = capex_kw * 1000.0 * _crf(life) + fom_kw_yr * 1000.0
        elif basis == "split_storage":
            # Power ($/kW) and energy ($/kWh) capex annualized separately.
            life = _f(row, "life_yr", 30.0)
            crf = _crf(life)
            cap_p_kw = _req(row, f"capex_power_kw_{sens}", name)
            cap_e_kwh = _req(row, f"capex_energy_kwh_{sens}", name)
            fom_p = _f(row, "fom_power_kw_yr")
            fom_e = _f(row, "fom_energy_kwh_yr")
            row_fixed = cap_p_kw * 1000.0 * crf + fom_p * 1000.0  # $/MW-yr (power)
            row_energy = cap_e_kwh * 1000.0 * crf + fom_e * 1000.0  # $/MWh-yr (energy)
            if not 0.0 < row_dmin <= row_dmax:
                raise ValueError(
                    f"resource {name!r}: split-storage duration bounds invalid "
                    f"({row_dmin}h .. {row_dmax}h)"
                )
        elif basis == "ppa_mwh":
            # Going-forward per-MWh cost + clean-attribute premium; no fixed cost.
            cost = _req(row, f"cost_{sens}", name)
            premium = config.eac_premium_mwh.get(name, _f(row, "eac_premium_mwh"))
            row_fixed = 0.0
            row_vom = cost + premium
        else:
            raise ValueError(f"unknown cost_basis {basis!r} for {name}")

        cap = _resolve_cap(name, config, iso_caps, _f(row, "cap_max_default_mw"))
        floor = config.resource_floors_mw.get(name, 0.0)
        if floor > cap:
            raise ValueError(
                f"resource {name!r}: floor {floor} MW exceeds cap {cap} MW "
                "(check resource_floors_mw vs resource_caps_mw/caps table)"
            )

        names.append(name)
        is_storage.append(stor)
        is_split.append(split)
        fixed_mwyr.append(row_fixed)
        vom.append(row_vom)
        cost_energy_mwhyr.append(row_energy)
        cap_max.append(cap)
        cap_min.append(floor)
        cf_assumed.append(_f(row, "cf_assumed"))
        duration_h.append(row_dur)
        duration_min_h.append(row_dmin)
        duration_max_h.append(row_dmax)
        rte.append(_f(row, "rte", 1.0) if stor else 1.0)

    return ResourceArrays(
        names=names,
        is_storage=np.array(is_storage, dtype=bool),
        fixed_mwyr=np.array(fixed_mwyr, dtype=float),
        vom=np.array(vom, dtype=float),
        cap_max_mw=np.array(cap_max, dtype=float),
        cap_min_mw=np.array(cap_min, dtype=float),
        cf_assumed=np.array(cf_assumed, dtype=float),
        duration_h=np.array(duration_h, dtype=float),
        rte=np.array(rte, dtype=float),
        is_split=np.array(is_split, dtype=bool),
        cost_energy_mwhyr=np.array(cost_energy_mwhyr, dtype=float),
        duration_min_h=np.array(duration_min_h, dtype=float),
        duration_max_h=np.array(duration_max_h, dtype=float),
    )
