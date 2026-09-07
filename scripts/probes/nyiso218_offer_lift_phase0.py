"""nyiso-218 phase 0 — the ZERO-LP pre-solve census for the +3.0 % fossil
energy-band offer lift (owner ruling R1, 2026-09-07).

Rule 29 ``[R-SCREEN]`` step 0. Two measurements, both from committed artifacts
plus a no-LP fleet rebuild — **no LP is solved here**:

**Part A — the offer-array delta (construction check).** The keeper's fleet is
rebuilt twice per year through ``scripts/lib/bundle_fleet`` (``fleet_only=True``,
the ``nyiso215_reserve_duty_census`` dual-rebuild pattern): once on the keeper
recipe, once with ``offer_curve_overrides`` carrying ``committed`` /
``econ_low`` / ``econ_high`` multiplied by exactly 1.03 on every one of the 13
fossil groups in ``offer_curve_by_group``, every ``peak`` band and every
``phys_*`` key left at its keeper value. The check is on the delivered
``mc_base`` (which already carries ``apply_gas_offer_margin``, applied upstream
of the ``fleet_only`` exit): every ``peak*``, ``mustrun``, ``sync`` and
non-fossil row must move by EXACTLY 0.0, and the moved set must be exactly the
three energy bands of the 13 groups. A non-zero peak delta is a
stop-the-line construction bug, not a result.

**Part B — the price-setting census and the passthrough prediction.** For each
hour and zone the marginal tranche is identified by matching the committed
``system_<year>.parquet`` zonal ``price`` against the rebuilt control fleet's
own ``mc_base`` (best match in that zone among rows dispatching in that hour, per
``class_hourly``-consistent zone assignment), and the predicted C3a response is
the load-weighted mean of the matched tranche's own Δmc. C3a's model statistic is
reproduced exactly as ``calibration_verdict.score_price_mean`` computes it —
the zonal mean price weighted by that zone's demand — so the prediction is on
the criterion's own basis.

ZERO LP. Nothing here is gated on a residual (rule 1 ``[R-STRUCT]``): the screen
year is chosen in Part B by the mechanism's own measured footprint, never by the
size of a price error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

BUNDLE = ROOT / "results/calibration/nyiso213_summer_seam"
OUT = ROOT / "results/calibration/_nyiso218_offer_lift_phase0.json"
YEARS = (2023, 2024, 2025)

#: The rule-22 validation touchpoint bundle. 2022 is REPORTED here as the
#: owner's stated MOTIVATION only — already SPENT twice on this recipe, read
#: from its COMMITTED sidecar, never a gate and never a target (rule 22).
TP2022 = ROOT / "results/calibration/nyiso213_tp2022"

#: Owner ruling R1 (2026-09-07): the three ENERGY bands only, x 1.03 exactly.
#: Every ``peak`` band is frozen; ``phys_*`` and the structural shares
#: (``econ_low_share``, ``pct_peaking``) are untouched (rule 1 forbids both).
LIFT = 1.03
LIFT_BANDS = ("committed", "econ_low", "econ_high")
FROZEN_BANDS = ("peak",)

#: The 13 fossil groups the keeper's ``offer_curve_by_group`` carries. ST_CHP is
#: fossil but has NO entry, so the channel provably does not reach it.
FOSSIL_GROUPS = frozenset(
    {
        "CC_CHP",
        "CC_INTERMEDIATE",
        "CC_REGULAR",
        "COAL",
        "COAL_BIT",
        "COAL_LIGNITE",
        "COAL_PRB",
        "COAL_WC",
        "CT_CHP",
        "CT_INTERMEDIATE",
        "CT_PEAKER",
        "ST_GAS",
        "ST_GAS_INTERMEDIATE",
    }
)


def lifted_overrides(curve: dict) -> dict:
    """Return the ``offer_curve_overrides`` deep-merge payload for the arm."""
    out: dict[str, dict[str, float]] = {}
    for group, bands in sorted(curve.items()):
        moved = {b: bands[b] * LIFT for b in LIFT_BANDS if b in bands}
        if moved:
            out[group] = moved
    return out


def _build(year: int, meta: dict, **over: object) -> dict:
    """Rebuild the keeper's fleet for ``year`` (no LP), with optional overrides."""
    import scripts.run_calibration as rc

    kwargs = full_run_year_kwargs(meta)
    kwargs.update(over)
    clear_fleet_caches()
    return rc.run_year(year, "NYISO", 8760, bundle_gas_price(meta, year), **kwargs)


def _band_of(uid: str) -> str:
    """Return the band suffix of an LP tranche unit id (bins_to_fleet vocabulary)."""
    for suffix in (
        "mustrun",
        "sync",
        "committed",
        "econlo",
        "econhi",
        "econ",
        "peak",
    ):
        if f"_{suffix}" in uid:
            return suffix
    return ""


def _row_frame(built: dict) -> pd.DataFrame:
    """One row per LP unit: uid, band, group, zone, pmax, mc row index."""
    fa = built["fleet_arrays"]
    gens = built["fleet"]
    if len(gens) != len(fa.unit_ids):
        raise SystemExit("fleet / fleet_arrays misalignment — instrument invalid")
    uids = [str(u) for u in fa.unit_ids]
    return pd.DataFrame(
        {
            "uid": uids,
            "band": [_band_of(u) for u in uids],
            "group": list(fa.plant_group),
            "zone": [g.zone for g in gens],
            "pmax": np.asarray(fa.pmax, dtype=float),
            "row": np.arange(len(uids)),
        }
    )


def _mc2d(built: dict, hours: int) -> np.ndarray:
    """Return ``mc_base`` as a dense ``(n_gen, T)`` float array."""
    mc = np.asarray(built["mc_base"], dtype=float)
    return mc if mc.ndim == 2 else np.repeat(mc[:, None], hours, axis=1)


def part_a(year: int, meta: dict, curve: dict) -> dict:
    """Measure the offer-array delta between control and arm."""
    ctl = _build(year, meta)
    arm = _build(year, meta, offer_curve_overrides=lifted_overrides(curve))
    frame = _row_frame(ctl)
    frame_arm = _row_frame(arm)
    if list(frame["uid"]) != list(frame_arm["uid"]):
        raise SystemExit("arm/control unit-id misalignment — instrument invalid")
    hours = int(meta.get("hours", 8760))
    mc_c, mc_a = _mc2d(ctl, hours), _mc2d(arm, hours)
    d = mc_a - mc_c
    frame["d_max"] = np.abs(d).max(axis=1)
    frame["d_mean"] = d.mean(axis=1)
    frame["mc_mean"] = mc_c.mean(axis=1)
    frame["rel_mean"] = np.where(
        frame["mc_mean"] > 0, frame["d_mean"] / frame["mc_mean"], 0.0
    )
    fossil = set(curve)
    moved = frame[frame["d_max"] > 0]
    frozen_moved = moved[moved["band"].isin(("peak", "mustrun", "sync", ""))]
    nonfossil_moved = moved[~moved["group"].isin(fossil)]
    by_band = (
        frame[frame["band"].isin(("committed", "econlo", "econhi", "econ"))]
        .groupby(["group", "band"])
        .agg(
            n=("uid", "size"),
            n_moved=("d_max", lambda s: int((s > 0).sum())),
            rel_mean=("rel_mean", "mean"),
            d_mean=("d_mean", "mean"),
        )
        .reset_index()
    )
    return {
        "year": year,
        "n_rows": int(len(frame)),
        "n_moved": int(len(moved)),
        "frozen_band_rows_moved": int(len(frozen_moved)),
        "frozen_band_rows_moved_uids": list(frozen_moved["uid"])[:20],
        "nonfossil_rows_moved": int(len(nonfossil_moved)),
        "nonfossil_rows_moved_uids": list(nonfossil_moved["uid"])[:20],
        "moved_bands": sorted(moved["band"].unique().tolist()),
        "moved_groups": sorted(moved["group"].unique().tolist()),
        "by_band": by_band.round(6).to_dict("records"),
        "_frame": frame,
        "_d": d,
        "_mc_c": mc_c,
    }


def part_b(year: int, a: dict, bundle: Path) -> dict:
    """Price-setting census + the load-weighted C3a passthrough prediction.

    C3a's model statistic is reproduced on the committed payload's OWN basis:
    each zone's ``p`` is the DEMAND-WEIGHTED mean of its hourly price (not the
    simple mean), and the system statistic is those zonal means weighted by
    zonal demand TWh. The predicted response is the same double-weighted mean
    of the matched marginal tranche's own Δmc.

    The marginal tranche is identified two ways and BOTH are reported, because
    neither is exact under a zonal loss surface plus congestion: ``inzone``
    (best mc match among rows in that zone) and ``system`` (best match among
    all rows). Each carries its match residual and a CLEAN-MATCH restriction
    (residual ≤ 1 % of price) with its own coverage, so a weak identification is
    visible rather than absorbed.
    """
    sysdf = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    frame, d, mc_c = a["_frame"], a["_d"], a["_mc_c"]
    energy = (
        frame["band"].isin(("committed", "econlo", "econhi", "econ"))
        & frame["group"].isin(FOSSIL_GROUPS)
    ).to_numpy()
    zones = sorted(z for z in sysdf["zone"].unique() if z != "NYISO_external")
    out_modes: dict[str, dict] = {}
    zone_demand: dict[str, float] = {}
    zone_price: dict[str, float] = {}
    for mode in ("inzone", "system"):
        per_zone: dict[str, dict] = {}
        for zone in zones:
            zdf = sysdf[sysdf["zone"] == zone].sort_values("hour")
            price = zdf["price"].to_numpy(dtype=float)
            dem = zdf["demand"].to_numpy(dtype=float)
            rows = (
                frame.index[frame["zone"] == zone].to_numpy()
                if mode == "inzone"
                else frame.index.to_numpy()
            )
            if rows.size == 0:
                continue
            mcz = mc_c[rows, : len(price)]
            idx = np.abs(mcz - price[None, :]).argmin(axis=0)
            cols = np.arange(len(price))
            resid = np.abs(mcz[idx, cols] - price)
            setter = rows[idx]
            dz = d[rows, : len(price)][idx, cols]
            clean = resid <= 0.01 * np.abs(price)
            wsum = dem.sum()
            per_zone[zone] = {
                "energy_band_setting_share": float(
                    np.average(energy[setter], weights=dem)
                ),
                "match_resid_p50": float(np.median(resid)),
                "match_resid_p90": float(np.percentile(resid, 90)),
                "clean_match_share": float(clean.mean()),
                "p_demand_weighted": float((price * dem).sum() / wsum),
                "pred_dp_demand_weighted": float((dz * dem).sum() / wsum),
                "pred_dp_clean_only": (
                    float((dz[clean] * dem[clean]).sum() / dem[clean].sum())
                    if clean.any()
                    else None
                ),
                "demand_twh": float(wsum / 1e6),
            }
            zone_demand[zone] = float(wsum)
            zone_price[zone] = per_zone[zone]["p_demand_weighted"]
        den = sum(zone_demand[z] for z in per_zone)
        lw_price = sum(zone_price[z] * zone_demand[z] for z in per_zone) / den
        lw_dp = (
            sum(per_zone[z]["pred_dp_demand_weighted"] * zone_demand[z] for z in per_zone)
            / den
        )
        share = sum(
            per_zone[z]["energy_band_setting_share"] * zone_demand[z] for z in per_zone
        ) / den
        out_modes[mode] = {
            "lw_mean_price_reproduced": round(lw_price, 4),
            "fossil_energy_band_setting_share_lw": round(share, 6),
            "pred_d_lw_price_usd_mwh": round(lw_dp, 4),
            "pred_d_lw_price_pct": round(100.0 * lw_dp / lw_price, 4),
            "per_zone": {
                k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                for k, v in per_zone.items()
            },
        }
    return {"year": year, "modes": out_modes}


def main() -> None:
    ensure_probe_path()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    curve = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"][
        "offer_curve_by_group"
    ]
    over = lifted_overrides(curve)
    out: dict = {
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "lift": LIFT,
        "lift_bands": list(LIFT_BANDS),
        "frozen_bands": list(FROZEN_BANDS),
        "n_groups_lifted": len(over),
        "overrides": over,
        "part_a": [],
        "part_b": [],
    }
    for year, bundle in [(y, BUNDLE) for y in YEARS] + [(2022, TP2022)]:
        a = part_a(year, meta, curve)
        b = part_b(year, a, bundle)
        for k in ("_frame", "_d", "_mc_c"):
            a.pop(k)
        out["part_a"].append(a)
        out["part_b"].append(b)
        print(
            f"{year}: moved rows {a['n_moved']}/{a['n_rows']}, frozen-band moved "
            f"{a['frozen_band_rows_moved']}, non-fossil moved "
            f"{a['nonfossil_rows_moved']}, setting share "
            f"{b['modes']['inzone']['fossil_energy_band_setting_share_lw']:.4f}, "
            f"pred dP inzone {b['modes']['inzone']['pred_d_lw_price_usd_mwh']:+.4f} "
            f"({b['modes']['inzone']['pred_d_lw_price_pct']:+.3f} %) | system "
            f"{b['modes']['system']['pred_d_lw_price_usd_mwh']:+.4f} "
            f"({b['modes']['system']['pred_d_lw_price_pct']:+.3f} %)",
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
