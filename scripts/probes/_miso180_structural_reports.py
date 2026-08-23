"""miso-180 structural report driver — the ungated PREREG §5 blocks.

Re-runs, on BOTH A/B bundles, the committed miso-178 instruments the prereg
names (all report-only, gated by nothing):

* **the South-dipole prediction** — the ``_miso178_c3a2025_anatomy`` zonal
  stage (per-zone demand-weighted own-error, all three years); the ex-ante
  expectation is MISO-South's 2025 own-error (+17.0 % at control) moving
  TOWARD ZERO with no South-specific mechanism (rule 1's falsifiable test);
* **the miso-178 bucket decomposition** (tail / top-decile / remainder pp);
* **the Δ-channel re-run** — the miso-156 three-channel decomposition on the
  ARM's 2025 (Δ₁ should collapse toward 0; Δ₂ must not grow materially more
  negative). The arm's model-side construction is faithful because
  ``_miso134.build_year`` gained the same seam step the pipeline did
  (flag-gated, no-op for every committed record).

The control's numbers double as the G-0 cross-check: a bit-identical control
must reproduce the committed miso-178 record.

Usage::

    cd <repo root> && uv run --no-project \\
      --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \\
      python scripts/probes/_miso180_structural_reports.py
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso178_c3a2025_anatomy as _anat  # noqa: E402
import _miso178_c3a_decomposition as _m178  # noqa: E402

_m156 = _m178._m156
_m134 = _m178._m134 if hasattr(_m178, "_m134") else None

BUNDLES = {
    "control": REPO / "results/calibration/miso180_anch_A",
    "arm": REPO / "results/calibration/miso180_anch_B",
}
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/_miso180_structural_reports.json"


def anatomy_stages(bundle: Path) -> dict:
    """Zonal + bucket stages of the miso-178 anatomy on one bundle."""
    _anat.BUNDLE = bundle
    out: dict = {}
    for year in YEARS:
        st = _anat.YearState(year)
        c3a = st.c3a_of(st.Pm)
        zonal = _anat.stage_zonal(st)
        buckets = _anat.stage_buckets(st, _anat.e930(year), _anat.model_class(year))
        out[str(year)] = {
            "c3a_pct": round(c3a, 4),
            "zonal": zonal,
            "buckets": buckets,
        }
        del st
        gc.collect()
    return out


def delta_channels_arm(bundle: Path) -> dict:
    """The miso-156 Δ decomposition on the ARM bundle, 2025."""
    import _miso134_ct_night_order_screen as m134

    m134.BUNDLE = bundle
    _m156.BUNDLE = bundle
    # Pin V1 to the ARM's own scored statistic so the gate checks
    # probe-vs-bundle consistency, exactly as the wrapper lineage pins it to
    # each keeper's.
    _anat.BUNDLE = bundle
    published = {}
    for year in YEARS:
        st = _anat.YearState(year)
        published[year] = round(st.c3a_of(st.Pm) / 100.0, 6)
        del st
    gc.collect()
    _m156.V1_PUBLISHED_C3A = published

    cfg = _m156.keeper_config()
    assert getattr(cfg, "miso_offer_spread_anchored", False), (
        "arm bundle's run_config does not arm miso_offer_spread_anchored — "
        "the Δ re-run would rebuild the wrong surface"
    )
    mb = _m156.model_year(cfg, 2025)
    v1 = _m156.v1_c3a_gate(mb, 2025)
    rec = {
        "V1": {k: v1[k] for k in ("c3a_pct", "published_c3a_pct", "delta_pp", "pass")},
        "flag_armed_in_construction": True,
    }
    if v1["pass"]:
        rec["decomposition_2025"] = _m156.decompose(mb, 2025)
    else:
        rec["decomposition_2025"] = {"SKIPPED": "V1 gate failed on the arm"}
    del mb
    gc.collect()
    return rec


def main() -> dict:
    out: dict = {
        "session": "miso-180",
        "prereg": "PREREG-miso180-anchored-spread-2026-08-23.md",
        "bundles": {k: str(v.name) for k, v in BUNDLES.items()},
    }
    for label, bundle in BUNDLES.items():
        if not (bundle / "run_config.json").is_file():
            out[label] = {"ABSENT": str(bundle)}
            continue
        out[label] = anatomy_stages(bundle)
    if "arm" in out and "ABSENT" not in out["arm"]:
        out["delta_channels_arm"] = delta_channels_arm(BUNDLES["arm"])

    OUT.write_text(json.dumps(out, indent=1, default=str))
    for label in ("control", "arm"):
        blk = out.get(label) or {}
        if "ABSENT" in blk:
            continue
        z25 = blk["2025"]["zonal"]
        south = (z25.get("zones") or {}).get("MISO-South", {}).get("own_err_pct")
        print(
            f"[{label}] 2025 C3a {blk['2025']['c3a_pct']:+.3f}%  "
            f"South own-err {south if south is None else round(south, 3)}%"
        )
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
