"""Registry of backcast runs whose payload + bundle were never committed to git.

These are INCOMPLETE registrations: the registry sidecar
(``frontend/data/backcast/registry/<id>.json``) landed on the tree, but the
dashboard payload (``frontend/data/backcast/runs/<id>.js``) and the solve
bundle (``results/calibration/<bundle>/``) never did. Verified 2026-07-20:
each id below appears in **0 commits** anywhere in history, and its source
bundle is absent or metrics-only on the tree, so the payload cannot be
regenerated in-session (that needs a re-solve, which the CI-cost policy and
rule 12 keep out of this lane).

Two of them are current ISO keepers (NYISO ``nyiso-65-scr-edrp``, NEISO
``neiso-60-phantom-outage``); the other two are stale NYISO probes.

The three quarantine gates (``check_registry_payload_parity``,
``audit_keepers``, ``legitimacy_diagnostics --keepers``) consult this set so
the pre-existing condition is reported as an explicit, tracked WARNING instead
of a hard failure or an outright crash — letting the restored CI land on the
current tree while EVERY OTHER parity/keeper break still fails loudly. This is
deliberately NOT a blanket ignore: only these exact ids are tolerated, and only
for the artifact-absent failure class they cause.

RESOLUTION (owner follow-up, tracked in the phase-refactor/ci-restoration PR and
docs/handoffs/backcast-artifacts-refactor-remaining-2026-07.md): re-sync the
missing bundles + payloads (re-solve the keeper span and re-register via the
``calibration-report`` skill), or re-point the NYISO/NEISO keeper shards to a run
whose artifacts are committed. Delete each id from this set the moment its
payload lands — a stale entry here is a re-armable hole in the gate.
"""

from __future__ import annotations

# runs/<id>.js payloads that are absent from git (sidecar-only registrations).
UNSYNCED_RUN_PAYLOADS: frozenset[str] = frozenset(
    {
        "2026-07-13-neiso-60-phantom-outage",  # NEISO keeper; bundle metrics-only
        "2026-07-13-nyiso-63-phantom-outage",  # probe; bundle absent
        "2026-07-13-nyiso-64-outage-refix",  # probe; bundle metrics/attestation only
        "2026-07-19-nyiso-65-scr-edrp",  # NYISO keeper; bundle absent
    }
)

# The subset that are designated ISO keepers — the scope audit_keepers /
# legitimacy_diagnostics --keepers iterate. Every artifact-absent finding on
# these is a consequence of the un-committed bundle, so the keeper gates
# downgrade them to warnings rather than failing/crashing.
UNSYNCED_KEEPERS: frozenset[str] = frozenset(
    {
        "2026-07-13-neiso-60-phantom-outage",
        "2026-07-19-nyiso-65-scr-edrp",
    }
)
