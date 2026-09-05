"""miso-213 L-5 (post-code, zero-solve): the arm's fuel-price liveness on the keeper.

Written AFTER the arm code and BEFORE the arm solve. On the miso-210 keeper's
own fleet chain, re-run ``resolve_fuel_prices`` with
``miso_zonal_gas_basis_skip_923_priced=True`` and compare cell by cell to the
keeper's ``F`` and to ``F_nobasis`` (basis off):

* every cell the PRODUCTION print path wrote (the mask the overlay returns,
  replayed on the pre-overlay array) must equal ``F_nobasis``;
* every unmasked gas cell must equal the keeper's ``F`` (it keeps the increment);
* the share of gas cells changed is reported beside the mask share. Phase 0
  inferred the mask as ``F_nobasis != F_noplant``, which is blind where the
  dual-fuel oil-parity cap equalises the two toggles; the hidden count is
  reported (the first pass mis-called those cells trajectory cells).

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso213_arm_liveness.py

Appends ``L5_arm_liveness`` to ``results/calibration/_miso213_basis_layering.json``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso211_rdt_binding_state as p  # noqa: E402  (re-points to the miso-210 keeper)
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from market_sim.data.fuel import (  # noqa: E402
    apply_plant_monthly_fuel_prices,
    resolve_fuel_prices,
)

OUT = REPO / "results/calibration/_miso213_basis_layering.json"
GAS = set(p.GAS_CLASSES)


def main() -> None:
    cfg0 = keeper_config()
    assert not cfg0.miso_zonal_gas_basis_skip_923_priced
    rec = json.loads(OUT.read_text())
    out: dict = {
        "note": "post-code zero-solve check on the keeper's fleet chain: arm F vs keeper F and F_nobasis",
        "years": {},
    }
    for year in p.YEARS:
        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, fp, _mc, _zn = build_year(cfg, year)
        fp = np.asarray(fp, float)
        fp_nb = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(cfg, miso_zonal_gas_basis=False), arrays, year
            ),
            float,
        )
        fp_np = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(
                    cfg,
                    miso_zonal_gas_basis=False,
                    gas_plant_monthly_fuel_pricing=False,
                ),
                arrays,
                year,
            ),
            float,
        )
        fp_arm = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(cfg, miso_zonal_gas_basis_skip_923_priced=True),
                arrays,
                year,
            ),
            float,
        )
        labels = np.array([p.m207.class_label(g) for g in fleet], dtype=object)
        gas = np.isin(labels, list(GAS))
        # The PRODUCTION mask: what the print path actually wrote, obtained by
        # replaying the overlay on the pre-overlay array (basis off, print off,
        # apply_monthly=False gives the trajectory base the chain starts from).
        base = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(cfg, miso_zonal_gas_basis=False),
                arrays,
                year,
                apply_monthly=False,
            ),
            float,
        )
        written = apply_plant_monthly_fuel_prices(base.copy(), arrays, cfg, year)
        written = written & gas[:, None]
        unmasked = gas[:, None] & ~written
        # phase-0's inference (F_nobasis != F_noplant) is blind where the
        # dual-fuel oil-parity cap equalises the two toggles; count those cells.
        inferred_print = ~np.isclose(fp_nb, fp_np, rtol=0, atol=1e-9) & gas[:, None]
        hidden_by_cap = written & ~inferred_print
        eq_nb = np.isclose(fp_arm, fp_nb, rtol=0, atol=1e-12)
        eq_keep = np.isclose(fp_arm, fp, rtol=0, atol=1e-12)
        changed = ~eq_keep & gas[:, None]
        n_gas_cells = int(gas.sum() * fp.shape[1])
        y = {
            "gas_cells": n_gas_cells,
            "production_mask_share": round(float(written.sum() / n_gas_cells), 6),
            "phase0_inferred_print_share": round(
                float(inferred_print.sum() / n_gas_cells), 6
            ),
            "print_cells_hidden_from_phase0_by_oil_parity_cap": int(
                hidden_by_cap.sum()
            ),
            "masked_cells_equal_F_nobasis_share": round(float(eq_nb[written].mean()), 6)
            if written.any()
            else None,
            "unmasked_cells_equal_keeper_F_share": round(
                float(eq_keep[unmasked].mean()), 6
            )
            if unmasked.any()
            else None,
            "unmasked_cells": int(unmasked.sum()),
            "gas_cells_changed_share": round(float(changed.sum() / n_gas_cells), 6),
            "max_abs_arm_minus_nobasis_on_masked_cells": round(
                float(np.abs(fp_arm - fp_nb)[written].max()), 9
            )
            if written.any()
            else None,
            "capw_mean_abs_increment_removed_usd_mmbtu": round(
                float(
                    (
                        np.abs(fp - fp_arm)[gas] * np.asarray(arrays.pmax)[gas][:, None]
                    ).sum()
                    / (np.asarray(arrays.pmax)[gas].sum() * fp.shape[1])
                ),
                4,
            ),
        }
        y["passed"] = bool(
            (y["masked_cells_equal_F_nobasis_share"] in (None, 1.0))
            and (y["unmasked_cells_equal_keeper_F_share"] in (None, 1.0))
        )
        out["years"][year] = y
        print(year, json.dumps(y), flush=True)
    out["passed"] = all(v["passed"] for v in out["years"].values())
    rec["L5_arm_liveness"] = out
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print("L5", "PASS" if out["passed"] else "FAIL", f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
