"""FF-2D scoring helper: emit run_config.json for forecast_verdict FC-7 —
HISTORICAL bundles only. Additive, scorer-side only; touches no model behavior.

Since FFR-3D (``run_full_horizon.py``) and FFR-3K (``run_capacity_hindcast.py``)
every new bundle carries a PRODUCER-written ``run_config.json``
(``scripts/lib/run_record.py::write_run_config`` — the solved-config RESOLUTION,
read verbatim from the cache's ``config.yaml``). This helper exists solely for
bundles that predate those writers and therefore lack the artifact:

  - full-horizon bundle: python _ff2d_emit_run_config.py summary <full_horizon_summary.json>
      -> reads the cached run_dir/config.yaml (the faithful ScenarioConfig dump)
  - hindcast bundle:     python _ff2d_emit_run_config.py hindcast <bundle_dir>
      -> reads the bundle's own run_config.yaml — the harness's full
         ScenarioConfig dump, which natively carries mode='forecast' and
         hindcast=True (set by build_config, FF-2C §1.2). NEVER meta.json:
         a ~30-key harness meta is not a config surface — scoring it as one
         was the FFR-2E propagation channel, and a config field the meta
         omits reads as absent downstream (FC-2 row 4, FC-7 row 1). Closed
         per FFR-3R §6.1 by FFR-3X.

REFUSE-IF-EXISTS (FFR-3X guard, the FFR-3K §6 follow-up): the helper never
overwrites an existing run_config.json. Overwriting a producer-written artifact
with a scoring-time reconstruction is a provenance downgrade — a record field
sourced from something other than the config the solve ran on, the exact defect
class FFR-3R closed. The refusal is LOUD (a silent skip and a silent overwrite
are both invisible; only one of them is safe). There is deliberately no
override flag: re-emitting over an already-scored artifact is verdict-affecting
and needs its own lane, so the only path is the explicit, visible act of
deleting the file first.

Writes run_config.json beside the summary / at the bundle root.
"""

import json
import pathlib
import sys

import yaml


def _refuse_overwrite(out: pathlib.Path, bundle: pathlib.Path) -> None:
    """SystemExit if ``out`` already exists — never overwrite, never skip quietly."""
    if out.exists():
        raise SystemExit(
            f"REFUSING to write {out}: bundle {bundle} already carries a "
            "run_config.json.\n"
            "Overwriting it with a scoring-time reconstruction is a provenance "
            "downgrade (FFR-3K §6 / FFR-3R): a post-FFR-3K bundle's artifact was "
            "written by the PRODUCER from the config the solve actually ran on "
            "and outranks anything this helper can rebuild; a historical bundle "
            "whose artifact this helper wrote earlier is already scored, and "
            "re-emitting over it is verdict-affecting (FFR-3R §6.1) and needs "
            "its own lane.\n"
            "This helper serves bundles that LACK the artifact. There is "
            "deliberately no override flag: if a future lane authorizes "
            "re-emission, delete the file first — an explicit, visible act."
        )


def main(argv: "list[str] | None" = None) -> pathlib.Path:
    """Emit ``run_config.json`` for one historical bundle; return the path written."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        raise SystemExit(__doc__)
    kind = argv[0]
    if kind == "summary":
        summ_path = pathlib.Path(argv[1])
        out = summ_path.parent / "run_config.json"
        _refuse_overwrite(out, summ_path.parent)
        summ = json.loads(summ_path.read_text())
        cfg = yaml.safe_load(
            (pathlib.Path(summ["run_dir"]) / "config.yaml").read_text()
        )
    elif kind == "hindcast":
        bundle = pathlib.Path(argv[1])
        out = bundle / "run_config.json"
        _refuse_overwrite(out, bundle)
        dump = bundle / "run_config.yaml"
        if not dump.exists():
            raise SystemExit(
                f"{bundle} has no run_config.yaml — the bundle predates the "
                "harness's full ScenarioConfig dump, so a faithful config "
                "surface cannot be reconstructed. Rebuilding one from meta.json "
                "is NOT a fallback: the meta is a ~30-key harness record, not "
                "the config the solve ran on (FFR-3R §6.1)."
            )
        cfg = yaml.safe_load(dump.read_text())
    else:
        raise SystemExit(f"unknown kind {kind!r}")
    out.write_text(json.dumps(cfg, indent=2, default=str) + "\n")
    print(
        f"wrote {out}  (mode={cfg.get('mode')}, cmc={cfg.get('capacity_market_clearing')}, "
        f"cmc_by_iso={cfg.get('capacity_market_clearing_by_iso')})"
    )
    return out


if __name__ == "__main__":
    main()
