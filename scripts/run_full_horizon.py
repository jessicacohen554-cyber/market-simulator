#!/usr/bin/env python
"""Full-horizon forecast runner + feasibility instrumentation (P-3A, plan §2 G1).

Runs one ISO's *reference* forecast across the full 2026-2050 horizon (the
horizon that, per the forecast-driver audit plan §2 testing-audit G1, has never
been solved end-to-end), captures per-year wall time and peak RSS, then scores
the I1-I14 forecast invariants over the completed run. It writes a single
``full_horizon_summary.json`` beside the cached run so the six per-ISO
invocations can be collated into one findings report.

This is a *forecast probe*: ``mode="forecast"``, every ScenarioConfig field at
its default (so ``use_campd_bins=True`` gives each ISO its own per-plant CAMPD
bins where an artifact exists — the ISO default), plus the two P-3A pins:

  * ``capacity_market_clearing=False`` — the P-2A recommendation (the flip is
    unvalidated; NOT an A/B this pass).
  * ``start_year``/``end_year`` = the requested window (default 2026-2050).

Nothing here tunes anything or changes a threshold (findings only, rules
1/11/14). It solves years sequentially inside one invocation (rule 12); the
caller runs at most two ISO invocations concurrently, each with its own
``--out-dir``.

PREREQUISITE — ``data/clean`` MUST EXIST (FFR-3A blocker 1, documented FFR-3D).
``data/clean`` is derived and gitignored, so a fresh container has none of it,
and this runner does NOT degrade gracefully without it: the confirmed-exits
loader REFUSES ("clean partition for <ISO> is absent while
confirmed_exits_enabled is on in forecast mode … refusing to silently degrade
to the economic screen") and the leg aborts at fleet build. Building it costs
**≈ 55 min / 50 datatypes / ≈ 1.6 GB** — budget it into the FIRST leg in a
container (one-time per container, not per leg); the wall-clock anchors in
``docs/forecast-development-plan-2026-07.md`` §2.4 all assume it is already
built. A PARTIAL tree is the trap: "the directory exists" is not the check::

    PYTHONPATH=. python scripts/regenerate_clean.py          # all datatypes
    PYTHONPATH=. python scripts/regenerate_clean.py --list   # what would be built

Memory: per-plant multi-zone forecast years are RAM-heavy and OOM without a
glibc arena cap (precedent: the NEISO/PJM/MISO per-plant probes). Launch with
``MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`` when running
two concurrently on a small box.

Usage::

    MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
        python scripts/run_full_horizon.py --iso ERCOT \
        --out-dir results/full-horizon/ercot 2>&1 | tee results/full-horizon/ercot.log
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.capacity_market import (  # noqa: E402
    resolve_capacity_market_clearing,
)
from market_sim.config.iso_configs import (  # noqa: E402
    apply_iso_scenario_defaults,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache as cachemod  # noqa: E402
from scripts.golden_forecast_bands import WEATHER_POSTURE  # noqa: E402
from scripts import check_forecast_invariants as C  # noqa: E402
from scripts.lib.forecast_posture import (  # noqa: E402
    shipped_capacity_clearing_by_iso,
    shipped_forecast_xyear_warmstart,
)
from market_sim.config.schedulable import (  # noqa: E402,F401  (re-export)
    MAX_UNAUTHORIZED_SOLVE_YEARS,
    assert_schedulable,
)
from scripts.lib.run_record import (  # noqa: E402
    Derived,
    FromConfig,
    RecordSpec,
    write_run_config,
)

#: The ``full_horizon_summary.json`` config-describing block (FFR-3R). Every
#: key here is read off the ScenarioConfig the solve ran on; a new
#: ScenarioConfig field cannot be summarized from ``args`` (or from a literal)
#: without being declared. The summary is the input to
#: ``register_forecast_baseline.build_sidecar`` and, through it, to the FF-2D
#: verdict machinery, so a wrong value here is a wrong published classification
#: — that is what FFR-2E found when the clearing gate was flag-sourced.
SUMMARY_RECORD_SPEC = RecordSpec(
    {
        "iso": FromConfig(),
        "start_year": FromConfig(),
        "end_year": FromConfig(),
        # The RESOLVED per-ISO clearing gate, not the scalar flag: under
        # --golden-posture the scalar stays False while
        # capacity_market_clearing_by_iso carries the curve-ON ISOs, and
        # forecast_verdict._curve_on reads this key — so a flag-sourced value
        # recorded every curve-ON T1-F leg as curve-OFF (FFR-2E / audit FR-14).
        "capacity_market_clearing": Derived(
            lambda cfg, ctx: bool(resolve_capacity_market_clearing(cfg, ctx["iso"])),
            "the RESOLVED per-ISO gate (FFR-2E), not the scalar field",
        ),
        # Normalized to None when empty so an absent posture reads as absent
        # rather than as an empty dict.
        "capacity_market_clearing_by_iso": Derived(
            lambda cfg, ctx: (
                dict(cfg.capacity_market_clearing_by_iso)
                if cfg.capacity_market_clearing_by_iso
                else None
            ),
            "empty/None normalized to null",
        ),
        "weather_year": FromConfig(),
        # The two MISO row-family gates, read off the RESOLVED config rather
        # than the CLI args — MISO's ISOConfig.default_scenario_overrides arms
        # miso_rps_compliance_regions (owner D-26) for a leg that passes no
        # flag at all, so an args-sourced value would record the standing
        # forecast posture as unarmed. Same FFR-2E/FFR-3R defect class as the
        # flag-sourced clearing gate: a sidecar must REPORT the posture it
        # solved, not assert one. Declared here so a paired arm/control
        # registration is self-describing on the dashboard (ARM3-MEASURE,
        # docs/handoffs/arm3-clean-row-horizon-2026-08-09.md).
        "miso_rps_compliance_regions": Derived(
            lambda cfg, ctx: bool(
                apply_iso_scenario_defaults(cfg, ctx["iso"]).miso_rps_compliance_regions
            ),
            "the RESOLVED posture after ISO default_scenario_overrides",
        ),
        "miso_clean_tier_rows": Derived(
            lambda cfg, ctx: bool(
                apply_iso_scenario_defaults(cfg, ctx["iso"]).miso_clean_tier_rows
            ),
            "the RESOLVED posture after ISO default_scenario_overrides",
        ),
    },
    name="full_horizon_summary.json",
)


# --------------------------------------------------------------------------- #
# RSS sampling + per-year timing
# --------------------------------------------------------------------------- #
def _read_rss_mb() -> float:
    """Current process resident set size in MB, from /proc/self/status."""
    try:
        with open("/proc/self/status", "r") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0  # kB -> MB
    except OSError:
        pass
    return 0.0


class Sampler:
    """Background RSS sampler: records (monotonic_time, rss_mb) every interval."""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.samples: list[tuple[float, float]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.samples.append((time.monotonic(), _read_rss_mb()))
            self._stop.wait(self.interval)

    def start(self) -> None:
        self.samples.append((time.monotonic(), _read_rss_mb()))
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        self.samples.append((time.monotonic(), _read_rss_mb()))

    def peak_between(self, t0: float, t1: float) -> float:
        vals = [rss for (t, rss) in self.samples if t0 < t <= t1]
        return max(vals) if vals else 0.0

    @property
    def global_peak(self) -> float:
        return max((rss for (_, rss) in self.samples), default=0.0)


# --------------------------------------------------------------------------- #
# Reference forecast config
# --------------------------------------------------------------------------- #
# The §2.1b window cap now lives in market_sim/config/schedulable.py so EVERY
# schedulable entry point shares one implementation (FFR-1D / audit FR-25 — it
# used to be reachable from this runner and run_ces_leg.py only). Re-exported
# here because run_ces_leg.py and tests/scoring/test_ff_readiness_battery.py
# import it from this module.


def reference_config(
    iso: str,
    start_year: int,
    end_year: int,
    cmc: bool,
    golden_posture: bool = False,
    transmission_expansion: bool = False,
    retirement_rule: "str | None" = None,
    entry_vre_capacity_revenue: "bool | None" = None,
    entry_rate_limits: "bool | None" = None,
    entry_commissioning_lag: "bool | None" = None,
    electrification_path: str = "off",
    entry_screen_diagnostics: bool = False,
    caiso_nqc_accreditation: bool = False,
    caiso_storage_nqc_accreditation: bool = False,
    caiso_ra_mpb_capacity_anchor: bool = False,
    miso_rps_compliance_regions: "bool | None" = None,
    miso_clean_tier_rows: "bool | None" = None,
) -> ScenarioConfig:
    """The P-3A reference forecast: all defaults, forecast mode, P-2A pins.

    Every field except mode/iso/horizon/capacity_market_clearing (and the
    optional FF-G1 ``transmission_expansion_enabled`` probe gate) is left at the
    ScenarioConfig default, so ``use_campd_bins=True`` yields each ISO's own
    per-plant CAMPD bins where an artifact exists (the ISO default). The FF-1F /
    FF-2A default flips (``datacenter_load_path="mid"``,
    ``correlated_forced_outage=True``, ``entry_lookahead_reprice=True``) are the
    ScenarioConfig defaults and therefore already active here (plan §2.1a c/d/e).

    ``golden_posture`` (FF-3E) carries §2.1a decision (a), the per-ISO
    capacity-market clearing gate, through ``capacity_market_clearing_by_iso``
    (the FF-2C per-ISO seam). Since owner decision **C.4(a) B1** (signed
    2026-08-03) it reads the SHIPPED ``ScenarioConfig`` field via
    ``scripts.lib.forecast_posture`` — the ONE reader — instead of the parallel
    ``GOLDEN_CMC_BY_ISO`` constant, which is DELETED (rule 26).

    **This changes what a --golden-posture NYISO leg solves.** The deleted
    constant carried ``NYISO: True``; the shipped field deliberately omits
    NYISO ("excluded pending re-calibration"), so it resolves curve-**OFF**.
    Every prior --golden-posture NYISO leg therefore solved a curve-ON posture
    production does not run — audit FR-14 in the T1-F lane, and the signature
    states the correction explicitly: "NYISO must resolve curve-OFF, matching
    production." Every other ISO's resolved gate is unchanged.

    Default ``False`` stays byte-identical to the P-3A probe (the field stays
    ``None``). With it True the value is now identical to the inherited
    default — which is the point of C.4(a): golden posture and shipped posture
    are one answer, not two. It remains explicit so the run's config records
    the posture it ran.

    ``entry_screen_diagnostics`` (RC-0C / BLK-8, FFR-3H) arms the per-candidate
    entry-screen decomposition sink that ``run_capacity_hindcast.py`` has always
    exposed and this runner did not, so a forecast leg could not answer *which
    revenue term starves the economic entry screen* without one. It is a pure
    observability gate — nothing reads it back, so the fleet outcome is
    identical with it on or off (``ScenarioConfig.entry_screen_diagnostics``
    docstring) — but it is NOT in ``_CACHE_KEY_OPTIONAL_FIELDS``, so an armed
    leg takes its own cache key and must be paired with an un-armed arm when the
    recorded key matters. Default ``False`` = byte-identical.

    ``caiso_nqc_accreditation`` (FFR-3P) arms CAISO's OWN published
    class-average VRE accreditation (the CPUC/CAISO Net Qualifying Capacity
    technology factors) in place of the generic non-CAISO 0.18/0.16 fallback.
    Unlike the diagnostics gate this DOES change the solve — it raises the
    accredited-firm ledger, so the adequacy backstop and the retirement
    reliability floor both see a different gap — and it is registered in
    ``_CACHE_KEY_OPTIONAL_FIELDS`` at ``False``, so an unarmed leg keeps its
    historical key and an armed leg keys distinctly. Default ``False``: the
    arming posture is an OWNER decision, not this runner's.

    ``miso_rps_compliance_regions`` (FFR-7B Arm 2 / FFR-6B E-1) replaces
    MISO's single ISO-wide RPS row with K per-state compliance-region rows
    (MISO only, forecast-mode; no-op in every other ISO, rule 25). It is
    registered in ``_CACHE_KEY_OPTIONAL_FIELDS`` at ``False``, so an unarmed
    leg keeps its historical key and an armed leg keys distinctly. Default
    ``None`` = NOT PASSED: the arming posture is an OWNER decision (D-26,
    carried by MISO's ``default_scenario_overrides``), not this runner's.

    ``miso_clean_tier_rows`` (FFR-7B Arm 3 / FFR-6B E-2) adds the MN
    carbon-free + MI clean tier row family on the Arm-2 machinery (REQUIRES
    ``miso_rps_compliance_regions`` — the runner fails loud otherwise).
    Registered cache-optional at ``False``; default ``None`` = NOT PASSED.
    **ARMED FOR THE MISO FORECAST LANE**
    by owner decision D-29 (2026-08-11) through
    ``ISOConfig.default_scenario_overrides``, so a MISO leg that passes no flag
    still SOLVES the clean family — read the posture off the RESOLVED config
    (``apply_iso_scenario_defaults``), never off ``args``, which is why both MISO
    row-family gates are ``Derived`` in the sidecar spec above.
    """
    cmc_by_iso = None
    if golden_posture:
        cmc_by_iso = shipped_capacity_clearing_by_iso()
    # D-1 / D-2 arms (audit FR-4 / FR-5). ``None`` means INHERIT THE SHIPPED
    # ScenarioConfig DEFAULT — the field is simply not passed. FFR-2B wrote
    # these as literal "legacy"/False mirrors of the then-shipped defaults, with
    # the note "the flips are the owner's, executed at FFR-3A step 0". This IS
    # that step: the owner signed D-1 (retirement_rule -> "pipeline") and D-2
    # (both entry dampers -> True) on 2026-08-02, and a mirrored literal here
    # would have silently overridden both flips, making the signed decisions
    # inert in exactly the T1-F legs launched through this runner. Reading the
    # live default instead of mirroring it is the FFR-2E instrument pattern
    # (ffr-2e-shipped-capacity-posture-2026-08-02.md §3(3)) and keeps
    # ScenarioConfig the single source of truth for a default (rule 24).
    arms = {
        "retirement_rule": retirement_rule,
        "entry_vre_capacity_revenue": entry_vre_capacity_revenue,
        "entry_rate_limits": entry_rate_limits,
        "entry_commissioning_lag": entry_commissioning_lag,
        # OVERRIDE-FIX 2026-08-13: these two joined the None-sentinel set the
        # moment ``apply_iso_scenario_defaults`` learned to honour an explicit
        # default-valued argument. They were mirrored literals (``= False``)
        # forwarded unconditionally, which the pre-fix seam silently re-armed
        # for MISO; post-fix that literal WINS and would have made owner
        # decision D-29 (and D-26's Arm-2 row grain) inert in exactly the T1-F
        # legs this runner launches — the FFR-3A step-0 hazard the comment
        # above describes, in its own mirror image. ``None`` = not passed =
        # inherit the ISO/ScenarioConfig posture.
        "miso_rps_compliance_regions": miso_rps_compliance_regions,
        "miso_clean_tier_rows": miso_clean_tier_rows,
    }
    return ScenarioConfig(
        iso=iso.upper(),
        mode="forecast",
        start_year=start_year,
        end_year=end_year,
        capacity_market_clearing=cmc,
        capacity_market_clearing_by_iso=cmc_by_iso,
        transmission_expansion_enabled=transmission_expansion,
        # FF-G4 probe arm (audit FR-16, owner box §8-D2 pending): the
        # electrification end-use layers stay at the shipped default "off"
        # unless a T0/T1 probe arms them explicitly — no default moves here.
        # NOTE (FFR-3A): this is the same mirrored-literal shape the four arms
        # below just moved OFF of. It is left alone deliberately — §8-D2 is
        # UNSIGNED, so there is no flip for it to override yet. If the owner
        # ever signs an electrification default, this line must become a
        # None-sentinel too or it will silently override that signature.
        electrification_path=electrification_path,
        entry_screen_diagnostics=entry_screen_diagnostics,
        caiso_nqc_accreditation=caiso_nqc_accreditation,
        caiso_storage_nqc_accreditation=caiso_storage_nqc_accreditation,
        caiso_ra_mpb_capacity_anchor=caiso_ra_mpb_capacity_anchor,
        # Owner decision D-10 (2026-08-04, sitting Addendum K.3): forecast
        # bundles run cross-year warm start OFF, so a killed-and-resumed
        # forecast reproduces from its own cache. Passed explicitly — and
        # therefore non-default — which is what gives every T1-F leg a cache
        # key distinct from its warm predecessor rather than colliding with it
        # (FFR-3T; scenarios.FORECAST_BUNDLE_XYEAR_WARMSTART carries the
        # measurement).
        forecast_xyear_warmstart=shipped_forecast_xyear_warmstart(),
        **{k: v for k, v in arms.items() if v is not None},
    )


# --------------------------------------------------------------------------- #
# Trajectory extraction (findings only — reconstructs, never tunes)
# --------------------------------------------------------------------------- #
SCARCITY_THRESHOLDS = (100.0, 500.0, 1000.0, 2000.0)


def _co2_tons(yd: "C.YearData") -> float | None:
    """Annual CO2 tons; reconstruct from context rate when the array is absent.

    The forecast path's DispatchResult carries no populated ``emissions`` array
    (a downstream/backcast step), so mirror golden_forecast_bands: dispatch ×
    the fleet context's per-generator emission rate (tCO2/MWh).
    """
    direct = C._annual_co2_tons(yd)
    if direct is not None:
        return direct
    if (
        yd.context is not None
        and getattr(yd.context, "emission_rate", None) is not None
    ):
        rate = np.asarray(yd.context.emission_rate, dtype=float)
        gen_mwh = np.asarray(yd.result.dispatch, dtype=float).sum(axis=1)
        if rate.shape == gen_mwh.shape:
            return float((gen_mwh * rate).sum())
    return None


def _system_hourly_price(yd: "C.YearData") -> np.ndarray:
    """Load-weighted system price per hour (falls back to zone mean)."""
    p = np.asarray(yd.result.prices, dtype=float)  # (n_zones, T)
    if yd.demand is not None:
        d = np.asarray(yd.demand, dtype=float)  # (n_zones, T)
        den = d.sum(axis=0)
        den = np.where(den > 0, den, 1.0)
        return (p * d).sum(axis=0) / den
    return p.mean(axis=0)


def _capacity_by_fuel(yd: "C.YearData") -> dict[str, float]:
    ctx = yd.context
    out: dict[str, float] = {}
    if ctx is None:
        return out
    for fuel, mw in zip(ctx.fuel_types, ctx.pmax_mw):
        out[fuel] = out.get(fuel, 0.0) + float(mw)
    out["wind"] = out.get("wind", 0.0) + float(getattr(ctx, "wind_cap_mw", 0.0))
    out["solar"] = out.get("solar", 0.0) + float(getattr(ctx, "solar_cap_mw", 0.0))
    return out


def _storage_throughput_mwh(yd: "C.YearData") -> tuple[float | None, float | None]:
    """Annual storage discharge / charge energy for one year, MWh.

    Returns ``(discharge_mwh, charge_mwh)``, or ``(None, None)`` when the
    result carries no storage arrays at all (an ISO-year solved with an empty
    storage fleet, or a legacy parquet written before the storage columns).
    ``None`` is "not measured" — never 0.0, which would be indistinguishable
    from a fleet that stood idle all year.
    """
    dis = getattr(yd.result, "storage_discharge", None)
    chg = getattr(yd.result, "storage_charge", None)
    if dis is None and chg is None:
        return None, None
    d = float(np.asarray(dis, dtype=float).sum()) if dis is not None else 0.0
    c = float(np.asarray(chg, dtype=float).sum()) if chg is not None else 0.0
    return d, c


def extract_trajectory(run: "C.Run") -> list[dict]:
    """Per-year headline trajectory metrics for the findings tables.

    Emits the price / scarcity / emissions block, the capacity block
    (``capacity_by_fuel_mw`` and its roll-ups), the evolution-event block
    (``builds_*`` / ``retire_mw``) and — since D29 — the **energy** block
    (``generation_by_fuel_mwh``, ``total_gen_mwh``, the storage throughput
    pair) plus the real storage power column ``storage_power_mw``.

    **The D29 addition is purely additive** (capx D25 §6.1, routed as the
    reporting-grain fix): every pre-existing key keeps its name, type and
    meaning, so a summary written before D29 stays readable by every consumer
    and a summary written after it is a superset. Two gaps closed:

    * **No generation by fuel at all.** The summary carried the fleet's
      *capacity* mix but never its *energy* mix, so the FC-5 corridor's 252
      AEO generation anchors could not be dispositioned against any bundle
      (D25 §2: "AEO's 252 generation anchors are **not** dispositioned — the
      committed summaries carry no generation-by-fuel").
    * **No real storage column** — see the ``storage_mw`` note below.

    Bundles committed before D29 lack the new keys entirely; they are NOT
    regenerated (that would need a re-solve, which D29 is chartered not to do).
    Every reader must therefore treat an absent new key as backward-compatible,
    the same contract the evolution ledger states for ``confirmed_derates`` /
    ``firm_clean_accredited_mw``.
    """
    rows: list[dict] = []
    for year in run.solved_years:
        yd = run.years[year]
        led = run.ledgers.get(year, {})
        price_h = _system_hourly_price(yd)
        scar = {
            f"hours_ge_{int(th)}": int((price_h >= th).sum())
            for th in SCARCITY_THRESHOLDS
        }
        co2 = _co2_tons(yd)
        cap = _capacity_by_fuel(yd)
        # Energy mix (D29). Reuses the invariant checker's own fuel attribution
        # — thermal dispatch summed by the fleet context's fuel_types, plus the
        # separately-dispatched wind/solar arrays — rather than a second
        # implementation of the same sum. Empty dict when the year carries no
        # fleet context, which is the honest "not measured".
        gen = C._fuel_gen_mwh(yd)
        storage_dis_mwh, storage_chg_mwh = _storage_throughput_mwh(yd)
        thermal = sum(mw for f, mw in cap.items() if f in C.THERMAL_FUELS)
        firm_clean = sum(mw for f, mw in cap.items() if f in C.FIRM_CLEAN_FUELS)
        vre = cap.get("wind", 0.0) + cap.get("solar", 0.0)

        def _sum_ledger(key: str, mwkey: str = "mw") -> float:
            return float(sum(float(r.get(mwkey, 0.0)) for r in led.get(key, [])))

        # Per-CHANNEL split of the thermal additions (FFR-3D, FFR-3A blocker 8).
        # The evolution ledger has always tagged every thermal_additions row with
        # its `source` — "planned" | "economic" | "reserve_backstop"
        # (results/evolution_ledger.py; evolve.py writes all three) — but the
        # trajectory summed them into one builds_thermal_mw, so the split never
        # reached a scorer. forecast_verdict.score_fc2 row 4 (backstop share of
        # additions) reads exactly `builds_thermal_backstop_mw` or
        # `builds_by_source["reserve_backstop"]`, so with the channel ARMED and
        # no split present it SKIPped on every run with the message "needs
        # builds_thermal_backstop_mw / builds_by_source from run_full_horizon".
        # That made BLK-10 backstop sizing — the evidence owner decision D-2 was
        # meant to re-open — unscorable anywhere. Emitting the split makes row 4
        # score; it changes no solve and no threshold (rule 1: this is an
        # instrument, not a lever).
        builds_by_source: dict[str, float] = {}
        for r in led.get("thermal_additions", []):
            src = str(r.get("source") or "unattributed")
            builds_by_source[src] = builds_by_source.get(src, 0.0) + float(
                r.get("mw", 0.0) or 0.0
            )

        rows.append(
            {
                "year": year,
                "lw_price": round(C._load_weighted_price(yd), 3),
                "max_hourly_price": round(float(price_h.max()), 1),
                "neg_price_hour_frac": round(
                    float((np.asarray(yd.result.prices) < 0).mean()), 5
                ),
                **scar,
                "co2_mt": round(co2 / 1e6, 4) if co2 is not None else None,
                "peak_demand_mw": led.get("peak_demand_mw"),
                "reserve_margin": led.get("reserve_margin"),
                "rps_dual": led.get("rps_dual"),
                "thermal_mw": round(thermal, 1),
                "firm_clean_mw": round(firm_clean, 1),
                "vre_mw": round(vre, 1),
                "total_cap_mw": round(sum(cap.values()), 1),
                # DEFECT, DELIBERATELY KEPT BUG-COMPATIBLE (capx D25 §6.1 →
                # D29 charter; first reported as FFR-3H §6 B-3 / FFR-3P B-3).
                # `cap` is _capacity_by_fuel, which sums the fleet context's
                # GENERATOR axis (plus the wind/solar scalars) — and LP storage
                # resources are not generators, so no fuel is ever "storage".
                # This key is therefore **0.0 by construction in every summary
                # ever written**, including runs whose real battery fleet is
                # 10-17 GW. It is NOT repaired in place because three committed
                # consumers read it — scripts/collate_full_horizon.py (the
                # storage GW table column), scripts/probes/_d9_relative_deltas
                # .py (SCALARS) and scripts/probes/_d9_forecast_warmstart_ab.py
                # (_CAPACITY_KEYS) — and the latter two compare two summaries
                # key-by-key, so a repaired new-vintage value against an
                # old-vintage committed summary would report a phantom
                # multi-GW delta and defeat the very guardrail it feeds. Read
                # `storage_power_mw` below instead; this key is retained only
                # so those cross-vintage comparisons stay well-defined.
                "storage_mw": round(cap.get("storage", 0.0), 1),
                # THE REAL storage power column (D29). Source: the evolution
                # ledger's own `storage_power_mw`, which runner.py writes as
                # sum(u.power_cap_mw for u in storage_units) — the storage
                # FLEET STATE after that year's new-entry screen, i.e. exactly
                # the quantity `storage_mw` was meant to carry. Read from the
                # ledger rather than reconstructed from a base fleet plus the
                # builds ledger (the reconstruction D25 §2 had to fall back on)
                # so the artifact reports the model's state, not an inference
                # over it. `None` — not 0.0 — on the 83 legacy ledgers written
                # before the key existed: "not measured", per the ledger's own
                # backward-compatibility contract.
                #
                # CLASSIFICATION TRAP, READ BEFORE COMPARING IT TO ANYTHING.
                # This is the WHOLE storage fleet: batteries AND pumped
                # storage. runner.run_scenario_iso puts PS into `storage_units`
                # on both legs — the measured leg logs "MW incl. pumped
                # storage", the default leg prepends the EIA-860 PS fleet — so
                # PS is in the sum by construction. AEO2025's "Diurnal Storage"
                # row (the FC-5 corridor's storage anchor) is BATTERIES ONLY;
                # AEO books PS separately. Comparing this column to it raw
                # manufactures a false convergence: PJM 2030 reads 5,546.1 MW
                # here against AEO's 6.42 GW (−13.6 %, which would score IN
                # CORRIDOR) when the battery-only divergence is −92 %. A
                # corridor consumer must net PS out — the model's PS fleet is
                # fixed EIA-860 existing capacity with no new build, so
                # `storage_power_mw − STORAGE_BASE_FLEET_MW[iso]["mid"]` is its
                # constant residual in the base year (derived on the five FC-5
                # bundles: PJM 5,046.1 / NEISO 1,865.0 / MISO 2,416.8 / NYISO
                # 1,220.0 MW; NOT valid for the measured-base-fleet ISOs, whose
                # battery seed is not the registry scalar). The battery/PS
                # SPLIT is carried by no committed artifact; emitting it is a
                # one-field producer addition in runner.py, ROUTED rather than
                # done here (D29 charter scope). Until it exists, this column
                # is the fleet TOTAL and must be labelled as such wherever it
                # is quoted.
                "storage_power_mw": (
                    round(float(led["storage_power_mw"]), 1)
                    if led.get("storage_power_mw") is not None
                    else None
                ),
                "builds_thermal_mw": _sum_ledger("thermal_additions"),
                # FC-2 row 4 reads builds_thermal_backstop_mw first, then
                # builds_by_source["reserve_backstop"]. Both are emitted: the
                # scalar is what the scorer keys on, the map keeps the full
                # channel attribution (planned / economic / reserve_backstop) in
                # the artifact so the share is auditable rather than asserted.
                "builds_thermal_backstop_mw": round(
                    builds_by_source.get("reserve_backstop", 0.0), 6
                ),
                "builds_by_source": {
                    k: round(v, 6) for k, v in sorted(builds_by_source.items())
                },
                "builds_renew_mw": _sum_ledger("renewable_additions"),
                "builds_storage_mw": _sum_ledger("storage_additions"),
                "retire_mw": _sum_ledger("retirements"),
                # NB: `capacity_by_fuel_mw` and its roll-ups (`total_cap_mw`,
                # `thermal_mw`, `vre_mw`) are GENERATOR-axis quantities and
                # structurally exclude storage — unchanged by D29, which adds
                # the storage column beside them rather than folding storage
                # into a total whose meaning readers already depend on.
                "capacity_by_fuel_mw": {k: round(v, 1) for k, v in sorted(cap.items())},
                # Energy mix (D29): the denominator-and-shares the FC-5
                # corridor's AEO generation anchors are stated in. Wind and
                # solar are DISPATCHED energy (post-curtailment), which is what
                # a generation anchor reports. Storage is NOT folded in here:
                # its discharge is round-tripped energy already counted at
                # charge, so summing it into the fuel mix would double-count.
                "generation_by_fuel_mwh": {
                    k: round(v, 1) for k, v in sorted(gen.items())
                },
                "total_gen_mwh": round(sum(gen.values()), 1) if gen else None,
                "storage_discharge_mwh": (
                    round(storage_dis_mwh, 1) if storage_dis_mwh is not None else None
                ),
                "storage_charge_mwh": (
                    round(storage_chg_mwh, 1) if storage_chg_mwh is not None else None
                ),
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Instrumented solve engine (shared: reference forecast + CES campaign leg)
# --------------------------------------------------------------------------- #
def solve_and_summarize(
    config: ScenarioConfig,
    iso: str,
    out_dir: Path,
    *,
    sample_interval: float = 0.5,
    redirect_cache: bool = True,
    extra_summary: dict | None = None,
    extra_spec: "RecordSpec | None" = None,
) -> dict:
    """Solve one forecast config with instrumentation, write its summary, return it.

    The shared engine behind :func:`main` (the P-3A reference forecast) and
    ``scripts/run_ces_leg.py`` (one premium-ladder leg — FF-3F): it solves
    ``config`` for ``iso`` with per-year wall/RSS sampling, scores the I1-I14
    forecast invariants and the headline trajectory over the cached years,
    writes ``<out_dir>/full_horizon_summary.json`` (the sidecar
    ``register_forecast_baseline.py`` consumes), prints the console report, and
    returns the summary dict.

    Args:
        config: A forecast ``ScenarioConfig`` (caller sets the window + posture;
            the §2.1b window cap is the caller's ``assert_schedulable`` gate).
        iso: ISO identifier.
        out_dir: Directory the ``full_horizon_summary.json`` is written to.
        sample_interval: RSS sampling period in seconds.
        redirect_cache: When True (default — ``run_full_horizon``'s behavior)
            the cache root is pointed at ``out_dir`` so an isolated reference
            solve lands under its own directory. A CES campaign leg passes
            False so its solve lands in the DEFAULT ``results/`` cache — where
            ``report_ces_campaign.py`` and the matrix bundle assemble every leg
            by ``cache_key`` (a redirected leg would be invisible to the report).
            The cache root is restored afterward either way.
        extra_summary: Optional dict merged into the summary verbatim (a leg
            records its ``case`` / ``premium_usd_per_mwh`` / ``crediting`` /
            ``campaign`` there for the CES sidecar).
        extra_spec: Optional :class:`RecordSpec` declaring any config-describing
            keys ``extra_summary`` contributes (FFR-3R). Required whenever
            ``extra_summary`` carries a key naming a ``ScenarioConfig`` field:
            the provenance check refuses an undeclared one, so the caller
            deliberately opts it in and it is then verified against the solved
            config like every other key.

    Returns:
        The summary dict (also written to disk). ``summary["error"]`` is the
        stringified solve exception or ``None``.
    """
    iso = iso.upper()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # runner binds ``save_result`` by name at import; patch it there to record
    # per-year completion timestamps. The solve itself goes through the public
    # facade (which delegates to runner at call time, so the patch is seen).
    from market_sim import runner as runnermod
    from market_sim.pipeline.api import run_scenario

    year_marks: list[tuple[int, float]] = []
    _orig_save = runnermod.save_result
    _orig_cache_root = cachemod.CACHE_ROOT

    def _timed_save(result, config_, iso_, year, **kwargs):
        path = _orig_save(result, config_, iso_, year, **kwargs)
        # record only the final-pass save (pass_label=None) as the boundary
        if kwargs.get("pass_label") is None:
            year_marks.append((int(year), time.monotonic()))
        return path

    sampler = Sampler(interval=sample_interval)
    error = None
    cache_key = None
    if redirect_cache:
        # Point the cache root at this run's out-dir (isolated reference solve).
        cachemod.CACHE_ROOT = out_dir
    runnermod.save_result = _timed_save
    sampler.start()
    run_start = time.monotonic()
    try:
        cache_key = run_scenario(config, iso)
    except Exception as exc:  # noqa: BLE001 — capture, report, keep partials
        error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        run_end = time.monotonic()
        sampler.stop()
        runnermod.save_result = _orig_save

    total_wall = run_end - run_start

    # Per-year wall + peak RSS from the recorded boundaries.
    per_year_perf: list[dict] = []
    prev_t = run_start
    for year, t in sorted(year_marks, key=lambda kv: kv[1]):
        per_year_perf.append(
            {
                "year": year,
                "wall_s": round(t - prev_t, 1),
                "peak_rss_mb": round(sampler.peak_between(prev_t, t), 1),
            }
        )
        prev_t = t

    # Locate the run dir (via the live cache root, so this resolves whether or
    # not the cache was redirected) and score invariants + trajectory.
    run_dir = (
        cachemod.get_cache_path(iso, cache_key, config.start_year).parent
        if cache_key
        else None
    )
    invariants: list[dict] = []
    trajectory: list[dict] = []
    solved_years: list[int] = []
    if run_dir and run_dir.exists():
        try:
            results = C.run_single(run_dir)
            invariants = [
                {"id": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
                for r in results
            ]
        except Exception as exc:  # noqa: BLE001
            invariants = [
                {
                    "id": "LOAD",
                    "name": "invariant load",
                    "status": "FAIL",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            ]
        try:
            run = C.load_run(run_dir)
            solved_years = run.solved_years
            trajectory = extract_trajectory(run)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    # Restore the cache root now that every cache read is done (matters when the
    # engine is called more than once in a process, e.g. a leg then an assembly).
    cachemod.CACHE_ROOT = _orig_cache_root

    start_year, end_year = config.start_year, config.end_year
    summary = {
        # Config-describing block, built FROM THE SOLVED CONFIG by
        # SUMMARY_RECORD_SPEC (FFR-3R) and re-asserted against it below. The
        # FFR-2E comment this replaced explained, key by key, why the clearing
        # gate is read resolved rather than off the scalar flag; the spec now
        # states that once, in a form the code enforces, and refuses any new
        # config-named key added here from another source.
        **SUMMARY_RECORD_SPEC.build(config, {"iso": iso}),
        # Owner decision D-7(ii), signed 2026-08-02: a single-draw forecast
        # deliverable carries the weather-conditional label WITH the artifact.
        # A build-time constant, not a config field.
        "weather_posture": WEATHER_POSTURE,
        "cache_key": cache_key,
        "run_dir": str(run_dir) if run_dir else None,
        "error": error,
        "total_wall_s": round(total_wall, 1),
        "global_peak_rss_mb": round(sampler.global_peak, 1),
        "n_solved_years": len(solved_years),
        "solved_years": solved_years,
        "per_year_perf": per_year_perf,
        "invariants": invariants,
        "trajectory": trajectory,
    }
    # FC-7 provenance artifact, from the run's OWN resolved config (blocker 7).
    # NB: ``run_dir`` is passed ONLY positionally. It used to be passed again
    # inside **extra to get it into the payload, which made every real call
    # raise `TypeError: write_run_config() got multiple values for argument
    # 'run_dir'` — after a full 5-year solve and before the summary was
    # written, so the leg lost its summary AND its FC-7 artifact. The function
    # now records the key itself (see its payload), so the caller must not.
    run_config_path = write_run_config(
        out_dir,
        run_dir,
        iso=iso,
        cache_key=cache_key,
        solved_years=solved_years,
    )
    summary["run_config_path"] = str(run_config_path) if run_config_path else None

    if extra_summary:
        summary.update(extra_summary)
    # Re-checked after the extra_summary merge: a leg driver may add keys here
    # verbatim, and one that names a ScenarioConfig field must agree with the
    # config the solve ran on (FFR-3R). A driver that legitimately records
    # extra config-describing keys (run_ces_leg's CES provenance block)
    # DECLARES them via extra_spec — composition, not a blanket exemption.
    SUMMARY_RECORD_SPEC.merged(extra_spec).assert_sourced(summary, config, {"iso": iso})
    summary_path = out_dir / "full_horizon_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    # Console report.
    print(f"\n===== {iso} {start_year}-{end_year} summary =====")
    print(
        f"  years solved: {len(solved_years)} / {end_year - start_year + 1}"
        f"  ({solved_years[:1]}..{solved_years[-1:]})"
    )
    print(
        f"  total wall: {total_wall / 60:.1f} min   global peak RSS: {sampler.global_peak / 1024:.2f} GB"
    )
    if error:
        print(f"  ERROR: {error}")
    if per_year_perf:
        med = sorted(p["wall_s"] for p in per_year_perf)[len(per_year_perf) // 2]
        maxrss = max(p["peak_rss_mb"] for p in per_year_perf)
        print(
            f"  median year wall: {med:.1f}s   max per-year peak RSS: {maxrss / 1024:.2f} GB"
        )
    # Invariant line (FFR-3A blocker 5). An empty `invariants` list means the
    # gate was NOT EVALUATED — no run directory, or the invariant load itself
    # failed — but the counts of an empty list are 0 and 0, so this printed
    # "invariants: 0 FAIL, 0 WARN" on a ZERO-YEAR run: a hard failure rendered
    # as a clean gate. The JSON summary was always honest (`"invariants": []`);
    # only the console lied, which is the surface an operator reads first.
    if invariants:
        n_fail = sum(1 for i in invariants if i["status"] == "FAIL")
        n_warn = sum(1 for i in invariants if i["status"] == "WARN")
        print(f"  invariants: {n_fail} FAIL, {n_warn} WARN  ({len(invariants)} scored)")
    else:
        why = (
            "solve raised before any result was cached"
            if error
            else "no run directory / no cached years to score"
            if not solved_years
            else "invariant checker returned no rows"
        )
        print(f"  invariants: NOT SCORED — {why}. The gate was not evaluated.")
    for i in invariants:
        if i["status"] in ("FAIL", "WARN"):
            print(
                f"    [{i['status']}] {i['id']:<4} {i['name']:<26} {i['detail'][:120]}"
            )
    if run_config_path:
        print(f"  wrote {run_config_path}")
    else:
        print("  run_config.json NOT written — no resolved config.yaml to read")
    print(f"  wrote {summary_path}")
    return summary


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--end-year", type=int, default=2050)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--capacity-market-clearing",
        action="store_true",
        help="Flip the CR-1 sloped-curve gate on (default OFF = P-2A recommendation).",
    )
    ap.add_argument(
        "--transmission-expansion",
        action="store_true",
        help=(
            "Flip the FF-G1 forward transmission-expansion gate on "
            "(default OFF; committed-registry TTC deltas per solve year)."
        ),
    )
    ap.add_argument(
        "--sample-interval", type=float, default=0.5, help="RSS sampling seconds."
    )
    ap.add_argument(
        "--golden-posture",
        action="store_true",
        help=(
            "Layer the §2.1a decision-(a) per-ISO capacity-market clearing onto "
            "the config (PJM/MISO/NYISO/NEISO/CAISO curve-ON, ERCOT energy-only "
            "OFF). Off by default = the P-3A probe posture. Use for a golden solve."
        ),
    )
    ap.add_argument(
        "--full-solve-authorized",
        action="store_true",
        help=(
            "Lift the §2.1b window cap (the '10-hour rule'). Without it this "
            "runner REFUSES a window wider than 5 solve-years — the schedulable "
            "instruments are T0/T1-F/T1-X/T1-H (≤5 yr). Mirrors the rule-22 "
            "--holdout-authorized gate: a full-horizon (T2/T3/golden) solve is "
            "unschedulable until the owner authorizes it per ISO (plan §2.1b)."
        ),
    )
    ap.add_argument(
        "--retirement-rule",
        choices=["legacy", "pipeline"],
        default=None,
        help=(
            "Economic-retirement decision rule (audit FR-4 / owner D-1). "
            "OMIT to inherit the SHIPPED ScenarioConfig default, which owner "
            "decision D-1 flipped to 'pipeline' on 2026-08-02 (the R-NEW "
            "decision/execution split: uniform bar, joint adequacy-capped "
            "entry, soft latch, measured per-fuel execution lags). Pass "
            "'legacy' to force the retired per-fuel consecutive-loss counters "
            "as a CONTROL arm."
        ),
    )
    ap.add_argument(
        "--entry-vre-capacity-revenue",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 1 PROBE arm (audit FR-5 / owner D-2'): VRE entry "
            "candidates earn the capacity price x published ELCC credit on the "
            "same seam thermal entry uses. No-op in energy-only ISOs. OMIT to "
            "inherit the shipped default — D-2' is signed HOLD, so that is OFF."
        ),
    )
    ap.add_argument(
        "--entry-rate-limits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 2 arm (audit FR-5 / BLK-10): per-tech annual "
            "economic entry AND the reserve-margin backstop capped at "
            "ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) x prior-max annual build "
            "(ReEDS relative-growth constraint, EIA-860-seeded). OMIT to "
            "inherit the shipped default, ARMED by owner decision D-2 "
            "(2026-08-02); --no-entry-rate-limits forces the undamped control."
        ),
    )
    ap.add_argument(
        "--entry-commissioning-lag",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 3 arm (audit FR-5 / FR-13): entry decides in "
            "year Y, commissions at Y+ENTRY_COD_LAG_YEARS (2, LBNL IA->COD "
            "median); pending MW net against later caps. The structural "
            "anti-cobweb. OMIT to inherit the shipped default, ARMED by owner "
            "decision D-2 (2026-08-02); --no-entry-commissioning-lag forces "
            "the un-lagged control."
        ),
    )
    ap.add_argument(
        "--electrification-path",
        choices=["off", "low", "mid", "high"],
        default="off",
        help=(
            "FF-G4 PROBE arm (audit FR-16, owner box §8-D2): additive "
            "electrification end-use layers (heat_pump/ev) over the "
            "weather-8760, relocated energy-invariantly like the DC block. "
            "Default off = the shipped posture; arming is per-ISO owner "
            "evidence-first (NEISO first, memo §8-D3)."
        ),
    )
    ap.add_argument(
        "--entry-screen-diagnostics",
        action="store_true",
        help=(
            "Arm the RC-0C per-candidate entry-screen decomposition sink "
            "(revenue/cost terms, margin, binding queue cap) into each year's "
            "evolution ledger. Pure observability — the fleet outcome is "
            "identical with it on or off — but it MOVES THE CACHE KEY, so pair "
            "an armed leg with an un-armed arm when the key matters."
        ),
    )
    ap.add_argument(
        "--caiso-nqc-accreditation",
        action="store_true",
        help=(
            "FFR-3P arm (CAISO only, DEFAULT OFF pending an owner decision): "
            "accredit CAISO wind/solar at the ISO's OWN published CPUC/CAISO "
            "Net Qualifying Capacity class factors (solar 0.2096, wind 0.2202 "
            "- the Jul/Aug/Sep peak-risk minima of the CY2026 report) instead "
            "of the generic non-CAISO 0.18/0.16 fallback. Solve-affecting: it "
            "raises the accredited-firm ledger, so pair it with an unarmed "
            "control. No-op in every other ISO (rule 25)."
        ),
    )
    ap.add_argument(
        "--caiso-storage-nqc-accreditation",
        action="store_true",
        help=(
            "FFR-4E arm (CAISO only, DEFAULT OFF pending an owner decision): "
            "accredit CAISO STORAGE at the ISO's OWN published whole-class "
            "ratio (13,365 MW September NQC / 15,448.4 MW EIA-860 nameplate = "
            "0.865138, the 2026 SLRA Table 1.1 battery row) instead of the "
            "generic NREL/E3 duration curve. CAISO publishes no storage "
            "duration table, so this REPLACES the by-duration lookup rather "
            "than overriding a row in it (rule 19); pumped storage is excluded "
            "(CAISO books it on the Hydro row). Solve-affecting: it raises the "
            "accredited-firm ledger, so pair it with an unarmed control. No-op "
            "in every other ISO (rule 25)."
        ),
    )
    ap.add_argument(
        "--caiso-ra-mpb-capacity-anchor",
        action="store_true",
        help=(
            "FFR-4F arm (CAISO only, DEFAULT OFF pending an owner decision): "
            "price CAISO capacity at the CPUC unified Resource Adequacy Market "
            "Price Benchmark (11.53 $/kW-month x 12 = 138.36 $/kW-yr, the 2026 "
            "Forecast delivery-year value) instead of the CPM SOFT-OFFER CAP "
            "(88.08 $/kW-yr) the registry ships. The shipped anchor is a "
            "GOING-FORWARD fixed cost of an EXISTING 550 MW COMBINED-CYCLE x "
            "1.20 (FERC ER24-1225) used as the entry price for a new "
            "COMBUSTION TURBINE, and is in any case a ceiling on backstop "
            "OFFERS rather than a price anyone is paid. REPLACES the anchor at "
            "the one shared capacity-price seam (rule 19), so all five "
            "consumers move together. NOT A ROW-4 FIX: row 4's movement is a "
            "reported side effect, never the objective. Solve-affecting: it "
            "raises capacity revenue in the retirement, entry and storage "
            "screens, so pair it with an unarmed control. No-op in every other "
            "ISO (rule 25)."
        ),
    )
    ap.add_argument(
        "--miso-rps-compliance-regions",
        action="store_true",
        # default=None (not False) so "flag absent" is UNSET rather than an
        # explicit off — post-OVERRIDE-FIX an explicit False wins over the ISO
        # override, which would silently un-arm owner decision D-26 for MISO.
        default=None,
        help=(
            "FFR-7B Arm 2 arm (MISO only, DEFAULT OFF pending an owner "
            "decision): replace the single MISO-wide RPS row with K per-state "
            "compliance-region rows (MN/MI/WI/IL/MO — cited "
            "MISO_RPS_COMPLIANCE_REGIONS table), each with its statute's "
            "eligibility mask, obligated-load RHS and own $30 ACP escape. "
            "Solve-affecting (distinct LP layout, distinct cache key); pair "
            "with an unarmed control. No-op in every other ISO (rule 25)."
        ),
    )
    ap.add_argument(
        "--miso-clean-tier-rows",
        action="store_true",
        # default=None: see --miso-rps-compliance-regions (owner decision D-29).
        default=None,
        help=(
            "FFR-7B Arm 3 arm (MISO only; requires "
            "--miso-rps-compliance-regions): add the MN carbon-free + MI "
            "clean tier row family (MISO_CLEAN_TIER_REGIONS, cited) on the "
            "Arm-2 K-row machinery, each row with its own $30 feasibility "
            "escape. REDUNDANT FOR MISO since owner decision D-29 "
            "(2026-08-11) armed it as the MISO forecast default via the ISO "
            "override — a MISO leg builds the family with or without this "
            "flag. This CLI exposes no negative form, so the flag cannot turn "
            "the family back off here; since the OVERRIDE-FIX (2026-08-13) "
            "the CONFIG path can express the off arm (an explicit False now "
            "beats the ISO override), which is why omitting the flag has to "
            "leave the field UNSET rather than pass False. "
            "Solve-affecting, distinct cache key."
        ),
    )
    args = ap.parse_args(argv)

    # §2.1b full-solve authorization gate (the FF-3E schedulability guard). No
    # forecast/hindcast invocation under this program may span > 5 solve-years
    # unless the owner has authorized the full-horizon campaign for this ISO
    # (plan §2.1b/§2.4-0, §7.9). Discipline-level enforcement, mirroring
    # run_calibration_full.py's rule-22 --holdout gate.
    assert_schedulable(args.start_year, args.end_year, args.full_solve_authorized)

    iso = args.iso.upper()
    config = reference_config(
        iso,
        args.start_year,
        args.end_year,
        args.capacity_market_clearing,
        golden_posture=args.golden_posture,
        transmission_expansion=args.transmission_expansion,
        retirement_rule=args.retirement_rule,
        entry_vre_capacity_revenue=args.entry_vre_capacity_revenue,
        entry_rate_limits=args.entry_rate_limits,
        entry_commissioning_lag=args.entry_commissioning_lag,
        electrification_path=args.electrification_path,
        entry_screen_diagnostics=args.entry_screen_diagnostics,
        caiso_nqc_accreditation=args.caiso_nqc_accreditation,
        caiso_storage_nqc_accreditation=args.caiso_storage_nqc_accreditation,
        caiso_ra_mpb_capacity_anchor=args.caiso_ra_mpb_capacity_anchor,
        miso_rps_compliance_regions=args.miso_rps_compliance_regions,
        miso_clean_tier_rows=args.miso_clean_tier_rows,
    )
    summary = solve_and_summarize(
        config,
        iso,
        args.out_dir,
        sample_interval=args.sample_interval,
        redirect_cache=True,
    )
    return 1 if summary.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
