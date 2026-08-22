# FINDING miso-177 — the RHO_CLIP 0.5 floor: identification REFUTED on MISO's primary record; the only admissible MISO treatment is the measured value

**Session miso-177, 2026-08-22.** Charter: the standing owner escalation from
the miso-169 promotion and nyiso-144, unresolved for six director cycles —
*identify or refute* the uncited `RHO_CLIP = (0.5, 4.0)` floor
(`src/market_sim/data/online_reserve_rho.py:87`) that clips MISO's
CAMPD-measured `online_rho` 0.1764 UP ~2.8× in the designated keeper
`2026-08-22-miso-175-hourkey`. **No solve was spent on this document**; every
repo number is read from committed artifacts and the committed source, and the
primary-source reading is from MISO's own published manual (§3).

**THE VERDICT, in one line: the 0.5 floor has NO identification — not in this
repository, not in MISO's market rules, not in the physics — and the negative
result is the deliverable. The floor is REFUTED as a citable parameter.**

---

## 1. The object

The online-gated class-2 reserve row (`model/lp/reserve_rows.py`) is
`R[c,z] − rho·Σ_g P[g,t] ≤ 0`: `rho` is the MW of 10-minute deliverable
headroom one MW of on-line output carries. MISO's armed
`miso_reserve_online_gated` (keeper since miso-169) draws the nested
market-wide Reg+Spin family on gated per-pool columns carrying exactly this
coupling row, **in addition to** the pool's joint P+R headroom row (unlike
NYISO, where the row replaces the capability row). The consumption seam
(`data/online_reserve_rho.py::OnlineReserveRho.rho_used`, applied at
`model/reserves/spec.py::_identified_online_rho`) clips the measured statistic
to `RHO_CLIP = (0.5, 4.0)`.

MISO's measured value (`campd_online_reserve_rho_MISO.csv`, committed):
**rho = 0.17644175978069962** — Σ head / Σ P with
`head = min(HSL − P, ramp10_frac × HSL)` over 5,276,357 online unit-hours,
93.07 % CAMPD coverage of the eligible fleet, pooled 2023–2025; per bucket
coal 0.1399 / gas_cc 0.1898 / gas_ct 0.3065 / gas_st 0.2943 / oil 0.2885;
full-hour sensitivity 0.1705. So `rho_used` returns **0.5, the floor — the
guardrail, not the measurement — clipped UP 2.83×**, and the keeper's armed
mechanism solves on it. `config/scenarios.py` documents the floor as UNCITED
in its own field comment; this is a rule 5 `[R-NO-MAGIC]` violation live in a
designated keeper.

## 2. The repository record (verified, not re-litigated)

The repo-internal hunt was executed by nyiso-144/nyiso-145 and is confirmed
here at HEAD:

* **Earliest textual appearance**:
  `PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md` §2 — *"the ρ
  multiplier is the gated fleet's own (pmax−pmin)/pmin property clipped to
  [0.5, 4.0]. No fitted scalar"* — asserted with **no source**.
* **Both legacy call sites** described the band only as *"the same [0.5, 4.0]
  physical band the path-A family uses"* — self-referential (the path-A
  family is PJM's `pjm_reserve_online_gated`/`pjm_reserve_online_rho`, whose
  own default carries `needs-citation` in `docs/parameter-citations.md:894`).
  nyiso-145's `git log -S` archaeology found **no earlier primary citation**
  (`docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md` §3).
* **The band's true genealogy** (decision card §2(b)): it was written for the
  LEGACY estimand — cap-weighted `(pmax−pmin)/pmin` **at minimum stable
  load**, where the value is `(1−f)/f` and `[0.5, 4.0]` brackets
  `f ∈ [0.2, 0.667]` — and was **inherited across a change of estimand** when
  the measured as-operated seam replaced the dead `pmin` path. Every measured
  `rho_minload` lands inside the band; every measured as-operated `rho` lands
  below the floor. The floor is an a-priori plausibility bracket for a
  quantity the seam no longer computes.
* `docs/model-audit-release-plan-2026-08.md` (director board): the ruling is
  *"PREPARED AND WAITING, the oldest piece of finished work on the board"*;
  the named deliverable is exactly this session's re-solve.

## 3. The primary sources — the MISO leg, searched for this finding

The charter's question: does MISO BPM-002, Schedule 28, or the FERC record
behind MISO's reserve demand curves ground a 0.5 **floor** on
reserve-capability-per-MW-online? Read for this session:
**BPM-002-r25, Energy and Operating Reserve Markets Business Practices
Manual** (effective SEP-30-2024 — inside the training window; public copy:
Indiana URC posting, `iurc.portal.in.gov`, "MISO Bus Practices Manual No 2
Attachment_B"; 297 pp). Findings:

1. **The per-resource reserve capability limits in MISO's own clearing are
   ramp-based, not ratio-based.** §4.2.1.46 (Contingency Reserve Ramp
   Constraints): `[ContResRampMult / ContResDeployTime] × ContResDispatch(r,h)
   ≤ InputRampRate(r,h)` — with the current tuning values (§10)
   `ContResRampMult = 1.0`, `ContResDeployTime = 10 Minutes`: **cleared
   contingency reserve ≤ ramp rate × 10 minutes.** §4.2.1.47 applies the same
   form to Regulating Reserve (`RegRampMult = 1.0`,
   `RegResponseTime = 5 Minutes`). This is precisely the
   `ramp10_frac × HSL` leg of the measured statistic's `head` construction —
   the market's own capability definition is what the measurement reproduces.
2. **The ONLY 0.5 anywhere in the reserve-capability formulation is a hard
   CEILING on a different denominator.** §4.2.1.37 (Regulating Reserve
   Dispatch Constraints): `RegResDispatch1 + RegResDispatch2 ≤
   0.5 × RF(r,h) × [RegMaxLimit − RegMinLimit]` — fifty percent of the
   resource's REGULATION RANGE, because regulation deploys bidirectionally
   about the band midpoint. A ≤ on the reg range cannot ground a ≥ on
   headroom-per-MW-online: wrong direction, wrong denominator, wrong product
   scope.
3. **The only other fixed ratios are concentration ceilings**:
   `MaxContResFactor = MaxRegResFactor = 0.2` — the maximum share of the
   MARKET-WIDE requirement one resource may supply (§10, §11.5). Ceilings
   again, and denominated on the requirement, not on output.
4. **Schedule 28 and the FERC filings behind MISO's reserve demand curves are
   requirement-side instruments** — demand-curve levels, not supply
   capability. BPM-002 §6.1.13 confirms the Market-Wide Regulating plus
   Spinning Reserve demand curve as the three-step $98/$65/$0 construction —
   incidentally re-confirming, from the primary source, the exact curve the
   armed mechanism encodes (`MISO_REGSPIN_DEMAND_CURVE_STEPS`). Nothing on
   the demand side speaks to a supply-ratio floor at all.
5. **No floor of any kind on reserve-per-MW-online exists in the
   formulation.** The SCUC/SCED chapters enumerate every per-resource reserve
   constraint (availability flags, ramp constraints, dispatch limits,
   concentration caps); a "resource must carry ≥ 0.5 MW reserve per MW
   on-line" concept appears nowhere. Physically the lower bound of
   headroom-per-MW-online is **zero** (a fleet at full load carries none) —
   the decision card's §3 point, confirmed rather than disturbed by the
   manual.

**Outcome of the hunt: NEGATIVE, on all three source classes.** No citation
exists to record. Under the charter's own terms the floor is unidentified, and
a negative result is the deliverable.

## 4. The treatment (rules 5, 14, 21, 25)

Of the charter's four candidates:

* **Cite and keep — unavailable.** There is nothing to cite (§2–§3).
* **Narrow the clip to a "physically-grounded range" — refuted as a
  concept.** The physical lower bound is 0; any positive floor chosen now
  would be chosen *knowing the measurement*, i.e. a fitted guardrail (rules
  5/21; decision card option B's recorded defect).
* **Replace the floor with the measured value / remove the clip at the MISO
  seam — the same treatment, and the admissible one.** Rule 14
  `[R-ACCURATE]`: the measured statistic exists, is rule-13 admissible
  (regenerates from the CAMPD pipeline for any vintage, responds to fleet
  change, reads no residual), and is grounded in the market's own capability
  definition (§3.1). The uncited floor overriding it is exactly the defect
  class rule 14 names. The **ceiling stays**: 4.0 is `(1−f)/f` at the deepest
  turn-down in the model's own class tables — cited, derivable, and unable to
  bind on any as-operated measurement (harmless-but-grounded).

**Scope (rule 25).** `RHO_CLIP` is shared code and its band is the owner's
standing nyiso-145 decision card — **this session does not touch it.** The
treatment is a MISO-scoped, gated, default-off `ScenarioConfig` field
(`miso_online_rho_no_floor`) read ONLY inside `_miso_design`'s
`miso_reserve_online_gated` branch: when armed, the seam consumes the measured
MISO statistic bounded by the cited ceiling alone
(`OnlineReserveRho.rho_used_no_floor = min(rho, 4.0)`), and hard-errors if the
measured artifact is absent (no silent fallback to a different
identification). Every NYISO call site, the legacy `pmin` path, the shared
band, and every other ISO's build are byte-untouched at any polarity of the
field — the control arm of the A/B proves the default path bit-identical
against the committed keeper. The value adopted for MISO is MISO's own record
(rule 25); NYISO's gated flags remain `U` and inadmissible pending the
owner's band ruling, exactly as nyiso-144 left them.

**DOF (rule 21).** Zero new free parameters: the field is a boolean selector
between two treatments of one committed measured input; the consumed value is
the artifact's, to full precision. The DOF ledger gains a selector entry with
`n_scalars 0`; `n_residual` unchanged.

## 5. What this finding does NOT do

* It does not re-band `RHO_CLIP`, globally or for NYISO — the nyiso-145
  decision card stands untouched as the owner's ruling surface.
* It does not arm anything: the A/B (PREREG-miso177) is pre-registered
  separately, and promotion — if the gates pass — is **presented to the
  owner**, never self-executed: this is a six-cycle-old owner escalation and
  the ruling is theirs.
* It claims nothing against C3a-2025, which is closed end-to-end as a
  model-class limit (miso-163 owner ruling; FINDING-miso171 §6). The expected
  direction — a 2.83× tighter coupling row can only tighten gated Reg+Spin
  supply — is toward MORE scarce-hour reserve pricing, and every number the
  A/B produces is disclosed, never claimed as calibration skill.
* It does not extend to any other ISO's rho (rule 25/28d): NYISO's measured
  values await the owner's band ruling; PJM's path-A default is its own
  lane's `needs-citation` row.

## 6. Provenance

* Charter: the miso-169 §5 ask 1 / nyiso-144 §2.3 escalation;
  `docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md`.
* Code: `src/market_sim/data/online_reserve_rho.py:87` (`RHO_CLIP`);
  `src/market_sim/model/reserves/spec.py::_identified_online_rho` and the
  `_miso_design` gated branch.
* Measurement: `scripts/data/derive_campd_online_reserve_rho.py` →
  `data/raw/_processed-legacy/campd_online_reserve_rho_MISO.csv`.
* Primary source: MISO BPM-002-r25 (SEP-30-2024), §§3.4, 4.2.1.37,
  4.2.1.46–47, 6.1.13, 10, 11.5 (public IURC posting; local extraction in
  session scratchpad).
* This session's A/B: `PREREG-miso177-rho-measured-ab-2026-08-22.md` (control
  `2026-08-22-miso-177-control` / arm `2026-08-22-miso-177-rho-measured`).
