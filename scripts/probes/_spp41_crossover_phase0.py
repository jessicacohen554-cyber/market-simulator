"""spp-41 phase 0 (ZERO LP): the coal<->gas merit-order crossover in SPP's own offer arrays.

Rebuilds the SPP keeper's fleet on its own recipe via the sanctioned
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``) and reports, with NO solve:

* the resolved coal passthrough series actually applied to PRB -- so an
  "armed" ``coal_prb_passthrough_sigmoid`` gate that resolves to the FLAT
  fallback is visible as such (rule 24 ``[R-REGISTRY]`` / the xiso-3
  armed-looking-but-dead shape);
* per-class capacity-weighted marginal cost from ``mc_base``, the SAME
  assembled P0 objective the LP is handed -- never a re-derivation;
* the marginal (dearest) COAL_PRB tranche versus the marginal CC_REGULAR
  tranche, the pair whose ordering IS the crossover;
* the gas price at which those two cross, computed from each row's OWN
  heat rate and its own fuel price (exact; no sweep, no solve).

Extracted per-row tables are cached as ``.npz`` under the scratchpad so a
year is built at most once.

Run: ``python3 scripts/probes/_spp41_crossover_phase0.py 2022 2023``
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CACHE = Path(
    os.environ.get(
        "SPP41_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/"
        "d1272d6d-a347-5fa8-85cd-cf88fd75dd3e/scratchpad/spp41",
    )
)

# Keeper 11 (2023-2025) and the SPP-40 holdout replay (2019-2022). The two
# metas were diffed at HEAD and carry the SAME recipe -- only provenance
# (timestamp, git_sha, basis_sha), ``years``, ``gas_prices``, the shared-input
# content hashes and the NYISO-only ``nyiso_st_gas_econ_bands_deleaked``
# differ. A year drawn from either bundle is therefore the same configuration.
BUNDLES = {
    2019: "results/calibration/spp40_holdout",
    2020: "results/calibration/spp40_holdout",
    2021: "results/calibration/spp40_holdout",
    2022: "results/calibration/spp40_holdout",
    2023: "results/calibration/spp38_span",
    2024: "results/calibration/spp38_span",
    2025: "results/calibration/spp38_span",
}


def extract(year: int) -> dict:
    """Build (or load) the per-row offer table for one year.

    Returns a dict of parallel arrays: ``unit_id``, ``klass``, ``pmax``,
    ``heat_rate``, ``vom``, ``emission_rate``, the hourly ``mc`` reduced to
    its annual mean/min/max, the row's own annual-mean fuel price, and the
    scalar metadata the crossover arithmetic needs.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"rows_{year}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=True)
        return {k: z[k] for k in z.files}

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = Path(BUNDLES[year])
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)

    fa = payload["fleet_arrays"]
    mc = np.asarray(payload["mc_base"], dtype=float)
    fuel = np.asarray(payload["fuel_prices"], dtype=float)
    if fuel.ndim == 1:
        fuel = np.broadcast_to(fuel[:, None], mc.shape)

    # Reproduce EXACTLY the klass / band construction the committed sidecars
    # use, so this probe's classes are the same objects the scorer reports:
    #   klass -- run_calibration_full._class_hourly_frame: a non-ERCOT row
    #     takes its real `plant_group`, and a COAL row is then split to its
    #     supply class by `_coal_supply_class(plant_code)`.
    #   band  -- run_calibration_full._tranche_band(unit_id), matched against
    #     that module's closed suffix vocabulary (a non-tranche column -> "").
    from scripts.run_calibration_full import (
        _coal_supply_class,
        _model_class_for_unit,
        _tranche_band,
    )

    fleet = payload["fleet"]
    fuel_type = np.array([getattr(u, "fuel_type", "") or "" for u in fleet], dtype=object)
    supply = np.array(
        [getattr(u, "coal_supply", "") or "" for u in fleet], dtype=object
    )
    klass_l = []
    for u in fleet:
        k = getattr(u, "plant_group", "") or _model_class_for_unit(
            u.unit_id, u.fuel_type, getattr(u, "efficiency_bin", "")
        )
        if k == "COAL":
            k = _coal_supply_class(int(getattr(u, "plant_code", 0) or 0), u.fuel_type)
        klass_l.append(k)
    klass = np.array(klass_l, dtype=object)
    band = np.array(
        [_tranche_band(str(u.unit_id)) for u in fleet], dtype=object
    )

    # Hourly MC for the two classes whose ordering IS the crossover, kept in
    # full so the merit-order comparison can be made HOUR BY HOUR. An annual
    # mean is not safe here: 2021's annual-mean gas is dragged to $6.33/MMBtu
    # by Winter Storm Uri against a $3.72 index, which would make the CC stack
    # look structurally dearer than it is in a normal hour.
    _key = np.array(
        [
            k in ("COAL_PRB", "CC_REGULAR") and b in ("econlo", "econ", "econhi")
            for k, b in zip(klass, band)
        ]
    )

    out = {
        "key_mask": _key,
        "key_mc_hourly": mc[_key].astype(np.float32),
        "key_fuel_hourly": np.asarray(fuel)[_key].astype(np.float32),
        "mc_p50": np.median(mc, axis=1),
        "year": np.array(year),
        "meta_gas": np.array(gas),
        "unit_id": np.asarray(fa.unit_ids, dtype=object),
        "klass": klass,
        "fuel_type": fuel_type,
        "coal_supply": supply,
        "band": band,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "heat_rate": np.asarray(fa.heat_rate, dtype=float),
        "vom": np.asarray(fa.vom, dtype=float),
        "emission_rate": np.asarray(fa.emission_rate, dtype=float),
        "mc_mean": mc.mean(axis=1),
        "mc_min": mc.min(axis=1),
        "mc_max": mc.max(axis=1),
        "fuel_mean": fuel.mean(axis=1),
        "avail_mean": np.asarray(fa.availability, dtype=float).mean(axis=1)
        if np.asarray(fa.availability).ndim == 2
        else np.asarray(fa.availability, dtype=float),
        "min_gen_mean": np.asarray(fa.min_gen, dtype=float).mean(axis=1)
        if np.asarray(fa.min_gen).ndim == 2
        else np.asarray(fa.min_gen, dtype=float),
    }
    np.savez(path, **out)
    return out


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2022, 2023]
    for y in years:
        r = extract(y)
        print(f"\n===== {y} (meta gas ${float(r['meta_gas']):.2f}/MMBtu) =====")
        ks, counts = np.unique(r["klass"].astype(str), return_counts=True)
        for k, n in zip(ks, counts):
            m = r["klass"].astype(str) == k
            print(
                f"  {k:24s} n={n:4d}  pmax={r['pmax'][m].sum():9.1f} MW  "
                f"mc_mean=${np.average(r['mc_mean'][m], weights=np.maximum(r['pmax'][m], 1e-9)):8.3f}"
            )
        print("  sample unit_ids:", list(r["unit_id"][:4]))
        print("  bands seen:", sorted(set(r["band"].astype(str)))[:12])
        print("  coal_supply seen:", sorted(set(r["coal_supply"].astype(str)))[:12])


if __name__ == "__main__":
    main()
