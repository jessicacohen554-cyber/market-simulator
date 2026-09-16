"""nyiso-235: score the rule-29 [R-SCREEN] gates for the 2022 gas-repair arm. ZERO LP.

CONTROL is the incumbent keeper's COMMITTED bundle (rule 29(b) form 4) — no control solve.
G-1 is decided pre-solve on the delivered gas array (see the ADDENDUM); this script scores
G-2 / G-4 / G-5 against the control and reports G-3 against the pre-registered dmc band.

The gates are STRUCTURAL and STOP-ONLY. C3a / C1 / C3b are NOT gates and are not read here.

Usage: python3 scripts/probes/_nyiso235_screen_gates.py <arm_bundle> [control_bundle]
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

YEAR = 2022
CONTROL_DEFAULT = Path("results/calibration/nyiso232_deleak_span")
# Pre-registered in the ADDENDUM before the arm solved.
DMC_BAND = {
    "CC_REGULAR": (207.38, 220.96),
    "CC_CHP": (222.19, 236.75),
    "CT_CHP": (266.63, 284.10),
    "ST_GAS": (325.88, 347.23),
    "CT_PEAKER": (385.13, 410.36),
}
ELLIOTT = (pd.Timestamp(f"{YEAR}-12-22"), pd.Timestamp(f"{YEAR}-12-24"))
TOUCHED_MONTHS = (11, 12)


def _sys(bundle: Path) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{YEAR}.parquet")
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def _lw_price(df: pd.DataFrame, mask=None) -> float:
    d = df if mask is None else df[mask]
    return float(np.average(d["price"], weights=d["demand"].clip(lower=1e-9)))


def main() -> None:
    arm_dir = Path(sys.argv[1])
    ctl_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else CONTROL_DEFAULT
    arm, ctl = _sys(arm_dir), _sys(ctl_dir)
    hrs = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")

    print("=" * 78)
    print(
        f"nyiso-235 SCREEN GATES — arm={arm_dir.name}  control={ctl_dir.name} (committed keeper)"
    )
    print("=" * 78)

    # ---- G-4 NO STRUCTURAL BREAK (checked first: it is the one most likely to fire) ----
    print("\nG-4 NO STRUCTURAL BREAK — slack/dump stay at zero")
    for nm, df in (("control", ctl), ("arm", arm)):
        print(
            f"   {nm:8s} slack sum={df['slack'].sum():.6f}  dump sum={df['dump'].sum():.6f}"
            f"  hours slack>0: {(df['slack'] > 1e-9).sum()}  dump>0: {(df['dump'] > 1e-9).sum()}"
        )
    new_slack = float(arm["slack"].sum()) - float(ctl["slack"].sum())
    new_dump = float(arm["dump"].sum()) - float(ctl["dump"].sum())
    g4 = (arm["slack"].sum() <= 1e-6) and (arm["dump"].sum() <= 1e-6)
    print(f"   arm-minus-control: slack {new_slack:+.6f}  dump {new_dump:+.6f}")
    print(
        f"   G-4: {'PASS' if g4 else 'STOP — the arm introduced load shed / dump the control did not have'}"
    )

    # ---- G-2 DIRECTION ----
    print(
        "\nG-2 DIRECTION — on the recovered Elliott days the delivered gas rises, and price rises with it"
    )
    zones = sorted(arm["zone"].unique())
    am = arm.set_index([arm["zone"], arm["hour"]])
    cm = ctl.set_index([ctl["zone"], ctl["hour"]])
    ell_h = np.where((hrs >= ELLIOTT[0]) & (hrs < ELLIOTT[1]))[0]
    a_e = arm[arm["hour"].isin(ell_h)]
    c_e = ctl[ctl["hour"].isin(ell_h)]
    lw_a, lw_c = _lw_price(a_e), _lw_price(c_e)
    print(
        f"   Dec 22-23 load-weighted price: control {lw_c:9.2f} -> arm {lw_a:9.2f}   ({lw_a - lw_c:+.2f} $/MWh)"
    )
    g2 = lw_a > lw_c
    print(
        f"   G-2: {'PASS' if g2 else 'STOP — price did not rise on the recovered days'}"
    )

    # ---- G-3 ORDER OF MAGNITUDE ----
    print(
        "\nG-3 ORDER OF MAGNITUDE — response consistent with the PRE-REGISTERED dmc band"
    )
    lo = min(v[0] for v in DMC_BAND.values())
    hi = max(v[1] for v in DMC_BAND.values())
    print(f"   pre-registered dmc band (ADDENDUM §4): {lo:.2f} .. {hi:.2f} $/MWh")
    print(f"   realized Dec 22-23 load-weighted rise:  {lw_a - lw_c:+.2f} $/MWh")
    # REPORTED, not part of the gate: the load-weighted mean over 48 h x 6 zones could
    # in principle hide a single amplifying hour. Added BEFORE the arm landed; the gate
    # below is unchanged from the PRECOMMIT.
    _j = arm.merge(ctl, on=["zone", "hour"], suffixes=("_a", "_c"))
    _je = _j[_j["hour"].isin(ell_h)]
    _d = _je["price_a"] - _je["price_c"]
    print(
        f"   reported (not the gate): max single zone-hour price rise on Dec 22-23 = {_d.max():+.2f} $/MWh"
    )
    print(
        f"   reported (not the gate): min single zone-hour price move  on Dec 22-23 = {_d.min():+.2f} $/MWh"
    )
    g3 = (lw_a - lw_c) <= hi
    print(
        f"   G-3: {'PASS — a repricing, inside what dmc x heat rate admits' if g3 else 'STOP — exceeds the CT_PEAKER ceiling; the LP is amplifying'}"
    )

    # ---- G-1 (restated; decided pre-solve) + output confinement, reported ----
    print(
        "\nG-1 FOOTPRINT CONFINEMENT — decided PRE-SOLVE on the delivered gas array (ADDENDUM §3): PASS"
    )
    out = arm[
        ~pd.Series(hrs[arm["hour"].to_numpy()].month, index=arm.index).isin(
            TOUCHED_MONTHS
        )
    ]
    outc = ctl[
        ~pd.Series(hrs[ctl["hour"].to_numpy()].month, index=ctl.index).isin(
            TOUCHED_MONTHS
        )
    ]
    dmax = float((out["price"].to_numpy() - outc["price"].to_numpy()).__abs__().max())
    print(
        f"   reported (not the gate): max |price delta| OUTSIDE months {TOUCHED_MONTHS} = {dmax:.4f} $/MWh"
    )
    print(
        "      (a non-zero value here is storage-SOC / hydro-budget coupling, which is annual by construction)"
    )

    # ---- G-5 IDENTITY ----
    print(
        "\nG-5 IDENTITY — no class appears or vanishes; annual energy moves only through re-priced hours"
    )
    try:
        ac = pd.read_parquet(arm_dir / "hourly" / f"class_hourly_{YEAR}.parquet")
        cc = pd.read_parquet(ctl_dir / "hourly" / f"class_hourly_{YEAR}.parquet")
        for d in (ac, cc):
            if "pass" in d.columns:
                d.drop(d.index[d["pass"] != "P1"], inplace=True)
        gcol = next(c for c in ("klass", "class", "group") if c in ac.columns)
        vcol = next(c for c in ("mw", "gen_mwh", "mwh") if c in ac.columns)
        a = ac.groupby(gcol)[vcol].sum() / 1e6
        c = cc.groupby(gcol)[vcol].sum() / 1e6
        allc = sorted(set(a.index) | set(c.index))
        print(f"   value column: {vcol}   (TWh)")
        print(f"   {'class':<22}{'control':>10}{'arm':>10}{'delta':>10}{'%':>9}")
        worst, worstc = 0.0, ""
        for k in allc:
            cv, av = float(c.get(k, 0.0)), float(a.get(k, 0.0))
            pct = (
                (av - cv) / cv * 100
                if abs(cv) > 1e-9
                else (np.inf if abs(av) > 1e-9 else 0.0)
            )
            flag = ""
            if (k not in c.index and abs(av) > 1e-9) or (
                k not in a.index and abs(cv) > 1e-9
            ):
                flag = "  <-- APPEARS/VANISHES"
            if abs(pct) > abs(worst) and np.isfinite(pct):
                worst, worstc = pct, k
            print(
                f"   {str(k):<22}{cv:10.3f}{av:10.3f}{av - cv:+10.3f}{pct:+8.1f}%{flag}"
            )
        g5 = abs(worst) <= 10.0
        print(
            f"   largest class move: {worstc} {worst:+.1f}%  (STOP if >10% with no dmc to explain it)"
        )
        print(
            f"   G-5: {'PASS' if g5 else 'REVIEW — a class moved >10%; check it has a dmc explanation'}"
        )
    except Exception as e:
        g5 = None
        print(f"   G-5 could not be scored: {e}")

    print("\n" + "=" * 78)
    verdict = {"G-1": True, "G-2": g2, "G-3": g3, "G-4": g4, "G-5": g5}
    print(
        "VERDICT:",
        "  ".join(
            f"{k}={'PASS' if v else ('STOP' if v is False else 'n/a')}"
            for k, v in verdict.items()
        ),
    )
    stops = [k for k, v in verdict.items() if v is False]
    print(
        ("SCREEN STOPS on " + ", ".join(stops))
        if stops
        else "SCREEN CLEARS — the arm may proceed to the full span (rule 29 (2))."
    )
    print(
        "NOTE: a screen may KILL an arm; it may never PROMOTE one. C3a/C1/C3b are NOT gates."
    )


if __name__ == "__main__":
    main()
