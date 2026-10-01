# FINDING — miso-93 LANE A: the MISO keeper on the guard-corrected CAMPD envelope

**Verdict: RE-TUNE REQUIRED.** `2026-07-25-miso-88-egrid-hr` does **not** hold
its determination on the availability envelope the repo now carries.
Determination falls `CALIBRATED-WITH-CAVEATS` → **`NOT-YET`**, on a single
newly-failing gate: **C3a-2024, −8.7 % → −10.1 %**, crossing the ±10 % veto by
**0.1 pp**.

**Registered arm:** `2026-07-26-miso-93-meritguard-a1`
(`results/calibration/miso93_meritguard_a1`, MISO 2023/2024/2025, one bundle,
rule 16). Rule 15: registered whatever the verdict.
**Charter, pre-registered before any result was read:**
`docs/handoffs/miso-93-keeper-reaudit-charter-2026-07.md`.
**Parent:** `campd-economic-layup-fix-charter-2026-07.md` §5/§8 blast radius.
**Predecessor:** miso-89 attempted this and was RAM-blocked; miso-92's 35 %
floor reduction is what made the staged recipe fit.

**No tuning was applied and none is licensed by this result.** The ledger budget
is 3/3 and this lane consumed and freed none of it.

---

## 1. Headline

| criterion | keeper | A1 (corrected envelope) | verdict |
|---|---|---|---|
| C1 fuel-mix by class | PASS (free 12/12) | **PASS** | held |
| C2 family volume | PASS | **PASS** | held |
| **C3a mean LMP** | 2025 ledgered; 2023/2024 PASS | **2024 FAIL −10.1 %** | **BROKE** |
| C3b shape | 2025 NRMSE 0.208 ledgered | 0.214, still ledgered | widened |
| C3c tail | ledgered | ledgered | held |
| C4 / C5a / C6 / C7 / C8 | PASS | **PASS** | held |

Everything the keeper had except C3a survives the corrected envelope. The
determination turns on one year of one criterion, by one tenth of a point.

## 2. The isolation — the whole drift is the extract, and the code is provably inert

The charter flagged that miso-92's attribution of the HEAD drift to CAMPD was an
**attribution, not an isolation**: `git diff 3babe5f..HEAD` touches
`offer_surfaces.py` (+391), `renewables.py` (+342), `scenarios.py` (+220),
`runner.py` (+129) and six more modules, none audited for MISO-inertness.
caiso-123 is the precedent for why that gap matters — CAISO's re-audit verdict
was measured against a confounded A0 and had to be withdrawn.

A single-year throwaway probe closes it. 2024 (the failing year) was solved at
**HEAD** with the extract reverted to the keeper's own blob `f2b3ec8`, against
the registered A1 arm at HEAD with `c298c68`. Load-weighted price, one
consistent basis, keeper value read from its **committed** `hourly/` sidecar:

| arm | 2024 load-weighted price | C3a |
|---|---|---|
| KEEPER (sha `3babe5f`, pre-guard extract) | $29.470 | −8.68 % |
| **A0′** (HEAD, pre-guard extract) | **$29.470** | −8.68 % |
| **A1** (HEAD, guard-corrected extract) | **$29.024** | −10.06 % |

* **code drift `3babe5f..HEAD`, extract held fixed: $+0.000 — exactly zero.**
  A0′ reproduces the keeper's committed 2024 price to three decimals. The entire
  post-keeper code surface is **measured MISO-inert**, not assumed so.
* **guard/extract effect at identical HEAD: −$0.445 (−1.38 pp)** — i.e. 100 % of
  the drift.

This upgrades miso-92's "CAMPD is a sufficient explanation" to a measured
isolation, and it confirms MISO does **not** carry the confounded-A0 defect.
The extract axis was independently verified single-delta *before* solving: the
committed blob is byte-identical across the keeper's own `git_sha`, changes
exactly once (at the guard commit `6a8f285`), and has not changed since.

The effect is stable across all three years — it is not a 2024 artifact:

| year | keeper | A1 | Δ | actual |
|---|---|---|---|---|
| 2023 | $31.791 | $31.324 | −$0.467 (−1.42 pp) | $32.87 |
| 2024 | $29.470 | $29.024 | −$0.445 (−1.38 pp) | $32.27 |
| 2025 | $37.839 | $37.443 | −$0.396 (−0.87 pp) | $45.39 |

2024 fails and 2023 does not simply because 2024 started closest to the veto.

## 3. Why prices fall — measured from the two committed blobs, no solve

The guard's effect on the envelope, computed directly from the A0 and A1 CSVs:

* **2,424 windows / 11,614 GW-days REMOVED. Zero added.** (A0 90,722 → A1
  79,108 GW-days, −12.8 %.)
* By class: **ST_GAS 8,541 GW-days (73.5 %)**, CC_REGULAR 1,522 (13.1 %),
  COAL 810 (7.0 %), CC_CHP 625 (5.4 %), CT/ST_CHP 117 (1.0 %).
* In-sample slice 2023–2025: **755 windows / 3,630 GW-days** — reproducing the
  figure committed with the guard **exactly**, an independent check on this
  session's read of the extract.

The mechanism is therefore exactly the one the parent charter predicted: gas
**steam** units priced out of merit for weeks were being booked as mechanically
unavailable. Returning ~8.5 GW-days-per-thousand of ST_GAS to the available
fleet adds supply, and more supply lowers the clearing price. The model's mean
LMP was already low, so the correction pushes it further from the actual.

Corroborated inside the run: **C8 ST_GAS forced share rises** 35.7 → 39.9 %
(2023), 36.9 → 41.1 % (2024), 51.1 → 53.8 % (2025) — the same class, the same
direction. All three remain **grounded above budget** (D-4 clean, profile
r 0.972–0.977, CV ratio 1.137–1.427), so C8 still PASSes.

## 4. This is a rule-11 signal, not a reason to revert

Per CLAUDE.md rule 11 `[R-ACCURATE]`: the accurate input **stays in**, and the
worse fit is a **discovered bug**, not grounds to restore the estimate. The
keeper's offer curves were silently compensating for an inflated outage
envelope — the same condition the parent charter measured at NEISO (§5:
relieving the over-count moved mean LMP −7 to −9 % and halved h>$200) and the
ERCOT-79 / nyiso-63 condition it cites.

The MISO instance is far milder than NEISO's (−1.4 pp, not −7 to −9 %), which
is consistent with MISO's extract being over-counted by a smaller share.

**What this finding does NOT license** (rules 1 / 10 / 23 / 24): no offer adder,
no level multiplier, no summer band, no widening of the C3a ledger entry to
absorb 2024, and no re-derivation of `SUMMER_WEFOR_SHARE` or
`SUMMER_CLASS_DERATE` — this lane has no source-data change of that kind to
cite. The re-tune is a **future chartered session's** work, and the budget is
already 3/3, so it must be closed by structure, not by a ledger slot.

## 5. A clean-partition dependency that was silently contaminating MISO replays

**neiso-65 §2's partition table has no MISO row** — MISO never solved in that
session (RAM-blocked), so its dependencies were never audited. That omission
contaminated this session's first launch and would contaminate every future
MISO replay.

* `model/interchange/miso.py::_miso_cil_cel_groups` builds **per-zone seasonal
  CIL/CEL interface groups** from the curated `capacity-deliverability`
  partition (MISO LOLE Study Reports).
* Absent the partition it returns `[]` and the caller falls back to **static
  PY2025-26 summer caps** — documented and graceful, but a structurally
  different network.
* It does this **independently of the `capacity_deliverability_limits` flag**,
  which is `false` in the MISO keeper. **Reading the flag is not sufficient to
  conclude the partition is unneeded** — that is precisely the trap.
* With the partition present the log instead reads `seasonal CIL/CEL interface
  caps on 5 zone group(s) … static summer fallbacks replaced`.
* `ramp-capability` also carries a MISO partition (991 rows).

The first (degraded) launch was killed, its bundle deleted, and **no number from
it is quoted anywhere**. Every arm in this finding was solved with
`capacity-deliverability`, `ramp-capability`, `transfer-interface-limits` and
`winter-fuel-inventory` regenerated first, and every solve log audited for
missing-input warnings (all clean).

**Consequence for the record:** miso-92's replay levels (mean LWP
$31.224 → $30.770) were measured on the degraded network — its session predates
this discovery. Its *delta* (−$0.454) agrees with this session's 2023 delta
(−$0.467) to within $0.02, so its conclusion stands; its **absolute levels are
~$0.5 low and should not be quoted**. The authoritative keeper baseline is its
own committed `hourly/` sidecar ($31.791 for 2023), used throughout §2.

## 6. Pre-registration honesty

The charter §5 named **C3a-2024 as the single exposure** before solving, on the
ground that it sat at −8.0 % against a −10 % veto with little margin, and
predicted the class shifts would cancel within the C1/C2 bands.

* **Right:** the failing gate, the year, the direction, and that C1/C2/C5a/C8
  would hold. C1 and C2 did hold, exactly as reasoned.
* **Wrong:** the magnitude. The charter estimated ≈−9.4 % and called it "inside
  the band". It landed at **−10.1 %, outside**. The point estimate was
  optimistic; recorded here rather than narrated after the fact as predicted.

## 7. What the next session inherits

1. **The keeper's registered numbers are now reproducible** — A1 is the bundle
   that reproduces at HEAD. The pre-adoption state flagged by miso-89/miso-92 is
   resolved.
2. **MISO needs a re-tune charter**, scoped to C3a level under a ~1.4 pp
   structural price reduction, with the 3/3 ledger saturated. Rule 1: the fix
   must be structural, and the corrected extract stays in whatever it does to
   the residual.
3. **The keeper designation is an owner call.** This session did **not** change
   `frontend/data/backcast/keepers/MISO.json`: miso-88 remains the designated
   keeper, now carrying a measured RE-TUNE trigger. Promoting or demoting on a
   NOT-YET arm is not a session's act.
4. **The neiso-65 partition table needs a MISO row** (§5) before any further
   MISO replay.
5. **Code churn `3babe5f..HEAD` is measured MISO-inert** (§2) — a future session
   does not need to re-establish that for this window.
