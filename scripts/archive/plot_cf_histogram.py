#!/usr/bin/env python3
"""Per-plant capacity-factor histogram (model vs CAMPD), binned into fixed
intervals — a standalone, dependency-free companion to the calibration
report's ``[7b]`` table.

Why this exists
---------------
A per-CF-value "hours at each CF" line is dominated by spikes: the LP parks an
already-committed unit at the discrete edges of its offer-curve tranches
(committed floor, each econ slice, the duct-fired peak), so the model's CF
density is a comb of spikes that never lines up with the smooth, physically
continuous CAMPD density. Binning the same hours into fixed CF intervals
(default **5%**) collapses that comb into a shape you can actually compare to
reality, and makes the structural gaps obvious — most importantly the missing
mass above 90% CF for efficient combined-cycle plants whose duct-firing peak
band the model gates behind scarcity prices.

The hours-per-band counts come straight from
:func:`market_sim.results.calibration.check_cf_band_occupancy`, the same
routine that feeds ``plant_cf_bands.parquet`` and the ``[7b]`` panel, so this
view never disagrees with the calibration metrics — it only renders them
finer and visually. Output is a single self-contained HTML file (inline SVG,
no JS libraries, no matplotlib), matching the repo's client-side chart idiom.

Usage
-----
    uv run python scripts/archive/plot_cf_histogram.py \
        results/calibration/run118_reldeploy_spatial \
        --plants 60122,59812,55226,55153,56350 \
        --years 2023,2024,2025 --band-width 0.05 \
        --out /tmp/cc_cf_histogram.html

``--plants`` accepts EIA plant codes (comma-separated); omit it to chart every
plant the bundle resolved. Capacity normalization matches the ``[7b]`` panel
(the larger of the model and CAMPD per-plant peaks) so the bands line up with
the calibration tables.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402

from market_sim.results.calibration import (  # noqa: E402
    check_cf_band_occupancy,
)


# CEMS reports a split plant (coal + gas-steam under one stack) as a single
# parent id; the model carries synthetic ``parent*10+digit`` child codes. Fold
# children back onto the parent before comparing, mirroring
# run_calibration_full._plant_hourly_fit.
def _model_series_by_plant(
    dispatch: pd.DataFrame, cems_ids: set[int]
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: hourly MW}`` for the model, child codes folded."""
    d = dispatch[dispatch["plant_code"] > 0].copy()

    def _to_cems(code: int) -> int:
        code = int(code)
        return code // 10 if (code not in cems_ids and code // 10 in cems_ids) else code

    d["plant_code"] = d["plant_code"].map(_to_cems)
    piv = (
        d.groupby(["plant_code", "hour"], observed=True)["mw"]
        .sum()
        .unstack("plant_code", fill_value=0.0)
        .sort_index()
    )
    return {int(c): piv[c].to_numpy(dtype=float) for c in piv.columns}


def _svg_histogram(bands: list[dict], title: str, sub: str, band_width: float) -> str:
    """Render one plant-year model-vs-CAMPD CF histogram as inline SVG.

    Side-by-side bars per CF band: CAMPD (blue) and model (orange). The y-axis
    is hours; the x-axis is the capacity-factor band. Pure SVG so the page has
    no external dependencies.
    """
    W, H, L, R, TT, B = 720, 300, 56, 14, 54, 46
    pw, ph = W - L - R, H - TT - B
    n = len(bands)
    ymax = max([max(b["model_hours"], b["actual_hours"]) for b in bands] + [1])
    ymax = ymax * 1.12
    slot = pw / n
    bw = slot * 0.40

    def y(v: float) -> float:
        return TT + ph - (v / ymax) * ph

    parts = [
        f'<svg viewBox="0 0 {W} {H}" class="hist">',
        f'<text x="{L}" y="20" class="t">{title}</text>',
        f'<text x="{L}" y="38" class="s">{sub}</text>',
    ]
    # y gridlines + labels
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        yy = TT + ph - frac * ph
        parts.append(
            f'<line x1="{L}" y1="{yy:.1f}" x2="{W - R}" y2="{yy:.1f}" class="grid"/>'
        )
        parts.append(
            f'<text x="{L - 6}" y="{yy + 4:.1f}" class="yl">{int(frac * ymax)}</text>'
        )
    for i, b in enumerate(bands):
        x0 = L + i * slot + slot / 2
        ch, mh = b["actual_hours"], b["model_hours"]
        parts.append(
            f'<rect x="{x0 - bw:.1f}" y="{y(ch):.1f}" '
            f'width="{bw:.1f}" height="{TT + ph - y(ch):.1f}" '
            f'class="campd"><title>CAMPD {ch} h</title></rect>'
        )
        parts.append(
            f'<rect x="{x0:.1f}" y="{y(mh):.1f}" '
            f'width="{bw:.1f}" height="{TT + ph - y(mh):.1f}" '
            f'class="model"><title>model {mh} h</title></rect>'
        )
        if i % max(1, round(0.10 / band_width)) == 0:
            parts.append(
                f'<text x="{x0:.1f}" y="{TT + ph + 16:.0f}" '
                f'class="xl">{b["lo"] * 100:.0f}</text>'
            )
    parts.append(
        f'<text x="{L + pw / 2:.0f}" y="{H - 8}" class="ax">capacity factor (%)</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


_PAGE = """<!doctype html><meta charset=utf-8>
<title>CC capacity-factor histograms — {bw:.0%} bands</title>
<style>
 body{{font:14px system-ui,Segoe UI,Arial;margin:24px;color:#1b2733;background:#f6f8fa}}
 h1{{font-size:19px}} .meta{{color:#5a6b7b;margin:-6px 0 18px}}
 .card{{background:#fff;border:1px solid #dce3ea;border-radius:8px;padding:10px 14px;margin:14px 0}}
 svg.hist{{width:100%;height:auto;display:block}}
 .t{{font-size:14px;font-weight:600;fill:#1b2733}} .s{{font-size:12px;fill:#5a6b7b}}
 .grid{{stroke:#eef2f5;stroke-width:1}} .yl{{font-size:10px;fill:#8295a4;text-anchor:end}}
 .xl{{font-size:10px;fill:#8295a4;text-anchor:middle}} .ax{{font-size:11px;fill:#5a6b7b;text-anchor:middle}}
 .campd{{fill:#2f9bd6}} .model{{fill:#ef7d2b}}
 .legend span{{display:inline-block;margin-right:16px}}
 .sw{{display:inline-block;width:12px;height:12px;border-radius:2px;vertical-align:-1px;margin-right:5px}}
</style>
<h1>Per-plant capacity-factor histogram — {bw:.0%} bands</h1>
<div class=meta>{bundle} &middot; model (orange) vs CAMPD net (blue) &middot;
 hours each plant spent in each capacity-factor band, normalized to the larger
 of the two per-plant peaks (matching the calibration <code>[7b]</code> panel)</div>
<div class=legend><span><i class="sw campd"></i>CAMPD net</span>
 <span><i class="sw model"></i>model</span></div>
{cards}
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path, help="calibration bundle directory")
    ap.add_argument(
        "--plants", default="", help="comma-separated EIA plant codes (default: all)"
    )
    ap.add_argument(
        "--years", default="", help="comma-separated years (default: all in the bundle)"
    )
    ap.add_argument(
        "--band-width",
        type=float,
        default=0.05,
        help="CF band width as a fraction (default 0.05 = 5%%)",
    )
    ap.add_argument("--out", type=Path, default=Path("/tmp/cf_histogram.html"))
    args = ap.parse_args()

    bundle: Path = args.bundle
    campd = pd.read_parquet(bundle_input_path(bundle, "campd"))
    cems_ids = set(int(p) for p in campd["plant_id"].unique())
    want_plants = (
        {int(p) for p in args.plants.split(",") if p.strip()} if args.plants else None
    )
    want_years = (
        [int(y) for y in args.years.split(",") if y.strip()]
        if args.years
        else sorted(int(y) for y in campd["year"].unique())
    )
    names = _plant_names(bundle)

    cards: list[str] = []
    for year in want_years:
        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
        model = _model_series_by_plant(disp, cems_ids)
        cy = campd[campd["year"] == year]
        obs = {
            int(pid): g.sort_values("hour")["net_mw"].to_numpy(dtype=float)
            for pid, g in cy.groupby("plant_id", observed=True)
        }
        codes = (
            sorted(want_plants & model.keys()) if want_plants else sorted(model.keys())
        )
        for code in codes:
            m, o = model.get(code), obs.get(code)
            if m is None or o is None:
                continue
            T = min(m.shape[0], o.shape[0])
            try:
                occ = check_cf_band_occupancy(m[:T], o[:T], band_width=args.band_width)
            except ValueError:
                continue
            m_gwh, c_gwh = m.sum() / 1e3, o.sum() / 1e3
            hi = sum(b["model_hours"] for b in occ["bands"] if b["lo"] >= 0.90 - 1e-9)
            chi = sum(b["actual_hours"] for b in occ["bands"] if b["lo"] >= 0.90 - 1e-9)
            title = f"{names.get(code, code)} ({code}) — {year}"
            sub = (
                f"model {m_gwh:,.0f} GWh / CAMPD {c_gwh:,.0f} GWh"
                f" &nbsp;|&nbsp; hours ≥90% CF: model {hi:,} / "
                f"CAMPD {chi:,} &nbsp;|&nbsp; cap {occ['capacity_mw']:,.0f} MW"
            )
            cards.append(
                "<div class=card>"
                + _svg_histogram(occ["bands"], title, sub, args.band_width)
                + "</div>"
            )

    html = _PAGE.format(bw=args.band_width, bundle=bundle.name, cards="\n".join(cards))
    args.out.write_text(html)
    print(f"wrote {args.out}  ({len(cards)} plant-year charts)")


def _plant_names(bundle: Path) -> dict[int, str]:
    """Best-effort plant-code -> name map from the ERCOT bin sheet."""
    try:
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins

        bins = load_campd_bins(ScenarioConfig().campd_bins_path)
        return dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"].astype(str)))
    except Exception:
        return {}


if __name__ == "__main__":
    main()
