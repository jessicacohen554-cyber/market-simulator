"""caiso-132 D-gate instrument — the derive-first kill/pass gates for ASK A1.

A1 (``docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`` §3) proposes arming
the caiso-121 *corridor / export-path* family in surplus — the corridor's
export-direction deliverability envelope plus a surplus-scoped
``caiso_wecc_export_floor`` — to close **C3a-2025** (+10.91 %, needing only
−$0.31/MWh) by removing the DSW→CA corridor congestion rent that
``FINDING-caiso131`` §7 measures at **+$3.87/MWh in Sep–Dec 2025 (57 % of the
window's over-price)**.

The memo makes the ask conditional on three no-LP gates, in the caiso-127 §5 /
caiso-129 discipline that let S1 be killed for the cost of a derive. This
instrument runs them, and ONLY them:

* **D1 — the export-direction envelope exists and is stable.** Derive the
  measured net-export envelope on each corridor leg from the committed EIA-930
  interchange series (``measured_corridor_flow_envelope(direction="export")``,
  the same object the LP already builds) and gate the hour-of-day shape on
  pairwise cross-year ``r >= 0.99`` — the caiso-106/107/129 standard. The
  import-direction envelope is carried alongside as the **control** limb, the
  role the charge side played at caiso-129 (it cleared 0.9919 while the
  discharge side failed at 0.9726).
* **D2 — the envelope binds where the defect is.** In the Sep–Dec 2025
  surplus-regime hours that carry the +$3.87 term, the export-direction bound
  must be binding (or within 10 % of binding) in >= 50 % of hours. Binding
  direction is read off the LP's OWN duals, exactly and without a solve: for a
  corridor link priced between its two ends, ``lambda_CA - lambda_corridor``
  is ``mu_import - mu_export`` with both multipliers non-negative, so the sign
  of the measured spread *is* the binding direction (positive => the import
  ceiling binds and the export bound is strictly slack; negative => the export
  bound binds; ~0 => neither).
* **D3 — direction check.** The mechanism must *reduce* ``lambda_CA -
  lambda_WECC_DSW``. An export floor can only move energy OUT of CA; in an
  import-bound hour that is a supply reduction, so CA's lambda weakly rises and
  the spread widens (the ``FINDING-caiso129`` §3(c) "a floor can only ADD" form,
  in its export mirror). Reported with the realised magnitude of the export
  envelope in the defect hours, so an inert mechanism is distinguished from a
  wrong-signed one.

Everything is read from the keeper's **committed** bytes — the hourly sidecars
(``hourly/system_<y>.parquet``, ``class_hourly_<y>.parquet``), the committed
actual-LMP reference, and the committed EIA-930 interchange parquet that
``measured_corridor_flow_envelope`` already reads. **No LP is built, no matrix
is assembled, no solver is called, and nothing is armed** (rule 1 ``[R-STRUCT]``
/ rule 19 ``[R-ONE-MECH]``: arming remains a separate owner act).

Regime conventions are caiso-120/121's, unchanged so the rows compose with
theirs: belly = hod 10–15, surplus = belly hour with measured RT <= $20/MWh,
intertie equalisation tolerance $0.50/MWh (caiso-105).

Usage::

    PYTHONPATH=.:src .venv/bin/python \\
        scripts/probes/_caiso132_corridor_export_gates.py \\
        results/calibration/caiso130_nameplate_B [--years 2023 2024 2025]

Finding: ``results/calibration/FINDING-caiso132-corridor-export-gates-2026-07-28.md``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
T = 8760
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
BELLY = (10, 11, 12, 13, 14, 15)  # caiso-120 lane convention
SURPLUS_THRESHOLD = 20.0  # $/MWh — the caiso-120 regime split point
EQ_TOL = 0.5  # $/MWh — the caiso-105 intertie equalisation tolerance
SEP_DEC = (9, 10, 11, 12)  # FINDING-caiso131 §7's window (81 % of the C3a gap)
# Corridor zone -> the CA trading zone its import link terminates on
# (model.interchange.caiso._CAISO_CORRIDOR_LINK_TO, mirrored so the probe reads
# the same pairing the LP wires).
CORRIDOR_TERMINUS = {"WECC_PNW": "NP15", "WECC_DSW": "SP15_rest"}
# D-gate thresholds, as filed in the caiso-131 ask memo §3.
D1_R_MIN = 0.99  # pairwise cross-year r on the hour-of-day shape
D2_BIND_SHARE_MIN = 0.50  # share of defect hours the envelope must bind in
D2_NEAR_BIND_FRAC = 0.10  # "within 10 % of binding" counts for D2

ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"


# ---------------------------------------------------------------------------
# committed-bytes readers (no LP)
# ---------------------------------------------------------------------------
def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT price ($/MWh), NaN where uncovered."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(T)).to_numpy()


def zonal_prices(bundle: Path, year: int) -> pd.DataFrame:
    """P1 per-zone hourly price pivot from the committed system sidecar."""
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="price")


def zonal_demand(bundle: Path, year: int) -> pd.DataFrame:
    """P1 per-zone hourly demand pivot from the committed system sidecar."""
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="demand")


def class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 per-class hourly MW pivot from the committed class sidecar."""
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return c[c["pass"] == "P1"].pivot_table(index="hour", columns="klass", values="mw")


def envelopes(year: int) -> dict[str, dict[str, np.ndarray]]:
    """Both corridor deliverability envelopes for ``year``, MW per model hour.

    Returns ``{"import": {zone: (8760,)}, "export": {zone: (8760,)}}`` straight
    from :func:`market_sim.data.eia_loader.measured_corridor_flow_envelope` —
    the SAME object ``scripts/run_calibration.py`` hands to
    ``build_caiso_corridor_flow_groups``, so the gate is measured on the LP's
    own bound and not on a re-derivation of it.
    """
    from market_sim.data.eia_loader import measured_corridor_flow_envelope

    return {
        d: (measured_corridor_flow_envelope(ISO, year, T, direction=d) or {})
        for d in ("import", "export")
    }


def month_of_hour() -> np.ndarray:
    """1-based model month for each of the 8760 fixed-calendar hours."""
    from market_sim.data.fleet import _hour_to_month_index

    return _hour_to_month_index(T) + 1


# ---------------------------------------------------------------------------
# D1 — does the export-direction envelope exist and is its shape stable?
# ---------------------------------------------------------------------------
def hod_shape(series: np.ndarray) -> np.ndarray:
    """Mean hour-of-day profile (24,) of an 8760 series.

    Equivalent to caiso-129's normalised annual hod *share* for the purpose of
    the ``r`` gate: on the fixed 8,760 calendar every hod carries exactly 365
    days, so the share vector is a positive scalar multiple of this mean profile
    and Pearson ``r`` is identical (verified to six decimals, FINDING §4).
    """
    return (
        series.reshape(-1, 24).mean(axis=0) if series.size == T else np.full(24, np.nan)
    )


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r between two 24-vectors; NaN when either is degenerate."""
    if (
        np.std(a) == 0
        or np.std(b) == 0
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
    ):
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def section_d0(bundle: Path, years: tuple[int, ...]) -> dict:
    """D0: the GLOBAL binding-direction census — all 8,760 h of every year.

    Scope check for the whole family, before its own gates are run: if the
    export-direction bound is never the active one anywhere in the record, then
    no export-direction mechanism can change the LP anywhere, and the question
    of where the defect lives never arises. Read off the duals exactly as D2
    does (the sign of ``lambda_terminus - lambda_corridor`` IS the binding
    direction), so it needs no solve and no flow sidecar.
    """
    print("\n" + "=" * 96)
    print("D0 — global binding-direction census (ALL hours, ALL years): is the export")
    print("     bound EVER the active one?")
    print("=" * 96)
    print(
        f"  {'year':>6} {'leg':<10} {'import-bd':>10} {'export-bd':>10} {'neither':>9} "
        f"{'min spread':>11}"
    )
    total_export_bound = 0
    total_hours = 0
    for year in years:
        sp = spread_frame(bundle, year)
        for leg in CORRIDOR_TERMINUS:
            if leg not in sp.columns:
                continue
            s = sp[leg].to_numpy()
            eb = int((s < -EQ_TOL).sum())
            total_export_bound += eb
            total_hours += s.size
            print(
                f"  {year:>6} {leg:<10} {(s > EQ_TOL).mean():>10.4f} "
                f"{(s < -EQ_TOL).mean():>10.4f} {(np.abs(s) <= EQ_TOL).mean():>9.4f} "
                f"{s.min():>11.2f}"
            )
    print(
        f"\n  >>> export-direction bound active in {total_export_bound} of "
        f"{total_hours} corridor-hours ({total_export_bound / max(total_hours, 1):.4%})."
    )
    return {"export_bound_hours": total_export_bound, "corridor_hours": total_hours}


def section_d1(years: tuple[int, ...]) -> dict:
    """D1: the export envelope's level, and its cross-year hour-of-day stability."""
    print("\n" + "=" * 96)
    print("D1 — the export-direction envelope: does it exist, and is its shape stable?")
    print("=" * 96)
    print(
        "  Gate: pairwise cross-year r >= %.2f on the hour-of-day shape "
        "(caiso-106/107/129 standard).\n"
        "  The IMPORT limb is the control (the role caiso-129's charge side "
        "played at r=0.9919)." % D1_R_MIN
    )

    env = {y: envelopes(y) for y in years}
    shapes: dict[tuple[str, str], dict[int, np.ndarray]] = {}

    for direction in ("export", "import"):
        print(f"\n  --- {direction.upper()} envelope, level (MW) ---")
        print(
            f"  {'leg':<10} {'year':>6} {'mean':>10} {'median':>10} {'p90':>10} {'max':>10} {'share>0':>9}"
        )
        for leg in ("WECC_DSW", "WECC_PNW"):
            for y in years:
                e = env[y][direction].get(leg)
                if e is None:
                    print(f"  {leg:<10} {y:>6}   (absent)")
                    continue
                shapes[(direction, leg)] = shapes.get((direction, leg), {})
                shapes[(direction, leg)][y] = hod_shape(e)
                print(
                    f"  {leg:<10} {y:>6} {e.mean():>10.1f} {np.median(e):>10.1f} "
                    f"{np.percentile(e, 90):>10.1f} {e.max():>10.1f} "
                    f"{float((e > 1.0).mean()):>9.3f}"
                )

    verdicts: dict[tuple[str, str], dict] = {}
    for direction in ("export", "import"):
        print(f"\n  --- {direction.upper()} envelope, cross-year hour-of-day r ---")
        for leg in ("WECC_DSW", "WECC_PNW"):
            sh = shapes.get((direction, leg), {})
            pairs = []
            for i, y1 in enumerate(years):
                for y2 in years[i + 1 :]:
                    if y1 in sh and y2 in sh:
                        pairs.append(((y1, y2), pearson(sh[y1], sh[y2])))
            if not pairs:
                print(f"  {leg:<10} (no pairs)")
                continue
            rs = [r for _, r in pairs]
            worst = np.nanmin(rs) if np.isfinite(rs).any() else float("nan")
            ok = np.isfinite(worst) and worst >= D1_R_MIN
            txt = "  ".join(f"{a}/{b}: {r:.4f}" for (a, b), r in pairs)
            verdicts[(direction, leg)] = {
                "worst_r": worst,
                "pass": bool(ok),
                "pairs": pairs,
            }
            print(
                f"  {leg:<10} {txt}   worst {worst:.4f}  "
                f"{'PASS' if ok else 'FAIL'} (>= {D1_R_MIN})"
            )
            if not np.isfinite(worst):
                print(
                    f"             ^ degenerate: the {leg} {direction} envelope is "
                    "constant across the hour-of-day (no shape to correlate)."
                )

    exp_ok = all(
        verdicts.get(("export", leg), {}).get("pass", False)
        for leg in ("WECC_DSW", "WECC_PNW")
        if ("export", leg) in verdicts
    )
    print(
        f"\n  >>> D1 verdict (export limb, both legs): "
        f"{'PASS' if exp_ok and verdicts else 'FAIL'}"
    )
    return {"env": env, "verdicts": verdicts, "pass": bool(exp_ok and verdicts)}


# ---------------------------------------------------------------------------
# the defect hour set — Sep-Dec 2025 surplus regime
# ---------------------------------------------------------------------------
def defect_mask(bundle: Path, year: int) -> np.ndarray:
    """Sep-Dec surplus-regime belly hours — the set carrying FINDING §7's term."""
    hod = np.arange(T) % 24
    mon = month_of_hour()
    rt = actual_rt(year)
    return (
        np.isin(hod, BELLY)
        & np.isin(mon, SEP_DEC)
        & np.isfinite(rt)
        & (rt <= SURPLUS_THRESHOLD)
    )


def spread_frame(bundle: Path, year: int) -> pd.DataFrame:
    """Per-hour corridor spread ``lambda_terminus - lambda_corridor`` per leg."""
    p = zonal_prices(bundle, year)
    out = {}
    for leg, term in CORRIDOR_TERMINUS.items():
        if leg in p.columns and term in p.columns:
            out[leg] = (p[term] - p[leg]).to_numpy()
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# D2 — does the export bound bind where the defect is?
# ---------------------------------------------------------------------------
def section_d2(bundle: Path, years: tuple[int, ...], d1: dict) -> dict:
    """D2: binding-direction census on the defect hours, read off the LP duals."""
    print("\n" + "=" * 96)
    print("D2 — does the export-direction bound BIND where the +$3.87 defect lives?")
    print("=" * 96)
    print(
        "  Method (exact, no solve): for a corridor link bounded\n"
        "    -export_cap <= f <= +import_cap,\n"
        "  LP optimality gives  lambda_terminus - lambda_corridor = mu_import - mu_export\n"
        "  with mu_import, mu_export >= 0 and complementary. So the SIGN of the measured\n"
        "  zonal spread IS the binding direction:  > +tol import-bound (export bound\n"
        "  STRICTLY SLACK);  < -tol export-bound;  |.| <= tol neither binds.\n"
        f"  tol = ${EQ_TOL:.2f}/MWh (caiso-105).  Gate: export-bound in >= "
        f"{D2_BIND_SHARE_MIN:.0%} of the defect hours."
    )

    # Reconciliation to FINDING-caiso131 §7, so the rows below are readable
    # against the memo's headline: that table is CA demand-weighted lambda minus
    # the WECC_DSW node over ALL Sep-Dec hours (+$3.87 in 2025). The gate rows
    # then narrow to the surplus-regime belly inside that window.
    print("\n  --- reconciliation to FINDING-caiso131 §7 (ALL Sep-Dec hours) ---")
    print(
        f"      {'year':>6} {'CA lam':>8} {'DSW lam':>8} {'CA-DSW':>8} "
        f"{'PNW lam':>8} {'CA-PNW':>8}"
    )
    for year in years:
        p = zonal_prices(bundle, year)
        dem = zonal_demand(bundle, year)
        ca = [z for z in CA_ZONES if z in p.columns]
        sel = np.isin(month_of_hour(), SEP_DEC)
        w = dem[ca].sum(axis=1).to_numpy()[sel]
        ca_lam = ((p[ca] * dem[ca]).sum(axis=1) / dem[ca].sum(axis=1)).to_numpy()[sel]
        dsw = p["WECC_DSW"].to_numpy()[sel]
        pnw = p["WECC_PNW"].to_numpy()[sel]
        print(
            f"      {year:>6} {np.average(ca_lam, weights=w):>8.2f} "
            f"{np.average(dsw, weights=w):>8.2f} "
            f"{np.average(ca_lam - dsw, weights=w):>8.2f} "
            f"{np.average(pnw, weights=w):>8.2f} "
            f"{np.average(ca_lam - pnw, weights=w):>8.2f}"
        )

    res = {}
    for year in years:
        mask = defect_mask(bundle, year)
        sp = spread_frame(bundle, year)
        p = zonal_prices(bundle, year)
        dem = zonal_demand(bundle, year)
        ca = [z for z in CA_ZONES if z in p.columns]
        ca_lam = (p[ca] * dem[ca]).sum(axis=1) / dem[ca].sum(axis=1)
        idx = np.flatnonzero(mask)
        print(f"\n  --- {year}: Sep-Dec surplus belly, n = {idx.size} h ---")
        if idx.size == 0:
            continue
        print(
            f"      CA lambda ${ca_lam.to_numpy()[idx].mean():7.2f}   "
            f"actual RT ${actual_rt(year)[idx].mean():7.2f}"
        )
        print(
            f"      {'leg':<10} {'lam_leg':>9} {'spread':>9} "
            f"{'import-bd':>10} {'export-bd':>10} {'neither':>9}"
        )
        year_res = {}
        for leg in CORRIDOR_TERMINUS:
            if leg not in sp.columns:
                continue
            s = sp[leg].to_numpy()[idx]
            imp_bd = float((s > EQ_TOL).mean())
            exp_bd = float((s < -EQ_TOL).mean())
            nei = float((np.abs(s) <= EQ_TOL).mean())
            print(
                f"      {leg:<10} {p[leg].to_numpy()[idx].mean():>9.2f} "
                f"{s.mean():>9.2f} {imp_bd:>10.3f} {exp_bd:>10.3f} {nei:>9.3f}"
            )
            year_res[leg] = {
                "import_bound": imp_bd,
                "export_bound": exp_bd,
                "neither": nei,
                "mean_spread": float(s.mean()),
            }
        res[year] = year_res

        # Corroboration: the export envelope's own magnitude in these hours, and
        # the model's total import against the corridor import ceiling.
        env = d1["env"][year]
        ch = class_hourly(bundle, year)
        imp_mw = ch["import"].to_numpy() if "import" in ch.columns else np.zeros(T)
        cap_sum = (
            np.sum([env["import"][z] for z in env["import"]], axis=0)
            if env["import"]
            else np.zeros(T)
        )
        exp_sum = (
            np.sum([env["export"][z] for z in env["export"]], axis=0)
            if env["export"]
            else np.zeros(T)
        )
        util = imp_mw / np.where(cap_sum > 0, cap_sum, np.nan)
        print(
            f"      corridor import ceiling (sum of legs) {cap_sum[idx].mean():8.0f} MW | "
            f"model import {imp_mw[idx].mean():8.0f} MW | utilisation "
            f"{np.nanmean(util[idx]):.3f}"
        )
        print(
            f"      export ceiling (sum of legs) {exp_sum[idx].mean():8.0f} MW | "
            f"hours with a NON-ZERO export ceiling: "
            f"{float((exp_sum[idx] > 1.0).mean()):.3f}"
        )
        year_res["_export_ceiling_mean_mw"] = float(exp_sum[idx].mean())
        year_res["_export_ceiling_nonzero_share"] = float((exp_sum[idx] > 1.0).mean())
        year_res["_import_utilisation"] = float(np.nanmean(util[idx]))

    tgt = res.get(2025, {})
    dsw = tgt.get("WECC_DSW", {})
    ok = dsw.get("export_bound", 0.0) >= D2_BIND_SHARE_MIN
    print(
        f"\n  >>> D2 verdict (2025 WECC_DSW, the leg carrying the +$3.87 term): "
        f"export-bound share {dsw.get('export_bound', float('nan')):.3f} vs gate "
        f"{D2_BIND_SHARE_MIN:.2f} -> {'PASS' if ok else 'FAIL'}"
    )
    return {"rows": res, "pass": bool(ok)}


# ---------------------------------------------------------------------------
# D3 — sign check
# ---------------------------------------------------------------------------
def section_d3(bundle: Path, years: tuple[int, ...], d2: dict) -> dict:
    """D3: can the family move ``lambda_CA - lambda_DSW`` in the required direction?"""
    print("\n" + "=" * 96)
    print(
        "D3 — sign check: can an export-path mechanism REDUCE lambda_CA - lambda_DSW?"
    )
    print("=" * 96)
    print(
        "  A1 must pull CA lambda DOWN toward its own (correctly-priced) import node.\n"
        "  Both limbs of the family are checked against the D2 census:\n"
        "    (a) the export CEILING (already armed on the keeper via\n"
        "        caiso_corridor_flow_limit -> build_caiso_corridor_flow_groups'\n"
        "        asymmetric group): can only change the LP where the EXPORT bound is\n"
        "        active. In an import-bound hour it is strictly slack => INERT\n"
        "        (the FINDING-caiso129 §3(a) form).\n"
        "    (b) a surplus-scoped export FLOOR (forced net export): moves energy OUT\n"
        "        of CA. In an import-bound hour that is a supply reduction, so CA's\n"
        "        lambda weakly RISES and lambda_DSW weakly falls => the spread WIDENS\n"
        "        (the FINDING-caiso129 §3(c) 'a floor can only ADD' form, mirrored)."
    )

    out = {}
    for year in years:
        mask = defect_mask(bundle, year)
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            continue
        sp = spread_frame(bundle, year)
        p = zonal_prices(bundle, year)
        dem = zonal_demand(bundle, year)
        ca = [z for z in CA_ZONES if z in p.columns]
        ca_lam = ((p[ca] * dem[ca]).sum(axis=1) / dem[ca].sum(axis=1)).to_numpy()
        w = dem[ca].sum(axis=1).to_numpy()

        print(f"\n  --- {year} ---")
        for leg in CORRIDOR_TERMINUS:
            if leg not in sp.columns:
                continue
            s = sp[leg].to_numpy()
            imp = s[idx] > EQ_TOL
            # Demand-weighted congestion term the mechanism would have to remove.
            rent = float(np.average(np.maximum(s[idx], 0.0), weights=w[idx]))
            # The share of that rent sitting in hours where the export bound is
            # slack — i.e. unreachable by limb (a) by construction.
            unreachable = float(
                np.average(np.maximum(s[idx], 0.0) * imp, weights=w[idx])
            )
            print(
                f"      {leg:<10} defect-hour congestion rent ${rent:6.2f}/MWh; "
                f"${unreachable:6.2f} ({(unreachable / rent if rent else 0):.1%}) of it "
                f"sits in IMPORT-bound hours"
            )
        # Annual, demand-weighted, on the whole year — the C3a currency.
        for leg in CORRIDOR_TERMINUS:
            if leg not in sp.columns:
                continue
            s = sp[leg].to_numpy()
            ann = float(np.average(s, weights=w))
            print(
                f"      {leg:<10} ANNUAL demand-weighted spread ${ann:6.2f}/MWh   "
                f"(import-bound in {(s > EQ_TOL).mean():.3f} of all 8760 h)"
            )
        out[year] = {
            "ca_lambda_defect": float(np.average(ca_lam[idx], weights=w[idx])),
        }

    dsw25 = d2["rows"].get(2025, {}).get("WECC_DSW", {})
    imp_share = dsw25.get("import_bound", float("nan"))
    exp_share = dsw25.get("export_bound", float("nan"))
    ok = exp_share > imp_share
    print(
        "\n  >>> D3 verdict: the defect hours are "
        f"{imp_share:.1%} IMPORT-bound vs {exp_share:.1%} export-bound.\n"
        f"      Limb (a) export ceiling: {'reachable' if ok else 'INERT'} — it can only "
        "act where the export bound is active.\n"
        f"      Limb (b) export floor:   {'correct sign' if ok else 'WRONG SIGN'} — "
        "forcing export out of an import-bound zone widens the spread.\n"
        f"      -> D3 {'PASS' if ok else 'FAIL'}"
    )
    return {"rows": out, "pass": bool(ok)}


def section_e(years: tuple[int, ...]) -> dict:
    """E: where the corridor lane actually is — measured NET vs GROSS interchange.

    Forward-pointing measurement, filed as an observation and **not** as a
    recommendation (rule 1 ``[R-STRUCT]``: arming anything is a separate owner
    act). The model represents each corridor as ONE signed link carrying NET
    flow, and bounds it at the p95 of measured NET import. Reality moves power
    both ways within the same hour across the corridor's several DIBAs, so the
    measured net understates the gross import that physically flowed. This
    section sizes that gap per corridor-year straight from the committed
    EIA-930 BA-to-BA parquet — the same bytes
    :func:`measured_corridor_flow_envelope` reads.

    Sign convention is EIA-930's, as in the envelope builder: ``mw`` > 0 means
    CISO *exports* to the DIBA, so per-DIBA net import is ``-mw``.
    """
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.config.paths import RAW_DIR
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock

    print("\n" + "=" * 96)
    print("E — forward pointer: measured NET vs GROSS corridor interchange")
    print("=" * 96)
    print(
        "  The LP bounds ONE signed link at the p95 of measured NET import. Reality\n"
        "  imports on some DIBAs while exporting on others in the same hour, so gross\n"
        "  import exceeds net. OBSERVATION ONLY — nothing is proposed or armed here."
    )
    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        print("  (interchange parquet absent — section skipped)")
        return {}
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    frame = frame.assign(
        corridor=frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA),
        ts=local,
        yr=local.year,
    ).dropna(subset=["corridor"])
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    frame = frame.dropna(subset=["mw"])

    print(
        f"\n  {'year':>6} {'leg':<10} {'net imp':>9} {'gross imp':>10} "
        f"{'gross exp':>10} {'gross/net':>10} {'simul-h':>8}"
    )
    out = {}
    for year in years:
        f = frame[frame["yr"] == year]
        for leg in ("WECC_PNW", "WECC_DSW"):
            g = f[f["corridor"] == leg]
            if g.empty:
                continue
            per = g.groupby("ts")["mw"]
            net_imp = (-per.sum()).mean()
            gross_imp = per.apply(lambda s: np.maximum(-s, 0.0).sum()).mean()
            gross_exp = per.apply(lambda s: np.maximum(s, 0.0).sum()).mean()
            # Hours where the corridor imports on one DIBA and exports on another.
            simul = per.apply(lambda s: bool((s < 0).any() and (s > 0).any())).mean()
            ratio = gross_imp / net_imp if net_imp else float("nan")
            print(
                f"  {year:>6} {leg:<10} {net_imp:>9.0f} {gross_imp:>10.0f} "
                f"{gross_exp:>10.0f} {ratio:>10.2f} {simul:>8.3f}"
            )
            out[(year, leg)] = {
                "net_import_mw": float(net_imp),
                "gross_import_mw": float(gross_imp),
                "gross_export_mw": float(gross_exp),
                "simultaneous_share": float(simul),
            }
    print(
        "\n  Read: 'gross/net' is how much the single-signed-link NET representation\n"
        "  compresses the corridor's real gross import; 'simul-h' is the share of hours\n"
        "  the corridor moves power BOTH ways at once — flow the net link cannot hold."
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(int(y) for y in args.years)

    print("caiso-132 — ASK A1 derive-first gates (D1/D2/D3). NO LP, NOTHING ARMED.")
    print(f"bundle: {args.bundle}   years: {years}")

    d0 = section_d0(args.bundle, years)
    d1 = section_d1(years)
    d2 = section_d2(args.bundle, years, d1)
    d3 = section_d3(args.bundle, years, d2)
    section_e(years)

    print("\n" + "=" * 96)
    print("SUMMARY — ASK A1 admissibility")
    print("=" * 96)
    print(
        f"  D0 (scope): export bound active in {d0['export_bound_hours']} of "
        f"{d0['corridor_hours']} corridor-hours"
    )
    for name, r in (("D1", d1), ("D2", d2), ("D3", d3)):
        print(f"  {name}: {'PASS' if r['pass'] else 'FAIL'}")
    allpass = all(r["pass"] for r in (d1, d2, d3))
    print(
        f"\n  A1 is {'ADMISSIBLE — proceed to prereg + A/B' if allpass else 'KILLED at the derive gate; no solve is authorized'}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
