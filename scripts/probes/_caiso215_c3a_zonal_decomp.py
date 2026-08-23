"""caiso-215 (owner charter "caiso-214", 2026-08-22) — C3a 2024/2025 overrun
ZONAL decomposition on the caiso-200 keeper (`2026-08-17-caiso-200-h1-memberpanel`).
NO LP, NO SOLVE — committed bytes only.

The one axis caiso-202 never cut: every §A-§C number there is a CA-wide
aggregate (`_caiso202_c3a_decomp.ca_lambda` demand-weights the five CA zones
into one scalar and drops the WECC corridor zones). This probe re-slices the
SAME committed bytes per zone, per hub, and per seam:

* **Z0 — controls.** (i) The CA-wide §A gap re-printed through the imported
  caiso-202 machinery (proves same data, same weights). (ii) The committed
  scalar actual (`actual_lmp_hourly_CAISO.parquet`) re-derived from the raw
  per-hub RTM CSVs with the deriver's own hub weights — proves the per-hub
  actual series this probe scores against are the committed scalar's own
  constituents on the committed hour clock.
* **Z1 — per-zone C3a** (charter cut a): per zone-year, zone-demand-weighted
  model λ vs the zone's actual trading-hub RT LMP, each zone's share of the
  ISO gap, 2023 control column, plus the weight-reconciliation bridge
  (rubric-weight vs realised-weight vs hub-collapse terms).
* **Z2 — per-zone × actual-RT price bucket** (cut b): the caiso-202 §B table
  re-cut per zone on identical bucket edges.
* **Z3 — the WECC seam** (cut c): corridor-zone λ vs attached CA zone λ —
  separation level (loss surface + adders) vs separation EXCESS (candidate
  binding), overlap with overrun hours, model corridor λ vs measured
  MALIN/PALOVRDE hub actuals. Sidecars carry no duals/flows, so binding state
  is inferred from λ separation only (stated honestly).
* **Z4 — congestion split** (cut d): gap_z = common (system-energy) term +
  zonal-spread mismatch term, model spread vs actual hub spread vs the RTM
  CSVs' own measured MCC congestion component.
* **Z5 — per-zone × month** (cut e) + the DLAP DA pocket cross-check
  (2024/2025 only — no RT DLAP exists in the committed record; SP15-pocket RT
  resolution is impossible from committed bytes).

Actual-side zone resolution is the CAISO market's own: three trading hubs.
NP15 -> TH_NP15, ZP26 -> TH_ZP26, and the three SP15-split zones (LA_BASIN,
SDGE, SP15_rest — the caiso-172/LCT split of old SP15) all score against
TH_SP15; DLAP_SCE-APND / DLAP_SDGE-APND give pocket-level DA actuals for
2024/2025.

Writes `results/calibration/_caiso215_c3a_zonal_decomp.json` (deterministic:
sorted keys, rounded floats, no timestamps).

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso215_c3a_zonal_decomp.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso202_c3a_decomp as c202  # noqa: E402  (same-dir committed probe)

YEARS = (2023, 2024, 2025)
HOURS = 8760
LMP_DIR = REPO / "data/raw/lmp-data/CAISO"
INTERTIE = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"
OUT_JSON = REPO / "results/calibration/_caiso215_c3a_zonal_decomp.json"

# The committed scalar actual's own hub-collapse weights
# (scripts/data/derive_actual_lmp.py CAISO_HUB_WEIGHTS — the pre-caiso-172
# NP15/ZP26 split and the pre-SP15-split SP15 total). Used ONLY to re-derive
# the committed scalar as a control; never as a model input.
HUB_W = {"TH_NP15_GEN-APND": 0.3969, "TH_ZP26_GEN-APND": 0.0646, "TH_SP15_GEN-APND": 0.5385}
HUBS = tuple(HUB_W)

# Model zone -> actual trading hub (config/iso_configs.py _caiso_config: the
# three SP15-split zones are the caiso-172/LCT partition of old SP15).
ZONE_HUB = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "LA_BASIN": "TH_SP15_GEN-APND",
    "SDGE": "TH_SP15_GEN-APND",
    "SP15_rest": "TH_SP15_GEN-APND",
}
CA_ZONES = tuple(ZONE_HUB)
# Corridor zone -> (attached CA zone, actual intertie hub) — per-hub intertie
# split (model/interchange/caiso.py _CAISO_CORRIDOR_LINK_TO).
SEAM = {"WECC_PNW": ("NP15", "MALIN"), "WECC_DSW": ("SP15_rest", "PALOVRDE")}

DLAP_ZONE = {"DLAP_SCE-APND": "LA_BASIN", "DLAP_SDGE-APND": "SDGE"}

BUCKET_EDGES = [-1e9, 0, 10, 20, 30, 40, 60, 100, 1e9]  # == caiso-202 §B edges
BUCKET_NAMES = ["<0", "0-10", "10-20", "20-30", "30-40", "40-60", "60-100", ">100"]


def local_hour_index(year: int) -> pd.DatetimeIndex:
    """The committed 8760 hour clock: local-standard PST (Etc/GMT+8, no DST),
    local Feb 29 dropped — mirrors derive_actual_lmp.py / c202.month_of_hour."""
    stamps = pd.date_range(f"{year}-01-01", periods=HOURS + 24, freq="h", tz="Etc/GMT+8")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps


def load_market_csv(market: str, year: int, nodes: tuple) -> pd.DataFrame:
    """Hourly per-node frame (8760 × node) of LMP plus components from the raw
    committed CSVs, on the committed hour clock. Missing hours stay NaN."""
    df = pd.read_csv(LMP_DIR / f"CAISO_{market}_hourly_{year}.csv")
    df = df[df["node"].isin(nodes)].copy()
    ts = pd.to_datetime(df["interval_start_gmt"], utc=True).dt.tz_convert("Etc/GMT+8")
    idx = local_hour_index(year)
    pos = pd.Series(np.arange(HOURS), index=idx)
    df["hour"] = pos.reindex(ts).to_numpy()  # NaN for Feb-29 / out-of-clock rows
    df = df.dropna(subset=["hour"])
    df["hour"] = df["hour"].astype(int)
    out = {}
    for col in ("LMP", "MCC", "MCE", "MCL"):
        out[col] = df.pivot_table(index="hour", columns="node", values=col).reindex(range(HOURS))
    return out


def wmean(x: np.ndarray, w: np.ndarray, ok: np.ndarray) -> float:
    return float(np.sum(x[ok] * w[ok]) / np.sum(w[ok]))


def r4(x) -> float:
    return round(float(x), 4)


def zone_frames(year: int):
    sc = c202.sidecars(year)
    lam = {z: sc["price"][z].to_numpy() for z in sc["price"].columns}
    dem = {z: sc["demand"][z].to_numpy() for z in sc["demand"].columns}
    return sc, lam, dem


def main() -> None:
    results = {"session": "caiso-215", "bundle": c202.BUNDLE.name, "years": {}}
    for year in YEARS:
        print("=" * 78)
        print(f"YEAR {year}")
        print("=" * 78)
        sc, lam, dem = zone_frames(year)
        act = c202.actuals(year)
        rt_scalar = act["rt"].to_numpy()
        rtm = load_market_csv("rtm", year, HUBS)
        hub_lmp = rtm["LMP"]
        yr = {}

        # ---- Z0 controls -------------------------------------------------
        w_rub = c202.rubric_weights(year)
        lam_ca = c202.ca_lambda(sc)
        ok_sc = ~np.isnan(rt_scalar)
        g_rub = wmean(lam_ca, w_rub, ok_sc) - wmean(rt_scalar, w_rub, ok_sc)
        m_rub = wmean(lam_ca, w_rub, ok_sc)
        a_rub = wmean(rt_scalar, w_rub, ok_sc)
        print(f"[Z0.i] CA-wide control (caiso-202 §A machinery): model {m_rub:7.2f}  "
              f"actual RT {a_rub:7.2f}  gap {g_rub:+6.2f} ({g_rub / a_rub * 100:+5.1f}%)")

        # committed scalar re-derived from the raw per-hub CSVs
        collapse = sum(HUB_W[h] * hub_lmp[h].to_numpy() for h in HUBS)
        both = ok_sc & ~np.isnan(collapse)
        maxdiff = float(np.nanmax(np.abs(collapse[both] - rt_scalar[both]))) if both.any() else float("nan")
        nan_mismatch = int(np.sum(ok_sc != ~np.isnan(collapse)))
        print(f"[Z0.ii] hub-collapse check: max |rederived - committed| = {maxdiff:.4g} "
              f"over {int(both.sum())} h; NaN-mask mismatch {nan_mismatch} h")
        yr["control"] = {"model_lw": r4(m_rub), "act_rt_lw": r4(a_rub), "gap": r4(g_rub),
                         "gap_pct": r4(g_rub / a_rub * 100)}
        yr["collapse_check"] = {"max_abs_diff": r4(maxdiff), "nan_mismatch_hours": nan_mismatch,
                                "common_hours": int(both.sum())}

        # ---- Z1 per-zone C3a --------------------------------------------
        # Per zone: zone-demand-weighted model λ vs the zone's own hub actual.
        # Common mask per zone: hub present. Contribution shares use zone
        # demand MWh so the rows sum to the realised-weight per-hub ISO gap.
        print(f"\n[Z1] per-zone C3a (model λ_z vs hub RT actual, zone-demand-weighted)  year {year}")
        print(f"  {'zone':10s} {'hub':8s} {'dTWh':>6s} {'dshare':>6s} {'model':>7s} {'actual':>7s} "
              f"{'gap$':>7s} {'gap%':>6s} {'share%':>7s}")
        num = {}
        den_zone = {}
        for z in CA_ZONES:
            a_h = hub_lmp[ZONE_HUB[z]].to_numpy()
            ok = ~np.isnan(a_h)
            num[z] = float(np.sum(dem[z][ok] * (lam[z][ok] - a_h[ok])))
            den_zone[z] = float(np.sum(dem[z][ok]))
        den = sum(den_zone.values())
        g_perhub = sum(num.values()) / den
        yr["per_zone"] = {}
        for z in CA_ZONES:
            a_h = hub_lmp[ZONE_HUB[z]].to_numpy()
            ok = ~np.isnan(a_h)
            m_z = wmean(lam[z], dem[z], ok)
            a_z = wmean(a_h, dem[z], ok)
            dtwh = float(np.sum(dem[z])) / 1e6
            share = num[z] / sum(num.values()) * 100
            print(f"  {z:10s} {ZONE_HUB[z][3:7]:8s} {dtwh:6.2f} {den_zone[z] / den:6.3f} "
                  f"{m_z:7.2f} {a_z:7.2f} {m_z - a_z:+7.2f} {(m_z - a_z) / a_z * 100:+5.1f}% {share:6.1f}%")
            yr["per_zone"][z] = {"hub": ZONE_HUB[z], "demand_twh": r4(dtwh),
                                 "demand_share": r4(den_zone[z] / den), "model": r4(m_z),
                                 "actual": r4(a_z), "gap": r4(m_z - a_z),
                                 "gap_pct": r4((m_z - a_z) / a_z * 100),
                                 "share_of_iso_gap_pct": r4(share)}
        # SP15 composite row (the 3 pockets against their single hub)
        sp = ("LA_BASIN", "SDGE", "SP15_rest")
        a_h = hub_lmp["TH_SP15_GEN-APND"].to_numpy()
        ok = ~np.isnan(a_h)
        d_sp = sum(dem[z] for z in sp)
        lam_sp = sum(lam[z] * dem[z] for z in sp) / d_sp
        m_c, a_c = wmean(lam_sp, d_sp, ok), wmean(a_h, d_sp, ok)
        print(f"  {'SP15(all3)':10s} {'SP15':8s} {np.sum(d_sp) / 1e6:6.2f} {'':6s} "
              f"{m_c:7.2f} {a_c:7.2f} {m_c - a_c:+7.2f} {(m_c - a_c) / a_c * 100:+5.1f}%")
        yr["per_zone"]["SP15_composite"] = {"hub": "TH_SP15_GEN-APND", "model": r4(m_c),
                                            "actual": r4(a_c), "gap": r4(m_c - a_c),
                                            "gap_pct": r4((m_c - a_c) / a_c * 100)}

        # reconciliation bridge: scored construction -> per-hub construction
        d_ca = sum(dem[z] for z in CA_ZONES)
        g_real_scalar = wmean(lam_ca, d_ca, ok_sc) - wmean(rt_scalar, d_ca, ok_sc)
        print(f"  bridge: rubric-w scalar-act gap {g_rub:+.2f} | realised-w scalar-act {g_real_scalar:+.2f} "
              f"| realised-w per-hub-act {g_perhub:+.2f}")
        print(f"          weight-vector term {g_real_scalar - g_rub:+.3f}; hub-collapse term "
              f"{g_perhub - g_real_scalar:+.3f}")
        yr["bridge"] = {"gap_rubric_scalar": r4(g_rub), "gap_realised_scalar": r4(g_real_scalar),
                        "gap_realised_perhub": r4(g_perhub),
                        "weight_vector_term": r4(g_real_scalar - g_rub),
                        "hub_collapse_term": r4(g_perhub - g_real_scalar)}

        # ---- Z2 per-zone × actual-RT price bucket ------------------------
        print(f"\n[Z2] per-zone × actual-RT-price bucket: hours / (model−actual) $ per bucket")
        hdr = "  " + f"{'bucket':>7s}" + "".join(f" | {z:>16s}" for z in CA_ZONES)
        print(hdr)
        yr["buckets"] = {z: {} for z in CA_ZONES}
        for lo, hi, name in zip(BUCKET_EDGES[:-1], BUCKET_EDGES[1:], BUCKET_NAMES):
            row = f"  {name:>7s}"
            for z in CA_ZONES:
                a_h = hub_lmp[ZONE_HUB[z]].to_numpy()
                ok = ~np.isnan(a_h)
                m = ok & (a_h >= lo) & (a_h < hi)
                if m.sum() == 0:
                    row += f" | {'—':>16s}"
                    yr["buckets"][z][name] = {"hours": 0}
                    continue
                d_z = dem[z]
                am = wmean(a_h, d_z, m)
                mm = wmean(lam[z], d_z, m)
                contrib = float(np.sum(d_z[m] * (lam[z][m] - a_h[m]))) / den_zone[z]
                row += f" | {int(m.sum()):4d}h {mm - am:+7.1f}"
                yr["buckets"][z][name] = {"hours": int(m.sum()), "act_mean": r4(am),
                                          "mod_mean": r4(mm), "delta": r4(mm - am),
                                          "contrib": r4(contrib)}
            print(row)

        # ---- Z3 the WECC seam -------------------------------------------
        print(f"\n[Z3] WECC seam (per-hub intertie corridor zones; no duals in sidecars — "
              f"λ-separation inference)")
        it = pd.read_parquet(INTERTIE)
        it = it[it["year"] == year].pivot_table(index="hour", columns="hub", values="price").reindex(range(HOURS))
        # CA-wide positive-gap mask on the caiso-202 construction
        gap_h = np.where(ok_sc, w_rub * (lam_ca - np.where(ok_sc, rt_scalar, 0.0)), 0.0)
        pos = gap_h > 0
        yr["seam"] = {}
        for cz, (az, ihub) in SEAM.items():
            d = lam[az] - lam[cz]
            med = float(np.median(d))
            exc = d > med + 1.0
            excess_hours = int(exc.sum())
            ov = int((exc & pos).sum())
            act_h = it[ihub].to_numpy() if ihub in it.columns else np.full(HOURS, np.nan)
            okh = ~np.isnan(act_h)
            corr = float(np.corrcoef(lam[cz][okh], act_h[okh])[0, 1]) if okh.sum() > 100 else float("nan")
            print(f"  {cz:9s} λmean {np.mean(lam[cz]):6.2f} vs {az} {np.mean(lam[az]):6.2f} | "
                  f"Δ med {med:+5.2f} p95 {np.percentile(d, 95):+6.2f} max {np.max(d):+7.2f} | "
                  f"Δ>med+$1: {excess_hours}h (∩pos-gap {ov}h) | vs {ihub} actual: "
                  f"model−act mean {np.mean(lam[cz][okh] - act_h[okh]):+6.2f}, corr {corr:.3f}")
            yr["seam"][cz] = {"attached_zone": az, "lambda_mean": r4(np.mean(lam[cz])),
                              "attached_lambda_mean": r4(np.mean(lam[az])),
                              "sep_median": r4(med), "sep_p95": r4(np.percentile(d, 95)),
                              "sep_max": r4(np.max(d)), "excess_hours_gt_med_plus_1": excess_hours,
                              "excess_and_posgap_hours": ov, "intertie_hub": ihub,
                              "model_minus_actual_hub_mean": r4(np.mean(lam[cz][okh] - act_h[okh])),
                              "corr_vs_actual_hub": r4(corr) if corr == corr else None,
                              "posgap_hours_total": int(pos.sum())}

        # ---- Z4 congestion split ----------------------------------------
        # gap_z = (λ_ref − act_ref)  [common system term]
        #       + (λ_z − λ_ref) − (act_hub − act_ref)  [zonal-spread mismatch]
        print(f"\n[Z4] congestion split: gap_z = common + spread-mismatch  (refs: model=CA "
              f"demand-wtd λ, actual=committed hub-collapse scalar)")
        yr["congestion"] = {"per_zone": {}}
        common_terms = []
        print(f"  {'zone':10s} {'model_spread':>12s} {'act_spread':>10s} {'mismatch':>9s} "
              f"{'common':>7s} {'gap_z':>7s}")
        for z in CA_ZONES:
            a_h = hub_lmp[ZONE_HUB[z]].to_numpy()
            ok = ~np.isnan(a_h) & ok_sc
            ms = wmean(lam[z] - lam_ca, dem[z], ok)
            asp = wmean(a_h - rt_scalar, dem[z], ok)
            cm = wmean(lam_ca, dem[z], ok) - wmean(rt_scalar, dem[z], ok)
            gz = wmean(lam[z], dem[z], ok) - wmean(a_h, dem[z], ok)
            common_terms.append(cm)
            print(f"  {z:10s} {ms:+12.2f} {asp:+10.2f} {ms - asp:+9.2f} {cm:+7.2f} {gz:+7.2f}")
            yr["congestion"]["per_zone"][z] = {"model_spread": r4(ms), "actual_spread": r4(asp),
                                               "spread_mismatch": r4(ms - asp),
                                               "common_term": r4(cm), "gap_total": r4(gz)}
        # measured actual congestion component (MCC) per hub
        mcc = rtm["MCC"]
        yr["congestion"]["actual_mcc_mean"] = {}
        line = "  actual MCC mean by hub:"
        for h in HUBS:
            v = float(np.nanmean(mcc[h].to_numpy()))
            line += f"  {h[3:7]} {v:+5.2f}"
            yr["congestion"]["actual_mcc_mean"][h] = r4(v)
        print(line)

        # ---- Z5 per-zone × month ----------------------------------------
        mo = c202.month_of_hour(year)
        print(f"\n[Z5] per-zone monthly gap (model−hub actual, $/MWh, zone-demand-wtd)")
        print("  " + f"{'zone':10s}" + "".join(f" {m:>6d}" for m in range(1, 13)))
        yr["monthly"] = {}
        for z in CA_ZONES:
            a_h = hub_lmp[ZONE_HUB[z]].to_numpy()
            row = f"  {z:10s}"
            yr["monthly"][z] = {}
            for m in range(1, 13):
                ok = (~np.isnan(a_h)) & (mo == m)
                g = wmean(lam[z], dem[z], ok) - wmean(a_h, dem[z], ok) if ok.any() else float("nan")
                row += f" {g:+6.1f}"
                yr["monthly"][z][str(m)] = r4(g) if g == g else None
            print(row)

        # DLAP DA pocket cross-check (2024/2025 only; 2023 DLAP is a stub)
        if year >= 2024:
            dam = load_market_csv("dam", year, HUBS + tuple(DLAP_ZONE))
            da_lmp = dam["LMP"]
            print(f"\n[Z5b] pocket DA cross-check (model λ_z vs DLAP/hub DA)")
            yr["dlap_da"] = {}
            checks = [("LA_BASIN", "DLAP_SCE-APND"), ("SDGE", "DLAP_SDGE-APND"),
                      ("SP15_rest", "TH_SP15_GEN-APND"), ("NP15", "TH_NP15_GEN-APND"),
                      ("ZP26", "TH_ZP26_GEN-APND")]
            for z, node in checks:
                if node not in da_lmp.columns:
                    continue
                a_h = da_lmp[node].to_numpy()
                ok = ~np.isnan(a_h)
                m_z, a_z = wmean(lam[z], dem[z], ok), wmean(a_h, dem[z], ok)
                print(f"  {z:10s} vs {node:16s} ({int(ok.sum())}h): model {m_z:6.2f}  "
                      f"DA act {a_z:6.2f}  gap {m_z - a_z:+6.2f} ({(m_z - a_z) / a_z * 100:+5.1f}%)")
                yr["dlap_da"][z] = {"node": node, "hours": int(ok.sum()), "model": r4(m_z),
                                    "actual_da": r4(a_z), "gap": r4(m_z - a_z),
                                    "gap_pct": r4((m_z - a_z) / a_z * 100)}

        # ---- Z6 N-S congestion witness + belly share --------------------
        # The dominant ACTUAL zonal break is Path 15 (NP15 vs ZP26-and-south):
        # count hours of material N-over-S separation, model vs actual, and
        # the hod-10-15 belly share of the south's gap (localizing the
        # caiso-202 compression geographically).
        a_np = hub_lmp["TH_NP15_GEN-APND"].to_numpy()
        a_sp = hub_lmp["TH_SP15_GEN-APND"].to_numpy()
        okns = ~np.isnan(a_np) & ~np.isnan(a_sp)
        m_ns = lam["NP15"] - lam_sp
        a_ns = np.where(okns, a_np - a_sp, np.nan)
        hd = np.arange(HOURS) % 24
        belly = np.isin(hd, (10, 11, 12, 13, 14, 15))
        print(f"\n[Z6] N-S separation witness (NP15 − SP15) + belly share of south gap")
        for thr in (5.0, 15.0):
            hm = int((m_ns[okns] > thr).sum())
            ha = int((a_ns[okns] > thr).sum())
            print(f"  hours with NP15−SP15 > ${thr:.0f}: model {hm:5d}  actual {ha:5d}")
        print(f"  mean NP15−SP15: model {np.mean(m_ns[okns]):+.2f}  actual {np.nanmean(a_ns):+.2f}; "
              f"belly-only: model {np.mean(m_ns[okns & belly]):+.2f}  actual {np.nanmean(a_ns[okns & belly]):+.2f}")
        okh = ~np.isnan(a_sp)
        num_sp_belly = float(np.sum(d_sp[okh & belly] * (lam_sp[okh & belly] - a_sp[okh & belly])))
        num_sp_all = float(np.sum(d_sp[okh] * (lam_sp[okh] - a_sp[okh])))
        print(f"  belly (hod10-15) share of SP15-composite gap: "
              f"{num_sp_belly / num_sp_all * 100:.0f}%  (gap-MWh belly {num_sp_belly / 1e6:+.1f}M$, "
              f"all {num_sp_all / 1e6:+.1f}M$)")
        yr["ns_witness"] = {
            "model_gt5_h": int((m_ns[okns] > 5.0).sum()), "actual_gt5_h": int((a_ns[okns] > 5.0).sum()),
            "model_gt15_h": int((m_ns[okns] > 15.0).sum()), "actual_gt15_h": int((a_ns[okns] > 15.0).sum()),
            "model_mean": r4(np.mean(m_ns[okns])), "actual_mean": r4(np.nanmean(a_ns)),
            "model_belly_mean": r4(np.mean(m_ns[okns & belly])),
            "actual_belly_mean": r4(np.nanmean(a_ns[okns & belly])),
            "sp15_belly_gap_share_pct": r4(num_sp_belly / num_sp_all * 100)}

        results["years"][str(year)] = yr
        print()

    OUT_JSON.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
