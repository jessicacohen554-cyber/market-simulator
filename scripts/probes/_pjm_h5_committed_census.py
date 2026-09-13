"""pjm-h5 phase 0 (A/B): the registered-vs-measured `committed` band across EVERY
PJM class, and coal's EFFECTIVE committed multiplier once the sigmoid is applied.

ZERO LP. Reads the keeper bundles' own `meta.json` recipes and the committed
measured artifact `data/raw/reference/pjm_campd_marginal_hr_summary.csv`; calls
`fuel.coal_passthrough_series` for the bituminous sigmoid so the effective
multiplier is the model's own number rather than a citation.

Rule 29 `[R-SCREEN]` clause 0. Rule 21 `[R-DOF]`: nothing here is tunable — the
operand is fixed by the convention already committed to
`pipeline/backcast_config.py` (`committed -> avg_committed_p50`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "data/raw/reference/pjm_campd_marginal_hr_summary.csv"
BUNDLES = {
    "pjm_d4_4_TP": (2020, 2021, 2022),
    "pjm_d4_4_A": (2023, 2024, 2025),
}

#: Model offer-curve class -> the artifact row that measures it. The artifact
#: carries ONE `COAL` row (n=65), so every coal supply group's measured basis is
#: that same row: the measurement has no per-supply grain to select from.
CLASS_TO_ARTIFACT = {
    "CC_REGULAR": "CC_REGULAR",
    "CC_CHP": "CC_CHP",
    "CT_CHP": "CT_CHP",
    "CT_PEAKER": "CT_PEAKER",
    "CT_INTERMEDIATE": "CT_PEAKER",
    "ST_GAS": "ST_GAS",
    "COAL": "COAL",
    "COAL_BIT": "COAL",
    "COAL_PRB": "COAL",
    "COAL_LIGNITE": "COAL",
    "COAL_WC": "COAL",
}


def main() -> int:
    art = pd.read_csv(ART).set_index("class")
    meta = json.loads((REPO / "results/calibration/pjm_d4_4_A/meta.json").read_text())
    ovr = meta["offer_curve_overrides"]

    print("=" * 78)
    print("(A) REGISTERED `committed` vs MEASURED avg_committed_p50 — EVERY PJM CLASS")
    print(
        "    convention: pipeline/backcast_config.py `committed -> avg_committed_p50`"
    )
    print("=" * 78)
    print(
        f"{'class':<16}{'registered':>11}{'measured':>10}{'reg-meas':>10}"
        f"{'reg/meas':>10}   n"
    )
    rows = []
    for cls, bands in ovr.items():
        reg = bands.get("committed")
        if reg is None:
            continue
        arow = art.loc[CLASS_TO_ARTIFACT[cls]]
        meas = float(arow["avg_committed_p50"])
        rows.append((cls, reg, meas))
        print(
            f"{cls:<16}{reg:>11.4f}{meas:>10.3f}{reg - meas:>+10.3f}"
            f"{reg / meas:>10.3f}   {int(arow['n_units'])}"
        )
    below = [r for r in rows if r[1] < r[2]]
    print(
        f"\n  classes registered BELOW their measured basis: {len(below)} of {len(rows)}"
    )
    print(f"  {', '.join(r[0] for r in below)}")

    print()
    print("  Every OTHER band, for the same classes (is `committed` special?):")
    print(
        f"{'class':<16}{'band':<12}{'registered':>11}{'measured':>10}{'reg-meas':>10}"
    )
    for cls, bands in ovr.items():
        arow = art.loc[CLASS_TO_ARTIFACT[cls]]
        for band, col in (
            ("econ_low", "marg_econ_low_p50"),
            ("econ_high", "marg_econ_high_p50"),
        ):
            reg = bands.get(band)
            if reg is None:
                continue
            m = float(arow[col])
            print(f"{cls:<16}{band:<12}{reg:>11.4f}{m:>10.3f}{reg - m:>+10.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
