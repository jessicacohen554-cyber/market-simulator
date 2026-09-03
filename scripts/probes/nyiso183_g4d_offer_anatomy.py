#!/usr/bin/env python3
"""nyiso-183 G4d (POST-HOC) — WHERE in the offer does the 2023 inversion sit?

**POST-HOC and labelled as such.** G4c fired on its pre-registered leg (ii) —
the model prices Ravenswood \$23.35/MWh below the downstate-steam peer median
while its MEASURED SRMC is ABOVE that median, a four-place merit displacement
(model rank 3 of 11, measured rank 7 of 11). G4c does not say WHICH term of the
offer carries it. This addendum decomposes it, still with **no solve, no
parameter and no residual**: it compares, per plant, the model's own
``heat_rate`` array (from the same fidelity-guarded no-LP reconstruction G4c
used) against the CAMPD-measured heat rate computed by the merit panel's OWN
documented formula — ``sum(heatInput) / sum(grossLoad)`` over the unit's running
hours (``grossLoad / peak >= REAL_RUN_CF``), clipped to
``[MERIT_HR_MIN, MERIT_HR_MAX]``.

No bar is declared or scored here: G4d is a locator, not a gate. Its numbers are
reported at full magnitude and nothing is adopted or rejected on them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data import campd  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.probes.nyiso183_g4c_offer_position import stgas_units  # noqa: E402
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_HR_MAX,
    MERIT_HR_MIN,
    MIN_REAL_RUN_HOURS,
    REAL_RUN_CF,
)

KEEPER = _REPO / "results" / "calibration" / "nyiso177_vintage_B1p"
RAW = _REPO / "data" / "raw"
YEARS = (2023, 2024, 2025)
ISO = "NYISO"
CLASS = "ST_GAS"
NAMES = {
    2500: "Ravenswood",
    2490: "Arthur Kill",
    8906: "Astoria Gen",
    2516: "Northport",
    2511: "E F Barrett",
    2625: "Bowline Point",
    2517: "Port Jefferson",
    2480: "Danskammer",
    2527: "Greenidge",
    8006: "Roseton",
    2682: "S A Carlson",
}


def measured_hr(
    year: int, members: set[tuple[int, str]]
) -> dict[int, tuple[float, float, float]]:
    """``{plant: (MWh-wt measured HR, gross MWh, 0)}`` — the panel's own formula.

    Restricted to ``members``, the units the MODEL routes to ``ST_GAS`` on the
    keeper's own per-unit crosswalk (see
    ``nyiso183_g4c_offer_position.stgas_units``). Without that restriction the
    plant means mix in Ravenswood's combined cycle (``UCC001``, measured HR
    7.137) and Astoria's four heat-recovery halves (5.3-5.6) — the population
    trap this session found and disclosed.
    """
    acc: dict[int, list[tuple[float, float]]] = {}
    for state in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "grossLoad", "heatInput"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df.dropna(subset=["facilityId"])
        for (fac, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
            if (int(fac), str(_uid)) not in members:
                continue
            gross = pd.to_numeric(g["grossLoad"], errors="coerce").fillna(0.0).to_numpy()
            heat = pd.to_numeric(g["heatInput"], errors="coerce").fillna(0.0).to_numpy()
            peak = float(np.max(gross)) if gross.size else 0.0
            if peak <= 0:
                continue
            run = gross / peak >= REAL_RUN_CF
            if int(run.sum()) < MIN_REAL_RUN_HOURS:
                continue
            gmwh, hmmbtu = float(gross[run].sum()), float(heat[run].sum())
            if gmwh <= 0:
                continue
            hr = float(np.clip(hmmbtu / gmwh, MERIT_HR_MIN, MERIT_HR_MAX))
            acc.setdefault(int(fac), []).append((hr, gmwh))
    return {
        f: (
            float(sum(hr * w for hr, w in rows) / sum(w for _, w in rows)),
            float(sum(w for _, w in rows)),
            0.0,
        )
        for f, rows in acc.items()
    }


def run(bundle: Path) -> dict:
    out = {
        "session": "nyiso-183",
        "gate": "G4d (POST-HOC locator, no bar, not scored)",
        "measured_hr_basis": (
            "sum(heatInput)/sum(grossLoad) over running hours "
            f"(grossLoad/peak >= REAL_RUN_CF={REAL_RUN_CF}), clipped to "
            f"[{MERIT_HR_MIN}, {MERIT_HR_MAX}] — MeritOrderPanel's own documented formula"
        ),
        "years": {},
    }
    for year in YEARS:
        state, _ = reconstruct_bundle_fleet(bundle, year, verbose=True)
        fa = state["fleet_arrays"]
        df = pd.DataFrame(
            {
                "plant": np.asarray(fa.plant_code).astype(int),
                "klass": np.asarray(fa.plant_group).astype(str),
                "cap_mw": np.asarray(fa.pmax, dtype=float),
                "heat_rate": np.asarray(fa.heat_rate, dtype=float),
                "vom": np.asarray(fa.vom, dtype=float),
                "emission_rate": np.asarray(fa.emission_rate, dtype=float),
            }
        )
        df = df[df["klass"] == CLASS]

        g = df.groupby("plant").apply(
            lambda d: pd.Series(
                {
                    "cap_mw": d["cap_mw"].sum(),
                    "model_hr": (d["heat_rate"] * d["cap_mw"]).sum()
                    / max(d["cap_mw"].sum(), 1e-9),
                    "model_vom": (d["vom"] * d["cap_mw"]).sum()
                    / max(d["cap_mw"].sum(), 1e-9),
                    "model_co2_rate": (d["emission_rate"] * d["cap_mw"]).sum()
                    / max(d["cap_mw"].sum(), 1e-9),
                }
            ),
            include_groups=False,
        )
        groups: dict[int, set[str]] = {}
        for _pl, _kl in zip(
            np.asarray(fa.plant_code).astype(int),
            np.asarray(fa.plant_group).astype(str),
        ):
            groups.setdefault(int(_pl), set()).add(_kl)
        meas = measured_hr(year, stgas_units(year, groups))
        rows = []
        for plant, r in g.iterrows():
            m = meas.get(int(plant))
            rows.append(
                {
                    "plant": int(plant),
                    "name": NAMES.get(int(plant), ""),
                    "cap_mw": round(float(r["cap_mw"]), 1),
                    "model_hr": round(float(r["model_hr"]), 3),
                    "measured_hr": None if m is None else round(m[0], 3),
                    "model_minus_measured_hr": (
                        None if m is None else round(float(r["model_hr"]) - m[0], 3)
                    ),
                    "ratio_model_over_measured": (
                        None if m is None or m[0] <= 0 else round(float(r["model_hr"]) / m[0], 3)
                    ),
                    "measured_gross_gwh": None if m is None else round(m[1] / 1000.0, 1),
                    "model_vom": round(float(r["model_vom"]), 3),
                    "model_co2_rate": round(float(r["model_co2_rate"]), 4),
                }
            )
        rows.sort(key=lambda x: x["model_hr"])
        out["years"][str(year)] = {"rows": rows}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=KEEPER)
    ap.add_argument(
        "--out",
        default=str(_REPO / "results" / "calibration" / "_nyiso183_g4d_offer_anatomy.json"),
    )
    args = ap.parse_args()
    res = run(args.bundle)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str))
    for year, v in res["years"].items():
        print(f"\n=== {year}: model heat rate vs CAMPD-measured, NYISO ST_GAS ===")
        print(pd.DataFrame(v["rows"]).to_string(index=False))
    print("\nwritten:", args.out)


if __name__ == "__main__":
    main()
