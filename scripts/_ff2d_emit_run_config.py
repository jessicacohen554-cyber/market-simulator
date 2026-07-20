"""FF-2D scoring helper: emit run_config.json for forecast_verdict.py FC-7.
Additive, scorer-side only; touches no model behavior.
  - full-horizon bundle: python _ff2d_emit_run_config.py summary <full_horizon_summary.json>
      -> reads the cached run_dir/config.yaml (the faithful ScenarioConfig dump)
  - hindcast bundle:     python _ff2d_emit_run_config.py hindcast <bundle_dir>
      -> reads meta.json (the faithful flag surface); adds mode=forecast
         (the hindcast harness runs mode='forecast', hindcast=True — FF-2C §1.2)
Writes run_config.json beside the summary / at the bundle root."""

import json
import sys
import pathlib
import yaml

kind = sys.argv[1]
if kind == "summary":
    summ_path = pathlib.Path(sys.argv[2])
    summ = json.loads(summ_path.read_text())
    cfg = yaml.safe_load((pathlib.Path(summ["run_dir"]) / "config.yaml").read_text())
    out = summ_path.parent / "run_config.json"
elif kind == "hindcast":
    bundle = pathlib.Path(sys.argv[2])
    meta = json.loads((bundle / "meta.json").read_text())
    cfg = {**meta, "mode": "forecast", "hindcast": True}
    out = bundle / "run_config.json"
else:
    raise SystemExit(f"unknown kind {kind!r}")
out.write_text(json.dumps(cfg, indent=2, default=str) + "\n")
print(
    f"wrote {out}  (mode={cfg.get('mode')}, cmc={cfg.get('capacity_market_clearing')}, cmc_by_iso={cfg.get('capacity_market_clearing_by_iso')})"
)
