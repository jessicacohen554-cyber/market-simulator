"""Emit the NWPP-NEXT-27 calibration attestation for the Path 76 served-schedule span bundle.

NWPP-NEXT-27 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext27-path76-served-2019-2025-2026-10-03.md``) is keeper
``2026-10-03-nwpp-next-26-nevp``'s recipe (:mod:`gen_nwppnext26_attestation`) with WECC Path 76
moved from a priced link (``nwpp_path76_alturas_link``, NEXT-6) to its measured bilateral leg
(``nwpp_path76_served_schedule``): the NEVP<->BPAT pair clears no WEIM transfer, so the leg is
served at SNV and NW instead of priced (rule 19, one mechanism replacing one). **ZERO NEW FREE
PARAMETERS** (rules 21 / 24): the leg is NEVP's own EIA-930 per-DIBA row.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext26_attestation as n26  # noqa: E402
import scripts.gen_nwppnext6_attestation as n6  # noqa: E402

PIN = "440ad14416cbfd3399e4877a17e7c974c4862fb9"
FIELD = "nwpp_path76_served_schedule"
REPLACED = "nwpp_path76_alturas_link"

_SOURCE = (
    "WECC Path 76 (Alturas, NW<->SNV) served at NEVP's measured EIA-930 per-DIBA BPAT leg "
    "(data/raw/eia-930-interchange/NEVP interchange hourly.parquet), +SNV / -NW, instead of the "
    "priced 300 MW link: the NEVP<->BPAT pair clears zero WEIM transfers in every month "
    "2023-07..2025-12 (WEIM benefits reports Appendix 2, data/raw/nwpp-weim/"
    "weim_benefits_appendix2_transfers.csv) and BPAT entered the WEIM only 2022-05. Rule 19: "
    "replaces nwpp_path76_alturas_link (priced or served, never both; arming both raises)."
)


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-27 attestation built on NEXT-26's generator."""
    base = n26.n25.base
    # NEXT-6's priced link is replaced, not stacked (rule 19). The NEXT-6
    # generator arms its FIELD inside build(), so point it at the key that
    # replaces it; the chain then asserts the NEXT-27 key reads True.
    n6.FIELD = FIELD
    if REPLACED in base._ARMED:
        base._ARMED = tuple(k for k in base._ARMED if k != REPLACED)
    base._SOURCES.pop(REPLACED, None)
    if FIELD not in base._ARMED:
        base._ARMED = (*base._ARMED, FIELD)
    base._SOURCES[FIELD] = _SOURCE
    att = n26.build(bundle, pin)
    run_config = json.loads((bundle / "run_config.json").read_text())
    sc = run_config.get("scenario_config", run_config)
    if sc.get(FIELD) is not True or sc.get(REPLACED) is not False:
        raise SystemExit(
            f"run_config {FIELD}={sc.get(FIELD)!r} / {REPLACED}={sc.get(REPLACED)!r} "
            "-- not the NEXT-27 arm (expected True / False)"
        )
    att.get("switches", {}).pop(REPLACED, None)
    if FIELD in att.get("switches", {}):
        att["switches"][FIELD]["source"] = _SOURCE
    att["lane"] = "NWPP-NEXT-27"
    att["governance"]["notes"] = (
        "Keeper 2026-10-03-nwpp-next-26-nevp recipe with WECC Path 76 served at its measured "
        "NEVP<->BPAT leg instead of priced (owner card 2026-10-03 'Path 76 served'). Offer-curve "
        "multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main c5bce342 "
        "(keeper NEXT-26) + the NEXT-27 key and tests, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config keys moved against keeper 2026-10-03-nwpp-next-26-nevp: "
        "nwpp_path76_served_schedule -> True and nwpp_path76_alturas_link -> False (one "
        "mechanism replacing one). Every year moves. Same libraries; other drift INERT "
        "(PRECOMMIT G-DRIFT)."
    )
    disc.pop("path76_overflow", None)
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pin", default=PIN, help="full 40-char solve pin")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle, args.pin)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
