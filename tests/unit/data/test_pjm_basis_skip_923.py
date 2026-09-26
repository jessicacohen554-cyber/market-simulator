"""PJM-NEXT-2: the PJM zonal basis skips print-derived cells under its scope flag.

PJM's own twin of miso-213 (rule 25: the MISO verdict does not transfer, so the
PJM applier carries its own flag). Rule 19 ``[R-ONE-MECH]``: a gas cell whose
delivered price the EIA-923 print path SET already embeds the regional premium,
so the mean-zero zonal increment is not layered on top of it. Pinned here:

* with ``pjm_zonal_gas_basis_skip_923_priced`` ON, masked cells are left
  byte-untouched and unmasked cells receive EXACTLY the flag-off spread;
* with the flag OFF a passed mask is ignored (byte-identical to HEAD);
* the field is registered, default-off and dropped from the cache key.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel import apply_pjm_zonal_gas_basis

_PJM_ZONES = [
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
]
HOURS = 48


def _fleet():
    gens = [
        Generator(
            unit_id=f"GAS_{z}",
            name=f"{z} CC",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=400.0,
        )
        for z in ("PJM_SWMAAC", "PJM_AEP_Ohio", "PJM_Dominion")
    ]
    return generators_to_fleet_arrays(gens, _PJM_ZONES, hours=HOURS)


def test_registered_default_off_and_key_stable():
    assert ScenarioConfig().pjm_zonal_gas_basis_skip_923_priced is False
    assert cache_key_drop_defaults()["pjm_zonal_gas_basis_skip_923_priced"] is False
    base = ScenarioConfig(iso="PJM")
    armed = base.with_overrides(pjm_zonal_gas_basis_skip_923_priced=True)
    assert base.cache_key() != armed.cache_key()


def test_skip_mask_leaves_masked_cells_untouched_and_keeps_spread_elsewhere():
    fleet = _fleet()
    base = np.full((fleet.n_gen, HOURS), 3.0)
    on_cfg = ScenarioConfig(iso="PJM", hours=HOURS, pjm_zonal_gas_basis=True)
    on = base.copy()
    apply_pjm_zonal_gas_basis(on, fleet, on_cfg, 2024)
    sw = fleet.unit_ids.index("GAS_PJM_SWMAAC")
    aep = fleet.unit_ids.index("GAS_PJM_AEP_Ohio")
    assert not np.allclose(on[sw], base[sw])  # the basis is live in 2024

    mask = np.zeros((fleet.n_gen, HOURS), dtype=bool)
    mask[sw, : HOURS // 2] = True
    arm_cfg = on_cfg.with_overrides(pjm_zonal_gas_basis_skip_923_priced=True)
    arm = base.copy()
    apply_pjm_zonal_gas_basis(arm, fleet, arm_cfg, 2024, skip_cells=mask)
    np.testing.assert_array_equal(arm[sw, : HOURS // 2], base[sw, : HOURS // 2])
    np.testing.assert_array_equal(arm[sw, HOURS // 2 :], on[sw, HOURS // 2 :])
    np.testing.assert_array_equal(arm[aep], on[aep])


def test_flag_off_ignores_a_passed_mask():
    fleet = _fleet()
    base = np.full((fleet.n_gen, HOURS), 3.0)
    cfg = ScenarioConfig(iso="PJM", hours=HOURS, pjm_zonal_gas_basis=True)
    on = base.copy()
    apply_pjm_zonal_gas_basis(on, fleet, cfg, 2024)
    with_mask = base.copy()
    apply_pjm_zonal_gas_basis(
        with_mask, fleet, cfg, 2024, skip_cells=np.ones_like(base, dtype=bool)
    )
    np.testing.assert_array_equal(with_mask, on)
