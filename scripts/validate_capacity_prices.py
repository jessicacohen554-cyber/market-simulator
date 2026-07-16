#!/usr/bin/env python3
"""Validate the CR-1 sloped capacity demand curves against auction history (P-2A / CR-2).

**Comparison only** (rules 1/13/23): this tool evaluates the *implemented* capacity
demand curves (``config.constants.MARKET_DESIGN``) against published auction
outcomes and reports residuals. It never adjusts a curve parameter, never fits a
multiplier, never writes into the model. It answers the CR-2 question the plan
poses (``docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md``
§3.3 / §2 T3.1):

    Do the published-parameter demand curves, evaluated at the auctions' own
    (fleet-independent) reserve positions, reproduce the observed clearing-price
    *regime* — order-of-magnitude and direction — NOT a fitted match?

Two passes per capacity-market ISO:

* **Pass 1 — curve isolated from the fleet.** Placed on the ISO's *own published*
  demand curve using only published quantities (that year's net-CONE, price cap,
  curve x-positions, clearing price) — not the model's evolved fleet, so *curve*
  error is isolated from *fleet* error. Two views:
    - **1A shape reproduction** — the implemented normalized curve's price *fraction
      of net-CONE* at each year's published curve x-positions vs the published
      fractions (published cap ÷ net-CONE). Pure shape, no dollars, no circularity.
    - **1B price reproduction** — the implemented curve's dollar price at the
      published cleared reserve position vs the published clearing price.

* **Pass 2 — curve on the model's own hindcast fleet.** For ISOs with a capacity
  hindcast (ERCOT excluded; only PJM has one today), recover the model's *own*
  accredited reserve position per solved year from the persisted evolution ledger
  (``firm_mw / requirement`` — the exact basis :func:`capacity_reserve_position`
  uses), read the model curve there, compare to the published clearing price. The
  Pass-1 vs Pass-2 gap is the fleet-position error.

Governance (rule 22): delivery years labelled 2026 or later, and any price that is
a 2026-dated observation of the current capability year, are ``locked`` (H1-2026
forward edge) — reported greyed and excluded from every verdict. No LP solves run;
nothing is registered on any dashboard (forecast/validation probe).

Usage::

    python -m scripts.validate_capacity_prices --markdown \\
        --out results/capacity-price-validation/validation.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from market_sim.config.constants import (
    EFORD,
    MARKET_DESIGN,
    MISO_SEASONAL_RBDC,
    CapacityDemandCurvePoint,
    evaluate_demand_curve,
    resolve_capacity_curve_eligible,
    resolve_demand_curve_vintage,
)
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import (
    resolve_adequacy_requirement_mw,
    thermal_accreditation_fraction,
)

CAPMKT_RAW = RAW_DATA_DIR / "capacity-market"
HINDCAST_ROOT = Path("results/hindcast")

# ISOs running a centrally-cleared capacity auction with a published sloped demand
# curve. CAISO is bilateral RA (fixed proxy, no curve) — reported, not slope-scored.
CURVE_ISOS = ("PJM", "NYISO", "NEISO", "MISO")

# Non-ERCOT capacity hindcasts that exist today (plan §1 D10). ERCOT is energy-only.
# Override or extend per invocation with --pass2-run ISO=<run dir name|path>
# (the RC-1A probe-fleet restatements, plan §3 T-R4). MISO added 2026-07-16
# (RC-1A) — its committed hindcast landed 2026-07-14.
HINDCAST_RUNS = {
    "PJM": "pjm-2021-2025-realized",
    "MISO": "miso-2021-2025-realized",
}


# --------------------------------------------------------------------------- #
# Units — everything compared in $/kW-yr (UCAP basis, as published)
# --------------------------------------------------------------------------- #
def to_kw_yr(value: float, unit: str) -> float:
    """Annualize a published capacity price/anchor to $/kW-yr."""
    u = unit.strip().lower()
    if u in ("usd_per_mw_day", "usd_per_mw_day_icap"):
        return value * 365.0 / 1000.0
    if u == "usd_per_kw_month":
        return value * 12.0
    if u == "usd_per_kw_yr":
        return value
    if u == "usd_per_mw_yr":
        return value / 1000.0
    raise ValueError(f"unhandled price unit: {unit!r}")


def kw_yr_to_mw_day(value_kw_yr: float) -> float:
    """$/kW-yr -> $/MW-day (display for $/MW-day-native ISOs)."""
    return value_kw_yr * 1000.0 / 365.0


# --------------------------------------------------------------------------- #
# Delivery-year labels + locked-window governance (rule 22)
# --------------------------------------------------------------------------- #
def delivery_start_year(label: str) -> int:
    """First calendar year of a label ('2025/2026', '2020/21', '2025')."""
    return int(label.replace("-", "/").split("/")[0].strip())


def canon_year(label: str) -> str:
    """Canonical 'YYYY/YYYY' key so '2025/26', '2025-2026', '2025/2026' all match."""
    s = delivery_start_year(label)
    return f"{s}/{s + 1}"


def is_locked(iso: str, label: str, source_doc: str) -> bool:
    """True if a row falls in the locked H1-2026 forward edge (rule 22).

    Locked when the delivery-year label starts in 2026+ (forward-edge auctions:
    PJM 2026/2027, ISO-NE 2026-2027), or when the clearing price is a 2026-dated
    observation of the current capability year (NYISO's 2025/26 spot is a
    2026-published SOM average running into H1-2026). Locked rows are shown greyed
    and excluded from every verdict.
    """
    if delivery_start_year(label) >= 2026:
        return True
    if iso == "NYISO" and delivery_start_year(label) >= 2025 and "2026" in source_doc:
        return True
    return False


# --------------------------------------------------------------------------- #
# Raw P-0B CSV loaders (immutable source of truth)
# --------------------------------------------------------------------------- #
def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _f(row: dict, key: str) -> float | None:
    v = (row.get(key) or "").strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_demand_curve(iso: str) -> list[dict]:
    return _read_csv(CAPMKT_RAW / "demand-curve" / iso.lower() / f"{iso.lower()}.csv")


def load_auction_price(iso: str) -> list[dict]:
    return _read_csv(CAPMKT_RAW / "auction-price" / iso.lower() / f"{iso.lower()}.csv")


# --------------------------------------------------------------------------- #
# Per-ISO published curve anchors, reduced to what the validation needs
# --------------------------------------------------------------------------- #
@dataclass
class YearParams:
    """One delivery year's published curve anchors (annualized to $/kW-yr)."""

    net_cone_kw_yr: float  # demand-curve reference-point price (per-ISO basis)
    net_cone_ucap_kw_yr: float | None  # published UCAP $/MW-yr net-CONE where given
    price_cap_kw_yr: float | None
    ref_x: float
    cap_x: float
    zero_x: float
    cap_frac_source: str  # published | model_shape_proxy | first_order


def pjm_year_params(rows: list[dict]) -> dict[str, YearParams]:
    """PJM VRR anchors per delivery year.

    ``net_cone_kw_yr`` is the demand-curve reference-point price (the $/MW-day
    figure the VRR curve is drawn around); ``net_cone_ucap_kw_yr`` is PJM's
    separately-published UCAP $/MW-yr net-CONE (the two differ by PJM's ~0.78
    ICAP<->UCAP factor — the #1532 basis flag). x-positions are the Manual-18
    points (0 = cap plateau end, 1 = reference, 2 = zero-cross). Price cap
    published for 2026/27+; where absent (2025/26) the model's normalized cap
    fraction stands in (flagged model_shape_proxy).
    """
    by_year: dict[str, dict] = {}
    for r in rows:
        d = by_year.setdefault(r["delivery_year"], {})
        m, yu = r["metric"], r["y_unit"]
        if m == "net_cone" and yu == "usd_per_mw_day":
            d["nc_day"] = to_kw_yr(_f(r, "y_value"), yu)
        elif m == "net_cone" and yu == "usd_per_mw_yr":
            d["nc_ucap"] = to_kw_yr(_f(r, "y_value"), yu)
        elif m == "price_cap" and yu == "usd_per_mw_day":
            d["cap"] = to_kw_yr(_f(r, "y_value"), yu)
        elif m == "curve_point":
            d.setdefault("pts", {})[int(float(r["point_index"]))] = _f(r, "x_value")
    model_cap_frac = _model_cap_frac("PJM")
    out: dict[str, YearParams] = {}
    for y, d in by_year.items():
        if "nc_day" not in d or "pts" not in d or len(d["pts"]) < 3:
            continue
        nc = d["nc_day"]
        cap = d.get("cap")
        out[canon_year(y)] = YearParams(
            net_cone_kw_yr=nc,
            net_cone_ucap_kw_yr=d.get("nc_ucap"),
            price_cap_kw_yr=cap if cap else model_cap_frac * nc,
            ref_x=d["pts"][1],
            cap_x=d["pts"][0],
            zero_x=d["pts"][2],
            cap_frac_source="published" if cap else "model_shape_proxy",
        )
    return out


def _neiso_fca11_geometry(rows: list[dict]) -> dict[str, float]:
    """Net-ICR-normalized cap/zero reserve positions from the FCA11 MW curve.

    The published FCA11 (2020-2021) curve is in MW; the Net ICR is the MW where
    price == net-CONE. Positions are MW / Net-ICR — the exact construction the
    implemented _NEISO_FCA_CURVE used.
    """
    pts: list[tuple[float, float]] = []
    nc = None
    for r in rows:
        if r["delivery_year"] != "2020-2021":
            continue
        if r["metric"] == "net_cone":
            nc = _f(r, "y_value")
        elif r["metric"] == "curve_point" and r["x_unit"] == "mw":
            pts.append((_f(r, "x_value"), _f(r, "y_value")))
    pts.sort()
    net_icr = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (y0 - nc) * (y1 - nc) <= 0 and y0 != y1:
            net_icr = x0 + (y0 - nc) / (y0 - y1) * (x1 - x0)
            break
    peak_price = max(p[1] for p in pts)
    cap_plateau_end = max(x for x, y in pts if math.isclose(y, peak_price))
    zero_x_mw = max(x for x, y in pts if y == 0.0)
    return {"cap_x": cap_plateau_end / net_icr, "zero_x": zero_x_mw / net_icr}


def neiso_year_params(rows: list[dict]) -> dict[str, YearParams]:
    """ISO-NE FCA anchors per delivery year (net-CONE + starting price published
    each year; reserve-position geometry from the FCA11 MW curve, held constant
    exactly as the implemented curve does)."""
    geom = _neiso_fca11_geometry(rows)
    by_year: dict[str, dict] = {}
    for r in rows:
        if r["metric"] in ("net_cone", "price_cap"):
            key = "nc" if r["metric"] == "net_cone" else "cap"
            by_year.setdefault(r["delivery_year"], {})[key] = to_kw_yr(
                _f(r, "y_value"), r["y_unit"]
            )
    out: dict[str, YearParams] = {}
    for y, d in by_year.items():
        if "nc" not in d:
            continue
        out[canon_year(y)] = YearParams(
            net_cone_kw_yr=d["nc"],
            net_cone_ucap_kw_yr=d["nc"],
            price_cap_kw_yr=d.get("cap"),
            ref_x=1.0,
            cap_x=geom["cap_x"],
            zero_x=geom["zero_x"],
            cap_frac_source="published",
        )
    return out


_NYISO_CURVE_LENGTH = 0.12  # NYCA Demand Curve Length, DCR-cycle-invariant


def nyiso_year_params(rows: list[dict]) -> dict[str, YearParams]:
    """NYISO NYCA PER-VINTAGE anchors (RC-1C): each delivery year on its OWN
    published Annual Reference Value (net-CONE), max clearing price (cap), and
    monthly reference-point price — no frozen single-vintage anchor held across
    years. The zero-cross is 100% + the 12% Demand Curve Length (DCR-cycle-
    invariant); the cap x-position is 1 − (cap_frac − 1)×12% (the implemented
    ``_nyiso_icap_vintage_curve`` geometry). A season-split vintage (2025-2026)
    uses its SUMMER cap/reference (the binding season, matching the registry).
    2021-22/2022-23 publish NO Annual Reference Value and no cap (only a
    reference point + IRM) → NO params, so Pass 1 reports them as non-scoreable
    with no interpolation (explicit sparse handling)."""
    by_year: dict[str, dict] = {}
    for r in rows:
        if r["area"] != "NYCA":
            continue
        y = canon_year(r["delivery_year"])
        d = by_year.setdefault(y, {})
        m, season = r["metric"], (r.get("season") or "").strip()
        if m == "net_cone":
            d["nc"] = to_kw_yr(_f(r, "y_value"), r["y_unit"])
        elif m == "price_cap" and ("cap_month" not in d or season == "summer"):
            d["cap_month"] = _f(r, "y_value")  # $/kW-month
        elif m == "curve_point" and int(float(r["point_index"])) == 0:
            if "ref_month" not in d or season == "summer":
                d["ref_month"] = _f(r, "y_value")  # $/kW-month reference point
    out: dict[str, YearParams] = {}
    for y, d in by_year.items():
        if "nc" not in d or "cap_month" not in d or "ref_month" not in d:
            continue  # 2021-22/2022-23: no ARV/cap → non-scoreable (sparse)
        cap_frac = d["cap_month"] / d["ref_month"]
        out[y] = YearParams(
            net_cone_kw_yr=d["nc"],
            net_cone_ucap_kw_yr=d["nc"],
            price_cap_kw_yr=cap_frac * d["nc"],
            ref_x=1.0,
            cap_x=1.0 - (cap_frac - 1.0) * _NYISO_CURVE_LENGTH,
            zero_x=1.0 + _NYISO_CURVE_LENGTH,
            cap_frac_source="published",
        )
    return out


def miso_year_params(rows: list[dict]) -> dict[str, YearParams]:
    """MISO annual anchors (North/Central Net CONE; RBDC shape first-order, CR-3)."""
    out: dict[str, YearParams] = {}
    for r in rows:
        if r["metric"] == "net_cone" and r["y_unit"] == "usd_per_mw_yr":
            nc = to_kw_yr(_f(r, "y_value"), r["y_unit"])
            out[canon_year(r["delivery_year"])] = YearParams(
                net_cone_kw_yr=nc,
                net_cone_ucap_kw_yr=nc,
                price_cap_kw_yr=1.596 * nc,
                ref_x=1.0,
                cap_x=0.97,
                zero_x=1.05,
                cap_frac_source="first_order",
            )
    return out


YEAR_PARAM_BUILDERS = {
    "PJM": pjm_year_params,
    "NEISO": neiso_year_params,
    "NYISO": nyiso_year_params,
    "MISO": miso_year_params,
}


# --------------------------------------------------------------------------- #
# Implemented (model) curve — call the REAL code, never a reimplementation
# --------------------------------------------------------------------------- #
def _model_cap_frac(iso: str) -> float:
    return MARKET_DESIGN[iso].demand_curve[0].price_frac_net_cone


def model_vintage_curve_anchor(
    iso: str, year: int | None
) -> tuple[tuple[CapacityDemandCurvePoint, ...], float]:
    """The model's (curve, net-CONE anchor $/kW-yr) for ``iso`` at ``year``.

    ``year=None`` uses the registry reference (byte-identical to the pre-RC-1C
    tool). A given ``year`` consults the shipped per-delivery-year vintage table
    (:func:`resolve_demand_curve_vintage`, RC-1B) so the model side is scored on
    each delivery year's OWN published parameters — no frozen single-vintage
    anchor held across years (rule 13). A ()-shape vintage (flat anchor, no
    normalizable curve) returns an empty curve; the caller prices its flat anchor.
    """
    d = MARKET_DESIGN[iso]
    curve = d.demand_curve
    anchor = d.net_cone_curve_per_kw_yr or d.net_cone_per_kw_yr
    if year is not None:
        v = resolve_demand_curve_vintage(iso, year)
        if v is not None:
            anchor = v.net_cone_curve_per_kw_yr or anchor
            curve = v.demand_curve
    return curve, anchor


def model_curve_frac(
    iso: str, reserve_position: float, year: int | None = None
) -> float:
    """Implemented normalized curve's price fraction of net-CONE at a position."""
    curve, _ = model_vintage_curve_anchor(iso, year)
    return evaluate_demand_curve(curve, reserve_position)


def model_curve_price_kw_yr(
    iso: str, reserve_position: float, year: int | None = None
) -> float:
    """Implemented CR-1 curve price at a reserve position, $/kW-yr (real seam).

    A ()-shape vintage (no normalizable curve) prices its flat anchor,
    position-independent — mirroring the seam's flat-anchor fallback.
    """
    curve, anchor = model_vintage_curve_anchor(iso, year)
    if not curve:
        return anchor
    return evaluate_demand_curve(curve, reserve_position) * anchor


def model_net_cone_kw_yr(iso: str, year: int | None = None) -> float:
    _, anchor = model_vintage_curve_anchor(iso, year)
    return anchor


# --------------------------------------------------------------------------- #
# Invert a year's OWN published curve (fleet-independent reserve position)
# --------------------------------------------------------------------------- #
def own_curve_anchors(p: YearParams) -> list[tuple[float, float]]:
    """Normalized (reserve_ratio, price/net-CONE) anchors of a year's own curve."""
    anchors = [(p.ref_x, 1.0), (p.zero_x, 0.0)]
    if p.price_cap_kw_yr:
        anchors.append((p.cap_x, p.price_cap_kw_yr / p.net_cone_kw_yr))
    return sorted(anchors)


def invert_own_curve(p: YearParams, price_kw_yr: float) -> float:
    """Reserve position where a year's own published curve equals ``price_kw_yr``.

    Uses only published quantities (net-CONE, cap, curve x-positions). Flat-
    extrapolates past the plateau (cap_x for prices >= cap, zero_x for <= 0).
    """
    y = price_kw_yr / p.net_cone_kw_yr
    anchors = own_curve_anchors(p)  # ascending x, descending price fraction
    if y >= anchors[0][1]:
        return anchors[0][0]
    if y <= anchors[-1][1]:
        return anchors[-1][0]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if y1 <= y <= y0:
            return x0 if y0 == y1 else x0 + (y0 - y) / (y0 - y1) * (x1 - x0)
    return anchors[-1][0]


# --------------------------------------------------------------------------- #
# Auction clearing prices (system/RTO level, annualized)
# --------------------------------------------------------------------------- #
def system_clearing_prices(iso: str) -> dict[str, dict]:
    """System/RTO clearing price per (canonical) delivery year, $/kW-yr.

    For MISO (seasonal) the summer PRA — the binding season — is the annual-
    comparison print; the full seasonal spread is in :func:`miso_seasonal_spread`.
    """
    out: dict[str, dict] = {}
    for r in load_auction_price(iso):
        at, area = r.get("area_type", ""), r.get("area", "")
        price = _f(r, "clearing_price")
        if price is None:
            continue
        if iso == "PJM" and at != "rto":
            continue
        if iso == "NYISO" and area != "NYCA":
            continue
        if iso == "NEISO" and at != "rto":
            continue
        if iso == "MISO" and not (
            at == "rto" or (r.get("season") == "summer" and at == "lrz")
        ):
            continue
        key = canon_year(r["delivery_year"])
        entry = {
            "price_kw_yr": to_kw_yr(price, r["price_unit"]),
            "native": price,
            "unit": r["price_unit"],
            "source": r["source_doc"],
            "cleared_mw": _f(r, "cleared_mw"),
            "season": r.get("season", ""),
        }
        if iso == "MISO":
            if at == "rto":
                out[key] = entry
            else:
                out.setdefault(key, entry)
        else:
            out[key] = entry
    return out


def miso_seasonal_spread() -> dict[str, dict[str, float]]:
    """MISO cleared price by season per delivery year (system/modal LRZ), $/kW-yr."""
    spread: dict[str, dict[str, float]] = {}
    for r in load_auction_price("MISO"):
        price = _f(r, "clearing_price")
        season = r.get("season", "")
        if price is None or not season or season == "annual":
            continue
        spread.setdefault(canon_year(r["delivery_year"]), {}).setdefault(
            season, to_kw_yr(price, r["price_unit"])
        )
    return spread


# --------------------------------------------------------------------------- #
# MISO seasonal RBDC Pass 1 (RC-1C prereq 4a — the seasonal grain)
# --------------------------------------------------------------------------- #
def invert_normalized_curve(
    points: tuple[CapacityDemandCurvePoint, ...], target_frac: float
) -> float:
    """Reserve position where a normalized curve equals ``target_frac``.

    ``points`` ascend in reserve_ratio (price fraction descends). Flat-
    extrapolates past the cap (left) and the zero-cross (right) — the inverse of
    :func:`market_sim.config.constants.evaluate_demand_curve`.
    """
    if target_frac >= points[0].price_frac_net_cone:
        return points[0].reserve_ratio
    if target_frac <= points[-1].price_frac_net_cone:
        return points[-1].reserve_ratio
    for lo, hi in zip(points, points[1:]):
        if hi.price_frac_net_cone <= target_frac <= lo.price_frac_net_cone:
            span = lo.price_frac_net_cone - hi.price_frac_net_cone
            if span <= 0.0:
                return lo.reserve_ratio
            f = (lo.price_frac_net_cone - target_frac) / span
            return lo.reserve_ratio + f * (hi.reserve_ratio - lo.reserve_ratio)
    return points[-1].reserve_ratio


def miso_nc_seasonal_cleared() -> dict[str, dict[str, float]]:
    """MISO PY2025-26 North/Central cleared price ($/MW-day) + cleared MW per
    season, from the demand-curve 'RBDC labeled clearing intersection' points."""
    out: dict[str, dict[str, float]] = {}
    for r in load_demand_curve("MISO"):
        if (
            r["delivery_year"] == "2025-2026"
            and r["metric"] == "curve_point"
            and r["area"] == "North/Central"
            and (r.get("season") or "").strip()
        ):
            out[r["season"]] = {
                "cleared_mw_day": _f(r, "y_value"),
                "cleared_mw": _f(r, "x_value"),
            }
    return out


def miso_seasonal_pass1() -> dict:
    """MISO PY2025-26 seasonal RBDC Pass 1 (fleet-independent, RC-1C prereq 4a).

    Evaluates the SHIPPED seasonal RBDC (:data:`MISO_SEASONAL_RBDC`) per season
    and annualizes revenue as the market's own seasonal SUM
    (Σ ACP_season × days_season), replacing the old annual approximation. Each
    season's cleared $/MW-day is placed on that season's own model curve to
    recover its implied reserve position — reproducing the observed
    summer-short / other-seasons-long CONCENTRATION directionally. The annual sum
    of the seasonal contributions is the scoreable number, compared to the
    published North/Central net-CONE. ≥2026 delivery rows are locked (rule 22);
    PY2025-26 is scored (in-train).
    """
    cleared = miso_nc_seasonal_cleared()
    daily_net = MISO_SEASONAL_RBDC.daily_net_cone_per_mw_day
    net_cone_mw_yr = daily_net * 365.0  # published N/C net-CONE (79,800)
    seasons = []
    annual_contrib = 0.0
    for s in MISO_SEASONAL_RBDC.seasons:
        c = cleared.get(s.name, {})
        acp = c.get("cleared_mw_day")
        cap_frac = s.demand_curve[0].price_frac_net_cone
        gross_cap_day = cap_frac * daily_net
        implied_pos = model_price_day = contrib = None
        if acp is not None:
            implied_pos = invert_normalized_curve(s.demand_curve, acp / daily_net)
            model_price_day = (
                evaluate_demand_curve(s.demand_curve, implied_pos) * daily_net
            )
            contrib = acp * s.days  # $/MW-yr contribution (market settlement)
            annual_contrib += contrib
        seasons.append(
            {
                "season": s.name,
                "days": s.days,
                "cleared_mw_day": acp,
                "annualized_if_all_year_kw_yr": (
                    acp * 365.0 / 1000.0 if acp is not None else None
                ),
                "gross_cone_cap_mw_day": gross_cap_day,
                "model_cap_frac": cap_frac,
                "implied_reserve_position": implied_pos,
                "model_price_mw_day": model_price_day,
                "contribution_mw_yr": contrib,
            }
        )
    return {
        "delivery_year": "2025/2026",
        "locked": False,  # in-train delivery year (2025 < 2026)
        "daily_net_cone_mw_day": daily_net,
        "seasons": seasons,
        "annual_capacity_revenue_mw_yr": annual_contrib,
        "published_net_cone_mw_yr": net_cone_mw_yr,
        "pct_error": (
            100.0 * (annual_contrib - net_cone_mw_yr) / net_cone_mw_yr
            if net_cone_mw_yr
            else None
        ),
    }


# --------------------------------------------------------------------------- #
# Pass 1
# --------------------------------------------------------------------------- #
@dataclass
class Pass1Row:
    iso: str
    delivery_year: str
    locked: bool
    cleared_kw_yr: float | None
    cleared_native: float | None
    native_unit: str | None
    pub_net_cone_kw_yr: float | None
    pub_net_cone_ucap_kw_yr: float | None
    model_net_cone_kw_yr: float
    # 1A shape: model curve fraction at cap-x vs published cap/net-CONE fraction
    pub_cap_frac: float | None
    model_cap_frac: float | None
    shape_resid_pct: float | None
    # 1B price: model dollar price at the published cleared position
    reserve_position: float | None
    model_price_kw_yr: float | None
    residual_kw_yr: float | None
    pct_error: float | None
    cap_frac_source: str
    note: str = ""


def run_pass1(iso: str) -> list[Pass1Row]:
    params = YEAR_PARAM_BUILDERS[iso](load_demand_curve(iso))
    prices = system_clearing_prices(iso)
    rows: list[Pass1Row] = []
    for y in sorted(set(params) | set(prices), key=delivery_start_year):
        p = params.get(y)
        pr = prices.get(y)
        src = pr["source"] if pr else ""
        # RC-1C: NYISO scores each delivery year on its OWN vintage (anchor +
        # curve), removing the frozen single-vintage anchor. PJM/NEISO/MISO keep
        # the registry reference (year=None) so their Pass-1 numbers are stable.
        yr = delivery_start_year(y) if iso == "NYISO" else None
        m_nc = model_net_cone_kw_yr(iso, yr)
        if p is None:  # clearing price but no published curve params that year
            rows.append(
                Pass1Row(
                    iso,
                    y,
                    is_locked(iso, y, src),
                    pr["price_kw_yr"] if pr else None,
                    pr["native"] if pr else None,
                    pr["unit"] if pr else None,
                    None,
                    None,
                    m_nc,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "n/a",
                    "no published curve params this year (position not "
                    "reconstructable from published data)",
                )
            )
            continue
        # 1A shape reproduction (fraction of net-CONE at the cap x-position)
        pub_cap_frac = None
        shape_resid = None
        model_at_cap = None
        if p.cap_frac_source == "published" and p.price_cap_kw_yr:
            pub_cap_frac = p.price_cap_kw_yr / p.net_cone_kw_yr
            model_at_cap = model_curve_frac(iso, p.cap_x, yr)
            shape_resid = 100.0 * (model_at_cap - pub_cap_frac) / pub_cap_frac
        # 1B price reproduction at the published cleared position
        pos = mp = resid = pct = None
        note = ""
        if pr is not None:
            pos = invert_own_curve(p, pr["price_kw_yr"])
            mp = model_curve_price_kw_yr(iso, pos, yr)
            resid = mp - pr["price_kw_yr"]
            pct = 100.0 * resid / pr["price_kw_yr"] if pr["price_kw_yr"] else None
            if p.cap_frac_source != "published":
                note = f"cap fraction {p.cap_frac_source}"
        rows.append(
            Pass1Row(
                iso,
                y,
                is_locked(iso, y, src),
                pr["price_kw_yr"] if pr else None,
                pr["native"] if pr else None,
                pr["unit"] if pr else None,
                p.net_cone_kw_yr,
                p.net_cone_ucap_kw_yr,
                m_nc,
                pub_cap_frac,
                model_at_cap if pub_cap_frac is not None else None,
                shape_resid,
                pos,
                mp,
                resid,
                pct,
                p.cap_frac_source,
                note,
            )
        )
    return rows


# --------------------------------------------------------------------------- #
# Pass 2
# --------------------------------------------------------------------------- #
@dataclass
class Pass2Row:
    iso: str
    calendar_year: int
    delivery_year: str
    locked: bool
    peak_demand_mw: float
    firm_mw: float
    requirement_mw: float
    reserve_position: float
    model_price_kw_yr: float
    cleared_kw_yr: float | None
    cleared_native: float | None
    native_unit: str | None
    residual_kw_yr: float | None
    pct_error: float | None


def _restate_firm_on_adopted_basis(iso: str, led: dict, firm_old: float) -> float:
    """Restate a frozen ledger's accredited firm MW on the adopted basis.

    P-2B Option A re-validation (no LP): the persisted ``reserve_margin`` was
    solved on the OLD thermal accreditation basis (UCAP, ``1 - EFORd``). To
    read the migration's effect without re-solving, restate ONLY the thermal
    block on the adopted basis (:func:`thermal_accreditation_fraction` — PJM's
    published ELCC class ratings, R3), keeping the non-thermal (VRE pools +
    storage ELCC + firm ties) residual exactly as the ledger froze it (VRE
    re-basing is P-2C, out of scope here). This is the memo's §3.1
    decomposition automated through the SHIPPED resolver — a re-statement of a
    fixed fleet's accreditation, never a re-tune (rules 1/13). When the ledger
    carries no per-fuel breakdown, the frozen firm is returned unchanged.
    """
    fleet_by_fuel = led.get("fleet_by_fuel_after") or {}
    if not fleet_by_fuel:
        return firm_old
    thermal_ucap_old = sum(
        mw * (1.0 - EFORD[f]) for f, mw in fleet_by_fuel.items() if f in EFORD
    )
    thermal_new = sum(
        mw * thermal_accreditation_fraction(f, EFORD[f], iso)
        for f, mw in fleet_by_fuel.items()
        if f in EFORD
    )
    non_thermal_firm = firm_old - thermal_ucap_old
    return thermal_new + non_thermal_firm


def run_pass2(
    iso: str, run: str | None = None, adopted_basis_ledger: bool = False
) -> list[Pass2Row]:
    """Pass 2 rows for ``iso``'s hindcast fleet.

    ``run`` overrides the committed default in :data:`HINDCAST_RUNS` — a bare
    name resolves under ``results/hindcast/``; a value containing a path
    separator is used as a path directly (the RC-1A probe-leg restatements).

    ``adopted_basis_ledger``: the committed pre-N-5 bundles froze their
    ``reserve_margin`` on the legacy (1−EFORd)-UCAP supply basis, so Pass 2
    devintages them through :func:`_restate_firm_on_adopted_basis`. A bundle
    produced at HEAD (post-N-5 runner) already writes
    ``accredited_firm_capacity_mw`` — the adopted ELCC/FPR basis — into
    ``reserve_margin``, so restating it double-derates the thermal block
    (~25 GW low on PJM). Pass ``True`` for HEAD-produced bundles (the RC-1A
    legs): firm is read back as ``peak × (1 + reserve_margin)``, the
    base-year placeholder row (``reserve_margin ≈ −1``) is skipped, and the
    model price is taken from the REAL pricing seam
    (:meth:`MarketDesign.capacity_price_per_firm_mw_yr` with ``iso``/``year``
    threaded) so gate, eligibility, vintage, and the MISO seasonal RBDC grain
    price exactly as the runner's screens do.
    """
    run = run or HINDCAST_RUNS.get(iso)
    if not run:
        return []
    run_root = Path(run) if "/" in str(run) else HINDCAST_ROOT / run
    ledgers = sorted(run_root.glob(f"{iso}/*/evolution_*.json"))
    prices = system_clearing_prices(iso)
    cfg = ScenarioConfig(iso=iso)
    gate_on = SimpleNamespace(capacity_market_clearing=True)
    out: list[Pass2Row] = []
    for lp in ledgers:
        led = json.loads(lp.read_text())
        if led.get("bridge") or led.get("reserve_margin") is None:
            continue
        cal = int(led["year"])
        peak = float(led["peak_demand_mw"])
        rm = float(led["reserve_margin"])
        if adopted_basis_ledger:
            if rm <= -0.9:  # base-year placeholder (no prior pools)
                continue
            firm = peak * (1.0 + rm)
        else:
            # Firm: restate the frozen (pre-N-5) ledger's thermal block on the
            # adopted ELCC class-rating basis (R3); requirement: devintage
            # onto the published FPR of the matching delivery year (R2, via
            # the threaded calendar year). Both pick up the migration without
            # an LP re-solve.
            firm = _restate_firm_on_adopted_basis(iso, led, peak * (1.0 + rm))
        req = resolve_adequacy_requirement_mw(cfg, iso, peak, cal)
        pos = firm / req if req > 0 else float("nan")
        if adopted_basis_ledger:
            # Price through the real seam (gate + eligibility + vintage +
            # seasonal RBDC), $/firm-MW-yr → $/kW-yr.
            mp = (
                MARKET_DESIGN[iso].capacity_price_per_firm_mw_yr(
                    gate_on, pos, iso=iso, year=cal
                )
                / 1000.0
            )
        else:
            mp = model_curve_price_kw_yr(iso, pos)
        dy = canon_year(f"{cal}/{cal + 1}")
        pr = prices.get(dy)
        resid = (mp - pr["price_kw_yr"]) if pr else None
        pct = 100.0 * resid / pr["price_kw_yr"] if pr and pr["price_kw_yr"] else None
        out.append(
            Pass2Row(
                iso,
                cal,
                dy,
                is_locked(iso, dy, pr["source"] if pr else ""),
                round(peak, 1),
                round(firm, 1),
                round(req, 1),
                round(pos, 4),
                round(mp, 3),
                round(pr["price_kw_yr"], 3) if pr else None,
                pr["native"] if pr else None,
                pr["unit"] if pr else None,
                round(resid, 3) if resid is not None else None,
                round(pct, 1) if pct is not None else None,
            )
        )
    return sorted(out, key=lambda r: r.calendar_year)


# --------------------------------------------------------------------------- #
# PJM cleared-quantity regime series (illustrative corroboration of the spike)
# --------------------------------------------------------------------------- #
def pjm_regime_series() -> dict:
    """Map PJM's published cleared-UCAP series to reserve positions and the model
    curve, to show the 2024/25 -> 2025/26 spike DIRECTION reproduces.

    Requirement anchored ONCE off the shortage auction that cleared exactly at the
    cap (2026/27 cleared at the cap plateau, so R = cleared / cap_x). Illustrative
    only (the true requirement drifts with the IRM year to year); reported as
    direction/order-of-magnitude corroboration, never a scored metric.
    """
    prices = system_clearing_prices("PJM")
    params = pjm_year_params(load_demand_curve("PJM"))
    anchor = "2026/2027"
    cap_x = params[anchor].cap_x
    R = prices[anchor]["cleared_mw"] / cap_x
    series = []
    for y in sorted(prices, key=delivery_start_year):
        cm = prices[y].get("cleared_mw")
        if cm is None:
            continue
        pos = cm / R
        series.append(
            {
                "delivery_year": y,
                "locked": is_locked("PJM", y, prices[y]["source"]),
                "cleared_mw": cm,
                "reserve_position": round(pos, 4),
                "model_price_mw_day": round(
                    kw_yr_to_mw_day(model_curve_price_kw_yr("PJM", pos)), 2
                ),
                "cleared_mw_day": prices[y]["native"],
            }
        )
    return {
        "requirement_anchor_mw": round(R, 1),
        "anchor_year": anchor,
        "series": series,
    }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #
def _g(locked: bool, s: str) -> str:
    return f"_{s}_" if locked else s


def _fmt(v, spec="{:.1f}", dash="—"):
    return (
        dash
        if v is None or (isinstance(v, float) and math.isnan(v))
        else spec.format(v)
    )


def render_pass1(iso: str, rows: list[Pass1Row]) -> str:
    out = [
        f"#### {iso} — Pass 1B: curve price vs cleared price "
        f"(at published, fleet-independent reserve position)",
        "",
        "| Delivery yr | Cleared $/kW-yr | Pub net-CONE | Model net-CONE "
        "| Reserve pos | Model curve | Resid | %err | Note |",
        "|---|--:|--:|--:|--:|--:|--:|--:|---|",
    ]
    for r in rows:
        lk = r.locked
        tag = " ⛔locked" if lk else ""
        note = (r.note + tag).strip()
        cells = [
            r.delivery_year,
            _fmt(r.cleared_kw_yr),
            _fmt(r.pub_net_cone_kw_yr),
            _fmt(r.model_net_cone_kw_yr),
            _fmt(r.reserve_position, "{:.3f}"),
            _fmt(r.model_price_kw_yr),
            _fmt(r.residual_kw_yr, "{:+.1f}"),
            _fmt(r.pct_error, "{:+.0f}%"),
            note or "—",
        ]
        out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    # 1A shape table
    shape_rows = [r for r in rows if r.pub_cap_frac is not None]
    if shape_rows:
        out += [
            "",
            f"#### {iso} — Pass 1A: normalized curve SHAPE reproduction "
            "(price ÷ net-CONE at the published cap position)",
            "",
            "| Delivery yr | Published cap frac | Model cap frac | Shape resid |",
            "|---|--:|--:|--:|",
        ]
        for r in shape_rows:
            lk = r.locked
            cells = [
                r.delivery_year,
                _fmt(r.pub_cap_frac, "{:.3f}"),
                _fmt(r.model_cap_frac, "{:.3f}"),
                _fmt(r.shape_resid_pct, "{:+.1f}%"),
            ]
            out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    return "\n".join(out)


def render_pass2(iso: str, rows: list[Pass2Row]) -> str:
    if not rows:
        return f"#### {iso} — Pass 2: no capacity hindcast available.\n"
    out = [
        f"#### {iso} — Pass 2: curve at the model's own hindcast accredited position",
        "",
        "| Cal yr | Delivery yr | Peak MW | Firm MW | Req MW | Reserve pos "
        "| Model curve | Cleared | Resid | %err |",
        "|---|---|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for r in rows:
        lk = r.locked
        cells = [
            str(r.calendar_year),
            r.delivery_year,
            f"{r.peak_demand_mw:.0f}",
            f"{r.firm_mw:.0f}",
            f"{r.requirement_mw:.0f}",
            f"{r.reserve_position:.3f}",
            _fmt(r.model_price_kw_yr),
            _fmt(r.cleared_kw_yr),
            _fmt(r.residual_kw_yr, "{:+.1f}"),
            _fmt(r.pct_error, "{:+.0f}%"),
        ]
        out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    return "\n".join(out)


_NYISO_INELIGIBLE_NOTE = (
    "> **NYISO is curve-INELIGIBLE for the flip** (R5a ICAP→UCAP translation-"
    "factor pairing adjudicated, owner sign-off PENDING — "
    "nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md §3, Option D "
    "stands). Pass 1 below validates the INSTRUMENT per vintage (a diagnostic, "
    "unaffected by eligibility); the model's screens price NYISO on its FIXED "
    "anchor regardless (`constants.resolve_capacity_curve_eligible` returns "
    "False), so a flip cannot be executed for NYISO until that sign-off lands."
)


def render_miso_seasonal(mp: dict) -> str:
    lk = mp["locked"]
    out = [
        "#### MISO — Pass 1 (SEASONAL RBDC grain, RC-1C prereq 4a)",
        "",
        "MISO clears a seasonal PRA; the market settles capacity as a seasonal "
        "SUM (Σ ACP_season[$/MW-day] × days_season). The model's SHIPPED seasonal "
        "RBDC is evaluated per season and each season's North/Central cleared "
        "price is placed on that season's own curve to recover its implied "
        f"reserve position. daily net-CONE = {mp['daily_net_cone_mw_day']:.2f} "
        "$/MW-day (79,800 $/MW-yr ÷ 365, the flat requirement-point price).",
        "",
        "| Season | Days | Cleared $/MW-day | if-all-yr $/kW-yr | Gross-CONE cap "
        "$/MW-day | Model cap frac | Implied reserve pos | Contribution $/MW-yr |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for s in mp["seasons"]:
        cells = [
            s["season"],
            str(s["days"]),
            _fmt(s["cleared_mw_day"], "{:.2f}"),
            _fmt(s["annualized_if_all_year_kw_yr"]),
            _fmt(s["gross_cone_cap_mw_day"], "{:.1f}"),
            _fmt(s["model_cap_frac"], "{:.3f}"),
            _fmt(s["implied_reserve_position"], "{:.3f}"),
            _fmt(s["contribution_mw_yr"], "{:.0f}"),
        ]
        out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    out += [
        "",
        f"**Annualized (seasonal SUM) = {mp['annual_capacity_revenue_mw_yr']:.0f} "
        f"$/MW-yr vs published North/Central net-CONE "
        f"{mp['published_net_cone_mw_yr']:.0f} $/MW-yr "
        f"({mp['pct_error']:+.1f}%).** Summer's implied reserve position is SHORT "
        "(≤ 1.0, near the cap) while fall/winter/spring sit LONG (> 1.0, near the "
        "zero-cross) — the observed summer-at-cap / other-seasons-near-zero "
        "concentration reproduces directionally, and the seasonal sum lands on "
        "net-CONE. The 'if-all-yr' column is what the OLD annual approximation "
        "did — mis-annualizing summer's $/MW-day as if it ran all 365 days "
        "(~3× net-CONE); the seasonal grain replaces that.",
        "",
        "_One-position limit (documented):_ the model holds ONE annual accredited "
        "position and feeds it to all four seasons (no seasonal fleet "
        "accreditation), so its own-fleet (Pass-2-style) price cannot reproduce "
        "this concentration — it OVER-states at a short annual position (all four "
        "seasons priced near their caps) and UNDER-states at a long one. Pre-RBDC "
        "MISO years (PY2021/22-2024/25) are VERTICAL-at-CONE (no sloped shape, "
        "priced as a step) and are not seasonally scoreable. MISO has no capacity "
        "hindcast, so there is no Pass 2 today.",
    ]
    return "\n".join(out)


def render_markdown(
    report: dict,
    pass2_runs: dict[str, str] | None = None,
    pass2_adopted_basis: bool = False,
) -> str:
    pass2_runs = pass2_runs or {}

    def _pass2(iso: str) -> list[Pass2Row]:
        override = pass2_runs.get(iso)
        return run_pass2(
            iso,
            override,
            adopted_basis_ledger=pass2_adopted_basis and override is not None,
        )

    out: list[str] = []
    for iso in CURVE_ISOS:
        if iso == "MISO":
            out.append(render_miso_seasonal(report["miso_seasonal_pass1"]))
            out.append("")
            out.append(render_pass2(iso, _pass2(iso)))
            out.append("")
            continue
        if iso == "NYISO":
            out.append(_NYISO_INELIGIBLE_NOTE)
            out.append("")
        out.append(render_pass1(iso, run_pass1(iso)))
        out.append("")
        out.append(render_pass2(iso, _pass2(iso)))
        out.append("")
    reg = report["pjm_regime"]
    out += [
        "#### PJM cleared-quantity regime series (illustrative — spike direction)",
        "",
        f"Requirement anchored at {reg['requirement_anchor_mw']:.0f} MW "
        f"(the {reg['anchor_year']} cap-plateau clearing). Illustrative only.",
        "",
        "| Delivery yr | Cleared MW | Reserve pos | Model $/MW-day | Cleared $/MW-day |",
        "|---|--:|--:|--:|--:|",
    ]
    for s in reg["series"]:
        lk = s["locked"]
        cells = [
            s["delivery_year"],
            f"{s['cleared_mw']:.0f}",
            f"{s['reserve_position']:.3f}",
            f"{s['model_price_mw_day']:.1f}",
            f"{s['cleared_mw_day']:.2f}",
        ]
        out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_report(
    pass2_runs: dict[str, str] | None = None, pass2_adopted_basis: bool = False
) -> dict:
    report: dict = {
        "passes": {},
        # RC-1C curve-eligibility (the governance gate the model screens read):
        # NYISO is False (R5a pairing not owner-signed) — its Pass 1 below is a
        # diagnostic only; the screens price it fixed.
        "curve_eligibility": {
            iso: resolve_capacity_curve_eligible(iso) for iso in CURVE_ISOS
        },
        "pjm_regime": pjm_regime_series(),
        "miso_seasonal_pass1": miso_seasonal_pass1(),
        "miso_seasonal_spread": miso_seasonal_spread(),
        "caiso": {
            "note": "Bilateral RA, no central auction/demand curve. MARKET_DESIGN "
            "keeps a FIXED proxy (90 $/kW-yr) in both modes; not slope-validatable.",
            "fixed_proxy_kw_yr": MARKET_DESIGN["CAISO"].net_cone_per_kw_yr,
        },
    }
    for iso in CURVE_ISOS:
        override = (pass2_runs or {}).get(iso)
        report["passes"][iso] = {
            "pass1": [asdict(r) for r in run_pass1(iso)],
            "pass2": [
                asdict(r)
                for r in run_pass2(
                    iso,
                    override,
                    adopted_basis_ledger=pass2_adopted_basis and override is not None,
                )
            ],
        }
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("results/capacity-price-validation/validation.json"),
    )
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument(
        "--pass2-run",
        action="append",
        default=[],
        metavar="ISO=RUN",
        help=(
            "Override the Pass-2 hindcast run for an ISO (repeatable), e.g. "
            "--pass2-run PJM=results/hindcast/pjm-2021-2025-realized-cmc-probe. "
            "A bare name resolves under results/hindcast/. Restates the named "
            "fleet's ledger on the adopted basis (RC-1A probe legs, plan §3 "
            "T-R4); never a re-tune."
        ),
    )
    ap.add_argument(
        "--pass2-adopted-basis",
        action="store_true",
        help=(
            "Treat every --pass2-run override bundle as HEAD-produced: its "
            "ledger reserve_margin already carries the adopted "
            "(accredited_firm_capacity_mw, post-N-5) basis, so firm is read "
            "back directly instead of re-restating (which double-derates the "
            "thermal block), and the model price is taken from the real "
            "pricing seam (gate + eligibility + vintage + seasonal RBDC). The "
            "committed pre-N-5 defaults are unaffected."
        ),
    )
    args = ap.parse_args(argv)

    pass2_runs: dict[str, str] = {}
    for spec in args.pass2_run:
        iso, _, run = spec.partition("=")
        if not run:
            ap.error(f"--pass2-run expects ISO=RUN, got {spec!r}")
        pass2_runs[iso.upper()] = run

    report = build_report(pass2_runs, pass2_adopted_basis=args.pass2_adopted_basis)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {args.out}")
    if args.markdown:
        print(
            "\n"
            + render_markdown(
                report, pass2_runs, pass2_adopted_basis=args.pass2_adopted_basis
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
