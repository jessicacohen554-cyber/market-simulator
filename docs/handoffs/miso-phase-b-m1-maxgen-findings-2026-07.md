# MISO Phase B — M-1 max-gen-event registry: primary-source findings (F4)

**Date:** 2026-07-15. **Session:** `claude/miso-phase-b-execution` (Phase B).
**Scope:** M-1 of the price-formation lane
(`docs/handoffs/miso-price-formation-design-2026-07.md` §3/M-1) — the
`miso-maxgen-events` declared-event-window registry that M-2's CT/CC revealed
derates are scoped to. This memo records what the **primary sources** reachable
this session actually say, under the pre-declared **F4** discipline ("a window
with no primary document does NOT enter the registry; never reconstruct windows
from prices or from the residual").

## Headline: F4 is engaged — the registry cannot be authoritatively populated this session, and the design's Jan-2024 window is contradicted by the primary source.

Two independent blockers, both pre-declared as F4 triggers:

### 1. The authoritative declaration record (OASIS) is unreachable.

`oasis.oati.com/woa/docs/MISO/MISOdocs/Capacity_Emergency_Historical_Information.pdf`
— the standing "Maximum Generation Emergency Declarations" record and the design's
primary source #1 — returns **HTTP 502 (CONNECT tunnel failed)** through the
session's egress proxy (host not on the allowlist). This is the same failure
Phase A hit (503 on 2026-07-15). Per the proxy contract we do **not** route
around it. MISO's own site (`cdn.misoenergy.org`, `www.misoenergy.org`) returns
**403** (blocked). Only Potomac Economics (`potomaceconomics.com`, the SOM/IMM
source, ladder #3) is reachable (200).

### 2. The primary source (2024 MISO SOM) CONTRADICTS the design's Jan-2024 window.

The design (`miso-run66-triage-design-2026-07.md` §Issue-3; price-formation
§2) classifies **all 24 of 2024's DA tail hours (Jan 14-17)** as a
"winter arctic-blast **Maximum Generation Emergency** (Winter Storm Heather
window)" and makes it the driver of the expected 2024 C3c delta (4h -> [12,48]).

The **2024 MISO State of the Market report** (Potomac Economics, IMM — a primary
report, fetched this session:
`potomaceconomics.com/.../2024-MISO-SOM_Report_Body_Final.pdf`) states the
opposite for Winter Storm Heather (mid-January 2024):

> "MISO managed the system reliably... **MISO did not declare an emergency** or
> substantially overcommit resources." System-wide RT prices "peaked at just
> over $200/MWh"; wind set a ~26 GW record.

So the Jan-2024 tail hours are **real prices** but there was **no declared MISO
Maximum Generation Emergency** in Jan 2024. Under F4 (and rule 12 — no window
without a driver), **Jan-2024 cannot enter the registry as a declared max-gen
event** on the evidence reachable this session. It could still enter at a
*lower* ladder rung (Conservative Operations / Capacity Advisory) **iff** a
primary MISO document confirms one in that window — which requires the
OASIS/ops-deck sources that are currently blocked. The design's assumption that
Jan-2024 was an Emergency is **not supported by the primary source** and must
not be carried forward on Phase A's assertion alone.

Corollary: the arctic-blast Max Gen Emergency that search surfaces
(RTO Insider "MISO Enters Max Gen Emergency in Arctic Blast") is dated
**January 24, 2026** — **out of the 2023-2025 window** (and rule-22 quarantined),
not a 2024 event. Phase A appears to have conflated the (real) Jan-2024 price
tail with an emergency declaration that did not occur in 2024.

## What IS primary-confirmable this session

| year | window (design) | primary-source status this session |
|---|---|---|
| 2023 | Aug 24 Max Gen Event (1h tail) | **unconfirmed** — needs OASIS or 2023 SOM emergency table (not fetched) |
| 2024 | Jan 14-17 "Max Gen Emergency" | **CONTRADICTED** — 2024 SOM: no emergency declared (Winter Storm Heather) |
| 2025 | Jun 23-24 Max Gen Event | **confirmed at the event level** — MISO Midwest entered a Max Gen Emergency during the mid-June 2025 heat wave (SOM-summary + RTO Insider); exact hours need the OASIS/ops record |
| 2025 | Jul 24/28/29 advisory/warning | design says advisory-level, never a declared Event — needs the ops-deck ladder |
| 2025 | Jan cold-snap / Feb / Sep / Oct | **unconfirmed** — ladder-level declarations need OASIS/ops decks |

Only **one** window (Jun-2025 Max Gen Emergency, Midwest) is even event-level
confirmable this session, and its exact start/end hours still require the
blocked OASIS/ops-deck sources. A registry built from this alone would be a
single-window stub, and the composed-probe deltas that depended on the
Jan-2024 window (2024 C3c -> [12,48]) would not materialize.

## F4 consequence (pre-declared, not a retune)

Per design §5 F4: "if no primary document yields a ... vintage covering
Jun/Jul-2025 (or the Jan-2024 winter declarations), those windows are absent and
the expected deltas shrink accordingly — the lane reports the gap; it never
reconstructs windows from prices or from the residual." **This memo IS that
report.** The M-2 derate channel and the composed probe are therefore **deferred**
until the OASIS `Capacity_Emergency_Historical_Information.pdf` (or the MISO
monthly operations-report / Informational-Forum decks on `cdn.misoenergy.org`)
are reachable — an access item for the owner, not a modelling knob. The
`miso-maxgen-events` schema + curation scaffolding ships so the intake is
ready the moment those documents are in hand; it is intentionally **not
populated from prices or from Phase A's unverified assertions**.

## Owner action items

1. **Provide access to a primary MISO emergency-declaration record for 2023-2025**
   — either allowlist `oasis.oati.com` (the `Capacity_Emergency_Historical_Information.pdf`)
   / `cdn.misoenergy.org`, or drop the OASIS PDF + the relevant MISO monthly
   operations-report decks into `data/raw/miso-maxgen-events/`.
2. **Re-adjudicate the Jan-2024 window** against that record: confirm whether ANY
   ladder-level declaration (Conservative Operations / Capacity Advisory / Max Gen
   Alert) was issued Jan 14-17 2024. If none, the 2024 C3c window is genuinely
   absent and the price-formation lane's 2024 tail expectation must be revised
   (not force-closed).
3. Only then run M-2 + the composed probe.

## Rule fidelity

- Rule 1/11/13: no window is fit to the price residual; the registry admits only
  primary-documented declarations.
- F4 (pre-declared): engaged on its stated trigger (no primary vintage), not
  invented after a probe.
- Rule 22: all candidate windows are inside 2023-2025 (the Jan-24-**2026**
  arctic-blast emergency is explicitly excluded as out-of-window).
