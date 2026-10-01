# miso-80 — Direction-symmetric loss surface: successor charter — VERDICT NO-BUILD

**Date:** 2026-07-20 (charter-first, docs-only — NO LP was solved, no data
was intaken, nothing was registered). **Lane:** the miso-76 loss lane's
named successor (`docs/calibration-log.md` miso-76 entry, "Frontier
evidenced" clause), chartered per the miso-78 precedent: adjudicate at the
design layer BEFORE any build, with NO-BUILD an acceptable verdict.
**Model per rule 27: Fable/Opus** (the lane's build target would edit
`transmission.py`). **Base documents:** the FROZEN miso-76 charter
`docs/handoffs/miso-nc-price-separation-design-2026-07.md` (untouched);
the miso-76 adjudication (frozen monolith `docs/calibration-log.md`
~L17992; registry sidecars `2026-07-19-miso-76-loss-{surface,base}`);
the miso-78 M4 NO-BUILD charter + miso-79 RO-3 NEGATIVE probe.

**Charter discipline:** §4's candidate definitions, §5's verdict, and §7's
reopening conditions are pre-registered. If the owner overrides the verdict
and orders a build, the §6 gate block binds verbatim and may not be revised
after the first LP solve (miso-72..76 precedent).

---

## 0. The question this charter answers

miso-76 built the measured marginal-loss physics (M3): Midwest L1–L6 split
into one-way pairs, receiving-end balance coefficient `1 − eps(month)`,
`eps_(x→y),m = max(0, (dev_y − dev_x)/(1 + dev_y))` from the frozen
MLC-derived surface, reverse direction clamped to 0 (conservative — no
fabricated inverted separation). It was REJECTED by its own pre-registered
R2 on East-2025, with B1 5/9 (undershoot 0.35–0.47× on West-2024 /
Illinois-2024/2025). The miso-76 entry named two successors: the
congestion component (M4 — since adjudicated NO-BUILD, fundamental, by
miso-78/79) and **direction-symmetric loss structure** — this charter.

The question: is the R2 East-2025 trip the one-way clamp's *sign rigidity*
(fixable by making both directions lossy), or a deeper structural property
(not fixable — then NO-BUILD)? And separately: does a symmetric coefficient
re-arm the negative-price free-disposal channel the
`MISO_LOSS_LINK_TIEBREAK_EPS` construction closed
(`transmission.py` ~L3091)?

## 1. Diagnosis: the R2 trip is flow-rectification, and symmetry AMPLIFIES it

### 1a. How an LP loss link prices separation

A one-way link `x→y` with receiving coefficient `1 − eps` and flow cost `c`
constrains the duals two ways (complementary slackness):

- **always** (reduced cost ≥ 0): `λ_y (1 − eps) ≤ λ_x + c`;
- **when the link flows** (basic at margin): equality —
  `λ_y = (λ_x + c)/(1 − eps)`, i.e. separation `≈ +eps·λ`.

So a loss link *prices* separation only in hours it FLOWS at margin, and
the separation it prices carries the **sign of the model's realized flow
direction** — never the sign of the measured gradient directly. The
measured MLC gradient, by contrast, is a **node property of the full
network**, priced in *every* hour whatever any particular corridor does.
This representation gap — link-conditioned vs node-property pricing — is
the root object of this charter.

### 1b. The East-2025 numbers (from the committed surface + adjudication)

From `data/raw/iso-specific-transmission/MISO_loss_surface.csv`
(East − Indiana monthly gradient, 2025): Jan −0.0113, Feb −0.0072,
Mar +0.0119, Apr +0.0069, May −0.0059, Jun −0.0056, Jul +0.0014,
Aug +0.0030, Sep −0.0011, Oct −0.0006, Nov +0.0003, Dec +0.0051 —
**6 months negative, 6 positive, annual net −0.0003** (near-perfect
cancellation). Measured annual dMLC −$0.024; measured RT TOTAL mean
separation **+$0.033** (sign set by offsetting congestion — the
data-blocked M4 component). The miso-76 model realized **−$0.066**
(2.81× the dMLC, > 1.0× the total, wrong sign → R2 trip).

### 1c. Why the one-way variant realized −$0.066 on a net-zero surface

Under the clamp, in a **negative-gradient month** (East dev < Indiana dev)
the lossy direction is East→Ind; the model's East↔Indiana corridor flows
persistently East→Ind, so those months transmit `−|eps_m|·λ` (partially).
In a **positive-gradient month** the lossy direction swaps to Ind→East —
but the model still flows East→Ind, which in those months is the
*lossless* clamped direction: separation ≈ −tiebreak ≈ 0. Result: the
negative months price, the positive months don't — the corridor
**rectifies** a sign-alternating, zero-net measured signal into a
one-signed model separation (−$0.066). The realized number is itself the
evidence of persistent model flow: had the corridor direction tracked the
gradient's monthly sign, the annual would have netted toward
−0.0003·λ ≈ −$0.01.

### 1d. Direction symmetry makes every month rectify

The symmetric candidate (§4 SY-1) charges `|dev_y − dev_x|` on BOTH
directions. Now the positive-gradient months' East→Ind flow is *also*
lossy — and prices `λ_Ind` ABOVE `λ_East`, i.e. **the wrong sign for
exactly those months** (reality has East above Indiana then). Every month
contributes with the model-flow sign; the magnitudes never cancel:

    annual ≈ −Σ_m |eps_m|·λ·(transmission) ≈ 2× the one-way's −$0.066
           ≈ −$0.13 vs measured total +$0.033.

**R2 trips roughly twice as hard.** The one-way clamp was not the trip's
cause — it was the only thing *bounding* it. Answer to the charter
question: the trip is (a) rectification inherent to any nonnegative-loss
LP transport fed a sign-alternating near-zero-net gradient, compounded by
(b) the missing offsetting congestion (M4 — NO-BUILD fundamental per
miso-78/79). Neither is fixable by direction symmetry.

## 2. The B1 undershoot is not symmetric-fixable either

The hypothesis worth checking: does symmetry at least fix the persistent
pairs' undershoot (West-2024 0.35×, Illinois-2024 0.47×, Illinois-2025
0.40× — realized transmission 35–70%)? No — it moves the wrong way:

- **Atypical-direction hours flip sign instead of clamping to 0.** Under
  the clamp, an hour where the corridor flows counter-gradient prices
  ≈ −tiebreak ≈ $0. Under symmetry it prices `−eps·λ` — the wrong sign vs
  the measured persistent gradient — SUBTRACTING from the annual mean.
  Symmetric annual transmission is `(share_typical − share_atypical)·eps·λ`
  vs the clamp's `share_typical·eps·λ`: strictly ≤, never more.
- **The reverse charge is anti-physical at the measured operating point.**
  The surface is the marginal-DF gradient measured at the real network's
  actual operating state; at that state, counter-gradient flow *reduces*
  system losses (marginal delivery factor > 1). Charging `+eps` on it is a
  linearize-about-zero-flow invention — admissible only as an assumption,
  not as the measured object. The symmetric coefficient therefore carries
  strictly WEAKER provenance than miso-76's clamp (which at least never
  fabricates inverted separation) while scoring worse.
- **The transmission ceiling is a representation property, not a
  formulation defect.** The measured gradient is priced every hour as a
  node property; the model can price it only through a flowing link
  (§1a). Hours where the corridor is not flowing typical-direction at an
  uncongested margin — the 30–65% gap — are unreachable by ANY loss
  coefficient, symmetric or not. Closing them would need either the
  congestion component (M4, NO-BUILD) or a non-dual price-side device
  (refused: rule 4, and the measured-MCC hurdle family is charter-refuted
  M2).

## 3. The free-disposal composition (pre-build analysis, per the session ask)

The `MISO_LOSS_LINK_TIEBREAK_EPS` comment (`transmission.py` ~L3091)
closed the circulating-flow disposal channel for the ONE-WAY pairs. Under
symmetry the channel widens — analyzed here BEFORE any build:

- **Mechanics.** Circulating `f` MW both ways on a symmetric pair nets
  `−f·eps_yx` at `x` and `−f·eps_xy` at `y`: free disposal of
  `(eps_xy + eps_yx)·f ≈ 2|Δdev|·f` MWh at flow cost `2·tiebreak·f` =
  $0.002·f. Cost per disposed MWh ≈ `0.002/2|Δdev|` ≈ **$0.2/MWh**
  (one-way pairs: only one lossy direction → ≈ $0.4/MWh — symmetry halves
  the arming threshold).
- **Why it still never arms in MISO.** Every zone carries a Dump column at
  `dump_cost = max(ε, −min(wind_mc, solar_mc) + ε)`; MISO renewables offer
  ≥ $0 (`negative_renewable_offers` is CAISO-only), so `dump_cost = ε =`
  $0.001/MWh. Dump both (a) bounds zonal duals ≥ −ε (the disposal *value*
  can never reach $0.2) and (b) is itself the strictly cheaper disposal
  ($0.001 vs $0.2 per MWh). The loss-link disposal channel is dominated in
  every hour; circulation stays strictly cost-positive.
- **The fence that would be required anyway.** In any composition where a
  zone's duals can go materially negative (negative renewable offers —
  ERCOT's flat −$26 PTC wind, CAISO's REC-valued offers), the $0.2
  threshold is live and a symmetric surface WOULD arm disposal. A
  symmetric mechanism would therefore need a hard MISO-only fence plus an
  explicit incompatibility assert against `negative_renewable_offers`
  (rule 24 scoping). Recorded for completeness: **this is a manageable
  cost, not the binding refutation** — §1–§2 refute the candidate on its
  merits before composition is reached.

## 4. Candidate enumeration (pre-registered)

- **SY-1 — symmetric magnitude, both directions lossy**
  (`eps_both = |dev_y − dev_x|/(1 + dev_recv)`): **REFUTED at the design
  layer.** Amplifies the R2 rectification (§1d, predicted ≈ −$0.13 on
  East-2025 vs measured +$0.033), prices the wrong sign in
  atypical-direction hours so B1 transmission falls (§2), carries weaker
  provenance than the clamp (linearize-at-zero invention vs measured
  operating-point gradient), and halves the disposal-arming threshold
  (§3). Strictly dominated by the existing (rejected) one-way mechanism
  on every axis. Not built.
- **SY-2 — signed coefficients both directions** (counter-gradient
  direction carries coefficient > 1): **LP-INADMISSIBLE.** A receiving
  coefficient above 1 creates energy on reverse flow — the exact defect
  the miso-76 one-way split exists to prevent (`build_miso_link_loss`
  docstring). Free energy, unbounded arbitrage against dump/slack. Not
  built, in any form.
- **SY-3 — persistence-gated re-derive of the EXISTING one-way mechanism**
  (zero a pair's surface in year-months where the gradient's monthly sign
  alternates — the linearization-validity argument: a sign-unstable
  gradient means the true loss surface is flat/nonmonotone around the
  operating point and the monthly linearization is noise): **NOT REFUTED
  as physics, but NOT CHARTERED.** It is the one variant that clears R2 on
  East-2025 (a zeroed surface prices ~$0) keyed to source data, not the
  residual (rule 23-compatible in form). But it cannot reach adoption on
  any honest re-registration: (a) with the East-2025 surface zeroed, the
  pair scores ~0× against B1's own [0.5×, 1.5×] band on the measured
  −$0.024 — the bands would have to be redesigned around the mechanism's
  known failing pair, post-hoc and answer-shaped; (b) the West/Illinois
  undershoots — the actual B1 failures — are the §2 transmission ceiling,
  which gating touches not at all. A variant that converts one overshoot
  into a different band failure while leaving the undershoots is motion,
  not progress. Recorded as reopening path RO-S3 only.

## 5. Verdict: NO-BUILD — the loss lane is at its representation frontier

No derivable direction-symmetric (or gated) variant both survives the
frozen charter's own refutation criteria and improves on the rejected
one-way probe. The trip the successor was chartered to fix is not a
formulation defect: it is the composition of (a) link-conditioned pricing
— a reduced-network property no loss coefficient escapes — and (b) the
absent congestion component, already adjudicated NO-BUILD-fundamental
(miso-78, confirmed by the miso-79 RO-3 negative probe at every zonal
granularity). The Midwest intra-pool separation ledger therefore stands
as: **~half the persistent wind-belt separation is representable loss
physics (built, merged, tier-3 default-OFF, rejected on East-2025 by its
own pre-registration); the remainder — and the East cancellation pairs —
are congestion, data-blocked at representation.** The miso-76 mechanism
stays exactly as merged (default OFF, no re-arm, no deletion — it is
structurally faithful measured physics, rule 1); the one-way clamp is
recorded as the CORRECT conservative choice, not a defect.

Consistent with rule 12's spirit (windows/drivers/forward stories for
floors) applied to refutations: this verdict is grounded in the mechanism
algebra (§1a) and the committed measured record (§1b), not in the
residual's direction.

## 6. Gate block — binds ONLY if the owner overrides to build (pre-registered)

Included for completeness per charter discipline; the verdict above
recommends against exercising it.

- **Recipe:** the CURRENT keeper recipe (`2026-07-19-miso-gasshape-interpfix`,
  bundle `results/calibration/miso_gasshape_interpfix_main` — NOT miso75),
  full span 2023+2024+2025, years sequential, main + same-box base, BOTH
  arms registered whatever the verdict (rules 12/15/16).
- **R1 (veto):** C3b ≤ 0.20 every year. Keeper: 0.082/0.137/0.198 —
  the 2025 headroom is 0.002.
- **R2 (the kill gate, named on its known failure):** no pair-year's model
  annual-mean separation may exceed 1.0× its measured RT TOTAL mean —
  scored FIRST on **East-2025** (measured +$0.033; §1d predicts ≈ −$0.13
  for SY-1 — the gate this charter expects any symmetric build to fail).
- **B1:** [0.5×, 1.5×] of measured mean dMLC per benchmarked pair-year
  (West/Illinois/East vs Indiana) — unchanged from the frozen miso-76
  charter; no band may be re-fit to exempt a pair.
- **R3/R4/R5:** inertness, no-criterion-regression (incl. NO new floors —
  the loss physics carries no D-2 mechanism id), and no-price-movement-
  as-validation — verbatim from the frozen charter §6.
- **Disposal guard (new, from §3):** the build asserts MISO-only scoping
  and incompatibility with `negative_renewable_offers`; a probe run must
  show zero simultaneous both-direction flow on every loss pair in every
  hour (circulation = the disposal channel arming = automatic reject).
- C3a/C3c movement is disclosure, never the target (rules 13/14); keeper
  swap is an OWNER-ONLY recommendation.

## 7. Pre-registered reopening conditions

- **RO-S1 (congestion arrives):** a miso-78 reopening (RO-1 published
  PTDFs/boundary-aligned limits, or RO-2 owner-chartered physics-network
  program) fires. With a congestion component representable, the East
  cancellation pairs gain their offsetting term and a JOINT
  loss+congestion charter supersedes this one. This is the only path that
  addresses the R2 sign structure.
- **RO-S2 (flow/gradient concordance demonstrated):** a derive-layer,
  no-LP probe shows the model's hourly corridor flow direction agrees
  with the measured hourly MLC gradient sign at ≥ a pre-set threshold
  (set a priori in the probe's charter, before the concordance is
  computed) on the failing pairs — evidence that an hourly-resolved
  surface would not rectify. Monthly evidence says otherwise today
  (§1c); this condition exists so better time-resolution can be tested
  without a build.
- **RO-S3 (owner-chartered SY-3):** a persistence-gated re-derive with
  an a-priori materiality floor — noting §4's finding that it cannot
  clear B1 as-registered and would require the owner to explicitly
  re-charter the band structure FIRST (never retroactively).

## 8. Disposition

Docs-only. NO LP, NO solve, NO intake, NO registration (rule 15 N/A — no
run exists); quarantine untouched; keeper UNCHANGED
(`2026-07-19-miso-gasshape-interpfix`, determination NOT-YET on the
ledgered irreducible {C3a-2025 −15.1%, C3c} tail). The frozen miso-76
charter is not edited (this document is the successor record, the miso-79
addendum precedent notwithstanding — no pre-sign-off decision of that
charter is affected). **Next action is the owner's** (single decision,
miso-78 §7 precedent): sign off the NO-BUILD verdict (this charter
freezes; the Midwest-separation lane closes at its frontier pending
RO-S1/RO-S2/RO-S3), or override — order the §6-gated SY-1 build
regardless (both arms will be registered on the pre-registered gates),
or redirect the MISO lane (open lanes: D1 Z2/Z7 split, blocked on a load
split; the PJM merit-cap twin; scarcity-tail successor work is ledgered
out of scope). Next number: miso-81.

---

**OWNER SIGN-OFF (2026-07-20):** NO-BUILD verdict signed off in-session
("Ok do it", responding to the recommendation to sign off this charter and
proceed to the phantom-outage re-audit as miso-81). This charter is FROZEN.
The Midwest-separation lane closes at its representation frontier pending
RO-S1/RO-S2/RO-S3.
