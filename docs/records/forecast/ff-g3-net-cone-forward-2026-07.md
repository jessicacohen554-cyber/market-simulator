# FF-G3 — forward net-CONE vintages (lane L-CAP), 2026-07-20

**Session.** Deep-research grounding for the *forward-year* net-CONE anchor that
drives capacity-market retirement/entry economics, modeled on the
capacity-cost-grounding pattern. Branch
`claude/forward-net-cone-vintages-txs2an`. The standing deliverable is
`docs/capacity-price-forward-methodology-2026-07.md` (design, per-ISO grounding,
delta ledger, divergence quantification, field survey, gaps, maintenance). This
handoff records the audit trail, the scope calls, and the **owner-decision box**.

## 1. What shipped (all default-inert, byte-identical defaults)

- `ScenarioConfig.net_cone_forward_escalation` (`config/scenarios.py`):
  `"hold_last"` (default) | `"reindex_net"` | `"reindex_gross"`. In
  `_CACHE_KEY_OPTIONAL_FIELDS`; TIER-2; `__post_init__` validates + coerces to
  `"hold_last"` in a plain backcast.
- `constants.forward_net_cone_anchor(iso, year, escalation, *, rate,
  eas_offset_per_kw_yr)` — pure resolver on `resolve_demand_curve_vintage`;
  escalates only years past the last published vintage; `None` for CAISO/ERCOT.
- `constants.NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` — cited per-ISO real rate,
  **0.0 for all** (inflation-only finding).
- `tests/test_net_cone_forward.py` (19). Methodology doc + this handoff +
  CHANGELOG + raw-README MANUAL-DOWNLOADS rows.

**Not shipped, by scope guard:** no wiring into the pricing seam
`capacity_price_per_firm_mw_yr` (FF-2C owns that + the per-ISO
`capacity_market_clearing` flips); no new `MARKET_DESIGN_VINTAGES` entry (§3); no
LP solve; no dashboard registration; no default flip.

## 2. Key findings

1. **The field escalates GROSS CONE by a construction index and RE-NETS the E&AS
   offset each year; net-CONE is never indexed directly** (PJM OATT Att. DD
   §5.10(a)(iv); NYISO MST 5.14.1.2.2.1 composite BLS/BEA blend; ISO-NE Tariff
   §III.13; MISO §69A.8; Brattle 2025). ⇒ `reindex_gross` is the faithful mode;
   `reindex_net` is a documented low-fidelity approximation; the real central
   rate is **0.0** (Brattle out-year guidance = inflation-only). The sharp recent
   moves are **step re-anchorings**, not a smooth real trend.
2. **PJM 2028/2029 cleared July 2026 at net-CONE 325.69 $/MW-day UCAP (+34 % over
   the on-disk 2027/28)** — the single biggest stale-anchor gap. Blocked from
   encoding (Table-3 image + XLSX bot-walled).
3. **ISO-NE's FCM is terminating.** FCA 18 (2027/28, on disk) was the last
   forward auction held; FCA 19 (2028/29) is superseded by a prompt/seasonal
   market whose parameters are **unpublished (design only)**. The 2028/29 FCA-19
   CONE (9.614 $/kW-mo) exists on paper but no auction clears against it.
4. **CAISO has no forward CONE trajectory** — the CPM soft-offer cap
   ($88.09/kW-yr) is a static admin value on a 4-year reset; the resolver returns
   `None` (keeps the fixed proxy), which is the honest analogue.
5. **Divergence is material** (§6 of the methodology doc): at +2 %/yr real,
   `reindex_gross` lifts the 2040 anchor +46–87 % across ISOs (gross/net leverage
   1.6–2.5×), all flowing into the retirement/entry capacity-revenue term.

## 3. Scope calls (why no vintage was encoded)

This environment is **bot-walled** for the machine-readable forward-vintage
sources: standard fetch returns empty; the research agents' curl workarounds
retrieved report PDFs but the 2028/29-era numeric tables are **images**
(no OCR/`openpyxl`/rendering tools here), and the authoritative XLSX / FERC
eLibrary attachments return JS shells. Per rule 13 (no guessing) and the
charter's own "MANUAL DOWNLOADS NEEDED for bot-walled sources" convention, the
researched values are **documented + sha256-pinned (where a PDF was obtained) +
filed as MANUAL DOWNLOADS NEEDED** rather than encoded. Re-anchoring is a
follow-up intake session on a non-bot-walled host; the escalation infrastructure
does not depend on it.

## 4. Plan/register bookkeeping

- **FF plan §1.2-11 frontier row and gap-register §3.11 FF-G3 row are ABSENT on
  `main`** (grep-confirmed 2026-07-20): the FF-G1 core-wiring patch that the
  charter says landed them 2026-07-19 is not on `main`. Per charter instruction I
  did **not** create them; when FF-G1 lands, its §3.11/§1.2-11 rows should mark
  FF-G3 as "design shipped; re-anchoring intake + FF-2C seam-wiring pending."
- `docs/handoffs/ff-wave-manager-ledger-2026-07.md` — **not edited** (manager-owned).

## 5. OWNER-DECISION BOX

> **POPULATED 2026-08-02 by FFR-2C** (`docs/handoffs/ffr-2c-net-cone-currency-2026-08-02.md`,
> audit FR-19, owner decision D-3). Every number below is measured, not estimated;
> **no default was flipped and none is recommended by the act of measuring.** The
> shipped mode is still `hold_last` and every real rate is still 0.0.
>
> **The headline the box did not have in July: D3 has largely been EXECUTED, and it
> dominates D1/D2.** Two of the four stale vintages are re-anchored from their
> published instruments, and the size of that one act, expressed in the currency
> D1/D2 argue about:
>
> | ISO | held anchor → re-anchored | step | = years of +2 %/yr real escalation |
> |---|---|---|---|
> | **PJM** | 88.52 → **118.88** $/kW-yr (2027/28 → 2028/29) | **+34.3 %** | **14.9 yr** |
> | **NYISO** | 50.55 → **57.70** $/kW-yr (2025-26 → 2026-27) | **+14.1 %** | **6.7 yr** |
> | MISO | 79.80 (PY2025-26 held) | derivable +1.5 %, **not taken** | 0.8 yr |
> | NEISO | 108.94 (FCA 18 held) | **no newer vintage exists** | — |
>
> On a 2026–2050 horizon there are ~4 more PJM vintages and ~24 more NYISO annual
> updates to come. **Keeping the vintages current is worth more than any defensible
> escalation rate, and it requires no owner decision at all** — it is maintenance.
> That reframes D1/D2 from "how do we grow the anchor" to "what do we do in the tail
> years past the last auction anyone will ever publish".
>
> **Measured D1/D2 spread** — 2050 anchor ($/kW-yr) by mode × real rate, computed on
> each ISO's *re-anchored* base through `constants.forward_net_cone_anchor`. The
> `reindex_gross` column now uses each ISO's **published** gross−net offset, not an
> illustration: PJM 164.41 (workbook), NYISO 74.24 (published Net EAS Revenues),
> MISO 47.56 (LRZ 1-7 mean gross − N/C net). Leverage = gross/net.
>
> | ISO | leverage | r | hold_last | reindex_net | reindex_gross | gross vs hold |
> |---|--:|--:|--:|--:|--:|--:|
> | PJM | 2.383 | 0 % | 118.88 | 118.88 | 118.88 | ±0 % |
> | PJM | | 1 % | 118.88 | 147.97 | 188.20 | +58.3 % |
> | PJM | | 2 % | 118.88 | 183.78 | 273.55 | **+130.1 %** |
> | NYISO | 2.287 | 1 % | 57.70 | 73.26 | 93.29 | +61.7 % |
> | NYISO | | 2 % | 57.70 | 92.81 | 137.98 | **+139.1 %** |
> | MISO | 1.596 | 1 % | 79.80 | 102.34 | 115.77 | +45.1 % |
> | MISO | | 2 % | 79.80 | 130.92 | 161.39 | **+102.2 %** |
> | NEISO | n/a | 2 % | 108.94 | 171.79 | n/a | n/a |
>
> NEISO's `reindex_gross` cell is **n/a because no gross CONE for FCA 18 is on disk**,
> not because the mode fails there. Do not fill it by inference.
>
> **At r = 0.0 every mode is byte-identical to `hold_last`** — so D1 is a decision
> about what a *future* non-zero rate would mean, and is inert until D2 chooses one.
> Choosing `reindex_gross` at 0.0 costs nothing and buys the faithful construction;
> choosing it *with* a positive rate is where the 2–2.4× leverage bites.



Findings-first; **no default is changed by any choice below** (the shipped
default stays `hold_last`). Decisions gate FF-2C (wiring) and a re-anchoring
intake session.

**D1 — Which forward-evolution mode should FF-2C wire as the *recommended*
(still opt-in) forward posture?**
- **(a) `reindex_gross` — RECOMMENDED.** Field-standard and structurally faithful:
  escalate gross by the ISO index, re-net the model's OWN simulated E&AS margin.
  Requires FF-2C to thread the model's E&AS offset into the seam. Central real
  rate 0.0 ⇒ inert until a tightness rate is chosen.
- (b) `reindex_net` — cheap, no E&AS threading, but indexes a residual the field
  never indexes; keep only as a sensitivity.
- (c) `hold_last` — status quo; acceptable ONLY if re-anchoring keeps the last
  vintage current (D3).

> **Measured 2026-08-02 (FFR-2C).** Option (c)'s condition is now half-met and
> half-unmeetable: PJM and NYISO ARE current (D3 executed), MISO is one document
> away, and **NEISO can never be** — FCA 18 is the last forward auction that will
> ever be held, so `hold_last` there is not a maintenance posture but a permanent
> one. Option (a) is also cheaper to adopt than it was in July: every ISO that
> needs it now has a **published** gross−net offset on disk (PJM 164.41, NYISO
> 74.24, MISO 47.56 $/kW-yr) — except NEISO, where no gross CONE for FCA 18 is on
> disk at all. So (a) at r = 0.0 is byte-identical to today and buys the faithful
> construction with zero measured change; the box-header table is the price of (a)
> once r > 0.

**D2 — Forward real escalation rate.** Ship central **0.0 real** (inflation-only,
cited) as the default; expose a positive real rate ONLY as an explicitly-labelled
structural-tightness sensitivity (e.g. +1–2 %/yr real). Confirm 0.0-central, or
name a different cited basis. (A per-ISO published-index rate could be wired if
the owner wants the composite index tracked explicitly rather than a scalar.)

> **Measured 2026-08-02 (FFR-2C).** The 0.0-central finding SURVIVES its first
> confrontation with new data, and this is the box's most decision-relevant result.
> PJM's +34.3 % is the largest single anchor move in this file's history — and it is
> a **step**, explicitly labelled by PJM as the first year of a new Periodic/Quad
> Review cost basis (ER26-455), not a year-over-year trend. Fitting a positive real
> rate to it would extrapolate a one-time re-basing across 23 years, which is exactly
> the error the 0.0-central finding exists to prevent. NYISO's +14.1 % cuts the same
> way from the other side: most of it is a **falling E&AS offset** (Net EAS Revenues
> 77.15 → 74.24), which no construction-cost index would have produced at all.
> **Recommendation unchanged: keep 0.0 central; a positive rate stays a labelled
> sensitivity.** The real lever is vintage currency (D3) — maintenance, not a rate
> choice.

**D3 — Re-anchoring intake.** ~~Authorize a follow-up intake (non-bot-walled host)
for the four MANUAL-DOWNLOAD vintages (PJM 2028/29, NYISO 2026/27, MISO PY26/27,
ISO-NE FCA19-or-successor).~~ **LARGELY EXECUTED 2026-08-02 (FFR-2C).** The
bot-wall was not permanent: PJM's machine-readable Planning-Parameters workbook
and NYISO's document-library posting are both retrievable now, so **PJM 2028/2029
and NYISO CY2026-2027 are intaken, encoded and reconciliation-tested** — the two
that carried essentially all of the stale-anchor bias (+34.3 % and +14.1 %). The
other two rows are **not** intake work and need no authorization:

- **MISO PY2026-27 — derivable but deliberately not encoded.** The N/C aggregate
  is now *proven* (not estimated) at **81.03 $/kW-yr, +1.5 %**: MISO's North/Central
  aggregation is the LRZ 1-7 arithmetic mean (validated on PY2025-26 gross CONE
  against MISO's own published N/C seasonal CONE to 0.0003 %), and its E&AS offset
  is a single per-Planning-Area value (proven arithmetically — gross − net is
  identical at 52,735 across all of LRZ 1-7). It is not encoded because the
  PY2026-27 **seasonal RBDC** parameters are unretrievable (the 2026 PRA Results
  Posting returns S3 `AccessDenied` while 2023/24/25 return 200), and an annual-only
  vintage would drop MISO back to the annual approximation RC-1C replaced — a
  fidelity regression bought for +1.5 %. **The only owner ask here is whether that
  trade is worth revisiting; the engineering is one document away.**
- **ISO-NE — nothing exists to intake.** See D4, which is now the whole of it.

**D4 — ISO-NE regime.** Decide how to represent ISO-NE post-2028/29 once the FCM
terminates: (i) hold FCA 18/19 net-CONE flat until the prompt/seasonal market
publishes parameters, or (ii) encode FCA 19 as a labelled superseded vintage.
Blocked until CAR-SA files (expected Q4 2026).

> **Status re-checked 2026-08-02 (FFR-2C).** Unchanged and still blocked, with the
> dates firmed: FCA 19 is delayed to **February 2028**; CAR-PD was **accepted by FERC
> 2026-03-30 (Docket ER26-925)**; **CAR-SA is expected Q4 2026** and its parameters
> are unpublished. FCA 18 (2027/2028) therefore remains the last forward auction
> ISO-NE has ever held, and holding it flat is the *status quo* — option (i) is
> already what the code does, so **D4 is only a decision if the owner prefers (ii)**.
> One consequence worth pricing: ISO-NE is the ISO where `hold_last` will be doing
> the most work for the longest, because there is no next vintage to re-anchor to.
> That makes D1/D2 matter *more* for NEISO than for PJM/NYISO, which is the opposite
> of the intuition the +34 % PJM headline creates.

**D5 — Gross-CONE ↔ new-build cost coupling (analysis only).** Whether to couple
the reindex-gross basis to the CT/CC capital costs in
`docs/new-build-cost-methodology-2026-07.md` (so one cost driver feeds both the
entry LCOE and the capacity-price anchor) — in-scope to analyze, out-of-scope to
wire; route to FF-2C/an owner call.

> **Evidence added 2026-08-02 (FFR-2C).** The PJM 2028/2029 vintage is a natural
> experiment for exactly this question, and it argues *for* the coupling: PJM's
> +34.3 % net-CONE step is explicitly "the first year for the new Periodic/Quad
> Review" gross-CONE values (ER26-455) — i.e. it is a **new-build capital-cost
> re-estimate propagating into the capacity-price anchor**, which is the coupling
> D5 proposes, happening in the real market. Gross CONE UCAP moved to 776.14
> $/MW-day (223,800 $/MW-yr ICAP levelized revenue requirement) on new cost data
> while the E&AS offset stayed put.
>
> **But the two ISOs decompose oppositely, so do not generalize from PJM.** NYISO's
> +14.1 % is mostly the *other* term: gross CONE moved only +3.3 % (127.71 → 131.94)
> while Net EAS Revenues *fell* 3.8 % (77.15 → 74.24). A coupling that drives the
> capacity anchor off build costs alone would have reproduced roughly a quarter of
> NYISO's actual move and none of its direction. **If D5 is taken, it must couple
> the GROSS leg only and leave E&AS as its own driver** — which is also exactly what
> `reindex_gross` does (escalate gross, re-net E&AS), so D5 and D1(a) are the same
> decision seen from two ends.
>
> Still analysis-only; nothing is wired.

## 6. Verification

- Default `cache_key` cache-neutral (the hashed payload is byte-identical with the field added, verified by diff; dropped at its `"hold_last"` default).
- `test_net_cone_forward.py` (19) + `test_capacity_demand_curve.py` (58) +
  `test_config.py` green. No vintage anchor changed. Seam untouched.
- No solve/score/intake touched 2022, ≤2021, 2019, or H1-2026 (rule 22): this is
  a design + published-parameter session, no LP.
