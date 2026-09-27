"""soco-81 zero-LP census + greedy for ``coal_econ_marginal_hr_two_sided``.

Rule 32 ``[R-SHARD]`` (a): never solves.

``fleet``  — ``fleet_only`` rebuild of the soco76 keeper recipe per year, flag off
            vs on. Asserts ``pmax`` / ``min_gen`` / ``availability`` identical
            for every unit; ``mc`` moves only on coal tranches of plants with a
            measured must-run floor, and only on ``_committed`` / ``_econ*``;
            each moved tranche's heat rate equals the plant average x the
            artifact ratio. Writes ``docs/handoffs/r-soco/soco81_fleet_census.json``.

``greedy`` — price-taker greedy, baseline-differenced. For each moved plant, the
            tranche set is dispatched against its zone's committed P1 price at the
            keeper offers and at the arm offers (``max(run, min_gen)``); the
            hourly difference is added to the plant's committed payload MW
            (clipped to [0, nameplate]) and taken from CC_REGULAR. C1 through
            ``calibration_verdict.score_fuelmix`` on the keeper payload; C4
            through ``_soco73_phase0.c4_coal``. Prices are held fixed (soco-72
            measured the LP moving ~3x its greedy). The soco76 legs are gone
            from origin, so the committed payload stands in for unit hourlies.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco81_census.py fleet
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco81_census.py greedy
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "scripts" / "probes"))
sys.path.insert(0, str(_ROOT / "src"))

import _soco73_phase0 as s73  # noqa: E402
import calibration_verdict as cv  # noqa: E402

KEEPER = "2026-09-27-soco76-egrid-identity-hr"
SPAN = _ROOT / "results/calibration/soco76_span"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
T = 8760
OUT = _ROOT / "docs/handoffs/r-soco"
FLAG = "coal_econ_marginal_hr_two_sided"
RATIO = _ROOT / "data/raw/_processed-legacy/coal_incremental_hr_ratio_SOCO.csv"
RECIPE_SETS = (
    "eia860_vintage_tracks_solve_year",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "egrid_identity_heat_rates",
)
SCOPED = ("_committed", "_commitcyc", "_econlo", "_econhi", "_econ")

s73.KEEPER_ID = KEEPER
s73.SPAN = SPAN


def build(year: int, arm: bool) -> dict:
    """fleet_only rebuild on the soco76 recipe, optionally with the flag armed."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((SPAN / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    # The keeper recipe's --set flags (PRECOMMIT-soco-76 §5), which meta.json
    # does not carry: routed through the same prb_overrides channel --set uses.
    kw.setdefault("prb_overrides", {}).update({k: True for k in RECIPE_SETS})
    if arm:
        kw[FLAG] = True
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    av = np.asarray(fa.availability, float)
    return dict(
        ids=list(map(str, fa.unit_ids)),
        plant=np.asarray(fa.plant_code).astype(int),
        hr=np.asarray(fa.heat_rate, float),
        mc=mc if mc.ndim == 2 else np.repeat(mc[:, None], T, axis=1),
        pmax=np.asarray(fa.pmax, float),
        mg=np.asarray(fa.min_gen, float),
        av=av,
    )


def ratios(year: int) -> dict[int, tuple[float, float]]:
    """The artifact's year row else pooled row, per plant (the loader's rule)."""
    d = pd.read_csv(RATIO)
    d = d[d.flag == "ok"]
    out = {}
    for y in (0, year):
        for r in d[d.year == y].itertuples():
            out[int(r.plant_code)] = (float(r.ratio_econ_low), float(r.ratio_econ_high))
    return out


def main_fleet() -> dict:
    """Flag off vs on per year; prints and records what moved."""
    out = {}
    for y in YEARS:
        a, b = build(y, False), build(y, True)
        assert a["ids"] == b["ids"]
        same = all(np.array_equal(a[k], b[k]) for k in ("pmax", "mg", "av"))
        moved = np.flatnonzero(np.abs(b["mc"] - a["mc"]).max(axis=1) > 1e-9)
        ids = a["ids"]
        coal = [i for i, x in enumerate(ids) if x.startswith("COAL")]
        mr_plants = {
            int(a["plant"][i]) for i in coal if ids[i].endswith(("_mustrun", "_sync"))
        }
        coal_plants = {int(a["plant"][i]) for i in coal}
        r = ratios(y)
        rows, bad = {}, []
        for i in moved:
            p, x = int(a["plant"][i]), ids[i]
            if not (x.startswith("COAL") and p in mr_plants and x.endswith(SCOPED)):
                bad.append(x)
            dmc = float(np.median(b["mc"][i] - a["mc"][i]))
            rows[x] = dict(
                hr_old=round(float(a["hr"][i]), 4),
                hr_new=round(float(b["hr"][i]), 4),
                ratio=round(float(b["hr"][i] / a["hr"][i]), 4),
                mc_old=round(float(np.median(a["mc"][i])), 3),
                mc_new=round(float(np.median(b["mc"][i])), 3),
                dmc=round(dmc, 3),
                cap_mw=round(float(a["pmax"][i]), 1),
            )
        moved_plants = sorted({int(a["plant"][i]) for i in moved})
        unmoved_mr = sorted(mr_plants - set(moved_plants))
        ok = same and not bad
        print(
            f"\n===== {y}: units {len(ids)}, mc moved {len(moved)} at plants {moved_plants}; "
            f"must-run coal plants {sorted(mr_plants)}; floorless coal {sorted(coal_plants - mr_plants)}; "
            f"must-run plants NOT moved {unmoved_mr}; pmax/min_gen/avail identical {same}; "
            f"out-of-scope moves {bad} => {'OK' if ok else 'STOP'}"
        )
        for k, v in rows.items():
            print(f"  {k}: {v}")
        out[str(y)] = dict(
            ok=bool(ok),
            units=len(ids),
            must_run_plants=sorted(mr_plants),
            floorless=sorted(coal_plants - mr_plants),
            moved=rows,
            artifact_ratio={str(p): r.get(p) for p in moved_plants},
        )
    (OUT / "soco81_fleet_census.json").write_text(
        json.dumps(out, indent=0, sort_keys=True) + "\n"
    )
    return out


def _dispatch(f: dict, idx: list[int], price: np.ndarray) -> np.ndarray:
    """Price-taker MW of tranches ``idx`` at ``price`` (respecting min_gen)."""
    tot = np.zeros(T)
    for i in idx:
        av = f["av"][i] if f["av"].ndim == 2 else np.full(T, f["av"][i])
        cap = f["pmax"][i] * av
        mg = f["mg"][i] if np.ndim(f["mg"][i]) else np.full(T, f["mg"][i])
        run = np.where(f["mc"][i] <= price + 1e-6, cap, 0.0)
        tot += np.maximum(run, np.minimum(mg, cap))
    return tot


def main_greedy() -> pd.DataFrame:
    """Greedy of the armed repricing on the keeper's committed payload + prices."""
    art = cv.load_artifacts(KEEPER)
    rows = []
    for y in YEARS:
        a, b = build(y, False), build(y, True)
        moved = np.flatnonzero(np.abs(b["mc"] - a["mc"]).max(axis=1) > 1e-9)
        plants = sorted({int(a["plant"][i]) for i in moved})
        sysd = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        price = {
            z: g.sort_values("hour").price.to_numpy(float)[:T]
            for z, g in sysd.groupby("zone")
        }
        pay = art["payload"]["years"][str(y)]["plants"]
        bench = art["bench"][y]["plants"]
        coal_dt, delta, pdelta = np.zeros(T), {}, {}
        for p in plants:
            idx = [
                i
                for i, x in enumerate(a["ids"])
                if x.startswith("COAL") and int(a["plant"][i]) == p
            ]
            bks = [
                k
                for k, v in bench.items()
                if int(str(k).split(":")[0]) == p
                and str(v.get("group", "")).startswith("COAL")
            ]
            if not bks:
                continue
            bv = bench[bks[0]]
            pk = bks[0] if bks[0] in pay else str(p)
            npl = float(bv["npl"])
            m = (
                np.frombuffer(base64.b64decode(pay[pk]["m"])[:T], dtype=np.uint8)
                * npl
                / 100.0
            )
            pz = price[bv["zone"]]
            d = _dispatch(b, idx, pz) - _dispatch(a, idx, pz)
            new = np.clip(m + d, 0.0, npl)
            add = new - m
            coal_dt += add
            cls = bv["group"]
            delta[cls] = delta.get(cls, 0.0) + add.sum() / 1e6
            delta["CC_REGULAR"] = delta.get("CC_REGULAR", 0.0) - add.sum() / 1e6
            pdelta[p] = round(add.sum() / 1e6, 3)
        c1 = s73.c1_rows(y, delta)
        for _, r in c1.iterrows():
            if abs(r.pp1 - r.pp0) > 0.005 or r.st0 != "PASS":
                rows.append(
                    dict(
                        year=y,
                        row=f"C1 {r.cls}",
                        keeper=f"{r.pp0:+.2f} {r.st0}",
                        arm=f"{r.pp1:+.2f} {r.st1}",
                    )
                )
        if y <= 2024:
            r0, n0, r1, n1 = s73.c4_coal(y, coal_dt)
            rows.append(
                dict(
                    year=y,
                    row="C4 coal r/NRMSE",
                    keeper=f"{r0:.3f}/{n0:.4f}",
                    arm=f"{r1:.3f}/{n1:.4f}",
                )
            )
        rows.append(
            dict(year=y, row="plant delta TWh", keeper="", arm=json.dumps(pdelta))
        )
    g = pd.DataFrame(rows)
    g.to_csv(OUT / "soco81_greedy.csv", index=False)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 200)
    print(g.to_string(index=False))
    return g


if __name__ == "__main__":
    {"fleet": main_fleet, "greedy": main_greedy}[sys.argv[1]]()
