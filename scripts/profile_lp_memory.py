"""Peak-memory profiler for the dispatch LP build (construction vs solve).

Stage-6 orchestrator gate blocker (G-40): the MISO/PJM keeper LPs OOM on the
standard ~16 GB container. The OOM-killer log
(``Killed ... anon-rss:15933104kB ... during reserve-column construction``)
points at sparse-matrix *assembly*, not the HiGHS solve. This harness quantifies
that: it reports peak anon-RSS with a construction-vs-solve phase split and
per-block column/nnz counts (energy, reserve, storage, flow), so the reserve
block's marginal GB is measured rather than guessed.

Two modes:

* ``--keeper <name>``: solve a real keeper config end to end (needs the ISO's
  curated ``data/clean`` partitions and enough RAM — the very thing that OOMs;
  use on a box that can hold it, or to capture the partial peak before the kill).
* ``--synthetic-reserve``: build ONLY the per-generator reserve block
  (:func:`dispatch._build_reserve_rows_pergen`) at MISO/PJM-representative
  dimensions, with no data dependency. This isolates the exact phase the OOM log
  blames and is runnable on the constrained box, so the assembly-optimization
  win (Step 2) can be measured old-vs-new without a full keeper solve.

RSS is sampled two ways and both reported: a background thread polling
``/proc/self/status`` ``VmRSS`` (peak observed live, so a value survives even if
the process is later OOM-killed mid-phase) and ``resource.getrusage`` ``VmHWM``
high-water mark. Numbers are anon-RSS in GiB.

Usage:
    python scripts/profile_lp_memory.py --synthetic-reserve --iso MISO
    python scripts/profile_lp_memory.py --synthetic-reserve --iso PJM
    python scripts/profile_lp_memory.py --keeper miso-41-ct-evening   # big box
"""

from __future__ import annotations

import argparse
import gc
import resource
import threading
import time
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp


# ---------------------------------------------------------------------------
# RSS sampling
# ---------------------------------------------------------------------------
def _vmrss_kb() -> int:
    """Current anon-RSS in KiB from ``/proc/self/status`` (VmRSS)."""
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS"):
                return int(line.split()[1])
    return 0


def _vmhwm_gib() -> float:
    """Process high-water RSS in GiB (getrusage ru_maxrss, KiB on Linux)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


class RSSSampler:
    """Background thread polling VmRSS; records the peak seen while running."""

    def __init__(self, interval_s: float = 0.01) -> None:
        self.interval_s = interval_s
        self.peak_kb = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "RSSSampler":
        self.peak_kb = _vmrss_kb()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        while not self._stop.is_set():
            self.peak_kb = max(self.peak_kb, _vmrss_kb())
            time.sleep(self.interval_s)

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self.peak_kb = max(self.peak_kb, _vmrss_kb())

    @property
    def peak_gib(self) -> float:
        return self.peak_kb / (1024.0 * 1024.0)


# ---------------------------------------------------------------------------
# Synthetic MISO/PJM-representative reserve block
# ---------------------------------------------------------------------------
@dataclass
class ReserveCase:
    """Dimensions of a per-generator reserve co-opt block."""

    iso: str
    n_gen: int  # reserve-eligible thermal units (joint-row P terms)
    n_zones: int
    n_classes: int  # fuel classes → R columns = up to n_zones * n_classes
    T: int = 8760

    @staticmethod
    def preset(iso: str, T: int = 8760) -> "ReserveCase":
        """Representative dims from the keeper configs / reserve-config docs.

        MISO miso-41: 6 load zones, per-(zone,fuel-class) R columns (~30-40/hr,
        reserve_config.py:1446), joint rows carry one P term per reserve-eligible
        unit — the plant-level fleet is ~1.5-3k thermal units. PJM pjm-77: 8
        zones, pjm_reserve_pergen=false (zone-aggregate), but the plant-level
        8-zone energy fleet is itself ~2.5-4k units. These bracket the observed
        ~16 GB transient; tune with --n-gen for sensitivity.
        """
        iso = iso.upper()
        if iso == "MISO":
            return ReserveCase(iso, n_gen=2400, n_zones=6, n_classes=5, T=T)
        if iso == "PJM":
            return ReserveCase(iso, n_gen=3200, n_zones=8, n_classes=5, T=T)
        return ReserveCase(iso, n_gen=1500, n_zones=5, n_classes=5, T=T)


def _synth_fleet_and_design(case: ReserveCase, rng: np.random.Generator):
    """Build a FleetArrays + per-gen reserve design at the case's dimensions.

    Mirrors reserve_config._miso branch: R column per unique (zone, fuel), one
    joint P term per eligible generator. Availability is a realistic (n_gen, T)
    dense array (its memory is part of what the real build holds), so the profile
    reflects the true joint-block nnz = T * (n_gen + n_r).
    """
    from market_sim.data.fleet import FleetArrays

    n_gen = case.n_gen
    T = case.T
    zone_idx = rng.integers(0, case.n_zones, size=n_gen).astype(int)
    fuel_idx = rng.integers(0, case.n_classes, size=n_gen).astype(int)
    pmax = rng.uniform(30.0, 800.0, size=n_gen)
    # (n_gen, T) availability — mostly 1.0 with sparse derates, like CAMPD.
    availability = np.ones((n_gen, T), dtype=float)
    ramp10 = pmax * 0.3  # RAMP10_FRAC-ish; all eligible & > 0

    fa = FleetArrays.__new__(FleetArrays)
    fa.pmax = pmax
    fa.availability = availability
    fa.zone_idx = zone_idx
    fa.fuel_type_idx = fuel_idx
    fa.ramp10 = ramp10
    fa.unit_ids = [str(i) for i in range(n_gen)]  # fleet.n_gen == len(unit_ids)

    # Per-(zone, fuel) R columns — the MISO aggregate tier.
    gidx = np.arange(n_gen)
    keys = np.stack([zone_idx, fuel_idx], axis=1)
    _, pergen_col = np.unique(keys, axis=0, return_inverse=True)
    n_r = int(pergen_col.max()) + 1
    # Single system-wide balance family (keeps the profile on the joint block,
    # which is the nnz driver; add a zonal mask via --families for sensitivity).
    return fa, gidx, pergen_col.astype(int), n_r


def _layout_for(case: ReserveCase, n_r: int, n_storage: int = 0):
    """A VariableLayout carrying the reserve columns for the synthetic case."""
    from market_sim.model.dispatch import VariableLayout

    # Minimal but representative column set (energy P, per-zone W/S/slack/dump,
    # reserve). Storage adds a SOC block so the outer assembly is multi-block
    # (energy | soc | reserve) — the real ISO structure whose pairwise-vstack
    # chain the free-concat targets.
    return VariableLayout(
        n_gen=case.n_gen,
        n_zones=case.n_zones,
        n_storage=n_storage,
        n_links=0,
        T=case.T,
        n_reserve=n_r,
        n_reserve_classes=1,
        n_ordc_steps=3,
    )


def profile_synthetic_reserve(case: ReserveCase, seed: int = 0) -> dict:
    """Build the per-gen reserve block; report peak RSS + per-block nnz."""
    from market_sim.model.dispatch import _build_reserve_rows_pergen

    rng = np.random.default_rng(seed)
    fa, gidx, pergen_col, n_r = _synth_fleet_and_design(case, rng)
    layout = _layout_for(case, n_r)
    req = np.full(case.T, 1500.0)

    gc.collect()
    base_kb = _vmrss_kb()
    t0 = time.perf_counter()
    with RSSSampler() as s:
        block, lo, hi = _build_reserve_rows_pergen(
            layout, fa, req, gidx, pergen_col=pergen_col
        )
        block = block.tocsr()
        block.sum_duplicates()
        block.sort_indices()
    build_s = time.perf_counter() - t0

    # Per-block accounting: joint = n_r*T rows, balance = 1*T rows.
    joint_rows = n_r * case.T
    balance_rows = 1 * case.T
    return {
        "iso": case.iso,
        "n_gen": case.n_gen,
        "n_zones": case.n_zones,
        "n_r": n_r,
        "T": case.T,
        "block_rows": int(block.shape[0]),
        "block_cols": int(block.shape[1]),
        "block_nnz": int(block.nnz),
        "joint_rows": int(joint_rows),
        "balance_rows": int(balance_rows),
        "indices_dtype": str(block.indices.dtype),
        "indptr_dtype": str(block.indptr.dtype),
        "build_s": build_s,
        "base_rss_gib": base_kb / (1024.0 * 1024.0),
        "peak_rss_gib": s.peak_gib,
        "delta_rss_gib": (s.peak_kb - base_kb) / (1024.0 * 1024.0),
        "vmhwm_gib": _vmhwm_gib(),
        "csr_hash": _csr_hash(block),
    }


def profile_full_build(case: ReserveCase, seed: int = 0) -> dict:
    """Drive the real ``build_constraints`` (energy balance ± reserve vstack).

    Measures where the peak actually is: the reserve-block construction plus the
    final ``A = sp.vstack([A_energy, res_block])`` copy. Two builds — energy-only
    and energy+reserve — isolate the reserve block's *marginal* contribution to
    peak RSS through the real assembly path.
    """
    from market_sim.model.dispatch import build_constraints

    rng = np.random.default_rng(seed)
    fa, gidx, pergen_col, n_r = _synth_fleet_and_design(case, rng)
    demand = rng.uniform(1000.0, 5000.0, size=(case.n_zones, case.T))
    req = np.full(case.T, 1500.0)
    # Storage → a SOC block between energy and reserve, so the outer assembly is
    # multi-block (the real ISO structure). ~8% of the fleet as storage units.
    n_storage = max(1, case.n_gen // 12)
    storage_zone_idx = rng.integers(0, case.n_zones, size=n_storage).astype(int)
    eta = np.full(n_storage, 0.9)

    layout_e = _layout_for(case, 0, n_storage=n_storage)  # energy+soc, no reserve
    gc.collect()
    with RSSSampler() as s_e:
        A_e = build_constraints(
            layout_e,
            fa,
            demand,
            incidence=None,
            storage_zone_idx=storage_zone_idx,
            eta_chg=eta,
            eta_dis=eta,
        )[0]
        e_nnz = int(A_e.nnz)
        del A_e
        gc.collect()
    energy_peak = s_e.peak_gib

    layout_r = _layout_for(case, n_r, n_storage=n_storage)  # energy+soc+reserve
    gc.collect()
    with RSSSampler() as s_r:
        A_r = build_constraints(
            layout_r,
            fa,
            demand,
            incidence=None,
            storage_zone_idx=storage_zone_idx,
            eta_chg=eta,
            eta_dis=eta,
            reserve_requirement=req,
            reserve_pergen_gen_idx=gidx,
            reserve_pergen_col=pergen_col,
        )[0]
        full_nnz = int(A_r.nnz)
        full_hash = _csr_hash(A_r)
        del A_r
        gc.collect()
    full_peak = s_r.peak_gib

    return {
        "iso": case.iso,
        "n_gen": case.n_gen,
        "n_zones": case.n_zones,
        "n_r": n_r,
        "T": case.T,
        "energy_nnz": e_nnz,
        "full_nnz": full_nnz,
        "energy_peak_gib": energy_peak,
        "full_peak_gib": full_peak,
        "reserve_marginal_gib": full_peak - energy_peak,
        "full_csr_hash": full_hash,
        "vmhwm_gib": _vmhwm_gib(),
    }


def _csr_hash(m: sp.csr_matrix) -> str:
    """Stable hash of a canonicalized CSR's (data, indices, indptr).

    The byte-identity gate: two builds of the same logical matrix hash equal iff
    their canonical CSR bytes match. Canonicalize first so construction order
    can't spuriously differ.
    """
    import hashlib

    m = m.tocsr()
    m.sum_duplicates()
    m.sort_indices()
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(m.data, dtype=np.float64).tobytes())
    h.update(np.ascontiguousarray(m.indices, dtype=np.int64).tobytes())
    h.update(np.ascontiguousarray(m.indptr, dtype=np.int64).tobytes())
    h.update(np.asarray(m.shape, dtype=np.int64).tobytes())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Keeper mode (full build+solve; needs data + RAM)
# ---------------------------------------------------------------------------
def profile_keeper(name: str) -> dict:
    """Solve a keeper config with MARKET_SIM_MEM_DEBUG on; report peak RSS.

    Relies on dispatch.py's built-in ``_rss`` checkpoints (MARKET_SIM_MEM_DEBUG=1)
    for the construction/solve phase split in the log, plus this harness's peak
    sampler for the headline anon-RSS. Requires the ISO's data/clean partitions.
    """
    import os

    os.environ["MARKET_SIM_MEM_DEBUG"] = "1"
    raise SystemExit(
        "keeper mode needs the ISO's data/clean partitions (absent in this "
        "container) and >16 GB to complete for MISO/PJM. Run on a provisioned "
        "box: MARKET_SIM_MEM_DEBUG=1 python scripts/run_calibration_full.py "
        f"--keeper {name} ... and read the MEM checkpoints, or use "
        "--synthetic-reserve here."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--synthetic-reserve", action="store_true")
    ap.add_argument("--full-build", action="store_true")
    ap.add_argument("--keeper", type=str, default=None)
    ap.add_argument("--iso", type=str, default="MISO")
    ap.add_argument(
        "--n-gen", type=int, default=None, help="override eligible gen count"
    )
    ap.add_argument("--hours", type=int, default=8760)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.keeper:
        print(profile_keeper(args.keeper))
        return

    case = ReserveCase.preset(args.iso, T=args.hours)
    if args.n_gen is not None:
        case.n_gen = args.n_gen

    if args.full_build:
        r = profile_full_build(case, seed=args.seed)
        print(
            f"\n=== full build (energy ± reserve vstack), {r['iso']} synthetic "
            f"(n_gen={r['n_gen']}, n_zones={r['n_zones']}, n_r={r['n_r']}, "
            f"T={r['T']}) ==="
        )
        print(
            f"  energy-only:   {r['energy_nnz']:,} nnz, peak {r['energy_peak_gib']:.2f} GiB"
        )
        print(
            f"  energy+reserve:{r['full_nnz']:,} nnz, peak {r['full_peak_gib']:.2f} GiB"
        )
        print(f"  reserve marginal to peak: {r['reserve_marginal_gib']:.2f} GiB")
        print(
            f"  full-A CSR hash: {r['full_csr_hash']}   VmHWM {r['vmhwm_gib']:.2f} GiB"
        )
        return

    r = profile_synthetic_reserve(case, seed=args.seed)
    print(
        f"\n=== per-gen reserve block, {r['iso']} synthetic "
        f"(n_gen={r['n_gen']}, n_zones={r['n_zones']}, n_r={r['n_r']}, "
        f"T={r['T']}) ==="
    )
    print(
        f"  block: {r['block_rows']:,} rows x {r['block_cols']:,} cols, "
        f"{r['block_nnz']:,} nnz  (idx dtype {r['indices_dtype']})"
    )
    print(f"  joint rows: {r['joint_rows']:,}   balance rows: {r['balance_rows']:,}")
    print(f"  build: {r['build_s']:.2f}s")
    print(
        f"  RSS: base {r['base_rss_gib']:.2f} GiB -> peak {r['peak_rss_gib']:.2f} "
        f"GiB (Δ {r['delta_rss_gib']:.2f} GiB), VmHWM {r['vmhwm_gib']:.2f} GiB"
    )
    print(f"  CSR hash: {r['csr_hash']}")


if __name__ == "__main__":
    main()
