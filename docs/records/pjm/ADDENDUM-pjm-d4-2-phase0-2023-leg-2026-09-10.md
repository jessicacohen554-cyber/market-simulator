# ADDENDUM to PRECOMMIT pjm-d4-2 — the 2023 leg of phase 0, and the handoff's pre-registered target

**Session** `pjm-d4-2` · **Date** 2026-09-10 · Written **while the six per-year shards were still
solving**, so it records the pre-solve position rather than reporting one.
Parent: `docs/PRECOMMIT-pjm-d4-2-stgas-membership-2026-09-10.md` (§3, §4 carried 2025 only).

---

## 1. THE SECOND YEAR — same construction, same direction, no new parameter

`run_year(..., fleet_only=True)` off the keeper's own recipe. Because the membership change is now
**on disk**, the control for this leg is built by **removing** the eleven PJM codes in-process, not
by leaving the registry alone — a control built the old way after the edit is a second arm, and one
was built and discarded before this was caught.

| 2023 | control | arm | Δ |
|---|---|---|---|
| whole-fleet min-gen mandate | 445.4442 TWh | 439.4735 TWh | **−5.9707 TWh** |
| fleet rows | 2,989 | 2,978 | −11 (the econ-split leg) |
| mean availability, ST_GAS | 39.6008 | 39.6008 | **0.000000** (leg 2 inert — PRECOMMIT §3) |
| non-admitted plants that move | — | — | **0** |
| **D-4 conduct convictions** | **4** (384, 593, 3149, 3775) | **0** | **−4** |

**2025, restated for the pair:** mandate **−7.9793 TWh**, convictions **2 → 0**.

Every surviving floored plant passes in both years: 1353, 3131, 3138, 3140 — the four the criterion
declines to admit. **The plants that lose the floor are exactly the plants that were failing**, and
no plant that was passing loses it.

## 2. THE HANDOFF'S PRE-REGISTERED TARGET, ANSWERED

pjm-d4-1 §12 set two questions with no free parameter in them, against the backcast-only lay-up mask
(which removed **34.2 % / 34.0 %** of the 2023 / 2025 mandate and cleared all but one conviction):

> *"Does a forward-native membership repair reach a comparable share of the mandate, and does it
> clear plant 3149 (14.3 % duty in 2023), which the lay-up derive never classified?"*

| | lay-up mask (refused, rule 17(c)) | **membership (this card)** |
|---|---|---|
| share of the 2023 mandate removed | 34.2 % | **67.8 %** |
| share of the 2025 mandate removed | 34.0 % | **69.3 %** |
| plant 3149 in 2023 | **NOT cleared** — the one conviction it could not reach | **cleared** — 3149 is admitted at 30.8 % pooled duty, so its 7,666 h floor is removed outright (control: median 0.00 MW, zero-share 0.844) |
| forward analogue | **none** — `_BACKCAST_ONLY_OVERLAY_FIELDS` | forward-native (PRECOMMIT §2d) |

**Both answers are yes, and by roughly twice the margin.** That is the comparison the predecessor
fixed ex ante, and it is reported here as it fell rather than re-framed.

## 3. WHAT THIS STILL DOES NOT SETTLE

Unchanged from PRECOMMIT §5 item 2 and §7, and not softened by the above:

- The rider's basis (`{min_gen > 0}`) is **more forgiving** than the solve's `at_floor_mask`. On the
  committed artifact 2025 shows **5** convictions where this basis shows 2, and three of those five
  (3775, 593, 3148) are admitted while **3131 and 3138 are not**. If the solved arm leaves ST_GAS
  above the 30 % forced-share budget, C8 escalates to the provenance leg and **those two would still
  convict it**. Membership is the largest part of the defect and is not proven to be all of it.
- **Leg 3 still cuts the other way** and is not re-scoped to hide it: the admitted plants lose the
  3.024× ST_GAS peak band. 2023 cap-weighted heat rate falls 17.50 → 13.83 (593), 17.10 → 13.53
  (3148), 15.06 → 12.39 (3149). Floor removal pushes ST_GAS down; this pushes it up. The net is the
  LP's answer, not this document's.
- Nothing here is a gate. No number above was consulted to choose the criterion, which was fixed in
  PRECOMMIT §2 from ERCOT's and CAISO's membership with PJM never consulted.
