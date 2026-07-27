"""Decompose the NYISO CT_PEAKER energy gap into ONLINE-HOURS x LOADING-WHEN-ON.

The follow-on to ``nyiso90_ct_run_lengths.py``. That probe showed the model
reproduces the measured run-LENGTH distribution, which eliminates minimum-run /
block commitment as the class's missing mechanism. This one asks where the
energy actually goes, using the identity::

    energy = online_plant_hours x mean_MW_when_online

so the 1.8-2.1 TWh gap splits into a COMMITMENT term (how many plant-hours the
fleet is synchronized) and a LOADING term (how hard it is pushed when it is).

Both sides use ONE common capacity scale — the plant's measured CAMPD HSL
(p99.5 of pooled gross load, the ``derive_campd_gas_commitment_params.py``
convention) — so the online threshold ``max(1 MW, 0.05 x HSL)`` is literally the
same number for the model and the meter. That removes the asymmetry in the
run-length probe, where each side was thresholded against its OWN observed
maximum and the model's is depressed by the very under-dispatch being measured.

The measured series is converted GROSS -> NET with the committed parasitic
factors (``parasitic_load_factors.parquet``), the same artifact the benchmark
uses, so both sides are net MWh (nyiso-89 §1: mixing the two bases was worth
2.5x on that session's headline).

Usage::

    python scripts/probes/nyiso90_ct_gap_decomposition.py \
        --bundle results/calibration/nyiso90_ctrl_zerodelta
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CLEAN_DIR, PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

CT_UNIT_TYPE = "combustion turbine"
ONLINE_FRAC = 0.05
HSL_PCTILE = 99.5


def _parasitic_factors() -> dict[int, float]:
    """Return ``{plant_code: parasitic factor}`` from the committed artifact."""
    for path in (
        CLEAN_DIR / "parasitic-load" / "parasitic_load_factors.parquet",
        PROCESSED_DIR / "parasitic_load_factors.parquet",
    ):
        if path.exists():
            d = pd.read_parquet(path)
            code = "plant_code" if "plant_code" in d else "plant_id"
            col = next(
                (c for c in ("parasitic_factor", "factor", "net_frac") if c in d), None
            )
            if col:
                return dict(zip(d[code].astype(int), d[col].astype(float)))
    return {}


def measured_plant_hours(iso: str, year: int, codes: set[int]) -> pd.DataFrame:
    """Return per-plant measured HSL, online hours and gross MWh for the year."""
    frames = []
    for state in states_for_iso(iso):
        path = RAW_DIR / "campd-unit-level" / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        d = pd.read_parquet(
            path,
            columns=["facilityId", "date", "hour", "grossLoad", "unitType"],
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["facilityId"].isin(codes)]
        d = d[d["unitType"].astype(str).str.strip().str.casefold() == CT_UNIT_TYPE]
        if not d.empty:
            frames.append(d)
    if not frames:
        return pd.DataFrame()
    d = pd.concat(frames, ignore_index=True)
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    plant = (
        d.groupby(["facilityId", "date", "hour"], observed=True)["grossLoad"]
        .sum()
        .reset_index()
    )
    rows = []
    for code, g in plant.groupby("facilityId", observed=True):
        mw = g["grossLoad"].to_numpy(dtype=float)
        hsl = float(np.percentile(mw, HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue
        thresh = max(_ONLINE_MW, ONLINE_FRAC * hsl)
        on = mw >= thresh
        rows.append(
            {
                "plant_code": int(code),
                "hsl_mw": hsl,
                "thresh_mw": thresh,
                "meas_online_h": int(on.sum()),
                "meas_gross_mwh": float(mw[on].sum()),
            }
        )
    return pd.DataFrame(rows)


def model_plant_hours(bundle: Path, year: int, thresh: dict[int, float]) -> pd.DataFrame:
    """Return per-plant model online hours and MWh at the COMMON threshold."""
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "plant_code", "klass", "hour", "mw"],
    )
    df = df[(df["klass"] == "CT_PEAKER") & (df["pass"] == "P1")]
    plant = df.groupby(["plant_code", "hour"], observed=True)["mw"].sum().unstack("hour")
    rows = []
    for code, row in plant.iterrows():
        code = int(code)
        if code not in thresh:
            continue
        mw = np.nan_to_num(row.to_numpy(dtype=float))
        on = mw >= thresh[code]
        rows.append(
            {
                "plant_code": code,
                "model_online_h": int(on.sum()),
                "model_mwh": float(mw[on].sum()),
                "model_mwh_all": float(mw.sum()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Print the per-year commitment/loading decomposition of the CT gap."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--arm", default=None)
    ap.add_argument("--iso", default="NYISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    par = _parasitic_factors()
    out = []
    for year in args.years:
        disp = Path(args.bundle) / "dispatch" / f"{year}_P1.parquet"
        if not disp.exists():
            print(f"  (skip {year}: not on disk)")
            continue
        codes = set(
            pd.read_parquet(disp, columns=["klass", "plant_code"])
            .query("klass == 'CT_PEAKER'")["plant_code"]
            .astype(int)
            .unique()
            .tolist()
        )
        meas = measured_plant_hours(args.iso, year, codes)
        if meas.empty:
            continue
        thresh = dict(zip(meas["plant_code"], meas["thresh_mw"]))
        meas["parasitic"] = meas["plant_code"].map(par).fillna(1.0)
        meas["meas_net_mwh"] = meas["meas_gross_mwh"] * meas["parasitic"]

        for label, bundle in (("control", args.bundle), ("ARM", args.arm)):
            if bundle is None:
                continue
            if not (Path(bundle) / "dispatch" / f"{year}_P1.parquet").exists():
                continue
            mod = model_plant_hours(Path(bundle), year, thresh)
            j = meas.merge(mod, on="plant_code", how="inner")
            mh, oh = j["meas_online_h"].sum(), j["model_online_h"].sum()
            mm, om = j["meas_net_mwh"].sum(), j["model_mwh"].sum()
            out.append(
                {
                    "year": year,
                    "series": label,
                    "plants": len(j),
                    "meas_online_h": mh,
                    "model_online_h": oh,
                    "online_ratio": oh / mh if mh else np.nan,
                    "meas_MW_on": mm / mh if mh else np.nan,
                    "model_MW_on": om / oh if oh else np.nan,
                    "loading_ratio": (om / oh) / (mm / mh) if oh and mh else np.nan,
                    "meas_TWh": mm / 1e6,
                    "model_TWh": om / 1e6,
                    "energy_ratio": om / mm if mm else np.nan,
                }
            )

    d = pd.DataFrame(out)
    with pd.option_context("display.width", 220, "display.max_columns", 40):
        print(d.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(
        "\nIdentity check: online_ratio x loading_ratio should equal energy_ratio"
    )
    if not d.empty:
        print(
            (d["online_ratio"] * d["loading_ratio"] - d["energy_ratio"])
            .abs()
            .max()
            .round(9),
            "= max abs residual",
        )


if __name__ == "__main__":
    main()
