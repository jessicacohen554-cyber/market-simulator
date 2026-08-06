"""pjm-158 Phase 0.2 (cont.) — does the layer still RESHAPE, or does it just add?

pjm-105's structural claim for the symmetric net form is that it is "a
time-of-day reshaper, not a volume adder": at actual DA prices the INC side
clears overnight/evening (h19-02, up to 3.9 GW mean) and the DEC side on the
morning ramp / afternoon, so the annual net is ≈ 0 while the hourly position
is large.  That claim is what separates it from the condemned pjm-102 clamp.

This probe checks whether the LP's OWN clearing preserves that shape.  It
compares, hour-of-day:

* the reference position — the raw measured curve cleared at the actual DA
  price (what the real DA market did), and
* the model position — the committed ``VIRTUAL_INC`` / ``VIRTUAL_DEC`` P1
  class hourlies (what the LP actually did).

In-sample 2023-2025 only; committed artifacts plus the measured corpus; no
solve, no scoring, no out-of-training year.

Run:  .venv/bin/python scripts/probes/_pjm158_virtual_shape.py
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
    BUNDLE,
    TWH,
    YEARS,
    build_hour_arrays,
    eval_net_fast,
    load_curve,
)
from _pjm158_virtual_basis import canonical_prices  # noqa: E402


def model_hourly_net(year: int) -> np.ndarray:
    """Model hourly net virtual DEMAND in MW (+ = phantom load), P1."""
    ch = pd.read_parquet(f"{BUNDLE}/hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(["VIRTUAL_INC", "VIRTUAL_DEC"]))]
    s = ch.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0)
    return -s.to_numpy(dtype=float)  # sidecar: INC +, DEC −; flip to net demand


def main() -> None:
    pd.set_option("display.width", 200)
    print("=" * 84)
    print("pjm-158 — hour-of-day shape: reference vs the LP's own clearing")
    print("=" * 84)
    print("(GW, + = net virtual DEMAND / phantom load; − = net virtual SUPPLY)")

    out = []
    for year in YEARS:
        bids = load_curve(year)
        hours = build_hour_arrays(bids)
        da = canonical_prices(year)["da:CANON"]
        ref = eval_net_fast(hours, da) / 1e3  # GW
        mod = model_hourly_net(year) / 1e3
        hod = np.arange(8760) % 24
        r = pd.Series(ref).groupby(hod).mean()
        m = pd.Series(mod).groupby(hod).mean()

        print(f"\n--- {year} ---")
        print("  h   " + " ".join(f"{h:6d}" for h in range(24)))
        print("  ref " + " ".join(f"{r[h]:6.2f}" for h in range(24)))
        print("  mod " + " ".join(f"{m[h]:6.2f}" for h in range(24)))
        print("  Δ   " + " ".join(f"{m[h] - r[h]:6.2f}" for h in range(24)))
        corr = float(np.corrcoef(r.to_numpy(), m.to_numpy())[0, 1])
        peak_r, peak_m = r[14:19].mean(), m[14:19].mean()
        night_r, night_m = r[[*range(0, 4), *range(19, 24)]].mean(), m[
            [*range(0, 4), *range(19, 24)]
        ].mean()
        print(
            f"  hour-of-day corr(ref, model) = {corr:+.3f}   "
            f"afternoon h14-18: ref {peak_r:+.2f} model {peak_m:+.2f} GW   "
            f"overnight h19-03: ref {night_r:+.2f} model {night_m:+.2f} GW"
        )
        print(
            f"  annual net: ref {ref.sum() * 1e3 / TWH:+.3f} TWh   "
            f"model {mod.sum() * 1e3 / TWH:+.3f} TWh   "
            f"mean |position|: ref {np.abs(ref).mean():.2f} GW "
            f"model {np.abs(mod).mean():.2f} GW"
        )
        out.append(
            {
                "year": year,
                "hod_corr": corr,
                "ref_peak_GW": float(peak_r),
                "model_peak_GW": float(peak_m),
                "ref_night_GW": float(night_r),
                "model_night_GW": float(night_m),
                "ref_abs_GW": float(np.abs(ref).mean()),
                "model_abs_GW": float(np.abs(mod).mean()),
            }
        )

    print("\n" + "=" * 84)
    print(pd.DataFrame(out).set_index("year").round(3).to_string())
    Path("results/calibration/_pjm158_virtual_shape.json").write_text(
        json.dumps(out, indent=2, default=float)
    )


if __name__ == "__main__":
    main()
