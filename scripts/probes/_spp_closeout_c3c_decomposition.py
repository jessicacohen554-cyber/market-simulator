"""SPP close-out W3 (zero LP): decompose the C3c RT price tail for the owner's R-10 classification.

Charter: closeout-SPP wave 1 (docs/backcast-closeout-plan-2026-10.md §3.4 row C3c, §5.0 R-10).
Re-derives SPP-29's DA-vs-RT reading on the CURRENT keeper (`spp100_arm_span`) for every
registered year and adds three splits SPP-29 did not publish:

1. Tail-hour class: RT hub average > $200 (the scorer's actual, `TAIL_THRESHOLD["SPP"]`), split by
   what SPP's own hourly day-ahead market cleared in the same hour (DA > $200 / $100-200 / <= $100).
2. Hub-average LMP components (MEC / MCC / MLC, RT and DA) in tail hours: whether the tail is an
   energy-component (system-wide) event or a congestion one.
3. RTBM reserve MCPs (zone mean of the 5-minute posts) in tail hours vs all hours: whether reserve
   scarcity pricing co-occurs with the tail (SPP's ramp product is not in the archive; the MCP file
   carries RegUp / RegDn / Spin / Supp only).

Model side: the keeper's P1 max zonal dual (the scorer's gated quantity) in the same hours.

Usage: uv run python scripts/probes/_spp_closeout_c3c_decomposition.py
Writes results/phase0/spp/_spp_closeout_c3c_decomposition.json (and prints the table).
"""

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/spp100_arm_span"
VAL = REPO / "data/raw/_validation-source"
OUT = REPO / "results/phase0/spp/_spp_closeout_c3c_decomposition.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
TAIL = 200.0  # calibration_verdict.TAIL_THRESHOLD["SPP"] (owner ruling P6)
DA_LOW = 100.0  # SPP-29 §1c reading: "DA cleared below $100"


def hourly_mcp(year: int) -> pd.DataFrame:
    """Zone-mean, hour-mean RTBM MCPs on the model clock (the `_spp96` reader, every product column)."""
    z = zipfile.ZipFile(REPO / f"data/raw/spp-or-mcp/RTBM_MCP_{year}.csv.zip")
    d = pd.read_csv(z.open(z.namelist()[0]))
    d.columns = [c.strip().upper() for c in d.columns]
    t = pd.to_datetime(d["GMTINTERVALEND"], format="mixed")
    t = t - pd.Timedelta(minutes=5) - pd.Timedelta(hours=6)
    keep = (t.dt.year == year) & ~((t.dt.month == 2) & (t.dt.day == 29))
    d, t = d[keep], t[keep]
    doy = t.dt.dayofyear.values
    if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366:
        doy = np.where(doy > 60, doy - 1, doy)
    d = d.assign(hour=(doy - 1) * 24 + t.dt.hour.values)
    cols = [c for c in d.columns if c in ("REGUPSERVICE", "REGDNSERVICE", "SPIN", "SUPP")
            or "RAMP" in c or "UNC" in c]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.groupby("hour")[cols].mean().reindex(range(8760))


def year_row(year: int, hub: pd.DataFrame, comp: pd.DataFrame) -> dict:
    """One year's decomposition."""
    h = hub[hub.year == year].set_index("hour").reindex(range(8760))
    rt, da = h["rt"].values.astype(float), h["da"].values.astype(float)
    sysd = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"].astype(str).str.upper().str.contains("P1")] if "pass" in sysd else sysd
    model = sysd.groupby("hour")["price"].max().reindex(range(8760)).values.astype(float)
    tail = rt > TAIL
    n = int(tail.sum())
    c = comp[comp.year == year].groupby(["market", "hour"])[["lmp", "mec", "mcc", "mlc"]].mean()
    out = {
        "rt_tail_hours": n,
        "model_hours_gt200": int((model > TAIL).sum()),
        "model_hours_gt200_in_rt_tail": int(((model > TAIL) & tail).sum()),
        "da_hours_gt200": int((da > TAIL).sum()),
        "tail_da_gt200": int((tail & (da > TAIL)).sum()),
        "tail_da_100_200": int((tail & (da > DA_LOW) & (da <= TAIL)).sum()),
        "tail_da_le100": int((tail & (da <= DA_LOW)).sum()),
        "rt_mean": round(float(np.nanmean(rt)), 3),
    }
    if n:
        wedge = rt[tail] - da[tail]
        out |= {
            "tail_median_rt": round(float(np.median(rt[tail])), 2),
            "tail_median_da": round(float(np.nanmedian(da[tail])), 2),
            "tail_median_rt_minus_da": round(float(np.nanmedian(wedge)), 2),
            "allhour_median_rt_minus_da": round(float(np.nanmedian(rt - da)), 2),
            "tail_share_rt_gt_da": round(float(np.nanmean(wedge > 0)), 3),
            "tail_median_model": round(float(np.nanmedian(model[tail])), 2),
            # Tail-hour premium over the year's RT median, carried by each RT component.
            "tail_energy_contrib_to_rt_mean": round(float(rt[tail].sum() - n * np.nanmedian(rt)) / 8760, 3),
        }
        th = np.flatnonzero(tail)
        for mk in ("rt", "da"):
            if mk not in c.index.get_level_values(0):
                continue
            cm = c.loc[mk].reindex(range(8760))
            for col in ("mec", "mcc", "mlc"):
                out[f"tail_median_{mk}_{col}"] = round(float(np.nanmedian(cm[col].values[th])), 2)
            prem = cm["lmp"].values[th] - np.nanmedian(cm["lmp"].values)
            mec_prem = cm["mec"].values[th] - np.nanmedian(cm["mec"].values)
            out[f"tail_{mk}_premium_share_mec"] = round(float(np.nansum(mec_prem) / np.nansum(prem)), 3)
        try:
            mcp = hourly_mcp(year)
            for col in mcp.columns:
                v = mcp[col].values
                out[f"mcp_{col.lower()}_tail_median"] = round(float(np.nanmedian(v[th])), 2)
                out[f"mcp_{col.lower()}_all_median"] = round(float(np.nanmedian(v)), 2)
            spin = mcp["SPIN"].values if "SPIN" in mcp else None
            if spin is not None:
                # Contingency reserve offer cap $100/MW (spp-planning transcription): a Spin MCP above
                # it is demand-curve (shortage) pricing, not an offer.
                out["tail_hours_spin_mcp_gt100"] = int(np.sum(spin[th] > 100.0))
                out["all_hours_spin_mcp_gt100"] = int(np.nansum(spin > 100.0))
        except (FileNotFoundError, KeyError) as exc:
            out["mcp_error"] = repr(exc)
    return out


def main() -> None:
    """Compute and write the per-year decomposition."""
    hub = pd.read_parquet(VAL / "actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(VAL / "actual_lmp_components_hourly_zonal_SPP.parquet")
    rows = {y: year_row(y, hub, comp) for y in YEARS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"bundle": str(BUNDLE.relative_to(REPO)), "years": rows}, indent=1))
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
