"""ercot-235 round 1: the 2023-discrete-config offer-surface sweep driver.

PRECOMMIT-ercot235-2023-discrete-offer-sweep-2026-08-25.md fixes the grid,
gates and selection rule. This driver, per grid point: scales the keeper
recipe's ``offer_curve_by_group`` gas-group top bands (``peak``,
``peak_ladder`` multipliers, ``phys_peak`` by k_peak; ``econ_high``/
``phys_econ_high`` by k_eh), replays the keeper meta 2023-ONLY via
``replay_keeper.py --set``, and scores the result (official C3a/C3b/C3c via
``ercot226_official_score`` plus the precommit's kill/report measures).

The swept scalars are residual-identified 2023 tuning values on the rule-1
sanctioned surface, run under the owner's 2023-discrete-config order
(rule-16 waiver invoked; see the ercot-235 log entry). Sweep bundles are
local probe bundles (gitignored); only the selected winner is registered.

Usage:
    python scripts/probes/ercot235_offer2023_sweep.py --run R1 R2 R3
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/ercot234_eastex_identity"
OUT_ROOT = REPO / "results/calibration"
GRID = {
    "R1": {"k_peak": 3.0, "k_eh": 1.0},
    "R2": {"k_peak": 3.0, "k_eh": 1.75},
    "R3": {"k_peak": 5.0, "k_eh": 2.5},
    # Round 2 (precommit amendment): econ_high excluded (the corrupt lever,
    # G-COAL148 kills at 1.75/2.5); peak-band family alone, pushed harder.
    "R4": {"k_peak": 6.0, "k_eh": 1.0},
    "R5": {"k_peak": 10.0, "k_eh": 1.0},
    "R6": {"k_peak": 14.0, "k_eh": 1.0},
    # Round 3 (precommit amendment 2): the peak-only response is monotone and
    # kill-clean through k=14; extend toward the measured 2023 ask range
    # ($3.4-5k at k~40-50).
    "R7": {"k_peak": 20.0, "k_eh": 1.0},
    "R8": {"k_peak": 30.0, "k_eh": 1.0},
    "R9": {"k_peak": 45.0, "k_eh": 1.0},
    # Round 4 (precommit amendment 3, LAST round this session): bracket the
    # clean frontier between R7 (20, clean) and R8 (30, h4097 shed kill).
    "R10": {"k_peak": 24.0, "k_eh": 1.0},
    "R11": {"k_peak": 27.0, "k_eh": 1.0},
}
PEAK_KEYS = ("peak", "phys_peak")
EH_KEYS = ("econ_high", "phys_econ_high")


def actual_band_counts(a) -> dict:
    """Actual-side 2023 RT band counts, DERIVED from the loaded actual series.

    ercot-237 Amendment 1 / owner correction pass 2026-08-26: these counts
    were previously HARDCODED here as 77/43/59 and copied into the ercot-236
    scorer — the actual side was never computed from data, and the >=$1,000
    literal was WRONG (true 2023 count: 61; 77+43+61 = 181). Derivation
    replaces the literals so a stale constant cannot propagate again
    [R-NO-MAGIC]; the band sum is cross-checked against the committed tail
    record (frontend/data/backcast/tail/actual_tail.json, ERCOT 2023 rt_gt,
    threshold $200) and any mismatch fails loudly rather than scoring.
    """
    import numpy as np

    af = a[np.isfinite(a)]
    counts = {
        "200_500": int(((af >= 200) & (af < 500)).sum()),
        "500_1000": int(((af >= 500) & (af < 1000)).sum()),
        "ge_1000": int((af >= 1000).sum()),
    }
    tail = json.loads(
        (REPO / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )["isos"]["ERCOT"]["2023"]
    if sum(counts.values()) != tail["rt_gt"]:
        raise AssertionError(
            f"actual band counts {counts} sum to {sum(counts.values())} != "
            f"actual_tail.json ERCOT 2023 rt_gt {tail['rt_gt']}"
        )
    return counts


def scaled_ocg(k_peak: float, k_eh: float) -> dict:
    """The keeper's offer_curve_by_group with top bands scaled (all groups)."""
    rc = json.loads((KEEPER / "run_config.json").read_text())
    ocg = json.loads(json.dumps(rc["scenario_config"]["offer_curve_by_group"]))
    for _group, bands in ocg.items():
        for k in PEAK_KEYS:
            if k in bands:
                bands[k] = round(bands[k] * k_peak, 6)
        for k in EH_KEYS:
            if k in bands:
                bands[k] = round(bands[k] * k_eh, 6)
        if "peak_ladder" in bands:
            bands["peak_ladder"] = [
                [share, round(mult * k_peak, 6)] for share, mult in bands["peak_ladder"]
            ]
    return ocg


def run_point(name: str) -> None:
    """Solve one grid point 2023-only into results/calibration/ercot235_<name>."""
    g = GRID[name]
    out = OUT_ROOT / f"ercot235_{name.lower()}"
    ocg = scaled_ocg(g["k_peak"], g["k_eh"])
    cmd = [
        sys.executable,
        str(REPO / "scripts/replay_keeper.py"),
        str(KEEPER),
        "--out-dir",
        str(out),
        "--years",
        "2023",
        "--set",
        "offer_curve_by_group=" + json.dumps(ocg),
        "--note",
        f"ercot-235 {name}: 2023-discrete offer sweep k_peak={g['k_peak']} k_eh={g['k_eh']}"
        " (owner 2023-discrete-config order; PRECOMMIT-ercot235)",
    ]
    print(f"=== {name}: k_peak={g['k_peak']} k_eh={g['k_eh']} -> {out}", flush=True)
    subprocess.run(cmd, check=True)


def score_point(name: str) -> dict:
    """Official + precommit measures for one solved grid point."""
    import numpy as np
    import pandas as pd

    out = OUT_ROOT / f"ercot235_{name.lower()}"
    off = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/probes/ercot226_official_score.py"),
            "--bundle",
            str(out),
            "--years",
            "2023",
            "--json-out",
            str(out / "official_2023.json"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(off.stdout.strip(), flush=True)

    def lw(bundle: Path) -> tuple[np.ndarray, np.ndarray]:
        df = pd.read_parquet(bundle / "hourly" / "system_2023.parquet")
        df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
        num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        g = df.groupby("hour")
        return (
            (num / den).reindex(range(8760)).to_numpy(float),
            den.reindex(range(8760)).to_numpy(float),
            g["slack"].sum().reindex(range(8760)).fillna(0.0).to_numpy(float),
        )

    m, dem, slack = lw(out)
    km, kdem, kslack = lw(KEEPER)
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    a = a[a["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    cum = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    mon = np.searchsorted(cum, np.arange(8760), side="right")

    def mo_lw(x, w, k):
        return float(np.nansum(x[k] * w[k]) / np.nansum(w[k]))

    monthly = {}
    offseason_kill = False
    for mo in range(1, 13):
        k = mon == mo
        mm, aa_, kk = mo_lw(m, dem, k), mo_lw(a, dem, k), mo_lw(km, kdem, k)
        monthly[mo] = {"model": round(mm, 2), "actual": round(aa_, 2), "keeper": round(kk, 2)}
        if mo in (1, 2, 3, 4, 5, 10, 11, 12):
            if abs(mm - aa_) > abs(kk - aa_) + 5.0:
                offseason_kill = True
    new_shed = sorted(set(np.where(slack > 1e-6)[0]) - set(np.where(kslack > 1e-6)[0]))

    def coal_twh(bundle: Path) -> float:
        ch = pd.read_parquet(bundle / "hourly" / "class_hourly_2023.parquet")
        ch = ch[(ch["year"] == 2023) & (ch["pass"] == "P1")]
        return float(
            ch[ch["klass"].isin(["COAL_LIGNITE", "COAL_PRB"])]["mw"].sum() / 1e6
        )

    coal_rise = coal_twh(out) - coal_twh(KEEPER)
    mm_ = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    act = actual_band_counts(a)
    bands = {
        "200_500": [int(((mm_ >= 200) & (mm_ < 500)).sum()), act["200_500"]],
        "500_1000": [int(((mm_ >= 500) & (mm_ < 1000)).sum()), act["500_1000"]],
        "ge_1000": [int((mm_ >= 1000).sum()), act["ge_1000"]],
    }
    res = {
        "point": name,
        **GRID[name],
        "official": json.loads((out / "official_2023.json").read_text()),
        "monthly_lw": monthly,
        "kills": {
            "g_shed_new": [int(h) for h in new_shed],
            "g_offseason": bool(offseason_kill),
            "g_coal148_rise_twh": round(coal_rise, 4),
        },
        "spur_band": int(((mm_ >= 150) & (mm_ <= 500) & (aa < 150)).sum()),
        "spur_nolid": int(((mm_ >= 150) & (aa < 150)).sum()),
        "model_band_hours_vs_actual": bands,
    }
    (out / "ercot235_point_score.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("point", "k_peak", "k_eh", "kills", "spur_band", "spur_nolid", "model_band_hours_vs_actual")}, indent=1), flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", nargs="+", choices=sorted(GRID), required=True)
    ap.add_argument("--score-only", action="store_true")
    args = ap.parse_args()
    for name in args.run:
        if not args.score_only:
            run_point(name)
        score_point(name)


if __name__ == "__main__":
    main()
