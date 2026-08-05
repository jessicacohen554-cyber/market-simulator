"""pjm-157 §2 — PJM coal<->CC switching elasticity, identified IN-SAMPLE on 2023-2025.

The pjm-156 hand-back asserts the model's CC fleet is gas-price-inelastic and
that 2022 is "the only year with a large enough fuel excursion to expose it".
This probe tests both claims without touching 2022 for identification, which is
what CLAUDE.md rule 22 requires: PJM-footprint delivered gas reaches $6.63 /
$5.88 / $6.69 per MMBtu in the Januaries of 2023 / 2024 / 2025, so the in-sample
gas/coal ratio already spans 1.00-2.51 against 2022's 2.20-3.40.

Method, all from committed artifacts (no LP, no scoring):

* **actual** monthly class energy is reconstructed from the per-plant ``campd``
  blobs in ``bench/PJM/<year>.json.gz`` — uint8 capacity-factor percent times the
  plant's ``npl``.  Fidelity against the committed ``c_ann`` is printed first;
  ``CC_REGULAR`` reconstructs to within 0.02 %.
* **model** monthly class energy is the P1 ``class_hourly`` sidecar.
* **prices** are the EIA-923 quantity-weighted delivered cost over the PJM
  footprint states, by fuel group and month.

It then regresses the coal share of (coal + ``CC_REGULAR``) on
``ln(delivered gas / delivered coal)`` and decomposes each year's ``CC_REGULAR``
error into a thermal-LEVEL term and a switching-SHARE term:

    CC_m - CC_a = (T_m - T_a)(1 - s_a)  -  T_m (s_m - s_a)
                  \_____ LEVEL _____/     \____ SHARE ____/
"""

from __future__ import annotations

import base64
import gzip
import json
from collections import defaultdict

import numpy as np
import pandas as pd

TWH = 1e6

BUNDLES = {
    2022: "results/calibration/pjm2022_touchpoint",
    2023: "results/calibration/pjm152_collapse_A",
    2024: "results/calibration/pjm152_collapse_A",
    2025: "results/calibration/pjm152_collapse_A",
}
COAL = ["COAL_BIT", "COAL_PRB", "COAL_WC"]

#: EIA-923 reports by state; the PJM footprint is approximated by its member
#: states.  Used only to build a delivered-price index, never a volume.
PJM_STATES = ["OH", "PA", "NJ", "MD", "DE", "VA", "WV", "IL", "IN", "KY", "MI", "NC", "DC"]

F923 = "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"


def actual_hourly(year: int, groups: list[str]) -> tuple[np.ndarray, float, float]:
    """Reconstruct a class group's actual hourly MW from the bench ``campd`` blobs.

    Args:
        year: bench year to read.
        groups: bench plant groups to include.

    Returns:
        ``(hourly_mw, annual_twh_from_blob, annual_twh_from_c_ann)`` — the last
        two are the fidelity check.
    """
    bench = json.load(gzip.open(f"frontend/data/backcast/bench/PJM/{year}.json.gz"))
    total, c_ann = np.zeros(8760), 0.0
    for rec in bench["bench"]["plants"].values():
        if rec["group"] not in groups or rec.get("nodata"):
            continue
        cf = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
        total += cf / 100.0 * float(rec["npl"])
        c_ann += rec.get("c_ann") or 0.0
    return total, total.sum() / TWH, c_ann


def model_hourly(year: int, bundle: str, classes: list[str]) -> np.ndarray:
    """Return the P1 model hourly MW for a set of LP classes.

    Args:
        year: solve year.
        bundle: bundle directory holding ``hourly/``.
        classes: LP ``klass`` values to sum.

    Returns:
        Length-8760 array of MW.
    """
    ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(classes))]
    return ch.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0).to_numpy()


def delivered_price(fuel_group: str) -> pd.Series:
    """Return the PJM-footprint quantity-weighted delivered price by (year, month).

    Args:
        fuel_group: EIA-923 ``fuel_group`` value, e.g. ``"Natural Gas"``.

    Returns:
        Series indexed by ``(year, month)`` in $/MMBtu.
    """
    df = pd.read_parquet(F923)
    sub = df[
        (df.fuel_group == fuel_group)
        & (df.state.isin(PJM_STATES))
        & (df.year.between(2022, 2025))
    ]
    return sub.groupby(["year", "month"]).apply(
        lambda d: np.average(d.price_per_mmbtu, weights=np.maximum(d.quantity, 1e-9)),
        include_groups=False,
    )


def build_panel() -> pd.DataFrame:
    """Assemble the 48-month model/actual/price panel.

    Returns:
        Frame with one row per (year, month) carrying model and actual coal and
        ``CC_REGULAR`` energy (TWh), delivered prices and the derived shares.
    """
    gas, coal = delivered_price("Natural Gas"), delivered_price("Coal")
    rows = []
    for year, bundle in BUNDLES.items():
        idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        a_cc = pd.Series(actual_hourly(year, ["CC_REGULAR"])[0], index=idx).resample("MS").sum() / TWH
        a_co = pd.Series(actual_hourly(year, COAL)[0], index=idx).resample("MS").sum() / TWH
        m_cc = pd.Series(model_hourly(year, bundle, ["CC_REGULAR"]), index=idx).resample("MS").sum() / TWH
        m_co = pd.Series(model_hourly(year, bundle, COAL), index=idx).resample("MS").sum() / TWH
        for i in range(12):
            rows.append(
                dict(
                    year=year, month=i + 1,
                    gas=gas.loc[(year, i + 1)], coal=coal.loc[(year, i + 1)],
                    a_cc=a_cc.iloc[i], a_co=a_co.iloc[i],
                    m_cc=m_cc.iloc[i], m_co=m_co.iloc[i],
                )
            )
    df = pd.DataFrame(rows)
    df["ratio"] = df.gas / df.coal
    df["a_share"] = df.a_co / (df.a_co + df.a_cc)
    df["m_share"] = df.m_co / (df.m_co + df.m_cc)
    return df


def fit(df: pd.DataFrame, share_col: str) -> tuple[float, float]:
    """Fit ``share ~ a + b * ln(ratio)`` and return ``(slope, pearson r)``.

    Args:
        df: panel subset to fit.
        share_col: ``"m_share"`` or ``"a_share"``.

    Returns:
        ``(slope, r)``.
    """
    x, y = np.log(df["ratio"].to_numpy()), df[share_col].to_numpy()
    slope = np.polyfit(x, y, 1)[0]
    return slope, float(np.corrcoef(x, y)[0, 1])


def main() -> None:
    """Print the fidelity check, the elasticity fits and the CC error decomposition."""
    print("blob-reconstruction fidelity (annual TWh from blob vs committed c_ann):")
    for year in sorted(BUNDLES):
        for label, groups in (("CC_REGULAR", ["CC_REGULAR"]), ("coal", COAL)):
            _, blob, ann = actual_hourly(year, groups)
            print(f"  {year} {label:<11} blob {blob:8.2f}  c_ann {ann:8.2f}  err {(blob / ann - 1) * 100:+6.2f}%")
    print("  (coal reconstructs less exactly than CC because some coal plants carry")
    print("   `nodata`; the annual decomposition below therefore uses c_ann, not the blob.)")

    df = build_panel()
    print()
    print("COAL-SHARE ELASTICITY  d(coal share of coal+CC) / d ln(delivered gas/coal)")
    print(f"{'sample':<26}{'model slope':>13}{'actual slope':>14}{'ratio':>8}{'model r':>10}{'actual r':>10}")
    for label, sub in (
        ("IN-SAMPLE 2023-25 (n=36)", df[df.year.between(2023, 2025)]),
        ("HOLDOUT 2022 (n=12)", df[df.year == 2022]),
        ("all 48 months", df),
    ):
        bm, rm = fit(sub, "m_share")
        ba, ra = fit(sub, "a_share")
        print(f"{label:<26}{bm:>13.4f}{ba:>14.4f}{bm / ba:>8.3f}{rm:>10.3f}{ra:>10.3f}")

    print()
    print("coal-share error (model - actual), percentage points:")
    for year in sorted(df.year.unique()):
        e = (df[df.year == year].m_share - df[df.year == year].a_share) * 100
        print(f"  {year}: mean {e.mean():+6.2f}  MAE {e.abs().mean():5.2f}  max|e| {e.abs().max():5.2f}")

    print()
    print("CC_REGULAR ANNUAL ERROR DECOMPOSITION — thermal LEVEL vs switching SHARE")
    print("(actual = committed bench c_ann, grid-delivered)")
    print(
        f"{'yr':>5}{'T_mdl':>8}{'T_act':>8}{'dT':>8}{'s_mdl%':>8}{'s_act%':>8}"
        f"{'ds pp':>7}{'CC err':>8}{'LEVEL':>8}{'SHARE':>8}{'lvl%':>7}"
    )
    for year, bundle in BUNDLES.items():
        ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
        m = ch[ch["pass"] == "P1"].groupby("klass")["mw"].sum() / TWH
        bench = json.load(gzip.open(f"frontend/data/backcast/bench/PJM/{year}.json.gz"))
        a = defaultdict(float)
        for rec in bench["bench"]["plants"].values():
            a[rec["group"]] += rec.get("c_ann") or 0.0
        t_m = m["CC_REGULAR"] + sum(m.get(c, 0.0) for c in COAL)
        t_a = a["CC_REGULAR"] + sum(a[c] for c in COAL)
        s_m = sum(m.get(c, 0.0) for c in COAL) / t_m
        s_a = sum(a[c] for c in COAL) / t_a
        cc_err = m["CC_REGULAR"] - a["CC_REGULAR"]
        level, share = (t_m - t_a) * (1 - s_a), -t_m * (s_m - s_a)
        print(
            f"{year:>5}{t_m:>8.1f}{t_a:>8.1f}{t_m - t_a:>8.2f}{s_m * 100:>8.2f}"
            f"{s_a * 100:>8.2f}{(s_m - s_a) * 100:>7.2f}{cc_err:>8.2f}"
            f"{level:>8.2f}{share:>8.2f}{level / cc_err * 100:>7.0f}"
        )


if __name__ == "__main__":
    main()
