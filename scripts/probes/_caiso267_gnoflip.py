"""caiso-267 — G-NOFLIP: does any NON-TARGET load-bearing criterion flip PASS -> FAIL?

The fourth pre-registered screen gate of
``ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md`` §E. Scored on the SCREEN
year (2023) for the arm and the control through the SAME scorer the dashboard
uses, so the comparison is like-for-like rather than a re-implementation.

Nothing is registered and nothing is committed to
``frontend/data/backcast/``: the payload is built IN MEMORY via
``render_calibration_html.build_payload`` and handed straight to
``calibration_verdict``'s per-criterion scorers (rule 29(2)/(c) — a screen
bundle is never registered).

C3a (``price_mean``) is the TARGET and is exempt in both directions; C3c
(``price_tail``) is exempt as the keeper's standing ledgered caveat under
rubric v3.6. Both are reported for the reader, never gated.

Usage: python3 scripts/probes/_caiso267_gnoflip.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import calibration_verdict as cv  # noqa: E402
from scripts import render_calibration_html as rch  # noqa: E402

ISO = "CAISO"
YEAR = 2023
OUT = REPO / "results/calibration/_caiso267_gnoflip.json"
ARMS = [
    ("ctrl", REPO / "results/calibration/caiso267_ctrl_screen2023"),
    ("arm", REPO / "results/calibration/caiso267_fossil92_screen2023"),
]
#: Load-bearing + protective criteria the gate watches. C3a is the target and
#: C3c the standing caveat, so neither appears here (addendum §E).
GATED = ("fuelmix", "sysvol", "price_shape", "dispatch_corr")


def _worst(rows) -> str:
    """Collapse a scorer's per-row statuses into one criterion status."""
    if isinstance(rows, dict):
        rows = [rows]
    st = {r.get("status") for r in rows if isinstance(r, dict)}
    for bad in ("FAIL", "CAVEAT", "PASS"):
        if bad in st:
            return bad
    return "n/a"


def main() -> int:
    """Score the gated criteria for both arms and report any PASS -> FAIL flip."""
    D = rch.build_payload(ARMS, years={YEAR})
    ybench = D["bench"][YEAR] if YEAR in D["bench"] else D["bench"][str(YEAR)]
    rec: dict = {"iso": ISO, "year": YEAR, "arms": {}}

    for i, (name, _bundle) in enumerate(ARMS):
        ypay = D["model"][i]["years"][YEAR]
        scored = {
            "fuelmix": cv.score_fuelmix(YEAR, ypay, ybench, iso=ISO),
            "sysvol": cv.score_sysvol(YEAR, ypay, ybench, iso=ISO),
            "price_shape": cv.score_price_shape(YEAR, ypay, ybench),
            "dispatch_corr": cv.score_dispatch_corr(YEAR, ypay, ybench, iso=ISO),
            # reported, NOT gated (addendum §E)
            "price_mean_TARGET": cv.score_price_mean(YEAR, ypay, ybench),
        }
        rec["arms"][name] = {
            k: {"status": _worst(v), "detail": v} for k, v in scored.items()
        }

    flips = []
    for crit in GATED:
        a = rec["arms"]["arm"][crit]["status"]
        c = rec["arms"]["ctrl"][crit]["status"]
        if c == "PASS" and a == "FAIL":
            flips.append(f"{crit}: PASS -> FAIL")
    rec["gates"] = {"G_NOFLIP": {"flips": flips, "pass": not flips}}
    rec["summary"] = {
        crit: f"ctrl {rec['arms']['ctrl'][crit]['status']} -> arm "
        f"{rec['arms']['arm'][crit]['status']}"
        for crit in list(GATED) + ["price_mean_TARGET"]
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps({"summary": rec["summary"], "gates": rec["gates"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
