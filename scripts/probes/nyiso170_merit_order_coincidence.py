"""nyiso-170 PHASE 0 — is the within-gas merit-order split an HOURLY DISPLACEMENT?

ZERO SOLVE. Reads the designated keeper's committed hourly sidecars, the
committed per-ISO benchmark parts, NYISO's CAMPD unit-level hourly record, the
committed actual-LMP series and the Transco Z6 NY daily gas record. No LP runs;
nothing here is or becomes an LP input.

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.
Rule 13 ``[R-MEASURED]``: CAMPD dispatch enters as CONDUCT identification only.
Nothing here pins, rescales or offsets a class to its observed generation.

The question
------------
nyiso-169b measured that NYISO's total gas volume is right to ~1 % while the
split inside it is not (2025 TWh vs benchmark: CC_CHP +2.77, CC_REGULAR +2.15,
ST_CHP +0.69 against ST_GAS -3.92, CT_PEAKER -1.82, CT_CHP -0.55). The brief
opens that as a candidate carrier of the nyiso-167 price-response gain (0.7032):
if the model clears cheap combined cycles (base HR ~7.0-7.8) in the high-load
hours where the market clears CTs and gas steam (base HR ~10.6-11.9), its
marginal cost at the top of the stack is roughly half the market's.

That story requires the over-run and the under-run to be THE SAME HOURS. If they
are not, this is two unrelated volume objects, not a displacement, and the lane
stops here (the nyiso-152/168/169 precedent).

PRE-REGISTERED GATES — written and committed BEFORE the probe was run
---------------------------------------------------------------------
The confound this probe must survive: NYISO load is matched hour by hour, so any
gas the model does not produce as CT/ST it tends to produce as SOMETHING, which
can manufacture apparent coincidence with no merit-order content at all. Gate G1
is therefore stated twice — once literally (the brief's question) and once in a
form that is exactly free of the total-gas level.

**G1a — LITERAL COINCIDENCE.** ``OVER(h)`` = the model-minus-measured error
summed over the over-run classes {CC_CHP, CC_REGULAR, ST_CHP}; ``UNDER(h)`` =
minus the same over {CT_PEAKER, ST_GAS, CT_CHP}. Statistics: Pearson r, and
``matched_share`` = sum_h min(OVER+, UNDER+) / sum_h OVER+. Null = 999 circular
shifts of UNDER against OVER (preserves each series' marginal distribution and
autocorrelation). COINCIDENT iff matched_share >= 0.60 in all three years AND
above the null p95 in all three.

**G1b — THE CONFOUND-FREE DECOMPOSITION (decisive).** With ``s`` the class's
share of its side's own gas total and ``G`` that gas total, the class error
factors EXACTLY:

    delta_class(h) = s_meas,class(h) * dG(h)   +   ds_class(h) * G_model(h)
                     \___ TOTAL-GAS LEVEL ___/      \___ WITHIN-GAS MIX ___/

The object is a merit-order object only if the MIX term carries it. DECISIVE
GATE: the mix term must carry >= 60 % of |delta| for the over-run group AND for
the under-run group, in all three years. If the level term dominates, the
class-split errors are a gas-versus-non-gas object wearing merit-order clothes,
and the lane stops whatever G1a says.

**G2 — REVEALED MARGINAL CLASS.** Independent of price: on hours whose system
load rises by > 200 MW (the nyiso-168 section 4 first-difference threshold),
each gas class's share of the increment, model vs measured. The displacement
story predicts the model's increment is disproportionately CC and the market's
disproportionately CT/ST. SUPPORTED iff the model's CC share of the increment
exceeds the measured CC share in all three years.

**G3 — THE C3a LINKAGE (what makes this a C3a lever and not only a C1 one).**
Model-minus-actual DA price by decile of the hourly CC-share excess ds_CC(h).
The displacement carries the gain deficit only if the price gap is monotone in
ds_CC: hours where the model runs the most excess CC must be the hours it
under-prices most. CARRIES iff the top-ds decile's price gap is at least
$2/MWh more negative than the bottom's, in all three years, AND the same sign
holds inside the 50-90 load band that carries 73 % of the 2025 deficit.

**STOP CONDITION.** If G1b fails, or G1a and G2 both fail, the object is NOT an
hourly displacement, no parameter is touched, no solve is spent, and the finding
records the stop. That is a legitimate outcome, not an omission.

Measurements
------------
A. CLASS VOLUME and the exact level/mix decomposition of each class's error.
B. G1a coincidence statistics with the circular-shift null.
C. G2 revealed marginal class from load-rise first differences.
D. G3 price gap by CC-share-excess decile, whole year and in the 50-90 band.
E. The offer-band effective heat-rate ladder both sides imply — the cost
   separation phase 2 would have to identify, reported for the record only.

Measured classes are CAMPD ``unitType`` crossed with the EIA-860 CHP flag
(``market_sim.data.chp._chp_by_plant``) — the model's own CHP determination, and
the same construction as nyiso-169b, extended from three classes to the full
six-way gas split. CAMPD reports GROSS load while the benchmark is
grid-delivered, so each measured class is scaled by ONE factor,
benchmark_TWh / CAMPD_TWh, which puts it on the grid-delivered basis while
PRESERVING the annual level error exactly (the anchored series sums to the
benchmark, so model - anchored sums to the committed delta_twh).

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso170_merit_order_coincidence.py``
Writes: ``results/calibration/_nyiso170_merit_order_coincidence.json``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.data.derive_actual_lmp import _std_hour_index  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
GAS_CSV = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
HR_SUMMARY = RAW_DATA_DIR / "reference/nyiso_campd_marginal_hr_summary.csv"
OUT = REPO / "results/calibration/_nyiso170_merit_order_coincidence.json"
STD_TZ = "Etc/GMT+5"

#: The six model gas classes, split into the two groups nyiso-169b measured.
OVER_CLASSES = ("CC_CHP", "CC_REGULAR", "ST_CHP")
UNDER_CLASSES = ("CT_PEAKER", "ST_GAS", "CT_CHP")
GAS_CLASSES = OVER_CLASSES + UNDER_CLASSES

#: CAMPD unitType predicate per model class. Steam is every boiler form the NY
#: vocabulary carries (Tangentially-fired / Dry bottom wall-fired / Other
#: boiler); nyiso-169b's ST_GAS pooled the CHP boilers in with them, so this
#: probe reports BOTH that pooled series and the CHP-split one (cross-check).
UNIT_KIND = {
    "CC_CHP": ("Combined cycle", True),
    "CC_REGULAR": ("Combined cycle", False),
    "CT_CHP": ("Combustion turbine", True),
    "CT_PEAKER": ("Combustion turbine", False),
    "ST_CHP": ("STEAM", True),
    "ST_GAS": ("STEAM", False),
}

#: Load-percentile bands, the nyiso-168 measurement-A edges.
BANDS = ((0, 50), (50, 80), (80, 90), (90, 95), (95, 99), (99, 100))

#: Circular-shift null for G1a.
N_NULL = 999
NULL_SEED = 170

#: Pre-registered gate thresholds (see the module docstring).
G1A_MATCHED_MIN = 0.60
G1B_MIX_SHARE_MIN = 0.60
G3_SPREAD_MIN = 2.0
LOAD_RISE_MW = 200.0


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_frame(year: int) -> pd.DataFrame:
    """CAMPD NY unit-level hourly, stamped onto the model's 8760 clock."""
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitType", "date", "hour", "grossLoad"],
    )
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    d = d.assign(
        _h=_std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ),
        _fid=d["facilityId"].astype(int),
        _ut=d["unitType"].fillna(""),
    )
    return d


def measured_hourly(d: pd.DataFrame, klass: str, chpset: set[int]) -> pd.Series:
    """Measured GROSS hourly MW for one model class, on the 8760 clock."""
    kind, is_chp = UNIT_KIND[klass]
    ut = d["_ut"]
    sel = ut.str.contains("fired|boiler", case=False) if kind == "STEAM" else ut.str.contains(kind)
    inchp = d["_fid"].isin(chpset)
    sel = sel & (inchp if is_chp else ~inchp)
    s = pd.Series(d.loc[sel, "grossLoad"].to_numpy())
    return s.groupby(d.loc[sel, "_h"].to_numpy()).sum().reindex(range(8760)).fillna(0.0)


def model_hourly(year: int, klass: str) -> pd.Series:
    """The keeper's own P1 hourly MW for one class (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == klass)]
    return c.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0).astype(float)


def bench_classes(year: int) -> dict[str, float]:
    """Committed grid-delivered class volumes, TWh."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def keeper_system(year: int) -> tuple[np.ndarray, np.ndarray]:
    """``(system load, load-weighted model price)`` from the keeper's sidecar."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot_table(index="hour", columns="zone", values="price")
    d = s.pivot_table(index="hour", columns="zone", values="demand")
    load = d.sum(axis=1).to_numpy()
    return load, (p * d).sum(axis=1).to_numpy() / load


def hourly_gas(year: int) -> np.ndarray:
    """Daily Transco Z6 NY spot broadcast to the year's 8760 standard hours."""
    gas = pd.read_csv(GAS_CSV, parse_dates=["date"]).set_index("date")
    ser = gas["transco_z6_ny_usd_mmbtu"].astype(float)
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    ser = ser.reindex(days).ffill().bfill()
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return ser.reindex(idx.normalize()).to_numpy()


def build_series(year: int, chpset: set[int]) -> tuple[dict, dict, dict]:
    """Model, benchmark-anchored measured, and raw CAMPD hourly MW per class."""
    d = campd_frame(year)
    bench = bench_classes(year)
    model, meas, raw = {}, {}, {}
    for k in GAS_CLASSES:
        m = model_hourly(year, k).to_numpy()
        x = measured_hourly(d, k, chpset).to_numpy()
        tot = float(x.sum())
        scale = (bench.get(k, 0.0) * 1e6 / tot) if tot > 0 else 0.0
        model[k], meas[k], raw[k] = m, x * scale, x
    return model, meas, raw


def measure_a(year: int, model: dict, meas: dict) -> dict:
    """Class volume plus the EXACT level/mix decomposition of each class error.

    ``delta = s_meas * dG + ds * G_model`` is an algebraic identity, so the two
    terms sum to the class error to floating-point. G1b reads the mix share.
    """
    bench = bench_classes(year)
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    dG = gm - gx
    rows, group = {}, {"over": [0.0, 0.0], "under": [0.0, 0.0]}
    for k in GAS_CLASSES:
        sx = np.divide(meas[k], gx, out=np.zeros(8760), where=gx > 0)
        sm = np.divide(model[k], gm, out=np.zeros(8760), where=gm > 0)
        lvl, mix = sx * dG, (sm - sx) * gm
        d = model[k] - meas[k]
        rows[k] = dict(
            model_twh=round(float(model[k].sum()) / 1e6, 4),
            bench_twh=round(float(bench.get(k, 0.0)), 4),
            delta_twh=round(float(d.sum()) / 1e6, 4),
            delta_pct=(
                round(float(d.sum()) / (bench[k] * 1e6) * 100, 2)
                if bench.get(k) else None
            ),
            level_term_twh=round(float(lvl.sum()) / 1e6, 4),
            mix_term_twh=round(float(mix.sum()) / 1e6, 4),
            identity_residual_twh=round(float((lvl + mix - d).sum()) / 1e6, 8),
            mix_share_of_abs=round(
                float(abs(mix.sum())) / max(float(abs(lvl.sum()) + abs(mix.sum())), 1e-9), 4
            ),
        )
        g = "over" if k in OVER_CLASSES else "under"
        group[g][0] += float(lvl.sum())
        group[g][1] += float(mix.sum())
    grp = {
        g: dict(
            level_term_twh=round(v[0] / 1e6, 4),
            mix_term_twh=round(v[1] / 1e6, 4),
            mix_share_of_abs=round(abs(v[1]) / max(abs(v[0]) + abs(v[1]), 1e-9), 4),
        )
        for g, v in group.items()
    }
    return dict(
        by_class=rows,
        by_group=grp,
        total_gas_model_twh=round(float(gm.sum()) / 1e6, 4),
        total_gas_measured_twh=round(float(gx.sum()) / 1e6, 4),
        total_gas_delta_pct=round(float(dG.sum()) / float(gx.sum()) * 100, 2),
        G1b_mix_carries=bool(
            grp["over"]["mix_share_of_abs"] >= G1B_MIX_SHARE_MIN
            and grp["under"]["mix_share_of_abs"] >= G1B_MIX_SHARE_MIN
        ),
    )


def measure_b(model: dict, meas: dict) -> dict:
    """G1a — literal hourly coincidence, against a circular-shift null."""
    over = np.sum([model[k] - meas[k] for k in OVER_CLASSES], axis=0)
    under = -np.sum([model[k] - meas[k] for k in UNDER_CLASSES], axis=0)
    op, up = np.clip(over, 0, None), np.clip(under, 0, None)
    denom = float(op.sum())
    matched = float(np.minimum(op, up).sum()) / denom if denom else 0.0

    rng = np.random.default_rng(NULL_SEED)
    shifts = rng.integers(1, 8760, size=N_NULL)
    null = np.array(
        [float(np.minimum(op, np.roll(up, int(s))).sum()) / denom for s in shifts]
    )
    r = float(np.corrcoef(over, under)[0, 1])
    return dict(
        pearson_r=round(r, 4),
        matched_share=round(matched, 4),
        null_median=round(float(np.median(null)), 4),
        null_p95=round(float(np.percentile(null, 95)), 4),
        excess_over_null_median=round(matched - float(np.median(null)), 4),
        hours_both_positive=int(((over > 0) & (under > 0)).sum()),
        hours_over_positive=int((over > 0).sum()),
        G1a_coincident=bool(
            matched >= G1A_MATCHED_MIN and matched > float(np.percentile(null, 95))
        ),
    )


def measure_c(model: dict, meas: dict, load: np.ndarray) -> dict:
    """G2 — revealed marginal class from load-rise first differences."""
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    dl = np.diff(load)
    up = dl > LOAD_RISE_MW
    out = {}
    for nm, src, tot in (("model", model, gm), ("measured", meas, gx)):
        dt = float(np.diff(tot)[up].sum())
        out[nm] = {
            k: (round(float(np.diff(src[k])[up].sum()) / dt, 4) if dt else None)
            for k in GAS_CLASSES
        }
        out[nm]["_gas_increment_mw"] = round(dt, 1)
        out[nm]["_cc_share"] = (
            round(
                float(sum(np.diff(src[k])[up].sum() for k in ("CC_CHP", "CC_REGULAR")))
                / dt,
                4,
            )
            if dt
            else None
        )
        out[nm]["_ct_st_share"] = (
            round(float(sum(np.diff(src[k])[up].sum() for k in UNDER_CLASSES)) / dt, 4)
            if dt
            else None
        )
    out["n_rising_hours"] = int(up.sum())
    out["G2_model_cc_heavier"] = bool(
        (out["model"]["_cc_share"] or 0) > (out["measured"]["_cc_share"] or 0)
    )
    return out


def measure_d(model: dict, meas: dict, load, mprice, da) -> dict:
    """G3 — price gap by decile of the hourly CC-share excess, and by load band."""
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    cm = np.divide(
        model["CC_CHP"] + model["CC_REGULAR"], gm, out=np.zeros(8760), where=gm > 0
    )
    cx = np.divide(
        meas["CC_CHP"] + meas["CC_REGULAR"], gx, out=np.zeros(8760), where=gx > 0
    )
    ds = cm - cx
    gap = mprice - da

    order = np.argsort(ds)
    dec = []
    for k in range(10):
        idx = order[int(8760 * k / 10) : int(8760 * (k + 1) / 10)]
        dec.append(
            dict(
                decile=k,
                ds_cc=round(float(ds[idx].mean()), 4),
                load_mw=round(float(load[idx].mean()), 1),
                model=round(float(mprice[idx].mean()), 2),
                actual_da=round(float(np.nanmean(da[idx])), 2),
                gap=round(float(np.nanmean(gap[idx])), 2),
            )
        )
    spread = dec[9]["gap"] - dec[0]["gap"]

    lo = np.argsort(load)[int(8760 * 0.50) : int(8760 * 0.90)]
    dsb, gpb = ds[lo], gap[lo]
    ob = np.argsort(dsb)
    n = len(ob) // 4
    band_spread = float(np.nanmean(gpb[ob[-n:]]) - np.nanmean(gpb[ob[:n]]))

    return dict(
        by_ds_decile=dec,
        top_minus_bottom_gap=round(spread, 2),
        band_50_90_top_minus_bottom_quartile_gap=round(band_spread, 2),
        ds_cc_mean=round(float(ds.mean()), 4),
        ds_cc_hours_positive=int((ds > 0).sum()),
        G3_carries=bool(spread <= -G3_SPREAD_MIN and band_spread < 0),
    )


def measure_e() -> dict:
    """The offer-band effective heat-rate ladder, for the record (not a gate)."""
    from market_sim.pipeline.backcast_config import _NYISO_OFFER_CURVE

    hr = pd.read_csv(HR_SUMMARY).set_index("class")["base_hr"].to_dict()
    out = {}
    for k, bands in _NYISO_OFFER_CURVE.items():
        b = float(hr.get(k, float("nan")))
        out[k] = dict(
            base_hr=b,
            **{
                n: (round(b * float(bands[n]), 3) if n in bands else None)
                for n in ("committed", "econ_low", "econ_high", "peak")
            },
        )
    return out


def main() -> None:
    chpset = chp_plants()
    act = pd.read_parquet(ACTUAL_HOURLY)
    rec: dict = {
        "probe": "nyiso170_merit_order_coincidence",
        "bundle": str(KEEPER.relative_to(REPO)),
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "years": list(YEARS),
        "note": (
            "Zero solve. PHASE 0 of the within-gas merit-order object: is the "
            "CC over-run the SAME HOURS as the CT/ST under-run, and is the "
            "content a within-gas MIX error rather than a total-gas level "
            "error? Gates pre-registered in the module docstring and committed "
            "before the probe was run."
        ),
        "gate_thresholds": dict(
            G1a_matched_min=G1A_MATCHED_MIN,
            G1b_mix_share_min=G1B_MIX_SHARE_MIN,
            G3_spread_min_usd=G3_SPREAD_MIN,
            load_rise_mw=LOAD_RISE_MW,
            n_null=N_NULL,
            null_seed=NULL_SEED,
        ),
        "E_offer_band_effective_hr": measure_e(),
        "by_year": {},
    }

    for year in YEARS:
        model, meas, _ = build_series(year, chpset)
        load, mprice = keeper_system(year)
        a = act[act["year"] == year].sort_values("hour")
        da = a["da"].to_numpy(float)

        A = measure_a(year, model, meas)
        B = measure_b(model, meas)
        C = measure_c(model, meas, load)
        D = measure_d(model, meas, load, mprice, da)
        rec["by_year"][str(year)] = {
            "A_volume_and_decomposition": A,
            "B_G1a_coincidence": B,
            "C_G2_revealed_marginal": C,
            "D_G3_price_linkage": D,
        }

        print(f"\n{year}")
        print(
            f"  A  total gas model {A['total_gas_model_twh']:.2f} vs measured "
            f"{A['total_gas_measured_twh']:.2f} TWh ({A['total_gas_delta_pct']:+.2f}%)"
        )
        for g in ("over", "under"):
            v = A["by_group"][g]
            print(
                f"     {g:<5} level {v['level_term_twh']:+7.3f} TWh   mix "
                f"{v['mix_term_twh']:+7.3f} TWh   mix share {v['mix_share_of_abs']:.3f}"
            )
        print(f"     G1b MIX CARRIES: {A['G1b_mix_carries']}")
        print(
            f"  B  matched {B['matched_share']:.3f}  null p95 {B['null_p95']:.3f}  "
            f"r {B['pearson_r']:+.3f}   G1a COINCIDENT: {B['G1a_coincident']}"
        )
        print(
            f"  C  CC share of load-rise increment: model {C['model']['_cc_share']:.3f} "
            f"vs measured {C['measured']['_cc_share']:.3f}   G2: {C['G2_model_cc_heavier']}"
        )
        print(
            f"  D  gap top-minus-bottom ds decile {D['top_minus_bottom_gap']:+.2f} "
            f"$/MWh; 50-90 band {D['band_50_90_top_minus_bottom_quartile_gap']:+.2f}"
            f"   G3 CARRIES: {D['G3_carries']}"
        )

    ys = rec["by_year"]
    rec["verdict"] = dict(
        G1b_mix_carries_all_years=all(
            ys[str(y)]["A_volume_and_decomposition"]["G1b_mix_carries"] for y in YEARS
        ),
        G1a_coincident_all_years=all(
            ys[str(y)]["B_G1a_coincidence"]["G1a_coincident"] for y in YEARS
        ),
        G2_supported_all_years=all(
            ys[str(y)]["C_G2_revealed_marginal"]["G2_model_cc_heavier"] for y in YEARS
        ),
        G3_carries_all_years=all(
            ys[str(y)]["D_G3_price_linkage"]["G3_carries"] for y in YEARS
        ),
    )
    v = rec["verdict"]
    v["proceed_to_phase_2"] = bool(
        v["G1b_mix_carries_all_years"]
        and (v["G1a_coincident_all_years"] or v["G2_supported_all_years"])
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\n  VERDICT {json.dumps(v)}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
