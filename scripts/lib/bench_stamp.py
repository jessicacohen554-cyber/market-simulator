"""Builder fingerprint for the per-(ISO, year) benchmark parts.

THE DEFECT THIS CLOSES (nyiso-148, 2026-08-21; owner ruling "sweep and fix the
mechanism"). A benchmark part is refreshed only when a registering bundle
happens to carry the benchmark inputs, so a committed part can sit
un-refreshed while the builder that produces it moves underneath — silently,
because the parts are byte-deterministic and therefore show no git diff until
something regenerates them. NYISO's part went un-refreshed from 2026-08-17;
regenerating it moved CC_REGULAR-2024's metered actual by ~4 TWh and flipped
EVERY registered NYISO run to NOT-YET, the keeper included
(``results/calibration/FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md``).

THE STAMP. Each part carries ``meta.builderFingerprint`` — a short hash over
the SOURCE of the scripts that compute and write it. A part whose fingerprint
differs from the current one **provably predates the builder at HEAD**, so a
verdict scored against it is not reproducible from the code that would produce
it now.

WHY THE FINGERPRINT IS CONTENT-DERIVED ONLY. The parts must stay
byte-deterministic — "rewriting identical content yields identical bytes" is
what keeps concurrent registrations conflict-free and keeps unchanged parts out
of every diff. A timestamp or a HEAD sha in the stamp would rewrite every part
on every registration and destroy that property. Hashing the builder source
keeps it: same code + same data ⇒ same bytes.

WHAT IT DELIBERATELY DOES NOT COVER. The builder imports the engine
(``src/market_sim/``) for the plant→class map, the CHP shares and the EIA-923
reconciliation, and those move far more often than the scripts do. Folding them
into the hash would mark every part stale after any lane's edit and the signal
would be ignored within a week. That exposure is real and is reported
SEPARATELY, as a count of intervening engine commits, by
``scripts/check_bench_freshness.py`` — a warning, not a gate.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: The scripts that compute and write a bench part's payload. Order-stable so
#: the hash is reproducible; a missing file is hashed as absent rather than
#: skipped, so deleting one still moves the fingerprint.
BUILDER_SOURCES: tuple[str, ...] = (
    "scripts/render_calibration_html.py",
    "scripts/render_backcast.py",
    "scripts/lib/backcast_artifacts.py",
    "scripts/lib/bench_stamp.py",
)

#: Length of the hex digest carried in the part. 12 hex chars ≈ 48 bits — far
#: beyond collision range for a handful of source files, and short enough to
#: read in a diff.
_DIGEST_CHARS: int = 12


def builder_fingerprint() -> str:
    """Return the current builder fingerprint (12 hex chars).

    Hashes the byte content of :data:`BUILDER_SOURCES` in order, each prefixed
    by its path and length so a rename or a truncation cannot collide with an
    edit.
    """
    h = hashlib.sha256()
    for rel in BUILDER_SOURCES:
        p = REPO / rel
        data = p.read_bytes() if p.exists() else b""
        h.update(rel.encode())
        h.update(str(len(data)).encode())
        h.update(data)
    return h.hexdigest()[:_DIGEST_CHARS]


def part_fingerprint(part_obj: dict) -> str | None:
    """Return the fingerprint a loaded bench part carries, or ``None``.

    ``None`` means the part predates the stamp entirely — which is itself a
    staleness signal, and is reported as such rather than tolerated.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    fp = (part_obj or {}).get("meta", {}).get("builderFingerprint")
    return str(fp) if fp else None


def is_stale(part_obj: dict) -> bool:
    """Return True when *part_obj* was not written by the builder at HEAD.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    return part_fingerprint(part_obj) != builder_fingerprint()
