"""xiso-1 audit: is diurnal price-amplitude compression NEISO-specific or systemic?

neiso-74 measured NEISO's keeper reproducing only **24-30 %** of the measured
diurnal price amplitude while its *level* and its *phase* are both right
(`results/calibration/FINDING-neiso74-ps-cycling-price-shape-2026-08-01.md`).
Two other ISOs already carry a same-shaped finding reached by different routes —
miso-89 ("the model reproduces 29-47 % of the observed diurnal spread, every
season, every year") and pjm-139/140/141 ("31 / 33 / 32 % of the measured
overnight->evening-peak swing"). Nobody has ever measured all six ISOs with ONE
construction, so nobody knows whether this is three ISO-specific defects or one
systemic property of the LP.

This probe answers exactly that question and nothing else. It is an **audit**,
not a mechanism: it reads each ISO's CURRENT keeper hourly sidecars and its own
committed measured hub price, and reports. No LP is solved, no config is
changed, no parameter is proposed.

Admissibility (stated up front, per the session brief):

  * **Model side** — ``hourly/system_<year>.parquet`` from each ISO's keeper
    bundle, ``pass == "P1"`` (rule: P1 is THE scored run). The ``price`` column
    is the delivered model price: ``run_calibration_full._system_frame`` writes
    ``prices[z] + total_overlay``, so any ERCOT RTORDPA / DAM-AS / ORDC adder is
    ALREADY inside it and the audit-only ``*_overlay`` columns must not be
    re-added. The system price is the zone dual vector load-weighted by the
    model's own hourly zonal demand — the same basis C3a is scored on.
  * **Measured side** — ``data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet``,
    the committed hub-mean hourly DA/RT series that ``scripts/data/derive_actual_lmp.py``
    writes on the model's CHRONOLOGICAL 8760-hour calendar (row k = the k-th UTC
    hour after local-standard-time midnight Jan 1, local-standard Feb 29
    dropped). Model and measured therefore pair hour-for-hour with no re-keying,
    which is what makes the construction portable across six ISOs.
  * **Basis caveat, measured not assumed** — the model side is load-weighted
    across zones, the measured side is a hub mean. Section 3 re-runs the model
    amplitude on a SIMPLE zone mean so the reader can see the compression is not
    a weighting artifact.
  * **Rule 25 [R-ISO-SCOPE]** — every number is reported per ISO. A compression
    ratio measured in one ISO is never another ISO's verdict; the cross-ISO
    table answers "is the defect shared", not "does ISO X inherit ISO Y's
    number".

Reported statistics, per ISO x year x series:

  * level (mean $/MWh) — the thing C3a already gates;
  * mean daily MAX / mean daily MIN / mean daily spread (max-min), plus the
    MEDIAN daily spread and a $200-body-censored daily spread, so the headline
    cannot be a scarcity-tail artifact (miso-89's censoring convention);
  * the hour-of-day mean profile: its range, its peak hour and its trough hour
    (the phase test), and its correlation with the measured profile;
  * days clearing the 1/RTE = 1.25x round-trip arbitrage hurdle.

The headline is the **amplitude ratio** — model hour-of-day range divided by
measured — which is the statistic neiso-74 sized at 24-30 % and pjm-141 at
31-33 %.

Section 4 ports neiso-74 section 8's attribution to all six ISOs: which classes absorb
the model's own diurnal demand swing, and which of them are ALREADY ONLINE at
the overnight trough (so the same offer band is marginal at both ends of the day
and the clearing price cannot move).

Read-only over 2023-2025 (rule 20 ``[R-HOLDOUT]``: no out-of-training year is
touched). No LP solve, no bundle written, no dashboard registration.

Run:  uv run python scripts/probes/_xiso1_diurnal_amplitude_audit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
KEEPER_DIR = REPO / "frontend/data/backcast/keepers"
REGISTRY_DIR = REPO / "frontend/data/backcast/registry"
ACTUAL_DIR = REPO / "data/raw/_validation-source"
# Round-trip hurdle for the "is there a day's worth of arbitrage here" count.
# Same 0.80 RTE the storage block carries (constants.PUMPED_STORAGE_RTE); it is
# used here only as a fixed yardstick, never as a fitted quantity.
RTE_HURDLE = 1.0 / 0.80
BODY_CENSOR = 200.0  # miso-89's body-censoring convention, $/MWh


def hdr(text: str) -> None:
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}")


# --------------------------------------------------------------- keeper lookup
def keepers() -> dict[str, tuple[str, Path]]:
    """Map ISO -> (keeper run id, bundle path), read from the live keeper store.

    Reads ``frontend/data/backcast/keepers/<ISO>.json`` (the per-ISO promotion
    lane) and resolves the bundle through the run's registry sidecar, so the
    audit re-runs against whatever each ISO's keeper is at HEAD rather than a
    hard-coded path.
    """
    out: dict[str, tuple[str, Path]] = {}
    order = json.loads((KEEPER_DIR / "index.json").read_text())["isos"]
    for iso in order:
        shard = KEEPER_DIR / f"{iso}.json"
        if not shard.exists():
            continue
        kid = json.loads(shard.read_text()).get("keeper")
        if not kid:
            continue
        reg = REGISTRY_DIR / f"{kid}.json"
        if not reg.exists():
            continue
        bundle = json.loads(reg.read_text()).get("bundle")
        if not bundle:
            continue
        out[iso] = (kid, REPO / bundle)
    return out


# ------------------------------------------------------------------ price load
def model_price(bundle: Path, year: int, weighted: bool = True) -> np.ndarray | None:
    """Model P1 system price, dense on the chronological 8760 calendar.

    ``weighted`` selects the C3a basis (zonal duals weighted by the model's own
    hourly zonal demand); ``False`` gives the simple zone mean, the control for
    the load-weighting basis caveat.
    """
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p, columns=["pass", "zone", "hour", "price", "demand"])
    d = df[df["pass"] == "P1"]
    if d.empty:
        return None
    if weighted:
        num = d["price"].to_numpy(float) * np.maximum(d["demand"].to_numpy(float), 0.0)
        den = np.maximum(d["demand"].to_numpy(float), 0.0)
        h = d["hour"].to_numpy(int)
        T = int(h.max()) + 1
        n = np.bincount(h, weights=num, minlength=T)
        w = np.bincount(h, weights=den, minlength=T)
        # A zero-demand hour (no ISO has one, but do not divide by zero) falls
        # back to the simple zone mean.
        simple = np.bincount(h, weights=d["price"].to_numpy(float), minlength=T)
        cnt = np.maximum(np.bincount(h, minlength=T), 1)
        out = np.where(w > 0, n / np.maximum(w, 1e-9), simple / cnt)
    else:
        g = d.groupby("hour")["price"].mean().sort_index()
        out = g.to_numpy(float)
    return out[:8760] if out.size >= 8760 else None


def measured_price(iso: str, year: int, kind: str) -> np.ndarray | None:
    """Committed hub-mean hourly actual (``da``/``rt``), same 8760 calendar."""
    p = ACTUAL_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    d = df[df["year"].astype(int) == year]
    if d.empty or kind not in d.columns:
        return None
    d = d.sort_values("hour")
    arr = pd.to_numeric(d[kind], errors="coerce").to_numpy(float)
    return arr[:8760] if arr.size >= 8760 else None


# ------------------------------------------------------------------- statistics
def stats(price: np.ndarray) -> dict:
    """Level / daily-envelope / hour-of-day statistics for one price vector.

    Days carrying any missing hour are dropped from the daily statistics (and
    counted), so a partial measured year (CAISO 2023 DA) reports on its covered
    days instead of silently propagating NaN.
    """
    d = price[: 365 * 24].reshape(365, 24)
    ok = ~np.isnan(d).any(axis=1)
    dd = d[ok]
    hi, lo = dd.max(axis=1), dd.min(axis=1)
    cen = np.minimum(dd, BODY_CENSOR)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(lo > 0.01, hi / lo, np.inf)
    hod = np.nanmean(d, axis=0)
    return {
        "days": int(ok.sum()),
        "mean": float(np.nanmean(price)),
        "daily_max": float(hi.mean()),
        "daily_min": float(lo.mean()),
        "daily_spread": float((hi - lo).mean()),
        "daily_spread_med": float(np.median(hi - lo)),
        "daily_spread_cen": float((cen.max(axis=1) - cen.min(axis=1)).mean()),
        "ratio_p50": float(np.nanmedian(ratio[np.isfinite(ratio)])),
        "days_over_hurdle": int((ratio > RTE_HURDLE).sum()),
        "hod": hod,
        "hod_range": float(np.nanmax(hod) - np.nanmin(hod)),
        "hod_peak": int(np.nanargmax(hod)),
        "hod_trough": int(np.nanargmin(hod)),
    }


def pct(a: float, b: float) -> float:
    return 100.0 * (a / b - 1.0) if b not in (0.0, None) else float("nan")


def main() -> int:
    hdr("xiso-1 — cross-ISO diurnal price-amplitude audit (six ISOs, no LP)")
    ks = keepers()
    print("keepers audited (live keeper store at HEAD):")
    for iso, (kid, b) in ks.items():
        print(f"  {iso:<6} {kid:<44} {b.relative_to(REPO)}")
    print(
        f"\nmeasured side: data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet"
        f"  (hub-mean DA/RT, model's chronological 8760 calendar)"
        f"\nbody censor ${BODY_CENSOR:.0f}/MWh (miso-89 convention); arbitrage hurdle "
        f"{RTE_HURDLE:.2f}x"
    )

    # ------------------------------------------------------------------ table 1
    hdr("1. per-ISO diurnal amplitude — model P1 vs measured DA and RT")
    rows: list[dict] = []
    for iso, (_kid, bundle) in ks.items():
        for year in YEARS:
            pm = model_price(bundle, year)
            if pm is None:
                print(f"  {iso} {year}: no model system hourly")
                continue
            sm = stats(pm)
            print(
                f"\n  {iso} {year}  model P1   level ${sm['mean']:7.2f}   "
                f"daily max ${sm['daily_max']:7.2f}  min ${sm['daily_min']:7.2f}  "
                f"spread ${sm['daily_spread']:7.2f} (med ${sm['daily_spread_med']:6.2f}, "
                f"cen ${sm['daily_spread_cen']:6.2f})"
            )
            print(
                f"  {' ' * len(iso)}       hod range ${sm['hod_range']:6.2f}  "
                f"peak h{sm['hod_peak']:02d} trough h{sm['hod_trough']:02d}  "
                f"ratio p50 {sm['ratio_p50']:5.2f}  days>hurdle "
                f"{sm['days_over_hurdle']:3d}/{sm['days']}"
            )
            for kind in ("da", "rt"):
                pa = measured_price(iso, year, kind)
                if pa is None:
                    print(f"  {iso} {year} measured {kind.upper()}: not committed")
                    continue
                sa = stats(pa)
                corr = float(np.corrcoef(sm["hod"], sa["hod"])[0, 1])
                amp = 100.0 * sm["hod_range"] / sa["hod_range"]
                spr = 100.0 * sm["daily_spread"] / sa["daily_spread"]
                spr_c = 100.0 * sm["daily_spread_cen"] / sa["daily_spread_cen"]
                print(
                    f"  {' ' * len(iso)}    vs {kind.upper()}  level "
                    f"${sa['mean']:7.2f} ({pct(sm['mean'], sa['mean']):+6.1f}%)   "
                    f"daily max ${sa['daily_max']:7.2f} "
                    f"({pct(sm['daily_max'], sa['daily_max']):+6.1f}%)  "
                    f"min ${sa['daily_min']:7.2f} "
                    f"({pct(sm['daily_min'], sa['daily_min']):+6.1f}%)"
                )
                print(
                    f"  {' ' * len(iso)}          hod range ${sa['hod_range']:6.2f} -> "
                    f"AMPLITUDE {amp:5.1f}%   daily spread ${sa['daily_spread']:7.2f} -> "
                    f"{spr:5.1f}% (censored {spr_c:5.1f}%)   peak h{sa['hod_peak']:02d} "
                    f"trough h{sa['hod_trough']:02d}  hod corr {corr:+.3f}  "
                    f"days>hurdle {sa['days_over_hurdle']:3d}/{sa['days']}"
                )
                rows.append(
                    {
                        "iso": iso,
                        "year": year,
                        "kind": kind,
                        "level_pct": pct(sm["mean"], sa["mean"]),
                        "max_pct": pct(sm["daily_max"], sa["daily_max"]),
                        "min_pct": pct(sm["daily_min"], sa["daily_min"]),
                        "amp_pct": amp,
                        "spread_pct": spr,
                        "spread_cen_pct": spr_c,
                        "corr": corr,
                        "peak_m": sm["hod_peak"],
                        "peak_a": sa["hod_peak"],
                        "trough_m": sm["hod_trough"],
                        "trough_a": sa["hod_trough"],
                        "days_m": sm["days_over_hurdle"],
                        "days_a": sa["days_over_hurdle"],
                        "days": sa["days"],
                    }
                )

    # ------------------------------------------------------------------ table 2
    hdr("2. THE ANSWER — amplitude as % of measured, six ISOs x three years")
    df = pd.DataFrame(rows)
    for kind in ("da", "rt"):
        sub = df[df["kind"] == kind]
        if sub.empty:
            continue
        print(
            f"\n  vs measured {kind.upper()}  (hour-of-day range, model as % of actual)"
        )
        print(f"  {'ISO':<6} " + "  ".join(f"{y:>7d}" for y in YEARS) + "     level %")
        for iso in ks:
            s = sub[sub["iso"] == iso].set_index("year")
            if s.empty:
                continue
            cells = "  ".join(
                f"{s.loc[y, 'amp_pct']:6.1f}%" if y in s.index else "      -"
                for y in YEARS
            )
            lv = "  ".join(
                f"{s.loc[y, 'level_pct']:+5.1f}" if y in s.index else "    -"
                for y in YEARS
            )
            print(f"  {iso:<6} {cells}   {lv}")
        print(
            f"  {'ALL':<6} mean amplitude {sub['amp_pct'].mean():5.1f}%   "
            f"min {sub['amp_pct'].min():5.1f}%   max {sub['amp_pct'].max():5.1f}%   "
            f"mean |level err| {sub['level_pct'].abs().mean():4.1f}%"
        )

    hdr("2b. phase — does the model put the peak and trough in the right hour?")
    print(
        f"  {'ISO':<6} {'year':<5} {'kind':<4}  peak model/actual   trough model/actual   hod corr"
    )
    for r in rows:
        pk = "OK " if abs(r["peak_m"] - r["peak_a"]) <= 1 else "OFF"
        tr = "OK " if abs(r["trough_m"] - r["trough_a"]) <= 1 else "OFF"
        print(
            f"  {r['iso']:<6} {r['year']:<5} {r['kind'].upper():<4}  "
            f"h{r['peak_m']:02d} / h{r['peak_a']:02d}  {pk}          "
            f"h{r['trough_m']:02d} / h{r['trough_a']:02d}  {tr}         {r['corr']:+.3f}"
        )

    # ------------------------------------------------------------------ table 3
    hdr("3. control — is the compression a load-weighting artifact? (simple zone mean)")
    print(f"  {'ISO':<6} {'year':<5}  hod range: load-wtd / simple-mean / measured DA")
    for iso, (_kid, bundle) in ks.items():
        for year in YEARS:
            pw = model_price(bundle, year, weighted=True)
            ps = model_price(bundle, year, weighted=False)
            pa = measured_price(iso, year, "da")
            if pw is None or ps is None:
                continue
            rw, rs = stats(pw)["hod_range"], stats(ps)["hod_range"]
            ra = stats(pa)["hod_range"] if pa is not None else float("nan")
            print(
                f"  {iso:<6} {year:<5}  ${rw:6.2f} / ${rs:6.2f} / ${ra:6.2f}   "
                f"amplitude load-wtd {100 * rw / ra:5.1f}%  simple {100 * rs / ra:5.1f}%"
            )

    # ----------------------------------------------------------------- table 3b
    hdr(
        "3b. control — is the MEASURED side understated by using a hub? (MISO, the only committed hourly zonal actual)"
    )
    zp = ACTUAL_DIR / "actual_lmp_hourly_zonal_MISO.parquet"
    if zp.exists():
        zdf = pd.read_parquet(zp)
        for year in YEARS:
            d = zdf[zdf["year"].astype(int) == year]
            if d.empty:
                continue
            wide = d.pivot_table(index="hour", columns="zone", values="da")
            # Reindex onto the dense 8760 grid: a zonal file may be short an
            # hour (2025 is 8759), and a missing hour must read as missing —
            # stats() drops the day it falls in, never silently shifts the clock.
            wide = wide.reindex(range(8760))
            zone_mean = wide.mean(axis=1).to_numpy(float)
            hub = measured_price("MISO", year, "da")
            pm = model_price(ks["MISO"][1], year)
            rz = stats(zone_mean)["hod_range"]
            rh = stats(hub)["hod_range"] if hub is not None else float("nan")
            rm = stats(pm)["hod_range"] if pm is not None else float("nan")
            print(
                f"  MISO {year}  measured hod range: hub-mean ${rh:6.2f} / "
                f"{wide.shape[1]}-zone mean ${rz:6.2f}   ->  model amplitude "
                f"vs hub {100 * rm / rh:5.1f}%  vs zone-mean {100 * rm / rz:5.1f}%"
            )
    else:
        print("  no committed hourly zonal actual")

    # ------------------------------------------------------------------ table 4
    hdr(
        "4. attribution — who absorbs the model's diurnal swing, and what is already online at the trough"
    )
    for iso, (_kid, bundle) in ks.items():
        cp = bundle / "hourly" / "class_hourly_2025.parquet"
        sp = bundle / "hourly" / "system_2025.parquet"
        if not (cp.exists() and sp.exists()):
            print(f"  {iso}: no 2025 class/system hourly")
            continue
        cd = pd.read_parquet(cp)
        cd = cd[cd["pass"] == "P1"].pivot(index="hour", columns="klass", values="mw")
        cd = cd.fillna(0.0)
        hod = cd.groupby(cd.index % 24).mean()
        sd = pd.read_parquet(sp)
        sd = sd[sd["pass"] == "P1"].groupby("hour")["demand"].sum().sort_index()
        dem = sd.groupby(sd.index % 24).mean()
        trough, peak = int(dem.idxmin()), int(dem.idxmax())
        swing = float(dem[peak] - dem[trough])
        print(
            f"\n  {iso} 2025: demand h{trough} {dem[trough]:,.0f} MW -> h{peak} "
            f"{dem[peak]:,.0f} MW  (swing {swing:,.0f} MW)"
        )
        delta = (hod.loc[peak] - hod.loc[trough]).sort_values(ascending=False)
        for k in list(delta.index[:5]) + list(delta.index[-2:]):
            lo, hi = float(hod.loc[trough, k]), float(hod.loc[peak, k])
            print(
                f"    {str(k):<14} h{trough:02d} {lo:9,.0f} MW -> h{peak:02d} {hi:9,.0f} MW  "
                f"({hi - lo:+8,.0f} MW, {100 * (hi - lo) / max(swing, 1):5.1f}% of swing; "
                f"online at trough: {'YES' if lo > 1.0 else 'no'})"
            )
        # The flat-margin signature: peaking classes already loaded overnight.
        peakers = [
            c
            for c in hod.columns
            if any(t in str(c).upper() for t in ("CT_", "PEAK", "OIL", "ST_GAS"))
        ]
        on = [c for c in peakers if float(hod.loc[trough, c]) > 1.0]
        tot = float(sum(hod.loc[trough, c] for c in on))
        print(
            f"    -> peaking/oil classes ONLINE at the overnight trough: "
            f"{len(on)}/{len(peakers)} ({', '.join(str(c) for c in on) or 'none'}) "
            f"carrying {tot:,.0f} MW"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
