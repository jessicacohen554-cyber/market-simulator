"""Digitize the PJM IMM SOM §3 "Spot average fuel price comparison" figure (PJM-NEXT-13).

Monitoring Analytics prints the monthly Platts spot fuel prices it uses to decompose
PJM LMP (East / West / Production natural gas; Northern Appalachian / Central
Appalachian / PRB coal) only as a line chart. The chart is embedded as VECTOR paths,
so each monthly point is read exactly from the PDF drawing commands — no raster
estimate. The $-axis is calibrated from the printed tick labels (slope) and the
drawn x-axis line ($0); series are identified from their legend swatches.

Verified against the report's own prose (printed year-over-year % changes; see
``data/raw/som-competitive-conduct/README.md`` §PJM spot fuel) and against a second
vintage's figure (2024 SOM vs 2025 SOM, same months, |Δ| ≤ $0.003/MMBtu).

Emits ``som_competitive_conduct.csv`` rows (``iso=PJM``, ``period=month_MM``,
``metric=spot_price_digitized_usd_per_mmbtu``) on stdout; the raw CSV is appended
once by hand (``data/raw`` is never rewritten by a script).

Run: ``python3 scripts/data/digitize_pjm_som_spot_fuel.py <2025-som-pjm-sec3.pdf>``
(requires ``pymupdf``; the PDF is not committed — re-fetch from the README URL).
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter

import numpy as np

#: Legend word -> fleet_segment code.
LEGEND = {
    "East": "east_gas",
    "West": "west_gas",
    "Production": "production_gas",
    "Northern": "napp_coal",
    "Central": "capp_coal",
    "PRB": "prb_coal",
}
#: First month the IMM chart plots (every vintage 2020-2025 starts Jan-2012).
FIRST_YEAR = 2012


def _paths(page) -> list[tuple]:
    """(colour, width, [(x, y), ...], rect) for every stroked polyline on the page."""
    out = []
    for d in page.get_drawings():
        col = d.get("color")
        if not col:
            continue
        pts: list[tuple[float, float]] = []
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
            if not pts or abs(pts[-1][0] - a[0]) + abs(pts[-1][1] - a[1]) > 1e-6:
                pts.append(a)
            pts.append(b)
        if len(pts) >= 2:
            out.append(
                (
                    tuple(round(v, 3) for v in col),
                    round(d.get("width") or 0, 3),
                    pts,
                    d["rect"],
                )
            )
    return out


def digitize(pdf: str) -> tuple[dict[str, list[float]], int]:
    """Return ``{segment: [monthly $/MMBtu ...]}`` and the page number."""
    import pymupdf

    doc = pymupdf.open(pdf)
    for pno, page in enumerate(doc):
        if "Average Monthly Spot Price" not in page.get_text():
            continue
        words = page.get_text("words")
        paths = _paths(page)
        long = [p for p in paths if len(p[2]) >= 100]
        widths = Counter(p[1] for p in long)
        long = [p for p in long if widths[p[1]] >= len(LEGEND)]
        x0 = min(min(q[0] for q in p[2]) for p in long)
        x1 = max(max(q[0] for q in p[2]) for p in long)
        y1 = max(p[3].y1 for p in long)
        ticks = sorted(
            (float(w[4][1:]), (w[1] + w[3]) / 2)
            for w in words
            if re.fullmatch(r"\$\d+", w[4]) and x0 - 40 < w[2] < x0 + 2
        )
        slope, icpt = np.polyfit([t[0] for t in ticks], [t[1] for t in ticks], 1)
        zero = icpt
        for p in paths:
            for (ax, ay), (bx, by) in zip(p[2][:-1], p[2][1:]):
                if (
                    abs(ay - by) < 1e-3
                    and min(ax, bx) <= x0 + 1
                    and max(ax, bx) >= x1 - 1
                    and abs(ay - icpt) < 3
                    and p[1] < 1.0
                ):
                    zero = ay
        series: dict[str, list[float]] = {}
        for col, _w, pts, _r in long:
            legs = [
                q for q in paths if q[0] == col and len(q[2]) == 2 and q[3].y0 > y1 - 1
            ]
            lx, ly = legs[0][2][1]
            near = [
                w for w in words if w[0] >= lx - 1 and abs((w[1] + w[3]) / 2 - ly) < 4
            ]
            name = LEGEND[min(near, key=lambda w: w[0])[4]]
            series[name] = [(zero - py) / (-slope) for _x, py in pts]
        return series, pno + 1
    raise SystemExit(f"figure not found in {pdf}")


def main() -> None:
    """Print CSV rows for 2019-2025 (monthly + annual mean)."""
    pdf = sys.argv[1]
    series, page = digitize(pdf)
    doc = pdf.rsplit("/", 1)[-1]
    w = csv.writer(sys.stdout, lineterminator="\n")
    for seg, vals in series.items():
        for y in range(2019, 2026):
            i = (y - FIRST_YEAR) * 12
            months = vals[i : i + 12]
            if len(months) < 12:
                continue
            for m, v in enumerate(months, 1):
                w.writerow(
                    [
                        "PJM",
                        y,
                        f"month_{m:02d}",
                        seg,
                        "spot_price_digitized_usd_per_mmbtu",
                        f"{v:.3f}",
                        "usd_per_mmbtu",
                        doc,
                        page,
                        "DIGITIZED from vector paths; Platts monthly spot avg (IMM)",
                    ]
                )
            w.writerow(
                [
                    "PJM",
                    y,
                    "annual",
                    seg,
                    "spot_price_digitized_usd_per_mmbtu",
                    f"{np.mean(months):.3f}",
                    "usd_per_mmbtu",
                    doc,
                    page,
                    "DIGITIZED; mean of the 12 monthly points",
                ]
            )


if __name__ == "__main__":
    main()
