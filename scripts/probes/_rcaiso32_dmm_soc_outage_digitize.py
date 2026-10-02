"""R-CAISO-32 probe: digitize the DMM Battery Special Report SOC-outage figures.

Reads the two DMM PDFs (2023 report Fig 2.23, 2024 report Fig 2.26: "Quarterly
average real-time state-of-charge outages") and recovers the plotted values
from the PDF vector objects, not from pixels: the bars are filled rectangles
and the line is a 4-point polyline, so each value is exact to the axis mapping.
The axis is anchored on the bar baseline (y of the bar bottoms) and scaled by
the tick-label centres (0 and the top tick).

Output: one JSON with, per quarter, the Max-SOC outage (MWh), the Min-SOC
outage (MWh), the share of aggregate charging range on outage (%) and the
implied aggregate charging range (MWh = (max + min) / share).

Zero LP. Report-only (handoff R-CAISO-32, link 14). The PDFs are not
committed; pass their paths. Usage::

    python3 scripts/probes/_rcaiso32_dmm_soc_outage_digitize.py \
        --pdf 2023=path/to/2023-special-report-on-battery-storage-jul-16-2024.pdf \
        --pdf 2024=path/to/2024-special-report-on-battery-storage-may-29-2025.pdf \
        --out results/calibration/_rcaiso32/dmm_soc_outage.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pdfplumber

#: (report year) -> (page, figure id, top MWh tick, top percent tick)
FIGURES = {
    2023: {"page": 30, "figure": "Figure 2.23", "mwh_top": 2000, "pct_top": 10},
    2024: {"page": 31, "figure": "Figure 2.26", "mwh_top": 2200, "pct_top": 10},
}
BLUE = (0.31, 0.459, 0.545)  # Max SOC outage bars
YELLOW = (1.0, 0.639, 0.0)  # Min SOC outage bars
LINE = (0.447, 0.451, 0.216)  # percent-of-range line
QUARTERS = ("Q1", "Q2", "Q3", "Q4")


def _close(a, b, tol=0.01):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def digitize(pdf_path: Path, year: int) -> dict:
    """Return the digitized figure for one report year."""
    spec = FIGURES[year]
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[spec["page"] - 1]
        words = page.extract_words()
        rects = [r for r in page.rects if r.get("fill")]
        curves = page.curves

    def label_centre(text, x_min):
        hits = [w for w in words if w["text"] == text and w["x0"] > x_min]
        if not hits:
            raise ValueError(f"{year}: tick label {text!r} not found")
        w = min(hits, key=lambda w: w["x0"])
        return (w["top"] + w["bottom"]) / 2

    # Data bars: full-height rectangles of the two series, left of the legend
    # swatches (which are 5.5 pt tall squares).
    bars = [r for r in rects if r["height"] > 0.6 and 20 < r["width"] < 30]
    blue = sorted(
        [r for r in bars if _close(r["non_stroking_color"], BLUE)],
        key=lambda r: r["x0"],
    )
    yellow = sorted(
        [r for r in bars if _close(r["non_stroking_color"], YELLOW)],
        key=lambda r: r["x0"],
    )
    if len(blue) != 4 or len(yellow) != 4:
        raise ValueError(f"{year}: expected 4+4 bars, got {len(blue)}+{len(yellow)}")
    baseline = max(r["bottom"] for r in blue + yellow)

    # Left axis (MWh): the "0" label sits left of x=130; the top tick is the
    # comma-formatted top value. Right axis (%) labels sit right of x=450.
    y0_left = label_centre("0", 100)
    ytop_left = label_centre(f"{spec['mwh_top']:,}", 90)
    y0_right = label_centre("0%", 450)
    ytop_right = label_centre(f"{spec['pct_top']}%", 450)
    mwh_per_pt = spec["mwh_top"] / (y0_left - ytop_left)
    pct_per_pt = spec["pct_top"] / (y0_right - ytop_right)
    # The label centres sit ~1 pt below the baseline tick; anchor on the bars.
    offset_left = y0_left - baseline
    offset_right = y0_right - baseline

    line = [
        c for c in curves if _close(c["stroking_color"], LINE) and len(c["pts"]) == 4
    ]
    if len(line) != 1:
        raise ValueError(f"{year}: expected one 4-point line, got {len(line)}")
    pts = sorted(line[0]["pts"], key=lambda p: p[0])

    out = {}
    for q, b, yl, (_, py) in zip(QUARTERS, blue, yellow, pts):
        max_mwh = b["height"] * mwh_per_pt
        min_mwh = yl["height"] * mwh_per_pt
        pct = (baseline - py) * pct_per_pt
        out[q] = {
            "max_soc_outage_mwh": round(max_mwh),
            "min_soc_outage_mwh": round(min_mwh),
            "share_of_charge_range_pct": round(pct, 2),
            "implied_charge_range_mwh": round((max_mwh + min_mwh) / (pct / 100)),
        }
    mean = sum(v["share_of_charge_range_pct"] for v in out.values()) / 4
    return {
        "source": pdf_path.name,
        "figure": spec["figure"],
        "page": spec["page"],
        "axis_offset_pt": {
            "left": round(offset_left, 2),
            "right": round(offset_right, 2),
        },
        "quarters": out,
        "mean_of_quarterly_share_pct": round(mean, 2),
    }


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--pdf", action="append", required=True, help="YEAR=path, repeatable"
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = {}
    for item in args.pdf:
        year, path = item.split("=", 1)
        result[year] = digitize(Path(path), int(year))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    for year, r in result.items():
        print(f"{year} {r['figure']} mean share {r['mean_of_quarterly_share_pct']} %")
        for q, v in r["quarters"].items():
            print(
                f"  {q}: max {v['max_soc_outage_mwh']:>5} MWh  min {v['min_soc_outage_mwh']:>4} MWh  "
                f"share {v['share_of_charge_range_pct']:5.2f} %  range {v['implied_charge_range_mwh']:>6} MWh"
            )


if __name__ == "__main__":
    main()
