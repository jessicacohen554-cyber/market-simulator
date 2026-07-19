"""Single home for the holdout-quarantine policy constants (CLAUDE.md rule 22).

``CALIBRATION_YEARS`` is the in-sample training window (2023-2025) — the ONLY
years tuned against (rule 22 train/validation/locked-test split). Any solve,
score, or registration touching a year outside it is a designated holdout (2022,
2019, H1-2026, <=2021) and is gated on a per-ISO calibration-complete marker.
``MARKER_FILE`` is that marker's repo-relative path (its ``complete`` block
authorizes an ISO's one-shot frozen-config holdout score).

Imported by the three rule-22 gates so the window and marker path are defined
exactly once instead of triplicated behind a cross-file parity test:

  * ``run_calibration_full.enforce_holdout_year_gate`` (the ``--year`` gate),
  * ``legitimacy_diagnostics.run_d6_quarantine`` (the ``--keepers`` CI gate),
  * ``audit_keepers`` (the H1 governance gate).

Stdlib-only (no imports) — consumed by the deploy/CI paths that run on a bare
``python3``.
"""

from __future__ import annotations

CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})

# Repo-relative path (POSIX form). Consumers join it onto the repo root
# (``repo / MARKER_FILE``) or wrap it in a Path for ``.name`` — a plain string
# so both the message text and the join are identical across the three gates.
MARKER_FILE: str = "frontend/data/backcast/calibration-complete.json"
