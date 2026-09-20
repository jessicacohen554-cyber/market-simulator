"""Phase-0: can PJM's conventional-hydro floor be established without a clean series?

PJM has NO published hourly conventional-hydro series: Data Miner's
``gen_by_fuel`` ``Hydro`` category folds pumped storage (15.5 TWh against
8.9 TWh of EIA-923 ``HY``; 6.4 GW max against 3.3 GW of conventional
nameplate — Data Miner ``Storage`` is batteries, 20 MW max), and PJM is in
``EIA930_PS_FOLDED_INTO_WAT`` for the same reason. So the nyiso-111
falsification test — does the measured fleet swing more than the classifier's
shapeable set allows? — cannot be run for PJM the way it was run for NYISO.

This probe establishes what CAN be said from PJM's own data, and says exactly
where the evidence stops:

1. **The overnight window is PS-quiet.** A pumped-storage plant PUMPS in the
   overnight trough, so its GENERATION there is ~0 and the folded series'
   overnight percentiles are a conservative reading of the CONVENTIONAL fleet
   alone (folding can only ADD generation, never subtract it, so every number
   below is an UPPER bound on conventional output and the floor claim it
   supports is therefore a LOWER bound — the safe direction).
2. Against that, the model's own overnight distribution.
3. The EHA mode partition of PJM's fleet, with the conservative (unambiguous
   RoR + Canal/Conduit only) flat set separated from the CAISO rule's wider one.

Run: ``uv run --no-sync python3 scripts/probes/_hydro_phase0_pjm_ps_separation.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from _hydro_phase0_pjm_nyiso import actual_pjm, model_hydro  # noqa: E402

BUNDLE = "results/calibration/pjm_h13_meritalloc_span"
OVERNIGHT = (2, 3, 4, 5)  # HE 03-06 EST: deepest PJM load trough, PS pumping


def ps_nameplate(iso: str) -> tuple[float, int]:
    """Return the ISO's EIA-860 pumped-storage (``PS``) nameplate MW and count."""
    from market_sim.config.paths import RAW_DATA_DIR
    from market_sim.data.fleet import ba_codes

    df = pd.read_parquet(RAW_DATA_DIR / "eia-860" / "eia860_generators.parquet")
    sub = df[
        (df["prime_mover"] == "PS")
        & (df["balancing_authority_code"].isin(ba_codes(iso)))
    ]
    return float(sub["nameplate_capacity_mw"].sum()), int(sub["plant_id"].nunique())


def eha_partition() -> dict:
    """Return PJM's EHA ``Mode`` partition, with two candidate flat sets."""
    import sys as _s

    _s.path.insert(0, str(ROOT))
    from market_sim.data.hydro import _load_hydro_generation, _load_hydro_nameplate
    from market_sim.data.eia923 import monthly_netgen_columns

    nm = _load_hydro_nameplate("PJM")
    g = _load_hydro_generation("PJM", 2024)
    energy = dict(
        zip(
            g["plant_id"].astype(int),
            g[monthly_netgen_columns()].to_numpy(float).sum(axis=1),
        )
    )
    eha = pd.read_excel(
        ROOT / "data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx",
        sheet_name="Operational",
    )
    mode = eha[eha["EIA_PtID"].isin(list(nm))].groupby("EIA_PtID")["Mode"].first()

    def agg(labels: set[str]) -> dict:
        ids = [int(i) for i, m in mode.items() if str(m) in labels]
        return {
            "n": len(ids),
            "mw": round(sum(nm.get(i, 0.0) for i in ids), 1),
            "twh_2024": round(sum(energy.get(i, 0.0) for i in ids) / 1e6, 3),
        }

    conservative = {"Run-of-river", "Canal/Conduit"}
    caiso_rule = conservative | {"Reregulating", "Run-of-river/Peaking"}
    return {
        "fleet_mw": round(sum(nm.values()), 1),
        "fleet_twh_2024": round(sum(energy.values()) / 1e6, 3),
        "flat_set_conservative_unambiguous_ror": agg(conservative),
        "flat_set_caiso_committed_rule": agg(caiso_rule),
        "shapeable_peaking": agg({"Peaking", "Intermediate Peaking"}),
        "mode_nan_pending_hilarri_completion": agg({"nan", "NaN", "Unknown"}),
    }


def main() -> None:
    out: dict = {"eha_partition_pjm": eha_partition()}
    mw, n = ps_nameplate("PJM")
    out["pjm_pumped_storage_eia860"] = {"nameplate_mw": round(mw, 1), "plants": n}
    out["years"] = {}
    hod = np.arange(8760) % 24
    night = np.isin(hod, OVERNIGHT)
    for y in (2023, 2024, 2025):
        a = actual_pjm(y)
        m = model_hydro(BUNDLE, y)
        an = a[night]
        an = an[np.isfinite(an)]
        mn = m[night]
        out["years"][y] = {
            "actual_overnight_p05_mw": round(float(np.percentile(an, 5)), 1),
            "actual_overnight_p25_mw": round(float(np.percentile(an, 25)), 1),
            "actual_overnight_p50_mw": round(float(np.percentile(an, 50)), 1),
            "actual_overnight_min_mw": round(float(an.min()), 1),
            "actual_overnight_hours_below_200mw": int((an < 200).sum()),
            "model_overnight_p05_mw": round(float(np.percentile(mn, 5)), 1),
            "model_overnight_p25_mw": round(float(np.percentile(mn, 25)), 1),
            "model_overnight_p50_mw": round(float(np.percentile(mn, 50)), 1),
            "model_overnight_hours_at_zero": int((mn < 1.0).sum()),
            "model_overnight_hours_total": int(night.sum()),
        }
    out["reading"] = (
        "The overnight folded series is an UPPER bound on PJM's conventional "
        "output (PS generation is >=0, never negative in gen_by_fuel), so its "
        "LOW percentiles are the admissible evidence: whatever the real "
        "conventional fleet does overnight, it is at most this. The model "
        "sitting at 0 MW in these hours is falsified only if the folded "
        "series' own floor is well above zero AND the PS fleet is plausibly "
        "idle there — both stated above, neither assumed."
    )
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
