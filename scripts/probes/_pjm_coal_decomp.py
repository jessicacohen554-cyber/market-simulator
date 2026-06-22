"""Probe #0 (no solve): decompose the PJM coal over-run — EXPORT vs DOMESTIC,
MARGINAL (price-setting) vs INFRAMARGINAL baseload.

Reads a solved keeper bundle's dispatch + system parquets (no LP re-solve) and
the dashboard payload's model/actual fuel totals, and answers the three
questions the coal-offer handoff (docs/multi-iso/pjm-coal-offer-handoff-2026-06.md)
says decide lever A (export seam) vs lever B (marginal coal offer):

  1. ENERGY BALANCE — is the coal/thermal over-generation leaving PJM as EXPORT
     or displacing DOMESTIC gas? Within the model, load is fixed, so
     Sum(Delta fuel TWh) == Delta net-export exactly (data-closure aside). If the
     thermal over == the export over, the lever is the seam; if coal is up while
     gas is down, coal is shuffling the domestic merit order.

  2. COAL TRANCHE SPLIT — is the over in the cheap base tranches (mustrun /
     committed, take-or-pay legitimate) or the marginal econ/peak tranches
     (no take-or-pay justification — lever B's target)? Split by the coal unit_id
     suffix (_mustrun/_committed/_econlo/_econhi/_econcNN/_peak).

  3. PRICE-SETTING — does fixing coal move the LMP? In an LP a PARTIALLY-LOADED
     tranche sits exactly at its marginal cost == the zonal energy dual, so coal
     is price-setting in a zone-hour iff a coal tranche is partially loaded that
     hour. Report the load-weighted share of hours where coal is marginal, the
     LMP in those hours, and whether the EXPORT-heavy hours are coal-marginal
     (the linked coal-cheap -> over-export + LMP-suppression story).

Tranche capacity is proxied by each unit-tranche's max MW over the year (these
are flat blocks; a tranche running below that max is partially loaded). This is
a diagnostic proxy, not a re-solve.

Usage: python scripts/probes/_pjm_coal_decomp.py <bundle> [<bundle> ...]
       [--years 2025] [--out FILE.md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_calibration_html import build_payload  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL")
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")

_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MSTART = tuple(int(sum(_DAYS[:m]) * 24) for m in range(13))
_MNAMES = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _month(hours: np.ndarray) -> np.ndarray:
    return np.searchsorted(_MSTART, hours, side="right").clip(1, 12)


def _tranche(uid: str) -> str:
    for suf in ("mustrun", "committed", "econlo", "econhi", "peak"):
        if uid.endswith("_" + suf):
            return suf
    if "_econc" in uid:
        return "econ-ramp"
    return "other"


def _payload_totals(bundle: str) -> dict:
    """Model + actual TWh by fuel/coal-class + net interchange, from the payload."""
    pay = build_payload([(bundle, ROOT / bundle)])
    run = pay["model"][0]["years"]
    bench = pay["bench"]
    out = {}
    for year, y in run.items():
        b = bench[year]
        fuels = {}
        for fr in y["fuelRows"]:
            fuels[fr["fuel"]] = (fr["m"], fr["b"])  # (model, actual) TWh
        coal = {}
        for cls in ("COAL_BIT", "COAL_PRB", "COAL_WC"):
            coal[cls] = (
                float(y["gmModel"].get(cls, 0.0)),
                float(b["classFull"].get(cls, 0.0)),
            )
        out[year] = {"fuels": fuels, "coal": coal}
    return out


def _analyze_year(disp: pd.DataFrame, year: int) -> dict:
    """Hourly export / coal-marginal analysis from one year's dispatch frame."""
    d = disp[disp["year"] == year]
    if "pass" in d.columns and (d["pass"] == "P1").any():
        d = d[d["pass"] == "P1"]
    T = int(d["hour"].max()) + 1

    # Net export (EIA-930 sign: export positive) = -(import-klass dispatch).
    imp = d[d["klass"] == "import"]
    net_exp = -(
        imp.groupby("hour")["mw"]
        .sum()
        .reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )  # MW per hour, positive = PJM exporting

    # Load-weighted system price per hour (demand-weighted zonal duals), built
    # from the dispatch frame's per-unit lmp via total generation as the weight
    # is unavailable here; use the simple per-hour mean of zonal duals weighted
    # by zonal dispatched MW.
    gen = d[(d["mw"] > 0) & (~d["klass"].isin(["import"]))]
    zh = gen.groupby(["zone", "hour"], observed=True).agg(
        mw=("mw", "sum"), lmp=("lmp", "first")
    )
    zh = zh.reset_index()
    pw = (
        zh.assign(pd_=zh["lmp"] * zh["mw"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), w=("mw", "sum"))
    )
    lmp_h = (pw["pd_"] / pw["w"]).reindex(range(T)).to_numpy(float)

    # Coal dispatch per hour + per tranche.
    coal = d[d["klass"].isin(COAL_CLASSES) & (d["mw"] != 0)].copy()
    coal["tr"] = coal["unit_id"].astype(str).map(_tranche)
    coal_h = (
        coal.groupby("hour")["mw"]
        .sum()
        .reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )
    tranche_twh = coal.groupby("tr")["mw"].sum() / 1e6

    # Marginality (price-setting), measured PER (zone, hour): in an LP a
    # partially-loaded tranche sits exactly at its marginal cost == the zonal
    # energy dual, so a fuel is price-setting in a zone-hour iff one of its
    # tranches is partially loaded there. cap = each unit-tranche's max MW over
    # the year (flat blocks). "coal SOLE" (coal partial, no gas partial in that
    # zone-hour) is where raising the coal offer lifts the LMP; where gas is
    # co-marginal it just refills at the same price (lever-B LMP-neutral).
    def _zone_marginal(sub: pd.DataFrame) -> pd.DataFrame:
        cap = sub.groupby("unit_id", observed=True)["mw"].transform("max")
        part = (sub["mw"] > 0.02 * cap) & (sub["mw"] < 0.98 * cap) & (cap > 1.0)
        return sub.loc[part, ["zone", "hour"]].drop_duplicates().assign(flag=True)

    coal_pos = d[d["klass"].isin(COAL_CLASSES) & (d["mw"] > 0)].copy()
    gas = d[d["klass"].isin(GAS_CLASSES) & (d["mw"] > 0)].copy()
    cm = _zone_marginal(coal_pos).rename(columns={"flag": "c"})
    gm = _zone_marginal(gas).rename(columns={"flag": "g"})
    # Zonal weight = total dispatched gen per zone-hour (load proxy).
    zw = (
        gen.groupby(["zone", "hour"], observed=True)["mw"]
        .sum()
        .rename("w")
        .reset_index()
    )
    zh_marg = zw.merge(cm, on=["zone", "hour"], how="left").merge(
        gm, on=["zone", "hour"], how="left"
    )
    zh_marg["c"] = zh_marg["c"].fillna(False)
    zh_marg["g"] = zh_marg["g"].fillna(False)

    # System-hour coal-marginal flag (any zone) for the export-hour cross-tab.
    coal_marg_hours = set(cm["hour"].unique())
    is_coal_marg = np.array([h in coal_marg_hours for h in range(T)])
    gas_marg_hours = set(gm["hour"].unique())
    is_gas_marg = np.array([h in gas_marg_hours for h in range(T)])

    return {
        "T": T,
        "net_exp": net_exp,
        "lmp_h": lmp_h,
        "coal_h": coal_h,
        "tranche_twh": tranche_twh,
        "zh_marg": zh_marg,
        "is_coal_marg": is_coal_marg,
        "is_gas_marg": is_gas_marg,
    }


def _fmt(x, nd=2):
    return f"{x:,.{nd}f}" if x is not None and np.isfinite(x) else "—"


def report(bundles: list[str], years: list[int] | None) -> str:
    L: list[str] = ["# Probe #0 — PJM coal over-run decomposition", ""]
    for bundle in bundles:
        disp = pd.read_parquet(ROOT / bundle / "dispatch")
        tot = _payload_totals(bundle)
        yrs = sorted(tot) if not years else [y for y in sorted(tot) if y in years]
        L += [f"## {bundle}", ""]
        for year in yrs:
            a = _analyze_year(disp, year)
            f = tot[year]["fuels"]
            c = tot[year]["coal"]
            T = a["T"]
            ne, lmp, coalh = a["net_exp"], a["lmp_h"], a["coal_h"]

            # --- 1. Energy balance: Delta fuel vs Delta net-export ---
            coal_m = sum(v[0] for v in c.values())
            coal_a = sum(v[1] for v in c.values())
            gas_m, gas_a = f.get("gas", (None, None))
            ix_m, ix_a = f.get("interchange", (None, None))
            dcoal = coal_m - coal_a
            dgas = (gas_m - gas_a) if gas_m is not None and gas_a is not None else None
            dix = (ix_m - ix_a) if ix_m is not None and ix_a is not None else None

            L += [f"### {year}", ""]
            L += ["**1. Energy balance (model − actual, TWh)**", ""]
            rows = [
                ["coal-tot", coal_m, coal_a, dcoal],
                ["gas", gas_m, gas_a, dgas],
                ["net-export", ix_m, ix_a, dix],
            ]
            for fl in ("nuclear", "wind", "solar"):
                if fl in f:
                    m, b = f[fl]
                    rows.append([fl, m, b, (m - b) if b is not None else None])
            L += ["| series | model | actual | Δ |", "|---|---|---|---|"]
            for nm, m, b, dd in rows:
                L.append(f"| {nm} | {_fmt(m)} | {_fmt(b)} | {_fmt(dd, 2)} |")
            if dgas is not None and dix is not None:
                thermal_over = dcoal + dgas
                L += [
                    "",
                    f"- thermal over (Δcoal+Δgas) = **{_fmt(thermal_over)}** TWh; "
                    f"export over (Δnet-export) = **{_fmt(dix)}** TWh.",
                    f"- export over / thermal over = "
                    f"**{_fmt(100 * dix / thermal_over if thermal_over else float('nan'), 0)}%** "
                    f"→ {'EXPORT-driven (lever A)' if dix > 0.6 * thermal_over else 'DOMESTIC merit shuffle (lever B)'} "
                    f"if Δgas≈0; if Δgas<0 coal is displacing domestic gas.",
                    "",
                ]

            # --- 2. Coal tranche split ---
            L += ["**2. Coal dispatch by tranche (model TWh)**", ""]
            tt = a["tranche_twh"].sort_values(ascending=False)
            base = float(tt.reindex(["mustrun", "committed"]).fillna(0).sum())
            marg = float(
                tt.reindex(["econlo", "econhi", "econ-ramp", "peak"]).fillna(0).sum()
            )
            L += ["| tranche | TWh |", "|---|---|"]
            for tr, v in tt.items():
                L.append(f"| {tr} | {_fmt(float(v))} |")
            L += [
                "",
                f"- base (mustrun+committed) = **{_fmt(base)}** TWh; "
                f"marginal (econ/peak) = **{_fmt(marg)}** TWh "
                f"({_fmt(100 * marg / (base + marg) if base + marg else 0, 0)}% marginal).",
                "",
            ]

            # --- 3. Price-setting (per zone-hour, load-weighted) ---
            zm = a["zh_marg"]
            W = float(zm["w"].sum())
            sh = lambda mask: 100 * float(zm.loc[mask, "w"].sum()) / W  # noqa: E731
            c, g = zm["c"].to_numpy(bool), zm["g"].to_numpy(bool)
            cm, gm = a["is_coal_marg"], a["is_gas_marg"]
            ok = np.isfinite(lmp)
            thr = np.nanpercentile(ne, 66.7)
            exp_hi = (ne >= thr) & ok
            L += [
                "**3. Price-setting (load-wtd zone-hours; partial-load ⇒ marginal)**",
                "",
            ]
            L += [
                f"- coal price-setting (some coal tranche partial): "
                f"**{_fmt(sh(c), 1)}%**; gas **{_fmt(sh(g), 1)}%**.",
                f"- **coal SOLE** (coal partial, gas NOT — raising coal lifts LMP): "
                f"**{_fmt(sh(c & ~g), 1)}%**; gas SOLE **{_fmt(sh(g & ~c), 1)}%**; "
                f"both co-marginal **{_fmt(sh(c & g), 1)}%**; neither "
                f"**{_fmt(sh(~c & ~g), 1)}%**.",
                f"- mean LMP — all hours **{_fmt(np.nanmean(lmp[ok]))}**; "
                f"coal-marginal hrs **{_fmt(np.nanmean(lmp[cm & ok]))}**; "
                f"gas-marginal hrs **{_fmt(np.nanmean(lmp[gm & ok]))}**.",
                f"- net export — mean **{_fmt(np.nanmean(ne))}** MW; top-tercile "
                f"threshold **{_fmt(thr)}** MW.",
                f"- in export-heavy (top-tercile) hours: mean LMP "
                f"**{_fmt(np.nanmean(lmp[exp_hi]))}**, mean coal MW "
                f"**{_fmt(np.nanmean(coalh[exp_hi]))}**.",
                f"- corr(hourly coal MW, net export) = "
                f"**{_fmt(np.corrcoef(coalh[ok], ne[ok])[0, 1], 2)}**; "
                f"corr(coal MW, LMP) = **{_fmt(np.corrcoef(coalh[ok], lmp[ok])[0, 1], 2)}**.",
                "",
            ]

            # Monthly net-export over.
            mon = _month(np.arange(T))
            L += ["**Net export by month (model MW mean)**", ""]
            L += ["| " + " | ".join(_MNAMES) + " |", "|" + "---|" * 12]
            mvals = [np.nanmean(ne[mon == m]) for m in range(1, 13)]
            L.append("| " + " | ".join(_fmt(v, 0) for v in mvals) + " |")
            L += [""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    md = report(args.bundles, args.years)
    if args.out:
        args.out.write_text(md)
        print(f"wrote {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
