"""No benchmark actual may be NEGATIVE unless the measurement itself is (miso-267).

The owner's ask was a test "that asserts no classFull entry is negative for any
(ISO, year)". Taken literally that is FALSE of net generation, which EIA-923
books net of station service and pumping: SOCO's ``OTHER`` class carries its
pumped storage (``PS/WAT`` -0.65 to -0.70 TWh a year), and NEISO's 2020
``COAL_PRB`` is one idle coal unit's station service (Bridgeport 568 ``ST/SUB``
-19,082 MWh). Both are measured and both are right. What must never happen is
the builder MANUFACTURING a negative — MISO ``oil`` 2022 read raw EIA-923
+0.3836 TWh and came out -0.0731 because the dual-fuel re-attribution moved only
positive rows (``docs/FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md``).

So every negative ``classFull`` entry in a committed part must be ONE of:

* ``MEASURED_NEGATIVE`` — a pass-through of a negative raw EIA-923 class total,
  re-verified against ``data/raw`` by the ``fulldata`` test below (sign equal,
  magnitude within the vintage reconcile's reach);
* ``KNOWN_DEFECT`` — a named, routed defect, carried as ``xfail(strict=True)``
  so the part turns RED the moment its owner refreshes it clean and the entry
  has to be deleted. Never a place to park a new negative.

An unlisted negative fails with the instruction to classify it, which is the
whole point: a lane that finds one must show it is measured before it scores.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest
from tests.helpers import REPO_ROOT, requires_raw

BENCH = REPO_ROOT / "frontend" / "data" / "backcast" / "bench"
GEN_923 = (
    REPO_ROOT
    / "data"
    / "raw"
    / "_processed-legacy"
    / "eia923_monthly_generation.parquet"
)

#: (ISO, year, class) -> the measured cause. Re-verified by the fulldata test.
MEASURED_NEGATIVE: dict[tuple[str, int, str], str] = {
    (
        "NEISO",
        2020,
        "COAL_PRB",
    ): "Bridgeport Station (568) ST/SUB -19,082 MWh: an idle coal unit's station service",
    (
        "SOCO",
        2023,
        "OTHER",
    ): "pumped storage PS/WAT -0.647 TWh net (pumping exceeds generation)",
    ("SOCO", 2024, "OTHER"): "pumped storage PS/WAT net pumping",
    (
        "SOCO",
        2025,
        "OTHER",
    ): "pumped storage PS/WAT -0.695 TWh net (pumping exceeds generation)",
}

#: (ISO, year) -> reason. Each is ROUTED, not absorbed, and turns red when fixed.
KNOWN_DEFECT: dict[tuple[str, int], str] = {
    ("SPP", 2022): (
        "oil -0.2482: Larned (1299) IC/DFO books -311,800 MWh in 2022 against "
        "-235..-408 MWh in every other year (kWh entered as MWh), plus the stale "
        "part's one-sided re-attribution. Routed: the EIA-923 respondent-error "
        "screen (miso-267 FINDING §5) and SPP's own refresh."
    ),
    ("MISO", 2022): (
        "oil -0.0480 after the miso-267 repair: Granite Falls 2 (7977) IC/DFO books "
        "-107,000 MWh in 2022 against -78..-98 MWh in every other year (kWh entered "
        "as MWh). Routed: the EIA-923 respondent-error screen (miso-267 FINDING §5)."
    ),
}


def _parts() -> list[tuple[str, int, Path]]:
    if not BENCH.exists():
        return []
    return [
        (p.parent.name, int(p.name.split(".")[0]), p)
        for p in sorted(BENCH.glob("*/*.json.gz"))
    ]


def _negatives(path: Path) -> dict[str, float]:
    part = json.loads(gzip.decompress(path.read_bytes()))
    return {
        k: v
        for k, v in (part["bench"].get("classFull") or {}).items()
        if isinstance(v, (int, float)) and v < 0
    }


def _params():
    out = []
    for iso, year, path in _parts():
        marks = []
        if (iso, year) in KNOWN_DEFECT:
            marks.append(
                pytest.mark.xfail(strict=True, reason=KNOWN_DEFECT[(iso, year)])
            )
        out.append(pytest.param(iso, year, path, marks=marks, id=f"{iso}-{year}"))
    return out


@pytest.mark.parametrize("iso, year, path", _params())
def test_no_manufactured_negative_actual(iso, year, path):
    """Every negative classFull entry is a verified measured negative."""
    unexplained = {
        k: v
        for k, v in _negatives(path).items()
        if (iso, year, k) not in MEASURED_NEGATIVE
    }
    assert not unexplained, (
        f"{iso} {year}: classFull carries NEGATIVE actual(s) {unexplained} that are not "
        "verified measured negatives. Net generation CAN be negative (station service, "
        "pumping) — if the raw EIA-923 class total is itself negative and the part passes "
        "it through, add it to MEASURED_NEGATIVE with its cause (the fulldata test "
        "re-verifies it). Otherwise the benchmark builder manufactured it — fix the "
        "builder, never the list."
    )


def test_measured_negative_entries_are_live():
    """A listed measured negative that no committed part carries is dead weight."""
    live = {(iso, year, k) for iso, year, p in _parts() for k in _negatives(p)}
    stale = sorted(set(MEASURED_NEGATIVE) - live)
    assert not stale, f"MEASURED_NEGATIVE entries no part carries any more: {stale}"


@requires_raw(GEN_923)
@pytest.mark.integration
@pytest.mark.parametrize("key", sorted(MEASURED_NEGATIVE))
def test_measured_negative_is_the_raw_measurement(key):
    """Re-verify a listed negative against the raw EIA-923 class total.

    The raw total must be negative itself, and the committed value must sit within
    the combined-fossil vintage reconcile's reach of it (a common positive scale
    factor, so the sign is preserved and the magnitude moves only by that factor).
    """
    import importlib.util

    iso, year, klass = key
    spec = importlib.util.spec_from_file_location(
        "rcf_sign", str(REPO_ROOT / "scripts" / "run_calibration_full.py")
    )
    rcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcf)
    f = rcf._eia923_frame(year, rcf.load_monthly_generation(), iso)
    raw = float(f.loc[f["klass"] == klass, "annual_mwh"].sum()) / 1e6
    committed = _negatives(BENCH / iso / f"{year}.json.gz")[klass]
    assert raw < 0.0, f"{key}: raw EIA-923 class total {raw:.4f} TWh is NOT negative"
    assert abs(committed - raw) <= 0.1 * abs(raw) + 1e-3, (
        f"{key}: committed {committed:.4f} TWh is not a pass-through of raw {raw:.4f}"
    )
