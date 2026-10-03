"""Fixed schema for ``calibration_attestation.json`` (owner ruling 2026-10-03).

The contract lives in ``data/dictionary/schema/calibration_attestation.document.yaml``;
this module loads it, validates an attestation against it and migrates an
existing keeper's attestation ADDITIVELY (adds the keys the schema requires,
never deletes, renames or rewrites a lane block, a DOF entry or an exception).

Wired into ``scripts/audit_keepers.py`` (E16, FAIL) and
``scripts/promote_keeper.py`` step 3 (migrate, then refuse an invalid file).

CLI (idempotent, safe to re-run after a merge)::

    python3 scripts/lib/attestation_schema.py --migrate results/calibration/*/calibration_attestation.json
    python3 scripts/lib/attestation_schema.py --check   results/calibration/*/calibration_attestation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO / "data" / "dictionary" / "schema" / "calibration_attestation.document.yaml"
)

#: Fields a well-formed ``governance.authorized_price_tuning`` declaration
#: carries (mirrors ``calibration_verdict.score_governance`` / audit E10).
TUNING_FIELDS = ("channel", "ruling", "value", "years_held", "set_ex_ante", "not_swept")


@lru_cache(maxsize=1)
def load_schema() -> dict:
    """Load the document schema YAML once."""
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def _is_known_key(key: str, schema: dict) -> bool:
    if key in schema["required_keys"] or key in schema.get("optional_keys", ()):
        return True
    return any(key.startswith(p) for p in schema.get("optional_key_prefixes", ()))


def tuning_declared(att: dict) -> bool:
    """Whether ``governance.authorized_price_tuning`` is a well-formed declaration."""
    gov = att.get("governance")
    blk = gov.get("authorized_price_tuning") if isinstance(gov, dict) else None
    return isinstance(blk, dict) and all(f in blk for f in TUNING_FIELDS)


def validate(att: dict | None) -> list[str]:
    """Return every schema violation of ``att`` (empty list = valid)."""
    if not isinstance(att, dict):
        return ["attestation is not a JSON object"]
    schema = load_schema()
    keys = schema["keys"]
    problems: list[str] = []
    for k in schema["required_keys"]:
        if k not in att:
            problems.append(f"missing required key {k!r}")
    if "schema" in att and att["schema"] != schema["schema_tag"]:
        problems.append(
            f"schema is {att['schema']!r}, expected {schema['schema_tag']!r}"
        )

    gov = att.get("governance")
    if "governance" in att:
        if not isinstance(gov, dict):
            problems.append("governance is not an object")
        else:
            for k in keys["governance"]["required"]:
                if k == "attested_by":
                    if not str(gov.get(k) or "").strip():
                        problems.append("governance.attested_by missing or empty")
                elif not isinstance(gov.get(k), bool):
                    problems.append(f"governance.{k} missing or not a bool")
            blk = gov.get("authorized_price_tuning")
            if blk is not None and not isinstance(blk, dict):
                problems.append(
                    "governance.authorized_price_tuning is neither null nor an object"
                )

    fp = att.get("free_parameters")
    if "free_parameters" in att:
        spec = keys["free_parameters"]
        if not isinstance(fp, dict):
            problems.append("free_parameters is not an object (dof-ledger/v1)")
        else:
            for k in spec["required"]:
                if k not in fp:
                    problems.append(f"free_parameters.{k} missing")
            entries = fp.get("entries")
            if not isinstance(entries, list):
                problems.append("free_parameters.entries is not a list")
            else:
                for i, e in enumerate(entries):
                    tag = f"free_parameters.entries[{i}]"
                    if not isinstance(e, dict):
                        problems.append(f"{tag} is not an object")
                        continue
                    for k in spec["entry_required"]:
                        if k not in e:
                            problems.append(f"{tag} ({e.get('name', '?')}) lacks {k!r}")
                    if (
                        e.get("identification") == "residual"
                        and not str(e.get(spec["entry_residual_requires"], "")).strip()
                    ):
                        problems.append(
                            f"{tag} ({e.get('name', '?')}) is residual without root_cause"
                        )

    exc = att.get("exceptions")
    if "exceptions" in att:
        if not isinstance(exc, list):
            problems.append("exceptions is not a list")
        else:
            for i, e in enumerate(exc):
                if not isinstance(e, dict):
                    problems.append(f"exceptions[{i}] is not an object")
                    continue
                for k in keys["exceptions"]["entry_required"]:
                    if k not in e:
                        problems.append(f"exceptions[{i}] lacks {k!r}")

    apt = att.get("authorized_price_tuning")
    if "authorized_price_tuning" in att:
        if not isinstance(apt, dict) or not isinstance(apt.get("declared"), bool):
            problems.append(
                'authorized_price_tuning must be an object with a bool "declared" '
                '({"declared": false} when no rule-1 band tuning is used)'
            )
        elif apt["declared"] != tuning_declared(att):
            problems.append(
                f"authorized_price_tuning.declared={apt['declared']} disagrees with "
                f"governance.authorized_price_tuning (well-formed={tuning_declared(att)})"
            )

    if "disclosures" in att and not isinstance(att["disclosures"], (dict, list)):
        problems.append("disclosures is neither an object nor a list")

    blocks = att.get("lane_blocks")
    if "lane_blocks" in att:
        if not isinstance(blocks, list) or not all(isinstance(b, str) for b in blocks):
            problems.append("lane_blocks is not a list of key names")
        else:
            for b in blocks:
                if b not in att:
                    problems.append(f"lane_blocks names {b!r} but no such key exists")
                elif _is_known_key(b, schema):
                    problems.append(
                        f"lane_blocks lists schema key {b!r}; list lane-named blocks only"
                    )
    listed = set(blocks) if isinstance(blocks, list) else set()
    for k in att:
        if not _is_known_key(k, schema) and k not in listed:
            problems.append(
                f"unlisted top-level key {k!r}: add it to lane_blocks or remove it"
            )
    return problems


def migrate_dict(att: dict) -> list[str]:
    """Additively bring ``att`` onto the schema in place; return the changes made.

    Never deletes or renames. Idempotent: a conforming attestation is returned
    unchanged with an empty change list.
    """
    schema = load_schema()
    changes: list[str] = []
    if not str(att.get("schema") or "").strip():
        att["schema"] = schema["schema_tag"]
        changes.append("schema: added version tag")
    if "exceptions" not in att:
        att["exceptions"] = []
        changes.append("exceptions: added []")
    if "disclosures" not in att:
        att["disclosures"] = {}
        changes.append("disclosures: added {}")
    want = {"declared": tuning_declared(att)}
    apt = att.get("authorized_price_tuning")
    if not isinstance(apt, dict):
        att["authorized_price_tuning"] = want
        changes.append(f"authorized_price_tuning: {apt!r} -> {want}")
    elif "declared" not in apt:
        apt["declared"] = want["declared"]
        changes.append(f"authorized_price_tuning.declared: added {want['declared']}")
    lane = [k for k in att if not _is_known_key(k, schema)]
    blocks = att.get("lane_blocks")
    if not isinstance(blocks, list):
        att["lane_blocks"] = lane
        changes.append(f"lane_blocks: added {lane}")
    else:
        new = [k for k in lane if k not in blocks]
        if new:
            blocks.extend(new)
            changes.append(f"lane_blocks: appended {new}")
    return changes


def migrate(path: Path) -> list[str]:
    """Migrate one attestation file on disk, preserving key order, indent and encoding."""
    raw = path.read_text(encoding="utf-8")
    att = json.loads(raw)
    changes = migrate_dict(att)
    if changes:
        ensure_ascii = "\\u" in raw  # keep the file's own escaping style
        out = json.dumps(att, indent=2, ensure_ascii=ensure_ascii)
        path.write_text(out + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
    return changes


def main(argv: list[str] | None = None) -> int:
    """CLI: ``--migrate`` (write) or ``--check`` (validate only) one or more files."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+", type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--migrate", action="store_true", help="additively migrate, then validate"
    )
    mode.add_argument(
        "--check", action="store_true", help="validate only; exit 1 on any violation"
    )
    args = ap.parse_args(argv)
    rc = 0
    for p in args.paths:
        if args.migrate:
            for c in migrate(p):
                print(f"{p}: {c}")
        problems = validate(json.loads(p.read_text(encoding="utf-8")))
        if problems:
            rc = 1
            print(f"{p}: INVALID\n  " + "\n  ".join(problems))
        else:
            print(f"{p}: valid ({load_schema()['schema_tag']})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
