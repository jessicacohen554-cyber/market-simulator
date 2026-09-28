"""soco-83 zero-LP probe: SOCO's CC_REGULAR over-run / ST_GAS under-run against Southern's own system lambda.

Rule 32 ``[R-SHARD]`` (a): never solves. Instruments, all on the incumbent keeper
``2026-09-27-soco82-perunitdark-regen`` (bundle ``results/calibration/soco82_span``):

``plants`` — per gas plant-class (CC_REGULAR, ST_GAS, CT_PEAKER) and year: model TWh
            (committed run payload) vs benchmark TWh (EIA-923 boundary, committed bench).
``offers`` — ``fleet_only`` rebuilds on the keeper's own recipe (the soco-73 ``rebuild``
            pointed at ``soco82_span``): each gas plant-class's capacity-weighted median
            offer (``mc_base``), and — in the plant's CEMS-synchronised hours — the share of
            hours Southern's FERC-714 Sch. 6 system lambda sits BELOW that offer (the
            FINDING-soco-82 §3 test, applied to gas). Also the model P1 price vs lambda.
            Writes ``docs/handoffs/r-soco/soco83_gas_offers.csv``.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco83_gas_split.py plants
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco83_gas_split.py offers [--years 2021]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(_ROOT / "scripts"),
    str(_ROOT / "scripts" / "probes"),
    str(_ROOT / "src"),
]

import _soco73_phase0 as s73  # noqa: E402

KEEPER = "2026-09-27-soco82-perunitdark-regen"
SPAN = _ROOT / "results/calibration/soco82_span"
BENCH = _ROOT / "frontend/data/backcast/bench/SOCO/{y}.json.gz"
OUT = _ROOT / "docs/handoffs/r-soco/soco83_gas_offers.csv"
#: The per-plant monthly ST_GAS cost the lambda-conditioned out-of-merit derive reads
#: (scripts/data/derive_thermal_tranche_oom_level_mw.py --condition lambda).
COST_OUT = _ROOT / "data/raw/_processed-legacy/thermal_tranches_oom_cost_SOCO.csv"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
GAS = ("CC_REGULAR", "ST_GAS", "CT_PEAKER")
#: CAMPD unit-level extracts are per state; SOCO's gas fleet sits in these four.
STATES = ("AL", "GA", "MS", "FL")
T = 8760

s73.KEEPER_ID = KEEPER
s73.SPAN = SPAN


def _bench(year: int) -> dict:
    return json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["plants"]


def _payload(year: int) -> dict:
    import calibration_verdict as cv

    return cv.load_artifacts(KEEPER)["payload"]["years"][str(year)]["plants"]


def _model_mw(pay: dict, key: str, npl: float) -> np.ndarray:
    raw = np.frombuffer(base64.b64decode(pay[key]["m"])[:T], dtype=np.uint8)
    return raw.astype(float) * npl / 100.0


def plants_table(year: int) -> pd.DataFrame:
    """Per gas plant-class: model vs benchmark TWh."""
    b, pay = _bench(year), _payload(year)
    rows = []
    for key, v in b.items():
        g = v.get("group")
        if g not in GAS:
            continue
        a = float(
            np.nansum(
                json.loads(v["e_mon"])
                if isinstance(v.get("e_mon"), str)
                else (v.get("e_mon") or [0])
            )
        )
        m = float(pay[key]["m_ann"]) if key in pay else 0.0
        rows.append(
            dict(
                year=year,
                key=key,
                name=v.get("name"),
                cls=g,
                npl=float(v.get("npl") or 0),
                bench_twh=round(a / 1e3, 3),
                model_twh=round(m, 3),
                d_twh=round(m - a / 1e3, 3),
            )
        )
    return pd.DataFrame(rows)


def main_plants(years: list[int]) -> None:
    """Print class totals and the largest plant-level misses per year."""
    pd.set_option("display.width", 250)
    for y in years:
        t = plants_table(y)
        print(f"== {y}")
        print(
            t.groupby("cls")[["bench_twh", "model_twh", "d_twh"]]
            .sum()
            .round(2)
            .to_string()
        )
        print(
            t.sort_values("d_twh")
            .iloc[list(range(4)) + list(range(-5, 0))]
            .to_string(index=False)
        )


def lambda_series(year: int) -> np.ndarray:
    """Southern's hourly system lambda for ``year`` on the model's hour grid (UTC-6 local, hour-beginning)."""
    from market_sim.data.ferc714 import load_ferc714_system_lambda

    L = load_ferc714_system_lambda()
    # The model's hour 0 is local 00:00 on Jan 1; the committed series is UTC hour-beginning
    # at fixed UTC-6 (data/raw/ferc-714/README.md), so local = UTC - 6 h.
    loc = (
        L.index.tz_convert(None) - pd.Timedelta(hours=6)
        if L.index.tz is not None
        else L.index - pd.Timedelta(hours=6)
    )
    s = pd.Series(L["system_lambda_usd_mwh"].to_numpy(float), index=loc)
    s = s[(s.index >= f"{year}-01-01") & (s.index < f"{year + 1}-01-01")]
    return s.to_numpy(float)[:T]


def cems_plant(plant: int, year: int, fuel: str = "Natural Gas") -> np.ndarray:
    """8760 CEMS gross MW over the plant's units whose primary fuel names ``fuel``."""
    out = np.zeros(T)
    for st in STATES:
        p = _ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "grossLoad",
                "primaryFuelInfo",
            ],
        )
        d = d[d.facilityId.astype(str) == str(plant)]
        if d.empty:
            continue
        d = d[d.primaryFuelInfo.astype(str).str.contains(fuel)]
        h = ((d.date - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + d.hour).to_numpy()
        ok = (h >= 0) & (h < T)
        np.add.at(
            out, h[ok].astype(int), np.nan_to_num(d.grossLoad.to_numpy(float))[ok]
        )
        return out
    return out


def main_offers(years: list[int]) -> None:
    """Gas offers vs lambda in CEMS-synced hours; model price vs lambda."""
    rows = []
    cost_rows: list[dict] = []
    for y in years:
        lam = lambda_series(y)
        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        p = (
            s[(s.zone == "SOCO_AL") & (s["pass"] == "P1")]
            .sort_values("hour")
            .price.to_numpy(float)[:T]
        )
        n = min(len(p), len(lam))
        print(
            f"{y}: model P1 mean {p[:n].mean():.2f} | lambda mean {lam[:n].mean():.2f} | "
            f"bias {p[:n].mean() - lam[:n].mean():+.2f} | r {np.corrcoef(p[:n], lam[:n])[0, 1]:.3f}"
        )
        r = s73.rebuild(y, None)
        mc = r["mc"] if r["mc"].ndim == 2 else np.repeat(r["mc"][:, None], T, axis=1)
        ids = pd.Series(r["unit_ids"])
        b = _bench(y)
        for key, v in b.items():
            g = v.get("group")
            if g not in ("CC_REGULAR", "ST_GAS"):
                continue
            plant = int(str(key).split(":")[0])
            sel = (
                pd.Series(r["plant"]).astype(str) == str(plant)
            ).to_numpy() & ids.str.startswith(g).to_numpy()
            if not sel.any():
                continue
            w = r["pmax"][sel]
            # capacity-weighted offer per hour across the plant-class's tranches, cheapest band excluded
            # only if it is a must-run floor (min_gen) -- here every tranche counts, weighted by pmax.
            off = (mc[sel] * w[:, None]).sum(0) / w.sum()
            if g == "ST_GAS":
                mon = pd.Series(off[:T], index=pd.date_range(f"{y}-01-01", periods=T, freq="h")).groupby(
                    lambda t: t.month).median()
                for mo, c in mon.items():
                    cost_rows.append(dict(plant_code=plant, plant_group=g, year=y, month=int(mo),
                                          cost_usd_mwh=round(float(c), 3)))
            a = cems_plant(plant, y)
            npl = float(v.get("npl") or 0) or float(w.sum())
            syn = a > 0.01 * npl
            m = min(n, T)
            below = (lam[:m] < off[:m]) & syn[:m]
            rows.append(
                dict(
                    year=y,
                    plant=plant,
                    name=v.get("name"),
                    cls=g,
                    offer_med=round(float(np.median(off)), 2),
                    sync_h=int(syn[:m].sum()),
                    lam_below_offer_share=round(
                        float(below.sum() / max(syn[:m].sum(), 1)), 3
                    ),
                    lam_minus_offer_med_synced=round(
                        float(np.median((lam[:m] - off[:m])[syn[:m]])), 2
                    )
                    if syn[:m].any()
                    else None,
                    cems_gross_twh=round(a.sum() / 1e6, 3),
                    cems_twh_lam_below=round(float(a[:m][below].sum()) / 1e6, 3),
                    p50_load_frac_lam_below=round(
                        float(np.median(a[:m][below]) / npl), 3
                    )
                    if below.any()
                    else None,
                )
            )
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(t.to_string(index=False))
    t.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(_ROOT)}")
    if set(years) == set(YEARS):
        c = pd.DataFrame(cost_rows).sort_values(["plant_code", "year", "month"])
        c["source"] = (f"keeper {KEEPER} fleet_only mc_base (measured ST heat rate x EIA-923 delivered "
                       "gas + VOM), pmax-weighted over the plant's ST_GAS tranches, monthly median")
        c.to_csv(COST_OUT, index=False)
        print(f"wrote {COST_OUT.relative_to(_ROOT)} ({len(c)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("plants", "offers"))
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    a = ap.parse_args()
    {"plants": main_plants, "offers": main_offers}[a.mode](a.years)
