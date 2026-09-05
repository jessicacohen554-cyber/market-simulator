"""nyiso-192 PHASE 0 (NO LP) — the dashboard payload's CHP add-back is the SECTOR share, not the LP's hold-out.

``scripts/render_calibration_html.py`` adds a cogen's behind-the-meter host
supply back onto its model series so the plant heatmap compares the full plant
to the full CAMPD plant. The bench side passes the nyiso-147 MEASURED per-plant
shares (``measured=_btm_measured``); the model-payload site did not, so every
NYISO cogen's ``m`` / ``m_ann`` carried ``e_ann x 35 %`` (the "merchant" sector
default) on top of an LP that — under ``nyiso_chp_btm_measured`` — held out the
MEASURED share (0 % at Sithe Independence 54547). This probe MEASURES that on
the committed keeper payload, before any repair:

* class identity: sum over CHP plants of the payload ``m`` minus the flat
  sector add-back must equal the committed ``class_hourly`` CHP totals;
* per plant: the payload's hourly minimum equals the flat add-back wherever the
  LP ever reaches zero, and ``m_ann - 0.35 x e_ann`` is the LP annual;
* the nyiso-190 plant-grain table recomputed with the add-back removed
  (LP + MEASURED BTM vs full-plant CAMPD), labelled the arithmetic correction —
  the re-rendered payload after the code repair is the instrument of record.

Every number is read from committed bytes. Nothing is adopted or rejected here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from _nyiso192_common import (
    CHP_GROUPS,
    KEEPER_BUNDLE,
    KEEPER_ID,
    T,
    YEARS,
    bench_plants,
    dec_u8,
    keeper_payload,
    write_json,
)
from market_sim.data.chp import chp_btm_pct, measured_chp_btm_pct_nyiso


def main() -> int:
    run = keeper_payload()
    measured = {c: p / 100.0 for c, p in measured_chp_btm_pct_nyiso().items()}
    rec = {
        "session": "nyiso-192",
        "object": "dashboard payload CHP add-back audit (instrument defect, measured before repair)",
        "run": KEEPER_ID,
        "defect": (
            "render_calibration_html model-payload add-back used chp_btm_pct(sector) "
            "instead of the measured per-plant share the LP held out"
        ),
        "by_year": {},
    }
    for year in YEARS:
        bench = bench_plants(year)
        plants = run["years"][str(year)]["plants"]
        ch = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        yrec = {"classes": {}, "plants": [], "plant_grain": {}}
        for grp in CHP_GROUPS:
            lp_cls = ch[ch.klass == grp].sort_values("hour")["mw"].to_numpy()[:T]
            tot = np.zeros(T)
            tot_corr = np.zeros(T)
            for key, v in plants.items():
                b = bench.get(key)
                if not b or b["group"] != grp:
                    continue
                m = dec_u8(v["m"]) * float(b["npl"]) / 100.0
                code = int(key.split(":")[0])
                sector = chp_btm_pct(code, grp, iso="NYISO") / 100.0
                add = float(b["e_ann"]) * 1e6 * sector / T
                tot += m
                tot_corr += np.clip(m - add, 0.0, None)
            yrec["classes"][grp] = {
                "payload_sum_twh": round(tot.sum() / 1e6, 4),
                "payload_minus_sector_addback_twh": round(tot_corr.sum() / 1e6, 4),
                "class_hourly_lp_twh": round(lp_cls.sum() / 1e6, 4),
                "identity_gap_twh": round((tot_corr.sum() - lp_cls.sum()) / 1e6, 4),
                "flat_offset_mw_mean": round(float((tot - lp_cls).mean()), 1),
                "flat_offset_mw_min": round(float((tot - lp_cls).min()), 1),
                "flat_offset_mw_max": round(float((tot - lp_cls).max()), 1),
            }
        # per-plant: published vs corrected, every benched plant
        rows = []
        for key, b in bench.items():
            if b.get("nodata") or key not in plants:
                continue
            code = int(key.split(":")[0])
            m_ann = float(plants[key]["m_ann"])
            c_ann = float(b["c_ann"])
            e_ann = float(b["e_ann"])
            btm_meas = float(b.get("btm") or 0.0)
            if b["group"] in CHP_GROUPS:
                sector = chp_btm_pct(code, b["group"], iso="NYISO") / 100.0
                lp = m_ann - e_ann * sector
                m_min = float(dec_u8(plants[key]["m"]).min() * float(b["npl"]) / 100.0)
                corr = (lp + btm_meas) - c_ann
            else:
                sector, lp, m_min, corr = 0.0, m_ann, None, m_ann - c_ann
            rows.append(
                {
                    "key": key,
                    "name": b["name"],
                    "group": b["group"],
                    "zone": b["zone"],
                    "published_m_ann": round(m_ann, 4),
                    "sector_share_applied": sector,
                    "measured_share": measured.get(code),
                    "lp_annual_twh": round(lp, 4),
                    "payload_hourly_min_mw": (
                        round(m_min, 1) if m_min is not None else None
                    ),
                    "flat_addback_mw": (
                        round(e_ann * 1e6 * sector / T, 1) if sector else 0.0
                    ),
                    "campd_full_plant_twh": round(c_ann, 4),
                    "bench_btm_measured_twh": round(btm_meas, 4),
                    "published_over_twh": round(m_ann - c_ann, 4),
                    "corrected_over_twh": round(corr, 4),
                }
            )
        df = pd.DataFrame(rows)
        for col, lab in (
            ("published_over_twh", "published"),
            ("corrected_over_twh", "corrected"),
        ):
            o = float(df[df[col] > 0][col].sum())
            u = float(df[df[col] < 0][col].sum())
            yrec["plant_grain"][lab] = {
                "gross_over_twh": round(o, 3),
                "gross_under_twh": round(u, 3),
                "net_twh": round(o + u, 3),
                "offsetting_misallocation_twh": round(min(o, -u), 3),
            }
        df = df.sort_values("corrected_over_twh", ascending=False)
        yrec["plants"] = df.to_dict(orient="records")
        rec["by_year"][str(year)] = yrec
        print(year)
        for grp, v in yrec["classes"].items():
            print(
                f"  {grp:7} payload {v['payload_sum_twh']:7.3f} | minus sector add-back "
                f"{v['payload_minus_sector_addback_twh']:7.3f} | LP class_hourly "
                f"{v['class_hourly_lp_twh']:7.3f} | gap {v['identity_gap_twh']:+.4f} TWh "
                f"| flat offset {v['flat_offset_mw_min']}-{v['flat_offset_mw_max']} MW"
            )
        for lab, v in yrec["plant_grain"].items():
            print(
                f"  plant grain {lab:9}: over {v['gross_over_twh']:+.2f} under {v['gross_under_twh']:+.2f} offsetting {v['offsetting_misallocation_twh']:.2f}"
            )
        for r in yrec["plants"][:4]:
            print(
                f"    {r['name'][:26]:28}{r['group']:11} published {r['published_over_twh']:+.3f} -> corrected {r['corrected_over_twh']:+.3f}"
            )
    write_json("_nyiso192_payload_addback_audit.json", rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
