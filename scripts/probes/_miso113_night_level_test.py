"""miso-113 structural test: does the arm put the fleet ON its measured night level?

The statistic that adjudicates the promotion question, reproducing
``FINDING-miso112-prb-committed-split-2026-08-01.md`` §4 verbatim so the two
sessions' numbers are directly comparable: per plant, over ONLINE hours only,
capacity-weighted across the regulated PRB plants, the model's within-run night
loading level against each plant's OWN measured ``night_p50``.

The mechanism under test (``miso_coal_night_floor``) exists to hold the fleet at
that level, so this — not a gate — is what decides whether it does what it
claims. Run it on the control and the arm:

    python scripts/probes/_miso113_night_level_test.py <run-id> [<run-id> ...]

Every input is a committed artifact: the run payload's per-plant hourly model MW
(``frontend/data/backcast/runs/<id>.js``), the frozen measured night level
(``coal_prb_committed_split_MISO.csv``: ``night_p50`` and the ``hsl_mw`` basis
it was derived on), and the EIA-860 regulated self-commitment scope. No LP.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from lib import backcast_artifacts as ba  # noqa: E402

from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants  # noqa: E402

YEARS = ("2023", "2024", "2025")
NIGHT_HOURS = range(6)  # h0-5, the artifact's own night window
RUN_THRESHOLD_FRAC = 0.05  # the detector's own online/run threshold


def _decode_cf_bytes(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode an 8760-byte CF%-encoded series to hourly MW (scorer's codec)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (float(annual_twh) * 1e6 / tot)
    return raw / 100.0 * npl


def night_levels(run_id: str, scope: list[tuple[int, float, float]]) -> dict:
    """Return ``{year: (cap-wtd model level, cap-wtd |model - measured|)}``."""
    payload = ba.decode_run_js((REPO / f"frontend/data/backcast/runs/{run_id}.js").read_text())
    out = {}
    for year in YEARS:
        plants = payload["years"].get(year, {}).get("plants", {})
        levels, errs, weights = [], [], []
        for code, night_p50, hsl in scope:
            rec = plants.get(str(code))
            if rec is None or not rec.get("m") or hsl <= 0.0:
                continue
            cap = float(rec.get("cap") or hsl)
            mw = _decode_cf_bytes(rec["m"], rec.get("m_ann"), cap)
            hod = np.arange(mw.size) % 24
            night = np.isin(hod, list(NIGHT_HOURS)) & (mw > RUN_THRESHOLD_FRAC * cap)
            if not night.any():
                continue
            model_level = float(np.median(mw[night] / hsl))
            levels.append(model_level)
            errs.append(abs(model_level - night_p50))
            weights.append(hsl)
        w = np.asarray(weights)
        out[year] = (
            float(np.dot(levels, w) / w.sum()),
            float(np.dot(errs, w) / w.sum()),
            len(levels),
        )
    return out


def main() -> None:
    run_ids = sys.argv[1:]
    if not run_ids:
        raise SystemExit(__doc__)
    night = pd.read_csv(
        REPO / "data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv"
    )
    regulated = eia860_selfcommit_scope_plants()
    scope = [
        (int(r.plant_code), float(r.night_p50), float(r.hsl_mw))
        for r in night.itertuples(index=False)
        if str(r.leg) == "REG" and int(r.plant_code) in regulated
    ]
    w = np.array([h for _, _, h in scope])
    measured = float(np.dot([n for _, n, _ in scope], w) / w.sum())
    print(f"scope: {len(scope)} regulated PRB plants; MEASURED cap-wtd "
          f"night_p50 = {measured:.4f}\n")

    results = {rid: night_levels(rid, scope) for rid in run_ids}
    header = "year  measured  " + "  ".join(f"{rid[-22:]:>24}" for rid in run_ids)
    print(header)
    for year in YEARS:
        cells = []
        for rid in run_ids:
            lvl, err, n = results[rid][year]
            cells.append(f"{lvl:>10.4f} (err {err:.4f}, n={n:2d})")
        print(f"{year}  {measured:8.4f}  " + "  ".join(cells))
    print(
        "\nRead: the arm PASSES this test when it moves the cap-weighted model "
        "level TOWARD the measured value and shrinks the cap-weighted absolute "
        "error vs the control. miso-112's split arm FAILED it — it drove the "
        "level BELOW the meter (0.434 measured; control 0.483/0.437, arm "
        "0.407/0.374)."
    )


if __name__ == "__main__":
    main()
