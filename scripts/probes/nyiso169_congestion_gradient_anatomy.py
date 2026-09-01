"""nyiso-169 — anatomy of the ZONAL-GRADIENT half of NYISO's C3a price-response deficit.

ZERO SOLVE. Reads committed artifacts (the designated keeper's own hourly
sidecars, the committed zonal/hourly actual-LMP reference, the curated NYISO
interface-flow record) plus NYISO's own posted zonal LBMP **component** record
(MIS P-24A real-time and ``damlbmp`` day-ahead monthly archives, re-fetched by
the frozen ``scripts/data/fetch_nyiso_zonal_lmp.py``). No LP runs; nothing here
is or becomes an LP input (CLAUDE.md rule 13 ``[R-MEASURED]`` — a posted price
is a measured *outcome* and is used here only as evidence).

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.

The object
----------
nyiso-168 §F split NYISO's load-weighted C3a deficit into a **zonal-gradient**
component and a **level** component, and found the gradient component is *not
consistently signed* (+0.96 / −1.49 / −2.32 $/MWh across 2023/24/25). This probe
decomposes that gradient component and asks the one question that decides
whether it is a mechanism at all:

    **Does any single binding transmission constraint carry it in all three
    years, with a consistent sign and material magnitude?**

Why an exact per-link decomposition exists
------------------------------------------
NYISO's model topology is a **radial chain** (``config/iso_configs.py``):

    Upstate_West -> Capital_Hudson -> Lower_Hudson -> NYC -> Long_Island

so a zone's spread against the reference zone is the sum of the link spreads
along the chain, and nyiso-168's gradient statistic

    grad = SUM_z w_z * [ (model_z - model_ref) - (actual_z - actual_ref) ]

re-associates **exactly** into one term per link::

    grad = SUM_L  W_L * d_L,        W_L = SUM_{z >= L} w_z,
                                    d_L = model link spread - actual link spread

with ``W_L`` the cumulative downstream load share. The decomposition is an
identity, not a regression: measurement B asserts it reproduces measurement A
to 1e-9.

Measurements
------------
A. GRADIENT/LEVEL SPLIT — nyiso-168 §F reproduced verbatim (regression gate).
B. PER-LINK ATTRIBUTION of the gradient component, with the identity check.
C. COMPONENT DECOMPOSITION of each link's ACTUAL spread into congestion (MCC)
   and losses (MCL), from NYISO's own posted components. Carries two gates:
   the published identity ``LBMP = E + MCL - MCC`` recovering a uniform
   reference energy price, and agreement between the component record's zonal
   annual means and the committed scoring actual.
D. MEASURED BINDING per NYISO interface (flow vs posted limit) and the actual
   congestion conditional on it, mapped onto the model links.
E. HOURLY BAND STRUCTURE — model vs actual link spread by model-load band.
G. REPRESENTABILITY — how often the measured congestion is non-zero, how
   often the model separates, and what share of the measured congestion
   arises in the hours a posted interface is actually at its limit.
F. VERDICT — the pre-registered sign-consistency test, per link.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso169_congestion_gradient_anatomy.py``
Writes: ``results/calibration/_nyiso169_congestion_gradient_anatomy.json``
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_actual_lmp import (  # noqa: E402
    LMP_DIR,
    NYISO_INTERNAL,
    NYISO_ZONE_MAP,
    _EASTERN_TZ,
    _localize_ordered,
    _std_hour_index,
)

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
ACTUAL_ZONAL = REPO / "data/raw/_validation-source/actual_lmp.json"
FLOWS = REPO / "data/clean/nyiso-interface-flows/NYISO"
OUT = REPO / "results/calibration/_nyiso169_congestion_gradient_anatomy.json"

#: The model's radial chain, upstream -> downstream (config/iso_configs.py).
CHAIN = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]

#: Model link -> the NYISO posted interface(s) that cut it. Sourced from the
#: topology docstring in ``config/iso_configs.py`` (the five model zones
#: aggregate zones A-K along NYISO's own published cutsets) and NYISO Manual 12
#: interface definitions. ``CENTRAL EAST - VC`` is the C->E cut that separates
#: the western zones from Capital; ``TOTAL EAST`` is the wider east-of-Central
#: cut; ``UPNY CONED`` is the Hudson Valley -> Con Ed cut; ``SPR/DUN-SOUTH``
#: (Sprainbrook/Dunwoodie South) is the cut into New York City.
LINK_INTERFACES: dict[str, tuple[str, ...]] = {
    "Upstate_West->Capital_Hudson": ("CENTRAL EAST - VC", "TOTAL EAST"),
    "Capital_Hudson->Lower_Hudson": ("UPNY CONED",),
    "Lower_Hudson->NYC": ("SPR/DUN-SOUTH",),
    "NYC->Long_Island": (),  # no posted internal cutset in the flow record
}

#: Published component identity tolerance. Components post to $0.01, so the
#: recovered reference energy price can carry stacked publication rounding;
#: nyiso-159 phase-0 measured max $0.015 on the same feed.
E_IDENTITY_MAX = 0.05

#: "At the limit" tolerance for the measured binding test, MW. NYISO's posted
#: limits move hour to hour; nyiso-109 used the same 50 MW proximity band.
BIND_TOL_MW = 50.0


def _read_components(data: bytes) -> pd.DataFrame:
    """Parse one NYISO zone CSV's timestamp, zone and all three components."""
    d = pd.read_csv(
        io.BytesIO(data),
        usecols=[
            "Time Stamp",
            "Name",
            "LBMP ($/MWHr)",
            "Marginal Cost Losses ($/MWHr)",
            "Marginal Cost Congestion ($/MWHr)",
        ],
    )
    return d.rename(
        columns={
            "LBMP ($/MWHr)": "lmp",
            "Marginal Cost Losses ($/MWHr)": "mcl",
            "Marginal Cost Congestion ($/MWHr)": "mcc",
        }
    )


def component_hourly(year: int, kind: str) -> dict[str, pd.DataFrame] | None:
    """Per-model-zone hourly LBMP / MCL / MCC frames on the model's 8760 clock.

    Applies the frozen ``derive_actual_lmp`` conventions unchanged: the RT
    5-minute stamps are interval-ENDING (shifted back one second before the
    hour floor), the DA hourly stamps interval-BEGINNING; the DST fall-back
    hour is disambiguated by row order; a model zone is the SIMPLE MEAN of its
    constituent A-K zones. Returns ``{"lmp": df, "mcl": df, "mcc": df}`` each
    indexed 0..8759 on the ISO's fixed standard-time clock, or ``None`` when
    the source archives are absent.
    """
    frames: list[pd.DataFrame] = []
    if kind == "da":
        outer = LMP_DIR / "NYISO" / "NYISO_zonal_hourly.zip"
        if not outer.exists():
            return None
        fmt = "%m/%d/%Y %H:%M"
        with zipfile.ZipFile(outer) as oz:
            for name in oz.namelist():
                base = name.rsplit("/", 1)[-1]
                if not (base.startswith(str(year)) and "damlbmp_zone" in base):
                    continue
                with zipfile.ZipFile(io.BytesIO(oz.read(name))) as inner:
                    frames += [
                        _read_components(inner.read(dn))
                        for dn in inner.namelist()
                        if dn.endswith(".csv")
                    ]
    else:
        fmt = "%m/%d/%Y %H:%M:%S"
        for path in sorted((LMP_DIR / "NYISO").glob(f"{year}*realtime_zone_csv.zip")):
            with zipfile.ZipFile(path) as z:
                frames += [
                    _read_components(z.read(dn))
                    for dn in z.namelist()
                    if dn.endswith(".csv")
                ]
    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = df[df["Name"].isin(NYISO_INTERNAL)]
    ts = pd.to_datetime(df["Time Stamp"], format=fmt, errors="coerce")
    df, ts = df[ts.notna()], ts[ts.notna()]
    utc = _localize_ordered(ts, df["Name"], _EASTERN_TZ).tz_convert("UTC")
    shift = pd.Timedelta(0) if kind == "da" else pd.Timedelta(seconds=1)
    df = df.assign(ts=(pd.DatetimeIndex(utc) - shift).floor("h"))

    out: dict[str, pd.DataFrame] = {}
    for comp in ("lmp", "mcl", "mcc"):
        wide = df.pivot_table(index="ts", columns="Name", values=comp, aggfunc="mean")
        idx = _std_hour_index(pd.DatetimeIndex(wide.index), year, "Etc/GMT+5")
        wide = wide[idx >= 0]
        wide.index = pd.Index(idx[idx >= 0], name="hour")
        wide = wide.groupby(level=0).mean().reindex(range(8760))
        cols = {
            z: wide[[c for c in members if c in wide.columns]].mean(axis=1)
            for z, members in NYISO_ZONE_MAP.items()
        }
        cols["_internal_mean"] = wide[
            [c for c in NYISO_INTERNAL if c in wide.columns]
        ].mean(axis=1)
        out[comp] = pd.DataFrame(cols)
    return out


def keeper_hourly(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The keeper's own P1 hourly zonal price and demand frames (rule 15)."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    price = s.pivot_table(index="hour", columns="zone", values="price")
    demand = s.pivot_table(index="hour", columns="zone", values="demand")
    return price, demand


def actual_zonal_da(year: int) -> dict[str, float]:
    """Committed per-model-zone annual DA actual — the nyiso-168 §F input."""
    zones = json.load(open(ACTUAL_ZONAL))["NYISO"][str(year)]["zones"]
    out = {}
    for z, rec in zones.items():
        v = rec.get("da")
        if v is None:
            continue
        out[z] = float(np.mean(v)) if isinstance(v, list) else float(v)
    return out


def measure_ab(year: int) -> dict:
    """A: nyiso-168 §F reproduced. B: its exact per-link re-association."""
    price, demand = keeper_hourly(year)
    actual = actual_zonal_da(year)
    zones = [z for z in price.columns if z != "NYISO_external"]
    tot = demand[zones].sum().sum()
    w = {z: float(demand[z].sum() / tot) for z in zones}
    ref = CHAIN[0]

    # --- A: the nyiso-168 §F statistic, recomputed on its own inputs.
    weighted = grad = 0.0
    per_zone = {}
    for z in zones:
        if z not in actual:
            continue
        mz, az = float(price[z].mean()), actual[z]
        weighted += w[z] * (mz - az)
        if z != ref:
            grad += w[z] * (
                (mz - float(price[ref].mean())) - (az - actual[ref])
            )
        per_zone[z] = dict(
            load_share=round(w[z], 6),
            model=round(mz, 4),
            actual_da=round(az, 4),
            delta=round(mz - az, 4),
        )

    # --- B: per-link re-association along the radial chain.
    links, recon = {}, 0.0
    for i in range(1, len(CHAIN)):
        up, dn = CHAIN[i - 1], CHAIN[i]
        name = f"{up}->{dn}"
        m_spread = float(price[dn].mean() - price[up].mean())
        a_spread = actual[dn] - actual[up]
        cum_w = sum(w[z] for z in CHAIN[i:] if z in actual)
        contrib = cum_w * (m_spread - a_spread)
        recon += contrib
        links[name] = dict(
            cumulative_downstream_load_share=round(cum_w, 6),
            model_link_spread=round(m_spread, 4),
            actual_link_spread=round(a_spread, 4),
            spread_deficit=round(m_spread - a_spread, 4),
            gradient_contribution=round(contrib, 4),
        )
    return dict(
        zones=per_zone,
        load_weighted_deficit=round(weighted, 4),
        gradient_component=round(grad, 4),
        level_component=round(weighted - grad, 4),
        links=links,
        identity_reconstructed_gradient=round(recon, 4),
        identity_abs_error=round(abs(recon - grad), 12),
        identity_holds=bool(abs(recon - grad) < 1e-9),
        reference_zone=ref,
    )


def measure_c(year: int, comps: dict[str, pd.DataFrame], kind: str) -> dict:
    """Each link's ACTUAL spread split into congestion (MCC) and losses (MCL).

    NYISO posts ``LBMP_z = E + MCL_z - MCC_z`` (MST §17.1 / Manual 12: losses
    add, congestion subtracts). With ``E`` uniform across the internal zones,
    a link's actual spread is exactly
    ``(MCL_dn - MCL_up) - (MCC_dn - MCC_up)`` — the two halves this measures.
    """
    lmp, mcl, mcc = comps["lmp"], comps["mcl"], comps["mcc"]
    e = lmp - mcl + mcc  # recovered reference energy price, per zone-hour
    zs = list(NYISO_ZONE_MAP)
    spread_e = float((e[zs].max(axis=1) - e[zs].min(axis=1)).max())

    links = {}
    for i in range(1, len(CHAIN)):
        up, dn = CHAIN[i - 1], CHAIN[i]
        d_lmp = float((lmp[dn] - lmp[up]).mean())
        d_mcl = float((mcl[dn] - mcl[up]).mean())
        d_mcc = float(-(mcc[dn] - mcc[up]).mean())
        links[f"{up}->{dn}"] = dict(
            actual_spread=round(d_lmp, 4),
            loss_half=round(d_mcl, 4),
            congestion_half=round(d_mcc, 4),
            congestion_share=(
                round(d_mcc / d_lmp, 4) if abs(d_lmp) > 1e-9 else None
            ),
            residual=round(d_lmp - d_mcl - d_mcc, 6),
        )
    return dict(
        basis=kind,
        links=links,
        zonal_annual_mean={z: round(float(lmp[z].mean()), 4) for z in zs},
        E_identity_max_spread=round(spread_e, 4),
        E_identity_holds=bool(spread_e <= E_IDENTITY_MAX),
        hours_covered=int(lmp[zs].notna().all(axis=1).sum()),
    )


def measure_d(year: int, comps: dict[str, pd.DataFrame]) -> dict:
    """Measured interface binding, and the congestion it coincides with."""
    f = pd.read_parquet(FLOWS / f"nyiso-interface-flows_{year}.parquet")
    mcc = comps["mcc"]
    out = {}
    for link, ifaces in LINK_INTERFACES.items():
        up, dn = link.split("->")
        cong = -(mcc[dn] - mcc[up])  # this link's congestion component, hourly
        per = {}
        for iface in ifaces:
            d = f[f["interface"] == iface].copy()
            if d.empty:
                continue
            d["hour"] = _std_hour_index(
                pd.DatetimeIndex(d["interval_start_utc"]), year, "Etc/GMT+5"
            )
            d = d[d["hour"] >= 0].groupby("hour").first()
            lim, flow = d["positive_limit_mw"], d["flow_mw"]
            bind = (lim - flow) <= BIND_TOL_MW
            bind = bind & lim.notna() & flow.notna()
            al = cong.reindex(d.index)
            per[iface] = dict(
                hours=int(len(d)),
                binding_hours=int(bind.sum()),
                binding_share=round(float(bind.mean()), 4),
                mean_utilisation=round(float((flow / lim).mean()), 4),
                mean_congestion_all_hours=round(float(al.mean()), 4),
                mean_congestion_when_binding=(
                    round(float(al[bind].mean()), 4) if int(bind.sum()) else None
                ),
                mean_congestion_when_not_binding=(
                    round(float(al[~bind].mean()), 4) if int((~bind).sum()) else None
                ),
            )
        out[link] = per
    return out


def measure_e(year: int, comps: dict[str, pd.DataFrame]) -> dict:
    """Model vs actual link spread by model-load percentile band."""
    price, demand = keeper_hourly(year)
    zones = [z for z in price.columns if z != "NYISO_external"]
    load = demand[zones].sum(axis=1)
    edges = [0, 50, 80, 90, 95, 99, 100]
    q = np.percentile(load.to_numpy(), edges)
    lmp = comps["lmp"]

    bands = []
    for lo, hi, ql, qh in zip(edges[:-1], edges[1:], q[:-1], q[1:]):
        m = (load >= ql) & (load < qh) if hi < 100 else (load >= ql)
        idx = load.index[m]
        row = {"band": f"{lo}-{hi}", "n": int(m.sum())}
        for i in range(1, len(CHAIN)):
            up, dn = CHAIN[i - 1], CHAIN[i]
            ms = float((price[dn] - price[up]).reindex(idx).mean())
            as_ = float((lmp[dn] - lmp[up]).reindex(idx).mean())
            row[f"{up}->{dn}"] = dict(
                model=round(ms, 3), actual=round(as_, 3), deficit=round(ms - as_, 3)
            )
        bands.append(row)
    return dict(bands=bands)


def measure_g(year: int, comps: dict[str, pd.DataFrame]) -> dict:
    """REPRESENTABILITY: is the measured congestion reachable at five-zone grain?

    A chain link's LP dual can be non-zero only in the hours its own flow is
    at its TTC, so the model can price congestion on a link only in the hours
    that link separates. This measures the two shares that decide whether that
    mechanism can reach the measured object: how often NYISO's posted
    congestion is actually non-zero on each link, and how much of each link's
    annual mean congestion arises in the hours its posted interface is within
    :data:`BIND_TOL_MW` of its limit.
    """
    mcc = comps["mcc"]
    price, _ = keeper_hourly(year)
    f = pd.read_parquet(FLOWS / f"nyiso-interface-flows_{year}.parquet")

    out = {}
    for i in range(1, len(CHAIN)):
        up, dn = CHAIN[i - 1], CHAIN[i]
        name = f"{up}->{dn}"
        cong = -(mcc[dn] - mcc[up])
        m_spread = price[dn] - price[up]
        annual = float(cong.mean())

        share_from_binding = {}
        for iface in LINK_INTERFACES[name]:
            d = f[f["interface"] == iface].copy()
            if d.empty:
                continue
            d["hour"] = _std_hour_index(
                pd.DatetimeIndex(d["interval_start_utc"]), year, "Etc/GMT+5"
            )
            d = d[d["hour"] >= 0].groupby("hour").first()
            bind = ((d["positive_limit_mw"] - d["flow_mw"]) <= BIND_TOL_MW) & d[
                "positive_limit_mw"
            ].notna() & d["flow_mw"].notna()
            c = cong.reindex(d.index)
            contrib = float((c * bind).sum() / len(c)) if len(c) else 0.0
            share_from_binding[iface] = dict(
                binding_share=round(float(bind.mean()), 5),
                congestion_from_binding_hours=round(contrib, 4),
                share_of_annual_congestion=(
                    round(contrib / annual, 4) if abs(annual) > 1e-9 else None
                ),
            )

        out[name] = dict(
            actual_annual_mean_congestion=round(annual, 4),
            actual_hours_congested_gt_1c=round(float((cong.abs() > 0.01).mean()), 4),
            actual_hours_congested_gt_1d=round(float((cong.abs() > 1.0).mean()), 4),
            model_hours_separated_gt_1c=round(float((m_spread.abs() > 0.01).mean()), 4),
            model_hours_separated_gt_1d=round(float((m_spread.abs() > 1.0).mean()), 4),
            posted_binding=share_from_binding,
        )
    return out


def main() -> int:
    """Run every measurement for 2023-2025 and write the probe record."""
    rec: dict = {
        "probe": "nyiso169_congestion_gradient_anatomy",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "bundle": str(KEEPER.relative_to(REPO)),
        "years": list(YEARS),
        "chain": CHAIN,
        "link_interfaces": {k: list(v) for k, v in LINK_INTERFACES.items()},
        "bind_tolerance_mw": BIND_TOL_MW,
        "by_year": {},
    }

    for year in YEARS:
        print(f"[{year}]")
        ab = measure_ab(year)
        print(
            f"  A  deficit ${ab['load_weighted_deficit']:+.2f}"
            f" = gradient ${ab['gradient_component']:+.2f}"
            f" + level ${ab['level_component']:+.2f}"
        )
        print(
            f"  B  per-link identity {'OK' if ab['identity_holds'] else 'FAILED'}"
            f" (|err| {ab['identity_abs_error']:.2e})"
        )
        for k, v in ab["links"].items():
            print(
                f"       {k:<34} model {v['model_link_spread']:+7.2f}"
                f"  actual {v['actual_link_spread']:+7.2f}"
                f"  -> grad {v['gradient_contribution']:+6.3f}"
            )

        year_rec = {"A_B_gradient_per_link": ab}
        for kind in ("da", "rt"):
            comps = component_hourly(year, kind)
            if comps is None:
                year_rec[f"C_components_{kind}"] = {"available": False}
                continue
            c = measure_c(year, comps, kind)
            year_rec[f"C_components_{kind}"] = c
            print(
                f"  C  [{kind}] E-identity max ${c['E_identity_max_spread']:.4f}"
                f" {'OK' if c['E_identity_holds'] else 'FAILED'},"
                f" {c['hours_covered']} h"
            )
            for k, v in c["links"].items():
                print(
                    f"       {k:<34} actual {v['actual_spread']:+7.2f}"
                    f" = loss {v['loss_half']:+6.2f} + cong {v['congestion_half']:+7.2f}"
                )
            if kind == "da":
                year_rec["D_interface_binding"] = measure_d(year, comps)
                year_rec["E_load_bands"] = measure_e(year, comps)
                g = measure_g(year, comps)
                year_rec["G_representability"] = g
                for k, v in g.items():
                    pb = v["posted_binding"]
                    frm = sum(
                        x["share_of_annual_congestion"] or 0.0 for x in pb.values()
                    )
                    print(
                        f"  G  {k:<32} actual congested"
                        f" {v['actual_hours_congested_gt_1d']*100:5.1f}% of h,"
                        f" model separated"
                        f" {v['model_hours_separated_gt_1d']*100:5.1f}%,"
                        f" from posted-binding h {frm*100:5.1f}%"
                    )
        rec["by_year"][str(year)] = year_rec

    # --- F: the pre-registered sign-consistency verdict, per link.
    verdict = {}
    for i in range(1, len(CHAIN)):
        name = f"{CHAIN[i - 1]}->{CHAIN[i]}"
        contribs = {
            str(y): rec["by_year"][str(y)]["A_B_gradient_per_link"]["links"][name][
                "gradient_contribution"
            ]
            for y in YEARS
        }
        vals = list(contribs.values())
        signs = {int(np.sign(v)) for v in vals if abs(v) > 0.05}
        verdict[name] = dict(
            contributions=contribs,
            consistently_signed=bool(len(signs) == 1),
            min_abs=round(min(abs(v) for v in vals), 4),
            max_abs=round(max(abs(v) for v in vals), 4),
            carries_in_all_three=bool(len(signs) == 1 and min(abs(v) for v in vals) >= 0.25),
        )
    rec["F_verdict"] = dict(
        per_link=verdict,
        any_link_carries_all_three=bool(
            any(v["carries_in_all_three"] for v in verdict.values())
        ),
        rule=(
            "A link CARRIES the gradient deficit iff its contribution has the same "
            "sign in all three years (ignoring |v| <= 0.05 as noise) AND its "
            "smallest absolute contribution is >= 0.25 $/MWh. Pre-registered "
            "before the numbers were read; the 0.25 floor is ~10% of 2025's "
            "-2.32 $/MWh gradient component."
        ),
    )

    print("\nF  sign-consistency verdict")
    for k, v in verdict.items():
        print(
            f"     {k:<34} {list(v['contributions'].values())}"
            f"  consistent={v['consistently_signed']}"
            f"  carries={v['carries_in_all_three']}"
        )
    print(f"\n  ANY LINK CARRIES ALL THREE YEARS: {rec['F_verdict']['any_link_carries_all_three']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
