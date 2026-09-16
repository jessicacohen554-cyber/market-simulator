"""Hydraulic-cascade coupling rows for the dispatch LP (NWPP-36, owner ruling N3).

The Columbia mainstem and the lower Snake are one hydraulic chain: water
turbined or spilled at an upstream project arrives at the next project a
measured lag ``τ`` later and, less what the downstream pond can hold, must be
turbined or spilled there in turn. The existing hydro budget family
(``rows._build_hydro_rows``) caps each plant's MONTHLY energy independently
and so lets a run-of-river plant concentrate a month's water into any hours it
likes; this family adds the hourly water balance that bounds WHEN a coupled
plant's water can be turbined.

**The coupling redistributes when energy is produced. It never changes how much
per month** (rule 19 ``[R-ONE-MECH]``): the monthly cap stays the sole
energy-quantity mechanism, no generation column is added, and every row here
is feasible at zero generation (spill is unbounded above), so the family can
never force a plant's monthly total off its budget. Specification:
``docs/handoffs/PRECOMMIT-nwpp-36-2026-09-16.md`` §3.

Units: water in kcfs (flow) and kcfs·h (volume), the CROHMS native unit; the
existing generation columns enter through a measured, month-varying
water-to-energy ratio ``η`` [MWh per kcfs·h] so ``P/η`` is turbine flow.

One equality row per coupled downstream plant ``d`` and hour ``t``::

    P_d(t)/η_d(t) + S_d(t) + V_d(t) − V_d(t−1)
        − Σ_{u∈up(d)} [ P_u(t−τ_ud)/η_u(t−τ_ud) + S_u(t−τ_ud) ]
        = I_d(t) + Σ_{u∈up(d), u a head} q̄_u(t−τ_ud)

with two NEW columns per coupled plant and hour — spill ``S_d ≥ 0`` and pond
volume ``0 ≤ V_d ≤ B_d`` — laid out in the ``n_cascade`` block
:class:`~market_sim.model.lp.layout.VariableLayout` appends after the
discharge-tranche block. A chain HEAD (Grand Coulee, Dworshak) has no spill
column: a free spill at a head would be phantom water, so its measured
monthly-mean spill (or, when the head is not an LP unit that year, its
measured monthly-mean outflow) enters the right-hand side as the measured
physical input ``q̄_u``. Lags and the ``V(t−1)`` term wrap cyclically at the
horizon boundary — the house convention for storage SOC.

Rule 2 ``[R-VECTOR]``: every coefficient family is assembled from
``np.arange(T)`` with ``np.repeat`` / modular index arithmetic in one
``coo_matrix``; the only Python loop is over the O(15) links.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from market_sim.model.lp.layout import VariableLayout


@dataclass(frozen=True)
class HydroCascadeSpec:
    """LP-ready arrays for the cascade rows of one ISO-year.

    Built by :func:`market_sim.data.hydro.load_hydro_cascade` from the
    measured artifact; consumed only by the LP builders in this package.

    Attributes:
        coupled_gen_idx: ``(n_c,)`` thermal-block generator index of each
            coupled downstream plant ``d`` (the plant carrying the row and the
            ``S``/``V`` columns), in cascade-local order ``c = 0..n_c-1``.
        eta_dn: ``(n_c, T)`` water-to-energy ratio of each coupled plant in
            MWh per kcfs·h, by hour (month-varying, measured).
        pond_cap: ``(n_c,)`` operated pondage band ``B_d`` in kcfs·h.
        side_inflow: ``(n_c, T)`` measured side inflow ``I_d`` in kcfs
            arriving between ``up(d)`` and ``d`` (monthly mean, held flat).
        link_dn_local: ``(n_l,)`` cascade-local index ``c`` of each link's
            downstream plant.
        link_up_gen_idx: ``(n_l,)`` generator index of each link's upstream
            plant ``u`` (``-1`` when the upstream is a head absent from the
            LP fleet that year — its outflow then enters only through
            ``link_head_flow``).
        link_up_local: ``(n_l,)`` cascade-local index of the upstream plant
            when it is itself a coupled plant (carries an ``S`` column), else
            ``-1`` (a chain head).
        link_tau: ``(n_l,)`` integer lag in hours, measured per link.
        link_eta_up: ``(n_l, T)`` η of the upstream plant by hour (unused
            when ``link_up_gen_idx == -1``).
        link_head_flow: ``(n_l, T)`` kcfs entering the RHS for a head link —
            the head's measured monthly-mean spill when the head is an LP
            unit, its measured monthly-mean total outflow when it is not; 0
            for a non-head link.
        plant_codes: ``(n_c,)`` EIA plant ids of the coupled plants
            (diagnostics / labelling only).
    """

    coupled_gen_idx: np.ndarray
    eta_dn: np.ndarray
    pond_cap: np.ndarray
    side_inflow: np.ndarray
    link_dn_local: np.ndarray
    link_up_gen_idx: np.ndarray
    link_up_local: np.ndarray
    link_tau: np.ndarray
    link_eta_up: np.ndarray
    link_head_flow: np.ndarray
    plant_codes: np.ndarray

    @property
    def n_coupled(self) -> int:
        """Number of coupled downstream plants (rows and column pairs)."""
        return int(np.asarray(self.coupled_gen_idx).size)

    @property
    def n_links(self) -> int:
        """Number of links (upstream → downstream pairs)."""
        return int(np.asarray(self.link_dn_local).size)

    def validate(self, n_gen: int, T: int) -> None:
        """Raise ``ValueError`` on any shape / index inconsistency."""
        n_c = self.n_coupled
        n_l = self.n_links
        if np.asarray(self.eta_dn).shape != (n_c, T):
            raise ValueError(
                f"eta_dn shape {np.asarray(self.eta_dn).shape} != ({n_c}, {T})"
            )
        if np.asarray(self.side_inflow).shape != (n_c, T):
            raise ValueError(
                f"side_inflow shape {np.asarray(self.side_inflow).shape} != ({n_c}, {T})"
            )
        if np.asarray(self.pond_cap).shape != (n_c,):
            raise ValueError(
                f"pond_cap shape {np.asarray(self.pond_cap).shape} != ({n_c},)"
            )
        for name in ("link_up_gen_idx", "link_up_local", "link_tau"):
            if np.asarray(getattr(self, name)).shape != (n_l,):
                raise ValueError(f"{name} shape != ({n_l},)")
        if np.asarray(self.link_eta_up).shape != (n_l, T):
            raise ValueError(f"link_eta_up shape != ({n_l}, {T})")
        if np.asarray(self.link_head_flow).shape != (n_l, T):
            raise ValueError(f"link_head_flow shape != ({n_l}, {T})")
        cg = np.asarray(self.coupled_gen_idx, dtype=int)
        if n_c and (cg.min() < 0 or cg.max() >= n_gen):
            raise ValueError("coupled_gen_idx out of range")
        ug = np.asarray(self.link_up_gen_idx, dtype=int)
        if n_l and ug.max() >= n_gen:
            raise ValueError("link_up_gen_idx out of range")
        dl = np.asarray(self.link_dn_local, dtype=int)
        if n_l and (dl.min() < 0 or dl.max() >= n_c):
            raise ValueError("link_dn_local out of range")
        ul = np.asarray(self.link_up_local, dtype=int)
        if n_l and ul.max() >= n_c:
            raise ValueError("link_up_local out of range")
        if n_l and (np.asarray(self.link_tau, dtype=int) < 0).any():
            raise ValueError("link_tau must be non-negative")
        if (np.asarray(self.eta_dn) <= 0).any():
            raise ValueError("eta_dn must be strictly positive")
        live = ug >= 0
        if live.any() and (np.asarray(self.link_eta_up)[live] <= 0).any():
            raise ValueError("link_eta_up must be strictly positive on live links")
        if (np.asarray(self.pond_cap) < 0).any():
            raise ValueError("pond_cap must be non-negative")


def build_hydro_cascade_rows(
    layout: VariableLayout, spec: HydroCascadeSpec
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Return the cascade water-balance rows and their (equality) bounds.

    Row ``r = c * T + t`` is coupled plant ``c``'s balance in hour ``t`` (see
    the module docstring). Coefficients: ``+1/η_d(t)`` on ``P_d(t)``, ``+1`` on
    ``S_d(t)`` and ``V_d(t)``, ``−1`` on ``V_d(t−1)`` (cyclic), and for each
    link into ``d``: ``−1/η_u(t')`` on ``P_u(t')`` and ``−1`` on ``S_u(t')``
    (upstream spill column exists only for a coupled upstream), with
    ``t' = (t − τ) mod T``. The RHS is the measured side inflow plus the head
    links' measured flow, both lag-shifted.

    Args:
        layout: Variable layout; ``layout.n_cascade`` must equal
            ``2 * spec.n_coupled``.
        spec: The cascade arrays.

    Returns:
        ``(block, row_lower, row_upper)`` with ``block`` CSR of shape
        ``(n_c * T, layout.total_columns)`` and ``row_lower == row_upper``
        (equalities).
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    n_c = spec.n_coupled
    if layout.n_cascade != 2 * n_c:
        raise ValueError(
            f"layout.n_cascade ({layout.n_cascade}) != 2 * n_coupled ({2 * n_c})"
        )
    if n_c == 0:
        return (
            sp.csr_matrix((0, layout.total_columns)),
            np.zeros(0, dtype=float),
            np.zeros(0, dtype=float),
        )
    spec.validate(layout.n_gen, T)

    t = np.arange(T)  # t: hour index
    c = np.arange(n_c)  # c: cascade-local coupled-plant index
    cg = np.asarray(spec.coupled_gen_idx, dtype=int)
    eta_dn = np.asarray(spec.eta_dn, dtype=float)

    # Row index of (c, t), (n_c, T) then ravelled row-major: r = c*T + t.
    rows_ct = (c[:, None] * T + t[None, :]).ravel()

    rows_list: list[np.ndarray] = []
    cols_list: list[np.ndarray] = []
    data_list: list[np.ndarray] = []

    # +P_d(t)/η_d(t)
    rows_list.append(rows_ct)
    cols_list.append((t[None, :] * vph + layout._p_off + cg[:, None]).ravel())
    data_list.append((1.0 / eta_dn).ravel())
    # +S_d(t)
    rows_list.append(rows_ct)
    cols_list.append((t[None, :] * vph + layout._cas_s_off + c[:, None]).ravel())
    data_list.append(np.ones(n_c * T))
    # +V_d(t)
    rows_list.append(rows_ct)
    cols_list.append((t[None, :] * vph + layout._cas_v_off + c[:, None]).ravel())
    data_list.append(np.ones(n_c * T))
    # −V_d(t−1), cyclic
    t_prev = (t - 1) % T
    rows_list.append(rows_ct)
    cols_list.append((t_prev[None, :] * vph + layout._cas_v_off + c[:, None]).ravel())
    data_list.append(-np.ones(n_c * T))

    rhs = np.asarray(spec.side_inflow, dtype=float).copy()  # (n_c, T)

    # Links: loop over the O(15) links, never over hours.
    for ln in range(spec.n_links):
        d = int(spec.link_dn_local[ln])
        tau = int(spec.link_tau[ln])
        t_lag = (t - tau) % T
        row_d = d * T + t  # (T,)
        u_gen = int(spec.link_up_gen_idx[ln])
        if u_gen >= 0:
            eta_u = np.asarray(spec.link_eta_up[ln], dtype=float)  # (T,) by hour
            rows_list.append(row_d)
            cols_list.append(t_lag * vph + layout._p_off + u_gen)
            data_list.append(-1.0 / eta_u[t_lag])
        u_loc = int(spec.link_up_local[ln])
        if u_loc >= 0:
            rows_list.append(row_d)
            cols_list.append(t_lag * vph + layout._cas_s_off + u_loc)
            data_list.append(-np.ones(T))
        head_flow = np.asarray(spec.link_head_flow[ln], dtype=float)
        if head_flow.any():
            rhs[d] += head_flow[t_lag]

    block = sp.coo_matrix(
        (
            np.concatenate(data_list),
            (np.concatenate(rows_list), np.concatenate(cols_list)),
        ),
        shape=(n_c * T, layout.total_columns),
    ).tocsr()
    # Coincident entries (e.g. τ = 0 on a self-referencing layout) are summed
    # by tocsr(); the physical formulation never produces duplicates for a
    # well-formed chain, but summing is the correct semantics regardless.
    block.sum_duplicates()
    rhs_flat = rhs.ravel()
    return block, rhs_flat.copy(), rhs_flat.copy()
