"""SOCO-77 phase 0 (ZERO LP): the CT fleet's plant split as a COST-BASED START, on the soco-76 keeper legs.

Rule 32 ``[R-SHARD]`` (a): never solves. Instruments:

1. ``conduct`` — per CT_PEAKER plant x year from its OWN CEMS (CAMPD unit-level, opTime > 0 runs):
   starts, starts per unit-year, median run length, and the measured START FUEL = heat input in the
   first online hour in excess of the unit's own steady-state heat rate x that hour's gross load,
   per MW of HSL (MMBtu/MW-start). Beside it: model TWh (soco76 leg) vs EIA-923 TWh (bench).
2. ``markup`` — the keeper's live P1 start markup per CT tranche = solved ``mc`` - ``fleet_only``
   ``mc_base`` (the SOCO-65 construction), p50 over the tranche's hours, by suffix.
3. ``greedy`` — baseline-differenced price-taker greedy (SOCO-63 §4 / SOCO-64 §5) of a start cost on
   the CT ``econ*`` / ``peak`` tranches, which carry none today:
     arm N  : NREL start ($/MW, the unit's own ``startup_cost_per_mw``) / the tranche's own P1 monthly
              mean run length (``compute_monthly_markup`` v2 construction);
     arm F  : SOCO-64 §4's measured fuel-only start, $3.6/MW, over the arm-N horizon;
     arm M  : (dropped — not identifiable at hourly grain, see conduct) MEASURED start fuel ($/MW = plant's pooled CEMS start MMBtu/MW x the tranche's own fuel
              $/MMBtu) over the same horizon — the fuel-only cost-based start, a lower bound;
     arm V3 : arm N with the horizon capped at the plant's pooled CEMS median run (``fast_start_run_hours``
              v3 construction).
   Every arm's tranches are re-dispatched at the keeper offer (baseline) and at the arm offer against the
   leg's zone price; the per-hour difference is refilled / displaced over the other gas + coal classes.
   Reports scorer-exact C1 rows (``calibration_verdict.score_fuelmix`` on the keeper payload), C4 coal,
   and the per-CT-plant model vs EIA-923 split before/after.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco77_ct_start.py conduct|markup|greedy
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts" / "probes"))
sys.path.insert(0, str(_ROOT / "scripts"))
import _soco63_phase0 as s63  # noqa: E402  (unit_class_map)
import _soco73_phase0 as s73  # noqa: E402  (rebuild, c1_rows, c4_coal)

KEEPER = "2026-09-27-soco76-egrid-identity-hr"
s73.KEEPER_ID = KEEPER
s73.SPAN = _ROOT / "results/calibration/soco76_span"
s73.LEG = _ROOT / "results/calibration/soco76_{y}"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
T = 8760
CT = "CT_PEAKER"
REFILL = (
    "CC_REGULAR",
    "CT_PEAKER",
    "ST_GAS",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_WC",
    "OIL",
)
OUT = _ROOT / "docs/handoffs/r-soco"
FUEL_REF = 3.34  # $/MMBtu, SOCO-64 §4 CT mean delivered gas 2023-2025 — used ONLY to print $/MW, never in an arm


def _leg(y: int) -> pd.DataFrame:
    leg = _ROOT / f"results/calibration/soco76_{y}"
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{y}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    u["unit_id"] = u.unit_id.astype(str)
    u["g"] = u.plant_group.astype(str)
    s = pd.read_parquet(
        leg / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price"]
    )
    return u.merge(s, on=["zone", "hour"], how="left")


def _bench_ct(y: int) -> dict[int, float]:
    b = json.load(gzip.open(str(s73.BENCH).format(y=y)))["bench"]["plants"]
    out: dict[int, float] = {}
    for k, v in b.items():
        if str(v.get("group", "")) == CT:
            p = int(str(k).split(":")[0])
            out[p] = out.get(p, 0.0) + float(v.get("e_ann") or 0.0)
    return out


def _runs(on: np.ndarray) -> list[tuple[int, int]]:
    from market_sim.model.commitment import find_runs

    return find_runs(on)


def conduct() -> pd.DataFrame:
    """Per CT plant x year: CEMS starts, run length, measured start fuel; model vs EIA-923 TWh."""
    from market_sim.data.campd import states_for_iso

    cmap = s63.unit_class_map()
    cmap = cmap[cmap.cls == CT]
    rows = []
    for y in YEARS:
        fr = []
        for st in states_for_iso("SOCO"):
            p = _ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet"
            if p.exists():
                fr.append(
                    pd.read_parquet(
                        p,
                        columns=[
                            "facilityId",
                            "unitId",
                            "date",
                            "hour",
                            "opTime",
                            "grossLoad",
                            "heatInput",
                        ],
                    )
                )
        c = pd.concat(fr)
        c["facilityId"] = c.facilityId.astype(int)
        c["unitId"] = c.unitId.astype(str)
        c = c.merge(
            cmap, left_on=["facilityId", "unitId"], right_on=["plant_code", "unit_id"]
        )
        c = c.sort_values(["plant_code", "unit_id", "date", "hour"])
        for (p, u), g in c.groupby(["plant_code", "unit_id"]):
            op = g.opTime.fillna(0).to_numpy(float)
            on = op > 0
            gl = g.grossLoad.fillna(0).to_numpy(float)
            hi = g.heatInput.fillna(0).to_numpy(float)
            runs = _runs(on)
            full = on & (op >= 0.99) & (gl > 0)
            hsl = (
                float(np.percentile(gl[full], 97))
                if full.sum() > 20
                else float(g.cap_mw.iloc[0])
            )
            # steady-state HR from hours >= 2 into a run at full opTime
            steady = np.zeros_like(on)
            for s, e in runs:
                steady[s + 2 : e] = True
            ss = steady & full
            hr_ss = hi[ss].sum() / gl[ss].sum() if gl[ss].sum() > 0 else np.nan
            excess = (
                [hi[s] - hr_ss * gl[s] for s, e in runs] if np.isfinite(hr_ss) else []
            )
            L = np.array([e - s for s, e in runs]) if runs else np.array([])
            rows.append(
                dict(
                    year=y,
                    plant=int(p),
                    unit=u,
                    starts=len(runs),
                    run_med=float(np.median(L)) if len(L) else np.nan,
                    on_h=int(L.sum()) if len(L) else 0,
                    cems_twh=gl.sum() / 1e6,
                    hsl=hsl,
                    hr_ss=hr_ss,
                    start_mmbtu=float(np.sum(excess)),
                    start_mmbtu_med=float(np.median(excess)) if excess else np.nan,
                )
            )
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "soco77_ct_conduct_units.csv", index=False)
    return d


def plant_table(d: pd.DataFrame) -> pd.DataFrame:
    """Aggregate unit conduct to plant x year and join model / EIA-923 TWh."""
    g = (
        d.groupby(["year", "plant"])
        .agg(
            units=("unit", "nunique"),
            starts=("starts", "sum"),
            run_med=("run_med", "median"),
            cems_twh=("cems_twh", "sum"),
            hsl=("hsl", "sum"),
            start_mmbtu=("start_mmbtu", "sum"),
        )
        .reset_index()
    )
    g["starts_per_unit"] = g.starts / g.units
    g["start_mmbtu_per_mw"] = g.start_mmbtu / g.starts.clip(lower=1) / (g.hsl / g.units)
    rows = []
    for y in YEARS:
        u = _leg(y)
        m = u[u.g == CT].groupby("plant_code").mw.sum() / 1e6
        b = _bench_ct(y)
        for p in sorted(set(m.index) | set(b)):
            rows.append(
                dict(
                    year=y,
                    plant=int(p),
                    model_twh=float(m.get(p, 0.0)),
                    eia923_twh=float(b.get(p, 0.0)),
                )
            )
    t = pd.DataFrame(rows).merge(g, on=["year", "plant"], how="left")
    return t


def pooled_plant(d: pd.DataFrame) -> pd.DataFrame:
    """Pooled 2019-2025 per plant: CEMS median run and start MMBtu/MW (the arm inputs)."""
    x = d[d.starts > 0]
    r = x.groupby("plant").apply(
        lambda g: pd.Series(
            dict(
                run_med=float(np.average(g.run_med, weights=g.starts)),
                start_mmbtu_per_mw=float(
                    g.start_mmbtu.sum() / g.starts.sum() / (g.hsl.mean())
                ),
                starts=int(g.starts.sum()),
            )
        ),
        include_groups=False,
    )
    return r


_RB: dict = {}


def _rebuild(y: int) -> dict:
    if y not in _RB:
        _RB[y] = s73.rebuild(y, None)
    return _RB[y]


def markup(y: int, u: pd.DataFrame) -> pd.DataFrame:
    """Keeper live P1 start markup per CT tranche: p50 over hours of (solved mc - mc_base)."""
    fl = _rebuild(y)
    idx = {x: i for i, x in enumerate(fl["unit_ids"])}
    mcb = fl["mc"]
    out = []
    for uid, g in u[u.g == CT].groupby("unit_id"):
        i = idx[uid]
        base = mcb[i] if mcb.ndim == 1 else mcb[i, g.hour.to_numpy()]
        mk = g.mc.to_numpy(float) - base
        out.append(
            dict(
                unit_id=uid,
                plant=int(g.plant_code.iloc[0]),
                sfx=uid.rsplit("_", 1)[1],
                mk_p50=float(np.median(mk)),
                mk_max=float(mk.max()),
                startup=fl["stash"]["startup"].get(uid, np.nan),
                twh=float(g.mw.sum() / 1e6),
            )
        )
    return pd.DataFrame(out)


def _monthly_run_h(mw: np.ndarray, pmax: float) -> np.ndarray:
    """compute_monthly_markup's horizon: per-month mean run length of mw > 5% pmax, per hour."""
    from market_sim.model.commitment import _month_bounds

    h = np.zeros(T)
    for a, b in _month_bounds(T):
        r = _runs(mw[a:b] > 0.05 * pmax)
        h[a:b] = np.mean([e - s for s, e in r]) if r else 0.0
    return h


def greedy(y: int, arm: str, pooled: pd.DataFrame) -> dict:
    """Arm-minus-baseline price-taker greedy of a start cost on CT econ*/peak tranches."""
    u = _leg(y)
    fl = _rebuild(y)
    idx = {x: i for i, x in enumerate(fl["unit_ids"])}
    hr = fl["stash"]["heat_rate"]
    vom = fl["stash"]["vom"]
    mine = (u.g == CT) & ~u.unit_id.str.endswith("_committed")
    x = u[mine]
    delta_t = np.zeros(T)
    plant_d: dict[int, float] = {}
    for uid, g in x.groupby("unit_id"):
        i = idx[uid]
        p = int(g.plant_code.iloc[0])
        g = g.set_index("hour").reindex(range(T))
        mc0 = g.mc.to_numpy(float)
        cap = g.cap_mw.fillna(0).to_numpy(float)
        pr = g.price.to_numpy(float)
        mw = g.mw.fillna(0).to_numpy(float)
        pmax = float(np.nanmax(cap)) if np.nanmax(cap) > 0 else 1.0
        horizon = _monthly_run_h(mw, pmax)
        meas = float(pooled.run_med.get(p, np.nan)) if p in pooled.index else np.nan
        if arm == "V3":
            ceil_ = (
                meas
                if np.isfinite(meas)
                else float(np.average(pooled.run_med, weights=pooled.starts))
            )
            horizon = np.where(horizon > 0, np.minimum(horizon, ceil_), ceil_)
        elif arm in ("N", "M"):
            # a month with no P1 run: v2 amortizes over 1 h (compute_monthly_markup max(avg_run, 1))
            pass
        if arm == "F":
            # SOCO-64 §4 measured FUEL-ONLY start (CEMS warm-up heat to LSL, 1.07 MMBtu/MW at
            # $3.34/MMBtu = $3.6/MW, CT class p50 2023-2025), over the arm-N horizon.
            su = 3.6
        elif arm in ("N", "V3"):
            # the SAME registered start the plant's _committed anchor carries (rule 19): the
            # fleet's BIN_STARTUP_COST_PER_MW["CT_PEAKER"]; econ/peak carry 0 today.
            from market_sim.data.fleet.assembly import BIN_STARTUP_COST_PER_MW

            su = float(BIN_STARTUP_COST_PER_MW.get(CT, 0.0))
        else:  # M: measured start fuel at the tranche's own fuel price
            fuel = (np.nanmedian(mc0) - vom[i]) / hr[i]
            smw = (
                float(pooled.start_mmbtu_per_mw.get(p, np.nan))
                if p in pooled.index
                else np.nan
            )
            if not np.isfinite(smw):
                smw = float(
                    np.average(pooled.start_mmbtu_per_mw, weights=pooled.starts)
                )
            su = max(smw, 0.0) * fuel
        mk = su / np.maximum(horizon, 1.0)
        mc1 = mc0 + mk
        r0 = np.where(mc0 <= pr + 1e-6, cap, 0.0)
        r1 = np.where(mc1 <= pr + 1e-6, cap, 0.0)
        d = np.nan_to_num(r1 - r0)
        delta_t += d
        plant_d[p] = plant_d.get(p, 0.0) + d.sum() / 1e6
    oth = u[u.g.isin(REFILL) & ~mine]
    up = oth.assign(head=(oth.cap_mw - oth.mw).clip(lower=0))
    up = up[up["head"] > 0.01][["hour", "g", "plant_code", "mc", "head"]].sort_values(
        ["hour", "mc"]
    )
    up["cum"] = up.groupby("hour")["head"].cumsum()
    need = np.clip(-delta_t, 0, None)[up.hour.to_numpy()]
    up["take"] = np.clip(
        need - (up.cum.to_numpy() - up["head"].to_numpy()), 0, up["head"].to_numpy()
    )
    down = oth[oth.mw > 0.01][["hour", "g", "plant_code", "mc", "mw"]].sort_values(
        ["hour", "mc"], ascending=[True, False]
    )
    down["cum"] = down.groupby("hour").mw.cumsum()
    need2 = np.clip(delta_t, 0, None)[down.hour.to_numpy()]
    down["take"] = np.clip(
        need2 - (down.cum.to_numpy() - down.mw.to_numpy()), 0, down.mw.to_numpy()
    )
    dcls = (
        up.groupby("g")["take"].sum().sub(down.groupby("g")["take"].sum(), fill_value=0)
    ) / 1e6
    dcls[CT] = dcls.get(CT, 0.0) + delta_t.sum() / 1e6
    for fr, sgn in ((up, 1.0), (down, -1.0)):
        f = fr[fr.g == CT].groupby("plant_code")["take"].sum() / 1e6
        for p, v in f.items():
            plant_d[int(p)] = plant_d.get(int(p), 0.0) + sgn * float(v)
    coal_t = np.zeros(T)
    for fr, sgn in ((up, 1.0), (down, -1.0)):
        f = fr[fr.g.str.startswith("COAL")]
        coal_t += (
            sgn * f.groupby("hour")["take"].sum().reindex(range(T)).fillna(0).to_numpy()
        )
    unmet = (np.clip(-delta_t, 0, None).sum() - up["take"].sum()) / 1e6
    return dict(
        delta={k: float(v) for k, v in dcls.items()},
        plant=plant_d,
        coal_t=coal_t,
        unmet=float(unmet),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["conduct", "markup", "greedy"])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--arms", nargs="+", default=["N", "V3", "F"])
    a = ap.parse_args()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.max_rows", 400)
    uc = OUT / "soco77_ct_conduct_units.csv"
    d = (
        pd.read_csv(uc, dtype={"unit": str})
        if uc.exists() and a.mode != "conduct"
        else conduct()
    )
    pooled = pooled_plant(d)
    if a.mode == "conduct":
        t = plant_table(d)
        t.to_csv(OUT / "soco77_ct_plant_split.csv", index=False)
        cols = [
            "year",
            "plant",
            "model_twh",
            "eia923_twh",
            "cems_twh",
            "units",
            "starts_per_unit",
            "run_med",
            "start_mmbtu_per_mw",
        ]
        print(t[cols].round(3).to_string(index=False))
        print("\npooled 2019-2025 per plant:\n", pooled.round(2).to_string())
        return
    if a.mode == "markup":
        res = []
        for y in a.years:
            m = markup(y, _leg(y))
            m["year"] = y
            res.append(m)
            s = m.groupby("sfx").agg(
                n=("unit_id", "size"),
                mk_p50=("mk_p50", "median"),
                mk_max=("mk_max", "max"),
                startup=("startup", "median"),
            )
            print(f"== {y}\n{s.round(2).to_string()}")
        pd.concat(res).to_csv(OUT / "soco77_ct_markup.csv", index=False)
        return
    out: dict = {}
    split = pd.read_csv(OUT / "soco77_ct_plant_split.csv")
    for y in a.years:
        for arm in a.arms:
            g = greedy(y, arm, pooled)
            r0, n0, r1, n1 = s73.c4_coal(y, g["coal_t"])
            c1 = s73.c1_rows(y, g["delta"])
            c1["m0"] = c1.pp0.abs()
            print(
                f"\n===== {y} arm {arm}  unmet {g['unmet']:.4f} TWh  C4 coal {n0:.4f} -> {n1:.4f}"
            )
            print(
                "  class d TWh: "
                + "  ".join(
                    f"{k} {v:+.3f}"
                    for k, v in sorted(g["delta"].items())
                    if abs(v) > 1e-3
                )
            )
            print(
                c1[["cls", "actual", "keeper", "arm", "pp0", "pp1", "st0", "st1"]]
                .round(3)
                .to_string(index=False)
            )
            sp = split[split.year == y].set_index("plant")
            pdl = pd.Series(g["plant"]).rename("d_twh")
            pt = sp[["model_twh", "eia923_twh"]].join(pdl, how="outer").fillna(0)
            pt["arm_twh"] = pt.model_twh + pt.d_twh
            e0 = (pt.model_twh - pt.eia923_twh).abs().sum()
            e1 = (pt.arm_twh - pt.eia923_twh).abs().sum()
            print(f"  CT plant split sum|model-923|: {e0:.3f} -> {e1:.3f} TWh")
            print(
                pt[pt[["model_twh", "eia923_twh", "arm_twh"]].abs().max(axis=1) > 0.1]
                .round(3)
                .to_string()
            )
            out.setdefault(str(y), {})[arm] = dict(
                delta=g["delta"],
                c4=[n0, n1],
                unmet=g["unmet"],
                split_abs_err=[e0, e1],
                c1=c1.drop(columns="m0").round(4).to_dict("records"),
                plant=pt.round(4).reset_index().to_dict("records"),
            )
    prev = OUT / "soco77_ct_start_greedy.json"
    if prev.exists():
        old = json.loads(prev.read_text())
        for y, v in old.items():
            for k, w in v.items():
                out.setdefault(y, {}).setdefault(k, w)
    (OUT / "soco77_ct_start_greedy.json").write_text(
        json.dumps(out, indent=0, default=float) + "\n"
    )


if __name__ == "__main__":
    main()
