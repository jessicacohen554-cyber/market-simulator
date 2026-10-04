"""closeout-SOCO-w3, zero LP: score the composed BTM-holdout probe against the keeper, record by record.

The arm moves the per-(ISO, year) bench parts (the lockstep seam), so the keeper's records are taken on the
keeper's own bench (``--keeper-records``, written before the probe's registration re-rendered the parts) and the
probe's on the re-rendered parts. Writes docs/records/soco/closeout-soco-w3/solve_score.csv. The probe is
unattested at registration, so a ledgered keeper CAVEAT can print FAIL on the probe; read the magnitude column.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import calibration_verdict as cv  # noqa: E402

ARM = "2026-10-04-closeout-soco-w3-btm"
OUT = REPO / "docs/records/soco/closeout-soco-w3/solve_score.csv"


def records(run: str) -> tuple[dict, pd.DataFrame]:
    """Return the run's verdict and its flattened records."""
    v = cv.determine(run)
    rows = []
    for cid, crit in (v.get("criteria") or {}).items():
        for r in crit.get("records") or []:
            rows.append(dict(crit=cid, year=r.get("year"), key=r.get("key") or r.get("metric"),
                             status=r.get("status"), magnitude=r.get("magnitude")))
    return v, pd.DataFrame(rows)


def main() -> None:
    """Write the side-by-side table and print every status change and the headline rows."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--keeper-records", required=True, help="CSV of the keeper's records on its own bench")
    a = ap.parse_args()
    k = pd.read_csv(a.keeper_records)
    va, p = records(ARM)
    m = k.merge(p, on=["crit", "year", "key"], how="outer", suffixes=("_keeper", "_arm"))
    m.to_csv(OUT, index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 80, "display.max_rows", 500)
    print("ARM:", va.get("determination"), "|", va.get("reasons"))
    print("status changes:\n", m[m.status_keeper != m.status_arm].to_string(index=False))
    keep = m.crit.isin(["price_mean", "price_shape", "dispatch_corr", "sysvol"]) | (
        (m.crit == "fuelmix") & m.key.isin(["CC_REGULAR", "COAL_BIT", "COAL_PRB", "ST_GAS", "CT_PEAKER"]))
    print(m[keep].to_string(index=False))


if __name__ == "__main__":
    main()
