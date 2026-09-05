"""nyiso-192 — the nyiso-190 plant-grain table on the RE-RENDERED keeper payload.

After the payload repair (``render_calibration_html`` adds back the run's own
measured BTM hold-out), a cogen's ``m_ann`` is LP grid dispatch + measured host
supply, i.e. the full plant — so ``m_ann − c_ann`` (CAMPD full-plant gross) is
the over-run without any arithmetic correction. This is the nyiso-190
post-hoc (``nyiso190_plant_grain_posthoc.py``) re-run on the repaired
instrument for any registered run; it also closes the PREREG §3 V2 identity
by accounting for the CHP plants the bench carries no CAMPD row for.

Usage:
    python scripts/probes/nyiso192_plant_grain_rerendered.py [RUN_ID] [--label NAME]
"""

from __future__ import annotations

import argparse

import pandas as pd

from _nyiso192_common import (
    CHP_GROUPS,
    KEEPER_BUNDLE,
    KEEPER_ID,
    REPO,
    YEARS,
    bench_plants,
    keeper_payload,
    write_json,
)
from market_sim.data.chp import chp_btm_pct, measured_chp_btm_pct_nyiso

HOURS = {2023: 8760, 2024: 8784, 2025: 8760}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_id", nargs="?", default=KEEPER_ID)
    ap.add_argument("--bundle", default=str(KEEPER_BUNDLE.relative_to(REPO)))
    ap.add_argument("--label", default=None)
    args = ap.parse_args()
    run = keeper_payload(args.run_id)
    bundle = REPO / args.bundle
    measured = {c: p / 100.0 for c, p in measured_chp_btm_pct_nyiso().items()}
    rec = {
        "session": "nyiso-192",
        "run": args.run_id,
        "basis": "re-rendered payload m_ann (LP + the run's measured BTM add-back) vs bench c_ann (CAMPD full plant)",
        "by_year": {},
    }
    for year in YEARS:
        bench = bench_plants(year)
        plants = run["years"][str(year)]["plants"]
        rows = []
        for key, b in bench.items():
            if b.get("nodata") or key not in plants:
                continue
            m, c, e, npl = (
                float(plants[key]["m_ann"]),
                float(b["c_ann"]),
                float(b["e_ann"]),
                float(b["npl"]) or 1.0,
            )
            rows.append(
                {
                    "key": key,
                    "name": b["name"],
                    "group": b["group"],
                    "zone": b["zone"],
                    "npl_mw": round(npl),
                    "model_twh": round(m, 4),
                    "campd_twh": round(c, 4),
                    "e923_twh": round(e, 4),
                    "model_minus_campd": round(m - c, 4),
                    "cf_model": round(m * 1e6 / (npl * HOURS[year]), 4),
                    "cf_campd": round(c * 1e6 / (npl * HOURS[year]), 4),
                    "ct_only": bool(b.get("ct_only")),
                }
            )
        rows.sort(key=lambda r: -r["model_minus_campd"])
        over = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] > 0)
        under = sum(r["model_minus_campd"] for r in rows if r["model_minus_campd"] < 0)
        # V2 closure: CHP class identity with the unbenched plants accounted for
        disp = (
            pd.read_parquet(
                bundle / "dispatch" / f"{year}_P1.parquet",
                columns=["plant_code", "klass", "mw"],
            )
            if (bundle / "dispatch" / f"{year}_P1.parquet").exists()
            else None
        )
        ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        identity = {}
        for grp in CHP_GROUPS:
            benched = {
                int(k.split(":")[0])
                for k, b in bench.items()
                if b["group"] == grp and not b.get("nodata")
            }
            s = sum(
                float(plants[k]["m_ann"])
                for k, b in bench.items()
                if b["group"] == grp and not b.get("nodata") and k in plants
            )
            add = sum(
                float(b["e_ann"])
                * measured.get(
                    int(k.split(":")[0]),
                    chp_btm_pct(int(k.split(":")[0]), grp, iso="NYISO") / 100.0,
                )
                for k, b in bench.items()
                if b["group"] == grp and not b.get("nodata") and k in plants
            )
            lp_cls = float(ch[ch.klass == grp].mw.sum()) / 1e6
            unbenched = None
            if disp is not None:
                d = disp[(disp.klass == grp) & (~disp.plant_code.isin(benched))]
                unbenched = float(d.mw.sum()) / 1e6
            identity[grp] = {
                "payload_sum_twh": round(s, 4),
                "measured_addback_twh": round(add, 4),
                "class_hourly_twh": round(lp_cls, 4),
                "unbenched_lp_twh": (
                    round(unbenched, 4) if unbenched is not None else None
                ),
                "residual_twh": (
                    round(s - add - (lp_cls - unbenched), 4)
                    if unbenched is not None
                    else round(s - add - lp_cls, 4)
                ),
            }
        rec["by_year"][str(year)] = {
            "n_plants": len(rows),
            "gross_over_twh": round(over, 3),
            "gross_under_twh": round(under, 3),
            "net_twh": round(over + under, 3),
            "offsetting_misallocation_twh": round(min(over, -under), 3),
            "chp_identity": identity,
            "rows": rows,
        }
        print(
            f"{year}: over +{over:.2f} / under {under:.2f} / net {over + under:+.2f} TWh (offsetting {min(over, -under):.2f} over {len(rows)} plants)"
        )
        for r in rows[:5]:
            print(
                f"    {r['model_minus_campd']:+.3f} {r['name'][:30]:32}{r['group']:11}{r['zone']:15} CF {r['cf_model']:.2f} vs {r['cf_campd']:.2f}"
            )
        for r in rows[-3:]:
            print(
                f"    {r['model_minus_campd']:+.3f} {r['name'][:30]:32}{r['group']:11}{r['zone']:15} CF {r['cf_model']:.2f} vs {r['cf_campd']:.2f}"
            )
        print(
            "   identity:",
            {
                g: (v["residual_twh"], v["unbenched_lp_twh"])
                for g, v in identity.items()
            },
        )
    label = args.label or ("keeper" if args.run_id == KEEPER_ID else args.run_id)
    write_json(f"_nyiso192_plant_grain_rerendered_{label}.json", rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
