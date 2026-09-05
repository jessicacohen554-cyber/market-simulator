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

WHY THE HASH IS OVER THE **AST**, NOT THE RAW BYTES (owner ruling **R-AS**,
2026-09-05, adopting Proposal A of
``docs/handoffs/FINDING-y10-bench-stamp-instrument-2026-09-05.md``). The stamp
was hashing whole file bytes, so **any** edit to any byte moved it — and 53 %
of the hashed surface is comments and docstrings, which cannot change a bench
payload under any circumstances. Measured over the three fingerprint moves of
2026-09-05: all three were adjudicated payload-inert, and one (``677b605a``)
was a single **comment reword** that cost a dedicated lane to re-stamp 20
artifacts. Hashing ``ast.dump(ast.parse(source))`` instead makes comment,
docstring and whitespace edits inert while every semantic edit still fires.

This **cannot weaken the guarantee**: two sources with identical ASTs compile
to identical behaviour, so a part written under either is byte-identical by
construction. The guarantee narrows to exactly what it was ever able to
promise. Counterfactual, computed rather than argued (finding §3):
``677b605a^``/``677b605a`` (the comment reword) hash **identically**
(``96e5860ce4ec``) where the byte hash moved ``4e78c85427bb`` →
``b2f21b9a00d3``; ``dee6472c^``/``dee6472c`` (a real code change) still
**differs** (``3fabde12b672`` → ``96e5860ce4ec``). Pinned by
``tests/scoring/test_bench_stamp_ast.py``.

WHAT IT DELIBERATELY DOES NOT COVER. The builder imports the engine
(``src/market_sim/``) for the plant→class map, the CHP shares and the EIA-923
reconciliation, and those move far more often than the scripts do. Folding them
into the hash would mark every part stale after any lane's edit and the signal
would be ignored within a week. That exposure is real and is reported
SEPARATELY, as a count of intervening engine commits, by
``scripts/check_bench_freshness.py`` — a warning, not a gate.
"""

from __future__ import annotations

import ast
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


def _semantic_material(data: bytes) -> bytes:
    """Return the bytes to hash for one builder source: its dumped AST.

    ``ast.dump`` with its defaults omits line/column attributes, so
    reformatting, blank lines and moved code hash identically to the original
    as long as the parsed tree is the same. Comments and docstrings never reach
    the tree at all — docstrings do (they are string expressions), so a
    docstring edit DOES move the fingerprint; comments and whitespace do not.

    A source that will not parse falls back to its raw bytes. That is the
    FAIL-SAFE direction: an unparseable builder can only OVER-fire the stamp
    (every byte edit moves it, as before R-AS), never under-fire it.

    Args:
        data: Raw source bytes, or ``b""`` for a source that is absent.

    Returns:
        The dumped-AST bytes, or ``data`` unchanged when it will not parse.
    """
    try:
        return ast.dump(ast.parse(data)).encode()
    except (SyntaxError, ValueError):
        # ValueError: ``ast.parse`` raises it (not SyntaxError) on embedded
        # null bytes. Both mean "not parseable" and take the same fallback.
        return data


def builder_fingerprint() -> str:
    """Return the current builder fingerprint (12 hex chars).

    Hashes the SEMANTICS of :data:`BUILDER_SOURCES` in order — each source's
    dumped AST (:func:`_semantic_material`), prefixed by its path and by the
    length of that material so a rename or a truncation cannot collide with an
    edit. A missing file contributes the dumped AST of an empty module, exactly
    as an empty file would, so deleting a source still moves the fingerprint.

    The digest is over ``ast.dump`` output, whose exact spelling is a property
    of the CPython version in use. The repo pins ``requires-python = ">=3.11"``
    and every lane runs 3.11; a future interpreter bump would move the
    fingerprint once, which is a re-stamp (the Y-8 method), not a defect.
    """
    h = hashlib.sha256()
    for rel in BUILDER_SOURCES:
        p = REPO / rel
        material = _semantic_material(p.read_bytes() if p.exists() else b"")
        h.update(rel.encode())
        h.update(str(len(material)).encode())
        h.update(material)
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
