"""caiso-180 outage re-audit: arm identity, sha ladder, envelope evidence, scoring.

The fail-closed instrument ``PRECHECK-caiso180-outage-reaudit-2026-08-07.md`` §3a
and §4 pre-register. It refuses to write its record unless every pre-registered
comparability condition holds, so a finding can never be assembled on arms that
are not actually comparable.

What it asserts, in the order the PRECHECK fixes them:

* **§4 — key-by-key ``scenario_config`` identity.** This session's delta is the
  *bytes of one data file*, never a ``ScenarioConfig`` field, so all three arms
  and the incumbent keeper must agree on **every** key. The comparison is over
  the union of key sets (a key present in one config and absent in another is a
  difference, not a skip) and **no key is exempted** — the caiso-175 predicate,
  not the caiso-174 one. Any difference at all stops the session.
* **§3a leg 1 — the sha ladder.** All three arms read one mutable path. Each
  arm's recorded pre-solve and post-solve sha256 of
  ``data/raw/campd-unit-outages-CAISO.csv`` must be equal to each other and to
  that arm's intended envelope state. An arm whose envelope moved under it is
  void.
* **§3a leg 2 — solved-output evidence.** Each arm is evidenced from its OWN
  bundle, never from the on-disk CSV (which cannot simultaneously evidence three
  arms). The per-arm outage-derate census is read back from the solve log and
  the availability ordering ``A1 <= A0`` and ``A1 <= A2`` in *derated tranches*
  — equivalently ``A1 >= A0, A2`` in available capability — must hold, because
  A1 carries strictly fewer outage windows.
* **§6.6 — the DOF ledger** must be UNCHANGED at ``n_entries`` 11 /
  ``n_residual`` 8. This session swaps input bytes and measures; it introduces
  no free parameter, so a moved count is a defect in the session itself.

Scoring is rubric **v3.1** for every arm and for the keeper, re-scored at this
head from committed artifacts (scorer-only, no LP) — the keeper's committed
``metrics.json`` predates v3.1 and still reads ``rubric_version 3.0`` /
``CALIBRATED-WITH-CAVEATS``, so quoting it directly would compare two different
rubrics.

Usage::

    uv run python scripts/probes/_caiso180_arm_identity.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/caiso175_tac_intake"
YEARS = (2023, 2024, 2025)

#: PRECHECK §6.6. The session's pre-registered ledger position; a move is a
#: defect in this session, so the instrument refuses to write.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 8

#: PRECHECK §2a. The three recovered envelope states, keyed by arm. Every value
#: is a sha256 of the exact bytes the arm's solve read.
ENVELOPES = {
    "A0": ("GUARD (current on-disk)", "c4ded33df08de5927fd58fa7200320353e73ceedfeb0084586ffd2e32f93ff5e"),
    "A1": ("PRE (49e85fb4^, pre-regeneration)", "7f80b94e1c5576d626cb9ea1c37fa312b73e5dbe2633d97b0ba23adae555ece0"),
    "A2": ("REGEN (49e85fb4, guard-off)", "a35990908aa2ea8f7ef62f3ee8ab1066e27c0c55c8c0a40080c4df29b4e85e9e"),
}

#: PRECHECK §2a/§2b window census, per arm per year, from the recovered blobs.
WINDOW_CENSUS = {
    "A0": {2023: 547, 2024: 458, 2025: 635},
    "A1": {2023: 439, 2024: 405, 2025: 509},
    "A2": {2023: 640, 2024: 622, 2025: 733},
}

ARMS = {
    "A0": REPO / "results/calibration/caiso180_a0_control",
    "A1": REPO / "results/calibration/caiso180_a1_pre",
    "A2": REPO / "results/calibration/caiso180_a2_regen",
}

#: Written by the session driver as each arm runs (PRECHECK §3a leg 1).
SHA_LEDGER = REPO / "results/calibration/_caiso180_sha_ledger.json"

OUT = REPO / "results/calibration/_caiso180_outage_reaudit.json"

_DERATE_RE = re.compile(
    r"unit-outage derate \(CAISO (\d{4})\): (\d+) plant-tranches derated"
)


class Failure(RuntimeError):
    """A pre-registered comparability condition failed: the session stops."""


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def check_config_identity(present: dict[str, Path]) -> dict:
    """Assert §4: every arm's scenario_config matches the keeper, key by key.

    Compares over the UNION of key sets so a key present in one config and
    absent in another counts as a difference rather than being skipped. Raises
    :class:`Failure` on any difference at all — no key is exempted and no
    allow-list is written after seeing the diff.
    """
    ref = _cfg(KEEPER)
    out = {"n_keys_keeper": len(ref), "arms": {}}
    diffs_total = 0
    for arm, bundle in present.items():
        cfg = _cfg(bundle)
        keys = set(ref) | set(cfg)
        diffs = {
            k: {"keeper": ref.get(k, "<ABSENT>"), arm: cfg.get(k, "<ABSENT>")}
            for k in sorted(keys)
            if ref.get(k, "<ABSENT>") != cfg.get(k, "<ABSENT>")
        }
        diffs_total += len(diffs)
        out["arms"][arm] = {
            "n_keys": len(cfg),
            "n_keys_compared": len(keys),
            "n_diffs": len(diffs),
            "diffs": diffs,
        }
    out["identical"] = diffs_total == 0
    if diffs_total:
        raise Failure(
            f"scenario_config identity FAILED: {diffs_total} key difference(s) "
            f"vs the keeper. PRECHECK §4 stops the session — the arms are not "
            f"comparable. Detail: {json.dumps(out['arms'], indent=1)[:2000]}"
        )
    return out


def check_sha_ladder(present: dict[str, Path]) -> dict:
    """Assert §3a leg 1: each arm's envelope was stable across its own solve."""
    if not SHA_LEDGER.exists():
        raise Failure(f"sha ledger {SHA_LEDGER} missing — §3a leg 1 unverifiable")
    ledger = json.loads(SHA_LEDGER.read_text())
    out = {}
    for arm in present:
        rec = ledger.get(arm)
        if not rec:
            raise Failure(f"sha ledger has no entry for arm {arm}")
        want = ENVELOPES[arm][1]
        before, after = rec.get("before"), rec.get("after")
        ok = before == after == want
        out[arm] = {
            "state": ENVELOPES[arm][0],
            "intended": want,
            "before": before,
            "after": after,
            "stable_and_correct": ok,
        }
        if not ok:
            raise Failure(
                f"arm {arm} envelope sha ladder FAILED: intended {want}, "
                f"before {before}, after {after}. The arm is void (§3a leg 1)."
            )
    return out


def envelope_evidence(logs: dict[str, Path], present: dict[str, Path]) -> dict:
    """Assert §3a leg 2: solved-output derate census orders as the windows do.

    A1 carries strictly fewer outage windows than A0 and A2 in every year, so
    its solve must derate no more plant-tranches than either. This is read from
    each arm's OWN solve log — never from the on-disk CSV, which cannot
    simultaneously evidence three arms.
    """
    census: dict[str, dict[int, int]] = {}
    for arm in present:
        log = logs.get(arm)
        if log is None or not log.exists():
            raise Failure(f"arm {arm} solve log missing — §3a leg 2 unverifiable")
        found = {
            int(y): int(n) for y, n in _DERATE_RE.findall(log.read_text(errors="replace"))
        }
        missing = [y for y in YEARS if y not in found]
        if missing:
            raise Failure(
                f"arm {arm} log carries no derate census for {missing} "
                f"— §3a leg 2 unverifiable"
            )
        census[arm] = found

    checks = []
    if {"A0", "A1"} <= set(census):
        for y in YEARS:
            checks.append(
                {
                    "claim": f"A1 <= A0 derated tranches ({y})",
                    "a1": census["A1"][y],
                    "a0": census["A0"][y],
                    "holds": census["A1"][y] <= census["A0"][y],
                }
            )
    if {"A1", "A2"} <= set(census):
        for y in YEARS:
            checks.append(
                {
                    "claim": f"A1 <= A2 derated tranches ({y})",
                    "a1": census["A1"][y],
                    "a2": census["A2"][y],
                    "holds": census["A1"][y] <= census["A2"][y],
                }
            )
    bad = [c for c in checks if not c["holds"]]
    if bad:
        raise Failure(
            f"§3a leg 2 FAILED — an arm's solved output does not evidence the "
            f"envelope it claims: {json.dumps(bad, indent=1)}"
        )
    return {
        "derated_plant_tranches": census,
        "window_census": {a: WINDOW_CENSUS[a] for a in present},
        "ordering_checks": checks,
    }


def check_dof_ledger(present: dict[str, Path]) -> dict:
    """Assert §6.6: every arm's DOF ledger is unchanged at 11 entries / 8 residual.

    Checked per arm (not once globally) because the ledger is built FROM a
    bundle: an arm that silently acquired a free parameter would only show up
    against its own bundle.
    """
    from scripts.build_dof_ledger import build_ledger

    out = {}
    for arm, bundle in present.items():
        led = build_ledger(bundle, "CAISO")
        n_e, n_r = led["n_entries"], led["n_residual"]
        ok = (n_e, n_r) == (KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL)
        out[arm] = {"n_entries": n_e, "n_residual": n_r, "unchanged": ok}
        if not ok:
            raise Failure(
                f"arm {arm} DOF ledger moved: {n_e}/{n_r} vs pre-registered "
                f"{KEEPER_N_ENTRIES}/{KEEPER_N_RESIDUAL} (PRECHECK §6.6). This "
                f"session introduces no free parameter, so a move is a defect here."
            )
    return out


def score(run_ids: dict[str, str]) -> dict:
    """Re-score every arm and the keeper at rubric v3.1 (scorer-only, no LP)."""
    from scripts.calibration_verdict import determine

    out = {}
    for tag, rid in run_ids.items():
        v = determine(rid)
        crit = {}
        for rec in v.get("records", []):
            crit.setdefault(rec["criterion"], {})[rec.get("year")] = {
                "status": rec.get("status"),
                "magnitude": rec.get("magnitude"),
                "model": rec.get("model"),
                "actual": rec.get("actual"),
                "key": rec.get("key"),
            }
        out[tag] = {
            "run_id": rid,
            "determination": v.get("determination"),
            "rubric_version": v.get("rubric_version"),
            "criteria": v.get("criteria"),
            "price_mean": crit.get("price_mean", {}),
            "records_by_criterion": {k: len(x) for k, x in crit.items()},
        }
    return out


def main() -> None:
    """Run every pre-registered check, then write the session record."""
    present = {a: b for a, b in ARMS.items() if (b / "run_config.json").exists()}
    if not present:
        sys.exit("no arm bundles found; solve at least A0 first.")

    logs = {
        a: Path(
            "/tmp/claude-0/-home-user-market-simulator/"
            "b48190de-546f-5e95-8d8a-27ac99d88a55/scratchpad"
        )
        / f"{a.lower()}_solve.log"
        for a in present
    }

    rec: dict = {
        "session": "caiso-180",
        "precheck": "results/calibration/PRECHECK-caiso180-outage-reaudit-2026-08-07.md",
        "arms_present": sorted(present),
        "arms_expected": sorted(ARMS),
        "partial_audit": sorted(present) != sorted(ARMS),
    }
    rec["config_identity"] = check_config_identity(present)
    rec["sha_ladder"] = check_sha_ladder(present)
    rec["envelope_evidence"] = envelope_evidence(logs, present)
    rec["dof_ledger"] = check_dof_ledger(present)

    ids_path = REPO / "results/calibration/_caiso180_run_ids.json"
    if ids_path.exists():
        rec["scoring"] = score(json.loads(ids_path.read_text()))

    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps({k: v for k, v in rec.items() if k != "scoring"}, indent=1)[:3000])


if __name__ == "__main__":
    main()
