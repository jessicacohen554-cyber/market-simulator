"""nyiso-191 (object 2, MEASUREMENT ONLY) — the ``ST_GAS`` error is ZONAL, not class-level.

nyiso-190 §6 handed forward that the keeper's ``ST_GAS`` class total (−0.62 TWh
in 2024) hides large offsetting per-plant errors. This resolves that to its zone
grain on committed artifacts, with NO LP and NO lever proposed
(``PREREG-nyiso191-ccchp-capacity-scope.md`` stop **S7**).

Basis: the keeper's registered per-plant model annual (``m_ann``) against the
bench's CAMPD annual (``c_ann``), per ``ST_GAS`` plant, aggregated by model zone.
Ravenswood's *availability* was adjudicated at nyiso-183; this is energy
PLACEMENT between zones, a different object.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.backcast_artifacts import decode_run_js  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
KEEPER_ID = "2026-09-05-nyiso-189-steam-identity"
YEARS = ("2023", "2024", "2025")
KLASS = "ST_GAS"
REPORT_MIN_TWH = 0.15  # printed-detail threshold only; every plant enters the sums


def main() -> int:
    run = decode_run_js(
        (REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    rec = {
        "session": "nyiso-191",
        "object": "2 (measurement only — no lever proposed, PREREG stop S7)",
        "run": KEEPER_ID,
        "klass": KLASS,
        "basis": "keeper m_ann vs bench c_ann (CAMPD), per plant, summed by model zone",
        "by_year": {},
    }
    for year in YEARS:
        bench = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz")
        )["bench"]["plants"]
        plants = run["years"][year]["plants"]
        rows, by_zone = [], {}
        for key, v in bench.items():
            if v["group"] != KLASS or v.get("nodata"):
                continue
            m, c = float(plants[key]["m_ann"]), float(v["c_ann"])
            rows.append(
                {
                    "key": key,
                    "name": v["name"],
                    "zone": v["zone"],
                    "npl_mw": v["npl"],
                    "model_twh": round(m, 4),
                    "campd_twh": round(c, 4),
                    "e923_twh": round(float(v["e_ann"]), 4),
                    "model_minus_campd": round(m - c, 4),
                }
            )
            by_zone[v["zone"]] = by_zone.get(v["zone"], 0.0) + (m - c)
        rows.sort(key=lambda r: -r["model_minus_campd"])
        over = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] > 0)
        under = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] < 0)
        rec["by_year"][year] = {
            "n_plants": len(rows),
            "class_net_twh": round(over + under, 3),
            "gross_over_twh": round(over, 3),
            "gross_under_twh": round(under, 3),
            "offsetting_misallocation_twh": round(min(over, -under), 3),
            "by_zone_twh": {k: round(v, 3) for k, v in sorted(by_zone.items(), key=lambda x: -abs(x[1]))},
            "rows": rows,
        }
        print(
            f"{year}: class net {over + under:+.2f} | gross over +{over:.2f} / "
            f"under {under:.2f} | offsetting {min(over, -under):.2f} TWh"
        )
        print(f"   by zone: {rec['by_year'][year]['by_zone_twh']}")
        for r in rows:
            if abs(r["model_minus_campd"]) >= REPORT_MIN_TWH:
                print(
                    f"   {r['model_minus_campd']:+7.3f}  {r['name'][:26]:28}"
                    f"{r['zone']:16} model {r['model_twh']:6.3f} vs {r['campd_twh']:6.3f}"
                )
    # The sign pattern is the finding: is it stable across every year?
    zones = set()
    for y in YEARS:
        zones |= set(rec["by_year"][y]["by_zone_twh"])
    rec["zone_sign_stable"] = {
        z: (
            len({(rec["by_year"][y]["by_zone_twh"].get(z, 0.0) > 0) for y in YEARS}) == 1
        )
        for z in sorted(zones)
    }
    out = REPO / "results/calibration/_nyiso191_stgas_placement.json"
    out.write_text(json.dumps(rec, indent=2))
    print(f"\nzone sign stable across all three years: {rec['zone_sign_stable']}")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
