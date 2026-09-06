"""miso-225 phase 0 (A2) — is the 923-print-over-hub wedge FIXED-CHARGE amortization, or a REAL marginal delivery cost?

The owner's ruling (2026-09-06) rests on a premise stated in miso-224 and in
``apply_miso_gas_marginal_commodity``'s own docstring: the EIA-923 print exceeds
the traded hub because it amortizes DEMAND CHARGES and CONTRACTED TRANSPORT over
the month's takes, and a dispatch offer must carry only the variable part.  That
premise is TESTABLE against the receipts, and A1
(``_miso225_transport_identification_phase0.py``) already returned its first
diagnostic: the ``wedge = v + F/burn`` fit has median R2 ~ 0.10, so volume
explains almost none of the wedge's variation.

This instrument asks the three questions that decide whether the ruled form is a
material change from the status quo at all, all zero-LP and all on committed
inputs:

* **(a) How big is the amortized fixed leg where it matters?**  Each plant's own
  fitted ``F[p]`` evaluated at that plant's own mean burn, in $/MMBtu, capacity-
  weighted and by class.  If the fixed leg is immaterial for the classes that set
  price, the wedge is variable by measurement and the ruled form lands near the
  status quo in LEVEL — the arm's move was never mostly a convention repair.
* **(b) Does the print LAG the commodity?**  miso-224 §3.3 says it does ("the
  print lags the collapse of the commodity").  A lagging average would make the
  wedge move OPPOSITE to the hub's month-over-month change.  A real delivery cost
  would not.  Correlation of the wedge with d(hub) is the discriminator.
* **(c) What does a direct, regression-free estimator say?**  The variable leg is
  the asymptote of the wedge as burn grows, so the plant's own top-burn-quartile
  months estimate it with no functional form at all.  Two estimators that agree
  are a measurement; two that disagree are a warning.

Zero-LP.  Writes ``_miso225_wedge_anatomy.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "results/calibration/_miso225_transport_id.json"
OUT = ROOT / "results/calibration/_miso225_wedge_anatomy.json"

# Rebuilt here from the same committed inputs A1 used, so this instrument is
# self-contained and its panel is reproducible without A1's intermediate frame.
import sys

sys.path.insert(0, str(ROOT / "scripts/probes"))
from _miso225_transport_identification_phase0 import (  # noqa: E402
    BINS,
    F923,
    GAS_GROUPS,
    YEARS,
    _fit,
    _hub_month_means,
)
from market_sim.data.fuel.basis.miso import _miso_zone_hub_kind  # noqa: E402


def _panel() -> pd.DataFrame:
    bins = pd.read_csv(BINS)
    gas = bins[bins["Plant_Group"].astype(str).str.startswith(GAS_GROUPS)].copy()
    zone_kind = _miso_zone_hub_kind(YEARS[0])
    gas["hub_kind"] = gas["Zone"].map(zone_kind).fillna("chicago")
    f923 = pd.read_parquet(F923)
    f923 = f923[
        (f923["fuel_group"] == "Natural Gas")
        & (f923["year"].isin(YEARS))
        & (f923["quantity"] > 0)
        & (f923["price_per_mmbtu"] > 0)
    ]
    hub = _hub_month_means()
    rows = []
    for r in gas.itertuples():
        for m in f923[f923["plant_id"] == int(r.Plant_Code)].itertuples():
            h = hub.get((r.hub_kind, int(m.year), int(m.month)))
            if h is None:
                continue
            rows.append(
                dict(
                    plant_id=int(r.Plant_Code),
                    group=str(r.Plant_Group),
                    zone=str(r.Zone),
                    mw=float(r.Nameplate_MW),
                    year=int(m.year),
                    month=int(m.month),
                    burn=float(m.quantity),
                    hub=h,
                    wedge=float(m.price_per_mmbtu) - h,
                )
            )
    p = pd.DataFrame(rows)
    p["t"] = p["year"] * 12 + p["month"]
    return p


def main() -> None:
    panel = _panel()
    per = {r["plant_id"]: r for r in json.loads(IN.read_text())["per_plant"]}

    # ---- (a) the amortized fixed leg, in $/MMBtu, at each plant's own mean burn
    recs = []
    for pid, grp in panel.groupby("plant_id"):
        rec = per.get(int(pid))
        if not rec or not rec.get("identified"):
            continue
        mean_burn = float(grp["burn"].mean())
        fixed_leg = float(rec["fixed_usd_month"]) / mean_burn
        recs.append(
            dict(
                plant_id=int(pid),
                group=grp["group"].iloc[0],
                mw=float(grp["mw"].iloc[0]),
                mean_burn=mean_burn,
                v=float(rec["v_usd_mmbtu"]),
                fixed_leg_usd_mmbtu=fixed_leg,
                mean_wedge=float(grp["wedge"].mean()),
                burn_wtd_wedge=float((grp["wedge"] * grp["burn"]).sum() / grp["burn"].sum()),
            )
        )
    a = pd.DataFrame(recs)

    def wmean(frame: pd.DataFrame, col: str, wcol: str = "mw") -> float:
        w = frame[wcol].to_numpy(float)
        return float((frame[col].to_numpy(float) * w).sum() / w.sum()) if w.sum() else float("nan")

    by_class = {}
    for g, grp in a.groupby("group"):
        by_class[str(g)] = dict(
            n_plants=int(len(grp)),
            mw=float(grp["mw"].sum()),
            v_cap_wtd=wmean(grp, "v"),
            fixed_leg_cap_wtd=wmean(grp, "fixed_leg_usd_mmbtu"),
            mean_wedge_cap_wtd=wmean(grp, "mean_wedge"),
            fixed_share_of_wedge=(
                wmean(grp, "fixed_leg_usd_mmbtu") / wmean(grp, "mean_wedge")
                if wmean(grp, "mean_wedge")
                else float("nan")
            ),
        )

    # ---- (b) does the print lag the commodity?
    lag = {}
    for label, sub in (("all", panel), ("CC_REGULAR", panel[panel["group"] == "CC_REGULAR"])):
        sub = sub.sort_values(["plant_id", "t"]).copy()
        sub["d_hub"] = sub.groupby("plant_id")["hub"].diff()
        sub["d_wedge"] = sub.groupby("plant_id")["wedge"].diff()
        ok = sub.dropna(subset=["d_hub", "d_wedge"])
        lag[label] = dict(
            n=int(len(ok)),
            corr_wedge_level_vs_hub_level=float(np.corrcoef(sub["wedge"], sub["hub"])[0, 1]),
            corr_dwedge_vs_dhub=float(np.corrcoef(ok["d_wedge"], ok["d_hub"])[0, 1]),
            # A pure one-month-lagged average print implies d_wedge = -d_hub exactly:
            # slope -1.  A real delivery cost implies slope ~0.
            slope_dwedge_on_dhub=float(
                np.polyfit(ok["d_hub"].to_numpy(float), ok["d_wedge"].to_numpy(float), 1)[0]
            ),
        )

    # ---- (c) regression-free asymptote: the plant's own top-burn-quartile months
    top = []
    for pid, grp in panel.groupby("plant_id"):
        if len(grp) < 8:
            continue
        cut = grp["burn"].quantile(0.75)
        hi = grp[grp["burn"] >= cut]
        top.append(
            dict(
                plant_id=int(pid),
                group=grp["group"].iloc[0],
                mw=float(grp["mw"].iloc[0]),
                v_topq=float((hi["wedge"] * hi["burn"]).sum() / hi["burn"].sum()),
            )
        )
    t = pd.DataFrame(top)
    joined = a.merge(t[["plant_id", "v_topq"]], on="plant_id", how="inner")

    out = dict(
        generated_by="scripts/probes/_miso225_wedge_anatomy_phase0.py",
        years=list(YEARS),
        a_fixed_leg=dict(
            n_plants=int(len(a)),
            mw=float(a["mw"].sum()),
            v_cap_wtd=wmean(a, "v"),
            fixed_leg_cap_wtd=wmean(a, "fixed_leg_usd_mmbtu"),
            mean_wedge_cap_wtd=wmean(a, "mean_wedge"),
            fixed_leg_p50=float(a["fixed_leg_usd_mmbtu"].median()),
            fixed_leg_p90=float(a["fixed_leg_usd_mmbtu"].quantile(0.90)),
            by_class=by_class,
        ),
        b_lag_test=lag,
        c_topquartile=dict(
            n_plants=int(len(joined)),
            v_topq_cap_wtd=wmean(joined, "v_topq"),
            v_regression_cap_wtd=wmean(joined, "v"),
            corr_two_estimators=float(np.corrcoef(joined["v"], joined["v_topq"])[0, 1]),
            by_class={
                str(g): dict(
                    mw=float(grp["mw"].sum()),
                    v_topq=wmean(grp, "v_topq"),
                    v_reg=wmean(grp, "v"),
                )
                for g, grp in joined.groupby("group")
            },
        ),
    )
    OUT.write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
