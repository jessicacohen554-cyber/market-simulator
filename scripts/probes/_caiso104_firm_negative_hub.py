"""CAISO-104 M-EVE-1 pre-measurement: firm-flow conduct in NEGATIVE-HUB hours.

The owner-granted M-EVE-1 ask (docs/handoffs/caiso-103-evening-firm-import-ask-
2026-07-19.md §3.2) requires this measurement BEFORE any mechanism leg: a
price-taking firm-import bid flows through negative-price hours unless the bid
constant is $0; the real contract-holder's conduct in negative-hub hours
decides which constant is structurally faithful. The rule is fixed A PRIORI
(no sweep):

  * If the measured corridor net import shows CURTAILMENT CONDUCT in
    negative-hub hours — pooled same-(month x hod)-cell relative depression
    >= 10 % AND >= 2/3 of populated cells depressed — the firm bid constant
    is $0 (+ the existing intertie tie-break eps), so the block curtails
    below zero exactly as the measured conduct does.
  * Otherwise (flows persist through negative hubs) the constant is -eps —
    the block is a pure price-taker.

Measurement (per year 2023-2025, per corridor):

  1. Corridor net import on the model clock: EIA-930 CISO BA-to-BA
     interchange (`data/raw/eia-930-interchange/CISO interchange hourly
     .parquet`), summed over the corridor DIBAs of CAISO_CORRIDOR_DIBA and
     negated — the caiso-73 shape's own basis (eia_loader.measured_firm_
     import_shape), same clock mapping (_caiso_interchange_model_clock).
  2. The corridor's own measured hub: MALIN for WECC_PNW, PALOVRDE for
     WECC_DSW (`wecc_intertie_lmp_hourly_CAISO.parquet`, model-hour keyed).
  3. Stratified comparison: within each (month, hod) cell holding >= 5
     negative-hub AND >= 5 non-negative-hub hours, the median net import in
     negative vs non-negative hours. Stratification removes the midday-glut
     confounder (negative hubs cluster at solar hours where the base is low
     anyway); the within-cell delta isolates the conduct response.
  4. The firm-base coverage check: the share of negative-hub hours whose net
     import still covers that cell's all-hours median (the caiso-73 shape
     value, clipped >= 0) — does the SELF-SCHEDULED BASE keep flowing even
     when the hub is negative, whatever the spot rungs do?

NO LP is built or solved; nothing is armed. Output feeds the FINDING-caiso104
pre-registration block.

Usage: python scripts/probes/_caiso104_firm_negative_hub.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
CORRIDOR_HUB = {"WECC_PNW": "MALIN", "WECC_DSW": "PALOVRDE"}
MIN_CELL_HOURS = 5  # per stratum, each side
DEPRESSION_THRESHOLD = 0.10  # pooled relative depression => curtailment
CELL_MAJORITY = 2.0 / 3.0  # share of cells depressed => curtailment


def corridor_net_import() -> pd.DataFrame:
    """(ts, corridor) -> net import MW on the model clock, all years."""
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.data.eia_loader import _caiso_interchange_model_clock

    path = (
        REPO
        / "data"
        / "raw"
        / "eia-930-interchange"
        / "CISO interchange hourly.parquet"
    )
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    corridor = frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    work = pd.DataFrame(
        {
            "ts": local.to_numpy(),
            "corridor": corridor.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["corridor", "mw"])
    # Net import per timestamp per corridor = -sum(interchange) (930 sign:
    # positive = CISO exporting to the DIBA).
    g = (-work.groupby(["ts", "corridor"])["mw"].sum()).reset_index(name="net_import")
    g["year"] = pd.DatetimeIndex(g["ts"]).year
    g["month"] = pd.DatetimeIndex(g["ts"]).month
    g["hod"] = pd.DatetimeIndex(g["ts"]).hour
    # Model-hour key for the hub join (hour index within the 8760 frame).
    doy = pd.DatetimeIndex(g["ts"]).dayofyear.to_numpy().copy()
    is_leap = pd.DatetimeIndex(g["ts"]).is_leap_year
    after_feb29 = is_leap & (doy > 59)  # Feb-29 dropped from the model frame
    feb29 = is_leap & (doy == 60) & (pd.DatetimeIndex(g["ts"]).month == 2)
    doy[after_feb29] = doy[after_feb29] - 1
    g = g[~feb29].copy()
    g["model_hour"] = (doy[~feb29] - 1) * 24 + g["hod"].to_numpy()
    return g


def hub_series(year: int, hub: str) -> np.ndarray:
    """(8760,) measured hub LMP, NaN where unmeasured."""
    h = pd.read_parquet(
        REPO
        / "data"
        / "raw"
        / "_validation-source"
        / "wecc_intertie_lmp_hourly_CAISO.parquet"
    )
    hy = h[(h.year == year) & (h.hub == hub)]
    v = np.full(8760, np.nan)
    v[hy.hour.to_numpy(int)] = hy.price.to_numpy(float)
    return v


def main() -> int:
    ni = corridor_net_import()
    verdict_cells = []
    for corridor, hub in CORRIDOR_HUB.items():
        print(f"\n===== {corridor} (hub {hub}) =====")
        for year in YEARS:
            gy = ni[(ni.year == year) & (ni.corridor == corridor)].copy()
            if gy.empty:
                print(f"  {year}: no interchange data")
                continue
            hp = hub_series(year, hub)
            gy = gy[gy.model_hour.between(0, 8759)]
            gy["hub"] = hp[gy.model_hour.to_numpy(int)]
            gy = gy[np.isfinite(gy.hub)]
            neg = gy[gy.hub < 0.0]
            pos = gy[gy.hub >= 0.0]
            n_neg = len(neg)
            if n_neg < 20:
                print(f"  {year}: only {n_neg} negative-hub hours — skip")
                continue
            # Stratified within-(month,hod) medians.
            cells = []
            for (m, h_), sub_n in neg.groupby(["month", "hod"]):
                sub_p = pos[(pos.month == m) & (pos.hod == h_)]
                if len(sub_n) < MIN_CELL_HOURS or len(sub_p) < MIN_CELL_HOURS:
                    continue
                med_n = float(sub_n.net_import.median())
                med_p = float(sub_p.net_import.median())
                cells.append((m, h_, len(sub_n), med_n, med_p))
            if not cells:
                print(f"  {year}: {n_neg} neg-hub hours but no populated strata")
                continue
            cdf = pd.DataFrame(
                cells, columns=["month", "hod", "n_neg", "med_neg", "med_pos"]
            )
            # Pooled relative depression, weighted by the cell's neg-hour count;
            # denominator floored at 100 MW so near-zero-base cells cannot blow
            # up the ratio.
            depr = (cdf.med_pos - cdf.med_neg) / np.maximum(cdf.med_pos, 100.0)
            pooled = float(np.average(depr, weights=cdf.n_neg))
            share_depressed = float((cdf.med_neg < cdf.med_pos).mean())
            # Firm-base coverage: all-hours cell median (the caiso-73 shape
            # statistic, clipped >= 0) vs the negative-hub hours' flow.
            shape_med = gy.groupby(["month", "hod"]).net_import.median().clip(lower=0.0)
            neg = neg.assign(
                shape_mw=shape_med.reindex(
                    pd.MultiIndex.from_arrays([neg.month, neg.hod])
                ).to_numpy()
            )
            cover = float((neg.net_import >= neg["shape_mw"]).mean())
            still_importing = float((neg.net_import > 0.0).mean())
            print(
                f"  {year}: {n_neg} neg-hub hrs ({n_neg / len(gy):.1%}), "
                f"{len(cdf)} strata | pooled rel depression {pooled:+.3f} | "
                f"cells depressed {share_depressed:.2f} | neg-hub hours with "
                f"net import > 0: {still_importing:.2f}, >= shape median: {cover:.2f} | "
                f"med flow neg {cdf.med_neg.mean():.0f} vs pos {cdf.med_pos.mean():.0f} MW"
            )
            verdict_cells.append((corridor, year, pooled, share_depressed))

    print("\n===== A-PRIORI VERDICT (>=10% pooled depression AND >=2/3 cells) =====")
    curtail_votes = 0
    for corridor, year, pooled, share in verdict_cells:
        curt = pooled >= DEPRESSION_THRESHOLD and share >= CELL_MAJORITY
        curtail_votes += int(curt)
        print(f"  {corridor} {year}: {'CURTAILMENT' if curt else 'flows persist'}")
    n = len(verdict_cells)
    overall = curtail_votes > n / 2 if n else None
    print(
        f"  OVERALL ({curtail_votes}/{n} corridor-years curtailed): bid constant = "
        + ("$0 + tie-break eps" if overall else "-eps (pure price-taker)")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
