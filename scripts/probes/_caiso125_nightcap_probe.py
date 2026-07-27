"""caiso-125 diagnostic probe: clamp the OVERNIGHT hydro envelope to the bucket mean.

Rule-13 EXPLICITLY-LABELLED DIAGNOSTIC, rule-16 single-year throwaway clause:
this pins a measured *outcome* (the per-(month x hod) MEAN of EIA-930
``NG: WAT`` in hod 0-6) as the overnight ceiling — an outcome pin with no
forward analogue, so it can NEVER be a mechanism, a keeper input, or a
registered run. Its sole purpose is attribution: with overnight hydro forced
off the p95 envelope down to the measured typical level, (a) which class
fills the overnight hole (gas / import / storage — the C5a direction), and
(b) where the freed water goes (evening vs belly — the spread-compression
grip measured in FINDING-caiso125 §4). Out-dirs default under the gitignored
``results/probes/``; never registered (FINDING-caiso92b protocol).

Without ``--clamp`` this is a plain same-HEAD control (the caiso-123 pattern).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso125_nightcap_probe.py \
        --out-dir results/probes/caiso125_ctrl_2025 --years 2025
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso125_nightcap_probe.py \
        --clamp --out-dir results/probes/caiso125_nightcap_2025 --years 2025
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# replay_keeper pins MARKET_SIM_WARMSTART_XYEAR=0 at import time (before it
# imports run_calibration_full), which this probe inherits for byte
# comparability with cold-solved arms.
import replay_keeper  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER_BUNDLE = REPO / "results" / "calibration" / "caiso_netrev_margin"

# The clamp window: the caiso-125 overnight charter window, hod 0-6.
NIGHT_HODS = tuple(range(0, 7))


def _install_nightcap_clamp() -> None:
    """Monkeypatch the hydro envelope loader to clamp overnight at the bucket mean.

    Wraps :func:`market_sim.data.eia930.envelopes.measured_hydro_hourly_envelope`
    so that for hours with hod in ``NIGHT_HODS`` the returned ceiling is
    ``min(p95 envelope, mean of the (month, hod) bucket)`` of the same measured
    series. All other hours keep the real envelope. Patched on every namespace
    the solve paths resolve the symbol from at call time.
    """
    import market_sim.data.eia930 as eia930_pkg
    import market_sim.data.eia930.envelopes as env_mod
    import market_sim.data.eia_loader as facade

    real = env_mod.measured_hydro_hourly_envelope

    def _clamped(iso, year, hours, percentile=None):
        env = real(iso, year, hours, percentile)
        if env is None or iso.upper() != "CAISO":
            return env
        from market_sim.data.eia930.envelopes import _hydro_wat_month_hod
        from market_sim.data.fleet import _hour_to_month_index

        frame = _hydro_wat_month_hod(iso, year)
        if frame is None:
            return env
        work = frame.dropna(subset=["mw"])
        mean_tab = np.full((12, 24), np.nan)
        for (m, h), g in work.groupby(["month", "hod"], observed=True):
            mean_tab[m - 1, h] = float(np.mean(g["mw"].to_numpy(dtype=float)))
        rm = _hour_to_month_index(hours)
        rh = np.arange(hours) % 24
        night = np.isin(rh, NIGHT_HODS)
        bucket_mean = mean_tab[rm, rh]
        clamp = night & np.isfinite(bucket_mean)
        out = env.copy()
        out[clamp] = np.minimum(out[clamp], np.clip(bucket_mean[clamp], 0.0, None))
        print(
            f"nightcap clamp ACTIVE {iso} {year}: hod {NIGHT_HODS[0]}-"
            f"{NIGHT_HODS[-1]} ceiling p95 -> bucket mean on "
            f"{int(clamp.sum())} hours (mean cap {out[clamp].mean():.0f} MW, "
            f"was {env[clamp].mean():.0f})"
        )
        return out

    for mod in (env_mod, eia930_pkg, facade):
        mod.measured_hydro_hourly_envelope = _clamped


def _analyze(ctrl: Path, clamped: Path, year: int) -> None:
    """Compare the control and clamped arms: displacement + freed-water flow."""
    import pandas as pd

    windows = {
        "overnight": range(0, 7),
        "morning": range(7, 9),
        "belly": range(9, 16),
        "shoulder": range(16, 17),
        "evening": range(17, 22),
        "late": range(22, 24),
    }
    gas_classes = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS")

    def load(bundle: Path):
        f = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        f = f[f["pass"] == "P1"]
        piv = f.pivot_table(
            index="hour", columns="klass", values="mw", observed=True
        ).sort_index()
        s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        s = s[s["pass"] == "P1"]
        ca = s[~s["zone"].str.startswith("WECC")]
        lam = (
            (ca["price"] * ca["demand"]).groupby(ca["hour"]).sum()
            / ca["demand"].groupby(ca["hour"]).sum()
        ).sort_index()
        by_hour = s.groupby("hour")[["demand", "slack", "dump"]].sum().sort_index()
        storage_net = (
            by_hour["demand"] - by_hour["slack"] + by_hour["dump"] - piv.sum(axis=1)
        )
        return piv, lam, storage_net

    pc, lc, sc = load(ctrl)
    pp, lp, sp = load(clamped)
    hod = np.arange(len(pc)) % 24
    print(f"=== nightcap probe A/B, {year} (clamped - control, window mean MW) ===")
    print(
        f"{'window':>10} {'hydro':>7} {'gas':>7} {'import':>7} {'storage':>8} "
        f"{'lam ctrl':>9} {'lam clmp':>9}"
    )
    for name, win in windows.items():
        sel = np.isin(hod, list(win))
        d_hydro = float((pp["hydro"] - pc["hydro"])[sel].mean())
        gas_p = pp[[c for c in gas_classes if c in pp]].sum(axis=1)
        gas_c = pc[[c for c in gas_classes if c in pc]].sum(axis=1)
        d_gas = float((gas_p - gas_c)[sel].mean())
        d_imp = float((pp["import"] - pc["import"])[sel].mean())
        d_sto = float((sp - sc)[sel].mean())
        print(
            f"{name:>10} {d_hydro:>+7.0f} {d_gas:>+7.0f} {d_imp:>+7.0f} "
            f"{d_sto:>+8.0f} {lc[sel].mean():>9.2f} {lp[sel].mean():>9.2f}"
        )
    print(
        f"annual: hydro {(pp['hydro'].sum() - pc['hydro'].sum()) / 1e6:+.3f} TWh, "
        f"gas {(pp[[c for c in gas_classes if c in pp]].sum(axis=1).sum() - pc[[c for c in gas_classes if c in pc]].sum(axis=1).sum()) / 1e6:+.3f} TWh, "
        f"import {(pp['import'].sum() - pc['import'].sum()) / 1e6:+.3f} TWh, "
        f"CA lam {lc.mean():.3f} -> {lp.mean():.3f} "
        f"({(lp.mean() / lc.mean() - 1) * 100:+.2f} %)"
    )


def main() -> None:
    """Solve the keeper recipe, optionally with the overnight clamp."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--clamp",
        action="store_true",
        help="clamp the overnight hydro ceiling to the measured bucket mean "
        "(omit for a plain same-HEAD control)",
    )
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2025])
    ap.add_argument("--note", default=None)
    ap.add_argument(
        "--analyze",
        nargs=2,
        metavar=("CTRL", "CLAMPED"),
        default=None,
        help="no solve: compare a solved control/clamped pair for --years[0]",
    )
    args = ap.parse_args()

    if args.analyze:
        _analyze(Path(args.analyze[0]), Path(args.analyze[1]), int(args.years[0]))
        return

    if args.clamp:
        _install_nightcap_clamp()

    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["note"] = args.note or (
        "caiso-125 DIAGNOSTIC probe (rule 13 outcome-pin, attribution only, "
        "never registered): keeper recipe at HEAD"
        + (
            " + overnight hod0-6 hydro ceiling clamped to the measured "
            "(month x hod) bucket MEAN"
            if args.clamp
            else " (plain same-HEAD control)"
        )
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
