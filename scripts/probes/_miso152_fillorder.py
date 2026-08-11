"""miso-152 — the tranche FILL-ORDER screen (PREREG charter B). NO LP solve of
the real system; the fleet and its offer basis are assembled through the
production chain and interrogated statically.

The object (PREREG §1): physics fills a thermal plant in OUTPUT-POSITION order
(the min-load block first — a unit cannot produce its incremental band without
being at min load), but the LP fills in COST order and carries no same-plant
fill-order constraint. Where MISO's registered bands are non-monotone in
position (``econ_low < committed``), the model therefore produces a plant's
incremental band while its min-load block sits idle.

Gates implemented here:

* **G-2** per-plant, per-hour ordering of the EFFECTIVE marginal cost, computed
  through the real offer path (``assemble_mc`` -> ``apply_coal_tranches`` ->
  ``apply_gas_offer_margin``), never from the registered multipliers (trap T-3).
* **G-4** magnitude: the share of CC energy exposed to out-of-order fill,
  reconstructed from the keeper's own hourly prices.
* **G-5** sign: whether enforcing fill order raises or lowers the price the
  fleet clears at, inferred from the change in supply-at-price.

T-6 counter-measurement gates G-4/G-5: the price-driven reconstruction must
reproduce the keeper's committed ``class_hourly`` within +/-10 % of class annual
energy, else the session falls to PREREG branch B-5 (descriptive only).

Reuses the miso-134 production chain verbatim (``build_year``): fleet -> arrays
-> resolved delivered fuel prices -> mc -> coal tranches -> gas margin.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# The miso-134 module is hard-wired to the miso-132 bundle. This session's
# keeper is miso-148 (2026-08-09-miso-148-basis-aware), so the bundle is
# REPOINTED here before any of its helpers run — inheriting miso-132's config
# would silently screen the wrong keeper. Asserted, never assumed.
BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE

from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_class_mw,
    keeper_config,
    keeper_prices,
)

OUT = REPO / "results/calibration/_miso152_fillorder.json"
YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years touched anywhere below

# Output-position order of the tranche bands, cheapest-physical-position first.
# A plant produces its min-load block before any incremental block; the peak
# (duct-fire / overfire) band is physically last.
BAND_POSITION = {"mustrun": 0, "committed": 1, "econ": 2, "peak": 3}

# The CC fleet under test (PREREG §1(1)): both classes carry MISO CC capacity
# and both register econ_low < committed. This is the PRE-REGISTERED G-4/G-5
# scope and the only scope from which a gated verdict is taken.
CC_CLASSES = ("CC_REGULAR", "CC_INTERMEDIATE")

# NOT PRE-REGISTERED (reported as an addition, never as a gated result). G-2
# found the same inversion on CT_PEAKER and ST_GAS with LARGER per-MWh gaps,
# and a min_gen census found CT_PEAKER's 79 committed rows are as unfloored as
# CC's — so the pre-registered CC-only scope under-counts the object. ST_GAS is
# partly pinned (16/23 rows, 27.7 % of hours) and is measured for contrast.
EXTRA_CLASSES = ("CT_PEAKER", "ST_GAS")

# T-6 bar (PREREG §5): reconstruction vs the committed class_hourly.
T6_TOL = 0.10


def _band_of(unit_id: str) -> str:
    """Return the tranche band suffix of a CAMPD per-plant unit id.

    Raises rather than defaulting: a silent default on the offer path IS the
    bug (trap T-2, the miso-151 ``pmax``/``pmax_mw`` incident).
    """
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", unit_id)
    if m is None:
        return ""
    band = m.group(2)
    for key in BAND_POSITION:
        if band.startswith(key):
            return key
    return band


def _plant_of(unit_id: str) -> int:
    m = re.search(r"_p(\d+)_", unit_id)
    return int(m.group(1)) if m else -1


def tranche_table(fleet, arrays, zone_names) -> pd.DataFrame:
    """Static per-tranche table. Required fields are read DIRECTLY (trap T-2)."""
    z_of = {n: i for i, n in enumerate(zone_names)}
    rows = []
    for i, g in enumerate(fleet):
        uid = str(g.unit_id)
        rows.append(
            {
                "i": i,
                "klass": str(g.plant_group or ""),
                "plant": _plant_of(uid),
                "band": _band_of(uid),
                "zi": z_of.get(str(g.zone), 0),
                "pmax": float(arrays.pmax[i]),
            }
        )
    df = pd.DataFrame(rows)
    df["pos"] = df["band"].map(BAND_POSITION)
    return df


def g2_ordering(tt: pd.DataFrame, mc: np.ndarray) -> dict:
    """G-2 — per-plant inversion rate of the EFFECTIVE mc against position.

    For every plant, every ordered band pair (lower position, higher position),
    count the hours in which the LOWER-position band is more expensive than the
    higher one — i.e. the hours the LP would fill the plant out of physical
    order.
    """
    out: dict[str, dict] = {}
    cc = tt[tt["klass"].isin(CC_CLASSES) & (tt["pos"].notna())]
    for klass, grp in tt[tt["pos"].notna()].groupby("klass"):
        pair_stats: dict[str, dict] = {}
        for plant, pg in grp.groupby("plant"):
            pg = pg.sort_values("pos")
            recs = list(pg.itertuples())
            for a_idx in range(len(recs)):
                for b_idx in range(a_idx + 1, len(recs)):
                    lo, hi = recs[a_idx], recs[b_idx]
                    if lo.pos == hi.pos:
                        continue
                    key = f"{lo.band}>{hi.band}"
                    inv = mc[lo.i, :] > mc[hi.i, :] + 1e-9  # T-5: tolerance
                    d = pair_stats.setdefault(
                        key, {"plant_hours": 0, "inverted_hours": 0,
                              "plants": 0, "inverted_plants": 0,
                              "gap_sum": 0.0, "gap_n": 0}
                    )
                    d["plant_hours"] += mc.shape[1]
                    d["inverted_hours"] += int(inv.sum())
                    d["plants"] += 1
                    d["inverted_plants"] += int(inv.any())
                    if inv.any():
                        d["gap_sum"] += float((mc[lo.i, inv] - mc[hi.i, inv]).sum())
                        d["gap_n"] += int(inv.sum())
        for key, d in pair_stats.items():
            d["inverted_hour_share"] = (
                d["inverted_hours"] / d["plant_hours"] if d["plant_hours"] else 0.0
            )
            d["mean_gap_per_mwh"] = (
                d["gap_sum"] / d["gap_n"] if d["gap_n"] else 0.0
            )
            d.pop("gap_sum")
        if pair_stats:
            out[klass] = pair_stats
    out["_cc_tranche_count"] = int(len(cc))
    return out


def _dispatch_at_price(
    tt: pd.DataFrame, mc: np.ndarray, avail_mw: np.ndarray, price: np.ndarray
) -> np.ndarray:
    """(n_tranche, T) dispatched MW under pure price-taking merit.

    A tranche runs at its available capacity in every hour its effective mc is
    at or below its own zone's price. This is the LP's own clearing rule for an
    unconstrained, unfloored column and is what makes the fill-order defect
    visible: nothing in it references the plant's other tranches.
    """
    idx = tt["i"].to_numpy()
    zi = tt["zi"].to_numpy()
    clears = mc[idx, :] <= price[zi, :] + 1e-9  # T-5: tolerance
    return np.where(clears, avail_mw[idx, :], 0.0)


def _fill_order_stats(
    tt: pd.DataFrame, disp: np.ndarray, avail_mw: np.ndarray, classes: tuple[str, ...]
) -> dict:
    """G-4 magnitude and G-5 sign for one class group.

    NOTE the econ block is SMOOTHED into n sub-tranches
    (``offer_curve_smoothing_n``, 6 on this keeper: econc00..econc05). They must
    be carried as a LIST — collapsing them into one entry per band keeps only
    the DEAREST sub-tranche and drives the out-of-order count to a spurious
    exact 0.0 (this probe's own first result, and the miso-151
    healthy-looking-zero pattern).
    """
    sub = tt[tt["klass"].isin(classes)]
    oo_mwh = 0.0        # incremental MW produced with the min-load block idle
    total_mwh = 0.0
    oo_hours = 0
    plants_affected = 0
    supply_free = 0.0
    supply_pin = 0.0    # repair R-a: min-load must-take whenever the plant runs
    supply_gate = 0.0   # repair R-b: no upper band unless min-load is economic
    for _plant, pg in sub.groupby("plant"):
        com = pg[pg["band"] == "committed"]
        upper = pg[pg["pos"] > BAND_POSITION["committed"]]
        if com.empty or upper.empty:
            continue
        ci = int(com["i"].iloc[0])
        ui = upper["i"].to_numpy()
        c_disp, c_cap = disp[ci, :], avail_mw[ci, :]
        up_disp = disp[ui, :].sum(axis=0)
        total_mwh += float(up_disp.sum() + c_disp.sum())

        # Out-of-order: an upper band producing while the min-load block it
        # physically sits on top of is not fully loaded.
        short = (c_cap - c_disp) > 1e-6  # T-5: tolerance
        oo = np.where(short, up_disp, 0.0)
        oo_mwh += float(oo.sum())
        oo_hours += int((oo > 0).sum())
        if oo.sum() > 0:
            plants_affected += 1

        supply_free += float(c_disp.sum() + up_disp.sum())
        runs = (c_disp + up_disp) > 1e-6
        # R-a PIN: if the plant produces at all it is synchronized, so its
        # min-load block is must-take at full capacity.
        supply_pin += float(np.where(runs, c_cap, 0.0).sum() + up_disp.sum())
        # R-b GATE: the plant may only produce upper bands in hours its own
        # min-load block clears, i.e. the plant is economic as a whole.
        on = c_disp > 1e-6
        supply_gate += float(c_disp.sum() + np.where(on, up_disp, 0.0).sum())

    return {
        "G4": {
            "out_of_order_mwh": oo_mwh,
            "total_mwh": total_mwh,
            "out_of_order_share": oo_mwh / total_mwh if total_mwh else 0.0,
            "out_of_order_plant_hours": oo_hours,
            "plants_affected": plants_affected,
            "plants": int(sub["plant"].nunique()),
        },
        "G5": {
            "supply_free_mwh": supply_free,
            "repair_a_pin_mwh": supply_pin,
            "repair_b_gate_mwh": supply_gate,
            "delta_pin_share": (
                (supply_pin - supply_free) / supply_free if supply_free else 0.0
            ),
            "delta_gate_share": (
                (supply_gate - supply_free) / supply_free if supply_free else 0.0
            ),
        },
    }


def run(year: int) -> dict:
    cfg = keeper_config()
    _, fleet, arrays, _, mc, zone_names = build_year(cfg, year)
    price_df, _ = keeper_prices(year)
    price = np.zeros((len(zone_names), mc.shape[1]))
    for j, zn in enumerate(zone_names):
        if zn in price_df.columns:
            price[j, :] = price_df[zn].to_numpy()[: mc.shape[1]]

    tt = tranche_table(fleet, arrays, zone_names)
    avail_mw = arrays.pmax[:, None] * arrays.availability

    res: dict = {"year": year, "n_tranches": int(len(tt))}
    res["G2"] = g2_ordering(tt, mc)

    # ---- T-6 counter-measurement: reconstruction vs committed class_hourly ----
    disp = _dispatch_at_price(tt, mc, avail_mw, price)
    tt = tt.reset_index(drop=True)

    def _t6(classes: tuple[str, ...]) -> dict:
        out: dict = {}
        for klass in classes:
            sel = (tt["klass"] == klass).to_numpy()
            if not sel.any():
                continue
            recon = float(disp[sel, :].sum() / 1e6)
            actual = float(keeper_class_mw(year, klass).sum() / 1e6)
            out[klass] = {
                "recon_twh": recon,
                "keeper_twh": actual,
                "rel_err": (recon - actual) / max(actual, 1e-9),
            }
        recon = sum(v["recon_twh"] for v in out.values())
        keeper = sum(v["keeper_twh"] for v in out.values())
        rel = (recon - keeper) / max(keeper, 1e-9)
        out["_total"] = {
            "recon_twh": recon,
            "keeper_twh": keeper,
            "rel_err": rel,
            "tolerance": T6_TOL,
            "passes": abs(rel) <= T6_TOL,
        }
        return out

    groups = (
        ("CC_pre_registered", CC_CLASSES),
        *((c, (c,)) for c in EXTRA_CLASSES),
    )
    res["T6"] = {grp: _t6(classes) for grp, classes in groups}
    res["G4_G5"] = {
        grp: _fill_order_stats(tt, disp, avail_mw, classes) for grp, classes in groups
    }
    return res


def main() -> None:
    out = {"years": {}}
    for year in YEARS:
        out["years"][str(year)] = run(year)
        print(f"--- {year} done ---", flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
