"""SOCO-79 (ZERO LP): fleet-grain census of the eGRID family-rate VINTAGE, three keepers.

Rule 32 ``[R-SHARD]`` (a): never solves. Owner scoping question (3) from soco-78 §5: the plant-grain
eGRID join is year-matched since F1 (``egrid_vintage_for_year``) while
``egrid_family_heat_rates_<ISO>.csv`` is pinned to ``APPLIED_VINTAGE = 2023``. For every keeper that
arms ``egrid_family_heat_rates`` this probe rebuilds each keeper year ``fleet_only`` on the keeper's
own recipe (``bundle_fleet.reconstruct_bundle_fleet``) under three arms, and differences the
per-unit ``heat_rate`` / ``mc_base``:

  A  today      : the 2023 applied artifact, ``flag == ok`` rows (the shipped loader, unpatched).
  B  year-match : the ``_vintages.csv`` rows at ``egrid_vintage_for_year(year)``, ``flag == ok``.
  C  B + class  : B, and a family ``out_of_window`` at that vintage takes the ``HEAT_RATE_BINS``
                  class default (the row loop's own ``heat_rate <= 0`` fall-back) instead of the
                  plant blend.

B and C are implemented by monkeypatching ``eia860.egrid_family_heat_rates_for`` — no ``src`` edit.
Arm C passes ``-1.0`` for an out-of-window key, which ``_apply_egrid_family_heat_rates`` writes to
the frame and the row loop's ``heat_rate <= 0`` branch replaces with the class default; every
downstream measured mechanism keeps its precedence exactly as for a real family rate.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco79_family_vintage.py census \
        --iso SOCO|CAISO|NYISO
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco79_family_vintage.py greedy
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (_ROOT, _ROOT / "src", _ROOT / "scripts", _ROOT / "scripts" / "probes"):
    sys.path.insert(0, str(_p))

OUT = _ROOT / "docs/records/soco/r-soco"
PROC = _ROOT / "data/raw/_processed-legacy"
T = 8760

#: Current designated keeper bundles (frontend/data/backcast/keepers/<ISO>.json at 571147d0) and
#: the fold bundles carrying their out-of-span years. NYISO's keeper moved nyisonext3 -> nyisonext6
#: the same day (PR #6786); both arm the flag.
BUNDLES: dict[str, list[tuple[str, tuple[int, ...]]]] = {
    "SOCO": [("soco76_span", (2019, 2020, 2021, 2022, 2023, 2024, 2025))],
    "CAISO": [
        ("rcaiso5_XE_tp_2019_2021", (2019, 2020, 2021)),
        ("rcaiso5_XE_span", (2022, 2023, 2024, 2025)),
    ],
    "NYISO": [
        ("nyisonext6_2021", (2021,)),
        ("nyisonext6_span", (2022, 2023, 2024, 2025)),
    ],
}


def _rates(iso: str, vintage: int, arm: str) -> dict[tuple[int, str], float]:
    """Arm B / C replacement for ``egrid_family_heat_rates_for`` at one vintage."""
    d = pd.read_csv(PROC / f"egrid_family_heat_rates_{iso}_vintages.csv")
    d = d[d.vintage == vintage]
    out = {
        (int(r.plant_id), str(r.family)): float(r.heat_rate_mmbtu_mwh)
        for r in d[d.flag == "ok"].itertuples()
        if float(r.heat_rate_mmbtu_mwh) > 0.0
    }
    if arm == "C":
        for r in d[d.flag == "out_of_window"].itertuples():
            out[(int(r.plant_id), str(r.family))] = -1.0
    return out


@contextlib.contextmanager
def _arm(iso: str, year: int, arm: str):
    from market_sim.data.egrid import egrid_vintage_for_year
    from market_sim.data.fleet import eia860

    orig = eia860.egrid_family_heat_rates_for
    if arm != "A":
        v = egrid_vintage_for_year(year)
        eia860.egrid_family_heat_rates_for = lambda _iso: _rates(iso, v, arm)
    try:
        yield
    finally:
        eia860.egrid_family_heat_rates_for = orig


def rebuild(bundle: str, year: int, iso: str, arm: str) -> pd.DataFrame:
    """fleet_only rebuild of one keeper year under one arm; per-unit frame."""
    from scripts.lib.bundle_fleet import clear_fleet_caches, reconstruct_bundle_fleet

    clear_fleet_caches()
    with (
        _arm(iso, year, arm),
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        st, _ = reconstruct_bundle_fleet(
            _ROOT / "results/calibration" / bundle, year, verbose=False
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    return pd.DataFrame(
        dict(
            unit_id=list(map(str, fa.unit_ids)),
            plant=np.asarray(fa.plant_code).astype(int),
            cls=[str(g) for g in fa.plant_group],
            pmax=np.asarray(fa.pmax, float),
            hr=np.asarray(fa.heat_rate, float),
            mc=np.median(mc, axis=1) if mc.ndim == 2 else mc,
        )
    )


def census(iso: str) -> dict:
    """Per year: rows / MW whose heat rate moves A->B and B->C, and McDonough 710 rows."""
    res: dict = {}
    frames = []
    for bundle, years in BUNDLES[iso]:
        for y in years:
            try:
                f = {a: rebuild(bundle, y, iso, a) for a in ("A", "B", "C")}
            except Exception as e:  # noqa: BLE001 — a keeper-recipe rebuild that fails is reported, not hidden
                res[str(y)] = dict(error=f"{type(e).__name__}: {str(e)[:300]}")
                print(
                    f"{iso} {y} [{bundle}] REBUILD FAILED: {res[str(y)]['error']}",
                    flush=True,
                )
                continue
            m = f["A"].merge(
                f["B"],
                on=["unit_id", "plant", "cls", "pmax"],
                how="outer",
                suffixes=("_A", "_B"),
                indicator=True,
            )
            m = m.merge(
                f["C"].rename(columns={"hr": "hr_C", "mc": "mc_C"}),
                on=["unit_id", "plant", "cls", "pmax"],
                how="outer",
            )
            m["year"] = y
            m["bundle"] = bundle
            assert (m._merge == "both").all(), (
                f"{iso} {y}: unit sets differ across arms"
            )
            # hr == 0 is a legitimate non-thermal row; a negative hr would be the arm-C sentinel
            # leaking past the row loop's class-default fall-back.
            assert (m[["hr_A", "hr_B", "hr_C"]] >= 0).all().all(), (
                f"{iso} {y}: negative hr"
            )
            frames.append(m.drop(columns="_merge"))
            row = {}
            for lab, a, b in (
                ("AB", "hr_A", "hr_B"),
                ("BC", "hr_B", "hr_C"),
                ("AC", "hr_A", "hr_C"),
            ):
                mv = m[(m[a] - m[b]).abs() > 1e-9]
                row[lab] = dict(
                    rows=int(len(mv)),
                    mw=round(float(mv.pmax.sum()), 1),
                    plants=sorted(int(p) for p in mv.plant.unique()),
                    d_hr_mw_wtd=round(
                        float(
                            ((mv[b] - mv[a]) * mv.pmax).sum() / max(mv.pmax.sum(), 1e-9)
                        ),
                        4,
                    ),
                    d_hr_min=round(float((mv[b] - mv[a]).min()), 4) if len(mv) else 0.0,
                    d_hr_max=round(float((mv[b] - mv[a]).max()), 4) if len(mv) else 0.0,
                )
            res[str(y)] = row
            print(
                f"{iso} {y} [{bundle}] units {len(m)}  "
                + "  ".join(
                    f"{k}: {v['rows']} rows {v['mw']} MW plants {v['plants']} dHR(wtd) {v['d_hr_mw_wtd']:+.3f}"
                    for k, v in row.items()
                ),
                flush=True,
            )
    allf = pd.concat(frames)
    allf.to_csv(OUT / f"soco79_family_vintage_units_{iso}.csv.gz", index=False)
    (OUT / f"soco79_family_vintage_{iso}.json").write_text(
        json.dumps(res, indent=1) + "\n"
    )
    return res


def greedy(y: int, arm: str = "C") -> dict:
    """SOCO: price-taker greedy of the arm's per-unit ``mc_base`` delta on the soco76 leg.

    The soco-77 construction (``_soco77_ct_start.greedy``) with the start markup replaced by the
    census delta ``mc_<arm> - mc_A`` on every unit whose heat rate moved: baseline and arm offers
    are re-dispatched against the leg's zone price, and the hourly difference is refilled /
    displaced over the other gas + coal classes in merit order. Scorer-exact C1 and C4 coal.
    """
    import _soco77_ct_start as s77

    s73 = s77.s73
    u = pd.read_csv(OUT / "soco79_family_vintage_units_SOCO.csv.gz")
    u = u[u.year == y]
    col = f"hr_{arm}"
    mv = u[(u[col] - u.hr_A).abs() > 1e-9].set_index("unit_id")
    leg = s77._leg(y)
    delta_t = np.zeros(T)
    for uid, g in leg[leg.unit_id.isin(mv.index)].groupby("unit_id"):
        d_mc = float(mv.at[uid, f"mc_{arm}"] - mv.at[uid, "mc_A"])
        g = g.set_index("hour").reindex(range(T))
        mc0 = g.mc.to_numpy(float)
        cap = g.cap_mw.fillna(0).to_numpy(float)
        pr = g.price.to_numpy(float)
        r0 = np.where(mc0 <= pr + 1e-6, cap, 0.0)
        r1 = np.where(mc0 + d_mc <= pr + 1e-6, cap, 0.0)
        delta_t += np.nan_to_num(r1 - r0)
    moved_ids = set(mv.index)
    oth = leg[leg.g.isin(s77.REFILL) & ~leg.unit_id.isin(moved_ids)]
    up = oth.assign(head=(oth.cap_mw - oth.mw).clip(lower=0))
    up = up[up["head"] > 0.01][["hour", "g", "mc", "head"]].sort_values(["hour", "mc"])
    up["cum"] = up.groupby("hour")["head"].cumsum()
    need = np.clip(-delta_t, 0, None)[up.hour.to_numpy()]
    up["take"] = np.clip(
        need - (up.cum.to_numpy() - up["head"].to_numpy()), 0, up["head"].to_numpy()
    )
    down = oth[oth.mw > 0.01][["hour", "g", "mc", "mw"]].sort_values(
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
    moved_cls = mv.cls.iloc[0] if len(mv) else s77.CT
    dcls[moved_cls] = dcls.get(moved_cls, 0.0) + delta_t.sum() / 1e6
    coal_t = np.zeros(T)
    for fr, sgn in ((up, 1.0), (down, -1.0)):
        f = fr[fr.g.str.startswith("COAL")]
        coal_t += (
            sgn * f.groupby("hour")["take"].sum().reindex(range(T)).fillna(0).to_numpy()
        )
    r0, n0, r1, n1 = s73.c4_coal(y, coal_t)
    c1 = s73.c1_rows(y, dcls.to_dict())
    return dict(
        year=y,
        arm=arm,
        moved_rows=int(len(mv)),
        moved_mw=float(mv.pmax.sum()),
        moved_twh=float(delta_t.sum() / 1e6),
        delta={k: round(float(v), 4) for k, v in dcls.items() if abs(v) > 1e-6},
        c4=[round(n0, 4), round(n1, 4)],
        c4_r=[round(r0, 4), round(r1, 4)],
        c1=c1.round(4).to_dict("records"),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["census", "greedy"])
    ap.add_argument("--iso", choices=sorted(BUNDLES))
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2022, 2024, 2025])
    a = ap.parse_args()
    if a.mode == "census":
        census(a.iso)
        return
    out = []
    for y in a.years:
        g = greedy(y)
        out.append(g)
        print(
            f"\n== {y} arm C  moved {g['moved_rows']} rows {g['moved_mw']:.1f} MW  "
            f"class d {g['delta']}  C4 coal {g['c4'][0]} -> {g['c4'][1]}"
        )
        c1 = pd.DataFrame(g["c1"])
        print(
            c1[
                c1.cls.isin(["COAL_BIT", "CT_PEAKER", "CC_REGULAR", "COAL_PRB"])
            ].to_string(index=False)
        )
    (OUT / "soco79_family_vintage_greedy.json").write_text(
        json.dumps(out, indent=1, default=float) + "\n"
    )


if __name__ == "__main__":
    main()
