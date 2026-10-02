"""Tabulate the probe_live_sweep.py outputs: after vs main vs pre-#7047, per ISO-year."""

import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
BUNDLES = [
    ("MISO", "miso280_span"),
    ("NWPP", "nwppnext16c_span"),
    ("PJM", "pjmnext16_A_span"),
    ("SOCO", "soco96_span"),
    ("NEISO", "neiso119_span"),
]
rows, summary = [], {}
for iso, b in BUNDLES:
    legs = {
        k: json.loads((d / f"{k}_{b}.json").read_text())
        for k in ("after", "main", "pre")
    }
    for y in sorted(legs["after"]):
        a, m, p = (legs[k][y] for k in ("after", "main", "pre"))
        ident = a["hashes"] == m["hashes"]
        movers = sorted(
            (
                (k, a["by_plant_twh"].get(k, 0.0) - m["by_plant_twh"].get(k, 0.0))
                for k in set(a["by_plant_twh"]) | set(m["by_plant_twh"])
            ),
            key=lambda kv: kv[1],
        )
        movers = [(k, round(v, 3)) for k, v in movers if abs(v) >= 0.0005]
        rec = dict(
            iso=iso,
            year=int(y),
            d_vs_main_twh=round(a["avail_twh"] - m["avail_twh"], 3),
            d_vs_pre7047_twh=round(a["avail_twh"] - p["avail_twh"], 3),
            byte_identical_vs_main=ident,
            changed_arrays=[
                k for k in a["hashes"] if a["hashes"][k] != m["hashes"].get(k)
            ],
            dead_cohorts=a["dead_cohorts"],
            in_year_cohorts=a["in_year_cohorts"],
            movers_vs_main=movers[:6],
            flag_ge_0p1=abs(a["avail_twh"] - m["avail_twh"]) >= 0.1,
        )
        rows.append(rec)
(d / "table.json").write_text(json.dumps(rows, indent=1))
print(
    "| ISO | Year | Δ vs main (TWh) | Δ vs pre-#7047 (TWh) | ≥0.1 | byte-identical | changed arrays | dead cohorts | largest movers vs main |"
)
print("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(
        f"| {r['iso']} | {r['year']} | {r['d_vs_main_twh']:+.3f} | {r['d_vs_pre7047_twh']:+.3f} | "
        f"{'**yes**' if r['flag_ge_0p1'] else ''} | {'yes' if r['byte_identical_vs_main'] else 'no'} | "
        f"{', '.join(r['changed_arrays'])} | {len(r['dead_cohorts'])} | "
        + "; ".join(f"{k} {v:+.3f}" for k, v in r["movers_vs_main"][:3])
        + " |"
    )
