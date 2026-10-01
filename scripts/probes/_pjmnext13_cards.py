"""PJM-NEXT-13 zero-LP cards 1-3 on the keeper ``2026-09-28-pjm-next8-exitfix``.

Reads the ``fleet_only`` dumps written by ``_pjmnext13_fleet_dump.py`` (pass their
directory as argv[1]) plus committed artifacts only — the keeper's run payload, the
bench, its hourly sidecars and the IMM rows in ``som-competitive-conduct``. No LP.

Card 1 — coal AVAILABILITY vs dispatch. Per bench COAL_BIT plant-month: the model's
available MW (sum of the plant's tranche ``pmax x availability``), the model's own
monthly max output, and CAMPD's monthly max hourly net output (the bench series).
``excess_over_real_max`` = model energy above the real month's max (the most a
measured monthly derate at the demonstrated max could remove), set against the
C1 over-run by year. ``hp_max_ratio`` repeats the real-max / available ratio on the
months carrying at least one hub-price hour above $80 (where an available coal unit
has every reason to be at its max), which separates a derate from an economic choice.

Card 2 — replacement-cost gas. The keeper's capacity-weighted CC_REGULAR / CT_PEAKER
fuel price per zone and year against the IMM's digitized Platts East / West /
Production gas (``spot_price_digitized_usd_per_mmbtu``).

Card 3 — the model's coal-set LMP share. From ``class_band_hourly`` and the rebuilt
band capacities: an hour is COAL-PARTIAL when at least one coal econ / peak / sync
band sits strictly inside (2 %, 98 %) of its available MW. That is an UPPER bound on
coal-marginal hours: a band aggregates many plants, so a partial aggregate can also
be one plant full and another idle. Reported with the IMM's RT marginal-unit and LMP
fuel-component shares.

Writes ``results/phase0/pjm/_pjmnext13_cards.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext10_coal_phase0 as P10  # noqa: E402
import _pjmnext11_margin_audit as P11  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext13_cards.json"
BUNDLE = P10.BUNDLE
ZONES = (
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
    "PJM_external",
)
COAL = ("COAL_BIT", "COAL_WC", "COAL_PRB")
PRICE_BAND_BANDS = ("econc", "peak", "sync")
HIGH_PRICE = 80.0  # $/MWh — the NEXT-11 bin above which real coal loading rises
PARTIAL = (0.02, 0.98)
MONTH = pd.date_range("2001-01-01", periods=8760, freq="h").month.to_numpy() - 1


def load_dump(d: Path, y: int) -> dict:
    """The rebuilt fleet arrays for one year."""
    z = np.load(d / f"pjmnext13_fleet_{y}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def card1(y: int, f: dict, run: dict) -> dict:
    """Coal availability vs dispatch on bench COAL_BIT plants."""
    ps = P10.plant_series(y, run)
    grp, pc = f["plant_group"], f["plant_code"]
    avail_mw = f["pmax"][:, None] * f["availability"]
    ah = P11.actual_hub_prices(y)
    rows = []
    for k, (m, c, v) in ps.items():
        code = k.split(":")[0]
        sel = (pc == code) & (grp == "COAL_BIT")
        if not sel.any() or c.sum() <= 0:
            continue
        a = avail_mw[sel].sum(axis=0)[:8760]
        hub = P10.HUB.get(v["zone"])
        hp = ah[hub].to_numpy()[:8760] if hub in ah.columns else np.zeros(8760)
        for mo in range(12):
            h = MONTH == mo
            cmax, mmax, amean = c[h].max(), m[h].max(), a[h].mean()
            if amean <= 0 and cmax <= 0:
                continue
            rows.append(
                {
                    "plant": code,
                    "month": mo + 1,
                    "avail_mean": float(amean),
                    "avail_max": float(a[h].max()),
                    "campd_max": float(cmax),
                    "model_max": float(mmax),
                    "campd_on": bool(cmax > 0),
                    "high_price_month": bool((hp[h] > HIGH_PRICE).any()),
                    "excess_mwh": float(np.clip(m[h] - cmax, 0, None).sum()),
                    "model_mwh": float(m[h].sum()),
                    "campd_mwh": float(c[h].sum()),
                }
            )
    r = pd.DataFrame(rows)
    on = r[r.campd_on & (r.avail_mean > 0)]
    hp = on[on.high_price_month]
    return {
        "n_plant_months": len(r),
        "gap_twh": round((r.model_mwh.sum() - r.campd_mwh.sum()) / 1e6, 2),
        "excess_over_real_max_twh": round(on.excess_mwh.sum() / 1e6, 2),
        "real_max_over_avail": round(on.campd_max.sum() / on.avail_max.sum(), 3),
        "model_max_over_avail": round(on.model_max.sum() / on.avail_max.sum(), 3),
        "hp_months": len(hp),
        "hp_real_max_over_avail": (
            round(hp.campd_max.sum() / hp.avail_max.sum(), 3) if len(hp) else None
        ),
        "hp_model_max_over_avail": (
            round(hp.model_max.sum() / hp.avail_max.sum(), 3) if len(hp) else None
        ),
        "dark_but_available_twh": round(
            r[~r.campd_on].avail_mean.mul(730).sum() / 1e6, 2
        ),
    }


def card2(y: int, f: dict, imm: pd.DataFrame) -> dict:
    """Keeper gas price by zone (cap-weighted) vs the IMM's Platts regions."""
    out = {}
    fp, pm, grp, zi = (
        f["fuel_prices"],
        f["pmax"],
        f["plant_group"],
        f["zone"].astype(int),
    )
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        per = {}
        for z, name in enumerate(ZONES[:-1]):
            s = (grp == cls) & (zi == z)
            if pm[s].sum() <= 0:
                continue
            per[name] = round(
                float((fp[s].mean(axis=1) * pm[s]).sum() / pm[s].sum()), 3
            )
        s = grp == cls
        per["ALL"] = round(float((fp[s].mean(axis=1) * pm[s]).sum() / pm[s].sum()), 3)
        out[cls] = per
    iy = imm[imm.year == y].set_index("fleet_segment")["value"]
    out["imm"] = {
        k: round(float(iy[k]), 3)
        for k in ("east_gas", "west_gas", "production_gas")
        if k in iy
    }
    return out


def card3(y: int, f: dict, som: pd.DataFrame) -> dict:
    """Coal-partial hour share (upper bound on coal-marginal) vs the IMM shares."""
    cb = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{y}.parquet")
    cb = cb[(cb["pass"] == "P1") & cb.klass.isin(COAL)]
    uid, grp = f["unit_ids"].astype(str), f["plant_group"]
    avail_mw = f["pmax"][:, None] * f["availability"]
    partial = np.zeros(8760, bool)
    per_band = {}
    for (kl, band), g in cb.groupby(["klass", "band"]):
        if not band.startswith(PRICE_BAND_BANDS):
            continue
        sel = (grp == kl) & np.char.endswith(uid.astype("U"), "_" + band)
        cap = avail_mw[sel].sum(axis=0)[:8760]
        mw = g.sort_values("hour").mw.to_numpy()[:8760]
        with np.errstate(invalid="ignore", divide="ignore"):
            lf = np.where(cap > 1.0, mw / cap, np.nan)
        p = (lf > PARTIAL[0]) & (lf < PARTIAL[1])
        per_band[f"{kl}:{band}"] = round(float(np.nanmean(p)), 3)
        partial |= p
    s = som[(som.year == y) & (som.period == "annual")]

    def pick(seg: str, met: str) -> float | None:
        v = s[(s.fleet_segment == seg) & (s.metric == met)].value
        return round(float(v.iloc[0]), 3) if len(v) else None

    return {
        "model_coal_partial_hour_share": round(float(partial.mean()), 3),
        "top_bands": dict(sorted(per_band.items(), key=lambda kv: -kv[1])[:6]),
        "imm_rt_marginal_unit_share_coal": pick("coal", "rt_marginal_resource_share"),
        "imm_rt_lmp_share_coal_fuel": pick("coal_fuel", "rt_lmp_component_share"),
    }


TRANCHE_ORDER = (
    "mustrun",
    "committed",
    "sync",
    "econc00",
    "econc01",
    "econc02",
    "econc03",
    "econc04",
    "econc05",
    "peak",
)
#: A plant-hour sits INSIDE a price tranche when its MW is further than this share of
#: the plant's nameplate from every cumulative tranche boundary. The run payload
#: stores hourly MW as a 1 %-of-nameplate CF byte, so 1.5 % is the quantization floor.
BOUNDARY_TOL = 0.015


def card3_plants(y: int, f: dict, run: dict, load_w: pd.DataFrame) -> dict:
    """Coal-marginal zone-hours from per-plant hourly MW vs the plant's tranche stack."""
    b = P10.bench(y)["plants"]
    mp = run[str(y)]["plants"]
    uid, grp, pc = f["unit_ids"].astype(str), f["plant_group"], f["plant_code"]
    zi = f["zone"].astype(int)
    avail_mw = f["pmax"][:, None] * f["availability"]
    marg = np.zeros((8760, len(ZONES)), bool)
    n = 0
    for code in set(pc[np.isin(grp, COAL)]):
        sel = (pc == code) & np.isin(grp, COAL)
        if code not in mp:
            continue
        npl = b.get(code, {}).get("npl") or float(f["pmax"][sel].sum())
        m = P10.decode(mp[code]["m"], mp[code]["m_ann"], npl)[:8760]
        idx = np.where(sel)[0]
        order = sorted(
            idx,
            key=lambda i: next(
                (j for j, t in enumerate(TRANCHE_ORDER) if uid[i].endswith("_" + t)), 99
            ),
        )
        cum = np.cumsum(avail_mw[order][:, :8760], axis=0)
        lo = np.vstack([np.zeros(8760), cum[:-1]])
        price_t = np.array(
            [uid[i].rsplit("_", 1)[-1].startswith(PRICE_BAND_BANDS) for i in order]
        )
        tol = BOUNDARY_TOL * npl
        inside = (m[None, :] > lo + tol) & (m[None, :] < cum - tol) & price_t[:, None]
        marg[:, zi[idx[0]]] |= inside.any(axis=0)
        n += 1
    w = load_w[list(ZONES[:-1])].to_numpy()[:8760]
    share_lw = float((marg[:, :-1] * w).sum() / w.sum())
    any_zone = float(marg[:, :-1].any(axis=1).mean())
    return {
        "n_coal_plants": n,
        "coal_marginal_zonehour_share_load_weighted": round(share_lw, 3),
        "hours_with_any_coal_marginal": round(any_zone, 3),
    }


def main() -> None:
    """Run all three cards per year and write the JSON."""
    d = Path(sys.argv[1])
    run = P10.load_run()
    som = pd.read_csv(
        REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
    )
    som = som[som.iso == "PJM"]
    imm = som[
        (som.metric == "spot_price_digitized_usd_per_mmbtu") & (som.period == "annual")
    ]
    out = {}
    for y in P10.YEARS:
        if not (d / f"pjmnext13_fleet_{y}.npz").exists():
            continue
        f = load_dump(d, y)
        sysd = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        load_w = sysd.pivot_table(
            index="hour", columns="zone", values="demand"
        ).sort_index()
        c3 = card3(y, f, som)
        c3.update(card3_plants(y, f, run, load_w))
        rec = {"card1": card1(y, f, run), "card2": card2(y, f, imm), "card3": c3}
        out[str(y)] = rec
        print(y, json.dumps(rec), flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
