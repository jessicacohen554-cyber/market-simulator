"""pjm-147 — audit the freshly-derived PJM measured-CHP artifact before any solve.

Answers, on the artifact plus PJM's own metered CAMPD record, the four questions
every prior ISO's CHP session had to answer before it was allowed to arm the
flag (miso-99, caiso-147, nyiso-105, neiso-70):

1. **What did the caiso-147 seam fix actually buy in PJM?** PJM is the other
   member of ``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS``, so the pre-fix gate
   (compare eGRID's credited rate against the SHIPPED rate) would have thrown
   out every hand-factored plant. Count them.
2. **Coverage** — of class capacity, and of the class's own metered CAMPD
   energy (the statistic that decides whether thin capacity coverage matters).
3. **Adverse selection** — is the covered population systematically different
   from the uncovered one?
4. **Direction and size** of the repricing, per class and per plant, at the
   seam the LP actually reads.

Rule 23 [R-FROZEN-DERIVE]: this reads the artifact, it does not tune it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR
from market_sim.data import campd
from market_sim.data.fleet import load_fleet_from_csv

ISO = "PJM"
TARGET = ("CC_CHP", "CT_CHP")
HAND_CT_MULT = 1.8  # data/chp.py::_correct_chp_steam_credit_hr, sub-8.0 CT_CHP
HAND_CC_MULT = 1.15  # sub-6.0 CC_CHP, floored at 6.3


def main() -> int:
    art = pd.read_csv(PROCESSED_DIR / f"chp_power_only_heat_rates_{ISO}.csv")
    fleet = load_fleet_from_csv(ISO, get_iso_config(ISO))

    caps: dict[tuple[int, str], float] = {}
    for gen in fleet:
        if gen.plant_group in TARGET and int(gen.plant_code or 0):
            key = (int(gen.plant_code), gen.plant_group)
            caps[key] = caps.get(key, 0.0) + float(gen.pmax_mw)

    print("=" * 78)
    print("Q1  the caiso-147 seam fix — how much of PJM was it worth?")
    print("=" * 78)
    hand = art[
        np.isfinite(art["basis_heat_rate"])
        & np.isfinite(art["model_heat_rate"])
        & (np.abs(art["model_heat_rate"] / art["basis_heat_rate"] - 1.0) > 1e-3)
    ]
    print(f"  rows whose SHIPPED rate != the seam rate (hand factor fired): {len(hand)}")
    for _, r in hand.iterrows():
        mult = float(r["model_heat_rate"]) / float(r["basis_heat_rate"])
        print(
            f"    {int(r['plant_code']):>6} {r['plant_name'][:34]:<34} "
            f"{r['plant_group']:<7} {r['class_capacity_mw']:7.1f} MW  "
            f"seam {r['basis_heat_rate']:7.4f} -> shipped {r['model_heat_rate']:7.4f} "
            f"(x{mult:.3f})  measured {r['heat_rate']:7.4f}  flag={r['flag']}"
        )
    hand_ok = hand[hand["flag"] == "ok"]
    print(
        f"  of those, applied (flag==ok): {len(hand_ok)} rows / "
        f"{hand_ok['class_capacity_mw'].sum():.1f} MW"
    )
    print(
        "  => under the PRE-caiso-147 gate these would have read basis_mismatch\n"
        f"     and been excluded. PJM's latent defect: {len(hand_ok)} rows."
    )

    print()
    print("=" * 78)
    print("Q2  coverage — capacity, and the class's own metered CAMPD energy")
    print("=" * 78)
    cems = _campd_class_energy()
    ok = art[art["flag"] == "ok"]
    for klass in TARGET:
        tot_mw = sum(mw for (_, k), mw in caps.items() if k == klass)
        sub = ok[ok["plant_group"] == klass]
        cov_mw = float(sub["class_capacity_mw"].sum())
        codes_all = {c for (c, k) in caps if k == klass}
        codes_ok = set(sub["plant_code"].astype(int))
        e_all = sum(cems.get(c, 0.0) for c in codes_all)
        e_ok = sum(cems.get(c, 0.0) for c in codes_ok)
        print(
            f"  {klass:<7} {len(sub):>2}/{len(codes_all):<3} plants  "
            f"{cov_mw:8.1f}/{tot_mw:8.1f} MW ({100 * cov_mw / tot_mw:5.1f} %)   "
            f"metered energy {e_ok / 1e6:8.3f}/{e_all / 1e6:8.3f} TWh "
            f"({100 * e_ok / e_all if e_all else float('nan'):5.1f} %)"
        )

    print()
    print("=" * 78)
    print("Q3  adverse selection — covered vs uncovered incumbent rate")
    print("=" * 78)
    for klass in TARGET:
        sub = art[art["plant_group"] == klass]
        cov = sub[sub["flag"] == "ok"]
        unc = sub[sub["flag"] != "ok"]
        for name, frame in (("covered", cov), ("uncovered", unc)):
            w = frame["class_capacity_mw"].to_numpy(float)
            hr = frame["model_heat_rate"].to_numpy(float)
            fin = np.isfinite(hr) & (w > 0)
            val = float(np.average(hr[fin], weights=w[fin])) if fin.any() else float("nan")
            print(
                f"  {klass:<7} {name:<9} n={len(frame):>3}  {w.sum():8.1f} MW  "
                f"cap-wt shipped HR {val:7.3f}"
            )

    print()
    print("=" * 78)
    print("Q4  direction and size at the LP seam (measured vs SHIPPED rate)")
    print("=" * 78)
    for klass in TARGET:
        sub = ok[ok["plant_group"] == klass]
        w = sub["class_capacity_mw"].to_numpy(float)
        meas = sub["heat_rate"].to_numpy(float)
        ship = sub["model_heat_rate"].to_numpy(float)
        fin = np.isfinite(ship) & (w > 0)
        mw_meas = float(np.average(meas[fin], weights=w[fin]))
        mw_ship = float(np.average(ship[fin], weights=w[fin]))
        dearer = int((meas[fin] > ship[fin] * 1.001).sum())
        cheaper = int((meas[fin] < ship[fin] * 0.999).sum())
        mw_dearer = float(w[fin][meas[fin] > ship[fin] * 1.001].sum())
        mw_cheaper = float(w[fin][meas[fin] < ship[fin] * 0.999].sum())
        print(
            f"  {klass:<7} cap-wt {mw_ship:7.3f} -> {mw_meas:7.3f} MMBtu/MWh "
            f"({100 * (mw_meas / mw_ship - 1.0):+6.1f} %)   "
            f"dearer {dearer} rows / {mw_dearer:7.1f} MW   "
            f"cheaper {cheaper} rows / {mw_cheaper:7.1f} MW"
        )

    print()
    print("  excluded population (what the gates threw out, by capacity):")
    exc = art[art["flag"] != "ok"]
    for flag, grp in exc.groupby("flag"):
        ts = grp["thermal_share"].astype(float)
        print(
            f"    {flag:<22} n={len(grp):>3}  {grp['class_capacity_mw'].sum():8.1f} MW  "
            f"median thermal_share {ts.median():.3f}  "
            f"median add-back HR {grp['heat_rate'].astype(float).median():8.3f}"
        )
    return 0


def _campd_class_energy() -> dict[int, float]:
    """Return ``{plant_code: metered CAMPD gross MWh}`` summed over 2023-2025.

    Narrowed to the ISO's own states on read, exactly as the deriver's own
    :func:`cems_annual_heat` does, so a shared state extract cannot leak another
    ISO's units in.
    """
    out: dict[int, float] = {}
    for state in campd.states_for_iso(ISO):
        for year in (2023, 2024, 2025):
            path = RAW_DIR / "campd-unit-level" / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(path, columns=["facilityId", "grossLoad"])
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df.dropna(subset=["facilityId", "grossLoad"])
            for code, mwh in df.groupby("facilityId")["grossLoad"].sum().items():
                out[int(code)] = out.get(int(code), 0.0) + float(mwh)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
