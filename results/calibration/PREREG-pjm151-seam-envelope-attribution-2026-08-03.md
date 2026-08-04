# PREREG — pjm-151: repair the PJM seam deliverability-envelope attribution

> Session pjm-151, 2026-08-03. Branch `claude/pjm-151-backcast-calibration-cznn3e`.
> Incumbent keeper `2026-08-03-pjm-147b-chp-heat` (bundle `pjm147_chp_B`),
> determination **CALIBRATED**, 9 scored / 9 target / 0 ledgered / 0 fails,
> C1 `all 16/16 · free 12/12`.
> **Pushed BEFORE the first arm solves.** Rule 22 `[R-HOLDOUT]`: 2023–2025 only;
> PJM holds `complete` (validation 2022 unspent) and is absent from `final`;
> holdout spend freeze untouched.

## §1 — the defect, and why this is admissible off an empty lever queue

The PJM price-formation lever queue is EMPTY and the frontier is **owner-declared**
(pjm-142). This arm is **off-queue and says so**: rule 28(a) admits it as a **NEW
measured identification** of a **rule 14 `[R-ACCURATE]` internal-consistency defect**
— keeper-note item 12, carried since pjm-135 and never fixed. It is not a price
lever, not a successor to the flat-stack amplitude deficit, and no part of it was
selected against a residual.

Two modules attribute the SAME physical seam by different rules:

| | TVA | LGEE | Carolinas | NYISO |
|---|---|---|---|---|
| `data/eia930/envelopes.py::_PJM_TIE_ZONE` | `PJM_Dominion` (whole tie) | `PJM_AEP_Ohio` (whole tie) | `PJM_Dominion` | `PJM_EMAAC` |
| `model/interchange/spec.py::INTERFACE_NEIGHBORS` `border_zones` | `("PJM_AEP_Ohio","PJM_Dominion")` | `("PJM_West_APS","PJM_AEP_Ohio")` | `("PJM_Dominion",)` | `("PJM_EMAAC",)` |

**The handoff's framing is corrected on one point of fact: LGEE is inconsistent
too, not a self-consistent contrast case.** TVA and LGEE are both single-zone in
`_PJM_TIE_ZONE` and two-zone in `INTERFACE_NEIGHBORS`.

**Why it bites.** The two structures are not independent —
`model/interchange/pjm.py::inject_pjm_seam_flow_limit` builds a per-model-ZONE
(month × hod) p90 envelope from `_PJM_TIE_ZONE` and then **sums it over each
neighbour's `border_zones`** to get that neighbour's cap. A zone bucket holds
*every* tie that lands in it, and several neighbours name the same border zone, so
each seam's cap absorbs other seams' ties.

## §2 — the derivation, and why no share needed deriving

The charter said *derive the two-zone TVA split from a measured basis or STOP*.
**The split turns out to be the wrong question for the mechanism that matters, and
the correct construction has ZERO free parameters.** The object
`inject_pjm_seam_flow_limit` needs is a **per-NEIGHBOUR** cap; the per-zone
envelope is an unnecessary intermediary that is (a) documented in its own source as
"Tier 3 (calibration) — approximate pending PJM's authoritative tie-to-zone
assignment", and (b) the sole source of the cross-contamination. Building the
envelope from **the seam's own ties** needs only the tie → interface map, which is
an **identity read off PJM's own tie labels** (`spec.PJM_TIE_NEIGHBOR`), not a
derived or fitted share. Rules 5 `[R-NO-MAGIC]` / 24 `[R-REGISTRY]` are satisfied
because there is no number to fit.

`_PJM_TIE_ZONE` is **not** changed and is **not** wrong: a per-zone attribution is
the right grain for the genuinely per-zone objects (the measured zonal net-position
schedule feeding `load_demand`, and the star topology's per-border link caps). After
this repair the two structures answer different questions and no longer collide.

## §3 — what was measured, ex ante, with no LP

`scripts/probes/pjm151_seam_envelope_attribution.py` →
`results/calibration/_pjm151_seam_envelope_attribution.json`. p90, ties **netted
within the hour before the directional clip** (exactly what `pjm_zonal_interchange`
does with `np.add.at` over signed flows). Legacy cap ÷ direct cap, and the fraction
of (month × hod) cells in which the legacy cap sits below the seam's TTC and can
therefore bind at all:

| seam | dir | legacy/direct 2023 / 2024 / 2025 | legacy binds |
|---|---|---|---|
| TVA | export | **124× / 53× / 40×** | 0.000 / 0.000 / 0.097 |
| LGEE | export | **33× / 42× / 26×** | 0.000 / 0.000 / 0.014 |
| TVA | import | 2.05× / 2.20× / 2.38× | 0.167 / 0.125 / 0.240 |
| Carolinas | import | 1.79× / 1.73× / 1.67× | 0.681 / 0.531 / 0.635 |
| MISO | import | 1,538 / 2,139 / 2,323 MW vs **0.1 / 11 / 24 MW** | 1.000 |
| LGEE | import | **0 MW vs 518 / 539 / 549 MW** | 1.000 / 1.000 / 0.986 |
| Carolinas | export | 0.67× / 0.97× / 0.81× | 1.000 |
| **NYISO** | export | **1.00× (exact)** | control |

Three things this establishes before a solve is spent:

1. **`pjm_seam_export_limit` — armed on the keeper *precisely* to fix the
   structural over-export — is effectively INERT on two of the five seams.** Its
   TVA and LGEE caps sit 26–124× above measured and never bind in 2023–24.
2. **The repair LOOSENS as well as tightens.** The legacy LGEE *import* cap is
   0 MW against a measured p90 of ~520–550 MW, and the legacy Carolinas *export*
   cap is *tighter* than measured. A residual-fitted change would not do that.
3. **NYISO reproduces exactly** (its border zone holds only its own four ties) —
   the construction's own control, and evidence the two paths differ only where
   the buckets are mixed.

**A first version of this probe clipped each tie before summing and is recorded as
wrong**: it reported a MISO *import* cap of 2,225 MW when the netted series says
0.1 MW. Netting-then-clipping is the convention both envelope builders use and the
one the numbers above are on. A regression test pins it.

## §4 — the single delta

`ScenarioConfig.pjm_seam_envelope_by_neighbor: bool = False` (`scenarios.py:9060`),
armed **True** in arm B via `replay_keeper.py --set`. Off, the legacy path runs and
every existing run — PJM and non-PJM alike — is byte-identical; registered in
`_CACHE_KEY_OPTIONAL_FIELDS` with its default declared in the FFR-3A ledger, so
off-runs' cache keys are byte-stable. Matrix row: registered on `seam_flow_envelopes`
in the same PR (rule 28(c) duty c).

**It is gated rather than fixed in place deliberately**, for a single-delta A/B on
an ISO with zero caveat budget. **If arm B is promoted, collapsing the flag and
deleting the zone-summed path is the rule 26 `[R-DELETE]` follow-up and is stated
here so it cannot be forgotten** — a repaired mechanism must not leave a re-armable
broken version parsing.

## §5 — arms

| arm | config | status |
|---|---|---|
| **A (control)** | the committed keeper `pjm147_chp_B` | **NOT re-solved — see K2** |
| **B (treatment)** | keeper recipe + `pjm_seam_envelope_by_neighbor=true` | 2023 + 2024 + 2025, ONE bundle |

Driver `scripts/probes/pjm151_seam_arm.py`, walking the rule-12 separate-directory
chain (`--out X_y23` → `X_y24 --reuse-from X_y23` → `X_final --reuse-from X_y24`);
`results/PJM` scrubbed before the first link only. No `--set` other than the single
declared delta.

## §6 — pre-registered gates

**K1 — recipe integrity.** `config_drift(pjm147_chp_B, arm B)` returns exactly one
differing key, `pjm_seam_envelope_by_neighbor` (`False → True`). Any other
value difference is enumerated with the commit that moved it and why it cannot
reach a PJM backcast, or the arm is VOID. Re-diffed again at promotion time
(a parallel session can promote underneath us — the caiso-158 failure).

**K2 — control integrity, discharged WITHOUT a solve.** pjm-150 measured the keeper
reproducing **bit-identically at HEAD `01b6a6a`** (max |ΔMW| = 0.000000 across
499,320 P1 class-hours). Only **two** `src/market_sim/` commits have landed since,
and both are provably PJM-inert by inspection: `5b04fab` changes
`model/reserves/spec.py` **docstring text only** (23 insertions / 1 deletion, no
executable line), and `fcdcac0` adds one `nyiso_nyc_rcpf_step_curve` entry to the
cache-key defaults ledger, read only by the flip guard. Combined with a default-OFF
flag whose entire effect is inside `if by_neighbor:`, **arm A is the committed
keeper.** *(If any further `src/market_sim/` commit lands before arm B solves, this
discharge is void and a zero-delta control arm must be solved.)*

**K3 — liveness.** Arm B must differ from the keeper on the `PJM_Dominion` and
`PJM_AEP_Ohio` net positions. **Zero movement is a REPORTABLE "inert" result, never
a reason to tune anything.** *(A no-solve unit test already confirms the TVA and
LGEE export caps move, so a fully inert dispatch would itself be the finding.)*

**K4 — no criterion regresses.** PJM is 9/9 with ZERO ledgered caveats: there is no
slack. Every criterion that moves is reported as a regression, never absorbed. **C6
will flip `PASS → UNATTESTED` for a probe** (no rule-21 attestation is authored
unless something is promoted) — reported, not absorbed, per caiso-159 §3.

**K5 — span.** `[2023, 2024, 2025]` in ONE bundle (rule 16). No holdout year is
solved, scored, or registered.

**E1 — C1 MAGNITUDE GATE, declared ex ante** (the gate pjm-146 lacked). C1 passes a
class iff `|Δ TWh| ≤ min(2 % of ISO load, 8 TWh) = 8.0 TWh` **and**
`|Δ share| ≤ 3.0 pp`. The 16 gated cells are 2023 × 8 and 2024 × 8; 2025's eight are
SKIPPED on preliminary EIA-923. **Largest admissible move per gated class**, as
remaining headroom to the 8.0 TWh band on the keeper:

| class | 2023 Δ / headroom | 2024 Δ / headroom |
|---|---|---|
| CC_REGULAR | −2.70 / **5.30** | +1.40 / 6.60 |
| CC_CHP | +2.49 / 5.51 | +0.79 / 7.21 |
| CT_PEAKER | −2.00 / 6.00 | −2.89 / **5.11** |
| ST_GAS | +2.01 / 5.99 | −2.17 / 5.83 |
| ST_CHP | −1.27 / 6.73 | −1.33 / 6.67 |
| COAL_PRB | −0.39 / 7.61 | −0.40 / 7.60 |
| COAL_BIT | +1.00 / 7.00 | −0.16 / 7.84 |
| COAL_WC | −0.13 / 7.87 | −0.07 / 7.93 |

**The declared bound: no gated class may move by more than its own headroom above,
and no class may move more than 3.0 TWh in any single year.** The 3.0 TWh cap is
the *ex ante* magnitude discipline — a seam-deliverability repair whose measured
caps change by ≲2 GW on two small seams has no mechanism by which to move a
340 TWh CC fleet by more than that, so a larger move means the change is doing
something other than what it is chartered to do and the arm is REJECTED as
mis-specified, whatever it does to the fit. **2025's ungated classes are held to the
same 3.0 TWh reporting bound** (reported, not gated — no C1 verdict rides on them).

**A note this session is bound to, per rule 1 `[R-STRUCT]` and rule 14
`[R-ACCURATE]`:** the consistent attribution is the structurally correct one and
**ships regardless of the residual**. If the fit degrades, that is a **discovered
bug elsewhere** and a root-cause item is opened — the inconsistency is never
restored and the tie→interface map is never tuned. The one outcome that rejects the
arm is a **mis-specification** signal (E1's magnitude bound), not a worse number.

**Known exposure, stated before solving so it cannot be claimed as a prediction
afterwards:** the keeper's measured net interchange is 29.16 / 22.78 / 26.17 TWh
export against actuals of 39.98 / 32.64 / **17.97** TWh — the model **under**-exports
in 2023–24 and **over**-exports in 2025. Tightening the TVA/LGEE export caps pushes
net export DOWN, which moves *away* from actual in 2023–24 and *toward* it in 2025.
**This is expected to look worse in two of three years and is not a reason to
revert.**

## §7 — kills

* Any second config delta → arm VOID (K1).
* Any `src/market_sim/` commit landing between now and arm B's solve without a
  re-run of the K2 inspection → the control discharge is void.
* Any gated C1 class moving more than its §E1 headroom, or any class moving more
  than 3.0 TWh in a year → REJECT as mis-specified.
* A holdout year touched in any way → stop-the-line.
* Tuning `PJM_TIE_NEIGHBOR`, the percentile, or `_PJM_TIE_ZONE` against a residual
  → forbidden outright (rules 5 / 20 / 24). The percentile stays at the shipped
  `PJM_SEAM_FLOW_PERCENTILE = 90` in both arms.
