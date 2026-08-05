#!/usr/bin/env python
"""ERCOT-169 Phase 0 — do the three armed margin identifications survive their
own fuel-invariance claim on the delivery-2023 SCED corpus?

Charter: mechanism-testing-matrix §5.1 **item 13**, owner-chartered on the
ercot-168 FINDING §4 named-successor list. Decision rule pre-registered BEFORE
this ran: ``docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md``.

**NO LP.** No solve, no keeper file touched, no ``ScenarioConfig`` field
written, no residual consulted (rule 13 ``[R-MEASURED]``). Every number is
either a measured corpus read on an already-accepted convention, a committed
identification artifact read back, or a no-LP fleet reconstruction of the
delivered-fuel array the identification itself was expressed against.

Each of ``COAL_OFFER_MARGIN_LEVEL_BY_ISO`` (ERCOT-137),
``CC_COMMITTED_OFFER_LEVEL_BY_ISO`` (ERCOT-139) and
``COAL_PEAK_OFFER_LEVEL_BY_ISO`` (ERCOT-140) declares in its ``constants.py``
block that *"2023 application is a declared extrapolation (no 2023 SCED
disclosure exists) — the margin is fuel-invariant by construction"*. The
ercot-157 delivery-2023 corpus dissolves that premise, and because all three are
MARGIN forms the corpus tests the invariance claim itself:

    level_2023 = measured_instrument_2023 − HR × (fuel_2023 − anchor)   vs   armed

Sections
--------
* **0** — harness fidelity: the reconstruction reproduces every committed
  instrument on all four identification subsets. Without this the 2023 read has
  no footing.
* **1** — the delivery-2023 instruments on the matched window (T1, gating) and
  full day (T2, reported), plus the clock-convention sensitivity.
* **2** — the fuel-basis footing gate (precommit §1c) and ``fuel_2023``.
* **3** — the per-limb verdicts under the pre-registered rule.
* **4** — the coverage-licensing diagnostic: what the 2023 shortfall IS.

Usage
-----
    python scripts/probes/ercot169_margin_invariance_phase0.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO / "src"), str(_REPO), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.lib.sced_corpus_instruments import (  # noqa: E402
    LIMBS,
    MATCHED_HOURS,
    assess_limb,
    coverage,
    curve_bottom,
    inc_bid_quantiles,
    load_corpus_year,
    monthly_curve_bottom,
    monthly_inc_p90,
    restrict_hours,
    year_instruments,
)

#: The keeper whose no-LP fleet reconstruction supplies the delivered-fuel
#: array (precommit §1c). ERCOT-138's own bundle is no longer on disk, so the
#: basis is re-established by reproducing its committed 2024/2025 values.
KEEPER_BUNDLE = _REPO / "results" / "calibration" / "ercot168_yearcurves_B"

#: Committed ERCOT-138 §J values the footing gate must reproduce ($/MMBtu).
ERCOT138_FUEL_CAPWTD = {"CC": {2024: 2.213, 2025: 3.232}, "COAL": {2024: 1.748, 2025: 1.630}}

#: Footing tolerance, pre-registered (precommit §1c).
FOOTING_TOL = 0.02

#: Delivered coal on the ERCOT-137 anchor's OWN basis (ercot135 per-plant,
#: cap-weighted; the anchor 1.7387 is the plain mean of these three).
COAL_FUEL_BY_YEAR = {2023: 1.8169, 2024: 1.7556, 2025: 1.6436}


def section_0_fidelity() -> list[dict]:
    """0 — the reconstruction IS the committed instrument, on all four subsets.

    Runs the module's three statistics over ``ercot123.load_sced``'s own frames
    and compares to the committed ERCOT-136 / ERCOT-138 artifacts. A divergence
    here means the delivery-2023 read is not comparable and nothing downstream
    stands.
    """
    from ercot123_coal_sced_reach import SUBSETS, load_sced

    e136 = json.loads((_REPO / "results/calibration/ercot136_coal_headroom_conduct.json").read_text())
    e138 = json.loads((_REPO / "results/calibration/ercot138_coal_gas_ranking.json").read_text())
    bot = {(r["year"], r["family"], r["class"]): r["bot_p50"] for r in e136["B1_curve_bottom"]}
    cov = {(r["year"], r["family"], r["class"]): r["curve_share"] for r in e136["A_ercot123_reproduced"]}
    p90 = {
        (r["year"], r["family"], r["class"]): r["measured"]
        for r in e138["E_bid_detail"]
        if r["q"] == "p90"
    }

    rows = []
    for tag, year, fam in SUBSETS:
        loaded = load_sced(tag)
        if loaded is None:
            continue
        df, _c = loaded
        for cls in ("COAL", "CC"):
            g = df[df["cls"] == cls]
            k = (year, fam, cls)
            mine = (curve_bottom(g)["bot_p50"], inc_bid_quantiles(g)["inc_bid_q"]["p90"], coverage(g)["curve_share"])
            cmt = (bot[k], p90[k], cov[k])
            rows.append(
                {
                    "subset": tag, "class": cls,
                    "bot_p50": round(mine[0], 4), "bot_p50_committed": cmt[0],
                    "p90": round(mine[1], 4), "p90_committed": cmt[1],
                    "curve_share": round(mine[2], 6), "curve_share_committed": round(cmt[2], 6),
                    "reproduced": bool(
                        abs(mine[0] - cmt[0]) < 5e-3
                        and abs(mine[1] - cmt[1]) < 5e-3
                        and abs(mine[2] - cmt[2]) < 1e-6
                    ),
                }
            )
    return rows


def section_2_fuel_basis() -> dict:
    """2 — ``fuel_2023`` on the ERCOT-138 §J basis, and the footing gate.

    Reconstructs the keeper fleet with NO LP for each training year and takes
    the ERCOT-138 §J statistic verbatim — ``Σ pmax·fuel_price / Σ pmax`` over
    the class's ``committed``/``econ`` model rows, ``fuel_price`` being the
    row's annual-mean delivered fuel captured at the ``apply_coal_tranches``
    seam. The gate is that 2024 and 2025 reproduce the committed values within
    :data:`FOOTING_TOL`; only then is the 2023 value basis-consistent.
    """
    from ercot138_coal_gas_ranking import MODEL_CC_GROUPS, MODEL_COAL_GROUPS, _tranche_role

    from scripts import run_calibration as rc
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    out: dict = {"construction": "ERCOT-138 J fuel_capwtd = sum(pmax*fuel_price)/sum(pmax), "
                 "committed+econ rows, no LP", "bundle": KEEPER_BUNDLE.name, "years": {}}
    for year in (2024, 2025, 2023):  # rule 12: sequential within one invocation
        real_coal = rc.apply_coal_tranches
        box: dict = {}

        def _pre_spy(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config=None, **kw):
            box["fuel_price"] = np.asarray(fuel_prices, dtype=float).mean(axis=1)
            real_coal(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config, **kw)

        rc.apply_coal_tranches = _pre_spy
        try:
            state, _meta = reconstruct_bundle_fleet(KEEPER_BUNDLE, year, verbose=False)
        finally:
            rc.apply_coal_tranches = real_coal

        fa, fleet = state["fleet_arrays"], state["fleet"]
        grp = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
        role = np.array([_tranche_role(str(u)) for u in fa.unit_ids])
        pmax = np.asarray(fa.pmax, dtype=float)
        fp = box["fuel_price"]
        row = {}
        for cls, groups in (("CC", MODEL_CC_GROUPS), ("COAL", MODEL_COAL_GROUPS)):
            idx = np.flatnonzero(np.isin(grp, list(groups)) & np.isin(role, ["committed", "econ"]))
            row[cls] = round(float((fp[idx] * pmax[idx]).sum() / pmax[idx].sum()), 4)
        out["years"][year] = row

    footing = []
    for cls, by_year in ERCOT138_FUEL_CAPWTD.items():
        for y, committed in by_year.items():
            got = out["years"][y][cls]
            footing.append(
                {"class": cls, "year": y, "reconstructed": got, "committed": committed,
                 "delta": round(got - committed, 4), "tol": FOOTING_TOL,
                 "pass": bool(abs(got - committed) <= FOOTING_TOL)}
            )
    out["footing"] = footing
    out["footing_pass"] = all(f["pass"] for f in footing)
    out["gas_2023"] = out["years"][2023]["CC"]
    out["coal_2023_ercot137_basis"] = COAL_FUEL_BY_YEAR[2023]
    return out


def section_4_licensing_diagnostic(df: pd.DataFrame) -> dict:
    """4 — what the 2023 coverage shortfall actually IS, per class.

    Reported for every limb whatever its verdict: the monthly ``curve_share``
    path and the worst-covered resources. A licensing failure is a finding in
    its own right — it says the year's conduct is not the conduct the constant
    was licensed on — so it is characterised, not merely flagged.
    """
    import ercot123_coal_sced_reach as e123

    out: dict = {}
    for cls in ("COAL", "CC"):
        d = restrict_hours(df[df["cls"] == cls], MATCHED_HOURS)
        g = e123._decompose(d)
        per = (
            g.groupby("Resource Name")
            .agg(res_hours=("has_curve", "size"), curve_share=("has_curve", "mean"), hsl_mw=("HSL", "mean"))
            .sort_values("curve_share")
        )
        out[cls] = {
            "n_resources": int(len(per)),
            "monthly_curve_share": [
                {"month": int(m), "curve_share": round(float(x["has_curve"].mean()), 4),
                 "res_hours": int(len(x))}
                for m, x in g.groupby("month")
            ],
            "worst_covered_resources": [
                {"resource": r, "res_hours": int(v.res_hours),
                 "curve_share": round(float(v.curve_share), 4), "hsl_mw": round(float(v.hsl_mw), 1)}
                for r, v in per.head(6).iterrows()
            ],
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the Phase-0 test and emit the committed artifact."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args(argv)

    from market_sim.config import constants as C

    armed = {
        "coal_mustrun": float(C.COAL_OFFER_MARGIN_LEVEL_BY_ISO["ERCOT"]),
        "cc_committed": float(C.CC_COMMITTED_OFFER_LEVEL_BY_ISO["ERCOT"]),
        "coal_peak": float(C.COAL_PEAK_OFFER_LEVEL_BY_ISO["ERCOT"]),
    }

    print("§0 harness fidelity ...", flush=True)
    fidelity = section_0_fidelity()
    if not all(r["reproduced"] for r in fidelity):
        print("FATAL: the reconstruction does not reproduce the committed instruments")
        return 1
    print(f"    {len(fidelity)}/{len(fidelity)} subset-class reads reproduced exactly", flush=True)

    print("§1 delivery-2023 corpus ...", flush=True)
    df = load_corpus_year(2023)
    windows: dict = {}
    for cls in ("COAL", "CC"):
        windows[f"T1_{cls}"] = year_instruments(2023, cls, MATCHED_HOURS, "cst", df)
        windows[f"T2_{cls}"] = year_instruments(2023, cls, None, "cst", df)
        windows[f"T1cpt_{cls}"] = year_instruments(2023, cls, MATCHED_HOURS, "cpt", df)
    monthly = {
        "COAL_bot_p50": monthly_curve_bottom(df, "COAL"),
        "CC_bot_p50": monthly_curve_bottom(df, "CC"),
        "COAL_p90": monthly_inc_p90(df, "COAL"),
    }

    print("§2 fuel-basis footing (no LP) ...", flush=True)
    fuel = section_2_fuel_basis()
    print(f"    footing {'PASS' if fuel['footing_pass'] else 'FAIL'}; gas_2023 = {fuel['gas_2023']}", flush=True)

    print("§3 verdicts ...", flush=True)
    verdicts = {}
    for key, spec in LIMBS.items():
        fy = COAL_FUEL_BY_YEAR[2023] if spec["fuel"] == "coal" else fuel["gas_2023"]
        verdicts[key] = {
            "T1_gating": assess_limb(key, windows[f"T1_{spec['cls']}"], fy, armed[key]),
            "T2_reported": assess_limb(key, windows[f"T2_{spec['cls']}"], fy, armed[key]),
            "T1cpt_sensitivity": assess_limb(key, windows[f"T1cpt_{spec['cls']}"], fy, armed[key]),
        }

    out = {
        "lane": "ercot169-margin-fuel-invariance",
        "phase": 0,
        "no_lp": True,
        "keeper_unchanged": True,
        "charter": "mechanism-testing-matrix §5.1 item 13",
        "precommit": "docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md",
        "armed_constants": armed,
        "corpus": {
            "root": "data/raw/ercot/SCED",
            "rows": int(len(df)),
            "days": int(df["ts"].dt.normalize().nunique()),
            "by_class": {k: int(v) for k, v in df["cls"].value_counts().items()},
        },
        "section_0_harness_fidelity": fidelity,
        "section_1_instruments_2023": windows,
        "section_1b_monthly": monthly,
        "section_2_fuel_basis": fuel,
        "section_3_verdicts": verdicts,
        "section_4_licensing_diagnostic": section_4_licensing_diagnostic(df),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=1, default=float))
        print(f"wrote {args.json_out}")

    print()
    hdr = f"{'limb':<6}{'constant':<34}{'measured':>10}{'level23':>10}{'armed':>9}{'delta':>9}{'band':>8}{'cov':>9}{'verdict':>20}"
    print(hdr)
    print("-" * len(hdr))
    for key in LIMBS:
        v = verdicts[key]["T1_gating"]
        print(f"{v['limb']:<6}{v['constant']:<34}{v['measured_usd_mwh']:>10.3f}"
              f"{v['level_year_usd_mwh']:>10.3f}{v['armed_usd_mwh']:>9.3f}"
              f"{v['delta_usd_mwh']:>+9.3f}{v['band_usd_mwh']:>8.3f}"
              f"{v['curve_share']:>9.4f}{v['verdict']:>20}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
