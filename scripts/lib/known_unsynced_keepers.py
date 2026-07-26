"""Registry of backcast runs whose payload + bundle were never committed to git.

These are INCOMPLETE registrations: the registry sidecar
(``frontend/data/backcast/registry/<id>.json``) landed on the tree, but the
dashboard payload (``frontend/data/backcast/runs/<id>.js``) — and for most,
the solve bundle (``results/calibration/<bundle>/``) — never did. Verified
2026-07-26 for every id below: the payload appears in **0 commits** reachable
from any remote ref, and the render inputs ``render_calibration_html.
build_payload`` needs (the bundle's gitignored ``dispatch/<year>_P*.parquet``
+ ``system.parquet`` — deliberately never committed, .gitignore §8) exist
nowhere, so the payload cannot be regenerated in-session: that needs a
re-solve, which the CI-cost policy and rule 12 keep out of this lane.

The tracked id is the surviving casualty of the API-only push rule (see
``docs/handoffs/dashboard-payload-push-gap-2026-07.md``): its session could
push the small sidecar via ``push_files`` but not the 400 KB–1 MB payload
(over the ~457 KB per-payload cap), and the local commit died with the
ephemeral container. The rule was amended 2026-07-26 (CLAUDE.md
"Git & Pushing": payloads now go over small-pack ``git push``), so this class
of stranding is closed going forward. The other eight casualties of the same
window (caiso-112, caiso-114, pjm-116, pjm-117, pjm-118, pjm-119,
neiso-62-opcap-a0/a1 — all superseded probes or a lineage superseded by the
pjm-121 keeper) were PRUNED 2026-07-26 on owner decision via the three-store
retention semantics (sidecar + bundle; no payload ever existed).

The three quarantine gates (``check_registry_payload_parity``,
``audit_keepers``, ``legitimacy_diagnostics --keepers``) consult this set so
the pre-existing condition is reported as an explicit, tracked WARNING instead
of a hard failure or an outright crash — letting CI stay green on the current
tree while EVERY OTHER parity/keeper break still fails loudly. This is
deliberately NOT a blanket ignore: only these exact ids are tolerated, and only
for the artifact-absent failure class they cause.

RESOLUTION (owner decision 2026-07-26, recorded in
``docs/handoffs/dashboard-payload-push-gap-2026-07.md``): the NEISO 2022
holdout validation run is AUTHORIZED for a re-solve in a solve-capable
session (``--holdout-authorized``, rule 22 validation tier, session-logged);
re-register via the ``calibration-report`` skill, push the payload over
``git push``, and delete the id here the moment it lands — a stale entry is
a re-armable hole in the gate.

Prior entries, all resolved: ``2026-07-13-neiso-60-phantom-outage`` (payload
since landed on the tree; no longer the NEISO keeper), ``2026-07-13-nyiso-63-
phantom-outage`` + ``2026-07-13-nyiso-64-outage-refix`` (sidecars retired from
the registry), ``2026-07-19-nyiso-65-scr-edrp`` (retired 2026-07-20, keeper
re-pointed to 2026-07-20-nyiso-66-resync-base), ``2026-07-24-miso-83-netrev-
margin`` (retired 2026-07-24, keeper re-solved as miso-85 with artifacts
committed; see docs/calibration-log/miso.md).
"""

from __future__ import annotations

# runs/<id>.js payloads that are absent from git (sidecar-only registrations).
# Bundle state verified 2026-07-26 at main 19b0b91 (see module docstring for
# why this cannot render without a re-solve).
UNSYNCED_RUN_PAYLOADS: frozenset[str] = frozenset(
    {
        # Bundle metrics-only; NEISO validation-tier (2022 holdout) record.
        # Re-solve authorized 2026-07-26 (owner) — see module docstring.
        "2026-07-23-neiso-2022-holdout-validation",
    }
)

# The subset that are designated ISO keepers — the scope audit_keepers /
# legitimacy_diagnostics --keepers iterate. Every artifact-absent finding on
# these is a consequence of the un-committed bundle, so the keeper gates
# downgrade them to warnings rather than failing/crashing. Empty since
# 2026-07-26: every current keeper shard points at a run whose payload is
# committed (PJM moved off payload-less pjm-119 to pjm-121 on 2026-07-25).
UNSYNCED_KEEPERS: frozenset[str] = frozenset()
