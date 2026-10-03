"""closeout-PJM-lossdemand (zero LP): the energy identity residual of a solved PJM bundle.

For each year of a composed PJM span this reports, from the committed hourly sidecars and each leg's
``flows.parquet``:

* ``residual`` ``R = gen (incl. the import node's net) - storage net charge - demand`` against the MEASURED
  demand row (the K1 kill of PRECOMMIT-closeout-pjm-lossdemand-2026-10-03: ``|R| <= 0.05`` TWh/yr);
* ``loss_p1`` ``= sum eps * F1``, the P1 dissipation of the ``pjm_zonal_loss_surface`` links;
* ``netted_p0 = loss_p1 - R``: under ``zonal_loss_demand_reconciliation`` the identity is
  ``R = sum eps * (F1 - F0)``, so this is the P0 dissipation the P1 demand was netted by.

The balance and loss arithmetic is :mod:`scripts.probes._closeoutpjm_balance_trace` verbatim.

Usage::

    python scripts/probes/_closeoutpjm_lossdemand_residual.py --bundle results/calibration/<span> \
        --legs <dir with <year>/flows.parquet> --out results/phase0/pjm/_closeoutpjm_lossdemand_residual.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_closeoutpjm_balance_trace", REPO / "scripts/probes/_closeoutpjm_balance_trace.py"
)
trace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trace)


def main() -> None:
    """Score every year of ``--bundle`` and write the JSON payload."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--legs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="*", default=list(trace.YEARS))
    args = ap.parse_args()
    out = {"bundle": str(args.bundle), "years": {}}
    for y in args.years:
        b = trace.balance(args.bundle, y)
        fl = trace.link_losses(pd.read_parquet(args.legs / str(y) / "flows.parquet"), y)
        loss = float(fl.loss_mw.sum() / trace.TWH)
        out["years"][str(y)] = {
            "residual_twh": round(b["residual"], 4),
            "loss_p1_twh": round(loss, 4),
            "netted_p0_twh": round(loss - b["residual"], 4),
            "slack_twh": round(b["slack"], 4),
            "dump_twh": round(b["dump"], 4),
            "demand_twh": round(b["demand"], 3),
            "k1_pass": abs(b["residual"]) <= 0.05,
        }
        print(y, out["years"][str(y)])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
