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

from market_sim.config.constants import EFORD, MARKET_DESIGN, evaluate_demand_curve
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
HINDCAST_RUNS = {"PJM": "pjm-2021-2025-realized"}


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


def nyiso_year_params(rows: list[dict]) -> dict[str, YearParams]:
    """NYISO NYCA annual anchors: the Annual Reference Value is net-CONE at the
    requirement (frac 1.0), zero-cross at 100% + the 12% Demand Curve Length —
    exactly the implemented _NYISO_ICAP_CURVE annualization."""
    out: dict[str, YearParams] = {}
    for r in rows:
        if r["area"] == "NYCA" and r["metric"] == "net_cone":
            nc = to_kw_yr(_f(r, "y_value"), r["y_unit"])
            out[canon_year(r["delivery_year"])] = YearParams(
                net_cone_kw_yr=nc,
                net_cone_ucap_kw_yr=nc,
                price_cap_kw_yr=3.792 * nc,  # published max clearing / reference
                ref_x=1.0,
                cap_x=0.665,
                zero_x=1.12,
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


def model_curve_frac(iso: str, reserve_position: float) -> float:
    """Implemented normalized curve's price fraction of net-CONE at a position."""
    return evaluate_demand_curve(MARKET_DESIGN[iso].demand_curve, reserve_position)


def model_curve_price_kw_yr(iso: str, reserve_position: float) -> float:
    """Implemented CR-1 curve price at a reserve position, $/kW-yr (real seam)."""
    return model_curve_frac(iso, reserve_position) * model_net_cone_kw_yr(iso)


def model_net_cone_kw_yr(iso: str) -> float:
    d = MARKET_DESIGN[iso]
    return d.net_cone_curve_per_kw_yr or d.net_cone_per_kw_yr


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
    m_nc = model_net_cone_kw_yr(iso)
    m_cap_frac = _model_cap_frac(iso)
    rows: list[Pass1Row] = []
    for y in sorted(set(params) | set(prices), key=delivery_start_year):
        p = params.get(y)
        pr = prices.get(y)
        src = pr["source"] if pr else ""
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
        if p.cap_frac_source == "published" and p.price_cap_kw_yr:
            pub_cap_frac = p.price_cap_kw_yr / p.net_cone_kw_yr
            model_at_cap = model_curve_frac(iso, p.cap_x)
            shape_resid = 100.0 * (model_at_cap - pub_cap_frac) / pub_cap_frac
        # 1B price reproduction at the published cleared position
        pos = mp = resid = pct = None
        note = ""
        if pr is not None:
            pos = invert_own_curve(p, pr["price_kw_yr"])
            mp = model_curve_price_kw_yr(iso, pos)
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
                m_cap_frac if pub_cap_frac is not None else None,
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


def run_pass2(iso: str) -> list[Pass2Row]:
    run = HINDCAST_RUNS.get(iso)
    if not run:
        return []
    ledgers = sorted((HINDCAST_ROOT / run).glob(f"{iso}/*/evolution_*.json"))
    prices = system_clearing_prices(iso)
    cfg = ScenarioConfig(iso=iso)
    out: list[Pass2Row] = []
    for lp in ledgers:
        led = json.loads(lp.read_text())
        if led.get("bridge") or led.get("reserve_margin") is None:
            continue
        cal = int(led["year"])
        peak = float(led["peak_demand_mw"])
        # Firm: restate the frozen ledger's thermal block on the adopted ELCC
        # class-rating basis (R3); requirement: devintage onto the published
        # FPR of the matching delivery year (R2, via the threaded calendar
        # year). Both pick up the migration without an LP re-solve.
        firm = _restate_firm_on_adopted_basis(
            iso, led, peak * (1.0 + float(led["reserve_margin"]))
        )
        req = resolve_adequacy_requirement_mw(cfg, iso, peak, cal)
        pos = firm / req if req > 0 else float("nan")
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


def render_markdown(report: dict) -> str:
    out: list[str] = []
    for iso in CURVE_ISOS:
        out.append(render_pass1(iso, run_pass1(iso)))
        out.append("")
        out.append(render_pass2(iso, run_pass2(iso)))
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
    out += [
        "",
        "#### MISO seasonal spread (why an annual curve cannot score MISO)",
        "",
        "| Delivery yr | Summer | Fall | Winter | Spring | (all $/kW-yr) |",
        "|---|--:|--:|--:|--:|---|",
    ]
    for y, seas in sorted(report["miso_seasonal_spread"].items(), key=lambda kv: kv[0]):
        lk = delivery_start_year(y) >= 2026
        cells = [
            y,
            _fmt(seas.get("summer")),
            _fmt(seas.get("fall")),
            _fmt(seas.get("winter")),
            _fmt(seas.get("spring")),
            "",
        ]
        out.append("| " + " | ".join(_g(lk, c) for c in cells) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_report() -> dict:
    report: dict = {
        "passes": {},
        "pjm_regime": pjm_regime_series(),
        "miso_seasonal_spread": miso_seasonal_spread(),
        "caiso": {
            "note": "Bilateral RA, no central auction/demand curve. MARKET_DESIGN "
            "keeps a FIXED proxy (90 $/kW-yr) in both modes; not slope-validatable.",
            "fixed_proxy_kw_yr": MARKET_DESIGN["CAISO"].net_cone_per_kw_yr,
        },
    }
    for iso in CURVE_ISOS:
        report["passes"][iso] = {
            "pass1": [asdict(r) for r in run_pass1(iso)],
            "pass2": [asdict(r) for r in run_pass2(iso)],
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
    args = ap.parse_args(argv)

    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {args.out}")
    if args.markdown:
        print("\n" + render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
