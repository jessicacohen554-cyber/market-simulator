"""Self-contained HTML run report + versioned report payload (ADR 0014).

Implements the reporting deliverable's renderer shape (ADR 0014 §6): pure
functions over already-computed sweep results, no LP interaction and no
``market_sim`` import.

* :func:`build_report_payload` assembles the single-run report payload
  (ADR 0014 §3): a ``payload_version``-stamped dict holding the provenance
  block (§2.1 fields, with ``iso``/``mode``/``sensitivity``/
  ``additionality_only`` mandatory for the future N-run overlay, §3/§4), the
  full frontier rows, the long-form build-mix rows, and an ``hourly`` block
  with 3-significant-figure series for a small set of named setpoints only
  (§3 size discipline — full-precision hourly data stays in Parquet).
* :func:`render_report` renders that payload — and nothing else (§1: the HTML
  never re-reads Parquet) — into one fully offline static HTML document with
  the §2.1–§2.7 views: inline CSS/JS/data, hand-rolled inline SVG charts and
  a tiny inline canvas renderer for the 24×365 heatmap. No CDN, no external
  fetch, no external libraries.

The renderer refuses any ``payload_version`` it does not know (§3).
"""

from __future__ import annotations

import html
import json
import math
from dataclasses import asdict

import numpy as np

from lce_portfolio import __version__
from lce_portfolio.config import PortfolioConfig
from lce_portfolio.outputs import frontier_table
from lce_portfolio.sweep import SweepResult

#: Current report-payload schema version (ADR 0014 §3). Any breaking schema
#: change bumps this; the renderer refuses versions it doesn't know.
PAYLOAD_VERSION = 1

#: Payload versions this renderer knows how to render (ADR 0014 §3).
KNOWN_PAYLOAD_VERSIONS = (1,)

#: Stable HTML ``id`` anchors for the ADR 0014 §2 views, keyed by § number.
#: Tests assert on these, and deep links (``report.html#sec-2-7-hourly``) rely
#: on them staying put.
SECTION_ANCHORS = {
    "2.1": "sec-2-1-provenance",
    "2.2": "sec-2-2-frontier",
    "2.3": "sec-2-3-build-mix",
    "2.4": "sec-2-4-cost",
    "2.5": "sec-2-5-residual-co2",
    "2.6": "sec-2-6-multi-iso",
    "2.7": "sec-2-7-hourly",
}

# Categorical palette (dataviz reference palette, light mode; fixed slot
# order, never cycled — the order is the CVD-safety mechanism).
_SERIES = (
    "#2a78d6",  # 1 blue
    "#1baf7a",  # 2 aqua
    "#eda100",  # 3 yellow
    "#008300",  # 4 green
    "#4a3aa7",  # 5 violet
    "#e34948",  # 6 red
    "#e87ba4",  # 7 magenta
    "#eb6834",  # 8 orange
)
_OVERFLOW_COLOR = "#898781"  # muted gray for any series past the 8 slots
_CRITICAL = "#d03b3b"  # status color: non-optimal solve flags only
_SURFACE = "#fcfcfb"
_INK = "#0b0b0b"
_INK_2 = "#52514e"
_MUTED = "#898781"
_GRID = "#e1e0d9"
_BASELINE = "#c3c2b7"


def _series_color(i: int) -> str:
    """Fixed-order categorical slot color; gray past slot 8 (never cycled)."""
    return _SERIES[i] if i < len(_SERIES) else _OVERFLOW_COLOR


# --------------------------------------------------------------------------
# payload assembly (ADR 0014 §3)
# --------------------------------------------------------------------------


def _round_sig3(values: np.ndarray) -> list[float]:
    """Round a 1-D array to 3 significant figures (ADR 0014 §3 size discipline).

    Uses ``%.3g`` formatting per element so the JSON serialization is as short
    as the rounding implies (``123.00000000001``-style float dust never leaks
    into the payload).
    """
    return [float(f"{v:.3g}") for v in np.asarray(values, dtype=float)]


def _is_optimal(status: str) -> bool:
    """True when a solver status string means an optimal solve (ADR 0014 §2.1)."""
    return status.lower() == "optimal"


def _setpoint_key(setpoint: float) -> str:
    """Stable string key for a setpoint (JSON object keys must be strings)."""
    return f"{float(setpoint):g}"


def select_hourly_setpoint(sweep: SweepResult) -> float | None:
    """Default §2.7 setpoint: the highest-matching *optimal* one (ADR 0014 §2.7).

    Ties break toward the lowest setpoint (the cheaper cap / laxer target that
    reaches the same matching). ``None`` when no setpoint solved to optimal.
    """
    optimal = [r for r in sweep.results if _is_optimal(r.status)]
    if not optimal:
        return None
    best = max(optimal, key=lambda r: (r.matching_pct, -r.setpoint))
    return float(best.setpoint)


def _sanitize(value):
    """Make a scalar strict-JSON-safe: numpy scalars → python, NaN/inf → None."""
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _frontier_rows(sweep: SweepResult) -> list[dict]:
    """Full frontier table rows (ADR 0014 §3), strict-JSON-safe.

    Reuses :func:`lce_portfolio.outputs.frontier_table` so the payload and the
    Parquet frontier can never disagree on columns.
    """
    records = frontier_table(sweep).to_dict("records")
    return [{k: _sanitize(v) for k, v in row.items()} for row in records]


def _build_mix_rows(sweep: SweepResult) -> list[dict]:
    """Long-form build-mix rows (ADR 0014 §3), with split-tech energy MWh.

    ``build_energy_mwh`` is the selected energy capacity for split-storage
    techs (ADR 0006, required by the §2.3 view) and ``None`` for every other
    resource.
    """
    rows = []
    for r in sweep.results:
        split = dict(zip(r.split_names, np.asarray(r.build_energy_mwh, dtype=float)))
        for name, mw in zip(r.resource_names, r.build_mw):
            rows.append(
                {
                    "iso": sweep.iso,
                    "setpoint": float(r.setpoint),
                    "resource": name,
                    "build_mw": float(mw),
                    "build_energy_mwh": (float(split[name]) if name in split else None),
                }
            )
    return rows


def _hourly_series(result) -> dict:
    """§2.7 hourly arrays for one setpoint, 3-sig-fig rounded (ADR 0014 §3)."""
    return {
        "setpoint": float(result.setpoint),
        "status": result.status,
        "grid_buy_mwh": _round_sig3(result.grid_buy),
        "soc_mwh": {
            name: _round_sig3(result.storage_soc[i])
            for i, name in enumerate(result.storage_names)
        },
    }


def build_report_payload(
    sweeps: list[SweepResult],
    configs: list[PortfolioConfig],
    *,
    run_id: str | None = None,
    report_hourly: str = "selected",
) -> dict:
    """Assemble the single-run report payload (ADR 0014 §3).

    ``sweeps``/``configs`` are parallel lists, one entry per ISO in the run
    (a single-ISO run passes one of each; an ``--all-isos`` batch passes one
    per ISO and yields the §2.6 comparison data). ``report_hourly`` selects
    which setpoints get §2.7 hourly series: ``"selected"`` (default — only
    the highest-matching optimal setpoint per ISO) or ``"all"`` (every
    setpoint; ADR 0014 §3 ``--report-hourly all``).

    Provenance carries the §3-mandatory ``iso``/``mode``/``sensitivity``/
    ``additionality_only`` fields (single-valued across the run — a batch
    shares one base config, enforced here) so a future overlay pack can
    consume N payloads side-by-side without schema change (§4).
    """
    if not sweeps or len(sweeps) != len(configs):
        raise ValueError("sweeps and configs must be parallel, non-empty lists")
    if report_hourly not in ("selected", "all"):
        raise ValueError(f"report_hourly must be selected/all, got {report_hourly!r}")
    for label in ("mode", "lcoe_sensitivity", "additionality_only"):
        values = {getattr(c, label) for c in configs}
        if len(values) > 1:
            raise ValueError(
                f"one report covers one run: {label} differs across ISOs ({values})"
            )
    base = configs[0]

    per_iso = []
    for sweep, config in zip(sweeps, configs):
        per_iso.append(
            {
                "iso": sweep.iso,
                "config": asdict(config),
                "solves": [
                    {
                        "setpoint": float(r.setpoint),
                        "status": r.status,
                        "matching_pct": _sanitize(r.matching_pct),
                        "premium_per_mwh": _sanitize(r.premium),
                    }
                    for r in sweep.results
                ],
            }
        )

    selected: dict[str, float | None] = {}
    series: dict[str, dict] = {}
    for sweep in sweeps:
        sel = select_hourly_setpoint(sweep)
        selected[sweep.iso] = sel
        include = (
            list(sweep.results)
            if report_hourly == "all"
            else [r for r in sweep.results if sel is not None and r.setpoint == sel]
        )
        series[sweep.iso] = {
            _setpoint_key(r.setpoint): _hourly_series(r) for r in include
        }

    frontier: list[dict] = []
    build_mix: list[dict] = []
    for sweep in sweeps:
        frontier.extend(_frontier_rows(sweep))
        build_mix.extend(_build_mix_rows(sweep))

    return {
        "payload_version": PAYLOAD_VERSION,
        "provenance": {
            "run_id": run_id,
            "tool_version": __version__,
            "iso": sweeps[0].iso if len(sweeps) == 1 else "multi",
            "isos": [s.iso for s in sweeps],
            "mode": base.mode,
            "sensitivity": base.lcoe_sensitivity,
            "additionality_only": base.additionality_only,
            "per_iso": per_iso,
        },
        "frontier": frontier,
        "build_mix": build_mix,
        "hourly": {
            "report_hourly": report_hourly,
            "selected": selected,
            "series": series,
        },
    }


# --------------------------------------------------------------------------
# formatting helpers
# --------------------------------------------------------------------------


def _esc(text) -> str:
    """HTML-escape a value for text/attribute contexts."""
    return html.escape(str(text), quote=True)


def _fmt_num(v: float, digits: int = 0) -> str:
    """Thousands-comma'd fixed-point number for labels and table cells."""
    return f"{v:,.{digits}f}"


def _fmt_money(v: float) -> str:
    """Compact SI dollars ($176.3M, $100M) for axis ticks and cost labels."""
    a = abs(v)
    for cut, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if a >= cut:
            return f"${v / cut:,.4g}{suffix}"
    return f"${v:,.0f}"


def _nice_ticks(vmin: float, vmax: float, n: int = 5) -> list[float]:
    """~n clean-number axis ticks whose first/last tick SPAN [vmin, vmax].

    The span guarantee matters: chart scales use ``ticks[0]``/``ticks[-1]`` as
    the plot domain, so a tick set that stopped short of the data would let
    marks overflow the plot area.
    """
    if vmax <= vmin:
        vmax = vmin + 1.0
    raw = (vmax - vmin) / max(n, 1)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(s * mag for s in (1, 2, 5, 10) if s * mag >= raw)
    start = math.floor(vmin / step) * step
    end = math.ceil(vmax / step) * step
    count = int(round((end - start) / step)) + 1
    return [round(start + i * step, 10) for i in range(count)]


class _LinScale:
    """Minimal linear scale: data domain → pixel range."""

    def __init__(self, d0: float, d1: float, r0: float, r1: float) -> None:
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v: float) -> float:
        span = self.d1 - self.d0 or 1.0
        return self.r0 + (v - self.d0) / span * (self.r1 - self.r0)


def _svg_open(width: int, height: int) -> str:
    """Opening tag for a responsive inline-SVG chart."""
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'preserveAspectRatio="xMidYMid meet">'
    )


def _axis_grid(
    xs: _LinScale,
    ys: _LinScale,
    xticks: list[float],
    yticks: list[float],
    xfmt,
    yfmt,
) -> str:
    """Hairline gridlines + muted tick labels (recessive chart chrome)."""
    out = []
    for t in yticks:
        y = ys(t)
        out.append(
            f'<line x1="{xs.r0:.1f}" x2="{xs.r1:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
            f'<text x="{xs.r0 - 8:.1f}" y="{y + 4:.1f}" text-anchor="end" '
            f'class="tick">{_esc(yfmt(t))}</text>'
        )
    for t in xticks:
        x = xs(t)
        out.append(
            f'<text x="{x:.1f}" y="{ys.r0 + 20:.1f}" text-anchor="middle" '
            f'class="tick">{_esc(xfmt(t))}</text>'
        )
    out.append(
        f'<line x1="{xs.r0:.1f}" x2="{xs.r1:.1f}" y1="{ys.r0:.1f}" y2="{ys.r0:.1f}" '
        f'stroke="{_BASELINE}" stroke-width="1"/>'
    )
    return "".join(out)


def _legend(entries: list[tuple[str, str]]) -> str:
    """Legend row: (label, color) chips. Present whenever ≥ 2 series."""
    chips = "".join(
        f'<span class="key"><span class="swatch" style="background:{c}"></span>'
        f"{_esc(label)}</span>"
        for label, c in entries
    )
    return f'<div class="legend">{chips}</div>'


# --------------------------------------------------------------------------
# §2 section renderers
# --------------------------------------------------------------------------


def _sec_provenance(payload: dict) -> str:
    """§2.1 provenance header: run id, ISO(s), mode, tool version, config echo,
    per-setpoint solver status with non-optimal setpoints flagged inline."""
    prov = payload["provenance"]
    run_id = prov.get("run_id") or "(ad-hoc run)"
    meta_rows = [
        ("Run id", run_id),
        ("ISO(s)", ", ".join(prov["isos"])),
        ("Mode", prov["mode"]),
        ("Sensitivity", prov["sensitivity"]),
        ("Additionality only", str(prov["additionality_only"])),
        ("Tool version", prov["tool_version"]),
        ("Payload version", str(payload["payload_version"])),
    ]
    meta = "".join(
        f'<div class="meta-item"><div class="meta-label">{_esc(k)}</div>'
        f'<div class="meta-value">{_esc(v)}</div></div>'
        for k, v in meta_rows
    )

    solve_blocks = []
    for entry in prov["per_iso"]:
        chips = []
        for s in entry["solves"]:
            ok = _is_optimal(s["status"])
            match = (
                f"{s['matching_pct'] * 100:.1f}%"
                if s["matching_pct"] is not None
                else "—"
            )
            flag = "" if ok else f' <strong class="flag">⚠ {_esc(s["status"])}</strong>'
            cls = "solve" if ok else "solve solve-bad"
            chips.append(
                f'<span class="{cls}">set {_esc(_setpoint_key(s["setpoint"]))}: '
                f"{match} matched{flag}</span>"
            )
        config_json = _esc(json.dumps(entry["config"], indent=2, default=str))
        solve_blocks.append(
            f'<div class="iso-solves"><h3>{_esc(entry["iso"])}</h3>'
            f'<div class="solves">{"".join(chips)}</div>'
            f"<details><summary>Config echo</summary>"
            f"<pre>{config_json}</pre></details></div>"
        )

    return (
        f'<section id="{SECTION_ANCHORS["2.1"]}">'
        f"<h2>Run provenance</h2>"
        f'<div class="meta-grid">{meta}</div>'
        f"{''.join(solve_blocks)}</section>"
    )


def _frontier_title(row: dict) -> str:
    """Hover text for one frontier point: the full frontier row (§2.2)."""
    shadow = row["shadow_price"]
    return (
        f"setpoint {_setpoint_key(row['setpoint'])} [{row['status']}]\n"
        f"matching: {row['matching_pct'] * 100:.2f}%\n"
        f"premium: ${row['premium_per_mwh']:.2f}/MWh\n"
        f"premium/yr: {_fmt_money(row['premium_per_year'])}\n"
        f"over BAU: {row['pct_over_bau'] * 100:.2f}%\n"
        f"shadow price: " + (f"{shadow:.4f}" if shadow is not None else "n/a")
    )


def _sec_frontier(payload: dict) -> str:
    """§2.2 frontier chart: matching % vs premium $/MWh across setpoints.

    Axis roles follow ``mode`` (ADR 0014 §2.2): premium_cap puts the achieved
    premium on x and matching on y; matching_target swaps them. Hover (SVG
    ``<title>``) shows the full frontier row.
    """
    prov = payload["provenance"]
    mode = prov["mode"]
    isos = prov["isos"]
    rows = payload["frontier"]
    W, H, L, R, T, B = 680, 320, 64, 20, 16, 44

    def xy(row):
        if mode == "premium_cap":
            return row["premium_per_mwh"], row["matching_pct"] * 100
        return row["matching_pct"] * 100, row["premium_per_mwh"]

    pts = [xy(r) for r in rows]
    xvals = [p[0] for p in pts] or [0.0]
    yvals = [p[1] for p in pts] or [0.0]
    xticks = _nice_ticks(min(xvals + [0]), max(xvals) or 1)
    yticks = _nice_ticks(min(yvals + [0]), max(yvals) or 1)
    xs = _LinScale(xticks[0], xticks[-1], L, W - R)
    ys = _LinScale(yticks[0], yticks[-1], H - B, T)

    if mode == "premium_cap":
        xlabel, ylabel = "premium $/MWh", "matching %"
        xfmt, yfmt = lambda v: f"{v:g}", lambda v: f"{v:g}%"
    else:
        xlabel, ylabel = "matching %", "premium $/MWh"
        xfmt, yfmt = lambda v: f"{v:g}%", lambda v: f"{v:g}"

    parts = [_svg_open(W, H), _axis_grid(xs, ys, xticks, yticks, xfmt, yfmt)]
    for i, iso in enumerate(isos):
        color = _series_color(i)
        iso_rows = sorted(
            (r for r in rows if r["iso"] == iso), key=lambda r: r["setpoint"]
        )
        path = " ".join(f"{xs(xy(r)[0]):.1f},{ys(xy(r)[1]):.1f}" for r in iso_rows)
        if path:
            parts.append(
                f'<polyline points="{path}" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        for r in iso_rows:
            px, py = xs(xy(r)[0]), ys(xy(r)[1])
            fill = color if _is_optimal(r["status"]) else _CRITICAL
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{fill}" '
                f'stroke="{_SURFACE}" stroke-width="2">'
                f"<title>{_esc(iso)} — {_esc(_frontier_title(r))}</title></circle>"
                f'<text x="{px:.1f}" y="{py - 9:.1f}" text-anchor="middle" '
                f'class="pt-label">{_esc(_setpoint_key(r["setpoint"]))}</text>'
            )
    parts.append(
        f'<text x="{(L + W - R) / 2:.0f}" y="{H - 6}" text-anchor="middle" '
        f'class="axis-label">{_esc(xlabel)}</text>'
        f'<text x="14" y="{(T + H - B) / 2:.0f}" text-anchor="middle" '
        f'class="axis-label" transform="rotate(-90 14 {(T + H - B) / 2:.0f})">'
        f"{_esc(ylabel)}</text></svg>"
    )
    legend = (
        _legend([(iso, _series_color(i)) for i, iso in enumerate(isos)])
        if len(isos) > 1
        else ""
    )
    note = (
        '<p class="note">Point labels are setpoints; red points are '
        "non-optimal solves (flagged in the provenance header).</p>"
    )
    table = _frontier_table_view(rows)
    return (
        f'<section id="{SECTION_ANCHORS["2.2"]}"><h2>Frontier — matching vs premium'
        f"</h2>{legend}{''.join(parts)}{note}{table}</section>"
    )


def _frontier_table_view(rows: list[dict]) -> str:
    """Collapsible table twin of the frontier chart (accessibility fallback)."""
    body = "".join(
        f"<tr><td>{_esc(r['iso'])}</td><td>{_esc(_setpoint_key(r['setpoint']))}</td>"
        f"<td>{r['matching_pct'] * 100:.2f}%</td>"
        f"<td>{r['premium_per_mwh']:.2f}</td>"
        f"<td>{_fmt_money(r['premium_per_year'])}</td>"
        f"<td>{r['pct_over_bau'] * 100:.2f}%</td>"
        f"<td>{_esc(r['status'])}</td></tr>"
        for r in rows
    )
    return (
        "<details><summary>Table view</summary><table><thead><tr>"
        "<th>ISO</th><th>setpoint</th><th>matching</th><th>premium $/MWh</th>"
        "<th>premium $/yr</th><th>over BAU</th><th>status</th>"
        f"</tr></thead><tbody>{body}</tbody></table></details>"
    )


def _stack_column(
    x: float,
    width: float,
    segments: list[tuple[float, float, str, str]],
) -> str:
    """One stacked column: ``segments`` = (y_top, y_bottom, color, title) rects.

    The topmost paint order is preserved; each segment keeps a 2px surface gap
    from its neighbor (the dataviz surface-gap rule) and the stack's data-end
    is rounded via the section renderers passing an adjusted first segment.
    """
    out = []
    for y0, y1, color, title in segments:
        h = max(y1 - y0 - 2.0, 0.5)  # 2px surface gap between touching fills
        out.append(
            f'<rect x="{x:.1f}" y="{y0:.1f}" width="{width:.1f}" height="{h:.1f}" '
            f'rx="2" fill="{color}"><title>{_esc(title)}</title></rect>'
        )
    return "".join(out)


def _sec_build_mix(payload: dict) -> str:
    """§2.3 build-mix by setpoint: stacked MW bars per resource per setpoint;
    split-storage techs additionally report selected energy MWh (ADR 0006)."""
    prov = payload["provenance"]
    rows = payload["build_mix"]
    resources: list[str] = []
    for r in rows:
        if r["resource"] not in resources:
            resources.append(r["resource"])
    color_of = {name: _series_color(i) for i, name in enumerate(resources)}

    blocks = []
    for iso in prov["isos"]:
        iso_rows = [r for r in rows if r["iso"] == iso]
        setpoints = sorted({r["setpoint"] for r in iso_rows})
        totals = {
            sp: sum(r["build_mw"] for r in iso_rows if r["setpoint"] == sp)
            for sp in setpoints
        }
        W, H, L, R, T, B = 680, 300, 64, 20, 16, 44
        ymax = max(list(totals.values()) + [1.0])
        yticks = _nice_ticks(0, ymax)
        ys = _LinScale(0, yticks[-1], H - B, T)
        band = (W - R - L) / max(len(setpoints), 1)
        bar_w = min(24.0, band * 0.6)

        parts = [_svg_open(W, H)]
        for t in yticks:
            y = ys(t)
            parts.append(
                f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" '
                f'stroke="{_GRID}" stroke-width="1"/>'
                f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
                f"{_esc(_fmt_num(t))}</text>"
            )
        for j, sp in enumerate(setpoints):
            cx = L + band * (j + 0.5)
            x0 = cx - bar_w / 2
            y_cursor = ys(0)
            segs = []
            for name in resources:
                mw = sum(
                    r["build_mw"]
                    for r in iso_rows
                    if r["setpoint"] == sp and r["resource"] == name
                )
                if mw <= 1e-6:
                    continue
                y_top = y_cursor - (ys(0) - ys(mw))
                energy = next(
                    (
                        r["build_energy_mwh"]
                        for r in iso_rows
                        if r["setpoint"] == sp
                        and r["resource"] == name
                        and r["build_energy_mwh"] is not None
                    ),
                    None,
                )
                title = f"{name}: {_fmt_num(mw)} MW"
                if energy is not None:
                    title += f" / {_fmt_num(energy)} MWh energy"
                title += f"\nsetpoint {_setpoint_key(sp)}"
                segs.append((y_top, y_cursor, color_of[name], title))
                y_cursor = y_top
            parts.append(_stack_column(x0, bar_w, segs))
            parts.append(
                f'<text x="{cx:.1f}" y="{H - B + 20:.1f}" text-anchor="middle" '
                f'class="tick">{_esc(_setpoint_key(sp))}</text>'
            )
        parts.append(
            f'<line x1="{L}" x2="{W - R}" y1="{ys(0):.1f}" y2="{ys(0):.1f}" '
            f'stroke="{_BASELINE}" stroke-width="1"/>'
            f'<text x="{(L + W - R) / 2:.0f}" y="{H - 6}" text-anchor="middle" '
            f'class="axis-label">setpoint</text>'
            f'<text x="14" y="{(T + H - B) / 2:.0f}" text-anchor="middle" '
            f'class="axis-label" transform="rotate(-90 14 {(T + H - B) / 2:.0f})">'
            f"build MW</text></svg>"
        )
        heading = f"<h3>{_esc(iso)}</h3>" if len(prov["isos"]) > 1 else ""
        blocks.append(heading + "".join(parts) + _split_energy_table(iso_rows))

    legend = _legend([(name, color_of[name]) for name in resources])
    table = _build_mix_table_view(rows)
    return (
        f'<section id="{SECTION_ANCHORS["2.3"]}"><h2>Build mix by setpoint</h2>'
        f"{legend}{''.join(blocks)}{table}</section>"
    )


def _split_energy_table(iso_rows: list[dict]) -> str:
    """Energy-MWh sub-table for split-storage techs (§2.3, ADR 0006); empty
    string when the run has no split tech built."""
    split_rows = [
        r
        for r in iso_rows
        if r["build_energy_mwh"] is not None and r["build_mw"] > 1e-6
    ]
    if not split_rows:
        return ""
    body = "".join(
        f"<tr><td>{_esc(r['resource'])}</td><td>{_esc(_setpoint_key(r['setpoint']))}"
        f"</td><td>{_fmt_num(r['build_mw'])}</td>"
        f"<td>{_fmt_num(r['build_energy_mwh'])}</td>"
        f"<td>{r['build_energy_mwh'] / r['build_mw']:.1f} h</td></tr>"
        for r in split_rows
    )
    return (
        "<h4>Split-tech energy sizing (ADR 0006)</h4><table><thead><tr>"
        "<th>resource</th><th>setpoint</th><th>power MW</th><th>energy MWh</th>"
        f"<th>duration</th></tr></thead><tbody>{body}</tbody></table>"
    )


def _build_mix_table_view(rows: list[dict]) -> str:
    """Collapsible table twin of the build-mix chart."""
    body = "".join(
        f"<tr><td>{_esc(r['iso'])}</td><td>{_esc(_setpoint_key(r['setpoint']))}</td>"
        f"<td>{_esc(r['resource'])}</td><td>{_fmt_num(r['build_mw'], 1)}</td>"
        f"<td>{_fmt_num(r['build_energy_mwh'], 1) if r['build_energy_mwh'] is not None else '—'}</td></tr>"
        for r in rows
        if r["build_mw"] > 1e-6
    )
    return (
        "<details><summary>Table view</summary><table><thead><tr>"
        "<th>ISO</th><th>setpoint</th><th>resource</th><th>MW</th><th>MWh (split)</th>"
        f"</tr></thead><tbody>{body}</tbody></table></details>"
    )


def _sec_cost(payload: dict) -> str:
    """§2.4 cost breakdown by setpoint: capital+VOM and grid-purchase stacks
    above the baseline, surplus revenue negative below it (ADR 0005 netting),
    with a net-cost tick and the BAU reference line."""
    prov = payload["provenance"]
    rows = payload["frontier"]
    comp_colors = {
        "capital + VOM": _SERIES[0],
        "grid purchases": _SERIES[4],
        "surplus revenue": _SERIES[1],
    }

    blocks = []
    for iso in prov["isos"]:
        iso_rows = sorted(
            (r for r in rows if r["iso"] == iso), key=lambda r: r["setpoint"]
        )
        if not iso_rows:
            continue
        bau = iso_rows[0]["bau_cost"]
        tops, bottoms = [bau], [0.0]
        for r in iso_rows:
            grid_cost = r["bau_cost"] - r["avoided_purchase_cost"]
            tops.append(r["capital_cost"] + grid_cost)
            bottoms.append(-r["surplus_revenue"])
        W, H, L, R, T, B = 680, 320, 76, 20, 16, 44
        yticks = _nice_ticks(min(bottoms), max(tops))
        ys = _LinScale(yticks[0], yticks[-1], H - B, T)
        band = (W - R - L) / max(len(iso_rows), 1)
        bar_w = min(24.0, band * 0.6)

        parts = [_svg_open(W, H)]
        for t in yticks:
            y = ys(t)
            parts.append(
                f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" '
                f'stroke="{_GRID}" stroke-width="1"/>'
                f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
                f"{_esc(_fmt_money(t))}</text>"
            )
        y_bau = ys(bau)
        parts.append(
            f'<line x1="{L}" x2="{W - R}" y1="{y_bau:.1f}" y2="{y_bau:.1f}" '
            f'stroke="{_MUTED}" stroke-width="1">'
            f"<title>BAU cost: {_esc(_fmt_money(bau))}</title></line>"
            f'<text x="{L - 8}" y="{y_bau + 4:.1f}" text-anchor="end" '
            f'class="pt-label">BAU</text>'
        )
        for j, r in enumerate(iso_rows):
            cx = L + band * (j + 0.5)
            x0 = cx - bar_w / 2
            grid_cost = r["bau_cost"] - r["avoided_purchase_cost"]
            common = (
                f"\nnet cost: {_fmt_money(r['net_cost'])}"
                f"\npremium/yr: {_fmt_money(r['premium_per_year'])}"
                f"\nover BAU: {r['pct_over_bau'] * 100:.2f}%"
            )
            segs = []
            y_cursor = ys(0)
            for label, value in (
                ("grid purchases", grid_cost),
                ("capital + VOM", r["capital_cost"]),
            ):
                if value <= 1e-9:
                    continue
                y_top = y_cursor - (ys(0) - ys(value))
                segs.append(
                    (
                        y_top,
                        y_cursor,
                        comp_colors[label],
                        f"{label}: {_fmt_money(value)}\n"
                        f"setpoint {_setpoint_key(r['setpoint'])}{common}",
                    )
                )
                y_cursor = y_top
            parts.append(_stack_column(x0, bar_w, segs))
            if r["surplus_revenue"] > 1e-9:  # revenues negative in the stack
                y1 = ys(-r["surplus_revenue"])
                parts.append(
                    f'<rect x="{x0:.1f}" y="{ys(0) + 1:.1f}" width="{bar_w:.1f}" '
                    f'height="{max(y1 - ys(0) - 1, 0.5):.1f}" rx="2" '
                    f'fill="{comp_colors["surplus revenue"]}">'
                    f"<title>surplus revenue: -{_esc(_fmt_money(r['surplus_revenue']))}"
                    f"\nsetpoint {_esc(_setpoint_key(r['setpoint']))}{_esc(common)}"
                    f"</title></rect>"
                )
            y_net = ys(r["net_cost"])
            parts.append(
                f'<line x1="{x0 - 4:.1f}" x2="{x0 + bar_w + 4:.1f}" '
                f'y1="{y_net:.1f}" y2="{y_net:.1f}" stroke="{_INK}" '
                f'stroke-width="2"><title>net cost: '
                f"{_esc(_fmt_money(r['net_cost']))}</title></line>"
                f'<text x="{cx:.1f}" y="{H - B + 20:.1f}" text-anchor="middle" '
                f'class="tick">{_esc(_setpoint_key(r["setpoint"]))}</text>'
            )
        parts.append(
            f'<line x1="{L}" x2="{W - R}" y1="{ys(0):.1f}" y2="{ys(0):.1f}" '
            f'stroke="{_BASELINE}" stroke-width="1"/>'
            f'<text x="{(L + W - R) / 2:.0f}" y="{H - 6}" text-anchor="middle" '
            f'class="axis-label">setpoint</text></svg>'
        )
        heading = f"<h3>{_esc(iso)}</h3>" if len(prov["isos"]) > 1 else ""
        blocks.append(heading + "".join(parts))

    legend = _legend(list(comp_colors.items()) + [("net cost (tick)", _INK)])
    note = (
        '<p class="note">Revenues are negative in the stack (ADR 0005 netting); '
        "the black tick is net cost, the gray line is BAU cost.</p>"
    )
    table = _cost_table_view(rows)
    return (
        f'<section id="{SECTION_ANCHORS["2.4"]}"><h2>Cost breakdown by setpoint'
        f"</h2>{legend}{''.join(blocks)}{note}{table}</section>"
    )


def _cost_table_view(rows: list[dict]) -> str:
    """Collapsible table twin of the cost-breakdown chart."""
    body = "".join(
        f"<tr><td>{_esc(r['iso'])}</td><td>{_esc(_setpoint_key(r['setpoint']))}</td>"
        f"<td>{_fmt_money(r['capital_cost'])}</td>"
        f"<td>{_fmt_money(r['bau_cost'] - r['avoided_purchase_cost'])}</td>"
        f"<td>-{_fmt_money(r['surplus_revenue'])}</td>"
        f"<td>{_fmt_money(r['net_cost'])}</td>"
        f"<td>{_fmt_money(r['bau_cost'])}</td>"
        f"<td>{_fmt_money(r['premium_per_year'])}</td></tr>"
        for r in rows
    )
    return (
        "<details><summary>Table view</summary><table><thead><tr>"
        "<th>ISO</th><th>setpoint</th><th>capital+VOM</th><th>grid purchases</th>"
        "<th>surplus revenue</th><th>net cost</th><th>BAU cost</th>"
        f"<th>premium $/yr</th></tr></thead><tbody>{body}</tbody></table></details>"
    )


def _show_residual(payload: dict) -> bool:
    """§2.5 gate: omitted, like the CLI summary, when the emission rate was off
    for the whole sweep (every residual is zero — ADR 0014 §2.5)."""
    return any(r["residual_co2_tons"] > 0 for r in payload["frontier"])


def _sec_residual(payload: dict) -> str:
    """§2.5 residual-CO₂ view: residual tCO₂/yr (ADR 0013) vs setpoint, with
    the achieved matching % direct-labeled on each bar (one axis, no dual-y)."""
    prov = payload["provenance"]
    rows = payload["frontier"]
    blocks = []
    for i, iso in enumerate(prov["isos"]):
        iso_rows = sorted(
            (r for r in rows if r["iso"] == iso), key=lambda r: r["setpoint"]
        )
        W, H, L, R, T, B = 680, 280, 76, 20, 28, 44
        ymax = max([r["residual_co2_tons"] for r in iso_rows] + [1.0])
        yticks = _nice_ticks(0, ymax)
        ys = _LinScale(0, yticks[-1], H - B, T)
        band = (W - R - L) / max(len(iso_rows), 1)
        bar_w = min(24.0, band * 0.6)

        parts = [_svg_open(W, H)]
        for t in yticks:
            y = ys(t)
            parts.append(
                f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" '
                f'stroke="{_GRID}" stroke-width="1"/>'
                f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
                f"{_esc(_fmt_num(t))}</text>"
            )
        for j, r in enumerate(iso_rows):
            cx = L + band * (j + 0.5)
            x0 = cx - bar_w / 2
            y_top = ys(r["residual_co2_tons"])
            title = (
                f"setpoint {_setpoint_key(r['setpoint'])}\n"
                f"residual: {_fmt_num(r['residual_co2_tons'])} tCO2/yr\n"
                f"grid: {_fmt_num(r['grid_co2_tons'])} t / resource: "
                f"{_fmt_num(r['resource_co2_tons'])} t\n"
                f"matching: {r['matching_pct'] * 100:.2f}%"
            )
            parts.append(
                f'<rect x="{x0:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                f'height="{max(ys(0) - y_top, 0.5):.1f}" rx="2" '
                f'fill="{_series_color(i)}"><title>{_esc(title)}</title></rect>'
                f'<text x="{cx:.1f}" y="{y_top - 6:.1f}" text-anchor="middle" '
                f'class="pt-label">{r["matching_pct"] * 100:.1f}%</text>'
                f'<text x="{cx:.1f}" y="{H - B + 20:.1f}" text-anchor="middle" '
                f'class="tick">{_esc(_setpoint_key(r["setpoint"]))}</text>'
            )
        parts.append(
            f'<line x1="{L}" x2="{W - R}" y1="{ys(0):.1f}" y2="{ys(0):.1f}" '
            f'stroke="{_BASELINE}" stroke-width="1"/>'
            f'<text x="{(L + W - R) / 2:.0f}" y="{H - 6}" text-anchor="middle" '
            f'class="axis-label">setpoint</text>'
            f'<text x="14" y="{(T + H - B) / 2:.0f}" text-anchor="middle" '
            f'class="axis-label" transform="rotate(-90 14 {(T + H - B) / 2:.0f})">'
            f"residual tCO2/yr</text></svg>"
        )
        heading = f"<h3>{_esc(iso)}</h3>" if len(prov["isos"]) > 1 else ""
        blocks.append(heading + "".join(parts))
    note = (
        '<p class="note">Bar labels are the achieved matching % at each '
        "setpoint; hover for the grid vs resource residual split "
        "(ADR 0013 / ADR 0012).</p>"
    )
    return (
        f'<section id="{SECTION_ANCHORS["2.5"]}"><h2>Residual CO2</h2>'
        f"{''.join(blocks)}{note}</section>"
    )


def _sec_multi_iso(payload: dict) -> str:
    """§2.6 multi-ISO comparison table: matching % and premium at each common
    setpoint per ISO. Rendered only for batch (>1 ISO) runs."""
    prov = payload["provenance"]
    rows = payload["frontier"]
    isos = prov["isos"]
    setpoints = sorted({r["setpoint"] for r in rows})
    cell = {(r["iso"], r["setpoint"]): r for r in rows}
    head = "".join(f'<th colspan="2">{_esc(iso)}</th>' for iso in isos)
    sub = "".join("<th>matching</th><th>$/MWh</th>" for _ in isos)
    body = []
    for sp in setpoints:
        tds = [f"<td>{_esc(_setpoint_key(sp))}</td>"]
        for iso in isos:
            r = cell.get((iso, sp))
            if r is None:
                tds.append("<td>—</td><td>—</td>")
            else:
                flag = "" if _is_optimal(r["status"]) else " ⚠"
                tds.append(
                    f"<td>{r['matching_pct'] * 100:.2f}%{flag}</td>"
                    f"<td>{r['premium_per_mwh']:.2f}</td>"
                )
        body.append(f"<tr>{''.join(tds)}</tr>")
    return (
        f'<section id="{SECTION_ANCHORS["2.6"]}"><h2>Multi-ISO comparison</h2>'
        f'<table><thead><tr><th rowspan="2">setpoint</th>{head}</tr>'
        f"<tr>{sub}</tr></thead><tbody>{''.join(body)}</tbody></table></section>"
    )


def _sec_hourly(payload: dict) -> str:
    """§2.7 hourly dispatch view scaffold: per-ISO 24×365 unmatched-heatmap
    canvas + storage-SOC SVG, rendered client-side by the tiny inline script
    from the embedded hourly block; a setpoint selector appears when the
    payload carries more than one setpoint for an ISO (ADR 0014 §2.7/§3)."""
    hourly = payload["hourly"]
    prov = payload["provenance"]
    blocks = []
    for iso in prov["isos"]:
        series = hourly["series"].get(iso, {})
        selected = hourly["selected"].get(iso)
        heading = f"<h3>{_esc(iso)}</h3>" if len(prov["isos"]) > 1 else ""
        if not series:
            blocks.append(
                f'<div class="hourly-block">{heading}<p class="note">No optimal '
                "setpoint solved for this ISO — hourly view unavailable.</p></div>"
            )
            continue
        sel_key = (
            _setpoint_key(selected)
            if selected is not None and _setpoint_key(selected) in series
            else next(iter(series))
        )
        buttons = ""
        if len(series) > 1:
            btns = []
            for k in series:
                active = ' class="active"' if k == sel_key else ""
                btns.append(
                    f'<button type="button" data-iso="{_esc(iso)}" '
                    f'data-sp="{_esc(k)}"{active}>set {_esc(k)}</button>'
                )
            buttons = f'<div class="sp-select">setpoint: {"".join(btns)}</div>'
        blocks.append(
            f'<div class="hourly-block" data-iso="{_esc(iso)}" '
            f'data-selected="{_esc(sel_key)}">{heading}{buttons}'
            f"<h4>Unmatched grid purchases (MWh), hour-of-day × day</h4>"
            f'<div class="heatmap-wrap"><canvas class="heatmap" height="24">'
            f'</canvas><div class="heatmap-scale"><span>0</span>'
            f'<span class="scale-bar"></span><span class="scale-max"></span>'
            f"</div></div>"
            f"<h4>Storage state of charge (MWh)</h4>"
            f'<div class="soc-wrap"></div></div>'
        )
    note = (
        '<p class="note">The heatmap shows when matching fails: darker cells '
        "are hours with more unmatched grid purchases at the selected "
        "setpoint. Hover any cell for its value.</p>"
    )
    return (
        f'<section id="{SECTION_ANCHORS["2.7"]}"><h2>Hourly dispatch — '
        f"selected setpoint</h2>{note}{''.join(blocks)}</section>"
    )


# --------------------------------------------------------------------------
# static chrome: CSS + inline JS (fully offline, no external fetch — §1)
# --------------------------------------------------------------------------

_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; padding: 0; background: #f9f9f7; color: #0b0b0b;
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 20px 64px; }
h1 { font-size: 24px; font-weight: 650; margin: 8px 0 2px; }
h2 { font-size: 18px; font-weight: 650; margin: 0 0 12px; }
h3 { font-size: 15px; font-weight: 650; margin: 16px 0 6px; color: #52514e; }
h4 { font-size: 13px; font-weight: 600; margin: 14px 0 6px; color: #52514e; }
.subtitle { color: #52514e; margin: 0 0 24px; }
section { background: #fcfcfb; border: 1px solid rgba(11,11,11,0.10);
  border-radius: 10px; padding: 20px; margin: 0 0 20px; overflow-x: auto; }
svg { display: block; width: 100%; height: auto; max-width: 720px; }
svg text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
.tick { font-size: 11px; fill: #898781; font-variant-numeric: tabular-nums; }
.axis-label { font-size: 12px; fill: #52514e; }
.pt-label { font-size: 10px; fill: #898781; }
.note { color: #898781; font-size: 13px; margin: 8px 0 0; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px; margin-bottom: 8px; }
.meta-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em;
  color: #898781; }
.meta-value { font-weight: 600; overflow-wrap: anywhere; }
.solves { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0; }
.solve { font-size: 12px; padding: 2px 10px; border-radius: 999px;
  background: #f0efec; color: #52514e; }
.solve-bad { background: #fbeaea; color: #a02c2c; }
.flag { color: #d03b3b; }
details { margin-top: 12px; }
summary { cursor: pointer; color: #52514e; font-size: 13px; }
pre { background: #f0efec; padding: 12px; border-radius: 6px; overflow-x: auto;
  font-size: 12px; }
table { border-collapse: collapse; font-size: 13px; margin-top: 8px;
  font-variant-numeric: tabular-nums; }
th, td { padding: 4px 10px; text-align: right; border-bottom: 1px solid #e1e0d9; }
th:first-child, td:first-child { text-align: left; }
thead th { color: #52514e; font-weight: 600; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin: 0 0 10px; }
.key { display: inline-flex; align-items: center; gap: 6px; font-size: 13px;
  color: #52514e; }
.swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.sp-select { display: flex; gap: 6px; align-items: center; font-size: 13px;
  color: #52514e; margin: 8px 0; flex-wrap: wrap; }
.sp-select button { font: inherit; padding: 3px 12px; border-radius: 999px;
  border: 1px solid #e1e0d9; background: #fcfcfb; cursor: pointer; }
.sp-select button.active { background: #2a78d6; border-color: #2a78d6;
  color: #fff; }
.heatmap-wrap { position: relative; }
canvas.heatmap { width: 100%; max-width: 720px; height: 220px;
  image-rendering: pixelated; border: 1px solid #e1e0d9; border-radius: 4px; }
.heatmap-scale { display: flex; align-items: center; gap: 8px; font-size: 11px;
  color: #898781; margin-top: 4px; font-variant-numeric: tabular-nums; }
.scale-bar { width: 140px; height: 8px; border-radius: 4px;
  background: linear-gradient(90deg,#fcfcfb,#cde2fb,#86b6ef,#3987e5,#1c5cab,#0d366b); }
#tooltip { position: fixed; pointer-events: none; background: #0b0b0b;
  color: #fff; font-size: 12px; padding: 6px 9px; border-radius: 6px;
  display: none; z-index: 10; white-space: pre; }
footer { color: #898781; font-size: 12px; text-align: center; }
"""

# Tiny inline renderer for §2.7: reads the embedded hourly block, draws the
# 24x365 unmatched heatmap on a canvas (1px per cell, CSS-scaled) and the SOC
# trace as a generated SVG polyline; wires the setpoint selector + tooltips.
# No external libraries (ADR 0014 §1).
_JS = """
(function () {
  var HOURLY = JSON.parse(document.getElementById('report-hourly').textContent);
  var RAMP = ['#cde2fb','#9ec5f4','#86b6ef','#5598e7','#3987e5','#256abf','#1c5cab','#104281','#0d366b'];
  var SOC_COLORS = ['#2a78d6','#1baf7a','#eda100','#008300','#4a3aa7','#e34948'];
  var tooltip = document.getElementById('tooltip');

  function fmt(v) { return v.toLocaleString('en-US', {maximumFractionDigits: 1}); }

  function cellColor(v, vmax) {
    if (v <= 0 || vmax <= 0) return '#fcfcfb';
    var i = Math.min(RAMP.length - 1, Math.floor(v / vmax * RAMP.length));
    return RAMP[i];
  }

  function drawHeatmap(block, s) {
    var canvas = block.querySelector('canvas.heatmap');
    var buy = s.grid_buy_mwh, T = buy.length;
    var days = Math.ceil(T / 24);
    canvas.width = days;
    canvas.height = 24;
    var vmax = 0;
    for (var t = 0; t < T; t++) if (buy[t] > vmax) vmax = buy[t];
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fcfcfb';
    ctx.fillRect(0, 0, days, 24);
    for (t = 0; t < T; t++) {
      ctx.fillStyle = cellColor(buy[t], vmax);
      ctx.fillRect(Math.floor(t / 24), t % 24, 1, 1);
    }
    block.querySelector('.scale-max').textContent = fmt(vmax) + ' MWh';
    canvas.onmousemove = function (ev) {
      var r = canvas.getBoundingClientRect();
      var day = Math.floor((ev.clientX - r.left) / r.width * days);
      var hr = Math.floor((ev.clientY - r.top) / r.height * 24);
      var t2 = day * 24 + hr;
      if (t2 < 0 || t2 >= T) { tooltip.style.display = 'none'; return; }
      tooltip.textContent = 'day ' + (day + 1) + ', hour ' + hr +
        '\\nunmatched: ' + fmt(buy[t2]) + ' MWh';
      tooltip.style.display = 'block';
      tooltip.style.left = (ev.clientX + 14) + 'px';
      tooltip.style.top = (ev.clientY + 14) + 'px';
    };
    canvas.onmouseleave = function () { tooltip.style.display = 'none'; };
  }

  function drawSoc(block, s) {
    var wrap = block.querySelector('.soc-wrap');
    var names = Object.keys(s.soc_mwh);
    if (!names.length) {
      wrap.innerHTML = '<p class="note">No storage in this portfolio.</p>';
      return;
    }
    var W = 720, H = 150, L = 56, R = 8, T0 = 8, B = 20;
    var vmax = 0, T = s.soc_mwh[names[0]].length;
    names.forEach(function (n) {
      s.soc_mwh[n].forEach(function (v) { if (v > vmax) vmax = v; });
    });
    if (vmax <= 0) vmax = 1;
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img">';
    [0, 0.5, 1].forEach(function (f) {
      var y = (H - B) - f * (H - B - T0);
      svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y +
        '" stroke="#e1e0d9" stroke-width="1"/>' +
        '<text x="' + (L - 6) + '" y="' + (y + 4) + '" text-anchor="end" class="tick">' +
        fmt(vmax * f) + '</text>';
    });
    names.forEach(function (n, i) {
      var pts = [], arr = s.soc_mwh[n];
      for (var t = 0; t < T; t++) {
        var x = L + t / (T - 1) * (W - L - R);
        var y = (H - B) - arr[t] / vmax * (H - B - T0);
        pts.push(x.toFixed(1) + ',' + y.toFixed(1));
      }
      svg += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="' +
        SOC_COLORS[i % SOC_COLORS.length] + '" stroke-width="1.2"/>';
    });
    svg += '<text x="' + ((L + W - R) / 2) + '" y="' + (H - 4) +
      '" text-anchor="middle" class="axis-label">hour of year</text></svg>';
    var legend = '<div class="legend">' + names.map(function (n, i) {
      return '<span class="key"><span class="swatch" style="background:' +
        SOC_COLORS[i % SOC_COLORS.length] + '"></span>' + n + '</span>';
    }).join('') + '</div>';
    wrap.innerHTML = legend + svg;
  }

  function render(block, spKey) {
    var iso = block.getAttribute('data-iso');
    var s = HOURLY.series[iso][spKey];
    if (!s) return;
    drawHeatmap(block, s);
    drawSoc(block, s);
    block.querySelectorAll('.sp-select button').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-sp') === spKey);
    });
  }

  document.querySelectorAll('.hourly-block[data-iso]').forEach(function (block) {
    render(block, block.getAttribute('data-selected'));
    block.querySelectorAll('.sp-select button').forEach(function (b) {
      b.addEventListener('click', function () {
        render(block, b.getAttribute('data-sp'));
      });
    });
  });
})();
"""


def render_report(payload: dict) -> str:
    """Render the report payload into one self-contained HTML page (ADR 0014).

    Implements §1 (fully offline: inline CSS/JS/data only, renders exclusively
    from ``payload``) and the §2.1–§2.7 views in order; §2.5 is omitted when
    the emission rate was off for the whole sweep and §2.6 only appears for
    multi-ISO batch runs. Raises :class:`ValueError` on any
    ``payload_version`` not in :data:`KNOWN_PAYLOAD_VERSIONS` (§3).

    Pure function of ``payload`` — same payload, byte-identical HTML — so
    ``scripts/render_report.py`` can regenerate a committed run's HTML
    deterministically (§6).
    """
    version = payload.get("payload_version")
    if version not in KNOWN_PAYLOAD_VERSIONS:
        raise ValueError(
            f"unknown payload_version {version!r}; this renderer supports "
            f"{list(KNOWN_PAYLOAD_VERSIONS)} (ADR 0014 §3)"
        )
    prov = payload["provenance"]
    run_id = prov.get("run_id") or "ad-hoc run"
    title = f"LCE portfolio report — {run_id}"

    sections = [
        _sec_provenance(payload),
        _sec_frontier(payload),
        _sec_build_mix(payload),
        _sec_cost(payload),
    ]
    if _show_residual(payload):
        sections.append(_sec_residual(payload))
    if len(prov["isos"]) > 1:
        sections.append(_sec_multi_iso(payload))
    sections.append(_sec_hourly(payload))

    # Embed only the hourly block for the client-side §2.7 renderer; escape
    # "</" so payload text can never terminate the script element.
    hourly_json = json.dumps(payload["hourly"], separators=(",", ":")).replace(
        "</", "<\\/"
    )

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head><body>\n"
        '<div id="tooltip"></div>\n'
        "<main>\n"
        f"<h1>Scope 2 LCE portfolio report</h1>\n"
        f'<p class="subtitle">{_esc(run_id)} — '
        f"{_esc(', '.join(prov['isos']))} / {_esc(prov['mode'])}</p>\n"
        + "\n".join(sections)
        + "\n<footer>Generated by lce_portfolio "
        f"{_esc(prov['tool_version'])} — self-contained report "
        "(ADR 0014); data: report.json in this run folder.</footer>\n"
        "</main>\n"
        f'<script id="report-hourly" type="application/json">{hourly_json}'
        "</script>\n"
        f"<script>{_JS}</script>\n"
        "</body></html>\n"
    )
