"""pjm-137 M1/M2/M3 (no LP): is the Dominion CT_PEAKER deficit reachable by ANY
zonal congestion mechanism? PJM's own binding-constraint record answers it.

`FINDING-pjm136` closed the flow-limit family by measurement (every internal PJM
link is *bound-but-priceless*) and bought the **loss** half of the measured
DOM-vs-AEP separation with a measured delivery-factor surface. It handed
forward the statement that the remaining 76-80 % of that separation is
**congestion**, which nothing in the model produces on that boundary, and named
the open question: *make an internal PJM constraint actually price, or prove it
can't.*

This probe asks PJM. Three measurements, no solve:

* **M1 — where the MODEL prices now.** The pjm-136 M1a dual-space census, re-run
  on the NEW keeper (`pjm136_lossurf_B`), whose loss surface changed the dual
  structure completely. Per model link, per year: how often the two zonal duals
  separate at all, the mean separation, and the same statistics on PJM's own
  zonal prices split into congestion (MCC) and loss (MLC). **The residual after
  the loss surface is the congestion deficit** the successor mechanism would
  have to produce.
* **M2 — what PJM says was binding.** PJM publishes the day-ahead market's own
  binding transmission constraints with their shadow prices
  (``da_marginal_value``; the intake is
  `scripts/data/fetch_pjm_binding_constraints.py`). Every binding constraint is
  classified as an **interface** (a named zonal-scale transfer interface — the
  only class an 8-zone reduction can express) or a **facility** (a specific
  monitored line/transformer, carrying its voltage rating in its name), and the
  congestion rent is attributed across that split, across voltage bands, and
  **inside the hours DOM actually separates from AEP-DAYTON**. Facilities are
  ranked by their rent *lift* in high-DOM-separation hours over their own
  baseline — so the constraint set driving Dominion's price surfaces from the
  data rather than from a hand-drawn substation map.
* **M3 — the CT reality check.** PJM's congestion record says *where*; CAMPD
  says *when the Dominion CT fleet actually ran*. The roster is taken from the
  committed benchmark payload — the exact plants the model's own fleet assigns
  to `PJM_Dominion` / `CT_PEAKER` — and then narrowed to those plants'
  `unitType == 'Combustion turbine'` units, the same filter the CT heat-rate
  derive applies, so the measurement and the class it explains cover the same
  machines rather than a mixed plant's combined-cycle blocks. Their CAMPD
  hourly generation is weighted
  against the measured DOM LMP, the measured DOM congestion component, and the
  model's own Dominion dual in the same hours. This decides whether the CT leg
  is a **congestion-tail** phenomenon a zonal mechanism could reach, or
  something else entirely.

Nothing is written outside `results/probes/`. Measured sources are the pjm-136
zonal LMP-component intake, the pjm-137 binding-constraint intake, the committed
CAMPD unit-level record, and the committed keeper `hourly/` sidecars.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm137_dominion_ct_congestion.py
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm137_dominion_ct_congestion.py \
        --bundle results/calibration/pjm136_lossurf_B
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.zonal_shares import _PJM_LOAD_ZONE_GROUPS

YEARS = (2023, 2024, 2025)
HOURS = 8760

ZONAL_LMP_DIR = RAW_DATA_DIR / "pjm-zonal-lmp"
BINDING_DIR = RAW_DATA_DIR / "pjm-binding-constraints"
CAMPD_DIR = RAW_DATA_DIR / "campd-unit-level"
OUT_PATH = Path("results/probes/pjm137_dominion_ct_congestion.json")

#: CAMPD state extracts searched for the Dominion CT roster. VA and NC are the
#: two states `zone_assignment._PJM_STATE_ZONES` maps to `PJM_Dominion`, but the
#: roster itself is taken from the committed benchmark (below), NOT from the
#: state list: most of NC's CAMPD combustion turbines are Duke Energy Carolinas
#: / Progress units that are not in PJM at all, and sweeping the state whole
#: would put ~8 TWh of non-PJM generation into a PJM class statistic.
DOMINION_STATES = ("VA", "NC")

#: The committed per-run benchmark payload, which carries each CAMPD plant with
#: the model zone and class the fleet actually assigns it. Reading the roster
#: from here means M3 measures the SAME plants the model's `PJM_Dominion`
#: `CT_PEAKER` class contains — no hand-drawn plant list, and no state sweep.
BENCH_DIR = Path("frontend/data/backcast/bench/PJM")

LMP_PNODE_TO_LOAD_ZONE: dict[str, str] = {
    "AECO": "AE",
    "AEP": "AEP",
    "APS": "AP",
    "ATSI": "ATSI",
    "BGE": "BC",
    "COMED": "CE",
    "DAY": "DAY",
    "DEOK": "DEOK",
    "DOM": "DOM",
    "DPL": "DPL",
    "DUQ": "DUQ",
    "EKPC": "EKPC",
    "JCPL": "JC",
    "METED": "ME",
    "OVEC": "OVEC",
    "PECO": "PE",
    "PENELEC": "PN",
    "PEPCO": "PEP",
    "PPL": "PL",
    "PSEG": "PS",
    "RECO": "RECO",
}
NON_ZONE_PNODES = ("PJM-RTO", "MID-ATL/APS")

MODEL_ZONES = (
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)

MODEL_LINKS = (
    ("PJM_ComEd", "PJM_AEP_Ohio"),
    ("PJM_AEP_Ohio", "PJM_ATSI"),
    ("PJM_AEP_Ohio", "PJM_Dominion"),
    ("PJM_AEP_Ohio", "PJM_West_APS"),
    ("PJM_ATSI", "PJM_Central_PA"),
    ("PJM_West_APS", "PJM_Central_PA"),
    ("PJM_West_APS", "PJM_SWMAAC"),
    ("PJM_West_APS", "PJM_Dominion"),
    ("PJM_Central_PA", "PJM_EMAAC"),
    ("PJM_SWMAAC", "PJM_EMAAC"),
    ("PJM_SWMAAC", "PJM_Dominion"),
)

#: Below this a dual difference is HiGHS noise, not congestion.
EPS = 1e-6
#: The materiality threshold the pjm-134/135/136 lineage quotes.
MATERIAL = 1.0

_MONTH_START_HOUR = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def _hour_of_year(ts: pd.Series) -> np.ndarray:
    """Non-leap hour-of-year index for naive local timestamps (Feb 29 removed)."""
    return (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


# --------------------------------------------------------------------------
# model side
# --------------------------------------------------------------------------
def _model_duals(bundle: Path, year: int) -> pd.DataFrame:
    """Keeper P1 hourly zonal duals, hour-of-year index x model zone."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="price")


# --------------------------------------------------------------------------
# measured zonal LMP components
# --------------------------------------------------------------------------
def _metered_load(year: int) -> pd.DataFrame:
    """Metered PJM zonal load (MW), hour-of-year index x load-zone code."""
    path = RAW_DATA_DIR / "zone-specific-demand" / f"PJM{year}_hrl_load_metered.csv"
    frame = pd.read_csv(path, usecols=["datetime_beginning_ept", "zone", "mw"])
    ept = pd.to_datetime(frame["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    frame = frame[keep].copy()
    frame["hour"] = _hour_of_year(ept[keep])
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    return frame.pivot_table(index="hour", columns="zone", values="mw", aggfunc="mean")


def _measured_components(year: int) -> dict[str, pd.DataFrame]:
    """Load-weighted measured DA components per MODEL zone, hour-of-year index."""
    files = sorted(ZONAL_LMP_DIR.glob(f"da_hrl_lmps_{year}_*.parquet"))
    if not files:
        raise SystemExit(
            f"no measured zonal LMP parquet for {year} — run "
            "scripts/data/fetch_pjm_zonal_lmp_components.py first"
        )
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw = raw[~raw["pnode_name"].isin(NON_ZONE_PNODES)].copy()

    ept = pd.to_datetime(raw["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    raw = raw[keep].copy()
    raw["hour"] = _hour_of_year(ept[keep])
    raw["load_zone"] = raw["pnode_name"].map(LMP_PNODE_TO_LOAD_ZONE)
    raw["model_zone"] = raw["load_zone"].map(_PJM_LOAD_ZONE_GROUPS)
    raw = raw[raw["model_zone"].notna()].copy()

    load = _metered_load(year)
    weights = load.stack().rename("mw").reset_index()
    weights.columns = ["hour", "load_zone", "mw"]
    raw = raw.merge(weights, on=["hour", "load_zone"], how="left")
    raw["mw"] = raw["mw"].fillna(raw["mw"].median())

    out: dict[str, pd.DataFrame] = {}
    for key, col in (
        ("lmp", "total_lmp_da"),
        ("mcc", "congestion_price_da"),
        ("mlc", "marginal_loss_price_da"),
        ("mec", "system_energy_price_da"),
    ):
        raw["_wv"] = raw[col] * raw["mw"]
        num = raw.pivot_table(
            index="hour", columns="model_zone", values="_wv", aggfunc="sum"
        )
        den = raw.pivot_table(
            index="hour", columns="model_zone", values="mw", aggfunc="sum"
        )
        out[key] = (num / den).reindex(range(HOURS))
    return out


# --------------------------------------------------------------------------
# M1 — the dual-structure census on the NEW keeper
# --------------------------------------------------------------------------
def measure_m1(bundle: Path) -> dict:
    """Model vs measured separation per internal link, on the new keeper."""
    per_year: dict[str, dict] = {}
    for year in YEARS:
        duals = _model_duals(bundle, year)
        comp = _measured_components(year)
        rows = []
        for a, b in MODEL_LINKS:
            md = (duals[a] - duals[b]).to_numpy()
            xl = (comp["lmp"][a] - comp["lmp"][b]).to_numpy()
            xc = (comp["mcc"][a] - comp["mcc"][b]).to_numpy()
            xm = (comp["mlc"][a] - comp["mlc"][b]).to_numpy()
            ok = np.isfinite(xl)
            rows.append(
                {
                    "link": f"{a}->{b}",
                    "model_sep_share_pct": float(np.mean(np.abs(md) > EPS) * 100),
                    "model_material_share_pct": float(
                        np.mean(np.abs(md) > MATERIAL) * 100
                    ),
                    "model_mean_delta": float(np.mean(md)),
                    "model_mean_abs_delta": float(np.mean(np.abs(md))),
                    "meas_sep_share_pct": float(
                        np.mean(np.abs(xl[ok]) > EPS) * 100
                    ),
                    "meas_material_share_pct": float(
                        np.mean(np.abs(xl[ok]) > MATERIAL) * 100
                    ),
                    "meas_mean_delta": float(np.mean(xl[ok])),
                    "meas_mean_congestion": float(np.mean(xc[ok])),
                    "meas_mean_loss": float(np.mean(xm[ok])),
                    # what the loss surface bought, and what is left
                    "model_over_loss_ratio": (
                        float(np.mean(md) / np.mean(xm[ok]))
                        if abs(np.mean(xm[ok])) > 1e-9
                        else None
                    ),
                    "congestion_residual": float(np.mean(xc[ok])),
                }
            )
        # copper-plate statistic
        arr = duals[list(MODEL_ZONES)].to_numpy()
        spread = arr.max(axis=1) - arr.min(axis=1)
        per_year[str(year)] = {
            "links": rows,
            "all_eight_one_dual_pct": float(np.mean(spread <= EPS) * 100),
            "mean_max_zonal_spread": float(np.mean(spread)),
        }
    return per_year


# --------------------------------------------------------------------------
# M2 — PJM's own binding constraints
# --------------------------------------------------------------------------
def _binding(year: int) -> pd.DataFrame:
    """One year of PJM DA binding constraints with parsed voltage + UTC hour."""
    files = sorted(BINDING_DIR.glob(f"da_marginal_value_{year}_*.parquet"))
    if not files:
        raise SystemExit(
            f"no binding-constraint parquet for {year} — run "
            "scripts/data/fetch_pjm_binding_constraints.py first"
        )
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    ept = pd.to_datetime(d["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    d = d[keep].copy()
    d["hour"] = _hour_of_year(ept[keep])
    d["abs_sp"] = d["shadow_price"].abs()
    # PJM names a monitored FACILITY with its voltage rating ("... 230 KV");
    # a zonal-scale transfer INTERFACE carries no voltage (AEP-DOM, APSOUTH,
    # BED-BLA, WEST, EAST, CENTRAL). That is the split a zonal reduction cares
    # about, and it is read off PJM's own naming, not assigned by hand.
    d["kv"] = (
        d["monitored_facility"].str.extract(r"(\d+)\s*KV", flags=re.I)[0].astype(float)
    )
    d["is_interface"] = d["kv"].isna()
    d["base"] = d["monitored_facility"].str.split(" contingency").str[0].str.strip()
    return d


def measure_m2() -> dict:
    """Binding-constraint anatomy, overall and inside high-DOM-separation hours."""
    per_year: dict[str, dict] = {}
    lift_pool: list[pd.DataFrame] = []
    for year in YEARS:
        d = _binding(year)
        comp = _measured_components(year)
        tot = d["abs_sp"].sum()

        bands = pd.cut(
            d["kv"],
            [0, 100, 140, 240, 400, 600, 1000],
            labels=["<=100kV", "115-138kV", "230kV", "345kV", "500kV", "765kV"],
        )
        band_rent = (
            d.groupby(bands, observed=True)["abs_sp"].sum() / tot * 100
        ).round(3)

        # the DOM-vs-AEP separation this lineage is chartered on
        dom_mcc = (comp["mcc"]["PJM_Dominion"] - comp["mcc"]["PJM_AEP_Ohio"]).reindex(
            range(HOURS)
        )
        thresh = float(dom_mcc.quantile(0.90))
        hot = set(np.flatnonzero((dom_mcc >= thresh).to_numpy()))
        hot_rows = d[d["hour"].isin(hot)]
        hot_tot = hot_rows["abs_sp"].sum()

        # per-facility rent LIFT inside the hot hours vs its own baseline share
        base_share = d.groupby("base")["abs_sp"].sum() / tot
        hot_share = hot_rows.groupby("base")["abs_sp"].sum() / hot_tot
        lift = pd.concat(
            {"base_share": base_share, "hot_share": hot_share}, axis=1
        ).fillna(0.0)
        lift["lift_pp"] = (lift["hot_share"] - lift["base_share"]) * 100
        lift["year"] = year
        lift_pool.append(lift.reset_index())

        top_hot = (
            lift.sort_values("hot_share", ascending=False)
            .head(12)
            .assign(
                hot_share_pct=lambda f: (f["hot_share"] * 100).round(3),
                base_share_pct=lambda f: (f["base_share"] * 100).round(3),
            )[["hot_share_pct", "base_share_pct", "lift_pp"]]
            .round(3)
        )

        iface = d[d["is_interface"]]
        named = ("AEP-DOM", "APSOUTH", "BED-BLA", "WEST", "EAST", "CENTRAL", "BCPEP")
        named_rent = {
            n: float(d.loc[d["base"] == n, "abs_sp"].sum() / tot * 100) for n in named
        }

        per_year[str(year)] = {
            "rows": int(len(d)),
            "distinct_facilities": int(d["monitored_facility"].nunique()),
            "total_abs_shadow": float(tot),
            "interface_rent_pct": float(iface["abs_sp"].sum() / tot * 100),
            "interface_rows_pct": float(d["is_interface"].mean() * 100),
            "rent_pct_by_voltage_band": {
                str(k): float(v) for k, v in band_rent.items()
            },
            "rent_pct_at_or_below_230kV": float(
                d.loc[d["kv"] <= 240, "abs_sp"].sum() / tot * 100
            ),
            "named_interface_rent_pct": named_rent,
            "dom_hot_hour_threshold_mcc": thresh,
            "hot_hours": int(len(hot)),
            "hot_interface_rent_pct": float(
                hot_rows.loc[hot_rows["is_interface"], "abs_sp"].sum() / hot_tot * 100
            ),
            "hot_rent_pct_at_or_below_230kV": float(
                hot_rows.loc[hot_rows["kv"] <= 240, "abs_sp"].sum() / hot_tot * 100
            ),
            "hot_top_constraints": json.loads(top_hot.to_json(orient="index")),
        }

    pooled = pd.concat(lift_pool, ignore_index=True)
    agg = (
        pooled.groupby("base")
        .agg(
            hot_share_pct=("hot_share", lambda s: float(np.mean(s) * 100)),
            base_share_pct=("base_share", lambda s: float(np.mean(s) * 100)),
            years=("year", "size"),
        )
        .assign(lift_pp=lambda f: f["hot_share_pct"] - f["base_share_pct"])
        .sort_values("hot_share_pct", ascending=False)
        .head(20)
        .round(4)
    )
    return {
        "per_year": per_year,
        "pooled_top_hot_constraints": json.loads(agg.to_json(orient="index")),
    }


# --------------------------------------------------------------------------
# M3 — the Dominion CT reality check
# --------------------------------------------------------------------------
def _bench_dominion_ct_roster(year: int) -> set[int]:
    """ORIS codes the model's own fleet puts in `PJM_Dominion` / `CT_PEAKER`.

    Read from the committed benchmark payload, whose per-plant records carry
    the zone and class the fleet loader assigned. A plant split across classes
    is keyed ``"<oris>:<CLASS>"``, so only the leading ORIS code is taken.
    """
    path = BENCH_DIR / f"{year}.json.gz"
    with gzip.open(path, "rt") as handle:
        bench = json.load(handle)
    roster: set[int] = set()
    for code, rec in bench["bench"]["plants"].items():
        if rec.get("zone") == "PJM_Dominion" and rec.get("group") == "CT_PEAKER":
            roster.add(int(str(code).split(":")[0]))
    return roster


def _dominion_ct_hourly(year: int) -> tuple[np.ndarray, dict]:
    """Hourly Dominion CT_PEAKER fleet output (MW) from CAMPD, plus fleet meta."""
    roster = _bench_dominion_ct_roster(year)
    frames = []
    for state in DOMINION_STATES:
        path = CAMPD_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        frames.append(
            pd.read_parquet(
                path,
                columns=[
                    "facilityName",
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                    "primaryFuelInfo",
                    "unitType",
                ],
            )
        )
    d = pd.concat(frames, ignore_index=True)
    d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
    # The roster selects the PLANTS; `unitType` selects the MACHINES. Both are
    # required: several roster plants are MIXED, and taking a plant whole would
    # count its combined-cycle blocks as peaker output. Doswell Energy Center is
    # the case — the model fleet splits it into 6 CC_REGULAR + 3 CT_PEAKER
    # generators, and its CC blocks alone ran 4.47 TWh in 2025 against 1.08 TWh
    # from its turbines. This is the same filter
    # `scripts/data/derive_campd_ct_heat_rates.py` applies, so the class
    # measured here and the class the derive prices are the same machines.
    unit_type = d["unitType"].fillna("")
    is_ct = unit_type.str.contains(
        "combustion turbine", case=False, regex=False
    ) & ~unit_type.str.contains("combined cycle", case=False, regex=False)
    ct = d[d["facilityId"].isin(roster) & is_ct].copy()

    dt = pd.to_datetime(ct["date"])
    keep = ~((dt.dt.month == 2) & (dt.dt.day == 29))
    ct = ct[keep].copy()
    ct["hoy"] = (
        _MONTH_START_HOUR[dt[keep].dt.month.to_numpy() - 1]
        + (dt[keep].dt.day.to_numpy() - 1) * 24
        + ct["hour"].to_numpy()
    )
    ct["grossLoad"] = pd.to_numeric(ct["grossLoad"], errors="coerce").fillna(0.0)
    series = ct.groupby("hoy")["grossLoad"].sum().reindex(range(HOURS), fill_value=0.0)
    meta = {
        "roster_plants": len(roster),
        "units": int(ct.groupby(["facilityId", "unitId"]).ngroups),
        "facilities": int(ct["facilityId"].nunique()),
        "twh": float(series.sum() / 1e6),
        "fleet_max_mw": float(series.max()),
        "hours_running_pct": float((series > 0).mean() * 100),
    }
    return series.to_numpy(), meta


def measure_m3(bundle: Path) -> dict:
    """When Dominion's real CTs ran, what PJM charged, and what the model priced."""
    per_year: dict[str, dict] = {}
    for year in YEARS:
        ct, meta = _dominion_ct_hourly(year)
        comp = _measured_components(year)
        duals = _model_duals(bundle, year)

        lmp = comp["lmp"]["PJM_Dominion"].to_numpy()
        mcc = comp["mcc"]["PJM_Dominion"].to_numpy()
        mec = comp["mec"]["PJM_Dominion"].to_numpy()
        dom_aep_mcc = (
            comp["mcc"]["PJM_Dominion"] - comp["mcc"]["PJM_AEP_Ohio"]
        ).to_numpy()
        model_dom = duals["PJM_Dominion"].to_numpy()

        ok = np.isfinite(lmp) & np.isfinite(model_dom)
        w = np.where(ok, ct, 0.0)
        wsum = w.sum()

        def _wq(x: np.ndarray, qs=(0.1, 0.25, 0.5, 0.75, 0.9)) -> dict:
            """CT-energy-weighted quantiles of x."""
            m = ok & np.isfinite(x)
            order = np.argsort(x[m])
            xv, wv = x[m][order], w[m][order]
            c = np.cumsum(wv) / wv.sum()
            return {
                f"p{int(q * 100)}": float(np.interp(q, c, xv)) for q in qs
            }

        # what share of real CT energy is produced in hours PJM prices Dominion
        # congestion at all, and in hours it is material
        share_mcc_material = float(w[ok][np.abs(mcc[ok]) > 5.0].sum() / wsum * 100)
        share_mcc_tiny = float(w[ok][np.abs(mcc[ok]) <= 1.0].sum() / wsum * 100)

        per_year[str(year)] = {
            "fleet": meta,
            "ct_energy_weighted_measured_dom_lmp": _wq(lmp),
            "ct_energy_weighted_measured_dom_mcc": _wq(mcc),
            "ct_energy_weighted_measured_dom_mec": _wq(mec),
            "ct_energy_weighted_measured_dom_minus_aep_mcc": _wq(dom_aep_mcc),
            "ct_energy_weighted_model_dominion_dual": _wq(model_dom),
            "mean_measured_dom_lmp_ct_weighted": float(
                np.sum(w[ok] * lmp[ok]) / wsum
            ),
            "mean_model_dominion_dual_ct_weighted": float(
                np.sum(w[ok] * model_dom[ok]) / wsum
            ),
            "mean_measured_dom_mcc_ct_weighted": float(np.sum(w[ok] * mcc[ok]) / wsum),
            "pct_ct_energy_with_dom_mcc_gt_5": share_mcc_material,
            "pct_ct_energy_with_abs_dom_mcc_le_1": share_mcc_tiny,
            "mean_measured_dom_lmp_all_hours": float(np.nanmean(lmp)),
            "mean_model_dominion_dual_all_hours": float(np.mean(model_dom)),
            # diurnal shape of the real CT fleet
            "ct_diurnal_mw": [
                float(ct[np.arange(HOURS) % 24 == h].mean()) for h in range(24)
            ],
        }
    return per_year


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=Path("results/calibration/pjm136_lossurf_B"),
        help="calibration bundle whose hourly/ sidecars supply the model duals",
    )
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    print(f"M1  dual-structure census on {args.bundle} …", flush=True)
    m1 = measure_m1(args.bundle)
    print("M2  PJM binding-constraint anatomy …", flush=True)
    m2 = measure_m2()
    print("M3  Dominion CT reality check (CAMPD) …", flush=True)
    m3 = measure_m3(args.bundle)

    payload = {
        "bundle": str(args.bundle),
        "years": list(YEARS),
        "M1_model_vs_measured_separation": m1,
        "M2_pjm_binding_constraints": m2,
        "M3_dominion_ct_reality": m3,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
