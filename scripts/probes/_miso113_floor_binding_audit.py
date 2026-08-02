"""miso-113 Phase-2 probe: would the COAL_PRB night-level floor BIND on the keeper?

Evaluates kill rule **K1 (INERTNESS)** of
``results/calibration/PREREG-miso113-prb-night-floor-2026-08-01.md`` §5, which
was committed before this script ran.

No LP. Every input is a committed artifact:

- the keeper's own per-plant hourly model MW —
  ``frontend/data/backcast/runs/2026-07-31-miso-109b-hy-level.js`` (CF-byte
  payload, decoded with the dashboard's own ``_decode_cf_bytes`` codec);
- the frozen measured night level —
  ``data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv``
  (``night_p50``, deriver ``scripts/data/derive_prb_committed_split.py``);
- the plant's own tranche bands — ``thermal_tranches_MISO.csv``
  (``mustrun_pct`` / ``committed_pct`` / ``nameplate_mw``);
- the regulated self-commitment scope — ``eia860_selfcommit_scope_plants()``.

The floor the mechanism can physically write on a plant is capped twice: at the
plant's measured night level, and at the ``_committed`` tranche's own capacity
(the detector rejects the incremental ``_econ``/``_peak`` tranches by physics,
so it can never reach past ``mustrun + committed``). Merit order inside a plant
(mustrun fuel-free < committed discounted < econ < peak) makes the plant-total
test exact::

    floor_mw = min(night_p50, (mustrun_pct + committed_pct)/100) * nameplate
    bind_mwh = sum over ONLINE hours of max(0, floor_mw - model_mw)

K1 fires -- the mechanism is INERT and no solve is spent -- when ``bind_twh`` is
under 0.5 % of the keeper's COAL_PRB annual energy in EVERY year.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from lib import backcast_artifacts as ba  # noqa: E402

KEEPER = "2026-07-31-miso-109b-hy-level"
YEARS = ("2023", "2024", "2025")
RUN_THRESHOLD_FRAC = 0.05  # the detector's own online/run threshold
K1_SHARE = 0.005  # PREREG §5: 0.5 % of class energy


def _decode_cf_bytes(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode an 8760-byte CF%-encoded series to hourly MW (scorer's codec)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (float(annual_twh) * 1e6 / tot)
    return raw / 100.0 * npl


def main() -> None:
    night = pd.read_csv(
        REPO / "data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv"
    )
    tranches = pd.read_csv(REPO / "data/raw/_processed-legacy/thermal_tranches_MISO.csv")
    tranches = tranches[tranches.plant_group.astype(str).str.contains("COAL")]
    bands = tranches.set_index("plant_code")[
        ["nameplate_mw", "mustrun_pct", "committed_pct"]
    ].to_dict("index")
    reg_scope = eia860_selfcommit_scope_plants()

    payload = ba.decode_run_js((REPO / f"frontend/data/backcast/runs/{KEEPER}.js").read_text())

    # The mechanism's scope: the artifact's REG leg, cross-checked against the
    # live EIA-860 regulated self-commitment set the runtime would gate on.
    scope = []
    for r in night.itertuples(index=False):
        code = int(r.plant_code)
        if str(r.leg) != "REG" or code not in bands:
            continue
        if code not in reg_scope:
            print(f"  (plant {code}: artifact REG but not in live 860 scope — skipped)")
            continue
        scope.append((code, float(r.night_p50)))
    print(f"miso-113 K1 scope: {len(scope)} regulated PRB plants\n")

    verdicts = {}
    for year in YEARS:
        plants = payload["years"][year]["plants"]
        tot_bind = 0.0
        tot_floor_reachable = 0.0
        rows = []
        for code, night_p50 in scope:
            rec = plants.get(str(code))
            b = bands[code]
            npl = float(b["nameplate_mw"])
            if rec is None or not rec.get("m") or npl <= 0.0:
                continue
            mw = _decode_cf_bytes(rec["m"], rec.get("m_ann"), float(rec.get("cap") or npl))
            reach = (float(b["mustrun_pct"]) + float(b["committed_pct"])) / 100.0
            floor_frac = min(night_p50, reach)
            floor_mw = floor_frac * npl
            online = mw > RUN_THRESHOLD_FRAC * npl
            deficit = np.clip(floor_mw - mw, 0.0, None) * online
            bind = float(deficit.sum())
            tot_bind += bind
            tot_floor_reachable += float((floor_mw * online).sum())
            rows.append(
                (code, npl, night_p50, reach, floor_frac, int(online.sum()),
                 int((deficit > 0.0).sum()), bind / 1e6)
            )

        # Class energy from the keeper's own committed class hourly sidecar.
        cls = pd.read_parquet(
            REPO / f"results/calibration/miso109_hy_level_B/hourly/class_hourly_{year}.parquet"
        )
        # Long form: (year, pass, klass, hour, mw). The scored pass is P1.
        sel = cls[(cls["klass"] == "COAL_PRB") & (cls["pass"] == "P1")]
        prb_twh = float(sel["mw"].sum()) / 1e6 if not sel.empty else float("nan")

        share = tot_bind / 1e6 / prb_twh if prb_twh == prb_twh and prb_twh > 0 else float("nan")
        verdicts[year] = share
        print(f"=== {year} ===")
        print(f"  COAL_PRB class energy (keeper)      : {prb_twh:8.3f} TWh")
        print(f"  floor volume the arm would WRITE    : {tot_floor_reachable/1e6:8.3f} TWh")
        print(f"  floor volume that would BIND        : {tot_bind/1e6:8.4f} TWh")
        print(f"  binding share of COAL_PRB energy    : {share*100:8.4f} %   "
              f"(K1 line {K1_SHARE*100:.1f} %)")
        top = sorted(rows, key=lambda r: -r[7])[:6]
        print("   top binding plants  code   npl    night  reach  floor  online_h  bind_h  bind_TWh")
        for c, npl, n, reach, ff, oh, bh, bt in top:
            print(f"      {c:>21}  {npl:6.0f}  {n:5.3f}  {reach:5.3f}  {ff:5.3f}  "
                  f"{oh:7d}  {bh:6d}  {bt:8.4f}")
        print()

    scored = [s for s in verdicts.values() if s == s]
    if len(scored) != len(YEARS):
        raise SystemExit(
            f"K1 UNDECIDABLE: only {len(scored)}/{len(YEARS)} years scored — "
            "the class-energy lookup failed; fix before quoting a verdict."
        )
    fired = all(s < K1_SHARE for s in scored)
    print("K1 (INERTNESS) verdict:", "FIRED — mechanism INERT, no solve" if fired
          else "NOT fired — the floor binds; Phase 3 A/B runs")
    print("   per-year binding share:", {y: f"{s*100:.4f}%" for y, s in verdicts.items()})


if __name__ == "__main__":
    main()
