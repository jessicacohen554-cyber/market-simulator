"""pjm-158 Phase 0.2 (cont.) — the virtual layer's PRICE-BASIS mismatch.

``_pjm158_virtual_gain.py`` attributes ~99 % of the layer's deviation from its
rule-13 anchor to the model's price LEVEL, with the rung compression exact.
This probe asks the follow-up question that attribution raises:

**against which price is the anchor even defined?**

The measured ``hrl_da_incs_decs`` curves are submitted into, and clear in, the
**Day-Ahead** market — pjm-105's ≈ 0 admissibility reference is computed at
actual **DA** prices.  But the model's energy dual is calibrated and scored as
a **real-time** marginal-energy analogue: ``render_calibration_html`` builds
``lmpDeltaHr`` as ``model − _actual_rt_padded`` precisely because "the model's
clearing price is a real-time marginal-energy analogue (no day-ahead
unit-commitment smoothing)".

So even a model whose dual reproduced actual RT **exactly** would clear this
DA-submitted curve at the wrong price, by the DA-RT basis.  With a measured
gain of ≈ −400 MW per $/MWh, a systematic DA-RT spread of a few $/MWh is worth
several TWh/yr of phantom energy.  This probe measures that term and separates
it from the model's own price error:

    observed deviation = [DA-RT basis]  +  [model's error vs actual RT]

Reads the same in-sample 2023-2025 corpus and the same committed sidecars; no
solve, no scoring, no out-of-training year.

Run:  .venv/bin/python scripts/probes/_pjm158_virtual_basis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pjm158_virtual_gain import (  # noqa: E402
    TWH,
    YEARS,
    _on_model_clock,
    build_hour_arrays,
    eval_net_fast,
    load_curve,
    model_cleared,
    model_zonal,
    zonal_sum,
)

HUBS = ("WESTERN HUB", "EASTERN HUB", "AEP-DAYTON HUB", "DOMINION HUB")

#: The repo's own committed PJM system LMP series — the SAME reference
#: ``scripts/probes/_pjm105_symmetric_equilibrium.py`` cleared the ladders at
#: when it established the mechanism's ≈ 0 admissibility anchor.  Anything else
#: below is a sensitivity check against it, never a replacement for it.
CANON = Path("data/raw/_validation-source/actual_lmp_hourly_PJM.parquet")


def canonical_prices(year: int) -> dict[str, np.ndarray]:
    """The canonical committed PJM DA and RT system LMP series, model clock."""
    df = pd.read_parquet(CANON)
    df = df[df["year"] == year]
    out = {}
    for run in ("da", "rt"):
        a = np.full(8760, np.nan)
        idx = df["hour"].to_numpy(dtype=int)
        keep = (idx >= 0) & (idx < 8760)
        a[idx[keep]] = df[run].to_numpy(dtype=float)[keep]
        out[f"{run}:CANON"] = pd.Series(a).ffill().bfill().to_numpy()
    return out


def hub_prices(year: int) -> dict[str, np.ndarray]:
    """Hourly DA and RT reference prices on the model clock, per hub and mean."""
    path = Path("data/raw/lmp-data") / f"PJM_{year}_rt_da_monthly_lmps.csv"
    f = pd.read_csv(path)
    f["ept"] = pd.to_datetime(f["datetime_beginning_ept"], format="mixed")
    f = f[f["ept"].dt.year == year]
    out: dict[str, np.ndarray] = dict(canonical_prices(year))
    for run in ("da", "rt"):
        col = f"total_lmp_{run}"
        out[f"{run}:ALL_HUBS"] = _on_model_clock(
            f.groupby("ept")[col].mean().sort_index(), year
        )
        for h in HUBS:
            s = f[f["pnode_name"] == h].groupby("ept")[col].mean().sort_index()
            if len(s):
                out[f"{run}:{h}"] = _on_model_clock(s, year)
    return out


def main() -> None:
    pd.set_option("display.width", 190)
    print("=" * 92)
    print("pjm-158 — the DA virtual layer's PRICE-BASIS mismatch")
    print("=" * 92)

    rows = []
    for year in YEARS:
        bids = load_curve(year)
        hours = build_hour_arrays(bids)
        px = hub_prices(year)
        price_z, share_z, lam_m = model_zonal(year)
        vinc, vdec = model_cleared(year)
        observed = -(vinc + vdec)  # + = net virtual DEMAND

        print(f"\n{'#' * 74}\n#  {year}\n{'#' * 74}")

        print("\n--- reference-price sensitivity: annual net cleared (TWh) ---")
        print("  (+ = net virtual DEMAND; the mechanism's admissibility claim is ~0)")
        anchors = {}
        for k in sorted(px):
            v = eval_net_fast(hours, px[k]).sum() / TWH
            anchors[k] = v
            print(f"    {k:24s} mean ${px[k].mean():6.2f}/MWh   net {v:+7.3f}")

        da, rt = px["da:CANON"], px["rt:CANON"]
        a_da, a_rt = anchors["da:CANON"], anchors["rt:CANON"]
        basis = a_rt - a_da
        model_err = observed - a_rt

        print("\n--- the two terms of the deviation (TWh) ---")
        print(f"  anchor @ actual DA (the rule-13 reference)      {a_da:+7.3f}")
        print(f"  anchor @ actual RT (the model's own price target){a_rt:+7.3f}")
        print(f"  ==> DA-RT BASIS term                            {basis:+7.3f}"
              "   <- present even with a PERFECT RT price")
        print(f"  observed (the LP's own clearing)                {observed:+7.3f}")
        print(f"  ==> model's own error vs actual RT              {model_err:+7.3f}")
        print(f"  TOTAL deviation from the DA anchor              {observed - a_da:+7.3f}")

        print("\n--- the DA-RT spread that drives the basis term ---")
        d = da - rt
        print(f"  mean DA-RT {d.mean():+6.2f} $/MWh   MAE {np.abs(d).mean():6.2f}   "
              f"hours DA>RT {int((d > 0).sum()):5d} / 8760")
        # LEVEL vs SHAPE. ``a_mid`` clears at RT's hour-by-hour SHAPE carrying
        # DA's MEAN, so it sits exactly between the two anchors:
        #   a_mid − a_da  = shape/dispersion (same mean, different shape)
        #   a_rt  − a_mid = level            (same shape, different mean)
        # Cross-check: the level leg must equal −mean(DA−RT) × the measured
        # gain; it does, to ~1 % (2024: 0.256 × 462.8 MW × 8760 h = 1.04 TWh).
        a_mid = eval_net_fast(hours, rt + d.mean()).sum() / TWH
        shape_term = a_mid - a_da
        level_term = a_rt - a_mid
        print(f"  basis split: LEVEL {level_term:+6.3f} TWh   "
              f"SHAPE/dispersion {shape_term:+6.3f} TWh"
              f"   (mid anchor {a_mid:+.3f}; sum {level_term + shape_term:+.3f} "
              f"vs basis {basis:+.3f})")
        print(f"  model dual: mean ${lam_m.mean():6.2f}  vs DA ${da.mean():6.2f}  "
              f"vs RT ${rt.mean():6.2f};  MAE vs RT {np.abs(lam_m - rt).mean():5.2f}")

        # Counterfactual: what would the layer clear if the model's dual were
        # EXACTLY the actual RT price, zone by zone?  (basis term, zonally.)
        perfect_rt = zonal_sum(
            lambda lz: eval_net_fast(hours, rt), price_z, share_z
        ).sum() / TWH
        print(f"\n  counterfactual — a model whose dual IS actual RT clears "
              f"{perfect_rt:+.3f} TWh")
        print(f"  i.e. {100 * abs(basis) / max(abs(observed - a_da), 1e-9):5.1f}% of the "
              "observed deviation survives a perfect RT price.")

        rows.append(
            {
                "year": year,
                "anchor_DA": a_da,
                "anchor_RT": a_rt,
                "basis_DA_RT": basis,
                "observed": observed,
                "model_err_vs_RT": model_err,
                "total_dev": observed - a_da,
                "basis_share_pct": 100 * abs(basis) / max(abs(observed - a_da), 1e-9),
                "mean_DA_minus_RT": float(d.mean()),
                "hub_spread_TWh": max(anchors[k] for k in anchors if k.startswith("da:"))
                - min(anchors[k] for k in anchors if k.startswith("da:")),
            }
        )

    print("\n" + "=" * 92)
    print("SUMMARY (TWh, + = net virtual DEMAND / phantom load)")
    print("=" * 92)
    df = pd.DataFrame(rows).set_index("year")
    print(df.round(3).to_string())
    Path("results/calibration/_pjm158_virtual_basis.json").write_text(
        json.dumps(rows, indent=2, default=float)
    )


if __name__ == "__main__":
    main()
