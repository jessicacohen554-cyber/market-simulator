"""Byte-parity contract tests for ``scripts.lib.backcast_artifacts``.

The dashboard artifact codecs are a frozen wire format
(``docs/backcast-artifact-contract.md`` §4/§9): a re-render of unchanged data
MUST produce byte-identical output, or concurrent registrations conflict and
every registered keeper silently re-grades (CLAUDE.md rules 15/20). These tests
round-trip the *committed* ``runs/<id>.js`` payloads and ``bench/<ISO>/<year>``
parts through the library and assert the bytes come back identical, plus the
smaller codec/parser invariants.

Stdlib-only (no numpy/pandas) — the same constraint the Pages deploy runs under.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from scripts.lib import backcast_artifacts as ba
from scripts.lib import bench_stamp


# --------------------------------------------------------------------------- #
# gzb64 / ungzb64
# --------------------------------------------------------------------------- #
def test_gzb64_roundtrip():
    obj = {"b": 1, "a": [1, 2, 3], "nested": {"z": 0.5, "y": "text"}}
    assert ba.ungzb64(ba.gzb64(obj)) == obj


def test_gzb64_is_deterministic():
    obj = {"a": 1, "b": [2, 3]}
    assert ba.gzb64(obj) == ba.gzb64(obj)  # mtime=0 -> stable bytes


def test_gzb64_sort_keys_is_a_distinct_encoding():
    # The frozen backcast codec is sort_keys=False; the forecast-bands variant
    # sorts keys. For a payload whose key order differs from sorted order the
    # two must produce different bytes (both still decode to the same object).
    obj = {"b": 1, "a": 2}
    assert ba.gzb64(obj, sort_keys=False) != ba.gzb64(obj, sort_keys=True)
    assert ba.ungzb64(ba.gzb64(obj, sort_keys=True)) == obj


# --------------------------------------------------------------------------- #
# runs/<id>.js payload wrapper (WIRE FORMAT)
# --------------------------------------------------------------------------- #
def test_encode_decode_run_js_roundtrip():
    model = {"label": "demo", "years": {"2024": {"plants": {}}}}
    rid = "2026-01-02-demo"
    js = ba.encode_run_js(rid, model)
    assert js.startswith("window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};")
    assert f'window.BC.runGz["{rid}"]=' in js
    assert ba.decode_run_js(js) == model


def test_decode_run_js_raises_without_payload():
    with pytest.raises(ValueError):
        ba.decode_run_js("window.BC=window.BC||{};// no payload here")


def _committed_run_files() -> list[Path]:
    return sorted(ba.RUNS.glob("*.js")) if ba.RUNS.exists() else []


def test_committed_run_payloads_reencode_byte_identical():
    """Every committed ``runs/<id>.js`` re-encodes to identical bytes.

    This is the conflict-free-registration property: decode a committed payload,
    re-encode it with the same run id, and the bytes must match exactly.
    """
    run_files = _committed_run_files()
    if not run_files:
        pytest.skip("no committed runs/<id>.js payloads in this checkout")
    mismatches = []
    for path in run_files:
        original = path.read_text()
        model = ba.decode_run_js(original)
        remade = ba.encode_run_js(path.stem, model)
        if remade != original:
            mismatches.append(path.name)
    assert not mismatches, f"run payload re-encode drift: {mismatches}"


# --------------------------------------------------------------------------- #
# bench parts (WIRE FORMAT)
# --------------------------------------------------------------------------- #
def _committed_bench_parts() -> list[Path]:
    return sorted(ba.BENCH.rglob("*.json.gz")) if ba.BENCH.exists() else []


def test_committed_bench_parts_rewrite_byte_identical():
    """Re-writing a committed part is byte-identical — and drift is EXPLAINED.

    The determinism contract is what keeps concurrent registrations
    conflict-free, and it is also what let a stale part hide (nyiso-148): an
    un-refreshed part shows no diff until something regenerates it. Since the
    builder fingerprint was added, the contract is sharper, and this test now
    pins both halves:

    * a part written by the builder at HEAD MUST re-write to identical bytes;
    * a part that does NOT re-write identically MUST be one the stamp already
      flags as stale — i.e. every byte difference is accounted for by the
      staleness mechanism, and UNEXPLAINED drift still fails.
    """
    parts = _committed_bench_parts()
    if not parts:
        pytest.skip("no committed bench parts in this checkout")
    unexplained = []
    stale_seen = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for path in parts:
            iso = path.parent.name
            year = int(path.stem.split(".")[0])
            part = ba.load_bench_part(path)
            out = ba.write_bench_part(tmp, iso, year, part["meta"], part["bench"])
            if out.read_bytes() == path.read_bytes():
                continue
            if bench_stamp.is_stale(part):
                stale_seen.append(f"{iso}/{year}")
            else:
                unexplained.append(f"{iso}/{year}")
    assert not unexplained, (
        "bench part re-write drift NOT explained by the staleness stamp: "
        f"{unexplained} — these parts carry the current builder fingerprint yet "
        "do not reproduce, which means the writer is non-deterministic"
    )
    # `stale_seen` is expected to be non-empty until every ISO regenerates its
    # part (nyiso-148 §11); it is reported by scripts/check_bench_freshness.py,
    # not gated here.


def test_write_bench_part_pins_year_and_stamps_the_builder():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        out = ba.write_bench_part(tmp, "ERCOT", 2024, {"groups": ["a"]}, {"x": 1})
        assert out == tmp / "ERCOT" / "2024.json.gz"
        loaded = ba.load_bench_part(out)
        assert loaded == {
            "meta": {
                "groups": ["a"],
                "years": [2024],
                "builderFingerprint": bench_stamp.builder_fingerprint(),
            },
            "bench": {"x": 1},
        }
        # A part the current builder just wrote is never stale.
        assert not bench_stamp.is_stale(loaded)


def test_bench_stamp_is_deterministic_and_detects_staleness():
    """The fingerprint is content-derived, so it is stable and it discriminates."""
    fp = bench_stamp.builder_fingerprint()
    assert fp == bench_stamp.builder_fingerprint()
    assert len(fp) == 12 and all(c in "0123456789abcdef" for c in fp)
    # A part written before the stamp existed reads as stale, not as current.
    assert bench_stamp.part_fingerprint({"meta": {"years": [2024]}}) is None
    assert bench_stamp.is_stale({"meta": {"years": [2024]}})
    assert bench_stamp.is_stale({"meta": {"builderFingerprint": "0" * 12}})
    assert not bench_stamp.is_stale({"meta": {"builderFingerprint": fp}})


# --------------------------------------------------------------------------- #
# manifest.js writer/parser PAIR
# --------------------------------------------------------------------------- #
def test_manifest_js_write_parse_roundtrip():
    meta = {"ERCOT": {"groups": ["CC"], "years": [2024]}}
    manifest = [{"id": "2026-01-01-x", "iso": "ERCOT", "years": [2024]}]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "manifest.js"
        ba.write_manifest_js(path, meta, manifest)
        got_meta, got_manifest = ba.parse_manifest_js(path)
    assert got_meta == meta
    assert got_manifest == manifest


def test_parse_manifest_js_tolerates_bracket_semicolon_in_strings():
    # A definition string containing "];" must not truncate the parse
    # (the raw_decode-anchored contract, contract §3.4).
    meta = {"PJM": {"groups": [], "years": [2024]}}
    manifest = [{"id": "2026-01-01-x", "definition": "band [7,9]; see note};"}]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "manifest.js"
        ba.write_manifest_js(path, meta, manifest)
        got_meta, got_manifest = ba.parse_manifest_js(path)
    assert got_manifest[0]["definition"] == "band [7,9]; see note};"


def test_render_manifest_js_sort_keys_toggle():
    meta = {"B": 1, "A": 2}
    sorted_js = ba.render_manifest_js(meta, [], sort_keys=True)
    unsorted_js = ba.render_manifest_js(meta, [], sort_keys=False)
    # Default json.dumps separators (", " / ": ") — manifest.js is not compacted.
    assert '{"A": 2, "B": 1}' in sorted_js
    assert '{"B": 1, "A": 2}' in unsorted_js


# --------------------------------------------------------------------------- #
# sidecars / resolution
# --------------------------------------------------------------------------- #
def test_write_load_sidecar_roundtrip():
    entry = {"id": "2026-01-01-x", "iso": "ERCOT", "bundle": "results/calibration/x"}
    with tempfile.TemporaryDirectory() as td:
        reg = Path(td)
        path = ba.write_sidecar(entry, registry_dir=reg)
        assert path.read_text().endswith("}\n")  # indent=2 + trailing newline
        assert ba.load_sidecar("2026-01-01-x", registry_dir=reg) == entry
        assert [rec for _, rec in ba.iter_sidecars(reg)] == [entry]


def test_bundle_dir_for_guards_outside_calibration_root():
    repo = Path("/repo")
    assert ba.bundle_dir_for({"bundle": "results/calibration/x"}, repo=repo) == (
        repo / "results/calibration/x"
    )
    # Outside the calibration root -> None (retention safety guard).
    assert ba.bundle_dir_for({"bundle": "../../etc/passwd"}, repo=repo) is None
    assert ba.bundle_dir_for({}, repo=repo) is None


def test_resolve_run_id_by_id_and_by_bundle():
    with tempfile.TemporaryDirectory() as td:
        reg = Path(td)
        ba.write_sidecar(
            {"id": "2026-01-01-x", "bundle": "results/calibration/xbundle"},
            registry_dir=reg,
        )
        # by id
        assert ba.resolve_run_id("2026-01-01-x", registry_dir=reg) == "2026-01-01-x"
        # by bundle path
        assert (
            ba.resolve_run_id("results/calibration/xbundle", registry_dir=reg)
            == "2026-01-01-x"
        )
        with pytest.raises(SystemExit):
            ba.resolve_run_id("nonexistent-run", registry_dir=reg)
