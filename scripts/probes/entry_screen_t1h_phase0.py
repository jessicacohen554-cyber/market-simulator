"""ENTRY-SCREEN DIAGNOSTIC Phase-0: the entry/storage screens replayed offline.

The measurement set behind ``docs/FINDING-entry-screen-t1h-2026-08.md``. Read-only
and arithmetic-only: it **never solves**, never imports the LP, and touches nothing
but a run bundle's committed ``screen_signal_diag_<solve>_for_<entering>.npz`` dumps
plus the committed registry constants. Four reads:

* **(A) storage screen replay** — ``model.storage.apply_storage_new_entry``'s value
  stack and merit allocator re-executed per decision year on the committed price
  signal. On the ERCOT T1-H refresh bundle this REPRODUCES the registered ledger
  exactly (iron_air 3,000 MW + flow_battery 2,000 MW, entering-2023 only), which is
  what closes the attribution of that ledger line to the allocator rather than to
  any other mechanism.
* **(B) signal shape** — the base merit-order price's own diurnal spread against the
  spread after the ORDC adder, i.e. how much of what the screens read as
  "arbitrage" is the scarcity overlay rather than the energy price. Reported both as
  a daily top-``d``/bottom-``d`` spread and as the adder's share of a thermal
  candidate's price-duration margin (``new_entry.py``'s ``sum_t max(p - vc, 0)``).
* **(C) VRE capture** — each of wind and solar valued on its own committed potential
  profile against the same signal, expressed as a ratio to the flat signal mean. The
  ratio is nameplate-invariant, so it is well defined without the zonal pools.
* **(D) break-even** — for an ISO whose ``MARKET_DESIGN`` pays capacity, the
  arbitrage each storage tech must earn to clear, and the raw round-trip spread the
  price shape would have to deliver in EVERY arbitrage window to supply it. This is
  what makes a capacity-anchor lever adjudicable without a solve.

The storage cost/value formulas are re-declared here from the registry rather than
imported, so the probe runs in a bare interpreter (numpy only) on a ``code`` data
profile with no pandas/pydantic/highspy present. Every constant carries the
``config/`` file and symbol it mirrors; a divergence between this file and the
registry is a bug in this file. Usage::

    python3 scripts/probes/entry_screen_t1h_phase0.py \
        --bundle results/hindcast/ercot-2021-2025-realized-t1h-refresh \
        --iso ERCOT --scarcity-overlay \
        --out results/calibration/entry_screen_t1h_phase0_ercot.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]

# --- registry mirrors -------------------------------------------------------
# config/scenarios.py: nominal_discount_rate 0.08; config/constants.py:
# INFLATION_RATE 0.022; ScenarioConfig.real_discount_rate is the Fisher ratio.
_REAL_DISCOUNT_RATE = (1.0 + 0.08) / (1.0 + 0.022) - 1.0
# model/storage.py::_STORAGE_ECONOMIC_LIFE_YR — 20 for EVERY tech, which is why
# the per-tech ``lifetime_yr`` below is carried but deliberately unused (D-4).
_STORAGE_ECONOMIC_LIFE_YR = 20
# config/capacity_market.py::STORAGE_DEGRADATION_REPLACEMENT_FRACTION
_DEGRADATION_REPLACEMENT_FRACTION = 0.25
# config/scenarios.py::ScenarioConfig.ira_itc_storage; policy/ira.py's phaseout
# fraction is 1.0 through ira_other_clean_last_full_year (2033), so a 2021-2025
# hindcast books the full rate.
_ITC_STORAGE = 0.30
# config/capacity_market.py::STORAGE_TECH_BUILD_SHARE_CAP
_TECH_BUILD_SHARE_CAP = 0.6
# config/capacity_market.py::STORAGE_ELCC_SATURATION_EXPONENT
_ELCC_SATURATION_EXPONENT = 1.5
# config/capacity_market.py::STORAGE_ELCC_BY_DURATION (generic NREL/E3 curve).
_ELCC_BY_DURATION = [
    (2.0, 0.40),
    (4.0, 0.60),
    (6.0, 0.75),
    (8.0, 0.87),
    (10.0, 0.93),
    (12.0, 0.97),
    (24.0, 1.00),
]
# config/capacity_market.py::STORAGE_TECHS. ``rte_config`` mirrors the
# ScenarioConfig overrides model/storage.py::_storage_rte applies.
_STORAGE_TECHS: dict[str, dict[str, float]] = {
    "li_ion_4hr": dict(
        duration_hr=4, rte=0.86, rte_config=0.85, cycles=5000,
        capex_per_kw=1810.3, capex_per_kwh=452.6, fom_per_kw_yr=40.9,
    ),
    "li_ion_8hr": dict(
        duration_hr=8, rte=0.86, rte_config=0.80, cycles=5000,
        capex_per_kw=3154.3, capex_per_kwh=394.3, fom_per_kw_yr=73.4,
    ),
    "iron_air": dict(
        duration_hr=100, rte=0.50, rte_config=0.50, cycles=3000,
        capex_per_kw=2000.0, capex_per_kwh=20.0, fom_per_kw_yr=20.0,
    ),
    "li_ion_12hr": dict(
        duration_hr=12, rte=0.78, rte_config=0.78, cycles=4000,
        capex_per_kw=4498.4, capex_per_kwh=374.9, fom_per_kw_yr=105.8,
    ),
    "flow_battery": dict(
        duration_hr=10, rte=0.70, rte_config=0.70, cycles=15000,
        capex_per_kw=4700.0, capex_per_kwh=350.0, fom_per_kw_yr=15.0,
    ),
    "compressed_air": dict(
        duration_hr=8, rte=0.55, rte_config=0.55, cycles=10000,
        capex_per_kw=2700.0, capex_per_kwh=150.0, fom_per_kw_yr=10.0,
    ),
}
# config/capacity_market.py::STORAGE_ANNUAL_BUILD_CAP_MW / _DEPLOYMENT_CEILING_MW
_ANNUAL_BUILD_CAP_MW = {
    "ERCOT": 5_000.0, "CAISO": 3_000.0, "PJM": 4_000.0,
    "NYISO": 1_500.0, "NEISO": 1_200.0, "MISO": 4_000.0,
}
_DEPLOYMENT_CEILING_MW = {
    "ERCOT": 45_000.0, "CAISO": 25_000.0, "PJM": 75_000.0,
    "NYISO": 16_000.0, "NEISO": 13_000.0, "MISO": 62_000.0,
}
# config/capacity_market.py::MARKET_DESIGN[iso].net_cone_per_kw_yr, $/kW-yr; 0.0
# where capacity_market is False (ERCOT is energy-only and pays no capacity).
_NET_CONE_PER_KW_YR = {
    "ERCOT": 0.0, "CAISO": 88.08, "PJM": 77.431, "NYISO": 110.0,
}


def capital_recovery_factor(rate: float, lifetime_yr: float) -> float:
    """Return the capital recovery factor (``model/storage.py`` mirror)."""
    if rate <= 0.0:
        return 1.0 / lifetime_yr
    growth = (1.0 + rate) ** lifetime_yr
    return rate * growth / (growth - 1.0)


def storage_annual_cost_per_mw_yr(tech_name: str) -> float:
    """Annualized storage cost in $/MW-yr at the entry seed (no Wright discount).

    Mirrors ``model.storage.compute_storage_annual_cost`` with
    ``cumulative_gw=None`` — the state the first screened year is in, and the
    state that makes this replay comparable across bundles.
    """
    tech = _STORAGE_TECHS[tech_name]
    capex_per_kw = tech["capex_per_kw"] * (1.0 - _ITC_STORAGE)
    crf = capital_recovery_factor(_REAL_DISCOUNT_RATE, _STORAGE_ECONOMIC_LIFE_YR)
    return (capex_per_kw * crf + tech["fom_per_kw_yr"]) * 1000.0


def degradation_cost_per_mwh(tech_name: str) -> float:
    """Cycling-degradation charge per MWh discharged (``storage.py`` mirror)."""
    tech = _STORAGE_TECHS[tech_name]
    if tech["cycles"] <= 0.0:
        return 0.0
    return (
        tech["capex_per_kwh"] * 1000.0 / tech["cycles"]
        * _DEGRADATION_REPLACEMENT_FRACTION
    )


def arbitrage_block_days(duration_hr: float) -> int:
    """Window length in days (``model.storage._arbitrage_block_days`` mirror)."""
    return max(1, math.ceil(duration_hr / 12.0))


def estimate_storage_revenue(
    prices: np.ndarray,
    duration_hr: int,
    rte: float,
    degradation_cost_per_mwh_: float = 0.0,
) -> float:
    """Annual arbitrage revenue per MW (``model.storage`` mirror, vectorized)."""
    price_arr = np.asarray(prices, dtype=float)
    if price_arr.ndim == 1:
        price_arr = price_arr[None, :]
    n_zones, total_hours = price_arr.shape
    d = int(duration_hr)
    if d <= 0:
        return 0.0
    block_hours = arbitrage_block_days(d) * 24
    n_blocks = total_hours // block_hours
    if n_blocks == 0:
        return 0.0
    block = price_arr[:, : n_blocks * block_hours].reshape(
        n_zones, n_blocks, block_hours
    )
    ordered = np.sort(block, axis=2)
    charge_avg = ordered[:, :, :d].mean(axis=2)
    discharge_avg = ordered[:, :, -d:].mean(axis=2)
    best_zone = np.argmax(discharge_avg - charge_avg, axis=0)
    idx = np.arange(n_blocks)
    margin = (
        discharge_avg[best_zone, idx]
        - charge_avg[best_zone, idx] / rte
        - degradation_cost_per_mwh_
    )
    return float(np.maximum(margin, 0.0).sum() * d)


def capacity_value_per_mw_yr(
    tech_name: str, iso: str, existing_mw: float, anchor_per_kw_yr: float | None = None
) -> float:
    """RA capacity value for the marginal build (``estimate_capacity_value`` mirror).

    ``anchor_per_kw_yr`` overrides the shipped ``MARKET_DESIGN`` anchor so a gated
    capacity-price arm (e.g. CAISO's MPB anchor) can be evaluated arithmetically.
    """
    anchor = (
        _NET_CONE_PER_KW_YR.get(iso, 0.0) if anchor_per_kw_yr is None
        else anchor_per_kw_yr
    )
    base_price = anchor * 1000.0
    if base_price <= 0.0:
        return 0.0
    duration_hr = _STORAGE_TECHS[tech_name]["duration_hr"]
    elcc = float(
        np.interp(
            duration_hr,
            [d for d, _ in _ELCC_BY_DURATION],
            [c for _, c in _ELCC_BY_DURATION],
        )
    )
    ceiling = _DEPLOYMENT_CEILING_MW.get(iso, 0.0)
    penetration = 0.0 if ceiling <= 0.0 else min(1.0, existing_mw / ceiling)
    derate = (1.0 - penetration) ** _ELCC_SATURATION_EXPONENT
    return base_price * elcc * derate


def allocate(ranked: list[tuple[float, str]], budget_mw: float) -> list[dict]:
    """Run the storage merit allocator (``storage.py``'s loop, verbatim shape).

    Profitable techs in descending absolute $/MW-yr margin; each takes
    ``budget × STORAGE_TECH_BUILD_SHARE_CAP`` or whatever remains. The volume is
    independent of the margin's SIZE — that property is the point of this replay.
    """
    per_tech_cap = budget_mw * _TECH_BUILD_SHARE_CAP
    remaining = budget_mw
    built: list[dict] = []
    for margin, tech_name in ranked:
        if margin <= 0.0 or remaining <= 0.0:
            break
        build_mw = min(remaining, per_tech_cap)
        remaining -= build_mw
        built.append({"tech": tech_name, "build_mw": round(build_mw, 3)})
    return built


def _signal(dump: dict, with_adder: bool) -> np.ndarray:
    """Return the entry-screen price series from one committed dump."""
    base = np.asarray(dump["price_base_usd_mwh"], dtype=float)
    if not with_adder:
        return base
    return base + np.asarray(dump["adder_usd_mwh"], dtype=float)


def read_storage_screen(
    dump: dict, iso: str, existing_mw: float, anchor_per_kw_yr: float | None
) -> dict:
    """(A) Replay the storage value stack + allocator for one decision year."""
    prices = _signal(dump, with_adder=True)
    rows = []
    for tech_name, tech in _STORAGE_TECHS.items():
        arb = estimate_storage_revenue(
            prices,
            int(tech["duration_hr"]),
            tech["rte_config"],
            degradation_cost_per_mwh(tech_name),
        )
        cap = capacity_value_per_mw_yr(tech_name, iso, existing_mw, anchor_per_kw_yr)
        cost = storage_annual_cost_per_mw_yr(tech_name)
        rows.append(
            {
                "tech": tech_name,
                "arbitrage_per_mw_yr": round(arb, 1),
                "capacity_value_per_mw_yr": round(cap, 1),
                # as_revenue is 0 in both T1-H runs (as_revenue_enabled False, and
                # AS_REVENUE_PER_KW_YR_BY_ISO populates ERCOT only) -- recorded as
                # an explicit zero so it is measured rather than inferred.
                "as_revenue_per_mw_yr": 0.0,
                "annual_cost_per_mw_yr": round(cost, 1),
                "margin_per_mw_yr": round(arb + cap - cost, 1),
            }
        )
    ranked = sorted(((r["margin_per_mw_yr"], r["tech"]) for r in rows), reverse=True)
    budget = min(
        _ANNUAL_BUILD_CAP_MW[iso], max(0.0, _DEPLOYMENT_CEILING_MW[iso] - existing_mw)
    )
    return {
        "budget_mw": budget,
        "per_tech_cap_mw": budget * _TECH_BUILD_SHARE_CAP,
        "ranked": [t for _, t in ranked],
        "techs": rows,
        "allocator_result": allocate(ranked, budget),
    }


def read_signal_shape(dump: dict, spread_hours: int = 4) -> dict:
    """(B) How much of the signal's dispersion is the ORDC adder, not the price."""
    base = _signal(dump, with_adder=False)
    full = _signal(dump, with_adder=True)

    def daily_spread(series: np.ndarray) -> float:
        days = series[: 365 * 24].reshape(365, 24)
        ordered = np.sort(days, axis=1)
        top = ordered[:, -spread_hours:].mean(axis=1)
        bottom = ordered[:, :spread_hours].mean(axis=1)
        return float((top - bottom).mean())

    base_spread, full_spread = daily_spread(base), daily_spread(full)
    out = {
        "base_min": round(float(base.min()), 2),
        "base_p50": round(float(np.percentile(base, 50)), 2),
        "base_p95": round(float(np.percentile(base, 95)), 2),
        "base_max": round(float(base.max()), 2),
        "adder_mean": round(float((full - base).mean()), 3),
        "adder_max": round(float((full - base).max()), 2),
        "daily_spread_base_only": round(base_spread, 2),
        "daily_spread_with_adder": round(full_spread, 2),
        "adder_share_of_spread": (
            round(1.0 - base_spread / full_spread, 4) if full_spread > 0 else None
        ),
        "thermal_margin_adder_share": {},
    }
    # The price-duration margin new_entry.py:1104-1108 computes, swept over a
    # plausible gas-CC variable cost since the dump carries no fuel price.
    for var_cost in (20.0, 25.0, 30.0, 40.0, 60.0):
        full_margin = float(np.maximum(full - var_cost, 0.0).sum())
        base_margin = float(np.maximum(base - var_cost, 0.0).sum())
        out["thermal_margin_adder_share"][f"vc_{int(var_cost)}"] = {
            "energy_margin_per_mw_yr": round(full_margin, 1),
            "base_only_per_mw_yr": round(base_margin, 1),
            "adder_share": (
                round(1.0 - base_margin / full_margin, 4) if full_margin > 0 else None
            ),
        }
    return out


def read_vre_capture(dump: dict) -> dict:
    """(C) Wind/solar capture price on the same signal, as a ratio to the mean.

    Nameplate-invariant: the potential profile's own scale cancels in
    ``sum(p·pot)/sum(pot)``, so the ratio is well defined without the zonal pools.
    """
    prices = _signal(dump, with_adder=True)
    flat_mean = float(prices.mean())
    out: dict = {"flat_signal_mean": round(flat_mean, 2)}
    for tech, key in (("wind", "wind_potential_mw"), ("solar", "solar_potential_mw")):
        if key not in dump:
            continue
        pot = np.asarray(dump[key], dtype=float)
        if pot.sum() <= 0.0:
            continue
        capture = float((prices * pot).sum() / pot.sum())
        out[tech] = {
            "capture_price": round(capture, 2),
            "capture_ratio_vs_flat_mean": (
                round(capture / flat_mean, 4) if flat_mean > 0 else None
            ),
            "profile_mean_over_max": round(float(pot.mean() / pot.max()), 4),
        }
    return out


def read_break_even(
    iso: str, existing_mw: float, anchor_per_kw_yr: float | None
) -> dict:
    """(D) Required arbitrage, and the per-window spread that would supply it."""
    rows = []
    for tech_name, tech in _STORAGE_TECHS.items():
        cap = capacity_value_per_mw_yr(tech_name, iso, existing_mw, anchor_per_kw_yr)
        cost = storage_annual_cost_per_mw_yr(tech_name)
        required = max(0.0, cost - cap)
        duration = int(tech["duration_hr"])
        n_windows = 8760 // (arbitrage_block_days(duration) * 24)
        mwh_per_year = n_windows * duration
        net_per_mwh = required / mwh_per_year if mwh_per_year else float("nan")
        rows.append(
            {
                "tech": tech_name,
                "capacity_value_per_mw_yr": round(cap, 1),
                "annual_cost_per_mw_yr": round(cost, 1),
                "required_arbitrage_per_mw_yr": round(required, 1),
                "n_arbitrage_windows": n_windows,
                # Net of the degradation charge the arbitrage estimator already
                # subtracts, then gross of it -- the raw (discharge - charge/rte)
                # spread the price shape must actually deliver.
                "required_net_margin_per_mwh": round(net_per_mwh, 2),
                "required_gross_spread_per_mwh": round(
                    net_per_mwh + degradation_cost_per_mwh(tech_name), 2
                ),
            }
        )
    return {"anchor_per_kw_yr": anchor_per_kw_yr or _NET_CONE_PER_KW_YR.get(iso, 0.0),
            "rows": rows}


def resolve_cache_dir(bundle: Path, iso: str) -> Path:
    """Return the bundle's per-ISO cache directory holding the committed dumps."""
    iso_dir = bundle / iso.upper()
    if not iso_dir.is_dir():
        raise SystemExit(f"no {iso.upper()}/ directory under {bundle}")
    keys = [p for p in sorted(iso_dir.iterdir()) if p.is_dir()]
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {iso_dir}, got {keys}")
    return keys[0]


def main() -> None:
    """CLI entry point: emit every read above as one JSON artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="capacity-hindcast out-dir")
    ap.add_argument("--iso", required=True)
    ap.add_argument(
        "--existing-storage-mw",
        type=float,
        default=0.0,
        help="storage fleet the marginal build is screened against (saturation "
        "derate and budget); 0.0 is the conservative seed-year reading",
    )
    ap.add_argument(
        "--capacity-anchor-per-kw-yr",
        type=float,
        default=None,
        help="override MARKET_DESIGN's net-CONE anchor, to evaluate a gated "
        "capacity-price arm arithmetically (e.g. CAISO MPB 138.36)",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    iso = args.iso.upper()
    cache_dir = resolve_cache_dir(Path(args.bundle), iso)
    dumps = sorted(cache_dir.glob("screen_signal_diag_*_for_*.npz"))

    result: dict = {
        "probe": "entry_screen_t1h_phase0",
        "finding": "docs/FINDING-entry-screen-t1h-2026-08.md",
        "iso": iso,
        "bundle": str(Path(args.bundle)),
        "cache_dir": str(cache_dir),
        "real_discount_rate": round(_REAL_DISCOUNT_RATE, 6),
        "existing_storage_mw": args.existing_storage_mw,
        # (D) needs no dump at all -- it is exact from the registry, which is what
        # makes a capacity-anchor lever adjudicable on a bundle with no dumps.
        "break_even": read_break_even(
            iso, args.existing_storage_mw, args.capacity_anchor_per_kw_yr
        ),
        "decision_years": {},
    }
    if not dumps:
        result["warning"] = (
            "no screen_signal_diag_*.npz in this bundle -- the dump is gated on "
            "capacity_screen_unified_lookahead (runner.py:3382), so a run with "
            "that flag off cannot be diagnosed offline. Only break_even is "
            "populated. See the FINDING, defect D-7."
        )
    for path in dumps:
        with np.load(path, allow_pickle=True) as z:
            dump = {k: z[k] for k in z.files}
        entering = int(dump["entering_year"])
        result["decision_years"][str(entering)] = {
            "dump": path.name,
            "storage_screen": read_storage_screen(
                dump, iso, args.existing_storage_mw, args.capacity_anchor_per_kw_yr
            ),
            "signal_shape": read_signal_shape(dump),
            "vre_capture": read_vre_capture(dump),
        }

    out_path = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
