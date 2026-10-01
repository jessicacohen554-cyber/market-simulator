# NYISO/NEISO capacity accreditation pairing adjudication (R5a/R5b) — 2026-07-15

RC-1D of the accreditation-basis lane (gap register §3.10 — `docs/gap-register-
2026-07.md`). Adjudicates the two audits the P-2B memo opened
(`docs/handoffs/accreditation-basis-memo-2026-07-12.md` §4.3 R5) using this
session's own research
(`data/raw/capacity-market/accreditation-filings/{nyiso,neiso}/README.md`,
landed by RC-0A — `docs/handoffs/retirement-lane-intake-2026-07-15.md` §7).
Scope: accreditation registry/requirement layer only. **No dispatch-layer or
backcast-keeper changes; no LP solve.**

**Outcome: R5b (NEISO) implemented this session — `THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"] = "claimed_capability"`.
R5a (NYISO) NOT implemented — adjudicated below, owner-decision box §3, code
unchanged, curve stays INELIGIBLE.**

---

## 1. R5b — NEISO qualified-capacity basis (IMPLEMENTED)

### 1.1 The question and the answer

Does ISO-NE's Forward Capacity Market accredit a resource's Qualified
Capacity (QC) with a forced-outage (EFORd-style) derate, the way this repo's
supply ledger derates thermal at `pmax x (1 - EFORd)`? **No.** RC-0A's
research (`data/raw/capacity-market/accreditation-filings/neiso/README.md`)
found, from primary tariff text:

> ISO New England Transmission, Markets and Services Tariff, Market Rule 1,
> §III.13.1.2.2.1.1 ("Summer Qualified Capacity"), eff. 2025-05-03, Docket
> ER25-2149-000: "The summer Qualified Capacity of an Existing Generating
> Capacity Resource that is not an Intermittent Power Resource shall be equal
> to the median of that Existing Generating Capacity Resource's summer
> Seasonal Claimed Capability ratings from the most recent five years... with
> only positive summer ratings included."

A full-text search of the 235-page III.13/III.14 tariff sections for "EFORd"
/ "Equivalent Forced Outage" returns **zero matches**. EFORd instead sizes
only the SYSTEM-WIDE Installed Capacity Requirement, through the GE MARS
probabilistic reliability simulation (ISO-NE ICR Reference Guide rev. 2.0
§5.6.1: "A non-intermittent Generating Capacity Resource's [EFORd] assumption
is calculated... The GE MARS model includes a representative EFORd... for all
non-intermittent Generating Capacity Resources") — a fleet-wide *aggregate*
sizing input, never an individual resource's own accredited QC.

Individual forced-outage/performance risk is instead priced **ex post**,
resource-by-resource, through Pay-for-Performance — a second, independent
settlement layered on top of the (undischarged) QC-based Base Payment:

- Capacity Scarcity Condition trigger — Market Rule 1 §III.13.7.2.1, eff.
  2024-03-01, Docket ER22-983-000.
- Performance Payment Rate — Market Rule 1 §III.13.7.2.5, same docket: a
  historical schedule from $2,000/MWh (2018-2021) to the **current
  $9,337/MWh** (June 2025-May 2026+), with ISO-NE's own pending FERC petition
  to cut it to $3,500/MWh.
- "Introduction to ISO-NE FCM Pay-For-Performance," ISO-NE training module,
  2018-03-19/23: "Capacity Payment = Base payment [...never negative] +
  Performance payment [...may be negative, zero, or positive]."

So the repo's `1 - EFORd` thermal derate has **no ISO-NE analogue on the
supply-accreditation side** — applying it to NEISO double-derates a risk
ISO-NE already prices through PFP, exactly the "requirement and supply must
pair on the ISO's own construction" principle the accreditation-basis memo
established for PJM/MISO/ERCOT (§4.1).

### 1.2 What changed

`THERMAL_ACCREDITATION_BASIS_BY_ISO` (`src/market_sim/config/constants.py`)
gains `"NEISO": "claimed_capability"`, a new basis value handled by
`thermal_accreditation_fraction` (`src/market_sim/model/capacity.py`)
identically to `"seasonal_rating"` (returns `1.0`, no EFORd derate) but kept
as its own string — the two ISOs' *reason* for the un-derated basis differs
(ERCOT: outage risk lives in the 13.75% target margin; ISO-NE: outage risk is
priced ex post through PFP), and conflating two distinct market mechanisms
under one label would misdocument the provenance for a future reader (rule
5/13 discipline — a citation trail must trace to the actual mechanism, not a
numerically-convenient neighbor).

Because `thermal_accreditation_fraction` is the ONE resolver both the
adequacy ledger (`_thermal_firm_mw`) and the per-unit payment
(`capacity_revenue_per_mw_yr`) read (rule 19), this single registry entry
fixes both sides at once — no separate payment-seam edit needed (the existing
`test_default_off_byte_identity` in `tests/test_capacity_demand_curve.py`
already asserts ledger/payment consistency generically across every
`MARKET_DESIGN` ISO, so it now covers NEISO's new basis without a code
change to that test).

### 1.3 What did NOT change (and why)

- **The requirement side.** NEISO's Net ICR / planning-reserve-margin
  registry entry (`PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"] = 0.157`, itself
  flagged `needs-citation` — a NERC reference-margin stand-in "until the
  ICR-implied margin is wired in") is untouched. R5b's scope (per the P-2B
  memo §4.1 NEISO row: "audit with the FCA qualified-capacity definition")
  is the supply-side accreditation basis, not the ICR sizing methodology —
  that is a separate, already-tracked open item.
- **VRE / storage accreditation for NEISO.** Only
  `THERMAL_ACCREDITATION_BASIS_BY_ISO` (dispatchable thermal) moved; ISO-NE's
  Intermittent Power Resource QC construction (ICR Reference Guide §5.6.2:
  historical median output during "Intermittent Reliability Hours," no
  EFORd/maintenance allocation) and its storage default (5% EFORd pending
  fleet data, §5.7.2) are out of this session's scope — no VRE/storage
  registry claim is made here.
- **The FCM sunset.** The current tariff (eff. 2026-03-31, Docket
  ER26-925-000) states plainly that "the final Forward Capacity Auction was
  held in February 2024... and no Forward Capacity Auctions shall be held
  thereafter" for delivery years past CCP2027-2028 (FCA18). The
  `"claimed_capability"` basis documents this dating caveat inline
  (`constants.py` comment) — it is the mechanism *current through* that
  sunset, not validated against ISO-NE's Capacity Accreditation Reform
  successor process, which was not researched this session.

### 1.4 Tests added (mirrors the R2/R3 pattern)

`tests/test_capacity.py::TestClaimedCapabilityBasis` (mirrors
`TestThermalElccClassRatings`, the R3 basis-consistency pattern):

- `test_thermal_firm_mw_uses_claimed_capability_for_neiso` — a 1000 MW
  gas-CC (eford 0.05) accredits 1000 MW on NEISO, not 950 MW; NYISO/`None`
  keep the UCAP fallback (950 MW) as the contrast case.
- `test_claimed_capability_is_class_agnostic` — every `EFORD` fuel class
  returns `1.0` on NEISO (unlike PJM's per-class ELCC table, QC has no
  fuel-class dependency — a per-unit SCC median, so no
  `THERMAL_..._BY_ISO["NEISO"]` fuel-class registry was needed or added).
- `test_claimed_capability_matches_seasonal_rating_numerically` — confirms
  the two labels are arithmetically identical (both `1.0`) while remaining
  distinct strings, so the provenance documentation above stays accurate.

`tests/test_capacity_demand_curve.py::TestReservePosition::test_hand_computed_ratio`
previously used NEISO as its generic "plain UCAP ISO" fixture (DR fraction 0,
ICAP→UCAP ratio 1.0) — now inaccurate for NEISO's `claimed_capability` basis,
so that fixture switched to NYISO (which still carries all three of those
properties; see R5a below). No other test in the repo hard-coded a NEISO
`(1 - EFORd)` expectation (checked: `test_reliability_floor.py`,
`test_validate_capacity_prices.py`, `test_replay_keeper_strict.py`,
`test_driver_directionality.py` reference NEISO only for commitment-floor /
price-validation / byte-identity-iteration purposes unrelated to thermal
accreditation).

`model-methodology-spec.md` §5.9 updated to name the new basis alongside the
other three and drop NEISO from the "UCAP, the default" list.

---

## 2. R5a — NYISO ICAP→UCAP translation-factor construction (NOT IMPLEMENTED)

### 2.1 The question

NYISO's published Installed Reserve Margin (IRM, 24.4% for 2025-2026, NYSRC
Final Base Case) is stated on an **ICAP** basis
(`PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"] = 0.244`), but the model's supply
ledger counts NYISO thermal at UCAP (`1 - EFORd`, the registry default — the
same basis NYISO's OWN construction uses for individual units). Unlike
PJM/MISO, NYISO is absent from
`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`, so
`resolve_adequacy_requirement_mw` falls back to ratio `1.0` — i.e. it
compares an ICAP-stated requirement directly against a UCAP-counted supply
without any conversion. Same basis-mismatch error class the P-2B memo fixed
for PJM/MISO, in the opposite direction (PJM/MISO's ratios are `< 1`, so the
missing-ratio default of `1.0` for NYISO *overstates* the requirement rather
than understating it) — the requirement is too high by roughly the
translation factor, so the measured reserve position reads too low, and the
CR-1 curve (when enabled) over-pays.

### 2.2 Why NYISO has no PJM/MISO-style fix available

RC-0A's research
(`data/raw/capacity-market/accreditation-filings/nyiso/README.md`) confirms,
from the primary source, that **no such filed ratio exists to intake**:

> NYISO Installed Capacity Manual (Manual 04), v18.0, eff. 2026-07-07,
> Committee Acceptance 2026-06-18 BIC, §2.5 (verbatim): "the NYISO will
> calculate the NYCA Minimum Unforced Capacity Requirement by multiplying the
> NYCA Minimum Installed Capacity Requirement by one (1) minus the NYCA
> translation factor. The NYCA translation factor shall be calculated by
> taking the quantity one (1) minus a value equal to: (a) the total amount of
> Unforced Capacity that all resources electrically located in the NYCA are
> qualified to provide during such Capability Period... divided by (b) the
> sum of the Installed Capacity values used to determine the Unforced
> Capacity of such resources for such Capability Period."

i.e. `translation_factor = 1 - [Σ(qualified fleet UCAP) / Σ(qualified fleet
ICAP)]`, **recomputed twice per Capability Year** (§8: "these translations
occur twice during the course of each capability year, prior to the start of
the summer and winter capability periods") from whichever units are actually
qualified that period — not a number NYISO files once per planning year the
way PJM files its FPR or MISO files its dual-basis PRM. NYISO's own IRM Study
materials confirm this is by design, not an omission: "the increase in wind
resources lowers the translation factor from required ICAP to required UCAP"
(NYSRC 2024 IRM Study Technical Report §8) — the ratio is meant to move with
the qualified fleet's own performance, as a standing incentive effect ("The
conversion to UCAP provides financial incentives to decrease the forced
outage rates while improving reliability").

The only concrete in-effect number RC-0A located is **NYC's *Locational*
translation factor for the Summer 2025 Capability Period: 5.18%** (NYISO
"ICAP Demand Curve" Intermediate ICAP Course training deck, 2026-05-20/21,
slides 38-39, worked example). No NYCA-wide (system-wide) worked numeric
example, and no per-Capability-Period published time series of the NYCA-wide
factor, was located (see §4 below).

### 2.3 The two candidate constructions

**(i) Model-derived: compute the translation factor from the model's own
fleet, via the manual's own Σ(UCAP)/Σ(ICAP) roll-up formula.**

This is admissible under rule 13's own test — "could this same quantity be
produced for a forward year from forward drivers, and would it respond to
changed conditions?" — because there is no published constant being
shortcut here (unlike the rejected P-2B "Option D," which proposed dividing
the model's supply by a *model-derived pool factor as a substitute for a
published FPR that exists*: "a self-referential, fleet-dependent conversion
— exactly what stage-5's 'not a model-derived pool EFORd' clause was written
to prevent," rejected on rule-24-spirit grounds precisely because PJM/MISO
*do* publish the number being bypassed). For NYISO, the manual's own formula
**is** "compute it from the qualified fleet each period" — there is nothing
to bypass. Applying the manual's formula to the model's own forecast fleet
is, in that narrow sense, the *more* faithful construction, not a shortcut.

**However, this repo's existing architecture makes a naive (synchronous,
same-year) implementation of (i) mathematically degenerate**, and that
degeneracy is the reason this session does not implement it. Walking the
algebra with this repo's actual call graph
(`capacity_reserve_position` calls both `resolve_adequacy_requirement_mw`
and `accredited_firm_capacity_mw` on the **same** year's **same** fleet,
`src/market_sim/model/capacity.py:2534-2537`):

```
translation_factor  = 1 - accredited_firm_capacity_mw / total_nameplate_mw      (same-year fleet)
requirement_ucap_mw = peak x (1 + IRM) x (1 - translation_factor)
                     = peak x (1 + IRM) x (accredited_firm_capacity_mw / total_nameplate_mw)

position = accredited_firm_capacity_mw / requirement_ucap_mw
         = total_nameplate_mw / [peak x (1 + IRM)]
```

`accredited_firm_capacity_mw` cancels exactly out of the position ratio,
regardless of what thermal EFORd, VRE ELCC, or storage duration-derate the
model applies to any individual class — the reserve position collapses to a
straight nameplate-vs-ICAP-requirement comparison, and the entire point of
per-class accreditation (the reason PJM's gas-CT pays 0.60 and NYISO's coal
pays `1-EFORd`) becomes invisible to the adequacy screens and the CR-1 price.
This is functionally the same failure mode the P-2B memo's rejected Option B
("revert the ICAP→UCAP ratio... makes Pass-2 positions land in the priced
region... two errors cancelling") warned against, arrived at from a
different direction: not two independently-wrong numbers cancelling, but one
number (the translation factor) constructed from the exact same population
it is then measured against, so it cancels itself by algebraic
construction — an anti-pattern **structurally adjacent to but distinct from**
the rejected Option D (Option D bypassed an *existing* published number;
this failure mode exists even with no published number to bypass, purely
from the self-referential population choice).

A non-degenerate version of (i) is describable — compute the translation
factor from the **prior** year's realized/evolved fleet and apply it to the
**current** year's requirement (mirroring NYISO's own real-world timing:
§8's "twice... prior to the start of" each period means NYISO's own
translation factor is *also* always computed from a fleet snapshot that
precedes the period it governs, not synchronously self-measured). This
breaks the algebraic cancellation whenever the modeled fleet's accreditation
mix changes year over year, and is architecturally analogous to the existing
`prior_results`-threaded pattern the economic-retirement screen already uses
for `mc_cost` (CLAUDE.md capacity-evolution section). But it requires
threading a new prior-year aggregate (Σ accredited MW, Σ nameplate MW) through
`resolve_adequacy_requirement_mw`'s call sites — a signature/architecture
change, not a citation-only registry entry — and was not designed or
implemented this session.

**(ii) Static proxy: carry the most-recently-realized published factor
forward.**

The only located concrete number, NYC Summer 2025's 5.18%, is **Locational**
(the NYC zone's own qualified-fleet mix), not NYCA-wide. Applying it as the
model's NYCA-wide `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]`
entry would be exactly the boundary-mismatch case CLAUDE.md rule 5 flags as
needing explicit reconciliation before use ("the data is defined on a
different boundary than our zones... prefer a *reconciled* version of the
real data over a pure guess") — NYC's generation mix (import-dependent,
gas-heavy, comparatively little wind) is not representative of the NYCA-wide
qualified fleet the requirement actually governs, and no reconciliation
between the two boundaries was performed or is straightforward to perform
from what RC-0A retrieved. The NYCA-wide equivalent (referenced by the NYSRC
IRM Study text as "Appendix D, Table D.1.1" but not located this session —
§4 below) is the number this construction actually needs.

### 2.4 Quantified expected shift

The gap-register entry (`docs/gap-register-2026-07.md` §3.10, R5a) already
carries the order-of-magnitude estimate: **position understated ~5-7%,
over-pays** — i.e. supplying *any* correctly-scoped translation factor in the
5-7% range (consistent with the one concrete data point found, NYC's 5.18%)
closes a requirement that is currently ~5-7% too high on a UCAP basis, moving
the reserve position ratio up by a comparable amount and collapsing the
corresponding over-payment on the CR-1 curve (gated
`capacity_market_clearing`, currently default-off, so this has no effect on
any currently-enabled run). This is consistent in direction and rough
magnitude with the PJM/MISO ratios already in the registry (0.77-0.93 range)
being applied to a similarly-structured ICAP-basis IRM.

### 2.5 Recommendation

**Recommend (i) in principle** — it is the ISO's own published methodology,
not a proxy, and it is the only construction with a genuine forward story
(rule 13): it regenerates every forecast year from the model's own fleet,
exactly mirroring what NYISO itself does with the realized fleet. **But its
only currently-describable non-degenerate implementation requires an
architecture change (lagged prior-year threading) this session did not
design**, so it fails this task's own bar ("implement... if its construction
is unambiguous"). (ii) is well-defined mechanically (a static registry
entry, identical machinery to PJM/MISO's ratios) but its only concrete
number is boundary-mismatched (Locational, not NYCA-wide) without a
documented reconciliation. **Neither is implemented this session.** NYISO's
`THERMAL_ACCREDITATION_BASIS_BY_ISO` / `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`
entries are unchanged (NYISO stays on the byte-identical UCAP/ratio-1.0
fallback), and NYISO's capacity curve **stays INELIGIBLE** pending this
adjudication's owner sign-off (P-2A already blocks it on curve vintage
separately; this adds the pairing-basis blocker on top, per the P-2B memo
§4.1 NYISO row and the gap register's original framing).

---

## 3. Owner-decision box (R5a)

| | Construction | What it requires | Verdict |
|---|---|---|---|
| **A** | **Lagged model-derived translation factor** — compute `1 - Σ(prior-year accredited MW)/Σ(prior-year nameplate MW)` from the model's own evolved NYISO fleet, thread it into `resolve_adequacy_requirement_mw` for the *following* year (mirrors NYISO's own "compute ahead of the period it governs" timing; breaks the same-year cancellation identified in §2.3) | An architecture change: new prior-year aggregate threaded through the requirement resolver (comparable scope to the existing `mc_cost`/`prior_results` pattern), plus its own dedicated tests | **RECOMMENDED design target** — not implemented this session; needs a scoped follow-up session to design + implement + test |
| **B** | **NYCA-wide static proxy**, once intaken — carry a genuinely NYCA-wide (not Locational) realized translation factor forward as a static `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]` entry, identical machinery to PJM/MISO | The NYSRC IRM Study "Appendices" PDF (Appendix D, Table D.1.1) — not located this session, added to MANUAL DOWNLOADS NEEDED below; or the NYISO Gold Book's raw ICAP/UCAP totals, back-computed | **ALTERNATE** — cheaper to implement once the data lands, but freezes a number NYISO's own design treats as intentionally time-varying (weaker rule-13 story than A) |
| **C** | **Locational (NYC) 5.18% used directly as the NYCA-wide proxy** | Nothing further — already on disk | **REJECTED this session** — boundary mismatch (rule 5): NYC's qualified-fleet mix is not representative of NYCA-wide: not reconciled, not verified representative |
| **D** | **Status quo** (ratio 1.0 fallback, i.e. no conversion) | Nothing | **Current state; stays until A or B lands** — known ~5-7% overstatement of the requirement, no CR-1/curve exposure while `capacity_market_clearing` stays default-off |

**This session's action: D stands.** NYISO's curve stays INELIGIBLE. Next
step is an owner call on A vs. B (or authorizing the Appendix D intake to
make B possible) — flagged, not decided, here.

---

## 4. MANUAL DOWNLOADS NEEDED (added by this session)

- **NYSRC IRM Study "Appendices" PDF, Appendix D, Table D.1.1** — the
  NYCA-wide "UCAP reserve margin trends" numeric table the Report Body text
  references but which was not located at a resolvable URL this session (the
  2024/2025 IRM Study Report Body is on disk;
  `2024-IRM-Study-Report-Appendices-12-8-2023.pdf` was seen in search results
  by title only, no working URL found). This is the single artifact that
  would make Option B (§3) implementable without a boundary-mismatch caveat.
- **NYISO Gold Book (Load & Capacity Data)** raw NYCA ICAP/UCAP totals by
  year — an alternative back-computation path to the same NYCA-wide
  translation-factor series, not opened for this specific purpose (RC-0A
  flagged the 2024 edition's URL but did not mine it).
- **A NYCA-wide (as opposed to NYC-Locational) worked UCAP-translation
  numeric example**, in any NYISO training/filing material — would at least
  give one additional dated data point even short of a full time series.

---

## 5. Gap register update

`docs/gap-register-2026-07.md` §3.10 rows R5a/R5b updated in this commit —
R5b marked implemented (this memo, this session); R5a marked adjudicated /
not implemented, curve-ineligible status reaffirmed, owner-decision box
cross-referenced.

## 6. Follow-up: parameter registry regeneration not pushed this session

`scripts/generate_parameter_registry.py` was run locally and confirmed clean
(`python scripts/validate_parameters.py` exits 0) after adding the R5b
`THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"]` entry — one new registry row,
`thermal_accreditation_basis_by_iso.NEISO`, in both
`frontend/data/parameters.json` and `docs/parameter-citations.md`. That
regenerated `frontend/data/parameters.json` (~1.3 MB) exceeds what this
session's push mechanism (`mcp__github__push_files`, which requires each
file's complete content inline — no diff/patch mode) can transport in a
single tool call, so **neither derived file was pushed this session**; both
are unchanged on this branch (still missing the new NEISO row). This is a
citation-registry completeness gap only — `src/market_sim/config/constants.py`
itself carries the full inline citation (rule 5), which is the actual source
of truth the registry is rendered from (`docs/parameter-citations.md`'s own
header: "edit citations in the JSON (or the constant's comment, then re-run
the generator), not here"). `validate_parameters.py` is not currently wired
into `.github/workflows/ci.yml`, so this does not fail CI, but it should
still be closed: a follow-up session (with local git-CLI or a
size-appropriate transport) should run
`python scripts/generate_parameter_registry.py` and push the refreshed
`frontend/data/parameters.json` + `docs/parameter-citations.md` alone.

*Produced 2026-07-15 (RC-1D). No LP solve. No holdout year touched (rule 22).
Nothing on the backcast dashboard (capacity evolution is forecast-mode only).
Code touched: `src/market_sim/config/constants.py`,
`src/market_sim/model/capacity.py`, `model-methodology-spec.md`,
`tests/test_capacity.py`, `tests/test_capacity_demand_curve.py`,
`docs/gap-register-2026-07.md`. Parameter-registry regeneration
(`frontend/data/parameters.json`, `docs/parameter-citations.md`) deferred —
see §6.*
