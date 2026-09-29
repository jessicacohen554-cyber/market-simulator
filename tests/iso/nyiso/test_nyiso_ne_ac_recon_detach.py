"""The NE AC node detached from the monthly net-interchange band (NYISO-NEXT-13).

Trivial cases first: one pooled row + one node row, a one-month band; the node
leaves the band, the tie's measured monthly schedule leaves the target, the
half-width is re-taken on the new target, a band with no node row refuses, and
the measured-flow loader places the P-32 row on the model clock. Byte-identity
off is the ScenarioConfig default plus the cache-key optional-field ledger.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.interchange.nyiso import (
    detach_nyiso_ne_ac_from_reconciliation,
    load_nyiso_ne_ac_measured_flow,
)
from market_sim.model.interchange.spec import NYISO_NE_AC_SEAM_ROW, NYISO_NE_AC_ZONE


def test_detach_drops_node_rows_and_measured_schedule():
    """Pooled 100 MWh target, NE measured -30 MWh -> pooled target 130, +-2 %."""
    unit_ids = ["NYISO_external_HQ_hydro", f"{NYISO_NE_AC_ZONE}_exp#1"]
    recon = (np.array([0, 1]), np.array([98.0]), np.array([102.0]))
    flow = np.full(24, -30.0 / 24)  # 24 h, all January
    idx, lo, hi = detach_nyiso_ne_ac_from_reconciliation(
        recon, unit_ids, flow, band_frac=0.02
    )
    assert idx.tolist() == [0]
    assert lo[0] == pytest.approx(130.0 - 2.6)
    assert hi[0] == pytest.approx(130.0 + 2.6)


def test_detach_refuses_band_without_node():
    """No NE AC row in the band: refuse rather than silently no-op."""
    recon = (np.array([0]), np.array([98.0]), np.array([102.0]))
    with pytest.raises(ValueError):
        detach_nyiso_ne_ac_from_reconciliation(
            recon, ["NYISO_external_HQ_hydro"], np.zeros(24)
        )


def test_measured_flow_on_model_clock():
    """The P-32 NE AC row's flow_mw lands on its own local hour."""
    local = pd.date_range("2024-01-01", periods=24, freq="h")
    frame = pd.DataFrame(
        {
            "interface": [NYISO_NE_AC_SEAM_ROW] * 24 + ["SCH - OH - NY"] * 24,
            "interval_start_local": list(local) * 2,
            "flow_mw": list(np.arange(24.0) - 12.0) + [999.0] * 24,
        }
    )
    out = load_nyiso_ne_ac_measured_flow(2024, 24, frame=frame)
    assert out.tolist() == list(np.arange(24.0) - 12.0)


def test_flag_default_off_and_key_stable():
    """Default off; arming it moves the cache key, the default does not."""
    base = ScenarioConfig(iso="NYISO", mode="backcast")
    assert base.nyiso_ne_ac_recon_detach is False
    armed = base.with_overrides(nyiso_ne_ac_recon_detach=True)
    assert armed.cache_key() != base.cache_key()
