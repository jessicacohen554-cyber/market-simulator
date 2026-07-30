"""caiso-140 D1/D2 — the C3a-2025 belly residual, and the EXACT supply-state
ledger behind the ~2 GW import excess. NO LP, NO SOLVE — committed bytes only.

Charter: the caiso-140 session brief. caiso-138 §C measured the ~1 GW-mean
phantom northern firm import and explicitly declined to re-base it: shrinking
the forced cheap import raises CA lambda and fails E1 unless CA's own midday
supply state is fixed first. THAT prerequisite is this probe's object:
what is CA's midday supply actually missing, such that the LP must import
~2 GW more than the real market did to clear the belly?

Inputs (every one committed):

* the caiso-139 keeper's own ``hourly/`` sidecars
  (``results/calibration/caiso139_dumpguard_B``) — system, class_hourly,
  storage;
* the committed actual hourly RT LMP reference
  (``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``);
* the committed supply-consistent demand artifact
  (``data/raw/reference/caiso-supply-consistent-demand/``) — the keeper's OWN
  demand input, verified here to reproduce the sidecar demand to 4e-11 MW;
* the EIA-930 CISO hourly extract via the loader's own frame
  (:func:`market_sim.data.eia930.frames._eia_hourly_frame_filled`) — the same
  rows, same local clock, the demand artifact was derived from.

The load-bearing construction (§B): the keeper's demand input is BUILT from
measured supply — ``demand = NetGen − NG_cell + CEMS_gas + flats − TI`` — and
the model's own hourly balance closes on that same demand to <0.01 MW
(verified in §B0). Therefore, per hour,

    (model_import − measured_import) = Σ_fuel (measured_fuel − model_fuel)
                                       − (model_storage_net − measured_OTH)

EXACTLY, with no coverage gap: the import wedge decomposes one-for-one into
CA-side per-fuel supply-state wedges on the very series the demand rides.
This is the D2 attribution "to a SUPPLY state, not a price, with the import
wedge held fixed" — the wedge is the LHS; the RHS names who is short.

Sections:

* **A (D1)** — the 2025 C3a residual per (month × hod) on the rubric's rt_lw
  weights (caiso-131 §2's common-weight convention: cell contributions sum to
  the printed annual gap). 2023/2024 as controls.
* **B (D2)** — the exact ledger, annually and in the defect window (Sep–Dec,
  hod 10–15, measured RT ≤ $20 — the caiso-120/121 convention), per fuel.
* **C** — the biggest wedge component drilled one level down (gas by class
  against the bench CEMS hourly's own grid basis; storage by tech and side;
  hydro incl. PS-in-WAT like-for-like note).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso140_belly_supply_state.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso139_dumpguard_B"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
SCD_DIR = REPO / "data/raw/reference/caiso-supply-consistent-demand"

GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# model classes matched to each 930 fuel cell of the demand identity
OTHER_KLASSES = ("biomass", "OTHER", "oil", "COAL")

# caiso-120/121 defect-hour convention, reused verbatim for composability
DEFECT_MONTHS = (9, 10, 11, 12)
DEFECT_HODS = (10, 11, 12, 13, 14, 15)
DEFECT_RT_CAP = 20.0


# ---------------------------------------------------------------------------
# committed-artifact readers
# ---------------------------------------------------------------------------
def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT price ($/MWh), NaN where uncovered."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def sidecars(year: int) -> dict:
    """P1 pivots from the keeper's committed hourly sidecars."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    s = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    demand = d.pivot_table(index="hour", columns="zone", values="demand")
    return {
        "price": price,
        "demand": demand,
        "klass": c.pivot_table(index="hour", columns="klass", values="mw"),
        "chg": s.pivot_table(index="hour", columns="tech", values="charge_mw"),
        "dis": s.pivot_table(index="hour", columns="tech", values="discharge_mw"),
    }


def ca_lambda(sc: dict) -> np.ndarray:
    """Hourly CA demand-weighted model lambda (the C3a construction)."""
    ca = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
    p = (sc["price"][ca] * sc["demand"][ca]).sum(axis=1) / sc["demand"][ca].sum(axis=1)
    return p.to_numpy()


def rubric_weights(year: int) -> np.ndarray:
    """The rubric's rt_lw weights: measured system load (eia_loader)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def frame930(year: int) -> pd.DataFrame:
    """The CISO 930 hourly frame on the generation-frame local clock."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    f = _eia_hourly_frame_filled("CISO", year)
    assert f is not None and len(f) == HOURS
    return f.reset_index(drop=True)


def scd(year: int) -> pd.DataFrame:
    """The committed supply-consistent demand artifact (identity terms)."""
    return pd.read_csv(SCD_DIR / f"caiso_supply_consistent_demand_{year}.csv")


def flats(year: int) -> float:
    """The identity's flat adders (cogen + geo/biomass fold-in), MW."""
    prov = json.loads((SCD_DIR / "provenance.json").read_text())
    return float(prov["years"][str(year)]["flat_adders_mw"])


def month_of_hour(year: int) -> np.ndarray:
    """Month (1–12) per hour-of-year on the non-leap 8760 calendar."""
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def hod_of_hour() -> np.ndarray:
    return np.arange(HOURS) % 24


# ---------------------------------------------------------------------------
# §A — D1: the residual per (month × hod), rt_lw common weights
# ---------------------------------------------------------------------------
def section_a() -> dict:
    print("=" * 78)
    print("A (D1). C3a residual per (month x hod), rt_lw common weights")
    print("  cell = sum_cell w*(model-actual) / sum_year w  [$ /MWh of annual mean]")
    print("=" * 78)
    out = {}
    for year in YEARS:
        sc = sidecars(year)
        lam = ca_lambda(sc)
        a = actual_rt(year)
        w = rubric_weights(year)
        ok = ~np.isnan(a)
        mo, hd = month_of_hour(year), hod_of_hour()
        wsum = w[ok].sum()
        contrib = np.where(ok, w * (lam - np.where(ok, a, 0.0)), 0.0) / wsum
        gap = contrib.sum()
        print(f"\n  {year}: total weighted gap {gap:+.2f} $/MWh  (n={ok.sum()} h)")
        # month x hod-band table: belly 10-15, evening 17-21, overnight 0-6, rest
        bands = {
            "belly10-15": np.isin(hd, DEFECT_HODS),
            "eve17-21": np.isin(hd, (17, 18, 19, 20, 21)),
            "night0-6": np.isin(hd, (0, 1, 2, 3, 4, 5, 6)),
            "other": ~(
                np.isin(hd, DEFECT_HODS)
                | np.isin(hd, (17, 18, 19, 20, 21))
                | np.isin(hd, (0, 1, 2, 3, 4, 5, 6))
            ),
        }
        hdr = "".join(f"{b:>12}" for b in bands)
        print(f"    {'month':<6}{hdr}{'total':>12}")
        rows = {}
        for m in range(1, 13):
            mrow = []
            for b, mask in bands.items():
                mrow.append(float(contrib[(mo == m) & mask].sum()))
            tot = float(contrib[mo == m].sum())
            rows[m] = mrow + [tot]
            flag = " <-- " if m in DEFECT_MONTHS else ""
            print(
                f"    {m:<6}"
                + "".join(f"{v:+12.3f}" for v in mrow)
                + f"{tot:+12.3f}{flag}"
            )
        band_tot = {
            b: float(contrib[mask].sum()) for b, mask in bands.items()
        }
        print(
            f"    {'ALL':<6}"
            + "".join(f"{band_tot[b]:+12.3f}" for b in bands)
            + f"{gap:+12.3f}"
        )
        sepdec = float(contrib[np.isin(mo, DEFECT_MONTHS)].sum())
        sepdec_belly = float(
            contrib[np.isin(mo, DEFECT_MONTHS) & np.isin(hd, DEFECT_HODS)].sum()
        )
        print(
            f"    Sep-Dec total {sepdec:+.2f}  |  Sep-Dec belly(10-15) "
            f"{sepdec_belly:+.2f}  ({sepdec_belly / gap * 100 if gap else 0:.0f}% of gap)"
        )
        out[year] = {
            "gap": gap,
            "sepdec": sepdec,
            "sepdec_belly": sepdec_belly,
            "bands": band_tot,
        }
    return out


# ---------------------------------------------------------------------------
# §B — D2: the exact supply-state ledger
# ---------------------------------------------------------------------------
def ledger(year: int) -> pd.DataFrame:
    """Hourly per-component (model, measured) MW on the demand identity."""
    sc = sidecars(year)
    f = frame930(year)
    art = scd(year)
    kl = sc["klass"].reindex(range(HOURS)).fillna(0.0)
    chg = sc["chg"].reindex(range(HOURS)).fillna(0.0)
    dis = sc["dis"].reindex(range(HOURS)).fillna(0.0)

    def cell(name: str) -> np.ndarray:
        return (
            pd.to_numeric(f[name], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy()
        )

    out = pd.DataFrame({"hour": np.arange(HOURS)})
    # import: model = WECC tranche output (dump == 0 since caiso-139, sinks dead)
    out["imp_model"] = kl["import"].to_numpy()
    out["imp_meas"] = -cell("Total interchange")
    # gas: measured side is the identity's OWN gas term (CEMS grid + flat cogen)
    prov = json.loads((SCD_DIR / "provenance.json").read_text())
    cogen_flat = (
        float(prov["years"][str(year)]["gas_cogen_grid_twh"]) * 1e6 / HOURS
    )
    foldin_flat = (
        float(prov["years"][str(year)]["geo_biomass_foldin_twh"]) * 1e6 / HOURS
    )
    out["gas_model"] = kl[list(GAS_KLASSES)].sum(axis=1).to_numpy()
    out["gas_meas"] = art["cems_gas_grid_mw"].to_numpy() + cogen_flat
    # hydro incl PS net (930 WAT carries PS net output; like-for-like both sides)
    ps_net = (dis.get("pumped_storage", 0.0) - chg.get("pumped_storage", 0.0))
    ps_net = np.asarray(ps_net) if np.ndim(ps_net) else np.full(HOURS, 0.0)
    out["hyd_model"] = kl["hydro"].to_numpy() + ps_net
    out["hyd_meas"] = cell("NG: WAT")
    out["sun_model"] = kl["solar"].to_numpy()
    out["sun_meas"] = cell("NG: SUN")
    out["wnd_model"] = kl["wind"].to_numpy()
    out["wnd_meas"] = cell("NG: WND")
    out["nuc_model"] = kl["nuclear"].to_numpy()
    out["nuc_meas"] = cell("NG: NUC")
    # battery: 930 puts LESR net in OTH (with a small non-battery residual)
    bat_net = (dis.get("li_ion", 0.0) - chg.get("li_ion", 0.0))
    out["bat_model"] = np.asarray(bat_net)
    out["bat_meas"] = cell("NG: OTH")  # net battery + misc residual
    # other bundle, defined as the NetGen REMAINDER so the components are
    # disjoint and the ledger closes exactly: everything in the identity's
    # NetGen not already assigned above (GEO — 100 % NaN as a cell in
    # 2023/24 but inside NetGen — OIL, COL, biomass, misc) plus the flat
    # fold-in adder, vs the model's biomass/OTHER/oil/COAL.
    out["oth_meas"] = (
        art["netgen_mw"].to_numpy()
        - art["ng_cell_mw"].to_numpy()
        - out["nuc_meas"]
        - out["sun_meas"]
        - out["wnd_meas"]
        - out["hyd_meas"]
        - out["bat_meas"]
        + foldin_flat
    )
    out["oth_model"] = (
        kl[[k for k in OTHER_KLASSES if k in kl.columns]].sum(axis=1).to_numpy()
    )
    out["demand"] = art["demand_mw"].to_numpy()
    return out


def section_b(a_out: dict) -> dict:
    print("\n" + "=" * 78)
    print("B (D2). The EXACT ledger: import wedge == sum of CA-side supply wedges")
    print("  wedge = measured - model (MW mean over the hour set); import wedge")
    print("  = model - measured. Identity check printed per set.")
    print("=" * 78)
    out = {}
    for year in YEARS:
        led = ledger(year)
        a = actual_rt(year)
        mo, hd = month_of_hour(year), hod_of_hour()
        defect = (
            np.isin(mo, DEFECT_MONTHS)
            & np.isin(hd, DEFECT_HODS)
            & (np.nan_to_num(a, nan=1e9) <= DEFECT_RT_CAP)
        )
        belly_all = np.isin(mo, DEFECT_MONTHS) & np.isin(hd, DEFECT_HODS)
        sets = {
            "annual": np.ones(HOURS, bool),
            "SepDec belly(all)": belly_all,
            f"defect(RT<=${DEFECT_RT_CAP:.0f})": defect,
        }
        print(f"\n  {year}:")
        out[year] = {}
        for name, mask in sets.items():
            L = led[mask]
            imp_wedge = float((L["imp_model"] - L["imp_meas"]).mean())
            rows = {
                "gas": float((L["gas_meas"] - L["gas_model"]).mean()),
                "hydro+PS": float((L["hyd_meas"] - L["hyd_model"]).mean()),
                "solar": float((L["sun_meas"] - L["sun_model"]).mean()),
                "wind": float((L["wnd_meas"] - L["wnd_model"]).mean()),
                "nuclear": float((L["nuc_meas"] - L["nuc_model"]).mean()),
                "battery(OTH)": float((L["bat_meas"] - L["bat_model"]).mean()),
                "other": float((L["oth_meas"] - L["oth_model"]).mean()),
            }
            closure = imp_wedge - sum(rows.values())
            print(
                f"    {name:<22} n={int(mask.sum()):5d}  import wedge "
                f"{imp_wedge:+8.1f} MW"
            )
            for k, v in rows.items():
                share = v / imp_wedge * 100 if abs(imp_wedge) > 1 else float("nan")
                print(f"        {k:<14}{v:+9.1f} MW  ({share:5.1f}% of wedge)")
            print(f"        {'closure resid':<14}{closure:+9.1f} MW")
            out[year][name] = {"import_wedge": imp_wedge, **rows, "closure": closure}
    return out


# ---------------------------------------------------------------------------
# §C — drill-down of the dominant wedges
# ---------------------------------------------------------------------------
def section_c() -> None:
    print("\n" + "=" * 78)
    print("C. Drill-down: storage by tech/side, gas by class, hod profile of the")
    print("   dominant wedge components in Sep-Dec")
    print("=" * 78)
    for year in YEARS:
        sc = sidecars(year)
        led = ledger(year)
        mo, hd = month_of_hour(year), hod_of_hour()
        sepdec = np.isin(mo, DEFECT_MONTHS)
        kl = sc["klass"].reindex(range(HOURS)).fillna(0.0)
        chg = sc["chg"].reindex(range(HOURS)).fillna(0.0)
        dis = sc["dis"].reindex(range(HOURS)).fillna(0.0)
        print(f"\n  {year} Sep-Dec, mean MW by hod band:")
        bands = {
            "belly10-15": np.isin(hd, DEFECT_HODS),
            "eve17-21": np.isin(hd, (17, 18, 19, 20, 21)),
            "night0-6": np.isin(hd, (0, 1, 2, 3, 4, 5, 6)),
        }
        print(
            f"    {'component':<26}" + "".join(f"{b:>14}" for b in bands)
        )

        def prow(name: str, series: np.ndarray) -> None:
            vals = [float(series[sepdec & m].mean()) for m in bands.values()]
            print(f"    {name:<26}" + "".join(f"{v:+14.1f}" for v in vals))

        prow("battery wedge (meas-mod)", (led["bat_meas"] - led["bat_model"]).to_numpy())
        prow("  model li_ion chg", -chg["li_ion"].to_numpy())
        prow("  model li_ion dis", dis["li_ion"].to_numpy())
        prow("  meas OTH net", led["bat_meas"].to_numpy())
        prow("hydro+PS wedge", (led["hyd_meas"] - led["hyd_model"]).to_numpy())
        prow("  model hydro", kl["hydro"].to_numpy())
        prow("  model PS net", (dis["pumped_storage"] - chg["pumped_storage"]).to_numpy())
        prow("  meas WAT", led["hyd_meas"].to_numpy())
        prow("gas wedge", (led["gas_meas"] - led["gas_model"]).to_numpy())
        for k in GAS_KLASSES:
            prow(f"  model {k}", kl[k].to_numpy())
        prow("  meas CEMS+cogen", led["gas_meas"].to_numpy())
        prow("import wedge (mod-meas)", (led["imp_model"] - led["imp_meas"]).to_numpy())
        prow("solar wedge", (led["sun_meas"] - led["sun_model"]).to_numpy())


def main() -> int:
    a_out = section_a()
    section_b(a_out)
    section_c()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
