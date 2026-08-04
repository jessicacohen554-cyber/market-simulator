"""caiso-167 PHASE 0 — the CAISO import price basis, decomposed. NO LP, NO SOLVE.

Reads **committed artifacts only**:

* the incumbent keeper bundle's P1 hourly sidecars
  (``results/calibration/caiso164_zonal_loss_surface/hourly/system_<y>.parquet``)
  for the model's zonal duals — the two WECC corridor nodes (``WECC_DSW`` /
  ``WECC_PNW``) and the two CA zones they terminate on (``SP15_rest`` / ``NP15``);
* the measured intertie scheduling-point LMP
  (``data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet``,
  ``PALOVRDE`` / ``MALIN``, hour index 0..8759 local calendar — the same series
  the keeper's own import tranches are priced off);
* CAISO's committed day-ahead component record
  (``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv``) — the CA trading hubs
  ``TH_SP15_GEN-APND`` / ``TH_NP15_GEN-APND`` for all three years, and the
  intertie APNodes ``PALOVRDE_ASR-APND`` / ``MALIN_5_N101`` for the 1,488-hour
  2023-01-01..2023-03-10 window in which they printed.

The question (mechanism-matrix §5.2 lever-queue item 2, its one live half):
**under the surplus regime, is the model's corridor wedge — the gap between a CA
zone's dual and its own import node's dual — a real market basis or a model
artifact; and can the one never-adjudicated import-side price-basis mechanism
reach it?** caiso-121 measured the model side (+$4.39/+13.53/+8.00, 59-101 % of
it corridor rent) against the *hub level*; it never measured the real
CA-hub-minus-tie basis those hours actually carry. This probe measures it, then
bounds what a seam loss surface (the caiso-164 mechanism extended to the WECC
links, which ``_caiso_internal`` excludes by construction) could move.

Four stages, printed in order:

1. ``basis``  — measured basis vs model wedge, per corridor x year x regime,
   plus a month cut on the belly-surplus mask.
2. ``census`` — the model wedge's sign distribution (a lossless link has a
   nonzero dual gap only at a bound, so this reads out corridor binding).
3. ``split``  — the measured basis decomposed into dMCC + dMCL on the committed
   intertie-component window (the caiso-164 instrument, pointed at the seam).
4. ``reach``  — the seam-loss mechanism's dual movement, at the measured eps and
   at a stress eps larger than any value in ANY committed loss surface.

Rule 13 ``[R-MEASURED]``: every number here is a measurement of committed
inputs and committed model output. Nothing is fitted, nothing is tuned, and no
value computed here is fed back into any model input.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/caiso164_zonal_loss_surface/hourly"
INTERTIE = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"
DAM = REPO / "data/raw/lmp-data/CAISO"
SURFACES = REPO / "data/raw/iso-specific-transmission"

YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: training years ONLY, fail closed.

# The two corridors, as the model builds them (``model.interchange.caiso
# .split_caiso_import_corridors``) and as the keeper prices them
# (``measured_import_hub_prices`` maps PALOVRDE -> the DSW tranches, MALIN -> the
# PNW tranches): (label, model import node, model CA zone, tie hub key, CA hub
# node, tie APNode in the component record).
CORRIDORS = (
    (
        "DSW",
        "WECC_DSW",
        "SP15_rest",
        "PALOVRDE",
        "TH_SP15_GEN-APND",
        "PALOVRDE_ASR-APND",
    ),
    ("PNW", "WECC_PNW", "NP15", "MALIN", "TH_NP15_GEN-APND", "MALIN_5_N101"),
)

# caiso-165 §2 belly window, carried verbatim: Pacific hours [09, 16).
BELLY = (9, 16)
# caiso-120's surplus-regime cut, re-expressed on the measured DAY-AHEAD CA hub
# (the model is a day-ahead-shaped LP, and the DA component record is the series
# both caiso-164 and caiso-165 decomposed). $20/MWh, unchanged.
SURPLUS_MAX = 20.0
# A dual gap this small is numerically zero (HiGHS tolerance scale).
WEDGE_TOL = 0.01
# Stress delivery-factor deviation for the reach bound: larger than the maximum
# within-month pairwise eps in ANY committed loss surface (CAISO 0.0534 /
# MISO 0.0943 / PJM 0.1275 — printed by stage 4).
STRESS_EPS = 0.13


def _hour_index(ts: pd.Series, year: int) -> np.ndarray:
    """Map GMT timestamps to the model's 0-based local-calendar hour index."""
    local = ts.dt.tz_convert("America/Los_Angeles")
    start = pd.Timestamp(f"{year}-01-01", tz="America/Los_Angeles")
    return ((local - start).dt.total_seconds() // 3600).to_numpy().astype(int)


def _dam(year: int) -> pd.DataFrame:
    frame = pd.read_csv(
        DAM / f"CAISO_dam_hourly_{year}.csv", parse_dates=["interval_start_gmt"]
    )
    frame["h"] = _hour_index(frame["interval_start_gmt"], year)
    return frame


def _model(year: int) -> pd.DataFrame:
    s = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    return s[s["pass"] == "P1"].pivot_table(
        index="hour", columns="zone", values="price"
    )


def _masks(year: int, hours: int, hub: np.ndarray) -> dict[str, np.ndarray]:
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    hod = clock.hour.to_numpy()
    belly = (hod >= BELLY[0]) & (hod < BELLY[1])
    return {
        "belly": belly,
        "surplus": belly & (hub <= SURPLUS_MAX),
        "month": clock.month.to_numpy(),
    }


def stage_basis_and_census(tie: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Stages 1 + 2 — the measured basis vs the model wedge, and its sign census."""
    basis_rows: list[dict] = []
    census_rows: list[dict] = []
    for year in YEARS:
        model = _model(year)
        hours = len(model)
        dam = _dam(year)
        for label, mnode, mzone, tiehub, cahub, _apnode in CORRIDORS:
            hub = (
                dam[dam["node"] == cahub]
                .set_index("h")["LMP"]
                .reindex(range(hours))
                .to_numpy()
            )
            ts = (
                tie[(tie["year"] == year) & (tie["hub"] == tiehub)]
                .set_index("hour")["price"]
                .reindex(range(hours))
                .to_numpy()
            )
            wedge = (model[mzone] - model[mnode]).to_numpy()
            lam = model[mnode].to_numpy()
            meas = hub - ts
            ok = np.isfinite(meas) & np.isfinite(wedge)
            mk = _masks(year, hours, hub)

            cuts = {
                "all": ok,
                "belly": ok & mk["belly"],
                "belly_surplus": ok & mk["surplus"],
            }
            for m in range(1, 13):
                mm = ok & mk["surplus"] & (mk["month"] == m)
                if mm.sum() >= 24:
                    cuts[f"belly_surplus_m{m:02d}"] = mm

            for regime, mask in cuts.items():
                if mask.sum() == 0:
                    continue
                basis_rows.append(
                    {
                        "year": year,
                        "corridor": label,
                        "regime": regime,
                        "n": int(mask.sum()),
                        "meas_basis_mean": float(meas[mask].mean()),
                        "meas_neg_pct": float(100 * (meas[mask] < -WEDGE_TOL).mean()),
                        "model_wedge_mean": float(wedge[mask].mean()),
                        "defect_mean": float((wedge[mask] - meas[mask]).mean()),
                        "ca_hub_meas_mean": float(hub[mask].mean()),
                        "ca_zone_model_mean": float(
                            model[mzone].to_numpy()[mask].mean()
                        ),
                        "tie_meas_mean": float(ts[mask].mean()),
                        "tie_model_mean": float(lam[mask].mean()),
                    }
                )

            k = cuts["belly_surplus"]
            census_rows.append(
                {
                    "year": year,
                    "corridor": label,
                    "n": int(k.sum()),
                    "wedge_pos_pct": float(100 * (wedge[k] > WEDGE_TOL).mean()),
                    "wedge_zero_pct": float(
                        100 * (np.abs(wedge[k]) <= WEDGE_TOL).mean()
                    ),
                    "wedge_neg_pct": float(100 * (wedge[k] < -WEDGE_TOL).mean()),
                    "meas_neg_pct": float(100 * (meas[k] < -WEDGE_TOL).mean()),
                    "tie_lam_neg_pct": float(100 * (lam[k] < 0).mean()),
                    "tie_lam_absmean": float(np.abs(lam[k]).mean()),
                }
            )
    return basis_rows, census_rows


def stage_split() -> tuple[list[dict], dict[str, float]]:
    """Stage 3 — decompose the measured seam basis into dMCC + dMCL, and derive eps.

    Only the 2023-01-01..2023-03-10 window carries intertie components in
    ``data/raw``; the belly months do not, which is stated as a coverage limit
    rather than papered over.
    """
    dam = _dam(2023)
    piv = {
        c: dam.pivot_table(index="h", columns="node", values=c)
        for c in ("LMP", "MCE", "MCC", "MCL")
    }
    rows: list[dict] = []
    eps: dict[str, float] = {}
    for label, _mn, _mz, _th, cahub, apnode in CORRIDORS:
        if apnode not in piv["LMP"].columns:
            continue
        frame = pd.DataFrame(
            {
                "basis": piv["LMP"][cahub] - piv["LMP"][apnode],
                "dMCC": piv["MCC"][cahub] - piv["MCC"][apnode],
                "dMCL": piv["MCL"][cahub] - piv["MCL"][apnode],
                "dMCE": piv["MCE"][cahub] - piv["MCE"][apnode],
            }
        ).dropna()
        hod = pd.Series(frame.index % 24, index=frame.index)
        for name, sub in (
            ("all", frame),
            ("belly", frame[(hod >= BELLY[0]) & (hod < BELLY[1])]),
        ):
            rows.append(
                {
                    "corridor": label,
                    "window": "2023-01-01..2023-03-10",
                    "cut": name,
                    "n": int(len(sub)),
                    "basis_mean": float(sub.basis.mean()),
                    "dMCC_mean": float(sub.dMCC.mean()),
                    "dMCL_mean": float(sub.dMCL.mean()),
                    "loss_share_pct": float(100 * sub.dMCL.mean() / sub.basis.mean()),
                    "dMCE_absmax": float(sub.dMCE.abs().max()),
                }
            )
        # eps on the caiso-164 frozen estimator, per month, max over the window.
        sub = dam[dam["node"].isin([cahub, apnode])]
        common = piv["LMP"][[cahub, apnode]].dropna().index
        sub = sub[sub["h"].isin(common)]
        sub = sub.assign(
            mon=sub["interval_start_gmt"].dt.tz_convert("America/Los_Angeles").dt.month
        )
        dev = sub.groupby(["node", "mon"]).apply(
            lambda g: g["MCL"].sum() / g["MCE"].sum(), include_groups=False
        )
        per_month = [
            max(0.0, (dev[(cahub, m)] - dev[(apnode, m)]) / (1 + dev[(cahub, m)]))
            for m in sorted({m for _n, m in dev.index})
            if (cahub, m) in dev.index and (apnode, m) in dev.index
        ]
        eps[label] = float(max(per_month))
    return rows, eps


def stage_reach(tie: pd.DataFrame, eps: dict[str, float]) -> list[dict]:
    """Stage 4 — bound the dual movement a seam loss surface could produce.

    ``reach_signed`` is the physical quantity: a receiving-end coefficient
    ``1 - eps`` sets ``lambda_to = lambda_from / (1 - eps)`` on an interior link,
    so the wedge moves by ``lambda_from * eps / (1 - eps)`` — which is NEGATIVE
    wherever the import node prices below zero. ``reach_upper`` is deliberately
    over-generous: it takes ``|lambda|`` (no cancellation) over ALL hours,
    including the ones where the corridor is at a bound and the bound, not the
    loss, sets the wedge.
    """
    rows: list[dict] = []
    for year in YEARS:
        model = _model(year)
        hours = len(model)
        dam = _dam(year)
        for label, mnode, mzone, tiehub, cahub, _ap in CORRIDORS:
            hub = (
                dam[dam["node"] == cahub]
                .set_index("h")["LMP"]
                .reindex(range(hours))
                .to_numpy()
            )
            ts = (
                tie[(tie["year"] == year) & (tie["hub"] == tiehub)]
                .set_index("hour")["price"]
                .reindex(range(hours))
                .to_numpy()
            )
            wedge = (model[mzone] - model[mnode]).to_numpy()
            lam = model[mnode].to_numpy()
            ok = np.isfinite(hub - ts) & np.isfinite(wedge)
            k = ok & _masks(year, hours, hub)["surplus"]
            defect = float((wedge[k] - (hub - ts)[k]).mean())
            interior = np.abs(wedge[k]) <= WEDGE_TOL
            for tag, e in (("measured", eps[label]), ("stress", STRESS_EPS)):
                f = e / (1 - e)
                rows.append(
                    {
                        "year": year,
                        "corridor": label,
                        "eps": tag,
                        "eps_val": round(e, 5),
                        "n": int(k.sum()),
                        "defect_mean": round(defect, 3),
                        "reach_signed": round(float((lam[k] * f).mean()), 3),
                        "reach_signed_interior_only": round(
                            float((lam[k][interior] * f).mean() * interior.mean()), 3
                        ),
                        "reach_upper_bound": round(
                            float((np.abs(lam[k]) * f).mean()), 3
                        ),
                        "reach_upper_pct_of_defect": round(
                            100 * float((np.abs(lam[k]) * f).mean()) / abs(defect), 1
                        ),
                    }
                )
    return rows


def surface_eps_ceiling() -> dict[str, float]:
    """Max within-month pairwise eps in each committed loss surface (stress justification)."""
    out: dict[str, float] = {}
    for iso in ("CAISO", "PJM", "MISO"):
        frame = pd.read_csv(SURFACES / f"{iso}_loss_surface.csv")
        best = 0.0
        for _key, grp in frame.groupby(["year", "month"]):
            a = grp["df_deviation"].to_numpy()
            best = max(
                best, float(np.nanmax((a[:, None] - a[None, :]) / (1 + a[:, None])))
            )
        out[iso] = round(best, 5)
    return out


def main() -> None:
    tie = pd.read_parquet(INTERTIE)
    basis, census = stage_basis_and_census(tie)
    split, eps = stage_split()
    ceiling = surface_eps_ceiling()
    reach = stage_reach(tie, eps)

    pd.set_option("display.width", 230)
    fmt = lambda v: f"{v:8.3f}"  # noqa: E731
    b = pd.DataFrame(basis)
    print(
        "== 1. measured basis (CA hub - tie) vs model wedge (CA zone - import node) =="
    )
    print(b[~b.regime.str.contains("_m")].to_string(index=False, float_format=fmt))
    print("\n-- month cut, belly-surplus --")
    print(b[b.regime.str.contains("_m")].to_string(index=False, float_format=fmt))
    print(
        "\n== 2. model wedge sign census, belly-surplus (lossless seam: nonzero <=> at a bound) =="
    )
    print(pd.DataFrame(census).to_string(index=False, float_format=fmt))
    print(
        "\n== 3. measured seam basis decomposed (committed intertie-component window only) =="
    )
    print(pd.DataFrame(split).to_string(index=False, float_format=fmt))
    print(
        f"\n   derived seam eps (caiso-164 frozen estimator, max over window months): {eps}"
    )
    print(
        f"   max within-month pairwise eps in committed surfaces: {ceiling}  -> stress eps {STRESS_EPS}"
    )
    print("\n== 4. seam-loss reach bound vs the measured defect ==")
    print(pd.DataFrame(reach).to_string(index=False, float_format=fmt))

    dest = REPO / "results/calibration/_caiso167_import_basis_phase0.json"
    dest.write_text(
        json.dumps(
            {
                "basis": basis,
                "census": census,
                "split": split,
                "seam_eps": eps,
                "surface_eps_ceiling": ceiling,
                "stress_eps": STRESS_EPS,
                "reach": reach,
            },
            indent=1,
        )
    )
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
