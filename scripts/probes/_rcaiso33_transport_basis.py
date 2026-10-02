"""R-CAISO-33 scoping probe: the CAISO citygate->burner-tip transport adder on its own base. ZERO LP.

Measures, from committed inputs only, every gauge of the transport term that
``CAISO_CITYGATE_TRANSPORT_ADDER`` (0.46 $/MMBtu) stands for, expressed on the
base the keeper actually rides on -- the NGI California Composite daily spot,
flow-dated (``caiso_citygate_flow_date``, ``caiso_citygate_spot_level``):

A. the EIA census gauge: N3045CA3 (CA delivered to electric power) minus the
   composite, by year (the R-CAISO-29 §1 reading) -- plus WHO is in that census
   (EIA-923 Schedule 2 cost reporting is utility-only), by balancing authority;
B. the plant gauge: each reporting CA gas plant's own EIA-923 delivered price
   minus the composite, per-plant medians, by model class, 2019-22 and 2023-25;
C. the bid gauge: the adder the fleet's own measured DAM bids imply over the
   composite, from the committed ``caiso_offer_curve_measured.json`` per-year
   band multipliers (identity: mult = 1 + a / (g + 0.057 P_CO2)), with a
   marginal-heat-rate sensitivity;
D. the consequence table: what a joint re-basis at each candidate adder does to
   the re-derived multipliers (approximate, annual-mean ratio) and to the gap
   between the ``committed`` tranche (1.0 x delivered) and the measured
   ``econ_low`` bid;
E. the channel census: keeper P1 energy by class and band (where the committed
   band carries weight).

Outputs ``docs/records/caiso/r-caiso-33/transport_basis.json`` and
``transport_basis.png``. Nothing here is a lever; it is the evidence table for
``PRECOMMIT-r-caiso-33-joint-gas-rebasis-2026-10-02.md``. Rule 34(e): every
input is committed; re-run time ~20 s.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    CAISO_CITYGATE_TRANSPORT_ADDER,
    STATE_CARBON_PRICE_BY_ISO,
)

OUT_DIR = REPO / "docs/records/caiso/r-caiso-33"
GAS = REPO / "data/raw/gas-prices"
LEGACY = REPO / "data/raw/_processed-legacy"
KEEPER = REPO / "results/calibration/rcaiso20_A_span"
MEASURED = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
MCF_TO_MMBTU = 1.037
CO2_FACTOR = 0.057
CLASS_HR = {"CC_REGULAR": 7.442, "CT_PEAKER": 10.862}
CANDIDATES = {
    "a=0.46 (keeper)": {y: CAISO_CITYGATE_TRANSPORT_ADDER for y in (2023, 2024, 2025)},
    "a=census per-year median": {2023: 1.20, 2024: 1.15, 2025: 1.28},
    "a=census pooled 2023-25": {y: 1.22 for y in (2023, 2024, 2025)},
}


def composite_monthly() -> pd.Series:
    """Flow-dated (trade+1, forward-filled) NGI CA composite, calendar-month mean."""
    c = pd.read_csv(GAS / "caiso_citygate_daily.csv", parse_dates=["date"]).sort_values(
        "date"
    )
    c["flow"] = c["date"] + pd.Timedelta(days=1)
    cal = pd.date_range(c["flow"].min(), "2026-06-30")
    s = c.set_index("flow")["ca_composite_usd_mmbtu"].reindex(cal).ffill()
    m = s.groupby([s.index.year, s.index.month]).mean()
    m.index = pd.MultiIndex.from_tuples(m.index, names=["year", "month"])
    return m.rename("comp")


def wmedian(v: np.ndarray, w: np.ndarray) -> float:
    """Weighted median."""
    o = np.argsort(v)
    cw = np.cumsum(w[o]) / w.sum()
    return float(v[o][np.searchsorted(cw, 0.5)])


def gauge_a(comp: pd.Series) -> tuple[dict, dict]:
    """EIA N3045CA3 minus composite by year, and the census' own composition."""
    d = pd.read_csv(
        GAS / "eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
    )
    d = d[d.state == "CA"].copy()
    d["n3045"] = d.price_usd_mcf / MCF_TO_MMBTU
    cg = pd.read_csv(GAS / "eia_citygate_CA_monthly.csv")
    cg["n3050"] = pd.to_numeric(cg.citygate_usd_per_mcf, errors="coerce") / MCF_TO_MMBTU
    d = d.merge(cg[["year", "month", "n3050"]], on=["year", "month"], how="left")
    d = d.join(comp, on=["year", "month"])
    d = d[d.year.between(2018, 2025)]
    d["gap"] = d.n3045 - d.comp
    by_year = {
        int(y): {
            "n3045": round(float(s.n3045.mean()), 3),
            "composite": round(float(s.comp.mean()), 3),
            "n3050": round(float(s.n3050.mean()), 3),
            "n3045_minus_composite_mean": round(float(s.gap.mean()), 3),
            "n3045_minus_composite_median": round(float(s.gap.median()), 3),
            "n3045_minus_n3050_mean": round(float((s.n3045 - s.n3050).mean()), 3),
            "n3050_minus_composite_mean": round(float((s.n3050 - s.comp).mean()), 3),
        }
        for y, s in d.groupby("year")
    }
    pooled = {
        "2023-25_median": round(float(d[d.year >= 2023].gap.median()), 3),
        "2023-25_mean": round(float(d[d.year >= 2023].gap.mean()), 3),
        "2019-22_median": round(float(d[d.year.between(2019, 2022)].gap.median()), 3),
    }
    # Who reports: EIA-923 Schedule 2 cost rows for CA gas, 2023-25.
    f = pd.read_parquet(LEGACY / "eia923_monthly_fuel_costs.parquet")
    f = f[
        (f.state == "CA") & (f.fuel_group == "Natural Gas") & f.year.between(2023, 2025)
    ]
    plants = pd.read_parquet(REPO / "data/raw/eia-860/eia860_plant.parquet")
    plants = plants.drop_duplicates("Plant Code").set_index("Plant Code")
    q = f.groupby("plant_id").quantity.sum()
    census = pd.DataFrame(
        {
            "share": (q / q.sum()).round(3),
            "name": q.index.map(plants["Plant Name"]),
            "utility": q.index.map(plants["Utility Name"]),
            "ba": q.index.map(plants["Balancing Authority Code"]),
        }
    ).sort_values("share", ascending=False)
    by_ba = census.groupby("ba").share.sum().round(3).to_dict()
    return (
        {"by_year": by_year, "pooled": pooled},
        {
            "n_plants": int(len(census)),
            "share_by_ba": by_ba,
            "share_in_CISO": round(float(by_ba.get("CISO", 0.0)), 3),
            "plants": [
                {
                    "plant_id": int(i),
                    **{k: (float(v) if k == "share" else str(v)) for k, v in r.items()},
                }
                for i, r in census.iterrows()
            ],
        },
    )


def gauge_b(comp: pd.Series) -> dict:
    """Per-plant EIA-923 delivered price minus composite, by model class."""
    f = pd.read_parquet(LEGACY / "eia923_monthly_fuel_costs.parquet")
    f = f[
        (f.state == "CA") & (f.fuel_group == "Natural Gas") & f.year.between(2019, 2025)
    ].copy()
    b = pd.read_csv(LEGACY / "bin_assignments_CAISO.csv")
    main_group = b.sort_values("Nameplate_MW", ascending=False).drop_duplicates(
        "Plant_Code"
    )
    f["cls"] = f.plant_id.map(main_group.set_index("Plant_Code").Plant_Group)
    f["mw"] = f.plant_id.map(b.groupby("Plant_Code").Nameplate_MW.sum())
    f["name"] = f.plant_id.map(main_group.set_index("Plant_Code").Plant_Name)
    f = f.join(comp, on=["year", "month"])
    f["gap"] = f.price_per_mmbtu - f.comp
    # caiso-242 §5 lesson: a cost reported on a sliver of normal volume is not a price.
    medq = f.groupby("plant_id").quantity.median()
    f = f[(f.quantity >= 0.2 * f.plant_id.map(medq)) & f.cls.notna()]
    out: dict = {"spans": {}, "by_year_class_burn_w_median": {}, "plants_2023_25": []}
    for span, yrs in (
        ("2023-25", [2023, 2024, 2025]),
        ("2019-22", [2019, 2020, 2021, 2022]),
    ):
        h = f[f.year.isin(yrs)]
        pp = (
            h.groupby(["plant_id", "cls"])
            .agg(
                gap_med=("gap", "median"),
                n=("gap", "size"),
                q=("quantity", "sum"),
                mw=("mw", "first"),
                name=("name", "first"),
            )
            .reset_index()
        )
        pp = pp[pp.n >= 6]
        rows = {}
        for cls, sub in list(pp.groupby("cls")) + [("ALL_BINNED", pp)]:
            v, w, wq = (
                sub.gap_med.to_numpy(float),
                sub.mw.to_numpy(float),
                sub.q.to_numpy(float),
            )
            rows[cls] = {
                "n_plants": int(len(sub)),
                "mw": int(w.sum()),
                "cap_w_median": round(wmedian(v, w), 2),
                "burn_w_median": round(wmedian(v, wq), 2),
                "burn_w_mean": round(float(np.average(v, weights=wq)), 2),
                "p10_p50_p90": [
                    round(float(np.percentile(v, p)), 2) for p in (10, 50, 90)
                ],
            }
        out["spans"][span] = rows
        if span == "2023-25":
            out["plants_2023_25"] = [
                {
                    "plant_id": int(r.plant_id),
                    "name": str(r.name),
                    "cls": r.cls,
                    "mw": float(r.mw),
                    "gap_median": round(float(r.gap_med), 2),
                    "months": int(r.n),
                }
                for r in pp.itertuples()
            ]
    for (y, cls), sub in f.groupby(["year", "cls"]):
        pp = sub.groupby("plant_id").agg(gm=("gap", "median"), q=("quantity", "sum"))
        out["by_year_class_burn_w_median"].setdefault(cls, {})[int(y)] = round(
            wmedian(pp.gm.to_numpy(float), pp.q.to_numpy(float)), 2
        )
    return out


def keeper_composite_annual() -> dict[int, float]:
    """Annual mean of the keeper's own flow-dated composite series (hubs.py)."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import hubs

    rc = json.loads((KEEPER / "run_config.json").read_text())
    sc = rc.get("scenario_config", rc)
    keys = {
        k: sc[k]
        for k in (
            "gas_hub_basis_overlay",
            "caiso_citygate_spot_level",
            "caiso_citygate_flow_date",
            "caiso_citygate_spot_coverage",
            "gas_flow_date_year_start_package",
            "caiso_citygate_blackout_bridge",
        )
    }
    out = {}
    for y in range(2019, 2026):
        cfg = ScenarioConfig(iso="CAISO", mode="backcast", hours=8760, **keys)
        h = hubs._caiso_hub_daily_gas_prices(
            cfg, y, spot_level=True, spot_coverage=True
        )
        out[y] = round(float(np.nanmean(h)), 3)
    return out


def gauge_c(g: dict[int, float]) -> tuple[dict, dict]:
    """Bid-implied adder over the composite, per class / band / year, and the consequence table."""
    m = json.loads(MEASURED.read_text())
    py = m["_provenance"]["per_year_band_mults"]
    pc = {y: float(STATE_CARBON_PRICE_BY_ISO["CAISO"][y]) for y in (2023, 2024, 2025)}
    implied: dict = {}
    for cls in CLASS_HR:
        for band in ("committed", "econ_low", "econ_high", "peak"):
            for y in (2023, 2024, 2025):
                mult = py[cls][band][str(y)]
                if mult is None or mult != mult:
                    continue
                cp = g[y] + CO2_FACTOR * pc[y]
                implied.setdefault(cls, {}).setdefault(band, {})[y] = {
                    "mult": mult,
                    "a_at_base_hr": round((mult - 1) * cp, 2),
                    "a_at_0.95_base_hr": round((mult / 0.95 - 1) * cp, 2),
                }
    consequences: dict = {}
    for label, a in CANDIDATES.items():
        row: dict = {}
        for cls, hr in CLASS_HR.items():
            bands = {}
            for band in ("econ_low", "econ_high", "peak"):
                bands[band] = {
                    "keeper_pooled": m[cls]["bands"][band],
                    "rebased_per_year_approx": {
                        y: round(
                            py[cls][band][str(y)]
                            * (g[y] + CO2_FACTOR * pc[y])
                            / (g[y] + a[y] + CO2_FACTOR * pc[y]),
                            3,
                        )
                        for y in (2023, 2024, 2025)
                    },
                }
            gap = {}
            for y in (2023, 2024, 2025):
                me = py[cls]["econ_low"][str(y)]
                cp = g[y] + CO2_FACTOR * pc[y]
                committed = hr * (g[y] + a[y] + CO2_FACTOR * pc[y])
                econ = me * hr * cp
                gap[y] = round(committed - econ, 1)
            row[cls] = {"bands": bands, "committed_minus_econ_low_usd_mwh": gap}
        consequences[label] = row
    return implied, consequences


def gauge_e() -> dict:
    """Keeper P1 energy (TWh) by gas class and band family."""
    out = {}
    for y in (2022, 2023, 2024, 2025):
        d = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{y}.parquet")
        d = d[
            (d["pass"] == "P1")
            & d.klass.isin(["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"])
        ].copy()
        d["fam"] = d.band.str.replace(r"econc\d+", "econ", regex=True).str.replace(
            r"peak\d*", "peak", regex=True
        )
        t = d.groupby(["klass", "fam"]).mw.sum().unstack(fill_value=0.0) / 1e6
        out[y] = {
            k: {c: round(float(v), 2) for c, v in r.items()} for k, r in t.iterrows()
        }
    return out


def figure(a_by_year: dict, b: dict, implied: dict, cons: dict, g: dict) -> None:
    """Two panels: the three gauges by year; the committed-vs-econ gap by candidate."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=130)
    yrs = list(range(2019, 2026))
    census = [a_by_year[y]["n3045_minus_composite_median"] for y in yrs]
    ax1.plot(
        yrs,
        census,
        "o-",
        color="#444",
        label="EIA N3045CA3 − composite (median of months; utility-only census, 35 % CISO)",
    )
    for cls, col in (("CC_REGULAR", "#1f77b4"), ("CT_PEAKER", "#d62728")):
        plant = b["by_year_class_burn_w_median"].get(cls, {})
        ax1.plot(
            [y for y in yrs if y in plant],
            [plant[y] for y in yrs if y in plant],
            "s--",
            color=col,
            alpha=0.6,
            label=f"EIA-923 plant gauge, {cls} ({4 if cls == 'CC_REGULAR' else 2} CISO utility plants)",
        )
        lo = [
            min(implied[cls][bd][y]["a_at_base_hr"] for bd in ("econ_low", "econ_high"))
            for y in (2023, 2024, 2025)
        ]
        hi = [
            max(
                implied[cls][bd][y]["a_at_0.95_base_hr"]
                for bd in ("econ_low", "econ_high")
            )
            for y in (2023, 2024, 2025)
        ]
        ax1.fill_between(
            [2023, 2024, 2025],
            lo,
            hi,
            color=col,
            alpha=0.25,
            label=f"bid-implied, {cls} econ bands (base HR … 0.95× base HR)",
        )
    ax1.axhline(0.46, color="k", ls=":", label="keeper adder 0.46")
    ax1.set_ylabel("$/MMBtu over the NGI CA composite")
    ax1.set_title("Transport over the composite: three measured gauges")
    ax1.legend(fontsize=6.5, loc="upper left")
    ax1.grid(alpha=0.3)
    labels = list(cons)
    x = np.arange(3)
    for i, (label, hatch) in enumerate(zip(labels, ("", "//", "..", "xx"))):
        for j, (cls, col) in enumerate(
            (("CC_REGULAR", "#1f77b4"), ("CT_PEAKER", "#d62728"))
        ):
            gap = [
                cons[label][cls]["committed_minus_econ_low_usd_mwh"][y]
                for y in (2023, 2024, 2025)
            ]
            ax2.bar(
                x + (i * 2 + j) * 0.13 - 0.33,
                gap,
                width=0.12,
                color=col,
                alpha=0.5 + 0.15 * i,
                hatch=hatch,
                label=f"{cls}, {label}",
            )
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["2023", "2024", "2025"])
    ax2.set_ylabel("$/MWh")
    ax2.set_title("committed (1.0 × delivered) − measured econ_low bid")
    ax2.legend(fontsize=6.5)
    ax2.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "transport_basis.png")


def main() -> None:
    """Run every gauge and write the JSON + figure."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    comp = composite_monthly()
    a, census = gauge_a(comp)
    b = gauge_b(comp)
    g = keeper_composite_annual()
    implied, cons = gauge_c(g)
    e = gauge_e()
    doc = {
        "probe": "scripts/probes/_rcaiso33_transport_basis.py",
        "keeper": "2026-09-30-caiso-r20-overnight (rcaiso20_A_span)",
        "keeper_adder": CAISO_CITYGATE_TRANSPORT_ADDER,
        "keeper_composite_annual_mean": g,
        "A_census_gauge": a,
        "A_census_composition_2023_25": census,
        "B_plant_gauge": b,
        "C_bid_implied_adder": implied,
        "D_consequences": cons,
        "E_keeper_p1_twh_by_class_band": e,
    }
    (OUT_DIR / "transport_basis.json").write_text(
        json.dumps(doc, indent=1, default=float) + "\n"
    )
    figure(a["by_year"], b, implied, cons, g)
    print(
        json.dumps(
            {
                "A": a,
                "census_share_by_ba": census["share_by_ba"],
                "B_2023_25": b["spans"]["2023-25"],
            },
            indent=1,
        )
    )
    print("wrote", OUT_DIR / "transport_basis.json", "and transport_basis.png")


if __name__ == "__main__":
    main()
