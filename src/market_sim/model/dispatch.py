"""Economic dispatch optimization model.

Part 1: variable layout bookkeeping and objective cost-vector assembly.
Constraints and solver invocation are built in later parts.
"""

from dataclasses import dataclass

import numpy as np

HOURS_PER_YEAR = 8760


@dataclass(frozen=True)
class VariableLayout:
    """Maps dispatch decision variables to flat LP column indices.

    Decision variables are grouped into per-hour blocks laid out
    contiguously across ``T`` hours. Within each hour the block order is:
    thermal generation, wind, solar, storage charge, storage discharge,
    storage state-of-charge, transmission flow, then per-zone load slack.
    """

    n_gen: int
    n_zones: int
    n_storage: int
    n_links: int
    T: int = HOURS_PER_YEAR

    @property
    def vars_per_hour(self) -> int:
        """Return the number of decision variables in a single hour block."""
        return (
            self.n_gen
            + 2 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_zones
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

    def flow_col(self, l: int, t: int) -> int:
        """Return the column index of transmission link ``l`` in hour ``t``."""
        return t * self.vars_per_hour + self._flow_off + l

    def slack_col(self, z: int, t: int) -> int:
        """Return the column index of load slack for zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._slack_off + z

    def p_cols_gen(self, g: int) -> slice:
        """Return a slice selecting all ``T`` columns of thermal generator ``g``."""
        start = self._p_off + g
        return slice(start, start + self.T * self.vars_per_hour, self.vars_per_hour)


def build_cost_vector(
    layout: VariableLayout,
    mc: np.ndarray,
    voll: float,
    storage_epsilon: float = 0.001,
) -> np.ndarray:
    """Assemble the flat LP objective cost vector.

    Thermal slots carry their hourly marginal cost, storage charge and
    discharge carry a small ``storage_epsilon`` penalty to break degeneracy,
    load slack carries the value of lost load (``voll``), and renewable and
    SOC/flow slots are zero-cost.

    Args:
        layout: Variable layout describing the column structure.
        mc: Marginal cost array of shape ``(n_gen, T)``.
        voll: Value of lost load applied to slack variables.
        storage_epsilon: Cycling penalty on storage charge/discharge.

    Returns:
        Cost vector of length ``layout.total_columns``.
    """
    cost = np.zeros(layout.total_columns, dtype=float)
    block = cost.reshape(layout.T, layout.vars_per_hour)

    # Thermal: mc is (n_gen, T); the per-hour block wants (T, n_gen).
    block[:, layout._p_off : layout._w_off] = mc.T

    # Storage charge and discharge: flat cycling penalty.
    block[:, layout._chg_off : layout._dis_off] = storage_epsilon
    block[:, layout._dis_off : layout._soc_off] = storage_epsilon

    # Load slack: value of lost load.
    block[:, layout._slack_off :] = voll

    return cost
