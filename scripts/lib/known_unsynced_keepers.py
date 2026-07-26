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

All nine ids are the 2026-07-22 → 2026-07-24 casualties of the API-only push
rule (see ``docs/handoffs/dashboard-payload-push-gap-2026-07.md``): their
sessions could push the small sidecar via ``push_files`` but not the
400 KB–1 MB payload (over the ~457 KB per-payload cap), and the local commits
died with the ephemeral containers. The rule was amended 2026-07-26 (CLAUDE.md
"Git & Pushing": payloads now go over small-pack ``git push``), so this class
of stranding is closed going forward.

The three quarantine gates (``check_registry_payload_parity``,
``audit_keepers``, ``legitimacy_diagnostics --keepers``) consult this set so
the pre-existing condition is reported as an explicit, tracked WARNING instead
of a hard failure or an outright crash — letting CI stay green on the current
tree while EVERY OTHER parity/keeper break still fails loudly. This is
deliberately NOT a blanket ignore: only these exact ids are tolerated, and only
for the artifact-absent failure class they cause.

RESOLUTION (owner follow-up, tracked in
``docs/handoffs/dashboard-payload-push-gap-2026-07.md``): per id, either
re-solve its full rule-16 year span in a solve-capable session, re-register via
the ``calibration-report`` skill and push the payload over ``git push``; or,
for superseded probes, prune the sidecar under retention
(``dashboard_add_run.py``'s three-store prune). Delete each id from this set
the moment its payload lands or its sidecar is pruned — a stale entry here is
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
# why none of these can render without a re-solve).
UNSYNCED_RUN_PAYLOADS: frozenset[str] = frozenset(
    {
        "2026-07-22-caiso-112-export-floor",  # bundle metrics-only
        "2026-07-23-caiso-114-endogenous-west",  # bundle metrics-only
        "2026-07-23-neiso-2022-holdout-validation",  # bundle metrics-only
        "2026-07-23-pjm-116-netrev-base",  # bundle absent (0 commits)
        "2026-07-23-pjm-117-netrev-margin",  # bundle absent (0 commits)
        "2026-07-24-neiso-62-opcap-a0",  # bundle absent (0 commits)
        "2026-07-24-neiso-62-opcap-a1",  # bundle absent (0 commits)
        "2026-07-24-pjm-118-netrev-level",  # slim bundle; no dispatch/system parquet
        "2026-07-24-pjm-119-overlay-restore",  # slim bundle; no dispatch/system
        # parquet. Ex-PJM-keeper: superseded 2026-07-25 by pjm-121-cc-belt
        # (payload committed), so no keeper is payload-less today.
    }
)

# The subset that are designated ISO keepers — the scope audit_keepers /
# legitimacy_diagnostics --keepers iterate. Every artifact-absent finding on
# these is a consequence of the un-committed bundle, so the keeper gates
# downgrade them to warnings rather than failing/crashing. Empty since
# 2026-07-26: every current keeper shard points at a run whose payload is
# committed (PJM moved off payload-less pjm-119 to pjm-121 on 2026-07-25).
UNSYNCED_KEEPERS: frozenset[str] = frozenset()
