# caiso-191 — OWNER RULINGS RECORD (Wave 0C, CAISO close-out campaign) — 2026-08-11

**This document RECORDS rulings the owner gave on 2026-08-11 via the orchestrating
session. They are quoted as RULINGS, not proposals — nothing below is re-argued, and
nothing below is this session's recommendation.** The decision packets they answer are
`docs/handoffs/caiso-186-owner-sitting-2026-08-09.md` (§a, §b, §4, §5) and
`FINDING-caiso187-wefor-overlay-2026-08-09.md` §6.

Session caiso-191 is READ-AND-WRITE-DOCS ONLY: no code, no config, no keeper, no
status, no attestation file touched; no solve run; no matrix cell verdict moved.
Keeper unchanged at **`2026-08-09-caiso-188-d1-micseam`** (NOT-YET; C3a the sole
load-bearing FAIL at +3.4 / +10.4 / +12.9 % vs ±10 %; required falls to the band:
2024 −$0.16/MWh, 2025 −$1.01/MWh — verified by arithmetic from the caiso-189
refreshed magnitudes 38.27 vs 34.65 and 38.87 vs 34.42). C3a was never read as a
number to act on; it appears here only as the recorded state of the keeper.

---

## The seven rulings

1. **caiso-187 option 1 — the overlay mechanical-vs-economic identification:
   GRANTED.** The CAMPD outage overlay's downtime-vs-unavailability separation
   (FINDING-caiso187 §3, §6 option 1) is authorized as a measurement lane. It is
   chartered with the direction hazard stated, exactly as caiso-187 required. Gate
   spec: `GATESPEC-caiso192-overlay-identification-2026-08-11.md` (lane 1).

2. **caiso-187 option 2 — the narrow arm: GRANTED.** `wefor_residual = 0.0` scoped to
   `{CC_REGULAR, CC_CHP}` via `wefor_residual_groups`, with `wefor_multiplier`
   returned to 1.0 — the gate-consistent (G-NODOUBLE-dominant) reading of the frozen
   caiso-187 §2 formula. **Both grants are independent, per the FINDING** (§6: "Option
   1 and option 2 are independent and can both be granted"). Gate spec:
   `GATESPEC-caiso193-wefor-residual-2026-08-11.md` (lane 2), which also carries the
   cure of the caiso-187 §4 pre-registration defect.

3. **`caiso_storage_nqc_accreditation` arming: DEFERRED.** The field stays gate-off.
   Gate-off is proved exactly inert (`KeeperInertnessTest`; default cache key
   `603c2498bf71d21d` unmoved — owner-sitting §4), so deferral carries zero cost. It
   is OUT of this campaign; arming remains its own future session in the CAISO lane.

4. **Hourly PS water-state intake purchase: DECLINED.** The caiso-141 wall stands
   (re-verified live 5/5 at the owner sitting). **No purchased data in this
   campaign.** Fabricated PS shapes remain forbidden (rule 13 `[R-MEASURED]`;
   caiso-141 §G — deriving an hourly PS shape from monthly nets, from the model's own
   arbitrage profile, or from any assumed/fitted allocation is an outcome-pin wearing
   a data costume).

5. **Rubric amendment to ledger C3a: DECLINED.** C3a must genuinely pass; **NOT-YET is
   the honest fallback.** The v3.1 restriction (`LEDGERABLE_CRITERIA = {price_tail}`)
   stands; the owner-sitting §b.2 inheritance arithmetic (ERCOT −32.4 %, MISO flips
   for free, budget 1 → 2 doubles every ISO's excuse capacity) is accepted as decisive.

6. **C3c: remains the accepted ledgered caveat.** The standing rule (owner 2026-08-06,
   extended to every year 2026-08-09) governs; the exceptions are carried in the
   keeper attestation as of caiso-189, with magnitudes measured on the current bundle.
   Note for wave 2: a promotion attestation **re-measures** the C3c exceptions on the
   new bundle — verbatim carry of a superseded bundle's magnitudes would be a false
   attestation (the caiso-189 §8.3 precedent).

7. **Lane 5 (PS cited-physical parameters): CONDITIONALLY AUTHORIZED**, subject to
   caiso-191's adjudication against (a) the caiso-140 §D/§G DO-NOT-REDO and (b) the
   caiso-141 §G fabricated-shape prohibition, with **default NO-GO if ambiguous**.
   *Adjudicated this session: **GO, with scope restrictions** — the full argument both
   ways and the restrictions are in
   `FINDING-caiso191-campaign-adjudication-2026-08-11.md` §3 and
   `GATESPEC-caiso195-ps-physical-2026-08-11.md`.*

---

## The campaign charter — the lane inventory is CLOSED

The Wave-1 measurement lanes are, exhaustively:

| lane | object | gate spec | session |
|---|---|---|---|
| 1 | overlay mechanical-vs-economic identification | `GATESPEC-caiso192-overlay-identification-2026-08-11.md` | caiso-192 |
| 2 | `wefor_residual` narrow arm (the ruling-2 grant) | `GATESPEC-caiso193-wefor-residual-2026-08-11.md` | caiso-193 |
| 3 | `gas_st_wefor_base_override` CAISO derivation | `GATESPEC-caiso193-stgas-wefor-2026-08-11.md` | caiso-193 |
| 4 | hydro RoR split made effective (partition + solve) | `GATESPEC-caiso194-hydro-ror-split-2026-08-11.md` | caiso-194 |
| 5 | PS cited-physical parameters (6 plants) | `GATESPEC-caiso195-ps-physical-2026-08-11.md` | caiso-195 |
| 6 | the 8,800 MW uncited import spot capacities | **no gate spec — desk-adjudicated NO** (stays a declared residual; see the FINDING §4) | — |

**This inventory is CLOSED.** If C3a-2025 still fails after the Wave-2 ladder
(`caiso191-integration-protocol-2026-08-11.md`), the campaign outcome is an
**exhaustion memo, not an improvised new lane.** Any new lane requires a fresh
adjudication session and explicit owner authorization — no measuring session may
extend this table, and no session may re-open lane 6 without the new evidence the
caiso-188 §7 fences demand.

Every lane's acceptance gates are authored HERE, before any lane measures, so that no
downstream session shapes its own gates. Every gate spec embeds the campaign's
direction-hazard regime verbatim. The closeout session audits anchor legitimacy: no
band in any spec is anchored to the values under adjudication (the 21.6/26.2/31.9 %
overlay removal rates, or any successor measurement of them) nor to anything derived
from the C3a residual.
