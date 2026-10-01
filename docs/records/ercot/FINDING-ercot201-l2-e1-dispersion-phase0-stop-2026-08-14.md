# FINDING — ercot-201 / L2-BUILD: Phase-0 STOP — the chartered E1 dispersion surface is superseded on main, and its identification route is barred by an adjudicated prior stop

> **Session.** ercot-201 / L2-BUILD (ERCOT-SCAR workstream manager dispatch,
> cycle 9, 2026-08-14; pack `docs/handoffs/ercot-scar-workstream-pack-2026-08.md`
> §2.8; child session `session_017mYAd1w2geiUyhvBtYPxC4`). Branch
> `claude/ercot-scar-l2-e1-dispersion` off `origin/main` `5bf5f13`. Model:
> Fable (rule 27). **PHASE-0 STOP under the dispatch's own named STOP
> conditions** ("Phase-0 surface mismatch"; "unidentifiable correction"; "any
> must-not conflict … anything outside scope → STOP and report"). **NOTHING WAS
> BUILT OR SOLVED: no `ScenarioConfig` field (rule 28c not triggered — no
> mechanism row or shard cell is owed), no derive, no A/B, no run registered in
> any namespace, no matrix edit, no keeper/registry/bench contact, no year
> solved or scored (rule 22 honoured trivially), no promotion. Screen-revenue
> movement produced: $0.00/kW-yr.** The L-1/V0 discipline (`docs/
> FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`; charter §2.6 "stay
> inside that distinction or stop") applies verbatim: this stop IS the
> deliverable.

**Standing rulings inherited and cited, never re-litigated:** card Q = (Q-B)
FINAL — no ERCOT C3a-2023 backcast spend of any kind (this lane never touches
dispatch pricing at all); card R = (R-A) — NOT-YET stands, no C3b-2023-targeted
determination rounds; the L-SCAR §4 must-nots bind verbatim (nothing here
touches dispatch prices, LP objectives/bounds, any scored series, or any
backcast artifact — nothing was built); the V0-FAIL adjudication
(`docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`, foot) — no
tightness-conditioned identification re-attempted, none contemplated here.

---

## 0. The chartered object, and what Phase 0 was required to confirm

The 2026-08-14 owner sitting adjudicated the L-SCAR V0 FAIL and **chartered
L-2**: the E1 dispersion repair, described by the signed charter (§6, and the
V0-FAIL ADJUDICATION item (i)) and by the dispatch as:

> "the screen's forward committed-capability formula under-disperses against
> measured RTOLCAP — p1 13.3 GW modeled vs 7.9 GW measured — so the screen's
> ORDC/lookahead tail under-visits the knee"

with the FFR-8A finding (`docs/handoffs/ffr-8a-scarcity-restoration-2026-08-08.md`
§2.5 / §4.1 / §5(c)) as the candidate surface, and the identification
pre-registered as: *"the dispersion target derives from MEASURED RTOLCAP
telemetry only … NO model residual anywhere in the fit; if the telemetry on
disk cannot identify the correction, STOP at Phase 0 and report."*

Phase 0's first duty: **"confirm the E1 surface as FFR-8A describes it (which
formula, which inputs, where the dispersion is lost)."** The mechanical half of
that confirmation SUCCEEDS; the substantive half FAILS. Both halves are
recorded here at full magnitude.

## 1. The mechanical surface check — CONFIRMED as described

The formula and the dispersion-loss mechanism are exactly as FFR-8A describes:

* **Which formula:** `ercot_rtolcap_forward_supply_cap_mw`
  (`src/market_sim/results/scarcity.py:1291`), consumed by E1
  (`ercot_lookahead_committed_reserves`, scarcity.py:1566) under the armed
  `capacity_screen_scarcity_restoration` bundle in
  `runner._lookahead_reprice_signal`, its output bounded by the physical stack
  headroom `min()` and fed to the expected-adder tail
  (`ercot_lookahead_expected_ordc_adder`, E4's Gauss–Hermite integration over
  the WEFOR σ_R).
* **Which inputs:** the frozen `ERCOT_RTOLCAP_FWD_ONLINE_SHARE`/
  `OFFLINE_SHARE` tables — pooled 2023–2025 conditional **medians** per
  (class × season × net-load decile) from the CAMPD unit extracts — times the
  evolved fleet's class capacities, times `ERCOT_RTOLCAP_FWD_DELIV_COEF` (fit
  to the measured RTOLCAP MW quantity), plus the storage-AS term
  (`0.35 ×` evolved storage power) (`scripts/data/derive_ercot_rtolcap_forward.py`).
* **Where dispersion is lost:** the share table is a conditional-median POINT
  model — the within-cell realization distribution is discarded at
  `derive()`'s `np.median(...)`; the decile axis is the evaluated series' OWN
  within-year percentile rank, so the formula's unconditional year-distribution
  is a (season × decile) step function nearly invariant to the net-load series
  it is fed.
* **The telemetry is on disk and rich:** `data/raw/ercot/
  ercot_{2018..2025}_ordc_reserves_hourly.parquet` (NP6-905-CD; 2025 truncated
  at the 2025-12-05 RTC+B go-live), the same vintage family the derive cites.

Had the record stopped at FFR-8A, Phase 0 would have proceeded to the
precommit. It does not stop there.

## 2. The surface as SIZED by the charter is superseded on main — twice

The charter's L-2 paragraph and the dispatch cite FFR-8A's pre-epoch numbers.
Two later pre-registered lanes, both landed on main BEFORE the charter was
assembled (2026-08-13) and before the sitting (2026-08-14), re-measured the
same object. Neither the charter, the V0-FAIL adjudication, the workstream
pack, nor the dispatch cites either one.

### 2.1 FFR-8B (2026-08-09) — the dispersion decomposed; the gap re-attributed

`docs/handoffs/ffr-8b-rebase-dispersion-2026-08-09.md` §2–§3 (its §2
supersedes FFR-8A §4 AS BASELINE by its own clause; probes
`scripts/probes/ffr8b_e1_dispersion.py` → `docs/handoffs/ffr-8b/
e1-dispersion-2026-08-09.json`, identity self-check exact):

* **The "p1 13.3 vs 7.9" gap is SCREEN-ASYMMETRIC and does not reproduce as
  stated.** At the re-based 2024 screen the arm's own low tail (phys-headroom
  bound) drives p1 to **6.3 GW — BELOW the measured 7.9** (133/83/39 h at/below
  the $10/$100/$1000 knees, all via the phys bound). At the long-fleet 2025
  screen it persists (C p1 14.9 vs measured 9.0).
* **The dominant model-side inflator of E1's reserve quantity is NOT the share
  formula but the storage-AS term**: +7,289 MW (2024) / +8,805 MW (2025) at p1
  — the correct 0.35 constant times the over-built evolved storage fleet, an
  FFR-4/5 entry-lane object explicitly outside L-2's scope.
* **The in-scope commitment share proper is +0.8–1.7 GW at p1** (B→A step at
  TRUE net load and TRUE storage), with within-cell (season × decile) residual
  std 4,515/4,727 MW **of which E4's own σ_R already covers 58.5 % in both
  years** — the net un-carried commitment-realization dispersion is
  ≈ 3.7–3.8 GW std.
* **FFR-8B Phase 2, applied verbatim to its pre-registered admissibility rule,
  STOPPED: "NO REPAIR; ESCALATED"** (§4): *"the only faithful identification
  source for that dispersion is realized commitment conduct — the NP6-905-CD
  RTOLCAP telemetry or the CAMPD hourly online-headroom extracts … The charter
  bars them from PARAMETERIZING a repair — validate-only. None of the four
  admissible sources can produce it. … Therefore the repair cannot be built
  without inventing a parameter → STOP."*
* That stop was **adjudicated CLEAN by the FFR-FH workstream manager**
  (`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum **AG.1**,
  2026-08-09): *"the Phase-2 admissibility test applied verbatim and the
  repair correctly ESCALATED rather than parameterized (the measured RTOLCAP
  conduct sources may validate, never parameterize — no admissible
  identification exists for the commitment-realization dispersion)"* — and
  called *"the evidence quality … the program's best."*

### 2.2 FFR-9A (2026-08-09) — the dominant inflator removed, UNGATED; E1 now tracks measured

`docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md` (fix `57cb3e7`,
**ungated — it re-bases every capacity hindcast at HEAD**; its record
supersedes FFR-8B §2 as baseline by the same clause):

* The 17 GW phantom storage base is gone (vintage-2020 fleet to the decimal);
  the E1 storage-term inflation collapses ~71 %/~59 % (2024/2025) **with zero
  changes to E1 itself** (§3.2).
* **E1's full reserve quantity now tracks the measured series where the fleet
  is close to right: 2024 mean 16,703 vs 16,679 measured; 2025 p1 8,619 vs
  8,955 measured** (the FFR-8B-era control read 22,604 mean / 14,871 p1). At
  the tight 2024 screen the treated low tail runs **BELOW** measured
  (p1 −3,328 MW, min −9,175 — the phys-headroom energy-shortage mechanism).
* The screens' remaining price error is the **missing VRE build** (solar 10.0
  vs 25.1 GW, wind 5.5 vs 12.7 GW): the mid-window into-2024 screen
  **OVERSHOOTS** measured scarcity ~11× on the mean ($309.69 vs $26.82; 960 vs
  161 h > $100; margins ~26× the replica-at-measured columns), while the
  forward-edge into-2025 screen's undershoot is half-closed by the storage fix
  alone (112 vs 217 h > $100; mean 31.20 vs 32.49). FFR-9A §4 routes all of
  this to the FFR-4/5 entry lanes; FFR-9B/9C then took the VRE-entry surface,
  and the FFR-9C stage-B unit (owner card D-30, `a71fc84`/PR #3888) is today's
  armed HEAD posture.

**Consequence for the chartered object, stated plainly:** at the current
baseline there is no committed evidence that the E1 formula's tail
under-visits the knee — the last two committed measurements show the arm's
tight screens visiting the knee MORE than the measured series (via the
physical-headroom bound), the mid-window screens overshooting the measured
scarcity content outright, and the residual in-scope dispersion
(≈ 3.7–3.8 GW within-cell std net of σ_R; +0.8–1.7 GW at p1) sitting
second-order behind out-of-scope fleet-trajectory error. A
dispersion-WIDENING repair built now would add tail mass to screens the
committed record shows already overshooting — the opposite of the chartered
intent — and its honest expected reach at the surviving surface is below even
the charter's single-digit floor. (No solve was run to re-size at HEAD:
Phase 0 precedes any solve by the dispatch's own terms; the statement above is
the committed record's, cited, not a new measurement.)

## 3. The identification conflict — why the precommit cannot be written by this session

The dispatch pre-registers the identification VERBATIM as *"the dispersion
target derives from MEASURED RTOLCAP telemetry only."* That is — to the word —
the route FFR-8B pre-registered as barred (*"the measured RTOLCAP distribution
is an OUTCOME of commitment — it may VALIDATE a repair, never parameterize
one"*), applied verbatim, stopped on, and had adjudicated CLEAN (AG.1). Two
standing records now conflict:

* **FFR-FH lane record (on main, manager-adjudicated):** no admissible
  identification exists for the commitment-realization dispersion; the
  telemetry is validate-only; the correct outcome is exactly the stop that was
  taken.
* **ERCOT-SCAR owner signature (on main, 2026-08-14):** "L-2 IS CHARTERED" —
  citing only the pre-epoch FFR-8A surface (p1 13.3 vs 7.9), with the
  identification route stated in the manager's dispatch, not in the signed
  card.

The signature and the adjudicated stop were never put in the same room: no
document of the chartering chain (charter §6/adjudication/pack §0/§2.8)
engages FFR-8B §4, AG.1, or FFR-9A. This session cannot treat the owner
signature as an overrule of a record the sitting never saw — that is a
§2.6-class adjacency question ("carry an outcome-derived distribution into the
screen's tail"), and the L-SCAR lane's own precedent is that such distinctions
are **owner signatures, not lane-level calls** (S1 was signed for exactly this
reason; V0's discipline — stop rather than ship an unidentified or
un-adjudicated knob — was honoured by L-1 and is honoured here). Under pack
§1 fence 9 ("conflicts escalate to the owner") and fence 8 (DO-NOT-REDO: the
FFR-8B stop is an adjudicated record of this precise repair attempt; no new
evidence exists — the only new fact is a signature made without the record),
the correct Phase-0 outcome is this STOP.

## 4. What this stop does NOT decide, and the routes open to a future sitting

This finding refuses nothing on the merits and re-opens nothing. It reports
that the chartered surface's evidentiary basis is stale and its pre-registered
identification is in adjudicated conflict. The routes, for the owner (none is
dispatchable by this session; recommendation at §5):

* **(a) Re-charter L-2 on the live record.** Requires BOTH: (i) an explicit
  owner signature on the identification adjacency — measured-RTOLCAP-
  dispersion-conditioned identification declared admissible for the screen's
  tail, distinguishing (or overruling) FFR-8B §4/AG.1 with that record quoted
  in the card (the S1/§2.6 pattern); and (ii) a live-posture Phase-0 re-size
  gate solved FIRST (the charter's own §5.3 device: "the implementing lane's
  Phase 0 re-sizes the residual at the live posture"), with a pre-registered
  stop if the under-dispersion does not reproduce at HEAD — the committed
  record says it will not, at the screens that matter.
* **(b) Route the screen's price-object error where the committed record
  already points:** the FFR-4/5 entry-lane objects (missing VRE build; storage
  entry timing) — FFR-9A §4's one-mechanism attribution; the FFR-9C stage-B
  arming is that route's first landed increment. This is the structurally
  live surface, and it is another workstream's lane (fence 9 boundary).
* **(c) Park L-2** and leave frontier rank 2 carried by the regime-conditioning
  card lane (in flight, §2.10) alone.

**The honesty bound, restated either way:** the charter's own ceiling stands —
the missing screen revenue is measured λ-led (149/184 of 2024's λ>$100 hours
carried adders ≤$10), so ANY E1-side repair is bounded to
single-digit-to-~20 $/kW-yr of the ~50–70 gap; at the superseded-surface
baseline the surviving in-scope component (+0.8–1.7 GW at p1 against knees at
~7.4 GW) sits at the very bottom of that range.

## 5. Recommendation (recommendation only — no route is taken)

**Route (b) as the program's spend, route (a) only if the owner, with FFR-8B
§4/AG.1 and FFR-9A §3.2 read into the card, still wants a dispersion term.**
The committed record locates the screen's live error in the fleet trajectory
the screens price, not in the E1 formula's dispersion; the in-scope residual
is second-order, σ_R-majority-covered, and identification-orphaned twice
(FFR-8B's admissibility stop; L-1's V0 as the family precedent). If (a) is
signed, this branch's Phase-0 record is its starting point and the
re-size-first gate is non-negotiable.

## 6. Governance — what this session did and did not do

* **Rule 22:** no year solved or scored; no data intake performed (all
  evidence is committed artifacts, cited in place); the 2022 bridge untouched;
  no holdout marker read, granted, or spent.
* **Rule 13/23:** no derive run, no fit performed, no parameter invented; the
  telemetry parquets were listed on disk (presence check) and never read into
  any fit.
* **Rules 15/28:** no run produced, nothing registered (forecast namespace and
  backcast registry both untouched); **no matrix row or cell edited** — 28c is
  not triggered (no field exists), 28b is not triggered (nothing was tested);
  the `capacity_screen_scarcity_restoration` cell's standing text (which
  carries the FFR-8B/9A stamps this finding cites) is read, not changed.
* **Rule 25:** ERCOT only, throughout. **Rule 12:** moot (no invocation).
* **Rule 27:** Fable; edit-local; blob-verify on push (this file and the log
  are the only artifacts).
* **L-SCAR §4 must-nots:** honoured by vacuity and by construction — no
  dispatch price, LP object, scored series, backcast artifact, keeper, bench,
  or registry file is touched; no bar/FOM re-level, no scalar uplift, no
  outcome pin contemplated.
* **Charter §2.6 / V0 discipline:** the stop was taken at the FIRST point the
  identification's adjudicated status became visible, before any precommit,
  build, or solve.
* **Artifacts this session commits:** this FINDING + one calibration-log
  entry (`docs/calibration-log/ercot.md`, shorthand ercot-201). Nothing else.
  Landing: push-and-stop on `claude/ercot-scar-l2-e1-dispersion`; NO PR, NO
  merge (the cycle-8 landing convention).
