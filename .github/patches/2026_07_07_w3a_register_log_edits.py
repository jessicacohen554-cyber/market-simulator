"""W3a carrier: apply the session's gap-register + calibration-log edits.

Run by .github/workflows/apply-w3a-seam-clock.yml alongside the code patch.
The register/log rows being edited are multi-kilobyte single lines, so a
unified diff of them cannot travel through the agent sandbox's MCP-only write
path without hand-transcribing giant mechanical lines (the corruption risk
the apply-export-cap.yml precedent exists to avoid). This script instead
addresses each edit by SHORT literal anchors into the checked-out files and
splices in the session's new text. Idempotent: an edit whose new text is
already present is skipped, so the carrier workflow can re-run freely.

Full forensics context:
results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "docs" / "gap-register-2026-07.md"
LOG = REPO / "docs" / "calibration-log.md"


def splice(text: str, start: str, end: str, replacement: str, key: str) -> str:
    """Replace the span [start..end] (inclusive) with ``replacement``.

    ``start``/``end`` must each occur exactly once at/after the span start.
    ``key`` is a distinctive substring of the new text used as the
    idempotency check.
    """
    if key in text:
        print(f"  skip (already applied): {key[:60]!r}")
        return text
    i = text.find(start)
    if i < 0 or text.find(start, i + 1) >= 0:
        raise SystemExit(f"anchor not unique/absent: {start[:80]!r}")
    j = text.find(end, i)
    if j < 0:
        raise SystemExit(f"end anchor absent after start: {end[:80]!r}")
    j += len(end)
    return text[:i] + replacement + text[j:]


def insert_after(text: str, anchor: str, insertion: str, key: str) -> str:
    """Insert ``insertion`` immediately after the unique ``anchor``."""
    if key in text:
        print(f"  skip (already applied): {key[:60]!r}")
        return text
    i = text.find(anchor)
    if i < 0 or text.find(anchor, i + 1) >= 0:
        raise SystemExit(f"anchor not unique/absent: {anchor[:80]!r}")
    i += len(anchor)
    return text[:i] + insertion + text[i:]


G15_NEW = (
    '**The drag\'s "scarcity-pricing half" is therefore NOT closable by any '
    "reserve-scarcity curve** — ~~re-attributed to the WECC seam diurnal shape "
    "(evening +2–3.2 GW over-import suppresses the premium; midday −1 to −1.8 GW "
    "under-import owns the C3a body)~~ **ATTRIBUTION WITHDRAWN (2026-07-07, W3a "
    'lane): it was a timezone artifact** — the seam FINDING\'s "measured actual" '
    "hod table was UTC-bucketed (reproduced to the MW in "
    "`FINDING-caiso-seam-tz-correction-2026-07-07.md`), inverting the "
    "model-vs-actual comparison. On the true clock the model **over**-imports the "
    "belly +2.5–3.3 GW against a mis-phased envelope cap (the per-DIBA stamps lag "
    "the model clock 1 h PST / 2 h PDT; envelope fixed at the read seam + guard "
    "script, A/B `caiso-65`), **under**-imports the overnight/evening contracted "
    "base −0.6–2.3 GW (price-gated: border-LMP + wheel + CARB wedge structurally "
    "deletes the revealed 4.3–5.9 GW self-scheduled base — the MISO-G-23 "
    "signature, here gated by the self-referential border price), and there is NO "
    "evening over-import suppressing the premium. **The C3a body reattributes to "
    "belly gas commitment**: measured CAISO runs 3.1–5.2 GW MORE gas through the "
    "belly than the model while printing $13–33 (committed-gas surplus sets a "
    "curtailment/import margin; the model's exact-fit belly is gas-marginal at "
    "$37–59). G-15's residual = (a) ground the real belly commitment (measured "
    "drivers: CEMS belly min-load patterns, must-offer/exceptional-dispatch "
    "records, AS-holding), (b) the seam's contracted evening/overnight base (DMM "
    "RA-import capacity is the firm blocks' basis and is undersized vs the "
    "revealed base; EIM transfer volumes / CARB specified-source imports are the "
    "measured objects), then (c) re-examine the drag's remaining carry. | "
    "registry `2026-07-06-caiso-59-lcr-proxy.json`, "
    "`2026-07-07-caiso-61-lolp-tail.json`, `2026-07-07-caiso-62-coopt-full.json`; "
    "docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §6–7; "
    "FINDING-caiso-seam-tz-correction-2026-07-07.md | B | open (re-attributed: "
    "belly commitment + seam contracted base) | SH (belly grounding + seam-base "
    "intake) |"
)

G20D_NEW = (
    "~~Root cause relocated with measured data: the WECC seam's diurnal delivery "
    "owns the C3a body and starves G-61's release signals~~ **RELOCATION "
    "WITHDRAWN (2026-07-07, W3a lane — timezone artifact; the seam FINDING's "
    "actual-flow table was UTC-bucketed, reproduced to the MW).** On the true "
    "clock the model over-imports the belly and under-imports the "
    "overnight/evening base; the C3a body reattributes to **belly gas "
    "commitment** (measured CAISO runs 3.1–5.2 GW more belly gas than the model "
    "while printing $13–33; the model's exact-fit belly is gas-marginal at "
    "$37–59) with the seam's contracted-base under-delivery second — see "
    "`FINDING-caiso-seam-tz-correction-2026-07-07.md` §4/§6 (the reserve-channel "
    "inertness results above stand untouched); **G-20e MISO**"
)

G61_COUPLING_NEW = (
    "~~**Coupling:** the seam's midday −1 to −1.8 GW under-import is WHY the "
    "price/curtailed-VRE release signals never fire — the seam fix is a "
    "precondition for §7's open paths~~ **COUPLING INVERTED (2026-07-07, W3a "
    "lane — the seam under-import was a timezone artifact; "
    "`FINDING-caiso-seam-tz-correction-2026-07-07.md`):** on the true clock the "
    "model already OVER-imports the belly +2.5–3.3 GW and still never curtails, "
    "so the release signals are starved by the *internal* belly balance, not by "
    "seam under-delivery. Moreover the measured belly runs 3.1–5.2 GW MORE gas "
    "than the model at $13–33 — the real market *over*-commits the belly "
    "relative to the model, which cuts against release mechanisms that decommit "
    "it. §7's open paths re-adjudicated: (a) RA-quantity gate from published RA "
    "contract data, (b) startup-aware bridge detection, (c) curtailed-VRE-volume "
    "release."
)

G61_B_CAVEAT_NEW = (
    "λ +$0.30–0.46 (the phantom floors were price-suppressing; 2023 tail "
    "502→530 h) — more faithful UC physics + a ~40% smaller RA forcing budget "
    "at a small honest C3a cost; KEEPER ADOPTION = OWNER DECISION** *(W3a "
    "caveat, 2026-07-07: the measured belly comparison — actual 3.1–5.2 GW MORE "
    "belly gas than the model at $13–33 — says CAISO's real belly is "
    "over-committed relative to the model, and caiso-63's λ moved AWAY from "
    "actual exactly as that predicts; weigh tz-correction FINDING §4.3 before "
    "adopting)*."
)

G61_C_REREAD_NEW = (
    "**probed `2026-07-07-caiso-64-g61c-curtail` — BYTE-IDENTICAL to base ×3 "
    "years (P0 never curtails a MWh of VRE 2023–25)**; ~~the exact "
    "seam-coupling prediction; stays built for the day the seam fix lands~~ "
    "*(W3a re-read: P0's zero curtailment persists DESPITE +2.5–3.3 GW belly "
    "over-import, so the starvation is the internal belly balance — (c) stays "
    "built but is blocked on the belly-commitment grounding (G-15 residual "
    "(a)), not on any seam fix)*."
)

G61_TAIL_NEW = (
    "Full record: D-8 closure §8. | "
    "docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §7–8; "
    "results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md; "
    "registry `2026-07-07-caiso-63-g61b-startup.json` / "
    "`2026-07-07-caiso-64-g61c-curtail.json`; constants.CAISO_RA_MUSTOFFER_GAS_MW "
    "| B | blocks-claim (C1/C4 CC over-run) | open, re-adjudicated (adopt-(b) "
    "owner decision now carries the W3a belly caveat; (c) blocked on "
    "belly-commitment grounding, not the seam) |"
)

LOG_ENTRY = """### 2026-07-07 — CAISO — W3a seam-clock forensics: the seam-diurnal attribution was a timezone artifact (WITHDRAWN); corridor-envelope clock fixed in the LP (`caiso-65` A/B); C3a body reattributed to belly gas commitment — keeper stays caiso-60

**Lane:** caiso-seam-diurnal-shape-w3a, commissioned to build the
FINDING-caiso-seam-diurnal fix (neighbor evening-scarcity withdrawal). The
pre-build evidence pass instead **falsified the FINDING's central table**: its
"measured actual" hod column reproduces to the MW as the UTC-hod bucketing of
EIA-930 −TI (2023 h0/h12/h19/h21 = 948/5,131/669/200 vs the quoted
955/5,131/669/200), 7–8 hours out of phase with the model column. The
commissioned mechanism was therefore **not built** (it would have tuned the
seam toward the artifact — real evening flows RISE into the neighbors' peak;
rule 13). Full forensics: `results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md`
(supersedes §2/§5 of the seam FINDING; banner added there; G-15/G-20d/G-61
register rows corrected).

**Layer-2 discovery (in-LP, fixed + A/B'd).** The CISO per-DIBA interchange
parquet's `local_time` stamps lag the model's hourly frame by a measured 1 h
(standard) / 2 h (daylight) — lag-scan corr 0.972/0.961 at −1/−2 vs ≤0.930
elsewhere; the model frame itself is wall-true (January solar exactly within
astronomical daylight {7..16}; 2024-04-08 eclipse dip exactly at hod 11). The
keeper's measured (month × hod) p95 corridor envelope therefore reached the LP
1–2 h late. Fixed at the read seam (`eia_loader._caiso_interchange_model_clock`,
pinned constants + unit tests) and guarded by
`scripts/validate_caiso_seam_hod_frame.py`, which re-measures the lag from
source and fails on drift (a re-fetched parquet with honest stamps cannot be
silently double-shifted). A/B at HEAD, all years, one bundle:
the registered caiso-61 recipe re-solved as the base arm (its corridor hods
reproduce the seam FINDING's model column exactly) vs
`caiso65_seam_envelope_clock` (single-delta envelope-clock fix): hod-mean
corridor-flow error improves every year (mean |Δ| 1,402→1,362 / 1,803→1,692 /
1,979→1,816 MW), concentrated at the phase edges (h9 over-import −508/−620/
−670 MW; h18 under-import +504/+293/+146 toward the real base), λ a near-wash
(±$0.0–0.8 by hod) — the pre-registered expectation, since the envelope is
rarely price-setting and the body is internal. caiso-65 registered per rule
15 with its `--zero-forcing-ablation` twin.

**True residual (both sides on the model clock).** Midday +2.5–3.3 GW
OVER-import at the (previously mis-phased) envelope cap; overnight/evening
−0.6–2.3 GW UNDER-import, price-gated (border-LMP + wheel + CARB wedge —
2023 DSW_CCGT ≈ hub+$16.2 — structurally deletes the revealed 4.3–5.9 GW
contracted/self-scheduled base; the MISO-G-23 signature at a self-referential
border price); NO evening over-import. Model solar ≈ measured (the "phantom
evening solar cliff" seen mid-forensics was a frame misread of the fueltype
file — the HSL profiles are eclipse-verified). **The C3a body's worst bucket
reattributes to belly gas commitment:** measured CAISO runs 3.1–5.2 GW MORE
gas through the belly than the model while printing $13–33 (committed-gas
surplus → curtailment/import margin) where the model's exact-fit belly is
gas-marginal at $37–59. Consequences threaded into G-15 (residual = belly
commitment grounding + seam contracted base), G-61 (coupling inverted;
caiso-63 adoption now carries a belly caveat; (c) blocked on the belly, not
the seam), G-20d (relocation withdrawn; reserve-channel inertness stands).
Open data-provider question filed: the EIA-930 extract's `Demand` column sits
+1 h from the OASIS SLD frame while its generation columns are
astronomy-exact (model internally consistent either way).

"""

LOG_ADDENDUM = """
*[SUPERSEDED same day — the "measured actual" flow table under this paragraph was
UTC-bucketed; the attribution inverts on the true clock. See the W3a entry above and
`FINDING-caiso-seam-tz-correction-2026-07-07.md`; the caiso-61/62 probe results in this
entry stand.]*"""


def main() -> None:
    print("gap-register edits:")
    reg = REGISTER.read_text()
    reg = splice(
        reg,
        '**The drag\'s "scarcity-pricing half" is therefore NOT closable by any '
        "reserve-scarcity curve — re-attributed to the WECC seam diurnal shape**",
        "| SH (seam intake + probe) |",
        G15_NEW,
        "ATTRIBUTION WITHDRAWN (2026-07-07, W3a lane)",
    )
    reg = splice(
        reg,
        "Root cause relocated with measured data: the WECC seam's diurnal delivery",
        "fix prediction; **G-20e MISO**",
        G20D_NEW,
        "RELOCATION WITHDRAWN (2026-07-07, W3a lane",
    )
    reg = splice(
        reg,
        "**Coupling (FINDING-caiso-seam-diurnal-2026-07-07.md):** the seam's "
        "midday −1 to −1.8 GW under-import is WHY",
        "(c) curtailed-VRE-volume release.",
        G61_COUPLING_NEW,
        "COUPLING INVERTED (2026-07-07, W3a lane",
    )
    reg = splice(
        reg,
        "λ +$0.30–0.46 (the phantom floors were price-suppressing; 2023 tail "
        "502→530 h)",
        "KEEPER ADOPTION = OWNER DECISION.**",
        G61_B_CAVEAT_NEW,
        "W3a caveat, 2026-07-07: the measured belly comparison",
    )
    reg = splice(
        reg,
        "**probed `2026-07-07-caiso-64-g61c-curtail` — BYTE-IDENTICAL to base",
        "stays built for the day the seam fix lands.**",
        G61_C_REREAD_NEW,
        "W3a re-read: P0's zero curtailment persists DESPITE",
    )
    reg = splice(
        reg,
        "Full record: D-8 closure §8. | "
        "docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §7–8; "
        "results/calibration/FINDING-caiso-seam-diurnal-2026-07-07.md;",
        "| open, narrowed (adopt-(b) owner decision + seam fix unblocks (c)) |",
        G61_TAIL_NEW,
        "open, re-adjudicated (adopt-(b) owner decision now carries",
    )
    REGISTER.write_text(reg)
    print("  register: OK")

    print("calibration-log edits:")
    log = LOG.read_text()
    log = insert_after(
        log,
        "## Runs\n\n",
        LOG_ENTRY,
        "W3a seam-clock forensics: the seam-diurnal attribution was a timezone",
    )
    log = insert_after(
        log,
        "**Root cause relocated (G-20d → seam; "
        "`FINDING-caiso-seam-diurnal-2026-07-07.md`).**",
        LOG_ADDENDUM,
        'SUPERSEDED same day — the "measured actual" flow table',
    )
    LOG.write_text(log)
    print("  calibration-log: OK")


if __name__ == "__main__":
    sys.exit(main())
