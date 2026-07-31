"""caiso-147 probe: CAISO CHP artifact coverage, selection and energy reach.

No LP. Reports what the applied (``flag == "ok"``) population covers on
capacity AND on independently metered CAMPD energy, and whether the covered
plants differ systematically from the excluded ones (adverse selection).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402

ART = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv"


def campd_gen(year: int, codes: set[int]) -> dict[int, float]:
    """Return ``{plant_code: metered gross MWh}`` for the ISO's CHP plants."""
    out: dict[int, float] = {}
    for state in campd.states_for_iso("CAISO"):
        p = RAW_DIR / "campd-unit-level" / f"{state}_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p, columns=["facilityId", "grossLoad"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)].dropna(subset=["grossLoad"])
        for c, v in df.groupby("facilityId")["grossLoad"].sum().items():
            out[int(c)] = out.get(int(c), 0.0) + float(v)
    return out


def main() -> int:
    """Report coverage, energy reach and selection for the CAISO artifact."""
    df = pd.read_csv(ART)
    codes = set(df.plant_code.astype(int))
    gen = campd_gen(2023, codes)
    df["campd_mwh_2023"] = df.plant_code.astype(int).map(gen)

    print("=== COVERAGE by class ===")
    for k, s in df.groupby("plant_group"):
        ok = s[s.flag == "ok"]
        cap_c, cap_t = ok.class_capacity_mw.sum(), s.class_capacity_mw.sum()
        # Energy is per PLANT, so credit it once per plant, not once per row.
        e_ok = s[s.flag == "ok"].drop_duplicates("plant_code").campd_mwh_2023.sum()
        e_all = s.drop_duplicates("plant_code").campd_mwh_2023.sum()
        print(
            f"{k}: {len(ok)}/{len(s)} rows  {cap_c:.0f}/{cap_t:.0f} MW "
            f"({100 * cap_c / cap_t:.1f} %)  |  metered 2023 energy "
            f"{e_ok / 1e6:.3f}/{e_all / 1e6:.3f} TWh "
            f"({100 * e_ok / e_all if e_all else float('nan'):.1f} %)"
        )

    print("\n=== ADVERSE SELECTION (eGRID CREDITED rate, cap-weighted) ===")
    for k, s in df.groupby("plant_group"):
        for lab, sub in (
            ("covered ", s[s.flag == "ok"]),
            ("excluded", s[s.flag != "ok"]),
        ):
            sub = sub[np.isfinite(sub.heat_rate_credited) & (sub.class_capacity_mw > 0)]
            if sub.empty:
                continue
            w = sub.class_capacity_mw
            print(
                f"  {k} {lab}: n={len(sub):>3} {w.sum():7.1f} MW  "
                f"credited {np.average(sub.heat_rate_credited, weights=w):6.3f}  "
                f"thermal_share {np.average(sub.thermal_share.fillna(0), weights=w):.3f}"
            )

    print("\n=== not_unfired_topping: thermal_share distribution ===")
    nt = df[df.flag == "not_unfired_topping"]
    print(
        f"  n={len(nt)}  {nt.class_capacity_mw.sum():.0f} MW  "
        f"thermal_share min {nt.thermal_share.min():.3f} "
        f"median {nt.thermal_share.median():.3f} max {nt.thermal_share.max():.3f} "
        f"(gate 0.50)"
    )
    print(
        f"  power-only rate they WOULD have taken: median "
        f"{nt.heat_rate.median():.2f}, max {nt.heat_rate.max():.1f} MMBtu/MWh"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
