"""SOCO-80 (ZERO LP): does the registered per-yard coal TAKE floor carry SOCO's two coal misses?

Rule 32 ``[R-SHARD]`` (a): never solves. The candidate is the registered
``coal_fuel_inventory_take_floor`` (NWPP-NEXT-7), whose construction is fixed ex
ante in ``data/coal_fuel_inventory.py::build_coal_take_floor``::

    take_net_y = max(0, C_{Y-1} + S_dec_{Y-1} - S_max_{<=Y-1}) * hc_{Y-1}

with every operand predating the solved year (rule 13). This probe reproduces
that arithmetic per SOCO coal plant (same loaders, same purchase types, same
net form) and converts it to MWh at the plant's applied net heat rate
(``campd_coal_heat_rates_SOCO.csv``, the keeper's own), then sets it beside
the keeper's committed model energy (payload ``m_ann``) and the EIA-923 actual
(bench ``e_ann``). A floor lifts a plant only where floor > model; a floor
above ACTUAL forces energy the real plant never produced.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco80_take_floor.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
import calibration_verdict as cv  # noqa: E402
from market_sim.data.coal_fuel_inventory import (  # noqa: E402
    TAKE_PURCHASE_TYPES,
    _shared_storage_map,
)
from market_sim.data.coal_receipts import load_coal_receipts  # noqa: E402
from market_sim.data.coal_stocks import load_coal_stocks  # noqa: E402

KEEPER = "2026-09-27-soco76-egrid-identity-hr"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
HR = _ROOT / "data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv"
OUT = _ROOT / "docs/records/soco/r-soco/soco80_take_floor.csv"


def main() -> None:
    """Per coal plant x year: take floor MWh vs keeper model vs EIA-923 actual."""
    art = cv.load_artifacts(KEEPER)
    hr = pd.read_csv(HR)
    hr = hr[hr.year == 0].set_index("plant_code")["heat_rate"]
    stocks = load_coal_stocks()
    shared = _shared_storage_map()
    rows = []
    for y in YEARS:
        pay = art["payload"]["years"][str(y)]["plants"]
        bench = art["bench"][y]["plants"]
        model, act = {}, {}
        for k, v in bench.items():
            if str(v.get("group", "")).startswith("COAL"):
                p = int(str(k).split(":")[0])
                act[p] = act.get(p, 0.0) + float(v.get("e_ann") or 0.0)
        for k, v in pay.items():
            # multi-class plants key "<code>:<CLASS>", single-class plants key "<code>"
            p = int(k.split(":")[0])
            if ":COAL" in k or (":" not in k and p in act):
                model[p] = model.get(p, 0.0) + float(v.get("m_ann") or 0.0)
        rec = load_coal_receipts([y - 1])
        st_y = stocks[stocks.year <= y - 1]
        for p in sorted(set(model) | set(act)):
            ids = {p}
            for sid, served in shared.items():
                if p in served or p == sid:
                    ids |= {sid} | set(served)
            st = st_y[st_y.plant_id.isin(ids)]
            r = rec[rec.plant_id.isin(ids)]
            row = dict(
                year=y,
                plant=p,
                yard=",".join(map(str, sorted(ids))),
                model_twh=round(model.get(p, 0.0), 3),
                actual_twh=round(act.get(p, 0.0), 3),
            )
            if (
                st.empty
                or not ((st.year == y - 1) & (st.month == 12)).any()
                or r.empty
                or p not in hr.index
            ):
                rows.append(
                    dict(
                        row,
                        floor_twh=np.nan,
                        note="no floor (missing stock/receipt/HR)",
                    )
                )
                continue
            bm = st.groupby(["year", "month"]).ending_stock_tons.sum()
            s_dec, s_max = float(bm.get((y - 1, 12), 0.0)), float(bm.max())
            tons = float(r.quantity_tons.sum())
            hc = float((r.quantity_tons * r.heat_content_mmbtu_per_ton).sum()) / tons
            c = float(
                r.loc[r.purchase_type.isin(TAKE_PURCHASE_TYPES), "quantity_tons"].sum()
            )
            net_tons = max(c + s_dec - s_max, 0.0)
            floor_twh = net_tons * hc / float(hr[p]) / 1e6
            rows.append(
                dict(
                    row,
                    contract_kt=round(c / 1e3),
                    s_dec_kt=round(s_dec / 1e3),
                    s_max_kt=round(s_max / 1e3),
                    net_kt=round(net_tons / 1e3),
                    hr=float(hr[p]),
                    floor_twh=round(floor_twh, 3),
                    lift_twh=round(max(floor_twh - model.get(p, 0.0), 0.0), 3),
                    over_actual_twh=round(max(floor_twh - act.get(p, 0.0), 0.0), 3),
                )
            )
    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    pd.set_option("display.width", 220)
    print(d.to_string(index=False))
    g = (
        d.groupby("year")[
            ["model_twh", "actual_twh", "floor_twh", "lift_twh", "over_actual_twh"]
        ]
        .sum()
        .round(2)
    )
    print(g.to_string())
    print(
        json.dumps(
            {
                "shared_storage_soco": {
                    k: sorted(v)
                    for k, v in shared.items()
                    if k in set(d.plant) or set(v) & set(d.plant)
                }
            }
        )
    )


if __name__ == "__main__" and "greedy" not in sys.argv:
    main()


# ---------------------------------------------------------------------------
# greedy: scorer-exact C1 / C4 with the floor lift dispatched LP-style
# ---------------------------------------------------------------------------
def greedy(d: pd.DataFrame) -> pd.DataFrame:
    """Price-taker greedy of the take floor on the keeper's committed hourlies.

    An annual floor's dual is a flat per-MWh discount on the yard's offers, so the
    LP places the lift in the plant's highest-price hours at full headroom. Here:
    per plant with ``lift_twh > 0``, sort its zone's hourly P1 price descending and
    fill ``npl - model MW`` (payload ``m`` decoded on the bench nameplate, the
    scorer's own construction) until the lift is met. The same MW are displaced
    from CC_REGULAR (the marginal class in every lifted hour). Outage windows are
    not visible in the payload, so the fill is an upper bound on how well the lift
    lands in-shape. Scores via ``calibration_verdict.score_fuelmix`` and the
    ``_soco73_phase0.c4_coal`` construction.
    """
    import base64

    sys.path.insert(0, str(_ROOT / "scripts" / "probes"))
    import _soco73_phase0 as s73

    s73.KEEPER_ID = KEEPER
    s73.SPAN = _ROOT / "results/calibration/soco76_span"
    art = cv.load_artifacts(KEEPER)
    out = []
    for y in YEARS:
        pay = art["payload"]["years"][str(y)]["plants"]
        bench = art["bench"][y]["plants"]
        sysd = pd.read_parquet(s73.SPAN / f"hourly/system_{y}.parquet")
        price = {
            z: g.sort_values("hour").price.to_numpy(float)[:8760]
            for z, g in sysd.groupby("zone")
        }
        coal_dt = np.zeros(8760)
        delta: dict[str, float] = {}
        for _, r in d[(d.year == y) & (d.lift_twh > 0)].iterrows():
            p = int(r.plant)
            for bk, bv in bench.items():
                if int(str(bk).split(":")[0]) != p or not str(
                    bv.get("group", "")
                ).startswith("COAL"):
                    continue
                pk = bk if bk in pay else str(p)
                npl = float(bv["npl"])
                m = (
                    np.frombuffer(base64.b64decode(pay[pk]["m"])[:8760], dtype=np.uint8)
                    * npl
                    / 100.0
                )
                head = np.clip(npl - m, 0.0, None)
                need = float(r.lift_twh) * 1e6
                add = np.zeros(8760)
                for h in np.argsort(-price[bv["zone"]]):
                    if need <= 0:
                        break
                    x = min(head[h], need)
                    add[h], need = x, need - x
                coal_dt += add
                cls = bv["group"]
                delta[cls] = delta.get(cls, 0.0) + add.sum() / 1e6
                delta["CC_REGULAR"] = delta.get("CC_REGULAR", 0.0) - add.sum() / 1e6
        c1 = s73.c1_rows(y, delta)
        r0, n0, r1, n1 = s73.c4_coal(y, coal_dt)
        for _, row in c1[
            c1.cls.isin(["COAL_BIT", "COAL_PRB", "CC_REGULAR"])
        ].iterrows():
            out.append(
                dict(
                    year=y,
                    row=f"C1 {row.cls}",
                    keeper=f"{row.pp0:+.2f}pp {row.st0}",
                    arm=f"{row.pp1:+.2f}pp {row.st1}",
                )
            )
        out.append(
            dict(
                year=y,
                row="C4 coal r/NRMSE",
                keeper=f"{r0:.3f}/{n0:.3f}",
                arm=f"{r1:.3f}/{n1:.3f}",
            )
        )
        out.append(
            dict(
                year=y,
                row="lift TWh by class",
                keeper="",
                arm=json.dumps({k: round(v, 2) for k, v in delta.items()}),
            )
        )
    g = pd.DataFrame(out)
    g.to_csv(
        _ROOT / "docs/records/soco/r-soco/soco80_take_floor_greedy.csv", index=False
    )
    print(g.to_string(index=False))
    return g


if __name__ == "__main__" and "greedy" in sys.argv:
    greedy(pd.read_csv(OUT))
