# ADDENDUM 1 to PRECOMMIT-scn-ws5a-policy-pjm-2026-09-06 — the P4 hold is RELEASED

**Lane** SCN-WS5A-POLICY-PJM · **Date** 2026-09-06 · **Written BEFORE the first solve**, so
nothing below is revised by a result. The PRECOMMIT itself is **unchanged** — no case, key,
prediction or gate moves. This addendum records two facts the PRECOMMIT could not: who released
the slot, and what HEAD the legs actually run at.

## 1. Precondition P4 — RELEASED BY OWNER ACT

The PRECOMMIT §1/§8 held the first solve because two SCN policy lanes (NYISO, NEISO) were
running and PJM would have been the third against ruling S14's ~2-concurrent cap. **The owner
was asked and answered "take the slot now", with the scope answer "solve all 13 as chartered".**

- P4 reads **MET by grant**, not by assumption. The lane never assumed a free slot (charter P4's
  own instruction), and the grant is an owner act recorded here rather than inferred.
- **The chartered set is NOT narrowed.** All thirteen legs solve, the CES premium ladder
  included — which is what actually *tests* prediction P-9 (that {10, 20, 30} are near-identical
  on PJM under the $45 RPS ceiling) instead of assuming it. A lane does not shrink its own
  charter (PRECOMMIT §8).
- The lane is the third concurrent SCN solve and says so. It runs **one leg at a time**, never
  two PJM LPs at once.

## 2. The HEAD guard — the pin, or a descendant with a ZERO solve-path diff

The PRECOMMIT commit `d0fb83a8` sits on top of THE PIN, so a literal
`[ "$(git rev-parse HEAD)" = "bdfb3095" ]` guard could not pass. The convention RESOLVE §4.2(c)
already established applies — *"its `git.sha` is THE PIN, or a descendant of it with a zero
solve-path diff … this lane commits while later legs solve"* — and the diff is **measured empty**
before the first solve:

```
git diff bdfb3095 HEAD -- src/market_sim scripts/lib scripts/run_full_horizon.py \
  scripts/run_ces_leg.py scripts/check_forecast_invariants.py configs/ \
  data/raw/_validation-source data/raw/reference
→ (no output)
```

So every leg runs on **byte-identical solve-path bytes to THE PIN**, and the guard this lane
actually executes is the pair:

```
H0=<the lane HEAD at launch>
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
git diff --quiet bdfb3095e9fa0cd2bec3f4e843f320b42588c72b HEAD -- \
  src/market_sim scripts/lib scripts/run_full_horizon.py scripts/run_ces_leg.py \
  scripts/check_forecast_invariants.py configs/ data/raw/_validation-source \
  data/raw/reference || exit 91
```

`exit 91` is the stronger half: it fails the solve if any commit this lane makes between legs
ever touches a solve-path file, which is the real hazard the literal-sha guard was standing in
for. **Rebase happens between legs, never during one**, and after any rebase the pair is
re-checked before the next leg — a rebase that pulls a solve-path change onto this branch stops
the lane rather than silently re-pinning it.

## 3. Leg order — highest-information first, heaviest last

Not a charter requirement; recorded so the order cannot be read as chosen after seeing a result.

1. `CARB-MID` — the cross-lane anchor (P-1 scores against WS-1b §3.4)
2. `CARB-LO`, 3. `CARB-HI` — the ladder's sub-linearity (P-5, P-6)
4. `CES-T80` — the dual identity G4 and the one arm that clears the $45 ceiling (P-11, P-12)
5. `CES-P20`, 6. `CES-P10`, 7. `CES-P30` — the domination null (P-9, P-10)
8. `VOL-MID`, 9. `VOL-HI` — the escape regime and the deployment null (P-13, P-14, P-15)
10. `CES-P20+VOL-HI` — the empty composition (P-16)
11. `CAP-STATE-TIGHT` — price vs quantity (P-19, G10–G12)
12. `CARB-MID+LOAD-HI`, 13. `ALL-CLEAN` — the two high-load arms, heaviest and last (P-17, P-18)

Every leg is committed on its own, so an interruption costs at most one leg.
