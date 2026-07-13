"""Re-gate the PJM/NYISO/NEISO keepers on the fixed fleet_to_bins CC HR basis.

The caiso-78 blast radius (calibration log, 2026-07-12): under
``cc_nameplate_summer_derate`` — defaulted ON for PJM/NYISO/NEISO/CAISO in
``pipeline.backcast_config`` — the ``fleet_to_bins`` aggregation computed
``base_hr = hr_cap / cap`` AFTER the nameplate rescale, deflating every CC
plant's base heat rate by its own net-summer/nameplate ratio and scrambling
the within-CC merit order. CAISO re-gated same-day (caiso-78, promoted); the
PJM/NYISO/NEISO keepers were solved on the buggy code and were "flagged for
follow-up, not silently re-solved". This driver is that follow-up: a
recipe-VERBATIM re-solve of each keeper (and a fresh zero-forcing twin) on
the fixed code, registered as a NEW probe pair so the A/B against the
committed keeper stays on record (never an in-place rewrite).

Recipe reconstruction is the sanctioned ``replay_keeper.build_kwargs`` off
the keeper bundle's ``meta.json`` (the only recipe channel that hard-errors
rather than silently dropping structure). The twin is rebuilt canonically
from the SAME keeper meta with ``zero_forcing_ablation=True`` pointed at the
new main bundle — not replayed from the old twin's meta, which does not
record the ablation kwargs (its neutralized flags live only in
run_config.json).

Zero recipe changes, zero new parameters; the only difference from the
committed keeper bundles is the corrected measured HR basis already on main
(rule-14 measured-input correction; LOYO-exempt per the caiso-78 precedent —
the fix is code-level and year-invariant).

Usage: python scripts/probes/_fleet_to_bins_regate.py {PJM|NYISO|NEISO} {main|ablation} [--smoke]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"

# ISO -> (keeper bundle, new probe bundle dir). Session numbering: next free
# per-ISO number at authoring time (pjm-104 / nyiso-61 / neiso-58 highest).
REGATES: dict[str, tuple[str, str]] = {
    "PJM": ("pjm98_cc_mustrun", "pjm105_cc_hr_regate"),
    "NYISO": ("nyiso61_downstate_import", "nyiso62_cc_hr_regate"),
    "NEISO": ("neiso56_reserve_coopt", "neiso59_cc_hr_regate"),
}

REGATE_NOTE = (
    "fleet_to_bins CC HR-basis re-gate (caiso-78 blast radius): keeper recipe "
    "VERBATIM via replay_keeper.build_kwargs off {keeper}/meta.json, re-solved "
    "on the fixed base_hr-pre-rescale code (fleet.py, caiso-78 2026-07-12). "
    "Zero recipe changes, zero new parameters."
)


def _write_attestation(iso: str, keeper: str, out: Path) -> None:
    """Copy the keeper's DOF attestation, appending the re-gate provenance.

    The probe adds no free parameter, so the ledger is the keeper's ledger;
    only the ``attested_by`` line changes (the _caiso80_attestation pattern —
    deterministic from repo state, so CI reproduces it byte-identically).
    """
    src = ROOT / keeper / "calibration_attestation.json"
    att = json.loads(src.read_text())
    att["governance"]["attested_by"] = (
        f"{iso.lower()} fleet_to_bins re-gate session 2026-07-13: "
        + att["governance"]["attested_by"]
        + " RE-GATE: same recipe re-solved on the fixed fleet_to_bins CC "
        "heat-rate basis (base_hr computed pre-rescale under "
        "cc_nameplate_summer_derate — the caiso-78 rule-14 measured-input "
        "correction). Zero recipe changes, zero new free parameters; "
        "LOYO-exempt per the caiso-78 precedent (code-level, year-invariant)."
    )
    (out / "calibration_attestation.json").write_text(json.dumps(att, indent=2) + "\n")


def main() -> None:
    """Replay one keeper (or mint its fresh zero-forcing twin) on fixed code."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iso", choices=sorted(REGATES))
    ap.add_argument("mode", choices=["main", "ablation"])
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="240-hour single-year smoke run into a throwaway dir (data-"
        "availability check only; never registered)",
    )
    args = ap.parse_args()

    keeper, new_dir = REGATES[args.iso]
    ablate = args.mode == "ablation"
    out = ROOT / (new_dir + ("-ablation" if ablate else ""))
    if args.smoke:
        out = ROOT / f"_smoke_{new_dir}" / args.mode

    meta = json.loads((ROOT / keeper / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [2023] if args.smoke else [int(y) for y in meta["years"]]
    kwargs["hours"] = 240 if args.smoke else int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out
    kwargs["note"] = REGATE_NOTE.format(keeper=keeper) + (
        " ZERO-FORCING TWIN (D-3): every merchant floor/bridge neutralized "
        "via the registry off-list."
        if ablate
        else ""
    )
    if ablate:
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = new_dir

    out.mkdir(parents=True, exist_ok=True)
    print(f"re-gate solve: {args.iso} {args.mode} {kwargs['years']} -> {out}")
    rcf.solve_and_persist(**kwargs)
    if not ablate and not args.smoke:
        _write_attestation(args.iso, keeper, out)
    print(f"DONE {args.iso} {args.mode} -> {out}")


if __name__ == "__main__":
    main()
