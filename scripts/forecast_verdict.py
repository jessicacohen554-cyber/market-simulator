"""Reproducible forecast determination for a forecast bundle, per tier.

Implements ``docs/forecast-determination-rubric.md`` (RUBRIC v1.0, FF-0A): reads a
forecast bundle's **committed artifacts only** — the full-horizon summary, the
standalone/embedded forecast-invariant output (I1-I14, paired P1-P3), the
committed capacity-hindcast score, the crossover score, the driver-battery
output, the external-corridor table, ``run_config.json`` / ``dof_ledger.json`` /
``forecast_attestation.json`` — and emits one ``PASS`` / ``CAVEAT`` / ``FAIL`` /
``SKIPPED`` line per category FC-1..FC-8 plus one overall determination per tier
in ``{PROMOTE, PROMOTE-WITH-CAVEATS, HOLD}``. **No LP is ever solved inside the
scorer**, and it never reads gitignored dispatch parquets, so re-running it on
the same artifacts always yields the same verdict.

Precedent: ``scripts/calibration_verdict.py`` (the backcast C1-C8 scorer). This
scorer is its forecast-side sibling and inherits its governance posture: a bundle
is promoted because its **mechanisms** are structurally faithful and its evidence
is complete, never because a number was tuned into a band. Every threshold below
is **pre-registered** in the rubric (design targets / external practice /
already-committed measured evidence) and imported here as a named constant with a
rationale pointer — the scorer never widens a band (rubric §4).

What a determination certifies: a tier-N ``PROMOTE`` says the bundle's evidence
supports entering tier N+1 of the solve ladder (T0->T1->T2->T3, plan §2.1). It is
a *promotion* claim, not an accuracy claim; accuracy claims live only where a
measured instrument exists (FC-3/FC-4). Only a T3 ``PROMOTE`` with the §5
attestation certifies a deliverable.

Stdlib-only on the core path (json, argparse) so it runs anywhere the committed
artifacts are checked out. Two optional imports are lazy and guarded: ``pyyaml``
(only for a hindcast bundle's ``run_config.yaml``) and ``market_sim`` (only for
the pre-registered per-ISO planning-reserve floor behind FC-2's terminal-drift
row). Each falls back to a recorded SKIP when unavailable, so the scorer and its
tests never require the model stack.

Usage (rubric §8)::

    # T1-F short-forecast bundle (invariants + adequacy + provenance + runtime):
    python scripts/forecast_verdict.py --tier t1f \
        --summary results/ff-t1f-baseline/ercot/full_horizon_summary.json \
        --run-config results/ff-t1f-baseline/ercot/run_config.json \
        --json-out results/ff-t1f-baseline/ercot/forecast_verdict.json

    # T1-H hindcast bundle (FC-3 primary):
    python scripts/forecast_verdict.py --tier t1h \
        --hindcast-score results/hindcast/<run_id>/score.json \
        --run-config results/hindcast/<run_id>/run_config.json

    # T2 gate (all instruments):
    python scripts/forecast_verdict.py --tier t2 \
        --summary <t2 summary> --hindcast-score <t1h score> \
        --crossover-score <t1x score> --driver-battery <battery json> \
        --corridor <corridor table> --dof-ledger <dof> --json-out <sidecar>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Repo import bootstrap so the lazy constants fallback (the pre-registered FC-2.2
# planning-reserve floor) resolves when the scorer runs from a checkout without an
# install. The market_sim import stays lazy + except-guarded inside _planning_floor
# — the scorer never *requires* the model stack; this only lets the fallback find
# it when present (mirrors scripts/check_forecast_invariants.py).
_SRC = REPO / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Rubric version implemented by this scorer (rubric §0/§9). v1.0 = the FF-0A
# initial rubric: categories FC-1..FC-8, tier ladder T0->T3, golden attestation.
RUBRIC_VERSION = "1.0"

# --- statuses (per row / per category) --------------------------------------
PASS, CAVEAT, FAIL, SKIPPED = "PASS", "CAVEAT", "FAIL", "SKIPPED"
# A T3 attestation that is required-but-absent reads UNATTESTED (a FAIL flavour,
# mirroring backcast C6) so the reason surfaces the missing checklist explicitly.
UNATTESTED = "UNATTESTED"

# --- overall determinations (rubric §3) -------------------------------------
PROMOTE = "PROMOTE"
PROMOTE_CAVEATS = "PROMOTE-WITH-CAVEATS"
HOLD = "HOLD"

# --- per-tier category applicability (rubric §3 table) ----------------------
# Each (tier, category) resolves to one applicability token:
#   REQUIRED  — must be scored; a SKIPPED (absent) required category ⇒ HOLD.
#   OPTIONAL  — scored if artifacts present; absence recorded, does NOT HOLD; a
#               present-and-FAIL optional category still gates ("failed evidence
#               never promotes").
#   REPORT    — report-only: computed and listed, but NEVER gates.
#   NA        — not applicable at this tier; not scored (recorded).
#   RUNTIME   — FC-8 only: required-but-never-blocking (can never FAIL/HOLD; a
#               CAVEAT surfaces, a SKIPPED does not HOLD).
REQUIRED, OPTIONAL, REPORT, NA, RUNTIME = (
    "required",
    "optional",
    "report",
    "n/a",
    "runtime",
)

TIERS = ("t1f", "t1x", "t1h", "t2", "t3")

# The §3 applicability matrix, transcribed verbatim. FC-2's per-row tier logic
# (rows 1,3,4 gate at t1f; row 2 terminal-drift is t2/t3 only; row 5 gates only
# curve-ON; row 6 ERCOT-scarcity is t1-report / t2-t3-gate) is applied inside
# :func:`score_fc2`; the category token here is its top-level applicability.
APPLICABILITY: dict[str, dict[str, str]] = {
    #        t1f        t1x        t1h        t2        t3
    "FC-1": {
        "t1f": REQUIRED,
        "t1x": REQUIRED,
        "t1h": OPTIONAL,
        "t2": REQUIRED,
        "t3": REQUIRED,
    },
    "FC-2": {
        "t1f": REQUIRED,
        "t1x": OPTIONAL,
        "t1h": NA,
        "t2": REQUIRED,
        "t3": REQUIRED,
    },
    "FC-3": {"t1f": NA, "t1x": REPORT, "t1h": REQUIRED, "t2": REQUIRED, "t3": REQUIRED},
    "FC-4": {"t1f": NA, "t1x": REQUIRED, "t1h": NA, "t2": REQUIRED, "t3": REQUIRED},
    "FC-5": {"t1f": REPORT, "t1x": REPORT, "t1h": NA, "t2": REQUIRED, "t3": REQUIRED},
    "FC-6": {"t1f": OPTIONAL, "t1x": NA, "t1h": NA, "t2": REQUIRED, "t3": REQUIRED},
    "FC-7": {
        "t1f": REQUIRED,
        "t1x": REQUIRED,
        "t1h": REQUIRED,
        "t2": REQUIRED,
        "t3": REQUIRED,
    },
    "FC-8": {
        "t1f": RUNTIME,
        "t1x": RUNTIME,
        "t1h": RUNTIME,
        "t2": RUNTIME,
        "t3": RUNTIME,
    },
}

# Category id -> human label (rubric §2).
CATEGORY_LABEL = {
    "FC-1": "FC-1 structural integrity (I1-I14)",
    "FC-2": "FC-2 adequacy & equilibrium behavior",
    "FC-3": "FC-3 capacity-evolution skill (T1-H hindcast)",
    "FC-4": "FC-4 crossover dispatch skill (T1-X)",
    "FC-5": "FC-5 external corridor",
    "FC-6": "FC-6 driver response",
    "FC-7": "FC-7 provenance & DOF",
    "FC-8": "FC-8 runtime feasibility",
}
CATEGORY_ORDER = ["FC-1", "FC-2", "FC-3", "FC-4", "FC-5", "FC-6", "FC-7", "FC-8"]

# ===========================================================================
# Pre-registered thresholds (rubric §2). Every value carries its rationale
# pointer; NONE is derived from a run this scorer will score (rubric §4 clause 1
# — bands never widen in response to a result).
# ===========================================================================

# FC-2 row 4 — backstop share of additions (rubric §2 FC-2.4). The administrative
# reliability channel is a single-digit-percent residual in real markets.
BACKSTOP_SHARE_PASS = 0.10  # ≤10% PASS
BACKSTOP_SHARE_FAIL = 0.30  # >30% FAIL (10-30% ⇒ CAVEAT)

# FC-2 row 2 — terminal reserve-margin drift (rubric §2 FC-2.2, T2/T3 only).
# Band [floor − 10pp, floor + 25pp] around PLANNING_RESERVE_MARGIN_BY_ISO: RTO
# planning targets ~13.75-18% RM, CPUC procurement tops ~25%; no external outlook
# plans to > floor+25pp, and sustained RM < floor−10pp is chronic shortage.
TERMINAL_DRIFT_LO_PP = -0.10
TERMINAL_DRIFT_HI_PP = 0.25

# FC-2 row 6 — ERCOT scarcity-hour frequency (rubric §2 FC-2.6, ERCOT only).
# Quantity: the trajectory's committed hours_ge_500 count/year (lowest committed
# threshold that unambiguously indicates scarcity-adder pricing). ORDC design
# math ⇒ order-of-magnitude corridor [2, 200] h/yr on the window mean; >800h in
# one year is sustained-VOLL behaviour no external outlook contemplates.
SCARCITY_THRESHOLD_KEY = "hours_ge_500"
SCARCITY_MEAN_LO = 2.0
SCARCITY_MEAN_HI = 200.0
SCARCITY_YEAR_FAIL = 800.0
# T2/T3 stability window over which a sustained scarcity/RM signal is read.
STABILITY_WINDOW = (2031, 2035)
# I12 WARN chain length that fails FC-2 row 1 at t2 (rubric §3, T2->T3 stability).
I12_WARN_CHAIN_FAIL = 3

# FC-4 — crossover absolute dispatch-skill bands (rubric §2 FC-4.2). Commercial
# band × the ISO's input-gap multiple K_iso (from the D-7 statmode evidence,
# committed 2026-07-05 — predates every run this rubric scores). ERCOT/NEISO/
# CAISO/NYISO carry little system-level overlay skill ⇒ K=1.5; PJM/MISO overlays
# carry real skill in outage/coal-cost-sensitive fleets ⇒ K=3.0 (ceiling ±30%
# CO2, inside the D-7 worst case PJM +26.6%).
CROSSOVER_K_ISO = {
    "ERCOT": 1.5,
    "NEISO": 1.5,
    "CAISO": 1.5,
    "NYISO": 1.5,
    "PJM": 3.0,
    "MISO": 3.0,
}
CROSSOVER_K_DEFAULT = 1.5  # strict default for an unlisted ISO
# Commercial bands (the backcast rubric's own commercial-grade tolerances,
# rubric §2 FC-4.2): price ±10%, system CO2 ±10%, gas/coal family volume ±5%.
CROSSOVER_COMMERCIAL = {
    "price": 0.10,
    "co2": 0.10,
    "gas_twh": 0.05,
    "coal_twh": 0.05,
}
# Scored years for the crossover dispatch skill (rubric §2 FC-4; rule 22 stops at
# 2025 — the scorer must never read ≥2026 actuals).
CROSSOVER_SCORED_YEARS = (2023, 2024, 2025)
CROSSOVER_QUARANTINE_FLOOR = 2026  # first quarantined (never-scored) year

# FC-5 — external-corridor divergence trigger (rubric §2 FC-5). The
# cross-model-corridor convention, imported whole: divergence > 15% (or opposite
# sign) requires a written ours-vs-theirs explanation naming the mechanism.
CORRIDOR_DIVERGENCE_TRIGGER = 0.15

# FC-8 — runtime budgets (rubric §2 FC-8; plan §2.4 measured scheduling anchors),
# total wall-clock seconds per tier and the 15 GB-box RSS "no co-run" anchor.
RUNTIME_WALL_BUDGET_S = {
    "t1f": 45 * 60,
    "t1x": 45 * 60,
    "t1h": int(2.5 * 3600),
    "t2": 2 * 3600,
    "t3": 9 * 3600,
}
RUNTIME_RSS_NOCORUN_MB = 8_600.0  # ≥8.6 GB flags the "no co-run" condition

# FC-7 — forecast governance. In a forecast-mode run the CAMPD outage-windows
# overlay is armed exactly when ``outage_source`` is the backcast source; a
# forecast run uses a statistical/forward source. The delivered-fuel (F923)
# overlay flags below are all default-OFF, so asserting "must be falsy" never
# false-positives a clean forecast config (rubric §2 FC-7.2).
BACKCAST_OUTAGE_SOURCES = frozenset({"historic"})
# Curated backcast-only overlay flags (F923 delivered-fuel family) that must be
# off in a forecast-mode run. Each is default-falsy in ScenarioConfig and is
# flipped on only by the backcast config builder (pipeline/backcast_config.py).
BACKCAST_OVERLAY_FLAGS = (
    "gas_hub_basis_overlay",
    "ercot_gas_delivered_floor_basis",
    "ercot_west_gas_delivered_floor",
)
# The mode a given tier's run_config must record (rubric §2 FC-7.1). Forecast
# tiers assert "forecast"; the hindcast tier accepts the harness's own mode.
TIER_EXPECTED_MODE = {
    "t1f": ("forecast",),
    "t1x": ("forecast",),
    "t1h": ("forecast", "backcast", "hindcast"),
    "t2": ("forecast",),
    "t3": ("forecast",),
}
# The flag surface FC-7.1 expects a run_config to expose (non-empty config dump
# plus the tier's capacity-clearing gate key — rule 24, every tunable visible).
EXPECTED_GATE_KEYS = ("capacity_market_clearing",)
# A real ScenarioConfig dump exposes hundreds of flags (the golden run_config
# carries ~319); fewer than this is a stub/thin config, not the full surface rule
# 24 requires. Structural presence check, not a tuned value.
CONFIG_FULL_SURFACE_MIN_KEYS = 20

# §5 golden-attestation checklist assertion keys (rubric §5). The scorer checks
# presence + internal consistency; the truth of each assertion is the attesting
# session's auditable responsibility (the backcast C6 posture).
ATTESTATION_ASSERTIONS = (
    "dof_ledger_complete",
    "run_config_reproducible",
    "honest_unfit_referenced",
    "quarantine_attested",
    "no_off_registry_knobs",
    "registered",
)

ISO_DEFAULT = "ERCOT"


# ===========================================================================
# Artifact loading (committed files only; every optional input ⇒ None)
# ===========================================================================
def _load_json(path: str | Path | None) -> dict | list | None:
    """Load a committed JSON artifact, or return ``None`` when absent.

    A path that is given but does not exist is an explicit ``FileNotFoundError``
    (a caller asked to score against a file that is not there — surface it), but
    an *un-supplied* artifact (``None``) simply reads ``None`` so the category
    SKIPs rather than crashing.
    """
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"artifact not found: {p}")
    return json.loads(p.read_text())


def _load_config(path: str | Path | None) -> dict | None:
    """Load a run_config artifact — JSON, or the hindcast bundle's YAML dump.

    Forecast/golden bundles write ``run_config.json``; the capacity-hindcast
    harness writes ``run_config.yaml`` (a flat ``ScenarioConfig`` dump). YAML is
    parsed with a lazy ``pyyaml`` import (a repo dependency) so the JSON path
    stays stdlib-only. An unreadable YAML records ``None`` (FC-7 then SKIPs).
    """
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"artifact not found: {p}")
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # lazy: only hindcast run_config.yaml needs it

            return yaml.safe_load(p.read_text())
        except Exception:  # noqa: BLE001 — pyyaml absent / malformed ⇒ SKIP
            return None
    return json.loads(p.read_text())


def load_artifacts(args: argparse.Namespace) -> dict:
    """Load every committed artifact named on the CLI into one dict.

    Missing (un-supplied) artifacts are ``None`` so each category can record a
    SKIPPED rather than crash. Split out from :func:`main` so the decision logic
    can be unit-tested on synthetic artifacts without touching the filesystem.
    """
    return {
        "summary": _load_json(args.summary),
        "invariants": _load_json(args.invariants),
        "paired_invariants": _load_json(args.paired_invariants),
        "hindcast": _load_json(args.hindcast_score),
        "crossover": _load_json(args.crossover_score),
        "driver_battery": _load_json(args.driver_battery),
        "corridor": _load_json(args.corridor),
        "run_config": _load_config(args.run_config),
        "dof_ledger": _load_json(args.dof_ledger),
        "attestation": _load_json(args.attestation),
        "position": _load_json(getattr(args, "position", None)),
    }


# ===========================================================================
# Small helpers (stdlib only)
# ===========================================================================
def _row(
    category: str,
    row: str,
    status: str,
    detail: str,
    *,
    gating: bool = True,
    values: dict | None = None,
) -> dict:
    """Build one per-row scoring record.

    ``gating`` marks whether the row participates in its category's status (a
    report-only row within a gating category — e.g. FC-2 row 6 at t1 — is listed
    but never contributes). ``values`` carries the offending numbers for the
    JSON sidecar / the dashboard.
    """
    return {
        "category": category,
        "row": row,
        "status": status,
        "detail": detail,
        "gating": gating,
        "values": values or {},
    }


def _agg_rows(rows: list[dict]) -> str:
    """Aggregate a category's GATING rows (FAIL > CAVEAT > SKIPPED > PASS).

    Non-gating (report-only) rows never contribute. A gating SKIPPED outranks
    PASS so an "all pass except one unmeasured" category never reads a clean PASS
    (rubric §0/§4 — an absent input is recorded, never silently passed); a real
    FAIL or CAVEAT still dominates. A category with no gating rows at all reads
    SKIPPED (nothing was scored).
    """
    s = {r["status"] for r in rows if r.get("gating", True)}
    if FAIL in s or UNATTESTED in s:
        return FAIL
    if CAVEAT in s:
        return CAVEAT
    if SKIPPED in s:
        return SKIPPED
    if PASS in s:
        return PASS
    return SKIPPED


def _iso_of(art: dict) -> str:
    """Resolve the bundle's ISO from whichever artifact carries meta."""
    for key in ("summary", "hindcast", "crossover", "run_config"):
        obj = art.get(key)
        if isinstance(obj, dict):
            meta = obj.get("meta", obj)
            iso = meta.get("iso") or obj.get("iso")
            if iso:
                return str(iso).upper()
    sc = _scenario_config(art)
    if sc.get("iso"):
        return str(sc["iso"]).upper()
    return ISO_DEFAULT


def _scenario_config(art: dict) -> dict:
    """Return the run's ScenarioConfig dict from run_config (or summary meta)."""
    rc = art.get("run_config")
    if isinstance(rc, dict):
        for key in ("scenario_config", "config"):
            if isinstance(rc.get(key), dict):
                return rc[key]
        # A run_config that IS the scenario_config dict (no wrapper).
        if rc.get("iso") or rc.get("mode"):
            return rc
    summ = art.get("summary")
    if isinstance(summ, dict):
        meta = summ.get("meta", {})
        if isinstance(meta.get("scenario_config"), dict):
            return meta["scenario_config"]
    return {}


def _curve_on(art: dict) -> bool:
    """Whether the run has capacity_market_clearing enabled (curve-ON).

    Read from the run_config's ScenarioConfig first, then the full-horizon
    summary's top-level ``capacity_market_clearing`` flag (the harness records it
    there, not in a meta block).
    """
    sc = _scenario_config(art)
    if "capacity_market_clearing" in sc:
        return bool(sc["capacity_market_clearing"])
    summ = art.get("summary")
    if isinstance(summ, dict):
        if "capacity_market_clearing" in summ:  # top-level in full_horizon_summary
            return bool(summ["capacity_market_clearing"])
        meta = summ.get("meta", {})
        if "capacity_market_clearing" in meta:
            return bool(meta["capacity_market_clearing"])
    return False


# ===========================================================================
# Invariant + trajectory readers (shared by FC-1, FC-2, FC-8)
# ===========================================================================
# The forecast-invariant status literals (owned by check_forecast_invariants.py;
# this scorer consumes them and never re-derives an invariant — rubric §2 FC-1).
I_PASS, I_FAIL, I_WARN, I_SKIP = "PASS", "FAIL", "WARN", "SKIP"


def _invariant_map(art: dict) -> dict[str, dict] | None:
    """Return ``{ident: {status, detail, name}}`` from the committed invariants.

    Sources, in order: an explicit ``--invariants`` list (keyed ``ident``), then
    the full-horizon summary's embedded ``invariants`` (keyed ``id``), then a
    hindcast sidecar's embedded ``invariants`` (keyed ``ident``). Returns ``None``
    when no invariant record exists at all (⇒ FC-1 SKIPPED, never a silent pass).
    """
    rows: list | None = None
    inv = art.get("invariants")
    if isinstance(inv, list):
        rows = inv
    elif isinstance(art.get("summary"), dict) and isinstance(
        art["summary"].get("invariants"), list
    ):
        rows = art["summary"]["invariants"]
    elif isinstance(art.get("hindcast"), dict) and isinstance(
        art["hindcast"].get("invariants"), list
    ):
        rows = art["hindcast"]["invariants"]
    if rows is None:
        return None
    out: dict[str, dict] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        ident = r.get("ident") or r.get("id")  # producers disagree on the key
        if ident:
            out[str(ident)] = {
                "status": r.get("status"),
                "detail": r.get("detail", ""),
                "name": r.get("name", ""),
            }
    return out or None


def _paired_list(art: dict) -> list[dict]:
    """Return the paired invariant rows (P1-P3) from ``--paired-invariants``."""
    p = art.get("paired_invariants")
    return [r for r in p if isinstance(r, dict)] if isinstance(p, list) else []


def _trajectory(art: dict) -> list[dict]:
    """Return the full-horizon summary's per-year trajectory rows (or [])."""
    summ = art.get("summary")
    if isinstance(summ, dict) and isinstance(summ.get("trajectory"), list):
        return [r for r in summ["trajectory"] if isinstance(r, dict)]
    return []


# ===========================================================================
# Per-category scorers (rubric §2). Each returns a list of per-row records; the
# category status is _agg_rows() of its gating rows. Every optional/absent input
# is recorded SKIPPED, never silently passed (rubric §0/§4).
# ===========================================================================
def score_fc1(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-1 structural integrity — consume I1-I14 (hard gate; never re-derived).

    Any invariant FAIL ⇒ FC-1 FAIL (offending ids listed); any WARN ⇒ CAVEAT;
    all PASS (individual SKIP invariants noted, never gating) ⇒ PASS. A missing
    invariant record ⇒ SKIPPED (an unscored bundle, not a passing one).
    """
    imap = _invariant_map(art)
    if imap is None:
        return [
            _row(
                "FC-1",
                "invariants I1-I14",
                SKIPPED,
                "no committed invariant record (summary.invariants / --invariants)",
            )
        ]
    fails = sorted(k for k, v in imap.items() if v["status"] == I_FAIL)
    warns = sorted(k for k, v in imap.items() if v["status"] == I_WARN)
    skips = sorted(k for k, v in imap.items() if v["status"] == I_SKIP)
    values = {"fail": fails, "warn": warns, "skip": skips, "n": len(imap)}
    if fails:
        det = "; ".join(f"{k}: {imap[k]['detail']}" for k in fails)
        return [
            _row(
                "FC-1", "invariants I1-I14", FAIL, f"FAIL {fails}: {det}", values=values
            )
        ]
    if warns:
        det = "; ".join(f"{k}: {imap[k]['detail']}" for k in warns)
        return [
            _row(
                "FC-1",
                "invariants I1-I14",
                CAVEAT,
                f"WARN {warns}: {det}",
                values=values,
            )
        ]
    tail = f" ({len(skips)} SKIP: {skips})" if skips else ""
    return [
        _row(
            "FC-1",
            "invariants I1-I14",
            PASS,
            f"all {len(imap)} invariants PASS{tail}",
            values=values,
        )
    ]


def _fc2_gates(tier: str, row: int, curve_on: bool, iso: str) -> bool | None:
    """Whether FC-2 row ``row`` gates at ``tier`` (rubric §2 FC-2 / §3 table).

    Returns True (gating), False (report-only at this tier), or None (row not
    applicable / not emitted at this tier).
    """
    ercot = iso.upper() == "ERCOT"
    if row == 1 or row == 3 or row == 4:  # reserve margin / cobweb / backstop
        return True if tier in ("t1f", "t1x", "t2", "t3") else None
    if row == 2:  # terminal drift — T2/T3 only
        return True if tier in ("t2", "t3") else None
    if row == 5:  # curve-ON position — only when curve-ON
        if not curve_on:
            return None
        return True if tier in ("t1f", "t1x", "t2", "t3") else None
    if row == 6:  # ERCOT scarcity — gate at T2/T3, report at T1
        if not ercot:
            return None
        return True if tier in ("t2", "t3") else False
    return None


def score_fc2(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-2 adequacy & equilibrium behavior (trajectory + I12/I13 + curve/scarcity).

    Six rows with per-tier gating (:func:`_fc2_gates`): (1) reserve-margin band
    consumes I12; (2) terminal drift (T2/T3); (3) cobweb consumes I13; (4)
    backstop share of additions; (5) curve-ON position; (6) ERCOT scarcity
    frequency.
    """
    imap = _invariant_map(art) or {}
    traj = _trajectory(art)
    curve_on = _curve_on(art)
    rows: list[dict] = []

    def emit(rn: int, status: str, detail: str, values=None):
        g = _fc2_gates(tier, rn, curve_on, iso)
        if g is None:
            return  # not applicable at this tier
        rows.append(
            _row("FC-2", f"row{rn}", status, detail, gating=g, values=values or {})
        )

    # Row 1 — reserve-margin band (consume I12).
    if _fc2_gates(tier, 1, curve_on, iso) is not None:
        i12 = imap.get("I12")
        if i12 is None:
            emit(1, SKIPPED, "reserve-margin band: I12 absent from invariant record")
        elif i12["status"] == I_FAIL:
            emit(1, FAIL, f"reserve-margin band (I12 FAIL): {i12['detail']}")
        elif i12["status"] == I_WARN:
            emit(1, CAVEAT, f"reserve-margin band (I12 WARN): {i12['detail']}")
        else:
            emit(1, PASS, "reserve-margin band (I12 PASS)")

    # Row 2 — terminal reserve-margin drift (T2/T3 only).
    if _fc2_gates(tier, 2, curve_on, iso) is not None:
        floor = _planning_floor(iso, art)
        rm = traj[-1].get("reserve_margin") if traj else None
        if floor is None:
            emit(
                2,
                SKIPPED,
                "terminal drift: planning-reserve floor unresolved (import/meta absent)",
            )
        elif rm is None:
            emit(
                2, SKIPPED, "terminal drift: no final-year reserve_margin in trajectory"
            )
        else:
            lo, hi = floor + TERMINAL_DRIFT_LO_PP, floor + TERMINAL_DRIFT_HI_PP
            vals = {
                "final_rm": rm,
                "floor": floor,
                "band": [lo, hi],
                "year": traj[-1].get("year"),
            }
            if lo <= rm <= hi:
                emit(2, PASS, f"final RM {rm:.1%} in [{lo:.1%}, {hi:.1%}]", vals)
            else:
                emit(
                    2,
                    FAIL,
                    f"final RM {rm:.1%} outside [{lo:.1%}, {hi:.1%}] (floor {floor:.1%})",
                    vals,
                )

    # Row 3 — cobweb (consume I13).
    if _fc2_gates(tier, 3, curve_on, iso) is not None:
        i13 = imap.get("I13")
        if i13 is None:
            emit(3, SKIPPED, "cobweb: I13 absent from invariant record")
        elif i13["status"] == I_WARN:
            emit(3, FAIL, f"cobweb (I13 WARN ⇒ row FAIL): {i13['detail']}")
        else:
            emit(3, PASS, "no cobweb (I13 PASS)")

    # Row 4 — backstop share of additions.
    if _fc2_gates(tier, 4, curve_on, iso) is not None:
        rows.append(_score_fc2_backstop(tier, art, traj, curve_on, iso))

    # Row 5 — curve-ON position trajectory.
    if _fc2_gates(tier, 5, curve_on, iso) is not None:
        pos = art.get("position")
        if pos is None:
            emit(
                5,
                SKIPPED,
                "curve-ON position-validation artifact absent (unscored evidence)",
            )
        else:
            st = str(
                pos.get("status") or pos.get("verdict") or pos.get("band") or ""
            ).upper()
            det = (
                pos.get("detail")
                or pos.get("note")
                or "committed position-validation verdict"
            )
            if st in ("FAIL", "OUT"):
                emit(5, FAIL, f"position vs published auction out of T-R4 band: {det}")
            elif st in ("CAVEAT", "WARN"):
                emit(5, CAVEAT, f"position vs auction marginal: {det}")
            elif st in ("PASS", "IN"):
                emit(5, PASS, f"position vs auction in T-R4 band: {det}")
            else:
                emit(
                    5,
                    SKIPPED,
                    f"position artifact carries no recognizable verdict ({st or 'none'})",
                )

    # Row 6 — ERCOT scarcity-hour frequency (gate T2/T3, report T1).
    if _fc2_gates(tier, 6, curve_on, iso) is not None:
        counts = [
            r.get(SCARCITY_THRESHOLD_KEY)
            for r in traj
            if r.get(SCARCITY_THRESHOLD_KEY) is not None
        ]
        if not counts:
            emit(6, SKIPPED, f"scarcity: no {SCARCITY_THRESHOLD_KEY} in trajectory")
        else:
            mean = sum(counts) / len(counts)
            worst = max(counts)
            vals = {"mean_hours": mean, "max_year_hours": worst, "counts": counts}
            if worst > SCARCITY_YEAR_FAIL:
                emit(
                    6,
                    FAIL,
                    f"{SCARCITY_THRESHOLD_KEY} peaks {worst:.0f}h/yr > {SCARCITY_YEAR_FAIL:.0f} (sustained-VOLL)",
                    vals,
                )
            elif mean == 0:
                emit(
                    6,
                    CAVEAT,
                    f"scarcity never forms (mean {SCARCITY_THRESHOLD_KEY} = 0h/yr — BLK-6/G-31 gap)",
                    vals,
                )
            elif SCARCITY_MEAN_LO <= mean <= SCARCITY_MEAN_HI:
                emit(
                    6,
                    PASS,
                    f"mean {SCARCITY_THRESHOLD_KEY} {mean:.0f}h/yr in [{SCARCITY_MEAN_LO:.0f}, {SCARCITY_MEAN_HI:.0f}]",
                    vals,
                )
            else:
                emit(
                    6,
                    CAVEAT,
                    f"mean {SCARCITY_THRESHOLD_KEY} {mean:.0f}h/yr outside [{SCARCITY_MEAN_LO:.0f}, {SCARCITY_MEAN_HI:.0f}]",
                    vals,
                )

    if not rows:
        return [
            _row(
                "FC-2",
                "adequacy",
                SKIPPED,
                "no trajectory / invariant evidence to score FC-2",
            )
        ]
    return rows


def _score_fc2_backstop(
    tier: str, art: dict, traj: list[dict], curve_on: bool, iso: str
) -> dict:
    """FC-2 row 4 — cumulative reserve_backstop thermal additions ÷ total additions.

    When the reserve-margin backstop channel is disabled (``reserve_margin_build
    _enabled`` off — its default), backstop builds are structurally zero, so the
    share is provably 0% ⇒ PASS with no producer dependency. When the channel is
    armed, the share needs the trajectory's per-channel split
    (``builds_thermal_backstop_mw`` or a ``builds_by_source`` map); absent that,
    the row SKIPs with an actionable message (the run_full_horizon trajectory
    currently emits only the ``builds_thermal_mw`` total).
    """
    g = _fc2_gates(tier, 4, curve_on, iso)
    sc = _scenario_config(art)
    enabled = bool(sc.get("reserve_margin_build_enabled"))
    if not enabled and "reserve_margin_build_enabled" in sc:
        return _row(
            "FC-2",
            "row4",
            PASS,
            "backstop share 0% (reserve_margin_build_enabled off — no backstop channel)",
            gating=bool(g),
            values={"backstop_share": 0.0, "channel": "off"},
        )
    if not traj:
        return _row(
            "FC-2",
            "row4",
            SKIPPED,
            "backstop share: no trajectory rows",
            gating=bool(g),
        )
    backstop = 0.0
    total = 0.0
    have_split = False
    for r in traj:
        t_add = float(r.get("builds_thermal_mw", 0.0) or 0.0)
        renew = float(r.get("builds_renew_mw", 0.0) or 0.0)
        stor = float(r.get("builds_storage_mw", 0.0) or 0.0)
        total += t_add + renew + stor
        if "builds_thermal_backstop_mw" in r:
            backstop += float(r.get("builds_thermal_backstop_mw", 0.0) or 0.0)
            have_split = True
        elif isinstance(r.get("builds_by_source"), dict):
            backstop += float(r["builds_by_source"].get("reserve_backstop", 0.0) or 0.0)
            have_split = True
    if not have_split:
        return _row(
            "FC-2",
            "row4",
            SKIPPED,
            "backstop channel armed but trajectory carries no reserve_backstop split "
            "(needs builds_thermal_backstop_mw / builds_by_source from run_full_horizon)",
            gating=bool(g),
        )
    if total <= 0:
        return _row(
            "FC-2",
            "row4",
            PASS,
            "backstop share 0% (no additions in window)",
            gating=bool(g),
            values={"backstop_share": 0.0},
        )
    share = backstop / total
    vals = {"backstop_share": share, "backstop_mw": backstop, "total_add_mw": total}
    if share <= BACKSTOP_SHARE_PASS:
        return _row(
            "FC-2",
            "row4",
            PASS,
            f"backstop share {share:.1%} ≤ {BACKSTOP_SHARE_PASS:.0%}",
            gating=bool(g),
            values=vals,
        )
    if share <= BACKSTOP_SHARE_FAIL:
        return _row(
            "FC-2",
            "row4",
            CAVEAT,
            f"backstop share {share:.1%} in ({BACKSTOP_SHARE_PASS:.0%}, {BACKSTOP_SHARE_FAIL:.0%}]",
            gating=bool(g),
            values=vals,
        )
    return _row(
        "FC-2",
        "row4",
        FAIL,
        f"backstop share {share:.1%} > {BACKSTOP_SHARE_FAIL:.0%} (administrative over-build)",
        gating=bool(g),
        values=vals,
    )


def _planning_floor(iso: str, art: dict) -> float | None:
    """Pre-registered planning-reserve-margin floor for FC-2.2 (rubric §2 FC-2.2).

    Reproducible-from-artifact first (summary meta / run_config), then the
    pre-registered ``PLANNING_RESERVE_MARGIN_BY_ISO`` from constants (lazy import
    — the scorer never hardcodes the floor, rule 4). ``None`` when unresolved
    (the row then SKIPs).
    """
    summ = art.get("summary")
    if isinstance(summ, dict):
        for src in (summ, summ.get("meta", {})):
            if isinstance(src, dict) and isinstance(
                src.get("planning_reserve_margin"), (int, float)
            ):
                return float(src["planning_reserve_margin"])
    sc = _scenario_config(art)
    if isinstance(sc.get("planning_reserve_margin"), (int, float)):
        return float(sc["planning_reserve_margin"])
    try:
        from market_sim.config.constants import PLANNING_RESERVE_MARGIN_BY_ISO

        return PLANNING_RESERVE_MARGIN_BY_ISO.get(iso.upper())
    except Exception:  # noqa: BLE001 — model stack unavailable ⇒ SKIP the row
        return None


def score_fc3(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-3 capacity-evolution skill — read the hindcast score's committed bands.

    Reads only the ``band`` verdicts already computed by
    ``score_capacity_hindcast.py`` (PASS/FAIL/SKIP; no CAVEAT exists there) — it
    never recomputes a band (rubric §2 FC-3 / §4 clause 3). Any gated band FAIL ⇒
    FC-3 FAIL; all bands PASS with baselines present ⇒ PASS; baselines absent ⇒
    CAVEAT (skill-vs-baseline unproven). No committed score ⇒ SKIPPED.
    """
    hc = art.get("hindcast")
    if hc is None:
        return [
            _row(
                "FC-3",
                "hindcast bands",
                SKIPPED,
                "no committed capacity-hindcast score for the ISO",
            )
        ]
    score = hc.get("score", hc) if isinstance(hc, dict) else {}
    bands = _collect_hindcast_bands(score)
    if not bands:
        return [
            _row(
                "FC-3",
                "hindcast bands",
                SKIPPED,
                "hindcast score carries no band verdicts",
            )
        ]
    fails = [name for name, st in bands if st == "FAIL"]
    skips = [name for name, st in bands if st == "SKIP"]
    baselines = score.get("baselines") if isinstance(score, dict) else None
    values = {
        "bands": dict(bands),
        "n_bands": len(bands),
        "fails": fails,
        "skips": skips,
    }
    rows = []
    if fails:
        rows.append(
            _row("FC-3", "hindcast bands", FAIL, f"band FAIL: {fails}", values=values)
        )
    elif not baselines:
        rows.append(
            _row(
                "FC-3",
                "hindcast bands",
                CAVEAT,
                f"all {len(bands)} bands PASS but baselines absent — skill-vs-baseline unproven"
                + (f"; SKIP bands {skips}" if skips else ""),
                values=values,
            )
        )
    else:
        rows.append(
            _row(
                "FC-3",
                "hindcast bands",
                PASS,
                f"all {len(bands)} bands PASS; baselines present"
                + (f"; SKIP bands {skips}" if skips else ""),
                values=values,
            )
        )
    return rows


def _collect_hindcast_bands(score: dict) -> list[tuple[str, str]]:
    """Collect every committed ``band`` verdict from a hindcast score block."""
    if not isinstance(score, dict):
        return []
    out: list[tuple[str, str]] = []
    ret = score.get("retirements", {})
    if isinstance(ret, dict):
        for key in ("total_gw", "unit_recall_gt300", "false_retire"):
            b = ret.get(key, {})
            if isinstance(b, dict) and b.get("band"):
                out.append((f"retire.{key}", b["band"]))
    add = score.get("additions", {})
    if isinstance(add, dict):
        for grp in ("by_tech", "shares"):
            g = add.get(grp, {})
            if isinstance(g, dict):
                for tech, b in g.items():
                    if isinstance(b, dict) and b.get("band"):
                        out.append((f"add.{grp}.{tech}", b["band"]))
    return out


def score_fc4(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-4 crossover dispatch skill — quarantine integrity + banded absolute skill.

    Reads the committed ``score_crossover.py`` output (FF-0E; absent until that
    session lands ⇒ SKIPPED). Row 1 (quarantine): the ≥2026 refusal marker must
    be present and clean, else FC-4 FAILs outright (rule 22). Row 2 (absolute
    skill): per metric-year |error| within commercial band × K_iso ⇒ within-band;
    beyond ⇒ FAIL; within K-band but beyond the commercial band ⇒ CAVEAT. Row 3
    (input-gap ratio): report-only.
    """
    cx = art.get("crossover")
    if cx is None:
        return [
            _row(
                "FC-4",
                "crossover score",
                SKIPPED,
                "no committed crossover score (FF-0E instrument)",
            )
        ]
    rows: list[dict] = []
    # Row 1 — quarantine integrity (the refusal marker).
    marker = cx.get("refusal_marker") or cx.get("quarantine") or {}
    read_ge = bool(marker.get("read_ge_2026", marker.get("ge_2026_read", False)))
    scored_max = marker.get("scored_max_year") or marker.get("max_year_scored")
    if not marker:
        rows.append(
            _row(
                "FC-4",
                "quarantine",
                FAIL,
                "≥2026 refusal marker ABSENT — crossover score inadmissible (rule 22)",
            )
        )
        return rows  # inadmissible evidence: stop
    if read_ge or (
        scored_max is not None and int(scored_max) >= CROSSOVER_QUARANTINE_FLOOR
    ):
        rows.append(
            _row(
                "FC-4",
                "quarantine",
                FAIL,
                f"refusal marker VIOLATED (read ≥{CROSSOVER_QUARANTINE_FLOOR} / scored_max {scored_max})",
            )
        )
        return rows
    rows.append(
        _row(
            "FC-4",
            "quarantine",
            PASS,
            f"≥{CROSSOVER_QUARANTINE_FLOOR} refusal marker present and clean",
        )
    )
    # Row 2 — absolute dispatch skill per metric-year.
    k = CROSSOVER_K_ISO.get(iso.upper(), CROSSOVER_K_DEFAULT)
    metrics = cx.get("metrics", [])
    worst = PASS
    detail_bits: list[str] = []
    scored_any = False
    for m in metrics if isinstance(metrics, list) else []:
        metric = m.get("metric")
        year = m.get("year")
        err = m.get("forecast_abs_err_frac", m.get("forecast_err_frac"))
        if metric not in CROSSOVER_COMMERCIAL or err is None:
            continue
        if year is not None and int(year) not in CROSSOVER_SCORED_YEARS:
            continue  # rule 22: never score ≥2026
        scored_any = True
        err = abs(float(err))
        commercial = CROSSOVER_COMMERCIAL[metric]
        band = commercial * k
        if err > band:
            worst = FAIL
            detail_bits.append(
                f"{metric} {year} |{err:.1%}|>{band:.1%}=K{k}×{commercial:.0%} FAIL"
            )
        elif err > commercial:
            worst = FAIL if worst == FAIL else CAVEAT
            detail_bits.append(
                f"{metric} {year} |{err:.1%}| in ({commercial:.0%}, {band:.1%}] CAVEAT"
            )
    if not scored_any:
        rows.append(
            _row(
                "FC-4",
                "dispatch skill",
                SKIPPED,
                "crossover score carries no scorable 2023-2025 metric errors",
            )
        )
    else:
        rows.append(
            _row(
                "FC-4",
                "dispatch skill",
                worst,
                (f"K_iso={k}; " + "; ".join(detail_bits))
                if detail_bits
                else f"all metrics within commercial band (K={k})",
                values={"k_iso": k},
            )
        )
    # Row 3 — input-gap ratio (report-only).
    ratios = [
        m
        for m in (metrics if isinstance(metrics, list) else [])
        if m.get("keeper_abs_err_frac") or m.get("keeper_err_frac")
    ]
    if ratios:
        rows.append(
            _row(
                "FC-4",
                "input-gap ratio",
                PASS,
                "forecast/keeper input-gap ratios reported (report-only)",
                gating=False,
                values={"n": len(ratios)},
            )
        )
    return rows


def score_fc5(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-5 external corridor — explanation discipline, not proximity.

    Reads the committed benchmark-corridor table (FF-0D intake; absent ⇒ SKIPPED
    with the missing-source list). Per-row verdict IN CORRIDOR / EXPLAINED
    DIVERGENCE / UNEXPLAINED: any UNEXPLAINED ⇒ FC-5 FAIL (routes to root cause);
    all in-corridor ⇒ PASS; explained divergences only ⇒ CAVEAT (rubric §2 FC-5).
    """
    co = art.get("corridor")
    if co is None:
        return [
            _row(
                "FC-5",
                "corridor",
                SKIPPED,
                "no committed benchmark-corridor table (FF-0D intake; rubric §6 list pending)",
            )
        ]
    crows = co.get("rows", []) if isinstance(co, dict) else []
    if not crows:
        miss = co.get("missing_sources") if isinstance(co, dict) else None
        return [
            _row(
                "FC-5",
                "corridor",
                SKIPPED,
                "corridor table present but carries no scored rows"
                + (f"; missing sources: {miss}" if miss else ""),
            )
        ]
    unexplained, explained, incorr = [], [], []
    for r in crows:
        v = str(r.get("verdict", "")).upper().replace("-", " ").strip()
        label = f"{r.get('quantity', '?')}@{r.get('target_year', '?')}"
        if "UNEXPLAINED" in v:
            unexplained.append(label)
        elif "EXPLAINED" in v:
            explained.append(label)
        elif "IN CORRIDOR" in v or v == "IN":
            incorr.append(label)
        else:
            unexplained.append(label + f"(unrecognized verdict {v!r})")
    values = {"unexplained": unexplained, "explained": explained, "in_corridor": incorr}
    if unexplained:
        return [
            _row(
                "FC-5",
                "corridor",
                FAIL,
                f"UNEXPLAINED divergence rows: {unexplained}",
                values=values,
            )
        ]
    if explained:
        return [
            _row(
                "FC-5",
                "corridor",
                CAVEAT,
                f"explained divergences: {explained}",
                values=values,
            )
        ]
    return [
        _row(
            "FC-5",
            "corridor",
            PASS,
            f"all {len(incorr)} rows in corridor",
            values=values,
        )
    ]


def score_fc6(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-6 driver response — Tier-1 monotonicity battery + paired P1-P3.

    Gate rows (``expectations[].gate == True``): a FAIL ⇒ FC-6 FAIL; a SKIP
    (vacuous / insufficient rungs) ⇒ CAVEAT, never PASS (rubric §2 FC-6.2).
    Report rows (``gate == False``) annotate but never gate. Paired invariants:
    P1/P2 FAIL ⇒ FAIL; P3 WARN ⇒ CAVEAT. Nothing committed ⇒ SKIPPED.
    """
    battery = art.get("driver_battery")
    paired = _paired_list(art)
    rows: list[dict] = []

    if battery is not None:
        gate_fail, vacuous, report = [], [], []
        n_gate = 0
        for ladder in battery.get("ladders", []) if isinstance(battery, dict) else []:
            tid = ladder.get("test_id", "?")
            for e in ladder.get("expectations", []):
                if not isinstance(e, dict):
                    continue
                label = f"{tid}/{e.get('expr_id', e.get('description', '?'))}"
                if e.get("gate", True):
                    n_gate += 1
                    if e.get("status") == I_FAIL:
                        gate_fail.append(f"{label}: {e.get('detail', '')}")
                    elif e.get("status") == I_SKIP:
                        vacuous.append(label)
                elif e.get("status") in (I_FAIL, I_WARN):
                    report.append(f"{label} [{e.get('status')}]")
        if gate_fail:
            rows.append(
                _row(
                    "FC-6",
                    "battery gate rows",
                    FAIL,
                    f"gate FAIL: {gate_fail}",
                    values={"n_gate": n_gate},
                )
            )
        elif vacuous:
            rows.append(
                _row(
                    "FC-6",
                    "battery gate rows",
                    CAVEAT,
                    f"gate rows PASS but {len(vacuous)} vacuous (SKIP, insufficient rungs): {vacuous}",
                    values={"n_gate": n_gate, "vacuous": vacuous},
                )
            )
        else:
            rows.append(
                _row(
                    "FC-6",
                    "battery gate rows",
                    PASS,
                    f"all {n_gate} gate rows PASS",
                    values={"n_gate": n_gate},
                )
            )
        for r in report:
            rows.append(_row("FC-6", "battery report rows", CAVEAT, r, gating=False))

    for r in paired:
        ident = r.get("ident") or r.get("id")
        st = r.get("status")
        if ident in ("P1", "P2"):
            status = FAIL if st == I_FAIL else (SKIPPED if st == I_SKIP else PASS)
            rows.append(
                _row(
                    "FC-6",
                    f"paired {ident}",
                    status,
                    f"{ident} {r.get('name', '')}: {r.get('detail', '')}",
                )
            )
        elif ident == "P3":
            status = CAVEAT if st == I_WARN else (SKIPPED if st == I_SKIP else PASS)
            rows.append(_row("FC-6", "paired P3", status, f"P3 {r.get('detail', '')}"))

    if not rows:
        return [
            _row(
                "FC-6",
                "driver response",
                SKIPPED,
                "no committed driver-battery or paired-invariant output",
            )
        ]
    return rows


def score_fc7(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-7 provenance & DOF — run_config, overlay-off, DOF ledger, attestation.

    (1) run_config present/parses/mode/flag-surface; (2) no backcast overlay armed
    in a forecast-mode run; (3) DOF ledger well-formed (absent ⇒ CAVEAT at t1/t2,
    FAIL at t3); (4) §5 golden attestation present + assertions true (T3 only,
    absent ⇒ UNATTESTED). Thresholds are structural (present/absent/armed) — rule
    5/13/21/24 made executable.
    """
    rows: list[dict] = []
    sc = _scenario_config(art)
    rc = art.get("run_config")

    # Row 1 — run_config presence + mode + flag surface.
    if rc is None or not sc:
        rows.append(
            _row(
                "FC-7",
                "run_config",
                FAIL if rc is None else CAVEAT,
                "run_config.json absent"
                if rc is None
                else "run_config carries no scenario_config flag surface",
            )
        )
        mode = None
    else:
        mode = sc.get("mode")
        expected = TIER_EXPECTED_MODE.get(tier, ("forecast",))
        gate_keys_present = [k for k in EXPECTED_GATE_KEYS if k in sc]
        # Rule 24 = "every tunable visible". The real check is a full flag
        # surface: a ScenarioConfig dump exposes hundreds of flags. The gate key
        # is illustrative (rubric §2 FC-7.1 "e.g. capacity_market_clearing") — the
        # hindcast run_config.yaml is a full surface that simply omits that
        # derived flag, so a full dump PASSes; only a thin/stub config caveats.
        full_surface = len(sc) >= CONFIG_FULL_SURFACE_MIN_KEYS or bool(
            gate_keys_present
        )
        if mode is None:
            rows.append(_row("FC-7", "run_config", FAIL, "run_config records no mode"))
        elif mode not in expected:
            rows.append(
                _row(
                    "FC-7",
                    "run_config",
                    FAIL,
                    f"mode={mode!r} not in expected {expected} for {tier}",
                )
            )
        elif not full_surface:
            rows.append(
                _row(
                    "FC-7",
                    "run_config",
                    CAVEAT,
                    f"mode={mode}; config dump is not a full flag surface "
                    f"({len(sc)} keys, gates {gate_keys_present}) — rule 24 unverifiable",
                )
            )
        else:
            gate_note = (
                f"gates {gate_keys_present}" if gate_keys_present else "full surface"
            )
            rows.append(
                _row(
                    "FC-7",
                    "run_config",
                    PASS,
                    f"mode={mode}; {len(sc)} config keys; {gate_note}",
                )
            )

    # Row 2 — no backcast overlay armed in a forecast-mode run.
    if mode == "forecast":
        armed = []
        outage = sc.get("outage_source")
        if outage in BACKCAST_OUTAGE_SOURCES:
            armed.append(f"outage_source={outage!r} (CAMPD outage windows)")
        for flag in BACKCAST_OVERLAY_FLAGS:
            if sc.get(flag):
                armed.append(f"{flag}={sc[flag]!r}")
        if armed:
            rows.append(
                _row(
                    "FC-7",
                    "overlay-off",
                    FAIL,
                    "backcast overlay armed in forecast run: " + "; ".join(armed),
                )
            )
        else:
            rows.append(
                _row(
                    "FC-7",
                    "overlay-off",
                    PASS,
                    f"no backcast overlay armed (outage_source={outage!r})",
                )
            )
    elif mode is not None:
        rows.append(
            _row(
                "FC-7",
                "overlay-off",
                PASS,
                f"mode={mode!r}: harness-mode run, overlay-off check n/a (realized inputs admissible)",
                gating=False,
            )
        )

    # Row 3 — DOF ledger.
    rows.append(_score_dof_ledger(art, tier))

    # Row 4 — golden attestation (T3 only).
    if tier == "t3":
        rows.append(_score_attestation(art))

    return rows


def _score_dof_ledger(art: dict, tier: str) -> dict:
    """FC-7 row 3 — the DOF ledger names every free parameter → identification.

    Reads a standalone ``dof_ledger.json`` or a ``free_parameters`` block inside
    the attestation (``schema: dof-ledger/v1``). Well-formed = entries present,
    each with a name + identification, and every ``residual`` carries an open
    ``root_cause`` (rule 21). Absent ⇒ CAVEAT at t1/t2, FAIL at t3.
    """
    ledger = art.get("dof_ledger")
    if ledger is None:
        att = art.get("attestation")
        if isinstance(att, dict) and isinstance(att.get("free_parameters"), dict):
            ledger = att["free_parameters"]
    if not ledger:
        status = FAIL if tier == "t3" else CAVEAT
        return _row(
            "FC-7",
            "dof ledger",
            status,
            "DOF ledger absent"
            + (
                " (unattestable golden candidate)"
                if tier == "t3"
                else " (identification unproven)"
            ),
        )
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    if not entries:
        status = FAIL if tier == "t3" else CAVEAT
        return _row(
            "FC-7", "dof ledger", status, "DOF ledger present but carries no entries"
        )
    malformed = []
    open_residuals = 0
    for e in entries:
        if not isinstance(e, dict) or not e.get("name") or not e.get("identification"):
            malformed.append(str(e.get("name", e) if isinstance(e, dict) else e))
            continue
        if e.get("identification") == "residual":
            open_residuals += 1
            if not e.get("root_cause"):
                malformed.append(f"{e['name']} (residual without root_cause)")
    if malformed:
        return _row("FC-7", "dof ledger", FAIL, f"malformed DOF entries: {malformed}")
    return _row(
        "FC-7",
        "dof ledger",
        PASS,
        f"{len(entries)} entries well-formed ({open_residuals} open residual DOF listed)",
    )


def _score_attestation(art: dict) -> dict:
    """FC-7 row 4 — the §5 golden-attestation checklist (T3 only).

    Presence + internal consistency (machine-checkable); the truth of each
    assertion is the attesting session's auditable responsibility (backcast C6
    posture). Absent ⇒ UNATTESTED (a FAIL flavour ⇒ HOLD).
    """
    att = art.get("attestation")
    if not isinstance(att, dict):
        return _row(
            "FC-7",
            "attestation",
            UNATTESTED,
            "no forecast_attestation.json (a golden run cannot be certified unattested)",
        )
    block = att
    for key in ("checklist", "attestation", "assertions", "golden"):
        if isinstance(att.get(key), dict):
            block = att[key]
            break
    missing = [a for a in ATTESTATION_ASSERTIONS if a not in block]
    false_asserts = [
        a for a in ATTESTATION_ASSERTIONS if a in block and not block.get(a)
    ]
    if missing:
        return _row(
            "FC-7",
            "attestation",
            UNATTESTED,
            f"attestation missing assertions: {missing}",
        )
    if false_asserts:
        return _row(
            "FC-7",
            "attestation",
            FAIL,
            f"attestation assertions false: {false_asserts}",
        )
    return _row(
        "FC-7", "attestation", PASS, "all §5 checklist assertions present and true"
    )


def score_fc8(art: dict, tier: str, iso: str) -> list[dict]:
    """FC-8 runtime feasibility — WARN-level, never blocking (rubric §2 FC-8).

    Total wall vs the tier's plan §2.4 budget; peak RSS vs the 15 GB-box anchor.
    Over budget ⇒ CAVEAT (with the measured numbers); within ⇒ PASS; missing perf
    ⇒ SKIPPED. FC-8 can never FAIL (:func:`_determine` treats it as non-blocking).
    """
    summ = art.get("summary")
    if not isinstance(summ, dict) or summ.get("total_wall_s") is None:
        return [
            _row("FC-8", "runtime", SKIPPED, "no perf ledger (total_wall_s) in summary")
        ]
    wall = float(summ["total_wall_s"])
    rss = summ.get("global_peak_rss_mb")
    budget = RUNTIME_WALL_BUDGET_S.get(tier)
    vals = {"total_wall_s": wall, "budget_s": budget, "peak_rss_mb": rss}
    bits = []
    status = PASS
    if budget is not None and wall > budget:
        status = CAVEAT
        bits.append(f"wall {wall / 60:.1f} min > {budget / 60:.0f} min budget")
    if rss is not None and float(rss) >= RUNTIME_RSS_NOCORUN_MB:
        status = CAVEAT
        bits.append(
            f"peak RSS {float(rss) / 1000:.1f} GB ≥ {RUNTIME_RSS_NOCORUN_MB / 1000:.1f} GB (no co-run)"
        )
    detail = "; ".join(bits) if bits else f"wall {wall / 60:.1f} min within budget"
    return [_row("FC-8", "runtime", status, detail, values=vals)]


# ===========================================================================
# Determination (rubric §3)
# ===========================================================================
def _determine(
    categories: dict[str, dict], tier: str
) -> tuple[str, list[str], list[str]]:
    """Fold the per-category verdicts into one determination (rubric §3).

    Returns ``(determination, reasons, caveats)``. A category gates when its
    applicability is REQUIRED, or OPTIONAL-and-actually-scored (present). REPORT
    and NA categories never gate; FC-8 (RUNTIME) never FAILs and never HOLDs, but
    a runtime CAVEAT is surfaced.
    """
    caveats: list[str] = []
    holds: list[str] = []

    for cid in CATEGORY_ORDER:
        cat = categories[cid]
        appl = cat["applicability"]
        status = cat["status"]
        label = cat["label"]
        if appl == NA or appl == REPORT:
            continue  # never gates (report-only rows are surfaced as notes)
        if appl == RUNTIME:
            if status == CAVEAT:
                caveats.append(f"{label}: over runtime budget")
            continue  # FC-8 never FAILs and never HOLDs (rubric §2 FC-8)
        if appl == REQUIRED:
            if status in (FAIL, UNATTESTED):
                holds.append(f"{label} FAIL")
            elif status == SKIPPED:
                holds.append(f"{label} SKIPPED (required, unscored)")
            elif status == CAVEAT:
                caveats.append(label)
        elif appl == OPTIONAL:
            # Present-and-FAIL gates; absent (SKIPPED) is recorded but does not
            # HOLD; a present CAVEAT is surfaced.
            if status in (FAIL, UNATTESTED):
                holds.append(f"{label} FAIL")
            elif status == CAVEAT:
                caveats.append(label)

    if holds:
        return HOLD, holds, caveats
    if caveats:
        return PROMOTE_CAVEATS, [], caveats
    return PROMOTE, [], []


def determine_from_artifacts(art: dict, tier: str) -> dict:
    """Score one forecast bundle's loaded artifacts at ``tier`` (rubric §2/§3).

    Split out from :func:`determine` so the decision logic is unit-testable on
    synthetic artifacts without reading files.
    """
    if tier not in TIERS:
        raise SystemExit(f"unknown tier {tier!r}; choose from {', '.join(TIERS)}")
    iso = _iso_of(art)

    scorers = {
        "FC-1": score_fc1,
        "FC-2": score_fc2,
        "FC-3": score_fc3,
        "FC-4": score_fc4,
        "FC-5": score_fc5,
        "FC-6": score_fc6,
        "FC-7": score_fc7,
        "FC-8": score_fc8,
    }
    categories: dict[str, dict] = {}
    for cid in CATEGORY_ORDER:
        appl = APPLICABILITY[cid][tier]
        if appl == NA:
            categories[cid] = {
                "label": CATEGORY_LABEL[cid],
                "applicability": appl,
                "status": NA,
                "rows": [],
            }
            continue
        rows = scorers[cid](art, tier, iso)
        categories[cid] = {
            "label": CATEGORY_LABEL[cid],
            "applicability": appl,
            "status": _agg_rows(rows),
            "rows": rows,
        }

    determination, reasons, caveats = _determine(categories, tier)
    notes = _report_notes(categories)
    return {
        "rubric_version": RUBRIC_VERSION,
        "schema": "forecast-verdict/v1",
        "tier": tier,
        "iso": iso,
        "determination": determination,
        "reasons": reasons,
        "caveats": caveats,
        "notes": notes,
        "categories": categories,
    }


def _report_notes(categories: dict[str, dict]) -> list[str]:
    """Collect report-only / non-gating row statuses as surfaced notes."""
    notes: list[str] = []
    for cid in CATEGORY_ORDER:
        cat = categories[cid]
        if cat["applicability"] == REPORT and cat["status"] not in (SKIPPED, NA):
            notes.append(f"{cat['label']} (report-only): {cat['status']}")
        for r in cat.get("rows", []):
            if not r.get("gating", True) and r["status"] in (FAIL, CAVEAT):
                notes.append(f"{cat['label']} / {r['row']} (report): {r['detail']}")
    return notes


# ===========================================================================
# Rendering
# ===========================================================================
_MARK = {PASS: "✓", CAVEAT: "~", FAIL: "✗", SKIPPED: "·", NA: "-", UNATTESTED: "?"}


def render_text(v: dict) -> str:
    """Render a verdict as a compact, auditable text block."""
    lines = ["=" * 72]
    lines.append(f"FORECAST DETERMINATION [{v['tier'].upper()}]: {v['determination']}")
    lines.append(f"  {v['iso']}   rubric v{v['rubric_version']}")
    lines.append("=" * 72)
    for cid in CATEGORY_ORDER:
        c = v["categories"][cid]
        appl = c["applicability"]
        tag = {
            REQUIRED: "REQ",
            OPTIONAL: "OPT",
            REPORT: "rpt",
            NA: "n/a",
            RUNTIME: "run",
        }.get(appl, "?")
        lines.append(
            f"[{_MARK.get(c['status'], '?')}] {c['status']:7s} {tag:3s}  {c['label']}"
        )
        for r in c["rows"]:
            if r["status"] == PASS:
                continue  # keep the block focused on what is not a clean pass
            gate = "" if r.get("gating", True) else " (report)"
            lines.append(f"        {r['status']:7s} {r['row']}{gate}: {r['detail']}")
    lines.append("-" * 72)
    if v["reasons"]:
        lines.append("determination basis (HOLD):")
        for r in v["reasons"]:
            lines.append(f"  - {r}")
    elif v["caveats"]:
        lines.append("promoted with caveats:")
        for cav in v["caveats"]:
            lines.append(f"  - {cav}")
    else:
        lines.append(
            "determination basis: every required category scored, no FAIL/CAVEAT."
        )
    if v.get("notes"):
        lines.append("notes:")
        for n in v["notes"]:
            lines.append(f"  - {n}")
    lines.append("=" * 72)
    return "\n".join(lines)


def headline(v: dict) -> str:
    """One-line determination headline."""
    extra = (
        f" — {v['reasons'][0]}"
        if v["reasons"]
        else (f" — {len(v['caveats'])} caveat(s)" if v["caveats"] else "")
    )
    return (
        f"DETERMINATION [{v['tier'].upper()} {v['iso']}]: {v['determination']}{extra}"
    )


def condensed_sidecar(v: dict) -> dict:
    """Condense a full verdict to the JSON sidecar the dashboard reads (§8).

    Keeps the determination, per-category status + applicability, and the
    per-row status/detail (dropping the bulky ``values`` blocks the dashboard
    re-derives from the source artifacts).
    """
    return {
        "schema": v["schema"],
        "rubric_version": v["rubric_version"],
        "tier": v["tier"],
        "iso": v["iso"],
        "determination": v["determination"],
        "reasons": v["reasons"],
        "caveats": v["caveats"],
        "notes": v["notes"],
        "categories": {
            cid: {
                "label": c["label"],
                "applicability": c["applicability"],
                "status": c["status"],
                "rows": [
                    {
                        "row": r["row"],
                        "status": r["status"],
                        "detail": r["detail"],
                        "gating": r.get("gating", True),
                    }
                    for r in c["rows"]
                ],
            }
            for cid, c in v["categories"].items()
        },
    }


# ===========================================================================
# CLI
# ===========================================================================
def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--tier", required=True, choices=list(TIERS), help="test-ladder tier to score"
    )
    ap.add_argument("--summary", help="full_horizon_summary.json")
    ap.add_argument("--invariants", help="check_forecast_invariants.py --json output")
    ap.add_argument(
        "--paired-invariants",
        dest="paired_invariants",
        help="check_forecast_invariants.py --paired --json output (FC-6)",
    )
    ap.add_argument(
        "--hindcast-score", dest="hindcast_score", help="hindcast score.json (FC-3)"
    )
    ap.add_argument(
        "--crossover-score", dest="crossover_score", help="crossover score JSON (FC-4)"
    )
    ap.add_argument(
        "--driver-battery", dest="driver_battery", help="driver-battery JSON (FC-6)"
    )
    ap.add_argument("--corridor", help="external-corridor table JSON (FC-5)")
    ap.add_argument("--position", help="curve-ON position-validation artifact (FC-2.5)")
    ap.add_argument("--run-config", dest="run_config", help="run_config.json (FC-7)")
    ap.add_argument("--dof-ledger", dest="dof_ledger", help="dof_ledger.json (FC-7)")
    ap.add_argument("--attestation", help="forecast_attestation.json (FC-7 / §5, T3)")
    ap.add_argument("--json-out", dest="json_out", help="write the JSON sidecar here")
    ap.add_argument(
        "--json", action="store_true", help="print the machine verdict JSON"
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    """CLI: score one forecast bundle at a tier and print its determination."""
    args = _build_parser().parse_args(argv)
    art = load_artifacts(args)
    verdict = determine_from_artifacts(art, args.tier)
    if args.json:
        print(json.dumps(verdict, indent=2, default=str))
    else:
        print(render_text(verdict))
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(condensed_sidecar(verdict), indent=2, default=str) + "\n"
        )
        print(f"wrote {out}")
    # Exit nonzero on HOLD so a CI gate can assert on the determination directly.
    return 0 if verdict["determination"] != HOLD else 1


if __name__ == "__main__":
    raise SystemExit(main())
