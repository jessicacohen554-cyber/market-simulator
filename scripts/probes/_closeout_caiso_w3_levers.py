"""Close-out CAISO w3, phase 0 (ZERO LP): size two measured-input levers on the w2 probe bundle.

Control: the w2 probe ``results/calibration/closeout_caiso_w2_a1_span`` legs
(``closeout_caiso_w2_a1_<y>``), i.e. the keeper recipe + the R-63 unprinted arm.

L1  2021 own measured DSW clean depths. 2021 is the only scored year whose four
    DSW clean rungs ride the pooled 2023-25 static depth (2022-25 carry their
    own rows). The rungs' own derives (``--extra-years 2021``, unchanged
    statistic) give surplus 6,644 / overnight 6,892 / daytime 7,426 /
    late-evening 7,288 MW against static 5,192 / 6,187 / 5,733 / 6,415.
    First-order added DSW import = Σ over 2021 hours where the active clean rung
    is AT its capability, the corridor is not binding and the rung's offer is
    below λ_SP15, of the capability increase (Δdepth, net of nothing else).

L2  Within-month daily shape on the unprinted-hour formula hub's gas operand.
    The R-CAISO-18 formula prices Palo Verde as gas_AZ(MONTH) x HR x shape; AZ's
    Feb-2021 delivered-to-power gas is $10.28 (the Uri spike averaged over the
    month), which prices every February hour. L2 multiplies the monthly AZ level
    by the measured CA Composite citygate daily shape (flow-date staircase, the
    keeper's own CA gas construction), month-mean preserving, so the measured
    monthly level is kept and the spike lands on the days it printed.
    First-order at fixed duals, every hub-priced WECC_DSW tranche's offer moves
    by Δhub(t) = hub(t) x (f(day) - 1) in unprinted hours.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w3_levers.py [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]

from market_sim.data.eia930.envelopes import measured_intertie_hub_unprinted_year_mask  # noqa: E402
from market_sim.data.fuel.hubs import _caiso_citygate_daily_dated, _flow_date_staircase  # noqa: E402
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LEG = ROOT / "results/calibration/closeout_caiso_w2_a1_{y}/hourly"
T = 8760
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
DAY = np.arange(T) // 24
BIND_TOL = 1.0
CLEAN = (
    "DSW_surplus_clean",
    "DSW_overnight_clean",
    "DSW_daytime_clean",
    "DSW_lateevening_clean",
)
DEPTH_2021 = {  # rung -> (measured 2021, static in force)
    "DSW_surplus_clean": (6644.0, 5192.0),
    "DSW_overnight_clean": (6892.0, 6187.0),
    "DSW_daytime_clean": (7426.0, 5733.0),
    "DSW_lateevening_clean": (7288.0, 6415.0),
}
NOT_HUB_PRICED = ("DSW_solar_PV",)


def _leg(year: int):
    """Wide per-unit mw / cap / mc frames for WECC_DSW, the zonal duals and the binding mask."""
    um = pd.read_parquet(
        LEG.as_posix().format(y=year) + f"/unit_marginal_{year}.parquet",
        columns=["unit_id", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    u = um[um.zone.astype(str) == "WECC_DSW"].copy()
    u["n"] = u.unit_id.astype(str).str[len("WECC_DSW_") :]
    wide = {
        c: u.pivot_table(index="hour", columns="n", values=c, aggfunc="mean").reindex(
            range(T)
        )
        for c in ("mw", "cap_mw", "mc")
    }
    s = pd.read_parquet(
        LEG.as_posix().format(y=year) + f"/system_{year}.parquet",
        columns=["zone", "hour", "price"],
    )
    lam = {
        z: s[s.zone == z].set_index("hour").price.reindex(range(T)).to_numpy()
        for z in ("WECC_DSW", "SP15_rest")
    }
    binding = (lam["SP15_rest"] - lam["WECC_DSW"]) > BIND_TOL
    return wide, lam, binding


def l1_reach() -> dict:
    """First-order added DSW import from 2021 own depths (rung at cap, corridor open, offer < λ)."""
    wide, lam, binding = _leg(2021)
    out = {}
    tot = 0.0
    for rung, (meas, static) in DEPTH_2021.items():
        mw, cap, mc = (
            wide[c][rung].fillna(0).to_numpy() for c in ("mw", "cap_mw", "mc")
        )
        armed = cap > 1
        at_cap = armed & (mw >= cap - 1)
        clears = (
            np.nan_to_num(wide["mc"][rung].to_numpy(), nan=np.inf) < lam["SP15_rest"]
        )
        # capability scales with depth (cap = depth - netted firm/sibling capability)
        add = np.where(at_cap & ~binding & clears, meas - static, 0.0)
        out[rung] = {
            "armed_hours": int(armed.sum()),
            "at_cap_open_clearing_hours": int((at_cap & ~binding & clears).sum()),
            "first_order_added_twh": round(float(add.sum() / 1e6), 3),
        }
        tot += add.sum() / 1e6
    out["total_first_order_added_twh"] = round(tot, 3)
    return out


def ca_daily_shape(year: int) -> np.ndarray:
    """Hourly month-mean-preserving factor from the CA Composite citygate daily flow-date staircase."""
    dated = _caiso_citygate_daily_dated(None)
    daily = _flow_date_staircase(dated.get(year, {}), year)
    f = np.ones(T)
    if daily is None:
        return f
    daily = np.asarray(daily, dtype=float)[:365]
    mon_of_day = np.repeat(np.arange(1, 13), _DAYS)
    fd = np.ones(365)
    for m in range(1, 13):
        sel = mon_of_day == m
        mean = np.nanmean(daily[sel])
        if np.isfinite(mean) and mean > 0:
            fd[sel] = daily[sel] / mean
    return fd[DAY]


def l2_reach(year: int) -> dict:
    """First-order DSW volume change from the daily-shaped formula-hub gas operand."""
    wide, lam, binding = _leg(year)
    mask = measured_intertie_hub_unprinted_year_mask(
        "CAISO", year, T, "PALOVRDE", gap_fill_measured_dam=True
    )
    mask = np.zeros(T, bool) if mask is None else mask
    f = ca_daily_shape(year)
    hub = wide["mc"][
        "DSW_overnight_clean"
    ].to_numpy()  # formula hub + ε (no wheel, EF 0)
    dhub = np.where(mask, hub * (f - 1.0), 0.0)
    add = drop = 0.0
    by_month = np.zeros(12)
    for n in wide["mw"].columns:
        if n in NOT_HUB_PRICED or n.startswith("export"):
            continue
        mw, cap, mc = (wide[c][n].fillna(0).to_numpy() for c in ("mw", "cap_mw", "mc"))
        new = mc + dhub
        a = np.where(
            mask & ~binding & (new < lam["SP15_rest"] - 0.01) & (mw < cap - 1e-6),
            cap - mw,
            0.0,
        )
        d = np.where(mask & (new > lam["SP15_rest"] + 0.01) & (mw > 1e-6), mw, 0.0)
        add += a.sum()
        drop += d.sum()
        for m in range(12):
            by_month[m] += (a - d)[MONTH == m + 1].sum()
    return {
        "unprinted_hours": int(mask.sum()),
        "factor_range": [round(float(f[mask].min()), 3), round(float(f[mask].max()), 3)]
        if mask.any()
        else None,
        "first_order_add_twh": round(add / 1e6, 3),
        "first_order_drop_twh": round(drop / 1e6, 3),
        "first_order_net_twh": round((add - drop) / 1e6, 3),
        "net_by_month_twh": [round(v / 1e6, 2) for v in by_month],
    }


def main() -> None:
    """Size L1 (2021) and L2 (2019-2021) and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out", default=str(ROOT / "docs/records/caiso/closeout-caiso-w3/_levers.json")
    )
    a = ap.parse_args()
    meas = corridor_net_import(years=(2019, 2020, 2021))
    res = {
        "L1_2021_own_depths": l1_reach(),
        "L2_daily_shape": {str(y): l2_reach(y) for y in (2019, 2020, 2021)},
    }
    res["eia930_dsw_twh"] = {
        str(y): round(float(np.nansum(meas.loc[y]["WECC_DSW"]) / 1e6), 2)
        for y in (2019, 2020, 2021)
    }
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
