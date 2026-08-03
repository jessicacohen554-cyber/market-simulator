#!/usr/bin/env python
"""Emit the FORECAST DOF-ledger SKELETON for a run — a STUB, honestly chartered.

**What this is.** Forecast-readiness audit FR-27: *"FC-7 reads CAVEAT 'DOF ledger
absent' for every forecast bundle — the forecast side has no DOF-ledger builder
(rule-21 analogue is Phase-B-required)."* The backcast lane has
``scripts/build_dof_ledger.py``, which enumerates each tuned scalar in a keeper's
config together with its **identification source** (``published`` /
``measured-physical`` / ``residual``) — the CLAUDE.md rule 21 ``[R-DOF]`` ledger.
The forecast lane has no analogue, so FC-7's CAVEAT is unfalsifiable: it says a
ledger is absent without saying what the ledger would have had to contain.

This script turns that silent CAVEAT into a **fillable artifact**. It enumerates,
from a run's own ``run_config.json``, every solve-affecting parameter the forecast
actually carries — and writes each one's ``identification`` as the literal token
``unattested``.

**What this is NOT.** It does not attest anything. Deciding whether a forecast
parameter is published, measured-physical, or residual requires reading its
source and its derivation, per parameter — that is the working-group / Phase-B
work the audit charters, not something a config walk can infer. A builder that
guessed identifications would produce exactly the artifact rule 21 exists to
prevent: a ledger that looks attested and is not.

**Consequence, deliberately preserved.** ``scripts/forecast_verdict.py``'s FC-7
scorer treats an ``unattested`` entry as NOT identified, so a run carrying this
skeleton still scores **CAVEAT** — the CAVEAT simply changes from "DOF ledger
absent (identification unproven)" to "N of M entries unattested", naming them.
Filling an entry in (source + evidence + a real identification token) is what
retires it. **Emitting the skeleton must never move a verdict**, and a test pins
that: ``tests/scoring/test_forecast_dof_ledger.py``.

Usage::

    # write the skeleton next to a forecast/hindcast run's config
    python scripts/build_forecast_dof_ledger.py results/ff-t1f-baseline/pjm

    # inspect without writing
    python scripts/build_forecast_dof_ledger.py <bundle> --stdout

    # score a run against it
    python scripts/forecast_verdict.py --dof-ledger <bundle>/dof_ledger.json ...

Stdlib-only (json/argparse/pathlib), no model import, no LP.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SCHEMA = "dof-ledger/v1"

#: The literal identification token this builder writes. It is NOT one of the
#: three real tokens (``published`` / ``measured-physical`` / ``residual``) —
#: that is the point. FC-7 recognizes it and keeps its CAVEAT.
UNATTESTED = "unattested"

#: Parameter GROUPS the forecast lane carries, each with the question its
#: attestation has to answer. Grouping is what makes the skeleton fillable: an
#: attester works a group at a time rather than staring at ~200 loose fields.
#: Membership is by config-field name prefix/exact match, checked in order, so a
#: field lands in exactly one group; anything unmatched falls to "other".
GROUPS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "retirement",
        ("retirement_", "confirmed_exits", "announced_", "forecast_fossil_"),
        "Economic-retirement screen thresholds and exogenous exit channels. "
        "Attest: which are published instrument rules, which are measured "
        "execution lags (EIA-860 announced-to-deactivation), which were chosen "
        "against a hindcast recall residual.",
    ),
    (
        "entry",
        ("entry_", "new_entry", "storage_", "build_", "reserve_margin_build"),
        "Economic-entry economics and dynamics (rate limits, commissioning lag, "
        "capacity-revenue terms, storage value stack). Attest: published source "
        "(ReEDS growth bound, LBNL queue medians, ATB) vs residual.",
    ),
    (
        "capacity_market",
        ("capacity_", "cmc_", "net_cone", "gross_cone", "elcc_", "accredit"),
        "Capacity-market clearing, net-CONE and accreditation. Attest against "
        "the filed per-ISO curve/parameter documents; a forward-evolution rate "
        "is a modelling choice needing its own line.",
    ),
    (
        "fuel_and_policy",
        ("fuel_", "gas_", "coal_", "aeo_", "ira_", "rps_", "carbon_", "eac_", "ces_"),
        "Forward fuel path and policy parameters. Attest to the published "
        "outlook/statute vintage actually consumed.",
    ),
    (
        "demand_and_weather",
        ("demand_", "load_", "weather_", "growth_", "peak_"),
        "Forward demand growth and weather posture. Attest the driver series "
        "and its vintage; a single weather draw is a disclosed posture, not an "
        "identification (D-7(ii)).",
    ),
    (
        "dispatch_mechanism",
        (
            "offer_",
            "min_gen",
            "reliability_floor",
            "commitment",
            "bridge",
            "ramp_",
            "reserve_",
            "ordc",
            "scarcity_",
            "as_",
            "ercot_",
            "caiso_",
            "nyiso_",
            "pjm_",
            "miso_",
            "neiso_",
        ),
        "Dispatch/commitment mechanisms inherited from the backcast calibration. "
        "MOST WILL ALREADY BE ATTESTED in the ISO's backcast ledger — the "
        "forecast attestation should CITE that entry rather than re-derive it, "
        "and must state whether the identification survives extrapolation "
        "forward (a curve fitted on 2023-2025 conduct is not automatically "
        "identified for 2040).",
    ),
)

#: Config fields that describe WHICH scenario is being run rather than tuning
#: HOW it runs. They change results but carry no identification burden — a start
#: year is not a free parameter. Excluded so the skeleton stays about tuning.
SCENARIO_SELECTORS = frozenset(
    {
        "iso",
        "mode",
        "start_year",
        "end_year",
        "year",
        "years",
        "weather_year",
        "scenario_name",
        "name",
        "label",
        "out_dir",
        "cache_dir",
        "cache_key",
        "seed",
        "vintage",
        "vintage_year",
        "crossover_forward_year",
        "run_id",
        "notes",
    }
)


def _group_of(field: str) -> tuple[str, str]:
    """Return ``(group_name, attestation_question)`` for one config field."""
    for name, prefixes, question in GROUPS:
        if any(field == p or field.startswith(p) for p in prefixes):
            return name, question
    return (
        "other",
        "Ungrouped solve-affecting parameter. Attest individually, or extend "
        "GROUPS in scripts/build_forecast_dof_ledger.py if a family emerges.",
    )


def _is_parameterish(value) -> bool:
    """Whether a config value is the kind of thing a DOF ledger enumerates.

    Numbers, booleans that arm a mechanism, and containers of numbers count.
    Pure strings/None do not: a string is almost always a mode selector or a
    path, and enumerating them buries the real parameters in noise. A container
    holding no numeric leaf is likewise skipped.
    """
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, (dict, list, tuple)):
        return _count_scalars(value) > 0
    return False


def _count_scalars(obj) -> int:
    """Count numeric leaves in a nested structure (the tuned-scalar census).

    Mirrors ``scripts/build_dof_ledger._count_scalars`` so a forecast entry's
    ``n_scalars`` means the same thing as a backcast entry's. Booleans are not
    scalars: an arming flag is one decision, not a magnitude.
    """
    if isinstance(obj, bool):
        return 0
    if isinstance(obj, (int, float)):
        return 1
    if isinstance(obj, dict):
        return sum(_count_scalars(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return sum(_count_scalars(v) for v in obj)
    return 0


def _scenario_config(run_config: dict) -> dict:
    """Extract the ScenarioConfig dict from a run_config artifact.

    Accepts the wrapped forms (``scenario_config`` / ``config``) and a bare
    config dict (the hindcast harness's flat YAML dump), matching
    ``scripts/forecast_verdict._scenario_config`` so both read the same runs.
    """
    for key in ("scenario_config", "config"):
        inner = run_config.get(key)
        if isinstance(inner, dict):
            return inner
    if run_config.get("iso") or run_config.get("mode"):
        return run_config
    return {}


def _defaults() -> dict | None:
    """Return the DEFAULT ScenarioConfig as a dict, or ``None`` if unavailable.

    Lazy + guarded: the model stack is a repo dependency but this script must
    still run on a bare checkout (and inside the stdlib CI lanes). ``None``
    means "could not read defaults", which the ledger records explicitly rather
    than silently widening its scope.
    """
    try:
        sys.path.insert(0, str(REPO / "src"))
        from dataclasses import asdict  # noqa: PLC0415

        from market_sim.config.scenarios import ScenarioConfig  # noqa: PLC0415

        return asdict(ScenarioConfig())
    except Exception:  # noqa: BLE001 — absent/unimportable model stack
        return None


def skeleton_entries(sc: dict, defaults: dict | None = None) -> list[dict]:
    """Build one UNATTESTED entry per solve-affecting config parameter.

    When ``defaults`` is available, a field still holding its DEFAULT value is
    skipped: an un-armed mechanism flag or an untouched threshold is not a free
    parameter *of this run*, and enumerating ~200 of them buries the parameters
    that actually carry an identification burden. Without defaults every
    parameterish field is listed, and the ledger says so.
    """
    entries = []
    for field in sorted(sc):
        if field in SCENARIO_SELECTORS or field.startswith("_"):
            continue
        value = sc[field]
        if not _is_parameterish(value):
            continue
        if defaults is not None and field in defaults and value == defaults[field]:
            continue
        group, question = _group_of(field)
        n = _count_scalars(value)
        entry = {
            "name": field,
            "where": "ScenarioConfig",
            "group": group,
            "identification": UNATTESTED,
            "attestation_question": question,
            # Left blank for the attester to fill — present so the artifact is
            # a form, not a list. An entry is retired when `source` cites a
            # primary document AND `identification` becomes a real token.
            "source": "",
            "evidence": "",
        }
        if n:
            entry["n_scalars"] = n
        if isinstance(value, bool) or isinstance(value, (int, float)):
            entry["value"] = value
        entries.append(entry)
    return entries


def build_ledger(run_config: dict, *, run_id: str | None = None) -> dict:
    """Assemble the forecast DOF-ledger skeleton from a run_config artifact."""
    sc = _scenario_config(run_config)
    defaults = _defaults()
    entries = skeleton_entries(sc, defaults)
    by_group: dict[str, int] = {}
    for e in entries:
        by_group[e["group"]] = by_group.get(e["group"], 0) + 1
    return {
        "schema": SCHEMA,
        "lane": "forecast",
        "status": "SKELETON — UNATTESTED",
        "run_id": run_id,
        "iso": sc.get("iso"),
        "seeded_by": (
            "scripts/build_forecast_dof_ledger.py (FFR-3B, 2026-08-02) — audit "
            "FR-27. A STUB: it enumerates what must be attested and attests "
            "NOTHING. Full attestation is working-group / Phase-B work "
            "(docs/forecast-readiness-audit-2026-07.md §4 Phase 5)."
        ),
        "how_to_fill": (
            "Per entry: replace `identification` with one of published | "
            "measured-physical | residual, cite the primary document in "
            "`source`, and put the specific figure/derivation in `evidence`. A "
            "`residual` entry MUST also carry `root_cause` naming an OPEN issue "
            "(CLAUDE.md rule 21 [R-DOF]) — a residual that can only be closed by "
            "a tuned value is an open root cause, not a parameter. Entries in "
            "the `dispatch_mechanism` group should CITE the ISO's backcast "
            "ledger entry rather than re-derive it, and must state whether that "
            "identification survives extrapolation forward."
        ),
        "verdict_effect": (
            "NONE by construction. forecast_verdict.py FC-7 treats `unattested` "
            "as not-identified, so a run carrying this skeleton keeps the same "
            "CAVEAT it had with no ledger at all — the CAVEAT just becomes "
            "specific. Emitting the skeleton can never improve a determination."
        ),
        "scope": (
            "NON-DEFAULT solve-affecting ScenarioConfig fields — the parameters "
            "THIS run chose. A field at its default is an un-armed mechanism or "
            "an untouched threshold, not a free parameter of this run."
            if defaults is not None
            else "EVERY parameterish ScenarioConfig field: the default config "
            "could not be imported, so default-valued fields could not be "
            "excluded and the list is WIDER than the run's real free "
            "parameters. Re-run where market_sim imports to narrow it."
        ),
        "defaults_available": defaults is not None,
        "n_entries": len(entries),
        "n_unattested": sum(1 for e in entries if e["identification"] == UNATTESTED),
        "n_by_group": dict(sorted(by_group.items())),
        "entries": entries,
    }


def _load_run_config(bundle: Path) -> tuple[dict, Path]:
    """Locate and load a run's config artifact (JSON, else the harness YAML)."""
    if bundle.is_file():
        return json.loads(bundle.read_text()), bundle
    for name in ("run_config.json", "full_horizon_summary.json"):
        p = bundle / name
        if p.exists():
            return json.loads(p.read_text()), p
    p = bundle / "run_config.yaml"
    if p.exists():
        try:
            import yaml  # lazy: only the hindcast harness writes YAML

            return yaml.safe_load(p.read_text()) or {}, p
        except Exception as exc:  # noqa: BLE001 — surface, never guess a config
            raise SystemExit(f"cannot parse {p}: {exc}") from exc
    raise SystemExit(
        f"no run_config.json / run_config.yaml / full_horizon_summary.json under {bundle}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "bundle",
        type=Path,
        help="forecast/hindcast run directory (or a run_config.json directly)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        help="output path (default: <bundle>/dof_ledger.json)",
    )
    ap.add_argument(
        "--stdout", action="store_true", help="print the ledger instead of writing it"
    )
    args = ap.parse_args(argv)

    run_config, src = _load_run_config(args.bundle)
    run_id = (
        run_config.get("run_id")
        or (run_config.get("meta") or {}).get("run_id")
        or (args.bundle.name if args.bundle.is_dir() else None)
    )
    ledger = build_ledger(run_config, run_id=run_id)

    text = json.dumps(ledger, indent=2, ensure_ascii=False) + "\n"
    if args.stdout:
        print(text, end="")
        return 0
    out = args.out or (
        (args.bundle if args.bundle.is_dir() else args.bundle.parent)
        / "dof_ledger.json"
    )
    out.write_text(text)
    print(
        f"[dof-ledger] wrote SKELETON to {out} from {src.name}: "
        f"{ledger['n_entries']} entries, ALL UNATTESTED "
        f"({ledger['n_by_group']}). FC-7 stays CAVEAT until they are filled.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
