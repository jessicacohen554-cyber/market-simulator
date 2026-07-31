"""caiso-147 probe: why does the CHP derive's basis gate exclude 65 of 92 rows?

No LP. Measures whether CAISO's ``basis_mismatch`` population is exactly the
population :func:`market_sim.data.chp._correct_chp_steam_credit_hr` hand-corrects,
by loading the fleet twice — once as shipped, once with the hand factor
neutralised — and comparing each (plant, class) incumbent against eGRID's
credited rate ``PLHTIAN / PLNGENAN``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import eia860  # noqa: E402

TARGET = ("CC_CHP", "CT_CHP")
ISO = "CAISO"


def cap_weighted(gens) -> dict[tuple[int, str], tuple[float, float]]:
    """Return ``{(plant, class): (cap-weighted heat rate, capacity MW)}``."""
    num: dict[tuple[int, str], float] = {}
    den: dict[tuple[int, str], float] = {}
    for g in gens:
        if g.plant_group not in TARGET:
            continue
        code = int(g.plant_code or 0)
        if not code:
            continue
        key = (code, g.plant_group)
        num[key] = num.get(key, 0.0) + float(g.pmax_mw) * float(g.heat_rate)
        den[key] = den.get(key, 0.0) + float(g.pmax_mw)
    return {k: (num[k] / den[k], den[k]) for k in num if den[k] > 0}


def main() -> int:
    """Report the basis-gate census with and without the hand factor."""
    cfg = get_iso_config(ISO)
    shipped = cap_weighted(eia860.load_fleet_from_csv(ISO, cfg))

    real = eia860._correct_chp_steam_credit_hr
    eia860._correct_chp_steam_credit_hr = lambda *a, **k: None
    try:
        eia860._pkg_ns()._BINNED_FLEET_CACHE.clear()
    except Exception:
        pass
    try:
        raw = cap_weighted(eia860.load_fleet_from_csv(ISO, cfg))
    finally:
        eia860._correct_chp_steam_credit_hr = real

    art = pd.read_csv(
        REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv"
    )
    art["key"] = list(zip(art.plant_code.astype(int), art.plant_group))
    art["hr_shipped"] = [shipped.get(k, (np.nan, 0))[0] for k in art.key]
    art["hr_prehand"] = [raw.get(k, (np.nan, 0))[0] for k in art.key]
    art["prehand_vs_credited"] = art.hr_prehand / art.heat_rate_credited

    print(f"{'flag':<22}{'n':>4}{'MW':>9}  pre-hand/credited within 0.5 %")
    for flag, sub in art.groupby("flag"):
        ok = sub.prehand_vs_credited.between(0.995, 1.005).sum()
        print(
            f"{flag:<22}{len(sub):>4}{sub.class_capacity_mw.sum():>9.1f}  {ok}/{len(sub)}"
        )

    bm = art[art.flag == "basis_mismatch"]
    hits = bm.prehand_vs_credited.between(0.995, 1.005)
    print(
        f"\nbasis_mismatch explained by the hand factor alone: "
        f"{hits.sum()}/{len(bm)} rows, "
        f"{bm.loc[hits, 'class_capacity_mw'].sum():.1f}/"
        f"{bm.class_capacity_mw.sum():.1f} MW"
    )
    miss = bm[~hits]
    if not miss.empty:
        print("\nNOT explained (genuine repair / bin fallback):")
        print(
            miss[
                [
                    "plant_code",
                    "plant_group",
                    "plant_name",
                    "class_capacity_mw",
                    "heat_rate_credited",
                    "hr_prehand",
                    "hr_shipped",
                    "heat_rate",
                ]
            ].to_string(index=False)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
