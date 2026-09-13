"""pjm-h5 phase 0 (C): the EXACT pre-solve offer-array delta for re-pricing the
`committed` band to its measured `avg_committed_p50`.

ZERO LP. Rebuilds the PJM keeper's fleet on its own `meta.json` recipe via the
sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``) and diffs the assembled P0 marginal-cost
array ``mc_base`` row-for-row against two arms:

* ``COAL``   — the card's arm: every coal supply group's `committed` multiplier
  := 0.916, the artifact's single ``COAL`` row.
* ``ALL``    — the NON-SELECTIVE rule-14 substitution: EVERY class's `committed`
  multiplier := its own measured ``avg_committed_p50``. This is the same
  substitution applied without choosing which class receives it, and it exists
  because 10 of PJM's 11 registered classes sit below their measured basis
  (probe A) — so a coal-only arm is a selection, not a substitution.

Also answers, before any solve (rule 29 ``[R-SCREEN]`` clause 0):

* whether coal `committed` tranches carry ANY min_gen floor (the load-bearing
  claim that re-pricing them moves DISPATCH, not only price);
* the bituminous sigmoid passthrough per year, and therefore whether
  substituting the MULTIPLIER actually delivers the measured EFFECTIVE basis
  (rule 19 ``[R-ONE-MECH]``: the sigmoid already prices this same block).

Run: ``python3 scripts/probes/_pjm_h5_committed_delta.py 2020 2021 ...``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "data/raw/reference/pjm_campd_marginal_hr_summary.csv"
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}
ARMS: tuple[str, ...] = ("COAL", "ALL", "REPLACE")
COAL_CLASSES = ("COAL", "COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC")
#: model class -> artifact row (the artifact has ONE `COAL` row, n=65)
ARTIFACT_ROW = {
    "CC_REGULAR": "CC_REGULAR",
    "CC_CHP": "CC_CHP",
    "CT_CHP": "CT_CHP",
    "CT_PEAKER": "CT_PEAKER",
    "CT_INTERMEDIATE": "CT_PEAKER",
    "ST_GAS": "ST_GAS",
    **{c: "COAL" for c in COAL_CLASSES},
}


def measured_committed() -> dict[str, float]:
    """Return ``{model class: measured avg_committed_p50}``.

    ``avg_committed_p50`` is the operand PJM's own registered convention names
    for this band (``pipeline/backcast_config.py``: "committed ->
    avg_committed_p50"), so the operand is fixed by precedent, not chosen here
    (rule 21 ``[R-DOF]``).
    """
    art = pd.read_csv(ART).set_index("class")
    return {
        cls: float(art.loc[row, "avg_committed_p50"])
        for cls, row in ARTIFACT_ROW.items()
    }


def build(year: int, arm: str):
    """Build the keeper's fleet for *year*; ``arm`` in {"control","COAL","ALL"}."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    # ONE DECLARED SIMPLIFICATION, inherited from pjm-h4 §2 where it was
    # VERIFIED rather than asserted: the DA-virtual layer APPENDS pseudo-units
    # and its corpus is licence-restricted (README-only), and pjm-h4 measured
    # 553 coal tranches IDENTICAL either way on unit_id / heat_rate / pmax /
    # delivered-fuel mean and sd. It is additionally self-cancelling here: both
    # legs of every diff carry the same setting, so no moved row can be its.
    kw["pjm_da_virtual_bids"] = False

    if arm != "control":
        meas = measured_committed()
        targets = COAL_CLASSES if arm in ("COAL", "REPLACE") else tuple(ARTIFACT_ROW)
        ovr = {k: dict(v) for k, v in (kw.get("offer_curve_overrides") or {}).items()}
        for cls in targets:
            if cls in ovr:
                ovr[cls]["committed"] = meas[cls]
        kw["offer_curve_overrides"] = ovr

    if arm != "REPLACE":
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )

    # ARM REPLACE — the rule 19 [R-ONE-MECH] form. Substituting the multiplier
    # while the bituminous sigmoid still scales the SAME block STACKS the two:
    # the effective basis becomes 0.916 x passthrough, which undershoots the
    # measurement in cheap-gas years and overshoots it in dear-gas ones, so the
    # substitution never actually delivers the measured physics. REPLACE removes
    # the sigmoid from the `committed` band ONLY (the econ/peak bands keep it,
    # where its merit-order-crossover rationale is about INCREMENTAL coal
    # competing with gas), so the effective basis IS 0.916 in every year and
    # every hour — which is also what makes it year-invariant under rule 1
    # [R-STRUCT] condition (b).
    #
    # Patched on the PACKAGE namespace, the sanctioned route: package internals
    # resolve this name through `models._pkg_ns()` at call time.
    import market_sim.data.fleet as _fleet

    orig = _fleet.campd_tranche_fuel_frac

    def _patched(gen, *a, **k):
        if gen.fuel_type == "coal" and gen.unit_id.rsplit("_", 1)[-1].startswith(
            "committed"
        ):
            return 1.0
        return orig(gen, *a, **k)

    _fleet.campd_tranche_fuel_frac = _patched
    try:
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        _fleet.campd_tranche_fuel_frac = orig


def _band(unit_id: str) -> str:
    tail = unit_id.rsplit("_", 1)[-1]
    if tail.startswith("econc"):
        return "econ"
    return tail


def compare(ctl: dict, arm: dict) -> dict:
    """Diff two fleet builds' assembled P0 offer arrays."""
    f_c, f_a = ctl["fleet"], arm["fleet"]
    assert len(f_c) == len(f_a), f"row count moved {len(f_c)} -> {len(f_a)}"
    ids_c = [g.unit_id for g in f_c]
    assert ids_c == [g.unit_id for g in f_a], "unit_id order moved"

    mc_c, mc_a = np.asarray(ctl["mc_base"]), np.asarray(arm["mc_base"])
    d = mc_a - mc_c
    if d.ndim == 2:
        d_mean = d.mean(axis=1)
    else:
        d_mean = d
    cap = np.array([g.pmax_mw for g in f_c], dtype=float)

    rows = []
    for i, g in enumerate(f_c):
        rows.append(
            {
                "unit_id": g.unit_id,
                "group": g.efficiency_bin,
                "fuel": g.fuel_type,
                "band": _band(g.unit_id),
                "cap": cap[i],
                "d": float(d_mean[i]),
            }
        )
    df = pd.DataFrame(rows)
    moved = df[df["d"].abs() > 1e-9]
    return {"df": df, "moved": moved, "cap": cap, "d_mean": d_mean}


def _capwtd(df: pd.DataFrame) -> float:
    if df.empty or df["cap"].sum() == 0:
        return 0.0
    return float((df["d"] * df["cap"]).sum() / df["cap"].sum())


def min_gen_audit(ctl: dict) -> None:
    """Report whether coal `committed` tranches carry any min_gen floor."""
    fa = ctl["fleet_arrays"]
    mg = None
    for name in ("min_gen", "min_gen_mw", "pmin"):
        if hasattr(fa, name):
            mg = np.asarray(getattr(fa, name))
            break
    if mg is None:
        print("  (fleet_arrays exposes no min_gen field under the tried names)")
        return
    fleet = ctl["fleet"]
    mg2 = mg if mg.ndim == 2 else np.repeat(mg[:, None], 8760, axis=1)
    tot = mg2.sum(axis=1)
    print(
        f"  {'group':<13}{'band':<11}{'n':>4}{'cap MW':>10}"
        f"{'floored MWh':>13}{'cap-hrs':>13}{'% floored':>10}{'hrs>0':>8}"
    )
    agg: dict[tuple[str, str], list] = {}
    for i, g in enumerate(fleet):
        if g.fuel_type != "coal":
            continue
        k = (g.efficiency_bin, _band(g.unit_id))
        a = agg.setdefault(k, [0, 0.0, 0.0, 0])
        a[0] += 1
        a[1] += g.pmax_mw
        a[2] += float(tot[i])
        a[3] = max(a[3], int((mg2[i] > 1e-9).sum()))
    for (grp, band), (n, cap, mwh, hrs) in sorted(agg.items()):
        caphrs = cap * mg2.shape[1]
        pct = 100.0 * mwh / caphrs if caphrs else 0.0
        print(
            f"  {grp:<13}{band:<11}{n:>4}{cap:>10,.0f}"
            f"{mwh:>13,.0f}{caphrs:>13,.0f}{pct:>9.2f}%{hrs:>8}"
        )
    print(
        "  NOTE: the `committed` row is what the card's premise turns on — a"
        " floored\n        MWh dispatches regardless of price, so only the"
        " UNFLOORED share responds."
    )


def main() -> None:
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    global ARMS
    if "--replace-only" in sys.argv:
        ARMS = ("REPLACE",)
    years = [int(a) for a in argv] or [2020]
    meas = measured_committed()
    print("measured avg_committed_p50 operands:")
    for k in sorted(set(ARTIFACT_ROW)):
        print(f"  {k:<16}{meas[k]:.3f}")

    summary = []
    sig_rows: list[dict] = []
    for y in years:
        print(f"\n{'=' * 74}\n===== {y} =====\n{'=' * 74}")
        ctl = build(y, "control")

        print("\n-- min_gen on coal tranches (is `committed` floored?) --")
        min_gen_audit(ctl)

        # Rule 19 [R-ONE-MECH]: the bituminous sigmoid already prices this same
        # block, so the substitution does NOT deliver the measured basis unless
        # the sigmoid is REPLACED on this band. State what it actually delivers.
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ctl["config"]
        pt = coal_passthrough_series(cfg, y, 8760, "bituminous")
        pt = float(np.mean(pt))
        reg = 0.548
        m = measured_committed()["COAL_BIT"]
        print(
            f"\n-- bituminous sigmoid passthrough {y}: {pt:.4f} --\n"
            f"   effective committed basis  registered {reg:.3f} x pt ="
            f" {reg * pt:.4f}\n"
            f"   effective AFTER substitution {m:.3f} x pt = {m * pt:.4f}"
            f"   (measured basis {m:.3f}, "
            f"{'OVERSHOOT' if m * pt > m else 'still BELOW'}"
            f" {m * pt - m:+.4f})"
        )
        sig_rows.append({"year": y, "pt": pt, "eff_reg": reg * pt, "eff_arm": m * pt})

        for armname in ARMS:
            arm = build(y, armname)
            r = compare(ctl, arm)
            df, moved = r["df"], r["moved"]
            coal = df[df["fuel"] == "coal"]
            coal_comm = coal[coal["band"] == "committed"]
            allc = _capwtd(df)
            print(f"\n-- ARM {armname} --")
            print(
                f"  rows moved: {len(moved)} of {len(df)}   "
                f"bands moved: {sorted(moved['band'].unique())}"
            )
            print(
                f"  groups moved: "
                f"{sorted(moved['group'].unique()) if len(moved) else []}"
            )
            print(
                f"  coal committed: n={len(coal_comm)} "
                f"cap={coal_comm['cap'].sum():,.0f} MW  "
                f"cap-wtd d={_capwtd(coal_comm):+.4f} $/MWh"
            )
            print(f"  ALL-COAL cap-wtd d = {_capwtd(coal):+.4f} $/MWh")
            print(f"  WHOLE-FLEET cap-wtd d = {allc:+.4f} $/MWh")
            for grp, sub in moved.groupby("group"):
                print(
                    f"     {grp:<16} n={len(sub):<4} cap={sub['cap'].sum():>9,.0f} MW"
                    f"  cap-wtd d={_capwtd(sub):+9.4f} $/MWh"
                )
            summary.append(
                {
                    "year": y,
                    "arm": armname,
                    "coal_committed_d": _capwtd(coal_comm),
                    "coal_committed_cap": float(coal_comm["cap"].sum()),
                    "all_coal_d": _capwtd(coal),
                    "fleet_d": allc,
                    "footprint": abs(_capwtd(coal_comm))
                    * float(coal_comm["cap"].sum())
                    / 1e3,
                }
            )

    print(
        f"\n{'=' * 74}\nSUMMARY — footprint = |d$/MWh| x committed cap (10^3 MW·$/MWh)"
    )
    print(f"{'=' * 74}")
    print(
        f"{'yr':<6}{'arm':<7}{'coal comm d':>13}{'all-coal d':>12}"
        f"{'fleet d':>10}{'footprint':>12}"
    )
    for s in summary:
        print(
            f"{s['year']:<6}{s['arm']:<7}{s['coal_committed_d']:>+13.4f}"
            f"{s['all_coal_d']:>+12.4f}{s['fleet_d']:>+10.4f}{s['footprint']:>12.1f}"
        )
    print(f"\n{'=' * 74}\nSIGMOID — what the substitution actually delivers on coal")
    print(f"{'=' * 74}")
    print(
        f"{'yr':<6}{'passthru':>10}{'eff registered':>16}{'eff substituted':>17}{'vs measured':>13}"
    )
    for r in sig_rows:
        print(
            f"{r['year']:<6}{r['pt']:>10.4f}{r['eff_reg']:>16.4f}{r['eff_arm']:>17.4f}{r['eff_arm'] - 0.916:>+13.4f}"
        )
    out = REPO / "results/calibration/_pjm_h5_committed_delta.json"
    out.write_text(json.dumps({"delta": summary, "sigmoid": sig_rows}, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
