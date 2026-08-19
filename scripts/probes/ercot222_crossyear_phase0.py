"""ercot-222 Phase-0: the CROSS-YEAR-SEEDED expectation variant (read-only).

Executes docs/PRECOMMIT-ercot222-crossyear-seed-2026-08-19.md exactly as
pinned: NO LP, NO solve, NO arming. Evaluates the M-2 seed statistic (36-month
mean of the top-100 evening HE17-22 hourly RT prices) as a year-scale memory
level composed with the ARMED ercot-221 adaptive-expectation mechanism as
``P_hat(d) = clip(max(P_seed(d)/VOLL, beta*P_trail(d)), 0, 1)`` — the armed
member's own committed ``p_hat_day`` supplies the ``clip(beta*P_trail,0,1)``
term unchanged, so the seed enters purely as a floor under it (max, never
sum).

Purity convention (precommit §1): the seed's history is FROZEN at Jan-1 of
the solve year — no solve-year measured price enters the seed; the window
START rolls forward daily (span [d - 36 months, Jan-1-of-solve-year]) so the
seed decays by its own data composition. Seed history reads 2020-01-01
through 2024-12-31 ONLY (rule 22 data-not-score; the 2020-2022 reads are
DOF-ledgered in the finding); 2019 enters NO statistic; 2025 measured prices
are never read (the M-2 as-scanned ->2025 fidelity value is CITED from
RESEARCH-ercot221prep §2, not recomputed).

Gates (precommit §3): G-R, G-WINTER, G-C, G-S24, G-S25; LOYO structurally
N/A (zero new fitted scalars). All committed data, no solve:
- measured 2023 evening surface: results/calibration/ercot221_daily_surface_2023.json
  (monthly implied-P p50s inherited from ercot221_adaptive_phase0.json)
- year anchors: the ercot-210 committed p98-tightness p50s (2714/1281/990)
- model path: results/calibration/ercot221_adaptive_B/hourly/adaptive_<yr>.parquet
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ACTUAL = ROOT / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
ADAPTIVE_B = ROOT / "results/calibration/ercot221_adaptive_B/hourly"
PHASE0_JSON = ROOT / "results/calibration/ercot221_adaptive_phase0.json"
OUT = ROOT / "results/calibration/ercot222_crossyear_phase0.json"

# Pinned conventions — every value cited, none fitted here (rule 5).
VOLL = 5000.0  # ScenarioConfig.ordc_voll on the armed keeper (run_config.json)
WINDOW_MONTHS = 36  # M-2 statistic, RESEARCH-ercot221prep §2 (inherited)
TOP_N = 100  # M-2 statistic (inherited; selection freedom spent there)
FLOOR_WINDOW_HOD = (17, 18, 19, 20)  # ERCOT_ADAPTIVE_WINDOW_HOURS (hour-beginning CST)
VOM_PLUS_100 = 110.0  # storage vom $10 + $100 — the ercot-221 G-SAFE bar unchanged
BAND = 0.35  # the standing ±35 % monthly/anchor band (ercot-221 Phase-0)
ANCHORS = {2023: 2714.0, 2024: 1281.0, 2025: 990.0}  # ercot-210 p98-cut p50s
M2_AS_SCANNED = {2023: 3016.0, 2024: 1626.0, 2025: 1660.0}  # research §2 table
KILL_DAY_2024 = 3066 // 24  # day 127 — May-8-2024; h3066 is its HE18 (hod 18)
AUG1, SEP30 = 212, 272  # 0-based day-of-year, non-leap (ercot-221 phase0 conv.)


def load_evening(hod_set: tuple[int, ...]) -> pd.DataFrame:
    """Evening-hour actual RT rows, 2020-2024 ONLY, with approximate dates.

    2019 is never read into any statistic; 2025 rows are excluded before any
    computation touches them (rule 22 / precommit §2). The 8760-hour year
    maps day index -> calendar date as Jan-1 + d days (≤1-day drift after
    Feb in leap years — immaterial to a 36-month top-100 mean).
    """
    df = pd.read_parquet(ACTUAL)
    df = df[df["year"].isin([2020, 2021, 2022, 2023, 2024])].copy()
    df["day"] = df["hour"] // 24
    df["hod"] = df["hour"] % 24
    df = df[df["hod"].isin(hod_set)]
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-01-01") + pd.to_timedelta(
        df["day"], unit="D"
    )
    return df[["date", "rt"]].sort_values("date").reset_index(drop=True)


def seed_stat(ev: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float:
    """Mean of the top-TOP_N evening RT prices in [start, end); all if fewer."""
    sel = ev[(ev["date"] >= start) & (ev["date"] < end)]["rt"].to_numpy(float)
    if sel.size == 0:
        return 0.0
    k = min(TOP_N, sel.size)
    return float(np.sort(sel)[-k:].mean())


def daily_seed_series(ev: pd.DataFrame, year: int) -> np.ndarray:
    """P_seed(d) in $ for each of the solve year's 365 days (precommit §1)."""
    freeze = pd.Timestamp(year, 1, 1)
    out = np.zeros(365)
    for d in range(365):
        day_date = freeze + pd.Timedelta(days=d)
        start = day_date - pd.DateOffset(months=WINDOW_MONTHS)
        out[d] = seed_stat(ev, start, freeze)
    return out


def armed_daily_p_hat(year: int) -> np.ndarray:
    """The armed member's committed daily P_hat (365,) from its sidecar."""
    df = pd.read_parquet(ADAPTIVE_B / f"adaptive_{year}.parquet")
    df = df.sort_values("hour")
    ph = df["p_hat_day"].to_numpy(float)[:8760].reshape(365, 24)
    return ph.max(axis=1)


def armed_floor_hourly(year: int) -> np.ndarray:
    df = pd.read_parquet(ADAPTIVE_B / f"adaptive_{year}.parquet")
    return df.sort_values("hour")["floor_usd"].to_numpy(float)[:8760]


def seeded_floor_hourly(seed_usd: np.ndarray, armed_floor: np.ndarray) -> np.ndarray:
    """Hourly seeded floor: max(armed, clip(seed/VOLL,0,1)*VOLL) in-window."""
    hod = np.arange(8760) % 24
    day = np.arange(8760) // 24
    in_win = np.isin(hod, FLOOR_WINDOW_HOD)
    seed_floor = np.clip(seed_usd / VOLL, 0.0, 1.0)[day] * VOLL
    out = armed_floor.copy()
    out[in_win] = np.maximum(armed_floor[in_win], seed_floor[in_win])
    return out


def main() -> None:
    # --- hour-of-day convention: resolve HE17-22 against the M-2 fidelity
    # values (3,016 / 1,626 as-scanned, windows ending June-1). HE17-22 is
    # hour-ending 17..22 = hour-beginning 16..21; both candidate mappings are
    # computed and the reproducing one carries the probe (reported either way).
    fidelity = {}
    for label, hod_set in (("HB16-21 (HE17-22)", tuple(range(16, 22))),
                           ("HB17-22", tuple(range(17, 23)))):
        ev = load_evening(hod_set)
        rep = {}
        for yr in (2023, 2024):  # ->2025 needs Jan-May-2025 reads: cited, not computed
            end = pd.Timestamp(yr, 6, 1)
            start = end - pd.DateOffset(months=WINDOW_MONTHS)
            got = seed_stat(ev, start, end)
            rep[yr] = dict(
                as_scanned=M2_AS_SCANNED[yr],
                reproduced=round(got, 1),
                rel_err=round(got / M2_AS_SCANNED[yr] - 1, 4),
            )
        fidelity[label] = rep
    # pick the mapping with the smaller max |rel_err|
    pick = min(
        fidelity,
        key=lambda k: max(abs(v["rel_err"]) for v in fidelity[k].values()),
    )
    hod_set = tuple(range(16, 22)) if pick.startswith("HB16") else tuple(range(17, 23))
    ev = load_evening(hod_set)

    # --- seed series per solve year (purity form)
    seeds = {yr: daily_seed_series(ev, yr) for yr in (2023, 2024, 2025)}

    # --- G-R + G-WINTER (2023): seeded P_hat vs the measured monthly surface
    armed_ph23 = armed_daily_p_hat(2023)
    seeded_ph23 = np.maximum(armed_ph23, np.clip(seeds[2023] / VOLL, 0.0, 1.0))
    measured_monthly = {
        int(m): float(v)
        for m, v in json.load(open(PHASE0_JSON))["daily_monthly_measured_p50"].items()
    }
    doy_month = (
        pd.date_range("2023-01-01", periods=365).month.to_numpy()
    )
    monthly = {}
    for m in range(1, 13):
        msel = doy_month == m
        pred = float(np.median(seeded_ph23[msel]) * VOLL)
        meas = measured_monthly[m]
        monthly[m] = dict(
            measured_p50=round(meas, 1),
            seeded_p50=round(pred, 1),
            rel_err=round(pred / meas - 1, 4),
            in_band=bool(abs(pred / meas - 1) <= BAND),
        )
    n_band = sum(v["in_band"] for v in monthly.values())
    aug_sep_ok = monthly[8]["in_band"] and monthly[9]["in_band"]
    augsep_floor_mean = float(np.mean(seeded_ph23[AUG1 : SEP30 + 1]) * VOLL)
    g_r = dict(
        monthly=monthly,
        n_in_band=n_band,
        bar=">=5 months in ±35% incl BOTH Aug and Sep; Aug-Sep mean in-window "
            "seeded floor >= $2,200",
        aug_sep_in_band=bool(aug_sep_ok),
        aug_sep_mean_floor_usd=round(augsep_floor_mean, 1),
        ok=bool(n_band >= 5 and aug_sep_ok and augsep_floor_mean >= 2200.0),
    )

    # --- G-WINTER: Jan-Feb 2023 seeded P_hat p50 >= 0.65
    janfeb = seeded_ph23[:59]
    g_winter = dict(
        janfeb_p50=round(float(np.median(janfeb)), 4),
        bar=">= 0.65",
        ok=bool(float(np.median(janfeb)) >= 0.65),
    )

    # --- G-C: the seed's year-level predictions vs the ercot-210 anchors.
    # Reported at BOTH natural year-level readings of the pinned daily form —
    # the Jan-1 opening level (full 36-month window) and the annual mean of
    # the daily series (which carries the within-year decay). The gate takes
    # the CONJUNCTION (both readings in band) — under ambiguity the stricter
    # reading is the honest one; each is reported at full magnitude.
    g_c_years = {}
    for yr in (2024, 2025):
        anchor = ANCHORS[yr]
        jan1 = float(seeds[yr][0])
        ymean = float(seeds[yr].mean())
        g_c_years[yr] = dict(
            anchor_usd=anchor,
            jan1_seed_usd=round(jan1, 1),
            jan1_rel_err=round(jan1 / anchor - 1, 4),
            annual_mean_seed_usd=round(ymean, 1),
            annual_mean_rel_err=round(ymean / anchor - 1, 4),
            in_band=bool(
                abs(jan1 / anchor - 1) <= BAND and abs(ymean / anchor - 1) <= BAND
            ),
        )
    g_c = dict(
        years={str(k): v for k, v in g_c_years.items()},
        bar="2024 within ±35% of $1,281 AND 2025 within ±35% of $990 "
            "(both year-level readings)",
        ok=bool(all(v["in_band"] for v in g_c_years.values())),
    )

    # --- G-S24: 2024 shed feasibility on the committed sidecars
    armed_floor24 = armed_floor_hourly(2024)
    seeded_floor24 = seeded_floor_hourly(seeds[2024], armed_floor24)
    share24 = float((seeded_floor24 <= VOM_PLUS_100).mean())
    kill_hours = [KILL_DAY_2024 * 24 + h for h in FLOOR_WINDOW_HOD]
    kill = {
        int(h): dict(
            armed_floor=round(float(armed_floor24[h]), 1),
            seeded_floor=round(float(seeded_floor24[h]), 1),
            increase=round(float(seeded_floor24[h] - armed_floor24[h]), 1),
        )
        for h in kill_hours
    }
    no_increase = all(v["increase"] <= 0.0 for v in kill.values())
    g_s24 = dict(
        share_hours_floor_le_110=round(share24, 4),
        kill_hours=kill,
        bar=">=95% hours <= vom+$100 AND no floor increase at May-8-2024 "
            "h3065-3068 (h3066 = HE18 kill hour)",
        ok=bool(share24 >= 0.95 and no_increase),
    )

    # --- G-S25: 2025 self-extinction
    armed_floor25 = armed_floor_hourly(2025)
    seeded_floor25 = seeded_floor_hourly(seeds[2025], armed_floor25)
    share25 = float((seeded_floor25 <= VOM_PLUS_100).mean())
    g_s25 = dict(
        armed_floor_max=round(float(armed_floor25.max()), 1),
        seeded_floor_max=round(float(seeded_floor25.max()), 1),
        share_hours_floor_le_110=round(share25, 4),
        bar=">=95%",
        ok=bool(share25 >= 0.95),
    )

    gates = {
        "G-R": g_r,
        "G-WINTER": g_winter,
        "G-C": g_c,
        "G-S24": g_s24,
        "G-S25": g_s25,
        "LOYO": dict(
            declared="structurally N/A: zero new fitted scalars (pinned "
            "statistic + frozen ercot-221 constants); the per-year seed "
            "values ARE the out-of-year predictions and G-C is their test"
        ),
    }
    verdict = "PASS" if all(
        g.get("ok", True) for g in gates.values()
    ) else "FAIL"

    out = {
        "probe": "ercot222_crossyear_phase0",
        "date": "2026-08-19",
        "precommit": "docs/PRECOMMIT-ercot222-crossyear-seed-2026-08-19.md",
        "keeper_at_dispatch": "2026-08-19-ercot221-arm-adaptive (armed)",
        "conventions": dict(
            voll=VOLL,
            window_months=WINDOW_MONTHS,
            top_n=TOP_N,
            evening_hod_mapping_picked=pick,
            floor_window_hod=list(FLOOR_WINDOW_HOD),
            vom_plus_100=VOM_PLUS_100,
            band=BAND,
            seed_history="2020-01-01..2024-12-31 ONLY; 2019 in NO statistic; "
            "2025 measured prices never read (M-2 ->2025 as-scanned CITED)",
        ),
        "m2_fidelity": dict(
            note="as-scanned windows end June-1 of delivery year "
            "(RESEARCH-ercot221prep §2); ->2025 (1,660, +68% vs $990) cited "
            "not recomputed — computing it would read Jan-May-2025 prices",
            reproduction=fidelity,
        ),
        "seed_series": {
            str(yr): dict(
                jan1_usd=round(float(s[0]), 1),
                annual_mean_usd=round(float(s.mean()), 1),
                dec31_usd=round(float(s[-1]), 1),
                min_usd=round(float(s.min()), 1),
                max_usd=round(float(s.max()), 1),
            )
            for yr, s in seeds.items()
        },
        "gates": gates,
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
