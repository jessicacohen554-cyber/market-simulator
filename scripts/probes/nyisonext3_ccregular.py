"""NYISO-NEXT-3 (zero LP): CC_REGULAR (and ST_GAS CC plants) TWh vs EIA-923 by zone and plant, keeper vs arm.

Reads the two runs' payloads -- from the working tree, else from ``git show <ref>:<path>`` so a
keeper pruned in the promoting session still resolves -- and the committed NYISO bench parts.
Writes ``results/calibration/_nyisonext3_ccregular.json``.

Usage::

    python3 scripts/probes/nyisonext3_ccregular.py --ref origin/main \\
        --pair 2026-09-26-nyisonext2-astoria-pair-span 2026-09-26-nyisonext3-tranche-basis-span \\
        --pair 2026-09-26-nyisonext2-astoria-pair-2021 2026-09-26-nyisonext3-tranche-basis-2021
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _payload(rid: str, ref: str) -> dict:
    """Decode a gzip+base64 run payload from the tree or from ``ref``."""
    rel = f"frontend/data/backcast/runs/{rid}.js"
    p = REPO / rel
    s = (
        p.read_text()
        if p.exists()
        else subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair", nargs=2, action="append", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/_nyisonext3_ccregular.json")
    )
    a = ap.parse_args()
    res: dict = {}
    for k, x in a.pair:
        pk, px = _payload(k, a.ref), _payload(x, a.ref)
        for y in sorted(px["years"]):
            bench = json.loads(
                gzip.open(
                    REPO / f"frontend/data/backcast/bench/NYISO/{y}.json.gz"
                ).read()
            )["bench"]["plants"]
            zone = defaultdict(lambda: [0.0, 0.0, 0.0])
            moved = {}
            for key, bp in bench.items():
                if bp.get("group") != "CC_REGULAR":
                    continue
                mk = pk["years"].get(y, {}).get("plants", {}).get(key)
                mx = px["years"][y]["plants"].get(key)
                if mk is None or mx is None:
                    continue
                z = zone[bp["zone"]]
                z[0] += mk["m_ann"]
                z[1] += mx["m_ann"]
                z[2] += bp["e_ann"] or 0.0
                if abs(mx["m_ann"] - mk["m_ann"]) > 0.05:
                    moved[f"{key} {bp['name']}"] = [
                        round(mk["m_ann"], 2),
                        round(mx["m_ann"], 2),
                        round(bp["e_ann"] or 0.0, 2),
                    ]
            res[y] = {
                "zone": {z: [round(v, 2) for v in vals] for z, vals in zone.items()},
                "plants_moved_gt_0.05": moved,
            }
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
