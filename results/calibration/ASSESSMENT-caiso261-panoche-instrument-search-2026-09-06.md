# ASSESSMENT — caiso-261: the Panoche obligation-instrument search — **NOT FOUND**. The only public instrument is a 20-year PG&E tolling PPA (CPUC-approved 2006; PG&E "dictates when the facility will be operated") — a bilateral dispatch right with no published window, not an RMR / CPM / exceptional-dispatch obligation. ZERO LP; nothing armed; no pin.

**Owner decision (card, 2026-09-06): "Run the instrument search — search
CAISO RMR/CPM designations, exceptional-dispatch reports and CPUC filings
for a Panoche obligation 2023-2025; report found / not found. No pin, no
re-pricing either way."**

## §1 — The object

Panoche Energy Center (EIA 56803, NP15, 4 × GE LMS100, ~400 MW, COD
2009-07-01) runs 87–211 MW overnight for 3,000–4,800 h/yr — 0.74 / 1.42 /
0.85 TWh actual vs 0.16 / 0.13 / 0.05 TWh model, **39 / 68 / 86 % of the
CEMS-basis CT volume miss** (caiso-252 §3.3). caiso-119 R4: a per-plant
commitment is admissible **only** through a public obligation instrument
with a cited D-4 window; never a pin (rules 13, 21).

## §2 — What was searched, what was found

| record | result |
|---|---|
| CAISO **CPM designations** (e.g. the 2023-11-02 designation notice: SYCAMR_2_UNIT 3, 70 MW, 60 days, SCE 230 kV overload) | Panoche **not** named |
| CAISO **RMR** contract list / 2022 conditional RMR extension decision | Panoche **not** named (the RMR fleet is the Oakland / coastal units) |
| CAISO **exceptional-dispatch reports** (FERC Tables 1/2, monthly; Jan-2024 Table 2 read in full, 20 pp, 0 hits for "PANOCH") | the tables report ED by **reason and MWh**, not by resource; **no resource is named** in the published series, so ED cannot ground a per-plant window from the public record |
| **CPUC / court record** | the PG&E–Panoche PPA executed 2006-03-28, CPUC-approved Nov-2006: a **20-year tolling agreement** (PG&E supplies the gas, "dictates when the facility will be operated and how much electricity will be generated"; *Panoche Energy Center, LLC v. PG&E*, Cal. Ct. App. 2016). Term runs to ~2029. Terms redacted; no minimum-run, must-offer or window published |

**Verdict: NOT FOUND.** The plant's 3,000–4,800 h/yr overnight conduct is
PG&E's dispatch under a tolling PPA — a **contractual self-schedule**, not
a reliability obligation keyed to a public window. Under caiso-119 R4 a
tolling right is not an admissible floor driver: it names no hours, no
trigger and no regenerating forward condition (the PPA expires 2029 and its
successor is unknown), so any floor built on it would be a plant-level pin
of observed conduct (rule 13) with a fitted window (rule 17).

## §3 — What this leaves

* The CT volume miss stays where caiso-252 §3.3 and caiso-257 §10 #4 left
  it: mostly one plant's commitment, un-groundable from the public record.
* One measured route exists and is **not** a pin: Panoche's DA
  **self-schedule** is visible in `PUB_DAM_GRP` (masked ids, persistent
  `RESOURCEBID_SEQ`) — but the caiso-150 §B wall (no public crosswalk to a
  masked id) means it cannot be attributed to Panoche, and a fleet-wide
  measured self-schedule floor for CT would be the very thing the CT class
  D-2/D-4 machinery already guards. Not proposed.
* Owner decision: **close as un-groundable** (declared residual; DO-NOT-REDO
  without new evidence such as a public RMR/CPM designation after 2029 or a
  published PPA term) — or **carry**.

## §4 — OWNER RULING (card, 2026-09-06): "Close as un-groundable"

**Ruled.** The CT volume miss — Panoche 39 / 68 / 86 % of it — is recorded
as a **permanent declared residual** on the CAISO keeper
(`keepers/CAISO.json` `declared_residual_ct_volume`): no floor, no pin, no
class re-pricing, no window may be built to reach it. **DO-NOT-REDO** without
new *public* evidence — a post-2029 RMR / CPM designation naming the plant,
a published PPA term with dispatch hours, or a resource-named exceptional
dispatch record. Genealogy: caiso-119 R4 (guardrail) → caiso-252 §3.3 (one
plant) → caiso-257 §10 #4 (deepened, not closed) → **caiso-261 (search run,
NOT FOUND, closed)**.

