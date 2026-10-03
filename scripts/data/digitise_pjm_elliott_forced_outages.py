"""Digitise PJM's Winter Storm Elliott hourly forced-outage figure into a raw CSV.

Source: PJM, *Winter Storm Elliott Event Analysis and Recommendation Report*
(2023-07-17), Figure 30 "Dec. 23 and Dec. 24 Forced Outages" (report p. 50, PDF
p. 57): GADS forced outages and derates by fuel, hourly bars at even hours of
23-25 Dec 2022 plus 24 Dec 07:00 (the labelled 46,124 MW peak), wind and solar
excluded (source: GADS as of 2023-03-01). The figure is a raster image with no
underlying table in the report, so the bars are read pixel by pixel from the
losslessly extracted image (``pdfimages``) committed beside the README.

Method (no free parameter): the y scale is fixed by the chart's own 30 / 40 GW
gridlines (96 px per 10 GW; zero at the bar baseline); each bar's top is the
median first non-background row over its interior columns, walked upward from
the baseline; the fuel split is each legend colour's pixel share of the bar.
The labelled 46,124 MW peak is the check (owner ruling R-64; record
``docs/records/pjm/closeout-pjm-elliott/``).

Run: ``uv run python scripts/data/digitise_pjm_elliott_forced_outages.py``
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config import paths

RAW_DIR = paths.RAW_DIR / "pjm-elliott-forced-outages"
FIGURE = RAW_DIR / "figure30_gads_forced_outages_by_fuel.png"
OUT_CSV = RAW_DIR / "figure30_digitised.csv"

# Chart geometry read off the figure itself (pixel rows of the labelled gridlines).
GRID_40_GW_ROW = 148.5
GRID_30_GW_ROW = 244.5
PX_PER_GW = (GRID_30_GW_ROW - GRID_40_GW_ROW) / 10.0
ZERO_ROW = GRID_30_GW_ROW + 30.0 * PX_PER_GW
BASELINE_SCAN_ROW = 531  # last row inside the bars (above the black baseline)
BAR_SEED_ROW = 515  # a row where every bar shows its bottom (gas) colour
EDGE_PX = 4  # interior columns only (skip the black bar outline + anti-aliasing)
LABELLED_PEAK_MW = 46_124.0  # the figure's own annotation for 24 Dec 07:00

# Legend colours (RGB) and the tolerance (L1) for a pixel to count as that fuel.
FUEL_RGB = {
    "gas": (240, 90, 93),
    "coal": (250, 148, 45),
    "oil": (70, 115, 165),
    "nuclear": (125, 195, 190),
    "hydro": (95, 170, 85),
    "other": (250, 215, 80),
}
COLOUR_TOL = 120

# Bar labels left to right (EPT, hour beginning, as printed on the x axis).
BAR_TIMES = (
    [f"2022-12-23 {h:02d}:00" for h in range(0, 24, 2)]
    + [f"2022-12-24 {h:02d}:00" for h in (0, 2, 4, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22)]
    + [f"2022-12-25 {h:02d}:00" for h in range(0, 24, 2)]
)


def read_png_rgb(path: Path) -> np.ndarray:
    """Decode an 8-bit, non-interlaced RGB/RGBA PNG into an (h, w, 3) int array."""
    b = path.read_bytes()
    pos, idat, meta = 8, b"", None
    while pos < len(b):
        (n,) = struct.unpack(">I", b[pos : pos + 4])
        kind, data = b[pos + 4 : pos + 8], b[pos + 8 : pos + 8 + n]
        if kind == b"IHDR":
            meta = struct.unpack(">IIBBBBB", data)
        elif kind == b"IDAT":
            idat += data
        pos += 12 + n
    w, h, depth, ctype, _, _, interlace = meta
    if depth != 8 or ctype not in (2, 6) or interlace:
        raise ValueError(f"unsupported PNG layout {meta}")
    bpp = 3 if ctype == 2 else 4
    raw = np.frombuffer(zlib.decompress(idat), np.uint8)
    stride = w * bpp
    out = np.zeros((h, stride), np.int32)
    prev = np.zeros(stride, np.int32)
    for y in range(h):
        f, row = (
            raw[y * (stride + 1)],
            raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)].astype(np.int32),
        )
        cur = row.copy()
        if f == 1:
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif f == 2:
            cur = (row + prev) & 255
        elif f == 3:
            for i in range(stride):
                left = cur[i - bpp] if i >= bpp else 0
                cur[i] = (row[i] + (left + prev[i]) // 2) & 255
        elif f == 4:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                bb = prev[i]
                p = a + bb - c
                pa, pb, pc = abs(p - a), abs(p - bb), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (bb if pb <= pc else c)
                cur[i] = (row[i] + pr) & 255
        out[y], prev = cur, cur
    return out.reshape(h, w, bpp)[:, :, :3]


def _classify(p: np.ndarray) -> str:
    """Fuel name, 'border', 'bg' or '?' for one pixel."""
    if (p < 60).all():
        return "border"
    if (p > 235).all() or (abs(p[0] - p[1]) < 10 and abs(p[1] - p[2]) < 10):
        return "bg"
    d = {k: int(np.abs(p - np.array(v)).sum()) for k, v in FUEL_RGB.items()}
    k = min(d, key=d.get)
    return k if d[k] < COLOUR_TOL else "?"


def digitise(figure: Path = FIGURE) -> pd.DataFrame:
    """Read every bar of Figure 30: total and per-fuel MW at each labelled hour."""
    im = read_png_rgb(figure)
    seed = im[BAR_SEED_ROW]
    is_gas = (seed[:, 0] > 200) & (seed[:, 1] < 110) & (seed[:, 2] < 110)
    xs = np.where(is_gas)[0]
    bars = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
    if len(bars) != len(BAR_TIMES):
        raise ValueError(f"found {len(bars)} bars, expected {len(BAR_TIMES)}")
    rows = []
    for t, bar in zip(BAR_TIMES, bars, strict=True):
        tops, cnt = [], dict.fromkeys(FUEL_RGB, 0)
        for x in range(bar[0] + EDGE_PX, bar[-1] - EDGE_PX + 1):
            y = BASELINE_SCAN_ROW
            while y > 0 and _classify(im[y, x]) != "bg":
                y -= 1
            tops.append(y + 1)
            for yy in range(y + 1, BASELINE_SCAN_ROW + 1):
                c = _classify(im[yy, x])
                if c in cnt:
                    cnt[c] += 1
        total_mw = 1000.0 * (ZERO_ROW + 0.5 - float(np.median(tops))) / PX_PER_GW
        n = sum(cnt.values())
        for fuel, k in cnt.items():
            rows.append(
                {
                    "hour_beginning_ept": t,
                    "fuel": fuel,
                    "forced_outage_mw": round(total_mw * k / n, 0),
                    "bar_total_mw": round(total_mw, 0),
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    """Digitise the committed figure and write ``figure30_digitised.csv``."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_CSV)
    args = ap.parse_args()
    df = digitise()
    peak = df[df.hour_beginning_ept == "2022-12-24 07:00"].bar_total_mw.iloc[0]
    print(f"24 Dec 07:00 bar {peak:,.0f} MW vs labelled {LABELLED_PEAK_MW:,.0f} MW")
    df.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
