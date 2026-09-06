"""Single home for the forecast-invariant declared-failure ledger policy.

The ledger ``frontend/data/hindcast/invariant-failures.json`` is the file that
makes a registered forecast run's invariant FAIL a *reviewed line* rather than a
number that lands on the forecast dashboard unremarked. Two consumers read it,
and before lane Y-24 they did not exist as a pair:

  * ``scripts/check_forecast_invariants.py --sidecar-dir`` — the CI job
    ``forecast-invariant-artifacts``, which audits every already-committed
    sidecar. It is a **detector**: it goes red after the fact.
  * ``scripts/register_forecast_run.py`` — the single registration seam, which
    since Y-24 REFUSES a registration whose sidecar carries an undeclared FAIL.
    It is the **ratchet**: it stops the inflow.

Both now answer "which FAILs does this run carry, and which of them does the
ledger cover?" out of this module, so the detector and the ratchet can never
disagree about it — the same one-policy-module construction
``scripts/lib/holdout_policy.py`` gives the two rule-22 marker gates
(``dashboard_add_run.enforce_registration_marker_gate`` /
``run_calibration_full.enforce_holdout_year_gate``). Like that module this one
is **stdlib-only and import-free of the model**: ``register_forecast_run.py``'s
``--reindex`` IS the Pages deploy assembly step and runs under a bare
``python3`` with no dependencies installed (``.github/workflows/deploy-pages.yml``),
so anything it imports at module scope must not reach numpy or ``market_sim``.
Consumers do their own file read via :func:`load_ledger`.

WHY A RATCHET, AND WHY IT HAS A BASELINE
----------------------------------------
The audit job is a detector with no enforcement at the seam that creates the
problem: ``register_forecast_run.py`` had no declaration check at all, so a lane
could land a sidecar carrying FAILs and nothing refused it. The backlog of
undeclared runs consequently regressed 4 -> 16 -> 17 -> 20; lane Y-19 declared
16 of 20 and was already behind before it merged, because four more registered
while it worked.

So the ledger carries two independent blocks:

  ``declared_failures``               {run_id: [ident, ...]} — an ADJUDICATION.
      The registering desk states the FAIL is understood and names the finding
      that owns it. Read by BOTH consumers.
  ``registration_ratchet_baseline``   {run_id: [ident, ...]} — NOT an
      adjudication, and deliberately not one. It records the (run, ident) pairs
      that were ALREADY registered when the ratchet landed, so the ratchet gates
      **inflow only** and changes no already-registered run. Read by the
      REGISTRATION RATCHET ONLY: :func:`undeclared_failures` ignores it unless
      the caller opts in, so the CI audit stays RED on the whole backlog and the
      routing keeps its teeth. Declaring an undiagnosed FAIL is precisely the
      silent landing the gate exists to prevent (Y-19's ruling), and a baseline
      entry must never be mistaken for one.

The baseline may only SHRINK — the same property the Y-20 mechanism-matrix gap
ratchet has (``check_mechanism_matrix.gap_ratchet``). A new run id is never in
it, so inflow is gated; and :func:`stale_baseline_entries` turns an entry that
has been superseded (the run improved, the run's sidecar is gone, or a desk
finally declared it) into an audit problem, so closing a backlog row also prunes
its baseline line instead of leaving dead weight behind.

Genealogy: ``docs/handoffs/FINDING-y24-invariant-declaration-ratchet-2026-09-06.md``.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path

# Repo-relative path of the ledger. Value-equal to
# ``check_forecast_invariants``'s ``--failure-ledger`` default and to
# ``register_forecast_run``'s gate default; both resolve it against their own
# repo root, so this module never has to know where the checkout lives.
LEDGER_FILE: str = "frontend/data/hindcast/invariant-failures.json"

# The adjudication block: {run_id: [ident, ...]}, written by the registering
# desk in the same commit as the registration.
DECLARED_KEY: str = "declared_failures"

# The inflow-ratchet baseline: {run_id: [ident, ...]} of pairs that predate the
# ratchet. Forgiven by the REGISTRATION gate only, never by the CI audit.
BASELINE_KEY: str = "registration_ratchet_baseline"

# The status string the checker writes for a failing invariant. Duplicated
# rather than imported: importing ``check_forecast_invariants`` for it would
# drag numpy and ``market_sim`` into the stdlib-only deploy path. A parity test
# asserts the two agree (tests/scoring/test_invariant_declaration_ratchet.py).
FAIL: str = "FAIL"


def load_ledger(repo: Path, ledger_path: Path | None = None) -> dict:
    """Read the declared-failure ledger; an absent file is an empty ledger.

    Args:
        repo: Repo root, used to resolve :data:`LEDGER_FILE`.
        ledger_path: Explicit ledger path, overriding the default.

    Returns:
        The parsed ledger document, or ``{}`` when the file does not exist.

    Raises:
        ValueError: if the file exists but is not valid JSON. A ledger that
            cannot be read is never silently treated as empty — that would turn
            the ratchet off exactly when the file is broken.
    """
    path = ledger_path if ledger_path is not None else repo / LEDGER_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def fail_idents(sidecar: Mapping) -> list[str]:
    """Return the sorted, de-duplicated FAIL idents of one sidecar.

    Reads the sidecar's committed ``invariants`` block exactly as the CI audit
    does. A gate/crossover sidecar stores only its non-PASS rows, so the FAILs
    are present there too and this reads them identically.

    Args:
        sidecar: A canonical ``frontend/data/hindcast/<id>.json`` document (or
            the in-memory dict a builder just produced).

    Returns:
        Sorted unique idents whose status is ``FAIL``; empty when the sidecar
        carries no ``invariants`` list (a scoring-only registration).
    """
    records = sidecar.get("invariants")
    if not isinstance(records, list):
        return []
    return sorted(
        {
            rec["ident"]
            for rec in records
            if isinstance(rec, Mapping)
            and rec.get("status") == FAIL
            and rec.get("ident")
        }
    )


def _block(ledger: Mapping, key: str) -> dict:
    """Return ledger block ``key`` as a dict, tolerating an absent/odd value."""
    value = ledger.get(key)
    return value if isinstance(value, Mapping) else {}


def covered_idents(
    run_id: str, ledger: Mapping, *, include_baseline: bool = False
) -> set[str]:
    """Idents the ledger covers for ``run_id``.

    Args:
        run_id: The run's id.
        ledger: The parsed ledger document.
        include_baseline: Whether :data:`BASELINE_KEY` counts as coverage. The
            CI audit passes ``False`` (a baselined row stays RED, so routing
            keeps its teeth); the registration ratchet passes ``True`` (it gates
            inflow, not somebody else's backlog).

    Returns:
        The covered idents, possibly empty.
    """
    covered = set(_block(ledger, DECLARED_KEY).get(run_id, ()))
    if include_baseline:
        covered |= set(_block(ledger, BASELINE_KEY).get(run_id, ()))
    return covered


def undeclared_failures(
    run_id: str,
    idents: Iterable[str],
    ledger: Mapping,
    *,
    include_baseline: bool = False,
) -> list[str]:
    """The FAIL idents of ``run_id`` that ``ledger`` does not cover.

    Args:
        run_id: The run's id.
        idents: The run's FAIL idents (from :func:`fail_idents`).
        ledger: The parsed ledger document.
        include_baseline: See :func:`covered_idents`.

    Returns:
        The uncovered idents, in the order given (callers pass a sorted list).
    """
    covered = covered_idents(run_id, ledger, include_baseline=include_baseline)
    return [i for i in idents if i not in covered]


def registration_refusals(sidecar: Mapping, ledger: Mapping) -> list[str]:
    """Return why this sidecar may not be REGISTERED (empty = it may).

    The ratchet half of the invariant-declaration policy, and the mirror of
    ``holdout_policy.registration_refusals``: the caller turns a non-empty
    result into a refusal and writes nothing. The baseline IS honoured here —
    the ratchet exists to stop new undeclared FAILs, not to hold a lane
    responsible for the standing backlog.

    A sidecar with no ``run_id`` is not refused: there is nothing to key a
    declaration on, and the registration paths always set one (the ``--reindex``
    path skips such a file outright). Malformed sidecars are the CI audit's
    business, not this gate's.

    Args:
        sidecar: The canonical sidecar about to be written.
        ledger: The parsed ledger document.

    Returns:
        Human-readable refusal lines; empty when the registration may proceed.
    """
    run_id = sidecar.get("run_id") or sidecar.get("id")
    if not run_id:
        return []
    undeclared = undeclared_failures(
        run_id, fail_idents(sidecar), ledger, include_baseline=True
    )
    if not undeclared:
        return []
    return [
        f"{run_id}: invariant FAIL(s) {undeclared} are not declared in {LEDGER_FILE}.",
        f'The remedy is the declaration: add "{run_id}": '
        f"{json.dumps(sorted(set(undeclared)))} under `{DECLARED_KEY}` in the "
        "same commit as this registration, and name the finding that owns the "
        "FAIL in your findings doc.",
    ]


def stale_baseline_entries(
    observed_failures: Mapping[str, Iterable[str]], ledger: Mapping
) -> list[tuple[str, list[str], str]]:
    """Baseline rows that no longer earn their place, for the CI audit.

    The baseline may only shrink. A row is stale when the run it names is gone,
    when the ident no longer FAILs (the defect was fixed), or when a desk has
    since DECLARED it — in that last case the declaration is the real record and
    the baseline line is dead weight that would silently forgive a future
    regression on the same ident.

    Args:
        observed_failures: ``{run_id: fail idents}`` over every audited sidecar
            that carries an ``invariants`` block.
        ledger: The parsed ledger document.

    Returns:
        ``(run_id, idents, reason)`` triples; empty when the baseline is clean.
    """
    out: list[tuple[str, list[str], str]] = []
    for run_id, idents in sorted(_block(ledger, BASELINE_KEY).items()):
        listed = sorted(set(idents))
        if run_id not in observed_failures:
            out.append(
                (run_id, listed, "no sidecar carrying invariants (the run is gone)")
            )
            continue
        failing = set(observed_failures[run_id])
        gone = [i for i in listed if i not in failing]
        if gone:
            out.append((run_id, gone, "no longer FAIL (the run improved)"))
        declared = set(_block(ledger, DECLARED_KEY).get(run_id, ()))
        both = [i for i in listed if i in declared]
        if both:
            out.append(
                (
                    run_id,
                    both,
                    f"now also declared under `{DECLARED_KEY}`, which is the "
                    "real record",
                )
            )
    return out
