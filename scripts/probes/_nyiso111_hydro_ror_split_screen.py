"""nyiso-111 screen: can `hydro_ror_split` be armed at NYISO? (no LP)

The §5.5 lever-queue item 8 (`hydro_ror_split` NYISO classifier review) has
stood blocked since nyiso-92 on one question: what does the ORNL EHA hybrid
label ``Run-of-river/Peaking`` mean for **Robert Moses Niagara**, the plant
that carries ~52 % of NYISO's conventional-hydro MW?  nyiso-110 §10 named the
item as one of the three routes the peak half re-opens behind (its
energy-side leg: model thermal at peak = 0.936 x measured, i.e. the LP
over-peak-shaves hydro).

This screen answers the question with a **falsification test on NYISO's own
measured hydro output**, so no solve is spent on a transfer the data already
refutes (or, if it survives, so the arm is pre-checked against the bound it
would impose).

Construction
------------
A. **Classifier partition.**  Apply the committed
   ``curate_hydro_plant_modes`` rule 1 (EHA ``Mode``: Peaking / Intermediate
   Peaking -> shapeable; Run-of-river, Canal/Conduit and every hybrid label
   -> NOT shapeable) to the EHA FY2024 ``Operational`` sheet restricted to
   NYISO's own BA (``BACode == NYIS``).  Report the MW each side carries.
   Under ``hydro_ror_split`` a NOT-shapeable plant is pinned FLAT at its own
   measured monthly water (``min_gen == availability cap ==
   budget[g,m]/hours[m]``, mechanism id ``MECH_HYDRO_ROR_FLAT``), so it
   contributes EXACTLY ZERO to the fleet's diurnal swing by construction.

B. **The measured swing.**  EIA-930 ``NYIS`` ``NG: WAT`` hourly, local time,
   2023-2025.  ``NG: WAT`` is conventional hydro only for this BA: nyiso-107
   re-verified NYISO's absence from ``EIA930_PS_FOLDED_INTO_WAT``
   (``NG: WAT``/923-``HY`` = 0.9448 / 0.9606, *below* 923 HY — the opposite of
   the MISO/PJM fold signature — and NYIS ``PS`` is net negative), so
   Lewiston's and Blenheim-Gilboa's pumped storage is reported separately and
   is NOT in this series.  Zero-dropout screened the nyiso-98/99 way.

C. **The test (one-sided, sound).**  With the flat subset contributing zero,
   the model's achievable hydro diurnal swing under the arm is bounded above
   by the shapeable subset's own capability — it cannot exceed that subset's
   nameplate MW.  If the MEASURED swing exceeds that bound, arming the
   committed rule would make the model physically unable to reproduce NY
   hydro's own measured behaviour: a rule 14 ``[R-ACCURATE]`` falsification of
   the transfer, decided on NYISO data alone (rule 25 ``[R-ISO-SCOPE]``).

D. **Direction check.**  The keeper's own ``hydro`` class-hourly sidecar
   against the same measured series — which way, and by how much, the model's
   hydro shape already errs (nyiso-110 E3's over-peak-shave, restated on the
   diurnal profile rather than the peak-window level).

Governance: reads only committed artifacts, never a price or a residual; the
verdict is a statement about representability, not about fit.

Usage::

    PYTHONPATH=.:src python scripts/probes/_nyiso111_hydro_ror_split_screen.py \
        --bundle results/calibration/nyiso109_zonalanchor_B \
        --out results/calibration/_nyiso111_hydro_ror_split_screen.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EHA = REPO / "data" / "raw" / "ornl-eha" / "ORNL_EHAHydroPlant_PublicFY2024.xlsx"
NYIS_930 = REPO / "data" / "raw" / "eia-930-hourly" / "NYIS hourly.parquet"
YEARS = (2023, 2024, 2025)

# curate_hydro_plant_modes rule 1, verbatim: only these two EHA labels are
# shapeable; every other label (incl. every hybrid) is pinned flat.
SHAPEABLE_MODES = {"Peaking", "Intermediate Peaking"}
# nyiso-109/110 windows, verbatim.
TROUGH_HOURS = (1, 2, 3, 4, 5)
PEAK_HOURS = (17, 18, 19)


def eha_partition() -> dict:
    """MW on each side of the committed classifier for NYISO's own BA."""
    df = pd.read_excel(EHA, sheet_name="Operational")
    ny = df[df["BACode"].astype(str).str.upper() == "NYIS"].copy()
    ny["CH_MW"] = pd.to_numeric(ny["CH_MW"], errors="coerce").fillna(0.0)
    ny["Mode"] = ny["Mode"].astype(str)
    total = float(ny["CH_MW"].sum())
    by_mode = (
        ny.groupby("Mode")["CH_MW"].agg(n="size", mw="sum").sort_values("mw", ascending=False)
    )
    shapeable = ny[ny["Mode"].isin(SHAPEABLE_MODES)]
    flat = ny[~ny["Mode"].isin(SHAPEABLE_MODES)]
    top = ny.sort_values("CH_MW", ascending=False).head(6)
    return {
        "n_plants": int(len(ny)),
        "total_ch_mw": round(total, 1),
        "by_mode": {
            str(m): {"n": int(r.n), "mw": round(float(r.mw), 1), "share_pct": round(100 * r.mw / total, 1)}
            for m, r in by_mode.iterrows()
        },
        "shapeable_mw": round(float(shapeable["CH_MW"].sum()), 1),
        "shapeable_share_pct": round(100 * float(shapeable["CH_MW"].sum()) / total, 1),
        "flat_mw": round(float(flat["CH_MW"].sum()), 1),
        "flat_share_pct": round(100 * float(flat["CH_MW"].sum()) / total, 1),
        "largest_plants": [
            {
                "eia_id": (int(r.EIA_PtID) if pd.notna(r.EIA_PtID) else None),
                "name": str(r.PtName),
                "mode": str(r.Mode),
                "ch_mw": round(float(r.CH_MW), 1),
                "ps_mw": (None if pd.isna(r.PS_MW) else round(float(r.PS_MW), 1)),
                "shapeable_under_committed_rule": bool(str(r.Mode) in SHAPEABLE_MODES),
            }
            for r in top.itertuples(index=False)
        ],
    }


def measured_hydro() -> dict:
    """Hour-of-day profile of EIA-930 NYIS ``NG: WAT``, per year."""
    raw = pd.read_parquet(NYIS_930)
    df = raw[["Local time", "NG: WAT"]].copy()
    df["ts"] = pd.to_datetime(df["Local time"])
    df["year"] = df.ts.dt.year
    df["hod"] = df.ts.dt.hour
    df["date"] = df.ts.dt.date
    out: dict = {}
    for year in YEARS:
        s = df[(df.year == year) & df["NG: WAT"].notna()].copy()
        if s.empty:
            continue
        # nyiso-98/99 zero-dropout screen: exactly-0.0 hours in a series whose
        # neighbours are multi-GW are a reporting artifact, not real output.
        zeros = int((s["NG: WAT"] == 0.0).sum())
        s = s[s["NG: WAT"] > 0.0]
        prof = s.groupby("hod")["NG: WAT"].mean()
        day = s.groupby("date")["NG: WAT"].agg(["min", "max"])
        rng = day["max"] - day["min"]
        out[str(year)] = {
            "n_hours": int(len(s)),
            "zero_hours_screened": zeros,
            "annual_twh": round(float(s["NG: WAT"].sum()) / 1e6, 3),
            "hod_profile_mw": {str(h): round(float(prof.get(h, np.nan)), 1) for h in range(24)},
            "hod_trough_mw": round(float(prof.loc[list(TROUGH_HOURS)].mean()), 1),
            "hod_peak_mw": round(float(prof.loc[list(PEAK_HOURS)].mean()), 1),
            "hod_window_swing_mw": round(
                float(prof.loc[list(PEAK_HOURS)].mean() - prof.loc[list(TROUGH_HOURS)].mean()), 1
            ),
            "hod_minmax_swing_mw": round(float(prof.max() - prof.min()), 1),
            "within_day_range_p50_mw": round(float(rng.median()), 1),
            "within_day_range_p90_mw": round(float(rng.quantile(0.90)), 1),
            "within_day_range_max_mw": round(float(rng.max()), 1),
        }
    return out


def model_hydro(bundle: Path) -> dict:
    """Hour-of-day profile of the keeper's own ``hydro`` class dispatch."""
    out: dict = {}
    for year in YEARS:
        path = bundle / "hourly" / f"class_hourly_{year}.parquet"
        if not path.exists():
            continue
        d = pd.read_parquet(path)
        h = d[(d["klass"] == "hydro")].copy()
        if "pass" in h.columns:
            h = h[h["pass"] == sorted(h["pass"].unique())[-1]]
        h = h.groupby("hour", as_index=False)["mw"].sum()
        # Model hour 0..8759 is local-time-indexed the same way the scorer reads it.
        h["hod"] = h["hour"] % 24
        prof = h.groupby("hod")["mw"].mean()
        out[str(year)] = {
            "annual_twh": round(float(h["mw"].sum()) / 1e6, 3),
            "hod_profile_mw": {str(k): round(float(v), 1) for k, v in prof.items()},
            "hod_trough_mw": round(float(prof.loc[list(TROUGH_HOURS)].mean()), 1),
            "hod_peak_mw": round(float(prof.loc[list(PEAK_HOURS)].mean()), 1),
            "hod_window_swing_mw": round(
                float(prof.loc[list(PEAK_HOURS)].mean() - prof.loc[list(TROUGH_HOURS)].mean()), 1
            ),
            "hod_minmax_swing_mw": round(float(prof.max() - prof.min()), 1),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/nyiso109_zonalanchor_B")
    ap.add_argument("--out", default="results/calibration/_nyiso111_hydro_ror_split_screen.json")
    args = ap.parse_args(argv)

    part = eha_partition()
    meas = measured_hydro()
    mod = model_hydro(REPO / args.bundle if not Path(args.bundle).is_absolute() else Path(args.bundle))

    bound = part["shapeable_mw"]
    verdict: dict = {"bound_mw": bound, "years": {}}
    for year, m in meas.items():
        verdict["years"][year] = {
            "measured_hod_window_swing_mw": m["hod_window_swing_mw"],
            "measured_hod_minmax_swing_mw": m["hod_minmax_swing_mw"],
            "measured_within_day_p50_mw": m["within_day_range_p50_mw"],
            "swing_over_bound_ratio": round(m["hod_minmax_swing_mw"] / bound, 3),
            "p50_over_bound_ratio": round(m["within_day_range_p50_mw"] / bound, 3),
            "falsified_on_mean_profile": bool(m["hod_minmax_swing_mw"] > bound),
            "falsified_on_median_day": bool(m["within_day_range_p50_mw"] > bound),
        }
    verdict["all_years_falsified_on_mean_profile"] = all(
        v["falsified_on_mean_profile"] for v in verdict["years"].values()
    )

    payload = {
        "probe": "nyiso-111 hydro_ror_split NYISO screen",
        "eha_partition": part,
        "measured_hydro_930": meas,
        "model_hydro_keeper": mod,
        "falsification": verdict,
    }
    out = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1))

    print("=== A: committed classifier partition on NYISO's own BA (EHA FY2024) ===")
    print(f"  {part['n_plants']} plants, {part['total_ch_mw']:,.1f} MW conventional hydro")
    for m, r in part["by_mode"].items():
        mark = "SHAPEABLE" if m in SHAPEABLE_MODES else "flat-pinned"
        print(f"    {m:32s} n={r['n']:3d}  {r['mw']:8.1f} MW  {r['share_pct']:5.1f} %   -> {mark}")
    print(
        f"  => shapeable {part['shapeable_mw']:,.1f} MW ({part['shapeable_share_pct']} %) | "
        f"FLAT-PINNED {part['flat_mw']:,.1f} MW ({part['flat_share_pct']} %)"
    )
    print("\n  largest plants:")
    for p in part["largest_plants"]:
        print(
            f"    {p['name']:32s} EIA {p['eia_id']}  {p['mode']:30s} "
            f"CH {p['ch_mw']:8.1f} MW  PS {p['ps_mw']}  shapeable={p['shapeable_under_committed_rule']}"
        )

    print("\n=== B/C: measured swing vs the arm's own bound ===")
    print(f"  bound = shapeable-subset nameplate = {bound:,.1f} MW")
    for year, v in verdict["years"].items():
        print(
            f"  {year}: measured hod swing {v['measured_hod_minmax_swing_mw']:7.1f} MW "
            f"({v['swing_over_bound_ratio']:.2f}x bound)   median-day range "
            f"{v['measured_within_day_p50_mw']:7.1f} MW ({v['p50_over_bound_ratio']:.2f}x)   "
            f"FALSIFIED={v['falsified_on_mean_profile']}"
        )

    print("\n=== D: model vs measured hydro diurnal shape (keeper) ===")
    for year in meas:
        if year not in mod:
            continue
        m, k = meas[year], mod[year]
        print(
            f"  {year}: model swing {k['hod_window_swing_mw']:7.1f} vs measured "
            f"{m['hod_window_swing_mw']:7.1f} MW (peak-trough window); "
            f"model peak {k['hod_peak_mw']:7.1f} vs measured {m['hod_peak_mw']:7.1f} MW"
        )

    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
