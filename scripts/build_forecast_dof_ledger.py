#!/usr/bin/env python
"""Build the FORECAST DOF ledger for a registered bundle — the FC-7 instrument.

**What this is.** The rule-21 ``[R-DOF]`` keeper discipline, forecast-side:
for a registered forecast/hindcast bundle (its committed ``run_config.json`` /
``run_config.yaml`` resolved-config dump), enumerate every free parameter that
entered the solve and REPORT each one's identification source from committed
evidence. The recognised identification sources (capx-D8 charter):

* **registry citation** — the parameter's value is the ISO's registered
  override (``ISOConfig.default_scenario_overrides`` in
  ``src/market_sim/config/iso_configs.py``) or a runner posture read off the
  registry (``scripts/lib/forecast_posture.py``), and the registry entry
  carries a citation comment (rule 5 ``[R-NO-MAGIC]``);
* **derive-script provenance** — the value is produced by a frozen derive
  script from measured source data (rule 23 ``[R-FROZEN-DERIVE]``);
* **published-source intake finding** — a committed finding/handoff documents
  the intake of the value from a published primary source.

A parameter with NO identifiable committed source is listed as
**UNIDENTIFIED** — that is the instrument's point; it is never papered over.
An UNIDENTIFIED entry keeps the literal identification token ``unattested``,
which ``scripts/forecast_verdict.py``'s FC-7 scorer already treats as
not-identified, so **a ledger carrying any UNIDENTIFIED entry scores exactly
as an absent ledger does** (CAVEAT at t1/t2, FAIL at t3). Only a ledger whose
every entry carries a real identification can retire the CAVEAT — and only
when a chartered re-score consumes it; this builder never moves a verdict by
itself.

**History.** Grew out of the FFR-3B FR-27 SKELETON stub (2026-08-02), which
enumerated the same parameters and deliberately attested nothing. The
enumeration scope, grouping, scalar census and the never-improves-a-verdict
property of an unidentified entry are unchanged; what capx-D8 adds
(2026-08-30) is the attribution engine that REPORTS identifications already
committed to the repository. Rule 21 discipline: **the ledger reports
identification, it never supplies one** — every identified row is (a)
mechanically cross-checked against the committed surface it cites (a curated
row whose expected value does not match the run's value is REFUSED, the entry
stays UNIDENTIFIED), and (b) drawn from the curated table below, which cites
committed evidence per row and was reviewed row-by-row in the session that
added it (the same committed-curation pattern as the backcast lane's
``scripts/build_dof_ledger.py``).

**Identification taxonomy** (superset of the backcast lane's, each token's
meaning pinned here):

* ``published`` — read from a published market/physical primary source
  (tariff, ISO planning document, statute, published study);
* ``measured-physical`` — derived from measured physical/behaviour data by a
  frozen derive script (rule 23); admissible under rule 13;
* ``residual`` — chosen (wholly or finally) against a backcast residual;
  MUST carry an open ``root_cause`` (rule 21) or the ledger is malformed;
* ``design-decision`` — a structural/reproducibility posture identified to a
  signed owner decision or a committed decision record (e.g. the D-10
  forecast warm-start posture; the hindcast harness's production-scarcity
  footing). Valid ONLY for non-magnitude values (booleans / selectors): a
  numeric magnitude can never be identified by decision alone, and the
  builder refuses to attach this token to one;
* ``unattested`` — NOT an identification. The token an UNIDENTIFIED entry
  carries so FC-7 keeps scoring it as unproven.

**Scope.** Entries are the NON-DEFAULT solve-affecting ScenarioConfig fields —
the parameters THIS run chose relative to the shipped registry. Registry
defaults themselves (including the backcast-calibrated offer surfaces) carry
their identification burden in the registry's own citations (rule 5) and in
the ISO's backcast keeper DOF ledger (rule 21, backcast lane) — they are not
re-enumerated per forecast bundle; the ledger's ``registry_identification``
block names where that burden lives. Fields whose difference from the HEAD
default is EPOCH DRIFT (the shipped default moved after the run solved —
verified against the run's own recorded git sha) are not free parameters of
the run and are reported in ``epoch_drift``, not scored as entries.

Usage::

    # write the ledger next to a forecast/hindcast run's config
    python scripts/build_forecast_dof_ledger.py results/ff-t1f-s4b-ara/neiso

    # inspect without writing
    python scripts/build_forecast_dof_ledger.py <bundle> --stdout

    # hermetic mode (no git subprocess; epoch drift becomes unverifiable)
    python scripts/build_forecast_dof_ledger.py <bundle> --no-git

    # score a run against it (a chartered re-score, not this lane)
    python scripts/forecast_verdict.py --dof-ledger <bundle>/dof_ledger.json ...

Stdlib + guarded ``market_sim`` config imports only; no LP, no solve, no
model-surface write.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SCHEMA = "dof-ledger/v1"

#: The literal token an UNIDENTIFIED entry carries. It is NOT one of the real
#: identification tokens — FC-7 recognizes it and keeps its CAVEAT/FAIL.
UNATTESTED = "unattested"

#: Real identification tokens this builder may report (see module docstring).
IDENTIFICATION_TOKENS = (
    "published",
    "measured-physical",
    "residual",
    "design-decision",
)

#: Parameter GROUPS the forecast lane carries, each with the question its
#: attestation has to answer. Grouping is what makes the artifact workable: an
#: attester works a group at a time rather than staring at ~700 loose fields.
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
#: year is not a free parameter. Excluded so the ledger stays about tuning.
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
        # Harness-mode markers, same class as `mode`: they say WHICH kind of
        # run this is (a hindcast-harness leg seeded from WHICH EIA-860 fleet
        # snapshot), not how it is tuned.
        "hindcast",
        "eia860_vintage_year",
    }
)

#: A curated-row sentinel: the row applies for any run value (used only where
#: the identification genuinely covers the whole value domain — currently
#: nothing; every live row pins an expected value or requires a registry match).
ANY_VALUE = object()

#: Curated identification rows, keyed ``(iso_or_star, field)`` — the committed,
#: session-reviewed half of the instrument (the ``build_dof_ledger.py``
#: pattern). Each row:
#:
#: * ``identification`` — one of :data:`IDENTIFICATION_TOKENS`;
#: * ``source`` — the primary document/decision identified against;
#: * ``evidence`` — where the committed citation lives (file/finding);
#: * exactly one cross-check gate — ``expected`` (the run value must equal it,
#:   normalized) or ``requires: "iso-registry"`` (the mechanical registry match
#:   must have succeeded for this field). A row whose gate fails is REFUSED and
#:   the entry stays UNIDENTIFIED: curation can never claim a source for a
#:   value that does not match it (rule 21 — report, never supply).
#:
#: Verified in-session capx-D8 (2026-08-30) against the cited surfaces.
CURATED_IDENTIFICATIONS: dict[tuple[str, str], dict] = {
    # --- NEISO scarcity/ORDC registry overrides -------------------------------
    # All six are the ISO-NE-grounded scarcity footing registered in
    # src/market_sim/config/iso_configs.py::_neiso_config
    # default_scenario_overrides, whose cite block names the primary sources
    # quoted per-row below. requires="iso-registry" makes each row apply only
    # when the run value byte-matches the live registered override.
    ("NEISO", "scarcity_price_overlay"): {
        "identification": "published",
        "source": (
            "ISO-NE winter scarcity pricing exists as market design (post-solve "
            "ORDC overlay recovering the reserve-shortage tail the "
            "perfect-foresight LP structurally misses); arming it for NEISO is "
            "the registered production footing"
        ),
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block (ISO-NE Tariff "
            "§III.1.10.1A; FERC Order 831)"
        ),
        "requires": "iso-registry",
    },
    ("NEISO", "ordc_voll"): {
        "identification": "published",
        "source": "ISO-NE Tariff §III.1.10.1A energy offer cap, $2,000/MWh",
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block"
        ),
        "requires": "iso-registry",
    },
    ("NEISO", "ordc_mcl_mw"): {
        "identification": "published",
        "source": (
            "Millstone 3 largest single contingency (~1,233 MW nameplate) — "
            "ISO-NE RSP Table 4.1 / NPCC Directory #1"
        ),
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block"
        ),
        "requires": "iso-registry",
    },
    ("NEISO", "ordc_lolp_sigma_mw"): {
        "identification": "published",
        "source": (
            "ISO-NE Probabilistic Energy Adequacy (PAF) Study 2022 winter "
            "reserve-error std dev, bounded by the 10-min reserve requirement "
            "1,000-1,200 MW"
        ),
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block"
        ),
        "requires": "iso-registry",
    },
    ("NEISO", "ordc_lolp_shift_sigma"): {
        "identification": "published",
        "source": (
            "No administrative ORDC curve shift applies to ISO-NE (the shift is "
            "an ERCOT PUCT instrument); 0.0 is the documented absence, not a "
            "tuned magnitude"
        ),
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block"
        ),
        "requires": "iso-registry",
    },
    ("NEISO", "ordc_multistep_floor"): {
        "identification": "published",
        "source": (
            "No OBDRR048 multi-step floor exists in ISO-NE (ERCOT-specific "
            "market rule); False is the documented absence"
        ),
        "evidence": (
            "src/market_sim/config/iso_configs.py::_neiso_config "
            "default_scenario_overrides cite block"
        ),
        "requires": "iso-registry",
    },
    # --- Hindcast/crossover harness posture ----------------------------------
    ("*", "scarcity_pricing_enabled"): {
        "identification": "design-decision",
        "source": (
            "Harness adoption of each ISO's PRODUCTION scarcity footing (the "
            "master switch engages the ISO's registered "
            "default_scenario_overrides scarcity cell): the capacity screens "
            "must see the same price formation the forecast uses. Root cause "
            "recorded on the s2 run (screens priced against bare "
            "perfect-foresight duals -> 9.7 GW over-retirement, 94% false)"
        ),
        "evidence": (
            "scripts/run_capacity_hindcast.py::build_config docstring; "
            "docs/hindcast-reports/ercot-2021-2025-realized-s2-2026-07-05.md "
            "root cause 1"
        ),
        "expected": True,
        "provenance": "runner-posture",
    },
    # --- Forecast-bundle runner posture --------------------------------------
    ("*", "forecast_xyear_warmstart"): {
        "identification": "design-decision",
        "source": (
            "Owner decision D-10 (signed 2026-08-04, "
            "docs/handoffs/ffr-owner-sitting-2026-08-02.md Addendum K.3): "
            "forecast bundles run cross-year LP warm start OFF so a "
            "killed-and-resumed forecast reproduces from its own cache"
        ),
        "evidence": (
            "market_sim.config.scenarios.FORECAST_BUNDLE_XYEAR_WARMSTART "
            "(the one registry carrier) read through scripts/lib/"
            "forecast_posture.py::shipped_forecast_xyear_warmstart; "
            "measurement docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md"
        ),
        "expected": False,
        "provenance": "runner-posture",
    },
    # --- capx D50 A/B arm posture --------------------------------------------
    ("*", "ccs_retrofit_capex_co2_scaling"): {
        "identification": "design-decision",
        "source": (
            "capx D50 construction repair of the CCS retrofit screen (the "
            "D49 §1.5 seams): the capture island sized to the host's captured "
            "CO2 against the ATB 2024 reference host — captured_ref = "
            "capture_rate × min(HEAT_RATE_BINS[gas_cc]) × "
            "FUEL_CO2_FACTOR_PER_MMBTU[gas_cc] = 0.32319 t/MWh, the host "
            "new_entry._emerging_lcoe already charges the ATB increment "
            "against — and cogeneration (CC_CHP) hosts excluded on the "
            "electric-only cost basis of ATB/NETL. ZERO free parameters: every "
            "term is an existing cited constant; the gate is a construction "
            "choice, never a magnitude"
        ),
        "evidence": (
            "src/market_sim/model/capacity_evolution/ccs.py::"
            "ccs_retrofit_captured_ref_t_per_mwh; "
            "docs/handoffs/FINDING-capx-d49-2026-09-04.md §1.4-§1.5; "
            "docs/handoffs/PREDECL-capx-d50-2026-09-04.md §1; "
            "docs/handoffs/FINDING-capx-d50-2026-09-04.md"
        ),
        "expected": True,
        "provenance": "runner-posture",
    },
}


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


def _norm(value):
    """Normalize a config value for cross-representation comparison.

    A JSON round-trip turns dataclass tuples into lists, so a run_config read
    from disk can never byte-match an in-process default tuple — the FFR-3B
    stub compared raw and mis-listed every tuple-valued field (the six
    ``*_offer_surface_*`` families) as non-default. Tuples normalize to lists,
    dict values normalize recursively, scalars pass through.
    """
    if isinstance(value, tuple):
        return [_norm(v) for v in value]
    if isinstance(value, list):
        return [_norm(v) for v in value]
    if isinstance(value, dict):
        return {k: _norm(v) for k, v in value.items()}
    return value


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


def _iso_registry_overrides(iso: str | None) -> dict:
    """Return the ISO's registered ``default_scenario_overrides``, or ``{}``.

    Guarded like :func:`_defaults`; an empty dict means "no registry surface
    readable", never "the ISO registers nothing" — the ledger's per-entry
    provenance only ever claims a registry match it actually made.
    """
    if not iso:
        return {}
    try:
        sys.path.insert(0, str(REPO / "src"))
        from market_sim.config.iso_configs import get_iso_config  # noqa: PLC0415

        return dict(get_iso_config(iso).default_scenario_overrides or {})
    except Exception:  # noqa: BLE001 — absent/unimportable model stack
        return {}


def _iso_registry_where(iso: str) -> str:
    """Human-readable location of the ISO's override registry."""
    return (
        "ISOConfig.default_scenario_overrides "
        f"(src/market_sim/config/iso_configs.py::_{iso.lower()}_config)"
    )


def _git_show(sha: str, path: str) -> str | None:
    """Return ``path``'s content at ``sha`` via ``git show``, or ``None``.

    Best-effort and read-only. In a blobless partial clone this MAY lazily
    fetch the one blob it names — an intended, bounded download (a single
    source file), unlike the tree-wide resolution the fast-clone doc warns
    about.
    """
    try:
        out = subprocess.run(
            ["git", "show", f"{sha}:{path}"],
            capture_output=True,
            text=True,
            cwd=REPO,
            timeout=60,
            check=False,
        )
    except Exception:  # noqa: BLE001 — no git / no repo / timeout
        return None
    return out.stdout if out.returncode == 0 else None


_FIELD_DEF_RE = r"^\s{{4}}{field}\s*:[^=\n]*=\s*(?P<rhs>.+?)\s*(?:#.*)?$"


def _epoch_default(field: str, sha: str) -> tuple[bool, object, str | None]:
    """Read ``field``'s shipped default from ``scenarios.py`` AT ``sha``.

    Returns ``(resolved, value, source_line)``. ``resolved`` is True only when
    the field's default is a simple literal this parser can honestly evaluate
    (``ast.literal_eval``); a factory/expression default returns ``(False,
    None, source_line)`` so the caller reports "epoch default unparseable"
    instead of guessing. This powers the epoch-drift classification: a run
    value equal to its OWN epoch's shipped default is not a free parameter of
    the run, however far the HEAD default has since moved.
    """
    text = _git_show(sha, "src/market_sim/config/scenarios.py")
    if text is None:
        return False, None, None
    m = re.search(_FIELD_DEF_RE.format(field=re.escape(field)), text, re.M)
    if not m:
        return False, None, None
    line = m.group(0).strip()
    rhs = m.group("rhs")
    try:
        return True, ast.literal_eval(rhs), line
    except (ValueError, SyntaxError):
        return False, None, line


def _run_git_sha(run_config: dict) -> str | None:
    """The solve-time git sha the run_config records, if any."""
    git = run_config.get("git")
    if isinstance(git, dict):
        sha = git.get("sha") or git.get("basis_sha")
        if isinstance(sha, str) and sha:
            return sha
    sha = run_config.get("git_sha") or run_config.get("sha")
    return sha if isinstance(sha, str) and sha else None


def _curated_row(iso: str | None, field: str) -> dict | None:
    """The curated identification row for ``(iso, field)``, ISO-specific first."""
    if iso:
        row = CURATED_IDENTIFICATIONS.get((iso, field))
        if row is not None:
            return row
    return CURATED_IDENTIFICATIONS.get(("*", field))


def _apply_curation(
    entry: dict, value, iso: str | None, registry_matched: bool
) -> None:
    """Fill ``entry`` from its curated row when every cross-check passes.

    Mutates ``entry`` in place. The gates (rule 21 — the ledger reports, it
    never supplies):

    * a ``requires: "iso-registry"`` row applies only when the mechanical
      registry match succeeded for this field;
    * an ``expected`` row applies only when the run value equals it
      (normalized);
    * a ``design-decision`` token never attaches to a numeric magnitude.

    A refused row leaves the entry UNIDENTIFIED and records why, so a stale
    curation surfaces in the artifact instead of silently identifying the
    wrong value.
    """
    row = _curated_row(iso, entry["name"])
    if row is None:
        return
    if row.get("requires") == "iso-registry" and not registry_matched:
        entry["curation_refused"] = (
            "curated row requires an iso-registry value match that failed — "
            "the run value is not the registered override"
        )
        return
    if "expected" in row and row["expected"] is not ANY_VALUE:
        if _norm(value) != _norm(row["expected"]):
            entry["curation_refused"] = (
                f"curated row identifies value {row['expected']!r}, but the "
                f"run carries {value!r} — identification refused"
            )
            return
    ident = row["identification"]
    if (
        ident == "design-decision"
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        entry["curation_refused"] = (
            "design-decision cannot identify a numeric magnitude — refused"
        )
        return
    entry["identification"] = ident
    entry["status"] = "IDENTIFIED"
    entry["source"] = row["source"]
    entry["evidence"] = row["evidence"]
    if row.get("provenance"):
        entry["provenance"] = row["provenance"]
    if row.get("root_cause"):
        entry["root_cause"] = row["root_cause"]


def build_entries(
    sc: dict,
    defaults: dict | None,
    *,
    iso: str | None = None,
    git_sha: str | None = None,
    use_git: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Enumerate + attribute the run's free parameters.

    Returns ``(entries, epoch_drift)``:

    * ``entries`` — one row per solve-affecting parameter the run chose away
      from the shipped registry, each attributed through the chain:
      iso-registry override match → curated identification (cross-checked) →
      UNIDENTIFIED (token ``unattested``);
    * ``epoch_drift`` — fields whose run value differs from the HEAD default
      but EQUALS the shipped default at the run's own recorded sha: shipped
      defaults that moved after the solve, not free parameters of the run.
      Report-only, never scored.

    When ``defaults`` is unavailable every parameterish field is listed and
    the ledger's ``scope`` says so (the FFR-3B posture, unchanged).
    """
    iso = iso or (sc.get("iso") if isinstance(sc.get("iso"), str) else None)
    overrides = _iso_registry_overrides(iso)
    entries: list[dict] = []
    epoch_drift: list[dict] = []
    for field in sorted(sc):
        if field in SCENARIO_SELECTORS or field.startswith("_"):
            continue
        value = sc[field]
        if not _is_parameterish(value):
            # A None where HEAD ships a parameterish default is epoch context
            # worth reporting (the field's default moved after the run solved,
            # e.g. a by-ISO map growing a default_factory) — but a None is
            # never a tuned magnitude, so it is report-only, never an entry.
            if (
                value is None
                and defaults is not None
                and defaults.get(field) is not None
            ):
                drift = {
                    "name": field,
                    "run_value": None,
                    "head_default": _norm(defaults[field]),
                    "note": (
                        "run carries null where HEAD ships a non-null "
                        "default. Cause not mechanically established — a "
                        "moved default, or a runner-passed posture (a runner "
                        "may explicitly null a field, e.g. run_full_horizon's "
                        "non-golden cmc_by_iso=None); see the run's finding"
                    ),
                }
                if use_git and git_sha:
                    resolved, epoch_value, line = _epoch_default(field, git_sha)
                    if resolved and epoch_value is None:
                        drift["epoch_default_at"] = git_sha
                        drift["epoch_source_line"] = line
                        drift["note"] = (
                            "run value equals the shipped default at the "
                            "run's own sha (null) — the HEAD default moved "
                            "after the solve; not a free parameter of this run"
                        )
                    elif line is not None:
                        drift["epoch_source_line"] = line
                        drift["note"] = (
                            "run carries null; the field's definition at the "
                            "run's own sha is quoted but not mechanically "
                            "evaluable (factory/expression), so the null is "
                            "either that epoch's resolution or a "
                            "runner-passed posture — see the run's finding"
                        )
                epoch_drift.append(drift)
            continue
        if (
            defaults is not None
            and field in defaults
            and _norm(value) == _norm(defaults[field])
        ):
            continue

        registry_matched = field in overrides and _norm(value) == _norm(
            overrides[field]
        )

        # Epoch drift: only worth checking when nothing else explains the
        # value — a registry/curation match is a stronger, cheaper answer.
        if (
            not registry_matched
            and _curated_row(iso, field) is None
            and defaults is not None
            and use_git
            and git_sha
        ):
            resolved, epoch_value, line = _epoch_default(field, git_sha)
            if resolved and _norm(value) == _norm(epoch_value):
                epoch_drift.append(
                    {
                        "name": field,
                        "run_value": value,
                        "head_default": _norm(defaults.get(field)),
                        "epoch_default_at": git_sha,
                        "epoch_source_line": line,
                        "note": (
                            "run value equals the shipped default at the "
                            "run's own sha — the HEAD default moved after "
                            "the solve; not a free parameter of this run"
                        ),
                    }
                )
                continue

        group, question = _group_of(field)
        entry = {
            "name": field,
            "where": (
                _iso_registry_where(iso)
                if registry_matched and iso
                else "ScenarioConfig"
            ),
            "group": group,
            "identification": UNATTESTED,
            "status": "UNIDENTIFIED",
            "source": "",
            "evidence": "",
        }
        if registry_matched:
            entry["provenance"] = "iso-registry"
        n = _count_scalars(value)
        if n:
            entry["n_scalars"] = n
        if isinstance(value, (bool, int, float)):
            entry["value"] = value

        _apply_curation(entry, value, iso, registry_matched)

        if entry["status"] == "UNIDENTIFIED":
            entry["attestation_question"] = question
        entries.append(entry)
    return entries, epoch_drift


def _epoch_field_gaps(sc: dict, defaults: dict | None) -> dict:
    """Fields added to / removed from ScenarioConfig since the run's epoch.

    Report-only context: a field present in the HEAD defaults but absent from
    the run's dump did not exist when the run solved (the run used the
    then-shipped behaviour); the reverse marks a field since deleted. Neither
    is a free parameter of the run.
    """
    if defaults is None:
        return {}
    added = sorted(f for f in defaults if f not in sc)
    removed = sorted(f for f in sc if f not in defaults and not f.startswith("_"))
    out = {}
    if added:
        out["fields_added_since_epoch"] = added
    if removed:
        out["fields_removed_since_epoch"] = removed
    return out


def _registry_identification(iso: str | None) -> dict | None:
    """Name where the registry defaults' own identification burden lives.

    The entries above cover the run's deviations; the shipped registry values
    the run inherited (offer surfaces, floors, sigmoids, ...) are identified
    in the registry's rule-5 citations and in the ISO's designated backcast
    keeper's rule-21 DOF ledger. This block records the keeper designation at
    build time so a reader can follow the chain; it asserts nothing about the
    keeper's content.
    """
    if not iso:
        return None
    shard = REPO / "frontend" / "data" / "backcast" / "keepers" / f"{iso}.json"
    keeper = None
    try:
        data = json.loads(shard.read_text())
        keeper = data.get("keeper") or data.get("keeper_id")
        if keeper is None and isinstance(data.get("keepers"), list):
            first = next(iter(data["keepers"]), None)
            if isinstance(first, dict):
                keeper = first.get("id") or first.get("run_id")
    except Exception:  # noqa: BLE001 — absent/unreadable shard
        return None
    if not keeper:
        return None
    return {
        "note": (
            "Registry defaults inherited by this run (offer surfaces, "
            "floors, passthrough sigmoids, ...) carry their identification "
            "in the registry's rule-5 citations and in the designated "
            "backcast keeper's rule-21 DOF ledger "
            "(calibration_attestation.json `free_parameters`); they are not "
            "re-enumerated per forecast bundle. Whether each identification "
            "survives extrapolation forward is the standing question the "
            "dispatch_mechanism group's guidance records."
        ),
        "backcast_keeper_at_build": keeper,
        "keeper_shard": str(shard.relative_to(REPO)),
    }


def build_ledger(
    run_config: dict,
    *,
    run_id: str | None = None,
    use_git: bool = True,
) -> dict:
    """Assemble the forecast DOF ledger from a run_config artifact."""
    sc = _scenario_config(run_config)
    iso = sc.get("iso") if isinstance(sc.get("iso"), str) else None
    defaults = _defaults()
    git_sha = _run_git_sha(run_config)
    entries, epoch_drift = build_entries(
        sc, defaults, iso=iso, git_sha=git_sha, use_git=use_git
    )
    by_group: dict[str, int] = {}
    for e in entries:
        by_group[e["group"]] = by_group.get(e["group"], 0) + 1
    n_unidentified = sum(1 for e in entries if e["identification"] == UNATTESTED)
    n_identified = len(entries) - n_unidentified
    if not entries:
        status = "INSTRUMENT — NO RUN-CHOSEN FREE PARAMETERS ENUMERATED"
    elif n_unidentified == 0:
        status = f"INSTRUMENT — ALL {len(entries)} ENTRIES IDENTIFIED"
    elif n_identified == 0:
        status = f"INSTRUMENT — ALL {len(entries)} ENTRIES UNIDENTIFIED"
    else:
        status = (
            f"INSTRUMENT — {n_identified} IDENTIFIED / {n_unidentified} UNIDENTIFIED"
        )
    ledger = {
        "schema": SCHEMA,
        "lane": "forecast",
        "status": status,
        "run_id": run_id,
        "iso": iso,
        "run_git_sha": git_sha,
        "generated_by": (
            "scripts/build_forecast_dof_ledger.py (capx-D8, 2026-08-30) — the "
            "FC-7 DOF-ledger instrument, grown from the FFR-3B FR-27 skeleton. "
            "It REPORTS identifications committed to the repository (rule 21); "
            "it never supplies one. An UNIDENTIFIED entry keeps the "
            "`unattested` token and FC-7 keeps its CAVEAT."
        ),
        "how_to_fill": (
            "Per UNIDENTIFIED entry: add a curated row to "
            "CURATED_IDENTIFICATIONS in scripts/build_forecast_dof_ledger.py "
            "citing committed evidence (registry citation, frozen derive "
            "script, or published-source intake finding), with its expected "
            "value or registry cross-check, then regenerate the ledger. A "
            "`residual` identification MUST carry `root_cause` naming an OPEN "
            "issue (CLAUDE.md rule 21 [R-DOF]). dispatch_mechanism entries "
            "should CITE the ISO's backcast keeper ledger entry and state "
            "whether the identification survives extrapolation forward. Never "
            "hand-edit the emitted JSON: the curated table is the reviewed, "
            "committed surface."
        ),
        "verdict_effect": (
            "None from emission alone — this lane re-scores nothing. On a "
            "chartered FC-7 re-score: any UNIDENTIFIED entry keeps the same "
            "CAVEAT an absent ledger draws (forecast_verdict.py treats "
            "`unattested` as not-identified); only a ledger whose every entry "
            "carries a real identification can retire it."
        ),
        "scope": (
            "NON-DEFAULT solve-affecting ScenarioConfig fields — the "
            "parameters THIS run chose relative to the shipped registry "
            "(tuple/list representation normalized). Registry defaults "
            "inherited by the run keep their identification burden in the "
            "registry citations and the backcast keeper DOF ledger (see "
            "registry_identification). Epoch drift is reported separately, "
            "never scored."
            if defaults is not None
            else "EVERY parameterish ScenarioConfig field: the default config "
            "could not be imported, so default-valued fields could not be "
            "excluded and the list is WIDER than the run's real free "
            "parameters. Re-run where market_sim imports to narrow it."
        ),
        "defaults_available": defaults is not None,
        "n_entries": len(entries),
        "n_identified": n_identified,
        "n_unidentified": n_unidentified,
        # Scorer/back-compat alias: forecast_verdict counts `unattested`
        # tokens; the two numbers are the same census.
        "n_unattested": n_unidentified,
        "n_by_group": dict(sorted(by_group.items())),
        "entries": entries,
    }
    recon = run_config.get("reconstruction")
    if isinstance(recon, dict):
        # A ledger built from a RECONSTRUCTED run_config inherits that label:
        # it enumerates the reconstruction's parameters, and its honesty is
        # bounded by the reconstruction's own evidence chain.
        ledger["basis"] = (
            "RECONSTRUCTED run_config — "
            + str(recon.get("status", "see the run_config's reconstruction block"))
            + "; evidence chain and verification in the sibling "
            "run_config.json `reconstruction` block"
        )
    if epoch_drift:
        ledger["epoch_drift"] = epoch_drift
    gaps = _epoch_field_gaps(sc, defaults)
    if gaps:
        ledger["epoch_field_gaps"] = gaps
    reg = _registry_identification(iso)
    if reg:
        ledger["registry_identification"] = reg
    return ledger


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
    """CLI entry point: build and write (or print) one bundle's DOF ledger."""
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
    ap.add_argument(
        "--no-git",
        action="store_true",
        help=(
            "skip the git epoch-default check (hermetic mode; epoch drift "
            "then stays in entries as UNIDENTIFIED rather than being "
            "classified)"
        ),
    )
    args = ap.parse_args(argv)

    run_config, src = _load_run_config(args.bundle)
    run_id = (
        run_config.get("run_id")
        or (run_config.get("meta") or {}).get("run_id")
        or (args.bundle.name if args.bundle.is_dir() else None)
    )
    ledger = build_ledger(run_config, run_id=run_id, use_git=not args.no_git)

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
        f"[dof-ledger] wrote {out} from {src.name}: "
        f"{ledger['n_entries']} entries — {ledger['n_identified']} identified, "
        f"{ledger['n_unidentified']} UNIDENTIFIED ({ledger['n_by_group']}). "
        "An UNIDENTIFIED entry keeps FC-7's CAVEAT.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
