"""nyiso-203 phase 0 — re-derive the NYC ST_GAS persistent-base limb's BASIS per unit.

ZERO LP. Source data ONLY (rule 23 ``[R-FROZEN-DERIVE]``, rule 1 ``[R-STRUCT]``): the same
CAMPD unit-level extract, guard-corrected outage extract, bin assignments and archived zone
TMAX that :mod:`scripts.data.derive_nyiso_st_reliability_floor` reads. No metrics file, no
solve output, no price/volume residual is opened at any point.

THE OBJECT — the one live ``NYISO,NYC,ST_GAS,tmax,-50.0`` row of
``data/raw/reference/reliability_floor_coeffs_NYISO.csv``::

    driver=tmax  threshold=-50.0 C  floor_pct=0.175  distribution=pro_rata
    exclude_plant_codes: (empty)
    basis: "persistent 24h base: base_24h (when-available cool-day CF p25)"

A -50 C ``tmax`` threshold is never not met, so the limb binds in all 8,760 hours, and
``pro_rata`` (``model/interchange/core.py::_apply_frac``) floors EVERY unit of the class in
the zone at ``0.175 x pmax x availability[t]``.

The basis is a FLEET-AGGREGATE, DAILY-MEAN cool-day when-available CF p25, applied PER UNIT
and HOURLY. That is the identical pair of basis divergences nyiso-140 diagnosed on
Long_Island, where they CANCELLED (hourly-p25-excluding-the-laid-up-plant 0.2666 vs frozen
0.2620) so the correction was membership-only at zero DOF. On NYC the membership question is
already CLOSED NEGATIVE (nyiso-201 §5: Astoria 8906 is 0 of 18 zero-cells, pooled median
166 MW, online 66.7 %) — so this probe asks the OTHER half: with no laid-up member to deflate
the aggregate, do the two errors still cancel?

Reported, per unit and for the fleet:

  * **Step 0** — the frozen coefficient reproduced from source, so every gap below is a basis
    difference and not a pipeline difference.
  * **A** — cool-day when-available CF by hour block per plant, plus P(CF=0) and online share:
    nyiso-140 §2's window test, repeated for NYC.
  * **B** — the 2x2 basis grid: {daily-mean, hourly} x {fleet-aggregate, per-unit}.
  * **C** — the forced-energy accounting the floor actually produces: observed vs floored vs
    added TWh per plant (nyiso-140 §3's table).

Reproduce with ``uv run python scripts/probes/_nyiso203_nyc_persistent_base_basis.py``.
Writes its machine record to ``results/calibration/_nyiso203_nyc_base_phase0.json``.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR, REPO_ROOT

ZONE = "NYC"
PLANT_CLASS = "ST_GAS"
YEARS = (2023, 2024, 2025)
T0_C = 25.0  # the derive script's cool/hot split
FROZEN_FLOOR_PCT = 0.175  # the live limb's coefficient, for the step-0 identity
HOUR_BLOCKS = {
    "h00-05": range(0, 6),
    "h06-13": range(6, 14),
    "h14-21": range(14, 22),
    "h22-23": range(22, 24),
}
OUT = REPO_ROOT / "results" / "calibration" / "_nyiso203_nyc_base_phase0.json"


def zone_plants() -> dict[int, float]:
    """Return ``{plant_code: bin nameplate MW}`` for the zone's floored class."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    z = b[(b["Plant_Group"] == PLANT_CLASS) & (b["Zone"] == ZONE)]
    return dict(zip(z["Plant_Code"].astype(int), z["Nameplate_MW"].astype(float)))


def plant_names() -> dict[int, str]:
    """Return ``{plant_code: plant name}`` for reporting."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    z = b[(b["Plant_Group"] == PLANT_CLASS) & (b["Zone"] == ZONE)]
    return dict(zip(z["Plant_Code"].astype(int), z["Plant_Name"].astype(str)))


def plant_available_capacity(
    code: int, nameplate: float, index: pd.DatetimeIndex
) -> pd.Series:
    """Hourly AVAILABLE capacity (MW) for ONE plant.

    The per-plant restriction of ``derive_nyiso_st_reliability_floor.zone_available_capacity``
    — same extract, same ``unit_capacity_mw / plant_capacity_mw`` normalised share basis (CAMPD
    splits steam reheat/superheat sections into rows each carrying the full section nameplate,
    so the raw caps sum to ~2x plant nameplate). Summing these over a zone's plants reproduces
    the fleet series exactly, which is what makes the aggregate/per-unit comparison like-for-like.
    """
    avail = pd.Series(nameplate, index=index)
    path = RAW_DIR / "campd-unit-outages-NYISO.csv"
    if not path.exists():
        return avail
    o = pd.read_csv(path)
    o["facility_id"] = pd.to_numeric(o["facility_id"], errors="coerce")
    o = o[o["facility_id"] == code].copy()
    o["outage_start"] = pd.to_datetime(o["outage_start"])
    o["outage_end"] = pd.to_datetime(o["outage_end"])
    for _, e in o.iterrows():
        pcap = float(e["plant_capacity_mw"]) or 1.0
        share_mw = nameplate * float(e["unit_capacity_mw"]) / pcap
        mask = (index >= e["outage_start"]) & (index < e["outage_end"])
        avail.loc[mask] -= share_mw
    return avail.clip(lower=0.0)


def load_hourly() -> tuple[pd.DataFrame, dict[int, float]]:
    """Return the pooled per-plant hourly ``gross``/``avail``/``tmax`` frame."""
    npl = zone_plants()
    arch = pd.read_csv(
        RAW_DIR / "nyiso-weather" / "nyiso_zone_tmax_daily.csv", parse_dates=["date"]
    )
    zt = arch[arch["zone"] == ZONE].set_index("date")["tmax_c"]
    frames = []
    for yr in YEARS:
        c = pd.read_parquet(RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet")
        c = c[c["facilityId"].astype(int).isin(npl)].copy()
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        c["code"] = c["facilityId"].astype(int)
        gross = c.groupby(["code", "ts"])["grossLoad"].sum().rename("gross")
        idx = gross.index.get_level_values("ts").unique().sort_values()
        for code, cap in npl.items():
            av = plant_available_capacity(code, cap, idx)
            g = (
                gross.loc[code].reindex(idx).fillna(0.0)
                if code in gross.index.get_level_values("code")
                else pd.Series(0.0, index=idx)
            )
            frames.append(
                pd.DataFrame(
                    {
                        "year": yr,
                        "code": code,
                        "ts": idx,
                        "gross": g.to_numpy(),
                        "avail": av.to_numpy(),
                    }
                )
            )
    df = pd.concat(frames, ignore_index=True)
    df["date"] = df["ts"].dt.normalize()
    df["hour"] = df["ts"].dt.hour
    df["tmax"] = df["date"].map(zt)
    return df.dropna(subset=["tmax"]), npl


def p25(x: pd.Series) -> float:
    """The derive script's p25 (pandas linear interpolation), guarded for emptiness."""
    return float(x.quantile(0.25)) if len(x) else float("nan")


def main() -> None:  # noqa: PLR0915 - a report, printed in the order it is read
    """Print the per-unit basis re-derivation and write the machine record."""
    df, npl = load_hourly()
    names = plant_names()
    rec: dict = {
        "object": {
            "iso": "NYISO",
            "zone": ZONE,
            "plant_class": PLANT_CLASS,
            "driver": "tmax",
            "threshold_c": -50.0,
            "frozen_floor_pct": FROZEN_FLOOR_PCT,
            "distribution": "pro_rata",
            "exclude_plant_codes": [],
        },
        "years": list(YEARS),
        "plants": {},
    }

    cool = df[df["tmax"] < T0_C]

    # --- step 0: reproduce the frozen coefficient from source -----------------
    # The derive script's construction: FLEET gross / FLEET avail, aggregated to a
    # DAILY mean over all 24 h, p25 over cool days, pooled across years.
    fleet_day = cool.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
    daily24 = (
        (fleet_day["gross"] / fleet_day["avail"]).where(fleet_day["avail"] > 0).dropna()
    )
    base24_frozen = p25(daily24)
    print("=== STEP 0 — the frozen coefficient, reproduced from source ===")
    print(
        f"  base_24h (fleet-aggregate, DAILY-MEAN cool-day when-avail CF p25)"
        f" = {base24_frozen:.4f}"
    )
    print(
        f"  frozen floor_pct in reliability_floor_coeffs_NYISO.csv         "
        f" = {FROZEN_FLOOR_PCT:.4f}"
    )
    rec["step0"] = {
        "reproduced_base_24h": base24_frozen,
        "frozen_floor_pct": FROZEN_FLOOR_PCT,
        "abs_gap": abs(base24_frozen - FROZEN_FLOOR_PCT),
    }

    # --- A: the window test, per plant (nyiso-140 section 2 repeated) ---------
    print(
        f"\n=== A — cool-day (tmax < {T0_C:.0f}C) when-available CF by hour block,"
        " per plant ==="
    )
    hdr = f"  {'plant':<34}{'MW':>8}" + "".join(f"{b:>10}" for b in HOUR_BLOCKS)
    print(hdr + f"{'P(CF=0)':>10}{'online':>9}")
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        p = cool[cool["code"] == code]
        cf = (p["gross"] / p["avail"]).where(p["avail"] > 0)
        blocks = {}
        for bname, hrs in HOUR_BLOCKS.items():
            blocks[bname] = float(cf[p["hour"].isin(hrs)].median())
        pzero = float((cf.fillna(0.0) <= 0.0).mean())
        allp = df[df["code"] == code]
        online = float((allp["gross"] > 0.0).mean())
        label = f"{names[code]} {code}"[:33]
        print(
            f"  {label:<34}{cap:>8.0f}"
            + "".join(f"{blocks[b]:>10.3f}" for b in HOUR_BLOCKS)
            + f"{pzero:>10.3f}{online:>9.3f}"
        )
        rec["plants"][str(code)] = {
            "name": names[code],
            "nameplate_mw": cap,
            "cool_day_median_cf_by_block": blocks,
            "cool_hour_zero_share": pzero,
            "online_share": online,
        }

    # --- B: the 2x2 basis grid ------------------------------------------------
    # rows: how the CF is AGGREGATED IN TIME (daily-mean, as identified, vs hourly,
    #       as the floor is APPLIED); columns: over WHAT population (fleet aggregate,
    #       as identified, vs the unit itself, as the floor is APPLIED).
    fleet_hourly = cool.groupby("ts").agg(
        gross=("gross", "sum"), avail=("avail", "sum")
    )
    hcf = (
        (fleet_hourly["gross"] / fleet_hourly["avail"])
        .where(fleet_hourly["avail"] > 0)
        .dropna()
    )
    fleet_hourly_p25 = p25(hcf)
    print("\n=== B — the 2x2 basis grid: {time aggregation} x {population} ===")
    print(f"  {'basis':<44}{'fleet-aggregate':>18}")
    print(f"  {'DAILY-MEAN p25  (as IDENTIFIED = frozen)':<44}{base24_frozen:>18.4f}")
    print(f"  {'HOURLY p25      (as APPLIED)':<44}{fleet_hourly_p25:>18.4f}")
    per_unit = {}
    print(
        "\n  per-unit HOURLY p25 (the basis the floor is actually applied on, per unit):"
    )
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        p = cool[cool["code"] == code]
        cf = (p["gross"] / p["avail"]).where(p["avail"] > 0).dropna()
        pu_h = p25(cf)
        pday = p.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
        pu_d = p25((pday["gross"] / pday["avail"]).where(pday["avail"] > 0).dropna())
        per_unit[str(code)] = {"hourly_p25": pu_h, "daily_mean_p25": pu_d}
        print(
            f"    {names[code] + ' ' + str(code):<42}{pu_h:>18.4f}   (daily-mean {pu_d:.4f})"
        )
    rec["basis_grid"] = {
        "fleet_daily_mean_p25": base24_frozen,
        "fleet_hourly_p25": fleet_hourly_p25,
        "per_unit": per_unit,
    }

    # --- C: what the floor actually forces, per plant --------------------------
    # floored energy = frac x pmax x availability, summed; observed = metered gross.
    # "added" is the excess of the floor over measured conduct in the SAME hours,
    # i.e. sum(max(0, floor - gross)) — the energy the LP is compelled to manufacture.
    print(
        f"\n=== C — what pro_rata at {FROZEN_FLOOR_PCT} forces, per plant, "
        f"pooled {YEARS[0]}-{YEARS[-1]} (TWh) ==="
    )
    print(
        f"  {'plant':<34}{'observed':>10}{'floored':>10}{'added':>10}{'x own out':>11}"
    )
    tot = {"observed": 0.0, "floored": 0.0, "added": 0.0}
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        p = df[df["code"] == code]
        floor_mw = FROZEN_FLOOR_PCT * p["avail"]
        obs = float(p["gross"].sum()) / 1e6
        flo = float(floor_mw.sum()) / 1e6
        add = float(np.maximum(0.0, floor_mw - p["gross"]).sum()) / 1e6
        tot["observed"] += obs
        tot["floored"] += flo
        tot["added"] += add
        print(
            f"  {names[code] + ' ' + str(code):<34}{obs:>10.3f}{flo:>10.3f}{add:>10.3f}"
            f"{add / obs if obs else float('nan'):>11.2f}"
        )
        rec["plants"][str(code)]["forcing_twh"] = {
            "observed": obs,
            "floored": flo,
            "added": add,
        }
    print(
        f"  {'FLEET':<34}{tot['observed']:>10.3f}{tot['floored']:>10.3f}{tot['added']:>10.3f}"
    )
    rec["fleet_forcing_twh"] = tot
    for code in npl:
        a = rec["plants"][str(code)]["forcing_twh"]["added"]
        rec["plants"][str(code)]["share_of_fleet_added"] = (
            a / tot["added"] if tot["added"] else 0.0
        )
        o = rec["plants"][str(code)]["forcing_twh"]["observed"]
        rec["plants"][str(code)]["share_of_fleet_observed"] = (
            o / tot["observed"] if tot["observed"] else 0.0
        )

    # --- D: the basis the floor is APPLIED on, measured on its own terms ------
    # ``_apply_frac`` sets ``min_gen[r,t] = frac x pmax[r] x avail[r,t]``, so ``frac`` is
    # asserted as a PER-UNIT-HOUR capacity factor. Its measured analogue is therefore the
    # p25 of the pooled (unit, hour) when-available CF distribution — the SAME scalar in the
    # SAME CSV cell, re-derived on the population the coefficient is applied to instead of
    # on the fleet sum. The gap between the two is Jensen's inequality on a percentile: the
    # p25 of a SUM is not the sum of per-unit p25s unless the units' low hours coincide.
    cool_cf = (cool["gross"] / cool["avail"]).where(cool["avail"] > 0)
    ok = cool_cf.notna()
    pooled_unweighted = p25(cool_cf[ok])
    w = cool.loc[ok, "avail"].to_numpy()
    v = cool_cf[ok].to_numpy()
    order = np.argsort(v, kind="stable")
    cw = np.cumsum(w[order]) / w.sum()
    pooled_capweighted = float(v[order][np.searchsorted(cw, 0.25)])
    sum_unit_p25_mw = sum(
        per_unit[str(c)]["hourly_p25"] * cap for c, cap in npl.items()
    )
    fleet_p25_mw = fleet_hourly_p25 * sum(npl.values())
    print("\n=== D — the coefficient re-derived on the population it is APPLIED to ===")
    print(
        f"  fleet-aggregate hourly p25 (identified)          = {fleet_hourly_p25:.4f}"
        f"   = {fleet_p25_mw:>7.1f} MW at full availability"
    )
    print(
        f"  sum of the three per-unit hourly p25s            =         "
        f"   = {sum_unit_p25_mw:>7.1f} MW at full availability"
    )
    print(
        f"  pooled per-UNIT-hour p25, capacity-weighted      = {pooled_capweighted:.4f}"
    )
    print(
        f"  pooled per-UNIT-hour p25, unweighted             = {pooled_unweighted:.4f}"
    )
    rec["applied_basis"] = {
        "fleet_hourly_p25": fleet_hourly_p25,
        "fleet_hourly_p25_mw": fleet_p25_mw,
        "sum_per_unit_p25_mw": sum_unit_p25_mw,
        "pooled_unit_hour_p25_capweighted": pooled_capweighted,
        "pooled_unit_hour_p25_unweighted": pooled_unweighted,
    }

    # --- E: how often the asserted floor is above the unit's own conduct -------
    # Rule 17 [R-FLOOR-WINDOW]'s substance: does the driver evidence support binding in
    # these hours, per unit? Reported over ALL 8,760 h (the limb's declared window), not
    # only cool days.
    print(
        f"\n=== E — per-unit binding of the {FROZEN_FLOOR_PCT} floor over its declared "
        "all-hours window ==="
    )
    print(
        f"  {'plant':<34}{'P(own CF=0)':>13}{'P(CF<frac)':>12}{'own p50':>9}{'own p25':>9}"
    )
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        p = df[df["code"] == code]
        cf = (p["gross"] / p["avail"]).where(p["avail"] > 0).dropna()
        pz = float((cf <= 0.0).mean())
        pb = float((cf < FROZEN_FLOOR_PCT).mean())
        print(
            f"  {names[code] + ' ' + str(code):<34}{pz:>13.3f}{pb:>12.3f}"
            f"{float(cf.median()):>9.3f}{p25(cf):>9.3f}"
        )
        rec["plants"][str(code)]["all_hours"] = {
            "zero_share": pz,
            "share_below_frozen_frac": pb,
            "own_p50": float(cf.median()),
            "own_p25": p25(cf),
        }

    # --- F: is the measured base actually distributed PRO RATA? ---------------
    # The decisive, source-data-only test of the DISTRIBUTION operator, which is what
    # turns a fleet-aggregate coefficient into a per-unit assertion. Under ``pro_rata``
    # each unit's share of fleet generation equals its share of fleet AVAILABLE capacity
    # in every hour. Measured in the hours the limb exists to represent — the fleet's own
    # lowest quartile of when-available CF, i.e. the hours the p25 coefficient is drawn
    # from — that identity either holds or it does not.
    piv_g = cool.pivot_table(index="ts", columns="code", values="gross", aggfunc="sum")
    piv_a = cool.pivot_table(index="ts", columns="code", values="avail", aggfunc="sum")
    fleet_cf_h = (piv_g.sum(axis=1) / piv_a.sum(axis=1)).where(piv_a.sum(axis=1) > 0)
    low = fleet_cf_h <= fleet_cf_h.quantile(0.25)
    gshare = piv_g[low].sum(axis=0) / piv_g[low].sum(axis=0).sum()
    ashare = piv_a[low].sum(axis=0) / piv_a[low].sum(axis=0).sum()
    print(
        "\n=== F — is the measured base distributed PRO RATA? "
        "(fleet's lowest-quartile cool hours) ==="
    )
    print(f"  {'plant':<34}{'gen share':>11}{'avail share':>13}{'g/a ratio':>11}")
    prorata = {}
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        gs, as_ = float(gshare.get(code, 0.0)), float(ashare.get(code, 0.0))
        prorata[str(code)] = {
            "gen_share": gs,
            "avail_share": as_,
            "ratio": gs / as_ if as_ else float("nan"),
        }
        print(
            f"  {names[code] + ' ' + str(code):<34}{gs:>11.3f}{as_:>13.3f}"
            f"{gs / as_ if as_ else float('nan'):>11.2f}"
        )
    # How concentrated is the base? The share of the fleet's low-hour energy carried by
    # its single largest contributor, against the pro-rata expectation.
    top = max(prorata.values(), key=lambda d: d["gen_share"])
    print(
        f"  -> largest contributor carries {top['gen_share']:.1%} of the low-hour energy"
        f" on {top['avail_share']:.1%} of available capacity"
    )
    rec["prorata_test"] = prorata

    # --- G: coverage guard — every plant must be metered in every year --------
    # Guards the section-A/E zero shares: a plant absent from a year's CAMPD extract
    # would be filled 0.0 and read as "off", which would be a pipeline artifact, not
    # conduct. Any year with no positive metered hour for a plant is reported loudly.
    print("\n=== G — coverage guard: positive metered hours per plant-year ===")
    cov = {}
    for code in sorted(npl, key=lambda c: -npl[c]):
        row = {}
        for yr in YEARS:
            s = df[(df["code"] == code) & (df["year"] == yr)]
            row[str(yr)] = int((s["gross"] > 0).sum())
        cov[str(code)] = row
        flag = "" if all(v > 0 for v in row.values()) else "   <-- MISSING YEAR"
        print(
            f"  {names[code] + ' ' + str(code):<34}"
            + "".join(f"{row[str(y)]:>9d}" for y in YEARS)
            + flag
        )
    rec["coverage_positive_hours"] = cov

    # --- H: size the ONE real construction gap (daily-mean identified / hourly applied) --
    # The pre-solve delta an arm would have to beat. Two sizings, both source-data only:
    #   (1) the forced-energy the limb manufactures at the frozen vs the basis-matched
    #       coefficient (the direct analogue of nyiso-140 section 3's "added TWh");
    #   (2) the measured band BETWEEN the two coefficients per plant — the share of a
    #       plant's own hours whose metered CF falls in [basis-matched, frozen). Only
    #       hours in that band can change their binding state from the coefficient move,
    #       so it bounds how much of the D-4 conviction the level can possibly reach.
    corrected = fleet_hourly_p25
    print(
        f"\n=== H — sizing the one construction gap: {FROZEN_FLOOR_PCT:.4f} (frozen, "
        f"daily-mean) -> {corrected:.4f} (basis-matched, hourly) ==="
    )
    print(
        f"  {'plant':<34}{'added@frozen':>14}{'added@fixed':>13}{'delta':>10}{'band %':>9}"
    )
    tot_f = tot_c = 0.0
    for code, cap in sorted(npl.items(), key=lambda kv: -kv[1]):
        p = df[df["code"] == code]
        a_f = (
            float(np.maximum(0.0, FROZEN_FLOOR_PCT * p["avail"] - p["gross"]).sum())
            / 1e6
        )
        a_c = float(np.maximum(0.0, corrected * p["avail"] - p["gross"]).sum()) / 1e6
        cf = (p["gross"] / p["avail"]).where(p["avail"] > 0).dropna()
        band = float(((cf >= corrected) & (cf < FROZEN_FLOOR_PCT)).mean())
        tot_f += a_f
        tot_c += a_c
        print(
            f"  {names[code] + ' ' + str(code):<34}{a_f:>14.3f}{a_c:>13.3f}"
            f"{a_c - a_f:>10.3f}{band * 100:>9.2f}"
        )
        rec["plants"][str(code)]["gap_sizing"] = {
            "added_twh_frozen": a_f,
            "added_twh_basis_matched": a_c,
            "delta_twh": a_c - a_f,
            "measured_band_share": band,
        }
    print(f"  {'FLEET':<34}{tot_f:>14.3f}{tot_c:>13.3f}{tot_c - tot_f:>10.3f}")
    print(
        f"  -> the coefficient move is {100 * (corrected / FROZEN_FLOOR_PCT - 1):+.1f} % relative"
        f" and changes fleet forced energy by {tot_c - tot_f:+.3f} TWh over"
        f" {YEARS[0]}-{YEARS[-1]} ({100 * ((tot_c - tot_f) / tot_f):+.1f} %)"
    )
    rec["gap_sizing_fleet"] = {
        "frozen_floor_pct": FROZEN_FLOOR_PCT,
        "basis_matched_floor_pct": corrected,
        "relative_change": corrected / FROZEN_FLOOR_PCT - 1.0,
        "added_twh_frozen": tot_f,
        "added_twh_basis_matched": tot_c,
        "delta_twh": tot_c - tot_f,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
