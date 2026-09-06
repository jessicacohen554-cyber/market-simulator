"""nyiso-197 PHASE 0 part 1 (NO LP) — decompose Linden 50006 ``CC_CHP``'s gap
against its meters, and diff the keeper against the prior keeper hour by hour
to locate the ~1.0 TWh/yr the extract-basis repair moved OFF the plant.

Everything here reads committed artifacts only (rule 29 ``[R-SCREEN]`` step 0;
control = the keeper's committed bundle, rule 29(b) form 4):

* the keeper's and the prior keeper's dashboard payloads
  (``frontend/data/backcast/runs/<id>.js``), decoded exactly as
  ``legitimacy_diagnostics`` and the nyiso-194/195/196 probes decode them;
* the shared bench part (``bench/NYISO/<yr>.json.gz``) for each plant's CAMPD
  hourly series, its EIA-923 annual (``e_ann``) and the measured CHP
  behind-the-meter hold-out (``btm``);
* both bundles' ``hourly/`` sidecars (class dispatch, zonal price, demand);
* the raw CAMPD unit-level series for 50006 (gross load, heat input, CO2) —
  the fuel-consistency check on the meter itself.

Three measurements, no gate:

**L-1  bucket decomposition.**  Per plant-hour, against the CAMPD gross series
on the payload's own basis (model = LP grid dispatch + the flat CHP add-back,
exactly as the run page renders it):

  (a) model on, meter off   -> Sum m      (online-hours excess)
  (b+) both on, model above -> Sum (m-c)  (loading excess)
  (b-) both on, model below -> Sum (c-m)  (loading deficit)
  (c) meter on, model off   -> Sum c      (netted under-run)

split by month, hour-of-day and NYC-zone LMP quartile, so ``a + b+ - b- - c``
equals the annual net by identity.

**L-2  the comparand ladder.**  The plant's four published quantities on one
line — CAMPD gross (hourly, the plant-grain table's meter), EIA-923 net
generation, the measured NYISO Gold-Book net energy implied by the committed
BTM artifact, and the model's LP grid dispatch (payload minus its own flat
add-back) — plus the CEMS fuel-consistency check (implied gross and net heat
rates against the same reported heat input).

**L-3  the displacement.**  Keeper minus prior keeper, hour by hour: Linden's
own delta, then where it went — per class (``class_hourly``), per plant
aggregated to (zone, class) from the payloads, imports, slack/dump — measured
BOTH over all hours and restricted to the hours Linden fell, with the zonal
price delta alongside.

Nothing here is gated on any residual; the output is a measurement.  Writes
``results/calibration/_nyiso197_linden_phase0.json``.

Usage::

    python scripts/probes/nyiso197_linden_phase0.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
KEEPER_BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
PRIOR_ID = "2026-09-05-nyiso-192-astoria-panel"
PRIOR_BUNDLE = ROOT / "results/calibration/nyiso192_astoria_panel"
PLANT = 50006
PLANT_KEY = "50006"
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
CAMPD_RAW = ROOT / "data/raw/campd-unit-level/NJ_{year}.parquet"
E923 = ROOT / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
BTM_ARTIFACT = ROOT / "data/raw/_processed-legacy/chp_btm_share_measured_NYISO.csv"


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, key_bytes: str, key_ann: str, npl: float) -> np.ndarray | None:
    """Decode a payload/bench hourly series, annual-rescaled (the LD decode)."""
    raw_b64 = entry.get(key_bytes)
    if not raw_b64:
        return None
    raw = _dec(raw_b64)[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    if npl > 0:
        return raw * npl / 100.0
    return None


def _month_of_hour() -> np.ndarray:
    m = np.zeros(T, dtype=int)
    for i in range(12):
        m[MONTH_STARTS[i] : MONTH_STARTS[i + 1]] = i + 1
    return m


def _quartile(x: np.ndarray) -> np.ndarray:
    q = np.percentile(x, [25, 50, 75])
    return np.digitize(x, q) + 1  # 1..4


def _by(energy: np.ndarray, groups: np.ndarray, keys) -> dict:
    return {str(k): round(float(energy[groups == k].sum()) / 1e3, 1) for k in keys}


def _payload_plants(run: dict, bench_plants: dict, year: int) -> dict:
    """{key: (group, zone, model_mw, campd_mw, npl)} for one payload year."""
    out: dict[str, tuple] = {}
    for key, ent in run["years"][str(year)]["plants"].items():
        b = bench_plants.get(key)
        if not b:
            continue
        npl = float(b.get("npl") or 0.0)
        m = _series(ent, "m", "m_ann", npl)
        c = _series(b, "campd", "c_ann", npl)
        if m is None:
            continue
        out[key] = (b.get("group"), b.get("zone"), m, c, npl)
    return out


def _cems_fuel_check(year: int) -> dict:
    """Plant-level CEMS gross/heat/CO2 for 50006 — the meter's own consistency."""
    path = Path(str(CAMPD_RAW).format(year=year))
    if not path.exists():
        return {"available": False}
    d = pd.read_parquet(path)
    lin = d[d.facilityId.astype(str) == str(PLANT)]
    if lin.empty:
        return {"available": False}
    g = lin.groupby("unitId").agg(
        gross_mwh=("grossLoad", "sum"),
        heat_mmbtu=("heatInput", "sum"),
        gross_max_mw=("grossLoad", "max"),
        co2_short_tons=("co2Mass", "sum"),
        steam_load=("steamLoad", "sum"),
    )
    hourly = lin.pivot_table(
        index=["date", "hour"], columns="unitId", values="grossLoad", aggfunc="sum"
    ).sum(axis=1)
    gross = float(g.gross_mwh.sum())
    heat = float(g.heat_mmbtu.sum())
    return {
        "available": True,
        "n_cems_units": int(g.shape[0]),
        "unit_gross_max_mw": {u: float(v) for u, v in g.gross_max_mw.items()},
        "plant_gross_gwh": round(gross / 1e3, 1),
        "plant_hourly_max_mw": round(float(hourly.max()), 1),
        "plant_hourly_mean_mw": round(float(hourly.mean()), 1),
        "heat_input_mmbtu": round(heat, 0),
        "implied_gross_hr_btu_per_kwh": round(heat * 1e6 / (gross * 1e3), 0),
        "co2_t_per_mwh_gross": round(
            float(g.co2_short_tons.sum()) * 0.907185 / gross, 4
        ),
        "steam_load_reported": float(g.steam_load.sum()),
    }


def _e923_net(year: int) -> dict:
    d = pd.read_parquet(E923)
    l = d[(d.plant_id == PLANT) & (d.year == year)]
    if l.empty:
        return {"available": False}
    by_pm = l.groupby("prime_mover").netgen_annual_mwh.sum()
    return {
        "available": True,
        "net_gwh": round(float(l.netgen_annual_mwh.sum()) / 1e3, 1),
        "by_prime_mover_gwh": {k: round(float(v) / 1e3, 1) for k, v in by_pm.items()},
        "ba_code": sorted(set(l.ba_code.dropna().astype(str))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    a = ap.parse_args()

    keeper = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    prior = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{PRIOR_ID}.js").read_text()
    )
    btm_art = pd.read_csv(BTM_ARTIFACT)
    btm_row = btm_art[btm_art.plant_code == PLANT].iloc[0].to_dict()
    month = _month_of_hour()
    hod = np.arange(T) % 24

    out = {
        "session": "nyiso-197",
        "status": "PHASE 0 part 1 — NO LP, MEASUREMENT ONLY",
        "keeper": KEEPER_ID,
        "prior_keeper": PRIOR_ID,
        "plant": PLANT,
        "btm_artifact_row": {
            k: (round(float(v), 4) if isinstance(v, (int, float)) else str(v)[:90])
            for k, v in btm_row.items()
        },
        "years": {},
    }

    for yr in a.years:
        bench = json.load(
            gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
        )["bench"]
        bplants = bench["plants"]
        kp = _payload_plants(keeper, bplants, yr)
        pp = _payload_plants(prior, bplants, yr)
        sysk = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"system_{yr}.parquet")
        sysp = pd.read_parquet(PRIOR_BUNDLE / "hourly" / f"system_{yr}.parquet")
        lmp_k = sysk.pivot(index="hour", columns="zone", values="price").iloc[:T]
        lmp_p = sysp.pivot(index="hour", columns="zone", values="price").iloc[:T]
        clk = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
        clp = pd.read_parquet(PRIOR_BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
        piv_k = clk.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).iloc[:T]
        piv_p = clp.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).iloc[:T]

        # ---------------- L-1 : Linden buckets vs the CAMPD gross meter ----------
        grp, zone, m_k, c, npl = kp[PLANT_KEY]
        _, _, m_p, _, _ = pp[PLANT_KEY]
        b = bplants[PLANT_KEY]
        e_ann = float(b["e_ann"])  # EIA-923 net generation, TWh
        btm_twh = float(b["btm"])  # measured CHP hold-out, TWh
        addback_mw = btm_twh * 1e6 / T  # the flat per-hour add-back
        lp_k = np.clip(m_k - addback_mw, 0.0, None)
        lp_p = np.clip(m_p - addback_mw, 0.0, None)

        thr = 0.01 * npl + 1.0
        on_m, on_c = m_k > thr, c > thr
        A = on_m & ~on_c
        Bp = on_m & on_c & (m_k > c)
        Bm = on_m & on_c & (m_k < c)
        C = ~on_m & on_c
        e_a = np.where(A, m_k, 0.0)
        e_bp = np.where(Bp, m_k - c, 0.0)
        e_bm = np.where(Bm, c - m_k, 0.0)
        e_c = np.where(C, c, 0.0)
        zq = _quartile(lmp_k[zone].to_numpy())

        linden = {
            "zone": zone,
            "group": grp,
            "npl_mw": npl,
            "model_gwh": round(m_k.sum() / 1e3, 1),
            "prior_model_gwh": round(m_p.sum() / 1e3, 1),
            "campd_gross_gwh": round(c.sum() / 1e3, 1),
            "net_vs_campd_gwh": round((m_k.sum() - c.sum()) / 1e3, 1),
            "online_h_model": int(on_m.sum()),
            "online_h_campd": int(on_c.sum()),
            "buckets_gwh": {
                "a_model_on_meter_off": round(e_a.sum() / 1e3, 1),
                "b_plus_loading_excess": round(e_bp.sum() / 1e3, 1),
                "b_minus_loading_deficit": round(e_bm.sum() / 1e3, 1),
                "c_meter_on_model_off": round(e_c.sum() / 1e3, 1),
                "identity_check_gwh": round(
                    (
                        e_a.sum()
                        + e_bp.sum()
                        - e_bm.sum()
                        - e_c.sum()
                        - (m_k.sum() - c.sum())
                    )
                    / 1e3,
                    4,
                ),
            },
            "b_minus_by_month_gwh": _by(e_bm, month, range(1, 13)),
            "b_minus_by_hour_gwh": _by(e_bm, hod, range(24)),
            "b_minus_by_zone_lmp_quartile_gwh": _by(e_bm, zq, range(1, 5)),
            "b_plus_by_month_gwh": _by(e_bp, month, range(1, 13)),
            "model_mw_stats": {
                "max": round(float(m_k.max()), 1),
                "mean": round(float(m_k.mean()), 1),
                "p95": round(float(np.percentile(m_k, 95)), 1),
            },
            "campd_mw_stats": {
                "max": round(float(c.max()), 1),
                "mean": round(float(c.mean()), 1),
                "p95": round(float(np.percentile(c, 95)), 1),
            },
        }

        # ---------------- L-2 : the comparand ladder -----------------------------
        gold_book_twh = e_ann * (1.0 - float(btm_row["btm_pct"]) / 100.0)
        ladder = {
            "campd_gross_twh": round(c.sum() / 1e6, 4),
            "eia923_net_twh": round(e_ann, 4),
            "measured_btm_holdout_twh": round(btm_twh, 4),
            "goldbook_grid_delivery_twh_implied": round(gold_book_twh, 4),
            "model_payload_full_plant_twh": round(m_k.sum() / 1e6, 4),
            "model_lp_grid_twh": round(lp_k.sum() / 1e6, 4),
            "prior_model_lp_grid_twh": round(lp_p.sum() / 1e6, 4),
            "model_lp_minus_goldbook_twh": round(lp_k.sum() / 1e6 - gold_book_twh, 4),
            "prior_lp_minus_goldbook_twh": round(lp_p.sum() / 1e6 - gold_book_twh, 4),
            "model_payload_minus_923net_twh": round(m_k.sum() / 1e6 - e_ann, 4),
            "campd_gross_minus_923net_twh": round(c.sum() / 1e6 - e_ann, 4),
            "cems": _cems_fuel_check(yr),
            "eia923": _e923_net(yr),
        }
        if ladder["cems"].get("available") and ladder["eia923"].get("available"):
            heat = ladder["cems"]["heat_input_mmbtu"]
            ladder["cems"]["implied_net_hr_btu_per_kwh"] = round(
                heat * 1e6 / (ladder["eia923"]["net_gwh"] * 1e6), 0
            )

        # ---------------- L-3 : the displacement, keeper - prior -----------------
        d_lin = m_k - m_p
        fell = d_lin < -1.0
        cls_delta_all = {}
        cls_delta_fell = {}
        for k in sorted(set(piv_k.columns) | set(piv_p.columns)):
            dk = piv_k[k].to_numpy() if k in piv_k else np.zeros(T)
            dp = piv_p[k].to_numpy() if k in piv_p else np.zeros(T)
            d = dk[:T] - dp[:T]
            cls_delta_all[k] = round(float(d.sum()) / 1e3, 1)
            cls_delta_fell[k] = round(float(d[fell].sum()) / 1e3, 1)

        zc_delta_all: dict[str, float] = defaultdict(float)
        zc_delta_fell: dict[str, float] = defaultdict(float)
        plant_delta: list[tuple[float, str]] = []
        for key, (g2, z2, mk2, _c2, _n2) in kp.items():
            if key not in pp:
                continue
            d = mk2 - pp[key][2]
            zc_delta_all[f"{z2}|{g2}"] += float(d.sum())
            zc_delta_fell[f"{z2}|{g2}"] += float(d[fell].sum())
            plant_delta.append(
                (
                    float(d.sum()) / 1e3,
                    f"{key} {bplants[key].get('name', '')[:28]} {z2}|{g2}",
                )
            )
        plant_delta.sort()

        price_delta = {
            z: round(float((lmp_k[z] - lmp_p[z]).mean()), 3) for z in lmp_k.columns
        }
        price_delta_fell = {
            z: round(
                float(
                    (
                        lmp_k[z].to_numpy()[:T][fell] - lmp_p[z].to_numpy()[:T][fell]
                    ).mean()
                ),
                3,
            )
            for z in lmp_k.columns
        }

        out["years"][str(yr)] = {
            "L1_linden_buckets": linden,
            "L2_comparand_ladder": ladder,
            "L3_displacement": {
                "linden_delta_gwh": round(float(d_lin.sum()) / 1e3, 1),
                "hours_linden_fell": int(fell.sum()),
                "linden_fall_in_those_hours_gwh": round(
                    float(d_lin[fell].sum()) / 1e3, 1
                ),
                "class_delta_gwh_all_hours": cls_delta_all,
                "class_delta_gwh_in_linden_fall_hours": cls_delta_fell,
                "zone_class_delta_gwh_all_hours": {
                    k: round(v / 1e3, 1)
                    for k, v in sorted(zc_delta_all.items(), key=lambda x: x[1])
                },
                "zone_class_delta_gwh_in_fall_hours": {
                    k: round(v / 1e3, 1)
                    for k, v in sorted(zc_delta_fell.items(), key=lambda x: x[1])
                },
                "plant_delta_gwh_bottom8": [
                    f"{v:+.1f} {n}" for v, n in plant_delta[:8]
                ],
                "plant_delta_gwh_top8": [f"{v:+.1f} {n}" for v, n in plant_delta[-8:]],
                "zone_mean_price_delta": price_delta,
                "zone_mean_price_delta_in_fall_hours": price_delta_fell,
                "slack_dump_delta_gwh": {
                    "slack": round(float(sysk.slack.sum() - sysp.slack.sum()) / 1e3, 2),
                    "dump": round(float(sysk.dump.sum() - sysp.dump.sum()) / 1e3, 2),
                },
            },
        }
        print(
            f"[{yr}] done — linden Δ {out['years'][str(yr)]['L3_displacement']['linden_delta_gwh']:+.1f} GWh"
        )

    dest = ROOT / "results/calibration/_nyiso197_linden_phase0.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"wrote {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
