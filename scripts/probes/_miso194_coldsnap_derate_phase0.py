"""miso-194 phase-0 census: a MISO winter cold-snap gas derate (zero-solve).

Charter: the miso-192-corrected census queue, lever 2 — CHARTER exactly ONE of
matrix rows ``gas_coldsnap_derate`` (K@NEISO) or ``winter_fuelsec_posture``
(K@NEISO), never both (rule 19 [R-ONE-MECH]) — aimed at the Jan-2025 −1.43 pp
winter component of C3a-2025 named in FINDING-miso178 §1. Keeper at session
start and throughout: ``2026-08-30-miso-191-bexit`` (bundle
``results/calibration/miso191_bax_B``), Ask-A reproduced NOT-YET on
{C3a-2025 −12.3405%} ALONE, C1 16/16 / 12/12 free, C3c the single ledgered
caveat, C6 attested, C8 PASS (two grounded notes); ``audit_keepers --iso MISO``
PASS 0/0; ``build_status --iso MISO --check`` in sync; ``check_mechanism_matrix``
integrity OK.

THE CHOICE (Ask B), made from the two NEISO cells' mechanism SHAPE only — no
parameter and no verdict transfers (rules 25 [R-ISO-SCOPE] / 28(d)); MISO's own
numbers are derived below from MISO's own admissible record:

  CHARTERED: ``gas_coldsnap_derate``. (1) DIRECTION. It REMOVES gas capability
  in cold hours, so its price action is upward — the sign MISO's Jan-2025
  −13.8% own-month under-price needs. ``winter_fuelsec_posture`` is a must-run
  COMMITMENT floor (neiso_winter_fuel_mustrun at min-stable + an oil-inventory
  budget): it ADDS forced inframarginal supply, whose price action is downward,
  i.e. adverse by construction on an under-priced target. (2) IT HAS A MISO
  OBJECT. The fuel-security posture is an ISO-NE PROGRAM — the FERC ER14-2407
  Winter Reliability Program's oil-tank inventory, sized in barrels — with no
  MISO counterpart in kind; MISO's winter instruments are its cold-weather
  operating procedures and Maximum Generation Events, not a budgeted oil
  inventory, and MISO's oil-fired steam fleet is trivial. The cold-snap gas
  derate's object — winter gas deliverability lost to heating load — is a
  physical driver MISO's own published record measures (below). (3) RULE 19.
  ``winter_fuelsec_posture`` would stack a second must-run floor on ST_GAS, a
  class already reported ABOVE its C8 budget on this keeper (2025 ST_GAS 34.2%
  forced, grounded); the derate writes availability, where the target
  population currently carries no temperature-conditioned mechanism at all
  (W1 below tests exactly that). ``winter_fuelsec_posture`` therefore stays
  **U** in MISO's shard, untested and un-transferred.

WIRING NOTE (stated ex ante, not an adjudicating quantity): the implementing
function ``model.interchange.neiso.inject_neiso_gas_coldsnap_derate`` hard-gates
``if iso != "NEISO": return False`` and reads a NEISO-only temperature wrapper,
so an arm would require a generalization + a MISO-scoped ``ScenarioConfig``
field (rule 28(c): a new row + a cell line in every shard, same PR). Phase 0 is
what decides whether that code is worth writing. NOTHING IS ARMED HERE.

THE DOCUMENTED SUPERSEDING-MECHANISM PROBLEM, named before it is tested
(the charter's "anticipate documented superseding mechanisms"): this repo
already carries an owner-charter ruling that a temperature-keyed cold-event
forced-outage derate is a DOUBLE COUNT in backcast mode.
``data.outages.apply_correlated_outage_derate`` — whose own docstring calls
itself "the neiso_gas_coldsnap_derate pattern, generalized" — refuses to fire
when ``mode != forecast`` and again when ``outage_source == "historic"``, with
the comment "measured overlays own the events (belt and braces)" (FF-1B charter
D.5). The MISO keeper is a backcast with ``outage_source='historic'`` and the
CAMPD unit-outage overlay armed, so that ruling points straight at this lever.
It is NOT, however, a settled bar: pjm-161 phase 0 MEASURED the ruling's
premise and falsified it for PJM (the CAMPD detector infers unavailability from
ZERO GENERATION, so it cannot see an outage at a unit that would not have run
anyway; corr(derated MW, net load) −0.68..−0.77 in every year, and during Winter
Storm Elliott the envelope asserted its LOWEST outage level of the year against
PJM's published 40.7 GW forced). W2 below is that same test, re-derived on
MISO's own bases. Read for shape; every MISO number is MISO's own.

FROZEN ADJUDICATION RULE (ex ante, pushed before any adjudicating quantity —
the miso-193 pattern; the miso-191 mis-freeze lessons applied: every witness
derives from the SAME basis the mechanism would read, the witnesses are
RELATIONS not constants, and satisfiability is verified on the control before
the relation is frozen):

  TARGET POPULATION (frozen; rule-19 exclusions applied up front). MISO plant
  groups ``CC_REGULAR``, ``CT_PEAKER``, ``ST_GAS``, restricted to non-dual-fuel
  rows with ``pmax > 0``. This is the NEISO group set with EVERY CHP class
  removed — the keeper's armed ``temp_dependent_derate`` is scoped to
  ``['CT_CHP','ST_CHP']`` and the miso-192 CHP steam-host clamp class already
  governs cogen capability, so including them would stack (rule 19) — and with
  ``ST_GAS`` added, MISO's gas-steam fleet being material and carrying no
  temperature-conditioned mechanism. Dual-fuel rows are excluded by the
  mechanism's own design and because the keeper arms ``dual_fuel_switching``,
  which already re-prices them to oil parity.

  BASES (each the exact object the mechanism or its witness would read):
    M (model, armed envelope): the load-bearing build
      ``load_fleet_from_csv → fleet_to_bins → bins_to_fleet →
      generators_to_fleet_arrays(config=<keeper cfg>, iso="MISO", year=Y)``.
      Offline MW at hour t = Σ over target rows of ``pmax·(1 − availability)``.
    P (published, measured): ``data.miso_outages.miso_outage_mw_series(Y,
      region="MISO", cause_types=("Forced","Derated"))`` — MISO's own daily
      Multiday Operating Margin OUTAGE record (``_SOURCE.md``; rule-13
      admissible measured availability, never a price and never an outcome).
      Forced+Derated only: ``Planned`` is not weather-driven and ``Unplanned``
      is a superset that would double-count ``Forced``.
    T (temperature): ``data.eia930.weather.iso_zone_tmax("MISO", Y, 8760,
      zone=z)`` daily TMIN — the SAME loader the armed ``temp_dependent_derate``
      reads — aggregated across model zones weighted by each zone's target-
      population MW.

  W1 RULE-19 EXCLUSIVITY (load-bearing, boolean). Enumerate every mechanism
  armed on the keeper's ``run_config.json`` that writes a TEMPERATURE-
  CONDITIONED availability change onto the target population. PASS iff the
  count is 0. (Measured-window overlays — the CAMPD unit/short/maxgen/layup
  derates, the summer-basis and WEFOR mechanisms — are not temperature-
  conditioned and are reported, not gated; they are W2's subject, not W1's.)
  FAIL ⇒ the lever stacks and is refuted here.

  W2 THE DOUBLE-COUNT TEST (load-bearing; pjm-161 shape, MISO bases). Define,
  for a basis X and year Y, the COLD-RESPONSE RATIO
      R_X(Y) = mean(X over the coldest DECILE of DJF days by T)
             / mean(X over the MILD HALF of DJF days by T).
    W2a (GATED, 2025): the armed model envelope leaves a real gap iff
        R_P(2025) / R_M(2025) ≥ 1.25,
      i.e. basis M reproduces LESS THAN 80% of the published relative cold
      response. RATIOS, never levels: M covers the modeled thermal fleet and P
      covers all MISO capacity of every fuel, so a level comparison is
      basis-misaligned (the miso-141 basis lesson). R_X is reported for 2023
      and 2024 as well; the gate reads 2025, the charter's target year.
    W2b (REPORTED, never gated, against interest either way): Spearman
      corr(daily offline MW, daily T) over DJF for both bases. Basis M with
      corr ≥ 0 while basis P has corr < 0 is the pjm-161 inversion signature.

  W3 POPULATION & SATISFIABILITY (load-bearing).
    W3a: target-population MW ≥ 20% of MISO total gas-class MW on the keeper
      build. Below ⇒ the mechanism cannot be material whatever its curve.
    W3b (satisfiability on the control, verified BEFORE any relation is
      frozen): ``iso_zone_tmax`` must return a non-None TMIN for model zones
      covering ≥ 50% of target-population MW, in ALL of 2023/2024/2025. A
      missing TMIN makes the mechanism a silent no-op and the A/B impossible.

  W4 LP ABSORPTION (load-bearing; "would it move price at all", read from the
  keeper's OWN committed hourly sidecars — zero-solve).
    Onset ``t0`` is MISO-DERIVED, never transferred: the 10th percentile of the
      2023–2025 DJF daily T series of basis T (a distributional definition of
      deep cold). BINDING HOURS = DJF hours with T < t0.
    The removal magnitude is MEASURED, not assumed: cold-excess
      ``E(t) = max(0, P(t) − mean(P over the MILD HALF of DJF days))``, scaled
      to the target population by its share of MISO thermal capacity.
    HEADROOM ``H(t)`` = Σ over target classes of the keeper's own unused
      capability = (Σ target-row ``pmax·availability`` from basis M) − the
      P1 dispatch of those classes in ``hourly/class_hourly_<Y>.parquet``
      (the class sidecar carries dispatch only; this difference is exactly the
      LP's own unused bound).
    FROZEN RELATION: the removal is NOT absorbed at t iff ``E(t) > H(t)``.
      PASS iff that holds in ≥ 25% of 2025 binding hours. Below the line the LP
      absorbs the derate against standing surplus and the lever is inert on
      price whatever its magnitude.

  CHARTER GATE: an LP A/B is chartered iff W1 ∧ W2a ∧ W3a ∧ W3b ∧ W4. ANY
  load-bearing miss ⇒ REFUTE: stamp the MISO ``gas_coldsnap_derate`` cell with
  the citation, write the FINDING, STOP (one lever per session, charter E).

  DIRECTIONAL PREREG (ex ante, with confidence, per the charter): IF chartered,
  the arm raises MISO mean LMP and moves C3a-2025 UP (less negative).
  CONFIDENCE that it delivers ≥ +0.30 pp on annual C3a-2025: **0.35** — stated
  low and against interest, because (a) Jan-2025 carries only −1.43 pp of the
  −12.34 pp miss (FINDING-miso178 §1) and (b) miso-178 §5 measures the model
  already leaving 5+ GW of REAL gas idle in the stress hours, a
  surplus-headroom regime in which removing availability is absorbed rather
  than priced. W4 is the pre-registered test of exactly that failure mode.
  Whatever the sign, it is reported at full magnitude.

  MATERIALITY LINE, declared: a lever that cannot plausibly reach +0.30 pp of
  annual C3a-2025 is not worth a two-leg solve at this frontier (the distance
  to band is +2.34 pp; miso-193's bands carried ~1.0–1.3 pp/yr for comparison).

Rule 21 [R-DOF]: this probe adds ZERO solve inputs and has zero free
parameters; the 1.25× / 20% / 50% / 25% / p10 / decile / mild-half lines are
ex-ante adjudication thresholds of the census, not model parameters. Rule 13
[R-MEASURED]: both measured inputs (the MISO OUTAGE record, the curated MISO
weather series) are physical availability/weather quantities that regenerate
for a forward year and respond to changed conditions; no price, no residual and
no measured outcome enters any witness.

Read-only and idempotent. Output:
``results/calibration/_miso194_coldsnap_derate_phase0.json``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import typing
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia930.weather import iso_zone_tmax  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    dual_fuel_plant_groups,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.miso_outages import miso_outage_mw_series  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
GATE_YEAR = 2025
KEEPER = REPO / "results/calibration/miso191_bax_B"
OUT = REPO / "results/calibration/_miso194_coldsnap_derate_phase0.json"

# Frozen target population (docstring "TARGET POPULATION"): the NEISO group set
# minus every CHP class (temp_dependent_derate is scoped to CT_CHP/ST_CHP on
# this keeper — rule 19) plus ST_GAS.
TARGET_GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
# The full MISO gas class, W3a's denominator.
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
DJF_MONTHS = (12, 1, 2)

# Ex-ante adjudication thresholds (docstring; not solve inputs, rule 21).
W2A_RATIO_LINE = 1.25
W3A_SHARE_LINE = 0.20
W3B_COVER_LINE = 0.50
W4_UNABSORBED_LINE = 0.25
COLD_DECILE = 0.10
MILD_HALF = 0.50


def _hour_month(hours: int = 8760) -> np.ndarray:
    return pd.date_range("2023-01-01", periods=hours, freq="h").month.to_numpy()


def keeper_config(year: int) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config dump."""
    dump = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    hints = typing.get_type_hints(ScenarioConfig)
    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.name not in dump:
            continue
        val = dump[f.name]
        ann = str(hints.get(f.name, ""))
        if val is None:
            out[f.name] = None
        elif "frozenset" in ann and isinstance(val, list):
            out[f.name] = frozenset(val)
        elif "tuple" in ann and isinstance(val, list):
            out[f.name] = tuple(val)
        elif "Path" in ann and isinstance(val, str):
            out[f.name] = Path(val)
        else:
            out[f.name] = val
    out["mode"] = "backcast"
    out["weather_year"] = year
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def build_arrays(year: int):
    """Load the keeper's load-bearing fleet build for ``year``."""
    cfg = keeper_config(year)
    iso_cfg = get_iso_config(ISO)
    gens = load_fleet_from_csv(
        ISO,
        iso_cfg,
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        egrid_identity_heat_rates=bool(
            getattr(cfg, "egrid_identity_heat_rates", False)
        ),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in iso_cfg.zones]
    fa = generators_to_fleet_arrays(
        gens, zones, 8760, iso=ISO, config=cfg, year=year
    )
    return cfg, gens, zones, fa


def target_mask(gens, fa) -> tuple[np.ndarray, np.ndarray]:
    """Return (target_mask, gas_mask) over the fleet rows, dual-fuel excluded."""
    groups = np.array([str(getattr(g, "plant_group", "")) for g in gens])
    codes = np.array([int(getattr(g, "plant_code", -1)) for g in gens])
    dual = dual_fuel_plant_groups()
    is_dual = np.array(
        [(int(codes[i]), str(groups[i])) in dual for i in range(groups.size)],
        dtype=bool,
    )
    gas = np.isin(groups, np.asarray(GAS_GROUPS)) & (fa.pmax > 0.0)
    tgt = np.isin(groups, np.asarray(TARGET_GROUPS)) & (fa.pmax > 0.0) & ~is_dual
    return tgt, gas


def temp_series(year: int, gens, fa, tgt: np.ndarray) -> dict:
    """Basis T: target-MW-weighted daily TMIN across model zones (W3b too)."""
    iso_cfg = get_iso_config(ISO)
    zones = [z.name for z in iso_cfg.zones]
    zone_of = np.array([str(getattr(g, "zone", "")) for g in gens])
    per_zone = {}
    covered_mw = 0.0
    total_mw = float(fa.pmax[tgt].sum())
    for z in zones:
        mw = float(fa.pmax[tgt & (zone_of == z)].sum())
        pair = iso_zone_tmax(ISO, year, 8760, zone=z)
        tmin = None if pair is None else pair[1]
        if tmin is not None and np.isfinite(tmin).any():
            per_zone[z] = (mw, np.asarray(tmin, dtype=float))
            covered_mw += mw
    if not per_zone:
        return {"ok": False, "cover_share": 0.0, "series": None, "zones": {}}
    wsum = sum(mw for mw, _ in per_zone.values())
    if wsum <= 0:
        series = np.mean([s for _, s in per_zone.values()], axis=0)
    else:
        series = sum(mw * s for mw, s in per_zone.values()) / wsum
    return {
        "ok": covered_mw >= W3B_COVER_LINE * total_mw and total_mw > 0,
        "cover_share": covered_mw / total_mw if total_mw > 0 else 0.0,
        "series": series,
        "zones": {z: round(mw, 1) for z, (mw, _) in per_zone.items()},
    }


def _daily(x: np.ndarray) -> np.ndarray:
    """Collapse an 8760 hourly series to 365 daily means."""
    return np.asarray(x, dtype=float).reshape(365, 24).mean(axis=1)


def cold_response(daily_x: np.ndarray, daily_t: np.ndarray, djf: np.ndarray) -> dict:
    """R_X = mean(X | coldest decile of DJF days) / mean(X | mild half)."""
    t = daily_t[djf]
    x = daily_x[djf]
    order = np.argsort(t)
    n = t.size
    k = max(1, int(round(COLD_DECILE * n)))
    cold = order[:k]
    mild = order[int(round((1.0 - MILD_HALF) * n)) :]
    m_cold = float(np.mean(x[cold]))
    m_mild = float(np.mean(x[mild]))
    return {
        "n_djf_days": int(n),
        "n_cold": int(k),
        "n_mild": int(mild.size),
        "cold_mean": m_cold,
        "mild_mean": m_mild,
        "ratio": (m_cold / m_mild) if m_mild > 0 else float("nan"),
        "cold_t_max_c": float(np.max(t[cold])),
        "mild_t_min_c": float(np.min(t[mild])),
    }


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def w1_exclusivity(cfg: ScenarioConfig) -> dict:
    """W1: armed temperature-conditioned availability mechanisms on the target.

    Enumerated from the keeper's own config; each entry records why it does or
    does not write a temperature-conditioned availability change onto
    TARGET_GROUPS.
    """
    rows = []

    def add(field, armed, temp_keyed, hits_target, why):
        rows.append(
            {
                "field": field,
                "armed": bool(armed),
                "temperature_conditioned": bool(temp_keyed),
                "writes_target_population": bool(hits_target),
                "why": why,
            }
        )

    tdd = bool(getattr(cfg, "temp_dependent_derate", False))
    scope = getattr(cfg, "temp_derate_classes", None)
    scope_list = list(scope) if scope else []
    tdd_hits = tdd and (
        not scope_list or bool(set(scope_list) & set(TARGET_GROUPS))
    )
    add(
        "temp_dependent_derate",
        tdd,
        True,
        tdd_hits,
        f"armed but scoped to temp_derate_classes={scope_list!r}; "
        f"target groups {list(TARGET_GROUPS)} "
        + ("INTERSECT the scope" if tdd_hits else "are OUTSIDE the scope"),
    )
    cfo = bool(getattr(cfg, "correlated_forced_outage", False))
    add(
        "correlated_forced_outage",
        cfo,
        True,
        cfo
        and str(getattr(cfg, "mode", "")) == "forecast"
        and str(getattr(cfg, "outage_source", "")) != "historic",
        "the documented cold-event derate; apply_correlated_outage_derate "
        f"refuses on mode={getattr(cfg, 'mode', None)!r} and "
        f"outage_source={getattr(cfg, 'outage_source', None)!r} (FF-1B D.5)",
    )
    add(
        "gt_ambient_derate",
        bool(getattr(cfg, "gt_ambient_derate", False)),
        True,
        bool(getattr(cfg, "gt_ambient_derate", False)),
        "hot-ambient GT derate (miso-90 inert); reported",
    )
    add(
        "neiso_gas_coldsnap_derate",
        bool(getattr(cfg, "neiso_gas_coldsnap_derate", False)),
        True,
        False,
        "NEISO-gated in inject_neiso_gas_coldsnap_derate (iso != NEISO -> False)",
    )
    for f, why in (
        ("outage_source", "measured CAMPD window overlay — not temperature-keyed"),
        ("unit_outage_short_windows", "measured CAMPD short windows — not temp-keyed"),
        ("unit_outage_maxgen_events", "measured max-gen events — not temp-keyed"),
        (
            "unit_outage_fleet_status_scope",
            "measured fleet-status scoping — not temp-keyed",
        ),
        ("mustrun_layup_window_mask", "measured layup window — not temp-keyed"),
        ("summer_derate_basis_aware", "SUMMER capability basis — not a winter path"),
        ("summer_wefor_share_override", "SUMMER WEFOR share — not a winter path"),
        ("gas_st_wefor_base_override", "flat WEFOR base — not temp-keyed"),
        ("dual_fuel_switching", "re-prices dual-fuel rows; excluded from target"),
    ):
        v = getattr(cfg, f, None)
        add(f, bool(v) if not isinstance(v, str) else True, False, False, why)

    violations = [r for r in rows if r["temperature_conditioned"] and r["writes_target_population"]]
    return {
        "rows": rows,
        "n_violations": len(violations),
        "violations": [r["field"] for r in violations],
        "pass": len(violations) == 0,
    }


def w5_reported_reach_ceiling(binding_h, dt, t0) -> dict:
    """REPORTED-ONLY reach ceiling. ADDED POST-VERDICT — disclosed, never gated.

    The frozen W1-W4 gate above resolved before this function existed; nothing
    here can change it. It exists to bound the WHOLE winter-lever family for the
    queue, in the scorer's own basis: C3a reads the LOAD-WEIGHTED model mean
    against the bench ``rt_lw`` (calibration_verdict.py:1675), so a uniform
    +$1/MWh applied to every binding hour moves C3a-2025 by
    (Σ_binding demand / Σ_year demand) / rt_lw x 100 pp.
    """
    import gzip

    sysdf = pd.read_parquet(KEEPER / "hourly" / f"system_{GATE_YEAR}.parquet")
    if "pass" in sysdf:
        sysdf = sysdf[sysdf["pass"].astype(str).str.upper() == "P1"]
    dem = sysdf.pivot_table(
        index="hour", columns="zone", values="demand", aggfunc="sum"
    ).reindex(range(8760)).fillna(0.0).to_numpy().sum(axis=1)
    prc = sysdf.pivot_table(
        index="hour", columns="zone", values="price", aggfunc="mean"
    ).reindex(range(8760)).fillna(0.0).to_numpy().mean(axis=1)
    bench = json.loads(
        gzip.open(
            REPO / "frontend/data/backcast/bench/MISO" / f"{GATE_YEAR}.json.gz"
        ).read()
    )["bench"]["avgLMP"]
    rt_lw = float(bench["rt_lw"])
    w = float(dem[binding_h].sum()) / float(dem.sum())
    pp_per_dollar = w / rt_lw * 100.0
    model_lw = float((prc * dem).sum() / dem.sum())
    jan = np.zeros(8760, dtype=bool)
    jan[: 31 * 24] = True
    return {
        "disclosure": "added after the frozen W1-W4 gate resolved; reported only",
        "n_binding_hours": int(binding_h.sum()),
        "binding_share_of_hours": float(binding_h.mean()),
        "binding_share_of_annual_demand": w,
        "bench_rt_lw": rt_lw,
        "model_lw_mean_annual": model_lw,
        "model_mean_price_binding_hours": float(prc[binding_h].mean()),
        "model_mean_price_jan": float(prc[jan].mean()),
        "bench_rt_lw_mon_jan": float(bench["rt_lw_mon"][0]),
        "pp_C3a_per_dollar_across_binding_hours": pp_per_dollar,
        "dollars_needed_for_0p30pp": 0.30 / pp_per_dollar,
        "dollars_needed_for_band_2p34pp": 2.34 / pp_per_dollar,
    }


def w6_reported_netload_inversion(offline_by_year: dict) -> dict:
    """REPORTED-ONLY: the pjm-161 NET-LOAD inversion quantity. POST-VERDICT.

    W2 asked whether the armed envelope tracks TEMPERATURE (the winter object
    this session chartered). pjm-161's original quantity is corr(derated MW,
    NET LOAD) — whether the envelope hands the LP the most capacity in the
    TIGHTEST hours, which is a year-round question and lands on the summer
    target that owns 60% of C3a-2025 (miso-178 §1: Jun -3.28 + Jul -3.69 pp).
    Reported so the queue inherits the measurement; NEVER gated, and it stamps
    no cell — the outage-envelope rows are a different object this session did
    not test.
    """
    out = {
        "disclosure": (
            "added after the frozen W1-W4 gate resolved; reported only; "
            "stamps no cell"
        )
    }
    for year, offline in offline_by_year.items():
        sysdf = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        if "pass" in sysdf:
            sysdf = sysdf[sysdf["pass"].astype(str).str.upper() == "P1"]
        dem = sysdf.pivot_table(
            index="hour", columns="zone", values="demand", aggfunc="sum"
        ).reindex(range(8760)).fillna(0.0).to_numpy().sum(axis=1)
        dfh = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        if "pass" in dfh:
            dfh = dfh[dfh["pass"].astype(str).str.upper() == "P1"]
        piv = dfh.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).reindex(range(8760)).fillna(0.0)
        vre = sum(
            piv[c].to_numpy() for c in ("wind", "solar") if c in piv.columns
        )
        netload = dem - vre
        off = np.asarray(offline, dtype=float)
        top1 = netload >= np.quantile(netload, 0.99)
        out[str(year)] = {
            "spearman_offline_vs_netload": _spearman(off, netload),
            "annual_mean_offline_mw": float(off.mean()),
            "top1pct_netload_mean_offline_mw": float(off[top1].mean()),
            "top1pct_over_annual_ratio": float(off[top1].mean() / off.mean())
            if off.mean() > 0
            else float("nan"),
        }
    return out


def main() -> dict:
    rec: dict = {
        "probe": "miso-194 phase-0 cold-snap gas derate census",
        "keeper": "2026-08-30-miso-191-bexit",
        "bundle": str(KEEPER.relative_to(REPO)),
        "chartered_mechanism": "gas_coldsnap_derate",
        "not_chartered": "winter_fuelsec_posture (stays U)",
        "target_groups": list(TARGET_GROUPS),
        "years": list(YEARS),
        "gate_year": GATE_YEAR,
        "thresholds": {
            "W2a_ratio_line": W2A_RATIO_LINE,
            "W3a_share_line": W3A_SHARE_LINE,
            "W3b_cover_line": W3B_COVER_LINE,
            "W4_unabsorbed_line": W4_UNABSORBED_LINE,
        },
        "per_year": {},
    }

    mon = _hour_month()
    djf_h = np.isin(mon, DJF_MONTHS)
    djf_d = _daily(djf_h.astype(float)) > 0.5

    t_pool = []
    for year in YEARS:
        cfg, gens, zones, fa = build_arrays(year)
        tgt, gas = target_mask(gens, fa)
        tgt_mw = float(fa.pmax[tgt].sum())
        gas_mw = float(fa.pmax[gas].sum())

        T = temp_series(year, gens, fa, tgt)
        y: dict = {
            "target_mw": round(tgt_mw, 1),
            "gas_class_mw": round(gas_mw, 1),
            "target_share_of_gas": (tgt_mw / gas_mw) if gas_mw > 0 else 0.0,
            "n_target_rows": int(tgt.sum()),
            "w3b_zone_cover_share": T["cover_share"],
            "w3b_zones": T["zones"],
            "w3b_ok": bool(T["ok"]),
        }

        # Basis M: armed model offline MW on the target population.
        offline_m = (fa.pmax[tgt][:, None] * (1.0 - fa.availability[tgt])).sum(axis=0)
        cap_m = (fa.pmax[tgt][:, None] * fa.availability[tgt]).sum(axis=0)
        # Basis P: MISO's published Forced+Derated offline MW.
        offline_p = miso_outage_mw_series(
            year, region="MISO", cause_types=("Forced", "Derated")
        )
        y["published_record_present"] = bool(np.any(np.asarray(offline_p) > 0))

        if T["series"] is not None:
            dt = _daily(T["series"])
            t_pool.append(dt[djf_d])
            dm = _daily(offline_m)
            dp = _daily(np.asarray(offline_p, dtype=float))
            y["R_M"] = cold_response(dm, dt, djf_d)
            y["R_P"] = cold_response(dp, dt, djf_d)
            rm = y["R_M"]["ratio"]
            rp = y["R_P"]["ratio"]
            y["w2a_gap_ratio"] = (rp / rm) if rm and np.isfinite(rm) and rm > 0 else float("nan")
            y["w2b_spearman_model_vs_T"] = _spearman(dm[djf_d], dt[djf_d])
            y["w2b_spearman_published_vs_T"] = _spearman(dp[djf_d], dt[djf_d])
            y["_dt"] = dt
            y["_dm"] = dm
            y["_dp"] = dp
            y["_cap_m"] = cap_m
        y["_offline_m"] = offline_m
        rec["per_year"][str(year)] = y

        if year == GATE_YEAR:
            rec["w1"] = w1_exclusivity(cfg)
            rec["_gate_gens"] = None

    # W4 uses the pooled 2023-25 DJF T distribution for the MISO-derived onset.
    pooled = np.concatenate(t_pool) if t_pool else np.array([])
    t0 = float(np.quantile(pooled, COLD_DECILE)) if pooled.size else float("nan")
    rec["w4_t0_c_miso_derived"] = t0

    g = rec["per_year"][str(GATE_YEAR)]
    w4: dict = {"t0_c": t0}
    if "_dt" in g:
        dt, dp, cap_m = g["_dt"], g["_dp"], g["_cap_m"]
        # Mild-half baseline of the published record, DJF.
        mild_ref = g["R_P"]["mild_mean"]
        excess_d = np.maximum(0.0, dp - mild_ref)
        # Scale the system-wide published excess to the target population by its
        # share of MISO thermal capacity (the same aggregate-to-population step
        # miso_outages documents for its own envelope).
        cfg_g, gens_g, _, fa_g = build_arrays(GATE_YEAR)
        tgt_g, _ = target_mask(gens_g, fa_g)
        groups_g = np.array([str(getattr(x, "plant_group", "")) for x in gens_g])
        thermal = np.isin(
            groups_g,
            np.asarray(list(GAS_GROUPS) + ["COAL", "NUCLEAR", "OIL", "BIOMASS"]),
        ) & (fa_g.pmax > 0.0)
        share = float(fa_g.pmax[tgt_g].sum()) / float(fa_g.pmax[thermal].sum())
        w4["target_share_of_thermal"] = share

        # Hourly binding set: DJF hours whose day-mean T is below t0.
        cold_day = dt < t0
        binding_h = djf_h & np.repeat(cold_day, 24)
        E_h = np.repeat(excess_d * share, 24)

        # Headroom: target-class LP bound minus the keeper's own P1 dispatch.
        dfh = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{GATE_YEAR}.parquet")
        if "pass" in dfh:
            dfh = dfh[dfh["pass"].astype(str).str.upper() == "P1"]
        piv = dfh.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        piv = piv.reindex(range(8760)).fillna(0.0)
        missing = [c for c in TARGET_GROUPS if c not in piv.columns]
        w4["sidecar_classes_missing"] = missing
        assert not missing, f"target class absent from sidecar: {missing}"
        disp = piv[list(TARGET_GROUPS)].to_numpy().sum(axis=1)
        H = np.maximum(0.0, cap_m - disp)

        nb = int(binding_h.sum())
        unabs = int(np.sum(E_h[binding_h] > H[binding_h])) if nb else 0
        w4.update(
            {
                "n_binding_hours": nb,
                "n_unabsorbed": unabs,
                "unabsorbed_share": (unabs / nb) if nb else 0.0,
                "median_E_mw": float(np.median(E_h[binding_h])) if nb else 0.0,
                "median_H_mw": float(np.median(H[binding_h])) if nb else 0.0,
                "median_headroom_all_djf_mw": float(np.median(H[djf_h])),
                "pass": (unabs / nb if nb else 0.0) >= W4_UNABSORBED_LINE,
            }
        )
        w4["_binding_h"] = binding_h
        w4["_dt"] = dt
    rec["w4"] = w4
    bh = w4.pop("_binding_h", None)
    _dtv = w4.pop("_dt", None)
    rec["w5_reported"] = (
        w5_reported_reach_ceiling(bh, _dtv, t0) if bh is not None else {}
    )

    rec["w6_reported"] = w6_reported_netload_inversion(
        {y: rec["per_year"][str(y)]["_offline_m"] for y in YEARS}
    )

    # Verdicts.
    w2a = g.get("w2a_gap_ratio", float("nan"))
    verdict = {
        "W1_rule19_exclusivity": bool(rec.get("w1", {}).get("pass", False)),
        "W2a_double_count_gap": bool(np.isfinite(w2a) and w2a >= W2A_RATIO_LINE),
        "W3a_population": bool(g["target_share_of_gas"] >= W3A_SHARE_LINE),
        "W3b_satisfiability": all(
            bool(rec["per_year"][str(y)]["w3b_ok"]) for y in YEARS
        ),
        "W4_lp_absorption": bool(w4.get("pass", False)),
    }
    verdict["CHARTER_AB"] = all(verdict.values())
    rec["verdict"] = verdict

    # Strip the bulky intermediates before serializing.
    for y in rec["per_year"].values():
        for k in ("_dt", "_dm", "_dp", "_cap_m", "_offline_m"):
            y.pop(k, None)
    rec.pop("_gate_gens", None)

    OUT.write_text(json.dumps(rec, indent=2, default=float))
    return rec


if __name__ == "__main__":
    r = main()
    v = r["verdict"]
    print(json.dumps({"verdict": v, "w4": r["w4"]}, indent=2, default=float))
    for y in r["years"]:
        s = r["per_year"][str(y)]
        print(
            f"{y}: target {s['target_mw']:.0f} MW "
            f"({s['target_share_of_gas']:.1%} of gas) "
            f"R_M={s.get('R_M', {}).get('ratio', float('nan')):.3f} "
            f"R_P={s.get('R_P', {}).get('ratio', float('nan')):.3f} "
            f"gap={s.get('w2a_gap_ratio', float('nan')):.3f} "
            f"rho_M={s.get('w2b_spearman_model_vs_T', float('nan')):+.3f} "
            f"rho_P={s.get('w2b_spearman_published_vs_T', float('nan')):+.3f}"
        )
