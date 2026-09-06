"""The stamp's two fingerprints: aggregate records provenance, payload decides.

``scripts/lib/bench_stamp.py`` is a member of its own ``BUILDER_SOURCES``, so
Y-12's edit to it (``3d0fd19d``, 2026-09-05) moved the aggregate fingerprint for
EVERY bench part in existence. The self-inclusion is correct as provenance — a
change to the stamping logic should invalidate the stamp — but it made the
aggregate degenerate as the payload-REPRODUCIBILITY test, which is the question
a re-stamp turns on: the aggregate could never read "equal" for a part built
before such an edit, so no such part was ever re-stampable, while ``404f1908``
re-stamped 20 parts across exactly that boundary. Recorded in
``docs/handoffs/FINDING-y15-flipset-sweep-2026-09-06.md`` §3.5; repaired by
Y-17 (``FINDING-y17-bench-payload-fingerprint-2026-09-06.md``).

These tests pin the resulting contract:

* (a) the two measures are structurally related — the payload surface is the
  builder surface minus this module, and nothing else;
* (b) a stamp-only edit moves the aggregate and NOT the payload, so a part
  written before it still reads FRESH;
* (c) a payload edit reads STALE whatever the stamp says, and an unidentifiable
  builder state reads STALE too (fail-closed);
* (d) the resolution table is not a hand-written escape hatch — every entry is
  recomputed from git, and every aggregate on a committed part must resolve.

(a)–(c) are hermetic: each builds a throwaway source tree in ``tmp_path`` and
points the module's ``REPO``, ``PAYLOAD_SOURCES`` and ``BUILDER_SOURCES`` at it.
No writes into the checkout, no network. (d) reads the real repo.
"""

import gzip
import json
import subprocess

import pytest

from scripts.lib import bench_stamp

#: A miniature payload producer — stands in for render_calibration_html.py.
PAYLOAD_SRC = '''"""Payload producer."""


def bench(x):
    """Return a bench number."""
    return x * 2
'''

#: A miniature stamper — stands in for bench_stamp.py itself. It contributes no
#: number to a payload, which is the whole reason it is excluded.
STAMP_SRC = '''"""Stamper."""


def stamp():
    """Return a digest."""
    return "abc"
'''

#: Synthetic fixture paths, deliberately NOT under ``scripts/``. Any
#: repo-relative path exercises ``_fingerprint`` identically (it only does
#: ``REPO / rel``), and a ``scripts/``-shaped literal would be picked up by
#: ``ci_refactor_guards.py``'s ``--script-refs`` scan of tracked files as a
#: dangling reference — the trap that cost ``test_bench_stamp_ast.py`` an entry
#: in that guard's KNOWN_DANGLING allowlist (Y-13). The real payload surface is
#: asserted against the live tuple in test (a) instead.
_PAYLOAD_REL = "fixture/fake_payload.py"
_STAMP_REL = "fixture/fake_stamp.py"

#: The checkout git is read from, captured at import: the fixtures below
#: monkeypatch ``bench_stamp.REPO`` to a throwaway tree, and reading the patched
#: value would run git outside a repository and silently hash EMPTY files — a
#: green test that measures nothing. (Same trap as test_bench_stamp_ast.py.)
_CHECKOUT = bench_stamp.REPO


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Point the stamp at a throwaway payload+stamper tree; return a writer."""
    (tmp_path / "fixture").mkdir()
    monkeypatch.setattr(bench_stamp, "REPO", tmp_path)
    monkeypatch.setattr(bench_stamp, "PAYLOAD_SOURCES", (_PAYLOAD_REL,))
    monkeypatch.setattr(bench_stamp, "BUILDER_SOURCES", (_PAYLOAD_REL, _STAMP_REL))
    monkeypatch.setattr(bench_stamp, "PAYLOAD_FINGERPRINT_BY_BUILDER", {})

    def write(payload: str = PAYLOAD_SRC, stamp: str = STAMP_SRC) -> tuple[str, str]:
        """Write both sources and return ``(aggregate, payload)`` fingerprints."""
        (tmp_path / _PAYLOAD_REL).write_text(payload)
        (tmp_path / _STAMP_REL).write_text(stamp)
        return bench_stamp.builder_fingerprint(), bench_stamp.payload_fingerprint()

    return write


def _part(aggregate: str | None) -> dict:
    """Return a bench part carrying *aggregate* (or no stamp when ``None``)."""
    meta: dict = {"years": [2024]}
    if aggregate is not None:
        meta["builderFingerprint"] = aggregate
    return {"meta": meta, "bench": {"CC": 1.0}}


# --------------------------------------------------------------------------- #
# (a) the two surfaces are related by construction
# --------------------------------------------------------------------------- #
def test_a_payload_surface_is_the_builder_surface_minus_this_module():
    """BUILDER_SOURCES == PAYLOAD_SOURCES + (bench_stamp.py,), exactly."""
    assert bench_stamp.BUILDER_SOURCES == bench_stamp.PAYLOAD_SOURCES + (
        bench_stamp._STAMP_SOURCE,
    )
    assert bench_stamp._STAMP_SOURCE == "scripts/lib/bench_stamp.py"
    assert bench_stamp._STAMP_SOURCE not in bench_stamp.PAYLOAD_SOURCES
    # The three payload producers named by the charter, and only those.
    assert bench_stamp.PAYLOAD_SOURCES == (
        "scripts/render_calibration_html.py",
        "scripts/render_backcast.py",
        "scripts/lib/backcast_artifacts.py",
    )


def test_a_both_fingerprints_are_12_hex_and_deterministic():
    """Same tree in, same digests out — on the real sources."""
    agg, pay = bench_stamp.builder_fingerprint(), bench_stamp.payload_fingerprint()
    assert (agg, pay) == (
        bench_stamp.builder_fingerprint(),
        bench_stamp.payload_fingerprint(),
    )
    for fp in (agg, pay):
        assert len(fp) == bench_stamp._DIGEST_CHARS
        assert all(c in "0123456789abcdef" for c in fp)
    # Different surfaces, so different digests — the split is not cosmetic.
    assert agg != pay


# --------------------------------------------------------------------------- #
# (b) a stamp-only edit moves the aggregate, never the payload
# --------------------------------------------------------------------------- #
def test_b_stamp_edit_moves_the_aggregate_and_not_the_payload(tree):
    """The Y-12 shape: edit the stamper, and only the aggregate moves."""
    agg_before, pay_before = tree()
    agg_after, pay_after = tree(stamp=STAMP_SRC + "\nX = 1\n")
    assert agg_after != agg_before, "a stamping-logic change must move the aggregate"
    assert pay_after == pay_before, "a stamping-logic change cannot move a payload"


def test_b_part_with_a_stamp_moved_aggregate_reads_FRESH(tree, monkeypatch):
    """A payload-identical, stamp-moved part is NOT stale — the ERCOT/2022 case.

    This is the assertion the whole repair exists for: under the aggregate test
    this part was unconditionally STALE and could never be re-stamped.
    """
    agg_before, pay_before = tree()
    part = _part(agg_before)
    assert not bench_stamp.is_stale(part), "sanity: fresh before the stamp moves"

    # The stamper changes; the payload producer does not.
    monkeypatch.setitem(
        bench_stamp.PAYLOAD_FINGERPRINT_BY_BUILDER, agg_before, pay_before
    )
    agg_after, pay_after = tree(stamp=STAMP_SRC + "\nX = 1\n")

    assert bench_stamp.part_fingerprint(part) != agg_after  # aggregate superseded
    assert bench_stamp.part_payload_fingerprint(part) == pay_after
    assert bench_stamp.payload_origin(part) == "historical"
    assert not bench_stamp.is_stale(part)


def test_b_part_carrying_the_current_aggregate_needs_no_table(tree):
    """An equal aggregate pins every source, so the payload resolves with no entry."""
    agg, pay = tree()
    part = _part(agg)
    assert bench_stamp.PAYLOAD_FINGERPRINT_BY_BUILDER == {}
    assert bench_stamp.part_payload_fingerprint(part) == pay
    assert bench_stamp.payload_origin(part) == "current"
    assert not bench_stamp.is_stale(part)


# --------------------------------------------------------------------------- #
# (c) a payload move is STALE whatever the stamp says; unknown states fail closed
# --------------------------------------------------------------------------- #
def test_c_payload_edit_reads_STALE_even_with_a_resolvable_stamp(tree, monkeypatch):
    """A real payload change is stale — the table cannot forgive it."""
    agg_before, pay_before = tree()
    part = _part(agg_before)
    monkeypatch.setitem(
        bench_stamp.PAYLOAD_FINGERPRINT_BY_BUILDER, agg_before, pay_before
    )

    _, pay_after = tree(payload=PAYLOAD_SRC.replace("x * 2", "x * 3"))

    assert pay_after != pay_before, "sanity: the payload producer really moved"
    assert bench_stamp.part_payload_fingerprint(part) == pay_before
    assert bench_stamp.payload_origin(part) == "historical"
    assert bench_stamp.is_stale(part), "a moved payload must read STALE"


def test_c_payload_edit_reads_STALE_when_the_stamp_also_moved(tree, monkeypatch):
    """Both surfaces moving is still stale — the stamp move never masks it."""
    agg_before, pay_before = tree()
    part = _part(agg_before)
    monkeypatch.setitem(
        bench_stamp.PAYLOAD_FINGERPRINT_BY_BUILDER, agg_before, pay_before
    )
    tree(payload=PAYLOAD_SRC.replace("x * 2", "x * 3"), stamp=STAMP_SRC + "\nX = 1\n")
    assert bench_stamp.is_stale(part)


def test_c_unknown_aggregate_fails_closed(tree):
    """An unidentifiable builder state is never assumed to reproduce."""
    tree()
    part = _part("0" * 12)
    assert bench_stamp.part_payload_fingerprint(part) is None
    assert bench_stamp.payload_origin(part) == "unknown"
    assert bench_stamp.is_stale(part)


def test_c_no_stamp_at_all_fails_closed(tree):
    """A part predating the stamp entirely is stale, not tolerated."""
    tree()
    part = _part(None)
    assert bench_stamp.part_fingerprint(part) is None
    assert bench_stamp.part_payload_fingerprint(part) is None
    assert bench_stamp.payload_origin(part) == "unknown"
    assert bench_stamp.is_stale(part)


# --------------------------------------------------------------------------- #
# (d) the resolution table is derived, not asserted
# --------------------------------------------------------------------------- #
#: Each historical aggregate and the commit whose builder state emitted it, from
#: the Y-17 decomposition. The VALUE is what this test recomputes: the payload
#: fingerprint of that commit's three payload sources, under HEAD's instrument.
#: The KEY's own derivation is not recomputed — ``b2f21b9a00d3`` is a BYTE-era
#: digest, and reimplementing the retired byte construction to check it would
#: ship exactly the kind of re-armable dead code rule 26 ``[R-DELETE]`` refuses.
_TABLE_PROVENANCE = {
    "4254168edcfe": "3d0fd19d",  # Y-12, the AST-era aggregate
    "b2f21b9a00d3": "dc0f7c14",  # == 3d0fd19d^, the byte-era aggregate
}


def _blob(rev: str, rel: str) -> bytes | None:
    """Return the bytes of *rel* at *rev*, or ``None`` when git cannot serve it."""
    r = subprocess.run(
        ["git", "-C", str(_CHECKOUT), "show", f"{rev}:{rel}"],
        capture_output=True,
    )
    return r.stdout if r.returncode == 0 else None


@pytest.mark.parametrize("aggregate, commit", sorted(_TABLE_PROVENANCE.items()))
def test_d_table_value_is_the_payload_fingerprint_at_the_cited_commit(
    aggregate, commit, tmp_path, monkeypatch
):
    """Recompute each table entry from history rather than trusting the literal.

    SKIPS on a shallow or blob-filtered checkout that cannot serve the revision
    — CI's fast tier runs ``actions/checkout@v4`` at depth 1 — so this pins the
    claim for anyone on a full clone and never reddens a shallow one.
    """
    rels = (
        "scripts/render_calibration_html.py",
        "scripts/render_backcast.py",
        "scripts/lib/backcast_artifacts.py",
    )
    for rel in rels:
        data = _blob(commit, rel)
        if data is None:
            pytest.skip(f"checkout cannot serve {commit}:{rel}")
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    monkeypatch.setattr(bench_stamp, "REPO", tmp_path)
    monkeypatch.setattr(bench_stamp, "PAYLOAD_SOURCES", rels)
    assert (
        bench_stamp.payload_fingerprint()
        == bench_stamp.PAYLOAD_FINGERPRINT_BY_BUILDER[aggregate]
    ), (
        f"PAYLOAD_FINGERPRINT_BY_BUILDER[{aggregate!r}] does not match the payload "
        f"sources at {commit}. Either the entry is wrong or the interpreter's "
        f"ast.dump spelling moved (a re-stamp, not a defect)."
    )


def test_d_every_committed_part_resolves_to_a_known_builder_state():
    """No committed part may carry an aggregate the table cannot resolve.

    This is the maintenance guard. An edit to ``bench_stamp.py`` moves the
    aggregate for every part at once; without an entry they would all read
    STALE on a payload that never moved — the very defect this design closes.
    The failure message carries the exact line to add.
    """
    bench = bench_stamp.REPO / "frontend" / "data" / "backcast" / "bench"
    parts = sorted(bench.rglob("*.json.gz")) if bench.exists() else []
    if not parts:
        pytest.skip("no committed bench parts in this checkout")
    unresolved: dict[str, list[str]] = {}
    for path in parts:
        obj = json.loads(gzip.decompress(path.read_bytes()))
        if bench_stamp.payload_origin(obj) == "unknown":
            fp = bench_stamp.part_fingerprint(obj) or "(none)"
            unresolved.setdefault(fp, []).append(f"{path.parent.name}/{path.stem}")
    assert not unresolved, (
        "committed bench part(s) carry an aggregate stamp that "
        "PAYLOAD_FINGERPRINT_BY_BUILDER cannot resolve, so they read STALE:\n"
        + "\n".join(f"  {fp}: {sorted(v)}" for fp, v in sorted(unresolved.items()))
        + "\n\nIf the aggregate moved because bench_stamp.py was edited and NO "
        "payload source changed, add to PAYLOAD_FINGERPRINT_BY_BUILDER:\n"
        + "\n".join(
            f'    "{fp}": "{bench_stamp.payload_fingerprint()}",'
            for fp in sorted(unresolved)
        )
        + "\nIf a PAYLOAD source changed, the parts are genuinely stale and must "
        "be regenerated by their ISO's calibration desk — do NOT add an entry."
    )
