"""nwpp-46 phase 0 (ZERO LP): does NWPP's OWN coal meter a RISING incremental cost?

The decisive measurement for C4. NWPP-45 ruled C4's amplitude defect IN on the
coal offer stack's vertical extent, and ``_nwpp46_coal_stack_phase0.py`` then
measured that NWPP's coal bands are the IDENTITY -- ``econlo == econhi ==
peak`` to the cent at every one of the 17 plants, because ``backcast_config``
deep-merges ``_SPP_OFFER_CURVE`` (1.0 on every band) for NWPP.

That identity is a DECLARED POSTURE, not a measurement (lane NWPP-20, seeded
before any NWPP solve existed, to avoid transplanting ERCOT's fitted bands
under rule 25 ``[R-ISO-SCOPE]``). This probe asks whether NWPP's own CEMS
record agrees with it, reproducing the WP-3 construction of
``scripts/data/derive_campd_marginal_hr.py`` BAND FOR BAND -- same steady-state
screen, same LSL/HSL percentiles, same band edges, same normalized-quadratic
input-output fit -- and differing in exactly two declared ways:

  (1) the class map is resolved from NWPP's OWN rebuilt fleet rather than from
      ``bin_assignments_NWPP.csv``, which does not exist for NWPP (owner ruling
      N8; established by NWPP-43); and
  (2) it reports PER PLANT as well as per class, because a class mean cannot
      tell a fleet that is uniformly flat from one where a few plants are
      steeply sloped and the rest are flat.

The load-bearing output is ``marg_econ_high / marg_econ_low`` -- the measured
rise in incremental heat rate across a unit's economic range. It is a RATIO of
two quantities sharing the same base, so it is basis-independent: whatever HR
normalization is chosen cancels. A ratio at 1.0 says the identity posture is
physically right and C4's amplitude must be sought elsewhere; a ratio above 1.0
says the identity understates the real stack's vertical extent, by that much.

NO RESIDUAL IS READ ANYWHERE IN THIS FILE (rules 1 / 13).

Run: ``PYTHONPATH=.:src python3 scripts/probes/_nwpp46_marginal_hr_phase0.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.campd import states_for_iso  # noqa: E402

BUNDLE = Path("results/calibration/nwpp44_takeorpay_reg")
UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"
YEARS = (2023, 2024, 2025)

# Every constant below is COPIED from scripts/data/derive_campd_marginal_hr.py
# so the construction is the ISOs' shared one, not a new one (rule 19).
LSL_PCT, HSL_PCT = 3.0, 97.0
MIN_UNIT_HOURS = 200
HR_LO, HR_HI = 3.0, 60.0
PCTS = (0.25, 0.50, 0.75)


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Weighted quantile via the cumulative-weight CDF (deriver verbatim)."""
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return float(np.interp(q, cw, v))


def derive_unit_bands(u: pd.DataFrame, base_hr: float) -> dict[str, float] | None:
    """Per-unit band multipliers — ``derive_campd_marginal_hr`` verbatim."""
    gl = u["grossLoad"].to_numpy(float)
    hi = u["heatInput"].to_numpy(float)
    hr = u["hr"].to_numpy(float)
    if len(gl) < MIN_UNIT_HOURS:
        return None
    lsl = float(np.percentile(gl, LSL_PCT))
    hsl = float(np.percentile(gl, HSL_PCT))
    if hsl <= lsl:
        return None
    rng = hsl - lsl
    rel = np.clip((gl - lsl) / rng, 0.0, 1.0)

    comm_a, lo_a, hi_a = hr[gl <= lsl * 1.05], hr[rel <= 0.33], hr[rel >= 0.67]
    avg = {
        "committed": float(np.median(comm_a)) / base_hr if len(comm_a) > 5 else np.nan,
        "econ_low": float(np.median(lo_a)) / base_hr if len(lo_a) > 5 else np.nan,
        "econ_high": float(np.median(hi_a)) / base_hr if len(hi_a) > 5 else np.nan,
    }
    marg = {"committed": np.nan, "econ_low": np.nan, "econ_high": np.nan,
            "peak": np.nan}
    try:
        x = (gl - lsl) / rng
        c2, c1, _c0 = np.polyfit(x, hi, 2)
        # The PEAK band extends the SAME fit to the top of the measured
        # operating range (x = 1.0, i.e. HSL). The deriver stops at 0.9 because
        # its tuning targets are gas classes whose peak band is duct firing --
        # a different physical object. A coal unit has no duct burner, so its
        # peak band IS the top of its own I/O curve and needs no new scalar.
        for b, xpos in (("committed", 0.0), ("econ_low", 0.5),
                        ("econ_high", 0.9), ("peak", 1.0)):
            m = float((c1 + 2.0 * c2 * xpos) / rng) / base_hr
            marg[b] = m if 0 < m < 5 else np.nan
    except (np.linalg.LinAlgError, ValueError):
        pass
    return {
        "cap": hsl,
        "lsl": lsl,
        "hsl": hsl,
        "hours": len(gl),
        "avg_committed": avg["committed"],
        "avg_econ_low": avg["econ_low"],
        "avg_econ_high": avg["econ_high"],
        "marg_committed": marg["committed"],
        "marg_econ_low": marg["econ_low"],
        "marg_econ_high": marg["econ_high"],
        "marg_peak": marg["peak"],
    }


def coal_plant_codes() -> dict[int, str]:
    """NWPP's coal plant codes and LP class, from the keeper's own fleet."""
    import scripts.run_calibration as RC
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, 2023))
    out = RC.run_year(2023, meta["iso"], 8760, meta.get("gas_price"), {},
                      fleet_only=True, **kw)
    fa = out["fleet_arrays"]
    codes: dict[int, str] = {}
    for uid, grp in zip(fa.unit_ids, np.asarray(fa.plant_group)):
        g = str(grp)
        if not g.startswith("COAL"):
            continue
        stem = str(uid).rpartition("_")[0]          # COAL_<ZONE>_p<code>
        tok = stem.rpartition("_p")[2]
        if tok.isdigit():
            codes[int(tok)] = g
    return codes


def load_campd(codes: set[int]) -> pd.DataFrame:
    """Steady-state CEMS operating hours for NWPP's coal plants (deriver screen)."""
    cols = ["facilityId", "unitId", "grossLoad", "heatInput", "opTime",
            "unitType", "primaryFuelInfo"]
    frames = []
    for st in states_for_iso("NWPP"):
        for y in YEARS:
            p = UNIT_LEVEL_DIR / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            df = pd.read_parquet(p, columns=cols)
            df = df[df["facilityId"].astype(int).isin(codes)]
            if not df.empty:
                df["year"] = y
                frames.append(df)
    camp = pd.concat(frames, ignore_index=True)
    camp["facilityId"] = camp["facilityId"].astype(int)
    # NWPP-42's declared departure: fuel identification reads primaryFuelInfo,
    # because at Jim Bridger / Naughton / North Valmy the coal units and the
    # gas-converted units are BOTH boilers.
    camp = camp[camp["primaryFuelInfo"].astype(str).str.contains("Coal", case=False,
                                                                na=False)].copy()
    op = (camp["grossLoad"] > 0) & (camp["heatInput"] > 0) & (camp["opTime"] >= 0.95)
    camp = camp[op].copy()
    camp["hr"] = camp["heatInput"] / camp["grossLoad"]
    return camp[(camp["hr"] >= HR_LO) & (camp["hr"] <= HR_HI)].copy()


def main() -> None:
    codes = coal_plant_codes()
    print(f"NWPP coal plant codes from the keeper fleet: {len(codes)}")
    camp = load_campd(set(codes))
    print(f"steady-state coal unit-hours {len(camp):,} over {YEARS}\n")

    rows = []
    for (fid, uid), u in camp.groupby(["facilityId", "unitId"]):
        # Per-unit OWN-HR basis: the unit's own cap-weighted average heat rate.
        # A ratio of two bands is basis-independent, so this choice cannot move
        # the load-bearing econ_high/econ_low number.
        own = float(np.median(u["hr"]))
        b = derive_unit_bands(u, own)
        if b is None:
            continue
        b.update({"plant": fid, "unit": uid, "klass": codes.get(fid, "?"),
                  "own_hr": own})
        rows.append(b)
    per = pd.DataFrame(rows)

    print(f"{'plant':>7} {'unit':<8}{'klass':<10}{'MW':>8}{'hrs':>7}{'ownHR':>7}"
          f"{'m_com':>7}{'m_elo':>7}{'m_ehi':>7}{'ehi/elo':>9}{'a_com':>7}{'a_ehi':>7}")
    for _, r in per.sort_values(["plant", "unit"]).iterrows():
        ratio = r["marg_econ_high"] / r["marg_econ_low"] if r["marg_econ_low"] > 0 else np.nan
        print(f"{int(r['plant']):>7} {str(r['unit'])[:7]:<8}{r['klass']:<10}"
              f"{r['cap']:>8.0f}{int(r['hours']):>7}{r['own_hr']:>7.2f}"
              f"{r['marg_committed']:>7.3f}{r['marg_econ_low']:>7.3f}"
              f"{r['marg_econ_high']:>7.3f}{ratio:>9.3f}"
              f"{r['avg_committed']:>7.3f}{r['avg_econ_high']:>7.3f}")

    print(f"\n{'=' * 96}\nCAP-WEIGHTED BAND MULTIPLIERS (own-HR basis), per LP class\n{'=' * 96}")
    print(f"{'class':<10}{'units':>6}{'MW':>10}" + "".join(
        f"{c:>12}" for c in ("marg_com", "marg_elo", "marg_ehi", "marg_peak",
                             "ehi/elo", "avg_com", "avg_ehi")))
    for klass, d in list(per.groupby("klass")) + [("** ALL COAL **", per)]:
        w = d["cap"].to_numpy(float)
        cells = []
        for col in ("marg_committed", "marg_econ_low", "marg_econ_high",
                    "marg_peak"):
            v = d[col].to_numpy(float)
            m = np.isfinite(v) & (v > 0)
            cells.append(_wquantile(v[m], w[m], 0.50) if m.any() else np.nan)
        ratio = cells[2] / cells[1] if cells[1] and np.isfinite(cells[1]) else np.nan
        acells = []
        for col in ("avg_committed", "avg_econ_high"):
            v = d[col].to_numpy(float)
            m = np.isfinite(v) & (v > 0)
            acells.append(_wquantile(v[m], w[m], 0.50) if m.any() else np.nan)
        print(f"{klass:<10}{len(d):>6}{w.sum():>10,.0f}" +
              "".join(f"{x:>12.3f}" for x in cells + [ratio] + acells))

    v = per["marg_econ_high"].to_numpy(float) / per["marg_econ_low"].to_numpy(float)
    w = per["cap"].to_numpy(float)
    m = np.isfinite(v) & (v > 0)
    print(f"\nFLEET ehi/elo ratio  p25 {_wquantile(v[m], w[m], 0.25):.3f} "
          f" p50 {_wquantile(v[m], w[m], 0.50):.3f} "
          f" p75 {_wquantile(v[m], w[m], 0.75):.3f}   "
          f"(units above 1.05: {int((v[m] > 1.05).sum())}/{int(m.sum())})")


if __name__ == "__main__":
    main()
