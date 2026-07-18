"""Derive per-backcast-year border-proxy heat rates for the CAISO WECC seam.

The CAISO reference-price seam (``caiso_reference_price_seam``) prices each WECC
corridor as ``(henry_hub + gas_basis) x marginal_heat_rate x load_shape`` — the
same forward-native construction the PJM/MISO ``INTERFACE_NEIGHBORS`` seams use,
specialized to CAISO's two physical ties (COI/Path-66 at the Malin hub →
``WECC_PNW``; Path-46/WOR at the Palo Verde hub → ``WECC_DSW``).

This script re-anchors each corridor's heat rate PER YEAR to the neighbor hub's
OWN measured annual-mean realized RT LMP (the committed
``wecc_intertie_lmp_hourly_CAISO.parquet`` Malin / Palo Verde series) so the
constructed seam reproduces the neighbor's realized annual mean each backcast
year:

    HR[year] = measured_mean_hub_LMP[year]
               / ((henry_hub[year] + gas_basis) x K[year])

where ``K[year] = mean(load_shape)`` is the convexity inflation of the corridor's
load-shape multiplier (so the constructed ANNUAL MEAN, not just the baseload,
equals the measured mean). The load shape is the CISO net/gross driver
(net = load − solar − wind for the solar-driven desert-SW; gross for the
hydro-following Pacific-NW), the same shape the dispatch uses.

This is the NEIGHBOR's own measured price formation (claude.md rule #12 —
measured over a multi-year estimate; the forward analogue is the structural
``marginal_heat_rate``), NOT tuned to CAISO's net interchange (rule #11): it
never reads CAISO's flow, only the WECC hub LMP and the neighbor's load shape.

Run::

    python scripts/data/derive_caiso_seam_hr_by_year.py

and paste the emitted ``hr_by_year`` / structural ``marginal_heat_rate`` into the
CAISO entries of ``INTERFACE_NEIGHBORS`` in ``config/constants.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.data.neighbor_price import caiso_hub_load_shape

_HOURS = 8760

# Corridor → (measured hub label, gas_basis, load_shape_kind, load_shape_exponent).
# Gas bases and shape kinds mirror CAISO_PER_HUB_NEIGHBORS (PNW Sumas discount,
# desert-SW Permian premium; net-load for the solar desert-SW, gross for the
# hydro-following PNW). Exponent 1.0 = parameter-free, mean-preserving.
_CORRIDORS = {
    "WECC_PNW": dict(hub="MALIN", gas_basis=-0.30, kind="gross", exp=1.0),
    "WECC_DSW": dict(hub="PALOVRDE", gas_basis=0.30, kind="net", exp=1.0),
}


class _Spec:
    """Minimal CaisoHubNeighbor-shaped object for caiso_hub_load_shape."""

    def __init__(self, kind: str, exp: float) -> None:
        self.load_shape_kind = kind
        self.load_shape_exponent = exp


def _measured_hub_mean(hub: str, year: int) -> tuple[float, int] | None:
    """Return (annual-mean Malin/Palo-Verde RT LMP, n_hours) for ``year``."""
    path = paths.CALIBRATION_DIR / "wecc_intertie_lmp_hourly_CAISO.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    sub = df[(df["year"] == year) & (df["hub"] == hub)]
    if sub.empty:
        return None
    price = pd.to_numeric(sub["price"], errors="coerce").to_numpy(dtype=float)
    price = price[np.isfinite(price)]
    if price.size == 0:
        return None
    return float(price.mean()), int(price.size)


def derive(years: list[int]) -> None:
    """Print the per-year HR anchors and structural mean for both corridors."""
    for zone, c in _CORRIDORS.items():
        spec = _Spec(c["kind"], c["exp"])
        per_year: dict[int, float] = {}
        print(
            f"\n{zone}  (hub={c['hub']}, basis={c['gas_basis']:+.2f}, "
            f"kind={c['kind']}, exp={c['exp']})"
        )
        for year in years:
            meas = _measured_hub_mean(c["hub"], year)
            if meas is None:
                print(f"  {year}: no measured hub series")
                continue
            mean_lmp, n = meas
            shape = caiso_hub_load_shape(spec, year, _HOURS)
            k = float(np.mean(shape)) if shape is not None else 1.0
            gas = HENRY_HUB_TRAJECTORIES["mid"][year]
            delivered = gas + c["gas_basis"]
            hr = mean_lmp / (delivered * k)
            per_year[year] = hr
            print(
                f"  {year}: mean_LMP={mean_lmp:6.2f} (n={n:5d}h)  "
                f"gas={gas:.2f} deliv={delivered:.2f}  K={k:.3f}  -> HR={hr:.2f}"
            )
        if per_year:
            struct = float(np.mean(list(per_year.values())))
            tbl = ", ".join(f"{y}: {hr:.2f}" for y, hr in sorted(per_year.items()))
            print(f"  hr_by_year={{{tbl}}}")
            print(f"  marginal_heat_rate={struct:.2f}  (mean of per-year anchors)")


if __name__ == "__main__":
    derive([2023, 2024, 2025])
