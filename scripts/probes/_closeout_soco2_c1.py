"""closeout-SOCO-2 zero-LP probe (FINDING-closeout-soco-2-2026-10-03.md); run from the repo root."""

import json
import re
import base64
import gzip
import sys

sys.path.insert(0, "scripts")
sys.path.insert(0, ".")
import calibration_verdict as cv

t = open("frontend/data/backcast/runs/2026-10-02-w0-soco-fix2.js").read()
p = json.loads(
    gzip.decompress(base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1)))
)
for y in range(2019, 2026):
    yp = p["years"][str(y)]
    yb = json.load(gzip.open(f"frontend/data/backcast/bench/SOCO/{y}.json.gz"))["bench"]
    rows = cv.score_fuelmix(y, yp, yb, iso="SOCO")
    for r in rows:
        if (
            r.get("key")
            in ("CC_REGULAR", "COAL_BIT", "COAL_PRB", "ST_GAS", "CT_PEAKER")
            or r.get("status") != "PASS"
        ):
            print(
                y,
                {
                    k: r[k]
                    for k in r
                    if k
                    in (
                        "key",
                        "status",
                        "model",
                        "actual",
                        "delta",
                        "share_pp",
                        "vol_band",
                        "tol",
                        "band",
                    )
                }
                if isinstance(r, dict)
                else r,
            )
print("---- denominators")
for y in range(2019, 2026):
    yp = p["years"][str(y)]
    yb = json.load(gzip.open(f"frontend/data/backcast/bench/SOCO/{y}.json.gz"))["bench"]
    m_gen, a_gen = cv._gen_totals(yp, yb)
    m = yp["gmModel"]["CC_REGULAR"]
    a = yb["classFull"]["CC_REGULAR"]
    print(
        y,
        "m_gen %.1f a_gen %.1f gap %.1f | CC share pp %.2f ; at actual denom %.2f ; denom part %.2f ; CC TWh to clear 3.0pp: %.2f"
        % (
            m_gen,
            a_gen,
            a_gen - m_gen,
            100 * m / m_gen - 100 * a / a_gen,
            100 * m / a_gen - 100 * a / a_gen,
            100 * m / m_gen - 100 * m / a_gen,
            m - (0.03 + a / a_gen) * m_gen,
        ),
    )
