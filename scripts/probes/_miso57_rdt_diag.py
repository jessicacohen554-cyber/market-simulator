"""THROWAWAY DIAGNOSTIC (never registered): 2025-only RDT flow-duration probe.

Sanity chain for the miso-57 RDT congestion-depth lane (handoff pointer):
re-solves 2025 alone with the exact miso-56 recipe (strict meta.json replay,
same RENAME/SKIP machinery as ``_miso56_measured_scarcity.py``), then dumps
the flow duration on

  - L7a Plains->South (RDT N->S, ttc 3,000 MW, one-way),
  - L7b South->Plains (RDT S->N, ttc 2,500 MW, one-way),
  - the MISO-South <-> MISO_external border link (ttc 3,000 MW, bidirectional)
    -- the suspected free wheel-through bypass around the RDT,

to establish whether the model's Midwest-South separation is ~$0 because the
RDT never saturates, or because the external-bus wheel bypasses it.

Rule-16 note: a single-year solve is permitted ONLY as a throwaway diagnostic
probe; this run must never be registered on the dashboard.

Usage: python scripts/probes/_miso57_rdt_diag.py
"""

import inspect
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso56_measured_scarcity"
OUT = ROOT / "_diag_miso57_rdt_2025"

RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
SKIP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "timestamp",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "highspy_version",
    "shared_inputs",
    "commitment",
    "commitment_screen_coal",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}


def main() -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)

    sig = inspect.signature(solve_and_persist).parameters
    kwargs = {}
    unmapped = []
    for k, v in meta.items():
        if k in SKIP:
            continue
        mapped = RENAME.get(k, k)
        if mapped in sig:
            kwargs[mapped] = v
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(f"meta.json keys not bound to solve_and_persist: {unmapped}")

    solve_and_persist(
        [2025],  # single-year THROWAWAY DIAGNOSTIC (rule 16) -- never register
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=OUT,
        note="THROWAWAY diag: miso-56 replay, 2025 only, RDT flow duration",
        **kwargs,
    )
    dump_flows()


def dump_flows() -> None:
    """Read the freshest 2025 MISO P1 dispatch parquet and print RDT flows."""
    from market_sim.results.cache import CACHE_ROOT

    cands = sorted(
        (CACHE_ROOT / "MISO").glob("*/year_2025*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    if not cands:
        raise SystemExit("no MISO 2025 dispatch parquet found")
    path = cands[-1]
    print(f"reading {path}")
    from market_sim.results.outputs import DispatchResult

    res = DispatchResult.from_parquet(path)
    # Link order = extended-topology link order (base L1-L7 + import-node links).
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.transmission import extend_with_import_node

    cfg = extend_with_import_node(get_iso_config("MISO"))
    links = [f"{ln.from_zone}->{ln.to_zone}" for ln in cfg.links]
    flows = res.flows
    if flows is None:
        raise SystemExit("no flows persisted in this parquet")
    for i, name in enumerate(
        links if len(links) == flows.shape[0] else range(flows.shape[0])
    ):
        f = flows[i]
        print(
            f"[{i}] {name}: min {f.min():.0f} max {f.max():.0f} "
            f"mean {f.mean():.0f} | h>=99% of max-abs: "
            f"{(np.abs(f) >= 0.99 * max(1.0, np.abs(f).max())).sum()}"
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "flows-only":
        dump_flows()
    else:
        main()
