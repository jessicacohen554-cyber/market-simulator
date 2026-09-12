"""miso-255 phase 0: does MISO's CC_REGULAR fleet capacity factor track the meter?

Ports the ``pjm-h1`` zero-LP instrument
(``docs/FINDING-pjm-h1-cc-cf-does-not-track-2026-09-12.md``) onto MISO's own
committed artifacts. Rule 28(d) ``[R-MECH-MATRIX]``: a PJM verdict fills no
MISO cell, so every number here is re-measured on MISO data.

Reads ONLY committed artifacts — the registry sidecars, the run payloads and
the CAMPD bench parts — decoded exactly as :mod:`legitimacy_diagnostics`
decodes them (``load_bench`` / ``load_payload_plants`` / ``_decode_cf_bytes``).
**Zero LP.**

Emits, per class and year: matched-fleet annual capacity factor (model vs
CAMPD meter), the cross-year correlation and slope, the on-hours / loading
split, the ``a / b+ / b- / c`` energy decomposition, the meter's revealed
capability (p99.5 MW / nameplate) and the concentration of the net miss.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import legitimacy_diagnostics as L  # noqa: E402

# The MISO runs that carry a per-plant payload, one per year. Every one is a
# COMMITTED registry sidecar (rule 15 [R-DASHBOARD]); 2023-2025 is the keeper,
# 2020-2022 the folded touchpoints / screen.
SIDECARS = {
    2020: "2026-09-10-miso-251-tp2020",
    2021: "2026-09-10-miso-251-tp2021",
    2022: "2026-09-10-miso-251-screen2022",
    2023: "2026-09-09-miso-250-ep-gas",
    2024: "2026-09-09-miso-250-ep-gas",
    2025: "2026-09-09-miso-250-ep-gas",
}
YEARS = tuple(sorted(SIDECARS))
CLASSES = (
    "CC_REGULAR",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_LIGNITE",
    "CT_PEAKER",
    "ST_GAS",
    "CC_CHP",
)


def _sidecar(run_id: str) -> dict:
    return json.loads(
        (REPO / "frontend/data/backcast/registry" / f"{run_id}.json").read_text()
    )


def load_year(year: int) -> tuple[dict, dict]:
    """Return ``(bench, model)`` keyed identically, restricted to matched plants."""
    bench = L.load_bench(REPO, "MISO", year)
    model = L.load_payload_plants(REPO, _sidecar(SIDECARS[year]), year, bench)
    keys = sorted(set(bench) & set(model))
    return {k: bench[k] for k in keys}, {k: model[k] for k in keys}


def _fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Pearson r and OLS slope d(y)/d(x)."""
    if x.size < 3 or x.std() == 0.0 or y.std() == 0.0:
        return float("nan"), float("nan")
    r = float(np.corrcoef(x, y)[0, 1])
    slope = float(np.polyfit(x, y, 1)[0])
    return r, slope


def main() -> None:
    per_year: dict[int, tuple[dict, dict]] = {y: load_year(y) for y in YEARS}

    rows: dict[str, dict[int, dict]] = {c: {} for c in CLASSES}
    for year, (bench, model) in per_year.items():
        for klass in CLASSES:
            keys = [k for k, b in bench.items() if b["group"] == klass]
            if not keys:
                continue
            npl = float(sum(bench[k]["npl"] for k in keys))
            if npl <= 0.0:
                continue
            m = np.sum([model[k] for k in keys], axis=0)
            c = np.sum([bench[k]["mw"] for k in keys], axis=0)
            n_h = m.size
            m_on, c_on = m > 0.0, c > 0.0
            both = m_on & c_on
            d = m - c
            rows[klass][year] = {
                "n": len(keys),
                "npl_gw": npl / 1e3,
                "model_twh": float(m.sum()) / 1e6,
                "meter_twh": float(c.sum()) / 1e6,
                "model_cf": float(m.sum()) / (npl * n_h),
                "meter_cf": float(c.sum()) / (npl * n_h),
                "model_onhr": float(m_on.mean()),
                "meter_onhr": float(c_on.mean()),
                # loading when BOTH are on, against the matched nameplate
                "model_load_both": float(m[both].mean()) / npl if both.any() else 0.0,
                "meter_load_both": float(c[both].mean()) / npl if both.any() else 0.0,
                # the a / b+ / b- / c energy decomposition (TWh)
                "a": float(m[m_on & ~c_on].sum()) / 1e6,
                "c": float(c[c_on & ~m_on].sum()) / 1e6,
                "bp": float(d[both][d[both] > 0].sum()) / 1e6,
                "bm": float(-d[both][d[both] < 0].sum()) / 1e6,
            }

    print("=" * 100)
    print("1. CF-TRACKING TABLE — MISO matched fleet, model vs CAMPD meter")
    print("=" * 100)
    for klass in CLASSES:
        yrs = sorted(rows[klass])
        if len(yrs) < 3:
            continue
        mcf = np.array([rows[klass][y]["model_cf"] for y in yrs])
        ccf = np.array([rows[klass][y]["meter_cf"] for y in yrs])
        r, slope = _fit(ccf, mcf)
        print(f"\n--- {klass} ---")
        hdr = f"{'':28s}" + "".join(f"{y:>10d}" for y in yrs)
        print(hdr)
        for label, key, fmt in (
            ("plants", "n", "{:10d}"),
            ("matched nameplate (GW)", "npl_gw", "{:10.2f}"),
            ("model TWh", "model_twh", "{:10.2f}"),
            ("meter TWh", "meter_twh", "{:10.2f}"),
            ("model CF", "model_cf", "{:10.4f}"),
            ("meter CF", "meter_cf", "{:10.4f}"),
            ("model on-hours frac", "model_onhr", "{:10.4f}"),
            ("meter on-hours frac", "meter_onhr", "{:10.4f}"),
            ("model loading (both on)", "model_load_both", "{:10.4f}"),
            ("meter loading (both on)", "meter_load_both", "{:10.4f}"),
        ):
            print(
                f"{label:28s}" + "".join(fmt.format(rows[klass][y][key]) for y in yrs)
            )
        print(
            f"{'delta CF (model-meter)':28s}"
            + "".join(
                "{:10.4f}".format(
                    rows[klass][y]["model_cf"] - rows[klass][y]["meter_cf"]
                )
                for y in yrs
            )
        )
        print(
            f"{'on-hours gap (pp)':28s}"
            + "".join(
                "{:10.1f}".format(
                    100.0
                    * (rows[klass][y]["model_onhr"] - rows[klass][y]["meter_onhr"])
                )
                for y in yrs
            )
        )
        print(
            f"  model CF range {mcf.max() - mcf.min():.4f}   "
            f"meter CF range {ccf.max() - ccf.min():.4f}   "
            f"cross-year r {r:+.3f}   d(model)/d(meter) {slope:+.3f}"
        )

    print("\n" + "=" * 100)
    print("2. HOURS / LOADING SPLIT (TWh) — net = (a - c) + (b+ - b-)")
    print("=" * 100)
    for klass in CLASSES:
        yrs = sorted(rows[klass])
        if len(yrs) < 3:
            continue
        print(f"\n--- {klass} ---")
        print(
            f"{'yr':>6s}{'net':>10s}{'hours a-c':>12s}{'loading b+ - b-':>18s}"
            f"{'a':>9s}{'b+':>9s}{'b-':>9s}{'c':>9s}"
        )
        for y in yrs:
            d = rows[klass][y]
            net = d["model_twh"] - d["meter_twh"]
            print(
                f"{y:>6d}{net:>10.2f}{d['a'] - d['c']:>12.2f}"
                f"{d['bp'] - d['bm']:>18.2f}"
                f"{d['a']:>9.2f}{d['bp']:>9.2f}{d['bm']:>9.2f}{d['c']:>9.2f}"
            )

    print("\n" + "=" * 100)
    print("3a. REVEALED CAPABILITY — per-plant p99.5 meter MW / nameplate")
    print("    PLANT grain (bench_plant_view): the bench carries slice keys whose")
    print("    nameplate sentinel is 1.0 MW, which is meaningless per slice.")
    print("=" * 100)
    print(f"{'class':>14s}{'stat':>9s}" + "".join(f"{y:>10d}" for y in YEARS))
    for klass in CLASSES:
        means, meds, ns = [], [], []
        for y in YEARS:
            bench, _ = per_year[y]
            # attribute each plant to the class carrying most of its nameplate
            own: dict[str, tuple[float, str]] = {}
            agg: dict[str, dict] = {}
            for k, b in bench.items():
                code = k.split(":")[0]
                cur = agg.setdefault(code, {"npl": 0.0, "mw": np.zeros_like(b["mw"])})
                cur["npl"] += b["npl"]
                cur["mw"] = cur["mw"] + b["mw"]
                if b["npl"] > own.get(code, (0.0, ""))[0]:
                    own[code] = (b["npl"], b["group"])
            rat = [
                float(np.percentile(agg[c]["mw"], 99.5)) / agg[c]["npl"]
                for c in agg
                if own.get(c, (0.0, ""))[1] == klass and agg[c]["npl"] > 10.0
            ]
            means.append(float(np.mean(rat)) if rat else float("nan"))
            meds.append(float(np.median(rat)) if rat else float("nan"))
            ns.append(len(rat))
        print(f"{klass:>14s}{'mean':>9s}" + "".join(f"{v:>10.4f}" for v in means))
        print(f"{'':>14s}{'median':>9s}" + "".join(f"{v:>10.4f}" for v in meds))
        print(f"{'':>14s}{'n':>9s}" + "".join(f"{v:>10d}" for v in ns))

    print("\n" + "=" * 100)
    print("3c. CONCENTRATION of the CC_REGULAR net miss (plant level)")
    print("    'top5 same-sign' ranks plants in the DIRECTION of the net miss.")
    print("=" * 100)
    print(
        f"{'yr':>6s}{'net TWh':>10s}{'n':>5s}{'n over':>8s}{'n under':>9s}"
        f"{'top5 same-sign':>16s}{'% of net':>10s}{'gross same-sign':>17s}"
    )
    for y in YEARS:
        bench, model = per_year[y]
        keys = [k for k, b in bench.items() if b["group"] == "CC_REGULAR"]
        per = sorted(float(model[k].sum() - bench[k]["mw"].sum()) / 1e6 for k in keys)
        net = sum(per)
        n_over = sum(1 for v in per if v > 0)
        same = [v for v in per if (v < 0) == (net < 0)]
        same.sort(key=abs, reverse=True)
        top5 = sum(same[:5])
        print(
            f"{y:>6d}{net:>10.2f}{len(per):>5d}{n_over:>8d}"
            f"{len(per) - n_over:>9d}{top5:>16.2f}"
            f"{100.0 * top5 / net if net else float('nan'):>9.1f}%"
            f"{sum(same):>17.2f}"
        )


if __name__ == "__main__":
    main()
