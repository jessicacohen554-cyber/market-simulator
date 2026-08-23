"""miso-178 — C3a-2025 anatomy: where the -11.75% lives (READ-ONLY, no LP solved).

The owner re-opened the MISO summer-scarcity lane 2026-08-18 (matrix section 5.4);
the keeper `2026-08-22-miso-177-rho-measured` is NOT-YET on C3a-2025 ALONE
(-11.75%; 2023 +1.28%, 2024 -4.06%, band +/-10%). This instrument measures WHERE
the annual miss lives on THIS keeper -- zonally, by hour bucket, by month, by
DA-foreseen vs RT-only reach, and against the two honest counterfactual ceilings
-- so the successor lever plan is bounded by measurement, not hope. Everything
here is a MEASUREMENT of committed artifacts against measured actuals; nothing is
fed back into a solve (rule 13 [R-MEASURED]). Years 2023-2025 only (rule 22
[R-HOLDOUT]). No LP, nothing armed, no cell verdict minted, no registration
(rule 15 not engaged -- the miso-167/171/174/176 no-LP precedent).

Sources, all committed:
  model P1 zonal price/demand        results/calibration/miso177_rho_B/hourly/system_<y>.parquet
  model P1 class dispatch            .../class_hourly_<y>.parquet
  model P1 reserve family duals      .../reserve_family_<y>.parquet   (via the miso-167 re-run)
  resolved keeper config             results/calibration/miso177_rho_B/run_config.json
  measured RT/DA hourly LMP (system) data/raw/_validation-source/actual_lmp_hourly_MISO.parquet
  measured RT/DA hourly LMP (zonal)  data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet
  scored benchmark (rt_lw etc.)      frontend/data/backcast/bench/MISO/<y>.json.gz
  measured demand/interchange (930)  data/raw/MISO_region.parquet
  measured wind/solar gen (930)      data/raw/MISO_fueltype.parquet
  ASM MCP / cleared MW               data/raw/MISO-AS/*.parquet       (via the miso-167 re-run)

Stages (record keys per year):
  footing   -- reproduce the registered C3a to <=0.01 pp (HARD GATE, SystemExit on
               miss; miso-151 section-2 reproduce-before-extend precedent) + the
               named residual components (coverage hour, bench 2-dp quantization)
               + the resolved-config flag table for the override-carried fields
  zonal     -- per-zone lw model-actual vs the zonal validation series (annual +
               monthly), MISO-Plains via the documented MINN+ILLINOIS hub-mean
               proxy (scripts/report_miso_zonal_gates.py), and the benchmark-basis
               wedge: zone-resolved actual lw vs the scored Indiana-hub lw
  buckets   -- additive pp-of-C3a decomposition over {actual rt>$200 tail;
               top-decile actual net-load ex-tail; remainder} + a per-family
               model-vs-930 generation guard table inside the tail hours
  seasonal  -- monthly additive pp + own-month miss vs bench rt_lw_mon; May vs
               Jun+Jul (body vs tail) vs rest rollups
  foreseen  -- (i) the whole-gap two-term split G = sum w(Pm-DA) + sum w(DA-RT)
               [deterministic-reachable vs RT-only wedge], annual/monthly/bucket;
               (ii) the 88-hour tail split at the miso-167 DA>$150 line;
               (iii) the FULL miso-167 instrument re-run at this bundle
               (record key m167_repoint); (iv) the miso-171 scarce-set continuity
               assertion (top-47-by-load bit-identity vs miso170_layup_B2)
  ceilings  -- C3a with the tail priced at actual RT (the honest ceiling of ANY
               scarcity-only lever) and C3a with the model priced at actual DA
               everywhere (the deterministic-model ceiling)

Sign convention: pp values are contributions to (model - actual)/bench in
percentage points -- NEGATIVE means the model is UNDER-priced there. Bucket and
monthly pp sum to the reproduced C3a minus a named residual reported alongside.

Hour keys: model chronological non-leap 8760 CST calendar throughout. EIA-930 is
UTC-stamped -> CST = UTC-6h, Feb 29 dropped, hour keyed FROM THE TIMESTAMP
(MONTH_START[m-1] + (day-1)*24 + hh) and reindexed -- NOT positionally: the raw
2024 extract is missing all of Jun 1 (hours 4344-4367) and positional keying
(the reused miso-167 loader's construction) would shift Jul-Dec 2024 by 24 h.
The miso-167 re-run inherits that instrument's own conventions untouched
(continuity over harmonization): its e930 join carries the positional key
(affects only its stage-2 2024 D/TI columns, disclosed) and its ASM alignment
is the -2h construction, not the production loader's EST key -- levels are
key-sensitive, product shares are not (miso-171 section-5 robustness).

Run:
  cd <repo root> && uv run --no-project \
    --with pyarrow,pandas,numpy,pydantic,scipy --python 3.12 \
    python scripts/probes/_miso178_c3a2025_anatomy.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "probes"))

BUNDLE = ROOT / "results" / "calibration" / "miso177_rho_B"
OUT = ROOT / "results" / "calibration" / "_miso178_c3a2025_anatomy.json"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
ZONAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_zonal_MISO.parquet"
REGION = ROOT / "data" / "raw" / "MISO_region.parquet"
FUELTYPE = ROOT / "data" / "raw" / "MISO_fueltype.parquet"
BENCH_DIR = ROOT / "frontend" / "data" / "backcast" / "bench" / "MISO"

YEARS = (2023, 2024, 2025)
HOURS = 8760

# RESULT-miso177-rho-measured-execution-2026-08-22.md (r6/scorer basis).
REGISTERED_C3A_PCT = {2023: 1.279, 2024: -4.056, 2025: -11.747}
FOOTING_TOL_PP = 0.01

# Same objects as actual_tail.json rt_gt / C3c's TAIL_THRESHOLD["MISO"] and the
# miso-167 FORESEEN_DA line -- reused unchanged, never re-derived here.
TAIL_RT = 200.0
FORESEEN_DA = 150.0

MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30

CARRY_ZONES = ("MISO-East", "MISO-Illinois", "MISO-Indiana",
               "MISO-Plains", "MISO-South", "MISO-West")
# MISO-Plains has no trading hub; documented proxy = MINN+ILLINOIS hub mean
# (scripts/report_miso_zonal_gates.py, scripts/data/derive_miso_hub_lmp.py).
PLAINS_PROXY_HUBS = ("MINN.HUB", "ILLINOIS.HUB")

# Resolved-config fields whose top-level calibration_flags entry is misleading
# (override-carried); ground truth is run_config.json:scenario_config.
CONFIG_FLAGS = (
    "miso_reserve_online_gated", "miso_measured_reserve_requirements",
    "miso_midwest_subregional_reserves", "miso_zonal_reserves",
    "miso_seam_envelope_merit_cap", "miso_seam_envelope_hour_ending_key",
    "miso_seam_flow_limit", "miso_seam_export_limit", "miso_seam_measured_ladder",
    "miso_pjm_border_anchor", "miso_manitoba_seam", "miso_firm_imports",
    "miso_south_seam_split", "miso_rdt_tcdc", "miso_rpe_pricing",
    "maxgen_emergency_tier_pricing", "unit_outage_maxgen_events",
    "miso_winter_citygate_daily", "miso_zonal_gas_basis",
)

MODEL_FAMILY = {
    "coal": ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB"),
    "gas": ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS"),
    "nuclear": ("nuclear",),
    "wind": ("wind",),
    "solar": ("solar",),
    "hydro": ("hydro",),
}
E930_FAMILY = {"coal": "COL", "gas": "NG", "nuclear": "NUC",
               "wind": "WND", "solar": "SUN", "hydro": "WAT"}


def month_of(hour: np.ndarray) -> np.ndarray:
    """1-12 month index for each hour-of-year on the fixed non-leap calendar."""
    return np.searchsorted(np.array(MONTH_START[1:]), hour, side="right") + 1


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def sidecar(year: int) -> dict:
    """Model P1 series from the keeper bundle: hourly W, dw price, per-zone."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    carry = d[d["zone"].isin(CARRY_ZONES)]
    pw = carry.assign(pw=carry["price"] * carry["demand"]).groupby("hour")[["pw"]].sum()
    W = carry.groupby("hour")["demand"].sum().reindex(range(HOURS))
    Pm = (pw["pw"] / W).reindex(range(HOURS))
    zprice = carry.pivot_table(index="hour", columns="zone", values="price").reindex(range(HOURS))
    zdem = carry.pivot_table(index="hour", columns="zone", values="demand").reindex(range(HOURS))
    return {"W": W.to_numpy(float), "Pm": Pm.to_numpy(float),
            "zprice": zprice, "zdem": zdem}


def actuals(year: int) -> dict:
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].set_index("hour").sort_index()
    return {"rt": a["rt"].reindex(range(HOURS)).to_numpy(float),
            "da": a["da"].reindex(range(HOURS)).to_numpy(float)}


def zonal_actuals(year: int) -> dict[str, pd.DataFrame]:
    """Per-zone hourly measured rt/da: hub->zone mean + the Plains hub proxy."""
    d = pd.read_parquet(ZONAL)
    d = d[d["year"] == year]
    out = {}
    for col in ("rt", "da"):
        piv = d.groupby(["hour", "zone"])[col].mean().unstack("zone").reindex(range(HOURS))
        piv["MISO-Plains"] = (
            d[d["hub"].isin(PLAINS_PROXY_HUBS)]
            .groupby("hour")[col].mean().reindex(range(HOURS))
        )
        out[col] = piv
    return out


def bench_avg(year: int) -> dict:
    with gzip.open(BENCH_DIR / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["avgLMP"]


def _e930_frame(path: Path, keycol: str, keys: tuple[str, ...], year: int) -> pd.DataFrame:
    """Timestamp-keyed EIA-930 pivot on the model CST hour (UTC-6, Feb 29 dropped)."""
    d = pd.read_parquet(path)
    d = d[d[keycol].isin(keys)].copy()
    d["cst"] = d["period"] - pd.Timedelta(hours=6)
    d = d[d["cst"].dt.year == year]
    d = d[~((d["cst"].dt.month == 2) & (d["cst"].dt.day == 29))]
    mon = d["cst"].dt.month.to_numpy()
    hour = (np.array(MONTH_START)[mon - 1]
            + (d["cst"].dt.day.to_numpy() - 1) * 24 + d["cst"].dt.hour.to_numpy())
    d["hour"] = hour
    return (d.pivot_table(index="hour", columns=keycol, values="value_mwh", aggfunc="first")
            .reindex(range(HOURS)))


def e930(year: int) -> pd.DataFrame:
    reg = _e930_frame(REGION, "type", ("D", "TI"), year)
    fuel = _e930_frame(FUELTYPE, "fueltype",
                       ("WND", "SUN", "COL", "NG", "NUC", "WAT"), year)
    out = reg.join(fuel)
    out["netload"] = out["D"] - out["WND"] - out["SUN"]
    return out


def model_class(year: int) -> pd.DataFrame:
    d = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="klass", values="mw",
                         aggfunc="sum").reindex(range(HOURS))


# --------------------------------------------------------------------------
# the shared decomposition state per year
# --------------------------------------------------------------------------
class YearState:
    def __init__(self, year: int):
        self.year = year
        m = sidecar(year)
        a = actuals(year)
        self.W, self.Pm = m["W"], m["Pm"]
        self.zprice, self.zdem = m["zprice"], m["zdem"]
        self.rt, self.da = a["rt"], a["da"]
        self.bench = bench_avg(year)
        self.A = float(self.bench["rt_lw"])
        self.cov = np.isfinite(self.rt)
        self.den = float((self.W[self.cov] * self.A).sum())
        self.mon = month_of(np.arange(HOURS))
        self.tail = self.cov & (self.rt > TAIL_RT)

    def pp(self, mask: np.ndarray) -> float:
        """Contribution of the hour set to C3a, in percentage points."""
        m = mask & self.cov
        return float(100.0 * (self.W[m] * (self.Pm[m] - self.rt[m])).sum() / self.den)

    def pp_terms(self, mask: np.ndarray) -> dict:
        """Two-term split of the same contribution: model->DA and DA->RT."""
        m = mask & self.cov & np.isfinite(self.da)
        det = float(100.0 * (self.W[m] * (self.Pm[m] - self.da[m])).sum() / self.den)
        wedge = float(100.0 * (self.W[m] * (self.da[m] - self.rt[m])).sum() / self.den)
        return {"pp_model_to_da": det, "pp_da_to_rt": wedge}

    def lw(self, price: np.ndarray, mask: np.ndarray | None = None) -> float:
        m = np.ones(HOURS, bool) if mask is None else mask
        m = m & np.isfinite(price)
        return float((self.W[m] * price[m]).sum() / self.W[m].sum())

    def c3a_of(self, price: np.ndarray) -> float:
        return float(100.0 * (self.lw(price) / self.A - 1.0))

    def means(self, mask: np.ndarray) -> dict:
        m = mask & self.cov
        n = int(m.sum())
        if not n:
            return {"n_hours": 0}
        return {
            "n_hours": n,
            "mean_load_gw": float(self.W[m].mean() / 1000),
            "mean_model": float(self.Pm[m].mean()),
            "mean_rt": float(self.rt[m].mean()),
            "mean_da": float(np.nanmean(self.da[m])),
        }


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------
def stage_footing(st: YearState) -> dict:
    model_lw = st.lw(st.Pm)
    c3a = 100.0 * (model_lw / st.A - 1.0)
    reg = REGISTERED_C3A_PCT[st.year]
    delta = c3a - reg
    if abs(delta) > FOOTING_TOL_PP:
        raise SystemExit(
            f"FOOTING FAIL {st.year}: reproduced C3a {c3a:+.4f}% vs registered "
            f"{reg:+.3f}% (|delta| {abs(delta):.4f} pp > {FOOTING_TOL_PP})")
    rt_lw_repro = float((st.W[st.cov] * st.rt[st.cov]).sum() / st.W[st.cov].sum())
    model_lw_cov = st.lw(st.Pm, st.cov)
    resid_cov = 100.0 * (model_lw - model_lw_cov) / st.A
    resid_bench = 100.0 * (rt_lw_repro - st.A) / st.A
    cfg = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    return {
        "model_lw": model_lw,
        "bench_rt_lw": st.A,
        "bench_rt_lw_reproduced": rt_lw_repro,
        "c3a_pct": c3a,
        "registered_pct": reg,
        "delta_pp": delta,
        "n_cov": int(st.cov.sum()),
        "residual_pp": {"coverage": resid_cov, "bench_quantization": resid_bench},
        "resolved_config": {k: cfg.get(k) for k in CONFIG_FLAGS},
    }


def stage_zonal(st: YearState) -> dict:
    za = zonal_actuals(st.year)
    rows, contrib_sum = {}, 0.0
    for z in CARRY_ZONES:
        d = st.zdem[z].to_numpy(float)
        pm = st.zprice[z].to_numpy(float)
        rt = za["rt"][z].to_numpy(float) if z in za["rt"] else np.full(HOURS, np.nan)
        m = np.isfinite(rt) & np.isfinite(pm)
        own = float(100.0 * (d[m] * (pm[m] - rt[m])).sum() / (d[m] * rt[m]).sum())
        contrib = float(100.0 * (d[m] * (pm[m] - rt[m])).sum() / st.den)
        contrib_sum += contrib
        monthly = {}
        for mo in range(1, 13):
            mm = m & (st.mon == mo)
            monthly[mo] = float(100.0 * (d[mm] * (pm[mm] - rt[mm])).sum()
                                / (d[mm] * rt[mm]).sum()) if mm.any() else None
        rows[z] = {
            "proxy": z == "MISO-Plains",
            "own_err_pct": own,
            "contrib_pp_zonal_basis": contrib,
            "model_lw": float((d[m] * pm[m]).sum() / d[m].sum()),
            "actual_lw": float((d[m] * rt[m]).sum() / d[m].sum()),
            "own_err_pct_monthly": monthly,
        }
    # benchmark-basis wedge: zone-resolved actual lw mean vs the scored
    # Indiana-hub lw. Weights = per-zone hourly demand; hours where every zone
    # has a measured (or proxied) price.
    rtz = za["rt"][list(CARRY_ZONES)].to_numpy(float)
    dz = st.zdem[list(CARRY_ZONES)].to_numpy(float)
    ok = np.isfinite(rtz).all(axis=1)
    zonal_lw = float((dz[ok] * rtz[ok]).sum() / dz[ok].sum())
    rt_lw_repro = float((st.W[st.cov] * st.rt[st.cov]).sum() / st.W[st.cov].sum())
    model_lw = st.lw(st.Pm)
    return {
        "zones": rows,
        "sum_zone_contrib_pp_zonal_basis": contrib_sum,
        "basis_wedge": {
            "zone_resolved_actual_lw": zonal_lw,
            "indiana_hub_actual_lw": rt_lw_repro,
            "wedge_usd": zonal_lw - rt_lw_repro,
            "c3a_vs_indiana_hub_pct": float(100.0 * (model_lw / st.A - 1.0)),
            "c3a_vs_zone_resolved_pct": float(100.0 * (model_lw / zonal_lw - 1.0)),
            "note": ("wedge>0 means the scored single-hub benchmark reads BELOW the "
                     "zone-resolved actual; report-only, never a lever (bench basis "
                     "is the scorer's, rule 15)"),
        },
    }


def stage_buckets(st: YearState, e9: pd.DataFrame, cls: pd.DataFrame) -> dict:
    nl = e9["netload"].to_numpy(float)
    rankable = np.isfinite(nl) & st.cov
    n_top = int(np.ceil(0.10 * HOURS))
    order = np.argsort(np.where(rankable, nl, -np.inf))[::-1][:n_top]
    top = np.zeros(HOURS, bool)
    top[order[rankable[order]]] = True
    b_tail = st.tail
    b_netdec = top & ~b_tail
    b_rest = st.cov & ~b_tail & ~b_netdec
    out = {"n_rankable": int(rankable.sum()),
           "n_rank_ineligible_in_cov": int((st.cov & ~rankable).sum()),
           "netload_top_decile_n": n_top}
    total = 0.0
    for name, mask in (("tail_rt_gt_200", b_tail),
                       ("top_decile_netload_ex_tail", b_netdec),
                       ("remainder", b_rest)):
        pp = st.pp(mask)
        total += pp
        out[name] = {**st.means(mask), "pp_of_c3a": pp,
                     "share_of_gap_pct": None}
    for name in ("tail_rt_gt_200", "top_decile_netload_ex_tail", "remainder"):
        out[name]["share_of_gap_pct"] = float(100.0 * out[name]["pp_of_c3a"] / total) if total else None
    out["sum_pp"] = total
    # generation guard inside the tail hours: model family vs 930 family.
    m = b_tail
    guard = {}
    for fam, klasses in MODEL_FAMILY.items():
        cols = [k for k in klasses if k in cls.columns]
        model_mw = float(cls.loc[m, cols].sum(axis=1).mean()) if cols else 0.0
        col930 = E930_FAMILY[fam]
        e_mw = float(e9.loc[m, col930].mean()) if col930 in e9 else None
        guard[fam] = {"model_mw": model_mw, "e930_mw": e_mw}
    imp = float(cls.loc[m, "import"].mean()) if "import" in cls.columns else 0.0
    guard["net_import"] = {"model_mw": imp,
                           "e930_mw": float(-e9.loc[m, "TI"].mean())}
    out["tail_generation_guard"] = guard
    return out


def stage_seasonal(st: YearState) -> dict:
    months, total = {}, 0.0
    rt_lw_mon = st.bench.get("rt_lw_mon") or [None] * 12
    for mo in range(1, 13):
        mm = st.mon == mo
        pp = st.pp(mm)
        total += pp
        mcov = mm & st.cov
        model_lw_mon = st.lw(st.Pm, mcov)
        bench_mon = rt_lw_mon[mo - 1]
        months[mo] = {
            "pp_of_c3a": pp,
            "model_lw_mon": model_lw_mon,
            "bench_rt_lw_mon": bench_mon,
            "own_month_miss_pct": (float(100.0 * (model_lw_mon / bench_mon - 1.0))
                                   if bench_mon else None),
        }
    su = np.zeros(HOURS, bool)
    su[SUMMER[0]:SUMMER[1]] = True
    jj = np.zeros(HOURS, bool)
    jj[MONTH_START[5]:MONTH_START[7]] = True
    may = st.mon == 5
    return {
        "monthly": months,
        "sum_monthly_pp": total,
        "rollups_pp": {
            "may": st.pp(may),
            "jun_jul": st.pp(jj),
            "jun_jul_tail": st.pp(jj & st.tail),
            "jun_jul_body_ex_tail": st.pp(jj & ~st.tail),
            "summer_jun_sep": st.pp(su),
            "summer_tail": st.pp(su & st.tail),
            "non_summer": st.pp(~su),
            "non_summer_tail": st.pp(~su & st.tail),
        },
    }


def stage_foreseen(st: YearState) -> dict:
    tail_f = st.tail & (st.da > FORESEEN_DA)
    tail_r = st.tail & ~(st.da > FORESEEN_DA)
    out = {
        "whole_gap_two_term": {
            "annual": st.pp_terms(np.ones(HOURS, bool)),
            "tail": st.pp_terms(st.tail),
            "ex_tail": st.pp_terms(~st.tail),
        },
        "tail_split_da_150": {
            "DA_foreseen": {**st.means(tail_f), "pp_of_c3a": st.pp(tail_f),
                            **st.pp_terms(tail_f)},
            "RT_only": {**st.means(tail_r), "pp_of_c3a": st.pp(tail_r),
                        **st.pp_terms(tail_r)},
        },
    }
    monthly = {}
    for mo in range(1, 13):
        mm = st.mon == mo
        monthly[mo] = st.pp_terms(mm)
    out["whole_gap_two_term"]["monthly"] = monthly
    return out


def stage_ceilings(st: YearState) -> dict:
    p_tail = st.Pm.copy()
    p_tail[st.tail] = st.rt[st.tail]
    p_da = np.where(np.isfinite(st.da), st.da, st.Pm)
    return {
        "c3a_pct_as_is": st.c3a_of(st.Pm),
        "c3a_pct_tail_at_actual_rt": st.c3a_of(p_tail),
        "c3a_pct_model_at_actual_da": st.c3a_of(p_da),
        "note": ("tail_at_actual_rt = honest ceiling of any scarcity-only lever; "
                 "model_at_actual_da = ceiling of ANY deterministic hourly LP "
                 "(MISO's own DA market is one)"),
    }


def m167_repoint() -> dict:
    """Full miso-167 instrument re-run at miso177_rho_B (never calls its main)."""
    import _miso167_summer_scarcity_instrument as m167

    m167.BUNDLE = BUNDLE / "hourly"
    assert m167.BUNDLE == BUNDLE / "hourly", "m167 BUNDLE rebind failed"
    out = {"basis": {
        "repoint_of": "scripts/probes/_miso167_summer_scarcity_instrument.py",
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "caveats": [
            "inherits m167.e930_hourly's POSITIONAL hour key: its stage-2 2024 "
            "D/TI joins are shifted 24h for Jul-Dec (raw 930 is missing Jun 1 "
            "2024); the committed miso-167 record carries the identical "
            "construction, so record-to-record comparison is like-for-like",
            "inherits m167's -2h ASM alignment (not the production loader's EST "
            "key); ASM LEVELS are key-sensitive, product shares are not "
            "(FINDING-miso171 section 5)",
        ],
    }}
    for year in YEARS:
        df = m167.assemble(year)
        out[str(year)] = {
            "tail": m167.stage1_tail(df),
            "inputs": m167.stage2_inputs(df),
            "slope": m167.stage3_slope(df),
            "reserves": m167.stage4_reserves(df),
            "foreseen": m167.stage5_foreseen(df),
        }
    return out


def m171_continuity() -> dict:
    """Bit-identity of the miso-171 scarce-47 set at the new bundle (no re-run).

    stage4_mcp reads only published ASM MCPs + the DA validation series; its sole
    bundle dependence is scarce_hours() (top-47 by keeper load). Demand is
    bit-identical across the keeper lineage, so the committed
    _miso171_reserve_product_decomposition.json stage-4 blocks remain current if
    and only if the hour sets match -- asserted here instead of re-computing.
    """
    import _miso171_reserve_product_decomposition as m171

    sets = {}
    for bundle in ("miso170_layup_B2", "miso177_rho_B"):
        m171.BUNDLE = ROOT / "results" / "calibration" / bundle / "hourly"
        sets[bundle] = m171.scarce_hours(2025)
    identical = bool(np.array_equal(sets["miso170_layup_B2"], sets["miso177_rho_B"]))
    if not identical:
        raise SystemExit("miso-171 scarce-47 set DIVERGED across bundles -- "
                         "the committed stage-4 record is stale, re-run it")
    return {
        "scarce47_bit_identical_across_bundles": identical,
        "n": int(len(sets["miso177_rho_B"])),
        "consequence": ("committed _miso171_reserve_product_decomposition.json "
                        "stage-4 (ASM MCP by product, DA-foreseen split) remains "
                        "CURRENT at this keeper"),
    }


# --------------------------------------------------------------------------
def main() -> int:
    out: dict = {"basis": {
        "session": "miso-178",
        "keeper": "2026-08-22-miso-177-rho-measured",
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "hour_key": "model chronological non-leap 8760 CST calendar",
        "sign": "pp = contribution to (model-actual)/bench; negative = model UNDER",
        "tail_rt_threshold": TAIL_RT,
        "foreseen_da_threshold": FORESEEN_DA,
        "footing_tol_pp": FOOTING_TOL_PP,
    }}
    for year in YEARS:
        st = YearState(year)
        e9 = e930(year)
        cls = model_class(year)
        out[str(year)] = {
            "footing": stage_footing(st),
            "zonal": stage_zonal(st),
            "buckets": stage_buckets(st, e9, cls),
            "seasonal": stage_seasonal(st),
            "foreseen": stage_foreseen(st),
            "ceilings": stage_ceilings(st),
        }
    out["m167_repoint"] = m167_repoint()
    out["m171_continuity"] = m171_continuity()

    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    for year in YEARS:
        y = out[str(year)]
        f, b, s, fo, c = (y["footing"], y["buckets"], y["seasonal"],
                          y["foreseen"], y["ceilings"])
        print(f"================ {year} ================")
        print(f" footing: C3a {f['c3a_pct']:+.4f}% vs registered {f['registered_pct']:+.3f}%"
              f" (delta {f['delta_pp']:+.4f} pp)  bench rt_lw {f['bench_rt_lw']:.2f}")
        print(f" buckets: tail {b['tail_rt_gt_200']['pp_of_c3a']:+.3f} pp"
              f" ({b['tail_rt_gt_200']['n_hours']} h) | top-decile-netload"
              f" {b['top_decile_netload_ex_tail']['pp_of_c3a']:+.3f} pp"
              f" ({b['top_decile_netload_ex_tail']['n_hours']} h) | remainder"
              f" {b['remainder']['pp_of_c3a']:+.3f} pp  (sum {b['sum_pp']:+.3f})")
        r = s["rollups_pp"]
        print(f" seasonal: May {r['may']:+.3f} | Jun+Jul {r['jun_jul']:+.3f}"
              f" (tail {r['jun_jul_tail']:+.3f}, body {r['jun_jul_body_ex_tail']:+.3f})"
              f" | summer {r['summer_jun_sep']:+.3f} | non-summer {r['non_summer']:+.3f}")
        t = fo["tail_split_da_150"]
        print(f" tail split: DA-foreseen {t['DA_foreseen'].get('n_hours', 0)} h"
              f" {t['DA_foreseen'].get('pp_of_c3a', 0.0):+.3f} pp | RT-only"
              f" {t['RT_only'].get('n_hours', 0)} h {t['RT_only'].get('pp_of_c3a', 0.0):+.3f} pp")
        w = fo["whole_gap_two_term"]["annual"]
        print(f" two-term: model->DA {w['pp_model_to_da']:+.3f} pp"
              f" | DA->RT wedge {w['pp_da_to_rt']:+.3f} pp")
        print(f" ceilings: tail@RT {c['c3a_pct_tail_at_actual_rt']:+.3f}%"
              f" | model@DA {c['c3a_pct_model_at_actual_da']:+.3f}%")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
