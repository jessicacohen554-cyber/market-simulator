"""Typed input contracts for the shared per-year solve core.

Two frozen dataclasses:

- :class:`DispatchSpec` — the base ``dispatch_kwargs`` the LP builder consumes,
  as a typed bundle. ``to_dispatch_kwargs()`` returns exactly the dict that
  ``runner.py``'s per-year loop assembles inline today (search for
  ``dispatch_kwargs = dict(`` in ``runner.py``), key-for-key. This is an
  *assembly-side* container only — ``dispatch.py``'s signature is unchanged.
- :class:`ReserveSpec` — a typed wrapper over the dict
  ``reserve_config.build_reserve_dispatch_kwargs`` already returns.
  ``merge_into()`` reproduces the current
  ``dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))`` exactly.

Stage 1 introduces both and unit-tests them; the container is *wired* into the
shared solve core in Stage 2 (plan §6). Neither changes any solved number —
each is a faithful re-packaging of a value assembled inline today.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    import numpy as np


class _Unset:
    """Sentinel for DispatchSpec keys the caller did not assemble at all.

    ``DispatchSpec.to_dispatch_kwargs()`` OMITS a field left at ``UNSET`` —
    distinct from an explicit ``None``, which is emitted as a ``None``-valued
    key. The distinction preserves each orchestrator's exact pre-refactor key
    set: the forecast assembly never carried ``ttc_import``/``oil_*`` keys,
    while the backcast assembly always carries them (``None``-valued when the
    overlay is off). Key-for-key fidelity is the Stage-2 acceptance contract
    (plan §7.1 item 2).
    """

    def __repr__(self) -> str:  # pragma: no cover - debugging nicety
        return "<UNSET>"


UNSET: Any = _Unset()


@dataclass(frozen=True)
class DispatchSpec:
    """Frozen bundle of the base ``dispatch_kwargs`` for the LP builder.

    Each field holds the *final* value the inline assembly places under the
    matching key (e.g. ``interface_groups`` already carries the ``... or None``
    applied at the call site, ``storage_daily_cycle_hours`` the resolved
    ``24``/``None``). :meth:`to_dispatch_kwargs` returns those values keyed by
    name, so a call site can swap the inline ``dict(...)`` for
    ``DispatchSpec(...).to_dispatch_kwargs()`` with no value change.

    Field names match the ``dispatch_kwargs`` keys one-to-one; the argument list
    mirrors the inline dict in ``runner.py``'s per-year loop exactly.
    """

    # Renewable potentials (decision-variable upper bounds; rule #3).
    wind_cf: "np.ndarray"
    wind_cap: "np.ndarray"
    solar_cf: "np.ndarray"
    solar_cap: "np.ndarray"
    # Load-shed penalty = the ISO's own energy bid cap (iso_config.voll).
    voll: float
    # Zone/link topology.
    incidence: "np.ndarray"
    ttc: "np.ndarray"
    interface_groups: Any
    link_bidirectional: "np.ndarray"
    # Storage arrays.
    storage_power_cap: "np.ndarray"
    storage_energy_cap: "np.ndarray"
    storage_zone_idx: "np.ndarray"
    eta_chg: "np.ndarray"
    eta_dis: "np.ndarray"
    # Renewable marginal-cost floors.
    wind_mc: "np.ndarray"
    solar_mc: "np.ndarray"
    # Storage discharge economics.
    storage_discharge_eac: Any
    storage_discharge_cost: "np.ndarray"
    # Policy / operational.
    rps_target: Any
    storage_daily_cycle_hours: int | None
    # Conventional-hydro monthly energy budget (both None when no hydro plants).
    hydro_gen_idx: Any
    hydro_monthly_energy: Any
    # Horizon (config.hours).
    T: int
    # ---- Keys only the backcast assembly carries (Stage 2). Left at UNSET
    #      they are OMITTED from to_dispatch_kwargs(), so the forecast dict's
    #      key set is unchanged; the backcast passes them explicitly (possibly
    #      None), reproducing its always-present keys. ----
    # RPS ACP ceiling ($/MWh) — prices the ACP escape column that keeps the RPS
    # row feasible and caps its dual. UNSET (backcast, which disables the RPS)
    # is omitted from the kwargs, so the LP key set there is unchanged.
    rps_acp_price: Any = UNSET
    # Import-direction TTC bound (measured ERCOT GTC overlay); None keeps the
    # symmetric -ttc.
    ttc_import: Any = UNSET
    # ERCOT West Texas Export corridor VRE curtailment ceilings — (n_zones, T)
    # multipliers in (0,1] on the wind/solar CF upper bound (1.0 off-corridor).
    # UNSET (driver off / non-ERCOT) omits the keys, leaving the uncurtailed bound.
    wind_curtail_share: Any = UNSET
    solar_curtail_share: Any = UNSET
    # NEISO oil-burn / winter-fuel-inventory budget rows.
    oil_monthly_budget: Any = UNSET
    oil_gen_idx: Any = UNSET
    oil_month_index: Any = UNSET
    oil_gen_hour_coeff: Any = UNSET
    oil_group_index: Any = UNSET

    def to_dispatch_kwargs(self) -> dict:
        """Return the base ``dispatch_kwargs`` dict, key-for-key.

        The keys and values are exactly those the inline assembly builds, so the
        LP receives an identical mapping (fields left at ``UNSET`` are omitted
        outright — see :class:`_Unset`). This is the whole point of the
        container: byte-identical assembly, typed at the seam.
        """
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not UNSET
        }


@dataclass(frozen=True)
class ReserveSpec:
    """Typed wrapper over the reserve co-optimization ``dispatch_kwargs``.

    ``reserve_config.build_reserve_dispatch_kwargs(design)`` returns a dict whose
    key set is *conditional* on the reserve design (single- vs multi-family,
    headroom rows, online-gating, supply cap, per-generator columns). This
    wrapper holds that dict verbatim and exposes the enumerated keys as typed
    accessors, so a reader gets ``spec.reserve_supply_cap`` instead of
    ``kw.get("reserve_supply_cap")`` — while :meth:`merge_into` preserves the
    exact key set (only the keys the builder actually emitted are merged).

    No value change: this is a re-packaging of the existing dict.
    """

    # The dict ``build_reserve_dispatch_kwargs`` returned, held verbatim so the
    # conditional key set (and thus the LP) is preserved exactly.
    kwargs: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_reserve_kwargs(cls, kw: Mapping[str, Any]) -> "ReserveSpec":
        """Wrap the dict ``build_reserve_dispatch_kwargs`` returned.

        A defensive ``dict(kw)`` copy is stored so later mutation of the source
        cannot alter the wrapped contract.
        """
        return cls(dict(kw))

    def merge_into(self, dispatch_kwargs: dict) -> None:
        """Merge the wrapped reserve kwargs into ``dispatch_kwargs`` in place.

        Reproduces exactly the current
        ``dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))``: only
        the keys the builder emitted are added, so the resulting LP is
        byte-identical.
        """
        dispatch_kwargs.update(self.kwargs)

    # -- Typed accessors for the enumerated reserve keys. Each returns the
    #    wrapped value, or None when the design did not emit that key (matching
    #    ``dict.get`` semantics — an absent key is not injected into the LP). --

    @property
    def reserve_requirement(self) -> Any:
        """Per-family (or squeezed ``(T,)``) reserve requirement, or None."""
        return self.kwargs.get("reserve_requirement")

    @property
    def reserve_eligible(self) -> Any:
        """Reserve-eligible generator mask, or None."""
        return self.kwargs.get("reserve_eligible")

    @property
    def ordc_penalties(self) -> Any:
        """Concatenated ORDC step penalties, or None."""
        return self.kwargs.get("ordc_penalties")

    @property
    def ordc_step_widths(self) -> Any:
        """Concatenated ORDC step widths, or None."""
        return self.kwargs.get("ordc_step_widths")

    @property
    def reserve_supply_cap(self) -> Any:
        """Reserve supply cap (ERCOT RTOLCAP / PJM deliverable ramp), or None."""
        return self.kwargs.get("reserve_supply_cap")

    @property
    def reserve_online_gated(self) -> Any:
        """Online-gated reserve mask (NYISO synchronised / PJM), or None."""
        return self.kwargs.get("reserve_online_gated")

    @property
    def reserve_online_rho(self) -> Any:
        """Online-gating headroom fraction ``ρ``, or None."""
        return self.kwargs.get("reserve_online_rho")

    @property
    def reserve_headroom_eligible(self) -> Any:
        """Headroom-row eligibility (ERCOT multiproduct cascade), or None."""
        return self.kwargs.get("reserve_headroom_eligible")

    @property
    def reserve_headroom_products(self) -> Any:
        """Headroom-row product indices, or None."""
        return self.kwargs.get("reserve_headroom_products")

    @property
    def reserve_headroom_extra_cap(self) -> Any:
        """Extra headroom capacity per product, or None."""
        return self.kwargs.get("reserve_headroom_extra_cap")

    @property
    def reserve_pergen_gen_idx(self) -> Any:
        """Per-generator reserve column generator indices, or None."""
        return self.kwargs.get("reserve_pergen_gen_idx")

    @property
    def reserve_pergen_ramp10(self) -> Any:
        """Per-generator 10-minute ramp capability, or None."""
        return self.kwargs.get("reserve_pergen_ramp10")

    @property
    def reserve_pergen_col(self) -> Any:
        """Per-generator reserve column layout, or None."""
        return self.kwargs.get("reserve_pergen_col")

    @property
    def reserve_posture_pools(self) -> Any:
        """Commitment-posture pool indices (MISO posture lever), or None."""
        return self.kwargs.get("reserve_posture_pools")

    @property
    def reserve_posture_mlf(self) -> Any:
        """Posture pools' min-stable-when-online fractions, or None."""
        return self.kwargs.get("reserve_posture_mlf")

    @property
    def reserve_posture_startup(self) -> Any:
        """Posture pools' startup costs ($/MW per start), or None."""
        return self.kwargs.get("reserve_posture_startup")

    @property
    def reserve_balance_zone_mask(self) -> Any:
        """Multi-family reserve balance zone mask, or None."""
        return self.kwargs.get("reserve_balance_zone_mask")

    @property
    def reserve_balance_ordc_counts(self) -> Any:
        """Per-family ORDC step counts, or None."""
        return self.kwargs.get("reserve_balance_ordc_counts")

    @property
    def reserve_balance_class(self) -> Any:
        """Per-family reserve class, or None."""
        return self.kwargs.get("reserve_balance_class")

    @property
    def reserve_storage(self) -> Any:
        """Storage reserve-eligibility flag, or None."""
        return self.kwargs.get("reserve_storage")

    @property
    def reserve_storage_duration_h(self) -> Any:
        """Per-product storage-reserve durations (ERCOT), or None."""
        return self.kwargs.get("reserve_storage_duration_h")
