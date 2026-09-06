"""Tests for the content-addressed on-disk mapping memo (``data/disk_memo``).

The load-bearing property is equality: a memo read must return exactly the
mapping ``compute()`` returns — same keys, same values, same Python types —
because the memoized sites feed lookups the LP reads, and the wall-clock byte
gate is ``atol=rtol=0``. Everything here is hermetic (``tmp_path`` sources,
counted computes), so the whole module stays in the fast tier.

The second property, equally load-bearing, is that the memo is *advisory*:
every failure mode — unhashable source, corrupt file, a value of the wrong
type, an unwritable directory — degrades to the computation rather than to a
wrong answer or an exception.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import pytest

from market_sim.data.disk_memo import (
    _decode_mapping,
    _encodable,
    _memo_path,
    content_digest,
    memoized_mapping,
)


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    """A tiny stand-in for the eGRID workbook."""
    path = tmp_path / "src2023_data.xlsx"
    path.write_bytes(b"source-bytes-v1")
    return path


class _Counter:
    """A ``compute`` callable that records how many times it ran."""

    def __init__(self, value: dict) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> dict:
        self.calls += 1
        return dict(self.value)


# --------------------------------------------------------------------------
# content_digest
# --------------------------------------------------------------------------


class TestContentDigest:
    def test_stable_across_calls(self, source: Path) -> None:
        assert content_digest([source], ("ns",)) == content_digest([source], ("ns",))

    def test_changes_with_source_bytes(self, source: Path) -> None:
        before = content_digest([source], ("ns",))
        source.write_bytes(b"source-bytes-v2")
        assert content_digest([source], ("ns",)) != before

    def test_changes_with_params(self, source: Path) -> None:
        assert content_digest([source], ("a",)) != content_digest([source], ("b",))

    def test_params_are_length_prefixed(self, source: Path) -> None:
        # Without the length prefix ("ab", "c") and ("a", "bc") would collide.
        assert content_digest([source], ("ab", "c")) != content_digest(
            [source], ("a", "bc")
        )

    def test_every_source_is_hashed(self, tmp_path: Path, source: Path) -> None:
        second = tmp_path / "vintage.parquet"
        second.write_bytes(b"v1")
        before = content_digest([source, second], ("ns",))
        second.write_bytes(b"v2")
        assert content_digest([source, second], ("ns",)) != before

    def test_source_order_matters(self, tmp_path: Path, source: Path) -> None:
        second = tmp_path / "vintage.parquet"
        second.write_bytes(b"v1")
        assert content_digest([source, second]) != content_digest([second, source])

    def test_missing_source_raises(self, tmp_path: Path) -> None:
        with pytest.raises(OSError):
            content_digest([tmp_path / "absent.xlsx"], ("ns",))


# --------------------------------------------------------------------------
# memoized_mapping — the happy path
# --------------------------------------------------------------------------


class TestMemoRoundTrip:
    def test_miss_computes_then_hit_does_not(self, source: Path) -> None:
        compute = _Counter({1: 2.5, 55641: 6.88})
        first = memoized_mapping("ns", [source], compute, float)
        second = memoized_mapping("ns", [source], compute, float)
        assert compute.calls == 1
        assert first == second == {1: 2.5, 55641: 6.88}

    def test_memo_file_is_written_beside_the_anchor(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 2.5}), float)
        memos = list(source.parent.glob("*.ns.json"))
        assert len(memos) == 1
        assert memos[0].parent == source.parent
        assert memos[0].name.startswith(source.stem + ".")

    def test_memo_path_shape(self, source: Path) -> None:
        assert _memo_path(source, "ns", "beef") == source.with_name(
            "src2023_data.beef.ns.json"
        )

    def test_types_survive_the_round_trip(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 2.5}), float)
        served = memoized_mapping("ns", [source], _Counter({}), float)
        (key,), (value,) = served.keys(), served.values()
        assert type(key) is int and type(value) is float

    def test_str_values(self, source: Path) -> None:
        compute = _Counter({3: "HOUSTON", 4: "WEST"})
        memoized_mapping("zones", [source], compute, str)
        served = memoized_mapping("zones", [source], _Counter({}), str)
        assert served == {3: "HOUSTON", 4: "WEST"}
        assert all(type(v) is str for v in served.values())

    def test_empty_mapping_is_memoized(self, source: Path) -> None:
        compute = _Counter({})
        assert memoized_mapping("ns", [source], compute, float) == {}
        assert memoized_mapping("ns", [source], compute, float) == {}
        assert compute.calls == 1

    def test_fresh_object_per_call(self, source: Path) -> None:
        first = memoized_mapping("ns", [source], _Counter({1: 2.5}), float)
        first[1] = 999.0
        first[2] = 1.0
        second = memoized_mapping("ns", [source], _Counter({}), float)
        assert second == {1: 2.5}

    def test_namespaces_do_not_collide(self, source: Path) -> None:
        memoized_mapping("a", [source], _Counter({1: 1.0}), float)
        memoized_mapping("b", [source], _Counter({2: 2.0}), float)
        assert memoized_mapping("a", [source], _Counter({}), float) == {1: 1.0}
        assert memoized_mapping("b", [source], _Counter({}), float) == {2: 2.0}

    def test_params_do_not_collide(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 1.0}), float, params=("x",))
        memoized_mapping("ns", [source], _Counter({2: 2.0}), float, params=("y",))
        served = memoized_mapping("ns", [source], _Counter({}), float, params=("x",))
        assert served == {1: 1.0}


class TestFloatExactness:
    """A memo read must be bit-equal to the computation it replaces."""

    ADVERSARIAL = [
        0.1,
        1.0 / 3.0,
        6.879999999999999,
        6.88,
        2.220446049250313e-16,
        5e-324,  # smallest denormal
        1.7976931348623157e308,  # largest finite double
        -0.0,
        6.0,  # integral: json emits 6.0, but a hand-written memo may say 6
        1e16 + 2.0,
    ]

    def test_values_round_trip_exactly(self, source: Path) -> None:
        mapping = {i: v for i, v in enumerate(self.ADVERSARIAL)}
        memoized_mapping("ns", [source], _Counter(mapping), float)
        served = memoized_mapping("ns", [source], _Counter({}), float)
        assert served == mapping
        for i, v in mapping.items():
            # `==` treats -0.0 == 0.0; repr pins the sign too.
            assert repr(served[i]) == repr(v)

    def test_integer_literal_in_memo_decodes_to_float(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 6.0}), float)
        memo = next(source.parent.glob("*.ns.json"))
        memo.write_text('{"1": 6}')  # what a hand-edited or re-encoded memo looks like
        served = memoized_mapping("ns", [source], _Counter({}), float)
        assert served == {1: 6.0} and type(served[1]) is float


class TestNonFiniteRefused:
    """NaN never equals itself, so it is never memoized."""

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_not_written_and_recomputed_every_time(
        self, source: Path, bad: float
    ) -> None:
        compute = _Counter({1: 1.0, 2: bad})
        first = memoized_mapping("ns", [source], compute, float)
        second = memoized_mapping("ns", [source], compute, float)
        assert compute.calls == 2, "a non-finite mapping must not be served from a memo"
        assert not list(source.parent.glob("*.ns.json"))
        for got in (first, second):
            assert got[1] == 1.0
            assert math.isnan(got[2]) if math.isnan(bad) else got[2] == bad

    def test_encodable_rejects_non_finite(self) -> None:
        assert _encodable({1: 1.0}, float)
        assert not _encodable({1: float("nan")}, float)


# --------------------------------------------------------------------------
# memoized_mapping — the advisory guarantees
# --------------------------------------------------------------------------


class TestAdvisoryFallback:
    def test_source_change_invalidates(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 1.0}), float)
        source.write_bytes(b"source-bytes-v2")
        compute = _Counter({1: 2.0})
        assert memoized_mapping("ns", [source], compute, float) == {1: 2.0}
        assert compute.calls == 1

    def test_second_source_change_invalidates(
        self, tmp_path: Path, source: Path
    ) -> None:
        vintage = tmp_path / "vintage.parquet"
        vintage.write_bytes(b"v1")
        memoized_mapping("ns", [source, vintage], _Counter({1: 1.0}), float)
        vintage.write_bytes(b"v2")
        compute = _Counter({1: 2.0})
        assert memoized_mapping("ns", [source, vintage], compute, float) == {1: 2.0}
        assert compute.calls == 1

    def test_corrupt_memo_recomputes(
        self, source: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        memoized_mapping("ns", [source], _Counter({1: 1.0}), float)
        memo = next(source.parent.glob("*.ns.json"))
        memo.write_text("{not json")
        compute = _Counter({1: 1.0})
        with caplog.at_level(logging.WARNING, logger="market_sim.data.disk_memo"):
            assert memoized_mapping("ns", [source], compute, float) == {1: 1.0}
        assert compute.calls == 1
        assert "memo read failed" in caplog.text

    @pytest.mark.parametrize(
        "payload",
        [
            '["not", "an", "object"]',
            '{"not-an-int": 1.0}',
            '{"1": true}',  # bool is an int subclass and is not a heat rate
            '{"1": [1.0]}',
            '{"1": null}',
            '{"1": "6.88"}',  # a string where a float belongs
            '{"1": NaN}',  # the non-standard token json.loads accepts
        ],
    )
    def test_malformed_memo_recomputes(self, source: Path, payload: str) -> None:
        memoized_mapping("ns", [source], _Counter({1: 1.0}), float)
        memo = next(source.parent.glob("*.ns.json"))
        memo.write_text(payload)
        compute = _Counter({1: 1.0})
        assert memoized_mapping("ns", [source], compute, float) == {1: 1.0}
        assert compute.calls == 1

    def test_missing_source_falls_back_to_compute(self, tmp_path: Path) -> None:
        compute = _Counter({1: 1.0})
        assert memoized_mapping("ns", [tmp_path / "absent.xlsx"], compute, float) == {
            1: 1.0
        }
        assert compute.calls == 1

    def test_unwritable_directory_still_returns_the_computation(
        self, source: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom(*_args, **_kwargs):
            raise OSError("read-only file system")

        monkeypatch.setattr(Path, "write_text", _boom)
        compute = _Counter({1: 1.0})
        assert memoized_mapping("ns", [source], compute, float) == {1: 1.0}
        assert not list(source.parent.glob("*.ns.json"))

    def test_no_temp_file_is_left_behind(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({1: 1.0}), float)
        assert not list(source.parent.glob("*.tmp"))


class TestNeverPickle:
    """The memo carries data, never an executable payload."""

    def test_memo_is_plain_json_text(self, source: Path) -> None:
        memoized_mapping("ns", [source], _Counter({55641: 6.88}), float)
        memo = next(source.parent.glob("*.ns.json"))
        raw = memo.read_bytes()
        assert json.loads(raw.decode("utf-8")) == {"55641": 6.88}
        # pickle protocol >= 2 opens with \x80; protocol 0/1 payloads that would
        # matter here start with an opcode byte JSON never emits.
        assert not raw.startswith(b"\x80")

    def test_module_has_no_pickle_path(self) -> None:
        """No pickle import, name, attribute or keyword anywhere in the code.

        Asserted over the parsed AST rather than the raw text, so the module
        docstring's own explanation of *why* it never pickles cannot satisfy
        (or trip) the check.
        """
        import ast

        import market_sim.data.disk_memo as module

        tree = ast.parse(Path(module.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name != "pickle" for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "pickle"
            elif isinstance(node, ast.Name):
                assert node.id not in {"pickle", "allow_pickle"}
            elif isinstance(node, ast.Attribute):
                assert node.attr != "pickle"
            elif isinstance(node, ast.keyword):
                assert node.arg != "allow_pickle"


class TestDecodeMapping:
    """Direct cover for the strict re-typing helper."""

    def test_float_and_str(self) -> None:
        assert _decode_mapping({"1": 2.5}, float) == {1: 2.5}
        assert _decode_mapping({"1": "WEST"}, str) == {1: "WEST"}

    @pytest.mark.parametrize(
        "raw",
        [[], {"x": 1.0}, {"1": True}, {"1": None}, {"1": float("inf")}],
    )
    def test_rejects(self, raw: object) -> None:
        assert _decode_mapping(raw, float) is None
