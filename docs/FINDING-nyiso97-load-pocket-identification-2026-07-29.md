# nyiso-97 — SCUC load-pocket security commitment: identification verdict (no build, no solve)

**Lane:** NYISO C3c sub-zonal load-pocket scoping — the lane's only surviving
candidate (nyiso-91 §j and nyiso-96 §5 both name it: NYISO SCUC load-pocket
security commitment inside NYC Zone J / Long Island Zone K with BPCG
make-whole).
**Keeper at session start:** `2026-07-28-nyiso-92-hydro-envelope`; promoted
in-session by owner decision to `2026-07-29-nyiso-96-ctamort` (step 0b below).
**Charter:** step 0 owner decisions BEFORE building; if authorized, step 1
establishes whether the as-enforced Con Edison in-city local reliability rule
is publicly obtainable, and **stops with no build and no solve if it is not** —
a pocket requirement backed out of the residual is rule 13/21 forbidden.

---

## 0. Owner decisions (AskUserQuestion, 2026-07-29, this session)

- **(a) Sub-zonal NYC/LI topology: AUTHORIZED, data-first** ("Yes — scope
  sub-zonal", the stop-if-walled variant). The authorization is contingent on
  a published primary-source pocket requirement; no access-seeking follow-up
  (MyNYISO credentials, FOIL) was requested.
- **(b) nyiso-96 C1 trade: owner took the gate.** `2026-07-29-nyiso-96-ctamort`
  promoted to keeper; see `keepers/NYISO.json` promotion note and
  `docs/calibration-log/nyiso.md` 2026-07-29 nyiso-97. Not repeated here.

## 1. What identification requires

To be buildable at all, the mechanism needs (rule 13 admissibility, charter
step 2): a **published** pocket requirement giving (i) the MW level or minimum
units online per pocket, (ii) the eligible unit set, and (iii) a story for how
the requirement regenerates for a forward year from forward drivers. The model
has no DA/RT split — P1 is a single clearing — so the mechanism would have to
be expressible like the three existing P1-native commitment bridges.

## 2. The as-enforced source is still login-walled (nyiso-83 confirmed)

The as-enforced requirements live in the **Applications of the Reliability
Rules (AORR)** table. Checked 2026-07-29: the AORR is reachable only through
the NYISO **Reports & Info** page behind a **MyNYISO login**
(https://www.nyiso.com/reports-information → login at
https://www.nyiso.com/login). The current Manual 12 replaced its former
Appendix B tables (B.1–B.5) with links to that walled location — exactly what
nyiso-83 documented. Manual 12 §2.1.5 states "The NYSRC shall post the updated
Applications of the Reliability Rules on its web site"; checked 2026-07-29,
nysrc.org's Documents section (Reliability Rules & Compliance Monitoring,
Policies, Agreements, Reports, Filings) carries **no AORR posting**.

## 3. New evidence this session: a public 2008-vintage copy exists — and it decides the question AGAINST buildability

A complete October 2017 Manual 12 (Version 3.4) with the full Appendix B is
publicly mirrored off-NYISO:

- Full manual (154 pp):
  https://www.ercot.com/files/docs/2011/01/28/nyiso_manual_12___transmission_and_distribution.pdf
- Section excerpts: https://www.nysrc.org/wp-content/uploads/2023/04/NYISO-Transmission-and-Dispatching-Manual-Section-2.2.6.pdf

Its Appendix B pages are stamped **"Version 2.1 09/04/2008"** — the appendix
predates even the 2017 manual body. The Con Edison / LIPA rows relevant to
this lane, quoted:

- **Table B.4 LRR 1 (Con Edison, PSC Directive July 17, 1961):** "Certain
  areas of the Con Edison system are designed and operated for the occurrence
  of a second contingency. Unit Commitment is based on second contingency
  operation as well as consideration of the Storm Watch Procedure, Loss of Six
  Lines South of Millwood and the locational requirements for its operating
  reserves."
- **Table B.4 LRR 2 (Con Edison, PSC Order No. 27302):** "Con Edison must
  maintain its 10 Minute Operating Reserve on in-City steam units and on Fast
  Start Gas Turbines."
- **Table B.4 LRR 3 (Con Edison gas-burning):** above 8000 MW forecast load,
  two of three Astoria generators to minimum oil burn; above 9000 MW, all
  Astoria/Ravenswood/East River generators.
- **ARR 37 (Con Edison):** in-City fast load pick-up / maximum generation to
  operate the cable system at STE ratings — triggered "if contingency analysis
  shows that the post contingency loading on the cable system will exceed STE
  ratings."
- **ARR 66 (Con Edison, LRR I-R1):** "Con Edison procedure SO3-18 states: The
  Gowanus and Narrows gas turbines will be placed in the quick start mode when
  contingency analysis indicates a post contingency violation to meet n-2
  criteria exceeds the LTE rating of a facility in the Greenwood/Staten island
  load pocket…"
- **ARR 28 (LIPA):** concrete unit-commitment voltage-support requirements
  (any 2 of 4 Northport at peak AND light load; up to 2 Port Jefferson east of
  Holbrook; 1 Barrett light-load; Far Rockaway / Montauk / South Fork units at
  stated load levels).

## 4. Verdict: NOT IDENTIFIABLE — on content, not only on access

Three independent blockers, any one sufficient:

1. **The published table carries no derivable parameter for NYC.** Even at the
   public vintage, every Con Edison in-city commitment row is **qualitative
   and condition-triggered**: the trigger is Con Ed's own real-time contingency
   analysis on its sub-transmission network (ARR 37, ARR 66), and the
   operational parameters live in Con Edison System Operation procedures
   (SO3-18 and kin) that are TO-internal, NYISO-reviewed, and published
   nowhere. There is no MW level, no minimum-units-per-pocket table, no
   eligible-unit list to derive. A trigger we cannot observe and a parameter
   we cannot read fails rule 13's regeneration test outright — and
   reconstructing either from the residual is exactly what rules 13/21
   forbid. (The LIPA rows ARE concrete — but they are voltage-support unit
   commitments on the 138/69 kV system, the Zone-K side already carries the
   published `nyiso_li_lcr_tsl` import limit in the keeper, and the vintage
   problem below still applies.)
2. **The public vintage is not the as-enforced rule.** The appendix is
   2008-stamped; the 2023–2025 NYC pocket fleet is materially different (DEC
   peaker-rule retirements 2023–2025, Astoria/Ravenswood steam retirements,
   repowerings). Deriving a 2023–2025 commitment obligation from a 2008 table
   would be an inaccurate input worn as a measured one — the reverse of rule
   14's intent.
3. **The as-enforced version is MyNYISO-walled** (§2), and the owner's chosen
   authorization variant was explicitly stop-if-walled, not seek-access.

**Make-whole data is not a substitute.** BPCG/uplift by NYC load pocket is
public in aggregate (Potomac SOM/quarterly reports), but it is an *outcome* of
the commitment, not the requirement — feeding it back as an input is rule 13's
definition of pinning.

## 5. Disposition

- **NYISO C3c is recorded as a DIAGNOSED, UNCLOSED structural limitation of
  the five-zone representation** (nyiso-91's own words), now with the
  identification question adjudicated rather than deferred. No solve was
  spent; no mechanism, topology change, or data intake was built. The
  sub-zonal authorization (§0a) remains on file but is unusable until a
  qualifying source exists.
- **Matrix:** new row `scuc_load_pocket_commitment` → NYISO **`G`** (ex-ante,
  identification-blocked; other ISOs `·` — the rule set is NYSRC/ConEd/LIPA
  specific). The CT_PEAKER start-frequency defect it would have addressed is
  carried on the promoted keeper's attestation as an owner-accepted
  misrepresentation (`_open_items (0)`).
- **Re-open conditions** (any one): NYISO/NYSRC restores a public AORR posting
  at current vintage carrying actual pocket parameters; a FERC/PSC docket
  publishes the as-enforced pocket MW requirements and eligible unit sets; or
  the owner supplies authorized access to the walled table AND its rows turn
  out (unlike the public vintage) to carry derivable parameters. Do **not**
  re-open by inferring the requirement from observed unit conduct, BPCG
  uplift, LBMP, or the C3c/CT_PEAKER residual.

*(nyiso-97, 2026-07-29. No run produced; nothing to register on the dashboard
beyond the step-0b promotion, which is registered and pushed.)*
