"""NWPP-NEXT-23 phase 0 (zero LP): why does the NW price sit below the seam anchors?

Reads only measured data, the committed registry, keeper 2026-10-03-nwpp-next-22b-w0's
committed ``hourly/`` sidecars and its seam flows (``flows_<Y>.parquet`` extracted from the
keeper's legs by full SHA into FLOWS_DIR). No LP.

A. Anchor vs its own source, hour by hour: the registered zero-flow anchor
   ``(HH + basis) x HR[y] x (CAISO net load / mean)`` against the measured MALIN
   intertie LMP (COI) and ELAP_BCHA (BC), 2021/2023-2025: mean, std, r, and the
   hour-of-day profile. MALIN/BCHA appear only as the anchor's validation series.
B. Gap decomposition in the keeper's export hours:
   (anchor - hurdle) - NW_model = (anchor - meas_anchor) + (meas_anchor - NW_meas)
   + (NW_meas - NW_model) - hurdle; NW_meas = the labelled WEIM imbalance benchmark.
C. Which NW class is marginal in the border zones in COI/BC export hours
   (``unit_marginal_<Y>``).
D. Price-taker counterfactuals on the keeper's NW price (measured caps), per candidate hurdle.
E. Measured flow by measured spread bin (the validation any hurdle must face, never its source).

Usage: PYTHONPATH=. python scripts/probes/_nwppnext23_price_level_phase0.py FLOWS_DIR
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts/data")
sys.path.insert(0, "scripts/probes")

from _nwppnext20_seam_phase0 import SEAMS, _measured  # noqa: E402

from market_sim.data.neighbor_price import seam_tranche_prices  # noqa: E402
from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly  # noqa: E402

YEARS = tuple(range(2019, 2026))
KEEPER = Path("results/calibration/nwppnext22b_span/hourly")
VAL = Path("data/raw/_validation-source")
EXT = {
    "CAISO_COI": "NWPP_ext_COI",
    "CAISO_NEVP": "NWPP_ext_NEVP",
    "WECC_CAN": "NWPP_ext_BC",
}


def _series(df: pd.DataFrame, y: int, col: str) -> np.ndarray:
    s = df[df["year"] == y].set_index("hour")[col].reindex(range(8760))
    return s.to_numpy(dtype=float)


def _meas_anchor(seam: str, y: int) -> np.ndarray:
    if seam.startswith("CAISO"):
        d = pd.read_parquet(VAL / "wecc_intertie_lmp_hourly_CAISO.parquet")
        return _series(d[d["hub"] == "MALIN"], y, "price")
    d = pd.read_parquet("data/raw/nwpp-weim/weim_hourly_counterparty.parquet")
    return _series(d[d["baa"] == "BCHA"], y, "lmp")


def _keeper(y: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    zp = s.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(8760)
    )
    return s, zp


def _flow(fdir: Path, y: int, seam: str) -> np.ndarray:
    f = pd.read_parquet(fdir / f"flows_{y}.parquet")
    f = f[(f["pass"] == "P1") & (f["from_zone"] == EXT[seam])]
    return -f.groupby("hour")["mw"].sum().reindex(range(8760)).fillna(0.0).to_numpy()


def _zero_flow_anchor(spec, y: int) -> np.ndarray:
    ex, im, _ = seam_tranche_prices(spec, y, 8760, n_tranches=1)
    # n=1 prices the band midpoint; recover the zero-flow price as the mean of
    # the export (load - L/2) and import (load + L/2) prices (exponent 1: linear).
    return 0.5 * (ex[0] + im[0])


def anchor_vs_source() -> None:
    """A: the registered zero-flow anchor vs its measured source series."""
    print("\n## A. Zero-flow anchor vs measured source ($/MWh)")
    for seam in ("CAISO_COI", "WECC_CAN"):
        spec = SEAMS[seam]
        for y in (2021, 2022, 2023, 2024, 2025):
            if spec.anchored_years_only and y not in (spec.hr_by_year or {}):
                continue
            a, m = _zero_flow_anchor(spec, y), _meas_anchor(seam, y)
            ok = np.isfinite(m)
            if ok.sum() < 1000:
                continue
            hod = np.arange(8760) % 24
            ga = pd.Series(a[ok]).groupby(hod[ok]).mean()
            gm = pd.Series(m[ok]).groupby(hod[ok]).mean()
            print(
                f"{seam:9s} {y} n {ok.sum():4d} anchor mean {a[ok].mean():6.2f} sd {a[ok].std():5.2f} | "
                f"meas mean {m[ok].mean():6.2f} sd {m[ok].std():5.2f} | r {np.corrcoef(a[ok], m[ok])[0, 1]:.3f} "
                f"| r(hod) {np.corrcoef(ga, gm)[0, 1]:.3f} hod-amp anchor {ga.max() - ga.min():5.1f} meas {gm.max() - gm.min():5.1f}"
            )
            print(
                "     hod anchor-meas: "
                + " ".join(f"{v:+.0f}" for v in (ga - gm).to_numpy())
            )


def decompose(fdir: Path) -> None:
    """B: the export-hour gap, split into anchor error, measured spread and NW model error."""
    print(
        "\n## B. Export-hour decomposition ($/MWh, means over the keeper's export hours, finite meas)"
    )
    nw = pd.read_parquet(VAL / "actual_lmp_hourly_NWPP.parquet")
    for seam in ("CAISO_COI", "WECC_CAN"):
        spec = SEAMS[seam]
        for y in (2023, 2024, 2025):
            _, zp = _keeper(y)
            a = _zero_flow_anchor(spec, y)
            m = _meas_anchor(seam, y)
            nwm = _series(nw, y, "rt")
            nwk = zp[list(spec.border_zones)].to_numpy().min(axis=1)
            ext = zp[EXT[seam]].to_numpy()
            fl = _flow(fdir, y, seam)
            meas = _measured(y)[seam]
            for lab, sel in (
                ("export", fl > 1),
                ("import", fl < -1),
                ("all", np.ones(8760, bool)),
            ):
                ok = sel & np.isfinite(m) & np.isfinite(nwm)
                if ok.sum() == 0:
                    continue
                print(
                    f"{seam:9s} {y} {lab:6s} h {ok.sum():4d} | anchor {a[ok].mean():6.2f} ext-dual {ext[ok].mean():6.2f} "
                    f"meas-anchor {m[ok].mean():6.2f} | NW meas {nwm[ok].mean():6.2f} NW model {nwk[ok].mean():6.2f} | "
                    f"anchor-meas {np.mean(a[ok] - m[ok]):+6.2f} spread_meas {np.mean(m[ok] - nwm[ok]):+6.2f} "
                    f"NWmeas-NWmodel {np.mean(nwm[ok] - nwk[ok]):+6.2f} | model flow {fl[ok].mean():6.0f} meas {np.nanmean(meas[ok]):6.0f}"
                )


def marginal_class(fdir: Path) -> None:
    """C: marginal NW class in the border zones, COI/BC export vs import hours."""
    print("\n## C. Marginal units in NWPP-NW/OR by fuel (share of marginal unit-hours)")
    for y in YEARS:
        u = pd.read_parquet(
            KEEPER / f"unit_marginal_{y}.parquet",
            columns=["zone", "hour", "fuel", "plant_group", "marginal", "mc"],
        )
        u = u[(u["marginal"] == 1) & u["zone"].isin(["NWPP-NW", "NWPP-OR"])]
        fl = _flow(fdir, y, "CAISO_COI")
        exp_h = set(np.flatnonzero(fl > 1))
        u["dir"] = np.where(u["hour"].isin(exp_h), "COIexp", "other")
        t = u.groupby(["dir", "fuel"]).size().unstack(0).fillna(0)
        t = (t / t.sum()).round(3)
        mc = u.groupby(["dir", "fuel"])["mc"].median().unstack(0).round(1)
        print(f"-- {y}  (COI export hours {len(exp_h)})")
        print(t.join(mc, rsuffix="_mc_median").to_string())


def price_taker() -> None:
    """D: price-taker COI/BC flows on the keeper's NW price under candidate hurdles (measured caps).

    H0 keeper (3.0 symmetric); H1 = H0 + CARB unspecified-import GHG
    (``CARB_UNSPECIFIED_IMPORT_EF`` x the measured CARB auction price) on NW->CA
    exports only; H2 = CAISO's own measured PNW delivered basis
    (``CAISO_IMPORT_DELIVERY_BASIS['PNW_midC']``: x1.05 + $5) on NW->CA exports.
    A DIAGNOSTIC row replaces the anchor with its measured source series (an overlay,
    never an input).
    """
    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.model.interchange.spec import CAISO_IMPORT_DELIVERY_BASIS
    from market_sim.policy.cap_and_trade import measured_price

    mult, add = CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]
    print("\n## D. Price-taker TWh (export +), measured caps, on the keeper's NW price")
    for seam in ("CAISO_COI", "CAISO_NEVP", "WECC_CAN"):
        spec = SEAMS[seam]
        for y in YEARS:
            if spec.anchored_years_only and y not in (spec.hr_by_year or {}):
                continue
            _, zp = _keeper(y)
            ex, im, _ = seam_tranche_prices(spec, y, 8760)
            bz = zp[list(spec.border_zones)].to_numpy()
            lo, hi = bz.min(axis=1), bz.max(axis=1)
            step = spec.interface_limit_mw / ex.shape[0]
            imp_cap, exp_cap = nwpp_seam_limits_hourly(y, 8760).get(
                seam, (np.full(8760, np.inf), np.full(8760, np.inf))
            )

            def flow(ex_, im_, hx, hi_=spec.hurdle):
                e = ((ex_ - hx) > lo[None, :]).sum(axis=0) * step
                i = ((im_ + hi_) < hi[None, :]).sum(axis=0) * step
                return np.minimum(e, exp_cap) - np.minimum(i, imp_cap)

            cp = measured_price("CAISO", y) or 0.0
            ghg = CARB_UNSPECIFIED_IMPORT_EF * cp
            h0 = flow(ex, im, spec.hurdle)
            out = f"{seam:9s} {y} H0 {h0.sum() / 1e6:6.2f}"
            if seam.startswith("CAISO"):
                h1 = flow(ex, im, spec.hurdle + ghg)
                # H2: delivered NW cost lo*mult + add must sit below the CA tranche price.
                e2 = (ex > (lo * (1.0 + mult) + add)[None, :]).sum(axis=0) * step
                i2 = ((im + spec.hurdle) < hi[None, :]).sum(axis=0) * step
                h2 = np.minimum(e2, exp_cap) - np.minimum(i2, imp_cap)
                h12 = flow(
                    ex - (lo * mult + add)[None, :] + spec.hurdle, im, spec.hurdle + ghg
                )
                out += f" | H1 (+GHG {ghg:5.2f}) {h1.sum() / 1e6:6.2f} | H2 (x{1 + mult}+{add}) {h2.sum() / 1e6:6.2f} | H1+H2 {h12.sum() / 1e6:6.2f}"
            m = _meas_anchor(seam, y)
            if np.isfinite(m).sum() > 4000:
                a0 = _zero_flow_anchor(spec, y)
                ok = np.isfinite(m)
                scale = np.where(ok, m / a0, 1.0)
                alt = flow(ex * scale[None, :], im * scale[None, :], spec.hurdle)
                out += f" | DIAG meas-anchor {alt[ok].sum() / 1e6:6.2f} vs H0 same hours {h0[ok].sum() / 1e6:6.2f}"
            meas = _measured(y)[seam]
            out += f" | actual {np.nansum(meas) / 1e6:6.2f}"
            print(out)


def flow_vs_spread() -> None:
    """E: measured record only — measured COI/BC flow by measured spread bin (validation of any hurdle)."""
    print(
        "\n## E. Measured flow (MW, export +) by measured spread (meas anchor - NW WEIM benchmark)"
    )
    nw = pd.read_parquet(VAL / "actual_lmp_hourly_NWPP.parquet")
    bins = [-1e9, -10, -5, 0, 5, 10, 15, 20, 30, 1e9]
    for seam in ("CAISO_COI", "WECC_CAN"):
        for y in (2023, 2024, 2025):
            m, n = _meas_anchor(seam, y), _series(nw, y, "rt")
            f = _measured(y)[seam]
            ok = np.isfinite(m) & np.isfinite(n) & np.isfinite(f)
            sp = pd.cut(m[ok] - n[ok], bins)
            g = pd.Series(f[ok]).groupby(sp).agg(["count", "mean"])
            print(
                f"{seam:9s} {y}: "
                + " | ".join(
                    f"{str(k)} n{int(r['count'])} {r['mean']:.0f}"
                    for k, r in g.iterrows()
                    if r["count"] > 0
                )
            )


def main() -> None:
    """Run A-D."""
    fdir = Path(sys.argv[1])
    anchor_vs_source()
    decompose(fdir)
    marginal_class(fdir)
    price_taker()
    flow_vs_spread()


if __name__ == "__main__":
    main()
