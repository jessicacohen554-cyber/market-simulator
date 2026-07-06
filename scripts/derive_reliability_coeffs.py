"""Derive honest per-(zone x class) temperature reliability-floor coefficients.

Part B of ``docs/multi-iso/reliability-floor-rebuild-plan.md``. For one ISO, for
every (model zone, fossil class), this script measures the temperature->commitment
relationship from CAMPD unit-level ``grossLoad`` and emits a transparent
coefficient row. The floor is **structural**, never tuned to a price/volume
residual (CLAUDE.md #9/#11):

    floor_pct = commit_frac x min_stable_pct

where
  * ``min_stable_pct`` = the class's **physical min-stable level (Pmin/Pmax) of a
    committed unit**, from ``constants.MIN_STABLE_PCT_PHYSICAL`` (NREL WWSIS-2
    Table 7) — NOT the offer-curve ``Pct_Must_Run`` share, which is 0 for merchant
    steam/CT/CC and so zeroed the priority fleet's floor. The temperature gate
    reliability-commits a merchant unit on an extreme day; once committed it sits
    at this physical Pmin (see ``reliability-floor-physical-parameter-research.md``
    §3), and
  * ``commit_frac`` = the share of the class's nameplate that is *online*
    (``grossLoad > 0``) on temperature-flagged days — a commitment count, NOT a
    measured-CF ceiling.

Per (zone, class) two limbs are evaluated: a **hot** limb gated on the zone's
daily TMAX and a **cold** limb gated on daily TMIN. Onsets are physical anchors
(plan D), not flat priors: the hot onset is the zone's 95th-percentile TMAX
(design cooling day — no ISO publishes a hot trigger); the cold onset is PJM's
documented Cold-Weather-Alert −12 °C (−20.5 °C for the CT-mobilization tier) for
PJM zones, else the zone's 1st-percentile TMIN (design heating day). For each
limb we report ``threshold`` (the °C onset), ``floor_pct``, ``commit_frac``,
``min_stable_pct``, plus diagnostics ``rho`` (Spearman of the temperature drive
vs daily CF), ``n`` (flagged-day count), ``slope``, ``baseline`` (mild-day mean
CF) and ``baseline_commit`` (mild-day mean online share).

A limb ships ``enabled=True`` ONLY when the response is real and the commitment
*rises with temperature*: ``rho >= RHO_MIN`` AND ``n >= N_MIN`` AND
``commit_frac > baseline_commit`` (the flagged-day online share exceeds the
mild-day online share — a like-for-like commitment test, replacing the earlier
``floor_pct > baseline`` clause that compared an instantaneous floor to a daily
energy average). Otherwise the limb ships ``enabled=False`` and is visible (with
its weak fit) in the markdown report so nothing is invented to plug a residual.

A limb listed in :data:`R1_DISABLED_LIMBS` overrides the gate and ships
``enabled=False`` / ``r1_disabled=True`` unconditionally: these limbs are
*unidentified* out-of-training (their Spearman ρ flips sign between the 2023-24
train fit and the 2025 holdout, D-8 §2B) and under decision rule R1 may not be
re-derived back on (scalar-remediation B-LIMB-1; CLAUDE.md rule 17).

Outputs:
  * ``data/raw/reference/reliability_floor_coeffs_<ISO>.csv`` — the coefficient
    table (one row per zone x class x limb that has data).
  * ``docs/multi-iso/reliability-floor-coefficients.md`` — a human-readable
    per-ISO section.

Usage:
    python scripts/derive_reliability_coeffs.py --iso ERCOT
    python scripts/derive_reliability_coeffs.py --iso ALL
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd

from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
from market_sim.config.paths import RAW_DIR, REFERENCE_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_reliability_coeffs")

# --- Enable/disable gate (plan B.3/C); diagnostics only, never residual-tuned. ---
RHO_MIN = 0.3  # min Spearman temperature->CF correlation to ship a limb on
N_MIN = 30  # min flagged-day sample size to trust a limb
HOURS_PER_DAY = 24  # CF denominator: nameplate x 24 hours

# --- R1 permanent disablement (unidentified limbs; scalar-remediation B-LIMB-1) ---
# These (iso, zone, plant_class, driver) limbs are UNIDENTIFIED out-of-training:
# their Spearman temperature->commitment correlation FLIPS SIGN between the
# 2023-24 train fit and the 2025 holdout (D-8 §2B, docs/out-of-sample-results-
# 2026-07.md: PJM ComEd/CC_REGULAR tmax ρ +0.35→−0.19; CAISO SP15/ST_GAS tmax
# ρ +0.41→−0.16; CAISO SP15/CC_REGULAR tmax ρ +0.69→−0.10). Under decision rule R1
# (docs/handoffs/scalar-remediation-plan-2026-07.md §1 R1, §2.3) and CLAUDE.md
# rule 17, a floor whose driver relationship reverses out-of-training is
# scaffolding fitted to noise: it may NOT be re-derived back on. This set FORCES
# ``enabled=False`` and stamps ``r1_disabled=True`` regardless of the pooled
# (all-year) fit, so a future re-derivation from the same fit cannot silently
# re-enable the limb — the pooled ρ for two of the three sits below RHO_MIN today,
# but CAISO SP15/CC_REGULAR pools to ρ=0.32 ≥ RHO_MIN and WOULD re-enable without
# this guard. This is an analysis-evidence disablement (a sign-flip finding), NOT a
# residual adjustment (rule 23). The tmin (cold) limbs of these pairs are left to
# the natural gate: the sign-flip evidence is tmax-only and those limbs are already
# gate-disabled (ρ≈0, n<30 — design-heating days too rare in these zones to clear
# N_MIN), so no R1 marker over-claims evidence there.
R1_DISABLED_LIMBS: frozenset[tuple[str, str, str, str]] = frozenset(
    {
        ("PJM", "PJM_ComEd", "CC_REGULAR", "tmax"),
        ("CAISO", "SP15", "ST_GAS", "tmax"),
        ("CAISO", "SP15", "CC_REGULAR", "tmax"),
    }
)


def _r1_disabled(iso: str, zone: str, klass: str, driver: str) -> bool:
    """Return ``True`` if this (iso, zone, class, driver) limb is R1-disabled.

    R1-disabled limbs are unidentified out-of-training (Spearman ρ sign flip,
    D-8 §2B) and ship permanently off regardless of the pooled fit — see
    :data:`R1_DISABLED_LIMBS`.
    """
    return (iso, zone, klass, driver) in R1_DISABLED_LIMBS


# --- Temperature onsets (plan D; physical anchors, not flat 25C/0C priors). ---
# COLD has documented operational triggers for PJM; non-PJM uses a per-zone design
# heating day. HOT has NO ISO-published trigger, so it is the per-zone design
# cooling-day percentile — never chosen to improve the backcast (CLAUDE.md #9).
PJM_COLD_ALERT_C = -12.0  # PJM Manual 13 Rev 97 Cold Weather Alert (tmin ≤ 10 °F)
PJM_COLD_CT_MOBILIZE_C = -20.5  # PJM Manual 13 extra CT-mobilization tier (≤ -5 °F)
COLD_PERCENTILE = 1.0  # non-PJM cold onset = 1st-pct zone tmin (design heating day)
HOT_PERCENTILE = 95.0  # hot onset = 95th-pct zone tmax (design cooling day)
_CT_CLASSES = frozenset({"CT_PEAKER", "CT_CHP"})

# Sub-daily hour-of-day window (inclusive, local-standard t%24) that a CT_PEAKER
# reliability limb is allowed to bind. A CT peaker serves the afternoon-evening
# cooling / net-load ramp; overnight its capacity factor is ~0, so a full-day
# temperature/net-load gate that floors it 00:00-23:59 binds it in hours its own
# driver evidence says it is offline — a rule-13 off-window artifact (the D-4
# gate's justified window for MECH_RELIABILITY_FLOOR x CT_PEAKER is [15, 22)).
# Emitted as a structural shape parameter, NOT a fitted coefficient: the window
# is the physical diurnal footprint of the peak driver, identical across ISOs and
# already carried by the CAISO CT limbs. CT_CHP (steam-host cogen) runs all hours
# and is deliberately NOT windowed.
_CT_EVENING_WINDOW: tuple[int, int] = (15, 21)  # inclusive → engine gate [15,22)

# Fossil classes the engine can floor (plan B.1). Renewables/nuclear/hydro never.
FOSSIL_CLASSES = (
    "COAL",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_WC",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "oil",
)

# CAMPD is filed by state; these are each ISO's footprint states (a superset is
# fine — the bin-map join restricts to the ISO's own plants by facilityId).
ISO_CAMPD_STATES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("TX",),
    "CAISO": ("CA",),
    "PJM": (
        "IL",
        "IN",
        "MI",
        "OH",
        "PA",
        "WV",
        "VA",
        "MD",
        "DC",
        "DE",
        "NJ",
        "NC",
        "TN",
        "KY",
    ),
    "MISO": (
        "MN",
        "ND",
        "SD",
        "IA",
        "MO",
        "WI",
        "IL",
        "IN",
        "MI",
        "AR",
        "LA",
        "MS",
        "TX",
    ),
    "NYISO": ("NY",),
    "NEISO": ("CT", "MA", "ME", "NH", "RI", "VT"),
}

# Per-ISO model-fleet bin source + its (zone, class, nameplate, must-run) columns.
# ERCOT uses the curated CAMPD per-plant bins (custom-bin-assignments.csv); the
# other multi-zone ISOs use bin_assignments_<ISO>.csv. PJM has no bin file, so it
# maps plant->zone via data.zone_assignment + class via classify_plant (below).
_LEGACY_BINS = RAW_DIR / "_processed-legacy"


def _zone_temps(iso: str) -> pd.DataFrame:
    """Load the per-zone daily ``date,zone,tmax_c,tmin_c`` series for an ISO."""
    path = RAW_DIR / f"{iso.lower()}-weather" / f"{iso.lower()}_zone_temp_daily.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"zone temp file missing for {iso}: {path} "
            f"(run scripts/fetch_zone_temperature.py --iso {iso})"
        )
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def _plant_map(iso: str) -> pd.DataFrame:
    """Return ``plant_code,zone,plant_class,nameplate_mw,must_run_pct`` for an ISO.

    ERCOT: curated ``custom-bin-assignments.csv`` (groups summed per plant).
    CAISO/MISO/NEISO/NYISO: ``bin_assignments_<ISO>.csv``.
    PJM: model zone from :func:`data.zone_assignment.build_zone_lookup`, class
    from :func:`config.plant_taxonomy.classify_plant` over the EIA-860 fleet.
    """
    iso = iso.upper()
    if iso == "ERCOT":
        b = pd.read_csv(REFERENCE_DIR / "custom-bin-assignments.csv")
        b = b.rename(columns={"ERCOT_Zone": "Zone", "Plant_Group": "plant_class"})
        grp = b.groupby(["Plant_Code", "Zone", "plant_class"], as_index=False).agg(
            nameplate_mw=("Nameplate_MW", "sum"),
            must_run_pct=("Pct_Must_Run", "mean"),
        )
        grp = grp.rename(columns={"Plant_Code": "plant_code", "Zone": "zone"})
        return grp

    legacy = _LEGACY_BINS / f"bin_assignments_{iso}.csv"
    if legacy.exists():
        b = pd.read_csv(legacy)
        grp = b.groupby(["Plant_Code", "Zone", "Plant_Group"], as_index=False).agg(
            nameplate_mw=("Nameplate_MW", "sum"),
            must_run_pct=("Pct_Must_Run", "mean"),
        )
        return grp.rename(
            columns={
                "Plant_Code": "plant_code",
                "Zone": "zone",
                "Plant_Group": "plant_class",
            }
        )

    if iso == "PJM":
        return _pjm_plant_map()

    raise FileNotFoundError(f"no bin/zone source for ISO {iso}")


def _pjm_plant_map() -> pd.DataFrame:
    """Build the PJM ``plant_code,zone,plant_class,nameplate_mw,must_run_pct`` map.

    Zone from eGRID/EIA-860 geography (``build_zone_lookup`` — its zone names are
    the same the per-zone weather series carries). Class and nameplate come from
    the model's own fleet loader (:func:`load_fleet_from_csv`), so the
    classification and CF denominator match the LP capacity basis. The ORIS plant
    code is recovered from each generator's ``unit_id`` (``"{plant_id}_{gen}"``).
    ``must_run_pct`` is set to 0 — the floor magnitude no longer uses it (it is
    sourced from ``MIN_STABLE_PCT_PHYSICAL``, plan B).
    """
    from market_sim.data.fleet import load_fleet_from_csv
    from market_sim.data.zone_assignment import build_zone_lookup

    zone_lookup = build_zone_lookup("PJM")
    try:
        gens = load_fleet_from_csv("PJM")
    except Exception as exc:  # pragma: no cover - fleet wiring
        log.warning("PJM fleet load unavailable (%s); PJM map empty", exc)
        return pd.DataFrame(
            columns=[
                "plant_code",
                "zone",
                "plant_class",
                "nameplate_mw",
                "must_run_pct",
            ]
        )

    rows = []
    for g in gens:
        token = g.unit_id.split("_", 1)[0]
        if not token.isdigit():
            continue
        oris = int(token)
        if oris not in zone_lookup:
            continue
        rows.append(
            {
                "plant_code": oris,
                "zone": zone_lookup[oris],
                "plant_class": g.plant_group,
                "nameplate_mw": float(g.pmax_mw or 0.0),
                "must_run_pct": 0.0,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby(["plant_code", "zone", "plant_class"], as_index=False).agg(
        nameplate_mw=("nameplate_mw", "sum"), must_run_pct=("must_run_pct", "mean")
    )


def _load_campd(iso: str, plant_codes: set[int]) -> pd.DataFrame:
    """Concatenate the ISO's state CAMPD unit-level frames, kept to its plants.

    Aggregates each unit row to a per-(facilityId, date, hour) ``grossLoad`` is
    not needed — we keep the unit rows and sum per group/day downstream. Raises a
    clear error when no CAMPD parquet is present for the ISO.
    """
    states = ISO_CAMPD_STATES.get(iso.upper(), ())
    frames: list[pd.DataFrame] = []
    for st in states:
        for yr in (2023, 2024, 2025):
            p = RAW_DIR / "campd-unit-level" / f"{st}_{yr}.parquet"
            if p.exists():
                frames.append(
                    pd.read_parquet(p, columns=["facilityId", "date", "grossLoad"])
                )
    if not frames:
        raise FileNotFoundError(
            f"no CAMPD unit-level parquet found for {iso} states {states}"
        )
    c = pd.concat(frames, ignore_index=True)
    c["facilityId"] = c["facilityId"].astype(int)
    c = c[c["facilityId"].isin(plant_codes)].copy()
    c["date"] = pd.to_datetime(c["date"])
    return c


def _group_daily_cf(
    campd: pd.DataFrame, plant_npl: dict[int, float], nameplate: float
) -> pd.DataFrame:
    """Daily ``cf`` and ``online_frac`` for a (zone, class) plant group.

    * ``cf`` = group daily MWh / (group nameplate x 24), clipped to [0, 1].
    * ``online_frac`` = nameplate-weighted share of the group's capacity that is
      online (any unit ``grossLoad > 0``) that day — the commitment count, on the
      same model nameplate basis as the CF denominator. CAMPD carries no
      nameplate, so each plant's online presence is weighted by its bin nameplate
      (``plant_npl``).
    """
    codes = set(plant_npl)
    if nameplate <= 0.0 or not codes:
        return pd.DataFrame(columns=["cf", "online_frac"])
    sub = campd[campd["facilityId"].isin(codes)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["cf", "online_frac"])
    daily_mwh = sub.groupby("date")["grossLoad"].sum(min_count=1)
    # A date in this index has CAMPD rows for the group; when every row's
    # grossLoad is NaN the units reported but did not operate (CEMS leaves
    # non-operating hours empty), so the day's energy is 0 — NOT missing data.
    # Without this, an intermittent single-plant group (e.g. NEISO ST_GAS /
    # Montville, offline ~90% of days) loses its offline days from the frame
    # entirely and every flagged-day statistic conditions on "was operating":
    # commit_frac saturates and the mild-day baselines are biased high.
    daily_mwh = daily_mwh.fillna(0.0)
    cf = (daily_mwh / (nameplate * HOURS_PER_DAY)).clip(0.0, 1.0)
    # Per-plant online nameplate: a plant counts as online on any day it reports
    # positive gross load; sum its bin nameplate, normalise by group nameplate.
    online = sub[sub["grossLoad"].fillna(0.0) > 0.0]
    online_plants = online.groupby("date")["facilityId"].agg(lambda s: set(s))
    online_share = online_plants.apply(
        lambda s: sum(plant_npl.get(int(p), 0.0) for p in s) / nameplate
    ).clip(0.0, 1.0)
    # A reporting day with NO online plant must count as online_frac = 0, not
    # drop out: ``online_plants`` only has rows for days with some positive
    # grossLoad, so without the reindex a SINGLE-plant group's online share is
    # 1.0-or-missing and its commit_frac saturates at 1.0 == baseline_commit
    # (the enable gate then can never pass — the 2026-06-30 NEISO ST_GAS rows
    # show exactly this artifact). Multi-plant groups are near-unaffected
    # (some plant reports load almost every day).
    online_share = online_share.reindex(cf.index).fillna(0.0)
    return pd.DataFrame({"cf": cf, "online_frac": online_share})


def _fit_limb(
    df: pd.DataFrame, temp: pd.Series, threshold: float, cold: bool
) -> dict | None:
    """Fit one temperature limb; return its coefficient dict or ``None``.

    ``drive`` rises with severity (TMAX above the hot onset, or coldness below the
    cold onset). Flagged days are those past the threshold. ``commit_frac`` is the
    mean online share on flagged days; ``baseline`` is the mild-day mean CF;
    ``baseline_commit`` is the mild-day mean online share (the like-for-like
    commitment comparand for the enable gate, plan C).
    """
    d = df.join(temp.rename("t"), how="inner").dropna(subset=["cf", "t"])
    if d.empty:
        return None
    if cold:
        flagged = d[d["t"] < threshold]
        drive = threshold - flagged["t"]
        mild = d[d["t"] >= threshold]
    else:
        flagged = d[d["t"] >= threshold]
        drive = flagged["t"] - threshold
        mild = d[d["t"] < threshold]
    n = int(len(flagged))
    if n < 2:
        return None
    commit_frac = float(flagged["online_frac"].mean())
    baseline = float(mild["cf"].mean()) if len(mild) else 0.0
    baseline_commit = float(mild["online_frac"].mean()) if len(mild) else 0.0
    slope = float(np.polyfit(drive, flagged["cf"], 1)[0]) if n >= 2 else 0.0
    rho = (
        float(drive.corr(flagged["cf"], method="spearman"))
        if n >= 2 and drive.nunique() > 1
        else float("nan")
    )
    return {
        "commit_frac": commit_frac,
        "baseline": baseline,
        "baseline_commit": baseline_commit,
        "slope": slope,
        "rho": rho,
        "n": n,
    }


def _min_stable_pct(plant_class: str) -> float:
    """Physical Pmin/Pmax for a class (coal subclasses fall back to COAL).

    Sourced from :data:`constants.MIN_STABLE_PCT_PHYSICAL` (NREL WWSIS-2 Table 7);
    the offer-curve ``Pct_Must_Run`` share is deliberately NOT used (plan B). An
    unmapped class returns 0.0 (no physical floor known → no floor).
    """
    if plant_class in MIN_STABLE_PCT_PHYSICAL:
        return MIN_STABLE_PCT_PHYSICAL[plant_class]
    if plant_class.startswith("COAL"):
        return MIN_STABLE_PCT_PHYSICAL["COAL"]
    return 0.0


# EIA-930 balancing-authority hourly extract + LST offset per ISO with a
# net-load-driven limb. NEISO joined 2026-07-06 (the ST_GAS re-grounding);
# other ISOs are added here if/when a netload limb is derived for them.
_NETLOAD_BA_FILES: dict[str, tuple[str, int]] = {
    "CAISO": ("CISO hourly.parquet", 8),  # UTC-8 (PST, matching the CT derive)
    "NEISO": ("ISNE hourly.parquet", 5),  # UTC-5 (EST)
}


def _system_net_load(
    iso: str,
    date_min: pd.Timestamp | None = None,
    date_max: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Load an ISO's system hourly net-load from EIA-930, return daily peak GW.

    Net-load = Demand − solar − wind (same formula as
    ``derive_caiso_ct_reliability_floor.ciso_net_load_mw``). Returns a DataFrame
    with columns ``date`` and ``peak_nl_gw`` (daily peak net-load in GW).

    ``date_min``/``date_max`` restrict the series to the derivation span (the
    zone-temperature file's coverage, 2023-2025 today). This matters twice:
    (1) the threshold percentile must be computed on the SAME span the CF
    regression sees — the BA parquets have since been backfilled to 2019
    (PR #1490 era), and an unrestricted percentile would silently shift the
    committed CAISO netload thresholds on re-derivation; (2) the holdout
    periods (2022, H1-2026; CLAUDE.md rule 22) must not leak into a
    calibration-derived threshold.
    """
    entry = _NETLOAD_BA_FILES.get(iso.upper())
    if entry is None:
        raise FileNotFoundError(f"no EIA-930 BA hourly mapping for ISO {iso}")
    fname, utc_offset = entry
    ba_path = RAW_DIR / "eia-930-hourly" / fname
    if not ba_path.exists():
        raise FileNotFoundError(f"EIA-930 BA hourly missing: {ba_path}")
    df = pd.read_parquet(ba_path)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    lst = utc.dt.tz_convert(None) - pd.Timedelta(hours=utc_offset)
    df = df.copy()
    df["lst"] = lst
    df["date"] = lst.dt.normalize()
    dem = pd.to_numeric(df["Demand"], errors="coerce")
    sun = pd.to_numeric(df.get("NG: SUN"), errors="coerce").fillna(0.0)
    wnd = pd.to_numeric(df.get("NG: WND"), errors="coerce").fillna(0.0)
    df["nl_mw"] = dem - sun - wnd
    daily = df.groupby("date")["nl_mw"].max().reset_index()
    daily.columns = ["date", "peak_nl_gw"]
    daily["peak_nl_gw"] = daily["peak_nl_gw"] / 1000.0
    daily["date"] = pd.to_datetime(daily["date"])
    if date_min is not None:
        daily = daily[daily["date"] >= date_min]
    if date_max is not None:
        daily = daily[daily["date"] <= date_max]
    return daily.reset_index(drop=True)


def _fit_netload_limb(
    cf_df: pd.DataFrame, daily_nl: pd.DataFrame, threshold_gw: float
) -> dict | None:
    """Fit a net-load limb: regress daily class CF on daily peak net-load (GW).

    ``cf_df`` has index=date, columns ``cf`` and ``online_frac``. ``daily_nl`` has
    columns ``date`` and ``peak_nl_gw``. Days with peak net-load > threshold are
    flagged; ``commit_frac`` is the flagged-day mean online share, ``baseline`` and
    ``baseline_commit`` are the below-threshold means. Spearman ρ measures the
    net-load→CF relationship on flagged days.
    """
    nl = daily_nl.set_index("date")["peak_nl_gw"]
    d = cf_df.join(nl.rename("nl"), how="inner").dropna(subset=["cf", "nl"])
    if d.empty:
        return None
    flagged = d[d["nl"] > threshold_gw]
    mild = d[d["nl"] <= threshold_gw]
    n = int(len(flagged))
    if n < 2:
        return None
    commit_frac = float(flagged["online_frac"].mean())
    baseline = float(mild["cf"].mean()) if len(mild) else 0.0
    baseline_commit = float(mild["online_frac"].mean()) if len(mild) else 0.0
    drive = flagged["nl"] - threshold_gw
    slope = float(np.polyfit(drive, flagged["cf"], 1)[0]) if n >= 2 else 0.0
    rho = (
        float(drive.corr(flagged["cf"], method="spearman"))
        if n >= 2 and drive.nunique() > 1
        else float("nan")
    )
    return {
        "commit_frac": commit_frac,
        "baseline": baseline,
        "baseline_commit": baseline_commit,
        "slope": slope,
        "rho": rho,
        "n": n,
    }


# Net-load threshold percentile for the onset: the daily peak net-load above
# which the CT fleet begins to mobilise. Analogous to HOT_PERCENTILE (p95 tmax)
# but on the net-load scale — the tightest ~30% of days see CT commitment rise.
NETLOAD_ONSET_PERCENTILE = 70.0


def _netload_threshold_gw(daily_nl: pd.DataFrame) -> tuple[float, str]:
    """Return ``(threshold_gw, basis)`` for a net-load limb."""
    thr = float(
        np.percentile(daily_nl["peak_nl_gw"].dropna(), NETLOAD_ONSET_PERCENTILE)
    )
    return thr, (
        f"netload: system p{int(NETLOAD_ONSET_PERCENTILE)} daily-peak net-load "
        f"(demand - VRE) GW"
    )


def _limb_threshold(
    iso: str, klass: str, driver: str, zt: pd.DataFrame
) -> tuple[float, str]:
    """Return ``(threshold_c, basis)`` for one limb (plan D; physical anchors).

    Hot (``tmax``): the zone's :data:`HOT_PERCENTILE` TMAX (design cooling day —
    no ISO publishes a hot trigger). Cold (``tmin``): PJM's documented
    Cold-Weather-Alert −12 °C (−20.5 °C for CT classes' extra mobilization tier)
    for the PJM footprint, else the zone's :data:`COLD_PERCENTILE` TMIN (design
    heating day). The basis string is carried into the CSV ``threshold_basis``
    column so each onset cites its operational criterion.
    """
    if driver == "tmax":
        thr = float(np.percentile(zt["tmax_c"].dropna(), HOT_PERCENTILE))
        return thr, f"hot: zone p{int(HOT_PERCENTILE)} tmax (design cooling day)"
    # cold limb (tmin)
    if iso == "PJM":
        if klass in _CT_CLASSES:
            return (
                PJM_COLD_CT_MOBILIZE_C,
                "cold: PJM Manual 13 CT-mobilization tier (tmin<=-5F/-20.5C)",
            )
        return (
            PJM_COLD_ALERT_C,
            "cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C)",
        )
    thr = float(np.percentile(zt["tmin_c"].dropna(), COLD_PERCENTILE))
    return thr, f"cold: zone p{int(COLD_PERCENTILE)} tmin (design heating day)"


def derive_iso(iso: str) -> pd.DataFrame:
    """Derive the full per-(zone, class, limb) coefficient table for one ISO."""
    iso = iso.upper()
    temps = _zone_temps(iso)
    pmap = _plant_map(iso)
    if pmap.empty:
        log.warning("%s: empty plant map; no coefficients derived", iso)
        return pd.DataFrame()

    pmap = pmap[pmap["plant_class"].isin(FOSSIL_CLASSES)].copy()
    all_codes = set(pmap["plant_code"].astype(int))
    campd = _load_campd(iso, all_codes)

    # Pre-load system net-load for the netload-driven classes, restricted to
    # the derivation span (the zone-temperature file's coverage) so the
    # threshold percentile matches the CF-regression span and never consumes
    # holdout-period data (rule 22).
    _daily_nl: pd.DataFrame | None = None
    if iso in _NETLOAD_BA_FILES:
        try:
            _daily_nl = _system_net_load(iso, temps["date"].min(), temps["date"].max())
        except FileNotFoundError:
            log.warning("%s: EIA-930 BA hourly missing; netload limbs skipped", iso)

    rows: list[dict] = []
    for (zone, klass), grp in pmap.groupby(["zone", "plant_class"], sort=False):
        plant_npl = dict(
            zip(grp["plant_code"].astype(int), grp["nameplate_mw"].astype(float))
        )
        nameplate = float(grp["nameplate_mw"].sum())
        min_stable_pct = _min_stable_pct(klass)
        cf = _group_daily_cf(campd, plant_npl, nameplate)
        if cf.empty:
            continue
        zt = temps[temps["zone"] == zone].set_index("date")
        if zt.empty:
            continue

        # Net-load-driven limbs: CAISO CT (duck-curve evening ramp) and NEISO
        # ST_GAS (rule-19 re-grounding, 2026-07-06). The NEISO legacy-steam
        # fleet (Montville) is committed by ISO-NE on TIGHT-SYSTEM days — both
        # the Feb-2023 arctic blast AND the post-Mystic Jun-Aug 2024/2025 heat
        # events — so neither temperature limb alone identifies it (the CSV's
        # tmax limb fit ρ=0.23 < RHO_MIN; the tmin limb n=8 < N_MIN; both ship
        # disabled). Daily peak net-load unifies the hot and cold commitment
        # driver (median committed day sits at the p93 of daily-peak net-load;
        # Spearman ρ≈0.5 on the flagged span, n≈330), exactly the CAISO-CT
        # precedent (rebuild-plan review decision 2: a net-load limb carries no
        # temperature gate).
        netload_limb = (iso == "CAISO" and klass in _CT_CLASSES) or (
            iso == "NEISO" and klass == "ST_GAS"
        )

        if netload_limb:
            # Net-load driver: regress daily class CF on daily peak system
            # net-load (GW). One limb per (zone, class).
            if _daily_nl is None:
                continue
            threshold, basis = _netload_threshold_gw(_daily_nl)
            fit = _fit_netload_limb(cf, _daily_nl, threshold)
            if fit is None:
                continue
            floor_pct = float(fit["commit_frac"] * min_stable_pct)
            r1 = _r1_disabled(iso, zone, klass, "netload")
            enabled = (
                bool(
                    (not np.isnan(fit["rho"]))
                    and fit["rho"] >= RHO_MIN
                    and fit["n"] >= N_MIN
                    and fit["commit_frac"] > fit["baseline_commit"]
                )
                and not r1
            )
            rows.append(
                {
                    "iso": iso,
                    "zone": zone,
                    "plant_class": klass,
                    "driver": "netload",
                    "threshold": round(threshold, 2),
                    "floor_pct": round(floor_pct, 4),
                    "enabled": enabled,
                    "commit_frac": round(fit["commit_frac"], 4),
                    "min_stable_pct": round(min_stable_pct, 4),
                    "rho": round(fit["rho"], 4) if not np.isnan(fit["rho"]) else "",
                    "n": fit["n"],
                    "baseline": round(fit["baseline"], 4),
                    "baseline_commit": round(fit["baseline_commit"], 4),
                    "threshold_basis": basis,
                    "r1_disabled": r1,
                    # CAISO CT net-load limbs are the duck-curve evening ramp:
                    # window them to the same afternoon-evening footprint.
                    "start_hour": (
                        _CT_EVENING_WINDOW[0] if klass == "CT_PEAKER" else ""
                    ),
                    "end_hour": (_CT_EVENING_WINDOW[1] if klass == "CT_PEAKER" else ""),
                }
            )
            continue

        for driver, cold in (("tmax", False), ("tmin", True)):
            threshold, basis = _limb_threshold(iso, klass, driver, zt)
            fit = _fit_limb(cf, zt[f"{driver}_c"], threshold, cold)
            if fit is None:
                continue
            floor_pct = float(fit["commit_frac"] * min_stable_pct)
            r1 = _r1_disabled(iso, zone, klass, driver)
            enabled = (
                bool(
                    (not np.isnan(fit["rho"]))
                    and fit["rho"] >= RHO_MIN
                    and fit["n"] >= N_MIN
                    and fit["commit_frac"] > fit["baseline_commit"]
                )
                and not r1
            )
            rows.append(
                {
                    "iso": iso,
                    "zone": zone,
                    "plant_class": klass,
                    "driver": driver,
                    "threshold": round(threshold, 2),
                    "floor_pct": round(floor_pct, 4),
                    "enabled": enabled,
                    "commit_frac": round(fit["commit_frac"], 4),
                    "min_stable_pct": round(min_stable_pct, 4),
                    "rho": round(fit["rho"], 4) if not np.isnan(fit["rho"]) else "",
                    "n": fit["n"],
                    "baseline": round(fit["baseline"], 4),
                    "baseline_commit": round(fit["baseline_commit"], 4),
                    "threshold_basis": basis,
                    "r1_disabled": r1,
                    # CT peakers serve only the afternoon-evening ramp; window
                    # the floor so a full-day temp gate can't bind them overnight
                    # (rule 13 / D-4). CT_CHP steam-host runs all hours: no window.
                    "start_hour": (
                        _CT_EVENING_WINDOW[0] if klass == "CT_PEAKER" else ""
                    ),
                    "end_hour": (_CT_EVENING_WINDOW[1] if klass == "CT_PEAKER" else ""),
                }
            )
    return pd.DataFrame(rows)


def _write_markdown(iso: str, table: pd.DataFrame) -> None:
    """Append a human-readable per-ISO section to the coefficient markdown."""
    md_path = RAW_DIR.parent / "multi-iso" / "reliability-floor-coefficients.md"
    # docs path: repo docs/multi-iso/ (RAW_DIR is data/raw, so go to repo root).
    repo_root = RAW_DIR.parent.parent
    md_path = repo_root / "docs" / "multi-iso" / "reliability-floor-coefficients.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    header = (
        "# Temperature reliability-floor coefficients\n\n"
        "Derived by `scripts/derive_reliability_coeffs.py`. `floor_pct = "
        "commit_frac x min_stable_pct`, where `min_stable_pct` is the class's "
        "PHYSICAL Pmin/Pmax of a committed unit (NREL WWSIS-2 Table 7, "
        "`constants.MIN_STABLE_PCT_PHYSICAL`), NOT the offer-curve must-run share "
        "(never residual-tuned, CLAUDE.md #9/#11). A limb is `enabled` only when "
        "`rho >= 0.3`, `n >= 30`, and `commit_frac > baseline_commit` (the "
        "flagged-day online share exceeds the mild-day online share — a "
        "like-for-like commitment test); weak limbs ship OFF but stay visible "
        "below. Onsets (`threshold`, °C) are physical anchors: hot = per-zone "
        "p95 tmax (design cooling day); cold = PJM Cold-Weather-Alert "
        "−12 °C / −20.5 °C (CT tier), else per-zone p1 tmin. See "
        "`threshold_basis` per row.\n"
    )
    existing = ""
    if md_path.exists():
        existing = md_path.read_text()
    if not existing.startswith("# Temperature reliability-floor coefficients"):
        existing = header

    # Strip any prior section for this ISO so re-runs are idempotent.
    marker = f"\n## {iso}\n"
    if marker in existing:
        existing = existing.split(marker)[0]
    if not existing.endswith("\n"):
        existing += "\n"

    lines = [f"\n## {iso}\n"]
    if table.empty:
        lines.append("\n_No coefficients derived (no data)._\n")
    else:
        cols = [
            "zone",
            "plant_class",
            "driver",
            "threshold",
            "floor_pct",
            "enabled",
            "commit_frac",
            "min_stable_pct",
            "rho",
            "n",
            "baseline",
            "baseline_commit",
            "threshold_basis",
            "r1_disabled",
        ]
        lines.append("\n| " + " | ".join(cols) + " |\n")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|\n")
        for r in table.itertuples(index=False):
            lines.append("| " + " | ".join(str(getattr(r, c)) for c in cols) + " |\n")
    md_path.write_text(existing + "".join(lines))
    log.info("wrote markdown section -> %s", md_path)


def _derive_one(iso: str) -> None:
    """Derive + write the coefficient CSV and markdown section for one ISO."""
    try:
        table = derive_iso(iso)
    except FileNotFoundError as exc:
        log.error("%s: %s", iso, exc)
        return

    out_csv = REFERENCE_DIR / f"reliability_floor_coeffs_{iso}.csv"
    if table.empty:
        log.warning("%s: no coefficient rows produced; CSV not written", iso)
    else:
        table.to_csv(out_csv, index=False)
        n_on = int(table["enabled"].sum())
        log.info("%s: %d limbs (%d enabled) -> %s", iso, len(table), n_on, out_csv)
    _write_markdown(iso, table)


def main() -> None:
    """CLI: derive the coefficient CSV(s) + markdown for one ISO or ``ALL``."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True, help="ISO to derive (e.g. ERCOT), or ALL.")
    args = ap.parse_args()
    iso = args.iso.upper()

    if iso == "ALL":
        # Rebuild the shared markdown from scratch so a full re-run is idempotent
        # (each ISO section is otherwise only stripped/re-appended in place).
        md_path = (
            RAW_DIR.parent.parent
            / "docs"
            / "multi-iso"
            / "reliability-floor-coefficients.md"
        )
        if md_path.exists():
            md_path.unlink()
        for one in ISO_CAMPD_STATES:
            _derive_one(one)
        return

    _derive_one(iso)


if __name__ == "__main__":
    main()
