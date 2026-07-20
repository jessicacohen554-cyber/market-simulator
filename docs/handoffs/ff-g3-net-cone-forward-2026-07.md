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

**D2 — Forward real escalation rate.** Ship central **0.0 real** (inflation-only,
cited) as the default; expose a positive real rate ONLY as an explicitly-labelled
structural-tightness sensitivity (e.g. +1–2 %/yr real). Confirm 0.0-central, or
name a different cited basis. (A per-ISO published-index rate could be wired if
the owner wants the composite index tracked explicitly rather than a scalar.)

**D3 — Re-anchoring intake.** Authorize a follow-up intake (non-bot-walled host)
for the four MANUAL-DOWNLOAD vintages (PJM 2028/29, NYISO 2026/27, MISO PY26/27,
ISO-NE FCA19-or-successor). Re-anchoring alone closes most of the stale-anchor
bias (PJM +34 %) even at hold_last. **Priority: PJM 2028/29.**

**D4 — ISO-NE regime.** Decide how to represent ISO-NE post-2028/29 once the FCM
terminates: (i) hold FCA 18/19 net-CONE flat until the prompt/seasonal market
publishes parameters, or (ii) encode FCA 19 as a labelled superseded vintage.
Blocked until CAR-SA files (expected Q4 2026).

**D5 — Gross-CONE ↔ new-build cost coupling (analysis only).** Whether to couple
the reindex-gross basis to the CT/CC capital costs in
`docs/new-build-cost-methodology-2026-07.md` (so one cost driver feeds both the
entry LCOE and the capacity-price anchor) — in-scope to analyze, out-of-scope to
wire; route to FF-2C/an owner call.

## 6. Verification

- Default `cache_key` cache-neutral (the hashed payload is byte-identical with the field added, verified by diff; dropped at its `"hold_last"` default).
- `test_net_cone_forward.py` (19) + `test_capacity_demand_curve.py` (58) +
  `test_config.py` green. No vintage anchor changed. Seam untouched.
- No solve/score/intake touched 2022, ≤2021, 2019, or H1-2026 (rule 22): this is
  a design + published-parameter session, no LP.
