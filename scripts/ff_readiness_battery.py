#!/usr/bin/env python
"""FF-3E full-solve readiness battery (forecast-development plan §2.1b / §0 Phase A).

Proves the full-horizon forecast path is bug-free BEFORE any full (T2/T3/golden)
solve is authorized — the battery where "wasted 10 hours" plumbing bugs die at
minutes of cost. It NEVER solves beyond T0 scale: parts a/b/d resolve/inspect
inputs and config with **no LP at all**; only the part-c kill-resume drill runs a
solve, and that is a single T0 NEISO 2026-2028 run (~a few minutes) behind an
explicit subcommand.

The five instruments (plan §2.1b, FF-3E prompt items a-e):

* **a. Input-resolution walk** (:func:`walk_inputs`): per ISO at the golden
  posture (§2.1a), resolve EVERY exogenous forward input for EVERY year
  2026-2050 — demand growth, data-center block, fuel paths (gas/coal/oil),
  carbon program, ATB entry costs, IRA/OBBBA windows, RPS/ACP, federal-CES
  premium, capacity-market params, confirmed-retirements horizon, weather-year
  pool. Loader-level execution, fail-loud per missing/stale/unresolvable item.
* **b. Config completeness** (:func:`config_completeness`): the golden-posture
  ``ScenarioConfig`` round-trips through ``run_config`` / ``config.yaml`` with a
  stable ``cache_key`` (rule 24), and every §2.1a decision is reflected.
* **c. Kill-resume drill** (:func:`kill_resume_drill`): a T0 NEISO 2026-2028 run
  killed after a year and resumed from the per-year cache produces a
  result-equivalent bundle (dispatch/ledger values identical) vs an
  uninterrupted control. THE ONLY SOLVE in this battery.
* **d. Wall/RSS projection** (:func:`project_full_horizon`): from the measured
  §2.4 anchors + the FF-2D per-ISO T1-F ledger, publish the per-ISO projected
  full-horizon (2026-2050) wall-clock/RSS table with a concurrency plan — the
  "what would 10 hours buy" table §2.1b(c) requires.
* **e. Schedulability guard**: lives in ``run_full_horizon.py`` (refuses > 5
  solve-years unless ``--full-solve-authorized``); this module owns the
  authoritative §2.1a golden-posture constant it reads and the guard's test.

Findings only — no model code, threshold, offer curve, or default is changed by
this battery (rules 1/11/14). It writes committed JSON to the forecast-validation
namespace; the gate-open decision is the owner's (plan §2.1b(d)).

Usage::

    # No-LP instruments (safe anywhere; used by CI-style checks):
    python scripts/ff_readiness_battery.py all --out results/ff-readiness
    python scripts/ff_readiness_battery.py resolve --iso ERCOT
    python scripts/ff_readiness_battery.py config
    python scripts/ff_readiness_battery.py projection

    # The one T0 solve (a few minutes; NEISO), explicit:
    python scripts/ff_readiness_battery.py kill-resume --work-dir /tmp/ff3e-drill
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
for _p in (_SRC, _ROOT):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402

from market_sim.config.capacity_market import (  # noqa: E402
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    resolve_capacity_market_clearing,
)
from market_sim.config.constants import (  # noqa: E402
    PLANNING_RESERVE_MARGIN_BY_ISO,
    weather_year_pool,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    ScenarioConfig,
    resolve_demand_growth_rate,
    resolve_new_entry_costs,
    resolve_policy_bundle,
)
from market_sim.data.confirmed_retirements import load_confirmed_exits  # noqa: E402
from market_sim.data.datacenter import datacenter_block_mw_by_zone  # noqa: E402
from market_sim.data.fuel import (  # noqa: E402
    resolve_annual_coal_price,
    resolve_annual_gas_price,
    resolve_annual_oil_price,
)
from market_sim.policy import federal_ces  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.rps import get_rps_acp, get_rps_target  # noqa: E402

# --------------------------------------------------------------------------- #
# Golden posture (§2.1a) — the single authoritative encoding
# --------------------------------------------------------------------------- #
GOLDEN_ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
HORIZON_START, HORIZON_END = 2026, 2050

# §2.1a decision (a): per-ISO capacity-market clearing ON for every ISO with a
# real capacity market — PJM, MISO, NYISO, NEISO, CAISO — and OFF for energy-only
# ERCOT. This is the frozen decision a golden run would carry; whether an ISO's
# *gate* actually opens (§2.1b: flip execution + calibration-complete marker) is
# a separate scorecard question (NYISO's marker was withdrawn 2026-07-19; FF-2C
# has executed the flip for CAISO/MISO/NEISO/PJM only). The DECISION set is the
# five non-ERCOT ISOs; the config reflects the decision, the scorecard reflects
# readiness.
GOLDEN_CMC_BY_ISO: dict[str, bool] = {
    "PJM": True,
    "MISO": True,
    "NYISO": True,
    "NEISO": True,
    "CAISO": True,
}

# The §2.1a c/d/e default flips a golden-posture config must carry (ScenarioConfig
# defaults since FF-1F/FF-2A). Checked by part b.
GOLDEN_DEFAULT_FLIPS: dict[str, object] = {
    "datacenter_load_path": "mid",
    "correlated_forced_outage": True,
    "entry_lookahead_reprice": True,
    "mode": "forecast",
}

# Every IRA/OBBBA credit window (an ira_*_last_year field) the walk reports, with
# a human label. Windows that close before 2050 are policy-correct, not failures.
_IRA_WINDOW_FIELDS: dict[str, str] = {
    "ira_wind_solar_last_year": "wind/solar PTC/ITC (OBBBA cliff)",
    "ira_45u_last_year": "45U existing-nuclear PTC",
    "ira_45q_last_year": "45Q CCUS (legacy field)",
    "ira_h2_45v_last_year": "45V clean-hydrogen PTC",
    "ira_ccus_45q_last_year": "45Q CCUS credit window",
}


def golden_posture_config(
    iso: str, start_year: int = HORIZON_START, end_year: int = HORIZON_END
) -> ScenarioConfig:
    """Return the §2.1a golden-posture ``ScenarioConfig`` for one ISO.

    Forecast mode, the full 2026-2050 horizon, the FF-1F/FF-2A default flips
    (carried by the ScenarioConfig defaults), and the §2.1a decision-(a) per-ISO
    capacity-market clearing (:data:`GOLDEN_CMC_BY_ISO`). ``resolve_policy_bundle``
    is applied so the ``ira_*_last_year`` fields are the resolved forecast values a
    run would use.

    Args:
        iso: Model ISO name.
        start_year: First forecast year (default 2026).
        end_year: Last forecast year (default 2050).

    Returns:
        The golden-posture config, policy-bundle-resolved.
    """
    cfg = ScenarioConfig(
        iso=iso.upper(),
        mode="forecast",
        start_year=start_year,
        end_year=end_year,
        capacity_market_clearing_by_iso=dict(GOLDEN_CMC_BY_ISO),
    )
    return resolve_policy_bundle(cfg)


# --------------------------------------------------------------------------- #
# Part a — input-resolution walk
# --------------------------------------------------------------------------- #
OK, PLATEAU, INFO, MISSING, ERROR, NA = (
    "OK",
    "PLATEAU",
    "INFO",
    "MISSING",
    "ERROR",
    "NA",
)

# A hard-fail status is one that would break (or silently corrupt) a golden solve.
_HARD_STATUSES = frozenset({MISSING, ERROR})


@dataclass
class InputResolution:
    """One forward input's resolution over the full 2026-2050 horizon."""

    iso: str
    name: str
    unit: str
    status: str
    detail: str = ""
    # First year of the terminal plateau (value held flat to 2050), or None when
    # the series varies through 2050. A plateau is a caveat, not a failure.
    hold_flat_from: int | None = None
    horizon: int | None = None  # last "live"/knowable year for horizon-bounded inputs
    sample: dict[int, float] | None = None  # 2026/2030/2040/2050 spot values


def _zone_names(iso: str) -> list[str]:
    return get_iso_config(iso).zone_names


def _finite(x: float) -> bool:
    return x is not None and math.isfinite(float(x))


def _hold_flat_from(values: dict[int, float], tol: float = 1e-9) -> int | None:
    """Return the first year of the terminal plateau (value == 2050 value).

    Returns ``None`` when the series is still changing at its last year (i.e.
    the input is live through 2050). A constant-everywhere series returns its
    first year.
    """
    years = sorted(values)
    if not years:
        return None
    last = values[years[-1]]
    plateau_start = years[-1]
    for y in reversed(years):
        if abs(values[y] - last) <= tol:
            plateau_start = y
        else:
            break
    return plateau_start if plateau_start != years[-1] else None


# Per-year scalar resolvers: (name, unit, fn(cfg, iso, year), zero_ok).
# ``zero_ok`` marks inputs for which 0.0 is a legitimate value (a non-DC ISO's
# block, a no-carbon-program ISO). A non-zero_ok input that resolves to 0 across
# the whole horizon is a MISSING finding.
def _per_year_resolvers():
    return [
        (
            "demand_growth_rate",
            "frac/yr",
            lambda c, iso, y: resolve_demand_growth_rate(c, y),
            False,
        ),
        (
            "datacenter_block_mw",
            "MW",
            lambda c, iso, y: float(
                datacenter_block_mw_by_zone(c, iso, y, _zone_names(iso)).sum()
            ),
            True,
        ),
        (
            "gas_price",
            "$/MMBtu",
            lambda c, iso, y: resolve_annual_gas_price(c, y),
            False,
        ),
        (
            "coal_price",
            "$/MMBtu",
            lambda c, iso, y: resolve_annual_coal_price(c, y),
            False,
        ),
        (
            "oil_price",
            "$/MMBtu",
            lambda c, iso, y: resolve_annual_oil_price(c, y),
            False,
        ),
        ("carbon_price", "$/tCO2", lambda c, iso, y: resolve_carbon_price(c, y), True),
        (
            "ces_premium",
            "$/MWh",
            lambda c, iso, y: federal_ces.premium_for_year(c, y),
            True,
        ),
        (
            "rps_target",
            "frac",
            lambda c, iso, y: (lambda v: float(v) if v is not None else None)(
                get_rps_target(iso, y)
            ),
            True,
        ),
        ("capacity_price_firm", "$/MW-yr", _capacity_price, True),
    ]


def _capacity_price(cfg: ScenarioConfig, iso: str, year: int) -> float:
    """Firm-capacity clearing price at a nominal reserve position (no LP).

    Probes the per-year net-CONE vintage resolution through the shared capacity
    seam at a fixed reserve position (0.95, a mildly-short posture). Energy-only
    ERCOT resolves 0.0 (no capacity market) — reported NA, not MISSING.
    """
    md = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    return float(
        md.capacity_price_per_firm_mw_yr(
            config=cfg, reserve_position=0.95, iso=iso, year=year
        )
    )


def _walk_per_year(
    iso: str, cfg: ScenarioConfig, years: list[int]
) -> list[InputResolution]:
    rows: list[InputResolution] = []
    for name, unit, fn, zero_ok in _per_year_resolvers():
        try:
            values = {y: fn(cfg, iso, y) for y in years}
        except Exception as exc:  # noqa: BLE001 — fail-loud, keep going
            rows.append(
                InputResolution(
                    iso, name, unit, ERROR, detail=f"{type(exc).__name__}: {exc}"
                )
            )
            continue
        # None handling: an all-None series is NA (input not applicable to ISO,
        # e.g. RPS for an ISO without an RPS); a partial-None series is MISSING.
        non_none = {y: v for y, v in values.items() if v is not None}
        if not non_none:
            rows.append(
                InputResolution(
                    iso,
                    name,
                    unit,
                    NA,
                    detail="resolves None for every year (not applicable to ISO)",
                )
            )
            continue
        if len(non_none) < len(values):
            gap = sorted(set(values) - set(non_none))
            rows.append(
                InputResolution(
                    iso,
                    name,
                    unit,
                    MISSING,
                    detail=f"None (unresolved) for years {gap}",
                )
            )
            continue
        bad = [y for y, v in non_none.items() if not _finite(v)]
        if bad:
            rows.append(
                InputResolution(
                    iso,
                    name,
                    unit,
                    ERROR,
                    detail=f"non-finite (NaN/inf) for years {sorted(bad)}",
                )
            )
            continue
        vals = {y: float(v) for y, v in non_none.items()}
        all_zero = all(abs(v) <= 1e-12 for v in vals.values())
        if all_zero and not zero_ok:
            rows.append(
                InputResolution(
                    iso,
                    name,
                    unit,
                    MISSING,
                    detail="resolves 0.0 across the whole horizon (expected a priced value)",
                )
            )
            continue
        neg = [y for y, v in vals.items() if v < 0]
        # A negative RPS/price/growth is nonsensical; carbon can never be < 0.
        if neg and name != "demand_growth_rate":
            rows.append(
                InputResolution(
                    iso,
                    name,
                    unit,
                    ERROR,
                    detail=f"negative value for years {sorted(neg)}",
                )
            )
            continue
        hold = _hold_flat_from(vals)
        status = OK
        detail = ""
        if all_zero and zero_ok:
            status = NA
            detail = "0.0 across horizon (input not active for this ISO/posture)"
        elif hold is not None and hold < years[-1]:
            # A terminal plateau: the value is held constant from `hold` through
            # 2050. Reported factually — the close-out distinguishes a benign
            # design constant (long-era growth rate, fixed net-CONE anchor) from
            # a source-horizon limit (DC-block anchors, RPS final target). Never
            # a failure; it is exactly the "held-constant past year N" honesty
            # §2.1b(c) asks for.
            status = PLATEAU
            detail = f"constant from {hold} through 2050 (held-flat horizon tail)"
        sample = {y: round(vals[y], 4) for y in (2026, 2030, 2040, 2050) if y in vals}
        rows.append(
            InputResolution(
                iso,
                name,
                unit,
                status,
                detail=detail,
                hold_flat_from=hold,
                sample=sample,
            )
        )
    return rows


def _walk_config_level(iso: str, cfg: ScenarioConfig) -> list[InputResolution]:
    rows: list[InputResolution] = []

    # ATB entry costs (config-level, year-invariant base; ATB2024 vintage).
    try:
        atb = resolve_new_entry_costs(cfg)
        capex = {t: d.get("capex_per_kw") for t, d in atb.items()}
        bad = [t for t, v in capex.items() if not _finite(v) or v <= 0]
        if not atb:
            rows.append(
                InputResolution(
                    iso,
                    "atb_entry_costs",
                    "techs",
                    MISSING,
                    detail="NEW_ENTRY_COSTS empty",
                )
            )
        elif bad:
            rows.append(
                InputResolution(
                    iso,
                    "atb_entry_costs",
                    "techs",
                    ERROR,
                    detail=f"non-positive capex for {bad}",
                )
            )
        else:
            rows.append(
                InputResolution(
                    iso,
                    "atb_entry_costs",
                    "techs",
                    OK,
                    detail=f"{len(atb)} techs, ATB2024 vintage (year-invariant base capex)",
                )
            )
    except Exception as exc:  # noqa: BLE001
        rows.append(
            InputResolution(
                iso,
                "atb_entry_costs",
                "techs",
                ERROR,
                detail=f"{type(exc).__name__}: {exc}",
            )
        )

    # RPS ACP ceiling (config/ISO-level).
    try:
        acp = get_rps_acp(iso)
        if acp is None:
            rows.append(
                InputResolution(
                    iso,
                    "rps_acp_price",
                    "$/MWh",
                    NA,
                    detail="no RPS ACP for ISO (no state RPS)",
                )
            )
        elif not _finite(acp) or acp <= 0:
            rows.append(
                InputResolution(
                    iso,
                    "rps_acp_price",
                    "$/MWh",
                    ERROR,
                    detail=f"non-positive ACP {acp}",
                )
            )
        else:
            rows.append(
                InputResolution(iso, "rps_acp_price", "$/MWh", OK, detail=f"ACP {acp}")
            )
    except Exception as exc:  # noqa: BLE001
        rows.append(
            InputResolution(
                iso,
                "rps_acp_price",
                "$/MWh",
                ERROR,
                detail=f"{type(exc).__name__}: {exc}",
            )
        )

    # IRA/OBBBA windows (config-level, resolved by the policy bundle).
    for field_name, label in _IRA_WINDOW_FIELDS.items():
        last = getattr(cfg, field_name, None)
        if last is None:
            rows.append(
                InputResolution(
                    iso, field_name, "year", NA, detail=f"{label}: no window field"
                )
            )
        elif not isinstance(last, int):
            rows.append(
                InputResolution(
                    iso, field_name, "year", ERROR, detail=f"{label}: non-int {last!r}"
                )
            )
        else:
            closes_in_window = HORIZON_START <= last < HORIZON_END
            status = INFO if closes_in_window else OK
            det = f"{label}: credit active through {last}"
            if closes_in_window:
                det += f" (window closes inside 2026-2050 — {HORIZON_END - last} yr of horizon with credit expired; policy-correct)"
            rows.append(
                InputResolution(
                    iso, field_name, "year", status, detail=det, horizon=last
                )
            )

    # Capacity-market clearing gate (config/ISO-level).
    cmc = resolve_capacity_market_clearing(cfg, iso)
    prm = PLANNING_RESERVE_MARGIN_BY_ISO.get(iso)
    rows.append(
        InputResolution(
            iso,
            "capacity_market_clearing",
            "bool",
            OK if isinstance(cmc, bool) else ERROR,
            detail=f"clearing={cmc}; planning_reserve_margin={prm}",
        )
    )

    # Confirmed-retirements horizon (reads the clean partition; fail-loud in
    # forecast mode when the clean tree is unbuilt — a real golden precondition).
    try:
        exits = load_confirmed_exits(iso, required=True)
        if not exits:
            rows.append(
                InputResolution(
                    iso,
                    "confirmed_retirements",
                    "exits",
                    NA,
                    detail="registry present but 0 live rows (degrades to economic screen)",
                )
            )
        else:
            yrs = [e.exit_year for e in exits]
            horizon = max(yrs)
            det = (
                f"{len(exits)} confirmed exits, {min(yrs)}-{horizon}; "
                f"no confirmed channel past {horizon} → economic screen governs "
                f"{horizon + 1}-2050"
            )
            status = INFO if horizon < HORIZON_END else OK
            rows.append(
                InputResolution(
                    iso,
                    "confirmed_retirements",
                    "exits",
                    status,
                    detail=det,
                    horizon=horizon,
                )
            )
    except RuntimeError as exc:
        # The loader's own fail-loud: clean partition absent while
        # confirmed_exits_enabled is on in forecast mode. A golden solve WILL
        # hit this on a fresh checkout — a genuine readiness blocker.
        rows.append(
            InputResolution(
                iso,
                "confirmed_retirements",
                "exits",
                MISSING,
                detail=(
                    "clean partition unbuilt (data/clean is gitignored): "
                    "run scripts/data/curate_confirmed_retirements.py "
                    "before any golden solve. " + str(exc)[:160]
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001
        rows.append(
            InputResolution(
                iso,
                "confirmed_retirements",
                "exits",
                ERROR,
                detail=f"{type(exc).__name__}: {exc}",
            )
        )

    # Weather-year pool (config-level). The forecast demand shape is pinned to
    # config.weather_year; it must be inside the ISO's verified pool.
    pool = weather_year_pool(iso)
    if cfg.weather_year in pool:
        rows.append(
            InputResolution(
                iso,
                "weather_year_pool",
                "year",
                OK,
                detail=f"weather_year={cfg.weather_year} in verified pool {pool}",
            )
        )
    else:
        rows.append(
            InputResolution(
                iso,
                "weather_year_pool",
                "year",
                MISSING,
                detail=f"weather_year={cfg.weather_year} NOT in verified pool {pool}",
            )
        )
    return rows


def walk_inputs(
    iso: str, start_year: int = HORIZON_START, end_year: int = HORIZON_END
) -> list[InputResolution]:
    """Resolve every exogenous forward input for one ISO across 2026-2050 (no LP).

    Args:
        iso: Model ISO name.
        start_year/end_year: Horizon bounds (default the full 2026-2050).

    Returns:
        One :class:`InputResolution` per input, ordered per-year inputs then
        config-level inputs.
    """
    cfg = golden_posture_config(iso, start_year, end_year)
    years = list(range(start_year, end_year + 1))
    return _walk_per_year(iso, cfg, years) + _walk_config_level(iso, cfg)


def resolve_report(isos: tuple[str, ...] = GOLDEN_ISOS) -> dict:
    """Run the input-resolution walk for every ISO and summarize (no LP)."""
    per_iso: dict[str, list[dict]] = {}
    hard_fail: list[str] = []
    plateau: list[str] = []
    for iso in isos:
        rows = walk_inputs(iso)
        per_iso[iso] = [asdict(r) for r in rows]
        for r in rows:
            if r.status in _HARD_STATUSES:
                hard_fail.append(f"{iso}:{r.name} [{r.status}] {r.detail}")
            elif r.status == PLATEAU:
                plateau.append(f"{iso}:{r.name} — {r.detail}")
    return {
        "instrument": "input-resolution-walk",
        "horizon": [HORIZON_START, HORIZON_END],
        "isos": list(isos),
        "hard_fail_count": len(hard_fail),
        "hard_fails": hard_fail,
        "plateau_notes": plateau,
        "green": len(hard_fail) == 0,
        "per_iso": per_iso,
    }


# --------------------------------------------------------------------------- #
# Part b — config completeness
# --------------------------------------------------------------------------- #
def config_completeness(iso: str) -> dict:
    """Verify the golden-posture config round-trips and reflects §2.1a (no LP).

    Checks (rule 24 / plan §2.1a):

    * ``config.yaml`` round-trip (``to_yaml_full`` -> ``from_yaml``) is a
      value-identical config with a **stable cache_key**;
    * every §2.1a c/d/e default flip is present
      (:data:`GOLDEN_DEFAULT_FLIPS`);
    * decision (a) capacity-market clearing resolves ON for every real-capacity
      ISO and OFF for energy-only ERCOT;
    * the run's full flag surface is dumpable (``asdict`` non-empty) so
      ``run_config.json`` can record every tunable.
    """
    import tempfile

    cfg = golden_posture_config(iso)
    checks: list[dict] = []

    def _add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # Round-trip through config.yaml (the faithful ScenarioConfig dump the cache
    # + run_config helper read — see _ff2d_emit_run_config.py).
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "config.yaml"
        cfg.to_yaml_full(path)
        rt = ScenarioConfig.from_yaml(path)
    key_stable = rt.cache_key() == cfg.cache_key()
    _add(
        "cache_key_stable_round_trip",
        key_stable,
        f"{cfg.cache_key()} == {rt.cache_key()}",
    )
    # run_config.json is JSON, which renders tuple and list identically (an
    # array) — the same normalization cache_key hashes through. So the faithful
    # "run_config round-trips" check compares the JSON-normalized configs, not a
    # strict Python asdict == (which trips on the benign tuple->list coercion the
    # *_offer_surface_netload_pcts sequence fields undergo on any yaml/json
    # round-trip; LP-inert, and exactly how run_config.json already stores them).
    same_json = json.dumps(asdict(cfg), sort_keys=True, default=list) == json.dumps(
        asdict(rt), sort_keys=True, default=list
    )
    _add(
        "run_config_round_trips_value_identical",
        same_json,
        "JSON-normalized config equality after yaml round-trip "
        "(tuple->list on sequence fields is the expected run_config.json form)",
    )

    # §2.1a c/d/e default flips.
    for fname, want in GOLDEN_DEFAULT_FLIPS.items():
        got = getattr(cfg, fname, None)
        _add(f"posture:{fname}", got == want, f"want={want!r} got={got!r}")

    # §2.1a decision (a): per-ISO capacity-market clearing.
    want_cmc = GOLDEN_CMC_BY_ISO.get(iso, False)
    got_cmc = resolve_capacity_market_clearing(cfg, iso)
    _add(
        "posture:capacity_market_clearing",
        got_cmc == want_cmc,
        f"want={want_cmc} got={got_cmc} (ERCOT energy-only OFF; §2.1a decision-a)",
    )

    # Full flag surface dumpable (rule 24 — every tunable visible in run_config).
    dump = asdict(cfg)
    _add(
        "run_config_full_surface",
        isinstance(dump, dict) and len(dump) > 50,
        f"{len(dump)} fields in the config dump",
    )

    ok = all(c["ok"] for c in checks)
    return {
        "instrument": "config-completeness",
        "iso": iso,
        "cache_key": cfg.cache_key(),
        "green": ok,
        "checks": checks,
    }


def config_report(isos: tuple[str, ...] = GOLDEN_ISOS) -> dict:
    per_iso = {iso: config_completeness(iso) for iso in isos}
    green = all(r["green"] for r in per_iso.values())
    return {"instrument": "config-completeness", "green": green, "per_iso": per_iso}


# --------------------------------------------------------------------------- #
# Part d — wall/RSS projection ("what would 10 hours buy")
# --------------------------------------------------------------------------- #
# Measured per-ISO T1-F anchors (FF-2D §2.1, HEAD 15dfe15, the FF-2C flipped
# defaults, MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 on a
# 15 GB / 4-CPU box). median_yr_s / peak_rss_gb are the T1-F medians; the
# late-horizon multiplier encodes the §2.4 super-linear caution (LPs grow as
# economic entry adds units — PJM/MISO late years measured at 30-40 min/yr, ~8x
# the early-year median; the others scale more gently). These are PROJECTION
# INPUTS, never fit targets (rule 13); the projection is arithmetic, no solve.
FF2D_ANCHORS: dict[str, dict[str, float]] = {
    "ERCOT": {
        "median_yr_s": 144.0,
        "peak_rss_gb": 3.71,
        "late_mult": 3.0,
        "late_rss_gb": 4.6,
    },
    "CAISO": {
        "median_yr_s": 200.0,
        "peak_rss_gb": 4.37,
        "late_mult": 3.0,
        "late_rss_gb": 5.5,
    },
    "NYISO": {
        "median_yr_s": 90.0,
        "peak_rss_gb": 3.33,
        "late_mult": 2.5,
        "late_rss_gb": 4.2,
    },
    "NEISO": {
        "median_yr_s": 78.0,
        "peak_rss_gb": 3.42,
        "late_mult": 2.5,
        "late_rss_gb": 4.3,
    },
    "PJM": {
        "median_yr_s": 235.0,
        "peak_rss_gb": 8.61,
        "late_mult": 8.0,
        "late_rss_gb": 10.0,
    },
    "MISO": {
        "median_yr_s": 324.0,
        "peak_rss_gb": 9.34,
        "late_mult": 8.0,
        "late_rss_gb": 10.5,
    },
}

# §2.4 box anchor: two per-plant multi-zone ISOs (>= ~8.6 GB each) cannot co-run
# on a 15 GB box (measured OOM, RC-1A-D1); a single ISO whose late-horizon RSS
# exceeds this runs solo.
BOX_RAM_GB = 15.0
NO_CORUN_RSS_GB = 8.6


def project_full_horizon(
    horizon_years: int = HORIZON_END - HORIZON_START + 1,
) -> dict:
    """Project per-ISO full-horizon (2026-2050) wall-clock/RSS with a co-run plan.

    Two bounds per ISO (no solve — arithmetic over the measured FF-2D anchors):

    * **lower bound** = ``median_yr_s x horizon_years`` — early years are a firm
      floor (FF-3B §2.4);
    * **projected (super-linear)** = a ramp from the early-year median up to
      ``late_mult x median`` at 2050, integrated across the horizon — encodes the
      §2.4 caution that late-horizon LPs grow super-linearly as economic entry
      adds units (do NOT extrapolate flat).

    The concurrency plan honours rule 12: two per-plant multi-zone ISOs cannot
    co-run on a 15 GB box, so per-ISO peak RSS >= 8.6 GB forces solo scheduling.
    """
    per_iso: dict[str, dict] = {}
    for iso, a in FF2D_ANCHORS.items():
        med = a["median_yr_s"]
        late_mult = a["late_mult"]
        # Linear ramp of the per-year cost from med (year 0) to med*late_mult
        # (final year); the integral is the average of the endpoints x years.
        ramp_avg = med * (1.0 + late_mult) / 2.0
        lower_s = med * horizon_years
        proj_s = ramp_avg * horizon_years
        # Peak RSS is the MEASURED/anchored late-horizon value (§2.4), not scaled
        # by the wall multiplier — RSS grows far more gently than solve time (a
        # sparse CSC LP gains rows/cols but stays sparse). PJM/MISO land at ~10 GB
        # late, forcing solo scheduling on a 15 GB box; the smaller per-plant
        # ISOs drift up mildly and stay pairable.
        peak_rss_late = a["late_rss_gb"]
        per_iso[iso] = {
            "median_yr_s": med,
            "t1f_peak_rss_gb": a["peak_rss_gb"],
            "late_mult": late_mult,
            "lower_bound_h": round(lower_s / 3600.0, 2),
            "projected_h": round(proj_s / 3600.0, 2),
            "projected_late_yr_min": round(med * late_mult / 60.0, 1),
            "proj_peak_rss_gb": round(peak_rss_late, 2),
            "no_corun": peak_rss_late >= NO_CORUN_RSS_GB,
        }
    # Concurrency plan: ISOs whose projected peak RSS forces solo scheduling run
    # one at a time; the rest may pair (<= 2, rule 12). Serial-worst-case wall is
    # the sum of solo-ISO projections plus the max of each co-run pair.
    solo = [iso for iso, r in per_iso.items() if r["no_corun"]]
    pairable = [iso for iso, r in per_iso.items() if not r["no_corun"]]
    solo_h = sum(per_iso[iso]["projected_h"] for iso in solo)
    # Pair the pairable ISOs two at a time; each pair's wall = the slower leg.
    pair_h = 0.0
    pl = sorted(pairable, key=lambda i: per_iso[i]["projected_h"], reverse=True)
    for i in range(0, len(pl), 2):
        chunk = pl[i : i + 2]
        pair_h += max(per_iso[c]["projected_h"] for c in chunk)
    total_serial_h = round(solo_h + pair_h, 2)
    return {
        "instrument": "wall-rss-projection",
        "horizon_years": horizon_years,
        "box_ram_gb": BOX_RAM_GB,
        "no_corun_rss_gb": NO_CORUN_RSS_GB,
        "caveat": (
            "Early years are a firm lower bound; late-horizon LPs grow "
            "super-linearly (FF-3B §2.4) — do NOT extrapolate the median "
            "flat. CES-armed legs add ~4-5 h/ISO (deferred W4)."
        ),
        "per_iso": per_iso,
        "concurrency_plan": {
            "solo_isos": solo,
            "pairable_isos": pairable,
            "solo_wall_h": round(solo_h, 2),
            "paired_wall_h": round(pair_h, 2),
            "total_serial_wall_h": total_serial_h,
        },
        "what_would_10h_buy": _ten_hour_reading(per_iso),
    }


def _ten_hour_reading(per_iso: dict[str, dict]) -> str:
    fastest = min(per_iso.items(), key=lambda kv: kv[1]["projected_h"])
    within_10 = [iso for iso, r in per_iso.items() if r["projected_h"] <= 10.0]
    return (
        f"A 10-hour budget buys ONE full-horizon golden ISO for "
        f"{sorted(within_10)} (each projected <= 10 h). "
        f"The heaviest (PJM/MISO) approach or exceed 10 h alone at the "
        f"super-linear projection and must run solo (>= 8.6 GB). Cheapest is "
        f"{fastest[0]} at ~{fastest[1]['projected_h']} h."
    )


# --------------------------------------------------------------------------- #
# Part c — kill-resume drill (THE ONLY SOLVE; T0 NEISO 2026-2028)
# --------------------------------------------------------------------------- #
def _bundle_signature(run_dir: Path) -> dict:
    """Deterministic per-year dispatch+ledger signature of a solved bundle.

    Reads the committed-artifact layer only (parquet dispatch/prices + the
    evolution ledgers), the same surface the invariants/trajectory score, so two
    result-equivalent bundles produce byte-equal signatures regardless of
    wall-clock metadata.
    """
    from scripts import check_forecast_invariants as C

    run = C.load_run(run_dir)
    sig: dict[int, dict] = {}
    for year in run.solved_years:
        yd = run.years[year]
        disp = np.asarray(yd.result.dispatch, dtype=float)
        price = np.asarray(yd.result.prices, dtype=float)
        led = run.ledgers.get(year, {})
        sig[year] = {
            "dispatch_sum": round(float(disp.sum()), 3),
            "dispatch_hash": _arr_hash(disp),
            "price_sum": round(float(price.sum()), 3),
            "price_hash": _arr_hash(price),
            "n_retire": len(led.get("retirements", [])),
            "n_thermal_add": len(led.get("thermal_additions", [])),
            "n_renew_add": len(led.get("renewable_additions", [])),
            "n_storage_add": len(led.get("storage_additions", [])),
        }
    return sig


def _arr_hash(arr: np.ndarray) -> str:
    import hashlib

    return hashlib.sha256(
        np.ascontiguousarray(arr, dtype=np.float64).tobytes()
    ).hexdigest()[:16]


class _KillSignal(Exception):
    """Sentinel raised inside the drill to simulate a mid-horizon process kill."""


def kill_resume_drill(
    iso: str = "NEISO",
    start_year: int = 2026,
    end_year: int = 2028,
    work_dir: Path | None = None,
) -> dict:
    """Prove a killed run resumes to a result-identical bundle (T0 solve).

    The kill MUST happen inside the same ``cache_key`` as the resume — the
    horizon bounds enter the cache key, so a shorter "partial" run would land in
    a different cache dir and the resume would silently re-solve everything (it
    would never exercise the resume path). This drill therefore runs the SAME
    full-window config for both the kill and the resume:

    1. **control** — the full window in one invocation, in its own cache root.
    2. **kill** — the SAME full-window config in a second cache root, with
       ``runner.save_result`` monkeypatched to raise :class:`_KillSignal` right
       after the final-pass parquet for ``end_year - 1`` is written — exactly the
       state a real ``kill -9`` leaves: years ``start .. end_year-1`` cached,
       ``end_year`` unsolved.
    3. **resume** — the SAME full-window config re-invoked over that partial
       cache. The already-solved years load from cache (``is_cached``
       short-circuit, ``runner.py:1156``) and only ``end_year`` solves. The
       fleet-evolution state (fleet, cumulative deployment, prior-year duals)
       reconstructs deterministically from the loaded results.

    Passes iff (i) the resume's ``cache_key`` matches the control's, (ii) the
    resume LOADED the pre-kill years rather than re-solving them (their parquet
    mtimes are unchanged across the resume), and (iii) every year's
    dispatch+ledger signature is identical to the control's. The only LP solve in
    the battery, bounded to a T0 window (rule 12; §2.1b).

    Args:
        iso: ISO to drill (default NEISO — cheapest per-plant, ~1.5-2 min/yr).
        start_year/end_year: T0 window (default 2026-2028).
        work_dir: Root for the two isolated cache dirs (a temp dir if None).

    Returns:
        A dict with the per-year equivalence verdict and the resume-load proof.
    """
    import tempfile

    from market_sim import runner as runnermod
    from market_sim.pipeline.api import run_scenario
    from market_sim.results import cache as cachemod

    kill_after_year = end_year - 1

    tmp_ctx = None
    if work_dir is None:
        tmp_ctx = tempfile.TemporaryDirectory()
        work_dir = Path(tmp_ctx.name)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    control_root = work_dir / "control"
    resume_root = work_dir / "resume"
    orig_root = cachemod.CACHE_ROOT
    orig_save = runnermod.save_result

    def _config():
        # The SAME full-window config for control, kill, and resume — so the
        # kill and resume share one cache_key (the resume actually resumes).
        return golden_posture_config(iso, start_year, end_year)

    try:
        # 1. control — full window, fresh cache root. The RUNNER-returned key is
        #    the authoritative cache key: run_scenario_iso applies each ISO's
        #    default config overrides (runner.py ~431-441) BEFORE hashing, so it
        #    differs from a bare golden_posture_config().cache_key(). We locate
        #    every bundle by this returned key, never a recomputed one.
        cachemod.CACHE_ROOT = control_root
        control_key = run_scenario(_config(), iso)

        # 2. kill — same config, second cache root, interrupted after the
        #    final-pass save of `kill_after_year`. Same config ⇒ same runner key
        #    ⇒ the partial cache lands under resume_root/iso/control_key.
        cachemod.CACHE_ROOT = resume_root

        def _killing_save(result, config, iso_, year, **kwargs):
            path = orig_save(result, config, iso_, year, **kwargs)
            if kwargs.get("pass_label") is None and int(year) >= kill_after_year:
                raise _KillSignal(f"simulated kill after {year}")
            return path

        runnermod.save_result = _killing_save
        killed = False
        try:
            run_scenario(_config(), iso)
        except _KillSignal:
            killed = True
        finally:
            runnermod.save_result = orig_save

        # Snapshot the pre-kill cached parquets' mtimes (proof they are loaded,
        # not re-solved, on resume).
        resume_dir = resume_root / iso / control_key
        pre_kill_years = list(range(start_year, kill_after_year + 1))
        mtimes_before = {
            y: (resume_dir / f"year_{y}.parquet").stat().st_mtime
            for y in pre_kill_years
            if (resume_dir / f"year_{y}.parquet").exists()
        }

        # 3. resume — same config, over the partial cache.
        resume_key2 = run_scenario(_config(), iso)
        mtimes_after = {
            y: (resume_dir / f"year_{y}.parquet").stat().st_mtime
            for y in pre_kill_years
            if (resume_dir / f"year_{y}.parquet").exists()
        }
    finally:
        cachemod.CACHE_ROOT = orig_root
        runnermod.save_result = orig_save

    control_dir = control_root / iso / control_key
    control_sig = _bundle_signature(control_dir)
    resume_sig = _bundle_signature(resume_dir)

    cached_years_loaded = bool(mtimes_before) and all(
        mtimes_before.get(y) == mtimes_after.get(y) for y in mtimes_before
    )

    years = sorted(set(control_sig) | set(resume_sig))
    per_year = []
    sigs_equal = True
    for y in years:
        eq = control_sig.get(y) == resume_sig.get(y)
        sigs_equal = sigs_equal and eq
        per_year.append(
            {
                "year": y,
                "equal": eq,
                "resumed_from_cache": y in mtimes_before,
                "control": control_sig.get(y),
                "resume": resume_sig.get(y),
            }
        )

    key_match = control_key == resume_key2
    green = bool(killed and key_match and cached_years_loaded and sigs_equal)
    result = {
        "instrument": "kill-resume-drill",
        "iso": iso,
        "window": [start_year, end_year],
        "kill_after_year": kill_after_year,
        "killed_mid_horizon": killed,
        "cache_key_match": key_match,
        "cached_years_loaded_not_resolved": cached_years_loaded,
        "resumed_years": sorted(mtimes_before),
        "result_identical": sigs_equal,
        "green": green,
        "per_year": per_year,
    }
    if tmp_ctx is not None:
        tmp_ctx.cleanup()
    return result


# --------------------------------------------------------------------------- #
# Registration — the forecast-validation-namespace §2.1b scorecard
# --------------------------------------------------------------------------- #
_MARKER_PATH = _ROOT / "frontend/data/backcast/calibration-complete.json"
_FF2D_VERDICTS = _ROOT / "docs/handoffs/ff-t1-gate-verdicts.json"


def _marker_state(iso: str) -> dict:
    """Read the §2.1b(a) backcast keeper + calibration-complete marker state."""
    try:
        obj = json.loads(_MARKER_PATH.read_text())
    except (OSError, ValueError):
        return {"marker": "unknown", "keeper": None}
    if iso in obj.get("complete", {}):
        row = obj["complete"][iso]
        return {
            "marker": "complete",
            "keeper": row.get("keeper"),
            "declared": row.get("declared"),
        }
    if iso in obj.get("withdrawn", {}):
        row = obj["withdrawn"][iso]
        return {
            "marker": "withdrawn",
            "keeper": row.get("keeper_at_declaration"),
            "withdrawn": row.get("withdrawn"),
        }
    return {"marker": "none", "keeper": None}


def _t1f_verdict(iso: str) -> dict:
    """Read the ISO's FF-2D T1-F rubric determination (no re-score)."""
    try:
        obj = json.loads(_FF2D_VERDICTS.read_text())
    except (OSError, ValueError):
        return {"determination": "unknown"}
    row = obj.get(f"{iso.lower()}-t1f", {})
    return {
        "determination": row.get("determination", "unknown"),
        "reasons": row.get("reasons", []),
    }


def build_registration(drill_result: dict | None = None) -> dict:
    """Assemble the compact FF-3E readiness artifact + §2.1b gate scorecard.

    Runs the three no-LP instruments, folds in the kill-resume drill result if
    provided, and reads the committed backcast marker + FF-2D verdict state to
    build the per-ISO gate scorecard. Registered on the forecast-validation
    namespace only (rule 15 / plan §2.3) — it never writes the backcast registry.
    """
    resolve = resolve_report()
    cfg = config_report()
    proj = project_full_horizon()
    per_iso_resolve = {
        iso: {
            "hard_fails": [r["name"] for r in rows if r["status"] in _HARD_STATUSES],
            "plateaus": [r["name"] for r in rows if r["status"] == PLATEAU],
        }
        for iso, rows in resolve["per_iso"].items()
    }
    scorecard = {}
    for iso in GOLDEN_ISOS:
        marker = _marker_state(iso)
        v = _t1f_verdict(iso)
        pj = proj["per_iso"].get(iso, {})
        scorecard[iso] = {
            "gate_a_backcast": marker,
            "gate_b_t1f": v,
            "gate_c_readiness": {
                "input_resolution_green": not per_iso_resolve[iso]["hard_fails"],
                "config_green": cfg["per_iso"][iso]["green"],
            },
            "gate_c_projected_wall_h": pj.get("projected_h"),
            "gate_c_solo": pj.get("no_corun"),
            "gate_open": False,  # no ISO clears (b) at HEAD; owner decides (d)
        }
    return {
        "run_id": "ff-3e-readiness",
        "meta": {
            "battery": "ff-3e-readiness",
            "kind": "readiness",
            "session": "FF-3E",
            "produced": "2026-07-20",
            "horizon": [HORIZON_START, HORIZON_END],
        },
        "green": bool(
            resolve["green"]
            and cfg["green"]
            and (drill_result is None or drill_result.get("green"))
        ),
        "input_resolution": {
            "green": resolve["green"],
            "hard_fail_count": resolve["hard_fail_count"],
            "hard_fails": resolve["hard_fails"],
            "plateau_notes": resolve["plateau_notes"],
            "per_iso": per_iso_resolve,
        },
        "config_completeness": {
            "green": cfg["green"],
            "per_iso": {iso: r["green"] for iso, r in cfg["per_iso"].items()},
        },
        "kill_resume_drill": drill_result,
        "wall_rss_projection": proj,
        "gate_scorecard": scorecard,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _write(out: Path | None, name: str, payload: dict) -> None:
    if out is None:
        return
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    # ensure_ascii=False so the committed artifact carries readable UTF-8
    # (em-dash, §) rather than \uXXXX escapes — the registered JSON is a
    # human-read dashboard sidecar, and this keeps it byte-reproducible against
    # what a reader sees.
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {p}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_res = sub.add_parser("resolve", help="Part a — input-resolution walk (no LP).")
    p_res.add_argument("--iso", help="Single ISO; default all six.")
    p_res.add_argument("--out", type=Path, default=None)

    p_cfg = sub.add_parser("config", help="Part b — config completeness (no LP).")
    p_cfg.add_argument("--out", type=Path, default=None)

    p_prj = sub.add_parser("projection", help="Part d — wall/RSS projection (no LP).")
    p_prj.add_argument("--out", type=Path, default=None)

    p_all = sub.add_parser(
        "all", help="Parts a+b+d (no LP) + write the readiness bundle."
    )
    p_all.add_argument("--out", type=Path, default=None)

    p_kr = sub.add_parser("kill-resume", help="Part c — kill-resume drill (T0 solve).")
    p_kr.add_argument("--iso", default="NEISO")
    p_kr.add_argument("--start-year", type=int, default=2026)
    p_kr.add_argument("--end-year", type=int, default=2028)
    p_kr.add_argument("--work-dir", type=Path, default=None)
    p_kr.add_argument("--out", type=Path, default=None)

    p_reg = sub.add_parser(
        "register",
        help="Build the forecast-validation §2.1b scorecard artifact (no LP).",
    )
    p_reg.add_argument(
        "--drill-result",
        type=Path,
        default=None,
        help="Path to a kill_resume_drill.json to fold into the artifact.",
    )
    p_reg.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "frontend/data/hindcast",
        help="Output dir (default the forecast-validation namespace).",
    )

    args = ap.parse_args(argv)

    if args.cmd == "resolve":
        isos = (args.iso.upper(),) if args.iso else GOLDEN_ISOS
        rep = resolve_report(isos)
        _print_resolve(rep)
        _write(args.out, "input_resolution.json", rep)
        return 0 if rep["green"] else 1

    if args.cmd == "config":
        rep = config_report()
        for iso, r in rep["per_iso"].items():
            bad = [c for c in r["checks"] if not c["ok"]]
            print(
                f"  {iso:6} {'GREEN' if r['green'] else 'FAIL'}  ({len(bad)} failed checks)"
            )
            for c in bad:
                print(f"      [FAIL] {c['check']}: {c['detail']}")
        _write(args.out, "config_completeness.json", rep)
        return 0 if rep["green"] else 1

    if args.cmd == "projection":
        rep = project_full_horizon()
        _print_projection(rep)
        _write(args.out, "wall_rss_projection.json", rep)
        return 0

    if args.cmd == "all":
        resolve = resolve_report()
        cfg = config_report()
        proj = project_full_horizon()
        bundle = {
            "battery": "ff-3e-readiness",
            "horizon": [HORIZON_START, HORIZON_END],
            "green": resolve["green"] and cfg["green"],
            "input_resolution": resolve,
            "config_completeness": cfg,
            "wall_rss_projection": proj,
        }
        _print_resolve(resolve)
        print(f"  config-completeness: {'GREEN' if cfg['green'] else 'FAIL'}")
        _print_projection(proj)
        _write(args.out, "ff3e_readiness_bundle.json", bundle)
        return 0 if bundle["green"] else 1

    if args.cmd == "kill-resume":
        print(
            f"  kill-resume drill: {args.iso} {args.start_year}-{args.end_year} (T0 solve)..."
        )
        rep = kill_resume_drill(args.iso, args.start_year, args.end_year, args.work_dir)
        print(
            f"  killed_mid_horizon={rep['killed_mid_horizon']} "
            f"cache_key_match={rep['cache_key_match']} "
            f"cached_loaded={rep['cached_years_loaded_not_resolved']} "
            f"result_identical={rep['result_identical']} "
            f"-> {'GREEN' if rep['green'] else 'FAIL'}"
        )
        print(f"      resumed years (loaded from cache): {rep['resumed_years']}")
        for r in rep["per_year"]:
            tag = "resumed" if r["resumed_from_cache"] else "solved"
            print(f"      {r['year']}: {'equal' if r['equal'] else 'DIFF'} ({tag})")
        _write(args.out, "kill_resume_drill.json", rep)
        return 0 if rep["green"] else 1

    if args.cmd == "register":
        drill = None
        if args.drill_result is not None and args.drill_result.exists():
            drill = json.loads(args.drill_result.read_text())
        art = build_registration(drill)
        _write(args.out, "ff-3e-readiness.json", art)
        print(f"  registered ff-3e-readiness (green={art['green']})")
        for iso, s in art["gate_scorecard"].items():
            print(
                f"    {iso:6} gate_a={s['gate_a_backcast']['marker']:9} "
                f"gate_b={s['gate_b_t1f']['determination']:5} "
                f"readiness={'green' if s['gate_c_readiness']['input_resolution_green'] and s['gate_c_readiness']['config_green'] else 'FAIL'} "
                f"gate_open={s['gate_open']}"
            )
        return 0 if art["green"] else 1

    return 2


def _print_resolve(rep: dict) -> None:
    print(f"\n===== input-resolution walk ({HORIZON_START}-{HORIZON_END}) =====")
    print(
        f"  hard fails: {rep['hard_fail_count']}  -> {'GREEN' if rep['green'] else 'FAIL'}"
    )
    for hf in rep["hard_fails"]:
        print(f"    [HARD] {hf}")
    for s in rep["plateau_notes"][:40]:
        print(f"    [plateau] {s}")


def _print_projection(rep: dict) -> None:
    print("\n===== full-horizon wall/RSS projection (2026-2050) =====")
    print(
        f"  {'ISO':6} {'lower_h':>8} {'proj_h':>8} {'late_min/yr':>11} {'peak_GB':>8} {'solo?':>6}"
    )
    for iso, r in rep["per_iso"].items():
        print(
            f"  {iso:6} {r['lower_bound_h']:>8} {r['projected_h']:>8} "
            f"{r['projected_late_yr_min']:>11} {r['proj_peak_rss_gb']:>8} "
            f"{'yes' if r['no_corun'] else 'no':>6}"
        )
    cp = rep["concurrency_plan"]
    print(f"  concurrency: solo={cp['solo_isos']} pairable={cp['pairable_isos']}")
    print(f"  total serial wall (rule-12 co-run plan): {cp['total_serial_wall_h']} h")
    print(f"  {rep['what_would_10h_buy']}")


if __name__ == "__main__":
    raise SystemExit(main())
