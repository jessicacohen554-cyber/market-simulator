"""Digitize the MISO PY2025-26 RBDC chart images from the PRA Results Posting.

The RBDC's full continuous shape is published only as chart images (one per
subregion x season, pp.4/15/16/17 of the PY2025-26 PRA Results Posting) — the
demand-curve README records that no numeric table of the curves was reachable.
This tool extracts each chart's orange RBDC polyline at pixel resolution and
emits the ``curve_point`` rows appended to
``data/raw/capacity-market/demand-curve/miso/miso.csv`` (capx D31,
2026-09-02).

Method
------
* The postings embed each two-panel chart as ONE raster image; panels are
  split at the image midline.
* x-calibration: the tick-mark stubs below the axis line (evenly spaced,
  count asserted against the chart's labeled tick values).
* y-calibration: the axis label text-row centroids left of the axis (count
  asserted against the labeled $ ladder).
* The curve trace is the per-column median row of the orange mask inside the
  plot area, converted through the two linear calibrations.
* Validation: interpolating the traced curve at the posting's own labeled
  clearing point (e.g. N/C summer "101.8, $666.50") must reproduce the
  labeled price — observed errors at intake: $0.2-$3.2 on seven panels, $81
  on South-summer where the curve drops ~$1,280 over ~0.7 GW (a ~2-pixel
  x-tolerance at that slope).
* The traced polylines are compressed to <=16 points by greedy max-relative-
  error selection (<=1.2%) before landing in the CSV. Only the OBSERVED
  segment is committed — clipped chart tops (fall/winter/spring rise past
  their y-axes) are NOT extrapolated here; the cap bridging happens in
  ``derive_miso_rbdc_system_curves.py`` with the published seasonal CONE
  caps.

Reproduction
------------
The source PDF payload is not committed (corpus posture). Re-fetch and
verify against ``data/raw/miso-pra/SHA256SUMS.txt``::

    curl -o posting.pdf "https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%2020250529_Corrections694160.pdf"
    sha256sum posting.pdf   # 4c8db42dabc340bc6747a178d446a4fc6ca37eb21897b36700e6c64905e9ad9b
    python scripts/data/digitize_miso_rbdc_charts.py --pdf posting.pdf --out rows.csv

Requires ``pymupdf`` and ``pillow`` (NOT project dependencies — this is an
out-of-band provenance tool, not part of any solve or curation path).
"""

from __future__ import annotations

import argparse

import numpy as np

# (page_index_0based, panel_side) -> chart spec. Tick values transcribed from
# the charts' own labeled axes; ``labeled`` is the posting's callout clearing
# point used as the per-panel validation anchor.
PANELS = {
    (3, "L"): dict(
        season="summer",
        sub="North/Central",
        x0=95.0,
        xstep=2.0,
        nx=8,
        ymax=1400,
        ystep=200,
        labeled=(101.8, 666.50),
        page="p.4",
    ),
    (3, "R"): dict(
        season="summer",
        sub="South",
        x0=35.0,
        xstep=0.5,
        nx=5,
        ymax=1400,
        ystep=200,
        labeled=(35.7, 666.50),
        page="p.4",
    ),
    (14, "L"): dict(
        season="fall",
        sub="North/Central",
        x0=95.0,
        xstep=1.0,
        nx=6,
        ymax=200,
        ystep=50,
        labeled=(97.7, 91.60),
        page="p.15",
    ),
    (14, "R"): dict(
        season="fall",
        sub="South",
        x0=32.0,
        xstep=1.0,
        nx=7,
        ymax=200,
        ystep=50,
        labeled=(34.8, 74.09),
        page="p.15",
    ),
    (15, "L"): dict(
        season="winter",
        sub="North/Central",
        x0=88.0,
        xstep=1.0,
        nx=9,
        ymax=100,
        ystep=25,
        labeled=(92.8, 33.20),
        page="p.16",
    ),
    (15, "R"): dict(
        season="winter",
        sub="South",
        x0=36.0,
        xstep=0.5,
        nx=9,
        ymax=125,
        ystep=25,
        labeled=(38.2, 33.20),
        page="p.16",
    ),
    (16, "L"): dict(
        season="spring",
        sub="North/Central",
        x0=92.0,
        xstep=1.0,
        nx=8,
        ymax=125,
        ystep=25,
        labeled=(95.5, 69.88),
        page="p.17",
    ),
    (16, "R"): dict(
        season="spring",
        sub="South",
        x0=32.0,
        xstep=1.0,
        nx=7,
        ymax=125,
        ystep=25,
        labeled=(35.2, 69.88),
        page="p.17",
    ),
}

SRC = (
    "https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%20"
    "20250529_Corrections694160.pdf"
)


def _clusters(idx, gap=3, minlen=1):
    """Group consecutive indices (within ``gap``) into clusters."""
    out: list[list[int]] = []
    for i in idx:
        if out and i - out[-1][-1] <= gap:
            out[-1].append(i)
        else:
            out.append([i])
    return [g for g in out if len(g) >= minlen]


def _chart_image(pdf_path: str, page_index: int) -> np.ndarray:
    """Extract the page's two-panel chart raster (the widest embedded image)."""
    import io

    import pymupdf
    from PIL import Image

    doc = pymupdf.open(pdf_path)
    page = doc[page_index]
    best = None
    for img in page.get_images(full=True):
        info = doc.extract_image(img[0])
        if best is None or info["width"] > best["width"]:
            best = info
    doc.close()
    if best is None:
        raise RuntimeError(f"page {page_index + 1}: no embedded chart image")
    return np.asarray(Image.open(io.BytesIO(best["image"])).convert("RGB")).astype(int)


def digitize_panel(im: np.ndarray, side: str, spec: dict) -> dict:
    """Trace one panel's RBDC polyline; return calibrated points + validation."""
    h, w, _ = im.shape
    gray = im.mean(axis=2)
    half = slice(0, w // 2) if side == "L" else slice(w // 2, w)
    off = half.start

    # plot frame: long light-gray lines inside the half
    isgrid = (
        (np.abs(im[..., 0] - im[..., 1]) < 14)
        & (np.abs(im[..., 1] - im[..., 2]) < 14)
        & (gray > 150)
        & (gray < 235)
    )
    colc = isgrid[:, half].sum(axis=0)
    vfr = [
        int(np.mean(g)) + off
        for g in _clusters(list(np.nonzero(colc > 0.55 * colc.max())[0]))
    ]
    vfr = [v for v in vfr if 5 < v - off <= (w // 2 - 1)]
    axis_x, right_x = vfr[-2], vfr[-1]
    rowc = isgrid[:, axis_x + 3 : right_x - 3].sum(axis=1)
    rowc[:5] = 0
    rowc[h - 10 :] = 0
    span = right_x - axis_x
    hfr = [int(np.mean(g)) for g in _clusters(list(np.nonzero(rowc > 0.5 * span)[0]))]
    axis_y = hfr[-1]

    # x ticks: stubs just below the axis line
    dark = gray < 235
    band = dark[axis_y + 1 : axis_y + 9, off : off + w // 2]
    cc = band.sum(axis=0)
    xstubs = [int(np.mean(g)) + off for g in _clusters(list(np.nonzero(cc >= 6)[0]))]
    xstubs = [s for s in xstubs if axis_x - 3 <= s <= right_x - 5]
    if len(xstubs) != spec["nx"]:
        raise RuntimeError(
            f"{spec['season']}/{spec['sub']}: expected {spec['nx']} x stubs, "
            f"got {len(xstubs)}"
        )
    xvals = [spec["x0"] + i * spec["xstep"] for i in range(spec["nx"])]
    bx = np.polyfit(xstubs, xvals, 1)

    # y labels: dark text rows in the strip left of the axis
    strip = gray[0 : axis_y + 8, axis_x - 48 : axis_x - 4] < 160
    rc = strip.sum(axis=1)
    ylab = [
        float(np.mean(g)) for g in _clusters(list(np.nonzero(rc >= 2)[0]), minlen=5)
    ]
    ny = spec["ymax"] // spec["ystep"] + 1
    if len(ylab) != ny:
        raise RuntimeError(
            f"{spec['season']}/{spec['sub']}: expected {ny} y labels, got {len(ylab)}"
        )
    yvals = [spec["ymax"] - i * spec["ystep"] for i in range(ny)]
    by = np.polyfit(ylab, yvals, 1)
    top_row = min(ylab)  # plot top = the axis max label's row

    # orange curve trace (per-column median row inside the plot area)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    o = (r > 190) & (g > 80) & (g < 175) & (b < 110)
    o[: int(top_row) - 1, :] = False
    o[axis_y + 1 :, :] = False
    o[:, : axis_x + 1] = False
    o[:, right_x:] = False
    gw, usd = [], []
    for cx in range(axis_x + 1, right_x):
        rows = np.nonzero(o[:, cx])[0]
        if len(rows) == 0:
            continue
        gw.append(float(np.polyval(bx, cx)))
        usd.append(float(np.polyval(by, float(np.median(rows)))))
    gw = np.array(gw)
    usd = np.clip(np.array(usd), 0.0, None)
    order = np.argsort(gw)
    gw, usd = gw[order], usd[order]
    usd = np.maximum.accumulate(usd[::-1])[::-1]  # monotone non-increasing

    lab_gw, lab_usd = spec["labeled"]
    err = float(np.interp(lab_gw, gw, usd)) - lab_usd
    return dict(gw=gw, usd=usd, labeled_err_usd=err, spec=spec)


def compress(
    gw: np.ndarray, usd: np.ndarray, max_pts: int = 16, rel_tol: float = 0.012
):
    """Greedy point selection minimizing the polyline's max relative error."""
    n = len(gw)
    keep = {0, n - 1}
    floor_ = max(usd.max() * 0.002, 0.5)
    while len(keep) < max_pts:
        ks = sorted(keep)
        approx = np.interp(gw, gw[ks], usd[ks])
        e = np.abs(approx - usd) / np.maximum(usd, floor_)
        i = int(np.argmax(e))
        if e[i] < rel_tol:
            break
        keep.add(i)
    ks = sorted(keep)
    return gw[ks], usd[ks]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True, help="PY2025-26 PRA Results Posting PDF")
    ap.add_argument("--out", default=None, help="write curve_point CSV rows here")
    args = ap.parse_args(argv)

    rows = []
    for (pno, side), spec in PANELS.items():
        im = _chart_image(args.pdf, pno)
        d = digitize_panel(im, side, spec)
        cg, cu = compress(d["gw"], d["usd"])
        print(
            f"{spec['season']:7s} {spec['sub']:14s}: {len(cg)} pts, "
            f"labeled-point err {d['labeled_err_usd']:+.2f} $/MW-day"
        )
        for i, (g_, u_) in enumerate(zip(cg, cu)):
            rows.append(
                f"MISO,2025-2026,{spec['sub']},{spec['season']},curve_point,{i + 1},"
                f"{g_ * 1000.0:.1f},mw,{u_:.2f},usd_per_mw_day,"
                f'"RBDC digitized polyline (observed segment), PY2025-26 PRA Results '
                f"Posting; chart-image extraction via "
                f'scripts/data/digitize_miso_rbdc_charts.py",'
                f"{SRC},\"{spec['page']} chart '{spec['sub']} "
                f"{spec['season'].title()}' RBDC curve\""
            )
    if args.out:
        with open(args.out, "w") as f:
            f.write("\n".join(rows) + "\n")
        print(f"wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
