"""The bench builder fingerprint hashes SEMANTICS, not bytes (owner ruling R-AS).

``scripts/lib/bench_stamp.builder_fingerprint`` gates C1 reproducibility for all
six ISOs: a committed bench part whose stamp differs from HEAD's provably was
not written by the builder that would run now. Until 2026-09-05 the stamp
hashed the RAW BYTES of four whole files, so any edit to any byte moved it —
and 53 % of that surface is comments and docstrings, which cannot change a
bench payload under any circumstances
(``docs/handoffs/FINDING-y10-bench-stamp-instrument-2026-09-05.md`` §2).
All three fingerprint moves of 2026-09-05 were adjudicated payload-inert; one
(``677b605a``) was a single reworded COMMENT that cost a dedicated lane to
re-stamp 20 artifacts.

R-AS adopted the finding's Proposal A: hash ``ast.dump(ast.parse(source))``.
These tests pin both halves of the resulting contract — the false alarms that
must stop firing, and every semantic move that must keep firing — plus the
recorded counterfactual over the two 2026-09-05 commits. Hermetic: each builds
a throwaway source tree in ``tmp_path`` and points the module's ``REPO`` and
``BUILDER_SOURCES`` at it. No writes into the checkout, no network.
"""

import subprocess

import pytest

from scripts.lib import bench_stamp

#: A miniature builder source. Deliberately carries every construct the stamp
#: has to reason about: a module docstring, a comment, a function docstring and
#: an executable body.
BASE = '''"""Module docstring."""


# A comment that cannot reach a bench payload.
def build(x):
    """Return the payload scale."""
    return x * 2
'''


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Point the stamp at a throwaway one-source tree and return a writer."""
    (tmp_path / "scripts").mkdir()
    rel = "scripts/fake_builder.py"
    monkeypatch.setattr(bench_stamp, "REPO", tmp_path)
    monkeypatch.setattr(bench_stamp, "BUILDER_SOURCES", (rel,))

    def write(text: str) -> str:
        """Write *text* as the single builder source and return the stamp."""
        (tmp_path / rel).write_text(text)
        return bench_stamp.builder_fingerprint()

    return write


# --------------------------------------------------------------------------- #
# (a) the false alarms that must stop firing
# --------------------------------------------------------------------------- #
def test_a_comment_only_edit_leaves_the_fingerprint_unchanged(tree):
    """The ``677b605a`` case in miniature: reword a comment, nothing moves."""
    before = tree(BASE)
    after = tree(
        BASE.replace(
            "# A comment that cannot reach a bench payload.",
            "# A comment reworded on 2026-09-05 (retired script, deleted).",
        )
    )
    assert after == before


def test_a_deleted_comment_and_added_comment_are_both_inert(tree):
    """Adding or removing comment lines is not a semantic change."""
    before = tree(BASE)
    assert (
        tree(BASE.replace("# A comment that cannot reach a bench payload.\n", ""))
        == before
    )
    assert tree("# leading comment\n" + BASE + "\n# trailing comment\n") == before


def test_whitespace_and_reformatting_are_inert(tree):
    """Blank lines and line moves shift every line number but no AST node.

    ``ast.dump`` at its defaults omits line/column attributes, which is what
    makes this hold — it is the property the whole change rests on.
    """
    before = tree(BASE)
    assert tree(BASE.replace("\n\n\n", "\n\n\n\n\n")) == before
    assert tree(BASE.replace("return x * 2", "return  x  *  2")) == before


# --------------------------------------------------------------------------- #
# (b) every semantic move must keep firing
# --------------------------------------------------------------------------- #
def test_b_one_token_semantic_edit_moves_the_fingerprint(tree):
    """A single changed literal is a payload-capable edit and must fire."""
    before = tree(BASE)
    assert tree(BASE.replace("return x * 2", "return x * 3")) != before


def test_b_renaming_one_identifier_moves_the_fingerprint(tree):
    """Names are AST fields, so a rename is semantic even at one token."""
    before = tree(BASE)
    assert tree(BASE.replace("def build(", "def build_payload(")) != before


def test_docstring_edits_still_move_the_fingerprint(tree):
    """STATED LIMIT of Proposal A, pinned rather than left to be discovered.

    Docstrings ARE ``Expr(Constant(...))`` nodes in the parsed tree, so
    ``ast.dump`` carries them and editing one moves the stamp. Comments and
    whitespace are the prose that goes inert; docstrings are not. Excluding
    them would need a tree transform — wider than the Proposal A that R-AS
    adopted, and it would not reproduce the counterfactual digests below.
    """
    before = tree(BASE)
    assert (
        tree(BASE.replace("Return the payload scale.", "Return the scale.")) != before
    )


def test_missing_source_still_moves_the_fingerprint(tmp_path, monkeypatch):
    """Deleting a builder source must fire — the pre-R-AS behaviour, unchanged.

    An absent file contributes the dumped AST of an empty module, exactly as an
    empty file would; both differ from any real source.
    """
    (tmp_path / "scripts").mkdir()
    rel = "scripts/fake_builder.py"
    monkeypatch.setattr(bench_stamp, "REPO", tmp_path)
    monkeypatch.setattr(bench_stamp, "BUILDER_SOURCES", (rel,))
    (tmp_path / rel).write_text(BASE)
    present = bench_stamp.builder_fingerprint()
    (tmp_path / rel).unlink()
    absent = bench_stamp.builder_fingerprint()
    assert absent != present
    (tmp_path / rel).write_text("")
    assert bench_stamp.builder_fingerprint() == absent


def test_unparseable_source_falls_back_to_raw_bytes(tree):
    """The fallback fails SAFE: an unparseable builder over-fires, never under.

    With no valid tree there is nothing semantic to hash, so the raw bytes are
    used and even a comment edit moves the stamp — the pre-R-AS behaviour for
    that one file.
    """
    broken = BASE + "\ndef (:\n"
    before = tree(broken)
    assert tree(broken + "# a comment\n") != before


# --------------------------------------------------------------------------- #
# (c) determinism, on the real builder sources
# --------------------------------------------------------------------------- #
def test_c_fingerprint_is_stable_across_two_calls():
    """Same tree in, same 12-hex digest out — twice, on the real sources."""
    fp = bench_stamp.builder_fingerprint()
    assert fp == bench_stamp.builder_fingerprint()
    assert len(fp) == bench_stamp._DIGEST_CHARS
    assert all(c in "0123456789abcdef" for c in fp)


# --------------------------------------------------------------------------- #
# (d) the recorded counterfactual over the two 2026-09-05 commits
# --------------------------------------------------------------------------- #
#: The finding's §3 counterfactual, re-measured under the shipped construction
#: (Python 3.11): the comment reword is inert, the code change is not.
#:
#: ===================  ==============  =============
#: revision             byte hash       AST hash
#: ===================  ==============  =============
#: ``dee6472c^``        dbea7bf45111    3fabde12b672
#: ``dee6472c``         4e78c85427bb    96e5860ce4ec
#: ``677b605a^``        4e78c85427bb    96e5860ce4ec
#: ``677b605a``         b2f21b9a00d3    96e5860ce4ec
#: ===================  ==============  =============
#:
#: The RELATIONS are asserted, not the absolute digests: ``ast.dump``'s exact
#: spelling is a CPython-version property, so pinning the literals here would
#: turn an interpreter bump into a red test rather than the one re-stamp it
#: actually is. The digests above are the record.
_CF_SOURCES = (
    "scripts/render_calibration_html.py",
    "scripts/render_backcast.py",
    "scripts/lib/backcast_artifacts.py",
    "scripts/lib/bench_stamp.py",
)


#: The checkout git is read from. Captured at import, because each stamping
#: below monkeypatches ``bench_stamp.REPO`` to a throwaway tree — reading the
#: patched value would run git outside a repository and silently hash four
#: EMPTY files, which is a green test that measures nothing.
_CHECKOUT = bench_stamp.REPO


def _blob(rev: str, rel: str) -> bytes | None:
    """Return the bytes of *rel* at *rev*, or ``None`` when git cannot serve it."""
    r = subprocess.run(
        ["git", "-C", str(_CHECKOUT), "show", f"{rev}:{rel}"],
        capture_output=True,
    )
    return r.stdout if r.returncode == 0 else None


def _fp_of(blobs: dict[str, bytes], tmp_path, monkeypatch) -> str:
    """Materialize *blobs* as a throwaway builder tree and stamp it."""
    for rel, data in blobs.items():
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    monkeypatch.setattr(bench_stamp, "REPO", tmp_path)
    monkeypatch.setattr(bench_stamp, "BUILDER_SOURCES", _CF_SOURCES)
    return bench_stamp.builder_fingerprint()


@pytest.mark.parametrize(
    "commit, moves, what",
    [
        ("677b605a", False, "a one-line comment reword"),
        ("dee6472c", True, "a real CHP add-back code change"),
    ],
)
def test_d_y10_counterfactual_at_the_recorded_commits(
    commit, moves, what, tmp_path, monkeypatch
):
    """Reproduce the finding's counterfactual against the real history.

    SKIPS on a shallow or blob-filtered checkout that cannot serve these
    revisions — CI's fast tier runs ``actions/checkout@v4`` at its default
    depth 1, so this pins the claim for anyone running the suite on a full
    clone and never reddens a shallow one. The measured digests are recorded
    in the table above and in ``docs/governance/rule-history.md``.
    """
    sides: dict[str, dict[str, bytes]] = {}
    for rev in (f"{commit}^", commit):
        sides[rev] = {}
        for rel in _CF_SOURCES:
            data = _blob(rev, rel)
            if data is None:
                pytest.skip(f"{rev}:{rel} unavailable (shallow/filtered checkout)")
            sides[rev][rel] = data
    # Guard against a silently-empty read: the two sides must differ in BYTES,
    # or the parametrization is not exercising the commit it names.
    assert sides[f"{commit}^"] != sides[commit]
    before = _fp_of(sides[f"{commit}^"], tmp_path / "before", monkeypatch)
    after = _fp_of(sides[commit], tmp_path / "after", monkeypatch)
    assert (before != after) is moves, f"{commit} is {what}"
