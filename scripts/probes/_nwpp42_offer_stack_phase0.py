"""nwpp-42 phase 0 (ZERO LP): the NWPP thermal offer stack, year by year.

Rebuilds the registered NWPP keeper's fleet on its OWN recipe via the
sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``) for 2023, 2024 and 2025, and dumps the
assembled marginal-cost array by class and by tranche band.

The question it answers before any solve (rule 29 ``[R-SCREEN]`` clause 0,
which survives as the practice): lane NWPP-41 §4 measured ONE year's coal
offer stack and found it bimodal -- a $4.50 must-run tranche against
$37.7-42.8 for everything else.  But the committed keeper's own
``hourly/class_band_hourly_<year>.parquet`` shows the defect is NOT flat
across the span: ``COAL_BIT`` reads +7.4 % in 2023 and -63.1 % in 2025, and
what collapses is the ECONOMIC bands (9.50 -> 1.20 TWh) while the must-run
band holds at ~6 TWh.  So the question is not "is the stack bimodal" but
"what moved between 2023 and 2024" -- delivered fuel, the assembled heat
rate, availability, or the price the stack is tested against.

Run: ``python3 scripts/probes/_nwpp42_offer_stack_phase0.py 2023 2024 2025``
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp41_span_A")


def build(year: int):
    """Assemble the keeper's own fleet for ``year`` with no LP solve."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _band_of(unit_id: str) -> str:
    """Tranche band suffix of an offer-curve unit id, else ``_none``."""
    for band in ("mustrun", "committed", "econlo", "econhi", "peak"):
        if unit_id.endswith("_" + band):
            return band
    return "_none"


def main() -> None:
    years = [int(a) for a in sys.argv[1:] if a.isdigit()] or [2023, 2024, 2025]
    for year in years:
        state = build(year)
        fa = state["fleet_arrays"]
        mc = np.asarray(state["mc_base"], dtype=float)
        pmax = np.asarray(fa.pmax, dtype=float)
        avail = np.asarray(fa.availability, dtype=float)
        groups = list(getattr(fa, "plant_group", []))
        unit_ids = list(fa.unit_ids)
        fuels = list(getattr(fa, "fuel_type", []))

        print(f"\n================ {year} ================")
        print(f"rows {len(unit_ids)}  mc shape {mc.shape}")

        rows: dict[tuple[str, str], list[int]] = defaultdict(list)
        for i, uid in enumerate(unit_ids):
            klass = groups[i] if i < len(groups) else (fuels[i] if i < len(fuels) else "?")
            rows[(str(klass), _band_of(str(uid)))].append(i)

        print(
            f"{'class':<16}{'band':<10}{'n':>4}{'pmax MW':>11}"
            f"{'avail MW':>11}{'mc mean':>10}{'mc p10':>9}{'mc p90':>9}"
        )
        for key in sorted(rows):
            klass, band = key
            idx = rows[key]
            cap = float(pmax[idx].sum())
            if cap <= 0.0:
                continue
            av = float((pmax[idx][:, None] * avail[idx]).mean(axis=1).sum()) if avail.ndim == 2 else cap
            m = mc[idx]
            w = np.repeat(pmax[idx], m.shape[1])
            flat = m.reshape(-1)
            mean = float((flat * w).sum() / w.sum())
            print(
                f"{klass:<16}{band:<10}{len(idx):>4}{cap:>11.1f}{av:>11.1f}"
                f"{mean:>10.2f}{float(np.percentile(flat, 10)):>9.2f}"
                f"{float(np.percentile(flat, 90)):>9.2f}"
            )


if __name__ == "__main__":
    main()
