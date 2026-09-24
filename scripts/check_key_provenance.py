#!/usr/bin/env python3
"""Census every committed ``run_config.json``'s ``cache_key``, and gate the
result against the committed exception record.

**What this answers.** A committed ``cache_key`` is what a bundle actually
solved under. When today's ``ScenarioConfig.cache_key()`` cannot recompute it,
that is a *provenance* fact about the record — a rule, a default or a solve
environment moved underneath it — and the honest repair is to DERIVE it, never
to rewrite the artifact so it agrees with today (capx D85 §5 refuses (iii) and
(iv) for exactly that reason). This script reports the census and enforces that
every non-reproducing record is a KNOWN, derived, cited exception:

    N committed run configs: R reproduce, K have no key, M mismatch
      M known, ZERO unknown

**Both keys, always.** ``cache_key`` appends a ``__solve_surface__`` block for
an ISO whose ``config/solve_surface.py`` rows have moved off their frozen
declaration, so a record can reproduce under one construction and not the
other. Every row is hashed both ways and the summary names which one matched.
A record that reproduces only at declaration is capx **D79**'s DESIGNED re-key
("a re-derived registry table re-keys the ISOs whose rows moved"), reported
here and repaired nowhere — re-declaring a moved row belongs to the ISO lane
that re-solves its frontier on the new table.

**The gates** are :func:`scripts.lib.key_provenance.check_exceptions`'s six;
read that docstring for what each one means. In short: a SIXTEENTH mismatch
fails (G1), and so does a listed entry that has started reproducing (G2) —
a stale exception is its own defect, and this script must never pass quietly
over one — and so does a new UNREGISTERED ``ScenarioConfig`` field (G6).

**WHAT G1–G5 CANNOT SEE, AND WHY G6 EXISTS.** G1–G5 are payload-driven: they
ask whether today's rules can reproduce a recorded literal from the config that
record STORED. A field added after a bundle solved is absent from that bundle's
payload by construction, so it never enters their arithmetic — while
``ScenarioConfig.cache_key`` hashes ``asdict(self)`` and does materialize it.
At ``fc927c2f`` that gap let this script report EXIT 0, *"15 known, ZERO
unknown"*, while 199 of 200 committed records could not be reconstructed to
their own recorded key because ``pjm_seam_neighbour_hourly_ladder`` landed
without a registration entry (capx D91, owner ruling Q64,
``docs/handoffs/FINDING-capx-d91-2026-09-09.md``). **G6 is the leg that would
have been red the day that field landed.** Read the "ok:" line below as the
scope it states and nothing wider.

Usage::

    uv run python scripts/check_key_provenance.py
    uv run python scripts/check_key_provenance.py --out <record.json>
    uv run python scripts/check_key_provenance.py --no-fetch   # offline runner

Exit 0 iff every mismatch is a listed exception whose recipe reproduces its
recorded literal, or a Q66 class-rule ``lag`` (capx D93: one row per
registration in ``docs/governance/key-provenance-lag-registrations.json``,
each such record printed as a REPORTED ``LAG`` line, never silently). ``--no-fetch`` downgrades an unreachable ``vintage`` blob (and a class-rule
ancestry this clone cannot decide) from a failure to a warning (the clone is ``blob:none`` and shallow, so one
recipe needs a depth-1 fetch); every other gate still binds.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.lib.key_provenance import (  # noqa: E402
    EXCEPTIONS_PATH,
    census,
    check_exceptions,
    lag_classifications,
    load_exceptions,
    unregistered_schema_drift,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the full JSON census record here")
    ap.add_argument(
        "--exceptions",
        default=str(EXCEPTIONS_PATH),
        help="the committed exception record (default: %(default)s)",
    )
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help=(
            "never fetch a missing vintage blob; report an unverifiable recipe "
            "as a warning instead of a failure"
        ),
    )
    args = ap.parse_args(argv)

    record = census()
    exceptions = load_exceptions(Path(args.exceptions))
    lag = lag_classifications(record, exceptions, fetch=not args.no_fetch)
    failures = check_exceptions(record, exceptions, fetch=not args.no_fetch, lag=lag)

    listed = {e["run_config"] for e in exceptions["entries"]}
    mismatch = {r["run_config"] for r in record["mismatch_detail"]}
    classed = {p for p, v in lag.items() if v["status"] == "lag"}
    unknown = sorted(mismatch - listed - classed)

    print(
        f"{record['configs_checked']} committed run configs at {record['head']}: "
        f"{record['instrument_validated']} reproduce, "
        f"{record['instrument_unvalidatable_no_recorded_key']} have no key, "
        f"{record['instrument_mismatch']} mismatch"
    )
    print(
        f"  {len(mismatch & listed)} KNOWN (listed exceptions), "
        f"{len(classed)} LAG (Q66 class rule), {len(unknown)} UNKNOWN"
    )
    # Q66: a class-rule `lag` is REPORTED, never silent (capx D93).
    for path in sorted(classed):
        v = lag[path]
        print(
            f"    LAG (Q66 class rule): {path} <- undrop {v['field']}; "
            f"registration {v['registration_sha'][:8]} not in solve "
            f"{v['solve_sha'][:10]}; reproduces {v['undrop_key']}"
        )
    print(
        f"  keys: {record['validated_under_both_constructions']} reproduce under "
        f"BOTH constructions, {record['validated_at_declaration_only']} only with "
        f"the surface AT DECLARATION (D79's designed re-key), "
        f"{record['validated_live_surface_only']} only with the LIVE surface"
    )
    print(f"  surface rows off declaration: {record['surface_moved_rows_by_iso']}")
    print(
        "  at-declaration-only by ISO: "
        f"{record['reproduces_at_declaration_only_by_iso']}"
    )
    for name, count in sorted(record["mismatch_by_class"].items()):
        print(f"    class {name:34s} {count}")
    drift = unregistered_schema_drift(record)
    exposed = sorted({p for v in drift.values() for p in v})
    print(
        f"  G6 unregistered schema drift: {len(drift)} field(s) off the ratchet"
        f"{' — ' + ', '.join(sorted(drift)) if drift else ''}"
        f"{f' (exposed by {len(exposed)} record(s))' if drift else ''}"
    )
    if record["unclassified_unreachable_commit"]:
        print(
            f"  NOTE: {record['unclassified_unreachable_commit']} row(s) could not "
            "run the vintage half of the ladder (blob absent from this clone) — "
            "a property of the checkout, not a finding; their listed recipes still "
            "gate below."
        )

    if args.out:
        # The per-row scenario_config payloads exist only so the recipes can be
        # re-hashed; they are not evidence and would multiply the record's size.
        writable = census_without_payloads(record)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(writable, indent=2) + "\n")

    if record["unclassified"]:
        print(
            f"\nFAIL: {record['unclassified']} mismatch(es) reproduce under NO "
            "recipe — the classification ladder is exhausted. This is a new "
            "finding: stop and report it (capx D85 §5).",
            file=sys.stderr,
        )
        return 1
    if failures:
        print(f"\nFAIL: {len(failures)} gate failure(s)", file=sys.stderr)
        for f in failures:
            print(
                f"  [{f['gate']}] {f['run_config']}\n      {f['detail']}",
                file=sys.stderr,
            )
        if args.no_fetch and all(
            f["gate"] in ("G3_UNVERIFIED", "G1_LAG_UNVERIFIED") for f in failures
        ):
            print(
                "  (--no-fetch: unverifiable recipes only — treated as a warning)",
                file=sys.stderr,
            )
            return 0
        return 1
    print(
        "\nok: every mismatch is a known, cited, recipe-verified exception or a "
        "reported Q66 class-rule lag, and "
        "no unregistered ScenarioConfig field is off the G6 ratchet"
    )
    return 0


def census_without_payloads(record: dict) -> dict:
    """A copy of the census record with the per-row config payloads removed."""
    out = dict(record)
    out["rows"] = [
        {k: v for k, v in r.items() if k != "scenario_config"} for r in record["rows"]
    ]
    out["mismatch_detail"] = [
        {k: v for k, v in r.items() if k != "scenario_config"}
        for r in record["mismatch_detail"]
    ]
    return out


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
