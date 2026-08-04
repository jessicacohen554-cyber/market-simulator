"""Append the caiso-166 entry to ``docs/calibration-log/caiso.md`` (rule 15 record).

**Why this exists instead of the edit being committed directly.** ``git push``
was unusable in the caiso-166 session — the origin returned HTTP 413 for *every*
push, including a no-op ref advance whose request body was 4 bytes, because git
sends the receive-pack RPC with ``Transfer-Encoding: chunked`` and the origin
rejects any chunked body. The working transport,
``mcp__github__push_files``, is text-only with a ~457 KB cap, and
``docs/calibration-log/caiso.md`` is **380 KB**, so the file itself could not be
pushed whole.

**Why an anchored applier and not a diff.** The first carrier for this edit WAS
a ``git diff`` patch, and it went stale within the session: a caiso-167 session
appended its own entry to the same file, moving the tail the patch was cut
against, and ``git apply`` refused it. The calibration log is a hot,
append-only file that several lanes touch at once, so a positional diff is the
wrong shape for it. This applier instead anchors on the file's LAST
``Next number:`` trailer, inserts the caiso-166 entry immediately above it, and
leaves that trailer's own text to whichever session owns it — except for
dropping the now-stale "caiso-166 unclaimed/in-flight" note, which this entry
resolves.

Idempotent: re-running is a no-op. Refuses rather than force-fits if the
trailer anchor is missing.

Run from the repo root::

    python results/calibration/_caiso166_apply_calibration_log.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LOG = Path("docs/calibration-log/caiso.md")

#: Present iff the entry has already been appended.
SENTINEL = "## caiso-166 — five MEASURED loss zones (Arm A)"

#: The entry, exactly as authored in the caiso-166 session.
ENTRY = "---\n\n## caiso-166 — five MEASURED loss zones (Arm A): the surface is KEPT, the arm is NOT PROMOTED\n\n**2026-08-04** · branch `claude/caiso166-measured-loss-zones-uwsq1n` · base `3bc37ce2`\n· prereg `PRECHECK-caiso166-measured-loss-zones-2026-08-04.md` (pushed at `6c2dbfd5`,\n**before either arm solved**) · arms `2026-08-04-caiso-166-measured-dlap` /\n`2026-08-04-caiso-166-control-hubsurface`.\n\n**KEEPER UNCHANGED: `2026-08-04-caiso164-zonal-loss-surface`.** Determination\n**NOT-YET**.\n\nCloses `FINDING-caiso164` §7 caveat 2 on the data side: `LA_BASIN` →\n`DLAP_SCE-APND` and `SDGE` → `DLAP_SDGE-APND`, replacing the `TH_SP15_GEN`\n**generation**-hub deviation both **load** pockets inherited. Rule 23\n`[R-FROZEN-DERIVE]` licence is the **source-data change** (the caiso-165 intake),\nnot a residual; estimator, schema and every threshold unchanged. The A/B delta is\na **DATA FILE** — `caiso_zonal_loss_surface` is `True` in **both** arms and config\ndrift vs the same-HEAD control is **zero of any kind**.\n\n**NOT PROMOTED on two pre-registered gates, neither relaxed after it fired:**\n1. **S3 adversarial ceiling BREACHED** — 2025 `LA_BASIN−SP15_rest` moved\n   `+1.0205` vs measured `dMCL` `+0.9686` = **105.4 % of ceiling**.\n2. **C3a mean LMP regresses 2024 PASS → FAIL** (+9.5 % → +11.5 %, ±10 % band);\n   the incumbent's ledgered `price_mean` exception covers **2025 only**.\n\n**The S3 breach is a GATE-SPECIFICATION defect, not a mechanism one.** The LP\ntracks the **surface-implied** separation at **0.914–1.011×** — never\nmeaningfully above it — while the surface itself sits **1.038–1.042×** above\nmeasured `dMCL`, which is the MCE-weighted estimator's own positive bias, the\nsame ≈+4 % the derive's `[0.5×, 1.5×]` acceptance band *accepts* and caiso-164\npassed on. 105.4 % = 1.042 × 1.011. A ceiling at exactly `1.00×` holds the LP\n**tighter than the derive's own accepted tolerance**. Re-charter it\n**PROSPECTIVELY** or not at all — that is an owner call.\n\n**Gates that PASSED, and they are not weak.** **S1 placebo**: 2023's surface rows\nare identical in both arms, and the two 2023 solves agree to **EXACTLY 0.0** on\nprice, class dispatch **and** flows — a falsifiable check that the CSV is the only\nobject differing. **S2 liveness on FLOWS**: the control carries **48.2/56.4/59.4\nTWh** on `SP15_rest→LA_BASIN` (8,760 of 8,760 h) and **7.6/7.4/6.9 TWh** on\n`SP15_rest→SDGE`; identical link counts; **zero** hours over any caiso-163\npublished cap. **S4**: `mode=backcast` both arms; the one incumbent-only field\n(`pjm_seam_envelope_by_neighbor`) is admitted only after asserting it is no longer\na `ScenarioConfig` field at all (upstream pjm-152 rule 26 `[R-DELETE]`). **C7/C8\nPASS** — diagnostics generated into both bundles before registration.\n\n**Pre-solve data gates:** acceptance **12/12** in band with the four pre-existing\npair-years reproducing caiso-164's 1.04–1.06× **exactly**; `NP15`/`ZP26`/\n`SP15_rest` **bit-identical** (0 diffs across 96 rows each); **48 of 240** rows\nchange.\n\n**The surface is KEPT regardless (rule 14, pre-committed).** λ rises +1.82 %\n(2024) / +2.06 % (2025) — physically obligatory, since losses consume MWh. CAISO\nwas **already** +9.5 %/+12.1 % hot vs RT; the arm pushed a pre-existing bias\nacross a line it was already touching. That is a **discovered bug elsewhere**,\nnever grounds to revert. (Against CAISO's own **DA** basis — which is what the\nsurface is derived on — the control sits −0.1 %/+9.0 % and the arm +1.8 %/+11.3 %.)\n\n**⚠ OPEN FOR OWNER:** the committed surface and the caiso-164 keeper (solved on\nthe *old* surface) now disagree, so **the keeper no longer reproduces from the\nrepo**. Arm A *is* that keeper's recipe on the corrected data. Reverting the CSV\nwould leave the committed derive and artifact disagreeing and would bury a\nknown-wrong input — both worse.\n\n**⚠ DELIVERY GAP:** `git push` returns **HTTP 413 for every push in this\ncontainer**, including a no-op ref advance with a **4-byte** body (git sends the\nRPC `Transfer-Encoding: chunked`; the origin rejects any chunked body — a direct\n4-byte POST to the same endpoint returns 200). `push_files` works and every blob\nwas hash-verified, but it is text-only with a ~457 KB cap, so the **674/677 KB\n`runs/*.js` payloads and the binary parquet sidecars are NOT on the remote**.\nRegistry sidecars were deliberately **withheld** rather than pushed alone (a\nsidecar without its payload is silently invisible in the Run Explorer), and the\ntop-15 prune was reverted locally for the same reason.\n\n**DO-NOT-REDO:** do not re-test the `caiso_zonal_loss_surface` **mechanism** — it\nwas not re-tested here, only its input data, and the cell stays `K`. Do not\nre-cut the S3 ceiling retroactively. Do not arm Arm B from the residual; no\npublished intra-SP15 limit is in `data/raw` and the prohibition binds harder now\nthat the target numbers are known. Do not charter an N–S topology lever.\n\nEvidence: `results/calibration/FINDING-caiso166-measured-loss-zones-2026-08-04.md`,\n`PRECHECK-caiso166-measured-loss-zones-2026-08-04.md`,\n`scripts/gen_caiso166_attestation.py`,\n`results/calibration/caiso166_measured_loss_zones/calibration_attestation.json`.\n"

#: The trailer's stale in-flight note, resolved by this entry.
STALE_TRAILER = "caiso-160 and caiso-166 unclaimed/in-flight"
FRESH_TRAILER = "caiso-160 unclaimed"


def main() -> int:
    """Insert the caiso-166 entry above the log's last trailer; 0 on success."""
    if not LOG.is_file():
        print(f"FATAL: {LOG} not found — run from the repo root", file=sys.stderr)
        return 2
    src = LOG.read_text()

    if SENTINEL in src:
        print("already applied — nothing to do")
        return 0

    matches = list(re.finditer(r"^Next number: .*$", src, flags=re.M))
    if not matches:
        print(
            "FATAL: no 'Next number:' trailer found in "
            f"{LOG} — the log's shape changed. Insert the caiso-166 entry by "
            "hand (see FINDING-caiso166-measured-loss-zones-2026-08-04.md); do "
            "NOT force-fit it.",
            file=sys.stderr,
        )
        return 1

    at = matches[-1].start()
    out = src[:at] + ENTRY + "\n" + src[at:]
    out = out.replace(STALE_TRAILER, FRESH_TRAILER)
    LOG.write_text(out)
    print(f"appended the caiso-166 entry to {LOG} above its last trailer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
