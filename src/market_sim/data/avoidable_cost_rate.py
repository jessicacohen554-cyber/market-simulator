"""Read the curated ``capacity-market-avoidable-cost-rate`` clean datatype.

The model's *consumption seam* for an ISO's PUBLISHED default going-forward
bar — PJM's Manual 18 §5.4.8.4(B) "Default Gross Avoidable Cost Rate" table
and the reactive component its own capacity demand curve nets against that bar
(capx D62, building ``docs/handoffs/FINDING-capx-d61-2026-09-05.md`` §4). The
intake pipeline (``scripts/lib/capacity_market_avoidable_cost_rate`` →
``data/clean/capacity-market-avoidable-cost-rate``) reconciles both onto one
tidy frame; everything here returns **plain floats** keyed by the model's own
dispatch fuel class, and no Pydantic object crosses into the screen.

WHAT THIS IS FOR (rule 14 [R-ACCURATE], rule 13 [R-MEASURED]). The retirement
screen's going-forward cost has always been an **ATB FOM proxy**
(``ScenarioConfig.fixed_om_* × retirement_fom_multiplier_*``) standing in for
the bar the market actually caps sell offers with. D61 measured the gap: the
model's bars are 1.15× (CT), 1.5× (CC), 1.5× (steam), 2.0× (coal) the numbers
PJM publishes, and 61–74 % of resources elected exactly that published default
in the 2022/23–2025/26 BRAs. Substituting the published table for the proxy is
therefore *measured over estimate*, not a fit: the value is the mechanism's own
operand, it regenerates for any forward delivery year from the then-current
manual, and it responds to nothing but PJM's own filing.

**IT IS DATA, NOT CONFIG (rule 24 [R-REGISTRY]).** There is no scalar field
anywhere for these numbers — only the per-ISO gate
``ScenarioConfig.capacity_going_forward_bar_published_by_iso``, resolved
through :func:`~market_sim.config.capacity_market.
resolve_capacity_going_forward_bar_published`. A lane that wants a different
bar must change the published table, with its source page, in
``data/raw/capacity-market/avoidable-cost-rate/``.

**THE VINTAGE RULE IS FIXED IN CODE, NOT CHOSEN PER RUN (rule 21 [R-DOF]).**
See :data:`_PJM_VINTAGE_SWITCH_DELIVERY_YEAR` and :func:`_vintage_column_for`.
Selecting a column, an escalation or a UCAP/nameplate convention by looking at
a result is the failure mode D61 §3 names; the rule below was written into
``docs/handoffs/PRECOMMIT-capx-d62-pjm-acr-bar-2026-09-06.md`` §1.1 before any
solve and is not revisited.

The clean tree is derived and gitignored. Unlike
:mod:`market_sim.data.capacity_deliverability` — whose absence merely removes a
locational *limit*, so it degrades to a warning — a missing partition here
would silently restore the ATB proxy under an armed gate, i.e. a wrong answer
that looks like an answer. So an ARMED gate with unreadable data raises.
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

DATATYPE = "capacity-market-avoidable-cost-rate"

# ISOs with a published default-ACR table intaken. Generic in form, PJM-scoped
# by data (rule 25 [R-ISO-SCOPE]): PJM is the only registry ISO that publishes
# a generic technology-class going-forward bar its own market caps sell offers
# with. Another ISO's analogue (MISO's Module E-1 process, say) is that ISO's
# own lane, with its own crosswalk derived from its own filings.
SUPPORTED_ISOS: frozenset[str] = frozenset({"PJM"})

# --- The crosswalk: model dispatch fuel class -> PJM's own published label ---
#
# PJM's table (M18 Rev 62 §5.4.8.4(B)) publishes eight resource types; five map
# onto the seven fuel classes the retirement screen evaluates
# (``retirements._THERMAL_FOM``). Two facts are stated here rather than left
# implicit, both fixed before any solve:
#
#  * ``gas_st`` and ``oil`` BOTH map to "Steam Oil & Gas" — that is the source's
#    own single class for oil- and gas-fired steam, not a modelling choice;
#  * ``nuclear`` maps to "Nuclear – Multi Unit". PJM publishes a single-unit
#    row too ($697 / $591 vs $445 / $537 per MW-day) and the model carries no
#    site-unit-count attribute to tell them apart, so the multi-unit row — the
#    lower of the two, and the configuration the great majority of PJM's
#    nuclear MW sit in — is the one taken. Nuclear never binds this screen in
#    the T1-H window under either row.
#
# A fuel class ABSENT from this map (``gas_cc_ccs``) has no published PJM class
# at all: a capture-retrofitted combined cycle is not one of the eight resource
# types. Its bar therefore stays on the ATB path — stated ex ante because there
# is no published number to substitute, never because of a result. It is inert
# on any horizon ending before ``ccs_retrofit_available_year`` (2028) anyway,
# since no ``gas_cc_ccs`` unit exists to screen.
PUBLISHED_ACR_CLASS_BY_FUEL: dict[str, dict[str, str]] = {
    "PJM": {
        "coal": "Coal",
        "gas_cc": "Combined Cycle",
        "gas_ct": "Combustion Turbine",
        "gas_st": "Steam Oil & Gas",
        "oil": "Steam Oil & Gas",
        "nuclear": "Nuclear – Multi Unit",
    },
}

# --- The vintage rule (PRECOMMIT §1.1), fixed here -------------------------
#
# PJM's table carries the SAME resource-type rows in two dollar bases,
# distinguished in the intake only by the ``vintage`` string (``capacity_bin``
# is null on every row, so it cannot disambiguate them). Screen year Y prices
# delivery year Y/Y+1, so:
#
#   DY <= 2025/26  (screen year <= 2025)  ->  the "Through the 2025/2026
#                                             Delivery Years" column, 2022/23 $
#   DY >= 2026/27  (screen year >= 2026)  ->  the "For the 2026/2027 Delivery
#                                             Year and Subsequent" column
#
# Classes printed "n/a" in the first column — "Steam Oil & Gas" — read the
# FIRST PUBLISHED value, i.e. the 2026/27 column, and that fact is carried into
# the DOF ledger rather than silently absorbed. See :func:`_row_for`.
_PJM_VINTAGE_SWITCH_DELIVERY_YEAR: int = 2026
_VINTAGE_MARK_EARLY: str = "Through the 2025/2026 Delivery Years"
_VINTAGE_MARK_LATE: str = (
    "For the 2026/2027 Delivery Year and Subsequent Delivery Years"
)

# The published reactive component's rows: PJM's own E&AS-offset input, the
# SINGLE out-of-market credit the screen's margin carries (rule 19
# [R-ONE-MECH] — no uplift, no regulation, no black start; D61 §2b refuses
# each by name under rule 13's forward test).
_REACTIVE_COMPONENT: str = "reactive_offset"
_GROSS_ACR_COMPONENT: str = "gross_acr"


class PublishedBarUnavailable(RuntimeError):
    """An armed published-bar gate could not read its published table.

    Raised rather than degraded: falling back to the ATB proxy under an armed
    gate would run a DIFFERENT mechanism than the one the run declares, and
    would look like a result.
    """


@lru_cache(maxsize=8)
def _read(iso: str):
    """Return the clean frame for ``iso``, or ``None`` when unavailable."""
    up = iso.upper()
    if up not in SUPPORTED_ISOS:
        return None
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:  # pragma: no cover - packaging-only path
        logger.warning(
            "avoidable-cost-rate: scripts.lib.clean_io unavailable; no "
            "published bar for %s",
            up,
        )
        return None
    try:
        return read_clean(DATATYPE, iso=up)
    except FileNotFoundError:
        logger.warning(
            "avoidable-cost-rate: clean partition for %s absent; run "
            "scripts/data/curate_capacity_market_avoidable_cost_rate.py",
            up,
        )
        return None


def partition_available(iso: str) -> bool:
    """Whether ``iso`` has a readable published avoidable-cost-rate partition."""
    df = _read(iso)
    return df is not None and not df.empty


def _vintage_column_for(delivery_year: int) -> str:
    """Return the vintage marker the fixed rule selects for ``delivery_year``.

    ``delivery_year`` is the FIRST year of the delivery-year label (a screen in
    year Y prices DY Y/Y+1, so it is Y).
    """
    return (
        _VINTAGE_MARK_LATE
        if int(delivery_year) >= _PJM_VINTAGE_SWITCH_DELIVERY_YEAR
        else _VINTAGE_MARK_EARLY
    )


def _row_for(
    iso: str, technology_class: str, delivery_year: int
) -> "tuple[float, str]":
    """Return ``(value $/MW-day, basis)`` for one class at one delivery year.

    ``basis`` is ``"vintage"`` when the rule's own column carries the class and
    ``"first_published"`` when it does not (the "n/a" limb: the class is absent
    from the through-2025/26 column, so the first published value — the
    2026/27 column — is read, and the substitution is named).

    Raises :class:`PublishedBarUnavailable` when no row exists at all, or when
    the selected column carries more than one row for the class (an ambiguous
    table is a data change that must fail loudly, never be resolved by picking).
    """
    df = _read(iso)
    if df is None or df.empty:
        raise PublishedBarUnavailable(
            f"no published avoidable-cost-rate partition for {iso}: run "
            "scripts/data/curate_capacity_market_avoidable_cost_rate.py"
        )
    rows = df[
        (df["cost_component"] == _GROSS_ACR_COMPONENT)
        & (df["technology_class"] == technology_class)
    ]
    if rows.empty:
        raise PublishedBarUnavailable(
            f"{iso}: no published gross_acr row for technology class "
            f"{technology_class!r}"
        )
    want = _vintage_column_for(delivery_year)
    hit = rows[rows["vintage"].str.contains(want, regex=False, na=False)]
    basis = "vintage"
    if hit.empty:
        # The "n/a" limb of the fixed vintage rule (PRECOMMIT §1.1): the class
        # is not published in the column this delivery year selects, so the
        # FIRST published value is read and the substitution is reported.
        hit = rows
        basis = "first_published"
    if len(hit) != 1:
        raise PublishedBarUnavailable(
            f"{iso}: published gross_acr for {technology_class!r} at delivery "
            f"year {delivery_year} resolves to {len(hit)} rows, not 1 — the "
            "vintage rule cannot disambiguate; repair the intake rather than "
            "choosing a row"
        )
    row = hit.iloc[0]
    unit = str(row["unit"])
    if unit != "usd_per_mw_day":
        raise PublishedBarUnavailable(
            f"{iso}: published gross_acr for {technology_class!r} is in "
            f"{unit!r}; this seam converts $/MW-day only"
        )
    return float(row["value"]), basis


def published_bar_per_kw_yr(
    iso: str, fuel_type: str, delivery_year: int
) -> "tuple[float, str] | None":
    """The published going-forward bar in $/kW-yr NAMEPLATE, or ``None``.

    ``None`` when the ISO publishes no such table, or when ``fuel_type`` has no
    published class (``gas_cc_ccs``) — the caller then keeps the ATB path
    unchanged. Otherwise ``(value, basis)`` with ``value =
    $/MW-day × 365 / 1000`` and ``basis`` from :func:`_row_for`.

    NAMEPLATE, deliberately: PJM's table is denominated per nameplate MW-day,
    and the screen's own bar (``fixed_om × pmax_mw × 1000``) is likewise a
    nameplate quantity, so the substitution is unit-for-unit. The UCAP/ELCC
    accreditation seam is elsewhere (``_thermal_firm_mw``) and is untouched.
    """
    classes = PUBLISHED_ACR_CLASS_BY_FUEL.get(iso.upper())
    if not classes:
        return None
    technology_class = classes.get(fuel_type)
    if technology_class is None:
        return None
    value_per_mw_day, basis = _row_for(iso, technology_class, delivery_year)
    return value_per_mw_day * 365.0 / 1000.0, basis


@lru_cache(maxsize=8)
def reactive_offset_per_mw_yr(iso: str) -> "float | None":
    """The published reactive component in $/MW-yr, or ``None``.

    PJM's own capacity demand-curve E&AS-offset input (Tariff Schedule 2
    reactive revenue), the SOLE out-of-market leg of the screen's margin under
    the published-bar gate. ``None`` when the ISO has no such row.

    One published figure, applied class-wide: PJM computes it for the
    **reference resource**, and the screen credits every thermal unit
    ``pmax_mw × this`` — stated in the raw README beside the row, with the
    section's own reactive TOTAL ($380.7 M/yr over ~185 GW ≈ $2,060/MW-yr) as
    corroboration of the scale and NEVER as an identification.

    Raises :class:`PublishedBarUnavailable` if the row exists but is not in
    $/MW-yr, or resolves to more than one row.
    """
    df = _read(iso)
    if df is None or df.empty:
        return None
    rows = df[df["cost_component"] == _REACTIVE_COMPONENT]
    if rows.empty:
        return None
    if len(rows) != 1:
        raise PublishedBarUnavailable(
            f"{iso}: {len(rows)} reactive_offset rows, not 1 — the seam credits "
            "exactly one published reactive component (rule 19 [R-ONE-MECH])"
        )
    row = rows.iloc[0]
    unit = str(row["unit"])
    if unit != "usd_per_mw_yr":
        raise PublishedBarUnavailable(
            f"{iso}: reactive_offset is in {unit!r}; this seam reads usd_per_mw_yr only"
        )
    return float(row["value"])
