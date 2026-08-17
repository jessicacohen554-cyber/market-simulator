"""neiso-98 — which persisted pass is the registered NEISO payload rendered from?

Read-only, committed-artifact-only. **No LP, no solve, nothing registered.**

Why: the keeper shard's ``frontier.reverified`` (written by neiso-84) states the
NEISO bundle is SCORED ON ``P2`` and quotes annual maxima 249.50 / 256.93 /
280.85; neiso-95's ``carried_forward_through`` quotes 248.97 / 218.24 / 280.85,
which are the ``P1`` maxima. Both are arithmetically right — they read different
passes — but the shard now carries both without saying so, and the 2024 figure
differs by 18 %.

The declaration itself is basis-INDEPENDENT (the C3c model tail is 0 h on both
passes in all three years, measured by ``neiso98_declaration_recheck.py``), so
nothing about the frontier turns on this. It is a documentation inconsistency,
and this probe decides it on the CURRENT keeper's own bytes by the same two
independent routes neiso-84 used:

  * per-year mean LMP at a single zone, payload vs each pass, and
  * per-year per-class generation TWh, payload vs each pass.

Whichever pass matches to the payload's stored precision is the rendered — hence
scored — pass.

Usage::

    uv run python scripts/probes/neiso98_scored_pass_identity.py
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_ID = "2026-08-17-neiso-97-dstrepair"
BUNDLE = REPO / "results/calibration/neiso97_dstrepair_A"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/_neiso98_scored_pass_identity.json"


def payload() -> dict:
    src = (REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', src)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))).decode())


def main() -> None:
    pay = payload()
    result = {
        "probe": "neiso98_scored_pass_identity",
        "keeper": KEEPER_ID,
        "solve_performed": False,
        "years": {},
    }

    for year in YEARS:
        sysy = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
        cls = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
        pdata = (pay.get("years") or {}).get(str(year)) or {}

        rec: dict = {"passes_present": sorted(map(str, sysy["pass"].unique()))}

        # --- route 1: max-across-zones annual maximum, per pass ------------
        rec["annual_max_by_pass"] = {}
        for pl in rec["passes_present"]:
            wide = sysy[sysy["pass"] == pl].pivot_table(
                index="hour", columns="zone", values="price"
            )
            rec["annual_max_by_pass"][pl] = round(float(wide.max(axis=1).max()), 4)

        # --- route 2: per-class annual TWh, per pass, vs payload gmModel ---
        # class_hourly carries (year, pass, klass, hour, mw); the payload's
        # gmModel is per-class annual TWh rounded to 2 dp.
        pay_gen = pdata.get("gmModel") or {}
        rec["class_twh_by_pass"] = {}
        for pl in rec["passes_present"]:
            g = cls[cls["pass"] == pl].groupby("klass", observed=True)["mw"].sum() / 1e6
            rec["class_twh_by_pass"][pl] = {str(k): round(float(v), 6) for k, v in g.items()}
        rec["class_match_abs_error"] = {}
        for pl, table in rec["class_twh_by_pass"].items():
            err, n = 0.0, 0
            for k, pv in pay_gen.items():
                if not isinstance(pv, (int, float)) or k not in table:
                    continue
                err += abs(float(pv) - table[k])
                n += 1
            rec["class_match_abs_error"][pl] = {
                "abs_error_twh": round(err, 6),
                "classes_compared": n,
            }

        # --- route 3: HQ_import mean LMP, per pass, vs payload -------------
        # NEISO's five model zones clear at one lambda in this keeper (no
        # binding internal constraint), so the payload's load-zone `p` carries
        # the ACTUAL hub mean; HQ_import has no actual counterpart and shows the
        # MODEL mean, which is what discriminates the passes. This is the same
        # test neiso-84 used.
        rec["mean_lmp_by_pass"] = {
            pl: round(float(sysy[sysy["pass"] == pl]["price"].mean()), 4)
            for pl in rec["passes_present"]
        }
        hq = (pdata.get("lmp") or {}).get("HQ_import") or {}
        rec["payload_hq_import_p"] = hq.get("p")
        if isinstance(rec["payload_hq_import_p"], (int, float)):
            rec["hq_import_abs_error"] = {
                pl: round(abs(float(rec["payload_hq_import_p"]) - v), 4)
                for pl, v in rec["mean_lmp_by_pass"].items()
            }

        # --- which pass does the payload agree with? ----------------------
        rec["rendered_pass_by_class_twh"] = min(
            rec["class_match_abs_error"],
            key=lambda p: rec["class_match_abs_error"][p]["abs_error_twh"],
        )
        if rec.get("hq_import_abs_error"):
            rec["rendered_pass_by_hq_import"] = min(
                rec["hq_import_abs_error"], key=rec["hq_import_abs_error"].get
            )

        result["years"][year] = rec

    routes = {
        r: sorted({rec.get(r) for rec in result["years"].values() if rec.get(r)})
        for r in ("rendered_pass_by_class_twh", "rendered_pass_by_hq_import")
    }
    result["verdict"] = {
        "routes_agree": len({tuple(v) for v in routes.values()}) == 1,
        "routes": routes,
        "rendered_scored_pass": (
            routes["rendered_pass_by_hq_import"][0]
            if len(routes["rendered_pass_by_hq_import"]) == 1
            else None
        ),
        "c3c_tail_is_basis_independent": (
            "measured separately by neiso98_declaration_recheck.py: model tail = 0 h "
            "on BOTH passes in all three years, so the frontier declaration does not "
            "turn on which pass is scored"
        ),
    }

    OUT.write_text(json.dumps(result, indent=2) + "\n")

    print(f"=== scored-pass identity — {KEEPER_ID} ===")
    for year, rec in result["years"].items():
        print(f"\n  {year}: passes {rec['passes_present']}")
        print(f"    annual max (max across zones): {rec['annual_max_by_pass']}")
        print(f"    mean LMP:                      {rec['mean_lmp_by_pass']}")
        print(
            f"    payload HQ_import p {rec.get('payload_hq_import_p')}"
            f"  abs err {rec.get('hq_import_abs_error')}"
            f"  -> {rec.get('rendered_pass_by_hq_import')}"
        )
        print(
            f"    payload gmModel class-TWh abs err {rec['class_match_abs_error']}"
            f"  -> {rec['rendered_pass_by_class_twh']}"
        )
    print("\n=== verdict ===")
    for k, v in result["verdict"].items():
        print(f"  {k}: {v}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
