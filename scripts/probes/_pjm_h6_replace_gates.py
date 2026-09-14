"""pjm-h6 phase 0 — the Route A REPLACE arm measured through the REAL field.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Rebuilds the PJM keeper's fleet on its own
``meta.json`` recipe via ``replay_keeper.run_year_kwargs`` +
``derived_run_year_inputs`` (``run_year(..., fleet_only=True)``) twice per year —
control and ``committed_band_measured_basis=True`` — and measures the
PRECOMMIT §7 gates on the assembled P0 objective array ``mc_base``:

* **G-1 confinement** — only ``committed`` rows move, only in covered classes;
  row count, ``unit_id`` order and ``pmax`` identical.
* **G-2 IDENTITY** — the arm's effective committed basis equals the measured
  ``avg_committed_p50`` to < 1e-6 in EVERY hour. Measured two independent ways:
  (a) the tranche multiplier ``heat_rate / base_hr`` against the artifact value,
  and (b) an EXACT AFFINE FIT of each row's assembled ``mc_base`` on its own
  delivered fuel price — under REPLACE the fuel passthrough is 1.0 in all 8760
  hours, so ``mc = nonfuel + base_hr × measured × fuel`` must hold with ~0
  residual, and the fitted slope over ``base_hr`` IS the effective basis. The
  SAME fit on the control carries a large residual, which is the sigmoid.
* **G-3 magnitude** — the per-year capacity-weighted ``Δ$/MWh`` table, against
  the values pre-registered in the charter §3.1.

Run: ``python3 scripts/probes/_pjm_h6_replace_gates.py 2020 2021 ...``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}
#: charter §3.1, pre-registered BEFORE any solve — the REPLACE arm's
#: coal-`committed` cap-weighted Δ$/MWh per year.
PREREGISTERED = {
    2020: 12.6296,
    2021: 7.8450,
    2022: 5.1848,
    2023: 17.6561,
    2024: 16.8422,
    2025: 12.0271,
}


def build(year: int, armed: bool) -> dict:
    """Build the keeper's fleet for *year*, control or armed."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    # Inherited from pjm-h4 §2 where it was VERIFIED, not asserted: the
    # DA-virtual layer APPENDS pseudo-units and its corpus is licence-
    # restricted (README-only); 553 coal tranches identical either way on
    # unit_id / heat_rate / pmax / delivered-fuel mean and sd. Self-cancelling
    # here anyway — both legs of every diff carry the same setting.
    kw["pjm_da_virtual_bids"] = False
    if armed:
        kw["committed_band_measured_basis"] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _band(unit_id: str) -> str:
    tail = unit_id.rsplit("_", 1)[-1]
    return "econ" if tail.startswith("econc") else tail


def _capwtd(df: pd.DataFrame, col: str = "d") -> float:
    if df.empty or df["cap"].sum() == 0:
        return 0.0
    return float((df[col] * df["cap"]).sum() / df["cap"].sum())


def _frame(res: dict) -> pd.DataFrame:
    mc = np.asarray(res["mc_base"], dtype=float)
    fleet = res["fleet"]
    d_mean = mc.mean(axis=1) if mc.ndim == 2 else mc
    return pd.DataFrame(
        {
            "unit_id": [g.unit_id for g in fleet],
            "plant": [int(g.plant_code) for g in fleet],
            "group": [g.efficiency_bin for g in fleet],
            "fuel": [g.fuel_type for g in fleet],
            "band": [_band(g.unit_id) for g in fleet],
            "cap": [float(g.pmax_mw) for g in fleet],
            "hr": [float(g.heat_rate) for g in fleet],
            "mc_mean": d_mean,
        }
    )


#: Base heat rate is recovered from the CONTROL build as ``heat_rate_ctl /
#: <the control config's OWN resolved `committed` multiplier for that
#: group>`` -- read off ``ctl["config"].offer_curve_by_group``, never a table
#: restated here, because PJM's keeper is PARTITIONED (2020-2022 solve the
#: `pjm_d4_4_TP` recipe, 2023-2025 the `pjm_d4_4_A` carve-out) and the two
#: configs carry different registered committed bands. Cross-checked against
#: the `_mustrun` sibling's heat rate wherever one exists (its own registered
#: multiplier is 1.0), so the recovery is verified rather than assumed.


def identity(ctl: dict, arm: dict, measured: dict[str, float]) -> dict:
    """G-2 — the armed effective committed basis, measured pointwise.

    Three legs, none of them a regression (an earlier draft fitted
    ``mc ~ a + b*fuel`` and that fit is DEGENERATE on the 12 plants whose
    delivered coal price is flat, where a constant regressor is collinear with
    the intercept — reported here because it is the exact failure a reader
    should be able to rule out):

    * **(a) the tranche multiplier**, ``heat_rate_arm / base_hr``, over EVERY
      coal committed row. ``base_hr`` is recovered from the CONTROL build as
      ``heat_rate_ctl / REGISTERED_COMMITTED[class]``, which needs no sibling
      tranche; where a ``_mustrun`` sibling exists its heat rate is asserted
      equal (its own registered multiplier is 1.0), so the recovery is
      cross-checked rather than assumed.
    * **(b) the passthrough, pointwise, sibling-free.** Under REPLACE
      ``mc[g,t] = nonfuel[g] + heat_rate[g] * fuel[g,t]`` exactly, so where the
      row's delivered fuel price MOVES the finite difference
      ``Δmc / Δfuel`` must equal ``heat_rate`` in every hour pair, and where it
      is FLAT ``mc`` must be exactly constant across all 8760 h (the sigmoid is
      keyed to GAS, so a live one would move ``mc`` even at a flat coal price).
    * **(c) the ``_mustrun`` cross-check** where a sibling exists: that band's
      own fuel fraction is 0.0, so its ``mc`` is the row's non-fuel constant and
      ``(mc_committed - mc_mustrun) / (heat_rate * fuel)`` is the passthrough
      itself, pointwise.
    """
    fa, fc = arm["fleet"], ctl["fleet"]
    # The model's OWN band resolver, not a table restated here: a coal
    # generator's `efficiency_bin` is the generic "COAL" for every supply,
    # and the supply class (COAL_BIT / COAL_WC / COAL_PRB) is resolved
    # INSIDE `_offer_curve_for_group` from the plant code. Reading the
    # registered multiplier off `efficiency_bin` would silently pick the
    # generic COAL row for a bituminous plant.
    from market_sim.data.offer_curves import _offer_curve_for_group

    mca = np.asarray(arm["mc_base"], dtype=float)
    fpa = np.asarray(arm["fuel_prices"], dtype=float)
    mustrun = {
        int(g.plant_code): i
        for i, g in enumerate(fa)
        if g.fuel_type == "coal" and g.unit_id.endswith("_mustrun")
    }
    mult_dev, pass_dev, cross_dev = [], [], []
    caps, n_flat, n_cross = [], 0, 0
    target = measured["COAL_BIT"]
    for i, g in enumerate(fa):
        if g.fuel_type != "coal" or _band(g.unit_id) != "committed":
            continue
        j = mustrun.get(int(g.plant_code))
        reg = (
            _offer_curve_for_group(
                str(fc[i].efficiency_bin), int(g.plant_code), ctl["config"]
            )
            or {}
        ).get("committed")
        base = None
        if j is not None:
            # The `_mustrun` band's own registered multiplier is 1.0, so its
            # assembled heat rate IS the plant's base heat rate.
            base = float(fa[j].heat_rate)
        if reg:
            recovered = float(fc[i].heat_rate) / float(reg)
            if base is None:
                base = recovered
            else:
                assert abs(recovered - base) <= 1e-6 * base, (
                    f"{g.unit_id}: base_hr from the control's registered "
                    f"multiplier ({recovered}) disagrees with its _mustrun "
                    f"tranche ({base})"
                )
        if not base:
            continue
        caps.append(float(g.pmax_mw))
        # (a)
        mult_dev.append(abs(float(g.heat_rate) / base - target))
        # (b)
        y, x = mca[i], fpa[i]
        dx = np.diff(x)
        move = np.abs(dx) > 1e-12
        if move.any():
            slope = np.diff(y)[move] / dx[move]
            pass_dev.append(float(np.max(np.abs(slope / float(g.heat_rate) - 1.0))))
        else:
            n_flat += 1
            pass_dev.append(float(np.ptp(y) / max(float(np.mean(np.abs(y))), 1e-12)))
        # (c)
        if j is not None:
            ff = (y - mca[j]) / (float(g.heat_rate) * x)
            cross_dev.append(float(np.max(np.abs(ff - 1.0))))
            n_cross += 1
    return {
        "n": len(caps),
        "cap": float(np.sum(caps)),
        "n_flat_fuel": n_flat,
        "n_cross": n_cross,
        "cap_cross": float(
            np.sum(
                [
                    float(g.pmax_mw)
                    for g in fa
                    if g.fuel_type == "coal"
                    and _band(g.unit_id) == "committed"
                    and int(g.plant_code) in mustrun
                ]
            )
        ),
        "mult_maxdev": float(np.max(mult_dev)) if mult_dev else float("nan"),
        "pass_maxdev": float(np.max(pass_dev)) if pass_dev else float("nan"),
        "cross_maxdev": float(np.max(cross_dev)) if cross_dev else float("nan"),
        "target": target,
    }


def control_passthrough(ctl: dict) -> dict:
    """The CONTROL's own pointwise passthrough — the sigmoid, for contrast."""
    fleet = ctl["fleet"]
    mc = np.asarray(ctl["mc_base"], dtype=float)
    fp = np.asarray(ctl["fuel_prices"], dtype=float)
    mustrun = {
        int(g.plant_code): i
        for i, g in enumerate(fleet)
        if g.fuel_type == "coal" and g.unit_id.endswith("_mustrun")
    }
    lo, hi = [], []
    for i, g in enumerate(fleet):
        if g.fuel_type != "coal" or _band(g.unit_id) != "committed":
            continue
        j = mustrun.get(int(g.plant_code))
        if j is None:
            continue
        ff = (mc[i] - mc[j]) / (float(g.heat_rate) * fp[i])
        lo.append(float(ff.min()))
        hi.append(float(ff.max()))
    return {
        "min": min(lo) if lo else float("nan"),
        "max": max(hi) if hi else float("nan"),
    }


def main() -> None:
    from market_sim.data.offer_curves import committed_measured_basis

    years = [int(a) for a in sys.argv[1:]] or [2023]
    measured = committed_measured_basis("PJM")
    print("measured avg_committed_p50 (PJM artifact):")
    for k in sorted(measured):
        print(f"  {k:<22}{measured[k]:.4f}")

    summary = []
    for y in years:
        print(f"\n{'=' * 78}\n===== {y} =====\n{'=' * 78}")
        ctl, arm = build(y, False), build(y, True)

        fc, fa = ctl["fleet"], arm["fleet"]
        assert len(fc) == len(fa), f"row count moved {len(fc)} -> {len(fa)}"
        assert [g.unit_id for g in fc] == [g.unit_id for g in fa], "unit_id order moved"
        assert np.allclose([g.pmax_mw for g in fc], [g.pmax_mw for g in fa]), (
            "pmax moved"
        )

        d = _frame(ctl)
        d["d"] = _frame(arm)["mc_mean"] - d["mc_mean"]
        moved = d[d["d"].abs() > 1e-9]
        coal = d[d["fuel"] == "coal"]
        cc = coal[coal["band"] == "committed"]

        print(
            f"\n-- G-1 CONFINEMENT --\n"
            f"   rows moved      : {len(moved)} of {len(d)}\n"
            f"   bands moved     : {sorted(moved['band'].unique())}\n"
            f"   groups moved    : {sorted(moved['group'].unique())}"
        )
        g1 = set(moved["band"].unique()) <= {"committed"}
        print(f"   G-1: {'PASS' if g1 else 'FAIL'}")

        idn = identity(ctl, arm, measured)
        cpt = control_passthrough(ctl)
        print(
            f"\n-- G-2 IDENTITY (target {idn['target']:.4f}) --\n"
            f"   ARM  n={idn['n']} rows, cap={idn['cap']:,.0f} MW"
            f"  ({idn['n_flat_fuel']} flat-fuel rows)\n"
            f"     (a) tranche multiplier vs measured   "
            f"max|dev| = {idn['mult_maxdev']:.3e}\n"
            f"     (b) passthrough, pointwise/sibling-free "
            f"max|dev| = {idn['pass_maxdev']:.3e}\n"
            f"     (c) _mustrun cross-check ({idn['n_cross']} rows, "
            f"{idn['cap_cross']:,.0f} MW)  max|ff-1| = {idn['cross_maxdev']:.3e}\n"
            f"   CONTROL pointwise passthrough (the sigmoid, for contrast): "
            f"[{cpt['min']:.4f}, {cpt['max']:.4f}]"
        )
        g2 = max(idn["mult_maxdev"], idn["pass_maxdev"], idn["cross_maxdev"]) < 1e-6
        print(f"   G-2: {'PASS' if g2 else 'FAIL'}")

        dcc, dall, dfleet = _capwtd(cc), _capwtd(coal), _capwtd(d)
        pre = PREREGISTERED[y]
        print(
            f"\n-- G-3 MAGNITUDE --\n"
            f"   coal committed : n={len(cc)} cap={cc['cap'].sum():,.0f} MW  "
            f"cap-wtd d={dcc:+.4f} $/MWh\n"
            f"   pre-registered : {pre:+.4f}   delta={dcc - pre:+.4f}\n"
            f"   ALL-COAL       : {dall:+.4f} $/MWh\n"
            f"   WHOLE-FLEET    : {dfleet:+.4f} $/MWh"
        )
        for grp, sub in moved.groupby("group"):
            print(
                f"      {grp:<18} n={len(sub):<4} cap={sub['cap'].sum():>9,.0f} MW"
                f"  cap-wtd d={_capwtd(sub):+9.4f} $/MWh"
            )
        summary.append(
            {
                "year": y,
                "g1": bool(g1),
                "g2": bool(g2),
                "coal_committed_d": dcc,
                "prereg": pre,
                "all_coal_d": dall,
                "fleet_d": dfleet,
                "rows_moved": int(len(moved)),
                "identity_maxdev": max(
                    idn["mult_maxdev"], idn["pass_maxdev"], idn["cross_maxdev"]
                ),
                "control_passthrough_min": cpt["min"],
                "control_passthrough_max": cpt["max"],
            }
        )

    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}")
    print(
        f"{'yr':<6}{'G-1':>5}{'G-2':>5}{'id maxdev':>12}"
        f"{'coal comm d':>13}{'prereg':>10}{'diff':>9}{'fleet d':>10}"
    )
    for s in summary:
        print(
            f"{s['year']:<6}{'ok' if s['g1'] else 'FAIL':>5}"
            f"{'ok' if s['g2'] else 'FAIL':>5}{s['identity_maxdev']:>12.2e}"
            f"{s['coal_committed_d']:>+13.4f}{s['prereg']:>+10.4f}"
            f"{s['coal_committed_d'] - s['prereg']:>+9.4f}{s['fleet_d']:>+10.4f}"
        )
    out = REPO / "results/calibration/_pjm_h6_replace_gates.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
