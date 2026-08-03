"""miso-118 Phase-0 probe — the four ``CC_CHP`` plant-level heat-rate outliers.

NO LP IS SOLVED. Every number is read from committed artifacts:

* the CURRENT keeper bundle ``results/calibration/miso117_ctheatrate_B`` —
  ``run_config.json`` (the keeper's exact ``ScenarioConfig``, so the fleet this
  probe loads is the fleet the keeper solved: the miso-116 §7 discipline),
* ``data/raw/_processed-legacy/chp_power_only_heat_rates_MISO.csv`` — the
  measured power-only artifact ``measured_chp_heat_rates`` applies,
* ``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` — CAMPD hourly unit gross
  load and heat input, read through the repo's own ``states_for_iso`` /
  ``_hour_index_8760`` / ``unit_family``,
* EIA-923 monthly generation via ``market_sim.data.eia923.load_monthly_generation``
  (rule 24 [R-REGISTRY]: no hand map, no re-derived constant).

The pre-registered question, hypotheses, decomposition identity, decision rule,
kills and predictions are in
``results/calibration/PREREG-miso118-cchp-plant-outliers-2026-08-03.md``,
written, committed AND PUSHED before this probe was run:

    A  K1 reproduction — reproduce miso-116 part E on miso-116's own basis
       BEFORE any correction (14 plants / 5,852 MW / the four codes / the four
       2023 ratios to +-0.005).
    B  Decomposition — ratio = A_cems x F_family x G_gross, exactly.
    C  Basis-matched comparator — R_basis = model_hr / (CEMS heat / net923),
       two independent meters, neither of them the eGRID number the model loads.
    D  H-C vintage staleness; E  H-D mis-key; F  H-E mixed facility.
    G  Verdict under the pre-registered per-plant decision rule.

Run:  uv run python scripts/probes/_miso118_cchp_plant_outlier_basis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.bench_multiclass import unit_family  # noqa: E402
from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.campd import _hour_index_8760, states_for_iso  # noqa: E402
from market_sim.data.fleet.campd_bins import measured_chp_heat_rates  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

BUNDLE = ROOT / "results/calibration/miso117_ctheatrate_B"
ISO = "MISO"
YEARS = (2023, 2024, 2025)
KLASS = "CC_CHP"
FAM = "CC"

#: The four plants miso-116 §3 left open, and its published 2023 figures. K1
#: forces a byte-level reproduction of these before any correction is allowed.
TARGETS = (10745, 55089, 55259, 55088)
MISO116_E = {
    # plant: (cap MW, model_hr, campd_gross_hr, ratio)
    10745: (1479.0, 8.82, 10.90, 0.810),
    55089: (739.0, 8.01, 12.27, 0.653),
    55259: (513.0, 9.39, 11.70, 0.802),
    55088: (350.0, 8.35, 10.22, 0.817),
}
K1_TOL_RATIO = 0.005
K1_N_MATCHED = 14
K1_MATCHED_MW = 5852.0
K1_BELOW_SHARE = 0.527

#: Pre-registered decision bands (PREREG section 5).
BASIS_BAND = (0.90, 1.10)
REAL_BAND = (0.85, 1.15)
#: Pre-registered kill bands (PREREG section 6).
K3_NET_TOL = 0.02  # net923 / PLNGENAN
K4_CEMS_TOL = 0.02  # cems_vs_egrid_total
#: H-B fires when >= this share of the plant's CEMS fuel or gross sits outside
#: the family the comparator keeps.
HB_TRUNCATION = 0.10
#: H-C fires when the plant's own measured rate moves more than this
#: year-on-year while the model holds one frozen vintage.
HC_YOY = 0.10

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


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def keeper_config(year: int) -> ScenarioConfig:
    """The CURRENT keeper's exact ``ScenarioConfig``, re-pointed at ``year``.

    The keeper solved before nyiso-114 deleted the inert ``CT_CHP`` tranche
    heat-rate override triple (2026-08-03, rule 26 ``[R-DELETE]``), so its
    ``run_config.json`` still carries those three keys. They are dropped here
    ONLY because they appear in the repo's own retired-field registry
    ``scenarios._CACHE_KEY_RETIRED_FIELDS`` (rule 24 ``[R-REGISTRY]``: no hand
    map). Any OTHER unknown key is a hard failure — a silently-dropped live
    flag is exactly the miso-115 section 4 defect.
    """
    from market_sim.config.scenarios import _CACHE_KEY_RETIRED_FIELDS

    d = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    from dataclasses import fields as _dc_fields

    unknown = set(d) - {f.name for f in _dc_fields(ScenarioConfig)}
    stale = unknown & set(_CACHE_KEY_RETIRED_FIELDS)
    if unknown - stale:
        raise SystemExit(f"K2: unknown ScenarioConfig keys {sorted(unknown - stale)}")
    return ScenarioConfig(
        **{k: v for k, v in d.items() if k not in stale}
    ).with_overrides(weather_year=year)


def model_fleet(year: int) -> pd.DataFrame:
    """MISO's modelled fleet for ``year``, one row per generator.

    Heat-rate flags come from the KEEPER's own ``ScenarioConfig`` (K2). A probe
    that lets ``load_fleet_from_csv`` default them reads a different model than
    the keeper solved — the origin of miso-115 section 4's withdrawn finding.
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


def campd_units(year: int, plant_codes: set[int]) -> pd.DataFrame:
    """CAMPD hourly unit rows for the given plants, on the model's calendar.

    Identical construction to miso-116's probe (K1 comparability).
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
    out["heatInput"] = out["heatInput"].fillna(0.0)
    return out


def artifact() -> pd.DataFrame:
    """The committed MISO CHP power-only artifact (all rows, all flags)."""
    return pd.read_csv(PROCESSED_DIR / f"chp_power_only_heat_rates_{ISO}.csv")


def net923_by_plant(year: int) -> dict[int, float]:
    """``{plant_id: annual EIA-923 net MWh}``, the model's own loader."""
    from market_sim.data.eia923 import load_monthly_generation

    gen = load_monthly_generation()
    gen = gen[gen["year"] == int(year)]
    if gen.empty:
        return {}
    tot = gen.groupby(gen["plant_id"].astype(int))["netgen_annual_mwh"].sum()
    return {int(p): float(v) for p, v in tot.items()}


# --------------------------------------------------------------------------- #
# A. K1 reproduction — miso-116 part E, verbatim basis
# --------------------------------------------------------------------------- #
def part_a(
    fleets: dict[int, pd.DataFrame], campds: dict[int, pd.DataFrame]
) -> tuple[dict[int, pd.DataFrame], bool]:
    """Reproduce miso-116 part E before any correction is applied (K1)."""
    print("=" * 78)
    print("A. K1 REPRODUCTION — miso-116 part E on miso-116's own basis")
    print("=" * 78)

    rates = measured_chp_heat_rates(ISO)
    out: dict[int, pd.DataFrame] = {}
    ok = True
    for year in YEARS:
        fleet, campd = fleets[year], campds[year]
        sub = fleet[fleet["klass"] == KLASS]
        plants = set(sub["plant_code"].unique())
        u = campd[campd["plant_code"].isin(plants) & (campd["family"] == FAM)]
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
            rows.append(
                {
                    "plant": code,
                    "cap": cap,
                    "model_hr": float((s["heat_rate"] * s["pmax_mw"]).sum() / cap),
                    "campd_hr": float(r["campd_gross_hr"]),
                    "on_artifact": (code, KLASS) in rates,
                }
            )
        d = pd.DataFrame(rows)
        d["ratio"] = d["model_hr"] / d["campd_hr"]
        out[year] = d
        w = d["cap"].to_numpy()
        below = d[d["ratio"] < 0.85]
        share = float(below["cap"].sum()) / w.sum()
        print(
            f"\n  {year}: {len(d)} matched CC_CHP plants, {w.sum():,.0f} MW"
            f" | below 0.85x: {len(below)}/{len(d)} ({share:.1%} of matched cap)"
            f" | on artifact {int(below['on_artifact'].sum())}/{len(below)}"
        )
        if year == 2023:
            for r in below.sort_values("cap", ascending=False).itertuples(index=False):
                exp = MISO116_E.get(int(r.plant))
                mark = "  <-- NOT IN miso-116" if exp is None else ""
                print(
                    f"      plant {r.plant:<6d} {r.cap:6,.0f} MW  model "
                    f"{r.model_hr:5.2f}  CAMPD gross {r.campd_hr:5.2f}  "
                    f"ratio {r.ratio:.3f}{mark}"
                )
            got = set(below["plant"].astype(int))
            if got != set(TARGETS):
                print(f"    K1 FAIL: plant set {sorted(got)} != {sorted(TARGETS)}")
                ok = False
            for r in below.itertuples(index=False):
                exp = MISO116_E.get(int(r.plant))
                if exp and abs(r.ratio - exp[3]) > K1_TOL_RATIO:
                    print(
                        f"    K1 FAIL: plant {r.plant} ratio {r.ratio:.3f} vs "
                        f"published {exp[3]:.3f}"
                    )
                    ok = False
            if len(d) != K1_N_MATCHED or abs(w.sum() - K1_MATCHED_MW) > 2.0:
                print(f"    K1 FAIL: {len(d)} plants / {w.sum():,.0f} MW")
                ok = False
            if abs(share - K1_BELOW_SHARE) > 0.005:
                print(f"    K1 FAIL: capacity share {share:.1%}")
                ok = False
    print(f"\n  K1 REPRODUCTION: {'PASS' if ok else 'FAIL'}")
    return out, ok


# --------------------------------------------------------------------------- #
# B/C. Decomposition and the basis-matched comparator
# --------------------------------------------------------------------------- #
def part_bc(
    e116: dict[int, pd.DataFrame],
    campds: dict[int, pd.DataFrame],
    art: pd.DataFrame,
    nets: dict[int, dict[int, float]],
) -> pd.DataFrame:
    """ratio = A_cems x F_family x G_gross, then R_basis on two meters."""
    print("\n" + "=" * 78)
    print("B/C. DECOMPOSITION and the BASIS-MATCHED comparator")
    print("=" * 78)
    print(
        "\n  ratio (miso-116)  =  model_hr / (CEMS_heat_CC / CEMS_gross_CC)\n"
        "                    =  A_cems  x  F_family  x  G_gross   [exact]\n"
        "    A_cems   = eGRID total heat / CEMS total heat   (meter agreement)\n"
        "    F_family = CEMS total heat / CEMS heat in family CC  (truncation)\n"
        "    G_gross  = CEMS gross load in family CC / PLNGENAN   (coverage)\n"
        "  G_gross < 1.0 is PHYSICALLY IMPOSSIBLE for a matched population:\n"
        "  gross generation is never below net generation.\n"
    )

    a = art[(art["plant_code"].isin(TARGETS)) & (art["plant_group"] == KLASS)]
    a = a.set_index("plant_code")
    rows = []
    for year in YEARS:
        campd = campds[year]
        d = e116[year].set_index("plant")
        for p in TARGETS:
            u = campd[campd["plant_code"] == p]
            heat_tot = float(u["heatInput"].sum())
            gross_tot = float(u["grossLoad"].sum())
            ucc = u[u["family"] == FAM]
            heat_cc = float(ucc["heatInput"].sum())
            gross_cc = float(ucc["grossLoad"].sum())
            egrid_tot = float(
                a.loc[p, "heat_input_electric_mmbtu"]
                + a.loc[p, "heat_input_thermal_mmbtu"]
            )
            plngenan = float(a.loc[p, "net_mwh"])
            net923 = float(nets[year].get(p, float("nan")))
            model_hr = float(d.loc[p, "model_hr"])

            A = egrid_tot / heat_tot if heat_tot else float("nan")
            F = heat_tot / heat_cc if heat_cc else float("nan")
            G = gross_cc / plngenan if plngenan else float("nan")
            rows.append(
                {
                    "year": year,
                    "plant": p,
                    "model_hr": model_hr,
                    "ratio_116": float(d.loc[p, "ratio"]),
                    "A_cems": A,
                    "F_family": F,
                    "G_gross": G,
                    "recon": A * F * G,
                    "heat_tot": heat_tot,
                    "gross_tot": gross_tot,
                    "heat_out_cc": 1.0 - heat_cc / heat_tot if heat_tot else 0.0,
                    "gross_out_cc": 1.0 - gross_cc / gross_tot if gross_tot else 0.0,
                    "plngenan": plngenan,
                    "net923": net923,
                    "gross_over_net": gross_tot / net923 if net923 else float("nan"),
                    "net_ratio": net923 / plngenan if plngenan else float("nan"),
                    "hr_match": heat_tot / net923 if net923 else float("nan"),
                }
            )
    df = pd.DataFrame(rows)
    df["R_basis"] = df["model_hr"] / df["hr_match"]
    df["recon_err"] = (df["recon"] - df["ratio_116"]).abs()

    print("  B. Decomposition of the miso-116 ratio (exact identity)\n")
    print(
        f"    {'yr':<5}{'plant':<8}{'ratio':>7}{'A_cems':>9}{'F_family':>10}"
        f"{'G_gross':>9}{'A*F*G':>9}{'err':>9}"
    )
    for r in df.itertuples(index=False):
        print(
            f"    {r.year:<5}{r.plant:<8}{r.ratio_116:7.3f}{r.A_cems:9.4f}"
            f"{r.F_family:10.4f}{r.G_gross:9.4f}{r.recon:9.3f}{r.recon_err:9.5f}"
        )
    print(f"\n    max |A*F*G - ratio| = {df['recon_err'].max():.6f}")

    print("\n  B. Where the comparator's two sides lose population\n")
    print(
        f"    {'yr':<5}{'plant':<8}{'fuel out CC':>13}{'gross out CC':>14}"
        f"{'CEMS gross/net923':>19}"
    )
    for r in df.itertuples(index=False):
        print(
            f"    {r.year:<5}{r.plant:<8}{r.heat_out_cc:12.1%}{r.gross_out_cc:14.1%}"
            f"{r.gross_over_net:19.4f}"
        )

    print("\n  C. Basis-matched comparator — CAMPD fuel over EIA-923 net MWh\n")
    print(
        f"    {'yr':<5}{'plant':<8}{'model_hr':>10}{'HR_match':>10}{'R_basis':>9}"
        f"{'net923/PLNGENAN':>17}"
    )
    for r in df.itertuples(index=False):
        print(
            f"    {r.year:<5}{r.plant:<8}{r.model_hr:10.4f}{r.hr_match:10.4f}"
            f"{r.R_basis:9.3f}{r.net_ratio:17.6f}"
        )
    return df


# --------------------------------------------------------------------------- #
# D/E/F. The REAL-branch hypotheses
# --------------------------------------------------------------------------- #
def part_def(
    df: pd.DataFrame,
    fleets: dict[int, pd.DataFrame],
    art: pd.DataFrame,
    campds: dict[int, pd.DataFrame],
) -> None:
    """H-C vintage staleness, H-D mis-key, H-E mixed facility."""
    print("\n" + "=" * 78)
    print("D/E/F. THE REAL-BRANCH HYPOTHESES")
    print("=" * 78)

    print("\n  D (H-C). Year-on-year move of the plant's OWN measured rate")
    print("     vs the model's frozen 2023-vintage eGRID rate.\n")
    print(f"    {'plant':<8}{'2023':>9}{'2024':>9}{'2025':>9}{'max |yoy|':>12}{'':>4}")
    for p in TARGETS:
        s = df[df["plant"] == p].set_index("year")["hr_match"]
        yoy = max(abs(s[2024] / s[2023] - 1.0), abs(s[2025] / s[2024] - 1.0))
        flag = "  H-C FIRES" if yoy > HC_YOY else ""
        print(f"    {p:<8}{s[2023]:9.4f}{s[2024]:9.4f}{s[2025]:9.4f}{yoy:11.1%}{flag}")

    print("\n  E (H-D). Loaded heat rate vs the artifact's published rate\n")
    a = art.set_index(["plant_code", "plant_group"])["heat_rate"]
    bad = 0
    for year in YEARS:
        fl = fleets[year]
        for p in TARGETS:
            for k in sorted(fl[fl["plant_code"] == p]["klass"].unique()):
                loaded = fl[(fl["plant_code"] == p) & (fl["klass"] == k)]
                caps = loaded["pmax_mw"].to_numpy()
                hrs = loaded["heat_rate"].to_numpy()
                want = float(a.get((p, k), float("nan")))
                spread = float(hrs.max() - hrs.min())
                mismatch = (
                    "" if (want == want and abs(hrs.mean() - want) < 1e-6) else "  <--"
                )
                if mismatch:
                    bad += 1
                if year == 2023:
                    print(
                        f"    {year} plant {p:<7}{k:<9} n={len(loaded):<3} "
                        f"cap {caps.sum():7,.1f} MW  loaded {hrs.mean():7.4f} "
                        f"(spread {spread:.4f})  artifact "
                        f"{want if want == want else float('nan'):7.4f}{mismatch}"
                    )
    print(f"\n    H-D: {bad} (plant, class, year) mismatches over all 3 years")

    print("\n  F (H-E). 55088 Dearborn — one plant rate over two prime movers\n")
    for year in YEARS:
        u = campds[year]
        u = u[u["plant_code"] == 55088]
        g = u.groupby("family")[["heatInput", "grossLoad"]].sum()
        g["gross_hr"] = g["heatInput"] / g["grossLoad"].where(g["grossLoad"] > 0)
        for fam, r in g.iterrows():
            print(
                f"    {year}  family {fam:<8} heat {r.heatInput:14,.0f} MMBtu  "
                f"gross {r.grossLoad:12,.0f} MWh  gross HR "
                f"{r.gross_hr if r.gross_hr == r.gross_hr else float('nan'):7.3f}"
            )


# --------------------------------------------------------------------------- #
# H/I/J. Corroboration — CEMS unit anatomy, the parasitic artifact, 55088's fuel
# --------------------------------------------------------------------------- #
def part_hij(
    campds: dict[int, pd.DataFrame],
    nets: dict[int, dict[int, float]],
    art: pd.DataFrame,
) -> None:
    """Where the CEMS gross-load hole physically is, and who else recorded it."""
    print("\n" + "=" * 78)
    print("H/I/J. CORROBORATION")
    print("=" * 78)

    print("\n  H. CEMS unit anatomy at the four plants (2023), by unitType\n")
    u = campds[2023]
    for p in TARGETS:
        s = u[u["plant_code"] == p]
        g = s.groupby(["family", "unitType"]).agg(
            units=("unitId", "nunique"),
            heat=("heatInput", "sum"),
            gross=("grossLoad", "sum"),
        )
        print(f"    plant {p}:")
        for (fam, ut), r in g.iterrows():
            zero = "   <-- FUEL, NO GROSS LOAD" if r.gross == 0 and r.heat > 0 else ""
            print(
                f"      {fam:<8} {str(ut)[:34]:<36} n={r.units:<3} "
                f"heat {r.heat:13,.0f}  gross {r.gross:12,.0f}{zero}"
            )

    print(
        "\n  I. The parasitic-factor artifact's OWN record for these plants\n"
        "     (a different derive, written for a different purpose — "
        "derive_parasitic_factors)\n"
    )
    par = pd.read_parquet(PROCESSED_DIR / "parasitic_load_factors.parquet")
    sub = par[par["plant_id"].isin(TARGETS)]
    if sub.empty:
        print("      no rows")
    for r in sub.itertuples(index=False):
        impossible = "  net > gross: IMPOSSIBLE" if r.net_mwh > r.gross_mwh else ""
        print(
            f"      plant {r.plant_id:<7} year {r.year:<6} gross {r.gross_mwh:12,.0f}"
            f"  net {r.net_mwh:12,.0f}  net/gross "
            f"{r.net_mwh / r.gross_mwh:6.3f}  {r.source}/{r.flag}{impossible}"
        )
    print(
        "\n      Plants absent from the table carry no measured factor at all;\n"
        "      every row that IS present is out_of_band and fell back to the\n"
        "      class default. The comparator's denominator was already known bad."
    )

    print("\n  J. 55088 Dearborn — the direct-fired boiler inside a topping rate\n")
    a = art[(art["plant_code"] == 55088) & (art["plant_group"] == KLASS)].iloc[0]
    for year in YEARS:
        s = campds[year][campds[year]["plant_code"] == 55088]
        heat_tot = float(s["heatInput"].sum())
        heat_boiler = float(s[s["family"].str.startswith("ST")]["heatInput"].sum())
        net = float(nets[year].get(55088, float("nan")))
        print(
            f"    {year}: total CEMS fuel {heat_tot:13,.0f} MMBtu | "
            f"zero-output boiler fuel {heat_boiler:12,.0f} "
            f"({heat_boiler / heat_tot:.1%}) | net923 {net:11,.0f} MWh\n"
            f"          loaded rate {float(a.heat_rate):.4f} vs power-train-only "
            f"{(heat_tot - heat_boiler) / net:.4f} MMBtu/MWh "
            f"(+{float(a.heat_rate) / ((heat_tot - heat_boiler) / net) - 1:.1%})"
        )
    print(
        f"\n      eGRID thermal_share for this plant is {float(a.thermal_share):.4f},\n"
        "      UNDER the derive's 0.50 unfired-topping ceiling, so its scope gate\n"
        "      passes the plant. CEMS says a share of the fuel is burned in units\n"
        "      that make no electricity at all."
    )


def part_k(art: pd.DataFrame, nets: dict[int, dict[int, float]]) -> None:
    """Does J generalise? Zero-electric-output fuel inside EVERY ok-flagged rate.

    Scans the whole committed artifact, not just the four outlier plants: for
    each ``flag == "ok"`` plant, the share of its 2023 CEMS fuel burned in units
    that report heat input and ZERO gross load. That fuel cannot be a topping
    cycle's free co-product — it is direct-fired host process fuel — and the
    derive charges it to the plant's power tranches.
    """
    print("\n" + "=" * 78)
    print("K. DOES J GENERALISE? — zero-output fuel inside every ok-flagged rate")
    print("=" * 78)

    ok = art[art["flag"] == "ok"]
    plants = sorted({int(p) for p in ok["plant_code"]})
    campd = campd_units(2023, set(plants))
    rows = []
    for p in plants:
        s = campd[campd["plant_code"] == p]
        if s.empty:
            continue
        heat_tot = float(s["heatInput"].sum())
        if heat_tot <= 0:
            continue
        by_unit = s.groupby("unitId")[["heatInput", "grossLoad"]].sum()
        dark = by_unit[(by_unit["grossLoad"] <= 0.0) & (by_unit["heatInput"] > 0.0)]
        heat_dark = float(dark["heatInput"].sum())
        net = float(nets[2023].get(p, float("nan")))
        a = ok[ok["plant_code"] == p]
        rows.append(
            {
                "plant": p,
                "cap": float(a["class_capacity_mw"].sum()),
                "classes": "+".join(sorted(a["plant_group"].unique())),
                "loaded_hr": float(a["heat_rate"].iloc[0]),
                "dark_share": heat_dark / heat_tot,
                "power_only_hr": (heat_tot - heat_dark) / net if net else float("nan"),
            }
        )
    d = pd.DataFrame(rows).sort_values("dark_share", ascending=False)
    d["overcharge"] = d["loaded_hr"] / d["power_only_hr"] - 1.0

    hit = d[d["dark_share"] > 0.01]
    print(
        f"\n  {len(d)} ok-flagged plants matched in CEMS 2023; "
        f"{len(hit)} carry >1 % of their fuel in zero-output units, "
        f"{float(hit['cap'].sum()):,.0f} of {float(d['cap'].sum()):,.0f} MW.\n"
    )
    print(
        f"    {'plant':<8}{'classes':<18}{'cap MW':>9}{'dark fuel':>11}"
        f"{'loaded HR':>11}{'power-only':>12}{'over-charge':>13}"
    )
    for r in d.itertuples(index=False):
        if r.dark_share <= 0.001:
            continue
        print(
            f"    {r.plant:<8}{r.classes:<18}{r.cap:9,.1f}{r.dark_share:11.1%}"
            f"{r.loaded_hr:11.4f}{r.power_only_hr:12.4f}{r.overcharge:13.1%}"
        )
    print(
        "\n    (power-only = CEMS fuel EXCLUDING zero-output units, over EIA-923\n"
        "     net MWh. Plants with no zero-output units are omitted — for them\n"
        "     the loaded rate and the power-only rate are the same number.)"
    )


# --------------------------------------------------------------------------- #
# G. Verdict
# --------------------------------------------------------------------------- #
def verdict(df: pd.DataFrame, k1: bool) -> None:
    """Apply the pre-registered per-plant decision rule (PREREG section 5).

    K3 is reported BOTH ways and the verdict is printed under both readings:

    * **as written** — ``|net923(year)/PLNGENAN - 1| <= 0.02`` in every year.
      PLNGENAN is the frozen eGRID2023 vintage, so in 2024/2025 this compares
      two DIFFERENT years' net generation and fires on every plant. That is a
      mis-specified test, not a finding about the basis.
    * **corrected** — the same-year identity the derive actually claims,
      ``net923(2023) / PLNGENAN(eGRID2023) = 1.000000``.

    The correction is a specification repair with an independent justification
    (it is the derive's own claim), NOT a band moved to reach a verdict; both
    readings are printed so the record carries the rule as pre-registered.
    """
    print("\n" + "=" * 78)
    print("G. VERDICT — pre-registered per-plant decision rule")
    print("=" * 78)
    if not k1:
        print("\n  K1 FIRED — reproduction failed. NO VERDICT (PREREG section 6).")
        return

    print(
        "\n  NOTE on 2023: R_basis is 1.000 in 2023 BY CONSTRUCTION — eGRID total\n"
        "  heat equals CEMS total heat (the artifact's own cems_vs_egrid_total)\n"
        "  and net923(2023) equals PLNGENAN, so the 2023 column carries no\n"
        "  information. 2024 and 2025 are the informative years: the model holds\n"
        "  a frozen 2023 vintage while both meters move independently.\n"
    )
    for p in TARGETS:
        s = df[df["plant"] == p].set_index("year")
        rb = s["R_basis"]
        in_basis = int(((rb >= BASIS_BAND[0]) & (rb <= BASIS_BAND[1])).sum())
        in_free = int(
            (
                (rb.loc[[2024, 2025]] >= BASIS_BAND[0])
                & (rb.loc[[2024, 2025]] <= BASIS_BAND[1])
            ).sum()
        )
        out_real = int(((rb < REAL_BAND[0]) | (rb > REAL_BAND[1])).sum())
        hb = bool(
            (s["heat_out_cc"] >= HB_TRUNCATION).any()
            or (s["gross_out_cc"] >= HB_TRUNCATION).any()
        )
        ha = bool((s["G_gross"] < 1.0).all())
        k3_written = bool(((s["net_ratio"] - 1.0).abs() <= K3_NET_TOL).all())
        k3_fixed = bool(abs(float(s.loc[2023, "net_ratio"]) - 1.0) <= K3_NET_TOL)

        def _rule(k3: bool) -> str:
            if not k3:
                return "INDETERMINATE (K3 fired)"
            if in_basis >= 2 and (ha or hb):
                return "BASIS-ARTIFACT — no charter, no solve"
            if out_real >= 2:
                return "REAL INPUT ERROR — charter owed"
            return "INDETERMINATE — report, no charter"

        print(
            f"  plant {p}: R_basis {rb[2023]:.3f} / {rb[2024]:.3f} / {rb[2025]:.3f}"
            f"  | in band {in_basis}/3 (informative years {in_free}/2)"
            f" | H-A {ha} | H-B {hb}\n"
            f"    K3 as written  ({k3_written}) -> {_rule(k3_written)}\n"
            f"    K3 corrected   ({k3_fixed}) -> {_rule(k3_fixed)}\n"
        )


def main() -> None:
    print("miso-118 Phase-0 probe — CC_CHP plant-level outliers (NO LP)\n")
    cfg = keeper_config(2023)
    print(
        f"  keeper bundle: {BUNDLE.name}\n"
        f"  K2 flag fidelity (READ from run_config.json): "
        f"measured_chp_heat_rates={cfg.measured_chp_heat_rates}, "
        f"measured_ct_heat_rates={getattr(cfg, 'measured_ct_heat_rates', False)}"
    )
    assert cfg.measured_chp_heat_rates, (
        "K2: keeper does not arm measured_chp_heat_rates"
    )

    art = artifact()
    a4 = art[(art["plant_code"].isin(TARGETS)) & (art["plant_group"] == KLASS)]
    print("\n  K4 CEMS completeness (artifact's own cems_vs_egrid_total):")
    for r in a4.itertuples(index=False):
        mark = "" if abs(r.cems_vs_egrid_total - 1.0) <= K4_CEMS_TOL else "  <-- K4"
        print(f"    plant {r.plant_code:<7} {r.cems_vs_egrid_total:.5f}{mark}")

    fleets = {y: model_fleet(y) for y in YEARS}
    plants = set()
    for f in fleets.values():
        plants |= set(f[f["klass"].isin((KLASS, "CT_CHP"))]["plant_code"].astype(int))
    campds = {y: campd_units(y, plants) for y in YEARS}
    nets = {y: net923_by_plant(y) for y in YEARS}

    e116, k1 = part_a(fleets, campds)
    df = part_bc(e116, campds, art, nets)
    part_def(df, fleets, art, campds)
    part_hij(campds, nets, art)
    part_k(art, nets)
    verdict(df, k1)


if __name__ == "__main__":
    main()
