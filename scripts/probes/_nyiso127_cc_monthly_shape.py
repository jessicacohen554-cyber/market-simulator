"""nyiso-127 — do the keeper's CC classes over-run in winter and under-run in summer?

Scorer-side, **no LP solve**. Tests a specific claim about the current NYISO
keeper (`2026-08-04-nyiso-125-seam-envelope`) against its own committed
`class_hourly_<year>.parquet` sidecar and the measured CAMPD unit record.

Method
------
* **Model** — CC_REGULAR + CC_CHP hourly MW from the keeper bundle's committed P1
  sidecar. Hours map to months on the model's FIXED NON-LEAP 8760 calendar keyed
  to 2023 (never positionally against a real calendar).
* **Actual** — CAMPD `NY_<year>.parquet` hourly `grossLoad`, summed over the units
  whose plant belongs to each class in the model's own fleet
  (`bin_assignments_NYISO.csv`), keyed by LOCAL (month, day, hour).

**Basis caveat, stated up front:** CAMPD is GROSS load at the unit; the model's
class series is the LP's dispatch on a net/grid-delivered basis, and CHP carries a
host-load allocation. The two therefore differ by a roughly constant factor, so
the ANNUAL ratio here is not a fit statistic. What is comparable — and what the
claim is about — is the **monthly SHAPE**: each side's month normalised by its own
annual mean. A seasonal error shows up there and cannot be an artifact of the
basis offset. (Class LEVELS are quoted only from the scorer's own net
grid-delivered benchmark, never from this probe's gross series.)

Result
------
**The claim holds for CC_REGULAR, and the error GROWS monotonically.** Winter-minus-
summer shape ratio **+0.150 / +0.222 / +0.304** across 2023/24/25 — the model puts
9-19 % more of its CC year into DJF than the measured fleet does, and 6-12 % less
into JJA. 2025, the year C3a fails, is the worst.

It is the visible half of a larger object. On the scorer's own net benchmark, 2025:
``ST_GAS`` **-5.07 TWh**, ``CT_PEAKER`` **-1.92 TWh**, against ``CC_CHP`` **+2.77**
and ``ST_CHP`` **+0.46``. The model substitutes PINNED, price-taking CHP for the
merchant steam-gas and peaking fleet that actually sets NYISO's summer peak — and
``CC_CHP``/``ST_CHP`` are in the C1 free-class score's ``excluded_from_free`` set,
so that substitution is invisible to the gate that would otherwise catch it.

The import channel is EXONERATED: model-vs-measured net seam is level 1.07/1.00/1.01
with JJA shape ratio 0.96/1.01/1.00 — imports are right, in level and in season, so
the seam is not what covers the missing summer thermal.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

BUNDLE = "results/calibration/nyiso125_seam_A/hourly"
YEARS = (2023, 2024, 2025)
CC_CLASSES = ("CC_REGULAR", "CC_CHP")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _model_month_of_hour(hours: int) -> np.ndarray:
    """Month index for each model hour on the fixed non-leap 2023-keyed clock."""
    return pd.date_range("2023-01-01", periods=hours, freq="h").month.to_numpy()


def model_monthly_twh(year: int, klass: str) -> np.ndarray:
    """Model monthly TWh for ``klass`` from the keeper's committed P1 sidecar."""
    df = pd.read_parquet(f"{BUNDLE}/class_hourly_{year}.parquet")
    mw = df[(df["klass"] == klass) & (df["pass"] == "P1")].sort_values("hour")["mw"]
    mw = mw.to_numpy()
    mon = _model_month_of_hour(len(mw))
    return np.array([mw[mon == m].sum() / 1e6 for m in range(1, 13)])


def actual_monthly_twh(year: int, plants: set[int]) -> np.ndarray:
    """Measured monthly TWh (CAMPD gross) over ``plants``, keyed by local clock."""
    df = pd.read_parquet(
        RAW_DIR / "campd-unit-level" / f"NY_{year}.parquet",
        columns=["facilityId", "date", "grossLoad"],
    )
    df = df[df["facilityId"].astype(int).isin(plants)]
    mon = pd.to_datetime(df["date"]).dt.month.to_numpy()
    load = df["grossLoad"].fillna(0.0).to_numpy()
    return np.array([load[mon == m].sum() / 1e6 for m in range(1, 13)])


def main() -> None:
    """Print the monthly model-vs-measured CC shape for 2023-2025."""
    fleet = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    record: dict = {"probe": "_nyiso127_cc_monthly_shape", "years": list(YEARS)}

    for klass in CC_CLASSES:
        plants = set(fleet.loc[fleet["Plant_Group"] == klass, "Plant_Code"].astype(int))
        print(f"\n================ {klass}  ({len(plants)} plants) ================")
        for year in YEARS:
            mod = model_monthly_twh(year, klass)
            act = actual_monthly_twh(year, plants)
            # Normalise each side by its OWN annual mean: shape, not level, so the
            # gross-vs-net basis offset cancels exactly.
            mod_n = mod / mod.mean()
            act_n = act / act.mean()
            ratio = mod_n / act_n
            print(f"\n  --- {year} ---   model {mod.sum():.2f} TWh (net/LP basis) · "
                  f"measured {act.sum():.2f} TWh (CAMPD gross)")
            print("        " + "".join(f"{m:>7s}" for m in MONTHS))
            print("  model " + "".join(f"{v:7.3f}" for v in mod_n))
            print("  meas  " + "".join(f"{v:7.3f}" for v in act_n))
            print("  ratio " + "".join(f"{v:7.2f}" for v in ratio))
            djf = ratio[[0, 1, 11]].mean()
            jja = ratio[[5, 6, 7]].mean()
            print(f"  >> winter (DJF) shape ratio {djf:.3f} · summer (JJA) {jja:.3f} "
                  f"· winter-minus-summer {djf - jja:+.3f}")
            record[f"{klass}|{year}"] = {
                "model_twh": round(float(mod.sum()), 3),
                "measured_gross_twh": round(float(act.sum()), 3),
                "shape_ratio_by_month": [round(float(v), 3) for v in ratio],
                "djf": round(float(djf), 3),
                "jja": round(float(jja), 3),
            }

    dest = "results/calibration/_nyiso127_cc_monthly_shape.json"
    with open(dest, "w") as fh:
        json.dump(record, fh, indent=2)
    print(f"\nrecord -> {dest}")
    print(
        "\nratio > 1 = the model puts MORE of its year in that month than the "
        "measured fleet does (over-running); < 1 = under-running."
    )


if __name__ == "__main__":
    main()
