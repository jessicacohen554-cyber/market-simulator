"""nyiso-190 POST-HOC (LABELLED, **NOT A BAR**) — the plant-grain misallocation B2 exposed.

``results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md`` fixed
four bars (V1, B1-B4) before any measurement. B2 came back REFUTED in every
year: 78 % of the 2024 displaced TWh moved the displaced plants TOWARD their
measured actuals, i.e. the control was OVER-running them. This probe
characterises that result at full magnitude — the per-plant model-vs-actual
table on the KEEPER (arm) alone, for all three years.

It is **post-hoc and descriptive**. It adopts nothing, rejects nothing, and
decides no verdict; the nyiso-187 precedent for a labelled post-hoc sensitivity
(``_nyiso187_merit_position_bare_srmc.json``) is the model. Stop S2 of the
pre-registration still binds: this is observed unit conduct and can never
identify a mechanism.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.backcast_artifacts import decode_run_js  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARM_ID = "2026-09-05-nyiso-189-steam-identity"
YEARS = ("2023", "2024", "2025")
HOURS = {"2023": 8760, "2024": 8784, "2025": 8760}


def main() -> int:
    arm = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{ARM_ID}.js").read_text()
    )
    rec = {
        "session": "nyiso-190",
        "status": "POST-HOC, LABELLED — NOT A PRE-REGISTERED BAR",
        "run": ARM_ID,
        "basis": "arm m_ann vs bench c_ann (CAMPD) and e_ann (EIA-923), per plant-class key",
        "by_year": {},
    }
    for year in YEARS:
        ap = arm["years"][year]["plants"]
        bp = json.load(
            gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{year}.json.gz")
        )["bench"]["plants"]
        rows = []
        for key, v in bp.items():
            if v.get("nodata"):
                continue
            m = float(ap[key]["m_ann"])
            c, e, npl = float(v["c_ann"]), float(v["e_ann"]), float(v["npl"]) or 1.0
            rows.append(
                {
                    "key": key,
                    "name": v["name"],
                    "group": v["group"],
                    "zone": v["zone"],
                    "npl_mw": round(npl),
                    "model_twh": round(m, 4),
                    "campd_twh": round(c, 4),
                    "e923_twh": round(e, 4),
                    "model_minus_campd": round(m - c, 4),
                    "model_minus_e923": round(m - e, 4),
                    "cf_model": round(m * 1e6 / (npl * HOURS[year]), 4),
                    "cf_campd": round(c * 1e6 / (npl * HOURS[year]), 4),
                    "ct_only": bool(v.get("ct_only")),
                }
            )
        rows.sort(key=lambda r: -r["model_minus_campd"])
        over = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] > 0)
        under = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] < 0)
        rec["by_year"][year] = {
            "n_plants": len(rows),
            "gross_over_twh": round(over, 3),
            "gross_under_twh": round(under, 3),
            "net_twh": round(over + under, 3),
            "gross_misallocation_twh": round(min(over, -under), 3),
            "rows": rows,
        }
    out = ROOT / "results/calibration/_nyiso190_plant_grain_posthoc.json"
    out.write_text(json.dumps(rec, indent=2))
    for year in YEARS:
        y = rec["by_year"][year]
        print(
            f"{year}: over +{y['gross_over_twh']} / under {y['gross_under_twh']} / "
            f"net {y['net_twh']:+} TWh  (offsetting misallocation "
            f"{y['gross_misallocation_twh']} TWh over {y['n_plants']} plants)"
        )
        for r in y["rows"][:5]:
            print(
                f"    +{r['model_minus_campd']:.3f} {r['name'][:30]:32}"
                f"{r['group']:11}{r['zone']:15} CF {r['cf_model']:.2f} vs {r['cf_campd']:.2f}"
            )
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
