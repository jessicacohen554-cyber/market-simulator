"""nyiso-140 Q1 — is the always-on Long_Island ST_GAS 26.2 % floor the right object?

Identification BEFORE any mechanism is written and BEFORE any LP is solved
(``FINDING-nyiso139b-zone-k-joint-lever-rescoped-2026-08-16.md`` §6 question 1).
The limb under examination is the ONE live Long_Island x ST_GAS row of
``data/raw/reference/reliability_floor_coeffs_NYISO.csv``:

    driver=tmax, threshold=-50.0 C, floor_pct=0.262, distribution=pro_rata,
    no start/end hour, no ramp_group
    basis: "persistent 24h base: base_24h (when-available cool-day CF p25)"

A -50 C tmax threshold is never not met, so the limb binds in all 8,760 hours,
and ``pro_rata`` distribution floors EVERY unit of the class in the zone at
``0.262 x pmax x availability[t]`` (``model/interchange/core.py::_apply_frac``).

Rule 17 ``[R-FLOOR-WINDOW]`` requires a window, a driver and a forward story, and
declares that a floor binding in hours its own driver evidence says the class is
offline is a bug by definition. Rule 23 ``[R-FROZEN-DERIVE]`` allows a
re-derivation ONLY on a source-data trigger, never because a residual moved --
so this probe reads the floor's OWN source (CAMPD unit-level conduct plus the
guard-corrected outage extract, the same two inputs
``scripts/data/derive_nyiso_st_reliability_floor.py`` uses) and never touches a
price or volume residual, a metrics file, or a solve.

The probe measures the coefficient's basis against the mechanism's application on
the two axes on which they differ:

  A  TEMPORAL      -- ``base_24h`` is a p25 over DAILY-MEAN fleet CF; the floor
                      is applied per HOUR. A daily mean of 0.262 is compatible
                      with overnight hours far below it.
  B  CROSS-SECTIONAL -- ``base_24h`` is a FLEET aggregate (sum gross / sum
                      avail over 3 plants); ``pro_rata`` applies it to EACH
                      plant separately. A fleet mean of 0.262 is compatible with
                      one plant at 0.

Step 0 reproduces the frozen coefficients (base_24h=0.262, base_ev=0.35) exactly,
so any divergence below is a basis difference and not a pipeline difference.

Run: ``.venv/bin/python scripts/probes/_nyiso140_li_st_floor_membership.py``
Rule 25 ``[R-ISO-SCOPE]``: NYISO only, Long_Island zone only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

ZONE = "Long_Island"
YEARS = (2023, 2024, 2025)  # training window only (rule 22 holdout freeze)
T0_C = 25.0  # the derive script's cool/hot split
EVENING_HOURS = range(14, 22)  # HB14-21, the derive script's evening window
FLOOR_PCT = 0.262  # the live limb's floor_pct, as frozen in the CSV
NAMES = {2511: "E F Barrett", 2516: "Northport", 2517: "Port Jefferson"}
HOUR_BLOCKS = {
    "h00-05": range(0, 6),
    "h06-13": range(6, 14),
    "h14-21": range(14, 22),
    "h22-23": range(22, 24),
}


def zone_steam_plant_codes(zone: str) -> dict[int, float]:
    """Return ``{plant_code: bin nameplate MW}`` for a zone's ST_GAS fleet."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    z = b[(b["Plant_Group"] == "ST_GAS") & (b["Zone"] == zone)]
    return dict(zip(z["Plant_Code"].astype(int), z["Nameplate_MW"].astype(float)))


def plant_available_capacity(
    plant_npl: dict[int, float], index: pd.DatetimeIndex
) -> dict[int, pd.Series]:
    """Per-PLANT hourly available MW on the derive script's own derate basis.

    Nameplate minus each out unit's ``unit_capacity_mw / plant_capacity_mw`` share
    of that plant's bin nameplate, from the guard-corrected
    ``campd-unit-outages-NYISO.csv``. Kept per-plant (the derive script sums to a
    fleet total) because axis B needs the per-unit denominator the ``pro_rata``
    floor actually multiplies.
    """
    out = {p: pd.Series(float(n), index=index) for p, n in plant_npl.items()}
    path = RAW_DIR / "campd-unit-outages-NYISO.csv"
    if not path.exists():
        return out
    o = pd.read_csv(path)
    o["facility_id"] = pd.to_numeric(o["facility_id"], errors="coerce")
    o = o[o["facility_id"].isin(plant_npl)].copy()
    o["outage_start"] = pd.to_datetime(o["outage_start"])
    o["outage_end"] = pd.to_datetime(o["outage_end"])
    for _, e in o.iterrows():
        pid = int(e["facility_id"])
        pcap = float(e["plant_capacity_mw"]) or 1.0
        share_mw = float(plant_npl.get(pid, 0.0)) * float(e["unit_capacity_mw"]) / pcap
        mask = (index >= e["outage_start"]) & (index < e["outage_end"])
        out[pid].loc[mask] -= share_mw
    return {p: s.clip(lower=0.0) for p, s in out.items()}


def load_unit_hours() -> tuple[pd.DataFrame, dict[int, float]]:
    """Build the per-plant hourly (gross, avail, tmax) panel for YEARS."""
    plant_npl = zone_steam_plant_codes(ZONE)
    codes = sorted(plant_npl)
    arch = pd.read_csv(
        RAW_DIR / "nyiso-weather" / "nyiso_zone_tmax_daily.csv", parse_dates=["date"]
    )
    tser = arch[arch["zone"] == ZONE].set_index("date")["tmax_c"]

    frames = []
    for yr in YEARS:
        path = RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet"
        if not path.exists():
            continue
        c = pd.read_parquet(path)
        # facilityId ships as a STRING column; comparing it to int plant codes
        # silently matches nothing, so cast before filtering.
        c["facilityId"] = c["facilityId"].astype(int)
        c = c[c["facilityId"].isin(codes)].copy()
        c["grossLoad"] = pd.to_numeric(c["grossLoad"], errors="coerce").fillna(0.0)
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        gp = c.groupby(["ts", "facilityId"])["grossLoad"].sum().unstack(fill_value=0.0)
        for p in codes:
            if p not in gp.columns:
                gp[p] = 0.0
        gp = gp[codes]
        av = pd.DataFrame(plant_available_capacity(plant_npl, gp.index), index=gp.index)
        u = gp.stack().rename("gross").to_frame()
        u["avail"] = av.stack()
        u = u.reset_index()
        u.columns = ["ts", "plant", "gross", "avail"]
        u["year"] = yr
        u["date"] = pd.to_datetime(u["ts"]).dt.normalize()
        u["hour"] = pd.to_datetime(u["ts"]).dt.hour
        u["tmax"] = u["date"].map(tser)
        frames.append(u)

    U = pd.concat(frames).dropna(subset=["tmax"])
    U["cf"] = (U["gross"] / U["avail"]).where(U["avail"] > 0)
    return U, plant_npl


def fleet_hourly(U: pd.DataFrame) -> pd.DataFrame:
    """Collapse the per-plant panel to the fleet hourly CF the derive script uses."""
    F = U.groupby("ts", as_index=False).agg(
        gross=("gross", "sum"), avail=("avail", "sum"), tmax=("tmax", "first")
    )
    F["hour"] = pd.to_datetime(F["ts"]).dt.hour
    F["date"] = pd.to_datetime(F["ts"]).dt.normalize()
    F["cf"] = (F["gross"] / F["avail"]).where(F["avail"] > 0)
    return F


def step0_reproduce(F: pd.DataFrame) -> float:
    """Reproduce the frozen base_24h / base_ev so basis gaps are not pipeline gaps."""
    day = F.groupby("date").agg(
        gross=("gross", "sum"), avail=("avail", "sum"), tmax=("tmax", "first")
    )
    day["cf"] = (day["gross"] / day["avail"]).where(day["avail"] > 0)
    cool = day[day["tmax"] < T0_C].dropna(subset=["cf"])
    base24 = float(cool["cf"].quantile(0.25))
    ev = F[F["hour"].isin(EVENING_HOURS)]
    evd = ev.groupby("date").agg(
        gross=("gross", "sum"), avail=("avail", "sum"), tmax=("tmax", "first")
    )
    evd["cf"] = (evd["gross"] / evd["avail"]).where(evd["avail"] > 0)
    base_ev = float(evd[evd["tmax"] < T0_C]["cf"].quantile(0.25))
    print("--- 0. REPRODUCTION of the frozen coefficients -------------------")
    print(
        f"    base_24h  (cool-day DAILY-MEAN fleet CF p25) = {base24:.4f}  [CSV: 0.262]"
    )
    print(
        f"    base_ev   (cool-day evening  fleet CF p25)   = {base_ev:.4f}  [CSV: 0.35]"
    )
    print(f"    cool days n={len(cool)}")
    return base24


def axis_a_temporal(F: pd.DataFrame) -> None:
    """Hourly fleet CF by hour of day — is a daily-mean p25 an hourly floor?"""
    Fc = F[F["tmax"] < T0_C].dropna(subset=["cf"])
    print("\n--- A. TEMPORAL: hourly FLEET when-available CF, COOL days -------")
    print(f"    {'block':>8} {'p25':>8} {'p50':>8}")
    for name, hrs in HOUR_BLOCKS.items():
        s = Fc[Fc["hour"].isin(hrs)]["cf"]
        print(f"    {name:>8} {s.quantile(0.25):>8.4f} {s.median():>8.4f}")
    print(
        f"    pooled ALL-24h HOURLY p25 = {Fc['cf'].quantile(0.25):.4f}   "
        f"<- basis-matched to how the floor is APPLIED"
    )
    print(f"    frozen coefficient        = {FLOOR_PCT:.4f}   <- a DAILY-MEAN p25")
    print(
        f"    P(hourly fleet cf >= {FLOOR_PCT}) over cool hours = "
        f"{(Fc['cf'] >= FLOOR_PCT).mean():.3f}"
    )


def axis_b_cross_sectional(U: pd.DataFrame, plant_npl: dict[int, float]) -> None:
    """Per-plant conduct — pro_rata floors EACH unit at the FLEET statistic."""
    Uc = U[U["tmax"] < T0_C].dropna(subset=["cf"])
    print("\n--- B. CROSS-SECTIONAL: per-PLANT cool-day conduct ----------------")
    print(
        f"    {'plant':>16} {'MW':>7} {'p50cf':>7} {'P(cf=0)':>8} "
        + " ".join(f"{b:>8}" for b in HOUR_BLOCKS)
    )
    for p in sorted(plant_npl):
        s = Uc[Uc["plant"] == p]
        if s.empty:
            continue
        blocks = " ".join(
            f"{s[s['hour'].isin(h)]['cf'].median():>8.3f}" for h in HOUR_BLOCKS.values()
        )
        print(
            f"    {NAMES.get(p, p):>16} {plant_npl[p]:>7.0f} "
            f"{s['cf'].median():>7.3f} {(s['cf'] <= 1e-9).mean():>8.3f} {blocks}"
        )
    print(
        "    (median cf by hour block; a plant at 0.000 in EVERY block has no "
        "persistent baseline)"
    )


def axis_c_forced_energy(U: pd.DataFrame, plant_npl: dict[int, float]) -> None:
    """Full-year, all-hours energy the pro_rata floor adds above measured conduct."""
    print("\n--- C. WHAT THE FLOOR ADDS ABOVE CONDUCT (all hours, 3 yr) --------")
    print(
        f"    {'plant':>16} {'obs_TWh':>9} {'floored_TWh':>12} {'ADDED_TWh':>10} "
        f"{'x own obs':>10}"
    )
    added = {}
    for p in sorted(plant_npl):
        s = U[U["plant"] == p]
        obs = float(s["gross"].sum())
        fl = float((FLOOR_PCT * s["avail"]).sum())
        add = float(np.maximum(FLOOR_PCT * s["avail"] - s["gross"], 0.0).sum())
        added[p] = add
        ratio = f"{fl / obs:>10.2f}" if obs > 0 else f"{'inf':>10}"
        print(
            f"    {NAMES.get(p, p):>16} {obs / 1e6:>9.4f} {fl / 1e6:>12.4f} "
            f"{add / 1e6:>10.4f} {ratio}"
        )
    tot = sum(added.values())
    print(
        f"    {'FLEET':>16} {U['gross'].sum() / 1e6:>9.4f} {'':>12} {tot / 1e6:>10.4f}"
    )
    for p, a in sorted(added.items(), key=lambda kv: -kv[1])[:1]:
        print(
            f"    -> {NAMES.get(p, p)} is {a / tot * 100:.1f}% of ALL energy the "
            f"floor adds, on {U[U['plant'] == p]['gross'].sum() / U['gross'].sum() * 100:.1f}% "
            f"of the fleet's observed output"
        )


def axis_d_temperature_response(U: pd.DataFrame) -> None:
    """Is the idle plant's commitment PERSISTENT or TEMPERATURE-CONDITIONAL?"""
    print("\n--- D. TEMPERATURE RESPONSE of the idle plant (2517) --------------")
    s = U[U["plant"] == 2517].copy()
    print(f"    {'tmax band C':>14} {'n_h':>7} {'P(on)':>7} {'meanMW':>8}")
    for lo, hi in [(-99, 0), (0, 10), (10, 20), (20, 25), (25, 30), (30, 99)]:
        b = s[(s["tmax"] >= lo) & (s["tmax"] < hi)]
        if b.empty:
            continue
        lbl = f"[{lo:>3},{hi:>3})"
        print(
            f"    {lbl:>14} {len(b):>7} {(b['gross'] > 1).mean():>7.3f} "
            f"{b['gross'].mean():>8.1f}"
        )
    print(
        f"    overall P(on) = {(s['gross'] > 1).mean():.3f}; mean MW when on = "
        f"{s[s['gross'] > 1]['gross'].mean():.0f} of "
        f"{s['avail'].max():.0f} MW available"
    )
    print(
        "    (a U-shaped hot+cold response is the RAMP limbs' driver, not a "
        "persistent 24 h base)"
    )


def axis_e_membership_corrected(U: pd.DataFrame) -> None:
    """Re-derive the coefficient on the correct basis with the idle plant removed."""
    print("\n--- E. BASIS-CORRECTED COEFFICIENT, idle plant excluded ------------")
    for label, sub in (
        ("3 plants (as frozen)", U),
        ("2 plants (excl 2517)", U[U["plant"] != 2517]),
    ):
        F = fleet_hourly(sub)
        Fc = F[F["tmax"] < T0_C].dropna(subset=["cf"])
        day = Fc.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
        dmean = float((day["gross"] / day["avail"]).quantile(0.25))
        print(
            f"    {label:>22}: HOURLY all-24h p25 = {Fc['cf'].quantile(0.25):.4f}  "
            f"| DAILY-MEAN p25 = {dmean:.4f}"
        )
    print(f"    frozen floor_pct = {FLOOR_PCT:.4f}")


def main() -> None:
    """Run the five identification steps and print the evidence table."""
    U, plant_npl = load_unit_hours()
    print(
        f"=== {ZONE} ST_GAS: {len(plant_npl)} plants, "
        f"{sum(plant_npl.values()):.0f} MW nameplate, {list(YEARS)} ==="
    )
    F = fleet_hourly(U)
    step0_reproduce(F)
    axis_a_temporal(F)
    axis_b_cross_sectional(U, plant_npl)
    axis_c_forced_energy(U, plant_npl)
    axis_d_temperature_response(U)
    axis_e_membership_corrected(U)


if __name__ == "__main__":
    main()
