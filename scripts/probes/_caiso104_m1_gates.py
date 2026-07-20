"""CAISO-104 M1 gate scorer: the pre-registered volume/allocation gates (B vs A).

Scores the FINDING-caiso104 §3 pre-registered gates that are NOT already
covered by `_caiso92_report` (which prints the C1 grid, the hod resid ladder
and C3c side-by-side):

  * Gate 3 (volume-holding, the mechanism's own claim): annual battery charge
    TWh AND belly-window (hod 10-14) charge TWh each within +-5 % of the
    A-leg, per year (PS excluded, P1).
  * Gate 6 (reporting): allocation-floor binding share — the fraction of
    (day x active-hod) slots where the B-leg's fleet charge sits AT the floor
    ``alloc_share[hod] x da_frac x day_total`` (rel tol 1e-3) — plus the
    per-window charge reallocation (B - A TWh by hod window).

Usage: python scripts/probes/_caiso104_m1_gates.py <bundle_A> <bundle_B>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
WINDOWS = {
    "overnight(0-5)": range(0, 6),
    "morning(6-9)": range(6, 10),
    "belly(10-14)": range(10, 15),
    "pm-shldr(15-16)": range(15, 17),
    "evening(17-21)": range(17, 22),
    "late(22-23)": range(22, 24),
}


def batt_charge(bundle: Path, year: int) -> np.ndarray:
    """(8760,) fleet battery charge MW (P1, PS excluded)."""
    s = pd.read_parquet(
        bundle / "storage.parquet",
        columns=["pass", "year", "tech", "hour", "charge_mw"],
    )
    s = s[(s["pass"] == "P1") & (s.year == year) & (s.tech != "pumped_storage")]
    return (
        s.groupby("hour")
        .charge_mw.sum()
        .reindex(range(8760), fill_value=0.0)
        .to_numpy()
    )


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    a_dir, b_dir = Path(sys.argv[1]), Path(sys.argv[2])

    from market_sim.model.storage import caiso_charge_allocation_params

    all_pass = True
    for year in YEARS:
        chg_a = batt_charge(a_dir, year)
        chg_b = batt_charge(b_dir, year)
        hod = np.arange(8760) % 24
        belly = np.isin(hod, list(WINDOWS["belly(10-14)"]))

        ann_a, ann_b = chg_a.sum() / 1e6, chg_b.sum() / 1e6
        bel_a, bel_b = chg_a[belly].sum() / 1e6, chg_b[belly].sum() / 1e6
        d_ann = (ann_b - ann_a) / max(ann_a, 1e-9)
        d_bel = (bel_b - bel_a) / max(bel_a, 1e-9)
        g3 = abs(d_ann) <= 0.05 and abs(d_bel) <= 0.05
        all_pass &= g3
        print(f"\n===== {year} =====")
        print(
            f"GATE 3 volume-holding: annual {ann_a:.3f} -> {ann_b:.3f} TWh "
            f"({d_ann:+.2%}) | belly {bel_a:.3f} -> {bel_b:.3f} TWh "
            f"({d_bel:+.2%}) | {'PASS' if g3 else 'FAIL'} (band +-5%)"
        )

        # Binding share in the B-leg (the mechanism's conduct report).
        _bidx, share, da_frac = caiso_charge_allocation_params([], year, 8760)
        share24 = share[:24]
        act = np.flatnonzero(share24 > 0.0)
        days = chg_b[: 365 * 24].reshape(365, 24)
        day_tot = days.sum(axis=1, keepdims=True)
        floor = share24[None, :] * da_frac * day_tot
        with np.errstate(divide="ignore", invalid="ignore"):
            at_floor = np.isclose(days[:, act], floor[:, act], rtol=1e-3, atol=0.5)
        active_days = (day_tot[:, 0] > 1.0).sum()
        bind_share = float(at_floor[day_tot[:, 0] > 1.0].mean()) if active_days else 0.0
        print(
            f"GATE 6 binding: {bind_share:.3f} of (charging-day x active-hod) "
            f"slots at the allocation floor ({active_days} charging days, "
            f"{act.size} active hods, da_frac {da_frac:.4f})"
        )
        realloc = {
            w: (chg_b[np.isin(hod, list(h))].sum() - chg_a[np.isin(hod, list(h))].sum())
            / 1e6
            for w, h in WINDOWS.items()
        }
        print(
            "GATE 6 reallocation (B - A TWh by window): "
            + " ".join(f"{w.split('(')[0]} {v:+.3f}" for w, v in realloc.items())
        )
    print(f"\nGATE 3 OVERALL: {'PASS' if all_pass else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
