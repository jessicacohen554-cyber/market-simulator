"""The key-provenance exception record must stay both COMPLETE and LIVE.

``docs/governance/key-provenance-exceptions.json`` lists every committed
``run_config.json`` whose recorded ``cache_key`` today's rules cannot recompute,
each with the recipe that derives its exact literal (capx D85, owner ruling Q59;
committed as a checked record by capx D85-R). A list like this fails in two
opposite directions and both are defects:

* **Incomplete** — a SIXTEENTH mismatch appears and nothing goes red, so the
  census quietly reports one more "mismatch" nobody has derived.
* **Stale** — a listed record starts reproducing again and the entry stays,
  which is a re-armable excuse for a mismatch that no longer exists (rule 26
  ``[R-DELETE]``: a deprecated thing that still parses is not deleted).

The first three tests measure the real record; the last two prove the gate
actually fires in each direction, against synthetic rows, so "it passed" is
evidence rather than an absence of evidence.

Offline by construction: every gate but ``G3_RECIPE`` is arithmetic over
committed bytes. One entry (the ERCOT golden fixture) has a ``vintage_sha``
recipe needing a blob a ``blob:none`` clone may not hold; these tests run with
``fetch=False`` and tolerate that ONE gate reading ``G3_UNVERIFIED`` — never a
``G3_RECIPE`` failure, which would mean the recipe was checked and is wrong.
``scripts/check_key_provenance.py`` (network-capable) verifies it for real.

**Why the seven census-backed tests carry ``@pytest.mark.slow`` (Y-27,
2026-09-07, docs/handoffs/FINDING-y27-fast-tier-timeout-2026-09-07.md).**
``K.census()`` costs ~5 s in the checkout a run was SOLVED in and ~570 s
anywhere else, and the difference is not incidental: ``cache_key()`` folds
checkout-absolute paths to ``<repo>`` / ``<data_root>`` sentinels using the
CURRENT checkout's ``REPO_ROOT``, so a committed payload recorded under
``/home/user/market-simulator`` only re-folds — and only reproduces its
recorded key — under that same prefix. On any other path (a GitHub runner at
``/home/runner/work/market-simulator/market-simulator``, a second local
clone) no ladder rung ever reproduces and :func:`K.classify` exhausts its
whole recipe search: measured 33-43 s per mismatch x 15 mismatches, on both
xdist workers. That is what took the 20-minute ``Fast test tier`` job past
its cap on every PR from 2026-09-07T16:47:43Z. The marker is a QUARANTINE,
not a verdict: the gate still runs in the full serial lane and through
``scripts/check_key_provenance.py``, and it comes back to the fast tier as
soon as ``classify`` is bounded (routed to the capx D85-R lane in the
FINDING, section 4). Note also that on a non-solving checkout every row
classifies ``unclassified-unreachable-commit`` rather than by its named
recipe, so the fast tier was measuring a degenerate case of this gate.
"""

from __future__ import annotations

import copy
import json

import pytest

from scripts.lib import key_provenance as K


@pytest.fixture(scope="module")
def record() -> dict:
    # fetch_vintages=False: these tests must pass on a blobless CI checkout with
    # no network. The vintage half of the classification ladder is then
    # unavailable, which the census reports as
    # ``unclassified_unreachable_commit`` rather than as a finding.
    return K.census(fetch_vintages=False)


@pytest.fixture(scope="module")
def exceptions() -> dict:
    return K.load_exceptions()


def _fatal(failures: list[dict]) -> list[dict]:
    """Gate failures that are not merely 'this recipe needs a blob we lack'."""
    return [
        f for f in failures if f["gate"] not in ("G3_UNVERIFIED", "G1_LAG_UNVERIFIED")
    ]


def test_exception_record_is_well_formed(exceptions):
    """Every entry names a record, its literal, its class, a recipe and a cite."""
    assert exceptions["entries"], "the exception record is empty"
    seen = set()
    for entry in exceptions["entries"]:
        path = entry["run_config"]
        assert path not in seen, f"{path} is listed twice"
        seen.add(path)
        assert entry["recorded_cache_key"], f"{path}: no recorded_cache_key"
        assert entry["class"], f"{path}: no class"
        assert entry["recipe"], f"{path}: no executable recipe"
        assert entry["citation"], f"{path}: no citation"
        assert entry["why"], f"{path}: no derivation prose"
    totals: dict[str, int] = {}
    for entry in exceptions["entries"]:
        totals[entry["class"]] = totals.get(entry["class"], 0) + 1
    assert exceptions["class_totals"] == totals, (
        "class_totals does not describe the entries it sits beside"
    )


@pytest.mark.slow
def test_census_has_zero_unknown_mismatches(record, exceptions):
    """Every non-reproducing committed record is a LISTED exception.

    This is the gate the whole record exists for. A failure here is a
    SIXTEENTH: stop and report it as a new finding — do not append it to the
    list to make this green.
    """
    listed = {e["run_config"] for e in exceptions["entries"]}
    mismatch = {r["run_config"] for r in record["mismatch_detail"]}
    # Q66 (capx D93): a class-rule record whose three legs hold — or whose
    # ancestry is merely undecidable offline — is not a sixteenth.
    classed = {
        p
        for p, v in K.lag_classifications(record, exceptions).items()
        if v["status"] in ("lag", "unverified")
    }
    unknown = sorted(mismatch - listed - classed)
    assert not unknown, (
        f"{len(unknown)} committed record(s) do not reproduce their cache_key and "
        f"are not in {K.EXCEPTIONS_PATH.name}: {unknown}. This is a SIXTEENTH — "
        "stop and report it as a new finding (capx D85 §5), do not append it here."
    )
    # And nothing is unclassified for a reason that is about the RECORD: a
    # mismatch the whole ladder could not derive is a finding. Rows whose only
    # unrun step was a vintage blob this clone lacks are counted apart and are
    # still gated, by their listed recipe, in the test below.
    assert record["unclassified"] == 0, (
        f"{record['unclassified']} mismatch(es) reproduce under NO recipe"
    )


@pytest.mark.slow
def test_every_listed_exception_still_binds_and_derives(record, exceptions):
    """No listed entry is stale, absent, mis-keyed, or wrongly derived."""
    failures = _fatal(K.check_exceptions(record, exceptions, fetch=False))
    assert not failures, "\n".join(
        f"[{f['gate']}] {f['run_config']}: {f['detail']}" for f in failures
    )


@pytest.mark.slow
def test_gate_fails_on_a_sixteenth_mismatch(record, exceptions):
    """G1: an unlisted non-reproducing record must fail the check."""
    doctored = copy.deepcopy(record)
    intruder = copy.deepcopy(doctored["rows"][0])
    intruder["run_config"] = "results/_synthetic_sixteenth/run_config.json"
    intruder["recorded_cache_key"] = "deadbeefdeadbeef"
    intruder["reproduces_recorded_key"] = False
    intruder["reproduces_at_declaration"] = False
    intruder["reproduces_live_surface"] = False
    intruder["reproduces_at_declaration_only"] = False
    intruder["classification"] = {"class": "unclassified", "reproduced": False}
    doctored["rows"].append(intruder)
    doctored["mismatch_detail"].append(intruder)

    failures = K.check_exceptions(doctored, exceptions, fetch=False)
    g1 = [f for f in failures if f["gate"] == "G1_UNKNOWN"]
    assert len(g1) == 1, f"a sixteenth mismatch did not trip G1: {failures}"
    assert g1[0]["run_config"] == intruder["run_config"]


@pytest.mark.slow
def test_gate_fails_on_a_stale_exception(record, exceptions):
    """G2: a listed record that has started reproducing must fail the check.

    This is the direction that is easy to get wrong — a check written only to
    catch new mismatches would go green while carrying a dead entry forever.
    """
    victim = exceptions["entries"][0]["run_config"]
    doctored = copy.deepcopy(record)
    for row in doctored["rows"]:
        if row["run_config"] == victim:
            # It now reproduces: the rules moved back, or the record was fixed.
            row["reproduces_recorded_key"] = True
            row["reproduces_at_declaration"] = True
            row["key_at_declaration"] = row["recorded_cache_key"]
            break
    else:  # pragma: no cover - the entry is asserted present elsewhere
        pytest.fail(f"{victim} is not in the census")
    doctored["mismatch_detail"] = [
        r for r in doctored["mismatch_detail"] if r["run_config"] != victim
    ]

    failures = K.check_exceptions(doctored, exceptions, fetch=False)
    g2 = [f for f in failures if f["gate"] == "G2_STALE"]
    assert len(g2) == 1, f"a stale exception did not trip G2: {failures}"
    assert g2[0]["run_config"] == victim
    assert "delete" in g2[0]["detail"].lower()


@pytest.mark.slow
def test_gate_fails_on_a_pruned_or_mis_keyed_entry(record, exceptions):
    """G4/G5: an entry describing a record that is gone, or a different key."""
    gone = copy.deepcopy(exceptions)
    gone["entries"] = copy.deepcopy(gone["entries"])
    gone["entries"][0] = dict(
        gone["entries"][0], run_config="results/_pruned_bundle/run_config.json"
    )
    g4 = [
        f
        for f in K.check_exceptions(record, gone, fetch=False)
        if f["gate"] == "G4_PRESENT"
    ]
    assert len(g4) == 1, "a pruned listed record did not trip G4"

    wrong = copy.deepcopy(exceptions)
    wrong["entries"] = copy.deepcopy(wrong["entries"])
    wrong["entries"][0] = dict(
        wrong["entries"][0], recorded_cache_key="0000000000000000"
    )
    g5 = [
        f
        for f in K.check_exceptions(record, wrong, fetch=False)
        if f["gate"] == "G5_KEY"
    ]
    assert len(g5) == 1, "a mis-keyed entry did not trip G5"


@pytest.mark.slow
def test_gate_fails_on_a_wrong_recipe(record, exceptions):
    """G3: an entry whose recipe does not reproduce its literal must fail.

    Uses a HEAD-rules entry so the check needs no blob.
    """
    offline = next(
        e for e in exceptions["entries"] if not e["recipe"].get("vintage_sha")
    )
    broken = copy.deepcopy(exceptions)
    broken["entries"] = [
        dict(e, recipe={"drop": ["iso"]})
        if e["run_config"] == offline["run_config"]
        else e
        for e in copy.deepcopy(broken["entries"])
    ]
    g3 = [
        f
        for f in K.check_exceptions(record, broken, fetch=False)
        if f["gate"] == "G3_RECIPE" and f["run_config"] == offline["run_config"]
    ]
    assert len(g3) == 1, "a recipe that does not reproduce its literal did not trip G3"


@pytest.mark.slow
def test_census_reports_both_key_constructions(record):
    """Repair 4: the census must never report one key and be blind to the other.

    A record that reproduces only with the solve surface AT ITS DECLARATION is
    capx D79's designed re-key, not a mismatch — the census counts it
    separately and this test pins that the split is reported at all, whatever
    its values are on the day.
    """
    for field in (
        "validated_under_both_constructions",
        "validated_at_declaration_only",
        "validated_live_surface_only",
    ):
        assert isinstance(record[field], int), f"census does not report {field}"
    assert record["instrument_validated"] == (
        record["validated_under_both_constructions"]
        + record["validated_at_declaration_only"]
        + record["validated_live_surface_only"]
    ), "the both-keys split does not account for every validated record"
    for row in record["rows"]:
        assert "key_at_declaration" in row and "key_live_surface" in row, (
            f"{row['run_config']} carries only one key construction"
        )


@pytest.mark.slow
def test_g6_is_green_and_fails_on_a_new_unregistered_field(record):
    """G6 (capx D91): a new UNREGISTERED ``ScenarioConfig`` field must be RED.

    The gate the payload-driven five are structurally blind to. G1-G5 hash only
    the fields a record STORED, and a field added after a bundle solved is never
    in that bundle's payload — which is how ``pjm_seam_neighbour_hourly_ladder``
    entered every config's digest at ``f2a834de`` while this suite stayed green
    (``docs/handoffs/FINDING-capx-d91-2026-09-09.md`` §3).

    Both directions are proved, because a gate that has only ever been seen
    green is indistinguishable from one that cannot fail.
    """
    baseline = set(json.loads(K.G6_BASELINE_PATH.read_text())["fields"])
    assert not K.unregistered_schema_drift(record, baseline=baseline), (
        "an unregistered ScenarioConfig field is off the G6 ratchet — register it "
        "in _CACHE_KEY_OPTIONAL_FIELDS + _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS, do "
        "NOT append it to the baseline"
    )
    # A field that IS registered, pretended un-registered, must be caught.
    victim = "pjm_seam_neighbour_hourly_ladder"
    assert victim in K._CACHE_KEY_OPTIONAL_FIELDS, (
        f"{victim} is the capx D91 registration; this test pins that it stays registered"
    )
    original = K._CACHE_KEY_OPTIONAL_FIELDS
    try:
        K._CACHE_KEY_OPTIONAL_FIELDS = tuple(x for x in original if x != victim)
        drift = K.unregistered_schema_drift(record, baseline=baseline)
    finally:
        K._CACHE_KEY_OPTIONAL_FIELDS = original
    assert victim in drift, "G6 cannot fail — it does not detect an unregistered field"
    assert drift[victim], f"G6 named {victim} but no record exposes it"


def test_exception_record_json_is_committed_and_parses():
    """The record is a committed artifact, not something a run regenerates."""
    assert K.EXCEPTIONS_PATH.exists(), f"{K.EXCEPTIONS_PATH} is not committed"
    json.loads(K.EXCEPTIONS_PATH.read_text())


# --------------------------------------------------------------------------- #
# The Q66 ``lag`` CLASS RULE (capx D93) — both directions, synthetic, offline
# --------------------------------------------------------------------------- #
# "A gate seen only green is indistinguishable from one that cannot fail"
# (capx D91). These build one synthetic record from the live dataclass and an
# injected ancestry oracle, so they need no census, no commits and no network
# and run in the fast tier.
_LAG_FIELD = "pjm_seam_neighbour_hourly_ladder"
_REG_SHA = "a" * 40
_SOLVE_SHA = "b" * 40


def _lag_row(**over) -> dict:
    """A record that hashed ``_LAG_FIELD`` at its drop value before registration."""
    from dataclasses import asdict

    payload = K._jsonable(asdict(K.ScenarioConfig()))
    drop_at = K._jsonable(K.cache_key_drop_defaults()[_LAG_FIELD])
    payload[_LAG_FIELD] = drop_at
    recorded = K.head_key(payload, undrop=(_LAG_FIELD,))
    assert recorded != K.head_key(payload), "synthetic record would reproduce"
    row = {
        "run_config": "results/_synthetic_lag/run_config.json",
        "reproduces_recorded_key": False,
        "recorded_cache_key": recorded,
        "scenario_config": payload,
        "git_sha": _SOLVE_SHA,
        "git_basis_sha": _SOLVE_SHA,
        "git_dirty": False,
        "git_changed_files": [],
    }
    row.update(over)
    return row


def _gates(row: dict, ancestor) -> tuple[dict, list[str]]:
    record = {"rows": [row], "mismatch_detail": [row]}
    table = [{"field": _LAG_FIELD, "registration_sha": _REG_SHA}]
    lag = K.lag_classifications(
        record,
        {"entries": []},
        table,
        ancestry=lambda reg, solve: ancestor,
        resolve=lambda sha: sha,
    )
    failures = K.check_exceptions(record, {"entries": []}, fetch=False, lag=lag)
    return lag, [f["gate"] for f in failures]


def test_q66_lag_record_classifies_lag_and_does_not_fail():
    """All three legs hold: classified ``lag``, reported, no gate failure."""
    lag, gates = _gates(_lag_row(), ancestor=False)
    verdict = lag["results/_synthetic_lag/run_config.json"]
    assert verdict["status"] == "lag" and verdict["field"] == _LAG_FIELD
    assert gates == [], f"a genuine lag record failed: {gates}"


def test_q66_perturbed_literal_fails_as_lag_signature_without_reproduction():
    """Payload + sha legs hold, the literal does not reproduce: a FAILURE."""
    _, gates = _gates(_lag_row(recorded_cache_key="deadbeefdeadbeef"), ancestor=False)
    assert gates == ["G1_LAG_NO_REPRODUCE"], gates


def test_q66_record_not_carrying_the_field_fails_normally():
    """No payload leg (field absent) — the class never applies: ``G1_UNKNOWN``."""
    row = _lag_row()
    row["scenario_config"] = dict(row["scenario_config"])
    row["scenario_config"].pop(_LAG_FIELD)
    lag, gates = _gates(row, ancestor=False)
    assert not lag and gates == ["G1_UNKNOWN"], (lag, gates)


def test_q66_post_registration_sha_fails_normally():
    """The registration IS in the solve's history: not a lag, ``G1_UNKNOWN``."""
    lag, gates = _gates(_lag_row(), ancestor=True)
    assert not lag and gates == ["G1_UNKNOWN"], (lag, gates)


def test_q66_declared_fallbacks_fail_the_sha_leg():
    """No sha, or a dirty tree that may carry scenarios.py: ``G1_UNKNOWN``."""
    for over in (
        {"git_sha": None, "git_basis_sha": None},
        {"git_dirty": True, "git_changed_files": None},
        {
            "git_dirty": True,
            "git_changed_files": ["src/market_sim/config/scenarios.py"],
        },
    ):
        lag, gates = _gates(_lag_row(**over), ancestor=False)
        assert not lag and gates == ["G1_UNKNOWN"], (over, lag, gates)
    # A tree dirty only OUTSIDE the registration file keeps the leg (addendum A1).
    lag, gates = _gates(
        _lag_row(git_dirty=True, git_changed_files=["docs/x.md"]), ancestor=False
    )
    assert gates == [], gates


def test_q66_undecidable_ancestry_is_unverified_not_silent():
    """Reproduces, ancestry undecidable here: ``G1_LAG_UNVERIFIED``, never a pass."""
    _, gates = _gates(_lag_row(), ancestor=None)
    assert gates == ["G1_LAG_UNVERIFIED"], gates


def test_q66_registration_table_is_well_formed():
    """Every row is one registration: a registered field and a full commit sha."""
    rows = K.load_lag_registrations()
    assert rows, "the class-rule table is empty"
    fields_seen = set()
    for r in rows:
        assert r["field"] in K._CACHE_KEY_OPTIONAL_FIELDS, (
            f"{r['field']} is not registered — a row names a REGISTRATION"
        )
        assert len(r["registration_sha"]) == 40, r
        assert r["field"] not in fields_seen, f"{r['field']} listed twice"
        fields_seen.add(r["field"])
        assert r.get("citation"), r


def test_q66_field_carried_off_its_drop_value_is_not_lag():
    """An ARMED value was never dropped by either rule: the class cannot apply."""
    row = _lag_row()
    row["scenario_config"] = dict(row["scenario_config"], **{_LAG_FIELD: True})
    lag, gates = _gates(row, ancestor=False)
    assert not lag and gates == ["G1_UNKNOWN"], (lag, gates)
