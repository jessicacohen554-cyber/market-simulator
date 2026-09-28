"""SPP-97 phase 0 (zero LP): can a CC commitment mechanism reach the keeper's CC shape miss?

For every SPP CC_REGULAR plant with a CEMS series, from the keeper's committed run payload
(model hourly CF, uint8 % of nameplate) and the SPP bench (CAMPD hourly CF), classify the
MISSING-COMMITMENT plant-hours (CAMPD online, CF >= 5 %; model off, CF < 1 %) by the model's own
run pattern: BRIDGEABLE if the model-off gap is bounded by model-on hours on both sides and is at
most 24 h long (what a P0-anchored gap bridge can floor), else NEVER-STARTED. Energy in each class
is the CAMPD MWh in those hours (clipped at the measured min-load, 0.209 of nameplate for CC,
SPP-44 FINDING §1). Also reports the FLAT-TOP excess: hours with the model >= 95 % while CAMPD
< 70 %.

Usage: uv run python scripts/probes/_spp97_cc_commit_reach.py <payload.json>
Writes docs/handoffs/spp97/cc_commit_reach.json
"""
import base64, gzip, json, sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
MIN_LOAD = 0.209  # SPP CC plant-basis min-load, measured (FINDING-spp-44-2026-09-07.md §1)
MAX_GAP = 24


def dec(s):
    """Decode a payload/bench base64 uint8 CF % series."""
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float)


def main():
    """Classify missing-commitment CC plant-hours for every keeper year."""
    j = json.load(open(sys.argv[1]))
    out = {}
    for y in map(str, range(2019, 2026)):
        b = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz"))["bench"]["plants"]
        mp = j["years"][y]["plants"]
        tot = dict(miss_h=0, bridge_h=0, never_h=0, miss_twh_minload=0.0, bridge_twh=0.0, never_twh=0.0, flattop_h=0, plants=0)
        for k, v in b.items():
            if v["group"] != "CC_REGULAR" or v.get("nodata") or not v.get("campd"):
                continue
            key = k if k in mp else f"{k}:CC_REGULAR"
            if key not in mp:
                continue
            m, c = dec(mp[key]["m"]), dec(v["campd"])
            if len(m) != len(c):
                continue
            npl = v["npl"]
            tot["plants"] += 1
            on = m >= 1
            miss = (c >= 5) & ~on
            # model-off run segments
            idx = np.flatnonzero(~on)
            if len(idx):
                breaks = np.flatnonzero(np.diff(idx) > 1)
                starts = np.r_[idx[0], idx[breaks + 1]]
                ends = np.r_[idx[breaks], idx[-1]]
                bridgeable = np.zeros(len(m), bool)
                for s, e in zip(starts, ends):
                    if s > 0 and e < len(m) - 1 and (e - s + 1) <= MAX_GAP:
                        bridgeable[s : e + 1] = True
            else:
                bridgeable = np.zeros(len(m), bool)
            e_h = np.minimum(c, MIN_LOAD * 100) / 100 * npl / 1e6  # TWh at min-load
            tot["miss_h"] += int(miss.sum())
            tot["bridge_h"] += int((miss & bridgeable).sum())
            tot["never_h"] += int((miss & ~bridgeable).sum())
            tot["miss_twh_minload"] += float(e_h[miss].sum())
            tot["bridge_twh"] += float(e_h[miss & bridgeable].sum())
            tot["never_twh"] += float(e_h[miss & ~bridgeable].sum())
            tot["flattop_h"] += int(((m >= 95) & (c < 70)).sum())
        tot = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in tot.items()}
        tot["bridge_share"] = round(tot["bridge_twh"] / tot["miss_twh_minload"], 3) if tot["miss_twh_minload"] else None
        out[y] = tot
        print(y, tot)
    p = REPO / "docs/handoffs/spp97"
    p.mkdir(parents=True, exist_ok=True)
    (p / "cc_commit_reach.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
