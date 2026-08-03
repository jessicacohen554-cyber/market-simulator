"""ercot-152: CC offline-tier identifiability census on the committed SCED corpus.

Phase-0 refusal evidence for the ercot-151 charter's CC widening, measured on
the four committed sample-day NP3-965 parquets (the only SCED Gen Resource
rows in-repo after the 2026-07-22 corpus purge). Two questions, both answered
against the tier:

1. Does CC sit in the intra-hour-startable pool statuses (OFFQS/OFFNS, the
   ERCOT-88 construction)? -> NO: zero material CC OFFQS/OFFNS MW in any of
   the four extracts (top statuses are ON/OUT/ONREG/ONOS/OFF/STARTUP).
2. Are plain-OFF CC's own disclosed SCED2 curves scarcity-priced (so that
   re-pricing the offline increment at "its true start-inclusive offer" would
   move the tail)? -> NO: MW-weighted above-LSL segment quantiles are CHEAP
   (2024 tail days p50 $19.5 / p90 $83.9; 2025 tail days p50 $34.7 / p90
   $75.0) -- near the ON fleet's own curve (+$7-12 at p50), ~30x below the
   OFFQS/OFFNS CT pool ladder ($271-1,010).

Conclusion (rule 13/19): the CC block's phantom depth is a COMMITMENT-STATE
gap, not an offer-conduct gap -- its admissible offer-side expression does not
exist (the measured offer is cheap), and its cap-side expression is the closed
ercot41/43/106/108 envelope family. Committed record:
results/calibration/ercot152_cc_tier_census.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
D = REPO / 'data/raw/ercot'
MWC = [f'SCED2 Curve-MW{i}' for i in range(1, 36)]
PRC = [f'SCED2 Curve-Price{i}' for i in range(1, 36)]
COLS = ['SCED Time Stamp', 'Resource Type', 'Telemetered Resource Status',
        'HSL', 'LSL', 'HASL'] + MWC + PRC
QS = (0.1, 0.3, 0.5, 0.7, 0.9)


def seg_quants(df: pd.DataFrame):
    """MW-weighted price quantiles of above-LSL SCED2 segments (ERCOT-86/87
    construction: per row, segments in (max(prev, LSL), min(step MW, HASL)]
    at the step price clipped to $5,000)."""
    MW = df[MWC].apply(pd.to_numeric, errors='coerce').to_numpy(float)
    PR = df[PRC].apply(pd.to_numeric, errors='coerce').to_numpy(float)
    lsl = np.maximum(np.nan_to_num(
        pd.to_numeric(df['LSL'], errors='coerce').to_numpy(float)), 0)
    hasl = pd.to_numeric(df['HASL'], errors='coerce').to_numpy(float)
    segs_mw, segs_pr = [], []
    prev = lsl.copy()
    for k in range(35):
        q, p = MW[:, k], PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, hasl)
        mw = np.where(valid, np.maximum(hi - np.maximum(prev, lsl), 0), 0)
        t = mw > 0
        segs_mw.append(mw[t])
        segs_pr.append(np.minimum(p[t], 5000.0))
        prev = np.where(valid, np.maximum(prev, q), prev)
    mw = np.concatenate(segs_mw)
    pr = np.concatenate(segs_pr)
    if mw.sum() == 0:
        return None
    order = np.argsort(pr)
    pr, w = pr[order], mw[order]
    cum = np.cumsum(w) / w.sum()
    return {f'p{int(q*100)}': float(pr[np.searchsorted(cum, q)]) for q in QS}


def main() -> None:
    out = {}
    for f in sorted(D.glob('60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_*.parquet')):
        df = pd.read_parquet(f, columns=COLS)
        cc = df[df['Resource Type'].isin(['CCGT90', 'CCLE90'])]
        st = cc['Telemetered Resource Status'].astype(str).str.strip()
        n_iv = cc['SCED Time Stamp'].nunique()
        hsl = pd.to_numeric(cc['HSL'], errors='coerce')
        status_mw = (hsl.groupby(st).sum() / n_iv).sort_values(ascending=False)
        rec = {
            'intervals': int(n_iv),
            'cc_mean_mw_by_status': {k: round(float(v), 1) for k, v in status_mw.head(10).items()},
            'cc_offqs_offns_mean_mw': round(float(status_mw.reindex(['OFFQS', 'OFFNS']).fillna(0).sum()), 1),
        }
        for grp in ('OFF', 'ON', 'STARTUP'):
            r = seg_quants(cc[st == grp])
            if r:
                rec[f'cc_{grp.lower()}_curve_quantiles'] = {k: round(v, 1) for k, v in r.items()}
        out[f.name.split('Data_')[1].replace('.parquet', '')] = rec
    path = REPO / 'results/calibration/ercot152_cc_tier_census.json'
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f'wrote {path}')


if __name__ == '__main__':
    main()
