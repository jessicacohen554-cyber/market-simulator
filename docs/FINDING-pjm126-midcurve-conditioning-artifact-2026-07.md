# FINDING — pjm-126: the mid-curve surface's tightest-bin inversion is a CONDITIONING ARTIFACT (2026-07-26)

**Verdict: ARTIFACT (2025, fidelity-exact). Lane 2 STAYS OPEN — a frontier
declaration would be premature.**

The measured PJM mid-curve offer surface prices every physics segment cheapest
in its tightest net-load bin. pjm-123 closed the **entire measured-offer-surface
family** as PJM's dispersion lever on exactly that basis. This probe re-measures
the same corpus under an alternative tightness conditioning and finds the
inversion **does not survive**: under within-**season** net-load ranking, the
CT_FAST inversion collapses from **+10.00 to −0.85** — it reverses sign — and
CC_LIKE's from **+0.35 to −0.20**.

Criteria were committed before the run (`9409f7f`); result JSON in
`results/calibration/pjm126_conditioning_precheck_2025.json`.

---

## 1. The measurement

Three arms, one corpus, one segmentation, one gas series. Inversion gap =
`median(bin2) − median(bin3)`; **positive means bin3 (tightest) is cheaper**,
i.e. the inversion is present.

| segment | arm | bin2 | bin3 | **gap** | flag |
|---|---|---|---|---|---|
| CT_FAST | A_frozen (within-year) | 33.725 | 23.725 | **+10.000** | — |
| CT_FAST | **B_season** (within-season) | 33.025 | 33.875 | **−0.850** | **FLIP** |
| CT_FAST | C_fixedpop | 33.725 | 23.725 | +10.000 | HOLDS |
| CC_LIKE | A_frozen | 5.275 | 4.925 | **+0.350** | — |
| CC_LIKE | **B_season** | 5.175 | 5.375 | **−0.200** | **FLIP** |
| CC_LIKE | C_fixedpop | 5.275 | 4.925 | +0.350 | HOLDS |
| LONG_RUN | A_frozen | 8.175 | 8.075 | +0.100 | — |
| LONG_RUN | B_season | 8.225 | 7.975 | +0.250 | HOLDS |
| LONG_RUN | C_fixedpop | 8.175 | 8.075 | +0.100 | HOLDS |

**2 of 3 segments FLIP** under the season split → **ARTIFACT** on the
pre-registered criteria. LONG_RUN holds, but its gap is +0.10 on a base of ~8.1
— a 1 % effect, an order of magnitude below the two that flip.

**Fidelity guard passed at full strength.** Arm A reproduces the committed
`pjm_offer_midcurve_condbinned.json` 2025 ladders to **8.5 × 10⁻¹³** (tolerance
0.05, one histogram cell). The 2025-only segmentation is identical to the
committed 3-year segmentation, so `--skip-fidelity` was not in fact needed —
this measures the frozen surface exactly.

## 2. The mechanism, named — and it is the *opposite* of the hypothesis

The handoff hypothesised **co-mingling**: "within-year net-load percentile puts
winter evening peaks and summer scarcity in the same bin3". The measured
seasonal composition of each bin shows the reverse — **segregation**:

| 2025 hours per bin | winter | summer | shoulder | total |
|---|---|---|---|---|
| **A_frozen** bin0 | 2,143 | 1,938 | 2,925 | 7,006 |
| **A_frozen** bin1 | 477 | 396 | 3 | 876 |
| **A_frozen** bin2 | 249 | 365 | 0 | 614 |
| **A_frozen** bin3 (tightest) | **34** | **229** | 0 | **263** |
| B_season bin3 | 88 | 88 | 88 | 264 |

**PJM is summer-peaking, so winter's own tight hours never reach the annual
top-3 % of net load.** Bin3 is therefore **87 % summer** and carries only 34
winter hours all year, while bins 1–2 are *winter-enriched* (477 and 249 winter
hours). Winter is precisely when CT offers are most expensive — oil parity, gas
basis blowouts, cold-snap commodity spikes.

So the within-year ranking does not mix the seasons into the tightest bin; it
**excludes winter from it** and deposits winter's expensive offers into the
middle bins. Bins 1–2 are inflated by winter, bin3 is a summer-only sample, and
the "tightest bin is cheapest" inversion follows arithmetically. Under a
within-season ranking each bin is balanced by construction (88/88/88) and the
inversion disappears.

This also explains why the earlier gas check did not catch it: bin3's lower mean
delivered gas ($4.03 vs $4.53) is itself a *symptom* of the same segregation —
bin3 is summer, and summer gas is cheap. Normalising by gas removes the price
level but not the seasonal population difference.

## 3. What arm C does and does not establish — a limitation, stated plainly

**Arm C is vacuous, and its HOLDS flags are not evidence.** It restricted the
ladder to units offering in **all four** bins — and **711 of 711 units qualify**.
PJM generators submit offers for essentially every hour regardless of commitment
state, so bin membership cannot differ by presence, and arm C reduces exactly to
arm A (identical to three decimals, as the table shows).

Consequently the **population half of the handoff's hypothesis is NOT tested
here.** The handoff's wording was about *commitment status* — "fast-start units
in those hours are largely already committed" — and commitment status is not
recoverable from the offer corpus, which records submissions, not awards.
Answering it needs the cleared/committed side (DA awards), which this probe does
not read. **That question remains open.**

The ARTIFACT verdict therefore rests entirely on **arm B**, which is decisive on
its own for the two segments that carry the effect.

## 4. Consequences

**For pjm-123.** Its §3 generalization — "any mechanism handing a class its
measured conditional level compresses top-end dispersion instead of widening it"
— **narrows to "the surface as conditioned in the 2026-07 vintage."** It is not
a property of PJM's offers. pjm-123's *legs* 1/2/3 were tested against the
frozen surface and those A/B results stand; what does not stand is the
generalization to the whole measured-offer-surface family.

**For the frontier ledger.** The measured surface is a **live candidate
dispersion lever again**, so PJM has a named admissible mechanism that is not
tried — which is exactly what the frontier bar excludes. **Lane 2 stays open.**

**Why this matters more than a bookkeeping blocker.** pjm-125 established that
the remaining >$200 residual is *not* on the reserve supply side. pjm-121's own
promotion caveat records that the dispersion compression is untouched (73 % of
the 2025 C3a gain was a level lift). This finding re-opens the one lever aimed
at that compression. The open lane and the un-repaired residual are the same
object.

**What it does not license.** Nothing here is authority to re-derive. Rule 20
binds: a re-derivation commit must cite a data or conditioning-**definition**
change. A season-conditioned surface *is* such a change and is admissible on
that basis — but adopting it is a **separate, owner-authorized step** needing
its own admissibility memo, and it must be justified as a better definition of
tightness state, never because a residual moved. Note also that the surface's
edges are **shared with the frozen pjm-99 top-of-curve surface** ("the same
tightness state definition"), so re-conditioning one raises the question of the
other — a scope question for that memo, not for this probe.

## 5. Guardrail review

* **Rule 20** — no surface written, no derive re-run, nothing but a diagnostic
  JSON produced. The season definition (PJM's own convention: summer Jun–Sep,
  winter Dec–Mar) was fixed in the module constants before the run and never
  adjusted against a result.
* **Rule 1** — the verdict rests on a conditioning comparison, not on whether
  any residual improved. No backcast number entered the decision.
* **Rule 13** — offers only; clearing prices stay validation-only, as the
  frozen derive requires.
* **Rule 22** — 2025 only; no out-of-training year touched.
* **Falsifiability, and a stated conflict of interest.** This probe was run by a
  session with an interest in the REAL outcome — it would have closed Lane 2 and
  completed the frontier ledger. The criteria were therefore made symmetric and
  quantitative and committed to git before any arm was computed, with the
  ARTIFACT branch spelled out as specifically as the REAL branch. The result went
  against the session's interest and is reported as measured.
* **Scope limit.** 2025 only. The 2023/2024 corpus is fetching for
  confirmation; the CT_FAST flip (+10.00 → −0.85) is far too large to be
  plausibly reversed by other years, but the multi-year check is owed before
  this is treated as settled for all three.

## 6. Reproduction

```
python scripts/data/fetch_pjm_energy_offers.py --years 2025    # ~3 h, ~142 MB
python scripts/probes/pjm126_midcurve_conditioning_precheck.py \
    --years 2025 --json-out results/calibration/pjm126_conditioning_precheck_2025.json
```

The seasonal-composition table (§2) needs no offer corpus at all — it is the
EIA-930 net-load frame plus the month→season map.

## Pointers

* Charter and ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §3 Lane 2.
* The generalization this narrows: `docs/FINDING-pjm123-composite-precheck-2026-07.md` §3.
* The frozen derive under review: `scripts/data/derive_pjm_offer_midcurve.py`
  (and its shared-edge sibling `derive_pjm_offer_surface.py`).
* Why the lane matters now: `docs/FINDING-pjm125-commitment-constraint-precheck-2026-07.md` §5.
