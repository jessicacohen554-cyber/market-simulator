"""LP variable layout and shared sparse helpers for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7): the flat-column :class:`VariableLayout` bookkeeping plus the zone
membership maps and the free-column CSR stacker shared by the energy-balance,
reserve, and bounds builders. Pure code motion — every def is byte-identical
to its pre-split ``dispatch.py`` source.
"""

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.fleet import FleetArrays


@dataclass(frozen=True)
class VariableLayout:
    """Maps dispatch decision variables to flat LP column indices.

    Decision variables are grouped into per-hour blocks laid out
    contiguously across ``T`` hours. Within each hour the block order is:
    thermal generation, wind, solar, storage charge, storage discharge,
    storage state-of-charge, transmission flow, per-zone load slack,
    then per-zone overgeneration dump.
    """

    n_gen: int
    n_zones: int
    n_storage: int
    n_links: int
    T: int = HOURS_PER_YEAR
    # Energy+reserve co-optimization columns, appended after the dump block so
    # every existing offset is unchanged. Both 0 (the default) leave
    # ``vars_per_hour`` and the whole layout byte-identical to the energy-only
    # LP. ``n_reserve`` is one upward-reserve variable per thermal generator
    # (R[g,t], eligibility enforced by its upper bound); ``n_ordc_steps`` is the
    # number of reserve-demand-curve shortfall variables per hour (the ORDC
    # steps that price a reserve shortfall, system-wide).
    #
    # Reserve is tracked per ZONE and per reserve *class*: ``n_reserve ==
    # n_reserve_classes * n_zones``, laid out class-major (R[c, z, t] at
    # ``_reserve_off + c*n_zones + z``). A reserve class is a distinct
    # eligibility tier — NYISO splits the full dispatchable fleet (30-minute
    # products) from the quick-start subset (10-minute products: gas-CT/oil that
    # can synchronize within 10 min), so a 10-minute reserve requirement cannot
    # be met by slow combined-cycle headroom. ERCOT/PJM run a single class
    # (``n_reserve_classes == 1``), byte-identical to the legacy per-zone layout.
    n_reserve: int = 0
    n_reserve_classes: int = 1
    n_ordc_steps: int = 0
    # Explicit per-zone storage-reserve columns RS[c, z, t] for the ERCOT
    # endogenous-storage DURATION GATE (config.ercot_storage_as_duration_gate).
    # When active, storage's upward AS is a distinct decision variable per
    # reserve class c and zone z (``n_storage_reserve == n_reserve_classes *
    # n_zones``, class-major at ``_storage_reserve_off + c*n_zones + z``) instead
    # of being pooled into the thermal shared-headroom rows, so the LP-linear
    # duration gate ``Σ_c dur_c·RS[c,z] ≤ Σ_{s∈z} SOC[s]`` can bound it by stored
    # energy. Appended AFTER the ORDC block so every existing offset is
    # unchanged; 0 (default) leaves the layout byte-identical.
    n_storage_reserve: int = 0
    # Commitment-posture columns (MISO miso_commitment_posture, design note
    # §A): per POSTURED pergen pool p, an online-capacity variable U[p,t] and
    # a startup variable SU[p,t] ≥ U[p,t] − U[p,t−1] (cyclic). Appended AFTER
    # the storage-reserve block so every existing offset is unchanged;
    # ``n_posture`` = the postured (non-fast-start) pool count, 0 (default)
    # leaves the layout byte-identical.
    n_posture: int = 0
    # RPS Alternative-Compliance-Payment (ACP) escape columns. One non-negative
    # variable per compliance region per hour (``n_rec_acp`` == K, region-major
    # within the hour block), each carrying a ``+1`` coefficient in its own
    # annual RPS/clean row and a cost of that region's ACP price ($/MWh) in the
    # objective. It represents the real-market ACP: an LSE short of RECs pays
    # the ACP rate rather than physically failing the standard, so no RPS row
    # is ever infeasible and each row's dual (that region's REC price) is
    # capped at its own ACP. The legacy single ISO-wide row is the K == 1 case
    # (byte-identical); per-state compliance regions (FFR-7B Arm 2, MISO) carry
    # K > 1. Appended AFTER the posture block so every existing offset is
    # unchanged; 0 (the default — set only when an ACP price accompanies an
    # active RPS target) leaves the layout byte-identical to the
    # hard-constraint LP.
    n_rec_acp: int = 0
    # Storage RT discharge-offer tranche columns (ERCOT
    # ercot_storage_rt_offer_surface). Each ARMED battery unit's single
    # discharge Dis[s,t] is decomposed into K priced tranches DisT[a,k,t]
    # (a = armed-battery index, k = tranche) via an equality
    # ``Dis[s,t] = Σ_k DisT[a,k,t]``, so the base Dis column keeps its exact
    # meaning (total discharge — energy balance, SOC, power cap, deployment
    # floor all untouched) and the tranches only add the measured rising
    # price ladder. ``n_dis_tranche == n_armed_batteries * K``, laid out
    # armed-major/tranche-minor at ``_dis_tranche_off + a*K + k``. Appended
    # AFTER the RPS ACP block so every existing offset is unchanged; 0 (the
    # default) leaves the layout byte-identical.
    n_dis_tranche: int = 0
    # Tranches per armed battery unit (K). Only meaningful when
    # n_dis_tranche > 0; the accessor uses it to stride armed units.
    dis_tranche_k: int = 0
    # Hydraulic-cascade coupling columns (NWPP-36, owner ruling N3,
    # config.hydro_cascade_coupling; model/lp/hydro_cascade.py). Per COUPLED
    # downstream plant c, a spill column S[c,t] (kcfs, water routed past the
    # turbines) and a pond-volume column V[c,t] (kcfs·h above the bottom of the
    # operated band). ``n_cascade == 2 * n_coupled``, laid out spill-block then
    # volume-block (S at ``_cas_s_off + c``, V at ``_cas_v_off + c``). Appended
    # AFTER the discharge-tranche block so every existing offset is unchanged;
    # 0 (the default) leaves the layout byte-identical.
    n_cascade: int = 0

    @property
    def vars_per_hour(self) -> int:
        """Return the number of decision variables in a single hour block."""
        return (
            self.n_gen
            + 4 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_reserve
            + self.n_ordc_steps
            + self.n_storage_reserve
            + 2 * self.n_posture
            + self.n_rec_acp
            + self.n_dis_tranche
            + self.n_cascade
        )

    @property
    def total_columns(self) -> int:
        """Return the total LP column count across all hours."""
        return self.vars_per_hour * self.T

    @property
    def _p_off(self) -> int:
        """Per-hour offset of the thermal generation block."""
        return 0

    @property
    def _w_off(self) -> int:
        """Per-hour offset of the wind generation block."""
        return self.n_gen

    @property
    def _s_off(self) -> int:
        """Per-hour offset of the solar generation block."""
        return self.n_gen + self.n_zones

    @property
    def _chg_off(self) -> int:
        """Per-hour offset of the storage charge block."""
        return self.n_gen + 2 * self.n_zones

    @property
    def _dis_off(self) -> int:
        """Per-hour offset of the storage discharge block."""
        return self.n_gen + 2 * self.n_zones + self.n_storage

    @property
    def _soc_off(self) -> int:
        """Per-hour offset of the storage state-of-charge block."""
        return self.n_gen + 2 * self.n_zones + 2 * self.n_storage

    @property
    def _flow_off(self) -> int:
        """Per-hour offset of the transmission flow block."""
        return self.n_gen + 2 * self.n_zones + 3 * self.n_storage

    @property
    def _slack_off(self) -> int:
        """Per-hour offset of the per-zone load slack block."""
        return self.n_gen + 2 * self.n_zones + 3 * self.n_storage + self.n_links

    @property
    def _dump_off(self) -> int:
        """Per-hour offset of the per-zone overgeneration dump block."""
        return (
            self.n_gen
            + 2 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_zones
        )

    @property
    def _reserve_off(self) -> int:
        """Per-hour offset of the upward-reserve block (co-opt only)."""
        return self._dump_off + self.n_zones

    @property
    def _ordc_off(self) -> int:
        """Per-hour offset of the ORDC shortfall block (co-opt only)."""
        return self._reserve_off + self.n_reserve

    @property
    def _storage_reserve_off(self) -> int:
        """Per-hour offset of the storage-reserve block (duration gate only)."""
        return self._ordc_off + self.n_ordc_steps

    @property
    def _posture_u_off(self) -> int:
        """Per-hour offset of the posture online-capacity block (U[p,t])."""
        return self._storage_reserve_off + self.n_storage_reserve

    @property
    def _posture_su_off(self) -> int:
        """Per-hour offset of the posture startup block (SU[p,t])."""
        return self._posture_u_off + self.n_posture

    @property
    def _rec_acp_off(self) -> int:
        """Per-hour offset of the RPS ACP escape columns (RPS only)."""
        return self._posture_su_off + self.n_posture

    @property
    def _dis_tranche_off(self) -> int:
        """Per-hour offset of the storage discharge-tranche block (ERCOT arm)."""
        return self._rec_acp_off + self.n_rec_acp

    @property
    def _cas_s_off(self) -> int:
        """Per-hour offset of the cascade spill block (S[c,t]; NWPP-36)."""
        return self._dis_tranche_off + self.n_dis_tranche

    @property
    def _cas_v_off(self) -> int:
        """Per-hour offset of the cascade pond-volume block (V[c,t]; NWPP-36)."""
        return self._cas_s_off + self.n_cascade // 2

    def cas_s_col(self, c: int, t: int) -> int:
        """Return the spill column of coupled cascade plant ``c`` in hour ``t``."""
        return t * self.vars_per_hour + self._cas_s_off + c

    def cas_v_col(self, c: int, t: int) -> int:
        """Return the pond-volume column of coupled cascade plant ``c`` in hour ``t``."""
        return t * self.vars_per_hour + self._cas_v_off + c

    def p_col(self, g: int, t: int) -> int:
        """Return the column index of thermal generator ``g`` in hour ``t``."""
        return t * self.vars_per_hour + self._p_off + g

    def w_col(self, z: int, t: int) -> int:
        """Return the column index of wind in zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._w_off + z

    def s_col(self, z: int, t: int) -> int:
        """Return the column index of solar in zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._s_off + z

    def chg_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` charge in hour ``t``."""
        return t * self.vars_per_hour + self._chg_off + s

    def dis_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` discharge in hour ``t``."""
        return t * self.vars_per_hour + self._dis_off + s

    def soc_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` SOC in hour ``t``."""
        return t * self.vars_per_hour + self._soc_off + s

    def flow_col(self, ln: int, t: int) -> int:
        """Return the column index of transmission link ``ln`` in hour ``t``."""
        return t * self.vars_per_hour + self._flow_off + ln

    def slack_col(self, z: int, t: int) -> int:
        """Return the column index of load slack for zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._slack_off + z

    def dump_col(self, z: int, t: int) -> int:
        """Return the column index of dump for zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._dump_off + z

    def r_col(self, g: int, t: int) -> int:
        """Return the column index of generator ``g``'s reserve in hour ``t``."""
        return t * self.vars_per_hour + self._reserve_off + g

    def ordc_col(self, k: int, t: int) -> int:
        """Return the column index of ORDC shortfall step ``k`` in hour ``t``."""
        return t * self.vars_per_hour + self._ordc_off + k

    def sr_col(self, c: int, z: int, t: int) -> int:
        """Return the storage-reserve column of class ``c``, zone ``z``, hour ``t``."""
        return t * self.vars_per_hour + self._storage_reserve_off + c * self.n_zones + z

    def u_col(self, p: int, t: int) -> int:
        """Return the online-capacity column of postured pool ``p``, hour ``t``."""
        return t * self.vars_per_hour + self._posture_u_off + p

    def su_col(self, p: int, t: int) -> int:
        """Return the startup column of postured pool ``p``, hour ``t``."""
        return t * self.vars_per_hour + self._posture_su_off + p

    def acp_col(self, t: int, k: int = 0) -> int:
        """Return region ``k``'s RPS ACP escape column in hour ``t`` (RPS only).

        ``k`` indexes the compliance region (region-major within the hour
        block); the default ``k=0`` is the legacy single ISO-wide row.
        """
        return t * self.vars_per_hour + self._rec_acp_off + k

    def dis_tranche_col(self, a: int, k: int, t: int) -> int:
        """Return the discharge-tranche column of armed unit ``a``, tranche ``k``, hour ``t``."""
        return (
            t * self.vars_per_hour + self._dis_tranche_off + a * self.dis_tranche_k + k
        )

    def p_cols_gen(self, g: int) -> slice:
        """Return a slice selecting all ``T`` columns of thermal generator ``g``."""
        start = self._p_off + g
        return slice(start, start + self.T * self.vars_per_hour, self.vars_per_hour)


def _build_zone_gen_map(fleet: FleetArrays, n_zones: int) -> sp.csr_matrix:
    """Return the sparse ``(n_zones, n_gen)`` zone-membership matrix.

    Entry ``(z, g)`` is ``1`` when thermal generator ``g`` resides in zone
    ``z``. Multiplying this matrix by a generation vector sums each zone's
    generators into its energy-balance row.
    """
    n_gen = fleet.n_gen
    data = np.ones(n_gen, dtype=float)
    return sp.csr_matrix(
        (data, (fleet.zone_idx, np.arange(n_gen))),
        shape=(n_zones, n_gen),
    )


def _build_zone_storage_map(
    storage_zone_idx: np.ndarray | None, n_zones: int, n_storage: int
) -> sp.csr_matrix:
    """Return the sparse ``(n_zones, n_storage)`` storage-membership matrix.

    Entry ``(z, s)`` is ``1`` when storage unit ``s`` resides in zone ``z``.
    When ``storage_zone_idx`` is ``None`` all units default to zone ``0``.
    """
    if n_storage == 0:
        return sp.csr_matrix((n_zones, 0))
    if storage_zone_idx is None:
        zone_idx = np.zeros(n_storage, dtype=int)
    else:
        zone_idx = np.asarray(storage_zone_idx, dtype=int)
    return sp.csr_matrix(
        (np.ones(n_storage, dtype=float), (zone_idx, np.arange(n_storage))),
        shape=(n_zones, n_storage),
    )


def _vstack_csr_free(
    blocks: list[sp.csr_matrix | None], total_cols: int
) -> sp.csr_matrix:
    """Vertically stack CSR blocks into one, releasing each input as consumed.

    Byte-for-byte identical to ``sp.vstack(blocks, format="csr")`` — same row
    order, same canonical CSR ``(data, indices, indptr)`` and the same scipy
    index dtype — but with a much lower construction peak. ``build_constraints``
    used to grow the matrix with a pairwise chain
    (``A = sp.vstack([A, block])`` per optional block): every step allocates a
    fresh copy of the *whole* accumulated matrix, so at the final (reserve-block)
    step the transient holds ~2×(|A|+|reserve|) — the OOM-killer's
    "during reserve-column construction" peak on the plant-level MISO/PJM LPs.

    Here the output ``indptr``/``indices``/``data`` are preallocated once and
    each block's slice is copied straight in; the block is then dropped from the
    ``blocks`` list (``blocks[k] = None``) so its arrays are freed before the next
    copy. Peak ≈ |result| + |largest single block| instead of ~2×|result|. The
    logical matrix is unchanged (vertical concatenation is associative and the
    inputs are already canonical CSR), so the LP — and the Stage-6 builder-swap
    byte gate — are untouched. No Python loop over hours (rule #2): the loop is
    over the O(10) constraint blocks, not the 8760 hours.

    Args:
        blocks: CSR blocks to stack top-to-bottom (``None`` entries skipped).
            MUTATED: consumed entries are set to ``None`` to release memory.
        total_cols: column count all blocks share (``layout.total_columns``).

    Returns:
        The stacked CSR matrix.
    """
    from scipy.sparse._sputils import get_index_dtype

    present = [b for b in blocks if b is not None]
    if not present:
        return sp.csr_matrix((0, total_cols))
    if len(present) == 1:
        return present[0].tocsr()

    total_rows = sum(b.shape[0] for b in present)
    total_nnz = sum(b.nnz for b in present)
    # Match scipy.sparse.bmat/vstack's index-dtype choice exactly so the result
    # is byte-identical (int32 until nnz/cols cross 2**31, then int64).
    idx_dtype = get_index_dtype(maxval=max(total_nnz, total_cols))
    indptr = np.empty(total_rows + 1, dtype=idx_dtype)
    indices = np.empty(total_nnz, dtype=idx_dtype)
    data = np.empty(total_nnz, dtype=np.float64)
    indptr[0] = 0
    rpos = 0  # rows written so far
    npos = 0  # nnz written so far
    for k in range(len(blocks)):
        b = blocks[k]
        if b is None:
            continue
        nr = b.shape[0]
        bn = b.nnz
        # Row pointers shift by the running nnz offset; column indices and data
        # copy verbatim (same column space, already sorted per row).
        indptr[rpos + 1 : rpos + nr + 1] = b.indptr[1:] + npos
        indices[npos : npos + bn] = b.indices
        data[npos : npos + bn] = b.data
        rpos += nr
        npos += bn
        blocks[k] = None  # release this block before copying the next
    return sp.csr_matrix((data, indices, indptr), shape=(total_rows, total_cols))
