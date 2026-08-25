# FINDING — NYISO external-capacity accreditation intake (capx D-2 successor)

**Session:** capx D-2 NYISO-EXTCAP-INTAKE (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-25 · **Branch:** `claude/capx-d2-nyiso-extcap-intake-sewmyx`
**Charter:** execute the pre-stated successor of
`FINDING-capx-d2-adequacy-nyiso-2026-08-24.md` §6 — source NYISO's *published*
external-capacity accreditation and add NYISO to `ADEQUACY_EXTERNAL_TIE_FIRM_MW`
on the FF-2B construction, never a number tuned to the invariant.

---

## 0. Headline

**Sourced and shipped: `ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"] = 3,168.5 × (1 − 0.1321)
= 2,749.9 MW UCAP**, from the 2026 Gold Book Table V-1 (Summer 2026 net capacity
purchases from external control areas) converted with the same published NYCA
ICAP→UCAP translation factor the requirement side already applies.
**I7 (TBD after solve). Honesty test: the value overshoots the 35.7 MW gap by
~77× — inside the pre-declared O(10²–10³) band, not suspiciously close.**

---

## 1. The sourced value and its citation chain

| quantity | value | source |
|---|---:|---|
| Summer 2026 net capacity purchases, total | **3,168.5 MW** (ICAP) | 2026 Gold Book, Table V-1 (p. 140) |
| — ISO-NE | 67.3 | same table |
| — Hydro-Québec | 2,443.0 | same table (incl. CHPE availability per its note 4) |
| — IESO (Ontario) | 3.3 | same table |
| — PJM | 654.9 | same table |
| NYCA ICAP→UCAP translation factor | 1 − 0.1321 = 0.8679 | NYSRC 2025-2026 IRM Study Technical Appendices, App. D Table D.2 (already intaken: `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv`) |
| **registry entry (UCAP)** | **2,749.9 MW** | product of the two published operands |

**Primary source identity.** `data/raw/NYISO/2026-Gold-Book-Public.pdf` (April
2026, 166 pp) was re-fetched from the README-verified URL
(`https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf`) and
verified **byte-identical** to the committed provenance record: sha256
`43865c1cbe38ca2ef4c8319d11454881de2b9dde3e48867dbbd2e94855b908bf`, 2,666,002
bytes, exactly as `data/raw/NYISO/SHA256SUMS.txt` records. The payload itself
stays gitignored (BLOAT-B-2 corpus conversion); the README's Gold-Book bullet
now names Table V-1 as this constant's source alongside the existing
`DEMAND_GROWTH_RATES` (Table I-1a) note.

**What Table V-1 is.** The Gold Book's own external-capacity accounting: *net*
capacity purchases from external control areas (imports minus capacity exports),
backed by UDR / External-CRIS-Rights / ETCNL / FCFSR elections and grandfathered
rights (table note 2) — i.e. the ICAP-market products through which external
capacity counts in NYISO's ledger. It is the exact quantity NYISO's own NYCA
Capacity Schedule adds to internal resources: Table V-2a Summer 2026,
37,697.7 (NYCA resource capability) + 3,168.5 (net capacity purchases)
= 40,866.2 MW Total Resource Capability, restated in prose on p. 75 and p. 137.

## 2. Basis discipline — why × 0.8679, and why that is the conservative direction

The Gold Book capacity schedule states **seasonal capability (ICAP)** MW, while
the model's NYISO adequacy requirement is **UCAP**:
`peak × (1 + IRM 0.244) × (1 − 0.1321)` (the R5a pairing,
`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`). Crediting the ICAP number
against a UCAP requirement would overstate by ~13 % of the entry. So the entry
converts with the **same published factor the requirement side uses** — one
basis across both sides of the I7 comparison (rule 19), the identical
documented-reconciliation pattern as the PJM DR entry (DR UCAP / UCAP
requirement). Zero free parameters: both operands are published, both are
already independently intaken/tested in this repo, and the arithmetic is stated
in the constant's citation block and pinned by test
(`test_ucap_conversion_uses_the_requirement_side_factor` — the entry's implied
conversion **is** the registered requirement-side ratio, so the two can never
silently diverge).

Direction of the approximation: NYISO's actual ledger derates each external
resource by its *own* EFORd / UDR-line availability (ICAP Manual §4.5). The HQ
and CHPE ties derate far less than the NYCA-wide 13.21 % fleet average applied
here, so this construction can only **under-credit** — it cannot manufacture
firm MW NYISO would not count (the same conservative-direction argument as the
hydro registry's lower-class-factor choice).

**Corroboration (UCAP basis + magnitude).** NYISO 2025 SOM (Potomac Economics,
May 2026 — re-fetched, sha-verified against `SHA256SUMS.txt`:
`80c27d0b…`, 14,425,051 B): Figure A-97 "NYISO Capacity Imports and Exports by
Interface" shows **net capacity imports transacting in UCAP** at roughly
1,500–2,500 MW monthly over May 2023–Apr 2026, and the adjoining text confirms
the §4.5 EFORd-derate construction. The Gold Book's 2026 figure sits at the top
of that historical band because it adds CHPE (in service 2026, note 4). A
2,749.9 MW UCAP entry is squarely the magnitude NYISO's own ICAP market record
shows.

**The two rejected bases, re-affirmed** (and pinned by
`test_entry_is_not_a_deliverability_limit_or_the_dispatch_floor`):

* **NOT** the model's 900 MW HQ firm dispatch floor — an inherited ladder
  constant (`scripts/data/derive_nyiso_import_tranches.py`: *"kept at the
  ladder's established value"*), not a published RA accreditation. The prior
  session's refusal stands; no new evidence overturned it, and none was needed
  once the published number existed.
* **NOT** the 4,350 MW Simultaneous Import Limit — a deliverability *limit*,
  the exact error the CAISO entry rejects for the MIC.

## 3. The honesty test, carried as declared

The prior session pre-declared: *"any real value is O(10²–10³) MW against a
36 MW gap … that overshoot is the evidence the input is honest rather than
tuned."* Result: **2,749.9 MW against 35.7 MW = 77×** — one-to-two orders of
magnitude, inside the declared band. The number was fixed by the two published
operands before any solve was run; the pre-solve arithmetic predictions were
recorded in-session before launching the T1-F leg.

## 4. Re-scored NYISO T1-F leg (I7's post-intake state)

TBD — solve + verdict + registration.

## 5. What was shipped

TBD — file list.

## 6. Governance

TBD.
