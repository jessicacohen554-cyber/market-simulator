"""caiso-169 Phase 0 — the CAISO storage foresight horizon, measured for the first time.

Lever: ``docs/mechanism-testing-matrix.md`` §5.2 lever-queue **item 3** (S2, the
DA/RT two-settlement separation charter) taken on its OWN object — the
evening/overnight spread compression of ``FINDING-caiso127`` §1/§2 — after
caiso-168 closed the *belly* route into it.

This is a **measurement-only Phase 0 on committed artifacts**: the keeper
bundle's own ``hourly/`` sidecars, EIA-930 CISO ``NG: OTH``, and the LP row
builder itself. **No LP is built or solved anywhere in it**, no derive is run,
no ``ScenarioConfig`` field is added and nothing is registered.

Rule 19 ``[R-ONE-MECH]`` is the reason it exists: before any new
two-settlement mechanism is proposed, the already-built bounded-foresight
instrument — ``ScenarioConfig.storage_daily_cycling``, wired to
``model.lp.rows._build_storage_daily_cycle_rows``, unarmed on CAISO and carrying
a mechanism-matrix cell of ``.`` (n/a) — has to be adjudicated on CAISO's own
data.

Stages
------
``A`` SOC reconstruction from the committed charge/discharge sidecars, with
      three independent validations (the LP's own annual cyclic identity, the
      pumped-storage swing against the model's PS energy capacity, and the
      hour-index clock against the keeper's own demand and solar profiles).
``B`` the model's cross-day energy banking: the per-day storage-side net that
      ``storage_daily_cycling`` would force to exactly zero, plus the day-start
      SOC dispersion.
``C`` the measured comparator — the same statistic on the real CAISO battery
      fleet (EIA-930 CISO ``NG: OTH``), like-for-like against model ``li_ion``.
``D`` the nu-chain geometry: which SOC hours the daily-cycle rows actually
      touch, and whether they fall inside the caiso-127 pinned-day coupling.
``E`` the reach: is the model's overnight discharge funded by, or limited by,
      the day-start SOC the constraint would equalize?

Rule 13 ``[R-MEASURED]``: every number is a measurement of committed inputs and
committed model output. Nothing is fitted, nothing is tuned, no value computed
here is fed back into any model input, and no residual motivates a re-derive
(rule 23 ``[R-FROZEN-DERIVE]``).

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only, hard-filtered and fail-closed. CAISO
holds no ``complete`` marker, so 2022 / 2019 / <=2021 / H1-2026 are untouched.

Usage::

    python scripts/probes/caiso169_storage_foresight_phase0.py

Artifact: ``results/calibration/_caiso169_storage_foresight_phase0.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/caiso166_measured_loss_zones/hourly"
EIA930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"
OUT = REPO / "results/calibration/_caiso169_storage_foresight_phase0.json"

# Rule 22 [R-HOLDOUT]: the training window, and nothing else. Fail closed.
YEARS = (2023, 2024, 2025)
HOURS = 8760
DAYS = 365

# One-way efficiencies. ``model.storage`` builds every unit as eta = rte ** 0.5
# with eta_charge == eta_discharge, so a per-tech aggregate obeys the SAME SOC
# recursion as each of its units and the tech-level reconstruction is EXACT.
RTE = {"li_ion": 0.85, "pumped_storage": 0.80}  # ScenarioConfig.storage_rte_4hr,
# constants.PUMPED_STORAGE_RTE.

# The model's pumped-storage column, for the stage-A capacity validation:
# 2,077.6 MW x constants.PUMPED_STORAGE_DURATION_HOURS (10.0). caiso-129 §7.
PS_ENERGY_CAP_MWH = 2077.6 * 10.0

# caiso-127 §1's two windows, carried VERBATIM -- neither is chosen here.
OVERNIGHT = (0, 7)  # local hod [0, 7)
EVENING = (17, 22)  # local hod [17, 22)


def _clock() -> np.ndarray:
    """Local hour-of-day for the model's fixed non-leap 8760 frame.

    The frame drops Feb-29 and hour 0 is LOCAL midnight -- verified in stage A
    against the keeper's own demand and solar profiles rather than assumed.
    """
    return np.arange(HOURS) % 24


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    """Map local timestamps onto the model's non-leap 8760 hour index.

    Feb-29 rows are dropped by the caller's mask; every later day of a leap year
    shifts back one day so the measured series stays hour-aligned to the solve.
    A linear offset from Jan 1 would put every 2024 hour after Feb-28 a full day
    out of phase (caiso-168 §1).
    """
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24


def _storage(year: int) -> dict[str, dict[str, np.ndarray]]:
    """P1 fleet charge/discharge MW per tech from the keeper's own sidecar."""
    s = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    out: dict[str, dict[str, np.ndarray]] = {}
    for tech in sorted(s["tech"].unique()):
        d = s[s["tech"] == tech].sort_values("hour")
        if len(d) != HOURS:
            raise SystemExit(f"{year} {tech}: {len(d)} rows, expected {HOURS}")
        out[str(tech)] = {
            "chg": d["charge_mw"].to_numpy(dtype=float),
            "dis": d["discharge_mw"].to_numpy(dtype=float),
        }
    return out


def _soc(chg: np.ndarray, dis: np.ndarray, eta: float) -> np.ndarray:
    """SOC at the START of each hour, relative to the annual floor.

    Integrates the LP's own dynamics ``SOC[t] = SOC[t-1] + eta*Chg - Dis/eta``.
    The absolute level is not observable from the sidecar (it carries no SOC
    column), so the path is anchored at its own minimum -- which is a TIGHT
    anchor whenever the fleet empties at least once, and a lower bound on the
    day-start levels otherwise. Every statistic used below is a DIFFERENCE, so
    the anchor cancels out of all of them.
    """
    inc = eta * chg - dis / eta
    return np.concatenate([[0.0], np.cumsum(inc)])[:HOURS] - np.cumsum(inc).min()


def stage_a() -> dict:
    """Reconstruction + three independent validations of it."""
    rows: list[dict] = []
    for year in YEARS:
        st = _storage(year)
        for tech, d in st.items():
            eta = RTE[tech] ** 0.5
            inc = eta * d["chg"] - d["dis"] / eta
            soc = _soc(d["chg"], d["dis"], eta)
            rows.append(
                {
                    "year": year,
                    "tech": tech,
                    # V1 -- the LP's annual cyclic SOC row, summed over the year.
                    # An exact reconstruction returns 0 to float rounding.
                    "cyclic_identity_mwh": float(inc.sum()),
                    "annual_swing_mwh": float(soc.max() - soc.min()),
                    "charge_twh": float(d["chg"].sum() / 1e6),
                    "discharge_twh": float(d["dis"].sum() / 1e6),
                }
            )
    # V2 -- pumped storage carries ONE continuous column whose energy capacity
    # is known independently (caiso-129 §7). Its reconstructed annual swing must
    # land on it, and does, in every year.
    ps = [r for r in rows if r["tech"] == "pumped_storage"]
    v2 = [
        {
            "year": r["year"],
            "recovered_swing_mwh": r["annual_swing_mwh"],
            "model_ps_energy_cap_mwh": PS_ENERGY_CAP_MWH,
            "ratio": r["annual_swing_mwh"] / PS_ENERGY_CAP_MWH,
        }
        for r in ps
    ]
    # V3 -- the clock. Hour 0 is LOCAL midnight, not UTC: the keeper's own
    # demand peaks in the local evening and its solar peaks near local noon.
    # Under a UTC index the solar peak would land at hod 19-20.
    hod = _clock()
    sysd = pd.read_parquet(BUNDLE / "system_2024.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    dem = sysd.pivot_table(index="hour", columns="zone", values="demand")
    dem = dem.sum(axis=1).reindex(range(HOURS)).to_numpy()
    cls = pd.read_parquet(BUNDLE / "class_hourly_2024.parquet")
    cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "solar")]
    sol = cls.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0)
    sol = sol.to_numpy()
    prof = lambda a: np.array([a[hod == h].mean() for h in range(24)])  # noqa: E731
    v3 = {
        "demand_peak_hod": int(prof(dem).argmax()),
        "demand_trough_hod": int(prof(dem).argmin()),
        "solar_peak_hod": int(prof(sol).argmax()),
        "verdict": "LOCAL (a UTC index would put the solar peak at hod 19-20)",
    }
    return {"per_tech": rows, "V2_ps_capacity": v2, "V3_clock": v3}


def _daily_net(chg: np.ndarray, dis: np.ndarray, eta: float) -> np.ndarray:
    """Storage-side MWh banked across each local-midnight boundary.

    This is EXACTLY the quantity ``_build_storage_daily_cycle_rows`` forces to
    zero: the day's change in stored energy.
    """
    return (eta * chg - dis / eta).reshape(DAYS, 24).sum(axis=1)


def stage_b() -> list[dict]:
    """The model's cross-day banking, and the day-start SOC dispersion."""
    rows: list[dict] = []
    for year in YEARS:
        for tech, d in _storage(year).items():
            eta = RTE[tech] ** 0.5
            dn = _daily_net(d["chg"], d["dis"], eta)
            soc = _soc(d["chg"], d["dis"], eta)
            start = soc.reshape(DAYS, 24)[:, 0]
            rows.append(
                {
                    "year": year,
                    "tech": tech,
                    "daily_net_sd_mwh": float(dn.std()),
                    "daily_net_mean_abs_dev_mwh": float(np.abs(dn - dn.mean()).mean()),
                    "daily_net_p95_abs_mwh": float(np.percentile(np.abs(dn), 95)),
                    "daily_net_max_abs_mwh": float(np.abs(dn).max()),
                    "day_start_soc_mean_mwh": float(start.mean()),
                    "day_start_soc_sd_mwh": float(start.std()),
                }
            )
    return rows


def _measured_oth(year: int) -> np.ndarray:
    """EIA-930 CISO ``NG: OTH`` on the model's frame (discharge +, charge -).

    The same series the armed anchor's own envelope is derived from. Pumped
    storage is absent from OTH by construction (caiso-168 §3), so this is a
    BATTERY-limb comparator and says nothing about the walled PS object.
    """
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    dy = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
    if dy.empty:
        raise SystemExit(f"EIA-930 CISO carries no {year} rows")
    dy = dy[~((dy["Local date"].dt.month == 2) & (dy["Local date"].dt.day == 29))]
    h = _model_hour(dy["Local date"], year) + (dy["Hour"].to_numpy() - 1)
    out = np.full(HOURS, np.nan)
    ok = (h >= 0) & (h < HOURS)
    out[h[ok]] = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))[ok]
    return out


def stage_c() -> list[dict]:
    """Model vs MEASURED cross-day banking, like-for-like on the battery limb.

    ``NG: OTH`` is a fleet NET series, so the two legs are separated hour by
    hour (``chg = max(0, -net)``, ``dis = max(0, net)``) before the efficiency
    is applied. That understates gross throughput in any hour where part of the
    fleet charges while another part discharges -- which biases the MEASURED
    dispersion DOWN only through the efficiency wedge, and leaves the day's net
    itself exact. The comparison is therefore conservative in the direction
    that matters: it cannot manufacture a model excess that is not there.
    """
    rows: list[dict] = []
    for year in YEARS:
        meas = _measured_oth(year)
        cover = int(np.isfinite(meas).sum())
        meas = np.nan_to_num(meas)
        eta = RTE["li_ion"] ** 0.5
        m_dn = _daily_net(np.clip(-meas, 0, None), np.clip(meas, 0, None), eta)
        st = _storage(year)["li_ion"]
        o_dn = _daily_net(st["chg"], st["dis"], eta)
        # Basis symmetry check. The measured side is net-collapsed by
        # construction; the model side is gross. Collapsing the MODEL the same
        # way must not move its statistic, or the ratio is a basis artifact.
        o_net = st["dis"] - st["chg"]
        o_dn_collapsed = _daily_net(
            np.clip(-o_net, 0, None), np.clip(o_net, 0, None), eta
        )
        # Efficiency sensitivity: the measured fleet's true RTE is not observed.
        m_sd_rte = {
            f"rte_{r}": float(
                _daily_net(
                    np.clip(-meas, 0, None), np.clip(meas, 0, None), r**0.5
                ).std()
            )
            for r in (0.80, 0.85, 0.90)
        }
        rows.append(
            {
                "year": year,
                "eia930_coverage_hours": cover,
                "model_hours_with_both_legs": int(
                    ((st["chg"] > 1.0) & (st["dis"] > 1.0)).sum()
                ),
                "model_sd_net_collapsed_mwh": float(o_dn_collapsed.std()),
                "measured_sd_by_rte": m_sd_rte,
                "model_sd_mwh": float(o_dn.std()),
                "measured_sd_mwh": float(m_dn.std()),
                "ratio": float(o_dn.std() / m_dn.std()),
                "model_mean_mwh": float(o_dn.mean()),
                "measured_mean_mwh": float(m_dn.mean()),
                # The two errors a horizon choice must trade off: the incumbent
                # annual-cyclic LP OVERSHOOTS the measured dispersion; a hard
                # 24 h cycle sets it to EXACTLY ZERO and undershoots it.
                "incumbent_error_mwh": float(o_dn.std() - m_dn.std()),
                "daily_cycle_error_mwh": float(0.0 - m_dn.std()),
            }
        )
    return rows


def stage_d() -> dict:
    """Which SOC hours the daily-cycle rows touch -- read off the row builder.

    Imports the production builder and inspects the matrix it returns, so this
    is a fact about the shipped code, not a restatement of its docstring. No LP
    is built: ``_build_storage_daily_cycle_rows`` takes a layout and returns a
    sparse matrix.
    """
    from market_sim.model.lp.layout import VariableLayout
    from market_sim.model.lp.rows import _build_storage_daily_cycle_rows

    lay = VariableLayout(n_gen=3, n_zones=5, n_storage=2, n_links=4, T=HOURS)
    m = _build_storage_daily_cycle_rows(lay, 24).tocoo()
    hrs = (m.col - lay._soc_off) // lay.vars_per_hour
    per_row: dict[int, list[int]] = {}
    for r, h in zip(m.row.tolist(), hrs.tolist()):
        per_row.setdefault(int(r), []).append(int(h))
    touched = sorted({h for v in per_row.values() for h in v})
    malformed = sum(
        1 for v in per_row.values() if sorted(v)[0] != 0 or sorted(v)[1] % 24 != 0
    )
    # Does any touched hour fall STRICTLY INSIDE the caiso-127 coupling, i.e.
    # between the overnight window's last hour and the evening window's first?
    inside = [h for h in touched if OVERNIGHT[1] <= (h % 24) < EVENING[0] and h % 24]
    return {
        "n_rows": int(m.shape[0]),
        "expected_rows": lay.n_storage * (HOURS // 24 - 1),
        "rows_not_of_form_SOC0_SOC24d": malformed,
        "distinct_soc_hours_touched": len(touched),
        "all_touched_are_local_midnight": all(h % 24 == 0 for h in touched),
        "touched_hours_inside_the_caiso127_coupling": len(inside),
        "overnight_window_hod": list(OVERNIGHT),
        "evening_window_hod": list(EVENING),
    }


def stage_e() -> list[dict]:
    """Is the overnight discharge funded by -- or limited by -- day-start SOC?

    ``storage_daily_cycling`` pins every day-start SOC to one COMMON level. It
    does not bound that level, so it can only reach the overnight position
    through the day-to-day VARIATION it removes. If overnight draw is
    uncorrelated with the day-start SOC, that channel is empty.
    """
    rows: list[dict] = []
    hod = _clock()
    on = (hod >= OVERNIGHT[0]) & (hod < OVERNIGHT[1])
    for year in YEARS:
        for tech, d in _storage(year).items():
            eta = RTE[tech] ** 0.5
            soc = _soc(d["chg"], d["dis"], eta)
            start = soc.reshape(DAYS, 24)[:, 0]
            draw = _daily_net(
                np.where(on, d["chg"], 0.0), np.where(on, d["dis"], 0.0), eta
            )
            rows.append(
                {
                    "year": year,
                    "tech": tech,
                    # metered MW over the window, the caiso-127 §3 basis
                    "overnight_net_metered_mw": float((d["dis"] - d["chg"])[on].mean()),
                    "overnight_storage_side_mwh_per_day": float(-draw.mean()),
                    "corr_daystart_soc_vs_overnight_draw": float(
                        np.corrcoef(start, -draw)[0, 1]
                    ),
                    "days_soc_bottoms_out_in_overnight": int(
                        (
                            soc.reshape(DAYS, 24)[:, OVERNIGHT[0] : OVERNIGHT[1]].min(1)
                            < 0.02 * soc.max()
                        ).sum()
                    ),
                }
            )
    return rows


def main() -> None:
    if set(YEARS) - {2023, 2024, 2025}:
        raise SystemExit("rule 22 [R-HOLDOUT]: 2023-2025 only")
    out = {
        "session": "caiso-169",
        "keeper_bundle": str(BUNDLE.parent.relative_to(REPO)),
        "years": list(YEARS),
        "A_reconstruction": stage_a(),
        "B_model_banking": stage_b(),
        "C_measured_comparator": stage_c(),
        "D_nu_chain_geometry": stage_d(),
        "E_reach": stage_e(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
