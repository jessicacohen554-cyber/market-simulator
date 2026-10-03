"""closeout-SOCO-3, zero LP: score the composed arm against the keeper, record by record.

Runs calibration_verdict.determine on both registered runs and writes every criterion record side by side
(status + magnitude) to docs/records/soco/closeout-soco-3/solve_score.csv. The arm is unattested at
registration (promote_keeper.py writes the attestation), so a ledgered keeper CAVEAT can print FAIL on the
arm; read the magnitude column for those.
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import calibration_verdict as cv  # noqa: E402

KEEPER, ARM = (
    "2026-10-03-closeout-soco-2-nuclear",
    "2026-10-03-closeout-soco-3-coalpile",
)


def records(run: str) -> tuple[dict, pd.DataFrame]:
    """Return the run's verdict and its flattened records."""
    v = cv.determine(run)
    rows = []
    for cid, crit in (v.get("criteria") or {}).items():
        for r in crit.get("records") or []:
            rows.append(
                dict(
                    crit=cid,
                    year=r.get("year"),
                    key=r.get("key") or r.get("metric"),
                    status=r.get("status"),
                    magnitude=r.get("magnitude"),
                )
            )
    return v, pd.DataFrame(rows)


def main() -> None:
    """Write and print the side-by-side table, the two determinations and every status change."""
    vk, k = records(KEEPER)
    va, a = records(ARM)
    m = k.merge(
        a, on=["crit", "year", "key"], how="outer", suffixes=("_keeper", "_arm")
    )
    m.to_csv(REPO / "docs/records/soco/closeout-soco-3/solve_score.csv", index=False)
    pd.set_option(
        "display.width", 250, "display.max_colwidth", 70, "display.max_rows", 500
    )
    print("KEEPER:", vk.get("determination"), "| ARM:", va.get("determination"))
    ch = m[m.status_keeper != m.status_arm]
    print("status changes:\n", ch.to_string(index=False))
    for c in (
        "fuelmix",
        "price_mean",
        "dispatch_corr",
        "forced_share",
        "governance",
        "sysvol",
    ):
        print(f"\n== {c}")
        print(
            m[m.crit == c][
                [
                    "year",
                    "key",
                    "status_keeper",
                    "magnitude_keeper",
                    "status_arm",
                    "magnitude_arm",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
