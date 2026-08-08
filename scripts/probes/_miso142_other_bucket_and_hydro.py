"""miso-142 — what is actually IN the model's ``OTHER`` bucket (P7), and the
seasonal leg of the hydro question (P6/O3).

No solve.  Two loose ends the main gates leave open.

**P7 — the classification question comes BEFORE the dispatch question.**
``config.plant_taxonomy.classify_plant`` returns ``"OTHER"`` from two different
branches: line 314, ``fuel == "NG"`` with a prime mover in none of the CC / CT /
ST sets, and line 327, the terminal fallback for any unrecognised fuel or prime
mover.  Those are not the same object and they do not share a comparator: a
gas-fuelled unit that fell through the prime-mover sets is reported by EIA-930
under ``NG: NG``, while a genuinely-other-fuelled unit is reported under
``NG: OTH``.  So the bucket is decomposed by fuel and prime mover FIRST, and only
then given a comparator.  Reported alongside the repo's own authoritative
rollup (``PLANT_CLASSES[*].fuel930``), which puts ``OTHER``, ``biomass`` and
``geothermal`` in the ``other`` bucket.

**P6/O3 — the seasonal leg.**  The hour-of-day leg is measured in
``_miso142_supply_vs_eia930.py``.  A hydro representation can track the diurnal
shape and still be wrong on the *seasonal* one (spring runoff), which is the
other thing "way off" could mean, so the monthly profile is measured too rather
than left as an untested branch of the claim.

Probe hygiene (miso-140b §6): REPO ROOT on ``sys.path``, ``load_zonal_shares``
asserted non-None.

Usage::

    .venv/bin/python scripts/probes/_miso142_other_bucket_and_hydro.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))
sys.path.insert(0, str(REPO / "scripts"))

from _miso137_c3a_gap_decomposition import HOURS, month_of_hour  # noqa: E402

KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso142_other_bucket_and_hydro.json"
YEARS = (2023, 2024, 2025)  # rule 22


def main() -> None:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.plant_taxonomy import (
        NG_CC_PRIME_MOVERS,
        NG_CT_PRIME_MOVERS,
    )
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled
    from market_sim.data.eia930.zonal_shares import load_zonal_shares
    from market_sim.data.fleet import load_fleet_from_csv
    from _miso141_summer_derate_basis import keeper_config

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, "load_zonal_shares None -- repo root off sys.path"

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "P7_other_bucket": {},
        "P6_hydro_monthly": {},
        "taxonomy_note": (
            "classify_plant returns OTHER at plant_taxonomy.py:314 (fuel==NG, "
            "prime mover outside the CC/CT/ST sets) and :327 (terminal fallback). "
            "The repo's own PLANT_CLASSES rollup puts OTHER/biomass/geothermal in "
            "the EIA-930 'other' bucket; a :314 unit is reported by EIA-930 under "
            "NG: NG, so the two branches do NOT share a comparator."
        ),
    }

    for year in YEARS:
        cfg = keeper_config(year)
        gens = load_fleet_from_csv(
            "MISO",
            get_iso_config("MISO"),
            year=year,
            measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
            measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
            cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
            cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
        )
        # WHAT LANDS IN OTHER -- and the answer is that NOTHING in the FLEET
        # does.  ``plant_group`` is populated for the fossil classes only, and
        # the sidecar's ``klass`` falls back to ``_model_class_for_unit`` for the
        # rest; measured on the MISO fleet, the tally is COAL / CC_REGULAR /
        # CT_PEAKER / nuclear / ST_GAS / CC_CHP / oil / CT_CHP / ST_CHP /
        # biomass and NO OTHER at all.  The sidecar's OTHER class is an
        # **injected must-run residual** (``_INJECTED_MUSTRUN_CLASSES =
        # ("biomass", "OTHER")``, ``_must_run_profiles``): its annual energy is
        # its EIA-923 benchmark, shaped FLAT WITHIN EACH MONTH and split by zone
        # demand share, netted out of the LP's demand and re-added to the
        # dispatch frame for reconciliation.  So it is a demand reduction, not a
        # supply-stack participant, and it can never set or respond to price.
        # Measured structurally below (12 distinct hourly values per year is the
        # signature of flat-within-month) rather than asserted.
        from run_calibration_full import (  # noqa: F401
            _INJECTED_MUSTRUN_CLASSES,
            _model_class_for_unit,
        )

        def klass_of(g) -> str:
            pg = str(getattr(g, "plant_group", "") or "")
            return pg if pg else _model_class_for_unit(
                str(g.unit_id), str(g.fuel_type), str(g.efficiency_bin)
            )

        fleet_tally: dict[str, float] = defaultdict(float)
        for g in gens:
            fleet_tally[klass_of(g)] += float(g.pmax_mw)

        df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        if "pass" in df:
            df = df[df["pass"].astype(str).str.upper() == "P1"]
        piv = df.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        piv = piv.reindex(range(HOURS)).fillna(0.0)

        struct = {}
        for k in ("OTHER", "biomass", "hydro"):
            v = piv[k].to_numpy(float)
            struct[k] = {
                "n_distinct_hourly_values": int(len(np.unique(np.round(v, 3)))),
                "min_mw": round(float(v.min()), 1),
                "max_mw": round(float(v.max()), 1),
                "mean_mw": round(float(v.mean()), 1),
                "flat_within_month": bool(len(np.unique(np.round(v, 3))) <= 12),
            }
        out["P7_other_bucket"][str(year)] = {
            "injected_mustrun_classes": list(_INJECTED_MUSTRUN_CLASSES),
            "OTHER_units_in_fleet": int(
                sum(1 for g in gens if klass_of(g) == "OTHER")
            ),
            "fleet_pmax_by_klass_mw": {
                k: round(v, 1)
                for k, v in sorted(fleet_tally.items(), key=lambda kv: -kv[1])
            },
            "hourly_structure": struct,
            "verdict": (
                "OTHER is an INJECTED must-run residual on the EIA-923 basis, "
                "flat within each month, netted out of LP demand -- not a "
                "dispatched class. Comparing it to EIA-930 'NG: OTH' crosses "
                "instruments (EIA-923 vs EIA-930) rather than measuring a "
                "dispatch defect."
            ),
        }

        # ---- P6 seasonal leg ---------------------------------------------
        m_hyd = piv["hydro"].to_numpy(float)
        f = _eia_hourly_frame_filled("MISO", year)
        assert f is not None and len(f) == HOURS
        a_hyd = f.reset_index(drop=True)["NG: WAT"].to_numpy(float)
        mon = month_of_hour(np.arange(HOURS))
        mm = [round(float(np.nanmean(m_hyd[mon == m])), 1) for m in range(1, 13)]
        aa = [round(float(np.nanmean(a_hyd[mon == m])), 1) for m in range(1, 13)]
        ok = np.isfinite(np.asarray(mm)) & np.isfinite(np.asarray(aa))
        out["P6_hydro_monthly"][str(year)] = {
            "model_mw_by_month": mm,
            "actual_mw_by_month": aa,
            "r": round(float(np.corrcoef(np.asarray(mm)[ok], np.asarray(aa)[ok])[0, 1]), 4),
            "model_peak_month": int(np.argmax(mm)) + 1,
            "actual_peak_month": int(np.argmax(aa)) + 1,
            "model_cv": round(float(np.std(mm) / np.mean(mm)), 4),
            "actual_cv": round(float(np.std(aa) / np.mean(aa)), 4),
        }

    OUT.write_text(json.dumps(out, indent=1))

    print("=" * 78)
    print("miso-142 -- P7 (what is in OTHER) and P6 seasonal (hydro by month)")
    print("=" * 78)
    for year in YEARS:
        b = out["P7_other_bucket"][str(year)]
        print(
            f"\n{year} OTHER: units in FLEET = {b['OTHER_units_in_fleet']}  "
            f"| injected must-run classes = {b['injected_mustrun_classes']}"
        )
        for k, v in b["hourly_structure"].items():
            print(
                f"     {k:8s} distinct hourly values {v['n_distinct_hourly_values']:5d}"
                f"  mean {v['mean_mw']:8.1f} MW  flat-within-month={v['flat_within_month']}"
            )
        h = out["P6_hydro_monthly"][str(year)]
        print(
            f"   hydro monthly: r {h['r']:+.3f}  peak month model {h['model_peak_month']}"
            f" vs actual {h['actual_peak_month']}  CV {h['model_cv']:.3f} / {h['actual_cv']:.3f}"
        )
        print(f"     model  {h['model_mw_by_month']}")
        print(f"     actual {h['actual_mw_by_month']}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
