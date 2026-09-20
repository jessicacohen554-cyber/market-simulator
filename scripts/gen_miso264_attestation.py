"""Write the miso-264 bundle's attestation — the gas-offer margin anchor vintage.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL outright
instead of reclassifying to a ledgered CAVEAT under the rule-22 ``[R-C3C]``
standing rule's guard (b)), so this is generated AT the registration and never
typed by hand.

Pattern unchanged from ``gen_miso260_attestation.py`` / ``gen_miso250_
attestation.py``: the last COMMITTED MISO attestation is carried verbatim,
``governance.attested_by`` is re-stamped with THIS bundle's narrative, and
every ``price_tail`` / ``price_mean`` exception magnitude is RE-MEASURED from
this bundle's own scored records rather than copied.

ONE DIFFERENCE FROM miso-260, and it is an improvement: the carried source is
the **incumbent keeper's own committed attestation**
(``results/calibration/miso263_coalcap_span/calibration_attestation.json``),
not a bundle recovered from git. miso-260 had to reach back to miso-255 because
the then-incumbent had never committed one; that gap was closed at the
miso-260 promotion and has stayed closed, so this carries the real predecessor.

RULE 21 ``[R-DOF]``: the ledger is carried VERBATIM with NO new entry. The arm
adds no ``ScenarioConfig`` field (``gas_offer_margin_anchor_vintage`` has been
in the dataclass and in ``_CACHE_KEY_OPTIONAL_FIELDS`` since pjm-169) and no
free parameter — the resolved anchor is the SAME measurement the frozen derive
defines, evaluated on the year being solved instead of on a frozen window, and
the run records the resolved value (rule 24 ``[R-REGISTRY]``). It is
deliberately NOT rebuilt by ``scripts/build_dof_ledger.py``, which silently
drops the hand-declared MISO entries (see ``gen_miso250_attestation.py``).

Usage::

    PYTHONPATH=.:src python scripts/gen_miso264_attestation.py \
        --bundle results/calibration/miso264_anchor_span \
        --run-id 2026-09-20-miso-264-anchor-vintage
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: The incumbent keeper's committed attestation.
CARRIED_REL = "results/calibration/miso263_coalcap_span/calibration_attestation.json"
CARRIED_REFS = ("HEAD", "origin/main", "HEAD~1", "HEAD~2", "HEAD~3")


def _carried_attestation() -> dict:
    """Return the last committed MISO attestation, from disk or from git."""
    src = REPO / CARRIED_REL
    if src.exists():
        return json.loads(src.read_text())
    for ref in CARRIED_REFS:
        got = subprocess.run(
            ["git", "show", f"{ref}:{CARRIED_REL}"],
            capture_output=True,
            text=True,
            cwd=REPO,
            check=False,
        )
        if got.returncode == 0 and got.stdout.strip():
            return json.loads(got.stdout)
    raise SystemExit(
        f"carried attestation not on disk at {src} and not in git at "
        f"{', '.join(CARRIED_REFS)} — refusing to write an attestation without "
        "the DOF ledger it must carry (rule 21 [R-DOF])"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--attested-by-file",
        required=True,
        help="path to the plain-text C6 narrative for governance.attested_by",
    )
    ap.add_argument(
        "--disclosures-file",
        required=True,
        help="path to the plain-text disclosures note",
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    att = _carried_attestation()

    # calibration_verdict exits 1 on NOT-YET, which is exactly the state this
    # bundle is in BEFORE its attestation exists (an unattested C6). The JSON on
    # stdout is complete either way, so the exit status is deliberately unchecked.
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            args.run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=False,
    )
    if not proc.stdout.strip():
        raise SystemExit(
            f"calibration_verdict produced no JSON:\n{proc.stderr[-2000:]}"
        )
    scored = json.loads(proc.stdout)["criteria"]

    # RE-MEASURE every carried exception magnitude on THIS bundle's own scored
    # records; classification and reason are the standing MISO adjudications.
    measured: dict[tuple[str, int], str] = {}
    for crit in ("price_tail", "price_mean"):
        for rec in scored.get(crit, {}).get("records", []):
            if rec.get("key") or rec.get("year") is None:
                continue
            measured[(crit, int(rec["year"]))] = rec["magnitude"]
    n_remeasured = 0
    for exc in att["exceptions"]:
        key = (str(exc.get("criterion")), int(exc.get("year", 0)))
        if key in measured:
            exc["magnitude"] = measured[key]
            exc["magnitude_basis"] = (
                "this run's own scored value (miso-264); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
            n_remeasured += 1

    att["free_parameters"]["carried_from"] = (
        f"{CARRIED_REL} — carried VERBATIM with no new entry: miso-264 adds no "
        "ScenarioConfig field and no free parameter. The arm re-resolves an "
        "EXISTING identification point on the solve year instead of on a frozen "
        "2023-2025 window; the formula is the frozen derive's own and only the "
        "index it is evaluated on moves (rules 21 [R-DOF] / 24 [R-REGISTRY])."
    )
    att["governance"]["attested_by"] = Path(args.attested_by_file).read_text().strip()
    att["disclosures"] = {"note": Path(args.disclosures_file).read_text().strip()}

    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(
        f"  exceptions carried: {len(att['exceptions'])}, re-measured: {n_remeasured}"
    )
    print(
        f"  DOF ledger entries carried: {att['free_parameters']['n_entries']} "
        f"({att['free_parameters']['n_residual']} residual-identified), 0 added"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
