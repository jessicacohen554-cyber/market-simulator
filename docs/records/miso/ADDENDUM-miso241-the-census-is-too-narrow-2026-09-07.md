# ADDENDUM miso-241 — the C7 census as COMMITTED is NARROWER than the question the PREREG asked, and the widening is declared here BEFORE it is run

Extends `PREREG-miso241-the-spp-quantity-side-charter-2026-09-07.md` (pushed `6fbc5e83`) and
`ADDENDUM-miso241-the-q2-instrument-gate-2026-09-07.md` (pushed `2ef2e667`).

**Pushed before the widened census is run and before any of its results are classified.** No
pre-registered decision rule is touched and **no pre-registered verdict can move**: Q-0, Q-1 and
Q-2 do not read the census at all, and the PREREG's C1–C7 enumeration, DOF rule, admissibility rule
and charter-verdict rule stand exactly as written. Zero LP; nothing armed, chartered, sized or
minted; keeper unchanged at `2026-09-07-miso-233-spp-hourly` (CALIBRATED, C3c the single ledgered
caveat, DOF 41/2).

---

## 0 — STATED FIRST, AGAINST INTEREST: a defect in this session's own instrument, and a fact already seen

**The defect.** PREREG §5 asks, for candidate **C7**, *"does this repository hold **any** measured
MISO–SPP tie outage / derate series, or any SPP reliability-event (EEA / conservative-operations)
log?"* — a question over the repository. The probe committed at `2ef2e667` implements it over
**six named directories only** (`data/raw/MISO`, `data/raw/eia-930-interchange`,
`data/raw/iso-specific-transmission`, `data/raw/campd-unit-level`, `data/raw/outages`,
`data/raw/reference`) and matches six filename tokens. **That is narrower than the question**, and
it is this session's error, not the PREREG's.

**The fact already seen, disclosed rather than papered over.** A plain listing of `data/raw`'s
top level was read while the probe was running — the same class of fact miso-236 recorded
pre-PREREG for `data/raw/MISO` ("holds only Potomac SOM/IMM PDFs") — and it shows SPP-side
measured series the committed census would have missed, among them `campd-unit-outages-SPP.csv`,
`campd-partial-outages-SPP.csv`, `spp-binding-constraints/`, `spp-hsl/`, `spp-genmix/`,
`spp-hourly-load/` and `spp-wind-shape/`. **No content of any of them has been opened**, and none
is classified anywhere until §2's rule below is fixed and pushed. The disclosure is made here
because the honest sequence is *declare the rule, then look* — not the reverse.

## 1 — THE WIDENING (declared here, before it is run)

The census is re-run over **the whole of `data/raw`**, one level of directory names plus every file
name recursively, matching a token list fixed here:

    outage, derate, forced, unavail, eea, alert, conservative, emergency,
    tie, interface, constraint, transfer, atc, ttc, flowgate, curtail

and, separately, **every** `data/raw` child whose name contains `spp` or `swpp` is listed in full
regardless of token, because SPP is the neighbour whose state the charter is about.

**The widening is MONOTONE and that is why it cannot rescue anything.** A wider search over a
superset of paths with a superset of tokens can only **ADD** matches; it can never remove one. So
it can only move the C7 leg from "nothing found" toward "something found" — i.e. **against** the
refusal this session's other legs may be heading for, never toward it. The committed narrow result
is reported beside the widened one so the reader can see exactly what the widening added.

## 2 — THE CLASSIFICATION RULE FOR ANYTHING IT FINDS (fixed here, before any series is opened)

For each candidate series the widened census surfaces, four things are recorded, in this order, and
the verdict follows mechanically:

1. **What it measures**, from the file's own header/README and the repo's data dictionary.
2. **DRIVER or OUTCOME**, on rule 13 `[R-MEASURED]`'s own forward test — *could this same quantity
   be produced for a forward year from forward drivers, and would it respond to changed
   conditions?* A **physical availability event** (a unit or tie outage window) is a DRIVER, which
   rule 13 names explicitly. **The market's own realized result** — a binding-constraint record, a
   realized flow, a realized clearing price on the constrained element, a realized schedule — is an
   **OUTCOME**, and is **INADMISSIBLE as an input**, exactly as miso-236 PREREG §2c ruled the DIBA
   interchange series itself inadmissible and for the same reason.
3. **Whether a DOF-FREE mapping exists** from that series to an LP object on the MISO–SPP seam,
   under PREREG §5's DOF rule unchanged: every constant either produced by an estimator already in
   the codebase reading a committed measured source, or fixed by an identity or a published
   external definition, and none selectable against any residual, gate or criterion.
4. **Rule 19 `[R-ONE-MECH]`**: whether it would REPLACE or RECONCILE with the SPP seam's existing
   mechanisms (PREREG §5's enumeration), never stack.

**A series is ADMISSIBLE only if it is a DRIVER *and* a DOF-free mapping exists *and* rule 19 is
satisfied.** All three, or it is not.

**And the distinction that must not be blurred, fixed here:** an admissible series on this seam is
**not automatically the object miso-236 and miso-237 named.** Their object is the **SWPP+SPA net
load and VRE** channel. A tie- or fleet-outage series is a *different* driver on the *same* seam.
If one is admissible, the FINDING says so **as a separate finding**, states plainly that it does
**not** carry the neighbour-net-load/VRE signal miso-236 measured, and the charter verdict on the
neighbour-state object is decided on its own merits regardless.

## 3 — What this changes: nothing except the census's reach

The PREREG's §5.2 no-licence block binds unchanged and in full: no re-derive, no damping factor, no
change of `K`, no re-spacing of `δ_k`, no envelope, percentile or interface-limit change; nothing
here is a tuning target; no adjudicated cell is re-tested; no cell verdict moves; no field is
minted; no promotion and no decertification. Q-0's, Q-1's and Q-2's numbers are computed by the
committed probe and are untouched by this addendum — none of them reads the census.

## 4 — Governance

Rule 1 `[R-STRUCT]`: nothing judged by a residual; nothing proposed. Rule 13 `[R-MEASURED]`: §2
fixes the admissibility test before any series is opened, and restates miso-236 PREREG §2c's
inadmissible-forms list unchanged. Rule 14 `[R-ACCURATE]` / 23 `[R-FROZEN-DERIVE]`: no input,
envelope, ladder or limit changes. Rule 15 `[R-DASHBOARD]`: no run produced. Rule 19
`[R-ONE-MECH]`: no mechanism added; §2.4 fixes the test. Rule 21 `[R-DOF]`: 41/2, unchanged.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only. Rule 24 `[R-REGISTRY]`: no field created. Rule 25
`[R-ISO-SCOPE]`: MISO's lane only — SPP's own shard, keeper and lane are untouched and nothing
here tests an SPP mechanism. Rule 28(b): evidence-append form. Rule 29 `[R-SCREEN]`: clause 0,
zero LP.
