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

TWO FINGERPRINTS, AND WHICH ONE DECIDES (Y-17, 2026-09-06, director's option
(a) on the recommendation of
``docs/handoffs/FINDING-y15-flipset-sweep-2026-09-06.md`` §3.5; this lane's
record is ``FINDING-y17-bench-payload-fingerprint-2026-09-06.md``). This module
is a member of its own ``BUILDER_SOURCES``, so Y-12's edit to it (``3d0fd19d``)
moved the aggregate for **every** bench part in existence. That self-inclusion
is not itself wrong — a change to the stamping logic SHOULD invalidate a
provenance stamp — but it makes the aggregate useless as the
payload-REPRODUCIBILITY test, which is the question a re-stamp actually turns
on: the aggregate test can never return "equal" for a part built before such an
edit, so under a literal re-stamp rule no such part is EVER re-stampable, and
``404f1908`` (which re-stamped 20 parts across exactly that boundary) would
have been wrong. The two measures are therefore separated:

* :func:`builder_fingerprint` over :data:`BUILDER_SOURCES` — unchanged, still
  what a part records in ``meta.builderFingerprint``, still the provenance
  record and the engine-drift key. Nothing is deprecated (rule 26
  ``[R-DELETE]`` does not bite; a second measure is ADDED).
* :func:`payload_fingerprint` over :data:`PAYLOAD_SOURCES` — the three sources
  that produce a part's numbers, this module excluded by construction. This is
  what :func:`is_stale` and ``scripts/check_bench_freshness.py`` decide on.

The guarantee is unweakened: identical payload-source ASTs still compile to
identical behaviour, so a part written under either is byte-identical in its
``bench`` block by construction. What narrows is only the surface — from "the
builder plus its stamper" to "the builder" — and the dropped member is the one
member that provably cannot change a number.

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

#: The scripts that compute and write a bench part's PAYLOAD. Order-stable so
#: the hash is reproducible; a missing file is hashed as absent rather than
#: skipped, so deleting one still moves the fingerprint.
#:
#: THIS MODULE IS EXCLUDED BY CONSTRUCTION. ``bench_stamp.py`` computes the
#: stamp and contributes not one number to a part's ``bench`` block, so it can
#: never change a payload — see :data:`PAYLOAD_FINGERPRINT_BY_BUILDER` and
#: ``docs/handoffs/FINDING-y17-bench-payload-fingerprint-2026-09-06.md`` for
#: the defect that exclusion closes.
PAYLOAD_SOURCES: tuple[str, ...] = (
    "scripts/render_calibration_html.py",
    "scripts/render_backcast.py",
    "scripts/lib/backcast_artifacts.py",
)

#: This module. In :data:`BUILDER_SOURCES` and out of :data:`PAYLOAD_SOURCES`:
#: a change to the stamping logic SHOULD invalidate the aggregate stamp every
#: part carries (that is what makes the stamp a provenance record), and MUST
#: NOT be read as evidence that a payload moved.
_STAMP_SOURCE: str = "scripts/lib/bench_stamp.py"

#: The full builder surface the recorded ``meta.builderFingerprint`` covers —
#: the payload producers plus the stamper. Composed, never re-spelled, so the
#: "payload sources plus this module" relation cannot drift.
BUILDER_SOURCES: tuple[str, ...] = PAYLOAD_SOURCES + (_STAMP_SOURCE,)

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


def _fingerprint(sources: tuple[str, ...]) -> str:
    """Return the 12-hex digest over *sources*' semantics.

    Hashes each source's dumped AST (:func:`_semantic_material`) in order,
    prefixed by its path and by the length of that material so a rename or a
    truncation cannot collide with an edit. A missing file contributes the
    dumped AST of an empty module, exactly as an empty file would, so deleting
    a source still moves the digest.

    The digest is over ``ast.dump`` output, whose exact spelling is a property
    of the CPython version in use. The repo pins ``requires-python = ">=3.11"``
    and every lane runs 3.11; a future interpreter bump would move both
    fingerprints once, which is a re-stamp (the Y-8 method), not a defect.

    Args:
        sources: Repo-relative paths, in a stable order.
    """
    h = hashlib.sha256()
    for rel in sources:
        p = REPO / rel
        material = _semantic_material(p.read_bytes() if p.exists() else b"")
        h.update(rel.encode())
        h.update(str(len(material)).encode())
        h.update(material)
    return h.hexdigest()[:_DIGEST_CHARS]


def builder_fingerprint() -> str:
    """Return the current AGGREGATE fingerprint over :data:`BUILDER_SOURCES`.

    This is the value written to and read from a part's
    ``meta.builderFingerprint``: the part's provenance record, covering the
    stamper as well as the payload producers. It answers *"was this part
    written by the exact builder at HEAD?"* — which is NOT the question a
    re-stamp turns on; see :func:`payload_fingerprint`.
    """
    return _fingerprint(BUILDER_SOURCES)


def payload_fingerprint() -> str:
    """Return the current PAYLOAD fingerprint over :data:`PAYLOAD_SOURCES`.

    This answers the question that actually matters for a committed part:
    *"would the builder at HEAD produce the same numbers?"* It excludes
    ``bench_stamp.py``, which cannot contribute a number to a payload, so an
    edit to the stamping logic no longer reads as a payload move.
    """
    return _fingerprint(PAYLOAD_SOURCES)


#: Historical ``meta.builderFingerprint`` values → the PAYLOAD fingerprint of
#: the builder state that emitted them.
#:
#: WHY THIS TABLE EXISTS. A committed part records only the aggregate. The
#: aggregate is not invertible, so for a part whose aggregate is no longer
#: current there is no way to recover its payload fingerprint from the part
#: itself — and a part CANNOT be made to carry one, because the writer
#: (``backcast_artifacts.write_bench_part``) is a payload source: teaching it
#: to stamp a second field would move the payload fingerprint and mark all 24
#: committed parts stale, which is the opposite of the repair. So the mapping
#: is recorded here instead, once per historical value.
#:
#: WHY IT IS NOT AN ESCAPE HATCH. An entry is a claim about a specific builder
#: STATE, not about a file: an aggregate pins all four sources by construction
#: (equal aggregate ⇒ equal material, barring collision), so recording its
#: payload fingerprint asserts nothing the aggregate did not already fix. Every
#: entry is recomputable from git and is recomputed by
#: ``tests/scoring/test_bench_stamp_payload.py`` when history is available; an
#: aggregate absent from this table resolves to ``None``, i.e. STALE. That is
#: the FAIL-CLOSED direction — an unknown builder state is never forgiven.
#:
#: MAINTENANCE. A table entry is owed EXACTLY when an edit moves the aggregate
#: without moving the payload — i.e. an edit to ``bench_stamp.py`` alone. Add
#: ``{previous builder_fingerprint(): payload_fingerprint()}``; the payload
#: value is unchanged by such an edit, which is the point.
#: ``test_bench_stamp_payload.py`` fails with the exact line to add when a
#: committed part carries an aggregate this table cannot resolve.
PAYLOAD_FINGERPRINT_BY_BUILDER: dict[str, str] = {
    # Y-12's AST-era aggregate (`3d0fd19d`, 2026-09-05, owner ruling R-AS),
    # carried by 23 of the 24 committed parts and superseded by THIS module's
    # edit. Payload blobs at `3d0fd19d`: render_calibration_html d382d9b,
    # render_backcast ccf8b1c, backcast_artifacts c75d828 — the same three
    # blobs HEAD carries, hence the same payload fingerprint.
    "4254168edcfe": "643eac24b565",
    # The byte-era aggregate at `dc0f7c14` (== `3d0fd19d^`), carried by
    # `bench/ERCOT/2022.json.gz`: built by the ercot-249/250 lane on a pre-Y-12
    # checkout, then committed (`f1561c2d`) onto a post-Y-12 `main` without
    # re-rendering. Payload blobs at `dc0f7c14` are the SAME three as above, so
    # the part's payload is what the builder at HEAD would produce; only
    # `bench_stamp.py` (e379717 → edb7d50) differs. This is the case that
    # exposed the defect — see
    # `docs/handoffs/FINDING-y15-flipset-sweep-2026-09-06.md` §3.5 and
    # `docs/handoffs/FINDING-y17-bench-payload-fingerprint-2026-09-06.md`.
    "b2f21b9a00d3": "643eac24b565",
}


def part_fingerprint(part_obj: dict) -> str | None:
    """Return the fingerprint a loaded bench part carries, or ``None``.

    ``None`` means the part predates the stamp entirely — which is itself a
    staleness signal, and is reported as such rather than tolerated.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    fp = (part_obj or {}).get("meta", {}).get("builderFingerprint")
    return str(fp) if fp else None


def part_payload_fingerprint(part_obj: dict) -> str | None:
    """Return the PAYLOAD fingerprint of the builder that wrote *part_obj*.

    Resolved from the aggregate the part records, in three cases:

    * the aggregate is HEAD's ⇒ HEAD's payload fingerprint, because an equal
      aggregate pins every source including the payload three;
    * the aggregate is a known historical value ⇒
      :data:`PAYLOAD_FINGERPRINT_BY_BUILDER`;
    * anything else — an unknown aggregate, or no stamp at all ⇒ ``None``,
      which reads as STALE. Fail-closed: a builder state we cannot identify is
      never assumed to have produced HEAD's numbers.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    aggregate = part_fingerprint(part_obj)
    if aggregate is None:
        return None
    if aggregate == builder_fingerprint():
        return payload_fingerprint()
    return PAYLOAD_FINGERPRINT_BY_BUILDER.get(aggregate)


def payload_origin(part_obj: dict) -> str:
    """Return how *part_obj*'s payload fingerprint was resolved, for reporting.

    ``"current"`` — the part carries HEAD's aggregate. ``"historical"`` — the
    aggregate is superseded but :data:`PAYLOAD_FINGERPRINT_BY_BUILDER` names
    the payload state it was written under. ``"unknown"`` — neither, so the
    part cannot be shown to reproduce.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    aggregate = part_fingerprint(part_obj)
    if aggregate is not None and aggregate == builder_fingerprint():
        return "current"
    if aggregate in PAYLOAD_FINGERPRINT_BY_BUILDER:
        return "historical"
    return "unknown"


def is_stale(part_obj: dict) -> bool:
    """Return True when *part_obj*'s payload is not reproducible at HEAD.

    DECIDED ON THE PAYLOAD MEASURE, not the aggregate (Y-17, director's option
    (a) on the Y-15 §3.5 recommendation). The aggregate covers this module,
    which computes the stamp and produces no payload number, so an edit here
    moved the aggregate for EVERY part in existence — making the aggregate test
    degenerate as a reproducibility question: it could never return "equal" for
    a part written before that edit, so no such part was ever re-stampable,
    which contradicts the program's own practice (``404f1908`` re-stamped 20
    parts across exactly that boundary). The aggregate stays as the recorded
    provenance stamp and as the engine-drift key; the PAYLOAD fingerprint is
    what decides reproducibility.

    Args:
        part_obj: A part as returned by ``backcast_artifacts.load_bench_part``.
    """
    return part_payload_fingerprint(part_obj) != payload_fingerprint()
