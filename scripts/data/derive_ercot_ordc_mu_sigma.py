"""Derive ERCOT's published seasonal ORDC mu / sigma from the Biennial ORDC Reports.

ERCOT re-derives the ORDC reserve-error distribution once per season (Dec /
Mar / Jun / Sep) and posts it as NP6-576-ER ("LOLP Distribution by Season and
TOD Block", MIS report 13233). The MIS listing is retention-expired on the free
path (it returns no documents) and the credentialed api.ercot.com archive is
owner-declined (``scripts/data/fetch_ercot_as_reports.py`` docstring), so the
values are read from the one public place ERCOT re-plots them: Figure 3,
"Timeline of relevant ORDC parameters", of

* the 2022 Biennial ERCOT Report on the ORDC (seasons Mar 2018 - Jun 2022),
  ``data/raw/ercot/ordc-biennial/2022-biennial-ordc-report.pdf``;
* the 2024 Biennial ERCOT Report on the ORDC (Mar 2018 - Sep 2024),
  ``data/raw/ercot/ordc-biennial/2024-biennial-ordc-report.pdf``.

The plotted "ORDC Mu" INCLUDES the PUCT 48551 shift (its Mar-2019 and Mar-2020
steps are each ~0.25 sigma), so the column written is ``mu_shifted_mw`` = the
OBD's ``mu_s = mu + S * sigma``. Since 2019 ERCOT computes one mu / sigma per
season (no time-of-day blocks; both reports' Figure 3 notes); the Dec-2018
season is the report's average of its six TOD values.

Digitization (rule 14 reconciliation, declared): the figures are raster. The
right (MW) axis is calibrated inside each figure on the ORDC Minimum
Contingency Level line, which sits at a published 2,000 MW before 2022-01-01
and 3,000 MW after; the quarter grid is anchored on that same step
(2022-01-01) and the sigma-marker spacing. Each season's value is the median
line row across the middle 40 % of its flat segment. Resolution: 6.3 MW/px
(2022 report) and 11.5 MW/px (2024 report); on the 15 seasons both report,
the two reads differ by -8 +/- 5 MW (mu) and -5 +/- 5 MW (sigma) — one pixel of
the coarser figure. No offset is applied between them. The 2022 report is used
through the Jun-2022 season (finer), the 2024 report from Sep-2022.

The PNGs are the figures' embedded images, extracted losslessly with
``pdfimages -png -f 13 -l 13 2024-...pdf`` / ``-f 9 -l 9 2022-...pdf``.

Writes ``data/raw/ercot/ercot_ordc_mu_sigma_seasonal.csv``. Frozen (rule 23):
re-derive only when ERCOT publishes a report with new seasons.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/raw/ercot/ordc-biennial"
OUT = ROOT / "data/raw/ercot/ercot_ordc_mu_sigma_seasonal.csv"

SIGMA_RGB, MU_RGB, MCL_RGB = (0, 56, 101), (91, 103, 112), (104, 91, 199)
MCL_STEP_DATE = pd.Timestamp("2022-01-01")  # MCL 2,000 -> 3,000 MW (OBDRR038)
FIGURES = {
    # report -> (png, seasons taken from it)
    "2022": ("fig3-2022-biennial.png", ("2018-12-01", "2022-06-01")),
    "2024": ("fig3-2024-biennial.png", ("2022-09-01", "2024-09-01")),
}


def read_png(path: Path) -> np.ndarray:
    """Decode an 8-bit RGB / RGBA non-interlaced PNG to an ``(H, W, 3)`` int array."""
    data = path.read_bytes()
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos : pos + 4])
        kind, body = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            if depth != 8 or ctype not in (2, 6) or inter:
                raise ValueError(f"{path.name}: unsupported PNG layout")
            ch = 3 if ctype == 2 else 4
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw = np.frombuffer(zlib.decompress(idat), dtype=np.uint8)
    stride = w * ch
    rows = raw.reshape(h, stride + 1)
    out = np.zeros((h, stride), dtype=np.int32)
    prev = np.zeros(stride, dtype=np.int32)
    for y in range(h):
        f, line = rows[y, 0], rows[y, 1:].astype(np.int32)
        cur = np.zeros(stride, dtype=np.int32)
        for x in range(stride):  # PNG filters are sequential by definition
            a = cur[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 0:
                p = 0
            elif f == 1:
                p = a
            elif f == 2:
                p = b
            elif f == 3:
                p = (a + b) // 2
            else:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                p = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            cur[x] = (line[x] + p) & 0xFF
        out[y], prev = cur, cur
    return out.reshape(h, w, ch)[:, :, :3]


def _mask(img: np.ndarray, rgb: tuple[int, int, int], tol: int) -> np.ndarray:
    m = np.abs(img - np.array(rgb)).sum(2) <= tol
    m[int(img.shape[0] * 0.75) :] = False  # legend below the plot
    return m


def digitize(img: np.ndarray) -> pd.DataFrame:
    """Per-season (mu_shifted, sigma) read off one Figure 3 image."""
    mcl = _mask(img, MCL_RGB, 20)
    rows = np.where(mcl)[0]
    y3000 = float(np.median(rows[rows < rows.mean()]))
    y2000 = float(np.median(rows[rows > rows.mean()]))
    mw_px = 1000.0 / (y2000 - y3000)
    y0 = y2000 + 2000.0 / mw_px

    def to_mw(y):
        return (y0 - y) * mw_px

    # quarter spacing from the sigma markers (blobs >= 8 px tall)
    sig = _mask(img, SIGMA_RGB, 20)
    xs = np.where(sig.sum(0) >= 8)[0]
    blobs = [g for g in np.split(xs, np.where(np.diff(xs) > 2)[0] + 1) if len(g) >= 4]
    step = float(np.median(np.diff([(g.min() + g.max()) / 2 for g in blobs])))
    # anchor: first column on the 3,000 MW level = 2022-01-01
    cols3000 = np.where(
        np.abs(np.where(mcl, np.arange(img.shape[0])[:, None], -99) - y3000).min(0) <= 2
    )[0]
    x_jan22 = float(cols3000.min())
    x_dec21 = x_jan22 - step / 3.0
    x_right = int(np.where(sig.any(0))[0].max())
    k0 = -int(np.floor(x_dec21 / step))
    recs = []
    for k in range(k0, 64):
        xa = x_dec21 + k * step
        if xa >= x_right:
            break
        xb = min(xa + step, x_right)
        if xa < 0:
            continue
        cols = np.arange(int(xa + 0.3 * (xb - xa)), int(xa + 0.7 * (xb - xa)) + 1)
        # A season cut by the plot edge is read through its marker, which is
        # centred on the line (so a marker-height run is admitted there).
        truncated = xb - xa < step * 0.5
        max_run = 14 if truncated else 6
        if truncated:
            cols = np.arange(int(np.ceil(xa)) + 1, x_right + 1)
        val = {}
        for name, rgb, tol, lo, hi in (
            ("sigma_mw", SIGMA_RGB, 20, 1000.0, 1600.0),
            ("mu_shifted_mw", MU_RGB, 12, 0.0, 1100.0),
        ):
            m = _mask(img, rgb, tol)
            ys = []
            for x in cols:
                rr = np.where(m[:, x])[0]
                runs = np.split(rr, np.where(np.diff(rr) > 1)[0] + 1) if len(rr) else []
                cand = [
                    r.mean()
                    for r in runs
                    if len(r) <= max_run and lo < to_mw(r.mean()) < hi
                ]
                if len(cand) == 1:
                    ys.append(cand[0])
            val[name] = round(float(to_mw(np.median(ys))), 1) if ys else np.nan
        months = 3 * k
        date = (pd.Timestamp("2021-12-01") + pd.DateOffset(months=months)).normalize()
        recs.append({"effective_date": date, **val, "mw_per_px": round(mw_px, 2)})
    return pd.DataFrame(recs)


def main() -> None:
    """Digitize both figures and write the seasonal table."""
    parts = []
    for report, (png, (d0, d1)) in FIGURES.items():
        df = digitize(read_png(SRC / png))
        df = df[(df.effective_date >= d0) & (df.effective_date <= d1)].copy()
        df["source"] = f"ERCOT {report} Biennial ORDC Report, Figure 3"
        parts.append(df)
    out = pd.concat(parts).sort_values("effective_date")
    if out[["mu_shifted_mw", "sigma_mw"]].isna().any().any():
        raise ValueError(f"unread seasons:\n{out[out.isna().any(axis=1)].to_string()}")
    out["effective_date"] = out.effective_date.dt.strftime("%Y-%m-%d")
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
