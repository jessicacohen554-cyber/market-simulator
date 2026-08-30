"""ercot-236: the h4097 manufactured-shed object — diagnosis + repair driver.

PRECOMMIT-ercot236-h4097-shed-repair-2026-08-25.md fixes the diagnosis bars
(D-0/D-1), the conditional SWCAP-clip repair spec, the V-0/V-1 verification
legs and the conditional {27, 30, 33} re-bracket before any solve. This
driver, adapted from ``ercot235_offer2023_sweep.py`` (the same official
basis, kills and baseline so the two campaigns' tables compare directly):

* ``--run <POINT>`` — replay the r10 keeper meta 2023-only with the peak
  bands ratio-scaled from the keeper's k=24 dict (``k/24``), optionally with
  ``ercot_offer_swcap_clip`` armed, into ``results/calibration/ercot236_*``.
* ``--score <POINT>`` — official C3a/C3b/C3c + the PRECOMMIT-ercot235 kills
  (baseline ``ercot234_eastex_identity`` for comparability) + the ercot-236
  additions: report vs the r10 keeper, h4097 slack, max zonal energy lambda
  (price − ordc_adder) with the count of hours >= $4,999 (the round-3
  max-offer report the ercot-235 driver never implemented).
* ``--diagnose <POINT>`` — the D-1 energy-balance attribution A/B (point vs
  the k=24 keeper) at h4097 with the h4085–4105 window table.

Grid points are local probe bundles (gitignored ``ercot236_*``); only a
selected winner is registered (rule 15, the ercot-235 pattern).

Usage:
    python scripts/probes/ercot236_h4097_repair.py --run DIAG_K30
    python scripts/probes/ercot236_h4097_repair.py --diagnose DIAG_K30
    python scripts/probes/ercot236_h4097_repair.py --run K24_CLIP K30_CLIP --score K24_CLIP K30_CLIP
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

#: The 2023-discrete keeper (k=24 baked into its offer_curve_by_group).
KEEPER_R10 = REPO / "results/calibration/ercot235_r10"
#: The ercot-235 campaign kill baseline (3-year eastex-identity keeper),
#: kept so G-COAL148 / G-OFFSEASON numbers compare across both campaigns.
BASELINE_234 = REPO / "results/calibration/ercot234_eastex_identity"
OUT_ROOT = REPO / "results/calibration"
KEEPER_K = 24.0  # k_peak baked into the r10 dict (FINDING-ercot235 winner)

GRID = {
    # D-1 diagnosis solve (PRECOMMIT-ercot236 §2): R8 re-solved at HEAD.
    "DIAG_K30": {"k_peak": 30.0, "clip": False},
    # V-0 inertness leg (§4): the keeper's own point with the clip armed.
    "K24_CLIP": {"k_peak": 24.0, "clip": True},
    # V-1 repair leg (§4) — doubles as the k=30 re-bracket point.
    "K30_CLIP": {"k_peak": 30.0, "clip": True},
    # Conditional re-bracket (§4), runs only if V-0 and V-1 pass.
    "K27_CLIP": {"k_peak": 27.0, "clip": True},
    "K33_CLIP": {"k_peak": 33.0, "clip": True},
}
PEAK_KEYS = ("peak", "phys_peak")


def scaled_ocg(k_peak: float) -> dict:
    """The r10 keeper's offer_curve_by_group with peak bands at k_peak.

    The r10 dict already carries k=24, so every peak/phys_peak/peak_ladder
    multiplier is ratio-scaled by ``k_peak / 24`` (handoff instruction; equal
    to the ercot-235 construction from the ercot-234 base at k_peak).
    """
    rc = json.loads((KEEPER_R10 / "run_config.json").read_text())
    ocg = json.loads(json.dumps(rc["scenario_config"]["offer_curve_by_group"]))
    ratio = k_peak / KEEPER_K
    for _group, bands in ocg.items():
        for k in PEAK_KEYS:
            if k in bands:
                bands[k] = round(bands[k] * ratio, 6)
        if "peak_ladder" in bands:
            bands["peak_ladder"] = [
                [share, round(mult * ratio, 6)] for share, mult in bands["peak_ladder"]
            ]
    return ocg


def _outdir(name: str) -> Path:
    return OUT_ROOT / f"ercot236_{name.lower()}"


def run_point(name: str) -> None:
    """Solve one grid point 2023-only into results/calibration/ercot236_<name>."""
    g = GRID[name]
    out = _outdir(name)
    ocg = scaled_ocg(g["k_peak"])
    cmd = [
        sys.executable,
        str(REPO / "scripts/replay_keeper.py"),
        str(KEEPER_R10),
        "--out-dir",
        str(out),
        "--years",
        "2023",
        "--set",
        "offer_curve_by_group=" + json.dumps(ocg),
    ]
    if g["clip"]:
        cmd += ["--set", "ercot_offer_swcap_clip=true"]
    cmd += [
        "--note",
        f"ercot-236 {name}: k_peak={g['k_peak']} clip={g['clip']}"
        " (PRECOMMIT-ercot236-h4097-shed-repair-2026-08-25)",
    ]
    print(f"=== {name}: k_peak={g['k_peak']} clip={g['clip']} -> {out}", flush=True)
    subprocess.run(cmd, check=True)


def _lw(bundle: Path):
    """(lw price, demand, slack, max zonal price, ordc adder) per hour."""
    import numpy as np
    import pandas as pd

    df = pd.read_parquet(bundle / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    g = df.groupby("hour")
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = g["demand"].sum()
    rng = range(8760)
    return (
        (num / den).reindex(rng).to_numpy(float),
        den.reindex(rng).to_numpy(float),
        g["slack"].sum().reindex(rng).fillna(0.0).to_numpy(float),
        g["price"].max().reindex(rng).to_numpy(float),
        g["ordc_adder"].max().reindex(rng).fillna(0.0).to_numpy(float),
    )


def score_point(name: str) -> dict:
    """Official + precommit measures for one solved grid point."""
    import numpy as np
    import pandas as pd

    out = _outdir(name)
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

    m, dem, slack, pmax_z, adder = _lw(out)
    bm, bdem, bslack, _, _ = _lw(BASELINE_234)
    km, kdem, kslack, _, _ = _lw(KEEPER_R10)
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
        mm, aa_, bb = mo_lw(m, dem, k), mo_lw(a, dem, k), mo_lw(bm, bdem, k)
        kk = mo_lw(km, kdem, k)
        monthly[mo] = {
            "model": round(mm, 2),
            "actual": round(aa_, 2),
            "baseline234": round(bb, 2),
            "keeper_k24": round(kk, 2),
        }
        if mo in (1, 2, 3, 4, 5, 10, 11, 12):
            if abs(mm - aa_) > abs(bb - aa_) + 5.0:
                offseason_kill = True
    # G-SHED-NEW vs the ercot-234 baseline 2023 set (empty) — identical to
    # the keeper r10 set (also empty), so ANY shed hour kills.
    new_shed = sorted(set(np.where(slack > 1e-6)[0]) - set(np.where(bslack > 1e-6)[0]))

    def coal_twh(bundle: Path) -> float:
        ch = pd.read_parquet(bundle / "hourly" / "class_hourly_2023.parquet")
        ch = ch[(ch["year"] == 2023) & (ch["pass"] == "P1")]
        return float(
            ch[ch["klass"].isin(["COAL_LIGNITE", "COAL_PRB"])]["mw"].sum() / 1e6
        )

    coal = coal_twh(out)
    mm_ = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    # ercot-237 Amendment 1 / owner correction pass 2026-08-26: the actual
    # band counts were hardcoded 77/43/59 (copied from the ercot-235 sweep;
    # the >=$1,000 literal was wrong — true 2023 count 61). Derived at the
    # single source, cross-checked against actual_tail.json [R-NO-MAGIC].
    sys.path.insert(0, str(REPO / "scripts/probes"))
    from ercot235_offer2023_sweep import actual_band_counts

    act = actual_band_counts(a)
    # The round-3 promised max-offer report (PRECOMMIT-ercot236 §1/§4): the
    # max zonal energy lambda (price − ordc adder) and the cap-adjacent count.
    lam = pmax_z - adder
    res = {
        "point": name,
        **GRID[name],
        "official": json.loads((out / "official_2023.json").read_text()),
        "monthly_lw": monthly,
        "kills": {
            "g_shed_new": [int(h) for h in new_shed],
            "g_offseason": bool(offseason_kill),
            "g_coal148_rise_twh": round(coal - coal_twh(BASELINE_234), 4),
        },
        "coal_rise_vs_keeper_k24_twh": round(coal - coal_twh(KEEPER_R10), 4),
        "h4097_slack_mwh": round(float(slack[4097]), 3),
        "shed_hours_mwh": {int(h): round(float(slack[h]), 3) for h in np.where(slack > 1e-6)[0]},
        "max_energy_lambda": round(float(np.nanmax(lam)), 2),
        "hours_lambda_ge_4999": int(np.nansum(lam >= 4999.0)),
        "spur_band": int(((mm_ >= 150) & (mm_ <= 500) & (aa < 150)).sum()),
        "spur_nolid": int(((mm_ >= 150) & (aa < 150)).sum()),
        "model_band_hours_vs_actual": {
            "200_500": [int(((mm_ >= 200) & (mm_ < 500)).sum()), act["200_500"]],
            "500_1000": [int(((mm_ >= 500) & (mm_ < 1000)).sum()), act["500_1000"]],
            "ge_1000": [int((mm_ >= 1000).sum()), act["ge_1000"]],
        },
    }
    (out / "ercot236_point_score.json").write_text(json.dumps(res, indent=1))
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "point",
                    "k_peak",
                    "clip",
                    "kills",
                    "h4097_slack_mwh",
                    "max_energy_lambda",
                    "hours_lambda_ge_4999",
                    "spur_band",
                    "spur_nolid",
                )
            },
            indent=1,
        ),
        flush=True,
    )
    return res


def diagnose_point(name: str) -> dict:
    """D-1: the h4097 energy-balance attribution A/B vs the k=24 keeper."""
    import numpy as np
    import pandas as pd

    out = _outdir(name)
    H, W0, W1 = 4097, 4085, 4106
    # "thermal" = every dispatched class except the variable renewables, so
    # the three deltas (thermal + renewables + net storage) span the supply
    # side of the balance and the shed attributes cleanly.
    thermal_excl = {"WIND", "SOLAR"}

    def comps(bundle: Path):
        ch = pd.read_parquet(bundle / "hourly" / "class_hourly_2023.parquet")
        ch = ch[(ch["year"] == 2023) & (ch["pass"] == "P1")]
        piv = ch.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        ).reindex(range(8760)).fillna(0.0)
        cols = piv.columns
        thermal = piv[[c for c in cols if not any(t in str(c).upper() for t in thermal_excl)]].sum(axis=1)
        renew = piv[[c for c in cols if any(t in str(c).upper() for t in ("WIND", "SOLAR"))]].sum(axis=1)
        sto = pd.read_parquet(bundle / "hourly" / "storage_2023.parquet")
        sto = sto[(sto["year"] == 2023) & (sto["pass"] == "P1")].groupby("hour")[
            ["charge_mw", "discharge_mw"]
        ].sum().reindex(range(8760)).fillna(0.0)
        rf = pd.read_parquet(bundle / "hourly" / "reserve_family_2023.parquet")
        rf = rf[(rf["year"] == 2023) & (rf["pass"] == "P1")]
        held = rf.pivot_table(
            index="hour", columns="family", values="held_mw", aggfunc="sum", observed=True
        ).reindex(range(8760)).fillna(0.0)
        sysd = pd.read_parquet(bundle / "hourly" / "system_2023.parquet")
        sysd = sysd[(sysd["year"] == 2023) & (sysd["pass"] == "P1")]
        g = sysd.groupby("hour")
        return {
            "thermal": thermal.to_numpy(float),
            "renew": renew.to_numpy(float),
            "net_dis": (sto["discharge_mw"] - sto["charge_mw"]).to_numpy(float),
            "held": held,
            "slack": g["slack"].sum().reindex(range(8760)).fillna(0.0).to_numpy(float),
            "price_min": g["price"].min().reindex(range(8760)).to_numpy(float),
            "price_max": g["price"].max().reindex(range(8760)).to_numpy(float),
        }

    d, k = comps(out), comps(KEEPER_R10)
    shed = float(d["slack"][H])
    held_delta = (d["held"].loc[H] - k["held"].loc[H]).to_dict()
    rep = {
        "point": name,
        "h": H,
        "shed_mwh": round(shed, 3),
        "delta_at_h4097": {
            "thermal": round(float(d["thermal"][H] - k["thermal"][H]), 2),
            "net_storage_discharge": round(float(d["net_dis"][H] - k["net_dis"][H]), 2),
            "renewables": round(float(d["renew"][H] - k["renew"][H]), 2),
            "reserve_held_by_family": {str(f): round(float(v), 2) for f, v in held_delta.items()},
            "reserve_held_total": round(float(sum(held_delta.values())), 2),
        },
        "zone_price_min_max_at_h4097": [
            round(float(d["price_min"][H]), 2),
            round(float(d["price_max"][H]), 2),
        ],
        "window": {
            int(h): {
                "thermal_d": round(float(d["thermal"][h]), 1),
                "thermal_k": round(float(k["thermal"][h]), 1),
                "netdis_d": round(float(d["net_dis"][h]), 1),
                "netdis_k": round(float(k["net_dis"][h]), 1),
                "slack_d": round(float(d["slack"][h]), 2),
                "price_d": round(float(d["price_max"][h]), 1),
                "price_k": round(float(k["price_max"][h]), 1),
            }
            for h in range(W0, W1)
        },
    }
    (out / "ercot236_d1_diagnosis.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({kk: rep[kk] for kk in ("point", "shed_mwh", "delta_at_h4097", "zone_price_min_max_at_h4097")}, indent=1), flush=True)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", nargs="+", choices=sorted(GRID), default=[])
    ap.add_argument("--score", nargs="+", choices=sorted(GRID), default=[])
    ap.add_argument("--diagnose", nargs="+", choices=sorted(GRID), default=[])
    args = ap.parse_args()
    for name in args.run:
        run_point(name)
    for name in args.score:
        score_point(name)
    for name in args.diagnose:
        diagnose_point(name)


if __name__ == "__main__":
    main()
