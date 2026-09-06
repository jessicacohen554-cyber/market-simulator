"""miso-226 post-solve — does the neighbour anchor fix the seam's LEVEL, its SLOPE, or both?

miso-225 §4 diagnosed its own G-2 failure in words: *an anchor changes a fixed
ladder's LEVELS and not its RESPONSIVENESS to the model's own price*.  It could
only assert that, because its seam leg ran inside a joint arm whose partner moved
the price.  The seam-alone arm can MEASURE it, and that is what this instrument
does.

Construction: bin the year by the **measured** MISO-Indiana hub price into
deciles, and read three import series in the same bins — the measured PJM seam
flow (EIA-930, the ladder's own source), the keeper's modelled imports, and the
arm's.  Level is the mean; slope is the d1 -> d10 difference.

The comparison that is basis-safe is the SLOPE WITHIN each series: the measured
column is the PJM seam alone (gross inbound) while the model columns are the
model's whole import class (PJM + SPP + South + Manitoba), so their annual LEVELS
are not directly comparable and are reported with their bases named rather than
differenced.  Both annual comparators on record disagree with each other
(40.94 TWh gross PJM here; the 37.9 TWh EIA-930 figure miso-224's stamp cites
against the model's all-seam total) and this session does not adjudicate between
them — it reports both and draws no conclusion that depends on the choice.

Zero-LP (reads two committed bundles).  Rule 22: 2023 only.  Writes
``_miso226_import_duration_shape.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso224_floor_anatomy_phase0 import actual_zone_price  # noqa: E402

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
ARM = REPO / "results/calibration/miso226_seamalone_S"
OUT = REPO / "results/calibration/_miso226_import_duration_shape.json"
YEAR, HOURS, ZONE = 2023, 8760, "MISO-Indiana"


def _imports(bundle: Path) -> np.ndarray:
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == "import")]
    return (
        c.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def _model_price(bundle: Path) -> np.ndarray:
    s = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] == ZONE)].sort_values("hour")
    return s["price"].to_numpy(float)


def main() -> int:
    from scripts.data.derive_miso_seam_ladders import load_joined

    j = load_joined().loc[YEAR]
    meas = j["PJM"].to_numpy(float)[:HOURS]
    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)[:HOURS]
    k, a = _imports(KEEPER), _imports(ARM)
    pk, pa = _model_price(KEEPER), _model_price(ARM)

    ok = np.isfinite(act) & np.isfinite(meas)
    q = np.percentile(act[ok], np.arange(0, 101, 10))
    rows = []
    for d in range(10):
        hi = (act < q[d + 1]) if d < 9 else (act <= q[d + 1])
        m = ok & (act >= q[d]) & hi
        rows.append(
            {
                "decile": d + 1,
                "n": int(m.sum()),
                "actual_hub_mean": round(float(act[m].mean()), 2),
                "measured_pjm_seam_mw": round(float(np.nanmean(meas[m])), 0),
                "keeper_import_mw": round(float(k[m].mean()), 0),
                "arm_import_mw": round(float(a[m].mean()), 0),
                "arm_minus_keeper_mw": round(float((a - k)[m].mean()), 0),
            }
        )

    def slope(key: str) -> float:
        return round(rows[0][key] - rows[9][key], 0)

    rec = {
        "probe": "miso-226 — import duration SHAPE: does the neighbour anchor move the level, the slope, or both?",
        "year": YEAR,
        "keeper": "2026-09-05-miso-220-nonsteam-lift",
        "arm": "miso226_seamalone_S (seam-alone neighbour-anchored PJM ladder)",
        "bins": "deciles of the MEASURED MISO-Indiana hub price",
        "deciles": rows,
        "slope_d1_minus_d10_mw": {
            "measured_pjm_seam": slope("measured_pjm_seam_mw"),
            "keeper": slope("keeper_import_mw"),
            "arm": slope("arm_import_mw"),
            "note": (
                "POSITIVE = imports MORE when MISO is cheap (the measured "
                "behaviour). NEGATIVE = imports more when MISO is expensive "
                "(the model's inversion)."
            ),
        },
        "level_mean_mw": {
            "measured_pjm_seam": round(float(np.nanmean(meas[ok])), 0),
            "keeper": round(float(k[ok].mean()), 0),
            "arm": round(float(a[ok].mean()), 0),
        },
        "annual_twh_BASES_DIFFER_do_not_difference": {
            "measured_pjm_seam_gross_inbound": round(float(np.nansum(meas)) / 1e6, 2),
            "model_all_seam_keeper": round(float(k.sum()) / 1e6, 3),
            "model_all_seam_arm": round(float(a.sum()) / 1e6, 3),
            "note": (
                "the measured column is the PJM seam alone; the model columns are "
                "PJM + SPP + South + Manitoba. miso-224's stamp cites a different "
                "measured comparator (EIA-930 37.9 TWh) against the model's "
                "all-seam total. This session reports both and adjudicates neither."
            ),
        },
        "responsiveness_corr_with_own_model_price": {
            "keeper": round(float(np.corrcoef(k[ok], pk[ok])[0, 1]), 3),
            "arm": round(float(np.corrcoef(a[ok], pa[ok])[0, 1]), 3),
            "measured_vs_actual_hub": round(
                float(np.corrcoef(meas[ok], act[ok])[0, 1]), 3
            ),
        },
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["slope_d1_minus_d10_mw"], indent=1))
    print(json.dumps(rec["responsiveness_corr_with_own_model_price"], indent=1))
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
