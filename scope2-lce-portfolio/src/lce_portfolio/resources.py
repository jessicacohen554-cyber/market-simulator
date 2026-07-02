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

Fuel-burning low-carbon rows (gas CC + CCS, ADR 0012) stay ``capex_fixed`` but
additionally carry ``heat_rate_mmbtu_mwh``/``capture_rate``/
``emission_rate_ton_mwh``: their effective VOM adds delivered gas fuel cost
(``data/fuel/gas_prices.csv`` or ``config.gas_price_mmbtu``) net of the IRA
§45Q credit, and the ADR 0012 admissibility threshold (capture > 0.90, residual
< 0.050 tCO2/MWh) is enforced at load time.
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
DEFAULT_GAS_PRICES = _PKG_ROOT / "data" / "fuel" / "gas_prices.csv"

# Pre-capture CO2 intensity of pipeline natural gas (tCO2/MMBtu burned).
# Source: EPA GHG Emission Factors Hub / 40 CFR Part 98 Table C-1: 53.06 kg
# CO2/MMBtu for pipeline natural gas (EIA carbon coefficient 52.91 kg/MMBtu
# agrees to <0.3%). Upstream methane is deliberately excluded (ADR 0012,
# deferred). Used both for the residual emission rate cross-check and to size
# the per-MWh 45Q credit: captured tCO2/MWh = capture_rate × this × heat_rate.
NG_CO2_TON_PER_MMBTU = 0.0531

# ADR 0012 low-carbon admissibility threshold for fossil matching resources: a
# resource counts fully toward hourly matching iff capture_rate > 0.90 (strict)
# AND residual emission rate < 0.050 tCO2/MWh (strict). A row failing either
# test is not admissible to the catalog at all — enforced at load time.
CCS_MIN_CAPTURE_RATE = 0.90
CCS_MAX_EMISSION_RATE_TON_MWH = 0.050

# Tolerance for the ADR 0012 residual-emission cross-check on fuel-burning
# rows: emission_rate_ton_mwh must equal (1 - capture_rate) ×
# NG_CO2_TON_PER_MMBTU × heat_rate up to CSV rounding (shipped rows state the
# rate to 4 decimals, so honest rounding error is ≤ 5e-5; 1e-3 leaves margin
# without letting a materially understated rate through).
CCS_EMISSION_CROSSCHECK_TOL_TON_MWH = 1e-3

# Resources whose annual energy is governed by a monthly energy budget rather than
# a flat CF — existing conventional hydro (ADR 0008, §Hydro). Kept as an explicit
# set here so the LP can flag budget-constrained resources without a magic string
# in the matrix builder.
HYDRO_BUDGET_RESOURCES = ("hydro_existing",)

GWH_TO_MWH = 1000.0  # 1 GWh = 1000 MWh (hydro budgets are stored in GWh)


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
    # --- existing-resource / additionality flags (ADR 0008) ---------------
    is_existing: np.ndarray = None  # (n_res,) bool; going-forward PPA (ppa_mwh)
    is_budget_hydro: np.ndarray = None  # (n_res,) bool; monthly-energy-budget hydro
    # --- residual emissions (ADR 0012) -------------------------------------
    emission_rate_ton_mwh: np.ndarray = None  # (n_res,) residual tCO2/MWh generated

    def __post_init__(self) -> None:
        """Default the optional flag arrays to zeros/False when omitted.

        Keeps existing callers that build :class:`ResourceArrays` with only the
        original fields working (the split-storage and existing-resource
        extensions become all-zero).
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
        if self.is_existing is None:
            object.__setattr__(self, "is_existing", np.zeros(n, dtype=bool))
        if self.is_budget_hydro is None:
            object.__setattr__(self, "is_budget_hydro", np.zeros(n, dtype=bool))
        if self.emission_rate_ton_mwh is None:
            object.__setattr__(self, "emission_rate_ton_mwh", np.zeros(n, dtype=float))

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
        resource = row["resource"].strip()
        if resource in caps.get(iso, {}):
            # Silent last-wins on a copy-paste duplicate hid a real data
            # error (audit finding DL-6; intake.py's dup=hard-error is the
            # house standard).
            raise ValueError(
                f"caps table {path}: duplicate row for ({iso!r}, {resource!r})"
            )
        cap = _f(row, "cap_mw")
        if np.isnan(cap) or cap < 0:
            raise ValueError(
                f"caps table {path}: cap_mw for ({iso!r}, {resource!r}) must "
                f"be a non-negative number, got {row.get('cap_mw')!r}"
            )
        caps.setdefault(iso, {})[resource] = cap
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
        if not np.isnan(budget[month - 1]):
            raise ValueError(
                f"hydro budget table {src}: duplicate month {month} for iso "
                f"{iso!r} (audit finding DL-10)"
            )
        raw = row.get("budget_gwh")
        if raw is None or str(raw).strip() == "":
            # _f's 0.0 default would silently zero a whole month of hydro.
            raise ValueError(
                f"hydro budget table {src}: blank budget_gwh for iso {iso!r} "
                f"month {month} — a blank cell is a data error, not zero"
            )
        val = float(raw)
        if val < 0:
            raise ValueError(
                f"hydro budget table {src}: negative budget_gwh ({val}) for "
                f"iso {iso!r} month {month}"
            )
        budget[month - 1] = val
    if np.isnan(budget).any():
        raise ValueError(f"no complete hydro monthly budget for iso {iso!r}")
    return budget


def load_hydro_budget_mwh(iso: str, path: Path | None = None) -> np.ndarray | None:
    """Return the (12,) monthly hydro budget in **MWh** for ``iso``, or ``None``.

    Wraps :func:`load_hydro_budgets` for LP use: converts the stored GWh to MWh
    (the LP's energy unit) and returns ``None`` — rather than raising — when the
    ISO has no rows in the budget table. This lets ISOs without a budget entry
    (e.g. the ``SAMPLE`` ISO) simply skip the hydro-budget constraint (ADR 0008).
    """
    src = path or DEFAULT_HYDRO_BUDGETS
    known_isos = {row["iso"].strip() for row in _read_csv(src)}
    if iso not in known_isos:
        return None
    return load_hydro_budgets(iso, path) * GWH_TO_MWH


def load_gas_price(iso: str, path: Path | None = None) -> float | None:
    """Return the delivered natural-gas price ($/MMBtu) for ``iso``, or ``None``.

    Reads ``data/fuel/gas_prices.csv`` (ADR 0012): per-ISO delivered prices for
    the ~2030 modeled year at the market simulator's forward-mode fidelity
    (AEO2025 Reference Henry Hub + per-ISO basis differential; see the table's
    ``basis``/``notes`` columns for citations). Mirrors the
    :func:`load_hydro_budget_mwh` pattern: an ISO with no row returns ``None``
    rather than raising, so the caller decides whether a missing price matters
    (it is fatal only when a fuel-burning resource is active). A non-positive
    table price is a data error and raises.
    """
    src = path or DEFAULT_GAS_PRICES
    price: float | None = None
    for row in _read_csv(src):
        if row["iso"].strip() != iso:
            continue
        if price is not None:
            # First-match-wins silently masked a conflicting duplicate row
            # (audit finding DL-6).
            raise ValueError(f"gas price table {src}: duplicate row for iso {iso!r}")
        price = _f(row, "price_mmbtu")
        if price <= 0:
            raise ValueError(
                f"gas price table {src}: non-positive price_mmbtu for iso {iso!r}"
            )
    return price


def _resolve_gas_price(config: PortfolioConfig, gas_table: Path | None) -> float | None:
    """Resolve the delivered gas price with precedence config > table > None.

    A ``config.gas_price_mmbtu > 0`` explicit override wins; otherwise the
    per-ISO table value; otherwise ``None`` (the caller raises if a
    fuel-burning resource actually needs it — ADR 0012).
    """
    if config.gas_price_mmbtu > 0:
        return config.gas_price_mmbtu
    return load_gas_price(config.iso, gas_table)


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
    gas_table: Path | None = None,
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

    **Fuel-burning low-carbon resources (ADR 0012).** A row with
    ``heat_rate_mmbtu_mwh > 0`` (gas CC + CCS) gets its fuel cost and IRA §45Q
    credit folded into its effective VOM at load time::

        vom = vom_table + heat_rate × delivered_gas_price
              − capture_rate × (0.0531 tCO2/MMBtu × heat_rate) × ccs_45q_per_ton

    clamped at ≥ 0. The delivered gas price resolves as
    ``config.gas_price_mmbtu`` (> 0 wins) > per-ISO ``data/fuel/gas_prices.csv``
    (``gas_table`` overrides the path) > hard error — a fuel-burning resource
    must never dispatch at zero fuel cost. The ADR 0012 admissibility threshold
    (``capture_rate > 0.90`` and ``emission_rate_ton_mwh < 0.050``) is enforced
    here for every row: qualifying output counts *fully* toward matching (no
    intensity-weighted discount), and its residual CO2 is reported via
    ``emission_rate_ton_mwh``. Additionality (ADR 0008) deliberately does NOT
    sweep CCS in: ``is_existing`` stays keyed to ``cost_basis == "ppa_mwh"``
    only, so the ``gas_cc_ccs_retrofit`` tranche — capex-basis new capture
    capacity bolted onto an existing plant — counts as new/additional supply.
    """
    path = cost_table or DEFAULT_COST_TABLE
    rows = _read_csv(path)

    # Key-cell hygiene (audit finding DL-11): strip categorical cells so a
    # stray space (e.g. " storage") cannot silently declassify a row, and
    # fail with the file named when a required column is absent (DL-13).
    required_cols = ("resource", "category", "cost_basis")
    for col in required_cols:
        if rows and col not in rows[0]:
            raise ValueError(f"cost table {path}: missing required column {col!r}")
    for r in rows:
        for col in required_cols:
            r[col] = (r[col] or "").strip()

    seen_names: set[str] = set()
    for r in rows:
        if r["resource"] in seen_names:
            # A duplicated resource row would instantiate the resource twice,
            # silently doubling its buildable capacity (audit finding DL-6).
            raise ValueError(
                f"cost table {path}: duplicate resource row {r['resource']!r}"
            )
        seen_names.add(r["resource"])

    sens = config.lcoe_sensitivity
    if sens not in ("low", "mid", "high"):
        raise ValueError(f"lcoe_sensitivity must be low/mid/high, got {sens!r}")

    # Config eac_premium_mwh overrides apply only to ppa_mwh existing
    # resources (documented in config.py); a key that matches nothing would
    # silently no-op (audit finding DL-9), so validate against the catalog.
    ppa_names = {r["resource"] for r in rows if r["cost_basis"] == "ppa_mwh"}
    bad_overrides = set(config.eac_premium_mwh) - ppa_names
    if bad_overrides:
        raise ValueError(
            f"eac_premium_mwh overrides {sorted(bad_overrides)} do not match "
            f"any ppa_mwh resource in {path}; have {sorted(ppa_names)}"
        )

    # --- select the candidate rows (explicit list or active_minimal flag) ---
    if config.active_resources is not None:
        wanted = set(config.active_resources)
        rows = [r for r in rows if r["resource"] in wanted]
        missing = wanted - {r["resource"] for r in rows}
        if missing:
            raise ValueError(f"unknown resources requested: {sorted(missing)}")
    else:
        if rows and "active_minimal" not in rows[0]:
            raise ValueError(
                f"cost table {path}: missing required column 'active_minimal' "
                "(needed when config.active_resources is unset)"
            )
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

    # Delivered gas price is resolved lazily: only a fuel-burning row forces the
    # lookup, so runs without CCS never touch the fuel table (ADR 0012).
    gas_price_resolved = False
    gas_price: float | None = None

    names: list[str] = []
    is_storage, is_split = [], []
    is_existing, is_budget_hydro = [], []
    fixed_mwyr, vom, cost_energy_mwhyr = [], [], []
    cap_max, cap_min, cf_assumed = [], [], []
    duration_h, duration_min_h, duration_max_h, rte = [], [], [], []
    emission_rate = []

    for row in rows:
        name = row["resource"]
        basis = row["cost_basis"]
        stor = row["category"] in ("storage", "storage_split")
        split = row["cost_basis"] == "split_storage"
        existing = basis == "ppa_mwh"  # going-forward PPA existing resource
        budget_hydro = name in HYDRO_BUDGET_RESOURCES

        row_fixed = 0.0
        row_vom = _f(row, "vom")
        row_energy = 0.0
        row_dur = _f(row, "duration_h")
        row_dmin = _f(row, "duration_min_h")
        row_dmax = _f(row, "duration_max_h")

        # --- ADR 0012: partial-capture fossil resource columns --------------
        row_heat_rate = _f(row, "heat_rate_mmbtu_mwh")  # MMBtu/MWh; 0 = no fuel
        if row_heat_rate > 0.0:
            # Fuel-burning rows must state capture and residual emissions
            # explicitly: a blank cell would default to 0.0, silently passing
            # the emission test and skipping the capture test — letting
            # unabated gas into the catalog as a fully-matching zero-emission
            # resource (audit finding DL-2).
            row_capture = _req(row, "capture_rate", name)
            row_emission = _req(row, "emission_rate_ton_mwh", name)
            if not 0.0 < row_capture <= 1.0:
                raise ValueError(
                    f"resource {name!r}: capture_rate={row_capture} must be in "
                    "(0, 1] — a rate above 1 would size the 45Q credit beyond "
                    "the fuel's CO2 content (audit finding DL-3)"
                )
        else:
            row_capture = _f(row, "capture_rate")  # fraction; 0/blank = not set
            row_emission = _f(row, "emission_rate_ton_mwh")  # residual tCO2/MWh

        # Low-carbon admissibility threshold (ADR 0012), enforced at load time:
        # matching credit is all-or-nothing, so a fossil row that fails either
        # bright-line test must never enter the catalog at all.
        if row_emission >= CCS_MAX_EMISSION_RATE_TON_MWH:
            raise ValueError(
                f"resource {name!r}: emission_rate_ton_mwh={row_emission} fails the "
                f"ADR 0012 low-carbon threshold (must be < "
                f"{CCS_MAX_EMISSION_RATE_TON_MWH} tCO2/MWh to count toward matching)"
            )
        if row_capture > 0.0 and row_capture <= CCS_MIN_CAPTURE_RATE:
            raise ValueError(
                f"resource {name!r}: capture_rate={row_capture} fails the ADR 0012 "
                f"low-carbon threshold (must be > {CCS_MIN_CAPTURE_RATE} to count "
                "toward matching)"
            )
        if row_heat_rate > 0.0:
            # Residual-emission cross-check (promised by the
            # NG_CO2_TON_PER_MMBTU docstring, audit finding DL-3): the stated
            # residual rate must be consistent with the stated capture rate
            # and heat rate, so a row cannot understate its emissions to slip
            # under the threshold.
            implied = (1.0 - row_capture) * NG_CO2_TON_PER_MMBTU * row_heat_rate
            if abs(row_emission - implied) > CCS_EMISSION_CROSSCHECK_TOL_TON_MWH:
                raise ValueError(
                    f"resource {name!r}: emission_rate_ton_mwh={row_emission} is "
                    f"inconsistent with (1 - capture_rate) × "
                    f"{NG_CO2_TON_PER_MMBTU} tCO2/MMBtu × heat_rate = "
                    f"{implied:.5f} tCO2/MWh (ADR 0012 cross-check, tolerance "
                    f"{CCS_EMISSION_CROSSCHECK_TOL_TON_MWH})"
                )

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
            if premium < 0:
                # config overrides are validated in PortfolioConfig; this
                # catches a negative TABLE value, which would drive vom
                # negative and pay the LP to dispatch (audit finding DL-9).
                raise ValueError(
                    f"resource {name!r}: eac_premium_mwh must be non-negative, "
                    f"got {premium}"
                )
            row_fixed = 0.0
            row_vom = cost + premium
        else:
            raise ValueError(f"unknown cost_basis {basis!r} for {name}")

        # --- fuel cost + 45Q for fuel-burning rows (ADR 0012) ----------------
        if row_heat_rate > 0.0:
            if not gas_price_resolved:
                gas_price = _resolve_gas_price(config, gas_table)
                gas_price_resolved = True
            if gas_price is None:
                raise ValueError(
                    f"resource {name!r} burns gas (heat_rate_mmbtu_mwh="
                    f"{row_heat_rate}) but no delivered gas price is available "
                    f"for iso {config.iso!r}: set config.gas_price_mmbtu (> 0) "
                    "or add a row to data/fuel/gas_prices.csv — a fuel-burning "
                    "resource must not dispatch at zero fuel cost (ADR 0012)"
                )
            # Net variable cost (ADR 0012): capture/fixed-O&M VOM component from
            # the table, plus fuel, minus the 45Q credit on captured CO2:
            #   vom = vom_table + heat_rate × delivered_gas
            #         − capture_rate × (NG_CO2_TON_PER_MMBTU × heat_rate) × 45Q
            captured_ton_mwh = row_capture * NG_CO2_TON_PER_MMBTU * row_heat_rate
            row_vom = (
                row_vom
                + row_heat_rate * gas_price
                - captured_ton_mwh * config.ccs_45q_per_ton
            )
            # Clamp at zero: at low gas prices a $85/t 45Q can exceed fuel+VOM,
            # and a negative net VOM would pay the LP to generate into the
            # excess/dump path to farm the credit. The real credit is bounded by
            # actually-stored tonnage; modeling sub-zero variable cost is out of
            # scope (ADR 0012), so the floor keeps the LP honest.
            row_vom = max(0.0, row_vom)

        # Storage rows must state their physics explicitly (audit DL-11):
        # a blank duration_h would build a 0-hour dead battery and a blank
        # rte would default to lossless round-trip, both silently.
        if stor and not split:
            if row_dur <= 0:
                raise ValueError(
                    f"resource {name!r}: storage rows require duration_h > 0, "
                    f"got {row_dur}"
                )
        row_rte = 1.0
        if stor:
            row_rte = _req(row, "rte", name)
            if not 0.0 < row_rte <= 1.0:
                raise ValueError(
                    f"resource {name!r}: rte must be in (0, 1], got {row_rte}"
                )

        cap = _resolve_cap(name, config, iso_caps, _f(row, "cap_max_default_mw"))
        if np.isnan(cap) or cap < 0:
            # A NaN default cell would flow straight into the LP column
            # bounds (audit finding DL-5).
            raise ValueError(
                f"resource {name!r}: resolved cap_max is not a non-negative "
                f"number ({cap}); check cap_max_default_mw / caps table / "
                "resource_caps_mw"
            )
        floor = config.resource_floors_mw.get(name, 0.0)
        if floor > cap:
            raise ValueError(
                f"resource {name!r}: floor {floor} MW exceeds cap {cap} MW "
                "(check resource_floors_mw vs resource_caps_mw/caps table)"
            )

        names.append(name)
        is_storage.append(stor)
        is_split.append(split)
        is_existing.append(existing)
        is_budget_hydro.append(budget_hydro)
        fixed_mwyr.append(row_fixed)
        vom.append(row_vom)
        cost_energy_mwhyr.append(row_energy)
        cap_max.append(cap)
        cap_min.append(floor)
        cf_assumed.append(_f(row, "cf_assumed"))
        duration_h.append(row_dur)
        duration_min_h.append(row_dmin)
        duration_max_h.append(row_dmax)
        rte.append(row_rte)
        emission_rate.append(row_emission)

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
        is_existing=np.array(is_existing, dtype=bool),
        is_budget_hydro=np.array(is_budget_hydro, dtype=bool),
        emission_rate_ton_mwh=np.array(emission_rate, dtype=float),
    )
