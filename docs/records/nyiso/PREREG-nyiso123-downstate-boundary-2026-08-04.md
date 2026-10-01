# PRE-REGISTRATION — nyiso-123: does the removed-mask reading survive 2023 and 2024?

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper:** `2026-08-04-nyiso-120-c119-scope`, **UNCHANGED**, determination **NOT-YET**
(re-derived at this session's HEAD with `scripts/calibration_verdict.py --run-id`, committed
artifacts only: `price_mean` **FAIL** (2025 −10.1 %), `price_tail` **CAVEAT** (ledgered, budget
1 of 3), the other seven **PASS**). `scripts/audit_keepers.py --iso NYISO` **PASS, 0 failures /
0 warnings**, at the same HEAD.

**Committed and pushed BEFORE the §3 measurements are run.** No solve is planned, budgeted or
permitted in this session. No `ScenarioConfig` field, constant, derive script or artifact will
be changed.

---

## §1 — why this session exists

nyiso-122 (2026-08-04, no solve) decomposed NYISO's 2025 C3a failure into two seasonally
separable objects — a **Jan+Feb $100–300-band** miss (−3.58 $/MWh) and a **Jun+Jul >$300 tail**
miss (−3.76) — and attributed **both** to the same unrepresented **downstate locational
boundary**. It declared the NYISO lever queue **EMPTY**, and named the only successor as the
`Capital_Hudson` → Zone-F/Zone-G **topology split**, which is an **owner-charter** item and
explicitly *not* a lever-queue entry or a mechanism flag.

That leaves this session with no lever to pull, and two jobs it can legitimately do:

1. put the **re-scoped charter question** to the owner (nyiso-122 chartered the split against
   C3c alone; it now also owns a winter *level* miss that is not a scarcity phenomenon), and
   put the **second open owner question** (queue item 4, `nyiso_iroquois_winter_spread`,
   refused ex ante on reach but with its standalone rule 14 `[R-ACCURATE]` case untested) —
   **neither of which this session may resolve itself**; and
2. produce the **leave-one-year-out grounding** that rule 22 requires *before* any structural
   mechanism is promoted, which does not depend on the owner's answer and is charter pre-work
   either way.

This pre-registration covers (2) only. (1) is a question, not an experiment.

## §2 — what is ALREADY on record, and what is genuinely new

Stated up front so no already-computed number is presented as this session's discovery.

**Already committed by nyiso-122, for all three years, and merely *unreported*:** both of that
session's probes carry `YEARS = (2023, 2024, 2025)` as a hard filter and wrote all three years
to disk; the finding narrated 2025 only. So the following are **reads, not measurements**:

- `_nyiso122_c3a_2025_decomp.json` — per-year **annual** band table, tail counts, the two
  counterfactual bounds, and p90/p10 for 2023 and 2024.
- `_nyiso122_winter_zonal_spread.json` — per-year Jan+Feb per-zone gaps, the mainland-4
  identity share, and the actual all-5 monthly zonal spread, for 2023 and 2024.

**Genuinely new in this session:**

- **(a)** the **month × actual-price-band** contribution table for **2023 and 2024**. The
  committed JSON carries bands aggregated over the *whole year*; the seasonal grouping that
  carries nyiso-122's argument (Jan+Feb / Jun+Jul / rest) exists for 2025 in that finding's
  prose only, and for no other year in any artifact.
- **(b)** the mainland-identity share and actual zonal spread **month by month across all
  twelve months**, per year — the committed artifact measures Jan+Feb only.
- **(c)** a **zonal-basis counterfactual**: what the load-weighted mean, and hence C3a, would
  read if the model reproduced the *observed* downstate basis around its own upstate price and
  changed nothing else. This is the locational analogue of nyiso-122's tail counterfactual and
  is the number a charter would be pre-registered against.

## §3 — the analytical point the counterfactual must respect

A **pure redistribution** of price across zones that holds the load-weighted mean fixed does
**not** move C3a — C3a *is* the load-weighted mean. So "the model has no zonal spread" is not,
by itself, an explanation of a mean miss, and this session must not assert that it is.

The mechanism by which a locational failure becomes a *mean* failure is specific: the model
prices every zone at the **unconstrained upstate** marginal cost, and ~65 % of NYISO load sits
**downstate** of the constraint. The correct counterfactual therefore anchors on upstate and
adds the observed basis:

    m*[z,k] = m[Upstate_West,k] + (a[z,k] − a[Upstate_West,k])

evaluated at monthly grain (the committed per-zone actuals are monthly), load-weighted with the
model's own demand so both sides share one basis. It is a **diagnostic bound only** — the
observed basis is a measured *outcome* and under rule 13 `[R-MEASURED]` it may never enter a
solve. Nothing in this session does.

## §4 — pre-registered predictions, and what would falsify the removed-mask reading

The brief's stated expectation is that the mainland-identity share is **~100 % in all three
years** while only 2025 fails C3a, which would confirm that 2025 has no new defect and merely
lost a compensating error. I pre-register the **directional criteria** rather than the outcome:

| | observation | reading |
|---|---|---|
| **P1** | identity share ~equal and near-total in all three years | **CONFIRMS** removed mask: the locational defect is constant, only its offset moved |
| **P1′** | identity share **rises materially** into 2025 | **PARTIALLY REFUTES** it: the model's own zonal dispersion also degraded, so 2025 is not purely a mask removal |
| **P2** | a large **actual** zonal spread in a year that PASSES C3a | **STRENGTHENS** the structural case: the locational miss predates 2025 and passing years are passing for an unrelated reason |
| **P2′** | actual zonal spread large only in 2025 | **WEAKENS** it: the boundary would be a 2025-specific event, not a standing representation gap |
| **P3** | the upstate zone is priced accurately while downstate zones are short, in every year | **STRENGTHENS**: the signature is the boundary, not the fuel or the level |
| **P3′** | upstate is *over*-priced in the passing years by enough to offset downstate | **STRENGTHENS the mask reading specifically, and identifies the mask as a distinct second object** — which must then be named as such rather than folded into the boundary story |
| **P4** | the zonal-basis counterfactual moves C3a materially toward PASS in 2025 | the split is worth a charter |
| **P4′** | it does not | the split is **not** the C3a-2025 route, whatever it does for C3c, and this session must say so |

**§3(c) of the brief asks for a strengthen-or-weaken verdict, and I commit in advance to
reporting whichever of these fires.** nyiso-122 refuted its own successor hypothesis in §3 of
its finding and reported it against interest; that is the standard here. In particular, if P1′
or P4′ fires, the finding will say the topology-split case is **weaker** than nyiso-122's write-up
implies, and will say it in the headline rather than a footnote.

## §5 — governance, declared in advance

- **Rule 12 / rule 16:** no solve, so neither applies. Nothing is registered on the dashboard,
  because there will be no run to register (rule 15 registers *runs*, and a no-LP probe session
  produces none).
- **Rule 13 `[R-MEASURED]`:** every actual price and spread below is a **validation target**.
  The §3(c) counterfactual consumes a measured outcome and is therefore explicitly a
  **diagnostic bound, never an input**, and no mechanism is proposed that would consume it.
- **Rule 22 `[R-HOLDOUT]`:** **training years only**. Both new probes hard-filter to
  {2023, 2024, 2025} and raise on anything else — which matters, because the committed actual
  parquet carries 2018–2022 and 2026. The holdout spend **freeze is ACTIVE** and outranks
  NYISO's `complete` marker; nothing here touches an out-of-training year.
- **Rule 21 / rule 23 / rule 24:** no free parameter is introduced, nothing is re-derived,
  no tunable is added.
- **Rule 25 `[R-ISO-SCOPE]`:** NYISO only. No other ISO's matrix cell is stamped.
- **Rule 28:** the queue was read first and found **EMPTY**; the off-queue element (this session
  tests no mechanism at all) is declared here. No cell verdict changes, because no mechanism is
  tested — the §5.5 status block is updated with the new evidence and the queue stays empty.
- **Owner questions are not decisions.** The topology-split charter and item 4's standalone
  rule 14 case are put to the owner and left there. This session will not write the charter, add
  a `ScenarioConfig` field, or substitute a different NYISO lever to avoid asking.
