# PRE-DECLARATION — capx D47b: the board's `c_cost` fields (r#33 amendment 3)

**Committed and pushed BEFORE any `c_cost` field is edited.** This is the fifth and last
D47 item. Items 1–4 (the GOLDEN-3 pre-declaration, the attestation, the `neiso-t3`
re-score, the `-pre-d46` like-for-like table and the `neiso-t1h` posture disclosure)
landed on `main` in PR #4691 (`bd4ba21d`, commits `71dd390e` / `57987a7d` / `96f5d84a`)
and are **verified in place at HEAD and not re-done here**: `neiso-t3` reads FC-7 `PASS`,
determination `HOLD`, session `capx-D47`; the prior record is preserved at
`neiso-t3-pre-d47` reading FC-7 `FAIL`, session `capx-D46`. The `c_cost` item was not
covered by that PR and is the only open half.

**Lane:** capx D47b — RECORDS ONLY. **ZERO SOLVES.** Branch
`claude/capx-d47-golden3-attestation-nrqtyq`, rebased on `origin/main` `8a18e9e1`.

**Guardrails, restated as binding:** no `ScenarioConfig` field, parameter, keeper, shard,
marker or matrix verdict; gate (a) never moved; rule 22 untouched; the backcast namespace
untouched. **No gate-leg `status` moves** — every `c_cost` leg reads `info` before and
after, and `info` is not a gate test. Only `detail` prose changes. Rule 27 applies to
`frontend/data/forecast/program-status.json` (1,155 lines): local `Edit` only, exact
on-disk bytes pushed, blob verified after the push.

---

## 1. The defect found before writing anything — declared here, not after

The dispatch instructed: *"D46 §2 measured the t1f legs at 8–23 min against `c_cost`
fields of 1.0–2.8 h. Correct … to the MEASURED values … mark PJM/MISO/NYISO's fields
'unmeasured at the t1f grain — D46 factor 7–10× suggests ~45–90 min'."*

**Executing that literally would put a wrong number on the board, in the dangerous
direction.** The two quantities are not the same measurement:

| | span | source |
|---|---|---|
| the `c_cost` fields | **25 solve-years** (2026–2050, full horizon) | FF-3E projection table, `docs/handoffs/ff-poc-closeout-2026-07.md` §6 |
| D46's measured t1f legs | **5 solve-years** (2026–2030) | `results/ff-t1f-d46/<iso>/full_horizon_summary.json`, `solved_years [2026…2030]` |

D46 §2's headline — *"wildly conservative, by factors of 7–10×"* — therefore compares a
5-year total against a 25-year projection. **The factor is a span artifact**: 5× span ×
the projection's own ~1.7–2× super-linear uplift ≈ 8.5×, which is the "7–10×" observed.
It is not a measurement of the board's field, and D46 §9 item 3 routes it to the director
as though it were.

**This is a correction to D46 §2's comparison and §9 item 3's inference. It is not a
correction to any D46 solve, cache key, verdict or determination**, all of which stand.

## 2. What I will write instead, declared before I write it

The evidence, all read from committed bytes before this document (per-year `wall_s` from
each bundle's `per_year_perf`):

| leg | span | total | median/yr | FF-3E anchor | peak RSS |
|---|---|---|---|---|---|
| ERCOT t1f | 5 yr | 11.81 min | **144.1 s** | 144 s (**+0.1 %**) | 4,137.7 MB |
| NEISO t1f | 5 yr | 7.96 min | **86.3 s** | 78 s (+10.6 %) | 3,336.7 MB |
| CAISO t1f | 5 yr | 22.59 min | **208.8 s** | 200 s (+4.4 %) | 4,917.4 MB |
| **NEISO GOLDEN-3** | **25 yr** | **33.0 min = 0.55 h** | **77.6 s** | 78 s (**−0.5 %**) | 3,694.0 MB |

Two findings follow, and I declare them now so neither can be presented later as
convenient:

1. **FF-3E's per-year anchors are ACCURATE** — within +0.1 % to +10.6 % on three ISOs at
   the 5-year grain, and within −0.5 % on the one 25-year run. They are not "an order
   out"; they are among the better-identified numbers on this board.
2. **FF-3E's super-linear uplift is REFUTED — with the sign reversed.** §6's caution
   ("late years grow super-linearly — do NOT extrapolate the median flat") predicted the
   uplift. GOLDEN-3's 25 measured years run the other way: years 21–25 mean **65.0 s**
   against years 1–5 mean **95.3 s**, a ratio of **0.68×**. Cost per year *falls* across
   the horizon. GOLDEN-3's total lands **1.8 % above the flat-median lower bound** (0.54 h)
   and **1.73× under the projection** (0.95 h). The whole projection error is the uplift.

So the corrected reading is **~1.7×, measured once**, not 7–10×. Applied to PJM's 7.34 h
that is **~4.2 h** — and if the uplift is refuted outright, PJM's flat-median lower bound
**1.63 h**. **Neither is ~45–90 min**, and I will not write that figure.

## 3. The edits, enumerated

Six `detail` strings in `frontend/data/forecast/program-status.json`, nothing else:

- **ERCOT, NEISO, CAISO** — the MEASURED values at the grain each was measured, with the
  span stated on its face; the prior number identified as FF-3E's projection and its
  basis decomposed (per-year anchor verified / uplift refuted); the citation chain
  D46 §2 → this lane's finding §8.
- **PJM, MISO, NYISO** — **unmeasured at every grain**, stated plainly. I will give a
  **bracket** (flat-median lower bound … FF-3E projection) rather than a point estimate,
  and record that the refutation transfers *least* well to PJM/MISO, whose projections
  carry a ~4.5× uplift tied to ~10 GB late-horizon growth that no measured ISO
  (all ≤ 4.9 GB, all pairable) exercises.
- **The ~10 GB / SOLO memory ceilings on PJM and MISO are preserved verbatim.** Nothing
  measured here speaks to them, and they are what rule 12 keys on. A wall-time correction
  must not erode a memory constraint.
- **The container's ~55 min `regenerate_clean.py` prerequisite** (54 datatypes, D46 §2) is
  named in each corrected field as a **separate, per-container** cost — not folded into
  any leg's wall time.

## 4. Pre-declared failure modes, graded at full magnitude

1. **Any gate-leg `status` moves, or any field other than the six `c_cost.detail`
   strings changes** → STOP, do not push, route to the director.
2. **`check_gate_a_provenance.py` regresses** → repair or route; gate (a) is never moved
   by this lane and its reading is re-checked at close.
3. **The JSON fails to parse, or the diff shows more than six changed lines** → revert and
   redo with `Edit`, never with a re-dump (a `json.dump` round-trip would reformat all
   1,155 lines and trip rule 27).

---

**Pre-declared 2026-09-04, capx D47b, before any `c_cost` field was edited.**
