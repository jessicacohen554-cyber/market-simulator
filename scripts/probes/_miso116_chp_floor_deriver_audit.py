"""miso-116 Phase-0 probe — audit the CHP steam floor's own deriver.

NO LP IS SOLVED. Every number is read from committed artifacts:

* the keeper bundle ``results/calibration/miso109_hy_level_B`` —
  ``hourly/class_hourly_<year>.parquet`` (P1 class dispatch, the model side),
  ``run_config.json`` (the keeper's exact ``ScenarioConfig``) and
  ``legitimacy_diagnostics.json`` (D-1 / D-2),
* ``data/raw/_processed-legacy/thermal_tranches_MISO.csv`` — the floor artifact
  (``chp_pmin_cf`` / ``chp_sector`` / ``steam_level_cf`` / ``status``),
* ``data/raw/_processed-legacy/parasitic_load_factors.parquet`` — the measured
  net/gross factors ``derive_thermal_tranches`` itself uses,
* ``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` — CAMPD hourly unit gross
  load, read through the repo's own ``states_for_iso`` / ``_hour_index_8760``,
* the repo's own ``chp.chp_btm_pct`` / ``chp.chp_pmin_cf`` / ``chp.chp_overrides``
  (rule 24 [R-REGISTRY]: no hand map, no re-derived constant).

The pre-registered question, estimators, bands and kills are in
``results/calibration/PREREG-miso116-chp-floor-deriver-2026-08-02.md``, written
and committed BEFORE this probe was run:

    A  Apportionment structure — is the floor per PRIME MOVER, or one pooled
       plant number applied across prime movers?
    B  Basis test — recompute miso-115's CC_CHP R on a basis-matched
       denominator (the DECISIVE estimator).
    C  Ceiling test — is the class floor-held or capacity-capped?
    D  Model-dependence — does any term read an LP price/dispatch/residual?

K3 forces the audit to reproduce miso-115's published R (2.156 / 2.246 / 2.555)
to within 0.005 before the correction is applied.

Run:  uv run python scripts/probes/_miso116_chp_floor_deriver_audit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.bench_multiclass import unit_family  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    CAMPD_UNIT_LEVEL_DIR,
    PROCESSED_DIR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.campd import (  # noqa: E402
    _hour_index_8760,
    pooled_factor_map,
    states_for_iso,
)
from market_sim.data.chp import (  # noqa: E402
    chp_btm_pct,
    chp_class_netgen_mwh,
    chp_overrides,
    chp_pmin_cf,
)
from market_sim.data.fleet.campd_bins import (  # noqa: E402
    measured_chp_heat_rates,
    thermal_tranche_chp_steam_level,
)
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

BUNDLE = ROOT / "results/calibration/miso109_hy_level_B"
ISO = "MISO"
YEARS = (2023, 2024, 2025)
TROUGH = (1, 2, 3)
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
# Model class -> CAMPD technology family. VERBATIM from miso-115's probe
# (``PAIRS``) so the corrected ratio is comparable to the ratio it corrects.
PAIRS = {"CC_CHP": "CC", "CT_CHP": "CT", "ST_CHP": "ST_GAS"}
# miso-115 §3, the figures this audit must reproduce before correcting (K3).
MISO115_R = {
    "CC_CHP": (2.156, 2.246, 2.555),
    "CT_CHP": (0.272, 0.356, 0.269),
    "ST_CHP": (0.000, 0.000, 0.000),
}
K3_TOL = 0.005
UNIT_COLS = [
    "stateCode",
    "facilityId",
    "unitId",
    "date",
    "hour",
    "opTime",
    "grossLoad",
    "heatInput",
    "unitType",
    "primaryFuelInfo",
]


def keeper_config(year: int) -> ScenarioConfig:
    """The keeper's exact ScenarioConfig, re-pointed at ``year``."""
    d = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    return ScenarioConfig(**d).with_overrides(weather_year=year)


def model_fleet(year: int) -> pd.DataFrame:
    """MISO's modelled fleet for ``year``, one row per plant-class.

    The heat-rate flags are read from the KEEPER's own ``ScenarioConfig``.
    ``load_fleet_from_csv`` defaults ``measured_chp_heat_rates`` to False, so a
    probe that omits it silently loads the pre-correction eGRID steam-credited
    rate while the keeper's LP ran on the measured power-only rate — a 6.76 vs
    8.77 MMBtu/MWh difference on MISO ``CC_CHP``. miso-115's probe omitted it,
    which is the origin of its §4 "CC_CHP priced 23 % too cheap" reading.
    """
    cfg = keeper_config(year)
    gens = load_fleet_from_csv(
        ISO,
        year=year,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        measured_ct_heat_rates=getattr(cfg, "measured_ct_heat_rates", False),
    )
    return pd.DataFrame(
        [
            {
                "plant_code": int(g.plant_code),
                "klass": str(g.plant_group),
                "pmax_mw": float(g.pmax_mw),
                "heat_rate": float(g.heat_rate),
            }
            for g in gens
            if g.plant_code is not None
        ]
    )


def model_trough_mw(year: int) -> dict[str, float]:
    """Keeper-bundle P1 generation at h1-h3, by class (MW, mean over hours)."""
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    wide = c.pivot_table(index="hour", columns="klass", values="mw")
    trough = wide[(wide.index % 24).isin(TROUGH)]
    return {k: float(trough[k].mean()) for k in wide.columns}


def campd_miso_units(year: int, plant_codes: set[int]) -> pd.DataFrame:
    """CAMPD hourly unit rows for MISO-fleet plants, on the model's calendar.

    Identical construction to miso-115's probe (K3 comparability).
    """
    frames = []
    for state in states_for_iso(ISO):
        path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=UNIT_COLS)
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(plant_codes)]
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["plant_code"] = out["facilityId"].astype(int)
    dt = pd.to_datetime(out["date"])
    out["hoy"] = _hour_index_8760(dt.dt.month, dt.dt.day, out["hour"])
    out = out[out["hoy"] >= 0]  # rule 8 [R-8760]: Feb 29 dropped
    out["family"] = [
        unit_family(t, f)
        for t, f in zip(out["unitType"], out["primaryFuelInfo"], strict=True)
    ]
    out["grossLoad"] = out["grossLoad"].fillna(0.0)
    out["opTime"] = out["opTime"].fillna(0.0)
    return out


def parasitic_map() -> dict[int, float]:
    """``{plant_id: net/gross}`` from the committed artifact (deriver's own)."""
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return pooled_factor_map(pd.read_parquet(path))


# --------------------------------------------------------------------------- #
# A. Apportionment structure
# --------------------------------------------------------------------------- #


def part_a(fleet: pd.DataFrame) -> None:
    """Is the floor per PRIME MOVER, or one pooled plant number?"""
    print("\n" + "=" * 78)
    print("A. APPORTIONMENT STRUCTURE — what does the floor identify?")
    print("=" * 78)

    art = pd.read_csv(PROCESSED_DIR / f"thermal_tranches_{ISO}.csv")
    chp_rows = art[art["plant_group"].isin(CHP_CLASSES)]

    print(f"\n  A3 floor provenance — artifact rows for {ISO} CHP groups")
    print(f"    artifact rows total {len(art)}, CHP rows {len(chp_rows)}")
    prov = chp_rows.groupby(["plant_group", "status"]).size()
    for (grp, status), n in prov.items():
        sub = chp_rows[
            (chp_rows["plant_group"] == grp) & (chp_rows["status"] == status)
        ]
        have = sub["chp_pmin_cf"].notna().sum() if "chp_pmin_cf" in sub else 0
        print(f"      {grp:<8s} status={status:<14s} n={n:3d}  with chp_pmin_cf={have}")

    # A1 key grain: the ARTIFACT is keyed (plant, class); the CONSUMER is not.
    print("\n  A1 key grain — artifact key vs consumer key")
    dup = chp_rows.groupby("plant_code").size()
    multi_art = dup[dup > 1]
    print(
        f"    artifact rows keyed (plant_code, plant_group): "
        f"{len(chp_rows)} rows over {chp_rows['plant_code'].nunique()} plants; "
        f"{len(multi_art)} plant(s) carry >1 CHP artifact row"
    )
    ov = chp_overrides(ISO)
    print(
        f"    chp_overrides() collapses to plant_code only -> {len(ov)} entries "
        "(one CF per PLANT, no class dimension)"
    )

    # Model plants carrying >= 2 CHP classes: every class gets the SAME CF.
    chp_fleet = fleet[fleet["klass"].isin(CHP_CLASSES)]
    per_plant = chp_fleet.groupby("plant_code")["klass"].nunique()
    multi = sorted(per_plant[per_plant > 1].index)
    multi_cap = float(chp_fleet[chp_fleet["plant_code"].isin(multi)]["pmax_mw"].sum())
    tot_cap = float(chp_fleet["pmax_mw"].sum())
    print(
        f"    model CHP plants with >=2 CHP classes: {len(multi)} "
        f"({multi_cap:,.0f} / {tot_cap:,.0f} MW = {multi_cap / tot_cap:.1%} of CHP cap)"
    )
    for code in multi:
        rows = chp_fleet[chp_fleet["plant_code"] == code]
        cf = chp_pmin_cf(code, iso=ISO)
        art_rows = chp_rows[chp_rows["plant_code"] == code]
        art_desc = ", ".join(
            f"{r.plant_group}:{r.chp_pmin_cf}({r.status})"
            for r in art_rows.itertuples(index=False)
        )
        print(
            f"      plant {code}: classes "
            + "/".join(f"{r.klass}({r.pmax_mw:,.0f}MW)" for r in rows.itertuples())
            + f"  -> ALL receive chp_pmin_cf={cf}  [artifact has: {art_desc or 'none'}]"
        )

    # A2 prime-mover resolution of the BTM share.
    print("\n  A2 BTM share — does it resolve by prime mover?")
    for klass in CHP_CLASSES:
        sub = chp_fleet[chp_fleet["klass"] == klass]
        if sub.empty:
            continue
        shares = np.array(
            [chp_btm_pct(int(c), klass, iso=ISO) for c in sub["plant_code"]]
        )
        caps = sub["pmax_mw"].to_numpy()
        wavg = float((shares * caps).sum() / caps.sum()) if caps.sum() else float("nan")
        vals = sorted(set(np.round(shares, 3)))
        print(
            f"    {klass:<8s} cap-weighted BTM {wavg:5.1f} %  "
            f"| distinct values {vals} over {len(sub)} plants"
        )
    # Same plant, different prime mover -> same share?
    if multi:
        print("    within-plant variation across prime movers:")
        for code in multi:
            rows = chp_fleet[chp_fleet["plant_code"] == code]
            vals = {
                str(r.klass): chp_btm_pct(int(code), str(r.klass), iso=ISO)
                for r in rows.itertuples()
            }
            same = len(set(vals.values())) == 1
            print(
                f"      plant {code}: {vals}  -> "
                f"{'IDENTICAL across prime movers' if same else 'varies'}"
            )

    # K1 BTM provenance: how much CC_CHP capacity lands on the unsourced default?
    print("\n  K1 BTM provenance — exposure to the unsourced merchant default")
    for klass in CHP_CLASSES:
        sub = chp_fleet[chp_fleet["klass"] == klass]
        if sub.empty:
            continue
        cap_by_sector: dict[str, float] = {}
        for r in sub.itertuples():
            _, sector, btm_ov = chp_overrides(ISO).get(
                int(r.plant_code), (None, None, None)
            )
            key = (
                "per-plant override"
                if btm_ov is not None
                else (sector or "NO SECTOR -> merchant default (unsourced 35.0)")
            )
            cap_by_sector[key] = cap_by_sector.get(key, 0.0) + float(r.pmax_mw)
        tot = sum(cap_by_sector.values())
        print(f"    {klass}:")
        for key, cap in sorted(cap_by_sector.items(), key=lambda kv: -kv[1]):
            print(f"      {key:<48s} {cap:8,.0f} MW ({cap / tot:5.1%})")


# --------------------------------------------------------------------------- #
# B. Basis test — the decisive estimator
# --------------------------------------------------------------------------- #


def part_b(
    fleets: dict[int, pd.DataFrame],
    campds: dict[int, pd.DataFrame],
    models: dict[int, dict[str, float]],
) -> dict[str, list[tuple[float, float, float]]]:
    """Recompute miso-115's R on a basis-matched denominator.

    Returns ``{klass: [(R_raw, R_btm_only, R_basis), ...]}`` per year.
    """
    print("\n" + "=" * 78)
    print("B. BASIS TEST — miso-115's R on a basis-matched denominator")
    print("=" * 78)
    print(
        "\n  miso-115 divided CAMPD grossLoad (WHOLE-PLANT output) by the model's\n"
        "  class_hourly.mw. For a CHP class the model's LP capacity is only the\n"
        "  GRID-FACING share: fleet/assembly.py builds grid_cap = nameplate x\n"
        "  (1 - btm), and the behind-the-meter host self-supply is never created\n"
        "  as a Generator (K4, verified in code). The basis-matched comparable is\n"
        "  therefore CAMPD gross x parasitic x (1 - btm)."
    )

    factors = parasitic_map()
    out: dict[str, list[tuple[float, float, float]]] = {k: [] for k in PAIRS}

    for year in YEARS:
        fleet, campd, model_mw = fleets[year], campds[year], models[year]
        chp_fleet = fleet[fleet["klass"].isin(CHP_CLASSES)]
        print("\n  " + "-" * 74)
        print(f"  YEAR {year}")
        print("  " + "-" * 74)

        for klass, fam in PAIRS.items():
            sub = chp_fleet[chp_fleet["klass"] == klass]
            plants = set(sub["plant_code"].unique())
            cap_model = float(sub["pmax_mw"].sum())

            u = campd[campd["plant_code"].isin(plants)]
            u_fam = u[u["family"] == fam]
            trough = u_fam[(u_fam["hoy"] % 24).isin(TROUGH)]
            n_hours = trough["hoy"].nunique()
            if not n_hours:
                out[klass].append((float("nan"),) * 3)
                continue

            mdl = model_mw.get(klass, float("nan"))

            # --- uncorrected (miso-115's own estimator), for K3 --------------
            meas_raw = float(trough["grossLoad"].sum()) / n_hours
            r_raw = meas_raw / mdl if mdl else float("nan")

            # --- per-plant basis correction ---------------------------------
            by_plant = trough.groupby("plant_code")["grossLoad"].sum() / n_hours
            covered_cap = float(
                sub[sub["plant_code"].isin(by_plant.index)]["pmax_mw"].sum()
            )
            meas_btm = 0.0
            meas_basis = 0.0
            missing_par_cap = 0.0
            for code, gross in by_plant.items():
                code = int(code)
                btm = chp_btm_pct(code, klass, iso=ISO) / 100.0
                par = factors.get(code)
                if par is None:
                    missing_par_cap += float(
                        sub[sub["plant_code"] == code]["pmax_mw"].sum()
                    )
                    par = 1.0
                meas_btm += float(gross) * (1.0 - btm)
                meas_basis += float(gross) * par * (1.0 - btm)

            r_btm = meas_btm / mdl if mdl else float("nan")
            r_basis = meas_basis / mdl if mdl else float("nan")
            out[klass].append((r_raw, r_btm, r_basis))

            k3 = MISO115_R[klass][YEARS.index(year)]
            ok = abs(r_raw - k3) <= K3_TOL
            print(f"\n    {klass:<8s} model {mdl:7,.0f} MW (grid-facing LP dispatch)")
            print(
                f"      CAMPD gross (miso-115 estimator)  {meas_raw:7,.0f} MW"
                f" -> R_raw   = {r_raw:.3f}   "
                f"[K3 vs published {k3:.3f}: {'REPRODUCED' if ok else 'MISMATCH'}]"
            )
            print(
                f"      x (1 - btm)         upper bound   {meas_btm:7,.0f} MW"
                f" -> R_btm   = {r_btm:.3f}"
            )
            print(
                f"      x parasitic x (1 - btm)  MATCHED  {meas_basis:7,.0f} MW"
                f" -> R_basis = {r_basis:.3f}"
            )
            print(
                f"      K2 parasitic coverage: {1 - missing_par_cap / cap_model:6.1%} "
                f"of model class capacity ({missing_par_cap:,.0f} MW unmapped, "
                f"factor=1.0); matched-plant cap {covered_cap:,.0f}/{cap_model:,.0f} MW"
            )

            # K1 split: the merchant 35.0 is an unsourced, residual-identified
            # constant. Re-read the correction on the sector-SOURCED plants only
            # (industrial / commercial, EIA-923 Schedule-8 cited), so the verdict
            # can be checked without it.
            if klass == "CC_CHP":
                sourced = {"industrial", "commercial"}
                num = {"sourced": 0.0, "merchant": 0.0}
                den = {"sourced": 0.0, "merchant": 0.0}
                for code, gross in by_plant.items():
                    code = int(code)
                    _, sector, btm_ov = chp_overrides(ISO).get(code, (None, None, None))
                    bucket = (
                        "sourced"
                        if (btm_ov is not None or (sector in sourced))
                        else "merchant"
                    )
                    btm = chp_btm_pct(code, klass, iso=ISO) / 100.0
                    par = factors.get(code, 1.0)
                    num[bucket] += float(gross) * par * (1.0 - btm)
                    # model-side split is unavailable at plant grain, so the
                    # denominator is apportioned by the plant's grid_cap share
                    cap = float(sub[sub["plant_code"] == code]["pmax_mw"].sum())
                    den[bucket] += cap * (1.0 - btm)
                tot_den = den["sourced"] + den["merchant"]
                for bucket in ("sourced", "merchant"):
                    share = den[bucket] / tot_den if tot_den else float("nan")
                    mdl_b = mdl * share
                    r_b = num[bucket] / mdl_b if mdl_b else float("nan")
                    print(
                        f"      K1 split [{bucket:<8s}] grid_cap share {share:5.1%} "
                        f"-> R_basis = {r_b:.3f}"
                    )
    return out


# --------------------------------------------------------------------------- #
# C. Ceiling test
# --------------------------------------------------------------------------- #


def part_c(
    fleets: dict[int, pd.DataFrame], models: dict[int, dict[str, float]]
) -> None:
    """Is the class floor-held, or capacity-capped?"""
    print("\n" + "=" * 78)
    print("C. CEILING TEST — floor-held or capacity-capped?")
    print("=" * 78)
    print(
        "\n  A min_gen floor is a LOWER bound: it cannot hold a class DOWN. If a\n"
        "  too-cheap class still under-runs, the binding constraint is an UPPER\n"
        "  bound. For CHP that ceiling is grid_cap = nameplate x (1 - btm)."
    )

    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    d2 = {
        (r["year"], r["class"]): r
        for r in diag["diagnostics"]["D2"]["rows"]
        if r["mechanism"] == "chp_steam"
    }
    d1 = {(r["year"], r["class"]): r for r in diag["diagnostics"]["D1"]["rows"]}

    for year in YEARS:
        fleet, model_mw = fleets[year], models[year]
        chp_fleet = fleet[fleet["klass"].isin(CHP_CLASSES)]
        print(f"\n  YEAR {year}")
        for klass in CHP_CLASSES:
            sub = chp_fleet[chp_fleet["klass"] == klass]
            if sub.empty:
                continue
            nameplate = float(sub["pmax_mw"].sum())
            grid_cap = float(
                sum(
                    float(r.pmax_mw)
                    * (1.0 - chp_btm_pct(int(r.plant_code), klass, iso=ISO) / 100.0)
                    for r in sub.itertuples()
                )
            )
            floor_mw = 0.0
            for r in sub.itertuples():
                code = int(r.plant_code)
                cf = chp_pmin_cf(code, iso=ISO)
                if cf is None:
                    continue
                btm = chp_btm_pct(code, klass, iso=ISO)
                floor_mw += (
                    max(0.0, cf * (1.0 - btm / 100.0)) / 100.0 * float(r.pmax_mw)
                )
            mdl = model_mw.get(klass, float("nan"))
            util_np = mdl / nameplate if nameplate else float("nan")
            util_gc = mdl / grid_cap if grid_cap else float("nan")
            fshare = floor_mw / mdl if mdl else float("nan")
            row1 = d1.get((year, klass), {})
            row2 = d2.get((year, klass), {})
            print(
                f"    {klass:<8s} trough {mdl:7,.0f} MW | nameplate {nameplate:8,.0f} "
                f"| grid_cap(analytic) {grid_cap:8,.0f}"
            )
            print(
                f"      util vs nameplate {util_np:6.1%} | "
                f"util vs grid_cap {util_gc:6.1%} | "
                f"analytic floor {floor_mw:7,.0f} MW = {fshare:6.1%} of trough MW"
            )
            print(
                f"      D-1 profile_r {row1.get('profile_r')} "
                f"cv_ratio {row1.get('cv_ratio')} | "
                f"D-2 chp_steam forced share {row2.get('share_of_class')} "
                "(MECH_CHP_STEAM is in D2_EXEMPT_MECHS — K5)"
            )


# --------------------------------------------------------------------------- #
# D. Model-dependence audit
# --------------------------------------------------------------------------- #


def part_d(fleets: dict[int, pd.DataFrame]) -> None:
    """Classify every term in the floor chain: measured / model-dependent."""
    print("\n" + "=" * 78)
    print("D. MODEL-DEPENDENCE — does any term read an LP price/dispatch/residual?")
    print("=" * 78)

    terms = [
        (
            "chp_pmin_cf (status=ok)",
            "derive_thermal_tranches.py:717 — p2 of CAMPD available-CF, outage-derated",
            "MEASURED (CEMS + measured outage overlay)",
        ),
        (
            "chp_pmin_cf (status=eia923_cf)",
            "derive_thermal_tranches.py:_chp_f923_floor_cf — EIA-923 class CF",
            "MEASURED (EIA-923)",
        ),
        (
            "parasitic factor",
            "campd.compute_parasitic_factors — EIA-923 net / CAMPD gross",
            "MEASURED",
        ),
        (
            "chp_sector",
            "EIA-860 Plant.Sector (or EIA-923 Page 1), 100% agreement on 232 plants",
            "MEASURED",
        ),
        (
            "CHP_BTM_PCT_BY_SECTOR['industrial'/'commercial']",
            "constants.py:405-406 — EIA-923 Schedule 8 useful-thermal share",
            "MEASURED (cited)",
        ),
        (
            "CHP_BTM_PCT_BY_SECTOR['merchant'] = 35.0",
            "constants.py:404 — 'residual-identified, forecast-risk — no "
            "independent source yet'",
            "*** UNSOURCED CONSTANT, residual-identified ***",
        ),
        (
            "steam_level_cf (chp_steam_floor_p25, OFF in keeper)",
            "derive_thermal_tranches.py:727 — on-freq x p50 loading-when-on",
            "MEASURED",
        ),
        (
            "chp_class_netgen_mwh (chp_export_floor_measured, OFF in keeper)",
            "chp.py:329 — same-year EIA-923 per-(plant,class) net generation",
            "MEASURED (backcast overlay; same-year 923 CF)",
        ),
        (
            "measured_chp_heat_rates (ON in keeper)",
            "eGRID (PLHTIAN + CHPCHTI) / PLNGENAN",
            "MEASURED",
        ),
    ]
    print()
    for name, source, verdict in terms:
        print(f"  {name}")
        print(f"      source : {source}")
        print(f"      verdict: {verdict}")

    print(
        "\n  No term in the chain reads an LP price, an LP dispatch or a scored\n"
        "  residual: the floor chain is a pure function of committed measured\n"
        "  inputs. The single non-measured term is the merchant BTM default."
    )

    # Q4: is the CC_CHP heat rate on the measured artifact?
    print("\n  Q4 — CC_CHP heat rate provenance (keeper arms measured_chp_heat_rates)")
    rates = measured_chp_heat_rates(ISO)
    fleet = fleets[YEARS[0]]
    for klass in CHP_CLASSES:
        sub = fleet[fleet["klass"] == klass]
        if sub.empty:
            continue
        on = np.array([(int(c), klass) in rates for c in sub["plant_code"]])
        cap = float(sub["pmax_mw"].sum())
        hr = sub["heat_rate"].to_numpy()
        w = sub["pmax_mw"].to_numpy()

        def _wavg(mask: np.ndarray) -> float:
            ww = w[mask]
            return float((hr[mask] * ww).sum() / ww.sum()) if ww.sum() else float("nan")

        print(
            f"    {klass:<8s} measured-HR coverage {float(w[on].sum()) / cap:6.1%} "
            f"of capacity | cap-weighted AS-KEEPER HR "
            f"{float((hr * w).sum() / w.sum()):.2f} MMBtu/MWh"
        )
        print(
            f"      repriced to measured  {_wavg(on):.2f}   |   "
            f"left on eGRID steam-credited rate {_wavg(~on):.2f}"
        )
    # Steam-level artifact (what an armed chp_steam_floor_p25 would give).
    lv = thermal_tranche_chp_steam_level(ISO)
    print(
        f"    steam_level_cf artifact covers {len(lv)} (plant, class) pairs; "
        "chp_steam_floor_p25 is OFF in the keeper"
    )
    # Same-year 923 CF (what an armed chp_export_floor_measured would give).
    for year in YEARS:
        ng = chp_class_netgen_mwh(year)
        n = sum(1 for k in ng if k[1] in CHP_CLASSES)
        print(
            f"    chp_class_netgen_mwh({year}) covers {n} CHP (plant, class) pairs "
            "(chp_export_floor_measured is OFF in the keeper)"
        )


# --------------------------------------------------------------------------- #


def part_e(fleets: dict[int, pd.DataFrame], campds: dict[int, pd.DataFrame]) -> None:
    """Q4 plant-matched: model CC_CHP heat rate vs CAMPD-measured, per plant.

    miso-115 §4 compared a model rate of 6.76 against a class-average CAMPD
    GROSS rate of 8.83 and read the class as "priced 23 % too cheap". 6.76 is
    the fleet loaded with ``measured_chp_heat_rates`` DEFAULTED OFF; the keeper
    arms it, and the as-keeper rate is 8.77. This re-takes the comparison plant
    by plant, on the full year (no trough selection) and on the keeper's own
    flags, so the residual disagreement is localised rather than averaged.
    """
    print("\n" + "=" * 78)
    print("E. Q4 PLANT-MATCHED — CC_CHP heat rate, model vs CAMPD measured")
    print("=" * 78)

    klass, fam = "CC_CHP", "CC"
    rates = measured_chp_heat_rates(ISO)
    for year in YEARS:
        fleet, campd = fleets[year], campds[year]
        sub = fleet[fleet["klass"] == klass]
        plants = set(sub["plant_code"].unique())
        u = campd[campd["plant_code"].isin(plants) & (campd["family"] == fam)]
        if u.empty:
            continue
        agg = u.groupby("plant_code")[["heatInput", "grossLoad"]].sum()
        agg = agg[agg["grossLoad"] > 0]
        agg["campd_gross_hr"] = agg["heatInput"] / agg["grossLoad"]

        rows = []
        for code, r in agg.iterrows():
            code = int(code)
            s = sub[sub["plant_code"] == code]
            if s.empty:
                continue
            cap = float(s["pmax_mw"].sum())
            mdl_hr = float((s["heat_rate"] * s["pmax_mw"]).sum() / cap)
            rows.append(
                {
                    "plant": code,
                    "cap": cap,
                    "model_hr": mdl_hr,
                    "campd_hr": float(r["campd_gross_hr"]),
                    "on_artifact": (code, klass) in rates,
                }
            )
        d = pd.DataFrame(rows)
        if d.empty:
            continue
        d["ratio"] = d["model_hr"] / d["campd_hr"]
        w = d["cap"].to_numpy()
        print(
            f"\n  {year}: {len(d)} matched CC_CHP plants, {w.sum():,.0f} MW\n"
            f"    cap-weighted model HR {float((d['model_hr'] * w).sum() / w.sum()):.2f}"
            f" | CAMPD gross HR {float((d['campd_hr'] * w).sum() / w.sum()):.2f}"
            f" | cap-weighted ratio {float((d['ratio'] * w).sum() / w.sum()):.3f}"
        )
        below = d[d["ratio"] < 0.85]
        print(
            f"    plants where model < 0.85 x CAMPD: {len(below)}/{len(d)} "
            f"({float(below['cap'].sum()) / w.sum():.1%} of matched capacity); "
            f"on measured artifact: {int(below['on_artifact'].sum())}/{len(below)}"
        )
        if year == YEARS[0]:
            top = below.sort_values("cap", ascending=False).head(8)
            for r in top.itertuples(index=False):
                print(
                    f"      plant {r.plant:<6d} {r.cap:6,.0f} MW  model "
                    f"{r.model_hr:5.2f}  CAMPD gross {r.campd_hr:5.2f}  "
                    f"ratio {r.ratio:.3f}  artifact={r.on_artifact}"
                )
    print(
        "\n  Basis note: CAMPD's rate is total heat input over GROSS load; the\n"
        "  model's eGRID-derived rate is (PLHTIAN + CHPCHTI) over NET generation.\n"
        "  A NET denominator is the smaller one, so the as-keeper rate sitting\n"
        "  just ABOVE the CAMPD gross rate is the expected ordering — which is\n"
        "  what the flag-on comparison shows and the flag-off one inverted."
    )


def verdict(ratios: dict[str, list[tuple[float, float, float]]]) -> None:
    """Apply the pre-registered decision rule."""
    print("\n" + "=" * 78)
    print("VERDICT — pre-registered decision rule")
    print("=" * 78)
    for klass in PAIRS:
        rr = ratios[klass]
        print(f"  {klass:<8s} R_raw   = " + " / ".join(f"{r[0]:.3f}" for r in rr))
        print("           R_basis = " + " / ".join(f"{r[2]:.3f}" for r in rr))

    rb = np.array([r[2] for r in ratios["CC_CHP"]])
    print(
        "\n  Scope: CC_CHP is the only kill-clean class (miso-115 K1: CT_CHP "
        "10.4 %, ST_CHP 26.9 % coverage -> VOID, not quoted)."
    )
    if np.sum((rb >= 0.80) & (rb <= 1.25)) >= 2:
        v = (
            "BASIS-ARTIFACT -> miso-115's CC_CHP deficit is a reporting-basis "
            "mismatch. REFUSE, no solve; correct the record."
        )
    elif np.sum(rb >= 1.40) >= 2:
        v = "REAL DEFICIT SURVIVES -> read A1/A2 to choose MIS-APPORTIONED vs CORRECT-AND-ELSEWHERE"
    else:
        v = "INCONCLUSIVE -> defaults to refuse; no charter"
    print(f"\n  Pre-registered verdict: {v}")


def main() -> None:
    print("=" * 78)
    print("miso-116 Phase 0 — CHP steam-floor deriver audit (NO LP)")
    print("=" * 78)
    cfg = keeper_config(YEARS[0])
    print(
        f"\n  keeper {BUNDLE.name}: chp_steam_following={cfg.chp_steam_following}, "
        f"chp_export_floor_measured={cfg.chp_export_floor_measured}, "
        f"chp_steam_floor_p25={cfg.chp_steam_floor_p25}, "
        f"measured_chp_heat_rates={cfg.measured_chp_heat_rates}"
    )

    fleets, campds, models = {}, {}, {}
    for year in YEARS:
        fleets[year] = model_fleet(year)
        models[year] = model_trough_mw(year)
        campds[year] = campd_miso_units(year, set(fleets[year]["plant_code"].unique()))
        print(
            f"  {year}: fleet {fleets[year]['plant_code'].nunique()} plants, "
            f"CAMPD rows {len(campds[year]):,}"
        )

    part_a(fleets[YEARS[0]])
    ratios = part_b(fleets, campds, models)
    part_c(fleets, models)
    part_d(fleets)
    part_e(fleets, campds)
    verdict(ratios)


if __name__ == "__main__":
    main()
