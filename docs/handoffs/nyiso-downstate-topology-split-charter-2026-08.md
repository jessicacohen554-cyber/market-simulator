# OWNER CHARTER (PRECOMMIT) — NYISO downstate boundary: the `Capital_Hudson` → Zone-F/Zone-G topology split, PAIRED with the upstate level object

**Status:** **CHARTERED, PRECOMMIT ONLY.** Nothing is built, armed, registered or
solved by this document. **Opened 2026-08-04** by owner ruling in session
nyiso-123 ("charter both, paired").
**Class:** topology change — the **ERCOT West/Panhandle class** (that one is CLOSED;
this one is open). **NOT a lever-queue entry and NEVER a mechanism flag.**
**Keeper at charter time:** `2026-08-04-nyiso-120-c119-scope`, determination
**NOT-YET**, C3c the sole ledgered caveat (budget **1 of 3, unspent**).

**Evidence base, all committed and all no-LP:**
`docs/handoffs/nyiso-123-downstate-boundary-2026-08-04.md` (this charter's grounding),
`results/calibration/FINDING-nyiso122-c3a-2025-is-two-objects-2026-08-04.md`,
`_nyiso123_month_band_allyears.json`, `_nyiso123_zonal_identity_allyears.json`,
`_nyiso122_c3a_2025_decomp.json`, `_nyiso122_winter_zonal_spread.json`,
`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`.

---

## §1 — What is chartered, and why it is a PAIR

**Two objects, one promotion.**

**Object A — the downstate locational boundary.** NYISO's five-zone representation
cannot form the sub-zonal price separation that the real market runs downstate of
Central East. The model prices its four mainland zones **identically in 95.9 % of
all 2025 hours** and in **100.0 %** of Jan+Feb 2025, while the market ran a
**$44.28** all-5 zonal spread in January 2025 with **no interface flow-limited**
(nyiso-122 §3) and with fuel able to explain at most **$12.75–17.00** of it
(nyiso-122 §2.1). Object A owns **both** halves of the C3a-2025 failure — the
cold-snap $100–300 miss and the summer >$300 tail — and it is C3c's standing
re-open condition.

**Object B — over-pricing of the unconstrained upstate zone.** The model's
load-weighted `Upstate_West` error is **+$7.93/MWh (2023)**, **+$3.25 (2024)**,
**+$1.59 (2025)** (nyiso-123 §3.3). This is the "mask" nyiso-122 identified as
trough over-pricing, located exactly.

**Why they cannot be separated.** nyiso-123 §3.3 establishes an exact identity,
asserted in probe code rather than observed:

> a model that reproduced the observed downstate basis and changed nothing else
> would score **exactly the C3a error of its own unconstrained upstate price**.

So closing Object A **converts Object B directly into the score**:

| year | C3a today | C3a with the basis closed, Object B untouched |
|---|--:|--:|
| 2023 | **+8.10 % PASS** | **+24.74 % FAIL** |
| 2024 | **+0.07 % PASS** | **+8.60 %** — in band, near the edge |
| 2025 | **−7.86 % FAIL** | **+2.45 % PASS** |

Shipping A alone would fix the failing year and **break a passing one**. That is
in-sample gain with held-out degradation — exactly what rule 22 `[R-HOLDOUT]`
exists to catch. Hence: **one charter, two objects, a single joint promotion gate.**

**Owner ruling, 2026-08-04 (nyiso-123):** *charter both, paired.*

## §2 — Scope, and what is explicitly OUT

**IN scope.**

1. Splitting `Capital_Hudson` into representable Zone-F / Zone-G nodes, with the
   transmission topology, load allocation, fleet re-assignment and interface
   limits that the split requires.
2. Whatever Object B turns out to be, diagnosed **before** it is treated (§4).
3. Re-derivation of any input whose *source* the split changes — zonal load
   allocation, zonal fleet membership, interface ratings — under rule 23
   `[R-FROZEN-DERIVE]`: the commit cites the topology change as the source change.

**OUT of scope, and not re-openable inside this charter.**

1. **Any mechanism flag.** This is a representation change. If the work reduces to
   adding a `ScenarioConfig` boolean, it has failed and must stop (rule 24).
2. **The G-J locality limit as a standalone lever** — refused ex ante at nyiso-101
   for want of a representable boundary. It re-opens **only** as a consequence of
   the split, once the boundary exists, and then on its own evidence.
3. **A second mechanism for the peak half.** Rule 19 `[R-ONE-MECH]`: the everyday
   peak-band reserve-price formation is **nyiso-110's object** and is
   route-exhausted (`diurnal_price_amplitude` NYISO = **G**). The split may fix it
   as a by-product; nothing else may be added for it.
4. **Re-grounding the Tier-3 interface TTCs on NYISO's measured as-enforced
   limits.** REFUTED at nyiso-122 §3 and reported against interest: UPNY-CONED and
   SPR/DUN-SOUTH bind >95 % in **0.0 %** of 2025 hours at medians **looser** than
   the model's estimates. Do not re-open it as "use the real limits." **New
   interface limits created by the split are a different question** and are in
   scope — they must be identified on their own evidence, not by transplanting a
   refuted one.
5. **Item 4 (`nyiso_iroquois_winter_spread`).** Held **unadjudicated** by owner
   ruling 2026-08-04. It is not part of this charter in either direction.
6. **Any out-of-training year.** The holdout spend freeze is **ACTIVE** and
   outranks NYISO's `complete` marker. All work here is 2023–2025.

## §3 — The identification bar, pre-registered

This is the bar the charter exists to enforce, and it is the one that killed every
prior candidate for this residual.

**The split must produce the downstate basis from a CONSTRAINT, not from the
observed basis.** nyiso-123 §3.3's counterfactual is a **diagnostic bound** — it
consumes measured outcomes and under rule 13 `[R-MEASURED]` may never enter a
solve. Concretely, the following are **inadmissible** and their presence fails the
charter outright:

- any per-zone adder, offset, uplift or multiplier whose value was chosen so the
  zonal price lands on the observed basis;
- any interface limit tuned until congestion appears, or until a residual moves;
- any zonal load re-allocation selected by its effect on price rather than by a
  published or metered allocation;
- any parameter that only regenerates for a forecast year by being re-fitted.

**The admissibility test is rule 13's own:** could this quantity be produced for a
forward year from forward drivers, and would it respond to changed conditions? An
F/G boundary rating read from a published NYISO transfer-limit posting passes. A
number that reproduces $44.28 does not.

**Every free parameter the split introduces enters the DOF ledger with its
identification source** (rule 20 `[R-DOF]`). A residual closable only by a tuned
value is an open blocker to be written up, **not** a value to pick.

**Note on precedent.** nyiso-97 closed the sub-zonal in-city object **on
identification**: the as-enforced AORR is MyNYISO-walled and the public
2008-vintage Appendix B carries no derivable NYC parameter. **That closure is not
overturned by this charter.** The charter's first gate (§4, G0) is precisely to
establish whether an F/G boundary can be identified from public data where the
in-city pocket could not. **If G0 fails, the charter closes with cause** — that is
a legitimate and expected outcome, not a failure of the session that reports it.

## §4 — Pre-registered gates, in order

No gate may be re-specified after it is measured. A gate that fails as written is
**recorded as failed**; the nyiso-115 G2 / nyiso-117 G2a / nyiso-119 G5 lesson
applies — a gate may be *re-specified onto what it meant* only with the original
result reported alongside.

**G0 — IDENTIFIABILITY (no-LP, gates everything else).**
Establish from **public, reproducible** sources: the F/G boundary definition, its
transfer limit(s), the zonal load allocation, and the fleet membership on each
side. **PASS** = every quantity has a citable public source and a forward
analogue. **FAIL** = the charter **closes with cause**, exactly as nyiso-97 closed.
*No LP runs before G0 passes.*

**G1 — OBJECT B DIAGNOSED (no-LP, gates the solve).**
Object B must be **diagnosed and attributed to a named cause** before any split is
solved. Its size is known (+$7.93 / +$3.25 / +$1.59); its cause is not. Candidate
classes to discriminate — upstate offer-curve level, hydro, wind, must-run/floor
forcing in upstate hours, the upstate marginal-unit mix. **PASS** = a named
mechanism with an identification source. **FAIL** = the pair cannot be promoted,
and the charter reports that rather than shipping A alone.

**G2 — CONSTRUCTION (no-LP, on the built topology).**
Load conservation across the split exactly (Δ = 0 on annual zonal load); fleet
conservation exactly (no unit gained, lost or duplicated); the pre-split
`Capital_Hudson` aggregate reproducible from F + G. Any non-zero conservation
residual is a **stop**, not a tolerance.

**G3 — BLAST RADIUS (A/B, same HEAD).**
Zones outside the split and outside its downstream path must move within noise. A
material move in `Upstate_West` from the **split alone** is a construction defect,
not a result.

**G4 — THE CONSTRAINT ACTUALLY BINDS, IN THE RIGHT HOURS.**
The new F/G boundary must bind in hours its own driver evidence justifies — the
cold snaps and summer peaks §2 of the finding localizes — and **not** in hours it
should not. **A window declared as "Jan+Feb" fails this gate.** nyiso-123 §2.1
measured that the winter object sits in **February in 2023**, **December in 2024**
and **Jan+Feb in 2025**; it is a **cold-snap** object and its window must be
derived from a cold-snap driver (rule 17 `[R-FLOOR-WINDOW]`).

**G5 — THE JOINT PROMOTION GATE. This is the gate the pairing exists for.**
Scored **leave-one-year-out within 2023–2025** on the committed bundle:

- **C3a passes in all three years** for the **paired** treatment (A + B together).
- The **A-alone** arm is solved and reported **whatever it shows** — it is the
  charter's own control and the record of why the pairing was required.
- **A-alone improving 2025 while degrading 2023 or 2024 is NOT a partial success.**
  It is the pre-registered expected outcome (+24.74 % / +8.60 %) and it authorizes
  **nothing**.
- C3c is re-measured. **The tail is not this gate's pass condition** — C3c is a
  ledgered caveat with an exhausted queue, and the split may or may not lift it.
  **The charter is not failed by C3c remaining a caveat.**
- Every other criterion holds: C1, C3b, C4, C6, C7, C8 non-regressing.

**G6 — GOVERNANCE ON PROMOTION.**
Rule 16: all three years, one invocation, one bundle. Rule 22 D-5(b): NYISO holds a
`complete` marker, so promotion **must** re-key `calibration-complete.json`'s
`keeper` **and** re-verify `determination` with
`scripts/calibration_verdict.py --run-id` **before** the promotion commit lands; a
**worse** re-verified determination **stops the promotion and escalates to the
owner** — it is never silently written. Rule 15: register on the backcast dashboard
in the same session, keeper or rejected probe. Rule 28: stamp the matrix cell and
re-stamp the §5.5 header in the same session.

## §5 — Sequencing

**G0 and G1 are both no-LP and independent — run them in either order or together,
and in a session that solves nothing.** G0 gates whether there is a charter at all;
G1 gates whether a passing pair is reachable. Only when both PASS does a solve
session open. This ordering is deliberate: it spends the cheap, decisive evidence
first, and it means a charter that should close does so **before** any LP time is
spent on it.

Expected shape once both pass: an A-alone arm and a paired A+B arm against a
same-HEAD zero-delta control, all three years, one bundle each, rule 12 concurrency
(≤2 simultaneous invocations, years sequential within each).

## §6 — What would close this charter WITHOUT a promotion

Stated in advance so a later session can close it cleanly rather than grinding:

1. **G0 fails** — the F/G boundary is no more identifiable from public data than
   the in-city pocket was at nyiso-97. Close with cause; NYISO's C3a-2025 failure
   becomes a documented representation-frontier limitation alongside C3c, and the
   owner decides whether to ledger it.
2. **G1 fails** — Object B has no identifiable cause, so the pair cannot be built
   and A alone is inadmissible under G5. Close; re-open if Object B is later
   diagnosed in another lane.
3. **G3 or G4 fails on construction** — the split as built is not the real
   boundary. Report and close; a re-scoped boundary is a new charter.

**A closure under any of these is a legitimate charter outcome and must be reported
as plainly as a promotion would be.** nyiso-122 refuted its own successor
hypothesis and nyiso-123 reported that its counterfactual breaks two passing years;
that standard applies here.

## §7 — Open questions carried into the charter

1. **Why did the model carry more zonal dispersion in 2023 (mainland-4 identity
   **86.40 %**) than in 2024 (95.88 %) or 2025 (95.94 %)?** Undiagnosed at
   nyiso-123 and not load-bearing for any conclusion there, but it is a clue about
   what currently creates zonal separation and may bear on G1.
2. **Is Object B the same object as nyiso-110's compression?** The upstate
   over-pricing lives in the trough band; nyiso-110's object is the missing peak
   reserve-price formation. They may be two ends of one compression or two
   defects. G1 must decide, because rule 19 `[R-ONE-MECH]` forbids treating them
   twice.
3. **Does the split subsume the LI zone's behaviour?** `Long_Island` already prices
   apart from the mainland (all-5 identity 80.2 % vs mainland-4 95.9 % in 2025) and
   carries its own locational RCPF ladder. The charter should confirm the split
   does not double-count what the LI ladder already represents.
