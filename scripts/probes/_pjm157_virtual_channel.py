"""pjm-157 §1.1 — the PJM DA virtual layer as a price-error -> quantity-error channel.

Measures two things from committed artifacts only (no LP, no scoring — legal
under the active holdout freeze, CLAUDE.md rule 22):

1. **The layer's net cleared volume by year and month.**  ``pjm_da_virtual_bids``
   renders the measured submitted INC/DEC curves as LP pseudo-units.  They carry
   no bench class, but they ARE columns on the energy balance, so their net
   clearing is real MWh the physical fleet must serve (``net < 0``) or displace
   (``net > 0``).  The mechanism's own rule-13 admissibility argument
   (``data/virtual_bids.py`` docstring, citing pjm-105) is that the annual net of
   the whole curve **cleared at actual DA prices is ~ 0** — measured there as
   -0.68 / -0.95 / +1.32 TWh for 2023/24/25.  This probe reports what the model
   actually clears against its own dual, i.e. the deviation from that anchor.

2. **The transmission channel.**  Decodes each run payload's ``lmpDeltaHr``
   (model minus actual hourly $/MWh, int16 with -32768 as the NaN sentinel) and
   conditions the net clearing on the sign of the price error.  A consistent
   "model under actual -> net virtual demand" relation is what makes C1 (a
   quantity gate) conditional on C3b (a price gate), with a gain that scales
   with the price level.
"""

from __future__ import annotations

import base64
import gzip
import json
import re

import numpy as np
import pandas as pd

TWH = 1e6

BUNDLES = {
    2022: "results/calibration/pjm2022_touchpoint",
    2023: "results/calibration/pjm152_collapse_A",
    2024: "results/calibration/pjm152_collapse_A",
    2025: "results/calibration/pjm152_collapse_A",
}
PAYLOADS = {
    2022: "frontend/data/backcast/runs/2026-08-05-pjm-2022-touchpoint.js",
    2023: "frontend/data/backcast/runs/2026-08-04-pjm-152-collapse.js",
    2024: "frontend/data/backcast/runs/2026-08-04-pjm-152-collapse.js",
    2025: "frontend/data/backcast/runs/2026-08-04-pjm-152-collapse.js",
}

#: pjm-105's measured reference: annual net of the whole submitted curve cleared
#: at ACTUAL DA prices (docs/FINDING-pjm-midmerit-level-2026-07.md §7).  2022 is
#: not computable here — the raw hrl_da_incs_decs corpus is gitignored.
PJM105_REFERENCE_TWH = {2023: -0.68, 2024: -0.95, 2025: 1.32}


def load_payload(path: str) -> dict:
    """Decode a committed dashboard run payload (``window.BC.runGz`` gzip+base64).

    Args:
        path: path to the ``runs/<id>.js`` file.

    Returns:
        The decoded run dict (``label``, ``years``).
    """
    src = open(path, encoding="utf-8").read()
    blob = re.search(r'runGz\["[^"]+"\]="([^"]+)"', src).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def net_virtual_mw(year: int, bundle: str) -> np.ndarray:
    """Return the hourly net cleared virtual position in MW (+ = net supply).

    Args:
        year: solve year.
        bundle: bundle directory holding ``hourly/class_hourly_<year>.parquet``.

    Returns:
        Length-8760 array of ``VIRTUAL_INC + VIRTUAL_DEC`` (DEC is already signed
        negative in the sidecar).
    """
    ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(["VIRTUAL_INC", "VIRTUAL_DEC"]))]
    piv = (
        ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .fillna(0.0)
        .reindex(range(8760), fill_value=0.0)
    )
    return (piv.get("VIRTUAL_INC", 0.0) + piv.get("VIRTUAL_DEC", 0.0)).to_numpy()


def lmp_delta(payload: dict, year: int) -> np.ndarray:
    """Return the hourly model-minus-actual LMP series in $/MWh, NaN where absent.

    Args:
        payload: decoded run payload.
        year: solve year key.

    Returns:
        Length-8760 float array; the int16 sentinel -32768 becomes ``np.nan``.
    """
    raw = np.frombuffer(
        base64.b64decode(payload["years"][str(year)]["lmpDeltaHr"]), dtype="<i2"
    ).astype(float)
    raw[raw == -32768] = np.nan
    return raw


def main() -> None:
    """Print the annual/monthly clearing tables and the price-error conditioning."""
    print("MODEL NET VIRTUAL CLEARING (INC supply + DEC withdrawal), TWh")
    print("  positive = net virtual SUPPLY (displaces physical generation)")
    print("  negative = net virtual DEMAND (phantom load the fleet must serve)")
    print()
    print(
        f"{'yr':>5}{'INC':>9}{'DEC':>9}{'NET':>9}{'gross':>9}"
        f"{'pjm-105 ref':>13}{'deviation':>11}"
    )
    monthly = {}
    for year, bundle in BUNDLES.items():
        net = net_virtual_mw(year, bundle)
        ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        cls = ch.groupby("klass")["mw"].sum() / TWH
        inc, dec = cls.get("VIRTUAL_INC", 0.0), cls.get("VIRTUAL_DEC", 0.0)
        ref = PJM105_REFERENCE_TWH.get(year)
        idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        monthly[year] = pd.Series(net, index=idx).resample("MS").sum() / TWH
        ref_s = f"{ref:>13.2f}" if ref is not None else f"{'n/a':>13}"
        dev_s = f"{net.sum() / TWH - ref:>11.2f}" if ref is not None else f"{'n/a':>11}"
        print(
            f"{year:>5}{inc:>9.2f}{dec:>9.2f}{net.sum() / TWH:>9.2f}"
            f"{inc - dec:>9.2f}{ref_s}{dev_s}"
        )

    print()
    print("MONTHLY NET VIRTUAL (TWh, + = net supply)")
    mdf = pd.DataFrame(
        {y: monthly[y].to_numpy() for y in sorted(monthly)},
        index=[f"{m:02d}" for m in range(1, 13)],
    )
    print(mdf.round(2).to_string())

    print()
    print("TRANSMISSION CHANNEL — net clearing conditioned on the model's price error")
    print(
        f"{'yr':>5}{'MAE dLMP':>10}{'mean dLMP':>11}{'corr':>8}"
        f"{'hrs UNDER':>11}{'net|under':>11}{'hrs OVER':>10}{'net|over':>10}"
    )
    for year, bundle in BUNDLES.items():
        net = net_virtual_mw(year, bundle)
        d = lmp_delta(load_payload(PAYLOADS[year]), year)
        ok = np.isfinite(d)
        lo, hi = (d < 0) & ok, (d > 0) & ok
        corr = np.corrcoef(d[ok], net[ok])[0, 1]
        print(
            f"{year:>5}{np.nanmean(np.abs(d)):>10.2f}{np.nanmean(d):>11.2f}{corr:>8.3f}"
            f"{lo.sum():>11}{net[lo].sum() / TWH:>11.2f}"
            f"{hi.sum():>10}{net[hi].sum() / TWH:>10.2f}"
        )


if __name__ == "__main__":
    main()
