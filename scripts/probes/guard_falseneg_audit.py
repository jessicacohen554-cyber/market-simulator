"""Merit-order guard FALSE-NEGATIVE audit — cross-ISO, no-LP, pre-registered.

THE QUESTION (owner-raised 2026-07-27). The merit-order guard
(`scripts/lib/outage_detect.py`, charter
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §3a, owner-adopted
2026-07-26 §8) drops a CAMPD outage window when the unit was plausibly OUT OF
MERIT across it. It does NOT test whether the unit was also mechanically
capable. A unit that breaks during a stretch when it is ALSO uneconomic is
indistinguishable from economic layup on that discriminator and gets erased.
If that happens materially, the corrected envelope UNDER-counts outages in
exactly the wrong hours => too much available capacity => prices too low and
too few scarcity hours (directionally, PJM's post-guard misses: C3a-2025
-10.6 %, C3c 0.39x/0.47x — `FINDING-pjm129-keeper-reaudit-meritguard-2026-07.md`).

THIS LANE AUDITS THE GUARD; IT DOES NOT CHANGE IT. The guard is owner-adopted
and frozen against residuals (rule 23 [R-FROZEN-DERIVE]); a fix would be a
separate memo with owner sign-off. Nothing here modifies `outage_detect.py`,
re-derives any extract, tunes anything to a price residual (rules 1/13/26),
touches a holdout year (rule 22), or edits keepers/frontier state. No LP is
solved, so there is nothing to register (rule 15).

POPULATION. Per ISO, committed bytes only: the guard-on extract
`campd-unit-outages[-<ISO>].csv` (KEPT windows) and its companion
`campd-unit-outages-layup[-<ISO>].csv` (DROPPED windows, the guard's vetoes);
their union is the guard-off baseline. Window selection and the day clock
follow the established cross-ISO machinery (`_campd_daygrain_crossiso.py`):
windows whose `outage_start` falls in the scored years, on a shared
2023-01-01..2025-12-31 day clock, spans clipped to the clock. Per-year
statistics score each year's days.

THREE MEASUREMENTS per (ISO, year), 2023/2024/2025:

D1 — DROP INVENTORY (descriptive, no gate). GW-days dropped by the guard, by
  `plant_group` class and by calendar month, plus the dropped share of
  baseline (kept+dropped) outage GW-days. In-clock whole days x
  `unit_capacity_mw` / 1000.

D2 — POPULATION TEST (the NEISO positive control of charter §3a D1, ported to
  the DROPPED side). The dropped windows' daily-MW series, correlated monthly
  (12 monthly means per year, Pearson r, the `level_and_r` construction)
  against the ISO's published instrument (charter §4 anchors):
    NEISO  ISO-NE Morning Report Section 3 — publishes BOTH populations:
           `gen_outages_reductions_mw` (mechanical) and
           `uncommitted_available_gen_nonfast_mw` (available-not-committed).
    MISO   native outage source (Forced+Planned+Unplanned) — outages only.
    PJM    Data Miner 2 gen_outages_by_type, PJM RTO, lead_days=0 — outages only.
    ERCOT  60-day DAM disclosure `rating_mw - live_mw` — CAVEAT (charter §4):
           DAM offered capacity conflates mechanical unavailability with a
           unit that simply did not offer, so this instrument carries some of
           the layup population itself and a D2 fire here is over-called by
           construction; the verdict carries this caveat wherever quoted.
    CAISO  CNOG, reviewed crosswalk, revision-aware build, active-plant scope
           (both sides restricted identically; `_neiso65_cnog_revision_rebuild`).
           Note: CNOG's non-operational bucket can itself include long-term
           economic states; the active-plant scope mitigates but does not
           eliminate this.
    NYISO  NO published anchor. D2 is UNVERIFIABLE; no proxy is substituted.
  YEAR-LEVEL RULE, pre-registered:
    * NEISO (two-population instrument): FIRE iff
      r(dropped, published OUTAGES) > r(dropped, published UNCOMMITTED) —
      the dropped windows look more like the mechanical population than the
      layup population they are claimed to be.
    * CAISO / MISO / PJM / ERCOT (outage-only instruments): the two-sided rule
      cannot be evaluated as stated, so the pre-registered degraded form is
      one-sided against the charter's own placebo null: FIRE iff
      r(dropped, published OUTAGES) > placebo p95, where the placebo drops the
      SAME in-year GW-days at random from the same baseline (30 draws). A
      random same-size drop carries the baseline's mixture of populations; a
      drop set that tracks the published mechanical series ABOVE that null is
      being selected FOR mechanical outages — the false-negative signature.
      (Under a clean guard the drop set is layup and should sit at or below
      the placebo median; NEISO's committed split measures its dropped set at
      r = -0.26/+0.01/+0.24 against published outages, charter §3a D1.)

D3 — TIGHTNESS PLACEMENT (the smoking gun). Hourly EIA-930 net load
  (Demand - wind - solar, `_eia_hourly_frame_filled` keyed on the eGRID BA
  code via `zone_assignment._ISO_TO_BA_CODE`), percentile-ranked within each
  ISO-year. TIGHT = the top net-load quartile (rank >= TIGHT_QUARTILE = 0.75).
  Statistic: the MW-weighted share of DROPPED window-hours falling in the
  tight quartile (windows are day-grain, so a window contributes its days'
  hours weighted by `unit_capacity_mw`). Economic layup must concentrate in
  LOW net-load hours; a genuine forced outage is independent of net load.
  YEAR-LEVEL RULE, pre-registered: FIRE iff the dropped tight-quartile share
  exceeds the proportion-matched placebo p95 (same in-year GW-days dropped at
  random from the same baseline, 30 draws — the charter's placebo machinery).
  The kept set's share is reported for context (no gate on it).

PRE-REGISTERED VERDICT (kill criteria — unmet-means-dead):
  * A discriminator FIRES for an ISO iff its year rule fires in >= 2 of the 3
    scored years. A non-finite measurement never fires (fail-safe).
  * CLEAN        — neither D2 nor D3 fires.
  * SUSPECT      — exactly one of D2/D3 fires.
  * CONFIRMED    — both fire: that ISO's corrected envelope under-counts
                   outages in tight hours and its post-guard re-tune has a
                   NAMED root cause.
  * UNVERIFIABLE — no published anchor (NYISO): D2 unmeasurable, verdict is
                   UNVERIFIABLE regardless of D3; D1/D3 are still reported
                   descriptively, recorded for when an anchor lands.
  * Constants: TIGHT_QUARTILE = 0.75, PLACEBO_DRAWS = 30, SEED = 20260727,
    YEARS = 2023/2024/2025 (rule 22: no holdout year is touched).

PLACEBO CONSTRUCTION (shared by D2-degraded and D3, one draw set per
ISO-year): permute the baseline windows; accumulate their IN-YEAR GW-days
until the year's dropped in-year GW-days target is met; the accumulated set is
the draw's drop set. This is the charter's proportion-matched placebo with the
GW-day matching applied per year (the charter's own applied it over the full
range); the per-year form is what a per-year band requires and is disclosed
here at the site (pjm-131 §4 / pjm-132 §4 precedent for site disclosure).

PORT CHECK (machinery control, not a verdict input): on NEISO the probe
reprints the dropped-side correlations next to the charter §3a D1 reference
values (vetoed vs OUTAGES -0.26/+0.01/+0.24; vs UNCOMMITTED
+0.77/+0.71/+0.67) and warns if |delta| > 0.05 — the ported machinery must
land on the charter's own numbers before any cross-ISO reading is taken.

SETTLED, NOT RE-LITIGATED HERE: the guard stays in (owner verdict 2026-07-26);
window-level classification; common-mode ruled out; the NEISO residual
over-count (1.29-1.36x) is a separate open item; NEISO's kept-side positive
control is not re-run — its METHOD is ported to the dropped side.

Usage::

    PYTHONPATH=. .venv/bin/python scripts/probes/guard_falseneg_audit.py \\
        --json results/calibration/guard_falseneg_audit_2026-07.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

RAW = REPO / "data" / "raw"

# Committed guard-on extract + layup companion per ISO (union = baseline).
_EXTRACTS: dict[str, tuple[str, str]] = {
    "ERCOT": ("campd-unit-outages.csv", "campd-unit-outages-layup.csv"),
    "CAISO": ("campd-unit-outages-CAISO.csv", "campd-unit-outages-layup-CAISO.csv"),
    "MISO": ("campd-unit-outages-MISO.csv", "campd-unit-outages-layup-MISO.csv"),
    "NEISO": ("campd-unit-outages-NEISO.csv", "campd-unit-outages-layup-NEISO.csv"),
    "NYISO": ("campd-unit-outages-NYISO.csv", "campd-unit-outages-layup-NYISO.csv"),
    "PJM": ("campd-unit-outages-PJM.csv", "campd-unit-outages-layup-PJM.csv"),
}
ISOS = ("ERCOT", "CAISO", "MISO", "NEISO", "NYISO", "PJM")
YEARS = (2023, 2024, 2025)

#: Pre-registered constants (docstring, kill criteria). Not tunables.
TIGHT_QUARTILE = 0.75
PLACEBO_DRAWS = 30
SEED = 20260727
#: Port-check tolerance on the NEISO charter reference values (machinery flag).
PORT_CHECK_TOL = 0.05
#: Charter §3a D1 reference: NEISO VETOED windows, monthly r, 2023/2024/2025.
NEISO_REF_VETOED_R_OUT = {2023: -0.26, 2024: +0.01, 2025: +0.24}
NEISO_REF_VETOED_R_UNC = {2023: +0.77, 2024: +0.71, 2025: +0.67}


# --------------------------------------------------------------------------- #
# window population (committed bytes; day clock as _campd_daygrain_crossiso)   #
# --------------------------------------------------------------------------- #
@dataclass
class WindowSet:
    """Baseline window population for one ISO on the shared 3-year day clock."""

    frame: pd.DataFrame
    day0: pd.Timestamp
    n_days: int
    a_day: np.ndarray  # clipped start day index
    b_day: np.ndarray  # clipped end day index (inclusive)
    mw: np.ndarray
    was_layup: np.ndarray  # True = DROPPED by the guard (layup companion)


def load_windows(iso: str, years: list[int], plant_filter: set[int] | None) -> WindowSet:
    """Committed extract UNION layup companion — the guard-off baseline."""
    kept_name, layup_name = _EXTRACTS[iso.upper()]

    def _rd(name: str, flag: bool) -> pd.DataFrame:
        d = pd.read_csv(RAW / name, parse_dates=["outage_start", "outage_end"])
        d = d[d["outage_start"].dt.year.isin(years)].copy()
        d["was_layup"] = flag
        return d

    d = pd.concat([_rd(kept_name, False), _rd(layup_name, True)], ignore_index=True)
    if plant_filter is not None:
        d = d[d["facility_id"].isin(plant_filter)].copy()
    day0 = pd.Timestamp(f"{min(years)}-01-01")
    last = pd.Timestamp(f"{max(years)}-12-31")
    n_days = int((last - day0).days) + 1
    a = np.clip((d["outage_start"] - day0).dt.days.to_numpy(dtype=int), 0, n_days - 1)
    b = np.clip((d["outage_end"] - day0).dt.days.to_numpy(dtype=int), 0, n_days - 1)
    return WindowSet(
        frame=d.reset_index(drop=True),
        day0=day0,
        n_days=n_days,
        a_day=a,
        b_day=np.maximum(a, b),
        mw=d["unit_capacity_mw"].to_numpy(dtype=float),
        was_layup=d["was_layup"].to_numpy(dtype=bool),
    )


def daily_series(ws: WindowSet, mask: np.ndarray) -> pd.Series:
    """Daily outage MW implied by a window subset (difference-array, O(n))."""
    diff = np.zeros(ws.n_days + 1, dtype=float)
    np.add.at(diff, ws.a_day[mask], ws.mw[mask])
    np.add.at(diff, ws.b_day[mask] + 1, -ws.mw[mask])
    idx = pd.date_range(ws.day0, periods=ws.n_days, freq="D")
    return pd.Series(np.cumsum(diff)[: ws.n_days], index=idx)


def year_span(ws: WindowSet, year: int) -> tuple[int, int]:
    """(first, last) day-clock indices of ``year`` (inclusive)."""
    y0 = int((pd.Timestamp(f"{year}-01-01") - ws.day0).days)
    y1 = int((pd.Timestamp(f"{year}-12-31") - ws.day0).days)
    return max(y0, 0), min(y1, ws.n_days - 1)


def inyear_days(ws: WindowSet, year: int) -> np.ndarray:
    """Per-window whole days falling inside ``year`` (0 where disjoint)."""
    y0, y1 = year_span(ws, year)
    return np.maximum(
        0, np.minimum(ws.b_day, y1) - np.maximum(ws.a_day, y0) + 1
    ).astype(float)


# --------------------------------------------------------------------------- #
# published instruments (charter §4)                                           #
# --------------------------------------------------------------------------- #
@dataclass
class Published:
    outages: pd.Series
    label: str
    caveat: str | None = None
    uncommitted: pd.Series | None = None  # only NEISO separates the populations
    plant_filter: set[int] | None = None  # only CAISO restricts the scope


def published(iso: str, years: list[int]) -> Published | None:
    """The ISO's published anchor; ``None`` for an ISO with none (NYISO)."""
    iso = iso.upper()
    if iso == "NEISO":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW / "neiso-operable-capacity" / f"neiso_operable_capacity_{y}.csv",
                    parse_dates=["report_date"],
                )
                for y in years
            ]
        ).set_index("report_date")
        return Published(
            outages=d["gen_outages_reductions_mw"].astype(float),
            label="ISO-NE Morning Report Section 3 (outages AND uncommitted)",
            uncommitted=d["uncommitted_available_gen_nonfast_mw"].astype(float),
        )
    if iso == "MISO":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW / "miso-generation-outages" / f"miso_outages_estimated_{y}.csv",
                    parse_dates=["interval_date"],
                )
                for y in years
            ]
        ).set_index("interval_date")
        return Published(
            outages=(d["MISO_Forced"] + d["MISO_Planned"] + d["MISO_Unplanned"]).astype(
                float
            ),
            label="MISO native outage source (Forced+Planned+Unplanned)",
        )
    if iso == "PJM":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW / "pjm-outages" / "by-year" / f"gen_outages_by_type_{y}.csv",
                    parse_dates=["forecast_date"],
                )
                for y in years
            ]
        )
        d = d[(d["region"] == "PJM RTO") & (d["lead_days"] == 0)]
        return Published(
            outages=d.groupby("forecast_date")["total_outages_mw"].mean().astype(float),
            label="PJM Data Miner 2 gen_outages_by_type, PJM RTO lead_days=0",
        )
    if iso == "ERCOT":
        d = pd.read_csv(RAW / "ercot-thermal-dam-availability.csv", parse_dates=["date"])
        d = d[d["date"].dt.year.isin(years)]
        return Published(
            outages=(
                d.assign(out=d["rating_mw"] - d["live_mw"])
                .groupby("date")["out"]
                .sum()
                .astype(float)
            ),
            label="ERCOT 60-day DAM disclosure rating_mw - live_mw",
            caveat=(
                "DAM offered capacity conflates mechanical unavailability with "
                "not-offered (carries some layup itself); a D2 fire here is "
                "over-called by construction"
            ),
        )
    if iso == "CAISO":
        from scripts.probes._neiso65_cnog_revision_rebuild import (
            _segments,
            build_revision,
        )

        seg = _segments(years)
        by_plant = build_revision(seg, years)
        # Active-plant scope (the neiso-65 convention): both sides restricted to
        # crosswalked plants where the CAMPD baseline carries any signal.
        ws_all = load_windows("CAISO", years, None)
        active = {int(p) for p in ws_all.frame["facility_id"].unique()} & {
            int(c) for c in by_plant.columns
        }
        return Published(
            outages=by_plant[[c for c in by_plant.columns if int(c) in active]].sum(
                axis=1
            ),
            label="CAISO CNOG, reviewed crosswalk, revision-aware, active-plant scope",
            caveat=(
                "CNOG's non-operational bucket can itself include long-term "
                "economic states; active-plant scope mitigates, not eliminates"
            ),
            plant_filter=active,
        )
    return None


def monthly_r(model: pd.Series, pub: pd.Series, year: int) -> float:
    """Monthly Pearson r for one year (the established `level_and_r` shape)."""
    j = pd.concat([model.rename("m"), pub.rename("p")], axis=1).dropna()
    j = j[(j.index.year == year) & (j["p"] > 0)]
    if j.empty:
        return float("nan")
    mm = j.groupby(j.index.month)[["m", "p"]].mean()
    if len(mm) < 3:
        return float("nan")
    return float(mm["m"].corr(mm["p"]))


# --------------------------------------------------------------------------- #
# net load (D3)                                                                #
# --------------------------------------------------------------------------- #
def tight_hours_by_day(iso: str, years: list[int], day0: pd.Timestamp, n_days: int):
    """(tight_by_day, hours_by_day): per day-clock day, the count of hours in
    the ISO-year's top net-load quartile and of valid hours.

    Net load is measured EIA-930 Demand - wind - solar. The frame loader keys
    on the eGRID BA code, not the model ISO name (they coincide only for PJM
    and MISO) — `zone_assignment._ISO_TO_BA_CODE`. Percentile ranks are
    within-year over finite hours; rows with a NaT local time (DST edges) or a
    day absent from the model's non-leap clock (Feb 29) contribute to neither
    numerator nor denominator, symmetrically for every window set and placebo
    draw.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled
    from market_sim.data.zone_assignment import _ISO_TO_BA_CODE

    tight = np.zeros(n_days, dtype=float)
    hours = np.zeros(n_days, dtype=float)
    for year in years:
        df = _eia_hourly_frame_filled(_ISO_TO_BA_CODE.get(iso, iso), year)
        net = pd.to_numeric(df["Demand"], errors="coerce").interpolate(
            limit_direction="both"
        )
        for col in ("NG: WND", "NG: SUN"):
            if col in df.columns:
                net = net - pd.to_numeric(df[col], errors="coerce").interpolate(
                    limit_direction="both"
                )
        net = net.to_numpy(dtype=float)
        lt = pd.DatetimeIndex(df["Local time"])
        valid = lt.notna().to_numpy() & np.isfinite(net)
        v = net[valid]
        # within-year percentile rank in [0, 1]
        rank = np.empty(v.size, dtype=float)
        rank[np.argsort(v, kind="stable")] = np.arange(v.size, dtype=float) / max(
            v.size - 1, 1
        )
        is_tight = rank >= TIGHT_QUARTILE
        di = ((lt[valid].normalize() - day0).days).to_numpy(dtype=int)
        ok = (di >= 0) & (di < n_days)
        np.add.at(hours, di[ok], 1.0)
        np.add.at(tight, di[ok], is_tight[ok].astype(float))
    return tight, hours


def tight_share(
    ws: WindowSet,
    mask: np.ndarray,
    year: int,
    cum_tight: np.ndarray,
    cum_hours: np.ndarray,
) -> float:
    """MW-weighted share of the window subset's in-year hours that are tight."""
    y0, y1 = year_span(ws, year)
    a = np.maximum(ws.a_day[mask], y0)
    b = np.minimum(ws.b_day[mask], y1)
    live = b >= a
    a, b = a[live], b[live]
    mw = ws.mw[mask][live]
    t = (cum_tight[b + 1] - cum_tight[a]) * mw
    h = (cum_hours[b + 1] - cum_hours[a]) * mw
    tot = float(h.sum())
    return float(t.sum()) / tot if tot > 0 else float("nan")


# --------------------------------------------------------------------------- #
# placebo (shared by D2-degraded and D3; one draw set per ISO-year)            #
# --------------------------------------------------------------------------- #
def placebo_draws(
    ws: WindowSet, year: int, target_gwd: float, rng: np.random.Generator, draws: int
) -> list[np.ndarray]:
    """Proportion-matched drop masks: random windows until the year's dropped
    in-year GW-days target is met (windows with no in-year days are skipped)."""
    iyd = inyear_days(ws, year)
    gwd = ws.mw * iyd / 1000.0
    eligible = np.flatnonzero(iyd > 0)
    out = []
    for _ in range(draws):
        drop = np.zeros(len(ws.frame), dtype=bool)
        tot = 0.0
        for i in rng.permutation(eligible):
            if tot >= target_gwd:
                break
            drop[i] = True
            tot += gwd[i]
        out.append(drop)
    return out


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def run_iso(iso: str, years: list[int], draws: int, seed: int) -> dict:
    """All three measurements + the pre-registered verdict for one ISO."""
    iso = iso.upper()
    print(f"\n{'=' * 78}\n===== {iso} — merit-order guard false-negative audit =====")
    pub = published(iso, years)
    ws = load_windows(iso, years, pub.plant_filter if pub else None)
    dropped = ws.was_layup
    kept = ~dropped
    if pub is not None:
        print(f"  anchor: {pub.label}")
        if pub.caveat:
            print(f"  CAVEAT: {pub.caveat}")
    else:
        print("  NO PUBLISHED ANCHOR — D2 UNVERIFIABLE (none substituted).")
    scope_note = f" (anchor scope: {len(pub.plant_filter)} plants)" if pub and pub.plant_filter else ""
    print(
        f"  baseline windows {len(ws.frame):,} = kept {int(kept.sum()):,} "
        f"+ dropped {int(dropped.sum()):,}{scope_note}"
    )

    tight_d, hours_d = tight_hours_by_day(iso, years, ws.day0, ws.n_days)
    cum_t = np.concatenate(([0.0], np.cumsum(tight_d)))
    cum_h = np.concatenate(([0.0], np.cumsum(hours_d)))

    drop_s = daily_series(ws, dropped)
    kept_s = daily_series(ws, kept)

    iso_idx = ISOS.index(iso)
    result: dict = {"iso": iso, "anchor": pub.label if pub else None,
                    "anchor_caveat": (pub.caveat if pub else None), "years": {}}
    d2_fired: list[bool] = []
    d3_fired: list[bool] = []

    for year in years:
        y0, y1 = year_span(ws, year)
        iyd = inyear_days(ws, year)
        gwd = ws.mw * iyd / 1000.0
        base_gwd = float(gwd.sum())
        drop_gwd = float(gwd[dropped].sum())
        yr: dict = {
            "d1_baseline_gwdays": round(base_gwd, 1),
            "d1_dropped_gwdays": round(drop_gwd, 1),
            "d1_dropped_share": round(drop_gwd / base_gwd, 4) if base_gwd else None,
        }

        # ---- D1: by class, by month (descriptive) --------------------------
        cls = ws.frame["plant_group"].astype(str).to_numpy()
        by_class = {}
        for c in sorted(set(cls)):
            m = cls == c
            cb, cd = float(gwd[m].sum()), float(gwd[m & dropped].sum())
            if cb > 0:
                by_class[c] = {
                    "baseline_gwd": round(cb, 1),
                    "dropped_gwd": round(cd, 1),
                    "dropped_share": round(cd / cb, 4),
                }
        yr["d1_by_class"] = by_class
        ydays = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        dmask = (drop_s.index >= ydays[0]) & (drop_s.index <= ydays[-1])
        month_gwd = (
            drop_s[dmask].groupby(drop_s[dmask].index.month).sum() / 1000.0
        )
        yr["d1_dropped_gwd_by_month"] = {
            int(m): round(float(v), 1) for m, v in month_gwd.items()
        }

        # ---- shared placebo draw set for this ISO-year ---------------------
        rng = np.random.default_rng([seed, iso_idx, year])
        masks = placebo_draws(ws, year, drop_gwd, rng, draws)

        # ---- D2: population test ------------------------------------------
        d2_fire = False
        if pub is not None:
            r_out = monthly_r(drop_s, pub.outages, year)
            r_kept = monthly_r(kept_s, pub.outages, year)
            yr["d2_r_dropped_vs_outages"] = round(r_out, 3)
            yr["d2_r_kept_vs_outages"] = round(r_kept, 3)
            if pub.uncommitted is not None:
                r_unc = monthly_r(drop_s, pub.uncommitted, year)
                yr["d2_r_dropped_vs_uncommitted"] = round(r_unc, 3)
                d2_fire = bool(
                    np.isfinite(r_out) and np.isfinite(r_unc) and r_out > r_unc
                )
                yr["d2_rule"] = "two-population: r_out > r_unc"
                ref_o = NEISO_REF_VETOED_R_OUT.get(year)
                ref_u = NEISO_REF_VETOED_R_UNC.get(year)
                if ref_o is not None:
                    port_ok = (
                        abs(r_out - ref_o) <= PORT_CHECK_TOL
                        and abs(r_unc - ref_u) <= PORT_CHECK_TOL
                    )
                    yr["port_check"] = {
                        "r_out": (round(r_out, 3), ref_o),
                        "r_unc": (round(r_unc, 3), ref_u),
                        "ok": bool(port_ok),
                    }
                    if not port_ok:
                        print(
                            f"  {year}: PORT-CHECK WARN — dropped-side r "
                            f"({r_out:+.2f}/{r_unc:+.2f}) vs charter reference "
                            f"({ref_o:+.2f}/{ref_u:+.2f}) beyond ±{PORT_CHECK_TOL}"
                        )
            else:
                plc = [monthly_r(daily_series(ws, m), pub.outages, year) for m in masks]
                plc = [r for r in plc if np.isfinite(r)]
                p95 = float(np.percentile(plc, 95)) if plc else float("nan")
                p50 = float(np.percentile(plc, 50)) if plc else float("nan")
                yr["d2_placebo_p95"] = round(p95, 3)
                yr["d2_placebo_p50"] = round(p50, 3)
                d2_fire = bool(
                    np.isfinite(r_out) and np.isfinite(p95) and r_out > p95
                )
                yr["d2_rule"] = "degraded one-sided: r_out > placebo p95"
            yr["d2_fire"] = d2_fire
            d2_fired.append(d2_fire)

        # ---- D3: tightness placement --------------------------------------
        ts_drop = tight_share(ws, dropped, year, cum_t, cum_h)
        ts_kept = tight_share(ws, kept, year, cum_t, cum_h)
        plc_ts = [tight_share(ws, m, year, cum_t, cum_h) for m in masks]
        plc_ts = [t for t in plc_ts if np.isfinite(t)]
        ts_p95 = float(np.percentile(plc_ts, 95)) if plc_ts else float("nan")
        ts_p50 = float(np.percentile(plc_ts, 50)) if plc_ts else float("nan")
        d3_fire = bool(np.isfinite(ts_drop) and np.isfinite(ts_p95) and ts_drop > ts_p95)
        yr.update(
            {
                "d3_tight_share_dropped": round(ts_drop, 4),
                "d3_tight_share_kept": round(ts_kept, 4),
                "d3_placebo_p95": round(ts_p95, 4),
                "d3_placebo_p50": round(ts_p50, 4),
                "d3_fire": d3_fire,
            }
        )
        d3_fired.append(d3_fire)

        top_cls = sorted(by_class.items(), key=lambda kv: -kv[1]["dropped_gwd"])[:3]
        cls_txt = ", ".join(f"{c} {v['dropped_gwd']:.0f}" for c, v in top_cls)
        print(
            f"  {year}: D1 dropped {drop_gwd:7.1f} of {base_gwd:8.1f} GWd "
            f"({100 * drop_gwd / base_gwd:4.1f} %)  top classes: {cls_txt}"
        )
        if pub is not None:
            if pub.uncommitted is not None:
                print(
                    f"        D2 dropped r vs OUT {yr['d2_r_dropped_vs_outages']:+.2f} "
                    f"vs UNC {yr['d2_r_dropped_vs_uncommitted']:+.2f} "
                    f"(kept vs OUT {yr['d2_r_kept_vs_outages']:+.2f})"
                    f"  -> {'FIRE' if d2_fire else 'clean'}"
                )
            else:
                print(
                    f"        D2 dropped r vs OUT {yr['d2_r_dropped_vs_outages']:+.2f} "
                    f"placebo p50 {yr['d2_placebo_p50']:+.2f} p95 {yr['d2_placebo_p95']:+.2f} "
                    f"(kept {yr['d2_r_kept_vs_outages']:+.2f})"
                    f"  -> {'FIRE' if d2_fire else 'clean'}"
                )
        print(
            f"        D3 tight-share dropped {ts_drop:.3f} kept {ts_kept:.3f} "
            f"placebo p50 {ts_p50:.3f} p95 {ts_p95:.3f}"
            f"  -> {'FIRE' if d3_fire else 'clean'}"
        )
        result["years"][year] = yr

    # ---- pre-registered verdict -------------------------------------------
    if pub is None:
        verdict = "UNVERIFIABLE"
        d3_iso = sum(d3_fired) >= 2
        note = (
            f"no published anchor; D3 {'fires' if d3_iso else 'clean'} "
            f"({sum(d3_fired)}/3) — recorded for when an anchor lands"
        )
    else:
        d2_iso = sum(d2_fired) >= 2
        d3_iso = sum(d3_fired) >= 2
        verdict = (
            "CONFIRMED" if (d2_iso and d3_iso)
            else "SUSPECT" if (d2_iso or d3_iso)
            else "CLEAN"
        )
        note = f"D2 {sum(d2_fired)}/3 ({'fires' if d2_iso else 'clean'}), " \
               f"D3 {sum(d3_fired)}/3 ({'fires' if d3_iso else 'clean'})"
        if pub.caveat and verdict != "CLEAN":
            note += f" — CAVEAT: {pub.caveat}"
    result["verdict"] = verdict
    result["verdict_note"] = note
    print(f"  VERDICT {iso}: {verdict}  [{note}]")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(ISOS))
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--placebo-draws", type=int, default=PLACEBO_DRAWS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    years = sorted(args.years)
    if any(y not in (2023, 2024, 2025) for y in years):
        raise SystemExit(
            "rule 22 [R-HOLDOUT]: this probe scores 2023-2025 only; "
            f"refused years {sorted(set(years) - {2023, 2024, 2025})}"
        )
    results = [run_iso(i.upper(), years, args.placebo_draws, args.seed) for i in args.iso]

    print(f"\n{'=' * 78}\n===== PER-ISO VERDICTS (pre-registered; unmet-means-dead) =====")
    for r in results:
        print(f"  {r['iso']:6s} {r['verdict']:12s} {r['verdict_note']}")
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "probe": "guard_falseneg_audit",
                    "seed": args.seed,
                    "placebo_draws": args.placebo_draws,
                    "tight_quartile": TIGHT_QUARTILE,
                    "years": years,
                    "results": results,
                },
                indent=1,
                default=float,
            )
        )
        print(f"\n  json -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
