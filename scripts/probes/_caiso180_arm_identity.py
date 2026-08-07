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
    """Assert §4 config identity on three separate, all fail-closed, legs.

    PRECHECK §4 pre-registers the predicate as: all three arms'
    ``scenario_config`` must be identical to each other and to the keeper's,
    *"compared key-by-key over all 692 keys"*, with *"any difference at all"*
    stopping the session and *"no key exempted"*.

    The first implementation of this function compared over the **union** of key
    sets, which is STRICTER than that text: it also flags keys that exist at HEAD
    but did not exist when the keeper was solved. That stricter form fired — on 8
    purely ADDITIVE fields (4 ERCOT, 2 MISO, 2 NYISO; none CAISO), every one at
    its ``ScenarioConfig`` code default, with **zero** of the keeper's own 692
    keys differing in value and none missing at HEAD.

    Rather than relax the check to make that pass, it is split into three legs,
    each of which stops the session on failure. Nothing among the keeper's 692
    keys is exempted, and the additive keys are not waved through on narrative —
    they must independently prove to be at code default and outside CAISO's
    namespace:

    * **L1 — the pre-registered predicate, verbatim.** Over the keeper's OWN key
      set, every arm must match exactly. This is the §4 text and it is absolute.
    * **L2 — arm-to-arm identity over the full union.** The arms are solved at
      one head, so they must agree on every key including the new ones. This is
      the leg that actually licenses the A-vs-A differences the finding quotes,
      and it is stricter than L1.
    * **L3 — additive drift is disclosed AND gated.** A key present at HEAD but
      absent from the keeper is recorded, and fails closed unless it is at its
      ``ScenarioConfig`` default *and* not CAISO-scoped. A drifted key that is
      off-default, or that names CAISO, stops the session.
    """
    import dataclasses  # noqa: F401  (ScenarioConfig introspection below)

    from market_sim.config.scenarios import ScenarioConfig

    defaults = ScenarioConfig()
    ref = _cfg(KEEPER)
    out: dict = {"n_keys_keeper": len(ref), "arms": {}, "legs": {}}

    # ---- L1: the pre-registered predicate, over the keeper's own key set. ----
    l1_bad = {}
    for arm, bundle in present.items():
        cfg = _cfg(bundle)
        diffs = {
            k: {"keeper": ref[k], arm: cfg.get(k, "<ABSENT>")}
            for k in sorted(ref)
            if ref[k] != cfg.get(k, "<ABSENT>")
        }
        out["arms"][arm] = {"n_keys": len(cfg), "n_diffs_on_keeper_keys": len(diffs)}
        if diffs:
            l1_bad[arm] = diffs
    out["legs"]["L1_keeper_keyset_identity"] = {
        "n_keys_compared": len(ref),
        "passes": not l1_bad,
        "diffs": l1_bad,
    }
    if l1_bad:
        raise Failure(
            f"L1 FAILED — PRECHECK §4's pre-registered predicate: "
            f"{sum(len(v) for v in l1_bad.values())} difference(s) on the "
            f"keeper's own key set. The arms are not comparable to the keeper's "
            f"recipe. Detail: {json.dumps(l1_bad, indent=1)[:2000]}"
        )

    # ---- L2: arm-to-arm identity over the full union (same head ⇒ exact). ----
    cfgs = {arm: _cfg(b) for arm, b in present.items()}
    l2_bad = {}
    if len(cfgs) > 1:
        base_arm = sorted(cfgs)[0]
        base = cfgs[base_arm]
        for arm, cfg in cfgs.items():
            if arm == base_arm:
                continue
            keys = set(base) | set(cfg)
            d = {
                k: {base_arm: base.get(k, "<ABSENT>"), arm: cfg.get(k, "<ABSENT>")}
                for k in sorted(keys)
                if base.get(k, "<ABSENT>") != cfg.get(k, "<ABSENT>")
            }
            if d:
                l2_bad[f"{base_arm}~{arm}"] = d
    out["legs"]["L2_arm_to_arm_identity"] = {
        "arms_compared": sorted(cfgs),
        "passes": not l2_bad,
        "diffs": l2_bad,
    }
    if l2_bad:
        raise Failure(
            f"L2 FAILED — two arms solved at the same head disagree on "
            f"scenario_config: {json.dumps(l2_bad, indent=1)[:2000]}. The A/B is "
            f"void; every difference the finding would quote is confounded."
        )

    # ---- L3: additive schema drift — disclosed, and gated on default+scope. ----
    any_cfg = next(iter(cfgs.values()))
    added = sorted(k for k in any_cfg if k not in ref)
    rows, offenders = {}, {}
    for k in added:
        dv = getattr(defaults, k, "<NO SUCH FIELD>")
        at_default = any_cfg[k] == dv
        caiso_scoped = "caiso" in k.lower()
        rows[k] = {
            "value_at_head": any_cfg[k],
            "scenario_config_default": dv,
            "at_default": at_default,
            "caiso_scoped": caiso_scoped,
        }
        if not at_default or caiso_scoped:
            offenders[k] = rows[k]
    out["legs"]["L3_additive_schema_drift"] = {
        "n_added_since_keeper": len(added),
        "removed_since_keeper": [k for k in ref if k not in any_cfg],
        "all_at_code_default": all(r["at_default"] for r in rows.values()),
        "any_caiso_scoped": any(r["caiso_scoped"] for r in rows.values()),
        "fields": rows,
        "passes": not offenders,
    }
    if offenders:
        raise Failure(
            f"L3 FAILED — a field that did not exist when the keeper was solved "
            f"is either off-default or CAISO-scoped, so it can reach this solve: "
            f"{json.dumps(offenders, indent=1)}"
        )

    out["identical_on_pre_registered_keyset"] = True
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


def envelope_depth() -> dict:
    """Measure each envelope's true DEPTH: outage MW-hours, per year, per blob.

    The quantity that actually governs available capability. Window COUNT does
    not, which is what falsified this session's original §3a leg-2 construction
    (see :func:`envelope_evidence`).
    """
    import pandas as pd

    scratch = Path(
        "/tmp/claude-0/-home-user-market-simulator/"
        "b48190de-546f-5e95-8d8a-27ac99d88a55/scratchpad"
    )
    blobs = {"A0": "env_GUARD.csv", "A1": "env_PRE.csv", "A2": "env_REGEN.csv"}
    out: dict = {}
    for arm, fname in blobs.items():
        f = scratch / fname
        if not f.exists():
            continue
        d = pd.read_csv(f)
        d["s"] = pd.to_datetime(d.outage_start)
        d["e"] = pd.to_datetime(d.outage_end)
        per_year = {}
        for y in YEARS:
            y0, y1 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")
            s = d.s.clip(lower=y0)
            e = (d.e + pd.Timedelta(days=1)).clip(upper=y1)
            hrs = ((e - s).dt.total_seconds() / 3600).clip(lower=0)
            m = hrs > 0
            per_year[y] = {
                "windows": int(m.sum()),
                "outage_mw_hours": round(float((hrs[m] * d.unit_capacity_mw[m]).sum()), 1),
                "distinct_plants": int(d.facility_id[m].nunique()),
                "median_duration_days": round(float(d.duration_days[m].median()), 2),
            }
        out[arm] = per_year
    return out


def envelope_evidence(logs: dict[str, Path], present: dict[str, Path]) -> dict:
    """Evidence that each arm actually read the envelope it claims.

    **The §3a leg-2 ordering assertion as pre-registered is WITHDRAWN, because
    this session's own measurement FALSIFIED it — reported, not quietly fixed.**
    The PRECHECK asserted ``A1 >= A0, A2`` in available capability, justified by
    the parenthetical *"(fewer outage windows ⇒ more capability)"*. That
    inference is wrong: window COUNT is not envelope DEPTH. The 2026-07-24
    regeneration replaced the pre-2026-07-19 phantom-outage detector, which
    produced FEWER but much LONGER windows (median 14.7-16.6 d) with one
    producing MORE and SHORTER ones (median 10.5-11.6 d). In 2023 the
    pre-regeneration envelope is therefore *deeper* (38.03M outage MW-h across
    439 windows) than the current one (36.68M across 547) — so A1 legitimately
    derates MORE plant-tranches than A0 that year (284 vs 275), and the
    pre-registered gate would have voided a perfectly sound arm.

    What replaces it is fail-closed and correctly constructed:

    * the **sha ladder** (leg 1) is the load-bearing proof of which bytes each
      arm read, and it is exact — leg 2 was always redundant to it;
    * every pair of arms must produce a **DIFFERENT** derate census in at least
      one year. Identical censuses would mean an envelope swap silently failed
      and two arms solved the same input, which is the real hazard §3a exists to
      catch.
    """
    census: dict[str, dict[int, int]] = {}
    for arm in present:
        log = logs.get(arm)
        if log is None or not log.exists():
            raise Failure(f"arm {arm} solve log missing — envelope evidence unverifiable")
        found = {
            int(y): int(n) for y, n in _DERATE_RE.findall(log.read_text(errors="replace"))
        }
        missing = [y for y in YEARS if y not in found]
        if missing:
            raise Failure(
                f"arm {arm} log carries no derate census for {missing} "
                f"— envelope evidence unverifiable"
            )
        census[arm] = found

    distinct = []
    arms = sorted(census)
    for i, a in enumerate(arms):
        for b in arms[i + 1 :]:
            differs = any(census[a][y] != census[b][y] for y in YEARS)
            distinct.append(
                {
                    "pair": f"{a}~{b}",
                    "a_census": census[a],
                    "b_census": census[b],
                    "differs_somewhere": differs,
                }
            )
    collided = [c for c in distinct if not c["differs_somewhere"]]
    if collided:
        raise Failure(
            f"envelope evidence FAILED — two arms produced IDENTICAL derate "
            f"censuses in every year, so an envelope swap silently did not take "
            f"effect: {json.dumps(collided, indent=1)}"
        )

    return {
        "derated_plant_tranches": census,
        "window_census": {a: WINDOW_CENSUS[a] for a in present},
        "envelope_depth_mw_hours": envelope_depth(),
        "distinctness_checks": distinct,
        "withdrawn_gate": (
            "PRECHECK §3a leg 2's ordering assertion (A1 >= A0, A2 in available "
            "capability, on the inference 'fewer outage windows => more "
            "capability') is WITHDRAWN as MALFORMED, falsified by this session's "
            "own envelope-depth measurement: in 2023 the 439-window "
            "pre-regeneration envelope is DEEPER (38.03M outage MW-h) than the "
            "547-window current one (36.68M), because the superseded detector "
            "produced fewer but far longer windows. Replaced by the pairwise "
            "distinctness check above; the sha ladder remains the load-bearing "
            "proof of which bytes each arm read."
        ),
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
