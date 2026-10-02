"""Tests for ``scripts/promote_keeper.py`` — step order and the exceptions carry.

Two defects, each finished by hand in four promotions on 2026-10-02 (NYISO
#7041, SPP-107 #7025, closeout-CAISO #7050):

* ORDER. The audit ran BEFORE the prune, so E13 ("every registered run is the
  keeper or stamped to it") always failed on the outgoing keeper. The audit now
  runs twice: a pre-prune pass tolerating only E13 (E11 needs the former bundle
  on disk), and a strict post-prune pass that refuses to finish on any FAIL.
* ATTESTATION. The fresh attestation dropped the outgoing keeper's C3c ledger
  ``exceptions``; a ledgered C3c then read FAIL (CAISO C3c 2024). Each outgoing
  entry is now carried to the incoming bundle that carries its year and
  re-measured there; an entry that no longer applies is refused unless
  ``--drop-exception`` drops it with a recorded reason.

Trivial cases only: toy registries in ``tmp_path``, an injected measurer, no
scorer and no live registry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts import promote_keeper as pk
from scripts.audit_keepers import orphan_run_findings

ISO = "CAISO"
OLD = "2026-10-01-old-keeper"
NEW = "2026-10-02-new-keeper"
TODAY = "2026-10-02"


def _sidecar(registry: Path, run_id: str, bundle: str, years: list[int]) -> None:
    rec = {"id": run_id, "iso": ISO, "years": years, "bundle": bundle}
    (registry / f"{run_id}.json").write_text(json.dumps(rec))


def _bundle(root: Path, name: str, exceptions: list[dict] | None) -> Path:
    b = root / "results" / "calibration" / name
    b.mkdir(parents=True)
    if exceptions is not None:
        (b / "calibration_attestation.json").write_text(
            json.dumps({"governance": {"attested_by": "x"}, "exceptions": exceptions})
        )
    return b


C3C_2024 = {
    "criterion": "price_tail",
    "year": 2024,
    "kind": "model-class",
    "magnitude": "model 0 h vs actual RT 35 h (outgoing bundle)",
    "reason": "OWNER-SIGNED model-class limitation",
}


def _fail(model: float, actual: float) -> dict:
    return {
        "criterion": "price_tail",
        "key": None,
        "status": "FAIL",
        "model": model,
        "actual": actual,
        "magnitude": f"model {model:.0f}h vs RT actual {actual:.0f}h",
    }


# --------------------------------------------------------------------------
# (1) ORDER — E13 passes after the prune, and the strict audit follows it
# --------------------------------------------------------------------------
def test_toy_two_run_iso_passes_e13_after_prune(tmp_path: Path) -> None:
    """Incoming designated, outgoing still registered: E13 fails; pruned: it passes."""
    _sidecar(tmp_path, OLD, "results/calibration/old", [2019, 2020])
    _sidecar(tmp_path, NEW, "results/calibration/new", [2019, 2020])

    before, _ = orphan_run_findings(ISO, NEW, tmp_path)
    assert len(before) == 1 and OLD in before[0]

    (tmp_path / f"{OLD}.json").unlink()  # what prune_iso_runs does to the sidecar
    after, years = orphan_run_findings(ISO, NEW, tmp_path)
    assert after == []
    assert years == [2019, 2020]


def test_main_audits_strictly_after_the_prune(monkeypatch, tmp_path: Path) -> None:
    """Order: register → attest → designate → status → pre-audit → prune → audit → parity."""
    calls: list[str] = []
    bundle = _bundle(tmp_path, "new", [])
    monkeypatch.setattr(pk, "REPO", tmp_path)
    monkeypatch.setattr(pk, "REGISTRY", tmp_path / "registry")
    monkeypatch.setattr(pk, "COMPLETE", tmp_path / "complete.json")
    monkeypatch.setattr(pk, "PROGRAM_STATUS", tmp_path / "program-status.json")
    monkeypatch.setattr(pk, "preflight", lambda b: [2024])
    monkeypatch.setattr(pk, "registered_years", lambda iso: ({2024}, [OLD]))
    monkeypatch.setattr(pk, "outgoing_exceptions", lambda *a: [])
    monkeypatch.setattr(
        pk, "register", lambda label, b, dry: calls.append("register") or NEW
    )
    monkeypatch.setattr(pk, "attest", lambda *a, **k: calls.append("attest"))
    monkeypatch.setattr(pk.keeper_store, "load_shard", lambda *a: {"keeper": OLD})
    monkeypatch.setattr(
        pk.keeper_store, "write_keeper", lambda *a, **k: calls.append("designate")
    )
    monkeypatch.setattr(pk, "rekey_complete", lambda *a, **k: calls.append("rekey"))
    monkeypatch.setattr(pk, "rekey_gate_a", lambda *a, **k: None)
    monkeypatch.setattr(
        pk, "audit", lambda iso, tolerate, dry: calls.append(f"audit{list(tolerate)}")
    )

    def fake_run(args, dry, capture=False):
        calls.append(Path(args[1]).stem)
        return ""

    monkeypatch.setattr(pk, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["promote_keeper.py", "--iso", ISO, "--bundle", str(bundle), "--label", "x"],
    )
    pk.main()
    assert calls == [
        "register",
        "attest",
        "designate",
        "rekey",
        "build_status",
        "audit['E13']",
        "prune_iso_runs",
        "audit[]",
        "check_registry_payload_parity",
    ]


def test_audit_tolerates_only_the_named_codes(monkeypatch) -> None:
    """Pre-prune: an E13 FAIL is tolerated, any other FAIL stops before the prune."""
    findings = [
        {"level": "FAIL", "code": "E13", "run_id": NEW, "msg": "orphan"},
        {"level": "OK", "code": "E1", "run_id": NEW, "msg": "ok"},
    ]

    class Res:
        returncode = 1
        stderr = ""

        def __init__(self, f):
            self.stdout = json.dumps({"fail": 1, "warn": 0, "findings": f})

    monkeypatch.setattr(pk.subprocess, "run", lambda *a, **k: Res(findings))
    pk.audit(ISO, tolerate=("E13",), dry=False)  # passes
    with pytest.raises(SystemExit, match="1 FAIL"):
        pk.audit(ISO, tolerate=(), dry=False)  # post-prune is strict

    findings.append({"level": "FAIL", "code": "E11", "run_id": NEW, "msg": "lineage"})
    with pytest.raises(SystemExit, match="1 FAIL"):
        pk.audit(ISO, tolerate=("E13",), dry=False)


# --------------------------------------------------------------------------
# (2) ATTESTATION — the outgoing C3c ledger is carried and re-measured
# --------------------------------------------------------------------------
def test_outgoing_exceptions_reads_keeper_and_skips_incoming(tmp_path: Path) -> None:
    """The outgoing keeper's entries are collected; a re-designated bundle is not."""
    reg = tmp_path / "registry"
    reg.mkdir()
    old = _bundle(tmp_path, "old", [C3C_2024])
    new = _bundle(tmp_path, "new", [])
    _sidecar(reg, OLD, "results/calibration/old", [2024])

    got = pk.outgoing_exceptions(ISO, OLD, reg, tmp_path, [new])
    assert got == [(OLD, C3C_2024)]
    assert pk.outgoing_exceptions(ISO, OLD, reg, tmp_path, [old]) == []
    assert pk.outgoing_exceptions(ISO, None, reg, tmp_path, [new]) == []


def test_c3c_exception_is_carried_and_remeasured(tmp_path: Path) -> None:
    """The owner-signed entry survives, with the INCOMING bundle's numbers."""
    new = _bundle(tmp_path, "new", [])
    existing = {new: []}
    seen: list[tuple[Path, int]] = []

    def measure(b: Path, y: int) -> dict:
        seen.append((b, y))
        return _fail(2, 41)

    add, dropped, _ = pk.plan_exception_carry(
        [(OLD, C3C_2024)], {new: [2023, 2024]}, new, existing, {}, measure, TODAY
    )
    assert seen == [(new, 2024)]
    assert dropped == {}
    (entry,) = add[new]
    assert entry["kind"] == "model-class"  # the owner's classification survives
    assert entry["reason"] == C3C_2024["reason"]
    assert entry["magnitude"].startswith("model 2h vs RT actual 41h")
    assert "RE-MEASURED on new" in entry["magnitude"]
    cf = entry["carried_forward"]
    assert (cf["model"], cf["actual"], cf["remeasured"]) == (2, 41, True)
    assert cf["magnitude_outgoing"] == C3C_2024["magnitude"]

    pk.write_exception_carry(add, dropped, existing, touched=set(), dry=False)
    att = json.loads((new / "calibration_attestation.json").read_text())
    assert att["governance"] == {"attested_by": "x"}  # untouched
    assert [e["year"] for e in att["exceptions"]] == [2024]


def test_routing_dry_pass_does_not_measure(tmp_path: Path) -> None:
    """Step 1b (measure=None) checks routing only — nothing is added yet."""
    new = _bundle(tmp_path, "new", [])
    add, dropped, log = pk.plan_exception_carry(
        [(OLD, C3C_2024)], {new: [2024]}, new, {new: []}, {}, None, TODAY
    )
    assert add == {} and dropped == {}
    assert log and log[0].startswith("ROUTED price_tail:2024")


def test_exception_whose_year_is_gone_refuses(tmp_path: Path) -> None:
    """A ledgered year the incoming span no longer carries is refused, not dropped."""
    new = _bundle(tmp_path, "new", [])
    with pytest.raises(SystemExit, match="price_tail:2024.*no longer applies"):
        pk.plan_exception_carry(
            [(OLD, C3C_2024)], {new: [2025]}, new, {new: []}, {}, None, TODAY
        )


def test_gone_year_drops_only_with_a_recorded_reason(tmp_path: Path) -> None:
    """``--drop-exception`` is the one way past the refusal, and the reason is kept."""
    new = _bundle(tmp_path, "new", [])
    drops = pk._parse_drops(["price_tail:2024=2024 left the span (owner ruling X)"])
    add, dropped, _ = pk.plan_exception_carry(
        [(OLD, C3C_2024)], {new: [2025]}, new, {new: []}, drops, None, TODAY
    )
    assert add == {}
    (rec,) = dropped[new]
    assert rec["dropped"]["reason"] == "2024 left the span (owner ruling X)"
    assert rec["dropped"]["source_run"] == OLD

    pk.write_exception_carry(add, dropped, {new: []}, touched=set(), dry=False)
    att = json.loads((new / "calibration_attestation.json").read_text())
    assert att["exceptions"] == []
    assert att["exceptions_dropped"][0]["year"] == 2024


def test_c3c_that_now_passes_refuses(tmp_path: Path) -> None:
    """A stale C3c number is never silently kept: PASS on the incoming bundle refuses."""
    new = _bundle(tmp_path, "new", [])
    passing = {**_fail(30, 35), "status": "PASS"}
    with pytest.raises(SystemExit, match="reads PASS"):
        pk.plan_exception_carry(
            [(OLD, C3C_2024)],
            {new: [2024]},
            new,
            {new: []},
            {},
            lambda b, y: passing,
            TODAY,
        )


def test_stray_drop_and_malformed_drop_refuse(tmp_path: Path) -> None:
    """A drop naming no outgoing entry (a typo) and a reasonless drop both refuse."""
    new = _bundle(tmp_path, "new", [])
    with pytest.raises(SystemExit, match="named no outgoing ledger entry"):
        pk.plan_exception_carry(
            [(OLD, C3C_2024)],
            {new: [2024]},
            new,
            {new: []},
            {"price_tail:2042": "typo"},
            lambda b, y: _fail(0, 35),
            TODAY,
        )
    with pytest.raises(SystemExit, match="criterion:year=<reason>"):
        pk._parse_drops(["price_tail:2024"])


def test_entry_routes_to_the_fold_carrying_its_year(tmp_path: Path) -> None:
    """A 2021 entry lands on the 2019-2021 fold, not the keeper span."""
    span = _bundle(tmp_path, "span", [])
    fold = _bundle(tmp_path, "fold", [])
    entry = {**C3C_2024, "year": 2021}
    add, _, _ = pk.plan_exception_carry(
        [(OLD, entry)],
        {span: [2022, 2023], fold: [2019, 2020, 2021]},
        span,
        {span: [], fold: []},
        {},
        lambda b, y: _fail(89, 27),
        TODAY,
    )
    assert list(add) == [fold]


def test_incoming_own_entry_stands_and_is_stamped(tmp_path: Path) -> None:
    """An entry the lane already wrote is not duplicated; its re-measure is stamped."""
    own = {**C3C_2024, "magnitude": "lane-written text"}
    new = _bundle(tmp_path, "new", [own])
    existing = {new: pk._own_exceptions(new)}
    add, _, log = pk.plan_exception_carry(
        [(OLD, C3C_2024)],
        {new: [2024]},
        new,
        existing,
        {},
        lambda b, y: _fail(0, 35),
        TODAY,
    )
    assert add == {}
    assert existing[new][0]["magnitude"] == "lane-written text"
    assert existing[new][0]["carried_forward"]["actual"] == 35
    assert log[0].startswith("KEPT price_tail:2024")


def test_non_ledgerable_entry_is_carried_labelled_not_remeasured(
    tmp_path: Path,
) -> None:
    """Inert (non-C3c) entries are kept as record, explicitly marked not re-measured."""
    new = _bundle(tmp_path, "new", [])
    storage = {"criterion": "storage", "year": 2024, "magnitude": "+1515%"}
    span = {"criterion": "fuelmix", "year": "2020-2025", "magnitude": "oil"}
    add, _, _ = pk.plan_exception_carry(
        [(OLD, storage), (OLD, span)],
        {new: [2024]},
        new,
        {new: []},
        {},
        lambda b, y: pytest.fail("non-C3c entries are never measured"),
        TODAY,
    )
    got = add[new]
    assert [e["criterion"] for e in got] == ["storage", "fuelmix"]
    assert all(e["carried_forward"]["remeasured"] is False for e in got)
    assert "not ledgerable" in got[0]["carried_forward"]["why"]
    assert "no single year" in got[1]["carried_forward"]["why"]
