"""miso-159 executor finalizer — fully self-contained (reads finalize_data.json).

Run from the repo root AFTER: (a) pack diff #1 applied + hash-verified,
tests + probe green; (b) both bundles re-solved (control then arm) and the
scorecard cross-checked against results/calibration/_miso159_authoring_scorecard.json
(written by step 1 below). It deterministically reconstructs every remaining
authoring-session edit from the repo's own committed state + the embedded
texts, and verifies EVERY output against the authoring session's git blob
hashes — any mismatch raises (stop-the-line, CLAUDE.md rule 27).

Steps: (1) write the scorecard + the arm's calibration_attestation.json
(built from the keeper miso148_basis_B's attestation + the authored
replacement strings); (2) pin both bundles' meta timestamps so run ids mint
identically; (3) register both runs (dashboard_add_run — regenerates
sidecars/payloads/bench, prunes miso-122b/-124); (4) restore the arm
sidecar's market_story; (5) promote the keeper shard
(keepers/MISO.json: keeper id + promotion_note + note prepend); (6) append
the calibration-log entry; (7) re-stamp the §5.4 prose header; (8) MISO
matrix-shard surgery (updated/keeper/gates/K-cell); (9) fix-anchors; then
verify the full manifest.

After this: python scripts/build_status.py --iso MISO; python
scripts/audit_keepers.py --iso MISO; python
scripts/check_registry_payload_parity.py; delete .claude-transfer/miso159;
commit + push (payload commits over git push; on 408/500/disconnect set
`git config http.version HTTP/1.1` and retry).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
D = json.loads((HERE / "finalize_data.json").read_text())

TIMESTAMPS = {
    "results/calibration/miso159_cod_A": "2026-08-15T22:39:56",
    "results/calibration/miso159_cod_B": "2026-08-15T23:14:36",
}
LABELS = {
    "results/calibration/miso159_cod_A": "miso 159 control",
    "results/calibration/miso159_cod_B": "miso 159 cod vintage",
}
OLD_PROSE_HEADER = (
    "### 5.4 MISO — target the **2024/2025 MEAN-LMP LEVEL MISS** (owner "
    "directive 2026-08-06; C7 COAL_PRB is DEPRIORITIZED by owner order and is "
    "NOT a lane) — keeper `2026-08-09-miso-148-basis-aware`, **NOT-YET**\n\n"
)
MANIFEST = {
    "docs/calibration-log/miso.md": "6b82e830e2d6c1eddef34c0ec79162f2d069ff41",
    "frontend/data/backcast/keepers/MISO.json": "181c7c89071d1824f38d0360b10f47458e37a8d7",
    "docs/codebase-site/data/mechanism-matrix/MISO.js": "0176f3dca594cf2a6981285b58ac3f02dc4ab7b5",
    "docs/mechanism-testing-matrix.md": "d04d3e904901c828f46bfb3cb2fba9e6c9acc475",
    "docs/codebase-site/data/mechanism-matrix.js": "5fb8f4fc69ceb7fa7e8cec3db81820be9611897f",
    "results/calibration/miso159_cod_B/calibration_attestation.json": "cdfefc03bc23f5a4402d4286f27adcfa4933d626",
    "results/calibration/_miso159_authoring_scorecard.json": "9ac166819654c4ee5307c9f753289a52aa83fa2d",
    "frontend/data/backcast/registry/2026-08-15-miso-159-cod-vintage.json": "6bc90ad83dd99c1b1a515ed86fd485b0611d086b",
    "frontend/data/backcast/registry/2026-08-15-miso-159-control.json": "fafa8e2ace328f567787a38998f36cc90f5ef1fa",
    # FINDING ships as a pushed file alongside this pack; verified here too.
    "results/calibration/FINDING-miso159-commission-year-cod-repair-2026-08-15.md": "5448a83128c39378e63a48ece38e499ea4d71bca",
}


def sh(*args: str) -> str:
    r = subprocess.run(args, capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        raise SystemExit(
            f"command failed: {args}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}"
        )
    return r.stdout


def blob(path: str) -> str:
    return sh("git", "hash-object", path).strip()


def verify(paths) -> None:
    bad = [(p, blob(p), MANIFEST[p]) for p in paths if blob(p) != MANIFEST[p]]
    if bad:
        for p, got, want in bad:
            print(f"HASH MISMATCH {p}: got {got} want {want}")
        raise SystemExit("stop-the-line: manifest mismatch (rule 27)")
    print(f"verified {len(list(paths))} manifest hash(es)")


def step1_artifacts() -> None:
    (REPO / "results/calibration/_miso159_authoring_scorecard.json").write_text(
        D["scorecard"]
    )
    src = json.loads(
        (
            REPO / "results/calibration/miso148_basis_B/calibration_attestation.json"
        ).read_text()
    )
    src["governance"]["attested_by"] = D["attested_by"]
    src["disclosures"]["note"] = D["disclosure_note"]
    out = REPO / "results/calibration/miso159_cod_B/calibration_attestation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(src, open(out, "w"), indent=1)
    verify(
        [
            "results/calibration/_miso159_authoring_scorecard.json",
            "results/calibration/miso159_cod_B/calibration_attestation.json",
        ]
    )


def step2_timestamps() -> None:
    for bundle, ts in TIMESTAMPS.items():
        mp = REPO / bundle / "meta.json"
        m = json.loads(mp.read_text())
        if m.get("timestamp") != ts:
            m["timestamp"] = ts
            mp.write_text(json.dumps(m, indent=2))
            print(f"pinned {bundle} -> {ts}")


def step3_register() -> None:
    for bundle, label in LABELS.items():
        out = sh(
            sys.executable,
            "scripts/dashboard_add_run.py",
            "--label",
            label,
            "--bundle",
            bundle,
        )
        for line in out.splitlines():
            if line.startswith(("RUN_ID=", "DETERMINATION:")) or "prune" in line:
                print(" ", line)


def step4_market_story() -> None:
    p = REPO / "frontend/data/backcast/registry/2026-08-15-miso-159-cod-vintage.json"
    d = json.loads(p.read_text())
    d["market_story"] = D["market_story"]
    p.write_text(json.dumps(d, indent=1))
    verify(
        [
            "frontend/data/backcast/registry/2026-08-15-miso-159-cod-vintage.json",
            "frontend/data/backcast/registry/2026-08-15-miso-159-control.json",
        ]
    )


def step5_keeper_shard() -> None:
    p = REPO / "frontend/data/backcast/keepers/MISO.json"
    d = json.loads(p.read_text())
    if d["keeper"] != "2026-08-15-miso-159-cod-vintage":
        assert d["keeper"] == "2026-08-09-miso-148-basis-aware", d["keeper"]
        d["keeper"] = "2026-08-15-miso-159-cod-vintage"
        d["promotion_note"] = D["promotion_note"]
        d["note"] = D["own_delta_para"] + "\n\n" + d["note"]
        json.dump(d, open(p, "w"), indent=1)
    verify(["frontend/data/backcast/keepers/MISO.json"])


def step6_log() -> None:
    p = REPO / "docs/calibration-log/miso.md"
    txt = p.read_text()
    if "## miso-159 (2026-08-15)" not in txt:
        assert txt.endswith("**Next number: miso-156.**\n")
        p.write_text(txt + D["log_append"])
    verify(["docs/calibration-log/miso.md"])


def step7_prose() -> None:
    p = REPO / "docs/mechanism-testing-matrix.md"
    txt = p.read_text()
    if "2026-08-15-miso-159-cod-vintage" not in txt:
        assert OLD_PROSE_HEADER in txt
        txt = txt.replace(OLD_PROSE_HEADER, D["new_header_block"], 1)
        p.write_text(txt)
    verify(["docs/mechanism-testing-matrix.md"])


def step8_shard() -> None:
    p = REPO / "docs/codebase-site/data/mechanism-matrix/MISO.js"
    txt = p.read_text()
    if 'commission_year_cod_fallback: { cell: "K"' not in txt:
        txt = txt.replace('  updated: "2026-08-14",', '  updated: "2026-08-15",', 1)
        txt = txt.replace(
            '  keeper: "2026-08-09-miso-148-basis-aware",',
            '  keeper: "2026-08-15-miso-159-cod-vintage",',
            1,
        )
        txt = txt.replace('  gates: "', '  gates: "' + D["gates_stamp"], 1)
        m = re.search(r'(    summer_derate_basis_aware: \{ cell: "K"[^\n]*\},\n)', txt)
        assert m, "summer_derate K-cell anchor not found"
        txt = txt[: m.end(1)] + D["k_cell_line"] + txt[m.end(1) :]
        p.write_text(txt)
    verify(["docs/codebase-site/data/mechanism-matrix/MISO.js"])


def step9_anchors() -> None:
    sh(sys.executable, "scripts/check_mechanism_matrix.py", "--fix-anchors")
    verify(["docs/codebase-site/data/mechanism-matrix.js"])


def main() -> None:
    step1_artifacts()
    step2_timestamps()
    step3_register()
    step4_market_story()
    step5_keeper_shard()
    step6_log()
    step7_prose()
    step8_shard()
    step9_anchors()
    verify(list(MANIFEST))
    print(
        "finalize_miso159: ALL VERIFIED — run build_status/audit/parity, delete .claude-transfer/miso159, commit + push"
    )


if __name__ == "__main__":
    main()
